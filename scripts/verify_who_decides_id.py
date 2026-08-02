"""Independent re-derivation of docs/who-decides-idaho.md, asserted against its prose.

CONVERTED TO AN ASSERTING VERIFIER 2026-08-01. This script previously printed each derived
value beside a hand-typed "(paper: ...)" for a human to compare by eye, and returned None —
so it always exited 0. The release checklist ran it as `verify_who_decides_id.py || echo
FAILED`, which could never print FAILED no matter what the data said. Three of its annotations
had also drifted from a paper that had been revised under them.

It now scrapes the paper and asserts. See `_verify_prose.py` for the three rules; the one that
matters most here is that a probe whose anchor matches nothing FAILS rather than skipping,
because a reworded sentence silently disarming a check is the failure this replaces.

Hits data/id_vrdb.duckdb (voters + voter_participation) DIRECTLY with from-scratch SQL — not
by importing the diag scripts — so agreement confirms the paper independently of the analysis
code. Contested-primary and safe-seat-by-registration also touch id_statewide.duckdb
(ATTACHed read-only). Read-only; AGGREGATE OUTPUT ONLY. The voter file carries personal data
under Idaho Code § 34-437A and this script must never emit a row.

TWO BASES, and conflating them is the trap. Idaho's paper reports some cuts over the
REGISTRATION ROLL and others over the 2024 GENERAL ELECTORATE, and the same label reads
differently in each: Republicans are 34.5% over-65 on the roll (§III) and 31.7% among 2024
general voters (§II). Both are correct. A probe pointed at the wrong one reads as a defect,
which is how a whole-column offset in New York's age bands was misdiagnosed once already.

Idaho gives current age as of the 2026 snapshot rather than date of birth, so election-time
age is `age - (2026 - year)`, accurate to about a year — bands and medians only, never a
point estimate of an individual's age. Turnout RATES are deliberately not reproduced: the
roll shrank 1.18M -> 1.03M since 2024, so rates are survivorship-inflated and the paper
reports composition shares instead.

Run:  python scripts/verify_who_decides_id.py [--coverage]
"""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _verify_prose as vp  # noqa: E402

vp.stdout_utf8()

VRDB = str(vp.DATA / "id_vrdb.duckdb")
STATEWIDE = str(vp.DATA / "id_statewide.duckdb")
PAPER = vp.DOCS / "who-decides-idaho.md"

BANDS = ["18-29", "30-44", "45-64", "65+"]
PARTY = ("CASE WHEN party='REP' THEN 'REP' WHEN party='DEM' THEN 'DEM' "
         "WHEN party='UNA' THEN 'UNAFF' ELSE 'OTHER' END")
_AGE = "(v.age - (2026 - {yr}))"


def _band(agesql: str) -> str:
    return (f"CASE WHEN {agesql}<30 THEN '18-29' WHEN {agesql}<45 THEN '30-44' "
            f"WHEN {agesql}<65 THEN '45-64' ELSE '65+' END")


def _electorate_join(year: int, kind: str) -> str:
    return (f"JOIN (SELECT DISTINCT state_voter_id FROM voter_participation "
            f"WHERE election_year={year} AND kind='{kind}') p USING (state_voter_id)")


def age_composition(con, d: dict, tag: str, year: int, kind: str | None) -> None:
    """Share of an electorate (or of the roll, when kind is None) by age band, plus median."""
    ag = _AGE.format(yr=year)
    join = "" if kind is None else _electorate_join(year, kind)
    rows = con.execute(f"""
        WITH e AS (SELECT {_band(ag)} band FROM voters v {join}
                   WHERE v.age IS NOT NULL AND {ag} BETWEEN 18 AND 105)
        SELECT band, COUNT(*) FROM e GROUP BY 1""").fetchall()
    counts = {b: 0 for b in BANDS}
    for b, n in rows:
        counts[b] = n
    tot = sum(counts.values()) or 1
    for b in BANDS:
        d[f"{tag}_{b}"] = 100.0 * counts[b] / tot
    d[f"{tag}_median"], = con.execute(f"""
        SELECT median({ag}) FROM voters v {join}
        WHERE v.age IS NOT NULL AND {ag} BETWEEN 18 AND 105""").fetchone()


def party_shares(con, d: dict, tag: str, year: int | None, kind: str | None) -> None:
    """Party-of-record mix over the roll or over one electorate."""
    join = "" if kind is None else _electorate_join(year, kind)
    rows = con.execute(
        f"SELECT {PARTY}, COUNT(*) FROM voters v {join} GROUP BY 1").fetchall()
    counts: dict[str, int] = {}
    for p, n in rows:
        counts[p] = counts.get(p, 0) + n
    tot = sum(counts.values()) or 1
    for p in ("REP", "DEM", "UNAFF", "OTHER"):
        d[f"{tag}_{p}"] = 100.0 * counts.get(p, 0) / tot
    d[f"{tag}_n"] = tot
    d[f"{tag}_RminusD"] = d[f"{tag}_REP"] - d[f"{tag}_DEM"]


