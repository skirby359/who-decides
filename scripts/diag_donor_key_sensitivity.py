"""Donor-identity KEY SENSITIVITY for cross-state-fec-money.md — the alternative-key
analysis the paper said was unbuilt (its §1 objection: "What would settle it is a
genuinely different key ... That is unbuilt"). RAISED BY AN EXTERNAL REFEREE, 2026-08-29:
"same direction" of the name+ZIP5 over-merge bias does not make the cross-state ORDERING
robust, because an uneven magnitude can reorder states. This measures how the orderings
actually move.

DESIGN — a bracketing ladder around the published key, same population as the paper
(`verify_cross_state_money.outflow()`: FEC individual rows, in-state resident donors,
positive amounts, whole loaded window):

    zip3     UPPER(TRIM(name)) + ZIP3            coarser  -> over-MERGES more than published
    zip5     UPPER(TRIM(name)) + ZIP5            the published construction
    city     UPPER(TRIM(name)) + UPPER(city)     different geography axis entirely
    zip5emp  UPPER(TRIM(name)) + ZIP5 + employer(A-Z0-9 only)
                                                 finer    -> over-SPLITS (employer strings are
                                                 noisy free text, so one person fragments
                                                 across spellings and blank-vs-filled)

The true person-level key lies between the over-merged and over-split constructions, so an
ordering that HOLDS at both ends of the ladder is bracketed, and one that FLIPS anywhere is
construction-dependent — which is exactly what the paper needs to say either way. This is a
sensitivity analysis on the loaded columns, NOT the contributor-id join a registry-grade
answer would use; FEC publishes no stable individual id, so a stronger key would need
street addresses the bulk itemized files do not carry.

Outputs one pin: docs/reference/donor_key_sensitivity_2026-08-29.csv
  - cycle='ALL' rows: n_keys, keys per resident (pinned ACS 2020-2024 denominators),
    top-1% / top-10% dollar share, Gini — per state x key.
  - per-cycle rows: top-1% share only (the abstract's "NY most top-heavy in every cycle"
    claim, re-checked under every key).

Aggregates only — no contributor row is selected or printed.

Usage (from repo root; ~1-2 min, read-only):
    python scripts/diag_donor_key_sensitivity.py [--csv docs/reference/donor_key_sensitivity_2026-08-29.csv]
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
POPS_CSV = ROOT / "docs" / "reference" / "state_population_acs2024.csv"
DEFAULT_OUT = ROOT / "docs" / "reference" / "donor_key_sensitivity_2026-08-29.csv"

STATES = ["WA", "NY", "TX", "ID"]

# The paper's population, verbatim from verify_cross_state_money.outflow():
FILT = ("regexp_matches(COALESCE(fec_candidate_id,''),'^[CPHS][0-9]') "
        "AND contributor_state='{st}' AND contribution_amount>0")

# key_id -> GROUP BY expression list (SQL). zip5 is the published construction.
KEYS = {
    "zip3": "UPPER(TRIM(contributor_name)), LEFT(COALESCE(contributor_zip,''),3)",
    "zip5": "UPPER(TRIM(contributor_name)), LEFT(COALESCE(contributor_zip,''),5)",
    "city": "UPPER(TRIM(contributor_name)), UPPER(TRIM(COALESCE(contributor_city,'')))",
    "zip5emp": ("UPPER(TRIM(contributor_name)), LEFT(COALESCE(contributor_zip,''),5), "
                "regexp_replace(UPPER(COALESCE(contributor_employer,'')),'[^A-Z0-9]','','g')"),
}
KEY_ORDER = ["zip3", "zip5", "city", "zip5emp"]


def _pops() -> dict[str, int]:
    with POPS_CSV.open(encoding="utf-8-sig", newline="") as fh:
        return {r["state"]: int(r["population"]) for r in csv.DictReader(fh)}


def pooled(con, st: str, key_sql: str) -> dict:
    """Whole-window donor-key aggregation under one key — outflow()'s shape exactly."""
    filt = FILT.format(st=st)
    n_keys, top1, top10, gini = con.execute(f"""
        WITH d AS (SELECT SUM(contribution_amount) t
                   FROM individual_contributions WHERE {filt}
                   GROUP BY {key_sql}),
             p AS (SELECT t, NTILE(100) OVER (ORDER BY t DESC) b,
                          ROW_NUMBER() OVER (ORDER BY t ASC) i,
                          COUNT(*) OVER () nn, SUM(t) OVER () s
                   FROM d)
        SELECT ANY_VALUE(nn),
               100.0*SUM(t) FILTER(WHERE b=1)/ANY_VALUE(s),
               100.0*SUM(t) FILTER(WHERE b<=10)/ANY_VALUE(s),
               (2.0*SUM(i*t)/(ANY_VALUE(nn)*ANY_VALUE(s))) - (ANY_VALUE(nn)+1.0)/ANY_VALUE(nn)
        FROM p""").fetchone()
    return dict(n_keys=int(n_keys), top1=float(top1), top10=float(top10), gini=float(gini))


