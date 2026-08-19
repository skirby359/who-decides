"""Shared state enumeration + competitiveness helpers for the cross-state FEC
money analysis scripts (docs/cross-state-fec-money.md).

State-agnostic by design: the analysis region is discovered by globbing
``data/*_statewide.duckdb`` — any state whose statewide DB is on disk is
included — overridable with the ``CROSS_STATE_REGION`` env var (comma-separated
codes, e.g. ``WA,ID``). Adding a state needs NO edits here or in the analysis
scripts: load its ``data/<code>_statewide.duckdb`` (+ ``FEC_INFLOW_STATES=<code>``
for the shared inflow DB) and re-run.

The 2-letter code equals ``contributor_state`` / ``recipient_state`` for these
states, so no ``config/`` dependency is needed for the SQL filters.
"""
from __future__ import annotations

import glob
import json
import os
from pathlib import Path
from typing import NamedTuple

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"


def region_states() -> list[tuple[str, str]]:
    """``[(CODE, statewide_db_abspath)]`` for the analysis region, sorted by code.

    ``CROSS_STATE_REGION`` (comma-separated codes) overrides discovery; otherwise
    every ``data/*_statewide.duckdb`` present on disk is included. Absolute paths
    are returned so callers work regardless of cwd.
    """
    override = os.environ.get("CROSS_STATE_REGION", "").strip()
    if override:
        codes = [c.strip().upper() for c in override.split(",") if c.strip()]
        pairs = [(c, str(DATA_DIR / f"{c.lower()}_statewide.duckdb")) for c in codes]
        return sorted(((c, p) for c, p in pairs if Path(p).exists()), key=lambda cp: cp[0])
    out = []
    for p in sorted(glob.glob(str(DATA_DIR / "*_statewide.duckdb"))):
        code = Path(p).stem.replace("_statewide", "").upper()
        out.append((code, p))
    return sorted(out, key=lambda cp: cp[0])


def region_codes() -> list[str]:
    return [c for c, _ in region_states()]


def region_sql(codes: list[str] | None = None) -> str:
    """SQL literal list of region codes, e.g. ``'WA','NY','TX','ID'``."""
    codes = codes if codes is not None else region_codes()
    return ",".join(f"'{c}'" for c in codes)


def broadly_funded_min(codes: list[str] | None = None) -> int:
    """Min # of region states for a "broadly funded" magnet = all but at most one.

    Replaces the old hardcoded ``>= 3`` / ``== 3`` thresholds so the "funded
    across the region" concept scales as states are added.
    """
    n = len(codes if codes is not None else region_codes())
    return max(1, n - 1)


def band(margin_abs: float) -> str:
    """Cook-style competitiveness band from the ABSOLUTE two-party margin (pts)."""
    if margin_abs < 5:
        return "Tossup"
    if margin_abs < 10:
        return "Lean"
    if margin_abs < 20:
        return "Likely"
    return "Solid"


def competitiveness_bands(states: list[tuple[str, str]] | None = None) -> dict:
    """``{(state, cd_id): (margin_abs, band)}`` from each state's latest Democratic
    congressional-district forecast.

    Reads ``forecast_predictions`` (party='Democratic', ``district_id LIKE 'cd%'``,
    latest ``as_of_date`` per district) from each state's statewide DB. States
    whose DB is locked or carries no ``cd`` rows are skipped, so the map contains
    whatever is available. This is the single copy of the logic that used to be
    duplicated inside each competitiveness script.

    ⚠ **This is a 2026-only map and must not be used to band money from an earlier
    cycle.** Doing so answers "did districts *forecast* competitive in 2026 receive
    more money across 2022–2026?", not "did money chase competitive races?" — a
    different estimand, and the one Sections D/E/H/J/K2 accidentally reported until
    2026-08-16. Use :func:`district_cycle_competitiveness`, which bands each cycle
    on its own evidence. Retained for the Senate cut and for reproducing the
    retired figures.
    """
    import duckdb

    states = states if states is not None else region_states()
    comp: dict = {}
    for st, f in states:
        try:
            c = duckdb.connect(f, read_only=True)
        except Exception:
            continue
        try:
            rows = c.execute(
                "WITH r AS (SELECT district_id, predicted_margin, "
                "ROW_NUMBER() OVER (PARTITION BY district_id ORDER BY as_of_date DESC) rn "
                "FROM forecast_predictions WHERE party='Democratic' AND district_id LIKE 'cd%') "
                "SELECT district_id, predicted_margin FROM r WHERE rn=1"
            ).fetchall()
        finally:
            c.close()
        for cd, m in rows:
            comp[(st, cd)] = (abs(float(m)), band(abs(float(m))))
    return comp


