"""Measure the Washington PDC name-order parse defect from the data, not from a heuristic.

Why this script exists
----------------------
The WA PDC files 99.9% of contributor names WITHOUT a comma, and the matcher's SQL
(``donor_analysis.match_voters_to_donors``) parses a comma-less name as
``SPLIT_PART(name,' ',1)`` = surname, ``SPLIT_PART(name,' ',2)`` = first name. For any
filer who wrote their name first-name-first, that is reversed.

Review round 17 pointed out that the paper carried THREE competing estimates of how big
that defect is (1.85% of comma-less rows from the originating script's own parser, an
unverifiable figure; 4.7% of rows from a from-scratch surname-vocabulary heuristic; and
the originating script's dollar analogue), and that a referee would reasonably ask why a
panel is published with a known parser defect and three numbers for its size.

This script answers the question that actually matters for the paper — **what does the
defect cost in coverage** — by rebuilding the primary key both ways and counting.

The instrument is the roll itself, not a name dictionary. For each comma-less PDC
contributor key we build:

  forward   (what the matcher does today):  last = token 1, first = token 2
  reversed  (name written first-name-first): last = last token, first = token 1

and ask which of the two resolves to **exactly one** active registrant at that ZIP5 —
the same uniqueness guard the primary specification uses. A key that resolves only under
the reversed parse is a donor the current parser loses; a key that resolves only under
the forward parse is one it correctly finds. That is a direct measurement of coverage
cost, on the paper's own key, with no vocabulary heuristic in the middle.

PRIVACY: this script prints COUNTS AND SHARES ONLY. It never selects, returns or writes a
contributor name, a voter name or any other person-level field. Every SELECT it issues is
an aggregate. See CLAUDE.md, "no person-level record goes to a hosted model".

Usage
-----
    python scripts/diag_wa_pdc_name_order.py [--csv out.csv]
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

WA_DB = ROOT / "data" / "wa_statewide.duckdb"
VRDB = ROOT / "data" / "wa_vrdb.duckdb"

# Eligibility and residence restriction are taken from `diag_match_rate.py`, which owns
# the paper's match-rate table. Reproducing them by hand here would let the two drift, and
# the whole point of this script is that its figure sits in the same row as that table's.
from diag_match_rate import ELIGIBLE, in_state  # noqa: E402


def _build(conn: duckdb.DuckDBPyConnection) -> None:
    """Materialize the donor-side keys (both parses) and the roll-side key."""
    # --- roll side: the primary key's voter lookup, uniqueness guard applied ----------
    # Exactly the rank-0 key: (last, FULL first, zip5) over ACTIVE registrants, keeping
    # only keys that resolve to one registrant. Same construction as diag_match_rate's
    # `roll` CTE, so the two scripts' denominators agree.
    conn.execute(
        """
        CREATE OR REPLACE TEMP TABLE _roll_key AS
        SELECT last_upper, first_full, zip5
        FROM (
            SELECT UPPER(TRIM(last_name))  AS last_upper,
                   UPPER(TRIM(first_name)) AS first_full,
                   SUBSTR(reg_zip, 1, 5)   AS zip5,
                   COUNT(*) AS n
            FROM vrdb.voters
            WHERE status_code = 'A'
              AND last_name IS NOT NULL AND first_name IS NOT NULL
              AND reg_zip IS NOT NULL
            GROUP BY 1, 2, 3
        )
        WHERE n = 1
        """
    )

    # --- donor side: PDC, natural persons, in-state, comma-less ----------------------
    # A one-token name (an org remnant, or a mononym) has no order to get wrong; it is
    # excluded by the `LENGTH(f_first) > 1` guard below, which is also the match-rate table's.
    conn.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE _pdc AS
        SELECT
            UPPER(TRIM(contributor_name))          AS nm,
            SUBSTR(contributor_zip, 1, 5)          AS zip5,
            contribution_amount                    AS amt
        FROM individual_contributions
        WHERE SPLIT_PART(contribution_id, ':', 1) = 'PDC'
          AND {ELIGIBLE}
          AND {in_state('WA')}
          AND LENGTH(SUBSTR(contributor_zip, 1, 5)) = 5
        """
    )

    # The matcher's parse, character for character — no whitespace normalisation.
    #
    # An earlier version collapsed runs of internal whitespace before splitting. That looks
    # harmless and is not: 40,400 PDC rows carry a doubled internal space, and collapsing them
    # produced 560,182 keys against the match-rate table's 555,107 comma-less ones. The two
    # tables then described the same layer with denominators 5,075 apart, which is what an
    # external reviewer caught. The matcher does not collapse, so neither does this:
    # `SPLIT_PART('SMITH  JANE', ' ', 2)` is the empty string, the key fails the
    # `LENGTH(f_first) > 1` guard, and it is absent from BOTH tables — which is the point.
    conn.execute(
        """
        CREATE OR REPLACE TEMP TABLE _keys AS
        SELECT
            nm, zip5,
            -- forward: what the matcher does today
            UPPER(TRIM(SPLIT_PART(TRIM(nm), ' ', 1)))          AS f_last,
            UPPER(SPLIT_PART(TRIM(nm), ' ', 2))                AS f_first,
            -- reversed: the name read as "FIRST [MIDDLE] LAST". Unaffected by internal
            -- doubles, which produce empty elements in the middle, not at either end.
            UPPER(LIST_EXTRACT(STR_SPLIT(TRIM(nm), ' '), -1))  AS r_last,
            UPPER(SPLIT_PART(TRIM(nm), ' ', 1))                AS r_first,
            amt
        FROM _pdc
        WHERE nm NOT LIKE '%,%'
        """
    )

    # Distinct contributor KEYS, not rows. The unit here must be the FORWARD key
    # `(f_last, f_first, zip5)` — that, and nothing finer, is the denominator of the
    # paper's strict-key match-rate table, and a figure quoted beside that table has to
    # share its basis. `LENGTH(f_first) > 1` mirrors diag_match_rate's `elig`, which drops
    # keys whose first name is a bare initial.
    #
    # One forward key can carry several reversed variants ("JOHN A SMITH" and
    # "JOHN A JONES" both forward-key to (JOHN, A)), so resolution is computed on the
    # finer grain and then rolled up with MAX: the forward key counts as
    # reversed-resolvable if any of its variants resolves.
    conn.execute(
        """
        CREATE OR REPLACE TEMP TABLE _variant AS
        SELECT f_last, f_first, r_last, r_first, zip5, SUM(amt) AS dollars
        FROM _keys
        WHERE f_last <> '' AND LENGTH(f_first) > 1
        GROUP BY 1, 2, 3, 4, 5
        """
    )

    conn.execute(
        """
        CREATE OR REPLACE TEMP TABLE _resolved AS
        SELECT f_last, f_first, zip5,
               SUM(dollars)              AS dollars,
               MAX(hit_fwd)::BOOLEAN     AS hits_forward,
               MAX(hit_rev)::BOOLEAN     AS hits_reversed
        FROM (
            SELECT v.f_last, v.f_first, v.zip5, v.dollars,
                   CASE WHEN fw.last_upper IS NOT NULL THEN 1 ELSE 0 END AS hit_fwd,
                   CASE WHEN rv.last_upper IS NOT NULL THEN 1 ELSE 0 END AS hit_rev
            FROM _variant v
            LEFT JOIN _roll_key fw
                   ON fw.last_upper = v.f_last AND fw.first_full = v.f_first
                  AND fw.zip5 = v.zip5
            LEFT JOIN _roll_key rv
                   ON rv.last_upper = v.r_last AND rv.first_full = v.r_first
                  AND rv.zip5 = v.zip5
        )
        GROUP BY 1, 2, 3
        """
    )


