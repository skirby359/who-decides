"""Populate voter_scores for NY and ID from their standalone voter files.

The WA `compute_voter_scores` ETL is WA-machinery (precinct crosswalk,
composite lean, PP matchback) and can't run for NY/ID. This standalone
script fills each state's empty `voter_scores` table (ny_statewide.duckdb /
id_statewide.duckdb) with the WA-SEMANTICS-COMPATIBLE core columns the
individual-layer cuts (cross-state F1/F3) need:

    state_voter_id, district_id (house district: NY 'adNNN', ID 'ldNN'),
    age_cohort, turnout_propensity, is_super_voter, lapsed/sporadic,
    total/recent_elections, voting_frequency, registration_age_years

Definitions transfer 1:1 from src/wa_analyzer/etl/vrdb.py::compute_voter_scores:
  * turnout_propensity — step function on last-voted year (inactive 0.15;
    2024+ 0.90; 2022+ 0.80; 2020+ 0.55; 2018+ 0.35; 2016+ 0.25; ever 0.15;
    never 0.10), blended as GREATEST(step, recent_elections/5).
  * is_super_voter — voted 2022+ AND registered >= 8 years.
  * age_cohort — Gen Z >=1997 / Millennial >=1981 / Gen X >=1965 /
    Boomer >=1946 / Silent (born 1900-1945) / Unknown.

Per-state sources (both in the state's standalone vrdb):
  * NY — `voters` (birthdate, registration_date, native last_voted with
    sentinel dates, status A*/I/P/17, assembly_district) + normalized
    `voter_participation` (election_year, kind; 58.4M rows). Last-voted =
    max of the plausible native date and the participation max.
  * ID — `voters` (age as of 2026-06-29 -> birth year approximation,
    registration_date, legislative_district, synthesized status 'A') +
    `voter_participation` (6 elections 2020-2026 with real dates).
    CAVEAT: the ID roll is a current-roll extract (survivorship-inflated
    rates — see who-decides-idaho §III); scores describe CURRENT registrants.

Wipe-scope discipline: deletes only this state's house-district rows
(district_id LIKE 'ad%'/'ld%') before the set-based INSERT ... BY NAME.

Run:  python scripts/populate_ny_id_voter_scores.py [NY] [ID]
"""
import sys
import time
from pathlib import Path

import duckdb

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA = REPO_ROOT / "data"

COHORT_SQL = """
    CASE
        WHEN birth_year IS NULL OR birth_year < 1900 OR birth_year > 2008 THEN 'Unknown'
        WHEN birth_year >= 1997 THEN 'Gen Z'
        WHEN birth_year >= 1981 THEN 'Millennial'
        WHEN birth_year >= 1965 THEN 'Gen X'
        WHEN birth_year >= 1946 THEN 'Boomer'
        ELSE 'Silent'
    END
"""

STEP_SQL = """
    CASE
        WHEN NOT is_active THEN 0.15
        WHEN last_year >= 2024 THEN 0.90
        WHEN last_year >= 2022 THEN 0.80
        WHEN last_year >= 2020 THEN 0.55
        WHEN last_year >= 2018 THEN 0.35
        WHEN last_year >= 2016 THEN 0.25
        WHEN last_year IS NOT NULL THEN 0.15
        ELSE 0.10
    END
"""


def _insert(conn: duckdb.DuckDBPyConnection, base_cte: str, district_pfx: str) -> int:
    conn.execute(f"DELETE FROM voter_scores WHERE district_id LIKE '{district_pfx}%'")
    conn.execute(f"""
        INSERT INTO voter_scores BY NAME
        WITH {base_cte}
        SELECT
            state_voter_id,
            district_id,
            registration_age_years,
            {COHORT_SQL} AS age_cohort,
            CASE WHEN total_elections > 0
                 THEN GREATEST({STEP_SQL}, LEAST(recent_elections / 5.0, 1.0))
                 ELSE {STEP_SQL}
            END AS turnout_propensity,
            (last_year IS NOT NULL AND last_year < 2020) AS lapsed_voter,
            (last_year BETWEEN 2016 AND 2021) AS sporadic_voter,
            (last_year >= 2022 AND registration_age_years >= 8) AS is_super_voter,
            total_elections,
            recent_elections,
            CASE WHEN registration_age_years > 0
                 THEN LEAST(total_elections / (registration_age_years * 0.5), 1.0)
                 ELSE 0 END AS voting_frequency
        FROM base
        WHERE district_id IS NOT NULL
    """)
    return conn.execute(
        f"SELECT COUNT(*) FROM voter_scores WHERE district_id LIKE '{district_pfx}%'"
    ).fetchone()[0]


