"""Score the stratified blinded match-validation sample.

Companion to `diag_match_validation_stratified.py`. Written BEFORE the verdicts were
recorded, so the analysis is fixed in advance rather than chosen after seeing them.

Joins recorded verdicts to the stratum key (which the rater never saw) and reports what
the external review asked for:

  * counts by state, panel, match tier and donor-dollar band;
  * precision separately for EVERY match tier, with a Wilson 95% interval;
  * confirmed-false (NC), probable-false (NP) and unverifiable (U) reported SEPARATELY,
    never pooled;
  * a sensitivity bound treating every unverifiable record as a false match;
  * a POPULATION-WEIGHTED precision per panel. The sample deliberately oversamples the
    weak tiers (120 each, against a population share of 0.3-13%), so the unweighted
    sample mean is NOT an estimate of panel precision — it must be reweighted by each
    tier's actual share of that panel.

TWO SPECIFICATIONS, TWO NUMBERS (2026-07-27). This sample was drawn from the ALL-TIER
panels, and the 93.0% donor-weighted figure it produces describes that — now
SUPERSEDED — specification. The paper's primary specification is the full-name key
alone, whose precision is simply the `STRICT_ZIP5_FULL` row: 120/120, 100%,
Wilson [96.9-100.0]. The script prints both, each labelled with its specification. They
must never be quoted in one breath without those labels.

WHY THE WEIGHTS ARE FROZEN, NOT QUERIED. An earlier version computed the reweighting
from LIVE per-tier panel shares. Once the panels are rebuilt full-name-only every panel
returns a single tier, the shares collapse to {STRICT_ZIP5_FULL: 1.0}, and the weighted
figure silently becomes 100.0% for all six panels — with exit code 0 and no warning.
The published 93.0% would have quietly rewritten itself into a result. The shares are
therefore pinned in `TIER_SHARES_2026_07_27` below, measured on the `_alltier`
snapshots, and `--verify-shares` re-derives them and fails loudly on drift.

PANEL TABLES ARE THE `_alltier` SNAPSHOTS, deliberately: this script scores a sample
drawn from that universe, so it must keep reading it after the primaries are rebuilt.
See `scripts/snapshot_alltier_panels.py`.

Verdicts: Y (same person) / NC (confirmed different) / NP (probably different) /
U (unverifiable). Refuses to score a partially-rated file.

Reads PII-bearing files under gitignored data/validation/ but prints only aggregates.

Run:  python scripts/score_match_validation.py
      python scripts/score_match_validation.py --verify-shares
"""
from __future__ import annotations

import argparse
import csv
import math
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUTDIR = DATA / "validation"
EVIDENCE = OUTDIR / "match_validation_stratified.csv"
KEYFILE = OUTDIR / "match_validation_stratified_key.csv"

VALID = {"Y", "NC", "NP", "U"}
TIERS = ["STRICT_ZIP5_FULL", "STRICT_ZIP5_MID", "STRICT_ZIP5", "RELAXED_ZIP3_MID"]
PANELS = [("WA", "federal"), ("WA", "state"), ("NY", "federal"), ("NY", "state"),
          ("ID", "federal"), ("ID", "state")]
# The `_alltier` snapshots, not the live primaries — see the docstring.
PANEL_TABLE = {"federal": "voter_donor_affiliation_fec_alltier",
               "state": "voter_donor_affiliation_state_alltier"}
DB = {"WA": "wa_statewide", "NY": "ny_statewide", "ID": "id_statewide"}

