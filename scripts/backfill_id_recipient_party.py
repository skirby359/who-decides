"""Backfill recipient-party for Idaho Sunshine contributions (from on-disk data).

Idaho Sunshine's transaction downloads (TCON/TEXP) carry the recipient filing
entity (`candidate_finance.candidate_name`, id `SUNSHINE:<n>`) but NO party
field — so the voter<->donor matcher's recipient-party join found nothing and the
crossover ("where did each voter-donor's money go") was unresolved.

There is NO party-bearing download to fetch: Idaho Sunshine simply does not carry
party on the contribution feed. Instead we resolve recipient party from data
already on disk, writing results to `committee_party_override` (which the matcher
reads via COALESCE(ov.party, cf.party)) so the original blank `candidate_finance`
is left intact and the step is fully reversible:

  1. **Party / caucus / central-committee filers** — resolved by name pattern
     (IDAHO REPUBLICAN PARTY, IDAHO STATE DEMOCRATIC PARTY, ...REPUBLICAN CENTRAL
     COMMITTEE, IDAHO HOUSE REPUBLICAN CAUCUS, ...LIBERTY CAUCUS, etc.).
  2. **Candidate committees** — matched by (last name + first initial), then by a
     uniqueness-guarded last-name-only fallback, to the SoS `candidates` roster
     whose `party_normalized` is populated (527 R / 326 D across 2016-2024).

COVERAGE (honest): this resolves ~2/3 of *candidate-directed* dollars and ~36%
of *all* matched dollars. The unresolved remainder is overwhelmingly PACs and
ballot-measure committees (Idahoans for Open Primaries, Reclaim Idaho, trade
PACs), which are genuinely non-candidate / mixed and are correctly left
unclassified (donor_party='OTHER'). Crossover results must be read as "among
donors whose money reached a party-resolvable recipient."

Usage:
    STATE=ID python scripts/backfill_id_recipient_party.py
    # then re-run: STATE=ID python scripts/match_id_voters_to_donors.py
"""
import os
import sys

import duckdb

os.environ.setdefault("STATE", "ID")
ID_STATEWIDE = "data/id_statewide.duckdb"

# Party/caucus/central-committee name patterns (applied to UPPER candidate_name).
REP_RE = r"(REPUBLICAN|LIBERTY CAUCUS|G\.?O\.?P\.?)"
DEM_RE = r"DEMOCRAT"


def build_map(con) -> None:
    # SoS candidate -> party maps (uniqueness-guarded).
    con.execute("""
        CREATE OR REPLACE TEMP TABLE _cp_li AS   -- last + first-initial
        SELECT ln, fi, ANY_VALUE(party) party FROM (
            SELECT UPPER(regexp_extract(UPPER(TRIM(candidate_name)),'([A-Z''-]+)$',1)) ln,
                   UPPER(SUBSTR(TRIM(candidate_name),1,1)) fi, party_normalized party
            FROM candidates
            WHERE party_normalized IN ('Republican','Democratic')
              AND candidate_name IS NOT NULL
              AND candidate_name NOT IN ('UNDERVOTES','OVERVOTES','WRITE-IN')
        ) GROUP BY ln, fi HAVING count(DISTINCT party)=1
    """)
    con.execute("""
        CREATE OR REPLACE TEMP TABLE _cp_ln AS   -- last-name only, unique to one party
        SELECT ln, ANY_VALUE(party) party FROM (
            SELECT UPPER(regexp_extract(UPPER(TRIM(candidate_name)),'([A-Z''-]+)$',1)) ln,
                   party_normalized party
            FROM candidates
            WHERE party_normalized IN ('Republican','Democratic')
              AND candidate_name IS NOT NULL
              AND candidate_name NOT IN ('UNDERVOTES','OVERVOTES','WRITE-IN')
        ) GROUP BY ln HAVING count(DISTINCT party)=1
    """)

    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE _recip_party AS
        WITH r AS (
            SELECT DISTINCT fec_candidate_id, candidate_name,
                CASE WHEN candidate_name LIKE '%,%' THEN 'candidate' ELSE 'committee' END kind,
                UPPER(TRIM(SPLIT_PART(candidate_name,',',1))) rln,
                UPPER(SUBSTR(TRIM(SPLIT_PART(candidate_name,',',2)),1,1)) rfi
            FROM candidate_finance
        )
        SELECT r.fec_candidate_id, r.candidate_name, r.kind,
            COALESCE(
                CASE WHEN regexp_matches(r.candidate_name,'{REP_RE}') THEN 'Republican'
                     WHEN regexp_matches(r.candidate_name,'{DEM_RE}') THEN 'Democratic' END,
                (SELECT party FROM _cp_li c WHERE c.ln=r.rln AND c.fi=r.rfi),
                CASE WHEN r.kind='candidate' THEN (SELECT party FROM _cp_ln c WHERE c.ln=r.rln) END
            ) party
        FROM r
    """)


def report_coverage(con) -> None:
    r = con.execute("SELECT count(*), count(party) FROM _recip_party").fetchone()
    print(f"  recipients resolved: {r[1]:,}/{r[0]:,} = {100*r[1]/r[0]:.1f}%")
    q = con.execute("""
        SELECT round(sum(ic.contribution_amount)/1e6,2),
               round(sum(ic.contribution_amount) FILTER(WHERE rp.party IS NOT NULL)/1e6,2),
               round(100.0*sum(ic.contribution_amount) FILTER(WHERE rp.party IS NOT NULL)/sum(ic.contribution_amount),1)
        FROM individual_contributions ic LEFT JOIN _recip_party rp USING(fec_candidate_id)
    """).fetchone()
    print(f"  all contribution $ resolved:       ${q[1]}M / ${q[0]}M = {q[2]}%")
    q2 = con.execute("""
        SELECT round(100.0*sum(ic.contribution_amount) FILTER(WHERE rp.party IS NOT NULL)/sum(ic.contribution_amount),1)
        FROM individual_contributions ic JOIN _recip_party rp USING(fec_candidate_id) WHERE rp.kind='candidate'
    """).fetchone()
    print(f"  candidate-directed $ resolved:     {q2[0]}%")
    print("  resolved $ by kind/party:")
    for row in con.execute("""
        SELECT rp.kind, COALESCE(rp.party,'UNRESOLVED') p, round(sum(ic.contribution_amount)/1e6,2) m
        FROM individual_contributions ic JOIN _recip_party rp USING(fec_candidate_id)
        GROUP BY 1,2 ORDER BY 3 DESC
    """).fetchall():
        print(f"    {row[0]:10} {row[1]:12} ${row[2]}M")


def write_overrides(con) -> int:
    con.execute("DELETE FROM committee_party_override WHERE source = 'id_recipient_backfill'")
    con.execute("""
        INSERT INTO committee_party_override (fec_candidate_id, party, committee_name, source, notes)
        SELECT fec_candidate_id, party, candidate_name, 'id_recipient_backfill',
               'resolved from SoS candidates roster + party/committee name patterns'
        FROM _recip_party WHERE party IS NOT NULL
    """)
    return con.execute(
        "SELECT count(*) FROM committee_party_override WHERE source='id_recipient_backfill'"
    ).fetchone()[0]


def main() -> int:
    con = duckdb.connect(ID_STATEWIDE)
    print("[backfill] building recipient->party map from on-disk data ...")
    build_map(con)
    print("\n=== COVERAGE ===")
    report_coverage(con)
    n = write_overrides(con)
    print(f"\n[backfill] wrote {n:,} committee_party_override rows (source=id_recipient_backfill)")
    print("  next: STATE=ID python scripts/match_id_voters_to_donors.py")
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
