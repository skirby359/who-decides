"""Single-year-of-age turnout and off-year retention curve (Appendix H).

The paper's body reports composition in Census-style age bands. This script
drops the banding entirely: for every single year of age 18-95 it computes,
from the WA voter file (data/wa_vrdb.duckdb: voters + voting_history),

  * 2024 presidential-general participation (current-roll reconstruction),
  * 2025 off-year participation (same basis),
  * off-year RETENTION = P(voted Nov 2025 | voted Nov 2024) — the headline
    measure, least sensitive to the current-roll denominator because both
    events are read off the same roll,
  * each age's share of the 2024 and 2025 electorates.

Age = 2025 - birth year (the paper's convention; the file carries year of
birth only). The finding the appendix reports: the gradient is a smooth,
monotone age ramp — retention climbs from ~23% at age 20 to a ~71% plateau
at ages 74-82 with NO discontinuity at 65, a first-election bump at 18-20
followed by the classic early-20s trough, and a decline from ~84 — so no
banding choice manufactures or hides the composition result, and no
data-driven clustering would find natural cohort breakpoints. Consistent
with (though not proof of) a life-cycle interpretation; age, cohort, and
period effects are not separable in a five-cycle panel.

Standalone: duckdb + stdlib. Run from the repo root with data/ populated.
Writes reports/wa_age_curve.json. Verified by verify_who_decides_wa.py #30.
"""
import json

import duckdb

DB = "data/wa_vrdb.duckdb"
OUT = "reports/wa_age_curve.json"
D24, D25 = "2024-11-05", "2025-11-04"


def main():
    c = duckdb.connect(DB, read_only=True)
    rows = c.execute(f"""
        WITH v24 AS (SELECT DISTINCT state_voter_id FROM voting_history
                     WHERE election_date = '{D24}'),
             v25 AS (SELECT DISTINCT state_voter_id FROM voting_history
                     WHERE election_date = '{D25}'),
        base AS (
            SELECT 2025 - YEAR(v.birthdate) AS age,
                   (a.state_voter_id IS NOT NULL) AS voted24,
                   (b.state_voter_id IS NOT NULL) AS voted25
            FROM voters v
            LEFT JOIN v24 a USING (state_voter_id)
            LEFT JOIN v25 b USING (state_voter_id)
            WHERE v.birthdate IS NOT NULL
        )
        SELECT age, COUNT(*) n_roll,
               SUM(CASE WHEN voted24 THEN 1 ELSE 0 END) n24,
               SUM(CASE WHEN voted25 THEN 1 ELSE 0 END) n25,
               SUM(CASE WHEN voted24 AND voted25 THEN 1 ELSE 0 END) n_both
        FROM base WHERE age BETWEEN 18 AND 95
        GROUP BY 1 ORDER BY 1
    """).fetchall()
    c.close()

    tot24 = sum(r[2] for r in rows)
    tot25 = sum(r[3] for r in rows)
    out = {}
    print(f"{'age':>4} {'roll':>9} {'t2024%':>7} {'t2025%':>7} {'ret%':>6} "
          f"{'sh24%':>6} {'sh25%':>6}")
    for age, n, n24, n25, nb in rows:
        rec = {
            "roll": n,
            "turnout_2024": round(n24 / n * 100, 1) if n else None,
            "turnout_2025": round(n25 / n * 100, 1) if n else None,
            "retention": round(nb / n24 * 100, 1) if n24 else None,
            "share_2024": round(n24 / tot24 * 100, 2),
            "share_2025": round(n25 / tot25 * 100, 2),
        }
        out[age] = rec
        print(f"{age:>4} {n:>9,} {rec['turnout_2024']:>7} {rec['turnout_2025']:>7} "
              f"{str(rec['retention']):>6} {rec['share_2024']:>6} {rec['share_2025']:>6}")

    # Structural reads the appendix reports. Ages 18-19 are excluded from the
    # peak search: an 18-year-old in Nov 2025 was 17 at the Nov 2024 general,
    # so that cell's "retention" is a near-empty-denominator artifact.
    ret = {a: r["retention"] for a, r in out.items()
           if r["retention"] is not None and a >= 20}
    plateau = max(ret, key=ret.get)
    print(f"\npeak retention: age {plateau} at {ret[plateau]}%")
    print(f"no-65-discontinuity check: ret(64)={ret[64]}%  ret(66)={ret[66]}%  "
          f"step {abs(ret[66]-ret[64]):.1f}pt (vs 60->64 step {abs(ret[64]-ret[60]):.1f}pt)")
    json.dump(out, open(OUT, "w"), indent=2)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
