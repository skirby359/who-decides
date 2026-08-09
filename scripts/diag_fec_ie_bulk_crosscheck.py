"""Reconcile loaded FEC independent expenditures against FEC's bulk files.

The API loader is the primary path, but it needs a key, it is rate-limited, and
its correctness rests on one filter (``is_notice=false``) whose meaning is not
self-evident from the response. This script checks the result against a source
that shares none of those properties: FEC's public bulk downloads, which need no
key and can be re-fetched by anyone reproducing the work.

FEC publishes independent expenditures in TWO bulk files, and the pair is the
whole point — they are the two halves the API returns interleaved:

  periodic  pas2<YY>.zip -> itpas2.txt, TRANSACTION_TP in ('24A','24E')
            Schedule E as filed on the committee's regular Form 3X. This is the
            authoritative universe and what the loader should match.
  notices   independent_expenditure_<YYYY>.csv
            The 24/48-hour Form 24 filings, which RESTATE the same money.

Measured 2026-08-08 for WA House 2024: periodic $25.5M, notices $31.4M, loaded
(pre-fix, unfiltered API) $53.8M — i.e. roughly the sum of the two, which is the
double-count. Post-fix the loaded total should track the periodic column.

Neither bulk file is a drop-in replacement for the API: the notice file retains
superseded amendments (AMNDT_IND A1..A4) and pas2 carries memo subtotals
(MEMO_CD='X'), both handled below. They are a CHECK, not a source.

Usage:
    python scripts/diag_fec_ie_bulk_crosscheck.py --cycle 2024 [--state WA]
    python scripts/diag_fec_ie_bulk_crosscheck.py --cycle 2024 --cache-dir /tmp/fec

No PII: independent expenditures are committee-to-vendor filings. Nothing here
reads a voter file or a contributor record.
"""
from __future__ import annotations

import argparse
import os
import sys
import urllib.request
import zipfile

import duckdb

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass


# --- self-contained, on purpose ------------------------------------------------------------
# This script is published to the public reproduction repo, which ships neither `db.py` nor
# the rest of the product schema, so it imports only duckdb + stdlib — the same constraint
# `who-decides/scripts/donor_matcher.py` carries and for the same reason: a reader must be
# able to run it against nothing but the FEC's public files and a DuckDB.
#
# That means the countable-row rule is stated TWICE, here and in `wa_analyzer.db`. Duplication
# of a rule is how the two drift apart, so it is not left to discipline:
# `tests/test_etl/test_fec_ie_notice_dedup.py::TestPublicCrosscheckMatchesDb` asserts this
# predicate is character-identical to `ie_countable_sql()` and fails the build otherwise.
IE_COUNTABLE_SQL = (
    "(source <> 'FEC' OR ("
    "is_notice IS FALSE AND "
    "COALESCE(memo_code, '') <> 'X'))"
)


