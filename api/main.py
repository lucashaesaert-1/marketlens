"""
InsightEngine API — Backend for MarketLens UI
Connects the Figma design to the pipeline.py analysis engine.
"""

import json
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).parent.parent))
from api.audience_config import AUDIENCE_CONFIG
from api.database import SessionLocal, get_db, init_db
from api.deps import get_optional_user
from api.industry_service import (
    _cache,
    build_industry_data,
    get_industry_state,
    merge_personalization,
)
from api.models import UserProfile
from api.user_routes import router as user_router
from industry_config import INDUSTRY_CONFIG, MOCK_INSIGHTS_BY_INDUSTRY
from pipeline import (
    _env_int,
    build_client,
    compute_dimension_scores,
    generate_insights,
)

app = FastAPI(title="InsightEngine API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router, prefix="/api")


@app.on_event("startup")
def _startup():
    init_db()
    _seed_demo_user()


def _seed_demo_user():
    from api.auth_utils import hash_password
    from api.models import User

    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == "demo@marketlens.ai").first():
            return
        user = User(email="demo@marketlens.ai", hashed_password=hash_password("demo12345"))
        db.add(user)
        db.commit()
        db.refresh(user)
        db.add(UserProfile(user_id=user.id, onboarding_completed=False))
        db.commit()
    finally:
        db.close()


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/audience-config")
def get_audience_config():
    return AUDIENCE_CONFIG


@app.get("/api/industries")
def list_industries():
    return {
        "industries": [
            {"id": k, "name": v["name"]}
            for k, v in INDUSTRY_CONFIG.items()
        ]
    }


def _industry_payload(industry: str, db: Session, user):
    if industry not in INDUSTRY_CONFIG:
        raise HTTPException(404, f"Industry '{industry}' not found")
    scores, insights = get_industry_state(industry)
    data = build_industry_data(industry, scores, insights)
    if user:
        prof = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        if (
            prof
            and prof.personalization_json
            and prof.industry == industry
            and prof.audience
            and prof.onboarding_completed
        ):
            try:
                pers = json.loads(prof.personalization_json)
                data = merge_personalization(data, pers, prof.audience)
            except json.JSONDecodeError:
                pass
    return data


@app.get("/api/industry/{industry}")
def get_industry_data(
    industry: str,
    db: Session = Depends(get_db),
    user=Depends(get_optional_user),
):
    return _industry_payload(industry, db, user)


@app.get("/api/industry/{industry}/audience/{audience}")
def get_industry_audience(
    industry: str,
    audience: str,
    db: Session = Depends(get_db),
    user=Depends(get_optional_user),
):
    if audience not in ("investors", "companies", "customers"):
        raise HTTPException(400, "Audience must be investors, companies, or customers")
    return _industry_payload(industry, db, user)


class RunAnalysisRequest(BaseModel):
    api_key: str | None = None
    provider: str = "groq"
    industry: str = "crm"
    resource_keys: dict[str, str] | None = None
    use_live_sources: bool = True


@app.post("/api/run-analysis")
def run_analysis(req: RunAnalysisRequest):
    if req.api_key:
        os.environ["GROQ_API_KEY" if req.provider == "groq" else "OPENAI_API_KEY"] = req.api_key
    if req.resource_keys:
        for k, v in req.resource_keys.items():
            if k == "trustpilot" and v:
                os.environ["TRUSTPILOT_API_KEY"] = v
            if k == "apify" and v:
                os.environ["APIFY_API_TOKEN"] = v

    industry = req.industry
    if industry not in INDUSTRY_CONFIG:
        raise HTTPException(400, f"Industry '{industry}' not supported")

    cfg = INDUSTRY_CONFIG[industry]
    data_path = Path(__file__).parent.parent / cfg["data_file"]
    companies = cfg["companies"]
    focal = cfg["focal"]

    reviews = None
    fetch_limit = max(40, _env_int("FETCH_REVIEW_LIMIT", 150))
    if req.use_live_sources:
        try:
            from resources.adapters import fetch_reviews_for_industry
            reviews = fetch_reviews_for_industry(industry, companies, focal, limit=fetch_limit)
        except Exception:
            pass

    if reviews is None and data_path.exists():
        reviews = json.loads(data_path.read_text(encoding="utf-8"))

    if reviews is None or not reviews:
        scores, insights = cfg["mock_scores"], MOCK_INSIGHTS_BY_INDUSTRY[industry]
        _cache[industry] = (dict(scores), list(insights))
        return {"status": "complete", "message": f"Using mock data for {industry} (no review file or live source)."}

    try:
        client, fast, smart, _ = build_client()
        if client is None:
            scores, insights = cfg["mock_scores"], MOCK_INSIGHTS_BY_INDUSTRY[industry]
            _cache[industry] = (dict(scores), list(insights))
            return {"status": "complete", "message": "Using mock data (no API key). Set GROQ_API_KEY for live analysis."}

        scores = compute_dimension_scores(
            reviews, client, fast, use_mock=False,
            companies=cfg["companies"],
            dimensions=cfg["dimensions"],
            mock_scores=cfg["mock_scores"],
        )
        use_cases = []
        for ac in AUDIENCE_CONFIG.values():
            use_cases.extend(uc["question"] for uc in ac.get("use_cases", []))
        insights = generate_insights(
            scores, client, smart,
            vertical=cfg["name"],
            focal=cfg["focal"],
            competitors=[c for c in cfg["companies"] if c != cfg["focal"]],
            use_cases=use_cases if use_cases else None,
        )
        _cache[industry] = (scores, insights)
        return {"status": "complete", "message": f"Analysis complete for {industry}. Refresh the dashboard."}
    except Exception as e:
        raise HTTPException(500, str(e))