#: Two-party classifier shared with ``diag_safe_seat_states`` / ``diag_tx_safe_seat_backfill``.
#: Anything that is not a major-party candidate falls to ``'O'`` and is excluded from the
#: margin, which is also what keeps Idaho's ``OVERVOTES`` / ``UNDERVOTES`` pseudo-candidate
#: rows (210 of them, party ``'Nan'``, 285K "votes") out of every figure here.
_PARTY_CASE = """CASE
  WHEN cd.party_normalized ILIKE '%democrat%' THEN 'D'
  WHEN cd.party_normalized ILIKE '%republican%' OR cd.party_normalized ILIKE '%gop%' THEN 'R'
  ELSE 'O' END"""

#: U.S. HOUSE office predicate. Named rather than inlined so the office-naming lint can
#: exercise it directly in DuckDB against the real strings -- see
#: tests/test_infrastructure/test_office_name_convention_lint.py.
#:
#: Idaho named its U.S. House seats 'REPRESENTATIVE DISTRICT 1' with NO 'U.S.' prefix through
#: 2022, and 'REPRESENTATIVE DISTRICT 1 SEAT A' is its STATE house from 2024. Anchoring on
#: end-of-string is the only thing separating them: a prefix match on 'REPRESENTATIVE DISTRICT%'
#: takes both, which is how two congressional districts were scored as state-house districts 1
#: and 2 until 2026-08-17.
_CONG_OFFICE_PRED = ("(r.office ILIKE '%U.S. REPRESENTATIVE%'"
                     " OR REGEXP_MATCHES(r.office, '^REPRESENTATIVE DISTRICT [0-9]+$'))")

#: Congressional general-election two-party totals per (cycle, district), for any state DB.
#: The district number is parsed out of ``race_name`` rather than read from ``races.district``
#: because the four states disagree: WA writes ``CONGRESSIONAL DISTRICT 1 - U.S.
#: REPRESENTATIVE`` with an EMPTY ``district`` column, NY/TX write ``U.S. REPRESENTATIVE
#: CONGRESSIONAL DISTRICT 1`` with ``district='01'``, and ID writes ``U.S. REPRESENTATIVE
#: DISTRICT 1`` with an empty column. ``DISTRICT <n>`` is the one token all four share.
_CONG_MARGIN_SQL = f"""
SELECT YEAR(e.election_date) AS cycle,
       'cd' || LPAD(REGEXP_EXTRACT(r.race_name, 'DISTRICT[ ]+([0-9]+)', 1), 2, '0') AS cd,
       SUM(CASE WHEN {_PARTY_CASE}='D' THEN pr.votes ELSE 0 END) AS d,
       SUM(CASE WHEN {_PARTY_CASE}='R' THEN pr.votes ELSE 0 END) AS r,
       MAX(CASE WHEN {_PARTY_CASE}='D' THEN 1 ELSE 0 END) AS has_d,
       MAX(CASE WHEN {_PARTY_CASE}='R' THEN 1 ELSE 0 END) AS has_r
FROM races r
JOIN elections e ON e.election_id = r.election_id
JOIN candidates cd ON cd.race_id = r.race_id
JOIN precinct_results pr ON pr.candidate_id = cd.candidate_id
WHERE e.election_type = 'general'
  AND {_CONG_OFFICE_PRED}
  AND COALESCE(cd.is_writein, FALSE) = FALSE
  AND REGEXP_EXTRACT(r.race_name, 'DISTRICT[ ]+([0-9]+)', 1) <> ''
GROUP BY 1, 2
"""

