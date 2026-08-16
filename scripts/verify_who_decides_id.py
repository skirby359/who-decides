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


SOS_PIN = vp.DOCS / "reference" / "id_sos_turnout_history_2026-08-15.csv"


def _id_sos_turnout() -> dict[int, dict[str, int | float]]:
    """The Idaho SoS's own registration/turnout table, read from the pin.

    These are EXTERNAL constants — the voter file cannot reproduce them, and that is the
    point of every figure that uses them. They lived as Python literals until an external
    referee found two of them wrong on 2026-08-15 (2022 ballots 595,602 against the SoS's
    599,493; 2024 917,608 against 917,469). Nothing in this file could have caught that:
    an asserting verifier checks the paper against the constant, never the constant
    against the world. Pinning does not fix that either — it makes the constant's source
    and retrieval date checkable in one click, which is the most a repo can do.

    A missing pin is a FAILURE, not a fallback to literals. The failure mode this whole
    section exists to prevent is a plausible number with no provenance.
    """
    if not SOS_PIN.exists():
        raise SystemExit(
            f"FATAL: the Idaho SoS turnout pin is missing ({SOS_PIN}). The coverage table, "
            f"the bounds it supports and the official turnout rate all rest on it. Refusing "
            f"to fall back to in-code constants — that is exactly how the retired 595,602 "
            f"and 917,608 survived unreviewed.")
    out: dict[int, dict[str, int | float]] = {}
    for line in SOS_PIN.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or line.startswith("election_date") or not line.strip():
            continue
        date_s, kind, reg, ballots, turnout = line.split(",")
        if kind != "general":
            continue
        out[int(date_s[:4])] = {"registered": int(reg), "ballots_cast": int(ballots),
                                "turnout_pct": float(turnout)}
    if not out:
        raise SystemExit(f"FATAL: the SoS pin {SOS_PIN} parsed to zero general-election rows.")
    return out


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

    # THE PARTY-NEUTRALITY CLAIM, narrowed and then asserted (2026-08-15, referee item 5).
    #
    # §II and the abstract said the age gap is "party-neutral" and that Idaho's youth "sits
    # in the unaffiliated bloc rather than in either party". The first half is a real
    # finding: R and D are within a fraction of a point on the 65+ share. The second half is
    # not true of Democrats — Democratic and unaffiliated 2024 general voters are within
    # 0.2 points of each other on the under-30 share (19.4 / 19.6), while Republicans sit
    # nearly seven points below both.
    #
    # So what distinguishes the unaffiliated bloc is the SENIOR end, not the young end: it
    # carries ten fewer points of 65+ than either party. Both relations are asserted, because
    # the narrowed sentence needs both to be true and neither has a token a probe could read.
    d["e24_RD_65_gap"] = abs(d["e24_REP_65"] - d["e24_DEM_65"])
    d["e24_DU_1829_gap"] = abs(d["e24_DEM_1829"] - d["e24_UNAFF_1829"])

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

    # THE TWO DENOMINATORS, derived so the paper can name them (2026-08-11). §IV publishes two
    # Republican-ballot-share series and described both as the share of primary ballots cast: the
    # range EXCLUDES the `id-primary-ballot-choice-blank` voters, whose choice the file does not
    # record — checked against the raw export rather than assumed from the load — while
    # `*_rep_ballot_share` below INCLUDES them. They differ by 0.11 to 0.39 points, which is
    # enough to print two different numbers for the same cycle (2022: 86.49 against 86.10) and
    # small enough that nothing looked wrong. Same class as the WA paper's retired
    # rate-share-under-one-name defect; the fix there and here is to state the basis.
    nc = con.execute("""
        SELECT COUNT(*) FILTER (WHERE ballot_choice IS NULL),
               100.0*COUNT(*) FILTER (WHERE ballot_choice IS NULL)/COUNT(*)
        FROM voter_participation WHERE kind='PRIMARY' GROUP BY election_year""").fetchall()
    d["nochoice_n_lo"], d["nochoice_n_hi"] = min(n for n, _ in nc), max(n for n, _ in nc)
    d["nochoice_pct_lo"], d["nochoice_pct_hi"] = min(p for _, p in nc), max(p for _, p in nc)

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
    # THE SAME COUNT ACROSS EVERY LOADED PRIMARY, both parties. Section IV states a
    # four-cycle Republican series ("36% (2016) -> 43% -> 68% -> 53%") and a
    # Democratic range ("2-14% across these cycles"); only the 2024 Republican cell
    # was derived, so the trend claim the section is built on rested on one point.
    # The race-name predicate is the one above, parameterised by party — a second,
    # differently-worded predicate would make the Democratic series incomparable to
    # the Republican one, which is the comparison the sentence makes.
    _rn = ("AND (UPPER(ra.race_name) LIKE '%LEGISLATIVE DISTRICT%' "
           "OR (UPPER(ra.race_name) LIKE '%REPRESENTATIVE DISTRICT%' "
           "AND UPPER(ra.race_name) LIKE '%SEAT%') "
           "OR UPPER(ra.race_name) LIKE '%SENATOR DISTRICT%')")
    for party, ptag in (("REPUBLICAN", "r"), ("DEMOCRATIC", "d")):
        for cyc, n_tot, n_con in con.execute(f"""
                WITH rr AS (
                    SELECT YEAR(e.election_date) yr, ra.race_id,
                           COUNT(DISTINCT pr.candidate_id) nc
                    FROM sw.elections e JOIN sw.races ra ON ra.election_id=e.election_id
                    JOIN sw.precinct_results pr ON pr.race_id=ra.race_id
                    WHERE e.election_type='primary'
                      AND UPPER(ra.race_name) LIKE '%{party}%' {_rn}
                    GROUP BY 1, 2)
                SELECT yr, COUNT(*), COUNT(*) FILTER (WHERE nc>=2)
                FROM rr GROUP BY 1""").fetchall():
            if n_tot:
                d[f"{ptag}prim_{int(cyc)}"] = 100.0 * n_con / n_tot
    # The Democratic range the section quotes. Taken over the cycles the Republican
    # series names, so the two sides describe the same window — "across these
    # cycles" is a claim about WHICH cycles, and a range over a different set would
    # agree numerically by luck.
    _dcycles = [d[f"dprim_{y}"] for y in (2016, 2018, 2022, 2024) if f"dprim_{y}" in d]
    if len(_dcycles) != 4:
        raise SystemExit(
            f"FATAL: Section IV's Democratic contested range covers the four cycles "
            f"its Republican series names; only {len(_dcycles)} are derivable. "
            f"Either a cycle stopped loading or the race-name predicate no longer "
            f"matches — both make the range say something other than it claims.")
    d["dprim_lo"], d["dprim_hi"] = min(_dcycles), max(_dcycles)

    # THE SHAPE OF THE SERIES, checked in code (2026-08-15, referee item 11). §IV said the
    # contested rate "roughly doubled across the decade" and printed 36 → 43 → 68 → 53. It
    # did not: it rose to 1.9x its 2016 level in 2022 and then fell by a sixth. "Doubled
    # across the decade" is an endpoint claim and the endpoints are 36 and 53.
    #
    # This is the class of defect no coverage gate can see, because a superlative or a trend
    # word has no numeric token to probe — the same blind spot that let "highest of the four"
    # stand false in the money paper. So the shape is asserted here instead of described.
    d["rprim_peak_ratio"] = d["rprim_2022"] / d["rprim_2016"]
    d["rprim_endpoint_ratio"] = d["rprim_2024"] / d["rprim_2016"]

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

    # THE ROLL-CHURN AND TURNOUT-BASIS FIGURES the boundary and §III notes rest on.
    #
    # `ID_SOS_REG_2024` is the Secretary of State's own registered total at the
    # November 2024 election, printed in the boundary section beside the official
    # turnout rate. It is an EXTERNAL published constant, not a repo derivation, and
    # it is named here rather than inlined so that the turnover figure below is
    # visibly a comparison against an outside source rather than the roll compared
    # with itself.
    _sos = _id_sos_turnout()
    ID_SOS_REG_2024 = _sos[2024]["registered"]
    d["id_sos_reg_2024"] = ID_SOS_REG_2024
    d["roll_net_decline_pct"] = 100.0 * (ID_SOS_REG_2024 - d["roll_n"]) / ID_SOS_REG_2024
    d["roll_net_decline_n"] = ID_SOS_REG_2024 - d["roll_n"]

    # The inflated all-voter rate the boundary section quotes as ~94% to show WHY a
    # shrunken roll cannot be used as a turnout denominator. The point of the
    # sentence is the gap against the official 77.8%, so the number has to be
    # computed the inflating way on purpose: 2024 general voters over registrations
    # dated on or before the election. Over the whole current roll it is 87.3% —
    # a different (also wrong) denominator, and not the one the sentence describes.
    # WHAT EACH RECONSTRUCTED ELECTORATE ACTUALLY COVERS, and therefore what it can
    # say. A "reconstructed" electorate is the set of CURRENT registrants carrying
    # a vote record for that election; everyone who has since left the roll is
    # absent by construction. Comparing it to the Secretary of State's certified
    # ballots-cast count measures the gap directly — and bounds the age
    # composition, because the missing voters can be at most all-65+ or all-under.
    #
    # This replaced an analogy. The boundary section argued the direction of the
    # bias from Washington's roll churn, because Idaho has no prior snapshot. The
    # analogy is sound and is retained, but the bound below is Idaho's own data and
    # is a limit rather than a direction — which is what the section needed.
    #
    # SoS ballots cast, READ FROM THE PIN rather than hand-written here. Until
    # 2026-08-15 these were three Python literals, and two of them were wrong —
    # 2022 read 595,602 against the SoS's 599,493 and 2024 read 917,608 against
    # 917,469. An external referee found it; this verifier could not, and no
    # verifier of this design can. Asserting a paper against a constant checks
    # that the paper matches the constant, and says nothing about whether the
    # constant matches the world. The pin carries the source URL and retrieval
    # date so the next reader can re-check it against the world in one click.
    ID_SOS_BALLOTS = {y: r["ballots_cast"] for y, r in _sos.items()
                      if y in (2020, 2022, 2024)}
    for yr, official in ID_SOS_BALLOTS.items():
        n, = con.execute(
            f"SELECT COUNT(DISTINCT state_voter_id) FROM voter_participation "
            f"WHERE election_year={yr} AND kind='GENERAL'").fetchone()
        d[f"cover{yr}_n"] = int(n)
        d[f"cover{yr}_pct"] = 100.0 * n / official
        d[f"cover{yr}_missing"] = official - int(n)
        # The bound needs the measured 65+ share, which age_composition() has
        # already put in `gen{yr}_65+`.
        p65 = d[f"gen{yr}_65+"]
        n65 = p65 / 100.0 * n
        d[f"bound{yr}_lo"] = 100.0 * n65 / official
        d[f"bound{yr}_hi"] = 100.0 * (n65 + (official - n)) / official
        if not (d[f"bound{yr}_lo"] <= p65 <= d[f"bound{yr}_hi"]):
            raise SystemExit(
                f"FATAL: the {yr} 65+ bound [{d[f'bound{yr}_lo']:.2f}, "
                f"{d[f'bound{yr}_hi']:.2f}] does not contain the measured "
                f"{p65:.2f}%. The bound is arithmetic on the same two counts, so "
                f"this means the reconstruction exceeds the certified ballot count "
                f"and one of the two is not what it is labelled.")
    for _y, _b in ID_SOS_BALLOTS.items():
        d[f"id_sos_{_y}"] = _b
    d["bound2024_width"] = d["bound2024_hi"] - d["bound2024_lo"]
    d["bound2020_width"] = d["bound2020_hi"] - d["bound2020_lo"]

    # WASHINGTON'S ROLL CHURN, which the boundary section cites by name as the
    # mechanism argument ("Comparing Washington's 2023 and 2026 roll snapshots").
    # Idaho has no prior snapshot; Washington retains a September-2023 one, which
    # is the only place in this project where a DEPARTED voter can still be aged.
    #
    # Derived here rather than exempted. A first attempt at this exemption on
    # 2026-08-10 called the figures unverifiable Idaho data and said so at length.
    # They are Washington's, the paper says so in the same sentence, and they
    # reproduce to the printed digit. Read the sentence before writing the reason.
    wac = duckdb.connect(str(vp.DATA / "wa_vrdb.duckdb"), read_only=True)
    try:
        g_n, r_n, g65, r65 = wac.execute("""
            WITH s AS (
                SELECT date_diff('year', s.birthdate, DATE '2023-09-01') a,
                       (v.state_voter_id IS NULL) AS departed
                FROM voters_20230901 s LEFT JOIN voters v USING (state_voter_id)
                WHERE s.birthdate IS NOT NULL)
            SELECT COUNT(*) FILTER (WHERE departed), COUNT(*) FILTER (WHERE NOT departed),
                   100.0*COUNT(*) FILTER (WHERE departed AND a>=65)
                       /COUNT(*) FILTER (WHERE departed),
                   100.0*COUNT(*) FILTER (WHERE NOT departed AND a>=65)
                       /COUNT(*) FILTER (WHERE NOT departed)
            FROM s""").fetchone()
    finally:
        wac.close()
    # Idaho's election-day registrations inside the SoS's 2024 registered total —
    # quoted so the "same-day registrants churn" clause carries its magnitude.
    d["id_edr_2024"] = 121_015

    # --- DID THEY ACTUALLY CHURN? (2026-08-15, referee item 9.)
    #
    # §III explained the roll's contraction partly by "the non-persistence of the 121,000
    # voters who registered same-day on Election Day 2024". The referee's objection was that
    # the claim was never measured — and it is measurable in the file the paper already uses,
    # because a voter who registered at the polls on 2024-11-05 carries that date.
    #
    # Measured, the claim is FALSE, and not marginally: 109,441 of the 121,015 are still on
    # the 2026 roll, a 90.4% floor. A floor rather than a rate because `registration_date` is
    # the MOST RECENT registration event — a same-day registrant who has since moved or
    # changed party carries a later date and is counted here as absent. The true retention
    # can only be higher.
    #
    # This is the one referee item that reversed on measurement rather than being conceded,
    # and it reversed against the paper. The mechanism sentence is withdrawn, not softened.
    d["edr_persist_n"], = con.execute(
        "SELECT COUNT(*) FROM voters WHERE registration_date = DATE '2024-11-05'").fetchone()
    d["edr_persist_pct"] = 100.0 * d["edr_persist_n"] / d["id_edr_2024"]
    d["edr_persist_voted24"], = con.execute("""
        SELECT COUNT(*) FROM voters v WHERE v.registration_date = DATE '2024-11-05'
          AND v.state_voter_id IN (SELECT DISTINCT state_voter_id FROM voter_participation
                                   WHERE election_year=2024 AND kind='GENERAL')""").fetchone()

    d["wachurn_gone_n"], d["wachurn_kept_n"] = int(g_n), int(r_n)
    d["wachurn_gone_65"], d["wachurn_kept_65"] = float(g65), float(r65)
    if d["wachurn_gone_65"] <= d["wachurn_kept_65"]:
        raise SystemExit(
            f"FATAL: the boundary section argues departing voters skew OLDER, and "
            f"rests the direction of the survivorship bias on it. Measured: "
            f"departed {d['wachurn_gone_65']:.1f}% 65+, retained "
            f"{d['wachurn_kept_65']:.1f}%. The mechanism claim no longer holds.")

    d["gen24_allvoter_rate"], = con.execute("""
        SELECT 100.0 * (SELECT COUNT(DISTINCT state_voter_id) FROM voter_participation
                        WHERE election_year=2024 AND kind='GENERAL')
             / COUNT(*) FROM voters WHERE registration_date <= DATE '2024-11-05'""").fetchone()
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

    # SECTION VI's re-registration correction. `registration_date` is the date of
    # the most recent registration EVENT, so the table's rows are not birth
    # cohorts. Detectable only where the vote history reaches: it starts in 2020,
    # so 2022 and 2024 can be cleaned and the earlier rows cannot.
    for yr in (2022, 2024):
        n_all, n_prior = con.execute(f"""
            WITH ev AS (SELECT state_voter_id, MIN(election_year) fy
                        FROM voter_participation GROUP BY 1)
            SELECT COUNT(*), COUNT(*) FILTER (WHERE ev.fy IS NOT NULL AND ev.fy < {yr})
            FROM voters v LEFT JOIN ev USING (state_voter_id)
            WHERE YEAR(v.registration_date) = {yr}
              AND v.age BETWEEN 18 AND 105""").fetchone()
        d[f"rereg{yr}_pct"] = 100.0 * n_prior / n_all
    clean = con.execute("""
        WITH ev AS (SELECT state_voter_id, MIN(election_year) fy
                    FROM voter_participation GROUP BY 1),
        b AS (SELECT v.* FROM voters v LEFT JOIN ev USING (state_voter_id)
              WHERE YEAR(v.registration_date) = 2024
                AND v.age BETWEEN 18 AND 105
                AND (ev.fy IS NULL OR ev.fy >= 2024))
        SELECT median(age - 2), 100.0*COUNT(*) FILTER (WHERE party='REP')/COUNT(*),
               100.0*COUNT(*) FILTER (WHERE party='UNA')/COUNT(*),
               100.0*COUNT(*) FILTER (WHERE party='DEM')/COUNT(*) FROM b""").fetchone()
    (d["clean2024_medage"], d["clean2024_rep"],
     d["clean2024_una"], d["clean2024_dem"]) = (float(x) for x in clean)
    # §VI's claim is that removing re-registrants SHARPENS the young skew rather
    # than explaining it. Asserted as a relation, because two medians that both
    # matched their printed values would still pass if the sign flipped.
    if d["clean2024_medage"] >= d["coh2024_median"]:
        raise SystemExit(
            f"FATAL: §VI argues that dropping detectable re-registrants makes the "
            f"2024 cohort YOUNGER. Measured: cleaned median "
            f"{d['clean2024_medage']:.0f} against {d['coh2024_median']:.0f} for the "
            f"full row. The paragraph's argument no longer holds.")

    _section_vii(con, d)
    _poll_book_conversion(con, d)
    _seat_outcomes(d)
    _donor_ballot_measure_split(con, d)
    _primary_vs_donor_age(con, d)
    con.close()
    assert_relations(d)
    return d


