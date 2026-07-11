"""Closed-primary participation by party enrollment (NY).

New York runs CLOSED primaries: only voters enrolled in a party may vote in
that party's primary. So primary participation by enrollment measures (a)
partisan engagement asymmetry and (b) a structural democratic-health fact — the
quarter of registrants enrolled "blank" (no party) are excluded from the
party-primary stage entirely, except for occasional nonpartisan/special races.

Participation rate = (enrollees of party P who cast a primary ballot in year Y)
/ (active enrollees of party P registered on or before that primary). Uses the
normalized voter_participation table (kind in PRIMARY / PRES_PRIMARY).

Usage:
    STATE=NY python scripts/diag_ny_primary_participation.py
"""
import duckdb

NY_VRDB = "data/ny_vrdb.duckdb"

PARTY_CASE = """
    CASE WHEN v.party='DEM' THEN 'DEM' WHEN v.party='REP' THEN 'REP'
         WHEN v.party='BLK' THEN 'NOPARTY' ELSE 'OTHER' END
"""

# (year, kind, approx primary date for the registration cutoff, label)
PRIMARIES = [
    (2024, "PRES_PRIMARY", "2024-04-02", "2024 Presidential Primary"),
    (2024, "PRIMARY",      "2024-06-25", "2024 State/Congress Primary"),
    (2022, "PRIMARY",      "2022-06-28", "2022 State/Congress Primary"),
    (2021, "PRIMARY",      "2021-06-22", "2021 Primary (odd-year)"),
]


def main() -> int:
    con = duckdb.connect(NY_VRDB, read_only=True)
    print("=== CLOSED-PRIMARY PARTICIPATION RATE by enrollment ===")
    print("    (share of each party's active enrollees who cast a primary ballot)\n")
    hdr = f"  {'primary':32} {'DEM':>7} {'REP':>7} {'NOPARTY':>8} {'OTHER':>7}"
    print(hdr); print("  " + "-" * (len(hdr) - 2))
    for year, kind, cutoff, label in PRIMARIES:
        rows = con.execute(f"""
            WITH base AS (
                SELECT v.state_voter_id, {PARTY_CASE} AS party
                FROM voters v
                WHERE v.status_code='A'
                  AND (v.registration_date IS NULL OR v.registration_date <= DATE '{cutoff}')
            ),
            voted AS (
                SELECT DISTINCT state_voter_id FROM voter_participation
                WHERE election_year={year} AND kind='{kind}'
            )
            SELECT party,
                   100.0*count(*) FILTER(WHERE b.state_voter_id IN (SELECT state_voter_id FROM voted))
                        /count(*) rate
            FROM base b GROUP BY party
        """).fetchall()
        d = {p: r for p, r in rows}
        print(f"  {label:32} " + " ".join(
            f"{d.get(p, float('nan')):6.1f}%" for p in ("DEM", "REP", "NOPARTY", "OTHER")))

    # Structural-exclusion headline: what share of the active roll is "blank"
    # and thus locked out of party primaries?
    blk = con.execute("""
        SELECT 100.0*count(*) FILTER(WHERE party='BLK')/count(*)
        FROM voters WHERE status_code='A'
    """).fetchone()[0]
    print(f"\n  Structural note: {blk:.1f}% of active registrants are enrolled "
          f"'blank' (no party)\n  and are excluded from closed party primaries by law.")
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
