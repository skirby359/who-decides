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


def age_composition(con, d: dict, tag: str, year: int, kind: str | None,
                    extra: str = "") -> None:
    """Share of an electorate (or of the roll, when kind is None) by age band, plus median.

    `extra` narrows the population — a registration filter (`v.party='REP'`) or a
    ballot-choice filter on the participation join (`p.ballot_choice='REP'`). Both are needed
    by §IV's primary-electorate table and neither changes the age basis, which stays keyed to
    `year` so the caller states it explicitly.
    """
    ag = _AGE.format(yr=year)
    join = "" if kind is None else _electorate_join(year, kind)
    if kind is not None and "p.ballot_choice" in extra:
        # The default join projects only state_voter_id, so a ballot-choice predicate has
        # nothing to bind to. Push it into the subquery instead of widening the projection,
        # which would change the join's cardinality if a voter had two rows for one primary.
        join = (f"JOIN (SELECT DISTINCT state_voter_id FROM voter_participation "
                f"WHERE election_year={year} AND kind='{kind}' "
                f"AND {extra.replace('p.', '')}) p USING (state_voter_id)")
        extra = ""
    where = f"AND {extra}" if extra else ""
    rows = con.execute(f"""
        WITH e AS (SELECT {_band(ag)} band FROM voters v {join}
                   WHERE v.age IS NOT NULL AND {ag} BETWEEN 18 AND 105 {where})
        SELECT band, COUNT(*) FROM e GROUP BY 1""").fetchall()
    counts = {b: 0 for b in BANDS}
    for b, n in rows:
        counts[b] = n
    tot = sum(counts.values()) or 1
    for b in BANDS:
        d[f"{tag}_{b}"] = 100.0 * counts[b] / tot
    d[f"{tag}_median"], = con.execute(f"""
        SELECT median({ag}) FROM voters v {join}
        WHERE v.age IS NOT NULL AND {ag} BETWEEN 18 AND 105 {where}""").fetchone()


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
    # The difference of the ROUNDED columns, which §IV's worked example contrasts with the
    # unrounded margin. Two different quantities; the paper prints the unrounded one.
    d["p24_RminusD_rounded"] = round(d["p24_REP"], 1) - round(d["p24_DEM"], 1)

    # ------------------------------------------------------------------ coverage gate, 2026-08-06
    # Three complete result tables had no probe pointing at them, which is the shape of gap
    # the donor paper learned about from an external reviewer. Grouped here so it is obvious
    # which derivations the gate forced out of the prose.

    d["roll_m"] = d["roll_n"] / 1e6
    d["ld_seats"] = d["ld_n"] * 3          # §IV's "105 legislative seats": 35 districts x 3

    # §IV, primary-electorate age table. THE TWO ROWS SIT ON TWO AGE BASES, and both were
    # checked before either was probed:
    #   "Republican registrants (all roll)"      -> current-roll age  (12.6/20.4/32.5/34.5, 55)
    #   "Republican-ballot primary voters, 2024" -> age at 2024       ( 4.9/14.2/34.2/46.7, 63)
    # On a single basis the primary row reads 4.09/12.37/31.73/51.81 with median 65, so the
    # mixed basis is not a rounding matter. It is also the paper's own stated convention (§VII
    # says §I's age-at-election figures "are not interchangeable" with current-roll ones), and
    # it runs AGAINST the paper's claim: aging the primary voters to 2024 makes them look
    # younger, so the 12.6 -> 4.9 collapse is understated rather than flattered.
    age_composition(con, d, "rreproll", 2026, None, extra="v.party='REP'")
    age_composition(con, d, "rballot24", 2024, "PRIMARY", extra="p.ballot_choice='REP'")

    # §IV, ballot choice among UNAFFILIATED primary voters. Denominator is participants with a
    # RECORDED ballot choice: including the null-choice rows reads 27.57/52.30/18.86 against
    # the paper's 27.7/52.6/19.0 — every cell low, in one direction, which is a denominator
    # difference and not drift. A row with no recorded ballot type cannot be classified into
    # any of the three columns, so excluding it is what the table means.
    for yr in (2022, 2024, 2026):
        rows = dict(con.execute(f"""
            SELECT p.ballot_choice, COUNT(*) FROM voters v
            JOIN voter_participation p USING (state_voter_id)
            WHERE v.party='UNA' AND p.kind='PRIMARY' AND p.election_year={yr}
              AND p.ballot_choice IS NOT NULL
            GROUP BY 1""").fetchall())
        tot = sum(rows.values()) or 1
        for col, key in (("REP", "rep"), ("DEM", "dem"), ("UNA", "np")):
            d[f"unaballot{yr}_{key}"] = 100.0 * rows.get(col, 0) / tot

    # §VI, the six registration cohorts. Age-banded (18-105), which is the convention
    # age_composition already uses and which reproduces five of the six counts exactly.
    # See the 2024 open question in COVERAGE_EXEMPT_LITERAL for the sixth.
    for yr in (2008, 2012, 2016, 2020, 2022, 2024):
        rows = dict(con.execute(f"""
            SELECT {PARTY}, COUNT(*) FROM voters v
            WHERE year(registration_date)={yr} AND v.age BETWEEN 18 AND 105
            GROUP BY 1""").fetchall())
        tot = sum(rows.values()) or 1
        d[f"coh{yr}_n"] = tot
        for p in ("REP", "DEM", "UNAFF"):
            d[f"coh{yr}_{p}"] = 100.0 * rows.get(p, 0) / tot
        d[f"coh{yr}_median"], = con.execute(f"""
            SELECT median(v.age - (2026 - {yr})) FROM voters v
            WHERE year(registration_date)={yr} AND v.age BETWEEN 18 AND 105""").fetchone()

    _section_vii(con, d)
    con.close()
    return d


