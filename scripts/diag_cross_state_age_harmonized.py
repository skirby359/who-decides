"""Harmonized age composition and representativeness across WA / NY / ID, from one code path.

WHAT THIS IS FOR. `docs/who-decides-cross-state.md` ("Who Returns the Ballot?") was assembled
with Finding 1 populated from the three single-state papers' **as-reported** figures and
Finding 3 left as a table of `[recompute]` placeholders. Its own Methods section names the
missing build step: "a single harmonization script that computes the seven metrics identically
across the three DBs ... the age twin of `scripts/diag_cross_state_giving_turnout.py`". This is
that script, and `verify_who_returns_ballot.py` checks that the placeholders disappear once it
exists — so creating this file without filling the table is a build failure, on purpose.

WHY A SEPARATE SCRIPT AND NOT THREE PAPERS' NUMBERS COPIED. The single-state papers compute
their cuts with per-state conventions, and three of those differences are real:

  * **Election classes are not the same calendar.** WA and NY have odd-year November generals;
    Idaho has none, and its lowest-salience decisive contest is the **closed May Republican
    primary** — which for much of the state IS the election. Comparing "off-year" across the
    three would manufacture an equivalence that does not exist, so the comparison is between
    election *classes defined by salience*, and every lowest-salience cell is labelled with
    the contest it actually refers to.
  * **Age is stored three ways.** Measured, not assumed: WA and NY birthdates are BOTH
    normalised to July 1 of the birth year (every row, all 5.5M and 13.5M of them), so
    `date_diff('year', ...)` returns the year difference and nothing finer is available in
    either. Idaho stores a current integer age, so age-at-election is `age - (2026 - year)`,
    accurate to about a year. All three are therefore **year-resolution**, which is what makes
    a shared-bin comparison legitimate; the paper's "age precision differs" caveat is true but
    understates how close the three actually are.
  * **The CVAP benchmark must be one vintage.** Read from the pinned
    `docs/reference/cvap_age_acs<vintage>.csv`, written by `acs_cvap_by_state.py`. This script
    REFUSES to run without it rather than fetching, because a per-run fetch would let one
    state's benchmark move to a newer ACS release while the others stayed, and the
    dissimilarity index would stop being comparable with nothing to say so.

DEFINITIONS, taken from the papers that own them rather than reinvented:

  * **Dissimilarity index** — `who-decides-washington.md`, verbatim: half the summed absolute
    differences between an electorate's cohort shares and the citizen voting-age population's,
    across the four cohorts. Reproduced against WA's published values as a check (below).
  * **Habitual-core overlap** — `verify_who_decides_wa.py`'s construction: the share of a
    low-salience electorate that ALSO cast a ballot in the 2024 presidential general. Note the
    direction; the converse share (presidential voters who turn up off-cycle) is a different
    and much smaller number, and the WA paper reports both.

Read-only, and AGGREGATE OUTPUT ONLY. Three state voter files are opened — WA under RCW
29A.08.720, NY under FOIL lawful-use terms, ID under Idaho Code § 34-437A — and this script
must never emit a row. Every query is a COUNT, a share or a median.

Run:  python scripts/diag_cross_state_age_harmonized.py [--vintage 2024] [--markdown]
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import re

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _verify_prose as vp  # noqa: E402

vp.stdout_utf8()

ROOT = vp.ROOT
DATA = vp.DATA
BANDS = ["18-29", "30-44", "45-64", "65+"]

#: The 2024 presidential general, per state — the habitual-core reference and the
#: highest-salience class. Keyed the way each file identifies an election.
PRES = {"WA": "DATE '2024-11-05'", "NY": 2024, "ID": 2024}


class Class:
    """One election class: a label, the contest it denotes, and how to select its voters."""

    def __init__(self, key: str, label: str, note: str = ""):
        self.key, self.label, self.note = key, label, note


# Lowest-salience is state-specific BY CONSTRUCTION and every cell carries its contest.
CLASSES = {
    "WA": [
        Class("pres", "Nov 2024 presidential"),
        Class("mid", "Nov 2022 midterm"),
        Class("low21", "Nov 2021 odd-year general", "odd-year Nov general (RCW 29A.04.321)"),
        Class("low23", "Nov 2023 odd-year general", "odd-year Nov general"),
        Class("low25", "Nov 2025 odd-year general", "odd-year Nov general"),
    ],
    "NY": [
        Class("pres", "Nov 2024 presidential"),
        Class("mid", "Nov 2022 midterm"),
        Class("low17", "Nov 2017 odd-year general", "odd-year Nov general"),
        Class("low19", "Nov 2019 odd-year general", "odd-year Nov general"),
        Class("low21", "Nov 2021 odd-year general", "odd-year Nov general"),
        Class("low23", "Nov 2023 odd-year general", "odd-year Nov general"),
        Class("low25", "Nov 2025 odd-year general", "odd-year Nov general"),
    ],
    "ID": [
        Class("pres", "Nov 2024 presidential"),
        Class("mid", "Nov 2022 midterm"),
        Class("lowrep22", "May 2022 closed Republican primary",
              "no odd-year Nov general exists; the closed May R primary is the decisive contest"),
        Class("lowrep24", "May 2024 closed Republican primary",
              "no odd-year Nov general exists; the closed May R primary is the decisive contest"),
        Class("lowrep26", "May 2026 closed Republican primary",
              "no odd-year Nov general exists; the closed May R primary is the decisive contest"),
    ],
}

# EVERY loaded low-salience contest, not a selection (widened 2026-08-09).
#
# This used to be NY ["low23", "low25"] and ID ["lowrep24"] — two of New York's
# five loaded odd-year generals and one of Idaho's three loaded Republican
# primaries — while Washington used all three of its. An adversarial pass found
# that the selection, not the states, drove two published claims: New York's
# low-salience 65+ floor is 28.4% on the full set (its 2017 general) rather than
# 34.4%, and Idaho's 2022 primary at 41.4% does NOT exceed New York's 2023
# general at 41.6%, which the paper asserted of "every odd-year general measured
# here".
#
# Reporting all of them also makes the lag confound visible instead of hiding it:
# both states' series are near-monotone in distance from the 2026 roll, which is
# what a current-roll reconstruction should do and what the paper now says.
LOW = {"WA": ["low21", "low23", "low25"],
       "NY": ["low17", "low19", "low21", "low23", "low25"],
       "ID": ["lowrep22", "lowrep24", "lowrep26"]}


# --------------------------------------------------------------------------- per-state SQL
def _wa(con, key: str) -> tuple[str, str, str]:
    """(age expression, voted-join, extra WHERE) for Washington.

    `voting_history` is keyed on election_date, so a class is one date. birthdate is July-1
    normalised, so date_diff('year', ...) is the year difference — the only resolution
    available and the convention the WA paper states.
    """
    dates = {"pres": "2024-11-05", "mid": "2022-11-08", "low21": "2021-11-02",
             "low23": "2023-11-07", "low25": "2025-11-04"}
    join = (f"JOIN (SELECT DISTINCT state_voter_id FROM voting_history "
            f"WHERE election_date = DATE '{dates[key]}') h USING (state_voter_id)")
    return f"date_diff('year', v.birthdate, DATE '{dates[key]}')", join, "v.birthdate IS NOT NULL"


def _ny(con, key: str) -> tuple[str, str, str]:
    """New York: `voter_participation` keyed on (election_year, kind); birthdate July-1 too."""
    spec = {"pres": (2024, "GENERAL", "2024-11-05"), "mid": (2022, "GENERAL", "2022-11-08"),
            "low17": (2017, "GENERAL", "2017-11-07"), "low19": (2019, "GENERAL", "2019-11-05"),
            "low21": (2021, "GENERAL", "2021-11-02"),
            "low23": (2023, "GENERAL", "2023-11-07"), "low25": (2025, "GENERAL", "2025-11-04")}
    year, kind, date = spec[key]
    join = (f"JOIN (SELECT DISTINCT state_voter_id FROM voter_participation "
            f"WHERE election_year = {year} AND kind = '{kind}') h USING (state_voter_id)")
    return f"date_diff('year', v.birthdate, DATE '{date}')", join, "v.birthdate IS NOT NULL"


def _id(con, key: str) -> tuple[str, str, str]:
    """Idaho: current integer age, so age-at-election is age - (2026 - year), +/- one year.

    The lowest-salience class is the closed Republican primary, selected on the BALLOT the
    voter actually pulled (`ballot_choice = 'REP'`) rather than on party of record — which is
    the distinction that makes Idaho's exclusion a measurement rather than an inference.
    """
    spec = {"pres": (2024, "GENERAL", None), "mid": (2022, "GENERAL", None),
            "lowrep22": (2022, "PRIMARY", "REP"), "lowrep24": (2024, "PRIMARY", "REP"),
            "lowrep26": (2026, "PRIMARY", "REP")}
    year, kind, ballot = spec[key]
    extra = f" AND ballot_choice = '{ballot}'" if ballot else ""
    join = (f"JOIN (SELECT DISTINCT state_voter_id FROM voter_participation "
            f"WHERE election_year = {year} AND kind = '{kind}'{extra}) h USING (state_voter_id)")
    return f"(v.age - (2026 - {year}))", join, "v.age IS NOT NULL"


ADAPTERS = {"WA": _wa, "NY": _ny, "ID": _id}
DBS = {"WA": "wa_vrdb.duckdb", "NY": "ny_vrdb.duckdb", "ID": "id_vrdb.duckdb"}


def _pres_join(state: str) -> str:
    if state == "WA":
        return ("SELECT DISTINCT state_voter_id FROM voting_history "
                "WHERE election_date = DATE '2024-11-05'")
    return ("SELECT DISTINCT state_voter_id FROM voter_participation "
            "WHERE election_year = 2024 AND kind = 'GENERAL'")


# ------------------------------------------------------------------------------ derivations
def load_cvap(vintage: int) -> dict[str, dict[str, float]]:
    path = ROOT / "docs" / "reference" / f"cvap_age_acs{vintage}.csv"
    if not path.exists():
        raise SystemExit(
            f"FATAL: {path.relative_to(ROOT)} is missing. The dissimilarity index is only\n"
            f"comparable across states if every state uses ONE ACS vintage, so this script does\n"
            f"not fetch.\n  Create it with:  python scripts/acs_cvap_by_state.py "
            f"--vintage {vintage}")
    out: dict[str, dict[str, float]] = {}
    with path.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            out.setdefault(row["state"], {})[row["cohort"]] = float(row["cvap_pct"])
    for st in ADAPTERS:
        missing = [b for b in BANDS if b not in out.get(st, {})]
        if missing:
            raise SystemExit(f"FATAL: {path.name} has no {st} row for {missing}")
    return out


def composition(con, state: str, key: str) -> dict:
    age, join, extra = ADAPTERS[state](con, key)
    band = (f"CASE WHEN {age} < 30 THEN '18-29' WHEN {age} < 45 THEN '30-44' "
            f"WHEN {age} < 65 THEN '45-64' ELSE '65+' END")
    where = f"WHERE {extra} AND {age} BETWEEN 18 AND 105"
    rows = dict(con.execute(f"""
        WITH e AS (SELECT {band} b FROM voters v {join} {where})
        SELECT b, COUNT(*) FROM e GROUP BY 1""").fetchall())
    total = sum(rows.values()) or 1
    out = {b: 100.0 * rows.get(b, 0) / total for b in BANDS}
    out["n"] = total
    out["median"], = con.execute(
        f"SELECT median({age}) FROM voters v {join} {where}").fetchone()
    # Habitual core: share of THIS electorate that also cast a 2024 presidential ballot.
    core, = con.execute(f"""
        WITH e AS (SELECT v.state_voter_id sid FROM voters v {join} {where})
        SELECT 100.0 * COUNT(*) FILTER (
                 WHERE sid IN ({_pres_join(state)})) / NULLIF(COUNT(*), 0) FROM e""").fetchone()
    out["core"] = float(core) if core is not None else float("nan")
    return out


def dissim(comp: dict, cvap: dict[str, float]) -> float:
    """The WA paper's definition: half the summed absolute cohort differences vs CVAP."""
    return 0.5 * sum(abs(comp[b] - cvap[b]) for b in BANDS)


