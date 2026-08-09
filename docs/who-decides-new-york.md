# Who Decides New York?

### The off-year electorate, resolved by party — from 13.5 million individual registration and vote records

**Stephen Kirby** · Tikor Consulting · July 2026

*AI-assisted drafting and analysis review. All figures are reproducible from
public-record data available through lawful request and from the open-source scripts
cited below, including `scripts/verify_who_decides_ny.py`. The paper source, code, and
data-acquisition recipe are public at <https://github.com/skirby359/who-decides>; the
underlying voter file is not redistributed. Contact: kirby@tikorconsulting.com.*

*Party-resolved companion to [`who-decides-washington.md`](who-decides-washington.md)
and [`who-decides-idaho.md`](who-decides-idaho.md) (the deep-red counterpart).
Washington showed the off-year electorate is **older**; New York publishes each
voter's **party enrollment**, so here we can ask the question Washington could
not — *whose* electorate ages, who is ineligible for the nominating stage, and how
one-sided the registration map is. **DRAFT — pending human/editorial sign-off.** `scripts/verify_who_decides_ny.py` scrapes
this paper and asserts its figures against the voter file, with the exceptions the script names
in its own output; see [`electoral-health-audit-log.md`](electoral-health-audit-log.md). That
gate is automated and is not the sign-off. The sign-off is a person reading the paper end to
end, recorded in [`ny-submission-notes.md`](ny-submission-notes.md) §Sign-off.*

*An earlier version of this line said the paper had been verified because "all `verify_*`
scripts re-run, exit 0". That was worth nothing: until 2026-08-01 this paper's verifier had
no assertions and no failing exit path, so it printed values for a human to compare and
returned 0 whatever the data said. When it was converted to assert, §II and §III did not
reproduce and have been recomputed — see the note under §III.*

*Provenance. All figures from `data/ny_vrdb.duckdb` — New York's NYSVOTER
statewide file (13.54M registrants; individual party enrollment + full DOB +
per-event vote history, all ~100% populated) — via
`scripts/diag_ny_turnout_party.py`, `scripts/diag_ny_primary_participation.py`,
and `scripts/diag_ny_electorate_extras.py`. Competitiveness from
`forecast_predictions`. Appendix C additionally compares the file against the New York State
Board of Elections' published enrollment series, via
`scripts/diag_ny_enrollment_validation.py` — the one place in this paper where an external
source enters. Each figure below traces to one of these scripts.*

*Load-bearing caveats, both temporal, both revised 2026-08-08 after external review.*

***(1) Party of record is CURRENT enrollment, not enrollment at the election analysed.**
NYSVOTER carries one enrollment field and no history of it, so every party-resolved
historical cut here reads "voted in year Y, enrolled X in 2026." New Yorkers may change
enrollment, so those are not the same population. The drift is bounded, not assumed: a closed
primary is open only to enrollees, so everyone in §III's numerators was enrolled at the time,
and **0.7–1.4% of them are enrolled blank today** — under half a point a year of movement out
of the major parties among primary participants. Movement **between** the two major parties
leaves no trace in a single extract and is **not** bounded here. §II's cross-sectional
results, which describe the 2026 roll, are unaffected. **Appendix C** bounds this jointly with
(2) against NYSBOE's published enrollment series.*

***(2) The file is the current roll**, so voters who cast a past ballot and were since purged
are absent. Participation **rates** are denominated on registrants enrolled in time to vote
(§I, §III). Composition **shares** are less denominator-sensitive but are not immune, and an
earlier version of this line called them "robust" and claimed the bias "hits every group
equally" — neither was established. Measured instead, using inactive status as the visible
pre-purge state: attrition is near-flat across parties (0.35pp spread) and **not** flat across
age — the under-30 band leaves at twice the 45–64 rate, so the age shares understate youth in
past electorates. See "Boundary of inference" and **Appendix C**, which puts an external
ceiling of **1.39 points** on (1) and (2) combined.*

*"NOPARTY" = New York's blank/no-party enrollment; its lean is never imputed.*

---

## Abstract

