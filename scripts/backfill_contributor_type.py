"""One-shot backfill of ``individual_contributions.contributor_type``.

Populates the column added 2026-07-27 for rows loaded before it existed, so the
voter-donor matcher can exclude organisations from a real source field rather than a name
heuristic. Loaders emit the value going forward, so this is a historical operation, not a
recurring chore.

NO SOURCE FILE IS RE-READ. FEC bulk (``entity_tp='IND'``), the two FEC API paths
(``&is_individual=true``), WA PDC (``contributor_category='Individual'``) and NY
(``CNTRBR_TYPE_DESC='INDIVIDUAL'``) all filtered to natural persons at load, so their type
is recoverable from the ``contribution_id`` prefix alone.

**Idaho Sunshine is deliberately excluded and its rows stay NULL.** It applies no person
filter at load, so its per-row type is only recoverable by re-reading the source — a
delete-then-insert reload that is the one irreversible step in this change and is deferred
to its own commit. NULL reads as "never backfilled" (distinct from ``UNKNOWN``, which means
the source said nothing), so ``--report`` shows the migration state of any database
without consulting a log.

Idempotent: every UPDATE carries ``AND contributor_type IS NULL``, so a second run matches
zero rows and never overwrites an existing value.

Note DuckDB implements UPDATE as delete+insert and does not reclaim the superseded row
groups in place, so expect the file to grow. Only ``EXPORT DATABASE`` / ``IMPORT`` truly
compacts. Rehearse on a copy before touching a database you care about.

Run:  python scripts/backfill_contributor_type.py --db data/wa_statewide.duckdb
      python scripts/backfill_contributor_type.py --all
      python scripts/backfill_contributor_type.py --all --report   # read-only census
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
# scripts/donor_matcher.py is the standalone extract of the private matcher and carries
# these two helpers, so this script needs no PYTHONPATH and no src/ tree.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from donor_matcher import (  # noqa: E402
    backfill_contributor_type, ensure_contributor_type_column,
)

DEFAULT_DBS = [
    "data/wa_statewide.duckdb",
    "data/ny_statewide.duckdb",
    "data/id_statewide.duckdb",
    "data/tx_statewide.duckdb",
]


def census(con) -> dict[str, int]:
    return {
        (t or "NULL"): int(n) for t, n in con.execute(
            "SELECT contributor_type, COUNT(*) FROM individual_contributions "
            "GROUP BY 1 ORDER BY 2 DESC").fetchall()
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", action="append", default=None,
                    help="database to backfill (repeatable)")
    ap.add_argument("--all", action="store_true",
                    help=f"backfill all of: {', '.join(DEFAULT_DBS)}")
    ap.add_argument("--report", action="store_true",
                    help="read-only: print the contributor_type census and exit")
    args = ap.parse_args()

    targets = args.db or (DEFAULT_DBS if args.all else None)
    if not targets:
        ap.error("pass --db PATH (repeatable) or --all")

    rc = 0
    for rel in targets:
        path = ROOT / rel if not Path(rel).is_absolute() else Path(rel)
        if not path.exists():
            print(f"\n-- {rel}: missing, skipped")
            continue
        print(f"\n{'=' * 78}\n{rel}\n{'=' * 78}")
        try:
            con = duckdb.connect(str(path), read_only=args.report)
        except duckdb.IOException as e:
            print(f"  !! cannot open (another process holds it?): {str(e)[:120]}")
            rc = 1
            continue
        try:
            has_ic = con.execute(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_name = 'individual_contributions'").fetchone()[0]
            if not has_ic:
                print("  no individual_contributions table — skipped")
                continue
            if args.report:
                ensure = {r[0] for r in con.execute(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'individual_contributions'").fetchall()}
                if "contributor_type" not in ensure:
                    print("  contributor_type column ABSENT (not yet migrated)")
                    continue
                for t, n in census(con).items():
                    print(f"    {t:14}{n:>12,}")
                continue

            ensure_contributor_type_column(con)
            res = backfill_contributor_type(con)
            for rule, info in res["updated_by_rule"].items():
                print(f"    {rule:14}{info['rows']:>12,}   {info['why']}")
            print("\n  census after:")
            for t, n in res["by_type"].items():
                print(f"    {t:14}{n:>12,}")
            if res["unresolved_by_prefix"]:
                print("\n  still NULL (awaiting a source reload):")
                for p, n in res["unresolved_by_prefix"].items():
                    print(f"    {p:14}{n:>12,}")
            if res["unknown_type_rows"]:
                print(f"\n  UNKNOWN-typed rows (source carried a blank type): "
                      f"{res['unknown_type_rows']:,}")
            con.execute("CHECKPOINT")
        finally:
            con.close()
    if not args.report:
        print("\nDone. Re-run any time — the backfill is idempotent.")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
