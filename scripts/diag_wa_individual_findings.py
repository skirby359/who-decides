"""WA individual-level civic-health findings on the improved 382K voter<->donor match.

Three analyses, all WA-only (WA needs no external voter file — it has the VRDB
voter roll + vote history + the matched-donor table). Refreshes the numbers the
democracy-insight gauntlet produced on the OLD 320K match (now 382K).

  (a) Turnout inequality by age   — vrdb.voting_history x vrdb.voters.birthdate:
      within-cohort turnout rate AND cohort share of the actual electorate, by
      cycle type (presidential / midterm / off-year November generals).
  (b) Donor-vs-electorate representativeness — voter_donor_affiliation x
      voter_scores.age_cohort, WITH the matcher-bias inverse-propensity
      re-weighting the white paper flagged (match rate by generation -> IPW),
      reported RAW and RE-WEIGHTED; plus dollar concentration + geography.
  (c) Cross-sectional giving->turnout — matched donors' super-voter rate vs
      non-donors (association only; reverse causation + match bias noted).

Data: data/wa_statewide.duckdb (voter_scores, voter_donor_affiliation) +
      data/wa_vrdb.duckdb ATTACHed (voters, voting_history). All reads read-only.

Matchability proxy (for the bias correction): a voter is "matchable" iff their
(last_upper, first_initial, zip5) key is UNIQUE on the VRDB roll — the matcher's
own uniqueness guard (donor_analysis.match_voters_to_donors, Tier 2
STRICT_ZIP5). Generations whose voters are easier to uniquely identify get
over-counted in the matched pool; IPW divides by P(matchable | generation).
"""
import duckdb
import json
import os

DB = "data/wa_statewide.duckdb"
VRDB = "data/wa_vrdb.duckdb"
# Side artifact — all findings print to stdout; this JSON is optional. reports/ is
# gitignored. (Was a stale per-session scratchpad path; repointed 2026-07-10.)
OUT = "reports/wa_individual_findings.json"

# November generals by cycle type (the ones VRDB voting_history carries).
ELECTIONS = [
    ("2024-11-05", "presidential"),
    ("2020-11-03", "presidential"),
    ("2022-11-08", "midterm"),
    ("2018-11-06", "midterm"),
    ("2025-11-04", "off-year"),
    ("2023-11-07", "off-year"),
    ("2021-11-02", "off-year"),
]
GEN_ORDER = ["Silent", "Boomer", "Gen X", "Millennial", "Gen Z"]


def conn():
    c = duckdb.connect(DB, read_only=True)
    c.execute(f"ATTACH '{VRDB}' AS vrdb (READ_ONLY)")
    return c


def age_cohort_sql(age_expr):
    return (f"CASE WHEN {age_expr} < 30 THEN '18-29' "
            f"WHEN {age_expr} < 45 THEN '30-44' "
            f"WHEN {age_expr} < 65 THEN '45-64' ELSE '65+' END")


