"""WA 2024-general PRECINCT-LEVEL roll-off vs demographics — the finer ecological
sequel named in Appendix F of `docs/who-decides-washington.md`.

The published Appendix F correlates even-year roll-off against the electorate's 65+
share at the COUNTY level (n=39, Pearson r ~= +0.6, explicitly *uncorrected for
urbanicity*), and closes: "A finer precinct- or district-level ecological analysis is
the natural sequel." This is that sequel. It moves the same measure to the PRECINCT
level (~4,900 precincts with usable ACS demographics), which buys two things the county
cut could not:

  1. ~125x more units, so the age<->roll-off correlation is estimated far more sharply
     and is not hostage to a handful of large rural/urban counties.
  2. Enough units to CONTROL for the urban/rural + SES gradient that confounds the
     county correlation ("older counties are rural, with thinner coverage of statewide
     judicial races"). We residualize roll-off and age on ACS income / education /
     home value / renter share / log(population) and ask whether the age relationship
     SURVIVES that control (partial correlation). That is the point of descending to
     precincts.

WHAT THIS STILL IS NOT (read before citing):
  * It remains ECOLOGICAL. Precinct is sharper than county but does not defeat the
    ecological fallacy: a precinct-level association between age composition and
    roll-off does NOT establish that individual young voters skip the contest more.
  * Cast-vote records are ballot-anonymous — no voter age — so an individual-level
    roll-off-by-age measurement is impossible under secret-ballot rules, at ANY
    geography. This correlation is the ceiling of what the data can say.
  * The contested statewide nonpartisan judicial race (Supreme Court Pos. 2) is an
    imperfect analog for hyperlocal city-council / school-board contests.

Measure: roll-off = 1 - (votes in the contested nonpartisan contest / votes for
President) within a precinct, from certified 2024-general precinct returns
(data/wa_statewide.duckdb, election_id=2). President (race 3106) is the top-of-ticket
denominator; Supreme Court Pos. 2 (race 3406) is the contested-nonpartisan analog,
matching the county cut; Superintendent of Public Instruction (race 3362) is a second
contested-nonpartisan contest for robustness.

*** PROVENANCE TIER — NOT fully standalone from the public extract. ***
Unlike `diag_wa_rolloff_2024.py` (which needs only public precinct returns + the VRDB),
this script also reads two tables assembled by the upstream product ETL and NOT present
in a raw state extract:
  * `precinct_demographics`  — ACS block-group demographics apportioned to precincts;
  * `vrdb_precinct_crosswalk`— VRDB precinct codes -> certified-results precinct_id.
It is included for transparency and reproduces the Appendix F precinct paragraph, but,
like `diag_ie_vs_margin.py`, it depends on build inputs beyond the public data. The
paper's CORE numbers still reproduce from public data via the `verify_*` scripts.

Read-only, aggregates only. Run from the repo root (needs `data/` populated):
    python scripts/diag_wa_rolloff_precinct.py
"""
import math

import duckdb

DB = "data/wa_statewide.duckdb"
VRDB = "data/wa_vrdb.duckdb"

ELECTION_ID = 2               # 2024 general
PRES_RACE = 3106             # PRESIDENT/VICE PRESIDENT (top-of-ticket denominator)
CONTESTED = [
    (3406, "Supreme Court Pos. 2 (nonpartisan, contested)"),      # primary — matches county cut
    (3362, "Superintendent of Public Instruction (contested)"),   # robustness
]
MIN_PRES_VOTES = 50         # drop tiny precincts whose roll-off ratio is pure noise


# ---- pure-stdlib stats (this script stays duckdb + stdlib, like diag_wa_rolloff_2024) ----
def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sx = sum((x - mx) ** 2 for x in xs) ** 0.5
    sy = sum((y - my) ** 2 for y in ys) ** 0.5
    return cov / (sx * sy) if sx and sy else float("nan")


def weighted_pearson(xs, ys, ws):
    sw = sum(ws)
    mx = sum(w * x for w, x in zip(ws, xs)) / sw
    my = sum(w * y for w, y in zip(ws, ys)) / sw
    cov = sum(w * (x - mx) * (y - my) for w, x, y in zip(ws, xs, ys))
    vx = sum(w * (x - mx) ** 2 for w, x in zip(ws, xs))
    vy = sum(w * (y - my) ** 2 for w, y in zip(ws, ys))
    return cov / (vx * vy) ** 0.5 if vx and vy else float("nan")


