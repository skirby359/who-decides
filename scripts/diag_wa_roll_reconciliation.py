"""External validation of the WA roll against the SoS's certified registration counts.

WHY THIS EXISTS. Every WA voter-paper denominator descends from `wa_vrdb.duckdb`'s April 1 2026
extract, and until now nothing compared that file's per-county registrant counts against a
number the state published independently. New York has had this check since 2026-08-11
(`diag_ny_enrollment_validation.py`); Washington and Idaho did not — and the first run of this
script found a defect the papers' own verifiers were structurally blind to (below).

WHAT IS COMPARED. The certified November 4 2025 general's turnout page publishes registered
voters per county — the official election denominator, which the WA paper itself shows is the
ACTIVE roll (2,001,425 ballots / 39.24% official turnout = 5,100,471 ≈ the active roll). That
page is pinned, county by county, in `docs/reference/wa_registration_20251104_by_county.csv`.
This script compares it against `COUNT(*)` of active registrants per county in the extract,
five months later. The gap per county is five months of net churn (new registrations, NVRA
maintenance, moves) plus any load defect; statewide the two agree to −0.05%.

WHAT THE FIRST RUN FOUND (2026-08-15). Kittitas and Klickitat were mirror-swapped — our labels
carried ~16.4K/~32.0K against certified 32,251/16,421, gaps of −49% and +95% in a run where
every other county landed within ±3%. The mechanism is the KT/KS county-code inversion known
since 2026-04-30 (`config/counties.py`, `docs/known_issues.md`) and assessed then as cosmetic;
the VRDB loader shares the map, so the inversion reached `voters.county_name` and, through it,
the published Appendix E county table (`who-decides-wa-corrections-ledger.md` C12).

THE SWAP IS ENCODED, NOT TOLERATED. The load stays inverted deliberately (the precinct
namespace and the VRDB crosswalk are internally consistent on the inverted labels), so this
script applies the SAME documented label correction the paper's verifier applies, and then
requires all 39 counties within tolerance. If the mapping is ever fixed and the VRDB reloaded,
the correction double-swaps, the two counties blow through the tolerance, and this script fails
loudly — remove the correction here and in `verify_who_decides_wa.py` together.

TOLERANCES are set from the measured 2026-08-15 run (worst county +3.0% Ferry, statewide
−0.05%) with headroom for churn, far below anything that would indicate a load defect. A
failure means fix the load or re-pin against a newer certified page — never widen the bound.

Aggregate output only. Never emits a row.

Usage:
    python scripts/diag_wa_roll_reconciliation.py [--selftest]
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
PIN = ROOT / "docs" / "reference" / "wa_registration_20251104_by_county.csv"
DB = ROOT / "data" / "wa_vrdb.duckdb"

# The two-county label correction — see the module docstring. Applied to OUR side.
LABEL_FIX = {"KITTITAS": "KLICKITAT", "KLICKITAT": "KITTITAS"}

STATEWIDE_TOL_PCT = 0.5   # measured -0.05%
COUNTY_TOL_PCT = 5.0      # measured worst +3.0% (Ferry, n=5,208); small counties churn most

# The certified statewide total on the pinned page, asserted so a re-pin against a different
# election cannot silently keep this script's tolerances.
PINNED_STATEWIDE = 5_100_871


def load_pin() -> dict[str, int]:
    with PIN.open(encoding="utf-8") as fh:
        rows = {r["county"]: int(r["registered_voters"]) for r in csv.DictReader(fh)}
    if len(rows) != 39:
        sys.exit(f"!! pin has {len(rows)} counties, expected 39")
    if sum(rows.values()) != PINNED_STATEWIDE:
        sys.exit(f"!! pin sums to {sum(rows.values()):,}, expected {PINNED_STATEWIDE:,} — "
                 "re-pinned without updating this script?")
    return rows


def load_ours() -> dict[str, int]:
    con = duckdb.connect(str(DB), read_only=True)
    try:
        raw = dict(con.execute(
            "SELECT UPPER(TRIM(county_name)), COUNT(*) FROM voters "
            "WHERE status_code = 'A' GROUP BY 1").fetchall())
    finally:
        con.close()
    return {LABEL_FIX.get(c, c): n for c, n in raw.items()}


def reconcile(pin: dict[str, int], ours: dict[str, int]) -> int:
    if set(pin) != set(ours):
        print(f"!! county name mismatch: {sorted(set(pin) ^ set(ours))}")
        return 1
    print("=" * 88)
    print("WA ROLL RECONCILIATION — April 1 2026 active roll vs certified Nov 4 2025 counts")
    print("=" * 88)
    print("\nNOTE: the Kittitas/Klickitat label correction is applied to the extract's labels")
    print("(KT/KS code inversion, known_issues.md / ledger C12). If those two counties fail")
    print("below, the mapping was probably fixed and the VRDB reloaded — update this script")
    print("and verify_who_decides_wa.py TOGETHER.\n")
    print(f"  {'county':<14}{'certified':>11}{'extract':>11}{'gap %':>9}")
    failures = 0
    worst = (0.0, "")
    for c in sorted(pin):
        gap = 100.0 * (ours[c] - pin[c]) / pin[c]
        flag = ""
        if abs(gap) > COUNTY_TOL_PCT:
            flag = "  << FAIL"
            failures += 1
        if abs(gap) > abs(worst[0]):
            worst = (gap, c)
        print(f"  {c:<14}{pin[c]:>11,}{ours[c]:>11,}{gap:>+8.2f}%{flag}")
    tot_pin, tot_ours = sum(pin.values()), sum(ours.values())
    tot_gap = 100.0 * (tot_ours - tot_pin) / tot_pin
    print(f"\n  {'STATEWIDE':<14}{tot_pin:>11,}{tot_ours:>11,}{tot_gap:>+8.3f}%")
    print(f"  worst county gap: {worst[0]:+.2f}% ({worst[1].title()})")
    if abs(tot_gap) > STATEWIDE_TOL_PCT:
        print(f"!! statewide gap {tot_gap:+.3f}% exceeds ±{STATEWIDE_TOL_PCT}%")
        failures += 1
    print("=" * 88)
    if failures:
        print(f"FAIL — {failures} bound(s) exceeded. Fix the load or re-pin; never widen.")
        return 1
    print("OK — every county within tolerance of the certified counts.")
    return 0


def selftest() -> int:
    """Prove the gate can fail: a swapped pair (the defect this script caught) must FAIL."""
    pin = load_pin()
    ours = load_ours()
    broken = dict(ours)
    broken["KITTITAS"], broken["KLICKITAT"] = broken["KLICKITAT"], broken["KITTITAS"]
    print(">> selftest: re-introducing the Kittitas/Klickitat swap — this run MUST fail\n")
    rc = reconcile(pin, broken)
    if rc == 0:
        print("!! selftest FAILED: the gate passed a swapped pair")
        return 1
    print("\n>> selftest OK: the swap is caught.")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        raise SystemExit(selftest())
    raise SystemExit(reconcile(load_pin(), load_ours()))
