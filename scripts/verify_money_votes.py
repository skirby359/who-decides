"""Independent verification of docs/does-money-move-votes.md, asserted against its prose.

NEW 2026-08-01. This paper had no verifier of any kind. Its figures came from four
`diag_*.py` scripts and nothing checked that the paper still agreed with them — which, for a
paper heading to a null-results venue, is the wrong gap to have: the first question a referee
asks a null is whether it was computed correctly.

Building it found three defects on the first run, and the split between them is worth
keeping in mind when reading a failure here:

  * Five Finding 1 figures had gone stale because their frame is LIVE. The correlation is
    matched against `candidate_finance`, so loading more filings moves it: 109 both-side
    cells gave +0.55, 129 give +0.58. Fixed by pinning the frame (below).
  * "Directional IE exists on disk for exactly one cycle" was false when written — two
    cycles carried a support/oppose flag — and is obsolete now: a 2026-08-08 backfill took
    the panel to FIVE cycles and 34 scorable races, reversing the sign of Finding 2c's slope
    (−0.39 -> +0.515) without changing its verdict, because the interval still spans zero.
    Every numeric probe passed throughout, which is why `_claim_checks` exists: the sentence
    built on top of individually-correct figures is what went false.
  * "PDC IE carries a null support/oppose flag" was false in the absolute — 5 of 4,456 rows
    carry one, worth $14,212. Immaterial to the argument, and checkable, so it was checked.

WHAT IS RE-DERIVED HERE AND WHAT IS NOT. The split follows verify_whitepaper.py's precedent
and is deliberate.

  RE-DERIVED, from scratch in SQL over the warehouse, independent of every diag script:
  the data-ceiling facts that the paper itself calls its most citable result — the flagged-IE
  cycle inventory, WA-03's total and net independent expenditure, the PDC IE total and its
  flag coverage, and the itemised-expenditure universe with its coded/uncoded dollar split.

  ASSERTED AGAINST A PINNED FRAME: Finding 1's correlations and fundraising-position means.
  These need `overperformance`, which is the actual Democratic share minus a MODEL-derived
  baseline, so re-deriving them here would fork the forecast model rather than check it —
  and running the model costs five and a half minutes, which does not belong in a release
  gate. `docs/reference/overperformance_cells_2026-08-15.csv` freezes the 163-cell frame
  (re-pinned 2026-08-15 for the referee's district-scoped finance linkage — two cells'
  finance corrected, residuals refit from otherwise-pinned inputs);
  this script recomputes the statistics from it with DuckDB's own `corr`, which is at least
  an independent implementation of the statistics even though the cells are shared. The
  file's shape is asserted too, so a silently truncated or regenerated frame fails rather
  than quietly changing the answer.

  NOT CHECKED, with the reason recorded in UNCHECKED below rather than left implicit.

Read-only; aggregate output only. This paper touches no voter file — it is candidate- and
race-level throughout, which is also why nothing here needs the person-level guard the
who-decides verifiers carry.

Run:  python scripts/verify_money_votes.py [--coverage]
"""
from __future__ import annotations

import math
import random
import csv
import re
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _verify_prose as vp  # noqa: E402

vp.stdout_utf8()

PAPER = vp.DOCS / "does-money-move-votes.md"
# The OPEN cycle's inventory reading, pinned. Finding 3's table is the only place this paper
# reads a still-accruing source, and as of 2026-08-24 it accrues UNATTENDED: the scheduled task
# "WA FEC IE Weekly Refresh" (f91c03d, Mondays 09:00) writes independent_expenditures for the
# watched district. That moved three published cells with no human running a loader --
# 50 -> 69 rows, $98K -> $490K, and the panel totals with them. Deriving the 2026 row live is
# therefore a floating basis, the same defect the WA paper's Appendix A carried against
# MAX(report_date) until it was pinned on 2026-08-21.
CURRENT_CYCLE_PIN = vp.DOCS / "reference" / "fec_ie_current_cycle_pin.csv"
# The last CLOSED cycle. The panel totals count completed cycles only, which is what the
# analysis uses (34 scorable races, all of them 2018-2024) and what does not move. The open
# cycle is printed with its as-of date beside it and excluded from the total.
LAST_COMPLETED_CYCLE = 2024
CELLS = vp.DOCS / "reference" / "overperformance_cells_2026-08-15.csv"
ALLOC = vp.DOCS / "reference" / "expenditures_vs_residual_2026-08-15.csv"
# The state-legislative directional panel behind Finding 3, one row per
# (advocacy scope, specification, cycle, district). Same reasoning as CELLS: the
# residual needs the forecast model, and running it 191 times costs minutes that
# do not belong in a release gate. The file pins the CELLS, not the
# coefficients — the slopes below are recomputed from it here, so a paper figure
# that drifted from the panel fails rather than matching a stored answer.
# Regenerate: python scripts/diag_pdc_ie_vs_margin.py --cells-csv <this path>
PDCIE = vp.DOCS / "reference" / "pdc_ie_vs_residual_2026-08-15.csv"
# The federal IE panel (34 scorable House race-cycles). Until 2026-08-15 every figure from
# it was exempted as diagnostic-owned; the referee's influence and clustering findings are
# now derived HERE from the pin, so the paper's leverage and clustered-interval sentences
# are asserted rather than trusted.
IECELLS = vp.DOCS / "reference" / "ie_vs_residual_2026-08-09.csv"
# The retired frame, kept for audit: the pin note narrates its 129-cell +0.58 state and
# the linkage audit's two corrected lookups are DERIVED as the diff between the two pins.
CELLS_OLD = vp.DOCS / "reference" / "overperformance_cells_2026-08-01.csv"
# The pre-election receipts pin (2026-08-29): per-report FEC period totals for every
# congressional frame candidate, cut at the last coverage window ending on or before
# election day. Written by scripts/diag_receipts_preelection.py --fetch; Appendix C's
# cutoff sensitivity and Finding 1's pre-election sentence are derived from it.
PREPIN = vp.DOCS / "reference" / "fec_receipts_preelection_2026-08-29.csv"
# Committee-grain sibling with each committee's designation AS OF ITS CYCLE (2026-08-29,
# second referee pass): the primary cutoff figures are computed from THIS pin on the
# authorized universe (at-cycle P or A), because "everything linked except J" is too broad
# as a rule — it swept in one genuine at-cycle leadership PAC. The candidate-grain pin
# above remains the everything-but-J comparability basis the reconciliation checks.
CMTE_PIN = vp.DOCS / "reference" / "fec_receipts_preelection_committees_2026-08-29.csv"
_EDAY = {2018: "2018-11-06", 2020: "2020-11-03", 2022: "2022-11-08", 2024: "2024-11-05"}


def _cluster_boot(xs, ys, clusters, ols, iters=5000, seed=12345):
    """Percentile bootstrap over CLUSTERS (external referee 2026-08-15, item 5).

    Mirrors `cluster_bootstrap_slope_ci` in diag_ie_vs_margin.py — same seed, same
    tails — so the paper's clustered intervals are recomputed by an independent
    copy of the same scheme rather than read back from the diagnostic.
    """
    rng = random.Random(seed)
    groups: dict = {}
    for x, y, c in zip(xs, ys, clusters):
        groups.setdefault(c, []).append((x, y))
    keys = sorted(groups)
    out = []
    for _ in range(iters):
        bx, by = [], []
        for k in [rng.choice(keys) for _ in keys]:
            for x, y in groups[k]:
                bx.append(x)
                by.append(y)
        s = ols(bx, by)[0]
        if s == 0.0 and len(set(bx)) <= 1:
            continue
        out.append(s)
    out.sort()
    return out[int(0.025 * len(out))], out[int(0.975 * len(out))]

# PDC records an itemised expenditure with no purpose code as the literal string 'nan', not
# as NULL. Reading it as NULL makes the file look 100% coded and silently contradicts the
# paper's 62%/38% split — which is exactly what happened on the first attempt at this probe.
UNCODED = "(code IS NULL OR TRIM(code) = '' OR LOWER(TRIM(code)) = 'nan')"


def derive_finding1(d: dict) -> None:
    """Finding 1, recomputed from the pinned cell frame."""
    if not CELLS.exists():
        raise SystemExit(
            f"FATAL: pinned cell frame missing: {CELLS}\n"
            f"  Regenerate with (about 5m30s):\n"
            f"    PYTHONPATH=src python scripts/diag_overperformance_patterns.py --csv {CELLS}\n"
            f"  Regenerating it re-pins Finding 1 to a new basis; expect the paper's five "
            f"Finding 1 figures to move and update them deliberately, not silently.")
    con = duckdb.connect()
    src = f"read_csv_auto('{CELLS.as_posix()}', header=true)"
    # Frame shape, asserted so a truncated or re-derived file fails loudly.
    d["cells_total"], d["cells_scorable"] = con.execute(
        f"SELECT COUNT(*), COUNT(*) FILTER (WHERE baseline_ok) FROM {src}").fetchone()
    row = con.execute(f"""
        SELECT corr(overperformance, fin_log2_dr), corr(overperformance, inc_signed),
               corr(overperformance, candidate_quality), corr(overperformance, local_trend),
               corr(overperformance, is_midterm),
               COUNT(*) FILTER (WHERE fin_log2_dr IS NOT NULL)
        FROM {src} WHERE baseline_ok""").fetchone()
    (d["r_fin"], d["r_inc"], d["r_quality"], d["r_trend"], d["r_midterm"],
     d["fin_cells"]) = [float(x) if x is not None else None for x in row[:5]] + [int(row[5])]
    # Appendix C's "two different 129s" paragraph (full-paper coverage, 2026-08-14): the
    # 163-cell frame's legislative/congressional split. The OTHER 129 is the C6.3 panel's
    # cell count (leg_all_agg_n); the paragraph's whole point is that the two populations
    # are different, so both sides are derived and asserted.
    d["cells_leg"], d["cells_cong"] = con.execute(f"""
        SELECT COUNT(*) FILTER (WHERE district LIKE 'ld%'),
               COUNT(*) FILTER (WHERE district NOT LIKE 'ld%')
        FROM {src} WHERE baseline_ok""").fetchone()
    for grp, tag in (("fin_log2_dr > 1", "d_outraised"), ("fin_log2_dr < -1", "r_outraised"),
                     ("fin_log2_dr BETWEEN -1 AND 1", "even")):
        d[f"mean_{tag}"], = con.execute(
            f"SELECT AVG(overperformance) FROM {src} WHERE baseline_ok AND {grp}").fetchone()
    # The paper writes the R-out-raised mean as "−1.77", and the minus sign is prose rather
    # than part of the captured group. Compare magnitudes so the probe is not asserting a
    # positive number against a negative one — which reads as a defect and is a probe bug.
    d["mean_r_outraised_abs"] = abs(d["mean_r_outraised"])

    # ---- Referee item (6): the stratification, all from this same pinned frame ----
    # Two questions the pooled +0.60 cannot answer on its own. Whether it is a BETWEEN-group
    # artifact (congressional and legislative races raise on different scales, so pooling can
    # manufacture a correlation present in neither), and whether the 128 cells carrying a
    # ratio differ in the OUTCOME from the 35 that do not -- which decides what population
    # the headline describes.
    for tag, pred in (("cong", "district NOT LIKE 'ld%'"), ("leg", "district LIKE 'ld%'")):
        n, r = con.execute(
            f"SELECT COUNT(*), corr(overperformance, fin_log2_dr) FROM {src} "
            f"WHERE baseline_ok AND fin_log2_dr IS NOT NULL AND {pred}").fetchone()
        d[f"r_fin_{tag}"], d[f"n_fin_{tag}"] = float(r), int(n)
    for yr, r in con.execute(
            f"SELECT year, corr(overperformance, fin_log2_dr) FROM {src} "
            f"WHERE baseline_ok AND fin_log2_dr IS NOT NULL GROUP BY 1").fetchall():
        d[f"r_fin_{int(yr)}"] = float(r)
    # The partial correlation, and the overlap that makes it necessary. Computed from three
    # Pearson r's rather than by fitting, so it stays a property of the same frame.
    rxy, rxz, ryz = con.execute(
        f"SELECT corr(overperformance, fin_log2_dr), corr(fin_log2_dr, inc_signed), "
        f"corr(overperformance, inc_signed) FROM {src} "
        f"WHERE baseline_ok AND fin_log2_dr IS NOT NULL").fetchone()
    d["r_fin_inc_overlap"] = float(rxz)
    d["r_fin_full"] = float(rxy)
    d["r_fin_partial_inc"] = (rxy - rxz * ryz) / math.sqrt((1 - rxz ** 2) * (1 - ryz ** 2))
    # Why the 35 lack a ratio, and whether their absence is related to the outcome.
    d["fin_missing_d_only"], d["fin_missing_r_only"], d["fin_missing_neither"],         d["fin_missing_leg"] = con.execute(f"""
        SELECT COUNT(*) FILTER (WHERE COALESCE(d_receipts,0) > 0
                                  AND COALESCE(r_receipts,0) = 0),
               COUNT(*) FILTER (WHERE COALESCE(r_receipts,0) > 0
                                  AND COALESCE(d_receipts,0) = 0),
               COUNT(*) FILTER (WHERE COALESCE(d_receipts,0) = 0
                                  AND COALESCE(r_receipts,0) = 0),
               COUNT(*) FILTER (WHERE district LIKE 'ld%')
        FROM {src} WHERE baseline_ok AND fin_log2_dr IS NULL""").fetchone()
    d["mean_op_with_ratio"], d["mean_op_without_ratio"] = con.execute(
        f"SELECT AVG(overperformance) FILTER (WHERE fin_log2_dr IS NOT NULL), "
        f"AVG(overperformance) FILTER (WHERE fin_log2_dr IS NULL) "
        f"FROM {src} WHERE baseline_ok").fetchone()
    d["cells_no_ratio"] = d["cells_scorable"] - d["fin_cells"]
    con.close()


