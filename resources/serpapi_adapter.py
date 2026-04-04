"""
SerpAPI adapter for Google Trends, Maps Reviews, News, Finance, and Glassdoor snippets.
Provides real data to replace synthetic sentiment trends, share-of-voice fallback,
and adds Google Maps as a review source for restaurant/hospitality industries.

Requires: pip install requests
Setup: Set SER_API in .env (get key at serpapi.com)

Supported engines used here:
  - google_trends          → historical search-interest timeline (sentiment trends proxy)
  - google_maps            → place search to resolve a company → data_id
  - google_maps_reviews    → real customer reviews for a place
  - google_news            → brand news headlines (investor audience)
  - google_finance         → live stock quote for publicly traded companies (investor audience)
  - google (search)        → Glassdoor employee rating snippets (companies/customers audience)
"""

from __future__ import annotations

import logging
import os
from typing import Optional

import requests

log = logging.getLogger("insightengine.serpapi")

SERPAPI_BASE = "https://serpapi.com/search.json"

# Industries where Google Maps reviews make sense (local / physical presence)
GOOGLE_MAPS_INDUSTRIES = {"restaurants", "hospitality", "travel"}


# ── Helpers ──────────────────────────────────────────────────────────────────


def _api_key() -> Optional[str]:
    return os.environ.get("SER_API") or os.environ.get("SERPAPI_API_KEY")


def _to_id(name: str) -> str:
    """Company name → safe JS key (same convention as industry_service.py)."""
    return name.lower().replace(" ", "").replace("-", "")


def _get(params: dict, timeout: int = 20) -> Optional[dict]:
    """GET serpapi.com/search.json with given params. Returns parsed JSON or None."""
    key = _api_key()
    if not key:
        return None
    try:
        resp = requests.get(SERPAPI_BASE, params={**params, "api_key": key}, timeout=timeout)
        if resp.status_code == 200:
            return resp.json()
        log.warning("serpapi %s → HTTP %s", params.get("engine"), resp.status_code)
    except Exception as exc:
        log.warning("serpapi %s error: %s", params.get("engine"), exc)
    return None


# ── Google Trends ─────────────────────────────────────────────────────────────


def fetch_google_trends_timeline(
    companies: list[str],
    quarters: list[str],
) -> Optional[list[dict]]:
    """
    Fetch Google Trends interest-over-time for up to 5 companies and map the
    result onto the provided list of quarter labels (e.g. ["Q1 25", …]).

    Returns a list of dicts in the same shape as _synthetic_sentiment():
        [{"month": "Q1 25", "hubspot": 0.12, "salesforce": -0.08, …}, …]
    Values are normalised to [-1, 1] (same scale as synthetic sentiment).

    Returns None if SerpAPI key missing or call fails.
    """
    if not _api_key() or not companies or not quarters:
        return None

    # Google Trends supports max 5 queries at once
    targets = companies[:5]
    q = ",".join(targets)

    data = _get({
        "engine": "google_trends",
        "q": q,
        "date": "today 2-y",   # 2-year window gives weekly points → enough quarters
        "data_type": "TIMESERIES",
    })
    if not data:
        return None

    timeline = (data.get("interest_over_time") or {}).get("timeline_data", [])
    if not timeline:
        log.warning("serpapi google_trends: no timeline_data returned")
        return None

    # Aggregate weekly points into buckets sized to match len(quarters)
    n = len(quarters)
    total = len(timeline)
    if total < n:
        log.warning("serpapi google_trends: only %d data points for %d quarters", total, n)
        return None

    bucket_size = total // n
    result: list[dict] = []

    for qi, q_label in enumerate(quarters):
        start = qi * bucket_size
        end = start + bucket_size
        bucket = timeline[start:end]

        row: dict = {"month": q_label}
        sums: dict[str, float] = {c: 0.0 for c in targets}
        counts: dict[str, int] = {c: 0 for c in targets}

        for entry in bucket:
            for v in entry.get("values", []):
                company = v.get("query", "")
                if company in sums:
                    sums[company] += float(v.get("extracted_value", 0))
                    counts[company] += 1

        for company in targets:
            n_pts = counts[company]
            avg = sums[company] / n_pts if n_pts else 50.0
            # Normalise Google Trends 0-100 → sentiment-like [-1, +1]
            row[_to_id(company)] = round(avg / 50.0 - 1.0, 3)

        result.append(row)

    log.info("serpapi google_trends: fetched %d quarters for %s", len(result), targets)
    return result


