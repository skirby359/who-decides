"""Reviewer-response diagnostics for docs/donor-class-and-the-electorate.md.

Answers the recomputation asks from the 2026-07-27 external review. Read-only;
aggregate output only (the voter files carry PII, so nothing individual-level is
printed or written). Each section maps to a numbered reviewer point:

  R11  registration denominators   all-records vs ACTIVE-only baselines. The matcher
                                   itself only considers status_code='A' voters, so an
                                   all-records registration baseline compares a matched
                                   set drawn from active registrants against a
                                   denominator that includes inactive/purged records.
  R6   crossover, relabeled        D-only / R-only / MIXED / unresolved donor
                                   CLASSIFICATION shares (not dollar flows) — plus the
                                   actual dollar-flow measure, which the panel tables
                                   can support via d_amount / r_amount.
  R7   match-tier sensitivity      per-tier counts, and every headline estimate
                                   recomputed on tier subsets (drop the weakest ZIP3
                                   tier; then full-first-name tier only).
  R7   household sensitivity       headline estimates excluding matched donors who
                                   share a surname+ZIP5 (and surname+street address)
                                   with another active registrant — a deliberate
                                   over-exclusion, so it bounds the false-merge effect.
  R9   panel overlap               |federal n state|, Jaccard, and a within-person
                                   read on donors present in both systems. Tests the
                                   "nearly fixed donor population" claim.
  R5   Idaho composition           unaffiliated share of the roll / general electorate
                                   / primary electorate — denominator-free, replacing
                                   the survivorship-biased 6.6% / 83% rate pair.

The period-aligned panels (reviewer point 9) are built by a separate step, since
they need write access: see build_aligned_panels() in this file and the
`--build-aligned` flag.

Run:  python scripts/diag_donor_class_revisions.py
      python scripts/diag_donor_class_revisions.py --build-aligned   # writes panels
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import duckdb

DATA = Path(__file__).resolve().parent.parent / "data"

FED = "voter_donor_affiliation_fec"
STATE = "voter_donor_affiliation_state"

# Tier subsets, weakest-dropped-first. STRICT_ZIP5_FULL is (last, full first, zip5);
# STRICT_ZIP5_MID is (last, first initial, middle initial, zip5); STRICT_ZIP5 is
# (last, first initial, zip5); RELAXED_ZIP3_MID is the weakest — it widens the
# geography to ZIP3 and leans on the middle initial to disambiguate.
TIER_SUBSETS = [
    ("all tiers", None),
    ("drop ZIP3 tier", ("STRICT_ZIP5_FULL", "STRICT_ZIP5_MID", "STRICT_ZIP5")),
    ("full-first-name only", ("STRICT_ZIP5_FULL",)),
]


def rule(title: str, char: str = "=") -> None:
    print("\n" + char * 78)
    print(title)
    print(char * 78)


def tier_sql(tiers: tuple[str, ...] | None, alias: str = "") -> str:
    """WHERE fragment restricting a panel table to a tier subset."""
    if tiers is None:
        return ""
    col = f"{alias}.match_quality" if alias else "match_quality"
    quoted = ", ".join(f"'{t}'" for t in tiers)
    return f" AND {col} IN ({quoted})"


# --------------------------------------------------------------------------
# shared metric helpers — each takes an extra WHERE fragment so the same
# estimator serves the tier and household sensitivities
# --------------------------------------------------------------------------
def concentration(con, panel: str, extra: str = "") -> tuple[int, float, float, float]:
    """(donors, $M, top-1% share, Gini) — Finding 2's estimator, NTILE(100)."""
    n, tot = con.execute(
        f"SELECT COUNT(*), COALESCE(SUM(total_donated), 0)/1e6 FROM {panel} "
        f"WHERE 1=1 {extra}").fetchone()
    if not n:
        return 0, 0.0, float("nan"), float("nan")
    top1 = con.execute(f"""
        WITH r AS (SELECT total_donated t, NTILE(100) OVER (ORDER BY total_donated DESC) p
                   FROM {panel} WHERE total_donated > 0 {extra})
        SELECT 100.0*SUM(t) FILTER (WHERE p=1)/SUM(t) FROM r""").fetchone()[0]
    gini = con.execute(f"""
        WITH r AS (SELECT total_donated t, ROW_NUMBER() OVER (ORDER BY total_donated) rn,
                          COUNT(*) OVER () n, SUM(total_donated) OVER () s
                   FROM {panel} WHERE total_donated > 0 {extra})
        SELECT (2.0*SUM(rn*t)/(MAX(n)*MAX(s))) - (MAX(n)+1.0)/MAX(n) FROM r""").fetchone()[0]
    return int(n), float(tot), float(top1), float(gini)