def derive_preelection(d: dict) -> None:
    """Appendix C's pre-election cutoff sensitivity (2026-08-29), from PREPIN + CELLS.

    Recomputes every correlation from the pin and the frame rather than trusting the diag's
    print. The state-legislative analogue re-resolves each cell's candidate_finance row by
    exact amount and sums dated itemized PDC rows in one scan — the same construction as
    scripts/diag_receipts_preelection.py, which owns the fetch and the full table.
    """
    if not PREPIN.exists() or not CMTE_PIN.exists():
        raise SystemExit(
            f"FATAL: pre-election receipts pin(s) missing: {PREPIN} / {CMTE_PIN}\n"
            f"  Regenerate with (network; needs FEC_API_KEY):\n"
            f"    python scripts/diag_receipts_preelection.py --fetch\n"
            f"  Re-fetching re-pins Appendix C's cutoff sensitivity; expect its figures to "
            f"move and update them deliberately.")
    con = duckdb.connect()
    cells = f"read_csv_auto('{CELLS.as_posix()}', header=true)"
    pin = f"read_csv_auto('{PREPIN.as_posix()}', header=true)"
    cpin = f"read_csv_auto('{CMTE_PIN.as_posix()}', header=true)"
    # The everything-but-J universe (candidate-grain pin): the comparability basis.
    row = con.execute(f"""
        WITH cong AS (SELECT district, year, overperformance, fin_log2_dr,
                             d_receipts, r_receipts
                      FROM {cells}
                      WHERE baseline_ok AND fin_log2_dr IS NOT NULL
                        AND district NOT LIKE 'ld%'),
        p AS (SELECT district, year,
                     MAX(CASE WHEN side='D' THEN pre_receipts END) dp,
                     MAX(CASE WHEN side='R' THEN pre_receipts END) rp,
                     MAX(CASE WHEN side='D' THEN full_receipts_reports END) df,
                     MAX(CASE WHEN side='R' THEN full_receipts_reports END) rf
              FROM {pin} GROUP BY 1, 2),
        j AS (SELECT c.*, p.dp, p.rp, p.df, p.rf FROM cong c JOIN p USING (district, year))
        SELECT COUNT(*),
               corr(overperformance, fin_log2_dr),
               corr(overperformance, log2(df/rf))   FILTER (WHERE df > 0 AND rf > 0),
               corr(overperformance, log2(dp/rp))   FILTER (WHERE dp > 0 AND rp > 0)
        FROM j""").fetchone()
    (d["pre_n_cong"], d["pre_r_cong_pinbasis"], d["nonj_full_r"],
     d["nonj_pre_r"]) = (int(row[0]), float(row[1]), float(row[2]), float(row[3]))
    # The AUTHORIZED universe (committee-grain pin, at-cycle designation P or A): the
    # primary basis the paper's figures state.
    row = con.execute(f"""
        WITH cong AS (SELECT district, year, overperformance FROM {cells}
                      WHERE baseline_ok AND fin_log2_dr IS NOT NULL
                        AND district NOT LIKE 'ld%'),
        a AS (SELECT district, year, side,
                     SUM(pre_receipts) pr, SUM(full_receipts_reports) fl
              FROM {cpin} WHERE designation_at_cycle IN ('P','A') GROUP BY 1, 2, 3),
        p AS (SELECT district, year,
                     MAX(CASE WHEN side='D' THEN pr END) dp,
                     MAX(CASE WHEN side='R' THEN pr END) rp,
                     MAX(CASE WHEN side='D' THEN fl END) df,
                     MAX(CASE WHEN side='R' THEN fl END) rf
              FROM a GROUP BY 1, 2),
        j AS (SELECT c.*, p.dp, p.rp, p.df, p.rf FROM cong c JOIN p USING (district, year))
        SELECT COUNT(*),
               corr(overperformance, log2(df/rf))   FILTER (WHERE df > 0 AND rf > 0),
               corr(overperformance, log2(dp/rp))   FILTER (WHERE dp > 0 AND rp > 0),
               COUNT(*) FILTER (WHERE dp > 0 AND rp > 0 AND df > 0 AND rf > 0)
        FROM j""").fetchone()
    (n_auth, d["fullrep_r_cong"], d["pre_r_cong"], d["pre_n_usable"]) = (
        int(row[0]), float(row[1]), float(row[2]), int(row[3]))
    if n_auth != d["pre_n_cong"]:
        raise SystemExit(
            f"FATAL: the authorized universe joins {n_auth} congressional cells against "
            f"{d['pre_n_cong']} on the candidate pin — the two pins have diverged; "
            f"re-run the --fetch.")
    # The validation counts and the excluded leadership PAC's cells, as the paper states them.
    d["cmte_rows_total"], d["cmte_rows_pa"] = [int(x) for x in con.execute(f"""
        SELECT COUNT(*), COUNT(*) FILTER (WHERE designation_at_cycle IN ('P','A'))
        FROM {cpin}""").fetchone()]
    flags = [float(x) for (x,) in con.execute(f"""
        SELECT full_receipts_reports FROM {cpin}
        WHERE designation_at_cycle NOT IN ('P','A') ORDER BY year""").fetchall()]
    if len(flags) != 3:
        raise SystemExit(
            f"FATAL: the paper enumerates THREE excluded committee-cycles; the pin holds "
            f"{len(flags)} — re-derive the committee-universe paragraph before trusting it.")
    d["flag_full_1"], d["flag_full_2"], d["flag_full_3"] = flags
    # Reconciliation of report-built full-cycle sums against the frame's summary totals,
    # per candidate-cycle, as a share of the frame value.
    d["pre_recon_mean_pct"], d["pre_recon_max_pct"] = [float(x) for x in con.execute(f"""
        WITH cong AS (SELECT district, year, d_receipts, r_receipts FROM {cells}
                      WHERE baseline_ok AND fin_log2_dr IS NOT NULL
                        AND district NOT LIKE 'ld%'),
        long AS (SELECT district, year, 'D' side, d_receipts amt FROM cong
                 UNION ALL SELECT district, year, 'R', r_receipts FROM cong),
        j AS (SELECT 100.0*ABS(p.full_receipts_reports - l.amt)/l.amt rel
              FROM {pin} p JOIN long l USING (district, year, side) WHERE l.amt > 0)
        SELECT AVG(rel), MAX(rel) FROM j""").fetchone()]
    con.close()
    # State-legislative itemized analogue: resolve each cell side by exact amount, then one
    # dated scan over the PDC rows.
    wcon = duckdb.connect(str(vp.DOCS.parent / "data" / "wa_statewide.duckdb"),
                          read_only=True)
    lcon = duckdb.connect()
    leg = lcon.execute(f"""
        SELECT district, year, overperformance, d_receipts, r_receipts FROM {cells}
        WHERE baseline_ok AND fin_log2_dr IS NOT NULL AND district LIKE 'ld%'""").fetchall()
    lcon.close()
    resolved: dict[tuple, str] = {}
    for dist, yr, _op, dr, rr in leg:
        bare = dist[2:].lstrip("0")
        for side, amt in (("D", float(dr)), ("R", float(rr))):
            hits = {r[0] for r in wcon.execute(
                "SELECT fec_candidate_id FROM candidate_finance "
                "WHERE office IN ('SR','SS') AND district=? AND election_cycle=? "
                "AND total_receipts IS NOT NULL AND ABS(total_receipts - ?) < 1.0",
                [bare, int(yr), amt]).fetchall()}
            if len(hits) == 1:
                resolved[(dist, int(yr), side)] = hits.pop()
    ids = sorted(set(resolved.values()))
    sums = {}
    if ids:
        marks = ",".join("?" for _ in ids)
        for fid, cyc, full, pre in wcon.execute(f"""
            SELECT fec_candidate_id, election_cycle,
                   SUM(contribution_amount),
                   SUM(contribution_amount) FILTER (WHERE contribution_date <=
                       CASE election_cycle WHEN 2018 THEN DATE '2018-11-06'
                            WHEN 2020 THEN DATE '2020-11-03'
                            WHEN 2022 THEN DATE '2022-11-08'
                            WHEN 2024 THEN DATE '2024-11-05' END)
            FROM individual_contributions
            WHERE fec_candidate_id IN ({marks}) AND contribution_amount > 0
            GROUP BY 1, 2""", ids).fetchall():
            sums[(fid, int(cyc))] = (float(full or 0), float(pre or 0))
    wcon.close()
    xs_full, xs_pre, ys = [], [], []
    pairs = 0
    for dist, yr, op, _dr, _rr in leg:
        kd, kr = (dist, int(yr), "D"), (dist, int(yr), "R")
        if kd not in resolved or kr not in resolved:
            continue
        pairs += 1
        dv = sums.get((resolved[kd], int(yr)), (0.0, 0.0))
        rv = sums.get((resolved[kr], int(yr)), (0.0, 0.0))
        if min(dv[0], rv[0]) <= 0 or min(dv[1], rv[1]) <= 0:
            continue
        xs_full.append(math.log2(dv[0] / rv[0]))
        xs_pre.append(math.log2(dv[1] / rv[1]))
        ys.append(float(op))
    d["leg_total_n"] = len(leg)
    d["leg_resolved_n"] = pairs
    n = len(ys)
    d["leg_item_n"] = n

    def _r(xs):
        mx, my = sum(xs) / n, sum(ys) / n
        sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
        sy = math.sqrt(sum((y - my) ** 2 for y in ys))
        return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy)

    d["leg_item_full_r"], d["leg_item_pre_r"] = _r(xs_full), _r(xs_pre)
    d["leg_item_delta"] = d["leg_item_full_r"] - d["leg_item_pre_r"]


def derive_allocation(d: dict) -> None:
    """Finding 2a's correlations, from the pinned allocation frame.

    THESE WERE EXEMPTED AND SHOULD NOT HAVE BEEN. The original exemption waived the whole of
    Finding 2a on the grounds that checking it means re-running a regression. That is true of
    the holdout R-squared table and false of everything else in the block: the share
    correlations, the total-spend correlation, the two persistence coefficients and the
    field-versus-overperformance figure are plain Pearson correlations over a frame already on
    disk. Seven figures were unchecked because they sat next to four that could not be.

    Persistence pairs a candidate's share in one cycle against the same candidate's share in
    the next, which is why it is computed by joining the frame to itself on the candidate
    rather than by any windowing over the whole table.
    """
    if not ALLOC.exists():
        raise SystemExit(
            f"FATAL: pinned allocation frame missing: {ALLOC}\n"
            f"  Regenerate with:\n"
            f"    PYTHONPATH=src python scripts/diag_expenditures_vs_residual.py "
            f"--csv {ALLOC}\n"
            f"  Regenerating re-pins Finding 2a; expect its figures to move and update them "
            f"deliberately.")
    con = duckdb.connect()
    src = f"read_csv_auto('{ALLOC.as_posix()}', header=true)"
    row = con.execute(f"""
        SELECT COUNT(*), corr(residual, field_share), corr(residual, media_share),
               corr(residual, professional_share), corr(residual, log_operational_total),
               corr(overperf, field_share)
        FROM {src}""").fetchone()
    (d["alloc_n"], d["r_field"], d["r_media"], d["r_prof"], d["r_totalspend"],
     d["r_field_overperf"]) = [int(row[0])] + [float(x) for x in row[1:]]
    d["r_field_overperf_abs"] = abs(d["r_field_overperf"])
    d["r_prof_abs"] = abs(d["r_prof"])
    pair = con.execute(f"""
        WITH a AS (SELECT dem, field_share f, media_share m FROM {src} WHERE year = 2022),
             b AS (SELECT dem, field_share f, media_share m FROM {src} WHERE year = 2024)
        SELECT COUNT(*), corr(a.f, b.f), corr(a.m, b.m) FROM a JOIN b USING (dem)""").fetchone()
    d["persist_n"], d["persist_field"], d["persist_media"] =         int(pair[0]), float(pair[1]), float(pair[2])
    con.close()


# --- PUBLIC ADAPTATION -------------------------------------------------------------------
# The private script imports StaleIEData / assert_ie_classified from the unpublished
# wa_analyzer package, so the guard is inlined here. It is the SAME check: FEC IE rows
# loaded before the 2026-08-08 notice/periodic split carry is_notice IS NULL, are excluded by
# v_independent_expenditures, and would silently yield $0.0M rather than an inflated total.
# Stopping is safer than reporting a number nobody measured. Kept character-comparable with
# the copy in diag_ie_vs_margin.py so there is one public definition to read.
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
# --- end public adaptation ---------------------------------------------------------------


def derive_legislative_panel(d: dict) -> None:
    """Finding 3's state-legislative directional panel, recomputed from the cells.

    The pinned file carries one row per (advocacy scope, specification, cycle,
    district) with the net pro-Dem IE and the fundamentals-net residual. The
    slopes, intervals and correlations the paper prints are recomputed HERE from
    those cells rather than read back from a stored coefficient, so a paper
    figure that drifted from the panel fails.

    The bootstrap is the same percentile bootstrap the diagnostic runs, at the
    same fixed seed — a different resampling scheme would produce intervals that
    differ in the third decimal and fail against the paper for no real reason.
    """
    if not PDCIE.exists():
        raise SystemExit(
            f"FATAL: pinned legislative IE panel missing: {PDCIE}\n"
            f"  Regenerate with:\n"
            f"    python scripts/diag_pdc_ie_vs_margin.py --cells-csv {PDCIE}\n"
            f"  Regenerating re-pins Finding 3's legislative table; expect its "
            f"figures to move and update them deliberately.")

    import csv as _csv
    rows: list[dict] = []
    with PDCIE.open(encoding="utf-8", newline="") as fh:
        for r in _csv.DictReader(fh):
            rows.append(r)

    def _panel(scope: str, spec: str):
        return [(float(r["net_pro_dem_musd"]), float(r["residual_pp"]),
                 float(r["total_directional_musd"]), r["district_id"])
                for r in rows
                if r["advocacy_scope"] == scope and r["specification"] == spec]

    def _ols(xs, ys):
        n = len(xs)
        mx, my = sum(xs) / n, sum(ys) / n
        sxx = sum((x - mx) ** 2 for x in xs)
        sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        syy = sum((y - my) ** 2 for y in ys)
        if sxx == 0 or syy == 0:
            return 0.0, 0.0
        return sxy / sxx, sxy / math.sqrt(sxx * syy)

    # The bootstrap's tails, named so the paper's printed "95% interval" can be
    # asserted against the code that produces it rather than restated. A probe on
    # a hard-coded 95 would agree with the paper while the slicing said otherwise.
    BOOT_LO, BOOT_HI = 0.025, 0.975

    def _boot(xs, ys, iters=5000, seed=12345):
        rng = random.Random(seed)
        idx = list(range(len(xs)))
        out = []
        for _ in range(iters):
            s = [rng.choice(idx) for _ in idx]
            out.append(_ols([xs[i] for i in s], [ys[i] for i in s])[0])
        out.sort()
        return out[int(BOOT_LO * iters)], out[int(BOOT_HI * iters)]

    # Same materiality floor as the diagnostic. Quoted in the paper's table, so
    # a change on either side has to be made on both.
    MATERIAL_M = 0.025

    for scope, spec, tag in (("express", "race_matched", "expr_matched"),
                             ("express", "district_aggregate", "expr_agg"),
                             ("all", "race_matched", "all_matched"),
                             ("all", "district_aggregate", "all_agg")):
        cells = _panel(scope, spec)
        if not cells:
            raise SystemExit(
                f"FATAL: pinned panel has no rows for {scope}/{spec}. The file "
                f"was regenerated with a different specification set; Finding 3's "
                f"table cannot be checked against it.")
        xs = [c[0] for c in cells]
        ys = [c[1] for c in cells]
        slope, rho = _ols(xs, ys)
        lo, hi = _boot(xs, ys)
        # District-clustered bootstrap + per-SD slope (external referee 2026-08-15,
        # items 5 and 11): resample the districts, not the race-cycles, and express
        # the slope per one SD of treatment so panels with $1M-vs-$67K treatment
        # scales can be compared at all. Same seed convention as _boot.
        clo, chi = _cluster_boot(xs, ys, [c[3] for c in cells], _ols)
        sdx = (sum((x - sum(xs) / len(xs)) ** 2 for x in xs) / len(xs)) ** 0.5
        d[f"leg_{tag}_cluster_lo_abs"] = abs(clo)
        d[f"leg_{tag}_cluster_hi"] = chi
        d[f"leg_{tag}_sd_x"] = sdx
        d[f"leg_{tag}_per_sd_slope"] = slope * sdx
        d[f"leg_{tag}_per_sd_slope_abs"] = abs(slope * sdx)
        d[f"leg_{tag}_n"] = len(cells)
        d[f"leg_{tag}_material"] = sum(1 for c in cells if c[2] >= MATERIAL_M)
        d[f"leg_{tag}_slope"] = slope
        d[f"leg_{tag}_r"] = rho
        d[f"leg_{tag}_ci_lo_abs"] = abs(lo)
        d[f"leg_{tag}_ci_hi"] = hi
        # The paper writes negative figures with the minus sign as prose, outside
        # the captured group, so a probe comparing the capture to a negative
        # derived value reads as a defect when it is a probe bug. Magnitudes are
        # carried alongside for those cells.
        d[f"leg_{tag}_slope_abs"] = abs(slope)
        d[f"leg_{tag}_material_pct"] = 100.0 * d[f"leg_{tag}_material"] / len(cells)
        d[f"leg_{tag}_r_abs"] = abs(rho)

    # The band the paper uses to argue the sample was never the binding
    # constraint ("only 13–47% of cells attract any material IE"). Derived from
    # the same four specifications printed in the table rather than restated, so
    # a change to any one of them moves the band and the probe catches it.
    _mat = [d[f"leg_{t}_material_pct"]
            for t in ("expr_matched", "expr_agg", "all_matched", "all_agg")]
    d["leg_material_pct_lo"], d["leg_material_pct_hi"] = min(_mat), max(_mat)

    # The three SPECIFICATION UNITS the paper prints — the bootstrap's confidence
    # level, the materiality floor and the slope's money scaling. None is a
    # measurement, so each was auto-exempt as a small integer until strict_units
    # surfaced it. They are derived rather than exempted because each is tied to
    # a constant that could move underneath the prose: change BOOT_LO/BOOT_HI and
    # "95% interval" is wrong, change MATERIAL_M and "≥$25K" is wrong, and if the
    # panel's x column stopped being denominated in millions "per $1M" would be
    # wrong by a factor of a million with every other figure still reconciling.
    d["boot_level_pct"] = 100.0 * (BOOT_HI - BOOT_LO)
    d["material_floor_k"] = MATERIAL_M * 1000.0
    if "net_pro_dem_musd" not in rows[0]:
        raise SystemExit(
            "FATAL: the pinned IE panel no longer carries `net_pro_dem_musd`. The "
            "slope's printed unit ('per $1M') describes that column's denomination; "
            "if the column changed, the unit in the paper is unverified.")
    d["slope_unit_musd"] = 1.0


