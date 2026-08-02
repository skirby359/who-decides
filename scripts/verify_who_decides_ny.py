"""Independent re-derivation of docs/who-decides-new-york.md, asserted against its prose.

CONVERTED TO AN ASSERTING VERIFIER 2026-08-01. It passes; the two blocks that did not were
recomputed the same day, and the record of why is below because the cause will recur.

This script previously printed derived values beside hand-typed "(paper: ...)" annotations
and returned None, so it always exited 0. Two of those annotations were themselves stale —
the roll party mix was captioned "paper ~: DEM 47.8 / NOPARTY 25.1 / REP 22.3" while the
paper says 25.3% of the active roll, which is exactly what the data gives. A human comparing
the two columns would have "confirmed" a mismatch that did not exist, and missed the ones
that do.

WHAT THE CONVERSION FOUND, and how it was resolved. Section III's table and Section IV's
participation rates did not reproduce on the roll as it stands, on either the active or the
full basis, and every deviation ran one way: the roll is younger and less participating than
the one those tables were computed on. Section VI supplies the mechanism — registrants added
since are 39.7% Democratic and 35.6% unaffiliated against a roll at 47.6% and 25.3%, and by
definition none of them voted in 2024.

The decisive evidence was WHICH blocks failed. Sections I and II are ELECTORATE-denominated —
the set of people who voted in a past election cannot change when registrants are added — and
all thirty-nine of their cells reproduced exactly. Sections III and IV are ROLL-denominated
and every cell was off. The split fell precisely on the denominator, which is what a roll
change looks like and is not what a coding error looks like.

Both blocks were recomputed on the current active roll on 2026-08-01 and the paper now states
the direction and cause. The donors-per-thousand column moved for a second, unrelated reason:
it was still built on the pre-2026-07-27 New York match (308,032) rather than the full-name
key now used across the series (558,017). No finding changed in either case.

WHAT WAS NOT CLAIMED, and still is not. Which roll snapshot the original tables were computed
on is not recoverable from the artifacts, and this script never asserted it.
`data/ny_vrdb.duckdb` was last written 2026-07-30, the day of the date-of-birth minimisation,
but the minimisation cannot produce this: `date_diff('year', ...)` returns the difference of
year parts, so it read the birth YEAR before and after — which is why the donor paper's twelve
New York age-band figures came through it identical to six decimal places. Ask the author
rather than inferring it from file timestamps.

CLOSED THE SAME DAY: NEW YORK'S ROLL IS NOW PINNED. It had none, on the assumption that a
static FOIL extract cannot move. It moved. `scripts/pin_ny_roll.py` freezes it the way
Washington's is — `ny_paper_roll`, 2026-08-01, 13,540,505 registrants of whom 12,448,034 are
active — and every roll-denominated derivation below reads that snapshot rather than `voters`.
Sections I and II still read `voters` directly and correctly: they are electorate-denominated
and cannot drift.

The pin is the DENOMINATOR only. Participation is still joined live from
`voter_participation`, because past elections do not change, and the donor panel is still
joined live from `ny_statewide`, because its specification belongs to the donor paper and
freezing a copy here would let the two diverge silently.

A byproduct worth knowing: NYSVOTER carries **53 state_voter_ids twice** (36 among active
registrants), and they are not duplicate copies — 8 disagree on party, 25 on congressional
district, 1 on birth year. The snapshot collapses them deterministically, so the pinned roll
is 13,540,505 registrants against 13,540,558 rows. Nothing printed moves — 53 in 13.5 million
is four orders of magnitude below the paper's precision — but the paper's counts are ROW
counts and this file's are now registrant counts, which is the honest basis for a roll.

Hits data/ny_vrdb.duckdb DIRECTLY with from-scratch SQL, not by importing the diag scripts.
Read-only; AGGREGATE OUTPUT ONLY — NYSVOTER carries personal data under FOIL lawful-use
terms and this script must never emit a row.

Run:  python scripts/verify_who_decides_ny.py [--coverage]
"""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _verify_prose as vp  # noqa: E402

vp.stdout_utf8()

VRDB = str(vp.DATA / "ny_vrdb.duckdb")
PAPER = vp.DOCS / "who-decides-new-york.md"

