"""Five NY electorate analyses enabled by the voter file (no new data needed):

1. The unaffiliated "blank" bloc characterized (25% of the roll, recurring blind spot).
2. Donor party mix x district (CD) competitiveness.
3. Turnout decomposition (Das-Gupta, party-resolved): is the gray off-year
   electorate a behavior (rate) or registration (composition) effect, per party?
4. Registration-cohort trend: party mix + age-at-registration of NEW registrants over time.
5. NY safe-seat map from registration lopsidedness (CD + Assembly).

Uses data/ny_vrdb.duckdb (voters, voter_participation) + data/ny_statewide.duckdb
(voter_donor_affiliation, forecast_predictions for competitiveness).

Usage:
    STATE=NY python scripts/diag_ny_electorate_extras.py
"""
import duckdb

NY_STATEWIDE = "data/ny_statewide.duckdb"
NY_VRDB = "data/ny_vrdb.duckdb"

PARTY = """
    CASE WHEN v.party='DEM' THEN 'DEM' WHEN v.party='REP' THEN 'REP'
         WHEN v.party='BLK' THEN 'NOPARTY' ELSE 'OTHER' END
"""
BUCKETS = ["18-29", "30-44", "45-64", "65+"]


def _con():
    con = duckdb.connect(NY_STATEWIDE, read_only=True)
    con.execute(f"ATTACH '{NY_VRDB}' AS vrdb (READ_ONLY)")
    return con


def s1_blank_bloc(con):
    print("=" * 76)
    print("1. THE UNAFFILIATED 'BLANK' BLOC vs the major parties (active roll)")
    print("=" * 76)
    rows = con.execute(f"""
        WITH base AS (
            SELECT v.state_voter_id, {PARTY} AS party,
                   date_diff('year', v.birthdate, DATE '2024-11-05') AS age,
                   v.county_name
            FROM vrdb.voters v
            WHERE v.status_code='A' AND v.birthdate IS NOT NULL
              AND date_diff('year', v.birthdate, DATE '2024-11-05') BETWEEN 18 AND 105
        ),
        voted24 AS (SELECT DISTINCT state_voter_id FROM vrdb.voter_participation
                    WHERE election_year=2024 AND kind='GENERAL'),
        don AS (SELECT DISTINCT state_voter_id FROM voter_donor_affiliation)
        SELECT party, count(*) n,
               median(age) med_age,
               100.0*count(*) FILTER(WHERE age>=65)/count(*) p65,
               100.0*count(*) FILTER(WHERE age<30)/count(*) p18_29,
               100.0*count(*) FILTER(WHERE state_voter_id IN (SELECT state_voter_id FROM voted24))/count(*) turnout24,
               1000.0*count(*) FILTER(WHERE state_voter_id IN (SELECT state_voter_id FROM don))/count(*) donor_per_1k
        FROM base GROUP BY party ORDER BY n DESC
    """).fetchall()
    print(f"  {'party':9} {'roll%':>7} {'med_age':>8} {'%65+':>7} {'%18-29':>8} {'2024 turnout':>13} {'donors/1k':>10}")
    tot = sum(r[1] for r in rows)
    for party, n, med, p65, p18, t24, dpk in rows:
        print(f"  {party:9} {100.0*n/tot:6.1f}% {med:8.0f} {p65:6.1f}% {p18:7.1f}% {t24:12.1f}% {dpk:9.1f}")
    print("  (donors/1k = matched federal donors per 1,000 registrants in that bloc)")


