#!/usr/bin/env python3
"""Do campaign-spend ALLOCATION shares explain the persistent candidate residual?

Open thread #2 probe (a NEW data modality). The over/underperformance arc
concluded the residual is a persistent candidate trait (cross-cycle r~0.675) that
messaging, demographics, gender, finance *aggregates*, and the opponent don't
reproducibly explain. This tests a genuinely new signal: HOW a campaign allocated
its itemized spend — field/ground vs paid-media vs professional/staff — from the
PDC C4 Schedule-A expenditures (table `candidate_expenditures`, loaded via
`main.py load-pdc-expenditures`).

We use SHARES of operational spend, not raw dollars: raw $ is just fundraising
(already tested, the strongest-but-non-reproducible finance signal). The
hypothesis is ALLOCATION — e.g. a candidate who puts an unusually high share into
field/ground out-performs their fundamentals (ground game beyond what money alone
predicts). `log_operational_total` is included as a scale control.

PDC = STATE filers only, so this covers the **LD** cells (the 10 CDs would need
FEC operating-expenditures; deferred). Coverage caveat: ~62% of candidate
expenditure DOLLARS carry a purpose `code`; shares are computed over the
clearly-categorized, non-transfer spend and per-candidate coded coverage is
reported. Mini-reporting (smallest) campaigns are excluded by PDC.

DECISION BAR (same as Track 4, diag_candidate_quality_index): in-sample
correlation is necessary but NOT sufficient. The honest test is whether adding
spend-shares to the candidate-quality index improves its CROSS-CYCLE HOLDOUT R^2
(fit 2022 -> predict 2024) above the ~0.00 Track-4 baseline, with a face-valid,
signed, PERSISTENT share. Read-only. Run alone (DB-lock trap).

    python scripts/diag_expenditures_vs_residual.py [--csv reports/expenditures_vs_residual.csv]
"""

from __future__ import annotations

import argparse
import logging
import math
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "scripts"))

import numpy as np  # noqa: E402

from wa_analyzer.db import get_connection  # noqa: E402
from wa_analyzer.analysis.national_model import _name_tokens  # noqa: E402
# Importing dop sets _nm._PERSONAL_VOTE_ENABLED=False (keeps the residual stable +
# non-circular). It also gives us the current-model cell frame + residual fit.
import diag_overperformance_patterns as dop  # noqa: E402
import diag_candidate_quality_index as cqi  # noqa: E402

# --- PDC C4 Schedule-A purpose code -> spend category (all 41 live codes) ---
# Shares are computed over FIELD+MEDIA+PROFESSIONAL+OVERHEAD ("operational"
# spend). EXCLUDE = transfers / in-kind / refunds / uncategorizable ("Other",
# blank) — not a persuasion-allocation decision.
_CODE_CATEGORY = {
    # MEDIA (paid communication)
    "Broadcast/cable TV advertising": "media",
    "Digital advertising": "media",
    "Other advertising": "media",
    "Newspaper/periodical advertising": "media",
    "Radio advertising": "media",
    "Billboard advertising": "media",
    "Robocalls": "media",
    # FIELD (voter-contact infrastructure / ground game)
    "Printing literature, fliers, postcards, etc.": "field",
    "Postage costs, mail permits, purchase of stamps": "field",
    "Printing campaign signs": "field",
    "Campaign merchandise/paraphernalia": "field",
    "Design/graphic art, etc.": "field",
    "Voter signature/petition gathering costs": "field",
    # PROFESSIONAL (paid capacity)
    "Management and consulting services": "professional",
    "Wages, salaries, benefits, payroll taxes": "professional",
    "Accounting, legal, regulatory compliance, etc.": "professional",
    "Surveys, polling, research costs": "professional",
    # OVERHEAD (non-persuasive operating cost)
    "Utilities, phone, and other overhead costs": "overhead",
    "Bank and payment processing charges": "overhead",
    "Travel, accommodations, meals": "overhead",
    "Fundraising events and related costs": "overhead",
    "Office supplies, furniture, staff food & beverages, etc.": "overhead",
    "Computers, printers, software, phones, etc.": "overhead",
    "Filing fees": "overhead",
    "Rent, lease, mortgage, PO box rental": "overhead",
    "Mileage reimbursement": "overhead",
    "Internet, phone & text charges": "overhead",
}
_EXCLUDE = {
    "Inkind contribution", "Monetary contributions to PAC or candidate",
    "Independent Expenditure", "Contribution Refunds", "Loan payments", "Charity",
    "Transfer to surplus funds account", "Disposal of surplus funds to charity",
    "Transfer to new campaign", "Transfer to political party or legislative caucus committee",
    "Payment for candidate's lost earnings", "Interest", "Transfer to state general fund",
    "Other", "nan", "None", "",
}
_OPERATIONAL = ("field", "media", "professional", "overhead")


