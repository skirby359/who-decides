# New York: Who Decides Off-Year Elections — by Age **and Party-of-Record**

> **Diagnostic companion — REGENERATED 2026-08-29 against the current pipeline.** The
> citable owner of every claim here is
> [`who-decides-new-york.md`](who-decides-new-york.md); this note carries the underlying
> tables, refreshed by re-running `scripts/diag_ny_turnout_party.py` (whose 2026-08-29
> header records a grouping bug fixed the same day — it wobbled only OTHER-column cells;
> the DEM/REP/NOPARTY columns were never affected). Exactly two cells moved in the
> refresh: §B's 2023 OTHER median (62 → 60) and §C's roll-baseline OTHER share
> (4.4 → 4.5). History: earlier on 2026-08-29 this file was marked SUPERSEDED after an
> external series review found it still stating two positions the paper had withdrawn —
> the "shares are robust / same bias hits every group" caveat and §B's dynamic finding,
> both corrected below with the original wording recorded — and the author then chose
> regeneration over archiving, so it is again a current companion rather than history.

*Early party-resolved working analysis, 2026-06-29. The party-of-record upgrade of
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

**Caveat (load-bearing — restated 2026-08-29 to match the paper).** The file is the
**current (2026) roll**, so voters purged/moved since a past election are absent, and
party is **2026 enrollment**, not enrollment at the election analysed. This note
originally called composition shares (Tables A–C) "robust" and said the same bias "hits
every group", making within-year cross-party comparison valid — **the paper withdrew both
as unestablished and measured the bias instead**: attrition is near-flat across parties
but *not* across age (the under-30 band leaves at roughly twice the 45–64 rate), so age
shares understate youth in past electorates. See the paper's front-matter caveats,
Boundary of inference, and Appendix C for the measured bounds. Turnout **rates** (Table D)
are biased high for older cycles.
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

The WA pattern replicates in level: both odd-year electorates are older than the 2024
presidential one, though not in a clean salience order (the 2025 odd-year is younger than the
2023 one — see the table). From the presidential electorate to the 2023 odd-year the under-30
share collapses (14% → 6%) and the 65+ share swells (28% → 42%); median age rises 53 → 61.

**Behavior, not rolls.** A Das-Gupta decomposition of the 65+ share rise from
2024 to the 2025 off-year (`diag_ny_electorate_extras.py`, detailed in
[`ny-electorate-extras.md`](ny-electorate-extras.md) §3) attributes it almost
entirely to differential **turnout** (rate effect), not to the registration age
structure (composition effect) — the rate effect outweighs composition by roughly
**3.6× (Democrats) to 12.5× (unaffiliated)**, and is largest in level terms for
Republicans (+10.2 pt 65+ rise, +8.7 of it behavioral). The gray off-year electorate
is a salience/turnout problem fixable by on-cycle timing, not a registration
artifact.

## B. ★ FLAGSHIP — the Republican electorate is OLDER than the Democratic one in every general

*⚠ This heading read "the Republican electorate ages hardest off-cycle" until 2026-08-26. That
dynamic claim was withdrawn in `who-decides-new-york.md` §I on 2026-08-16 and the tables below
are what withdrew it: the R−D gap in the 65+ share runs **+3.7** in 2024 (presidential) and
**+1.9** in 2022, against **+10.7** in 2025 and **+1.9** in 2023. The two odd years point
opposite ways and 2023 sits BELOW the presidential gap, so the gap does not widen as salience
falls — 2025 is an event-specific outlier, not a calendar effect. The durable finding is the
LEVEL, which every row here supports.*

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
| 2023 GENERAL (odd-year/local) | 61 | 62 | 60 | 60 |

**Under-30 share within each party:** REP falls from 11.6% (2024) → 6.6% (2025)
→ 4.8% (2023); DEM holds youth better (14.0% → 13.3% → 6.5%).

**Finding (restated 2026-08-29 — the level claim, which is what the paper supports).**
The off-year electorate is not just older — **its Republican wing is the oldest in every
general**, and 2025 is the extreme case: the GOP 65+ share runs 32% (presidential) to
**43%** (odd-year 2025), the DEM–REP median-age gap is ~5 years at the presidential level
against **~8 years** in 2025 (DEM 54 vs REP 62), and Republican youth participation in
2025 sits at roughly a third of its presidential level. *(Until 2026-08-29 this paragraph
announced the withdrawn dynamic claim — that the Republican wing "ages most" — as its
finding, four paragraphs after the heading note recording that the same claim had been
withdrawn. 2025's gap is an event-specific outlier, not a calendar effect; the paper's
eight-general series carries the level ordering.)*

