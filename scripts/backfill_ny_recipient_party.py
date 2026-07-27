"""Resolve NY *state* (NYSBOE) recipient party, so the state panel's crossover works.

The NY counterpart of backfill_id_recipient_party.py. NYSBOE publishes no party column
on the filer, so `donor_party` / `donation_lean` on the NY **state** panel resolved for
only 25.9% of matched donors and the paper could not report a state crossover table.
This backfills recipient party from sources already on disk and writes the result to
`committee_party_override`, which `match_voters_to_donors` COALESCEs over
`candidate_finance.party` — so the fix flows through the existing matcher untouched.

Four tiers, highest confidence first. Every tier is uniqueness-guarded: a filer that
resolves to more than one party is dropped, not guessed.

  1. EXPLICIT PARTY IN THE COMMITTEE NAME. NYSBOE committee names routinely carry the
     party outright ("NEW YORK STATE DEMOCRATIC COMMITTEE", "NASSAU COUNTY REPUBLICAN
     COMMITTEE"). Applied to the filer name, with a guard against names that mention
     both parties.
  2. candidate_finance.party WHERE ALREADY KNOWN. 2,365 NY rows carry a real party from
     earlier loads; they are trusted over any inference below.
  3. COMMITTEE -> CANDIDATE -> PARTY via ny_committee_candidate_map, restricted to its
     `first_last` method. That table's `last_unique` tier is NOT usable: it matches on a
     bare surname and produces howlers like "COMMITTEE TO ELECT LAKISHA FOR YONKERS" ->
     "ETHAN YONKERS" and "COUNCIL OF SCHOOL SUPERVISORS ..." -> "KIMBERLY COUNCIL".
  4. FULL-NAME CONTAINMENT against the election-results `candidates` roster: the
     committee name contains a candidate's full "FIRST LAST" ("FRIENDS FOR KATHY
     HOCHUL"). Requires the name to be >= 9 characters and to map to exactly one party
     across the whole roster, which keeps common short names out.

DELIBERATELY LEFT UNRESOLVED: corporate, labor and trade PACs (PFIZER INC PAC, VOICE OF
TEACHERS FOR EDUCATION, GREENBERG TRAURIG P.A. PAC, NORTHWESTERN MUTUAL ...). These are
genuinely non-partisan recipients, they are a large share of NY state money, and
assigning them a party would manufacture a crossover finding rather than measure one.
Unresolved is the correct answer for them, exactly as in Idaho.

A BARE-SURNAME TIER WAS BUILT, TESTED AND REJECTED. Idaho's backfill can fall back to a
uniqueness-guarded surname because its recipient strings are "LAST, FIRST" candidate
names. New York's are free-text committee names, so the same fallback has to search for
a surname *inside* a phrase, and it misfires badly: it read "FRIENDS OF DAVID KNAPP" as
Republican via DAVID and "SARATOGA COUNTY GREEN PARTY" as Republican via GREEN — first
names and party words colliding with real surnames on the roster. It would have added
~$67M of party-resolved money at the cost of silently wrong assignments, so it is not
used. Coverage below is lower as a result, and honest.

MINOR PARTIES: Conservative and Working Families filers are counted in the report but
NOT written, because committee_party_override carries a CHECK constraint admitting only
'Democratic'/'Republican' and the matcher's D/R split has nowhere to put a third party.
New York's fusion system means those lines usually cross-endorse a major-party candidate;
inferring which would be a guess, so they stay unresolved.

Run after scripts/load_ny_contributions.py, then rebuild the panel:

    python scripts/backfill_ny_recipient_party.py
    STATE=NY python scripts/match_ny_voters_to_donors.py --source state
"""
import os
import sys

import duckdb

os.environ.setdefault("STATE", "NY")
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "src"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

NY_STATEWIDE = "data/ny_statewide.duckdb"
SOURCE = "ny_recipient_backfill"

# Party words in a committee name. NY's minor parties matter here: Conservative and
# Working Families are real ballot lines that fusion-endorse major-party candidates, so
# they are recorded under their own labels rather than folded into R/D.
DEM_RE = r"(DEMOCRAT)"
REP_RE = r"(REPUBLICAN|\bG\.?O\.?P\.?\b)"
CON_RE = r"(CONSERVATIVE PARTY|CONSERVATIVE COMMITTEE)"
WFP_RE = r"(WORKING FAMILIES)"