#: Idaho U.S. House votes transcribed from the SoS canvass. **EXTERNAL VALIDATION FIXTURE, no
#: longer a band source** (2026-08-17): the results were in `precinct_results` the whole time,
#: under `office = 'REPRESENTATIVE DISTRICT n'` with no "U.S." prefix before 2024, and the
#: predicate above missed them. The file is kept because it independently reproduces the loaded
#: data to the vote on all six cells, which is a real check on the loader --
#: `tests/test_infrastructure/test_cycle_competitiveness.py` asserts it.
ID_CONG_PIN = REPO_ROOT / "docs" / "reference" / "id_congressional_margins_2018_2022.csv"

#: The state-house counterpart, same story and same status: **validation fixture, not a band
#: source.** It reproduces the loaded data on 34 of Idaho's 35 districts; the 35th is a defect
#: in the CANVASS rather than the load, documented in the file and in the test.
ID_LEG_PIN = REPO_ROOT / "docs" / "reference" / "id_legislative_margins_2022.csv"

#: The cycle whose band comes from the locked forecast rather than an observed result.
FORECAST_CYCLE = 2026

NO_MAJOR_CHOICE = "NoMajorChoice"
UNAVAILABLE = "Unavailable"


class CycleBand(NamedTuple):
    """One (state, cycle, district) competitiveness cell.

    ``margin`` is the SIGNED two-party margin in points, D minus R — signed, not
    absolute, because Section J needs the direction (favored vs longshot) and used to
    keep a private copy of this logic for exactly that reason. ``None`` where the cell
    carries no measurable two-party margin.
    """

    margin: float | None
    band: str
    basis: str