# ---------------------------------------------------------------------------
# (a) Turnout inequality by age
# ---------------------------------------------------------------------------
def turnout_by_age(c):
    print("\n" + "=" * 78)
    print("(a) TURNOUT INEQUALITY BY AGE  — WA November generals, VRDB vote history")
    print("=" * 78)
    rate_buckets = ["18-29", "30-44", "45-64", "65+"]
    out = {}
    # available dates actually present
    present = {r[0].isoformat() for r in c.execute(
        "SELECT DISTINCT election_date FROM vrdb.voting_history").fetchall()}
    print("\nWithin-cohort TURNOUT RATE (voted / age-eligible registered, current-roll "
          "denominator — survivorship-biased; read shares below as the robust cut):\n")
    print(f"{'election':12} {'type':13} " + " ".join(f"{b:>8}" for b in rate_buckets) + f" {'all':>8}")
    for date, kind in ELECTIONS:
        if date not in present:
            continue
        age = f"date_diff('year', v.birthdate, DATE '{date}')"
        coh = age_cohort_sql(age)
        # denominator: in current roll, age>=18 at E and registered on/before E
        rows = c.execute(f"""
            WITH elig AS (
                SELECT v.state_voter_id,
                       {coh} AS coh,
                       CASE WHEN h.state_voter_id IS NOT NULL THEN 1 ELSE 0 END AS voted
                FROM vrdb.voters v
                LEFT JOIN (SELECT DISTINCT state_voter_id FROM vrdb.voting_history
                           WHERE election_date = DATE '{date}') h
                  ON h.state_voter_id = v.state_voter_id
                WHERE v.birthdate IS NOT NULL
                  AND date_diff('year', v.birthdate, DATE '{date}') >= 18
                  AND v.registration_date IS NOT NULL
                  AND v.registration_date <= DATE '{date}'
            )
            SELECT coh, COUNT(*) reg, SUM(voted) voted FROM elig GROUP BY 1
        """).fetchall()
        d = {coh: (reg, voted) for coh, reg, voted in rows}
        tot_reg = sum(reg for reg, _ in d.values())
        tot_voted = sum(v for _, v in d.values())
        line = f"{date:12} {kind:13} "
        rec = {"type": kind, "rate": {}, "share": {}}
        for b in rate_buckets:
            reg, voted = d.get(b, (0, 0))
            r = voted / reg * 100 if reg else 0
            rec["rate"][b] = round(r, 1)
            line += f"{r:7.1f}% "
        line += f"{tot_voted/tot_reg*100:7.1f}%" if tot_reg else ""
        print(line)
        # composition shares: of actual voters, % in each cohort
        for b in rate_buckets:
            _, voted = d.get(b, (0, 0))
            rec["share"][b] = round(voted / tot_voted * 100, 1) if tot_voted else 0
        out[date] = rec

    print("\nCohort SHARE of the ACTUAL electorate (denominator-free — the robust cut):\n")
    print(f"{'election':12} {'type':13} " + " ".join(f"{b:>8}" for b in rate_buckets))
    for date, kind in ELECTIONS:
        if date in out:
            rec = out[date]
            line = f"{date:12} {kind:13} " + " ".join(f"{rec['share'][b]:7.1f}%" for b in rate_buckets)
            print(line)

    # summary contrasts (avg by cycle type)
    def avg(kind, field, bucket):
        vals = [rec[field][bucket] for rec in out.values() if rec["type"] == kind]
        return sum(vals) / len(vals) if vals else 0
    print("\nContrast (avg across cycles of each type):")
    for b in ["18-29", "65+"]:
        print(f"  {b:>6} turnout rate:  presidential {avg('presidential','rate',b):5.1f}%  "
              f"midterm {avg('midterm','rate',b):5.1f}%  off-year {avg('off-year','rate',b):5.1f}%")
    for b in ["18-29", "65+"]:
        print(f"  {b:>6} share of electorate: presidential {avg('presidential','share',b):5.1f}%  "
              f"midterm {avg('midterm','share',b):5.1f}%  off-year {avg('off-year','share',b):5.1f}%")
    return out


