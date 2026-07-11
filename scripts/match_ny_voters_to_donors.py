"""Match NY voters to FEC donors, then characterize the donor class by the
voter's OWN party-of-record + age (electoral-health: donor class != electorate).

Reuses the battle-tested WA matcher `match_voters_to_donors` (4-tier:
full-name+zip5 / first-initial+middle+zip5 / first-initial+zip5 /
zip3+middle; per-tier uniqueness guard; the conduit-PAC override join). We do
NOT reimplement it — we just point it at the NY data:
  - voters  : data/ny_vrdb.duckdb        ATTACHed AS vrdb   (13.54M; party + DOB)
  - donors  : data/ny_statewide.duckdb   individual_contributions (10.02M FEC rows)
  - output  : ny_statewide.duckdb         voter_donor_affiliation

RECIPIENT-PARTY caveat: NY's candidate_finance.party is ~96% Unknown and
committee_party_override is empty (the FEC committee-master / conduit-override
loads were never run for NY), and individual_contributions.fec_candidate_id is
a *committee* id. So `donation_lean` / `donor_party` (which recipient the money
went to) is NOT meaningful here yet — that needs an FEC committee->party
backfill (follow-on). What IS meaningful and is the point of this analysis: the
MATCH itself (which registered NY voters are federal donors), characterized by
their own NY party enrollment and age.

Usage (the script bootstraps sys.path itself, so no PYTHONPATH needed):
    STATE=NY python scripts/match_ny_voters_to_donors.py
"""
import os
import sys

import duckdb

os.environ.setdefault("STATE", "NY")
# wa_analyzer lives under src/, config/ at repo root — put both on the path so
# this runs regardless of PYTHONPATH (config.* is imported transitively).
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "src"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from wa_analyzer.analysis.donor_analysis import match_voters_to_donors  # noqa: E402

NY_STATEWIDE = "data/ny_statewide.duckdb"
NY_VRDB = "data/ny_vrdb.duckdb"

PARTY_CASE = """
    CASE WHEN v.party='DEM' THEN 'DEM' WHEN v.party='REP' THEN 'REP'
         WHEN v.party='BLK' THEN 'NOPARTY' ELSE 'OTHER' END
"""


