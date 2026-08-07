"""A9x — score the Idaho stratified validation draw (`idaho1`).

**Written 2026-08-01, before any verdict existed.** That is the point: the analysis in
`docs/idaho-validation-rater-instructions.md` §4 is pre-specified, and a scorer authored after
reading the verdicts would be a choice made with knowledge of the answer. This file exists so
that scoring is mechanical.

Why not `score_match_validation.py`. That script scores the 480-record 2026-07-27 pass and
cannot score this draw, for four separate reasons — each of which would fail quietly rather
than loudly:

  * Its paths are hard-coded to `match_validation_stratified*`. There is no `--label`.
  * It has **no party stratum**. It groups by tier, panel, band and panel×tier. The Idaho
    design turns on **panel × registered party**, which is the cell the finding under attack
    lives in, and that grouping does not exist there.
  * It **tier-reweights**, using `TIER_SHARES_2026_07_27`. This draw is single-tier by
    construction (`STRICT_ZIP5_FULL` only), so reweighting is meaningless here — and applying
    it is a near-relative of the bug that constant was introduced to prevent.
  * It has no `partial_merge` concept, so it would silently drop a column the specification
    requires to be reported.

What this script deliberately does NOT do. It stops at stratum bounds. Translating a bound
into the paper's adversarial-deletion table — the step that takes ID federal from 20.4% to
18.4% — belongs to whatever already computes that table, not to a second implementation here.
Two implementations of one number is how they drift apart.

    python scripts/score_idaho_validation.py --self-test
    python scripts/score_idaho_validation.py --extract      # verdicts-only, no names
    python scripts/score_idaho_validation.py                # score

Read-only with respect to the panels; writes nothing except under `--extract`.
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTDIR = ROOT / "data" / "validation"

VALID = {"Y", "NC", "NP", "U"}
PRIMARY_TIER = "STRICT_ZIP5_FULL"
PARTIES = ["DEM", "REP", "UNA"]
BANDS = ["top10", "rest"]
PANELS = ["federal", "state"]

# The three readings, fixed before the rater begins. `errors` and `excluded` partition the
# four verdicts; anything excluded leaves the denominator and is reported as a count, never
# dropped in silence.
SPECS: dict[str, tuple[set[str], set[str]]] = {
    # name              errors            excluded from denominator
    "primary":         ({"NC", "NP"},     {"U"}),
    "nc_only":         ({"NC"},           {"NP", "U"}),
    "nc_np_u":         ({"NC", "NP", "U"}, set()),
}
SPEC_BLURB = {
    "primary": "NC and NP are errors; U leaves the denominator (the published convention)",
    "nc_only": "NC only; NP treated as unresolved rather than wrong",
    "nc_np_u": "every indeterminate counted against the match",
}

# Zero-error Wilson ceilings quoted in the rater instructions. Reproducing these is the
# self-test: if the arithmetic here disagrees with the number the author published in the
# design document, one of the two is wrong and it must not be discovered later.
DOCUMENTED_CEILINGS = {20: 16.1, 34: 10.2, 51: 7.0, 102: 3.6}


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval, as percentages. Same formula as score_match_validation.wilson."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d * 100, (c + h) / d * 100)


def ceiling(n: int) -> float:
    """Upper 95% Wilson bound on the error rate when zero errors are observed in n records."""
    return wilson(0, n)[1]


def tally(counts: Counter, spec: str) -> tuple[int, int, float, float]:
    """(n_denominator, n_errors, error %, Wilson upper bound on error %) under one spec."""
    err_codes, excluded = SPECS[spec]
    n = sum(v for k, v in counts.items() if k not in excluded)
    e = sum(v for k, v in counts.items() if k in err_codes)
    if n == 0:
        return 0, 0, float("nan"), float("nan")
    return n, e, 100.0 * e / n, wilson(e, n)[1]


def load_key(label: str) -> dict[str, dict]:
    path = OUTDIR / f"match_validation_{label}_key.csv"
    if not path.exists():
        sys.exit(f"!! key file missing: {path}")
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return {r["sample_id"]: r for r in csv.DictReader(fh)}


def load_verdicts(path: Path) -> list[dict]:
    """Read sample_id / verdict / partial_merge. Never prints a row."""
    if not path.exists():
        sys.exit(f"!! verdict file missing: {path}\n"
                 f"   Place the rater's returned CSV there, or pass --verdicts.")
    with path.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    out = []
    for r in rows:
        out.append({
            "sample_id": (r.get("sample_id") or "").strip(),
            "verdict": (r.get("verdict") or "").strip().upper(),
            "partial_merge": (r.get("partial_merge") or "").strip().lower() in ("y", "yes", "1", "true"),
        })
    return out


def extract(label: str) -> int:
    """Write a verdicts-only file so scoring never has to open the name-bearing evidence.

    The evidence CSV pairs voter and donor names. This reduces it to three non-identifying
    columns, printing counts only, so every later step — including one run alongside an
    assistant — touches no personal data.
    """
    src = OUTDIR / f"match_validation_{label}.csv"
    dst = OUTDIR / f"match_validation_{label}_verdicts.csv"
    rows = load_verdicts(src)
    if dst.exists():
        sys.exit(f"!! refusing to overwrite {dst.name} — delete it deliberately first.")
    with dst.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["sample_id", "verdict", "partial_merge"])
        for r in rows:
            w.writerow([r["sample_id"], r["verdict"], "y" if r["partial_merge"] else ""])
    rated = sum(1 for r in rows if r["verdict"] in VALID)
    print(f"wrote {dst.relative_to(ROOT)} — {len(rows)} rows, {rated} carrying a valid verdict.")
    print("No names are in that file. Score with:  python scripts/score_idaho_validation.py")
    return 0


def report(key: dict[str, dict], verdicts: list[dict], label: str) -> int:
    by_id = {v["sample_id"]: v for v in verdicts}

    missing = sorted(set(key) - set(by_id))
    extra = sorted(set(by_id) - set(key))
    bad = sorted(s for s, v in by_id.items() if v["verdict"] not in VALID)
    if missing or extra or bad:
        if missing:
            print(f"!! {len(missing)} sampled records have no verdict (first: {missing[:5]})")
        if extra:
            print(f"!! {len(extra)} returned ids are not in the draw (first: {extra[:5]})")
        if bad:
            print(f"!! {len(bad)} invalid verdicts — need Y / NC / NP / U (first: {bad[:5]})")
        return 1

    tiers = {k["tier"] for k in key.values()}
    if tiers != {PRIMARY_TIER}:
        print(f"!! expected a single-tier draw ({PRIMARY_TIER}); found {sorted(tiers)}.")
        print("   Tier reweighting is not applied here and this script is not valid for a "
              "multi-tier draw.")
        return 1

    cells: dict[tuple, Counter] = defaultdict(Counter)
    merges: Counter = Counter()
    for sid, v in by_id.items():
        k = key[sid]
        panel, party, band = k["panel"], k["reg_party"], k["dollar_band"]
        cells[("panel_party", panel, party)][v["verdict"]] += 1
        cells[("panel_band", panel, band)][v["verdict"]] += 1
        cells[("panel", panel)][v["verdict"]] += 1
        cells[("party", party)][v["verdict"]] += 1
        cells[("all",)][v["verdict"]] += 1
        if v["partial_merge"]:
            merges[panel] += 1

    print("=" * 92)
    print(f"A9x — IDAHO STRATIFIED VALIDATION  ({label}, {len(by_id)} records, "
          f"{PRIMARY_TIER} only)")
    print("=" * 92)
    print("\nPre-specified in docs/idaho-validation-rater-instructions.md §4. Bounds are computed")
    print("WITHIN stratum and are not pooled across strata. The panel rows below are raw sample")
    print("means over a deliberately disproportionate draw: they are NOT panel precision")
    print("estimates and carry no bound.")

    for spec in SPECS:
        print(f"\n{'-' * 92}\n{spec.upper()}  —  {SPEC_BLURB[spec]}\n{'-' * 92}")
        print(f"  {'stratum':<34}{'n':>5}{'err':>5}{'err %':>9}{'95% upper':>11}")

        print("\n  by panel x registered party   <-- the bound that carries the party finding")
        for panel in PANELS:
            for party in PARTIES:
                n, e, pct, hi = tally(cells[("panel_party", panel, party)], spec)
                star = "  *" if (party == "DEM" and e == 0) else ""
                print(f"  {'ID ' + panel + ' / ' + party:<34}{n:>5}{e:>5}"
                      f"{pct:>8.1f}%{hi:>10.1f}%{star}")

        print("\n  by panel x dollar band")
        for panel in PANELS:
            for band in BANDS:
                n, e, pct, hi = tally(cells[("panel_band", panel, band)], spec)
                print(f"  {'ID ' + panel + ' / ' + band:<34}{n:>5}{e:>5}"
                      f"{pct:>8.1f}%{hi:>10.1f}%")

        print("\n  raw sample means (no bound — disproportionate draw)")
        for panel in PANELS:
            n, e, pct, _ = tally(cells[("panel", panel)], spec)
            print(f"  {'ID ' + panel:<34}{n:>5}{e:>5}{pct:>8.1f}%{'  —':>11}")
        n, e, pct, _ = tally(cells[("all",)], spec)
        print(f"  {'both panels':<34}{n:>5}{e:>5}{pct:>8.1f}%{'  —':>11}")

    print(f"\n{'-' * 92}\nPARTIAL MERGES — reported separately; NOT identity errors\n{'-' * 92}")
    for panel in PANELS:
        print(f"  ID {panel:<30}{merges[panel]:>5}")
    print("  The matched voter genuinely is a donor, but the attributed total sweeps in another")
    print("  person's gift. A dollar-attribution problem; the party finding rests on identities.")

    dem_clean = all(tally(cells[("panel_party", p, "DEM")], "primary")[1] == 0 for p in PANELS)
    print(f"\n{'=' * 92}")
    if dem_clean:
        lo = min(tally(cells[("panel_party", p, "DEM")], "primary")[0] for p in PANELS)
        print(f"Zero errors in both Democratic strata. Panel-specific ceiling {ceiling(lo):.1f}% "
              f"(n={lo}).")
        print("Apply it to the party result via the paper's existing deletion table — not here.")
    else:
        print("AT LEAST ONE ERROR IN A DEMOCRATIC STRATUM. Per §4.3 of the instructions this is")
        print("not to be smoothed: the 'no detected false match on the primary key' claim must be")
        print("restated as a measured rate, and that belongs in the abstract.")
    print("=" * 92)
    return 0


def self_test() -> int:
    """Validate the arithmetic against the design document, using no real data."""
    print("Reproducing the zero-error ceilings quoted in the rater instructions:\n")
    print(f"  {'n':>5}{'documented':>13}{'computed':>11}")
    ok = True
    for n, want in sorted(DOCUMENTED_CEILINGS.items()):
        got = ceiling(n)
        match = abs(got - want) < 0.05
        ok &= match
        print(f"  {n:>5}{want:>12.1f}%{got:>10.1f}%   {'ok' if match else 'MISMATCH'}")
    if not ok:
        print("\n!! The scorer disagrees with the published design. Resolve before rating.")
        return 1

    print("\nSynthetic all-Y pass over the real strata sizes (no verdicts, no names read):")
    key = load_key("idaho1")
    fake = [{"sample_id": s, "verdict": "Y", "partial_merge": False} for s in key]
    sizes = Counter((k["panel"], k["reg_party"]) for k in key.values())
    for (panel, party), n in sorted(sizes.items()):
        print(f"  ID {panel} / {party}: n={n}, zero-error ceiling {ceiling(n):.1f}%")
    print()
    return report(key, fake, "idaho1 [SYNTHETIC all-Y — not a result]")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--label", default="idaho1", help="draw label (default: idaho1)")
    ap.add_argument("--verdicts", type=Path, default=None,
                    help="verdict CSV; defaults to the _verdicts extract, then the evidence file")
    ap.add_argument("--extract", action="store_true",
                    help="write a verdicts-only CSV from the returned evidence, then stop")
    ap.add_argument("--self-test", action="store_true",
                    help="check the arithmetic against the design document and exit")
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    if args.extract:
        return extract(args.label)

    src = args.verdicts
    if src is None:
        preferred = OUTDIR / f"match_validation_{args.label}_verdicts.csv"
        src = preferred if preferred.exists() else OUTDIR / f"match_validation_{args.label}.csv"
    return report(load_key(args.label), load_verdicts(src), args.label)


if __name__ == "__main__":
    raise SystemExit(main())
