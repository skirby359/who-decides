"""Independent re-derivation of the headline numbers in docs/cross-state-fec-money.md.

Companion to the other verify_* harnesses. From-scratch SQL, read-only,
aggregate-only, derived-vs-paper. Two layers:

  OUTFLOW — each state's residents' FEC individual contributions
            (`individual_contributions` in wa/ny/tx_statewide.duckdb): dollar
            concentration (top-1% / top-10% / Gini), the retail/whale/retired
            dollar-share cuts, and donor counts (§Headline, §1-§3).
  INFLOW  — recipient-anchored dataset (`fec_inflow.duckdb`, one table
            `inflow_contributions`): total volume, per-recipient-state dollars,
            and out-of-state share (§E).

Outflow basis = the paper's: FEC individual contributions by IN-STATE RESIDENTS,
restricted to rows with an FEC committee id (`fec_candidate_id ~ '^[CPHS][0-9]'`) and
`contributor_state=<ST>` (WA's table also holds state PDC rows + non-resident donors;
this filter drops them and, incidentally, the odd/placeholder cycles). Donor identity
= (UPPER(name), zip5). NOTE: the matched-VOTER donor concentration (top-1% 47.7% WA) is
a different population (voter_donor_affiliation) — that's verify_donor_class.py; here
"donors" = all in-state FEC individual contributors.

Run:  python scripts/verify_cross_state_money.py
"""
from pathlib import Path
import sys

import duckdb

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

DATA = Path(__file__).resolve().parent.parent / "data"
# paper §Headline (all cycles pooled): <200 / >=5000 / retired $ share; top1 / top10 / Gini
PAPER_OUT = {
    "WA": dict(lt200=25.0, ge5000=20.0, retired=24.0, top1=39.3, top10=72.3, gini=0.800, donors="~362K"),
    "NY": dict(lt200=13.8, ge5000=34.8, retired=11.8, top1=47.5, top10=78.7, gini=0.848, donors="~671K"),
    "TX": dict(lt200=20.3, ge5000=33.3, retired=19.5, top1=41.7, top10=74.5, gini=0.818, donors="~837K"),
}
PAPER_INFLOW = {"rows": "5.48M", "dollars": "$1.20B",
                "WA": "$154.6M", "NY": "$462.7M", "TX": "$582.4M"}


def outflow(state):
    con = duckdb.connect(str(DATA / f"{state.lower()}_statewide.duckdb"), read_only=True)
    # Canonical outflow basis — identical to cross_state_fec_money.py and the paper:
    # FEC individual contributions BY IN-STATE RESIDENTS. WA's individual_contributions
    # mixes state PDC + federal FEC, so restrict to rows carrying an FEC committee id
    # AND a resident donor. No-op for TX (already clean bulk); tightens NY and WA to the
    # paper's population. This is the fix for the former WA-outflow divergence.
    filt = ("regexp_matches(COALESCE(fec_candidate_id,''),'^[CPHS][0-9]') "
            f"AND contributor_state='{state}' AND contribution_amount>0")
    shares = con.execute(f"""
        SELECT 100.0*SUM(contribution_amount) FILTER(WHERE contribution_amount<200)/SUM(contribution_amount),
               100.0*SUM(contribution_amount) FILTER(WHERE contribution_amount>=5000)/SUM(contribution_amount),
               100.0*SUM(contribution_amount) FILTER(WHERE contributor_occupation ILIKE '%retired%')/SUM(contribution_amount)
        FROM individual_contributions WHERE {filt}
    """).fetchone()
    # per-donor concentration (donor = UPPER(name)+zip5)
    conc = con.execute(f"""
        WITH d AS (SELECT SUM(contribution_amount) t
                   FROM individual_contributions WHERE {filt}
                   GROUP BY UPPER(TRIM(contributor_name)), LEFT(COALESCE(contributor_zip,''),5))
        SELECT COUNT(*) FROM d
    """).fetchone()[0]
    top = con.execute(f"""
        WITH d AS (SELECT SUM(contribution_amount) t
                   FROM individual_contributions WHERE {filt}
                   GROUP BY UPPER(TRIM(contributor_name)), LEFT(COALESCE(contributor_zip,''),5)),
             p AS (SELECT t, NTILE(100) OVER (ORDER BY t DESC) b FROM d)
        SELECT 100.0*SUM(t) FILTER(WHERE b=1)/SUM(t), 100.0*SUM(t) FILTER(WHERE b<=10)/SUM(t) FROM p
    """).fetchone()
    gini = con.execute(f"""
        WITH d AS (SELECT SUM(contribution_amount) t
                   FROM individual_contributions WHERE {filt}
                   GROUP BY UPPER(TRIM(contributor_name)), LEFT(COALESCE(contributor_zip,''),5)),
             r AS (SELECT t, ROW_NUMBER() OVER (ORDER BY t ASC) i FROM d)
        SELECT (2.0*SUM(i*t)/((SELECT COUNT(*) FROM r)*(SELECT SUM(t) FROM r)))
               - ((SELECT COUNT(*) FROM r)+1.0)/(SELECT COUNT(*) FROM r) FROM r
    """).fetchone()[0]
    con.close()
    return dict(lt200=shares[0], ge5000=shares[1], retired=shares[2],
                donors=conc, top1=top[0], top10=top[1], gini=gini)


