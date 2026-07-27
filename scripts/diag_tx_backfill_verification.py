"""Item 2 of the review response: district-level verification table for the 54 Texas
House seats backfilled as uncontested.

The review's objection was fair. `diag_tx_safe_seat_backfill.py` adds 54 rows to reach
150 TX House seats, but the paper verified only a named subset "among others" — which
shows *some* of the 54 were uncontested, not all of them. This script emits a row per
backfilled district so the claim can be audited seat by seat, and is explicit about which
rows are independently confirmed and which rest on inference.

Two verification tiers, and the difference matters:

  PRESS-CONFIRMED — the district appears on the press-reported list of 2024 Texas House
  races with no major-party opponent. Independent of our data pipeline.

  INFERRED FROM ABSENCE — the district has no VTD return in the TLC canvass file. The
  TLC does not publish a precinct tally for an unopposed race, so absence is evidence of
  non-contestation, but it is OUR pipeline's evidence, not an outside source's. A
  district could in principle be absent for an unrelated reporting reason.

The holding party is IMPUTED from the district's 2024 presidential margin (r206), not
observed from a candidate record. Any comparison between these imputed party labels and
presidential vote is therefore circular and is flagged as such in the paper.

To fully close this item, a certified Texas candidate-filing list is needed — one row per
district with the certified candidates and their party. That source is not on disk.

Usage:  python scripts/diag_tx_backfill_verification.py
Writes: reports/tx_backfill_verification.csv
"""
from __future__ import annotations

import csv
import os
import sys

import pandas as pd

R206 = os.path.join("data", "raw", "tx", "plans", "planh2316_r206_election24g.xls")
OUT = os.path.join("reports", "tx_backfill_verification.csv")

# The 54 districts with no VTD return in the TLC 2024 canvass file, from
# diag_tx_safe_seat_backfill.py.
MISSING = [1, 3, 9, 11, 15, 21, 22, 24, 31, 33, 35, 36, 38, 40, 42, 49, 50, 51, 60, 72,
           75, 77, 78, 79, 81, 83, 85, 86, 88, 90, 91, 92, 95, 100, 102, 103, 104, 107,
           109, 110, 111, 120, 123, 125, 131, 133, 135, 139, 140, 141, 142, 143, 144, 145]

# Districts independently reported in press coverage as having no major-party opponent in
# 2024. Source citation still required before publication — see the paper's Appendix F.
PRESS_CONFIRMED_D = {35, 36, 38, 40, 42, 49, 51, 75, 78, 79, 90, 92, 95}
PRESS_CONFIRMED_R = {81}


def r206_presidential() -> dict[int, tuple[float, float]]:
    """district -> (Harris D votes, Trump R votes) from the r206 report."""
    # Column 1 is the district (NOT column 0); 3 is Harris-D votes, 11 is Trump-R.
    # Matches diag_tx_safe_seat_backfill.r206_presidential — keep the two in step.
    df = pd.read_excel(R206, sheet_name="Sheet2", header=None)
    out: dict[int, tuple[float, float]] = {}
    for _, row in df.iterrows():
        dist = str(row[1]).strip()
        if not dist.replace(".0", "").isdigit():
            continue
        try:
            dv, rv = float(row[3]), float(row[11])
        except (TypeError, ValueError):
            continue
        out[int(float(dist))] = (dv, rv)
    if not out:
        raise RuntimeError("r206 parse produced no districts — column layout changed?")
    return out


def main() -> int:
    if not os.path.exists(R206):
        print(f"ERROR: r206 report not found at {R206}")
        return 1
    pres = r206_presidential()

    rows = []
    for d in sorted(MISSING):
        dv, rv = pres.get(d, (0.0, 0.0))
        tot = dv + rv
        margin = (100.0 * (dv - rv) / tot) if tot else 0.0
        imputed = "D" if margin > 0 else "R"
        if d in PRESS_CONFIRMED_D:
            tier, conf = "press-confirmed", "D"
        elif d in PRESS_CONFIRMED_R:
            tier, conf = "press-confirmed", "R"
        else:
            tier, conf = "inferred from absence", ""
        rows.append({
            "district": d,
            "verification": tier,
            "press_reported_party": conf,
            "pres_2024_D": int(dv), "pres_2024_R": int(rv),
            "pres_margin_D_minus_R": round(margin, 1),
            "imputed_holding_party": imputed,
            "party_source": "IMPUTED from presidential lean (not observed)",
            "classification": "no major-party choice",
            "reason_absent": "no VTD return published; TLC omits uncontested races",
        })

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    npress = sum(1 for r in rows if r["verification"] == "press-confirmed")
    ninf = len(rows) - npress
    nd = sum(1 for r in rows if r["imputed_holding_party"] == "D")
    print("TEXAS BACKFILL — district-level verification")
    print("=" * 74)
    print(f"  backfilled districts: {len(rows)}")
    print(f"    press-confirmed unopposed : {npress}")
    print(f"    inferred from absence     : {ninf}   <-- NOT independently verified")
    print(f"  imputed holding party: {nd} D / {len(rows)-nd} R  (imputed, not observed)")

    mism = [r for r in rows if r["press_reported_party"]
            and r["press_reported_party"] != r["imputed_holding_party"]]
    print(f"\n  press-reported party vs presidential imputation: "
          f"{len(mism)} disagreement(s) among the {npress} confirmed")
    for r in mism:
        print(f"    HD{r['district']}: press says {r['press_reported_party']}, "
              f"imputation says {r['imputed_holding_party']} "
              f"(pres margin {r['pres_margin_D_minus_R']:+.1f})")
    if not mism:
        print("    -> where both are available they agree, which is a check on the "
              "imputation\n       but only across the confirmed subset.")

    close = [r for r in rows if abs(r["pres_margin_D_minus_R"]) < 10]
    print(f"\n  backfilled seats in presidentially COMPETITIVE districts (<10pt): {len(close)}")
    for r in close:
        print(f"    HD{r['district']:>4}  pres margin {r['pres_margin_D_minus_R']:+6.1f}  "
              f"{r['verification']}")
    print("    -> these are the rows where 'uncontested' is most surprising and the")
    print("       imputed party least secure; they deserve manual confirmation first.")

    print(f"\nwrote {OUT}")
    print("\nOUTSTANDING: a certified TX candidate-filing list is required to verify the")
    print(f"{ninf} inferred districts individually and to replace imputed party with observed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
