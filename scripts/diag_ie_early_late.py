"""Early-versus-late independent expenditure against the fundamentals-net residual.

The second of the two tests `does-money-move-votes.md` names as runnable once the
FEC Schedule-E panel spans more than one cycle (the other is the next-cycle
placebo). The question: does independent expenditure spent in the closing weeks
associate with the outcome differently from money spent months out?

WHY THE SPLIT IS INTERESTING. Under a persuasion story, late money should carry
more weight — advertising decay is fast, and the marginal voter decides late.
Under a *signalling* story, the timing carries no information about effect and
the split is noise. Under the endogeneity story this paper argues for, late money
should look WORSE than early money, because late money is disproportionately
triage: committees move resources into races that have visibly deteriorated, so
the lateness of a dollar partly encodes bad news about the candidate receiving it.
The three predictions are distinguishable in principle. Whether they are
distinguishable in THIS sample is the thing the script has to answer honestly.

TWO DESIGN DECISIONS, both stated rather than buried.

  1. Expenditures dated AFTER election day are dropped. Money spent after the
     votes are cast cannot have moved them, and the FEC record carries such rows
     in every cycle (30 rows, ~$152K across 2018-2024, including one dated ten
     months post-election). Left in, they would land in the "late" bucket and
     make it partly a measure of post-hoc reporting.
  2. The cutoff is a free parameter, so the headline is reported at 30 days and
     the whole result is re-reported at 14 and 60. A split that only exists at
     one cutoff is a specification search, not a finding.

The dependent variable is the fundamentals-net residual, exactly as in
`diag_ie_vs_margin.py`, whose helpers this script imports rather than
reimplements — a second copy of the residual definition is how two numbers that
should be identical drift apart.

Reproducible, public-record inputs only (FEC Schedule E + FEC candidate party).
No PII, no voter file.

Usage:
    PYTHONPATH=src python scripts/diag_ie_early_late.py
    PYTHONPATH=src python scripts/diag_ie_early_late.py --cutoff-days 45
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import tempfile

import duckdb

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, os.path.dirname(__file__))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

from config.districts import get_profile  # noqa: E402
from diag_ie_vs_margin import (  # noqa: E402
    DB, assert_ie_classified, bootstrap_slope_ci, model_residual, ols_slope,
)

# Below this many races carrying money in BOTH windows, the two coefficients are
# not separately identified and only the descriptive table is printed. Matches
# the sibling script's MIN_N_FOR_SLOPE in spirit: the threshold is declared up
# front so a thin result cannot be talked up after the fact.
MIN_N_BOTH_WINDOWS = 10

# A race counts as having money in a window only above this. Written as a dollar
# floor rather than "> 0" after the first run reported 26 of 34 races carrying
# money in both windows — true, but only because a $10 sticker-price expenditure
# satisfies "> 0". On a $10 window the joint fit learns nothing about that race's
# timing, so counting it inflates the apparent identification of the split. At
# $10K the count is what it should have said.
MATERIAL_WINDOW_USD = 10_000 / 1e6  # in $M, matching the stored units

DEFAULT_CUTOFF_DAYS = 30
SENSITIVITY_CUTOFFS = (14, 30, 60)


def general_election_days() -> dict[int, str]:
    """Cycle year -> general election date, from the shared calendar.

    Read rather than hardcoded: the cutoff arithmetic is relative to election
    day, so a wrong date silently shifts every race's split by that many days.
    """
    from config.election_calendar import ELECTIONS
    return {e.year: e.date_slug
            for e in ELECTIONS if e.election_type == "general"}


def net_ie_by_window(conn, cutoff_days: int) -> dict[tuple[int, int], dict]:
    """Net pro-Dem IE per (cycle, district), split early vs late.

    Returns {(cycle, district_num): {"early": $, "late": $, "early_tot": $, ...}}.
    Sign convention matches diag_ie_vs_margin: pro-Dem = support-D + oppose-R.
    """
    eday = general_election_days()
    if not eday:
        raise SystemExit("no general elections in the calendar")
    values = ", ".join(
        f"({y}, DATE '{s[:4]}-{s[4:6]}-{s[6:]}')" for y, s in sorted(eday.items()))

    q = f"""
    WITH e(cycle, eday) AS (VALUES {values}),
    ie AS (
        SELECT DISTINCT v.ie_id, v.election_cycle, v.district, v.candidate_name,
               v.support_oppose, v.expenditure_amount, v.expenditure_date, e.eday
        FROM v_independent_expenditures v
        JOIN e ON e.cycle = v.election_cycle
        WHERE v.source = 'FEC' AND v.office = 'H' AND v.state = 'WA'
          AND v.support_oppose IN ('S', 'O')
          AND v.expenditure_date IS NOT NULL
          -- Money spent after the votes are cast cannot have moved them.
          AND v.expenditure_date <= e.eday
    ),
    party AS (
        SELECT DISTINCT election_cycle, UPPER(candidate_name) AS cn, party
        FROM candidate_finance
        WHERE state = 'WA' AND office = 'H'
          AND party IN ('Democratic', 'Republican')
    ),
    signed AS (
        SELECT ie.election_cycle, ie.district,
               (ie.eday - ie.expenditure_date) <= {cutoff_days} AS is_late,
               CASE WHEN (p.party = 'Democratic' AND ie.support_oppose = 'S')
                      OR (p.party = 'Republican' AND ie.support_oppose = 'O')
                    THEN ie.expenditure_amount
                    WHEN (p.party = 'Republican' AND ie.support_oppose = 'S')
                      OR (p.party = 'Democratic' AND ie.support_oppose = 'O')
                    THEN -ie.expenditure_amount
                    ELSE 0 END AS net_amt,
               ie.expenditure_amount AS gross_amt
        FROM ie
        LEFT JOIN party p
          ON ie.election_cycle = p.election_cycle
         AND UPPER(ie.candidate_name) = p.cn
    )
    SELECT election_cycle, district,
           SUM(net_amt)   FILTER (WHERE NOT is_late) AS net_early,
           SUM(net_amt)   FILTER (WHERE is_late)     AS net_late,
           SUM(gross_amt) FILTER (WHERE NOT is_late) AS tot_early,
           SUM(gross_amt) FILTER (WHERE is_late)     AS tot_late
    FROM signed
    GROUP BY 1, 2
    """
    out: dict[tuple[int, int], dict] = {}
    for cyc, dist, ne, nl, te, tl in conn.execute(q).fetchall():
        if not str(dist).isdigit():
            continue
        out[(int(cyc), int(dist))] = {
            "net_early_m": float(ne or 0) / 1e6,
            "net_late_m": float(nl or 0) / 1e6,
            "tot_early_m": float(te or 0) / 1e6,
            "tot_late_m": float(tl or 0) / 1e6,
        }
    return out


def ols2(x1, x2, ys):
    """Two-predictor OLS by closed form. Returns (b1, b2, intercept, r2) or None.

    None when the normal equations are singular — which here means early and
    late spending are collinear, i.e. the split carries no independent
    information. That is a result, not an error, and the caller reports it.
    """
    n = len(ys)
    m1, m2, my = sum(x1) / n, sum(x2) / n, sum(ys) / n
    s11 = sum((a - m1) ** 2 for a in x1)
    s22 = sum((b - m2) ** 2 for b in x2)
    s12 = sum((a - m1) * (b - m2) for a, b in zip(x1, x2))
    s1y = sum((a - m1) * (y - my) for a, y in zip(x1, ys))
    s2y = sum((b - m2) * (y - my) for b, y in zip(x2, ys))
    det = s11 * s22 - s12 * s12
    if abs(det) < 1e-12:
        return None
    b1 = (s22 * s1y - s12 * s2y) / det
    b2 = (s11 * s2y - s12 * s1y) / det
    b0 = my - b1 * m1 - b2 * m2
    syy = sum((y - my) ** 2 for y in ys)
    if syy == 0:
        return b1, b2, b0, 0.0
    ss_res = sum((y - (b0 + b1 * a + b2 * b)) ** 2 for a, b, y in zip(x1, x2, ys))
    return b1, b2, b0, 1.0 - ss_res / syy


def bootstrap_ols2_ci(x1, x2, ys, iters=5000, seed=12345):
    """Percentile bootstrap CIs for both coefficients. Deterministic.

    Resamples that produce a singular system are skipped rather than counted as
    zero — a dropped resample narrows the interval honestly, whereas a zero
    invents a coefficient the data did not support.
    """
    import random
    rng = random.Random(seed)
    n = len(ys)
    idx = list(range(n))
    b1s, b2s, singular = [], [], 0
    for _ in range(iters):
        s = [rng.choice(idx) for _ in range(n)]
        got = ols2([x1[i] for i in s], [x2[i] for i in s], [ys[i] for i in s])
        if got is None:
            singular += 1
            continue
        b1s.append(got[0])
        b2s.append(got[1])
    if len(b1s) < iters * 0.5:
        return None, None, singular
    b1s.sort()
    b2s.sort()
    k = len(b1s)
    return ((b1s[int(0.025 * k)], b1s[int(0.975 * k)]),
            (b2s[int(0.025 * k)], b2s[int(0.975 * k)]), singular)


def build_rows(conn, cutoff_days: int):
    """Scorable races with their early/late split and residual."""
    windows = net_ie_by_window(conn, cutoff_days)
    rows = []
    for (cyc, dist), w in sorted(windows.items()):
        did = f"cd{dist:02d}"
        resid, _ = model_residual(conn, did, cyc)
        if resid is None:
            continue
        rows.append({"cycle": cyc, "district_num": dist, "district_id": did,
                     **w, **resid})
    return rows


def report(rows, cutoff_days, verbose=True):
    """Run the split at one cutoff. Returns a result dict."""
    ys = [r["residual_pp"] for r in rows]
    xe = [r["net_early_m"] for r in rows]
    xl = [r["net_late_m"] for r in rows]
    n_both = sum(1 for r in rows
                 if r["tot_early_m"] >= MATERIAL_WINDOW_USD
                 and r["tot_late_m"] >= MATERIAL_WINDOW_USD)
    n_any = sum(1 for r in rows
                if r["tot_early_m"] + r["tot_late_m"] >= MATERIAL_WINDOW_USD)
    n_nonzero_both = sum(1 for r in rows
                         if r["tot_early_m"] > 1e-9 and r["tot_late_m"] > 1e-9)

    res = {"cutoff_days": cutoff_days, "n": len(rows), "n_both_windows": n_both,
           "n_any_material": n_any, "n_both_nonzero": n_nonzero_both}

    # Collinearity between the two regressors decides whether a joint fit means
    # anything. Reported before the coefficients, because it governs how to read
    # them rather than being a footnote to them.
    _, _, r_el = ols_slope(xe, xl)
    res["corr_early_late"] = r_el

    s_e, _, r_e = ols_slope(xe, ys)
    s_l, _, r_l = ols_slope(xl, ys)
    res["sep_early_slope"], res["sep_early_r"] = s_e, r_e
    res["sep_late_slope"], res["sep_late_r"] = s_l, r_l
    res["sep_early_ci"] = bootstrap_slope_ci(xe, ys)
    res["sep_late_ci"] = bootstrap_slope_ci(xl, ys)

    if verbose:
        print(f"\n{'=' * 78}")
        print(f"CUTOFF: last {cutoff_days} days before election day = 'late'")
        print("=" * 78)
        print(f"  scorable races                     : {len(rows)}")
        print(f"  ... with any material IE at all     : {n_any}"
              f"   (>= ${MATERIAL_WINDOW_USD * 1e6:,.0f} total)")
        print(f"  ... with material IE in BOTH windows: {n_both}"
              f"   (threshold for a joint fit: {MIN_N_BOTH_WINDOWS})")
        print(f"      [any nonzero cent in both: {n_nonzero_both} — not the same "
              f"thing, and not what identifies the split]")
        print(f"  corr(net early, net late)          : {r_el:+.3f}")
        print()
        print("  SEPARATE simple regressions (residual_pp ~ one window):")
        print(f"    early  slope {s_e:+7.3f} pp per $1M   r {r_e:+.3f}   "
              f"95% boot [{res['sep_early_ci'][0]:+.3f}, {res['sep_early_ci'][1]:+.3f}]")
        print(f"    late   slope {s_l:+7.3f} pp per $1M   r {r_l:+.3f}   "
              f"95% boot [{res['sep_late_ci'][0]:+.3f}, {res['sep_late_ci'][1]:+.3f}]")

    if n_both < MIN_N_BOTH_WINDOWS:
        res["joint"] = "withheld"
        if verbose:
            print(f"\n  JOINT FIT WITHHELD — only {n_both} race(s) carry money in both")
            print("  windows, so the two coefficients are not separately identified.")
        return res

    got = ols2(xe, xl, ys)
    if got is None:
        res["joint"] = "singular"
        if verbose:
            print("\n  JOINT FIT SINGULAR — early and late spending are collinear here,")
            print("  so the split carries no information the pooled total does not.")
        return res

    b1, b2, b0, r2 = got
    ci1, ci2, singular = bootstrap_ols2_ci(xe, xl, ys)
    res.update({"joint": "reported", "joint_early": b1, "joint_late": b2,
                "joint_intercept": b0, "joint_r2": r2,
                "joint_early_ci": ci1, "joint_late_ci": ci2,
                "boot_singular": singular})
    # Robustness: the same fit on races that actually received money. Roughly
    # half the panel sits at exactly (0, 0) on both regressors — real
    # observations of zero treatment, so they belong in the headline fit, but
    # they carry no information about TIMING and they anchor the intercept. If
    # the coefficients move a lot when they are dropped, the split is being
    # driven by the contrast between spending and not spending rather than by
    # when the spending happened, which is a different question.
    money = [r for r in rows
             if r["tot_early_m"] + r["tot_late_m"] >= MATERIAL_WINDOW_USD]
    sub = ols2([r["net_early_m"] for r in money],
               [r["net_late_m"] for r in money],
               [r["residual_pp"] for r in money]) if len(money) >= 4 else None
    if sub:
        res["money_only_n"] = len(money)
        res["money_only_early"], res["money_only_late"] = sub[0], sub[1]
        res["money_only_r2"] = sub[3]

    if verbose:
        print("\n  JOINT regression (residual_pp ~ net early + net late):")
        c1 = f"[{ci1[0]:+.3f}, {ci1[1]:+.3f}]" if ci1 else "(bootstrap degenerate)"
        c2 = f"[{ci2[0]:+.3f}, {ci2[1]:+.3f}]" if ci2 else "(bootstrap degenerate)"
        print(f"    early  {b1:+7.3f} pp per $1M   95% boot {c1}")
        print(f"    late   {b2:+7.3f} pp per $1M   95% boot {c2}")
        print(f"    R2 {r2:.3f}")
        if ci1 and ci2:
            crosses = (ci1[0] < 0 < ci1[1], ci2[0] < 0 < ci2[1])
            print(f"    early CI crosses zero: {crosses[0]};  "
                  f"late CI crosses zero: {crosses[1]}")
        if sub:
            print(f"\n  ROBUSTNESS — dropping the {len(rows) - len(money)} races with no "
                  f"material IE (n={len(money)}):")
            print(f"    early  {sub[0]:+7.3f}   late {sub[1]:+7.3f}   R2 {sub[3]:.3f}")
    return res


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cutoff-days", type=int, default=DEFAULT_CUTOFF_DAYS)
    ap.add_argument("--json", default=None, help="write the full result here")
    args = ap.parse_args()

    conn = duckdb.connect(DB, read_only=True)
    assert_ie_classified(conn)

    print("=" * 78)
    print("Early-vs-late IE split against the fundamentals-net residual")
    print("=" * 78)

    rows = build_rows(conn, args.cutoff_days)
    cycles = sorted({r["cycle"] for r in rows})
    print(f"Cycles: {', '.join(map(str, cycles)) or '(none)'}")
    print(f"Scorable races: {len(rows)}")

    print(f"\n{'race':>10} | {'net early':>10} | {'net late':>10} | "
          f"{'tot early':>10} | {'tot late':>10} | {'resid':>7}")
    print("-" * 78)
    for r in rows:
        print(f"{r['district_id']}/{str(r['cycle'])[2:]:>2} | "
              f"{r['net_early_m']:+9.2f}M | {r['net_late_m']:+9.2f}M | "
              f"{r['tot_early_m']:9.2f}M | {r['tot_late_m']:9.2f}M | "
              f"{r['residual_pp']:+7.2f}")

    headline = report(rows, args.cutoff_days)

    print(f"\n{'=' * 78}")
    print("SENSITIVITY — the cutoff is a free parameter, so it is swept")
    print("=" * 78)
    sweep = []
    for c in SENSITIVITY_CUTOFFS:
        r = report(build_rows(conn, c), c, verbose=False) if c != args.cutoff_days \
            else headline
        sweep.append(r)
        j = (f"joint early {r['joint_early']:+.3f} / late {r['joint_late']:+.3f}"
             if r.get("joint") == "reported" else f"joint {r.get('joint')}")
        print(f"  {c:>3}d: n_both {r['n_both_windows']:>2}  "
              f"corr(e,l) {r['corr_early_late']:+.3f}  "
              f"sep early {r['sep_early_slope']:+.3f} / late "
              f"{r['sep_late_slope']:+.3f}  |  {j}")

    conn.close()

    out = args.json or os.path.join(tempfile.gettempdir(), "ie_early_late.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"rows": rows, "headline": headline, "sweep": sweep}, f,
                  indent=2, default=str)
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
