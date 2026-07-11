"""Match Idaho voters to campaign donors, then characterize the donor class by
the voter's OWN party-of-record + age (electoral-health: donor class != electorate).

The deep-RED companion to match_ny_voters_to_donors.py. Reuses the battle-tested
WA matcher `match_voters_to_donors` (Tier 0 full-name+zip5 down to zip3+middle,
per-tier uniqueness guard) unchanged — we just point it at the ID data:
  - voters : data/id_vrdb.duckdb        ATTACHed AS vrdb (1.03M; party + age)
  - donors : data/id_statewide.duckdb   individual_contributions (216.7K rows)
  - output : id_statewide.duckdb         voter_donor_affiliation

DONOR SOURCE: unlike WA/NY (FEC federal individual contributions), the ID
`individual_contributions` are **Idaho Sunshine STATE campaign** donations
(recipient ids are `SUNSHINE:<cand>`), so this characterizes the *state*
donor class — the money behind Idaho legislative/statewide races, which is the
more relevant layer for state electoral health anyway.

Two ID-specific adaptations:
  * Age, not DOB — the age-skew section uses the current-roll `age` column for
    all three cohorts (donors / all voters / 2024 GE voters), a consistent
    denominator, rather than election-time DOB math.
  * RECIPIENT-PARTY: Idaho Sunshine carries no party on the recipient record, so
    `donor_party`/`donation_lean` are unresolved UNTIL you run
    `scripts/backfill_id_recipient_party.py` (resolves recipient party from the
    on-disk SoS candidate roster + party/committee name patterns into
    committee_party_override — ~52% of matched donors, ~66% of candidate-directed
    $). Run that first for the crossover section; without it the crossover prints
    0%. The MATCH itself + own-party + age + concentration + geography do not
    depend on recipient party and are robust either way.

Usage:
    STATE=ID python scripts/match_id_voters_to_donors.py
"""
import os
import sys

import duckdb

os.environ.setdefault("STATE", "ID")
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "src"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from wa_analyzer.analysis.donor_analysis import match_voters_to_donors  # noqa: E402

ID_STATEWIDE = "data/id_statewide.duckdb"
ID_VRDB = "data/id_vrdb.duckdb"

PARTY_CASE = """
    CASE WHEN v.party='REP' THEN 'REP' WHEN v.party='DEM' THEN 'DEM'
         WHEN v.party='UNA' THEN 'UNAFF' ELSE 'OTHER' END
"""
PARTIES = ["REP", "DEM", "UNAFF", "OTHER"]
AGE_BANDS = ["18-29", "30-44", "45-64", "65+"]

_BAND = """CASE WHEN age BETWEEN 18 AND 29 THEN '18-29'
    WHEN age BETWEEN 30 AND 44 THEN '30-44' WHEN age BETWEEN 45 AND 64 THEN '45-64'
    WHEN age BETWEEN 65 AND 105 THEN '65+' END"""


