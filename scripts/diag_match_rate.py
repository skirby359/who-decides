"""Match rate (recall) of the donor↔voter linkage, per panel.

The donor paper described the matched set as "a floor on identifiable donor–voter matches"
without ever saying how far below the ceiling that floor sits. This computes it, two ways,
for all six published panels:

  * **donor-identity recall** — of the distinct donor identities present in a contribution
    layer, what share resolved to exactly one active registrant. The identity is the
    primary specification's own key, ``(surname, FULL first name, ZIP5)``, built with the
    matcher's exact parsing rules so the denominator and the numerator are commensurable.
    That parsing matters: FEC files people ``LAST, FIRST`` while the WA PDC and Idaho
    Sunshine file them without a comma, and a comma-split denominator collapses those two
    layers to almost nothing.

  * **dollar coverage** — of the layer's itemized individual dollars, what share landed in
    the panel. This needs no identity resolution on the denominator side and is therefore
    the less contestable of the two.

Why both. Recall counts people and is the figure a referee asks for; coverage counts money
and is what the concentration findings actually rest on. They differ, and the direction is
usually informative — matched donors are larger donors, so coverage runs above recall in five
of the six panels. Washington's state panel is the exception, for a reason worth knowing: the
PDC files 99.9% of its contributor names WITHOUT a comma, so the parser takes the first token
as the surname and fails on every filer who wrote "FIRST MIDDLE LAST". That depresses both
columns there, and it is a source-format defect rather than a behavioural difference.

The eligibility filter replicates ``_contrib_keys`` in
``wa_analyzer.analysis.donor_analysis.match_voters_to_donors`` — non-null non-empty name and
ZIP, the three aggregator pseudo-names excluded, and the organisation exclusion in its
COALESCE form so NULL-typed rows are kept rather than silently dropped.

    PYTHONPATH=src python scripts/diag_match_rate.py

Read-only. Writes nothing.
"""
from __future__ import annotations

from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# Kept in step with wa_analyzer.db.CONTRIBUTOR_TYPE_KNOWN_ORG_VALUES. Duplicated rather
# than imported so this script runs without the package on the path, matching the other
# diagnostics; the assertion below fails loudly if the two ever diverge.
KNOWN_ORG = ("ORGANIZATION", "COMMITTEE")
UNKNOWN = "UNKNOWN"

PANELS = [
    # state, db,              source prefix, panel table
    ("WA", "wa_statewide", "FEC", "voter_donor_affiliation_fec"),
    ("WA", "wa_statewide", "PDC", "voter_donor_affiliation_state"),
    ("NY", "ny_statewide", "FEC", "voter_donor_affiliation_fec"),
    ("NY", "ny_statewide", "NY", "voter_donor_affiliation_state"),
    ("ID", "id_statewide", "FEC", "voter_donor_affiliation_fec"),
    ("ID", "id_statewide", "SUNSHINE", "voter_donor_affiliation_state"),
]

# The matcher's donor-side key, verbatim in shape: comma-form is "LAST, FIRST MIDDLE",
# comma-less form is "FIRST MIDDLE LAST" parsed as first-token-is-surname. The second is a
# known defect of the source files rather than of this script — it is why the WA PDC and
# Idaho Sunshine layers admit organisations as "people" on the weaker keys, and it is
# reproduced here on purpose so the denominator counts the same identities the matcher
# could ever have matched.
LAST_SQL = """CASE WHEN contributor_name LIKE '%,%'
                   THEN UPPER(TRIM(SPLIT_PART(contributor_name, ',', 1)))
                   ELSE UPPER(TRIM(SPLIT_PART(TRIM(contributor_name), ' ', 1))) END"""
FIRST_SQL = """CASE WHEN contributor_name LIKE '%,%'
                    THEN UPPER(SPLIT_PART(TRIM(SPLIT_PART(contributor_name, ',', 2)), ' ', 1))
                    ELSE UPPER(SPLIT_PART(TRIM(contributor_name), ' ', 2)) END"""

