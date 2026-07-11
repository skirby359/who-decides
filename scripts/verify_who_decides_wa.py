"""Independent re-derivation of every headline number in docs/who-decides-washington.md.

This is the human-owned verification the publication-checklist demands: it hits
data/wa_vrdb.duckdb DIRECTLY with from-scratch SQL (not by importing the diag
scripts), so a cell-for-cell match against the paper confirms the finding
independently of the analysis code. Read-only; aggregate output only (the VRDB
carries PII — never emit individual rows; RCW 29A.08.720).

Covers checklist ledger claims #1-#10:
  - turnout rate + composition share by age cohort x cycle type   (#1-#7)
  - Das-Gupta symmetric behavior-vs-rolls decomposition           (#8-#10)

Run from anywhere:  python scripts/verify_who_decides_wa.py
"""
from pathlib import Path
import duckdb

VRDB = str(Path(__file__).resolve().parent.parent / "data" / "wa_vrdb.duckdb")
BUCKETS = ["18-29", "30-44", "45-64", "65+"]
ELECTIONS = [("2024-11-05", "presidential"), ("2022-11-08", "midterm"),
             ("2021-11-02", "off-year"), ("2023-11-07", "off-year"), ("2025-11-04", "off-year")]
PRES, OFF = "2024-11-05", "2025-11-04"


def cohort_table(con, date):
    """{cohort -> (eligible_registrants, voted)} on the current roll, age as of `date`.
    Denominator = current-roll registrants age>=18 at the election, registered on/before it."""
    rows = con.execute(f"""
        WITH elig AS (
            SELECT CASE WHEN date_diff('year', v.birthdate, DATE '{date}') < 30 THEN '18-29'
                        WHEN date_diff('year', v.birthdate, DATE '{date}') < 45 THEN '30-44'
                        WHEN date_diff('year', v.birthdate, DATE '{date}') < 65 THEN '45-64'
                        ELSE '65+' END coh,
                   CASE WHEN h.state_voter_id IS NOT NULL THEN 1 ELSE 0 END voted
            FROM voters v
            LEFT JOIN (SELECT DISTINCT state_voter_id FROM voting_history
                       WHERE election_date = DATE '{date}') h ON h.state_voter_id = v.state_voter_id
            WHERE v.birthdate IS NOT NULL
              AND date_diff('year', v.birthdate, DATE '{date}') >= 18
              AND v.registration_date IS NOT NULL AND v.registration_date <= DATE '{date}')
        SELECT coh, COUNT(*) roll, SUM(voted) voted FROM elig GROUP BY 1
    """).fetchall()
    return {coh: (float(roll), float(voted)) for coh, roll, voted in rows}


def elect_share(roll, rate, target):
    voters = {c: roll[c] * rate[c] for c in BUCKETS}
    tot = sum(voters.values())
    return voters[target] / tot if tot else float("nan")


# Official certified statewide BALLOTS COUNTED, per WA Secretary of State
# (results.vote.wa.gov/results/<yyyymmdd>/turnout.html). External benchmark.
OFFICIAL_BALLOTS = {
    "2021-11-02": 1_896_481, "2022-11-08": 3_067_686, "2023-11-07": 1_758_084,
    "2024-11-05": 3_961_569, "2025-11-04": 2_001_425,
}


def coverage_table(con):
    """#11-#15: our observations vs official certified counts (survivorship check)."""
    print("\n" + "=" * 92)
    print("[#11-#15] DATA VALIDATION — coverage vs official certified counts (WA SoS)")
    print(f"{'election':12}{'type':13}{'official':>12}{'in_file':>12}{'analyzable':>12}{'anlz/off':>10}")
    for date, kind in ELECTIONS:
        official = OFFICIAL_BALLOTS[date]
        infile = con.execute(f"SELECT COUNT(DISTINCT state_voter_id) FROM voting_history "
                             f"WHERE election_date = DATE '{date}'").fetchone()[0]
        analyzable = con.execute(f"""
            SELECT COUNT(*) FROM (SELECT DISTINCT state_voter_id FROM voting_history
                                  WHERE election_date = DATE '{date}') h
            JOIN voters v USING (state_voter_id) WHERE v.birthdate IS NOT NULL""").fetchone()[0]
        print(f"{date:12}{kind:13}{official:>12,}{infile:>12,}{analyzable:>12,}"
              f"{analyzable/official*100:>9.1f}%")