def district_cycle_competitiveness(
    states: list[tuple[str, str]] | None = None,
) -> dict[tuple[str, int, str], CycleBand]:
    """``{(state, cycle, cd_id): CycleBand}`` — each cycle banded on ITS OWN evidence.

    This is the canonical competitiveness basis for any retrospective money question.
    :func:`competitiveness_bands` labels every cycle with the 2026 forecast, which
    silently changes the estimand; see the warning on that function.

    Basis, by cell:

    ==================  =======================================================
    ``observed``        this cycle's loaded general-election canvass, two-party
    ``certified``       NY 2024, from ``ny_downballot_2024`` (certified NYSBOE
                        PDF) — NY's 2024 congressional general is not in
                        ``precinct_results``
    ``pinned``          Idaho pre-2024, from :data:`ID_CONG_PIN`
    ``forecast``        2026 only, from the locked ``forecast_predictions``
    ``unavailable``     no canvass published for the seat (TX does not publish
                        precinct returns for uncontested races) or an unresolved
                        pin row
    ==================  =======================================================

    Two bands are NOT margins and must never be pooled into ``Solid``:

    * ``NoMajorChoice`` — only one major party fielded a candidate, so a two-party
      margin is degenerate (WA's top-two produces D-vs-D and R-vs-R generals that
      compute to ±100). This is the safe-seat paper's Dimension 2, kept separate
      here for the same reason it is kept separate there: a same-party general can
      be a real contest, and calling it ``Solid`` on a ±100 margin invents a
      competitiveness reading the votes do not carry.
    * ``Unavailable`` — the seat is absent from the canvass.

    Measured 2026-08-16 over 2018–2026 U.S. House inflow: ``observed``/``certified``
    two-party cells carry **80.4%** of the dollars and ``forecast`` 2026 a further
    **15.3%**, leaving 4.4% across ``NoMajorChoice`` (2.0%), ``Unavailable`` (2.0%)
    and the Idaho pin (0.4%). Report that residual; do not silently drop it.

    ⚠ **New York's districts are not a panel across 2022↔2024.** NY ran a
    special-master map in 2022 and a court-drawn map in 2024, so ``('NY', 2022,
    'cd05')`` and ``('NY', 2024, 'cd05')`` are different areas. Band each cycle on
    its own map — never difference a NY district across that boundary.
    """
    import duckdb

    states = states if states is not None else region_states()
    out: dict[tuple[str, int, str], CycleBand] = {}

    for st, f in states:
        try:
            c = duckdb.connect(f, read_only=True)
        except Exception:
            continue
        try:
            observed = c.execute(_CONG_MARGIN_SQL).fetchall()
            forecast = c.execute(
                "WITH r AS (SELECT district_id, predicted_margin, "
                "ROW_NUMBER() OVER (PARTITION BY district_id ORDER BY as_of_date DESC) rn "
                "FROM forecast_predictions WHERE party='Democratic' AND district_id LIKE 'cd%') "
                "SELECT district_id, predicted_margin FROM r WHERE rn=1"
            ).fetchall()
            certified = []
            if st == "NY":
                try:
                    certified = c.execute(
                        "SELECT district_id, dem_two_party_pct FROM ny_downballot_2024 "
                        "WHERE office='congressional'"
                    ).fetchall()
                except Exception:
                    certified = []
        finally:
            c.close()

        for cycle, cd, d, r, has_d, has_r in observed:
            total = float(d) + float(r)
            if not (has_d and has_r) or total <= 0:
                out[(st, int(cycle), cd)] = CycleBand(None, NO_MAJOR_CHOICE, "observed")
            else:
                m = 100.0 * (float(d) - float(r)) / total
                out[(st, int(cycle), cd)] = CycleBand(m, band(abs(m)), "observed")

        for cd, pct in certified:
            m = 2.0 * float(pct) - 100.0  # dem two-party % -> signed D-minus-R margin
            out[(st, 2024, cd)] = CycleBand(m, band(abs(m)), "certified")

        for cd, m in forecast:
            out[(st, FORECAST_CYCLE, cd)] = CycleBand(
                float(m), band(abs(float(m))), "forecast")

    return out


#: Lower-chamber general-election two-party totals per (cycle, district number). The office
#: predicate differs per state because the four chambers are named differently in each canvass;
#: these are the SAME predicates ``diag_safe_seat_states`` uses, so the two cannot fork.
_LOWER_CHAMBER_PRED = {
    "WA": "r.office IN ('State Representative Pos. 1','State Representative Pos. 2')",
    "NY": "r.office ILIKE '%ASSEMBLY DISTRICT%'",
    "TX": "r.office ILIKE '%HOUSE DISTRICT%'",
    # Idaho changed convention at 2024. Through 2022 its STATE house is
    # 'LEGISLATIVE DISTRICT 18 ST REP A'; from 2024 it is 'REPRESENTATIVE DISTRICT 18 SEAT A'.
    # The bare 'REPRESENTATIVE DISTRICT 1' in the earlier years is the U.S. House seat, so a
    # prefix match on 'REPRESENTATIVE DISTRICT%' silently imported two congressional districts
    # as state-house districts 1 and 2 -- which is what it did until 2026-08-17.
    # Both ends anchored. The trailing wildcard in 'LEGISLATIVE DISTRICT% ST REP %' also
    # matched Idaho's PRIMARY offices ('... ST REP A DEMOCRATIC'), which the general-election
    # filter happened to exclude downstream -- a predicate that is only safe because of where
    # it is called is the thing this file exists to stop.
    "ID": ("(REGEXP_MATCHES(r.office, '^LEGISLATIVE DISTRICT [0-9]+ ST REP [AB]$')"
           " OR REGEXP_MATCHES(r.office, '^REPRESENTATIVE DISTRICT [0-9]+ SEAT [AB]$'))"),
}


