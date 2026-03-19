"""
InsightEngine API — Backend for MarketLens UI
Connects the Figma design to the pipeline.py analysis engine.
Supports all industries: crm, food-delivery, ride-sharing, saas.
"""

import json
import os
import sys
from pathlib import Path

# Load .env (GROQ_API_KEY, etc.) from project root
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent))
from api.audience_config import AUDIENCE_CONFIG
from industry_config import INDUSTRY_CONFIG, MOCK_INSIGHTS_BY_INDUSTRY
from pipeline import (
    build_client,
    compute_dimension_scores,
    generate_insights,
)

QUARTERS = ["Q1 24", "Q2 24", "Q3 24", "Q4 24", "Q1 25", "Q2 25", "Q3 25", "Q4 25", "Q1 26"]


def to_id(name: str) -> str:
    return name.lower().replace(" ", "").replace("-", "")


def _synthetic_sentiment(scores: dict, companies: list) -> list:
    """Generate synthetic sentiment trends from dimension scores (avg of all dims, scaled to -1..1)."""
    trends = []
    for i, q in enumerate(QUARTERS[-6:]):
        row = {"month": q}
        for c in companies:
            sc = scores.get(c, {})
            vals = [v for v in sc.values() if isinstance(v, (int, float))]
            avg = sum(vals) / len(vals) if vals else 70
            # Slight variation over time
            jitter = (i - 2) * 1.5
            row[to_id(c)] = round((avg / 50 - 1) + jitter / 100, 2)
        trends.append(row)
    return trends


def build_industry_data(industry: str, scores: dict, insights: list) -> dict:
    """Transform pipeline output to Figma IndustryData format for any industry."""
    cfg = INDUSTRY_CONFIG.get(industry)
    if not cfg:
        raise HTTPException(404, f"Industry '{industry}' not found")

    companies_list = cfg["companies"]
    dims = cfg["dimensions"]
    colors = cfg.get("colors", {})

    # Value dimension for price/perceivedValue (industry-specific key)
    value_key = next((k for k in dims if "value" in k.lower() or "pricing" in k.lower()), list(dims.keys())[0])

    companies = []
    for name in companies_list:
        cid = to_id(name)
        sc = scores.get(name, {})
        value_score = sc.get(value_key, 50)
        perceived_value = value_score / 10
        price = max(1, min(10, 10 - value_score / 12))
        vals = [v for v in sc.values() if isinstance(v, (int, float))]
        avg = sum(vals) / len(vals) if vals else 70
        overall_sentiment = round(avg / 50 - 1, 2)
        review_count = 50000 + hash(name) % 100000  # Synthetic
        companies.append({
            "id": cid,
            "name": name,
            "price": round(price, 1),
            "perceivedValue": round(perceived_value, 1),
            "overallSentiment": overall_sentiment,
            "reviewCount": review_count,
            "color": colors.get(name, "#64748b"),
        })

    dimensions = []
    for dim_key, dim_label in dims.items():
        scores_by_co = {to_id(c): scores.get(c, {}).get(dim_key, 50) for c in companies_list}
        importance = 90 if "support" in dim_key or "value" in dim_key or "pricing" in dim_key else 85
        dimensions.append({
            "name": dim_label,
            "importance": importance,
            "scores": scores_by_co,
        })

    sentiment_trends = _synthetic_sentiment(scores, companies_list)

    audience_map = {"Companies": "companies", "Investors": "investors", "Customers": "customers"}
    insights_by_audience = {"investors": [], "companies": [], "customers": []}
    for ins in insights:
        aud = ins.get("audience", "Companies")
        key = audience_map.get(aud, "companies")
        conf = ins.get("confidence", "Medium")
        impact = "high" if conf == "High" else "medium" if conf == "Medium" else "low"
        insights_by_audience[key].append({
            "type": "trend",
            "title": ins.get("title", ""),
            "description": ins.get("body", ""),
            "impact": impact,
            "metrics": [ins.get("action", "")] if ins.get("action") else [],
        })

    # Chart data: praise vs complaint themes (synthetic from dimension scores)
    theme_names = list(dims.values())[:6]
    praise_complaint = []
    for name in companies_list:
        cid = to_id(name)
        sc = scores.get(name, {})
        praise_sum = sum(v for v in sc.values() if isinstance(v, (int, float)) and v >= 60)
        complaint_sum = sum(100 - v for v in sc.values() if isinstance(v, (int, float)) and v < 60)
        praise_complaint.append({
            "company": name,
            "companyId": cid,
            "praise": max(10, int(praise_sum / 6)) if sc else 50,
            "complaint": max(5, int(complaint_sum / 6)) if sc else 30,
        })

    # Share of voice (review counts)
    total_reviews = sum(c["reviewCount"] for c in companies)
    share_of_voice = [
        {"name": c["name"], "size": c["reviewCount"], "value": round(100 * c["reviewCount"] / total_reviews, 1)}
        for c in companies
    ]

    # Churn flows (synthetic: migration between competitors)
    churn_flows = []
    for i, src in enumerate(companies_list[:4]):
        for j, tgt in enumerate(companies_list[:4]):
            if i != j:
                churn_flows.append({
                    "source": src,
                    "target": tgt,
                    "value": 5 + (hash(f"{src}{tgt}") % 15),
                })

    # Dimension deltas vs category benchmark (for waterfall)
    cat_avg = {}
    for dim_key in dims:
        vals = [scores.get(c, {}).get(dim_key, 50) for c in companies_list]
        cat_avg[dim_key] = sum(v for v in vals if isinstance(v, (int, float))) / max(len(vals), 1)
    dimension_deltas = []
    for dim_key, dim_label in dims.items():
        bench = cat_avg.get(dim_key, 70)
        for name in companies_list:
            sc = scores.get(name, {})
            val = sc.get(dim_key, 50)
            delta = val - bench if isinstance(val, (int, float)) else 0
            dimension_deltas.append({
                "dimension": dim_label,
                "company": name,
                "companyId": to_id(name),
                "score": val,
                "benchmark": round(bench, 1),
                "delta": round(delta, 1),
            })

    return {
        "companies": companies,
        "dimensions": dimensions,
        "sentimentTrends": sentiment_trends,
        "insights": insights_by_audience,
        "praiseComplaintThemes": praise_complaint,
        "shareOfVoice": share_of_voice,
        "churnFlows": churn_flows,
        "dimensionDeltas": dimension_deltas,
        "_meta": {
            "industry": industry,
            "totalReviews": total_reviews,
            "totalInsights": sum(len(v) for v in insights_by_audience.values()),
        },
    }