def populate_ny() -> None:
    conn = duckdb.connect(str(DATA / "ny_statewide.duckdb"))
    conn.execute(f"ATTACH '{DATA / 'ny_vrdb.duckdb'}' AS vrdb (READ_ONLY)")
    # voter_participation has election_year only (no dates): "recent" =
    # election_year >= 2023 (the 4 election-years ending at the 2026 run date).
    base = """
        vp AS (
            SELECT state_voter_id,
                   COUNT(DISTINCT (election_year, kind)) AS total_elections,
                   COUNT(DISTINCT (election_year, kind))
                       FILTER (WHERE election_year >= 2023) AS recent_elections,
                   MAX(election_year) AS vp_last_year
            FROM vrdb.voter_participation
            GROUP BY state_voter_id
        ),
        base AS (
            SELECT
                v.state_voter_id,
                CASE WHEN TRY_CAST(v.assembly_district AS INT) BETWEEN 1 AND 150
                     THEN 'ad' || LPAD(TRY_CAST(v.assembly_district AS INT)::VARCHAR, 3, '0')
                END AS district_id,
                ROUND(DATEDIFF('day', v.registration_date, CURRENT_DATE) / 365.25, 1)
                    AS registration_age_years,
                CASE WHEN v.birthdate IS NOT NULL THEN YEAR(v.birthdate) END AS birth_year,
                v.status_code LIKE 'A%' AS is_active,
                NULLIF(GREATEST(
                    COALESCE(vp.vp_last_year, 0),
                    COALESCE(CASE WHEN v.last_voted BETWEEN DATE '1960-01-01'
                                       AND DATE '2026-12-31'
                                  THEN YEAR(v.last_voted) END, 0)
                ), 0) AS last_year,
                COALESCE(vp.total_elections, 0) AS total_elections,
                COALESCE(vp.recent_elections, 0) AS recent_elections
            FROM vrdb.voters v
            LEFT JOIN vp USING (state_voter_id)
            -- The NYSVOTER extract carries a few dozen duplicate ids; the
            -- table PK is state_voter_id, so keep one row per voter
            -- (prefer active status, then most recent vote).
            QUALIFY ROW_NUMBER() OVER (
                PARTITION BY v.state_voter_id
                ORDER BY (v.status_code LIKE 'A%') DESC, v.last_voted DESC NULLS LAST
            ) = 1
        )
    """
    n = _insert(conn, base, "ad")
    print(f"NY voter_scores: {n:,} rows")
    conn.close()


def populate_id() -> None:
    conn = duckdb.connect(str(DATA / "id_statewide.duckdb"))
    conn.execute(f"ATTACH '{DATA / 'id_vrdb.duckdb'}' AS vrdb (READ_ONLY)")
    # age is as-of the 2026-06-29 file date -> birth year approximation.
    base = """
        vp AS (
            SELECT state_voter_id,
                   COUNT(DISTINCT election_date) AS total_elections,
                   COUNT(DISTINCT election_date)
                       FILTER (WHERE election_date >= CURRENT_DATE - INTERVAL 4 YEAR)
                       AS recent_elections,
                   MAX(election_year) AS vp_last_year
            FROM vrdb.voter_participation
            GROUP BY state_voter_id
        ),
        base AS (
            SELECT
                v.state_voter_id,
                CASE WHEN TRY_CAST(v.legislative_district AS INT) BETWEEN 1 AND 35
                     THEN 'ld' || LPAD(TRY_CAST(v.legislative_district AS INT)::VARCHAR, 2, '0')
                END AS district_id,
                ROUND(DATEDIFF('day', v.registration_date, CURRENT_DATE) / 365.25, 1)
                    AS registration_age_years,
                CASE WHEN v.age BETWEEN 17 AND 120 THEN 2026 - v.age END AS birth_year,
                TRUE AS is_active,
                vp.vp_last_year AS last_year,
                COALESCE(vp.total_elections, 0) AS total_elections,
                COALESCE(vp.recent_elections, 0) AS recent_elections
            FROM vrdb.voters v
            LEFT JOIN vp USING (state_voter_id)
        )
    """
    n = _insert(conn, base, "ld")
    print(f"ID voter_scores: {n:,} rows")
    conn.close()


def main() -> None:
    which = [a.upper() for a in sys.argv[1:]] or ["NY", "ID"]
    for st in which:
        t0 = time.time()
        {"NY": populate_ny, "ID": populate_id}[st]()
        print(f"  ({st} done in {time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