How many people vote is the wrong question for understanding how a state is governed; the right
one is who. New York has settled most local offices in odd-year Novembers and most legislative
seats in closed primaries, and its voter file records each registrant's party of record — so
the question can be answered with the variable that matters most. Using the full statewide
registration file and per-election vote history for **13,540,505** registrants, this paper
measures the composition of each general electorate and of each nominating electorate. The
off-year electorate is markedly older: the 65-and-over share rises from **28.2%** of the 2024
presidential electorate to **41.6%** in the 2023 odd-year general while the under-30 share
collapses from **14.1%** to **6.0%**, and a decomposition attributes that rise several times
more to differential turnout than to the age structure of the rolls. Party of record shows the
graying is not partisan-neutral: in the odd-year electorate the Republican median voter is
**62** against the Democratic **54**, an eight-year gap that is roughly five years at the
presidential level. A quarter of registrants, **25.3%** of the active roll, enroll in no party;
they are the youngest bloc in the state, the least participating, and the least likely to
appear in matched political-contribution records, and while unaffiliated they are barred by law
from the nominating stage. Participation in those primaries runs from under two percent to the
high teens, and by registration only **21** of **176** congressional and Assembly districts are
within five points. Recent registration cohorts are markedly less likely to enroll in a party,
so the excluded bloc is growing. New York has since legislated part of the remedy these
patterns point to — Chapter 741 of 2023 moved many town and county elections to even years,
first effective in 2026 — which makes the electorates measured here the pre-transition
baseline. The paper reports composition, not preference, and imputes no partisan sympathy to
unaffiliated registrants.

**Keywords.** off-cycle elections; election timing; voter file; party registration; closed
primaries; turnout composition; unaffiliated voters; nominating electorate; state legislatures;
New York

---

## The question

How *many* people vote is the wrong question for understanding how a state is
governed. The right one is *who* — and in New York the answer changes
dramatically with the calendar, because local offices have been filled in
odd-year Novembers and most legislative seats are settled in low-turnout closed
primaries. New York lets us answer "who" with the variable that matters most:
**individual party of record.**

The short answer: **the people who decide New York are older than the state, the
graying is not partisan-neutral, and a quarter of registrants cannot take part in the
nominating stage while they remain unaffiliated.** That the off-year electorate is older
replicates a sixty-year-old literature and is established here in **Appendix A**, where it
belongs. What New York's party of record adds — and what we have not found shown at this
scale on individual records — is that the graying falls hardest on *one party's* electorate,
that the bloc it excludes is the youngest and least engaged in the state, and that the rolls
are shifting toward exactly that bloc.

---

## I. The graying is not partisan-neutral — the Republican electorate ages hardest

This is the cut Washington's data cannot make, and it is this paper's contribution.
Appendix A establishes the premise the off-cycle literature already predicts: as salience
falls, the electorate ages. The question that premise leaves open is *whose* electorate
ages — and the answer is not symmetric. Share of each party's voters who
are 65+:

| Election | DEM | REP | NOPARTY | OTHER |
|---|--:|--:|--:|--:|
| Nov 2024 (pres) | 28.7% | 32.4% | 22.2% | 27.0% |
| Nov 2025 (odd) | 32.1% | **42.8%** | 30.6% | 35.1% |
| Nov 2023 (odd) | 41.6% | 43.5% | 39.3% | 37.4% |

<sub>Shares are of each party's actual voters. The Das-Gupta decomposition in
[`ny-electorate-extras.md`](ny-electorate-extras.md) §3 uses all-roll-matched bases for the
2024 presidential row (DEM 29.0 / REP 32.7 / NOPARTY 22.4), ~0.3pp higher.</sub>

Median age within each party tells the same story — in the 2025 off-year, the
**Republican median voter is 62 vs the Democratic 54**, an 8-year gap that was
only ~5 years in the presidential electorate. The GOP's 65+ share jumps from 32%
(presidential) to 43% (odd-year), and its under-30 participation collapses to
roughly a third of the presidential level. The off-year electorate is not just
older; **its Republican wing ages most.**

That New York's *Republican* wing ages hardest is itself a New York fact, not a
law of nature: the deep-red companion, [`who-decides-idaho.md`](who-decides-idaho.md),
finds the opposite structure — Idaho's Democratic and Republican electorates age
almost identically (65+ share 31.5% vs 31.7% in 2024), and the youth that drops
off in low-salience contests sits in the *unaffiliated* and minor-party blocs, not
in one major party. Whose electorate ages is contingent on the state; *that* the
low-salience electorate is older, and that the young who exit are the least
partisan, recurs in both.

But the *composition* heuristic that "older off-year electorate ⇒ more
Republican" **does not hold in deep-blue New York.** The DEM–REP share gap among
actual voters is event-driven, not turnout-driven — it swings from +15.6 (2023)
to +33.2 (2025) depending on what's on the ballot — and the unaffiliated, not
either party, are the ones who drop out (25.5% of the roll, but only 16–22% of
voters). And in even-year federal contests Republicans out-turn Democrats at
*every* age, yet that discipline inverts off-cycle: in the 2025 general, Democratic
under-30 turnout (32.8%) was nearly **double** Republican (16.6%) — the share of each
party's under-30 active registrants **enrolled on or before election day** who returned a
ballot. Party-resolved, the signal lives in age structure and youth mobilization, not in a
simple rightward headcount shift.

