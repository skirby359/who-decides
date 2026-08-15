"""Does the linkage's geographic non-match bias Finding 2's county multipliers?

THE QUESTION, and why it is the sharpest one an external reviewer can put to this design.
Finding 2's county cut is computed on MATCHED donors joined to their county of registration.
Appendix F reports that the largest identified non-match bucket is keys whose surname and full
first name sit on the active roll **at a different ZIP5** — 13.8% to 26.8% of eligible resident
keys. That bucket is geographic displacement by definition, and it is dropped from a geographic
finding. Nothing in the paper cross-checked it. The top-1% dollar concentration DOES have an
all-donor cross-check (Appendix E, on far larger n); the county corollary did not.

WHY THE QUESTION REDUCES TO A SELECTION EFFECT. The primary specification is rank 0,
``STRICT_ZIP5_FULL`` — surname, full first name and ZIP5, unique on the active roll. The match
therefore REQUIRES ZIP5 equality between the filing and the roll, so a matched donor's county of
registration and the county of the ZIP they filed from are the same county, except where a ZIP5
straddles a county line. That impurity is measured below and is small. So using roll county
rather than filing ZIP cannot be what moves the multipliers, and the only live channel is
SELECTION: are the keys that match distributed across counties like the keys that do not?

WHAT IS COMPARED. Both sides use one geography source — the county of the ZIP5 on the filing —
so nothing here turns on which address is "right":

    matched   dollars on eligible resident keys that resolve to exactly one active registrant
    all       dollars on every eligible resident key, matched or not

If the two county distributions agree, the matched panel is geographically representative of the
universe it is drawn from and Finding 2's county cut is not a selection artifact. Where they
disagree, the difference is the bias, in points of dollar share and in multiplier.

The key rule is reimplemented here from the specification rather than imported, so this is an
independent reconstruction rather than a restatement of the matcher's own output. It reproduces
rank 0 only, which is the published panel's specification.

ZIP5 -> COUNTY comes from the state's own active roll: each ZIP5 is assigned the county holding
most of its registrants. Built from data in hand rather than an external crosswalk, and its
purity is reported per state — in Washington the modal county covers 99.31% of registrants in
their own ZIP, so the assignment is not carrying meaningful error.

Aggregate output only. Never emits a row.

Usage:
    PYTHONPATH=src python scripts/diag_donor_geography_selection.py
"""
from __future__ import annotations

import sys

import duckdb

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# (state, warehouse db, vrdb db, source prefix, label)
PANELS = [
    ("WA", "wa_statewide", "wa_vrdb", "FEC", "WA federal"),
    ("WA", "wa_statewide", "wa_vrdb", "PDC", "WA state"),
    ("NY", "ny_statewide", "ny_vrdb", "FEC", "NY federal"),
    ("NY", "ny_statewide", "ny_vrdb", "NY", "NY state"),
    ("ID", "id_statewide", "id_vrdb", "FEC", "ID federal"),
    ("ID", "id_statewide", "id_vrdb", "SUNSHINE", "ID state"),
]

# Counties the paper names, so the check reports on the exact figures a reader would quote.
NAMED = {"WA": ["KING"], "NY": ["NEW YORK"], "ID": ["ADA", "BLAINE"]}

# The paper's own in-state dollar coverage per panel (Appendix F §F8, via diag_match_rate.py).
# THE RECONSTRUCTION IS CHECKED AGAINST THESE BEFORE ANY GEOGRAPHY IS REPORTED. A panel whose
# matched set this script cannot reproduce is not the panel the paper published, and a
# geographic comparison over it would be measuring this script rather than the linkage.
#
# Five of six reproduce to within 0.3 points. WASHINGTON'S STATE PANEL DOES NOT — 8.8% here
# against 37.1% published — and the reason is documented rather than mysterious: the PDC name
# order defect (Appendix F §F8, `diag_wa_pdc_name_order.py`). The published figure takes its
# NUMERATOR from the panel table, i.e. the production matcher's output, against a denominator
# parsed the way this script parses; the naive rank-0 rule reimplemented here cannot reach the
# same keys. So WA state is reported as NOT RECONSTRUCTED and excluded, which is also how the
# paper already treats it — a secondary sensitivity panel whose match rate "should not be
# compared with the other panels' at face value".
PUBLISHED_COVERAGE = {
    "WA federal": 53.6, "WA state": 37.1, "NY federal": 49.2,
    "NY state": 46.8, "ID federal": 55.3, "ID state": 61.1,
}
RECON_TOL = 1.0

