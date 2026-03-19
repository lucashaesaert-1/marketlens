"""
Capterra reviews scraper. Capterra is JS-heavy; prefer Apify for production.
Attempts HTML/JSON extraction as fallback.
"""

import re
import json
from typing import Optional

from .base import BaseScraper


def capterra_scrape_reviews(
    product_slug: str,
    limit: int = 30,
    api_token: Optional[str] = None,
) -> Optional[list[dict]]:
    """
    Scrape Capterra reviews. If APIFY_API_TOKEN is set, delegates to Apify (recommended).
    Otherwise attempts HTML/JSON extraction.
    """
    if api_token or __import__("os").environ.get("APIFY_API_TOKEN"):
        from ..apify_adapter import apify_fetch_reviews
        company = product_slug.replace("-", " ").title()
        return apify_fetch_reviews(company, platform="capterra", limit=limit)

    url = f"https://www.capterra.com/p/{product_slug}/reviews/"
    scraper = BaseScraper()
    html = scraper._fetch_with_delay(url)
    if not html:
        return None

    reviews = _extract_from_embedded_json(html) or _extract_from_json_ld(html)
    if not reviews:
        return None

    out = []
    for i, r in enumerate(reviews):
        if i >= limit:
            break
        text = r.get("body", r.get("text", r.get("content", r.get("reviewText", ""))))
        if not text or len(str(text)) < 10:
            continue
        rating = r.get("rating", r.get("stars", r.get("score", 4)))
        if isinstance(rating, (int, float)):
            rating = max(1, min(5, round(float(rating))))
        else:
            rating = 4
        date = r.get("date", r.get("createdAt", "2024-01-01"))
        if isinstance(date, str) and len(date) >= 10:
            date = date[:10]
        out.append({
            "id": f"capterra_{product_slug}_{i}",
            "company": product_slug.replace("-", " ").title(),
            "source": "Capterra",
            "rating": rating,
            "date": date,
            "reviewer_type": r.get("reviewerType", "Customer"),
            "text": str(text)[:2000],
        })
    return out if out else None


def _extract_from_embedded_json(html: str) -> Optional[list]:
    """Look for JSON with review data in script tags."""
    patterns = [
        r'"reviews"\s*:\s*(\[[^\]]+\])',
        r'"reviews"\s*:\s*(\{[^}]+\})',
        r'"reviewList"\s*:\s*(\[[^\]]+\])',
    ]
    for pat in patterns:
        m = re.search(pat, html)
        if m:
            try:
                data = json.loads(m.group(1))
                if isinstance(data, list):
                    return data
                if isinstance(data, dict):
                    return data.get("items", data.get("data", []))
            except Exception:
                continue
    return None


def _extract_from_json_ld(html: str) -> Optional[list]:
    """Extract from JSON-LD review schema."""
    pattern = r'<script type="application/ld\+json">(.+?)</script>'
    for m in re.finditer(pattern, html, re.DOTALL):
        try:
            ld = json.loads(m.group(1))
            if isinstance(ld, dict) and ld.get("@type") == "Product":
                revs = ld.get("review", [])
                if isinstance(revs, dict):
                    revs = [revs]
                return revs
        except Exception:
            continue
    return None