def senior_share(con, panel: str, age_expr: str, extra: str = "") -> float:
    """65+ share of matched donors."""
    row = con.execute(f"""
        SELECT 100.0*COUNT(*) FILTER (WHERE {age_expr} >= 65)/NULLIF(COUNT(*), 0)
        FROM {panel} a JOIN vrdb.voters v USING (state_voter_id)
        WHERE {age_expr} IS NOT NULL {extra}""").fetchone()[0]
    return float(row) if row is not None else float("nan")


def party_shares(con, panel: str, party_case: str, extra: str = "") -> dict[str, float]:
    """Matched-donor own-party shares (percent)."""
    rows = con.execute(f"""
        SELECT {party_case} b, 100.0*COUNT(*)/SUM(COUNT(*)) OVER ()
        FROM {panel} a JOIN vrdb.voters v USING (state_voter_id)
        WHERE 1=1 {extra} GROUP BY 1""").fetchall()
    return {b: float(p) for b, p in rows}


def registration_shares(con, party_case: str, active_only: bool) -> dict[str, float]:
    where = "WHERE status_code = 'A'" if active_only else ""
    rows = con.execute(f"""
        SELECT {party_case} b, 100.0*COUNT(*)/SUM(COUNT(*)) OVER ()
        FROM vrdb.voters v {where} GROUP BY 1""").fetchall()
    return {b: float(p) for b, p in rows}


# --------------------------------------------------------------------------
# R11 — registration denominators
# --------------------------------------------------------------------------
def report_denominators(con, state: str, party_case: str, order: list[str],
                        panels: dict[str, str]) -> None:
    rule(f"R11  {state}: registration denominator — ALL records vs ACTIVE only")
    tot_all, tot_act = con.execute("""
        SELECT COUNT(*), COUNT(*) FILTER (WHERE status_code = 'A') FROM vrdb.voters""").fetchone()
    print(f"  roll: {tot_all:,} records, {tot_act:,} active "
          f"({100.0*tot_act/tot_all:.1f}%)")
    if tot_all == tot_act:
        print("  -> no record is flagged inactive. For ID this is because the export")
        print("     carries no active/inactive flag (load_id_voters.py sets every row")
        print("     'A'), so the two baselines coincide by construction, not by fact.")
    reg_all = registration_shares(con, party_case, active_only=False)
    reg_act = registration_shares(con, party_case, active_only=True)
    print("\n  NB the matcher only draws donors from status_code='A' voters, so the")
    print("     ACTIVE baseline is the one commensurable with the matched set.")
    for label, panel in panels.items():
        don = party_shares(con, panel, party_case)
        print(f"\n  {label} panel")
        print(f"    {'party':10}{'reg(all)':>10}{'reg(act)':>10}{'donor':>9}"
              f"{'skew/all':>10}{'skew/act':>10}{'delta':>8}")
        for b in order:
            ra, rc, d = reg_all.get(b, 0.0), reg_act.get(b, 0.0), don.get(b, 0.0)
            print(f"    {b:10}{ra:9.1f}%{rc:9.1f}%{d:8.1f}%"
                  f"{d - ra:+9.1f}{d - rc:+9.1f}{(d - rc) - (d - ra):+8.1f}")


