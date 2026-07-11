"""Electoral-health: Idaho turnout by age x PARTY-OF-RECORD + closed-primary.

The deep-RED party-resolved companion to the WA "who decides" finding and the
NY party-resolved run. Idaho differs from NY in two ways that shape the story:

  1. **Age, not DOB.** `voters.age` is current (2026-06-29). Election-time age
     is approximated as `age - (2026 - election_year)` — accurate to ~1y, fine
     for bands. We never claim exact ages.
  2. **The decisive contest is a CLOSED PRIMARY.** In an R+40 state the GOP
     primary, not the November general, chooses nearly every officeholder.
     Idaho's GOP primary is closed to registered Republicans (Democrats opened
     theirs to unaffiliated); the file records which party ballot each primary
     voter pulled (`voter_participation.ballot_choice`). Section E is the Idaho
     flagship — the mirror of NY's "DEM primary is the decisive contest."

Survivorship caveat: the file is the CURRENT roll, so past-election turnout
RATES are biased high for older cycles (purged/moved voters absent). We lead
with composition SHARES (robust) and report rates with the caveat.

Usage:
    python scripts/diag_id_turnout_party.py         # (duckdb only; no PYTHONPATH)
"""
import duckdb

ID_VRDB = "data/id_vrdb.duckdb"

# General elections available in the file (no odd-year local history here).
GENERALS = [
    (2024, "2024 GENERAL (presidential)"),
    (2022, "2022 GENERAL (midterm)"),
    (2020, "2020 GENERAL (presidential)"),
]
PRIMARIES = [
    (2026, "2026 PRIMARY (May)"),
    (2024, "2024 PRIMARY (May)"),
    (2022, "2022 PRIMARY (May)"),
]

# Party buckets: REP / DEM / UNAFF (unaffiliated) / OTHER (Lib + Con).
PARTY_CASE = """
    CASE WHEN v.party='REP' THEN 'REP' WHEN v.party='DEM' THEN 'DEM'
         WHEN v.party='UNA' THEN 'UNAFF' ELSE 'OTHER' END
"""
PARTIES = ["REP", "DEM", "UNAFF", "OTHER"]
AGE_BANDS = ["18-29", "30-44", "45-64", "65+"]

# election-time age from current (2026) age.
def _agex(year: int) -> str:
    return f"(v.age - ({2026 - year}))"


def _band(expr: str) -> str:
    return f"""
        CASE WHEN {expr} BETWEEN 18 AND 29 THEN '18-29'
             WHEN {expr} BETWEEN 30 AND 44 THEN '30-44'
             WHEN {expr} BETWEEN 45 AND 64 THEN '45-64'
             WHEN {expr} BETWEEN 65 AND 105 THEN '65+' ELSE NULL END
    """


def a_age_composition(con):
    print("\n" + "=" * 78)
    print("A.  AGE COMPOSITION OF THE ELECTORATE (share of general-election voters)")
    print("=" * 78)
    hdr = f"{'election':30} " + " ".join(f"{b:>8}" for b in AGE_BANDS) + f"{'med':>6}"
    print(hdr); print("-" * len(hdr))
    for year, label in GENERALS:
        ax = _agex(year)
        row = con.execute(f"""
            WITH e AS (
                SELECT {_band(ax)} band, {ax} age
                FROM voter_participation p JOIN voters v USING (state_voter_id)
                WHERE p.election_year={year} AND p.kind='GENERAL'
                  AND {ax} BETWEEN 18 AND 105
            )
            SELECT 100.0*count(*) FILTER(WHERE band='18-29')/count(*),
                   100.0*count(*) FILTER(WHERE band='30-44')/count(*),
                   100.0*count(*) FILTER(WHERE band='45-64')/count(*),
                   100.0*count(*) FILTER(WHERE band='65+')/count(*),
                   median(age) FROM e
        """).fetchone()
        print(f"{label:30} " + " ".join(f"{x:7.1f}%" for x in row[:4]) + f" {row[4]:5.0f}")
    # registration baseline
    row = con.execute(f"""
        WITH e AS (SELECT {_band('v.age')} band, v.age FROM voters v WHERE v.age BETWEEN 18 AND 105)
        SELECT 100.0*count(*) FILTER(WHERE band='18-29')/count(*),
               100.0*count(*) FILTER(WHERE band='30-44')/count(*),
               100.0*count(*) FILTER(WHERE band='45-64')/count(*),
               100.0*count(*) FILTER(WHERE band='65+')/count(*), median(age) FROM e
    """).fetchone()
    print("-" * len(hdr))
    print(f"{'REGISTRATION baseline (2026)':30} " + " ".join(f"{x:7.1f}%" for x in row[:4]) + f" {row[4]:5.0f}")


