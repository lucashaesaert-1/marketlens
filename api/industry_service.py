"""Industry payload building and per-industry score/insight cache (shared by API routes)."""

import json
import sys
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import HTTPException

from industry_config import INDUSTRY_CONFIG, MOCK_INSIGHTS_BY_INDUSTRY

QUARTERS = ["Q1 24", "Q2 24", "Q3 24", "Q4 24", "Q1 25", "Q2 25", "Q3 25", "Q4 25", "Q1 26"]
SENTIMENT_TREND_QUARTERS = QUARTERS[-6:]  # The 6 quarters shown in the chart


def to_id(name: str) -> str:
    return name.lower().replace(" ", "").replace("-", "")


def count_reviews_by_company(reviews: list, companies: list[str]) -> dict[str, int]:
    counts = {c: 0 for c in companies}
    for r in reviews:
        co = r.get("company")
        if co in counts:
            counts[co] += 1
    return counts


def load_review_counts_from_industry_file(industry: str) -> Optional[dict[str, int]]:
    """Real review counts from the on-disk sample JSON for this industry (if present)."""
    cfg = INDUSTRY_CONFIG.get(industry)
    if not cfg:
        return None
    path = Path(__file__).resolve().parent.parent / cfg["data_file"]
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, list):
        return None
    return count_reviews_by_company(data, list(cfg["companies"]))


def _synthetic_sentiment(scores: dict, companies: list) -> list:
    trends = []
    for i, q in enumerate(QUARTERS[-6:]):
        row = {"month": q}
        for c in companies:
            sc = scores.get(c, {})
            vals = [v for v in sc.values() if isinstance(v, (int, float))]
            avg = sum(vals) / len(vals) if vals else 70
            jitter = (i - 2) * 1.5
            row[to_id(c)] = round((avg / 50 - 1) + jitter / 100, 2)
        trends.append(row)
    return trends


def build_industry_data(
    industry: str,
    scores: dict,
    insights: list,
    *,
    review_counts: Optional[dict[str, int]] = None,
    data_source: Optional[str] = None,
    sentiment_trends: Optional[list] = None,
    praise_complaint_themes: Optional[list] = None,
    sov_interest: Optional[dict[str, int]] = None,
    news_headlines: Optional[list] = None,
    finance_data: Optional[dict] = None,
    glassdoor_data: Optional[dict] = None,
    executive_brief: Optional[str] = None,
    customer_recommendations: Optional[list] = None,
    competitor_gap: Optional[list] = None,
) -> dict:
    cfg = INDUSTRY_CONFIG.get(industry)
    if not cfg:
        raise HTTPException(404, f"Industry '{industry}' not found")

    companies_list = cfg["companies"]
    dims = cfg["dimensions"]
    colors = cfg.get("colors", {})
    value_key = next((k for k in dims if "value" in k.lower() or "pricing" in k.lower()), list(dims.keys())[0])

    companies = []
    for name in companies_list:
        cid = to_id(name)
        sc = scores.get(name, {})
        value_score = sc.get(value_key) or 50
        perceived_value = value_score / 10
        price = max(1, min(10, 10 - value_score / 12))
        vals = [v for v in sc.values() if isinstance(v, (int, float))]
        avg = sum(vals) / len(vals) if vals else 70
        overall_sentiment = round(avg / 50 - 1, 2)
        if review_counts is not None and name in review_counts and review_counts[name] > 0:
            review_count = review_counts[name]
        elif sov_interest is not None and name in sov_interest:
            # SerpAPI Google Trends interest (0-100) scaled to a plausible review-count range.
            # Not a real count but proportional to real search volume — far better than hash().
            review_count = 10000 + sov_interest[name] * 1500
        else:
            review_count = 50000 + hash(name) % 100000
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

    # Use real trends if provided (from SerpAPI Google Trends or dated-review aggregation);
    # fall back to the synthetic formula only when no real data is available.
    if sentiment_trends is None:
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
            "source": "pipeline",
        })

    # Use real LLM-extracted themes when available (passed from pipeline);
    # fall back to the score-sum formula only when no real themes exist.
    if praise_complaint_themes is not None:
        praise_complaint = praise_complaint_themes
    else:
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

    total_reviews = sum(c["reviewCount"] for c in companies) or 1
    share_of_voice = [
        {"name": c["name"], "size": c["reviewCount"], "value": round(100 * c["reviewCount"] / total_reviews, 1)}
        for c in companies
    ]

    churn_flows = []
    for i, src in enumerate(companies_list[:4]):
        for j, tgt in enumerate(companies_list[:4]):
            if i != j:
                churn_flows.append({
                    "source": src,
                    "target": tgt,
                    "value": 5 + (hash(f"{src}{tgt}") % 15),
                })

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

    is_mock = not bool(review_counts)
    payload: dict = {
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
            "dataSource": data_source or "unknown",
            "reviewCountsFromDataset": bool(review_counts),
            "isMock": is_mock,
        },
    }
    # Optional real-data enrichments — only included when data was fetched
    if news_headlines is not None:
        payload["newsHeadlines"] = news_headlines
    if finance_data is not None:
        payload["financeData"] = finance_data
    if glassdoor_data is not None:
        payload["glassdoorData"] = glassdoor_data
    if executive_brief:
        payload["executiveBrief"] = executive_brief
    if customer_recommendations:
        payload["customerRecommendations"] = customer_recommendations
    if competitor_gap:
        payload["competitorGap"] = competitor_gap
    return payload


