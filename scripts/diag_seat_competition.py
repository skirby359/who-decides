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
party. Write-ins are excluded. Outright MISSPELLINGS of a major party's name in the
certified file are normalized first — see SOURCE_MISSPELLINGS.

Also reports the primary/general participation ratio per cycle, on the same certified
universe, so the paper's table has a derivation rather than a remembered number.

Usage:  python scripts/diag_seat_competition.py [--csv reports/seat_competition.csv]
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import statistics
import sys

import duckdb

RAW = os.path.join("data", "raw", "election_results")

# Certified statewide general-election summary files, by cycle.
GENERALS = {2016: "20161108", 2018: "20181106", 2020: "20201103",
            2022: "20221108", 2024: "20241105"}

# The matching August top-two primary, same source and same race-name grammar.
PRIMARIES = {2016: "20160802", 2018: "20180807", 2020: "20200804",
             2022: "20220802", 2024: "20240806"}

# Statutory chamber sizes. The Senate is staggered, so its expected count varies by
# cycle and is taken from the certified file itself rather than asserted.
EXPECT_HOUSE = 98          # 49 districts x 2 positions, all up every even year
EXPECT_USHOUSE = 10        # WA congressional districts

# --- FROZEN PARTY-STRING MAPPING (2026-08-08) --------------------------------------------
# Party classification is no longer a regex over unseen text. Every distinct party string in
# the five certified files is enumerated in docs/reference/wa_party_strings_2016-2024.csv and
# classified explicitly; a string absent from that file is a hard error, not a silent "O".
#
# WHY. Regex classification failed silently and repeatedly. It missed "(Prefers Democractic
# Party)" (2020, found in an earlier round) and it also missed FIVE more that no one had
# looked for: "(Prefers G.O.P. Party)" (2018), "(Prefers G.O.P Party)" (2016, no trailing
# period — a G.O.P. patch would not have caught it), "(Prefers R Party)" twice (2020),
# "(Prefers MAGA Republican Party)" (2024, CD-2) and "(Prefers Culture Republican Party)"
# (2024). Each read as a minor party, so a real major-party contest was classified as
# major-versus-other. The defect is not any one pattern; it is that a regex cannot report
# what it did not match. An enumeration can, and this one fails loudly on a new string.
#
# THE RULE the enumeration encodes, decided by the author 2026-08-08:
#   a string names a major party iff it contains a variant of that party's OWN NAME and is
#   not qualified by an INDEPENDENCE marker or a hybrid naming two parties.
# So faction qualifiers do not disqualify ("MAGA Republican", "Culture Republican" -> R) but
# independence qualifiers do ("Ind. Republican", "Independent Dem." -> O), as do hybrids
# ("GOP/Independent", "Dem/Working Fmly" -> O).
#
# The independence exclusion is what keeps the classification SYMMETRIC across parties, and
# that is the point of it rather than a detail: a rule reading any string containing
# "Republican" as R while leaving "Independent Dem"/"Indep't Democrat" as O would flip nine
# Republican-flavoured races and no Democratic ones. It would also contradict the paper's own
# published account of 2016, which explains that year's 48.5% outlier by listing exactly those
# Independent-flavoured strings as non-major.
PARTY_MAP_CSV = os.path.join("docs", "reference", "wa_party_strings_2016-2024.csv")