def derive_federal_influence(d: dict) -> None:
    """The federal IE regression's influence and clustering facts, from its pin.

    Added 2026-08-15 (external referee, items 4 and 5): the +0.515 slope is a
    single-district leverage result — deleting WA-08/2018 (Cook's distance 0.69)
    moves it to −0.035 — and the iid case-resampling interval understates the
    clustered one. The paper now says both, and both are derived here.
    """
    import csv as _csv
    rows = list(_csv.DictReader(IECELLS.open(encoding="utf-8", newline="")))
    xs = [float(r["net_pro_dem_m"]) for r in rows]
    ys = [float(r["residual_pp"]) for r in rows]
    dists = [r["district_id"] for r in rows]
    labels = [f"{r['district_id']}/{str(r['cycle'])[-2:]}" for r in rows]
    n = len(rows)

    def _ols(bx, by):
        m = len(bx)
        mx, my = sum(bx) / m, sum(by) / m
        sxx = sum((x - mx) ** 2 for x in bx)
        sxy = sum((x - mx) * (y - my) for x, y in zip(bx, by))
        syy = sum((y - my) ** 2 for y in by)
        if sxx == 0 or syy == 0:
            return 0.0, 0.0
        return sxy / sxx, sxy / math.sqrt(sxx * syy)

    slope, _ = _ols(xs, ys)
    d["fed_slope"] = slope
    # Leave-one-out extremes, and the drop-all-WA-08 sensitivity.
    loo = sorted((_ols(xs[:i] + xs[i + 1:], ys[:i] + ys[i + 1:])[0], labels[i])
                 for i in range(n))
    d["fed_loo_min_abs"] = abs(loo[0][0])
    d["fed_loo_max"] = loo[-1][0]
    no8 = [(x, y) for x, y, dd in zip(xs, ys, dists) if dd != "cd08"]
    d["fed_no_cd08_slope_abs"] = abs(_ols([p[0] for p in no8], [p[1] for p in no8])[0])
    # Cook's distance of the top-leverage observation.
    intercept = (sum(ys) / n) - slope * (sum(xs) / n)
    mx = sum(xs) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    resid = [y - (intercept + slope * x) for x, y in zip(xs, ys)]
    mse = sum(e * e for e in resid) / (n - 2)
    d["fed_cooks_max"] = max(
        (resid[i] ** 2 / (2 * mse)) * ((1 / n + (xs[i] - mx) ** 2 / sxx)
                                       / (1 - (1 / n + (xs[i] - mx) ** 2 / sxx)) ** 2)
        for i in range(n))
    # Clustered intervals + the per-SD scale.
    clo, chi = _cluster_boot(xs, ys, dists, _ols)
    d["fed_cluster_lo_abs"], d["fed_cluster_hi"] = abs(clo), chi
    era = [f"{dd}-{'pre' if int(str(r['cycle'])) < 2022 else 'post'}"
           for dd, r in zip(dists, rows)]
    elo, ehi = _cluster_boot(xs, ys, era, _ols)
    d["fed_era_cluster_lo_abs"], d["fed_era_cluster_hi"] = abs(elo), ehi
    sdx = (sum((x - mx) ** 2 for x in xs) / n) ** 0.5
    d["fed_sd_x"] = sdx
    d["fed_per_sd_slope"] = slope * sdx
    # The leverage case's own coordinates, quoted in 2c's influence paragraph.
    imax = max(range(n), key=lambda i: xs[i])
    # --- FUNCTIONAL-FORM SENSITIVITY (2026-08-25, second external referee) --------------
    # The referee's objection was that influence diagnostics on ONE specification cannot show
    # whether the specification is the reason for the influence. These are the frame-level
    # facts and the alternative-form coefficients the paper now prints. Derived from the same
    # pinned frame, so they cost no database and no model; the full run with intervals is
    # scripts/diag_ie_functional_form.py, which reproduces the headline slope to the digit.
    import math as _math
    import numpy as _np
    tots = [float(r["total_m"]) for r in rows]
    d["ff_gross_m"] = sum(tots)
    d["ff_absnet_m"] = sum(abs(x) for x in xs)
    d["ff_cancel_pct"] = 100.0 * (d["ff_gross_m"] - d["ff_absnet_m"]) / d["ff_gross_m"]
    d["ff_zero_n"] = sum(1 for x in xs if abs(x) < 0.01)
    # The load-bearing qualifier: those zeros are GENUINE, not cancellation artifacts.
    d["ff_zero_with_ie"] = sum(1 for x, tt in zip(xs, tots)
                               if abs(x) < 0.01 and tt > 0.01)
    _i822 = next(i for i, r in enumerate(rows)
                 if r["district_id"] == "cd08" and str(r["cycle"]) == "2022")
    d["ff_wa08_22_total"] = tots[_i822]
    d["ff_wa08_22_net_abs"] = abs(xs[_i822])
    d["ff_wa08_22_survive_pct"] = 100.0 * abs(xs[_i822]) / tots[_i822]

    # Under the COMPRESSED forms, dropping the high-leverage race leaves the estimate
    # positive instead of flipping the sign. That is the finding the single form could
    # not show, so it is derived rather than described.
    _drop = [i for i in range(n) if labels[i] != "cd08/18"]
    for _tag, _fx in (("asinh", _math.asinh),
                      ("slog", lambda v: _math.copysign(_math.log1p(abs(v)), v))):
        _tx = [_fx(x) for x in xs]
        d[f"ff_{_tag}_loo_drop_wa0818"] = _ols([_tx[i] for i in _drop],
                                               [ys[i] for i in _drop])[0]

    def _multi(cols):
        A = _np.column_stack([_np.ones(n)] + [_np.array(c) for c in cols])
        beta, *_ = _np.linalg.lstsq(A, _np.array(ys), rcond=None)
        return [float(b) for b in beta]

    _prod = [float(r["pro_dem"]) / 1e6 for r in rows]
    _pror = [float(r["pro_rep"]) / 1e6 for r in rows]
    _b3 = _multi([_prod, _pror])
    d["ff_prodem_coef"], d["ff_prorep_coef_abs"] = _b3[1], abs(_b3[2])
    _b4 = _multi([xs, tots])
    d["ff_net_with_total"], d["ff_total_coef_abs"] = _b4[1], abs(_b4[2])

    # The scorable-race count, printed in the reproduction note (2026-08-25). It is the
    # frame's own length, so a frame that changed size would move the note with it.
    d["fed_scorable_n"] = n
    d["fed_max_net_ie"] = xs[imax]
    d["fed_max_net_resid"] = ys[imax]


def derive_linkage_audit(d: dict) -> None:
    """The 2026-08-15 finance-linkage correction, derived as the diff of the two pins.

    The pin note quotes the audit — 2 of 326 lookups changed, one crediting a
    same-name namesake's $190K — and the retired frame's 129-cell +0.58 state.
    All of it is derived from the retained old pin against the current one, so
    the narrative cannot drift from the files it describes.
    """
    con = duckdb.connect()
    old = f"read_csv_auto('{CELLS_OLD.as_posix()}', header=true)"
    new = f"read_csv_auto('{CELLS.as_posix()}', header=true)"
    d["fin_cells_oldpin"], d["r_fin_oldpin"] = con.execute(f"""
        SELECT COUNT(*) FILTER (WHERE fin_log2_dr IS NOT NULL),
               corr(overperformance, fin_log2_dr)
        FROM {old} WHERE baseline_ok""").fetchone()
    d["audit_changed"], = con.execute(f"""
        SELECT COUNT(*) FROM {old} o JOIN {new} n
          ON o.district = n.district AND o.year = n.year
        WHERE o.baseline_ok
          AND (COALESCE(o.d_receipts, -1) <> COALESCE(n.d_receipts, -1)
               OR COALESCE(o.r_receipts, -1) <> COALESCE(n.r_receipts, -1))""").fetchone()
    d["audit_lookups"] = 2.0 * float(d["cells_scorable"])
    # The wrongly-attached receipts: present in the old pin, absent from the new.
    d["audit_namesake_k"], = con.execute(f"""
        SELECT ROUND(o.r_receipts / 1000)
        FROM {old} o JOIN {new} n ON o.district = n.district AND o.year = n.year
        WHERE o.r_receipts IS NOT NULL AND n.r_receipts IS NULL""").fetchone()
    con.close()


def derive_common_sample(d: dict) -> None:
    """Finding 1's competing correlations on the common finance-complete sample.

    Added 2026-08-15 (external referee, item 2): the factor correlations used
    different samples — finance saw only its non-null cells while the other four
    saw all 163 — so the '+0.60 vs +0.43' ranking was not apples-to-apples until
    recomputed on the common cells. Both versions are now printed and derived.
    """
    con = duckdb.connect()
    src = f"read_csv_auto('{CELLS.as_posix()}', header=true)"
    row = con.execute(f"""
        SELECT corr(overperformance, inc_signed), corr(overperformance, candidate_quality),
               corr(overperformance, local_trend), corr(overperformance, is_midterm)
        FROM {src} WHERE baseline_ok AND fin_log2_dr IS NOT NULL""").fetchone()
    (d["r_inc_common"], d["r_quality_common"],
     d["r_trend_common"], d["r_midterm_common"]) = [float(x) for x in row]
    con.close()


def derive_estimator_facts(d: dict) -> None:
    """Appendix C's estimator statement, tied to the instruments' own source.

    Added 2026-08-15 (constructions-inventory finding 1): the paper now names its
    estimator (bivariate OLS) and its bootstrap (case-resampling percentile, fixed
    seed) with a replicate count. The count is read out of every IE script that
    computes an interval, and they must all agree — so the sentence cannot drift
    from the code, and a script that quietly changed its `iters=` would fail here
    before the paper printed a stale B.
    """
    scripts_dir = Path(__file__).resolve().parent
    iters_seen = {}
    for name in ("diag_ie_vs_margin.py", "diag_pdc_ie_vs_margin.py",
                 "diag_ie_early_late.py", "diag_ie_next_cycle_placebo.py"):
        src = (scripts_dir / name).read_text(encoding="utf-8")
        m = re.search(r"def bootstrap_\w+\([^)]*iters=(\d+), seed=(\d+)", src)
        if m is None:
            # A script may share the canonical implementation instead of defining
            # one — the placebo script imports it from diag_ie_vs_margin. That IS
            # the single-implementation property the paper's sentence relies on,
            # so an import is accepted as evidence; anything else fails.
            assert re.search(r"from diag_ie_vs_margin import\b[^)]*?bootstrap_slope_ci",
                             src, re.S), (
                f"{name}: neither defines a bootstrap with iters=/seed= nor imports "
                "the canonical one — the paper's estimator statement no longer "
                "describes this script")
            continue
        iters_seen[name] = int(m.group(1))
        assert "rng.choice" in src, (
            f"{name}: the case-resampling loop has changed shape — re-read it before "
            "trusting the paper's 'pairs percentile bootstrap' description")
    assert iters_seen and len(set(iters_seen.values())) == 1, (
        f"the IE scripts disagree on replicate counts: {iters_seen} — the paper "
        "states one B for all of them")
    d["mv_bootstrap_iters"] = float(next(iter(iters_seen.values())))


def _current_cycle_pin() -> dict:
    """The open cycle's pinned inventory reading.

    Read from the pin rather than written here so "what was the open cycle on the day this
    paper was derived" has ONE definition, shared with
    tests/test_infrastructure/test_fec_ie_current_cycle_pin.py. A missing pin is FATAL:
    falling back to a live count would silently restore the floating basis this exists to
    close, and would do it in the one paper whose figures a weekly scheduled task moves.
    """
    if not CURRENT_CYCLE_PIN.exists():
        raise SystemExit(
            f"FATAL: the open-cycle pin is missing ({CURRENT_CYCLE_PIN}). Finding 3's 2026 "
            f"row and the panel totals are pinned to it. Refusing to fall back to a live "
            f"count -- that is the floating basis this pin was created to close.")
    with CURRENT_CYCLE_PIN.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise SystemExit(f"FATAL: {CURRENT_CYCLE_PIN} has no rows.")
    return rows[0]