ELIGIBLE = f"""
    contributor_name IS NOT NULL AND contributor_name <> ''
    AND contributor_zip IS NOT NULL AND contributor_zip <> ''
    AND UPPER(contributor_name) NOT IN
        ('SMALL CONTRIBUTIONS', 'UNITEMIZED', 'ANONYMOUS')
    AND COALESCE(contributor_type, '{UNKNOWN}')
        NOT IN ({", ".join(f"'{v}'" for v in KNOWN_ORG)})
"""

# Residence restriction, and why the headline rate needs it. The two layer types are NOT
# filtered alike at load: the per-state FEC loads filter on donor residence and are 100%
# in-state, while the state-disclosure loads are not — the NYSBOE layer is 23.6%
# out-of-state, WA PDC 5.9% (plus 5.3% with no state at all) and Idaho Sunshine 5.7%
# (plus 8.1%). An out-of-state donor identity cannot match the state's own roll, so an
# unrestricted denominator charges the state panels for identities no linkage could ever
# resolve and makes their recall look worse than the federal panels' for a reason that has
# nothing to do with linkage. The comparable figure restricts every denominator to
# in-state identities; both are reported below.
def in_state(st: str) -> str:
    return f"UPPER(TRIM(contributor_state)) = '{st}'"


def _check_org_list_in_step() -> None:
    """Fail loudly if db.py's organisation list has moved on without this script."""
    try:
        from wa_analyzer.db import (
            CONTRIBUTOR_TYPE_KNOWN_ORG_VALUES, CONTRIBUTOR_TYPE_UNKNOWN,
        )
    except ImportError:
        print("  (wa_analyzer not importable — organisation list not cross-checked)")
        return
    assert tuple(CONTRIBUTOR_TYPE_KNOWN_ORG_VALUES) == KNOWN_ORG, (
        f"db.py now lists {tuple(CONTRIBUTOR_TYPE_KNOWN_ORG_VALUES)}; this script has "
        f"{KNOWN_ORG}. Update KNOWN_ORG or the denominator stops matching the matcher's.")
    assert CONTRIBUTOR_TYPE_UNKNOWN == UNKNOWN


VRDB = {"wa_statewide": "wa_vrdb", "ny_statewide": "ny_vrdb", "id_statewide": "id_vrdb"}


def decompose(con, prefix: str) -> dict:
    """Split the unmatched identities into the two causes that mean different things.

    A donor identity fails to match for one of two reasons, and they are not equivalent:

      * **0 registrants** carry that (surname, full first name, ZIP5). The donor is not on
        the active roll under that name and ZIP — genuinely unregistered, registered in
        another state, inactive or removed, deceased, moved since giving, filing from a work
        rather than home ZIP, or filing a nickname against a legal name on the roll. This is
        a property of the world and of the source files, not of the linkage rule.
      * **2 or more registrants** carry it. The donor is very likely on the roll, and the
        uniqueness guard dropped the record rather than guess between namesakes. This is the
        cost of the design, and it is the only part of the shortfall the rule itself causes.

    Reporting one number without this split invites the reading that the matcher misses half
    the donors it could reach, which the split shows is not what is happening.
    """
    src = f"SPLIT_PART(contribution_id, ':', 1) = '{prefix}'"
    rows = con.execute(f"""
        WITH ids AS (
            SELECT {LAST_SQL} AS last_nm, {FIRST_SQL} AS first_nm,
                   SUBSTR(contributor_zip, 1, 5) AS z5
            FROM individual_contributions
            WHERE {src} AND {ELIGIBLE}
            GROUP BY 1, 2, 3
        ), elig AS (
            SELECT * FROM ids
            WHERE last_nm <> '' AND LENGTH(first_nm) > 1 AND LENGTH(z5) = 5
        ), roll AS (
            SELECT UPPER(TRIM(last_name))  AS last_nm,
                   UPPER(TRIM(first_name)) AS first_nm,
                   SUBSTR(reg_zip, 1, 5)   AS z5,
                   COUNT(*)                AS n_reg
            FROM vrdb.voters
            WHERE status_code = 'A' AND first_name IS NOT NULL
              AND last_name IS NOT NULL AND reg_zip IS NOT NULL
            GROUP BY 1, 2, 3
        )
        SELECT CASE WHEN r.n_reg IS NULL THEN 'none'
                    WHEN r.n_reg = 1     THEN 'unique'
                    ELSE 'ambiguous' END AS bucket,
               COUNT(*) AS n_ids
        FROM elig e LEFT JOIN roll r USING (last_nm, first_nm, z5)
        GROUP BY 1
    """).fetchall()
    return {b: n for b, n in rows}


