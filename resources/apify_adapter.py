"""
Apify adapter for G2, Capterra, Trustpilot reviews.
Alternative to Trustpilot API — no Trustpilot key needed.

Requires: pip install apify-client
Setup: Set APIFY_API_TOKEN in .env (get free token at apify.com)

Recommended actors:
  - zen-studio/software-review-scraper (G2, Capterra, TrustRadius, Trustpilot)
  - focused_vanguard/multi-platform-reviews-scraper (G2, Capterra, Trustpilot, Gartner, Reddit)
"""

import os
from typing import Optional

# Target schema: { id, company, source, rating, date, reviewer_type?, text }


def apify_fetch_reviews(
    company: str,
    platform: str = "g2",
    api_token: Optional[str] = None,
    limit: int = 50,
) -> Optional[list[dict]]:
    """
    Fetch reviews via Apify. Uses software-review-scraper or multi-platform scraper.
    Returns None if no token or fetch fails.
    """
    token = api_token or os.environ.get("APIFY_API_TOKEN")
    if not token:
        return None

    try:
        from apify_client import ApifyClient
    except ImportError:
        return None

    # Map platform to actor input
    platform_lower = platform.lower()
    if platform_lower in ("g2", "capterra", "trustpilot", "trustradius"):
        actor_id = "zen-studio/software-review-scraper"
        run_input = {
            "startUrls": [{"url": _product_url(company, platform_lower)}],
            "maxReviews": min(limit, 200),
            "platforms": [platform_lower],
        }
    else:
        actor_id = "focused_vanguard/multi-platform-reviews-scraper"
        run_input = {
            "productName": company,
            "platforms": [platform_lower] if platform_lower in ("g2", "capterra", "trustpilot") else ["g2", "capterra"],
            "maxReviewsPerPlatform": min(limit, 100),
        }

    try:
        client = ApifyClient(token)
        run = client.actor(actor_id).call(run_input=run_input)
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    except Exception:
        return None

    out = []
    for i, r in enumerate(items):
        if i >= limit:
            break
        text = r.get("reviewText", r.get("text", r.get("body", r.get("content", ""))))
        if not text or len(str(text).strip()) < 10:
            continue
        rating_raw = r.get("rating", r.get("stars", r.get("score", 4)))
        rating = _norm_rating(rating_raw)
        date = r.get("date", r.get("createdAt", r.get("publishedAt", "")))
        if isinstance(date, str) and len(date) >= 10:
            date = date[:10]
        else:
            date = "2024-01-01"
        src = r.get("source", r.get("platform", platform))
        out.append({
            "id": f"apify_{platform}_{i}",
            "company": company,
            "source": str(src).title(),
            "rating": rating,
            "date": date,
            "reviewer_type": r.get("reviewerType", r.get("reviewer_type", "Customer")),
            "text": str(text)[:2000],
        })
    return out if out else None


def _product_url(company: str, platform: str) -> str:
    """Build product page URL for G2/Capterra/Trustpilot."""
    slug = company.lower().replace(" ", "-").replace(".", "")
    if platform == "g2":
        return f"https://www.g2.com/products/{slug}/reviews"
    if platform == "capterra":
        return f"https://www.capterra.com/p/{slug}/reviews/"
    if platform == "trustpilot":
        return f"https://www.trustpilot.com/review/{slug}.com"
    return f"https://www.g2.com/products/{slug}/reviews"


def _norm_rating(val) -> int:
    if val is None:
        return 4
    if isinstance(val, (int, float)):
        v = float(val)
        if v <= 5:
            return max(1, min(5, round(v)))
        if v <= 10:
            return max(1, min(5, round(v / 2)))
    return 4
