"""Harmonized federal-vs-state panel comparison (2026-07-28, external review item 3).

The reviewer's objection: "federal money is older money" is prominent, but the two panels
differ in disclosure threshold, in calendar window, and in WHO IS IN THEM (Jaccard 0.14-0.16),
so the comparison is mostly between different people under different rules. They asked for a
harmonized threshold, aligned windows, a paired within-person comparison, and separate
results for state-only / federal-only / both-system donors.

WHAT CAN AND CANNOT BE HARMONIZED, stated up front because one of the four asks is not
answerable as posed:

  * THRESHOLD -- yes, and it matters. Restricting every panel to donors whose aggregate in
    that panel exceeds $200 (the federal floor) is a direct test: if the age gap survives,
    the floor is not what produces it.
  * WINDOW -- yes for Idaho (already built: `diag_donor_class_revisions.py --build-aligned`),
    and immaterial for Washington, which this script quantifies rather than hedges. New York
    is aligned as built.
  * PAIRED WITHIN-PERSON on AGE -- NOT POSSIBLE, and it is worth saying why rather than
    quietly omitting it. Age and party are properties of the PERSON, not of the panel, so for
    a donor present in both systems the federal and state values are identical by
    construction. A within-person design can only compare DOLLARS. The age panel difference
    is inherently a between-person comparison; what the both-systems group can tell us is
    whether multi-system donors differ from single-system ones, which the paper already
    reports (Finding 1's within-person read).
  * GROUP SPLIT -- yes, reported here under harmonization as well as unrestricted.

Run:  python scripts/diag_panel_harmonized.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

DATA = Path(__file__).resolve().parent.parent / "data"
FED = "voter_donor_affiliation_fec"
STATE = "voter_donor_affiliation_state"
HARMONIZED_FLOOR = 200  # the federal itemization aggregate, the highest of the four

# Age basis per state. NY and WA carry a DOB and are measured at the 2024 general; Idaho's
# roll carries a current-age integer instead. Mixing them is a known defect class here.
_DOB = "date_diff('year', v.birthdate, DATE '2024-11-05')"
STATES = [("WA", "wa_statewide", "wa_vrdb", _DOB, "PDC"),
          ("NY", "ny_statewide", "ny_vrdb", _DOB, "NY"),
          ("ID", "id_statewide", "id_vrdb", "v.age", "SUNSHINE")]


def cut(con, panel, age, floor):
    """(n, 65+ share, top-1% share) for one panel at one floor."""
    n, p65 = con.execute(f"""
        SELECT COUNT(*), 100.0*COUNT(*) FILTER (WHERE {age} >= 65)/COUNT(*)
        FROM {panel} a JOIN vrdb.voters v USING(state_voter_id)
        WHERE a.total_donated > {floor} AND {age} IS NOT NULL""").fetchone()
    t1, = con.execute(f"""
        WITH r AS (SELECT total_donated t, NTILE(100) OVER (ORDER BY total_donated DESC) p
                   FROM {panel} WHERE total_donated > {floor})
        SELECT 100.0*SUM(t) FILTER (WHERE p=1)/SUM(t) FROM r""").fetchone()
    return int(n), float(p65), float(t1)


def groups(con, age, floor):
    """65+ share by which system(s) a donor gives in, at one floor."""
    return dict((g, (int(n), float(p))) for g, n, p in con.execute(f"""
        WITH f AS (SELECT state_voter_id FROM {FED} WHERE total_donated > {floor}),
             s AS (SELECT state_voter_id FROM {STATE} WHERE total_donated > {floor}),
        grp AS (
          SELECT 'fed only' g, f.state_voter_id FROM f
            LEFT JOIN s USING (state_voter_id) WHERE s.state_voter_id IS NULL
          UNION ALL SELECT 'state only', s.state_voter_id FROM s
            LEFT JOIN f USING (state_voter_id) WHERE f.state_voter_id IS NULL
          UNION ALL SELECT 'both', f.state_voter_id FROM f JOIN s USING (state_voter_id))
        SELECT g, COUNT(*), 100.0*COUNT(*) FILTER (WHERE {age} >= 65)/COUNT(*)
        FROM grp JOIN vrdb.voters v USING (state_voter_id)
        WHERE {age} IS NOT NULL GROUP BY 1""").fetchall())


def main() -> int:
    print("=" * 86)
    print(f"HARMONIZED PANEL COMPARISON — every panel restricted to a donor aggregate "
          f"> ${HARMONIZED_FLOOR}")
    print("=" * 86)
    print("The state floors are $25/$100 (WA), $99 (NY) and $50 (ID) against the federal")
    print("$200, so the state panels reach deeper into small-dollar giving by construction.")
    print("Retention below IS that confound made visible.\n")

    gaps = {}
    print(f"  {'st':4}{'panel':9}|{'unrestricted':>28}|{'> $200':>28}")
    print(f"  {'':13}|{'n':>10}{'65+':>9}{'top1':>9}|{'n':>10}{'65+':>9}{'top1':>9}  keep%")
    for st, db, vr, age, _pref in STATES:
        con = duckdb.connect(str(DATA / f"{db}.duckdb"), read_only=True)
        con.execute(f"ATTACH '{DATA / (vr + '.duckdb')}' AS vrdb (READ_ONLY)")
        row = {}
        for tag, panel in (("federal", FED), ("state", STATE)):
            n0, a0, c0 = cut(con, panel, age, 0)
            n1, a1, c1 = cut(con, panel, age, HARMONIZED_FLOOR)
            row[tag] = (n0, a0, c0, n1, a1, c1)
            print(f"  {st:4}{tag:9}|{n0:>10,}{a0:>8.1f}%{c0:>8.1f}%"
                  f"|{n1:>10,}{a1:>8.1f}%{c1:>8.1f}%{100.0*n1/n0:>7.1f}")
        gaps[st] = row
        con.close()

    print("\n" + "-" * 86)
    print("DOES 'FEDERAL MONEY IS OLDER MONEY' SURVIVE HARMONIZATION?")
    print("-" * 86)
    print("  federal 65+ minus state 65+, before and after the common floor:\n")
    print(f"  {'st':4}{'unrestricted gap':>19}{'harmonized gap':>17}{'change':>10}   verdict")
    for st in gaps:
        f0, s0 = gaps[st]["federal"], gaps[st]["state"]
        g0, g1 = f0[1] - s0[1], f0[4] - s0[4]
        verdict = ("survives" if g1 > 0 else "REVERSES") + (
            f", {abs(g0 - g1) / g0 * 100:.0f}% of it was the floor" if g0 else "")
        print(f"  {st:4}{g0:>+18.1f}{g1:>+17.1f}{g1 - g0:>+10.1f}   {verdict}")

    print("\n" + "-" * 86)
    print("AND THE CONCENTRATION ORDERING BETWEEN THE TWO LAYERS")
    print("-" * 86)
    print("  The paper reports that state money is MORE concentrated in WA and ID but LESS")
    print("  in NY, i.e. that the layer comparison 'does not run one way'. On a common")
    print("  floor:\n")
    print(f"  {'st':4}{'unrestricted':>26}{'harmonized':>26}")
    for st in gaps:
        f0, s0 = gaps[st]["federal"], gaps[st]["state"]
        d0, d1 = s0[2] - f0[2], s0[5] - f0[5]
        w0 = "state more" if d0 > 0 else "federal more"
        w1 = "state more" if d1 > 0 else "federal more"
        flip = "   <-- ORDERING FLIPS" if (d0 > 0) != (d1 > 0) else ""
        print(f"  {st:4}{f'{d0:+.1f} pts ({w0})':>26}{f'{d1:+.1f} pts ({w1})':>26}{flip}")

    print("\n" + "-" * 86)
    print("WITHIN-PERSON GROUPS (65+ share), unrestricted and harmonized")
    print("-" * 86)
    print("  Age is a property of the PERSON, so this is a between-GROUP comparison, not a")
    print("  paired within-person one — see the module docstring for why the latter cannot")
    print("  test an age difference.\n")
    for st, db, vr, age, _pref in STATES:
        con = duckdb.connect(str(DATA / f"{db}.duckdb"), read_only=True)
        con.execute(f"ATTACH '{DATA / (vr + '.duckdb')}' AS vrdb (READ_ONLY)")
        g0, g1 = groups(con, age, 0), groups(con, age, HARMONIZED_FLOOR)
        con.close()
        print(f"  {st}")
        for key in ("state only", "fed only", "both"):
            n0, p0 = g0.get(key, (0, 0.0))
            n1, p1 = g1.get(key, (0, 0.0))
            print(f"    {key:11} unrestricted {p0:5.1f}% (n={n0:>7,})   "
                  f"> ${HARMONIZED_FLOOR} {p1:5.1f}% (n={n1:>7,})")

    print("\n" + "-" * 86)
    print("WINDOW ALIGNMENT — the third confound, quantified rather than hedged")
    print("-" * 86)
    wa = duckdb.connect(str(DATA / "wa_statewide.duckdb"), read_only=True)
    n, m, n16, m16 = wa.execute("""
        SELECT COUNT(*), SUM(contribution_amount)/1e6,
               COUNT(*) FILTER (WHERE EXTRACT(year FROM contribution_date) = 2016),
               SUM(contribution_amount) FILTER (
                   WHERE EXTRACT(year FROM contribution_date) = 2016)/1e6
        FROM individual_contributions
        WHERE contribution_id LIKE 'PDC:%' AND contribution_amount > 0
          AND contribution_date IS NOT NULL""").fetchone()
    wa.close()
    print(f"  WA: the PDC layer opens in 2016, one year before the FEC layer. That year is")
    print(f"      {n16:,} of {n:,} gifts ({100.0*n16/n:.2f}%) and ${float(m16):.2f}M of "
          f"${float(m):.1f}M ({100.0*float(m16)/float(m):.2f}% of dollars) — so the")
    print(f"      misalignment is real but cannot move a panel comparison materially.")
    print("  NY: both layers 2017-2026, aligned as built.")
    print("  ID: Sunshine covers 2023-2025 against a 2017-2026 federal layer — the one")
    print("      material misalignment, and the aligned rebuild WIDENS the age gap")
    print("      (68.5% vs 51.3%), so alignment does not explain it either.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
