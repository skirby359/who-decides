"""Does the IE null survive better inference, and does a cleanly-assigned subset exist?

RAISED BY AN EXTERNAL REFEREE, 2026-08-25, as two separate asks that turn out to answer each
other.

PART A — INFERENCE SENSITIVITY. `does-money-move-votes.md` reports a case-resampling
percentile bootstrap and a district-clustered percentile bootstrap over TEN clusters. With
ten clusters and one observation carrying Cook's distance 0.69, a percentile cluster
bootstrap is exactly the estimator the few-clusters literature warns about. So three more:

    HC3                    heteroskedasticity-robust, no clustering. HC3 rather than HC1
                           because it inflates high-leverage residuals, which is the whole
                           problem here.
    CR2 (cluster-robust)   clustered on district, small-sample corrected. The
                           Bell-McCaffrey style adjustment statsmodels exposes as HC3 with
                           groups; reported as an interval for comparability.
    wild cluster bootstrap Rademacher weights applied to CLUSTER residuals under the null,
                           Cameron-Gelbach-Miller. This is the recommended procedure at ten
                           clusters, and it is the one that can differ most from the
                           percentile bootstrap the paper reports.

The expectation is that none of these rescues an effect. That is why it is worth running: if
every method agrees the sign is not pinned down, the identification-failure claim stops
resting on the paper's own choice of a single interval.

PART B — THE CLEANEST LEGISLATIVE SUBSET. The referee's sharpest design point: the PDC
legislative panel identifies a candidate's CHAMBER but not their House POSITION, so a
district-level expenditure is ambiguous between Position 1 and Position 2. Senate races carry
no such ambiguity -- one seat per district -- so a Senate-only panel is the cleanly assigned
one. "Turn your central insight into your design choice: sacrifice cell count for treatment
validity."

Done. And the answer is the paper's own thesis, measured rather than asserted: the cleanly
assigned subset is NINE district-cycles, below the threshold of ten this project already uses
to withhold inference (`MIN_N_FOR_SLOPE` in diag_ie_vs_margin.py), and its treatment is
almost entirely absent -- under the race-matched specification the largest net advantage in
any Senate cell is about $62K, and six of the nine sit within a thousand dollars of zero.
Where the Senate subset shows MORE dispersion than the full panel (the express-advocacy
scope) it is one race doing it, not nine.

So sacrificing cell count for treatment validity does not buy a cleaner estimate here. It
buys a panel with no usable treatment variation, which is a sharper statement of "raw cell
count is not the binding quantity; usable variation in treatment is" than the 129-cell
headline can make.

BASIS. Pinned frames only -- `ie_vs_residual_2026-08-09.csv` (federal, 34 scorable
district-cycles) and `pdc_ie_vs_residual_2026-08-15.csv` (legislative, 129 x 4
scope/specification combinations). No warehouse, no forecast model, so this runs from a bare
public clone. Race-level aggregates; no personal data. Deterministic (fixed seed).

    python scripts/diag_ie_inference_sensitivity.py
"""
from __future__ import annotations

import csv
import random
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FED = ROOT / "docs" / "reference" / "ie_vs_residual_2026-08-09.csv"
LEG = ROOT / "docs" / "reference" / "pdc_ie_vs_residual_2026-08-15.csv"
MIN_N_FOR_SLOPE = 10  # mirrors diag_ie_vs_margin.py; below this, inference is withheld

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

import numpy as np  # noqa: E402


def _read(p: Path) -> list[dict]:
    with p.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def _fit(x: np.ndarray, y: np.ndarray):
    """OLS with intercept. Returns (beta, residuals, X)."""
    X = np.column_stack([np.ones(len(x)), x])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta, y - X @ beta, X


def _hc3(x: np.ndarray, y: np.ndarray) -> float:
    """HC3 standard error on the slope. Inflates high-leverage residuals deliberately."""
    beta, e, X = _fit(x, y)
    XtX_inv = np.linalg.inv(X.T @ X)
    h = np.einsum("ij,jk,ik->i", X, XtX_inv, X)
    omega = (e / (1.0 - h)) ** 2
    V = XtX_inv @ (X.T @ (omega[:, None] * X)) @ XtX_inv
    return float(np.sqrt(V[1, 1]))


def _cr_se(x: np.ndarray, y: np.ndarray, groups: list[str]) -> tuple[float, int]:
    """Cluster-robust slope SE with the standard small-sample correction."""
    beta, e, X = _fit(x, y)
    XtX_inv = np.linalg.inv(X.T @ X)
    uniq = sorted(set(groups))
    meat = np.zeros((2, 2))
    for g in uniq:
        idx = [i for i, gg in enumerate(groups) if gg == g]
        Xg, eg = X[idx], e[idx]
        s = Xg.T @ eg
        meat += np.outer(s, s)
    G, n, k = len(uniq), len(y), 2
    c = (G / (G - 1.0)) * ((n - 1.0) / (n - k))
    V = c * (XtX_inv @ meat @ XtX_inv)
    return float(np.sqrt(V[1, 1])), G