# ── Per-industry cached state ─────────────────────────────────────────────────
_cache: dict[str, tuple[dict, list]] = {}


def _get_industry_state(industry: str) -> tuple[dict, list]:
    if industry not in _cache:
        cfg = INDUSTRY_CONFIG[industry]
        _cache[industry] = (dict(cfg["mock_scores"]), list(MOCK_INSIGHTS_BY_INDUSTRY[industry]))
    return _cache[industry]


app = FastAPI(title="InsightEngine API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174", "http://localhost:5175", "http://127.0.0.1:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/api/industry/{industry}")
def get_industry_data(industry: str):
    if industry not in INDUSTRY_CONFIG:
        raise HTTPException(404, f"Industry '{industry}' not found")
    scores, insights = _get_industry_state(industry)
    return build_industry_data(industry, scores, insights)


@app.get("/api/industry/{industry}/audience/{audience}")
def get_industry_audience(industry: str, audience: str):
    if audience not in ("investors", "companies", "customers"):
        raise HTTPException(400, "Audience must be investors, companies, or customers")
    data = get_industry_data(industry)
    return data


class RunAnalysisRequest(BaseModel):
    api_key: str | None = None
    provider: str = "groq"
    industry: str = "crm"
    resource_keys: dict[str, str] | None = None  # e.g. {"apify": "...", "kaggle": "..."}
    use_live_sources: bool = True  # Try Kaggle/Apify before falling back to data_file


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
    if req.use_live_sources:
        try:
            from resources.adapters import fetch_reviews_for_industry
            reviews = fetch_reviews_for_industry(industry, companies, focal, limit=200)
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
            return {"status": "complete", "message": f"Using mock data (no API key). Set GROQ_API_KEY for live analysis."}

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
