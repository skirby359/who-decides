"""External validation of the New York roll against NYSBOE's published enrollment series.

WHY THIS EXISTS. `who-decides-new-york.md` reads party of record from a single 2026 extract and
applies it to historical electorates. Two limitations follow, and until now both were argued
rather than measured:

  1. **Party drift.** The file carries CURRENT enrollment and no history of it, so a voter who
     voted in 2021 is labelled with their 2026 party.
  2. **Survivorship.** Voters present at a past election but since purged are absent, and
     purging is invisible in a single extract.

Both distort the same quantity in the same direction — the party composition of the people who
were on the roll at some past date — so a single external number bounds their COMBINED size.
NYSBOE publishes exactly that number: statewide enrollment by party and active/inactive status,
twice a year, back to 2006.

WHAT IS COMPARED, and what the gap does and does not mean. For each snapshot date D:

    published(D)  = NYSBOE's statewide ACTIVE enrollment shares as of D
    file(D)       = party shares among registrants in our extract who registered on or before D
                    and are ACTIVE today

The gap is the net of party switching, purges, active-to-inactive transitions, and NYSBOE's own
revisions, between D and the extract date. It is an UPPER bound on drift attributable to any one
of them, and it is not decomposable into them — nothing here separates a switcher from a purged
voter. That is the honest ceiling of what one extract plus a published aggregate can support.

THE 2026-02-20 ROW IS THE CONTROL, and it is the reason to trust the rest. It sits about four
months before the extract, so drift has had almost no time to accumulate. If the method were
mis-specified — wrong active filter, wrong party bucketing, wrong denominator — that row would
be off too, and the historical gaps would be measuring our own error. Read it first.

BUCKETING. NYSBOE publishes DEM / REP / CON / WOR / OTH / BLANK. The paper's four buckets map
as DEM, REP, NOPARTY = BLANK, OTHER = CON + WOR + OTH. Verified against the column header row
of each workbook rather than assumed, because the minor-party columns change across years as
parties gain and lose ballot status.

PROVENANCE. Figures below are the "Statewide Total / Active" row of the NYSBOE workbook served
at `https://elections.ny.gov/<slug>`, retrieved 2026-08-08. Those URLs return .xlsx directly
and the host answers 403 to scripted clients, so they were read through a browser rather than
fetched here; the constants are transcribed so this script has no network dependency and no
downloaded artifact to keep in step. Re-check them against the published workbook, not against
a cached copy.

Aggregate output only. Never emits a row.

Usage:
    PYTHONPATH=src python scripts/diag_ny_enrollment_validation.py
"""
from __future__ import annotations

import duckdb

NY_VRDB = "data/ny_vrdb.duckdb"

# NYSBOE "NYSVoter Enrollment by County, Party Affiliation and Status", Statewide Total /
# Active row. (date, slug, DEM, REP, CON, WOR, OTH, BLANK, TOTAL)
PUBLISHED = [
    ("2021-02-21", "voters-registered-county-2212021",
     6_216_759, 2_745_827, 154_711, 44_358, 463_961, 2_795_205, 12_420_821),
    ("2022-02-21", "voters-registered-county-2212022",
     5_929_375, 2_645_799, 152_669, 45_093, 419_193, 2_713_757, 11_905_886),
    ("2024-02-27", "voters-registered-county-02272024",
     5_778_841, 2_695_185, 154_128, 50_048, 366_132, 2_879_809, 11_924_143),
    ("2025-11-01", "voters-registered-county-11012025",
     6_043_040, 2_859_197, 161_187, 58_144, 309_302, 3_185_762, 12_616_632),
    ("2026-02-20", "voters-registered-county-02202026",
     6_002_006, 2_835_976, 160_464, 59_617, 301_469, 3_187_610, 12_547_142),
]

# What each snapshot is the right comparator FOR, in the paper's terms.
CONTEXT = {
    "2021-02-21": "party-change deadline before the 2021 odd-year primary (§III row 4)",
    "2022-02-21": "deadline before the 2022 state/congressional primary (§III row 3)",
    "2024-02-27": "deadline before both 2024 primaries (§III rows 1-2)",
    "2025-11-01": "the 2025 general electorate (§I under-30 pair)",
    "2026-02-20": "CONTROL — four months before the extract; drift should be near zero",
}

PARTY = ("CASE WHEN v.party='DEM' THEN 'DEM' WHEN v.party='REP' THEN 'REP' "
         "WHEN v.party='BLK' THEN 'NOPARTY' ELSE 'OTHER' END")
BUCKETS = ("DEM", "REP", "NOPARTY", "OTHER")


def _published_shares(row) -> dict[str, float]:
    _, _, dem, rep, con, wor, oth, blank, total = row
    return {"DEM": 100.0 * dem / total, "REP": 100.0 * rep / total,
            "NOPARTY": 100.0 * blank / total,
            "OTHER": 100.0 * (con + wor + oth) / total}


def main() -> int:
    con = duckdb.connect(NY_VRDB, read_only=True)
    print("=" * 88)
    print("NEW YORK ROLL vs NYSBOE PUBLISHED ENROLLMENT — combined party-drift + survivorship")
    print("=" * 88)
    print("  Gap = file(D) - published(D), in percentage points of the active roll.")
    print("  Positive means the surviving 2026 sample OVER-represents that bucket at D.\n")

    worst = 0.0
    for row in PUBLISHED:
        date, _slug = row[0], row[1]
        pub = _published_shares(row)
        obs = dict(con.execute(f"""
            SELECT {PARTY} p, 100.0*COUNT(*)/SUM(COUNT(*)) OVER ()
            FROM voters v
            WHERE v.status_code='A' AND v.registration_date <= DATE '{date}'
            GROUP BY 1""").fetchall())
        n_file, = con.execute(f"""
            SELECT COUNT(*) FROM voters v
            WHERE v.status_code='A' AND v.registration_date <= DATE '{date}'""").fetchone()

        print(f"  {date}   {CONTEXT[date]}")
        print(f"    {'':10} {'published':>10} {'file':>10} {'gap':>8}")
        for b in BUCKETS:
            gap = obs.get(b, 0.0) - pub[b]
            flag = "  <-- largest" if abs(gap) == max(
                abs(obs.get(x, 0.0) - pub[x]) for x in BUCKETS) else ""
            print(f"    {b:10} {pub[b]:9.2f}% {obs.get(b, 0.0):9.2f}% {gap:+8.2f}{flag}")
            if date != "2026-02-20":
                worst = max(worst, abs(gap))
        print(f"    active registrants: published {row[8]:,}  file {n_file:,} "
              f"({100.0*n_file/row[8]-100:+.2f}%)\n")

    print("=" * 88)
    print(f"  Largest historical bucket gap (excluding the control): {worst:.2f} points.")
    print("  Read as a CEILING on party-composition error from drift plus survivorship")
    print("  combined — not a decomposition, and not a correction factor.")
    print("=" * 88)
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