def assert_relations(d: dict) -> None:
    """Every RELATION the paper asserts in words, checked as a relation.

    CONSOLIDATED HERE 2026-08-15, and the reason is freeze-rule 2 rather than tidiness.
    These guards were written inline beside their derivations, which is where they read
    best — and `scripts/mutation_probe_verifiers.py` cannot reach them there, because it
    perturbs the derived dict AFTER `derive()` has returned. A guard the mutation sweep
    cannot exercise is exactly the shape of gate this project has twice shipped believing
    it worked. Pulled into one pure function of the derived dict, every one can be shown
    firing: `tests/test_infrastructure/test_id_relation_gates.py` perturbs a single key per
    case and requires SystemExit.

    These are the claims a coverage gate structurally cannot see. "Within a fraction of a
    point", "level with", "roughly doubled", "direction-safe", "largely persisted" — none
    carries a numeric token to probe, and each of them was either wrong or unsupported in
    the version an external referee read on 2026-08-15.
    """
    if d["e24_RD_65_gap"] > 1.0:
        raise SystemExit(
            f"FATAL: the senior-share parity is Sec II's surviving novel finding "
            f"(R {d['e24_REP_65']:.1f}% vs D {d['e24_DEM_65']:.1f}%). The gap is now "
            f"{d['e24_RD_65_gap']:.1f} points, not 'within a fraction of a point'.")
    if d["e24_DU_1829_gap"] > 1.0:
        raise SystemExit(
            f"FATAL: Sec II now says Democratic and unaffiliated voters are LEVEL on the "
            f"under-30 share — that is why the 'youth sits outside both parties' claim was "
            f"withdrawn. Measured D {d['e24_DEM_1829']:.1f}% vs UNAFF "
            f"{d['e24_UNAFF_1829']:.1f}%, a gap of {d['e24_DU_1829_gap']:.1f} points.")
    if not (d["e24_UNAFF_65"] < d["e24_DEM_65"] - 5
            and d["e24_UNAFF_65"] < d["e24_REP_65"] - 5):
        raise SystemExit(
            f"FATAL: Sec II's replacement claim is that the unaffiliated bloc is younger "
            f"than both parties at the SENIOR end specifically. That no longer holds "
            f"(UNAFF {d['e24_UNAFF_65']:.1f}% vs REP {d['e24_REP_65']:.1f}% / "
            f"DEM {d['e24_DEM_65']:.1f}%).")
    if not (d["rprim_2022"] > d["rprim_2024"] > d["rprim_2018"] > d["rprim_2016"]):
        raise SystemExit(
            f"FATAL: Sec IV now says the Republican contested rate rose to a 2022 peak and "
            f"then fell, with 2024 still above 2018. That ordering no longer holds "
            f"({d['rprim_2016']:.1f} / {d['rprim_2018']:.1f} / {d['rprim_2022']:.1f} / "
            f"{d['rprim_2024']:.1f}), so the sentence describes a different series.")
    if d["rprim_endpoint_ratio"] >= 1.8:
        raise SystemExit(
            f"FATAL: Sec IV withdrew 'roughly doubled across the decade' because the "
            f"endpoints are {d['rprim_endpoint_ratio']:.2f}x, not 2x. They now are — the "
            f"withdrawal needs revisiting rather than being left as it stands.")
    if d["edr_persist_pct"] < 50.0:
        raise SystemExit(
            f"FATAL: Sec III now states that the election-day-2024 registrants largely "
            f"PERSISTED ({d['edr_persist_pct']:.1f}% floor), which is why the churn "
            f"explanation was withdrawn. Measured below 50%, that withdrawal is itself "
            f"wrong and the section must be re-derived — never re-toleranced.")
    if d["venue_total"] != 105:
        raise SystemExit(
            f"FATAL: the decision-venue decomposition covers {d['venue_total']} seats, not "
            f"Idaho's 105. Every share in Sec IV is over that denominator.")
    if d["venuepct_contested_republican"] >= 50.0:
        raise SystemExit(
            f"FATAL: the contested-Republican-primary share is "
            f"{d['venuepct_contested_republican']:.1f}%, at or above 50%, so Sec IV's "
            f"correction — the primary electorate is the largest single venue but settles "
            f"less than half of seats — no longer describes the data.")
    if d.get("xo_UNAFF_survives") or not d.get("xo_DEM_survives"):
        raise SystemExit(
            f"FATAL: Sec VII's revised claim is that Democratic donor loyalty survives the "
            f"hostile bound and the unaffiliated Democratic tilt does NOT. Measured: DEM "
            f"survives={d.get('xo_DEM_survives')}, UNAFF "
            f"survives={d.get('xo_UNAFF_survives')}. The robustness language must be "
            f"re-derived, not adjusted.")