# --------------------------------------------------------------------------
# R6 — crossover, correctly labelled, with MIXED and dollar flow
# --------------------------------------------------------------------------
def report_crossover(con, state: str, party_case: str, order: list[str],
                     panels: dict[str, str]) -> None:
    rule(f"R6  {state}: donor CLASSIFICATION by own party (not dollar flow)")
    print("  donor_party is a classification of a donor's resolved recipients:")
    print("    D-only = every resolved recipient was D; R-only = every one R;")
    print("    MIXED  = gave to both; unresolved = no recipient carried a party.")
    print("  Percentages are of RESOLVED donors (D-only + R-only + MIXED = 100%).")
    print("  The final column is the separate DOLLAR-flow measure:")
    print("    share of a group's party-resolved dollars that went to D recipients.")
    for label, panel in panels.items():
        rows = con.execute(f"""
            SELECT {party_case} AS own,
                   COUNT(*)                                             AS matched,
                   COUNT(*) FILTER (WHERE donor_party <> 'OTHER')        AS resolved,
                   COUNT(*) FILTER (WHERE donor_party = 'D_DONOR')       AS d_only,
                   COUNT(*) FILTER (WHERE donor_party = 'R_DONOR')       AS r_only,
                   COUNT(*) FILTER (WHERE donor_party = 'MIXED')         AS mixed,
                   COALESCE(SUM(a.d_amount), 0)                          AS d_amt,
                   COALESCE(SUM(a.r_amount), 0)                          AS r_amt
            FROM {panel} a JOIN vrdb.voters v USING (state_voter_id)
            GROUP BY 1""").fetchall()
        by = {r[0]: r for r in rows}
        print(f"\n  {label} panel")
        print(f"    {'own party':10}{'matched':>10}{'resolved':>10}{'res%':>7}"
              f"{'D-only':>8}{'R-only':>8}{'MIXED':>8}{'  |':>4}{'$ to D':>9}")
        for b in order:
            if b not in by:
                continue
            _, matched, resolved, d1, r1, mx, damt, ramt = by[b]
            res_pct = 100.0 * resolved / matched if matched else float("nan")
            den = float(damt) + float(ramt)
            dollar_d = 100.0 * float(damt) / den if den else float("nan")
            f = (lambda x: 100.0 * x / resolved if resolved else float("nan"))
            print(f"    {b:10}{matched:>10,}{resolved:>10,}{res_pct:6.1f}%"
                  f"{f(d1):7.1f}%{f(r1):7.1f}%{f(mx):7.1f}%{'  |':>4}"
                  f"{dollar_d:8.1f}%")


# --------------------------------------------------------------------------
# R7 — match-tier sensitivity
# --------------------------------------------------------------------------
def report_tiers(con, state: str, panels: dict[str, str], age_expr: str | None,
                 party_case: str | None, order: list[str] | None) -> None:
    rule(f"R7  {state}: match-tier composition and headline sensitivity")
    for label, panel in panels.items():
        print(f"\n  {label} panel — tier composition")
        rows = con.execute(f"""
            SELECT match_quality, COUNT(*), 100.0*COUNT(*)/SUM(COUNT(*)) OVER (),
                   COALESCE(SUM(total_donated), 0)/1e6
            FROM {panel} GROUP BY 1 ORDER BY 2 DESC""").fetchall()
        for q, n, pct, m in rows:
            print(f"    {q:20}{n:>9,}{pct:7.1f}%   ${float(m):9.2f}M")

        print(f"  {label} panel — headline estimates by tier subset")
        hdr = f"    {'subset':22}{'donors':>9}{'top-1%':>9}{'Gini':>8}"
        if age_expr:
            hdr += f"{'65+':>8}"
        if party_case and order:
            hdr += "".join(f"{b:>9}" for b in order)
        print(hdr)
        for name, tiers in TIER_SUBSETS:
            extra = tier_sql(tiers)
            n, _tot, t1, g = concentration(con, panel, extra)
            line = f"    {name:22}{n:>9,}{t1:8.1f}%{g:8.3f}"
            if age_expr:
                line += f"{senior_share(con, panel, age_expr, tier_sql(tiers, 'a')):7.1f}%"
            if party_case and order:
                ps = party_shares(con, panel, party_case, tier_sql(tiers, "a"))
                line += "".join(f"{ps.get(b, 0.0):8.1f}%" for b in order)
            print(line)