def survivorship(con):
    """#16-#18: are the ballots we CAN'T see (voter since left the roll) older?"""
    print("\n[#16-#18] SURVIVORSHIP HOLE — voters who cast a past ballot but are gone")
    print("           from the current roll, aged via the 2023-09-01 snapshot")
    for date, kind in [("2021-11-02", "off-year"), ("2022-11-08", "midterm"),
                       ("2023-11-07", "off-year")]:
        rows = con.execute(f"""
            WITH miss AS (
                SELECT DISTINCT h.state_voter_id
                FROM (SELECT DISTINCT state_voter_id FROM voting_history
                      WHERE election_date = DATE '{date}') h
                LEFT JOIN voters v USING (state_voter_id) WHERE v.state_voter_id IS NULL),
            aged AS (
                SELECT CASE WHEN date_diff('year', s.birthdate, DATE '{date}') < 30 THEN '18-29'
                            WHEN date_diff('year', s.birthdate, DATE '{date}') < 45 THEN '30-44'
                            WHEN date_diff('year', s.birthdate, DATE '{date}') < 65 THEN '45-64'
                            ELSE '65+' END coh
                FROM miss m JOIN voters_20230901 s USING (state_voter_id)
                WHERE s.birthdate IS NOT NULL
                  AND date_diff('year', s.birthdate, DATE '{date}') >= 18)
            SELECT coh, COUNT(*) FROM aged GROUP BY 1""").fetchall()
        d = {c: n for c, n in rows}; t = sum(d.values())
        print(f"  {date} ({kind:9}): missing&aged={t:>8,}  65+={d.get('65+',0)/t*100:5.1f}%  "
              f"18-29={d.get('18-29',0)/t*100:4.1f}%   (observed off-year 65+ share ~37-40%)")
    # roll attrition 2023 snapshot -> current, by age (dated, age>=18 at snapshot)
    lv65, lvN, st65, stN = con.execute("""
        SELECT
          SUM(CASE WHEN v.state_voter_id IS NULL     AND a>=65 THEN 1 ELSE 0 END),
          SUM(CASE WHEN v.state_voter_id IS NULL              THEN 1 ELSE 0 END),
          SUM(CASE WHEN v.state_voter_id IS NOT NULL AND a>=65 THEN 1 ELSE 0 END),
          SUM(CASE WHEN v.state_voter_id IS NOT NULL          THEN 1 ELSE 0 END)
        FROM (SELECT s.state_voter_id, date_diff('year', s.birthdate, DATE '2023-09-01') a
              FROM voters_20230901 s WHERE s.birthdate IS NOT NULL
                AND date_diff('year', s.birthdate, DATE '2023-09-01') >= 18) x
        LEFT JOIN voters v USING (state_voter_id)""").fetchone()
    print(f"  roll attrition 2023->2026: leavers 65+={lv65/lvN*100:.1f}% (n={lvN:,})  "
          f"vs stayers 65+={st65/stN*100:.1f}% (n={stN:,})")


def finer_cohorts(con):
    """#19: composition holds under a finer 18-24/25-29 and 65-74/75+ split."""
    FINE = ['18-24', '25-29', '30-44', '45-64', '65-74', '75+']
    print("\n[#19] SENSITIVITY — composition with finer cohorts (share of electorate)")
    print(f"{'election':12}{'type':13}" + "".join(f"{b:>8}" for b in FINE))
    for date, kind in ELECTIONS:
        a = f"date_diff('year', v.birthdate, DATE '{date}')"
        rows = con.execute(f"""
            WITH e AS (SELECT CASE WHEN {a}<25 THEN '18-24' WHEN {a}<30 THEN '25-29'
                                   WHEN {a}<45 THEN '30-44' WHEN {a}<65 THEN '45-64'
                                   WHEN {a}<75 THEN '65-74' ELSE '75+' END coh
                       FROM (SELECT DISTINCT state_voter_id FROM voting_history
                             WHERE election_date = DATE '{date}') h
                       JOIN voters v USING (state_voter_id)
                       WHERE v.birthdate IS NOT NULL AND {a} >= 18)
            SELECT coh, COUNT(*) FROM e GROUP BY 1""").fetchall()
        d = {c: n for c, n in rows}; t = sum(d.values())
        print(f"{date:12}{kind:13}" + "".join(f"{d.get(b,0)/t*100:>7.1f}%" for b in FINE))


