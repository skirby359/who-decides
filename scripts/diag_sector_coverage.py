"""How much of the money does the Section-H 'sector' classifier actually classify? —
a coverage/robustness diagnostic for `docs/cross-state-fec-money.md` Section H.

Section H assigns a donor 'sector' by keyword-matching the free-text `contributor_employer`
string (hardcoded dict in `diag_sector_vs_competitiveness.py`, first-match-wins) — not FEC
industry codes (there are none in the bulk data) and not occupation. This script reuses that
exact classifier and reports how much inflow money lands in a named sector vs the
'non-working/none' and 'unclassified' buckets, and lists the biggest UNCLASSIFIED employers
— the money the sector cut can't see, and the shortlist for improving the keyword map.

Purpose: put hard numbers behind the paper's "indicative, not audited" caveat. If only a
small slice is classified, the sector-by-competitiveness findings rest on a thin base and
the prose should say so plainly (or the classifier should be extended from the list below).

Read-only, aggregates only. Same universe as Section H (House inflow, cycles >= 2022).
    python scripts/diag_sector_coverage.py
"""
import duckdb

from diag_sector_vs_competitiveness import sector_sql_column  # the exact Section-H classifier

DB = "data/fec_inflow.duckdb"
UNIVERSE = "recipient_office='H' AND election_cycle>=2022 AND contribution_amount>0"


def main():
    col = sector_sql_column()  # CASE ... END over alias `e`
    con = duckdb.connect(DB, read_only=True)
    base = (f"SELECT UPPER(TRIM(COALESCE(contributor_employer,''))) e, contribution_amount amt "
            f"FROM inflow_contributions WHERE {UNIVERSE}")

    total = con.execute(f"SELECT SUM(amt), COUNT(*) FROM ({base})").fetchone()
    tot_amt, tot_n = float(total[0]), int(total[1])
    print(f"Section-H sector classifier coverage — House inflow, cycles >= 2022")
    print(f"total: ${tot_amt/1e6:,.1f}M across {tot_n:,} contributions\n")

    rows = con.execute(
        f"WITH classed AS (SELECT {col} sector, amt FROM ({base})) "
        "SELECT sector, SUM(amt) amt, COUNT(*) n FROM classed GROUP BY 1 ORDER BY 2 DESC"
    ).fetchall()
    print(f"  {'sector':18}{'$M':>10}{'% of $':>9}{'% of rows':>11}")
    named_amt = 0.0
    for sector, amt, n in rows:
        amt = float(amt)
        if sector not in ("non-working/none", "unclassified"):
            named_amt += amt
        print(f"  {sector:18}{amt/1e6:>10.1f}{amt/tot_amt*100:>8.1f}%{n/tot_n*100:>10.1f}%")
    print(f"\n  -> only {named_amt/tot_amt*100:.1f}% of dollars land in a NAMED sector; the rest is "
          f"non-working/none or unclassified.")

    print("\n  Top 20 UNCLASSIFIED employers by $ (the classifier's blind spots / extension list):")
    un = con.execute(
        f"WITH classed AS (SELECT e, {col} sector, amt FROM ({base})) "
        "SELECT e, SUM(amt) amt, COUNT(*) n FROM classed WHERE sector='unclassified' "
        "GROUP BY 1 ORDER BY 2 DESC LIMIT 20"
    ).fetchall()
    for e, amt, n in un:
        label = e if e else "(blank)"
        print(f"    {label[:44]:44}{float(amt)/1e6:>8.2f}M  ({n:,} gifts)")
    con.close()

    print("\nInterpretation: the sector cut classifies only a thin slice of the money, so "
          "Section H's\nsector-by-competitiveness numbers are indicative at best. Either "
          "extend the keyword map\nfrom the list above, or soften the paper's sector claims "
          "to match the coverage.")


if __name__ == "__main__":
    main()