def derive_ceiling(d: dict) -> None:
    """The data-ceiling facts — re-derived in SQL, owing nothing to any diag script."""
    con = duckdb.connect(str(vp.DATA / "wa_statewide.duckdb"), read_only=True)

    # Every IE figure below reads v_independent_expenditures, which drops FEC's
    # 24/48-hour notice rows (they restate the periodic Schedule E and double
    # the totals). Rows loaded before that distinction existed are dropped too,
    # which would silently turn these assertions into $0.0M — so stop first.
    assert_ie_classified(con)

    # Flagged-IE cycle inventory. The paper's claim is about which cycles are SCORABLE, so
    # the inventory is reported per cycle rather than as a bare count.
    cycles = con.execute("""
        SELECT election_cycle, COUNT(*), COUNT(DISTINCT district), SUM(expenditure_amount)
        FROM v_independent_expenditures
        WHERE source='FEC' AND office='H' AND state='WA' AND support_oppose IN ('S','O')
        GROUP BY 1 ORDER BY 1""").fetchall()
    by_cycle = {int(c): (int(n), int(k), float(v)) for c, n, k, v in cycles}
    d["ie_cycles"] = len(by_cycle)
    # Every cycle in the panel, not a hand-picked pair. The old version derived
    # 2024 and 2026 only, because those were the only two on disk; after the
    # 2018/2020/2022 backfill that made the paper's inventory table three rows
    # wider than anything asserted against it.
    for cyc, (n, k, v) in by_cycle.items():
        d[f"ie{cyc}_rows"], d[f"ie{cyc}_districts"] = n, k
        d[f"ie{cyc}_m"], d[f"ie{cyc}_k"] = v / 1e6, v / 1e3

    # THE OPEN CYCLE COMES FROM THE PIN, NOT FROM THE QUERY ABOVE. Overwriting the live
    # values is the whole point: FEC filings for an open cycle keep arriving, and since
    # 2026-08-24 they arrive unattended on a weekly timer, so a live read makes the paper's
    # printed cells drift with no edit and no error. The paper prints the as-of date beside
    # the row; the pin is what that date means.
    pin = _current_cycle_pin()
    open_cycle = int(pin["cycle"])
    d[f"ie{open_cycle}_rows"] = int(pin["rows"])
    d[f"ie{open_cycle}_districts"] = int(pin["districts"])
    d[f"ie{open_cycle}_m"] = float(pin["total_usd"]) / 1e6
    d[f"ie{open_cycle}_k"] = float(pin["total_usd"]) / 1e3
    # The as-of date is PRINTED in the paper, so it is a figure and gets probed like one
    # rather than exempted -- editing the date in the prose without re-pinning then fails,
    # which is the coupling that keeps this basis from floating again. Same construction as
    # verify_who_decides_wa.py's a_rej_panel_* keys.
    _y, _m, _dd = pin["as_of"].split("-")
    d["ie_asof_y"], d["ie_asof_m"], d["ie_asof_d"] = int(_y), int(_m), int(_dd)

    # DRIFT IS DISCLOSED, NOT FAILED. The pin is a dated historical reading and stays true;
    # the live view moving past it is expected, not a defect. But silence would make the pin
    # unfalsifiable, which is this repo's first-named failure mode, so the gap is printed
    # with the mechanism named. Re-pin deliberately if the paper is re-derived.
    live_n, _live_k, live_v = by_cycle.get(open_cycle, (0, 0, 0.0))
    if live_n != int(pin["rows"]) or abs(live_v - float(pin["total_usd"])) >= 0.01:
        print(f"  NOTICE  open cycle {open_cycle} has moved past the pin "
              f"({pin['as_of']}): pinned {int(pin['rows'])} rows / "
              f"${float(pin['total_usd']):,.2f}, live {live_n} rows / ${live_v:,.2f}. "
              f"Expected -- the cycle is open and 'WA FEC IE Weekly Refresh' writes it "
              f"unattended. The paper's dated reading is unaffected; re-pin only if you "
              f"re-derive the paper (docs/reference/fec_ie_current_cycle_pin.csv).")

    # PANEL TOTALS COUNT COMPLETED CYCLES ONLY. This is what the analysis uses -- all 34
    # scorable races are 2018-2024 -- and it is the half that does not move. Including the
    # open cycle is what made these two cells drift.
    _done = {c: v for c, v in by_cycle.items() if c <= LAST_COMPLETED_CYCLE}
    # The number of COMPLETED cycles, distinct from `ie_cycles` (the inventory count). The
    # abstract needs this one: the estimator's 34 scorable races all sit in closed cycles, and
    # a claim-guard that compared the abstract against the INVENTORY count was what kept the
    # abstract saying "five cycles" for a test that runs on four (second external referee,
    # 2026-08-25). The gate was enforcing the defect.
    d["ie_cycles_completed"] = len(_done)
    d["ie_total_rows"] = sum(n for n, _, _ in _done.values())
    d["ie_total_m"] = sum(v for _, _, v in _done.values()) / 1e6

    # Appendix E's "party attribution is effectively complete" numerator, ON THE SAME
    # COMPLETED-CYCLE BASIS as the panel total beside it. Derived rather than left as prose:
    # the printed value was $0.03M, which reproduces on NEITHER basis today (completed cycles
    # $1,560; all cycles $228,866), and the reason is the same one that moved the panel
    # totals — new open-cycle filings routinely land before the candidate record that
    # resolves them to a party, so an all-cycle numerator drifts upward every refresh.
    # Confirmed against scripts/diag_ie_vs_margin.py, which owns Appendix E and splits it
    # $1,560.32 completed / $227,305.77 open (all cd05/26).
    unres, unres_cells = con.execute(f"""
        WITH p AS (SELECT DISTINCT election_cycle, UPPER(candidate_name) cn, party
                   FROM candidate_finance WHERE state='WA' AND office='H')
        SELECT SUM(CASE WHEN p.party IS NULL OR p.party NOT IN ('Democratic','Republican')
                        THEN ie.expenditure_amount ELSE 0 END),
               COUNT(DISTINCT CASE
                        WHEN p.party IS NULL OR p.party NOT IN ('Democratic','Republican')
                        THEN ie.district || '/' || ie.election_cycle END)
        FROM v_independent_expenditures ie
        LEFT JOIN p ON p.election_cycle = ie.election_cycle
                   AND p.cn = UPPER(ie.candidate_name)
        WHERE ie.source='FEC' AND ie.office='H' AND ie.state='WA'
          AND ie.support_oppose IN ('S','O')
          AND ie.election_cycle <= {LAST_COMPLETED_CYCLE}""").fetchone()
    d["ie_unresolved_usd"] = float(unres)
    d["ie_unresolved_cells"] = int(unres_cells)

    # --- THE RECEIPTS MEASUREMENT WINDOW (2026-08-25, second external referee) ----------
    # The referee asked what cutoff defines "receipts" and noted that full-cycle totals would
    # mean outcome-to-measure leakage on top of ordinary endogeneity. Measured rather than
    # asserted: candidate_finance carries ONE row per candidate-cycle, and coverage_end_date
    # straddles election day, so the predictor's window usually closes after the outcome it is
    # correlated with. Derived here so the disclosure in Appendix C is gated like any figure.
    _rb = con.execute("""
        WITH eday(cyc, d) AS (VALUES (2018,DATE '2018-11-06'),(2020,DATE '2020-11-03'),
                                     (2022,DATE '2022-11-08'),(2024,DATE '2024-11-05')),
             f AS (SELECT cf.election_cycle cyc, cf.district dist, cf.party,
                          date_diff('day', e.d, cf.coverage_end_date) rel
                   FROM candidate_finance cf JOIN eday e ON e.cyc = cf.election_cycle
                   WHERE cf.state='WA' AND cf.office='H' AND cf.total_receipts > 0
                     AND cf.party IN ('Democratic','Republican')),
             pr AS (SELECT cyc, dist,
                           MAX(CASE WHEN party='Democratic' THEN rel END) d_rel,
                           MAX(CASE WHEN party='Republican'  THEN rel END) r_rel
                    FROM f GROUP BY 1,2)
        SELECT COUNT(*), COUNT(*) FILTER (WHERE ABS(d_rel-r_rel) > 60),
               MAX(ABS(d_rel-r_rel)), AVG(ABS(d_rel-r_rel))
        FROM pr WHERE d_rel IS NOT NULL AND r_rel IS NOT NULL""").fetchone()
    d["rb_pairs"], d["rb_gap_over_60"] = int(_rb[0]), int(_rb[1])
    d["rb_worst_gap"], d["rb_mean_gap"] = float(_rb[2]), float(_rb[3])
    d["rb_rows"] = int(con.execute("""
        SELECT COUNT(*) FROM candidate_finance
        WHERE state='WA' AND office='H' AND total_receipts > 0
          AND election_cycle IN (2018,2020,2022,2024)""").fetchone()[0])

    # --- THE IDENTIFICATION SEARCH (2026-08-25, referee item 1) --------------------------
    # The paper now COUNTS the designs instead of naming them, so the counts are gated.
    # Imported from the script the section cites, for the same reason the inference
    # estimators are: one definition of "repeat match-up", not two.
    import diag_repeat_matchups as _rm
    for _lbl, _offs, _pfx in (("H", ("H",), "idsearch_fed"),
                              ("LEG", ("SR", "SS"), "idsearch_leg")):
        _tot, _rep, _diff, _mx = con.execute(_rm._sql(_offs)).fetchone()
        d[f"{_pfx}_cycles"] = int(_tot)
        d[f"{_pfx}_repeats"] = int(_rep)
        # Only the FEDERAL differenced count is printed (the legislative one coincides with
        # its repeat count, since every repeat spans exactly two cycles). Deriving the
        # legislative one too would be a key nothing reads, which is the thing the no-probe
        # ceiling exists to prevent -- so it is not derived.
        if _pfx == "idsearch_fed":
            d[f"{_pfx}_diffs"] = int(_diff)
    _leghouse = con.execute(_rm._sql(("SR",))).fetchone()
    _legsen = con.execute(_rm._sql(("SS",))).fetchone()
    d["idsearch_leg_house_repeats"] = int(_leghouse[1])
    d["idsearch_leg_sen_repeats"] = int(_legsen[1])
    # The redistricting count: one redraw, and every scorable district observed either side.
    import csv as _c2
    _fr2 = list(_c2.DictReader(IECELLS.open(encoding="utf-8", newline="")))
    d["idsearch_redraws"] = 1
    d["idsearch_both_sides"] = len({r["district_id"] for r in _fr2
                                    if int(r["cycle"]) < 2022}
                                   & {r["district_id"] for r in _fr2
                                      if int(r["cycle"]) >= 2022})

    # The two UNSCORABLE federal races that nonetheless carried real money, named in
    # Finding 3's zero-treatment paragraph (2026-08-25). They are NOT in the pinned 34-row
    # frame -- that frame holds scorable races only, which is precisely the point being made:
    # the federal panel discards treated observations for want of a scorable outcome. Derived
    # live, which is safe here because both cycles are closed (see the disposition in
    # tests/test_infrastructure/test_unattended_writer_exposure.py).
    for _dist, _cyc, _key in (("10", 2020, "unsc_cd10_20_net"),
                              ("04", 2024, "unsc_cd04_24_net")):
        _n = con.execute(f"""
            WITH p AS (SELECT DISTINCT election_cycle, UPPER(candidate_name) cn, party
                       FROM candidate_finance WHERE state='WA' AND office='H')
            SELECT SUM(CASE WHEN (p.party='Democratic' AND ie.support_oppose='S')
                              OR (p.party='Republican' AND ie.support_oppose='O')
                            THEN ie.expenditure_amount ELSE -ie.expenditure_amount END)/1e6
            FROM v_independent_expenditures ie
            LEFT JOIN p ON p.election_cycle = ie.election_cycle
                       AND p.cn = UPPER(ie.candidate_name)
            WHERE ie.source='FEC' AND ie.office='H' AND ie.state='WA'
              AND ie.support_oppose IN ('S','O') AND ie.election_cycle = {_cyc}
              AND ie.district IN ('{_dist}', '{_dist.lstrip("0")}')""").fetchone()[0]
        d[_key] = float(_n or 0.0)

    # --- INFERENCE SENSITIVITY + THE CLEAN LEGISLATIVE SUBSET (2026-08-25, referee) ------
    # IMPORTED from the script the paper cites rather than reimplemented here. Two copies of
    # an estimator drift apart, and this paper has already paid for a duplicated constant
    # three times in Appendix E; a duplicated ESTIMATOR would be worse. Importing also means
    # this gate checks the paper against the SAME code a reader would run.
    import numpy as _np
    import diag_ie_inference_sensitivity as _inf
    _fr = _inf._read(_inf.FED)
    _x = _np.array([float(r["net_pro_dem_m"]) for r in _fr])
    _y = _np.array([float(r["residual_pp"]) for r in _fr])
    _g = [r["district_id"] for r in _fr]
    _b, _, _ = _inf._fit(_x, _y)
    _se3 = _inf._hc3(_x, _y)
    _secr, _G = _inf._cr_se(_x, _y, _g)
    d["inf_hc3_lo_abs"] = abs(float(_b[1]) - 1.96 * _se3)
    d["inf_hc3_hi"] = float(_b[1]) + 1.96 * _se3
    d["inf_cr_lo_abs"] = abs(float(_b[1]) - 1.96 * _secr)
    d["inf_cr_hi"] = float(_b[1]) + 1.96 * _secr
    d["inf_wild_p"] = _inf._wild_cluster_p(_x, _y, _g)[0]

    # The Senate-only (cleanly assignable) legislative subset.
    _lg = _inf._read(_inf.LEG)
    _sen = [r for r in _lg if r["is_senate"] == "1"]
    d["sen_n"] = len({(r["district_id"], r["cycle"]) for r in _sen})
    d["sen_min_n_threshold"] = _inf.MIN_N_FOR_SLOPE
    _rm = [r for r in _sen if r["specification"] == "race_matched"
           and r["advocacy_scope"] == "all"]
    d["sen_max_net_k"] = max(abs(float(r["net_pro_dem_musd"])) for r in _rm) * 1000.0
    d["sen_nearzero"] = sum(1 for r in _rm if abs(float(r["net_pro_dem_musd"])) <= 0.001)
    _slopes = []
    for _sc in ("all", "express"):
        for _sp in ("district_aggregate", "race_matched"):
            _s = [r for r in _sen if r["advocacy_scope"] == _sc
                  and r["specification"] == _sp]
            _nx = _np.array([float(r["net_pro_dem_musd"]) for r in _s])
            _ny = _np.array([float(r["residual_pp"]) for r in _s])
            if len(set(_nx.tolist())) > 1:
                _slopes.append(float(_inf._fit(_nx, _ny)[0][1]))
    d["sen_slope_min_abs"] = abs(min(_slopes))
    d["sen_slope_max"] = max(_slopes)

    # WA-03 2024 — the largest independent-expenditure total in the panel.
    tot, net = con.execute("""
        WITH p AS (SELECT DISTINCT election_cycle, UPPER(candidate_name) cn, party
                   FROM candidate_finance WHERE state='WA' AND office='H')
        SELECT SUM(ie.expenditure_amount)/1e6,
               SUM(CASE WHEN (p.party='Democratic' AND ie.support_oppose='S')
                          OR (p.party='Republican' AND ie.support_oppose='O')
                        THEN ie.expenditure_amount ELSE -ie.expenditure_amount END)/1e6
        FROM v_independent_expenditures ie
        LEFT JOIN p ON p.election_cycle = ie.election_cycle
                   AND p.cn = UPPER(ie.candidate_name)
        WHERE ie.source='FEC' AND ie.office='H' AND ie.state='WA'
          AND ie.support_oppose IN ('S','O') AND ie.election_cycle = 2024
          AND ie.district IN ('03','3')""").fetchone()
    d["wa03_total_m"], d["wa03_net_m"] = float(tot), float(net)

    # PDC state-legislative IE. Direction lives in `pdc_ie_targets` (form C-6
    # section C6.3), NOT in independent_expenditures.support_oppose — a C6.3
    # target is one-to-many against an expenditure and cannot share that table's
    # key. An earlier version of this verifier asserted the paper's claim that
    # the flag was empty and that the money therefore "cannot enter a
    # directional test at all"; both the claim and this probe were wrong.
    # See docs/pdc-c6-direction-audit.md.
    rows, dollars = con.execute("""
        SELECT COUNT(*), SUM(portion_of_amount) FROM pdc_ie_targets
        WHERE candidate_office_type = 'Legislative'
          AND election_year BETWEEN 2018 AND 2024""").fetchone()
    d["pdc_c63_rows"] = int(rows)
    d["pdc_c63_dollars"] = float(dollars)
    # The DENOMINATOR the "100% of rows" sentence was missing (2026-08-25, referee). All C6.3
    # dollars in the same window, across every office, so the legislative slice can be stated
    # as a share of the directionally-coded record rather than of itself.
    _all_c63 = con.execute("""
        SELECT SUM(portion_of_amount) FROM pdc_ie_targets
        WHERE election_year BETWEEN 2018 AND 2024""").fetchone()[0]
    d["pdc_c63_all_offices_m"] = float(_all_c63) / 1e6
    d["pdc_c63_leg_share_pct"] = 100.0 * d["pdc_c63_dollars"] / float(_all_c63)
    d["pdc_c63_m"] = float(dollars) / 1e6
    # The abstract's "direction-coded on 100% of rows" — a rate, derived rather than
    # trusted: the share of legislative C6.3 rows carrying a For/Against value.
    coded, = con.execute("""
        SELECT 100.0 * COUNT(*) FILTER (WHERE for_or_against IN ('For','Against'))
             / COUNT(*)
        FROM pdc_ie_targets
        WHERE candidate_office_type = 'Legislative'
          AND election_year BETWEEN 2018 AND 2024""").fetchone()
    d["c63_direction_pct"] = float(coded)

    express, electioneering = con.execute("""
        SELECT
          SUM(portion_of_amount) FILTER (
            WHERE report_type IN ('Independent Expenditure',
                                  'Independent Expenditure Ad')),
          SUM(portion_of_amount) FILTER (
            WHERE report_type = 'Electioneering Communication')
        FROM pdc_ie_targets
        WHERE candidate_office_type = 'Legislative'
          AND election_year BETWEEN 2018 AND 2024
          AND for_or_against IN ('For','Against')""").fetchone()
    d["pdc_c63_express_m"] = float(express) / 1e6
    d["pdc_c63_electioneering_m"] = float(electioneering) / 1e6
    d["pdc_c63_electioneering_pct"] = (
        100.0 * float(electioneering) / (float(express) + float(electioneering)))

    # The DIRECTIONAL split within each report type. Finding 3 rests on these two
    # running opposite ways ("express advocacy 69% *for*, electioneering 61%
    # *against*"), which is the stated reason the two are reported apart rather
    # than summed — so the claim that carries the specification decision was
    # itself unchecked until strict_units surfaced the bare `69`/`61`.
    for label, tag in (("express", "expr"), ("electioneering", "elect")):
        filt = ("report_type IN ('Independent Expenditure', "
                "'Independent Expenditure Ad')" if label == "express"
                else "report_type = 'Electioneering Communication'")
        for_m, against_m = con.execute(f"""
            SELECT SUM(portion_of_amount) FILTER (WHERE for_or_against = 'For'),
                   SUM(portion_of_amount) FILTER (WHERE for_or_against = 'Against')
            FROM pdc_ie_targets
            WHERE candidate_office_type = 'Legislative'
              AND election_year BETWEEN 2018 AND 2024
              AND for_or_against IN ('For','Against')
              AND {filt}""").fetchone()
        tot = float(for_m) + float(against_m)
        d[f"c63_{tag}_for_pct"] = 100.0 * float(for_m) / tot
        d[f"c63_{tag}_against_pct"] = 100.0 * float(against_m) / tot

    # The CLAIM, not just the figures: the paper says the two "run in opposite
    # directions", and that is what justifies reporting them apart rather than
    # summed. A numeric probe on 69 and 61 would still pass if both flipped to
    # For-weighted, so the relation is asserted in code.
    if not (d["c63_expr_for_pct"] > 50.0 and d["c63_elect_against_pct"] > 50.0):
        raise SystemExit(
            f"FATAL: Finding 3 says express advocacy runs FOR candidates and "
            f"electioneering AGAINST them, and rests the specification choice on "
            f"it. Measured: express {d['c63_expr_for_pct']:.1f}% for, "
            f"electioneering {d['c63_elect_against_pct']:.1f}% against. The "
            f"sentence no longer describes the data.")

    # The PDC row count on `independent_expenditures`, retained ONLY because the
    # paper's correction note quotes the retired claim ("all but 5 of 4,456
    # rows"). A correction that quotes a figure the data no longer supports is a
    # worse defect than the one it corrects, so the quoted count is asserted too.
    d["pdc_ie_rows"], = con.execute(
        "SELECT COUNT(*) FROM v_independent_expenditures WHERE source <> 'FEC'"
    ).fetchone()

    # The completeness claim the correction rests on. Computed as the MINIMUM
    # fill rate across the four fields rather than one of them, so a single
    # field going sparse fails rather than being averaged away by the others.
    fills = con.execute("""
        SELECT
          100.0 * COUNT(*) FILTER (WHERE candidate_name <> '')        / COUNT(*),
          100.0 * COUNT(*) FILTER (WHERE candidate_filer_id <> '')    / COUNT(*),
          100.0 * COUNT(*) FILTER (WHERE candidate_jurisdiction <> '')/ COUNT(*),
          100.0 * COUNT(*) FILTER (WHERE for_or_against <> '')        / COUNT(*)
        FROM pdc_ie_targets
        WHERE candidate_office_type = 'Legislative'
          AND election_year BETWEEN 2018 AND 2024""").fetchone()
    d["pdc_c63_fill_pct"] = min(float(x) for x in fills)

    # The itemised-expenditure universe behind Finding 2a.
    n, m, coded = con.execute(f"""
        SELECT COUNT(*), SUM(amount)/1e6,
               100.0*SUM(amount) FILTER (WHERE NOT {UNCODED})/SUM(amount)
        FROM candidate_expenditures WHERE election_year BETWEEN 2018 AND 2024""").fetchone()
    d["exp_rows"], d["exp_m"], d["exp_coded_pct"] = int(n), float(m), float(coded)
    d["exp_uncoded_pct"] = 100.0 - float(coded)
    con.close()


