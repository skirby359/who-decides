"""Independent re-derivation of the headline numbers in docs/who-decides-idaho.md.

Companion to verify_who_decides_wa.py. Hits data/id_vrdb.duckdb (voters +
voter_participation) DIRECTLY with from-scratch SQL — not by importing the diag
scripts — so a match against the paper confirms it independently of the analysis
code. Contested-primary + safe-seat-by-registration also touch id_statewide.duckdb
(ATTACHed read-only). Read-only; aggregate output only (voter file carries PII;
Idaho Code §74-120).

Idaho gives current age (as of the 2026 snapshot), not DOB, so election-time age
is `age - (2026 - year)`, accurate to ~1yr — bands only. Party-of-record buckets:
REP / DEM / UNAFF (unaffiliated) / OTHER (Lib/Con). Prints derived-vs-paper.

Covers §I (age composition by cycle), §II (party-neutral age gap), §III
(unaffiliated: roll -> general -> primary), §IV (closed-primary R ballot share +
contested count), §V (safe-seat by registration). The donor layer (§VII) is in
verify_donor_class.py; turnout RATES are deliberately NOT reproduced (the paper
reports composition shares only — the roll shrank 1.18M->1.03M since 2024).

Run:  python scripts/verify_who_decides_id.py
"""
from pathlib import Path
import sys

import duckdb

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

ROOT = Path(__file__).resolve().parent.parent
VRDB = str(ROOT / "data" / "id_vrdb.duckdb")
STATEWIDE = str(ROOT / "data" / "id_statewide.duckdb")
BANDS = ["18-29", "30-44", "45-64", "65+"]
PARTY = ("CASE WHEN party='REP' THEN 'REP' WHEN party='DEM' THEN 'DEM' "
         "WHEN party='UNA' THEN 'UNAFF' ELSE 'OTHER' END")
_AGE = "(v.age - (2026 - {yr}))"


def _band(agesql):
    return (f"CASE WHEN {agesql}<30 THEN '18-29' WHEN {agesql}<45 THEN '30-44' "
            f"WHEN {agesql}<65 THEN '45-64' ELSE '65+' END")


def age_comp(con, year, kind="GENERAL"):
    """Composition: share of `kind`-`year` voters by age band (age as of election)."""
    ag = _AGE.format(yr=year)
    rows = con.execute(f"""
        WITH e AS (SELECT {_band(ag)} band FROM voters v
                   JOIN (SELECT DISTINCT state_voter_id FROM voter_participation
                         WHERE election_year={year} AND kind='{kind}') p USING (state_voter_id)
                   WHERE v.age IS NOT NULL AND {ag} BETWEEN 18 AND 105)
        SELECT band, COUNT(*) n FROM e GROUP BY 1
    """).fetchall()
    d = {b: 0 for b in BANDS}
    for b, n in rows:
        d[b] = n
    tot = sum(d.values()) or 1
    med = con.execute(f"""SELECT median({ag}) FROM voters v
        JOIN (SELECT DISTINCT state_voter_id FROM voter_participation
              WHERE election_year={year} AND kind='{kind}') p USING (state_voter_id)
        WHERE v.age IS NOT NULL AND {ag} BETWEEN 18 AND 105""").fetchone()[0]
    return {b: 100.0 * d[b] / tot for b in BANDS}, med


def party_mix(con, where_join):
    """Party-of-record mix (%) over a voter set defined by `where_join` SQL."""
    rows = con.execute(f"""
        SELECT {PARTY} p, COUNT(*) n FROM voters v {where_join} GROUP BY 1
    """).fetchall()
    d = {}
    for p, n in rows:
        d[p] = d.get(p, 0) + n
    tot = sum(d.values()) or 1
    return {k: 100.0 * v / tot for k, v in d.items()}, tot


