"""Independent re-derivation of docs/who-decides-washington.md, asserted against its prose.

CONVERTED TO AN ASSERTING VERIFIER 2026-08-01. The previous version derived roughly a hundred
values with from-scratch SQL and then PRINTED them, almost all with no paper value beside
them at all — two of about a hundred cells carried a "(paper: ...)" annotation. It returned
None, so it always exited 0, and the release checklist's `verify_who_decides_wa.py || echo
FAILED` could never fire. In practice it asked a human to open the paper and compare a
hundred cells by eye, every time, which is not a gate.

The derivations were sound — every cell spot-checked against the paper reproduced — so what
changed is that the comparison is now performed by the machine and its failure is fatal.

This paper is POSTED (SSRN abstract 7149263, 2026-07-26) and unmodified since. A failure here
is therefore a correction to a public preprint rather than a pre-submission fix, which raises
the bar for changing the paper and lowers it for suspecting the probe. Reproduce a mismatch
by hand before editing anything.

Hits data/wa_vrdb.duckdb DIRECTLY with from-scratch SQL, not by importing the diag scripts.
Read-only; AGGREGATE OUTPUT ONLY — the VRDB carries personal data under RCW 29A.08.720 and
this script must never emit a row.

TWO THINGS THE DERIVATIONS DEPEND ON, both easy to get wrong:
  * WA birthdates are stored as 1 July of the birth year, so `date_diff('year', ...)` gives
    year-difference age. That is the paper's stated convention; it is not true age, and it
    is one year high for anyone born after the election date in their birth year.
  * The eligibility denominator is the CURRENT roll, registered on or before the election
    and aged 18+ at it. Voters who have since left the roll are absent from it — which is
    the survivorship hole the paper measures in its own §Coverage and bounds explicitly,
    rather than a defect in this script.

Run:  python scripts/verify_who_decides_wa.py [--coverage]
"""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _verify_prose as vp  # noqa: E402

vp.stdout_utf8()

VRDB = str(vp.DATA / "wa_vrdb.duckdb")
PAPER = vp.DOCS / "who-decides-washington.md"

BANDS = ["18-29", "30-44", "45-64", "65+"]
ELECTIONS = [("2024-11-05", "e24"), ("2022-11-08", "e22"), ("2021-11-02", "e21"),
             ("2023-11-07", "e23"), ("2025-11-04", "e25")]
OFF_YEARS = ["e21", "e23", "e25"]

# Certified statewide ballots counted, WA Secretary of State
# (results.vote.wa.gov/results/<yyyymmdd>/turnout.html). An EXTERNAL benchmark: the point of
# the coverage table is to compare the voter file against a number the file cannot produce.
OFFICIAL = {"2021-11-02": 1_896_481, "2022-11-08": 3_067_686, "2023-11-07": 1_758_084,
            "2024-11-05": 3_961_569, "2025-11-04": 2_001_425}

# Metro counties, as the paper's geography cut defines them: the ten most populous.
METRO = ("KING", "PIERCE", "SNOHOMISH", "SPOKANE", "CLARK", "THURSTON", "KITSAP",
         "YAKIMA", "WHATCOM", "BENTON")


def _age(date: str) -> str:
    return f"date_diff('year', v.birthdate, DATE '{date}')"


def _band(date: str) -> str:
    a = _age(date)
    return (f"CASE WHEN {a}<30 THEN '18-29' WHEN {a}<45 THEN '30-44' "
            f"WHEN {a}<65 THEN '45-64' ELSE '65+' END")


def _eligible(date: str) -> str:
    """Current-roll registrants who could have voted on `date`."""
    return (f"FROM voters v WHERE v.birthdate IS NOT NULL AND {_age(date)} >= 18 "
            f"AND v.registration_date IS NOT NULL AND v.registration_date <= DATE '{date}'")


def _voted(date: str) -> str:
    return (f"LEFT JOIN (SELECT DISTINCT state_voter_id FROM voting_history "
            f"WHERE election_date = DATE '{date}') h ON h.state_voter_id = v.state_voter_id")