KNOWN_ORG = ("ORGANIZATION", "COMMITTEE", "BUSINESS", "PAC")
UNKNOWN = "UNKNOWN"

# Name parse and eligibility, copied from diag_match_rate.py so the denominator is the one the
# paper's match-rate table uses. A different eligibility filter here would make the comparison
# measure the filter rather than the selection.
LAST_SQL = """CASE WHEN contributor_name LIKE '%,%'
        THEN UPPER(TRIM(SPLIT_PART(contributor_name, ',', 1)))
        ELSE UPPER(TRIM(SPLIT_PART(contributor_name, ' ', -1))) END"""
FIRST_SQL = """CASE WHEN contributor_name LIKE '%,%'
        THEN UPPER(TRIM(SPLIT_PART(TRIM(SPLIT_PART(contributor_name, ',', 2)), ' ', 1)))
        ELSE UPPER(TRIM(SPLIT_PART(contributor_name, ' ', 1))) END"""
ELIGIBLE = f"""
    contributor_name IS NOT NULL AND contributor_name <> ''
    AND contributor_zip IS NOT NULL AND contributor_zip <> ''
    AND UPPER(contributor_name) NOT IN
        ('SMALL CONTRIBUTIONS', 'UNITEMIZED', 'ANONYMOUS')
    AND COALESCE(contributor_type, '{UNKNOWN}')
        NOT IN ({", ".join(f"'{v}'" for v in KNOWN_ORG)})
"""


def _zip_county(con) -> float:
    """Materialise ZIP5 -> modal county; return the assignment's purity as a percentage."""
    con.execute("DROP TABLE IF EXISTS _zc")
    con.execute("""
        CREATE TEMP TABLE _zc AS
        WITH z AS (
            SELECT SUBSTR(reg_zip, 1, 5) z5, county_name cty, COUNT(*) n
            FROM vrdb.voters
            WHERE status_code = 'A' AND reg_zip IS NOT NULL AND county_name IS NOT NULL
            GROUP BY 1, 2),
        ranked AS (
            SELECT z5, cty, n, ROW_NUMBER() OVER (PARTITION BY z5 ORDER BY n DESC, cty) rk,
                   SUM(n) OVER (PARTITION BY z5) tot
            FROM z WHERE LENGTH(z5) = 5)
        SELECT z5, cty, n AS modal_n, tot FROM ranked WHERE rk = 1""")
    purity, = con.execute("SELECT 100.0*SUM(modal_n)/SUM(tot) FROM _zc").fetchone()
    return float(purity)


def _panel(con, prefix: str, state: str) -> None:
    """Eligible RESIDENT keys with their dollars, flagged matched under rank 0.

    THE IN-STATE FILTER IS LOAD-BEARING and its absence is a real trap. The per-state FEC
    contribution loads are already donor-residence-filtered, but the state-disclosure loads
    (PDC, NYSBOE, Sunshine) are not — they carry out-of-state donors, whom no in-state roll can
    ever match. Omitting the filter reproduced the four federal panels to within 0.3 points and
    collapsed Washington's state panel to an 8.1% dollar match rate against the paper's 37.1%,
    because the whole out-of-state layer landed in the denominator as permanent non-matches.
    That split — federal right, state wrong — is what identified the missing filter.
    """
    con.execute("DROP TABLE IF EXISTS _keys")
    con.execute(f"""
        CREATE TEMP TABLE _keys AS
        WITH ids AS (
            SELECT {LAST_SQL} AS last_nm, {FIRST_SQL} AS first_nm,
                   SUBSTR(contributor_zip, 1, 5) AS z5,
                   SUM(contribution_amount) AS amt
            FROM individual_contributions
            WHERE SPLIT_PART(contribution_id, ':', 1) = '{prefix}' AND {ELIGIBLE}
              AND UPPER(TRIM(contributor_state)) = '{state}'
            GROUP BY 1, 2, 3),
        elig AS (
            SELECT * FROM ids
            WHERE last_nm <> '' AND LENGTH(first_nm) > 1 AND LENGTH(z5) = 5 AND amt > 0),
        roll AS (
            SELECT UPPER(TRIM(last_name)) AS last_nm, UPPER(TRIM(first_name)) AS first_nm,
                   SUBSTR(reg_zip, 1, 5) AS z5, COUNT(*) AS n_reg
            FROM vrdb.voters
            WHERE status_code = 'A' AND first_name IS NOT NULL
              AND last_name IS NOT NULL AND reg_zip IS NOT NULL
            GROUP BY 1, 2, 3)
        SELECT e.z5, e.amt, COALESCE(r.n_reg, 0) = 1 AS matched
        FROM elig e LEFT JOIN roll r USING (last_nm, first_nm, z5)""")


