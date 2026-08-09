"""Does money move votes? Independent expenditure (IE) advantage vs the model residual.

White-paper Finding 6 ("Does Money Move Votes in Washington?"). The design the
finding calls for: for FEC-attributed races (Schedule E carries support/oppose +
district), regress the *fundamentals-net residual* (actual_dem_pct − model
predicted_dem_pct, NOT the raw margin) on the net pro-Dem IE advantage. The
residual is used instead of the raw margin so the fundamentals the model already
captures (PVI, incumbency, the national wave) are partialled out — what's left is
the slice IE could plausibly have "moved."

  residual_pp           = actual_dem_pct − model_predicted_dem_pct   (per race)
  net_pro_dem_IE_$M     = (pro-Dem support + anti-Rep oppose)
                          − (pro-Rep support + anti-Dem oppose)      (per race)

A real vote-moving effect would show a POSITIVE slope (Dems beat their
fundamentals where pro-Dem IE outspent pro-Rep IE). The honest expectation, per
Jacobson (spending is endogenous to expected closeness) and Kalla & Broockman
(general-election persuasion ≈ 0), is a near-null the data cannot distinguish
from zero.

SCOPE: this script covers the FEDERAL panel only — WA U.S. House races, party
and direction from FEC Schedule E. The state-legislative counterpart is
``diag_pdc_ie_vs_margin.py``, which runs the same design on 129 district-cycles
built from the PDC's C6.3 filings.

**A "DATA CEILING" claim that used to live here was WITHDRAWN 2026-08-09.** This
docstring asserted that PDC state-legislative IE "has support_oppose = NULL for
every row, so it carries NO pro-D/pro-R direction and cannot enter a directional
test at all", and two papers cited that as a fact about Washington's disclosure
regime. It was a fact about our ETL. The PDC publishes direction in the **C6.3
"Identified Entities"** section of form C-6 — 4,653 legislative rows,
$51,723,243.45, direction on 100% of them — in the same dataset the loader was
already reading; the loader consumed only the C6.2 itemized section. See
docs/pdc-c6-direction-audit.md.

The narrower thing that remains true is worth keeping: ``support_oppose`` on
``independent_expenditures`` IS empty for PDC rows, because direction lives in
``pdc_ie_targets`` instead — a C6.3 target is one-to-many against an expenditure
and cannot share that table's primary key.

The inference block auto-expands: with n >= MIN_N_FOR_SLOPE scorable cells it
reports a bootstrap CI, and below that it withholds inference and prints a
descriptive slope clearly labelled as such.

Reproducible, public-record inputs only (FEC Schedule E + FEC candidate party).
No PII, no voter file. See docs/electoral-health-whitepaper.md Finding 6 and
docs/data-sources-and-reproducibility.md.
"""
import json
import math
import os
import sys
import tempfile

import duckdb

# Windows consoles default to cp1252, which chokes on the typographic chars
# below; force UTF-8 so the report renders identically everywhere.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001  (older interpreters / redirected streams)
    pass

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _ROOT)                       # repo root: config/ lives here
sys.path.insert(0, os.path.dirname(__file__))   # scripts/: backtest_model

from config.districts import get_profile  # noqa: E402

# --- PUBLIC ADAPTATION -------------------------------------------------------------------
# The private script imports assert_ie_classified from wa_analyzer.db; that package is not
# published, so the guard is inlined here. It is the SAME check: FEC IE rows loaded before the
# 2026-08-08 notice/periodic split carry is_notice IS NULL, are excluded by
# v_independent_expenditures, and would silently yield $0.0M rather than an inflated total.
# Stopping is safer than reporting a number nobody measured.
class StaleIEData(RuntimeError):
    pass


def assert_ie_classified(conn) -> None:
    cols = {r[1] for r in conn.execute("PRAGMA table_info('independent_expenditures')").fetchall()}
    predicate = "is_notice IS NULL" if "is_notice" in cols else "TRUE"
    stale = conn.execute(f"""
        SELECT state, office, district, election_cycle, COUNT(*)
        FROM independent_expenditures
        WHERE COALESCE(source,'') NOT ILIKE 'PDC%' AND {predicate}
        GROUP BY 1,2,3,4 ORDER BY 5 DESC""").fetchall()
    if stale:
        raise StaleIEData(
            "FEC independent-expenditure rows on disk predate the notice/periodic split, so "
            "they are excluded from every total and no IE figure here is measurable. Re-load "
            "per cycle with --fec-ie-replace. Groups affected: "
            + "; ".join(f"{s} {o}-{d} cycle {c}: {n:,} rows" for s, o, d, c, n in stale))

