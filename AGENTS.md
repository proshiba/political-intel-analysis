# Political Intel Analysis Agent Instructions

## Mission
Build tools that collect, normalize, and analyze open-source political and legal information from file-configured URLs.

## Operating Principles
- Respect robots.txt and site terms of use.
- Prefer official government, parliament, regulator, court, and intergovernmental sources when available.
- Preserve source URLs, fetch timestamps, and extraction metadata for auditability.
- Treat automated analysis as analyst support, not final legal advice.

## Data Handling
- Do not commit secrets, API keys, private source lists, or large raw crawl dumps.
- Store sample inputs under `data/` only when they are synthetic or public examples.
- Outputs should be reproducible JSON/JSONL/Markdown files.

## Python Style
- Target Python 3.11+.
- Keep modules small and typed where practical.
- Avoid try/catch blocks around imports.
- Prefer deterministic functions that are easy to unit test.

## PR Notes
Include a concise summary of crawler, extraction, analysis, and testing changes.