def derive() -> dict:
    d: dict = {}
    con = duckdb.connect(VRDB, read_only=True)

    for date, tag in ELECTIONS:
        # Rate and composition in one pass: eligible registrants and whether they voted.
        rows = con.execute(f"""
            WITH e AS (SELECT {_band(date)} b,
                              CASE WHEN h.state_voter_id IS NOT NULL THEN 1 ELSE 0 END v
                       FROM voters v {_voted(date)}
                       WHERE v.birthdate IS NOT NULL AND {_age(date)} >= 18
                         AND v.registration_date IS NOT NULL
                         AND v.registration_date <= DATE '{date}')
            SELECT b, COUNT(*), SUM(v) FROM e GROUP BY 1""").fetchall()
        roll = {b: 0 for b in BANDS}
        voted = {b: 0 for b in BANDS}
        for b, n, v in rows:
            roll[b], voted[b] = int(n), int(v or 0)
        tot_v = sum(voted.values()) or 1
        for b in BANDS:
            d[f"{tag}_rate_{b}"] = 100.0 * voted[b] / (roll[b] or 1)
            d[f"{tag}_comp_{b}"] = 100.0 * voted[b] / tot_v
        d[f"{tag}_rate_all"] = 100.0 * tot_v / (sum(roll.values()) or 1)
        d[f"{tag}_analyzable"] = tot_v

        # Coverage against the certified count.
        d[f"{tag}_official"] = OFFICIAL[date]
        d[f"{tag}_infile"], = con.execute(f"""
            SELECT COUNT(DISTINCT state_voter_id) FROM voting_history
            WHERE election_date = DATE '{date}'""").fetchone()
        # "Analyzable (roll + YOB)" means exactly what it says: on the current roll, with a
        # year of birth. NO age filter — adding `>= 18` here was wrong and put this column
        # one record low in 2022 and 2024, because a handful of ballot-returners compute as
        # under 18 under the year-difference convention. The rounding check caught it; the
        # tolerance had not, because one record in 3.9 million is inside any sane tolerance
        # and the figure was still not the one the paper prints.
        d[f"{tag}_analyzable"], = con.execute(f"""
            SELECT COUNT(*) FROM voters v {_voted(date)}
            WHERE h.state_voter_id IS NOT NULL AND v.birthdate IS NOT NULL""").fetchone()
        tot_v = d[f"{tag}_analyzable"]
        d[f"{tag}_infile_pct"] = 100.0 * d[f"{tag}_infile"] / OFFICIAL[date]
        d[f"{tag}_cov_pct"] = 100.0 * tot_v / OFFICIAL[date]
        d[f"{tag}_residual"] = OFFICIAL[date] - tot_v
        d[f"{tag}_residual_pct"] = 100.0 * d[f"{tag}_residual"] / OFFICIAL[date]

        # Bounding: what the 65+ share would be if every missing ballot were cast by an
        # under-65, and if every one were cast by a 65+.
        #
        # THE NUMERATOR MUST SIT ON THE SAME BASIS AS `analyzable`, which is the roll-and-YOB
        # set WITHOUT the registration-date filter. Taking the 65+ count from the
        # rate-eligible (registration-filtered) set instead mixes the two and moved the 2021
        # upper bound 42.6 -> 42.54. It also explains a pair in the paper that looks like an
        # inconsistency and is not: the 2021 65+ share is 36.7497 on the rate basis and
        # 36.7508 on the coverage basis, so the composition table rounds it to 36.7 and the
        # bounding table to 36.8. Both are right; they are different denominators.
        n65, = con.execute(f"""
            SELECT COUNT(*) FROM voters v {_voted(date)}
            WHERE h.state_voter_id IS NOT NULL AND v.birthdate IS NOT NULL
              AND {_age(date)} >= 65""").fetchone()
        res = d[f"{tag}_residual"]
        d[f"{tag}_obs65"] = 100.0 * n65 / tot_v
        d[f"{tag}_min65"] = 100.0 * n65 / (tot_v + res)
        d[f"{tag}_max65"] = 100.0 * (n65 + res) / (tot_v + res)

        # Finer cohorts, for the sensitivity table.
        a = _age(date)
        fine = con.execute(f"""
            WITH e AS (SELECT CASE WHEN {a}<25 THEN '18-24' WHEN {a}<30 THEN '25-29'
                                   WHEN {a}<45 THEN '30-44' WHEN {a}<65 THEN '45-64'
                                   WHEN {a}<75 THEN '65-74' ELSE '75+' END b
                       FROM voters v {_voted(date)}
                       WHERE h.state_voter_id IS NOT NULL AND v.birthdate IS NOT NULL
                         AND {a} >= 18 AND v.registration_date <= DATE '{date}')
            SELECT b, COUNT(*) FROM e GROUP BY 1""").fetchall()
        fd = dict(fine)
        ft = sum(fd.values()) or 1
        for b in ("18-24", "25-29", "30-44", "45-64", "65-74", "75+"):
            d[f"{tag}_fine_{b}"] = 100.0 * fd.get(b, 0) / ft

        # Geography: 65+ share of the electorate, four ways.
        geo = con.execute(f"""
            WITH e AS (SELECT UPPER(v.county_name) c, {a} ag
                       FROM voters v {_voted(date)}
                       WHERE h.state_voter_id IS NOT NULL AND v.birthdate IS NOT NULL
                         AND {a} >= 18 AND v.registration_date <= DATE '{date}')
            SELECT CASE WHEN c='KING' THEN 'king' ELSE 'rest' END,
                   CASE WHEN c IN {METRO} THEN 'metro' ELSE 'rural' END,
                   COUNT(*), COUNT(*) FILTER (WHERE ag>=65) FROM e GROUP BY 1, 2""").fetchall()
        agg: dict[str, list[int]] = {}
        for k1, k2, n, n65g in geo:
            for k in (k1, k2):
                agg.setdefault(k, [0, 0])
                agg[k][0] += int(n)
                agg[k][1] += int(n65g)
        for k in ("king", "rest", "metro", "rural"):
            n, n65g = agg.get(k, [1, 0])
            d[f"{tag}_geo_{k}"] = 100.0 * n65g / (n or 1)

        # Median age of the electorate.
        d[f"{tag}_median"], = con.execute(f"""
            SELECT median({a}) FROM voters v {_voted(date)}
            WHERE h.state_voter_id IS NOT NULL AND v.birthdate IS NOT NULL AND {a} >= 18
              AND v.registration_date <= DATE '{date}'""").fetchone()

    # Scale of the two source tables, and the retained snapshot. Stated in the abstract and
    # the methods note and probed nowhere until 2026-08-02.
    d["roll_m"], = con.execute(
        "SELECT COUNT(*) / 1e6 FROM voters").fetchone()
    d["history_m"], = con.execute(
        "SELECT COUNT(*) / 1e6 FROM voting_history").fetchone()
    d["snapshot_m"], = con.execute(
        "SELECT COUNT(*) / 1e6 FROM voters_20230901").fetchone()

    # Roll attrition 2023 -> 2026. The paper reads this as evidence that leaving the roll is
    # age-loaded, which is the mechanism behind the survivorship bound, so it is a result
    # rather than a description.
    left, left_k, left_pct, left_65, stay_65 = con.execute("""
        WITH s AS (SELECT state_voter_id, birthdate FROM voters_20230901
                   WHERE birthdate IS NOT NULL),
             j AS (SELECT s.birthdate, (v.state_voter_id IS NULL) AS gone
                   FROM s LEFT JOIN voters v USING (state_voter_id))
        SELECT COUNT(*) FILTER (WHERE gone),
               COUNT(*) FILTER (WHERE gone) / 1e3,
               100.0 * COUNT(*) FILTER (WHERE gone) / COUNT(*),
               100.0 * COUNT(*) FILTER (WHERE gone AND date_diff('year', birthdate,
                                                                 DATE '2023-09-01') >= 65)
                     / NULLIF(COUNT(*) FILTER (WHERE gone), 0),
               100.0 * COUNT(*) FILTER (WHERE NOT gone AND date_diff('year', birthdate,
                                                                     DATE '2023-09-01') >= 65)
                     / NULLIF(COUNT(*) FILTER (WHERE NOT gone), 0)
        FROM j""").fetchone()
    d["left_n"], d["left_k"], d["left_pct"] = int(left), float(left_k), float(left_pct)
    d["left_65"], d["stay_65"] = float(left_65), float(stay_65)

    # Coverage range across the five cycles, which the prose states as a span.
    d["cov_lo"] = min(d[f"{t}_cov_pct"] for t in ("e21", "e22", "e23", "e24", "e25"))
    d["cov_hi"] = max(d[f"{t}_cov_pct"] for t in ("e21", "e22", "e23", "e24", "e25"))

    # Habitual core: the share of each off-year's returners who also voted in 2024. The
    # abstract states it as a span, so the span needs derived endpoints.
    for date, tag in (("2021-11-02", "e21"), ("2023-11-07", "e23"), ("2025-11-04", "e25")):
        d[f"{tag}_core"], = con.execute(f"""
            WITH off AS (SELECT DISTINCT state_voter_id FROM voting_history
                         WHERE election_date = DATE '{date}'),
                 pres AS (SELECT DISTINCT state_voter_id FROM voting_history
                          WHERE election_date = DATE '2024-11-05')
            SELECT 100.0 * COUNT(*) FILTER (
                     WHERE state_voter_id IN (SELECT state_voter_id FROM pres))
                   / COUNT(*) FROM off""").fetchone()
    d["core_lo"] = min(d[f"{t}_core"] for t in ("e21", "e23", "e25"))
    d["core_hi"] = max(d[f"{t}_core"] for t in ("e21", "e23", "e25"))

    # Off-year averages, for the "who is counted" table.
    for b in BANDS:
        d[f"off_comp_{b}"] = sum(d[f"{t}_comp_{b}"] for t in OFF_YEARS) / 3.0
    # Official turnout rate for the 2021 example the methods note quotes: certified ballots
    # over registered voters as the Secretary of State reports it, not a file-derived rate.
    d["e21_official_turnout"] = 39.38
    d["off_median"] = sum(d[f"{t}_median"] for t in OFF_YEARS) / 3.0

    # The registered roll itself, as of the current extract.
    a26 = _age("2026-04-01")
    rows = con.execute(f"""
        WITH e AS (SELECT {_band('2026-04-01')} b FROM voters v
                   WHERE v.birthdate IS NOT NULL AND {a26} >= 18)
        SELECT b, COUNT(*) FROM e GROUP BY 1""").fetchall()
    rd = dict(rows)
    rt = sum(rd.values()) or 1
    for b in BANDS:
        d[f"roll_{b}"] = 100.0 * rd.get(b, 0) / rt
    d["roll_median"], = con.execute(
        f"SELECT median({a26}) FROM voters v WHERE v.birthdate IS NOT NULL AND {a26} >= 18"
    ).fetchone()

    # Survivorship: voters who cast a ballot and are no longer on the roll, aged via the
    # retained September-2023 snapshot (the only way to age someone the current roll lost).
    for date, tag in (("2021-11-02", "e21"), ("2022-11-08", "e22"), ("2023-11-07", "e23")):
        n, p65, p18 = con.execute(f"""
            WITH gone AS (
                SELECT s.state_voter_id, date_diff('year', s.birthdate, DATE '{date}') a
                FROM voters_20230901 s
                JOIN (SELECT DISTINCT state_voter_id FROM voting_history
                      WHERE election_date = DATE '{date}') h USING (state_voter_id)
                LEFT JOIN voters v USING (state_voter_id)
                WHERE v.state_voter_id IS NULL AND s.birthdate IS NOT NULL)
            SELECT COUNT(*), 100.0*COUNT(*) FILTER (WHERE a>=65)/COUNT(*),
                   100.0*COUNT(*) FILTER (WHERE a<30)/COUNT(*) FROM gone""").fetchone()
        d[f"{tag}_gone_n"], d[f"{tag}_gone_65"], d[f"{tag}_gone_18"] = \
            int(n), float(p65), float(p18)
        d[f"{tag}_gone_k"] = int(n) / 1000.0

    # Snapshot cross-validation: the same 65+ share computed on the Sept-2023 roll.
    for date, tag in (("2021-11-02", "e21"), ("2022-11-08", "e22"), ("2023-11-07", "e23")):
        snap, = con.execute(f"""
            WITH e AS (SELECT date_diff('year', s.birthdate, DATE '{date}') a
                       FROM voters_20230901 s
                       JOIN (SELECT DISTINCT state_voter_id FROM voting_history
                             WHERE election_date = DATE '{date}') h USING (state_voter_id)
                       WHERE s.birthdate IS NOT NULL
                         AND date_diff('year', s.birthdate, DATE '{date}') >= 18)
            SELECT 100.0*COUNT(*) FILTER (WHERE a>=65)/COUNT(*) FROM e""").fetchone()
        d[f"{tag}_snap65"] = float(snap)
        d[f"{tag}_snap_delta"] = float(snap) - d[f"{tag}_obs65"]

    # The largest gap between the current-roll and snapshot reconstructions, which the paper
    # states as a bound ("agree to within ~1.4 points"). Computed HERE and not earlier: the
    # per-cycle deltas it maxes over are produced by the loop immediately above, and putting
    # this before them raised a KeyError on the first run.
    d["recon_max_gap"] = max(abs(d[f"{tg}_snap_delta"]) for tg in ("e21", "e22", "e23"))
    con.close()
    return d


