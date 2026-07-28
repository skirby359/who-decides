"""Match Washington voters to donors, one money layer at a time.

The WA counterpart of match_ny_voters_to_donors.py / match_id_voters_to_donors.py.
Washington previously had no dedicated match script — the match ran either through
`main.py` or through the one-liner in CLAUDE.md, both of which call
`match_voters_to_donors(conn)` unscoped. That is how WA's matched layer came to pool
two money systems without anyone choosing it.

DONOR SOURCE — pick a panel with `--source`. WA's `individual_contributions` holds
**federal** FEC contributions (`contribution_id` prefix `FEC:`, 5.58M rows / $646.2M)
AND **state** PDC filings (`PDC:`, 2.97M rows / $394.6M). Matching across both pools
them, so one person's federal and state giving stacks into a single donor total and
measured concentration lands above either layer alone (top-1% 46.6% pooled vs 41.2%
federal / 43.5% state, on a tier-0 read).

    --source fec    -> FEC: rows -> voter_donor_affiliation_fec    (the paper's primary
                                    panel; comparable to NY and ID federal)
    --source state  -> PDC: rows -> voter_donor_affiliation_state  (WA state money;
                                    comparable to ID Sunshine)
    --source all    -> everything -> voter_donor_affiliation       (legacy pooled
                                    behavior; what the campaign tooling reads)

The canonical `voter_donor_affiliation` is only touched by `--source all`, so building
panels never disturbs the table `donor_prospects`, voter segments, and the walk-list
tooling depend on. See docs/donor-class-and-the-electorate.md for the panel design.

Note WA publishes no party of record, so there is no own-party cut here (that is the
dimension NY and ID supply). Generation multipliers and the give<->vote overlap come
from scripts/verify_donor_class.py, which reads voter_scores.

Usage:
    python scripts/match_wa_voters_to_donors.py --source fec
    python scripts/match_wa_voters_to_donors.py --source state
"""
import argparse
import os
import sys

import duckdb

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "src"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from wa_analyzer.analysis.donor_analysis import (  # noqa: E402
    PRIMARY_TIERS, _ALL_TIER_RANKS, match_voters_to_donors,
)

WA_STATEWIDE = "data/wa_statewide.duckdb"
WA_VRDB = "data/wa_vrdb.duckdb"

# --source -> (contribution_id prefixes, output table). See the module docstring.
PANELS = {
    "fec":   (["FEC"], "voter_donor_affiliation_fec"),
    "state": (["PDC"], "voter_donor_affiliation_state"),
    "all":   (None,    "voter_donor_affiliation"),
}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--source", choices=sorted(PANELS), default="fec",
                    help="money layer to match (default: fec)")
    ap.add_argument("--tiers", choices=("full", "all"), default="full",
                    help="match tiers: 'full' = the full-first-name key alone (the "
                         "paper's primary specification, 100%% precision), 'all' = every "
                         "tier incl. the initial-based keys (47.9-71.7%%). Default: full")
    args = ap.parse_args(argv)
    prefixes, vda = PANELS[args.source]
    tiers = list(PRIMARY_TIERS if args.tiers == "full" else _ALL_TIER_RANKS)

    con = duckdb.connect(WA_STATEWIDE)  # read-write: writes the panel table
    con.execute(f"ATTACH '{WA_VRDB}' AS vrdb (READ_ONLY)")

    print(f"[match] running multi-tier voter<->donor match (WA, "
          f"source={args.source} tiers={args.tiers} -> {vda})...")
    res = match_voters_to_donors(con, source_prefixes=prefixes,
                                 output_table=vda, tiers=tiers)
    if res.get("skipped"):
        print("  SKIPPED:", res.get("reason"))
        return 1
    print(f"  matched voters       : {res['matched_voters']:,}")
    print(f"  contributions matched: {res['contributions_matched']:,}")
    print("  match-quality tiers  :")
    for q, n in con.execute(f"""
        SELECT match_quality, count(*) FROM {vda} GROUP BY 1 ORDER BY 2 DESC
    """).fetchall():
        print(f"    {q:18} {n:>10,}")

    total_m = con.execute(
        f"SELECT SUM(total_donated)/1e6 FROM {vda}").fetchone()[0]
    print(f"  matched dollars      : ${total_m:,.2f}M")

    # ---- Donor-dollar concentration (standardized NTILE(100) estimator) ----
    # Same estimator as NY/ID and as verify_donor_class.py: equal-count donor
    # buckets over actual donors, robust to the heavy ties at round dollar amounts
    # that capped state systems produce.
    print("\n=== DONOR-DOLLAR CONCENTRATION (matched WA donors) ===")
    conc = con.execute(f"""
        WITH r AS (SELECT total_donated t, NTILE(100) OVER (ORDER BY total_donated DESC) p
                   FROM {vda} WHERE total_donated > 0)
        SELECT round(100.0*SUM(t) FILTER(WHERE p=1)/SUM(t),1),
               round(100.0*SUM(t) FILTER(WHERE p<=10)/SUM(t),1) FROM r
    """).fetchone()
    gini = con.execute(f"""
        WITH r AS (SELECT total_donated t, ROW_NUMBER() OVER (ORDER BY total_donated) rn,
                          COUNT(*) OVER () n, SUM(total_donated) OVER () s
                   FROM {vda} WHERE total_donated > 0)
        SELECT (2.0*SUM(rn*t)/(MAX(n)*MAX(s))) - (MAX(n)+1.0)/MAX(n) FROM r
    """).fetchone()[0]
    print(f"  top 1% of matched donors  = {conc[0]}% of matched $")
    print(f"  top 10% of matched donors = {conc[1]}% of matched $")
    print(f"  Gini                      = {gini:.3f}")

    # ---- Geographic concentration (top ZIP3s by matched $) ----
    print("\n=== DONOR $ BY ZIP3 (top 6, share of matched $) ===")
    for z3, dn, sh in con.execute(f"""
        WITH d AS (SELECT SUBSTR(v.reg_zip,1,3) z3, vda.total_donated
                   FROM {vda} vda JOIN vrdb.voters v USING (state_voter_id)
                   WHERE vda.total_donated > 0 AND v.reg_zip IS NOT NULL)
        SELECT z3, count(*), 100.0*sum(total_donated)/sum(sum(total_donated)) OVER ()
        FROM d GROUP BY z3 ORDER BY sum(total_donated) DESC LIMIT 6
    """).fetchall():
        print(f"  {z3}xx  {dn:>8,} donors  {sh:5.1f}% of $")

    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
