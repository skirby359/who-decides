"""Standalone voter-to-donor matcher — the reproduction path for the donor-class paper.

This is an EXTRACT of ``match_voters_to_donors`` from the private product codebase
(``src/wa_analyzer/analysis/donor_analysis.py``), bundled here so the donor panels can be
rebuilt from raw data without shipping the whole product. The function body below is
verbatim; only two lazy internal imports were replaced — the two ``contributor_type``
helpers are defined in this file instead of imported, and the automatic ``vrdb`` ATTACH
fallback (which read a private settings module) is now an explicit error telling the caller
to ATTACH it themselves.

WHAT IT DOES
------------
Joins ``individual_contributions`` (contributor name + ZIP) to ``vrdb.voters`` across four
match tiers, strictest first. Every tier requires its key to resolve to EXACTLY ONE voter
on the roll AND exactly one contributor identity; anything ambiguous is dropped rather than
guessed:

    rank  label               key
    0     STRICT_ZIP5_FULL    surname + FULL first name + ZIP5   <- primary specification
    1     STRICT_ZIP5_MID     surname + first initial + middle initial + ZIP5
    2     STRICT_ZIP5         surname + first initial + ZIP5
    3     RELAXED_ZIP3_MID    surname + first initial + middle initial + ZIP3

Pass ``tiers=PRIMARY_TIERS`` to reproduce the published panels. A stratified blinded rating
of 480 matched records measured rank 0 at 100% precision (120/120, Wilson [96.9-100])
against 47.9-71.7% for ranks 1-3, and every one of the 129 confirmed household/relative
false merges landed on an initial-based key — none on the full-name key. An independent
human re-rating of 150 of those records agreed on 75 of 75 rank-0 rows (Cohen's kappa 0.815
binary overall; all 18 divergences on initial-based keys). See Appendix F of
``docs/donor-class-and-the-electorate.md``.

Ranks are ABSOLUTE. Never renumber them to 0..N-1 for a restricted call — a ``tiers=[3]``
panel would then be labelled ``STRICT_ZIP5_FULL``, corrupting exactly the provenance this
specification exists to establish.

TWO NON-EQUIVALENT MEANINGS OF "FULL-NAME ONLY"
-----------------------------------------------
``tiers=`` restricts which tier JOINS FIRE, so a contribution reachable only by a weaker key
is dropped entirely. That is NOT the same as filtering an all-tier panel on
``match_quality``, which keeps a rank-0 voter's whole dollar total including gifts that
matched on a weak key. Both give IDENTICAL donor counts; dollars differ by 3.8-9.4% across
the six panels. The published figures use this function's semantics. Never move a dollar
figure between the two.

USAGE
-----
    import duckdb
    from donor_matcher import PRIMARY_TIERS, ensure_schema, match_voters_to_donors

    con = duckdb.connect("data/wa_statewide.duckdb")
    con.execute("ATTACH 'data/wa_vrdb.duckdb' AS vrdb (READ_ONLY)")
    ensure_schema(con)
    res = match_voters_to_donors(
        con,
        source_prefixes=["FEC"],                        # None = every money system pooled
        output_table="voter_donor_affiliation_fec",
        tiers=list(PRIMARY_TIERS),
    )

Requires ``individual_contributions`` and ``candidate_finance`` already populated in the
connected database, and the voter file ATTACHed as ``vrdb``. ``ensure_schema`` creates only
what the matcher itself needs — it does NOT create those two input tables. Neither the
voter files nor the panels are redistributable; see
``docs/data-sources-and-reproducibility.md`` for how to obtain each input.
"""
from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Identifier guards for the interpolated table name, contribution_id prefixes and date
# bounds. DuckDB cannot parameterize an identifier, nor a LIKE pattern assembled from one,
# so these are validated rather than bound.
_SAFE_TABLE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_SAFE_PREFIX_RE = re.compile(r"^[A-Za-z0-9_]+$")
_SAFE_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

_ALL_TIER_RANKS = (0, 1, 2, 3)

#: The paper's primary specification: the full-first-name key alone.
PRIMARY_TIERS = (0,)


# ---------------------------------------------------------------------------
# contributor_type — the organisation filter, taken from each source's REAL
# entity-type field rather than guessed from the contributor's name
# ---------------------------------------------------------------------------
CONTRIBUTOR_TYPE_PERSON = "PERSON"
CONTRIBUTOR_TYPE_ORGANIZATION = "ORGANIZATION"
CONTRIBUTOR_TYPE_COMMITTEE = "COMMITTEE"
CONTRIBUTOR_TYPE_UNKNOWN = "UNKNOWN"

#: Values KNOWN not to be a natural person. The matcher excludes these and KEEPS everything
#: else, including UNKNOWN and NULL — the rule is "exclude known organisations", not "keep
#: known persons". Idaho Sunshine leaves ~8% of rows blank-typed; dropping those would
#: discard many real people to remove a handful of organisations. NULL means "never
#: backfilled"; UNKNOWN means "the source said nothing".
CONTRIBUTOR_TYPE_KNOWN_ORG_VALUES: tuple[str, ...] = (
    CONTRIBUTOR_TYPE_ORGANIZATION,
    CONTRIBUTOR_TYPE_COMMITTEE,
)