def derive() -> dict:
    d: dict = {}
    con = duckdb.connect(VRDB, read_only=True)

    d["roll_n"], = con.execute("SELECT COUNT(*) FROM voters").fetchone()
    party_shares(con, d, "roll", None, None)
    d["unaff_n"], = con.execute(
        "SELECT COUNT(*) FROM voters WHERE party='UNA'").fetchone()

    # Section I — age composition of each general electorate, and of the roll itself.
    for year in (2024, 2022, 2020):
        age_composition(con, d, f"gen{year}", year, "GENERAL")
    age_composition(con, d, "rollage", 2026, None)

    # Section II — age profile of each party's 2024 GENERAL voters.
    ag = _AGE.format(yr=2024)
    rows = con.execute(f"""
        WITH e AS (SELECT {PARTY} p, {ag} a FROM voters v {_electorate_join(2024, 'GENERAL')}
                   WHERE v.age IS NOT NULL AND {ag} BETWEEN 18 AND 105)
        SELECT p, 100.0*COUNT(*) FILTER (WHERE a>=65)/COUNT(*),
                  100.0*COUNT(*) FILTER (WHERE a<30)/COUNT(*), median(a)
        FROM e GROUP BY 1""").fetchall()
    for p, p65, p1829, med in rows:
        d[f"e24_{p}_65"], d[f"e24_{p}_1829"], d[f"e24_{p}_median"] = \
            float(p65), float(p1829), float(med)

    # Section III — the same profile over the ROLL, which is a different denominator and
    # gives different numbers for the same words. Both appear in the paper.
    rows = con.execute(f"""
        WITH e AS (SELECT {PARTY} p, v.age a FROM voters v WHERE v.age BETWEEN 18 AND 105)
        SELECT p, 100.0*COUNT(*) FILTER (WHERE a>=65)/COUNT(*),
                  100.0*COUNT(*) FILTER (WHERE a<30)/COUNT(*), median(a)
        FROM e GROUP BY 1""").fetchall()
    for p, p65, p1829, med in rows:
        d[f"r_{p}_65"], d[f"r_{p}_1829"], d[f"r_{p}_median"] = \
            float(p65), float(p1829), float(med)

    # Section III/IV — each bloc's share of four electorates.
    for tag, year, kind in (("g24", 2024, "GENERAL"), ("g22", 2022, "GENERAL"),
                            ("p24", 2024, "PRIMARY"), ("p22", 2022, "PRIMARY")):
        party_shares(con, d, tag, year, kind)

    # Section IV — Republican share of primary ballots actually pulled. Distinct from the
    # party-of-record cut above: this is the ballot chosen, not the registration carried.
    # The paper's "80-86%" spans EVERY primary cycle in the file, not just the two in the
    # table, and the file now holds a 2026 primary at 79.6% — so a probe restricted to
    # 2022/2024 reads the claim as wrong when it is right.
    cycles = con.execute("""
        SELECT election_year, 100.0*COUNT(*) FILTER (WHERE ballot_choice='REP')/COUNT(*)
        FROM voter_participation WHERE kind='PRIMARY' AND ballot_choice IS NOT NULL
        GROUP BY 1""").fetchall()
    by_year = {int(y): float(v) for y, v in cycles}
    d["ballot24"], d["ballot22"] = by_year.get(2024, -1.0), by_year.get(2022, -1.0)
    d["ballot_lo"], d["ballot_hi"] = min(by_year.values()), max(by_year.values())

    # Section V — legislative districts banded by registration lean.
    (d["ld_safe_r"], d["ld_likely_r"], d["ld_lean_r"], d["ld_comp"], d["ld_any_d"],
     d["ld_n"]) = con.execute("""
        WITH ld AS (
            SELECT legislative_district,
                   100.0*COUNT(*) FILTER (WHERE party='REP')/COUNT(*)
                   - 100.0*COUNT(*) FILTER (WHERE party='DEM')/COUNT(*) net
            FROM voters WHERE legislative_district IS NOT NULL GROUP BY 1)
        SELECT COUNT(*) FILTER (WHERE net>=40), COUNT(*) FILTER (WHERE net>=20 AND net<40),
               COUNT(*) FILTER (WHERE net>=5 AND net<20), COUNT(*) FILTER (WHERE net>-5 AND net<5),
               COUNT(*) FILTER (WHERE net<=-5), COUNT(*) FROM ld""").fetchone()

    # Section IV — contested Republican legislative primaries, from the results warehouse.
    con.execute(f"ATTACH '{STATEWIDE}' AS sw (READ_ONLY)")
    d["prim_races"], d["prim_contested"] = con.execute("""
        WITH rr AS (
            SELECT ra.race_id, COUNT(DISTINCT pr.candidate_id) nc
            FROM sw.elections e JOIN sw.races ra ON ra.election_id=e.election_id
            JOIN sw.precinct_results pr ON pr.race_id=ra.race_id
            WHERE e.election_type='primary' AND e.election_date=DATE '2024-05-21'
              AND UPPER(ra.race_name) LIKE '%REPUBLICAN%'
              AND (UPPER(ra.race_name) LIKE '%LEGISLATIVE DISTRICT%'
                   OR (UPPER(ra.race_name) LIKE '%REPRESENTATIVE DISTRICT%'
                       AND UPPER(ra.race_name) LIKE '%SEAT%')
                   OR UPPER(ra.race_name) LIKE '%SENATOR DISTRICT%')
            GROUP BY 1)
        SELECT COUNT(*), COUNT(*) FILTER (WHERE nc>=2) FROM rr""").fetchone()
    d["prim_single"] = d["prim_races"] - d["prim_contested"]
    d["prim_contested_pct"] = 100.0 * d["prim_contested"] / d["prim_races"]
    d["prim_single_pct"] = 100.0 * d["prim_single"] / d["prim_races"]
    con.close()
    return d