# The WA paper differences against its PUBLISHED CVAP row, which is rounded to one decimal
# before the subtraction. This pin carries the unrounded ACS shares (19.8495... not 19.8).
#
# WHY THAT MATTERS, and how it was found. The first run of this script reported WA as
# 7.5 / 13.3 / 18.6-20.0 against the paper's 7.4 / 13.2 / 18.5-19.9 — every value 0.1 high, in
# the SAME direction, which by this repo's own rule is a basis difference and never drift. The
# first two suspects were wrong: the paper's composition also filters on
# `registration_date <= election_date` and has no upper age bound, and measuring both variants
# gave dissimilarity identical to three decimals (7.418 either way). It is the benchmark's
# rounding, and nothing else.
#
# So both are computed. The UNROUNDED value is the one this script publishes, because a
# benchmark rounded before differencing throws away precision for no reason. The ROUNDED value
# exists only to prove the definition reproduces the single-state paper exactly — which is the
# claim `who-decides-cross-state.md` makes about the harmonized recomputation.
_WA_PUBLISHED_CVAP = {"18-29": 19.8, "30-44": 26.7, "45-64": 30.9, "65+": 22.6}


# --------------------------------------------------------------- the WA cross-check
#
# WHY THIS IS A FUNCTION CALLED BY `derive()` AND NOT A BLOCK IN `main()`.
#
# `who-decides-cross-state.md` says this script "asserts on every run that its
# definition reproduces `who-decides-washington.md`'s published dissimilarity
# ladder exactly at that paper's printed precision, and exits non-zero if it does
# not — so a change to the shared definition cannot silently decouple this paper
# from the single-state one it generalises."
#
# Until 2026-08-09 that sentence was false three ways, and an adversarial pass
# found all three:
#
#   1. The check lived in `main()`. The only automated consumer,
#      `verify_who_returns_ballot.py`, calls `derive()` — so nothing in any gate,
#      test or release path ever executed it. Nothing else in the repo ran the
#      script at all.
#   2. It compared against HARDCODED LITERALS (`want = {"pres": 7.4, "mid": 13.2}`
#      and a bare 18.5 / 19.9). It never opened `who-decides-washington.md`. So it
#      could catch a change to the shared *definition* but not a revision to the
#      paper it claimed to be pinned to — which is the decoupling the sentence
#      describes.
#   3. It reported by return code, which is only meaningful to a human running
#      the script by hand.
#
# It now SCRAPES the ladder out of the WA paper and RAISES. A guard that a caller
# can decline to look at is not a guard.
_WA_PAPER = ROOT / "docs" / "who-decides-washington.md"