def fetch_google_trends_share_of_voice(
    companies: list[str],
) -> Optional[dict[str, int]]:
    """
    Compare relative search interest for companies over the past 12 months.
    Returns {company_name: average_interest_0_to_100}.
    Useful as a proxy for share-of-voice when real review counts are unavailable.
    """
    if not _api_key() or not companies:
        return None

    targets = companies[:5]
    q = ",".join(targets)

    data = _get({
        "engine": "google_trends",
        "q": q,
        "date": "today 12-m",
        "data_type": "TIMESERIES",
    })
    if not data:
        return None

    timeline = (data.get("interest_over_time") or {}).get("timeline_data", [])
    if not timeline:
        return None

    sums: dict[str, float] = {c: 0.0 for c in targets}
    counts: dict[str, int] = {c: 0 for c in targets}

    for entry in timeline:
        for v in entry.get("values", []):
            company = v.get("query", "")
            if company in sums:
                sums[company] += float(v.get("extracted_value", 0))
                counts[company] += 1

    result: dict[str, int] = {}
    for company in targets:
        n = counts[company]
        result[company] = round(sums[company] / n) if n else 50

    log.info("serpapi trends share-of-voice: %s", result)
    return result


# ── Google Maps Reviews ───────────────────────────────────────────────────────


def _resolve_place_data_id(company: str, location: str = "") -> Optional[str]:
    """Search Google Maps for a company and return the first result's data_id."""
    query = f"{company} {location}".strip()
    data = _get({"engine": "google_maps", "q": query, "type": "search"})
    if not data:
        return None
    places = data.get("local_results") or []
    if not places:
        log.warning("serpapi google_maps: no local_results for %r", query)
        return None
    data_id = places[0].get("data_id")
    log.info("serpapi google_maps: resolved %r → data_id=%s", company, data_id)
    return data_id


def fetch_google_maps_reviews(
    company: str,
    location: str = "",
    limit: int = 50,
) -> Optional[list[dict]]:
    """
    Fetch real Google Maps reviews for a company/place.
    Best suited for restaurants, hospitality, and other location-based businesses.

    Returns list of review dicts in the standard pipeline schema:
        {id, company, source, rating (1-5), date (YYYY-MM-DD), text}
    Returns None if API key missing, place not found, or no reviews returned.
    """
    if not _api_key():
        return None

    data_id = _resolve_place_data_id(company, location)
    if not data_id:
        return None

    data = _get({"engine": "google_maps_reviews", "data_id": data_id})
    if not data:
        return None

    raw_reviews = data.get("reviews") or []
    out: list[dict] = []

    for i, r in enumerate(raw_reviews):
        if i >= limit:
            break
        text = r.get("snippet") or r.get("text") or ""
        if not text or len(str(text).strip()) < 15:
            continue
        rating_raw = r.get("rating", 4)
        try:
            rating = max(1, min(5, int(float(rating_raw))))
        except (TypeError, ValueError):
            rating = 4
        date_str = r.get("date") or r.get("iso_date") or ""
        # iso_date is preferred (YYYY-MM-DD); "date" may be relative ("3 months ago")
        if len(date_str) >= 10 and date_str[4] == "-":
            date = date_str[:10]
        else:
            date = "2025-01-01"
        out.append({
            "id": f"gmaps_{_to_id(company)}_{i}",
            "company": company,
            "source": "Google Maps",
            "rating": rating,
            "date": date,
            "reviewer_type": "Customer",
            "text": str(text)[:2000],
        })

    if not out:
        log.warning("serpapi google_maps_reviews: no usable reviews for %r", company)
        return None

    log.info("serpapi google_maps_reviews: %d reviews for %r", len(out), company)
    return out


