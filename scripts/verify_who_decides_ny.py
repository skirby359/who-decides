"""Independent re-derivation of docs/who-decides-new-york.md, asserted against its prose.

CONVERTED TO AN ASSERTING VERIFIER 2026-08-01. It passes; the two blocks that did not were
recomputed the same day, and the record of why is below because the cause will recur.

This script previously printed derived values beside hand-typed "(paper: ...)" annotations
and returned None, so it always exited 0. Two of those annotations were themselves stale —
the roll party mix was captioned "paper ~: DEM 47.8 / NOPARTY 25.1 / REP 22.3" while the
paper says 25.3% of the active roll, which is exactly what the data gives. A human comparing
the two columns would have "confirmed" a mismatch that did not exist, and missed the ones
that do.

SECTION NUMBERS BELOW ARE POST-2026-08-06. The paper was reordered that day to open on its
party-resolved result; the age-composition replication became Appendix A and §II-§VI became
§I-§V. Nothing moved but the order. The paper's own Appendix B carries the map, and it exists
because `electoral-health-audit-log.md` is append-only and cites the OLD numbers — a
pre-2026-08-06 reference to "NY §III/§IV" means what are now §II and §III.

WHAT THE CONVERSION FOUND, and how it was resolved. Section II's table and Section III's
participation rates did not reproduce on the roll as it stands, on either the active or the
full basis, and every deviation ran one way: the roll is younger and less participating than
the one those tables were computed on. Section V supplies the mechanism — registrants added
since are 39.7% Democratic and 35.6% unaffiliated against a roll at 47.6% and 25.3%, and by
definition none of them voted in 2024.

The decisive evidence was WHICH blocks failed. Appendix A and Section I are
ELECTORATE-denominated — the set of people who voted in a past election cannot change when
registrants are added — and all thirty-nine of their cells reproduced exactly. Sections II
and III are ROLL-denominated and every cell was off. The split fell precisely on the
denominator, which is what a roll change looks like and is not what a coding error looks like.

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
Appendix A and Section I still read `voters` directly and correctly: they are
electorate-denominated and cannot drift.

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

import re
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
            f"FATAL: {PIN} is missing. Sections II and III are roll-denominated and drift "
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
    # took sections II and III with it. `_require_pin` fails loudly rather than falling back,
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

    # Appendix A — age composition of each general electorate (the replication).
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

    # Section I — 65+ share by party, per cycle, plus the 2025 median-age split.
    for date, year, tag in GENERALS:
        rows = con.execute(f"""
            WITH e AS (SELECT {PARTY} p, {_age(date)} a FROM voters v {_voted(year)}
                       WHERE v.birthdate IS NOT NULL AND {_age(date)} BETWEEN 18 AND 105)
            SELECT p, 100.0*COUNT(*) FILTER (WHERE a>=65)/COUNT(*), median(a)
            FROM e GROUP BY 1""").fetchall()
        for p, p65, med in rows:
            d[f"{tag}_{p}_65"], d[f"{tag}_{p}_median"] = float(p65), float(med)

    # Section II — the blank bloc, over the PINNED active roll, with 2024 turnout attached.
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

    # Section I — 2025 general under-30 turnout by party. RESTATED 2026-08-06 on §II's
    # convention (the pinned ACTIVE roll, age = election year minus birth_year, participation
    # kind GENERAL), because the printed 30.8 / 15.9 reproduced on none of fourteen bases —
    # see the note at the foot of this file for the full enumeration and why it was a real
    # defect rather than a basis difference. This is the only roll-denominated RATE in an
    # otherwise electorate-denominated section, which is how it survived the 2026-08-01
    # recompute. The live `voters` table agrees with the pin here to 2dp; the pin is used
    # because every other roll-denominated figure in this paper does.
    for p, r in con.execute(f"""
        WITH e AS (
            SELECT v.party p,
                   CASE WHEN v.state_voter_id IN (
                        SELECT DISTINCT state_voter_id FROM voter_participation
                        WHERE election_year=2025 AND kind='GENERAL') THEN 1 ELSE 0 END v25
            FROM {PIN} v
            WHERE v.is_active AND v.birth_year IS NOT NULL AND 2025 - v.birth_year < 30)
        SELECT p, 100.0*SUM(v25)/COUNT(*) FROM e GROUP BY 1""").fetchall():
        d[f"u30_g25_{p}"] = float(r)

    # Section III — closed-primary participation, as a share of each party's registrants.
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

    # Section II's donor column: matched donors per 1,000 active registrants of each party.
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

    # Section IV — districts banded by registration lean, active roll. Reads `voters`, not the
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

    # Section V — party mix of each registration cohort.
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

    # ------------------------------------------------------------------ coverage gate, 2026-08-06
    # Everything below was added to close the audit. Grouped rather than folded into the
    # blocks above so it is obvious which figures the gate forced out of the prose.

    # §IV's prose rolls the banded table up: "19/26 and 105/150 lean Democratic". Derived from
    # the same band counts rather than hard-coded, so a band-boundary change moves both.
    for tag in ("cd", "ad"):
        d[f"{tag}_lean_dem_total"] = (d[f"{tag}_safe_d"] + d[f"{tag}_likely_d"]
                                      + d[f"{tag}_lean_d"])

    # §III's "the 25.3% enrolled blank are structurally absent (~0.1-0.5%)" — the span of
    # NOPARTY participation across the FOUR primaries, min and max, not an eyeballed pair.
    # A range needs both endpoints probed against the right members: asserting against a
    # remembered pair is what left two ranges on the WA paper quoting 2 of 3 off-years.
    npy = [d[f"{t}_NOPARTY"] for t in ("ppres24", "pp24", "pp22", "pp21")]
    d["np_primary_lo"], d["np_primary_hi"] = min(npy), max(npy)

    # §I's "swings from +15.6 (2023) to +33.2 (2025)" — the DEM-REP gap in each odd-year
    # ELECTORATE (shares of actual voters), which is the basis the sentence names. Not the
    # roll gap: on the roll the gap is ~25 points and static, which is the sentence's point.
    for date, year, tag in GENERALS:
        rows = dict(con.execute(f"""
            WITH e AS (SELECT {PARTY} p FROM voters v {_voted(year)})
            SELECT p, 100.0*COUNT(*)/SUM(COUNT(*)) OVER () FROM e GROUP BY 1""").fetchall())
        d[f"{tag}_gap_dr"] = float(rows.get("DEM", 0)) - float(rows.get("REP", 0))
        d[f"{tag}_share_NOPARTY"] = float(rows.get("NOPARTY", 0))

    # Methods: the pin's own guard figure. NYSVOTER carries 53 state_voter_ids twice, so the
    # pin holds 13,540,505 registrants against the file's 13,540,558 ROWS. Both are stated and
    # both must be right — quoting the row count as a registrant count is the defect the pin
    # discovered, and it survives in other documents' "13.54M / 12,448,081".
    d["file_rows"], = con.execute("SELECT COUNT(*) FROM voters").fetchone()

    # Boundary of inference: the parser validation figure, "2024 presidential ~ 7.4M".
    d["turn24_m"], = con.execute("""
        SELECT COUNT(DISTINCT state_voter_id)/1e6 FROM voter_participation
        WHERE election_year=2024 AND kind='GENERAL'""").fetchone()
    con.close()

    _companion_docs(d)
    return d


def _companion_docs(d: dict) -> None:
    """Figures this paper COPIES from a companion document, checked against the source.

    Neither of these is re-derived, and the reason is the same in both cases: re-deriving
    would verify the companion a second time and say nothing about THIS paper. What this
    paper can get wrong is TRANSCRIPTION — a source revised under a citation that was
    right when written. So the source text is the ground truth, the way
    verify_who_returns_ballot.py treats the three single-state papers.

    1. `ny-electorate-extras.md` §3 owns the Das-Gupta rate/composition decomposition.
       Appendix A's
       prose states it as two RANGES and two RATIOS over the three parties, and that
       arithmetic — min, max, and rate/composition per party — is exactly where a summary
       drifts from the table it summarises. Derived from the scraped table, not retyped.
    2. `who-decides-idaho.md` owns the Idaho contrast in §I (of THIS paper; Idaho's own §II). verify_who_decides_id.py
       asserts those cells against the Idaho voter file.
    """
    ex = vp.normalise((vp.DOCS / "ny-electorate-extras.md").read_text(encoding="utf-8"))
    rows = re.findall(r"\| (DEM|REP|NOPARTY) \| ([\d.]+)% \| ([\d.]+)% \| \+[\d.]+ \| "
                      r"\*\*\+([\d.]+)\*\* \| \+([\d.]+) \|", ex)
    if len(rows) == 3:
        base = {p: float(b) for p, b, _, _, _ in rows}
        rate = {p: float(r) for p, _, _, r, _ in rows}
        comp = {p: float(c) for p, _, _, _, c in rows}
        for p in ("DEM", "REP", "NOPARTY"):
            d[f"dg_base_{p}"] = base[p]
        d["dg_rate_lo"], d["dg_rate_hi"] = min(rate.values()), max(rate.values())
        d["dg_comp_lo"], d["dg_comp_hi"] = min(comp.values()), max(comp.values())
        d["dg_ratio_DEM"] = rate["DEM"] / comp["DEM"]
        d["dg_ratio_NOPARTY"] = rate["NOPARTY"] / comp["NOPARTY"]
        # §II's footnote: the all-roll-matched bases run "~0.3pp higher" than §II's own
        # electorate-denominated 2024 row. Derived as the gap between the two tables this
        # script already holds, rather than exempted. Mean of the three, because "higher" is
        # asserted of all three parties (0.3 / 0.3 / 0.2); max prints 0.3 as well, so the
        # figure does not turn on the choice.
        gaps = [base[p] - d[f"g24_{p}_65"] for p in ("DEM", "REP", "NOPARTY")
                if f"g24_{p}_65" in d]
        if len(gaps) == 3:
            d["dg_base_gap"] = sum(gaps) / 3.0
    # The Idaho contrast is a TABLE in the companion (§II), so it is scraped as the adjacent
    # Republican/Democratic pair rather than from prose. Anchoring on the pair matters: the
    # Idaho paper carries several party-labelled tables and a single-row pattern would bind
    # to whichever came first, which is how a probe passes on the wrong number.
    idp = vp.normalise((vp.DOCS / "who-decides-idaho.md").read_text(encoding="utf-8"))
    m = re.search(r"\| Republican \| ([\d.]+)% \| [\d.]+% \| \d+ \| "
                  r"\| Democratic \| ([\d.]+)% \| [\d.]+% \| \d+ \|", idp)
    if m:
        d["id_rep_65"], d["id_dem_65"] = float(m.group(1)), float(m.group(2))


PROBES = [
    ("roll size", r"statewide file \(([\d.]+)M registrants", "roll_m", 0.005),
    ("blank share, active and full roll",
     r"\(([\d.]+)% of the active roll; ([\d.]+)% of the full roll\)",
     ("mixA_NOPARTY", "mixF_NOPARTY"), 0.05),

    # ---- Section I
    ("Appendix A Nov 2024 presidential",
     r"\| Nov 2024 \| Presidential \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \| ([\d.]+)% \| "
     r"([\d.]+)% \| (\d+) \|",
     ("g24_18-29", "g24_30-44", "g24_45-64", "g24_65+", "g24_median"), 0.05),
    ("Appendix A Nov 2022 midterm",
     r"\| Nov 2022 \| Midterm \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| (\d+) \|",
     ("g22_18-29", "g22_30-44", "g22_45-64", "g22_65+", "g22_median"), 0.05),
    ("Appendix A Nov 2025 off-year",
     r"\| Nov 2025 \| Off-year \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| (\d+) \|",
     ("g25_18-29", "g25_30-44", "g25_45-64", "g25_65+", "g25_median"), 0.05),
    ("Appendix A Nov 2023 off-year",
     r"\| Nov 2023 \| Off-year \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \| ([\d.]+)% \| "
     r"\*\*([\d.]+)%\*\* \| (\d+) \|",
     ("g23_18-29", "g23_30-44", "g23_45-64", "g23_65+", "g23_median"), 0.05),

    # ---- Section II
    ("§I 65+ by party, 2024 presidential",
     r"\| Nov 2024 \(pres\) \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \|",
     ("g24_DEM_65", "g24_REP_65", "g24_NOPARTY_65", "g24_OTHER_65"), 0.05),
    ("§I 65+ by party, 2025 odd-year",
     r"\| Nov 2025 \(odd\) \| ([\d.]+)% \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \| ([\d.]+)% \|",
     ("g25_DEM_65", "g25_REP_65", "g25_NOPARTY_65", "g25_OTHER_65"), 0.05),
    ("§I 65+ by party, 2023 odd-year",
     r"\| Nov 2023 \(odd\) \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \|",
     ("g23_DEM_65", "g23_REP_65", "g23_NOPARTY_65", "g23_OTHER_65"), 0.05),
    # Replaces the exemption that held the retired 30.8 / 15.9 pair (see the note at the
    # foot of this file). The sentence now names its own basis, so the probe can be exact.
    ("§I 2025 general under-30 turnout by party",
     r"Democratic\s+under-30 turnout \(([\d.]+)%\) was nearly \*\*double\*\* "
     r"Republican \(([\d.]+)%\)",
     ("u30_g25_DEM", "u30_g25_REP"), 0.05),

    # ---- Section III (see the module docstring: this block is the open discrepancy)
    ("§II blank bloc, DEM",
     r"\| DEM \| (\d+) \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+) \|",
     ("bloc_DEM_median", "bloc_DEM_65", "bloc_DEM_1829", "bloc_DEM_turn",
      "bloc_DEM_donors"), 0.05),
    ("§II blank bloc, REP",
     r"\| REP \| (\d+) \| ([\d.]+)% \| ([\d.]+)% \| \*\*([\d.]+)%\*\* \| ([\d.]+) \|",
     ("bloc_REP_median", "bloc_REP_65", "bloc_REP_1829", "bloc_REP_turn",
      "bloc_REP_donors"), 0.05),
    ("§II blank bloc, NOPARTY",
     r"\| NOPARTY \| \*\*(\d+)\*\* \| ([\d.]+)% \| \*\*([\d.]+)%\*\* \| \*\*([\d.]+)%\*\* \| "
     r"\*\*([\d.]+)\*\* \|",
     ("bloc_NOPARTY_median", "bloc_NOPARTY_65", "bloc_NOPARTY_1829", "bloc_NOPARTY_turn",
      "bloc_NOPARTY_donors"), 0.05),
    ("§III recompute note — the two match sizes it names",
     r"pre-2026-07-27 New York match \((\d[\d,]*) voters\) rather than the full-name-key\s+"
     r"specification now used throughout the series \((\d[\d,]*)\)",
     ("_prev_panel", "panel_n"), 0),

    # ---- Section IV
    ("§III 2024 presidential primary",
     r"\| 2024 Presidential \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \|",
     ("ppres24_DEM", "ppres24_REP", "ppres24_NOPARTY", "ppres24_OTHER"), 0.05),
    ("§III 2024 state/congressional primary",
     r"\| 2024 State/Congress \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \|",
     ("pp24_DEM", "pp24_REP", "pp24_NOPARTY", "pp24_OTHER"), 0.05),
    ("§III 2022 state/congressional primary",
     r"\| 2022 State/Congress \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \|",
     ("pp22_DEM", "pp22_REP", "pp22_NOPARTY", "pp22_OTHER"), 0.05),
    ("§III 2021 odd-year primary",
     r"\| 2021 \(odd-year\) \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \|",
     ("pp21_DEM", "pp21_REP", "pp21_NOPARTY", "pp21_OTHER"), 0.05),

    # ---- Section V
    ("§IV congressional districts by lean",
     r"\| Congressional \(26\) \| (\d+) \| (\d+) \| (\d+) \| \*\*(\d+)\*\* \| (\d+) \| (\d+) \|",
     ("cd_safe_d", "cd_likely_d", "cd_lean_d", "cd_comp", "cd_lean_r", "cd_safe_r"), 0),
    ("§IV assembly districts by lean",
     r"\| Assembly \(150\) \| (\d+) \| (\d+) \| (\d+) \| \*\*(\d+)\*\* \| (\d+) \| (\d+) \|",
     ("ad_safe_d", "ad_likely_d", "ad_lean_d", "ad_comp", "ad_lean_r", "ad_safe_r"), 0),

    # ---- Section VI
    ("§V 2008 registration cohort",
     r"\| 2008 \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| (\d+) \|",
     ("new2008_DEM", "new2008_REP", "new2008_NOPARTY", "new2008_median"), 0.05),
    ("§V 2016 registration cohort",
     r"\| 2016 \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| (\d+) \|",
     ("new2016_DEM", "new2016_REP", "new2016_NOPARTY", "new2016_median"), 0.05),
    ("§V 2020 registration cohort",
     r"\| 2020 \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| (\d+) \|",
     ("new2020_DEM", "new2020_REP", "new2020_NOPARTY", "new2020_median"), 0.05),
    ("§V 2024 registration cohort",
     r"\| 2024 \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \| \*\*([\d.]+)%\*\* \| (\d+) \|",
     ("new2024_DEM", "new2024_REP", "new2024_NOPARTY", "new2024_median"), 0.05),

    # ---- added 2026-08-06 by the coverage gate ------------------------------------------
    # §I's Das-Gupta summary, checked against the table it summarises (see _companion_docs).
    ("Appendix A decomposition — rate-effect range across the three parties",
     r"rate effect \*\*\+([\d.]+) to \+([\d.]+) pts\*\*",
     ("dg_rate_lo", "dg_rate_hi"), 0.05),
    ("Appendix A decomposition — composition-effect range",
     r"vs composition \+([\d.]+) to \+([\d.]+),", ("dg_comp_lo", "dg_comp_hi"), 0.05),
    ("Appendix A decomposition — the two named rate/composition ratios",
     r"a ([\d.]+)× ratio for Democrats up to ([\d.]+)× for the unaffiliated",
     ("dg_ratio_DEM", "dg_ratio_NOPARTY"), 0.05),
    ("§I footnote — all-roll-matched 2024 bases",
     r"2024 presidential row \(DEM ([\d.]+) / REP ([\d.]+) / NOPARTY ([\d.]+)\)",
     ("dg_base_DEM", "dg_base_REP", "dg_base_NOPARTY"), 0.05),
    ("§I — the Idaho contrast (vs who-decides-idaho.md §II)",
     r"65\+ share ([\d.]+)% vs ([\d.]+)% in 2024", ("id_dem_65", "id_rep_65"), 0.05),
    ("§I — DEM−REP electorate gap, 2023 then 2025",
     r"swings from \+([\d.]+) \(2023\) to \+([\d.]+) \(2025\)",
     ("g23_gap_dr", "g25_gap_dr"), 0.05),
    ("§III — the blank share and its primary-participation span",
     r"the \*\*([\d.]+)% enrolled \"blank\" are structurally absent\*\* \(≈([\d.]+)–([\d.]+)%",
     ("mixA_NOPARTY", "np_primary_lo", "np_primary_hi"), 0.05),
    ("§I footnote — the all-roll-matched bases run this much higher",
     r"NOPARTY [\d.]+\), ~([\d.]+)pp higher", "dg_base_gap", 0.05),
    ("§IV — Assembly chamber size, three restatements",
     r"\| Assembly \((\d+)\) \|", "ad_n", 0),
    ("§IV — Assembly size in the competitive-count sentence",
     r"17 of (\d+) Assembly districts", "ad_n", 0),
    ("§IV — Assembly size in the lean-Democratic sentence",
     r"105/(\d+) lean Democratic", "ad_n", 0),
    ("§III — the decisive-contest restatement, 2021 then 2024",
     r"2021 odd-year DEM ([\d.]+)% vs REP ([\d.]+)%; 2024 state DEM ([\d.]+)% vs REP ([\d.]+)%",
     ("pp21_DEM", "pp21_REP", "pp24_DEM", "pp24_REP"), 0.05),
    ("recompute note — new-registrant mix against the roll mix",
     r"Recent registrants are ([\d.]+)% Democratic and ([\d.]+)% unaffiliated against a roll "
     r"at ([\d.]+)% and ([\d.]+)%",
     ("new2024_DEM", "new2024_NOPARTY", "mixA_DEM", "mixA_NOPARTY"), 0.05),
    ("recompute note — the CURRENT side of the two primary-rate arrows",
     r"\(16\.9 → ([\d.]+) and 17\.9 → ([\d.]+)\)", ("pp21_DEM", "pp22_DEM"), 0.05),
    ("§IV — districts leaning Democratic, congressional then assembly",
     r"([\d]+)/26 and ([\d]+)/150 lean Democratic",
     ("cd_lean_dem_total", "ad_lean_dem_total"), 0),
    ("§I — NOPARTY roll share against its share of voters",
     r"\(([\d.]+)% of the roll, but only 16–22% of voters\)", "mixF_NOPARTY", 0.05),
    ("Methods — the pin against the file's ROW count",
     r"holds ([\d,]+) registrants against the file's ([\d,]+) rows",
     ("roll_all", "file_rows"), 0),
    ("Methods — the pin's registrant and active counts",
     r"taken 2026-08-01 at ([\d,]+) registrants, of whom ([\d,]+) are active",
     ("roll_all", "roll_active"), 0),
    ("Boundary — parser validation against known 2024 turnout",
     r"2024 presidential ≈ ([\d.]+)M", "turn24_m", 0.05),
    ("abstract — roll scale restated",
     r"individual-record measurement on ([\d.]+)M New York", "roll_m", 0.05),
]

UNCHECKED = [
    "Turnout RATES carry the paper's own survivorship caveat: the denominator is the roll as "
    "it stands, which includes registrants who could not have voted in an earlier election. "
    "That caveat is the subject of the open discrepancy in this module's docstring",
    "The Das-Gupta rate/composition decomposition ITSELF — ny-electorate-extras.md §3 owns "
    "it. This script checks that Appendix A's prose is a faithful summary of that table (ranges and "
    "ratios derived from the scraped cells), which is where a summary of a revised table "
    "drifts; it does not re-implement the decomposition",
]


# --- Coverage gate (ported 2026-08-06; see verify_who_decides_wa for the three rules) ----
# Sections I-V, Boundary, and the Appendix A replication. Partitioned so no
# slice overlaps another: spans are per-section coordinates, so a slice that swallows another
# reports the inner one's probed cells as unmapped. The §IV slice deliberately runs to §V so
# that it contains the recompute blockquote, which is where the roll-drift figures live.
# REORDERED 2026-08-06. The paper now opens on its party-resolved result and the
# age-composition replication moved to Appendix A, so every anchor below shifted by one and
# the old §I became an appendix at the end of the document. `slice_with_offset` raised on the
# stale anchor the first time the restructured paper was verified, which is the behaviour to
# keep: a silent slice would have audited the wrong text. Appendix B carries the old->new map.
AUDIT_BOUNDS = {
    "party":      ("## I. The graying is not partisan-neutral",
                   "## II. The unaffiliated quarter"),
    "blank_bloc": ("## II. The unaffiliated quarter", "## III. The nominating electorate"),
    "nominating": ("## III. The nominating electorate", "## IV. Safe-seat New York"),
    "safe_seat":  ("## IV. Safe-seat New York", "## V. A leading indicator"),
    "registrants": ("## V. A leading indicator", "## Boundary of inference"),
    "boundary":   ("## Boundary of inference", "## What it means"),
    # The replication, now an appendix. Audited exactly as it was when it led the paper —
    # moving a section must not be a way to stop checking it.
    "appendix_a": ("## Appendix A — Validation", "## Appendix B — Section numbering"),
}

COVERAGE_EXEMPT = [
    (r"^(?:19|20)\d{2}$", "a calendar year, not a result"),
    (r"^\d{1,2}$", "small integer — chamber sizes, band edges, list ordinals"),
]

COVERAGE_EXEMPT_LITERAL: dict[str, str] = {
    # The recompute note's before/after DELTAS and the retired left-hand sides of its two
    # arrows. These describe a state of the roll that no longer exists, so they are history
    # in the sense the corrections ledger is: re-deriving them would need the pre-2026-08-01
    # file. The CURRENT side of each arrow IS asserted, one probe above.
    "16.9": "retired 2021 DEM primary rate, pre-recompute; the 14.3 it fell to is asserted",
    "17.9": "retired 2022 DEM primary rate, pre-recompute; the 15.6 it fell to is asserted",
    "0.6": "lower bound of the recompute's turnout-rate fall (0.6-1.1 pts). A DELTA against "
           "a roll state that no longer exists on disk; the post-recompute rates themselves "
           "are all asserted in §III and §IV",
    "1.1": "upper bound of the same fall; as above",
    "0.7": "lower bound of the recompute's youth-share rise (0.7-1.6 pts); as above",
    "1.6": "upper bound of the same rise; as above. NB the same token is a §IV table cell "
           "(2024 state REP 1.6%) and IS asserted there — this exemption only reaches the "
           "occurrences the probes do not cover",
}

# --- ✅ RESOLVED 2026-08-06 — author answered "paper not yet published, so fix" ----------
# The pair now reads 31.5 / 16.1 and IS PROBED (see "§I 2025 general under-30 turnout by
# party" above), computed on §II's own convention: pinned ACTIVE roll, age = election year
# minus birth_year, participation kind GENERAL — the first row of the enumeration below.
# The sentence also now names that basis in the paper, which is what made a probe possible.
# The two exemptions this block used to install are deleted; the enumeration is KEPT,
# because the reason the old pair could not be reproduced is the useful part of the record.
#
# What it used to say — "in the 2025 general, Democratic under-30 turnout (30.8%) was
# nearly **double** Republican (15.9%)":
#
# This is a ROLL-denominated turnout rate sitting inside an otherwise ELECTORATE-denominated
# section — the one figure in §II that the 2026-08-01 recompute would have had to touch, and
# the note says §II's "thirty-nine cells" all reproduced, which counts table cells only.
#
# FOURTEEN bases enumerated 2026-08-06. None reproduces 30.8 / 15.9:
#
#   pin active, <30 (2025-birth_year)               31.53 / 16.07
#   pin active, 18-29                               31.95 / 16.44
#   pin FULL roll, <30                              28.83 / 14.36
#   pin FULL roll, 18-29                            29.88 / 15.56
#   pin active, <30 measured 2026-birth_year        30.95 / 15.81   <- closest
#   pin active, <30 measured 2024-birth_year        31.95 / 16.28
#   live voters active, date_diff age at 2025-11-04 31.53 / 16.07
#   live voters FULL roll, date_diff                28.83 / 14.36
#   live voters FULL roll, date_diff 18-29          29.88 / 15.56
#   live voters status A or I                       29.67 / 15.27
#   live active, registered on/before 2025-11-04    32.84 / 16.63
#   live all statuses, registered on/before         30.35 / 15.19
#   live active, ANY 2025 participation kind        35.12 / 16.66
#
# The paper's pair sits BETWEEN the active-roll and full-roll bases on both parties, so it is
# not a status filter; and the two deviations run in OPPOSITE directions against the closest
# candidate, which is not what a single basis difference looks like either.
#
# THE FINDING WAS NEVER AT RISK — the ratio is 1.92-2.11 on every basis, so "nearly double"
# holds throughout, and it is 1.96 on the basis now printed. Only the two decimals moved.
#
# NB "15.9" also occurs as a §IV table cell (Nov 2023 REP), which is asserted by its own
# probe — deleting the literal exemption does not orphan it. Verified by re-running the
# coverage gate after the change, not assumed.

COVERAGE_EXEMPT_SECTIONS: dict[str, str] = {}


def main() -> int:
    """Scrape the whole paper, assert, then GATE coverage over sections I-VI.

    COVERAGE BECAME A GATE 2026-08-06. `--coverage` was an advisory report nobody had to act
    on, so "96 figures agree" was a floor with no ceiling — and this paper's history is that
    its roll-denominated sections had already drifted once without any probe noticing.
    """
    norm = vp.normalise(PAPER.read_text(encoding="utf-8"))
    audit_sections, offsets, spans = {}, {}, {}
    for name, (start, end) in AUDIT_BOUNDS.items():
        audit_sections[name], offsets[name] = vp.slice_with_offset(norm, start, end)
    stats: dict = {}
    rc = vp.run("WHO DECIDES NEW YORK — prose scraped and asserted against the voter file",
                norm, PROBES, derive(), UNCHECKED, vp.wants_coverage(), spans_out=spans,
                stats_out=stats)
    fails = vp.audit_coverage(audit_sections, spans, offsets, tuple(AUDIT_BOUNDS),
                              COVERAGE_EXEMPT, COVERAGE_EXEMPT_LITERAL,
                              COVERAGE_EXEMPT_SECTIONS)
    fails += vp.audit_satellite_counts(PAPER.name, stats.get("figures"))
    if fails:
        print("\n" + "=" * 78)
        print(f"WHO DECIDES NEW YORK: {len(fails)} coverage/satellite FAILURE(S)")
        print("=" * 78)
        for f in fails:
            print(f"  - {f}")
        return 1
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
