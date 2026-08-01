"""D1 — what the validation ceiling on false matches does to the headline findings.

The paper concedes that a deterministic rule "moves the uncertainty out of the estimator and
into the sample definition", so match error can be **bounded by validation but not propagated**
through the results. It then reports every headline as a bare point estimate. This closes that
gap: it spends the entire error budget against each finding and reports what survives.

Two parts, because they answer different objections.

**Part 1 — the mechanism.** The blinded rating found 129 of 152 confirmed false matches were
household or relative merges, and **every one landed on an initial-based key**. That is not luck.
A household merge needs the *contributor's* name to equal the matched registrant's name, and on
the primary key that means the same surname AND the same FULL first name at the same ZIP5. Within
a household that is a Jr./Sr. collision, and the uniqueness guard **drops** those: two registrants
sharing the key means no match at all. So the dominant observed failure mode is structurally
suppressed on the specification the paper uses. Part 1 measures how much of it the guard removes,
and how large the household pool that the *initial-based* keys were exposed to actually is.

**Part 2 — the bound.** Whatever residual remains cannot be the household mechanism, so it has to
be a namesake who is not the matched registrant and not on the roll — an unregistered person at
that address, or someone who has since moved away. For that mechanism the right model is
**removal**, not reassignment: the record should never have entered the panel. So the budget is
spent adversarially, removing the 3.1% of matched donors whose deletion moves each statistic
furthest in the direction that would undermine the finding. 3.1% is the Wilson 95% lower bound on
120/120, i.e. the most error the validation cannot rule out.

    PYTHONPATH=src python scripts/diag_match_error_sensitivity.py

Read-only. Writes nothing.
"""
from __future__ import annotations

from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# Wilson 95% lower bound for 120 successes in 120 trials is 0.969, so the upper bound on the
# undetected false-match rate is 3.1%. Stated in the paper as "roughly 3%".
BUDGET = 0.031

AGE_2024 = "date_diff('year', v.birthdate, DATE '2024-11-05')"

PANELS = [
    # tag, db, vrdb, panel table, age expr, party col (None where unpublished)
    ("WA federal", "wa_statewide", "wa_vrdb", "voter_donor_affiliation_fec", AGE_2024, None),
    ("WA state", "wa_statewide", "wa_vrdb", "voter_donor_affiliation_state", AGE_2024, None),
    ("NY federal", "ny_statewide", "ny_vrdb", "voter_donor_affiliation_fec", AGE_2024, "v.party"),
    ("NY state", "ny_statewide", "ny_vrdb", "voter_donor_affiliation_state", AGE_2024, "v.party"),
    ("ID federal", "id_statewide", "id_vrdb", "voter_donor_affiliation_fec", "v.age", "v.party"),
    ("ID state", "id_statewide", "id_vrdb", "voter_donor_affiliation_state", "v.age", "v.party"),
]

# Party labels that carry the paper's Democratic finding, per state file.
DEM = {"ny": ("DEM",), "id": ("DEM", "DEMOCRAT", "DEMOCRATIC")}


def part1_mechanism() -> None:
    """How much of the household mechanism the uniqueness guard removes on the primary key."""
    print("=" * 100)
    print("PART 1 — the household mechanism against the full-name key")
    print("=" * 100)
    print(f"{'state':<8}{'active roll':>13}{'same-key pairs':>16}{'registrants in them':>21}"
          f"{'share of roll':>15}")
    print("-" * 100)
    for st, vrdb in (("WA", "wa_vrdb"), ("NY", "ny_vrdb"), ("ID", "id_vrdb")):
        con = duckdb.connect(str(DATA / f"{vrdb}.duckdb"), read_only=True)
        try:
            n_roll, = con.execute(
                "SELECT COUNT(*) FROM voters WHERE status_code = 'A' "
                "AND first_name IS NOT NULL AND last_name IS NOT NULL "
                "AND reg_zip IS NOT NULL").fetchone()
            # Keys carrying 2+ registrants: same surname, same FULL first name, same ZIP5.
            # These are exactly the collisions the guard refuses to resolve, so they are
            # non-matches rather than false matches.
            n_keys, n_regs = con.execute("""
                SELECT COUNT(*), SUM(n) FROM (
                    SELECT COUNT(*) AS n FROM voters
                    WHERE status_code = 'A' AND first_name IS NOT NULL
                      AND last_name IS NOT NULL AND reg_zip IS NOT NULL
                    GROUP BY UPPER(TRIM(last_name)), UPPER(TRIM(first_name)),
                             SUBSTR(reg_zip, 1, 5)
                    HAVING COUNT(*) > 1)""").fetchone()
        finally:
            con.close()
        print(f"{st:<8}{n_roll:>13,}{n_keys:>16,}{n_regs:>21,}"
              f"{100.0 * n_regs / n_roll:>14.2f}%")

    print()
    print("Those registrants are UNREACHABLE by the primary key — the guard drops the key, so")
    print("they contribute non-matches, never false matches. A same-household same-full-first-name")
    print("collision is the only way the observed failure mode reaches this key, and this is its")
    print("entire population.")
    print()
    print(f"{'state':<8}{'household pool (surname+ZIP5, diff. first name)':>50}{'share of roll':>16}")
    print("-" * 100)
    for st, vrdb in (("WA", "wa_vrdb"), ("NY", "ny_vrdb"), ("ID", "id_vrdb")):
        con = duckdb.connect(str(DATA / f"{vrdb}.duckdb"), read_only=True)
        try:
            n_roll, n_pool = con.execute("""
                SELECT COUNT(*),
                       COUNT(*) FILTER (WHERE n_sur > 1)
                FROM (
                    SELECT COUNT(*) OVER (PARTITION BY UPPER(TRIM(last_name)),
                                                       SUBSTR(reg_zip, 1, 5)) AS n_sur
                    FROM voters
                    WHERE status_code = 'A' AND first_name IS NOT NULL
                      AND last_name IS NOT NULL AND reg_zip IS NOT NULL)""").fetchone()
        finally:
            con.close()
        print(f"{st:<8}{n_pool:>50,}{100.0 * n_pool / n_roll:>15.1f}%")
    print()
    print("That pool is what the INITIAL-based keys were exposed to and where all 129 confirmed")
    print("household merges landed. The full-name key distinguishes those registrants by first")
    print("name, which is why none landed on it.")


