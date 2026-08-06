"""Independent re-derivation of docs/safe-seat-washington.md, asserted against its prose.

WHAT CHANGED 2026-08-01, AND WHY IT MATTERED. The previous version of this file was, by its
own docstring, "SUPERSEDED for Washington" — it reproduced the pre-2026-07-27 figures from
`precinct_results`, a universe missing ~24 King County House seats in 2016 and 2018. That was
honest, but it left the paper's CURRENT headline with no independent check at all: the
published 87.8% comes from `diag_seat_competition.py`, and the only thing verifying it was
`diag_seat_competition.py`. The script also had no assertions and no non-zero exit path, so
the release checklist's `verify_safe_seat.py || echo FAILED` could never print FAILED.

Worse, its own annotation had gone stale in exactly the way it warned about: it told the
reader "PAPER publishes WA **87.8**" and "the paper's 53/33" while the paper had moved to
111 of 133 not close and a 68/43 safe split.

This version derives the paper's live figures from the same CERTIFIED SOURCE, with a
from-scratch implementation, and asserts them against the paper's own sentences.

INDEPENDENCE, precisely. Same inputs, different code. `diag_seat_competition.py` streams the
certified `*_AllState.csv` rows into Python dicts and classifies them in a loop; this script
pushes the whole classification into one DuckDB statement — race-name parsing, party reading,
candidate ranking and banding all in SQL — and aggregates the per-seat result in Python. A
transcription or logic slip in either would have to be reproduced independently in the other
to survive. What this canNOT catch is an error in the shared *specification* (if the paper's
party-reading rule is wrong, both implement it wrongly and agree), which is what the paper's
own strict-versus-loose sensitivity table exists to price.

THE RULES, restated here so the SQL below can be read against them rather than against the
other script:
  * Universe: WA certified statewide summary returns. Legislative District N Senator ->
    SEN; Legislative District N Representative Pos./Position M -> HSE (both spellings —
    2020 LD15 uses the second and matching only the first silently drops two seats);
    Congressional District N U.S. Representative -> USH. Write-ins and zero-vote
    candidates dropped.
  * Party, STRICT: "Prefers Democratic/Democrat Party" -> D, "Prefers Republican/GOP
    Party" -> R, and an Independent- or Culture-prefixed preference is OTHER even when it
    names a major party. "Democractic" is normalised to "Democratic" first — a
    transcription error in the 2020 file, not a stated preference.
  * Party, LOOSE (sensitivity only): any string containing DEMOCRA -> D, else any
    containing REPUBLICAN or GOP -> R.
  * Dimension 1, candidate competition: margin between the top two candidates by votes
    regardless of party. Not close = single candidate, or margin >= 10.
  * Dimension 2, partisan availability: what the ballot offered. No D-v-R = the seat did
    not carry at least one D and at least one R.
  * Winner party = the leading candidate's party, NOT the sign of aggregate party votes.

THE COMPARISON STATES use a different rule and the paper says so: any seat with no D-v-R
option counts as not close whatever its margin. That is the rule implemented here for
NY/TX/ID, over each state's warehouse. Texas's canvass returns omit uncontested seats, so 54
certified single-candidate districts are backfilled to reach 150 (Appendix F).

Run:  python scripts/verify_safe_seat.py [--coverage]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _verify_prose as vp  # noqa: E402

vp.stdout_utf8()

RAW = (vp.ROOT / "data" / "raw" / "election_results").as_posix()
PAPER = vp.DOCS / "safe-seat-washington.md"

GENERALS = {2016: "20161108", 2018: "20181106", 2020: "20201103",
            2022: "20221108", 2024: "20241105"}
# The matching August top-two primary, same source and same race-name grammar.
PRIMARIES = {2016: "20160802", 2018: "20180807", 2020: "20200804",
             2022: "20220802", 2024: "20240806"}
YEARS = sorted(GENERALS)

# Certified-source transcription errors, corrected before any party is read. Only a spelling
# variant of a major party's own name belongs here; a hybrid like 2016's "GOP/Independent" is
# a real stated preference and is priced by the loose column instead.
TYPO_SQL = "regexp_replace(UPPER(COALESCE(party,'')), 'DEMOCRACTIC', 'DEMOCRATIC', 'g')"

STRICT_SQL = f"""
    CASE WHEN regexp_matches({TYPO_SQL}, 'PREFERS\\s+(INDEPENDENT|CULTURE)\\s')  THEN 'O'
         WHEN regexp_matches({TYPO_SQL}, 'PREFERS\\s+(DEMOCRATIC|DEMOCRAT)\\s+PARTY') THEN 'D'
         WHEN regexp_matches({TYPO_SQL}, 'PREFERS\\s+(REPUBLICAN|GOP)\\s+PARTY')  THEN 'R'
         ELSE 'O' END"""
LOOSE_SQL = f"""
    CASE WHEN regexp_matches({TYPO_SQL}, 'DEMOCRA')            THEN 'D'
         WHEN regexp_matches({TYPO_SQL}, 'REPUBLICAN|GOP')     THEN 'R'
         ELSE 'O' END"""

# One statement per year: parse the race, read the party, rank candidates, emit one row per
# seat carrying everything both dimensions need.
SEAT_SQL = """
WITH src AS (
    SELECT "Race" race, "Candidate" cand, "Party" party, TRY_CAST("Votes" AS BIGINT) votes
    FROM read_csv_auto('{path}', header=true, all_varchar=true, ignore_errors=true)),
