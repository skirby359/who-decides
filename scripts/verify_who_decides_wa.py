"""Independent re-derivation of docs/who-decides-washington.md, asserted against its prose.

CONVERTED TO AN ASSERTING VERIFIER 2026-08-01. The previous version derived roughly a hundred
values with from-scratch SQL and then PRINTED them, almost all with no paper value beside
them at all — two of about a hundred cells carried a "(paper: ...)" annotation. It returned
None, so it always exited 0, and the release checklist's `verify_who_decides_wa.py || echo
FAILED` could never fire. In practice it asked a human to open the paper and compare a
hundred cells by eye, every time, which is not a gate.

The derivations were sound — every cell spot-checked against the paper reproduced — so what
changed is that the comparison is now performed by the machine and its failure is fatal.

This paper is POSTED (SSRN abstract 7149263, 2026-07-26). The SOURCE has been revised since —
the corrections ledger (docs/who-decides-wa-corrections-ledger.md) records every change, and
the posted PDF still serves the pre-correction text until the owed re-upload — so "posted"
raises the bar for changing the paper and lowers it for suspecting the probe, but does NOT
mean the source is frozen. Reproduce a mismatch by hand before editing anything.

Hits data/wa_vrdb.duckdb DIRECTLY with from-scratch SQL, not by importing the diag scripts.
Read-only; AGGREGATE OUTPUT ONLY — the VRDB carries personal data under RCW 29A.08.720 and
this script must never emit a row.

TWO THINGS THE DERIVATIONS DEPEND ON, both easy to get wrong:
  * WA birthdates are stored as 1 July of the birth year, so `date_diff('year', ...)` gives
    year-difference age. That is the paper's stated convention; it is not true age, and it
    is one year high for anyone born after the election date in their birth year.
  * The eligibility denominator is the CURRENT roll, registered on or before the election
    and aged 18+ at it. Voters who have since left the roll are absent from it — which is
    the survivorship hole the paper measures in its own §Coverage and bounds explicitly,
    rather than a defect in this script.

Run:  python scripts/verify_who_decides_wa.py [--coverage]
"""
from __future__ import annotations

import math
import re
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _verify_prose as vp  # noqa: E402

vp.stdout_utf8()

VRDB = str(vp.DATA / "wa_vrdb.duckdb")
# ADDED 2026-08-11 for Appendix F. Every other section of this paper is derivable from
# the voter file alone; Appendix F is not — it measures CONTEST-level roll-off, which
# needs certified precinct returns, and its closing table needs apportioned ACS
# demographics and the VRDB→results precinct crosswalk. See `derive_appendix_f`.
STATEWIDE = str(vp.DATA / "wa_statewide.duckdb")
PAPER = vp.DOCS / "who-decides-washington.md"

# Official certified 2024 general ballots counted (WA SoS). EXTERNAL, like OFFICIAL
# below: the whole point of a roll-off denominator is that it is the published ballot
# count, not a figure the returns can produce.
BALLOTS_2024 = 3_961_569

BANDS = ["18-29", "30-44", "45-64", "65+"]
ELECTIONS = [("2024-11-05", "e24"), ("2022-11-08", "e22"), ("2021-11-02", "e21"),
             ("2023-11-07", "e23"), ("2025-11-04", "e25")]
OFF_YEARS = ["e21", "e23", "e25"]

# Certified statewide ballots counted, WA Secretary of State
# (results.vote.wa.gov/results/<yyyymmdd>/turnout.html). An EXTERNAL benchmark: the point of
# the coverage table is to compare the voter file against a number the file cannot produce.
OFFICIAL = {"2021-11-02": 1_896_481, "2022-11-08": 3_067_686, "2023-11-07": 1_758_084,
            "2024-11-05": 3_961_569, "2025-11-04": 2_001_425}

# Metro counties, as the paper's geography cut defines them: the ten most populous.
METRO = ("KING", "PIERCE", "SNOHOMISH", "SPOKANE", "CLARK", "THURSTON", "KITSAP",
         "YAKIMA", "WHATCOM", "BENTON")


def _age(date: str) -> str:
    return f"date_diff('year', v.birthdate, DATE '{date}')"


def _band(date: str) -> str:
    a = _age(date)
    return (f"CASE WHEN {a}<30 THEN '18-29' WHEN {a}<45 THEN '30-44' "
            f"WHEN {a}<65 THEN '45-64' ELSE '65+' END")


def _eligible(date: str) -> str:
    """Current-roll registrants who could have voted on `date`."""
    return (f"FROM voters v WHERE v.birthdate IS NOT NULL AND {_age(date)} >= 18 "
            f"AND v.registration_date IS NOT NULL AND v.registration_date <= DATE '{date}'")


def _voted(date: str) -> str:
    return (f"LEFT JOIN (SELECT DISTINCT state_voter_id FROM voting_history "
            f"WHERE election_date = DATE '{date}') h ON h.state_voter_id = v.state_voter_id")


def _pearson(xs, ys) -> float:
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sx = sum((x - mx) ** 2 for x in xs) ** 0.5
    sy = sum((y - my) ** 2 for y in ys) ** 0.5
    return cov / (sx * sy)


def _zscore(col):
    m = sum(col) / len(col)
    s = (sum((c - m) ** 2 for c in col) / len(col)) ** 0.5
    return [(c - m) / s for c in col] if s else [0.0] * len(col)


def _solve(A, b):
    """Gaussian elimination with partial pivoting. Returns None if singular."""
    n = len(A)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(M[r][col]))
        M[col], M[piv] = M[piv], M[col]
        if abs(M[col][col]) < 1e-12:
            return None
        for r in range(n):
            if r != col:
                f = M[r][col] / M[col][col]
                for c in range(col, n + 1):
                    M[r][c] -= f * M[col][c]
    return [M[i][n] / M[i][i] for i in range(n)]


def _partial_corr(y, x, controls) -> float:
    """Partial correlation of y and x net of `controls`, residual-on-residual.

    Covariates are z-scored so X'X stays well-conditioned; residuals are invariant to
    that rescaling. This is re-implemented here rather than imported from
    `diag_wa_rolloff_precinct.py` for the same reason every other derivation in this
    file is: a verifier that imports the analysis code it is checking confirms only
    that the code runs.
    """
    def _resid(v):
        n = len(v)
        Z = [_zscore(c) for c in controls]
        X = [[1.0] + [Z[j][i] for j in range(len(Z))] for i in range(n)]
        k = len(controls) + 1
        XtX = [[sum(X[i][a] * X[i][b] for i in range(n)) for b in range(k)] for a in range(k)]
        Xty = [sum(X[i][a] * v[i] for i in range(n)) for a in range(k)]
        beta = _solve(XtX, Xty)
        if beta is None:
            raise RuntimeError("singular design matrix in the partial-correlation control set")
        return [v[i] - sum(beta[a] * X[i][a] for a in range(k)) for i in range(n)]
    return _pearson(_resid(x), _resid(y))


# Appendix F's even-year contest panel. Grouped exactly as the paper's table groups
# them; the roll-off ranges it prints are the min and max within each group.
_F_CONTESTS = [
    ("top", "PRESIDENT/VICE PRESIDENT"),
    ("partisan", "GOVERNOR"), ("partisan", "U.S. SENATOR"),
    ("partisan", "ATTORNEY GENERAL"), ("partisan", "SECRETARY OF STATE"),
    ("partisan", "COMMISSIONER OF PUBLIC LANDS"), ("partisan", "INSURANCE COMMISSIONER"),
    ("measure", "INITIATIVE MEASURE NO. 2109"), ("measure", "INITIATIVE MEASURE NO. 2124"),
    ("npcon", "SUPERINTENDENT OF PUBLIC INSTRUCTION"),
    ("npcon", "SUPREME COURT - JUSTICE POSITION #02"),
    ("npunc", "SUPREME COURT - JUSTICE POSITION #08"),
    ("npunc", "SUPREME COURT - JUSTICE POSITION #09"),
]

# (election_id, label, certified ballots counted, King's share of that election's
# ballots). The King share is measured from the VRDB below rather than trusted from
# this table — see `derive_appendix_f`.
_F_ODD = [(8, "2021", 1_896_481), (4, "2023", 1_758_084), (1, "2025", 2_001_425)]

_F_OFFICE_GROUPS = """
    CASE WHEN race_name LIKE '%SCHOOL%DIRECTOR%' THEN 'school'
         WHEN race_name LIKE '%CITY COUNCIL%' OR race_name LIKE '%COUNCIL POSITION%'
              THEN 'council'
         WHEN race_name LIKE '%MAYOR%' THEN 'mayor'
         WHEN race_name LIKE '%FIRE%' THEN 'fire'
         WHEN race_name LIKE '%PORT%COMMISSIONER%' THEN 'port' END"""


def derive_appendix_f(d: dict) -> None:
    """Appendix F — contest-level roll-off. The only block of this paper that needs
    more than the voter file.

    THREE THINGS TO KNOW BEFORE READING THE SQL.

    1. **Two databases, and a hard dependency on two BUILD tables.** Certified returns
       come from `wa_statewide.duckdb`; the closing partial-correlation table also needs
       `precinct_demographics` (ACS block groups apportioned to precincts) and
       `vrdb_precinct_crosswalk`. Neither is in a raw state extract, which is why
       `diag_wa_rolloff_precinct.py` says so in its own header. If they are missing this
       function RAISES rather than skipping: a verifier that quietly drops a section
       reports "all figures agree" about a section it never looked at, and skipped is
       not passed.

    2. **The odd-year figures run on a 38-county, King-excluded footprint**, because
       `precinct_results` holds no King rows for 2021 or 2023 and only Seattle Mayor for
       2025. The statewide-item denominator is therefore the certified count scaled by
       King's ballot share, which makes it an estimate. King's share is MEASURED from
       the VRDB here rather than copied from the diag script's constants — a hard-coded
       share is exactly the kind of input that goes stale silently.

    3. **The local-office rows are lower bounds, not estimates.** The denominator is the
       best-attended contest in each precinct, and that contest rolls off too. The paper
       says so; the derivation cannot fix it and does not pretend to.
    """
    con = duckdb.connect(STATEWIDE, read_only=True)
    try:
        have = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        missing = {"precinct_demographics", "vrdb_precinct_crosswalk"} - have
        if missing:
            raise RuntimeError(
                f"Appendix F needs {sorted(missing)} in {STATEWIDE}, and they are absent. "
                f"These are build tables, not raw-extract tables — see the docstring. "
                f"Failing rather than skipping: a section this verifier cannot check must "
                f"not be reported as checked.")
        con.execute(f"ATTACH IF NOT EXISTS '{VRDB}' AS vrdb (READ_ONLY)")
        _f_even(con, d)
        _f_odd(con, d)
        _f_ecological(con, d)
        _a_rejection(con, d)
        # Appendix G shares this connection because it shares both databases and both
        # build tables. It is a different measure — off-cycle RETENTION by precinct
        # against race/income/education — but the dependency and the ecological ceiling
        # are identical, so it lives and fails with F.
        _g_dropoff(con, d)
    finally:
        con.close()


def _a_rejection(con, d: dict) -> None:
    """Appendix A — does the rejection channel skew young, and by how much?

    RAISED BY AN EXTERNAL REFEREE, 2026-08-11, and admitted under the freeze rule on that
    basis: the appendix asserted "no one is shut out of the off-year ballot" without
    checking the one channel that can shut someone out. Washington credits a vote when a
    ballot is ACCEPTED, not when it is returned, and signature-mismatch and late arrival
    are rejected at very different rates by age.

    TWO LIMITS, both load-bearing, both stated in the appendix itself. (1) This is the
    August 2026 PRIMARY, the only election for which a per-voter status panel exists —
    the odd-year elections this paper measures have no equivalent published file, so it
    is indicative of the channel, not a measurement of it in 2021/2023/2025. (2) It runs
    on the panel's latest snapshot, so ballots cured after that date still count as
    rejected and the gap is if anything overstated.

    The point of measuring it is that the answer is SMALL. A referee cannot be told the
    frame is safe; the frame has to be shown safe, and 0.13 points against a 6.6-point
    composition gap shows it.
    """
    if "voter_ballot_status" not in {r[0] for r in con.execute("SHOW TABLES").fetchall()}:
        raise RuntimeError(
            "Appendix A's rejection check needs `voter_ballot_status`, which is absent. "
            "Load a per-voter SoS ballot-status file (`main.py refresh-gotv`). Failing "
            "rather than skipping: an unmeasured channel must not read as a measured one.")
    # ⚠ THIS BASIS FLOATS, AND AS OF 2026-08-13 THIS BLOCK IS EXPECTED TO FAIL. Read this
    # before "fixing" anything.
    #
    # `MAX(report_date)` means the three Appendix A rejection figures are recomputed against
    # whatever ballot-status snapshot was loaded most recently, so every load moves them. The
    # paper says so in its own words — "it reads the panel at its latest snapshot" — which
    # declares the basis as floating rather than pinning it, and that is the defect.
    #
    # The 2026-08-13 load demonstrated it rather than leaving it hypothetical: 2.89 -> 2.96
    # (under-30), 0.76 -> 0.82 (65+), ratio 3.8 -> 3.6. Nothing about the finding changes —
    # the channel shifts the 18-29 share by 0.13 points against a 6.6-point composition gap —
    # but these are PUBLISHED figures (SSRN 7149263) and they will keep moving, because Too
    # Late rejections accumulate after election day: statewide rejection ran 0.70% on
    # 2026-07-21, 0.65% on 08-05 and 1.29% on 08-13, and it climbs until certification.
    #
    # AUTHOR DECISION 2026-08-13: do NOT pin yet and do NOT resubmit yet. Pinning now would
    # fix the figures to a pre-certification count and then need re-pinning anyway, so the
    # gate is left FAILING on these three cells deliberately, until the certified file lands
    # (~three weeks post-primary). At that point: pin to the certified snapshot, state the
    # date in the paper in place of "its latest snapshot", derive against that fixed date,
    # and record the move in `who-decides-wa-corrections-ledger.md`.
    #
    # So: a red run on THESE THREE CELLS is expected and accepted. A red run anywhere else in
    # this verifier is not.
    d["a_rej_date"], = con.execute(
        "SELECT MAX(report_date) FROM voter_ballot_status").fetchone()
    rows = con.execute("""
        WITH b AS (
            SELECT s.ballot_status,
                   CASE WHEN date_diff('year', v.birthdate, DATE '2026-08-04') < 30
                             THEN '18-29'
                        WHEN date_diff('year', v.birthdate, DATE '2026-08-04') >= 65
                             THEN '65+' ELSE 'mid' END AS band
            FROM voter_ballot_status s JOIN vrdb.voters v USING (state_voter_id)
            WHERE s.report_date = (SELECT MAX(report_date) FROM voter_ballot_status)
              AND v.birthdate IS NOT NULL)
        SELECT band, COUNT(*), COUNT(*) FILTER (WHERE ballot_status = 'Rejected')
        FROM b GROUP BY 1""").fetchall()
    tot = {b: n for b, n, _ in rows}
    rej = {b: r for b, _, r in rows}
    d["a_rej_young"] = 100.0 * rej["18-29"] / tot["18-29"]
    d["a_rej_senior"] = 100.0 * rej["65+"] / tot["65+"]
    d["a_rej_ratio"] = d["a_rej_young"] / d["a_rej_senior"]
    # What crediting RETURNED rather than ACCEPTED ballots would do to the 18-29 share —
    # the only number that bears on the paper's finding rather than on the frame.
    n_all = sum(tot.values())
    n_acc = n_all - sum(rej.values())
    d["a_rej_comp_shift"] = (100.0 * tot["18-29"] / n_all
                             - 100.0 * (tot["18-29"] - rej["18-29"]) / n_acc)


def _g_dropoff(con, d: dict) -> None:
    """Appendix G — off-cycle drop-off against precinct race, income and education.

    Retention is (distinct 2025 off-year voters) / (distinct 2024 presidential voters)
    within a precinct, mapped through the crosswalk. The partial correlations control for
    ONE covariate, the precinct's 65+ share — not the five-covariate set Appendix F uses,
    because the question here is explicitly whether race, income or education add anything
    BEYOND age. Using F's control set would answer a different question and quietly
    change every figure; the two appendices are not on the same specification and must
    not be read as if they were.
    """
    rows = con.execute("""
        WITH xw AS (SELECT UPPER(TRIM(county_name)) cty,
                           UPPER(TRIM(vrdb_precinct_code)) pc, precinct_id
                    FROM vrdb_precinct_crosswalk),
        pres AS (SELECT x.precinct_id, COUNT(DISTINCT h.state_voter_id) n
                 FROM vrdb.voting_history h
                 JOIN vrdb.voters v ON v.state_voter_id = h.state_voter_id
                 JOIN xw x ON x.cty = UPPER(TRIM(v.county_name))
                          AND x.pc = UPPER(TRIM(v.precinct_code))
                 WHERE h.election_date = DATE '2024-11-05' GROUP BY 1),
        off AS (SELECT x.precinct_id, COUNT(DISTINCT h.state_voter_id) n
                FROM vrdb.voting_history h
                JOIN vrdb.voters v ON v.state_voter_id = h.state_voter_id
                JOIN xw x ON x.cty = UPPER(TRIM(v.county_name))
                         AND x.pc = UPPER(TRIM(v.precinct_code))
                WHERE h.election_date = DATE '2025-11-04' GROUP BY 1)
        SELECT COALESCE(off.n, 0) * 1.0 / pres.n, CAST(d.pct_white AS DOUBLE),
               CAST(d.pct_hispanic AS DOUBLE), CAST(d.pct_college_degree AS DOUBLE),
               CAST(d.median_income AS DOUBLE), CAST(d.pct_over_65 AS DOUBLE)
        FROM pres JOIN precinct_demographics d ON d.precinct_id = pres.precinct_id
        LEFT JOIN off ON off.precinct_id = pres.precinct_id
        WHERE pres.n >= 100 AND d.pct_white IS NOT NULL AND d.pct_hispanic IS NOT NULL
          AND d.pct_college_degree IS NOT NULL AND d.median_income IS NOT NULL
          AND d.pct_over_65 IS NOT NULL""").fetchall()
    ret, white, hisp, college, income, over65 = (list(c) for c in zip(*rows))
    # The paper says "~4,700 precincts" — stated to the nearest hundred, and the measured
    # count is 4,719. The rounding is declared here rather than absorbed into a tolerance,
    # the same treatment as Appendix F's truncated span: a real drift still fails, since a
    # move to 4,6xx or 4,8xx changes this value.
    d["g_n_prec_h100"] = round(len(rows) / 100.0) * 100
    ctrl = [over65]
    for tag, col in (("white", white), ("hisp", hisp), ("college", college),
                     ("income", income), ("over65", over65)):
        # Magnitudes: hispanic and income print with a Unicode minus the paper's regex
        # cannot parse, so the anchors carry the sign and these carry the size.
        d[f"g_raw_{tag}"] = abs(_pearson(col, ret))
        if tag != "over65":                      # 65+ is the control, so it has no partial
            d[f"g_part_{tag}"] = abs(_partial_corr(ret, col, ctrl))


def _f_even(con, d: dict) -> None:
    """The even-year contest table, its two footnote counts, and the scenario grid."""
    d["f_ballots"] = BALLOTS_2024
    # The grid's three scenario columns and the precinct cut's two filter thresholds.
    # DECLARED PARAMETERS, not measurements — but derived here and asserted anyway,
    # because they are the numbers the SQL below actually uses and the text describes.
    # A floor changed in code and not in prose (or the reverse) is otherwise invisible:
    # the 50-vote floor was being waived by the small-integer coverage rule and the
    # 100-voter one was simply unmapped.
    d["f_scen_lo"], d["f_scen_mid"], d["f_scen_hi"] = 5, 17, 34
    d["f_min_pres_votes"], d["f_min_xwalk_voters"] = 50, 100
    groups: dict[str, list[float]] = {}
    for grp, name in _F_CONTESTS:
        votes, = con.execute(
            "SELECT SUM(pr.votes) FROM precinct_results pr JOIN races r USING (race_id) "
            "WHERE pr.election_id = 2 AND r.race_name = ?", [name]).fetchone()
        if votes is None:
            raise RuntimeError(f"Appendix F: no 2024 rows for {name!r} — the contest panel "
                               f"is curated by exact race_name and one has moved.")
        groups.setdefault(grp, []).append(100.0 * (BALLOTS_2024 - votes) / BALLOTS_2024)
        if name == "PRESIDENT/VICE PRESIDENT":
            d["f_pres_votes"] = int(votes)
        if name == "SUPREME COURT - JUSTICE POSITION #02":
            d["f_sc2_votes"] = int(votes)
    d["f_ro_president"] = groups["top"][0]
    for grp in ("partisan", "measure", "npcon", "npunc"):
        d[f"f_ro_{grp}_lo"] = min(groups[grp])
        d[f"f_ro_{grp}_hi"] = max(groups[grp])
    # Appendix A POOLS partisan offices with ballot measures into one "~3–7%" span. That is
    # a fourth quantity, not either table row, and pooling is where a restatement silently
    # changes what it is describing.
    _pm = groups["partisan"] + groups["measure"]
    d["f_ro_pm_lo"], d["f_ro_pm_hi"] = min(_pm), max(_pm)
    # Appendix A states the contested span as integers, "~16–17%", and that stays
    # a TRUNCATION of 16.5684-17.2224. Half-up does not work here: both
    # endpoints round to 17, so half-up would print the degenerate "17-17%".
    #
    # ⚠ As of 2026-08-18 this is the ONLY truncated integer span left in the
    # paper. The interpretation section's reverse-overlap span moved to half-up
    # ("43-48%", presret_*_rd, correction C13) on the author's call, so the two
    # spans now run on DIFFERENT declared conventions, each for a stated reason.
    # Both rows are in docs/reference/derivation-bases.csv. Do not harmonise them
    # without re-reading why: the constraint above is what blocks it.
    d["f_ro_npcon_lo_tr"] = float(int(d["f_ro_npcon_lo"]))
    d["f_ro_npcon_hi_tr"] = float(int(d["f_ro_npcon_hi"]))

    # The exclusions footnote. Both are counts the footnote states as fact.
    d["f_coa_races"], = con.execute(
        "SELECT COUNT(*) FROM races WHERE election_id = 2 "
        "AND race_name LIKE '%COURT OF APPEALS%'").fetchone()
    d["f_lg_precincts"], d["f_lg_counties"] = con.execute("""
        SELECT COUNT(DISTINCT pr.precinct_id), COUNT(DISTINCT UPPER(p.county_name))
        FROM precinct_results pr JOIN races r USING (race_id)
        JOIN precincts p USING (precinct_id)
        WHERE pr.election_id = 2 AND r.race_name LIKE '%LT. GOVERNOR%'""").fetchone()
    d["f_precincts_2024"], = con.execute(
        "SELECT COUNT(DISTINCT precinct_id) FROM precinct_results "
        "WHERE election_id = 2").fetchone()

    # The scenario grid. Baselines are the official turnout rates already transcribed
    # above; the off-year baseline is their three-cycle mean. Cells are computed on
    # UNROUNDED baselines — freeze rule 3 — which agrees with the printed cells on all
    # nine here, checked, so nothing hangs on the choice.
    d["f_base_pres"] = d["off_turnout_2024"]
    d["f_base_mid"] = d["off_turnout_2022"]
    d["f_base_odd"] = sum(d[f"off_turnout_{y}"] for y in (2021, 2023, 2025)) / 3.0
    for tag, base in (("pres", d["f_base_pres"]), ("mid", d["f_base_mid"]),
                      ("odd", d["f_base_odd"])):
        for pct in (5, 17, 34):
            d[f"f_grid_{tag}_{pct}"] = base * (1 - pct / 100.0)


