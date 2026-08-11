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

WHAT THE CONVERSION FOUND. Section II's table and Section III's participation rates did not
reproduce on the roll as it stands, on either the active or the full basis, and every
deviation ran one way. Appendix A and Section I are ELECTORATE-denominated — the set of people
who voted in a past election cannot change when registrants are added — and all thirty-nine of
their cells reproduced exactly. Sections II and III are ROLL-denominated and every cell was
off. Both blocks were recomputed against the roll as it then stood, and the divergence was
attributed to growth in the file.

THE 2026-08-01 RECOMPUTATION WAS ITSELF WRONG, AND WAS CORRECTED 2026-08-08 AFTER EXTERNAL
REVIEW. Read this before touching a denominator in this file.

A participation rate is voters divided by the people who COULD have voted: active registrants
enrolled on or before the contest. The recomputed figures were denominated on the whole
current active roll, so someone who registered in 2025 counted as a 2021-primary non-voter.
20.55% of the active roll registered after the 2021 primary. Restoring the cutoff moves the
eight major-party primary cells by +0.13 to +2.67 points, and §I's under-30 pair from
31.53/16.07 to 32.84/16.63.

Three checks make that a defect rather than a preference between bases, and all three are
derived here rather than asserted:

  1. The contemporaneous basis reproduces the figures the paper carried BEFORE 2026-08-01 —
     16.9 and 17.9 — exactly. Probed as "§III note — the pre-correction figures it reproduces".
  2. Roll growth explains none of the gap. The pinned and live rolls both return the
     uncorrected 14.26%, to the last digit, so the mechanism recorded in 2026-08-01's note
     ("the file has grown") cannot be what moved those cells.
  3. `diag_ny_primary_participation.py`, which the paper's Methods block names as §III's
     provenance, has applied the cutoff since its FIRST commit. So for one week the paper and
     its own cited script disagreed by up to 2.67 points — and both are published in the
     public reproduction repo, where a reader following the Methods block would have hit it.

The general lesson, which is the opposite of the one 2026-08-01 drew: when a paper and a
verifier disagree, the verifier is not automatically right. The convention this series already
has — "fix the paper or fix the derivation, never the tolerance" — is silent on which of the
two is wrong, and here it was the derivation.

The 2026-08-01 note also lacked probes on its OWN figures, which is why a wrong mechanism
stayed in print: "the roll grew" is a sentence, and the coverage gate cannot assert a sentence.
Every figure in the replacement note is derived, including the uncorrected values (`raw_*`),
which the earlier round had exempted as unreproducible. They were reproducible the whole time
— by dropping the cutoff.

WHAT WAS NOT CLAIMED, and still is not. Which roll snapshot the original tables were computed
on is not recoverable from the artifacts, and this script never asserted it. Nor does anything
here assert what any past session intended; the claims above are about file contents and
commit history, which are checkable. `data/ny_vrdb.duckdb` was last written 2026-07-30, the day
of the date-of-birth minimisation, but the minimisation cannot produce this:
`date_diff('year', ...)` returns the difference of year parts, so it read the birth YEAR before
and after — which is why the donor paper's twelve New York age-band figures came through it
identical to six decimal places. Ask the author rather than inferring it from file timestamps.

The donors-per-thousand column moved on 2026-08-01 for a second, unrelated reason: it was
still built on the pre-2026-07-27 New York match (308,032) rather than the full-name key now
used across the series (558,017). That change stands and no finding turned on it.

NEW YORK'S ROLL IS PINNED. It had no snapshot, on the assumption that a
static FOIL extract cannot move. It moved. `scripts/pin_ny_roll.py` freezes it the way
Washington's is — `ny_paper_roll`, 13,540,505 registrants of whom 12,448,034 are
active — and every roll-denominated derivation below reads that snapshot rather than `voters`.
Appendix A and Section I still read `voters` directly and correctly: they are
electorate-denominated and cannot drift. The snapshot was re-taken 2026-08-08 to add
`registration_date`, whose absence is what made the wrong denominator unavoidable; the re-pin
is value-identical on every column it already carried.

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

# Contemporaneous-eligibility cutoffs, added 2026-08-08. A participation RATE is
# voters / people who could have voted, so every denominator below is restricted to
# registrants enrolled on or before the contest. These dates are the same ones
# `diag_ny_primary_participation.py` has carried since its first commit; the two scripts
# now agree by construction, and before this they disagreed by up to 2.67 points on a
# figure the paper attributed to that script.
PRIMARY_DATE = {"ppres24": "2024-04-02", "pp24": "2024-06-25",
                "pp22": "2022-06-28", "pp21": "2021-06-22"}