def _poll_book_conversion(con, d: dict) -> None:
    """The §34-904A conversion signature, derived rather than argued.

    An unaffiliated elector who requests a REPUBLICAN primary ballot affiliates at
    the poll book; a Democratic ballot does not affiliate anyone. `voters.party` is
    a single 2026 snapshot with no affiliation date, so a past unaffiliated voter
    who entered the Republican primary is no longer unaffiliated when we look.

    The paper used to report the resulting shares as a behavioural trend ("even
    that door is closing"). These derivations are what make the artifact reading
    testable instead: the Republican column should fall monotonically with distance
    from the snapshot while the Democratic column does not, current-Republican
    concordance should be near-definitional, and re-registration after the primary
    should be far commoner among Republican-ballot pullers.
    """
    for date, tag in (("2022-05-17", "p22"), ("2024-05-21", "p24"), ("2026-05-19", "p26")):
        rows = dict(con.execute(f"""
            SELECT COALESCE(p.ballot_choice, '(none)'), COUNT(*)
            FROM voter_participation p JOIN voters v USING (state_voter_id)
            WHERE p.election_date = DATE '{date}' AND p.kind = 'PRIMARY'
              AND v.party = 'UNA'
            GROUP BY 1""").fetchall())
        tot = sum(rows.values())
        # NOTE: the per-cycle unaffiliated ballot-choice SHARES are already derived
        # above as `unaballot<yr>_*`, on the established basis that excludes NULL
        # ballot_choice. Do not re-derive them here on a different denominator — a
        # first attempt at this section did, and produced values 0.1-0.3 points
        # from the paper's, which reads as a paper defect and is not one.
        # Republican-ballot share of ALL primary ballots. The paper said the
        # one-party lock was "tightening"; this falls across all three cycles.
        allrows = dict(con.execute(f"""
            SELECT COALESCE(p.ballot_choice, '(none)'), COUNT(*)
            FROM voter_participation p
            WHERE p.election_date = DATE '{date}' AND p.kind = 'PRIMARY'
            GROUP BY 1""").fetchall())
        d[f"{tag}_rep_ballot_share"] = (
            100.0 * allrows.get("REP", 0) / sum(allrows.values()))
        # How completely the ballot column is populated, per cycle. §IV's basis note
        # (2026-08-15) argues that ballot choice is the sound measure and party of record
        # is the contaminated one; "populated for 99.6-99.9% of participants" is the claim
        # that makes the first half of that true, and it needs deriving rather than
        # asserting. Complement of the `nochoice_pct_*` range already used two sections up.
        d[f"{tag}_ballot_recorded_pct"] = (
            100.0 * (sum(allrows.values()) - allrows.get("(none)", 0))
            / sum(allrows.values()))
        # Concordance: current-REP voters pulling a REP ballot. Definitional, not
        # behavioural, and printed so the paper can say why.
        n, k = con.execute(f"""
            SELECT COUNT(*), SUM(CASE WHEN p.ballot_choice = 'REP' THEN 1 ELSE 0 END)
            FROM voter_participation p JOIN voters v USING (state_voter_id)
            WHERE p.election_date = DATE '{date}' AND p.kind = 'PRIMARY'
              AND v.party = 'REP'""").fetchone()
        d[f"{tag}_rep_concordance"] = 100.0 * k / n
        d[f"{tag}_una_share"] = 100.0 * tot / sum(allrows.values())
    # Re-registration asymmetry after the 2022 primary.
    for choice, key in (("REP", "rep"), ("DEM", "dem")):
        n, k = con.execute(f"""
            SELECT COUNT(*), SUM(CASE WHEN v.registration_date > DATE '2022-05-17'
                                      THEN 1 ELSE 0 END)
            FROM voter_participation p JOIN voters v USING (state_voter_id)
            WHERE p.election_date = DATE '2022-05-17' AND p.kind = 'PRIMARY'
              AND v.party = 'UNA' AND p.ballot_choice = '{choice}'""").fetchone()
        d[f"rereg_after_{key}"] = 100.0 * k / n
    # §IV's unaffiliated share of the primary electorate, "roughly 5-7%", over every
    # loaded primary rather than the two in the table — same reasoning as the
    # Republican ballot-share range. Placed here, after the per-primary shares are
    # computed: the first draft put it beside the contested-rate ranges 150 lines
    # earlier, where the keys it reads do not exist yet.
    _up = [d[k] for k in ("p22_una_share", "p24_una_share", "p26_una_share") if k in d]
    if len(_up) < 2:
        raise SystemExit(
            "FATAL: §IV states the unaffiliated primary share as a RANGE across "
            "primaries; fewer than two are derivable, so a range cannot be formed.")
    d["una_prim_lo"], d["una_prim_hi"] = min(_up), max(_up)


def _seat_outcomes(d: dict) -> None:
    """November outcomes by primary shape — the check §V used to assert instead.

    §V argued from registration lean that "the general election cannot change an
    outcome". Idaho's own 2024 results refute it, and the refutation is specific:
    nine of the forty-seven seats whose Republican primary drew a single candidate
    were won by a Democrat.
    """
    con = duckdb.connect(str(vp.DATA / "id_statewide.duckdb"), read_only=True)
    try:
        gen, = con.execute(
            "SELECT election_id FROM elections WHERE election_date = DATE '2024-11-05'"
        ).fetchone()
        pri, = con.execute(
            "SELECT election_id FROM elections WHERE election_date = DATE '2024-05-21'"
        ).fetchone()
        _leg = ("(r.race_name LIKE 'REPRESENTATIVE DISTRICT%' "
                "OR r.race_name LIKE 'SENATOR DISTRICT%')")
        for party, key in (("Republican", "r"), ("Democratic", "d")):
            d[f"seats24_{key}"], = con.execute(f"""
                WITH w AS (
                  SELECT r.race_name, cd.party_normalized p,
                         ROW_NUMBER() OVER (PARTITION BY r.race_name
                                            ORDER BY SUM(pr.votes) DESC) rk
                  FROM races r JOIN precinct_results pr USING (race_id)
                  JOIN candidates cd USING (candidate_id)
                  WHERE r.election_id = {gen} AND {_leg}
                  GROUP BY 1, 2)
                SELECT COUNT(*) FROM w WHERE rk = 1 AND p = '{party}'""").fetchone()
        d["seats24_total"] = d["seats24_r"] + d["seats24_d"]
        rows = dict(con.execute(f"""
            WITH prim AS (
              SELECT REPLACE(r.race_name, ' REPUBLICAN', '') seat,
                     COUNT(DISTINCT cd.candidate_id) n_r
              FROM races r JOIN precinct_results pr USING (race_id)
              JOIN candidates cd USING (candidate_id)
              WHERE r.election_id = {pri} AND r.race_name LIKE '% REPUBLICAN' AND {_leg}
              GROUP BY 1),
            gen AS (SELECT race_name seat, p FROM (
              SELECT r.race_name, cd.party_normalized p,
                     ROW_NUMBER() OVER (PARTITION BY r.race_name
                                        ORDER BY SUM(pr.votes) DESC) rk
              FROM races r JOIN precinct_results pr USING (race_id)
              JOIN candidates cd USING (candidate_id)
              WHERE r.election_id = {gen} AND {_leg}
              GROUP BY 1, 2) WHERE rk = 1)
            SELECT CAST(prim.n_r = 1 AS VARCHAR) || '|' || gen.p, COUNT(*)
            FROM prim JOIN gen USING (seat) GROUP BY 1""").fetchall())
        d["single_prim_r_won"] = rows.get("true|Republican", 0)
        d["single_prim_d_won"] = rows.get("true|Democratic", 0)
        d["single_prim_n"] = d["single_prim_r_won"] + d["single_prim_d_won"]
        d["filing_settled_pct"] = 100.0 * d["single_prim_r_won"] / d["seats24_r"]

        # --- THE DECISION-VENUE DECOMPOSITION over all 105 seats (2026-08-15).
        #
        # Added because an external referee pointed out that the paper's own seat counts
        # defeat its own headline: 52 of 105 is 49.5%, which is not "the great majority".
        # His decomposition was three-way (52 primary / 38 filing / 15 November) and is
        # right in structure, but it puts all fifteen Democratic seats in November. Six of
        # them had NO Republican primary at all — no Republican filed — so those were
        # settled at filing too, in the Democrats' favour, and the count that genuinely
        # turned on the general is nine, not fifteen.
        #
        # A four-way cut over the same 105 seats is therefore both more accurate and
        # sharper than either the old framing or the referee's. It is derived here from
        # the loaded canvasses rather than reasoned from the printed cells.
        for a, b, n in con.execute(f"""
            WITH gseat AS (SELECT race_name seat, p FROM (
                SELECT r.race_name, cd.party_normalized p,
                       ROW_NUMBER() OVER (PARTITION BY r.race_name
                                          ORDER BY SUM(pr.votes) DESC) rk
                FROM races r JOIN precinct_results pr USING (race_id)
                JOIN candidates cd USING (candidate_id)
                WHERE r.election_id = {gen} AND {_leg} GROUP BY 1, 2) WHERE rk = 1),
            rprim AS (
                SELECT REPLACE(r.race_name, ' REPUBLICAN', '') seat,
                       COUNT(DISTINCT cd.candidate_id) n_r
                FROM races r JOIN precinct_results pr USING (race_id)
                JOIN candidates cd USING (candidate_id)
                WHERE r.election_id = {pri} AND r.race_name LIKE '% REPUBLICAN' AND {_leg}
                GROUP BY 1)
            SELECT CASE WHEN rprim.n_r IS NULL THEN 'norprim'
                        WHEN rprim.n_r = 1 THEN 'single' ELSE 'contested' END,
                   gseat.p, COUNT(*)
            FROM gseat LEFT JOIN rprim USING (seat) GROUP BY 1, 2""").fetchall():
            d[f"venue_{a}_{str(b).lower()}"] = n
        d["venue_total"] = sum(v for k, v in d.items() if k.startswith("venue_"))
        for key in ("contested_republican", "single_republican",
                    "single_democratic", "norprim_democratic"):
            d[f"venuepct_{key}"] = 100.0 * d.get(f"venue_{key}", 0) / d["venue_total"]
        # Filing plus primary — every seat the Republican nomination process produced the
        # eventual winner of. This is the number that carries "the great majority", and it
        # is about the nomination PROCESS, not about the primary ELECTORATE.
        d["venue_r_nomination_n"] = (d.get("venue_contested_republican", 0)
                                     + d.get("venue_single_republican", 0))
        d["venue_r_nomination_pct"] = 100.0 * d["venue_r_nomination_n"] / d["venue_total"]
    finally:
        con.close()