# The sentence the ladder lives in. Anchored on the surrounding words rather than
# on position, and a miss is a failure: rewording it out from under this check is
# exactly the drift the check exists to catch.
_WA_LADDER_RX = re.compile(
    r"It comes out \*\*([\d.]+)\*\* for the 2024 presidential electorate, \*\*([\d.]+)\*\* at\s+"
    r"the midterm, and \*\*([\d.]+)–([\d.]+)\*\* across the three off-years")


def crosscheck_wa_paper(d: dict) -> dict:
    """Assert the shared definition still reproduces the WA paper's own ladder.

    Compared on the paper's OWN rounded CVAP row (`dissim_pub`), so the test
    isolates the definition rather than the benchmark's precision — and as an
    EXACT rounding test, not a tolerance. The first version of this check used
    `< 0.1` and passed while every value sat 0.07 high in the same direction,
    which is the systematic offset a tolerance is worst at catching.

    Raises:
        RuntimeError: if the paper's sentence cannot be found, or if the ladder
            it publishes is not what this definition produces.
    """
    try:
        text = _WA_PAPER.read_text(encoding="utf-8")
    except OSError as exc:                                   # pragma: no cover
        raise RuntimeError(
            f"WA cross-check: cannot read {_WA_PAPER}. This guard is what pins the "
            f"harmonized definition to the single-state paper; it must not be skipped."
        ) from exc
    m = _WA_LADDER_RX.search(re.sub(r"\s+", " ", text))
    if not m:
        raise RuntimeError(
            "WA cross-check: the dissimilarity-ladder sentence in "
            "who-decides-washington.md did not match. Either the paper was reworded "
            "(re-point _WA_LADDER_RX) or the ladder was removed. A silent skip here "
            "is how the two papers would decouple.")
    paper = tuple(float(x) for x in m.groups())

    pub = {k: d["WA"][k]["dissim_pub"] for k in ("pres", "mid", *LOW["WA"])}
    low = [pub[k] for k in LOW["WA"]]
    got = (round(pub["pres"], 1), round(pub["mid"], 1),
           round(min(low), 1), round(max(low), 1))
    if got != paper:
        raise RuntimeError(
            f"WA cross-check FAILED: who-decides-washington.md publishes "
            f"{paper[0]} / {paper[1]} / {paper[2]}–{paper[3]}, this definition gives "
            f"{got[0]} / {got[1]} / {got[2]}–{got[3]}. Do not publish the cross-state "
            f"table until this is understood — a one-directional gap is a basis "
            f"difference, not drift.")
    return {"paper": paper, "got": got,
            "gap": max(abs(d["WA"][k]["dissim"] - pub[k]) for k in pub)}


