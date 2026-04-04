"""
Data source adapters. When API keys are configured, fetch real data.
Otherwise return None (caller uses mock/fallback).

Primary sources (no Trustpilot key needed):
  - Kaggle: Free datasets for ride-sharing, food-delivery, e-commerce, restaurants
  - Apify: G2, Capterra, Trustpilot via APIFY_API_TOKEN
  - SerpAPI: Google Maps Reviews (restaurants/hospitality/travel) via SER_API
             Google Trends (sentiment timeline + share-of-voice) via SER_API
  - Scrapers: G2, Capterra (fallback when Apify not configured)
"""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

# ── Kaggle (replaces Trustpilot for many industries) ───────────────────────────


def kaggle_fetch_reviews(
    industry: str,
    companies: list,
    limit: int = 200,
    data_dir: Optional[Path] = None,
) -> Optional[list[dict]]:
    """
    Load reviews from Kaggle datasets. Requires kaggle package and ~/.kaggle/kaggle.json.
    Supported industries: ride-sharing, food-delivery, e-commerce, restaurants.
    Returns None if Kaggle not configured or industry not supported.
    """
    try:
        from resources.kaggle_loader import load_kaggle_dataset
    except ImportError:
        try:
            from .kaggle_loader import load_kaggle_dataset
        except ImportError:
            return None

    base = data_dir or Path(__file__).parent.parent / "data"
    return load_kaggle_dataset(industry, companies, data_dir=base / "kaggle", limit=limit)


# ── Apify (G2, Capterra, Trustpilot — no Trustpilot API key needed) ─────────────


def apify_fetch_reviews(
    company: str,
    platform: str = "g2",
    api_token: Optional[str] = None,
    limit: int = 50,
) -> Optional[list[dict]]:
    """
    Fetch reviews via Apify. Set APIFY_API_TOKEN in .env.
    Platforms: g2, capterra, trustpilot.
    """
    try:
        from resources.apify_adapter import apify_fetch_reviews as _fetch
    except ImportError:
        try:
            from .apify_adapter import apify_fetch_reviews as _fetch
        except ImportError:
            return None
    return _fetch(company, platform, api_token, limit)


# ── Scrapers (G2, Capterra — fallback when Apify not configured) ────────────


def g2_fetch_reviews(product_slug: str, limit: int = 30) -> Optional[list[dict]]:
    """Scrape G2 reviews. Delegates to Apify if APIFY_API_TOKEN set."""
    try:
        from resources.scrapers.g2_scraper import g2_scrape_reviews
    except ImportError:
        try:
            from .scrapers.g2_scraper import g2_scrape_reviews
        except ImportError:
            return None
    return g2_scrape_reviews(product_slug, limit=limit)


def capterra_fetch_reviews(product_slug: str, limit: int = 30) -> Optional[list[dict]]:
    """Scrape Capterra reviews. Delegates to Apify if APIFY_API_TOKEN set."""
    try:
        from resources.scrapers.capterra_scraper import capterra_scrape_reviews
    except ImportError:
        try:
            from .scrapers.capterra_scraper import capterra_scrape_reviews
        except ImportError:
            return None
    return capterra_scrape_reviews(product_slug, limit=limit)


# ── Unified fetch: tries Kaggle → Apify → local file ────────────────────────


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)).strip())
    except ValueError:
        return default