---

## II. The unaffiliated quarter: young, disengaged, and outside the primary

A quarter of New York registrants (25.3% of the active roll; 25.5% of the full roll) enroll in no party.
This section is **cross-sectional** — it describes the 2026 roll, so the temporal caveat on
party of record does not reach it.

| | median age | %65+ | %18–29 | 2024 turnout | matched donors / 1k |
|---|--:|--:|--:|--:|--:|
| DEM | 49 | 26.5% | 18.0% | 57.8% | 55.3 |
| REP | 55 | 30.4% | 14.9% | **68.7%** | 48.5 |
| NOPARTY | **42** | 17.4% | **25.6%** | **49.3%** | **22.7** |

<sub>"Matched donors / 1k" is the rate at which each party's active registrants appear in the
donor paper's matched contribution panel (FEC plus New York State disclosure, full-name key) —
not a measure of giving in general, and not a dollar figure. The ordering is not an artifact of
that match specification: on the retired 308,032-voter panel the NOPARTY-to-DEM ratio is 0.375
against 0.412 here.</sub>

The blank bloc is the **youngest, least likely to vote, and least likely to appear as a
political donor** group in the state. What it is *not* is measured here: we observe no
information level, no ideology, and no partisan sympathy. And under New York's **closed**
primaries, registrants are ineligible to vote in a party primary while they remain
unaffiliated — a quarter of the roll, at any given deadline, with no voice at the nominating
stage. Enrollment can be changed, and the statutory deadline for doing so falls in February
of the primary year; the finding is that a quarter of registrants do not.

---

## III. The nominating electorate is smaller still

New York settles most legislative seats in party primaries that only enrollees
may vote in. Participation rate by enrollment — voters as a share of that party's active
registrants **enrolled on or before that primary**:

| Primary | DEM | REP | NOPARTY | OTHER |
|---|--:|--:|--:|--:|
| 2024 Presidential | 4.8% | 4.9% | 0.1% | 0.2% |
| 2024 State/Congress | 7.7% | 1.7% | 0.1% | 0.6% |
| 2022 State/Congress | 17.9% | 18.4% | 0.6% | 2.0% |
| 2021 (odd-year) | 16.9% | 5.0% | 0.5% | 1.5% |

Two facts: primary turnout runs from single digits to the high teens — the
electorate that *nominates* is a small fraction of the one that *elects* — and
the **25.3% enrolled "blank" are structurally absent** (≈0.1–0.6%). In blue New York the
**Democratic primary draws far more participation than the Republican** in the contests that
matter most locally (2021 odd-year DEM 16.9% vs REP 5.0%; 2024 state DEM 7.7% vs REP 1.7%).

**What the NOPARTY cells actually are.** An earlier version read the 0.1–0.6% residual as
"nonpartisan/special races." That reading does not survive its own test. A closed primary is
open only to enrollees, so a voter recorded in one who is enrolled blank *today* changed
enrollment in between — and the **2024 presidential** primary settles which mechanism
dominates, because no nonpartisan contest appears on that ballot anywhere in the state and its
blank cell is still non-zero. Read the other way, these cells are the paper's switching bound:
of the voters in each closed primary, **0.7% (2024) to 1.4% (2021) are enrolled blank today**.
That is the only enrollment drift a single extract can see; movement between the two major
parties is invisible here.

