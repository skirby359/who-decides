"""NY donor follow-ons enabled by the voter file + recipient-party backfill:

A. In-state vs out-of-state money to NY federal candidates, split by RECIPIENT
   PARTY and office. Prior work (cross-state-fec-money.md §C/D/G) measured the
   in/out split by competitiveness/sector but NOT by recipient party. With the
   committee->party backfill we can now ask: are NY Democrats more
   nationally-funded than NY Republicans? Uses data/fec_inflow.duckdb
   (all-state donors -> NY H+S candidates) joined to the committee->party map.

B. In-state donor geographic concentration (NY analog of WA's "61% of
   matched-donor $ from two Seattle ZIP3s"). Uses the 308K matched donors'
   registration ZIP3 / county.

C. Giving <-> turnout stacking (replicates WA §F3 for NY): are matched donors
   super-voters? Uses the normalized voter_participation table.

Usage:
    STATE=NY python scripts/diag_ny_donor_extras.py
"""
import duckdb

NY_STATEWIDE = "data/ny_statewide.duckdb"
NY_VRDB = "data/ny_vrdb.duckdb"
INFLOW = "data/fec_inflow.duckdb"


def section_a() -> None:
    print("=" * 74)
    print("A. IN-STATE vs OUT-OF-STATE money to NY federal candidates, by party")
    print("=" * 74)
    con = duckdb.connect(INFLOW, read_only=True)
    con.execute(f"ATTACH '{NY_STATEWIDE}' AS ny (READ_ONLY)")
    # committee -> party from the backfilled candidate_finance (committee-keyed)
    # + conduit overrides.
    rows = con.execute("""
        WITH cf AS (SELECT fec_candidate_id, ANY_VALUE(party) p
                    FROM ny.candidate_finance GROUP BY 1),
        recip AS (
            SELECT i.*,
                   COALESCE(ov.party, cf.p, 'Unknown') AS recip_party,
                   CASE WHEN i.contributor_state='NY' THEN 'in-state' ELSE 'out-of-state' END AS origin
            FROM inflow_contributions i
            LEFT JOIN cf ON cf.fec_candidate_id = i.cmte_id
            LEFT JOIN ny.committee_party_override ov ON ov.fec_candidate_id = i.cmte_id
            WHERE i.recipient_state='NY'
        )
        SELECT recip_party, origin,
               round(sum(contribution_amount)/1e6,1) usd_m
        FROM recip WHERE recip_party IN ('Democratic','Republican')
        GROUP BY 1,2 ORDER BY 1,2
    """).fetchall()
    agg = {}
    for party, origin, m in rows:
        agg.setdefault(party, {})[origin] = m
    print(f"  {'recipient party':16} {'in-state $M':>12} {'out-state $M':>13} {'out-of-state %':>15}")
    print("  " + "-" * 58)
    for party in ("Democratic", "Republican"):
        d = agg.get(party, {})
        ins = d.get("in-state", 0.0)
        out = d.get("out-of-state", 0.0)
        tot = ins + out
        pct = 100.0 * out / tot if tot else float("nan")
        print(f"  {party:16} {ins:>12.1f} {out:>13.1f} {pct:>14.1f}%")
    # By office too (Senate vs House).
    print("\n  -- out-of-state share by recipient office x party --")
    orows = con.execute("""
        WITH cf AS (SELECT fec_candidate_id, ANY_VALUE(party) p FROM ny.candidate_finance GROUP BY 1)
        SELECT i.recipient_office,
               COALESCE(ov.party, cf.p, 'Unknown') recip_party,
               100.0*sum(CASE WHEN i.contributor_state<>'NY' THEN i.contribution_amount ELSE 0 END)
                    /sum(i.contribution_amount) out_pct,
               round(sum(i.contribution_amount)/1e6,1) total_m
        FROM inflow_contributions i
        LEFT JOIN cf ON cf.fec_candidate_id=i.cmte_id
        LEFT JOIN ny.committee_party_override ov ON ov.fec_candidate_id=i.cmte_id
        WHERE i.recipient_state='NY'
        GROUP BY 1,2 HAVING recip_party IN ('Democratic','Republican') AND total_m > 1
        ORDER BY 1,2
    """).fetchall()
    print(f"  {'office':8} {'party':12} {'out-of-state %':>15} {'total $M':>10}")
    for office, party, outp, totm in orows:
        print(f"  {office:8} {party:12} {outp:>14.1f}% {totm:>9.1f}")
    con.close()