def lower_chamber_cycle_competitiveness(
    states: list[tuple[str, str]] | None = None,
) -> dict[tuple[str, int, int], CycleBand]:
    """``{(state, cycle, district_number): CycleBand}`` for each state's lower chamber.

    The state-legislative counterpart of :func:`district_cycle_competitiveness`, and it
    exists for the same reason: ``cross_state_state_money``'s K2 cut banded 2022+2024 money
    with the **2026** state-house forecast, which answers a different question from the one
    the section asks.

    The district number is read from ``races.office`` where the state puts it there and from
    ``race_name`` otherwise: Washington writes ``State Representative Pos. 1`` in ``office``
    with the district only in ``LEGISLATIVE DISTRICT 35 - ...``, so an office-only extraction
    returns WA nothing at all rather than failing loudly.

    Washington is the one wrinkle. Its lower chamber elects **two** representatives per
    district (Position 1 and Position 2) on the same lines, so a district-cycle has two
    contests. They are pooled into one two-party margin here, which is the same convention
    the money side uses — K2 keys receipts on the district, not the position.

    New York's 2024 Assembly general is not in ``precinct_results``; like its congressional
    counterpart it comes from the certified ``ny_downballot_2024`` table.

    Coverage measured 2026-08-16 over the 2022+2024 window: WA, NY and TX have both cycles
    (NY 2024 via the certified table) and Idaho has 2024 only — its pre-2024 legislative
    canvasses are not loaded. Idaho's 2022 cells therefore come back absent, and callers must
    report them rather than silently pooling them into a band.
    """
    import duckdb

    states = states if states is not None else region_states()
    out: dict[tuple[str, int, int], CycleBand] = {}

    for st, f in states:
        pred = _LOWER_CHAMBER_PRED.get(st)
        if pred is None:
            continue
        try:
            c = duckdb.connect(f, read_only=True)
        except Exception:
            continue
        try:
            rows = c.execute(f"""
                SELECT YEAR(e.election_date) AS cycle,
                       CAST(COALESCE(
                         NULLIF(REGEXP_EXTRACT(r.office, 'DISTRICT[ ]+([0-9]+)', 1), ''),
                         REGEXP_EXTRACT(r.race_name, 'DISTRICT[ ]+([0-9]+)', 1)
                       ) AS INTEGER) d,
                       SUM(CASE WHEN {_PARTY_CASE}='D' THEN pr.votes ELSE 0 END),
                       SUM(CASE WHEN {_PARTY_CASE}='R' THEN pr.votes ELSE 0 END),
                       MAX(CASE WHEN {_PARTY_CASE}='D' THEN 1 ELSE 0 END),
                       MAX(CASE WHEN {_PARTY_CASE}='R' THEN 1 ELSE 0 END)
                FROM races r
                JOIN elections e ON e.election_id = r.election_id
                JOIN candidates cd ON cd.race_id = r.race_id
                JOIN precinct_results pr ON pr.candidate_id = cd.candidate_id
                WHERE e.election_type = 'general' AND {pred}
                  AND COALESCE(cd.is_writein, FALSE) = FALSE
                  AND COALESCE(
                        NULLIF(REGEXP_EXTRACT(r.office, 'DISTRICT[ ]+([0-9]+)', 1), ''),
                        REGEXP_EXTRACT(r.race_name, 'DISTRICT[ ]+([0-9]+)', 1)) <> ''
                GROUP BY 1, 2""").fetchall()
            certified = []
            if st == "NY":
                try:
                    certified = c.execute(
                        "SELECT district_id, dem_two_party_pct FROM ny_downballot_2024 "
                        "WHERE office='assembly'").fetchall()
                except Exception:
                    certified = []
        finally:
            c.close()

        for cycle, dist, d_v, r_v, has_d, has_r in rows:
            if dist is None:
                continue
            total = float(d_v) + float(r_v)
            if not (has_d and has_r) or total <= 0:
                out[(st, int(cycle), int(dist))] = CycleBand(None, NO_MAJOR_CHOICE, "observed")
            else:
                m = 100.0 * (float(d_v) - float(r_v)) / total
                out[(st, int(cycle), int(dist))] = CycleBand(m, band(abs(m)), "observed")

        for did, pct in certified:
            try:
                dist = int(str(did).lstrip("ad") or "0")
            except ValueError:
                continue
            m = 2.0 * float(pct) - 100.0
            out[(st, 2024, dist)] = CycleBand(m, band(abs(m)), "certified")

    return out