def geography(con):
    """#20: the salience gradient holds in King, the rest of state, metro, and rural."""
    METRO = ("('KING','PIERCE','SNOHOMISH','CLARK','SPOKANE','THURSTON',"
             "'KITSAP','WHATCOM','BENTON','YAKIMA')")

    def share65(date, where):
        a = f"date_diff('year', v.birthdate, DATE '{date}')"
        rows = con.execute(f"""
            WITH e AS (SELECT CASE WHEN {a}<65 THEN 'u' ELSE '65+' END coh
                       FROM (SELECT DISTINCT state_voter_id FROM voting_history
                             WHERE election_date = DATE '{date}') h
                       JOIN voters v USING (state_voter_id)
                       WHERE v.birthdate IS NOT NULL AND {a} >= 18 AND ({where}))
            SELECT coh, COUNT(*) FROM e GROUP BY 1""").fetchall()
        d = {c: n for c, n in rows}; t = sum(d.values())
        return d.get('65+', 0) / t * 100 if t else 0

    print("\n[#20] SENSITIVITY — 65+ share of electorate by geography")
    print(f"{'geography':16}" + "".join(f"{d[:7]:>10}" for d, _ in ELECTIONS))
    for label, where in [("King", "UPPER(v.county_name)='KING'"),
                         ("Rest of state", "UPPER(v.county_name)<>'KING'"),
                         ("Metro (top-10)", f"UPPER(v.county_name) IN {METRO}"),
                         ("Rural (other 29)", f"UPPER(v.county_name) NOT IN {METRO}")]:
        print(f"{label:16}" + "".join(f"{share65(d, where):>9.1f}%" for d, _ in ELECTIONS))


def _analyzable_65(con, date, yr):
    """(A, n65_reached, n65_notreached) on the analyzable electorate (matched to
    current roll + year of birth, no registration filter — matches coverage_table).
    Age convention = election_year - birth_year ('reached' = birthday passed)."""
    return con.execute(f"""
        WITH e AS (
            SELECT EXTRACT(year FROM v.birthdate) AS byr
            FROM (SELECT DISTINCT state_voter_id FROM voting_history
                  WHERE election_date = DATE '{date}') h
            JOIN voters v USING (state_voter_id)
            WHERE v.birthdate IS NOT NULL
              AND ({yr} - EXTRACT(year FROM v.birthdate)) >= 18)
        SELECT COUNT(*),
               SUM(CASE WHEN byr <= {yr}-65 THEN 1 ELSE 0 END),
               SUM(CASE WHEN byr <= {yr}-66 THEN 1 ELSE 0 END)
        FROM e""").fetchone()


def bounding(con):
    """#21: bound the 65+ share of the FULL certified electorate under the two
    extreme assumptions about the unobserved residual (official - analyzable)."""
    print("\n[#21] MISSING-VOTER BOUNDING — 65+ share of the certified electorate")
    print(f"{'election':12}{'type':13}{'official':>10}{'analyzable':>11}{'resid':>8}"
          f"{'obs%':>7}{'MIN%':>7}{'MAX%':>7}")
    mn = {}
    for date, kind in ELECTIONS:
        yr = int(date[:4]); O = OFFICIAL_BALLOTS[date]
        A, n65, _ = _analyzable_65(con, date, yr); R = O - A
        obs, lo, hi = n65 / A * 100, n65 / O * 100, (n65 + R) / O * 100
        mn[date] = (kind, lo, hi)
        print(f"{date:12}{kind:13}{O:>10,}{A:>11,}{R:>8,}{obs:>6.1f}%{lo:>6.1f}%{hi:>6.1f}%")
    pres_max = mn["2024-11-05"][2]
    print(f"  adversarial: presidential 2024 MAX 65+={pres_max:.1f}%; off-year MIN 65+ "
          + " ".join(f"{d[5:7]}/{d[2:4]}={mn[d][1]:.1f}%" for d in
                     ["2021-11-02", "2023-11-07", "2025-11-04"])
          + f"  -> all exceed pres MAX? "
          + ("YES" if all(mn[d][1] > pres_max for d in
                          ["2021-11-02", "2023-11-07", "2025-11-04"]) else "NO"))