> **The denominator of this table has been wrong twice, in opposite directions, and the
> record of both is kept here.** Every rate in §III and the under-30 pair in §I is
> **roll-denominated**: a participation rate whose denominator is a slice of the registration
> file. Appendix A and the rest of §I are **electorate**-denominated — the set of people who
> voted in a past election cannot change when registrants are added — which is why they have
> been stable throughout and why the split between the two identifies the denominator as the
> cause whenever these figures move.
>
> **2026-08-01.** §II and §III did not reproduce when this paper's verifier was converted from
> printing values to asserting them, and both were recomputed against the roll as it then
> stood, with the divergence attributed to growth in the file.
>
> **2026-08-08, after external review: that recomputation introduced an error and misdiagnosed
> its own cause.** A participation rate must be denominated on the people who *could* have
> voted — active registrants enrolled on or before the contest. The recomputed figures were
> denominated on the whole current active roll, which counts someone who registered in 2025 as
> a 2021-primary non-voter. **20.55%** of today's active roll registered after the 2021
> primary, and restoring the cutoff moves the rates **+0.13 to +2.67 points** across the eight
> major-party cells, largest on the oldest cycles. The table above is on the corrected basis.
>
> Three things make this checkable rather than a matter of judgment. The contemporaneous basis
> reproduces the figures this paper carried *before* 2026-08-01 — 16.9 and 17.9 — exactly.
> Roll growth explains none of the gap: the pinned and live rolls return the uncorrected 14.26%
> alike, to the last digit. And `scripts/diag_ny_primary_participation.py`, which the Methods
> block names as this section's provenance, has applied the cutoff since its first commit — so
> for one week the paper and its own cited script disagreed by up to 2.67 points, and both were
> public. The lesson is the one this series already writes down in the other direction: when a
> verifier and a paper disagree, the verifier is not automatically right.
>
> **No finding changes under either correction.** The blank bloc is still the youngest and
> least participating group by a wide margin; Democratic primary participation still far
> exceeds Republican in the odd-year and state contests; the ordering within every column is
> unchanged; and §I's under-30 ratio moves from 1.96× to 1.97×.
>
> The donors-per-thousand column moved for a second and unrelated reason: it was still built
> on the pre-2026-07-27 New York match (308,032 voters) rather than the full-name-key
> specification now used throughout the series (558,017). It is rebuilt on the current panel
> here. That change raises all three figures and leaves their ordering and the ratio between
> them substantially intact.
>
> **The roll is pinned, so drift cannot recur silently.** New York had no snapshot on the
> reasoning that a static FOIL extract cannot move; it moved, and a reload is invisible to a
> paper that names no snapshot. `scripts/pin_ny_roll.py` freezes it the way Washington's is:
> **`ny_paper_roll`, 13,540,505 registrants, of whom 12,448,034 are
> active.** Every roll-denominated figure in §II and §III is computed against that snapshot,
> and `scripts/verify_who_decides_ny.py` fails rather than falling back if it is absent.
> Appendix A and Section I continue to read the file directly, correctly: an electorate is a set of
> people who already voted, and it does not move. Re-pinning requires an explicit `--force`.
>
> Pinning changed no figure — all asserted values reproduced against the snapshot on the
> day it was taken, which is the check that distinguishes freezing a number from altering one.
> The snapshot was re-taken on **2026-08-08** to add each registrant's registration date, which
> is what the corrected denominators require and what its absence had made impossible. That
> re-pin is likewise value-identical: every party, active-status and birth-year aggregate is
> unchanged, because the field was appended to the tie-break key rather than inserted into it.
>
> **The identity of the underlying extract, so that a reproduction starts from the same
> bytes.** The pin freezes a derived table; the source it derives from is
> `ALLNYVOTERS20260629.zip`, 928,142,538 bytes, SHA-256
> `ea0b97ccb027b6bfce571d17f7ef19b8135e1c10ed8cbbec136f4b73e3ef4807`, obtained by FOIL request
> to the New York State Board of Elections and dated 29 June 2026. Publishing the digest
> identifies the source without redistributing it, and covers the sections that read the file
> directly rather than through the pin.
>
> One data-quality note the pin surfaced, disclosed because it is checkable: the NYSVOTER
> extract carries **53 registration identifiers twice** (36 of them among active registrants),
> and these are not duplicate copies — 8 of the pairs disagree on party, 25 on congressional
> district, 1 on birth year. The snapshot keeps one record per identifier, chosen
> deterministically, so it holds 13,540,505 registrants against the file's 13,540,558 rows.
> The difference is four orders of magnitude below anything this paper prints and moves no
> figure in it; it is reported rather than absorbed because a roll ought to be one row per
> registrant and the raw file is not.

---

## IV. The registration map: one-sided almost everywhere

Most New York districts carry a large registration advantage for one party.
District counts by registration lean (DEM% − REP%, active roll), on **symmetric**
bands:

| Level | D 40+ | D 20–40 | D 5–20 | Within ±5 | R 5–20 | R 20–40 | R 40+ |
|---|--:|--:|--:|--:|--:|--:|--:|
| Congressional (26) | 9 | 3 | 7 | **4** | 3 | 0 | 0 |
| Assembly (150) | 55 | 31 | 19 | **17** | 21 | 7 | 0 |

Only **21 of 176** congressional and Assembly districts — 4 of 26 and 17 of 150 — are within
five points on registration; 19/26 and 105/150 lean Democratic. The asymmetry runs one way:
**no New York district at either level is R+40**, so on the same threshold that makes 64 seats
safe for Democrats, none is safe for Republicans.

<sub>The bands were asymmetric until 2026-08-08 — 40+/20–40/5–20 on the Democratic side against
5–20/20+ on the Republican, so a D+25 district was labelled "Likely D" and an R+25 "Safe R."
The symmetric table above is the same data. The ±5 count, which is the finding, was never
affected; the seven Assembly seats formerly shown as "Safe R" are R+20–40.</sub>

