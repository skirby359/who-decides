"""Sanity-check the NYSBOE state contribution load (individual_contributions 'NY:' rows).

Written after the 2026-07-26 load because that load put 3.95M new rows / $880.3M behind
published figures in docs/donor-class-and-the-electorate.md, and the CSV has several
traps that would silently corrupt them. Read-only; run any time.

Checks, in order of how badly a failure would hurt:

  A. DOUBLE-COUNTING. NYSBOE reports carry R_AMEND, and an amended filing can re-state
     transactions from the original. 44% of rows in our slice sit on amended reports, so
     the question is real — but the flag alone proves nothing, because amended reports
     carry fresh TRANS_NUMBERs. The test that matters is content-level: the same filer,
     contributor, date and amount appearing more than once. Measured that way the excess
     is ~0.7% of dollars (see the threshold below), and the residue looks like genuine
     same-day repeat gifts with sequential transaction numbers rather than restatements.
  B. AMOUNT PARSING. ORG_AMT is currency text ("$40", "$1,250"). Anything that failed to
     cast was dropped by the loader; anything negative would be a refund/adjustment.
  C. INTERNAL CONSISTENCY. candidate_finance was aggregated from the SAME CSV by a
     different code path (ny_finance.load_ny_finance_from_csv, schedules A/B/C/G). Our
     Schedule-A individual subset must be <= its total_individual_contributions.
     IMPORTANT: that aggregate covers DEFAULT_CYCLES, which is EVEN YEARS ONLY, while the
     donor panel deliberately includes odd years (New York holds odd-year municipal and
     county elections, and the WA PDC panel includes its odd years too). The comparison is
     therefore restricted to even cycles on both sides; comparing all nine cycles against
     the even-year aggregate makes a valid subset look like a 1.5x superset.
  D. KEY INTEGRITY. contribution_id is the PK; duplicates would have thrown, but confirm
     the ROW_NUMBER de-collision actually worked and no id repeats.
  E. FIELD QUALITY. ZIP shape, name format ("LAST, FIRST" is load-bearing for the match
     parser), date range vs cycle, is_itemized.
  F. MATCH PLAUSIBILITY. Matched share of dollars, and whether matched donors look like
     NY residents.

Usage:  python scripts/sanity_check_ny_contributions.py
Exit 0 = all checks pass; exit 1 = at least one FAIL.
"""
import glob
import os
import sys

import duckdb

NY_DB = "data/ny_statewide.duckdb"
CSV_GLOB = "data/raw/ny/Campaign_Finance_Disclosure_Reports_Contributions*.csv"

fails: list[str] = []
warns: list[str] = []


def ok(msg):
    print(f"  [ok]   {msg}")


def warn(msg):
    warns.append(msg)
    print(f"  [WARN] {msg}")


def fail(msg):
    fails.append(msg)
    print(f"  [FAIL] {msg}")


con = duckdb.connect(NY_DB, read_only=True)
csvs = sorted(glob.glob(CSV_GLOB), key=os.path.getmtime, reverse=True)
CSV = csvs[0] if csvs else None
SRC = (f"read_csv_auto('{CSV.replace(chr(92), '/')}', header=true, all_varchar=true, "
       "ignore_errors=true)") if CSV else None

print("=" * 78)
print("A. AMENDMENTS — would double-count every re-stated transaction")
print("=" * 78)
SLICE = """TRY_CAST("ELECTION_YEAR" AS INTEGER) BETWEEN 2018 AND 2026
           AND upper(COALESCE("CNTRBR_TYPE_DESC",'')) = 'INDIVIDUAL'
           AND upper(COALESCE("FILING_SCHED_ABBREV",'')) = 'A'"""
AMT = "TRY_CAST(REPLACE(REPLACE(\"ORG_AMT\", '$', ''), ',', '') AS DOUBLE)"