def imputation(con):
    """#22: birth-year imputation sensitivity — 65+ share under 'birthday reached'
    (Jan/Jul-1) vs 'not reached' (Dec-31); report the swing."""
    print("\n[#22] BIRTH-YEAR IMPUTATION SENSITIVITY — 65+ share of analyzable electorate")
    print(f"{'election':12}{'type':13}{'reached':>9}{'notreached':>12}{'swing pp':>10}")
    worst = 0.0
    for date, kind in ELECTIONS:
        yr = int(date[:4])
        A, n65, n65_lo = _analyzable_65(con, date, yr)
        hi, lo = n65 / A * 100, n65_lo / A * 100
        if kind == "off-year":
            worst = max(worst, hi - lo)
        print(f"{date:12}{kind:13}{hi:>8.1f}%{lo:>11.1f}%{hi-lo:>9.2f}")
    print(f"  max off-year 65+ swing across extreme imputations: {worst:.2f} pp")


def who_is_counted(con):
    """#23: median age + 65+ share — registered roll vs ballot-returners."""
    print("\n[#23] WHO IS COUNTED — 65+ share and MEDIAN AGE")
    print(f"{'electorate':34}{'65+':>8}{'median age':>12}")
    base = con.execute("""
        WITH e AS (SELECT (2026 - EXTRACT(year FROM birthdate)) age FROM voters
                   WHERE birthdate IS NOT NULL AND (2026 - EXTRACT(year FROM birthdate))>=18)
        SELECT SUM(CASE WHEN age>=65 THEN 1 ELSE 0 END)*1.0/COUNT(*), MEDIAN(age) FROM e""").fetchone()
    print(f"{'Registered roll (April 2026)':34}{base[0]*100:>7.1f}%{base[1]:>12.0f}")
    for date, kind in [("2024-11-05", "presidential"), ("2022-11-08", "midterm"),
                       ("2021-11-02", "off-year"), ("2023-11-07", "off-year"),
                       ("2025-11-04", "off-year")]:
        yr = int(date[:4]); a = f"({yr} - EXTRACT(year FROM v.birthdate))"
        # same eligibility as the composition/rate tables (registered on/before E)
        r = con.execute(f"""
            WITH e AS (SELECT {a} age
                       FROM (SELECT DISTINCT state_voter_id FROM voting_history
                             WHERE election_date=DATE '{date}') h
                       JOIN voters v USING (state_voter_id)
                       WHERE v.birthdate IS NOT NULL AND {a}>=18
                         AND v.registration_date IS NOT NULL
                         AND v.registration_date <= DATE '{date}')
            SELECT SUM(CASE WHEN age>=65 THEN 1 ELSE 0 END)*1.0/COUNT(*), MEDIAN(age) FROM e""").fetchone()
        print(f"{date+' '+kind+' returners':34}{r[0]*100:>7.1f}%{r[1]:>12.0f}")


def county_65plus(con):
    """#24: 65+ share of the ballot-returning electorate by county, 2024/2023/2025.
    Rebuts "it's just King / just rural" — the gradient holds in all 39 counties."""
    print("\n[#24] 65+ SHARE OF ELECTORATE BY COUNTY (all 39; pres 2024 vs off 2023/2025)")
    print(f"{'county':16}{'2024':>8}{'2023':>8}{'2025':>8}{'pres->off':>11}")

    def sh(date, yr, county):
        a = f"({yr} - EXTRACT(year FROM v.birthdate))"
        r = con.execute(f"""
            WITH e AS (SELECT {a} age
                FROM (SELECT DISTINCT state_voter_id FROM voting_history
                      WHERE election_date=DATE '{date}') h
                JOIN voters v USING (state_voter_id)
                WHERE v.birthdate IS NOT NULL AND {a}>=18 AND UPPER(v.county_name)='{county}')
            SELECT SUM(CASE WHEN age>=65 THEN 1 ELSE 0 END)*1.0/NULLIF(COUNT(*),0) FROM e""").fetchone()[0]
        return (r or 0) * 100

    counties = [x[0] for x in con.execute(
        "SELECT DISTINCT UPPER(county_name) FROM voters WHERE county_name IS NOT NULL"
    ).fetchall()]
    rows = []
    for co in counties:
        p = sh("2024-11-05", 2024, co); o23 = sh("2023-11-07", 2023, co); o25 = sh("2025-11-04", 2025, co)
        rows.append((co, p, o23, o25, (o23 + o25) / 2 - p))
    allpos = all(r[4] > 0 for r in rows)
    for co, p, o23, o25, gap in sorted(rows, key=lambda x: -x[1]):
        print(f"{co:16}{p:>7.1f}%{o23:>7.1f}%{o25:>7.1f}%{gap:>+10.1f}")
    print(f"  presidential->off-year senior gap POSITIVE in all {len(rows)} counties? "
          f"{'YES' if allpos else 'NO'}")