def _primary_vs_donor_age(con, d: dict) -> None:
    """Donors against primary voters on ONE age basis.

    §VII said "the donor class is the oldest layer of all" while §IV's heading said
    the primary electorate was "grayest of all". Both cannot hold. On the shared
    current-roll basis §VII itself insists on, the primary electorate is at least as
    old, so the §VII superlative was the wrong one.
    """
    sd = str(vp.DATA / "id_statewide.duckdb")
    con.execute(f"ATTACH '{sd}' AS s (READ_ONLY)")
    try:
        cuts = {
            "donors": "v.state_voter_id IN (SELECT state_voter_id FROM s.voter_donor_affiliation_state)",
            "prim24": ("v.state_voter_id IN (SELECT state_voter_id FROM voter_participation "
                       "WHERE election_date = DATE '2024-05-21' AND kind = 'PRIMARY')"),
            "prim24r": ("v.state_voter_id IN (SELECT state_voter_id FROM voter_participation "
                        "WHERE election_date = DATE '2024-05-21' AND kind = 'PRIMARY' "
                        "AND ballot_choice = 'REP')"),
            "prim22": ("v.state_voter_id IN (SELECT state_voter_id FROM voter_participation "
                       "WHERE election_date = DATE '2022-05-17' AND kind = 'PRIMARY')"),
        }
        for key, where in cuts.items():
            p65, med = con.execute(f"""
                SELECT 100.0 * SUM(CASE WHEN v.age >= 65 THEN 1 ELSE 0 END) / COUNT(*),
                       MEDIAN(v.age)
                FROM voters v WHERE {where}""").fetchone()
            d[f"age65_{key}"] = float(p65)
            d[f"medage_{key}"] = float(med)
    finally:
        con.execute("DETACH s")


