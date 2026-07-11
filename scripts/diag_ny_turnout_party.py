"""Flagship electoral-health analysis: NY turnout by age x PARTY-OF-RECORD.

This is the party-resolved upgrade of the WA "who decides" finding (the gray
off-year electorate). WA could only show the electorate is *older* in off
years; NY publishes individual party enrollment, so we can ask the sharper
question: does one party's electorate age-collapse harder in off-year/local
elections than the other's — mechanically advantaging it when turnout falls?

Data: data/ny_vrdb.duckdb table `voters` (13.54M, party + full DOB +
voter_history). The voter_history field mixes ~6 free-text formats per
election across counties (e.g. "2024 GENERAL ELECTION", "General Election,
2024", date-form "20241105 GE"). We parse every event per-voter into a
normalized `voter_participation` table (state_voter_id, election_year, kind,
method), then join age + party.

Survivorship caveat: the file is the CURRENT (2026) roll, so voters who voted
in a past election but were since purged/moved are absent. => composition
SHARES (of those who voted) are robust; turnout RATES are biased high for
older cycles. We lead with shares and report rates with the caveat.

Usage:
    PYTHONPATH=src python scripts/diag_ny_turnout_party.py --rebuild   # build participation table (~1-2 min)
    PYTHONPATH=src python scripts/diag_ny_turnout_party.py             # run analyses (table must exist)
"""
import argparse

import duckdb

NY_VRDB = "data/ny_vrdb.duckdb"

# (election_year, label, kind) for the elections we contrast.
ELECTIONS = [
    (2024, "2024 GENERAL (presidential)", "pres"),
    (2020, "2020 GENERAL (presidential)", "pres"),
    (2022, "2022 GENERAL (midterm)", "midterm"),
    (2018, "2018 GENERAL (midterm)", "midterm"),
    (2025, "2025 GENERAL (odd-year/local)", "odd"),
    (2023, "2023 GENERAL (odd-year/local)", "odd"),
]

# Party-of-record buckets. CON/WOR/OTH/IND/etc. lumped as OTHER (each <3%).
PARTY_CASE = """
    CASE
        WHEN v.party = 'DEM' THEN 'DEM'
        WHEN v.party = 'REP' THEN 'REP'
        WHEN v.party = 'BLK' THEN 'NOPARTY'
        ELSE 'OTHER'
    END
"""

AGE_BANDS = ["18-29", "30-44", "45-64", "65+"]


def rebuild(con: duckdb.DuckDBPyConnection) -> None:
    print("[rebuild] parsing voter_history into voter_participation ...")
    con.execute("DROP TABLE IF EXISTS voter_participation;")
    con.execute(r"""
        CREATE TABLE voter_participation AS
        WITH ev AS (
            SELECT state_voter_id,
                   trim(unnest(str_split(voter_history, ';'))) AS e
            FROM voters
            WHERE voter_history IS NOT NULL AND voter_history <> ''
        ),
        parsed AS (
            SELECT
                state_voter_id,
                TRY_CAST(regexp_extract(e, '(19|20)\d{2}') AS INT) AS election_year,
                CASE
                    WHEN upper(e) LIKE '%PRESIDENTIAL PRIMARY%'
                         OR regexp_full_match(e, '\d{8} PP(\(.\))?') THEN 'PRES_PRIMARY'
                    WHEN upper(e) LIKE '%GENERAL%'
                         OR regexp_full_match(e, '\d{8} GE(\(.\))?') THEN 'GENERAL'
                    WHEN upper(e) LIKE '%PRIMARY%'
                         OR regexp_full_match(e, '\d{8} PR(\(.\))?') THEN 'PRIMARY'
                    WHEN upper(e) LIKE '%SPECIAL%'
                         OR regexp_full_match(e, '\d{8} (SE|SP)(\(.\))?') THEN 'SPECIAL'
                    ELSE 'OTHER'
                END AS kind,
                regexp_extract(e, '\(([A-Za-z])\)\s*$', 1) AS method
            FROM ev
        )
        SELECT DISTINCT state_voter_id, election_year, kind, method
        FROM parsed
        WHERE election_year BETWEEN 2016 AND 2026 AND kind <> 'OTHER';
    """)
    n = con.execute("SELECT count(*) FROM voter_participation").fetchone()[0]
    print(f"[rebuild] voter_participation: {n:,} rows")