PROBES = [
    # --- Appendix C's pre-election cutoff sensitivity + Finding 1's restatement of it
    # (2026-08-29; re-anchored the same day when the primary basis moved to the AUTHORIZED
    # committee universe after a referee's objection). Every value recomputed from
    # PREPIN + CMTE_PIN + CELLS in derive_preelection.
    ("Finding 1 — the cutoff pair, authorized universe",
     r"correlation is essentially unchanged — \*\*\+([\d.]+)\*\* against \*\*\+([\d.]+)\*\*\s*"
     r"full-cycle on the same\s*report-built basis",
     ("pre_r_cong", "fullrep_r_cong"), 0.005),
    ("Appendix C — the cutoff pair and its cell count",
     r"within the (\d+) congressional cells, r = \*\*\+([\d.]+)\*\* using receipts through "
     r"the final\s*pre-election report, against \*\*\+([\d.]+)\*\* on the same report-built "
     r"full-cycle basis",
     ("pre_n_cong", "pre_r_cong", "fullrep_r_cong"), 0.005),
    # The SAME printed 31, bound a second time to the USABLE-cell count: the sentence reads
    # as a same-cell contrast, which is only true while every frame cell carries positive
    # receipts on both sides in both windows. If a re-pin drops a cell from r_pre, this
    # probe fails against the printed count while the one above still passes — the two
    # meanings of one token, asserted separately. (_claim_checks states the same invariant
    # with a more actionable message.)
    ("Appendix C — every congressional cell usable in the pre-election cut",
     r"within the (\d+) congressional cells, r = \*\*\+[\d.]+\*\*",
     "pre_n_usable", 0),
    ("Appendix C — committee-cycle validation counts",
     r"\*\*(\d+) of the (\d+) committee-cycle rows were designation\s*"
     r"P or A as of their cycle\*\*", ("cmte_rows_pa", "cmte_rows_total"), 0),
    ("Appendix C — the excluded at-cycle leadership PAC's three cells",
     r"\$([\d,]+) / \$([\d,]+) / \$([\d,]+) across\s*2018–2022",
     ("flag_full_1", "flag_full_2", "flag_full_3"), 0.5),
    ("Appendix C — the everything-but-J pair, retained as the comparability check",
     r"it gives \*\*\+([\d.]+) / \+([\d.]+)\*\*", ("nonj_pre_r", "nonj_full_r"), 0.005),
    ("Appendix C — the pinned frame's own figure, matched by the non-J report basis",
     r"matching\s*the pinned frame's own \*\*\+([\d.]+)\*\*", "pre_r_cong_pinbasis", 0.005),
    ("Appendix C — report-built reconciliation against the summary totals",
     r"mean absolute difference of \*\*([\d.]+)%\*\* per candidate-cycle \(maximum\s*"
     r"\*\*([\d.]+)%\*\*\)", ("pre_recon_mean_pct", "pre_recon_max_pct"), 0.005),
    ("Appendix C — the state-legislative itemized analogue",
     r"resolves finance rows by exact amount for \*\*(\d+)\*\* of \*\*(\d+)\*\* legislative\s*"
     r"cells \(\*\*(\d+)\*\* usable after one zero-side drop\) and moves "
     r"\*\*\+([\d.]+) → \+([\d.]+)\*\*",
     ("leg_resolved_n", "leg_total_n", "leg_item_n", "leg_item_full_r", "leg_item_pre_r"),
     0.005),
    ("Appendix C — non-comparability with Finding 1's legislative correlation",
     r"not comparable to Finding 1's within-legislative \+([\d.]+)\*\*",
     "r_fin_leg", 0.005),
    ("Appendix C — the cutoff's own movement on the itemized measure",
     r"moves the itemized correlation by \*\*([\d.]+)\*\*", "leg_item_delta", 0.0015),

    ("frontmatter — the scorable count in the reproduction note",
     r"and all \*\*(\d+)\*\* scorable district-cycles\s*reconcile", "fed_scorable_n", 0.5),
    ("Finding 3 — the retired 100% restated in the correction note",
     r"earlier version bolded the (\d+)% as though it measured c",
     "pdc_c63_fill_pct", 0.05),
    ("Finding 3 — the C6.3 denominator the 100% sentence was missing",
     r"C6\.3 carries \*\*\$([\d.]+)M\*\* across all offices, so the legislative\s*"
     r"slice is \*\*([\d.]+)%\*\*",
     ("pdc_c63_all_offices_m", "pdc_c63_leg_share_pct"), 0.05),
    # --- The identification-search section, 2026-08-25 (referee item 1) ------------------
    ("Finding 3 — the congressional repeat-matchup count",
     r"of \*\*(\d+)\*\* congressional D-versus-R district-cycles,\s*\*\*(\d+)\*\* are repeats",
     ("idsearch_fed_cycles", "idsearch_fed_repeats"), 0.5),
    ("Finding 3 — the differenced observations a Levitt design would give",
     r"the design yields \*\*(\d+)\*\* differenced observations", "idsearch_fed_diffs", 0.5),
    ("Finding 3 — the legislative repeat-matchup counts",
     r"of \*\*(\d+)\*\* legislative D-versus-R district-cycles\s*only \*\*(\d+)\*\* are "
     r"repeats — \*\*(\d+)\*\* in the House and \*\*(\d+)\*\* in the Senate",
     ("idsearch_leg_cycles", "idsearch_leg_repeats", "idsearch_leg_house_repeats",
      "idsearch_leg_sen_repeats"), 0.5),
    # The redraw count is spelled as a WORD in the paper ("exactly **one** redraw"), which a
    # numeric probe cannot capture -- so the count is checked by `_claim_checks` and only the
    # district figure is probed here. Splitting them rather than renumbering the prose: "one"
    # is the right word in that sentence and a bolded "1" would read worse.
    ("Finding 3 — every scorable district observed either side of the redraw",
     r"redraw inside this panel, and \*\*all (\d+)\*\* scorable",
     "idsearch_both_sides", 0.5),
    ("Finding 3 — the two treated races the federal panel discards",
     r"\(cd10 2020, \+\$([\d.]+)M; cd04\s+2024, \+\$([\d.]+)M\)",
     ("unsc_cd10_20_net", "unsc_cd04_24_net"), 0.02),
    # --- Appendix F's errata table, 2026-08-25. Every figure it restates is bound to the
    # SAME key as its live counterpart elsewhere in the paper. That is the whole point of
    # consolidating: a correction history is a table of figures, and a table of figures that
    # nothing checks is how a retired value comes back to life. Three of this paper's
    # corrections were exactly that shape.
    ("appendix F — the C6.3 direction share restated",
     r"section \*\*C6\.3\*\*, on (\d+)% of rows", "c63_direction_pct", 0.05),
    ("appendix F — the retired and restored legislative cell counts",
     r"zero-treatment cells \(n=(\d+)\) \| restored to the full (\d+);",
     ("_prev_leg_matched_n", "_prev_leg_matched_n_plus2"), 0),
    ("appendix F — the retired and live primary slopes",
     r"primary slope \+([\d.]+) → \+([\d.]+)",
     ("_prev_leg_slope", "leg_expr_matched_slope"), 0.005),
    # --- Inference sensitivity and the clean legislative subset, 2026-08-25 (referee) ----
    ("Finding 2c — HC3 and the analytic cluster-robust intervals",
     r"gives \*\*−([\d.]+) to \+([\d.]+)\*\*\. An analytic cluster-robust standard error on "
     r"the same ten\s+districts gives \*\*−([\d.]+) to \+([\d.]+)\*\*",
     ("inf_hc3_lo_abs", "inf_hc3_hi", "inf_cr_lo_abs", "inf_cr_hi"), 0.005),
    ("Finding 2c — the wild cluster bootstrap p-value",
     r"returns\s+\*\*p = ([\d.]+)\*\*", "inf_wild_p", 0.02),
    # The two restatements of the legislative panel's n in the subset paragraph. Bound to
    # the derived cell count, not exempted: "129" is the number the whole comparison is
    # against, and a fourth copy of it is a fourth thing to update.
    ("Finding 3 — the legislative n restated in the subset paragraph",
     r"stop leaning on (\d+) cells and exploit the cl", "leg_all_matched_n", 0.5),
    ("Finding 3 — the legislative n restated again in the same paragraph",
     r"more sharply than the (\d+)-cell headline can", "leg_all_matched_n", 0.5),
    ("Finding 3 — the cleanly assigned Senate subset",
     r"the cleanly assigned panel is\s*\*\*(\d+)\*\* district-cycles — below the "
     r"\*\*(\d+)\*\* at which",
     ("sen_n", "sen_min_n_threshold"), 0.5),
    ("Finding 3 — how little treatment the clean subset carries",
     r"largest net advantage in any Senate cell is about \*\*\$(\d+)K\*\* and \*\*(\d+)\*\* of "
     r"the\s+9 sit within a thousand dollars of zero",
     ("sen_max_net_k", "sen_nearzero"), 0.6),
    ("Finding 3 — the clean subset's descriptive slopes",
     r"run from\s+\*\*−([\d.]+)\*\* to \*\*\+([\d.]+)\*\* across the four",
     ("sen_slope_min_abs", "sen_slope_max"), 0.02),
    # Appendix C's receipts-window disclosure, 2026-08-25 (second external referee).
    # RETIRED 2026-08-29: the sentence this probe anchored — "testing whether the **+0.60**
    # survives one requires re-pulling FEC data" — was replaced by the completed test
    # itself. The caveat no longer restates the headline; it reports the cutoff result,
    # whose probes sit at the top of this list, and the does-not-carry wording is
    # guarded in _claim_checks against the pre/full gap widening.
    ("appendix C — the receipts window, one row per candidate-cycle",
     r"\*\*one summary row per candidate-cycle\*\*\s*\((\d+) of (\d+) Washington",
     ("rb_rows", "rb_rows"), 0.5),
    ("appendix C — how far apart the two sides of the ratio are measured",
     r"of (\d+) district-cycles with\s*"
     r"both a Democratic and a Republican filer,\s*\*\*(\d+)\*\* differ by more than 60 days "
     r"and one by \*\*(\d+)\*\*, against a mean gap of \*\*([\d.]+)\*\* days",
     ("rb_pairs", "rb_gap_over_60", "rb_worst_gap", "rb_mean_gap"), 0.05),
    # --- Finding 2c's functional-form block, 2026-08-25 (second external referee) --------
    # The functional-form paragraph restates the LOO minimum as the thing the compressed
    # forms do NOT reproduce. Same key as the leave-one-out probe below, deliberately: two
    # copies of one figure is how they drift apart, and this paper has already lost that bet
    # three times in Appendix E.
    ("Finding 2c — the raw-dollar LOO minimum, restated in the form block",
     r"rather than flipping it to −([\d.]+)\. The cancellation assump",
     "fed_loo_min_abs", 0.005),
    ("Finding 2c — what net-IE cancellation discards",
     r"gross\s+IE across these 34 races is \*\*\$([\d.]+)M\*\* against a summed absolute net "
     r"of \*\*\$([\d.]+)M\*\*, so\s+\*\*([\d.]+)%\*\* of the money cancels",
     ("ff_gross_m", "ff_absnet_m", "ff_cancel_pct"), 0.05),
    ("Finding 2c — WA-08 2022, the race cancellation hides",
     r"WA-08 2022 turns \*\*\$([\d.]+)M\*\* of two-sided expenditure into\s+"
     r"\*\*−\$([\d.]+)M\*\* net — \*\*([\d.]+)%\*\* surviving",
     ("ff_wa08_22_total", "ff_wa08_22_net_abs", "ff_wa08_22_survive_pct"), 0.05),
    ("Finding 2c — the coded-untreated races are genuine zeros",
     r"The \*\*(\d+)\*\* races the specification codes as\s+untreated",
     "ff_zero_n", 0.5),
    ("Finding 2c — the compressed forms keep a positive estimate without WA-08 2018",
     r"leaves the\s+point estimate positive \(\*\*\+([\d.]+)\*\*, \*\*\+([\d.]+)\*\*\)",
     ("ff_asinh_loo_drop_wa0818", "ff_slog_loo_drop_wa0818"), 0.005),
    ("Finding 2c — the two sides entered separately",
     r"roughly equal and opposite coefficients \(\*\*\+([\d.]+)\*\*\s*"
     r"pro-Democratic, \*\*−([\d.]+)\*\* pro-Republican\)",
     ("ff_prodem_coef", "ff_prorep_coef_abs"), 0.005),
    ("Finding 2c — intensity adds nothing beside direction",
     r"intensity is \*\*−([\d.]+)\*\* with an interval\s+spanning zero while net advantage "
     r"is \*\*\+([\d.]+)\*\*",
     ("ff_total_coef_abs", "ff_net_with_total"), 0.005),
    # ---- abstract, which restates Finding 1 and the ceiling
    ("abstract — cell universe and the three top correlates",
     r"Across (\d+) Washington\s+legislative and congressional races from 2018 to 2024, the "
     r"ratio of Democratic to\s+Republican fundraising correlates with candidate "
     r"overperformance at \*\*\+([\d.]+)\*\*, the\s+strongest of any measured factor, ahead "
     r"of incumbency \(\+([\d.]+)\) and candidate quality\s+\(\+([\d.]+)\)",
     ("cells_scorable", "r_fin", "r_inc", "r_quality"), 0.005),
    ("abstract — legislative panel scale",
     r"\*\*\$([\d.]+)M of PDC independent expenditure across (\d+) scorable\s+"
     r"district-cycles, direction-coded on 100% of rows\*\*",
     ("pdc_c63_m", "leg_all_agg_n"), 0.05),
    ("abstract — the specification-dependent sign range",
     r"running from −([\d.]+) to \+([\d.]+) depending on whether electioneering",
     ("leg_all_matched_slope_abs", "leg_expr_matched_slope"), 0.05),
    ("abstract — WA-03 landed on its fundamentals",
     r"Washington's 3rd in 2024, finished ([\d.]+) points from its fundamentals",
     "wa03_residual_pp", 0.005),
    # --- Full-paper coverage, 2026-08-14 --------------------------------------
    ("abstract — the 2c slope and its interval",
     r"returns \*\*\+([\d.]+) points of residual per \$1M of net\s+pro-Democratic IE with a\s+"
     r"case-resampling bootstrap interval spanning −([\d.]+) to \+([\d.]+)\*\*",
     ("_slope2c", "_ci_lo_abs", "_ci_hi"), 0.05),
    ("abstract — the direction-coded share",
     r"direction-coded on (\d+)% of rows", ("c63_direction_pct",), 0.05),
    ("limits — the allocation-coverage denominator",
     r"Coverage is 40 of (\d+) legislative baseline cel", ("cells_leg",), 0),
    ("limits — the C6.3 panel restated",
     r"the \$([\d.]+)M panel is in and contributes (\d+) scorable district-cycles",
     ("pdc_c63_m", "leg_all_agg_n"), 0.05),
    ("appendix C — the meta-sentence naming the near-collision",
     r"A (\d+) and a (\d+) appear in this paper", ("cells_leg", "fin_cells"), 0),
    ("appendix C — the two 129s, frame side",
     r"Of the (\d+) baseline-scorable cells, \*\*(\d+) are legislative\*\* and "
     r"(\d+)\s+congressional",
     ("cells_scorable", "cells_leg", "cells_cong"), 0),
    ("appendix C — the allocation-coverage 129 is the frame's",
     r"that legislative\s+(\d+) is the denominator in the allocation-coverage limit "
     r"\(\"40 of\s+(\d+)\"\)",
     ("cells_leg", "cells_leg"), 0),
    ("appendix C — the both-side finance count",
     r"\*\*(\d+) of the (\d+) carry both-side finance\*\*",
     ("fin_cells", "cells_scorable"), 0),
    ("end note — the two reproduction-command counts",
     r"across (\d+) race-cycles", ("cells_scorable",), 0),
    ("end note — the legislative reproduction count",
     r"\((\d+) cells, PDC C6\.3\)", ("leg_all_agg_n",), 0),

    # ---- Finding 1
    ("Finding 1 — cell universe", r"Across the (\d+) baseline-scorable Washington",
     "cells_scorable", 0),
    ("Finding 1 — fundraising correlation, both columns",
     r"\| \*\*fundraising, log2\(D receipts / R receipts\)\*\* \| \*\*\+([\d.]+)\*\* "
     r"\*\(n=(\d+)\)\* \| \*\*\+([\d.]+)\*\* \|",
     ("r_fin", "fin_cells", "r_fin"), 0.005),
    ("Finding 1 — incumbency correlation, both columns",
     r"\| incumbency \| \+([\d.]+) \| \+([\d.]+) \|", ("r_inc", "r_inc_common"), 0.005),
    ("Finding 1 — quality correlation, both columns",
     r"\| candidate quality index \| \+([\d.]+) \| \+([\d.]+) \|",
     ("r_quality", "r_quality_common"), 0.005),
    ("Finding 1 — local-trend correlation, both columns",
     r"\| local trend \| \+([\d.]+) \| \+([\d.]+) \|",
     ("r_trend", "r_trend_common"), 0.005),
    ("Finding 1 — midterm common-sample cell",
     r"\| midterm year \| ≈0 \| \+([\d.]+) \|", ("r_midterm_common",), 0.005),
    ("Finding 1 — the common-sample count in the preamble",
     r"finance is\s+present for only \*\*(\d+)\*\* of the (\d+) cells",
     ("fin_cells", "cells_scorable"), 0),
    ("Finding 1 — fundraising-position means",
     r"average of \*\*\+([\d.]+)\*\* points; where funding was even, \*\*\+([\d.]+)\*\*; "
     r"where the Republican\s+out-raised, \*\*−([\d.]+)\*\*",
     ("mean_d_outraised", "mean_even", "mean_r_outraised_abs"), 0.005),
    ("Finding 1 — the pin note's first re-pin narrative",
     r"held \*\*(\d+)\*\* both-side cells and gave\s+\+([\d.]+), \+([\d.]+), \+([\d.]+) "
     r"and −([\d.]+); loading more filings took it to (\d+) and \+(\d+\.\d+)",
     ("_prev_cells", "_prev_fin", "_prev_d", "_prev_even", "_prev_r",
      "fin_cells_oldpin", "r_fin_oldpin"), 0.005),
    ("Finding 1 — the pin note's collision-audit counts",
     r"found (\d+) of (\d+) lookups\s+attaching the wrong records",
     ("audit_changed", "audit_lookups"), 0),
    ("Finding 1 — the pin note's namesake dollars",
     r"another chamber with \$(\d+)K his namesake never\s+raised",
     ("audit_namesake_k",), 0),
    ("Finding 1 — the pin note's corrected state",
     r"entirely \(\*\*(\d+)\*\* both-side cells\) and moves the\s+correlation to "
     r"\*\*\+([\d.]+)\*\*",
     ("fin_cells", "r_fin"), 0.005),
    ("Finding 1 — universe unchanged in the pin note",
     r"unchanged at (\d+) baseline-scorable cells", "cells_scorable", 0),

    # ---- Referee item (6): the stratification (2026-08-28) --------------------
    # The referee asked whether +0.60 is one relationship or an average over several.
    # Every figure the answer added is probed here rather than exempted to the diag
    # script, because all of them are recomputed from the SAME pinned frame this
    # verifier already reads -- an exemption would have named a script for numbers
    # sitting two lines above their own derivation.
    ("Finding 1 — within-chamber correlations",
     r"within congressional cells r = \*\*\+([\d.]+)\*\* \(n=(\d+)\), within "
     r"legislative cells\s+\*\*\+([\d.]+)\*\* \(n=(\d+)\)",
     ("r_fin_cong", "n_fin_cong", "r_fin_leg", "n_fin_leg"), 0.005),
    ("Finding 1 — within-cycle correlations",
     r"\*\*\+([\d.]+)\*\* in\s+2018, \*\*\+([\d.]+)\*\* in 2020, "
     r"\*\*\+([\d.]+)\*\* in 2022, \*\*\+([\d.]+)\*\* in 2024",
     ("r_fin_2018", "r_fin_2020", "r_fin_2022", "r_fin_2024"), 0.005),
    ("Finding 1 — the incumbency overlap and the partial correlation",
     r"correlates with the incumbency term at \*\*\+([\d.]+)\*\*\. Removing "
     r"incumbency's\s+linear contribution from both sides takes fundraising from "
     r"\*\*\+([\d.]+)\*\* to \*\*\+([\d.]+)\*\*",
     ("r_fin_inc_overlap", "r_fin_full", "r_fin_partial_inc"), 0.005),
    ("Finding 1 — the selection on missingness",
     r"the \*\*(\d+)\*\* cells that lack one average \*\*\+([\d.]+)\*\*\s+"
     r"points of Democratic overperformance against \*\*\+([\d.]+)\*\* among the "
     r"(\d+) that have it",
     ("cells_no_ratio", "mean_op_without_ratio", "mean_op_with_ratio", "fin_cells"), 0.005),
    ("Finding 1 — the composition of the missing cells",
     r"In \*\*(\d+)\*\*\s+of the 35 only the Democrat filed at all, and \*\*(\d+)\*\* "
     r"of the 35 are legislative",
     ("fin_missing_d_only", "fin_missing_leg"), 0),
    ("Appendix C — why 35 carry no ratio",
     r"of the 35, \*\*(\d+)\*\*\s+carry a row for the Democrat only, \*\*(\d+)\*\* "
     r"for the Republican only, and \*\*(\d+)\*\* for neither",
     ("fin_missing_d_only", "fin_missing_r_only", "fin_missing_neither"), 0),
    ("Appendix C — the legislative share of the missing cells",
     r"\*\*(\d+) of the 35 are legislative\.\*\*", "fin_missing_leg", 0),
    # The three RESTATEMENTS the new prose introduced, probed rather than exempted. A
    # restated constant is the defect shape this paper has already shipped twice -- Appendix
    # E's section exemption was hiding two of them -- and a second copy of a figure is a
    # second thing to update, so each is bound to the same key as its original.
    ("Finding 1 — the both-side count, restated",
     r"\*\*The (\d+) are not a random (\d+)", ("fin_cells", "fin_cells"), 0),
    ("Finding 1 — the headline correlation, restated in the selection paragraph",
     r"So the \+([\d.]+)\s+is measured on the subset", "r_fin", 0.005),
    ("Appendix C — the scorable universe, restated",
     r"Why 35 of the (\d+) carry no ratio", "cells_scorable", 0),

    # ---- Finding 2c influence + clustering (external referee 2026-08-15) -------
    ("Finding 2c — leave-one-out extremes",
     r"runs from \*\*−([\d.]+)\*\*\s+\(dropping WA-08 2018\) to \*\*\+([\d.]+)\*\* "
     r"\(dropping WA-03 2024\)",
     ("fed_loo_min_abs", "fed_loo_max"), 0.005),
    ("Finding 2c — Cook's distance and the drop-all-WA-08 slope",
     r"carries a Cook's distance of \*\*([\d.]+)\*\* in a\s+34-observation regression; "
     r"dropping every WA-08 observation gives \*\*−([\d.]+)\*\*",
     ("fed_cooks_max", "fed_no_cd08_slope_abs"), 0.005),
    ("Finding 2c — the district-clustered interval",
     r"\*\*district-clustered bootstrap\*\* \(10 clusters\) is\s+reported beside it: "
     r"\*\*−([\d.]+) to \+([\d.]+)\*\*",
     ("fed_cluster_lo_abs", "fed_cluster_hi"), 0.005),
    ("Finding 2c — the era-clustered interval",
     r"redistricting boundary \(20 clusters\) gives −(\d+\.\d+) to \+(\d+\.\d+)",
     ("fed_era_cluster_lo_abs", "fed_era_cluster_hi"), 0.005),
    ("Finding 2c — the per-SD slope",
     r"is\s+\*\*\+([\d.]+) points per one standard deviation of net IE\*\* "
     r"\(SD = \$([\d.]+)M in this panel\)",
     ("fed_per_sd_slope", "fed_sd_x"), 0.005),
    ("abstract — the leverage sentence",
     r"deleting one race\s+\(WA-08 2018, Cook's distance ([\d.]+)\) moves it to "
     r"\*\*−([\d.]+)\*\*, and a district-clustered\s+bootstrap widens the interval to "
     r"\*\*−([\d.]+) to \+([\d.]+)\*\*",
     ("fed_cooks_max", "fed_loo_min_abs", "fed_cluster_lo_abs", "fed_cluster_hi"), 0.05),
    ("limits — the leverage bullet",
     r"deleting the single highest-leverage race \(WA-08 2018, Cook's distance "
     r"([\d.]+)\)\s+moves it to −(\d+\.\d+)",
     ("fed_cooks_max", "fed_loo_min_abs"), 0.005),

    # ---- Finding 2a, the itemised-expenditure universe
    ("Finding 2a — expenditure universe",
     r"([\d,]+) candidate rows 2018–2024, \$(\d+)M, ~(\d+)% of\s+dollars carrying a code",
     ("exp_rows", "exp_m", "exp_coded_pct"), 0.5),
    ("Finding 2a — share correlations with the residual",
     r"field \*\*\+([\d.]+)\*\*, media\s+\*\*\+([\d.]+)\*\*, professional "
     r"\*\*−([\d.]+)\*\*", ("r_field", "r_media", "r_prof_abs"), 0.005),
    ("Finding 2a — total spend correlation",
     r"Total spend correlates at \+([\d.]+)", "r_totalspend", 0.005),
    ("Finding 2a — allocation persistence across cycles",
     # (\d+\.\d+) rather than ([\d.]+): the media figure ends a sentence, and a greedy
     # character class swallows the full stop and captures "0.998." — see the harness's
     # non-numeric guard, which exists because that killed a whole run.
     r"field-share persistence across cycles runs r = (\d+\.\d+) and media-share\s+"
     r"r = (\d+\.\d+)", ("persist_field", "persist_media"), 0.005),
    ("Finding 2a — field share against raw overperformance",
     r"field share correlates \*\*−([\d.]+)\*\* with\s+raw overperformance",
     "r_field_overperf_abs", 0.005),
    ("limits — uncoded dollar share",
     r"(\d+)% of expenditure dollars carry no purpose code", "exp_uncoded_pct", 0.5),

    # ---- Finding 2c / Finding 3, the two directional panels
    ("Finding 2c — WA-03 total and net IE",
     r"attracted \$([\d.]+)M in total independent expenditure — the\s+largest in the panel, "
     r"and \d+.. nationally among the \d+ U\.S\. House races drawing any — with\s+"
     r"a net \$([\d.]+)M advantage on the Democratic side\. It finished ([\d.]+) points from "
     r"its\s+fundamentals-based prediction",
     ("wa03_total_m", "wa03_net_m", "wa03_residual_pp"), 0.05),
    # The per-cycle inventory is now a TABLE, so each row is probed on its own.
    # Written as one regex over the whole table rather than four independent
    # ones so a row silently deleted from the table fails here rather than
    # simply going unchecked.
    # The open cycle's row now carries its AS-OF DATE inside the table, and the date is
    # captured here rather than exempted as provenance: the three date groups are asserted
    # against the pin, so rewording the date without re-pinning FAILS instead of reading as
    # a harmless caption. Same coupling as verify_who_decides_wa.py's Appendix A panel date.
    ("Finding 3 — the cycle inventory table",
     r"\| 2018 \| (\d+) \| \$([\d.]+)M \|.*?"
     r"\| 2020 \| (\d+) \| \$([\d.]+)M \|.*?"
     r"\| 2022 \| (\d+) \| \$([\d.]+)M \|.*?"
     r"\| 2024 \| \*\*(\d+)\*\* \| \*\*\$([\d.]+)M\*\* \|.*?"
     r"\| 2026 \(as of (\d{4})-(\d{2})-(\d{2})\) \| \*\*(\d+)\*\* \| \*\*\$(\d+)K\*\* \|",
     ("ie2018_rows", "ie2018_m", "ie2020_rows", "ie2020_m",
      "ie2022_rows", "ie2022_m", "ie2024_rows", "ie2024_m",
      "ie_asof_y", "ie_asof_m", "ie_asof_d",
      "ie2026_rows", "ie2026_k"), 1.0),
    # COMPLETED CYCLES ONLY (2026-08-24). This cell counted all five cycles and so drifted
    # every time an open-cycle filing landed -- which, since the weekly refresh task, happens
    # with no human in the loop. The completed-cycle panel is also the one the analysis uses:
    # all 34 scorable races are 2018-2024.
    ("Finding 3 — the panel totals",
     r"\*\*([\d,]+)\s+flagged rows across all ten districts and \$([\d.]+)M\*\*",
     ("ie_total_rows", "ie_total_m"), 0.05),
    # The same total restated in Appendix E, previously a SECOND unprobed copy of the
    # constant. Two hand-written copies of one figure is how they drift apart.
    # ⚠ THIRD FIGURE THIS SECTION'S BLANKET EXEMPTION HAS HIDDEN (2026-08-25, external
    # referee). Appendix E restates the open cycle's row, and it still said 50 rows after
    # Finding 3 was re-derived to 69 and PINNED the day before -- in the same paper, under a
    # paragraph promising the row "cannot drift under the paper unnoticed". It drifted,
    # because a second copy of a figure is a second thing to update and nothing was pointed
    # at this one. Now bound to the SAME keys as the inventory table, so the two cannot
    # disagree. See the exemption note above: a section-level reason absorbs every figure in
    # the section, and this section keeps having ordinary restated constants dropped into it.
    ("Appendix E — the open cycle restated, bound to the pin",
     r"it carries \*\*(\d+)\*\* flagged rows as of \*\*(\d{4})-(\d{2})-(\d{2})\*\*",
     ("ie2026_rows", "ie_asof_y", "ie_asof_m", "ie_asof_d"), 0.5),
    ("Appendix E — the completed-cycle total restated",
     r"\*\*\$([\d,]+)\*\* of the \*\*\$([\d.]+)M\*\* completed-cycle total is\s+"
     r"unresolvable to a side, across \*\*(\d+)\*\* district-cycles",
     ("ie_unresolved_usd", "ie_total_m", "ie_unresolved_cells"), 0.5),
    # The correction passages. The RETIRED figure is asserted as a literal — the
    # note's job is to keep saying what the defective load reported — while the
    # corrected figure beside it is asserted against the live derivation, so a
    # re-derivation that moved would fail here rather than leave the correction
    # quietly describing a number no longer on disk.
    ("Finding 2c — the retired inflated figure, in the correction note",
     r"House race in the country\" at \$([\d.]+)M", "_wa03_inflated", 0.05),
    ("Finding 2c — the corrected figure, in the correction note",
     r"At the true \$([\d.]+)M the race ranks 22nd; at the doubled \$([\d.]+)M",
     ("wa03_total_m", "_wa03_inflated"), 0.05),
    ("Finding 3 — the defect restated with both figures",
     r"reported as \$([\d.]+)M against a true \$([\d.]+)M",
     ("_wa03_inflated", "wa03_total_m"), 0.05),
    ("Finding 3 — the superlative's arithmetic",
     r"at \$([\d.]+)M nothing exceeded\s+it, and at the correct \$([\d.]+)M",
     ("_wa03_inflated", "wa03_total_m"), 0.05),
    ("Finding 3 — the interval restated",
     r"the interval in 2c,\s*which spans −(\d+\.\d+) to \+(\d+\.\d+)",
     ("_ci_lo_abs", "_ci_hi"), 0.001),
    # ---- Finding 3, the state-legislative directional panel.
    # These replace the old "PDC IE total and flag coverage" / "the five flagged
    # PDC rows" probes, which asserted a claim that was FALSE: that the money
    # carried no direction. It carries direction on 100% of rows, in the C6.3
    # section the loader had never read. See docs/pdc-c6-direction-audit.md.
    ("Finding 3 — the legislative universe",
     r"records \*\*\$([\d,.]+)\*\* of\s+independent expenditure identifying a legislative\s+"
     r"candidate across 2018–2024, on \*\*([\d,]+)\*\* filed rows",
     ("pdc_c63_dollars", "pdc_c63_rows"), 0.05),
    ("Finding 3 — scorable district-cycles",
     r"that yields \*\*(\d+) scorable district-cycles\*\*", "leg_all_agg_n", 0),
    # One regex over the whole table, per the precedent set by the five-cycle
    # inventory probe above: a row silently deleted fails here rather than
    # simply going unchecked.
    ("Finding 3 — the four-specification table",
     r"\| \*\*express advocacy, race-matched\*\* \| (\d+) \| (\d+) \| \*\*\+([\d.]+)\*\* \| "
     r"−([\d.]+) to \+([\d.]+) \| −([\d.]+) to \+([\d.]+) \| \+([\d.]+) \|.*?"
     r"\| express advocacy, district-aggregate \| (\d+) \| (\d+) \| −([\d.]+) \| "
     r"−([\d.]+) to \+([\d.]+) \| −([\d.]+) to \+([\d.]+) \| −([\d.]+) \|.*?"
     r"\| all directional, race-matched \| (\d+) \| (\d+) \| −([\d.]+) \| "
     r"−([\d.]+) to \+([\d.]+) \| −([\d.]+) to \+([\d.]+) \| −([\d.]+) \|.*?"
     r"\| all directional, district-aggregate \| (\d+) \| (\d+) \| \+([\d.]+) \| "
     r"−([\d.]+) to \+([\d.]+) \| −([\d.]+) to \+([\d.]+) \| \+([\d.]+) \|",
     ("leg_expr_matched_n", "leg_expr_matched_material", "leg_expr_matched_slope",
      "leg_expr_matched_ci_lo_abs", "leg_expr_matched_ci_hi",
      "leg_expr_matched_cluster_lo_abs", "leg_expr_matched_cluster_hi",
      "leg_expr_matched_r",
      "leg_expr_agg_n", "leg_expr_agg_material", "leg_expr_agg_slope_abs",
      "leg_expr_agg_ci_lo_abs", "leg_expr_agg_ci_hi",
      "leg_expr_agg_cluster_lo_abs", "leg_expr_agg_cluster_hi", "leg_expr_agg_r_abs",
      "leg_all_matched_n", "leg_all_matched_material", "leg_all_matched_slope_abs",
      "leg_all_matched_ci_lo_abs", "leg_all_matched_ci_hi",
      "leg_all_matched_cluster_lo_abs", "leg_all_matched_cluster_hi",
      "leg_all_matched_r_abs",
      "leg_all_agg_n", "leg_all_agg_material", "leg_all_agg_slope",
      "leg_all_agg_ci_lo_abs", "leg_all_agg_ci_hi",
      "leg_all_agg_cluster_lo_abs", "leg_all_agg_cluster_hi", "leg_all_agg_r"), 0.005),
    ("Finding 3 — the zeros-retained correction note",
     r"An earlier\s+version dropped those cells from the race-matched rows \(n = 127\), "
     r"treating zero treatment\s+as missing data; the correction, prompted by an external "
     r"referee, moved the primary slope\s+from \+([\d.]+) to \+([\d.]+)",
     ("_prev_leg_slope", "leg_expr_matched_slope"), 0.005),
    ("Finding 3 — the standardized cross-panel comparison",
     r"one\s+standard deviation of net IE moves the point estimate \*\*\+([\d.]+)\*\* "
     r"points in the federal\s+panel \(SD \$([\d.]+)M\) against \*\*\+([\d.]+)\*\* "
     r"points in the primary legislative specification\s+\(SD \$([\d.]+)M\)",
     ("fed_per_sd_slope", "fed_sd_x", "leg_expr_matched_per_sd_slope",
      "leg_expr_matched_sd_x"), 0.005),
    # The "100% of them" claim is the one that replaced the false ceiling, so it
    # is probed rather than exempted: if C6.3's fill rate ever fell below 100 the
    # paper's central correction would be overstating the record it corrected to.
    ("Finding 3 — the advocacy split",
     r"\$([\d.]+)M against \$([\d.]+)M — and the two run in opposite directions",
     ("pdc_c63_electioneering_m", "pdc_c63_express_m"), 0.05),
    # The two figures that carry the specification decision. "Opposite
    # directions" is a CLAIM ABOUT the figures, so it is asserted structurally
    # below as well as numerically here.
    ("Finding 3 — express advocacy is For-weighted, electioneering Against-weighted",
     r"express\s+advocacy (\d+)% \*for\* candidates and electioneering (\d+)% \*against\* them",
     ("c63_expr_for_pct", "c63_elect_against_pct"), 0.5),
    ("Findings 2/3 — the bootstrap's printed confidence level against its tails",
     r"(\d+)% bootstrap", "boot_level_pct", 0),
    ("Finding 3 — the cluster column header carries the same level",
     r"district-cluster (\d+)% \| Pearson", "boot_level_pct", 0),
    ("Finding 3 — the materiality floor in the table header against MATERIAL_M",
     r"cells with ≥\$(\d+)K", "material_floor_k", 0),
    ("Finding 2 — the slope's money scaling against the panel's denomination",
     r"(?:points(?: of residual)? per|causal effect of|width: a) \$(\d+)M", "slope_unit_musd", 0),
    ("Finding 3 — the materiality band across the four specifications",
     r"[Oo]nly (\d+)–(\d+)% of cells attract\s+any material independent expenditure",
     ("leg_material_pct_lo", "leg_material_pct_hi"), 0.5),
    ("Finding 1 — the two-sample table header",
     r"\| factor \| full sample \(n=(\d+)\) \| common sample \(n=(\d+)\) \|",
     ("cells_scorable", "fin_cells"), 0),
    ("Finding 3 — the zeros note runs on the full universe",
     r"runs on the full (\d+)-cell scorable universe", ("leg_expr_matched_n",), 0),
    ("Finding 3 — the zeros note's historical pair",
     r"race-matched rows \(n = (\d+)\), treating zero treatment",
     ("_prev_leg_matched_n",), 0),
    ("Finding 2c — the leverage case's IE and residual",
     r"pairs the panel's largest net pro-Democratic IE\s+\(\+\$([\d.]+)M\) with a "
     r"\+([\d.]+)-point residual",
     ("fed_max_net_ie", "fed_max_net_resid"), 0.005),
    ("appendix C — the audit figures restated in the linkage bullet",
     r"measured\s+the damage at (\d+) of (\d+) lookups",
     ("audit_changed", "audit_lookups"), 0),
    ("appendix C — the namesake dollars restated",
     r"\*\*same-name namesake's\*\* \$(\d+)K from another chamber",
     ("audit_namesake_k",), 0),
    ("appendix C — the broken coincidence, both values",
     r"were equal by coincidence \(both (\d+)\) until the 2026-08-15",
     ("_prev_leg_matched_n_plus2",), 0),
    ("Finding 3 — the retracted flag claim, quoted in the correction note",
     r"on all but 5 of ([\d,]+) rows", "pdc_ie_rows", 0),
    ("Finding 3 — the legislative panel restated in 'what more cycles would fix'",
     r"multiplies the cells by nearly four, to (\d+)", "leg_all_agg_n", 0),
    ("limits — fundraising correlation restated",
     r"no instrument\. The \+([\d.]+) correlation", "r_fin", 0.005),
    ("Appendix A — fundraising correlation restated in objection 1",
     r"\*\*1\. \"You found \+([\d.]+) and then explained it away\.\"\*\*", "r_fin", 0.005),
        ("Appendix C — cell universe restated twice",
     r"restricted to the \*\*(\d+) baseline-scorable cells\*\*", "cells_scorable", 0),
    ("Appendix C — the same 163 used by the backtest",
     r"the same (\d+) used by the published backtest", "cells_scorable", 0),
    # The estimator statement (2026-08-15): B is read out of the IE scripts' own
    # source by derive_estimator_facts, so the paper's replicate count cannot
    # drift from the code that produces the intervals.
    ("Appendix C — bootstrap replicate count, from the scripts' source",
     r"percentile bootstrap with ([\d,]+) replicates", "mv_bootstrap_iters", 0),
    ("Appendix A — WA-03 restated",
     r"landing ([\d.]+) points from its fundamentals", "wa03_residual_pp", 0.005),
]