def s2_donor_mix_competitiveness(con):
    print("\n" + "=" * 76)
    print("2. DONOR PARTY MIX x CONGRESSIONAL-DISTRICT COMPETITIVENESS")
    print("=" * 76)
    rows = con.execute(f"""
        WITH cd_comp AS (   -- one row per CD: competitiveness band from |margin|
            SELECT TRY_CAST(regexp_extract(district_id,'[0-9]+') AS INT) cd,
                   avg(abs(predicted_margin)) absm
            FROM forecast_predictions
            WHERE state='NY' AND district_id LIKE 'cd%'
            GROUP BY 1
        ),
        band AS (
            SELECT cd, CASE WHEN absm<5 THEN '1 Tossup (<5)' WHEN absm<10 THEN '2 Lean (5-10)'
                            WHEN absm<20 THEN '3 Likely (10-20)' ELSE '4 Solid (20+)' END b
            FROM cd_comp
        ),
        donors AS (
            SELECT TRY_CAST(v.congressional_district AS INT) cd, {PARTY} AS party
            FROM voter_donor_affiliation vda JOIN vrdb.voters v USING (state_voter_id)
            WHERE v.congressional_district IS NOT NULL
        )
        SELECT b.b AS band, count(*) donors,
               100.0*count(*) FILTER(WHERE party='DEM')/count(*) demp,
               100.0*count(*) FILTER(WHERE party='REP')/count(*) repp,
               100.0*count(*) FILTER(WHERE party='NOPARTY')/count(*) nop
        FROM donors d JOIN band b ON b.cd=d.cd
        GROUP BY b.b ORDER BY b.b
    """).fetchall()
    print(f"  {'CD band':18} {'donors':>9} {'%DEM':>7} {'%REP':>7} {'%NOPARTY':>9}")
    for b, n, dp, rp, no in rows:
        print(f"  {b:18} {n:>9,} {dp:6.1f}% {rp:6.1f}% {no:8.1f}%")
    # registrant party mix per band for comparison (does donor mix track registration?)
    reg = con.execute(f"""
        WITH cd_comp AS (
            SELECT TRY_CAST(regexp_extract(district_id,'[0-9]+') AS INT) cd, avg(abs(predicted_margin)) absm
            FROM forecast_predictions WHERE state='NY' AND district_id LIKE 'cd%' GROUP BY 1),
        band AS (SELECT cd, CASE WHEN absm<5 THEN '1 Tossup (<5)' WHEN absm<10 THEN '2 Lean (5-10)'
                                 WHEN absm<20 THEN '3 Likely (10-20)' ELSE '4 Solid (20+)' END b FROM cd_comp)
        SELECT b.b, 100.0*count(*) FILTER(WHERE {PARTY}='DEM')/count(*) demp
        FROM vrdb.voters v JOIN band b ON b.cd=TRY_CAST(v.congressional_district AS INT)
        WHERE v.status_code='A' GROUP BY b.b ORDER BY b.b
    """).fetchall()
    print("  (registrant %DEM by band, for reference: " +
          ", ".join(f"{b.split()[0]}={d:.0f}%" for b, d in reg) + ")")


def s3_decomposition(con):
    print("\n" + "=" * 76)
    print("3. TURNOUT DECOMPOSITION (Das-Gupta), party-resolved: 2024 pres -> 2025 off-year")
    print("   does the gray off-year electorate come from RATE (behavior) or COMPOSITION (roll)?")
    print("=" * 76)

    def cohorts(date, year):
        rows = con.execute(f"""
            WITH e AS (
                SELECT {PARTY} AS party,
                    CASE WHEN date_diff('year',v.birthdate,DATE '{date}')<30 THEN '18-29'
                         WHEN date_diff('year',v.birthdate,DATE '{date}')<45 THEN '30-44'
                         WHEN date_diff('year',v.birthdate,DATE '{date}')<65 THEN '45-64'
                         ELSE '65+' END coh,
                    CASE WHEN h.state_voter_id IS NOT NULL THEN 1 ELSE 0 END voted
                FROM vrdb.voters v
                LEFT JOIN (SELECT DISTINCT state_voter_id FROM vrdb.voter_participation
                           WHERE election_year={year} AND kind='GENERAL') h USING (state_voter_id)
                WHERE v.birthdate IS NOT NULL
                  AND date_diff('year',v.birthdate,DATE '{date}')>=18
                  AND (v.registration_date IS NULL OR v.registration_date<=DATE '{date}'))
            SELECT party, coh, count(*) roll, sum(voted) voted FROM e GROUP BY 1,2
        """).fetchall()
        d = {}
        for party, coh, roll, voted in rows:
            d.setdefault(party, {})[coh] = (float(roll), float(voted))
        return d

    P = cohorts("2024-11-05", 2024)
    O = cohorts("2025-11-04", 2025)

    def share65(roll, rate):
        v = {c: roll[c] * rate[c] for c in BUCKETS}
        tot = sum(v.values())
        return v["65+"] / tot if tot else float("nan")

    print(f"  {'party':9} {'65+ share P':>12} {'65+ share O':>12} {'observed chg':>13} {'RATE eff':>9} {'COMP eff':>9}")
    for party in ("DEM", "REP", "NOPARTY"):
        if party not in P or party not in O:
            continue
        rollP = {c: P[party].get(c, (0, 0))[0] for c in BUCKETS}
        rollO = {c: O[party].get(c, (0, 0))[0] for c in BUCKETS}
        rateP = {c: (P[party][c][1] / P[party][c][0]) if P[party].get(c, (0, 0))[0] else 0 for c in BUCKETS}
        rateO = {c: (O[party][c][1] / O[party][c][0]) if O[party].get(c, (0, 0))[0] else 0 for c in BUCKETS}
        sPP, sOO = share65(rollP, rateP), share65(rollO, rateO)
        # symmetric two-factor: rate effect = avg over the two roll structures
        rate_eff = 0.5 * (share65(rollP, rateO) - share65(rollP, rateP)) \
            + 0.5 * (share65(rollO, rateO) - share65(rollO, rateP))
        comp_eff = 0.5 * (share65(rollO, rateP) - share65(rollP, rateP)) \
            + 0.5 * (share65(rollO, rateO) - share65(rollP, rateO))
        print(f"  {party:9} {100*sPP:11.1f}% {100*sOO:11.1f}% {100*(sOO-sPP):+10.1f} "
              f"{100*rate_eff:+8.1f} {100*comp_eff:+8.1f}")
    print("  (RATE eff >> COMP eff => off-year skew is behavior/salience, fixable by on-cycle timing)")


