"""Independent re-derivation of the headline numbers in docs/donor-class-and-the-electorate.md.

Hits the state DBs directly with from-scratch SQL (not by importing the match/diag
scripts). Read-only; aggregate output only (voter files carry PII).

Reproduces the script-independent core of Findings 1-4 across WA / NY / ID:
  F1  donor age skew         (WA generation multipliers; NY & ID age bands)
  F2  whale concentration    (top-1% / top-10% / Gini of matched $) + geography
  F3  partisan skew          (own-party donor share vs registration; NY & ID)
  F4  give<->vote stacking    (WA super-voter rate; NY generals-voted)

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


def concentration(con):
    top1, top10 = con.execute("""
        WITH r AS (SELECT total_donated t, NTILE(100) OVER (ORDER BY total_donated DESC) p
                   FROM voter_donor_affiliation WHERE total_donated > 0)
        SELECT SUM(t) FILTER (WHERE p=1)/SUM(t), SUM(t) FILTER (WHERE p<=10)/SUM(t) FROM r
    """).fetchone()
    gini = con.execute("""
        WITH r AS (SELECT total_donated t, ROW_NUMBER() OVER (ORDER BY total_donated) rn,
                          COUNT(*) OVER () n, SUM(total_donated) OVER () s
                   FROM voter_donor_affiliation WHERE total_donated > 0)
        SELECT (2.0*SUM(rn*t)/(MAX(n)*MAX(s))) - (MAX(n)+1.0)/MAX(n) FROM r
    """).fetchone()[0]
    return top1 * 100, top10 * 100, gini


def party_skew(con, bucket_sql, order):
    """Registration share vs matched-donor own-party share, using bucket_sql on vrdb.voters.party."""
    reg = dict(con.execute(f"""
        SELECT {bucket_sql} b, COUNT(*) FROM vrdb.voters GROUP BY 1
    """).fetchall())
    don = dict(con.execute(f"""
        SELECT {bucket_sql} b, COUNT(*) FROM voter_donor_affiliation a JOIN vrdb.voters USING(state_voter_id) GROUP BY 1
    """).fetchall())
    dol = dict(con.execute(f"""
        SELECT {bucket_sql} b, SUM(a.total_donated) FROM voter_donor_affiliation a JOIN vrdb.voters USING(state_voter_id) GROUP BY 1
    """).fetchall())
    rt, dt, lt = sum(reg.values()), sum(don.values()), sum(v for v in dol.values() if v)
    print(f"    {'bucket':9}{'reg%':>8}{'donor%':>8}{'skew':>8}{'$ share':>9}")
    for b in order:
        rp = reg.get(b, 0) / rt * 100
        dp = don.get(b, 0) / dt * 100
        sp = (dol.get(b, 0) or 0) / lt * 100
        print(f"    {b:9}{rp:7.1f}%{dp:7.1f}%{dp-rp:+7.1f}{sp:8.1f}%")


def age_bands(con, age_expr, ref_voters_sql):
    """donor% vs reference-population% by 18-29/30-44/45-64/65+."""
    band = (f"CASE WHEN {age_expr}<30 THEN '18-29' WHEN {age_expr}<45 THEN '30-44' "
            f"WHEN {age_expr}<65 THEN '45-64' ELSE '65+' END")
    don = dict(con.execute(f"""
        SELECT {band} b, COUNT(*) FROM voter_donor_affiliation a JOIN vrdb.voters v USING(state_voter_id)
        WHERE {age_expr} IS NOT NULL GROUP BY 1""").fetchall())
    ref = dict(con.execute(f"""
        SELECT {band} b, COUNT(*) FROM vrdb.voters v WHERE {age_expr} IS NOT NULL AND ({ref_voters_sql}) GROUP BY 1""").fetchall())
    dt, rt = sum(don.values()), sum(ref.values())
    print(f"    {'band':7}{'donor%':>9}{'refpop%':>9}")
    for b in ["18-29", "30-44", "45-64", "65+"]:
        print(f"    {b:7}{don.get(b,0)/dt*100:8.1f}%{ref.get(b,0)/rt*100:8.1f}%")


# ============================== WASHINGTON ==============================
print("=" * 70 + "\nWASHINGTON  (wa_statewide + wa_vrdb)\n" + "=" * 70)
wa = duckdb.connect(str(DATA / "wa_statewide.duckdb"), read_only=True)
wa.execute(f"ATTACH '{DATA / 'wa_vrdb.duckdb'}' AS vrdb (READ_ONLY)")
n = wa.execute("SELECT COUNT(*) FROM voter_donor_affiliation").fetchone()[0]
print(f"matched donors: {n:,}   (paper: 382,408)")

print("\nF1 generation multiplier = donor share / roll share  (paper: Silent 1.87 Boomer 1.64 GenX 1.18 Mill 0.59 GenZ 0.17)")
roll = dict(wa.execute("SELECT age_cohort,COUNT(*) FROM voter_scores WHERE LEFT(district_id,2)='ld' AND age_cohort IS NOT NULL GROUP BY 1").fetchall())
don = dict(wa.execute("""SELECT s.age_cohort,COUNT(*) FROM voter_scores s JOIN voter_donor_affiliation a USING(state_voter_id)
                         WHERE LEFT(s.district_id,2)='ld' AND s.age_cohort IS NOT NULL GROUP BY 1""").fetchall())
rt, dt = sum(roll.values()), sum(don.values())
for g in ["Silent", "Boomer", "Gen X", "Millennial", "Gen Z"]:
    rp, dp = roll.get(g, 0) / rt * 100, don.get(g, 0) / dt * 100
    print(f"    {g:11}{dp/rp:5.2f}x   (roll {rp:4.1f}%  donor {dp:4.1f}%)")

t1, t10, g = concentration(wa)
print(f"\nF2 concentration: top-1% {t1:.1f}%  top-10% {t10:.1f}%  Gini {g:.3f}   (paper: 47.7 / 80.0)")
zip3 = wa.execute("""WITH z AS (SELECT SUBSTR(v.reg_zip,1,3) z3, SUM(a.total_donated) tot
    FROM voter_donor_affiliation a JOIN vrdb.voters v USING(state_voter_id)
    WHERE a.total_donated>0 AND v.reg_zip IS NOT NULL GROUP BY 1)
    SELECT z3, tot/SUM(tot) OVER () sh FROM z ORDER BY tot DESC LIMIT 3""").fetchall()
print("    geography (paper: 981xx 35.9% + 980xx 25.2% = 61.2%): " + "  ".join(f"{z}xx {s*100:.1f}%" for z, s in zip3))

print("\nF4 give<->vote stacking (paper: donor 84.0% super vs non-donor 50.1%; prop 0.953 vs 0.748)")
for donor, n2, sr, ap in wa.execute("""
    WITH roll AS (SELECT DISTINCT state_voter_id,is_super_voter,turnout_propensity FROM voter_scores WHERE LEFT(district_id,2)='ld'),
    f AS (SELECT r.*, CASE WHEN a.state_voter_id IS NOT NULL THEN 1 ELSE 0 END d FROM roll r LEFT JOIN voter_donor_affiliation a USING(state_voter_id))
    SELECT d,COUNT(*),AVG(CASE WHEN is_super_voter THEN 1.0 ELSE 0 END),AVG(turnout_propensity) FROM f GROUP BY d ORDER BY d""").fetchall():
    print(f"    {'matched donor' if donor else 'non-donor':14} n={n2:>10,}  super {sr*100:5.1f}%  avg prop {ap:.3f}")
wa.close()

# ============================== NEW YORK ==============================
print("\n" + "=" * 70 + "\nNEW YORK  (ny_statewide + ny_vrdb)\n" + "=" * 70)
ny = duckdb.connect(str(DATA / "ny_statewide.duckdb"), read_only=True)
ny.execute(f"ATTACH '{DATA / 'ny_vrdb.duckdb'}' AS vrdb (READ_ONLY)")
print(f"matched donors: {ny.execute('SELECT COUNT(*) FROM voter_donor_affiliation').fetchone()[0]:,}   (paper: 308,032)")
print("\nF1 age bands (paper donors: 3.0 / 14.2 / 34.9 / 47.9 ; 2024 GE voters ref)")
age_bands(ny, "date_diff('year', v.birthdate, DATE '2024-11-05')",
          "v.state_voter_id IN (SELECT state_voter_id FROM vrdb.voter_participation WHERE kind='GENERAL' AND election_year=2024)")
t1, t10, g = concentration(ny)
print(f"\nF2 concentration: top-1% {t1:.1f}%  top-10% {t10:.1f}%  Gini {g:.3f}   (paper: 51.2 / 81.4)")
print("\nF3 own-party skew (paper: DEM 62.8/47.8 +15.0 ; REP 21.4/22.3 -0.9 ; NOPARTY 12.5/25.5 -13.0 ; DEM $ 71.0%)")
party_skew(ny, "CASE WHEN party='DEM' THEN 'DEM' WHEN party='REP' THEN 'REP' WHEN party='BLK' THEN 'NOPARTY' ELSE 'OTHER' END",
           ["DEM", "REP", "NOPARTY", "OTHER"])
ny.close()

# ============================== IDAHO ==============================
print("\n" + "=" * 70 + "\nIDAHO  (id_statewide + id_vrdb)\n" + "=" * 70)
idc = duckdb.connect(str(DATA / "id_statewide.duckdb"), read_only=True)
idc.execute(f"ATTACH '{DATA / 'id_vrdb.duckdb'}' AS vrdb (READ_ONLY)")
print(f"matched donors: {idc.execute('SELECT COUNT(*) FROM voter_donor_affiliation').fetchone()[0]:,}   (paper: 27,250)")
print("\nF1 age bands, current-roll age (paper donors: 2.6 / 13.1 / 33.2 / 51.1 ; all voters ref)")
age_bands(idc, "v.age", "1=1")
t1, t10, g = concentration(idc)   # standardized NTILE estimator, same as WA/NY
print(f"\nF2 concentration: top-1% {t1:.1f}%  top-10% {t10:.1f}%  Gini {g:.3f}   (paper: 39.3 / 70.8, standardized NTILE)")
print("\nF3 own-party skew (paper: REP 66.5/62.9 +3.6 ; DEM 20.9/11.8 +9.1 ; UNAFF 12.0/23.9 -11.8)")
party_skew(idc, "CASE WHEN party='REP' THEN 'REP' WHEN party='DEM' THEN 'DEM' WHEN party='UNA' THEN 'UNAFF' ELSE 'OTHER' END",
           ["REP", "DEM", "UNAFF", "OTHER"])
idc.close()