def panel_rates(con, prefix: str, table: str, st: str) -> dict:
    src = f"SPLIT_PART(contribution_id, ':', 1) = '{prefix}'"

    # Residence-restricted denominators — the comparable ones. See the note on in_state().
    # Identities and dollars are restricted the SAME way so the recall and coverage columns
    # share a basis. Mixing an in-state recall with an all-residence coverage would repeat
    # exactly the mixed-basis defect this paper's own opening sentence carried until it was
    # caught on adversarial re-read.
    amt_instate, = con.execute(f"""
        SELECT SUM(contribution_amount) FROM individual_contributions
        WHERE {src} AND {ELIGIBLE} AND {in_state(st)}
    """).fetchone()
    ids_instate, = con.execute(f"""
        SELECT COUNT(*) FROM (
            SELECT {LAST_SQL} AS last_nm, {FIRST_SQL} AS first_nm,
                   SUBSTR(contributor_zip, 1, 5) AS z5
            FROM individual_contributions
            WHERE {src} AND {ELIGIBLE} AND {in_state(st)}
            GROUP BY 1, 2, 3
        )
        WHERE last_nm <> '' AND LENGTH(first_nm) > 1 AND LENGTH(z5) = 5
    """).fetchone()

    layer_ids, layer_amt = con.execute(f"""
        SELECT COUNT(*), SUM(amt) FROM (
            SELECT {LAST_SQL} AS last_nm, {FIRST_SQL} AS first_nm,
                   SUBSTR(contributor_zip, 1, 5) AS z5,
                   SUM(contribution_amount) AS amt
            FROM individual_contributions
            WHERE {src} AND {ELIGIBLE}
            GROUP BY 1, 2, 3
        )
        WHERE last_nm <> '' AND first_nm <> '' AND LENGTH(z5) = 5
    """).fetchone()

    # Identities the key can never resolve, separated out: a one-character first name
    # cannot satisfy a FULL-first-name key, so counting it in the denominator would
    # understate recall for a reason that has nothing to do with the linkage.
    initial_only, = con.execute(f"""
        SELECT COUNT(*) FROM (
            SELECT {LAST_SQL} AS last_nm, {FIRST_SQL} AS first_nm,
                   SUBSTR(contributor_zip, 1, 5) AS z5
            FROM individual_contributions
            WHERE {src} AND {ELIGIBLE}
            GROUP BY 1, 2, 3
        )
        WHERE last_nm <> '' AND LENGTH(first_nm) = 1 AND LENGTH(z5) = 5
    """).fetchone()

    n_matched, matched_amt = con.execute(
        f"SELECT COUNT(*), SUM(total_donated) FROM {table}").fetchone()

    resolvable = layer_ids - initial_only
    return {
        "ids_instate": ids_instate,
        "recall_instate": 100.0 * n_matched / ids_instate if ids_instate else 0.0,
        "amt_instate": float(amt_instate or 0),
        "coverage_instate": (100.0 * float(matched_amt or 0) / float(amt_instate)
                             if amt_instate else 0.0),
        "layer_ids": layer_ids,
        "initial_only": initial_only,
        "resolvable": resolvable,
        "matched": n_matched,
        "recall_all": 100.0 * n_matched / layer_ids if layer_ids else 0.0,
        "recall_resolvable": 100.0 * n_matched / resolvable if resolvable else 0.0,
        "layer_amt": float(layer_amt or 0),
        "matched_amt": float(matched_amt or 0),
        "coverage": 100.0 * float(matched_amt or 0) / float(layer_amt) if layer_amt else 0.0,
    }


