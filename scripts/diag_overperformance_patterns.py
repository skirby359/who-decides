#!/usr/bin/env python3
"""Candidate-level over/underperformance leaderboard + factor patterns.

For every partisan general race in the default backtest grid (10 CDs + 49 LDs
x 2018-2024), this diagnostic measures how much the *Democratic nominee* beat or
missed the district's **neutral partisan baseline** -- the PVI + down-ballot-drag
``baseline_dem_pct`` from :func:`build_structural_forecast` -- and then looks for
patterns by correlating that overperformance against the measurable candidate-
level factors the forecast model already computes:

    overperformance = actual_dem_two_party_pct - baseline_dem_pct
        (positive = Democrat beat the district's fundamentals)

Factors examined: incumbency, open-seat geometry, candidate-quality score,
fundraising advantage (raw log2 D/R receipts), local trend, midterm.

This is the *quantitative* track. It deliberately measures overperformance vs.
the **neutral** baseline (NOT the full model prediction), so the factor analysis
can then ask "how much of the overperformance do these measurable factors
explain, and how much is left over?" -- the leftover being the residual that a
future messaging/issue-positioning analysis would target.

Run from the project root:

    python scripts/diag_overperformance_patterns.py

Like ``scripts/backtest_model.py``, this first (re)populates the *derived*
``district_historical_performance`` cache from election results
(``compute_presidential_performance_statewide`` +
``compute_district_historical_from_results``) so PVI baselines are real per
district rather than falling back to a flat default. That is an idempotent
recompute of a cache table -- it does not touch raw results. Cells whose PVI
still has no presidential cycle behind it (no district presidential data) are
excluded from the leaderboard and the correlations, and the excluded count is
reported.

Optional flags:
    --top N        rows to show in each leaderboard half (default 18)
    --csv PATH     also dump the full candidate-cell frame to CSV
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

# --- path setup (mirror scripts/backtest_model.py) ---
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "scripts"))

import duckdb  # noqa: E402

from config.districts import get_profile  # noqa: E402
from wa_analyzer.db import get_connection  # noqa: E402
from wa_analyzer.analysis import national_model as _nm  # noqa: E402
from wa_analyzer.analysis.national_model import (  # noqa: E402
    build_structural_forecast,
    compute_district_historical_from_results,
    compute_presidential_performance_statewide,
    _name_tokens,
)

# Insulate the OVERPERFORMANCE/RESIDUAL artifact from forecast-layer changes.
# The residual is "actual − neutral baseline, after the flat *structural*
# factors (incumbency, quality, trend, money)". The personal-vote carryover
# (v-jun4-model) REPLACES the flat incumbency with a term derived from the
# candidate's PRIOR overperformance — feeding that back here would (a) mislabel
# D-incumbents (the incumbency_advantage_dem key disappears) and (b) be circular
# (it would "explain" the very cross-cycle persistence this analysis measures).
# So we disable it for the diagnostic, keeping the residual definition stable and
# comparable across model versions.
_nm._PERSONAL_VOTE_ENABLED = False

# Reuse the backtest's cell enumeration + actual-result extraction verbatim so
# the universe and race-selection logic stay in one place.
from backtest_model import (  # noqa: E402
    DEFAULT_DISTRICTS,
    DEFAULT_CYCLES,
    query_actual_results,
    get_national_env_for_cycle,
)

DB_PATH = str(project_root / "data" / "wa_statewide.duckdb")

# Spokane / Eastern-WA legislative districts that overlap CD5 (LD 3,4,6,7,9).
# Used for the CD5 zoom; CD5 itself is added separately.
EASTERN_WA_LDS = ["ld03", "ld04", "ld06", "ld07", "ld09"]

# Finance office codes we trust for matching candidate receipts (congressional
# + state-legislative). Excludes the large office=NULL statewide-contribution
# stub bucket and local/county offices.
_FINANCE_OFFICES = ("H", "S", "SR", "SS")


# ---------------------------------------------------------------------------
# Small stats helpers (no numpy dependency)
# ---------------------------------------------------------------------------

def pearson(xs: list[float], ys: list[float]) -> float | None:
    """Pearson correlation; None if < 3 points or zero variance."""
    pairs = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    n = len(pairs)
    if n < 3:
        return None
    mx = sum(p[0] for p in pairs) / n
    my = sum(p[1] for p in pairs) / n
    sxy = sum((p[0] - mx) * (p[1] - my) for p in pairs)
    sxx = sum((p[0] - mx) ** 2 for p in pairs)
    syy = sum((p[1] - my) ** 2 for p in pairs)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def stdev(xs: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


# ---------------------------------------------------------------------------
# The "unexplained signal": residual of overperformance after the measurable
# factors. We regress overperformance on [incumbency, candidate_quality,
# local_trend, fundraising] and take the residual. A large |residual| = a race
# that did much better/worse than money + incumbency + quality + trend can
# account for -> a hidden, currently-unmeasured factor (candidate fit, messaging,
# scandal, local dynamics) -- exactly what Track 2 would explain.
#
# Finance (PDC) is missing for ~1/3 of cells, almost all legislative. Rather than
# drop those cells, we use the standard MISSING-INDICATOR method so every cell
# gets a residual:
#   - fin_value     = fin_log2_dr where known, else 0
#   - finance_known = 1 where both-side finance known, else 0 (a dummy that
#                     absorbs the level difference between the two groups)
# fin_value is identified only from finance-known cells (it has no variance in
# the unknown group). Cells where real finance entered are flagged
# finance_controlled=True; for the others the residual does NOT control for that
# race's own (unknown) money, so a big residual there could still be a money story.
# ---------------------------------------------------------------------------

_RESID_FEATURES = ["inc_signed", "candidate_quality", "local_trend",
                   "fin_value", "finance_known"]


def fit_unexplained_residuals(rows: list[dict]) -> tuple[dict, float, int, int]:
    """Attach 'expected_from_factors', 'unexplained_residual', and
    'finance_controlled' to ALL rows via a unified missing-indicator OLS.
    Returns (coef dict, R^2, n_fit, n_finance_controlled)."""
    import numpy as np

    for r in rows:
        known = r["fin_log2_dr"] is not None
        r["finance_controlled"] = known
        r["_fin_value"] = float(r["fin_log2_dr"]) if known else 0.0
        r["_finance_known"] = 1.0 if known else 0.0

    def _feat(r: dict, name: str) -> float:
        if name == "fin_value":
            return r["_fin_value"]
        if name == "finance_known":
            return r["_finance_known"]
        return float(r[name])

    X = np.array([[1.0] + [_feat(r, f) for f in _RESID_FEATURES] for r in rows])
    y = np.array([float(r["overperformance"]) for r in rows])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ beta
    resid = y - pred
    ss_res = float(((y - pred) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    for r, p, e in zip(rows, pred, resid):
        r["expected_from_factors"] = round(float(p), 2)
        r["unexplained_residual"] = round(float(e), 2)
        del r["_fin_value"], r["_finance_known"]

    coef = {"intercept": round(float(beta[0]), 3)}
    for name, b in zip(_RESID_FEATURES, beta[1:]):
        coef[name] = round(float(b), 3)
    n_controlled = sum(1 for r in rows if r["finance_controlled"])
    return coef, r2, len(rows), n_controlled


def print_unexplained(rows: list[dict], top: int) -> None:
    coef, r2, n_fit, n_ctrl = fit_unexplained_residuals(rows)
    print("\n" + "=" * 100)
    print("UNEXPLAINED SIGNAL  (residual after the measurable factors)")
    print("=" * 100)
    print(f"\nOLS: overperformance ~ incumbency + candidate_quality + local_trend "
          f"+ fundraising + finance_known")
    print(f"  fit on ALL n={n_fit} cells (missing-indicator method; {n_ctrl} have "
          f"real both-side finance, {n_fit - n_ctrl} do not).")
    print(f"  R^2 = {r2:.2f}  -> the factors explain ~{r2*100:.0f}% of the spread; "
          f"the rest is the 'unexplained_residual' column (the hidden factor).")
    print(f"  coefficients: {coef}")

    scored = [r for r in rows if r.get("unexplained_residual") is not None]
    scored.sort(key=lambda r: r["unexplained_residual"], reverse=True)
    resids = [r["unexplained_residual"] for r in scored]
    print(f"  residual std = {stdev(resids):.2f} pts (typical surprise once "
          f"money/incumbency/quality are removed)\n")

    def _line(r: dict) -> str:
        flag = " " if r["finance_controlled"] else "*"
        fin = f"{r['fin_log2_dr']:+.1f}" if r["fin_log2_dr"] is not None else " n/a"
        return (f"{r['unexplained_residual']:+6.1f}{flag} {r['district']:5s} {r['year']}  "
                f"{r['dem_candidate'][:24]:24s} "
                f"act {r['actual_dem_pct']:5.1f}  raw-over {r['overperformance']:+5.1f}  "
                f"factors-expect {r['expected_from_factors']:+5.1f}  "
                f"[{r['incumbency']:5s} Q{r['candidate_quality']:+.0f} fin{fin}]")

    hdr = ("  RESID   DIST  YEAR  DEM CANDIDATE             "
           "ACTUAL  RAW-OVER  FACTORS-EXPECT  [drivers]")
    print(f"--- TOP {top}: did MUCH BETTER than the factors predict "
          f"(positive hidden factor) ---")
    print(hdr)
    for r in scored[:top]:
        print(_line(r))
    print(f"\n--- BOTTOM {top}: did MUCH WORSE than the factors predict "
          f"(negative hidden factor) ---")
    print(hdr)
    for r in scored[-top:]:
        print(_line(r))
    print("\n  * = finance NOT controlled (no PDC receipts for >=1 side; residual "
          "is vs incumbency/quality/trend + a group offset only -- a large value")
    print("    here may still be a money story). Trust unflagged residuals most.")


# ---------------------------------------------------------------------------
# Finance lookup: preload (cycle, last, initial) -> max receipts
# ---------------------------------------------------------------------------

def load_finance_index(conn: duckdb.DuckDBPyConnection) -> dict[tuple, float]:
    """Map (cycle, last_name, first_initial) -> max total_receipts.

    Keyed on :func:`_name_tokens` so FEC ('LAST, FIRST') and PDC ('First Last')
    name formats both resolve to the same key as the precinct-result name.
    Takes the max across rows sharing a key (general filing dominates primary
    committee fragments).
    """
    placeholders = ",".join("?" for _ in _FINANCE_OFFICES)
    rows = conn.execute(
        f"""
        SELECT election_cycle, candidate_name, total_receipts
        FROM candidate_finance
        WHERE office IN ({placeholders})
          AND total_receipts IS NOT NULL
          AND total_receipts > 0
        """,
        list(_FINANCE_OFFICES),
    ).fetchall()
    idx: dict[tuple, float] = {}
    for cyc, name, receipts in rows:
        key = (int(cyc),) + _name_tokens(name)
        rec = float(receipts)
        if key not in idx or rec > idx[key]:
            idx[key] = rec
    return idx


def finance_for(idx: dict[tuple, float], year: int, cand_name: str) -> float | None:
    if not cand_name:
        return None
    return idx.get((int(year),) + _name_tokens(cand_name))


# ---------------------------------------------------------------------------
# Candidate-name lookup for a specific race
# ---------------------------------------------------------------------------

def top_candidates(
    conn: duckdb.DuckDBPyConnection, race_name: str, year: int,
) -> tuple[str | None, str | None]:
    """Return (top_dem_name, top_rep_name) by votes for a race in a year."""
    rows = conn.execute(
        """
        SELECT c.party_normalized, UPPER(c.candidate_name) AS cand, SUM(pr.votes) AS v
        FROM precinct_results pr
        JOIN candidates c ON c.candidate_id = pr.candidate_id
        JOIN races r ON r.race_id = pr.race_id
        JOIN elections e ON e.election_id = r.election_id
        WHERE r.race_name = ?
          AND e.election_type = 'general'
          AND YEAR(e.election_date) = ?
          AND c.party_normalized IN ('Democratic', 'Republican')
        GROUP BY 1, 2
        ORDER BY v DESC
        """,
        [race_name, year],
    ).fetchall()
    dem = next((n for p, n, _ in rows if p == "Democratic"), None)
    rep = next((n for p, n, _ in rows if p == "Republican"), None)
    return dem, rep


# ---------------------------------------------------------------------------
# Build the candidate-cell frame
# ---------------------------------------------------------------------------

def incumbency_status(adj: dict) -> str:
    """Classify a cell's incumbency geometry from the adjustments dict."""
    if adj.get("incumbency_advantage_dem", 0) > 0:
        return "D-INC"
    if adj.get("incumbency_advantage_rep", 0) < 0:
        return "R-INC"
    if adj.get("open_seat_penalty_dem_retired", 0) or adj.get(
        "open_seat_penalty_rep_retired", 0
    ):
        return "OPEN"
    return "NONE"