PIN = "ny_paper_roll"
BANDS = ["18-29", "30-44", "45-64", "65+"]
PARTY = ("CASE WHEN party='DEM' THEN 'DEM' WHEN party='REP' THEN 'REP' "
         "WHEN party='BLK' THEN 'NOPARTY' ELSE 'OTHER' END")
GENERALS = [("2024-11-05", 2024, "g24"), ("2022-11-08", 2022, "g22"),
            ("2025-11-04", 2025, "g25"), ("2023-11-07", 2023, "g23")]


def _require_pin(con) -> None:
    """Fail loudly if the snapshot is absent rather than falling back to the live roll."""
    have, = con.execute("SELECT COUNT(*) FROM information_schema.tables "
                        "WHERE table_name = ?", [PIN]).fetchone()
    if not have:
        raise SystemExit(
            f"FATAL: {PIN} is missing. Sections III and IV are roll-denominated and drift "
            f"without it.\n  Create it with:  python scripts/pin_ny_roll.py")


def _age(date: str) -> str:
    return f"date_diff('year', v.birthdate, DATE '{date}')"


def _band(date: str) -> str:
    a = _age(date)
    return (f"CASE WHEN {a}<30 THEN '18-29' WHEN {a}<45 THEN '30-44' "
            f"WHEN {a}<65 THEN '45-64' ELSE '65+' END")


def _voted(year: int, kind: str = "GENERAL") -> str:
    return (f"JOIN (SELECT DISTINCT state_voter_id FROM voter_participation "
            f"WHERE election_year={year} AND kind='{kind}') p USING (state_voter_id)")


