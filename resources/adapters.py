"""
Data source adapters. When API keys are configured, fetch real data.
Otherwise return None (caller uses mock/fallback).

Primary sources (no Trustpilot key needed):
  - Kaggle: Free datasets for ride-sharing, food-delivery, e-commerce, restaurants
  - Apify: G2, Capterra, Trustpilot via APIFY_API_TOKEN
  - Scrapers: G2, Capterra (fallback when Apify not configured)
"""

import os
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


def fetch_reviews_for_industry(
    industry: str,
    companies: list,
    focal_company: str,
    limit: int = 200,
) -> Optional[list[dict]]:
    """
    Unified review fetcher. Tries in order:
    1. Kaggle (ride-sharing, food-delivery, e-commerce, restaurants)
    2. Apify for focal company (G2/Capterra) if APIFY_API_TOKEN set
    3. Returns None → caller uses data_file (local JSON)
    """
    # Try Kaggle first for supported industries
    kaggle_industries = ("ride-sharing", "food-delivery", "e-commerce", "restaurants")
    if industry in kaggle_industries:
        reviews = kaggle_fetch_reviews(industry, companies, limit=limit)
        if reviews:
            return reviews

    # Try Apify for CRM, SaaS, hospitality, banking, healthcare, travel, telecom, insurance
    apify_industries = ("crm", "saas", "hospitality", "banking", "healthcare", "travel", "telecom", "insurance")
    if industry in apify_industries:
        reviews = apify_fetch_reviews(focal_company, platform="g2", limit=min(limit, 100))
        if reviews:
            return reviews

    return None


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