def habitual_core(con):
    """#25: the off-year electorate is the presidential electorate's habitual core.
    (a) overlap each off-year <-> 2024 pres; (b) peripheral droppers (2024 pres, not the
    2023 off-year) vs the core, age as of 2024; (c) median registration tenure by cycle."""
    print("\n[#25] HABITUAL CORE vs PERIPHERAL DROPPERS + registration tenure")
    pres = "2024-11-05"
    for date in ["2021-11-02", "2023-11-07", "2025-11-04"]:
        no, inter, npres = con.execute(f"""
            WITH o AS (SELECT DISTINCT state_voter_id FROM voting_history WHERE election_date=DATE '{date}'),
                 p AS (SELECT DISTINCT state_voter_id FROM voting_history WHERE election_date=DATE '{pres}')
            SELECT (SELECT COUNT(*) FROM o),
                   (SELECT COUNT(*) FROM o JOIN p USING(state_voter_id)),
                   (SELECT COUNT(*) FROM p)""").fetchone()
        print(f"  {date}: {inter/no*100:.1f}% of off-year voters also voted 2024 pres; "
              f"{inter/npres*100:.1f}% of 2024 pres voters voted this off-year")
    off = "2023-11-07"
    rows = con.execute(f"""
        WITH p AS (SELECT DISTINCT state_voter_id FROM voting_history WHERE election_date=DATE '{pres}'),
             o AS (SELECT DISTINCT state_voter_id FROM voting_history WHERE election_date=DATE '{off}'),
             grp AS (
               SELECT CASE WHEN o.state_voter_id IS NOT NULL THEN 'core (voted both)'
                           ELSE 'dropper (pres only)' END g,
                      date_diff('year', v.birthdate, DATE '{pres}') age
               FROM p JOIN voters v USING(state_voter_id)
               LEFT JOIN o ON o.state_voter_id = v.state_voter_id
               WHERE v.birthdate IS NOT NULL AND date_diff('year', v.birthdate, DATE '{pres}') >= 18)
        SELECT g, SUM(CASE WHEN age>=65 THEN 1 ELSE 0 END)*1.0/COUNT(*),
                  SUM(CASE WHEN age<30 THEN 1 ELSE 0 END)*1.0/COUNT(*), COUNT(*)
        FROM grp GROUP BY 1 ORDER BY 1""").fetchall()
    print("  2024 pres voters split by whether they also voted the 2023 off-year:")
    for g, s65, s1829, n in rows:
        print(f"    {g:22} (n={n:,}): 65+ {s65*100:.1f}%  18-29 {s1829*100:.1f}%")
    print("  median registration tenure (yrs) at the election:")
    for date, kind in ELECTIONS:
        med = con.execute(f"""
            SELECT MEDIAN(date_diff('year', v.registration_date, DATE '{date}'))
            FROM (SELECT DISTINCT state_voter_id FROM voting_history WHERE election_date=DATE '{date}') h
            JOIN voters v USING(state_voter_id)
            WHERE v.registration_date IS NOT NULL AND v.registration_date <= DATE '{date}'""").fetchone()[0]
        print(f"    {date} {kind:12} {med:.0f} yrs")


def snapshot_crossval(con):
    """#26: reconstruct the 2021/22/23 electorate 65+ share from the Sept-2023 snapshot
    (voters_20230901, which still holds pre-2026 leavers) and compare to the current roll.
    Near-equality shows survivorship does not DISTORT composition (beyond the formal bound).
    2021/2022 are the cleanest (snapshot postdates them); the 2023 snapshot predates the
    Nov election by ~2 months, missing younger late-2023 registrants, so its 65+ share is
    if anything biased slightly UPWARD."""
    print("\n[#26] SNAPSHOT CROSS-VALIDATION — 65+ share: current roll vs Sept-2023 snapshot")
    print(f"{'election':12}{'type':13}{'current 65+':>13}{'snap-2023 65+':>15}{'delta':>8}")
    for date, kind in [("2021-11-02", "off-year"), ("2022-11-08", "midterm"), ("2023-11-07", "off-year")]:
        def s65(tbl):
            return con.execute(f"""
                WITH e AS (SELECT date_diff('year', v.birthdate, DATE '{date}') age
                    FROM (SELECT DISTINCT state_voter_id FROM voting_history WHERE election_date=DATE '{date}') h
                    JOIN {tbl} v USING(state_voter_id)
                    WHERE v.birthdate IS NOT NULL AND date_diff('year', v.birthdate, DATE '{date}')>=18)
                SELECT SUM(CASE WHEN age>=65 THEN 1 ELSE 0 END)*1.0/COUNT(*) FROM e""").fetchone()[0] * 100
        cur, snap = s65("voters"), s65("voters_20230901")
        print(f"{date:12}{kind:13}{cur:>12.1f}%{snap:>14.1f}%{snap-cur:>+8.1f}")


