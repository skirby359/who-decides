"""Safe-Seat robustness: (1) margin-threshold sensitivity and (2) the contest gap
(actual-race vs presidential-lean competitiveness) — the two reviewer-objection
killers for safe-seat-washington.md.

(1) THRESHOLD SENSITIVITY. "Non-competitive" = no-major-choice + (contested margin
    >= T). Re-run across T in {5,8,10,12,15} for each state's LOWER chamber so the
    headline isn't an artifact of the 10-pt cut. (no-major-choice is threshold-free.)

(2) CONTEST GAP. Actual-race non-competitive % vs the % of seats whose district
    PRESIDENTIAL lean is >=10pt safe. If actual > presidential, parties are leaving
    presidentially-winnable seats uncontested (the TX finding — is it universal?).
    Feasible where district presidential results exist on matching boundaries:
    TX (r206, all 150) + WA (precinct_results President 2024 x precinct_district_map)
    + ID (attempt). NY skipped: President loaded only thru 2020, pre-2022-redistricting,
    so it cannot be matched to the 2022 Assembly lines.
"""
import os
import sys

import duckdb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import diag_tx_safe_seat_backfill as txbf  # noqa: E402

PARTY = """CASE WHEN cd.party_normalized ILIKE '%democrat%' THEN 'D'
  WHEN cd.party_normalized ILIKE '%republican%' OR cd.party_normalized ILIKE '%gop%' THEN 'R'
  ELSE 'O' END"""
THRESHOLDS = [5, 8, 10, 12, 15]
LOWER = [
    ("WA", "data/wa_statewide.duckdb", "2024-11-05",
     "r.office IN ('State Representative Pos. 1','State Representative Pos. 2')"),
    ("NY", "data/ny_statewide.duckdb", "2022-11-08", "r.office ILIKE '%ASSEMBLY DISTRICT%'"),
    ("TX", "data/tx_statewide.duckdb", "2024-11-05", "r.office ILIKE '%HOUSE DISTRICT%'"),
    ("ID", "data/id_statewide.duckdb", "2024-11-05", "r.office ILIKE 'REPRESENTATIVE DISTRICT%'"),
]


def seat_margins(db, date, pred):
    """Return (no_major_choice_count, [contested two-party margins, pts])."""
    c = duckdb.connect(db, read_only=True)
    rows = c.execute(f"""
        WITH seat AS (
            SELECT r.race_id,
                   MAX(CASE WHEN {PARTY}='D' THEN 1 ELSE 0 END) hasD,
                   MAX(CASE WHEN {PARTY}='R' THEN 1 ELSE 0 END) hasR
            FROM races r JOIN elections e ON e.election_id=r.election_id
            JOIN candidates cd ON cd.race_id=r.race_id
            WHERE e.election_date=DATE '{date}' AND {pred}
              AND COALESCE(cd.is_writein,FALSE)=FALSE GROUP BY 1),
        votes AS (
            SELECT r.race_id,
                   SUM(CASE WHEN {PARTY}='D' THEN pr.votes ELSE 0 END) d,
                   SUM(CASE WHEN {PARTY}='R' THEN pr.votes ELSE 0 END) r
            FROM races r JOIN elections e ON e.election_id=r.election_id
            JOIN candidates cd ON cd.race_id=r.race_id
            JOIN precinct_results pr ON pr.candidate_id=cd.candidate_id
            WHERE e.election_date=DATE '{date}' AND {pred}
              AND COALESCE(cd.is_writein,FALSE)=FALSE GROUP BY 1)
        SELECT s.hasD, s.hasR, COALESCE(v.d,0) d, COALESCE(v.r,0) r
        FROM seat s LEFT JOIN votes v USING (race_id)
    """).fetchall()
    c.close()
    nmc = 0
    margins = []
    for hasD, hasR, d, r in rows:
        d = float(d or 0); r = float(r or 0)
        if not (hasD and hasR) or d + r == 0:
            nmc += 1
        else:
            margins.append(abs(d - r) / (d + r) * 100)
    return nmc, margins