def _band(alias_age: str) -> str:
    return f"""
        CASE
            WHEN {alias_age} BETWEEN 18 AND 29 THEN '18-29'
            WHEN {alias_age} BETWEEN 30 AND 44 THEN '30-44'
            WHEN {alias_age} BETWEEN 45 AND 64 THEN '45-64'
            WHEN {alias_age} BETWEEN 65 AND 105 THEN '65+'
            ELSE NULL
        END
    """


def analysis_age_composition(con):
    print("\n" + "=" * 78)
    print("A.  AGE COMPOSITION OF THE ELECTORATE  (share of general-election voters)")
    print("=" * 78)
    header = f"{'election':32} " + " ".join(f"{b:>8}" for b in AGE_BANDS) + f"{'med_age':>9}"
    print(header)
    print("-" * len(header))
    for year, label, _ in ELECTIONS:
        row = con.execute(f"""
            WITH e AS (
                SELECT {_band(f"date_diff('year', v.birthdate, make_date({year},11,5))")} AS band,
                       date_diff('year', v.birthdate, make_date({year},11,5)) AS age
                FROM voter_participation p JOIN voters v USING (state_voter_id)
                WHERE p.election_year={year} AND p.kind='GENERAL' AND v.birthdate IS NOT NULL
                  AND date_diff('year', v.birthdate, make_date({year},11,5)) BETWEEN 18 AND 105
            )
            SELECT
                100.0*count(*) FILTER(WHERE band='18-29')/count(*),
                100.0*count(*) FILTER(WHERE band='30-44')/count(*),
                100.0*count(*) FILTER(WHERE band='45-64')/count(*),
                100.0*count(*) FILTER(WHERE band='65+')/count(*),
                median(age)
            FROM e
        """).fetchone()
        cells = " ".join(f"{x:7.1f}%" for x in row[:4])
        print(f"{label:32} {cells} {row[4]:8.0f}")


def analysis_age_by_party(con):
    print("\n" + "=" * 78)
    print("B.  *** FLAGSHIP ***  AGE SKEW BY PARTY ACROSS ELECTION TYPES")
    print("    share 65+ and share 18-29 within each party's general-election voters")
    print("=" * 78)
    for metric, band in (("share 65+", "65+"), ("share 18-29", "18-29")):
        print(f"\n  -- {metric} (% of that party's voters) --")
        hdr = f"  {'election':32} {'DEM':>8} {'REP':>8} {'NOPARTY':>8} {'OTHER':>8}"
        print(hdr)
        print("  " + "-" * (len(hdr) - 2))
        for year, label, _ in ELECTIONS:
            vals = con.execute(f"""
                WITH e AS (
                    SELECT {PARTY_CASE} AS party,
                           {_band(f"date_diff('year', v.birthdate, make_date({year},11,5))")} AS band
                    FROM voter_participation p JOIN voters v USING (state_voter_id)
                    WHERE p.election_year={year} AND p.kind='GENERAL' AND v.birthdate IS NOT NULL
                      AND date_diff('year', v.birthdate, make_date({year},11,5)) BETWEEN 18 AND 105
                )
                SELECT party, 100.0*count(*) FILTER(WHERE band='{band}')/count(*) pct
                FROM e GROUP BY party
            """).fetchall()
            d = {p: v for p, v in vals}
            print(f"  {label:32} " + " ".join(
                f"{d.get(p, float('nan')):7.1f}%" for p in ("DEM", "REP", "NOPARTY", "OTHER")))

    print("\n  -- median age within each party --")
    hdr = f"  {'election':32} {'DEM':>8} {'REP':>8} {'NOPARTY':>8} {'OTHER':>8}"
    print(hdr); print("  " + "-" * (len(hdr) - 2))
    for year, label, _ in ELECTIONS:
        vals = con.execute(f"""
            SELECT {PARTY_CASE} AS party,
                   median(date_diff('year', v.birthdate, make_date({year},11,5))) m
            FROM voter_participation p JOIN voters v USING (state_voter_id)
            WHERE p.election_year={year} AND p.kind='GENERAL' AND v.birthdate IS NOT NULL
              AND date_diff('year', v.birthdate, make_date({year},11,5)) BETWEEN 18 AND 105
            GROUP BY party
        """).fetchall()
        d = {p: v for p, v in vals}
        print(f"  {label:32} " + " ".join(
            f"{d.get(p, float('nan')):8.0f}" for p in ("DEM", "REP", "NOPARTY", "OTHER")))


