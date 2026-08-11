"""Odd-year roll-off: the row Appendix F's enlargement grid left blank.

Why this exists
---------------
`diag_wa_rolloff_2024.py` measures even-year roll-off and feeds Appendix F's
scenario grid, whose odd-year baseline row is **ballot return with no roll-off
applied at all** while every even-year row has 5–34% subtracted. The paper's
justification was asserted, never measured: that Washington's odd-year ballot
"is mostly local and district contests … so ballot return is a closer stand-in
for local-race participation."

It is measurable from data already loaded, and it is not true as stated.

KING COUNTY IS NOT IN THE ODD-YEAR RESULTS, AND EVERYTHING HERE SCOPES AROUND IT
--------------------------------------------------------------------------------
Measured, not assumed: `precinct_results` holds **zero** King rows for the 2021
and 2023 generals, and for 2025 it holds only ``CITY OF SEATTLE MAYOR`` (3,051
rows) — no SJR 8201. King is 29–33% of each odd-year electorate.

The first version of this script divided non-King votes by the **statewide**
certified ballot count and reported odd-year statewide roll-off as 34.7–36.0%.
That was a partial-load artifact, not roll-off — the exact defect
``diag_wa_rolloff_2024.py`` already excludes Lt. Governor for ("loaded in only
5,355 of 8,111 precincts / 38 of 39 counties, a partial-load artifact, not
roll-off"). Corrected, the figure is **4.9–6.6%**, and the correction reverses
what the cut shows: a statewide measure on an odd-year ballot rolls off about as
much as a statewide measure on an even-year one (4.1–5.6%), not seven times as
much.

Every figure below therefore runs on a **38-county, King-excluded footprint**,
including the 2021 and 2023 columns that could not have contained King anyway —
so the three years are one panel over one population rather than three panels
over three.

Two cuts, both conservative
---------------------------
1. **Statewide item vs non-King certified ballots.** The denominator is the
   statewide certified count scaled by King's share of that election's ballots,
   taken from the VRDB reconstruction (31.3% / 29.2% / 32.7%). That makes it an
   **estimate**, unlike Appendix F's even-year figures, which divide by a
   directly published statewide total. Reported to one decimal for that reason
   and no further.

2. **Local offices vs a per-precinct ballot floor.** There is no per-precinct
   ballot count for odd years, so the denominator is the best-attended contest
   in that precinct. That contest has roll-off of its own, so every figure here
   **understates** roll-off — they are lower bounds, not estimates.

Both cuts pool contested with uncontested races, exactly as the even-year table
does *not* (it reports 16.6–17.2% contested against 33.7–34.4% uncontested), so
the local rows below are not directly comparable to the even-year contested
benchmark. What they establish is the narrow, sufficient point: odd-year
local-contest roll-off is **not zero** and is not small for several of the
offices this paper names.

Usage::

    python scripts/diag_wa_rolloff_oddyear.py
"""
import duckdb

DB = "data/wa_statewide.duckdb"

# election_id, label, certified ballots counted (WA SoS per-election turnout page),
# King's share of that election's ballots (VRDB distinct returners; see the
# module docstring for why the denominator has to be scaled).
ODD_YEARS = [
    (8, "Nov 2021", 1_896_481, 0.3131),
    (4, "Nov 2023", 1_758_084, 0.2918),
    (1, "Nov 2025", 2_001_425, 0.3269),
]

# The one county absent from the odd-year precinct returns. Scoped out
# everywhere rather than only where it is missing, so the three years share a
# footprint.
_EXCLUDED_COUNTY = "KING"

# A contest is "statewide" if it appears in essentially every reporting precinct.
# 2023 returns ZERO rows here, which is the correct answer and not a data gap:
# Washington abolished the tax advisory votes in 2023 (SB 5082, eff. July 2023).
_STATEWIDE_MIN_PRECINCTS = 4000

_OFFICE_GROUPS = """
    CASE
      WHEN race_name LIKE '%SCHOOL%DIRECTOR%'                              THEN 'school director'
      WHEN race_name LIKE '%CITY COUNCIL%' OR race_name LIKE '%COUNCIL POSITION%'
                                                                            THEN 'city council'
      WHEN race_name LIKE '%MAYOR%'                                         THEN 'mayor'
      WHEN race_name LIKE '%FIRE%'                                          THEN 'fire district'
      WHEN race_name LIKE '%PORT%COMMISSIONER%'                             THEN 'port commissioner'
    END
"""