# ---------------------------------------------------------------------------
# (b) Donor vs electorate representativeness + matcher-bias IPW
# ---------------------------------------------------------------------------
def donor_representativeness(c):
    print("\n" + "=" * 78)
    print("(b) DONOR-vs-ELECTORATE REPRESENTATIVENESS  (raw AND matcher-bias re-weighted)")
    print("=" * 78)

    # Electorate baseline = full roll, one row per voter (ld-scope covers all 5.05M).
    c.execute("""
        CREATE TEMP TABLE roll AS
        SELECT DISTINCT state_voter_id, age_cohort, is_super_voter, turnout_propensity
        FROM voter_scores WHERE LEFT(district_id,2)='ld' AND age_cohort IS NOT NULL
    """)
    # Matched donors that are present in voter_scores (have a generation label).
    c.execute("""
        CREATE TEMP TABLE mdon AS
        SELECT r.state_voter_id, r.age_cohort, r.is_super_voter, a.total_donated
        FROM roll r JOIN voter_donor_affiliation a USING (state_voter_id)
    """)
    n_roll = c.execute("SELECT COUNT(*) FROM roll").fetchone()[0]
    n_match_total = c.execute("SELECT COUNT(*) FROM voter_donor_affiliation").fetchone()[0]
    n_mdon = c.execute("SELECT COUNT(*) FROM mdon").fetchone()[0]
    print(f"\nfull roll (scored, generation-labeled): {n_roll:,}")
    print(f"matched donors total: {n_match_total:,}  |  matched & in scored roll: {n_mdon:,} "
          f"({n_mdon/n_match_total*100:.1f}%)")

    # Matchability on the VRDB roll: unique (last_upper, first_initial, zip5).
    c.execute("""
        CREATE TEMP TABLE matchable AS
        WITH k AS (
            SELECT state_voter_id,
                   UPPER(TRIM(last_name)) || '|' ||
                   UPPER(SUBSTR(TRIM(first_name),1,1)) || '|' ||
                   SUBSTR(reg_zip,1,5) AS key
            FROM vrdb.voters
            WHERE last_name IS NOT NULL AND first_name IS NOT NULL AND reg_zip IS NOT NULL
        ), g AS (SELECT key, COUNT(*) n FROM k GROUP BY 1)
        SELECT k.state_voter_id, CASE WHEN g.n=1 THEN 1 ELSE 0 END AS matchable
        FROM k JOIN g USING (key)
    """)
    # P(matchable | generation) over the full roll.
    pm = dict(c.execute("""
        SELECT r.age_cohort, AVG(m.matchable)
        FROM roll r JOIN matchable m USING (state_voter_id)
        GROUP BY 1
    """).fetchall())
    overall_pm = c.execute("""
        SELECT AVG(m.matchable) FROM roll r JOIN matchable m USING (state_voter_id)
    """).fetchone()[0]

    # Generation distributions
    roll_gen = dict(c.execute("SELECT age_cohort, COUNT(*) FROM roll GROUP BY 1").fetchall())
    don_gen = dict(c.execute("SELECT age_cohort, COUNT(*) FROM mdon GROUP BY 1").fetchall())
    roll_tot = sum(roll_gen.values())
    don_tot = sum(don_gen.values())

    # IPW-corrected donor counts: matched_count / P(matchable|gen)
    ipw = {g: don_gen.get(g, 0) / pm[g] for g in roll_gen if pm.get(g)}
    ipw_tot = sum(ipw.values())

    print(f"\n{'generation':12} {'roll%':>7} {'donor%':>7} {'over-rep':>9} | "
          f"{'P(match)':>9} {'rwt donor%':>11} {'rwt over-rep':>13}")
    print("-" * 78)
    rec = {}
    for g in GEN_ORDER:
        rp = roll_gen.get(g, 0) / roll_tot * 100
        dp = don_gen.get(g, 0) / don_tot * 100
        over = dp / rp if rp else 0
        rwt_dp = ipw.get(g, 0) / ipw_tot * 100 if ipw_tot else 0
        rwt_over = rwt_dp / rp if rp else 0
        print(f"{g:12} {rp:6.1f}% {dp:6.1f}% {over:8.2f}x | "
              f"{pm.get(g,0)*100:8.1f}% {rwt_dp:10.1f}% {rwt_over:12.2f}x")
        rec[g] = {"roll_pct": round(rp, 1), "donor_pct": round(dp, 1),
                  "over_rep": round(over, 2), "p_match": round(pm.get(g, 0), 4),
                  "rwt_donor_pct": round(rwt_dp, 1), "rwt_over_rep": round(rwt_over, 2)}
    print(f"\noverall P(matchable) on roll: {overall_pm*100:.1f}%")
    print("Interpretation: raw over-rep blends genuine giving-skew + matcher selection;")
    print("re-weighted strips the matcher's easier-to-match-when-older selection, leaving")
    print("the genuine donor-class age skew. (Older gens DO have higher P(match).)")

    # Dollar concentration among matched donors (refresh 48.8% / 80.7%)
    top1, top10 = c.execute("""
        WITH ranked AS (SELECT total_donated t, NTILE(100) OVER (ORDER BY total_donated DESC) p
                        FROM voter_donor_affiliation WHERE total_donated > 0)
        SELECT SUM(t) FILTER (WHERE p=1)/SUM(t), SUM(t) FILTER (WHERE p<=10)/SUM(t) FROM ranked
    """).fetchone()
    gini = c.execute("""
        WITH r AS (SELECT total_donated t, ROW_NUMBER() OVER (ORDER BY total_donated) rn,
                          COUNT(*) OVER () n, SUM(total_donated) OVER () s
                   FROM voter_donor_affiliation WHERE total_donated > 0)
        SELECT (2.0*SUM(rn*t)/(MAX(n)*MAX(s))) - (MAX(n)+1.0)/MAX(n) FROM r
    """).fetchone()[0]
    print(f"\nMatched-donor dollar concentration: top1%={top1*100:.1f}%  "
          f"top10%={top10*100:.1f}%  Gini={gini:.3f}")

    # Geography: top ZIP3 share of matched-donor dollars
    zip3 = c.execute("""
        WITH z AS (
            SELECT SUBSTR(vv.reg_zip,1,3) z3, SUM(a.total_donated) tot
            FROM voter_donor_affiliation a JOIN vrdb.voters vv USING (state_voter_id)
            WHERE a.total_donated > 0 AND vv.reg_zip IS NOT NULL
            GROUP BY 1)
        SELECT z3, tot, tot/SUM(tot) OVER () sh FROM z ORDER BY tot DESC LIMIT 5
    """).fetchall()
    top2 = sum(r[2] for r in zip3[:2])
    print(f"Top-2 ZIP3 share of matched-donor $: {top2*100:.1f}%  "
          + "; ".join(f"{z}xx {sh*100:.1f}%" for z, _, sh in zip3))

    return {"generations": rec, "overall_p_match": round(overall_pm, 4),
            "top1_share": round(top1, 4), "top10_share": round(top10, 4),
            "gini": round(gini, 4), "top2_zip3_share": round(top2, 4),
            "n_matched_total": n_match_total, "n_matched_scored": n_mdon, "n_roll": n_roll}