def _f_odd(con, d: dict) -> None:
    """The odd-year table: one statewide item per year, five local office groups."""
    # King's share of each odd-year electorate, measured, and the guard that the odd-year
    # returns really do exclude King. The guard matters because the scaling below is only
    # correct while King is absent; if the returns are ever loaded these figures must be
    # rebuilt on the real statewide basis rather than quietly re-scaled.
    shares: dict[str, float] = {}
    _sw_by_year: dict[str, list[float]] = {}
    for eid, lab, ballots in _F_ODD:
        date = {"2021": "2021-11-02", "2023": "2023-11-07", "2025": "2025-11-04"}[lab]
        shares[lab], = con.execute(f"""
            SELECT SUM(CASE WHEN UPPER(v.county_name) = 'KING' THEN 1 ELSE 0 END) * 1.0
                   / COUNT(*)
            FROM (SELECT DISTINCT state_voter_id FROM vrdb.voting_history
                  WHERE election_date = DATE '{date}') h
            JOIN vrdb.voters v USING (state_voter_id)""").fetchone()
        n_king, = con.execute("""
            SELECT COUNT(*) FROM precinct_results pr JOIN precincts p USING (precinct_id)
            JOIN races r USING (race_id)
            WHERE r.election_id = ? AND UPPER(p.county_name) = 'KING'""", [eid]).fetchone()
        # 2025 carries Seattle Mayor and nothing else; the paper names the race, not a
        # row count, so the count stays a local rather than an unconsumed derived key.
        if lab == "2025":
            if n_king > 3_051:
                raise RuntimeError(
                    f"Appendix F: 2025 now has {n_king} King precinct-result rows, beyond the "
                    f"3,051 Seattle Mayor rows the King-share scaling assumes. Rebuild on the "
                    f"real statewide basis.")
        elif n_king:
            raise RuntimeError(
                f"Appendix F: {n_king} King precinct-result rows are now loaded for {lab}. "
                f"The King-share scaling assumes they are absent — rebuild on the real "
                f"statewide basis.")
    d["f_king_share_lo"] = 100.0 * min(shares.values())
    d["f_king_share_hi"] = 100.0 * max(shares.values())

    # EXACT non-King denominators (2026-08-14, referee item 7). The statewide-item
    # denominator was previously `ballots * (1 - VRDB King share)` — an estimate the
    # paper itself flagged as unbuilt work. King's certified countywide ballots are on
    # the same SoS turnout pages as the OFFICIAL constants; they are pinned with source
    # URLs in docs/reference/wa_county_turnout_king_oddyears.csv, and the pin's statewide
    # column must reconcile with OFFICIAL exactly or the run stops — a pinned file that
    # disagrees with the constant it rode in with is a transcription error, not a basis.
    import csv as _csv
    _king_pin = {}
    _pin_path = vp.DOCS / "reference" / "wa_county_turnout_king_oddyears.csv"
    with _pin_path.open(newline="", encoding="utf-8") as fh:
        for r in _csv.DictReader(fh):
            _king_pin[r["election"]] = int(r["ballots_counted"])
            if int(r["statewide_ballots_counted"]) != OFFICIAL[r["election"]]:
                raise RuntimeError(
                    f"{_pin_path.name}: statewide count for {r['election']} disagrees with "
                    f"the OFFICIAL constant — re-fetch the turnout page.")
    d["f_king_2021"] = _king_pin["2021-11-02"]
    d["f_king_2023"] = _king_pin["2023-11-07"]
    d["f_king_2025"] = _king_pin["2025-11-04"]

    for eid, lab, ballots in _F_ODD:
        date = {"2021": "2021-11-02", "2023": "2023-11-07", "2025": "2025-11-04"}[lab]
        denom = ballots - _king_pin[date]
        rows = con.execute("""
            SELECT SUM(pr.votes) FROM races r JOIN precinct_results pr USING (race_id)
            JOIN precincts p USING (precinct_id)
            WHERE r.election_id = ? AND UPPER(p.county_name) <> 'KING'
            GROUP BY r.race_name HAVING COUNT(DISTINCT pr.precinct_id) >= 4000""",
            [eid]).fetchall()
        # 2023 returns zero rows, and that is the right answer rather than a gap: SB 5082
        # abolished the tax advisory votes effective July 2023, so the odd-year ballot
        # carried no statewide contest. The paper says "none on the ballot" for that cell.
        vals = [100.0 * (denom - v) / denom for (v,) in rows]
        _sw_by_year[lab] = vals
        # Only the endpoints a probe reads go into `d`. 2021 prints a range, 2025 a single
        # value, 2023 nothing at all — storing a `_hi` for 2025 would be an intermediate
        # nothing consumes, which is the shape the mutation sweep exists to surface.
        if lab == "2021" and vals:
            d["f_odd_statewide_2021_lo"], d["f_odd_statewide_2021_hi"] = min(vals), max(vals)
        elif lab == "2025" and vals:
            d["f_odd_statewide_2025_lo"] = min(vals)

        con.execute("""
            CREATE OR REPLACE TEMP TABLE _f_rv AS
            SELECT pr.precinct_id, r.race_name, SUM(pr.votes) AS v
            FROM precinct_results pr JOIN precincts p USING (precinct_id)
            JOIN races r USING (race_id)
            WHERE r.election_id = ? AND UPPER(p.county_name) <> 'KING'
            GROUP BY 1, 2""", [eid])
        con.execute("CREATE OR REPLACE TEMP TABLE _f_pmax AS "
                    "SELECT precinct_id, MAX(v) AS mx FROM _f_rv GROUP BY 1")
        for grp, pct in con.execute(f"""
            SELECT {_F_OFFICE_GROUPS} AS grp,
                   100.0 * (1 - SUM(_f_rv.v) * 1.0 / SUM(_f_pmax.mx))
            FROM _f_rv JOIN _f_pmax USING (precinct_id)
            WHERE _f_pmax.mx > 0 GROUP BY 1 HAVING grp IS NOT NULL""").fetchall():
            d[f"f_odd_{grp}_{lab}"] = float(pct)
    con.execute("DROP TABLE IF EXISTS _f_rv")
    con.execute("DROP TABLE IF EXISTS _f_pmax")

    # HOW OFTEN EACH OFFICE *IS* THE FLOOR (2026-08-11, external referee).
    #
    # The denominator is the best-attended contest in each precinct, so a contest that is
    # itself frequently that contest has its measured roll-off forced toward zero BY
    # CONSTRUCTION. "Lower bound" is true of every row but understates the problem,
    # because the bias is not a common shift: it scales with how often the office defines
    # the floor, and that varies twentyfold across the five. Mayor defines the floor in
    # over half its precincts and fire district in under three percent, which is close to
    # the inverse of the published ordering. Derived so the appendix can state the
    # magnitude instead of the direction only.
    for grp in ("fire", "school", "council", "port", "mayor"):
        shares = []
        for eid, lab, _ in _F_ODD:
            con.execute("""
                CREATE OR REPLACE TEMP TABLE _f_rv2 AS
                SELECT pr.precinct_id, r.race_name, SUM(pr.votes) AS v
                FROM precinct_results pr JOIN precincts p USING (precinct_id)
                JOIN races r USING (race_id)
                WHERE r.election_id = ? AND UPPER(p.county_name) <> 'KING'
                GROUP BY 1, 2""", [eid])
            con.execute("CREATE OR REPLACE TEMP TABLE _f_pm2 AS "
                        "SELECT precinct_id, MAX(v) mx FROM _f_rv2 GROUP BY 1")
            row = con.execute(f"""
                WITH g AS (SELECT precinct_id, {_F_OFFICE_GROUPS} AS grp, MAX(v) AS gmax
                           FROM _f_rv2 GROUP BY 1, 2 HAVING grp = '{grp}')
                SELECT 100.0 * COUNT(*) FILTER (WHERE g.gmax >= p.mx) / COUNT(*)
                FROM g JOIN _f_pm2 p USING (precinct_id) WHERE p.mx > 0""").fetchone()
            shares.append(float(row[0]))
        d[f"f_floorshare_{grp}"] = max(shares)      # the worst case, which is the caveat
    con.execute("DROP TABLE IF EXISTS _f_rv2")
    con.execute("DROP TABLE IF EXISTS _f_pm2")

    # The prose spans read ACROSS the three years, which is a different quantity from any
    # table cell and is where a "two quantities under one name" slip would land.
    _yrs = ("2021", "2023", "2025")
    # Per-office spans across the three years. "The question" quotes all five and
    # Appendix F's prose quotes fire; the LOW endpoint of each was being waived by the
    # small-integer rule (4, 16, 10, 19, 30 are all one or two digits), so five ranges had
    # only their upper half visible to the gate. Fourth instance of that exemption hiding
    # something on 2026-08-11.
    for _g in ("fire", "school", "council", "port", "mayor"):
        d[f"f_odd_{_g}_lo"] = min(d[f"f_odd_{_g}_{y}"] for y in _yrs)
        d[f"f_odd_{_g}_hi"] = max(d[f"f_odd_{_g}_{y}"] for y in _yrs)
    d["f_odd_school_council_hi"] = max(
        d[f"f_odd_{g}_{y}"] for g in ("school", "council") for y in _yrs)
    # The statewide-item span the prose quotes pools 2021 and 2025 — 2023 had no
    # statewide contest — so it is NOT the 2021 row restated.
    _sw = [v for vals in _sw_by_year.values() for v in vals]
    d["f_odd_statewide_lo"], d["f_odd_statewide_hi"] = min(_sw), max(_sw)
    # 2023's empty cell is a RESULT, not a gap: SB 5082 repealed the tax advisory votes, so
    # the odd-year ballot carried no statewide contest. The probe's anchor contains the
    # literal "*none on the ballot*", which catches the paper changing; this catches the
    # DATA changing, which the anchor cannot see. Read by `claim_guards`.
    d["f_odd_statewide_2023_n"] = len(_sw_by_year["2023"])
    # Appendix A restates the odd-year local rows as ONE span across every office group and
    # every year ("4–44% on a conservative floor"), which is a third quantity again — not
    # the fire-district span and not any table row.
    _all_local = [d[f"f_odd_{g}_{y}"] for g in ("fire", "school", "council", "port", "mayor")
                  for y in _yrs]
    d["f_odd_local_lo"], d["f_odd_local_hi"] = min(_all_local), max(_all_local)


def _f_ecological(con, d: dict) -> None:
    """The county correlation, the precinct cut, and the crosswalk-coverage caveat."""
    # County cut: 39 counties, roll-off of the contested nonpartisan race against the
    # county electorate's 65+ share. Precinct-namespace gaps do not bite at county level.
    rows = con.execute("""
        WITH pr AS (
            SELECT UPPER(p.county_name) cty,
                   SUM(CASE WHEN r.race_name = 'PRESIDENT/VICE PRESIDENT'
                            THEN pr.votes ELSE 0 END) pres,
                   SUM(CASE WHEN r.race_name = 'SUPREME COURT - JUSTICE POSITION #02'
                            THEN pr.votes ELSE 0 END) sc
            FROM precinct_results pr JOIN races r USING (race_id)
            JOIN precincts p ON p.precinct_id = pr.precinct_id
            WHERE pr.election_id = 2 GROUP BY 1),
        age AS (
            SELECT UPPER(v.county_name) cty,
                   SUM(CASE WHEN (2024 - EXTRACT(year FROM v.birthdate)) >= 65
                            THEN 1 ELSE 0 END) * 1.0 / COUNT(*) s65
            FROM (SELECT DISTINCT state_voter_id FROM vrdb.voting_history
                  WHERE election_date = DATE '2024-11-05') h
            JOIN vrdb.voters v USING (state_voter_id)
            WHERE v.birthdate IS NOT NULL
              AND (2024 - EXTRACT(year FROM v.birthdate)) >= 18 GROUP BY 1)
        SELECT (1 - pr.sc * 1.0 / pr.pres), age.s65
        FROM pr JOIN age USING (cty) WHERE pr.pres > 0""").fetchall()
    d["f_county_n"] = len(rows)
    d["f_county_r"] = _pearson([float(r[1]) for r in rows], [float(r[0]) for r in rows])

    # Precinct cut. `_load` is the paper's stated filter chain: a President vote, the
    # contest present, usable ACS demographics, and >= 50 presidential votes.
    def _load(race_id, floor):
        return con.execute("""
            WITH pres AS (SELECT precinct_id, SUM(votes) v FROM precinct_results
                          WHERE election_id = 2 AND race_id = 3106 GROUP BY 1),
                 cst AS (SELECT precinct_id, SUM(votes) v FROM precinct_results
                         WHERE election_id = 2 AND race_id = ? GROUP BY 1)
            SELECT pres.precinct_id, CAST(1 - cst.v * 1.0 / pres.v AS DOUBLE),
                   CAST(pres.v AS DOUBLE),
                   CAST(d.pct_over_65 AS DOUBLE), CAST(d.pct_under_30 AS DOUBLE),
                   CAST(d.median_age AS DOUBLE), CAST(d.median_income AS DOUBLE),
                   CAST(d.pct_college_degree AS DOUBLE), CAST(d.median_home_value AS DOUBLE),
                   CAST(d.pct_renter AS DOUBLE), CAST(d.total_population AS DOUBLE)
            FROM pres JOIN cst USING (precinct_id)
            JOIN precinct_demographics d ON d.precinct_id = pres.precinct_id
            WHERE pres.v >= ? AND d.pct_over_65 IS NOT NULL AND d.total_population > 0
              AND d.median_income IS NOT NULL AND d.pct_college_degree IS NOT NULL
              AND d.median_home_value IS NOT NULL AND d.pct_renter IS NOT NULL""",
            [race_id, floor]).fetchall()

    # The paper decomposes the sample loss, so both stages are derived: how many
    # precincts carry demographics at all, and how many the vote floor then removes.
    d["f_prec_demo"] = len(_load(3406, 0))
    for race_id, tag in ((3406, "sc2"), (3362, "spi")):
        res = _load(race_id, d["f_min_pres_votes"])
        (_, ro, pv, o65, u30, mage, inc, coll, hv, rent, pop) = zip(*res)
        ro = list(ro)
        ctrl = [list(inc), list(coll), list(hv), list(rent),
                [math.log(p) for p in pop]]
        if tag == "sc2":                      # only sc2's n and mean are published
            d["f_prec_n_sc2"] = len(res)
            d["f_prec_mean_sc2"] = sum(ro) / len(ro) * 100.0
        d[f"f_res65_raw_{tag}"] = _pearson(list(o65), ro)
        d[f"f_res65_partial_{tag}"] = _partial_corr(ro, list(o65), ctrl)
        if tag == "sc2":
            d["f_medage_raw"] = _pearson(list(mage), ro)
            d["f_medage_partial"] = _partial_corr(ro, list(mage), ctrl)
            # Magnitude: the paper prints "−0.11" with a Unicode minus, so the
            # probe captures digits only and the anchor carries the sign. If the
            # sign ever flipped, the anchor would stop matching and the probe
            # would FAIL rather than silently compare magnitudes.
            d["f_under30_raw_mag"] = abs(_pearson(list(u30), ro))
    d["f_prec_dropped"] = d["f_prec_demo"] - d["f_prec_n_sc2"]
    d["f_prec_pct_of_total"] = 100.0 * d["f_prec_n_sc2"] / d["f_precincts_2024"]

    # Statewide roll-off put on the PRECINCT cut's own basis (contest votes over
    # President votes), which is what makes it comparable to the precinct mean. The
    # 17.2% figure beside it belongs to the ballots basis and does not transfer.
    d["f_statewide_on_pres_basis"] = 100.0 * (1 - d["f_sc2_votes"] / d["f_pres_votes"])

    # The electorate-65+ predictor — the county cut's own yardstick, at precinct
    # resolution, which is the only partial that answers the question the descent to
    # precincts was made to answer.
    e65 = {int(pid): (float(s65), int(n)) for pid, s65, n in con.execute("""
        WITH voted AS (SELECT DISTINCT state_voter_id FROM vrdb.voting_history
                       WHERE election_date = DATE '2024-11-05'),
             v AS (SELECT vo.county_name, vo.precinct_code, vo.birthdate
                   FROM voted vt JOIN vrdb.voters vo USING (state_voter_id)
                   WHERE vo.birthdate IS NOT NULL
                     AND (2024 - EXTRACT(year FROM vo.birthdate)) >= 18)
        SELECT x.precinct_id,
               SUM(CASE WHEN (2024 - EXTRACT(year FROM v.birthdate)) >= 65
                        THEN 1 ELSE 0 END) * 1.0 / COUNT(*), COUNT(*)
        FROM v JOIN vrdb_precinct_crosswalk x
          ON UPPER(TRIM(v.county_name)) = UPPER(TRIM(x.county_name))
         AND UPPER(TRIM(v.precinct_code)) = UPPER(TRIM(x.vrdb_precinct_code))
        GROUP BY 1""").fetchall()}
    keep = [(e65[r[0]][0], r[1], r[6], r[7], r[8], r[9], r[10])
            for r in _load(3406, d['f_min_pres_votes'])
            if r[0] in e65 and e65[r[0]][1] >= d['f_min_xwalk_voters']]
    d["f_prec_n_xwalk"] = len(keep)
    xs, ys = [k[0] for k in keep], [k[1] for k in keep]
    ctrl = [[k[2] for k in keep], [k[3] for k in keep], [k[4] for k in keep],
            [k[5] for k in keep], [math.log(k[6]) for k in keep]]
    d["f_elec65_raw"] = _pearson(xs, ys)
    d["f_elec65_partial_mag"] = abs(_partial_corr(ys, xs, ctrl))  # sign in the anchor

    # Crosswalk coverage, the caveat the paragraph closes on. ON THE ACTIVE-REGISTRANT
    # BASIS, and the basis is now named in the paper's own sentence — see ledger item C4.
    # It used to pair a statewide PRECINCT-COUNT figure (86.7%, and stale: the crosswalk
    # has grown three times since it was measured) with an Okanogan ACTIVE-VOTER figure,
    # in one parenthesis, as though the two were a like-for-like pair.
    for tag, scope in (("all", ""), ("okanogan", " AND UPPER(v.county_name) = 'OKANOGAN'")):
        tot, hit = con.execute(f"""
            SELECT COUNT(*), SUM(CASE WHEN x.precinct_id IS NOT NULL THEN 1 ELSE 0 END)
            FROM vrdb.voters v LEFT JOIN vrdb_precinct_crosswalk x
              ON UPPER(TRIM(v.county_name)) = UPPER(TRIM(x.county_name))
             AND UPPER(TRIM(v.precinct_code)) = UPPER(TRIM(x.vrdb_precinct_code))
            WHERE v.status_code = 'A'{scope}""").fetchone()
        d[f"f_xwalk_{tag}"] = 100.0 * hit / tot


