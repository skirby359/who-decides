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


def panel_values(db, tbl):
    """total_donated for one built panel, or None if the table is absent."""
    c = duckdb.connect(db, read_only=True)
    exists = c.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
        [tbl]).fetchone()[0]
    if not exists:
        c.close()
        return None
    vals = np.array(c.execute(
        f"SELECT total_donated FROM {tbl} WHERE total_donated > 0").fetchall(),
        dtype=float).ravel()
    c.close()
    return vals


# ORDER IS LOAD-BEARING — APPEND ONLY, NEVER INSERT OR REORDER.
# One RNG is threaded through every panel in sequence, so the draws a panel receives depend
# on how many were consumed before it. Inserting a panel, or reordering these rows, silently
# changes every interval below it — including the WA intervals published in the paper's
# Appendix E and asserted by verify_whitepaper.py, which replays this same sequence. The
# four state panels added on 2026-07-28 (external review asked for CIs on all six panels,
# not just Washington's two) are therefore appended AFTER the original three rows rather
# than grouped with their states.
PANELS = [
    # (label, db, table)  — original three, positions fixed
    ("MATCHED WA donors — FEDERAL panel", "data/wa_statewide.duckdb",
     "voter_donor_affiliation_fec"),
    ("MATCHED WA donors — STATE panel (PDC)", "data/wa_statewide.duckdb",
     "voter_donor_affiliation_state"),
    ("__INFLOW__", None, None),
    # appended 2026-07-28
    ("MATCHED NY donors — FEDERAL panel", "data/ny_statewide.duckdb",
     "voter_donor_affiliation_fec"),
    ("MATCHED NY donors — STATE panel (NYSBOE)", "data/ny_statewide.duckdb",
     "voter_donor_affiliation_state"),
    ("MATCHED ID donors — FEDERAL panel", "data/id_statewide.duckdb",
     "voter_donor_affiliation_fec"),
    ("MATCHED ID donors — STATE panel (Sunshine)", "data/id_statewide.duckdb",
     "voter_donor_affiliation_state"),
]


def ordering_test(samples, rng):
    """Bootstrap the DIFFERENCE in top-1% share between states, within each panel.

    Added 2026-07-28. The paper claims the ordering "New York > Washington > Idaho" holds in
    both panels. Overlapping confidence intervals are not a test of that, and eyeballing them
    is how an unsupported ordering claim survives: the right question is whether the
    DIFFERENCE excludes zero. Each state's panel is an independent sample, so the difference
    is resampled independently on each side. A 95% interval containing 0 means the pair is
    not separable at this n and the ordering cannot be asserted for it.
    """
    print("\n" + "=" * 78)
    print("ORDERING TEST — is the NY > WA > ID top-1% ordering separable from zero?")
    print("=" * 78)
    for panel in ("federal", "state"):
        print(f"\n  {panel} panel")
        for a, b in (("NY", "WA"), ("WA", "ID"), ("NY", "ID")):
            xa, xb = samples.get((a, panel)), samples.get((b, panel))
            if xa is None or xb is None:
                continue
            diffs = np.empty(B)
            for i in range(B):
                sa = xa[rng.integers(0, xa.size, xa.size)]
                sb = xb[rng.integers(0, xb.size, xb.size)]
                diffs[i] = (topshare(sa, 0.01) - topshare(sb, 0.01)) * 100
            lo, hi = ci(diffs)
            pt = (topshare(xa, 0.01) - topshare(xb, 0.01)) * 100
            sep = "SEPARABLE" if lo > 0 or hi < 0 else "NOT separable — contains 0"
            print(f"    {a} - {b}: {pt:+6.2f} pts   95% CI [{lo:+.2f}, {hi:+.2f}]   {sep}")


def main():
    rng = np.random.default_rng(SEED)
    samples = {}
    # Panels are never pooled — a state's contribution table can hold federal (FEC:) and
    # state money, and pooling stacks one person's giving across two systems.
    # See docs/donor-class-and-the-electorate.md Appendix C.
    for label, db, tbl in PANELS:
        if label == "__INFLOW__":
            ic = duckdb.connect("data/fec_inflow.duckdb", read_only=True)
            inflow24 = np.array(ic.execute("""
                SELECT SUM(contribution_amount) tot
                FROM inflow_contributions
                WHERE recipient_office IN ('H','S') AND contribution_amount > 0
                  AND election_cycle = 2024 AND contributor_name IS NOT NULL
                GROUP BY UPPER(TRIM(contributor_name)) || '|'
                         || LEFT(COALESCE(contributor_zip,''),5)
            """).fetchall(), dtype=float).ravel()
            ic.close()
            report("INFLOW donors, 2024 cycle (fec_inflow)", inflow24, rng)
            continue
        vals = panel_values(db, tbl)
        if vals is None:
            src = "fec" if tbl.endswith("fec") else "state"
            state = db.split("/")[-1].split("_")[0]
            print(f"  !! {tbl} missing in {db} — build it with "
                  f"scripts/match_{state}_voters_to_donors.py --source {src}")
            continue
        report(f"{label} ({tbl})", vals, rng)
        st = db.split("/")[-1].split("_")[0].upper()
        samples[(st, "federal" if tbl.endswith("fec") else "state")] = vals
    print(f"\n(B={B} bootstrap resamples. Interval WIDTH varies enormously with n: Idaho's\n"
          " 23K-donor panels give a top-1% interval ~18 points wide against ~5 for\n"
          " Washington's, which is why the ordering below must be tested rather than read\n"
          " off the point estimates.)")
    ordering_test(samples, rng)


if __name__ == "__main__":
    main()