_cache: dict[str, dict[str, Any]] = {}


def _try_fetch_serpapi_enrichments(
    industry: str,
    companies: list,
    focal: str = "",
) -> dict[str, Any]:
    """
    Eagerly fetch SerpAPI enrichments on first cache miss.
    Returns keys: sentiment_trends, sov_interest, news_headlines, finance_data, glassdoor_data.
    All may be None if SerpAPI key not set or calls fail.
    """
    enrichments: dict[str, Any] = {
        "sentiment_trends": None,
        "sov_interest": None,
        "news_headlines": None,
        "finance_data": None,
        "glassdoor_data": None,
    }
    try:
        from resources.adapters import (
            fetch_sentiment_trends_for_industry,
            fetch_share_of_voice_for_industry,
            fetch_news_for_industry,
            fetch_finance_for_industry,
            fetch_glassdoor_for_industry,
        )
    except ImportError:
        return enrichments

    trends, _ = fetch_sentiment_trends_for_industry(companies, SENTIMENT_TREND_QUARTERS)
    enrichments["sentiment_trends"] = trends

    sov = fetch_share_of_voice_for_industry(companies)
    enrichments["sov_interest"] = sov

    if focal:
        try:
            enrichments["news_headlines"] = fetch_news_for_industry(focal, limit=8)
        except Exception:
            pass

    try:
        enrichments["finance_data"] = fetch_finance_for_industry(companies)
    except Exception:
        pass

    try:
        enrichments["glassdoor_data"] = fetch_glassdoor_for_industry(companies)
    except Exception:
        pass

    return enrichments


def get_industry_cache_entry(industry: str) -> dict[str, Any]:
    """Scores/insights plus optional real review counts, trends, and provenance label."""
    if industry not in _cache:
        cfg = INDUSTRY_CONFIG.get(industry)
        if not cfg:
            raise HTTPException(404, f"Industry '{industry}' not found")
        rc = load_review_counts_from_industry_file(industry)
        companies = list(cfg.get("companies", []))
        focal = cfg.get("focal", "")
        enrichments = _try_fetch_serpapi_enrichments(industry, companies, focal=focal)
        _cache[industry] = {
            "scores": dict(cfg["mock_scores"]),
            "insights": list(MOCK_INSIGHTS_BY_INDUSTRY.get(industry, [])),
            "review_counts": rc,
            "data_source": "sample_reviews_file" if rc else "template_scores",
            "sentiment_trends": enrichments["sentiment_trends"],
            "sov_interest": enrichments["sov_interest"],
            "praise_complaint_themes": None,
            "news_headlines": enrichments["news_headlines"],
            "finance_data": enrichments["finance_data"],
            "glassdoor_data": enrichments["glassdoor_data"],
            "executive_brief": None,
            "customer_recommendations": None,
            "competitor_gap": None,
        }
    return _cache[industry]