def derive() -> dict:
    d: dict = {"_prev_panel": 308_032}   # the retired match size the recompute note cites
    con = duckdb.connect(VRDB, read_only=True)

    # ROLL-DENOMINATED CUTS READ THE PIN. See the docstring: `voters` drifts on reload and
    # took sections III and IV with it. `_require_pin` fails loudly rather than falling back,
    # because a silent fallback would reproduce the exact defect the pin exists to prevent.
    _require_pin(con)
    d["roll_all"], d["roll_active"] = con.execute(
        f"SELECT COUNT(*), COUNT(*) FILTER (WHERE is_active) FROM {PIN}").fetchone()
    d["roll_m"] = d["roll_all"] / 1e6

    # Party mix, both bases — the paper states the blank share on each.
    for tag, filt in (("mixA", "WHERE is_active"), ("mixF", "")):
        rows = con.execute(f"SELECT party, COUNT(*) FROM {PIN} {filt} GROUP BY 1").fetchall()
        tot = sum(n for _, n in rows) or 1
        for p, n in rows:
            d[f"{tag}_{p}"] = 100.0 * n / tot

    # Section I — age composition of each general electorate.
    for date, year, tag in GENERALS:
        rows = con.execute(f"""
            WITH e AS (SELECT {_band(date)} b FROM voters v {_voted(year)}
                       WHERE v.birthdate IS NOT NULL AND {_age(date)} BETWEEN 18 AND 105)
            SELECT b, COUNT(*) FROM e GROUP BY 1""").fetchall()
        counts = {b: 0 for b in BANDS}
        for b, n in rows:
            counts[b] = n
        tot = sum(counts.values()) or 1
        for b in BANDS:
            d[f"{tag}_{b}"] = 100.0 * counts[b] / tot
        d[f"{tag}_median"], = con.execute(f"""
            SELECT median({_age(date)}) FROM voters v {_voted(year)}
            WHERE v.birthdate IS NOT NULL AND {_age(date)} BETWEEN 18 AND 105""").fetchone()

    # Section II — 65+ share by party, per cycle, plus the 2025 median-age split.
    for date, year, tag in GENERALS:
        rows = con.execute(f"""
            WITH e AS (SELECT {PARTY} p, {_age(date)} a FROM voters v {_voted(year)}
                       WHERE v.birthdate IS NOT NULL AND {_age(date)} BETWEEN 18 AND 105)
            SELECT p, 100.0*COUNT(*) FILTER (WHERE a>=65)/COUNT(*), median(a)
            FROM e GROUP BY 1""").fetchall()
        for p, p65, med in rows:
            d[f"{tag}_{p}_65"], d[f"{tag}_{p}_median"] = float(p65), float(med)

    # Section III — the blank bloc, over the PINNED active roll, with 2024 turnout attached.
    # Age is 2024 minus birth year, which is what date_diff('year', ...) returned on the live
    # table too — the paper's stated convention, unchanged by the pin.
    rows = con.execute(f"""
        WITH e AS (
            SELECT v.party p, 2024 - v.birth_year a,
                   CASE WHEN v.state_voter_id IN (
                        SELECT DISTINCT state_voter_id FROM voter_participation
                        WHERE election_year=2024 AND kind='GENERAL') THEN 1 ELSE 0 END v24
            FROM {PIN} v WHERE v.is_active AND v.birth_year IS NOT NULL)
        SELECT p, median(a), 100.0*COUNT(*) FILTER (WHERE a>=65)/COUNT(*),
               100.0*COUNT(*) FILTER (WHERE a<30)/COUNT(*), 100.0*SUM(v24)/COUNT(*)
        FROM e GROUP BY 1""").fetchall()
    for p, med, p65, p1829, turn in rows:
        d[f"bloc_{p}_median"], d[f"bloc_{p}_65"] = float(med), float(p65)
        d[f"bloc_{p}_1829"], d[f"bloc_{p}_turn"] = float(p1829), float(turn)

    # Section IV — closed-primary participation, as a share of each party's registrants.
    # New York's presidential primary is a distinct `kind`, so the paper's four rows are four
    # different contests rather than three; grouping by year alone would silently merge the
    # April presidential and June state primaries into one 2024 figure.
    for year, tag in ((2024, "ppres24"), (2024, "pp24"), (2022, "pp22"), (2021, "pp21")):
        kind = "PRES_PRIMARY" if tag == "ppres24" else "PRIMARY"
        rows = con.execute(f"""
            WITH reg AS (SELECT party p, state_voter_id FROM {PIN} WHERE is_active),
                 voted AS (SELECT DISTINCT state_voter_id FROM voter_participation
                           WHERE election_year={year} AND kind='{kind}')
            SELECT p, 100.0*COUNT(*) FILTER (
                     WHERE state_voter_id IN (SELECT state_voter_id FROM voted))/COUNT(*)
            FROM reg GROUP BY 1""").fetchall()
        for p, v in rows:
            d[f"{tag}_{p}"] = float(v)

    # Section III's donor column: matched donors per 1,000 active registrants of each party.
    # The PANEL is the donor paper's (full-name key, 558,017 New York voters) and that paper
    # asserts its size; the RATIO is this paper's and is derived here. Probing it rather than
    # exempting it is what caught the column still sitting on the retired 308,032 match.
    con.execute(f"ATTACH '{vp.DATA / 'ny_statewide.duckdb'}' AS sw (READ_ONLY)")
    d["panel_n"], = con.execute(
        "SELECT COUNT(DISTINCT state_voter_id) FROM sw.voter_donor_affiliation").fetchone()
    for p, per in con.execute(f"""
        SELECT v.party,
               1000.0 * COUNT(DISTINCT CASE WHEN a.state_voter_id IS NOT NULL
                                            THEN v.state_voter_id END) / COUNT(*)
        FROM {PIN} v
        LEFT JOIN sw.voter_donor_affiliation a ON a.state_voter_id = v.state_voter_id
        WHERE v.is_active GROUP BY 1""").fetchall():
        d[f"bloc_{p}_donors"] = float(per)

    # Section V — districts banded by registration lean, active roll. Reads `voters`, not the
    # pin: the pin deliberately carries no district column, and §V's cells are integer district
    # COUNTS that a 36-registrant change cannot move.
    for col, tag in (("congressional_district", "cd"), ("assembly_district", "ad")):
        row = con.execute(f"""
            WITH dd AS (
                SELECT {col} dist,
                       100.0*COUNT(*) FILTER (WHERE party='DEM')/COUNT(*)
                       - 100.0*COUNT(*) FILTER (WHERE party='REP')/COUNT(*) net
                FROM voters WHERE status_code='A' AND {col} IS NOT NULL AND {col}<>''
                GROUP BY 1)
            SELECT COUNT(*) FILTER (WHERE net>=40), COUNT(*) FILTER (WHERE net>=20 AND net<40),
                   COUNT(*) FILTER (WHERE net>=5 AND net<20),
                   COUNT(*) FILTER (WHERE net>-5 AND net<5),
                   COUNT(*) FILTER (WHERE net<=-5 AND net>-20),
                   COUNT(*) FILTER (WHERE net<=-20), COUNT(*) FROM dd""").fetchone()
        for k, v in zip(("safe_d", "likely_d", "lean_d", "comp", "lean_r", "safe_r", "n"), row):
            d[f"{tag}_{k}"] = v

    # Section VI — party mix of each registration cohort.
    for year in (2008, 2016, 2020, 2024):
        rows = con.execute(f"""
            SELECT {PARTY}, COUNT(*) FROM voters
            WHERE year(registration_date)={year} GROUP BY 1""").fetchall()
        tot = sum(n for _, n in rows) or 1
        for p, n in rows:
            d[f"new{year}_{p}"] = 100.0 * n / tot
        d[f"new{year}_median"], = con.execute(f"""
            SELECT median(date_diff('year', birthdate, registration_date)) FROM voters
            WHERE year(registration_date)={year} AND birthdate IS NOT NULL""").fetchone()
    con.close()
    return d