def b_age_by_party(con):
    print("\n" + "=" * 78)
    print("B.  *** FLAGSHIP ***  AGE SKEW BY PARTY across election types")
    print("=" * 78)
    for metric, band in (("share 65+", "65+"), ("share 18-29", "18-29")):
        print(f"\n  -- {metric} (% of that party's general voters) --")
        hdr = f"  {'election':30} " + " ".join(f"{p:>7}" for p in PARTIES)
        print(hdr); print("  " + "-" * (len(hdr) - 2))
        for year, label in GENERALS:
            ax = _agex(year)
            d = dict(con.execute(f"""
                WITH e AS (SELECT {PARTY_CASE} party, {_band(ax)} band
                    FROM voter_participation p JOIN voters v USING (state_voter_id)
                    WHERE p.election_year={year} AND p.kind='GENERAL' AND {ax} BETWEEN 18 AND 105)
                SELECT party, 100.0*count(*) FILTER(WHERE band='{band}')/count(*) FROM e GROUP BY party
            """).fetchall())
            print(f"  {label:30} " + " ".join(f"{d.get(p, float('nan')):6.1f}%" for p in PARTIES))
    print("\n  -- median age within each party (general voters) --")
    hdr = f"  {'election':30} " + " ".join(f"{p:>7}" for p in PARTIES)
    print(hdr); print("  " + "-" * (len(hdr) - 2))
    for year, label in GENERALS:
        ax = _agex(year)
        d = dict(con.execute(f"""
            SELECT {PARTY_CASE} party, median({ax})
            FROM voter_participation p JOIN voters v USING (state_voter_id)
            WHERE p.election_year={year} AND p.kind='GENERAL' AND {ax} BETWEEN 18 AND 105
            GROUP BY party
        """).fetchall())
        print(f"  {label:30} " + " ".join(f"{d.get(p, float('nan')):6.0f} " for p in PARTIES))


def c_party_composition(con):
    print("\n" + "=" * 78)
    print("C.  PARTY COMPOSITION OF THE ELECTORATE (share of voters by party)")
    print("    does the lower-turnout contest skew more Republican?")
    print("=" * 78)
    hdr = f"{'contest':30} " + " ".join(f"{p:>7}" for p in PARTIES) + f" {'R-D':>6}"
    print(hdr); print("-" * len(hdr))
    rows = [(y, l, "GENERAL") for y, l in GENERALS] + [(y, l, "PRIMARY") for y, l in PRIMARIES]
    for year, label, kind in rows:
        d = dict(con.execute(f"""
            WITH e AS (SELECT {PARTY_CASE} party
                FROM voter_participation p JOIN voters v USING (state_voter_id)
                WHERE p.election_year={year} AND p.kind='{kind}')
            SELECT party, 100.0*count(*)/sum(count(*)) OVER () FROM e GROUP BY party
        """).fetchall())
        gap = d.get("REP", 0) - d.get("DEM", 0)
        print(f"{label:30} " + " ".join(f"{d.get(p, float('nan')):6.1f}%" for p in PARTIES) + f" {gap:+6.1f}")
    d = dict(con.execute(f"""
        SELECT {PARTY_CASE} party, 100.0*count(*)/sum(count(*)) OVER () FROM voters v GROUP BY party
    """).fetchall())
    gap = d.get("REP", 0) - d.get("DEM", 0)
    print("-" * len(hdr))
    print(f"{'REGISTRATION baseline':30} " + " ".join(f"{d.get(p, float('nan')):6.1f}%" for p in PARTIES) + f" {gap:+6.1f}")