# ---------------------------------------------------------------------------
# (c) Cross-sectional giving -> turnout
# ---------------------------------------------------------------------------
def giving_vs_turnout(c):
    print("\n" + "=" * 78)
    print("(c) CROSS-SECTIONAL GIVING -> TURNOUT  (association only)")
    print("=" * 78)
    row = c.execute("""
        WITH roll AS (
            SELECT DISTINCT state_voter_id, is_super_voter, turnout_propensity
            FROM voter_scores WHERE LEFT(district_id,2)='ld'
        ),
        flagged AS (
            SELECT r.*, CASE WHEN a.state_voter_id IS NOT NULL THEN 1 ELSE 0 END AS donor
            FROM roll r LEFT JOIN voter_donor_affiliation a USING (state_voter_id)
        )
        SELECT donor, COUNT(*) n,
               AVG(CASE WHEN is_super_voter THEN 1.0 ELSE 0 END) super_rate,
               AVG(turnout_propensity) avg_prop
        FROM flagged GROUP BY donor ORDER BY donor
    """).fetchall()
    rec = {}
    print(f"\n{'group':14} {'n':>12} {'super-voter%':>13} {'avg turnout prop':>18}")
    for donor, n, sr, ap in row:
        label = "matched donor" if donor == 1 else "non-donor"
        print(f"{label:14} {n:>12,} {sr*100:12.1f}% {ap:17.3f}")
        rec[label] = {"n": int(n), "super_rate": round(sr, 4), "avg_prop": round(float(ap), 4)}
    d = rec["matched donor"]["super_rate"] * 100
    nd = rec["non-donor"]["super_rate"] * 100
    print(f"\nMatched donors are super-voters {d:.1f}% vs {nd:.1f}% of non-donors "
          f"({d/nd:.2f}x). Association only: donors are pre-selected for engagement,")
    print("and the matcher itself favors stable-address super-voters (reverse causation +")
    print("selection both inflate the gap). Not a causal 'giving makes you vote' claim.")
    return rec


def main():
    c = conn()
    out = {}
    out["turnout_by_age"] = turnout_by_age(c)
    out["donor_representativeness"] = donor_representativeness(c)
    out["giving_vs_turnout"] = giving_vs_turnout(c)
    c.close()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, default=str)
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
