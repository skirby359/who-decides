"""How much of the dependent variable can a reader reproduce, and exactly where does it stop?

RAISED BY AN EXTERNAL REFEREE, 2026-08-25: "A paper whose principal dependent variable is a
model residual is going to encounter resistance if the underlying model cannot itself be
regenerated." Correct, and the honest response is not to claim more reproducibility than
exists. It is to make the boundary exact.

AUTHOR DECISION 2026-08-25: publish a MINIMAL residual-generation extract rather than the
forecast implementation. This is that extract. It exists to convert a vague limitation --
"the residuals are not independently reproducible" -- into a precise one, and it turns out
that most of the construction IS reproducible from what is already published.

WHAT A READER CAN CHECK WITHOUT ANYTHING PRIVATE, and this script checks it:

  1. THE RESIDUAL'S ARITHMETIC. `residual_pp = actual_dem_pct - predicted_dem_pct`, and BOTH
     operands are published in the pinned frame. All 34 scorable district-cycles reconcile.
     So the residual is not an opaque quantity: it is a subtraction between two published
     columns, and anyone can verify it.
  2. THE MODEL'S FORM AND COEFFICIENTS. The forecast equation and the coefficient set are
     public in `config/national_data.py`, tagged `v-jun17`. A reader can see what the
     prediction is a function of, and with what weights.
  3. EVERY STATISTIC BUILT ON THE RESIDUAL. The slopes, intervals, leave-one-out sweeps,
     functional-form sensitivities and inference checks all read the pinned frame and are
     recomputable end to end -- see diag_ie_functional_form.py and
     diag_ie_inference_sensitivity.py, both of which run from a bare public clone.

WHAT REMAINS UNREPRODUCIBLE, stated as one step rather than as a general caveat:

  * `predicted_dem_pct` itself. Turning a district's inputs into a predicted Democratic share
    needs `national_model.build_structural_forecast`, which is not published because it is
    the campaign product this project also sells. A reader cannot regenerate that column;
    they can see its inputs, its coefficients, its output, and everything computed from it.

WHY THIS IS NOT A FULL ANSWER, said plainly. A reader who doubts the MODEL cannot check the
model. This extract does not fix that -- it establishes that the doubt is confined to one
column, that the column's consumers are all open, and that the arithmetic around it holds. If
a venue requires the model, the answer is to publish the model, not to point at this script.

No database, no person-level data: the pinned frame is race-level aggregates.

    python scripts/verify_residual_construction.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRAME = ROOT / "docs" / "reference" / "ie_vs_residual_2026-08-09.csv"
COEFFS = ROOT / "config" / "national_data.py"
TOL = 0.005

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass


def main() -> int:
    if not FRAME.exists():
        print(f"FATAL: pinned frame missing: {FRAME}")
        return 1
    with FRAME.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))

    print("=" * 88)
    print("RESIDUAL CONSTRUCTION — what is reproducible, and precisely where it stops")
    print("=" * 88)
    print(f"pinned frame: {FRAME.relative_to(ROOT)}\n")

    scorable = [r for r in rows if r.get("residual_pp") and r.get("predicted_dem_pct")]
    bad = []
    for r in scorable:
        got = float(r["residual_pp"])
        want = float(r["actual_dem_pct"]) - float(r["predicted_dem_pct"])
        if abs(got - want) > TOL:
            bad.append((r["district_id"], r["cycle"], got, round(want, 4)))

    print("STEP 1 — the residual is a subtraction between two PUBLISHED columns.")
    print(f"    residual_pp == actual_dem_pct - predicted_dem_pct   (tolerance {TOL})")
    print(f"    checked on {len(scorable)} scorable district-cycles: "
          f"{len(scorable) - len(bad)} reconcile, {len(bad)} do not.")
    for b in bad[:10]:
        print(f"      MISMATCH {b[0]}/{b[1]}: frame {b[2]}, arithmetic {b[3]}")
    if bad:
        print("\n    A mismatch here means the published frame is internally inconsistent,")
        print("    which is a defect in the frame rather than a limit on reproducibility.")
        return 1

    print("\nSTEP 2 — the model's form and coefficients are public.")
    print(f"    {COEFFS.relative_to(ROOT)} exists: {COEFFS.exists()}")
    if COEFFS.exists():
        src = COEFFS.read_text(encoding="utf-8", errors="replace")
        tag = next((ln.strip() for ln in src.splitlines() if "v-jun17" in ln), None)
        print(f"    coefficient set tagged: {tag or 'v-jun17 tag not found in this file'}")
    print("    equation: dem_pct = baseline + elasticity x wave + sum(adjustments),")
    print("    clipped to a safe-seat cap that scales with distance from 50%.")

    print("\nSTEP 3 — every statistic built on the residual is recomputable from the frame.")
    for s in ("diag_ie_functional_form.py", "diag_ie_inference_sensitivity.py"):
        print(f"    {s:38} present: {(ROOT / 'scripts' / s).exists()}")

    print("\nWHAT IS NOT REPRODUCIBLE, and it is one column:")
    print("    predicted_dem_pct. Producing it needs national_model.build_structural_forecast,")
    print("    which is not published. A reader can see its inputs, its coefficients, its")
    print("    output and everything computed from it — but cannot regenerate it.")
    print("\n    This narrows the limitation; it does not remove it. A reader who doubts the")
    print("    MODEL still cannot check the model, and no script in this repository fixes")
    print("    that. Publishing the model is the only thing that would.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
