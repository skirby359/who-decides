"""Load the Idaho statewide voter file (w/ history) into a standalone id_vrdb.duckdb.

Idaho is the deep-RED party-of-record counterpart that completes the
party-resolved §F playbook (WA = production/party-unknown, NY = deep-blue,
ID = deep-red). Like NY it publishes individual **party affiliation**
(`PartyDesc`) — the gating variable WA lacks — plus per-election voting
history. Two structural differences from the NY FOIL file:

  1. **Age, not DOB.** The file gives an integer `Age` as of the export
     date (2026-06-29), not a birthdate. Downstream age-band analysis
     approximates election-time age as `age - (2026 - election_year)`
     (off by at most ~1y for birthday timing). Bands are robust; we never
     claim exact ages. This was anticipated in the TODO ("age-band only,
     no exact DOB").
  2. **Wide history columns, not a history string.** Each election is its
     own block of columns — `VoteDate (MM/DD/YYYY)`, `VoteType (...)`,
     `BallotStyle (...)`, `PrecinctVoted (...)`, and for PRIMARIES a
     `SelectedBallotChoice (...)` recording *which party ballot the voter
     pulled* in Idaho's closed GOP primary. We melt these into a normalized
     `voter_participation` table (state_voter_id, election_date, kind,
     method, ballot_choice) so the analytics mirror the NY scripts.

Source: data/raw/id/id_statewide_voter_history_20260629.csv (~0.39 GB,
  headered, comma-delimited, double-quoted, ~1.03M rows).

Writes a standalone data/id_vrdb.duckdb (parallel to wa_vrdb / ny_vrdb) so
it never lock-conflicts with id_statewide.duckdb.

Usage:
    PYTHONPATH=src python scripts/load_id_voters.py   # (no PYTHONPATH needed; duckdb only)
"""
import argparse
import os
import sys

import duckdb

CSV_PATH = "data/raw/id/id_statewide_voter_history_20260629.csv"
ID_VRDB = "data/id_vrdb.duckdb"
FILE_AS_OF_YEAR = 2026  # Age is current as of the 2026-06-29 export.

# PartyDesc -> short code. Idaho registers voters by party; minor parties
# (Libertarian, Constitution) are small but real, so we keep them distinct.
PARTY_CASE = """
    CASE UPPER(TRIM(r."PartyDesc"))
        WHEN 'REPUBLICAN'   THEN 'REP'
        WHEN 'DEMOCRATIC'   THEN 'DEM'
        WHEN 'UNAFFILIATED' THEN 'UNA'
        WHEN 'LIBERTARIAN'  THEN 'LIB'
        WHEN 'CONSTITUTION' THEN 'CON'
        ELSE 'OTHER'
    END
"""

# Ballot-choice normalizer (closed-primary party ballot pulled).
BALLOT_CASE = lambda col: f"""
    CASE UPPER(TRIM({col}))
        WHEN 'REP' THEN 'REP' WHEN 'DEM' THEN 'DEM' WHEN 'UNA' THEN 'UNA'
        WHEN 'LIB' THEN 'LIB' WHEN 'CON' THEN 'CON'
        WHEN '' THEN NULL ELSE UPPER(TRIM({col}))
    END
"""

# (election_date, election_year, kind, mm/dd/yyyy tag as it appears in headers,
#  has_ballot_choice)
ELECTIONS = [
    ("2026-05-19", 2026, "PRIMARY", "05/19/2026", True),
    ("2024-11-05", 2024, "GENERAL", "11/05/2024", False),
    ("2024-05-21", 2024, "PRIMARY", "05/21/2024", True),
    ("2022-11-08", 2022, "GENERAL", "11/08/2022", False),
    ("2022-05-17", 2022, "PRIMARY", "05/17/2022", True),
    ("2020-11-03", 2020, "GENERAL", "11/03/2020", False),
]


