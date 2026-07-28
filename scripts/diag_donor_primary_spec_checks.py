"""Data checks the full-name-tier specification switch requires (2026-07-27).

Read-only; aggregate output only. Runs against the `_alltier` snapshots plus an independent
reconstruction of the rank-0 key, so it does NOT need the rebuilt panels and can be run
before or after them.

Each section answers a question the switch raises, in priority order:

  A  TWO DEFINITIONS, all six panels. "Full-name only" can mean filter-a-built-panel on
     `match_quality` (keeps a rank-0 voter's whole dollar total, weak-key gifts included)
     or restrict-the-match (drops them). Identical donor counts, different dollars. The
     paper must publish this delta rather than let the two figures sit inconsistently.

  B  NAMESAKE COLLISION ON THE FULL-NAME KEY — the main residual threat to the 100%
     precision claim, and the figure the paper currently gets wrong. Its published 7-9%
     was computed on a FIRST-INITIAL join, which is not the primary spec's risk at all. A
     same-name collision is undetectable by name, so this uses non-name discriminators
     (middle initial, city, employer) reported SEPARATELY, weighted by rows AND by dollars,
     and broken out by gift count — donors with many gifts have more opportunity to show
     variation, so an uncontrolled dollar figure is partly mechanical.

  C  ROLL-SIDE INACTIVE NAMESAKES. The uniqueness guard filters `status_code='A'`, so an
     INACTIVE registrant sharing the key does not block the match and their giving is
     attributed to the active twin. Not measurable for Idaho (no active flag in its export).

  D  RECALL COST OF THE RESTRICTION, by subgroup. The switch discards 11-19% of donors and
     the retained set skews older, which implies the discarded set is younger — so the
     change trades a measurement bias for a possible SELECTION bias, and the measured age
     skew rises partly for that reason. This is the strongest objection a reviewer will
     raise and it should be pre-empted with numbers, not discovered.

  E  JOINT FILINGS ("X AND Y", "X & Y"). These inflate one individual's dollar total and
     explain the partial-merge residue.

  F  MULTI-TOKEN FIRST NAMES. The roll key is UPPER(TRIM(first_name)) but the donor key is
     SPLIT_PART(name,' ',1), so a voter named "MARY ANN" can never reach rank 0. Recall
     loss, not a precision bug — worth confirming and sizing.

  G  NAME-ORDER PARSE FAILURE at population scale (WA PDC and Idaho Sunshine, the two
     comma-less sources). The paper currently cites the organisation figure as this mode's
     population analogue, which measures something else.

  H  DUPLICATE VOTER IDS reaching the panels (NY has 53 on the roll).

Run:  python scripts/diag_donor_primary_spec_checks.py
      python scripts/diag_donor_primary_spec_checks.py --sections A,B
"""
from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

DATA = Path(__file__).resolve().parent.parent / "data"

# (state, statewide db, vrdb db, {panel: (alltier table, source prefix)})
STATES = [
    ("WA", "wa_statewide", "wa_vrdb",
     {"federal": ("voter_donor_affiliation_fec_alltier", "FEC"),
      "state":   ("voter_donor_affiliation_state_alltier", "PDC")}),
    ("NY", "ny_statewide", "ny_vrdb",
     {"federal": ("voter_donor_affiliation_fec_alltier", "FEC"),
      "state":   ("voter_donor_affiliation_state_alltier", "NY")}),
    ("ID", "id_statewide", "id_vrdb",
     {"federal": ("voter_donor_affiliation_fec_alltier", "FEC"),
      "state":   ("voter_donor_affiliation_state_alltier", "SUNSHINE")}),
]
PRIMARY_TIER = "STRICT_ZIP5_FULL"


def rule(title: str, char: str = "=") -> None:
    print("\n" + char * 80 + f"\n{title}\n" + char * 80)