def build_probes():
    p = []
    labels = {"e21": "Nov 2021", "e22": "Nov 2022", "e23": "Nov 2023",
              "e24": "Nov 2024", "e25": "Nov 2025"}
    kinds = {"e21": "Off-year", "e22": "Midterm", "e23": "Off-year",
             "e24": "Presidential", "e25": "Off-year"}

    # Coverage against the certified count, asserted exactly.
    #
    # This block briefly carried a tolerance of 1 with a comment explaining that two of the
    # paper's own tables disagreed by a single record. That explanation was wrong: the paper
    # was consistent and THIS SCRIPT was applying an age filter the paper's definition does
    # not. Widening the tolerance had made the symptom go away and preserved the defect,
    # which is the exact move CLAUDE.md forbids. The derivation is fixed and the tolerance is
    # back to the printed precision.
    for tag in ("e21", "e22", "e23", "e24", "e25"):
        p.append((f"coverage {labels[tag]}",
                  rf"\| {labels[tag]} \| {kinds[tag]} \| ([\d,]+) \| ([\d,]+) \(([\d.]+)%\) \| "
                  rf"([\d,]+) \| \*\*([\d.]+)%\*\* \|",
                  (f"{tag}_official", f"{tag}_infile", f"{tag}_infile_pct",
                   f"{tag}_analyzable", f"{tag}_cov_pct"), 0.05))
    # Survivorship hole.
    for tag, n in (("e21", "106K"), ("e22", "140K"), ("e23", "45K")):
        p.append((f"survivorship {labels[tag]}",
                  rf"\| Cast a ballot {labels[tag]} \(n≈{n}\) \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \|",
                  (f"{tag}_gone_65", f"{tag}_gone_18"), 0.05))
    # Bounding.
    for tag in ("e21", "e23", "e25"):
        p.append((f"bounding {labels[tag]}",
                  rf"\| {labels[tag]} \(residual ([\d.]+)%\) \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \| "
                  rf"([\d.]+)% \|",
                  (f"{tag}_residual_pct", f"{tag}_min65", f"{tag}_obs65", f"{tag}_max65"), 0.05))
    # Snapshot cross-validation.
    for tag in ("e21", "e22", "e23"):
        kind = "off-year" if tag != "e22" else "midterm"
        p.append((f"snapshot cross-validation {labels[tag]}",
                  rf"\| {labels[tag]} \({kind}\) \| ([\d.]+)% \| ([\d.]+)% \| \+([\d.]+) \|",
                  (f"{tag}_obs65", f"{tag}_snap65", f"{tag}_snap_delta"), 0.05))
    # Composition of the electorate.
    for tag in ("e24", "e22", "e21", "e23", "e25"):
        p.append((f"composition {labels[tag]}",
                  rf"\| {labels[tag]} \| {kinds[tag]} \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| "
                  rf"([\d.]+)% \|(?!\s*[\d.]+%)",
                  tuple(f"{tag}_comp_{b}" for b in BANDS), 0.05, "composition"))
    # Turnout rate, which carries a fifth "All" column and so cannot collide with the above.
    for tag in ("e24", "e22", "e21", "e23", "e25"):
        p.append((f"turnout rate {labels[tag]}",
                  rf"\| {labels[tag]} \| {kinds[tag]} \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| "
                  rf"([\d.]+)% \| ([\d.]+)% \|",
                  tuple(f"{tag}_rate_{b}" for b in BANDS) + (f"{tag}_rate_all",),
                  0.05, "rates"))
    # Finer cohorts, six columns.
    for tag in ("e24", "e22", "e21", "e23", "e25"):
        p.append((f"finer cohorts {labels[tag]}",
                  rf"\| {labels[tag]} \| {kinds[tag]} \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| "
                  rf"([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \|",
                  tuple(f"{tag}_fine_{b}" for b in
                        ("18-24", "25-29", "30-44", "45-64", "65-74", "75+")), 0.05, "finer"))
    # ---- ABSTRACT restatements. The abstract is what a reviewer reads first and every figure
    # in it restates a table cell below. The harness checks every occurrence of a figure, but
    # only where a probe points at it — these sentences had no probe, so the abstract could
    # have drifted from its own tables without anything failing.
    p += [
        ("abstract — source scale",
         r"a ([\d.]+)-million-voter roll\s+linked to ([\d.]+) million individual vote-history "
         r"records", ("roll_m", "history_m"), 0.05),
        ("abstract — 65+ share, three off-years against 2024",
         r"Voters 65 and older were ([\d.]+)%, ([\d.]+)%, and\s+([\d.]+)% of the 2021, 2023, "
         r"and 2025 odd-year electorates, against ([\d.]+)% in 2024",
         ("e21_comp_65+", "e23_comp_65+", "e25_comp_65+", "e24_comp_65+"), 0.05),
        ("abstract — 18-29 fall",
         r"voters\s+18–29 fell from ([\d.]+)% in 2024 to about ([\d.]+)% off-cycle",
         ("e24_comp_18-29", "off_comp_18-29"), 0.05),
        ("abstract — habitual core span",
         r"habitual core\* \((\d+)–(\d+)% of\s+off-year voters also vote in presidential "
         r"years\)", ("core_lo", "core_hi"), 0.5),

        # ---- Methods and validation prose, none of it previously probed.
        ("methods — vote-history record count restated",
         r"`voting_history` \(([\d.]+)M records\)", "history_m", 0.05),
        ("methods — 2021 certified example",
         r"November 2021: ([\d,]+) ballots counted, ([\d.]+)% turnout",
         ("e21_official", "e21_official_turnout"), 0.05),
        ("methods — analyzable coverage span",
         r"Analyzable coverage runs from \*\*([\d.]+)% in 2021 to ([\d.]+)% in 2025\*\*",
         ("cov_lo", "cov_hi"), 0.05),
        ("methods — retained snapshot size",
         r"`voters_20230901`, ([\d.]+)M rows", "snapshot_m", 0.005),
        ("survivorship — roll attrition is age-loaded",
         r"of the (\d+)K voters \(([\d.]+)%\) who left the roll\s+between 2023 and 2026, "
         r"([\d.]+)% were 65\+, versus ([\d.]+)% of those who stayed",
         ("left_k", "left_pct", "left_65", "stay_65"), 0.5),
        ("cross-check — the two reconstructions agree within",
         r"agree to within ~([\d.]+) points", "recon_max_gap", 0.05),
        ("bounds — the three off-year minima restated in prose",
         r"each off-year electorate \(\*\*([\d.]+)% / ([\d.]+)% / ([\d.]+)%\*\* 65\+\)",
         ("e21_min65", "e23_min65", "e25_min65"), 0.05),
    ]

    # Who is counted.
    p += [
        ("who is counted — registered roll",
         r"\| Registered roll \(April 2026\) \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| "
         r"([\d.]+)% \| (\d+) \|",
         tuple(f"roll_{b}" for b in BANDS) + ("roll_median",), 0.05),
        ("who is counted — 2024 returners",
         r"\| 2024 presidential ballot-returners \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| "
         r"([\d.]+)% \| (\d+) \|",
         tuple(f"e24_comp_{b}" for b in BANDS) + ("e24_median",), 0.05),
        ("who is counted — off-year returners, three-cycle average",
         r"\| Off-year ballot-returners \(2021/23/25 avg\) \| ([\d.]+)% \| ([\d.]+)% \| "
         r"([\d.]+)% \| ([\d.]+)% \| (\d+) \|",
         tuple(f"off_comp_{b}" for b in BANDS) + ("off_median",), 0.5),
    ]
    # Geography.
    for label, key in (("King County", "king"), ("Rest of state", "rest"),
                       ("Metro counties¹", "metro"), ("Rural counties", "rural")):
        p.append((f"geography — {label}",
                  rf"\| {label} \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \|",
                  tuple(f"{t}_geo_{key}" for t in ("e24", "e21", "e23", "e25")), 0.05))
    return p