def derive() -> dict:
    d: dict = {}
    con = duckdb.connect(VRDB, read_only=True)

    for date, tag in ELECTIONS:
        # Rate and composition in one pass: eligible registrants and whether they voted.
        rows = con.execute(f"""
            WITH e AS (SELECT {_band(date)} b,
                              CASE WHEN h.state_voter_id IS NOT NULL THEN 1 ELSE 0 END v
                       FROM voters v {_voted(date)}
                       WHERE v.birthdate IS NOT NULL AND {_age(date)} >= 18
                         AND v.registration_date IS NOT NULL
                         AND v.registration_date <= DATE '{date}')
            SELECT b, COUNT(*), SUM(v) FROM e GROUP BY 1""").fetchall()
        roll = {b: 0 for b in BANDS}
        voted = {b: 0 for b in BANDS}
        for b, n, v in rows:
            roll[b], voted[b] = int(n), int(v or 0)
        tot_v = sum(voted.values()) or 1
        for b in BANDS:
            d[f"{tag}_rate_{b}"] = 100.0 * voted[b] / (roll[b] or 1)
            d[f"{tag}_comp_{b}"] = 100.0 * voted[b] / tot_v
        d[f"{tag}_rate_all"] = 100.0 * tot_v / (sum(roll.values()) or 1)
        d[f"{tag}_analyzable"] = tot_v

        # Coverage against the certified count.
        d[f"{tag}_official"] = OFFICIAL[date]
        d[f"{tag}_infile"], = con.execute(f"""
            SELECT COUNT(DISTINCT state_voter_id) FROM voting_history
            WHERE election_date = DATE '{date}'""").fetchone()
        # "Analyzable (roll + YOB)" means exactly what it says: on the current roll, with a
        # year of birth. NO age filter — adding `>= 18` here was wrong and put this column
        # one record low in 2022 and 2024, because a handful of ballot-returners compute as
        # under 18 under the year-difference convention. The rounding check caught it; the
        # tolerance had not, because one record in 3.9 million is inside any sane tolerance
        # and the figure was still not the one the paper prints.
        d[f"{tag}_analyzable"], = con.execute(f"""
            SELECT COUNT(*) FROM voters v {_voted(date)}
            WHERE h.state_voter_id IS NOT NULL AND v.birthdate IS NOT NULL""").fetchone()
        tot_v = d[f"{tag}_analyzable"]
        d[f"{tag}_infile_pct"] = 100.0 * d[f"{tag}_infile"] / OFFICIAL[date]
        d[f"{tag}_cov_pct"] = 100.0 * tot_v / OFFICIAL[date]
        d[f"{tag}_residual"] = OFFICIAL[date] - tot_v
        d[f"{tag}_residual_pct"] = 100.0 * d[f"{tag}_residual"] / OFFICIAL[date]

        # Bounding: what the 65+ share would be if every missing ballot were cast by an
        # under-65, and if every one were cast by a 65+.
        #
        # THE NUMERATOR MUST SIT ON THE SAME BASIS AS `analyzable`, which is the roll-and-YOB
        # set WITHOUT the registration-date filter. Taking the 65+ count from the
        # rate-eligible (registration-filtered) set instead mixes the two and moved the 2021
        # upper bound 42.6 -> 42.54. It also explains a pair in the paper that looks like an
        # inconsistency and is not: the 2021 65+ share is 36.7497 on the rate basis and
        # 36.7508 on the coverage basis, so the composition table rounds it to 36.7 and the
        # bounding table to 36.8. Both are right; they are different denominators.
        n65, = con.execute(f"""
            SELECT COUNT(*) FROM voters v {_voted(date)}
            WHERE h.state_voter_id IS NOT NULL AND v.birthdate IS NOT NULL
              AND {_age(date)} >= 65""").fetchone()
        res = d[f"{tag}_residual"]
        d[f"{tag}_obs65"] = 100.0 * n65 / tot_v
        d[f"{tag}_min65"] = 100.0 * n65 / (tot_v + res)
        d[f"{tag}_max65"] = 100.0 * (n65 + res) / (tot_v + res)

        # Finer cohorts, for the sensitivity table.
        a = _age(date)
        fine = con.execute(f"""
            WITH e AS (SELECT CASE WHEN {a}<25 THEN '18-24' WHEN {a}<30 THEN '25-29'
                                   WHEN {a}<45 THEN '30-44' WHEN {a}<65 THEN '45-64'
                                   WHEN {a}<75 THEN '65-74' ELSE '75+' END b
                       FROM voters v {_voted(date)}
                       WHERE h.state_voter_id IS NOT NULL AND v.birthdate IS NOT NULL
                         AND {a} >= 18 AND v.registration_date <= DATE '{date}')
            SELECT b, COUNT(*) FROM e GROUP BY 1""").fetchall()
        fd = dict(fine)
        ft = sum(fd.values()) or 1
        for b in ("18-24", "25-29", "30-44", "45-64", "65-74", "75+"):
            d[f"{tag}_fine_{b}"] = 100.0 * fd.get(b, 0) / ft

        # Geography: 65+ share of the electorate, four ways.
        geo = con.execute(f"""
            WITH e AS (SELECT UPPER(v.county_name) c, {a} ag
                       FROM voters v {_voted(date)}
                       WHERE h.state_voter_id IS NOT NULL AND v.birthdate IS NOT NULL
                         AND {a} >= 18 AND v.registration_date <= DATE '{date}')
            SELECT CASE WHEN c='KING' THEN 'king' ELSE 'rest' END,
                   CASE WHEN c IN {METRO} THEN 'metro' ELSE 'rural' END,
                   COUNT(*), COUNT(*) FILTER (WHERE ag>=65) FROM e GROUP BY 1, 2""").fetchall()
        agg: dict[str, list[int]] = {}
        for k1, k2, n, n65g in geo:
            for k in (k1, k2):
                agg.setdefault(k, [0, 0])
                agg[k][0] += int(n)
                agg[k][1] += int(n65g)
        for k in ("king", "rest", "metro", "rural"):
            n, n65g = agg.get(k, [1, 0])
            d[f"{tag}_geo_{k}"] = 100.0 * n65g / (n or 1)

        # Median age of the electorate.
        d[f"{tag}_median"], = con.execute(f"""
            SELECT median({a}) FROM voters v {_voted(date)}
            WHERE h.state_voter_id IS NOT NULL AND v.birthdate IS NOT NULL AND {a} >= 18
              AND v.registration_date <= DATE '{date}'""").fetchone()

    # Scale of the two source tables, and the retained snapshot. Stated in the abstract and
    # the methods note and probed nowhere until 2026-08-02.
    d["roll_m"], = con.execute(
        "SELECT COUNT(*) / 1e6 FROM voters").fetchone()
    d["history_m"], = con.execute(
        "SELECT COUNT(*) / 1e6 FROM voting_history").fetchone()
    # The subset that can carry an age. The abstract used to call all 27.1M
    # records "with the voter's year of birth"; 3.05% of them match no roll row,
    # so they carry no year of birth and enter no result in this paper. The
    # validation table's "In file" vs "Analyzable" columns always said so — the
    # abstract's compression did not.
    d["history_aged_m"], = con.execute("""
        SELECT COUNT(*) / 1e6 FROM voting_history h
        JOIN voters v USING (state_voter_id) WHERE v.birthdate IS NOT NULL""").fetchone()
    d["history_dates"], = con.execute(
        "SELECT COUNT(DISTINCT election_date) FROM voting_history").fetchone()
    d["history_aged_pct"] = 100.0 * d["history_aged_m"] / d["history_m"]
    d["snapshot_m"], = con.execute(
        "SELECT COUNT(*) / 1e6 FROM voters_20230901").fetchone()

    # Roll attrition 2023 -> 2026. The paper reads this as evidence that leaving the roll is
    # age-loaded, which is the mechanism behind the survivorship bound, so it is a result
    # rather than a description.
    left, left_k, left_pct, left_65, stay_65 = con.execute("""
        WITH s AS (SELECT state_voter_id, birthdate FROM voters_20230901
                   WHERE birthdate IS NOT NULL),
             j AS (SELECT s.birthdate, (v.state_voter_id IS NULL) AS gone
                   FROM s LEFT JOIN voters v USING (state_voter_id))
        SELECT COUNT(*) FILTER (WHERE gone),
               COUNT(*) FILTER (WHERE gone) / 1e3,
               100.0 * COUNT(*) FILTER (WHERE gone) / COUNT(*),
               100.0 * COUNT(*) FILTER (WHERE gone AND date_diff('year', birthdate,
                                                                 DATE '2023-09-01') >= 65)
                     / NULLIF(COUNT(*) FILTER (WHERE gone), 0),
               100.0 * COUNT(*) FILTER (WHERE NOT gone AND date_diff('year', birthdate,
                                                                     DATE '2023-09-01') >= 65)
                     / NULLIF(COUNT(*) FILTER (WHERE NOT gone), 0)
        FROM j""").fetchone()
    d["left_n"], d["left_k"], d["left_pct"] = int(left), float(left_k), float(left_pct)
    d["left_65"], d["stay_65"] = float(left_65), float(stay_65)

    # Coverage range across the five cycles, which the prose states as a span.
    d["cov_lo"] = min(d[f"{t}_cov_pct"] for t in ("e21", "e22", "e23", "e24", "e25"))
    d["cov_hi"] = max(d[f"{t}_cov_pct"] for t in ("e21", "e22", "e23", "e24", "e25"))

    # Habitual core: the share of each off-year's returners who also voted in 2024. The
    # abstract states it as a span, so the span needs derived endpoints.
    for date, tag in (("2021-11-02", "e21"), ("2023-11-07", "e23"), ("2025-11-04", "e25")):
        d[f"{tag}_core"], = con.execute(f"""
            WITH off AS (SELECT DISTINCT state_voter_id FROM voting_history
                         WHERE election_date = DATE '{date}'),
                 pres AS (SELECT DISTINCT state_voter_id FROM voting_history
                          WHERE election_date = DATE '2024-11-05')
            SELECT 100.0 * COUNT(*) FILTER (
                     WHERE state_voter_id IN (SELECT state_voter_id FROM pres))
                   / COUNT(*) FROM off""").fetchone()
    d["core_lo"] = min(d[f"{t}_core"] for t in ("e21", "e23", "e25"))
    d["core_hi"] = max(d[f"{t}_core"] for t in ("e21", "e23", "e25"))

    # --- The habitual core is SURVIVORSHIP-INFLATED, and by how much (2026-08-11)
    #
    # Raised by an external referee and confirmed. Membership in a measured off-year
    # electorate requires survival on the April 2026 roll, so a voter who cast a 2021
    # ballot and then died or left is dropped from BOTH numerator and denominator of the
    # overlap — and that population is guaranteed not to appear in the 2024 electorate.
    # The overlap is therefore biased UP, and the bias grows with distance from 2024.
    #
    # `voters_20230901` recovers the subset of those drop-offs still registered in
    # September 2023, so each correction here is a LOWER BOUND on the inflation: anyone
    # who left between the election and that snapshot is invisible to it too. The 2025
    # row is the control — four months from the roll, 0.09 points — which is what tells
    # you the mechanism is time-distance rather than something else.
    _corr: dict[str, float] = {}
    for date, tag in (("2021-11-02", "e21"), ("2023-11-07", "e23"), ("2025-11-04", "e25")):
        gone, = con.execute(f"""
            SELECT COUNT(*) FROM voters_20230901 s
            LEFT JOIN voters v USING (state_voter_id)
            WHERE v.state_voter_id IS NULL
              AND EXISTS (SELECT 1 FROM voting_history h
                          WHERE h.state_voter_id = s.state_voter_id
                            AND h.election_date = DATE '{date}')""").fetchone()
        n_off, = con.execute(f"""
            SELECT COUNT(DISTINCT state_voter_id) FROM voting_history
            WHERE election_date = DATE '{date}'""").fetchone()
        _corr[tag] = d[f"{tag}_core"] * n_off / (n_off + gone)
    # Only what a probe reads goes into `d`. The paper prints 2021 and 2023 corrected, the
    # span, and 2025's inflation as the control — not 2025's corrected level itself.
    d["e21_core_corr"], d["e23_core_corr"] = _corr["e21"], _corr["e23"]
    d["core_corr_lo"], d["core_corr_hi"] = min(_corr.values()), max(_corr.values())
    d["core_infl_2025"] = d["e25_core"] - _corr["e25"]

    # --- Interpretation §: the OTHER direction, and the core/only split (2026-08-11)
    #
    # THE BASIS QUESTION, SETTLED BY MEASUREMENT BEFORE ANYTHING WAS WRITTEN. The
    # Interpretation paragraph states two overlap spans in one sentence, and the
    # two halves sit on DIFFERENT bases. Both were computed both ways first:
    #
    #                                    raw history      roll-joined (aged)
    #   off -> pres (habitual core)      92.20-97.28      95.47-97.54
    #   pres -> off (returned off-year)  42.55-48.25      42.37-49.18
    #
    # The paper prints 92-97 and 42-48, so BOTH spans are on the raw basis and
    # `core_lo`/`core_hi` above are the right keys for the first. This is the
    # fifth instance in this series of "two quantities under one name", and the
    # one already on the record: the cross-state harmonizer quotes the habitual
    # core as 95.5-97.5, which is the AGED basis of the same quantity. Both are
    # right; they are not the same number, and neither paper may quote the
    # other's. Registered in docs/reference/derivation-bases.csv.
    # The per-year values are LOCAL, not keys in `d`. The paper publishes only
    # the span, so storing three intermediates nothing consumes would add three
    # rows to this verifier's `no-probe` count — the exact "derived and never
    # read" shape `mutation_probe_verifiers.py` exists to surface, and the shape
    # in which `e3938bd` hid four keys that carried published sentences.
    _presret = []
    for date in ("2021-11-02", "2023-11-07", "2025-11-04"):
        v, = con.execute(f"""
            WITH pres AS (SELECT DISTINCT state_voter_id FROM voting_history
                          WHERE election_date = DATE '2024-11-05'),
                 off AS (SELECT DISTINCT state_voter_id FROM voting_history
                         WHERE election_date = DATE '{date}')
            SELECT 100.0 * COUNT(*) FILTER (
                     WHERE state_voter_id IN (SELECT state_voter_id FROM off))
                   / COUNT(*) FROM pres""").fetchone()
        _presret.append(float(v))
    # HALF-UP ROUNDED, per the author's call 2026-08-18 (ledger open item 1,
    # now resolved; correction C13). The measured span is 42.5455-48.2530 and
    # the paper prints "43-48%", so both endpoints are half-up roundings of the
    # unrounded values. `math.floor(x + 0.5)` rather than `round()` because
    # round() is banker's rounding and would send an exact .5 to even.
    #
    # ⚠ This paper now carries TWO integer spans on TWO conventions, and the
    # split is deliberate and declared in docs/reference/derivation-bases.csv.
    # Appendix A's contested-race span stays TRUNCATED (f_ro_npcon_*_tr) because
    # half-up does not work for it: its measured endpoints are 16.5684 and
    # 17.2224, which both round to 17, so half-up would print the degenerate
    # "17-17%". Do not "harmonise" the two without re-reading that constraint.
    #
    # A real drift still fails: if the low endpoint fell to 42.4 the half-up
    # value would be 42 and the probe would break.
    d["presret_lo_rd"] = float(math.floor(min(_presret) + 0.5))
    d["presret_hi_rd"] = float(math.floor(max(_presret) + 0.5))

    # 2024 presidential voters split by whether they ALSO voted in the 2023
    # off-year — the paper's "habitual core" vs "presidential-only" contrast.
    # AGED basis (roll-joined, birthdate present), because the split is reported
    # by age band and an unaged voter carries no band; ages are assigned at the
    # 2024 election, per the paper's stated per-election cohort convention.
    for is_both, pfx in ((True, "hab"), (False, "presonly")):
        n_m, p65, u30 = con.execute(f"""
            WITH pres AS (SELECT DISTINCT state_voter_id FROM voting_history
                          WHERE election_date = DATE '2024-11-05'),
                 off AS (SELECT DISTINCT state_voter_id FROM voting_history
                         WHERE election_date = DATE '2023-11-07'),
                 j AS (SELECT date_diff('year', v.birthdate, DATE '2024-11-05') AS ag
                       FROM pres p JOIN voters v USING (state_voter_id)
                       WHERE v.birthdate IS NOT NULL
                         AND (p.state_voter_id IN (SELECT state_voter_id FROM off))
                             = {str(is_both).upper()})
            SELECT COUNT(*) / 1e6,
                   100.0 * COUNT(*) FILTER (WHERE ag >= 65) / COUNT(*),
                   100.0 * COUNT(*) FILTER (WHERE ag < 30) / COUNT(*) FROM j""").fetchone()
        d[f"{pfx}_m"], d[f"{pfx}_65"], d[f"{pfx}_u30"] = float(n_m), float(p65), float(u30)

    # Years since registration at each election, ballot-returners. FOUND BY
    # AUDITING WHAT THE SECTION EXEMPTS RATHER THAN WHETHER IT PASSES: with
    # `interpretation` newly in AUDIT_BOUNDS the gate reported it fully mapped,
    # but "a median of about 16-17 years ... versus 12" is three bare integers
    # with no unit suffix, so `^\d{1,2}$` waived all three. `strict_units` only
    # reaches tokens written with % or ×, which these are not. This paper's own
    # corrections ledger had listed registration tenure as unprobed since
    # 2026-08-06; the gate would have gone on reporting the section complete.
    # Off-year values LOCAL, for the same reason as `_presret` above: only the
    # presidential median and the off-year span are published.
    _tenure = {}
    for date, tag in (("2024-11-05", "e24"), ("2021-11-02", "e21"),
                      ("2023-11-07", "e23"), ("2025-11-04", "e25")):
        v, = con.execute(f"""
            WITH r AS (SELECT DISTINCT state_voter_id FROM voting_history
                       WHERE election_date = DATE '{date}')
            SELECT median(date_diff('year', v.registration_date, DATE '{date}'))
            FROM r JOIN voters v USING (state_voter_id)
            WHERE v.registration_date IS NOT NULL
              AND v.registration_date <= DATE '{date}'""").fetchone()
        _tenure[tag] = float(v)
    d["e24_tenure"] = _tenure["e24"]
    d["tenure_off_lo"] = min(_tenure[t] for t in OFF_YEARS)
    d["tenure_off_hi"] = max(_tenure[t] for t in OFF_YEARS)

    # --- Registration-date validation (2026-08-14, referee item 1) -------
    # WAC 434-324-045 lets an update's receipt date become the registration date, so
    # `registration_date <= election` could in principle misdate updaters and the
    # decomposition's reconstructed rolls with them. Measured two ways, both derived
    # here so the paper's validation is asserted rather than narrated:
    #   (a) SNAPSHOT IDENTITY — of registrants present in BOTH the September-2023
    #       snapshot and the April-2026 roll, the share whose registration_date is
    #       byte-identical across the 31 months, and the share re-stamped LATER;
    #   (b) the PER-ELECTION CEILING — credited voters at E whose current date
    #       postdates E (their own ballot credit proves registration by E), and the
    #       largest movement any published participation rate shows when they and
    #       every other provably-registered voter are reclassified as eligible.
    (d["regv_common_m"], d["regv_same_pct"],
     d["regv_restamp_pct"]) = (float(x) for x in con.execute("""
        WITH j AS (SELECT s.registration_date r23, v.registration_date r26
                   FROM voters_20230901 s JOIN voters v USING (state_voter_id))
        SELECT COUNT(*)/1e6,
               100.0*COUNT(*) FILTER (WHERE r23 = r26)/COUNT(*),
               100.0*COUNT(*) FILTER (WHERE r26 > r23)/COUNT(*) FROM j""").fetchone())
    _late, _rdelta = [], []
    for date, _tg in ELECTIONS:
        row = con.execute(f"""
            WITH earliest AS (SELECT state_voter_id, MIN(election_date) fe
                              FROM voting_history GROUP BY 1),
            b AS (SELECT (v.registration_date IS NOT NULL
                          AND v.registration_date <= DATE '{date}') reg_ok,
                         (ee.fe IS NOT NULL AND ee.fe <= DATE '{date}') voted_by,
                         (h.state_voter_id IS NOT NULL) voted_e
                  FROM voters v
                  LEFT JOIN earliest ee USING (state_voter_id)
                  LEFT JOIN (SELECT DISTINCT state_voter_id FROM voting_history
                             WHERE election_date = DATE '{date}') h
                         USING (state_voter_id)
                  WHERE v.birthdate IS NOT NULL AND {_age(date)} >= 18)
            SELECT 100.0*COUNT(*) FILTER (WHERE voted_e AND NOT reg_ok)
                   / NULLIF(COUNT(*) FILTER (WHERE voted_e), 0),
                   100.0*COUNT(*) FILTER (WHERE voted_e AND reg_ok)
                   / NULLIF(COUNT(*) FILTER (WHERE reg_ok), 0),
                   100.0*COUNT(*) FILTER (WHERE voted_e AND (reg_ok OR voted_by))
                   / NULLIF(COUNT(*) FILTER (WHERE reg_ok OR voted_by), 0)
            FROM b""").fetchone()
        _late.append(float(row[0]))
        _rdelta.append(abs(float(row[2]) - float(row[1])))
    d["regv_late_max"] = max(_late)
    d["regv_rate_maxdelta"] = max(_rdelta)

    # --- Longitudinal generals participation (2026-08-14, referee item 4) ---
    # The measure that EARNS the word "habitual": how many of the five 2021-2025
    # November generals each off-year electorate's members are credited in, against
    # the presidential electorate on the same panel. Current-roll panel, so the
    # neighbouring survivorship caveats apply here too.
    _GEN5 = "('2021-11-02','2022-11-08','2023-11-07','2024-11-05','2025-11-04')"
    _hm, _hg = [], []
    for date in ("2021-11-02", "2023-11-07", "2025-11-04"):
        m, g = con.execute(f"""
            WITH e AS (SELECT DISTINCT state_voter_id FROM voting_history
                       WHERE election_date = DATE '{date}'),
            k AS (SELECT e.state_voter_id, COUNT(DISTINCT h.election_date) n
                  FROM e JOIN voting_history h USING (state_voter_id)
                  WHERE h.election_date IN {_GEN5} GROUP BY 1)
            SELECT AVG(n), 100.0*COUNT(*) FILTER (WHERE n >= 4)/COUNT(*)
            FROM k""").fetchone()
        _hm.append(float(m))
        _hg.append(float(g))
    d["hab5_mean_lo"], d["hab5_mean_hi"] = min(_hm), max(_hm)
    d["hab5_ge4_lo"], d["hab5_ge4_hi"] = min(_hg), max(_hg)
    d["hab5_pres_mean"], d["hab5_pres_ge4"] = (float(x) for x in con.execute(f"""
        WITH p AS (SELECT DISTINCT state_voter_id FROM voting_history
                   WHERE election_date = DATE '2024-11-05'),
        k AS (SELECT p.state_voter_id, COUNT(DISTINCT h.election_date) n
              FROM p JOIN voting_history h USING (state_voter_id)
              WHERE h.election_date IN {_GEN5} GROUP BY 1)
        SELECT AVG(n), 100.0*COUNT(*) FILTER (WHERE n >= 4)/COUNT(*)
        FROM k""").fetchone())

    # Cited-literature figures in the Interpretation section. TRANSCRIBED, not
    # derived — same treatment as the OFFICIAL turnout benchmarks above, and
    # asserted at tolerance 0 because a transcription's only failure mode is a
    # typo. They are here rather than in COVERAGE_EXEMPT_LITERAL because a
    # literal exemption is matched against the BARE token document-wide, and all
    # three of these collide with real results elsewhere in this paper:
    #   58.4  also the 18-29 participation rate (rates table + prose) and an
    #         Appendix H retention cell
    #   49.7  also Cowlitz's 2025 off-year 65+ share in Appendix E, and an
    #         Appendix H cell
    #   415   also the upper end of the 298K-415K inactive-registrant bound
    # Waiving any of them by literal would punch a hole straight through a
    # section the audit currently reports as fully mapped.
    d.update({
        # Lucero et al. (2025), cities that switched to on-cycle elections:
        # voters over 45 as a share of the off-cycle and presidential electorates.
        "lit_lucero_off45": 58.4, "lit_lucero_pres45": 49.7,
        # Hajnal et al., cited inside the Lucero sentence: the over-55 gap.
        "lit_hajnal_over55_gap": 22,
        # Ornstein (2024) on California SB 415: the bill number and the number of
        # local governments in the study.
        "lit_sb_number": 415, "lit_ornstein_govts": 236,
    })

    # Off-year averages, for the "who is counted" table.
    for b in BANDS:
        d[f"off_comp_{b}"] = sum(d[f"{t}_comp_{b}"] for t in OFF_YEARS) / 3.0
    # Official turnout rate for the 2021 example the methods note quotes: certified ballots
    # over registered voters as the Secretary of State reports it, not a file-derived rate.
    d["e21_official_turnout"] = 39.38
    d["off_median"] = sum(d[f"{t}_median"] for t in OFF_YEARS) / 3.0

    # Official statewide turnout, WA SoS. EXTERNAL benchmarks, like OFFICIAL
    # above: the paper compares its file-derived reconstruction against a rate
    # the file cannot produce, so these are transcribed, not derived. Asserted
    # at tolerance 0 — a transcription's only failure mode is a typo.
    d.update({"off_turnout_2021": 39.38, "off_turnout_2022": 63.82,
              "off_turnout_2023": 36.41, "off_turnout_2024": 78.95,
              "off_turnout_2025": 39.24})

    # --- Reconstruction vs official, both sides (added 2026-08-09) -------
    #
    # The rate table's caveat used to say the reconstruction sits below official
    # turnout because "a later (larger) roll mechanically pulls them down", with
    # 2021 as "the exception". Measured, the reconstructed roll is SMALLER than
    # the official one in 2021 and 2022 and larger only from 2024, and the
    # numerator is short in all five years — so the stated mechanism was wrong
    # for three of five years and 2021's agreement is two ~9.2% shortfalls
    # cancelling. Both deltas are derived here so the corrected table cannot
    # drift back.
    for date, tag in ELECTIONS:
        year = date[:4]
        recon_roll, = con.execute(f"""
            SELECT COUNT(*) FROM voters v
            WHERE v.birthdate IS NOT NULL AND {_age(date)} >= 18
              AND v.registration_date IS NOT NULL
              AND v.registration_date <= DATE '{date}'""").fetchone()
        recon_voted, = con.execute(f"""
            SELECT COUNT(*) FROM voters v {_voted(date)}
            WHERE h.state_voter_id IS NOT NULL AND v.birthdate IS NOT NULL
              AND {_age(date)} >= 18
              AND v.registration_date IS NOT NULL
              AND v.registration_date <= DATE '{date}'""").fetchone()
        # Official registered = certified ballots / official turnout rate. The SoS
        # publishes both on the same page, so this is arithmetic on transcribed
        # figures, not a second source.
        official_roll = OFFICIAL[date] / (d[f"off_turnout_{year}"] / 100.0)
        d[f"{tag}_recon_roll_delta"] = 100.0 * (recon_roll - official_roll) / official_roll
        d[f"{tag}_recon_ballot_delta"] = (
            100.0 * (recon_voted - OFFICIAL[date]) / OFFICIAL[date])
        d[f"{tag}_recon_rate"] = 100.0 * recon_voted / (recon_roll or 1)
        d[f"{tag}_elig65"], = con.execute(f"""
            SELECT 100.0 * SUM(CASE WHEN {_age(date)} >= 65 THEN 1 ELSE 0 END) / COUNT(*)
            FROM voters v
            WHERE v.birthdate IS NOT NULL AND {_age(date)} >= 18
              AND v.registration_date IS NOT NULL
              AND v.registration_date <= DATE '{date}'""").fetchone()
        # The paper prints the sign as a literal "−" outside the capture group,
        # so the probe needs the magnitude. Kept as separate keys rather than a
        # tolerance on sign, because a sign flip here IS the defect being
        # guarded — 2021 and 2022 run the opposite way to 2024 and 2025.
        d[f"{tag}_recon_roll_delta_abs"] = abs(d[f"{tag}_recon_roll_delta"])
        d[f"{tag}_recon_ballot_delta_abs"] = abs(d[f"{tag}_recon_ballot_delta"])

        # MATCHED BASIS (added 2026-08-09, round 3). The delta above compares a
        # FULL-roll reconstruction against an official figure that counts only
        # ACTIVE registrants. On that mismatch the delta flips sign at 2023 and
        # invites a causal story that is not there. Restricted to active
        # registrants the reconstructed roll is smaller in EVERY year, shrinking
        # monotonically as the registration-date filter has less history to
        # discard. Both are derived so the paper cannot show one without the other.
        recon_roll_active, = con.execute(f"""
            SELECT COUNT(*) FROM voters v
            WHERE v.birthdate IS NOT NULL AND v.status_code = 'A'
              AND {_age(date)} >= 18
              AND v.registration_date IS NOT NULL
              AND v.registration_date <= DATE '{date}'""").fetchone()
        recon_voted_active, = con.execute(f"""
            SELECT COUNT(*) FROM voters v {_voted(date)}
            WHERE h.state_voter_id IS NOT NULL AND v.birthdate IS NOT NULL
              AND v.status_code = 'A' AND {_age(date)} >= 18
              AND v.registration_date IS NOT NULL
              AND v.registration_date <= DATE '{date}'""").fetchone()
        d[f"{tag}_recon_roll_active_delta"] = (
            100.0 * (recon_roll_active - official_roll) / official_roll)
        d[f"{tag}_recon_roll_active_delta_abs"] = abs(
            d[f"{tag}_recon_roll_active_delta"])
        d[f"{tag}_recon_rate_active"] = (
            100.0 * recon_voted_active / (recon_roll_active or 1))
        d[f"{tag}_recon_inactive_k"] = (recon_roll - recon_roll_active) / 1000.0
        d[f"{tag}_recon_inactive_infl"] = (
            100.0 * (recon_roll - recon_roll_active) / recon_roll_active)

    _infl = [d[f"{tg}_recon_inactive_infl"] for _, tg in ELECTIONS]
    d["recon_inactive_infl_min"], d["recon_inactive_infl_max"] = min(_infl), max(_infl)

    # --- Das-Gupta decomposition, all three off-years (added 2026-08-09) --
    #
    # Previously UNCHECKED, and that is how the 2023 and 2021 figures were
    # published under the wrong definition: the paper quoted
    # |rate| / (|rate| + |roll|) while calling it the rate effect's share of the
    # RISE. Those differ whenever the roll effect is negative, which it is in
    # both those years — and a share of the rise below 100% with a negative roll
    # effect is arithmetically impossible, so the sentence refuted itself.
    # BOTH ratios are derived, under names that cannot be confused.
    def _cohorts(date):
        rows = con.execute(f"""
            WITH e AS (SELECT {_band(date)} b,
                              CASE WHEN h.state_voter_id IS NOT NULL THEN 1 ELSE 0 END v
                       FROM voters v {_voted(date)}
                       WHERE v.birthdate IS NOT NULL AND {_age(date)} >= 18
                         AND v.registration_date IS NOT NULL
                         AND v.registration_date <= DATE '{date}')
            SELECT b, COUNT(*), SUM(v) FROM e GROUP BY 1""").fetchall()
        return {b: (float(n), float(v or 0)) for b, n, v in rows}

    def _share(roll, rate, target):
        vs = {b: roll[b] * rate[b] for b in BANDS}
        return vs[target] / sum(vs.values())

    _P = _cohorts("2024-11-05")
    _rollP = {b: _P[b][0] for b in BANDS}
    _rateP = {b: _P[b][1] / _P[b][0] for b in BANDS}
    for date, tag in [("2025-11-04", "e25"), ("2023-11-07", "e23"),
                      ("2021-11-02", "e21")]:
        O = _cohorts(date)
        rollO = {b: O[b][0] for b in BANDS}
        rateO = {b: O[b][1] / O[b][0] for b in BANDS}
        for target, key in (("65+", "65"), ("18-29", "18")):
            s_pp = _share(_rollP, _rateP, target)
            s_oo = _share(rollO, rateO, target)
            s_op = _share(rollO, _rateP, target)
            s_po = _share(_rollP, rateO, target)
            comp = 0.5 * ((s_op - s_pp) + (s_oo - s_po)) * 100
            rate = 0.5 * ((s_po - s_pp) + (s_oo - s_op)) * 100
            rise = (s_oo - s_pp) * 100
            d[f"{tag}_decomp{key}_rise"] = rise
            d[f"{tag}_decomp{key}_rate"] = rate
            d[f"{tag}_decomp{key}_roll"] = comp
            d[f"{tag}_decomp{key}_of_rise"] = 100.0 * rate / rise
            d[f"{tag}_decomp{key}_of_move"] = (
                100.0 * abs(rate) / (abs(rate) + abs(comp)))
            # Magnitudes, for the cells the paper prints with a literal sign.
            d[f"{tag}_decomp{key}_rise_abs"] = abs(rise)
            d[f"{tag}_decomp{key}_rate_abs"] = abs(rate)
            d[f"{tag}_decomp{key}_roll_abs"] = abs(comp)

    # --- Appendix H banding robustness (added 2026-08-09) ----------------
    #
    # Appendix H used to argue "a monotone curve means every possible cut of the
    # age axis preserves the ordering; no alternative bracket scheme could
    # reverse it." The retention curve is NOT monotone (it peaks at 79 and falls
    # to 59.5% by 95), and monotone retention would not imply monotone
    # composition anyway, since composition depends on how many people sit at
    # each age. The claim is now made on the composition measure directly, so it
    # is derived here rather than argued.
    _bands_sql = """
        CASE WHEN {y} - by_ < 65 THEN 'lt65' WHEN {y} - by_ < 70 THEN '65-69'
             WHEN {y} - by_ < 75 THEN '70-74' WHEN {y} - by_ < 80 THEN '75-79'
             WHEN {y} - by_ < 85 THEN '80-84' WHEN {y} - by_ < 90 THEN '85-89'
             ELSE '90+' END"""
    _base = """
        WITH b AS (
          SELECT EXTRACT(year FROM v.birthdate) by_,
                 CASE WHEN h24.state_voter_id IS NOT NULL THEN 1 ELSE 0 END v24,
                 CASE WHEN h25.state_voter_id IS NOT NULL THEN 1 ELSE 0 END v25
          FROM voters v
          LEFT JOIN (SELECT DISTINCT state_voter_id FROM voting_history
                     WHERE election_date = DATE '2024-11-05') h24 USING (state_voter_id)
          LEFT JOIN (SELECT DISTINCT state_voter_id FROM voting_history
                     WHERE election_date = DATE '2025-11-04') h25 USING (state_voter_id)
          WHERE v.birthdate IS NOT NULL
            AND 2024 - EXTRACT(year FROM v.birthdate) >= 18
            AND 2025 - EXTRACT(year FROM v.birthdate) >= 18)"""
    _a = dict(con.execute(
        _base + f" SELECT {_bands_sql.format(y=2024)} bd, SUM(v24) FROM b GROUP BY 1"
    ).fetchall())
    _b = dict(con.execute(
        _base + f" SELECT {_bands_sql.format(y=2025)} bd, SUM(v25) FROM b GROUP BY 1"
    ).fetchall())
    _t24, _t25 = sum(_a.values()), sum(_b.values())
    for k in ("lt65", "65-69", "70-74", "75-79", "80-84", "85-89", "90+"):
        d[f"bandratio_{k}"] = (_b[k] / _t25) / (_a[k] / _t24)
    d["bandratio_reversal"] = d["bandratio_85-89"] - d["bandratio_90+"]

    # Single-age retention at the ages Appendix H names in prose. Derived here so
    # those sentences are asserted rather than merely printed by a diag script.
    _ret = dict(con.execute("""
        WITH b AS (
          SELECT 2025 - EXTRACT(year FROM v.birthdate) AS a,
                 CASE WHEN h24.state_voter_id IS NOT NULL THEN 1 ELSE 0 END v24,
                 CASE WHEN h25.state_voter_id IS NOT NULL THEN 1 ELSE 0 END v25
          FROM voters v
          LEFT JOIN (SELECT DISTINCT state_voter_id FROM voting_history
                     WHERE election_date = DATE '2024-11-05') h24 USING (state_voter_id)
          LEFT JOIN (SELECT DISTINCT state_voter_id FROM voting_history
                     WHERE election_date = DATE '2025-11-04') h25 USING (state_voter_id)
          WHERE v.birthdate IS NOT NULL)
        SELECT a, 100.0 * SUM(CASE WHEN v24 = 1 AND v25 = 1 THEN 1 ELSE 0 END)
                   / NULLIF(SUM(v24), 0)
        FROM b WHERE a BETWEEN 19 AND 95 GROUP BY 1""").fetchall())
    for _a in (60, 64, 66, 79, 80, 84, 90, 95):
        d[f"h_ret_{_a}"] = float(_ret[_a])
    d["h_peak_ret"] = max(_ret.values())
    d["h_peak_age"] = max(_ret, key=_ret.get)
    d["h_step_64_66"] = d["h_ret_66"] - d["h_ret_64"]
    d["h_step_60_64"] = d["h_ret_64"] - d["h_ret_60"]

    # --- Appendix H: the PRINTED curve, and the prose around it (2026-08-11)
    #
    # WHY THIS EXISTS DESPITE AN UNCHECKED ENTRY SAYING IT NEED NOT. That entry
    # reads "78 rows at a granularity where a probe per cell buys no additional
    # failure mode". Two things are wrong with it and both are already recorded
    # against its twin. First, the appendix prints FIFTEEN rows, not 78 — the
    # five-year steps — so this is 60 cells, one derivation and one row loop, the
    # same shape and the same cost as the Appendix E county table. Second, the
    # Appendix E exemption made the identical argument and an outside pass then
    # reported six wrong cells in it; they turned out to be a basis difference in
    # the reviewer's query, but NOTHING IN THIS FILE COULD HAVE TOLD THE
    # DIFFERENCE, which is the whole point. An unchecked entry is a claim about
    # coverage and nothing checks it.
    #
    # BASIS, taken from scripts/diag_wa_age_curve.py rather than guessed: age is
    # `2025 - YEAR(birthdate)`, the Roll column is every registrant at that age
    # in the April 2026 extract, and retention divides the both-voted count by
    # the 2024 voters. Note `_ret` above restricts to 19-95; age 18 must stay
    # out of any peak or extremum, because an 18-year-old in November 2025 was
    # 17 at the 2024 general and the retention cell has no honest denominator.
    #
    # TURNOUT DENOMINATORS CORRECTED 2026-08-13 (Pass 1 of the calculation
    # review). The two turnout columns divide by registrants enrolled on or
    # before EACH election — the body rate table's `_eligible` basis, which the
    # appendix claimed ("the same caveats as the body's rate table") while both
    # this derivation and the diag script divided by the whole April-2026 roll
    # at that age. The gap was +0.9 to +5.2 points on the 2024 column across
    # the printed rows. Retention is untouched: its denominator is 2024 voters.
    # The correction also retired "age 19 is the minimum of the young range" —
    # a denominator artifact (19-year-olds registered after Nov 2024 could not
    # have voted in it); the true minimum is the mid-20s trough at 25. Ledger
    # item C11 in docs/who-decides-wa-corrections-ledger.md.
    _curve = con.execute("""
        WITH v24 AS (SELECT DISTINCT state_voter_id FROM voting_history
                     WHERE election_date = DATE '2024-11-05'),
             v25 AS (SELECT DISTINCT state_voter_id FROM voting_history
                     WHERE election_date = DATE '2025-11-04'),
             base AS (SELECT 2025 - YEAR(v.birthdate) AS age,
                             (a.state_voter_id IS NOT NULL) AS v_24,
                             (b.state_voter_id IS NOT NULL) AS v_25,
                             (v.registration_date IS NOT NULL AND
                              v.registration_date <= DATE '2024-11-05') AS e_24,
                             (v.registration_date IS NOT NULL AND
                              v.registration_date <= DATE '2025-11-04') AS e_25
                      FROM voters v
                      LEFT JOIN v24 a USING (state_voter_id)
                      LEFT JOIN v25 b USING (state_voter_id)
                      WHERE v.birthdate IS NOT NULL)
        SELECT age, COUNT(*),
               100.0 * SUM(CASE WHEN v_24 AND e_24 THEN 1 ELSE 0 END)
                     / NULLIF(COUNT(*) FILTER (WHERE e_24), 0),
               100.0 * SUM(CASE WHEN v_25 AND e_25 THEN 1 ELSE 0 END)
                     / NULLIF(COUNT(*) FILTER (WHERE e_25), 0)
        FROM base WHERE age BETWEEN 18 AND 95 GROUP BY 1 ORDER BY 1""").fetchall()
    d["h_n_ages"] = len(_curve)
    _roll = {int(r[0]): int(r[1]) for r in _curve}
    _t24 = {int(r[0]): float(r[2]) for r in _curve}
    _t25 = {int(r[0]): float(r[3]) for r in _curve}
    for _a in range(20, 91, 5):                       # the fifteen printed rows
        d[f"hrow_{_a}_roll"] = _roll[_a]
        d[f"hrow_{_a}_t24"] = _t24[_a]
        d[f"hrow_{_a}_t25"] = _t25[_a]
        d[f"hrow_{_a}_ret"] = float(_ret[_a])

    # The young end, where the non-monotonicity is in TURNOUT and not retention —
    # the appendix says so explicitly, so both measures are asserted. The
    # minimum-of-the-young-range claim is asserted as the AGE holding it (the
    # tossup18_next_year pattern): on the retired whole-roll basis that age was
    # 19, which the eligibility correction exposed as a denominator artifact.
    for _a in (19, 20, 25):
        d[f"h_t24_{_a}"] = _t24[_a]
    d["h_t24_young_min_age"] = float(min(range(19, 30), key=lambda a: _t24[a]))
    for _a in (19, 21):
        d[f"h_ret_{_a}"] = float(_ret[_a])
    d["h_ret_20"] = float(_ret[20])

    # SLOPES, ALL COMPUTED ON UNROUNDED RETENTION. Three of the paper's printed
    # slopes are not: see the round_exempt entries in main() and the ledger item
    # they are drafted against. Freeze rule 3 is explicit that a figure computed
    # from other figures uses unrounded inputs, so the derivation stays unrounded
    # and the divergence is recorded rather than encoded.
    d["h_ramp_avg"] = (d["h_peak_ret"] - _ret[20]) / (79 - 20)
    d["h_slope_40_50"] = (_ret[50] - _ret[40]) / 10
    d["h_slope_60_65"] = (_ret[65] - _ret[60]) / 5
    d["h_slope_65_70"] = (_ret[70] - _ret[65]) / 5
    d["h_slope_64_66"] = d["h_step_64_66"] / 2
    d["h_slope_60_64"] = d["h_step_60_64"] / 4
    # "the steepest five-year stretch on the curve" — a superlative, which carries
    # no numeric token of its own, so it is checked as a figure: the age at which
    # the steepest five-year stretch begins must be 65 for the sentence to hold.
    d["h_steepest_5yr_start"] = max(range(19, 91), key=lambda a: _ret[a + 5] - _ret[a])
    # "declines from 80 onward" — the complement of the peak, which is asserted
    # separately. Derived rather than hardcoded so the two cannot drift apart in prose.
    d["h_decline_start"] = d["h_peak_age"] + 1
    d["h_step_93_94"] = _ret[94] - _ret[93]
    d["h_dip_51_52"] = abs(_ret[52] - _ret[51])
    d["h_dip_ratio"] = d["h_step_93_94"] / d["h_dip_51_52"]

    # --- Appendix E: all 39 counties, derived (added 2026-08-09) ---------
    #
    # This table used to sit in UNCHECKED ("a granularity where a probe per cell
    # would triple this file for no additional failure mode"), and the paper
    # cited the verifier as its source anyway. Spot-checking 12 of the 39 rows
    # found SIX wrong cells in four rows — last-digit errors of exactly the class
    # `check_rounding` exists to catch. One derivation and one row-loop is not
    # "tripling the file", and the exemption was wrong on its own terms.
    # KITTITAS/KLICKITAT LABEL CORRECTION (2026-08-15). The loader's county-code map
    # inverts the SoS KT/KS codes (documented in config/counties.py and
    # docs/known_issues.md since 2026-04-30), and the VRDB loader derives
    # `voters.county_name` from that same map — so the rows labelled KLICKITAT are
    # Kittitas County's registrants and vice versa. Caught by
    # scripts/diag_wa_roll_reconciliation.py against the certified 2025 turnout page
    # (Kittitas 32,251 registered vs Klickitat 16,421; our labels carried the
    # opposite). The load stays inverted deliberately — the precinct namespace and
    # the VRDB crosswalk are internally consistent on the inverted labels — so the
    # correction is applied HERE, at the only place a county label reaches a
    # published attribution. If the mapping is ever fixed and the VRDB reloaded,
    # this CASE double-swaps and diag_wa_roll_reconciliation.py fails loudly:
    # remove both together.
    _CTY_FIX = """CASE UPPER(TRIM(v.county_name))
                    WHEN 'KITTITAS' THEN 'KLICKITAT'
                    WHEN 'KLICKITAT' THEN 'KITTITAS'
                    ELSE UPPER(TRIM(v.county_name)) END"""
    for date, tag in [("2024-11-05", "e24"), ("2023-11-07", "e23"),
                      ("2025-11-04", "e25"), ("2021-11-02", "e21")]:
        for county, pct in con.execute(f"""
            SELECT {_CTY_FIX},
                   100.0 * SUM(CASE WHEN {_age(date)} >= 65 THEN 1 ELSE 0 END) / COUNT(*)
            FROM voters v {_voted(date)}
            WHERE h.state_voter_id IS NOT NULL AND v.birthdate IS NOT NULL
              AND v.county_name IS NOT NULL
            GROUP BY 1""").fetchall():
            d[f"cty_{county}_{tag}"] = float(pct)
    # The correction note under the Appendix E table quotes the two certified
    # registered-voter counts that exposed the transposition. Derived from the
    # pinned certified turnout frame rather than restated, so the note cannot
    # drift from the evidence it cites.
    import csv as _csv
    with (Path(__file__).resolve().parent.parent / "docs" / "reference"
          / "wa_registration_20251104_by_county.csv").open(encoding="utf-8") as _fh:
        for _row in _csv.DictReader(_fh):
            if _row["county"] in ("KITTITAS", "KLICKITAT"):
                d[f"cty_pin_{_row['county']}_reg"] = float(_row["registered_voters"])

    _counties = sorted({k.split("_")[1] for k in d if k.startswith("cty_")
                        and not k.startswith("cty_pin_")})
    for c_ in _counties:
        # The paper's last column: mean of the two HIGH-COVERAGE off-years
        # (2023, 2025) minus the presidential share. 2021 is excluded there and
        # used only for the "all three off-years" restatement above the table.
        d[f"cty_{c_}_gap2"] = (
            (d[f"cty_{c_}_e23"] + d[f"cty_{c_}_e25"]) / 2 - d[f"cty_{c_}_e24"])
        d[f"cty_{c_}_gap3"] = (
            (d[f"cty_{c_}_e21"] + d[f"cty_{c_}_e23"] + d[f"cty_{c_}_e25"]) / 3
            - d[f"cty_{c_}_e24"])
    d["cty_n"] = len(_counties)

    # --- Active vs full roll (added 2026-08-09) --------------------------
    #
    # The ladder's "Registered roll" row is the FULL roll; every official
    # turnout rate the paper quotes has the ACTIVE roll as its denominator. The
    # two populations differ by 7.6% of rows that are much younger, so the
    # published row runs about a point younger at each end than the population
    # the word "registered" denotes elsewhere — in the direction that widens the
    # contrast the table exists to show. Undisclosed until now, so derived now.
    for label, where in (("active", "status_code = 'A'"),
                         ("inactive", "status_code <> 'A'")):
        n, p65, u30, med = con.execute(f"""
            SELECT COUNT(*),
                   100.0 * SUM(CASE WHEN 2026 - EXTRACT(year FROM birthdate) >= 65
                                    THEN 1 ELSE 0 END) / COUNT(*),
                   100.0 * SUM(CASE WHEN 2026 - EXTRACT(year FROM birthdate) < 30
                                    THEN 1 ELSE 0 END) / COUNT(*),
                   MEDIAN(2026 - EXTRACT(year FROM birthdate))
            FROM voters WHERE birthdate IS NOT NULL AND {where}""").fetchone()
        d[f"roll_{label}_n"] = n
        d[f"roll_{label}_65+"] = float(p65)
        d[f"roll_{label}_18-29"] = float(u30)
        d[f"roll_{label}_median"] = float(med)
    d["roll_inactive_pct"] = (
        100.0 * d["roll_inactive_n"] / (d["roll_active_n"] + d["roll_inactive_n"]))
    # Certified 2025 ballots over the official 2025 turnout rate. If this did not
    # land on the ACTIVE roll the disclosure above would be wrong, so it is
    # asserted rather than asserted-about.
    d["roll_implied_official"] = OFFICIAL["2025-11-04"] / (d["off_turnout_2025"] / 100.0)
    # The roll size itself, not the with-a-birthdate subset the composition rows
    # use: "an active roll of N" is a headcount claim, and the two differ by one
    # registrant whose birthdate is null.
    d["roll_active_total"], = con.execute(
        "SELECT COUNT(*) FROM voters WHERE status_code = 'A'").fetchone()
    d["roll_active_implied_gap"] = abs(
        100.0 * (d["roll_implied_official"] - d["roll_active_total"])
        / d["roll_active_total"])
    d["cty_gap2_min"] = min(d[f"cty_{c_}_gap2"] for c_ in _counties)
    d["cty_gap3_min"] = min(d[f"cty_{c_}_gap3"] for c_ in _counties)
    d["cty_gap3_max"] = max(d[f"cty_{c_}_gap3"] for c_ in _counties)
    d["cty_gap2_max"] = max(d[f"cty_{c_}_gap2"] for c_ in _counties)
    # The county 65+ LEVEL range, on both bases. Printed as a single "30.7% to 66%"
    # pair until 2026-08-09, which mixed a 2025 cell with a 2023 cell and sat below
    # the body's own geography table (King 2021 = 28.7%).
    _off2 = [(d[f"cty_{c_}_e23"] + d[f"cty_{c_}_e25"]) / 2 for c_ in _counties]
    d["cty_off2_min"], d["cty_off2_max"] = min(_off2), max(_off2)
    _cells = [d[f"cty_{c_}_{tg}"] for c_ in _counties for tg in ("e21", "e23", "e25")]
    d["cty_cell_min"], d["cty_cell_max"] = min(_cells), max(_cells)

    # ACS benchmark rows, TRANSCRIBED from the paper's own table. The ACS
    # derivation is external (diag_wa_adult_age.py, tables B01001/B29001) and is
    # declared in UNCHECKED below, so asserting the table against this proves
    # nothing about the ACS itself. What it DOES prove is that the table and the
    # prose ladder restating it agree with each other — which is the defect this
    # audit exists to catch, and which nothing checked before. Stated plainly so
    # nobody later mistakes a consistency check for a verification.
    # --- Dissimilarity index -------------------------------------------
    # The paper's definition, verbatim: "how far each electorate's age
    # distribution sits from the citizen voting-age population, taken as half
    # the summed absolute differences across cohorts". Benchmark is the ACS
    # CVAP row transcribed below, so this inherits that row's external status.
    _cvap = {"18-29": 19.8, "30-44": 26.7, "45-64": 30.9, "65+": 22.6}
    for t in [tag for _, tag in ELECTIONS]:
        d[f"{t}_dissim"] = 0.5 * sum(abs(d[f"{t}_comp_{b}"] - _cvap[b]) for b in BANDS)
    _off_dis = [d[f"{t}_dissim"] for t in OFF_YEARS]
    d["off_dissim_min"], d["off_dissim_max"] = min(_off_dis), max(_off_dis)
    # Two readings of "how much more age-unrepresentative", both named in the
    # paper now: the lowest off-year against the presidential year, and the
    # three-off-year mean against it.
    d["off_dissim_ratio_min"] = min(_off_dis) / d["e24_dissim"]
    d["off_dissim_ratio_mean"] = (sum(_off_dis) / 3) / d["e24_dissim"]
    _off65 = [d[f"{t}_comp_65+"] for t in OFF_YEARS]
    d["off_65_spread"] = max(_off65) - min(_off65)
    d["off_65_band_lo"], d["off_65_band_hi"] = min(_off65), max(_off65)
    d["off_turnout_avg"] = sum(
        d[f"off_turnout_{y}"] for y in ("2021", "2023", "2025")) / 3.0
    # Senior-to-youth ratio. The paper used to say this "roughly triples"
    # off-cycle; it is 2.55x, and the paper's own "2:1 -> 5:1" is 2.5x. Derived
    # now so the multiplier is a checked figure rather than an adjective.
    d["s2y_pres"] = d["e24_comp_65+"] / d["e24_comp_18-29"]
    d["s2y_off"] = d["off_comp_65+"] / d["off_comp_18-29"]
    # Off-year averages of the within-cohort RATE table, and the eligible-roll 65+
    # band. All four were prose-only until 2026-08-09 — the coverage gate that
    # should have caught them was a no-op (see _verify_prose.audit_coverage).
    for b in BANDS:
        d[f"off_rate_{b}"] = sum(d[f"{tg}_rate_{b}"] for tg in OFF_YEARS) / 3.0
    _elig = [d[f"{tg}_elig65"] for _, tg in ELECTIONS]
    d["elig65_min"], d["elig65_max"] = min(_elig), max(_elig)
    d["s2y_widening"] = d["s2y_off"] / d["s2y_pres"]
    d["ratio_base"] = 1          # the ":1" the ratio notation is stated against
    for t in OFF_YEARS:
        d[f"{t}_s2y"] = d[f"{t}_comp_65+"] / d[f"{t}_comp_18-29"]
    # "roughly 2.5x": mean-based is 2.59, min-based 2.50. Asserted on the mean
    # with a tolerance that honours the word "roughly" — this is the loosest
    # figure in the paper's result sections and the only one where the basis
    # is genuinely ambiguous from the prose.
    d["off_dissim_ratio"] = (sum(_off_dis) / len(_off_dis)) / d["e24_dissim"]

    # --- Recorded gender ------------------------------------------------
    # Share of returners recorded F, over F+M. Not over all returners: 'U'/'O'
    # and NULL together are ~2.4% of the roll, and including them puts the
    # presidential figure at 51.25 against the paper's 52.5. F/(F+M) reproduces
    # it to 52.49, so that is the paper's basis.
    for date, tag in ELECTIONS:
        d[f"{tag}_female"], = con.execute(f"""
            SELECT COUNT(*) FILTER (WHERE v.gender = 'F') * 100.0
                   / NULLIF(COUNT(*) FILTER (WHERE v.gender IN ('F','M')), 0)
            FROM voters v {_voted(date)} WHERE h.state_voter_id IS NOT NULL""").fetchone()

    # --- Birth-year sensitivity ----------------------------------------
    # The paper's opposite-extreme check: treat every voter as if their birthday
    # had NOT yet happened (a Dec-31 assumption), i.e. one year younger than the
    # main convention, so the 65+ test becomes year-difference >= 66. Same
    # analyzable basis as the coverage table (returned, has YOB, no registration
    # filter) — which is why 2021 reads 36.75 here and 36.7 in the composition
    # table: different denominators, as the bounding note already documents.
    for date, tag in ELECTIONS:
        a = _age(date)
        main, dec31 = con.execute(f"""
            SELECT COUNT(*) FILTER (WHERE {a} >= 65) * 100.0 / COUNT(*),
                   COUNT(*) FILTER (WHERE {a} >= 66) * 100.0 / COUNT(*)
            FROM voters v {_voted(date)}
            WHERE h.state_voter_id IS NOT NULL AND v.birthdate IS NOT NULL""").fetchone()
        d[f"{tag}_by_main"], d[f"{tag}_by_dec31"] = main, dec31
    d["off_by_maxshift"] = max(d[f"{t}_by_main"] - d[f"{t}_by_dec31"] for t in OFF_YEARS)

    # Off-year min/max for the finer cohorts the prose quotes as a range.
    for band in ("75+", "18-24"):
        vals = [d[f"{t}_fine_{band}"] for t in OFF_YEARS]
        d[f"off_fine_{band}_min"], d[f"off_fine_{band}_max"] = min(vals), max(vals)
    # Same, for the recorded-female footnote's off-year range (ledger item C2).
    _off_f = [d[f"{t}_female"] for t in OFF_YEARS]
    d["off_female_min"], d["off_female_max"] = min(_off_f), max(_off_f)

    d.update({"acs_adult_18-29": 20.0, "acs_adult_30-44": 28.3,
              "acs_adult_45-64": 30.5, "acs_adult_65+": 21.1,
              "acs_cvap_18-29": 19.8, "acs_cvap_30-44": 26.7,
              "acs_cvap_45-64": 30.9, "acs_cvap_65+": 22.6})

    # The registered roll itself, as of the current extract — on BOTH bases. The
    # ladder's primary row is the ACTIVE roll since 2026-08-14 (referee item 5):
    # once the paper had itself measured that the full roll's inactive rows are much
    # younger and that the full-roll basis flatters the ladder's gradient by about a
    # point, series consistency stopped being a reason to keep the flattering basis
    # as the headline. The full-roll figures stay derived for the sensitivity note.
    a26 = _age("2026-04-01")
    for pfx, where in (("roll", "1=1"), ("aroll", "v.status_code = 'A'")):
        rows = con.execute(f"""
            WITH e AS (SELECT {_band('2026-04-01')} b FROM voters v
                       WHERE v.birthdate IS NOT NULL AND {a26} >= 18 AND {where})
            SELECT b, COUNT(*) FROM e GROUP BY 1""").fetchall()
        rd = dict(rows)
        rt = sum(rd.values()) or 1
        for b in BANDS:
            d[f"{pfx}_{b}"] = 100.0 * rd.get(b, 0) / rt
        d[f"{pfx}_median"], = con.execute(
            f"SELECT median({a26}) FROM voters v "
            f"WHERE v.birthdate IS NOT NULL AND {a26} >= 18 AND {where}").fetchone()

    # Survivorship: voters who cast a ballot and are no longer on the roll, aged via the
    # retained September-2023 snapshot (the only way to age someone the current roll lost).
    for date, tag in (("2021-11-02", "e21"), ("2022-11-08", "e22"), ("2023-11-07", "e23")):
        n, p65, p18 = con.execute(f"""
            WITH gone AS (
                SELECT s.state_voter_id, date_diff('year', s.birthdate, DATE '{date}') a
                FROM voters_20230901 s
                JOIN (SELECT DISTINCT state_voter_id FROM voting_history
                      WHERE election_date = DATE '{date}') h USING (state_voter_id)
                LEFT JOIN voters v USING (state_voter_id)
                WHERE v.state_voter_id IS NULL AND s.birthdate IS NOT NULL)
            SELECT COUNT(*), 100.0*COUNT(*) FILTER (WHERE a>=65)/COUNT(*),
                   100.0*COUNT(*) FILTER (WHERE a<30)/COUNT(*) FROM gone""").fetchone()
        d[f"{tag}_gone_n"], d[f"{tag}_gone_65"], d[f"{tag}_gone_18"] = \
            int(n), float(p65), float(p18)
        d[f"{tag}_gone_k"] = int(n) / 1000.0

    # Snapshot cross-validation: the same 65+ share computed on the Sept-2023 roll.
    for date, tag in (("2021-11-02", "e21"), ("2022-11-08", "e22"), ("2023-11-07", "e23")):
        snap, = con.execute(f"""
            WITH e AS (SELECT date_diff('year', s.birthdate, DATE '{date}') a
                       FROM voters_20230901 s
                       JOIN (SELECT DISTINCT state_voter_id FROM voting_history
                             WHERE election_date = DATE '{date}') h USING (state_voter_id)
                       WHERE s.birthdate IS NOT NULL
                         AND date_diff('year', s.birthdate, DATE '{date}') >= 18)
            SELECT 100.0*COUNT(*) FILTER (WHERE a>=65)/COUNT(*) FROM e""").fetchone()
        d[f"{tag}_snap65"] = float(snap)
        d[f"{tag}_snap_delta"] = float(snap) - d[f"{tag}_obs65"]

    # The largest gap between the current-roll and snapshot reconstructions, which the paper
    # states as a bound ("agree to within ~1.4 points"). Computed HERE and not earlier: the
    # per-cycle deltas it maxes over are produced by the loop immediately above, and putting
    # this before them raised a KeyError on the first run.
    d["recon_max_gap"] = max(abs(d[f"{tg}_snap_delta"]) for tg in ("e21", "e22", "e23"))

    # --- King's share of each electorate (2026-08-11, external referee) ---
    # The obvious alternative reading of the statewide senior tilt is compositional: the
    # older, more rural counties simply turn out more off-cycle. That is checkable and it
    # is false in the direction that matters — King, the YOUNGEST county in the state at
    # 23.0% 65+ presidential, is a LARGER share of every off-year electorate than of the
    # 2024 one. The tilt happens despite the composition moving the other way, so the
    # within-county effect carries all of it and the statewide figures understate it.
    _king: dict[str, float] = {}
    for date, tag in (("2024-11-05", "e24"), ("2021-11-02", "e21"),
                      ("2023-11-07", "e23"), ("2025-11-04", "e25")):
        _king[tag], = con.execute(f"""
            SELECT 100.0 * SUM(CASE WHEN UPPER(v.county_name) = 'KING' THEN 1 ELSE 0 END)
                   / COUNT(*)
            FROM (SELECT DISTINCT state_voter_id FROM voting_history
                  WHERE election_date = DATE '{date}') h
            JOIN voters v USING (state_voter_id)""").fetchone()
    # The composition gap the rejection channel is weighed against in Appendix A.
    d["comp_gap_18_29"] = d["e24_comp_18-29"] - d["off_comp_18-29"]
    # Same rule: the presidential share and the off-year SPAN are published; the three
    # per-year off-year shares are intermediates and stay local.
    d["e24_king_share"] = _king["e24"]
    d["off_king_share_lo"] = min(_king[t] for t in OFF_YEARS)
    d["off_king_share_hi"] = max(_king[t] for t in OFF_YEARS)

    # --- Validation section (2026-08-11) ---------------------------------
    # The 2021 "observed" cell appears on TWO bases eleven lines apart, and the paper
    # explains the difference at the point of use rather than hiding it: the validation
    # table's 36.8% is the coverage basis, the composition table's 36.7% adds a
    # "registered on or before the election" filter, and the two straddle a rounding
    # boundary. DO NOT "FIX" THIS — the printed tenth of a point is real and documented.
    # The gap itself is what the sub-note quotes, so it is derived rather than described.
    d["e21_basis_gap"] = d["e21_obs65"] - d["e21_comp_65+"]
    # The blend check: the snapshot column is not independent evidence, because blending
    # the current-roll electorate with the tabulated drop-offs reproduces it. The paper
    # states that as a bound ("to within 0.2 points"), so the derivation is the MAXIMUM
    # over the three cycles, not any one of them.
    d["snap_blend_max"] = max(
        abs(((d[f"{t}_analyzable"] * d[f"{t}_obs65"]
              + d[f"{t}_gone_n"] * d[f"{t}_gone_65"])
             / (d[f"{t}_analyzable"] + d[f"{t}_gone_n"])) - d[f"{t}_snap65"])
        for t in ("e21", "e22", "e23"))

    # --- Appendix B: the July-1 sentinel (2026-08-11) --------------------
    # Appendix B's privacy argument rests on "in our file every birth value resolves to a
    # July-1 sentinel ... confirming that no full date of birth is stored or used here."
    # That is a checkable claim about the loaded data and nothing was checking it: the
    # only token in the sentence is the "1" of "July-1", which the small-integer rule
    # waives, and "every" is a word no probe can capture. Counted, not assumed.
    d["b_birthdates"], d["b_july1"] = con.execute("""
        SELECT COUNT(*), SUM(CASE WHEN month(birthdate) = 7 AND day(birthdate) = 1
                                  THEN 1 ELSE 0 END)
        FROM voters WHERE birthdate IS NOT NULL""").fetchone()

    # --- Appendix A restatements (2026-08-11) ----------------------------
    # The objections appendix re-quotes the body's figures in its own words, which is the
    # position an unnoticed contradiction occupies: correct table, correct appendix, and a
    # sentence between them that reports neither.
    #
    # The median-age SPAN across off-years is not `off_median`, which is their mean. Two
    # quantities, and the appendix uses the span.
    d["off_median_lo"] = min(d[f"{t}_median"] for t in OFF_YEARS)
    d["off_median_hi"] = max(d[f"{t}_median"] for t in OFF_YEARS)
    # "over 1.7 times the 22.6% of citizen voting-age Washingtonians" — a RATIO of two
    # figures each asserted separately, so nothing checked the ratio itself.
    d["a_ratio_65_cvap"] = d["off_comp_65+"] / d["acs_cvap_65+"]
    # Cited literature, transcribed and asserted at tolerance 0.
    d["lit_wattenberg_lo"], d["lit_wattenberg_hi"] = 2, 10
    con.close()
    # Appendix F last, and on its own connection: it is the only block needing the
    # statewide returns DB, and it reads `off_turnout_*` from `d` for the scenario grid,
    # so it has to run after those are set.
    derive_appendix_f(d)
    return d