def main() -> None:
    _check_org_list_in_step()
    print("=" * 100)
    print("DONOR-IDENTITY RECALL AND DOLLAR COVERAGE, per published panel")
    print("=" * 100)
    print(f"{'panel':<14}{'resolvable':>12}{'matched':>10}{'recall':>9}"
          f"{'in-state ids':>14}{'recall(IS)':>12}{'in-st $':>12}{'matched $':>12}{'cov(IS)':>8}")
    print("-" * 100)
    out = {}
    for state, db, prefix, table in PANELS:
        path = DATA / f"{db}.duckdb"
        if not path.exists():
            print(f"{state} {prefix:<10}  -- {path.name} absent")
            continue
        con = duckdb.connect(str(path), read_only=True)
        try:
            r = panel_rates(con, prefix, table, state)
            con.execute(f"ATTACH '{DATA / (VRDB[db] + '.duckdb')}' AS vrdb (READ_ONLY)")
            r["split"] = decompose(con, prefix)
        finally:
            con.close()
        key = f"{state}_{'fed' if prefix == 'FEC' else 'state'}"
        out[key] = r
        print(f"{state} {prefix:<11}{r['resolvable']:>12,}{r['matched']:>10,}"
              f"{r['recall_resolvable']:>8.1f}%{r['ids_instate']:>14,}"
              f"{r['recall_instate']:>11.1f}%"
              f"{r['amt_instate']/1e6:>11,.1f}M{r['matched_amt']/1e6:>11,.1f}M"
              f"{r['coverage_instate']:>7.1f}%")

    print("-" * 100)
    ris = [r["recall_instate"] for r in out.values()]
    print(f"in-state (comparable) recall spans {min(ris):.1f}% – {max(ris):.1f}%")
    rec = [r["recall_resolvable"] for r in out.values()]
    cov = [r["coverage_instate"] for r in out.values()]
    print(f"recall spans   {min(rec):.1f}% – {max(rec):.1f}%")
    print(f"in-state coverage spans {min(cov):.1f}% – {max(cov):.1f}%")
    higher = sum(1 for k in out
                 if out[k]["coverage_instate"] > out[k]["recall_instate"])
    print(f"coverage exceeds recall in {higher} of {len(out)} panels")

    print()
    print("=" * 100)
    print("WHY THE REST DID NOT MATCH — the two causes are not equivalent")
    print("=" * 100)
    print(f"{'panel':<14}{'eligible ids':>13}{'unique on roll':>16}{'2+ on roll':>12}"
          f"{'0 on roll':>12}{'guard cost':>12}")
    print("-" * 100)
    for key, r in out.items():
        sp = r.get("split") or {}
        tot = sum(sp.values()) or 1
        print(f"{key:<14}{tot:>13,}{sp.get('unique', 0):>16,}"
              f"{sp.get('ambiguous', 0):>12,}{sp.get('none', 0):>12,}"
              f"{100.0 * sp.get('ambiguous', 0) / tot:>11.1f}%")
    print("-" * 100)
    print("'guard cost' is the share of eligible donor identities that almost certainly")
    print("belong to a registrant but were dropped because 2+ registrants share the key.")
    print("That is the only part of the shortfall the linkage RULE causes; the '0 on roll'")
    print("column is unregistered, moved, inactive, work-ZIP and nickname cases, which no")
    print("uniqueness rule could recover.")


if __name__ == "__main__":
    main()
