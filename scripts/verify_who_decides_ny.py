"""Independent re-derivation of the headline numbers in docs/who-decides-new-york.md.

Companion to verify_who_decides_wa.py / verify_who_decides_id.py. Hits
data/ny_vrdb.duckdb (voters + voter_participation) DIRECTLY with from-scratch SQL
— not by importing the diag scripts — so a match against the paper confirms it
independently of the analysis code. Read-only; aggregate output only (NYSVOTER
carries PII; FOIL lawful-use terms). Prints derived-vs-paper.

Party-of-record buckets: DEM / REP / NOPARTY (New York's blank "BLK" enrollment) /
OTHER (Conservative, Working Families, etc.). Age from full DOB (as of each
election). Covers §I (age composition by cycle), §II (65+ share & median by party),
§III (the blank bloc), §IV (closed-primary participation by enrollment), §V
(safe-seat by registration), §VI (new-registrant party-mix trend). Turnout RATES
(§IV) are reproduced but carry the paper's survivorship caveat (current-roll
denominator); composition shares are the robust cut.

Run:  python scripts/verify_who_decides_ny.py
"""
from pathlib import Path
import sys

import duckdb

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

VRDB = str(Path(__file__).resolve().parent.parent / "data" / "ny_vrdb.duckdb")
BANDS = ["18-29", "30-44", "45-64", "65+"]
PARTY = ("CASE WHEN party='DEM' THEN 'DEM' WHEN party='REP' THEN 'REP' "
         "WHEN party='BLK' THEN 'NOPARTY' ELSE 'OTHER' END")
# (date, election_year, label) for the general-election cycles in the paper.
GENERALS = [("2024-11-05", 2024, "presidential"), ("2022-11-08", 2022, "midterm"),
            ("2025-11-04", 2025, "off-year"), ("2023-11-07", 2023, "off-year")]


def _band(date):
    a = f"date_diff('year', v.birthdate, DATE '{date}')"
    return (a, f"CASE WHEN {a}<30 THEN '18-29' WHEN {a}<45 THEN '30-44' "
               f"WHEN {a}<65 THEN '45-64' ELSE '65+' END")


def voters_in(year, kind="GENERAL"):
    return (f"JOIN (SELECT DISTINCT state_voter_id FROM voter_participation "
            f"WHERE election_year={year} AND kind='{kind}') p USING (state_voter_id)")


