"""WA even-year (2024 general) contest-level ROLL-OFF — the sequel the reviewer of
`docs/who-decides-washington.md` requested (open-data #5).

Question: if local nonpartisan races were consolidated onto even-year November
ballots, how many voters who return a ballot would skip the local contest? We
estimate it directly from certified 2024 precinct returns (data/wa_statewide.duckdb,
election_id=2), measuring roll-off = (ballots counted - votes cast in a contest) /
ballots counted, for statewide contests grouped by type. Even-year NONPARTISAN
judicial contests are the closest available analog to the local nonpartisan races
(city council, school board) that consolidation would add.

Excluded, by construction:
  - Court of Appeals: regional (only one division votes), so roll-off vs the STATEWIDE
    ballot count is not meaningful.
  - Lt. Governor: loaded in only 5,355 of 8,111 precincts (38 of 39 counties) — a
    partial-load artifact, not roll-off — so it is dropped rather than reported as ~32%.

Read-only, aggregates only. Run from the project root:
    python scripts/diag_wa_rolloff_2024.py
"""
import duckdb

DB = "data/wa_statewide.duckdb"
VRDB = "data/wa_vrdb.duckdb"
BALLOTS = 3_961_569  # official certified 2024 general ballots counted (WA SoS)

# (label, group, race_name match) — curated statewide contests
CONTESTS = [
    ("President", "top of ticket", "PRESIDENT/VICE PRESIDENT"),
    ("Governor", "partisan statewide", "GOVERNOR"),
    ("U.S. Senator", "partisan statewide", "U.S. SENATOR"),
    ("Attorney General", "partisan statewide", "ATTORNEY GENERAL"),
    ("Secretary of State", "partisan statewide", "SECRETARY OF STATE"),
    ("Commissioner of Public Lands", "partisan statewide", "COMMISSIONER OF PUBLIC LANDS"),
    ("Insurance Commissioner", "partisan statewide", "INSURANCE COMMISSIONER"),
    ("Initiative 2109", "ballot measure", "INITIATIVE MEASURE NO. 2109"),
    ("Initiative 2124", "ballot measure", "INITIATIVE MEASURE NO. 2124"),
    ("Supt. of Public Instruction (nonpartisan, contested)", "nonpartisan contested",
     "SUPERINTENDENT OF PUBLIC INSTRUCTION"),
    ("Supreme Court Justice Pos. 2 (nonpartisan, contested)", "nonpartisan contested",
     "SUPREME COURT - JUSTICE POSITION #02"),
    ("Supreme Court Justice Pos. 8 (nonpartisan, uncontested)", "nonpartisan uncontested",
     "SUPREME COURT - JUSTICE POSITION #08"),
    ("Supreme Court Justice Pos. 9 (nonpartisan, uncontested)", "nonpartisan uncontested",
     "SUPREME COURT - JUSTICE POSITION #09"),
]


def main():
    con = duckdb.connect(DB, read_only=True)
    print(f"2024 general — official ballots counted: {BALLOTS:,}\n")
    print(f"{'contest':56}{'group':24}{'votes':>11}{'roll-off':>10}")
    by_group = {}
    for label, group, match in CONTESTS:
        tot = con.execute(
            "SELECT SUM(pr.votes) FROM precinct_results pr JOIN races r USING (race_id) "
            "WHERE pr.election_id=2 AND r.race_name = ?", [match]).fetchone()[0]
        ro = (BALLOTS - tot) / BALLOTS * 100
        by_group.setdefault(group, []).append(ro)
        print(f"{label:56}{group:24}{tot:>11,}{ro:>9.1f}%")
    con.close()

    print("\nRoll-off by contest type (range):")
    for g in ["top of ticket", "partisan statewide", "ballot measure",
              "nonpartisan contested", "nonpartisan uncontested"]:
        v = by_group.get(g, [])
        if v:
            print(f"  {g:26} {min(v):.1f}%–{max(v):.1f}%")

    # Net-enlargement arithmetic: does consolidation still enlarge the deciding
    # electorate even at the observed even-year roll-off?
    OFF = 37.0   # ~off-year turnout, % of registered (2021/23/25)
    EVEN = 79.0  # ~2024 even-year turnout, % of registered
    print(f"\nNet enlargement — share of REGISTERED voters casting a vote in the local contest:")
    print(f"  off-year (local at top of a short ballot):            ~{OFF:.0f}%")
    for r, lab in [(0.05, "partisan-office roll-off"), (0.17, "contested nonpartisan"),
                   (0.34, "uncontested nonpartisan (worst observed)")]:
        even_local = EVEN * (1 - r)
        print(f"  even-year at {r*100:.0f}% roll-off ({lab:38}): ~{even_local:.0f}%  "
              f"({'still > off-year' if even_local > OFF else 'BELOW off-year'})")

    county_rolloff_vs_age()


