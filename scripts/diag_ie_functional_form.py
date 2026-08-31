"""Does the IE slope survive a functional form that does not privilege one race?

RAISED BY AN EXTERNAL REFEREE, 2026-08-25. `does-money-move-votes.md` regresses the
fundamentals-net residual on NET independent-expenditure advantage,
`support-D + oppose-R - support-R - oppose-D`, linear in raw dollars. Two objections, both
correct, and neither answerable by reporting more diagnostics on the same specification:

  1. CANCELLATION. Net treats a dollar for D as commensurate with a dollar against R and
     lets opposite sides cancel LINEARLY. Measured on the pinned panel: gross IE is
     $70.87M and the sum of |net| is $22.64M, so 68% of the money cancels away. cd08/22
     turns $17.47M of two-sided expenditure into -$0.20M net -- 1% surviving -- so the
     second most heavily financed race in the panel enters the regression as if it were
     almost untreated. The design therefore has least purchase exactly where treatment
     intensity is highest.

     ⚠ One qualifier the referee did not have, and it matters: of the 19 races the
     specification codes as untreated, ZERO carry any gross IE. Those are genuine zeros,
     not cancellation artifacts. The problem is confined to six races -- and they are the
     six largest.

  2. LEVERAGE UNDER A RAW-DOLLAR LINEAR FORM. The panel's x runs $0 to +$8.26M with a
     heavy tail. cd08/18 holds the largest net AND one of the largest residuals, Cook's
     distance 0.690, and deleting it moves the slope from +0.515 to -0.035. Reporting that
     influence honestly -- which the paper does -- is not the same as testing whether the
     functional form is the reason for it.

WHAT THIS RUNS. Five specifications on the SAME 34 district-cycles, so the only thing that
changes is the treatment's functional form:

    S1  residual ~ net                     the paper's specification, reproduced
    S2  residual ~ asinh(net)              same sign, tail de-weighted (asinh, not log:
                                           net is signed and crosses zero)
    S3  residual ~ pro_dem + pro_rep       cancellation relaxed; the two sides free to
                                           carry different coefficients
    S4  residual ~ net + total             net advantage AND intensity together: does
                                           "how much money" matter beside "whose money"
    S5  residual ~ sign(net)*log1p(|net|)  a second signed-compression, to show S2 is not
                                           an artifact of one transform

WHY IT IS WORTH RUNNING EVEN IF NOTHING SURVIVES -- and nothing is expected to. The paper's
thesis is that the observational record cannot identify an effect. A slope that appears only
under one functional form, driven by one observation, is WEAKER evidence for that thesis than
a slope that is unstable across every reasonable form. If all five say the sign is not pinned
down, the identification-failure claim stops resting on a single influence diagnostic.

BASIS. Reads the PINNED frame `docs/reference/ie_vs_residual_2026-08-09.csv` (34 scorable
district-cycles), not the live warehouse -- the residual column needs the forecast model,
which is not public, and pinning is what makes these statistics reproducible by a reader.
Race-level aggregates only; no personal data. Deterministic: fixed bootstrap seed.

    python scripts/diag_ie_functional_form.py
"""
from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
FRAME = ROOT / "docs" / "reference" / "ie_vs_residual_2026-08-09.csv"

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

import numpy as np  # noqa: E402