def load() -> None:
    con = duckdb.connect(ID_VRDB)
    csv = CSV_PATH.replace("\\", "/")

    print("[load] staging raw CSV (all VARCHAR)...")
    con.execute("DROP TABLE IF EXISTS _id_raw;")
    con.execute(f"""
        CREATE TABLE _id_raw AS
        SELECT * FROM read_csv(
            '{csv}', header = true, delim = ',', quote = '"', escape = '"',
            all_varchar = true, ignore_errors = true, null_padding = true
        );
    """)
    raw_n = con.execute("SELECT count(*) FROM _id_raw").fetchone()[0]
    print(f"[load] staged {raw_n:,} rows")

    print("[load] building typed voters table...")
    con.execute("DROP TABLE IF EXISTS voters;")
    con.execute(f"""
        CREATE TABLE voters AS
        SELECT
            r."VoterID"                                AS state_voter_id,
            UPPER(TRIM(r."LastName"))                  AS last_name,
            UPPER(TRIM(r."FirstName"))                 AS first_name,
            UPPER(TRIM(r."MiddleName"))                AS middle_name,
            NULLIF(TRIM(r."Suffix"), '')               AS name_suffix,
            TRY_CAST(r."Age" AS INT)                   AS age,
            NULLIF(TRIM(r."Gender"), '')               AS gender,
            {PARTY_CASE}                               AS party,
            UPPER(NULLIF(TRIM(r."PartyDesc"), ''))     AS party_desc,
            UPPER(NULLIF(TRIM(r."ResCountyDesc"), '')) AS county_name,
            UPPER(NULLIF(TRIM(r."ResCityDesc"), ''))   AS reg_city,
            NULLIF(TRIM(r."ResZip5"), '')              AS reg_zip,
            UPPER(NULLIF(TRIM(r."ResStreet"), ''))     AS reg_street_name,
            NULLIF(TRIM(r."ResHouseNumber"), '')       AS reg_street_num,
            TRY_STRPTIME(r."RegistrationDate", '%m/%d/%Y')::DATE AS registration_date,
            NULLIF(TRIM(r."Precinct"), '')             AS precinct,
            NULLIF(TRIM(r."Split"), '')                AS split,
            NULLIF(TRIM(r."PrecinctLabel"), '')        AS precinct_label,
            NULLIF(TRIM(r."CONGRESSIONAL DISTRICT"), '') AS congressional_district,
            LPAD(NULLIF(TRIM(r."LEGISLATIVE DISTRICT"), ''), 2, '0') AS legislative_district,
            -- The ID export is a current-roll extract with no active/inactive
            -- flag; every row is a live registrant. status_code='A' keeps the
            -- shared WA matcher (which filters status_code='A') working.
            'A'                                        AS status_code
        FROM _id_raw r;
    """)
    n = con.execute("SELECT count(*) FROM voters").fetchone()[0]
    print(f"[load] voters: {n:,} rows")

    # ---- normalized voter_participation (melt the 6 wide history blocks) ----
    print("[load] building voter_participation (melting history columns)...")
    con.execute("DROP TABLE IF EXISTS voter_participation;")
    parts = []
    for edate, eyear, kind, tag, has_choice in ELECTIONS:
        vd = f'r."VoteDate ({tag})"'
        vt = f'r."VoteType ({tag})"'
        choice = (BALLOT_CASE(f'r."SelectedBallotChoice ({tag})"')
                  if has_choice else "NULL")
        parts.append(f"""
            SELECT r."VoterID" AS state_voter_id,
                   DATE '{edate}'          AS election_date,
                   {eyear}                 AS election_year,
                   '{kind}'                AS kind,
                   NULLIF(TRIM({vt}), '')  AS method,
                   {choice}                AS ballot_choice
            FROM _id_raw r
            WHERE NULLIF(TRIM({vd}), '') IS NOT NULL
        """)
    con.execute(
        "CREATE TABLE voter_participation AS\n" + "\nUNION ALL\n".join(parts))
    con.execute("DROP TABLE _id_raw;")
    pn = con.execute("SELECT count(*) FROM voter_participation").fetchone()[0]
    print(f"[load] voter_participation: {pn:,} rows")

    _summarize(con, n)
    con.close()


def _summarize(con, n) -> None:
    print(f"\n[done] {ID_VRDB}: voters={n:,}\n")

    print("--- party-of-record (PartyDesc) ---")
    for party, cnt in con.execute("""
        SELECT party, count(*) FROM voters GROUP BY 1 ORDER BY 2 DESC
    """).fetchall():
        print(f"  {party:>8} {cnt:>10,}  ({100.0*cnt/n:5.2f}%)")

    print("\n--- coverage ---")
    cov = con.execute("""
        SELECT 100.0*count(age)/count(*),
               100.0*count(party) FILTER(WHERE party<>'OTHER')/count(*),
               100.0*count(registration_date)/count(*),
               count(DISTINCT county_name),
               count(DISTINCT legislative_district)
        FROM voters
    """).fetchone()
    print(f"  age present:          {cov[0]:5.2f}%")
    print(f"  party resolved:       {cov[1]:5.2f}%")
    print(f"  reg-date parsed:      {cov[2]:5.2f}%")
    print(f"  counties / LDs:       {cov[3]} / {cov[4]}")

    print("\n--- voter_participation by election ---")
    for row in con.execute("""
        SELECT election_date, kind, count(*) voted,
               count(ballot_choice) with_ballot
        FROM voter_participation GROUP BY 1,2 ORDER BY 1 DESC
    """).fetchall():
        extra = f"  ballot-choice={row[3]:,}" if row[3] else ""
        print(f"  {row[0]}  {row[1]:8} {row[2]:>9,}{extra}")


def main() -> int:
    if not os.path.exists(CSV_PATH):
        print(f"ERROR: {CSV_PATH} not found", file=sys.stderr)
        return 1
    argparse.ArgumentParser().parse_args()
    load()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
