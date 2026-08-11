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

import csv
import re
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _verify_prose as vp  # noqa: E402

vp.stdout_utf8()

RAW = (vp.ROOT / "data" / "raw" / "election_results").as_posix()
PAPER = vp.DOCS / "safe-seat-washington.md"
# This file's own name, as the basis registry keys it. Derived rather than hard-coded so a
# rename cannot silently orphan every registry row for this verifier — an orphaned row set
# makes require_bases() report "no rows", which is a failure, not a silent pass.
PAPER_VERIFIER = Path(__file__).name

GENERALS = {2016: "20161108", 2018: "20181106", 2020: "20201103",
            2022: "20221108", 2024: "20241105"}
# The matching August top-two primary, same source and same race-name grammar.
PRIMARIES = {2016: "20160802", 2018: "20180807", 2020: "20200804",
             2022: "20220802", 2024: "20240806"}
YEARS = sorted(GENERALS)

# --- FROZEN PARTY-STRING MAPPING ---------------------------------------------------------
# Party classification is a LOOKUP against docs/reference/wa_party_strings_2016-2024.csv, the
# same frozen enumeration diag_seat_competition.py reads. It is not a regex, and the reason is
# that regexes here failed silently six times across four cycles: "Democractic" (2020),
# "G.O.P." (2018), "G.O.P" with no trailing period (2016), "R" twice (2020), "MAGA Republican"
# (2024) and "Culture Republican" (2024). Every one read as a minor party. A regex cannot
# report what it did not match; an enumeration can, and this one is asserted to be exhaustive
# against the certified files by tests/test_analysis/test_wa_party_strings.py.
#
# THE TWO SCRIPTS SHARE THE SPECIFICATION, NOT THE IMPLEMENTATION -- which is the point. This
# file reads the mapping into SQL and derives every figure through DuckDB; the diagnostic reads
# the same mapping into a Python dict and derives them in Python. They are independent
# derivations of one written rule, which is the only sense in which "two implementations" is
# worth anything. Before this, they implemented DIFFERENT rules and nothing noticed: the public
# diagnostic did not apply the typo normalisation this file already did.
_PARTY_MAP_CSV = (Path(__file__).resolve().parent.parent / "docs" / "reference"
                  / "wa_party_strings_2016-2024.csv")


def _party_case_sql(column: str) -> tuple[str, str, str]:
    """-> (family, expansive, literal) CASE expressions built from the frozen mapping.

    Three specifications since 2026-08-08, not two. See the note in diag_seat_competition.py:
    folding "Culture Republican" in with "Republican" is a researcher's grouping, not one
    Washington makes, so the tiers are reported separately rather than argued for.
    """
    with _PARTY_MAP_CSV.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise SystemExit(f"empty party mapping: {_PARTY_MAP_CSV}")

    def build(col: str) -> str:
        arms = []
        for r in rows:
            lit = r["party_string"].strip().replace("'", "''")
            arms.append(f"WHEN TRIM(COALESCE({column},'')) = '{lit}' THEN '{r[col].strip()}'")
        # An unmapped, non-empty string must NOT fall to 'O'. It becomes 'UNMAPPED', which the
        # seat classifier can neither read as major nor quietly ignore -- the run fails instead.
        return ("CASE WHEN TRIM(COALESCE(" + column + ",'')) = '' THEN 'O' "
                + " ".join(arms) + " ELSE 'UNMAPPED' END")

    return build("party_class"), build("party_class_loose"), build("party_class_literal")


STRICT_SQL, LOOSE_SQL, LITERAL_SQL = _party_case_sql("party")

