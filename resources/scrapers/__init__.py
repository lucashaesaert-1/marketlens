"""
Web scrapers for review data. Use Apify when possible; these are fallbacks for simple pages.
"""

from .base import BaseScraper, rate_limit
from .g2_scraper import g2_scrape_reviews
from .capterra_scraper import capterra_scrape_reviews
from .generic_scraper import generic_scrape_reviews

__all__ = [
    "BaseScraper",
    "rate_limit",
    "g2_scrape_reviews",
    "capterra_scrape_reviews",
    "generic_scrape_reviews",
]
