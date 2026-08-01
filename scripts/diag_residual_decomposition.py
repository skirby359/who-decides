"""D3 — decompose the unmatched residual.

`diag_match_rate.py` establishes that 49-65% of eligible donor identities have **no** active
registrant carrying that surname, full first name and ZIP5, and labels the bucket a coverage
property of the key rather than an error rate. That is honest but uninformative: it lumps a
contributor who has never registered together with one who registered under "Robert" and gave
as "Bob", and those support different conclusions about what the panels miss.

This splits the bucket by relaxing exactly one condition at a time, as a **priority cascade** —
each identity is assigned to the first bucket it satisfies, so the buckets partition the residual
and sum back to it:

  1. **Inactive or removed.** The same key matches a registrant whose status is not active. The
     person is on the file; the matcher's `status_code = 'A'` restriction excluded them. Idaho's
     export carries no status flag, so this bucket is structurally unavailable there and is
     reported as such rather than as zero.
  2. **Different ZIP.** Surname and full first name match an active registrant, at another ZIP5.
     Movers who gave before a move, and donors who filed a work address. Recoverable in principle
     by relaxing geography, which the paper declines to do because it costs precision.
  3. **Name-form mismatch.** Surname, first *initial* and ZIP5 match an active registrant, but
     the full first names differ. Nicknames against legal names — "Bob"/"Robert",
     "Kate"/"Katherine" — which is the price of requiring the complete first name.
  4. **No roll counterpart.** Nothing matches on any of the above. Not registered in this state,
     or registered under a materially different name.

Bucket 4 is the only one that is genuinely outside the reach of any linkage on this data, so its
size is the real floor on coverage. The other three are choices the specification makes, and
naming them lets a reader see what a different specification would buy and what it would cost.

    PYTHONPATH=src python scripts/diag_residual_decomposition.py

Read-only. Writes nothing.
"""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diag_match_rate import ELIGIBLE, FIRST_SQL, LAST_SQL, PANELS, VRDB  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# Idaho's statewide export has no active/inactive flag, so bucket 1 cannot be measured there.
HAS_STATUS = {"wa_vrdb": True, "ny_vrdb": True, "id_vrdb": False}