def contributor_type_person_sql(alias: str = "ic") -> str:
    """SQL predicate selecting contributors that are NOT known organisations.

    The single place these semantics are defined. The ``COALESCE`` is load-bearing, not
    defensive noise: written as the obvious ``contributor_type NOT IN (...)``, SQL
    three-valued logic evaluates the predicate to NULL for every NULL-typed row, and
    ``WHERE`` treats NULL as false — silently DROPPING every unknown row and inverting the
    intended "keep unknowns" behaviour, with no error and no symptom beyond a smaller
    match count. Locked in by ``test_null_type_rows_are_kept``.
    """
    vals = ", ".join(f"'{v}'" for v in CONTRIBUTOR_TYPE_KNOWN_ORG_VALUES)
    col = f"{alias}.contributor_type" if alias else "contributor_type"
    return f"COALESCE({col}, '{CONTRIBUTOR_TYPE_UNKNOWN}') NOT IN ({vals})"


def ensure_contributor_type_column(conn) -> None:
    """Idempotently add ``individual_contributions.contributor_type``.

    Called from ``init_schema`` and also directly by the writers that connect with a bare
    ``duckdb.connect`` and never run the full schema init — the NY contribution loader, the
    Idaho Sunshine adapter's insert path (which uses ``INSERT ... BY NAME`` and would raise
    a Binder Error the moment its frame carries the new key), and the voter-donor matcher.
    Same reason ``ensure_voter_scores_preference_columns`` exists as a named helper.

    Additive only: ``ALTER TABLE ... ADD COLUMN`` on a table nothing FK-references. Never
    rebuild ``individual_contributions`` via CREATE TABLE AS — that would drop the
    ``contribution_id`` PRIMARY KEY every loader relies on for ``INSERT OR REPLACE``, and
    they would silently start appending duplicates instead of upserting.
    """
    try:
        cols = {
            r[0] for r in conn.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'individual_contributions'"
            ).fetchall()
        }
    except Exception:
        return
    if cols and "contributor_type" not in cols:
        conn.execute(
            "ALTER TABLE individual_contributions ADD COLUMN contributor_type VARCHAR"
        )


_CONTRIBUTOR_TYPE_PERSON_BY_CONSTRUCTION: dict[str, str] = {
    "FEC:": "fec.py bulk loader filters WHERE entity_tp = 'IND'",
    "PDC:": "pdc.py filters contributor_category = 'Individual'",
    "NY:":  "ny_finance.py filters CNTRBR_TYPE_DESC = 'INDIVIDUAL'",
}

_CONTRIBUTOR_TYPE_UNPREFIXED_IS_PERSON = "contribution_id NOT LIKE '%:%'"


def backfill_contributor_type(conn) -> dict[str, Any]:
    """Populate ``contributor_type`` for rows loaded before the column existed.

    Uses an explicit prefix ALLOWLIST rather than a negative rule. A negative rule
    (``NOT LIKE 'SUNSHINE:%'``) would also label any FUTURE unfiltered source as PERSON,
    silently; an unrecognized prefix here simply stays NULL and is reported in
    ``unresolved_by_prefix``. That costs one dict entry per new source and is the safer
    half of the trade.

    Idaho Sunshine is deliberately absent: it applies no person filter at load, so its
    per-row type is only recoverable by re-reading the source. Its rows stay NULL — which
    the vocabulary renders as "never backfilled" — until that reload happens.

    Every UPDATE carries ``AND contributor_type IS NULL``, so a second run matches zero
    rows and existing values are never overwritten. Deliberately NOT called from
    ``init_schema``: that runs at the top of ~40 CLI commands, and a multi-million-row
    UPDATE firing inside an unrelated ``report`` invocation is the wrong ergonomics.
    """
    ensure_contributor_type_column(conn)
    out: dict[str, Any] = {"updated_by_rule": {}}
    for prefix, why in _CONTRIBUTOR_TYPE_PERSON_BY_CONSTRUCTION.items():
        n = conn.execute(
            f"SELECT COUNT(*) FROM individual_contributions "
            f"WHERE contributor_type IS NULL AND contribution_id LIKE '{prefix}%'"
        ).fetchone()[0]
        if n:
            conn.execute(
                f"UPDATE individual_contributions "
                f"SET contributor_type = '{CONTRIBUTOR_TYPE_PERSON}' "
                f"WHERE contributor_type IS NULL AND contribution_id LIKE '{prefix}%'"
            )
        out["updated_by_rule"][prefix] = {"rows": int(n), "why": why}
    n_unpref = conn.execute(
        f"SELECT COUNT(*) FROM individual_contributions "
        f"WHERE contributor_type IS NULL AND {_CONTRIBUTOR_TYPE_UNPREFIXED_IS_PERSON}"
    ).fetchone()[0]
    if n_unpref:
        conn.execute(
            f"UPDATE individual_contributions "
            f"SET contributor_type = '{CONTRIBUTOR_TYPE_PERSON}' "
            f"WHERE contributor_type IS NULL "
            f"AND {_CONTRIBUTOR_TYPE_UNPREFIXED_IS_PERSON}"
        )
    out["updated_by_rule"]["<no prefix>"] = {
        "rows": int(n_unpref),
        "why": "fec.py API loaders filter &is_individual=true",
    }
    out["unresolved_by_prefix"] = {
        (p or "<no prefix>"): int(n) for p, n in conn.execute(
            "SELECT SPLIT_PART(contribution_id, ':', 1) || ':', COUNT(*) "
            "FROM individual_contributions WHERE contributor_type IS NULL "
            "GROUP BY 1 ORDER BY 2 DESC"
        ).fetchall()
    }
    out["by_type"] = {
        (t or "NULL"): int(n) for t, n in conn.execute(
            "SELECT contributor_type, COUNT(*) FROM individual_contributions "
            "GROUP BY 1 ORDER BY 2 DESC"
        ).fetchall()
    }
    out["unknown_type_rows"] = out["by_type"].get(CONTRIBUTOR_TYPE_UNKNOWN, 0)
    return out