# Sections closed by a written reason rather than a derivation (2026-08-14, full-paper
# coverage). Each reason names where the figures ARE verified — the audit-log rule.
COVERAGE_EXEMPT_SECTIONS = {
    "appendixD":
        "A bibliography. Its numeric tokens are page ranges, volume/issue numbers and DOIs "
        "— citations, not quantities; the figures those works are cited for are asserted "
        "where the paper uses them. The WA paper's Appendix D closure.",
    "appendixE":
        "The full IE cross-section: the pinned panel printed in full, one row per "
        "district-cycle, whose residual column only the forecast model produces. Owned by "
        "scripts/diag_ie_vs_margin.py (named in UNCHECKED); the pinned frame is "
        "docs/reference/ie_vs_residual_2026-08-09.csv, its statistics are recomputed and "
        "asserted in Finding 2c's probes, and verify_whitepaper.py cross-checks the "
        "restatements. Re-deriving 34 model residuals here would fork the model rather "
        "than check it. "
        "⚠ NARROWED IN PRACTICE 2026-08-24: a SECTION-level exemption covers everything in "
        "the section, not only the thing it is about, and this one was shielding two "
        "ordinary restated constants that had nothing to do with model residuals -- the "
        "completed-cycle panel total (a second, unprobed copy of Finding 3's figure) and the "
        "unresolvable-to-a-side numerator, which had drifted to a value no basis reproduced. "
        "Both are now probed individually above. The exemption stays for the 34-row table "
        "itself; if another prose figure is added to this section, PROBE IT rather than "
        "letting this reason absorb it.",
}

