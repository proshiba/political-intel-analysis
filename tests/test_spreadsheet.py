from pathlib import Path

from political_intel.spreadsheet import load_sites


def test_load_sites_from_csv(tmp_path: Path) -> None:
    path = tmp_path / "sites.csv"
    path.write_text("country,site_name,category,url\nJapan,Kantei,government,https://example.com\n", encoding="utf-8")

    sites = load_sites(path)

    assert len(sites) == 1
    assert sites[0].country == "Japan"
    assert sites[0].site_name == "Kantei"
    assert sites[0].url == "https://example.com"
