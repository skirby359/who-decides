"""Snapshot every donor panel to a `*_alltier` copy BEFORE the tier switch.

Run this exactly once, before any panel is rebuilt on the full-name-only specification
(2026-07-27). It is the first step of that change and nothing else may precede it.

WHY A COPY AND NOT A DERIVATION. All-tier is a SUPERSET of full-name-only, so it cannot
be reconstructed from the rebuilt panels — the weak-tier rows are simply gone. Three
things need the superset to keep working:

  1. Appendix F's tier-sensitivity table, which compares specifications and is
     meaningless against a single-tier panel.
  2. `score_match_validation.py`'s reweighting, which describes the SUPERSEDED all-tier
     specification and must keep reproducing 93.0%.
  3. `diag_match_validation_stratified.py` and the human-review sampler, which stratify
     by tier — the three weak tiers become unsampleable once the primaries are rebuilt,
     which would kill the by-tier inter-rater agreement.

ELEVEN TABLES, not six. The "six panels" language everywhere in the paper omits the two
Idaho period-aligned panels and the three pooled tables. `verify_donor_class.py` and
`report_aligned` key on the bare `_aligned` names and print a "not built" branch rather
than failing, so a missed aligned snapshot is silent.

REFUSES TO OVERWRITE. If a `*_alltier` table already exists this aborts that table
rather than re-copying: after the rebuild, a second run would overwrite the only
surviving all-tier artifact with a full-name-only copy and destroy it irrecoverably.

Writes a committed census manifest (row counts, dollar sums, per-tier composition) so a
reviewer can later check the snapshots against the state of the world on this date.

Run:  python scripts/snapshot_alltier_panels.py
      python scripts/snapshot_alltier_panels.py --dry-run
"""
from __future__ import annotations

import argparse
import csv
from datetime import date
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MANIFEST = ROOT / "docs" / "reference" / "panel_snapshot_2026-07-27.csv"

SUFFIX = "_alltier"

# (state, statewide db). Every panel table present in a DB is snapshotted; the aligned
# panels exist only for Idaho, and the pooled table exists for all three.
STATES = [("WA", "wa_statewide"), ("NY", "ny_statewide"), ("ID", "id_statewide")]

PANELS = [
    "voter_donor_affiliation",                  # legacy pooled — campaign tooling reads this
    "voter_donor_affiliation_fec",
    "voter_donor_affiliation_state",
    "voter_donor_affiliation_fec_aligned",      # Idaho only
    "voter_donor_affiliation_state_aligned",    # Idaho only
]


def has_table(con, t: str) -> bool:
    return con.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?", [t]
    ).fetchone()[0] > 0


def census(con, t: str) -> dict:
    n, tot = con.execute(
        f"SELECT COUNT(*), COALESCE(SUM(total_donated), 0) FROM {t}").fetchone()
    tiers = dict(con.execute(
        f"SELECT match_quality, COUNT(*) FROM {t} GROUP BY 1").fetchall())
    tier_d = {k: float(v or 0) for k, v in con.execute(
        f"SELECT match_quality, SUM(total_donated) FROM {t} GROUP BY 1").fetchall()}
    return {"rows": int(n), "total_donated": float(tot),
            "tiers": tiers, "tier_dollars": tier_d}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would be snapshotted; write nothing")
    args = ap.parse_args()

    rows_out: list[dict] = []
    made = skipped = refused = 0

    for state, db in STATES:
        path = DATA / f"{db}.duckdb"
        if not path.exists():
            print(f"  !! {state}: {path.name} missing — skipped")
            continue
        con = duckdb.connect(str(path), read_only=args.dry_run)
        print(f"\n{'=' * 78}\n{state}  ({db})\n{'=' * 78}")
        for panel in PANELS:
            snap = panel + SUFFIX
            if not has_table(con, panel):
                print(f"  -- {panel:42} absent")
                skipped += 1
                continue
            src = census(con, panel)
            if has_table(con, snap):
                # Never re-copy. Post-rebuild this would overwrite the only all-tier
                # artifact with a full-name-only copy.
                dst = census(con, snap)
                print(f"  !! {snap:42} ALREADY EXISTS — refusing to overwrite")
                print(f"       existing: {dst['rows']:>9,} rows  "
                      f"${dst['total_donated'] / 1e6:9.2f}M  tiers={len(dst['tiers'])}")
                print(f"       source:   {src['rows']:>9,} rows  "
                      f"${src['total_donated'] / 1e6:9.2f}M  tiers={len(src['tiers'])}")
                refused += 1
                continue
            if args.dry_run:
                print(f"  would copy {panel} -> {snap}  "
                      f"({src['rows']:,} rows, ${src['total_donated'] / 1e6:.2f}M)")
                made += 1
                continue

            con.execute(f"CREATE TABLE {snap} AS SELECT * FROM {panel}")
            dst = census(con, snap)
            # Exact equality, not a tolerance: this is a plain copy.
            assert dst["rows"] == src["rows"], f"{snap} row mismatch"
            assert abs(dst["total_donated"] - src["total_donated"]) < 0.005, \
                f"{snap} dollar mismatch"
            assert dst["tiers"] == src["tiers"], f"{snap} tier composition mismatch"
            print(f"  OK {panel} -> {snap}")
            print(f"       {src['rows']:>9,} rows  ${src['total_donated'] / 1e6:9.2f}M")
            for q, n in sorted(src["tiers"].items(), key=lambda x: -x[1]):
                print(f"         {q:20}{n:>9,}  "
                      f"${src['tier_dollars'].get(q, 0) / 1e6:8.2f}M")
            made += 1

            for q, n in src["tiers"].items():
                rows_out.append({
                    "snapshot_date": date(2026, 7, 27).isoformat(),
                    "state": state, "db": db, "panel": panel, "snapshot_table": snap,
                    "match_tier": q, "rows": n,
                    "total_donated": round(src["tier_dollars"].get(q, 0.0), 2),
                    "panel_rows": src["rows"],
                    "panel_total_donated": round(src["total_donated"], 2),
                })
        con.close()

    print(f"\n{'=' * 78}")
    print(f"snapshotted {made} | absent {skipped} | refused (already existed) {refused}")
    if refused:
        print("\n!! Refusals mean those panels were snapshotted by an earlier run.")
        print("   That is expected on a re-run and is NOT an error. Do not force it:")
        print("   overwriting a snapshot after a rebuild destroys the all-tier artifact.")

    if rows_out and not args.dry_run:
        MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        with open(MANIFEST, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows_out[0].keys()))
            w.writeheader()
            w.writerows(rows_out)
        print(f"\nmanifest -> {MANIFEST.relative_to(ROOT)}  ({len(rows_out)} rows)")
        print("Commit it: it is the record of the pre-switch world.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