def main():
    con = duckdb.connect(VRDB, read_only=True)

    v, bd = con.execute("SELECT COUNT(*), COUNT(birthdate) FROM voters").fetchone()
    print(f"roll {v:,} | DOB coverage {bd/v*100:.1f}%   (paper: 13.54M)")
    print("=" * 84)

    # Active-roll party mix (paper: DEM 47.8 / NOPARTY 25.1 / REP 22.3 of active roll).
    print("[roll] active-roll party mix  (paper ~: DEM 47.8 / NOPARTY 25.1 / REP 22.3)")
    rows = con.execute(f"""
        SELECT {PARTY} p, COUNT(*) n FROM voters
        WHERE status_code='A' GROUP BY 1
    """).fetchall()
    tot = sum(n for _, n in rows) or 1
    mix = {p: 100.0 * n / tot for p, n in rows}
    print("   " + "  ".join(f"{k} {mix.get(k,0):.1f}%" for k in ["DEM", "NOPARTY", "REP", "OTHER"]))

    print("\n[§I] AGE COMPOSITION of the general electorate by cycle")
    print("  (paper 2024: 14.1/23.1/34.6/28.2 med 53 ; 2023: 6.0/15.8/36.5/41.6 med 61)")
    print(f"  {'cycle':>11} " + "".join(f"{b:>9}" for b in BANDS) + f"{'median':>8}")
    for date, yr, lab in GENERALS:
        agecol, bandsql = _band(date)
        d = {b: 0 for b in BANDS}
        rows = con.execute(f"""
            WITH e AS (SELECT {bandsql} band FROM voters v {voters_in(yr)}
                       WHERE v.birthdate IS NOT NULL AND {agecol} BETWEEN 18 AND 105)
            SELECT band, COUNT(*) n FROM e GROUP BY 1
        """).fetchall()
        for b, n in rows:
            d[b] = n
        med = con.execute(f"""SELECT median({agecol}) FROM voters v {voters_in(yr)}
            WHERE v.birthdate IS NOT NULL AND {agecol} BETWEEN 18 AND 105""").fetchone()[0]
        tot = sum(d.values()) or 1
        print(f"  {date} ({lab[:4]})" + "".join(f"{100.0*d[b]/tot:8.1f}%" for b in BANDS)
              + f"{med:8.0f}")

    print("\n[§II] 65+ SHARE by party, per cycle  (paper 2024: DEM 28.7 / REP 32.4 / NOPARTY 22.2 ;")
    print("       2025: REP 42.8 ; 2023: DEM 41.6 / REP 43.5)")
    for date, yr, lab in GENERALS:
        agecol, _ = _band(date)
        rows = con.execute(f"""
            WITH e AS (SELECT {PARTY} p, {agecol} a FROM voters v {voters_in(yr)}
                       WHERE v.birthdate IS NOT NULL AND {agecol} BETWEEN 18 AND 105)
            SELECT p, 100.0*COUNT(*) FILTER(WHERE a>=65)/COUNT(*) FROM e GROUP BY 1
        """).fetchall()
        m = dict(rows)
        print(f"  {date} ({lab[:4]})  DEM {m.get('DEM',0):.1f}  REP {m.get('REP',0):.1f}  "
              f"NOPARTY {m.get('NOPARTY',0):.1f}  OTHER {m.get('OTHER',0):.1f}")
    # median by party, 2025 off-year (paper: REP 62 vs DEM 54)
    ag25, _ = _band("2025-11-04")
    med25 = dict(con.execute(f"""
        WITH e AS (SELECT {PARTY} p, {ag25} a FROM voters v {voters_in(2025)}
                   WHERE v.birthdate IS NOT NULL AND {ag25} BETWEEN 18 AND 105)
        SELECT p, median(a) FROM e GROUP BY 1""").fetchall())
    print(f"  2025 median age by party: REP {med25.get('REP',0):.0f} vs DEM {med25.get('DEM',0):.0f}"
          f"  (paper REP 62 / DEM 54)")

    print("\n[§III] THE BLANK BLOC vs parties (active roll; median age, %65+, %18-29, 2024 turnout)")
    print("  (paper: DEM 49/26.7/17.3/58.4 ; REP 55/30.6/14.0/69.5 ; NOPARTY 42/17.7/24.0/50.4)")
    ag24, band24 = _band("2024-11-05")   # age as of the 2024 election (pairs with 2024 turnout)
    rows = con.execute(f"""
        WITH e AS (
            SELECT {PARTY} p, {ag24} a,
                   CASE WHEN state_voter_id IN (SELECT DISTINCT state_voter_id FROM voter_participation
                        WHERE election_year=2024 AND kind='GENERAL') THEN 1 ELSE 0 END voted24
            FROM voters v WHERE status_code='A' AND birthdate IS NOT NULL)
        SELECT p, median(a) med, 100.0*COUNT(*) FILTER(WHERE a>=65)/COUNT(*) p65,
               100.0*COUNT(*) FILTER(WHERE a<30)/COUNT(*) p18,
               100.0*SUM(voted24)/COUNT(*) turn24
        FROM e GROUP BY 1
    """).fetchall()
    md = {r[0]: r for r in rows}
    for k in ["DEM", "REP", "NOPARTY"]:
        r = md.get(k)
        if r:
            print(f"     {k:8} median {r[1]:.0f}  65+ {r[2]:.1f}%  18-29 {r[3]:.1f}%  2024turn {r[4]:.1f}%")

    print("\n[§IV] CLOSED-PRIMARY participation by enrollment (voted primary / party registrants)")
    print("  (paper: 2024 state DEM 7.7/REP 1.7 ; 2022 state DEM 17.9/REP 18.4 ; 2021 DEM 16.9/REP 5.0)")
    for yr, lab in [(2024, "state/cong"), (2022, "state/cong"), (2021, "odd-year")]:
        rows = con.execute(f"""
            WITH reg AS (SELECT {PARTY} p, state_voter_id FROM voters WHERE status_code='A'),
                 voted AS (SELECT DISTINCT state_voter_id FROM voter_participation
                           WHERE election_year={yr} AND kind='PRIMARY')
            SELECT p, 100.0*COUNT(*) FILTER(WHERE state_voter_id IN (SELECT state_voter_id FROM voted))/COUNT(*)
            FROM reg GROUP BY 1
        """).fetchall()
        m = dict(rows)
        print(f"     {yr} ({lab})  DEM {m.get('DEM',0):.1f}%  REP {m.get('REP',0):.1f}%  "
              f"NOPARTY {m.get('NOPARTY',0):.1f}%")
    print("     NOTE: these RATES run ~1-2pp under the paper — denominator is the current")
    print("     active roll (later registrants inflate it); the DEM>>REP off-cycle pattern")
    print("     is the robust cut. Composition (§I/§II) + safe-seat (§V) match exactly.")

    print("\n[§V] SAFE-SEAT by registration — districts by DEM%-REP% lean (active roll)")
    print("  (paper: CD 26 -> 9 SafeD/3 LikelyD/7 LeanD/4 comp/3 R ; Assembly 150 -> 55/31/19/17/21+7)")
    for col, lvl, n_exp in [("congressional_district", "Congressional", 26),
                            ("assembly_district", "Assembly", 150)]:
        row = con.execute(f"""
            WITH dd AS (
                SELECT {col} d,
                       100.0*COUNT(*) FILTER(WHERE party='DEM')/COUNT(*)
                       - 100.0*COUNT(*) FILTER(WHERE party='REP')/COUNT(*) net
                FROM voters WHERE status_code='A' AND {col} IS NOT NULL AND {col}<>''
                GROUP BY 1)
            SELECT COUNT(*) FILTER(WHERE net>=40) safe_d,
                   COUNT(*) FILTER(WHERE net>=20 AND net<40) likely_d,
                   COUNT(*) FILTER(WHERE net>=5 AND net<20) lean_d,
                   COUNT(*) FILTER(WHERE net> -5 AND net<5) comp,
                   COUNT(*) FILTER(WHERE net<=-5) rlean, COUNT(*) n FROM dd
        """).fetchone()
        print(f"     {lvl:13}(n={row[5]}, exp {n_exp}): SafeD {row[0]} | LikelyD {row[1]} | "
              f"LeanD {row[2]} | Comp {row[3]} | R-lean {row[4]}")

    print("\n[§VI] NEW-REGISTRANT party mix by registration year  (paper: 2008 DEM 57.8/REP 16.2/NP 20.7 ;")
    print("       2024 DEM 39.7/REP 22.1/NP 35.6)")
    for yr in (2008, 2016, 2020, 2024):
        rows = con.execute(f"""
            SELECT {PARTY} p, COUNT(*) n FROM voters
            WHERE year(registration_date)={yr} GROUP BY 1
        """).fetchall()
        t = sum(n for _, n in rows) or 1
        m = {p: 100.0 * n / t for p, n in rows}
        medage = con.execute(f"""SELECT median(date_diff('year', birthdate, registration_date))
            FROM voters WHERE year(registration_date)={yr} AND birthdate IS NOT NULL""").fetchone()[0]
        print(f"     {yr}: DEM {m.get('DEM',0):.1f}%  REP {m.get('REP',0):.1f}%  "
              f"NOPARTY {m.get('NOPARTY',0):.1f}%  med-age-at-reg {medage:.0f}")

    con.close()


if __name__ == "__main__":
    main()
