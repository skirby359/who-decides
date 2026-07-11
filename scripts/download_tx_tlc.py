"""Download + place Texas Legislative Council Capitol Data Portal election returns.

The Texas Legislative Council (TLC) Capitol Data Portal (data.capitol.texas.gov)
publishes canvass-grade, VTD-level general-election returns as per-census-vintage
ZIPs, each containing one ``<year>_General_Election_Returns.csv`` per cycle with a
stable header::

    County,FIPS,VTD,cntyvtd,vtdkeyvalue,Office,Name,Party,Incumbent,Votes

This is the authoritative replacement for the community OpenElections-TX precinct
files (which had per-county mixed granularity / double-counting and only 101/254
counties for 2022). TLC rollups match the official SoS canvass exactly and cover
all 254 counties every cycle, and carry an ``Incumbent`` Y/N flag that feeds the
R-incumbency backtest directly.

This script downloads the vintage ZIPs, extracts the year CSVs we need for the
backtest window (2016/2018/2020/2022) plus 2024, and places each under
``data/raw/tx/<election_date_slug>/`` where the calendar-driven loader
(:func:`wa_analyzer.etl.election_results.load_all_results_adapter`) finds it.
Idempotent: skips downloads/extractions already present. Re-runnable.

Note (vintage labelling): a ZIP is named for its VTD vintage, NOT its content —
the "2020 General" zip actually holds 2012-2021 returns re-tabulated onto 2020
VTDs. We pull each year CSV from the appropriate vintage zip. County rollups are
vintage-stable; VTD-level cross-vintage joins are NOT (precincts renumber at each
redistricting — the same break WA hit in 2022).
"""

from __future__ import annotations

import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "tx"
ZIPS = RAW / "_tlc_zips"

# Verified direct-download URLs (data.capitol.texas.gov CKAN resources, no auth).
# All three verified (HTTP 200; rollups match the official canvass). 2024vtg lives
# in the SAME CKAN package as 2020vtg (35b16aee-...), resolved via the CKAN
# resource_show API. A download failure is non-fatal — it only affects the 2024
# cycle (the 2026 baseline), not the 2016-2022 backtest window.
VINTAGE_ZIPS = {
    "2020vtg": "https://data.capitol.texas.gov/dataset/35b16aee-0bb0-4866-b1ec-859f1f044241/resource/5af9f5e2-ca14-4e5d-880e-3c3cd891d3ed/download/2020-general-vtd-election-data-2020.zip",
    "2022vtg": "https://data.capitol.texas.gov/dataset/aab5e1e5-d585-4542-9ae8-1108f45fce5b/resource/b9ebdbdb-3e31-4c98-b158-0e2993b05efc/download/2022-general-vtds-election-data.zip",
    "2024vtg": "https://data.capitol.texas.gov/dataset/35b16aee-0bb0-4866-b1ec-859f1f044241/resource/e1cd6332-6a7a-4c78-ad2a-852268f6c7a2/download/2024-general-vtds-election-data.zip",
}

# TLC per-plan "r206 Election24G" reports: 2024 presidential by district on the
# maps used in 2026. CD = the enacted 2025 mid-decade redraw (PLANC2333);
# House/Senate = the stable 2021 maps (PLANH2316 / PLANS2168). These feed the
# 2026 district forecast (scripts/forecast_tx_2026.py) — they cover EVERY
# district (incl. uncontested / off-cycle senate seats) which the per-VTD
# election results cannot. Verified direct-download URLs (resolved via CKAN).
PLAN_REPORTS = {
    "planc2333_r206_election24g.xls": "https://data.capitol.texas.gov/dataset/748c952b-e926-4f44-8d01-a738884b3ec8/resource/5df18f83-bd79-4088-b6d3-b05778403693/download/planc2333_r206_election24g.xls",
    "planh2316_r206_election24g.xls": "https://data.capitol.texas.gov/dataset/71af633c-21bf-42cf-ad48-4fe95593a897/resource/30c0c5b7-c512-4a94-af01-afdcff39baf5/download/planh2316_r206_election24g.xls",
    "plans2168_r206_election24g.xls": "https://data.capitol.texas.gov/dataset/70836384-f10c-423d-a36e-748d7e000872/resource/e3eda2c0-627e-4c29-b1bd-35c55f594800/download/plans2168_r206_election24g.xls",
}

