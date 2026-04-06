"""Shared run-analysis pipeline: progress events + final JSON result (for POST and SSE)."""

from __future__ import annotations

import json
import logging
import os
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

from pydantic import BaseModel

log = logging.getLogger("insightengine.run_analysis")


# ── Helpers added for real-data enrichment ────────────────────────────────────


def _sentiment_from_reviews(
    reviews: list[dict],
    companies: list[str],
    quarters: list[str],
) -> Optional[list[dict]]:
    """
    Compute real per-quarter sentiment from dated reviews.
    Groups reviews by (company, quarter) and averages normalised ratings.
    Returns the same shape as _synthetic_sentiment() or None if reviews lack dates.
    """
    # Map "YYYY-MM" prefix → quarter label
    def _month_to_quarter(date_str: str) -> Optional[str]:
        try:
            year, month = int(date_str[:4]), int(date_str[5:7])
        except (ValueError, IndexError):
            return None
        q = (month - 1) // 3 + 1
        short_year = str(year)[2:]
        label = f"Q{q} {short_year}"
        return label if label in quarters else None

    # Accumulate ratings per (company, quarter)
    sums: dict = defaultdict(lambda: defaultdict(float))
    counts: dict = defaultdict(lambda: defaultdict(int))
    has_dates = False

    for r in reviews:
        date = r.get("date", "")
        if not date or len(date) < 7:
            continue
        has_dates = True
        company = r.get("company", "")
        if company not in companies:
            continue
        q_label = _month_to_quarter(date)
        if not q_label:
            continue
        rating = r.get("rating", 3)
        try:
            norm = (float(rating) - 3.0) / 2.0  # 1-5 → [-1, +1]
        except (TypeError, ValueError):
            continue
        sums[company][q_label] += norm
        counts[company][q_label] += 1

    if not has_dates:
        return None

    # Build output list; fill missing quarters with 0 (neutral)
    from api.industry_service import to_id  # local import to avoid circular
    result = []
    for q_label in quarters:
        row: dict = {"month": q_label}
        for company in companies:
            n = counts[company][q_label]
            row[to_id(company)] = round(sums[company][q_label] / n, 3) if n else 0.0
        result.append(row)

    # Only return if we have meaningful data (at least one company has ≥1 quarter)
    has_data = any(counts[c] for c in companies)
    return result if has_data else None


def _extract_praise_complaint_themes(
    reviews: list[dict],
    companies: list[str],
    client,
    smart_model: str,
) -> Optional[list[dict]]:
    """
    Ask the LLM to summarise top praise and complaint themes from review text.
    Returns list in same shape as the score-sum fallback:
        [{company, companyId, praise (int), complaint (int), praiseThemes, complaintThemes}]
    Returns None if client is unavailable or call fails.
    """
    if client is None or not reviews:
        return None

    from api.industry_service import to_id

    # Build a compact text corpus per company (max 30 reviews, 200 chars each)
    corpus: dict[str, list[str]] = {c: [] for c in companies}
    for r in reviews:
        co = r.get("company", "")
        if co in corpus and len(corpus[co]) < 30:
            text = str(r.get("text", ""))[:200].strip()
            if text:
                corpus[co].append(text)

    if not any(corpus.values()):
        return None

    results = []
    for company in companies:
        snippets = corpus[company]
        if not snippets:
            results.append({
                "company": company,
                "companyId": to_id(company),
                "praise": 50,
                "complaint": 30,
                "praiseThemes": [],
                "complaintThemes": [],
            })
            continue

        combined = "\n".join(f"- {s}" for s in snippets)
        prompt = (
            f"Analyse these customer reviews for {company}.\n"
            f"Respond ONLY with a JSON object:\n"
            f"{{\"praise_score\": <0-100>, \"complaint_score\": <0-100>, "
            f"\"praise_themes\": [<top 3 short phrases>], "
            f"\"complaint_themes\": [<top 3 short phrases>]}}\n\n"
            f"Reviews:\n{combined}"
        )
        try:
            resp = client.chat.completions.create(
                model=smart_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=200,
                response_format={"type": "json_object"},
            )
            parsed = json.loads(resp.choices[0].message.content)
            results.append({
                "company": company,
                "companyId": to_id(company),
                "praise": max(0, min(100, int(parsed.get("praise_score", 50)))),
                "complaint": max(0, min(100, int(parsed.get("complaint_score", 30)))),
                "praiseThemes": parsed.get("praise_themes", [])[:3],
                "complaintThemes": parsed.get("complaint_themes", [])[:3],
            })
        except Exception as exc:
            log.warning("praise/complaint LLM extraction failed for %s: %s", company, exc)
            results.append({
                "company": company,
                "companyId": to_id(company),
                "praise": 50,
                "complaint": 30,
                "praiseThemes": [],
                "complaintThemes": [],
            })

    return results if results else None


class RunAnalysisRequest(BaseModel):
    api_key: Optional[str] = None
    provider: str = "groq"
    industry: str = "crm"
    resource_keys: Optional[Dict[str, str]] = None
    use_live_sources: bool = True