def main() -> int:
    print("=" * 96)
    print("DOES GEOGRAPHIC NON-MATCH BIAS FINDING 2's COUNTY CUT?")
    print("=" * 96)
    print("  Both columns use ONE geography source — the county of the ZIP5 on the filing — so")
    print("  the comparison isolates SELECTION. Under rank 0 the match requires ZIP5 equality,")
    print("  so roll county and filing-ZIP county coincide but for ZIP5s crossing county lines.")
    print()

    for state, wh, vr, prefix, label in PANELS:
        con = duckdb.connect(f"data/{wh}.duckdb", read_only=True)
        con.execute("SET enable_progress_bar=false")
        con.execute(f"ATTACH 'data/{vr}.duckdb' AS vrdb (READ_ONLY)")
        try:
            purity = _zip_county(con)
            _panel(con, prefix, state)

            unmapped, = con.execute("""
                SELECT 100.0*SUM(k.amt) FILTER (WHERE z.cty IS NULL)/SUM(k.amt)
                FROM _keys k LEFT JOIN _zc z ON z.z5 = k.z5""").fetchone()
            mrate, = con.execute(
                "SELECT 100.0*SUM(amt) FILTER (WHERE matched)/SUM(amt) FROM _keys").fetchone()

            roll = dict(con.execute(
                "SELECT county_name, COUNT(*) FROM vrdb.voters WHERE status_code='A' "
                "GROUP BY 1").fetchall())
            rt = sum(roll.values())

            shares = {
                cty: (float(m), float(a))
                for cty, m, a in con.execute("""
                    SELECT z.cty,
                           100.0*SUM(k.amt) FILTER (WHERE k.matched)
                                 /SUM(SUM(k.amt) FILTER (WHERE k.matched)) OVER (),
                           100.0*SUM(k.amt)/SUM(SUM(k.amt)) OVER ()
                    FROM _keys k JOIN _zc z ON z.z5 = k.z5
                    GROUP BY 1""").fetchall()}

            pub = PUBLISHED_COVERAGE[label]
            drift = abs(mrate - pub)
            if drift > RECON_TOL:
                print(f"  {label}   NOT RECONSTRUCTED — this script's rank-0 rule reaches "
                      f"{mrate:.1f}% of in-state dollars\n"
                      f"    against the published {pub:.1f}%. Its matched set is not the "
                      f"published panel's, so no\n    geography is reported for it. See the "
                      f"note on PUBLISHED_COVERAGE.\n")
                continue

            print(f"  {label}   (dollar match rate {mrate:.1f}% vs published {pub:.1f}%, "
                  f"ZIP5 purity {purity:.2f}%, {unmapped:.2f}% of dollars unmapped)")
            print(f"    {'county':16} {'roll%':>7} {'matched%':>9} {'all%':>7} "
                  f"{'mult(m)':>8} {'mult(a)':>8} {'d-mult':>7}")

            targets = sorted(shares, key=lambda c: -shares[c][0])[:3]
            for c in NAMED[state]:
                if c not in targets and c in shares:
                    targets.append(c)
            worst = 0.0
            for cty in targets:
                m_pct, a_pct = shares[cty]
                rs = 100.0 * roll.get(cty, 0) / rt
                if not rs:
                    continue
                mm, ma = m_pct / rs, a_pct / rs
                worst = max(worst, abs(mm - ma))
                print(f"    {cty:16} {rs:6.1f}% {m_pct:8.1f}% {a_pct:6.1f}% "
                      f"{mm:8.2f} {ma:8.2f} {mm - ma:+7.2f}")
            print(f"    -> largest multiplier movement among these counties: {worst:.2f}\n")
        finally:
            con.close()

    print("=" * 96)
    print("  Read a small movement as: the matched panel is geographically representative of")
    print("  the eligible universe, so the county cut is not an artifact of who matched.")
    print("=" * 96)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