def build_probes(derived: dict):
    p = []
    labels = {"e21": "Nov 2021", "e22": "Nov 2022", "e23": "Nov 2023",
              "e24": "Nov 2024", "e25": "Nov 2025"}
    kinds = {"e21": "Off-year", "e22": "Midterm", "e23": "Off-year",
             "e24": "Presidential", "e25": "Off-year"}

    # Coverage against the certified count, asserted exactly.
    #
    # This block briefly carried a tolerance of 1 with a comment explaining that two of the
    # paper's own tables disagreed by a single record. That explanation was wrong: the paper
    # was consistent and THIS SCRIPT was applying an age filter the paper's definition does
    # not. Widening the tolerance had made the symptom go away and preserved the defect,
    # which is the exact move CLAUDE.md forbids. The derivation is fixed and the tolerance is
    # back to the printed precision.
    for tag in ("e21", "e22", "e23", "e24", "e25"):
        p.append((f"coverage {labels[tag]}",
                  rf"\| {labels[tag]} \| {kinds[tag]} \| ([\d,]+) \| ([\d,]+) \(([\d.]+)%\) \| "
                  rf"([\d,]+) \| \*\*([\d.]+)%\*\* \|",
                  (f"{tag}_official", f"{tag}_infile", f"{tag}_infile_pct",
                   f"{tag}_analyzable", f"{tag}_cov_pct"), 0.05))
    # Survivorship hole.
    # The cohort size is CAPTURED, not baked into the anchor. It used to be a literal in
    # the pattern, which catches the paper being reworded but never compares the number to
    # anything — and 2023 was printed as "n≈45K" against a measured 44,455 (44K) while the
    # other two rows rounded exactly. Ledger C6.
    for tag in ("e21", "e22", "e23"):
        p.append((f"survivorship {labels[tag]}",
                  rf"\| Cast a ballot {labels[tag]} \(n≈([\d.]+)K\) \| \*\*([\d.]+)%\*\* \| "
                  rf"([\d.]+)% \|",
                  (f"{tag}_gone_k", f"{tag}_gone_65", f"{tag}_gone_18"), 0.5))
    # Bounding.
    for tag in ("e21", "e23", "e25"):
        p.append((f"bounding {labels[tag]}",
                  rf"\| {labels[tag]} \(residual ([\d.]+)%\) \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \| "
                  rf"([\d.]+)% \|",
                  (f"{tag}_residual_pct", f"{tag}_min65", f"{tag}_obs65", f"{tag}_max65"), 0.05))
    # Snapshot cross-validation.
    for tag in ("e21", "e22", "e23"):
        kind = "off-year" if tag != "e22" else "midterm"
        p.append((f"snapshot cross-validation {labels[tag]}",
                  rf"\| {labels[tag]} \({kind}\) \| ([\d.]+)% \| ([\d.]+)% \| \+([\d.]+) \|",
                  (f"{tag}_obs65", f"{tag}_snap65", f"{tag}_snap_delta"), 0.05))
    # Composition of the electorate.
    for tag in ("e24", "e22", "e21", "e23", "e25"):
        p.append((f"composition {labels[tag]}",
                  rf"\| {labels[tag]} \| {kinds[tag]} \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| "
                  rf"([\d.]+)% \|(?!\s*[\d.]+%)",
                  tuple(f"{tag}_comp_{b}" for b in BANDS), 0.05, "composition"))
    # Turnout rate, which carries a fifth "All" column and so cannot collide with the above.
    for tag in ("e24", "e22", "e21", "e23", "e25"):
        p.append((f"turnout rate {labels[tag]}",
                  rf"\| {labels[tag]} \| {kinds[tag]} \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| "
                  rf"([\d.]+)% \| ([\d.]+)% \|",
                  tuple(f"{tag}_rate_{b}" for b in BANDS) + (f"{tag}_rate_all",),
                  0.05, "rates"))
    # Finer cohorts, six columns.
    for tag in ("e24", "e22", "e21", "e23", "e25"):
        p.append((f"finer cohorts {labels[tag]}",
                  rf"\| {labels[tag]} \| {kinds[tag]} \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| "
                  rf"([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \|",
                  tuple(f"{tag}_fine_{b}" for b in
                        ("18-24", "25-29", "30-44", "45-64", "65-74", "75+")), 0.05, "finer"))
    # ---- ABSTRACT restatements. The abstract is what a reviewer reads first and every figure
    # in it restates a table cell below. The harness checks every occurrence of a figure, but
    # only where a probe points at it — these sentences had no probe, so the abstract could
    # have drifted from its own tables without anything failing.
    p += [
        # RE-POINTED 2026-08-09. The old anchor captured only the roll and the
        # raw record count, so the qualifier "with the voter's year of birth" sat
        # OUTSIDE every capture group and could not be checked — and it was
        # false: 3.05% of vote-history rows resolve to no roll row and therefore
        # to no age. The qualifier is now a figure, so it can fail.
        ("abstract — source scale",
         r"a ([\d.]+)-million-voter roll\s+carrying each voter's year of birth, linked to "
         r"([\d.]+) million individual vote-history\s+records, of which ([\d.]+) million "
         r"resolve to a roll row", ("roll_m", "history_m", "history_aged_m"), 0.05),
        ("abstract — 65+ share, three off-years against 2024",
         r"Voters 65 and older were ([\d.]+)%, ([\d.]+)%, and\s+([\d.]+)% of the 2021, 2023, "
         r"and 2025 odd-year electorates, against ([\d.]+)% in 2024",
         ("e21_comp_65+", "e23_comp_65+", "e25_comp_65+", "e24_comp_65+"), 0.05),
        ("abstract — 18-29 fall",
         r"voters\s+18–29 fell from ([\d.]+)% in 2024 to about ([\d.]+)% off-cycle",
         ("e24_comp_18-29", "off_comp_18-29"), 0.05),
        # RE-POINTED 2026-08-11: the abstract now states the SURVIVORSHIP-CORRECTED
        # range, so it reads against `core_corr_*` and not the raw overlap.
        ("abstract — habitual core span, corrected",
         r"habitual core\* \(at most (\d+)–(\d+)% of\s+off-year voters also cast a 2024 "
         r"presidential ballot", ("core_corr_lo", "core_corr_hi"), 0.5),

        # ---- Methods and validation prose, none of it previously probed.
        ("methods — vote-history record count restated",
         r"`voting_history` \(([\d.]+)M records across (\d+) election dates, of which "
         r"([\d.]+)M — ([\d.]+)% — resolve",
         ("history_m", "history_dates", "history_aged_m", "history_aged_pct"), 0.05),
        ("methods — 2021 certified example",
         r"November 2021: ([\d,]+) ballots counted, ([\d.]+)% turnout",
         ("e21_official", "e21_official_turnout"), 0.05),
        ("methods — analyzable coverage span",
         r"Analyzable coverage runs from \*\*([\d.]+)% in 2021 to ([\d.]+)% in 2025\*\*",
         ("cov_lo", "cov_hi"), 0.05),
        ("methods — retained snapshot size",
         r"`voters_20230901`, ([\d.]+)M rows", "snapshot_m", 0.005),
        ("survivorship — roll attrition is age-loaded",
         r"of the (\d+)K voters \(([\d.]+)%\) who left the roll\s+between 2023 and 2026, "
         r"([\d.]+)% were 65\+, versus ([\d.]+)% of those who stayed",
         ("left_k", "left_pct", "left_65", "stay_65"), 0.5),
        ("cross-check — the two reconstructions agree within",
         r"agree to within ~([\d.]+) points", "recon_max_gap", 0.05),
        ("bounds — the three off-year minima restated in prose",
         r"each off-year electorate \(\*\*([\d.]+)% / ([\d.]+)% / ([\d.]+)%\*\* 65\+\)",
         ("e21_min65", "e23_min65", "e25_min65"), 0.05),
    ]

    # Who is counted.
    p += [
        # The ladder's roll row is the ACTIVE roll since 2026-08-14 (referee item 5);
        # the full-roll figures move to the sensitivity note beneath the table and
        # stay asserted there, so neither basis can drift.
        ("who is counted — active registered roll",
         r"\| Active registered roll \(April 2026\) \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| "
         r"([\d.]+)% \| (\d+) \|",
         tuple(f"aroll_{b}" for b in BANDS) + ("aroll_median",), 0.05),
        ("who is counted — the full-roll sensitivity figures in the note",
         r"full roll including inactive registrants reads ([\d.]+)% / ([\d.]+)% / "
         r"([\d.]+)% / ([\d.]+)% with median (\d+)",
         tuple(f"roll_{b}" for b in BANDS) + ("roll_median",), 0.05),
        ("who is counted — 2024 returners",
         r"\| 2024 presidential ballot-returners \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| "
         r"([\d.]+)% \| (\d+) \|",
         tuple(f"e24_comp_{b}" for b in BANDS) + ("e24_median",), 0.05),
        ("who is counted — off-year returners, three-cycle average",
         r"\| Off-year ballot-returners \(2021/23/25 avg\) \| ([\d.]+)% \| ([\d.]+)% \| "
         r"([\d.]+)% \| ([\d.]+)% \| (\d+) \|",
         tuple(f"off_comp_{b}" for b in BANDS) + ("off_median",), 0.5),
    ]
    # Geography.
    for label, key in (("King County", "king"), ("Rest of state", "rest"),
                       ("Metro counties¹", "metro"), ("Rural counties", "rural")):
        p.append((f"geography — {label}",
                  rf"\| {label} \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \|",
                  tuple(f"{t}_geo_{key}" for t in ("e24", "e21", "e23", "e25")), 0.05))

    # ---------------------------------------------------------------
    # PROSE RESTATEMENTS (added 2026-08-06 by the coverage audit).
    #
    # Each of these repeats a table value in a sentence. Every one was
    # unprobed until the audit gated: the tables were checked, the prose
    # describing them was not. That is precisely the gap an external
    # reviewer found in the donor paper — a correct table under a
    # sentence that misreports it — and it is the reason a figure stated
    # twice must agree with the data BOTH times.
    # ---------------------------------------------------------------
    p += [
        ("prose — headline off-year 65+ trio",
         r"Voters 65\+ make up \*\*~37–40%\*\* of it \(([\d.]+) / ([\d.]+) / ([\d.]+)% across",
         ("e21_comp_65+", "e23_comp_65+", "e25_comp_65+"), 0.05),
        ("prose — presidential 65+ share",
         r"across 2021 / 2023 / 2025\) versus \*\*([\d.]+)%\*\* in the presidential",
         "e24_comp_65+", 0.05),
        ("prose — 18-29 share, presidential to off-year",
         r"the 18–29 share falls from \*\*([\d.]+)%\*\* to \*\*~([\d.]+)%\*\*",
         ("e24_comp_18-29", "off_comp_18-29"), 0.05),
        # ADDED 2026-08-09. The bullet used to say the ratio "roughly triples"
        # off-cycle while quoting 2:1 and 5:1 in the same sentence, which is 2.5x
        # — an adjective contradicting its own two figures, with no token a probe
        # could catch. The multiplier is now a figure and is asserted.
        ("prose — senior-to-youth ratio and its widening",
         r"from\s*about \*\*2:1\*\* in the presidential year \(([\d.]+)/([\d.]+) = ([\d.]+)\) "
         r"to about \*\*5:1\*\* off-year\s*\(([\d.]+)/([\d.]+) = ([\d.]+), a ([\d.]+)× widening; "
         r"the individual off-years run ([\d.]+) / ([\d.]+) / ([\d.]+)\)",
         ("e24_comp_65+", "e24_comp_18-29", "s2y_pres",
          "off_comp_65+", "off_comp_18-29", "s2y_off", "s2y_widening",
          "e21_s2y", "e23_s2y", "e25_s2y"), 0.05),
        ("prose — midterm 65+ share",
         r"with\s*the midterm in between \(([\d.]+)% 65\+\)", "e22_comp_65+", 0.05),
        ("prose — 65+ ladder across the five benchmark rows",
         r"The 65\+ share climbs \*\*([\d.]+)% → ([\d.]+)% → ([\d.]+)% → ([\d.]+)% → ([\d.]+)%\*\*",
         ("acs_adult_65+", "acs_cvap_65+", "aroll_65+", "e24_comp_65+", "off_comp_65+"), 0.05),
        ("prose — 18-29 ladder across the five benchmark rows",
         r"the 18–29 share falls \*\*([\d.]+)% → ([\d.]+)% → ([\d.]+)% → ([\d.]+)% → ([\d.]+)%\*\*",
         ("acs_adult_18-29", "acs_cvap_18-29", "aroll_18-29", "e24_comp_18-29",
          "off_comp_18-29"), 0.05),
        ("who is counted — ACS adult residents (consistency, not verification)",
         r"\| WA adult residents \(ACS 2020–24\) \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| "
         r"([\d.]+)% \|",
         tuple(f"acs_adult_{b}" for b in BANDS), 0.0),
        ("who is counted — ACS citizen voting-age population (consistency)",
         r"\| WA citizen voting-age population \(ACS 2020–24\) \| ([\d.]+)% \| ([\d.]+)% \| "
         r"([\d.]+)% \| ([\d.]+)% \|",
         tuple(f"acs_cvap_{b}" for b in BANDS), 0.0),
        ("prose — roll senior share and the eligible-roll band",
         r"low and steady \(([\d.]+)% on the full April 2026 roll; ~([\d.]+)–([\d.]+)% on "
         r"the per-election eli", ("roll_65+", "elig65_min", "elig65_max"), 0.5),
        # F4, 2026-08-09 (round 4). These four were DERIVED and consumed by no
        # probe. `e24_max65` is the hinge of the whole bounding argument — it is
        # what makes "33.4% beats the presidential maximum" a bound rather than an
        # assertion — and it was computed and thrown away. An adversarial pass
        # instrumented build_probes() and found 180 such keys; these are the ones
        # a published sentence rests on.
        ("prose — the presidential upper bound, the hinge of the bound",
         r"under \*its\* most favorable assumption \(\*\*≤([\d.]+)%\*\*", "e24_max65", 0.05),
        ("prose — the two-off-year gap range",
         r"county moves toward seniors off-cycle \(gaps \+([\d.]+) to \+([\d.]+) points\)",
         ("cty_gap2_min", "cty_gap2_max"), 0.05),
        ("appendix E — the county 65+ range, both bases",
         r"averages\s*\*\*([\d.]+)% \(King\)\*\* to \*\*([\d.]+)% \(Jefferson\)\*\*; taking all "
         r"three off-years cell by cell the\s*span widens to \*\*([\d.]+)%\*\* \(King 2021\) to "
         r"\*\*([\d.]+)%\*\* \(Jefferson 2023\)",
         ("cty_off2_min", "cty_off2_max", "cty_cell_min", "cty_cell_max"), 0.05),
        ("prose — the three-off-year gap range",
         r"\(King \+([\d.]+) to Franklin \+([\d.]+)\)",
         ("cty_gap3_min", "cty_gap3_max"), 0.05),
        ("prose — county count, both statements",
         r"positive in \*\*all (\d+) counties\*\*", "cty_n", 0.0),
        # --- The four external-referee corrections, 2026-08-11 -------------
        ("interpretation — the survivorship correction to the habitual core",
         r"snapshot can still see moves 2021 from ([\d.]+)% to \*\*([\d.]+)%\*\* and 2023 "
         r"from ([\d.]+)% to \*\*([\d.]+)%\*\*, while 2025, four months from the roll, moves\s*"
         r"\*\*([\d.]+)\*\* points",
         ("e21_core", "e21_core_corr", "e23_core", "e23_core_corr", "core_infl_2025"), 0.05),
        ("interpretation — the corrected range, restated",
         r"the defensible range is \*\*at most (\d+)–(\d+)%\*\*",
         ("core_corr_lo", "core_corr_hi"), 0.5),
        ("interpretation — the decomposition's unrounded basis, stated",
         r"2025's ([\d.]+)% is ([\d.]+)/([\d.]+), not ([\d.]+)/([\d.]+)\.",
         ("e25_decomp65_of_rise", "e25_decomp65_rate", "e25_decomp65_rise",
          "e25_decomp65_rate", "e25_decomp65_rise"), 0.05),
        ("prose — King's share of each electorate, presidential against off-year",
         r"is \*\*([\d.]+)%\*\* of the 2024 presidential electorate and a \*larger\*\s*share "
         r"of every off-year one, at \*\*([\d.]+)–([\d.]+)%\*\*",
         ("e24_king_share", "off_king_share_lo", "off_king_share_hi"), 0.05),
        ("appendix F — how often each office defines the floor",
         r"mayor defines the floor in \*\*([\d.]+)%\*\* of\s*its precincts and city council in "
         r"\*\*([\d.]+)%\*\*, against \*\*([\d.]+)%\*\* for school director,\s*"
         r"\*\*([\d.]+)%\*\* for port commissioner and \*\*([\d.]+)%\*\* for fire district",
         ("f_floorshare_mayor", "f_floorshare_council", "f_floorshare_school",
          "f_floorshare_port", "f_floorshare_fire"), 0.05),
        ("appendix A — the rejection channel, measured",
         r"\*\*([\d.]+)%\*\* of ballots from under-30 voters against \*\*([\d.]+)%\*\* from "
         r"65\+, a ratio of\s*\*\*([\d.]+)\*\*\. But the effect on this paper's measure is "
         r"\*\*([\d.]+) points\*\* on the 18–29 share of the\s*electorate, against a "
         r"composition gap of about ([\d.]+) points",
         ("a_rej_young", "a_rej_senior", "a_rej_ratio", "a_rej_comp_shift",
          "comp_gap_18_29"), 0.05),
        # SURFACED BY `bold_is_result`, 2026-08-11. All four are results the author
        # bolded and no probe touched: the ratio restated in `n:1` notation, whose
        # decimal form beside it WAS asserted, and the two medians.
        # The `:1` denominators are captured too, not waived. They are part of the
        # notation, and a paper that drifted to "5:2" would otherwise pass — the ratio
        # is only meaningful against a base of one.
        ("prose — the senior-to-youth ratio in n:1 notation, both years",
         r"from about \*\*(\d+):(\d+)\*\* in the presidential year \([\d.]+/[\d.]+ = [\d.]+\) "
         r"to about \*\*(\d+):(\d+)\*\* off-year",
         ("s2y_pres", "ratio_base", "s2y_off", "ratio_base"), 0.5),
        ("prose — the median ladder, off-year against roll and CVAP",
         r"The median off-year\s*ballot-returner is \*\*(\d+)\*\*, about a decade older than "
         r"the median registered voter \((\d+)\)",
         ("off_median", "aroll_median"), 0.5),
        ("appendix H — the age the tail decline begins",
         r"declines from \*\*(\d+)\*\* onward", "h_decline_start", 0.0),
        ("prose — off-year returner senior share",
         r"the off-year returner share reaches ~([\d.]+)%", "off_comp_65+", 1.0),
        ("prose — headline off-year band, both endpoints",
         r"Voters 65\+ make up \*\*~([\d.]+)–([\d.]+)%\*\*",
         ("off_65_band_lo", "off_65_band_hi"), 0.5),
        ("prose — the headline ~38% restated in the basis note",
         r"and the headline ~([\d.]+)% — has the active roll as\s+its denominator",
         "off_turnout_avg", 0.5),
        ("prose — participation rate gap, 18-29 vs 65\\+",
         r"participation falls from \*\*([\d.]+)%\*\* \(2024\) to about \*\*([\d.]+)%\*\* "
         r"off-year, while 65\+ slips only from \*\*([\d.]+)%\*\* to \*\*~([\d.]+)%\*\*",
         ("e24_rate_18-29", "off_rate_18-29", "e24_rate_65+", "off_rate_65+"), 0.5),
        ("prose — official general-election turnout, five cycles",
         r"official general-election turnout in every year \(([\d.]+)% 2021, ([\d.]+)% 2022, "
         r"([\d.]+)% 2023, ([\d.]+)% 2024, ([\d.]+)% 2025\)",
         ("off_turnout_2021", "off_turnout_2022", "off_turnout_2023",
          "off_turnout_2024", "off_turnout_2025"), 0.0),
        # REBUILT 2026-08-09 (round 3). The as-built roll delta compares a
        # FULL-roll reconstruction against an official figure that counts only
        # ACTIVE registrants, and the sign flip at 2023 that the previous prose
        # explained causally is an artifact of that mismatch. Both bases are now
        # in the table and both are asserted, so it cannot revert to showing one.
        ("prose — reconstruction vs official, both bases, five cycles",
         r"\| 2021 \| −([\d.]+)% \| \*\*−([\d.]+)%\*\* \| −([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \|\s*"
         r"\| 2022 \| −([\d.]+)% \| \*\*−([\d.]+)%\*\* \| −([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \|\s*"
         r"\| 2023 \| \+([\d.]+)% \| \*\*−([\d.]+)%\*\* \| −([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \|\s*"
         r"\| 2024 \| \+([\d.]+)% \| \*\*−([\d.]+)%\*\* \| −([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \|\s*"
         r"\| 2025 \| \+([\d.]+)% \| \*\*−([\d.]+)%\*\* \| −([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \|",
         ("e21_recon_roll_delta_abs", "e21_recon_roll_active_delta_abs",
          "e21_recon_ballot_delta_abs", "e21_recon_rate", "off_turnout_2021",
          "e22_recon_roll_delta_abs", "e22_recon_roll_active_delta_abs",
          "e22_recon_ballot_delta_abs", "e22_recon_rate", "off_turnout_2022",
          "e23_recon_roll_delta", "e23_recon_roll_active_delta_abs",
          "e23_recon_ballot_delta_abs", "e23_recon_rate", "off_turnout_2023",
          "e24_recon_roll_delta", "e24_recon_roll_active_delta_abs",
          "e24_recon_ballot_delta_abs", "e24_recon_rate", "off_turnout_2024",
          "e25_recon_roll_delta", "e25_recon_roll_active_delta_abs",
          "e25_recon_ballot_delta_abs", "e25_recon_rate", "off_turnout_2025"), 0.05),
        ("prose — inactive registrants carried by the reconstruction",
         r"carries ([\d]+)K–([\d]+)K inactive registrants",
         ("e21_recon_inactive_k", "e25_recon_inactive_k"), 0.5),
        ("prose — inactive inclusion inflates the denominator",
         r"inflates the denominator\s*by ([\d.]+) to ([\d.]+) points",
         ("recon_inactive_infl_min", "recon_inactive_infl_max"), 0.05),
        ("prose — matched-basis reconstructed rates run above official",
         r"run \*above\* official in every year \(([\d.]+) / ([\d.]+) / ([\d.]+) / ([\d.]+) / "
         r"([\d.]+)%\)",
         ("e21_recon_rate_active", "e22_recon_rate_active", "e23_recon_rate_active",
          "e24_recon_rate_active", "e25_recon_rate_active"), 0.05),
        ("prose — 2021 cancellation sits in the weakest-coverage year",
         r"in the year with the weakest coverage \(([\d.]+)%\)",
         "e21_cov_pct", 0.05),
        ("prose — 2021 official rate restated in the cancellation note",
         r"near-exact agreement with the official ([\d.]+)%", "off_turnout_2021", 0.0),
        # ADDED 2026-08-09 — previously in UNCHECKED, which is how two of the
        # three off-years were published under the wrong definition.
        ("prose — decomposition, all three off-years",
         r"\| 2025 \| \+([\d.]+) \| \+([\d.]+) \| \*\*\+([\d.]+)\*\* \| ([\d.]+)% \| ([\d.]+)% \|\s*"
         r"\| 2023 \| \+([\d.]+) \| \+([\d.]+) \| \*\*−([\d.]+)\*\* \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \|\s*"
         r"\| 2021 \| \+([\d.]+) \| \+([\d.]+) \| \*\*−([\d.]+)\*\* \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \|",
         ("e25_decomp65_rise", "e25_decomp65_rate", "e25_decomp65_roll",
          "e25_decomp65_of_rise", "e25_decomp65_of_move",
          "e23_decomp65_rise", "e23_decomp65_rate", "e23_decomp65_roll_abs",
          "e23_decomp65_of_rise", "e23_decomp65_of_move",
          "e21_decomp65_rise", "e21_decomp65_rate", "e21_decomp65_roll_abs",
          "e21_decomp65_of_rise", "e21_decomp65_of_move"), 0.05),
        ("prose — 2025 decomposition headline",
         r"\*\*\+([\d.]+)-point\*\* rise in the 65\+ share from 2024 to 2025, \*\*\+([\d.]+) "
         r"points \(([\d.]+)%\) come from\s*turnout rates\*\* and only \*\*\+([\d.]+) from a "
         r"changing roll\*\*; for 18–29 the split is \*\*−([\d.]+) of\s*−([\d.]+) points "
         r"\(([\d.]+)%\) behavioral",
         ("e25_decomp65_rise", "e25_decomp65_rate", "e25_decomp65_of_move",
          "e25_decomp65_roll", "e25_decomp18_rate_abs", "e25_decomp18_rise_abs",
          "e25_decomp18_of_move"), 0.05),
        ("prose — the 2021 roll effect is not negligible",
         r"the 2021 roll effect \(−([\d.]+) points against an \+([\d.]+)-point rise\)",
         ("e21_decomp65_roll_abs", "e21_decomp65_rise"), 0.05),
        # Finer cohorts: the sentence quotes a RANGE across the three off-years,
        # so each endpoint is asserted against the off-year min and max rather
        # than an average — a range that quietly widened would otherwise pass.
        # CORRECTED 2026-08-06 (ledger item C1, author answered "fix — include
        # 2021"). The sentence used to quote 16.8–18.3, which is 2023 and 2025
        # only; the paper's own finer table gives a THIRD off-year, 2021 = 13.4%,
        # and the derivation reproduces all three exactly (13.42 / 16.84 /
        # 18.26). The range is now asserted against the off-year MIN and MAX, and
        # the two named endpoints in the same clause against 2023 and 2025, so a
        # range that quietly dropped a member would fail rather than pass.
        ("prose — 75+ share, presidential and the full off-year range",
         r"the 75\+ share rises from \*\*([\d.]+)%\*\* in the presidential year to "
         r"\*\*([\d.]+)–([\d.]+)%\*\*",
         ("e24_fine_75+", "off_fine_75+_min", "off_fine_75+_max"), 0.05),
        ("prose — 75+ share, the two named off-year endpoints",
         r"2021 is the low, with 2023 and 2025 at ([\d.]+)% and ([\d.]+)%",
         ("e23_fine_75+", "e25_fine_75+"), 0.05),
        ("prose — 18-24 share, presidential and off-year range",
         r"the 18–24 share falls from \*\*([\d.]+)%\*\* to \*\*~([\d.]+)–([\d.]+)%\*\*",
         ("e24_fine_18-24", "off_fine_18-24_min", "off_fine_18-24_max"), 0.05),
        ("prose — dissimilarity index, presidential and midterm",
         r"It comes out \*\*([\d.]+)\*\* for the 2024 presidential electorate, "
         r"\*\*([\d.]+)\*\* at the midterm, and \*\*([\d.]+)–([\d.]+)\*\* across the three",
         ("e24_dissim", "e22_dissim", "off_dissim_min", "off_dissim_max"), 0.05),
        # BOTH readings now printed and both asserted (2026-08-09, round 3). The
        # sentence used to give only 2.5, which is the min-based construction,
        # while its subject ("the off-year electorate") is the three-cycle mean
        # everywhere else in the paper — the 2.6 reading. Naming both closes the
        # round-exemption below rather than tolerating it.
        ("prose — off-year electorate is ~2.5x as age-unrepresentative",
         r"roughly \*\*([\d.]+)× as age-unrepresentative", "off_dissim_ratio_min", 0.05),
        # APPENDIX H, ASSERTED 2026-08-09 (round 3). These were DERIVED and then
        # referenced by no probe, while three places in the paper and this file's
        # own UNCHECKED entry said they were asserted. A derivation nothing reads
        # is not coverage; it is the same false-coverage defect the UNCHECKED
        # comment below was written to warn about, introduced by the edit that
        # added the warning.
        ("appendix H — the peak and the 65-boundary step",
         r"peak of ([\d.]+)% at age 79.*?retention moves from ([\d.]+)%\s*at 64 to "
         r"([\d.]+)% at 66, a two-year step of ([\d.]+) points, against a ([\d.]+)-point step",
         ("h_peak_ret", "h_ret_64", "h_ret_66", "h_step_64_66", "h_step_60_64"), 0.05),
        ("appendix H — the tail decline",
         r"peaks at \*\*([\d.]+)% at age 79\*\* and declines from \*\*80\*\*\s*onward "
         r"\(([\d.]+)% at 80, ([\d.]+)% at 84, ([\d.]+)% at 90, ([\d.]+)% at 95\)",
         ("h_peak_ret", "h_ret_80", "h_ret_84", "h_ret_90", "h_ret_95"), 0.05),
        ("appendix H — banding robustness on the composition measure",
         r"gives 65–69 \*\*([\d.]+)\*\*, 70–74 \*\*([\d.]+)\*\*, 75–79 \*\*([\d.]+)\*\*, 80–84 "
         r"\*\*([\d.]+)\*\*, 85–89\s*\*\*([\d.]+)\*\*, 90\+ \*\*([\d.]+)\*\*, against ([\d.]+) for "
         r"everyone under 65.*?by\s*([\d.]+), on the smallest band",
         ("bandratio_65-69", "bandratio_70-74", "bandratio_75-79", "bandratio_80-84",
          "bandratio_85-89", "bandratio_90+", "bandratio_lt65",
          "bandratio_reversal"), 0.005),
        ("prose — the mean-based reading of the same index",
         r"the three-off-year mean gives\s*([\d.]+)×", "off_dissim_ratio_mean", 0.05),
        ("prose — recorded-female share, presidential",
         r"at ([\d.]+)% in the 2024 presidential electorate", "e24_female", 0.05),
        # CORRECTED 2026-08-06 (ledger item C2, author answered "fix the data and
        # correct the sentence"). It used to read "rising from 52.5% … to
        # 53.0–53.1%", which covers 2023 (52.97) and 2025 (53.12) but not 2021,
        # which reads 52.46 — statistically indistinguishable from the
        # presidential 52.49 the sentence said it rose FROM. So the verb was
        # wrong for one of the three off-years, not just the range. Now asserted
        # against the off-year min and max, with the two that do rise named.
        ("prose — recorded-female share, full off-year range",
         r"and ([\d.]+)–([\d.]+)% across the off-year electorates",
         ("off_female_min", "off_female_max"), 0.05),
        ("prose — recorded-female share, the two off-years that do rise",
         r"while 2023 and 2025 sit at ([\d.]+)% and ([\d.]+)%",
         ("e23_female", "e25_female"), 0.05),
        ("prose — birth-year Dec-31 check, maximum off-year shift",
         r"moves the off-year 65\+ share by \*\*≤([\d.]+) points\*\*",
         "off_by_maxshift", 0.05),
        ("prose — birth-year Dec-31 check, the three worked examples",
         r"\(e\.g\., 2021: ([\d.]+)% → ([\d.]+)%; 2025: ([\d.]+)% → ([\d.]+)%\).*?"
         r"presidential share moves too, ([\d.]+)% → ([\d.]+)%\)",
         ("e21_by_main", "e21_by_dec31", "e25_by_main", "e25_by_dec31",
          "e24_by_main", "e24_by_dec31"), 0.05),
        ("prose — off-year 65+ trio restated in the ballot-content note",
         r"land close together\s*\(65\+ share ([\d.]+) / ([\d.]+) / ([\d.]+)%\)",
         ("e21_comp_65+", "e23_comp_65+", "e25_comp_65+"), 0.05),
        # ADDED 2026-08-09. The sentence used to call the 3.6-point spread across
        # the three off-years "direct evidence that none of them drives the
        # composition". Three observations with no counterfactual are consistent
        # with that, not evidence of it, and the spread is ~30% of the headline
        # gap the paper exists to establish. The figures are now probed so the
        # narrowed claim carries measured numbers.
        ("prose — off-year spread and the 2021 caveat",
         r"the 65\+ share moves ([\d.]+) → ([\d.]+) → ([\d.]+), a \*\*([\d.]+)-point\s*"
         r"spread\*\*, with the low year \(2021\) also being the year with the\s*"
         r"weakest voter-file coverage \(([\d.]+)%\) and the widest bound \(([\d.]+)–([\d.]+)%\)",
         ("e21_comp_65+", "e23_comp_65+", "e25_comp_65+", "off_65_spread",
          "e21_cov_pct", "e21_min65", "e21_max65"), 0.05),
    ]
    p += [
        # ADDED 2026-08-09; RE-ANCHORED 2026-08-14 when the ladder's primary row
        # switched to the active roll (referee item 5) and the note inverted —
        # the same nine figures, in the note's new arrangement.
        ("prose — active vs full roll, the ladder's basis disclosure",
         r"The ([\d.]+)M full roll additionally\s+carries ([\d,]+) inactive registrants "
         r"\(([\d.]+)%\), who are much\s+younger than active ones \(median (\d+) against "
         r"(\d+); ([\d.]+)% are 65\+ against ([\d.]+)%; ([\d.]+)% are\s+under 30 against "
         r"([\d.]+)%\)",
         ("roll_m", "roll_inactive_n", "roll_inactive_pct", "roll_inactive_median",
          "roll_active_median", "roll_inactive_65+", "roll_active_65+",
          "roll_inactive_18-29", "roll_active_18-29"), 0.05),
        # Tolerance 1.0, not 0.05: the middle term is a quotient printed as a whole
        # number (5,100,471.46), so a sub-unit tolerance would fail on the paper
        # having rounded it. The claim being tested is that the quotient lands on
        # the ACTIVE roll rather than the full one, and those differ by 416,492.
        ("prose — the five official turnout rates restated in the basis note",
         r"Every official turnout rate quoted here — ([\d.]+) / ([\d.]+) / ([\d.]+) / "
         r"([\d.]+) / ([\d.]+)%",
         ("off_turnout_2021", "off_turnout_2022", "off_turnout_2023",
          "off_turnout_2024", "off_turnout_2025"), 0.0),
        ("prose — the implied official denominator is the active roll",
         r"([\d,]+) ballots ÷ ([\d.]+)% = ([\d,]+) against an active roll of ([\d,]+)",
         ("e25_official", "off_turnout_2025", "roll_implied_official",
          "roll_active_total"), 1.0),
        ("prose — how closely the implied denominator lands on the active roll",
         r"against an active roll of [\d,]+, a ([\d.]+)% match",
         "roll_active_implied_gap", 0.005),
        # The retired "the row would read ..." probe's three figures now live in the
        # note's "full roll including inactive registrants reads ..." sentence, which
        # the who-is-counted full-roll probe above asserts in full.
    ]

    # ---------------------------------------------------------------
    # INTERPRETATION (added 2026-08-11, when the section entered AUDIT_BOUNDS).
    #
    # The decomposition table and its sub-note were already probed; everything
    # below was prose the gate could not see. The section is the smallest
    # remaining uncovered block in the paper and carries its highest-stakes
    # content, which is why it went before the three larger appendices.
    # ---------------------------------------------------------------
    p += [
        # RESTRUCTURED 2026-08-14 (referee item 4): the corrected bound now leads and
        # the uncorrected raw span sits in the parenthetical, so both are captured from
        # the one sentence — the lead is what a citing reader takes.
        ("interpretation — the corrected overlap bound leads; the raw span follows",
         r"At most \*\*(\d+)–(\d+)%\*\* of each off-year electorate also cast a 2024\s+"
         r"presidential ballot \(the survivorship-corrected bound derived below; the "
         r"uncorrected,\s+roll-visible figures read (\d+)–(\d+)%\)",
         ("core_corr_lo", "core_corr_hi", "core_lo", "core_hi"), 0.5),
        # The longitudinal measure that earns the word "habitual" (referee item 4):
        # off-year voters' participation across ALL FIVE 2021-2025 November generals,
        # against the presidential electorate on the same current-roll panel.
        ("interpretation — the sub-note's uncorrected-range lead",
         r"The uncorrected (\d+)–(\d+)% range is biased upward",
         ("core_lo", "core_hi"), 0.5),
        ("interpretation — longitudinal generals participation, off-year vs presidential",
         r"averaged\s+\*\*([\d.]+)–([\d.]+)\*\* of the five 2021–2025 November generals, "
         r"and \*\*([\d.]+)–([\d.]+)%\*\* cast a ballot in at\s+least four of the five, "
         r"against \*\*([\d.]+)\*\* and \*\*([\d.]+)%\*\* for the presidential electorate",
         ("hab5_mean_lo", "hab5_mean_hi", "hab5_ge4_lo", "hab5_ge4_hi",
          "hab5_pres_mean", "hab5_pres_ge4"), 0.05),
        # The registration-date validation (referee item 1): both instruments, all five
        # figures, so the paper's strongest new methods claim is asserted, not narrated.
        ("interpretation — registration-date validation, snapshot identity",
         r"Of the\s+\*\*([\d.]+) million\*\* registrants present in both the "
         r"September-2023 snapshot and the\s+April-2026 roll, \*\*([\d.]+)%\*\* carry a "
         r"byte-identical registration date across the 31\s+months between them and only "
         r"\*\*([\d.]+)%\*\* were re-stamped later",
         ("regv_common_m", "regv_same_pct", "regv_restamp_pct"), 0.05),
        ("interpretation — registration-date validation, per-election ceiling",
         r"at most\s+\*\*([\d.]+)%\*\* of credited voters carry a registration date later "
         r"than the election they are\s+credited in.*?moves no participation rate in this "
         r"paper by\s+more than \*\*([\d.]+)\*\* points",
         ("regv_late_max", "regv_rate_maxdelta"), 0.05),
        # The reverse overlap. Endpoints are the paper's HALF-UP ROUNDING of
        # 42.5455-48.2530; see the derivation for why that is encoded there
        # rather than absorbed into a tolerance.
        ("interpretation — the reverse overlap, presidential voters who returned",
         r"but only \*\*(\d+)–(\d+)%\*\* of 2024 presidential voters showed up in a given "
         r"off-year",
         ("presret_lo_rd", "presret_hi_rd"), 0.05),
        ("interpretation — habitual core vs presidential-only, size and both bands",
         r"the \*\*habitual core\*\* \(voted both; ([\d.]+)M\) is \*\*([\d.]+)% 65\+ and "
         r"([\d.]+)% under 30\*\*, while the \*\*presidential-only group\*\* \(([\d.]+)M\) "
         r"is \*\*([\d.]+)% 65\+ and ([\d.]+)% under 30\*\*",
         ("hab_m", "hab_65", "hab_u30", "presonly_m", "presonly_65", "presonly_u30"), 0.05),
        # Split from the presidential half so that 28.5% keeps a tight tolerance
        # and is NOT swept into the round_exempt the off-year half needs.
        # RESOLVED 2026-08-11 (author): "about 40%" -> "about 39%", so this is now the
        # rounding of the derived value and needs neither a wide tolerance nor a
        # round_exempt. It was ledger open item 2.
        ("interpretation — the gap restated, off-year half",
         r"\*gap\* \(about (\d+)% 65\+ off-year", "off_comp_65+", 0.5),
        ("interpretation — the gap restated, presidential half",
         r"off-year versus about ([\d.]+)% presidential\)", "e24_comp_65+", 0.05),
        # Registration tenure. Bare integers with no unit, so the small-integer
        # pattern was waiving them — see the derivation for how that was found.
        ("interpretation — registration tenure, off-year span and presidential",
         r"a median of about \*\*(\d+)–(\d+) years\*\* since they registered, versus "
         r"\*\*(\d+)\*\* for the presidential electorate",
         ("tenure_off_lo", "tenure_off_hi", "e24_tenure"), 0.0),
        ("interpretation — Lucero et al. (2025), over-45 shares",
         r"put voters over 45 at \*\*([\d.]+)%\*\* of the off-cycle electorate versus "
         r"\*\*([\d.]+)%\*\* of the presidential-year one",
         ("lit_lucero_off45", "lit_lucero_pres45"), 0.0),
        ("interpretation — Hajnal et al., the over-55 gap",
         r"a roughly \*\*(\d+)-point\*\* over-55 gap", "lit_hajnal_over55_gap", 0.0),
        ("interpretation — Ornstein (2024), bill number and study size",
         r"mandate \(SB (\d+)\) across (\d+) local governments",
         ("lit_sb_number", "lit_ornstein_govts"), 0.0),
    ]

    # ---------------------------------------------------------------
    # APPENDICES A, C, G and the End note (added 2026-08-11, fifth sitting).
    # A and C are almost entirely RESTATEMENTS of figures asserted elsewhere,
    # which is exactly the position a contradiction hides in: correct table,
    # correct appendix, and a sentence between them reporting neither. Four of
    # A's spans turned out to be quantities that exist nowhere else in the
    # paper — a pooled partisan+measure range, an all-office odd-year range, the
    # off-year median-age span (not its mean), and a ratio of two figures each
    # separately asserted.
    # ---------------------------------------------------------------
    p += [
        ("appendix A — roll-off by contest class, pooled and restated",
         r"was \*\*~([\d.]+)–([\d.]+)%\*\* for partisan statewide offices and ballot "
         r"measures,\s*\*\*~([\d.]+)–([\d.]+)%\*\* for \*contested\* nonpartisan statewide "
         r"races \(Supreme Court, Superintendent\s*of Public Instruction\), and "
         r"\*\*~([\d.]+)%\*\* for \*uncontested\* ones",
         ("f_ro_pm_lo", "f_ro_pm_hi", "f_ro_npcon_lo_tr", "f_ro_npcon_hi_tr",
          "f_ro_npunc_hi"), 0.5),
        ("appendix A — the classic roll-off estimate from the literature",
         r"classic ~(\d+)–(\d+)% estimate \(Wattenberg",
         ("lit_wattenberg_lo", "lit_wattenberg_hi"), 0.0),
        ("appendix A — the odd-year ballot-return figure the comparison rests on",
         r"the ~([\d.]+)% odd-year figure is \*ballot return\*", "f_base_odd", 0.5),
        ("appendix A — odd-year local contests, all offices and fire districts",
         r"roll off too — ([\d.]+)–([\d.]+)%\s*on a conservative floor, and ([\d.]+)–([\d.]+)% "
         r"for fire districts",
         ("f_odd_local_lo", "f_odd_local_hi", "f_odd_fire_lo", "f_odd_fire_hi"), 0.5),
        ("appendix A — the odd-year statewide item, restated",
         r"\*statewide\* item does not, at ([\d.]+)–([\d.]+)%",
         ("f_odd_statewide_lo", "f_odd_statewide_hi"), 0.05),
        ("appendix A — the symmetric comparison at a common 34%",
         r"at a common (\d+)% the deciding electorate is\s*~([\d.]+)% of registered voters on "
         r"a presidential ballot and ~([\d.]+)% on a midterm one, against an\s*odd-year "
         r"~([\d.]+)% rather than the ~([\d.]+)%",
         ("f_scen_hi", "f_grid_pres_34", "f_grid_mid_34", "f_grid_odd_34",
          "f_base_odd"), 0.5),
        ("appendix A — the median-age ladder, off-year SPAN not mean",
         r"median age ~(\d+)–(\d+) vs (\d+), and about a decade older than the\s*median "
         r"registrant at (\d+)",
         ("off_median_lo", "off_median_hi", "e24_median", "roll_median"), 0.5),
        ("appendix A — the 65+ representation ratio and both ACS benchmarks",
         r"electorate is ~([\d.]+)% 65\+, over \*\*([\d.]+) times\*\* the\s*\*\*([\d.]+)%\*\* "
         r"of citizen voting-age Washingtonians who are 65\+ \(ACS 2020–24 CVAP\) and nearly\s*"
         r"double the ([\d.]+)% of all adult residents",
         ("off_comp_65+", "a_ratio_65_cvap", "acs_cvap_65+", "acs_adult_65+"), 0.5),
        ("appendix A — the 18-29 side of the same comparison",
         r"its 18–29 share \(~([\d.]+)%\) is under\s*two-fifths of the ~(\d+)% in both "
         r"benchmarks",
         ("off_comp_18-29", "acs_cvap_18-29"), 0.5),
        # Appendix C restatements.
        # "The question" and the validation section (2026-08-11, sixth sitting).
        ("the question — the odd-year turnout figure the paper is about, both statements",
         r"when only about \*\*([\d.]+)%\*\* of registered voters", "f_base_odd", 0.5),
        ("the question — the same figure restated in the next sentence",
         r"who that ([\d.]+)% is, voter by voter", "f_base_odd", 0.5),
        ("the question — odd-year roll-off, all five offices",
         r"runs about \*\*([\d.]+)–([\d.]+)%\*\* for mayor, \*\*([\d.]+)–([\d.]+)%\*\* for port "
         r"commissioner, \*\*([\d.]+)–([\d.]+)%\*\* for city council, \*\*([\d.]+)–([\d.]+)%\*\* "
         r"for school director and \*\*([\d.]+)–([\d.]+)%\*\* for fire district",
         ("f_odd_mayor_lo", "f_odd_mayor_hi", "f_odd_port_lo", "f_odd_port_hi",
          "f_odd_council_lo", "f_odd_council_hi", "f_odd_school_lo", "f_odd_school_hi",
          "f_odd_fire_lo", "f_odd_fire_hi"), 0.5),
        ("the question — the statewide item, restated",
         r"rolls off only \*\*([\d.]+)–([\d.]+)%\*\*",
         ("f_odd_statewide_lo", "f_odd_statewide_hi"), 0.05),
        ("validation — the two bases of the 2021 observed cell, and the gap between them",
         r"\(2021 = ([\d.]+)%; the composition table's ([\d.]+)% adds a .registered "
         r"on/before the\s*election. filter, whose real effect is about \*\*([\d.]+)\*\* "
         r"points — the two figures are ([\d.]+)\s*and ([\d.]+) and straddle a rounding "
         r"boundary",
         ("e21_obs65", "e21_comp_65+", "e21_basis_gap", "e21_obs65", "e21_comp_65+"), 0.05),
        ("validation — the snapshot column is reproducible from the two published numbers",
         r"reproduces the snapshot column to within ([\d.]+) points", "snap_blend_max", 0.05),
        # End note.
        ("end note — the source scale, restated a third time",
         r"the ([\d.]+)M-voter roll joined to ([\d.]+)M individual vote records",
         ("roll_m", "history_m"), 0.05),
        ("end note — the grid columns named in the reproduction paragraph",
         r"the enlargement grid's (\d+)% and (\d+)% columns still match",
         ("f_scen_mid", "f_scen_hi"), 0.0),
        ("appendix C — the vote-history record count, restated in methods",
         r"`voting_history` \(([\d.]+)M records\) joined to `voters`", "history_m", 0.05),
        ("appendix C — the imputation bound, restated",
         r"moves the off-year 65\+ share by ≤([\d.]+) points and leaves the gap intact",
         "off_by_maxshift", 0.05),
        ("appendix C — the coverage span, restated",
         r"against certified\s*counts is ([\d.]+)–([\d.]+)%", ("cov_lo", "cov_hi"), 0.05),
        # Appendix G. Its partial correlations control for ONE covariate (the precinct 65+
        # share), not Appendix F's five — a different specification answering a different
        # question, and the two must never be quoted as if they were the same cut.
        ("appendix G — the precinct universe, stated to the nearest hundred",
         r"dropoff_demographics\.py`, ~([\d,]+) precincts\)", "g_n_prec_h100", 0.0),
        ("appendix G — the raw ecological picture, four predictors",
         r"Pearson r ≈ \+([\d.]+) on % white, \+([\d.]+) on % college, \+([\d.]+) on the 65\+ "
         r"share\),\s*more-Hispanic precincts hold onto fewer \(−([\d.]+)\), and income is "
         r"nearly flat \(−([\d.]+)\)",
         ("g_raw_white", "g_raw_college", "g_raw_over65", "g_raw_hisp",
          "g_raw_income"), 0.05),
        ("appendix G — what survives control for the precinct 65+ share",
         r"\(partial r ≈ \+([\d.]+)\) while race attenuates but does not vanish \(\+([\d.]+) "
         r"on % white, −([\d.]+) on\s*% Hispanic\) and income stays near zero \(\+([\d.]+)\)",
         ("g_part_college", "g_part_white", "g_part_hisp", "g_part_income"), 0.05),
    ]

    # ---------------------------------------------------------------
    # APPENDIX F (added 2026-08-11). 104 substantive tokens, none previously
    # asserted — the largest single uncovered block in the paper, and the only
    # one that needs more than the voter file. See `derive_appendix_f`.
    # ---------------------------------------------------------------
    p += [
        ("appendix F — the roll-off denominator, official ballots counted",
         r"official 2024 ballots = ([\d,]+)\)", "f_ballots", 0.0),
        ("appendix F — even-year, top of ticket",
         r"\| Top of ticket \| President \| ([\d.]+)% \|", "f_ro_president", 0.05),
        ("appendix F — even-year, partisan statewide range",
         r"\| Partisan statewide office \| Governor … Insurance Comm\. \| ([\d.]+)–([\d.]+)% \|",
         ("f_ro_partisan_lo", "f_ro_partisan_hi"), 0.05),
        ("appendix F — even-year, ballot measure range",
         r"\| Statewide ballot measure \| I-2109 … I-2124 \| ([\d.]+)–([\d.]+)% \|",
         ("f_ro_measure_lo", "f_ro_measure_hi"), 0.05),
        ("appendix F — even-year, nonpartisan contested range",
         r"\| \*\*Nonpartisan statewide, contested\*\* \| [^|]+ \| \*\*([\d.]+)–([\d.]+)%\*\* \|",
         ("f_ro_npcon_lo", "f_ro_npcon_hi"), 0.05),
        ("appendix F — even-year, nonpartisan uncontested range",
         r"\| \*\*Nonpartisan statewide, uncontested\*\* \| [^|]+ \| \*\*([\d.]+)–([\d.]+)%\*\* \|",
         ("f_ro_npunc_lo", "f_ro_npunc_hi"), 0.05),
        # The exclusions footnote states two load counts as fact. Both are derived,
        # because "a partial-load artifact, not roll-off" is a claim about the data
        # rather than about the world, and it is the reason a contest is dropped.
        ("appendix F — the Lt. Governor partial load, and the precinct universe",
         r"only ([\d,]+) of ([\d,]+) precincts / (\d+) of 39 counties",
         ("f_lg_precincts", "f_precincts_2024", "f_lg_counties"), 0.0),
        ("appendix F — the two headline roll-offs, restated in prose",
         r"about \*\*([\d.]+)%\*\* in contested statewide nonpartisan contests and about "
         r"\*\*([\d.]+)%\*\* in\s*uncontested ones",
         ("f_ro_npcon_hi", "f_ro_npunc_hi"), 0.5),
        # The scenario grid. Baselines and all nine cells, computed on unrounded
        # turnout; verified to agree with the printed cells on every one.
        ("appendix F — grid, presidential row",
         r"\| Presidential-year, 2024 \(~(\d+)%\) \| ~(\d+)% \| ~(\d+)% \| ~(\d+)% \|",
         ("f_base_pres", "f_grid_pres_5", "f_grid_pres_17", "f_grid_pres_34"), 0.5),
        ("appendix F — grid, midterm row",
         r"\| Midterm-year, 2022 \(~(\d+)%\) \| ~(\d+)% \| ~(\d+)% \| ~(\d+)% \|",
         ("f_base_mid", "f_grid_mid_5", "f_grid_mid_17", "f_grid_mid_34"), 0.5),
        ("appendix F — grid, odd-year row (the one that used to be blank)",
         r"\| Odd-year, 2021/23/25 avg \(~(\d+)%\), current baseline \| ~(\d+)% \| ~(\d+)% "
         r"\| ~(\d+)% \|",
         ("f_base_odd", "f_grid_odd_5", "f_grid_odd_17", "f_grid_odd_34"), 0.5),
        ("appendix F — King's share of the odd-year electorate",
         r"King — ([\d.]+)–([\d.]+)% of each odd-year\s*electorate",
         ("f_king_share_lo", "f_king_share_hi"), 0.5),
        # King's certified countywide ballots, from the pinned turnout-page CSV that
        # made the statewide-item denominator exact (2026-08-14, referee item 7).
        ("appendix F — King's certified ballots, all three odd years",
         r"King: ([\d,]+) in 2021, ([\d,]+) in 2023, ([\d,]+) in 2025",
         ("f_king_2021", "f_king_2023", "f_king_2025"), 0),
        # The odd-year table. 2023's statewide cell is "*none on the ballot*" and is
        # asserted as a COUNT of zero rather than left to a missing regex group — SB
        # 5082 repealed the advisory votes, so an empty cell is the right answer and
        # must be distinguishable from a load failure.
        ("appendix F — odd-year statewide item, both years that had one",
         r"\| Statewide item \(advisory votes / SJR 8201\) \| ([\d.]+)–([\d.]+)% \| "
         r"\*none on the ballot\* \| ([\d.]+)% \|",
         ("f_odd_statewide_2021_lo", "f_odd_statewide_2021_hi",
          "f_odd_statewide_2025_lo"), 0.05),
    ]
    for _label, _key in (("Fire district", "fire"), ("School director", "school"),
                         ("City council", "council"), ("Port commissioner", "port"),
                         ("Mayor", "mayor")):
        p.append((f"appendix F — odd-year {_label.lower()}, three years",
                  rf"\| {_label} \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| per-precinct",
                  tuple(f"f_odd_{_key}_{y}" for y in ("2021", "2023", "2025")), 0.05))
    p += [
        ("appendix F — the odd-vs-even statewide-measure comparison",
         r"rolls off ([\d.]+)–([\d.]+)%, which is essentially what a statewide measure on an "
         r"even-year ballot does \(([\d.]+)–([\d.]+)%\)",
         ("f_odd_statewide_lo", "f_odd_statewide_hi",
          "f_ro_measure_lo", "f_ro_measure_hi"), 0.05),
        ("appendix F — the local offices that roll off most",
         r"fire district ([\d.]+)–([\d.]+)%, school director and city council up to ([\d.]+)%",
         ("f_odd_fire_lo", "f_odd_fire_hi", "f_odd_school_council_hi"), 0.5),
        ("appendix F — the symmetric comparison the correction produces",
         r"presidential consolidation still reads ~([\d.]+)% against an odd-year ~([\d.]+)%, "
         r"and midterm consolidation ~([\d.]+)% against ~([\d.]+)%",
         ("f_grid_pres_17", "f_grid_odd_17", "f_grid_mid_17", "f_grid_odd_17"), 0.5),
        ("appendix F — the margin of safety the old one-sided grid had",
         r"midterm/uncontested worst case \(~([\d.]+)%\) still beat the odd-year baseline "
         r"\(~([\d.]+)%\)",
         ("f_grid_mid_34", "f_base_odd"), 0.5),
        # The ecological block.
        ("appendix F — the county cut's universe",
         r"Across the (\d+) counties, roll-off on that contest", "f_county_n", 0.0),
        ("appendix F — the county correlation, both times it is stated",
         r"coefficient, of \*\*\+([\d.]+)\*\*, ≈\+([\d.]+), \*\*uncorrected",
         ("f_county_r", "f_county_r"), 0.05),
        ("appendix F — the precinct sample and what it is a share of",
         r"Across ([\d,]+) precincts — \*\*([\d.]+)% of the state's ([\d,]+)\*\*",
         ("f_prec_n_sc2", "f_prec_pct_of_total", "f_precincts_2024"), 0.5),
        ("appendix F — how the precinct sample is lost, both stages and the floor",
         r"([\d,]+) precincts carry apportioned Census\s*demographics, and a floor of (\d+) "
         r"presidential votes removes a further ([\d,]+) of those",
         ("f_prec_demo", "f_min_pres_votes", "f_prec_dropped"), 0.0),
        ("appendix F — the precinct mean roll-off",
         r"race averages\s*\*\*([\d.]+)%\*\*", "f_prec_mean_sc2", 0.05),
        ("appendix F — the ballots basis, which does not transfer",
         r"\(giving ([\d.]+)% for this race\)", "f_ro_npcon_hi", 0.05),
        ("appendix F — statewide put on the precinct cut's own basis",
         r"([\d,]+) Supreme Court votes\s*against ([\d,]+) presidential votes — and it is "
         r"\*\*([\d.]+)%\*\*, against the precinct mean of ([\d.]+)%",
         ("f_sc2_votes", "f_pres_votes", "f_statewide_on_pres_basis",
          "f_prec_mean_sc2"), 0.05),
        ("appendix F — President's own roll-off against ballots",
         r"\(President itself rolls off ([\d.]+)% against ballots", "f_ro_president", 0.05),
        ("appendix F — the county correlation collapsing at precinct level",
         r"the correlation\s*falls from \+([\d.]+) to about \*\*\+([\d.]+)\*\*",
         ("f_county_r", "f_elec65_raw"), 0.05),
        ("appendix F — the resident-65+ predictor, raw",
         r"from the Census — gives \*\*\+([\d.]+)\*\*", "f_res65_raw_sc2", 0.05),
        ("appendix F — partial table, precinct electorate 65+",
         r"\| Precinct \*\*electorate\*\* 65\+ share \(the county cut's own yardstick\) \| "
         r"\+([\d.]+) \| \*\*−([\d.]+)\*\* \|",
         ("f_elec65_raw", "f_elec65_partial_mag"), 0.05),
        ("appendix F — partial table, resident 65+ on the contested court race",
         r"\| Precinct \*\*resident\*\* 65\+ share \(ACS\), contested court race \| \+([\d.]+) "
         r"\| \*\*\+([\d.]+)\*\* \|",
         ("f_res65_raw_sc2", "f_res65_partial_sc2"), 0.05),
        ("appendix F — partial table, resident 65+ on Superintendent",
         r"\| Precinct \*\*resident\*\* 65\+ share \(ACS\), Superintendent \| \+([\d.]+) \| "
         r"\*\*\+([\d.]+)\*\* \|",
         ("f_res65_raw_spi", "f_res65_partial_spi"), 0.05),
        ("appendix F — the electorate partial restated in prose",
         r"used — it is −([\d.]+), which is nothing", "f_elec65_partial_mag", 0.05),
        ("appendix F — the crosswalk-constrained subsample",
         r"rest on\s*\*\*([\d,]+)\*\* precincts rather than ([\d,]+)",
         ("f_prec_n_xwalk", "f_prec_n_sc2"), 0.0),
        # REWRITTEN 2026-08-11, ledger item C4. This parenthesis used to pair a
        # statewide PRECINCT-COUNT coverage figure with an Okanogan ACTIVE-VOTER
        # one, and the statewide half was stale besides. Both are now on the
        # active-registrant basis and the sentence names it.
        ("appendix F — crosswalk coverage, both halves on ONE declared basis",
         r"bridges \*\*([\d.]+)%\*\* of active registrants statewide but only "
         r"\*\*([\d.]+)%\*\* in Okanogan",
         ("f_xwalk_all", "f_xwalk_okanogan"), 0.05),
        # The grid's scenario columns, and both filter thresholds, asserted against the
        # parameters the SQL actually uses.
        ("appendix F — the grid's three scenario columns",
         r"\| Scenario \(baseline turnout\) \| (\d+)% roll-off \| (\d+)% roll-off \| "
         r"(\d+)% roll-off \|",
         ("f_scen_lo", "f_scen_mid", "f_scen_hi"), 0.0),
        ("appendix F — the scenario span restated",
         r"It applied (\d+)–(\d+)% roll-off to the two hyp",
         ("f_scen_lo", "f_scen_hi"), 0.0),
        ("appendix F — the contested column named in the sub-note",
         r"not like-for-like with the (\d+)% column", "f_scen_mid", 0.0),
        ("appendix F — the common-roll-off comparison",
         r"at a common (\d+)%, presidential consolidation", "f_scen_mid", 0.0),
        ("appendix F — the even-year ranges restated in the odd-year sub-note",
         r"deliberately separates \(([\d.]+)–([\d.]+)% contested against ([\d.]+)–([\d.]+)% "
         r"uncontested\)",
         ("f_ro_npcon_lo", "f_ro_npcon_hi", "f_ro_npunc_lo", "f_ro_npunc_hi"), 0.05),
        ("appendix F — the county r restated where the precinct cut takes over",
         r"just \*rural\*\. The \+([\d.]+) blends the two", "f_county_r", 0.05),
        ("appendix F — the ballots-basis figure that does not transfer",
         r"what does not transfer between them is the ([\d.]+)% figure",
         "f_ro_npcon_hi", 0.05),
        ("appendix F — the crosswalk subsample's voter threshold",
         r"a VRDB crosswalk row, and (\d+)\+ precinct voters",
         "f_min_xwalk_voters", 0.0),
        ("appendix F — the two further predictors, reported rather than dropped",
         r"ACS median age is the largest surviving partial at\s*\*\*\+([\d.]+)\*\* \(raw "
         r"\+([\d.]+)\), and the ACS under-30 share is the only raw predictor pointing toward\s*"
         r"the worry, at \*\*−([\d.]+)\*\*",
         ("f_medage_partial", "f_medage_raw", "f_under30_raw_mag"), 0.05),
    ]

    # ---------------------------------------------------------------
    # APPENDIX H (added 2026-08-11, when the section entered AUDIT_BOUNDS).
    # The fifteen printed rows, one probe each so a failure names the age, plus
    # the prose the table is read through. See the derivation for why the
    # UNCHECKED entry that covered this was not load-bearing.
    # ---------------------------------------------------------------
    for _a in range(20, 91, 5):
        p.append((f"appendix H — age {_a} row",
                  rf"\| {_a} \| ([\d,]+) \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \|",
                  (f"hrow_{_a}_roll", f"hrow_{_a}_t24", f"hrow_{_a}_t25", f"hrow_{_a}_ret"),
                  0.05))
    p += [
        ("appendix H — the curve's length, as the appendix states it twice",
         r"prints all (\d+) single ages", "h_n_ages", 0.0),
        ("appendix H — the ramp, its average and the two named stretches",
         r"rises steadily from ([\d.]+)% at age 20 to a peak of ([\d.]+)% at age 79 — an "
         r"average of about\s*\*\*([\d.]+) points per year of age\*\*",
         ("h_ret_20", "h_peak_ret", "h_ramp_avg"), 0.05),
        ("appendix H — the forties slope",
         r"about ([\d.]+) points per year from 40 to 50", "h_slope_40_50", 0.05),
        # The two sixties slopes and the 60-64 per-year figure are the three the
        # paper computes from its own PRINTED cells rather than the curve; each
        # carries a round_exempt naming that. The tolerance is not widened.
        ("appendix H — the sixties slopes",
         r"([\d.]+) points per year from 60 to 65 and \*\*([\d.]+) from 65 to 70\*\*",
         ("h_slope_60_65", "h_slope_65_70"), 0.05),
        ("appendix H — the 64/66 and 60/64 per-year slopes",
         r"same per-year slope \(([\d.]+) against ([\d.]+) points\)",
         ("h_slope_64_66", "h_slope_60_64"), 0.05),
        # "the steepest five-year stretch on the curve" is a superlative and so
        # carries no token a regex can catch — the same blind spot that let "the
        # highest of the four" ship false in the money paper. Asserted as the age
        # the steepest stretch begins at, which is what the sentence claims.
        ("appendix H — the steepest stretch really is 65-70 (superlative as a figure)",
         r"\*\*([\d.]+) from 65 to 70\*\*, the steepest\s*five-year stretch on the curve",
         "h_slope_65_70", 0.05),
        # The minimum's AGE is captured as well as its value (the
        # tossup18_next_year pattern): the retired whole-roll basis put the
        # minimum at 19, and only the attribution check would notice it moving.
        ("appendix H — young end, presidential TURNOUT not retention",
         r"age 20 is a local peak\s*\(([\d.]+)%\), above both 19 \(([\d.]+)%\) and the "
         r"mid-20s trough.*?minimum of the whole young range at (\d+) \(([\d.]+)%\)",
         ("h_t24_20", "h_t24_19", "h_t24_young_min_age", "h_t24_25"), 0.05),
        ("appendix H — young end, retention is flat where turnout is not",
         r"nearly flat \(([\d.]+)% at 19, ([\d.]+)% at 20, ([\d.]+)% at 21\)",
         ("h_ret_19", "h_ret_20", "h_ret_21"), 0.05),
        ("appendix H — 19-year-old retention, restated in the table footnote",
         r"19-year-olds retain at ([\d.]+)%", "h_ret_19", 0.05),
        ("appendix H — the ramp average, restated at the 65 boundary",
         r"running at roughly double the ([\d.]+)-point-per-year average",
         "h_ramp_avg", 0.05),
        ("appendix H — the one upward step in the tail, and the dip it is sized against",
         r"93→94 \(\+([\d.]+)\).*?a ([\d.]+)-point dip from 51 to 52",
         ("h_step_93_94", "h_dip_51_52"), 0.05),
    ]

    # ---------------------------------------------------------------
    # APPENDIX E prose (added 2026-08-11). The 39-row table and both range
    # statements were already probed; this sentence, which is the stated REASON
    # the table averages 2023 and 2025 rather than all three off-years, was not.
    # NOTE THE ORDER: the sentence names "2023 and 2025" but prints the coverage
    # figures DESCENDING (99.6 is 2025, 95.9 is 2023), so the keys below are
    # deliberately not in the order the words appear. Pinning the year to each
    # figure here is what stops the pair being read as respective.
    # ---------------------------------------------------------------
    p.append(
        # The appendix's claim about THIS script. It is the same 39 as the
        # "positive in all 39 counties" probe, but it is a separate sentence
        # making a separate promise, and the small-integer waiver was covering it.
        ("appendix E — the count of rows this script claims to re-derive",
         r"\(all (\d+) rows re-derived by", "cty_n", 0.0))
    p.append(
        ("appendix E — why the average uses 2023 and 2025 (coverage, desc order)",
         r"analyzable coverage is much higher than 2021's \(([\d.]+)% and ([\d.]+)% vs "
         r"([\d.]+)%\)",
         ("e25_cov_pct", "e23_cov_pct", "e21_cov_pct"), 0.05))

    # ---- Appendix E: every county row, both halves of the two-up table.
    # Built as one probe per county rather than one giant regex, so a failure
    # names the county instead of "the table".
    _CTY_RX = (r"\| {c} \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| \+([\d.]+) \|")
    for _c in sorted({k.split("_")[1] for k in derived if k.startswith("cty_")
                      and k.count("_") == 2 and k.endswith("_e24")}):
        _disp = _c.title().replace(" ", " ")
        p.append((f"appendix E — {_disp}",
                  _CTY_RX.format(c=re.escape(_disp)),
                  (f"cty_{_c}_e24", f"cty_{_c}_e23", f"cty_{_c}_e25", f"cty_{_c}_gap2"),
                  0.05))
    # The 2026-08-15 transposition correction cites the two certified counts that
    # exposed it; both come from the pinned certified turnout frame, so the note
    # is tied to its evidence rather than restated.
    p.append(("appendix E — the Kittitas/Klickitat correction's certified counts",
              r"certified November 2025 turnout page \(Kittitas ([\d,]+)\s*"
              r"registered; Klickitat ([\d,]+)\)",
              ("cty_pin_KITTITAS_reg", "cty_pin_KLICKITAT_reg"), 0))
    return p



