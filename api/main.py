"""
InsightEngine API — Backend for MarketLens UI
Connects the Figma design to the pipeline.py analysis engine.
"""

import csv
import io
import json
import logging
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).parent.parent))
from api.audience_config import AUDIENCE_CONFIG
from api.database import SessionLocal, get_db, init_db
from api.deps import get_current_user, get_optional_user
from api.industry_service import (
    build_industry_data,
    get_industry_cache_entry,
    merge_personalization,
)
from api.models import UserProfile
from api.run_analysis_core import RunAnalysisRequest, iter_run_analysis_events, run_analysis_sync
from api.user_routes import router as user_router
from industry_config import INDUSTRY_CONFIG

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logging.getLogger("insightengine").setLevel(logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiter — key by IP address
limiter = Limiter(key_func=get_remote_address)

# CORS origins: set ALLOWED_ORIGINS env var as comma-separated list for production
_default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
]
_env_origins = os.getenv("ALLOWED_ORIGINS", "")
ALLOWED_ORIGINS = [o.strip() for o in _env_origins.split(",") if o.strip()] or _default_origins

app = FastAPI(title="InsightEngine API", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
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
def health(db: Session = Depends(get_db)):
    """Health check — verifies DB connectivity."""
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
    except Exception as e:
        logger.error("Health check DB error: %s", e)
        raise HTTPException(503, "Database unavailable") from e
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
    entry = get_industry_cache_entry(industry)
    data = build_industry_data(
        industry,
        entry["scores"],
        entry["insights"],
        review_counts=entry.get("review_counts"),
        data_source=entry.get("data_source"),
    )
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


@app.get("/api/industry/{industry}/export/scores.csv")
def export_industry_scores_csv(
    industry: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Dimension scores as CSV (authenticated)."""
    if industry not in INDUSTRY_CONFIG:
        raise HTTPException(404, f"Industry '{industry}' not found")
    cfg = INDUSTRY_CONFIG[industry]
    entry = get_industry_cache_entry(industry)
    scores = entry["scores"]
    dim_keys = list(cfg["dimensions"].keys())
    dim_labels = list(cfg["dimensions"].values())

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["company"] + dim_labels)
    for company in cfg["companies"]:
        row = [company]
        co_scores = scores.get(company) or {}
        for dk in dim_keys:
            v = co_scores.get(dk)
            row.append("" if v is None else v)
        w.writerow(row)

    body = buf.getvalue()
    return Response(
        content=body,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{industry}_scores.csv"',
        },
    )


@app.post("/api/run-analysis")
@limiter.limit("5/hour")
def run_analysis(request: Request, req: RunAnalysisRequest):
    if req.industry not in INDUSTRY_CONFIG:
        raise HTTPException(400, f"Industry '{req.industry}' not supported")
    try:
        return run_analysis_sync(req)
    except RuntimeError as e:
        raise HTTPException(500, str(e)) from e


@app.post("/api/run-analysis/stream")
@limiter.limit("5/hour")
def run_analysis_stream(request: Request, req: RunAnalysisRequest):
    """Server-Sent Events: progress stages then final result in last event."""

    def gen():
        try:
            for evt in iter_run_analysis_events(req):
                yield f"data: {json.dumps(evt, ensure_ascii=False)}\n\n"
        except Exception as e:
            err = json.dumps({"stage": "error", "message": str(e)})
            yield f"data: {err}\n\n"
            done = json.dumps({"stage": "complete", "result": {"status": "error", "message": str(e)}})
            yield f"data: {done}\n\n"

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
