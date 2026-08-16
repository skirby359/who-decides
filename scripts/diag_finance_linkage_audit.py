"""Collision audit of Finding 1's finance linkage, and the district-scoped rebuild.

WHY THIS EXISTS (money-votes referee, 2026-08-15, item 3). The finance feature behind
Finding 1's +0.58 correlation attaches receipts to candidates by ``(cycle, last name,
first initial)`` and takes the MAX across matching `candidate_finance` rows — far weaker
entity resolution than the donor papers allow themselves, with no office or district in
the key. Two failure modes: (a) a same-cycle namesake in ANY of the four office codes
(H / S / SR / SS) donates their receipts to the wrong cell; (b) a candidate with several
same-key rows resolves to the max, which is usually right (general committee dominates
primary fragments) but is asserted, not shown.

WHAT THIS SCRIPT DOES.
1. For every candidate lookup the pinned frame performs (2 per cell x 163 cells), count
   how many DISTINCT (office, district) combinations share the key in that cycle — the
   collision census.
2. Rebuild the linkage DISTRICT-SCOPED — the reviewer's preferred repair short of a
   candidate-ID join, which `candidate_finance` cannot support for PDC rows (PDC filer
   ids, FEC ids and result names have no shared id) — and recompute every cell's
   d_receipts / r_receipts / fin_log2_dr under it: office 'H' + zero-padded-or-bare
   district for cdNN cells, offices ('SR','SS') + bare-or-padded district for ldNN.
3. Diff the two linkages cell by cell, and report Finding 1's headline quantities
   (+0.58 correlation, the three funding-direction bin means) under both.
4. Recompute the FOUR competing factor correlations on the common 129-cell
   finance-complete sample (referee item 2), beside their full-sample versions.

Aggregate output only — candidate names printed are ballot names from certified results,
already public in the paper's own appendix.

Usage:
    python scripts/diag_finance_linkage_audit.py
"""
from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from wa_analyzer.analysis.national_model import _name_tokens  # noqa: E402

FRAME = ROOT / "docs" / "reference" / "overperformance_cells_2026-08-01.csv"
DB = ROOT / "data" / "wa_statewide.duckdb"
_FINANCE_OFFICES = ("H", "S", "SR", "SS")


def _cell_scope(district: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """(offices, district forms) a cell's candidates could legitimately file under."""
    num = district[2:].lstrip("0") or "0"
    if district.startswith("cd"):
        return ("H",), (num, num.zfill(2))
    return ("SR", "SS"), (num, num.zfill(2))


def load_rows(conn):
    ph = ",".join("?" for _ in _FINANCE_OFFICES)
    return conn.execute(
        f"""SELECT election_cycle, candidate_name, office, district, total_receipts
            FROM candidate_finance
            WHERE office IN ({ph}) AND total_receipts IS NOT NULL AND total_receipts > 0""",
        list(_FINANCE_OFFICES)).fetchall()


def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return sxy / math.sqrt(sxx * syy) if sxx and syy else 0.0


def main() -> int:
    cells = [r for r in csv.DictReader(FRAME.open(encoding="utf-8"))
             if r["baseline_ok"] == "True"]
    conn = duckdb.connect(str(DB), read_only=True)
    rows = load_rows(conn)
    conn.close()

    pooled: dict[tuple, float] = {}
    scopes: dict[tuple, set] = {}
    scoped: dict[tuple, float] = {}
    for cyc, name, office, dist, rec in rows:
        key = (int(cyc),) + _name_tokens(name)
        pooled[key] = max(pooled.get(key, 0.0), float(rec))
        scopes.setdefault(key, set()).add((office, str(dist)))
        skey = key + (office, str(dist))
        scoped[skey] = max(scoped.get(skey, 0.0), float(rec))

    lookups = ambiguous = moved = 0
    diffs = []
    new_fin: dict[tuple, float | None] = {}
    for c in cells:
        offices, dists = _cell_scope(c["district"])
        recs = {}
        for side in ("dem_candidate", "rep_candidate"):
            name = c[side]
            key = (int(c["year"]),) + _name_tokens(name)
            lookups += 1
            combos = scopes.get(key, set())
            in_scope = {(o, d) for o, d in combos if o in offices and d in dists}
            out_scope = combos - in_scope
            if out_scope and combos:
                ambiguous += 1
            sc = max((scoped[key + od] for od in in_scope), default=None)
            po = pooled.get(key)
            recs[side] = sc
            if (po or None) != (sc or None):
                moved += 1
                diffs.append((c["district"], c["year"], name,
                              po, sc, sorted(combos)))
        d, r = recs["dem_candidate"], recs["rep_candidate"]
        new_fin[(c["district"], c["year"])] = (
            round(math.log2(d / r), 2) if d and r else None)

    print("=" * 90)
    print("FINANCE LINKAGE AUDIT — pooled (cycle,last,initial,max) vs district-scoped")
    print("=" * 90)
    print(f"lookups performed:                  {lookups} (2 x {len(cells)} cells)")
    print(f"keys with out-of-scope collisions:  {ambiguous}")
    print(f"lookups whose receipts CHANGE:      {moved}")
    for dist, yr, name, po, sc, combos in diffs:
        print(f"  {dist}/{yr} {name}: pooled {po and f'${po:,.0f}'} -> "
              f"scoped {sc and f'${sc:,.0f}'} (key spans {combos})")

    # Finding 1 quantities under both linkages, on the SAME cells.
    both, both_new = [], []
    for c in cells:
        op = float(c["overperformance"])
        old = float(c["fin_log2_dr"]) if c["fin_log2_dr"] else None
        new = new_fin[(c["district"], c["year"])]
        if old is not None:
            both.append((old, op))
        if new is not None:
            both_new.append((new, op))
    print(f"\nFinding 1 correlation, pinned linkage:   r = {pearson(*zip(*both)):+.4f} "
          f"(n={len(both)})")
    print(f"Finding 1 correlation, scoped linkage:   r = {pearson(*zip(*both_new)):+.4f} "
          f"(n={len(both_new)})")

    # Referee item 2: every competing correlation on the common finance-complete sample.
    common = [c for c in cells if c["fin_log2_dr"]]
    print(f"\nCommon-sample factor correlations (n={len(common)} finance-complete cells) "
          f"vs full sample (n={len(cells)}):")
    for label, col in (("fundraising log2(D/R)", "fin_log2_dr"),
                       ("incumbency (signed)", "inc_signed"),
                       ("candidate quality", "candidate_quality"),
                       ("local trend", "local_trend"),
                       ("midterm year", "is_midterm")):
        op_c = [float(c["overperformance"]) for c in common]
        xs_c = [float(c[col]) for c in common]
        r_common = pearson(xs_c, op_c)
        usable = [c for c in cells if c[col] not in ("", None)]
        r_full = pearson([float(c[col]) for c in usable],
                         [float(c["overperformance"]) for c in usable])
        print(f"  {label:24s}: common {r_common:+.3f}   full {r_full:+.3f} "
              f"(n={len(usable)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
