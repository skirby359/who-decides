"""Idaho electorate analyses enabled by the voter file (deep-RED companion to
diag_ny_electorate_extras.py). No new data needed:

1. The unaffiliated bloc characterized (24% of the roll, the recurring blind spot).
2. Donor party mix x legislative-district competitiveness.
3. Turnout decomposition (Das-Gupta, party-resolved): 2024 presidential ->
   2022 midterm. DIAGNOSTIC ONLY — the paper does not report it, see s3's
   docstring.
4. Registration-event-year trend: party mix + age at the most recent registration
   event. NOT a cohort series — see s4_registration_trend's docstring.
5. Idaho safe-seat map from registration lopsidedness (CD + LD).

Age note: ID gives current (2026) age, not DOB. Election-time / registration-time
age is approximated as `age - (2026 - year)`; bands are robust.

Usage:
    python scripts/diag_id_electorate_extras.py
"""
import duckdb

ID_STATEWIDE = "data/id_statewide.duckdb"
ID_VRDB = "data/id_vrdb.duckdb"

PARTY = """
    CASE WHEN v.party='REP' THEN 'REP' WHEN v.party='DEM' THEN 'DEM'
         WHEN v.party='UNA' THEN 'UNAFF' ELSE 'OTHER' END
"""
BUCKETS = ["18-29", "30-44", "45-64", "65+"]


def _con():
    con = duckdb.connect(ID_STATEWIDE, read_only=True)
    con.execute(f"ATTACH '{ID_VRDB}' AS vrdb (READ_ONLY)")
    return con


def s1_unaffiliated_bloc(con):
    print("=" * 76)
    print("1. THE UNAFFILIATED BLOC vs the parties (current roll; age as of 2026)")
    print("=" * 76)
    rows = con.execute(f"""
        WITH base AS (
            SELECT v.state_voter_id, {PARTY} AS party, v.age, v.registration_date AS rd
            FROM vrdb.voters v WHERE v.age BETWEEN 18 AND 105
        ),
        voted24 AS (SELECT DISTINCT state_voter_id FROM vrdb.voter_participation
                    WHERE election_year=2024 AND kind='GENERAL'),
        prim24 AS (SELECT DISTINCT state_voter_id FROM vrdb.voter_participation
                   WHERE election_year=2024 AND kind='PRIMARY'),
        don AS (SELECT DISTINCT state_voter_id FROM voter_donor_affiliation)
        SELECT party, count(*) n, median(age) med,
               100.0*count(*) FILTER(WHERE age>=65)/count(*) p65,
               100.0*count(*) FILTER(WHERE age<30)/count(*) p18,
               -- Rate columns use a REGISTERED-BY-ELECTION denominator: a voter
               -- who registered after an election could not have voted in it, so
               -- counting them in the denominator biases the rate low. This keeps
               -- §III consistent with diag_id_turnout_party (section D + E2), which
               -- already filter by registration_date. Composition columns above
               -- stay on the full current roll (they characterize the bloc, not a rate).
               100.0*count(*) FILTER(WHERE state_voter_id IN (SELECT state_voter_id FROM voted24)
                                       AND (rd IS NULL OR rd <= DATE '2024-11-05'))
                     / NULLIF(count(*) FILTER(WHERE rd IS NULL OR rd <= DATE '2024-11-05'), 0) t24,
               100.0*count(*) FILTER(WHERE state_voter_id IN (SELECT state_voter_id FROM prim24)
                                       AND (rd IS NULL OR rd <= DATE '2024-05-20'))
                     / NULLIF(count(*) FILTER(WHERE rd IS NULL OR rd <= DATE '2024-05-20'), 0) prim,
               1000.0*count(*) FILTER(WHERE state_voter_id IN (SELECT state_voter_id FROM don))/count(*) dpk
        FROM base GROUP BY party ORDER BY n DESC
    """).fetchall()
    print(f"  {'party':8} {'roll%':>7} {'med':>5} {'%65+':>7} {'%18-29':>8} {'2024GE':>8} {'2024pri':>8} {'don/1k':>8}")
    tot = sum(r[1] for r in rows)
    for party, n, med, p65, p18, t24, prim, dpk in rows:
        print(f"  {party:8} {100.0*n/tot:6.1f}% {med:5.0f} {p65:6.1f}% {p18:7.1f}% {t24:7.1f}% {prim:7.1f}% {dpk:7.1f}")
    print("  (don/1k = matched Idaho-Sunshine donors per 1,000 registrants;")
    print("   2024GE/2024pri = voted / registrants eligible by that election's date.")
    print("   CAVEAT: these RATES are survivorship-INFLATED — the 1.03M current roll is")
    print("   smaller than the 1.18M registered in 2024 (official turnout 77.8%), and the")
    print("   bias is non-uniform. The paper uses composition shares, NOT these rates.)")