UNCHECKED = [
    "The ACS resident and citizen-voting-age rows of the 'who is counted' table — external "
    "Census estimates, not derivable from the voter file. They are the benchmark the file is "
    "measured against, so re-deriving them here is not possible and not the point",
    "Appendix H's single-year-of-age retention curve and the 39-county table — both derive "
    "from the same per-election cuts asserted above, at a granularity where a probe per cell "
    "would triple this file for no additional failure mode. scripts/diag_offyear_age.py "
    "prints them",
    "The Das-Gupta behaviour-versus-rolls decomposition — a derived quantity of the "
    "composition and roll figures already asserted here, and one whose arithmetic belongs "
    "with the paper's own appendix rather than duplicated in a verifier",
]


def main() -> int:
    raw = PAPER.read_text(encoding="utf-8")
    # Three tables share a row prefix — every one of them starts "| Nov 2024 | Presidential |"
    # — and differ only in how many numeric columns follow. A five-column pattern matches the
    # first five cells of the six-column finer-cohort row, so the tables are sliced apart
    # rather than distinguished by lookahead. Each slice's end anchor is the paragraph that
    # introduces the next table, and vp.section() raises if either anchor moves.
    sections = {
        "composition": vp.section(raw, "## What the data shows",
                                  "**Within-cohort participation rate"),
        "rates": vp.section(raw, "**Within-cohort participation rate", "**Finer cohorts.**"),
        "finer": vp.section(raw, "**Finer cohorts.**", "**Birth-year assumption.**"),
    }
    return vp.run("WHO DECIDES WASHINGTON — prose scraped and asserted against the voter file",
                  vp.normalise(raw), build_probes(), derive(), UNCHECKED,
                  vp.wants_coverage(), sections=sections)


if __name__ == "__main__":
    raise SystemExit(main())