PROBES = [
    ("roll size", r"statewide file \(([\d.]+)M registrants", "roll_m", 0.005),
    ("blank share, active and full roll",
     r"\(([\d.]+)% of the active roll; ([\d.]+)% of the full roll\)",
     ("mixA_NOPARTY", "mixF_NOPARTY"), 0.05),

    # ---- Section I
    ("§I Nov 2024 presidential",
     r"\| Nov 2024 \| Presidential \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \| ([\d.]+)% \| "
     r"([\d.]+)% \| (\d+) \|",
     ("g24_18-29", "g24_30-44", "g24_45-64", "g24_65+", "g24_median"), 0.05),
    ("§I Nov 2022 midterm",
     r"\| Nov 2022 \| Midterm \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| (\d+) \|",
     ("g22_18-29", "g22_30-44", "g22_45-64", "g22_65+", "g22_median"), 0.05),
    ("§I Nov 2025 off-year",
     r"\| Nov 2025 \| Off-year \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| (\d+) \|",
     ("g25_18-29", "g25_30-44", "g25_45-64", "g25_65+", "g25_median"), 0.05),
    ("§I Nov 2023 off-year",
     r"\| Nov 2023 \| Off-year \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \| ([\d.]+)% \| "
     r"\*\*([\d.]+)%\*\* \| (\d+) \|",
     ("g23_18-29", "g23_30-44", "g23_45-64", "g23_65+", "g23_median"), 0.05),

    # ---- Section II
    ("§II 65+ by party, 2024 presidential",
     r"\| Nov 2024 \(pres\) \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \|",
     ("g24_DEM_65", "g24_REP_65", "g24_NOPARTY_65", "g24_OTHER_65"), 0.05),
    ("§II 65+ by party, 2025 odd-year",
     r"\| Nov 2025 \(odd\) \| ([\d.]+)% \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \| ([\d.]+)% \|",
     ("g25_DEM_65", "g25_REP_65", "g25_NOPARTY_65", "g25_OTHER_65"), 0.05),
    ("§II 65+ by party, 2023 odd-year",
     r"\| Nov 2023 \(odd\) \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \|",
     ("g23_DEM_65", "g23_REP_65", "g23_NOPARTY_65", "g23_OTHER_65"), 0.05),

    # ---- Section III (see the module docstring: this block is the open discrepancy)
    ("§III blank bloc, DEM",
     r"\| DEM \| (\d+) \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+) \|",
     ("bloc_DEM_median", "bloc_DEM_65", "bloc_DEM_1829", "bloc_DEM_turn",
      "bloc_DEM_donors"), 0.05),
    ("§III blank bloc, REP",
     r"\| REP \| (\d+) \| ([\d.]+)% \| ([\d.]+)% \| \*\*([\d.]+)%\*\* \| ([\d.]+) \|",
     ("bloc_REP_median", "bloc_REP_65", "bloc_REP_1829", "bloc_REP_turn",
      "bloc_REP_donors"), 0.05),
    ("§III blank bloc, NOPARTY",
     r"\| NOPARTY \| \*\*(\d+)\*\* \| ([\d.]+)% \| \*\*([\d.]+)%\*\* \| \*\*([\d.]+)%\*\* \| "
     r"\*\*([\d.]+)\*\* \|",
     ("bloc_NOPARTY_median", "bloc_NOPARTY_65", "bloc_NOPARTY_1829", "bloc_NOPARTY_turn",
      "bloc_NOPARTY_donors"), 0.05),
    ("§IV recompute note — the two match sizes it names",
     r"pre-2026-07-27 New York match \((\d[\d,]*) voters\) rather than the full-name-key\s+"
     r"specification now used throughout the series \((\d[\d,]*)\)",
     ("_prev_panel", "panel_n"), 0),

    # ---- Section IV
    ("§IV 2024 presidential primary",
     r"\| 2024 Presidential \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \|",
     ("ppres24_DEM", "ppres24_REP", "ppres24_NOPARTY", "ppres24_OTHER"), 0.05),
    ("§IV 2024 state/congressional primary",
     r"\| 2024 State/Congress \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \|",
     ("pp24_DEM", "pp24_REP", "pp24_NOPARTY", "pp24_OTHER"), 0.05),
    ("§IV 2022 state/congressional primary",
     r"\| 2022 State/Congress \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \|",
     ("pp22_DEM", "pp22_REP", "pp22_NOPARTY", "pp22_OTHER"), 0.05),
    ("§IV 2021 odd-year primary",
     r"\| 2021 \(odd-year\) \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \|",
     ("pp21_DEM", "pp21_REP", "pp21_NOPARTY", "pp21_OTHER"), 0.05),

    # ---- Section V
    ("§V congressional districts by lean",
     r"\| Congressional \(26\) \| (\d+) \| (\d+) \| (\d+) \| \*\*(\d+)\*\* \| (\d+) \| (\d+) \|",
     ("cd_safe_d", "cd_likely_d", "cd_lean_d", "cd_comp", "cd_lean_r", "cd_safe_r"), 0),
    ("§V assembly districts by lean",
     r"\| Assembly \(150\) \| (\d+) \| (\d+) \| (\d+) \| \*\*(\d+)\*\* \| (\d+) \| (\d+) \|",
     ("ad_safe_d", "ad_likely_d", "ad_lean_d", "ad_comp", "ad_lean_r", "ad_safe_r"), 0),

    # ---- Section VI
    ("§VI 2008 registration cohort",
     r"\| 2008 \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| (\d+) \|",
     ("new2008_DEM", "new2008_REP", "new2008_NOPARTY", "new2008_median"), 0.05),
    ("§VI 2016 registration cohort",
     r"\| 2016 \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| (\d+) \|",
     ("new2016_DEM", "new2016_REP", "new2016_NOPARTY", "new2016_median"), 0.05),
    ("§VI 2020 registration cohort",
     r"\| 2020 \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| (\d+) \|",
     ("new2020_DEM", "new2020_REP", "new2020_NOPARTY", "new2020_median"), 0.05),
    ("§VI 2024 registration cohort",
     r"\| 2024 \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \| \*\*([\d.]+)%\*\* \| (\d+) \|",
     ("new2024_DEM", "new2024_REP", "new2024_NOPARTY", "new2024_median"), 0.05),
]

UNCHECKED = [
    "Turnout RATES carry the paper's own survivorship caveat: the denominator is the roll as "
    "it stands, which includes registrants who could not have voted in an earlier election. "
    "That caveat is the subject of the open discrepancy in this module's docstring",
]


def main() -> int:
    return vp.run("WHO DECIDES NEW YORK — prose scraped and asserted against the voter file",
                  vp.normalise(PAPER.read_text(encoding="utf-8")),
                  PROBES, derive(), UNCHECKED, vp.wants_coverage())


if __name__ == "__main__":
    raise SystemExit(main())