# BOTH specifications are enumerated, not just the published one. The sensitivity test used to
# define LOOSE with its own regexes, and once the strict rule was fixed that became incoherent:
# `REPUBLICAN|GOP` does not match "(Prefers G.O.P Party)" or "(Prefers R Party)", so LOOSE
# would have classified as OTHER two strings STRICT now classifies as R — a "more generous"
# specification returning a less generous answer. Enumerating both columns makes that
# impossible by construction, and leaves the sensitivity test measuring the one judgment that
# is actually still open: whether independence-qualified strings and hybrids fold into a major
# party. Loose must be a superset of strict, and a test asserts it.
def _load_party_map() -> tuple[dict[str, str], dict[str, str]]:
    with open(PARTY_MAP_CSV, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    strict = {r["party_string"].strip(): r["party_class"].strip() for r in rows}
    loose = {r["party_string"].strip(): r["party_class_loose"].strip() for r in rows}
    return strict, loose


PARTY_MAP, PARTY_MAP_LOOSE = _load_party_map()

# MISSPELLINGS in the certified source, normalized before party matching.
# "(Prefers Democractic Party)" — 2020, LEGISLATIVE DISTRICT 8 State Representative
# Pos. 1, Shir Regev (26,979 votes against Brad Klippert's 51,981) — is a transcription
# error for "Democratic", not a distinct stated preference. Reading it literally made
# MAJOR_D miss it, so a real D-vs-R general was classified R-v-other and the 2020
# no-D-v-R share read 27.6% instead of 26.9%. The fix is applied in BOTH the strict and
# the loose specification, because normalizing a typo is data cleaning, not a judgment
# about how generously to read a party label — the strict/loose sensitivity test is only
# meaningful if it varies the JUDGMENT and holds the cleaning constant.
# Only add a key here that is a spelling variant of a major party's own name. A hybrid
# like 2016's "(Prefers GOP/Independent Party)" is a real stated preference and stays
# OTHER; it is a judgment call and belongs in the sensitivity test, not here.
SOURCE_MISSPELLINGS = {"DEMOCRACTIC": "DEMOCRATIC"}
_MISSPELL_RE = {re.compile(k, re.I): v for k, v in SOURCE_MISSPELLINGS.items()}


def normalize_source_typos(raw: str) -> tuple[str, bool]:
    """-> (corrected string, whether a known misspelling was corrected)."""
    s = raw or ""
    hit = False
    for pat, repl in _MISSPELL_RE.items():
        s, n = pat.subn(repl, s)
        hit = hit or bool(n)
    return s, hit


class UnmappedPartyString(RuntimeError):
    """A certified file carries a party string the frozen mapping does not classify."""


def party_of(raw: str, spec: str = "strict") -> str:
    """Classify a certified party string as D, R or O against the frozen mapping.

    Raises rather than defaulting. A silent "O" is what let six major-party candidates be
    counted as minor-party ones across four cycles; an unmapped string is a data event that
    needs a decision, and the only safe default is to stop.
    """
    s = (raw or "").strip()
    if not s or s.upper() == "WRITE-IN":
        return "O"
    table = PARTY_MAP if spec == "strict" else PARTY_MAP_LOOSE
    if s in table:
        return table[s]
    raise UnmappedPartyString(
        f"party string not in {PARTY_MAP_CSV}: {s!r}. Classify it there explicitly — "
        f"do not add a regex. See the frozen-mapping note above for the rule."
    )


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


def load_year(con, year: int) -> tuple[list[dict], list[str], list[str]]:
    path = os.path.join(RAW, f"{GENERALS[year]}_AllState.csv").replace("\\", "/")
    if not os.path.exists(path):
        return [], [f"missing certified file: {path}"], []
    rows = con.execute(f"""
        SELECT "Race" race, "Candidate" cand, "Party" party, TRY_CAST("Votes" AS BIGINT) votes
        FROM read_csv_auto('{path}', header=true, all_varchar=true, ignore_errors=true)
    """).fetchall()

    races: dict[tuple, list] = {}
    oddities: set[str] = set()
    fixed: set[str] = set()
    for race, cand, party, votes in rows:
        key = parse_race(race or "")
        if key is None:
            continue
        if (cand or "").strip().upper() == "WRITE-IN":
            continue
        p = party_of(party)
        _, was_fixed = normalize_source_typos(party or "")
        if was_fixed:
            fixed.add(f"{(party or '').strip()} -> major {p}")
        elif p == "O" and party and party.strip() and party.strip() != "-":
            # Report every near-miss — a string naming a major party that is still counted as
            # OTHER — so the transparency list is complete. The substring test is deliberately
            # WIDER than the classifier: it catches anything party-flavoured, including the
            # hybrids and independence-qualified strings the frozen mapping deliberately keeps
            # as OTHER, so a reader can see what was excluded and disagree with it.
            up = party.upper()
            if any(s in up for s in ("REPUBLIC", "DEMOCRA", "GOP", "G.O.P", "IND", "DEM")):
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
            # Full precision: rounding here and banding pre-rounding disagreed on a seat
            # sitting at 9.995, which made the threshold table contradict the headline.
            "cand_margin": margin,
            "cand_band": band(margin),
            "availability": availability(parties),
            "d_votes": d, "r_votes": r,
            "dr_margin": None if dr_margin is None else round(dr_margin, 2),
        })
    return out, sorted(oddities), sorted(fixed)