UNCHECKED = [
    "The ACS resident and citizen-voting-age rows of the 'who is counted' table — external "
    "Census estimates, not derivable from the voter file. They are the benchmark the file is "
    "measured against, so re-deriving them here is not possible and not the point",
    # NARROWED 2026-08-11. This entry used to cover the whole of Appendix H on the
    # argument that "a probe per cell buys no additional failure mode" — the same
    # argument the Appendix E entry made before an outside pass found six wrong
    # cells in it. The appendix PRINTS fifteen rows, not 78, and all sixty of
    # their cells are now asserted. What remains genuinely unchecked is the 63
    # ages the appendix does not print.
    "The 63 single ages Appendix H does NOT print — it shows five-year steps, and all "
    "fifteen printed rows (roll, both turnouts, retention) are asserted cell by cell, as "
    "are the prose figures read off the unprinted ages (19, 21, 51/52, 64, 66, 79, 84, 93/94, "
    "95). scripts/diag_wa_age_curve.py prints the full 78-row curve",
]

# WHAT THIS LIST USED TO SAY, AND WHY THAT MATTERED (2026-08-09).
#
# Two of its three entries were false, and the paper cited this verifier as the
# source for exactly what they disclaimed:
#
#   * "the 39-county table … a probe per cell would triple this file for no
#     additional failure mode" — one derivation and one row-loop, not a tripling.
#     And there WAS an additional failure mode: an outside pass spot-checked 12
#     of the 39 rows and reported six wrong cells. Re-derived here, all 39 rows
#     reconcile, so those were a basis difference in the reviewer's query rather
#     than paper defects — but nothing in this file could have told the
#     difference, which is the point. The table is now derived.
#   * "The Das-Gupta decomposition — a derived quantity of the composition and
#     roll figures already asserted here" — it is not. It is a separate
#     construction over four counterfactual electorates, and TWO of its three
#     published off-years were reported under the wrong definition for two
#     rounds. Now asserted, both ratios, all three years.
#
# It also pointed at scripts/diag_offyear_age.py, which does not exist.
#
# The general lesson, which is why this comment is long: an UNCHECKED entry is a
# claim about coverage, and nothing checks it. Treat adding one as needing the
# same evidence as adding a probe.