def zscore(col):
    m = sum(col) / len(col)
    s = (sum((c - m) ** 2 for c in col) / len(col)) ** 0.5
    return [(c - m) / s for c in col] if s else [0.0] * len(col)


def _solve(A, b):
    """Solve A x = b (A square) by Gaussian elimination with partial pivoting."""
    n = len(A)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(M[r][col]))
        M[col], M[piv] = M[piv], M[col]
        if abs(M[col][col]) < 1e-12:
            return None  # singular
        for r in range(n):
            if r != col:
                f = M[r][col] / M[col][col]
                for c in range(col, n + 1):
                    M[r][c] -= f * M[col][c]
    return [M[i][n] / M[i][i] for i in range(n)]


def _ols_resid(y, cols):
    """Residuals of y regressed on [intercept + standardized cols], via normal
    equations. Covariates are z-scored so X'X stays well-conditioned; residuals are
    invariant to that rescaling."""
    n = len(y)
    Z = [zscore(c) for c in cols]
    X = [[1.0] + [Z[j][i] for j in range(len(Z))] for i in range(n)]
    k = len(cols) + 1
    XtX = [[sum(X[i][a] * X[i][b] for i in range(n)) for b in range(k)] for a in range(k)]
    Xty = [sum(X[i][a] * y[i] for i in range(n)) for a in range(k)]
    beta = _solve(XtX, Xty)
    if beta is None:
        return None
    return [y[i] - sum(beta[a] * X[i][a] for a in range(k)) for i in range(n)]


def partial_corr(y, x, cols):
    """Partial correlation of y and x controlling for the columns of `cols`, via
    residual-on-residual Pearson."""
    ry, rx = _ols_resid(y, cols), _ols_resid(x, cols)
    if ry is None or rx is None:
        return None
    return pearson(rx, ry)


def load_precincts(con, contested_race):
    """One row per precinct: roll-off + ACS resident demographics, filtered to precincts
    with President votes >= MIN_PRES_VOTES, the contested contest present, and usable
    demographics. Numerics cast to DOUBLE (DuckDB returns Decimal otherwise)."""
    return con.execute(
        """
        WITH pres AS (
            SELECT precinct_id, SUM(votes) v FROM precinct_results
            WHERE election_id = ? AND race_id = ? GROUP BY 1),
        con AS (
            SELECT precinct_id, SUM(votes) v FROM precinct_results
            WHERE election_id = ? AND race_id = ? GROUP BY 1)
        SELECT pres.precinct_id,
               CAST(1 - con.v * 1.0 / pres.v AS DOUBLE)   AS rolloff,
               CAST(pres.v AS DOUBLE)                     AS pres_votes,
               CAST(d.pct_over_65 AS DOUBLE), CAST(d.pct_under_30 AS DOUBLE),
               CAST(d.median_age AS DOUBLE), CAST(d.median_income AS DOUBLE),
               CAST(d.pct_college_degree AS DOUBLE), CAST(d.median_home_value AS DOUBLE),
               CAST(d.pct_renter AS DOUBLE), CAST(d.total_population AS DOUBLE)
        FROM pres
        JOIN con USING (precinct_id)
        JOIN precinct_demographics d ON d.precinct_id = pres.precinct_id
        WHERE pres.v >= ?
          AND d.pct_over_65 IS NOT NULL AND d.total_population > 0
          AND d.median_income IS NOT NULL AND d.pct_college_degree IS NOT NULL
          AND d.median_home_value IS NOT NULL AND d.pct_renter IS NOT NULL
        """,
        [ELECTION_ID, PRES_RACE, ELECTION_ID, contested_race, MIN_PRES_VOTES],
    ).fetchall()


def electorate_65plus_by_precinct(con):
    """Electorate 65+ share per precinct: distinct VRDB voters who cast a 2024-general
    ballot, mapped to precinct_id via vrdb_precinct_crosswalk. Mirrors the county cut's
    predictor at precinct resolution. Returns {precinct_id: (share_65plus, n_voters)}."""
    con.execute(f"ATTACH IF NOT EXISTS '{VRDB}' AS vrdb (READ_ONLY)")
    rows = con.execute(
        """
        WITH voted AS (
            SELECT DISTINCT state_voter_id FROM vrdb.voting_history
            WHERE election_date = DATE '2024-11-05'),
        v AS (
            SELECT vo.county_name, vo.precinct_code, vo.birthdate
            FROM voted vt JOIN vrdb.voters vo USING (state_voter_id)
            WHERE vo.birthdate IS NOT NULL
              AND (2024 - EXTRACT(year FROM vo.birthdate)) >= 18)
        SELECT x.precinct_id,
               SUM(CASE WHEN (2024 - EXTRACT(year FROM v.birthdate)) >= 65 THEN 1 ELSE 0 END)
                   * 1.0 / COUNT(*)                       AS s65,
               COUNT(*)                                    AS n_voters
        FROM v
        JOIN vrdb_precinct_crosswalk x
          ON UPPER(TRIM(v.county_name)) = UPPER(TRIM(x.county_name))
         AND UPPER(TRIM(v.precinct_code)) = UPPER(TRIM(x.vrdb_precinct_code))
        GROUP BY 1
        """
    ).fetchall()
    return {pid: (float(s65), int(n)) for pid, s65, n in rows}