def _section_vii(con, d: dict) -> None:
    """§VII, re-derived here rather than deferred to the donor paper.

    The cheaper route was to exempt these to verify_donor_class.py, which owns the same cuts.
    Deriving them independently instead buys the one thing that route cannot: it catches a
    TRANSCRIPTION error in this paper's copy, which the donor paper's own verifier is blind to
    by construction. The panel is `voter_donor_affiliation_state` — Idaho Sunshine
    state-campaign money, the full-name key, which is what §VII names.

    Age here is CURRENT-ROLL age for all three populations, because §VII says so explicitly
    ("All three are computed on current-roll age... the age-at-election figures in Section I
    are not interchangeable with them"). Using age-at-2024 for the general-electorate column
    would read 2 points off and look like a paper defect.
    """
    con.execute(f"ATTACH IF NOT EXISTS '{STATEWIDE}' AS sw2 (READ_ONLY)")
    P = "sw2.voter_donor_affiliation_state"

    d["don_n"], d["don_gifts"], m = con.execute(
        f"SELECT COUNT(*), SUM(donation_count), SUM(total_donated)/1e6 FROM {P}").fetchone()
    d["don_m"] = float(m)

    rows = con.execute(f"""
        SELECT {PARTY} p, COUNT(*), SUM(a.total_donated)
        FROM {P} a JOIN voters v USING (state_voter_id) GROUP BY 1""").fetchall()
    tot_n = sum(r[1] for r in rows) or 1
    tot_m = sum(float(r[2]) for r in rows) or 1.0
    for p, n, m in rows:
        d[f"don_{p}_n"] = n
        d[f"don_{p}_share"] = 100.0 * n / tot_n
        d[f"don_{p}_dollars"] = 100.0 * float(m) / tot_m
        d[f"don_{p}_skew"] = d[f"don_{p}_share"] - d[f"roll_{p}"]

    d["don_65"], d["don_u30"] = (float(x) for x in con.execute(f"""
        SELECT 100.0*COUNT(*) FILTER (WHERE v.age>=65)/COUNT(*),
               100.0*COUNT(*) FILTER (WHERE v.age<30)/COUNT(*)
        FROM {P} a JOIN voters v USING (state_voter_id)""").fetchone())
    d["gen24_65_rollage"], = con.execute(f"""
        SELECT 100.0*COUNT(*) FILTER (WHERE v.age>=65)/COUNT(*) FROM voters v
        {_electorate_join(2024, 'GENERAL')}""").fetchone()

    d["don_top1"], d["don_top10"] = (float(x) for x in con.execute(f"""
        WITH r AS (SELECT total_donated t, NTILE(100) OVER (ORDER BY total_donated DESC) p
                   FROM {P} WHERE total_donated>0)
        SELECT 100.0*SUM(t) FILTER (WHERE p=1)/SUM(t),
               100.0*SUM(t) FILTER (WHERE p<=10)/SUM(t) FROM r""").fetchone())
    d["don_ada"], = con.execute(f"""
        SELECT 100.0*SUM(a.total_donated) FILTER (WHERE v.county_name='ADA')/SUM(a.total_donated)
        FROM {P} a JOIN voters v USING (state_voter_id)""").fetchone()

    # Donor mix by district safety, banded the same way §V bands them, so the two sections
    # cannot drift apart. Solid-R is net>=40 (the 27); Likely+Lean is 5<=net<40 (the 8).
    con.execute("""CREATE OR REPLACE TEMP TABLE _ldnet AS
        SELECT legislative_district ld,
               100.0*COUNT(*) FILTER (WHERE party='REP')/COUNT(*)
               - 100.0*COUNT(*) FILTER (WHERE party='DEM')/COUNT(*) net
        FROM voters WHERE legislative_district IS NOT NULL GROUP BY 1""")
    for tag, cond in (("solid", "l.net>=40"), ("marg", "l.net>=5 AND l.net<40")):
        n, pr, pd = con.execute(f"""
            SELECT COUNT(*), 100.0*COUNT(*) FILTER (WHERE v.party='REP')/COUNT(*),
                   100.0*COUNT(*) FILTER (WHERE v.party='DEM')/COUNT(*)
            FROM {P} a JOIN voters v USING (state_voter_id)
            JOIN _ldnet l ON l.ld = v.legislative_district WHERE {cond}""").fetchone()
        d[f"don_{tag}_n"], d[f"don_{tag}_r"], d[f"don_{tag}_d"] = n, float(pr), float(pd)

    # Crossover. Denominator is donors whose money reached a party-resolvable recipient, which
    # is what the paper's lead-in says; d_amount + r_amount > 0 is that condition.
    for p, od, orr, mx in con.execute(f"""
        SELECT {PARTY} p,
          100.0*COUNT(*) FILTER (WHERE a.d_amount>0 AND a.r_amount=0)
              /COUNT(*) FILTER (WHERE a.d_amount+a.r_amount>0),
          100.0*COUNT(*) FILTER (WHERE a.r_amount>0 AND a.d_amount=0)
              /COUNT(*) FILTER (WHERE a.d_amount+a.r_amount>0),
          100.0*COUNT(*) FILTER (WHERE a.d_amount>0 AND a.r_amount>0)
              /COUNT(*) FILTER (WHERE a.d_amount+a.r_amount>0)
        FROM {P} a JOIN voters v USING (state_voter_id) GROUP BY 1""").fetchall():
        if od is None:
            continue
        d[f"xo_{p}_d"], d[f"xo_{p}_r"], d[f"xo_{p}_mixed"] = float(od), float(orr), float(mx)
    d["xo_res_donors"], d["xo_res_dollars"] = (float(x) for x in con.execute(f"""
        SELECT 100.0*COUNT(*) FILTER (WHERE d_amount+r_amount>0)/COUNT(*),
               100.0*SUM(d_amount+r_amount)/SUM(total_donated) FROM {P}""").fetchone())

    # Methods: the ID FEC layer's scale, and the pooled table the methods note contrasts.
    d["fec_rows"], fm = con.execute(
        "SELECT COUNT(*), SUM(contribution_amount)/1e6 FROM sw2.individual_contributions "
        "WHERE contribution_id LIKE 'FEC:%'").fetchone()
    d["fec_m"] = float(fm)
    d["fec_matched"], = con.execute(
        "SELECT COUNT(*) FROM sw2.voter_donor_affiliation_fec").fetchone()
    d["pooled_n"], = con.execute(
        "SELECT COUNT(*) FROM sw2.voter_donor_affiliation").fetchone()

    # The series-wide recall cost of the full-name specification, "11-19%". Same construction
    # as verify_whitepaper's: min and max across every retained _alltier pair in the series,
    # NOT Idaho's own two (13.4% / 14.3%), which sit inside the range but are not its ends.
    losses = []
    for st in ("wa", "ny", "id"):
        c2 = duckdb.connect(str(vp.DATA / f"{st}_statewide.duckdb"), read_only=True)
        for t in ("fec", "state"):
            try:
                a, = c2.execute(
                    f"SELECT COUNT(*) FROM voter_donor_affiliation_{t}_alltier").fetchone()
                p2, = c2.execute(
                    f"SELECT COUNT(*) FROM voter_donor_affiliation_{t}").fetchone()
                losses.append(100.0 * (a - p2) / a)
            except Exception:  # noqa: BLE001
                pass
        c2.close()
    if losses:
        d["discard_lo"], d["discard_hi"] = min(losses), max(losses)