def fetch_google_maps_reviews_for_industry(
    companies: list[str],
    industry: str,
    limit_per_company: int = 40,
) -> Optional[list[dict]]:
    """
    Fetch Google Maps reviews for all companies in a location-based industry.
    Combines results into a single flat list (same format as other adapters).
    Only runs for industries in GOOGLE_MAPS_INDUSTRIES.
    """
    if industry not in GOOGLE_MAPS_INDUSTRIES:
        return None
    if not _api_key():
        return None

    merged: list[dict] = []
    for company in companies:
        reviews = fetch_google_maps_reviews(company, limit=limit_per_company)
        if reviews:
            merged.extend(reviews)

    return merged if merged else None


# ── Google News (brand sentiment for investor audience) ───────────────────────


def fetch_google_news_headlines(
    company: str,
    limit: int = 10,
) -> Optional[list[dict]]:
    """
    Fetch recent Google News headlines for a company.
    Returns list of {title, source, date, snippet, sentiment_hint}.
    Useful for the investor audience "recent news" panel.
    """
    if not _api_key():
        return None

    data = _get({"engine": "google_news", "q": company, "gl": "us", "hl": "en"})
    if not data:
        return None

    articles = data.get("news_results") or []
    out: list[dict] = []
    for a in articles[:limit]:
        title = a.get("title", "")
        snippet = a.get("snippet") or a.get("description") or ""
        out.append({
            "title": title,
            "source": (a.get("source") or {}).get("name", ""),
            "date": a.get("date", ""),
            "snippet": snippet,
            # Naive sentiment hint based on title keywords
            "sentiment_hint": _naive_title_sentiment(title),
        })

    return out if out else None


def _naive_title_sentiment(title: str) -> str:
    title_lower = title.lower()
    positive_words = {"surges", "rises", "gains", "beats", "record", "growth",
                      "expands", "wins", "launches", "profit", "strong"}
    negative_words = {"falls", "drops", "loses", "miss", "layoffs", "cuts",
                      "slump", "crash", "scandal", "sues", "fined", "decline"}
    if any(w in title_lower for w in positive_words):
        return "positive"
    if any(w in title_lower for w in negative_words):
        return "negative"
    return "neutral"


# ── Google Finance (stock quotes for investor audience) ───────────────────────

# Known tickers for companies tracked across industries.
# Format: "Company Name" → "TICKER:EXCHANGE"
COMPANY_TICKERS: dict[str, str] = {
    # CRM
    "HubSpot": "HUBS:NASDAQ",
    "Salesforce": "CRM:NYSE",
    # Food Delivery / Ride-Sharing
    "Uber Eats": "UBER:NYSE",
    "Uber": "UBER:NYSE",
    "DoorDash": "DASH:NYSE",
    "Lyft": "LYFT:NASDAQ",
    "Deliveroo": "ROO:LON",
    # SaaS / Productivity
    "Monday.com": "MNDY:NASDAQ",
    "Asana": "ASAN:NYSE",
    "Atlassian": "TEAM:NASDAQ",
    "Zendesk": "ZEN:NYSE",
    # E-commerce
    "Amazon": "AMZN:NASDAQ",
    "Shopify": "SHOP:NYSE",
    "eBay": "EBAY:NASDAQ",
    "Etsy": "ETSY:NASDAQ",
    "Walmart": "WMT:NYSE",
    # Banking
    "JPMorgan Chase": "JPM:NYSE",
    "Bank of America": "BAC:NYSE",
    "Wells Fargo": "WFC:NYSE",
    "Citigroup": "C:NYSE",
    "Goldman Sachs": "GS:NYSE",
    # Healthcare
    "UnitedHealth": "UNH:NYSE",
    "CVS Health": "CVS:NYSE",
    "Humana": "HUM:NYSE",
    # Travel
    "Airbnb": "ABNB:NASDAQ",
    "Booking.com": "BKNG:NASDAQ",
    "Expedia": "EXPE:NASDAQ",
    "TripAdvisor": "TRIP:NASDAQ",
    # Telecom
    "AT&T": "T:NYSE",
    "Verizon": "VZ:NYSE",
    "T-Mobile": "TMUS:NASDAQ",
    # Insurance
    "Lemonade": "LMND:NYSE",
    "Progressive": "PGR:NYSE",
    "Allstate": "ALL:NYSE",
}


