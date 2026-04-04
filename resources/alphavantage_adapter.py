"""
Alpha Vantage adapter for live stock quotes.
Replaces SerpAPI Google Finance for investor audience data.

Requires: pip install requests
Setup: Set Alpha_vantage in .env (get key at alphavantage.co)
"""

from __future__ import annotations

import logging
import os
from typing import Optional

import requests

log = logging.getLogger("insightengine.alphavantage")

AV_BASE = "https://www.alphavantage.co/query"

# Company name → ticker symbol (Alpha Vantage uses plain symbols, no exchange suffix)
COMPANY_TICKERS: dict[str, str] = {
    # CRM
    "HubSpot": "HUBS",
    "Salesforce": "CRM",
    # Food Delivery / Ride-Sharing
    "Uber Eats": "UBER",
    "Uber": "UBER",
    "DoorDash": "DASH",
    "Lyft": "LYFT",
    # SaaS / Productivity
    "Monday.com": "MNDY",
    "Asana": "ASAN",
    "Atlassian": "TEAM",
    # E-commerce
    "Amazon": "AMZN",
    "Shopify": "SHOP",
    "eBay": "EBAY",
    "Etsy": "ETSY",
    "Walmart": "WMT",
    # Banking
    "JPMorgan Chase": "JPM",
    "Bank of America": "BAC",
    "Wells Fargo": "WFC",
    "Citigroup": "C",
    "Goldman Sachs": "GS",
    # Healthcare
    "UnitedHealth": "UNH",
    "CVS Health": "CVS",
    "Humana": "HUM",
    # Travel
    "Airbnb": "ABNB",
    "Booking.com": "BKNG",
    "Expedia": "EXPE",
    "TripAdvisor": "TRIP",
    # Telecom
    "AT&T": "T",
    "Verizon": "VZ",
    "T-Mobile": "TMUS",
    # Insurance
    "Lemonade": "LMND",
    "Progressive": "PGR",
    "Allstate": "ALL",
    # Deliveroo is LSE-listed; Alpha Vantage supports it as ROO on LSE
    "Deliveroo": "ROO",
}


def _api_key() -> Optional[str]:
    return os.environ.get("Alpha_vantage") or os.environ.get("ALPHA_VANTAGE_API_KEY")


def fetch_quote(symbol: str) -> Optional[dict]:
    """
    Fetch a live stock quote from Alpha Vantage.
    Returns {ticker, price, currency, change, pct_change} or None.
    """
    key = _api_key()
    if not key:
        return None

    try:
        resp = requests.get(
            AV_BASE,
            params={"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": key},
            timeout=15,
        )
        if resp.status_code != 200:
            log.warning("alphavantage HTTP %s for %s", resp.status_code, symbol)
            return None

        data = resp.json()
        gq = data.get("Global Quote", {})

        if not gq or not gq.get("05. price"):
            # Alpha Vantage returns an empty Global Quote when the symbol isn't found
            log.warning("alphavantage: no quote data for %s", symbol)
            return None

        price = float(gq["05. price"])
        change = float(gq["09. change"])
        pct_raw = gq.get("10. change percent", "0%").replace("%", "").strip()
        pct = float(pct_raw) if pct_raw else None

        return {
            "ticker": symbol,
            "price": price,
            "currency": "USD",
            "change": change,
            "pct_change": pct,
        }

    except Exception as exc:
        log.warning("alphavantage error for %s: %s", symbol, exc)
        return None


def fetch_finance_data_for_companies(companies: list[str]) -> Optional[dict[str, dict]]:
    """
    Fetch stock quotes for all companies that have known tickers.
    Returns {company_name: quote_dict} or None if key missing / no data.
    """
    if not _api_key():
        return None

    result: dict[str, dict] = {}
    for company in companies:
        symbol = COMPANY_TICKERS.get(company)
        if not symbol:
            continue
        quote = fetch_quote(symbol)
        if quote:
            result[company] = quote
            log.info("alphavantage: %s → %s @ %s", company, symbol, quote.get("price"))

    return result if result else None