tagged AS (
    SELECT UPPER(race) r, cand, votes,
           {strict} AS pty_s, {loose} AS pty_l
    FROM src
    WHERE votes > 0 AND UPPER(TRIM(COALESCE(cand,''))) <> 'WRITE-IN'),
keyed AS (
    SELECT CASE
             WHEN regexp_matches(r, 'LEGISLATIVE DISTRICT\\s+\\d+')
                  AND regexp_matches(r, '\\bSENATOR\\b') THEN 'SEN'
             WHEN regexp_matches(r, 'LEGISLATIVE DISTRICT\\s+\\d+')
                  AND regexp_matches(r, 'REPRESENTATIVE,?\\s*POS(ITION)?\\.?\\s*\\d') THEN 'HSE'
             WHEN regexp_matches(r, 'CONGRESSIONAL DISTRICT\\s+\\d+')
                  AND r LIKE '%U.S. REPRESENTATIVE%' THEN 'USH'
           END AS chamber,
           -- regexp_extract yields '' (not NULL) on no match, so NULLIF before COALESCE or
           -- the empty string wins the coalesce and the CAST dies.
           TRY_CAST(COALESCE(
             NULLIF(regexp_extract(r, 'LEGISLATIVE DISTRICT\\s+(\\d+)', 1), ''),
             NULLIF(regexp_extract(r, 'CONGRESSIONAL DISTRICT\\s+(\\d+)', 1), '')
           ) AS INTEGER) AS district,
           COALESCE(TRY_CAST(NULLIF(regexp_extract(
             r, 'REPRESENTATIVE,?\\s*POS(?:ITION)?\\.?\\s*(\\d)', 1), '') AS INTEGER), 0) AS position,
           cand, votes, pty_s, pty_l
    FROM tagged),
u AS (SELECT * FROM keyed WHERE chamber IS NOT NULL),
ranked AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY chamber, district, position
                                 ORDER BY votes DESC, cand) rk
    FROM u)
SELECT chamber, district, position,
       COUNT(*)                                        AS ncand,
       MAX(votes) FILTER (WHERE rk = 1)                AS top1,
       COALESCE(MAX(votes) FILTER (WHERE rk = 2), 0)   AS runner,
       MAX(pty_s)  FILTER (WHERE rk = 1)               AS winner_pty,
       COUNT(*)    FILTER (WHERE pty_s = 'D')          AS nd,
       COUNT(*)    FILTER (WHERE pty_s = 'R')          AS nr,
       COUNT(*)    FILTER (WHERE pty_l = 'D')          AS nd_loose,
       COUNT(*)    FILTER (WHERE pty_l = 'R')          AS nr_loose