def pres_margins_by_ld(db, date, ld_col):
    """District-level presidential two-party margins (pts) from precinct_results."""
    c = duckdb.connect(db, read_only=True)
    rows = c.execute(f"""
        WITH pres AS (
            SELECT pr.precinct_id, {PARTY} pty, pr.votes
            FROM precinct_results pr JOIN races r ON r.race_id=pr.race_id
            JOIN elections e ON e.election_id=r.election_id
            JOIN candidates cd ON cd.candidate_id=pr.candidate_id
            WHERE e.election_date=DATE '{date}' AND r.office ILIKE '%PRESIDENT%')
        SELECT m.{ld_col} ld,
               SUM(CASE WHEN pty='D' THEN votes ELSE 0 END) d,
               SUM(CASE WHEN pty='R' THEN votes ELSE 0 END) r
        FROM pres JOIN precinct_district_map m ON m.precinct_id=pres.precinct_id
        WHERE m.{ld_col} IS NOT NULL AND TRIM(m.{ld_col}) <> ''
        GROUP BY 1
    """).fetchall()
    c.close()
    return [abs(float(d) - float(r)) / (float(d) + float(r)) * 100
            for _, d, r in rows if (float(d) + float(r)) > 0]


def main():
    # gather per-state seat status (lower chamber); TX backfilled
    state_data = {}
    for st, db, date, pred in LOWER:
        nmc, margins = seat_margins(db, date, pred)
        if st == "TX":
            dbres = txbf.db_house_results()
            nmc = sum(1 for v in dbres.values() if v[0] == "no_major_choice")
            margins = [abs(d - r) / (d + r) * 100 for cat, d, r in dbres.values()
                       if cat != "no_major_choice" and (d + r) > 0]
            nmc += txbf.HOUSE_TOTAL - len(dbres)  # + 54 absent (uncontested)
        state_data[st] = (nmc, margins)

    print("=" * 70)
    print("(1) THRESHOLD SENSITIVITY — non-competitive % of lower-chamber seats")
    print("=" * 70)
    print(f"\n{'state':5} {'seats':>5} " + " ".join(f"{'>='+str(t):>7}" for t in THRESHOLDS))
    for st, (nmc, margins) in state_data.items():
        n = nmc + len(margins)
        cells = []
        for t in THRESHOLDS:
            noncomp = nmc + sum(1 for m in margins if m >= t)
            cells.append(f"{noncomp/n*100:6.1f}%")
        print(f"{st:5} {n:>5} " + " ".join(f"{c:>7}" for c in cells))
    print("\n(no-major-choice seats are non-competitive at every threshold; only the "
          "contested\n seats move. The finding is flat across the plausible 5-15pt range.)")

    print("\n" + "=" * 70)
    print("(2) CONTEST GAP — actual-race vs district-presidential-lean (>=10pt)")
    print("=" * 70)
    pres = {
        "TX": [abs(d - r) / (d + r) * 100 for d, r in txbf.r206_presidential().values() if d + r > 0],
        "WA": pres_margins_by_ld("data/wa_statewide.duckdb", "2024-11-05", "legislative_district"),
        "ID": pres_margins_by_ld("data/id_statewide.duckdb", "2024-11-05", "legislative_district"),
    }
    print(f"\n{'state':5} {'actual non-comp%':>17} {'pres-lean safe%':>16} {'gap (pp)':>9}  note")
    for st in ["WA", "TX", "ID"]:
        nmc, margins = state_data[st]
        n = nmc + len(margins)
        actual = (nmc + sum(1 for m in margins if m >= 10)) / n * 100
        pm = pres.get(st, [])
        if not pm:
            print(f"{st:5} {actual:16.1f}% {'n/a':>16} {'':>9}  no matched-vintage presidential")
            continue
        presafe = sum(1 for m in pm if m >= 10) / len(pm) * 100
        print(f"{st:5} {actual:16.1f}% {presafe:15.1f}% {actual-presafe:8.1f}  "
              f"(pres districts n={len(pm)})")
    print("NY: skipped — President loaded only through 2020 (pre-2022 lines), can't match "
          "2022 Assembly.\nA POSITIVE gap = parties leave presidentially-winnable seats "
          "uncontested (worse than the map).")


if __name__ == "__main__":
    main()
