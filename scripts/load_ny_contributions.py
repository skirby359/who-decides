"""Load NYSBOE per-contribution rows into ny_statewide.duckdb individual_contributions.

Why this exists: New York's campaign money was always public and the adapter already
read it, but `normalize_ny_finance` keeps only roll-up columns and throws contributor
name and ZIP away — its job was candidate_finance totals. So New York had a *federal*
donor panel and no *state* one, which is the one asymmetry in
docs/donor-class-and-the-electorate.md. This closes it.

Source: NYSBOE "Campaign Finance Disclosure Reports Contributions: Beginning 1999"
(data.ny.gov Socrata `4j2b-6a2j`), exported to CSV under data/raw/ny/. The export is
~4.3 GB / 12.6M transaction rows; DuckDB streams it, so no pandas and no download if
the CSV is already staged. Filtered to individual contributors on Schedule A
(monetary receipts) for the 2018+ cycles — see
`ny_finance.load_ny_individual_contributions` for the scope rationale.

After this, build the panel and refresh the paper's numbers:

    python scripts/load_ny_contributions.py
    STATE=NY python scripts/match_ny_voters_to_donors.py --source state
    python scripts/verify_donor_class.py

Usage:
    python scripts/load_ny_contributions.py [--csv PATH] [--cycles 2018,2020,...]
"""
import argparse
import glob
import os
import sys

import duckdb

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "src"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from wa_analyzer.etl.adapters.ny_finance import (  # noqa: E402
    DONOR_PANEL_CYCLES,
    load_ny_individual_contributions,
)

NY_STATEWIDE = "data/ny_statewide.duckdb"
DEFAULT_GLOB = "data/raw/ny/Campaign_Finance_Disclosure_Reports_Contributions*.csv"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--csv", help=f"contributions CSV (default: newest matching {DEFAULT_GLOB})")
    ap.add_argument("--cycles", help="comma-separated election years "
                                     f"(default: {','.join(map(str, DONOR_PANEL_CYCLES))})")
    args = ap.parse_args(argv)

    csv = args.csv
    if not csv:
        hits = sorted(glob.glob(DEFAULT_GLOB), key=os.path.getmtime, reverse=True)
        if not hits:
            print(f"ERROR: no contributions CSV found at {DEFAULT_GLOB}\n"
                  "  Download it from https://data.ny.gov/d/4j2b-6a2j (Export -> CSV).")
            return 1
        csv = hits[0]
    if not os.path.exists(csv):
        print(f"ERROR: not found: {csv}")
        return 1

    cycles = (tuple(int(c) for c in args.cycles.split(","))
              if args.cycles else DONOR_PANEL_CYCLES)
    print(f"[load] {os.path.basename(csv)} ({os.path.getsize(csv)/1e9:.2f} GB)")
    print(f"[load] cycles: {','.join(map(str, cycles))}")

    con = duckdb.connect(NY_STATEWIDE)  # read-write
    try:
        res = load_ny_individual_contributions(con, csv, cycles=cycles)
        print(f"  loaded {res['contributions_loaded']:,} contributions "
              f"/ ${res['total_amount']/1e6:,.1f}M")
        for cycle, n, m in con.execute("""
            SELECT election_cycle, COUNT(*), ROUND(SUM(contribution_amount)/1e6, 1)
            FROM individual_contributions WHERE contribution_id LIKE 'NY:%'
            GROUP BY 1 ORDER BY 1""").fetchall():
            print(f"    {cycle}  {n:>9,} rows  ${m:>7.1f}M")
    finally:
        con.close()
    print("\nNext: STATE=NY python scripts/match_ny_voters_to_donors.py --source state")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