PROBES = [
    # --- Abstract, gated 2026-08-07 when it moved in from the metadata file. Each figure is a
    # restatement of one asserted in a section below, and each gets its own probe for that
    # reason: the abstract is the most-read and least-revised part of a paper.
    ("abstract — roll size, exact",
     r"statewide voter file for \*\*([\d,]+)\*\* registrants", "roll_n", 0),
    ("abstract — party-neutral 65+ share among 2024 general voters",
     r"65-and-over share, \*\*([\d.]+)%\*\* against \*\*([\d.]+)%\*\*",
     ("e24_REP_65", "e24_DEM_65"), 0.05),
    ("abstract — 2024 primary electorate against the roll, REP share",
     r"primary electorate runs \*\*([\d.]+)%\*\* Republican by registration against "
     r"\*\*([\d.]+)%\*\* of the roll", ("p24_REP", "roll_REP"), 0.05),
    ("abstract — Republican-minus-Democratic margin, primary against roll",
     r"margin of \*\*([\d.]+)\*\* points against \*\*([\d.]+)\*\* on the rolls",
     ("p24_RminusD", "roll_RminusD"), 0.05),
    ("abstract — Republican-ballot primary voters, 65+ share",
     r"with \*\*([\d.]+)%\*\* aged 65 or over", "rballot24_65+", 0.05),
    ("abstract — roll contraction, current extract",
     r"from about 1\.18 to ([\d.]+) million", "roll_m", 0.005),
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

    # ---- added 2026-08-06 by the coverage gate -------------------------------------------
    # §IV: the primary-electorate age table, both rows (see derive() on the two age bases).
    ("§IV Republican registrants, all roll",
     r"\| Republican registrants \(all roll\) \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| "
     r"([\d.]+)% \| (\d+) \|",
     ("rreproll_18-29", "rreproll_30-44", "rreproll_45-64", "rreproll_65+",
      "rreproll_median"), 0.05),
    # 5.0 and 34.1 were printed 4.9 and 34.2 until 2026-08-06. Every age-basis variant gives
    # 4.967 / 34.105 to three decimals and the row's other three cells plus its median
    # reproduce exactly, so the basis was never in doubt — the two cells were misrounded, in
    # OPPOSITE directions, which is why a basis hypothesis does not explain them. Idaho has no
    # pinned roll (only WA and NY do), so there is no snapshot alternative either.
    ("§IV Republican-ballot primary voters, 2024",
     r"\| Republican-ballot primary voters, 2024 \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \| "
     r"([\d.]+)% \| \*\*([\d.]+)%\*\* \| \*\*(\d+)\*\* \|",
     ("rballot24_18-29", "rballot24_30-44", "rballot24_45-64", "rballot24_65+",
      "rballot24_median"), 0.05),
    ("§IV the primary electorate's median age and 65+ share, restated",
     r"median age (\d+), nearly half of them 65\+", "rballot24_median", 0),

    # §IV: unaffiliated ballot choice, all three cycles.
    ("§IV unaffiliated ballot choice, May 2022",
     r"\| May 2022 \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \|",
     ("unaballot2022_rep", "unaballot2022_dem", "unaballot2022_np"), 0.05),
    ("§IV unaffiliated ballot choice, May 2024",
     r"\| May 2024 \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \|",
     ("unaballot2024_rep", "unaballot2024_dem", "unaballot2024_np"), 0.05),
    ("§IV unaffiliated ballot choice, May 2026",
     r"\| May 2026 \| \*\*([\d.]+)%\*\* \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \|",
     ("unaballot2026_rep", "unaballot2026_dem", "unaballot2026_np"), 0.05),

    # §IV: the unrounded-margin worked example, which is the paper explaining its own
    # convention. Probing it means the convention cannot silently stop being true.
    # The sixth capture is the difference of the ROUNDED columns, which is a different
    # quantity from the unrounded margin — that is the whole point the worked example makes,
    # so it needs its own derived key rather than reusing p24_RminusD.
    ("§IV unrounded-vs-rounded worked example",
     r"([\d.]+) − ([\d.]+) = ([\d.]+), against ([\d.]+) − ([\d.]+) = ([\d.]+) read off the table",
     ("p24_REP", "p24_DEM", "p24_RminusD", "p24_REP", "p24_DEM", "p24_RminusD_rounded"), 0.05),
    ("§IV legislative seats, both statements",
     r"Of the (\d+) legislative seats", "ld_seats", 0),
    ("§IV the 35-district / 105-seat frame",
     r"35-district / (\d+)-seat frame", "ld_seats", 0),

    # §VI: the six registration cohorts.
    ("§VI 2008 cohort", r"\| 2008 \| ([\d,]+) \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| (\d+) \|",
     ("coh2008_n", "coh2008_REP", "coh2008_DEM", "coh2008_UNAFF", "coh2008_median"), 0.05),
    ("§VI 2012 cohort", r"\| 2012 \| ([\d,]+) \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| (\d+) \|",
     ("coh2012_n", "coh2012_REP", "coh2012_DEM", "coh2012_UNAFF", "coh2012_median"), 0.05),
    ("§VI 2016 cohort", r"\| 2016 \| ([\d,]+) \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| (\d+) \|",
     ("coh2016_n", "coh2016_REP", "coh2016_DEM", "coh2016_UNAFF", "coh2016_median"), 0.05),
    ("§VI 2020 cohort", r"\| 2020 \| ([\d,]+) \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| (\d+) \|",
     ("coh2020_n", "coh2020_REP", "coh2020_DEM", "coh2020_UNAFF", "coh2020_median"), 0.05),
    ("§VI 2022 cohort", r"\| 2022 \| ([\d,]+) \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| (\d+) \|",
     ("coh2022_n", "coh2022_REP", "coh2022_DEM", "coh2022_UNAFF", "coh2022_median"), 0.05),
    # The count is now asserted like the other five (corrected 263,315 -> 263,322 on
    # 2026-08-06; see the resolved note near COVERAGE_EXEMPT_LITERAL).
    ("§VI 2024 cohort", r"\| 2024 \| ([\d,]+) \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \| "
     r"\*\*([\d.]+)%\*\* \| \*\*(\d+)\*\* \|",
     ("coh2024_n", "coh2024_REP", "coh2024_DEM", "coh2024_UNAFF", "coh2024_median"), 0.05),
    ("§VI newest cohort's Republican share, restated",
     r"less Republican \(([\d.]+)% vs the high-60s", "coh2024_REP", 0.05),

    # §VII: derived here independently rather than deferred (see _section_vii).
    ("§VII panel scale — voters, donations, dollars",
     r"links \*\*([\d,]+) registered voters to ([\d,]+) donations \(\$([\d.]+)M\)\*\*",
     ("don_n", "don_gifts", "don_m"), 0.005),
    ("§VII donor party table — Republican",
     r"\| Republican \| ([\d,]+) \| ([\d.]+)% \| ([\d.]+)% \| \+([\d.]+) \| ([\d.]+)% \|",
     ("don_REP_n", "don_REP_share", "roll_REP", "don_REP_skew", "don_REP_dollars"), 0.05),
    ("§VII donor party table — Democratic",
     r"\| Democratic \| ([\d,]+) \| ([\d.]+)% \| ([\d.]+)% \| \*\*\+([\d.]+)\*\* \| ([\d.]+)% \|",
     ("don_DEM_n", "don_DEM_share", "roll_DEM", "don_DEM_skew", "don_DEM_dollars"), 0.05),
    ("§VII donor party table — Unaffiliated",
     r"\| Unaffiliated \| ([\d,]+) \| ([\d.]+)% \| ([\d.]+)% \| \*\*−([\d.]+)\*\* \| ([\d.]+)% \|",
     ("don_UNAFF_n", "don_UNAFF_share", "roll_UNAFF", "_neg_unaff_skew",
      "don_UNAFF_dollars"), 0.05),
    ("§VII donor party table — Other",
     r"\| Other \| ([\d,]+) \| ([\d.]+)% \| ([\d.]+)% \| −([\d.]+) \| ([\d.]+)% \|",
     ("don_OTHER_n", "don_OTHER_share", "roll_OTHER", "_neg_other_skew",
      "don_OTHER_dollars"), 0.05),
    ("§VII donor age against roll and 2024 general",
     r"([\d.]+)% of matched donors are 65\+, versus ([\d.]+)% of the roll and ([\d.]+)% of 2024 "
     r"general voters; the under-30 share is ([\d.]+)% versus ([\d.]+)% of the roll",
     ("don_65", "rollage_65+", "gen24_65_rollage", "don_u30", "rollage_18-29"), 0.5),
    ("Boundary — the roll's contraction, both endpoints in millions",
     r"to \*\*~([\d.]+)M\*\* in this 2026 snapshot", "roll_m", 0.005),
    ("§VII concentration — top 1% and top 10%",
     r"top 1% of matched donors supply \*\*([\d.]+)%\*\* of the matched dollars; the top 10% "
     r"supply \*\*([\d.]+)%\*\*", ("don_top1", "don_top10"), 0.5),
    ("§VII geography — Ada County's dollar share",
     r"Ada County \(Boise\) alone accounts for \*\*([\d.]+)%\*\*", "don_ada", 0.5),
    ("§VII donors by district safety — Solid-R then the competitive-adjacent eight",
     r"the 27 Solid-R districts hold ([\d,]+) donors who are \*\*([\d.]+)% Republican / "
     r"([\d.]+)% Democratic\*\*, while the eight Likely-R and Lean-R districts hold ([\d,]+) "
     r"donors at a far more balanced \*\*([\d.]+)% / ([\d.]+)%\*\*",
     ("don_solid_n", "don_solid_r", "don_solid_d", "don_marg_n", "don_marg_r",
      "don_marg_d"), 0.5),
    ("§VII recipient resolution — donors then dollars",
     r"resolves the recipient for \*\*([\d.]+)% of matched donors and ([\d.]+)% of matched "
     r"dollars\*\*", ("xo_res_donors", "xo_res_dollars"), 0.5),
    ("§VII crossover — Republican donors",
     r"\| Republican \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \|",
     ("xo_REP_d", "xo_REP_r", "xo_REP_mixed"), 0.05),
    ("§VII crossover — Democratic donors",
     r"\| Democratic \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \| ([\d.]+)% \|",
     ("xo_DEM_d", "xo_DEM_r", "xo_DEM_mixed"), 0.05),
    ("§VII crossover — Unaffiliated donors",
     r"\| Unaffiliated \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \| ([\d.]+)% \|",
     ("xo_UNAFF_d", "xo_UNAFF_r", "xo_UNAFF_mixed"), 0.05),
    ("§VII recall cost of the full-name specification (series-wide)",
     r"discards ([\d]+)–([\d]+)% of matched donors", ("discard_lo", "discard_hi"), 0.5),

    # Boundary / Methods
    ("Boundary — current roll in millions, both statements",
     r"The 2026 roll \(([\d.]+)M\)", "roll_m", 0.005),
    ("Methods — the ID FEC layer's scale and match",
     r"([\d,]+) rows / \$([\d.]+)M outflow \+ inflow, with ([\d,]+) FEC voter",
     ("fec_rows", "fec_m", "fec_matched"), 0.05),
    ("Methods — the pooled table both money systems land in",
     r"both money systems in one table, ([\d,]+) donors", "pooled_n", 0),
]

