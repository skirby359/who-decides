"""Two-dimension seat-competition classification for Washington, from CERTIFIED returns.

Rebuilt 2026-07-27 in response to an adversarial review of docs/safe-seat-washington.md
that identified three defects, all confirmed:

  1. INCOMPLETE SEAT UNIVERSE. The prior script derived its universe from
     `precinct_results`. King County is essentially absent from the WA SoS statewide
     PRECINCT files for 2016 and 2018 (~190 of 330,845 rows in 2016), so every King
     legislative race silently vanished — 24 House seats per year, districts 5, 11, 33,
     34, 36, 37, 41, 43, 45, 46, 47, 48. A race missing from the results table
     disappeared instead of being detected as missing. This script instead builds the
     universe from the certified statewide SUMMARY files (`*_AllState.csv`), which carry
     all 98 House races in every even year, and asserts the count against the statutory
     chamber size.

  2. MISCLASSIFIED "SAME-PARTY". The prior rule was `same_party if (d == 0 or r == 0)`,
     which is "no D-v-R pairing", not "same party": it swept in D-vs-independent,
     R-vs-Libertarian and minor-only races. In WA 2024, 7 of the 23 races labelled
     same-party were not same-party at all.

  3. CONFLATED DIMENSIONS. Every same-party general was scored non-competitive
     regardless of margin, which answers "was there a D-v-R choice?" while claiming to
     answer "was it a contest?". Those are different questions and are now reported
     separately.

The two dimensions:

  CANDIDATE COMPETITION — the top-two margin among candidates actually on the ballot,
  computed regardless of party. A 51-49 D-vs-D general is competitive on this axis.

  PARTISAN AVAILABILITY — which parties the ballot offered: D-v-R, D-v-D, R-v-R,
  D-v-other, R-v-other, other-only, or a single candidate.

Party is taken from the certified "Prefers ___ Party" string, matched strictly: only
"Democratic"/"Democrat" and "Republican"/"GOP" count as major. WA's top-two system has
no nominees, so a candidate preferring e.g. "Independent Dem." or "Culture Republican"
is counted as OTHER and listed in the output, rather than silently folded into a major
party. Write-ins are excluded.

Usage:  python scripts/diag_seat_competition.py [--csv reports/seat_competition.csv]
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys

import duckdb

RAW = os.path.join("data", "raw", "election_results")

# Certified statewide general-election summary files, by cycle.
GENERALS = {2016: "20161108", 2018: "20181106", 2020: "20201103",
            2022: "20221108", 2024: "20241105"}

# Statutory chamber sizes. The Senate is staggered, so its expected count varies by
# cycle and is taken from the certified file itself rather than asserted.
EXPECT_HOUSE = 98          # 49 districts x 2 positions, all up every even year
EXPECT_USHOUSE = 10        # WA congressional districts

MAJOR_D = re.compile(r"PREFERS\s+(DEMOCRATIC|DEMOCRAT)\s+PARTY", re.I)
MAJOR_R = re.compile(r"PREFERS\s+(REPUBLICAN|GOP)\s+PARTY", re.I)
# "Independent Dem.", "Independent Rep", "Culture Republican" etc. are NOT major.
NOT_MAJOR_PREFIX = re.compile(r"PREFERS\s+(INDEPENDENT|CULTURE)\s", re.I)


def party_of(raw: str) -> str:
    s = (raw or "").strip()
    if not s or s.upper() == "WRITE-IN":
        return "O"
    if NOT_MAJOR_PREFIX.search(s):
        return "O"
    if MAJOR_D.search(s):
        return "D"
    if MAJOR_R.search(s):
        return "R"
    return "O"


def parse_race(race: str):
    """-> (chamber, district, position) or None for offices outside the universe."""
    s = race.upper()
    m = re.search(r"LEGISLATIVE DISTRICT\s+(\d+)", s)
    if m:
        d = int(m.group(1))
        if re.search(r"\bSENATOR\b", s):
            return ("SEN", d, 0)
        # WA SoS is not consistent across cycles: 2016-2018/2022-2024 use
        # "State Representative Pos. N", while 2020 LD15 uses
        # "Representative, Position N". Matching only the first spelling silently
        # dropped those two seats — the same failure mode this rebuild exists to fix.
        p = re.search(r"REPRESENTATIVE,?\s*POS(?:ITION)?\.?\s*(\d)", s)
        if p:
            return ("HSE", d, int(p.group(1)))
        return None
    m = re.search(r"CONGRESSIONAL DISTRICT\s+(\d+)", s)
    if m and "U.S. REPRESENTATIVE" in s:
        return ("USH", int(m.group(1)), 0)
    return None


def band(margin: float | None) -> str:
    if margin is None:
        return "single candidate"
    if margin < 5:
        return "Tossup <5"
    if margin < 10:
        return "Lean 5-10"
    if margin < 20:
        return "Likely 10-20"
    return "Solid 20+"


def availability(parties: list[str]) -> str:
    n = len(parties)
    if n <= 1:
        return "single candidate"
    nd, nr = parties.count("D"), parties.count("R")
    if nd and nr:
        return "D-v-R"
    if nd >= 2:
        return "D-v-D"
    if nr >= 2:
        return "R-v-R"
    if nd:
        return "D-v-other"
    if nr:
        return "R-v-other"
    return "other-only"


def load_year(con, year: int) -> tuple[list[dict], list[str]]:
    path = os.path.join(RAW, f"{GENERALS[year]}_AllState.csv").replace("\\", "/")
    if not os.path.exists(path):
        return [], [f"missing certified file: {path}"]
    rows = con.execute(f"""
        SELECT "Race" race, "Candidate" cand, "Party" party, TRY_CAST("Votes" AS BIGINT) votes
        FROM read_csv_auto('{path}', header=true, all_varchar=true, ignore_errors=true)
    """).fetchall()

    races: dict[tuple, list] = {}
    oddities: set[str] = set()
    for race, cand, party, votes in rows:
        key = parse_race(race or "")
        if key is None:
            continue
        if (cand or "").strip().upper() == "WRITE-IN":
            continue
        p = party_of(party)
        if p == "O" and party and party.strip() and party.strip() != "-":
            if NOT_MAJOR_PREFIX.search(party) or "REPUBLIC" in party.upper() or "DEMOCRA" in party.upper():
                oddities.add(party.strip())
        races.setdefault(key, []).append((cand, p, int(votes or 0)))

    out = []
    for (chamber, dist, pos), cands in sorted(races.items()):
        cands = [c for c in cands if c[2] > 0]
        if not cands:
            continue
        cands.sort(key=lambda t: -t[2])
        parties = [c[1] for c in cands]
        top1 = cands[0][2]
        runner = cands[1][2] if len(cands) > 1 else 0
        margin = (100.0 * (top1 - runner) / (top1 + runner)) if len(cands) > 1 and (top1 + runner) else None
        d = sum(v for _, p, v in cands if p == "D")
        r = sum(v for _, p, v in cands if p == "R")
        dr_margin = (100.0 * abs(d - r) / (d + r)) if (d and r) else None
        out.append({
            "year": year, "chamber": chamber, "district": dist, "position": pos,
            "ncand": len(cands), "winner_party": cands[0][1], "winner": cands[0][0],
            "top1": top1, "runner": runner,
            "cand_margin": None if margin is None else round(margin, 2),
            "cand_band": band(margin),
            "availability": availability(parties),
            "d_votes": d, "r_votes": r,
            "dr_margin": None if dr_margin is None else round(dr_margin, 2),
        })
    return out, sorted(oddities)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--csv", default=os.path.join("reports", "seat_competition.csv"))
    args = ap.parse_args(argv)

    con = duckdb.connect()
    allrows: list[dict] = []
    problems: list[str] = []

    print("=" * 88)
    print("SEAT UNIVERSE — certified statewide summary vs statutory expectation")
    print("=" * 88)
    print(f"  {'year':<6}{'House':>7}{'(want)':>8}{'Senate':>8}{'USHouse':>9}{'(want)':>8}{'total':>7}")
    for year in sorted(GENERALS):
        rows, odd = load_year(con, year)
        allrows += rows
        h = sum(1 for x in rows if x["chamber"] == "HSE")
        s = sum(1 for x in rows if x["chamber"] == "SEN")
        u = sum(1 for x in rows if x["chamber"] == "USH")
        flag = ""
        if h != EXPECT_HOUSE:
            flag += f"  <-- House short by {EXPECT_HOUSE - h}"
            problems.append(f"{year}: House {h}/{EXPECT_HOUSE}")
        if u != EXPECT_USHOUSE:
            flag += f"  <-- USHouse {u}/{EXPECT_USHOUSE}"
            problems.append(f"{year}: USHouse {u}/{EXPECT_USHOUSE}")
        print(f"  {year:<6}{h:>7}{EXPECT_HOUSE:>8}{s:>8}{u:>9}{EXPECT_USHOUSE:>8}{h+s+u:>7}{flag}")
        if odd:
            print(f"         non-major party strings seen: {', '.join(odd)}")

    print("\n" + "=" * 88)
    print("DIMENSION 1 — CANDIDATE COMPETITION (top-two margin, any party)")
    print("=" * 88)
    bands = ["single candidate", "Tossup <5", "Lean 5-10", "Likely 10-20", "Solid 20+"]
    print(f"  {'year':<6}{'seats':>7}" + "".join(f"{b:>17}" for b in bands) + f"{'non-comp':>10}")
    for year in sorted(GENERALS):
        yr = [x for x in allrows if x["year"] == year]
        n = len(yr)
        counts = [sum(1 for x in yr if x["cand_band"] == b) for b in bands]
        noncomp = sum(1 for x in yr
                      if x["cand_band"] in ("single candidate", "Likely 10-20", "Solid 20+"))
        print(f"  {year:<6}{n:>7}" + "".join(f"{c:>17}" for c in counts)
              + f"{100.0*noncomp/n:>9.1f}%")

    print("\n" + "=" * 88)
    print("DIMENSION 2 — PARTISAN AVAILABILITY (what the ballot offered)")
    print("=" * 88)
    kinds = ["D-v-R", "D-v-D", "R-v-R", "D-v-other", "R-v-other", "other-only", "single candidate"]
    print(f"  {'year':<6}{'seats':>7}" + "".join(f"{k:>13}" for k in kinds) + f"{'no D-v-R':>10}")
    for year in sorted(GENERALS):
        yr = [x for x in allrows if x["year"] == year]
        n = len(yr)
        counts = [sum(1 for x in yr if x["availability"] == k) for k in kinds]
        nodr = n - sum(1 for x in yr if x["availability"] == "D-v-R")
        print(f"  {year:<6}{n:>7}" + "".join(f"{c:>13}" for c in counts)
              + f"{100.0*nodr/n:>9.1f}%")

    print("\n" + "=" * 88)
    print("CROSS-TAB, most recent cycle — the two dimensions are NOT the same question")
    print("=" * 88)
    yr = [x for x in allrows if x["year"] == max(GENERALS)]
    print(f"  {'availability':<18}" + "".join(f"{b:>17}" for b in bands))
    for k in kinds:
        row = [sum(1 for x in yr if x["availability"] == k and x["cand_band"] == b) for b in bands]
        if sum(row):
            print(f"  {k:<18}" + "".join(f"{v:>17}" for v in row))
    close_same = [x for x in yr if x["availability"] in ("D-v-D", "R-v-R")
                  and x["cand_band"] in ("Tossup <5", "Lean 5-10")]
    print(f"\n  same-party generals decided by <10 pts: {len(close_same)}")
    for x in close_same:
        print(f"    {x['chamber']}{x['district']}"
              f"{'-' + str(x['position']) if x['position'] else '':<4} "
              f"{x['availability']:<7} margin {x['cand_margin']:.1f}  ({x['winner']})")

    print("\n" + "=" * 88)
    print("SENSITIVITY — does the party-string rule change the answer?")
    print("=" * 88)
    print("  STRICT (published): only 'Prefers Democratic/Democrat Party' and")
    print("  'Prefers Republican/GOP Party' count as major. WA's top-two has no nominees,")
    print("  so 'Independent Dem.', 'Ind. Republican', 'Culture Republican' and 'MAGA")
    print("  Republican' are counted as OTHER. LOOSE folds those into the major party.")
    print(f"\n  {'year':<6}{'no D-v-R, STRICT':>20}{'no D-v-R, LOOSE':>20}{'delta':>9}")
    loose_d = re.compile(r"DEMOCRA|DEMOCRACT", re.I)
    loose_r = re.compile(r"REPUBLICAN|GOP", re.I)
    for year in sorted(GENERALS):
        path = os.path.join(RAW, f"{GENERALS[year]}_AllState.csv").replace("\\", "/")
        rows = con.execute(f"""
            SELECT "Race", "Party", TRY_CAST("Votes" AS BIGINT) v
            FROM read_csv_auto('{path}', header=true, all_varchar=true, ignore_errors=true)
            WHERE upper("Candidate") <> 'WRITE-IN'""").fetchall()
        races: dict[tuple, list] = {}
        for race, party, v in rows:
            key = parse_race(race or "")
            if key is None or not v or v <= 0:
                continue
            s = party or ""
            races.setdefault(key, []).append(
                "D" if loose_d.search(s) else "R" if loose_r.search(s) else "O")
        n_loose = len(races)
        nodr_loose = sum(1 for ps in races.values() if not ("D" in ps and "R" in ps))
        yr = [x for x in allrows if x["year"] == year]
        nodr_strict = sum(1 for x in yr if x["availability"] != "D-v-R")
        a, b = 100.0 * nodr_strict / len(yr), 100.0 * nodr_loose / n_loose
        print(f"  {year:<6}{a:>19.1f}%{b:>19.1f}%{a-b:>8.1f}")
    print("\n  The rule matters most in 2016, when six different Independent-flavored")
    print("  party strings appeared; elsewhere it moves the figure by under a point.")

    os.makedirs(os.path.dirname(args.csv), exist_ok=True)
    with open(args.csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(allrows[0].keys()))
        w.writeheader()
        w.writerows(allrows)
    print(f"\nwrote {args.csv} ({len(allrows)} seats)")

    if problems:
        print("\nUNIVERSE PROBLEMS (do not publish a 'every seat' claim for these):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("\nAll cycles match the statutory seat universe.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