## C. Composition: the "older ⇒ more Republican" heuristic does **not** hold in NY

Party shares of the actual electorate vs the registration baseline:

| election | DEM | REP | NOPARTY | OTHER | DEM−REP |
|---|---:|---:|---:|---:|---:|
| 2024 GENERAL (presidential) | 47.3% | 26.7% | 21.5% | 4.5% | +20.6 |
| 2022 GENERAL (midterm) | 47.5% | 29.7% | 18.0% | 4.8% | +17.8 |
| 2018 GENERAL (midterm) | 52.8% | 26.0% | 16.6% | 4.7% | +26.8 |
| 2025 GENERAL (odd-year/local) | 56.4% | 23.2% | 16.7% | 3.7% | +33.2 |
| 2023 GENERAL (odd-year/local) | 47.6% | 32.0% | 15.7% | 4.7% | +15.6 |
| **REGISTRATION baseline (roll)** | 47.8% | 22.3% | 25.5% | 4.5% | +25.5 |

Two robust composition facts: (1) **the unaffiliated drop out** — NOPARTY is
25.5% of the roll but only 16–22% of voters, and falls further in off-years; (2)
the DEM–REP *composition* gap does not track aggregate turnout in the simple way that
heuristic assumes — it swings from +15.6 (2023) to +33.2 (2025) depending on what's on the
ballot, so a lower-turnout off-year electorate is not mechanically more Republican here.
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

*(Basis note, corrected 2026-08-29: the paper's §II quotes this pair as **32.8% / 16.6%**
because it additionally restricts the denominator to **active** registrants; §D above uses
the whole roll enrolled by election day. Both are enrolled-by-election-day rates — an
earlier version of this note, written the same morning, misattributed the difference to
the enrollment cutoff, which both bases share. The "nearly double" relation and the
inversion hold on either basis; the paper's active-roll figures are the published ones.)*

## E. The nominating stage is smaller still — and a quarter of voters cannot enter it while unaffiliated

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
**25.3% of active registrants enrolled "blank" are ineligible while unaffiliated**
(≈0.1–0.6% participation) — a structural democratic-health fact: a quarter of the registered
population has no voice at the nominating stage unless it re-enrolls before the February
deadline. (3) In blue NY the **Democratic primary draws far more participation than the
Republican** in the state and odd-year contests (2021 odd-year DEM 16.9% vs REP 5.0%; 2024
state DEM 7.7% vs REP 1.7%).

<sub>**Two prose corrections, 2026-08-11.** The residual blank participation was previously
described as "nonpartisan/special races." A closed primary admits only enrollees, so a
now-blank voter recorded in one changed enrollment afterwards — and the 2024 *presidential*
primary, which carries no nonpartisan contest anywhere in the state, still shows a non-zero
blank cell. These cells are principally enrollment change, and the main paper now uses them as
its switching bound. Separately, "the real election is its primary" was dropped: participation
asymmetry is not evidence about which stage decides a seat, and the companion safe-seat paper
withdrew a stronger form of that inference on better evidence. The rate figures in the table
above are unchanged — this document has carried the contemporaneous-eligibility denominator
since it was written.</sub>

## Why this matters (electoral-health framing)

This is the first **party-resolved** confirmation that the electorate returning
off-year/local ballots in a large state is structurally different — older, and
asymmetrically older-Republican — from the presidential one. It
sharpens the on-cycle-timing reform case (Sightline / Unite America audience):
the off-year electorate's distortion is not partisan-neutral aging but has a
measurable party-asymmetric age structure, while youth mobilization remains the
lever that can override it. It moves the WA finding from "weak-against-null"
(older, party unknown) toward a concrete, falsifiable party-resolved claim.

**Follow-ons:** (1) NY FEC donor-class × party — **done**
([`donor-class-and-the-electorate.md` Finding 3](donor-class-and-the-electorate.md)); (2) closed-primary
participation by enrollment — **done** (§E above); (4) district-level registration vs
the safe-seat map — **done** ([`ny-electorate-extras.md`](ny-electorate-extras.md) §5).
(3) The NOPARTY bloc's behavior/age/geography remains partly open (largely addressed in
[`ny-electorate-extras.md`](ny-electorate-extras.md) §1).
