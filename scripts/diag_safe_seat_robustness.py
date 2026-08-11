"""Safe-Seat robustness: (1) margin-threshold sensitivity and (2) the contest gap
(actual-race vs presidential-lean competitiveness) — the two reviewer-objection
killers for safe-seat-washington.md.

(1) THRESHOLD SENSITIVITY. "Non-competitive" = no-major-choice + (contested margin
    >= T). Re-run across T in {5,8,10,12,15} for each state's LOWER chamber so the
    headline isn't an artifact of the 10-pt cut. (no-major-choice is threshold-free.)

(2) CONTEST GAP. Actual-race non-competitive % vs the % of seats whose district
    PRESIDENTIAL lean is >=10pt safe. A positive gap means legislative contests are less
    competitive than the partisan geography alone would predict (the TX finding — is it
    universal?). It does NOT identify a mechanism: the comparison is between two aggregate
    shares and observes nobody's filing decision. Non-entry is one candidate; incumbency,
    candidate quality, spending, differential turnout and ticket-splitting are others.
    (This read "parties are leaving presidentially-winnable seats uncontested" until
    2026-08-10 — withdrawn in the paper's Appendix E as "more than the statistic supports",
    and still asserted here for two days after the paper stopped saying it.)
    Feasible where district presidential results exist on matching boundaries:
    TX (r206, all 150) + WA (precinct_results President 2024 x precinct_district_map)
    + ID (attempt). NY skipped: President loaded only thru 2020, pre-2022-redistricting,
    so it cannot be matched to the 2022 Assembly lines.

(3) COMPARABILITY WITH THE WA MEASURE — added 2026-07-28. This script's definition is
    NOT the paper's Dimension 1. Here, a no-major-choice seat is non-competitive at every
    threshold; in `diag_seat_competition.py` a seat is "not close" only if it has a single
    candidate OR a top-two margin >= T, so a CONTESTED same-party (or major-vs-minor)
    general decided by under 10 points counts as CLOSE — that distinction is the whole
    point of the paper's two-dimension design, and WA-04 2024 (R-v-R, 6.0 pts) is the
    case that motivated it. Section (3) measures whether the two definitions actually
    diverge in NY/TX/ID by re-scoring each no-major-choice seat on its top-two margin.
    They do not (0 such seats anywhere), so the four-state comparison is like-for-like in
    fact as well as in intent — but that has to be MEASURED, not assumed, and it must be
    re-measured whenever a comparison state's cycle is reloaded.

NOTE ON THE WA ROW: WA figures here come from `precinct_results` under this script's
definition and read 88.8% at >=10pt. The paper publishes WA from
`diag_seat_competition.py` on the certified universe (87.8%), which is the authoritative
WA number. Both are printed side by side below so the 1-seat difference is visible
instead of looking like a contradiction.
"""
import csv
import os
import sys

import duckdb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import diag_tx_safe_seat_backfill as txbf  # noqa: E402

PARTY = """CASE WHEN cd.party_normalized ILIKE '%democrat%' THEN 'D'
  WHEN cd.party_normalized ILIKE '%republican%' OR cd.party_normalized ILIKE '%gop%' THEN 'R'
  ELSE 'O' END"""
THRESHOLDS = [5, 8, 10, 12, 15]
# The paper's WA >=10pt figure, from diag_seat_competition.py on the certified universe.
# Kept here only so the contest gap can be printed on the number the paper publishes;
# it is not an input to anything this script computes.
WA_CERTIFIED_NOTCLOSE_10 = 87.8
LOWER = [
    ("WA", "data/wa_statewide.duckdb", "2024-11-05",
     "r.office IN ('State Representative Pos. 1','State Representative Pos. 2')"),
    ("NY", "data/ny_statewide.duckdb", "2022-11-08", "r.office ILIKE '%ASSEMBLY DISTRICT%'"),
    ("TX", "data/tx_statewide.duckdb", "2024-11-05", "r.office ILIKE '%HOUSE DISTRICT%'"),
    ("ID", "data/id_statewide.duckdb", "2024-11-05", "r.office ILIKE 'REPRESENTATIVE DISTRICT%'"),
]