def _placebo(conn: duckdb.DuckDBPyConnection) -> dict[str, float]:
    """Coincidence baseline: how often does a *correctly* ordered name resolve backwards?

    A key that resolves only under the reversed parse is not proof the filer wrote their
    name first-name-first — `(last_token, first_token)` could be an unrelated registrant
    who happens to be unique at that ZIP5. Without a baseline the whole measurement is
    open to that objection.

    The FEC layer supplies one. Its names are filed `LAST, FIRST MIDDLE`, so the comma
    tells us the true order; swapping the two halves therefore produces a key that is
    known to be wrong. The share of those wrong keys that still resolve uniquely is the
    coincidence rate, and the PDC excess over it is what name order actually explains.
    """
    conn.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE _fec AS
        SELECT
            UPPER(TRIM(SPLIT_PART(contributor_name, ',', 1)))                    AS t_last,
            UPPER(SPLIT_PART(TRIM(SPLIT_PART(contributor_name, ',', 2)), ' ', 1)) AS t_first,
            SUBSTR(contributor_zip, 1, 5)                                        AS zip5,
            SUM(contribution_amount)                                             AS dollars
        FROM individual_contributions
        WHERE SPLIT_PART(contribution_id, ':', 1) = 'FEC'
          AND contributor_name LIKE '%,%'
          AND {ELIGIBLE}
          AND {in_state('WA')}
          AND LENGTH(SUBSTR(contributor_zip, 1, 5)) = 5
        GROUP BY 1, 2, 3
        HAVING t_last <> '' AND LENGTH(t_first) > 1
        """
    )
    n_keys, n_true, n_swap_only = conn.execute(
        """
        SELECT COUNT(*),
               COUNT(*) FILTER (WHERE tr.last_upper IS NOT NULL),
               COUNT(*) FILTER (WHERE sw.last_upper IS NOT NULL
                                  AND tr.last_upper IS NULL)
        FROM _fec f
        LEFT JOIN _roll_key tr
               ON tr.last_upper = f.t_last AND tr.first_full = f.t_first
              AND tr.zip5 = f.zip5
        LEFT JOIN _roll_key sw
               ON sw.last_upper = f.t_first AND sw.first_full = f.t_last
              AND sw.zip5 = f.zip5
        """
    ).fetchone()
    return {
        "placebo_keys": float(n_keys),
        "placebo_true_resolved": float(n_true),
        "placebo_swap_only": float(n_swap_only),
        "placebo_swap_only_share": 100.0 * n_swap_only / max(n_keys, 1),
    }


def _age_sensitivity(conn: duckdb.DuckDBPyConnection) -> dict[str, float]:
    """Would repairing the parser move Finding 1? Compare the 65+ share of the donors the
    defect loses against the 65+ share of the panel it is missing from.

    This is the question that decides whether the defect is a coverage problem or a bias
    problem. If the recoverable donors look like the matched ones, the WA state panel is
    smaller than it should be but not skewed by the defect, and the finding stands on a
    narrower base. If they are much younger, the published 39.0% is inflated by the parser.

    Age is 2024 minus birth year, the paper's convention throughout.
    """
    conn.execute(
        """
        CREATE OR REPLACE TEMP TABLE _roll_age AS
        SELECT last_upper, first_full, zip5, birth_year
        FROM (
            SELECT UPPER(TRIM(last_name))  AS last_upper,
                   UPPER(TRIM(first_name)) AS first_full,
                   SUBSTR(reg_zip, 1, 5)   AS zip5,
                   ANY_VALUE(YEAR(birthdate)) AS birth_year,
                   COUNT(*) AS n
            FROM vrdb.voters
            WHERE status_code = 'A'
              AND last_name IS NOT NULL AND first_name IS NOT NULL
              AND reg_zip IS NOT NULL AND birthdate IS NOT NULL
            GROUP BY 1, 2, 3
        )
        WHERE n = 1
        """
    )
    # Recoverable set: forward keys whose REVERSED variant resolves and whose forward key does
    # not, read at FORWARD-KEY grain with a deterministic choice of variant.
    #
    # Both properties are load-bearing and both were wrong here first. Joining `_variant`
    # directly counts a forward key once per reversed variant it carries, which reweights the
    # age distribution; and picking the variant with `ANY_VALUE` follows scan order, so the
    # answer moved in the fourth decimal between identical runs. `MIN(STRUCT_PACK(...))`
    # compares field-wise and returns one real pair — column-wise `MIN` would be stable but
    # could name a pair no variant actually has. `verify_donor_class._d_pdc_name_order` does
    # exactly this, and the paper says that script re-derives this one, so the two must not
    # drift apart.
    conn.execute(
        """
        CREATE OR REPLACE TEMP TABLE _rec AS
        SELECT f_last, f_first, zip5, rv.r_last AS r_last, rv.r_first AS r_first FROM (
            SELECT v.f_last, v.f_first, v.zip5,
                   MIN(STRUCT_PACK(r_last := v.r_last, r_first := v.r_first)) rv
            FROM _variant v
            JOIN _resolved r
              ON r.f_last = v.f_last AND r.f_first = v.f_first AND r.zip5 = v.zip5
             AND r.hits_reversed AND NOT r.hits_forward
            GROUP BY 1, 2, 3)
        """
    )
    rec_n, rec_65 = conn.execute(
        """
        SELECT COUNT(*), COUNT(*) FILTER (WHERE 2024 - ra.birth_year >= 65)
        FROM _rec c
        JOIN _roll_age ra
          ON ra.last_upper = c.r_last AND ra.first_full = c.r_first
         AND ra.zip5 = c.zip5
        """
    ).fetchone()
    mat_n, mat_65 = conn.execute(
        """
        SELECT COUNT(*), COUNT(*) FILTER (WHERE 2024 - ra.birth_year >= 65)
        FROM _resolved r
        JOIN _roll_age ra
          ON ra.last_upper = r.f_last AND ra.first_full = r.f_first
         AND ra.zip5 = r.zip5
        WHERE r.hits_forward
        """
    ).fetchone()
    out = {
        "recoverable_dated": float(rec_n),
        "recoverable_65plus": 100.0 * rec_65 / max(rec_n, 1),
        "matched_dated": float(mat_n),
        "matched_65plus": 100.0 * mat_65 / max(mat_n, 1),
    }
    # The pooled figure a repaired parser would print.
    out["repaired_65plus"] = 100.0 * (rec_65 + mat_65) / max(rec_n + mat_n, 1)
    return out


def _scalars(conn: duckdb.DuckDBPyConnection) -> dict[str, float]:
    out: dict[str, float] = {}

    out["pdc_rows"], out["pdc_dollars"] = conn.execute(
        "SELECT COUNT(*), SUM(amt) FROM _pdc"
    ).fetchone()
    out["commaless_rows"] = conn.execute(
        "SELECT COUNT(*) FROM _pdc WHERE nm NOT LIKE '%,%'"
    ).fetchone()[0]
    out["commaless_share"] = 100.0 * out["commaless_rows"] / max(out["pdc_rows"], 1)

    (
        out["keys"],
        out["keys_dollars"],
        out["fwd_only"],
        out["fwd_only_dollars"],
        out["rev_only"],
        out["rev_only_dollars"],
        out["both"],
        out["both_dollars"],
        out["neither"],
        out["neither_dollars"],
    ) = conn.execute(
        """
        SELECT COUNT(*), SUM(dollars),
               COUNT(*) FILTER (WHERE hits_forward AND NOT hits_reversed),
               COALESCE(SUM(dollars) FILTER (WHERE hits_forward AND NOT hits_reversed), 0),
               COUNT(*) FILTER (WHERE hits_reversed AND NOT hits_forward),
               COALESCE(SUM(dollars) FILTER (WHERE hits_reversed AND NOT hits_forward), 0),
               COUNT(*) FILTER (WHERE hits_forward AND hits_reversed),
               COALESCE(SUM(dollars) FILTER (WHERE hits_forward AND hits_reversed), 0),
               COUNT(*) FILTER (WHERE NOT hits_forward AND NOT hits_reversed),
               COALESCE(SUM(dollars) FILTER (WHERE NOT hits_forward AND NOT hits_reversed), 0)
        FROM _resolved
        """
    ).fetchone()

    # DuckDB returns DECIMAL for SUM over a DECIMAL column; mixing that with float shares
    # raises rather than coercing, so normalise once here.
    out = {k_: (float(v) if v is not None else 0.0) for k_, v in out.items()}

    k = max(out["keys"], 1)
    d = max(out["keys_dollars"] or 1.0, 1.0)
    out["rev_only_share"] = 100.0 * out["rev_only"] / k
    out["rev_only_dollar_share"] = 100.0 * out["rev_only_dollars"] / d
    out["fwd_only_share"] = 100.0 * out["fwd_only"] / k
    out["both_share"] = 100.0 * out["both"] / k
    out["both_dollar_share"] = 100.0 * out["both_dollars"] / d

    # Reach if the parser tried both orders: everything that resolves under either,
    # minus the ambiguous ones (`both`) which a repaired parser would have to drop under
    # the same uniqueness logic that governs everything else.
    out["reach_forward"] = 100.0 * (out["fwd_only"] + out["both"]) / k
    out["reach_either"] = 100.0 * (out["fwd_only"] + out["rev_only"] + out["both"]) / k
    out["reach_either_unambiguous"] = 100.0 * (out["fwd_only"] + out["rev_only"]) / k
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", type=Path, default=None)
    args = ap.parse_args()

    if not WA_DB.exists():
        print(f"missing {WA_DB}", file=sys.stderr)
        return 2

    conn = duckdb.connect(str(WA_DB), read_only=True)
    try:
        conn.execute(f"ATTACH '{VRDB}' AS vrdb (READ_ONLY)")
        n_active = conn.execute(
            "SELECT COUNT(*) FROM vrdb.voters WHERE status_code = 'A'"
        ).fetchone()[0]
        print(f"WA active roll: {n_active:,} registrants\n")
        _build(conn)
        s = _scalars(conn)
        s.update(_placebo(conn))
        s.update(_age_sensitivity(conn))
    finally:
        conn.close()

    print("WA PDC contributor names (natural persons, ZIP5 present)")
    print(f"  rows                       {s['pdc_rows']:>12,.0f}")
    print(f"  comma-less rows            {s['commaless_rows']:>12,.0f}"
          f"   ({s['commaless_share']:.1f}%)")
    print()
    print("Comma-less keys with >= 2 tokens, resolved against the pinned active roll")
    print(f"  distinct (name, ZIP5) keys {s['keys']:>12,.0f}"
          f"   ${s['keys_dollars']:,.0f}")
    print(f"  resolve FORWARD only       {s['fwd_only']:>12,.0f}"
          f"   ({s['fwd_only_share']:.2f}%)")
    print(f"  resolve REVERSED only      {s['rev_only']:>12,.0f}"
          f"   ({s['rev_only_share']:.2f}%)"
          f"   ${s['rev_only_dollars']:,.0f} ({s['rev_only_dollar_share']:.2f}%)")
    print(f"  resolve BOTH (ambiguous)   {s['both']:>12,.0f}"
          f"   ({s['both_share']:.2f}%)"
          f"   ${s['both_dollars']:,.0f} ({s['both_dollar_share']:.2f}%)")
    print(f"  resolve NEITHER            {s['neither']:>12,.0f}")
    print()
    print("Reach on the primary key, comma-less keys")
    print(f"  forward parse only (today)          {s['reach_forward']:.2f}%")
    print(f"  either order accepted               {s['reach_either']:.2f}%")
    print(f"  either order, ambiguous dropped     {s['reach_either_unambiguous']:.2f}%")
    print()
    print("Placebo — FEC WA layer, names filed LAST, FIRST (true order known)")
    print(f"  comma-formatted keys       {s['placebo_keys']:>12,.0f}")
    print(f"  resolve on the TRUE order  {s['placebo_true_resolved']:>12,.0f}")
    print(f"  resolve SWAPPED only       {s['placebo_swap_only']:>12,.0f}"
          f"   ({s['placebo_swap_only_share']:.2f}%)  <- coincidence rate")
    print()
    excess = s["rev_only_share"] - s["placebo_swap_only_share"]
    print(f"  => the name-order defect costs {s['rev_only_share']:.2f}% of comma-less "
          f"keys and {s['rev_only_dollar_share']:.2f}% of their dollars,")
    print(f"     against a {s['placebo_swap_only_share']:.2f}% coincidence baseline "
          f"— an excess of {excess:.2f} points.")
    print()
    print("Would repairing it move Finding 1? (65+ share, age = 2024 - birth year)")
    print(f"  matched today              {s['matched_65plus']:>8.1f}%"
          f"   (n={s['matched_dated']:,.0f})")
    print(f"  recoverable by repair      {s['recoverable_65plus']:>8.1f}%"
          f"   (n={s['recoverable_dated']:,.0f})")
    print(f"  pooled, parser repaired    {s['repaired_65plus']:>8.1f}%")

    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        with args.csv.open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["metric", "value"])
            for key, val in s.items():
                w.writerow([key, val])
        print(f"\nwrote {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