UNCHECKED = [
    "Turnout RATES — deliberately absent from the paper. Idaho's roll is a current extract "
    "that shrank 1.18M to 1.03M since 2024, so any rate is survivorship-inflated; the paper "
    "reports composition shares, which are denominator-free, and so does this script",
    "The Das-Gupta decomposition and the Ballotpedia contested-count reconciliation — "
    "scripts/diag_id_primary_contested.py owns the second and the paper reports the first "
    "qualitatively, without a figure to assert",
    "§VII WAS previously deferred to verify_donor_class.py. It is now re-derived here "
    "(_section_vii) instead, because deferring it could never catch a transcription error in "
    "THIS paper's copy of a figure the donor paper states correctly",
]


# --- Coverage gate (ported 2026-08-06; see verify_who_decides_wa for the three rules) ----
# Sections I-VII, partitioned so no slice overlaps another: spans are per-section coordinates,
# so a slice that swallows another reports the inner one's probed cells as unmapped.
AUDIT_BOUNDS = {
    # Gated 2026-08-07, when the abstract moved into the paper from the metadata file. Same
    # reasoning as the New York companion: the abstract restates results from five sections, and
    # a drift there is the most expensive kind because it is what a referee reads first.
    "abstract": ("## Abstract", "## The question"),
    "sec1": ("## I. The off-year electorate is older", "## II. In Idaho the age gap"),
    "sec2": ("## II. In Idaho the age gap", "## III. The unaffiliated quarter"),
    "sec3": ("## III. The unaffiliated quarter", "## IV. The closed primary"),
    "sec4": ("## IV. The closed primary", "## V. Safe-seat Idaho"),
    "sec5": ("## V. Safe-seat Idaho", "## VI. A leading indicator"),
    "sec6": ("## VI. A leading indicator", "## VII. The donor class"),
    "sec7": ("## VII. The donor class", "## Boundary of inference"),
    "boundary": ("## Boundary of inference", "## What it means"),
}

