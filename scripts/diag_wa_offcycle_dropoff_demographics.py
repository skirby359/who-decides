"""Does off-cycle drop-off track a precinct's RACE / INCOME / EDUCATION, beyond age? —
an ecological companion to the age finding in `docs/who-decides-washington.md`.

The paper shows the off-year electorate is older, driven by differential turnout. Natural
next question (Kirby): are the precincts that drop off most off-cycle also the more
nonwhite / lower-income / less-college ones — a representation gap on dimensions the voter
file can't see directly? Washington's voter file carries no race, so — unlike age (from
birthdate) — race can ONLY be measured ecologically, from Census geography. This is that
ecological cut, with the same ceiling as Appendix F: a precinct-level association does NOT
establish individual behavior.

Measure: per precinct, off-cycle RETENTION = (distinct voters who cast a 2025 off-year
ballot) / (distinct voters who cast a 2024 presidential ballot), from the VRDB mapped to
precinct_id via vrdb_precinct_crosswalk. Low retention = big off-cycle drop-off. We
correlate retention with ACS precinct demographics, raw and — the key test — controlling
for the precinct's 65+ share, since age is the known driver and the question is whether
race/income/education add anything BEYOND age.

Read-only, aggregates only. Uses ETL-built precinct_demographics + vrdb_precinct_crosswalk
(not raw public data). Run from the project root:
    python scripts/diag_wa_offcycle_dropoff_demographics.py

ECOLOGICAL — precinct associations are not individual behavior; the voter file has no race,
so an individual race-by-turnout measure is impossible in WA at any geography.
"""
import math

import duckdb

DB = "data/wa_statewide.duckdb"
VRDB = "data/wa_vrdb.duckdb"
PRES = "2024-11-05"
OFF = "2025-11-04"          # best-covered recent off-year
MIN_PRES = 100             # precinct presidential electorate large enough for a stable ratio


# ---- pure-stdlib stats (mirrors diag_wa_rolloff_precinct.py) ----
def pearson(xs, ys):
    n = len(xs); mx = sum(xs) / n; my = sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sx = sum((x - mx) ** 2 for x in xs) ** 0.5; sy = sum((y - my) ** 2 for y in ys) ** 0.5
    return cov / (sx * sy) if sx and sy else float("nan")


def zscore(col):
    m = sum(col) / len(col)
    s = (sum((c - m) ** 2 for c in col) / len(col)) ** 0.5
    return [(c - m) / s for c in col] if s else [0.0] * len(col)


def _solve(A, b):
    n = len(A); M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(M[r][col]))
        M[col], M[piv] = M[piv], M[col]
        if abs(M[col][col]) < 1e-12:
            return None
        for r in range(n):
            if r != col:
                f = M[r][col] / M[col][col]
                for cc in range(col, n + 1):
                    M[r][cc] -= f * M[col][cc]
    return [M[i][n] / M[i][i] for i in range(n)]


def _ols_resid(y, cols):
    n = len(y); Z = [zscore(c) for c in cols]
    X = [[1.0] + [Z[j][i] for j in range(len(Z))] for i in range(n)]
    k = len(cols) + 1
    XtX = [[sum(X[i][a] * X[i][b] for i in range(n)) for b in range(k)] for a in range(k)]
    Xty = [sum(X[i][a] * y[i] for i in range(n)) for a in range(k)]
    beta = _solve(XtX, Xty)
    return None if beta is None else [y[i] - sum(beta[a] * X[i][a] for a in range(k)) for i in range(n)]


def partial_corr(y, x, cols):
    ry, rx = _ols_resid(y, cols), _ols_resid(x, cols)
    return None if ry is None or rx is None else pearson(rx, ry)


def load():
    con = duckdb.connect(DB, read_only=True)
    con.execute(f"ATTACH IF NOT EXISTS '{VRDB}' AS vrdb (READ_ONLY)")
    rows = con.execute(f"""
        WITH xw AS (
            SELECT UPPER(TRIM(county_name)) cty, UPPER(TRIM(vrdb_precinct_code)) pc, precinct_id
            FROM vrdb_precinct_crosswalk),
        pres AS (
            SELECT x.precinct_id, COUNT(DISTINCT h.state_voter_id) n
            FROM vrdb.voting_history h
            JOIN vrdb.voters v ON v.state_voter_id = h.state_voter_id
            JOIN xw x ON x.cty = UPPER(TRIM(v.county_name)) AND x.pc = UPPER(TRIM(v.precinct_code))
            WHERE h.election_date = DATE '{PRES}' GROUP BY 1),
        off AS (
            SELECT x.precinct_id, COUNT(DISTINCT h.state_voter_id) n
            FROM vrdb.voting_history h
            JOIN vrdb.voters v ON v.state_voter_id = h.state_voter_id
            JOIN xw x ON x.cty = UPPER(TRIM(v.county_name)) AND x.pc = UPPER(TRIM(v.precinct_code))
            WHERE h.election_date = DATE '{OFF}' GROUP BY 1)
        SELECT pres.precinct_id,
               COALESCE(off.n, 0) * 1.0 / pres.n              AS retention,
               CAST(pres.n AS DOUBLE)                          AS pres_n,
               CAST(d.pct_white AS DOUBLE), CAST(d.pct_hispanic AS DOUBLE),
               CAST(d.pct_college_degree AS DOUBLE), CAST(d.median_income AS DOUBLE),
               CAST(d.pct_over_65 AS DOUBLE)
        FROM pres
        JOIN precinct_demographics d ON d.precinct_id = pres.precinct_id
        LEFT JOIN off ON off.precinct_id = pres.precinct_id
        WHERE pres.n >= {MIN_PRES}
          AND d.pct_white IS NOT NULL AND d.pct_hispanic IS NOT NULL
          AND d.pct_college_degree IS NOT NULL AND d.median_income IS NOT NULL
          AND d.pct_over_65 IS NOT NULL
    """).fetchall()
    con.close()
    return rows


def main():
    rows = load()
    n = len(rows)
    (_, ret, pres_n, white, hisp, college, income, over65) = zip(*rows)
    ret = list(ret)
    print(f"WA off-cycle RETENTION (2025 voters / 2024 presidential voters) vs precinct")
    print(f"demographics — {n:,} precincts (pres >= {MIN_PRES} voters, w/ ACS demographics)")
    print(f"  mean precinct retention {sum(ret)/n*100:.1f}%  (low = larger off-cycle drop-off)\n")

    print("  raw Pearson r (retention vs ...):")
    preds = [("ACS % white", white), ("ACS % hispanic", hisp),
             ("ACS % college", college), ("ACS median income", income),
             ("ACS % 65+", over65)]
    for name, col in preds:
        r = pearson(list(col), ret)
        print(f"    {name:20} r = {r:+.2f}   {'higher retention' if r > 0 else 'lower retention'}")

    print("\n  partial r controlling for the precinct 65+ share (does it add BEYOND age?):")
    age_ctrl = [list(over65)]
    for name, col in [("ACS % white", white), ("ACS % hispanic", hisp),
                      ("ACS % college", college), ("ACS median income", income)]:
        pc = partial_corr(ret, list(col), age_ctrl)
        print(f"    {name:20} partial r = {pc:+.2f}")
    print("    (near 0 => the dimension is mostly the age story; nonzero => an extra")
    print("     race/income/education gap in who keeps voting off-cycle)")

    print("\nECOLOGICAL — precinct associations do not establish individual behavior; WA's")
    print("voter file has no race, so race-by-turnout is unmeasurable at the individual level.")


if __name__ == "__main__":
    main()
