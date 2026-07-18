from __future__ import annotations

import os
import time
from collections import defaultdict
from datetime import datetime, timezone
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

from .models import RawPage, SourceSite

DEFAULT_USER_AGENT = os.getenv("POLITICAL_INTEL_USER_AGENT", "PoliticalIntelBot/0.1")
DEFAULT_DELAY = float(os.getenv("POLITICAL_INTEL_REQUEST_DELAY_SECONDS", "2.0"))
DEFAULT_TIMEOUT = float(os.getenv("POLITICAL_INTEL_TIMEOUT_SECONDS", "20.0"))


class PoliticalCrawler:
    """Polite single-page crawler for spreadsheet-provided sources."""

    def __init__(self, user_agent: str = DEFAULT_USER_AGENT, delay_seconds: float = DEFAULT_DELAY, timeout_seconds: float = DEFAULT_TIMEOUT, respect_robots: bool = True) -> None:
        self.user_agent = user_agent
        self.delay_seconds = delay_seconds
        self.timeout_seconds = timeout_seconds
        self.respect_robots = respect_robots
        self._last_request_at: dict[str, float] = defaultdict(float)
        self._robots: dict[str, RobotFileParser] = {}
        self._client = httpx.Client(follow_redirects=True, timeout=timeout_seconds, headers={"User-Agent": user_agent})

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "PoliticalCrawler":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def fetch(self, source: SourceSite) -> RawPage:
        if self.respect_robots and not self._can_fetch(source.url):
            return RawPage.error_page(source, "Blocked by robots.txt")

        self._throttle(source.url)
        try:
            response = self._client.get(source.url)
            text = _html_to_text(response.text) if "html" in response.headers.get("content-type", "") else response.text[:200_000]
            return RawPage(
                source=source,
                final_url=str(response.url),
                status_code=response.status_code,
                content_type=response.headers.get("content-type", ""),
                fetched_at=datetime.now(timezone.utc).isoformat(),
                text=text[:200_000],
            )
        except httpx.HTTPError as exc:
            return RawPage.error_page(source, str(exc))

    def crawl(self, sources: list[SourceSite]) -> list[RawPage]:
        return [self.fetch(source) for source in sources]

    def _throttle(self, url: str) -> None:
        domain = urlparse(url).netloc
        elapsed = time.monotonic() - self._last_request_at[domain]
        if elapsed < self.delay_seconds:
            time.sleep(self.delay_seconds - elapsed)
        self._last_request_at[domain] = time.monotonic()

    def _can_fetch(self, url: str) -> bool:
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        if base not in self._robots:
            parser = RobotFileParser(f"{base}/robots.txt")
            parser.set_url(f"{base}/robots.txt")
            try:
                parser.read()
            except OSError:
                return True
            self._robots[base] = parser
        return self._robots[base].can_fetch(self.user_agent, url)


def _html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return "\n".join(line.strip() for line in soup.get_text("\n").splitlines() if line.strip())
