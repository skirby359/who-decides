"""Pin the New York registration roll that `who-decides-new-york.md` measures against.

WHY THIS EXISTS, and why the premise it replaces was wrong. Washington's roll was pinned
(`pin_wa_donor_roll.py`) because `voter_scores` is rebuilt on every ballot load. New York was
left unpinned on the reasoning that its NYSVOTER file is a static FOIL extract and therefore
cannot move.

It moved. When `verify_who_decides_ny.py` gained real assertions on 2026-08-01, Sections III
and IV did not reproduce, on either the active or the full roll, and every deviation ran the
same way — the roll as it stood was younger and less participating than the one those tables
were computed on. Sections I and II reproduced exactly, all thirty-nine cells. That split is
the whole diagnosis: I and II are ELECTORATE-denominated, and the set of people who voted in
a past election cannot change when registrants are added; III and IV are ROLL-denominated,
and they can. A static extract is static until it is reloaded, and a reload is invisible to a
paper that names no snapshot.

So this pins the denominator, not the answers. The tables are still derived from scratch on
every run — the snapshot only fixes WHICH registrants they are derived over, which is the
thing that drifted.

WHAT IS CAPTURED, and what deliberately is not. One row per registrant — ALL of them, with an
`is_active` flag, not just the active ones — carrying only what the paper's roll-denominated
cuts read: the party bucket and the birth year. All of them, because §III states the blank
share on both bases ("25.3% of the active roll; 25.5% of the full roll") and pinning only the
active side would leave half the sentence free to drift. Nothing else. Participation is not copied — `voter_participation` records past elections and does not
drift, so joining to it live is correct and copying it would only create a second thing to
keep in step. Neither is the donor panel: its specification is the donor paper's to set (the
full-name key, 558,017 New York voters) and freezing a copy here would let the two diverge
silently, which is the failure this script exists to prevent, one level up.

Birth YEAR rather than date of birth, because that is all the analysis reads —
`date_diff('year', ...)` returns the difference of year parts — and because New York's full
DOB was deliberately minimised on 2026-07-30. A snapshot that reintroduced it would quietly
undo that.

IT IS PERSON-LEVEL, and is treated as such. The table carries `state_voter_id`, so it is
registered in `config/product/restricted_fields.yml` alongside Washington's and is unreachable
through the product firewall's allowlisted view. It lives only in the gitignored database and
is never exported.

RE-PINNING IS A DELIBERATE ACT. Without `--force` this refuses to overwrite, because a silent
re-pin would reintroduce exactly the drift the snapshot prevents, invisibly and mid-review. If
you do re-pin, expect `verify_who_decides_ny.py` to fail on Sections III and IV and update the
paper to match. That friction is the point.

Run:  python scripts/pin_ny_roll.py            # create, or report the existing pin
      python scripts/pin_ny_roll.py --force    # re-pin, knowingly
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
NY_DB = ROOT / "data" / "ny_vrdb.duckdb"
TABLE = "ny_paper_roll"
META = "ny_paper_roll_meta"

NOTE = ("all registrants, one row per state_voter_id, with party bucket, is_active "
        "and birth year, pinned so who-decides-new-york.md's roll-denominated sections III "
        "and IV do not drift when the NYSVOTER extract is reloaded; duplicate identifiers "
        "collapsed deterministically via MIN(STRUCT_PACK(...))")


def describe(con) -> None:
    n, na = con.execute(
        f"SELECT COUNT(*), COUNT(*) FILTER (WHERE is_active) FROM {TABLE}").fetchone()
    print(f"  {TABLE}: {n:,} registrants ({na:,} active)")
    for pinned_on, n_voters, _ in con.execute(f"SELECT * FROM {META}").fetchall():
        print(f"  pinned {pinned_on} at {n_voters:,} registrants")
    mix = con.execute(f"""
        SELECT party, ROUND(100.0*COUNT(*) FILTER (WHERE is_active)
                            / SUM(COUNT(*) FILTER (WHERE is_active)) OVER (), 2)
        FROM {TABLE} GROUP BY 1 ORDER BY 2 DESC""").fetchall()
    print("  active party mix: " + ", ".join(f"{p} {v}%" for p, v in mix))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force", action="store_true",
                    help="re-pin over an existing snapshot. Changes published figures.")
    args = ap.parse_args()

    if not NY_DB.exists():
        print(f"!! {NY_DB} not found")
        return 1

    con = duckdb.connect(str(NY_DB))
    try:
        existing, = con.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
            [TABLE]).fetchone()
        if existing and not args.force:
            print(f"{TABLE} already exists — not re-pinning. Use --force if you mean to.")
            describe(con)
            print("\n  Re-pinning changes published figures: verify_who_decides_ny.py will "
                  "fail on\n  sections III and IV and the paper has to be updated to match. "
                  "That is the\n  intended friction.")
            return 0

        # NYSVOTER carries 36 state_voter_ids twice among active registrants (72 rows), and
        # they are NOT duplicate copies: 8 disagree on party, 25 on congressional district,
        # 1 on birth year. Two records share an identifier. A roll is one row per registrant,
        # so the snapshot collapses them — but deterministically, and to a row that actually
        # exists. MIN over a STRUCT rather than column-wise MIN: column-wise MIN is stable
        # but can invent a (party, birth_year) pair no record has, which is the determinism
        # trap already recorded in CLAUDE.md.
        con.execute(f"DROP TABLE IF EXISTS {TABLE}")
        con.execute(f"""
            CREATE TABLE {TABLE} AS
            WITH src AS (
                SELECT state_voter_id,
                       CASE WHEN party = 'DEM' THEN 'DEM' WHEN party = 'REP' THEN 'REP'
                            WHEN party = 'BLK' THEN 'NOPARTY' ELSE 'OTHER' END AS party,
                       EXTRACT(year FROM birthdate)::INTEGER AS birth_year,
                       (status_code = 'A') AS is_active
                FROM voters),
            picked AS (
                SELECT state_voter_id,
                       MIN(STRUCT_PACK(party := party, birth_year := birth_year,
                                       is_active := is_active)) AS r
                FROM src GROUP BY 1)
            SELECT state_voter_id, r.party AS party, r.birth_year AS birth_year,
                   r.is_active AS is_active FROM picked""")
        n, = con.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()

        # One row per registrant, or every denominator built on this is wrong.
        dupes, = con.execute(f"""
            SELECT COUNT(*) FROM (SELECT state_voter_id FROM {TABLE}
                                  GROUP BY 1 HAVING COUNT(*) > 1)""").fetchone()
        if dupes:
            print(f"!! {dupes} duplicated state_voter_id in the snapshot — refusing to keep it")
            con.execute(f"DROP TABLE {TABLE}")
            return 1

        # The snapshot must equal the live roll's DISTINCT registrant count on the day it is
        # taken, or it has frozen something other than what is on disk.
        live_rows, live_ids = con.execute(
            "SELECT COUNT(*), COUNT(DISTINCT state_voter_id) FROM voters").fetchone()
        if n != live_ids:
            print(f"!! snapshot {n:,} != live distinct registrants {live_ids:,} "
                  f"— refusing to keep it")
            con.execute(f"DROP TABLE {TABLE}")
            return 1
        if live_rows != live_ids:
            print(f"  collapsed {live_rows - live_ids} duplicate identifier row(s): "
                  f"{live_rows:,} rows -> {n:,} registrants")

        con.execute(f"CREATE TABLE IF NOT EXISTS {META} "
                    "(pinned_on VARCHAR, n_voters BIGINT, note VARCHAR)")
        con.execute(f"DELETE FROM {META}")
        con.execute(f"INSERT INTO {META} VALUES (?, ?, ?)",
                    [date.today().isoformat(), n, NOTE])
        print(f"pinned {TABLE}")
        describe(con)
        print("\n  Next: PYTHONPATH=src python scripts/verify_who_decides_ny.py")
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
