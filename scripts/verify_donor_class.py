"""Independent re-derivation of the headline numbers in docs/donor-class-and-the-electorate.md.

Hits the state DBs directly with from-scratch SQL (not by importing the match/diag
scripts). Read-only; aggregate output only (voter files carry PII).

Reproduces the script-independent core of Findings 1-4 across WA / NY / ID:
  F1  donor age skew         (WA generation multipliers; NY & ID age bands)
  F2  whale concentration    (top-1% / top-10% / Gini of matched $) + geography
  F3  partisan skew          (own-party donor share vs registration; NY & ID)
  F4  give<->vote stacking    (WA super-voter rate; NY generals-voted)

TWO PANELS (2026-07-26). A state's individual_contributions can hold more than one
money system, so the matched layer is built one source at a time and each panel gets
its own table (see docs/donor-class-and-the-electorate.md):

  voter_donor_affiliation_fec     federal (FEC) money  — WA, NY, ID   [primary panel]
  voter_donor_affiliation_state   state money          — WA (PDC), ID (Sunshine)
  voter_donor_affiliation         legacy POOLED match  — what the campaign tooling
                                  reads; NOT a paper panel, since pooling stacks one
                                  person's federal and state giving into a single
                                  donor total and inflates measured concentration.

New York has no state layer (BOE money is summary-only in candidate_finance), so it
verifies on the federal panel alone.

Recipient-party CROSSOVER tables and the IPW re-weighting depend on the match
scripts' recipient-resolution logic and are reproduced by those scripts, not here;
the 150-row match-precision hand-rate (publication-checklist §3/§4) is the remaining
HUMAN gate before this paper publishes. Own-party, age, and concentration cuts below
use the full matched set and need no hand-rate.

Run:  python scripts/verify_donor_class.py
"""
from pathlib import Path
import duckdb

DATA = Path(__file__).resolve().parent.parent / "data"

FED = "voter_donor_affiliation_fec"
STATE = "voter_donor_affiliation_state"


def has_table(con, t):
    return con.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?", [t]
    ).fetchone()[0] > 0


def require(con, state, tables):
    missing = [t for t in tables if not has_table(con, t)]
    if missing:
        print(f"  !! {state}: missing panel table(s) {', '.join(missing)} — rebuild with "
              f"scripts/match_{state.lower()}_voters_to_donors.py --source {{fec,state}}")
    return not missing


def concentration(con, vda):
    top1, top10 = con.execute(f"""
        WITH r AS (SELECT total_donated t, NTILE(100) OVER (ORDER BY total_donated DESC) p
                   FROM {vda} WHERE total_donated > 0)
        SELECT SUM(t) FILTER (WHERE p=1)/SUM(t), SUM(t) FILTER (WHERE p<=10)/SUM(t) FROM r
    """).fetchone()
    gini = con.execute(f"""
        WITH r AS (SELECT total_donated t, ROW_NUMBER() OVER (ORDER BY total_donated) rn,
                          COUNT(*) OVER () n, SUM(total_donated) OVER () s
                   FROM {vda} WHERE total_donated > 0)
        SELECT (2.0*SUM(rn*t)/(MAX(n)*MAX(s))) - (MAX(n)+1.0)/MAX(n) FROM r
    """).fetchone()[0]
    n, tot = con.execute(
        f"SELECT COUNT(*), SUM(total_donated)/1e6 FROM {vda}").fetchone()
    return int(n), float(tot), top1 * 100, top10 * 100, gini


def conc_line(con, label, vda, paper=""):
    n, tot, t1, t10, g = concentration(con, vda)
    tail = f"   (paper: {paper})" if paper else ""
    print(f"    {label:<16} {n:>9,} donors  ${tot:>8.2f}M   "
          f"top-1% {t1:5.1f}%  top-10% {t10:5.1f}%  Gini {g:.3f}{tail}")