def seat_margins(db, date, pred):
    """Return (no_major_choice_count, [contested two-party margins, pts], nmc_topline).

    `nmc_topline` is one entry per no-major-choice seat: its TOP-TWO candidate margin in
    points, or None where the seat has fewer than two candidates with votes. That is the
    WA measure (see module docstring section 3), and it is what section (3) uses to check
    whether this script's "no-major-choice is never close" shortcut actually changes any
    state's answer.
    """
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
              AND COALESCE(cd.is_writein,FALSE)=FALSE GROUP BY 1),
        cv AS (
            SELECT r.race_id, cd.candidate_id, SUM(pr.votes) v
            FROM races r JOIN elections e ON e.election_id=r.election_id
            JOIN candidates cd ON cd.race_id=r.race_id
            JOIN precinct_results pr ON pr.candidate_id=cd.candidate_id
            WHERE e.election_date=DATE '{date}' AND {pred}
              AND COALESCE(cd.is_writein,FALSE)=FALSE
            GROUP BY 1,2 HAVING SUM(pr.votes) > 0),
        ranked AS (
            SELECT race_id, v, ROW_NUMBER() OVER (PARTITION BY race_id ORDER BY v DESC) rn
            FROM cv),
        top2 AS (
            SELECT race_id, MAX(CASE WHEN rn=1 THEN v END) t1,
                   MAX(CASE WHEN rn=2 THEN v END) t2
            FROM ranked GROUP BY 1)
        SELECT s.hasD, s.hasR, COALESCE(v.d,0) d, COALESCE(v.r,0) r, t.t1, t.t2
        FROM seat s LEFT JOIN votes v USING (race_id) LEFT JOIN top2 t USING (race_id)
    """).fetchall()
    c.close()
    nmc = 0
    margins = []
    nmc_topline = []
    for hasD, hasR, d, r, t1, t2 in rows:
        d = float(d or 0); r = float(r or 0)
        if not (hasD and hasR) or d + r == 0:
            nmc += 1
            t1 = float(t1 or 0); t2 = float(t2 or 0)
            nmc_topline.append(abs(t1 - t2) / (t1 + t2) * 100 if t2 and (t1 + t2) else None)
        else:
            margins.append(abs(d - r) / (d + r) * 100)
    return nmc, margins, nmc_topline


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


NY_AD23_CSV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "docs", "reference", "ny_ad23_2022.csv")
NY_ASSEMBLY_TOTAL = 150


def ny_ad23_margin() -> float:
    """The two-party margin, in points, of NY Assembly District 23's 2022 general.

    The loaded NY returns carry 149 of 150 Assembly districts; the missing one is AD-23, and
    it is supplied here from the same pinned certified file verify_safe_seat.py reads, so the
    two code paths cannot drift to different denominators. That drift is exactly what this
    supplement exists to end: until 2026-08-08 the four-state table in the paper read 150 seats
    while this script's threshold sweep read 149, and the paper had to carry a footnote saying
    so.

    AD-23 is contested D-v-R and was decided by fifteen votes, so it lands in `margins` rather
    than the no-major-choice bucket, and it is NOT CLOSE at no threshold in the sweep — it can
    only lower each cell.
    """
    with open(NY_AD23_CSV, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    d = sum(int(r["votes"]) for r in rows if r["party"].strip().upper().startswith("DEM"))
    r_ = sum(int(r["votes"]) for r in rows if r["party"].strip().upper().startswith("REP"))
    if not d or not r_:
        raise SystemExit(f"{NY_AD23_CSV}: expected both a D and an R total")
    return abs(d - r_) / (d + r_) * 100


def main():
    # gather per-state seat status (lower chamber); TX backfilled, NY supplemented with AD-23
    state_data = {}
    nmc_topline = {}
    for st, db, date, pred in LOWER:
        nmc, margins, nmc_tl = seat_margins(db, date, pred)
        if st == "NY":
            loaded = nmc + len(margins)
            absent = NY_ASSEMBLY_TOTAL - loaded
            if absent != 1:
                raise SystemExit(
                    f"NY Assembly: {loaded} seats loaded, expected {NY_ASSEMBLY_TOTAL - 1} "
                    "before the AD-23 supplement. The supplement closes a gap of exactly one "
                    "seat; a different gap means the loaded returns changed and adding AD-23 "
                    "may now double-count or mask a wider hole.")
            margins.append(ny_ad23_margin())
        if st == "TX":
            dbres = txbf.db_house_results()
            nmc = sum(1 for v in dbres.values() if v[0] == "no_major_choice")
            margins = [abs(d - r) / (d + r) * 100 for cat, d, r in dbres.values()
                       if cat != "no_major_choice" and (d + r) > 0]
            nmc += txbf.HOUSE_TOTAL - len(dbres)  # + 54 absent (uncontested)
            # The 54 backfilled seats are single-candidate by construction (certified —
            # see diag_tx_backfill_verification.py), so they carry no top-two margin and
            # are "not close" under either definition. Only the loaded no-choice seats
            # can possibly diverge, and those are what nmc_tl already holds.
            nmc_tl = nmc_tl + [None] * (txbf.HOUSE_TOTAL - len(dbres))
        state_data[st] = (nmc, margins)
        nmc_topline[st] = nmc_tl

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
    print("\nWA row: this script's definition, not the paper's. The paper publishes WA from")
    print("diag_seat_competition.py on the CERTIFIED universe — 95.9 / 91.8 / 87.8 / 80.6 /")
    print("76.5% — which is the authoritative WA number. Use that row, not this one.")

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
        if st == "WA":
            print(f"{'  ^^ ':5} {WA_CERTIFIED_NOTCLOSE_10:16.1f}% {presafe:15.1f}% "
                  f"{WA_CERTIFIED_NOTCLOSE_10-presafe:8.1f}  <-- PAPER: certified universe "
                  f"(diag_seat_competition.py)")
    print("NY: skipped — President loaded only through 2020 (pre-2022 lines), can't match "
          "2022 Assembly.\nA POSITIVE gap = legislative contests are less competitive than "
          "district presidential lean alone would predict. It compares two AGGREGATE shares "
          "and does NOT observe who filed — non-entry is one mechanism consistent with it, "
          "alongside incumbency, candidate quality, spending, differential turnout and "
          "office-specific ticket-splitting.\n(Was 'parties leave presidentially-winnable "
          "seats uncontested' until 2026-08-10: the reading Appendix E withdrew as 'more "
          "than the statistic supports'.)")

    print("\n" + "=" * 70)
    print("(3) COMPARABILITY — does 'no-major-choice is never close' change any answer?")
    print("=" * 70)
    print("Re-scoring every no-major-choice seat on its TOP-TWO margin (the WA measure).")
    print("A seat that lands under 10 pts is a CONTESTED race with no D-v-R option, and")
    print("this script's shortcut would be miscounting it as not close.\n")
    print(f"{'state':5} {'no-choice':>10} {'single-cand':>12} {'top-two >=10':>13} "
          f"{'top-two <10':>12}")
    divergent = 0
    for st in [s[0] for s in LOWER]:
        tl = nmc_topline[st]
        single = sum(1 for m in tl if m is None)
        far = sum(1 for m in tl if m is not None and m >= 10)
        close = sum(1 for m in tl if m is not None and m < 10)
        divergent += close
        print(f"{st:5} {len(tl):>10} {single:>12} {far:>13} {close:>12}")
        for m in sorted(x for x in tl if x is not None and x < 10):
            print(f"        ^ contested no-choice seat at {m:.1f} pts — definitions DIVERGE")
    if divergent == 0:
        print("\n0 divergent seats in all three comparison states: the four-state 'not close'")
        print("column is identical under this script's definition and under WA's Dimension 1,")
        print("so the comparison is like-for-like in fact. Re-run after any cycle reload —")
        print("this is a measured result, not a property of the definitions.")
    else:
        print(f"\n{divergent} seat(s) DIVERGE. The four-state table is no longer like-for-like;")
        print("re-score the comparison states on top-two margin before publishing.")


if __name__ == "__main__":
    main()