COVERAGE_EXEMPT = [
    (r"^(?:19|20)\d{2}$", "a calendar year, not a result"),
    (r"^\d{1,2}$", "small integer — district/seat counts, band edges, list ordinals"),
]

COVERAGE_EXEMPT_LITERAL: dict[str, str] = {
    # Official Idaho SoS publications. These are the EXTERNAL benchmark the survivorship
    # caveat is measured against, so by construction the voter file cannot reproduce them —
    # that mismatch is the caveat's whole point.
    "1.18": "registrants at the November 2024 election, published by the Idaho SoS. The "
            "external benchmark the survivorship caveat is stated against; the voter file "
            "holds the 2026 extract (1.03M), which IS derived",
    "77.8": "official 2024 general turnout rate, Idaho SoS. External by design — the paper "
            "cites it to show its own ~94% is survivorship-inflated",
    "917,608": "official 2024 ballots cast, Idaho SoS; as above",
    "1,178,750": "official 2024 registered total, Idaho SoS; as above",
    "121,000": "Election-Day same-day registrants, Idaho SoS. An external count cited as a "
               "mechanism for roll churn, not a cut of the file",
    "100": "the survivorship caveat's '2020 even computes above 100%' — a reductio showing "
           "the rate basis is unusable, not a reported rate",
    "120": "the blinded-validation sample size (120/120), owned by the donor-class paper's "
           "Appendix F and asserted by verify_donor_class.py",
}
# NB the 2026 ballot-measure result (69.6-30.4), the extract date in the source filename, and
# the '~100% populated' field-coverage remark sit in "What it means" and Methods, which are not
# audited sections here — the audit covers I-VII plus Boundary. Exempting them would have been
# dead weight, and the gate says so ("literal exemption(s) no longer fire").