def _has_provenance(con) -> bool:
    try:
        cols = {r[0] for r in con.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'independent_expenditures'").fetchall()}
    except Exception:  # noqa: BLE001
        return False
    return {"is_notice", "memo_code"} <= cols


def _countable_relation(con) -> str:
    """Countable IE rows, however far the database has been migrated.

    The view is created by a WRITE connection; this script opens the warehouse
    read-only and is exactly what you run BEFORE repairing an un-migrated DB, so
    it must not depend on the view existing. With no provenance columns at all,
    every FEC row is unclassified — which is the same verdict the migrated case
    reaches for those rows, just expressed without the column.
    """
    try:
        con.execute("SELECT 1 FROM v_independent_expenditures LIMIT 0")
        return "v_independent_expenditures"
    except Exception:  # noqa: BLE001
        pass
    if _has_provenance(con):
        return f"(SELECT * FROM independent_expenditures WHERE {IE_COUNTABLE_SQL})"
    return "(SELECT * FROM independent_expenditures WHERE source <> 'FEC')"


def _unclassified(con) -> list[tuple]:
    """FEC rows loaded before the notice/periodic split was recorded.

    With the columns absent, EVERY FEC row qualifies. Returning nothing there
    would report a clean database, which is the precise opposite of the truth.
    """
    predicate = "is_notice IS NULL" if _has_provenance(con) else "TRUE"
    try:
        return con.execute(f"""
            SELECT state, office, district, election_cycle, COUNT(*) AS n_rows
            FROM independent_expenditures
            WHERE source = 'FEC' AND {predicate}
            GROUP BY 1, 2, 3, 4 ORDER BY 1, 2, 3, 4
        """).fetchall()
    except Exception:  # noqa: BLE001
        return []

_BULK = "https://www.fec.gov/files/bulk-downloads"

# itpas2.txt is pipe-delimited and headerless; column order is fixed by FEC's
# published file description and has been stable across every cycle since 2010.
_PAS2_COLS = [
    "CMTE_ID", "AMNDT_IND", "RPT_TP", "TRANSACTION_PGI", "IMAGE_NUM",
    "TRANSACTION_TP", "ENTITY_TP", "NAME", "CITY", "STATE", "ZIP_CODE",
    "EMPLOYER", "OCCUPATION", "TRANSACTION_DT", "TRANSACTION_AMT", "OTHER_ID",
    "CAND_ID", "TRAN_ID", "FILE_NUM", "MEMO_CD", "MEMO_TEXT", "SUB_ID",
]

# 24E = independent expenditure ADVOCATING a candidate, 24A = OPPOSING.
_IE_TRANSACTION_TYPES = ("24A", "24E")

# cn.txt (candidate master), also pipe-delimited and headerless.
_CN_COLS = [
    "CAND_ID", "CAND_NAME", "CAND_PTY_AFFILIATION", "CAND_ELECTION_YR",
    "CAND_OFFICE_ST", "CAND_OFFICE", "CAND_OFFICE_DISTRICT", "CAND_ICI",
    "CAND_STATUS", "CAND_PCC", "CAND_ST1", "CAND_ST2", "CAND_CITY", "CAND_ST",
    "CAND_ZIP",
]


def _download(url: str, dest: str) -> str:
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        print(f"  cached  {os.path.basename(dest)}")
        return dest
    print(f"  fetching {url}")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    urllib.request.urlretrieve(url, dest)
    return dest


def _candidate_districts(con, cycle: int, state: str, cache: str) -> str:
    """Register `cand` mapping CAND_ID -> the district the candidate RAN IN.

    NOT `substr(CAND_ID, 5, 2)`. An FEC candidate id encodes the district at
    first registration and never changes, so a candidate who moves districts —
    or is moved by redistricting — keeps the old digits forever. Deriving the
    district from the id put WA-08's `H0WA08046` under district 08 while every
    other source had those expenditures in district 01, which showed up here as
    a district reconciling to $0 against $3,160 loaded.

    This is the same trap CLAUDE.md records for committee state (resolve
    committee -> candidate -> CAND_OFFICE_ST, never CMTE_ST); `cn.txt`'s
    CAND_OFFICE_DISTRICT is the authority for the district half of it.
    """
    zpath = _download(f"{_BULK}/{cycle}/cn{str(cycle)[2:]}.zip",
                      os.path.join(cache, f"cn{cycle}.zip"))
    with zipfile.ZipFile(zpath) as z:
        z.extract("cn.txt", cache)
    txt = os.path.join(cache, "cn.txt").replace("\\", "/")
    cn_cols = ", ".join(f"'{c}': 'VARCHAR'" for c in _CN_COLS)
    con.execute(f"""
        CREATE OR REPLACE TEMP VIEW cand AS
        SELECT CAND_ID,
               lpad(TRIM(CAND_OFFICE_DISTRICT), 2, '0') AS district
        FROM read_csv('{txt}', delim='|', header=false, quote='',
                      columns={{{cn_cols}}})
        WHERE CAND_OFFICE = 'H' AND CAND_OFFICE_ST = '{state}'
    """)
    return "cand"


def periodic_totals(con, cycle: int, state: str, cache: str) -> list[tuple]:
    """Per-district Schedule E from the periodic reports (the authority)."""
    _candidate_districts(con, cycle, state, cache)
    zpath = _download(f"{_BULK}/{cycle}/pas2{str(cycle)[2:]}.zip",
                      os.path.join(cache, f"pas2{cycle}.zip"))
    with zipfile.ZipFile(zpath) as z:
        z.extract("itpas2.txt", cache)
    txt = os.path.join(cache, "itpas2.txt").replace("\\", "/")

    cols = ", ".join(f"'{c}': 'VARCHAR'" for c in _PAS2_COLS)
    tps = ", ".join(f"'{t}'" for t in _IE_TRANSACTION_TYPES)
    return con.execute(f"""
        SELECT c.district AS district,
               COUNT(*) AS n_rows,
               SUM(TRY_CAST(p.TRANSACTION_AMT AS DOUBLE)) AS amount
        FROM read_csv('{txt}', delim='|', header=false, quote='',
                      columns={{{cols}}}) p
        JOIN cand c ON c.CAND_ID = p.CAND_ID
        WHERE p.TRANSACTION_TP IN ({tps})
          -- Memo rows restate money itemized on another line. Summing them is
          -- the same error, one layer down, as summing the notice file.
          AND COALESCE(p.MEMO_CD, '') <> 'X'
        GROUP BY 1 ORDER BY 1
    """).fetchall()


def notice_totals(con, cycle: int, state: str, cache: str) -> list[tuple]:
    """Per-district 24/48-hour notices. Reported for contrast, never added."""
    csv = _download(f"{_BULK}/{cycle}/independent_expenditure_{cycle}.csv",
                    os.path.join(cache, f"ie_notice_{cycle}.csv")).replace("\\", "/")
    return con.execute(f"""
        SELECT can_office_dis AS district,
               COUNT(*) AS n_rows,
               SUM(exp_amo) AS amount
        FROM read_csv_auto('{csv}', header=true, sample_size=-1)
        WHERE can_office_state = '{state}' AND can_office = 'H'
          -- An amended notice does NOT remove the original from this file, so
          -- without this the file double-counts against itself.
          AND amndt_ind = 'N'
        GROUP BY 1 ORDER BY 1
    """).fetchall()


def national_rank(con, cycle: int, state: str, cache: str) -> list[tuple]:
    """Rank every U.S. House race nationally by total periodic IE for `cycle`.

    Exists because the warehouse cannot answer it: it holds Washington races
    only, so any claim of the form "the most IE-saturated House race in the
    country" is unfalsifiable from in-repo data and has to be checked against
    the national bulk file. One such claim survived review in this series and
    was false — WA-03 2024 ranks 22nd of 387 at its corrected $18.61M, and read
    as 1st only because the notice/periodic double-count had doubled it past
    every real race.

    Returns ``(rank, race, amount, is_target_state)`` for the top slice plus
    every race in `state`.
    """
    _candidate_districts(con, cycle, state, cache)  # extracts cn.txt
    txt = os.path.join(cache, "cn.txt").replace("\\", "/")
    cn_cols = ", ".join(f"'{c}': 'VARCHAR'" for c in _CN_COLS)
    pas = os.path.join(cache, "itpas2.txt").replace("\\", "/")
    cols = ", ".join(f"'{c}': 'VARCHAR'" for c in _PAS2_COLS)
    tps = ", ".join(f"'{t}'" for t in _IE_TRANSACTION_TYPES)
    return con.execute(f"""
        WITH allcand AS (
            SELECT CAND_ID, CAND_OFFICE_ST AS st,
                   lpad(TRIM(CAND_OFFICE_DISTRICT), 2, '0') AS d
            FROM read_csv('{txt}', delim='|', header=false, quote='',
                          columns={{{cn_cols}}})
            WHERE CAND_OFFICE = 'H'),
        ie AS (
            SELECT c.st, c.d, TRY_CAST(p.TRANSACTION_AMT AS DOUBLE) AS amt
            FROM read_csv('{pas}', delim='|', header=false, quote='',
                          columns={{{cols}}}) p
            JOIN allcand c ON c.CAND_ID = p.CAND_ID
            WHERE p.TRANSACTION_TP IN ({tps})
              AND COALESCE(p.MEMO_CD, '') <> 'X'),
        races AS (
            SELECT st || '-' || d AS race, st, SUM(amt) AS amount
            FROM ie GROUP BY 1, 2)
        SELECT RANK() OVER (ORDER BY amount DESC) AS rk, race, amount,
               st = '{state}' AS is_target,
               COUNT(*) OVER () AS n_races
        FROM races
        QUALIFY rk <= 5 OR is_target
        ORDER BY rk
    """).fetchall()


def loaded_totals(db: str, cycle: int, state: str) -> list[tuple]:
    """What the database currently holds, counted the way a total should be."""
    con = duckdb.connect(db, read_only=True)
    try:
        rel = _countable_relation(con)
        return con.execute(f"""
            SELECT district, COUNT(*) AS n_rows, SUM(expenditure_amount) AS amount
            FROM {rel}
            WHERE source = 'FEC' AND office = 'H'
              AND state = ? AND election_cycle = ?
            GROUP BY 1 ORDER BY 1
        """, [state, cycle]).fetchall()
    finally:
        con.close()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cycle", type=int, required=True)
    ap.add_argument("--state", default="WA")
    ap.add_argument("--db", default="data/wa_statewide.duckdb")
    ap.add_argument("--cache-dir", default=os.path.join("data", "raw", "fec_bulk"))
    ap.add_argument("--tolerance", type=float, default=0.05,
                    help="Fractional gap vs the periodic column tolerated "
                         "before a district is flagged (default 0.05).")
    ap.add_argument("--national-rank", action="store_true",
                    help="Also rank every U.S. House race by total periodic IE. "
                         "Use before writing any 'most expensive race in the "
                         "country'-shaped claim — the warehouse cannot check one.")
    args = ap.parse_args()

    print("=" * 78)
    print(f"FEC IE bulk cross-check — {args.state} U.S. House, cycle {args.cycle}")
    print("=" * 78)

    con = duckdb.connect()
    print("\nBulk files:")
    periodic = {d: (n, a) for d, n, a in
                periodic_totals(con, args.cycle, args.state, args.cache_dir)}
    notices = {d: (n, a) for d, n, a in
               notice_totals(con, args.cycle, args.state, args.cache_dir)}
    con.close()

    dbcon = duckdb.connect(args.db, read_only=True)
    stale = _unclassified(dbcon)
    dbcon.close()

    loaded = {d: (n, a) for d, n, a in loaded_totals(args.db, args.cycle, args.state)}

    districts = sorted(set(periodic) | set(notices) | set(loaded))
    print(f"\n{'dist':>5}  {'periodic($M)':>13}  {'notices($M)':>12}  "
          f"{'loaded($M)':>11}  {'gap vs periodic':>16}")
    print("-" * 68)
    flagged = []
    for d in districts:
        p = periodic.get(d, (0, 0.0))[1] or 0.0
        n = notices.get(d, (0, 0.0))[1] or 0.0
        ld = float(loaded.get(d, (0, 0.0))[1] or 0.0)
        gap = (ld - p) / p if p else (0.0 if not ld else float("inf"))
        mark = ""
        if p or ld:
            if abs(gap) > args.tolerance:
                mark = "  <-- CHECK"
                flagged.append(d)
        print(f"{d:>5}  {p/1e6:13.2f}  {n/1e6:12.2f}  {ld/1e6:11.2f}  "
              f"{gap*100:15.1f}%{mark}")

    tp = sum(v[1] or 0 for v in periodic.values())
    tn = sum(v[1] or 0 for v in notices.values())
    tl = sum(float(v[1] or 0) for v in loaded.values())
    print("-" * 68)
    print(f"{'TOTAL':>5}  {tp/1e6:13.2f}  {tn/1e6:12.2f}  {tl/1e6:11.2f}")

    print("\nReading this table:")
    print("  * loaded ~= periodic          -> correct; the notice column is the")
    print("                                   duplicate layer, excluded by design.")
    print("  * loaded ~= periodic+notices  -> the notice filter is not being")
    print("                                   applied. Re-load with --fec-ie-replace.")
    print("  * loaded <  periodic          -> truncation, or a district whose")
    print("                                   candidates are missing from")
    print("                                   candidate_finance (the loader scopes")
    print("                                   to it, so an absent candidate is an")
    print("                                   absent row, silently).")
    print("  * loaded == 0 everywhere      -> rows predate the notice/periodic")
    print("                                   split; see below.")

    if stale:
        print("\n  ⚠ STALE ROWS — excluded from `loaded` above:")
        for st, off, dist, cyc, n in stale:
            print(f"      {st} {off}-{dist} cycle {cyc}: {n:,} rows")
        # Name the cycles that are ACTUALLY stale, not the one being
        # cross-checked. They routinely differ — a clean 2024 reconciliation
        # sits happily beside untouched 2026 rows — and printing the wrong
        # cycle sends the reader to re-run a load that changes nothing.
        for cyc in sorted({c for _, _, _, c, _ in stale}):
            print("    python main.py load --fec-ie --statewide "
                  f"--fec-ie-replace --fec-ie-cycle {cyc}")

    if args.national_rank:
        con2 = duckdb.connect()
        rows = national_rank(con2, args.cycle, args.state, args.cache_dir)
        con2.close()
        n_races = rows[0][4] if rows else 0
        print(f"\nNational rank by total periodic IE — {args.cycle} U.S. House "
              f"({n_races} races with any IE):")
        seen_gap = False
        for rk, race, amount, is_target, _ in rows:
            if rk > 5 and not seen_gap:
                print("      ...")
                seen_gap = True
            mark = "  <-- " + args.state if is_target else ""
            print(f"    {rk:>4}. {race:<8} ${amount/1e6:8.2f}M{mark}")

    if flagged:
        print(f"\n  ⚠ {len(flagged)} district(s) outside tolerance: "
              f"{', '.join(flagged)}")
        return 1
    if stale:
        return 1
    print("\n  ✓ Every district reconciles to the periodic bulk file.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