def county_rolloff_vs_age():
    """Ecological: does even-year roll-off skew young? County-level roll-off for the
    contested statewide nonpartisan contest (President vs Supreme Court Pos. 2) vs each
    county's electorate 65+ share. Cross-DB: 2024 returns from wa_statewide, ages from
    the VRDB (ATTACHed). County-level avoids the precinct-crosswalk gap (all 39 join).
    NOTE: cast-vote records are ballot-anonymous (no voter age), so a roll-off age
    profile can only ever be ECOLOGICAL — this correlation is the ceiling, not a proxy
    for an individual-level measurement that secret-ballot rules make impossible."""
    con = duckdb.connect(DB, read_only=True)
    con.execute(f"ATTACH '{VRDB}' AS vrdb (READ_ONLY)")
    rows = con.execute("""
        WITH pr AS (
            SELECT UPPER(p.county_name) cty,
                   SUM(CASE WHEN r.race_name='PRESIDENT/VICE PRESIDENT' THEN pr.votes ELSE 0 END) pres,
                   SUM(CASE WHEN r.race_name='SUPREME COURT - JUSTICE POSITION #02' THEN pr.votes ELSE 0 END) sc
            FROM precinct_results pr JOIN races r USING (race_id)
            JOIN precincts p ON p.precinct_id = pr.precinct_id
            WHERE pr.election_id = 2 GROUP BY 1),
        age AS (
            SELECT UPPER(v.county_name) cty,
                   SUM(CASE WHEN (2024-EXTRACT(year FROM v.birthdate))>=65 THEN 1 ELSE 0 END)*1.0/COUNT(*) s65
            FROM (SELECT DISTINCT state_voter_id FROM vrdb.voting_history
                  WHERE election_date=DATE '2024-11-05') h
            JOIN vrdb.voters v USING (state_voter_id)
            WHERE v.birthdate IS NOT NULL AND (2024-EXTRACT(year FROM v.birthdate))>=18 GROUP BY 1)
        SELECT pr.cty, (1 - pr.sc*1.0/pr.pres) rolloff, age.s65
        FROM pr JOIN age USING (cty) WHERE pr.pres > 0""").fetchall()
    con.close()
    xs = [r[2] for r in rows]; ys = [r[1] for r in rows]; n = len(xs)
    mx, my = sum(xs)/n, sum(ys)/n
    cov = sum((x-mx)*(y-my) for x, y in zip(xs, ys))
    sx = sum((x-mx)**2 for x in xs)**0.5; sy = sum((y-my)**2 for y in ys)**0.5
    r = cov/(sx*sy)
    print(f"\n[ecological] COUNTY roll-off (Pres vs Supreme Court Pos.2) vs county 65+ share, "
          f"{n} counties:")
    print(f"  Pearson r = {r:+.2f}  (negative = younger counties roll off MORE)")
    print(f"  county roll-off range {min(ys)*100:.1f}%-{max(ys)*100:.1f}%; "
          f"65+ share range {min(xs)*100:.1f}%-{max(xs)*100:.1f}%")


if __name__ == "__main__":
    main()