**What this does and does not establish.** It is a registration structure, not an election
result. It says most New York districts are one-sided enough that the nominating stage is where
a serious contest is most likely to occur — which is the classic Key (1949) expectation and
what motivates §III. It does **not** establish that the November general is a foregone
conclusion or that the primary decides the seat: registration is not a vote, a dominant party's
primary may itself be uncontested, and incumbency, candidate quality and differential turnout
all move general-election outcomes away from registration. The companion safe-seat paper
withdrew a stronger version of that inference on **observed margins**, which are better evidence
than registration; it is not reinstated here on weaker evidence. Tracing each seat through both
its primary and its general to classify where a real choice existed is the test that would
settle it, and it is future work.

---

## V. A leading indicator: recent registration cohorts are choosing no party

The blank bloc is not a legacy artifact — it is *growing through new
registration*. Party mix of each year's **registration cohort** still on the roll — the people
whose registration record is dated that year. These are cohorts, not people observed over time,
so they show what successive intakes chose at registration, not individuals abandoning
affiliations:

| reg year | %DEM | %REP | %NOPARTY | median age at reg |
|---|--:|--:|--:|--:|
| 2008 | 57.8% | 16.2% | 20.7% | 29 |
| 2016 | 51.5% | 18.5% | 25.6% | 30 |
| 2020 | 40.9% | 21.3% | 33.7% | 30 |
| 2024 | **39.7%** | 22.1% | **35.6%** | 29 |

The Democratic share of each cohort has fallen ~18 points since 2008 while
the no-party share has risen ~15 points (Republican roughly flat). The
electorate that will decide future off-years is registering at a steady ~29–30
but is **increasingly choosing no party** — and, per §II–III, that choice is
also a choice to sit out the nominating stage. (Survivorship caveat: only
registrants still on today's roll appear; read the *trend in party mix*, which is
composition-based, as the robust cut.)

**A cohort is not the same thing as first-time registrants, and the difference runs against
this finding rather than for it.** `registration_date` records the most recent registration
transaction, not necessarily an initial one: a move, a name change or a party change can write
a new date. That is measurable, because someone who voted *before* their own registration date
was demonstrably registered earlier. On that test at least **9.96%** of the 2020 cohort and
**13.91%** of the 2024 cohort are re-registrations rather than first-time entrants — lower
bounds, since a re-registrant who never voted before leaves no trace.

Those re-registrants are **more** Democratic and **less** unaffiliated than the cohorts that
contain them — in 2024, **48.9%** Democratic and **25.1%** no-party against **38.2%** and
**37.3%** for the rest, at a median registration age of 38 against 28. So they pull the printed
figures *toward* the party column and *away* from the blank one, and the genuine first-time
trend is steeper than the table shows, not shallower.

The table is left on the whole-cohort basis deliberately: prior-vote detection needs vote
history preceding the cohort year, and this file's history begins in 2016, so the 2008 and 2016
rows cannot be split at all. Publishing two rows on one basis and two on another would be a
worse defect than the one it fixed. For the same reason **the two percentages above are not
comparable to each other** — 2024 has an eight-year detection window against 2020's four, so the
gap between them measures observability, not a rise in re-registration.

---

## Boundary of inference

- **Party of record is 2026 party.** The single largest limitation, and the one a reader
  should carry into every historical table with a party column. See caveat (1) in the front
  matter for the bound: 0.7–1.4% of each closed primary's voters are enrolled blank today,
  and major-party-to-major-party movement is unobservable in a single extract. Aggregate
  enrollment by county and district is published historically by the State Board of Elections
  and is the natural external validation; it is not yet incorporated here.
- **Turnout rates are denominated on contemporaneous eligibility.** Every rate in §I and §III
  counts only registrants enrolled on or before the contest. That is the correct
  specification and it is not what this paper printed between 2026-08-01 and 2026-08-08 —
  see the note under §III. Composition *shares* (Appendix A, §I) are a different cut and
  carry the survivorship caveat below rather than this one.
- **Survivorship, measured rather than assumed.** Voters purged since an election are absent
  from the file, and purging is invisible in a single extract. Using inactive status as the
  visible pre-purge state: among 2021 general voters, the inactive rate spans 3.23–3.58%
  across the four party buckets — a 0.35pp spread, which is what an earlier version was
  reaching for when it said the bias "hits every group equally," and it is close enough to
  support cross-party comparison within a year. Across **age** it does not hold: among 2023
  general voters, 2.69% of the under-30 band is now inactive against 1.34% of the 45–64 band.
  So the age composition shares are biased toward **understating** youth in past electorates.
  This is a proxy for attrition, not a measurement of it.
