# Political Intel Analysis

File-configured crawler and analysis toolkit for monitoring political and legal developments across countries.

## Quick start

1. Edit `data/sources.example.json` or create your own JSON source configuration with a `sources` array.
2. Copy `.env.example` to `.env` and adjust crawler settings if needed.
3. Install dependencies and run the pipeline:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m political_intel.pipeline --sources data/sources.example.json --output data/output --max-pages-per-site 2
```

The pipeline writes raw fetches, extracted records, and country-level analysis summaries under the output directory. For JavaScript-rendered portals, add `--render-javascript` to collect pages with Selenium and headless Chrome; Chrome/Chromium must be available in the runtime environment.

## Components

- `political_intel.sources`: loads source URLs and related metadata from JSON configuration files.
- `political_intel.crawler`: polite same-domain HTTP crawler and optional Selenium/headless Chrome crawler with per-domain rate limiting, robots.txt checks, and link prioritization.
- `political_intel.extractor`: extracts title, publication date, readable text, and political/legal signals.
- `political_intel.analyzer`: builds country-level summaries and simple insight/risk indicators.
- `political_intel.pipeline`: command-line orchestration.

## Source configuration schema

Top-level JSON object:

| Field | Required | Description |
| --- | --- | --- |
| `version` | No | Configuration schema version. |
| `description` | No | Human-readable explanation of the source list. |
| `defaults` | No | Default metadata applied to each source. |
| `sources` | Yes | Array of crawl source objects. |

Each object in `sources`:

| Field | Required | Description |
| --- | --- | --- |
| `url` | Yes | Website or article URL to crawl. |
| `country` | Recommended | Country or region associated with the source. |
| `site_name` | Recommended | Human-readable source name. |
| `category` | Recommended | Source type, such as `government`, `parliament`, `news`, `law`, or `ngo`. |
| `notes` | No | Analyst notes preserved in outputs. |
| `tags` | No | Analyst-defined labels, such as `official`, `legislation`, or `sanctions`. |
| `priority` | No | Monitoring priority, such as `high`, `medium`, or `low`. |
| `refresh_interval_hours` | No | Intended refresh cadence for scheduler integrations. |
| `preferred_language` | No | Preferred language code for analysis workflows. |

## Outputs

- `raw_pages.jsonl`: HTTP metadata, readable page text, discovered links, and source metadata for auditing.
- `records.jsonl`: normalized extracted records.
- `country_summaries.json`: per-country event summaries and metrics.
- `insights.md`: analyst-friendly Markdown report.

## Compliance notes

Use this crawler only for sites you are allowed to access. The default HTTP crawler and optional Selenium crawler check robots.txt, identify themselves through a configurable user agent, and throttle requests per domain. Selenium output is marked with `content_type` value `text/html; rendered=selenium` for auditability.

## Trial crawl notes

A live trial against `data/sources.example.json` with `--max-pages-per-site 2` collected four records on July 18, 2026 UTC: two Japanese Prime Minister's Office pages, the EUR-Lex landing page, and a Congress.gov 403 anti-bot response. The Congress.gov result is preserved in outputs for auditability, but analysts should replace that sample URL with a machine-accessible feed/API or an allowed mirror before relying on U.S. legislative coverage.

## Merge readiness check

If a target branch is available locally, run `python scripts/check_merge_conflicts.py --base-ref <target-ref>` before opening or updating a PR. Without `--base-ref`, the script scans tracked files for unresolved conflict markers.