# ---------------------------------------------------------------------------
# Coverage audit — ported from verify_donor_class.py, 2026-08-06
# ---------------------------------------------------------------------------
# WHY THIS PAPER NEEDS IT MOST. `--coverage` already existed here, but as an
# advisory report nobody had to act on, so "183 figures agree" was a floor with
# no stated ceiling. The donor paper learned the cost the hard way: after it
# claimed 309 figures verified, an EXTERNAL reviewer found four more
# contradictions in exactly the sections no probe pointed at. This paper is
# already public, so the same class of defect here is a correction to the
# published record rather than a pre-submission fix.
#
# Three rules the donor audit paid for, all of which bit on its first run:
#   1. An exemption must NAME where the figure is verified, or why it is not a
#      result. "Not a result" with no reason is how a real figure hides.
#   2. Sections MUST NOT OVERLAP. Spans are per-section coordinates, so a slice
#      that swallows another reports the inner one's cells as unmapped.
#   3. A section's end anchor must FOLLOW its start anchor, or `find` returns -1
#      and the slice silently runs to end-of-document.
# EXTENDED 2026-08-11 to `interpretation` and `appendixE`. The evidence for
# extending rather than guessing: across six papers taken through the four-pass
# protocol on 2026-08-10/11, EVERY paper defect found was outside a coverage
# span, or was a claim/cross-reference no regex gate can see. Not one was inside
# an audited section. This paper was the worst covered of the seven (30% of its
# substantive tokens) and is the only one already public.
#
# Order of extension is NOT largest-gap-first, deliberately:
#   * `appendixE` — its probes ALREADY EXIST (one per county, plus both range
#     statements and the gap ranges). The section simply was not in a span, so
#     completeness was never required of it. "Probes exist" and "coverage is
#     enforced" are different states, and the gap between them is where the risk
#     sits: nothing stopped a new uncovered figure being added beside 39 probed
#     rows.
#   * `interpretation` — the smallest remaining block and the highest-stakes
#     content in the paper (the Das-Gupta decomposition, the lever argument, the
#     policy caution). Two of its three published off-year decomposition ratios
#     were reported under the wrong definition for two rounds; the sub-note that
#     now keeps "rate ÷ rise" and "rate share of total movement" apart is the
#     repair, and this is what stops the two collapsing back into one name.
#
# EXTENDED AGAIN 2026-08-11 (same day, second sitting) to `appendixH`. Its 15
# printed rows were covered by an UNCHECKED entry making the same argument the
# Appendix E entry made before it was found wrong — see the derivation.
#
# COMPLETED 2026-08-11 (fifth sitting) with A, B, C, D and G. Every appendix is
# now gated. Appendix D is closed by a written reason rather than derivation —
# it is a bibliography — and B by its statute numbers being literals; both are
# in the exemption tables below with the reason stated, not waved through.
AUDITED_SECTIONS = ("composition", "rates", "finer", "tail", "interpretation",
                    "appendixA", "appendixB", "appendixC", "appendixD",
                    "appendixE", "appendixF", "appendixG", "appendixH",
                    "frontmatter", "abstract", "question", "validation", "limits",
                    "endnote")

