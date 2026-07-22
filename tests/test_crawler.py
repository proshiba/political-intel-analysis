from political_intel.crawler import SeleniumPoliticalCrawler, _discover_same_domain_links
from political_intel.models import SourceSite


class FakeDriver:
    def __init__(self) -> None:
        self.current_url = ""
        self.page_source = ""
        self.visited: list[str] = []
        self.quit_called = False

    def get(self, url: str) -> None:
        self.visited.append(url)
        self.current_url = url
        self.page_source = """
        <html>
          <body>
            <main>Rendered bill text from the parliament portal.</main>
            <a href="/press/new-bill">bill</a>
            <a href="https://other.example/story">external</a>
          </body>
        </html>
        """

    def quit(self) -> None:
        self.quit_called = True


def test_discover_same_domain_links_filters_external_and_locale_picker() -> None:
    html = """
    <a href="https://external.example/news">external</a>
    <a href="/homepage.html?locale=bg">locale</a>
    <a href="/about">about</a>
    <a href="/press/new-law.html">press</a>
    """

    links = _discover_same_domain_links(html, "https://example.com/")

    assert links == ["https://example.com/press/new-law.html", "https://example.com/about"]


def test_selenium_crawler_uses_headless_driver_factory_and_discovers_links() -> None:
    driver = FakeDriver()
    source = SourceSite(url="https://example.gov/session", site_name="Example Parliament")
    crawler = SeleniumPoliticalCrawler(
        delay_seconds=0,
        respect_robots=False,
        browser_wait_seconds=0,
        driver_factory=lambda: driver,
    )

    page = crawler.fetch(source)
    crawler.close()

    assert driver.visited == ["https://example.gov/session"]
    assert driver.quit_called is True
    assert page.status_code == 200
    assert page.content_type == "text/html; rendered=selenium"
    assert "Rendered bill text" in page.text
    assert page.discovered_links == ["https://example.gov/press/new-bill"]