def _rows() -> list[dict]:
    with FRAME.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def _ols(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Coefficients with an intercept prepended. Least squares, no regularisation."""
    A = np.column_stack([np.ones(len(X))] + [X[:, j] for j in range(X.shape[1])])
    beta, *_ = np.linalg.lstsq(A, y, rcond=None)
    return beta


def _boot_ci(X: np.ndarray, y: np.ndarray, idx: int, iters: int = 5000,
             seed: int = 12345) -> tuple[float, float]:
    """Percentile CI for one coefficient by CASE resampling.

    Same convention as diag_ie_vs_margin.bootstrap_slope_ci -- resample rows with
    replacement, refit, take the 2.5/97.5 percentiles -- so the intervals here are
    comparable to the paper's headline rather than to a different estimator.
    """
    # ⚠ USES `random.Random` AND THE SAME PERCENTILE INDEXING AS
    # diag_ie_vs_margin.bootstrap_slope_ci, DELIBERATELY. A numpy Generator draws a different
    # stream from the same seed, which made S1 report [-0.748, +2.748] against the paper's
    # published [-0.600, +2.821] -- identical coefficient, different interval, and a phantom
    # discrepancy that a later reader would try to "fix". Matching the estimator makes S1 a
    # genuine reproduction check on the published headline instead.
    import random
    rng = random.Random(seed)
    n = len(y)
    ids = list(range(n))
    out = []
    for _ in range(iters):
        pick = [rng.choice(ids) for _ in range(n)]
        Xb, yb = X[pick], y[pick]
        if bool(np.any(np.isclose(Xb.std(axis=0), 0.0))):
            continue
        try:
            out.append(_ols(Xb, yb)[idx])
        except np.linalg.LinAlgError:  # noqa: PERF203
            continue
    if not out:
        return float("nan"), float("nan")
    out.sort()
    return out[int(0.025 * len(out))], out[int(0.975 * len(out))]


def _loo_range(X: np.ndarray, y: np.ndarray, idx: int,
               labels: list[str]) -> tuple[float, str, float, str]:
    lo, lo_l, hi, hi_l = math.inf, "", -math.inf, ""
    for i in range(len(y)):
        keep = [j for j in range(len(y)) if j != i]
        b = _ols(X[keep], y[keep])[idx]
        if b < lo:
            lo, lo_l = b, labels[i]
        if b > hi:
            hi, hi_l = b, labels[i]
    return lo, lo_l, hi, hi_l


def main() -> int:
    if not FRAME.exists():
        print(f"FATAL: pinned frame missing: {FRAME}")
        return 1
    rows = _rows()
    lab = [f"{r['district_id']}/{str(r['cycle'])[2:]}" for r in rows]
    y = np.array([float(r["residual_pp"]) for r in rows])
    net = np.array([float(r["net_pro_dem_m"]) for r in rows])
    tot = np.array([float(r["total_m"]) for r in rows])
    prod = np.array([float(r["pro_dem"]) for r in rows]) / 1e6
    pror = np.array([float(r["pro_rep"]) for r in rows]) / 1e6

    print("=" * 92)
    print("IE FUNCTIONAL FORM — five specifications, one panel of "
          f"{len(rows)} scorable district-cycles")
    print("=" * 92)
    print(f"pinned frame: {FRAME.relative_to(ROOT)}")
    print(f"gross IE ${tot.sum():.2f}M   sum |net| ${np.abs(net).sum():.2f}M   "
          f"cancelled ${tot.sum() - np.abs(net).sum():.2f}M "
          f"({100 * (tot.sum() - np.abs(net).sum()) / tot.sum():.0f}%)")
    zero_net = int((np.abs(net) < 0.01).sum())
    print(f"coded ~untreated (|net| < $0.01M): {zero_net}; of those carrying gross IE: "
          f"{int(((np.abs(net) < 0.01) & (tot > 0.01)).sum())}  "
          f"(so the zeros are genuine, not cancellation)")

    signed_log = np.sign(net) * np.log1p(np.abs(net))
    specs = [
        ("S1  residual ~ net                    ", np.column_stack([net]), 1, "net"),
        ("S2  residual ~ asinh(net)             ", np.column_stack([np.arcsinh(net)]), 1,
         "asinh(net)"),
        ("S3  residual ~ pro_dem + pro_rep      ", np.column_stack([prod, pror]), 1,
         "pro_dem"),
        ("S4  residual ~ net + total            ", np.column_stack([net, tot]), 1, "net"),
        ("S5  residual ~ sign(net)*log1p(|net|) ", np.column_stack([signed_log]), 1,
         "signed log"),
    ]
    print(f"\n{'specification':40} {'coef':>9} {'95% boot CI':>22} {'spans 0':>8}"
          f" {'LOO range':>22}")
    print("-" * 92)
    verdicts = []
    for name, X, idx, term in specs:
        b = _ols(X, y)
        lo, hi = _boot_ci(X, y, idx)
        llo, llo_l, lhi, lhi_l = _loo_range(X, y, idx, lab)
        spans = "yes" if (lo <= 0 <= hi) else "NO"
        verdicts.append(spans)
        print(f"{name} {b[idx]:>9.3f} [{lo:>+8.3f},{hi:>+8.3f}] {spans:>8}"
              f"  [{llo:>+7.3f},{lhi:>+7.3f}]")
        if X.shape[1] > 1:
            lo2, hi2 = _boot_ci(X, y, 2)
            second = "pro_rep" if name.startswith("S3") else "total (intensity)"
            print(f"{'    (same fit) ' + second:40} {b[2]:>9.3f} "
                  f"[{lo2:>+8.3f},{hi2:>+8.3f}]")
        print(f"{'':40} drop {llo_l} -> {llo:+.3f} | drop {lhi_l} -> {lhi:+.3f}")

    print("\n" + "=" * 92)
    n_span = sum(1 for v in verdicts if v == "yes")
    print(f"{n_span} of {len(verdicts)} specifications have a 95% interval spanning zero.")
    if n_span == len(verdicts):
        print("READ: the sign is not pinned down under ANY of these treatment forms. That is a")
        print("stronger statement of the paper's thesis than an unstable estimate under one")
        print("form, because it cannot be attributed to the choice of functional form.")
    else:
        print("READ: at least one form excludes zero. That does NOT identify an effect -- the")
        print("treatment is still strategically assigned -- but it must be reported, and the")
        print("paper's 'every interval spans zero' framing would need narrowing.")
    print("\nNeither result identifies a causal effect. Net IE is chosen by committees who")
    print("observe expected closeness, so every specification here is an association.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