UNCHECKED = [
    "Finding 2a's cross-cycle holdout R² table (0.000 / 0.013 / 0.026 / 0.022) and the "
    "in-sample 0.039 -> 0.105 rise — these FIT and SCORE a regression, so checking them means "
    "re-running the fit rather than reading a value; scripts/diag_expenditures_vs_residual.py "
    "owns them. Note the narrowness: the block's correlations, persistence coefficients and "
    "field-vs-overperformance figure are NOT exempt and are asserted above. An earlier version "
    "of this list waived all of Finding 2a, which left seven checkable figures unchecked "
    "because four of their neighbours were not. The holdout values above were confirmed "
    "against a fresh run on 2026-08-01; they cannot be pinned the way the correlations are, "
    "because the fit needs the candidate-quality components and the frame does not carry "
    "them. The correlations that ARE pinned share the frame, so a basis change surfaces "
    "here first",
    "Finding 2c's slope, bootstrap interval and Pearson r (+0.515, [−0.600, +2.821], r=+0.186, n=34) — regressed on a fundamentals-net "
    "residual only the forecast model produces. verify_whitepaper.py already asserts that "
    "the white paper's restatement of them matches THIS paper, which is the cross-document "
    "check that matters; the independent derivation is scripts/diag_ie_vs_margin.py",
    "Finding 2b is a description of a modelling decision, not a measurement — the "
    "post-redistricting attenuation is locked in by TestPostRedistrictingAttenuation in "
    "tests/test_analysis/test_national_model.py, which is where a change to it would fail",
    "The §J longshot-share figure (4.8%) belongs to cross-state-fec-money.md and is derived "
    "by scripts/diag_loser_side_money.py",
]



# --- Coverage gate (ported 2026-08-06; see verify_who_decides_wa) --------------
# The result sections, partitioned so no slice overlaps another: spans are
# per-section coordinates, so a slice that swallows another reports the inner
# one's probed cells as unmapped.
#
# EXTENDED TO THE WHOLE PAPER 2026-08-14 (full-paper coverage round): the three
# findings covered under half the paper's numeric content; the abstract carried
# probes but no completeness demand, which is the gap the series' abstract
# defects lived in. Partitioned title to companion links, the WA standard.
AUDIT_BOUNDS = {
        "frontmatter": ("# Does Money Move Votes in Washington?", "## Abstract"),
        "abstract": ("## Abstract", "## The question"),
        "question": ("## The question", "## Finding 1"),
        "finding1": ("## Finding 1", "## Finding 2"),
        "finding2": ("## Finding 2", "## Finding 3"),
        "finding3": ("## Finding 3", "## What it means"),
        "meaning": ("## What it means", "## What this paper does not claim"),
        "limits": ("## What this paper does not claim", "## Appendix A"),
        "appendixA": ("## Appendix A", "## Appendix B"),
        "appendixB": ("## Appendix B", "## Appendix C"),
        "appendixC": ("## Appendix C", "## Appendix D"),
        "appendixD": ("## Appendix D", "## Appendix E"),
        "appendixE": ("## Appendix E", "## Appendix F"),
        # Added 2026-08-25 with the errata consolidation. The correction history moved out of
        # Findings 1 and 2a into its own appendix -- referee 2's call, and both referees agreed
        # it should stop being scattered. It is INSIDE the coverage gate, not exempted: the
        # retired figures it records are historical literals, and a section full of them is
        # exactly where a live figure could hide unnoticed.
        "appendixF": ("## Appendix F", "## End note"),
        # EXTENDED 2026-08-26 (item 9a). This ended at "This is Paper #4 …", which stopped one
        # sentence short of the document and left the series pointer in no span at all — the
        # only gap in this paper, and `scripts/diag_audit_span_gaps.py` counted its single
        # numeric token. Cheap to close and worth closing: a series pointer is where a paper
        # states its own position in the sequence, and the sequence has been renumbered once.
        "endnote": ("## End note", "(the four-state money layer)."),
    }

COVERAGE_EXEMPT = [
    (r"^(?:19|20)\d{2}$", "a calendar year, not a result"),
    (r"^\d{1,2}$", "small integer — list ordinals, chamber ids, column counts"),
]
COVERAGE_EXEMPT_LITERAL: dict[str, str] = {
    # A confidence LEVEL, not a result. Every interval in this paper is 95%; the number
    # describes the estimator's convention, and there is nothing in the data to compare it to.
    "95": "the confidence level of the reported intervals, not an estimate",
    # The holdout-R2 table and the IE cross-section are declared in UNCHECKED and
    # owned by the diagnostics the submission checklist re-runs before upload
    # (diag_ie_vs_margin.py and the holdout script). Exempted by REASON, naming
    # the owner -- not because they are "not results", which they plainly are.
    "0.000": "holdout table cell; owned by the holdout diagnostic (UNCHECKED)",
    "0.015": "holdout table cell (squared holdout correlation); as above",
    "0.031": "holdout table cell; as above",
    "0.028": "the allocation-alone holdout cell AS A TABLE CELL; the same value "
             "restated in the pin note's 0.041 -> 0.022 -> 0.028 history IS "
             "asserted, so a drift would still fail there",
    "1.09": "predictive R2 table cell (negative; sign is prose), owned by the "
            "holdout diagnostic — the 2026-08-15 metric split (referee item 7)",
    "2.75": "predictive R2 table cell; as above",
    "3.00": "predictive R2 table cell; as above",
    "0.18": "predictive R2 table cell; as above — and the wrong-signed holdout "
            "correlation −0.18 in the r-list sentence, same owner",
    "0.02": "holdout correlation r-list value (+0.02), same owner",
    "0.12": "holdout correlation r-list value (−0.12), same owner",
    "0.17": "holdout correlation r-list value (−0.17), same owner",
    "0.037": "in-sample squared-correlation floor beside the holdout table; as above",
    "0.101": "in-sample squared-correlation ceiling beside the holdout table; as above",
    # The IE regression output. Owned by diag_ie_vs_margin.py, which the submission
    # checklist re-runs immediately before upload — the same arrangement the retired
    # "0.39" entry had, updated for the four-cycle panel. Not derivable here: the
    # residual is model-produced, and re-deriving it would fork the forecast rather
    # than check it (see UNCHECKED).
    # Section identifiers on form C-6, not measurements. They appear in Finding
    # 3's correction note because naming the section is what makes the
    # correction reproducible — a reader has to know which part of the form
    # carries the direction data. Verified structurally instead: the loader's
    # origin filter and its tests (tests/test_etl/test_pdc_ie_targets.py) fail
    # if C6.3 rows stop being what is read.
    "6.3": "form C-6 section identifier (C6.3, Identified Entities), not a figure",
    "6.2": "form C-6 section identifier (C6.2, Itemized Expenditures), not a figure",
    "359": "part of the GitHub account name `skirby359` in the repository URL, not a "
           "figure — the tokenizer sees the digits inside the identifier",
    "4.8": "the §J longshot-side inflow share, owned by cross-state-fec-money.md and "
            "derived by scripts/diag_loser_side_money.py (named in UNCHECKED); quoted in "
            "'What it means' as the cross-paper hand-off",
    "0.515": "IE-vs-residual slope; owned by diag_ie_vs_margin.py (UNCHECKED)",
    "0.186": "IE-vs-residual Pearson r; owned by diag_ie_vs_margin.py (UNCHECKED)",
    "0.600": "lower bootstrap bound on the slope; as above",
    "2.821": "upper bootstrap bound on the slope; as above",
    "0.39": "the RETIRED single-cycle slope and r, quoted in 2c as the estimate this "
            "panel replaced. Historical by construction, like the pin-note literals "
            "in Finding 1 — the sentence's job is to keep saying what the old draft "
            "said, and the live figures beside it ARE asserted",
    # WA-03's national rank cannot be derived here: the warehouse holds no
    # out-of-state IE. _claim_checks guards the superlative negatively, and the
    # rank itself is produced by the bulk cross-check.
    # --- The two secondary tests, added 2026-08-08. Owned by their own scripts for
    # the same reason 2c's slope is: all three regress a fundamentals-net residual
    # that only the forecast model produces, so re-deriving them here would fork the
    # model rather than check it. The submission checklist re-runs both immediately
    # before upload.
    "1.128": "early-window coefficient, joint fit; owned by diag_ie_early_late.py",
    "2.129": "late-window coefficient, joint fit; as above",
    "0.083": "joint-fit R2 for the early/late split; as above",
    "0.753": "corr(net early, net late) among races with money in both windows; as above",
    "0.878": "next-cycle placebo slope; owned by diag_ie_next_cycle_placebo.py",
    "1.108": "contemporaneous comparison on the placebo's own cells; as above",
    "0.716": "placebo slope after the single-race deletion that reverses it; as above",
    "4.415": "contemporaneous slope after its single-race deletion; as above",
    "0.031": "corr(net IE t, net IE t+1) across same-era pairs; as above",
    # Added 2026-08-28 with referee item (10). Same owner and same 14 same-era pairs as
    # 0.031 directly above it: the paper prints the two side by side precisely because the
    # net figure alone could not support a sentence about money rather than direction.
    "0.122": "corr(TOTAL IE t, TOTAL IE t+1) across the same same-era pairs; as above",
    # Not a result: an HTTP status code, in the sentence recording that the WA SoS
    # bulk export serves 2014 and 2016 but not 2012. Verified by request, not derived,
    # and there is nothing in the warehouse it could be asserted against.
    "404": "HTTP status of the WA SoS 2012 results export; an observed response code, "
           "not a figure",
    "387": "count of U.S. House races drawing any IE in 2024; owned by "
           "scripts/diag_fec_ie_bulk_crosscheck.py --national-rank, which reads FEC's "
           "national bulk file (the warehouse is Washington-only)",
}