- **NOPARTY lean is never imputed.** The blank bloc's partisan sympathies are
  unobserved; we describe its age, turnout, and matched-donor rate, not its
  hidden preference, and we do not characterise its political information (its federal
  *giving*, separately, leans ~2:1 Democratic — see
  [`donor-class-and-the-electorate.md` Finding 3](donor-class-and-the-electorate.md)).
- **Vote-history formats.** NYSVOTER mixes ~6 county-specific history formats per
  election; the normalized parser is validated against known turnout (2024
  presidential ≈ 7.4M, the credible figure for the current roll).
- **Competitiveness (§IV uses registration; the safe-seat paper uses observed
  margins).** Registration lean is a structural proxy, not a vote result; it
  corroborates the observed map rather than replacing it.

---

## What it means

New York lets us put a party label on every filter between the registered
population and the decision: an older general electorate, an older-still and
asymmetrically-Republican off-year electorate, a closed primary that a young,
disengaged quarter of the state cannot enter while unaffiliated, and a district map that is
one-sided almost everywhere. The reform implication is the one Washington's data pointed to —
**move local elections on-cycle** — but New York adds the evidence that the off-year distortion
is not partisan-neutral and that the unaffiliated, fastest-growing slice of the electorate is
precisely the slice most excluded by the calendar and primary structure. Combined with the
donor-class paper, the picture is a series of narrowing, increasingly
unrepresentative gates — who registers, who votes, who votes in the primary, and
who pays.

**New York has already begun the change, which reframes this paper's contribution.**
Chapter 741 of the Laws of 2023 moved many town and county offices — supervisor, town board,
town clerk, highway superintendent; county executive, comptroller, legislator — from odd-year
to even-year Novembers, effective 1 January 2025 and first operative in 2026. It excludes New
York City entirely, and it cannot reach sheriff, county clerk, district attorney or the
judgeships, whose terms are fixed by Article XIII § 13 of the State Constitution; a
constitutional amendment addressing those is advancing. The statute was challenged and upheld
at every stage — reversed in the Appellate Division, Fourth Department, affirmed unanimously by
the Court of Appeals in *County of Onondaga v. State of New York* (16 October 2025), with
certiorari denied by the U.S. Supreme Court on 23 March 2026 and a parallel federal suit
dismissed in the Eastern District on 29 June 2026.

So the recommendation is not a proposal here; it is a policy in its first cycle. That changes
what this paper is for. The 2023 and 2025 odd-year electorates measured above are the
**pre-transition baseline** for a live natural experiment, on the offices the statute actually
moves, in a state that publishes party of record. Comparing the composition of the same classes
of local electorate before and after synchronisation — rather than comparing differently
constituted odd- and even-year ballots, which is all the present design can do — is a far
stronger test of election timing than anything reported here, and the data to run it begins
accumulating in November 2026.

---

## Related work

This paper's mechanisms are established; the contribution is the party-resolved,
individual-record measurement on 13.5M New York registration and vote records, and
the finding that the Republican electorate ages hardest. It sits in these literatures:

- **Turnout composition by salience (surge-and-decline).** Campbell, "Surge and
  Decline" (1960); Wolfinger & Rosenstone, *Who Votes?* (1980); Leighley & Nagler,
  *Who Votes Now?* (2013). Appendix A's presidential→off-year age gradient is this,
  measured directly. Plutzer, "Becoming a Habitual Voter" (2002) frames the young-adult
  drop-off in Appendix A.
- **Off-cycle election timing, composition, and representation.** Anzia, *Timing and
  Turnout* (2014); Hajnal & Trounstine, "Where Turnout Matters" (2005); Hajnal, Kogan
  & Markarian, "Who Votes: City Election Timing and Voter Composition" (2022); Einstein
  et al., "The Gray Vote" (2024) — the closest analog to the age result. Motivates the
  on-cycle remedy.
- **The primary as the real election under one-party dominance.** V.O. Key, *Southern
  Politics in State and Nation* (1949); Hirano & Snyder, *Primary Elections in the
  United States* (2019). Section IV's safe-seat map is a modern, party-resolved instance.
- **Primary-electorate representativeness (the tension).** Sides, Tausanovitch, Vavreck
  & Warshaw, "On the Representativeness of Primary Electorates" (2020) — distinguished
  here: our claim is composition and closure (Section III), not ideological extremism.
- **Independents / the unaffiliated.** Klar & Krupnikov, *Independent Politics* (2016);
  Fiorina, "The (Re)Nationalization of Congressional Elections" and the broader
  dealignment literature — the frame for the young, disengaged, locked-out unaffiliated
  quarter (Section II) and the new-registrant abandonment of party labels (Section V).