# (election year, date_slug, vintage zip, member CSV name) — the loader looks
# under data/raw/tx/<date_slug>/.
PLACEMENTS = [
    (2016, "20161108", "2020vtg", "2016_General_Election_Returns.csv"),
    (2018, "20181106", "2020vtg", "2018_General_Election_Returns.csv"),
    (2020, "20201103", "2020vtg", "2020_General_Election_Returns.csv"),
    (2022, "20221108", "2022vtg", "2022_General_Election_Returns.csv"),
    (2024, "20241105", "2024vtg", "2024_General_Election_Returns.csv"),
]


def _download(name: str, url: str) -> Path:
    ZIPS.mkdir(parents=True, exist_ok=True)
    dest = ZIPS / f"{name}.zip"
    if dest.exists() and dest.stat().st_size > 1_000_000:
        print(f"  {name}: present ({dest.stat().st_size/1e6:.1f} MB)")
        return dest
    print(f"  {name}: downloading {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
    with urllib.request.urlopen(req, timeout=600) as r, open(dest, "wb") as out:
        out.write(r.read())
    print(f"  {name}: {dest.stat().st_size/1e6:.1f} MB")
    return dest


def main(years: set[int] | None = None) -> None:
    print("Texas Legislative Council election returns — download + place")
    needed_vintages = {v for (yr, _slug, v, _csv) in PLACEMENTS
                       if years is None or yr in years}
    print("Downloading vintage zips:", sorted(needed_vintages))
    zip_paths = {v: _download(v, VINTAGE_ZIPS[v]) for v in needed_vintages}

    for year, slug, vintage, csv_name in PLACEMENTS:
        if years is not None and year not in years:
            continue
        slug_dir = RAW / slug
        slug_dir.mkdir(parents=True, exist_ok=True)
        # Remove any stale OpenElections precinct file (the loader would prefer
        # a name containing 'precinct' over the TLC file).
        for stale in slug_dir.glob("*precinct*.csv"):
            print(f"  {year}: removing stale {stale.name}")
            stale.unlink()
        dest = slug_dir / csv_name
        if dest.exists() and dest.stat().st_size > 100_000:
            print(f"  {year}: already placed ({dest.stat().st_size/1e6:.1f} MB)")
            continue
        with zipfile.ZipFile(zip_paths[vintage]) as z:
            try:
                with z.open(csv_name) as src, open(dest, "wb") as out:
                    out.write(src.read())
            except KeyError:
                print(f"  {year}: ERROR — {csv_name} not found in {vintage}.zip")
                continue
        print(f"  {year}: placed -> {dest.relative_to(ROOT)} ({dest.stat().st_size/1e6:.1f} MB)")

    # Per-plan r206 election reports (for the 2026 district forecast).
    plans_dir = RAW / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)
    print("Downloading per-plan r206 Election24G reports (2026 district forecast):")
    for fn, url in PLAN_REPORTS.items():
        dest = plans_dir / fn
        if dest.exists() and dest.stat().st_size > 10_000:
            print(f"  {fn}: present ({dest.stat().st_size/1e3:.0f} KB)")
            continue
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
            with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as out:
                out.write(r.read())
            print(f"  {fn}: {dest.stat().st_size/1e3:.0f} KB")
        except Exception as e:  # noqa: BLE001 — non-fatal; forecast can re-fetch
            print(f"  {fn}: ERROR {type(e).__name__} {e}")

    print("Done. Load with: STATE=TX python main.py load-tx-results  (or the "
          "adapter-driven loader); forecast with scripts/forecast_tx_2026.py.")


if __name__ == "__main__":
    yrs = {int(a) for a in sys.argv[1:] if a.isdigit()} or None
    main(yrs)