def party_skew(con, vda, bucket_sql, order):
    """Registration share vs matched-donor own-party share, using bucket_sql on vrdb.voters.party."""
    reg = dict(con.execute(f"""
        SELECT {bucket_sql} b, COUNT(*) FROM vrdb.voters GROUP BY 1
    """).fetchall())
    don = dict(con.execute(f"""
        SELECT {bucket_sql} b, COUNT(*) FROM {vda} a JOIN vrdb.voters USING(state_voter_id) GROUP BY 1
    """).fetchall())
    dol = dict(con.execute(f"""
        SELECT {bucket_sql} b, SUM(a.total_donated) FROM {vda} a JOIN vrdb.voters USING(state_voter_id) GROUP BY 1
    """).fetchall())
    rt, dt, lt = sum(reg.values()), sum(don.values()), sum(v for v in dol.values() if v)
    print(f"    {'bucket':9}{'reg%':>8}{'donor%':>8}{'skew':>8}{'$ share':>9}")
    for b in order:
        rp = reg.get(b, 0) / rt * 100
        dp = don.get(b, 0) / dt * 100
        sp = (dol.get(b, 0) or 0) / lt * 100
        print(f"    {b:9}{rp:7.1f}%{dp:7.1f}%{dp-rp:+7.1f}{sp:8.1f}%")


def age_bands(con, vda, age_expr, ref_voters_sql):
    """donor% vs reference-population% by 18-29/30-44/45-64/65+."""
    band = (f"CASE WHEN {age_expr}<30 THEN '18-29' WHEN {age_expr}<45 THEN '30-44' "
            f"WHEN {age_expr}<65 THEN '45-64' ELSE '65+' END")
    don = dict(con.execute(f"""
        SELECT {band} b, COUNT(*) FROM {vda} a JOIN vrdb.voters v USING(state_voter_id)
        WHERE {age_expr} IS NOT NULL GROUP BY 1""").fetchall())
    ref = dict(con.execute(f"""
        SELECT {band} b, COUNT(*) FROM vrdb.voters v WHERE {age_expr} IS NOT NULL AND ({ref_voters_sql}) GROUP BY 1""").fetchall())
    dt, rt = sum(don.values()), sum(ref.values())
    print(f"    {'band':7}{'donor%':>9}{'refpop%':>9}")
    for b in ["18-29", "30-44", "45-64", "65+"]:
        print(f"    {b:7}{don.get(b,0)/dt*100:8.1f}%{ref.get(b,0)/rt*100:8.1f}%")


# ============================== WASHINGTON ==============================
print("=" * 78 + "\nWASHINGTON  (wa_statewide + wa_vrdb)\n" + "=" * 78)
wa = duckdb.connect(str(DATA / "wa_statewide.duckdb"), read_only=True)
wa.execute(f"ATTACH '{DATA / 'wa_vrdb.duckdb'}' AS vrdb (READ_ONLY)")
require(wa, "WA", [FED, STATE])

print("\nF1 generation multiplier = donor share / roll share, FEDERAL panel")
roll = dict(wa.execute("SELECT age_cohort,COUNT(*) FROM voter_scores WHERE LEFT(district_id,2)='ld' AND age_cohort IS NOT NULL GROUP BY 1").fetchall())
don = dict(wa.execute(f"""SELECT s.age_cohort,COUNT(*) FROM voter_scores s JOIN {FED} a USING(state_voter_id)
                         WHERE LEFT(s.district_id,2)='ld' AND s.age_cohort IS NOT NULL GROUP BY 1""").fetchall())
rt, dt = sum(roll.values()), sum(don.values())
for g in ["Silent", "Boomer", "Gen X", "Millennial", "Gen Z"]:
    rp, dp = roll.get(g, 0) / rt * 100, don.get(g, 0) / dt * 100
    print(f"    {g:11}{dp/rp:5.2f}x   (roll {rp:4.1f}%  donor {dp:4.1f}%)")

print("\nF2 concentration by panel:")
conc_line(wa, "federal", FED)
conc_line(wa, "state (PDC)", STATE)
zip3 = wa.execute(f"""WITH z AS (SELECT SUBSTR(v.reg_zip,1,3) z3, SUM(a.total_donated) tot
    FROM {FED} a JOIN vrdb.voters v USING(state_voter_id)
    WHERE a.total_donated>0 AND v.reg_zip IS NOT NULL GROUP BY 1)
    SELECT z3, tot/SUM(tot) OVER () sh FROM z ORDER BY tot DESC LIMIT 3""").fetchall()