# --------------------------------------------------------------------------
# R7 — household false-merge sensitivity
# --------------------------------------------------------------------------
def report_households(con, state: str, panels: dict[str, str],
                      age_expr: str | None, has_street: bool) -> None:
    rule(f"R7  {state}: household false-merge sensitivity (bounding exclusion)")
    print("  A matched donor is flagged HOUSEHOLD-RISK when another ACTIVE registrant")
    print("  shares their surname and ZIP5 — the configuration in which a spouse's")
    print("  gift can be attributed to the wrong person. This deliberately")
    print("  over-excludes (most such matches are correct, since the match key also")
    print("  required a unique first name), so the excluded-set estimates BOUND the")
    print("  false-merge effect rather than correcting for it.")
    con.execute("""
        CREATE OR REPLACE TEMP TABLE _hh_zip AS
        SELECT UPPER(TRIM(last_name)) ln, SUBSTR(reg_zip, 1, 5) z5
        FROM vrdb.voters
        WHERE status_code = 'A' AND last_name IS NOT NULL AND reg_zip IS NOT NULL
        GROUP BY 1, 2 HAVING COUNT(*) > 1""")
    flag_zip = ("""AND NOT EXISTS (SELECT 1 FROM _hh_zip h
        WHERE h.ln = UPPER(TRIM(v.last_name)) AND h.z5 = SUBSTR(v.reg_zip, 1, 5))""")
    variants = [("all matched donors", ""), ("excl. surname+ZIP5 shared", flag_zip)]
    if has_street:
        con.execute("""
            CREATE OR REPLACE TEMP TABLE _hh_addr AS
            SELECT UPPER(TRIM(last_name)) ln, SUBSTR(reg_zip, 1, 5) z5,
                   UPPER(TRIM(COALESCE(reg_street_num, ''))) sn,
                   UPPER(TRIM(COALESCE(reg_street_name, ''))) st
            FROM vrdb.voters
            WHERE status_code = 'A' AND last_name IS NOT NULL AND reg_zip IS NOT NULL
            GROUP BY 1, 2, 3, 4 HAVING COUNT(*) > 1""")
        variants.append(("excl. surname+address shared", """
            AND NOT EXISTS (SELECT 1 FROM _hh_addr h
              WHERE h.ln = UPPER(TRIM(v.last_name))
                AND h.z5 = SUBSTR(v.reg_zip, 1, 5)
                AND h.sn = UPPER(TRIM(COALESCE(v.reg_street_num, '')))
                AND h.st = UPPER(TRIM(COALESCE(v.reg_street_name, ''))))"""))

    for label, panel in panels.items():
        print(f"\n  {label} panel")
        head = f"    {'variant':30}{'donors':>9}{'$M':>10}{'top-1%':>9}{'Gini':>8}"
        if age_expr:
            head += f"{'65+':>8}"
        print(head)
        for vname, pred in variants:
            # concentration() filters the panel alone, so join the roll in a view
            con.execute(f"""
                CREATE OR REPLACE TEMP VIEW _hh_panel AS
                SELECT a.* FROM {panel} a JOIN vrdb.voters v USING (state_voter_id)
                WHERE 1=1 {pred}""")
            n, tot, t1, g = concentration(con, "_hh_panel")
            line = f"    {vname:30}{n:>9,}{tot:9.1f}{t1:8.1f}%{g:8.3f}"
            if age_expr:
                line += f"{senior_share(con, '_hh_panel', age_expr):7.1f}%"
            print(line)