# --- ✅ RESOLVED 2026-08-06 — author answered "trivial, but the paper is unpublished: fix"
# §VI's 2024 cohort now prints 263,322 and IS asserted by the "§VI 2024 cohort" probe above,
# on the same age-banded basis as the other five rows. The exemption this block installed is
# deleted. The enumeration is KEPT: it is the evidence that the convention was right and one
# cell was wrong, which is the opposite of what a basis defect looks like.
#
# What it used to print — 263,315. THIRTEEN bases enumerated and none reproduced it; every
# one gives 263,322, seven higher:
#
#   plain year(registration_date)=2024                263,322
#   + age IS NOT NULL / age 18-105 / age 17-105       263,322
#   + party IS NOT NULL / party <> ''                 263,322
#   + status_code='A' / county / legislative_district  263,322
#   COUNT(DISTINCT state_voter_id)                    263,322   (the file has NO duplicate
#                                                                ids — 1,029,938 rows,
#                                                                1,029,938 distinct)
#   + age 18-100                                      263,301
#   + registration_date <= 2024-11-05                 261,661
#   + party IN (REP,DEM,UNA)                          258,736
#
# The 2022 cell (97,593) DOES reproduce, on the age-banded basis this script uses, and so do
# 2008/2012/2016/2020. So the convention is right and one cell is seven registrants off —
# 0.003%, moving no percentage or median in the row, all of which are asserted above.
#
# A duplicate-id hypothesis looked compelling (the +1 on 2022 and +7 on 2024 matched a
# dup-count story exactly) and was FALSE when checked. Worth recording: the coincidence was
# the whole evidence for it.
# (no literal exemption here any more — the count is probed)