# Regex exemptions, matched against the bare token. Reason required.
COVERAGE_EXEMPT = [
    (r"^(?:19|20)\d{2}$", "a calendar year, not a result"),
    (r"^\d{1,2}$", "small integer — list ordinals, cohort edges, column counts"),
    # Added 2026-08-11 with the `interpretation` section. All four occurrences
    # there are the ARITHMETIC BOUND of a ratio, not a measurement: "rate ÷ rise"
    # exceeds 100% whenever the roll effect is negative, "rate share of total
    # movement" is bounded by 100%, and a sub-100% figure described as a share of
    # the rise is self-contradictory. There is nothing to derive — the sentences
    # are what keeps the decomposition's two ratios from collapsing under one
    # name, which is the defect they were written to prevent.
    #
    # WHAT THIS MUST NOT BE ALLOWED TO SWALLOW LATER, since a pattern exemption
    # is document-wide: the paper's other three uses of "100%" are "~100%
    # coverage of the roll" (Data and validation, Appendix C, End note), which
    # IS an approximate empirical claim. It is checked as `history_aged_pct`
    # (96.95% of vote-history rows resolve to a roll row) and as the birth-year
    # completeness of the roll itself. A round that brings those sections into
    # AUDIT_BOUNDS must probe them rather than inheriting this waiver.
    (r"^100%$", "the arithmetic bound of a ratio, stated to keep the "
                "decomposition's two ratios distinct — see the note above"),
]
COVERAGE_EXEMPT = [(p, why) for p, why in COVERAGE_EXEMPT if why]