def derive(vintage: int) -> dict:
    cvap = load_cvap(vintage)
    out: dict = {"cvap": cvap, "vintage": vintage}
    for state, db in DBS.items():
        con = duckdb.connect(str(DATA / db), read_only=True)
        per: dict = {}
        for cls in CLASSES[state]:
            c = composition(con, state, cls.key)
            c["dissim"] = dissim(c, cvap[state])
            if state == "WA":
                c["dissim_pub"] = dissim(c, _WA_PUBLISHED_CVAP)
            c["label"], c["note"] = cls.label, cls.note
            per[cls.key] = c
        con.close()
        out[state] = per
    out["id_convention"] = id_convention_sensitivity(cvap)
    # Runs here, not in main(), so every automated consumer executes it. See the
    # long note above crosscheck_wa_paper for what this sentence used to claim.
    out["wa_crosscheck"] = crosscheck_wa_paper(out)
    return out


def id_convention_sensitivity(cvap) -> dict:
    """How much of Idaho's position is the age CONVENTION rather than Idaho.

    THE PROBLEM, measured 2026-08-10. All three states are year-of-birth
    resolution, but not on the same clock. WA and NY publish a birth YEAR, which
    the loaders materialise as July 1 — so `date_diff('year', ...)` against a
    November election is the calendar-year difference, and it implicitly assumes
    the birthday has already happened. Idaho publishes a current integer AGE,
    which already accounts for whether the birthday has happened, and
    `age - (2026 - year)` inherits that. The two conventions therefore differ by
    one year for whoever's 2026 birthday falls after the extract date, and an
    integer age cannot say who that is.

    So Idaho's figure is a BRACKET, not a point, and the bracket is one-sided:
    `age` is the low end and `age + 1` the high end. On the 65+ share that is
    **1.9-2.3 points** — larger than it sounds, because one single-year cohort
    near 65 is about 1.8% of the Idaho roll. The paper used to call this
    "accurate to about a year" and add that the caveat "understates how close the
    three are." A year of age resolution is two points of the 65+ share, in one
    direction, in exactly the comparison the dissimilarity index makes.

    Reported rather than corrected, because there is nothing to correct to: the
    point estimate is unrecoverable from an integer age. What matters is that the
    correction runs one way, and this returns the size and the direction.
    """
    con = duckdb.connect(str(DATA / DBS["ID"]), read_only=True)
    out: dict = {}
    try:
        for cls in CLASSES["ID"]:
            base_age, join, extra = _id(con, cls.key)
            hi_age = base_age.replace("(v.age -", "(v.age + 1 -")
            assert hi_age != base_age, "the +1 substitution stopped matching"
            row = {}
            for tag, age in (("lo", base_age), ("hi", hi_age)):
                band = (f"CASE WHEN {age} < 30 THEN '18-29' WHEN {age} < 45 THEN '30-44' "
                        f"WHEN {age} < 65 THEN '45-64' ELSE '65+' END")
                where = f"WHERE {extra} AND {age} BETWEEN 18 AND 105"
                rows = dict(con.execute(f"""
                    WITH e AS (SELECT {band} b FROM voters v {join} {where})
                    SELECT b, COUNT(*) FROM e GROUP BY 1""").fetchall())
                tot = sum(rows.values()) or 1
                comp = {b: 100.0 * rows.get(b, 0) / tot for b in BANDS}
                row[f"{tag}_65"] = comp["65+"]
                row[f"{tag}_dissim"] = dissim(comp, cvap["ID"])
            row["gap_65"] = row["hi_65"] - row["lo_65"]
            row["gap_dissim"] = row["hi_dissim"] - row["lo_dissim"]
            out[cls.key] = row
    finally:
        con.close()
    gaps = [r["gap_65"] for r in out.values()]
    # The direction is the load-bearing part: if the convention could push Idaho's
    # 65+ share DOWN, the paper's "if anything understated" reading would be wrong.
    if any(g < 0 for g in gaps):
        raise SystemExit(
            "FATAL: the Idaho age-convention bracket is supposed to run one way "
            "(the `age + 1` end is older). A negative gap means the bracket is not "
            "one-sided and the paper's caveat cannot be stated as a direction.")
    out["gap65_lo"], out["gap65_hi"] = min(gaps), max(gaps)
    return out


