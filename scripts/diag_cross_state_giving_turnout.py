"""Cross-state giving -> turnout (F3 replication) on WA-compatible voter_scores.

WA's F3 (donors are far likelier to be super-voters) previously couldn't run
for NY/ID because their voter_scores were empty; populated 2026-07-19 by
scripts/populate_ny_id_voter_scores.py with WA-identical definitions
(is_super_voter = voted 2022+ AND registered >= 8y; turnout_propensity =
the WA step/history blend). This makes the association apples-to-apples in
all three voter-file states.

State-agnostic: runs for every region state whose statewide DB has both
voter_scores and voter_donor_affiliation rows (TX has neither — no voter
file). WA voter_scores holds one row per (voter, scope); the ld-scope is the
complete one (CLAUDE.md), so rows are de-duplicated per voter. NY/ID are
already one-row-per-voter (ad/ld house scope).

Association only — donors are pre-selected for engagement and the matcher
favors stable-address voters; not a causal claim.
"""
import duckdb

from cross_state_common import region_states, write_json


def analyze(st: str, path: str) -> dict | None:
    c = duckdb.connect(path, read_only=True)
    try:
        pfx = {"WA": "ld"}.get(st, "")  # WA needs the ld-scope filter; NY/ID hold one scope
        where = f"WHERE district_id LIKE '{pfx}%'" if pfx else ""
        n_scores = c.execute(f"SELECT COUNT(*) FROM voter_scores {where}").fetchone()[0]
        n_aff = c.execute("SELECT COUNT(*) FROM voter_donor_affiliation").fetchone()[0]
        if not n_scores or not n_aff:
            return None
        rows = c.execute(f"""
            WITH roll AS (
                SELECT DISTINCT state_voter_id, is_super_voter, turnout_propensity, age_cohort
                FROM voter_scores {where}
            ),
            flagged AS (
                SELECT r.*, (a.state_voter_id IS NOT NULL) AS donor
                FROM roll r LEFT JOIN voter_donor_affiliation a USING (state_voter_id)
            )
            SELECT donor, COUNT(*) n,
                   AVG(CASE WHEN is_super_voter THEN 1.0 ELSE 0 END) super_rate,
                   AVG(turnout_propensity) avg_prop
            FROM flagged GROUP BY donor ORDER BY donor
        """).fetchall()
        out = {}
        for donor, n, sr, ap in rows:
            out["donor" if donor else "non_donor"] = dict(
                n=int(n), super_rate=round(float(sr), 4), avg_prop=round(float(ap), 4))
        if "donor" in out and "non_donor" in out and out["non_donor"]["super_rate"]:
            out["super_ratio"] = round(
                out["donor"]["super_rate"] / out["non_donor"]["super_rate"], 2)
        # Donor super-rate by generation (is the engagement gap age-driven?)
        out["donor_super_by_gen"] = {
            g: round(float(sr), 4) for g, sr in c.execute(f"""
                WITH roll AS (
                    SELECT DISTINCT state_voter_id, is_super_voter, age_cohort
                    FROM voter_scores {where}
                )
                SELECT r.age_cohort, AVG(CASE WHEN r.is_super_voter THEN 1.0 ELSE 0 END)
                FROM roll r JOIN voter_donor_affiliation a USING (state_voter_id)
                WHERE r.age_cohort NOT IN ('Unknown') GROUP BY 1
            """).fetchall()}
        return out
    finally:
        c.close()


def main() -> None:
    out = {}
    print(f"{'state':6} {'group':10} {'n':>12} {'super%':>8} {'avg prop':>9}")
    print("-" * 50)
    for st, path in region_states():
        r = analyze(st, path)
        if r is None:
            print(f"{st:6} (no voter_scores / matches — skipped)")
            continue
        out[st] = r
        for grp in ("donor", "non_donor"):
            d = r[grp]
            print(f"{st:6} {grp:10} {d['n']:>12,} {d['super_rate']*100:7.1f}% {d['avg_prop']:9.3f}")
        print(f"{st:6} super-voter ratio donor/non: {r.get('super_ratio')}x")
    path = write_json("cross_state_giving_turnout.json", out)
    print(f"\nwrote {path}")


if __name__ == "__main__":
    main()
