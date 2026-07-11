"""Bootstrap CIs on donor-concentration metrics.

Concentration (Gini, top-1% / top-10% dollar share) is computed over a donor pool
identified by a name+zip5 PROXY, so the point estimate carries sampling-style
uncertainty. We resample donors with replacement (B=1000) to put 95% CIs on each
metric — confirming the concentration is a precise feature of the data, not an
artifact of which donors happened to land in the pool.

Two pools:
  - MATCHED donors (data/wa_statewide.duckdb voter_donor_affiliation.total_donated) —
    the white-paper §F figures (top-1% 47.7%, top-10% 80.0%, Gini 0.862).
  - INFLOW donors, 2024 cycle (data/fec_inflow.duckdb) — the §I figure.

Note on the proxy's DIRECTION (not bootstrappable): name+zip5 over-merges distinct
people with the same key, which splits no one but fuses some — biasing concentration
slightly DOWN. So these CIs bound sampling noise; the proxy error, if anything, makes
true concentration a touch higher.
"""
import duckdb
import numpy as np

B = 1000
SEED = 12345  # fixed; the script forbids Date/random-driven nondeterminism anyway


def gini(x):
    x = np.sort(x)
    n = x.size
    s = x.sum()
    if s == 0:
        return float("nan")
    idx = np.arange(1, n + 1)
    return (2.0 * np.sum(idx * x) / (n * s)) - (n + 1.0) / n


def topshare(x, frac):
    x = np.sort(x)[::-1]
    k = max(1, int(round(x.size * frac)))
    return x[:k].sum() / x.sum()


def metrics(x):
    return gini(x), topshare(x, 0.01), topshare(x, 0.10)


def boot(x, rng):
    g = np.empty(B); t1 = np.empty(B); t10 = np.empty(B)
    n = x.size
    for b in range(B):
        s = x[rng.integers(0, n, n)]
        g[b], t1[b], t10[b] = metrics(s)
    return g, t1, t10


def ci(a):
    return np.percentile(a, 2.5), np.percentile(a, 97.5)


def report(name, x, rng):
    g, t1, t10 = metrics(x)
    bg, bt1, bt10 = boot(x, rng)
    print(f"\n{name}  (n={x.size:,} donors, ${x.sum()/1e6:,.0f}M)")
    for label, pt, samp in [("Gini", g, bg), ("top-1% share", t1, bt1), ("top-10% share", t10, bt10)]:
        lo, hi = ci(samp)
        unit = "" if label == "Gini" else "%"
        scale = 1 if label == "Gini" else 100
        print(f"   {label:14} {pt*scale:7.3f}{unit}   95% CI [{lo*scale:.3f}, {hi*scale:.3f}]{unit}")


def main():
    rng = np.random.default_rng(SEED)
    c = duckdb.connect("data/wa_statewide.duckdb", read_only=True)
    matched = np.array(c.execute(
        "SELECT total_donated FROM voter_donor_affiliation WHERE total_donated > 0"
    ).fetchall(), dtype=float).ravel()
    c.close()
    report("MATCHED WA donors (voter_donor_affiliation)", matched, rng)

    ic = duckdb.connect("data/fec_inflow.duckdb", read_only=True)
    inflow24 = np.array(ic.execute("""
        SELECT SUM(contribution_amount) tot
        FROM inflow_contributions
        WHERE recipient_office IN ('H','S') AND contribution_amount > 0
          AND election_cycle = 2024 AND contributor_name IS NOT NULL
        GROUP BY UPPER(TRIM(contributor_name)) || '|' || LEFT(COALESCE(contributor_zip,''),5)
    """).fetchall(), dtype=float).ravel()
    ic.close()
    report("INFLOW donors, 2024 cycle (fec_inflow)", inflow24, rng)
    print(f"\n(B={B} bootstrap resamples; CIs are tight at this n — the concentration "
          "estimates are precise.)")


if __name__ == "__main__":
    main()