def s2_donor_mix_competitiveness(con):
    print("\n" + "=" * 76)
    print("2. DONOR PARTY MIX x LEGISLATIVE-DISTRICT COMPETITIVENESS")
    print("=" * 76)
    rows = con.execute(f"""
        WITH ld_comp AS (
            SELECT lower(district_id) did, avg(abs(predicted_margin)) absm
            FROM forecast_predictions
            WHERE lower(district_id) LIKE 'ld%' GROUP BY 1
        ),
        band AS (
            SELECT regexp_extract(did,'[0-9]+') ld,
                   CASE WHEN absm<5 THEN '1 Tossup (<5)' WHEN absm<10 THEN '2 Lean (5-10)'
                        WHEN absm<20 THEN '3 Likely (10-20)' ELSE '4 Solid (20+)' END b
            FROM ld_comp
        ),
        donors AS (
            SELECT TRY_CAST(v.legislative_district AS INT)::VARCHAR ld, {PARTY} AS party
            FROM voter_donor_affiliation vda JOIN vrdb.voters v USING (state_voter_id)
            WHERE v.legislative_district IS NOT NULL
        )
        SELECT b.b band, count(*) donors,
               100.0*count(*) FILTER(WHERE party='REP')/count(*) repp,
               100.0*count(*) FILTER(WHERE party='DEM')/count(*) demp,
               100.0*count(*) FILTER(WHERE party='UNAFF')/count(*) unap
        FROM donors d JOIN band b ON TRY_CAST(b.ld AS INT)=TRY_CAST(d.ld AS INT)
        GROUP BY b.b ORDER BY b.b
    """).fetchall()
    if not rows:
        print("  (no forecast_predictions LD rows found — skipping)")
        return
    print(f"  {'LD band':18} {'donors':>9} {'%REP':>7} {'%DEM':>7} {'%UNAFF':>8}")
    for b, n, rp, dp, up in rows:
        print(f"  {b:18} {n:>9,} {rp:6.1f}% {dp:6.1f}% {up:7.1f}%")


def s3_decomposition(con):
    """Das-Gupta rate/composition split — RETAINED AS A DIAGNOSTIC, NOT A RESULT.

    Section I cited this as evidence that the presidential-to-midterm graying is "behavior,
    not rolls". It was withdrawn from the paper on 2026-08-15: the decomposition
    reconstructs historical roll populations from the CURRENT roll and the current
    `registration_date`, and the same paper establishes that those denominators are
    unusable (survivorship, resetting registration dates, non-uniform attrition). A
    rate-based decomposition inherits every one of those defects, so it cannot carry a
    mechanism claim even though it happens to point the same way.

    It stays here because a diagnostic that says "this is what a rate cut would show, and
    here is why we do not report it" is worth more than a deleted function.
    """
    print("\n" + "=" * 76)
    print("3. TURNOUT DECOMPOSITION (Das-Gupta), party-resolved: 2024 pres -> 2022 midterm")
    print("   DIAGNOSTIC ONLY — the paper reports no mechanism from this (see docstring)")
    print("=" * 76)

    def cohorts(year):
        agex = f"(v.age - ({2026 - year}))"
        rows = con.execute(f"""
            WITH e AS (
                SELECT {PARTY} AS party,
                    CASE WHEN {agex}<30 THEN '18-29' WHEN {agex}<45 THEN '30-44'
                         WHEN {agex}<65 THEN '45-64' ELSE '65+' END coh,
                    CASE WHEN h.state_voter_id IS NOT NULL THEN 1 ELSE 0 END voted
                FROM vrdb.voters v
                LEFT JOIN (SELECT DISTINCT state_voter_id FROM vrdb.voter_participation
                           WHERE election_year={year} AND kind='GENERAL') h USING (state_voter_id)
                WHERE {agex}>=18
                  AND (v.registration_date IS NULL OR v.registration_date<=make_date({year},11,5)))
            SELECT party, coh, count(*) roll, sum(voted) voted FROM e GROUP BY 1,2
        """).fetchall()
        d = {}
        for party, coh, roll, voted in rows:
            d.setdefault(party, {})[coh] = (float(roll), float(voted))
        return d

    P = cohorts(2024)
    O = cohorts(2022)

    def share65(roll, rate):
        v = {c: roll[c] * rate[c] for c in BUCKETS}
        tot = sum(v.values())
        return v["65+"] / tot if tot else float("nan")

    print(f"  {'party':8} {'65+ pres':>10} {'65+ mid':>9} {'observed':>10} {'RATE eff':>9} {'COMP eff':>9}")
    for party in ("REP", "DEM", "UNAFF"):
        if party not in P or party not in O:
            continue
        rollP = {c: P[party].get(c, (0, 0))[0] for c in BUCKETS}
        rollO = {c: O[party].get(c, (0, 0))[0] for c in BUCKETS}
        rateP = {c: (P[party][c][1] / P[party][c][0]) if P[party].get(c, (0, 0))[0] else 0 for c in BUCKETS}
        rateO = {c: (O[party][c][1] / O[party][c][0]) if O[party].get(c, (0, 0))[0] else 0 for c in BUCKETS}
        sPP, sOO = share65(rollP, rateP), share65(rollO, rateO)
        rate_eff = 0.5 * (share65(rollP, rateO) - share65(rollP, rateP)) \
            + 0.5 * (share65(rollO, rateO) - share65(rollO, rateP))
        comp_eff = 0.5 * (share65(rollO, rateP) - share65(rollP, rateP)) \
            + 0.5 * (share65(rollO, rateO) - share65(rollP, rateO))
        print(f"  {party:8} {100*sPP:9.1f}% {100*sOO:8.1f}% {100*(sOO-sPP):+9.1f} {100*rate_eff:+8.1f} {100*comp_eff:+8.1f}")
    print("  (RATE eff >> COMP eff would read as behavior rather than roll composition —")
    print("   but BOTH columns are built on reconstructed historical rolls, which this file's")
    print("   own survivorship caveat says are unusable. Directional only; the paper reports")
    print("   the COMPOSITION change and no mechanism. Withdrawn from §I on 2026-08-15.)")


