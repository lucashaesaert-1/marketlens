"""
Generic scraper for pages with review data in script tags or JSON-LD.
Useful for sites that embed review data in HTML.
"""

import re
import json
from typing import Optional
from urllib.parse import urlparse

from .base import BaseScraper


def generic_scrape_reviews(
    url: str,
    limit: int = 50,
    company_name: str = "Unknown",
) -> Optional[list[dict]]:
    """
    Attempt to extract reviews from a URL. Supports:
    - JSON-LD Product/review schema
    - Embedded JSON in script tags
    - Generic review-like structures
    """
    scraper = BaseScraper()
    html = scraper._fetch_with_delay(url)
    if not html:
        return None

    reviews = _extract_json_ld(html) or _extract_script_json(html)
    if not reviews:
        return None

    out = []
    for i, r in enumerate(reviews):
        if i >= limit:
            break
        text = _get_text(r)
        if not text or len(text) < 10:
            continue
        rating = _get_rating(r)
        date = _get_date(r)
        out.append({
            "id": f"generic_{len(out)}",
            "company": company_name,
            "source": urlparse(url).netloc.replace("www.", "").split(".")[0].title(),
            "rating": rating,
            "date": date,
            "reviewer_type": r.get("author", {}).get("name", "Customer") if isinstance(r.get("author"), dict) else "Customer",
            "text": text[:2000],
        })
    return out if out else None


def _get_text(r: dict) -> str:
    for k in ("reviewBody", "body", "text", "content", "reviewText", "description"):
        v = r.get(k)
        if v and isinstance(v, str) and len(v.strip()) > 10:
            return v.strip()
    return ""


def _get_rating(r: dict) -> int:
    v = r.get("reviewRating", r.get("rating", r.get("stars", 4)))
    if isinstance(v, dict):
        v = v.get("ratingValue", v.get("value", 4))
    if isinstance(v, (int, float)):
        return max(1, min(5, round(float(v))))
    return 4


def _get_date(r: dict) -> str:
    v = r.get("datePublished", r.get("date", r.get("createdAt", r.get("publishedAt", ""))))
    if isinstance(v, str) and len(v) >= 10:
        return v[:10]
    return "2024-01-01"


def _extract_json_ld(html: str) -> Optional[list]:
    pattern = r'<script type="application/ld\+json">(.+?)</script>'
    for m in re.finditer(pattern, html, re.DOTALL):
        try:
            ld = json.loads(m.group(1))
            if isinstance(ld, dict):
                if ld.get("@type") == "Product":
                    revs = ld.get("review", [])
                    if isinstance(revs, dict):
                        revs = [revs]
                    return revs
                if ld.get("@type") == "Review":
                    return [ld]
            if isinstance(ld, list):
                return [x for x in ld if isinstance(x, dict) and x.get("@type") == "Review"]
        except Exception:
            continue
    return None


def _extract_script_json(html: str) -> Optional[list]:
    """Look for review arrays in script content."""
    for m in re.finditer(r'"(?:reviews|reviewList|reviewsList)"\s*:\s*(\[[\s\S]*?\])\s*[,}]', html):
        try:
            # Fix common JSON issues
            raw = m.group(1)
            raw = re.sub(r',\s*}', '}', raw)
            raw = re.sub(r',\s*]', ']', raw)
            data = json.loads(raw)
            if isinstance(data, list) and len(data) > 0:
                first = data[0]
                if isinstance(first, dict) and (_get_text(first) or first.get("reviewBody")):
                    return data
        except Exception:
            continue
    return None
