"""Citizen voting-age population by age cohort, for any state, pinned to a CSV.

WHY THIS EXISTS SEPARATELY FROM `acs_wa_adult_age.py`. That script fetches Washington
(FIPS 53) and prints. The cross-state age paper needs the same benchmark for three states at
ONE vintage, because its age-dissimilarity index is only comparable if every state is measured
against the same ACS release — a per-run fetch would let one state's row silently move to a
newer vintage while the others stayed put, and nothing downstream would say so.

So this writes a **pinned reference CSV** rather than printing. `diag_cross_state_age_harmonized.py`
reads that file and refuses to run without it. Re-fetching is a deliberate act: pass
`--force`, and expect the harmonized figures to move.

VERIFIED AGAINST THE PUBLISHED WASHINGTON ROW. The 2024 vintage (ACS 2020-2024 5-year) returns
WA 19.8 / 26.7 / 30.9 / 22.6, which is character-identical to the CVAP row transcribed in
`docs/who-decides-washington.md` and asserted by `verify_who_decides_wa.py`. That agreement is
what identifies the vintage the series is already on; do not change it casually.

Table B29001 (Citizen, Voting-Age Population by Age) publishes exactly the four cohorts the
series uses, so no bracket arithmetic is needed and none is done — B01001, which
`acs_wa_adult_age.py` sums by hand for the all-adults row, is not used here.

Needs a free Census API key in CENSUS_API_KEY (env or repo .env).

Run:  python scripts/acs_cvap_by_state.py [--vintage 2024] [--force]
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "reference"

# The series' four cohorts, in B29001 order: 001 is the total, 002-005 are the cohorts.
COHORTS = ["18-29", "30-44", "45-64", "65+"]
_VARS = ["B29001_001E", "B29001_002E", "B29001_003E", "B29001_004E", "B29001_005E"]

# The three states with an individual-record voter file loaded. Texas is deliberately absent:
# no voter file is loaded, so it has no electorate row to compare a CVAP benchmark against.
STATES = {"WA": "53", "NY": "36", "ID": "16"}


def load_key() -> str:
    key = os.environ.get("CENSUS_API_KEY")
    if key:
        return key.strip()
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            m = re.match(r"\s*CENSUS_API_KEY\s*=\s*(.+)", line)
            if m:
                return m.group(1).strip().strip('"').strip("'")
    raise SystemExit("CENSUS_API_KEY not set (env or .env). Sign up: "
                     "https://api.census.gov/data/key_signup.html")


def fetch(vintage: int, fips: str, key: str) -> dict[str, int]:
    url = (f"https://api.census.gov/data/{vintage}/acs/acs5?get=" + ",".join(_VARS)
           + f"&for=state:{fips}&key={key}")
    with urllib.request.urlopen(url, timeout=60) as resp:
        data = json.load(resp)
    return {h: int(v) for h, v in zip(data[0], data[1]) if h.startswith("B29001")}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vintage", type=int, default=2024,
                    help="ACS 5-year end year (default 2024 = the 2020-2024 release)")
    ap.add_argument("--force", action="store_true",
                    help="overwrite an existing pin. Moves every harmonized figure.")
    args = ap.parse_args()

    out = OUT_DIR / f"cvap_age_acs{args.vintage}.csv"
    if out.exists() and not args.force:
        print(f"{out.relative_to(ROOT)} already exists — not re-fetching.")
        print("  A pin is meant to be stable; use --force if you mean to move it.")
        return 0

    key = load_key()
    rows = []
    print(f"ACS {args.vintage - 4}-{args.vintage} 5-year, table B29001 "
          f"(citizen voting-age population by age):\n")
    for st, fips in STATES.items():
        cv = fetch(args.vintage, fips, key)
        total = cv["B29001_001E"]
        counts = dict(zip(COHORTS, (cv["B29001_002E"], cv["B29001_003E"],
                                    cv["B29001_004E"], cv["B29001_005E"])))
        print(f"  {st}  total CVAP {total:>11,}")
        for c in COHORTS:
            pct = 100.0 * counts[c] / total
            print(f"        {c:6} {counts[c]:>10,}  {pct:5.1f}%")
            rows.append({"state": st, "cohort": c, "cvap": counts[c],
                         "cvap_pct": f"{pct:.4f}", "cvap_total": total,
                         "acs_vintage": args.vintage, "table": "B29001"})
        print()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"pinned -> {out.relative_to(ROOT)}  ({len(rows)} rows)")
    print("\nWashington's row is the cross-check: it must read 19.8 / 26.7 / 30.9 / 22.6, "
          "which is\nthe row who-decides-washington.md publishes and its verifier asserts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