# One statement per year: parse the race, read the party, rank candidates, emit one row per
# seat carrying everything both dimensions need.
SEAT_SQL = """
WITH src AS (
    SELECT "Race" race, "Candidate" cand, "Party" party, TRY_CAST("Votes" AS BIGINT) votes
    FROM read_csv_auto('{path}', header=true, all_varchar=true, ignore_errors=true)),
tagged AS (
    SELECT UPPER(race) r, cand, votes,
           {strict} AS pty_s, {loose} AS pty_l, {literal} AS pty_t
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
           cand, votes, pty_s, pty_l, pty_t
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
       COUNT(*)    FILTER (WHERE pty_l = 'R')          AS nr_loose,
       COUNT(*)    FILTER (WHERE pty_t = 'D')          AS nd_literal,
       COUNT(*)    FILTER (WHERE pty_t = 'R')          AS nr_literal
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
    sql = SEAT_SQL.format(path=path, strict=STRICT_SQL, loose=LOOSE_SQL, literal=LITERAL_SQL)
    out = []
    for (ch, dist, pos, ncand, top1, runner, wp, nd, nr, ndl, nrl, ndt,
         nrt) in con.execute(sql).fetchall():
        out.append(dict(
            chamber=ch, district=dist, position=pos, ncand=int(ncand),
            margin=(None if ncand <= 1 else
                    100.0 * (float(top1) - float(runner)) / (float(top1) + float(runner))),
            band=band(int(ncand), float(top1), float(runner)),
            avail=availability(int(nd), int(nr), int(ncand)),
            avail_loose=availability(int(ndl), int(nrl), int(ncand)),
            avail_literal=availability(int(ndt), int(nrt), int(ncand)),
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


def _assert_no_zero_vote_ballot_candidates(con, d: dict) -> None:
    """Both implementations drop candidates with zero recorded votes. That is only harmless
    if no such candidate exists.

    The paper calls the single-candidate count "the hardest number" because those seats
    presented voters with *exactly one name*. That sentence and the count are the same
    proposition ONLY if there is no ballot-listed, non-write-in candidate carrying zero votes —
    otherwise a seat with two printed names could be counted as single-candidate. It happens to
    be true in all five certified files, but "happens to be true" is what a reader cannot check.
    So it is measured, recorded, and printed as `zero-vote ballot candidates = N`.
    """
    total = 0
    for y in YEARS:
        path = f"{RAW}/{GENERALS[y]}_AllState.csv"
        n, = con.execute(f"""
            WITH src AS (
                SELECT "Race" race, "Candidate" cand, TRY_CAST("Votes" AS BIGINT) votes
                FROM read_csv_auto('{path}', header=true, all_varchar=true, ignore_errors=true))
            SELECT COUNT(*) FROM src
            WHERE COALESCE(votes, 0) = 0
              AND UPPER(TRIM(COALESCE(cand, ''))) <> 'WRITE-IN'
              AND TRIM(COALESCE(cand, '')) <> ''
              AND regexp_matches(UPPER(race), '(LEGISLATIVE|CONGRESSIONAL) DISTRICT\\s+\\d+')
        """).fetchone()
        d[f"zerovote_{y}"] = n
        total += n
    d["zerovote_total"] = total


def derive_wa(d: dict) -> dict[int, list[dict]]:
    con = duckdb.connect()
    by_year = {y: wa_seats(con, y) for y in YEARS}
    primary_general_medians(con, d)
    _assert_no_zero_vote_ballot_candidates(con, d)
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
        # LITERAL tier, added 2026-08-08: orthography normalised, faction names kept distinct.
        d[f"sens_{y}_literal"] = 100.0 * sum(
            1 for x in rows if x["avail_literal"] != "dr") / n

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
    # 2018's tossup count against the rest of the series. THE CLAIM USED TO BE "more than
    # double any other year in the series" and it was FALSE (round 1, 2026-08-10): 19 against
    # 11 in 2020 is 1.7x, and 2 x 10 = 20 > 19 for 2022 and 2024 as well, so it held only
    # against 2016's 8. Every comparator was already asserted by the per-year d1 probes, so the
    # sentence contradicted the table three rows above it. A superlative carries no numeric
    # token for a probe to anchor on, so the ordering is derived here and asserted instead —
    # the `_id_is_max_oos` pattern from verify_cross_state_money.py.
    # ROUND 2 found two holes in round 1's own fix, which is why this step exists.
    # (a) The probe asserted the VALUE 11 but not that 2020 is the year that holds it. Had 2020
    #     fallen to 9 while another cycle rose to 11, "11 in 2020" would still have passed while
    #     naming the wrong year — the value is checked, the attribution was not. Now both are.
    # (b) `tossup18 / max(other)` raises ZeroDivisionError if no other cycle has a tossup. A
    #     verifier that crashes is worse than one that fails, so the quotient is guarded and an
    #     empty comparator set reports as a claim failure instead.
    _other_tossup = {y: d[f"d1_{y}_tossup"] for y in YEARS if y != 2018}
    _max = max(_other_tossup.values())
    _holders = sorted(y for y, v in _other_tossup.items() if v == _max)
    d["tossup18_next"] = _max
    d["tossup18_next_year"] = _holders[0]
    # A tie makes "the next highest, N in YYYY" an arbitrary attribution, so it is a failure
    # rather than a coin flip. Deterministic pick (lowest year) only so the reported value is
    # stable while the guard explains itself.
    d["_tossup18_next_tied"] = len(_holders) > 1
    d["_tossup18_is_max"] = d["tossup18"] > _max
    # Guards the replacement wording "nearly double", which is a weaker claim than the one it
    # replaces and must stay weaker: true at 1.5x-2.0x, false if the gap ever reaches 2x (in
    # which case "more than double" becomes sayable) or falls below 1.5x (in which case
    # "nearly double" stops being honest).
    d["_tossup18_ratio"] = (d["tossup18"] / _max) if _max else float("inf")
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


_NY_AD23_CSV = (Path(__file__).resolve().parent.parent / "docs" / "reference"
                / "ny_ad23_2022.csv")
_NY_AD23_CACHE: dict[str, int] = {}


def _check_spelled_out_counts(raw: str, d: dict) -> list[str]:
    """Assert the abstract's SPELLED-OUT counts against the derived ones.

    The abstract writes these as words, so no numeric probe can reach them — and the empty-key
    probe that used to stand in for one was silently dropped by build_probes(), which is how
    "fifteen same-party generals" survived the count moving to sixteen. A claim a regex cannot
    compare has to be checked in code or not claimed; this is the same conclusion the money
    paper reached about superlatives.
    """
    words = {n: w for w, n in {
        "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
        "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20}.items()}
    same_party = d["d2_2024_dd"] + d["d2_2024_rr"]
    lopsided = same_party - 1          # exactly one same-party general was close; asserted below
    want = (f"of {words[same_party]} same-party generals, {words[lopsided]} were also "
            f"lopsided, but one was decided by six points")
    # Collapse whitespace on both sides: the sentence is wrapped across lines in the source,
    # so a literal substring test against the raw text fails on the newline alone.
    flat = re.sub(r"\s+", " ", raw)
    if want in flat:
        return []
    return [f"abstract's spelled-out same-party sentence does not match the data; expected "
            f"“{want}”"]


def _ny_ad23_supplement(tag: str) -> list[tuple]:
    """New York Assembly District 23, 2022 — the one seat absent from the loaded returns.

    The ingested NY warehouse carries 149 of 150 Assembly districts for the 2022 general; a
    check confirms the missing one is exactly AD-23 and nothing else. Earlier drafts handled
    that by BOUNDING the result — reporting 149/150 and a range wide enough to cover either
    outcome for the absent seat. That was honest but unnecessary, because the seat is not
    unknowable: NYSBOE publishes the certified contest, and it is the closest race in the
    chamber, decided by FIFTEEN votes (Pheffer Amato 16,185, Sullivan 16,170 — candidate
    totals across all ballot lines, not the Democratic and Republican lines alone, which sum
    to less). Filling it in is strictly better than bounding it: the denominator becomes the
    real 150 and the bound disappears.

    It is supplied from a pinned CSV carrying the source URL and retrieval date rather than
    hard-coded here, so the provenance travels with the figure. It is deliberately NOT loaded
    into the warehouse: a single hand-fetched race in a bulk-loaded table is a landmine for
    every other query, and this one is needed by exactly one derivation.
    """
    if tag != "ny":
        return []
    with _NY_AD23_CSV.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    dv = sum(int(r["votes"]) for r in rows if r["party"].strip().upper().startswith("DEM"))
    rv = sum(int(r["votes"]) for r in rows if r["party"].strip().upper().startswith("REP"))
    if not dv or not rv:
        raise SystemExit(f"{_NY_AD23_CSV.name}: expected both a D and an R total")
    _NY_AD23_CACHE.update({"ny_ad23_d": dv, "ny_ad23_r": rv})
    return [("NY-AD23-2022-supplement", 2, dv, rv)]


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
        rows += _ny_ad23_supplement(tag)
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
        # Share of the chamber present in the canvass source, as a PERCENTAGE.
        # The caveat bullet states it that way ("Texas is 64% loaded"); the
        # four-state table states the raw count. Both are now asserted — the
        # percentage was invisible to the coverage gate until strict_units was
        # enabled here, because `^\d{1,2}$` exempted it.
        d[f"fs_{tag}_loaded_pct"] = 100.0 * d[f"fs_{tag}_loaded"] / n

    # New York is now complete at 150 Assembly seats — AD-23 supplied from the certified
    # NYSBOE contest (see _ny_ad23_supplement). The bound this used to compute is retired: it
    # existed only because one seat was absent, and a fetched certified result beats a range.
    if d["fs_ny_seats"] != 150:
        raise SystemExit(
            f"NY Assembly seat count is {d['fs_ny_seats']}, expected 150. The AD-23 "
            "supplement exists to close a gap of exactly one seat; a different gap means the "
            "loaded returns changed and the supplement may now be double-counting.")


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
        # REMOVED 2026-08-08: an empty-key probe used to sit here for the abstract's
        # spelled-out same-party counts. It never ran — build_probes() ends with
        # `return [x for x in p if x[2]]`, which drops any probe with an empty key tuple — so
        # when the counts moved from fifteen to sixteen, its regex went on naming "fifteen"
        # and the suite stayed green. A probe that cannot fail is worse than no probe, because
        # it reads as coverage. The word forms are now checked in code by
        # _check_spelled_out_counts(), which is where a claim no regex can compare belongs.
        ("abstract — five-cycle not-close range",
         r"the not-close share runs (\d+)–(\d+)%", ("notclose_lo", "notclose_hi"), 0.5),
        # Restatements of the same two ranges deeper in the paper. Unprobed until
        # strict_units surfaced them: every one of these endpoints is a bare
        # two-digit integer and was auto-exempt.
        ("dimension 1 — not-close range restated in the section",
         r"The share runs (\d+)–(\d+)% across a decade",
         ("notclose_lo", "notclose_hi"), 0.5),
        ("dimension 2 — no-choice five-cycle range restated",
         r"widens the five-cycle range to (\d+)–(\d+)%", ("nodr_lo", "nodr_hi"), 0.5),
        ("four-state — the Texas canvass-coverage caveat",
         r"Texas is (\d+)% loaded in the canvass returns", "fs_tx_loaded_pct", 0.5),
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
        # The YEAR is captured as well as the value (round 2). Anchoring "2020" as a literal in
        # the regex asserted only that the sentence still said 2020, not that 2020 was the year
        # holding the maximum — so a shift between cycles would have kept passing on a wrong
        # attribution.
        ("2018 tossups — the next-highest comparator and its year",
         r"the most in the series and \*\*nearly double the next highest, (\d+) in (\d{4})\*\*",
         ("tossup18_next", "tossup18_next_year"), 0),
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
        # Three columns since 2026-08-08: literal | **family (published)** | expansive.
        p.append((f"sensitivity {y}",
                  rf"\| {y} \| ([\d.]+)% \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \|",
                  (f"sens_{y}_literal", f"sens_{y}_strict", f"sens_{y}_loose"), 0.05))
    # The 2026-08-08 party-string audit added a paragraph to §Sensitivity recording what the
    # enumeration found. Its figures are restatements of derived values, so they are probed
    # rather than exempted — a paragraph explaining a correction is exactly the place a stale
    # number would survive unnoticed.
    p.append(("sensitivity, party-audit paragraph — the three moved shares",
              r"moves 2018 to \*\*([\d.]+)%\*\*, 2020 to \*\*([\d.]+)%\*\* and 2024 to "
              r"\*\*([\d.]+)%\*\*",
              ("d2_2018_nodr", "d2_2020_nodr", "d2_2024_nodr"), 0.05))
    p.append(("sensitivity, party-audit paragraph — Dimension 1 unchanged",
              r"the headline (\d+) of (\d+) stands unchanged",
              ("notclose24_n", "d1_2024_seats"), 0))
    p.append(("sensitivity, 2024 delta is exactly zero",
              r"the 2024 delta is ([\d.]+):", "sens_2024_delta", 0.0005))
    # Retargeted to 2016 on 2026-08-08. The illustration used to be 2024, whose delta is now
    # exactly 0.0 — the faction-qualified strings that separated strict from loose are major
    # under both specifications — so 2024 no longer demonstrates the rounding point at all.
    # 2016 carries the largest delta and is the year the rule actually matters.
    p.append(("sensitivity, unrounded 2016 delta",
              r"\(2016: ([\d.]+) − ([\d.]+) = ([\d.]+)\)",
              ("sens_2016_strict", "sens_2016_loose", "sens_2016_delta"), 0.0005))
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
        # AD-23 is supplied from the certified NYSBOE contest as of 2026-08-08, so the bound
        # this used to assert no longer exists. What replaces it asserts the filled figures.
        ("NY AD-23 — the supplied certified result",
         r"Pheffer Amato\s+\*\*([\d,]+)\*\* to Thomas P\. Sullivan \*\*([\d,]+)\*\*",
         ("ny_ad23_d", "ny_ad23_r"), 0),
        ("NY AD-23 — the completed chamber",
         r"the chamber reads\s+\*\*([\d.]+)%\*\* not close with \*\*([\d.]+)%\*\* offering "
         r"no D-vs-R option", ("fs_ny_notclose", "fs_ny_nodr"), 0.05),
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
    # BOTH REASONS BELOW WERE FALSE UNTIL 2026-08-10 (round 1). They described the state of the
    # paper before the 2026-08-08 party-string audit, which moved 2020's no-D-v-R share to
    # 25.4%. "26.9" was exempted as "the adopted 2020 no-D-v-R share ... asserted at its table
    # cell" — it is neither: the adopted share is 25.4% and that is what the Dimension-2 table
    # asserts. "27.6" was exempted on the ground that "the adopted figure beside it is
    # asserted", and the figure beside it is 26.9, which is itself exempt. So one stale figure
    # was waived by pointing at an assertion that did not exist, and a second was waived by
    # pointing at the first. This is the shape the audit log's rule exists for: an exemption
    # must name where the figure IS verified.
    "27.6": "the 2020 no-D-v-R share as it read BEFORE the 'Democractic' misspelling was "
            "normalised — the first step of a two-step correction, quoted to show what a "
            "literal reading of the certified string would have cost. Not a current result. "
            "The current 2020 figure is 25.4%, asserted as d2_2020_nodr in the Dimension-2 "
            "table",
    "26.9": "the 2020 no-D-v-R share after the misspelling fix but BEFORE the 2026-08-08 "
            "enumeration of all 32 party strings, which found five more major-party strings "
            "counted as minor and moved 2020 to 25.4%. An intermediate value in a superseded "
            "pass, and the sentence says 'correcting it alone'. The current figure is 25.4%, "
            "asserted as d2_2020_nodr",
    # --- §Sensitivity's three-tier discussion, added 2026-08-08.
    "1.5": "a stated BOUND over the expansive-minus-family gaps ('nothing else by more than "
           "1.5'), not a measurement. Every cell it bounds is asserted by the per-year "
           "sensitivity probes, so the claim is checkable from asserted values",
    "35.3": "the 2024 LITERAL cell, restated in the historical note about the regex this "
            "enumeration replaced. It is asserted in the sensitivity table one paragraph "
            "above, as sens_2024_literal",
    "150": "the size of the NY Assembly, a chamber fact",
    "149": "Assembly districts carrying a race in the LOADED returns, quoted while "
           "explaining why an earlier draft bounded the figure. The chamber is now complete "
           "at 150 via the certified AD-23 supplement, and 150 is asserted as fs_ny_seats",
    "0.046": "the AD-23 margin in percentage points, a restatement of the 15-vote gap "
             "between the two candidate totals, both of which are asserted from "
             "docs/reference/ny_ad23_2022.csv by the AD-23 probe",
}


def claim_guards(d: dict) -> list[str]:
    """Assert the paper's COMPARATIVE claims, which no probe can anchor on.

    A superlative or a ratio carries no numeric token, so `audit_coverage` cannot see it and a
    regex probe has nothing to capture. That is how "2018 ... more than double any other year in
    the series" survived into round 1 while every value it compared — 19, 8, 11, 10, 10 — was
    already asserted by the per-year Dimension 1 probes. The sentence contradicted the table
    three rows above it: 19 is 1.7x the next highest, and 2 x 10 = 20 > 19, so it held only
    against 2016's 8.

    A module-level function rather than inline in `main()` so it can be shown FAILING without a
    ten-minute verifier run — freeze rule §0 rule 2. Tested in
    `tests/test_infrastructure/test_safe_seat_claim_guards.py`.
    """
    fails = []
    if not d["_tossup18_is_max"]:
        fails.append(
            f"claim: the paper calls 2018 'the most in the series' for seats inside five "
            f"points, and it is not — 2018 has {d['tossup18']} against a maximum of "
            f"{d['tossup18_next']} elsewhere. Fix the sentence, not this guard.")
    elif d["_tossup18_next_tied"]:
        fails.append(
            f"claim: {d['tossup18_next']} seats inside five points is tied across more than one "
            f"cycle, so naming a single 'next highest' year is arbitrary. Reword to the tie "
            f"rather than picking one.")
    elif not (1.5 <= d["_tossup18_ratio"] < 2.0):
        fails.append(
            f"claim: 2018's tossup count is {d['_tossup18_ratio']:.2f}x the next highest "
            f"({d['tossup18']} against {d['tossup18_next']}), so 'nearly double' is the wrong "
            f"description. At >=2.0x 'more than double' becomes sayable; below 1.5x neither is "
            f"honest. This is the sentence that was false in round 1 — fix the wording.")
    return fails


def main() -> int:
    d: dict = {}
    by_year = derive_wa(d)
    derive_comparison(d)
    derive_wa_house(d, by_year)
    d.update(_NY_AD23_CACHE)
    raw = PAPER.read_text(encoding="utf-8")
    _spelled = _check_spelled_out_counts(raw, d)
    # One slice, for the one pattern that is genuinely ambiguous document-wide: the universe
    # table's four-cell row is shaped exactly like the year-header row of the primary/general
    # table 150 lines later.
    sections = {"universe": vp.section(raw, "## The seat universe", "## Dimension 1")}
    norm = vp.normalise(raw)
    audit_sections, offsets, spans = {}, {}, {}
    for name, (start, end) in AUDIT_BOUNDS.items():
        audit_sections[name], offsets[name] = vp.slice_with_offset(norm, start, end)
    stats: dict = {}
    rc = vp.run("SAFE-SEAT WASHINGTON — prose scraped and asserted against certified returns",
                norm, build_probes(), d, UNCHECKED, vp.wants_coverage(),
                sections=sections, spans_out=spans, stats_out=stats)
    print(f"\n  zero-vote ballot candidates = {d['zerovote_total']}  "
          f"(by cycle: " + ", ".join(f"{y}:{d[f'zerovote_{y}']}" for y in YEARS) + ")")
    print("  Both implementations drop zero-vote candidates. At 0 this is a no-op, which is "
          "what\n  makes the paper's 'exactly one name' reading of the single-candidate count "
          "exact\n  rather than merely probable.")
    fails = vp.audit_coverage(audit_sections, spans, offsets, tuple(AUDIT_BOUNDS),
                              COVERAGE_EXEMPT, COVERAGE_EXEMPT_LITERAL, strict_units=True)
    fails += _spelled
    # Basis registry (2026-08-10). This paper is the ROLLOUT PILOT — see
    # tests/test_infrastructure/test_basis_registry_rollout.py for which verifiers are enabled
    # and what each remaining one owes. Coverage asks "is every published figure probed";
    # this asks "is every derived figure's footing declared", which is the question five of
    # this series' figure reversals turned on.
    fails += vp.require_bases(PAPER_VERIFIER, d)
    fails += vp.audit_basis_consistency()
    fails += claim_guards(d)
    if d["zerovote_total"]:
        fails.append(
            f"zero-vote ballot candidates = {d['zerovote_total']}, not 0. The "
            "single-candidate count can no longer be read as 'exactly one name on the "
            "ballot' — a seat with a printed candidate who drew no votes now classifies as "
            "single-candidate. Fix the paper's wording or the exclusion, not this check.")
    fails += vp.audit_satellite_counts(PAPER.name, stats.get("figures"))
    if fails:
        print("\nCOVERAGE / SATELLITE AUDIT: %d FAILURE(S)" % len(fails))
        for f in fails:
            print(f"  - {f}")
        return 1
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