def per_cycle_top1(con, st: str, key_sql: str) -> dict[int, float]:
    """Per-cycle top-1% dollar share under one key (the abstract's ordering claim)."""
    filt = FILT.format(st=st)
    rows = con.execute(f"""
        WITH dd AS (SELECT election_cycle cyc, SUM(contribution_amount) amt
                    FROM individual_contributions WHERE {filt}
                    GROUP BY election_cycle, {key_sql}),
        r AS (SELECT cyc, amt,
                     ROW_NUMBER() OVER (PARTITION BY cyc ORDER BY amt DESC) rn,
                     COUNT(*) OVER (PARTITION BY cyc) nn,
                     SUM(amt) OVER (PARTITION BY cyc) s
              FROM dd)
        SELECT cyc, 100.0*SUM(amt) FILTER (WHERE rn <= CEIL(nn*0.01))/ANY_VALUE(s)
        FROM r GROUP BY 1 ORDER BY 1""").fetchall()
    return {int(c): float(v) for c, v in rows}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    pops = _pops()
    results: dict[str, dict[str, dict]] = {}          # state -> key -> pooled dict
    cyc_top1: dict[str, dict[str, dict[int, float]]] = {}

    for st in STATES:
        con = duckdb.connect(str(DATA / f"{st.lower()}_statewide.duckdb"), read_only=True)
        results[st] = {}
        cyc_top1[st] = {}
        for k in KEY_ORDER:
            results[st][k] = pooled(con, st, KEYS[k])
            cyc_top1[st][k] = per_cycle_top1(con, st, KEYS[k])
        con.close()

    # ---- report ----------------------------------------------------------
    print("DONOR-IDENTITY KEY SENSITIVITY — same population as the paper, four keys")
    print("(zip3 = over-merged bound, zip5 = published, city = different axis, "
          "zip5emp = over-split bound)\n")
    hdr = f"{'state':6}{'key':9}{'keys':>10}{'/resident':>10}{'top-1%':>8}{'top-10%':>9}{'Gini':>8}"
    print(hdr)
    print("-" * len(hdr))
    for st in STATES:
        for k in KEY_ORDER:
            r = results[st][k]
            rate = 100.0 * r["n_keys"] / pops[st]
            print(f"{st:6}{k:9}{r['n_keys']:>10,}{rate:>9.2f}%{r['top1']:>8.1f}"
                  f"{r['top10']:>9.1f}{r['gini']:>8.3f}")
        print()

    # Orderings under each key, most-to-least.
    print("ORDERINGS (most -> least), per key:")
    verdict_lines = []
    for metric, label, rev in (("rate", "keys per resident", True),
                               ("top1", "top-1% concentration", True),
                               ("gini", "Gini", True)):
        base_order = None
        stable = True
        for k in KEY_ORDER:
            vals = {st: (100.0 * results[st][k]["n_keys"] / pops[st]) if metric == "rate"
                    else results[st][k][metric] for st in STATES}
            order = sorted(vals, key=vals.get, reverse=rev)
            if base_order is None:
                base_order = order          # zip3 first in KEY_ORDER
            if order != base_order:
                stable = False
            print(f"  {label:22} {k:9} " + " > ".join(order))
        verdict_lines.append((label, stable))
    print()
    for label, stable in verdict_lines:
        print(f"  {label}: ordering {'IDENTICAL under all four keys' if stable else '** MOVES with the key **'}")

    # The abstract's per-cycle claim under each key.
    print("\nPER-CYCLE top-1% leader, per key (abstract: 'NY most top-heavy in every cycle'):")
    ny_leads_everywhere = True
    for k in KEY_ORDER:
        cycles = sorted({c for st in STATES for c in cyc_top1[st][k]})
        leaders = []
        for c in cycles:
            row = {st: cyc_top1[st][k].get(c) for st in STATES if cyc_top1[st][k].get(c) is not None}
            leaders.append(max(row, key=row.get))
        ok = all(x == "NY" for x in leaders)
        ny_leads_everywhere &= ok
        print(f"  {k:9} leaders {cycles[0]}-{cycles[-1]}: {' '.join(leaders)}"
              f"  -> NY every cycle: {ok}")
    print(f"\n  NY most top-heavy in every cycle, under every key: {ny_leads_everywhere}")

    # ---- pin --------------------------------------------------------------
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    with args.csv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["state", "key", "cycle", "n_keys", "keys_per_resident_pct",
                    "top1_pct", "top10_pct", "gini"])
        for st in STATES:
            for k in KEY_ORDER:
                r = results[st][k]
                w.writerow([st, k, "ALL", r["n_keys"],
                            f"{100.0 * r['n_keys'] / pops[st]:.4f}",
                            f"{r['top1']:.4f}", f"{r['top10']:.4f}", f"{r['gini']:.6f}"])
        for st in STATES:
            for k in KEY_ORDER:
                for c, v in sorted(cyc_top1[st][k].items()):
                    w.writerow([st, k, c, "", "", f"{v:.4f}", "", ""])
    print(f"\nwrote {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
