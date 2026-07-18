from political_intel.analyzer import build_country_summaries
from political_intel.extractor import extract_record
from political_intel.models import RawPage, SourceSite


def test_extract_record_detects_law_signal() -> None:
    page = RawPage(
        source=SourceSite(url="https://example.com", country="Japan", site_name="Gov", category="government"),
        final_url="https://example.com",
        status_code=200,
        content_type="text/html",
        fetched_at="2026-07-18T00:00:00+00:00",
        text="New Cybersecurity Act 2026-07-01. The government passed a law on cyber defense.",
    )

    record = extract_record(page)

    assert record.published_at == "2026-07-01"
    assert "new_law_or_bill" in record.signals
    assert "security" in record.signals


def test_build_country_summaries_scores_records() -> None:
    page = RawPage(
        source=SourceSite(url="https://example.com", country="Japan", site_name="Gov", category="government"),
        final_url="https://example.com",
        status_code=200,
        content_type="text/html",
        fetched_at="2026-07-18T00:00:00+00:00",
        text="A new law and security regulation was announced.",
    )
    record = extract_record(page)

    summary = build_country_summaries([record])["Japan"]

    assert summary["record_count"] == 1
    assert summary["impact_score"] >= 3
    assert "insight" in summary
