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
    ID_SOS_REG_2024 = 1_178_750
    d["roll_turnover_pct"] = 100.0 * (ID_SOS_REG_2024 - d["roll_n"]) / ID_SOS_REG_2024

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
    # SoS certified ballots cast, from the official canvasses:
    #   2020  878,527   (1,082,417 registered, 81.2%)
    #   2022  595,602   (1,048,263 registered, 56.8%)
    #   2024  917,608   (1,178,750 registered, 77.8%)
    ID_SOS_BALLOTS = {2020: 878_527, 2022: 595_602, 2024: 917_608}
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
    return d


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
    ("§IV Democrats won seats, restated in the section lead",
     r"Democrats won (\d+) of Idaho's (\d+) legislative seats in\s*November 2024",
     ("seats24_d", "seats24_total"), 0),
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
    ("Boundary — the same turnover figure, restated as an upper bound",
     r"the ~(\d+)% gap is an upper bound", "roll_turnover_pct", 0.5),
    ("§III — the roll's turnover against the SoS's 2024 registered total",
     r"roughly a \*\*(\d+)%\s+turnover in eighteen months\*\*", "roll_turnover_pct", 0.5),
    ("§IV — the unaffiliated share, roll against primary",
     r"falls from ~(\d+)% of the roll to roughly \*\*(\d+)–(\d+)%\*\* of the primary",
     ("roll_UNAFF", "una_prim_lo", "una_prim_hi"), 0.5),
    ("§IV — the share of Republican-held seats settled at filing, both statements",
     r"seats, (\d+)%\*\*", "filing_settled_pct", 0.5),
    ("§IV — the same share restated in the next sentence",
     r"For that (\d+)% of Republican-held seats", "filing_settled_pct", 0.5),
    ("§IV — the Republican contested-rate series",
     r"\*\*(\d+)% \(2016\) → (\d+)% \(2018\) → (\d+)% \(2022\) → (\d+)% \(2024\)\*\*",
     ("rprim_2016", "rprim_2018", "rprim_2022", "rprim_2024"), 0.5),
    ("§IV — the Democratic contested range over the same cycles",
     r"almost never contested \((\d+)–(\d+)% across these cycles\)",
     ("dprim_lo", "dprim_hi"), 0.5),
    ("§IV — the unaffiliated quarter shut out of the closed primary",
     r"stays \*closed\* to the ~(\d+)% of registrants", "roll_UNAFF", 0.5),
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
    ("§VII — Republican donor loyalty and the apparent crossover",
     r"predominantly fund Republicans \((\d+)%\); the apparent ~(\d+)% giving only to",
     ("xo_REP_r", "xo_REP_d"), 0.5),
    # --- Boundary: the coverage table and the bounds it supports (2026-08-10).
    ("Boundary — 2024 coverage row",
     r"\| Nov 2024 \| 917,608 \| ([\d,]+) \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \| "
     r"\*\*([\d.]+) – ([\d.]+)%\*\* \|",
     ("cover2024_n", "cover2024_pct", "gen2024_65+", "bound2024_lo", "bound2024_hi"), 0.05),
    ("Boundary — the SoS ballot counts the coverage table divides by",
     r"\| Nov 2022 \| ([\d,]+) \|", "id_sos_2022", 0),
    ("Boundary — the 2020 SoS ballot count",
     r"\| Nov 2020 \| ([\d,]+) \|", "id_sos_2020", 0),
    ("Boundary — 2022 coverage row",
     r"\| Nov 2022 \| 595,602 \| ([\d,]+) \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \| "
     r"\*\*([\d.]+) – ([\d.]+)%\*\* \|",
     ("cover2022_n", "cover2022_pct", "gen2022_65+", "bound2022_lo", "bound2022_hi"), 0.05),
    ("Boundary — 2020 coverage row",
     r"\| Nov 2020 \| 878,527 \| ([\d,]+) \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \| "
     r"\*\*([\d.]+) – ([\d.]+)%\*\* \|",
     ("cover2020_n", "cover2020_pct", "gen2020_65+", "bound2020_lo", "bound2020_hi"), 0.06),
    ("Boundary — election-day registrants inside the SoS registered total",
     r"([\d,]+) of that 1\.18M\s+registered on election day", "id_edr_2024", 0),
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
    ("§V what filing actually settled",
     r"\*\*(\d+) of the (\d+) Republican-held seats \((\d+)%\)\*\*",
     ("single_prim_r_won", "seats24_r", "filing_settled_pct"), 0.5),
    ("§V single-candidate primary outcomes, both ways",
     r"Of those 47, \*\*(\d+)\*\* were\s*won by a Republican in November and \*\*(\d+)\*\* by a "
     r"Democrat",
     ("single_prim_r_won", "single_prim_d_won"), 0),
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
    "904": "part of the statutory citation Idaho Code § 34-904A, the poll-book "
           "affiliation provision. Not a quantity. Its CONSEQUENCES are asserted: see "
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