- **Voter-file / individual-level method.** Ansolabehere & Hersh, "Validation: What Big
  Data Reveal About Survey Misreporting and the Real Electorate" (2012); Hersh, *Hacking
  the Electorate* (2015). On the current-roll survivorship caveat (Boundary of inference):
  Huber, Meredith, Morse & Steele, "The Racial Burden of Voter List Maintenance Errors:
  Evidence from Wisconsin's Supplemental Movers Poll Books," *Science Advances* 7(8):eabe4498
  (2021), on list-maintenance error; and Feder & Miller, "Voter Purges After *Shelby*,"
  *American Politics Research* 48(6):687–692 (2020), on differential purge rates — the
  mechanism that would make this paper's attrition non-neutral. An earlier version cited a
  single work combining the two, attributing Huber et al.'s title and journal to Feder and
  Miller; they share no authors.

---

## Methods & reproducibility

```
python scripts/load_ny_voters.py                        # NYSVOTER FOIL -> ny_vrdb.duckdb
python scripts/diag_ny_turnout_party.py --rebuild       # turnout by age x party (App. A, I)
STATE=NY python scripts/diag_ny_primary_participation.py # closed-primary participation (II)
STATE=NY python scripts/diag_ny_electorate_extras.py     # blank bloc / decomposition / trend / safe-seat (I-V, App. A)
python scripts/pin_ny_roll.py                            # freeze the roll-denominated denominator
python scripts/diag_ny_enrollment_validation.py          # vs NYSBOE published enrollment (App. C)
python scripts/verify_who_decides_ny.py                  # assert every figure above against the file
```

All inputs are public records (NY NYSVOTER under its lawful-use FOIL terms). See
[`data-sources-and-reproducibility.md`](data-sources-and-reproducibility.md) for
the source ledger and method notes, and
[`ny-turnout-by-party-age.md`](ny-turnout-by-party-age.md) /
[`ny-electorate-extras.md`](ny-electorate-extras.md) for the full underlying
tables.

---

## Appendix A — Validation: the off-year electorate is older

**This is a replication, and it is placed here for that reason.** That the electorate ages
as salience falls has been established since Campbell (1960) and measured for local
elections by Anzia (2014); New York adds scale and individual records, not a new claim. The
paper's contribution begins at Section I, which asks the question this literature leaves
open — *whose* electorate ages. This appendix exists so that premise is measured rather
than assumed, and so a reader can check it against the sources in Related work.

Share of the general-election electorate by age band:

| Election | Type | 18–29 | 30–44 | 45–64 | 65+ | median |
|---|---|--:|--:|--:|--:|--:|
| Nov 2024 | Presidential | **14.1%** | 23.1% | 34.6% | 28.2% | 53 |
| Nov 2022 | Midterm | 9.8% | 21.1% | 38.5% | 30.6% | 56 |
| Nov 2025 | Off-year | 11.5% | 21.0% | 33.1% | 34.4% | 56 |
| Nov 2023 | Off-year | **6.0%** | 15.9% | 36.5% | **41.6%** | 61 |

As the contest shrinks (presidential → midterm → odd-year), the under-30 share
collapses (14% → 6% by 2023) and the 65+ share swells (28% → 42%); median age
rises from 53 to 61. **Behavior, not rolls.** A Das-Gupta decomposition of the
65+ share rise from 2024 to 2025 attributes it several times more to differential
**turnout** than to the registration age structure (rate effect **+2.5 to +8.7 pts**
vs composition +0.6 to +1.5, depending on party — a 3.6× ratio for Democrats up to
12.5× for the unaffiliated). What the decomposition establishes is that the age gradient is a
**participation** pattern rather than a registration artifact. It does not establish the
cause of the participation gap.

**And "odd year" is not one treatment — this table says so itself.** The two odd-year
electorates differ enormously: 2023 turned out 2,336,272 voters at 41.6% aged 65+, while 2025
turned out 4,039,285 — **1.73×** as many — at 34.4%. Different offices, candidates, salience
and geography sit behind those two rows, so an odd-year November is a bundle of conditions, not
a manipulated variable. No election was moved in this design. The off-cycle literature cited
above supports the causal timing claim; what these data can say is that they are consistent
with it. Chapter 741 (see "What it means") is about to supply the design that would settle it.

Like Section I, this table is **electorate**-denominated: it describes the set of people who
actually cast a ballot in a past election, which cannot change when new registrants are
added to the roll. That is why all of its cells reproduced unchanged through the
2026-08-01 recomputation that moved Sections II and III — see the note under Section III.

---

