"""External validation of the Idaho roll against the SoS's published registration totals.

WHY THIS EXISTS. Every Idaho voter-paper denominator descends from `id_vrdb.duckdb`'s
2026-06-29 export, and until now nothing compared that file against a number the state
published independently. New York has had this since 2026-08-11; this is Idaho's counterpart
(Washington's is `diag_wa_roll_reconciliation.py`).

WHAT IS COMPARED. The SoS publishes monthly registration totals by county and party at
`archive.voteidaho.gov/data/voter-registrations/<YYYYMM>_CountyTotals.csv` (the file behind
voteidaho.gov's "Voter Registration Totals" archive tool). The June and July 2026 files are
pinned in `docs/reference/id_registration_2026{06,07}_by_county.csv`; the extract (max
registration_date 2026-06-28) falls between them, so the two months bracket it. The published
convention for a month's as-of date is not stated by the SoS; the bracket makes that not
matter — the extract must sit near BOTH ends, and it does: against July the total differs by
127 of 1,029,811 (+0.012%) and the DEM count matches EXACTLY (121,622).

TOLERANCES are set from the measured 2026-08-15 run — July: worst county +0.13%, worst party
+0.17% (CON, n=4,095); June: worst county ±2.1%, worst party −1.25% — with modest headroom.
A failure means fix the load or re-pin against the month matching a newer extract; never widen.

Aggregate output only. Never emits a row.

Usage:
    python scripts/diag_id_roll_reconciliation.py [--selftest]
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "id_vrdb.duckdb"
PARTIES = ("CON", "DEM", "LIB", "REP", "UNA")

# (pin file, statewide tol %, county tol %, party tol %) — July is the near bracket
# (1-3 days from the extract), June the far one (a full month of churn).
PINS = [
    ("id_registration_202607_by_county.csv", 0.10, 0.75, 0.40),
    ("id_registration_202606_by_county.csv", 0.30, 3.00, 2.00),
]


def load_pin(name: str) -> dict[str, dict[str, int]]:
    path = ROOT / "docs" / "reference" / name
    with path.open(encoding="utf-8") as fh:
        rows = {r["county"]: {p: int(r[p]) for p in PARTIES} for r in csv.DictReader(fh)}
    if len(rows) != 44:
        sys.exit(f"!! {name} has {len(rows)} counties, expected 44")
    return rows


def load_ours() -> dict[str, dict[str, int]]:
    con = duckdb.connect(str(DB), read_only=True)
    try:
        raw = con.execute(
            "SELECT UPPER(TRIM(county_name)), party, COUNT(*) FROM voters "
            "GROUP BY 1, 2").fetchall()
    finally:
        con.close()
    out: dict[str, dict[str, int]] = {}
    for county, party, n in raw:
        out.setdefault(county, {p: 0 for p in PARTIES})
        if party not in PARTIES:
            sys.exit(f"!! unexpected party code {party!r} in the extract")
        out[county][party] = int(n)
    return out


def reconcile(pin_name: str, state_tol: float, county_tol: float, party_tol: float,
              ours: dict[str, dict[str, int]]) -> int:
    pin = load_pin(pin_name)
    if set(pin) != set(ours):
        print(f"!! county mismatch vs {pin_name}: {sorted(set(pin) ^ set(ours))}")
        return 1
    failures = 0
    print("-" * 88)
    print(f"vs {pin_name}  (statewide ±{state_tol}%, county ±{county_tol}%, "
          f"party ±{party_tol}%)")
    tot_pin = sum(sum(v.values()) for v in pin.values())
    tot_ours = sum(sum(v.values()) for v in ours.values())
    gap = 100.0 * (tot_ours - tot_pin) / tot_pin
    print(f"  statewide: published {tot_pin:,}  extract {tot_ours:,}  gap {gap:+.4f}%")
    if abs(gap) > state_tol:
        print(f"  !! statewide gap exceeds ±{state_tol}%")
        failures += 1
    for p in PARTIES:
        pub = sum(pin[c][p] for c in pin)
        our = sum(ours[c][p] for c in ours)
        pgap = 100.0 * (our - pub) / pub
        flag = ""
        if abs(pgap) > party_tol:
            flag = "  << FAIL"
            failures += 1
        print(f"  {p}: published {pub:>9,}  extract {our:>9,}  gap {pgap:+.4f}%{flag}")
    worst = (0.0, "")
    for c in pin:
        cp, co = sum(pin[c].values()), sum(ours[c].values())
        cgap = 100.0 * (co - cp) / max(cp, 1)
        if abs(cgap) > abs(worst[0]):
            worst = (cgap, c)
        if abs(cgap) > county_tol:
            print(f"  !! county {c}: published {cp:,} extract {co:,} gap {cgap:+.2f}%")
            failures += 1
    print(f"  worst county gap: {worst[0]:+.3f}% ({worst[1].title()})")
    return failures


def main() -> int:
    ours = load_ours()
    print("=" * 88)
    print("ID ROLL RECONCILIATION — 2026-06-29 extract vs SoS monthly registration totals")
    print("=" * 88)
    failures = 0
    for name, st, ct, pt in PINS:
        failures += reconcile(name, st, ct, pt, ours)
    print("=" * 88)
    if failures:
        print(f"FAIL — {failures} bound(s) exceeded. Fix the load or re-pin; never widen.")
        return 1
    print("OK — the extract sits inside both monthly brackets, statewide, by county and "
          "by party.")
    return 0


def selftest() -> int:
    """Prove the gate can fail: shifting 1,500 REP registrants into DEM must FAIL."""
    ours = load_ours()
    broken = {c: dict(v) for c, v in ours.items()}
    big = max(broken, key=lambda c: broken[c]["REP"])
    broken[big]["REP"] -= 1500
    broken[big]["DEM"] += 1500
    print(f">> selftest: moving 1,500 {big} registrants REP->DEM — this run MUST fail\n")
    failures = sum(reconcile(name, st, ct, pt, broken) for name, st, ct, pt in PINS)
    if failures == 0:
        print("!! selftest FAILED: the gate passed a corrupted party split")
        return 1
    print(f"\n>> selftest OK: caught ({failures} bound(s) fired).")
    return 0


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