def main():
    con = duckdb.connect(VRDB, read_only=True)

    n_roll = con.execute("SELECT COUNT(*) FROM voters").fetchone()[0]
    print(f"roll {n_roll:,}   (paper: 1,029,938)")
    print("=" * 80)

    roll, _ = party_mix(con, "")
    print("[roll party mix]  (paper: REP 62.9 / UNAFF 23.9 / DEM 11.8)")
    print("   " + "  ".join(f"{k} {roll.get(k,0):.1f}%" for k in ["REP", "UNAFF", "DEM", "OTHER"]))

    print("\n[§I] AGE COMPOSITION of the general electorate by cycle")
    print("  (paper 2024: 15.2 / 23.4 / 32.4 / 29.0, median 52)")
    print(f"  {'cycle':>6} " + "".join(f"{b:>9}" for b in BANDS) + f"{'median':>8}")
    for yr in (2024, 2022, 2020):
        comp, med = age_comp(con, yr)
        print(f"  {yr:>6} " + "".join(f"{comp[b]:8.1f}%" for b in BANDS) + f"{med:8.0f}")

    print("\n[§II] PARTY-NEUTRAL AGE GAP — 65+ share & median by party, 2024 general")
    print("  (paper: 65+ REP 31.7 ≈ DEM 31.5 ; median REP 54 / DEM 50 / UNAFF 46)")
    ag = _AGE.format(yr=2024)
    rows = con.execute(f"""
        WITH e AS (SELECT {PARTY} p, {ag} a FROM voters v
                   JOIN (SELECT DISTINCT state_voter_id FROM voter_participation
                         WHERE election_year=2024 AND kind='GENERAL') x USING (state_voter_id)
                   WHERE v.age IS NOT NULL AND {ag} BETWEEN 18 AND 105)
        SELECT p, 100.0*COUNT(*) FILTER(WHERE a>=65)/COUNT(*) p65, median(a) med
        FROM e GROUP BY 1
    """).fetchall()
    for p, p65, med in sorted(rows):
        print(f"     {p:6} 65+ {p65:5.1f}%   median {med:.0f}")

    print("\n[§III] UNAFFILIATED share: roll -> 2024 general -> 2024 primary electorate")
    print("  (paper: 23.9% -> 22.6% -> 5.9%)")
    gen, _ = party_mix(con, """JOIN (SELECT DISTINCT state_voter_id FROM voter_participation
             WHERE election_year=2024 AND kind='GENERAL') p USING (state_voter_id)""")
    pri, _ = party_mix(con, """JOIN (SELECT DISTINCT state_voter_id FROM voter_participation
             WHERE election_year=2024 AND kind='PRIMARY') p USING (state_voter_id)""")
    print(f"     UNAFF  roll {roll.get('UNAFF',0):.1f}%  ->  general {gen.get('UNAFF',0):.1f}%"
          f"  ->  primary {pri.get('UNAFF',0):.1f}%")

    print("\n[§IV] CLOSED PRIMARY — Republican share of 2024 primary ballots pulled")
    print("  (paper: 80-86% of primary ballots are Republican)")
    bc = con.execute("""
        SELECT 100.0*COUNT(*) FILTER(WHERE ballot_choice='REP')/COUNT(*)
        FROM voter_participation WHERE election_year=2024 AND kind='PRIMARY'
          AND ballot_choice IS NOT NULL
    """).fetchone()[0]
    print(f"     2024 primary ballots Republican: {bc:.1f}%")

    print("\n[§V] SAFE-SEAT by registration — legislative districts by REP%-DEM% lean")
    print("  (paper: all 35 LDs lean R — 27 Safe / 4 Likely / 4 Lean; 0 competitive, 0 D)")
    leans = con.execute(f"""
        WITH ld AS (
            SELECT legislative_district d,
                   100.0*COUNT(*) FILTER(WHERE party='REP')/COUNT(*)
                   - 100.0*COUNT(*) FILTER(WHERE party='DEM')/COUNT(*) net
            FROM voters v WHERE legislative_district IS NOT NULL
            GROUP BY 1)
        SELECT COUNT(*) FILTER(WHERE net>=40) safe_r,
               COUNT(*) FILTER(WHERE net>=20 AND net<40) likely_r,
               COUNT(*) FILTER(WHERE net>=5 AND net<20) lean_r,
               COUNT(*) FILTER(WHERE net> -5 AND net<5) comp,
               COUNT(*) FILTER(WHERE net<=-5) any_d,
               COUNT(*) n FROM ld
    """).fetchone()
    print(f"     Safe R {leans[0]} | Likely R {leans[1]} | Lean R {leans[2]} | "
          f"Competitive {leans[3]} | any D-lean {leans[4]}   (of {leans[5]} LDs)")

    # Contested-primary count needs the results DB (races/candidates).
    con.execute(f"ATTACH '{STATEWIDE}' AS sw (READ_ONLY)")
    print("\n[§IV] CONTESTED Republican legislative primaries, 2024  (paper: 99 races, 52 contested)")
    row = con.execute("""
        WITH rr AS (
            SELECT ra.race_id, COUNT(DISTINCT pr.candidate_id) nc
            FROM sw.elections e JOIN sw.races ra ON ra.election_id=e.election_id
            JOIN sw.precinct_results pr ON pr.race_id=ra.race_id
            WHERE e.election_type='primary' AND e.election_date=DATE '2024-05-21'
              AND UPPER(ra.race_name) LIKE '%REPUBLICAN%'
              AND (UPPER(ra.race_name) LIKE '%LEGISLATIVE DISTRICT%'
                   OR (UPPER(ra.race_name) LIKE '%REPRESENTATIVE DISTRICT%' AND UPPER(ra.race_name) LIKE '%SEAT%')
                   OR UPPER(ra.race_name) LIKE '%SENATOR DISTRICT%')
            GROUP BY 1)
        SELECT COUNT(*), COUNT(*) FILTER(WHERE nc>=2) FROM rr
    """).fetchone()
    print(f"     {row[0]} Republican legislative primaries, {row[1]} contested")
    con.close()


if __name__ == "__main__":
    main()