## Appendix C — External validation against NYSBOE published enrollment

The two limitations in the front matter — current-party labelling and current-roll
survivorship — distort the same quantity in the same direction: the party composition of the
people who were on the roll at some past date. So one external number bounds their **combined**
size, and New York publishes it. NYSBOE's *NYSVoter Enrollment by County, Party Affiliation and
Status* gives statewide enrollment by party, split active/inactive, twice a year back to 2006.

For each snapshot date *D* we compare NYSBOE's published active shares against the shares among
registrants in our extract who registered on or before *D* and are **active today**. The gap is
the net of party switching, purges, active-to-inactive transitions and NYSBOE's own revisions.

| Snapshot | Precedes | DEM | REP | NOPARTY | OTHER | file/published actives |
|---|---|--:|--:|--:|--:|--:|
| 2026-02-20 | **control** | -0.17 | +0.10 | -0.26 | +0.33 | **98.08%** |
| 2025-11-01 | the 2025 general | -0.17 | +0.10 | -0.24 | +0.31 | 96.63% |
| 2024-02-27 | both 2024 primaries | -0.34 | +0.57 | -0.16 | -0.07 | 91.89% |
| 2022-02-21 | the 2022 primary | -1.02 | +1.15 | +0.20 | -0.33 | 84.89% |
| 2021-02-21 | the 2021 primary | -1.06 | **+1.39** | +0.11 | -0.44 | **78.64%** |

<sub>Gaps in percentage points of the active roll; positive means the surviving 2026 sample
over-represents that bucket. February dates are New York's party-change deadline, which is the
eligibility date that governs a closed primary. Buckets map as NOPARTY = NYSBOE's BLANK and
OTHER = CON + WOR + OTH. Derived by
[`scripts/diag_ny_enrollment_validation.py`](../scripts/diag_ny_enrollment_validation.py).</sub>

**Read the control row first.** It sits about four months before the extract, so drift has had
almost no time to accumulate, and its gaps are -0.26 to +0.33. Had the method been
mis-specified — wrong active filter, wrong bucketing, wrong denominator — that row would be off
too and everything below it would be measuring our own error rather than New York's.

Three things follow.

1. **The bound is small, and it is a ceiling.** The largest historical gap is **1.39 points**,
   on the Republican share five and a half years back. Nothing here decomposes that into
   switching versus purging, and it should not be used as a correction factor.
2. **The direction is against the paper's headline, which is the useful way for it to run.**
   The surviving sample under-represents Democrats and over-represents Republicans at every
   historical date, so a 2026-labelled reconstruction makes past electorates look slightly
   *more* Republican than they were. The §I finding is that the Republican electorate ages
   hardest; a bias that inflates the Republican share of past electorates works in the same
   direction as that finding and is therefore a live caution, not a reassurance. It is an order
   of magnitude smaller than the effects §I reports — a 1.39-point share gap against an
   eight-year median-age difference — but it is why §I leads with median age and 65+ share
   *within* each party rather than with the parties' relative sizes.
3. **Attrition is large and composition is not.** Only **78.64%** of the registrants NYSBOE
   counted as active in February 2021 are active in this file — more than a fifth of that roll
   is gone — and yet the party composition moved by at most 1.39 points. That is the
   quantitative version of the claim an earlier draft made without evidence when it called
   composition shares "robust". They are more robust than the turnout rates, and now there is a
   number for how much.

What this does **not** address is the reviewer's sharpest point: aggregate enrollment cannot
recover any individual's party at a past election, so it validates composition without
recovering party-at-election. That remains open, and no source we know of closes it for New
York without contemporaneous individual snapshots.

---

## Appendix B — Section numbering, before and after 2026-08-06

The paper was reordered on 2026-08-06 to open on its party-resolved result rather than on
its replication. **Only the order and the numbering changed; no figure, table cell, or claim
was altered by the reordering.** This map is recorded because earlier documents in this
series — including the append-only
[`electoral-health-audit-log.md`](electoral-health-audit-log.md) — cite these sections by
number, and a silent renumbering would re-point those citations at different content.

| Before | After | Content |
|---|---|---|
| §I | **Appendix A** | The off-year electorate is older (replication / validation) |
| §II | **§I** | The graying is not partisan-neutral |
| §III | **§II** | The unaffiliated quarter |
| §IV | **§III** | The nominating electorate |
| §V | **§IV** | The registration map (titled "Safe-seat New York" until 2026-08-08) |
| §VI | **§V** | Recent registration cohorts choosing no party |

So a pre-2026-08-06 reference to "NY §III/§IV" — the roll-denominated blocks recomputed on
2026-08-01 — is a reference to what are now **§II and §III**.
