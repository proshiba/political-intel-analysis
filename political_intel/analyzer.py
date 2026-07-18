from __future__ import annotations

from collections import Counter, defaultdict

from .models import IntelRecord

HIGH_IMPACT_SIGNALS = {"new_law_or_bill", "sanctions_or_trade", "security"}


def build_country_summaries(records: list[IntelRecord]) -> dict[str, dict[str, object]]:
    grouped: dict[str, list[IntelRecord]] = defaultdict(list)
    for record in records:
        grouped[record.country].append(record)

    summaries: dict[str, dict[str, object]] = {}
    for country, country_records in sorted(grouped.items()):
        signal_counts = Counter(signal for record in country_records for signal in record.signals)
        keyword_counts = Counter(keyword for record in country_records for keyword in record.keywords)
        impact_score = sum(3 if signal in HIGH_IMPACT_SIGNALS else 1 for signal, count in signal_counts.items() for _ in range(count))
        summaries[country] = {
            "record_count": len(country_records),
            "signal_counts": dict(signal_counts.most_common()),
            "top_keywords": [keyword for keyword, _ in keyword_counts.most_common(15)],
            "impact_score": impact_score,
            "notable_records": [_record_brief(record) for record in country_records[:10]],
            "insight": _insight(country, signal_counts, impact_score),
        }
    return summaries


def render_markdown_report(summaries: dict[str, dict[str, object]]) -> str:
    lines = ["# Political Intelligence Insights", ""]
    for country, summary in summaries.items():
        lines.extend([
            f"## {country}",
            f"- Records reviewed: {summary['record_count']}",
            f"- Impact score: {summary['impact_score']}",
            f"- Signals: {summary['signal_counts']}",
            f"- Top keywords: {', '.join(summary['top_keywords'])}",
            f"- Insight: {summary['insight']}",
            "",
            "### Notable records",
        ])
        for record in summary["notable_records"]:
            lines.append(f"- [{record['title']}]({record['url']}) — {record['signals']}")
        lines.append("")
    return "\n".join(lines)


def _record_brief(record: IntelRecord) -> dict[str, object]:
    return {"title": record.title, "url": record.url, "signals": record.signals, "summary": record.summary[:300]}


def _insight(country: str, signal_counts: Counter[str], impact_score: int) -> str:
    if not signal_counts:
        return f"{country} has no strong political or legal signals in the crawled material; prioritize broader source coverage."
    leading_signal, _ = signal_counts.most_common(1)[0]
    if impact_score >= 6:
        return f"{country} shows elevated activity around {leading_signal}; analysts should review source documents and downstream policy impacts."
    return f"{country} shows early activity around {leading_signal}; monitor for official follow-up and implementation details."
