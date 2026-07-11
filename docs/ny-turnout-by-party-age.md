# New York: Who Decides Off-Year Elections — by Age **and Party-of-Record**

*Flagship party-resolved analysis, 2026-06-29. The party-of-record upgrade of
the WA "gray off-year electorate" finding ([`who-decides-washington.md`](who-decides-washington.md)).
WA could only show the off-year electorate is **older**; New York publishes
individual **party enrollment**, so we can ask the sharper question: when
turnout falls in off-year/local elections, does **one party's electorate age
harder than the other's** — mechanically tilting low-turnout local races?*

**Data.** `data/ny_vrdb.duckdb` — the NYSVOTER statewide FOIL file (13.54M
registrants; 100% party + DOB; per-voter `voter_history`). Each voter's history
is parsed into a normalized `voter_participation` table (the raw field mixes ~6
free-text formats per election across counties — `2024 GENERAL ELECTION`,
`General Election, 2024`, date-form `20241105 GE`, etc. — all unified).

**Reproduce.**
```
PYTHONPATH=src python scripts/load_ny_voters.py            # -> data/ny_vrdb.duckdb (one-time)
PYTHONPATH=src python scripts/diag_ny_turnout_party.py --rebuild
```

**Caveat (load-bearing).** The file is the **current (2026) roll**, so voters
who cast a ballot in a past election but were since purged/moved are absent.
=> composition **shares** (Tables A–C) are robust; turnout **rates** (Table D)
are biased high for older cycles. Cross-*party* comparison **within a year** is
valid (same bias hits every group); cross-*year* level comparisons in D are not.
Party `NOPARTY` = NY's "blank"/unaffiliated enrollment (25.5% of the roll); its
partisan lean is unknown and is **not** imputed.

---

## A. The gray off-year electorate — confirmed in NY (overall)

Share of general-election voters by age band, and median age:

| election | 18-29 | 30-44 | 45-64 | 65+ | median age |
|---|---:|---:|---:|---:|---:|
| 2024 GENERAL (presidential) | 14.1% | 23.1% | 34.6% | 28.2% | 53 |
| 2020 GENERAL (presidential) | 15.9% | 23.4% | 37.9% | 22.8% | 51 |
| 2022 GENERAL (midterm) | 9.8% | 21.1% | 38.5% | 30.6% | 56 |
| 2018 GENERAL (midterm) | 12.3% | 21.7% | 41.5% | 24.5% | 53 |
| 2025 GENERAL (odd-year/local) | 11.5% | 21.0% | 33.1% | 34.4% | 56 |
| 2023 GENERAL (odd-year/local) | 6.0% | 15.8% | 36.5% | 41.6% | 61 |

The WA pattern replicates: as the contest shrinks (presidential → midterm →
odd-year), the under-30 share collapses (14% → 10% → 6% in 2023) and the 65+
share swells (28% → 31% → 42%). Median age rises 53 → 61.

**Behavior, not rolls.** A Das-Gupta decomposition of the 65+ share rise from
2024 to the 2025 off-year (`diag_ny_electorate_extras.py`, detailed in
[`ny-electorate-extras.md`](ny-electorate-extras.md) §3) attributes it almost
entirely to differential **turnout** (rate effect), not to the registration age
structure (composition effect) — by ~5–6× for every party, and most strongly for
Republicans (+10.2 pt rise, +8.7 of it behavioral). The gray off-year electorate
is a salience/turnout problem fixable by on-cycle timing, not a registration
artifact.

## B. ★ FLAGSHIP — the Republican electorate ages hardest off-cycle

**Share 65+ within each party's voters:**

| election | DEM | REP | NOPARTY | OTHER |
|---|---:|---:|---:|---:|
| 2024 GENERAL (presidential) | 28.7% | **32.4%** | 22.2% | 27.0% |
| 2022 GENERAL (midterm) | 31.0% | 32.9% | 26.7% | 27.5% |
| 2025 GENERAL (odd-year/local) | 32.1% | **42.8%** | 30.6% | 35.1% |
| 2023 GENERAL (odd-year/local) | 41.6% | 43.5% | 39.3% | 37.4% |

**Median age within each party:**

| election | DEM | REP | NOPARTY | OTHER |
|---|---:|---:|---:|---:|
| 2024 GENERAL (presidential) | 52 | 57 | 48 | 54 |
| 2022 GENERAL (midterm) | 55 | 58 | 53 | 55 |
| 2025 GENERAL (odd-year/local) | **54** | **62** | 54 | 58 |
| 2023 GENERAL (odd-year/local) | 61 | 62 | 60 | 62 |

**Under-30 share within each party:** REP falls from 11.6% (2024) → 6.6% (2025)
→ 4.8% (2023); DEM holds youth better (14.0% → 13.3% → 6.5%).