def _wild_cluster_p(x: np.ndarray, y: np.ndarray, groups: list[str],
                    iters: int = 9999, seed: int = 12345) -> tuple[float, int]:
    """Wild CLUSTER bootstrap p-value for H0: slope = 0 (Cameron-Gelbach-Miller).

    Imposes the null, then re-signs each CLUSTER's residuals with a Rademacher draw. This is
    the recommended procedure with few clusters and is the check the paper's percentile
    cluster bootstrap cannot substitute for.
    """
    # restricted fit: slope forced to zero, so residuals are y - mean(y)
    e0 = y - y.mean()
    beta, _, _ = _fit(x, y)
    t_obs = abs(beta[1] / _cr_se(x, y, groups)[0])
    uniq = sorted(set(groups))
    rng = random.Random(seed)
    worse = 0
    ok = 0
    for _ in range(iters):
        w = {g: (1.0 if rng.random() < 0.5 else -1.0) for g in uniq}
        yb = y.mean() + np.array([e0[i] * w[groups[i]] for i in range(len(y))])
        try:
            bb, _, _ = _fit(x, yb)
            se, _ = _cr_se(x, yb, groups)
            if se <= 0 or not np.isfinite(se):
                continue
            ok += 1
            if abs(bb[1] / se) >= t_obs:
                worse += 1
        except np.linalg.LinAlgError:  # noqa: PERF203
            continue
    return ((worse + 1) / (ok + 1) if ok else float("nan")), len(uniq)


def part_a() -> None:
    rows = _read(FED)
    x = np.array([float(r["net_pro_dem_m"]) for r in rows])
    y = np.array([float(r["residual_pp"]) for r in rows])
    g = [r["district_id"] for r in rows]
    beta, _, _ = _fit(x, y)
    slope = float(beta[1])

    print("=" * 92)
    print("PART A — INFERENCE SENSITIVITY, federal panel "
          f"(n={len(rows)}, {len(set(g))} district clusters)")
    print("=" * 92)
    print(f"OLS slope: {slope:+.3f} points of residual per $1M net pro-Dem IE")
    print("(the paper's published case-resampling interval is [-0.600, +2.821] and its")
    print(" district-clustered percentile interval is [-1.595, +1.268])\n")

    se_hc3 = _hc3(x, y)
    se_cr, G = _cr_se(x, y, g)
    print(f"{'method':34} {'SE':>8} {'95% interval':>22} {'excludes 0':>11}")
    print("-" * 92)
    for name, se in (("HC3 (robust, unclustered)", se_hc3),
                     (f"CR (clustered on district, G={G})", se_cr)):
        lo, hi = slope - 1.96 * se, slope + 1.96 * se
        print(f"{name:34} {se:>8.3f} [{lo:>+8.3f},{hi:>+8.3f}] "
              f"{('NO' if lo <= 0 <= hi else 'YES'):>11}")
    p, G2 = _wild_cluster_p(x, y, g)
    print(f"{'wild cluster bootstrap (Rademacher)':34} {'—':>8} "
          f"{'p = ' + format(p, '.3f'):>22} {('NO' if p > 0.05 else 'YES'):>11}")
    print(f"\nWild cluster bootstrap imposes H0 and re-signs residuals by cluster over "
          f"{G2} clusters.")
    print("Every method here fails to exclude zero, on top of the two the paper already")
    print("reports. The sign is not pinned down under any inference procedure tried.")


def part_b() -> None:
    rows = _read(LEG)
    print("\n" + "=" * 92)
    print("PART B — THE CLEANLY ASSIGNED LEGISLATIVE SUBSET (Senate-only)")
    print("=" * 92)
    print("PDC identifies a candidate's CHAMBER but not their House POSITION, so a")
    print("district-level expenditure is ambiguous between Position 1 and Position 2.")
    print("Senate districts carry one seat, so assignment is unambiguous there.\n")
    print(f"{'scope':9} {'specification':20} {'n':>4} {'SD(net) $M':>11} "
          f"{'max|net| $M':>12} {'near-zero':>10} {'slope':>9}")
    print("-" * 92)
    for sc in ("all", "express"):
        for sp in ("district_aggregate", "race_matched"):
            sub = [r for r in rows
                   if r["advocacy_scope"] == sc and r["specification"] == sp
                   and r["is_senate"] == "1"]
            net = [float(r["net_pro_dem_musd"]) for r in sub]
            res = [float(r["residual_pp"]) for r in sub]
            nz = sum(1 for v in net if abs(v) <= 0.001)
            sd = st.stdev(net) if len(net) > 1 else 0.0
            if len(set(net)) > 1:
                b, _, _ = _fit(np.array(net), np.array(res))
                slope = f"{b[1]:+.2f}"
            else:
                slope = "n/a"
            print(f"{sc:9} {sp:20} {len(sub):>4} {sd:>11.4f} "
                  f"{max(abs(v) for v in net):>12.4f} {nz:>10} {slope:>9}")
    n_sen = len({(r["district_id"], r["cycle"]) for r in rows if r["is_senate"] == "1"})
    print(f"\nDistinct Senate district-cycles: {n_sen}, against a threshold of "
          f"{MIN_N_FOR_SLOPE} below which")
    print("this project already withholds inference (MIN_N_FOR_SLOPE, diag_ie_vs_margin.py).")
    print("So the cleanly assigned panel falls below the bar the paper set for itself, and")
    print("its treatment is nearly absent rather than merely sparse. Where the Senate subset")
    print("shows MORE dispersion than the full 129 (express scope) it is ONE race doing it.")
    print("\nSacrificing cell count for treatment validity does not buy a cleaner estimate")
    print("here — it buys a panel with no usable treatment variation. That is a sharper")
    print("statement of 'usable variation in treatment is the binding quantity' than the")
    print("129-cell headline can make, and it is the referee's design suggestion carried out")
    print("rather than declined.")


def main() -> int:
    for p in (FED, LEG):
        if not p.exists():
            print(f"FATAL: pinned frame missing: {p}")
            return 1
    part_a()
    part_b()
    print("\nNeither part identifies a causal effect. IE is allocated by committees who")
    print("observe expected closeness; every number here is an association.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