def fetch_google_finance_quote(ticker: str) -> Optional[dict]:
    """
    Fetch a live stock quote from Google Finance via SerpAPI.
    ticker should be in the format "SYMBOL:EXCHANGE" (e.g. "HUBS:NASDAQ").
    Returns dict with price, change, pct_change, currency, or None on failure.
    """
    if not _api_key():
        return None

    data = _get({"engine": "google_finance", "q": ticker})
    if not data:
        return None

    summary = data.get("summary") or {}
    if not summary:
        log.warning("serpapi google_finance: no summary for %r", ticker)
        return None

    price = summary.get("price")
    try:
        price = float(price) if price is not None else None
    except (TypeError, ValueError):
        price = None

    change = summary.get("price_change")
    try:
        change = float(change) if change is not None else None
    except (TypeError, ValueError):
        change = None

    pct = summary.get("price_change_percentage") or summary.get("price_change_pct")
    try:
        pct = float(str(pct).replace("%", "")) if pct is not None else None
    except (TypeError, ValueError):
        pct = None

    return {
        "ticker": ticker,
        "price": price,
        "currency": summary.get("currency", "USD"),
        "change": change,
        "pct_change": pct,
    }


def fetch_finance_data_for_companies(companies: list[str]) -> Optional[dict[str, dict]]:
    """
    Fetch stock quotes for all companies that have known tickers.
    Returns {company_name: quote_dict} for those with data, or None if key missing.
    """
    if not _api_key():
        return None

    result: dict[str, dict] = {}
    for company in companies:
        ticker = COMPANY_TICKERS.get(company)
        if not ticker:
            continue
        quote = fetch_google_finance_quote(ticker)
        if quote:
            result[company] = quote
            log.info("serpapi finance: %s → %s @ %s", company, ticker, quote.get("price"))

    return result if result else None


# ── Glassdoor snippets via Google Search (companies/customers audience) ───────


import re as _re

_RATING_RE = _re.compile(r"(\d+(?:\.\d+)?)\s*(?:out of 5|★|stars?|/5)", _re.IGNORECASE)


def fetch_glassdoor_snippets(company: str) -> Optional[dict]:
    """
    Fetch Glassdoor employee-review data for a company via Google Search.
    Looks for the aggregate rating and a representative snippet from the first result.
    Returns {rating, snippet} or None if no data found.
    """
    if not _api_key():
        return None

    data = _get({
        "engine": "google",
        "q": f"{company} glassdoor reviews rating",
        "num": "5",
        "gl": "us",
        "hl": "en",
    })
    if not data:
        return None

    rating: Optional[float] = None
    snippet_text = ""

    # 1) Check knowledge graph (often has aggregate rating)
    kg = data.get("knowledge_graph") or {}
    kg_rating = kg.get("rating") or kg.get("overall_rating")
    if kg_rating is not None:
        try:
            rating = float(kg_rating)
        except (TypeError, ValueError):
            pass

    # 2) Check answer_box
    ab = data.get("answer_box") or {}
    ab_rating = ab.get("rating") or ab.get("score")
    if rating is None and ab_rating:
        try:
            rating = float(ab_rating)
        except (TypeError, ValueError):
            pass

    # 3) Scan organic results for glassdoor.com entries
    for r in (data.get("organic_results") or []):
        link = r.get("link", "")
        snippet = r.get("snippet", "")
        if "glassdoor.com" not in link:
            continue
        if not snippet_text:
            snippet_text = snippet
        if rating is None:
            m = _RATING_RE.search(snippet or "")
            if m:
                try:
                    rating = float(m.group(1))
                    if rating > 5:
                        rating = None  # sanity check
                except ValueError:
                    pass

    if rating is None and not snippet_text:
        log.warning("serpapi glassdoor: no data found for %r", company)
        return None

    log.info("serpapi glassdoor: %s → rating=%s", company, rating)
    return {"rating": rating, "snippet": snippet_text[:300]}


def fetch_glassdoor_data_for_companies(companies: list[str]) -> Optional[dict[str, dict]]:
    """
    Fetch Glassdoor snippets for all companies.
    Returns {company_name: {rating, snippet}} or None if key missing / all fail.
    """
    if not _api_key():
        return None

    result: dict[str, dict] = {}
    for company in companies:
        gd = fetch_glassdoor_snippets(company)
        if gd:
            result[company] = gd

    return result if result else None