MIN_N_FOR_SLOPE = 10  # below this, inference is withheld (descriptive only)
DB = "data/wa_statewide.duckdb"


# Rows loaded before 2026-08-08 carry `is_notice IS NULL` — the loader could not
# tell a 24/48-hour notice from the periodic Schedule E row restating it, and
# stored both, inflating affected totals ~2x (WA-03 2024 read $40.08M against
# FEC's own $18.3M). They cannot be reclassified in place. Shared with the two
# paper verifiers so there is one definition of "stale".


def net_ie_by_race(conn):
    """Per (cycle, district) directional IE for WA U.S. House, party from FEC.

    Returns rows: (cycle, district_num, pro_dem_$, pro_rep_$, total_$, unmatched_$).
    pro_dem = pro-Dem support + anti-Rep oppose; pro_rep is the mirror. Party is
    resolved by joining the IE candidate name to candidate_finance (FEC carries
    party for federal candidates). Dedup on ie_id (the loader stores S/O pairs).

    Reads ``v_independent_expenditures``, NOT the base table: the base table
    retains FEC's 24/48-hour notice rows, which restate the same expenditures
    that appear on the periodic Schedule E and would double every total here.
    Guarded by ``assert_ie_classified`` at the call site rather than left to
    whoever edits this query next.
    """
    q = """
    WITH ie AS (
        SELECT DISTINCT ie_id, election_cycle, district, candidate_name,
               support_oppose, expenditure_amount
        FROM v_independent_expenditures
        WHERE source = 'FEC' AND office = 'H' AND state = 'WA'
          AND support_oppose IN ('S', 'O')
    ),
    party AS (
        SELECT DISTINCT election_cycle, UPPER(candidate_name) AS cn, party
        FROM candidate_finance
        WHERE state = 'WA' AND office = 'H'
          AND party IN ('Democratic', 'Republican')
    )
    SELECT ie.election_cycle, ie.district,
        SUM(CASE WHEN (p.party='Democratic' AND support_oppose='S')
                   OR (p.party='Republican' AND support_oppose='O')
                 THEN expenditure_amount ELSE 0 END)                      AS pro_dem,
        SUM(CASE WHEN (p.party='Republican' AND support_oppose='S')
                   OR (p.party='Democratic' AND support_oppose='O')
                 THEN expenditure_amount ELSE 0 END)                      AS pro_rep,
        SUM(expenditure_amount)                                           AS total_amt,
        SUM(CASE WHEN p.party IS NULL THEN expenditure_amount ELSE 0 END) AS unmatched_amt
    FROM ie
    LEFT JOIN party p
      ON ie.election_cycle = p.election_cycle AND UPPER(ie.candidate_name) = p.cn
    GROUP BY 1, 2
    ORDER BY 1, 2
    """
    out = []
    for cyc, dist, pd_, pr_, tot, unm in conn.execute(q).fetchall():
        if not str(dist).isdigit():
            continue
        out.append({
            "cycle": int(cyc),
            "district_num": int(dist),
            "district_id": f"cd{int(dist):02d}",
            "pro_dem": float(pd_ or 0),
            "pro_rep": float(pr_ or 0),
            "total": float(tot or 0),
            "unmatched": float(unm or 0),
            "net_pro_dem_m": (float(pd_ or 0) - float(pr_ or 0)) / 1e6,
            "total_m": float(tot or 0) / 1e6,
        })
    return out


def model_residual(conn, district_id, year):
    """fundamentals-net residual = actual_dem_pct − model predicted_dem_pct.

    Uses the canonical backtest forecast (single source of truth). Returns None
    for cells with no scorable actual (uncontested / future cycle / no PVI).
    """
    from backtest_model import run_single_backtest
    try:
        r = run_single_backtest(conn, get_profile(district_id), year, "Democratic")
    except Exception as e:  # noqa: BLE001
        return None, f"forecast error: {e}"
    if r.get("skipped"):
        return None, r.get("skip_reason", "skipped")
    if "actual_dem_pct" not in r or "predicted_dem_pct" not in r:
        return None, "no actual (unscorable)"
    resid = float(r["actual_dem_pct"]) - float(r["predicted_dem_pct"])
    return {
        "residual_pp": round(resid, 2),
        "actual_dem_pct": float(r["actual_dem_pct"]),
        "predicted_dem_pct": float(r["predicted_dem_pct"]),
        "actual_margin": float(r["actual_margin"]),
    }, None