# Per-tier share of each ALL-TIER panel, over donors with total_donated > 0, measured
# from the `_alltier` snapshots on 2026-07-27 (scripts/snapshot_alltier_panels.py; census
# in docs/reference/panel_snapshot_2026-07-27.csv). These are the reweighting weights for
# the SUPERSEDED all-tier specification and are pinned so that figure stays reproducible
# after the primaries are rebuilt. Regenerate ONLY if the underlying voter file or
# contribution load changes, and then re-date the constant rather than editing in place.
TIER_SHARES_2026_07_27: dict[tuple[str, str], dict[str, float]] = {
    ("WA", "federal"): {"STRICT_ZIP5_FULL": 0.854027, "STRICT_ZIP5": 0.106799,
                        "RELAXED_ZIP3_MID": 0.023382, "STRICT_ZIP5_MID": 0.015792},
    ("WA", "state"):   {"STRICT_ZIP5_FULL": 0.806527, "STRICT_ZIP5": 0.124800,
                        "RELAXED_ZIP3_MID": 0.049996, "STRICT_ZIP5_MID": 0.018676},
    ("NY", "federal"): {"STRICT_ZIP5_FULL": 0.874536, "STRICT_ZIP5": 0.095153,
                        "RELAXED_ZIP3_MID": 0.017642, "STRICT_ZIP5_MID": 0.012669},
    ("NY", "state"):   {"STRICT_ZIP5_FULL": 0.892371, "STRICT_ZIP5": 0.100677,
                        "STRICT_ZIP5_MID": 0.003589, "RELAXED_ZIP3_MID": 0.003363},
    ("ID", "federal"): {"STRICT_ZIP5_FULL": 0.856854, "STRICT_ZIP5": 0.098470,
                        "RELAXED_ZIP3_MID": 0.024526, "STRICT_ZIP5_MID": 0.020150},
    ("ID", "state"):   {"STRICT_ZIP5_FULL": 0.866532, "STRICT_ZIP5": 0.125982,
                        "STRICT_ZIP5_MID": 0.004440, "RELAXED_ZIP3_MID": 0.003046},
}
# Matched-donor count per all-tier panel on the same date, for donor-weighting the grand
# mean. Pinned for the same reason as the shares.
PANEL_N_2026_07_27: dict[tuple[str, str], int] = {
    ("WA", "federal"): 172_998, ("WA", "state"): 268_741,
    ("NY", "federal"): 307_841, ("NY", "state"): 424_020,
    ("ID", "federal"): 27_196,  ("ID", "state"): 27_250,
}
PRIMARY_TIER = "STRICT_ZIP5_FULL"
SHARE_DRIFT_TOLERANCE = 0.0005   # 0.05 percentage points


