"""
Kaggle dataset loader. Fetches review datasets and maps to InsightEngine schema.
Requires: pip install kaggle
Setup: Place kaggle.json (API credentials) in ~/.kaggle/ or set KAGGLE_USERNAME/KAGGLE_KEY env vars.

Supported datasets (industry → dataset slug):
  ride-sharing: jschne61701/uber-rides-costumer-reviews-dataset
  food-delivery: skamlo/food-delivery-apps-reviews
  e-commerce: yasserh/amazon-product-reviews-dataset
  restaurants: omkarsabnis/yelp-reviews-dataset
"""

import os
import json
import re
from pathlib import Path
from typing import Optional

# Target schema: { id, company, source, rating, date, reviewer_type?, text }
REVIEW_SCHEMA_KEYS = {"id", "company", "source", "rating", "date", "reviewer_type", "text"}


def _normalize_rating(val) -> Optional[int]:
    """Convert various rating formats to 1-5 scale."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        v = float(val)
        if v <= 5:
            return max(1, min(5, round(v)))
        if v <= 10:
            return max(1, min(5, round(v / 2)))
        if v <= 100:
            return max(1, min(5, round(v / 20)))
    if isinstance(val, str):
        m = re.search(r"(\d+(?:\.\d+)?)", val)
        if m:
            return _normalize_rating(float(m.group(1)))
    return None


def _ensure_text(r: dict) -> str:
    """Extract review text from various column names."""
    for k in ("text", "review", "content", "body", "review_text", "Review", "reviewText"):
        v = r.get(k)
        if v and isinstance(v, str) and len(v.strip()) > 10:
            return v.strip()
    return ""


def _map_uber_reviews(df_or_rows, companies: list) -> list[dict]:
    """Map Uber rides dataset to schema. Companies: Uber, Lyft, Bolt, etc."""
    rows = df_or_rows if isinstance(df_or_rows, list) else df_or_rows.to_dict("records")
    out = []
    for i, r in enumerate(rows):
        text = _ensure_text(r)
        if not text:
            continue
        company = r.get("company", r.get("Company", "Uber"))
        if company not in companies and companies:
            company = companies[0]  # Default to focal
        rating = _normalize_rating(r.get("rating", r.get("Rating", r.get("stars", 4))))
        date = r.get("date", r.get("Date", r.get("created_at", "")))
        if isinstance(date, str) and len(date) >= 10:
            date = date[:10]
        else:
            date = "2024-01-01"
        out.append({
            "id": f"kaggle_uber_{i}",
            "company": company,
            "source": "Kaggle",
            "rating": rating or 4,
            "date": date,
            "reviewer_type": r.get("reviewer_type", "Customer"),
            "text": text[:2000],
        })
    return out


def _map_food_delivery(df_or_rows, companies: list) -> list[dict]:
    """Map food delivery apps dataset. Companies: DoorDash, Uber Eats, Grubhub."""
    rows = df_or_rows if isinstance(df_or_rows, list) else df_or_rows.to_dict("records")
    company_map = {"doordash": "DoorDash", "ubereats": "Uber Eats", "uber eats": "Uber Eats",
                  "grubhub": "Grubhub", "deliveroo": "Deliveroo", "just eat": "Just Eat"}
    out = []
    for i, r in enumerate(rows):
        text = _ensure_text(r)
        if not text:
            continue
        raw_co = r.get("app", r.get("App", r.get("company", "")))
        company = company_map.get(str(raw_co).lower(), raw_co or companies[0] if companies else "DoorDash")
        if company not in companies and companies:
            company = companies[0]
        rating = _normalize_rating(r.get("rating", r.get("Rating", r.get("score", 4))))
        date = r.get("date", r.get("Date", ""))
        if isinstance(date, str) and len(date) >= 10:
            date = date[:10]
        else:
            date = "2024-01-01"
        out.append({
            "id": f"kaggle_food_{i}",
            "company": company,
            "source": "Kaggle",
            "rating": rating or 4,
            "date": date,
            "reviewer_type": "Customer",
            "text": text[:2000],
        })
    return out


def _map_amazon(df_or_rows, companies: list) -> list[dict]:
    """Map Amazon product reviews. Companies: Amazon, Shopify, eBay, etc."""
    rows = df_or_rows if isinstance(df_or_rows, list) else df_or_rows.to_dict("records")
    out = []
    for i, r in enumerate(rows):
        text = _ensure_text(r)
        if not text:
            continue
        company = r.get("company", r.get("brand", "Amazon"))
        if company not in companies and companies:
            company = companies[0]
        rating = _normalize_rating(r.get("rating", r.get("Rating", r.get("overall", 4))))
        date = r.get("date", r.get("reviewTime", ""))
        if isinstance(date, str) and len(date) >= 10:
            date = date[:10]
        else:
            date = "2024-01-01"
        out.append({
            "id": f"kaggle_amazon_{i}",
            "company": company,
            "source": "Kaggle",
            "rating": rating or 4,
            "date": date,
            "reviewer_type": "Customer",
            "text": text[:2000],
        })
    return out


def _map_yelp(df_or_rows, companies: list) -> list[dict]:
    """Map Yelp reviews. Companies: restaurant chains or categories."""
    rows = df_or_rows if isinstance(df_or_rows, list) else df_or_rows.to_dict("records")
    out = []
    for i, r in enumerate(rows):
        text = _ensure_text(r)
        if not text:
            continue
        company = r.get("business_name", r.get("company", companies[0] if companies else "Restaurant"))
        if company not in companies and companies:
            company = companies[0]
        rating = _normalize_rating(r.get("stars", r.get("rating", 4)))
        date = r.get("date", r.get("review_date", ""))
        if isinstance(date, str) and len(date) >= 10:
            date = date[:10]
        else:
            date = "2024-01-01"
        out.append({
            "id": f"kaggle_yelp_{i}",
            "company": company,
            "source": "Kaggle",
            "rating": rating or 4,
            "date": date,
            "reviewer_type": "Customer",
            "text": text[:2000],
        })
    return out


KAGGLE_DATASETS = {
    "ride-sharing": {
        "slug": "jschne61701/uber-rides-costumer-reviews-dataset",
        "mapper": _map_uber_reviews,
    },
    "food-delivery": {
        "slug": "skamlo/food-delivery-apps-reviews",
        "mapper": _map_food_delivery,
    },
    "e-commerce": {
        "slug": "yasserh/amazon-product-reviews-dataset",
        "mapper": _map_amazon,
    },
    "restaurants": {
        "slug": "omkarsabnis/yelp-reviews-dataset",
        "mapper": _map_yelp,
    },
}


def load_kaggle_dataset(
    industry: str,
    companies: list,
    data_dir: Optional[Path] = None,
    limit: int = 500,
) -> Optional[list[dict]]:
    """
    Load reviews from Kaggle for the given industry.
    Downloads dataset if not present. Returns None if Kaggle not configured or fails.
    """
    cfg = KAGGLE_DATASETS.get(industry)
    if not cfg:
        return None

    try:
        import kaggle
    except ImportError:
        return None

    slug = cfg["slug"]
    mapper = cfg["mapper"]
    base = data_dir or Path(__file__).parent.parent / "data" / "kaggle"
    base.mkdir(parents=True, exist_ok=True)

    csv_files = list(base.glob("**/*.csv"))
    json_files = list(base.glob("**/*.json"))
    if not csv_files and not json_files:
        try:
            kaggle.api.dataset_download_files(slug, path=str(base), unzip=True)
            csv_files = list(base.glob("**/*.csv"))
            json_files = list(base.glob("**/*.json"))
        except Exception:
            return None

    import pandas as pd
    df = None
    for p in csv_files[:1]:
        try:
            df = pd.read_csv(p, nrows=limit * 2)
            break
        except Exception:
            continue
    if df is None:
        for p in json_files[:1]:
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                rows = data if isinstance(data, list) else data.get("reviews", data.get("data", []))
                if rows:
                    df = pd.DataFrame(rows[: limit * 2])
                    break
            except Exception:
                continue

    if df is None or df.empty:
        return None

    reviews = mapper(df, companies)
    return reviews[:limit]


def load_from_local_kaggle_csv(
    csv_path: Path,
    industry: str,
    companies: list,
    limit: int = 500,
) -> list[dict]:
    """
    Load from a pre-downloaded Kaggle CSV (e.g. user downloaded manually).
    Use when Kaggle API is not configured.
    """
    cfg = KAGGLE_DATASETS.get(industry)
    if not cfg:
        return []

    import pandas as pd
    try:
        df = pd.read_csv(csv_path, nrows=limit * 2)
    except Exception:
        return []

    return cfg["mapper"](df, companies)[:limit]
