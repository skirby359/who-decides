"""Inflow concentration TREND + donor RETENTION (the small-dollar-democratization
question), on the recipient-anchored inflow (data/fec_inflow.duckdb: all-state
donors -> WA/NY/TX U.S. House+Senate candidates).

Section A measured concentration on the OUTFLOW (each state's resident donors).
This measures it on the INFLOW (everyone funding these states' candidates):

  (A) Per-cycle top-1% / top-10% donor dollar share + Gini, 2018-2026.
  (B) Donor retention: of donors (name+zip5 proxy) active in a cycle, what share
      are RETURNING (gave in a prior cycle) vs NEW; and what share of DOLLARS
      comes from one-time vs repeat (>=2 cycle) donors. Rising new/one-time share
      = broadening base; rising repeat-core dollar share = a persistent core.

Donor identity = UPPER(name)+zip5 (over-merges common names -> understates the
one-time count / overstates repeat, so retention here is an UPPER bound).
2026 is a partial cycle.
"""
import duckdb
import json

OUT = "reports/inflow_concentration_retention.json"
CYCLES = [2018, 2020, 2022, 2024, 2026]


def main():
    c = duckdb.connect("data/fec_inflow.duckdb", read_only=True)
    # Per-donor-per-cycle dollar totals (name+zip5 proxy), H+S, positive amounts.
    c.execute("""
        CREATE TEMP TABLE dc AS
        SELECT election_cycle ec,
               UPPER(TRIM(contributor_name)) || '|' || LEFT(COALESCE(contributor_zip,''),5) donor,
               SUM(contribution_amount) tot, COUNT(*) n
        FROM inflow_contributions
        WHERE recipient_office IN ('H','S') AND contribution_amount > 0
              AND contributor_name IS NOT NULL
        GROUP BY 1,2
    """)

    # ---- (A) concentration trend ----
    print("=" * 64)
    print("(A) INFLOW CONCENTRATION TREND — donor dollar share by cycle")
    print("=" * 64)
    print(f"\n{'cycle':7} {'$M':>8} {'donors':>10} {'top1%':>7} {'top10%':>7} {'Gini':>7}")
    trend = {}
    for cy in CYCLES:
        row = c.execute(f"""
            WITH d AS (SELECT donor, tot FROM dc WHERE ec={cy}),
            ranked AS (SELECT tot, NTILE(100) OVER (ORDER BY tot DESC) p FROM d),
            g AS (SELECT tot, ROW_NUMBER() OVER (ORDER BY tot) rn, COUNT(*) OVER () n,
                         SUM(tot) OVER () s FROM d)
            SELECT (SELECT SUM(tot) FROM d) total,
                   (SELECT COUNT(*) FROM d) ndon,
                   (SELECT SUM(tot) FILTER (WHERE p=1)/SUM(tot) FROM ranked) top1,
                   (SELECT SUM(tot) FILTER (WHERE p<=10)/SUM(tot) FROM ranked) top10,
                   (SELECT (2.0*SUM(rn*tot)/(MAX(n)*MAX(s))) - (MAX(n)+1.0)/MAX(n) FROM g) gini
        """).fetchone()
        total, ndon, top1, top10, gini = row
        marker = "*" if cy == 2026 else " "
        print(f"{cy}{marker}  {float(total)/1e6:7.1f} {ndon:>10,} {float(top1)*100:6.1f}% "
              f"{float(top10)*100:6.1f}% {float(gini):6.3f}")
        trend[cy] = {"total": float(total), "ndonors": int(ndon),
                     "top1": round(float(top1), 4), "top10": round(float(top10), 4),
                     "gini": round(float(gini), 4)}
    print("  (* 2026 partial cycle)")
    print("\n  vs Section A OUTFLOW top-1% (WA/NY/TX residents): "
          "2018 28/35/29 -> 2024 36/47/42 (presidential sawtooth, mild rise)")

    # ---- (B) donor retention ----
    print("\n" + "=" * 64)
    print("(B) DONOR RETENTION — returning vs new; repeat vs one-time dollars")
    print("=" * 64)
    # cycles each donor appears in
    c.execute("""
        CREATE TEMP TABLE dca AS
        SELECT donor, COUNT(DISTINCT ec) ncycles, SUM(tot) lifetime, MIN(ec) first_ec
        FROM dc GROUP BY 1
    """)
    one_n, one_tot, rep_n, rep_tot = c.execute("""
        SELECT SUM(CASE WHEN ncycles=1 THEN 1 ELSE 0 END),
               SUM(CASE WHEN ncycles=1 THEN lifetime ELSE 0 END),
               SUM(CASE WHEN ncycles>=2 THEN 1 ELSE 0 END),
               SUM(CASE WHEN ncycles>=2 THEN lifetime ELSE 0 END)
        FROM dca
    """).fetchone()
    tot_n = one_n + rep_n
    tot_d = float(one_tot) + float(rep_tot)
    print(f"\nLifetime (2018-2026, name+zip5 proxy):")
    print(f"  one-time donors (1 cycle):  {one_n:>10,} ({one_n/tot_n*100:4.1f}% of donors)  "
          f"${float(one_tot)/1e6:7.1f}M ({float(one_tot)/tot_d*100:4.1f}% of $)")
    print(f"  repeat donors  (>=2 cycles):{rep_n:>10,} ({rep_n/tot_n*100:4.1f}% of donors)  "
          f"${float(rep_tot)/1e6:7.1f}M ({float(rep_tot)/tot_d*100:4.1f}% of $)")

    # per-cycle retention. 'any-prior' grows mechanically (more look-back each
    # cycle); 'prior-cycle' (gave in cy-2) is a FIXED 1-cycle look-back, so its
    # trend is confound-free.
    print(f"\n{'cycle':7} {'donors':>10} {'ret(any)%':>10} {'ret(prior)%':>12} "
          f"{'$ ret(prior)':>13}")
    retention = {}
    for cy in CYCLES:
        row = c.execute(f"""
            WITH cur AS (SELECT donor, tot FROM dc WHERE ec={cy}),
            tagged AS (
                SELECT cur.donor, cur.tot,
                       CASE WHEN EXISTS (SELECT 1 FROM dc p WHERE p.donor=cur.donor AND p.ec < {cy})
                            THEN 1 ELSE 0 END AS any_prior,
                       CASE WHEN EXISTS (SELECT 1 FROM dc p WHERE p.donor=cur.donor AND p.ec = {cy}-2)
                            THEN 1 ELSE 0 END AS prior_cycle
                FROM cur)
            SELECT COUNT(*) ndon, AVG(any_prior) ret_any, AVG(prior_cycle) ret_prior,
                   SUM(tot*prior_cycle)/SUM(tot) ret_prior_dollar
            FROM tagged
        """).fetchone()
        ndon, ret_any, ret_prior, ret_prior_d = row
        marker = "*" if cy == 2026 else " "
        if cy == 2018:
            print(f"{cy}{marker}  {ndon:>10,} {'(baseline — no prior cycle in window)':>40}")
        else:
            print(f"{cy}{marker}  {ndon:>10,} {float(ret_any)*100:9.1f}% "
                  f"{float(ret_prior)*100:11.1f}% {float(ret_prior_d)*100:12.1f}%")
        retention[cy] = {"ndonors": int(ndon),
                         "returning_any_rate": round(float(ret_any), 4),
                         "returning_prior_rate": round(float(ret_prior), 4),
                         "returning_prior_dollar_share": round(float(ret_prior_d), 4)}
    print("  (* 2026 partial. ret(any)=gave in ANY earlier in-window cycle [grows];")
    print("   ret(prior)=gave in the immediately preceding cycle [fixed look-back].)")

    c.close()
    json.dump({"concentration_trend": trend,
               "lifetime": {"one_time_n": int(one_n), "one_time_dollars": float(one_tot),
                            "repeat_n": int(rep_n), "repeat_dollars": float(rep_tot)},
               "retention": retention}, open(OUT, "w"), indent=2)
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