def contrib_keys(con, prefix: str) -> None:
    """Rank-0 contribution keys for one money layer, mirroring the matcher exactly."""
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE _ck AS
        SELECT
          CASE WHEN contributor_name LIKE '%,%'
               THEN UPPER(TRIM(SPLIT_PART(contributor_name, ',', 1)))
               ELSE UPPER(TRIM(SPLIT_PART(TRIM(contributor_name), ' ', 1))) END AS lk,
          CASE WHEN contributor_name LIKE '%,%'
               THEN UPPER(SPLIT_PART(TRIM(SPLIT_PART(contributor_name, ',', 2)), ' ', 1))
               ELSE UPPER(SPLIT_PART(TRIM(contributor_name), ' ', 2)) END       AS ff,
          CASE WHEN contributor_name LIKE '%,%'
               THEN UPPER(SUBSTR(SPLIT_PART(TRIM(SPLIT_PART(contributor_name, ',', 2)), ' ', 2), 1, 1))
               ELSE UPPER(SUBSTR(SPLIT_PART(TRIM(contributor_name), ' ', 3), 1, 1)) END AS mi,
          SUBSTR(contributor_zip, 1, 5)                                          AS z5,
          UPPER(TRIM(COALESCE(contributor_city, '')))                            AS city,
          UPPER(TRIM(COALESCE(contributor_employer, '')))                        AS emp,
          contributor_name, contribution_amount AS amt
        FROM individual_contributions
        WHERE contributor_name IS NOT NULL AND contributor_name <> ''
          AND contributor_zip IS NOT NULL AND contributor_zip <> ''
          AND UPPER(contributor_name) NOT IN
              ('SMALL CONTRIBUTIONS', 'UNITEMIZED', 'ANONYMOUS')
          AND COALESCE(contributor_type, 'UNKNOWN') NOT IN ('ORGANIZATION', 'COMMITTEE')
          AND contribution_id LIKE '{prefix}:%'
    """)


def voter_keys(con, active_only: bool = True) -> None:
    """Unique rank-0 voter keys. `active_only=False` is used for the section-C twin test."""
    where = "status_code = 'A' AND" if active_only else ""
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE _vk AS
        SELECT UPPER(TRIM(last_name)) lk, UPPER(TRIM(first_name)) ff,
               SUBSTR(reg_zip, 1, 5) z5, ANY_VALUE(state_voter_id) svid
        FROM vrdb.voters
        WHERE {where} first_name IS NOT NULL AND last_name IS NOT NULL
          AND reg_zip IS NOT NULL
        GROUP BY 1, 2, 3 HAVING COUNT(*) = 1
    """)


# --------------------------------------------------------------------- A
def section_a(con, state, panel, table, prefix):
    contrib_keys(con, prefix)
    voter_keys(con)
    filt = con.execute(
        f"SELECT COUNT(*), COALESCE(SUM(total_donated), 0) FROM {table} "
        f"WHERE match_quality = '{PRIMARY_TIER}'").fetchone()
    restr = con.execute("""
        SELECT COUNT(DISTINCT v.svid), COALESCE(SUM(k.amt), 0)
        FROM _ck k JOIN _vk v ON v.lk = k.lk AND v.ff = k.ff AND v.z5 = k.z5
        WHERE LENGTH(k.ff) >= 2""").fetchone()
    fd, rd = float(filt[1]), float(restr[1])
    print(f"  {state} {panel:8} donors {filt[0]:>8,} / {restr[0]:>8,}"
          f"{'  MATCH' if filt[0] == restr[0] else '  DIFFER'}"
          f"   $ {fd/1e6:8.2f}M vs {rd/1e6:8.2f}M"
          f"   delta ${(fd-rd)/1e6:7.2f}M ({100*(fd-rd)/fd if fd else 0:5.2f}%)")