# --------------------------------------------------------------------------
# R7 — donor-side false-merge risk, per tier, over the WHOLE panel
# --------------------------------------------------------------------------
def report_donorside_risk(con, state: str, panels: dict[str, str],
                          prefixes: dict[str, str]) -> None:
    """Auditable per-tier precision indicators, computed on every matched donor.

    The 150-record hand rating was drawn unstratified from the pooled table and its
    per-record verdicts were never persisted, so it cannot yield per-tier precision
    (it holds ~3 records in the weakest tier). These two indicators need no human
    step, run over the full panel, and are reproducible:

      full-first-name agreement — the donor-side full first name equals the voter's.
        A match that clears this is not a first-initial ambiguity at all.
      namesake collision — the match key also pulls contributions carrying a
        DIFFERENT full first name, i.e. a distinct person shares the key. This is
        the population actually at risk of the household/relative false merge, and
        it is the direct donor-side analogue of the roll-side flag above.
    """
    rule(f"R7  {state}: per-tier false-merge risk on the donor side (full panel)")
    for label, panel in panels.items():
        prefix = prefixes[label]
        con.execute(f"""
            CREATE OR REPLACE TEMP TABLE _ic_keys AS
            SELECT
              CASE WHEN contributor_name LIKE '%,%'
                   THEN UPPER(TRIM(SPLIT_PART(contributor_name, ',', 1)))
                   ELSE UPPER(SPLIT_PART(TRIM(contributor_name), ' ', 1)) END lk,
              CASE WHEN contributor_name LIKE '%,%'
                   THEN SPLIT_PART(UPPER(TRIM(SPLIT_PART(contributor_name, ',', 2))), ' ', 1)
                   ELSE UPPER(SPLIT_PART(TRIM(contributor_name), ' ', 2)) END ffull,
              LEFT(contributor_zip, 5) z5
            FROM individual_contributions
            WHERE contribution_amount > 0 AND contributor_name IS NOT NULL
              AND contributor_zip IS NOT NULL
              AND UPPER(contributor_name) NOT IN
                  ('SMALL CONTRIBUTIONS', 'UNITEMIZED', 'ANONYMOUS')
              AND contribution_id LIKE '{prefix}:%'""")
        rows = con.execute(f"""
            WITH keyed AS (
                SELECT a.match_quality,
                       UPPER(TRIM(v.last_name)) lk,
                       UPPER(SPLIT_PART(UPPER(TRIM(v.first_name)), ' ', 1)) ff,
                       UPPER(SUBSTR(TRIM(v.first_name), 1, 1)) fi,
                       SUBSTR(v.reg_zip, 1, 5) z5
                FROM {panel} a JOIN vrdb.voters v USING (state_voter_id)
                WHERE v.first_name IS NOT NULL AND v.last_name IS NOT NULL
                  AND v.reg_zip IS NOT NULL),
            joined AS (
                SELECT k.match_quality,
                       MAX(CASE WHEN i.ffull = k.ff THEN 1 ELSE 0 END) agree,
                       COUNT(DISTINCT i.ffull) nfirst
                FROM keyed k
                LEFT JOIN _ic_keys i
                       ON i.lk = k.lk AND i.z5 = k.z5 AND LEFT(i.ffull, 1) = k.fi
                GROUP BY k.match_quality, k.lk, k.ff, k.fi, k.z5)
            SELECT match_quality, COUNT(*) n,
                   100.0*SUM(agree)/COUNT(*) agree_pct,
                   100.0*COUNT(*) FILTER (WHERE nfirst > 1)/COUNT(*) collide_pct
            FROM joined GROUP BY 1 ORDER BY n DESC""").fetchall()
        print(f"\n  {label} panel")
        print(f"    {'tier':22}{'donors':>9}{'full-name agrees':>19}{'namesake collision':>21}")
        for q, n, agree, coll in rows:
            print(f"    {q:22}{n:>9,}{float(agree):18.1f}%{float(coll):20.1f}%")


