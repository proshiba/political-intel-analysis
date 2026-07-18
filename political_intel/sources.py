from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

from .models import SourceSite

_REQUIRED_SOURCE_FIELDS = {"url"}
_DEFAULTS = {
    "country": "Unknown",
    "site_name": "",
    "category": "unspecified",
    "notes": "",
    "tags": [],
    "priority": "medium",
    "refresh_interval_hours": 24,
    "preferred_language": "en",
}


def load_sources(path: str | Path) -> list[SourceSite]:
    """Load crawl sources and related metadata from a JSON configuration file."""
    input_path = Path(path)
    if not input_path.exists():
        raise FileNotFoundError(f"Source configuration not found: {input_path}")

    payload = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("sources"), list):
        raise ValueError("Source configuration must be a JSON object with a 'sources' list")

    defaults = {**_DEFAULTS, **payload.get("defaults", {})}
    sources: list[SourceSite] = []
    for index, item in enumerate(payload["sources"], start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Source #{index} must be an object")
        missing = _REQUIRED_SOURCE_FIELDS - set(item)
        if missing:
            raise ValueError(f"Source #{index} missing required fields: {', '.join(sorted(missing))}")
        merged = {**defaults, **item}
        url = str(merged["url"]).strip()
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError(f"Invalid URL in source configuration: {url}")
        tags = merged.get("tags", [])
        if not isinstance(tags, list):
            raise ValueError(f"Source #{index} tags must be a list")
        sources.append(
            SourceSite(
                url=url,
                country=str(merged.get("country") or "Unknown").strip(),
                site_name=str(merged.get("site_name") or parsed.netloc).strip(),
                category=str(merged.get("category") or "unspecified").strip(),
                notes=str(merged.get("notes") or "").strip(),
                tags=[str(tag).strip() for tag in tags if str(tag).strip()],
                priority=str(merged.get("priority") or "medium").strip(),
                refresh_interval_hours=int(merged.get("refresh_interval_hours") or 24),
                preferred_language=str(merged.get("preferred_language") or "en").strip(),
            )
        )
    return sources