# --------------------------------------------------------------------- B
def section_b(con, state, panel, table, prefix):
    contrib_keys(con, prefix)
    voter_keys(con)
    rows = con.execute("""
        WITH j AS (
            SELECT v.svid, k.mi, k.city, k.emp, k.amt
            FROM _ck k JOIN _vk v ON v.lk = k.lk AND v.ff = k.ff AND v.z5 = k.z5
            WHERE LENGTH(k.ff) >= 2),
        agg AS (
            SELECT svid, COUNT(*) gifts, SUM(amt) tot,
                   COUNT(DISTINCT NULLIF(mi, ''))   AS n_mi,
                   COUNT(DISTINCT NULLIF(city, '')) AS n_city,
                   COUNT(DISTINCT NULLIF(emp, ''))  AS n_emp
            FROM j GROUP BY svid)
        SELECT COUNT(*), SUM(tot),
               COUNT(*) FILTER (WHERE n_mi   > 1), SUM(tot) FILTER (WHERE n_mi   > 1),
               COUNT(*) FILTER (WHERE n_city > 1), SUM(tot) FILTER (WHERE n_city > 1),
               COUNT(*) FILTER (WHERE n_emp  > 1), SUM(tot) FILTER (WHERE n_emp  > 1)
        FROM agg""").fetchone()
    n, tot = rows[0], float(rows[1] or 0)
    print(f"\n  {state} {panel}   {n:,} rank-0 donors, ${tot/1e6:.2f}M")
    print(f"    {'discriminator':22}{'donors':>9}{'% rows':>9}{'$M':>10}{'% $':>8}")
    for lbl, cn, cd in (("2+ middle initials", rows[2], rows[3]),
                        ("2+ cities", rows[4], rows[5]),
                        ("2+ employers", rows[6], rows[7])):
        cn = cn or 0
        cd = float(cd or 0)
        print(f"    {lbl:22}{cn:>9,}{100*cn/n if n else 0:8.2f}%"
              f"{cd/1e6:9.2f}{100*cd/tot if tot else 0:7.2f}%")
    # Gift-count control: more gifts -> more chance to show variation, so an uncontrolled
    # dollar share is partly mechanical.
    print(f"    by gift count (middle-initial signal):")
    for band, lo, hi in (("1 gift", 1, 1), ("2-4", 2, 4), ("5-19", 5, 19),
                         ("20+", 20, 10 ** 9)):
        r = con.execute(f"""
            WITH j AS (SELECT v.svid, k.mi, k.amt FROM _ck k
                       JOIN _vk v ON v.lk=k.lk AND v.ff=k.ff AND v.z5=k.z5
                       WHERE LENGTH(k.ff) >= 2),
            agg AS (SELECT svid, COUNT(*) g, SUM(amt) tot,
                           COUNT(DISTINCT NULLIF(mi,'')) n_mi FROM j GROUP BY svid)
            SELECT COUNT(*), COUNT(*) FILTER (WHERE n_mi>1),
                   SUM(tot), SUM(tot) FILTER (WHERE n_mi>1)
            FROM agg WHERE g BETWEEN {lo} AND {hi}""").fetchone()
        gn, gc, gt, gcd = r[0], r[1] or 0, float(r[2] or 0), float(r[3] or 0)
        print(f"      {band:8}{gn:>9,} donors  collide {gc:>7,} "
              f"({100*gc/gn if gn else 0:5.2f}%)   ${gcd/1e6:7.2f}M of ${gt/1e6:8.2f}M "
              f"({100*gcd/gt if gt else 0:5.2f}%)")