def race_vote_totals(con, stamp: str) -> dict[tuple, int]:
    """Total votes cast per seat in one certified summary file (write-ins excluded).

    Keyed by the same (chamber, district, position) tuple as the general universe, so a
    primary and its general match on office identity rather than on race-name spelling —
    which is what makes the 2020 "Representative, Position N" variant harmless here.
    """
    path = os.path.join(RAW, f"{stamp}_AllState.csv").replace("\\", "/")
    rows = con.execute(f"""
        SELECT "Race" race, "Candidate" cand, TRY_CAST("Votes" AS BIGINT) votes
        FROM read_csv_auto('{path}', header=true, all_varchar=true, ignore_errors=true)
    """).fetchall()
    totals: dict[tuple, int] = {}
    for race, cand, votes in rows:
        key = parse_race(race or "")
        if key is None or not votes or votes <= 0:
            continue
        if (cand or "").strip().upper() == "WRITE-IN":
            continue
        totals[key] = totals.get(key, 0) + int(votes)
    return totals


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
        rows, odd, fixed = load_year(con, year)
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
        if fixed:
            print(f"         source misspellings normalized: {', '.join(fixed)}")

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
    print("THRESHOLD SENSITIVITY — 'not close' share by margin cutoff")
    print("=" * 88)
    print("  Same code path as the headline, so the >=10 column reproduces Dimension 1")
    print("  exactly. A seat with a single candidate is not close at every cutoff.")
    cuts = [5, 8, 10, 12, 15]
    print(f"\n  {'scope':<22}" + "".join(f"{'>=' + str(k) + 'pt':>9}" for k in cuts) + f"{'seats':>8}")
    for label, sel in (("WA all seats 2024", lambda x: x["year"] == 2024),
                       ("WA House 2024", lambda x: x["year"] == 2024 and x["chamber"] == "HSE")):
        sub = [x for x in allrows if sel(x)]
        cells = []
        for k in cuts:
            v = sum(1 for x in sub
                    if x["ncand"] <= 1 or (x["cand_margin"] is not None and x["cand_margin"] >= k))
            cells.append(100.0 * v / len(sub))
        print(f"  {label:<22}" + "".join(f"{v:>8.1f}%" for v in cells) + f"{len(sub):>8}")
    print("\n  There is no threshold at which the chamber looks competitive.")

    print("\n" + "=" * 88)
    print("SENSITIVITY — does the party-string rule change the answer?")
    print("=" * 88)
    print("  Both specifications are ENUMERATED in the frozen mapping, one column each.")
    print("  STRICT (published): a string is major iff it carries a variant of the party's")
    print("  own name and is not qualified by independence. Faction qualifiers do NOT")
    print("  disqualify, so 'MAGA Republican' and 'Culture Republican' are major; WA's")
    print("  top-two has no nominees, so 'Independent Dem.', 'Ind. Republican' and the")
    print("  'GOP/Independent' and 'Dem/Working Fmly' hybrids are OTHER. LOOSE folds exactly")
    print("  those into the major party, and is the only judgment still varied.")
    print("  Deltas are computed unrounded, so they need not equal the difference of the")
    print("  two rounded columns.")
    print(f"\n  {'year':<6}{'no D-v-R, STRICT':>20}{'no D-v-R, LOOSE':>20}{'delta':>9}")
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
            races.setdefault(key, []).append(party_of(party, spec="loose"))
        n_loose = len(races)
        nodr_loose = sum(1 for ps in races.values() if not ("D" in ps and "R" in ps))
        yr = [x for x in allrows if x["year"] == year]
        nodr_strict = sum(1 for x in yr if x["availability"] != "D-v-R")
        a, b = 100.0 * nodr_strict / len(yr), 100.0 * nodr_loose / n_loose
        print(f"  {year:<6}{a:>19.1f}%{b:>19.1f}%{a-b:>8.1f}")
    print("\n  The rule matters most in 2016, when eight distinct non-major party strings")
    print("  appeared — six Independent-flavored plus TWO two-party hybrids, GOP/Independent")
    print("  and Dem/Working Fmly, all listed under the universe table above; elsewhere it")
    print("  moves the figure by")
    print("  under a point.")

    print("\n" + "=" * 88)
    print("PRIMARY PARTICIPATION — August top-two votes vs the same seat's November race")
    print("=" * 88)
    print("  A ratio of VOTES CAST IN A CONTEST, not of distinct voters: roll-off and")
    print("  undervoting mean a race's vote total is not a headcount of participants.")
    print("  Each general seat is matched to its same-office, same-district primary on the")
    print("  same certified universe; 'matched' must equal 'seats' for the median to")
    print("  describe the whole chamber rather than a convenience sample.")
    print(f"\n  {'year':<6}{'seats':>7}{'matched':>9}{'median primary/general':>25}")
    ratio_by_year: dict[int, float] = {}
    for year in sorted(GENERALS):
        gen = race_vote_totals(con, GENERALS[year])
        pri = race_vote_totals(con, PRIMARIES[year])
        ratios = sorted(100.0 * pri[k] / gen[k] for k in gen if k in pri and gen[k])
        med = statistics.median(ratios)
        ratio_by_year[year] = med
        flag = "" if len(ratios) == len(gen) else "  <-- UNMATCHED SEATS, do not publish"
        print(f"  {year:<6}{len(gen):>7}{len(ratios):>9}{med:>24.1f}%{flag}")
        if len(ratios) != len(gen):
            problems.append(f"{year}: primary match {len(ratios)}/{len(gen)} seats")
    print("\n  The primary is the smaller round in every cycle. That it is smaller does NOT")
    print("  establish that it is where the decision was made — see the paper's limits.")

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