def set_industry_cache_entry(
    industry: str,
    *,
    scores: dict,
    insights: list,
    reviews: Optional[list] = None,
    review_counts: Optional[dict[str, int]] = None,
    data_source: str = "pipeline",
    sentiment_trends: Optional[list] = None,
    sov_interest: Optional[dict[str, int]] = None,
    praise_complaint_themes: Optional[list] = None,
    news_headlines: Optional[list] = None,
    finance_data: Optional[dict] = None,
    glassdoor_data: Optional[dict] = None,
    executive_brief: Optional[str] = None,
    customer_recommendations: Optional[list] = None,
    competitor_gap: Optional[list] = None,
) -> None:
    cfg = INDUSTRY_CONFIG.get(industry) or {}
    comps = list(cfg.get("companies") or [])
    if review_counts is not None:
        rc = review_counts
    elif reviews is not None and comps:
        rc = count_reviews_by_company(reviews, comps)
    else:
        rc = load_review_counts_from_industry_file(industry)

    # Keep whatever was already cached for fields not passed in
    existing = _cache.get(industry, {})
    final_trends = sentiment_trends if sentiment_trends is not None else existing.get("sentiment_trends")
    final_sov = sov_interest if sov_interest is not None else existing.get("sov_interest")
    final_pc = praise_complaint_themes if praise_complaint_themes is not None else existing.get("praise_complaint_themes")
    final_news = news_headlines if news_headlines is not None else existing.get("news_headlines")
    final_finance = finance_data if finance_data is not None else existing.get("finance_data")
    final_glassdoor = glassdoor_data if glassdoor_data is not None else existing.get("glassdoor_data")
    final_brief = executive_brief if executive_brief is not None else existing.get("executive_brief")
    final_recs = customer_recommendations if customer_recommendations is not None else existing.get("customer_recommendations")
    final_gap = competitor_gap if competitor_gap is not None else existing.get("competitor_gap")

    _cache[industry] = {
        "scores": scores,
        "insights": insights,
        "review_counts": rc,
        "data_source": data_source,
        "sentiment_trends": final_trends,
        "sov_interest": final_sov,
        "praise_complaint_themes": final_pc,
        "news_headlines": final_news,
        "finance_data": final_finance,
        "glassdoor_data": final_glassdoor,
        "executive_brief": final_brief,
        "customer_recommendations": final_recs,
        "competitor_gap": final_gap,
    }


def get_industry_state(industry: str) -> tuple[dict, list]:
    e = get_industry_cache_entry(industry)
    return e["scores"], e["insights"]


def merge_personalization(base: dict, personalization: Optional[dict], audience: str) -> dict:
    """Attach personalization and merge chat insights into the selected audience list with labels."""
    if not personalization:
        return base
    out = json_deep_copy(base)
    out["personalization"] = personalization
    chat_insights = personalization.get("insights_from_chat") or []
    aud_key = audience if audience in ("investors", "companies", "customers") else "investors"
    merged = list(out["insights"].get(aud_key, []))
    for ci in chat_insights:
        merged.append({
            "type": "trend",
            "title": ci.get("title", ""),
            "description": ci.get("description", ""),
            "impact": ci.get("impact", "medium"),
            "metrics": [],
            "source": "chat",
        })
    out["insights"] = {**out["insights"], aud_key: merged}
    return out


def json_deep_copy(d: dict) -> dict:
    import copy

    return copy.deepcopy(d)