# --------------------------------------------------------------------- C
def section_c(con, state, panel, table, prefix):
    n_active = con.execute(
        "SELECT COUNT(*) FROM vrdb.voters WHERE status_code <> 'A'").fetchone()[0]
    if not n_active:
        print(f"  {state} {panel:8} no inactive registrants in this export — "
              f"not measurable (see load_id_voters.py)")
        return
    contrib_keys(con, prefix)
    voter_keys(con)
    con.execute("""
        CREATE OR REPLACE TEMP TABLE _twin AS
        SELECT UPPER(TRIM(last_name)) lk, UPPER(TRIM(first_name)) ff,
               SUBSTR(reg_zip,1,5) z5
        FROM vrdb.voters
        WHERE status_code <> 'A' AND first_name IS NOT NULL
          AND last_name IS NOT NULL AND reg_zip IS NOT NULL
        GROUP BY 1,2,3""")
    r = con.execute("""
        WITH m AS (SELECT DISTINCT v.svid, v.lk, v.ff, v.z5
                   FROM _ck k JOIN _vk v ON v.lk=k.lk AND v.ff=k.ff AND v.z5=k.z5
                   WHERE LENGTH(k.ff) >= 2)
        SELECT COUNT(*), COUNT(*) FILTER (WHERE t.lk IS NOT NULL)
        FROM m LEFT JOIN _twin t USING (lk, ff, z5)""").fetchone()
    print(f"  {state} {panel:8} {r[1]:>7,} of {r[0]:>8,} rank-0 matches "
          f"({100*r[1]/r[0] if r[0] else 0:.2f}%) have an INACTIVE registrant sharing "
          f"the exact key")


# --------------------------------------------------------------------- D
def section_d(con, state, panel, table, prefix, age_expr, party_case):
    """Who gets discarded by the restriction — the selection-bias question."""
    sel = [f"COUNT(*) n",
           f"COUNT(*) FILTER (WHERE {age_expr} >= 65) n65",
           f"COUNT(*) FILTER (WHERE {age_expr} IS NOT NULL) nage",
           "SUM(a.total_donated) tot"]
    if party_case:
        sel.append(f"COUNT(*) FILTER (WHERE {party_case} = 'DEM') ndem")
    q = f"""SELECT {', '.join(sel)}
            FROM {table} a JOIN vrdb.voters v USING (state_voter_id)
            WHERE a.match_quality {{op}} '{PRIMARY_TIER}'"""
    keep = con.execute(q.format(op="=")).fetchone()
    drop = con.execute(q.format(op="<>")).fetchone()
    def fmt(r):
        n, n65, nage, tot = r[0], r[1], r[2], float(r[3] or 0)
        s = (f"{n:>8,}  65+ {100*n65/nage if nage else 0:5.1f}%  "
             f"${tot/1e6:8.2f}M")
        if party_case and len(r) > 4:
            s += f"  DEM {100*r[4]/n if n else 0:5.1f}%"
        return s
    print(f"\n  {state} {panel}")
    print(f"    retained (rank 0)  {fmt(keep)}")
    print(f"    DISCARDED          {fmt(drop)}")
    tn = keep[0] + drop[0]
    print(f"    discarded share of donors: {100*drop[0]/tn if tn else 0:.1f}%")


# --------------------------------------------------------------------- E
def section_e(con, state, panel, table, prefix):
    r = con.execute(f"""
        SELECT COUNT(*), SUM(contribution_amount),
               COUNT(*) FILTER (WHERE joint), SUM(contribution_amount) FILTER (WHERE joint)
        FROM (SELECT contribution_amount,
                     (contributor_name LIKE '% AND %' OR contributor_name LIKE '%&%'
                      OR contributor_name LIKE '% OR %' OR contributor_name LIKE '%/%')
                     AS joint
              FROM individual_contributions
              WHERE contribution_id LIKE '{prefix}:%' AND contributor_name IS NOT NULL
                AND contribution_amount > 0)""").fetchone()
    n, tot, jn, jd = r[0], float(r[1] or 0), r[2] or 0, float(r[3] or 0)
    print(f"  {state} {panel:8} {jn:>8,} of {n:>10,} rows joint-filed "
          f"({100*jn/n if n else 0:5.3f}%)   ${jd/1e6:7.2f}M of ${tot/1e6:9.2f}M "
          f"({100*jd/tot if tot else 0:5.3f}% of $)")


