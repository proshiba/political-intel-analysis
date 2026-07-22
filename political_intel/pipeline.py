from __future__ import annotations

import argparse
from pathlib import Path

from .analyzer import build_country_summaries, render_markdown_report
from .crawler import PoliticalCrawler, SeleniumPoliticalCrawler
from .extractor import extract_record
from .io import write_json, write_jsonl
from .sources import load_sources


def run_pipeline(
    sources_path: str,
    output_dir: str,
    respect_robots: bool = True,
    max_pages_per_site: int = 1,
    render_javascript: bool = False,
) -> None:
    output = Path(output_dir)
    sites = load_sources(sources_path)
    crawler_class = SeleniumPoliticalCrawler if render_javascript else PoliticalCrawler
    with crawler_class(respect_robots=respect_robots) as crawler:
        pages = crawler.crawl(sites, max_pages_per_site=max_pages_per_site)
    records = [extract_record(page) for page in pages]
    summaries = build_country_summaries(records)

    write_jsonl(output / "raw_pages.jsonl", pages)
    write_jsonl(output / "records.jsonl", records)
    write_json(output / "country_summaries.json", summaries)
    (output / "insights.md").write_text(render_markdown_report(summaries), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Crawl and analyze political intelligence sources from a JSON source configuration.")
    parser.add_argument("--sources", required=True, help="JSON source configuration containing URLs and metadata")
    parser.add_argument("--output", required=True, help="Output directory for JSONL/JSON/Markdown artifacts")
    parser.add_argument("--ignore-robots", action="store_true", help="Disable robots.txt checks for controlled/internal sources")
    parser.add_argument("--max-pages-per-site", type=int, default=1, help="Maximum same-domain pages to collect per configured source")
    parser.add_argument("--render-javascript", action="store_true", help="Use Selenium with headless Chrome for JavaScript-rendered pages")
    args = parser.parse_args()
    run_pipeline(
        args.sources,
        args.output,
        respect_robots=not args.ignore_robots,
        max_pages_per_site=args.max_pages_per_site,
        render_javascript=args.render_javascript,
    )


if __name__ == "__main__":
    main()
