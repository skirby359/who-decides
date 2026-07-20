"""Cross-state FEC donor-profile comparison (state-agnostic).

Apples-to-apples basis = FEDERAL individual contributions BY IN-STATE
RESIDENTS (2018-2026). Pure-FEC-bulk DBs (NY/TX) and mixed state+FEC DBs
(WA=PDC, ID=Sunshine) are handled uniformly: rows are restricted to those
carrying an FEC committee id (fec_candidate_id ~ '^[CPHS][0-9]', which excludes
the 'SUNSHINE:'/PDC state-finance rows) AND contributor_state=<st>. The region
is discovered dynamically (cross_state_common.region_states: every
data/*_statewide.duckdb on disk, or CROSS_STATE_REGION override) — adding a
state needs no edit here.

This measures how each state's RESIDENTS give to federal committees
(outflow by donor residence) — NOT out-of-state money flowing INTO a
state's races (the FEC ingest is donor-residence-filtered, so inflow is
not observable here). Concentration / small-vs-whale / occupation /
conduit metrics are all robust on this basis.

Outputs a JSON blob (for write-up) + a printed comparison.
"""
import duckdb

from cross_state_common import region_states, write_json

STATES = region_states()
ACTBLUE = "C00401224"
WINRED = "C00694323"


def analyze(st: str, path: str) -> dict:
    c = duckdb.connect(path, read_only=True)
    where = (
        "regexp_matches(COALESCE(fec_candidate_id,''),'^[CPHS][0-9]') "
        f"AND contributor_state='{st}' AND contribution_amount > 0"
    )
    base = f"FROM individual_contributions WHERE {where}"

    total, n = c.execute(
        f"SELECT SUM(contribution_amount), COUNT(*) {base}"
    ).fetchone()
    med, mean = c.execute(
        f"SELECT median(contribution_amount), AVG(contribution_amount) {base}"
    ).fetchone()

    # Per-donor aggregation (name + zip5 proxy) for concentration.
    c.execute(
        "CREATE TEMP TABLE d AS SELECT UPPER(TRIM(contributor_name)) nm, "
        f"LEFT(COALESCE(contributor_zip,''),5) z, SUM(contribution_amount) tot {base} "
        "GROUP BY 1,2"
    )
    ndon = c.execute("SELECT COUNT(*) FROM d").fetchone()[0]
    gini = c.execute(
        "WITH r AS (SELECT tot, ROW_NUMBER() OVER (ORDER BY tot) rn, "
        "COUNT(*) OVER () n, SUM(tot) OVER () s FROM d) "
        "SELECT (2.0*SUM(rn*tot)/(MAX(n)*MAX(s))) - (MAX(n)+1.0)/MAX(n) FROM r"
    ).fetchone()[0]
    top1, top10 = c.execute(
        "WITH ranked AS (SELECT tot, NTILE(100) OVER (ORDER BY tot DESC) p FROM d) "
        "SELECT SUM(tot) FILTER (WHERE p=1)/SUM(tot), "
        "SUM(tot) FILTER (WHERE p<=10)/SUM(tot) FROM ranked"
    ).fetchone()

    # Dollar share by gift size.
    b = c.execute(
        f"SELECT "
        "SUM(contribution_amount) FILTER (WHERE contribution_amount<200)/SUM(contribution_amount), "
        "SUM(contribution_amount) FILTER (WHERE contribution_amount>=200 AND contribution_amount<1000)/SUM(contribution_amount), "
        "SUM(contribution_amount) FILTER (WHERE contribution_amount>=1000 AND contribution_amount<5000)/SUM(contribution_amount), "
        f"SUM(contribution_amount) FILTER (WHERE contribution_amount>=5000)/SUM(contribution_amount) {base}"
    ).fetchone()

    # Non-working / retired economy (share of dollars).
    nonwork = c.execute(
        "SELECT SUM(contribution_amount) FILTER (WHERE "
        "UPPER(COALESCE(contributor_occupation,'')) IN ('RETIRED','NOT EMPLOYED','NONE','N/A','UNEMPLOYED') "
        "OR UPPER(COALESCE(contributor_employer,'')) IN ('RETIRED','NOT EMPLOYED','NONE','N/A','UNEMPLOYED','')"
        f")/SUM(contribution_amount) {base}"
    ).fetchone()[0]
    retired = c.execute(
        "SELECT SUM(contribution_amount) FILTER (WHERE "
        "UPPER(COALESCE(contributor_occupation,''))='RETIRED' "
        "OR UPPER(COALESCE(contributor_employer,''))='RETIRED'"
        f")/SUM(contribution_amount) {base}"
    ).fetchone()[0]
    top_emp = c.execute(
        f"SELECT UPPER(contributor_employer) e, ROUND(SUM(contribution_amount)/1e6,2) M {base} "
        "AND contributor_employer IS NOT NULL "
        "AND UPPER(contributor_employer) NOT IN "
        "('RETIRED','NOT EMPLOYED','NONE','N/A','SELF','SELF EMPLOYED','SELF-EMPLOYED','HOMEMAKER','UNEMPLOYED','INFORMATION REQUESTED') "
        "GROUP BY 1 ORDER BY M DESC LIMIT 6"
    ).fetchall()

    # Conduit reliance (share of dollars routed through the big two).
    ab, wr = c.execute(
        f"SELECT "
        f"SUM(contribution_amount) FILTER (WHERE fec_candidate_id='{ACTBLUE}')/SUM(contribution_amount), "
        f"SUM(contribution_amount) FILTER (WHERE fec_candidate_id='{WINRED}')/SUM(contribution_amount) {base}"
    ).fetchone()

    bycycle = c.execute(
        f"SELECT election_cycle, ROUND(SUM(contribution_amount)/1e6,1) {base} GROUP BY 1 ORDER BY 1"
    ).fetchall()

    c.execute("DROP TABLE d")
    c.close()

    f = lambda x: round(float(x), 4) if x is not None else None
    return {
        "state": st,
        "total_dollars": float(total or 0),
        "n_contributions": int(n or 0),
        "n_donors": int(ndon or 0),
        "median_gift": f(med),
        "mean_gift": f(mean),
        "gini": f(gini),
        "top1_share": f(top1),
        "top10_share": f(top10),
        "dollar_share_sub200": f(b[0]),
        "dollar_share_200_999": f(b[1]),
        "dollar_share_1k_5k": f(b[2]),
        "dollar_share_5k_plus": f(b[3]),
        "nonworking_share": f(nonwork),
        "retired_share": f(retired),
        "top_employers": [(e, m) for e, m in top_emp],
        "actblue_share": f(ab),
        "winred_share": f(wr),
        "by_cycle_millions": [(int(yr), float(m)) for yr, m in bycycle],
    }