def analysis_party_composition(con):
    print("\n" + "=" * 78)
    print("C.  PARTY COMPOSITION OF THE ELECTORATE  (share of voters by party)")
    print("    does the off-year electorate skew more partisan / less unaffiliated?")
    print("=" * 78)
    hdr = f"{'election':32} {'DEM':>8} {'REP':>8} {'NOPARTY':>8} {'OTHER':>8} {'DEM-REP':>8}"
    print(hdr); print("-" * len(hdr))
    for year, label, _ in ELECTIONS:
        vals = con.execute(f"""
            WITH e AS (
                SELECT {PARTY_CASE} AS party
                FROM voter_participation p JOIN voters v USING (state_voter_id)
                WHERE p.election_year={year} AND p.kind='GENERAL'
            )
            SELECT party, 100.0*count(*)/sum(count(*)) OVER () pct FROM e GROUP BY party
        """).fetchall()
        d = {p: v for p, v in vals}
        gap = d.get("DEM", 0) - d.get("REP", 0)
        print(f"{label:32} " + " ".join(
            f"{d.get(p, float('nan')):7.1f}%" for p in ("DEM", "REP", "NOPARTY", "OTHER"))
            + f" {gap:+7.1f}")
    # Baseline: registration composition of the full roll.
    vals = con.execute(f"""
        SELECT {PARTY_CASE} AS party, 100.0*count(*)/sum(count(*)) OVER () pct
        FROM voters v GROUP BY party
    """).fetchall()
    d = {p: v for p, v in vals}
    gap = d.get("DEM", 0) - d.get("REP", 0)
    print("-" * len(hdr))
    print(f"{'REGISTRATION baseline (all roll)':32} " + " ".join(
        f"{d.get(p, float('nan')):7.1f}%" for p in ("DEM", "REP", "NOPARTY", "OTHER"))
        + f" {gap:+7.1f}")


def analysis_turnout_rate(con):
    print("\n" + "=" * 78)
    print("D.  TURNOUT RATE by age x party  (CAVEAT: current-roll denominator,")
    print("    survivorship-biased high for older cycles; trend within a year is valid)")
    print("=" * 78)
    for year in (2024, 2022, 2025):
        print(f"\n  -- {year} general: voted-in-{year} / on-roll & registered by {year}-11-05 --")
        hdr = f"  {'age band':10} {'DEM':>8} {'REP':>8} {'NOPARTY':>8} {'OTHER':>8}"
        print(hdr); print("  " + "-" * (len(hdr) - 2))
        rows = con.execute(f"""
            WITH base AS (
                SELECT v.state_voter_id, {PARTY_CASE} AS party,
                       {_band(f"date_diff('year', v.birthdate, make_date({year},11,5))")} AS band
                FROM voters v
                WHERE v.birthdate IS NOT NULL
                  AND date_diff('year', v.birthdate, make_date({year},11,5)) BETWEEN 18 AND 105
                  AND (v.registration_date IS NULL OR v.registration_date <= make_date({year},11,5))
            ),
            voted AS (
                SELECT DISTINCT state_voter_id FROM voter_participation
                WHERE election_year={year} AND kind='GENERAL'
            )
            SELECT band, party,
                   100.0*count(*) FILTER(WHERE b.state_voter_id IN (SELECT state_voter_id FROM voted))/count(*) rate
            FROM base b WHERE band IS NOT NULL GROUP BY band, party
        """).fetchall()
        tab = {}
        for band, party, rate in rows:
            tab.setdefault(band, {})[party] = rate
        for band in AGE_BANDS:
            d = tab.get(band, {})
            print(f"  {band:10} " + " ".join(
                f"{d.get(p, float('nan')):7.1f}%" for p in ("DEM", "REP", "NOPARTY", "OTHER")))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuild", action="store_true",
                    help="(re)build the voter_participation table first")
    args = ap.parse_args()

    if args.rebuild:
        con = duckdb.connect(NY_VRDB)
        rebuild(con)
        con.close()

    con = duckdb.connect(NY_VRDB, read_only=True)
    exists = con.execute(
        "SELECT count(*) FROM information_schema.tables WHERE table_name='voter_participation'"
    ).fetchone()[0]
    if not exists:
        print("voter_participation table missing — run with --rebuild first.")
        return 1
    analysis_age_composition(con)
    analysis_age_by_party(con)
    analysis_party_composition(con)
    analysis_turnout_rate(con)
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
