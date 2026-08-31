"""How many repeat match-ups does Washington's record actually contain?

RAISED BY AN EXTERNAL REFEREE, 2026-08-25. `does-money-move-votes.md` claims its
contribution is an identification failure, which obliges a search of the design space rather
than a list of designs. The referee's sharpest instance: Levitt (1994) differences out
candidate quality using the same two candidates meeting more than once, the paper named that
design and set it aside in a clause, and **it never reported how many repeat pairings exist**.
"If there are twenty, that's a Levitt design — underpowered, but the actual thing the
literature review says you lack."

So count them. A repeat match-up is a (chamber, district) where a Democratic candidate and a
Republican candidate both appear in more than one cycle with BOTH names unchanged; each extra
cycle contributes one differenced observation.

THE ANSWER, and it settles the design question rather than deferring it: three usable pairs
federally, eight in the legislature, each spanning exactly two cycles. Pooling to reach eleven
would pool FEC and PDC measurement systems the paper has already established are
non-equivalent. Three differenced observations is not an underpowered Levitt design; it is not
a design.

⚠ Worth stating because the intuition runs the other way: legislative rematches FEEL common,
and the referee expected them to be. Measured, they are 8 of 214 district-cycles.

NAME MATCHING, and its one weakness. Candidates are matched on the uppercased, trimmed
`candidate_name` as `candidate_finance` stores it, within (office, district, party). A
candidate whose filed name changes between cycles -- a middle initial appearing, a married
name -- reads as two people and UNDERCOUNTS repeats. That biases toward finding fewer pairs,
which is the direction that would make this script's conclusion too pessimistic, so it is
stated rather than buried. It cannot bias the other way: two different people cannot collapse
into one repeat unless they file identical names in the same district and party.

BASIS. `candidate_finance` state-disclosure and FEC rows, `total_receipts > 0`, major-party
only, cycles 2018-2024 (the four completed cycles the estimator uses). Aggregate counts only;
no personal data is printed -- candidate names are used as join keys and never emitted.

⚠ `both` is a DuckDB RESERVED WORD in alias position and the first version of this script
used it as a CTE name, failing with a bare "syntax error at or near" that names nothing.
Same class as the `rows` / `returning` / `matched` traps CLAUDE.md already lists; the CTE is
`bothsides`.

    python scripts/diag_repeat_matchups.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

import duckdb  # noqa: E402

DB = ROOT / "data" / "wa_statewide.duckdb"
CYCLES = (2018, 2020, 2022, 2024)

PANELS = (
    ("congressional (U.S. House)", ("H",)),
    ("state house", ("SR",)),
    ("state senate", ("SS",)),
    ("state legislative (both)", ("SR", "SS")),
)


def _sql(offices: tuple[str, ...]) -> str:
    off = ", ".join(f"'{o}'" for o in offices)
    cyc = ", ".join(str(c) for c in CYCLES)
    return f"""
    WITH cf AS (
        SELECT DISTINCT election_cycle cyc, office, district dist, party,
               UPPER(TRIM(candidate_name)) nm
        FROM candidate_finance
        WHERE state='WA' AND office IN ({off}) AND total_receipts > 0
          AND party IN ('Democratic','Republican')
          AND election_cycle IN ({cyc})),
    pair AS (
        SELECT cyc, office, dist,
               MAX(CASE WHEN party='Democratic' THEN nm END) d_nm,
               MAX(CASE WHEN party='Republican'  THEN nm END) r_nm
        FROM cf GROUP BY 1,2,3),
    bothsides AS (SELECT * FROM pair WHERE d_nm IS NOT NULL AND r_nm IS NOT NULL),
    rep AS (
        SELECT office, dist, d_nm, r_nm, COUNT(*) n
        FROM bothsides GROUP BY 1,2,3,4 HAVING COUNT(*) > 1)
    SELECT (SELECT COUNT(*) FROM bothsides),
           (SELECT COUNT(*) FROM rep),
           (SELECT COALESCE(SUM(n - 1), 0) FROM rep),
           (SELECT COALESCE(MAX(n), 0) FROM rep)"""


def main() -> int:
    if not DB.exists():
        print(f"FATAL: database missing: {DB}")
        return 1
    con = duckdb.connect(str(DB), read_only=True)
    print("=" * 88)
    print("REPEAT MATCH-UPS — is a Levitt (1994) design available in this record?")
    print("=" * 88)
    print("A repeat match-up: same district, same Democratic name, same Republican name,")
    print("in more than one of the four completed cycles. Each extra cycle contributes one")
    print("differenced observation.\n")
    print(f"{'panel':28} {'D-v-R cycles':>13} {'repeats':>8} {'differenced':>12} "
          f"{'max cycles':>11}")
    print("-" * 88)
    fed_diff = leg_diff = 0
    for label, offices in PANELS:
        tot, rep, diff, mx = con.execute(_sql(offices)).fetchone()
        print(f"{label:28} {tot:>13} {rep:>8} {diff:>12} {mx:>11}")
        if offices == ("H",):
            fed_diff = diff
        if offices == ("SR", "SS"):
            leg_diff = diff

    print("\nThe congressional repeats, for the record (district and cycles only):")
    for r in con.execute(_sql(("H",)).replace(
            """    SELECT (SELECT COUNT(*) FROM bothsides),
           (SELECT COUNT(*) FROM rep),
           (SELECT COALESCE(SUM(n - 1), 0) FROM rep),
           (SELECT COALESCE(MAX(n), 0) FROM rep)""",
            """    SELECT r.dist, LIST(b.cyc ORDER BY b.cyc)
    FROM rep r JOIN bothsides b
      ON b.office = r.office AND b.dist = r.dist
     AND b.d_nm = r.d_nm AND b.r_nm = r.r_nm
    GROUP BY 1 ORDER BY 1""")).fetchall():
        print(f"    cd{r[0]}  cycles {r[1]}")

    print(f"\nVERDICT: {fed_diff} differenced observations federally, {leg_diff} in the "
          f"legislature.")
    print("Pooling to reach the combined figure would pool FEC and PDC measurement systems")
    print("this paper establishes are non-equivalent (Finding 3). Neither panel supports a")
    print("repeat-challenger design; the congressional one is not underpowered, it is absent.")
    print("\n⚠ The name match UNDERCOUNTS if a candidate's filed name changes between cycles,")
    print("which is the direction that would make this verdict too pessimistic. It cannot")
    print("overcount: two people would have to file identical names in one district and party.")
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
