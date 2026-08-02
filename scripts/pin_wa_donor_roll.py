"""Pin the Washington analysis roll the donor paper measures against.

WHY THIS EXISTS. The paper's Washington denominators read the `ld` scope of `voter_scores`,
which is a LIVE table: `refresh-gotv` rebuilds it on every ballot load, and each improvement to
the VRDB precinct crosswalk brings previously unscoped voters into district scope. The roll
therefore grows a little every few days. On 2026-07-30 a two-row crosswalk bridge moved three
published counts — small, but the direction of travel is that a reviewer who re-runs
`verify_donor_class.py` next month gets numbers the paper does not contain, and the natural
reading of that is that the paper is wrong.

A dated snapshot fixes it: the figure a reviewer computes equals the figure the paper prints,
permanently, and the paper can name the date its roll was taken.

WHAT IS CAPTURED. One row per voter in the `ld` scope, with the four columns the donor paper's
derivations actually read. Nothing else — this is a denominator, not a copy of the roll. It
carries `state_voter_id`, so it is person-level: the table is added to the product firewall's
restricted list and lives only in the gitignored database.

The `ld` scope rather than `cd` because the cd scope is still incomplete; see CLAUDE.md.

REBUILDING IT IS A DELIBERATE ACT. Without `--force` this refuses to overwrite an existing
snapshot, because silently re-pinning would reintroduce exactly the drift the snapshot exists to
prevent — and would do it invisibly, mid-review. If you do re-pin, expect the verifier to fail
on the counts and update the paper to match.

Run:  python scripts/pin_wa_donor_roll.py            # create, or report the existing pin
      python scripts/pin_wa_donor_roll.py --force    # re-pin, knowingly
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
WA_DB = ROOT / "data" / "wa_statewide.duckdb"
TABLE = "donor_paper_wa_roll"
META = "donor_paper_wa_roll_meta"


def describe(con) -> None:
    n, = con.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()
    rows = con.execute(f"SELECT pinned_on, n_voters FROM {META}").fetchall()
    print(f"  {TABLE}: {n:,} voters")
    for pinned_on, n_voters in rows:
        print(f"  pinned {pinned_on} at {n_voters:,} voters")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force", action="store_true",
                    help="re-pin over an existing snapshot. Changes published counts.")
    args = ap.parse_args()

    if not WA_DB.exists():
        print(f"!! {WA_DB} not found")
        return 1

    con = duckdb.connect(str(WA_DB))
    try:
        existing = con.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
            [TABLE]).fetchone()[0]
        if existing and not args.force:
            print(f"{TABLE} already exists — not re-pinning. Use --force if you mean to.")
            describe(con)
            print("\n  Re-pinning changes published counts: the verifier will fail on them\n"
                  "  and the paper has to be updated to match. That is the intended friction.")
            return 0

        con.execute(f"DROP TABLE IF EXISTS {TABLE}")
        con.execute(f"""
            CREATE TABLE {TABLE} AS
            SELECT DISTINCT state_voter_id, age_cohort, is_super_voter, turnout_propensity
            FROM voter_scores
            WHERE LEFT(district_id, 2) = 'ld'""")
        n, = con.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()
        # One row per voter, or every denominator built on this is wrong.
        dupes, = con.execute(f"""
            SELECT COUNT(*) FROM (SELECT state_voter_id FROM {TABLE}
                                  GROUP BY 1 HAVING COUNT(*) > 1)""").fetchone()
        if dupes:
            print(f"!! {dupes} duplicated state_voter_id in the snapshot — refusing to keep it")
            con.execute(f"DROP TABLE {TABLE}")
            return 1

        con.execute(f"CREATE TABLE IF NOT EXISTS {META} "
                    "(pinned_on VARCHAR, n_voters BIGINT, note VARCHAR)")
        con.execute(f"DELETE FROM {META}")
        con.execute(f"INSERT INTO {META} VALUES (?, ?, ?)",
                    [date.today().isoformat(), n,
                     "ld-scope of voter_scores, pinned so the donor paper's WA denominators "
                     "do not drift as the precinct crosswalk improves"])
        print(f"pinned {TABLE}")
        describe(con)
        print("\n  Next: PYTHONPATH=src python scripts/verify_donor_class.py --refresh")
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