def ols_slope(xs, ys):
    """Simple OLS slope/intercept/Pearson r for y ~ x."""
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return 0.0, my, 0.0
    slope = sxy / sxx
    r = sxy / math.sqrt(sxx * syy)
    return slope, my - slope * mx, r


def bootstrap_slope_ci(xs, ys, iters=5000, seed=12345):
    """Percentile bootstrap CI for the OLS slope. Deterministic (fixed seed)."""
    import random
    rng = random.Random(seed)
    n = len(xs)
    slopes = []
    idx = list(range(n))
    for _ in range(iters):
        samp = [rng.choice(idx) for _ in range(n)]
        bx = [xs[i] for i in samp]
        by = [ys[i] for i in samp]
        s, _, _ = ols_slope(bx, by)
        slopes.append(s)
    slopes.sort()
    lo = slopes[int(0.025 * iters)]
    hi = slopes[int(0.975 * iters)]
    return lo, hi


def main():
    conn = duckdb.connect(DB, read_only=True)

    assert_ie_classified(conn)
    races = net_ie_by_race(conn)
    cycles = sorted({r["cycle"] for r in races})
    print("=" * 78)
    print("Finding 6 — Does money move votes? Net IE advantage vs model residual")
    print("=" * 78)
    print(f"Directional FEC Schedule-E IE on disk covers cycles: {cycles or '(none)'}")
    print(f"WA House district-cycles with directional IE: {len(races)}\n")

    # Attach the model residual to each race that has a scorable actual.
    rows = []
    for r in races:
        resid, why = model_residual(conn, r["district_id"], r["cycle"])
        if resid is None:
            r["residual_pp"] = None
            r["skip"] = why
        else:
            r.update(resid)
            r["skip"] = None
        rows.append(r)
    conn.close()

    scored = [r for r in rows if r.get("residual_pp") is not None]

    hdr = (f"{'race':>10} | {'net pro-D IE':>12} | {'total IE':>9} | "
           f"{'unmatched':>9} | {'resid pp':>8} | {'act margin':>10}")
    print(hdr)
    print("-" * len(hdr))
    for r in sorted(rows, key=lambda x: (x["cycle"], x["district_num"])):
        tag = f"{r['district_id']}/{str(r['cycle'])[2:]}"
        if r.get("residual_pp") is None:
            print(f"{tag:>10} | {r['net_pro_dem_m']:>+10.2f}M | {r['total_m']:>7.2f}M | "
                  f"{r['unmatched']/1e6:>7.2f}M | {'—':>8} | {'(' + (r['skip'] or '') + ')'}")
        else:
            print(f"{tag:>10} | {r['net_pro_dem_m']:>+10.2f}M | {r['total_m']:>7.2f}M | "
                  f"{r['unmatched']/1e6:>7.2f}M | {r['residual_pp']:>+8.2f} | {r['actual_margin']:>+10.2f}")

    unmatched_total = sum(r["unmatched"] for r in rows)
    total_ie = sum(r["total"] for r in rows)
    print(f"\nUnmatched-to-party IE (party not resolvable): "
          f"${unmatched_total/1e6:.2f}M of ${total_ie/1e6:.2f}M "
          f"({unmatched_total/total_ie*100 if total_ie else 0:.1f}%)")

    # ---- Inference, only if the data can bear it -------------------------
    print("\n" + "-" * 78)
    n = len(scored)
    if n < MIN_N_FOR_SLOPE:
        print(f"INFERENCE WITHHELD — only {n} scorable race(s) "
              f"(threshold {MIN_N_FOR_SLOPE}).")
        print("  Directional IE is loaded for a SINGLE cycle (2024 FEC Schedule-E).")
        print("  With one cross-section of ~7 races and no exogenous variation, the")
        print("  bootstrap CI, the early-vs-late-IE split, and the next-cycle placebo")
        print("  the finding calls for are not estimable. A descriptive slope on n<10")
        print("  would be a coin-flip dressed as a coefficient — so it is not reported.")
        # Still show the raw sign of the association, clearly labeled as descriptive.
        if n >= 3:
            xs = [r["net_pro_dem_m"] for r in scored]
            ys = [r["residual_pp"] for r in scored]
            slope, _, rho = ols_slope(xs, ys)
            print(f"\n  [DESCRIPTIVE ONLY, NOT INFERENTIAL] n={n}: "
                  f"slope {slope:+.2f} pp per $1M net pro-Dem IE, Pearson r={rho:+.2f}.")
            print("  Interpret as a picture of these specific races, not an estimate of any")
            print("  population effect. Sign can flip on a single race at this n.")
        result = {"inference": "withheld", "n_scored": n, "cycles": cycles}
    else:
        xs = [r["net_pro_dem_m"] for r in scored]
        ys = [r["residual_pp"] for r in scored]
        slope, intercept, rho = ols_slope(xs, ys)
        lo, hi = bootstrap_slope_ci(xs, ys)
        crosses_zero = lo <= 0 <= hi
        print(f"OLS  residual_pp ~ net_pro_dem_IE_$M   (n={n})")
        print(f"  slope    = {slope:+.3f} pp per $1M net pro-Dem IE")
        print(f"  95% boot = [{lo:+.3f}, {hi:+.3f}]  "
              f"{'(crosses 0 — cannot reject no effect)' if crosses_zero else '(excludes 0)'}")
        print(f"  Pearson r= {rho:+.3f}")
        print("  NOTE: a positive slope is NOT causal without an instrument — IE is")
        print("  endogenous to expected closeness (Jacobson). Treat as upper-bound-ish.")
        result = {"inference": "reported", "n_scored": n, "cycles": cycles,
                  "slope": slope, "ci": [lo, hi], "pearson_r": rho,
                  "crosses_zero": crosses_zero}

    # ---- Data-availability ceiling (the citable finding) ------------------
    #
    # DERIVED, not narrated. These bullets were hardcoded literals asserting
    # "2024 only (~7 WA House races)" — and they went on printing that sentence
    # verbatim after the 2018/2020/2022 backfill landed, under a table showing
    # four cycles. A script that states its own data inventory in a string
    # cannot notice when the inventory changes, which is the same defect the
    # paper verifiers exist to catch in prose.
    print("\n" + "=" * 78)
    print("DATA INVENTORY (derived from the rows actually on disk):")
    cyc_list = ", ".join(str(c) for c in cycles) or "(none)"
    print(f"  • Directional FEC Schedule-E covers {len(cycles)} cycle(s): {cyc_list}")
    print(f"    across {len(races)} district-cycles, {n} of them scorable.")
    print("  • PDC state-legislative IE carries direction in form C-6 section C6.3,")
    print("    loaded into `pdc_ie_targets` (4,653 legislative rows / $51.72M,")
    print("    2018-2024). It is NOT on independent_expenditures.support_oppose,")
    print("    because a C6.3 target is one-to-many against an expenditure. Run the")
    print("    state-legislative panel with scripts/diag_pdc_ie_vs_margin.py.")
    if n < MIN_N_FOR_SLOPE:
        print(f"  • UNLOCK: n={n} is below the {MIN_N_FOR_SLOPE}-observation floor for")
        print("    inference. Backfill more cycles —")
        print("      python main.py load --fec-ie --statewide --fec-ie-cycle YYYY \\")
        print("             --fec-ie-replace")
        print("    Runtime is minutes, not hours; it was never the constraint. The")
        print("    thing to get right is the notice/periodic de-duplication.")
    print("  • Verify any of this WITHOUT an API key via")
    print("    scripts/diag_fec_ie_bulk_crosscheck.py, which reconciles the loaded")
    print("    totals against FEC's public bulk files.")
    print("  • Sample stays uninstrumented whatever its size: with no exogenous")
    print("    variation these observations cannot identify a causal effect, only")
    print("    sharpen the descriptive picture.")

    out = os.path.join(tempfile.gettempdir(), "ie_vs_margin.json")
    json.dump({"races": rows, "result": result}, open(out, "w"), indent=2, default=str)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
