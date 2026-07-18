from political_intel.crawler import _discover_same_domain_links


def test_discover_same_domain_links_filters_external_and_locale_picker() -> None:
    html = """
    <a href="https://external.example/news">external</a>
    <a href="/homepage.html?locale=bg">locale</a>
    <a href="/about">about</a>
    <a href="/press/new-law.html">press</a>
    """

    links = _discover_same_domain_links(html, "https://example.com/")

    assert links == ["https://example.com/press/new-law.html", "https://example.com/about"]