# ----------------------------------------------------------------------------------- output
def _span(vals: list[float], nd: int = 1) -> str:
    lo, hi = min(vals), max(vals)
    return f"{lo:.{nd}f}" if abs(hi - lo) < 10 ** -nd / 2 else f"{lo:.{nd}f}–{hi:.{nd}f}"


def report(d: dict) -> None:
    print("=" * 92)
    print(f"HARMONIZED CROSS-STATE AGE COMPOSITION — one code path, shared bins, "
          f"ACS {d['vintage'] - 4}-{d['vintage']} CVAP")
    print("=" * 92)
    for state in DBS:
        print(f"\n{state}   CVAP benchmark  " +
              "  ".join(f"{b} {d['cvap'][state][b]:.1f}%" for b in BANDS))
        print(f"  {'class':38} {'n':>10}  {'18-29':>6} {'65+':>6} {'med':>4} "
              f"{'dissim':>7} {'core':>6}")
        for cls in CLASSES[state]:
            c = d[state][cls.key]
            print(f"  {cls.label:38} {c['n']:>10,}  {c['18-29']:>6.1f} {c['65+']:>6.1f} "
                  f"{c['median']:>4.0f} {c['dissim']:>7.2f} {c['core']:>6.1f}")
    print("\n  dissim = half the summed |electorate - CVAP| across the four cohorts")
    print("  core   = % of that electorate that also cast a 2024 presidential ballot")


