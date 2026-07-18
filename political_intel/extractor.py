from __future__ import annotations

import re
from collections import Counter
from .models import IntelRecord, RawPage

SIGNAL_PATTERNS = {
    "new_law_or_bill": re.compile(r"\b(bill|law|act|regulation|decree|ordinance|legislation|amendment)\b", re.I),
    "election": re.compile(r"\b(election|campaign|poll|vote|ballot|referendum)\b", re.I),
    "sanctions_or_trade": re.compile(r"\b(sanction|tariff|export control|trade restriction|embargo)\b", re.I),
    "security": re.compile(r"\b(defense|security|military|cyber|intelligence)\b", re.I),
    "budget_or_economy": re.compile(r"\b(budget|tax|inflation|subsidy|fiscal|monetary)\b", re.I),
}
STOPWORDS = {"the", "and", "for", "that", "with", "from", "this", "have", "are", "was", "were", "will", "shall", "government"}


def extract_record(page: RawPage) -> IntelRecord:
    title = _first_nonempty_line(page.text) or page.source.site_name
    published_at = _extract_date(page.text)
    summary = _summarize(page.text)
    signals = [name for name, pattern in SIGNAL_PATTERNS.items() if pattern.search(page.text)]
    keywords = _keywords(page.text)
    return IntelRecord(
        country=page.source.country,
        source_name=page.source.site_name,
        category=page.source.category,
        url=page.final_url,
        title=title[:300],
        published_at=published_at,
        fetched_at=page.fetched_at,
        summary=summary,
        signals=signals,
        keywords=keywords,
        metadata={"status_code": page.status_code, "content_type": page.content_type, "error": page.error},
    )


def _first_nonempty_line(text: str) -> str:
    return next((line.strip() for line in text.splitlines() if line.strip()), "")


def _extract_date(text: str) -> str | None:
    match = re.search(r"\b(20\d{2}[-/.年]\d{1,2}[-/.月]\d{1,2}日?)\b", text)
    if not match:
        return None
    normalized = match.group(1).replace("年", "-").replace("月", "-").replace("日", "").replace("/", "-").replace(".", "-")
    parts = [part for part in normalized.split("-") if part]
    if len(parts) != 3:
        return None
    year, month, day = parts
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _summarize(text: str, max_sentences: int = 3) -> str:
    sentences = re.split(r"(?<=[。.!?])\s+", " ".join(text.split()))
    return " ".join(sentence for sentence in sentences[:max_sentences] if sentence)[:1200]


def _keywords(text: str, limit: int = 12) -> list[str]:
    words = [word.lower() for word in re.findall(r"[A-Za-z][A-Za-z-]{3,}", text)]
    counts = Counter(word for word in words if word not in STOPWORDS)
    return [word for word, _ in counts.most_common(limit)]