def report_contest(con, race_id, label):
    rows = load_precincts(con, race_id)
    n = len(rows)
    (_, rolloff, pres_v, over65, under30, med_age,
     income, college, homeval, renter, pop) = zip(*rows)
    rolloff, pres_v = list(rolloff), list(pres_v)

    unw = sum(rolloff) / n * 100
    wtd = sum(r * p for r, p in zip(rolloff, pres_v)) / sum(pres_v) * 100
    print(f"\n=== {label} ===")
    print(f"  precincts (pres >= {MIN_PRES_VOTES} votes, w/ demographics): {n:,}")
    print(f"  roll-off  precinct-mean {unw:5.1f}%   ballot-weighted {wtd:5.1f}%   "
          f"(statewide Appendix F: ~17% contested)")

    print("  raw Pearson r (roll-off vs ...):")
    for name, col in [("ACS resident 65+ %", over65), ("ACS resident <30 %", under30),
                      ("ACS median age", med_age)]:
        r = pearson(list(col), rolloff)
        rw = weighted_pearson(list(col), rolloff, pres_v)
        print(f"    {name:22} r = {r:+.2f}   (ballot-weighted {rw:+.2f})   "
              f"{'older rolls off MORE' if r > 0 else 'younger rolls off MORE'}")

    controls = [list(income), list(college), list(homeval), list(renter),
                [math.log(p) for p in pop]]
    pc65 = partial_corr(rolloff, list(over65), controls)
    pc_age = partial_corr(rolloff, list(med_age), controls)
    print("  partial r controlling for income+education+home value+renter share+log(pop):")
    print(f"    roll-off vs 65+ %    partial r = {pc65:+.2f}")
    print(f"    roll-off vs med age  partial r = {pc_age:+.2f}")
    print("    (if these collapse toward 0 the county age signal was mostly urbanicity;")
    print("     if they stay positive, older places skip the contest even net of SES)")


def report_electorate_age(con, race_id, label):
    """Headline correlation using the ELECTORATE'S 65+ share (VRDB via crosswalk), the
    apples-to-apples upgrade of the county cut, which also used electorate 65+ share."""
    res = load_precincts(con, race_id)
    e65 = electorate_65plus_by_precinct(con)
    MIN_VOTERS = 100
    xs, ys, ws = [], [], []
    for row in res:
        pid, rolloff, pres_v = row[0], row[1], row[2]
        if pid in e65 and e65[pid][1] >= MIN_VOTERS:
            xs.append(e65[pid][0]); ys.append(rolloff); ws.append(pres_v)
    if len(xs) < 100:
        print(f"\n[electorate-age] {label}: only {len(xs)} precincts matched crosswalk — "
              "check county/precinct code normalization before trusting.")
        return
    r = pearson(xs, ys)
    rw = weighted_pearson(xs, ys, ws)
    print(f"\n[electorate-age] {label} — roll-off vs precinct ELECTORATE 65+ share "
          f"({len(xs):,} precincts, >= {MIN_VOTERS} voters):")
    print(f"    Pearson r = {r:+.2f}   (ballot-weighted {rw:+.2f})   "
          f"[county cut was r ~= +0.6 on this same predictor]")


def main():
    con = duckdb.connect(DB, read_only=True)
    print(f"WA 2024 general (election_id={ELECTION_ID}) — PRECINCT-LEVEL ecological roll-off")
    print("Roll-off = 1 - contested-nonpartisan votes / President votes, within precinct.")
    for race_id, label in CONTESTED:
        report_contest(con, race_id, label)
    report_electorate_age(con, CONTESTED[0][0], CONTESTED[0][1])
    con.close()
    print("\nECOLOGICAL — precinct associations do not establish individual behavior; "
          "ballot secrecy makes roll-off-by-age unmeasurable at the individual level.")


if __name__ == "__main__":
    main()