def decompose(con, prefix: str, has_status: bool) -> dict:
    src = f"SPLIT_PART(contribution_id, ':', 1) = '{prefix}'"
    active = "status_code = 'A'"
    inactive = "status_code <> 'A'" if has_status else "1=0"
    # Built as separate lookups rather than one query: each relaxation needs its own
    # aggregation of the roll, and DuckDB plans the four small hash joins far better than a
    # single query with four LEFT JOINs against 5-13M rows.
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE _elig AS
        SELECT * FROM (
            SELECT {LAST_SQL} AS l, {FIRST_SQL} AS f,
                   SUBSTR(contributor_zip, 1, 5) AS z
            FROM individual_contributions WHERE {src} AND {ELIGIBLE}
            GROUP BY 1, 2, 3)
        WHERE l <> '' AND LENGTH(f) > 1 AND LENGTH(z) = 5""")
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE _k_active AS
        SELECT UPPER(TRIM(last_name)) l, UPPER(TRIM(first_name)) f,
               SUBSTR(reg_zip, 1, 5) z, COUNT(*) n
        FROM vrdb.voters WHERE {active} AND first_name IS NOT NULL
          AND last_name IS NOT NULL AND reg_zip IS NOT NULL
        GROUP BY 1, 2, 3""")
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE _k_inactive AS
        SELECT UPPER(TRIM(last_name)) l, UPPER(TRIM(first_name)) f,
               SUBSTR(reg_zip, 1, 5) z
        FROM vrdb.voters WHERE {inactive} AND first_name IS NOT NULL
          AND last_name IS NOT NULL AND reg_zip IS NOT NULL
        GROUP BY 1, 2, 3""")
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE _k_anyzip AS
        SELECT UPPER(TRIM(last_name)) l, UPPER(TRIM(first_name)) f
        FROM vrdb.voters WHERE {active} AND first_name IS NOT NULL
          AND last_name IS NOT NULL GROUP BY 1, 2""")
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE _k_initial AS
        SELECT UPPER(TRIM(last_name)) l, UPPER(SUBSTR(TRIM(first_name), 1, 1)) fi,
               SUBSTR(reg_zip, 1, 5) z
        FROM vrdb.voters WHERE {active} AND first_name IS NOT NULL
          AND last_name IS NOT NULL AND reg_zip IS NOT NULL
        GROUP BY 1, 2, 3""")

    total, matched, ambiguous, inact, difzip, nameform, none = con.execute("""
        WITH tagged AS (
            SELECT e.*,
                   ka.n AS n_active,
                   ki.l IS NOT NULL AS is_inactive,
                   kz.l IS NOT NULL AS any_zip,
                   kn.l IS NOT NULL AS init_match
            FROM _elig e
            LEFT JOIN _k_active   ka USING (l, f, z)
            LEFT JOIN _k_inactive ki USING (l, f, z)
            LEFT JOIN _k_anyzip   kz USING (l, f)
            LEFT JOIN _k_initial  kn ON kn.l = e.l
                                    AND kn.fi = SUBSTR(e.f, 1, 1)
                                    AND kn.z = e.z)
        SELECT COUNT(*),
               COUNT(*) FILTER (WHERE n_active = 1),
               COUNT(*) FILTER (WHERE n_active > 1),
               COUNT(*) FILTER (WHERE n_active IS NULL AND is_inactive),
               COUNT(*) FILTER (WHERE n_active IS NULL AND NOT is_inactive AND any_zip),
               COUNT(*) FILTER (WHERE n_active IS NULL AND NOT is_inactive
                                  AND NOT any_zip AND init_match),
               COUNT(*) FILTER (WHERE n_active IS NULL AND NOT is_inactive
                                  AND NOT any_zip AND NOT init_match)
        FROM tagged""").fetchone()
    return {"total": total, "matched": matched, "ambiguous": ambiguous,
            "inactive": inact, "difzip": difzip, "nameform": nameform, "none": none}


def main() -> None:
    print("=" * 112)
    print("D3 — why an eligible donor identity did not match, as a priority cascade")
    print("=" * 112)
    print(f"{'panel':<13}{'eligible':>11}{'matched':>10}{'2+ (guard)':>11}"
          f"{'inactive':>10}{'diff ZIP':>10}{'name form':>11}{'no counterpart':>15}")
    print("-" * 112)
    out = {}
    for state, db, prefix, _panel in PANELS:
        p = DATA / f"{db}.duckdb"
        if not p.exists():
            continue
        vrdb = VRDB[db]
        con = duckdb.connect(str(p), read_only=True)
        try:
            con.execute(f"ATTACH '{DATA / (vrdb + '.duckdb')}' AS vrdb (READ_ONLY)")
            r = decompose(con, prefix, HAS_STATUS[vrdb])
        finally:
            con.close()
        key = f"{state} {'fed' if prefix == 'FEC' else 'state'}"
        out[key] = r
        t = r["total"]
        inact = f"{r['inactive']:,}" + ("" if HAS_STATUS[vrdb] else "*")
        print(f"{key:<13}{t:>11,}{r['matched']:>10,}{r['ambiguous']:>11,}"
              f"{inact:>10}{r['difzip']:>10,}{r['nameform']:>11,}{r['none']:>15,}")

    print("-" * 112)
    print("* Idaho's export carries no active/inactive flag, so its inactive bucket is not")
    print("  measurable and its identities fall through to the later buckets instead.")
    print()
    print("As shares of the eligible identities in each layer:")
    print(f"{'panel':<13}{'matched':>9}{'2+ guard':>10}{'inactive':>10}{'diff ZIP':>10}"
          f"{'name form':>11}{'no counterpart':>15}")
    print("-" * 112)
    for key, r in out.items():
        t = r["total"] or 1
        print(f"{key:<13}"
              f"{100.0*r['matched']/t:>8.1f}%{100.0*r['ambiguous']/t:>9.1f}%"
              f"{100.0*r['inactive']/t:>9.1f}%{100.0*r['difzip']/t:>9.1f}%"
              f"{100.0*r['nameform']/t:>10.1f}%{100.0*r['none']/t:>14.1f}%")
    print("-" * 112)
    nc = [100.0 * r["none"] / (r["total"] or 1) for r in out.values()]
    print(f"'no counterpart' spans {min(nc):.1f}% - {max(nc):.1f}% — the real floor on coverage.")
    print("Everything to its left is a consequence of a specification choice, not of the data.")


if __name__ == "__main__":
    main()