FROM ranked GROUP BY 1, 2, 3
"""


def band(ncand: int, top1: float, runner: float) -> str:
    """Candidate-competition band. Banding runs on the UNROUNDED margin: rounding first put a
    seat sitting at 9.995 in a different bucket than the threshold table, so the paper's
    headline and its robustness cut disagreed."""
    if ncand <= 1:
        return "single"
    m = 100.0 * (top1 - runner) / (top1 + runner)
    return "tossup" if m < 5 else "lean" if m < 10 else "likely" if m < 20 else "solid"


def availability(nd: int, nr: int, ncand: int) -> str:
    if ncand <= 1:
        return "single"
    if nd and nr:
        return "dr"
    if nd >= 2:
        return "dd"
    if nr >= 2:
        return "rr"
    if nd:
        return "dother"
    if nr:
        return "rother"
    return "other"


NOT_CLOSE = ("single", "likely", "solid")


def wa_seats(con, year: int) -> list[dict]:
    path = f"{RAW}/{GENERALS[year]}_AllState.csv"
    sql = SEAT_SQL.format(path=path, strict=STRICT_SQL, loose=LOOSE_SQL)
    out = []
    for ch, dist, pos, ncand, top1, runner, wp, nd, nr, ndl, nrl in con.execute(sql).fetchall():
        out.append(dict(
            chamber=ch, district=dist, position=pos, ncand=int(ncand),
            margin=(None if ncand <= 1 else
                    100.0 * (float(top1) - float(runner)) / (float(top1) + float(runner))),
            band=band(int(ncand), float(top1), float(runner)),
            avail=availability(int(nd), int(nr), int(ncand)),
            avail_loose=availability(int(ndl), int(nrl), int(ncand)),
            winner=wp))
    return out


SEAT_TOTALS_SQL = """
WITH src AS (
    SELECT "Race" race, "Candidate" cand, TRY_CAST("Votes" AS BIGINT) votes
    FROM read_csv_auto('{path}', header=true, all_varchar=true, ignore_errors=true)),
u AS (
    SELECT CASE
             WHEN regexp_matches(UPPER(race), 'LEGISLATIVE DISTRICT\\s+\\d+')
                  AND regexp_matches(UPPER(race), '\\bSENATOR\\b') THEN 'SEN'
             WHEN regexp_matches(UPPER(race), 'LEGISLATIVE DISTRICT\\s+\\d+')
                  AND regexp_matches(UPPER(race),
                        'REPRESENTATIVE,?\\s*POS(ITION)?\\.?\\s*\\d') THEN 'HSE'
             WHEN regexp_matches(UPPER(race), 'CONGRESSIONAL DISTRICT\\s+\\d+')
                  AND UPPER(race) LIKE '%U.S. REPRESENTATIVE%' THEN 'USH'
           END AS chamber,
           TRY_CAST(COALESCE(
             NULLIF(regexp_extract(UPPER(race), 'LEGISLATIVE DISTRICT\\s+(\\d+)', 1), ''),
             NULLIF(regexp_extract(UPPER(race), 'CONGRESSIONAL DISTRICT\\s+(\\d+)', 1), '')
           ) AS INTEGER) AS district,
           COALESCE(TRY_CAST(NULLIF(regexp_extract(UPPER(race),
             'REPRESENTATIVE,?\\s*POS(?:ITION)?\\.?\\s*(\\d)', 1), '') AS INTEGER), 0) AS position,
           votes
    FROM src
    WHERE votes > 0 AND UPPER(TRIM(COALESCE(cand,''))) <> 'WRITE-IN')