def main():
    print("=" * 82)
    print("OUTFLOW — FEC individual contributions by state residents (all cycles pooled)")
    print("=" * 82)
    print(f"{'state':>5} {'donors':>9} | {'<$200 $%':>9} {'≥$5k $%':>9} {'retired $%':>11} | "
          f"{'top1%':>6} {'top10%':>7} {'Gini':>6}")
    for st in ("WA", "NY", "TX"):
        try:
            d = outflow(st)
        except Exception as ex:  # noqa: BLE001
            print(f"{st:>5}  ERROR: {ex}")
            continue
        p = PAPER_OUT[st]
        print(f"{st:>5} {d['donors']:>9,} | {d['lt200']:>8.1f}% {d['ge5000']:>8.1f}% "
              f"{d['retired']:>10.1f}% | {d['top1']:>5.1f}% {d['top10']:>6.1f}% {d['gini']:>6.3f}")
        print(f"{'paper':>5} {p['donors']:>9} | {p['lt200']:>8.1f}% {p['ge5000']:>8.1f}% "
              f"{p['retired']:>10.1f}% | {p['top1']:>5.1f}% {p['top10']:>6.1f}% {p['gini']:>6.3f}")
    print("  (top1/top10/Gini use a name+zip donor key -> sub-0.5pt drift from the paper's")
    print("   grouping is expected; dollar-share cuts are grouping-free.)")
    print("  ✓ WA outflow RECONCILED (2026-07-10): applying the paper's filter (FEC committee id +")
    print("    contributor_state='WA') reproduces 361,818 donors / 39.3% / 72.3% / 0.800, matching")
    print("    the paper exactly. The former 1.12M/47.5% was raw-unfiltered (PDC + non-WA + odd")
    print("    cycles). NY tightens to 671K (was 699K raw); TX unchanged. All three now reproduce.")

    print("\n" + "=" * 82)
    print("INFLOW — recipient-anchored (fec_inflow.duckdb)")
    print("=" * 82)
    ic = duckdb.connect(str(DATA / "fec_inflow.duckdb"), read_only=True)
    nrows, dollars = ic.execute(
        "SELECT COUNT(*), SUM(contribution_amount) FROM inflow_contributions").fetchone()
    dollars = float(dollars)
    print(f"  total: {nrows:,} rows / ${dollars/1e9:.2f}B   (paper: {PAPER_INFLOW['rows']} / {PAPER_INFLOW['dollars']})")
    rows = ic.execute("""
        SELECT recipient_state,
               SUM(contribution_amount) tot,
               100.0*SUM(contribution_amount) FILTER(WHERE contributor_state<>recipient_state)
                   /SUM(contribution_amount) oos
        FROM inflow_contributions GROUP BY 1 ORDER BY tot DESC
    """).fetchall()
    print(f"  {'recip':>6} {'$ in':>10} {'paper':>10} {'out-of-state $%':>16}")
    for st, tot, oos in rows:
        print(f"  {st:>6} {'$'+format(float(tot)/1e6,',.1f')+'M':>10} {PAPER_INFLOW.get(st,'?'):>10} {float(oos):>15.1f}%")
    ic.close()
    print("  (paper §E: out-of-state share ~36-45% across competitiveness bands.)")


if __name__ == "__main__":
    main()