# --------------------------------------------------------------------------
# R9 — federal / state panel overlap
# --------------------------------------------------------------------------
def report_overlap(con, state: str, age_expr: str | None) -> None:
    rule(f"R9  {state}: federal vs state panel overlap (is the donor pool 'fixed'?)")
    f_n, s_n, both = con.execute(f"""
        SELECT (SELECT COUNT(*) FROM {FED}), (SELECT COUNT(*) FROM {STATE}),
               (SELECT COUNT(*) FROM (SELECT state_voter_id FROM {FED}
                 INTERSECT SELECT state_voter_id FROM {STATE}))""").fetchone()
    union = f_n + s_n - both
    print(f"  federal {f_n:,} | state {s_n:,} | both {both:,} | union {union:,}")
    print(f"  Jaccard |F n S| / |F u S| = {both/union:.3f}")
    print(f"  share of federal donors also in state panel = {100.0*both/f_n:.1f}%")
    print(f"  share of state donors also in federal panel = {100.0*both/s_n:.1f}%")
    if age_expr:
        rows = con.execute(f"""
            WITH f AS (SELECT state_voter_id, total_donated FROM {FED}),
                 s AS (SELECT state_voter_id, total_donated FROM {STATE}),
            grp AS (
              SELECT 'federal only' g, f.state_voter_id FROM f
                LEFT JOIN s USING (state_voter_id) WHERE s.state_voter_id IS NULL
              UNION ALL SELECT 'state only', s.state_voter_id FROM s
                LEFT JOIN f USING (state_voter_id) WHERE f.state_voter_id IS NULL
              UNION ALL SELECT 'both systems', f.state_voter_id FROM f
                JOIN s USING (state_voter_id))
            SELECT g, COUNT(*),
                   100.0*COUNT(*) FILTER (WHERE {age_expr} >= 65)/COUNT(*)
            FROM grp JOIN vrdb.voters v USING (state_voter_id)
            WHERE {age_expr} IS NOT NULL GROUP BY 1 ORDER BY 2 DESC""").fetchall()
        print(f"\n  within-person read — 65+ share by which system(s) they give in:")
        print(f"    {'group':16}{'donors':>10}{'65+':>8}")
        for g, n, sr in rows:
            print(f"    {g:16}{n:>10,}{float(sr):7.1f}%")
        print("  If 'federal money is older money' were purely a property of the")
        print("  regulatory layer, the both-systems group would sit between the two")
        print("  single-system groups rather than outside them.")


# --------------------------------------------------------------------------
# R5 — Idaho composition shares, denominator-free
# --------------------------------------------------------------------------
def report_idaho_composition(con) -> None:
    rule("R5  Idaho: unaffiliated COMPOSITION shares (replaces the 6.6% / 83% rates)")
    print("  Composition needs no denominator, so it is immune to the current-roll")
    print("  survivorship that makes Idaho turnout RATES unreliable. Party is measured")
    print("  at the voter-file extract date, AFTER any election-day affiliation change.")
    rows = con.execute("""
        WITH roll AS (SELECT state_voter_id, party FROM vrdb.voters),
        ge AS (SELECT DISTINCT state_voter_id FROM vrdb.voter_participation
               WHERE election_year = 2024 AND kind = 'GENERAL'),
        pr AS (SELECT DISTINCT state_voter_id FROM vrdb.voter_participation
               WHERE election_year = 2024 AND kind = 'PRIMARY'),
        pops AS (
          SELECT 'registration roll' pop, party FROM roll
          UNION ALL SELECT '2024 general electorate', r.party FROM roll r JOIN ge USING (state_voter_id)
          UNION ALL SELECT '2024 primary electorate', r.party FROM roll r JOIN pr USING (state_voter_id))
        SELECT pop, COUNT(*) n,
          100.0*COUNT(*) FILTER (WHERE party = 'REP')/COUNT(*) rep,
          100.0*COUNT(*) FILTER (WHERE party = 'DEM')/COUNT(*) dem,
          100.0*COUNT(*) FILTER (WHERE party = 'UNA')/COUNT(*) una
        FROM pops GROUP BY 1""").fetchall()
    order = ["registration roll", "2024 general electorate", "2024 primary electorate"]
    by = {r[0]: r for r in rows}
    print(f"\n    {'population':26}{'people':>11}{'REP':>8}{'DEM':>8}{'UNAFF':>8}")
    for k in order:
        if k not in by:
            continue
        _, n, rep, dem, una = by[k]
        print(f"    {k:26}{n:>11,}{float(rep):7.1f}%{float(dem):7.1f}%{float(una):7.1f}%")
    ballots = con.execute("""
        SELECT ballot_choice, COUNT(*) FROM vrdb.voter_participation
        WHERE election_year = 2024 AND kind = 'PRIMARY'
          AND ballot_choice IS NOT NULL AND ballot_choice <> ''
        GROUP BY 1 ORDER BY 2 DESC LIMIT 8""").fetchall()
    if ballots:
        tot = sum(n for _, n in ballots)
        print(f"\n    2024 primary ballots actually pulled (n={tot:,}):")
        for bc, n in ballots:
            print(f"      {bc:24}{n:>9,}{100.0*n/tot:7.1f}%")