def build_expenditure_shares(conn):
    """(election_year,)+_name_tokens(filer_name) -> {field_share, media_share,
    professional_share, log_operational_total, coded_total, coded_n}."""
    rows = conn.execute("""
        SELECT election_year, filer_name, code, SUM(amount) AS amt, COUNT(*) AS n
        FROM candidate_expenditures
        WHERE election_year IS NOT NULL AND filer_name IS NOT NULL
        GROUP BY election_year, filer_name, code
    """).fetchall()

    agg: dict[tuple, dict] = {}
    unmapped: dict[str, float] = {}
    for year, filer, code, amt, n in rows:
        amt = float(amt or 0.0)
        code = (code or "").strip()
        if code in _EXCLUDE:
            continue
        cat = _CODE_CATEGORY.get(code)
        if cat is None:
            unmapped[code] = unmapped.get(code, 0.0) + amt
            continue
        key = (int(year),) + _name_tokens(filer)
        d = agg.setdefault(key, {c: 0.0 for c in _OPERATIONAL} | {"n": 0})
        d[cat] += amt
        d["n"] += int(n)

    out = {}
    for key, d in agg.items():
        total = sum(d[c] for c in _OPERATIONAL)
        if total <= 0:
            continue
        out[key] = {
            "field_share": d["field"] / total,
            "media_share": d["media"] / total,
            "professional_share": d["professional"] / total,
            "log_operational_total": math.log10(total) if total > 0 else 0.0,
            "coded_total": total,
            "coded_n": d["n"],
        }
    return out, unmapped