def _id_legislative_pinned() -> dict[tuple[str, int, int], CycleBand]:
    """Idaho's 2022 state-house bands, from the dated pin.

    The pin stores DEM and REP vote totals rather than a margin, so the band is derived here
    by exactly the rule applied to observed cells — including the important one: a district
    where a major party fielded nobody is ``NoMajorChoice``, never Solid. **17 of Idaho's 35
    districts are in that state in 2022**, which is the single largest reason to keep the
    distinction rather than let a -100 margin read as a blowout.

    Raises if the pin is absent, for the same reason its congressional sibling does.
    """
    import csv

    if not ID_LEG_PIN.exists():
        raise FileNotFoundError(
            f"FATAL: the Idaho state-house canvass fixture is missing ({ID_LEG_PIN}). It is "
            "no longer a band source -- see "
            "id-legislative-general-2022-loaded-under-old-office-name in "
            "docs/reference/source_availability_claims.csv -- but it is the external check that "
            "the loader still reproduces the Secretary of State's own figures. Restore it.")

    out: dict[tuple[str, int, int], CycleBand] = {}
    with open(ID_LEG_PIN, encoding="utf-8") as fh:
        for row in csv.DictReader(r for r in fh if not r.lstrip().startswith("#")):
            key = ("ID", int(row["cycle"]), int(row["district"]))
            d_v, r_v = float(row["dem_votes"]), float(row["rep_votes"])
            if d_v <= 0 or r_v <= 0:
                out[key] = CycleBand(None, NO_MAJOR_CHOICE, "pinned")
                continue
            m = 100.0 * (d_v - r_v) / (d_v + r_v)
            out[key] = CycleBand(m, band(abs(m)), "pinned")
    return out


def _id_pinned_bands() -> dict[tuple[str, int, str], CycleBand]:
    """Idaho's pre-2024 congressional bands, from the dated pin.

    Raises if the pin is absent rather than falling back to a typed constant or to
    silence: two of Idaho's SoS numbers were wrong for months precisely because they
    lived as literals, one of them probed against itself. A row whose margin cell is
    blank is an HONEST hole and lands as ``Unavailable``/``pin_unresolved`` — which the
    consumers report — rather than being guessed.
    """
    import csv

    if not ID_CONG_PIN.exists():
        raise FileNotFoundError(
            f"FATAL: the Idaho congressional margin pin is missing ({ID_CONG_PIN}). "
            "Idaho has only its 2024 general loaded, so the 2018-2022 bands cannot be "
            "derived; they are pinned with a source URL and retrieval date. Restore the "
            "pin rather than typing the margins into a caller.")

    out: dict[tuple[str, int, str], CycleBand] = {}
    with open(ID_CONG_PIN, encoding="utf-8") as fh:
        for row in csv.DictReader(r for r in fh if not r.lstrip().startswith("#")):
            key = ("ID", int(row["cycle"]), row["district_id"])
            raw = (row.get("dem_minus_rep_margin") or "").strip()
            if not raw:
                out[key] = CycleBand(None, UNAVAILABLE, "pin_unresolved")
                continue
            m = float(raw)
            out[key] = CycleBand(m, band(abs(m)), "pinned")
    return out


def write_json(name: str, obj) -> str:
    """Write ``obj`` as JSON to ``reports/<name>``; return the path.

    Replaces the stale per-session scratchpad paths several scripts hardcoded.
    """
    out_dir = REPO_ROOT / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / name
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, default=str)
    return str(out)