def build_map(con) -> None:
    # Tier 4 source: full candidate names that map to exactly one party statewide.
    con.execute("""
        CREATE OR REPLACE TEMP TABLE _cand_party AS
        SELECT nm, ANY_VALUE(party) party FROM (
            SELECT UPPER(TRIM(candidate_name)) nm, party_normalized party
            FROM candidates
            WHERE party_normalized IN ('Republican', 'Democratic')
              AND candidate_name IS NOT NULL
              AND LENGTH(TRIM(candidate_name)) >= 9
              AND candidate_name NOT IN ('UNDERVOTES', 'OVERVOTES', 'WRITE-IN')
        ) GROUP BY nm HAVING COUNT(DISTINCT party) = 1
    """)

    # Tier 3 source: only the reliable arm of the committee->candidate map.
    con.execute("""
        CREATE OR REPLACE TEMP TABLE _map_party AS
        SELECT m.filer_id, ANY_VALUE(c.party_normalized) party
        FROM ny_committee_candidate_map m
        JOIN candidates c
          ON UPPER(TRIM(c.candidate_name)) = UPPER(TRIM(m.resolved_candidate_name))
        WHERE m.match_method = 'first_last'
          AND c.party_normalized IN ('Republican', 'Democratic')
        GROUP BY m.filer_id HAVING COUNT(DISTINCT c.party_normalized) = 1
    """)

    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE _recip_party AS
        WITH f AS (
            SELECT DISTINCT cf.fec_candidate_id,
                   UPPER(TRIM(cf.candidate_name)) nm,
                   REPLACE(cf.fec_candidate_id, 'NY:', '') filer_id,
                   ANY_VALUE(cf.party) OVER (PARTITION BY cf.fec_candidate_id) known
            FROM candidate_finance cf
            WHERE cf.fec_candidate_id LIKE 'NY:%' AND cf.candidate_name IS NOT NULL
        ),
        named AS (
            SELECT f.*,
                -- tier 1: explicit party word, dropped when a name claims both
                CASE
                  WHEN regexp_matches(nm, '{DEM_RE}') AND regexp_matches(nm, '{REP_RE}') THEN NULL
                  WHEN regexp_matches(nm, '{DEM_RE}') THEN 'Democratic'
                  WHEN regexp_matches(nm, '{REP_RE}') THEN 'Republican'
                  WHEN regexp_matches(nm, '{CON_RE}') THEN 'Conservative'
                  WHEN regexp_matches(nm, '{WFP_RE}') THEN 'Working Families'
                END t1,
                -- tier 2: party already known on the finance row
                CASE WHEN f.known IN ('Democratic','Republican') THEN f.known END t2
            FROM f
        )
        SELECT n.fec_candidate_id, n.nm AS committee_name,
               COALESCE(
                   n.t1,
                   n.t2,
                   (SELECT party FROM _map_party m WHERE m.filer_id = n.filer_id),
                   -- tier 4: committee name contains exactly one roster candidate's full name
                   (SELECT ANY_VALUE(cp.party) FROM _cand_party cp
                    WHERE position(cp.nm IN n.nm) > 0
                    HAVING COUNT(DISTINCT cp.party) = 1)
               ) party,
               CASE
                   WHEN n.t1 IS NOT NULL THEN 'name_party_word'
                   WHEN n.t2 IS NOT NULL THEN 'candidate_finance_party'
                   WHEN (SELECT party FROM _map_party m WHERE m.filer_id = n.filer_id)
                        IS NOT NULL THEN 'committee_candidate_map'
                   ELSE 'roster_name_containment'
               END tier
        FROM named n
    """)


def report_coverage(con) -> None:
    tot, res = con.execute(
        "SELECT COUNT(*), COUNT(party) FROM _recip_party").fetchone()
    print(f"  recipients resolved: {res:,}/{tot:,} = {100*res/tot:.1f}%")
    print("  by tier:")
    for tier, n in con.execute("""
        SELECT tier, COUNT(*) FROM _recip_party WHERE party IS NOT NULL
        GROUP BY 1 ORDER BY 2 DESC""").fetchall():
        print(f"    {tier:26} {n:>7,}")
    print("  by party:")
    for party, n in con.execute("""
        SELECT party, COUNT(*) FROM _recip_party WHERE party IS NOT NULL
        GROUP BY 1 ORDER BY 2 DESC""").fetchall():
        print(f"    {party:26} {n:>7,}")

    tot_m, res_m = con.execute("""
        SELECT ROUND(SUM(ic.contribution_amount)/1e6, 1),
               ROUND(SUM(ic.contribution_amount) FILTER (WHERE rp.party IS NOT NULL)/1e6, 1)
        FROM individual_contributions ic
        LEFT JOIN _recip_party rp USING (fec_candidate_id)
        WHERE ic.contribution_id LIKE 'NY:%'""").fetchone()
    print(f"  state dollars party-resolved: ${res_m}M / ${tot_m}M "
          f"= {100*float(res_m)/float(tot_m):.1f}%")

    print("  largest still-unresolved recipients (expected: corporate/labor PACs):")
    for nm, m in con.execute("""
        SELECT ANY_VALUE(rp.committee_name), ROUND(SUM(ic.contribution_amount)/1e6, 1)
        FROM individual_contributions ic JOIN _recip_party rp USING (fec_candidate_id)
        WHERE ic.contribution_id LIKE 'NY:%' AND rp.party IS NULL
        GROUP BY ic.fec_candidate_id ORDER BY SUM(ic.contribution_amount) DESC LIMIT 6""").fetchall():
        print(f"    ${m:>7.1f}M  {str(nm)[:56]}")


def write_overrides(con) -> int:
    # committee_party_override CHECKs party IN ('Democratic','Republican'); Conservative
    # and Working Families filers are reported above but not written (see module docstring).
    skipped = con.execute("""
        SELECT COUNT(*) FROM _recip_party
        WHERE party IS NOT NULL AND party NOT IN ('Democratic', 'Republican')""").fetchone()[0]
    con.execute(f"DELETE FROM committee_party_override WHERE source = '{SOURCE}'")
    con.execute(f"""
        INSERT INTO committee_party_override (fec_candidate_id, party, committee_name, source, notes)
        SELECT fec_candidate_id, party, committee_name, '{SOURCE}',
               'NYSBOE recipient party via ' || tier
        FROM _recip_party
        WHERE party IN ('Democratic', 'Republican')
    """)
    if skipped:
        print(f"  (skipped {skipped} Conservative / Working Families filers — "
              "not writable under the D/R CHECK constraint)")
    return con.execute(
        f"SELECT COUNT(*) FROM committee_party_override WHERE source='{SOURCE}'").fetchone()[0]


def main() -> int:
    con = duckdb.connect(NY_STATEWIDE)
    try:
        print("[backfill] resolving NYSBOE recipient party...")
        build_map(con)
        report_coverage(con)
        n = write_overrides(con)
        print(f"\n[backfill] wrote {n:,} committee_party_override rows (source={SOURCE})")
        print("Next: STATE=NY python scripts/match_ny_voters_to_donors.py --source state")
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
