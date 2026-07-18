from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class SourceSite:
    url: str
    country: str = "Unknown"
    site_name: str = ""
    category: str = ""
    notes: str = ""


@dataclass(slots=True)
class RawPage:
    source: SourceSite
    final_url: str
    status_code: int
    content_type: str
    fetched_at: str
    text: str
    error: str = ""

    @classmethod
    def error_page(cls, source: SourceSite, error: str) -> "RawPage":
        return cls(
            source=source,
            final_url=source.url,
            status_code=0,
            content_type="",
            fetched_at=datetime.now(timezone.utc).isoformat(),
            text="",
            error=error,
        )


@dataclass(slots=True)
class IntelRecord:
    country: str
    source_name: str
    category: str
    url: str
    title: str
    published_at: str | None
    fetched_at: str
    summary: str
    signals: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
