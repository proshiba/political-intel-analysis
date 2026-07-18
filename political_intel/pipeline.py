from __future__ import annotations

import argparse
from pathlib import Path

from .analyzer import build_country_summaries, render_markdown_report
from .crawler import PoliticalCrawler
from .extractor import extract_record
from .io import write_json, write_jsonl
from .spreadsheet import load_sites


def run_pipeline(input_path: str, output_dir: str, respect_robots: bool = True) -> None:
    output = Path(output_dir)
    sites = load_sites(input_path)
    with PoliticalCrawler(respect_robots=respect_robots) as crawler:
        pages = crawler.crawl(sites)
    records = [extract_record(page) for page in pages]
    summaries = build_country_summaries(records)

    write_jsonl(output / "raw_pages.jsonl", pages)
    write_jsonl(output / "records.jsonl", records)
    write_json(output / "country_summaries.json", summaries)
    (output / "insights.md").write_text(render_markdown_report(summaries), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Crawl and analyze political intelligence sources from a spreadsheet.")
    parser.add_argument("--input", required=True, help="CSV/XLSX spreadsheet containing source URLs")
    parser.add_argument("--output", required=True, help="Output directory for JSONL/JSON/Markdown artifacts")
    parser.add_argument("--ignore-robots", action="store_true", help="Disable robots.txt checks for controlled/internal sources")
    args = parser.parse_args()
    run_pipeline(args.input, args.output, respect_robots=not args.ignore_robots)


if __name__ == "__main__":
    main()