G25_DATE = "2025-11-04"


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

    # The unaffiliated bloc's share OF THE ROLL, and its share of each general
    # electorate. The paper contrasts the two ("25.5% of the roll, but only
    # 16-22% of voters"); until strict_units was enabled here the band endpoints
    # were bare integers and auto-exempt, so nothing checked the contrast.
    # Roll share: the pin stores NORMALIZED party labels (the loader has already
    # mapped NYSBOE's 'BLK' to 'NOPARTY'), so read `mixF_NOPARTY`. FULL roll, not
    # active: the two are 25.49 and 25.32, and only the full roll rounds to the
    # printed 25.5. The abstract's neighbouring sentence says "of the ACTIVE roll"
    # and is probed against `mixA_NOPARTY` — the paper distinguishes them, so the
    # probes must too. Getting this backwards is what the first draft of this
    # block did.
    d["bloc_NOPARTY_roll"] = d["mixF_NOPARTY"]
    # Share of each GENERAL electorate that is blank-enrolled.
    for date, year, tg in GENERALS:
        d[f"unaff_{tg}"], = con.execute(f"""
            SELECT 100.0 * COUNT(*) FILTER (WHERE v.party = 'BLK') / COUNT(*)
            FROM voters v {_voted(year)}
            WHERE v.birthdate IS NOT NULL AND {_age(date)} BETWEEN 18 AND 105""").fetchone()
    _uv = [d[f"unaff_{tg}"] for _, _, tg in GENERALS]
    d["unaff_voter_lo"], d["unaff_voter_hi"] = min(_uv), max(_uv)

    # Section I — 2025 general under-30 turnout by party. This is the only roll-denominated
    # RATE in an otherwise electorate-denominated section, which is how it survived the
    # 2026-08-01 recompute untouched.
    #
    # DENOMINATOR CORRECTED 2026-08-08 to contemporaneously eligible registrants. It was
    # computed against the whole pinned active roll, which counts everyone who registered
    # AFTER 4 Nov 2025 — 1.89% of the active roll — as a 2025 non-voter. That basis was
    # enumerated when the pair was restated on 2026-08-06 (it is the "live active, registered
    # on/before 2025-11-04" line in the note at the foot of this file) and the whole-roll
    # basis was printed instead. It understates every party's rate: DEM 31.53 -> 32.84,
    # REP 16.07 -> 16.63. The FINDING is untouched — the ratio moves 1.96x to 1.97x, so
    # "nearly double" holds either way — but a rate whose denominator includes people who
    # could not have voted is not the rate the sentence claims to report.
    for p, r in con.execute(f"""
        WITH e AS (
            SELECT v.party p,
                   CASE WHEN v.state_voter_id IN (
                        SELECT DISTINCT state_voter_id FROM voter_participation
                        WHERE election_year=2025 AND kind='GENERAL') THEN 1 ELSE 0 END v25
            FROM {PIN} v
            WHERE v.is_active AND v.birth_year IS NOT NULL AND 2025 - v.birth_year < 30
              AND (v.registration_date IS NULL
                   OR v.registration_date <= DATE '{G25_DATE}'))
        SELECT p, 100.0*SUM(v25)/COUNT(*) FROM e GROUP BY 1""").fetchall():
        d[f"u30_g25_{p}"] = float(r)

    # Section III — closed-primary participation, as a share of each party's registrants.
    # New York's presidential primary is a distinct `kind`, so the paper's four rows are four
    # different contests rather than three; grouping by year alone would silently merge the
    # April presidential and June state primaries into one 2024 figure.
    #
    # DENOMINATOR CORRECTED 2026-08-08 — the same defect as §I's under-30 pair, and the one
    # that mattered most. Each rate is now denominated on active registrants enrolled on or
    # before that primary, which is the specification
    # `diag_ny_primary_participation.py` — the script this paper names as §III's provenance —
    # has used since its first commit, and which the verifier could not apply while the pin
    # carried no registration date. Sizes: +0.13 to +2.67 points, largest on the oldest
    # cycles, because 20.55% of today's active roll registered after the 2021 primary.
    for year, tag in ((2024, "ppres24"), (2024, "pp24"), (2022, "pp22"), (2021, "pp21")):
        kind = "PRES_PRIMARY" if tag == "ppres24" else "PRIMARY"
        rows = con.execute(f"""
            WITH reg AS (SELECT party p, state_voter_id FROM {PIN}
                         WHERE is_active
                           AND (registration_date IS NULL
                                OR registration_date <= DATE '{PRIMARY_DATE[tag]}')),
                 voted AS (SELECT DISTINCT state_voter_id FROM voter_participation
                           WHERE election_year={year} AND kind='{kind}')
            SELECT p, 100.0*COUNT(*) FILTER (
                     WHERE state_voter_id IN (SELECT state_voter_id FROM voted))/COUNT(*)
            FROM reg GROUP BY 1""").fetchall()
        for p, v in rows:
            d[f"{tag}_{p}"] = float(v)

    # §III's NOPARTY cells, re-read as a SWITCHING bound. Under NY Elec. Law § 5-304 a closed
    # primary is open only to enrollees, so a voter now enrolled blank who is recorded in one
    # demonstrably changed enrollment afterwards. This is derived because the paper used to
    # attribute those cells to "nonpartisan/special races" and that reading is refuted by the
    # 2024 PRESIDENTIAL primary, which carries no nonpartisan contest anywhere in the state
    # and still shows a non-zero blank cell. Reported as the share of each primary's surviving
    # voters who are blank today — the direction of drift the reviewer flagged, and the only
    # direction this file can observe. D<->R switching leaves no trace here and is NOT bounded.
    for year, tag in ((2024, "ppres24"), (2024, "pp24"), (2022, "pp22"), (2021, "pp21")):
        kind = "PRES_PRIMARY" if tag == "ppres24" else "PRIMARY"
        d[f"switch_{tag}"], = con.execute(f"""
            SELECT 100.0*COUNT(*) FILTER (WHERE party='NOPARTY')/COUNT(*)
            FROM {PIN} WHERE state_voter_id IN (
                SELECT DISTINCT state_voter_id FROM voter_participation
                WHERE election_year={year} AND kind='{kind}')""").fetchone()
    d["switch_lo"] = min(d[f"switch_{t}"] for t in ("ppres24", "pp24", "pp22", "pp21"))
    d["switch_hi"] = max(d[f"switch_{t}"] for t in ("ppres24", "pp24", "pp22", "pp21"))

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

    # §II's footnote answers "is the blank bloc's low donor rate an artifact of the full-name
    # match key?" — a fair question, because that key is known to discard donors who are
    # younger than those it retains, and NOPARTY is the youngest bucket. Derived on BOTH
    # panels rather than argued: if the ordering were an artifact it would narrow on the
    # retired all-tier panel, and it widens.
    for tbl, tag in (("voter_donor_affiliation", "primary"),
                     ("voter_donor_affiliation_alltier", "alltier")):
        rows = dict(con.execute(f"""
            SELECT v.party,
                   1000.0 * COUNT(DISTINCT CASE WHEN a.state_voter_id IS NOT NULL
                                                THEN v.state_voter_id END) / COUNT(*)
            FROM {PIN} v LEFT JOIN sw.{tbl} a ON a.state_voter_id = v.state_voter_id
            WHERE v.is_active GROUP BY 1""").fetchall())
        d[f"donor_ratio_{tag}"] = rows["NOPARTY"] / rows["DEM"]

    # Section IV — districts banded by registration lean, active roll. Reads `voters`, not the
    # pin: the pin deliberately carries no district column, and §IV's cells are integer district
    # COUNTS that a 36-registrant change cannot move.
    #
    # BANDS SYMMETRISED 2026-08-08. They were 40+ / 20-40 / 5-20 / ±5 on the Democratic side
    # against 5-20 / 20+ on the Republican, so a D+25 district read "Likely D" while an R+25
    # read "Safe R" — an avoidable methodology objection on a table whose actual finding
    # (21 of 176 districts inside ±5) is symmetric and unaffected. The seventh band is not
    # cosmetic: NO New York district is R+40 at either level, so on the paper's own D-side
    # threshold the state has ZERO safe-Republican seats, and the old table showed seven.
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
                   COUNT(*) FILTER (WHERE net<=-20 AND net>-40),
                   COUNT(*) FILTER (WHERE net<=-40), COUNT(*) FROM dd""").fetchone()
        for k, v in zip(("safe_d", "likely_d", "lean_d", "comp", "lean_r", "likely_r",
                         "safe_r", "n"), row):
            d[f"{tag}_{k}"] = v
    # "only 21 of 176" — derived from the band counts so a boundary change moves both.
    d["comp_total"] = d["cd_comp"] + d["ad_comp"]
    d["seat_total"] = d["cd_n"] + d["ad_n"]
    d["safe_d_total"] = d["cd_safe_d"] + d["ad_safe_d"]

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

    # §V — the re-registration share of each cohort, and whether it biases the trend
    # (2026-08-08). `registration_date` is the most recent registration TRANSACTION, not
    # necessarily an initial one, so a "cohort" is not a set of first-time registrants. The
    # test is exact rather than inferred: voting requires being registered, so a cohort member
    # with a participation record predating their own registration_date was registered earlier.
    #
    # A LOWER BOUND, and the bound's tightness depends on the detection window — 2024 can look
    # back to 2016, 2020 only to 2016 as well but across four years rather than eight. The
    # paper says so, because otherwise the two percentages read as a trend and they are not
    # comparable. 2008 and 2016 are not computed at all: this file's vote history starts in
    # 2016, so there is no prior window and a "0.00%" would be an artifact reported as a fact.
    for year in (2020, 2024):
        n, prior = con.execute(f"""
            SELECT COUNT(*), COUNT(*) FILTER (WHERE v.state_voter_id IN (
                       SELECT DISTINCT state_voter_id FROM voter_participation
                       WHERE election_year < {year}))
            FROM voters v WHERE year(v.registration_date) = {year}""").fetchone()
        d[f"rereg{year}_share"] = 100.0 * prior / n
    # Direction of the bias: if re-registrants were indistinguishable from first-time
    # registrants the split would be flat, and the caveat would be pedantic rather than
    # load-bearing. They are not, so the paper states which way it runs.
    for grp, op in (("new", "NOT IN"), ("rereg", "IN")):
        rows = dict(con.execute(f"""
            SELECT {PARTY} p, COUNT(*) FROM voters v
            WHERE year(v.registration_date) = 2024
              AND v.state_voter_id {op} (SELECT DISTINCT state_voter_id
                  FROM voter_participation WHERE election_year < 2024)
            GROUP BY 1""").fetchall())
        tot = sum(rows.values()) or 1
        for p in ("DEM", "NOPARTY"):
            d[f"c24_{grp}_{p}"] = 100.0 * rows.get(p, 0) / tot
        d[f"c24_{grp}_medage"], = con.execute(f"""
            SELECT median(date_diff('year', v.birthdate, v.registration_date))
            FROM voters v WHERE year(v.registration_date) = 2024
              AND v.state_voter_id {op} (SELECT DISTINCT state_voter_id
                  FROM voter_participation WHERE election_year < 2024)""").fetchone()

    # Boundary of inference — SURVIVORSHIP, MEASURED RATHER THAN ASSERTED (2026-08-08).
    # The paper claimed composition shares were "robust" and that the survivorship bias "hits
    # every group equally". Neither was established, and the second is testable. Voters who
    # were purged outright are invisible in a single extract, but INACTIVE status is the
    # visible pre-purge state, so the inactive rate among a past election's voters is a proxy
    # for who leaves the roll. It is a proxy and the paper now says so.
    #
    # By PARTY the spread is small (~0.3pp on a ~3.3% base for 2021 voters), which is roughly
    # what "hits every group equally" wanted to claim, so the paper now prints the number
    # instead of asserting the property. By AGE it is NOT small — the youngest band leaves at
    # about twice the rate of the 45-64 band — so the age shares carry a real bias, in the
    # direction of UNDERSTATING youth in past electorates. That runs against the paper's
    # headline rather than for it, which is why it is disclosed rather than bounded away.
    att = dict(con.execute("""
        SELECT CASE WHEN v.party='DEM' THEN 'DEM' WHEN v.party='REP' THEN 'REP'
                    WHEN v.party='BLK' THEN 'NOPARTY' ELSE 'OTHER' END p,
               100.0*COUNT(*) FILTER (WHERE v.status_code<>'A')/COUNT(*)
        FROM voters v WHERE v.state_voter_id IN (
            SELECT DISTINCT state_voter_id FROM voter_participation
            WHERE election_year=2021 AND kind='GENERAL')
        GROUP BY 1""").fetchall())
    d["att21_lo"], d["att21_hi"] = min(att.values()), max(att.values())
    d["att21_spread"] = d["att21_hi"] - d["att21_lo"]
    for band, lo, hi in (("young", 18, 29), ("mid", 45, 64)):
        d[f"att23_{band}"], = con.execute(f"""
            SELECT 100.0*COUNT(*) FILTER (WHERE v.status_code<>'A')/COUNT(*)
            FROM voters v WHERE v.birthdate IS NOT NULL
              AND 2023-EXTRACT(year FROM v.birthdate) BETWEEN {lo} AND {hi}
              AND v.state_voter_id IN (
                SELECT DISTINCT state_voter_id FROM voter_participation
                WHERE election_year=2023 AND kind='GENERAL')""").fetchone()
    d["att23_ratio"] = d["att23_young"] / d["att23_mid"]

    # The size of the denominator error the 2026-08-08 correction removes: the share of
    # today's active roll that registered after the oldest contest the paper rates.
    d["post21_share"], = con.execute(f"""
        SELECT 100.0*COUNT(*) FILTER (WHERE registration_date > DATE '{PRIMARY_DATE["pp21"]}')
               /COUNT(*) FROM {PIN} WHERE is_active""").fetchone()

    # The §III note quantifies the correction, so the correction is itself derived rather than
    # remembered — including the UNCORRECTED figures, which are otherwise unreproducible once
    # the verifier stops computing them. Same queries as above with the cutoff removed.
    deltas = []
    for year, tag in ((2024, "ppres24"), (2024, "pp24"), (2022, "pp22"), (2021, "pp21")):
        kind = "PRES_PRIMARY" if tag == "ppres24" else "PRIMARY"
        for p, v in con.execute(f"""
            WITH reg AS (SELECT party p, state_voter_id FROM {PIN} WHERE is_active),
                 voted AS (SELECT DISTINCT state_voter_id FROM voter_participation
                           WHERE election_year={year} AND kind='{kind}')
            SELECT p, 100.0*COUNT(*) FILTER (
                     WHERE state_voter_id IN (SELECT state_voter_id FROM voted))/COUNT(*)
            FROM reg GROUP BY 1""").fetchall():
            d[f"raw_{tag}_{p}"] = float(v)
            if p in ("DEM", "REP"):
                deltas.append(d[f"{tag}_{p}"] - float(v))
    # MAJOR-PARTY cells only, and the paper says so. Over all sixteen the span would read
    # "-0.00 to +2.67", because the NOPARTY and OTHER rates are ~0.1-2% figures whose
    # numerator and denominator shrink together and can round the other way. Quoting a range
    # that straddles zero would imply the correction is directionless; it is not, on every
    # cell the paper's argument uses.
    d["fix_lo"], d["fix_hi"] = min(deltas), max(deltas)

    # §I's under-30 ratio on both bases — the note claims the finding is untouched, and a
    # claim of "untouched" needs the before as well as the after.
    raw = dict(con.execute(f"""
        WITH e AS (
            SELECT v.party p, CASE WHEN v.state_voter_id IN (
                     SELECT DISTINCT state_voter_id FROM voter_participation
                     WHERE election_year=2025 AND kind='GENERAL') THEN 1 ELSE 0 END v25
            FROM {PIN} v
            WHERE v.is_active AND v.birth_year IS NOT NULL AND 2025 - v.birth_year < 30)
        SELECT p, 100.0*SUM(v25)/COUNT(*) FROM e GROUP BY 1""").fetchall())
    d["u30_ratio_raw"] = raw["DEM"] / raw["REP"]
    d["u30_ratio_fixed"] = d["u30_g25_DEM"] / d["u30_g25_REP"]

    # Appendix C — external validation against NYSBOE's published enrollment series.
    #
    # The published shares are EXTERNAL ground truth, so they cannot be derived from the voter
    # file and are imported from the diagnostic that documents their provenance rather than
    # transcribed a second time here. Two copies of a hand-typed constant is exactly the drift
    # this series keeps finding. What IS derived independently is the file side and every gap.
    from diag_ny_enrollment_validation import PUBLISHED, _published_shares  # noqa: E402
    hist = []
    for row in PUBLISHED:
        date, tag = row[0], "nysboe_" + row[0].replace("-", "")
        pub = _published_shares(row)
        obs = dict(con.execute(f"""
            SELECT CASE WHEN v.party='DEM' THEN 'DEM' WHEN v.party='REP' THEN 'REP'
                        WHEN v.party='BLK' THEN 'NOPARTY' ELSE 'OTHER' END p,
                   100.0*COUNT(*)/SUM(COUNT(*)) OVER ()
            FROM voters v
            WHERE v.status_code='A' AND v.registration_date <= DATE '{date}'
            GROUP BY 1""").fetchall())
        n_file, = con.execute(f"""
            SELECT COUNT(*) FROM voters v
            WHERE v.status_code='A' AND v.registration_date <= DATE '{date}'""").fetchone()
        for b in ("DEM", "REP", "NOPARTY", "OTHER"):
            d[f"{tag}_{b}"] = obs.get(b, 0.0) - pub[b]
            if date != "2026-02-20":
                hist.append(abs(d[f"{tag}_{b}"]))
        d[f"{tag}_retain"] = 100.0 * n_file / row[8]
    d["nysboe_worst"] = max(hist)

    # The FOIL extract's own identity, so a reproduction starts from the same bytes. Size is
    # checked live (instant); the SHA-256 is not, because hashing 928 MB on every verifier run
    # would cost more than the whole rest of this script — see its exemption for the one-line
    # command that reproduces it.
    src = vp.DATA / "raw" / "ny" / "ALLNYVOTERS20260629.zip"
    d["src_bytes"] = src.stat().st_size if src.exists() else -1

    # Appendix A — the two odd-year electorates are not one treatment. Sizes, not shares:
    # 2025 turned out far more voters than 2023, which is the paper's own evidence that
    # "odd year" does not name a single condition.
    for year in (2023, 2025):
        d[f"n_g{year % 100}"], = con.execute(f"""
            SELECT COUNT(DISTINCT state_voter_id) FROM voter_participation
            WHERE election_year={year} AND kind='GENERAL'""").fetchone()
    d["odd_ratio"] = d["n_g25"] / d["n_g23"]

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
    # Surfaced by strict_units 2026-08-10. Every endpoint below is a bare one- or
    # two-digit integer, so COVERAGE_EXEMPT's small-integer rule auto-exempted it
    # and both audited sections reported "fully mapped" without looking.
    ("§party — the GOP 65+ share across classes",
     r"GOP's 65\+ share jumps from (\d+)%\s*\(presidential\) to (\d+)% \(odd-year\)",
     ("g24_REP_65", "g25_REP_65"), 0.5),
    ("§party — the unaffiliated drop-off band",
     r"\(([\d.]+)% of the roll, but only (\d+)–(\d+)% of\s*voters\)",
     ("bloc_NOPARTY_roll", "unaff_voter_lo", "unaff_voter_hi"), 0.5),
    ("appendix A — the composition gradient in prose",
     r"under-30 share\s*collapses \((\d+)% → (\d+)% by 2023\) and the 65\+ share swells "
     r"\((\d+)% → (\d+)%\)",
     ("g24_18-29", "g23_18-29", "g24_65+", "g23_65+"), 0.5),

    # --- Abstract, gated 2026-08-07 when it moved in from the metadata file. Every figure here
    # is a restatement of one asserted elsewhere in the paper, which is exactly why each gets
    # its own probe rather than riding on the section probe: the two can drift apart, and the
    # abstract is where a drift is most expensive.
    ("abstract — roll size, exact",
     r"vote history for \*\*([\d,]+)\*\* registrants", "roll_all", 0),
    ("abstract — 65+ share, 2024 presidential against the 2023 odd-year",
     r"65-and-over share rises from \*\*([\d.]+)%\*\* of the 2024 presidential electorate to "
     r"\*\*([\d.]+)%\*\* in the 2023 odd-year general",
     ("g24_65+", "g23_65+"), 0.05),
    ("abstract — under-30 share, same two electorates",
     r"under-30 share collapses from \*\*([\d.]+)%\*\* to \*\*([\d.]+)%\*\*",
     ("g24_18-29", "g23_18-29"), 0.05),
    # ACTIVE-roll key, not mixF_NOPARTY. The two differ — 25.3 against 25.49 — and the abstract
    # says "of the active roll", so the full-roll key would have failed on a real distinction.
    ("abstract — NOPARTY share of the active roll",
     r"A quarter of registrants, \*\*([\d.]+)%\*\* of the active roll", "mixA_NOPARTY", 0.05),
    ("abstract — the competitive count over both chambers",
     r"only \*\*(\d+)\*\* of \*\*(\d+)\*\* congressional and Assembly districts are\s+"
     r"within five points", ("comp_total", "seat_total"), 0),
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
    ("§IV congressional districts by lean (symmetric bands)",
     r"\| Congressional \(26\) \| (\d+) \| (\d+) \| (\d+) \| \*\*(\d+)\*\* \| (\d+) \| (\d+) \| "
     r"(\d+) \|",
     ("cd_safe_d", "cd_likely_d", "cd_lean_d", "cd_comp", "cd_lean_r", "cd_likely_r",
      "cd_safe_r"), 0),
    ("§IV assembly districts by lean (symmetric bands)",
     r"\| Assembly \(150\) \| (\d+) \| (\d+) \| (\d+) \| \*\*(\d+)\*\* \| (\d+) \| (\d+) \| "
     r"(\d+) \|",
     ("ad_safe_d", "ad_likely_d", "ad_lean_d", "ad_comp", "ad_lean_r", "ad_likely_r",
      "ad_safe_r"), 0),
    ("§IV — the competitive count over both chambers",
     r"Only \*\*(\d+) of (\d+)\*\* congressional and Assembly districts",
     ("comp_total", "seat_total"), 0),
    ("§IV — the two chamber-level competitive counts, and both chamber sizes",
     r"— (\d+) of (\d+) and (\d+) of (\d+) — are within\s+five points",
     ("cd_comp", "cd_n", "ad_comp", "ad_n"), 0),
    ("§IV — safe-D seats on the symmetric 40+ threshold, both chambers",
     r"makes (\d+) seats\s+safe for Democrats", "safe_d_total", 0),

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
    ("§IV — Assembly size in the lean-Democratic sentence",
     r"105/(\d+) lean Democratic", "ad_n", 0),
    ("§III — the decisive-contest restatement, 2021 then 2024",
     r"2021 odd-year DEM ([\d.]+)% vs REP ([\d.]+)%; 2024 state DEM ([\d.]+)% vs REP ([\d.]+)%",
     ("pp21_DEM", "pp21_REP", "pp24_DEM", "pp24_REP"), 0.05),
    # The 2026-08-08 note quantifies its own correction. These probes exist because the note
    # they replace carried its figures UNPROBED, which is how it kept a wrong mechanism in
    # print: "the roll grew" was a sentence no assertion could reach.
    ("§III note — the size of the denominator correction, both endpoints",
     r"moves the rates \*\*\+([\d.]+) to \+([\d.]+) points\*\*", ("fix_lo", "fix_hi"), 0.005),
    ("§III note — the pre-correction figures it reproduces",
     r"carried \*before\* 2026-08-01 — ([\d.]+) and ([\d.]+) — exactly",
     ("pp21_DEM", "pp22_DEM"), 0.05),
    ("§III note — the uncorrected 2021 rate the two rolls agree on",
     r"return the uncorrected ([\d.]+)% alike", "raw_pp21_DEM", 0.005),
    ("§III note — the disagreement against the paper's own cited script",
     r"disagreed by up to ([\d.]+) points", "fix_hi", 0.005),
    ("§III note — the under-30 ratio, before and after the correction",
     r"under-30 ratio moves from ([\d.]+)× to ([\d.]+)×",
     ("u30_ratio_raw", "u30_ratio_fixed"), 0.005),
    ("§IV — districts leaning Democratic, congressional then assembly",
     r"([\d]+)/26 and ([\d]+)/150 lean Democratic",
     ("cd_lean_dem_total", "ad_lean_dem_total"), 0),
    ("§I — NOPARTY roll share against its share of voters",
     r"\(([\d.]+)% of the roll, but only 16–22% of voters\)", "mixF_NOPARTY", 0.05),
    ("Methods — the pin against the file's ROW count",
     r"holds ([\d,]+) registrants against the file's ([\d,]+) rows",
     ("roll_all", "file_rows"), 0),
    ("Methods — the pin's registrant and active counts",
     r"`ny_paper_roll`, ([\d,]+) registrants, of whom ([\d,]+) are\s+active",
     ("roll_all", "roll_active"), 0),
    ("Methods — the source extract's byte count, checked against the file on disk",
     r"\.zip`, ([\d,]+) bytes", "src_bytes", 0),
    ("§III — the NOPARTY residual span, where the paper reinterprets it",
     r"read the ([\d.]+)–([\d.]+)% residual as", ("np_primary_lo", "np_primary_hi"), 0.05),
    ("Boundary — the switching bound restated in the limitations list",
     r"for the bound: ([\d.]+)–([\d.]+)% of each closed primary's voters",
     ("switch_lo", "switch_hi"), 0.05),
    ("Boundary — parser validation against known 2024 turnout",
     r"2024 presidential ≈ ([\d.]+)M", "turn24_m", 0.05),
    ("abstract — roll scale restated",
     r"individual-record measurement on ([\d.]+)M New York", "roll_m", 0.05),

    # ---- added 2026-08-08, the external-review round. Every claim introduced by that round
    # is probed, on the rule that a caveat carrying a number is a result: the 2026-08-01
    # round's own recompute note carried unprobed figures and that is how it kept a wrong
    # mechanism in print for a week.
    ("front matter — the switching bound, both endpoints",
     r"\*\*([\d.]+)–([\d.]+)% of them are enrolled blank today\*\*",
     ("switch_lo", "switch_hi"), 0.05),
    ("§III — the switching bound restated on its own cells",
     r"\*\*([\d.]+)% \(2024\) to ([\d.]+)% \(2021\) are enrolled blank today\*\*",
     ("switch_pp24", "switch_pp21"), 0.05),
    ("front matter — attrition spread across parties",
     r"near-flat across parties \(([\d.]+)pp spread\)", "att21_spread", 0.005),
    ("Boundary — the party attrition span, 2021 general voters",
     r"the inactive rate spans ([\d.]+)–([\d.]+)% across the four party buckets",
     ("att21_lo", "att21_hi"), 0.005),
    ("Boundary — the same spread restated as a gap",
     r"a ([\d.]+)pp spread, which is what an earlier version", "att21_spread", 0.005),
    ("Boundary — age attrition, under-30 against 45-64",
     r"([\d.]+)% of the under-30 band is now inactive against ([\d.]+)% of the 45–64 band",
     ("att23_young", "att23_mid"), 0.005),
    ("§III note — the share of today's roll registered after the 2021 primary",
     r"\*\*([\d.]+)%\*\* of today's active roll registered after the 2021", "post21_share", 0.005),
    ("Appendix A — the two odd-year electorate sizes and their ratio",
     r"turned out ([\d,]+) voters at [\d.]+% aged 65\+, while 2025\s+turned out ([\d,]+) — "
     r"\*\*([\d.]+)×\*\*",
     ("n_g23", "n_g25", "odd_ratio"), 0.005),
    ("Appendix A — the 65+ shares named beside those two sizes",
     r"at ([\d.]+)% aged 65\+, while 2025\s+turned out [\d,]+ — \*\*[\d.]+×\*\* as many — at "
     r"([\d.]+)%", ("g23_65+", "g25_65+"), 0.05),
    ("§II footnote — the donor ratio on both match panels",
     r"NOPARTY-to-DEM ratio is ([\d.]+) against ([\d.]+) here",
     ("donor_ratio_alltier", "donor_ratio_primary"), 0.005),
    ("§II footnote — the retired panel size it names",
     r"on the retired ([\d,]+)-voter panel", "_prev_panel", 0),

    # ---- Appendix C, the NYSBOE external validation. Every cell of the table is probed:
    # it is the answer to the survivorship objection, so an unchecked cell here would be an
    # unchecked limitation, which is the category this paper has already been burned by.
    # NB the gap cells are written with an ASCII hyphen-minus, not U+2212. The prose elsewhere
    # in this paper uses the typographic minus, but a captured value has to parse as a number
    # and U+2212 does not — the first version of these probes captured '-0.17' as a string and
    # failed with "not a number", which is the right failure and worth not re-causing.
    ("App. C — 2026-02-20 control row",
     r"\| 2026-02-20 \| \*\*control\*\* \| (-[\d.]+) \| \+([\d.]+) \| (-[\d.]+) \| "
     r"\+([\d.]+) \| \*\*([\d.]+)%\*\* \|",
     ("nysboe_20260220_DEM", "nysboe_20260220_REP", "nysboe_20260220_NOPARTY",
      "nysboe_20260220_OTHER", "nysboe_20260220_retain"), 0.005),
    ("App. C — 2025-11-01 row",
     r"\| 2025-11-01 \| the 2025 general \| (-[\d.]+) \| \+([\d.]+) \| (-[\d.]+) \| "
     r"\+([\d.]+) \| ([\d.]+)% \|",
     ("nysboe_20251101_DEM", "nysboe_20251101_REP", "nysboe_20251101_NOPARTY",
      "nysboe_20251101_OTHER", "nysboe_20251101_retain"), 0.005),
    ("App. C — 2024-02-27 row",
     r"\| 2024-02-27 \| both 2024 primaries \| (-[\d.]+) \| \+([\d.]+) \| (-[\d.]+) \| "
     r"(-[\d.]+) \| ([\d.]+)% \|",
     ("nysboe_20240227_DEM", "nysboe_20240227_REP", "nysboe_20240227_NOPARTY",
      "nysboe_20240227_OTHER", "nysboe_20240227_retain"), 0.005),
    ("App. C — 2022-02-21 row",
     r"\| 2022-02-21 \| the 2022 primary \| (-[\d.]+) \| \+([\d.]+) \| \+([\d.]+) \| "
     r"(-[\d.]+) \| ([\d.]+)% \|",
     ("nysboe_20220221_DEM", "nysboe_20220221_REP", "nysboe_20220221_NOPARTY",
      "nysboe_20220221_OTHER", "nysboe_20220221_retain"), 0.005),
    ("App. C — 2021-02-21 row",
     r"\| 2021-02-21 \| the 2021 primary \| (-[\d.]+) \| \*\*\+([\d.]+)\*\* \| \+([\d.]+) \| "
     r"(-[\d.]+) \| \*\*([\d.]+)%\*\* \|",
     ("nysboe_20210221_DEM", "nysboe_20210221_REP", "nysboe_20210221_NOPARTY",
      "nysboe_20210221_OTHER", "nysboe_20210221_retain"), 0.005),
    # Bounded digit groups, not [\d.]+ — the sentence ends right after the value and a greedy
    # character class captures the full stop, giving "0.33." and a "not a number" failure.
    ("App. C — the control row's gap span, quoted in prose",
     r"its gaps are (-\d+\.\d+) to \+(\d+\.\d+)",
     ("nysboe_20260220_NOPARTY", "nysboe_20260220_OTHER"), 0.005),
    ("App. C — the largest historical gap, twice",
     r"largest historical gap is \*\*([\d.]+) points\*\*", "nysboe_worst", 0.005),
    ("App. C — the same bound restated against the median-age effect",
     r"a ([\d.]+)-point share gap against an", "nysboe_worst", 0.005),
    ("App. C — Feb 2021 retention, restated in prose",
     r"Only \*\*([\d.]+)%\*\* of the registrants NYSBOE", "nysboe_20210221_retain", 0.005),
    ("App. C — the same bound in the attrition sentence",
     r"moved by at most ([\d.]+) points", "nysboe_worst", 0.005),
    # The front matter is NOT inside AUDIT_BOUNDS, so the coverage gate cannot reach these two
    # restatements and they would be unchecked by default — which is the precise shape of the
    # defect this round corrected in the §III note. Probed explicitly instead.
    ("front matter — Appendix C's ceiling, restated in caveat (2)",
     r"external\s+ceiling of \*\*([\d.]+) points\*\*", "nysboe_worst", 0.005),

    # ---- §V's re-registration caveat, 2026-08-08.
    ("§V — re-registration lower bound, both measurable cohorts",
     r"at least \*\*([\d.]+)%\*\* of the 2020 cohort and\s+\*\*([\d.]+)%\*\* of the 2024 cohort",
     ("rereg2020_share", "rereg2024_share"), 0.005),
    ("§V — the 2024 split that gives the bias its direction",
     r"\*\*([\d.]+)%\*\* Democratic and \*\*([\d.]+)%\*\* no-party against \*\*([\d.]+)%\*\* "
     r"and\s+\*\*([\d.]+)%\*\*",
     ("c24_rereg_DEM", "c24_rereg_NOPARTY", "c24_new_DEM", "c24_new_NOPARTY"), 0.05),
    ("§V — median registration age of each group",
     r"median registration age of (\d+) against (\d+)",
     ("c24_rereg_medage", "c24_new_medage"), 0),
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
    # Gated 2026-08-07, when the abstract moved into the paper from the metadata file. It
    # restates results from four different sections, so it is gated on arrival rather than
    # later: an abstract drifting from the tables it summarises is the same defect as a prose
    # restatement, in the one place a referee always reads.
    "abstract":   ("## Abstract", "## The question"),
    "party":      ("## I. The graying is not partisan-neutral",
                   "## II. The unaffiliated quarter"),
    "blank_bloc": ("## II. The unaffiliated quarter", "## III. The nominating electorate"),
    "nominating": ("## III. The nominating electorate", "## IV. The registration map"),
    "safe_seat":  ("## IV. The registration map", "## V. A leading indicator"),
    "registrants": ("## V. A leading indicator", "## Boundary of inference"),
    "boundary":   ("## Boundary of inference", "## What it means"),
    # The replication, now an appendix. Audited exactly as it was when it led the paper —
    # moving a section must not be a way to stop checking it.
    "appendix_a": ("## Appendix A — Validation", "## Appendix C — External validation"),
    # Appendix C is placed BEFORE Appendix B in the document — substance ahead of the
    # numbering map — so that both appendices have a following anchor to slice against.
    # A slice whose end anchor does not exist runs to end-of-document and silently swallows
    # whatever follows, which is one of the three coverage rules this gate already encodes.
    "appendix_c": ("## Appendix C — External validation", "## Appendix B — Section numbering"),
}

COVERAGE_EXEMPT = [
    (r"^(?:19|20)\d{2}$", "a calendar year, not a result"),
    (r"^\d{1,2}$", "small integer — chamber sizes, band edges, list ordinals"),
    # Added 2026-08-08 with the source-identity block. A SHA-256 tokenises into runs of
    # digits, so the gate sees '256', '027', '4807' and so on as unmapped figures. They are
    # fragments of one opaque identifier, not results, and the identifier IS checkable — the
    # byte count beside it is asserted against the file on disk by the probe "Methods — the
    # source extract's byte count", and the digest itself reproduces with:
    #     sha256sum data/raw/ny/ALLNYVOTERS20260629.zip
    # Deliberately narrow: 3-4 digit runs only, and only because the hex string is confined
    # to one sentence. It cannot swallow a rate, a share or a district count, which are all
    # either decimal or comma-grouped.
    (r"^[0-9a-f]{3,4}$", "fragment of the source extract's SHA-256 or its filename date "
                         "stamp; the digest reproduces with sha256sum and the byte count "
                         "beside it is asserted live"),
]

COVERAGE_EXEMPT_LITERAL: dict[str, str] = {
    # PRUNED 2026-08-08. The six literals that used to sit here covered the 2026-08-01
    # recompute note's deltas and the retired sides of its two arrows. That note has been
    # replaced: its figures are now derived — including the UNCORRECTED ones, by
    # `raw_*` — so nothing in it needs exempting. The rule that produced them was sound
    # ("a delta against a roll state that no longer exists cannot be re-derived"); what it
    # missed is that the state could be reconstructed by simply dropping the cutoff, which is
    # what `raw_*` does. An exemption is a last resort, and this one had a derivation
    # available the whole time.
    "741": "the chapter number of a New York session law (Chapter 741 of the Laws of 2023), "
           "not a measurement. The statute's content and litigation history are cited in "
           "'What it means'; nothing numeric is claimed of it",
    "20260629": "the date stamp inside the FOIL extract's filename (ALLNYVOTERS20260629.zip), "
                "which is an identifier rather than a result. The file it names is checked "
                "live by the probe 'Methods — the source extract's byte count'",
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
                              COVERAGE_EXEMPT_SECTIONS, strict_units=True)
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
