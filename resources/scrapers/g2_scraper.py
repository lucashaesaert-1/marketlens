"""
G2 reviews scraper. G2 is JS-heavy; prefer Apify for production.
This scraper attempts to extract review data from HTML/embedded JSON.
"""

import re
import json
from typing import Optional

from .base import BaseScraper


def g2_scrape_reviews(
    product_slug: str,
    limit: int = 30,
    api_token: Optional[str] = None,
) -> Optional[list[dict]]:
    """
    Scrape G2 reviews. If APIFY_API_TOKEN is set, delegates to Apify (recommended).
    Otherwise attempts HTML/JSON extraction (may fail on dynamic content).
    """
    if api_token or __import__("os").environ.get("APIFY_API_TOKEN"):
        from ..apify_adapter import apify_fetch_reviews
        company = product_slug.replace("-", " ").title()
        return apify_fetch_reviews(company, platform="g2", limit=limit)

    url = f"https://www.g2.com/products/{product_slug}/reviews"
    scraper = BaseScraper()
    html = scraper._fetch_with_delay(url)
    if not html:
        return None

    # G2 often embeds review data in __NEXT_DATA__ or similar script tags
    reviews = _extract_from_next_data(html) or _extract_from_json_ld(html)
    if not reviews:
        return None

    out = []
    for i, r in enumerate(reviews):
        if i >= limit:
            break
        text = r.get("body", r.get("text", r.get("content", "")))
        if not text or len(str(text)) < 10:
            continue
        rating = r.get("rating", r.get("stars", 4))
        if isinstance(rating, (int, float)):
            rating = max(1, min(5, round(float(rating))))
        else:
            rating = 4
        date = r.get("date", r.get("createdAt", "2024-01-01"))
        if isinstance(date, str) and len(date) >= 10:
            date = date[:10]
        out.append({
            "id": f"g2_{product_slug}_{i}",
            "company": product_slug.replace("-", " ").title(),
            "source": "G2",
            "rating": rating,
            "date": date,
            "reviewer_type": r.get("reviewerType", "Customer"),
            "text": str(text)[:2000],
        })
    return out if out else None


def _extract_from_next_data(html: str) -> Optional[list]:
    """Extract from Next.js __NEXT_DATA__ script."""
    m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html, re.DOTALL)
    if not m:
        return None
    try:
        data = json.loads(m.group(1))
        props = data.get("props", {}).get("pageProps", {})
        reviews = props.get("reviews", props.get("productReviews", []))
        return reviews if isinstance(reviews, list) else None
    except Exception:
        return None


def _extract_from_json_ld(html: str) -> Optional[list]:
    """Extract from JSON-LD review schema."""
    pattern = r'<script type="application/ld\+json">(.+?)</script>'
    for m in re.finditer(pattern, html, re.DOTALL):
        try:
            ld = json.loads(m.group(1))
            if isinstance(ld, dict) and ld.get("@type") == "Product":
                agg = ld.get("aggregateRating", {})
                revs = ld.get("review", [])
                if isinstance(revs, dict):
                    revs = [revs]
                return revs
            if isinstance(ld, list):
                for item in ld:
                    if isinstance(item, dict) and item.get("@type") == "Review":
                        return [item]
        except Exception:
            continue
    return None
