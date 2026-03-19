"""
Base scraper with rate limiting, headers, and error handling.
Respect robots.txt and add delays between requests.
"""

import time
import random
from typing import Optional
from urllib.parse import urljoin

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
DEFAULT_DELAY_SEC = (2, 5)


def rate_limit(min_sec: float = 2, max_sec: float = 5) -> None:
    """Sleep between requests to avoid overloading servers."""
    time.sleep(random.uniform(min_sec, max_sec))


class BaseScraper:
    """Base class for review scrapers."""

    def __init__(
        self,
        user_agent: str = DEFAULT_USER_AGENT,
        delay_range: tuple[float, float] = DEFAULT_DELAY_SEC,
        timeout: int = 15,
    ):
        self.user_agent = user_agent
        self.delay_range = delay_range
        self.timeout = timeout

    def _headers(self) -> dict:
        return {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def _fetch(self, url: str) -> Optional[str]:
        """Fetch HTML. Returns None on failure."""
        try:
            import httpx
            resp = httpx.get(
                url,
                headers=self._headers(),
                timeout=self.timeout,
                follow_redirects=True,
            )
            if resp.status_code != 200:
                return None
            return resp.text
        except Exception:
            return None

    def _fetch_with_delay(self, url: str) -> Optional[str]:
        rate_limit(*self.delay_range)
        return self._fetch(url)