# --------------------------------------------------------------------------
# aligned-window panels (writes)
# --------------------------------------------------------------------------
ALIGNED = [
    # (state, statewide db, vrdb, source prefix, window, output table)
    ("ID", "id_statewide", "id_vrdb", "FEC", ("2023-01-01", "2025-12-31"),
     "voter_donor_affiliation_fec_aligned"),
    ("ID", "id_statewide", "id_vrdb", "SUNSHINE", ("2023-01-01", "2025-12-31"),
     "voter_donor_affiliation_state_aligned"),
]


def build_aligned_panels() -> int:
    """Rebuild the Idaho panels on the shared 2023-2025 window.

    Idaho Sunshine holds 2023-2025; the FEC layer holds 2017-2026. Comparing them
    unwindowed confounds the regulatory difference with a decade-vs-three-years
    difference in election portfolio (reviewer point 9). Sunshine is re-matched on
    the same window too, so both panels come from the identical code path.
    """
    # The matcher ships beside this file as donor_matcher.py — a standalone extract of
    # the private product's match_voters_to_donors, function body verbatim.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from donor_matcher import (
        PRIMARY_TIERS, ensure_schema, match_voters_to_donors,
    )

    for state, db, vrdb, prefix, (dmin, dmax), out in ALIGNED:
        print(f"\n[{state}] {prefix} -> {out}   window {dmin} .. {dmax}   "
              f"tiers={list(PRIMARY_TIERS)}")
        con = duckdb.connect(str(DATA / f"{db}.duckdb"))
        con.execute(f"ATTACH '{DATA / f'{vrdb}.duckdb'}' AS vrdb (READ_ONLY)")
        ensure_schema(con)
        # These are paper panels, so they take the primary specification like the rest.
        res = match_voters_to_donors(
            con, source_prefixes=[prefix], output_table=out,
            date_min=dmin, date_max=dmax, tiers=list(PRIMARY_TIERS))
        print(f"  matched_voters={res.get('matched_voters'):,} "
              f"contributions={res.get('contributions_matched'):,}")
        con.close()
    return 0


def report_aligned(con, state: str, age_expr: str, party_case: str,
                   order: list[str]) -> None:
    """Compare unwindowed vs period-aligned panels (reviewer point 9)."""
    have = {r[0] for r in con.execute(
        "SELECT table_name FROM information_schema.tables").fetchall()}
    pairs = [("federal, full window 2017-2026", FED),
             ("federal, aligned 2023-2025", FED + "_aligned"),
             ("state, full window 2023-2025", STATE),
             ("state, aligned 2023-2025", STATE + "_aligned")]
    if not all(p in have for _, p in pairs):
        print(f"\n  !! {state}: aligned panels missing — run with --build-aligned")
        return
    rule(f"R9  {state}: period-aligned vs full-window panels")
    print("  'federal money is older money' is a claim about the money SYSTEM. It is")
    print("  only identified if both panels cover the same years. Compare rows 1-2.")
    print(f"\n    {'panel':32}{'donors':>9}{'$M':>9}{'top-1%':>9}{'65+':>8}"
          + "".join(f"{b:>9}" for b in order))
    for label, panel in pairs:
        n, tot, t1, _g = concentration(con, panel)
        sr = senior_share(con, panel, age_expr)
        ps = party_shares(con, panel, party_case)
        print(f"    {label:32}{n:>9,}{tot:8.1f}{t1:8.1f}%{sr:7.1f}%"
              + "".join(f"{ps.get(b, 0.0):8.1f}%" for b in order))


