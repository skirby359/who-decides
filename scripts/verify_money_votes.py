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
  gate. `docs/reference/overperformance_cells_2026-08-01.csv` freezes the 163-cell frame;
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
import re
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _verify_prose as vp  # noqa: E402

vp.stdout_utf8()

PAPER = vp.DOCS / "does-money-move-votes.md"
CELLS = vp.DOCS / "reference" / "overperformance_cells_2026-08-01.csv"
ALLOC = vp.DOCS / "reference" / "expenditures_vs_residual_2026-08-01.csv"
# The state-legislative directional panel behind Finding 3, one row per
# (advocacy scope, specification, cycle, district). Same reasoning as CELLS: the
# residual needs the forecast model, and running it 191 times costs minutes that
# do not belong in a release gate. The file pins the CELLS, not the
# coefficients — the slopes below are recomputed from it here, so a paper figure
# that drifted from the panel fails rather than matching a stored answer.
# Regenerate: python scripts/diag_pdc_ie_vs_margin.py --cells-csv <this path>
PDCIE = vp.DOCS / "reference" / "pdc_ie_vs_residual_2026-08-09.csv"

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
    for grp, tag in (("fin_log2_dr > 1", "d_outraised"), ("fin_log2_dr < -1", "r_outraised"),
                     ("fin_log2_dr BETWEEN -1 AND 1", "even")):
        d[f"mean_{tag}"], = con.execute(
            f"SELECT AVG(overperformance) FROM {src} WHERE baseline_ok AND {grp}").fetchone()
    # The paper writes the R-out-raised mean as "−1.77", and the minus sign is prose rather
    # than part of the captured group. Compare magnitudes so the probe is not asserting a
    # positive number against a negative one — which reads as a defect and is a probe bug.
    d["mean_r_outraised_abs"] = abs(d["mean_r_outraised"])
    con.close()


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
                 float(r["total_directional_musd"]))
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

    def _boot(xs, ys, iters=5000, seed=12345):
        rng = random.Random(seed)
        idx = list(range(len(xs)))
        out = []
        for _ in range(iters):
            s = [rng.choice(idx) for _ in idx]
            out.append(_ols([xs[i] for i in s], [ys[i] for i in s])[0])
        out.sort()
        return out[int(0.025 * iters)], out[int(0.975 * iters)]

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
        d[f"leg_{tag}_r_abs"] = abs(rho)


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
    d["ie_total_rows"] = sum(n for n, _, _ in by_cycle.values())
    d["ie_total_m"] = sum(v for _, _, v in by_cycle.values()) / 1e6

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
    d["pdc_c63_m"] = float(dollars) / 1e6

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

    # ---- Finding 1
    ("Finding 1 — cell universe", r"Across the (\d+) baseline-scorable Washington",
     "cells_scorable", 0),
    ("Finding 1 — fundraising correlation",
     r"\| \*\*fundraising, log2\(D receipts / R receipts\)\*\* \| \*\*\+([\d.]+)\*\* \|",
     "r_fin", 0.005),
    ("Finding 1 — incumbency correlation", r"\| incumbency \| \+([\d.]+) \|", "r_inc", 0.005),
    ("Finding 1 — quality correlation",
     r"\| candidate quality index \| \+([\d.]+) \|", "r_quality", 0.005),
    ("Finding 1 — local-trend correlation",
     r"\| local trend \| \+([\d.]+) \|", "r_trend", 0.005),
    ("Finding 1 — fundraising-position means",
     r"average of \*\*\+([\d.]+)\*\* points; where funding was even, \*\*\+([\d.]+)\*\*; "
     r"where the Republican\s+out-raised, \*\*−([\d.]+)\*\*",
     ("mean_d_outraised", "mean_even", "mean_r_outraised_abs"), 0.005),
    ("Finding 1 — the pin note's cell counts",
     r"held \*\*(\d+)\*\* such cells and\s+gave \+([\d.]+), \+([\d.]+), \+([\d.]+) and "
     r"−([\d.]+); it now holds \*\*(\d+)\*\*",
     ("_prev_cells", "_prev_fin", "_prev_d", "_prev_even", "_prev_r", "fin_cells"), 0.005),
    ("Finding 1 — universe unchanged in the pin note",
     r"unchanged at (\d+) baseline-scorable cells", "cells_scorable", 0),

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
    ("Finding 3 — the five-cycle inventory table",
     r"\| 2018 \| (\d+) \| \$([\d.]+)M \|.*?"
     r"\| 2020 \| (\d+) \| \$([\d.]+)M \|.*?"
     r"\| 2022 \| (\d+) \| \$([\d.]+)M \|.*?"
     r"\| 2024 \| \*\*(\d+)\*\* \| \*\*\$([\d.]+)M\*\* \|.*?"
     r"\| 2026 \| \*\*(\d+)\*\* \| \*\*\$(\d+)K\*\* \|",
     ("ie2018_rows", "ie2018_m", "ie2020_rows", "ie2020_m",
      "ie2022_rows", "ie2022_m", "ie2024_rows", "ie2024_m",
      "ie2026_rows", "ie2026_k"), 1.0),
    ("Finding 3 — the panel totals",
     r"\*\*([\d,]+) flagged rows across all ten districts and\s+\$([\d.]+)M\*\*",
     ("ie_total_rows", "ie_total_m"), 0.05),
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
     r"candidate across 2018–2024, on \*\*([\d,]+) filed rows",
     ("pdc_c63_dollars", "pdc_c63_rows"), 0.05),
    ("Finding 3 — scorable district-cycles",
     r"that yields \*\*(\d+) scorable district-cycles\*\*", "leg_all_agg_n", 0),
    # One regex over the whole table, per the precedent set by the five-cycle
    # inventory probe above: a row silently deleted fails here rather than
    # simply going unchecked.
    ("Finding 3 — the four-specification table",
     r"\| \*\*express advocacy, race-matched\*\* \| (\d+) \| (\d+) \| \*\*\+([\d.]+)\*\* \| "
     r"−([\d.]+) to \+([\d.]+) \| \+([\d.]+) \|.*?"
     r"\| express advocacy, district-aggregate \| (\d+) \| (\d+) \| −([\d.]+) \| "
     r"−([\d.]+) to \+([\d.]+) \| −([\d.]+) \|.*?"
     r"\| all directional, race-matched \| (\d+) \| (\d+) \| −([\d.]+) \| "
     r"−([\d.]+) to \+([\d.]+) \| −([\d.]+) \|.*?"
     r"\| all directional, district-aggregate \| (\d+) \| (\d+) \| \+([\d.]+) \| "
     r"−([\d.]+) to \+([\d.]+) \| \+([\d.]+) \|",
     ("leg_expr_matched_n", "leg_expr_matched_material", "leg_expr_matched_slope",
      "leg_expr_matched_ci_lo_abs", "leg_expr_matched_ci_hi", "leg_expr_matched_r",
      "leg_expr_agg_n", "leg_expr_agg_material", "leg_expr_agg_slope_abs",
      "leg_expr_agg_ci_lo_abs", "leg_expr_agg_ci_hi", "leg_expr_agg_r_abs",
      "leg_all_matched_n", "leg_all_matched_material", "leg_all_matched_slope_abs",
      "leg_all_matched_ci_lo_abs", "leg_all_matched_ci_hi", "leg_all_matched_r_abs",
      "leg_all_agg_n", "leg_all_agg_material", "leg_all_agg_slope",
      "leg_all_agg_ci_lo_abs", "leg_all_agg_ci_hi", "leg_all_agg_r"), 0.005),
    # The "100% of them" claim is the one that replaced the false ceiling, so it
    # is probed rather than exempted: if C6.3's fill rate ever fell below 100 the
    # paper's central correction would be overstating the record it corrected to.
    ("Finding 3 — the four fields are complete",
     r"named candidate, a filer id and a jurisdiction on (\d+)% of them",
     "pdc_c63_fill_pct", 0.05),
    ("Finding 3 — the advocacy split",
     r"\$([\d.]+)M against \$([\d.]+)M — and the two run in opposite directions",
     ("pdc_c63_electioneering_m", "pdc_c63_express_m"), 0.05),
    ("Finding 3 — the retracted flag claim, quoted in the correction note",
     r"on all but 5 of ([\d,]+) rows", "pdc_ie_rows", 0),
    ("Finding 3 — the legislative panel restated in 'what more cycles would fix'",
     r"multiplies the cells by nearly four, to (\d+)", "leg_all_agg_n", 0),
    ("limits — fundraising correlation restated",
     r"no instrument\. The \+([\d.]+) correlation", "r_fin", 0.005),
    ("Appendix A — fundraising correlation restated in objection 1",
     r"\*\*1\. \"You found \+([\d.]+) and then explained it away\.\"\*\*", "r_fin", 0.005),
    ("Finding 1 — incumbency restated in the pin note",
     r"ahead of incumbency at \+(\d+\.\d+)", "r_inc", 0.005),
    ("Appendix C — cell universe restated twice",
     r"restricted to the \*\*(\d+) baseline-scorable cells\*\*", "cells_scorable", 0),
    ("Appendix C — the same 163 used by the backtest",
     r"the same (\d+) used by the published backtest", "cells_scorable", 0),
    ("Appendix A — WA-03 restated",
     r"landing ([\d.]+) points from its fundamentals", "wa03_residual_pp", 0.005),
]

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
AUDIT_BOUNDS = {
        "finding1": ("## Finding 1", "## Finding 2"),
        "finding2": ("## Finding 2", "## Finding 3"),
        "finding3": ("## Finding 3", "## What it means"),
    }