def _king_is_absent(con) -> None:
    """Fail loudly if King ever IS loaded — the scaling below would then be wrong.

    This guard exists because the defect it protects against was shipped once:
    a denominator that silently mixed a statewide certified total with a
    38-county numerator. If someone loads King's odd-year returns, these figures
    must be rebuilt on the real statewide basis, not quietly re-scaled.
    """
    for eid, label, _, _ in ODD_YEARS:
        n, = con.execute("""
            SELECT COUNT(*) FROM precinct_results pr
            JOIN precincts p USING (precinct_id)
            JOIN races r USING (race_id)
            WHERE r.election_id = ? AND UPPER(p.county_name) = ?
        """, [eid, _EXCLUDED_COUNTY]).fetchone()
        # 2025 carries Seattle Mayor and nothing else; anything beyond that means
        # the load changed.
        if (eid == 1 and n > 3_051) or (eid != 1 and n > 0):
            raise RuntimeError(
                f"{label}: {n} {_EXCLUDED_COUNTY} precinct-result rows are now loaded. "
                f"The King-share scaling in ODD_YEARS assumes they are absent. "
                f"Rebuild these figures on the real statewide basis.")


def main() -> int:
    con = duckdb.connect(DB, read_only=True)
    _king_is_absent(con)
    print("WA odd-year roll-off — the blank row in Appendix F's enlargement grid")
    print(f"All figures EXCLUDE {_EXCLUDED_COUNTY} County, which is absent from the "
          f"odd-year precinct returns.\n")

    print("=== Cut 1: statewide item vs NON-KING CERTIFIED BALLOTS (an estimate — "
          "the denominator is scaled by King's ballot share) ===")
    for eid, label, ballots, king_share in ODD_YEARS:
        denom = ballots * (1 - king_share)
        rows = con.execute(f"""
            SELECT r.race_name, SUM(pr.votes) AS v
            FROM races r
            JOIN precinct_results pr USING (race_id)
            JOIN precincts p USING (precinct_id)
            WHERE r.election_id = ? AND UPPER(p.county_name) <> ?
            GROUP BY 1
            HAVING COUNT(DISTINCT pr.precinct_id) >= {_STATEWIDE_MIN_PRECINCTS}
            ORDER BY 1
        """, [eid, _EXCLUDED_COUNTY]).fetchall()
        if not rows:
            print(f"  {label}: NO statewide contest on the ballot "
                  f"(advisory votes repealed by SB 5082, eff. July 2023)")
            continue
        for name, v in rows:
            print(f"  {label}: {name:34s} {v:>9,} votes / {denom:>11,.0f} non-King "
                  f"ballots -> roll-off {100 * (denom - v) / denom:5.1f}%")
    print("  (Even-year statewide ballot measures, for comparison: 4.1-5.6%.)")

    print("\n=== Cut 2: local offices vs a per-precinct BALLOT FLOOR "
          "(lower bounds — the floor rolls off too) ===")
    header = f"  {'office':<20s}" + "".join(
        f"{lab.split()[1]:>10s}" for _, lab, _, _ in ODD_YEARS)
    print(header)
    per_year: dict[str, dict[str, float]] = {}
    for eid, label, _, _ in ODD_YEARS:
        con.execute("""
            CREATE OR REPLACE TEMP TABLE rv AS
            SELECT pr.precinct_id, r.race_name, SUM(pr.votes) AS v
            FROM precinct_results pr
            JOIN precincts p USING (precinct_id)
            JOIN races r USING (race_id)
            WHERE r.election_id = ? AND UPPER(p.county_name) <> ?
            GROUP BY 1, 2
        """, [eid, _EXCLUDED_COUNTY])
        con.execute("""
            CREATE OR REPLACE TEMP TABLE pmax AS
            SELECT precinct_id, MAX(v) AS mx FROM rv GROUP BY 1
        """)
        for grp, pct in con.execute(f"""
            SELECT {_OFFICE_GROUPS} AS grp,
                   ROUND(100.0 * (1 - SUM(rv.v) * 1.0 / SUM(pmax.mx)), 1)
            FROM rv JOIN pmax USING (precinct_id)
            WHERE pmax.mx > 0
            GROUP BY 1 HAVING grp IS NOT NULL
        """).fetchall():
            per_year.setdefault(grp, {})[label] = float(pct)

    for grp in sorted(per_year):
        cells = "".join(f"{per_year[grp].get(lab, float('nan')):9.1f}%"
                        for _, lab, _, _ in ODD_YEARS)
        print(f"  {grp:<20s}{cells}")

    con.close()
    print("\nBoth cuts are conservative. The statewide item rolls off about as much as an")
    print("even-year statewide measure does; several LOCAL offices roll off far more.")
    print("Neither supports treating odd-year roll-off as zero, which is what leaving")
    print("the grid's odd-year row blank does.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