def main() -> int:
    con = duckdb.connect(NY_STATEWIDE)  # read-write: writes voter_donor_affiliation
    con.execute(f"ATTACH '{NY_VRDB}' AS vrdb (READ_ONLY)")

    print("[match] running 4-tier voter<->donor match (NY)...")
    res = match_voters_to_donors(con)
    if res.get("skipped"):
        print("  SKIPPED:", res.get("reason"))
        return 1
    print(f"  matched voters       : {res['matched_voters']:,}")
    print(f"  contributions matched: {res['contributions_matched']:,}")
    print("  match-quality tiers  :")
    for q, n in con.execute("""
        SELECT match_quality, count(*) FROM voter_donor_affiliation
        GROUP BY 1 ORDER BY 2 DESC
    """).fetchall():
        print(f"    {q:18} {n:>10,}")

    # ---- Donor class vs electorate, by the voter's OWN party-of-record ----
    print("\n=== DONOR CLASS vs ELECTORATE — by NY party-of-record ===")
    rows = con.execute(f"""
        WITH d AS (
            SELECT {PARTY_CASE} AS party, vda.total_donated
            FROM voter_donor_affiliation vda JOIN vrdb.voters v USING (state_voter_id)
        )
        SELECT party, count(*) donors,
               100.0*count(*)/sum(count(*)) OVER () donor_share_pct,
               round(sum(total_donated)/1e6,1) total_m,
               100.0*sum(total_donated)/sum(sum(total_donated)) OVER () dollar_share_pct
        FROM d GROUP BY party ORDER BY donors DESC
    """).fetchall()
    reg = dict(con.execute(f"""
        SELECT {PARTY_CASE} AS party, 100.0*count(*)/sum(count(*)) OVER () FROM vrdb.voters v GROUP BY party
    """).fetchall())
    print(f"  {'party':8} {'donors':>10} {'donor%':>8} {'reg%':>7} {'skew':>6} {'$ (M)':>9} {'$ %':>7}")
    print("  " + "-" * 62)
    for party, donors, dshare, totm, dollar in rows:
        r = reg.get(party, float("nan"))
        skew = dshare - r
        print(f"  {party:8} {donors:>10,} {dshare:7.1f}% {r:6.1f}% {skew:+5.1f} {totm:>8.1f} {dollar:6.1f}%")

    # ---- Donor age skew vs the electorate (2024 general voters) ----
    print("\n=== DONOR AGE SKEW vs 2024 general electorate ===")
    print("  age-band share among: matched donors  |  all active voters  |  2024 GE voters")
    age_rows = con.execute("""
        WITH donors AS (
            SELECT v.state_voter_id,
                   date_diff('year', v.birthdate, DATE '2024-11-05') AS age
            FROM voter_donor_affiliation vda JOIN vrdb.voters v USING (state_voter_id)
            WHERE v.birthdate IS NOT NULL
        ),
        allv AS (
            SELECT date_diff('year', v.birthdate, DATE '2024-11-05') AS age
            FROM vrdb.voters v WHERE v.status_code='A' AND v.birthdate IS NOT NULL
        ),
        ge24 AS (
            SELECT date_diff('year', v.birthdate, DATE '2024-11-05') AS age
            FROM vrdb.voter_participation p JOIN vrdb.voters v USING (state_voter_id)
            WHERE p.election_year=2024 AND p.kind='GENERAL' AND v.birthdate IS NOT NULL
        ),
        band AS (
            SELECT 'donors' src, CASE WHEN age BETWEEN 18 AND 29 THEN '18-29'
                WHEN age BETWEEN 30 AND 44 THEN '30-44' WHEN age BETWEEN 45 AND 64 THEN '45-64'
                WHEN age BETWEEN 65 AND 105 THEN '65+' END b FROM donors
            UNION ALL SELECT 'allv', CASE WHEN age BETWEEN 18 AND 29 THEN '18-29'
                WHEN age BETWEEN 30 AND 44 THEN '30-44' WHEN age BETWEEN 45 AND 64 THEN '45-64'
                WHEN age BETWEEN 65 AND 105 THEN '65+' END FROM allv
            UNION ALL SELECT 'ge24', CASE WHEN age BETWEEN 18 AND 29 THEN '18-29'
                WHEN age BETWEEN 30 AND 44 THEN '30-44' WHEN age BETWEEN 45 AND 64 THEN '45-64'
                WHEN age BETWEEN 65 AND 105 THEN '65+' END FROM ge24
        )
        SELECT b,
            100.0*count(*) FILTER(WHERE src='donors')/sum(count(*) FILTER(WHERE src='donors')) OVER (),
            100.0*count(*) FILTER(WHERE src='allv')/sum(count(*) FILTER(WHERE src='allv')) OVER (),
            100.0*count(*) FILTER(WHERE src='ge24')/sum(count(*) FILTER(WHERE src='ge24')) OVER ()
        FROM band WHERE b IS NOT NULL GROUP BY b ORDER BY b
    """).fetchall()
    print(f"  {'band':8} {'donors':>9} {'allvoters':>10} {'2024GE':>9}")
    for b, dn, av, ge in age_rows:
        print(f"  {b:8} {dn:8.1f}% {av:9.1f}% {ge:8.1f}%")

    # ---- Donor-dollar concentration (top 1% of matched donors) ----
    print("\n=== DONOR-DOLLAR CONCENTRATION (matched NY donors) ===")
    # Concentration estimator standardized across WA/NY/ID: NTILE(100) equal-count donor
    # buckets over actual donors (total_donated>0). Equal-count buckets are robust to ties;
    # PERCENT_RANK (the prior method) drifts from an exact decile at small N. See
    # docs/donor-class-and-the-electorate.md §F2 note.
    conc = con.execute("""
        WITH r AS (SELECT total_donated t, NTILE(100) OVER (ORDER BY total_donated DESC) p
                   FROM voter_donor_affiliation WHERE total_donated > 0)
        SELECT round(100.0*SUM(t) FILTER(WHERE p=1)/SUM(t),1) top1,
               round(100.0*SUM(t) FILTER(WHERE p<=10)/SUM(t),1) top10
        FROM r
    """).fetchone()
    print(f"  top 1% of matched donors = {conc[0]}% of matched $")
    print(f"  top 10% of matched donors = {conc[1]}% of matched $")

    # ---- Recipient lean x own party (crossover) ----
    # Requires the recipient-party backfill (scripts/backfill_ny_committee_party.py)
    # so donation_lean / donor_party are meaningful. donor_party: D_DONOR (gave
    # only to D recipients), R_DONOR, MIXED (both), OTHER (recipient party
    # unresolved -> no signal).
    print("\n=== RECIPIENT LEAN x OWN PARTY (crossover) ===")
    print("  among donors with a resolved recipient lean, where their $ went:")
    rows = con.execute(f"""
        WITH d AS (
            SELECT {PARTY_CASE} AS own_party, vda.donor_party
            FROM voter_donor_affiliation vda JOIN vrdb.voters v USING (state_voter_id)
        )
        SELECT own_party,
            count(*) FILTER(WHERE donor_party<>'OTHER')                 AS resolved,
            100.0*count(*) FILTER(WHERE donor_party='D_DONOR')/NULLIF(count(*) FILTER(WHERE donor_party<>'OTHER'),0) AS pct_to_D,
            100.0*count(*) FILTER(WHERE donor_party='R_DONOR')/NULLIF(count(*) FILTER(WHERE donor_party<>'OTHER'),0) AS pct_to_R,
            100.0*count(*) FILTER(WHERE donor_party='MIXED')/NULLIF(count(*) FILTER(WHERE donor_party<>'OTHER'),0)   AS pct_mixed
        FROM d GROUP BY own_party ORDER BY resolved DESC
    """).fetchall()
    print(f"  {'own party':10} {'resolved':>9} {'->D':>7} {'->R':>7} {'mixed':>7}")
    print("  " + "-" * 44)
    for op, res_n, pd, pr, pm in rows:
        print(f"  {op:10} {res_n:>9,} {pd or 0:6.1f}% {pr or 0:6.1f}% {pm or 0:6.1f}%")

    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
