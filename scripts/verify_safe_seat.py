"""Independent re-derivation of the headline numbers in docs/safe-seat-washington.md.

Companion to the verify_who_decides_* harnesses. Re-derives OBSERVED general-
election competitiveness with from-scratch SQL over `precinct_results` in each
state DB (not by importing diag_safe_seat_*). Read-only; aggregate output only.

Per seat (race): tally D vs R two-party votes (party via candidates.party_normalized,
write-ins excluded); classify UNCONTESTED (1 candidate) / SAME-PARTY (>=2 but no
cross-party — WA top-two) / D-vs-R banded by |D-R|/(D+R) (Tossup<5 / Lean5-10 /
Likely10-20 / Solid>=20). NON-COMPETITIVE = uncontested + same-party + Likely + Solid.

Covers: WA observed by-year 2016-2024 + 2024 detail (lead table), and the four-state
lower-chamber map. TX note: the TLC VTD returns omit uncontested seats, so
precinct_results carries only ~96/150 TX House districts; the 54 absent are
uncontested by construction, so we backfill them as no-major-choice to reach 150
(the r206 presidential holding-party split is NOT re-derived here — it only affects
the D/R split, not the non-competitive count).

Run:  python scripts/verify_safe_seat.py
"""
from pathlib import Path
import sys

import duckdb

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

D = str(Path(__file__).resolve().parent.parent / "data")
PARTY = ("CASE WHEN party_normalized ILIKE '%democrat%' THEN 'D' "
         "WHEN party_normalized ILIKE '%republican%' OR party_normalized ILIKE '%gop%' "
         "THEN 'R' ELSE 'O' END")
WA_OFFICES = ("State Representative Pos. 1", "State Representative Pos. 2",
              "State Senator", "U.S. Representative")


def band(m):
    return "Tossup" if m < 5 else "Lean" if m < 10 else "Likely" if m < 20 else "Solid"


def seats(con, date, office_sql):
    """Per-seat (ncand, D, R) for the general on `date` where `office_sql` matches."""
    return con.execute(f"""
        WITH cand AS (
            SELECT r.race_id, ({PARTY}) pty, cd.candidate_id
            FROM races r JOIN elections e ON e.election_id=r.election_id
            JOIN candidates cd ON cd.race_id=r.race_id
            WHERE e.election_type='general' AND date_part('year', e.election_date)=date_part('year', DATE '{date}')
              AND ({office_sql}) AND COALESCE(cd.is_writein, FALSE)=FALSE),
        -- sum per CANDIDATE first (so ncand counts candidates, not parties — a WA
        -- top-two same-party general has 2 candidates of one party), then per race.
        v AS (SELECT c.race_id, c.candidate_id, c.pty, SUM(pr.votes) vv
              FROM cand c JOIN precinct_results pr ON pr.candidate_id=c.candidate_id GROUP BY 1,2,3)
        SELECT race_id, COUNT(*) FILTER(WHERE vv>0) ncand,
               COALESCE(SUM(vv) FILTER(WHERE pty='D'),0) d,
               COALESCE(SUM(vv) FILTER(WHERE pty='R'),0) r
        FROM v GROUP BY 1
    """).fetchall()


def classify(rows):
    cats = {"uncontested": 0, "same_party": 0, "Tossup": 0, "Lean": 0, "Likely": 0, "Solid": 0}
    d_safe = r_safe = 0
    for _, ncand, d, r in rows:
        d, r = float(d), float(r)
        cat = ("uncontested" if ncand <= 1 else "same_party" if (d == 0 or r == 0)
               else band(abs(d - r) / (d + r) * 100))
        cats[cat] += 1
        if cat in ("uncontested", "same_party", "Likely", "Solid"):
            d_safe += int(d >= r)
            r_safe += int(d < r)
    n = sum(cats.values())
    noncomp = cats["uncontested"] + cats["same_party"] + cats["Likely"] + cats["Solid"]
    return cats, n, noncomp, d_safe, r_safe


def main():
    wa = duckdb.connect(f"{D}/wa_statewide.duckdb", read_only=True)

    print("[WA] OBSERVED non-competitive % of partisan leg+cong seats, by even-year general")
    print("  (paper: 2016 90.7 / 2018 75.0 / 2020 84.1 / 2022 87.1 / 2024 85.0)")
    off = " OR ".join(f"r.office='{o}'" for o in WA_OFFICES)
    print(f"  {'year':>5} {'seats':>6} {'uncont':>7} {'same':>5} {'no-choice':>10} {'comp':>5} {'non-comp%':>10}")
    for y in (2016, 2018, 2020, 2022, 2024):
        cats, n, nc, ds, rs = classify(seats(wa, f"{y}-11-05", off))
        nochoice = cats["uncontested"] + cats["same_party"]
        comp = cats["Tossup"] + cats["Lean"]
        print(f"  {y:>5} {n:>6} {cats['uncontested']:>7} {cats['same_party']:>5} "
              f"{nochoice:>10} {comp:>5} {100.0*nc/n:>9.1f}%")

    cats, n, nc, ds, rs = classify(seats(wa, "2024-11-05", off))
    print(f"\n[WA 2024 detail]  (paper: 133 seats, 46 no-choice, 20 competitive, 85.0%, safe 69 D / 44 R)")
    print(f"  {n} seats | {cats['uncontested']+cats['same_party']} no-choice "
          f"({cats['uncontested']} uncontested + {cats['same_party']} same-party) | "
          f"{cats['Tossup']+cats['Lean']} competitive | {100.0*nc/n:.1f}% non-comp | "
          f"safe {ds} D / {rs} R")
    wa.close()

    print("\n[FOUR-STATE] lower-chamber non-competitive %  (paper: WA 88.8 / NY 88.6 / TX 94.0 / ID 92.9)")
    print(f"  {'state':>14} {'seats':>6} {'no-choice':>10} {'comp':>5} {'non-comp%':>10} {'safe D/R':>10}")
    specs = [
        ("WA House", "wa_statewide", "2024-11-05",
         "r.office='State Representative Pos. 1' OR r.office='State Representative Pos. 2'", None),
        ("NY Assembly", "ny_statewide", "2022-11-08", "r.office ILIKE '%ASSEMBLY DISTRICT%'", None),
        ("ID House", "id_statewide", "2024-11-05", "r.office ILIKE 'REPRESENTATIVE DISTRICT%'", None),
        ("TX House", "tx_statewide", "2024-11-05", "r.office ILIKE '%HOUSE DISTRICT%'", 150),
    ]
    for label, db, date, off_sql, backfill_to in specs:
        con = duckdb.connect(f"{D}/{db}.duckdb", read_only=True)
        cats, n, nc, ds, rs = classify(seats(con, date, off_sql))
        con.close()
        note = ""
        if backfill_to:  # TX: absent seats are uncontested-by-construction -> no-major-choice
            absent = backfill_to - n
            nc += absent
            cats["uncontested"] += absent
            n = backfill_to
            note = f"  (+{absent} uncontested backfill -> 150; D/R split needs r206, not shown)"
        nochoice = cats["uncontested"] + cats["same_party"]
        comp = cats["Tossup"] + cats["Lean"]
        print(f"  {label:>14} {n:>6} {nochoice:>10} {comp:>5} {100.0*nc/n:>9.1f}% "
              f"{str(ds)+'/'+str(rs):>10}{note}")


if __name__ == "__main__":
    main()