def _share_after_removal(con, panel, expr, age_expr, budget=BUDGET):
    """Adversarially remove `budget` of the panel from the bucket `expr` is true for.

    Returns (share before, share after). The removal is the worst case: every deleted record
    is taken from the bucket that supports the finding, which is the most a given error rate
    can do to it.
    """
    n, k = con.execute(f"""
        SELECT COUNT(*), COUNT(*) FILTER (WHERE {expr})
        FROM {panel} a JOIN vrdb.voters v USING (state_voter_id)
        WHERE {age_expr} IS NOT NULL""").fetchone()
    if not n:
        return None, None
    drop = min(int(round(n * budget)), k)
    return 100.0 * k / n, 100.0 * (k - drop) / (n - drop)


def part2_bound() -> None:
    print()
    print("=" * 100)
    print(f"PART 2 — spending the whole {BUDGET:.1%} budget against each finding")
    print("=" * 100)
    print(f"{'panel':<12}{'65+ share':>22}{'DEM share':>22}{'top-1% $ (de-merge)':>22}")
    print(f"{'':<12}{'as built -> bounded':>22}{'as built -> bounded':>22}"
          f"{'as built -> bounded':>22}")
    print("-" * 100)
    for tag, db, vrdb, panel, age_expr, party in PANELS:
        p = DATA / f"{db}.duckdb"
        if not p.exists():
            continue
        con = duckdb.connect(str(p), read_only=True)
        try:
            con.execute(f"ATTACH '{DATA / (vrdb + '.duckdb')}' AS vrdb (READ_ONLY)")
            b65, a65 = _share_after_removal(con, panel, f"{age_expr} >= 65", age_expr)

            if party:
                st = db[:2]
                lst = ", ".join(f"'{x}'" for x in DEM[st])
                bd, ad = _share_after_removal(
                    con, panel, f"UPPER(TRIM({party})) IN ({lst})", age_expr)
            else:
                bd = ad = None

            # Concentration needs a DIFFERENT model, and the reason is worth stating rather
            # than working around. Adversarial *removal* is degenerate for a top-share
            # statistic: deleting the largest 3.1% of donors deletes three times the top-1%
            # population by construction, so the surviving top 1% is a different and far
            # smaller set and the "bound" collapses to an artifact of its own arithmetic
            # (it reads 41.2% -> 9.2% on WA federal, which says nothing about match error).
            #
            # The informative model is a **de-merge**. A household false merge stacks two
            # people's giving into one donor total, which is the mechanism that would inflate
            # concentration, so the adversarial correction is to split the largest 3.1% of
            # donors into two equal halves each and recompute. Total dollars are unchanged;
            # only the ranking is.
            n_pos, = con.execute(
                f"SELECT COUNT(*) FROM {panel} WHERE total_donated > 0").fetchone()
            split = int(round(n_pos * BUDGET))
            t_before, t_after = con.execute(f"""
                WITH r AS (
                    SELECT total_donated amt,
                           ROW_NUMBER() OVER (ORDER BY total_donated DESC) rn
                    FROM {panel} WHERE total_donated > 0),
                base AS (SELECT amt, rn, COUNT(*) OVER () n1, SUM(amt) OVER () tot1 FROM r),
                demerged AS (
                    SELECT CASE WHEN rn <= {split} THEN amt / 2 ELSE amt END AS amt FROM r
                    UNION ALL
                    SELECT amt / 2 FROM r WHERE rn <= {split}),
                d2 AS (SELECT amt, ROW_NUMBER() OVER (ORDER BY amt DESC) rn2,
                              COUNT(*) OVER () n2, SUM(amt) OVER () tot2 FROM demerged)
                SELECT (SELECT 100.0 * SUM(amt) FILTER (WHERE rn <= CEIL(n1 * 0.01))
                               / ANY_VALUE(tot1) FROM base),
                       (SELECT 100.0 * SUM(amt) FILTER (WHERE rn2 <= CEIL(n2 * 0.01))
                               / ANY_VALUE(tot2) FROM d2)""").fetchone()
        finally:
            con.close()

        def fmt(x, y):
            if x is None:
                return f"{'—':>22}"
            return f"{x:>9.1f} -> {y:<9.1f}".rjust(22)

        print(f"{tag:<12}{fmt(b65, a65)}{fmt(bd, ad)}"
              f"{fmt(float(t_before), float(t_after))}")

    print("-" * 100)
    print("Every column is a WORST CASE, not an estimate. Age and party spend the whole budget")
    print("by DELETING records from the single bucket that supports the finding. Concentration")
    print("uses a DE-MERGE instead — splitting the largest 3.1% of donors in two — because")
    print("adversarial removal is degenerate for a top-share statistic: deleting the largest")
    print("3.1% removes three times the top-1% population by construction. The turnout finding")
    print("is omitted because a 3.1% deletion cannot close a 25-29 point gap between groups of")
    print("269K and 12.2M.")


if __name__ == "__main__":
    part1_mechanism()
    part2_bound()