COVERAGE_EXEMPT = [
    (r"^(?:19|20)\d{2}$", "a calendar year, not a result"),
    (r"^\d{1,2}$", "small integer — list ordinals, chamber ids, column counts"),
]
COVERAGE_EXEMPT_LITERAL: dict[str, str] = {
    # The holdout-R2 table and the IE cross-section are declared in UNCHECKED and
    # owned by the diagnostics the submission checklist re-runs before upload
    # (diag_ie_vs_margin.py and the holdout script). Exempted by REASON, naming
    # the owner -- not because they are "not results", which they plainly are.
    "0.000": "holdout R2 table cell; owned by the holdout diagnostic (UNCHECKED)",
    "0.013": "holdout R2 table cell; as above",
    "0.026": "holdout R2 table cell; as above",
    "0.022": "the allocation-alone holdout cell AS A TABLE CELL; the same value "
             "restated in the pin note's 'fell from 0.041 to 0.022' IS asserted, "
             "so a drift would still fail there",
    "0.15": "wrong-signed r beside the allocation-alone holdout cell; as above",
    "0.039": "in-sample R2 floor quoted beside the holdout table; as above",
    "0.105": "in-sample R2 ceiling quoted beside the holdout table; as above",
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

    # The abstract's cycle count, spelled out. `_WORD_NUM` exists because the
    # paper writes "five cycles" rather than "5 cycles" in prose, and a
    # spelled-out number is exactly what a numeric probe cannot see.
    _WORD_NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                 "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
    m = re.search(r"estimable across (\w+) cycles", norm)
    if not m:
        out.append(
            "the abstract no longer states how many cycles the directional test spans "
            "('estimable across N cycles'). That sentence is the only place the panel's "
            "breadth is claimed in prose; restore it or this check is dead weight."
        )
    else:
        claimed = _WORD_NUM.get(m.group(1).lower())
        if claimed != n_cycles:
            out.append(
                f"the abstract says the directional test is estimable across "
                f"'{m.group(1)}' cycles; the warehouse holds {n_cycles}. Re-run "
                f"scripts/diag_ie_vs_margin.py — a change in panel breadth moves the "
                f"slope, the interval and n, none of which are figure swaps."
            )

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
    derive_allocation(d)
    derive_legislative_panel(d)
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
    # The bootstrap bounds as the paper prints them. Owned by
    # diag_ie_vs_margin.py (see UNCHECKED); asserted here only for INTERNAL
    # consistency, so 2c and Finding 3 cannot drift apart while both stay
    # individually plausible — which is the failure mode that let the
    # single-cycle framing survive three sections after the panel grew.
    d["_ci_lo_abs"], d["_ci_hi"] = 0.600, 2.821
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
              "_prev_alloc_cell": 0.041, "_alloc_alone": 0.022})
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
        ("pin note — allocation-alone holdout cell fell",
         r"in fact fell from ([\d.]+) to ([\d.]+)\.",
         ("_prev_alloc_cell", "_alloc_alone"), 0.0005),
        ("finding 2 — field vs overperformance is unchanged",
         r"field-vs-overperformance −([\d.]+)", "r_field_overperf_abs", 0.005),
    ])
    stats: dict = {}
    rc = vp.run("DOES MONEY MOVE VOTES — prose scraped and asserted against the warehouse",
                norm, PROBES, d, UNCHECKED, vp.wants_coverage(), spans_out=spans,
                stats_out=stats)
    fails = vp.audit_coverage(audit_sections, spans, offsets, tuple(AUDIT_BOUNDS),
                              COVERAGE_EXEMPT, COVERAGE_EXEMPT_LITERAL)
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