**Finding.** The off-year electorate is not just older — **its Republican wing
ages most.** The GOP 65+ share jumps from 32% (presidential) to **43%**
(odd-year 2025) and the DEM–REP median-age gap widens from ~5 years
(presidential) to **~8 years** (2025: DEM 54 vs REP 62). Republican youth
participation collapses to roughly a third of its presidential level.

## C. Composition: the "older ⇒ more Republican" heuristic does **not** hold in NY

Party shares of the actual electorate vs the registration baseline:

| election | DEM | REP | NOPARTY | OTHER | DEM−REP |
|---|---:|---:|---:|---:|---:|
| 2024 GENERAL (presidential) | 47.3% | 26.7% | 21.5% | 4.5% | +20.6 |
| 2022 GENERAL (midterm) | 47.5% | 29.7% | 18.0% | 4.8% | +17.8 |
| 2018 GENERAL (midterm) | 52.8% | 26.0% | 16.6% | 4.7% | +26.8 |
| 2025 GENERAL (odd-year/local) | 56.4% | 23.2% | 16.7% | 3.7% | +33.2 |
| 2023 GENERAL (odd-year/local) | 47.6% | 32.0% | 15.7% | 4.7% | +15.6 |
| **REGISTRATION baseline (roll)** | 47.8% | 22.3% | 25.5% | 0.5% | +25.5 |

Two robust composition facts: (1) **the unaffiliated drop out** — NOPARTY is
25.5% of the roll but only 16–22% of voters, and falls further in off-years; (2)
the DEM–REP *composition* gap is **event-driven, not turnout-driven** — it
swings from +15.6 (2023) to +33.2 (2025) depending on what's on the ballot.
Unlike the national "midterm electorate is older and redder" story, in deep-blue
NY the older off-year electorate is **not** systematically more Republican in
composition; the partisan signal lives in *age structure and youth turnout*, not
in the headcount mix.

## D. Turnout rate by age × party (within-year valid; see caveat)

Republicans out-turn Democrats at **every age** in even-year (federal) cycles —
e.g. 2024 ages 45-64: REP 72% vs DEM 61%; 2022 ages 18-29: REP 38% vs DEM 28%.
**But that discipline does not carry to odd-year/local elections**: in the 2025
general, DEM under-30 turnout (30.8%) is nearly **double** REP's (15.9%),
inverting the even-year pattern — evidence that a Democratic-mobilizing local
contest can flip the age/party turnout geometry that otherwise favors the GOP.

## E. The nominating stage is smaller still — and locks out a quarter of voters

New York runs **closed** primaries (only a party's enrollees may vote in its
primary). Participation rate by enrollment (`scripts/diag_ny_primary_participation.py`):

| primary | DEM | REP | NOPARTY | OTHER |
|---|---:|---:|---:|---:|
| 2024 Presidential Primary | 4.8% | 4.9% | 0.1% | 0.2% |
| 2024 State/Congress Primary | 7.7% | 1.7% | 0.1% | 0.6% |
| 2022 State/Congress Primary | 17.9% | 18.4% | 0.6% | 2.0% |
| 2021 Primary (odd-year) | 16.9% | 5.0% | 0.5% | 1.5% |

**Findings.** (1) Primary turnout is in the single digits to high teens — the
electorate that *nominates* is a small fraction of the one that elects. (2) The
**25.3% of active registrants enrolled "blank" are excluded by law** (≈0.1–0.6%
participation, the residual being nonpartisan/special races) — a structural
democratic-health fact: a quarter of the registered population has no voice at
the nominating stage. (3) In blue NY the **Democratic primary is frequently the
decisive contest** (2021 odd-year DEM 16.9% vs REP 5.0%; 2024 state DEM 7.7% vs
REP 1.7%), echoing the safe-seat finding that where one party dominates, the
real election is its primary — decided by a doubly-small, enrollment-gated
electorate.

## Why this matters (electoral-health framing)

This is the first **party-resolved** confirmation that off-year/local elections
in a large state are decided by a structurally different — older, and
asymmetrically older-Republican — electorate than presidential elections. It
sharpens the on-cycle-timing reform case (Sightline / Unite America audience):
the off-year electorate's distortion is not partisan-neutral aging but has a
measurable party-asymmetric age structure, while youth mobilization remains the
lever that can override it. It moves the WA finding from "weak-against-null"
(older, party unknown) toward a concrete, falsifiable party-resolved claim.

**Open follow-ons:** (1) join to NY FEC contributions (donor-class × party,
needs the NY matcher); (2) closed-primary participation by enrollment; (3)
resolve the NOPARTY bloc's behavior/age/geography; (4) district-level
registration vs the safe-seat map.