def gender_share(con):
    """#28: female share of the electorate by cycle (gender 98.6% populated)."""
    print("\n[#28] GENDER — female share of the electorate by cycle")
    print(f"{'election':12}{'type':13}{'%F':>7}{'%M':>7}{'%F among 65+':>14}")
    for date, kind in ELECTIONS:
        r = con.execute(f"""
            WITH e AS (SELECT v.gender g, date_diff('year', v.birthdate, DATE '{date}') age
                FROM (SELECT DISTINCT state_voter_id FROM voting_history WHERE election_date=DATE '{date}') h
                JOIN voters v USING(state_voter_id)
                WHERE v.gender IN ('F','M') AND v.birthdate IS NOT NULL
                  AND date_diff('year', v.birthdate, DATE '{date}')>=18)
            SELECT SUM(CASE WHEN g='F' THEN 1 ELSE 0 END)*1.0/COUNT(*),
                   SUM(CASE WHEN g='M' THEN 1 ELSE 0 END)*1.0/COUNT(*),
                   SUM(CASE WHEN g='F' AND age>=65 THEN 1 ELSE 0 END)*1.0
                     /NULLIF(SUM(CASE WHEN age>=65 THEN 1 ELSE 0 END),0)
            FROM e""").fetchone()
        print(f"{date:12}{kind:13}{r[0]*100:>6.1f}%{r[1]*100:>6.1f}%{r[2]*100:>13.1f}%")


def representativeness(con):
    """#29: index of dissimilarity between each electorate's age distribution and the CVAP
    age distribution (ACS 2020-24, table B29001). D = 0.5 * sum |electorate_c - CVAP_c|."""
    print("\n[#29] REPRESENTATIVENESS — index of dissimilarity vs CVAP (0=identical)")
    cvap = {"18-29": 19.8, "30-44": 26.7, "45-64": 30.9, "65+": 22.6}
    for date, kind in ELECTIONS:
        comp = con.execute(f"""
            WITH e AS (SELECT CASE WHEN date_diff('year', v.birthdate, DATE '{date}')<30 THEN '18-29'
                                   WHEN date_diff('year', v.birthdate, DATE '{date}')<45 THEN '30-44'
                                   WHEN date_diff('year', v.birthdate, DATE '{date}')<65 THEN '45-64'
                                   ELSE '65+' END coh
                FROM (SELECT DISTINCT state_voter_id FROM voting_history WHERE election_date=DATE '{date}') h
                JOIN voters v USING(state_voter_id)
                WHERE v.birthdate IS NOT NULL AND date_diff('year', v.birthdate, DATE '{date}')>=18)
            SELECT coh, COUNT(*)*100.0/SUM(COUNT(*)) OVER () FROM e GROUP BY 1""").fetchall()
        d = {c: p for c, p in comp}
        diss = 0.5 * sum(abs(d.get(c, 0) - cvap[c]) for c in BUCKETS)
        print(f"  {date} {kind:12} dissimilarity index {diss:.1f}")