# --------------------------------------------------------------------- F
def section_f(con, state):
    r = con.execute("""
        SELECT COUNT(*), COUNT(*) FILTER (WHERE TRIM(first_name) LIKE '% %')
        FROM vrdb.voters
        WHERE status_code = 'A' AND first_name IS NOT NULL AND last_name IS NOT NULL
          AND reg_zip IS NOT NULL""").fetchone()
    print(f"  {state}  {r[1]:>9,} of {r[0]:>10,} active registrants "
          f"({100*r[1]/r[0] if r[0] else 0:.2f}%) carry a MULTI-TOKEN first name and are "
          f"therefore unreachable by the rank-0 key")


# --------------------------------------------------------------------- G
def section_g(con, state, panel, prefix):
    """Name-order parse failure signature, for the comma-less sources only."""
    has_comma = con.execute(
        f"SELECT 100.0*COUNT(*) FILTER (WHERE contributor_name LIKE '%,%')/COUNT(*) "
        f"FROM individual_contributions WHERE contribution_id LIKE '{prefix}:%' "
        f"AND contributor_name IS NOT NULL").fetchone()[0]
    if has_comma is None or float(has_comma) > 50:
        print(f"  {state} {panel:8} {float(has_comma or 0):.1f}% of names carry a comma — "
              f"parsed LAST, FIRST, so this mode does not apply")
        return
    r = con.execute(f"""
        WITH ic AS (
            SELECT UPPER(TRIM(SPLIT_PART(TRIM(contributor_name), ' ', 1))) t1,
                   UPPER(TRIM(SPLIT_PART(TRIM(contributor_name), ' ', 2))) t2,
                   contribution_amount amt
            FROM individual_contributions
            WHERE contribution_id LIKE '{prefix}:%' AND contributor_name IS NOT NULL
              AND contributor_name NOT LIKE '%,%' AND contribution_amount > 0),
        sur AS (SELECT DISTINCT UPPER(TRIM(last_name)) n FROM vrdb.voters
                WHERE last_name IS NOT NULL),
        giv AS (SELECT DISTINCT UPPER(TRIM(first_name)) n FROM vrdb.voters
                WHERE first_name IS NOT NULL)
        SELECT COUNT(*), SUM(amt),
               COUNT(*) FILTER (WHERE s1.n IS NULL AND s2.n IS NOT NULL
                                 AND g1.n IS NOT NULL),
               SUM(amt) FILTER (WHERE s1.n IS NULL AND s2.n IS NOT NULL
                                 AND g1.n IS NOT NULL)
        FROM ic
        LEFT JOIN sur s1 ON s1.n = ic.t1
        LEFT JOIN sur s2 ON s2.n = ic.t2
        LEFT JOIN giv g1 ON g1.n = ic.t1""").fetchone()
    n, tot, bn, bd = r[0], float(r[1] or 0), r[2] or 0, float(r[3] or 0)
    print(f"  {state} {panel:8} {bn:>8,} of {n:>10,} comma-less rows "
          f"({100*bn/n if n else 0:5.2f}%) look FIRST-name-first "
          f"(token1 is a given name and not a surname, token2 is a surname); "
          f"${bd/1e6:6.2f}M ({100*bd/tot if tot else 0:5.2f}% of $)")


# --------------------------------------------------------------------- H
def section_h(con, state, panels):
    dups = con.execute("""
        SELECT COUNT(*) FROM (SELECT state_voter_id FROM vrdb.voters
                              GROUP BY 1 HAVING COUNT(*) > 1)""").fetchone()[0]
    if not dups:
        print(f"  {state}  no duplicated state_voter_id on the roll")
        return
    print(f"  {state}  {dups} duplicated state_voter_id on the roll")
    for panel, (table, _p) in panels.items():
        r = con.execute(f"""
            WITH d AS (SELECT state_voter_id FROM vrdb.voters
                       GROUP BY 1 HAVING COUNT(*) > 1)
            SELECT COUNT(*), COUNT(*) FILTER (WHERE a.match_quality = '{PRIMARY_TIER}')
            FROM {table} a JOIN d USING (state_voter_id)""").fetchone()
        print(f"    {panel:8} {r[0]} in the panel, {r[1]} of them on the rank-0 key")