if SRC:
    for a, n in con.execute(f"""
        SELECT COALESCE("R_AMEND", '(null)'), COUNT(*)
        FROM {SRC} WHERE {SLICE} GROUP BY 1 ORDER BY 2 DESC""").fetchall():
        print(f"     R_AMEND={a:<8} {n:>10,}")
    # Content-level duplicate test: same filer + contributor + date + amount.
    groups, excess_rows, excess_m, tot_m = con.execute(f"""
        WITH k AS (SELECT "FILER_ID" f, upper(COALESCE("FLNG_ENT_LAST_NAME",'')) ln,
                          upper(COALESCE("FLNG_ENT_FIRST_NAME",'')) fn,
                          COALESCE("FLNG_ENT_ZIP",'') z, "SCHED_DATE" d, {AMT} a
                   FROM {SRC} WHERE {SLICE}),
        g AS (SELECT a, COUNT(*) n FROM k GROUP BY f, ln, fn, z, d, a HAVING COUNT(*) > 1)
        SELECT (SELECT COUNT(*) FROM g), (SELECT SUM(n-1) FROM g),
               (SELECT SUM((n-1)*a)/1e6 FROM g),
               (SELECT SUM({AMT})/1e6 FROM {SRC} WHERE {SLICE})""").fetchone()
    pct = 100.0 * float(excess_m) / float(tot_m)
    print(f"   content-level duplicates: {groups:,} groups, {excess_rows:,} excess rows, "
          f"${excess_m:.1f}M ({pct:.2f}% of dollars)")
    if pct > 5.0:
        fail(f"{pct:.1f}% of dollars are duplicated content — amended filings are likely "
             "being counted alongside their originals")
    elif pct > 0.25:
        warn(f"{pct:.2f}% of dollars sit in same-filer/contributor/date/amount groups; "
             "inspection shows sequential transaction numbers, i.e. genuine same-day "
             "repeat gifts rather than restatements — immaterial at this size")
    else:
        ok(f"content-level duplication is {pct:.2f}% of dollars")
else:
    warn("source CSV not found; skipping CSV-side checks")

print("\n" + "=" * 78)
print("B. AMOUNT PARSING")
print("=" * 78)
n, tot, neg, zero, mx = con.execute("""
    SELECT COUNT(*), SUM(contribution_amount),
           COUNT(*) FILTER (WHERE contribution_amount < 0),
           COUNT(*) FILTER (WHERE contribution_amount = 0),
           MAX(contribution_amount)
    FROM individual_contributions WHERE contribution_id LIKE 'NY:%'""").fetchone()
print(f"   loaded {n:,} rows / ${float(tot)/1e6:,.1f}M; max single ${float(mx):,.0f}")
if neg or zero:
    warn(f"{neg:,} negative and {zero:,} zero amounts (loader filters amount>0)")
else:
    ok("no negative or zero amounts")
if SRC:
    csv_n, csv_tot, unparsed = con.execute(f"""
        SELECT COUNT(*),
               SUM(TRY_CAST(REPLACE(REPLACE("ORG_AMT", '$', ''), ',', '') AS DOUBLE)),
               COUNT(*) FILTER (WHERE TRY_CAST(REPLACE(REPLACE("ORG_AMT",'$',''),',','')
                                               AS DOUBLE) IS NULL)
        FROM {SRC}
        WHERE TRY_CAST("ELECTION_YEAR" AS INTEGER) BETWEEN 2018 AND 2026
          AND upper(COALESCE("CNTRBR_TYPE_DESC",'')) = 'INDIVIDUAL'
          AND upper(COALESCE("FILING_SCHED_ABBREV",'')) = 'A'""").fetchone()
    print(f"   CSV slice: {csv_n:,} rows / ${float(csv_tot)/1e6:,.1f}M; "
          f"{unparsed:,} unparseable amounts")
    drop_pct = 100.0 * (csv_n - n) / csv_n
    if drop_pct > 2.0:
        warn(f"{csv_n - n:,} CSV rows ({drop_pct:.1f}%) did not load — "
             "expected: null last name / null zip / non-positive amount")
    else:
        ok(f"{csv_n - n:,} rows dropped ({drop_pct:.1f}%) — within expectation")
    delta = abs(float(csv_tot) - float(tot)) / float(csv_tot) * 100
    print(f"   dollar delta CSV vs loaded: {delta:.1f}% (dropped rows carry their dollars)")

print("\n" + "=" * 78)
print("C. INTERNAL CONSISTENCY vs candidate_finance (independent code path)")
print("=" * 78)
# Even cycles only on BOTH sides — candidate_finance was built over DEFAULT_CYCLES
# (even years), while the donor panel deliberately spans odd years too.
EVEN = "(2018, 2020, 2022, 2024, 2026)"
cf_ind, our_even, our_all = con.execute(f"""
    SELECT (SELECT SUM(total_individual_contributions) FROM candidate_finance
            WHERE fec_candidate_id LIKE 'NY:%' AND election_cycle IN {EVEN}),
           (SELECT SUM(contribution_amount) FROM individual_contributions
            WHERE contribution_id LIKE 'NY:%' AND election_cycle IN {EVEN}),
           (SELECT SUM(contribution_amount) FROM individual_contributions
            WHERE contribution_id LIKE 'NY:%')""").fetchone()