print("    federal geography: " + "  ".join(f"{z}xx {s*100:.1f}%" for z, s in zip3))

print("\nF4 give<->vote stacking, FEDERAL panel")
for donor, n2, sr, ap in wa.execute(f"""
    WITH roll AS (SELECT DISTINCT state_voter_id,is_super_voter,turnout_propensity FROM voter_scores WHERE LEFT(district_id,2)='ld'),
    f AS (SELECT r.*, CASE WHEN a.state_voter_id IS NOT NULL THEN 1 ELSE 0 END d FROM roll r LEFT JOIN {FED} a USING(state_voter_id))
    SELECT d,COUNT(*),AVG(CASE WHEN is_super_voter THEN 1.0 ELSE 0 END),AVG(turnout_propensity) FROM f GROUP BY d ORDER BY d""").fetchall():
    print(f"    {'matched donor' if donor else 'non-donor':14} n={n2:>10,}  super {sr*100:5.1f}%  avg prop {ap:.3f}")
wa.close()

# ============================== NEW YORK ==============================
print("\n" + "=" * 78 + "\nNEW YORK  (ny_statewide + ny_vrdb) — federal panel only\n" + "=" * 78)
ny = duckdb.connect(str(DATA / "ny_statewide.duckdb"), read_only=True)
ny.execute(f"ATTACH '{DATA / 'ny_vrdb.duckdb'}' AS vrdb (READ_ONLY)")
require(ny, "NY", [FED])
print("\nF1 age bands (2024 GE voters ref)")
age_bands(ny, FED, "date_diff('year', v.birthdate, DATE '2024-11-05')",
          "v.state_voter_id IN (SELECT state_voter_id FROM vrdb.voter_participation WHERE kind='GENERAL' AND election_year=2024)")
print("\nF2 concentration by panel:")
conc_line(ny, "federal", FED)
print("\nF3 own-party skew, FEDERAL panel")
party_skew(ny, FED, "CASE WHEN party='DEM' THEN 'DEM' WHEN party='REP' THEN 'REP' WHEN party='BLK' THEN 'NOPARTY' ELSE 'OTHER' END",
           ["DEM", "REP", "NOPARTY", "OTHER"])
ny.close()

# ============================== IDAHO ==============================
print("\n" + "=" * 78 + "\nIDAHO  (id_statewide + id_vrdb)\n" + "=" * 78)
idc = duckdb.connect(str(DATA / "id_statewide.duckdb"), read_only=True)
idc.execute(f"ATTACH '{DATA / 'id_vrdb.duckdb'}' AS vrdb (READ_ONLY)")
require(idc, "ID", [FED, STATE])

print("\nF1 age bands, current-roll age, FEDERAL panel (all voters ref)")
age_bands(idc, FED, "v.age", "1=1")
print("\nF1 age bands, current-roll age, STATE panel (all voters ref)")
age_bands(idc, STATE, "v.age", "1=1")

print("\nF2 concentration by panel:")
conc_line(idc, "federal", FED)
conc_line(idc, "state (Sunshine)", STATE)

print("\nF3 own-party skew, FEDERAL panel")
party_skew(idc, FED, "CASE WHEN party='REP' THEN 'REP' WHEN party='DEM' THEN 'DEM' WHEN party='UNA' THEN 'UNAFF' ELSE 'OTHER' END",
           ["REP", "DEM", "UNAFF", "OTHER"])
print("\nF3 own-party skew, STATE panel")
party_skew(idc, STATE, "CASE WHEN party='REP' THEN 'REP' WHEN party='DEM' THEN 'DEM' WHEN party='UNA' THEN 'UNAFF' ELSE 'OTHER' END",
           ["REP", "DEM", "UNAFF", "OTHER"])
idc.close()