PROBES = [
    ("registration roll size", r"file with history \(([\d,]+) registrants", "roll_n", 0),
    ("unaffiliated registrants and roll share",
     r"Idaho's ([\d,]+) unaffiliated registrants \(([\d.]+)% of the roll\)",
     ("unaff_n", "roll_UNAFF"), 0.05),

    # ---- Section I: age composition of the general electorate, by cycle
    ("§I 2024 presidential composition",
     r"\| Nov 2024 \| Presidential \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| (\d+) \|",
     ("gen2024_18-29", "gen2024_30-44", "gen2024_45-64", "gen2024_65+", "gen2024_median"), 0.05),
    ("§I 2022 midterm composition",
     r"\| Nov 2022 \| Midterm \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \| ([\d.]+)% \| "
     r"\*\*([\d.]+)%\*\* \| (\d+) \|",
     ("gen2022_18-29", "gen2022_30-44", "gen2022_45-64", "gen2022_65+", "gen2022_median"), 0.05),
    ("§I 2020 presidential composition",
     r"\| Nov 2020 \| Presidential \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| (\d+) \|",
     ("gen2020_18-29", "gen2020_30-44", "gen2020_45-64", "gen2020_65+", "gen2020_median"), 0.05),
    ("§I registration baseline composition",
     r"\| — \| Registration baseline \(2026\) \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| "
     r"([\d.]+)% \| (\d+) \|",
     ("rollage_18-29", "rollage_30-44", "rollage_45-64", "rollage_65+", "rollage_median"), 0.05),
    ("§I under-30 halving and 65+ swell",
     r"\(([\d.]+)% → ([\d.]+)%\) and the 65\+ share swells \((\d+)% → (\d+)%\)",
     ("gen2024_18-29", "gen2022_18-29", "gen2024_65+", "gen2022_65+"), 0.5),

    # ---- Section II: the 2024 GENERAL electorate, by party
    ("§II Republican general-electorate age",
     r"\| Republican \| ([\d.]+)% \| ([\d.]+)% \| (\d+) \|",
     ("e24_REP_65", "e24_REP_1829", "e24_REP_median"), 0.05),
    ("§II Democratic general-electorate age",
     r"\| Democratic \| ([\d.]+)% \| ([\d.]+)% \| (\d+) \|",
     ("e24_DEM_65", "e24_DEM_1829", "e24_DEM_median"), 0.05),
    ("§II unaffiliated general-electorate age",
     r"\| \*\*Unaffiliated\*\* \| \*\*([\d.]+)%\*\* \| \*\*([\d.]+)%\*\* \| \*\*(\d+)\*\* \|",
     ("e24_UNAFF_65", "e24_UNAFF_1829", "e24_UNAFF_median"), 0.05),
    ("§II other-party general-electorate age",
     r"\| Other \(Lib/Con\) \| ([\d.]+)% \| ([\d.]+)% \| (\d+) \|",
     ("e24_OTHER_65", "e24_OTHER_1829", "e24_OTHER_median"), 0.05),

    # ---- Section III: the bloc table. Columns 2-5 are ROLL-based, 6-7 are electorate shares.
    ("§III Republican bloc row",
     r"\| Republican \| ([\d.]+)% \| (\d+) \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| "
     r"\*\*([\d.]+)%\*\* \|",
     ("roll_REP", "r_REP_median", "r_REP_65", "r_REP_1829", "g24_REP", "p24_REP"), 0.05),
    ("§III unaffiliated bloc row",
     r"\| Unaffiliated \| ([\d.]+)% \| (\d+) \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| "
     r"\*\*([\d.]+)%\*\* \|",
     ("roll_UNAFF", "r_UNAFF_median", "r_UNAFF_65", "r_UNAFF_1829", "g24_UNAFF", "p24_UNAFF"),
     0.05),
    ("§III Democratic bloc row",
     r"\| Democratic \| ([\d.]+)% \| (\d+) \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \|",
     ("roll_DEM", "r_DEM_median", "r_DEM_65", "r_DEM_1829", "g24_DEM", "p24_DEM"), 0.05),
    ("§III other bloc row",
     r"\| Other \| ([\d.]+)% \| (\d+) \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \|",
     ("roll_OTHER", "r_OTHER_median", "r_OTHER_65", "r_OTHER_1829", "g24_OTHER", "p24_OTHER"),
     0.05),
    ("§III unaffiliated general vs roll, in prose",
     r"\*\*([\d.]+)% of the 2024 general electorate\*\* — essentially their full ([\d.]+)% "
     r"of the roll", ("g24_UNAFF", "roll_UNAFF"), 0.05),
    ("§III unaffiliated primary share, in prose",
     r"only \*\*([\d.]+)% of the May primary electorate\*\*", "p24_UNAFF", 0.05),

    # ---- Section IV: the contest table and the closed-primary claim
    ("§IV Nov 2024 general",
     r"\| Nov 2024 general \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| \+([\d.]+) \|",
     ("g24_REP", "g24_DEM", "g24_UNAFF", "g24_RminusD"), 0.05),
    ("§IV Nov 2022 general",
     r"\| Nov 2022 general \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| \+([\d.]+) \|",
     ("g22_REP", "g22_DEM", "g22_UNAFF", "g22_RminusD"), 0.05),
    ("§IV May 2024 primary",
     r"\| \*\*May 2024 primary\*\* \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \| ([\d.]+)% \| "
     r"\*\*\+([\d.]+)\*\* \|", ("p24_REP", "p24_DEM", "p24_UNAFF", "p24_RminusD"), 0.05),
    ("§IV May 2022 primary",
     r"\| \*\*May 2022 primary\*\* \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \| ([\d.]+)% \| "
     r"\*\*\+([\d.]+)\*\* \|", ("p22_REP", "p22_DEM", "p22_UNAFF", "p22_RminusD"), 0.05),
    ("§IV registration baseline row",
     r"\| — Registration baseline \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| \+([\d.]+) \|",
     ("roll_REP", "roll_DEM", "roll_UNAFF", "roll_RminusD"), 0.05),
    ("§IV Republican share of primary ballots, across every cycle on file",
     r"\*\*(\d+)–(\d+)% of every primary ballot cast in Idaho is a Republican ballot\*\* — the\s+"
     r"range spans every primary cycle in the file, from ([\d.]+)% in 2026 to ([\d.]+)% in 2022",
     ("ballot_lo", "ballot_hi", "ballot_lo", "ballot_hi"), 0.5),
    ("§IV contested Republican legislative primaries",
     r"\*\*(\d+) drew a Republican primary in 2024\*\*.*?of those \d+, just \*\*(\d+) \((\d+)%\) "
     r"were contested\*\* and \*\*(\d+) \((\d+)%\) had a single Republican",
     ("prim_races", "prim_contested", "prim_contested_pct", "prim_single", "prim_single_pct"),
     0.5),

    # ---- Section V
    ("§V legislative districts by registration lean",
     r"the (\d+) Solid-R", "ld_safe_r", 0),
]

UNCHECKED = [
    "The donor layer (§VII) — asserted against the databases by verify_donor_class.py, which "
    "owns the matched panels and their tier specification",
    "Turnout RATES — deliberately absent from the paper. Idaho's roll is a current extract "
    "that shrank 1.18M to 1.03M since 2024, so any rate is survivorship-inflated; the paper "
    "reports composition shares, which are denominator-free, and so does this script",
    "The Das-Gupta decomposition and the Ballotpedia contested-count reconciliation — "
    "scripts/diag_id_primary_contested.py owns the second and the paper reports the first "
    "qualitatively, without a figure to assert",
]


def main() -> int:
    return vp.run("WHO DECIDES IDAHO — prose scraped and asserted against the voter file",
                  vp.normalise(PAPER.read_text(encoding="utf-8")),
                  PROBES, derive(), UNCHECKED, vp.wants_coverage())


if __name__ == "__main__":
    raise SystemExit(main())