def s4_registration_trend(con):
    """Party mix and age by the YEAR OF THE MOST RECENT REGISTRATION EVENT.

    NOT cohorts, and the labels said cohorts until 2026-08-15. `registration_date` is
    rewritten on an address change, a party change (including the § 34-411A poll-book
    affiliation) and an election-day registration, so a row groups people who have avoided
    a resetting event for N years — not people who entered the electorate in that year. The
    paper (§VI) has carried that correction since an earlier round; this script's headings
    still said "NEW-REGISTRANT COHORTS" and "voters ... who first registered that year",
    and an external referee found the stale text here rather than in the paper.
    """
    print("\n" + "=" * 76)
    print("4. REGISTRATION-EVENT YEARS over time: party mix + age at that event")
    print("   (NOT cohorts — registration_date is the most recent event, not the first)")
    print("=" * 76)
    rows = con.execute(f"""
        SELECT year(v.registration_date) ry, count(*) n,
               100.0*count(*) FILTER(WHERE {PARTY}='REP')/count(*) repp,
               100.0*count(*) FILTER(WHERE {PARTY}='DEM')/count(*) demp,
               100.0*count(*) FILTER(WHERE {PARTY}='UNAFF')/count(*) unap,
               median(v.age - (2026 - year(v.registration_date))) med_age_at_reg
        FROM vrdb.voters v
        WHERE v.registration_date IS NOT NULL AND v.age IS NOT NULL
          AND year(v.registration_date) IN (2008,2012,2016,2020,2022,2024)
          AND (v.age - (2026 - year(v.registration_date))) BETWEEN 16 AND 100
        GROUP BY ry ORDER BY ry
    """).fetchall()
    print(f"  {'reg year':9} {'new regs':>10} {'%REP':>7} {'%DEM':>7} {'%UNAFF':>8} {'med age@reg':>12}")
    for ry, n, rp, dp, up, ma in rows:
        print(f"  {ry:<9} {n:>10,} {rp:6.1f}% {dp:6.1f}% {up:7.1f}% {ma:11.0f}")
    print("  (row = voters on the current roll whose MOST RECENT registration event falls")
    print("   in that year — re-registrations, moves, party changes and election-day sign-ups")
    print("   are all in it. 36.3% of the 2024 row had already voted in an earlier election.)")


def s5_safe_seat_registration(con):
    print("\n" + "=" * 76)
    print("5. IDAHO SAFE-SEAT MAP from REGISTRATION lean (current roll; REP%-DEM%)")
    print("=" * 76)
    for level, col, total in (("Congressional", "congressional_district", 2),
                              ("Legislative", "legislative_district", 35)):
        rows = con.execute(f"""
            WITH d AS (
                SELECT v.{col} dist,
                       100.0*count(*) FILTER(WHERE v.party='REP')/count(*)
                       - 100.0*count(*) FILTER(WHERE v.party='DEM')/count(*) lean
                FROM vrdb.voters v
                WHERE v.{col} IS NOT NULL AND v.{col}<>'' GROUP BY 1
            )
            SELECT CASE WHEN lean>=40 THEN '1 Safe R (R+40+)' WHEN lean>=20 THEN '2 Likely R (R+20-40)'
                        WHEN lean>=5 THEN '3 Lean R (R+5-20)' WHEN lean>-5 THEN '4 Competitive (<5)'
                        WHEN lean>-20 THEN '5 Lean/Likely D' ELSE '6 Safe D (D+20+)' END band,
                   count(*) n
            FROM d GROUP BY 1 ORDER BY 1
        """).fetchall()
        print(f"\n  -- {level} districts (n={total}) by registration lean --")
        for band, n in rows:
            print(f"     {band:24} {n:>4}")


def main():
    con = _con()
    s1_unaffiliated_bloc(con)
    s2_donor_mix_competitiveness(con)
    s3_decomposition(con)
    s4_registration_trend(con)
    s5_safe_seat_registration(con)
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