def prime_historical(conn: duckdb.DuckDBPyConnection) -> None:
    """Populate the derived district_historical_performance cache, exactly as
    scripts/backtest_model.py does, so PVI baselines are real per district."""
    compute_presidential_performance_statewide(conn)
    for did in DEFAULT_DISTRICTS:
        try:
            compute_district_historical_from_results(conn, profile=get_profile(did))
        except Exception:
            continue


def build_frame(conn: duckdb.DuckDBPyConnection) -> list[dict]:
    fin_idx = load_finance_index(conn)
    rows: list[dict] = []
    skipped = 0
    for did in DEFAULT_DISTRICTS:
        try:
            profile = get_profile(did)
        except Exception:
            continue
        for year in DEFAULT_CYCLES:
            actual = query_actual_results(conn, profile, year)
            if actual is None or not actual.get("contested"):
                continue
            try:
                fc = build_structural_forecast(
                    conn,
                    party="Democratic",
                    national_environment=get_national_env_for_cycle(year),
                    profile=profile,
                    target_year=year,
                )
            except Exception:
                skipped += 1
                continue

            baseline = fc.get("baseline_dem_pct")
            if baseline is None:
                skipped += 1
                continue
            pvi = fc.get("pvi") or {}
            pvi_cycles = len(pvi.get("presidential_cycles_used") or [])
            actual_dem = actual["dem_two_party_pct"]
            overperf = round(actual_dem - baseline, 2)

            dem_name, rep_name = top_candidates(conn, actual["race_name"], year)
            adj = fc.get("adjustments", {}) or {}

            d_rec = finance_for(fin_idx, year, dem_name)
            r_rec = finance_for(fin_idx, year, rep_name)
            fin_log2 = (
                round(math.log2(d_rec / r_rec), 2)
                if d_rec and r_rec and d_rec > 0 and r_rec > 0
                else None
            )

            inc_signed = (
                adj.get("incumbency_advantage_dem", 0)
                + adj.get("incumbency_advantage_rep", 0)
            )

            rows.append({
                "district": did,
                "year": year,
                "dem_candidate": dem_name or "?",
                "rep_candidate": rep_name or "?",
                "actual_dem_pct": round(actual_dem, 2),
                "baseline_dem_pct": round(baseline, 2),
                "overperformance": overperf,
                "pvi_cycles": pvi_cycles,
                "baseline_ok": pvi_cycles >= 1,
                "two_party_votes": actual["dem_votes"] + actual["rep_votes"],
                "incumbency": incumbency_status(adj),
                "inc_signed": round(inc_signed, 2),
                "candidate_quality": round(adj.get("candidate_quality", 0.0), 2),
                "local_trend": round(adj.get("local_trend", 0.0), 2),
                "fin_log2_dr": fin_log2,
                "d_receipts": d_rec,
                "r_receipts": r_rec,
                "is_midterm": 1 if year % 4 == 2 else 0,
            })
    if skipped:
        print(f"[note] {skipped} cells skipped (no forecast/baseline available)\n")
    return rows


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def _fmt_row(r: dict) -> str:
    fin = f"{r['fin_log2_dr']:+.2f}" if r["fin_log2_dr"] is not None else "  n/a"
    return (
        f"{r['overperformance']:+6.1f}  {r['district']:5s} {r['year']}  "
        f"{r['dem_candidate'][:24]:24s} "
        f"act {r['actual_dem_pct']:5.1f} / base {r['baseline_dem_pct']:5.1f}  "
        f"{r['incumbency']:5s}  Q{r['candidate_quality']:+.1f}  "
        f"trend{r['local_trend']:+.1f}  fin$ {fin}"
    )


