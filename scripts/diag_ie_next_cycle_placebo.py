"""Next-cycle placebo: does FUTURE independent expenditure "predict" a PAST residual?

The last of the three tests `does-money-move-votes.md` names as unrunnable on one
cycle. The other two are done: the contemporaneous regression (n=34, slope
+0.515, interval spanning zero) and the early-vs-late split, both in
`diag_ie_vs_margin.py` and `diag_ie_early_late.py`.

THE LOGIC. Money spent in 2024 cannot have changed a 2022 result. So regressing
the cycle-t residual on cycle-(t+1) independent expenditure must return zero if
the contemporaneous association is causal. If instead it returns something
similar to the contemporaneous estimate, then that estimate is picking up a
persistent property of the district or the candidate — a seat that is chronically
competitive attracts money every cycle AND has residuals that behave a certain
way — rather than an effect of the money. The placebo cannot prove causation; it
can only fail to rule out confounding, which is the direction that matters for a
paper arguing the naive correlation is uninterpretable.

The comparison is run on the SAME cells as the placebo, not against the headline
n=34 figure. A placebo compared to a contemporaneous estimate from a different
sample is comparing two things that differ in two ways.

THE REDISTRICTING TRAP, which governs the whole design. Washington redrew every
congressional district for 2022 (`StateConfig.district_boundary_year`). "cd08" in
2020 and "cd08" in 2022 are different territory with different voters, so pairing
them tests nothing about a district's persistent character — the district is not
the same district. Adjacent-cycle pairs are therefore classified:

    2018 -> 2020   both pre-redistricting   USABLE
    2020 -> 2022   CROSSES the boundary     reported separately, never pooled
    2022 -> 2024   both post-redistricting  USABLE

That leaves two usable pair-sets and a small n, which is stated rather than
worked around. Pooling all three would roughly double the sample and silently
mix a same-district comparison with a different-district one.

Reproducible, public-record inputs only. No PII, no voter file.

Usage:
    PYTHONPATH=src python scripts/diag_ie_next_cycle_placebo.py
"""
from __future__ import annotations

import argparse
import json
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

from diag_ie_vs_margin import (  # noqa: E402
    DB, assert_ie_classified, bootstrap_slope_ci, model_residual,
    net_ie_by_race, ols_slope,
)

# Below this the regression is not reported at all. Deliberately the same floor
# the contemporaneous script uses, so "the placebo was too small to run" and "the
# main test was too small to run" mean the same thing.
MIN_N = 10


def boundary_year() -> int:
    from config.state_config import get_state_config
    return get_state_config().district_boundary_year


def era(cycle: int, boundary: int) -> str:
    return "post" if cycle >= boundary else "pre"


def build_panel(conn):
    """(cycle, district) -> {net_pro_dem_m, residual_pp} for scorable cells."""
    panel = {}
    for r in net_ie_by_race(conn):
        did = r["district_id"]
        resid, _ = model_residual(conn, did, r["cycle"])
        if resid is None:
            continue
        panel[(r["cycle"], r["district_num"])] = {
            "district_id": did,
            "net_pro_dem_m": r["net_pro_dem_m"],
            "total_m": r["total_m"],
            "residual_pp": resid["residual_pp"],
        }
    return panel


def make_pairs(panel, boundary):
    """Adjacent-cycle pairs, tagged by whether they cross redistricting."""
    cycles = sorted({c for c, _ in panel})
    pairs = []
    for t, nxt in zip(cycles, cycles[1:]):
        crosses = era(t, boundary) != era(nxt, boundary)
        for (c, d), cell in panel.items():
            if c != t:
                continue
            future = panel.get((nxt, d))
            if future is None:
                continue
            pairs.append({
                "t": t, "t_next": nxt, "district_num": d,
                "district_id": cell["district_id"],
                "residual_t": cell["residual_pp"],
                "net_ie_t": cell["net_pro_dem_m"],
                "net_ie_next": future["net_pro_dem_m"],
                "crosses_redistricting": crosses,
            })
    return pairs