def attach_to_cells(cells, shares):
    """Attach the D candidate's spend shares to each cell; return covered LD cells."""
    covered = []
    for c in cells:
        s = shares.get((c["year"],) + _name_tokens(c["dem"])) if c["dem"] else None
        if s is None:
            continue
        c.update(s)
        covered.append(c)
    return covered


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", default=None)
    args = ap.parse_args()

    logging.getLogger("wa_analyzer").setLevel(logging.ERROR)
    conn = get_connection()
    try:
        # Fresh current-model residual frame (dop disabled personal-vote on import).
        dop.compute_presidential_performance_statewide(conn)
        for did in dop.DEFAULT_DISTRICTS:
            try:
                dop.compute_district_historical_from_results(
                    conn, profile=dop.get_profile(did))
            except Exception:
                continue
        frame = [r for r in dop.build_frame(conn) if r["baseline_ok"]]
        dop.fit_unexplained_residuals(frame)
        # Normalize to the cell shape the cqi/drh helpers expect.
        cells = [{
            "key": (r["district"], r["year"]), "district": r["district"],
            "year": r["year"], "dem": r["dem_candidate"], "rep": r["rep_candidate"],
            "residual": r["unexplained_residual"], "overperf": r["overperformance"],
            "incumbency": r["incumbency"],
        } for r in frame]

        shares, unmapped = build_expenditure_shares(conn)
        ld_cells = [c for c in cells if c["district"].startswith("ld")]
        covered = attach_to_cells(ld_cells, shares)

        print("=" * 96)
        print("CAMPAIGN-SPEND ALLOCATION vs the persistent residual (PDC, LD cells)")
        print("=" * 96)
        if unmapped:
            print(f"\n[warn] {len(unmapped)} unmapped non-excluded codes "
                  f"(${sum(unmapped.values()):,.0f}): {list(unmapped)[:5]}")
        n_ld = len(ld_cells)
        print(f"\nCoverage: {len(covered)}/{n_ld} LD baseline-ok cells matched to "
              f"itemized PDC spend ({len(shares)} candidate-cycles have shares).")
        if covered:
            cov = [c["coded_total"] for c in covered]
            print(f"  median coded operational spend/candidate: ${np.median(cov):,.0f}  "
                  f"(min ${min(cov):,.0f}, max ${max(cov):,.0f})")

        if len(covered) < 5:
            print("\nToo few covered cells for correlation. Stopping.")
            return

        resid = [c["residual"] for c in covered]
        print("\n--- Pearson r of each spend feature vs unexplained_residual ---")
        for feat in ("field_share", "media_share", "professional_share",
                     "log_operational_total"):
            xs = [c[feat] for c in covered]
            r, n = dop.pearson(xs, resid), len(covered)
            print(f"  {feat:24s}: r = {r:+.3f}  (n={n})" if r is not None
                  else f"  {feat:24s}: n/a")
        # also vs raw overperformance (less filtered target)
        op = [c["overperf"] for c in covered]
        rf = dop.pearson([c["field_share"] for c in covered], op)
        print(f"  {'field_share vs RAW overperf':24s}: r = "
              + (f"{rf:+.3f}" if rf is not None else "n/a"))

        # --- Persistence of the allocation style itself (is it a stable trait?) ---
        print("\n--- Is allocation a persistent candidate trait? (2022 vs 2024) ---")
        for feat in ("field_share", "media_share", "professional_share"):
            by = {}
            for c in covered:
                by.setdefault(_name_tokens(c["dem"]), {})[c["year"]] = c[feat]
            pairs = [(v[2022], v[2024]) for v in by.values() if 2022 in v and 2024 in v]
            if len(pairs) >= 3:
                r = dop.pearson([p[0] for p in pairs], [p[1] for p in pairs])
                print(f"  {feat:20s}: r = {r:+.3f} (n={len(pairs)} repeat candidates)")
            else:
                print(f"  {feat:20s}: n/a (<3 repeat candidates)")

        # --- THE DECISIVE TEST: does spend-share improve the Track-4 holdout? ---
        # Reuse cqi's components + OLS holdout machinery; inject spend shares as
        # extra components, compare CORE vs CORE+spend on the cross-cycle holdout.
        print("\n" + "=" * 96)
        print("DECISIVE TEST — cross-cycle holdout R^2 (fit 2022 -> predict 2024)")
        print("  Bar: beat the Track-4 candidate-quality-index holdout (~0.00).")
        print("=" * 96)
        comps = cqi.build_components(conn, cells)        # base quality components
        for c in covered:                                # add spend shares as components
            comps[c["key"]].update({
                "field_share": c["field_share"],
                "media_share": c["media_share"],
                "professional_share": c["professional_share"],
            })
        resid_by_key = {c["key"]: c["residual"] for c in cells}
        keys_2022 = [c["key"] for c in cells if c["year"] == 2022]
        keys_2024 = [c["key"] for c in cells if c["year"] == 2024]
        all_keys = [c["key"] for c in cells]

        def holdout(names, label):
            ho_pred, nfit = cqi.ols_fit_predict(keys_2022, all_keys, comps, names, resid_by_key)
            ho = [k for k in keys_2024 if k in ho_pred]
            ins, _ = cqi.ols_fit_predict(all_keys, all_keys, comps, names, resid_by_key)
            ik = [k for k in all_keys if k in ins]
            ri = dop.pearson([ins[k] for k in ik], [resid_by_key[k] for k in ik]) if len(ik) >= 5 else None
            if len(ho) >= 5:
                r = dop.pearson([ho_pred[k] for k in ho], [resid_by_key[k] for k in ho])
                print(f"  {label:34s}: holdout R^2={ (r*r if r is not None else float('nan')):.3f} "
                      f"(r={r:+.3f}, n={len(ho)}) | in-sample R^2="
                      f"{ (ri*ri if ri is not None else float('nan')):.3f}")
            else:
                print(f"  {label:34s}: holdout n<5 (covered cells too sparse)")

        holdout(cqi._CORE, "CORE quality (Track-4 baseline)")
        holdout(cqi._CORE + ["field_share"], "CORE + field_share")
        holdout(cqi._CORE + ["field_share", "media_share", "professional_share"],
                "CORE + all spend shares")
        holdout(["field_share", "media_share", "professional_share"],
                "spend shares ALONE")

        # --- Leaderboard for eyeballing ---
        covered.sort(key=lambda c: c["residual"], reverse=True)
        print("\n--- LD cells by residual (top/bottom 12): field/media/prof shares ---")
        print(f"  {'resid':>6s} {'over':>6s}  cell                         "
              f"{'field':>6s}{'media':>6s}{'prof':>6s}  coded$")
        for c in covered[:12] + covered[-12:]:
            print(f"  {c['residual']:+6.1f} {c['overperf']:+6.1f}  {c['district']:4s} {c['year']} "
                  f"{c['dem'][:18]:18s} {c['field_share']:6.2f}{c['media_share']:6.2f}"
                  f"{c['professional_share']:6.2f}  ${c['coded_total']:>10,.0f}")

        if args.csv:
            import csv as _csv
            cols = ["district", "year", "dem", "incumbency", "residual", "overperf",
                    "field_share", "media_share", "professional_share",
                    "log_operational_total", "coded_total", "coded_n"]
            with open(args.csv, "w", newline="", encoding="utf-8") as f:
                w = _csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
                w.writeheader()
                w.writerows(covered)
            print(f"\n[wrote {len(covered)} covered LD cells to {args.csv}]")

        print("\nNOTE: the holdout R^2 vs the Track-4 ~0.00 baseline + share persistence "
              "are the honest headlines. ~62% of $ is coded; mini-reporting excluded; "
              "allocation is partly endogenous to candidate strength.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
