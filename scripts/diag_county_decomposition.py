"""D2 — split each county's dollar multiplier into participation and intensity.

Finding 2 reports, per panel, a county's share of matched dollars divided by its share of the
active roll. That multiplier conflates two different facts about a place: how many of its
residents give at all, and how much each of them gives. They mean different things. A county
that is disproportionate because a large minority of its residents are donors is a
participation story about civic composition; a county that is disproportionate because a
handful of residents give enormous sums is an intensity story about wealth, and the paper's
own concentration finding says which one to expect at the extremes.

The decomposition is exact and multiplicative, not an approximation:

    multiplier = (county $ / total $) / (county roll / total roll)
               = [(D_c / R_c) / (D / R)] x [(S_c / D_c) / (S / D)]
               =        participation ratio        x    intensity ratio

where D is matched donors, R is active registrants and S is matched dollars. So a multiplier
of 7.83 that decomposes as 1.2 x 6.5 is a very different claim from one that decomposes as
6.5 x 1.2, and the paper currently cannot tell a reader which it has.

    PYTHONPATH=src python scripts/diag_county_decomposition.py

Read-only. Writes nothing.
"""
from __future__ import annotations

from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

PANELS = [
    ("WA federal", "wa_statewide", "wa_vrdb", "voter_donor_affiliation_fec"),
    ("WA state", "wa_statewide", "wa_vrdb", "voter_donor_affiliation_state"),
    ("NY federal", "ny_statewide", "ny_vrdb", "voter_donor_affiliation_fec"),
    ("NY state", "ny_statewide", "ny_vrdb", "voter_donor_affiliation_state"),
    ("ID federal", "id_statewide", "id_vrdb", "voter_donor_affiliation_fec"),
    ("ID state", "id_statewide", "id_vrdb", "voter_donor_affiliation_state"),
]

# `status_code` is absent from Idaho's export, so its roll and active roll coincide — the
# paper says so where the age bands are reported, and the same caveat applies here.
ACTIVE = {"wa_vrdb": "status_code = 'A'", "ny_vrdb": "status_code = 'A'", "id_vrdb": "1=1"}


def county_rows(con, panel: str, active: str, top: int = 4):
    rows = con.execute(f"""
        WITH roll AS (
            SELECT UPPER(TRIM(county_name)) AS cty, COUNT(*) AS n_reg
            FROM vrdb.voters WHERE {active} AND county_name IS NOT NULL
            GROUP BY 1),
        don AS (
            SELECT UPPER(TRIM(v.county_name)) AS cty,
                   COUNT(*) AS n_don, SUM(a.total_donated) AS amt
            FROM {panel} a JOIN vrdb.voters v USING (state_voter_id)
            WHERE v.county_name IS NOT NULL
            GROUP BY 1),
        tot AS (
            SELECT (SELECT SUM(n_reg) FROM roll)  AS R,
                   (SELECT SUM(n_don) FROM don)   AS D,
                   (SELECT SUM(amt)   FROM don)   AS S)
        SELECT d.cty, r.n_reg, d.n_don, d.amt,
               100.0 * d.amt / t.S                        AS dollar_share,
               100.0 * r.n_reg / t.R                      AS roll_share,
               (d.amt / t.S) / (CAST(r.n_reg AS DOUBLE) / t.R)          AS multiplier,
               (CAST(d.n_don AS DOUBLE) / r.n_reg) / (CAST(t.D AS DOUBLE) / t.R) AS participation,
               (d.amt / d.n_don) / (t.S / CAST(t.D AS DOUBLE))          AS intensity
        FROM don d JOIN roll r USING (cty) CROSS JOIN tot t
        WHERE d.n_don >= 100
        ORDER BY multiplier DESC
        LIMIT {top}""").fetchall()
    return rows


def main() -> None:
    print("=" * 108)
    print("D2 — county dollar multipliers decomposed:  multiplier = participation x intensity")
    print("=" * 108)
    for tag, db, vrdb, panel in PANELS:
        p = DATA / f"{db}.duckdb"
        if not p.exists():
            continue
        con = duckdb.connect(str(p), read_only=True)
        try:
            con.execute(f"ATTACH '{DATA / (vrdb + '.duckdb')}' AS vrdb (READ_ONLY)")
            rows = county_rows(con, panel, ACTIVE[vrdb])
        finally:
            con.close()
        print(f"\n{tag}   (counties with >= 100 matched donors, top 4 by multiplier)")
        print(f"  {'county':<22}{'donors':>8}{'$ share':>9}{'roll share':>11}"
              f"{'mult':>8}{'particip.':>11}{'intensity':>11}   reads as")
        print("  " + "-" * 104)
        for cty, n_reg, n_don, amt, ds, rs, mult, part, inten in rows:
            # Which factor carries the multiplier is the whole point of the table.
            if part >= 1.15 and inten >= 1.15:
                reads = "both"
            elif inten > part:
                reads = "intensity — few donors, large gifts"
            elif part > inten:
                reads = "participation — many donors, ordinary gifts"
            else:
                reads = "neither dominates"
            print(f"  {cty[:21]:<22}{n_don:>8,}{ds:>8.1f}%{rs:>10.1f}%"
                  f"{mult:>8.2f}{part:>11.2f}{inten:>11.2f}   {reads}")

    print()
    print("=" * 108)
    print("The two factors multiply to the published multiplier exactly, so this adds no")
    print("assumption — it only says which half of it a county's disproportion comes from.")


if __name__ == "__main__":
    main()