def ensure_schema(conn) -> None:
    """Create only the tables this matcher needs, if they do not already exist.

    A deliberately minimal subset of the product schema: the canonical output table (whose
    shape every named panel table is cloned from), the conduit-PAC party override that the
    party split COALESCEs over, and the ``contributor_type`` column. It does NOT create
    ``individual_contributions`` or ``candidate_finance`` — those come from the data loaders
    and must already be populated.
    """
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS voter_donor_affiliation (
            state_voter_id      VARCHAR PRIMARY KEY,
            donor_party         VARCHAR,
            donation_count      INTEGER,
            total_donated       DECIMAL(12,2),
            last_donation_date  DATE,
            match_quality       VARCHAR,
            d_amount            DECIMAL(12,2),
            r_amount            DECIMAL(12,2),
            donation_lean       DECIMAL(5,3)
        );
        """
    )
    # Conduit PACs (ActBlue / WinRed and similar) that the FEC tags as nonpartisan; the
    # party split reads this in preference to the committee's own party code. Empty is
    # fine — the matcher LEFT JOINs it — but the table must exist for the join to parse.
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS committee_party_override (
            fec_candidate_id  VARCHAR PRIMARY KEY,
            party             VARCHAR NOT NULL,
            committee_name    VARCHAR,
            source            VARCHAR DEFAULT 'manual',
            notes             VARCHAR,
            added_at          TIMESTAMP DEFAULT current_timestamp,
            CHECK (party IN ('Democratic', 'Republican'))
        );
        """
    )
    ensure_contributor_type_column(conn)