def main() -> int:
    con = duckdb.connect(ID_STATEWIDE)  # read-write: writes voter_donor_affiliation
    con.execute(f"ATTACH '{ID_VRDB}' AS vrdb (READ_ONLY)")

    print("[match] running multi-tier voter<->donor match (ID)...")
    res = match_voters_to_donors(con)
    if res.get("skipped"):
        print("  SKIPPED:", res.get("reason"))
        return 1
    print(f"  matched voters       : {res['matched_voters']:,}")
    print(f"  contributions matched: {res['contributions_matched']:,}")
    print("  match-quality tiers  :")
    for q, n in con.execute("""
        SELECT match_quality, count(*) FROM voter_donor_affiliation GROUP BY 1 ORDER BY 2 DESC
    """).fetchall():
        print(f"    {q:18} {n:>10,}")

    # ---- Donor class vs electorate, by the voter's OWN party-of-record ----
    print("\n=== DONOR CLASS vs ELECTORATE — by ID party-of-record ===")
    rows = con.execute(f"""
        WITH d AS (SELECT {PARTY_CASE} party, vda.total_donated
                   FROM voter_donor_affiliation vda JOIN vrdb.voters v USING (state_voter_id))
        SELECT party, count(*) donors, 100.0*count(*)/sum(count(*)) OVER () donor_share,
               round(sum(total_donated)/1e6,2) total_m,
               100.0*sum(total_donated)/sum(sum(total_donated)) OVER () dollar_share
        FROM d GROUP BY party ORDER BY donors DESC
    """).fetchall()
    reg = dict(con.execute(f"""
        SELECT {PARTY_CASE} party, 100.0*count(*)/sum(count(*)) OVER () FROM vrdb.voters v GROUP BY party
    """).fetchall())
    print(f"  {'party':8} {'donors':>9} {'donor%':>8} {'reg%':>7} {'skew':>6} {'$ (M)':>8} {'$ %':>7}")
    print("  " + "-" * 60)
    for party, donors, dshare, totm, dollar in rows:
        r = reg.get(party, float("nan"))
        print(f"  {party:8} {donors:>9,} {dshare:7.1f}% {r:6.1f}% {dshare-r:+5.1f} {totm:>7.2f} {dollar:6.1f}%")

    # ---- Donor age skew vs electorate (current-roll age; consistent denom) ----
    print("\n=== DONOR AGE SKEW vs electorate (current-roll age bands) ===")
    print("  age-band share among: matched donors | all voters | 2024 GE voters")
    age_rows = con.execute(f"""
        WITH donors AS (SELECT v.age FROM voter_donor_affiliation vda
                        JOIN vrdb.voters v USING (state_voter_id) WHERE v.age IS NOT NULL),
             allv AS (SELECT v.age FROM vrdb.voters v WHERE v.age IS NOT NULL),
             ge24 AS (SELECT v.age FROM vrdb.voter_participation p JOIN vrdb.voters v USING (state_voter_id)
                      WHERE p.election_year=2024 AND p.kind='GENERAL' AND v.age IS NOT NULL),
             band AS (
                SELECT 'donors' src, {_BAND} b FROM donors
                UNION ALL SELECT 'allv', {_BAND} FROM allv
                UNION ALL SELECT 'ge24', {_BAND} FROM ge24)
        SELECT b,
            100.0*count(*) FILTER(WHERE src='donors')/sum(count(*) FILTER(WHERE src='donors')) OVER (),
            100.0*count(*) FILTER(WHERE src='allv')/sum(count(*) FILTER(WHERE src='allv')) OVER (),
            100.0*count(*) FILTER(WHERE src='ge24')/sum(count(*) FILTER(WHERE src='ge24')) OVER ()
        FROM band WHERE b IS NOT NULL GROUP BY b ORDER BY b
    """).fetchall()
    print(f"  {'band':8} {'donors':>9} {'allvoters':>10} {'2024GE':>9}")
    for b, dn, av, ge in age_rows:
        print(f"  {b:8} {dn:8.1f}% {av:9.1f}% {ge:8.1f}%")

    # ---- Donor-dollar concentration (top 1% / top 10% of matched donors) ----
    print("\n=== DONOR-DOLLAR CONCENTRATION (matched ID donors) ===")
    # Concentration estimator standardized across WA/NY/ID: NTILE(100) equal-count
    # donor buckets over actual donors (total_donated>0). "top 1%/10%" = summed $ of the
    # top 1/10 buckets / all matched $. Equal-count buckets are robust to ties at round
    # dollar amounts; PERCENT_RANK (the prior method) drifts from an exact decile at ID's
    # small N (~27k: it read 69.0% vs 70.8%). See docs/donor-class-and-the-electorate.md §F2 note.
    conc = con.execute("""
        WITH r AS (SELECT total_donated t, NTILE(100) OVER (ORDER BY total_donated DESC) p
                   FROM voter_donor_affiliation WHERE total_donated > 0)
        SELECT round(100.0*SUM(t) FILTER(WHERE p=1)/SUM(t),1),
               round(100.0*SUM(t) FILTER(WHERE p<=10)/SUM(t),1) FROM r
    """).fetchone()
    print(f"  top 1% of matched donors  = {conc[0]}% of matched $")
    print(f"  top 10% of matched donors = {conc[1]}% of matched $")

    # ---- Geographic concentration (top counties by matched $) ----
    print("\n=== DONOR $ BY COUNTY (top 8, share of matched $) ===")
    for cty, dn, sh in con.execute("""
        WITH d AS (SELECT v.county_name, vda.total_donated
                   FROM voter_donor_affiliation vda JOIN vrdb.voters v USING (state_voter_id))
        SELECT county_name, count(*), 100.0*sum(total_donated)/sum(sum(total_donated)) OVER ()
        FROM d GROUP BY county_name ORDER BY sum(total_donated) DESC LIMIT 8
    """).fetchall():
        print(f"  {cty:16} {dn:>7,} donors  {sh:5.1f}% of $")

    # ---- Recipient lean x own party (crossover) — reliability-flagged ----
    print("\n=== RECIPIENT LEAN x OWN PARTY (crossover) ===")
    resolved = con.execute("""
        SELECT 100.0*count(*) FILTER(WHERE donor_party<>'OTHER')/count(*) FROM voter_donor_affiliation
    """).fetchone()[0]
    print(f"  resolved-recipient share: {resolved:.1f}% "
          f"({'USABLE' if resolved and resolved > 40 else 'UNRESOLVED — Idaho Sunshine has no recipient party; needs a Sunshine candidate->party backfill (follow-on)'})")
    rows = con.execute(f"""
        WITH d AS (SELECT {PARTY_CASE} own_party, vda.donor_party
                   FROM voter_donor_affiliation vda JOIN vrdb.voters v USING (state_voter_id))
        SELECT own_party, count(*) FILTER(WHERE donor_party<>'OTHER') resolved,
            100.0*count(*) FILTER(WHERE donor_party='D_DONOR')/NULLIF(count(*) FILTER(WHERE donor_party<>'OTHER'),0) pd,
            100.0*count(*) FILTER(WHERE donor_party='R_DONOR')/NULLIF(count(*) FILTER(WHERE donor_party<>'OTHER'),0) pr,
            100.0*count(*) FILTER(WHERE donor_party='MIXED')/NULLIF(count(*) FILTER(WHERE donor_party<>'OTHER'),0) pm
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
