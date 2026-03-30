"""Auth, profile, chat streaming, login panel content, onboarding."""

import json
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from api.audience_config import AUDIENCE_CONFIG
from api.auth_utils import create_access_token, hash_password, verify_password
from api.chat_service import build_system_prompt, stream_groq_reply
from api.database import get_db
from api.deps import get_current_user, get_optional_user
from api.models import ChatMessage, ChatSession, SavedView, User, UserProfile
from api.personalization import compute_personalization, get_smart_model_from_env

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)
router = APIRouter(tags=["users"])

CONTENT_DIR = Path(__file__).parent.parent / "content"
LOGIN_PANEL_PATH = CONTENT_DIR / "login_panel.md"


class RegisterBody(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=6, max_length=256)


class LoginBody(BaseModel):
    email: str
    password: str


@router.post("/auth/register")
@limiter.limit("10/hour")
def register(request: Request, body: RegisterBody, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email.lower().strip()).first():
        raise HTTPException(400, "Email already registered")
    user = User(email=body.email.lower().strip(), hashed_password=hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    prof = UserProfile(user_id=user.id)
    db.add(prof)
    db.commit()
    token = create_access_token(user.email, user.id)
    return {"access_token": token, "token_type": "bearer", "user": {"id": user.id, "email": user.email}}


@router.post("/auth/login")
@limiter.limit("20/hour")
def login(request: Request, body: LoginBody, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.lower().strip()).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(401, "Invalid email or password")
    token = create_access_token(user.email, user.id)
    return {"access_token": token, "token_type": "bearer", "user": {"id": user.id, "email": user.email}}


@router.get("/auth/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email}


@router.get("/content/login-panel")
def get_login_panel():
    if not LOGIN_PANEL_PATH.exists():
        return {"markdown": "## MarketLens\n\nEdit `content/login_panel.md` to customize this panel."}
    return {"markdown": LOGIN_PANEL_PATH.read_text(encoding="utf-8")}


class LoginPanelPut(BaseModel):
    markdown: str = Field(..., max_length=50000)


@router.put("/content/login-panel")
def put_login_panel(body: LoginPanelPut, user: User = Depends(get_current_user)):
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    LOGIN_PANEL_PATH.write_text(body.markdown, encoding="utf-8")
    return {"ok": True}


@router.get("/profile")
def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    prof = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not prof:
        prof = UserProfile(user_id=user.id)
        db.add(prof)
        db.commit()
        db.refresh(prof)
    pers = None
    if prof.personalization_json:
        try:
            pers = json.loads(prof.personalization_json)
        except json.JSONDecodeError:
            pers = None
    return {
        "audience": prof.audience,
        "industry": prof.industry,
        "onboarding_completed": prof.onboarding_completed,
        "personalization": pers,
    }


@router.post("/profile/reset-onboarding")
def reset_onboarding(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Clear onboarding flag so the user sees login flow -> onboarding again (token stays valid)."""
    prof = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not prof:
        prof = UserProfile(user_id=user.id)
        db.add(prof)
    prof.onboarding_completed = False
    prof.personalization_json = None
    db.commit()
    return {"ok": True}


class OnboardingCompleteBody(BaseModel):
    audience: str = Field(..., pattern="^(investors|companies|customers)$")
    industry: str = Field(..., min_length=2, max_length=64)
    session_id: int


@router.post("/onboarding/complete")
def onboarding_complete(
    body: OnboardingCompleteBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from industry_config import INDUSTRY_CONFIG
    from pipeline import build_client

    if body.industry not in INDUSTRY_CONFIG:
        raise HTTPException(400, "Invalid industry")

    sess = db.query(ChatSession).filter(
        ChatSession.id == body.session_id, ChatSession.user_id == user.id
    ).first()
    if not sess:
        raise HTTPException(404, "Chat session not found")

    msgs = db.query(ChatMessage).filter(ChatMessage.session_id == sess.id).order_by(ChatMessage.id).all()
    lines = []
    for m in msgs:
        if m.role in ("user", "assistant"):
            lines.append(f"{m.role.upper()}: {m.content}")
    transcript = "\n".join(lines)

    prof = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not prof:
        prof = UserProfile(user_id=user.id)
        db.add(prof)
        db.flush()

    from api.industry_service import build_industry_data, get_industry_cache_entry

    ent = get_industry_cache_entry(body.industry)
    industry_json = build_industry_data(
        body.industry,
        ent["scores"],
        ent["insights"],
        review_counts=ent.get("review_counts"),
        data_source=ent.get("data_source"),
    )

    client, _fast, smart, provider = build_client()
    pers_dict = {}
    if client and provider == "Groq":
        model = get_smart_model_from_env()
        pers_dict = compute_personalization(
            audience=body.audience,
            industry_json=industry_json,
            chat_transcript=transcript,
            client=client,
            model=model,
        )
    else:
        pers_dict = {
            "narrative_summary": "Set GROQ_API_KEY to enable full AI personalization.",
            "focus_dimensions": [],
            "suggested_kpis": [],
            "insights_from_chat": [],
            "chart_series": {"priority_scores": []},
        }

    prof.audience = body.audience
    prof.industry = body.industry
    prof.onboarding_completed = True
    prof.personalization_json = json.dumps(pers_dict, ensure_ascii=False)
    db.commit()

    return {"ok": True, "personalization": pers_dict}


class ChatSessionCreate(BaseModel):
    purpose: str = Field("onboarding", pattern="^(onboarding|dashboard)$")
    industry: str | None = None


@router.post("/chat/session")
def create_chat_session(
    body: ChatSessionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sess = ChatSession(
        user_id=user.id,
        purpose=body.purpose,
        industry_context=body.industry,
    )
    db.add(sess)
    db.commit()
    db.refresh(sess)
    return {"session_id": sess.id}


class ChatStreamBody(BaseModel):
    session_id: int
    industry: str | None = None
    audience: str | None = None  # investors | companies | customers
    content: str = Field(..., min_length=1, max_length=1000)


@router.post("/chat/stream")
@limiter.limit("60/hour")
def chat_stream(
    request: Request,
    body: ChatStreamBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from industry_config import INDUSTRY_CONFIG
    from pipeline import build_client

    sess = db.query(ChatSession).filter(
        ChatSession.id == body.session_id, ChatSession.user_id == user.id
    ).first()
    if not sess:
        raise HTTPException(404, "Session not found")

    client, fast_model, _smart, provider = build_client()
    if not client or provider != "Groq":
        raise HTTPException(
            503,
            "Chat requires GROQ_API_KEY. Add it to your .env and restart the API.",
        )

    industry_json = None
    ind = body.industry or sess.industry_context
    if ind and ind in INDUSTRY_CONFIG:
        from api.industry_service import build_industry_data, get_industry_cache_entry

        ent = get_industry_cache_entry(ind)
        industry_json = build_industry_data(
            ind,
            ent["scores"],
            ent["insights"],
            review_counts=ent.get("review_counts"),
            data_source=ent.get("data_source"),
        )
        sess.industry_context = ind

    guided = []
    aud = body.audience
    if aud and aud in AUDIENCE_CONFIG:
        guided = [u["question"] for u in AUDIENCE_CONFIG[aud]["use_cases"]]

    system = build_system_prompt(
        industry_json=industry_json,
        audience=aud,
        guided_questions=guided,
    )

    prior = db.query(ChatMessage).filter(ChatMessage.session_id == sess.id).order_by(ChatMessage.id).all()
    messages = [{"role": "system", "content": system}]
    for m in prior:
        if m.role in ("user", "assistant"):
            messages.append({"role": m.role, "content": m.content})
    messages.append({"role": "user", "content": body.content})

    user_msg = ChatMessage(session_id=sess.id, role="user", content=body.content)
    db.add(user_msg)
    db.commit()

    def event_stream():
        pieces: list[str] = []
        try:
            for chunk in stream_groq_reply(client, fast_model, messages):
                pieces.append(chunk)
                yield f"data: {json.dumps({'token': chunk})}\n\n"
            full = "".join(pieces)
            am = ChatMessage(session_id=sess.id, role="assistant", content=full)
            db.add(am)
            db.commit()
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


class DashboardPersonalizeBody(BaseModel):
    industry: str
    session_id: int


@router.post("/dashboard/personalize")
def dashboard_personalize(
    body: DashboardPersonalizeBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Re-run personalization after dashboard chat (optional follow-up)."""
    from industry_config import INDUSTRY_CONFIG
    from pipeline import build_client

    if body.industry not in INDUSTRY_CONFIG:
        raise HTTPException(400, "Invalid industry")

    sess = db.query(ChatSession).filter(
        ChatSession.id == body.session_id, ChatSession.user_id == user.id
    ).first()
    if not sess:
        raise HTTPException(404, "Session not found")

    prof = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not prof or not prof.audience:
        raise HTTPException(400, "Complete onboarding first")

    msgs = db.query(ChatMessage).filter(ChatMessage.session_id == sess.id).order_by(ChatMessage.id).all()
    transcript = "\n".join(f"{m.role.upper()}: {m.content}" for m in msgs if m.role in ("user", "assistant"))

    from api.industry_service import build_industry_data, get_industry_cache_entry

    ent = get_industry_cache_entry(body.industry)
    industry_json = build_industry_data(
        body.industry,
        ent["scores"],
        ent["insights"],
        review_counts=ent.get("review_counts"),
        data_source=ent.get("data_source"),
    )

    client, _f, _s, provider = build_client()
    if not client or provider != "Groq":
        raise HTTPException(503, "GROQ_API_KEY required")

    pers_dict = compute_personalization(
        audience=prof.audience,
        industry_json=industry_json,
        chat_transcript=transcript,
        client=client,
        model=get_smart_model_from_env(),
    )
    prof.personalization_json = json.dumps(pers_dict, ensure_ascii=False)
    db.commit()
    return {"personalization": pers_dict}


class SavedViewCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    industry: str
    audience: str


@router.get("/saved-views")
def list_saved_views(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(SavedView)
        .filter(SavedView.user_id == user.id)
        .order_by(SavedView.created_at.desc())
        .all()
    )
    return {
        "views": [
            {
                "id": v.id,
                "name": v.name,
                "industry": v.industry,
                "audience": v.audience,
                "created_at": v.created_at.isoformat() if v.created_at else "",
            }
            for v in rows
        ]
    }


@router.post("/saved-views")
def create_saved_view(body: SavedViewCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from industry_config import INDUSTRY_CONFIG

    if body.industry not in INDUSTRY_CONFIG:
        raise HTTPException(400, "Invalid industry")
    if body.audience not in ("investors", "companies", "customers"):
        raise HTTPException(400, "Invalid audience")
    v = SavedView(
        user_id=user.id,
        name=body.name.strip(),
        industry=body.industry,
        audience=body.audience,
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return {"id": v.id, "name": v.name, "industry": v.industry, "audience": v.audience}


@router.delete("/saved-views/{view_id}")
def delete_saved_view(view_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    v = db.query(SavedView).filter(SavedView.id == view_id, SavedView.user_id == user.id).first()
    if not v:
        raise HTTPException(404, "Not found")
    db.delete(v)
    db.commit()
    return {"ok": True}