def match_voters_to_donors(
    conn,
    *,
    source_prefixes: list[str] | None = None,
    output_table: str = "voter_donor_affiliation",
    date_min: str | None = None,
    date_max: str | None = None,
    tiers: list[int] | tuple[int, ...] | None = None,
    persons_only: bool = True,
) -> dict[str, Any]:
    """Match itemized individual contributions to VRDB voters.

    Joins ``individual_contributions`` (contributor name + ZIP) to
    ``vrdb.voters`` (must already be ATTACHed) on
    ``(last_name, first_initial, zip5)``. The match is intentionally
    conservative — when the (last, first_initial, zip5) key resolves to
    multiple voters we record nothing (don't guess between siblings).

    For each matched voter, all of their contributions are aggregated
    into a single ``voter_donor_affiliation`` row with D/R splits and a
    ``donation_lean`` in [-1, +1].

    All heavy work runs in DuckDB via temp tables — pulling 5M voters
    into Python takes minutes; the SQL join takes seconds.

    MONEY-SOURCE SCOPING (``source_prefixes``, added 2026-07-26). A state's
    ``individual_contributions`` can hold more than one money system, keyed by the
    ``contribution_id`` prefix: WA carries both ``FEC:`` (federal) and ``PDC:``
    (state) rows, and ID carries both ``FEC:`` and ``SUNSHINE:`` (state) rows since
    the 2026-07-19 ID FEC load. Unscoped, this function pools them, so one person's
    federal and state giving stack into a single donor total — which inflates
    measured concentration relative to either layer alone. Pass e.g.
    ``source_prefixes=["FEC"]`` to build a single-layer panel, and ``output_table``
    to keep panels side by side. **Both default to the historical behavior**
    (all sources -> ``voter_donor_affiliation``) because the campaign tooling
    (``donor_prospects``, segments, walk lists) reads that table and assumes one row
    per voter. See ``docs/donor-class-and-the-electorate.md`` for the panel design.

    CONTRIBUTION WINDOW (``date_min`` / ``date_max``, added 2026-07-27). The two money
    systems in a state do not cover the same years: Idaho Sunshine holds 2023-2025 while
    the FEC layer holds 2017-2026, so an unwindowed federal-vs-state panel comparison
    confounds the regulatory difference with a decade-vs-three-years difference in
    election portfolio. Pass a window to build **period-aligned** panels for that
    comparison. Both default to ``None`` (no date filter), preserving prior behavior;
    rows with a NULL ``contribution_date`` are dropped whenever either bound is set,
    since they cannot be placed in the window. See the temporal-alignment section of
    ``docs/donor-class-and-the-electorate.md`` Appendix C.

    MATCH-TIER SELECTION (``tiers``, added 2026-07-27). Precision is a property of the
    match KEY, not of the panel. A stratified blinded rating of 480 matched records found
    rank 0 (full first name + surname + ZIP5) at **100%** precision — 120/120, Wilson
    95% [96.9-100.0] — against 71.7% / 47.9% / 50.4% for ranks 1/2/3, with **all 129
    household-or-relative false merges landing on an initial-based key and none on the
    full-name key**. ``tiers=[0]`` is therefore the precision-first specification and is
    what the paper and the pooled table now use; see ``PRIMARY_TIERS``.

    Note this restricts which tier joins FIRE, so a contribution that only matches on a
    weak key is dropped entirely. That is deliberate and is *not* the same as filtering a
    built panel on ``match_quality``: the latter keeps a rank-0 voter's whole dollar total
    including weak-key gifts. Both yield identical donor counts, but on WA federal the
    dollar totals differ $346.32M vs $375.26M (7.71%). Restricting the match is the
    honest reading — every dollar then traces to the validated key.

    ``None`` (default) runs all four ranks, preserving the historical contract.

    ORGANISATION EXCLUSION (``persons_only``, added 2026-07-27). Reads the PERSISTED
    ``individual_contributions.contributor_type`` column, populated from each source's real
    entity-type field — not a name heuristic. Semantics: exclude *known* organisations,
    KEEP unknown and NULL. Idaho Sunshine is the only source carrying non-person rows (it
    applies no person filter at load, and 14 of the 152 confirmed false matches in the
    480-record validation were Sunshine organisations parsed as people); those rows stay in
    the table, because Appendix G's all-filers cut is computed over the whole layer, and
    are filtered here at match time instead. Defaults to ``True``: an organisation cannot
    legitimately appear on a voter roll, so a matched organisation is a false positive by
    definition. ``persons_only=False`` is for Appendix-G-style diagnostics, never a
    publishable panel.

    Args:
        conn: Open DuckDB connection. ``vrdb.voters`` must be ATTACHed.
        source_prefixes: Optional list of ``contribution_id`` prefixes to restrict
            the match to (e.g. ``["FEC"]``, ``["PDC"]``, ``["SUNSHINE"]``). ``None``
            (default) matches every contribution, whatever its source.
        output_table: Table to write the aggregated rows into. Defaults to the
            canonical ``voter_donor_affiliation``; any other name is created on
            demand with the same schema.
        date_min: Optional inclusive lower bound on ``contribution_date``
            (``'YYYY-MM-DD'``). ``None`` (default) applies no lower bound.
        date_max: Optional inclusive upper bound on ``contribution_date``
            (``'YYYY-MM-DD'``). ``None`` (default) applies no upper bound.
        tiers: Optional match-tier ranks to run — a non-empty subset of ``{0, 1, 2, 3}``
            (see ``_ALL_TIER_RANKS`` for the key each rank uses). ``None`` (default) runs
            all four. Ranks are absolute, so ``tiers=[3]`` still labels its matches
            ``RELAXED_ZIP3_MID``. Pass ``PRIMARY_TIERS`` for a publishable panel.
        persons_only: When ``True`` (default), skip contributions whose
            ``contributor_type`` is a known organisation or political committee. Rows with
            an unknown or NULL type are KEPT. ``False`` admits everything, for diagnostics.

    Returns:
        Dict with ``skipped`` (true if no contribution rows or no voters
        attached), ``matched_voters``, ``contributions_matched``, a
        ``breakdown`` mapping party -> {count, total_donated}, plus the
        ``source_prefixes`` and ``output_table`` actually used.
    """
    if not _SAFE_TABLE_RE.match(output_table):
        raise ValueError(f"unsafe output_table name: {output_table!r}")
    if source_prefixes is not None:
        if not source_prefixes:
            raise ValueError("source_prefixes must be None or a non-empty list")
        for p in source_prefixes:
            if not _SAFE_PREFIX_RE.match(p):
                raise ValueError(f"unsafe contribution_id prefix: {p!r}")
    for _label, _d in (("date_min", date_min), ("date_max", date_max)):
        if _d is not None and not _SAFE_DATE_RE.match(_d):
            raise ValueError(f"{_label} must be 'YYYY-MM-DD', got {_d!r}")
    if date_min and date_max and date_min > date_max:
        raise ValueError(f"date_min {date_min!r} is after date_max {date_max!r}")
    if tiers is None:
        _tier_ranks = list(_ALL_TIER_RANKS)
    else:
        for _t in tiers:
            # `bool` is an int subclass, so reject it explicitly — tiers=[True] would
            # otherwise silently become tier 1.
            if isinstance(_t, bool) or not isinstance(_t, int) \
                    or _t not in _ALL_TIER_RANKS:
                raise ValueError(
                    f"tiers must be a non-empty subset of {set(_ALL_TIER_RANKS)}, "
                    f"got {tiers!r}")
        _tier_ranks = sorted(set(tiers))
        # An empty set skips the loop above, so this is the check that catches it — and
        # it must, because an empty tier list would emit `WITH all_tiers AS ()`, which is
        # a DuckDB parse error rather than a clean no-op.
        if not _tier_ranks:
            raise ValueError(
                f"tiers must be None or a non-empty subset of {set(_ALL_TIER_RANKS)}")
    try:
        contrib_count = conn.execute(
            "SELECT COUNT(*) FROM individual_contributions"
        ).fetchone()[0]
    except Exception:
        return {"skipped": True, "reason": "individual_contributions table missing"}

    if contrib_count == 0:
        return {"skipped": True, "reason": "no individual contributions loaded"}

    # Attach vrdb if it isn't already — the analyze pipeline runs
    # compute_voter_scores earlier which detaches in its finally block.
    try:
        conn.execute("SELECT 1 FROM vrdb.voters LIMIT 1").fetchone()
    except Exception:
        return {"skipped": True, "reason":
                "vrdb.voters is not attached. ATTACH the voter-file DuckDB as `vrdb` "
                "before calling this function, e.g. "
                "conn.execute(\"ATTACH 'data/wa_vrdb.duckdb' AS vrdb (READ_ONLY)\")."}

    try:
        voter_count = conn.execute(
            "SELECT COUNT(*) FROM vrdb.voters"
        ).fetchone()[0]
    except Exception:
        return {"skipped": True, "reason": "vrdb.voters not accessible"}

    if voter_count == 0:
        return {"skipped": True, "reason": "no voters in attached vrdb"}

    # ===== Four-tier match design =====
    #
    # Real donors use different ZIPs for different recipients (home vs
    # work, P.O. box vs mailing). Strict ZIP5 was too conservative — e.g.
    # Stephen T. Kirby gives to WSAJ via his work zip (99201) and to
    # SCDCC via his home zip (99202); pre-fix only the 99202 gifts
    # matched his voter row.
    #
    # Each tier requires UNIQUENESS at its (key) granularity to avoid
    # mismatching siblings/relatives. Ranks are strictest first and are
    # ABSOLUTE — see `_ALL_TIER_RANKS`, which is the single definition:
    #
    #   0 STRICT_ZIP5_FULL : last + FULL first name + zip5
    #   1 STRICT_ZIP5_MID  : last + first_initial + middle_initial + zip5
    #   2 STRICT_ZIP5      : last + first_initial + zip5
    #   3 RELAXED_ZIP3_MID : last + first_initial + middle_initial + zip3
    #
    # Rank 3 only fires when BOTH sides have a middle initial — that's
    # the disambiguator that lets us safely widen the geographic radius.
    # We never relax to zip3-without-middle (too many same-named people
    # in the same metro area).
    #
    # The ranks are NOT interchangeable. Blinded validation puts rank 0 at 100%
    # precision and ranks 1-3 at 47.9-71.7%, so `tiers=` exists to build a
    # rank-0-only panel; each key build below is skipped when its rank is out
    # of scope, which is a pure speed win (three 5M-row GROUP BY ... HAVING
    # scans of vrdb.voters avoided).

    # Build the voter-key lookups, one per requested tier.
    if 1 in _tier_ranks:
        conn.execute("""
            CREATE OR REPLACE TEMP TABLE _voter_keys_zip5_mid AS
            SELECT last_upper, first_initial, middle_initial, zip5,
                   ANY_VALUE(state_voter_id) AS state_voter_id
            FROM (
                SELECT
                    state_voter_id,
                    UPPER(TRIM(last_name))                          AS last_upper,
                    UPPER(SUBSTR(TRIM(first_name), 1, 1))           AS first_initial,
                    UPPER(SUBSTR(TRIM(middle_name), 1, 1))          AS middle_initial,
                    SUBSTR(reg_zip, 1, 5)                           AS zip5
                FROM vrdb.voters
                WHERE status_code = 'A'
                  AND first_name  IS NOT NULL
                  AND last_name   IS NOT NULL
                  AND middle_name IS NOT NULL
                  AND TRIM(middle_name) != ''
                  AND reg_zip     IS NOT NULL
            )
            GROUP BY last_upper, first_initial, middle_initial, zip5
            HAVING COUNT(*) = 1
        """)

    if 2 in _tier_ranks:
        conn.execute("""
            CREATE OR REPLACE TEMP TABLE _voter_keys_zip5 AS
            SELECT last_upper, first_initial, zip5,
                   ANY_VALUE(state_voter_id) AS state_voter_id
            FROM (
                SELECT
                    state_voter_id,
                    UPPER(TRIM(last_name))                AS last_upper,
                    UPPER(SUBSTR(TRIM(first_name), 1, 1)) AS first_initial,
                    SUBSTR(reg_zip, 1, 5)                 AS zip5
                FROM vrdb.voters
                WHERE status_code = 'A'
                  AND first_name IS NOT NULL
                  AND last_name  IS NOT NULL
                  AND reg_zip    IS NOT NULL
            )
            GROUP BY last_upper, first_initial, zip5
            HAVING COUNT(*) = 1
        """)

    if 3 in _tier_ranks:
        conn.execute("""
            CREATE OR REPLACE TEMP TABLE _voter_keys_zip3_mid AS
            SELECT last_upper, first_initial, middle_initial, zip3,
                   ANY_VALUE(state_voter_id) AS state_voter_id
            FROM (
                SELECT
                    state_voter_id,
                    UPPER(TRIM(last_name))                          AS last_upper,
                    UPPER(SUBSTR(TRIM(first_name), 1, 1))           AS first_initial,
                    UPPER(SUBSTR(TRIM(middle_name), 1, 1))          AS middle_initial,
                    SUBSTR(reg_zip, 1, 3)                           AS zip3
                FROM vrdb.voters
                WHERE status_code = 'A'
                  AND first_name  IS NOT NULL
                  AND last_name   IS NOT NULL
                  AND middle_name IS NOT NULL
                  AND TRIM(middle_name) != ''
                  AND reg_zip     IS NOT NULL
            )
            GROUP BY last_upper, first_initial, middle_initial, zip3
            HAVING COUNT(*) = 1
        """)

    # Full-first-name key (more unique than first-initial): resolves donors
    # whose (last, first_initial, zip5) collides with a sibling/relative but
    # whose full first name is unique in the ZIP.
    if 0 in _tier_ranks:
        conn.execute("""
            CREATE OR REPLACE TEMP TABLE _voter_keys_zip5_full AS
            SELECT last_upper, first_full, zip5,
                   ANY_VALUE(state_voter_id) AS state_voter_id
            FROM (
                SELECT
                    state_voter_id,
                    UPPER(TRIM(last_name))  AS last_upper,
                    UPPER(TRIM(first_name)) AS first_full,
                    SUBSTR(reg_zip, 1, 5)   AS zip5
                FROM vrdb.voters
                WHERE status_code = 'A'
                  AND first_name IS NOT NULL
                  AND last_name  IS NOT NULL
                  AND reg_zip    IS NOT NULL
            )
            GROUP BY last_upper, first_full, zip5
            HAVING COUNT(*) = 1
        """)

    # Materialize candidate_finance dedup'd once as a TEMP TABLE so the
    # contribution-key build doesn't redo the GROUP BY for every row.
    # The original inline subquery form scaled badly once
    # candidate_finance grew from 1.5K rows (FEC-only) to 107K rows
    # (after the PDC committee stubs + FEC committee master load):
    # an earlier May 20 matcher run on 8.6M contribution rows did not
    # finish in 4+ hours and burned 46 CPU-hours before being killed.
    #
    # COALESCE'd against committee_party_override so manually-classified
    # conduit PACs (ActBlue, WinRed, party-affiliated joint-fundraising
    # vehicles) override FEC's frequently-blank CMTE_PTY_AFFILIATION.
    # See [[donor-prospects]] for the OTHER-bucket investigation.
    conn.execute("""
        CREATE OR REPLACE TEMP TABLE _cf_dedup AS
        WITH cf_one AS (
            SELECT fec_candidate_id, ANY_VALUE(party) AS party
            FROM candidate_finance
            GROUP BY fec_candidate_id
        )
        SELECT cf.fec_candidate_id,
               COALESCE(ov.party, cf.party) AS party
        FROM cf_one cf
        LEFT JOIN committee_party_override ov USING (fec_candidate_id)
    """)

    # Parse contributor names into match keys; keep `contribution_id` so
    # we can dedupe by it across the three tier passes (see _matched_contribs).
    #
    # `_source_sql` is the single point where money-source scoping applies: every
    # tier below reads _contrib_keys, so filtering here scopes the whole match.
    if source_prefixes:
        _ors = " OR ".join(
            f"ic.contribution_id LIKE '{p}:%'" for p in source_prefixes
        )
        _source_sql = f"AND ({_ors})"
    else:
        _source_sql = ""

    # `_window_sql` scopes the match to a contribution-date window (see the
    # CONTRIBUTION WINDOW note in the docstring). Literals are safe: both bounds
    # are regex-validated as YYYY-MM-DD above. A NULL contribution_date cannot be
    # placed in a window, so those rows drop out as soon as either bound is set.
    _window_parts = []
    if date_min:
        _window_parts.append(f"ic.contribution_date >= DATE '{date_min}'")
    if date_max:
        _window_parts.append(f"ic.contribution_date <= DATE '{date_max}'")
    _window_sql = (
        "AND " + " AND ".join(_window_parts) if _window_parts else ""
    )

    # Organisation exclusion, applied here in `_contrib_keys` so all four tiers inherit it
    # from a single point — the same property the `_source_sql` note above documents. The
    # aggregator-name list below is NOT made redundant by this: PDC files its unitemized
    # pseudo-contributor under contributor_category='Individual', so it arrives typed
    # PERSON and only the name list catches it.
    if persons_only:
        # Defined at the top of THIS module rather than imported from the product
        # codebase, so this file stands alone.
        # The matcher is read-write by construction (it writes output_table), and several
        # callers connect with a bare duckdb.connect and never run init_schema.
        ensure_contributor_type_column(conn)
        _person_sql = f"AND {contributor_type_person_sql('ic')}"
    else:
        _person_sql = ""
    conn.execute(f"""
        CREATE OR REPLACE TEMP TABLE _contrib_keys AS
        SELECT
            ic.contribution_id,
            CASE
                WHEN ic.contributor_name LIKE '%,%'
                THEN UPPER(TRIM(SPLIT_PART(ic.contributor_name, ',', 1)))
                ELSE UPPER(TRIM(SPLIT_PART(TRIM(ic.contributor_name), ' ', 1)))
            END AS last_upper,
            CASE
                WHEN ic.contributor_name LIKE '%,%'
                THEN UPPER(SUBSTR(TRIM(SPLIT_PART(ic.contributor_name, ',', 2)), 1, 1))
                ELSE UPPER(SUBSTR(TRIM(SPLIT_PART(TRIM(ic.contributor_name), ' ', 2)), 1, 1))
            END AS first_initial,
            CASE
                WHEN ic.contributor_name LIKE '%,%'
                THEN UPPER(SPLIT_PART(TRIM(SPLIT_PART(ic.contributor_name, ',', 2)), ' ', 1))
                ELSE UPPER(SPLIT_PART(TRIM(ic.contributor_name), ' ', 2))
            END AS first_full,
            CASE
                WHEN ic.contributor_name LIKE '%,%'
                THEN UPPER(SUBSTR(
                    SPLIT_PART(TRIM(SPLIT_PART(ic.contributor_name, ',', 2)), ' ', 2),
                    1, 1))
                ELSE UPPER(SUBSTR(SPLIT_PART(TRIM(ic.contributor_name), ' ', 3), 1, 1))
            END AS middle_initial,
            SUBSTR(ic.contributor_zip, 1, 5) AS zip5,
            SUBSTR(ic.contributor_zip, 1, 3) AS zip3,
            ic.contribution_amount,
            ic.contribution_date,
            COALESCE(cf.party, 'Unknown')    AS party
        FROM individual_contributions ic
        LEFT JOIN _cf_dedup cf
            ON cf.fec_candidate_id = ic.fec_candidate_id
        WHERE ic.contributor_name IS NOT NULL
          AND ic.contributor_name <> ''
          AND ic.contributor_zip  IS NOT NULL
          AND ic.contributor_zip  <> ''
          AND UPPER(ic.contributor_name) NOT IN
              ('SMALL CONTRIBUTIONS', 'UNITEMIZED', 'ANONYMOUS')
          {_source_sql}
          {_window_sql}
          {_person_sql}
    """)

    # ===== Three-tier match: INNER JOIN per tier into UNION ALL =====
    #
    # Each tier produces matched-contribution rows independently via
    # INNER JOIN (smaller intermediate results than LEFT JOIN, lets
    # DuckDB hash-build on the smaller voter-key table each time). The
    # three results UNION ALL together; a window function then picks
    # the strictest tier per contribution_id so we don't double-count
    # rows that match multiple tiers (a contrib with middle initial T
    # against a voter with middle initial T matches both ZIP5+MID and
    # plain ZIP5).
    #
    # This replaced the COALESCE'd 3-way LEFT JOIN that DuckDB couldn't
    # plan efficiently once contrib rows × cf rows × voter rows reached
    # 8.6M × 107K × 5M scale.
    # `_tier_bodies` is the tier-restriction seam — same f-string interpolation idiom as
    # `_source_sql` / `_window_sql` above. Only the requested ranks are UNION ALL'd, which
    # is what makes `tiers=[0]` genuinely skip three joins rather than compute them and
    # throw the rows away. `str.join` over N>=1 items emits exactly N-1 separators, so a
    # dangling UNION ALL is structurally impossible; the non-empty invariant comes from
    # the `tiers` validation above.
    _tier_bodies = {
        0: """
            -- Tier 0: full first name + zip5 (most precise; resolves cases
            -- where the first initial alone collides with a relative)
            SELECT ck.contribution_id, ck.contribution_amount,
                   ck.contribution_date, ck.party,
                   v.state_voter_id, 0 AS tier_rank
            FROM _contrib_keys ck
            JOIN _voter_keys_zip5_full v
                 ON v.last_upper = ck.last_upper
                AND v.first_full = ck.first_full
                AND v.zip5       = ck.zip5
            WHERE LENGTH(ck.first_full) >= 2
""",
        1: """
            -- Tier 1: zip5 + middle initial (strictest initial-based)
            SELECT ck.contribution_id, ck.contribution_amount,
                   ck.contribution_date, ck.party,
                   v.state_voter_id, 1 AS tier_rank
            FROM _contrib_keys ck
            JOIN _voter_keys_zip5_mid v
                 ON v.last_upper     = ck.last_upper
                AND v.first_initial  = ck.first_initial
                AND v.middle_initial = ck.middle_initial
                AND v.zip5           = ck.zip5
            WHERE ck.middle_initial != ''
""",
        2: """
            -- Tier 2: zip5 alone (no middle disambiguator)
            SELECT ck.contribution_id, ck.contribution_amount,
                   ck.contribution_date, ck.party,
                   v.state_voter_id, 2 AS tier_rank
            FROM _contrib_keys ck
            JOIN _voter_keys_zip5 v
                 ON v.last_upper    = ck.last_upper
                AND v.first_initial = ck.first_initial
                AND v.zip5          = ck.zip5
""",
        3: """
            -- Tier 3: zip3 + middle initial (relaxed geographic radius)
            SELECT ck.contribution_id, ck.contribution_amount,
                   ck.contribution_date, ck.party,
                   v.state_voter_id, 3 AS tier_rank
            FROM _contrib_keys ck
            JOIN _voter_keys_zip3_mid v
                 ON v.last_upper     = ck.last_upper
                AND v.first_initial  = ck.first_initial
                AND v.middle_initial = ck.middle_initial
                AND v.zip3           = ck.zip3
            WHERE ck.middle_initial != ''
""",
    }
    _tier_sql = "\n            UNION ALL\n".join(
        _tier_bodies[r] for r in _tier_ranks
    )
    # Everything below is rank-agnostic and needs no change when tiers are restricted:
    # ROW_NUMBER(... ORDER BY tier_rank) degenerates correctly to all-rn=1 on a single
    # branch, and MIN(tier_rank) plus the label CASE are per-rank lookups.
    conn.execute(f"""
        CREATE OR REPLACE TEMP TABLE _matched_contribs AS
        WITH all_tiers AS ({_tier_sql}
        )
        SELECT contribution_id, contribution_amount, contribution_date,
               party, state_voter_id, tier_rank
        FROM (
            SELECT *,
                   ROW_NUMBER() OVER (
                       PARTITION BY contribution_id ORDER BY tier_rank
                   ) AS rn
            FROM all_tiers
        )
        WHERE rn = 1
    """)

    # Aggregate per voter, tracking best (lowest) tier_rank.
    conn.execute("""
        CREATE OR REPLACE TEMP TABLE _matched_donors AS
        SELECT
            state_voter_id,
            COUNT(*)                                                                AS donation_count,
            SUM(contribution_amount)                                                AS total,
            SUM(CASE WHEN party = 'Democratic' THEN contribution_amount ELSE 0 END) AS d_amount,
            SUM(CASE WHEN party = 'Republican' THEN contribution_amount ELSE 0 END) AS r_amount,
            MAX(contribution_date)                                                  AS last_donation_date,
            MIN(tier_rank)                                                          AS best_tier_rank
        FROM _matched_contribs
        GROUP BY state_voter_id
    """)

    matched_contribs = conn.execute(
        "SELECT COALESCE(SUM(donation_count), 0) FROM _matched_donors"
    ).fetchone()[0]

    # 4. Replace the output table's contents (full recompute, not incremental).
    #    Panel tables (anything other than the canonical voter_donor_affiliation,
    #    which db.py pre-creates) are materialized on demand with the same schema.
    if output_table != "voter_donor_affiliation":
        conn.execute(
            f"CREATE TABLE IF NOT EXISTS {output_table} AS "
            "SELECT * FROM voter_donor_affiliation WHERE 1=0"
        )
    conn.execute(f"DELETE FROM {output_table}")
    conn.execute(f"""
        INSERT INTO {output_table} (
            state_voter_id, donor_party, donation_count, total_donated,
            last_donation_date, match_quality, d_amount, r_amount,
            donation_lean
        )
        SELECT
            state_voter_id,
            CASE
                WHEN d_amount > 0 AND r_amount = 0 THEN 'D_DONOR'
                WHEN r_amount > 0 AND d_amount = 0 THEN 'R_DONOR'
                WHEN d_amount > 0 AND r_amount > 0 THEN 'MIXED'
                ELSE                                      'OTHER'
            END                                                              AS donor_party,
            donation_count,
            ROUND(total, 2),
            last_donation_date,
            CASE best_tier_rank
                WHEN 0 THEN 'STRICT_ZIP5_FULL'
                WHEN 1 THEN 'STRICT_ZIP5_MID'
                WHEN 2 THEN 'STRICT_ZIP5'
                WHEN 3 THEN 'RELAXED_ZIP3_MID'
                ELSE        'UNKNOWN'
            END                                                              AS match_quality,
            ROUND(d_amount, 2),
            ROUND(r_amount, 2),
            CASE
                WHEN (d_amount + r_amount) > 0
                THEN ROUND((d_amount - r_amount) / (d_amount + r_amount), 3)
                ELSE 0
            END                                                              AS donation_lean
        FROM _matched_donors
    """)

    # 5. Build the per-party breakdown for the return value.
    breakdown_rows = conn.execute(f"""
        SELECT donor_party, COUNT(*), COALESCE(SUM(total_donated), 0)
        FROM {output_table}
        GROUP BY donor_party
    """).fetchall()
    breakdown: dict[str, dict[str, float]] = {}
    for party, count, total in breakdown_rows:
        breakdown[party] = {
            "count": int(count),
            "total_donated": float(total),
        }

    matched_voters = conn.execute(
        f"SELECT COUNT(*) FROM {output_table}"
    ).fetchone()[0]

    # Clean up temp tables.
    for t in ("_voter_keys_zip5_mid", "_voter_keys_zip5", "_voter_keys_zip5_full",
              "_voter_keys_zip3_mid", "_cf_dedup", "_contrib_keys",
              "_matched_contribs", "_matched_donors"):
        conn.execute(f"DROP TABLE IF EXISTS {t}")

    logger.info(
        "Voter-donor matching: %d voters matched from %d contributions "
        "(sources=%s tiers=%s -> %s).",
        matched_voters, matched_contribs,
        ",".join(source_prefixes) if source_prefixes else "ALL",
        ",".join(str(r) for r in _tier_ranks), output_table,
    )
    return {
        "skipped": False,
        "matched_voters": int(matched_voters),
        "contributions_matched": int(matched_contribs),
        "breakdown": breakdown,
        "source_prefixes": list(source_prefixes) if source_prefixes else None,
        "output_table": output_table,
        "date_min": date_min,
        "date_max": date_max,
        # The EFFECTIVE ranks, not the argument: a default call reports [0,1,2,3] rather
        # than None, because the panel scripts echo this for provenance.
        "tiers": list(_tier_ranks),
        "persons_only": persons_only,
    }


# ---------------------------------------------------------------------------
# Composite political-preference scoring per voter
# ---------------------------------------------------------------------------

# Thresholds for labelling a -1..+1 preference score.
_LABEL_THRESHOLDS = (
    (0.30, "Strong D"),
    (0.10, "Lean D"),
    (-0.10, "Swing"),
    (-0.30, "Lean R"),
)