def d_turnout_rate(con):
    print("\n" + "=" * 78)
    print("D.  TURNOUT RATE by age x party  (CAVEAT: current-roll denominator is")
    print("    survivorship-INFLATED — 1.03M roll vs 1.18M registered in 2024; official")
    print("    2024 turnout 77.8% vs our ~94%. Bias is non-uniform across groups, so")
    print("    even within-year contrasts are unreliable. Illustrative only — the paper")
    print("    reports COMPOSITION shares (section A/C), not these rates.)")
    print("=" * 78)
    for year in (2024, 2022):
        print(f"\n  -- {year} general: voted / registered-by-election voters on current roll --")
        hdr = f"  {'age band':10} " + " ".join(f"{p:>7}" for p in PARTIES)
        print(hdr); print("  " + "-" * (len(hdr) - 2))
        ax = _agex(year)
        rows = con.execute(f"""
            WITH base AS (
                SELECT v.state_voter_id, {PARTY_CASE} party, {_band(ax)} band
                FROM voters v
                WHERE {ax} BETWEEN 18 AND 105
                  AND (v.registration_date IS NULL OR v.registration_date <= make_date({year},11,5))
            ),
            voted AS (SELECT DISTINCT state_voter_id FROM voter_participation
                      WHERE election_year={year} AND kind='GENERAL')
            SELECT band, party,
                   100.0*count(*) FILTER(WHERE b.state_voter_id IN (SELECT state_voter_id FROM voted))/count(*)
            FROM base b WHERE band IS NOT NULL GROUP BY band, party
        """).fetchall()
        tab = {}
        for band, party, rate in rows:
            tab.setdefault(band, {})[party] = rate
        for band in AGE_BANDS:
            d = tab.get(band, {})
            print(f"  {band:10} " + " ".join(f"{d.get(p, float('nan')):6.1f}%" for p in PARTIES))