def _donor_ballot_measure_split(con, d: dict) -> None:
    """How much of the Democratic donor tilt is three ballot-measure committees.

    Reproduces the primary-spec match (tier 0, persons-only, SUNSHINE prefix)
    read-only and tags each matched donor by whether any of their gifts went to
    Reclaim Idaho, Idahoans for Open Primaries or Idahoans United for Women and
    Families. The "all donors" row must reproduce the published panel exactly —
    that reconciliation is what makes the excluded row meaningful.
    """
    # ADAPTED FOR THE PUBLIC REPO. The private copy imports this from `wa_analyzer.db`,
    # which is the product schema and is deliberately never published — so importing it
    # here would make a cited public verifier die with ModuleNotFoundError. Inlined instead,
    # byte-identical in what it renders: the same pattern the public verify_money_votes.py
    # already uses for its IE guard.
    #
    # The COALESCE is LOAD-BEARING, not defensive noise. Written as the obvious
    # `contributor_type NOT IN (...)`, SQL three-valued logic evaluates the predicate to
    # NULL for every NULL-typed row and WHERE treats NULL as false — silently DROPPING
    # every unknown-type row and inverting the intended 'keep unknowns' behaviour, with no
    # error and no symptom beyond a smaller match count.
    def contributor_type_person_sql(alias: str = "ic") -> str:
        col = f"{alias}.contributor_type" if alias else "contributor_type"
        return f"COALESCE({col}, 'UNKNOWN') NOT IN ('ORGANIZATION', 'COMMITTEE')"


    sd = str(vp.DATA / "id_statewide.duckdb")
    c = duckdb.connect(sd, read_only=True)
    try:
        c.execute(f"ATTACH '{VRDB}' AS vrdb (READ_ONLY)")
        c.execute("""
            CREATE TEMP TABLE vk AS
            SELECT last_upper, first_full, zip5, ANY_VALUE(state_voter_id) svid FROM (
              SELECT state_voter_id, UPPER(TRIM(last_name)) last_upper,
                     UPPER(TRIM(first_name)) first_full, SUBSTR(reg_zip, 1, 5) zip5
              FROM vrdb.voters
              WHERE status_code = 'A' AND first_name IS NOT NULL
                AND last_name IS NOT NULL AND reg_zip IS NOT NULL)
            GROUP BY 1, 2, 3 HAVING COUNT(*) = 1""")
        c.execute(f"""
            CREATE TEMP TABLE ck AS
            SELECT ic.contribution_id, ic.fec_candidate_id,
              CASE WHEN ic.contributor_name LIKE '%,%'
                   THEN UPPER(TRIM(SPLIT_PART(ic.contributor_name, ',', 1)))
                   ELSE UPPER(TRIM(SPLIT_PART(TRIM(ic.contributor_name), ' ', 1))) END lu,
              CASE WHEN ic.contributor_name LIKE '%,%'
                   THEN UPPER(SPLIT_PART(TRIM(SPLIT_PART(ic.contributor_name, ',', 2)), ' ', 1))
                   ELSE UPPER(SPLIT_PART(TRIM(ic.contributor_name), ' ', 2)) END ff,
              SUBSTR(ic.contributor_zip, 1, 5) z5
            FROM individual_contributions ic
            WHERE ic.contributor_name IS NOT NULL AND ic.contributor_name <> ''
              AND ic.contributor_zip IS NOT NULL AND ic.contributor_zip <> ''
              AND UPPER(ic.contributor_name) NOT IN
                  ('SMALL CONTRIBUTIONS', 'UNITEMIZED', 'ANONYMOUS')
              AND ic.contribution_id LIKE 'SUNSHINE:%'
              AND {contributor_type_person_sql('ic')}""")
        _bm = ("UPPER(cf.candidate_name) LIKE '%RECLAIM IDAHO%' "
               "OR UPPER(cf.candidate_name) LIKE '%OPEN PRIMARIES%' "
               "OR UPPER(cf.candidate_name) LIKE '%IDAHOANS UNITED%'")
        c.execute(f"""
            CREATE TEMP TABLE donors AS
            SELECT v.svid, MAX(CASE WHEN {_bm} THEN 1 ELSE 0 END) bm
            FROM ck
            JOIN vk v ON v.last_upper = ck.lu AND v.first_full = ck.ff AND v.zip5 = ck.z5
            JOIN candidate_finance cf USING (fec_candidate_id)
            WHERE LENGTH(ck.ff) >= 2
            GROUP BY 1""")
        for tag, where in (("all", ""), ("nobm", " WHERE d.bm = 0")):
            n, dem, rep = c.execute(f"""
                SELECT COUNT(*),
                       100.0 * SUM(CASE WHEN v.party = 'DEM' THEN 1 ELSE 0 END) / COUNT(*),
                       100.0 * SUM(CASE WHEN v.party = 'REP' THEN 1 ELSE 0 END) / COUNT(*)
                FROM donors d JOIN vrdb.voters v ON v.state_voter_id = d.svid{where}""").fetchone()
            d[f"bm_{tag}_n"] = n
            d[f"bm_{tag}_dem"] = float(dem)
            d[f"bm_{tag}_rep"] = float(rep)
        d["bm_touched_n"], = c.execute("SELECT SUM(bm) FROM donors").fetchone()
        d["bm_touched_pct"] = 100.0 * d["bm_touched_n"] / d["bm_all_n"]
        # COUNT(DISTINCT contribution_id), NOT COUNT(*), and the person filter.
        #
        # `candidate_finance` holds ONE ROW PER (fec_candidate_id, election_cycle) —
        # 100,324 rows over 45,825 distinct ids, a 2.19x fan-out overall and exactly
        # 3x for Reclaim Idaho, which filed in 2023, 2024 and 2025. The first
        # version of this derivation used COUNT(*) after that join and published
        # 109,551, which is 3 x 36,517. The probe asserted the paper against this
        # same query at tolerance 0, so agreement was guaranteed by construction and
        # the gate could not have caught it — an independent DERIVATION does not help
        # when both sides share the error.
        #
        # The `person-gifts` noun also needed earning: without the type filter the
        # count includes 11 organisation and 16 unknown-type rows.
        d["bm_reclaim_gifts"], = c.execute("""
            SELECT COUNT(DISTINCT i.contribution_id) FROM individual_contributions i
            JOIN candidate_finance cf USING (fec_candidate_id)
            WHERE i.contribution_id LIKE 'SUNSHINE:%'
              AND i.contributor_type = 'PERSON'
              AND UPPER(cf.candidate_name) LIKE '%RECLAIM IDAHO%'""").fetchone()
        # The superlative the sentence makes, checked rather than asserted: Reclaim
        # must still lead on the de-duplicated count, which it does (36,490 against
        # 27,052 for the next-largest).
        d["bm_reclaim_runner_up"], = c.execute("""
            SELECT COUNT(DISTINCT i.contribution_id) g
            FROM individual_contributions i
            JOIN candidate_finance cf USING (fec_candidate_id)
            WHERE i.contribution_id LIKE 'SUNSHINE:%' AND i.contributor_type = 'PERSON'
              AND UPPER(cf.candidate_name) NOT LIKE '%RECLAIM IDAHO%'
            GROUP BY cf.candidate_name ORDER BY g DESC LIMIT 1""").fetchone()
        if d["bm_reclaim_gifts"] <= d["bm_reclaim_runner_up"]:
            raise RuntimeError(
                f"Reclaim Idaho is no longer the largest Sunshine recipient by "
                f"person-gift count ({d['bm_reclaim_gifts']:,} against "
                f"{d['bm_reclaim_runner_up']:,}). The paper states it is.")
        # The over-representation, before and after, against the roll's DEM share.
        roll_dem, = c.execute(
            "SELECT 100.0 * SUM(CASE WHEN party = 'DEM' THEN 1 ELSE 0 END) / COUNT(*) "
            "FROM vrdb.voters").fetchone()
        d["bm_over_all"] = d["bm_all_dem"] - float(roll_dem)
        d["bm_over_nobm"] = d["bm_nobm_dem"] - float(roll_dem)
    finally:
        c.close()


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
    # ADA NORMALIZED TO ITS REGISTRATION WEIGHT (2026-08-15, referee item 15). "Boise is half
    # the money" sounds more geographically extreme than it is, because Ada is also the
    # largest county on the roll. The donor-class companion already reports county
    # concentration as a RATIO to roll share, so the bare share was also inconsistent across
    # the series. Both sides of the ratio are derived here so the ratio cannot be read off two
    # rounded cells — a fourth-decimal trap this project has already been bitten by twice.
    d["ada_roll_share"], = con.execute(
        "SELECT 100.0*COUNT(*) FILTER (WHERE county_name='ADA')/COUNT(*) FROM voters").fetchone()
    d["ada_dollar_ratio"] = d["don_ada"] / d["ada_roll_share"]
    d["don_ada_donors"], = con.execute(f"""
        SELECT 100.0*COUNT(*) FILTER (WHERE v.county_name='ADA')/COUNT(*)
        FROM {P} a JOIN voters v USING (state_voter_id)""").fetchone()
    d["ada_donor_ratio"] = d["don_ada_donors"] / d["ada_roll_share"]

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

    # --- PARTY-SPECIFIC MISSINGNESS AND THE HOSTILE BOUND (2026-08-15, referee item 14).
    #
    # §VII called two crossover rows "robust, direction-safe" while conceding the Republican
    # row is an upper bound because the unresolved pool skews Republican. That concession is
    # the argument that breaks the unaffiliated row, and the paper made it without noticing:
    # if unresolved recipients lean Republican, they lean Republican for UNAFFILIATED donors
    # too, and the unaffiliated row is the LEAST resolved of the four.
    #
    # The bound is arithmetic. Assign every unresolved donor in a group to R-only — the
    # hostile assignment for a Democratic-tilt claim — and ask whether D-only still exceeds
    # R-only. `xo_<p>_survives` is that test, and it is what the word "direction-safe" has to
    # mean if it means anything.
    for p, n_all, n_res, d_only, r_only in con.execute(f"""
        SELECT {PARTY} p, COUNT(*), COUNT(*) FILTER (WHERE a.d_amount+a.r_amount>0),
               COUNT(*) FILTER (WHERE a.d_amount>0 AND a.r_amount=0),
               COUNT(*) FILTER (WHERE a.r_amount>0 AND a.d_amount=0)
        FROM {P} a JOIN voters v USING (state_voter_id) GROUP BY 1""").fetchall():
        if not n_res:
            continue
        unres = n_all - n_res
        d[f"xo_{p}_resolved_pct"] = 100.0 * n_res / n_all
        d[f"xo_{p}_hostile_d"] = 100.0 * d_only / n_all
        d[f"xo_{p}_hostile_r"] = 100.0 * (r_only + unres) / n_all
        d[f"xo_{p}_survives"] = d_only > r_only + unres

    # Methods: the ID FEC layer's scale, and the pooled table the methods note contrasts.
    d["fec_rows"], fm = con.execute(
        "SELECT COUNT(*), SUM(contribution_amount)/1e6 FROM sw2.individual_contributions "
        "WHERE contribution_id LIKE 'FEC:%'").fetchone()
    d["fec_m"] = float(fm)
    d["fec_matched"], = con.execute(
        "SELECT COUNT(*) FROM sw2.voter_donor_affiliation_fec").fetchone()
    d["pooled_n"], = con.execute(
        "SELECT COUNT(*) FROM sw2.voter_donor_affiliation").fetchone()
    # The pooled panel's party mix, quoted in the boundary section as "D 20% / R
    # 67% / O 13%" and used there to argue the pooled table tracks the Sunshine-only
    # one. That is a claim about two distributions, and neither side of it was
    # derived. `O` is everything that is not DEM or REP — unaffiliated AND other —
    # which is why it cannot be read off the four-way table in Section VII.
    _mix = dict(con.execute("""
        SELECT CASE WHEN v.party IN ('DEM','REP') THEN v.party ELSE 'O' END, COUNT(*)
        FROM sw2.voter_donor_affiliation a JOIN voters v USING (state_voter_id)
        GROUP BY 1""").fetchall())
    _mixtot = sum(_mix.values())
    for k, tag in (("DEM", "d"), ("REP", "r"), ("O", "o")):
        d[f"pooled_{tag}_pct"] = 100.0 * _mix.get(k, 0) / _mixtot

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
    # --- §IV, the poll-book conversion (2026-08-09). The paper reported these
    # shares as a behavioural trend ("even that door is closing") until an
    # adversarial pass established they are a snapshot artifact: Idaho Code
    # §34-904A affiliates an unaffiliated elector who requests a REPUBLICAN
    # ballot, and voters.party is a single 2026 snapshot with no affiliation
    # date. Every figure the corrected reading rests on is asserted here.
    ("§IV unaffiliated ballot choice, three primaries",
     r"\| May 2022 \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| [\d.]+ \|\s*"
     r"\| May 2024 \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| [\d.]+ \|\s*"
     r"\| May 2026 \| \*\*([\d.]+)%\*\* \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \| [\d.]+ \|",
     ("unaballot2022_rep", "unaballot2022_dem", "unaballot2022_np",
      "unaballot2024_rep", "unaballot2024_dem", "unaballot2024_np",
      "unaballot2026_rep", "unaballot2026_dem", "unaballot2026_np"), 0.05),
    ("§IV the conversion signature — monotone Republican column",
     r"Republican column\s*falls monotonically with distance from the snapshot "
     r"\(([\d.]+) → ([\d.]+) → ([\d.]+)\) while the Democratic\s*column does not "
     r"\(([\d.]+) → ([\d.]+) → ([\d.]+)\)",
     ("unaballot2022_rep", "unaballot2024_rep", "unaballot2026_rep",
      "unaballot2022_dem", "unaballot2024_dem", "unaballot2026_dem"), 0.05),
    ("§IV re-registration asymmetry after the 2022 primary",
     r"\*\*([\d.]+)%\*\* carry a registration date \*after\* that primary[^.]*?"
     r"against \*\*([\d.]+)%\*\* of those who pulled a\s*Democratic ballot",
     ("rereg_after_rep", "rereg_after_dem"), 0.05),
    ("§IV current-Republican concordance is definitional",
     r"pulled a Republican ballot in\s*([\d.]+) / ([\d.]+) / ([\d.]+)% of cases",
     ("p22_rep_concordance", "p24_rep_concordance", "p26_rep_concordance"), 0.05),
    ("§IV the 2024 unaffiliated share restated as a lower bound",
     r"The ([\d.]+)% unaffiliated share of the May 2024 primary\s*electorate is not a "
     r"measurement", "p24_UNAFF", 0.05),
    ("Conclusion — the D seat count, restated where the decomposition is summarised",
     r"Democrats took the remaining (\d+) in November", "seats24_d", 0),
    ("§IV the 2026 unaffiliated share is the honest estimate",
     r"unaffiliated registrants are \*\*([\d.]+)%\*\* of that primary electorate",
     "p26_una_share", 0.05),
    ("§IV the Republican ballot share is FALLING",
     r"\*\*([\d.]+)% \(2022\), ([\d.]+)%\s*\(2024\), ([\d.]+)% \(2026\)\*\*",
     ("p22_rep_ballot_share", "p24_rep_ballot_share", "p26_rep_ballot_share"), 0.05),
    # --- THE BARE-INTEGER PERCENTAGES, unprobed until strict_units was enabled here
    # on 2026-08-10. Every one of these is a result; each was auto-exempt because
    # `^\d{1,2}$` is matched against the token with its unit stripped, so `63%`
    # looked like an ordinal. Probing them found one prose/table contradiction in
    # §VII (21%/21% against a table printing 21.6% and 20.0%, inches above).
    ("abstract — the registration headline",
     r"Idaho is \*\*(\d+)%\*\* Republican and \*\*(\d+)%\*\* Democratic by registration",
     ("roll_REP", "roll_DEM"), 0.5),
    ("Boundary — the net decline, restated as a lower bound on gross departures",
     r"the ~(\d+)% gap is a net change", "roll_net_decline_pct", 0.5),
    ("§III — the roll's NET DECLINE against the SoS's 2024 registered total",
     r"net decline of\s*(?:\*\*)?([\d,]+) registrations, ([\d.]+)%\*\*",
     ("roll_net_decline_n", "roll_net_decline_pct"), 0.05),
    ("§IV — the unaffiliated share, roll against primary",
     r"falls from ~(\d+)% of the roll to roughly \*\*(\d+)–(\d+)%\*\* of the primary",
     ("roll_UNAFF", "una_prim_lo", "una_prim_hi"), 0.5),
    ("§IV — the share of Republican-held seats settled at filing, both statements",
     r"seats, (\d+)%\*\*", "filing_settled_pct", 0.5),
    # Repurposed 2026-08-15. It probed "For that 42% of Republican-held seats", a sentence
    # the decomposition rewrite deleted; the same key is still asserted twice elsewhere
    # (§IV and §V), so no check is lost. It now covers the abstract's four venue shares,
    # which are the paper's new headline and were unprobed the moment they were written.
    ("abstract — venue 1, the contested Republican primary",
     r"a \*\*contested\*\* Republican primary for \*\*(\d+)\*\* of them \(\*\*([\d.]+)%\*\*\)",
     ("venue_contested_republican", "venuepct_contested_republican"), 0.05),
    ("abstract — venue 2, a single Republican filer who won",
     r"single filed candidate for \*\*(\d+)\*\* more \(\*\*([\d.]+)%\*\*\)",
     ("venue_single_republican", "venuepct_single_republican"), 0.05),
    ("abstract — venue 3, the November general",
     r"the November general for \*\*(\d+)\*\* \(\*\*([\d.]+)%\*\*\)",
     ("venue_single_democratic", "venuepct_single_democratic"), 0.05),
    ("abstract — venue 4, no Republican filed at all",
     r"the remaining \*\*(\d+)\*\* \(\*\*([\d.]+)%\*\*\)",
     ("venue_norprim_democratic", "venuepct_norprim_democratic"), 0.05),
    ("§IV — the Republican contested-rate series",
     r"\*\*(\d+)% \(2016\) → (\d+)% \(2018\) → (\d+)% \(2022\) → (\d+)% \(2024\)\*\*",
     ("rprim_2016", "rprim_2018", "rprim_2022", "rprim_2024"), 0.5),
    ("§IV — the Democratic contested range over the same cycles",
     r"almost never contested \((\d+)–(\d+)% across these cycles\)",
     ("dprim_lo", "dprim_hi"), 0.5),
    ("Opening — the unaffiliated quarter facing the affiliation requirement",
     r"The (\d+)% of registrants who decline a party", "roll_UNAFF", 0.5),
    ("§VI — the full table's Democratic and unaffiliated endpoints",
     r"Democratic share sits near (\d+)% and the unaffiliated share climbs\s+to (\d+)%",
     ("coh2024_DEM", "coh2024_UNAFF"), 0.5),
    ("§VI — the full row's Republican share, against the cleaned one",
     r"where it was \((\d+\.\d)% → \*\*([\d.]+)%\*\*",
     ("coh2024_REP", "clean2024_rep"), 0.05),
    ("§VI — the full row's unaffiliated and Democratic shares, against cleaned",
     r"share rises\s+([\d.]+)% → \*\*([\d.]+)%\*\* while the Democratic share falls "
     r"([\d.]+)% → \*\*([\d.]+)%\*\*",
     ("coh2024_UNAFF", "clean2024_una", "coh2024_DEM", "clean2024_dem"), 0.05),
    ("§VII — Democrats' roll, donor and dollar shares",
     r"they are (\d+)% of the roll but (\d+)% of donors and give (\d+)% of the money",
     ("roll_DEM", "don_DEM_share", "don_DEM_dollars"), 0.5),
    ("§VII — the unaffiliated donors' absence",
     r"nearly absent \((\d+)% of donors, (\d+)% of dollars\)",
     ("don_UNAFF_share", "don_UNAFF_dollars"), 0.5),
    ("§VII — the Republican registration share restated as a constraint",
     r"as a (\d+)%-Republican state must", "roll_REP", 0.5),
    ("§VII — Democratic donor loyalty",
     r"near-monolithic donors \((\d+)% give only to Democrats", "xo_DEM_d", 0.5),
    ("§VII — Republican donor loyalty",
     r"predominantly fund Republicans \((\d+)%\)", "xo_REP_r", 0.5),
    # --- Boundary: the coverage table and the bounds it supports (2026-08-10).
    #
    # RESTRUCTURED 2026-08-15, after an external referee found two of the three SoS ballot
    # counts wrong. The old shape had both failure modes this project keeps re-learning:
    #
    #   * 2024's ballot count, 917,608, appeared ONLY inside a regex ANCHOR. A number in an
    #     anchor looks probed and is not — it is a precondition for the check, so the check
    #     silently stops running if it changes, and nothing ever compares it to anything.
    #     That is the same defect the 2026-08-11 WA sitting recorded, in the same file shape.
    #   * 2022's count WAS probed — against `id_sos_2022`, which was the same wrong literal.
    #     A probe that asserts a constant against itself passes forever and carries no
    #     information. It is the referee's own point: an asserting verifier can faithfully
    #     assert an incorrect external constant, and the only real check is provenance.
    #
    # So the ballot column is now CAPTURED in every row and asserted against the pin, and
    # the pin carries the URL and retrieval date. That still cannot verify the SoS; it makes
    # the paper, the verifier and one citable source agree or fail loudly.
    ("Boundary — 2024 coverage row, ballot count included",
     r"\| Nov 2024 \| ([\d,]+) \| ([\d,]+) \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \| "
     r"\*\*([\d.]+) – ([\d.]+)%\*\* \|",
     ("id_sos_2024", "cover2024_n", "cover2024_pct", "gen2024_65+",
      "bound2024_lo", "bound2024_hi"), 0.05),
    ("Boundary — 2022 coverage row, ballot count included",
     r"\| Nov 2022 \| ([\d,]+) \| ([\d,]+) \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \| "
     r"\*\*([\d.]+) – ([\d.]+)%\*\* \|",
     ("id_sos_2022", "cover2022_n", "cover2022_pct", "gen2022_65+",
      "bound2022_lo", "bound2022_hi"), 0.05),
    ("Boundary — 2020 coverage row, ballot count included",
     r"\| Nov 2020 \| ([\d,]+) \| ([\d,]+) \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \| "
     r"\*\*([\d.]+) – ([\d.]+)%\*\* \|",
     ("id_sos_2020", "cover2020_n", "cover2020_pct", "gen2020_65+",
      "bound2020_lo", "bound2020_hi"), 0.06),
    ("Boundary — election-day registrants, now cited as a withdrawn mechanism",
     r"the churn of the\s*([\d,]+) election-day registrants", "id_edr_2024", 0),
    ("Boundary — Washington's roll churn, the mechanism argument",
     r"the ([\d,]+) voters\s+who left the rolls are \*\*([\d.]+)% 65\+ against ([\d.]+)% "
     r"of the ([\d,]+) retained\*\*",
     ("wachurn_gone_n", "wachurn_gone_65", "wachurn_kept_65", "wachurn_kept_n"), 0.05),
    # --- Section VI: the re-registration correction.
    ("§VI — detectable re-registration in the two cleanable rows",
     r"dated 2024, \*\*([\d.]+)% had already voted in an earlier election\*\*; of\s+"
     r"those dated 2022, \*\*([\d.]+)%\*\*",
     ("rereg2024_pct", "rereg2022_pct"), 0.05),
    ("§VI — the 2024 row is a re-registration count",
     r"the ([\d,]+) registrants dated 2024", "coh2024_n", 0),
    ("§VI — the cleaned median age against the full row's",
     r"registration (\d+) → \*\*(\d+)\*\*",
     ("coh2024_median", "clean2024_medage"), 0.05),
    ("Boundary — the inflated all-voter rate the shrunken roll produces",
     r"all-voter 2024 general rate is ~(\d+)%", "gen24_allvoter_rate", 0.5),
    ("Boundary — party-resolved share, restated in the recipient-party note",
     r"reconstructed for ~(\d+)% of matched donors", "xo_res_donors", 0.5),
    ("Boundary — the pooled panel's party mix",
     r"its mix D (\d+)% / R (\d+)% / O (\d+)%",
     ("pooled_d_pct", "pooled_r_pct", "pooled_o_pct"), 0.5),
    # --- §V, the seat outcomes that refute the registration-lean inference.
    ("§V Democrats won seats the registration map calls safe",
     r"Democrats won \*\*(\d+) of Idaho's (\d+) legislative seats\*\* \((\d+) R / (\d+) D",
     ("seats24_d", "seats24_total", "seats24_r", "seats24_d"), 0),
    ("§V single-candidate primaries did not all settle a seat",
     r"Of the (\d+) seats whose Republican primary drew a single candidate",
     "single_prim_n", 0),
    ("abstract — the nomination process against the primary electorate",
     r"produced\s*the winner in \*\*(\d+) of (\d+)\*\* seats, \*\*([\d.]+)%\*\*",
     ("venue_r_nomination_n", "venue_total", "venue_r_nomination_pct"), 0.05),
    ("§IV single-candidate primary outcomes, both ways",
     r"\*\*(\d+) of them were won by a Democrat in November\*\*,\s*while all (\d+)\s*"
     r"contested-primary seats went Republican",
     ("single_prim_d_won", "venue_contested_republican"), 0),
    ("§V filing-settled share restated",
     r"\*\*(\d+) of the\s*(\d+) Republican-held seats, (\d+)%\*\*",
     ("single_prim_r_won", "seats24_r", "filing_settled_pct"), 0.5),
    # --- §VII, the ballot-measure circularity and the age superlative (2026-08-09).
    ("§VII ballot-measure committees in the matched panel",
     r"drew gifts from \*\*([\d,]+) of the ([\d,]+) matched\s*donors \(([\d.]+)%\)\*\*",
     ("bm_touched_n", "bm_all_n", "bm_touched_pct"), 0.05),
    ("§VII Reclaim Idaho gift count",
     r"by gift count, with ([\d,]+) person-gifts", "bm_reclaim_gifts", 0),
    ("§VII donor party mix with and without the three committees",
     r"falls from \*\*([\d.]+)% to ([\d.]+)%\*\* and the Republican share\s*rises from "
     r"([\d.]+)% to ([\d.]+)%",
     ("bm_all_dem", "bm_nobm_dem", "bm_all_rep", "bm_nobm_rep"), 0.05),
    ("§VII the over-representation before and after",
     r"so the \+([\d.]+)-point Democratic over-representation becomes\s*\*\*\+([\d.]+)\*\*",
     ("bm_over_all", "bm_over_nobm"), 0.05),
    ("§VII donors are not older than the primary electorate",
     r"at least as old: ([\d.]+)% of 2024 primary voters\s*are 65\+ \(([\d.]+)% of "
     r"Republican-ballot voters,\s*([\d.]+)% of 2022 primary voters\), against ([\d.]+)% of "
     r"matched donors, all four at median age\s*(\d+)",
     ("age65_prim24", "age65_prim24r", "age65_prim22", "age65_donors",
      "medage_donors"), 0.05),
    # --- Abstract, gated 2026-08-07 when it moved in from the metadata file. Each figure is a
    # restatement of one asserted in a section below, and each gets its own probe for that
    # reason: the abstract is the most-read and least-revised part of a paper.
    ("abstract — roll size, exact",
     r"statewide voter file for \*\*([\d,]+)\*\* registrants", "roll_n", 0),
    ("abstract — party-neutral 65+ share among 2024 general voters",
     r"65-and-over share, \*\*([\d.]+)%\*\* against \*\*([\d.]+)%\*\*",
     ("e24_REP_65", "e24_DEM_65"), 0.05),
    ("abstract — 2024 primary electorate against the roll, REP share",
     r"primary electorate is\s*\*\*([\d.]+)%\*\* Republican by party of record against\s*"
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
    # The denominator note added with those keys. Nine cells, and every one is a restatement of a
    # figure printed elsewhere in the section — which is exactly why each gets a probe rather than
    # an exemption: the note's whole job is to say that two of them differ.
    ("§IV the two ballot-share denominators, named",
     r"The ([\d.]+) / ([\d.]+) range above is the Republican\s+share of ballots \*\*whose party "
     r"choice is recorded\*\*.*?([\d.]+)% / ([\d.]+)% / ([\d.]+)% — is the Republican share of "
     r"\*\*all primary participants\*\*, including the\s+([\d.]+)–([\d.]+)% of them \(([\d,]+) "
     r"to ([\d,]+) voters a cycle\)",
     ("ballot_lo", "ballot_hi", "p22_rep_ballot_share", "p24_rep_ballot_share",
      "p26_rep_ballot_share", "nochoice_pct_lo", "nochoice_pct_hi",
      "nochoice_n_lo", "nochoice_n_hi"), 0.05),
    ("§IV contested Republican legislative primaries",
     r"\*\*(\d+) drew a Republican primary in 2024\*\*.*?of those \d+, just \*\*(\d+) \((\d+)%\) "
     r"were contested\*\* and \*\*(\d+) \((\d+)%\) had a single Republican",
     ("prim_races", "prim_contested", "prim_contested_pct", "prim_single", "prim_single_pct"),
     0.5),

    # ---- Section V
    ("§VII districts in the widest registration band, cross-checked against §V's count",
     r"the (\d+) districts at R\+40 or more", "ld_safe_r", 0),

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
    # The old "less Republican (57.5% vs the high-60s...)" wording was replaced when
    # §VI was rewritten for the re-registration correction. The same value is now
    # asserted by "the full row's Republican share, against the cleaned one" —
    # re-anchored rather than deleted, since dropping a probe silently drops a check.

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
    ("§VII geography — Ada's dollars, its roll weight, and the ratio of the two",
     r"Ada County \(Boise\) accounts for \*\*([\d.]+)%\*\* of matched donor dollars\s*"
     r"against \*\*([\d.]+)%\*\* of the roll — \*\*([\d.]+)×\*\*",
     ("don_ada", "ada_roll_share", "ada_dollar_ratio"), 0.05),
    ("§VII geography — the same on donor counts rather than dollars",
     r"it is ([\d.]+)%, or ([\d.]+)×", ("don_ada_donors", "ada_donor_ratio"), 0.05),
    ("§VII donors by registration band — widest band, then the eight narrower ones",
     r"more hold\s*([\d,]+) donors who are \*\*([\d.]+)% Republican / ([\d.]+)% "
     r"Democratic\*\*, while the eight districts\s*between R\+5 and R\+40 hold ([\d,]+) "
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

    # ================================================================================
    # ADDED 2026-08-15 — the external Idaho referee round. Every figure the rewrite
    # introduced gets a probe in the same round that writes it, which is freeze-rule 2:
    # a round must close its own additions. The RELATIONS these figures support (the
    # senior-share parity, the under-30 level-pegging, the hostile-bound direction test,
    # the contestation series' shape, the election-day persistence floor) have no numeric
    # token a coverage gate can see, so they are asserted as guards in derive() /
    # _seat_outcomes / _section_vii instead.
    # ================================================================================
    ("abstract — the seat denominator the whole decomposition sits on",
     r"decomposition of all\s*\*\*(\d+)\*\* legislative seats", "venue_total", 0),
    ("abstract — the unaffiliated bloc's senior share against the two parties'",
     r"\*\*([\d.]+)%\*\* aged 65 or\s*over against roughly ([\d.]+)% in both parties",
     ("e24_UNAFF_65", "_rd_65_mean"), 0.06),
    ("abstract — unaffiliated and Democratic level on the under-30 share",
     r"level at \*\*([\d.]+)%\*\* and \*\*([\d.]+)%\*\* under 30",
     ("e24_UNAFF_1829", "e24_DEM_1829"), 0.05),
    ("abstract — the directly observed Republican ballot share, 2024",
     r"\*\*([\d.]+)%\*\* of 2024 primary participants took a\s*Republican ballot",
     "p24_rep_ballot_share", 0.05),

    # ---- §II, the narrowed party-neutrality claim
    ("§II — the unaffiliated senior deficit against both parties",
     r"\(([\d.]+)% against ([\d.]+)% and ([\d.]+)%\)",
     ("e24_UNAFF_65", "e24_REP_65", "e24_DEM_65"), 0.05),
    ("§II — unaffiliated and Democratic level on the under-30 share",
     r"level there — ([\d.]+)% against\s*([\d.]+)%",
     ("e24_UNAFF_1829", "e24_DEM_1829"), 0.05),

    # ---- §III, the measured refutation of the same-day-churn mechanism
    ("§III — election-day registrants still on the roll, the floor and its base",
     r"\*\*([\d,]+) of the ([\d,]+) election-day registrants are still on the 2026\s*"
     r"roll, at least ([\d.]+)%\*\*",
     ("edr_persist_n", "id_edr_2024", "edr_persist_pct"), 0.05),
    ("§III — how many of those carry a 2024 general vote record",
     r"and ([\d,]+) of them carry a 2024 general vote record", "edr_persist_voted24", 0),

    # ---- §IV, the decision-venue table
    ("§IV venue table — contested Republican primary",
     r"a Republican won in November \| \*\*(\d+)\*\* \| \*\*([\d.]+)%\*\* \|",
     ("venue_contested_republican", "venuepct_contested_republican"), 0.05),
    ("§IV venue table — single Republican filer who won",
     r"that Republican won in November \| \*\*(\d+)\*\* \| \*\*([\d.]+)%\*\* \|",
     ("venue_single_republican", "venuepct_single_republican"), 0.05),
    ("§IV venue table — single Republican filer who lost",
     r"a \*\*Democrat\*\* won \| \*\*(\d+)\*\* \| \*\*([\d.]+)%\*\* \|",
     ("venue_single_democratic", "venuepct_single_democratic"), 0.05),
    ("§IV venue table — no Republican filed",
     r"no\* Republican filed; a Democrat won \| \*\*(\d+)\*\* \| \*\*([\d.]+)%\*\* \|",
     ("venue_norprim_democratic", "venuepct_norprim_democratic"), 0.05),
    ("§IV — the nomination process against the primary electorate",
     r"eventual winner of \*\*(\d+) of (\d+) seats \(([\d.]+)%\)\*\*",
     ("venue_r_nomination_n", "venue_total", "venue_r_nomination_pct"), 0.05),
    ("§IV — the contested primary as the largest single venue",
     r"contested primary settles (\d+) seats, ([\d.]+)%\*\*",
     ("venue_contested_republican", "venuepct_contested_republican"), 0.05),
    ("§IV — the filing total, and the two bands that make it up",
     r"\*\*(\d+) seats\*\* \((\d+) Republican-held plus (\d+) Democratic-held\)",
     ("_filing_total", "venue_single_republican", "venue_norprim_democratic"), 0),

    # ---- §IV, the two-denominator basis note (referee item 4)
    ("§IV basis note — ballot choice against party of record, both cycles",
     r"Republican ballots were \*\*([\d.]+)%\*\* of 2024 primary participants against\s*"
     r"([\d.]+)% classified\s*Republican, and \*\*([\d.]+)%\*\* in 2022 against ([\d.]+)%",
     ("p24_rep_ballot_share", "p24_REP", "p22_rep_ballot_share", "p22_REP"), 0.05),
    ("§IV basis note — how completely the ballot column is populated",
     r"populated for ([\d.]+)–([\d.]+)% of participants",
     ("_ballot_recorded_lo", "_ballot_recorded_hi"), 0.05),

    # ---- §VII, the party-specific hostile bounds (referee item 14)
    ("§VII — resolution rate by donor registration, all three groups",
     r"resolves for \*\*([\d.]+)%\*\* of Republican donors, \*\*([\d.]+)%\*\* of\s*"
     r"Democratic donors and only \*\*([\d.]+)%\*\* of unaffiliated donors",
     ("xo_REP_resolved_pct", "xo_DEM_resolved_pct", "xo_UNAFF_resolved_pct"), 0.05),
    ("§VII hostile bound — registered Republicans",
     r"\| Registered Republican \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \|",
     ("xo_REP_resolved_pct", "xo_REP_d", "xo_REP_hostile_d", "xo_REP_hostile_r"), 0.05),
    ("§VII hostile bound — registered Democrats, the row that survives",
     r"\| Registered Democratic \| ([\d.]+)% \| ([\d.]+)% \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \|",
     ("xo_DEM_resolved_pct", "xo_DEM_d", "xo_DEM_hostile_d", "xo_DEM_hostile_r"), 0.05),
    ("§VII hostile bound — registered unaffiliated, the row that does not",
     r"\| Registered unaffiliated \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \|",
     ("xo_UNAFF_resolved_pct", "xo_UNAFF_d", "xo_UNAFF_hostile_d", "xo_UNAFF_hostile_r"), 0.05),
    ("§VII — the unresolved share of unaffiliated donors, restated in prose",
     r"hostile assignment of\s*the unresolved (\d+)%", "_unaff_unresolved_pct", 0.5),


    # ---- Restatements introduced by the 2026-08-15 rewrite. Every one is a figure the
    # paper prints twice, and the project's rule is to close an unmapped token with a
    # DERIVATION rather than an exemption wherever the figure is derivable — a second
    # printing is exactly where a paper drifts against itself.
    ("§III — the unaffiliated primary share, restated after the mechanism paragraph",
     r"So the ([\d.]+)% is not a measure of people turned away", "p24_UNAFF", 0.05),
    ("§III — gross departures bounded below by the net decline",
     r"at least\*\* ([\d,]+) and could be far more", "roll_net_decline_n", 0),
    ("§IV — the seat denominator, restated at the table",
     r"The decision venue, all (\d+) legislative seats", "venue_total", 0),
    ("§IV — the arithmetic the referee's objection rested on",
     r"(\d+) of (\d+) is ([\d.]+)%, so \"the closed",
     ("venue_contested_republican", "venue_total", "venuepct_contested_republican"), 0.05),
    ("§IV — the contaminated headline share, quoted then translated",
     r"\"([\d.]+)% of the 2024 primary electorate was Republican\" therefore means, "
     r"exactly, \*([\d.]+)% of", ("p24_REP", "p24_REP"), 0.05),
    ("§IV — both ratios the withdrawn 'doubled' claim is measured against",
     r"36 → 53 is ([\d.]+)×, and the ([\d.]+)× is 2016 to the 2022 peak",
     ("rprim_endpoint_ratio", "rprim_peak_ratio"), 0.05),
    ("§VII — Ada's dollar share as it was previously printed, rounded",
     r"The bare (\d+)% stood alone here", "don_ada", 0.5),
    ("§VII — the Republican crossover upper bound, restated in the bounds table",
     r"\(the ([\d.]+)% is an upper bound\)", "xo_REP_d", 0.05),
    ("Boundary — the corrected SoS counts, restated in the correction note",
     r"against the Secretary of State's ([\d,]+) and ([\d,]+)",
     ("id_sos_2024", "id_sos_2022"), 0),
    ("Boundary — what the correction moved, 2022 coverage and bound",
     r"to ([\d.]+)% and its bound from [\d.]+–[\d.]+ to ([\d.]+)–([\d.]+)",
     ("cover2022_pct", "bound2022_lo", "bound2022_hi"), 0.05),
    ("Boundary — the election-day persistence floor, restated",
     r"at least ([\d.]+)% of them are still on the roll", "edr_persist_pct", 0.05),
    ("Boundary — the official turnout rate's two inputs",
     r"\(([\d,]+) ballots / ([\d,]+) registered", ("id_sos_2024", "id_sos_reg_2024"), 0),

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
    # Six of these eight anchors changed on 2026-08-15 because the headings did. Anchors are
    # section IDENTITY here, not decoration: a start anchor that no longer matches raises
    # rather than skipping (by design — see _verify_prose.slice_with_offset), which is what
    # forced this edit rather than letting six sections quietly drop out of the coverage gate.
    "sec1": ("## I. The midterm electorate", "## II. Senior representation"),
    "sec2": ("## II. Senior representation", "## III. The unaffiliated quarter"),
    "sec3": ("## III. The unaffiliated quarter", "## IV. Where seats are actually settled"),
    "sec4": ("## IV. Where seats are actually settled", "## V. Every district carries"),
    "sec5": ("## V. Every district carries", "## VI. Recently-dated registration"),
    "sec6": ("## VI. Recently-dated registration", "## VII. The donor class"),
    "sec7": ("## VII. The donor class", "## Boundary of inference"),
    "boundary": ("## Boundary of inference", "## What it means"),
}

COVERAGE_EXEMPT = [
    (r"^(?:19|20)\d{2}$", "a calendar year, not a result"),
    (r"^\d{1,2}$", "small integer — district/seat counts, band edges, list ordinals"),
    # COHORT EDGES under strict_units — "the top 1% of matched donors supply 40%"
    # names a group; the 40% is the measurement and is probed (don_top1/don_top10).
    # Written as explicit unit-carrying patterns so the waiver reaches exactly these
    # two tokens; a literal on "1" and "10" would cover every bare 1 and 10 here.
    (r"^1%$", "the top-1% cohort EDGE; the share it names is probed as don_top1"),
    (r"^10%$", "the top-10% cohort EDGE; probed as don_top10"),
]

COVERAGE_EXEMPT_LITERAL: dict[str, str] = {
    # Added 2026-08-10 when strict_units was enabled here.
    "72": "the upper end of the initial-based match-key precision range (48-72%), "
          "a result of the donor-class companion's Appendix F blinded validation. "
          "Owned by verify_donor_class.py, which asserts it against the frozen "
          "verdict CSVs; the lower end 48 is exempt as a bare integer. Restated "
          "here as context for the full-name restriction, not measured here",
    "904": "part of the statutory citation Idaho Code § 34-904A, the primary-eligibility "
           "provision that makes the primary closed. Not a quantity. Its CONSEQUENCES are asserted: see "
           "the four '§IV the conversion signature' probes",
    "4.1": "years between the May 2022 primary and the 2026 snapshot — the recency "
           "column of the ballot-choice table, which is arithmetic on two dates rather "
           "than a derived figure",
    "2.1": "years between the May 2024 primary and the snapshot, as above",
    "0.1": "years between the May 2026 primary and the snapshot, as above",
    "0.7": "the New York companion's switching bound, cited from that paper and "
           "asserted by verify_who_decides_ny.py, not here",
    "1.4": "the upper end of the same New York bound, as above",
    # Official Idaho SoS publications. These are the EXTERNAL benchmark the survivorship
    # caveat is measured against, so by construction the voter file cannot reproduce them —
    # that mismatch is the caveat's whole point.
    "1.18": "registrants at the November 2024 election, published by the Idaho SoS. The "
            "external benchmark the survivorship caveat is stated against; the voter file "
            "holds the 2026 extract (1.03M), which IS derived",
    "77.8": "official 2024 general turnout rate, Idaho SoS. External by design — the paper "
            "cites it to show its own ~94% is survivorship-inflated",
    # --- RETIRED FIGURES, narrated in place. Each is a number the paper printed until
    # 2026-08-15 and now prints only to say what it was and why it is gone. They are not
    # derivable — that is what "retired" means — so an exemption is the only honest
    # treatment, and each names what REPLACED it so the pairing cannot be lost. Retired
    # figures deliberately do NOT go in withdrawn_claims.csv: that register guards
    # PHRASES, and forbidding a number there fails papers for quoting their own history
    # correctly (see tests/test_infrastructure/test_withdrawn_claims.py).
    "917,608": "RETIRED 2026-08-15. The wrong 2024 ballots-cast figure, carried as a "
               "Python literal in this file and in the Boundary table. The SoS's own "
               "figure is 917,469, now pinned in id_sos_turnout_history_2026-08-15.csv "
               "and probed as id_sos_2024",
    "595,602": "RETIRED 2026-08-15. The wrong 2022 ballots-cast figure; the SoS's is "
               "599,493, pinned and probed as id_sos_2022. This one was PROBED against "
               "the same wrong literal, so the check compared a constant to itself",
    "96.0": "RETIRED 2026-08-15. The 2022 coverage share computed on the wrong ballot "
            "count; the corrected value is 95.4%, probed as cover2022_pct",
    "33.0": "RETIRED 2026-08-15. The lower end of the 2022 65+ bound on the wrong ballot "
            "count; corrected to 32.8, probed as bound2022_lo",
    "37.0": "RETIRED 2026-08-15. The upper end of the same bound; corrected to 37.4, "
            "probed as bound2022_hi",
    "121,000": "Election-Day same-day registrants, Idaho SoS, rounded. The exact count "
               "121,015 is probed as id_edr_2024, and §III now measures what became of "
               "that cohort rather than assuming it churned",
    "411": "part of the statutory citation Idaho Code § 34-411A, which supplies the "
           "same-day affiliation mechanism and the clause requiring the county clerk to "
           "record the affiliation in the registration system. Not a quantity — same "
           "treatment as the 904 of § 34-904A above. Its CONSEQUENCES are asserted: see "
           "the four '§IV the conversion signature' probes",
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
    # Derived-from-derived, kept here rather than in derive() so it is obvious these are
    # presentation conveniences for a sentence, not independent measurements. Each is
    # computed on UNROUNDED inputs — the rounding rule that produced the +76.8/+76.9 flip.
    d["_rd_65_mean"] = (d["e24_REP_65"] + d["e24_DEM_65"]) / 2.0
    d["_filing_total"] = d["venue_single_republican"] + d["venue_norprim_democratic"]
    d["_unaff_unresolved_pct"] = 100.0 - d["xo_UNAFF_resolved_pct"]
    d["_ballot_recorded_lo"] = min(d[f"p{y}_ballot_recorded_pct"] for y in (22, 24, 26))
    d["_ballot_recorded_hi"] = max(d[f"p{y}_ballot_recorded_pct"] for y in (22, 24, 26))
    stats: dict = {}
    rc = vp.run("WHO DECIDES IDAHO — prose scraped and asserted against the voter file",
                norm, PROBES, d, UNCHECKED, vp.wants_coverage(), spans_out=spans,
                stats_out=stats)
    fails = vp.audit_coverage(audit_sections, spans, offsets, tuple(AUDIT_BOUNDS),
                              COVERAGE_EXEMPT, COVERAGE_EXEMPT_LITERAL,
                              COVERAGE_EXEMPT_SECTIONS, strict_units=True)
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