SELECT chamber, district, position, SUM(votes) tot
FROM u WHERE chamber IS NOT NULL GROUP BY 1, 2, 3
"""


def primary_general_medians(con, d: dict) -> None:
    """Median primary:general vote ratio per seat, per cycle.

    Seats are matched on the parsed (chamber, district, position) identity rather than on the
    race-name string, so the 2020 "Representative, Position N" spelling variant lines up with
    its general instead of dropping out. This is a ratio of VOTES CAST IN A CONTEST, which is
    what the paper says it is — roll-off means it is not a headcount of participants.
    """
    import statistics
    for y in YEARS:
        gen = {tuple(r[:3]): float(r[3]) for r in con.execute(
            SEAT_TOTALS_SQL.format(path=f"{RAW}/{GENERALS[y]}_AllState.csv")).fetchall()}
        pri = {tuple(r[:3]): float(r[3]) for r in con.execute(
            SEAT_TOTALS_SQL.format(path=f"{RAW}/{PRIMARIES[y]}_AllState.csv")).fetchall()}
        ratios = [100.0 * pri[k] / gen[k] for k in gen if k in pri and gen[k] > 0]
        d[f"pg_{y}"] = statistics.median(ratios) if ratios else -1.0


def derive_wa(d: dict) -> dict[int, list[dict]]:
    con = duckdb.connect()
    by_year = {y: wa_seats(con, y) for y in YEARS}
    primary_general_medians(con, d)
    con.close()

    for y, rows in by_year.items():
        n = len(rows)
        d[f"u{y}_house"] = sum(1 for x in rows if x["chamber"] == "HSE")
        d[f"u{y}_sen"] = sum(1 for x in rows if x["chamber"] == "SEN")
        d[f"u{y}_ush"] = sum(1 for x in rows if x["chamber"] == "USH")
        d[f"u{y}_total"] = n
        for key, b in (("single", "single"), ("tossup", "tossup"), ("lean", "lean"),
                       ("likely", "likely"), ("solid", "solid")):
            d[f"d1_{y}_{key}"] = sum(1 for x in rows if x["band"] == b)
        d[f"d1_{y}_seats"] = n
        d[f"d1_{y}_notclose"] = 100.0 * sum(1 for x in rows if x["band"] in NOT_CLOSE) / n
        for key in ("dr", "dd", "rr", "dother", "rother", "single"):
            d[f"d2_{y}_{key}"] = sum(1 for x in rows if x["avail"] == key)
        d[f"d2_{y}_seats"] = n
        d[f"d2_{y}_nodr"] = 100.0 * sum(1 for x in rows if x["avail"] != "dr") / n
        # Sensitivity: the same count with the loose party reading.
        d[f"sens_{y}_strict"] = d[f"d2_{y}_nodr"]
        d[f"sens_{y}_loose"] = 100.0 * sum(1 for x in rows if x["avail_loose"] != "dr") / n
        d[f"sens_{y}_delta"] = d[f"sens_{y}_strict"] - d[f"sens_{y}_loose"]

    d["notclose_lo"] = min(d[f"d1_{y}_notclose"] for y in YEARS)
    d["notclose_hi"] = max(d[f"d1_{y}_notclose"] for y in YEARS)
    d["nodr_lo"] = min(d[f"d2_{y}_nodr"] for y in YEARS)
    d["nodr_hi"] = max(d[f"d2_{y}_nodr"] for y in YEARS)

    r24 = by_year[2024]
    nc = [x for x in r24 if x["band"] in NOT_CLOSE]
    d["notclose24_n"] = len(nc)
    d["close24_n"] = len(r24) - len(nc)
    d["close24_pct"] = 100.0 * (len(r24) - len(nc)) / len(r24)
    d["safe24_d"] = sum(1 for x in nc if x["winner"] == "D")
    d["safe24_r"] = sum(1 for x in nc if x["winner"] == "R")
    nodr = [x for x in r24 if x["avail"] != "dr"]
    d["nodr24_n"] = len(nodr)
    d["nodr24_single"] = sum(1 for x in nodr if x["avail"] == "single")
    d["nodr24_same"] = sum(1 for x in nodr if x["avail"] in ("dd", "rr"))
    d["nodr24_majorminor"] = sum(1 for x in nodr if x["avail"] in ("dother", "rother"))
    same = [x for x in r24 if x["avail"] in ("dd", "rr")]
    d["same24_n"] = len(same)
    d["same24_lopsided"] = sum(1 for x in same if x["margin"] is not None and x["margin"] >= 10)
    d["same24_over20"] = sum(1 for x in same if x["margin"] is not None and x["margin"] >= 20)
    # The one same-party general that was a real contest: WA-04, R-v-R.
    contest = [x for x in same if x["margin"] is not None and x["margin"] < 10]
    d["wa04_margin"] = contest[0]["margin"] if len(contest) == 1 else -1.0
    d["tossup18"] = d["d1_2018_tossup"]
    # 2024 cross-tab, availability x band.
    for a in ("dr", "dd", "rr", "dother", "rother", "single"):
        for b in ("single", "tossup", "lean", "likely", "solid"):
            d[f"x24_{a}_{b}"] = sum(1 for x in r24 if x["avail"] == a and x["band"] == b)
    return by_year


# --------------------------------------------------------------- comparison states
CMP_PARTY = ("CASE WHEN party_normalized ILIKE '%democrat%' THEN 'D' "
             "WHEN party_normalized ILIKE '%republican%' OR party_normalized ILIKE '%gop%' "
             "THEN 'R' ELSE 'O' END")
CMP_SPECS = [
    ("ny", "ny_statewide", 2022, "r.office ILIKE '%ASSEMBLY DISTRICT%'", None),
    ("tx", "tx_statewide", 2024, "r.office ILIKE '%HOUSE DISTRICT%'", 150),
    ("id", "id_statewide", 2024, "r.office ILIKE 'REPRESENTATIVE DISTRICT%'", None),
]


def derive_comparison(d: dict) -> None:
    """NY / TX / ID lower chambers, on the rule the paper states for them: a seat with no
    D-v-R option is not close whatever its margin, plus Likely and Solid on top."""
    for tag, db, year, office_sql, backfill_to in CMP_SPECS:
        con = duckdb.connect(str(vp.DATA / f"{db}.duckdb"), read_only=True)
        rows = con.execute(f"""
            WITH cand AS (
                SELECT r.race_id, ({CMP_PARTY}) pty, cd.candidate_id
                FROM races r JOIN elections e ON e.election_id = r.election_id
                JOIN candidates cd ON cd.race_id = r.race_id
                WHERE e.election_type = 'general'
                  AND date_part('year', e.election_date) = {year}
                  AND ({office_sql}) AND COALESCE(cd.is_writein, FALSE) = FALSE),
            v AS (SELECT c.race_id, c.candidate_id, c.pty, SUM(pr.votes) vv
                  FROM cand c JOIN precinct_results pr ON pr.candidate_id = c.candidate_id
                  GROUP BY 1, 2, 3)
            SELECT race_id, COUNT(*) FILTER (WHERE vv > 0) ncand,
                   COALESCE(SUM(vv) FILTER (WHERE pty = 'D'), 0) dv,
                   COALESCE(SUM(vv) FILTER (WHERE pty = 'R'), 0) rv
            FROM v GROUP BY 1""").fetchall()
        con.close()
        loaded = len(rows)
        n_nodr = n_notclose = 0
        for _, ncand, dv, rv in rows:
            dv, rv = float(dv), float(rv)
            nodr = ncand <= 1 or dv == 0 or rv == 0
            n_nodr += nodr
            n_notclose += nodr or (abs(dv - rv) / (dv + rv) * 100 >= 10)
        n = loaded
        if backfill_to:                      # TX: the canvass omits uncontested seats
            absent = backfill_to - loaded
            n, n_nodr, n_notclose = backfill_to, n_nodr + absent, n_notclose + absent
            d[f"fs_{tag}_backfill"] = absent
            d[f"fs_{tag}_loaded"] = loaded
        d[f"fs_{tag}_seats"] = n
        d[f"fs_{tag}_loaded"] = d.get(f"fs_{tag}_loaded", loaded)
        d[f"fs_{tag}_nodr_n"] = n_nodr
        d[f"fs_{tag}_nodr"] = 100.0 * n_nodr / n
        d[f"fs_{tag}_notclose"] = 100.0 * n_notclose / n

    # New York is one Assembly seat short; the paper bounds the effect rather than hiding it.
    ny_nc = d["fs_ny_notclose"] * d["fs_ny_seats"] / 100.0
    d["fs_ny_bound_lo"] = 100.0 * ny_nc / 150.0
    d["fs_ny_bound_hi"] = 100.0 * (ny_nc + 1) / 150.0


def derive_wa_house(d: dict, by_year: dict[int, list[dict]]) -> None:
    """The four-state table's WA row: House only, on WA's own top-two-margin rule."""
    hse = [x for x in by_year[2024] if x["chamber"] == "HSE"]
    d["fs_wa_seats"] = len(hse)
    d["fs_wa_notclose"] = 100.0 * sum(1 for x in hse if x["band"] in NOT_CLOSE) / len(hse)
    d["fs_wa_nodr_n"] = sum(1 for x in hse if x["avail"] != "dr")
    d["fs_wa_nodr"] = 100.0 * d["fs_wa_nodr_n"] / len(hse)
    lo = [d[f"fs_{t}_notclose"] for t in ("wa", "ny", "tx", "id")]
    d["fs_all_lo"], d["fs_all_hi"] = min(lo), max(lo)
    cmp_only = [d[f"fs_{t}_notclose"] for t in ("ny", "tx", "id")]
    d["fs_cmp_lo"], d["fs_cmp_hi"] = min(cmp_only), max(cmp_only)


# ------------------------------------------------------------------------------- the probes
def build_probes():
    p = [
        # ---- abstract, which restates the headline and is where a contradiction would show
        ("abstract — 2024 not close",
         r"In 2024, (\d+) of (\d+) seats \(([\d.]+)%\) were not close",
         ("notclose24_n", "d1_2024_seats", "d1_2024_notclose"), 0.05),
        ("abstract — 2024 no D-v-R",
         r"and (\d+) \(([\d.]+)%\) offered no Democratic-versus-Republican option",
         ("nodr24_n", "d2_2024_nodr"), 0.05),
        ("abstract — same-party lopsided / the one contest",
         r"of fifteen same-party generals, (\w+) were also lopsided, but one was decided by "
         r"(\w+) points", (), 0),      # worded, not numeric; checked numerically below
        ("abstract — five-cycle not-close range",
         r"the not-close share runs (\d+)–(\d+)%", ("notclose_lo", "notclose_hi"), 0.5),
        ("abstract — five-cycle no-choice range",
         r"no-major-choice share (\d+)–(\d+)%", ("nodr_lo", "nodr_hi"), 0.5),
        ("abstract — comparison-state range",
         r"in the lower chambers of three comparison states, (\d+)–(\d+)% of seats were not "
         r"close", ("fs_cmp_lo", "fs_cmp_hi"), 0.5),
        ("abstract — safe split",
         r"splitting (\d+)\s*Democratic to (\d+) Republican", ("safe24_d", "safe24_r"), 0),
    ]
    # ---- seat universe table
    #
    # The trailing (?! \d) is load-bearing. Normalisation collapses the document to one line,
    # so a four-cell pattern keyed on the year also matches the FIRST four cells of that same
    # year's row in the dimension-1 and dimension-2 tables below — which is how the first run
    # of this probe reported 24 spurious failures against perfectly good data. Requiring that
    # no further numeric cell follows pins each match to a row that really is four cells wide.
    for y in YEARS:
        p.append((f"universe {y}",
                  rf"\| {y} \| (\d+) \| (\d+) \| (\d+) \| (\d+) \|(?! \d)",
                  (f"u{y}_house", f"u{y}_sen", f"u{y}_ush", f"u{y}_total"), 0, "universe"))
    # Primary:general participation. Probed rather than exempted — the derivation is fifteen
    # lines over files this script already opens, and "another script owns it" is the weakest
    # form of coverage the donor paper's audit accepts.
    p.append(("primary:general median ratio, all five cycles",
              r"\| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| \*\*([\d.]+)%\*\* \|",
              tuple(f"pg_{y}" for y in YEARS), 0.05))
    # ---- dimension 1
    for y in YEARS:
        p.append((f"dimension 1, {y}",
                  rf"\| {y} \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| "
                  rf"\*\*([\d.]+)%\*\* \|",
                  (f"d1_{y}_seats", f"d1_{y}_single", f"d1_{y}_tossup", f"d1_{y}_lean",
                   f"d1_{y}_likely", f"d1_{y}_solid", f"d1_{y}_notclose"), 0.05))
    # ---- dimension 2
    for y in YEARS:
        p.append((f"dimension 2, {y}",
                  rf"\| {y} \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| "
                  rf"\*\*([\d.]+)%\*\* \|",
                  (f"d2_{y}_seats", f"d2_{y}_dr", f"d2_{y}_dd", f"d2_{y}_rr", f"d2_{y}_dother",
                   f"d2_{y}_rother", f"d2_{y}_single", f"d2_{y}_nodr"), 0.05))
    p += [
        ("2024 close seats",
         r"of (\d+) partisan seats only \*\*(\d+) \(([\d.]+)%\) were decided by under ten "
         r"points\*\*", ("d1_2024_seats", "close24_n", "close24_pct"), 0.05),
        ("2018 tossups", r"when (\d+) seats landed inside five points", "tossup18", 0),
        ("safe seats are bipartisan",
         r"\*\*(\d+) were won by Democrats and (\d+) by Republicans\*\*",
         ("safe24_d", "safe24_r"), 0),
        ("2024 no-choice decomposition",
         r"\*\*(\d+) of (\d+) Washington races — more than a third of the partisan ballot — "
         r"offered no Democratic-versus-Republican option\*\*: (\d+) had a single candidate, "
         r"(\d+) pitted two candidates of the same party against each other, and (\d+) set a "
         r"major-party candidate",
         ("nodr24_n", "d2_2024_seats", "nodr24_single", "nodr24_same", "nodr24_majorminor"), 0),
        ("same-party generals, lopsided and over twenty",
         r"(\d+) of (\d+) in 2024 exceeded ten points, and (\d+) exceeded twenty",
         ("same24_lopsided", "same24_n", "same24_over20"), 0),
        ("WA-04, the contested same-party general",
         r"R-vs-R general decided by \*\*([\d.]+) points\*\*", "wa04_margin", 0.05),
    ]
    # ---- 2024 cross-tab
    for label, a in (("D-v-R", "dr"), ("D-v-D", "dd"), ("R-v-R", "rr"),
                     ("D-v-other", "dother"), ("R-v-other", "rother")):
        p.append((f"cross-tab {label}",
                  rf"\| {re.escape(label)} \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| (\d+) \|",
                  tuple(f"x24_{a}_{b}" for b in
                        ("single", "tossup", "lean", "likely", "solid")), 0))
    p.append(("cross-tab single candidate",
              r"\| single candidate \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| (\d+) \|",
              tuple(f"x24_single_{b}" for b in
                    ("single", "tossup", "lean", "likely", "solid")), 0))
    # ---- sensitivity
    for y in YEARS:
        p.append((f"sensitivity {y}",
                  rf"\| {y} \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+) \|",
                  (f"sens_{y}_strict", f"sens_{y}_loose", f"sens_{y}_delta"), 0.05))
    p.append(("sensitivity, unrounded 2024 delta",
              r"\(2024: ([\d.]+) − ([\d.]+) = ([\d.]+)\)",
              ("sens_2024_strict", "sens_2024_loose", "sens_2024_delta"), 0.0005))
    # ---- four-state
    p += [
        ("four-state, WA House",
         r"\| WA House 2024 \| (\d+) / \d+ \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \((\d+)\) \|",
         ("fs_wa_seats", "fs_wa_notclose", "fs_wa_nodr", "fs_wa_nodr_n"), 0.05),
        ("four-state, NY Assembly",
         r"\| NY Assembly 2022 \| (\d+) / 150 \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \((\d+)\) \|",
         ("fs_ny_loaded", "fs_ny_notclose", "fs_ny_nodr", "fs_ny_nodr_n"), 0.05),
        ("four-state, TX House",
         r"\| TX House 2024 \| (\d+) canvass \+ (\d+) certified single-candidate \| "
         r"\*\*([\d.]+)%\*\* \| ([\d.]+)% \((\d+)\) \|",
         ("fs_tx_loaded", "fs_tx_backfill", "fs_tx_notclose", "fs_tx_nodr", "fs_tx_nodr_n"),
         0.05),
        ("four-state, ID House",
         r"\| ID House 2024 \| (\d+) / \d+ \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \((\d+)\) \|",
         ("fs_id_seats", "fs_id_notclose", "fs_id_nodr", "fs_id_nodr_n"), 0.05),
        ("four-state range across all four",
         r"in every state examined, \*\*(\d+)–(\d+)% of lower-chamber seats were not close",
         ("fs_all_lo", "fs_all_hi"), 0.5),
        ("NY AD-23 bounds",
         r"if AD-23 was close the chamber reads \*\*([\d.]+)%\*\* not close, if it was not "
         r"close, \*\*([\d.]+)%\*\*", ("fs_ny_bound_lo", "fs_ny_bound_hi"), 0.05),
    ]
    return [x for x in p if x[2]]      # drop the prose-only anchor placeholder


UNCHECKED = [
    "Appendix G's SUPERSEDED figures — they describe the retired precinct_results universe "
    "on purpose; reproducing them is what the pre-2026-08-01 version of this script did, and "
    "asserting them here would re-enshrine the count this rebuild replaced",
    "The Texas seat-by-seat backfill roster and its 56 D / 85 R split — sourced from the TX "
    "SoS certified results in Appendix F, independently derived by "
    "scripts/diag_safe_seat_party_ratio.py",
    "Appendix E's threshold sweep (74%-98% across 15-to-5-point cuts) and the no-major-choice "
    "re-scoring counts — derived by scripts/diag_safe_seat_robustness.py",
]



# --- Coverage gate (ported 2026-08-06; see verify_who_decides_wa) --------------
# The result sections, partitioned so no slice overlaps another: spans are
# per-section coordinates, so a slice that swallows another reports the inner
# one's probed cells as unmapped.
AUDIT_BOUNDS = {
        "universe": ("## The seat universe", "## Dimension 1"),
        "dim1": ("## Dimension 1", "## Dimension 2"),
        "dim2": ("## Dimension 2", "## The four-state comparison"),
        "fourstate": ("## The four-state comparison", "## Why it matters"),
    }

COVERAGE_EXEMPT = [
    (r"^(?:19|20)\d{2}$", "a calendar year, not a result"),
    (r"^\d{1,2}$", "small integer — list ordinals, chamber ids, column counts"),
]
COVERAGE_EXEMPT_LITERAL: dict[str, str] = {
    "48.5": "the 2016 outlier share, stated in the Dimension-2 table one line "
            "above and asserted there; the prose repeats the table cell",
    "51,981": "an illustrative candidate vote count naming the Klippert/Regev "
              "race to show how a same-party general classifies; a worked "
              "example of the rule, not a result of it",
    "26,979": "the other side of the same worked example",
    "27.6": "the no-D-v-R share under the ALTERNATIVE definition the paper "
            "rejects, quoted to show what rejecting it would cost; the adopted "
            "figure beside it is asserted",
    "26.9": "the adopted 2020 no-D-v-R share as restated in this sentence; "
            "asserted at its table cell in the Dimension-2 block",
    "150": "the size of the NY Assembly, a chamber fact",
    "149": "Assembly districts carrying a race in the loaded returns; the one "
           "absent seat (AD 23) is named in the same sentence",
}


def main() -> int:
    d: dict = {}
    by_year = derive_wa(d)
    derive_comparison(d)
    derive_wa_house(d, by_year)
    raw = PAPER.read_text(encoding="utf-8")
    # One slice, for the one pattern that is genuinely ambiguous document-wide: the universe
    # table's four-cell row is shaped exactly like the year-header row of the primary/general
    # table 150 lines later.
    sections = {"universe": vp.section(raw, "## The seat universe", "## Dimension 1")}
    norm = vp.normalise(raw)
    audit_sections, offsets, spans = {}, {}, {}
    for name, (start, end) in AUDIT_BOUNDS.items():
        audit_sections[name], offsets[name] = vp.slice_with_offset(norm, start, end)
    rc = vp.run("SAFE-SEAT WASHINGTON — prose scraped and asserted against certified returns",
                norm, build_probes(), d, UNCHECKED, vp.wants_coverage(),
                sections=sections, spans_out=spans)
    fails = vp.audit_coverage(audit_sections, spans, offsets, tuple(AUDIT_BOUNDS),
                              COVERAGE_EXEMPT, COVERAGE_EXEMPT_LITERAL)
    if fails:
        print("\nCOVERAGE AUDIT: %d FAILURE(S)" % len(fails))
        for f in fails:
            print(f"  - {f}")
        return 1
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
