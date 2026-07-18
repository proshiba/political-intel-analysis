# Political Intel Analysis

Spreadsheet-driven crawler and analysis toolkit for monitoring political and legal developments across countries.

## Quick start

1. Prepare a spreadsheet as CSV/XLSX with at least a `url` column. Optional columns include `country`, `site_name`, `category`, and `notes`.
2. Copy `.env.example` to `.env` and adjust crawler settings if needed.
3. Install dependencies and run the pipeline:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m political_intel.pipeline --input data/sites.example.csv --output data/output
```

The pipeline writes raw fetches, extracted records, and country-level analysis summaries under the output directory.

## Components

- `political_intel.spreadsheet`: loads source URLs from CSV/XLSX spreadsheets.
- `political_intel.crawler`: polite HTTP crawler with per-domain rate limiting and robots.txt checks.
- `political_intel.extractor`: extracts title, publication date, readable text, and political/legal signals.
- `political_intel.analyzer`: builds country-level summaries and simple insight/risk indicators.
- `political_intel.pipeline`: command-line orchestration.

## Input schema

| Column | Required | Description |
| --- | --- | --- |
| `url` | Yes | Website or article URL to crawl. |
| `country` | Recommended | Country or region associated with the source. |
| `site_name` | No | Human-readable source name. |
| `category` | No | Source type, such as `government`, `parliament`, `news`, or `ngo`. |
| `notes` | No | Analyst notes preserved in outputs. |

## Outputs

- `raw_pages.jsonl`: HTTP metadata and raw HTML/text snippets for auditing.
- `records.jsonl`: normalized extracted records.
- `country_summaries.json`: per-country event summaries and metrics.
- `insights.md`: analyst-friendly Markdown report.

## Compliance notes

Use this crawler only for sites you are allowed to access. The default crawler checks robots.txt, identifies itself through a configurable user agent, and throttles requests per domain.