def leave_one_out(xs, ys, tags):
    """Largest single-observation influence on the slope.

    Mandatory at this n, not a nicety. Fourteen pairs, most of them at exactly
    zero on the regressor, means one race with real money is most of the
    leverage — and a slope that one deletion halves is a description of that
    race, not of a relationship. Returns (worst_tag, slope_without_it, full).
    """
    full, _, _ = ols_slope(xs, ys)
    worst_tag, worst_slope, worst_gap = None, full, 0.0
    for i in range(len(xs)):
        sx = xs[:i] + xs[i + 1:]
        sy = ys[:i] + ys[i + 1:]
        s, _, _ = ols_slope(sx, sy)
        if abs(s - full) > worst_gap:
            worst_tag, worst_slope, worst_gap = tags[i], s, abs(s - full)
    return worst_tag, worst_slope, full


def fit(label, xs, ys, tags=None, verbose=True):
    if len(xs) < MIN_N:
        if verbose:
            print(f"  {label:<34} n={len(xs):<3} WITHHELD (below {MIN_N})")
        return {"label": label, "n": len(xs), "status": "withheld"}
    slope, _, r = ols_slope(xs, ys)
    lo, hi = bootstrap_slope_ci(xs, ys)
    out = {"label": label, "n": len(xs), "status": "reported",
           "slope": slope, "r": r, "ci": [lo, hi], "crosses_zero": lo < 0 < hi}
    if verbose:
        print(f"  {label:<34} n={len(xs):<3} slope {slope:+7.3f}  r {r:+.3f}  "
              f"95% boot [{lo:+.3f}, {hi:+.3f}]"
              f"{'  crosses 0' if lo < 0 < hi else '  EXCLUDES 0'}")
    if tags:
        tag, without, _ = leave_one_out(xs, ys, tags)
        out["loo_worst"], out["loo_slope_without"] = tag, without
        if verbose:
            print(f"  {'':<34} drop {tag}: slope -> {without:+.3f}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    conn = duckdb.connect(DB, read_only=True)
    assert_ie_classified(conn)
    boundary = boundary_year()

    print("=" * 78)
    print("Next-cycle placebo — future IE against a past residual")
    print("=" * 78)
    print(f"Redistricting boundary year: {boundary} "
          f"(pairs spanning it are not the same district)")

    panel = build_panel(conn)
    pairs = make_pairs(panel, boundary)
    usable = [p for p in pairs if not p["crosses_redistricting"]]
    crossing = [p for p in pairs if p["crosses_redistricting"]]

    print(f"\nScorable cells: {len(panel)}   adjacent-cycle pairs: {len(pairs)}")
    for t, nxt in sorted({(p['t'], p['t_next']) for p in pairs}):
        n = sum(1 for p in pairs if p["t"] == t)
        tag = "CROSSES REDISTRICTING" if era(t, boundary) != era(nxt, boundary) \
            else f"both {era(t, boundary)}"
        print(f"  {t} -> {nxt}: {n:>2} pair(s)   [{tag}]")

    print(f"\n{'pair':>12} | {'net IE t':>9} | {'net IE t+1':>11} | {'resid t':>8} | era")
    print("-" * 66)
    for p in sorted(pairs, key=lambda q: (q["t"], q["district_num"])):
        tag = "CROSS" if p["crosses_redistricting"] else "same"
        print(f"{p['district_id']}/{str(p['t'])[2:]}->{str(p['t_next'])[2:]:>2} | "
              f"{p['net_ie_t']:+8.2f}M | {p['net_ie_next']:+10.2f}M | "
              f"{p['residual_t']:+8.2f} | {tag}")

    print("\n" + "=" * 78)
    print("SAME-ERA PAIRS ONLY (the test)")
    print("=" * 78)
    res = {}
    tags = [f"{p['district_id']}/{str(p['t'])[2:]}" for p in usable]
    res["placebo"] = fit("PLACEBO  resid_t ~ net IE t+1",
                         [p["net_ie_next"] for p in usable],
                         [p["residual_t"] for p in usable], tags)
    res["contemp"] = fit("compare  resid_t ~ net IE t",
                         [p["net_ie_t"] for p in usable],
                         [p["residual_t"] for p in usable], tags)
    xs_t = [p["net_ie_t"] for p in usable]
    xs_n = [p["net_ie_next"] for p in usable]
    if len(xs_t) >= 3:
        _, _, r_persist = ols_slope(xs_t, xs_n)
        res["ie_persistence_r"] = r_persist
        print(f"\n  corr(net IE t, net IE t+1) = {r_persist:+.3f}")
        # Persistence in the SPENDING is the obvious channel by which a placebo
        # could pick up a signal, so whether it is present changes how a
        # non-null placebo should be read. Stated conditionally rather than
        # asserted: an earlier version of this line called persistence "the
        # channel", which the measured +0.03 flatly contradicts.
        if abs(r_persist) >= 0.3:
            print("    A district's money persists across cycles, which is the "
                  "obvious channel\n    for a placebo to pick up signal through.")
        else:
            print("    A district's money does NOT persist across cycles, so the "
                  "obvious channel\n    for placebo signal is absent. Any non-null "
                  "placebo here has to run\n    through something else — most "
                  "likely the residual's own persistence, or\n    a single "
                  "high-leverage race.")

    if crossing:
        print("\n" + "=" * 78)
        print("BOUNDARY-CROSSING PAIRS — reported, never pooled with the above")
        print("=" * 78)
        print("  These compare a district label to itself across a redraw, so a "
              "nonzero\n  result here is not evidence about persistence — it is "
              "evidence about\n  whichever seats inherited the territory.")
        res["crossing_placebo"] = fit("CROSS    resid_t ~ net IE t+1",
                                      [p["net_ie_next"] for p in crossing],
                                      [p["residual_t"] for p in crossing])

    print("\n" + "=" * 78)
    print("READING IT")
    print("=" * 78)
    pl, ct = res["placebo"], res["contemp"]
    # Leverage is checked BEFORE the interval test, because it is the stronger
    # objection and it can be true while the interval test looks merely
    # uninformative. A slope that one deletion reverses is not a weak estimate
    # of a relationship; it is a description of one race.
    fragile = []
    for name, f in (("placebo", pl), ("contemporaneous", ct)):
        if f.get("status") != "reported" or "loo_slope_without" not in f:
            continue
        s, w = f["slope"], f["loo_slope_without"]
        if s * w < 0 or (abs(s) > 1e-9 and abs(w - s) / abs(s) > 0.5):
            fragile.append((name, f["loo_worst"], s, w))
    if fragile:
        print("  SINGLE-OBSERVATION FRAGILITY — this dominates everything below:")
        for name, tag, s, w in fragile:
            flip = "SIGN FLIPS" if s * w < 0 else "changes by >50%"
            print(f"    {name}: dropping {tag} moves the slope "
                  f"{s:+.3f} -> {w:+.3f} ({flip})")
        print("    At this n the estimates describe individual races, not a")
        print("    relationship, and no amount of interval arithmetic repairs that.")
        print()

    if pl["status"] != "reported" or ct["status"] != "reported":
        print("  Withheld. Two same-era adjacent-cycle pair-sets over ten districts")
        print("  is not enough cells to run a placebo, which is itself the answer:")
        print("  the design needs more cycles, not more spending.")
    else:
        print(f"  placebo slope {pl['slope']:+.3f}  vs  contemporaneous "
              f"{ct['slope']:+.3f} on the same cells.")
        if pl["crosses_zero"] and ct["crosses_zero"]:
            print("  BOTH intervals cross zero, so neither is distinguishable from")
            print("  no-effect and the placebo cannot discriminate. This is the")
            print("  underpowered outcome, not a clean bill of health.")
        elif pl["crosses_zero"] and not ct["crosses_zero"]:
            print("  The placebo is null while the contemporaneous estimate is not —")
            print("  the pattern a real effect would produce. Still not causal:")
            print("  it rules out one confounder, not targeting on expected closeness.")
        else:
            print("  The PLACEBO IS NON-NULL. Future money 'predicts' a past residual,")
            print("  so the contemporaneous estimate is picking up something persistent")
            print("  about these districts rather than an effect of the spending.")

    conn.close()
    out = args.json or os.path.join(tempfile.gettempdir(), "ie_next_cycle_placebo.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"pairs": pairs, "result": res, "boundary_year": boundary},
                  f, indent=2, default=str)
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