def fetch_reviews_for_industry(
    industry: str,
    companies: list,
    focal_company: str,
    limit: int = 200,
) -> tuple[Optional[list[dict]], str]:
    """
    Unified review fetcher. Returns (reviews, source_tag).

    Order:
    1. Kaggle datasets (ride-sharing, food-delivery, e-commerce, restaurants) → "kaggle"
    2. SerpAPI Google Maps (restaurants, hospitality, travel) → "serpapi_maps"
    3. Apify G2 scrapes for multiple competitors if APIFY_API_TOKEN is set → "apify"
    4. No live data → (None, "none") — caller should load data_file (local JSON)
    """
    # 1) Kaggle (real public datasets)
    kaggle_industries = ("ride-sharing", "food-delivery", "e-commerce", "restaurants")
    if industry in kaggle_industries:
        reviews = kaggle_fetch_reviews(industry, companies, limit=limit)
        if reviews:
            return reviews, "kaggle"

    # 2) SerpAPI Google Maps — real customer reviews for location-based industries
    ser_key = os.environ.get("SER_API") or os.environ.get("SERPAPI_API_KEY")
    if ser_key:
        try:
            from resources.serpapi_adapter import (
                GOOGLE_MAPS_INDUSTRIES,
                fetch_google_maps_reviews_for_industry,
            )
        except ImportError:
            try:
                from .serpapi_adapter import (
                    GOOGLE_MAPS_INDUSTRIES,
                    fetch_google_maps_reviews_for_industry,
                )
            except ImportError:
                GOOGLE_MAPS_INDUSTRIES = set()
                fetch_google_maps_reviews_for_industry = None  # type: ignore[assignment]

        if fetch_google_maps_reviews_for_industry and industry in GOOGLE_MAPS_INDUSTRIES:
            per_co = max(20, limit // max(len(companies), 1))
            maps_reviews = fetch_google_maps_reviews_for_industry(
                companies, industry, limit_per_company=per_co
            )
            if maps_reviews:
                for i, r in enumerate(maps_reviews):
                    co = r.get("company", "x")
                    r["id"] = f"{to_slug(co)}_gmaps_{i}"[:120]
                return maps_reviews[:limit], "serpapi_maps"

    # 3) Apify — fetch several competitors (not only focal) for real multi-brand coverage
    token = os.environ.get("APIFY_API_TOKEN")
    if token and companies:
        max_cos = max(1, min(len(companies), _env_int("APIFY_MAX_COMPANIES", 6)))
        targets = companies[:max_cos]
        n = len(targets)
        per_co = max(20, min(100, limit // n))

        def _fetch_one(company_name: str) -> list[dict]:
            batch = apify_fetch_reviews(company_name, platform="g2", api_token=token, limit=per_co)
            return batch or []

        merged: list[dict] = []
        workers = min(_env_int("APIFY_PARALLEL_ACTORS", 3), n)
        if workers <= 1:
            for co in targets:
                merged.extend(_fetch_one(co))
        else:
            with ThreadPoolExecutor(max_workers=workers) as ex:
                futs = [ex.submit(_fetch_one, co) for co in targets]
                for fut in as_completed(futs):
                    merged.extend(fut.result())

        # Stable unique ids across companies
        for i, r in enumerate(merged):
            co = r.get("company", "x")
            rid = r.get("id", i)
            r["id"] = f"{to_slug(co)}_{rid}_{i}"[:120]

        if merged:
            return merged[:limit], "apify"

    return None, "none"


# ── Sentiment trends ──────────────────────────────────────────────────────────


def fetch_sentiment_trends_for_industry(
    companies: list,
    quarters: list,
) -> tuple[Optional[list[dict]], str]:
    """
    Fetch real sentiment/interest timeline for the companies.

    Order:
    1. SerpAPI Google Trends — returns real search-interest-over-time → "serpapi_trends"
    2. Falls back to (None, "none") — caller uses _synthetic_sentiment()
    """
    ser_key = os.environ.get("SER_API") or os.environ.get("SERPAPI_API_KEY")
    if not ser_key:
        return None, "none"

    try:
        from resources.serpapi_adapter import fetch_google_trends_timeline
    except ImportError:
        try:
            from .serpapi_adapter import fetch_google_trends_timeline
        except ImportError:
            return None, "none"

    trends = fetch_google_trends_timeline(companies, quarters)
    if trends:
        return trends, "serpapi_trends"
    return None, "none"


def fetch_news_for_industry(
    focal_company: str,
    limit: int = 8,
) -> Optional[list[dict]]:
    """
    Fetch recent Google News headlines for the focal company (investor audience).
    Returns list of {title, source, date, snippet, sentiment_hint} or None.
    """
    ser_key = os.environ.get("SER_API") or os.environ.get("SERPAPI_API_KEY")
    if not ser_key:
        return None

    try:
        from resources.serpapi_adapter import fetch_google_news_headlines
    except ImportError:
        try:
            from .serpapi_adapter import fetch_google_news_headlines
        except ImportError:
            return None

    return fetch_google_news_headlines(focal_company, limit=limit)


def fetch_finance_for_industry(
    companies: list,
) -> Optional[dict[str, dict]]:
    """
    Fetch live stock quotes for companies (investor audience).
    Uses Alpha Vantage when Alpha_vantage key is set,
    falls back to SerpAPI Google Finance if only SER_API is set.
    Returns {company_name: {ticker, price, change, pct_change, currency}} or None.
    """
    # Prefer Alpha Vantage
    if os.environ.get("Alpha_vantage") or os.environ.get("ALPHA_VANTAGE_API_KEY"):
        try:
            from resources.alphavantage_adapter import fetch_finance_data_for_companies as _av_fetch
        except ImportError:
            try:
                from .alphavantage_adapter import fetch_finance_data_for_companies as _av_fetch
            except ImportError:
                _av_fetch = None  # type: ignore[assignment]
        if _av_fetch:
            return _av_fetch(companies)

    # Fallback: SerpAPI Google Finance
    ser_key = os.environ.get("SER_API") or os.environ.get("SERPAPI_API_KEY")
    if not ser_key:
        return None

    try:
        from resources.serpapi_adapter import fetch_finance_data_for_companies
    except ImportError:
        try:
            from .serpapi_adapter import fetch_finance_data_for_companies
        except ImportError:
            return None

    return fetch_finance_data_for_companies(companies)


def fetch_glassdoor_for_industry(
    companies: list,
) -> Optional[dict[str, dict]]:
    """
    Fetch Glassdoor employee-rating snippets for companies (companies/customers audience).
    Returns {company_name: {rating, snippet}} or None.
    """
    ser_key = os.environ.get("SER_API") or os.environ.get("SERPAPI_API_KEY")
    if not ser_key:
        return None

    try:
        from resources.serpapi_adapter import fetch_glassdoor_data_for_companies
    except ImportError:
        try:
            from .serpapi_adapter import fetch_glassdoor_data_for_companies
        except ImportError:
            return None

    return fetch_glassdoor_data_for_companies(companies)


def fetch_share_of_voice_for_industry(
    companies: list,
) -> Optional[dict[str, int]]:
    """
    Fetch real share-of-voice data via SerpAPI Google Trends.
    Returns {company_name: relative_interest_0_to_100} or None.
    """
    ser_key = os.environ.get("SER_API") or os.environ.get("SERPAPI_API_KEY")
    if not ser_key:
        return None

    try:
        from resources.serpapi_adapter import fetch_google_trends_share_of_voice
    except ImportError:
        try:
            from .serpapi_adapter import fetch_google_trends_share_of_voice
        except ImportError:
            return None

    return fetch_google_trends_share_of_voice(companies)


def to_slug(name: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in str(name).lower())[:40]


# ── Legacy Trustpilot (kept for backwards compat; user cannot get key) ─────────


def trustpilot_fetch_reviews(
    domain: str,
    api_key: Optional[str] = None,
    limit: int = 20,
) -> Optional[list[dict]]:
    """
    Fetch reviews from Trustpilot Business API.
    DEPRECATED: Use apify_fetch_reviews(company, platform="trustpilot") instead —
    no Trustpilot API key needed when using Apify.
    """
    key = api_key or os.environ.get("TRUSTPILOT_API_KEY")
    if not key:
        # Use Apify as alternative (no Trustpilot key needed)
        company = domain.replace(".com", "").replace(".co.uk", "").split(".")[0]
        return apify_fetch_reviews(company.title(), platform="trustpilot", limit=limit)
    try:
        import httpx
        resp = httpx.get(
            f"https://api.trustpilot.com/v1/business-units/{domain}/reviews",
            headers={"ApiKey": key},
            params={"perPage": min(limit, 100)},
            timeout=10,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        reviews = data.get("reviews", [])
        return [
            {
                "id": r.get("id"),
                "text": r.get("text", ""),
                "rating": r.get("stars"),
                "date": r.get("createdAt", "")[:10],
                "source": "Trustpilot",
            }
            for r in reviews[:limit]
        ]
    except Exception:
        return None


# ── FactSet (placeholder) ────────────────────────────────────────────────────


def factset_fetch_comparables(
    ticker: str,
    api_key: Optional[str] = None,
) -> Optional[dict]:
    """Placeholder. FactSet API requires enterprise setup."""
    return None


# ── Glassdoor (placeholder) ───────────────────────────────────────────────────


def glassdoor_fetch_reviews(
    company: str,
    api_key: Optional[str] = None,
) -> Optional[list[dict]]:
    """Placeholder. Glassdoor has no public reviews API."""
    return None
