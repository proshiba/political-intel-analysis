from pathlib import Path

from political_intel.sources import load_sources


def test_load_sources_from_json_config(tmp_path: Path) -> None:
    path = tmp_path / "sources.json"
    path.write_text(
        """
        {
          "defaults": {"refresh_interval_hours": 6, "preferred_language": "en"},
          "sources": [
            {
              "country": "Japan",
              "site_name": "Kantei",
              "category": "government",
              "url": "https://example.com",
              "tags": ["official", "policy"],
              "priority": "high"
            }
          ]
        }
        """,
        encoding="utf-8",
    )

    sources = load_sources(path)

    assert len(sources) == 1
    assert sources[0].country == "Japan"
    assert sources[0].site_name == "Kantei"
    assert sources[0].tags == ["official", "policy"]
    assert sources[0].refresh_interval_hours == 6
