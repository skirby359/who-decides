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
  * "Directional IE exists on disk for exactly one cycle" was false — two cycles carry a
    support/oppose flag; the 2026 one is a 14-row trickle that cannot be scored, which is a
    different and weaker claim than the one the paper made.
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

import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _verify_prose as vp  # noqa: E402

vp.stdout_utf8()

PAPER = vp.DOCS / "does-money-move-votes.md"
CELLS = vp.DOCS / "reference" / "overperformance_cells_2026-08-01.csv"
ALLOC = vp.DOCS / "reference" / "expenditures_vs_residual_2026-08-01.csv"

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


def derive_ceiling(d: dict) -> None:
    """The data-ceiling facts — re-derived in SQL, owing nothing to any diag script."""
    con = duckdb.connect(str(vp.DATA / "wa_statewide.duckdb"), read_only=True)

    # Flagged-IE cycle inventory. The paper's claim is about which cycles are SCORABLE, so
    # the inventory is reported per cycle rather than as a bare count.
    cycles = con.execute("""
        SELECT election_cycle, COUNT(*), COUNT(DISTINCT district), SUM(expenditure_amount)
        FROM independent_expenditures
        WHERE source='FEC' AND office='H' AND state='WA' AND support_oppose IN ('S','O')
        GROUP BY 1 ORDER BY 1""").fetchall()
    by_cycle = {int(c): (int(n), int(k), float(v)) for c, n, k, v in cycles}
    d["ie_cycles"] = len(by_cycle)
    for cyc in (2024, 2026):
        n, k, v = by_cycle.get(cyc, (0, 0, 0.0))
        d[f"ie{cyc}_rows"], d[f"ie{cyc}_districts"] = n, k
        d[f"ie{cyc}_m"], d[f"ie{cyc}_k"] = v / 1e6, v / 1e3

    # WA-03 2024 — the most IE-saturated House race in the country that cycle.
    tot, net = con.execute("""
        WITH p AS (SELECT DISTINCT election_cycle, UPPER(candidate_name) cn, party
                   FROM candidate_finance WHERE state='WA' AND office='H')
        SELECT SUM(ie.expenditure_amount)/1e6,
               SUM(CASE WHEN (p.party='Democratic' AND ie.support_oppose='S')
                          OR (p.party='Republican' AND ie.support_oppose='O')
                        THEN ie.expenditure_amount ELSE -ie.expenditure_amount END)/1e6
        FROM independent_expenditures ie
        LEFT JOIN p ON p.election_cycle = ie.election_cycle
                   AND p.cn = UPPER(ie.candidate_name)
        WHERE ie.source='FEC' AND ie.office='H' AND ie.state='WA'
          AND ie.support_oppose IN ('S','O') AND ie.election_cycle = 2024
          AND ie.district IN ('03','3')""").fetchone()
    d["wa03_total_m"], d["wa03_net_m"] = float(tot), float(net)

    # PDC state-legislative IE, and how nearly empty its directional flag is.
    rows, flagged, dollars, flagged_d = con.execute("""
        SELECT COUNT(*), COUNT(*) FILTER (WHERE support_oppose IN ('S','O')),
               SUM(expenditure_amount),
               COALESCE(SUM(expenditure_amount) FILTER (WHERE support_oppose IN ('S','O')), 0)
        FROM independent_expenditures WHERE source <> 'FEC'""").fetchone()
    d["pdc_ie_m"] = float(dollars) / 1e6
    d["pdc_ie_rows"], d["pdc_ie_flagged"] = int(rows), int(flagged)
    d["pdc_ie_flagged_dollars"] = float(flagged_d)
    d["pdc_ie_flagged_pct"] = 100.0 * float(flagged_d) / float(dollars)

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
    ("abstract — PDC IE total", r"while \$([\d.]+)M of state\s+legislative IE carries no "
     r"support-or-oppose flag", "pdc_ie_m", 0.05),
    ("abstract — WA-03 landed on its fundamentals",
     r"the most IE-saturated House race in the country finished ([\d.]+) points from\s+its "
     r"fundamentals", "wa03_residual_pp", 0.005),

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

    # ---- Finding 2c / Finding 3, the data ceiling
    ("Finding 2c — WA-03 total and net IE",
     r"attracted \$([\d.]+)M in total independent expenditure — the most\s+IE-saturated "
     r"House race in the country — with a net \$([\d.]+)M advantage on the Democratic\s+side. "
     r"It finished ([\d.]+) points from its fundamentals-based prediction",
     ("wa03_total_m", "wa03_net_m", "wa03_residual_pp"), 0.05),
    ("Finding 3 — the two flagged cycles, only one scorable",
     r"2024 holds \*\*(\d+) flagged rows across all ten districts\*\* and \$([\d.]+)M, while "
     r"2026 holds\s+\*\*(\d+) rows across seven districts\*\* and \$(\d+)K",
     ("ie2024_rows", "ie2024_m", "ie2026_rows", "ie2026_k"), 1.0),
    ("Finding 3 — PDC IE total and flag coverage",
     r"Washington's PDC records \*\*\$([\d.]+)M\*\* of\s+independent expenditure",
     "pdc_ie_m", 0.05),
    ("Finding 3 — the five flagged PDC rows",
     r"empty on all but (\d+) of ([\d,]+) rows — \$([\d,]+), or ([\d.]+)% of the\s+dollars",
     ("pdc_ie_flagged", "pdc_ie_rows", "pdc_ie_flagged_dollars", "pdc_ie_flagged_pct"), 0.55),
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
    "Finding 2c's slope and Pearson r (−0.39, n=7) — regressed on a fundamentals-net "
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
    "0.39": "IE-vs-residual association, both statements; owned by "
            "diag_ie_vs_margin.py, which the checklist re-runs immediately "
            "before upload (UNCHECKED)",
}


def main() -> int:
    d: dict = {}
    derive_finding1(d)
    derive_allocation(d)
    derive_ceiling(d)
    # WA-03's residual is model-derived; the paper states it and the whitepaper restates it,
    # so it is asserted for INTERNAL consistency across the two places this paper says it.
    # Not re-derived — see UNCHECKED.
    d["wa03_residual_pp"] = 0.06
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
    if fails:
        print("\nCOVERAGE / SATELLITE AUDIT: %d FAILURE(S)" % len(fails))
        for f in fails:
            print(f"  - {f}")
        return 1
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