def main():
    con = duckdb.connect(VRDB, read_only=True)

    v, bd = con.execute("SELECT COUNT(*), COUNT(birthdate) FROM voters").fetchone()
    vh = con.execute("SELECT COUNT(*) FROM voting_history").fetchone()[0]
    # Provenance check: the birth field is YEAR-only (every value is a July-1
    # sentinel), so we carry year of birth, not full date of birth.
    jul1 = con.execute("SELECT COUNT(*) FROM voters WHERE birthdate IS NOT NULL "
                       "AND EXTRACT(month FROM birthdate)=7 AND EXTRACT(day FROM birthdate)=1"
                       ).fetchone()[0]
    print(f"[#7] roll {v:,} | year-of-birth coverage {bd/v*100:.1f}% "
          f"(July-1 sentinel {jul1/bd*100:.1f}% => YEAR only, not full DOB) | vote records {vh:,}")
    print("=" * 92)

    rate, share = {}, {}
    print("[#1-#3] WITHIN-COHORT TURNOUT RATE")
    print(f"{'election':12}{'type':13}" + "".join(f"{b:>9}" for b in BUCKETS) + f"{'ALL':>9}")
    for date, kind in ELECTIONS:
        t = cohort_table(con, date)
        tot_r = sum(r for r, _ in t.values()); tot_v = sum(vv for _, vv in t.values())
        rate[date] = {c: t[c][1] / t[c][0] * 100 for c in t}
        share[date] = {c: t[c][1] / tot_v * 100 for c in t}
        print(f"{date:12}{kind:13}" + "".join(f"{rate[date].get(b,0):8.1f}%" for b in BUCKETS)
              + f"{tot_v/tot_r*100:8.1f}%")

    print("\n[#4-#5] COHORT SHARE OF THE ACTUAL ELECTORATE (denominator-free, the robust cut)")
    print(f"{'election':12}{'type':13}" + "".join(f"{b:>9}" for b in BUCKETS))
    for date, kind in ELECTIONS:
        print(f"{date:12}{kind:13}" + "".join(f"{share[date].get(b,0):8.1f}%" for b in BUCKETS))

    offavg = lambda st, b: sum(st[d][b] for d in ["2021-11-02", "2023-11-07", "2025-11-04"]) / 3
    print(f"\n[#6] senior:youth share ratio  pres {share[PRES]['65+']/share[PRES]['18-29']:.1f}:1"
          f"  ->  off-year {offavg(share,'65+')/offavg(share,'18-29'):.1f}:1")

    # ---- validation + sensitivity (reviewer-response additions) ----
    coverage_table(con)
    survivorship(con)
    bounding(con)
    finer_cohorts(con)
    imputation(con)
    geography(con)
    who_is_counted(con)
    county_65plus(con)
    habitual_core(con)
    snapshot_crossval(con)
    gender_share(con)
    representativeness(con)

    # ---- Das-Gupta symmetric two-factor decomposition (behavior vs rolls) ----
    P = cohort_table(con, PRES)
    Os = {lab: cohort_table(con, d) for d, lab in
          [("2025-11-04", "2025"), ("2023-11-07", "2023"), ("2021-11-02", "2021")]}
    con.close()
    rollP = {c: P[c][0] for c in BUCKETS}; rateP = {c: P[c][1] / P[c][0] for c in BUCKETS}

    print("\n" + "=" * 92)
    print("[#8-#10] BEHAVIOR-vs-ROLLS DECOMPOSITION (2024 pres -> each off-year)")
    for lab in ["2025", "2023", "2021"]:
        O = Os[lab]
        rollO = {c: O[c][0] for c in BUCKETS}; rateO = {c: O[c][1] / O[c][0] for c in BUCKETS}
        for target in (["65+", "18-29"] if lab == "2025" else ["65+"]):
            S_PP = elect_share(rollP, rateP, target); S_OO = elect_share(rollO, rateO, target)
            S_OP = elect_share(rollO, rateP, target); S_PO = elect_share(rollP, rateO, target)
            comp = 0.5 * ((S_OP - S_PP) + (S_OO - S_PO))   # roll-composition effect
            beh = 0.5 * ((S_PO - S_PP) + (S_OO - S_OP))    # turnout-rate (behavior) effect
            tot = (S_OO - S_PP) * 100
            print(f"  2024->{lab} {target}: {S_PP*100:.1f}% -> {S_OO*100:.1f}%  (change {tot:+.1f}pp) "
                  f"= behavior {beh*100:+.1f}pp ({abs(beh)/(abs(beh)+abs(comp))*100:.0f}%) "
                  f"+ rolls {comp*100:+.1f}pp")
    O25 = Os["2025"]; rate25 = {c: O25[c][1] / O25[c][0] for c in BUCKETS}
    print(f"  [#10] off-cycle retention (2025):  65+ keep {rate25['65+']/rateP['65+']*100:.0f}% of "
          f"presidential turnout | 18-29 keep {rate25['18-29']/rateP['18-29']*100:.0f}%")


if __name__ == "__main__":
    main()