def section_b() -> None:
    print("\n" + "=" * 74)
    print("B. IN-STATE DONOR GEOGRAPHIC CONCENTRATION (matched NY donors)")
    print("=" * 74)
    con = duckdb.connect(NY_STATEWIDE, read_only=True)
    con.execute(f"ATTACH '{NY_VRDB}' AS vrdb (READ_ONLY)")
    print("  -- top 8 counties by matched-donor dollars --")
    rows = con.execute("""
        SELECT v.county_name,
               count(*) donors,
               round(sum(vda.total_donated)/1e6,1) m,
               100.0*sum(vda.total_donated)/sum(sum(vda.total_donated)) OVER () pct
        FROM voter_donor_affiliation vda JOIN vrdb.voters v USING (state_voter_id)
        GROUP BY 1 ORDER BY m DESC LIMIT 8
    """).fetchall()
    print(f"  {'county':16} {'donors':>9} {'$ (M)':>9} {'$ %':>7}")
    for c, d, m, p in rows:
        print(f"  {c:16} {d:>9,} {m:>8.1f} {p:6.1f}%")
    # ZIP3 concentration (WA analog).
    z = con.execute("""
        WITH g AS (
            SELECT SUBSTR(v.reg_zip,1,3) z3, sum(vda.total_donated) amt
            FROM voter_donor_affiliation vda JOIN vrdb.voters v USING (state_voter_id)
            WHERE v.reg_zip IS NOT NULL GROUP BY 1
        )
        SELECT z3, round(amt/1e6,1) m, 100.0*amt/sum(amt) OVER () pct,
               100.0*sum(amt) OVER (ORDER BY amt DESC ROWS UNBOUNDED PRECEDING)/sum(amt) OVER () cum
        FROM g ORDER BY amt DESC LIMIT 6
    """).fetchall()
    print("\n  -- top 6 ZIP3s by matched-donor dollars (WA analog: 2 ZIP3s = 61%) --")
    print(f"  {'ZIP3':6} {'$ (M)':>9} {'$ %':>7} {'cumulative %':>13}")
    for z3, m, pct, cum in z:
        print(f"  {z3:6} {m:>8.1f} {pct:6.1f}% {cum:12.1f}%")
    con.close()


def section_c() -> None:
    print("\n" + "=" * 74)
    print("C. GIVING <-> TURNOUT STACKING (NY; replicates WA F3)")
    print("=" * 74)
    con = duckdb.connect(NY_STATEWIDE, read_only=True)
    con.execute(f"ATTACH '{NY_VRDB}' AS vrdb (READ_ONLY)")
    # super-voter = voted in >=3 of the last 4 federal generals (2018-2024).
    row = con.execute("""
        WITH gen AS (
            SELECT state_voter_id, count(DISTINCT election_year) ngen
            FROM vrdb.voter_participation
            WHERE kind='GENERAL' AND election_year IN (2018,2020,2022,2024)
            GROUP BY 1
        ),
        roll AS (
            SELECT v.state_voter_id,
                   COALESCE(g.ngen,0) AS ngen,
                   (vda.state_voter_id IS NOT NULL) AS is_donor
            FROM vrdb.voters v
            LEFT JOIN gen g USING (state_voter_id)
            LEFT JOIN voter_donor_affiliation vda USING (state_voter_id)
            WHERE v.status_code='A'
        )
        SELECT is_donor,
               count(*) n,
               100.0*count(*) FILTER(WHERE ngen>=3)/count(*) super_pct,
               round(avg(ngen),2) avg_gen
        FROM roll GROUP BY is_donor ORDER BY is_donor
    """).fetchall()
    print(f"  {'group':14} {'voters':>11} {'super-voter %':>14} {'avg generals (of 4)':>21}")
    for is_donor, n, sp, ag in row:
        label = "matched donors" if is_donor else "non-donors"
        print(f"  {label:14} {n:>11,} {sp:>13.1f}% {ag:>20.2f}")
    con.close()


def main() -> int:
    section_a()
    section_b()
    section_c()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