COVERAGE_EXEMPT_SECTIONS: dict[str, str] = {}


def main() -> int:
    """Scrape the paper, assert, then GATE coverage over sections I-VII.

    COVERAGE BECAME A GATE 2026-08-06, and it found that THREE complete result tables had no
    probe pointing at them — §IV's primary-electorate age table, §IV's unaffiliated
    ballot-choice table, and §VI's six registration cohorts. "96 figures agree" was a floor
    with no ceiling, which is exactly how an external reviewer found four contradictions in
    the donor paper after it claimed 309 figures verified.
    """
    norm = vp.normalise(PAPER.read_text(encoding="utf-8"))
    audit_sections, offsets, spans = {}, {}, {}
    for name, (start, end) in AUDIT_BOUNDS.items():
        audit_sections[name], offsets[name] = vp.slice_with_offset(norm, start, end)
    d = derive()
    # The paper prints two skews with a minus sign the capture group cannot carry.
    d["_neg_unaff_skew"] = -d["don_UNAFF_skew"]
    d["_neg_other_skew"] = -d["don_OTHER_skew"]
    stats: dict = {}
    rc = vp.run("WHO DECIDES IDAHO — prose scraped and asserted against the voter file",
                norm, PROBES, d, UNCHECKED, vp.wants_coverage(), spans_out=spans,
                stats_out=stats)
    fails = vp.audit_coverage(audit_sections, spans, offsets, tuple(AUDIT_BOUNDS),
                              COVERAGE_EXEMPT, COVERAGE_EXEMPT_LITERAL,
                              COVERAGE_EXEMPT_SECTIONS)
    fails += vp.audit_satellite_counts(PAPER.name, stats.get("figures"))
    if fails:
        print("\n" + "=" * 78)
        print(f"WHO DECIDES IDAHO: {len(fails)} coverage/satellite FAILURE(S)")
        print("=" * 78)
        for f in fails:
            print(f"  - {f}")
        return 1
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