def print_leaderboard(rows: list[dict], top: int) -> None:
    ordered = sorted(rows, key=lambda r: r["overperformance"], reverse=True)
    header = (
        "  OVER   DIST  YEAR  DEM CANDIDATE             "
        "ACTUAL / BASELINE   INCUMB  QUAL   TREND   FIN(log2 D/R)"
    )
    print("=" * 100)
    print(f"STATEWIDE LEADERBOARD  ({len(rows)} contested candidate-cells, 2018-2024)")
    print("  overperformance = actual D two-party % minus neutral PVI+drag baseline")
    print("=" * 100)
    print(f"\n--- TOP {top} OVERPERFORMERS (Democrat beat the fundamentals) ---")
    print(header)
    for r in ordered[:top]:
        print(_fmt_row(r))
    print(f"\n--- BOTTOM {top} (Democrat underperformed the fundamentals) ---")
    print(header)
    for r in ordered[-top:]:
        print(_fmt_row(r))


def print_factor_analysis(rows: list[dict]) -> None:
    print("\n" + "=" * 100)
    print("FACTOR PATTERNS  (what tracks overperformance?)")
    print("=" * 100)

    op = [r["overperformance"] for r in rows]
    print(f"\nOverall: n={len(rows)}  mean overperf={mean(op):+.2f}  "
          f"std={stdev(op):.2f}  (std = how much candidates scatter around baseline)")

    # --- Pearson correlations vs continuous/ordinal factors ---
    print("\nPearson correlation of overperformance with each factor:")
    feats = {
        "incumbency (signed adj)": [r["inc_signed"] for r in rows],
        "candidate_quality score": [r["candidate_quality"] for r in rows],
        "local_trend": [r["local_trend"] for r in rows],
        "midterm (0/1)": [float(r["is_midterm"]) for r in rows],
    }
    for label, xs in feats.items():
        c = pearson(xs, op)
        print(f"  {label:26s}: r = {c:+.3f}" if c is not None else f"  {label:26s}: n/a")

    # finance correlation only over cells where both receipts known
    fin_pairs = [(r["fin_log2_dr"], r["overperformance"])
                 for r in rows if r["fin_log2_dr"] is not None]
    c = pearson([p[0] for p in fin_pairs], [p[1] for p in fin_pairs])
    print(f"  {'fundraising log2(D/R)':26s}: r = "
          + (f"{c:+.3f}  (n={len(fin_pairs)} with both filings)"
             if c is not None else "n/a"))

    # --- Grouped means by incumbency geometry ---
    print("\nMean overperformance by incumbency geometry:")
    for status in ["D-INC", "R-INC", "OPEN", "NONE"]:
        grp = [r["overperformance"] for r in rows if r["incumbency"] == status]
        if grp:
            print(f"  {status:6s}: n={len(grp):3d}  mean={mean(grp):+6.2f}  "
                  f"std={stdev(grp):5.2f}")

    # --- Grouped means by fundraising advantage bucket ---
    print("\nMean overperformance by fundraising position:")
    buckets = {"D out-raised R (>+1 log2)": [], "roughly even (-1..+1)": [],
               "R out-raised D (<-1 log2)": []}
    for r in rows:
        f = r["fin_log2_dr"]
        if f is None:
            continue
        if f > 1:
            buckets["D out-raised R (>+1 log2)"].append(r["overperformance"])
        elif f < -1:
            buckets["R out-raised D (<-1 log2)"].append(r["overperformance"])
        else:
            buckets["roughly even (-1..+1)"].append(r["overperformance"])
    for label, grp in buckets.items():
        if grp:
            print(f"  {label:28s}: n={len(grp):3d}  mean={mean(grp):+6.2f}")

    # --- The residual that messaging could target ---
    # Open seats with no incumbency edge are the cells most like Conroy 2024.
    challenger_like = [r["overperformance"] for r in rows
                       if r["incumbency"] in ("OPEN", "NONE")]
    print("\nResidual spread among open-seat / no-incumbent cells "
          "(the 'messaging-explainable' subset):")
    if challenger_like:
        print(f"  n={len(challenger_like)}  mean={mean(challenger_like):+.2f}  "
              f"std={stdev(challenger_like):.2f}")
        print("  -> this scatter is NOT explained by incumbency and is only "
              "partly explained by money;")
        print("     it is the slice a candidate-messaging analysis (Track 2) "
              "would try to explain.")