def s4_registration_trend(con):
    print("\n" + "=" * 76)
    print("4. NEW-REGISTRANT COHORTS over time: party mix + age at registration")
    print("=" * 76)
    rows = con.execute(f"""
        SELECT year(v.registration_date) ry, count(*) n,
               100.0*count(*) FILTER(WHERE {PARTY}='DEM')/count(*) demp,
               100.0*count(*) FILTER(WHERE {PARTY}='REP')/count(*) repp,
               100.0*count(*) FILTER(WHERE {PARTY}='NOPARTY')/count(*) nop,
               median(date_diff('year', v.birthdate, v.registration_date)) med_age_at_reg
        FROM vrdb.voters v
        WHERE v.registration_date IS NOT NULL AND v.birthdate IS NOT NULL
          AND year(v.registration_date) IN (2004,2008,2012,2016,2020,2024)
          AND date_diff('year', v.birthdate, v.registration_date) BETWEEN 16 AND 100
        GROUP BY ry ORDER BY ry
    """).fetchall()
    print(f"  {'reg year':9} {'new regs':>10} {'%DEM':>7} {'%REP':>7} {'%NOPARTY':>9} {'med age@reg':>12}")
    for ry, n, dp, rp, no, ma in rows:
        print(f"  {ry:<9} {n:>10,} {dp:6.1f}% {rp:6.1f}% {no:8.1f}% {ma:11.0f}")
    print("  (cohort = voters still on the current roll who first registered that year)")


def s5_safe_seat_registration(con):
    print("\n" + "=" * 76)
    print("5. NY SAFE-SEAT MAP from REGISTRATION lean (active roll; DEM%-REP%)")
    print("=" * 76)
    for level, col, total in (("Congressional", "congressional_district", 26),
                              ("Assembly", "assembly_district", 150)):
        rows = con.execute(f"""
            WITH d AS (
                SELECT v.{col} dist,
                       100.0*count(*) FILTER(WHERE v.party='DEM')/count(*)
                       - 100.0*count(*) FILTER(WHERE v.party='REP')/count(*) lean
                FROM vrdb.voters v
                WHERE v.status_code='A' AND v.{col} IS NOT NULL AND v.{col}<>'' AND v.{col}<>'000'
                GROUP BY 1
            )
            SELECT CASE WHEN lean>=40 THEN '1 Safe D (D+40+)' WHEN lean>=20 THEN '2 Likely D (D+20-40)'
                        WHEN lean>=5 THEN '3 Lean D (D+5-20)' WHEN lean>-5 THEN '4 Competitive (<5)'
                        WHEN lean>-20 THEN '5 Lean/Likely R' ELSE '6 Safe R (R+20+)' END band,
                   count(*) n
            FROM d GROUP BY 1 ORDER BY 1
        """).fetchall()
        print(f"\n  -- {level} districts (n={total}) by registration lean --")
        for band, n in rows:
            print(f"     {band:24} {n:>4}")


def main():
    con = _con()
    s1_blank_bloc(con)
    s2_donor_mix_competitiveness(con)
    s3_decomposition(con)
    s4_registration_trend(con)
    s5_safe_seat_registration(con)
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