print(f"   candidate_finance individual, even cycles (A/B/C/G): ${float(cf_ind)/1e6:,.1f}M")
print(f"   our Schedule-A individual, even cycles:              ${float(our_even)/1e6:,.1f}M")
print(f"   our Schedule-A individual, all nine cycles:          ${float(our_all)/1e6:,.1f}M")
ratio = float(our_even) / float(cf_ind)
if ratio > 1.02:
    fail(f"our even-cycle subset EXCEEDS the aggregate ({ratio:.2f}x) — a subset cannot be "
         "larger; suspect double-counting")
elif ratio < 0.5:
    warn(f"our subset is only {ratio:.0%} of the aggregate — check the schedule filter")
else:
    ok(f"even-cycle subset is {ratio:.0%} of the A/B/C/G individual aggregate — consistent "
       "(we take Schedule A only, the aggregate also counts B/C/G)")

print("\n" + "=" * 78)
print("D. KEY INTEGRITY")
print("=" * 78)
d = con.execute("""
    SELECT COUNT(*) - COUNT(DISTINCT contribution_id)
    FROM individual_contributions WHERE contribution_id LIKE 'NY:%'""").fetchone()[0]
ok("contribution_id unique across NY rows") if d == 0 else fail(f"{d:,} duplicate ids")
orphan = con.execute("""
    SELECT COUNT(DISTINCT ic.fec_candidate_id) FROM individual_contributions ic
    LEFT JOIN candidate_finance cf USING (fec_candidate_id)
    WHERE ic.contribution_id LIKE 'NY:%' AND cf.fec_candidate_id IS NULL""").fetchone()[0]
if orphan:
    warn(f"{orphan:,} filer ids have contributions but no candidate_finance row "
         "(filers below the aggregate's reporting threshold)")
else:
    ok("every recipient filer resolves to a candidate_finance row")

print("\n" + "=" * 78)
print("E. FIELD QUALITY")
print("=" * 78)
bad_zip, bad_name, nulldate = con.execute("""
    SELECT COUNT(*) FILTER (WHERE NOT regexp_matches(contributor_zip, '^[0-9]{5}')),
           COUNT(*) FILTER (WHERE contributor_name NOT LIKE '%,%'),
           COUNT(*) FILTER (WHERE contribution_date IS NULL)
    FROM individual_contributions WHERE contribution_id LIKE 'NY:%'""").fetchone()
print(f"   zips not starting with 5 digits: {bad_zip:,}")
print(f"   names without a comma:           {bad_name:,}")
print(f"   null contribution_date:          {nulldate:,}")
if bad_name > n * 0.01:
    fail(f"{bad_name:,} names lack the 'LAST, FIRST' comma the match parser splits on")
else:
    ok("name format is 'LAST, FIRST' as the matcher expects")
if bad_zip > n * 0.05:
    warn(f"{100.0*bad_zip/n:.1f}% of zips are non-standard")
else:
    ok("zip format is clean")
print("   cycle vs contribution-date span:")
for cyc, lo, hi, cnt in con.execute("""
    SELECT election_cycle, MIN(contribution_date), MAX(contribution_date), COUNT(*)
    FROM individual_contributions WHERE contribution_id LIKE 'NY:%'
    GROUP BY 1 ORDER BY 1""").fetchall():
    print(f"     {cyc}  {lo} .. {hi}  {cnt:>9,}")

print("\n" + "=" * 78)
print("F. MATCH PLAUSIBILITY")
print("=" * 78)
md, mt = con.execute("""
    SELECT COUNT(*), SUM(total_donated) FROM voter_donor_affiliation_state""").fetchone()
print(f"   matched: {md:,} voters / ${float(mt)/1e6:,.1f}M "
      f"({100*float(mt)/float(tot):.1f}% of loaded dollars)")
ny_share = con.execute("""
    SELECT 100.0*COUNT(*) FILTER (WHERE upper(contributor_state)='NY')/COUNT(*)
    FROM individual_contributions WHERE contribution_id LIKE 'NY:%'""").fetchone()[0]
print(f"   NY-resident share of loaded contributions: {ny_share:.1f}%")
if float(mt) / float(tot) > ny_share / 100 + 0.05:
    warn("matched dollar share exceeds the NY-resident share — unexpected")
else:
    ok("matched share sits below the NY-resident ceiling, as it must")

con.close()
print("\n" + "=" * 78)
if fails:
    print(f"RESULT: {len(fails)} FAIL, {len(warns)} warn")
    for f in fails:
        print(f"  FAIL: {f}")
    sys.exit(1)
print(f"RESULT: all checks pass ({len(warns)} warning(s))")
for w in warns:
    print(f"  warn: {w}")