def _claim_checks(d: dict, norm: str) -> list[str]:
    """Assertions about CLAIMS, which no numeric probe can make.

    The paper's data-ceiling argument rests on a spelled-out quantity — "a
    single cycle", "seven scorable Washington House races" — and a spelled-out
    number carries no token for a regex to capture or for the coverage audit to
    demand be probed. `ie_cycles` was therefore derived and then never asserted
    against anything.

    That is not hypothetical here. The 2018/2020/2022 Schedule-E backfill on
    2026-08-08 took the panel from one cycle to five and the scorable sample
    from 7 to 34, and every numeric probe in this file still passed, because
    each individually-correct 2024 figure stayed individually correct. The
    sentence built on top of them was the thing that became false.

    Same defect shape as the cross-state paper's "the highest of the four",
    and handled the same way: in code, in plain language, naming what to fix.
    """
    out: list[str] = []
    n_cycles = d.get("ie_cycles")

    # Appendix C / Finding 1 say the association is "essentially unchanged" under the
    # pre-election cutoff and "does not depend on receipts reported after that cutoff".
    # Those sentences are licensed by the two correlations sitting within a hair of each
    # other; if a re-pin separates them, the wording must move with the measurement.
    # (2026-08-29; reworded the same day — a referee noted the earlier "contributes
    # essentially nothing" claimed a decomposition the design does not perform.)
    if "pre_r_cong" in d and "fullrep_r_cong" in d:
        # Every congressional cell must stay usable in the pre-election cut: a side whose
        # pre-window receipts hit zero drops its cell SILENTLY from r_pre, and the two
        # correlations would then compare different samples while the sentence reads as a
        # same-cell contrast. This is the structural guard that consumes pre_n_usable.
        if d["pre_n_usable"] != d["pre_n_cong"]:
            out.append(
                f"Appendix C: only {d['pre_n_usable']} of {d['pre_n_cong']} congressional "
                f"cells carry positive receipts on both sides in both windows — the "
                f"pre/full contrast is no longer same-cell; restate both ns in the paper.")
        gap = abs(d["pre_r_cong"] - d["fullrep_r_cong"])
        if gap > 0.02:
            out.append(
                f"Appendix C: the paper says the association is essentially unchanged "
                f"under the cutoff, but pre ({d['pre_r_cong']:+.3f}) and full-cycle "
                f"({d['fullrep_r_cong']:+.3f}) now differ by {gap:.3f} — fix the sentences "
                f"in Finding 1 and Appendix C, not this guard.")
        # "The result is invariant to the choice" — the authorized and everything-but-J
        # universes must agree, or that sentence and the universe adoption both need
        # re-arguing.
        if abs(d["pre_r_cong"] - d["nonj_pre_r"]) > 0.01 \
                or abs(d["fullrep_r_cong"] - d["nonj_full_r"]) > 0.01:
            out.append(
                f"Appendix C: 'the result is invariant to the choice' no longer holds — "
                f"authorized ({d['pre_r_cong']:+.3f}/{d['fullrep_r_cong']:+.3f}) vs "
                f"everything-but-J ({d['nonj_pre_r']:+.3f}/{d['nonj_full_r']:+.3f}); "
                f"re-argue the universe choice rather than loosening this guard.")
        if abs(d["leg_item_pre_r"] - d["leg_item_full_r"]) > 0.05:
            out.append(
                "Appendix C: the state-legislative analogue no longer moves by a rounding "
                "hair between full and pre-election — re-read its sentence before trusting "
                "it.")

    # The abstract's cycle count, spelled out. `_WORD_NUM` exists because the
    # paper writes "five cycles" rather than "5 cycles" in prose, and a
    # spelled-out number is exactly what a numeric probe cannot see.
    _WORD_NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                 "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
    # ⚠ REWRITTEN 2026-08-25. This guard used to require the abstract to state a cycle count
    # and compared it to `ie_cycles` -- the INVENTORY count, 5. But the sentence describes the
    # ESTIMATOR, whose 34 scorable races all sit in the four COMPLETED cycles, so the gate was
    # actively holding the abstract at a wrong number. A guard that enforces the defect is
    # worse than no guard: it makes the error look checked. The abstract now states BOTH
    # quantities and each is compared against its own denominator.
    n_done = d.get("ie_cycles_completed")
    m = re.search(r"estimable across \*\*(\w+) completed cycles\*\*", norm)
    if not m:
        out.append(
            "the abstract no longer states how many COMPLETED cycles the directional test "
            "spans ('estimable across **N completed cycles**'). That sentence is the only "
            "place the estimator's breadth is claimed in prose; restore it or this check is "
            "dead weight. Do NOT restore the pre-2026-08-25 form, which compared the "
            "abstract to the inventory count and so required a wrong number."
        )
    else:
        claimed = _WORD_NUM.get(m.group(1).lower())
        if claimed != n_done:
            out.append(
                f"the abstract says the directional test is estimable across "
                f"'{m.group(1)}' COMPLETED cycles; the warehouse holds {n_done} completed "
                f"({n_cycles} in the inventory). Re-run scripts/diag_ie_vs_margin.py — a "
                f"change in panel breadth moves the slope, the interval and n, none of "
                f"which are figure swaps."
            )
    mi = re.search(r"the inventory spans (\w+), but 2026 contributes no scorable race", norm)
    if not mi:
        out.append(
            "the abstract no longer distinguishes the INVENTORY breadth from the estimator's. "
            "Conflating them is the defect this pair of checks exists for."
        )
    elif _WORD_NUM.get(mi.group(1).lower()) != n_cycles:
        out.append(
            f"the abstract says the inventory spans '{mi.group(1)}' cycles; the warehouse "
            f"holds {n_cycles}."
        )

    # "the strongest of any measured factor" (abstract) and "ahead of incumbency and
    # candidate quality" — an ORDERING over Finding 1's correlate set, which the abstract
    # probe cannot see: it asserts each value individually, so incumbency overtaking
    # fundraising would pass every probe while the superlative went false. Added 2026-08-14
    # (Pass 2 of the calculation review); same shape as safe-seat's "more than double any
    # other year". The comparison set is every correlate the pinned frame measures.
    # Finding 2c's functional-form block says the 19 races coded untreated "are *genuine*
    # zeros: none carries any gross IE". That is the qualifier which keeps the cancellation
    # objection confined to six races instead of nineteen, and it has NO numeric token for a
    # probe to capture -- "none" is a word. If a race ever appears with gross IE and a
    # cancelling net, the sentence becomes false and the objection widens.
    # The identification section says "there is exactly **one** redraw inside this panel".
    # Spelled as a word, so no probe can see it, and the whole collinearity argument rests on
    # it: two redraws would give the timing variation the section says is absent.
    # Finding 3 used to print "a jurisdiction on 100% of them" and the 100 was probed. The
    # sentence now says "every one carries ..." and explains that this is TRUE BY CONSTRUCTION
    # rather than a coverage claim (2026-08-25, referee item on the self-selecting
    # denominator). A word claim, so no probe can reach it -- but it still has to be true, and
    # if a C6.3 row ever arrived with a missing field the sentence would be false.
    _fill = d.get("pdc_c63_fill_pct")
    if _fill is not None and abs(_fill - 100.0) > 0.05:
        out.append(
            f"claim: Finding 3 says every C6.3 row carries a direction, a named candidate, a "
            f"filer id and a jurisdiction, and that this holds by construction. The derived "
            f"fill rate is {_fill:.2f}%, not 100%. Either a row arrived incomplete or the "
            f"extract is no longer what that sentence describes.")

    _rd = d.get("idsearch_redraws")
    if _rd is not None and _rd != 1:
        out.append(
            f"claim: the identification section says there is exactly ONE redistricting event "
            f"inside this panel, and the collinearity argument depends on it — a second redraw "
            f"would supply the cross-sectional timing variation the section says is missing. "
            f"The derivation now counts {_rd}.")

    _zwi = d.get("ff_zero_with_ie")
    if _zwi:
        out.append(
            f"claim: Finding 2c says the races coded untreated are genuine zeros and that "
            f"'none carries any gross IE', but {_zwi} of them do. The cancellation objection "
            f"is then not confined to the six largest races, and that sentence must change."
        )

    _others = {k: d[k] for k in ("r_inc", "r_quality", "r_trend", "r_midterm")
               if d.get(k) is not None}
    _weaker = {k: v for k, v in _others.items() if abs(v) >= abs(d["r_fin"])}
    if _weaker:
        out.append(
            f"the abstract calls fundraising (+{d['r_fin']:.2f}) 'the strongest of any "
            f"measured factor', and it is not: " +
            ", ".join(f"{k}={v:+.2f}" for k, v in _weaker.items()) +
            ". Fix the sentence, not this guard.")

    # The superlative that a $2x data defect manufactured. WA-03's national rank
    # cannot be derived from the warehouse (it holds no out-of-state IE), so the
    # claim is checked NEGATIVELY: the paper must not reassert it.
    if "most\nIE-saturated House race in the country" in norm or \
       "most IE-saturated House race in the country" in norm.replace("\n", " "):
        if "an earlier draft" not in norm and "previous draft" not in norm:
            out.append(
                "the paper calls WA-03 'the most IE-saturated House race in the country'. "
                "It is 22nd of 387 on the corrected 2024 figures; the superlative was an "
                "artifact of the notice/periodic double-count. Rank is owned by "
                "scripts/diag_fec_ie_bulk_crosscheck.py --national-rank, which reads FEC's "
                "bulk files (the warehouse holds no out-of-state IE and cannot check it)."
            )
    return out


def main() -> int:
    d: dict = {}
    derive_finding1(d)
    derive_preelection(d)
    derive_allocation(d)
    derive_legislative_panel(d)
    derive_estimator_facts(d)
    derive_federal_influence(d)
    derive_linkage_audit(d)
    derive_common_sample(d)
    try:
        derive_ceiling(d)
    except StaleIEData as exc:
        # Not a paper defect and not something a tolerance can absorb: the IE
        # figures below cannot be measured at all until the rows are re-loaded.
        # Reported as a gate failure rather than a traceback because it is an
        # expected, actionable state with a one-line repair.
        print("\nIE DERIVATION BLOCKED — cannot verify this paper's IE figures.\n")
        print(exc)
        return 1
    # WA-03's residual is model-derived; the paper states it and the whitepaper restates it,
    # so it is asserted for INTERNAL consistency across the two places this paper says it.
    # Not re-derived — see UNCHECKED.
    d["wa03_residual_pp"] = 0.06
    # The figure the defective loader reported for WA-03 2024, before the
    # notice/periodic de-duplication. Historical by construction — it can never
    # be re-derived, because the load that produced it was wrong — so it is
    # asserted as a literal, exactly like the retired Finding 1 correlations.
    # Its purpose is that the correction note must keep saying what was said.
    d["_wa03_inflated"] = 40.1
    # The bootstrap bounds and slope as the paper prints them. Owned by
    # diag_ie_vs_margin.py (see UNCHECKED); asserted here only for INTERNAL
    # consistency, so 2c, Finding 3 and the abstract cannot drift apart while
    # each stays individually plausible — which is the failure mode that let the
    # single-cycle framing survive three sections after the panel grew.
    d["_ci_lo_abs"], d["_ci_hi"] = 0.600, 2.821
    d["_slope2c"] = 0.515
    # The pin note quotes the frame it replaced. Those are historical by construction, so
    # they are asserted as literals: the note must keep saying what the old frame said.
    d.update({"_prev_cells": 109, "_prev_fin": 0.55, "_prev_d": 4.20,
              "_prev_even": 2.37, "_prev_r": 1.93,
              # The same pin note also quotes the OLD correlations beside the
              # new ones ("media +0.05 -> +0.04"). The left-hand values are
              # historical by construction, exactly like the five above: the
              # note's job is to keep saying what the retired frame said, so
              # they are asserted as literals while the right-hand values are
              # asserted against the live derivation.
              # _prev_prof is POSITIVE: the regex captures the digits after the
              # minus sign, so a signed literal here is a sign mismatch, not a
              # defect in the note.
              "_prev_media": 0.05, "_prev_prof": 0.03, "_prev_totalspend": 0.26,
              # Finding 3's zeros note quotes the retired race-matched n and slope
              # (127, +4.890): historical by construction, like the five above. The
              # broken-coincidence sentence in Appendix C quotes the OLD both-side
              # count (129 = 127 + 2 only numerologically; it is the retired
              # fin_cells), so it is pinned as its own literal.
              "_prev_leg_matched_n": 127, "_prev_leg_matched_n_plus2": 129,
              "_prev_leg_slope": 4.890,
              "_prev_alloc_cell": 0.041, "_alloc_alone_08_01": 0.022,
              # The 2026-08-15 residual re-pin moved the holdout cells a second
              # time; the current allocation-alone cell is diagnostic-owned
              # (0.028 on the 08-15 basis) and quoted in the note's history.
              "_alloc_alone": 0.028})
    norm = vp.normalise(PAPER.read_text(encoding="utf-8"))
    audit_sections, offsets, spans = {}, {}, {}
    for name, (start, end) in AUDIT_BOUNDS.items():
        audit_sections[name], offsets[name] = vp.slice_with_offset(norm, start, end)
    # The pin note states each retired correlation beside its live replacement.
    # Left-hand values are historical literals (as with the five above); the
    # right-hand ones are asserted against the derivation, so a re-derivation
    # that moved would fail here rather than quietly disagreeing with the note.
    PROBES.extend([
        ("pin note — correlations recomputed against the residual",
         r"media \+([\d.]+) → \+([\d.]+), professional −([\d.]+) → −([\d.]+), "
         r"total spend \+([\d.]+) → \+([\d.]+)",
         ("_prev_media", "r_media", "_prev_prof", "r_prof_abs",
          "_prev_totalspend", "r_totalspend"), 0.006),
        ("pin note — allocation-alone holdout cell history",
         r"has run ([\d.]+) → ([\d.]+) → ([\d.]+) across the\s+three bases",
         ("_prev_alloc_cell", "_alloc_alone_08_01", "_alloc_alone"), 0.0005),
        ("finding 2 — field vs overperformance is unchanged",
         r"field-vs-overperformance −([\d.]+)", "r_field_overperf_abs", 0.005),
    ])
    stats: dict = {}
    rc = vp.run("DOES MONEY MOVE VOTES — prose scraped and asserted against the warehouse",
                norm, PROBES, d, UNCHECKED, vp.wants_coverage(), spans_out=spans,
                stats_out=stats)
    fails = vp.audit_coverage(audit_sections, spans, offsets, tuple(AUDIT_BOUNDS),
                              COVERAGE_EXEMPT, COVERAGE_EXEMPT_LITERAL,
                              COVERAGE_EXEMPT_SECTIONS, strict_units=True,
        bold_is_result=True)
    fails += vp.audit_satellite_counts(PAPER.name, stats.get("figures"))
    fails += _claim_checks(d, norm)
    if fails:
        print("\nCOVERAGE / SATELLITE AUDIT: %d FAILURE(S)" % len(fails))
        for f in fails:
            print(f"  - {f}")
        return 1
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