def main():
    results = [analyze(st, path) for st, path in STATES]
    out = write_json("cross_state_fec.json", results)
    print(f"wrote {out}\n")

    cols = [
        ("Total $M", lambda r: f"{r['total_dollars']/1e6:,.0f}"),
        ("Contribs", lambda r: f"{r['n_contributions']:,}"),
        ("Donors", lambda r: f"{r['n_donors']:,}"),
        ("Median$", lambda r: f"{r['median_gift']:,.0f}"),
        ("Gini", lambda r: f"{r['gini']:.3f}"),
        ("Top1%$", lambda r: f"{r['top1_share']*100:.1f}%"),
        ("Top10%$", lambda r: f"{r['top10_share']*100:.1f}%"),
        ("<$200$", lambda r: f"{r['dollar_share_sub200']*100:.1f}%"),
        (">=$5k$", lambda r: f"{r['dollar_share_5k_plus']*100:.1f}%"),
        ("NonWork$", lambda r: f"{r['nonworking_share']*100:.1f}%"),
        ("Retired$", lambda r: f"{r['retired_share']*100:.1f}%"),
        ("ActBlue$", lambda r: f"{r['actblue_share']*100:.1f}%"),
        ("WinRed$", lambda r: f"{r['winred_share']*100:.1f}%"),
    ]
    hdr = "Metric".ljust(12) + "".join(r["state"].rjust(14) for r in results)
    print(hdr)
    print("-" * len(hdr))
    for name, fn in cols:
        print(name.ljust(12) + "".join(fn(r).rjust(14) for r in results))
    print("\nTop employers (by $M, ex-retired/self/homemaker):")
    for r in results:
        print(f"  {r['state']}: " + "; ".join(f"{e} ${m}M" for e, m in r["top_employers"]))
    print("\nBy cycle ($M):")
    for r in results:
        print(f"  {r['state']}: " + ", ".join(f"{yr}:{m}" for yr, m in r["by_cycle_millions"]))


if __name__ == "__main__":
    main()