def markdown(d: dict) -> None:
    print("\n" + "=" * 92)
    print("PASTE-READY — Finding 1")
    print("=" * 92 + "\n")
    print("| State | Presidential 65+ / 18–29 | Midterm 65+ / 18–29 | "
          "Lowest-salience 65+ / 18–29 (class) |")
    print("|---|---|---|---|")
    low_class = {"WA": "odd-year Nov general", "NY": "odd-year Nov general",
                 "ID": "closed May GOP primary"}
    for state in DBS:
        p, m = d[state]["pres"], d[state]["mid"]
        lows = [d[state][k] for k in LOW[state]]
        l65 = _span([c["65+"] for c in lows])
        l29 = _span([c["18-29"] for c in lows])
        print(f"| **{state}** | {p['65+']:.1f}% / {p['18-29']:.1f}% | "
              f"{m['65+']:.1f}% / {m['18-29']:.1f}% | "
              f"{l65}% / {l29}% ({low_class[state]}) |")

    print("\n" + "=" * 92)
    print("PASTE-READY — Finding 3")
    print("=" * 92 + "\n")
    print("| Metric | WA | NY | ID |")
    print("|---|---|---|---|")
    cells = []
    for state in DBS:
        p = d[state]["pres"]["dissim"]
        lows = [d[state][k]["dissim"] for k in LOW[state]]
        cells.append(f"{p:.1f} → {_span(lows)}")
    print("| Age-dissimilarity vs CVAP (pres → lowest-salience) | " + " | ".join(cells) + " |")
    cells = []
    for state in DBS:
        lows = [d[state][k]["core"] for k in LOW[state]]
        cells.append(f"{_span(lows)}%")
    print("| Habitual-core overlap (off-year ⊂ presidential) | " + " | ".join(cells) + " |")
    print()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vintage", type=int, default=2024, help="ACS 5-year end year of the pin")
    ap.add_argument("--markdown", action="store_true", help="emit paste-ready paper tables")
    args = ap.parse_args()
    d = derive(args.vintage)
    report(d)
    if args.markdown:
        markdown(d)
    # WA's published dissimilarity ladder is the cross-check on this whole construction. It is
    # an EXACT rounding test, not a tolerance: the first version of this check used `< 0.1` and
    # passed while every value sat 0.07 high in the same direction, which is precisely the
    # systematic offset a tolerance is worst at catching. Compared on the paper's own rounded
    # benchmark, so the test isolates the DEFINITION rather than the benchmark's precision.
    pub = {k: d["WA"][k]["dissim_pub"] for k in ("pres", "mid", *LOW["WA"])}
    want = {"pres": 7.4, "mid": 13.2}
    got = {k: round(v, 1) for k, v in pub.items()}
    low_pub = [pub[k] for k in LOW["WA"]]
    print(f"\n  CROSS-CHECK — definition, on the paper's own rounded CVAP row")
    print(f"    who-decides-washington.md  7.4 / 13.2 / 18.5–19.9")
    print(f"    this script               {got['pres']} / {got['mid']} / "
          f"{round(min(low_pub), 1)}–{round(max(low_pub), 1)}"
          f"   (unrounded {pub['pres']:.3f} / {pub['mid']:.3f})")
    ok = (got["pres"] == want["pres"] and got["mid"] == want["mid"]
          and round(min(low_pub), 1) == 18.5 and round(max(low_pub), 1) == 19.9)
    print("    " + ("ok  reproduces the single-state paper EXACTLY at its printed precision"
                    if ok else
                    "FAIL the shared definition does NOT reproduce the WA paper. Do not "
                    "publish the\n        cross-state table until this is understood — a "
                    "one-directional gap is a basis\n        difference, not drift."))
    # And the gap the published (unrounded-benchmark) column carries against that ladder, so
    # the footnote in the paper can state it rather than leave a reader to wonder.
    gap = max(abs(d["WA"][k]["dissim"] - pub[k]) for k in pub)
    print(f"\n  Benchmark-rounding gap on the WA column: {gap:.3f} index points "
          f"(unrounded CVAP vs the paper's 1-dp row).\n  That is the ENTIRE difference between "
          f"this script's WA figures and the single-state paper's.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