def wilson(k, n, z=1.96):
    """Wilson score interval — behaves sanely at small n and p near 1, unlike normal."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d * 100, (c + h) / d * 100)


def precision(counts):
    """(precision %, lo, hi, n_judged) over judged records; U excluded."""
    y = counts["Y"]
    judged = y + counts["NC"] + counts["NP"]
    if judged == 0:
        return float("nan"), float("nan"), float("nan"), 0
    lo, hi = wilson(y, judged)
    return 100.0 * y / judged, lo, hi, judged


def bound(counts):
    """Sensitivity bound: every unverifiable record counted as a false match."""
    n = sum(counts[k] for k in VALID)
    return (100.0 * counts["Y"] / n) if n else float("nan")


def line(label, counts, width=30):
    p, lo, hi, judged = precision(counts)
    n = sum(counts[k] for k in VALID)
    return (f"  {label:<{width}}{n:>5}{counts['Y']:>6}{counts['NC']:>5}"
            f"{counts['NP']:>5}{counts['U']:>5}{p:8.1f}%  [{lo:4.1f}-{hi:5.1f}]"
            f"{bound(counts):9.1f}%")


HEADER = (f"  {'':<30}{'n':>5}{'Y':>6}{'NC':>5}{'NP':>5}{'U':>5}"
          f"{'precision':>9}  {'95% CI':^13}{'bound':>9}")


def measure_tier_shares():
    """Re-derive per-tier shares from the `_alltier` snapshots — for --verify-shares ONLY.

    Deliberately NOT used for scoring. Querying live shares is exactly the bug the frozen
    TIER_SHARES_2026_07_27 constant exists to prevent: on single-tier panels the shares
    collapse to 1.0 and the weighted figure silently reads 100%.
    """
    shares, sizes = {}, {}
    for state, panel in PANELS:
        con = duckdb.connect(str(DATA / f"{DB[state]}.duckdb"), read_only=True)
        rows = con.execute(f"""
            SELECT match_quality, COUNT(*) FROM {PANEL_TABLE[panel]}
            WHERE total_donated > 0 GROUP BY 1""").fetchall()
        con.close()
        tot = sum(n for _, n in rows) or 1
        shares[(state, panel)] = {t: n / tot for t, n in rows}
        sizes[(state, panel)] = tot
    return shares, sizes


def verify_shares() -> int:
    """Assert the frozen weights still describe the `_alltier` snapshots.

    Catches the case where someone rebuilds `_alltier` from a refreshed voter file and the
    published 93.0% quietly stops being the number the ledger claims.
    """
    print("=" * 78)
    print("VERIFY FROZEN TIER SHARES against the _alltier snapshots")
    print("=" * 78)
    live, sizes = measure_tier_shares()
    worst, failed = 0.0, []
    for state, panel in PANELS:
        frozen, got = TIER_SHARES_2026_07_27[(state, panel)], live[(state, panel)]
        n_frozen, n_live = PANEL_N_2026_07_27[(state, panel)], sizes[(state, panel)]
        flag = "" if n_frozen == n_live else f"   !! n {n_frozen:,} -> {n_live:,}"
        if n_frozen != n_live:
            failed.append(f"{state} {panel}: panel size {n_frozen:,} -> {n_live:,}")
        print(f"\n  {state} {panel}   n={n_live:,}{flag}")
        for t in TIERS:
            f_, l_ = frozen.get(t, 0.0), got.get(t, 0.0)
            d = abs(f_ - l_)
            worst = max(worst, d)
            if d > SHARE_DRIFT_TOLERANCE:
                failed.append(f"{state} {panel} {t}: {f_:.6f} -> {l_:.6f}")
            print(f"    {t:20} frozen {f_:.6f}  live {l_:.6f}  d={d:.6f}"
                  f"{'  OK' if d <= SHARE_DRIFT_TOLERANCE else '  DRIFT'}")
    print(f"\n  worst drift {worst:.6f}  (tolerance {SHARE_DRIFT_TOLERANCE})")
    if failed:
        print("\n  !! FAILED — the frozen weights no longer describe the snapshots:")
        for f in failed:
            print(f"     - {f}")
        print("\n  Do NOT edit TIER_SHARES_2026_07_27 in place. Add a new dated constant,")
        print("  and state in the paper which specification each figure describes.")
        return 1
    print("\n  PASS — the published 93.0% remains reproducible.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verify-shares", action="store_true",
                    help="re-derive the frozen tier shares from the _alltier snapshots "
                         "and fail loudly on drift")
    args = ap.parse_args()
    if args.verify_shares:
        return verify_shares()

    if not EVIDENCE.exists() or not KEYFILE.exists():
        print("!! sample missing — run scripts/diag_match_validation_stratified.py")
        return 1

    key = {r["sample_id"]: r for r in csv.DictReader(open(KEYFILE, encoding="utf-8"))}
    ev = list(csv.DictReader(open(EVIDENCE, encoding="utf-8-sig")))

    bad = [r["sample_id"] for r in ev if (r.get("verdict") or "").strip().upper() not in VALID]
    if bad:
        print(f"!! {len(bad)} of {len(ev)} rows unrated or invalid "
              f"(need Y / NC / NP / U). First few: {', '.join(bad[:8])}")
        return 1

    verdict = {r["sample_id"]: r["verdict"].strip().upper() for r in ev}
    by = defaultdict(Counter)
    for sid, v in verdict.items():
        k = key[sid]
        by["ALL"][v] += 1
        by[("tier", k["tier"])][v] += 1
        by[("panel", k["state"], k["panel"])][v] += 1
        by[("band", k["dollar_band"])][v] += 1
        by[("tp", k["state"], k["panel"], k["tier"])][v] += 1

    print("=" * 96)
    print("STRATIFIED BLINDED MATCH-PRECISION VALIDATION")
    print("=" * 96)
    print(f"\n{len(ev)} records rated. Verdicts: Y same person / NC confirmed different /")
    print("NP probably different / U unverifiable. `precision` = Y/(Y+NC+NP), U excluded;")
    print("`bound` = Y/(Y+NC+NP+U), i.e. every unverifiable record counted as an error.")

    print("\n--- BY MATCH TIER (the reviewer's headline ask) " + "-" * 49)
    print(HEADER)
    for t in TIERS:
        print(line(t, by[("tier", t)]))

    print("\n--- BY STATE x PANEL " + "-" * 75)
    print(HEADER)
    for state, panel in PANELS:
        print(line(f"{state} {panel}", by[("panel", state, panel)]))

    print("\n--- BY DONOR-DOLLAR BAND " + "-" * 71)
    print(HEADER)
    for b, lbl in (("top10", "top decile of matched $"), ("rest", "deciles 2-10")):
        print(line(lbl, by[("band", b)]))

    print("\n--- RAW SAMPLE MEAN (NOT a panel estimate — tiers are oversampled) " + "-" * 29)
    print(HEADER)
    print(line("all 480 records", by["ALL"]))

    # ---- CURRENT PRIMARY SPECIFICATION ----
    pc = by[("tier", PRIMARY_TIER)]
    pp, plo, phi, pjudged = precision(pc)
    _fs = [v[PRIMARY_TIER] for v in TIER_SHARES_2026_07_27.values()]
    print("\n" + "=" * 96)
    print("PRECISION OF THE CURRENT PRIMARY SPECIFICATION (full-name key only)")
    print("=" * 96)
    print(f"  {PRIMARY_TIER}: {pc['Y']}/{pjudged} judged -> {pp:.1f}%  "
          f"Wilson 95% [{plo:.1f}-{phi:.1f}]")
    print(f"  This is the specification the paper reports. It carries "
          f"{min(_fs)*100:.1f}-{max(_fs)*100:.1f}% of matches across the six panels.")
    print("  CEILING CAVEAT: this measures DETECTABLE error only. The rating catches")
    print("  'a different person with a different name'; it cannot catch a true namesake")
    print("  (same full first name, surname and ZIP5), so 100% is an upper bound on")
    print("  precision, not proof of zero error.")

    # ---- SUPERSEDED all-tier specification, on FROZEN weights ----
    shares = TIER_SHARES_2026_07_27
    sizes = PANEL_N_2026_07_27
    print("\n" + "=" * 96)
    print("WEIGHTED PRECISION OF THE 2026-07-27 ALL-TIER SPECIFICATION (SUPERSEDED)")
    print("=" * 96)
    print("Each tier's sample precision reweighted by that tier's share of the all-tier")
    print("panel, using the FROZEN shares (see TIER_SHARES_2026_07_27). The raw sample")
    print("mean above is not a panel estimate: weak tiers are oversampled ~30-300x.")
    print("This describes the panels as they were BEFORE the tier switch.")
    print(f"\n  {'panel':<16}{'donors':>10}   " + "".join(f"{t[:14]:>16}" for t in TIERS)
          + f"{'weighted':>11}{'bound':>9}")
    grand_num = grand_bnd = grand_den = 0.0
    for state, panel in PANELS:
        w = shares[(state, panel)]
        num = bnd = wsum = 0.0
        cells = []
        for t in TIERS:
            c = by[("tp", state, panel, t)]
            p, _lo, _hi, judged = precision(c)
            share = w.get(t, 0.0)
            cells.append(f"{share*100:5.1f}%x{p:5.1f}%" if judged else f"{share*100:5.1f}%x  n/a")
            if judged:
                num += share * p
                bnd += share * bound(c)
                wsum += share
        wp = num / wsum if wsum else float("nan")
        wb = bnd / wsum if wsum else float("nan")
        n = sizes[(state, panel)]
        print(f"  {state + ' ' + panel:<16}{n:>10,}   "
              + "".join(f"{c:>16}" for c in cells) + f"{wp:10.1f}%{wb:8.1f}%")
        grand_num += wp * n
        grand_bnd += wb * n
        grand_den += n
    print(f"\n  Donor-weighted across all six panels: "
          f"precision {grand_num/grand_den:.1f}%, "
          f"bound (all unverifiable = wrong) {grand_bnd/grand_den:.1f}%")

    print("\n--- PER TIER x PANEL CELL COUNTS " + "-" * 63)
    print(f"  {'cell':<34}{'n':>5}{'Y':>6}{'NC':>5}{'NP':>5}{'U':>5}")
    for state, panel in PANELS:
        for t in TIERS:
            c = by[("tp", state, panel, t)]
            print(f"  {state + ' ' + panel + ' / ' + t:<34}"
                  f"{sum(c[k] for k in VALID):>5}{c['Y']:>6}{c['NC']:>5}"
                  f"{c['NP']:>5}{c['U']:>5}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
