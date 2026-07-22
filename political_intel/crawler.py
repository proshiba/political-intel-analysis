from __future__ import annotations

import os
import time
from collections import defaultdict
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Protocol
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
import trafilatura
from bs4 import BeautifulSoup

from .models import RawPage, SourceSite

DEFAULT_USER_AGENT = os.getenv("POLITICAL_INTEL_USER_AGENT", "PoliticalIntelBot/0.1")
DEFAULT_DELAY = float(os.getenv("POLITICAL_INTEL_REQUEST_DELAY_SECONDS", "2.0"))
DEFAULT_TIMEOUT = float(os.getenv("POLITICAL_INTEL_TIMEOUT_SECONDS", "20.0"))
DEFAULT_BROWSER_WAIT = float(os.getenv("POLITICAL_INTEL_BROWSER_WAIT_SECONDS", "1.0"))


class PoliticalCrawler:
    """Polite bounded HTTP crawler for file-configured sources."""

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

    def fetch(self, source: SourceSite, url: str | None = None) -> RawPage:
        target_url = url or source.url
        if self.respect_robots and not self._can_fetch(target_url):
            return RawPage.error_page(source, f"Blocked by robots.txt: {target_url}")

        self._throttle(target_url)
        try:
            response = self._client.get(target_url)
            content_type = response.headers.get("content-type", "")
            text = _response_text(response)
            discovered_links = _discover_same_domain_links(response.text, str(response.url)) if response.status_code == 200 and "html" in content_type else []
            return RawPage(
                source=source,
                final_url=str(response.url),
                status_code=response.status_code,
                content_type=content_type,
                fetched_at=datetime.now(timezone.utc).isoformat(),
                text=text[:200_000],
                discovered_links=discovered_links,
            )
        except httpx.HTTPError as exc:
            return RawPage.error_page(source, str(exc))

    def crawl(self, sources: list[SourceSite], max_pages_per_site: int = 1) -> list[RawPage]:
        pages: list[RawPage] = []
        for source in sources:
            pages.extend(self.crawl_site(source, max_pages=max_pages_per_site))
        return pages

    def crawl_site(self, source: SourceSite, max_pages: int = 1) -> list[RawPage]:
        visited: set[str] = set()
        queue = [source.url]
        pages: list[RawPage] = []
        while queue and len(pages) < max_pages:
            target_url = queue.pop(0)
            if target_url in visited:
                continue
            visited.add(target_url)
            page = self.fetch(source, target_url)
            pages.append(page)
            if page.status_code == 200:
                queue.extend(link for link in page.discovered_links if link not in visited and link not in queue)
        return pages

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


class BrowserDriver(Protocol):
    current_url: str
    page_source: str

    def get(self, url: str) -> None: ...

    def quit(self) -> None: ...


class SeleniumPoliticalCrawler(PoliticalCrawler):
    """Headless Chrome crawler for pages that require JavaScript rendering."""

    def __init__(
        self,
        user_agent: str = DEFAULT_USER_AGENT,
        delay_seconds: float = DEFAULT_DELAY,
        timeout_seconds: float = DEFAULT_TIMEOUT,
        respect_robots: bool = True,
        browser_wait_seconds: float = DEFAULT_BROWSER_WAIT,
        driver_factory: Callable[[], BrowserDriver] | None = None,
    ) -> None:
        super().__init__(user_agent=user_agent, delay_seconds=delay_seconds, timeout_seconds=timeout_seconds, respect_robots=respect_robots)
        self.browser_wait_seconds = browser_wait_seconds
        self._driver_factory = driver_factory
        self._driver: BrowserDriver | None = None

    def close(self) -> None:
        if self._driver is not None:
            self._driver.quit()
            self._driver = None
        super().close()

    def fetch(self, source: SourceSite, url: str | None = None) -> RawPage:
        target_url = url or source.url
        if self.respect_robots and not self._can_fetch(target_url):
            return RawPage.error_page(source, f"Blocked by robots.txt: {target_url}")

        self._throttle(target_url)
        try:
            driver = self._get_driver()
            driver.get(target_url)
            if self.browser_wait_seconds > 0:
                time.sleep(self.browser_wait_seconds)
            html = driver.page_source
            final_url = driver.current_url or target_url
            return RawPage(
                source=source,
                final_url=final_url,
                status_code=200,
                content_type="text/html; rendered=selenium",
                fetched_at=datetime.now(timezone.utc).isoformat(),
                text=_html_to_readable_text(html)[:200_000],
                discovered_links=_discover_same_domain_links(html, final_url),
            )
        except Exception as exc:
            return RawPage.error_page(source, f"Selenium fetch failed: {exc}")

    def _get_driver(self) -> BrowserDriver:
        if self._driver is None:
            self._driver = self._driver_factory() if self._driver_factory is not None else _create_headless_chrome_driver(self.user_agent, self.timeout_seconds)
        return self._driver


def _create_headless_chrome_driver(user_agent: str, timeout_seconds: float) -> BrowserDriver:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument(f"--user-agent={user_agent}")
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(timeout_seconds)
    return driver


def _response_text(response: httpx.Response) -> str:
    content_type = response.headers.get("content-type", "")
    if "html" not in content_type:
        return response.text[:200_000]
    return _html_to_readable_text(response.text)


def _html_to_readable_text(html: str) -> str:
    extracted = trafilatura.extract(html, include_links=False, include_comments=False)
    return extracted or _html_to_text(html)


def _html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return "\n".join(line.strip() for line in soup.get_text("\n").splitlines() if line.strip())


def _discover_same_domain_links(html: str, base_url: str, limit: int = 25) -> list[str]:
    base_domain = urlparse(base_url).netloc
    links: list[str] = []
    soup = BeautifulSoup(html, "html.parser")
    for anchor in soup.find_all("a", href=True):
        href = str(anchor["href"]).strip()
        if href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        absolute = urljoin(base_url, href).split("#", 1)[0]
        parsed = urlparse(absolute)
        if parsed.scheme in {"http", "https"} and parsed.netloc == base_domain and absolute not in links and not _looks_like_locale_picker(absolute):
            links.append(absolute)
        if len(links) >= limit:
            break
    return sorted(links, key=_link_priority)


def _looks_like_locale_picker(url: str) -> bool:
    parsed = urlparse(url)
    return "locale=" in parsed.query or parsed.path.rstrip("/").endswith("homepage.html")


def _link_priority(url: str) -> tuple[int, str]:
    lowered = url.lower()
    preferred_terms = ("news", "press", "speech", "law", "bill", "legal", "legislation", "regulation", "proposal")
    return (0 if any(term in lowered for term in preferred_terms) else 1, url)