# Literal tokens, each with the reason it is not an unverified result.
COVERAGE_EXEMPT_LITERAL: dict[str, str] = {
    "01001": "Census table id B01001 (sex by age), not a figure — the values drawn "
             "from it are the ACS benchmark row, probed separately",
    "29001": "Census table id B29001 (citizen voting-age population by age), as above",
    "8201": "a bill number — Senate Joint Resolution 8201, named as the 2025 ballot's "
            "only statewide measure. Not a quantity",
    # Added 2026-08-11 with Appendix F. Both are MEASURE numbers naming the two 2024
    # initiatives whose roll-off the table reports; the roll-off itself is asserted as
    # the "ballot measure" range (f_ro_measure_lo/hi). Each occurs exactly once in the
    # paper, so neither waiver can reach anything else.
    "2109": "a measure number — Initiative 2109, one of the two 2024 ballot measures the "
            "roll-off table names. Its roll-off is verified in the table's range probe",
    "2124": "a measure number — Initiative 2124, as above",
    # Appendix B, added 2026-08-11. Statute and session-law numbers, each occurring only
    # in its own citation. The one CHECKABLE claim in that appendix — that every birth
    # value is a July-1 sentinel, which is what "no full date of birth is stored or used
    # here" rests on — is a `claim_guards` check, because the token is a bare "1" that the
    # small-integer rule waives and no probe can anchor on the word "every".
    "04.321": "an RCW section number — 29A.04.321, which sets which offices appear on the "
              "odd-year ballot. Not a quantity",
    "20230901": "part of the table identifier `voters_20230901`, the retained Sept-2023 roll "
                "snapshot. Its ROW COUNT is asserted separately as `snapshot_m`",
    "08.710": "an RCW section number — 29A.08.710, the statute limiting what the public "
              "voter file may contain. Not a quantity",
    "08.720": "an RCW section number — 29A.08.720, the elections-and-political-purposes "
              "use restriction. Not a quantity",
    "08.740": "an RCW section number — 29A.08.740, the redistribution penalty. Not a quantity",
    "5892": "a bill number — SB 5892 (2026), the voter-data protection strengthening. "
            "Not a quantity",
    "213": "a session-law chapter — Ch. 213, Laws of 2026, the same bill. Not a quantity",
    "359": "part of the GitHub account name `skirby359` in the repository URL, not a "
           "figure — `_NUMBER` sees the digits inside the identifier",
    "5082": "a bill number — SB 5082 (2023), which abolished Washington's tax advisory "
            "votes and is why the 2023 odd-year ballot carried no statewide contest. The "
            "FACT it is cited for is checked: `scripts/diag_wa_rolloff_oddyear.py` finds "
            "zero 2023 general races at statewide precinct coverage, against three in "
            "2021 and one in 2025. Not a quantity",
}

# Whole sections closed by a written reason rather than by derivation. Each must
# say WHERE the figures are checked, per rule 1 above.
COVERAGE_EXEMPT_SECTIONS: dict[str, str] = {
    # Added 2026-08-11. Appendix D is a BIBLIOGRAPHY: its nineteen unmapped tokens are
    # journal volume and issue numbers, page ranges and a DOI. There is no quantity in it
    # to derive, and the substantive figures it is cited FOR are asserted where the paper
    # uses them — Lucero et al.'s 58.4/49.7 and Hajnal et al.'s 22-point gap in the
    # interpretation section, Wattenberg et al.'s 2-10% roll-off estimate in Appendix A,
    # and Kitagawa-Das Gupta as the decomposition itself, whose three off-year ratios are
    # asserted in the interpretation table. A citation's page range is the one thing in
    # this paper that genuinely cannot be wrong about the world.
    "appendixD": "a bibliography — volume, issue, page and DOI numbers only. Every figure "
                 "these works are CITED for is asserted where the paper uses it: Lucero "
                 "and Hajnal in the interpretation section, Wattenberg in Appendix A, "
                 "Kitagawa-Das Gupta as the decomposition table itself",
}

_NUM_RX = vp._NUMBER
_SECTION_REF = vp._SECTION_REF


def claim_guards(d: dict) -> list[str]:
    """Assert Appendix H's COMPARATIVE claims, which no probe can anchor on.

    A superlative or an order-of-magnitude carries no numeric token, so `audit_coverage`
    cannot see it and a regex probe has nothing to capture. This project already shipped one
    false comparative on exactly that blind spot — safe-seat's "more than double any other
    year in the series" survived a round while every value it compared was individually
    asserted. Appendix H makes two of them, and both are cheap to check in code.

    A module-level function rather than inline in `main()` so it can be shown FAILING without
    a full verifier run — freeze rule §0 rule 2. Tested in
    `tests/test_infrastructure/test_wa_claim_guards.py`.
    """
    fails = []
    # The formal bound's SUBSET assumption (2026-08-14, referee item 6): the residual
    # `official − analyzable` is a strict bound only if the analyzable records are a
    # subset of the certified-ballot universe. The paper now states the assumption; this
    # asserts its observable implication — analyzable never exceeds certified.
    _over = {t: d[f"{t}_cov_pct"] for _, t in ELECTIONS if d.get(f"{t}_cov_pct", 0) > 100}
    if _over:
        fails.append(
            f"claim: the worst-case bound assumes analyzable ⊆ certified ballots, and the "
            f"reconstruction now EXCEEDS the certified count in {_over} — the residual is "
            f"no longer pure omission, so the bound construction is invalid there. Fix the "
            f"data or the bound, not this guard.")
    if d["h_steepest_5yr_start"] != 65:
        fails.append(
            f"claim: Appendix H calls 65→70 'the steepest five-year stretch on the curve', "
            f"and it is not — the steepest begins at age {d['h_steepest_5yr_start']}. Fix the "
            f"sentence, not this guard.")
    if not (8.0 <= d["h_dip_ratio"] <= 12.0):
        fails.append(
            f"claim: the 93→94 step is described as 'about ten times the size of the 51→52 "
            f"dip', and the ratio is {d['h_dip_ratio']:.2f}. Outside 8-12 'about ten times' is "
            f"the wrong description — reword it.")

    # --- Appendix F -------------------------------------------------------
    # The grid's 17% and 34% columns are not free parameters: the appendix picks them
    # BECAUSE they are the measured contested and uncontested nonpartisan roll-off, and
    # the prose calls them "the 17% column" and "uncontested (worst observed)". If the
    # measurements move and the columns do not, the grid quietly starts modelling
    # scenarios this paper no longer reports. Nothing else checks that: both sides are
    # individually asserted and would both still pass.
    for scen, measured, what in ((d["f_scen_mid"], d["f_ro_npcon_hi"], "contested"),
                                 (d["f_scen_hi"], d["f_ro_npunc_hi"], "uncontested")):
        if round(measured) != scen:
            fails.append(
                f"claim: the enlargement grid's {scen}% column is presented as the measured "
                f"{what} nonpartisan roll-off, which is now {measured:.1f}% and rounds to "
                f"{round(measured)}%. Either the column or the description has to move.")
    # "Court of Appeals (eight contests across all three divisions in 2024)" — a count
    # written as a WORD, so it carries no token for the coverage audit to see and no
    # digits for a probe to capture. It is the stated reason those contests are excluded.
    # --- Appendix B -------------------------------------------------------
    # "every birth value resolves to a July-1 sentinel" is the factual half of the
    # paper's strongest privacy claim. A single non-sentinel row would make it false, and
    # the sentence contains no token any probe can capture.
    if d["b_july1"] != d["b_birthdates"]:
        fails.append(
            f"claim: Appendix B says every birth value in the loaded file is a July-1 "
            f"sentinel, and {d['b_birthdates'] - d['b_july1']:,} of {d['b_birthdates']:,} "
            f"are not. That sentence supports 'no full date of birth is stored or used "
            f"here' — fix the claim, or find out why the extract changed.")
    if d["f_odd_statewide_2023_n"] != 0:
        fails.append(
            f"claim: the odd-year table prints '*none on the ballot*' for 2023's statewide "
            f"item, and the returns now carry {d['f_odd_statewide_2023_n']} statewide "
            f"contest(s) for that year. The probe's anchor is the literal phrase, so it "
            f"catches the paper changing but not the data — this is that half.")
    if d["f_coa_races"] != 8:
        fails.append(
            f"claim: the exclusions footnote says Court of Appeals had 'eight contests' in "
            f"2024, and the returns carry {d['f_coa_races']}. The word is spelled out, so no "
            f"probe can catch this — fix the footnote.")
    return fails


def main() -> int:
    raw = PAPER.read_text(encoding="utf-8")
    # Three tables share a row prefix — every one of them starts "| Nov 2024 | Presidential |"
    # — and differ only in how many numeric columns follow. A five-column pattern matches the
    # first five cells of the six-column finer-cohort row, so the tables are sliced apart
    # rather than distinguished by lookahead. Each slice's end anchor is the paragraph that
    # introduces the next table, and vp.section() raises if either anchor moves.
    sections = {
        "composition": vp.section(raw, "## What the data shows",
                                  "**Within-cohort participation rate"),
        "rates": vp.section(raw, "**Within-cohort participation rate", "**Finer cohorts.**"),
        "finer": vp.section(raw, "**Finer cohorts.**", "**Birth-year assumption.**"),
        # The rest of Sensitivity, previously unaudited. NOTE the real ordering:
        # "## Sensitivity" falls INSIDE the `rates` slice (the heading sits
        # between the rate table and "**Finer cohorts.**"), so slicing
        # Sensitivity as its own section would overlap both `rates` and `finer`
        # and report their probed cells as unmapped — rule 2. These four slices
        # partition "What the data shows" through "## Interpretation" exactly
        # once each.
        "tail": vp.section(raw, "**Birth-year assumption.**", "## Interpretation"),
    }
    norm = vp.normalise(raw)
    # Audit slices are taken from the NORMALISED text so their coordinates and
    # the whole-document probe spans agree. The probe-scoping slices above stay
    # on `raw` — they only feed regex matching, where the offset is irrelevant.
    audit_bounds = {
        "composition": ("## What the data shows", "**Within-cohort participation rate"),
        "rates": ("**Within-cohort participation rate", "**Finer cohorts.**"),
        "finer": ("**Finer cohorts.**", "**Birth-year assumption.**"),
        "tail": ("**Birth-year assumption.**", "## Interpretation"),
        # Added 2026-08-11. Both are disjoint from the four above and from each
        # other — rule 2. `interpretation` starts exactly where `tail` ends, and
        # `appendixE` sits between two appendix headings far below it.
        "interpretation": ("## Interpretation: mechanism, lever, and policy caution",
                           "## What this paper does not claim, and limits"),
        "appendixE": ("## Appendix E — 65+ share of the electorate by county",
                      "## Appendix F — Contest-level roll-off"),
        "appendixH": ("## Appendix H — The age gradient, one year at a time",
                      "## End note — data, reproduction, and series"),
        # Added 2026-08-11 (fourth sitting). Disjoint from appendixE, which ends
        # exactly where this begins, and from appendixH far below — rule 2.
        "appendixF": ("## Appendix F — Contest-level roll-off on the even-year ballot",
                      "## Appendix G — Off-cycle drop-off by precinct race"),
        # Added 2026-08-11 (fifth sitting), completing the appendices. These five
        # partition the run from Appendix A to Appendix E exactly once each, and
        # `appendixG` fills the gap between F and H — so the whole appendix block
        # A through H is now covered with no overlap and no hole (rule 2).
        "appendixA": ("## Appendix A — The objections, in full",
                      "## Appendix B — Data access and privacy"),
        "appendixB": ("## Appendix B — Data access and privacy", "## Appendix C — Methods"),
        "appendixC": ("## Appendix C — Methods", "## Appendix D — Related work"),
        "appendixD": ("## Appendix D — Related work", "## Appendix E — 65+ share"),
        "appendixG": ("## Appendix G — Off-cycle drop-off by precinct race",
                      "## Appendix H — The age gradient"),
        # Added 2026-08-11 (sixth sitting), completing the paper. `frontmatter`
        # starts at the H1, so together with the rest these partition the whole
        # document from title to End note with no overlap and no hole.
        "frontmatter": ("# Who Decides Washington State?", "## Abstract"),
        "abstract": ("## Abstract", "## The question"),
        "question": ("## The question", "## Data and validation"),
        "validation": ("## Data and validation", "## What the data shows"),
        "limits": ("## What this paper does not claim, and limits", "# Appendices"),
        # The End note runs to end-of-document, so it is sliced with an explicit
        # tail anchor rather than a following heading.
        "endnote": ("## End note — data, reproduction, and series",
                    "**Companion paper: [Safe-Seat Washington]"),
    }
    audit_sections, offsets = {}, {}
    for name, (start, end) in audit_bounds.items():
        audit_sections[name], offsets[name] = vp.slice_with_offset(norm, start, end)

    spans: dict = {}
    stats: dict = {}
    _derived = derive()
    rc = vp.run("WHO DECIDES WASHINGTON — prose scraped and asserted against the voter file",
                norm, build_probes(_derived), _derived, UNCHECKED,
                vp.wants_coverage(), sections=sections, spans_out=spans,
                stats_out=stats,
                round_exempt={
                    # The sentence says "ROUGHLY 2.5x", an explicit approximation,
                    # and the basis is ambiguous from the prose: mean-of-off-years
                    # over presidential is 2.59, minimum-off-year over presidential
                    # is 2.50 exactly. Both are defensible readings of "the off-year
                    # electorate", so the printed 2.5 is not a mis-rounding of a
                    # single derived value — it is a rounded statement of one of two
                    # constructions. Recorded rather than silently tolerated; if the
                    # paper is ever revised, saying which is meant would close this.
                    "prose — off-year electorate is ~2.5x as age-unrepresentative":
                        "paper states it as an approximation ('roughly'), and 2.50 vs "
                        "2.59 is the min-based vs mean-based reading of the same index",
                })

    # strict_units: an integer PERCENTAGE is a result and must be probed; a bare
    # small integer (ordinal, cohort edge, column count) stays exempt. Turned on
    # here first, 2026-08-09, because this is the posted paper — see the note in
    # `_verify_prose.audit_coverage` for what the loose form was hiding.
    # The End note states how many figures this verifier asserts, which no probe can
    # capture — the value IS the result of the probe pass. `vp.audit_satellite_counts`
    # below owns it and fails on a mismatch, which is how it has been corrected four times
    # today. The exemption is generated from whatever the paper currently claims rather
    # than hardcoded, so it cannot go stale and silently start waiving a different number.
    _literals = dict(COVERAGE_EXEMPT_LITERAL)
    _claimed = re.search(r"re-derives \*\*([\d,]+) figures\*\*", norm)
    if _claimed:
        _literals[_claimed.group(1).replace(",", "")] = (
            "the count of figures this run asserts, in the End note's reproduction "
            "paragraph. Owned by vp.audit_satellite_counts, which compares it against this "
            "run's own total; a probe cannot assert it because it is that total")
    # bold_is_result: a small integer the AUTHOR bolded is a result, not an ordinal, so it
    # is ineligible for pattern exemption. Enabled here first — this is the paper whose four
    # 2026-08-11 finds motivated the flag, and the only one already public. See
    # `tests/test_infrastructure/test_bold_is_result_rollout.py` for the roster.
    audit_fails = vp.audit_coverage(
        audit_sections, spans, offsets, AUDITED_SECTIONS,
        COVERAGE_EXEMPT, _literals, COVERAGE_EXEMPT_SECTIONS,
        strict_units=True, bold_is_result=True)
    audit_fails += vp.audit_satellite_counts(PAPER.name, stats.get("figures"))
    audit_fails += claim_guards(_derived)
    if audit_fails:
        print("\n" + "=" * 92)
        print(f"COVERAGE AUDIT: {len(audit_fails)} FAILURE(S)")
        print("=" * 92)
        for f in audit_fails:
            print(f"  - {f}")
        return 1
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