def print_cd5_zoom(rows: list[dict], top: int) -> None:
    print("\n" + "=" * 100)
    print("CD5 / EASTERN-WA ZOOM  (CD5 + Spokane-region LDs 3,4,6,7,9)")
    print("=" * 100)
    region = ["cd05"] + EASTERN_WA_LDS
    sub = [r for r in rows if r["district"] in region]
    ordered = sorted(sub, key=lambda r: r["overperformance"], reverse=True)
    header = (
        "  OVER   DIST  YEAR  DEM CANDIDATE             "
        "ACTUAL / BASELINE   INCUMB  QUAL   TREND   FIN(log2 D/R)"
    )
    print(f"\n{len(sub)} contested cells in the region:")
    print(header)
    for r in ordered:
        marker = "  <- Conroy" if (r["district"] == "cd05" and r["year"] == 2024) else ""
        print(_fmt_row(r) + marker)

    cd5 = sorted([r for r in sub if r["district"] == "cd05"], key=lambda r: r["year"])
    if cd5:
        print("\nCD5 Democrats over time (vs neutral baseline):")
        for r in cd5:
            print(f"  {r['year']}  {r['dem_candidate'][:26]:26s} "
                  f"overperf {r['overperformance']:+5.1f}  ({r['incumbency']})")
        op = [r["overperformance"] for r in cd5]
        print(f"  CD5 mean overperf: {mean(op):+.2f}  "
              f"(all open/non-incumbent challengers -- no D ever held this seat in window)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--top", type=int, default=18,
                    help="rows per leaderboard half (default 18)")
    ap.add_argument("--csv", type=str, default=None,
                    help="optional path to dump the full candidate-cell frame")
    args = ap.parse_args()

    import logging
    # Quiet the expected per-cell PVI/elasticity fallback chatter.
    logging.getLogger("wa_analyzer").setLevel(logging.ERROR)

    conn = get_connection()
    try:
        print("Populating district historical performance "
              "(derived cache, idempotent)...")
        prime_historical(conn)
        all_rows = build_frame(conn)
    finally:
        conn.close()

    if not all_rows:
        print("No contested candidate-cells found.")
        return

    # Keep only cells with a real PVI baseline; exclude default-baseline cells.
    rows = [r for r in all_rows if r["baseline_ok"]]
    excluded = len(all_rows) - len(rows)
    if excluded:
        print(f"[note] {excluded} cells excluded (no district presidential "
              f"data -> baseline fell back to a default; not comparable)\n")

    print_leaderboard(rows, args.top)
    print_factor_analysis(rows)
    print_unexplained(rows, args.top)
    print_cd5_zoom(rows, args.top)

    if args.csv:
        import csv as _csv
        cols: list[str] = []
        for r in all_rows:
            for k in r:
                if k not in cols:
                    cols.append(k)
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            w = _csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(all_rows)
        print(f"\n[wrote {len(all_rows)} rows ({len(rows)} baseline-ok) to {args.csv}]")


if __name__ == "__main__":
    main()