# ==========================================================================
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--build-aligned", action="store_true",
                    help="rebuild the period-aligned Idaho panels (writes)")
    args = ap.parse_args()
    if args.build_aligned:
        return build_aligned_panels()

    NY_PARTY = ("CASE WHEN v.party='DEM' THEN 'DEM' WHEN v.party='REP' THEN 'REP' "
                "WHEN v.party='BLK' THEN 'NOPARTY' ELSE 'OTHER' END")
    NY_PARTY_REG = NY_PARTY  # vrdb.voters is aliased v in both contexts
    NY_ORDER = ["DEM", "REP", "NOPARTY", "OTHER"]
    NY_AGE = "date_diff('year', v.birthdate, DATE '2024-11-05')"
    ID_PARTY = ("CASE WHEN v.party='REP' THEN 'REP' WHEN v.party='DEM' THEN 'DEM' "
                "WHEN v.party='UNA' THEN 'UNAFF' ELSE 'OTHER' END")
    ID_ORDER = ["REP", "DEM", "UNAFF", "OTHER"]
    PANELS = {"federal": FED, "state": STATE}
    # The tier-sensitivity, household and donor-side-risk sections MUST read the
    # `_alltier` snapshots (2026-07-27). The primaries are now single-tier, so comparing
    # tier subsets against them is meaningless: three of the four subsets would return
    # zero rows and the comparison would silently read as "no difference".
    PANELS_ALL = {"federal": FED + "_alltier", "state": STATE + "_alltier"}

    # ---------------- NEW YORK ----------------
    rule("NEW YORK  (ny_statewide + ny_vrdb)", "#")
    ny = duckdb.connect(str(DATA / "ny_statewide.duckdb"), read_only=True)
    ny.execute(f"ATTACH '{DATA / 'ny_vrdb.duckdb'}' AS vrdb (READ_ONLY)")
    report_denominators(ny, "NY", NY_PARTY_REG, NY_ORDER, PANELS)
    report_crossover(ny, "NY", NY_PARTY, NY_ORDER, PANELS)
    report_tiers(ny, "NY", PANELS_ALL, NY_AGE, NY_PARTY, NY_ORDER)
    report_households(ny, "NY", PANELS_ALL, NY_AGE, has_street=True)
    report_donorside_risk(ny, "NY", PANELS_ALL, {"federal": "FEC", "state": "NY"})
    report_overlap(ny, "NY", NY_AGE)
    ny.close()

    # ---------------- IDAHO ----------------
    rule("IDAHO  (id_statewide + id_vrdb)", "#")
    idc = duckdb.connect(str(DATA / "id_statewide.duckdb"), read_only=True)
    idc.execute(f"ATTACH '{DATA / 'id_vrdb.duckdb'}' AS vrdb (READ_ONLY)")
    report_denominators(idc, "ID", ID_PARTY, ID_ORDER, PANELS)
    report_crossover(idc, "ID", ID_PARTY, ID_ORDER, PANELS)
    report_tiers(idc, "ID", PANELS_ALL, "v.age", ID_PARTY, ID_ORDER)
    report_households(idc, "ID", PANELS_ALL, "v.age", has_street=True)
    report_donorside_risk(idc, "ID", PANELS_ALL, {"federal": "FEC", "state": "SUNSHINE"})
    report_overlap(idc, "ID", "v.age")
    report_idaho_composition(idc)
    report_aligned(idc, "ID", "v.age", ID_PARTY, ID_ORDER)
    idc.close()

    # ---------------- WASHINGTON ----------------
    rule("WASHINGTON  (wa_statewide + wa_vrdb)", "#")
    wa = duckdb.connect(str(DATA / "wa_statewide.duckdb"), read_only=True)
    wa.execute(f"ATTACH '{DATA / 'wa_vrdb.duckdb'}' AS vrdb (READ_ONLY)")
    WA_AGE = "date_diff('year', v.birthdate, DATE '2024-11-05')"
    print("\n  (WA publishes no party of record, so there is no denominator or")
    print("   crossover cut here — only the tier, household and overlap tests.)")
    report_tiers(wa, "WA", PANELS_ALL, WA_AGE, None, None)
    report_households(wa, "WA", PANELS_ALL, WA_AGE, has_street=True)
    report_donorside_risk(wa, "WA", PANELS_ALL, {"federal": "FEC", "state": "PDC"})
    report_overlap(wa, "WA", WA_AGE)
    wa.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