# ==========================================================================
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sections", default="ABCDEFGH",
                    help="subset of section letters to run (default: all)")
    args = ap.parse_args()
    want = {c.upper() for c in args.sections.replace(",", "")}

    AGE = {"WA": "date_diff('year', v.birthdate, DATE '2024-11-05')",
           "NY": "date_diff('year', v.birthdate, DATE '2024-11-05')",
           "ID": "v.age"}
    PARTY = {
        "WA": None,
        "NY": ("CASE WHEN v.party='DEM' THEN 'DEM' WHEN v.party='REP' THEN 'REP' "
               "WHEN v.party='BLK' THEN 'NOPARTY' ELSE 'OTHER' END"),
        "ID": ("CASE WHEN v.party='REP' THEN 'REP' WHEN v.party='DEM' THEN 'DEM' "
               "WHEN v.party='UNA' THEN 'UNAFF' ELSE 'OTHER' END"),
    }

    cons = {}
    for state, db, vrdb, panels in STATES:
        con = duckdb.connect(str(DATA / f"{db}.duckdb"), read_only=True)
        con.execute(f"ATTACH '{DATA / f'{vrdb}.duckdb'}' AS vrdb (READ_ONLY)")
        cons[state] = (con, panels)

    if "A" in want:
        rule("A  TWO DEFINITIONS OF 'FULL-NAME ONLY' — donors identical, dollars differ")
        print("  filter-a-panel keeps a rank-0 voter's weak-key gifts; restrict-the-match")
        print("  drops them. The panels use the latter, so this delta must be published.")
        for state, (con, panels) in cons.items():
            for panel, (table, prefix) in panels.items():
                section_a(con, state, panel, table, prefix)

    if "B" in want:
        rule("B  NAMESAKE COLLISION ON THE FULL-NAME KEY (residual risk to the 100%)")
        print("  The paper's published 7-9% was computed on a FIRST-INITIAL join and does")
        print("  not describe this key. Discriminators reported separately, not OR-ed.")
        for state, (con, panels) in cons.items():
            for panel, (table, prefix) in panels.items():
                section_b(con, state, panel, table, prefix)

    if "C" in want:
        rule("C  ROLL-SIDE INACTIVE NAMESAKES (uniqueness guard filters status_code='A')")
        for state, (con, panels) in cons.items():
            for panel, (table, prefix) in panels.items():
                section_c(con, state, panel, table, prefix)

    if "D" in want:
        rule("D  RECALL COST OF THE RESTRICTION — who gets discarded")
        print("  If the discarded set is not demographically flat, the primary spec trades")
        print("  a measurement bias for a SELECTION bias. Pre-empt this, do not discover it.")
        for state, (con, panels) in cons.items():
            for panel, (table, prefix) in panels.items():
                section_d(con, state, panel, table, prefix, AGE[state], PARTY[state])

    if "E" in want:
        rule("E  JOINT FILINGS — the partial-merge / dollar-inflation residue")
        for state, (con, panels) in cons.items():
            for panel, (table, prefix) in panels.items():
                section_e(con, state, panel, table, prefix)

    if "F" in want:
        rule("F  MULTI-TOKEN FIRST NAMES — recall loss on the rank-0 key")
        for state, (con, _panels) in cons.items():
            section_f(con, state)

    if "G" in want:
        rule("G  NAME-ORDER PARSE FAILURE at population scale (comma-less sources)")
        for state, (con, panels) in cons.items():
            for panel, (_table, prefix) in panels.items():
                section_g(con, state, panel, prefix)

    if "H" in want:
        rule("H  DUPLICATE VOTER IDS reaching the panels")
        for state, (con, panels) in cons.items():
            section_h(con, state, panels)

    for con, _ in cons.values():
        con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
