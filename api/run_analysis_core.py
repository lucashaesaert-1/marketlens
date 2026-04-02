"""Shared run-analysis pipeline: progress events + final JSON result (for POST and SSE)."""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

from pydantic import BaseModel

log = logging.getLogger("insightengine.run_analysis")


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
    from pipeline import _env_int, build_client, compute_dimension_scores, generate_insights

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

        set_industry_cache_entry(
            industry,
            scores=scores,
            insights=insights,
            reviews=reviews,
            data_source=f"live_pipeline_{fetch_source}",
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