def _apply_env_from_request(req: RunAnalysisRequest) -> None:
    if req.api_key:
        os.environ["GROQ_API_KEY" if req.provider == "groq" else "OPENAI_API_KEY"] = req.api_key
    if req.resource_keys:
        for k, v in req.resource_keys.items():
            if k == "trustpilot" and v:
                os.environ["TRUSTPILOT_API_KEY"] = v
            if k == "apify" and v:
                os.environ["APIFY_API_TOKEN"] = v


def iter_run_analysis_events(req: RunAnalysisRequest) -> Iterator[dict[str, Any]]:
    """
    Yields progress dicts: stage in (fetch, scoring, insights, complete, error).
    Final event is always stage=complete or stage=error.
    """
    from industry_config import INDUSTRY_CONFIG, MOCK_INSIGHTS_BY_INDUSTRY
    from pipeline import _env_int, build_client, compute_dimension_scores, generate_insights, generate_executive_brief

    from api.audience_config import AUDIENCE_CONFIG
    from api.industry_service import set_industry_cache_entry

    t0 = time.perf_counter()

    def _elapsed_ms() -> int:
        return int((time.perf_counter() - t0) * 1000)

    try:
        _apply_env_from_request(req)
        industry = req.industry
        if industry not in INDUSTRY_CONFIG:
            yield {
                "stage": "complete",
                "message": f"Industry '{industry}' not supported",
                "elapsed_ms": _elapsed_ms(),
                "result": {"status": "error", "message": f"Industry '{industry}' not supported"},
            }
            return

        cfg = INDUSTRY_CONFIG[industry]
        data_path = Path(__file__).resolve().parent.parent / cfg["data_file"]
        companies = cfg["companies"]
        focal = cfg["focal"]

        yield {"stage": "fetch", "message": "Fetching reviews…", "elapsed_ms": _elapsed_ms()}
        log.info("run_analysis fetch_start industry=%s", industry)

        reviews = None
        fetch_source = "none"
        fetch_limit = max(40, _env_int("FETCH_REVIEW_LIMIT", 150))
        if req.use_live_sources:
            try:
                from resources.adapters import fetch_reviews_for_industry

                reviews, fetch_source = fetch_reviews_for_industry(
                    industry, companies, focal, limit=fetch_limit
                )
            except Exception as e:
                log.warning("fetch_reviews failed industry=%s err=%s", industry, e)
                reviews, fetch_source = None, "none"

        if reviews is None and data_path.exists():
            reviews = json.loads(data_path.read_text(encoding="utf-8"))
            fetch_source = "local_file"

        log.info(
            "run_analysis fetch_done industry=%s source=%s count=%s elapsed_ms=%s",
            industry,
            fetch_source,
            len(reviews) if reviews else 0,
            _elapsed_ms(),
        )

        if reviews is None or not reviews:
            scores, insights = cfg["mock_scores"], MOCK_INSIGHTS_BY_INDUSTRY[industry]
            set_industry_cache_entry(
                industry,
                scores=dict(scores),
                insights=list(insights),
                reviews=None,
                data_source="mock_no_reviews",
            )
            msg = f"Using mock data for {industry} (no review file or live source)."
            yield {
                "stage": "complete",
                "message": msg,
                "elapsed_ms": _elapsed_ms(),
                "result": {"status": "complete", "message": msg},
            }
            log.info("run_analysis done industry=%s path=mock_no_reviews total_ms=%s", industry, _elapsed_ms())
            return

        client, fast, smart, provider_name = build_client()
        if client is None:
            scores, insights = cfg["mock_scores"], MOCK_INSIGHTS_BY_INDUSTRY[industry]
            set_industry_cache_entry(
                industry,
                scores=dict(scores),
                insights=list(insights),
                reviews=reviews,
                data_source=f"mock_scores_{fetch_source}",
            )
            msg = "Using mock data (no API key). Set GROQ_API_KEY for live analysis."
            yield {
                "stage": "complete",
                "message": msg,
                "elapsed_ms": _elapsed_ms(),
                "result": {"status": "complete", "message": msg},
            }
            log.info("run_analysis done industry=%s path=no_client total_ms=%s", industry, _elapsed_ms())
            return

        yield {"stage": "scoring", "message": "Scoring reviews with LLM…", "elapsed_ms": _elapsed_ms()}
        t_score = time.perf_counter()
        scores = compute_dimension_scores(
            reviews,
            client,
            fast,
            use_mock=False,
            companies=cfg["companies"],
            dimensions=cfg["dimensions"],
            mock_scores=cfg["mock_scores"],
        )
        log.info(
            "run_analysis scoring_done industry=%s ms=%s",
            industry,
            int((time.perf_counter() - t_score) * 1000),
        )

        yield {"stage": "insights", "message": "Generating strategic insights…", "elapsed_ms": _elapsed_ms()}
        t_ins = time.perf_counter()
        use_cases = []
        for ac in AUDIENCE_CONFIG.values():
            use_cases.extend(uc["question"] for uc in ac.get("use_cases", []))
        insights = generate_insights(
            scores,
            client,
            smart,
            vertical=cfg["name"],
            focal=cfg["focal"],
            competitors=[c for c in cfg["companies"] if c != cfg["focal"]],
            use_cases=use_cases if use_cases else None,
        )
        log.info(
            "run_analysis insights_done industry=%s ms=%s",
            industry,
            int((time.perf_counter() - t_ins) * 1000),
        )

        executive_brief = generate_executive_brief(
            scores,
            client,
            smart,
            vertical=cfg["name"],
            focal=cfg["focal"],
            competitors=[c for c in cfg["companies"] if c != cfg["focal"]],
        )
        log.info("run_analysis executive_brief generated industry=%s", industry)

        # ── Real enrichments ──────────────────────────────────────────────────
        yield {"stage": "enriching", "message": "Computing real sentiment & themes…", "elapsed_ms": _elapsed_ms()}

        # 1) Sentiment trends from dated reviews (most accurate — actual ratings over time)
        from api.industry_service import SENTIMENT_TREND_QUARTERS
        sentiment_trends = _sentiment_from_reviews(reviews, companies, SENTIMENT_TREND_QUARTERS)
        trend_source = "reviews"

        # 2) Fall back to SerpAPI Google Trends if reviews lack dates
        if sentiment_trends is None:
            try:
                from resources.adapters import fetch_sentiment_trends_for_industry
                sentiment_trends, trend_source = fetch_sentiment_trends_for_industry(
                    companies, SENTIMENT_TREND_QUARTERS
                )
            except Exception as exc:
                log.warning("serpapi trends fetch failed: %s", exc)
                trend_source = "none"

        log.info("run_analysis trends source=%s industry=%s", trend_source, industry)

        # 3) SerpAPI share-of-voice (Google Trends relative interest)
        sov_interest = None
        try:
            from resources.adapters import fetch_share_of_voice_for_industry
            sov_interest = fetch_share_of_voice_for_industry(companies)
            if sov_interest:
                log.info("run_analysis sov fetched industry=%s", industry)
        except Exception as exc:
            log.warning("serpapi sov fetch failed: %s", exc)

        # 4) LLM-extracted praise/complaint themes from real review text
        praise_complaint_themes = _extract_praise_complaint_themes(reviews, companies, client, smart)
        if praise_complaint_themes:
            log.info("run_analysis praise/complaint themes extracted industry=%s", industry)

        # 5) Google News headlines for focal company (investor audience)
        news_headlines = None
        try:
            from resources.adapters import fetch_news_for_industry
            news_headlines = fetch_news_for_industry(focal, limit=8)
            if news_headlines:
                log.info("run_analysis news fetched industry=%s count=%d", industry, len(news_headlines))
        except Exception as exc:
            log.warning("news fetch failed: %s", exc)

        # 6) Google Finance stock quotes (investor audience)
        finance_data = None
        try:
            from resources.adapters import fetch_finance_for_industry
            finance_data = fetch_finance_for_industry(companies)
            if finance_data:
                log.info("run_analysis finance fetched industry=%s companies=%s", industry, list(finance_data.keys()))
        except Exception as exc:
            log.warning("finance fetch failed: %s", exc)

        # 7) Glassdoor employee rating snippets (companies + customers audience)
        glassdoor_data = None
        try:
            from resources.adapters import fetch_glassdoor_for_industry
            glassdoor_data = fetch_glassdoor_for_industry(companies)
            if glassdoor_data:
                log.info("run_analysis glassdoor fetched industry=%s companies=%s", industry, list(glassdoor_data.keys()))
        except Exception as exc:
            log.warning("glassdoor fetch failed: %s", exc)

        set_industry_cache_entry(
            industry,
            scores=scores,
            insights=insights,
            reviews=reviews,
            data_source=f"live_pipeline_{fetch_source}",
            sentiment_trends=sentiment_trends,
            sov_interest=sov_interest,
            praise_complaint_themes=praise_complaint_themes,
            news_headlines=news_headlines,
            finance_data=finance_data,
            glassdoor_data=glassdoor_data,
            executive_brief=executive_brief or None,
        )
        msg = f"Analysis complete for {industry} (reviews: {fetch_source}). Refresh the dashboard."
        yield {
            "stage": "complete",
            "message": msg,
            "elapsed_ms": _elapsed_ms(),
            "result": {"status": "complete", "message": msg},
        }
        log.info(
            "run_analysis done industry=%s provider=%s fetch=%s total_ms=%s",
            industry,
            provider_name,
            fetch_source,
            _elapsed_ms(),
        )
    except Exception as e:
        log.exception("run_analysis failed industry=%s", req.industry)
        yield {
            "stage": "error",
            "message": str(e),
            "elapsed_ms": _elapsed_ms(),
        }
        yield {"stage": "complete", "result": {"status": "error", "message": str(e)}}


def run_analysis_sync(req: RunAnalysisRequest) -> dict:
    """Run pipeline and return the final API result dict (raises on unhandled error in iterator)."""
    result: dict | None = None
    for evt in iter_run_analysis_events(req):
        if evt.get("stage") == "complete" and "result" in evt:
            result = evt["result"]
    if result is None:
        raise RuntimeError("Analysis produced no result")
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Analysis failed"))
    return result