def e_closed_primary(con):
    print("\n" + "=" * 78)
    print("E.  *** IDAHO FLAGSHIP ***  THE CLOSED PRIMARY IS THE DECISIVE CONTEST")
    print("    In an R+40 state the GOP primary, not November, picks the winner.")
    print("=" * 78)

    print("\n  E1. Which party's ballot did primary voters pull? (share of ballots)")
    hdr = f"  {'primary':22} " + " ".join(f"{p:>7}" for p in ["REP", "DEM", "UNA", "OTHER"]) + f" {'total':>10}"
    print(hdr); print("  " + "-" * (len(hdr) - 2))
    for year, label in PRIMARIES:
        d = dict(con.execute(f"""
            SELECT CASE WHEN ballot_choice IN ('REP','DEM','UNA') THEN ballot_choice ELSE 'OTHER' END b,
                   count(*) FROM voter_participation
            WHERE election_year={year} AND kind='PRIMARY' AND ballot_choice IS NOT NULL
            GROUP BY 1
        """).fetchall())
        tot = sum(d.values())
        print(f"  {label:22} " + " ".join(f"{100.0*d.get(p,0)/tot:6.1f}%" for p in ["REP", "DEM", "UNA", "OTHER"]) + f" {tot:>10,}")

    print("\n  E2. Primary PARTICIPATION rate by party-of-record (current roll)")
    print("      what fraction of each party's registrants voted? (survivorship-inflated;")
    print("      see section D — the paper uses composition/ballot-share, not these rates)")
    hdr = f"  {'primary':22} " + " ".join(f"{p:>7}" for p in PARTIES)
    print(hdr); print("  " + "-" * (len(hdr) - 2))
    for year, label in PRIMARIES:
        d = dict(con.execute(f"""
            WITH reg AS (SELECT {PARTY_CASE} party, v.state_voter_id FROM voters v
                         WHERE (v.registration_date IS NULL OR v.registration_date <= make_date({year},5,20))),
                 voted AS (SELECT DISTINCT state_voter_id FROM voter_participation
                           WHERE election_year={year} AND kind='PRIMARY')
            SELECT party, 100.0*count(*) FILTER(WHERE state_voter_id IN (SELECT state_voter_id FROM voted))/count(*)
            FROM reg GROUP BY party
        """).fetchall())
        print(f"  {label:22} " + " ".join(f"{d.get(p, float('nan')):6.1f}%" for p in PARTIES))

    print("\n  E3. Where do UNAFFILIATED primary voters go? (their ballot choice)")
    hdr = f"  {'primary':22} " + " ".join(f"{p:>7}" for p in ["REP", "DEM", "UNA", "OTHER"])
    print(hdr); print("  " + "-" * (len(hdr) - 2))
    for year, label in PRIMARIES:
        d = dict(con.execute(f"""
            SELECT CASE WHEN p.ballot_choice IN ('REP','DEM','UNA') THEN p.ballot_choice ELSE 'OTHER' END b,
                   count(*)
            FROM voter_participation p JOIN voters v USING (state_voter_id)
            WHERE p.election_year={year} AND p.kind='PRIMARY' AND v.party='UNA' AND p.ballot_choice IS NOT NULL
            GROUP BY 1
        """).fetchall())
        tot = sum(d.values()) or 1
        print(f"  {label:22} " + " ".join(f"{100.0*d.get(p,0)/tot:6.1f}%" for p in ["REP", "DEM", "UNA", "OTHER"]))

    print("\n  E4. Age skew: GOP-primary electorate vs GOP registrants (2024)")
    hdr = f"  {'group':28} " + " ".join(f"{b:>8}" for b in AGE_BANDS) + f"{'med':>6}"
    print(hdr); print("  " + "-" * (len(hdr) - 2))
    for lbl, where in (
        ("REP registrants (all roll)", "v.party='REP'"),
        ("REP-ballot primary voters 2024",
         "v.party='REP' AND p.state_voter_id IN (SELECT state_voter_id FROM voter_participation WHERE election_year=2024 AND kind='PRIMARY' AND ballot_choice='REP')"),
    ):
        ax = _agex(2024)
        if "primary" in lbl:
            q = f"""WITH e AS (SELECT {_band(ax)} band, {ax} age FROM voters v
                     JOIN (SELECT DISTINCT state_voter_id FROM voter_participation
                           WHERE election_year=2024 AND kind='PRIMARY' AND ballot_choice='REP') p
                     USING (state_voter_id) WHERE v.party='REP' AND {ax} BETWEEN 18 AND 105)
                     SELECT 100.0*count(*) FILTER(WHERE band='18-29')/count(*),
                            100.0*count(*) FILTER(WHERE band='30-44')/count(*),
                            100.0*count(*) FILTER(WHERE band='45-64')/count(*),
                            100.0*count(*) FILTER(WHERE band='65+')/count(*), median(age) FROM e"""
        else:
            q = f"""WITH e AS (SELECT {_band('v.age')} band, v.age FROM voters v
                     WHERE v.party='REP' AND v.age BETWEEN 18 AND 105)
                     SELECT 100.0*count(*) FILTER(WHERE band='18-29')/count(*),
                            100.0*count(*) FILTER(WHERE band='30-44')/count(*),
                            100.0*count(*) FILTER(WHERE band='45-64')/count(*),
                            100.0*count(*) FILTER(WHERE band='65+')/count(*), median(age) FROM e"""
        row = con.execute(q).fetchone()
        print(f"  {lbl:28} " + " ".join(f"{x:7.1f}%" for x in row[:4]) + f" {row[4]:5.0f}")


def main() -> int:
    con = duckdb.connect(ID_VRDB, read_only=True)
    a_age_composition(con)
    b_age_by_party(con)
    c_party_composition(con)
    d_turnout_rate(con)
    e_closed_primary(con)
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
