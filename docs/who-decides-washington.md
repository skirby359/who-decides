# Who Decides Washington?

### Who Returns the Ballot? Age Composition in Washington's Odd-Year Electorate, 2021–2025

**Stephen Kirby** · Tikor Consulting · July 2026

*AI-assisted analysis; every figure is independently reproducible from public records
via the cited open-source scripts (e.g. `scripts/verify_who_decides_wa.py`). Contact:
kirby@tikorconsulting.com.*

## Abstract

Many of Washington's local offices are filled in odd-numbered November elections,
when turnout is far below presidential-year turnout. This paper asks *who returns those
ballots*. Joining Washington's statewide voter-registration database — a
5.51-million-voter roll linked to 27.1 million individual vote-history records and each
voter's year of birth — it measures the age composition of every November general
electorate from 2021 through 2025. The central finding is descriptive: Washington's
odd-year ballot-return electorate is markedly older than its presidential electorate.
Voters 65 and older were 36.7%, 40.2%, and 40.3% of the 2021, 2023, and 2025 odd-year
electorates, versus 28.5% in the 2024 presidential electorate; voters 18–29 fell from
14.2% in 2024 to roughly 7.6% off-cycle. The result survives validation against
certified ballot counts, a formal worst-case bound for voters missing from the
current-roll reconstruction (confirmed against a second, closer-in-time roll snapshot),
alternative birth-year imputations, all 39 counties, and the exclusion of any single
off-year; the off-year electorate is older than the registered roll and the citizen
voting-age population as well. Individual records further show it is largely the
presidential electorate's *habitual core* — 92–97% of off-year voters also vote in
presidential years, while the peripheral voters who fall away off-cycle are
disproportionately young. The paper measures ballot return, not votes cast in specific
down-ballot contests, and does not estimate partisan or policy consequences. Its contribution is a validated, individual-record measurement
of age composition across the presidential–midterm–off-year salience gradient in a
universal vote-by-mail state where formal ballot-access friction is comparatively low.

**Keywords:** election timing; voter turnout; local elections; age representation;
voter files; Washington; vote by mail; off-cycle elections.

---

## The question

Most coverage of "turnout" asks how *many* people vote. The more consequential
question for how a state is governed is *who* — because the answer changes with
which election you look at. Washington runs many of its most local offices — city
councils, school boards, port and fire commissions, and many county and judicial races — in
**odd-numbered, off-cycle Novembers** (RCW 29A.04.321 limits the odd-year statewide
general election chiefly to city, town, and district offices, certain county
positions, and state measures), when only **~38%** of registered voters return a
ballot. This paper measures, at the individual level, who that ~38% is.

The short answer: **the observable odd-year ballot-return electorate is markedly
older than the presidential one.** It is not a smaller copy of the presidential
electorate; it is an older one.

**What is measured.** This paper measures **ballot return** — whether a registered
voter cast a November ballot — at the individual level. It does *not* observe whether
that voter marked a specific city-council, school-board, port, fire, judicial, or
county contest; voter-file records show participation in an *election*, not a *contest*
(Lucero et al. 2025). That distinction matters most for the **even-year
counterfactual**: if local races were consolidated onto longer even-year ballots, some
added voters would return a ballot but skip the local race. For the **odd-year
electorate described here**, ballot return is a closer proxy for local-election
participation, because Washington's odd-year general election is dominated by local and
district contests, with only occasional statewide measures — but it remains an
election-level measure, not a contest-level one. Appendix F treats roll-off as the live
counterargument.

---

## Data and validation

**Source.** `voting_history` (27.1M records) joined to `voters` (year of birth,
~100% coverage) from Washington's standard statewide VRDB extract (April 2026;
provenance and use terms in Appendix B). Age is taken as election year − birth year;
cohorts are assigned per election. November generals only, 2021–2025.

A hostile reading of any voter-file study is: *you did not measure the electorate;
you measured the electorate that remains observable in your current voter file.*
Because the vote-history table is keyed to a current (2026) roll, a voter who cast a
ballot in 2021–2024 but has since died, moved, or been canceled is absent. If those
departed voters were a random slice, coverage loss would be harmless; if they skew
young, the finding would be inflated. Both are checkable, and the answers favor the
finding.

**Coverage is high, and the lowest-coverage case is bounded directly.** The
reconstruction is benchmarked against certified WA Secretary of State ballot counts
(`results.vote.wa.gov`). "In file" is distinct voters in the cumulative vote-history
table for that election; "Analyzable" additionally requires a match to the April 2026
roll with a year of birth. Analyzable coverage ranges from **90.8% in 2021 to 99.6%
in 2025** and improves sharply over time; the lowest-coverage election is the 2021
off-year, which is why the analysis reports an explicit worst-case bound (below)
rather than assuming the missing voters resemble observed voters. The validation
target is *certified ballots counted*; the vote-history file is a voter-level
reconstruction of ballot credit, expected to track the certified count closely but not
to be mechanically identical to it.

| Election | Type | Official ballots counted | In file | Analyzable (roll + YOB) | Analyzable / official |
|---|---|--:|--:|--:|--:|
| Nov 2021 | Off-year | 1,896,481 | 1,828,231 (96.4%) | 1,722,262 | **90.8%** |
| Nov 2022 | Midterm | 3,067,686 | 3,025,352 (98.6%) | 2,884,966 | **94.0%** |
| Nov 2023 | Off-year | 1,758,084 | 1,731,431 (98.5%) | 1,686,656 | **95.9%** |
| Nov 2024 | Presidential | 3,961,569 | 3,958,965 (99.9%) | 3,880,070 | **97.9%** |
| Nov 2025 | Off-year | 2,001,425 | 1,995,509 (99.7%) | 1,993,505 | **99.6%** |

**The observable attrition component skews old, and the full residual is bounded.**
A second roll snapshot (`voters_20230901`, 5.29M rows, Sept 2023) partially
characterizes voters who cast a past ballot but are absent from the April 2026 roll.
Among these **observable attrition cases**, seniors are substantially overrepresented:

| Missing-from-current-roll voters | 65+ share | 18–29 share |
|---|--:|--:|
| Cast a ballot Nov 2021 (n≈106K) | **60.4%** | 6.8% |
| Cast a ballot Nov 2022 (n≈140K) | **60.3%** | 7.1% |
| Cast a ballot Nov 2023 (n≈45K) | **69.0%** | 4.5% |

Roll departure is age-loaded more broadly (of the 504K voters, 9.5%, who left the
roll 2023→2026, 33.1% were 65+ vs 23.9% of those who stayed — consistent with
mortality and age-correlated mobility/cancellation). This evidence suggests the
current-roll reconstruction **likely understates** the senior share of past
electorates. But because not every missing ballot can be characterized from the
second snapshot, a **formal bound** is also reported that assumes nothing about the
residual: the 65+ share of the *full certified electorate* if every unobserved
residual voter (official − analyzable) were under 65, and if every one were 65+.

| Off-year 65+ share of the certified electorate | all missing < 65 (min) | observed | all missing 65+ (max) |
|---|--:|--:|--:|
| Nov 2021 (residual 9.2%) | **33.4%** | 36.8% | 42.6% |
| Nov 2023 (residual 4.1%) | **38.6%** | 40.2% | 42.6% |
| Nov 2025 (residual 0.4%) | **40.2%** | 40.3% | 40.6% |

<sub>"Observed" is the 65+ share of the analyzable electorate from the validation
table (2021 = 36.8%; the composition table's 36.7% adds a "registered on/before the
election" filter — a 0.1-point difference). Min/max apply the extreme assumption to
the residual = official − analyzable.</sub>

Even under the minimum assumption — every unobserved off-year ballot cast by someone
under 65 — each off-year electorate (**33.4% / 38.6% / 40.2%** 65+) remains older than
the presidential electorate under *its* maximum assumption (**≤30.0%**, i.e. even if
every missing 2024 ballot were 65+). The substantive result therefore does not depend
on how the residual missing voters are allocated. Two claims, kept distinct: the
observed composition estimates are **likely conservative** given the attrition
evidence, and the **formal worst-case bound** preserves the finding regardless.

**A direct check: composition barely moves under a closer-in-time roll.** The bound
above is agnostic about the missing residual; a complementary check asks whether
reconstructing from a *current* roll distorts composition at all. The database's
Sept-2023 snapshot (`voters_20230901`) still contains voters who have since left the
2026 roll, so it reconstructs the 2021–2023 electorates from a roll much closer in
time. The two reconstructions agree to within ~1.4 points — and what movement there is
runs *upward*, consistent with the current roll modestly under-counting seniors:

| Election | Current-roll 65+ | Sept-2023-snapshot 65+ | Δ |
|---|--:|--:|--:|
| Nov 2021 (off-year) | 36.8% | 38.1% | +1.4 |
| Nov 2022 (midterm) | 31.0% | 32.4% | +1.4 |
| Nov 2023 (off-year) | 40.2% | 41.1% | +0.9 |

The snapshot — which recovers older voters the current roll has since dropped — sits
slightly *higher*, not lower, so the composition finding is not an artifact of
current-roll reconstruction. The 2021 and 2022 comparisons are the cleanest checks
because the September-2023 snapshot postdates those elections. The 2023 comparison
should be read more cautiously: the snapshot predates the November-2023 election by two
months and so misses late-2023 registrants who voted that November; if those late
registrants skew younger, as new registrants often do, the September-snapshot 2023
estimate may be biased slightly *upward*. Even so, the check is reassuring — the
closer-in-time reconstruction does not make any electorate younger than the
current-roll one, and the 2021–2022 comparisons point the same way.

---

## What the data shows

The robust cut is **composition** — each age group's share of the ballot-returning
electorate. It needs no turnout denominator, rests on three consistent off-year
cycles, and (per the validation above) survives an explicit worst-case bound.

| Election | Type | 18–29 | 30–44 | 45–64 | 65+ |
|---|---|--:|--:|--:|--:|
| Nov 2024 | Presidential | 14.2% | 24.9% | 32.4% | 28.5% |
| Nov 2022 | Midterm | 10.4% | 22.9% | 35.7% | 31.0% |
| Nov 2021 | Off-year | 7.5% | 19.7% | 36.0% | 36.7% |
| Nov 2023 | Off-year | 7.4% | 19.2% | 33.2% | 40.2% |
| Nov 2025 | Off-year | 8.0% | 19.9% | 31.7% | 40.3% |

- **The off-year electorate is a senior-plurality electorate, stably so.** Voters
  65+ are **~37–40%** of it (36.7 / 40.2 / 40.3% across 2021 / 2023 / 2025) versus
  **28.5%** presidential; the 18–29 share falls from **14.2%** to **~7.6%**.
- **The senior-to-youth ratio roughly triples off-cycle** — from about **2:1**
  (presidential) to **~5:1** (off-year), with the midterm between (31.0% 65+). The
  *off-year* result is stable across three cycles; the presidential and midterm points
  are single elections (2024, 2022), so the ordering is consistent with a salience
  gradient but should not be read as a smoothly estimated curve.

**Residents, registrants, voters: an escalating age ladder.** The off-year electorate
is older than the presidential one, older than the registered roll, older than the
citizen voting-age population, and older than all adult residents. Setting the
ballot-returning electorates beside the roll (April 2026), the citizen voting-age
population, and all adult residents (both ACS 2020–24) gives a monotonic ladder:

| Population | 18–29 | 30–44 | 45–64 | 65+ | Median age |
|---|--:|--:|--:|--:|--:|
| WA adult residents (ACS 2020–24) | 20.0% | 28.3% | 30.5% | 21.1% | ~46† |
| WA citizen voting-age population (ACS 2020–24) | 19.8% | 26.7% | 30.9% | 22.6% | ~47† |
| Registered roll (April 2026) | 16.7% | 27.2% | 29.8% | 26.3% | 48 |
| 2024 presidential ballot-returners | 14.2% | 24.9% | 32.4% | 28.5% | 52 |
| Off-year ballot-returners (2021/23/25 avg) | 7.6% | 19.6% | 33.6% | 39.1% | 59 |

<sub>† Age composition from ACS 2020–24 five-year (the most recent five-year vintage;
the 2024 one-year is consistent), reproduced by `scripts/acs_wa_adult_age.py`: total
18+ residents from table B01001, and the **citizen voting-age population (CVAP)** — the
eligible-electorate benchmark, which excludes non-citizens — from table B29001. Median
ages for the two ACS rows are interpolated from the age brackets; the roll and
ballot-returner medians are computed from year of birth and are integer-year (±1)
approximations. Roll and ballot-returner figures from the VRDB
(`scripts/verify_who_decides_wa.py` #23).</sub>

The 65+ share climbs **21.1% → 22.6% → 26.3% → 28.5% → 39.1%** across the five; the
18–29 share falls **20.0% → 19.8% → 16.7% → 14.2% → 7.6%**. The median off-year
ballot-returner is **59** — about a decade older than the median registered voter (48)
and over a decade older than the median citizen-voting-age adult (~47). Residents,
eligible citizens, registrants, and voters are distinct populations, and it is
participation that moves the composition: the registered roll's senior share is stable
and low (26.3% on the full April 2026 roll; ~22–25% on the per-election eligible roll in
each of these years) while the off-year returner share reaches ~40%.

**One number for "how unrepresentative."** Collapsing the ladder into an index of
dissimilarity between each electorate's age distribution and the citizen voting-age
population (half the summed absolute cohort differences; 0 = identical) turns the
gradient into a single figure: **7.4** for the 2024 presidential electorate, **13.2**
at the midterm, and **18.5–19.9** across the three off-years — the off-year electorate
is roughly **2.5× as age-unrepresentative** of the eligible population as the
presidential one. The index is cohort-based, so its level depends on the age bins used;
its value here is comparative, not absolute.

<sub>Recorded gender shows a much smaller secondary pattern: the electorate is majority
recorded-female throughout, rising from 52.5% in the 2024 presidential electorate to
53.0–53.1% in the off-year electorates, concentrated among older voters. Because the
shift is small and administrative gender is not the paper's focus, the analysis treats
age as the primary dimension.</sub>

The mechanism is differential participation. The within-cohort rates below make it
concrete — 18–29 participation falls from **58.4%** (2024) to an off-year **~16%**
while 65+ falls only from **88.3%** to **~61%** — but they *corroborate* the
composition finding, they do not carry it:

**Within-cohort participation rate — current-roll reconstruction, not official turnout:**

| Election | Type | 18–29 | 30–44 | 45–64 | 65+ | All |
|---|---|--:|--:|--:|--:|--:|
| Nov 2024 | Presidential | 58.4% | 68.6% | 80.1% | 88.3% | 75.0% |
| Nov 2022 | Midterm | 36.4% | 52.5% | 69.6% | 84.6% | 62.4% |
| Nov 2021 | Off-year | 16.5% | 28.6% | 43.1% | 65.6% | 39.4% |
| Nov 2023 | Off-year | 14.5% | 24.6% | 37.1% | 59.0% | 34.9% |
| Nov 2025 | Off-year | 16.4% | 27.0% | 39.0% | 59.3% | 36.7% |

**These are not official turnout rates.** The denominator is the age-eligible
**April 2026 roll**, not the election-day registered cohort, so a later (larger) roll
mechanically depresses them — the "All" column (e.g., 75.0% in 2024) runs below
Washington's official general-election turnout (39.38% 2021, 63.82% 2022, 36.41%
2023, 78.95% 2024, 39.24% 2025). Read the table as a current-roll *reconstruction* of
within-cohort participation. It also rests on a single presidential (2024) and single
midterm (2022) cycle.

---

## Sensitivity

The finding does not depend on the cohort boundaries, the birth-year imputation, any
single off-year, or King County.

**Finer cohorts.** Splitting the endpoints sharpens the pattern: the 75+ share rises
from **11.8%** (presidential) to **16.8–18.3%** off-year; the 18–24 share falls from
**7.7%** to **~3.7–4.0%**.

| Election | Type | 18–24 | 25–29 | 30–44 | 45–64 | 65–74 | 75+ |
|---|---|--:|--:|--:|--:|--:|--:|
| Nov 2024 | Presidential | 7.7% | 6.5% | 24.9% | 32.4% | 16.7% | 11.8% |
| Nov 2022 | Midterm | 5.3% | 5.1% | 22.9% | 35.7% | 19.4% | 11.7% |
| Nov 2021 | Off-year | 3.7% | 3.8% | 19.7% | 36.0% | 23.3% | 13.4% |
| Nov 2023 | Off-year | 3.7% | 3.6% | 19.2% | 33.2% | 23.4% | 16.8% |
| Nov 2025 | Off-year | 4.0% | 4.0% | 19.9% | 31.7% | 22.1% | 18.3% |

**Birth-year imputation.** The file supplies year of birth, not full date, so the
main analysis uses age = election year − birth year — equivalent to assuming the
birthday has occurred by the November election. This may classify voters with
late-November or December birthdays as one year older than their exact age on
Election Day. As a sensitivity test the 65+ share is recomputed under the opposite
extreme — every voter treated as if their birthday had *not* yet occurred (a Dec-31
imputation) — which moves the off-year 65+ share by **≤2.4 points** (e.g., 2021:
36.8% → 34.3%; 2025: 40.3% → 38.2%) and leaves the presidential/off-year gap intact
(the presidential share moves too, 28.5% → 26.7%). Because November falls late in the
calendar year, the true value should lie *closer to the main convention* than to this
all-younger extreme, absent unusual late-year birthday clustering.

**Off-year stability, and statewide measures.** The three off-years bracket the same
result (65+ share 36.7 / 40.2 / 40.3%) despite *different* statewide ballot content:
2021 and 2023 carried only the state's non-binding tax "advisory votes" (since
repealed), and 2025's only statewide item was a single fiscal constitutional
amendment (SJR 8201, on investing the WA Cares trust fund — the only statewide measure
on the 2025 ballot, per the WA Secretary of State). None is a high-salience mobilizing
contest, and the stability of the 65+ share across all three is the direct evidence
that none drives the composition. Excluding any one off-year leaves the conclusion
intact.

**Geography.** King County (largest, youngest) runs younger than the rest at every
salience level, but the gradient is present everywhere and steeper outside the urban
core.

| 65+ share of electorate | 2024 Pres | 2021 Off | 2023 Off | 2025 Off |
|---|--:|--:|--:|--:|
| King County | 23.0% | 28.7% | 32.2% | 30.7% |
| Rest of state | 30.7% | 40.4% | 43.5% | 45.0% |
| Metro counties¹ | 26.4% | 34.3% | 37.5% | 37.3% |
| Rural counties | 37.7% | 46.7% | 51.5% | 54.2% |

<sub>¹ Metro = the ten most-populous counties (King, Pierce, Snohomish, Clark,
Spokane, Thurston, Kitsap, Whatcom, Benton, Yakima); rural = the remaining 29.</sub>

The presidential→off-year shift toward seniors is positive in **all 39 counties**
(full breakdown in Appendix E).

---

## Interpretation: mechanism, lever, and policy caution

**It is behavior, not the rolls.** A symmetric two-factor decomposition (Kitagawa–Das
Gupta; `scripts/diag_turnout_decomposition.py`) of the 2024→2025 change in the 65+
share **supports the behavioral interpretation**: of the **+11.8-point** rise,
**+10.9 (92%) is the turnout-rate effect** and only **+0.9 is roll composition**; for
18–29 the split is **−6.0 of −6.2 (97%) behavioral.** The split is stable across all
three off-years — the turnout-rate (behavior) effect accounts for **92% (2025), 95%
(2023), and 79% (2021)** of the 65+ rise, with the roll-composition effect small and,
in 2021 and 2023, slightly *negative* (a marginally younger roll worked against the
shift, so behavior more than accounts for it). Both endpoints of each pair are drawn
from nearly the same near-current roll, so the current-roll denominator bias is common
to both and largely cancels in the difference; and the older-skewing attrition above
would, if corrected, *raise* the senior rate, not shift weight to the roll term. The
skew is a turnout/salience phenomenon — which is why the lever is **election timing**,
not registration policy.

**The off-year electorate is the presidential electorate's habitual core.** Among
**analyzable current-roll voters**, individual records make surge-and-decline concrete
in a way aggregate data cannot. Roughly **92–97%** of each off-year electorate also cast
a 2024 presidential ballot, while only **42–48%** of 2024 presidential voters turned out
in a given off-year — the off-year electorate is close to a *recurring core* of the
presidential one. Splitting 2024 presidential voters by whether they *also* voted the
2023 off-year shows who stays and who leaves: the **habitual core** (voted both; 1.6M)
is **42.8% 65+ and 6.1% under 30**, while the **presidential-only drop-off** (2.2M) is
**18.0% 65+ and 20.2% under 30**. The voters who appear mainly when a presidential race
is on the ballot are disproportionately young; the off-year electorate is what remains
when that peripheral electorate falls away. Off-year voters also have **older current
registration records** — a median of roughly **16–17 years** since registration date
versus **12** for the presidential electorate — though registration-record age is not a
perfect measure of lifetime civic attachment. Because this overlap is computed among
analyzable current-roll voters, it should be read alongside the survivorship checks
above: attrition removes some past voters from the panel, especially older voters who
died or moved before the 2024 comparison point.

**The lever.** The quasi-experimental evidence that on-cycle timing reshapes the
electorate is strong. Anzia (2014) and Hajnal & Trounstine (2005): off-cycle
elections shrink the electorate and make it less representative, shifting outcomes
toward organized, high-propensity groups. Hajnal, Kogan & Markarian (2022), using individual
micro-targeting data, find California's move to on-cycle municipal elections roughly
**doubles** local turnout and makes the electorate considerably more representative by
age, race, and partisanship. Lucero et al. (2025), in a switcher-city survey, report
voters over 45 at **58.4%** of the off-cycle vs **49.7%** of the presidential-
concurrent electorate (and, citing Hajnal et al., a ~**22-point** over-55 gap). This
paper measures Washington's *gap* — ~40% off-year 65+ vs ~28.5% presidential — but not
what consolidation would do here: **if Washington followed the pattern those studies
document, the expected effect of moving local races onto even-year Novembers would be
a substantially larger and younger local electorate** — a plausible extrapolation from
California city-election evidence, not a Washington simulation.

**Policy caution.** The mechanism literature gives reason to *expect* that a smaller,
older, more-organized off-cycle electorate produces different policy (Anzia 2014, on
public-employee compensation; Kogan, Lavertu & Peskowitz 2018, on school-district
spending). But the evidence is not settled: **Ornstein (2024)**, using California's
2018 on-cycle mandate (SB 415) across 236 local governments, finds the expected
turnout and diversity gains but **no** detectable downstream effect on descriptive
representation, the candidate pool, the incumbency advantage, housing policy, or
public-employee salaries. **This paper does not adjudicate that debate.** It estimates
participation and composition; the composition result is not evidence of policy
capture. (The full taxonomy of objections — preference-intensity, ballot dilution /
roll-off, and age-as-proxy — is in Appendix A.)

---

## What this paper does not claim, and limits

- **No partisan consequence.** Washington does not publish party of record, so this
  paper stops at participation and composition. The party-registration companions
  ([New York](who-decides-new-york.md), [Idaho](who-decides-idaho.md)) test that.
- **No policy-outcome claim.** The composition finding is not evidence of policy
  capture, union influence, or changed local outcomes; the literature is mixed
  (above) and it is not tested here.
- **No contest-level claim.** This paper measures ballot return in November, not participation
  in a specific local contest (Lucero et al. 2025). Appendix F estimates even-year
  *contest*-level roll-off as a first look at the sequel.
- **No individual-level causal claim** about why any person votes or abstains.
- **Age vs cohort.** Five cycles (2021–2025) cannot separate a *life-cycle* effect
  (older people vote off-cycle) from a *cohort* effect (a durable high-propensity
  generation that is currently old). The habitual-core result is consistent with
  either; distinguishing them needs a longer individual panel.
- **Cycle coverage.** The vote history begins in 2021, so the presidential row rests
  on **2024 alone** and the midterm on **2022 alone**; only the off-year row averages
  three cycles. King County 2020 presidential is not loaded and is excluded (all
  figures are 2021+).
- **Uncertainty.** The VRDB figures are near-population counts and carry no sampling
  error; the ACS resident/CVAP rows are 5-year *estimates* with margins of error (small
  at this geography and aggregation but nonzero), and the county roll-off correlation
  (n=39) is reported without a confidence interval — it is descriptive, not inferential.
- **Rates are a current-roll reconstruction**, not official turnout (above); the
  **share-of-electorate** figures, which need no denominator and are a bounded and
  validated estimate, carry the finding. Methods detail in Appendix C.

---

# Appendices

## Appendix A — The objections, in full

The most obvious objection is the weakest: **this is voluntary participation, not
disenfranchisement.** Correct, and the right frame. Washington votes entirely by
mail, prepaid, with automatic and same-day registration; no one is kept from the
off-year ballot, and the remedy (moving local races onto even-year ballots) is an
ordinary scheduling choice. This is a **design** question, not a rights question. But
the benign reading explains *why* the off-year electorate is older; it does not make
it less so, and the descriptive gap stands regardless of how one judges it. (It is
also what makes Washington an informative case: with the usual access-cost explanation
for youth drop-off weaker in a prepaid, same-day-registration state, the age gap is
harder to attribute to friction.) Three stronger objections deserve direct treatment.

**1 — The off-year electorate as a preference-intensity filter, not a defect.**
Perhaps the people who return low-salience local ballots are more informed, more
locally attached, and more directly affected by property taxes, schools, and utility
districts — and presidential-year voters, drawn by the national contest, may be *less*
informed about local races and more likely to use national cues. This is the genuine
normative crux. Three points bound it. (a) It is an argument about the *quality* of
the marginal voter, which this participation study does not measure or resolve. (b) It
cuts against a large literature finding on-cycle electorates *more* representative of
the underlying population by age, race, and partisanship (Hajnal, Kogan & Markarian
2022) — closer to the community the government serves. (c) The information deficit it
posits is itself partly an artifact of off-cycle timing (thin media coverage), so it
is not clearly exogenous to the scheduling choice.

**2 — Ballot dilution / down-ballot roll-off.** If local races move to even years,
more people receive the ballot but some skip the local contest, so the contest-level
electorate grows by less than total turnout. This is measured directly for Washington
(Appendix F): in the 2024 even-year general, roll-off (the share of counted ballots
casting no vote in a contest) was **~3–7%** for partisan statewide offices and ballot
measures, **~16–17%** for *contested* nonpartisan statewide contests (Supreme Court,
Superintendent of Public Instruction), and **~34%** for *uncontested* ones —
nonpartisan judicial races being the closest even-year analog to the local nonpartisan
races (city council, school board) consolidation would add, and likely an upper bound
(voters know least about judges). This exceeds the ~2–10% classic estimate (Wattenberg,
McAllister & Salvanto 2000, who attribute roll-off substantially to *information*), and
it is not assumed to be age-neutral for WA local contests, which remains untested.
**Even so, the likely net direction is enlargement**, though its size depends on
whether local races move onto a presidential- or a midterm-year ballot (Appendix F):
even at the worst observed roll-off (34%), the even-year deciding electorate is ~52% of
registered on a presidential ballot and ~42% on a midterm ballot, both above the ~38%
who turn out off-cycle today. Enlargement survives substantial roll-off unless local
roll-off runs far above the contested-nonpartisan benchmark.

**3 — Age is not a clean proxy for whose interests matter.** Seniors are heavily
affected by local taxes, emergency services, transit, utilities, public safety,
housing supply, and school levies, and no claim is made that younger people have more
legitimate interests (an earlier draft's "most affected" phrasing overreached and is
retracted). The narrower claim is **representational**, and stays entirely within the
registered electorate the data measures: among registered voters, off-year
ballot-returners are substantially older than presidential-year ballot-returners
(median age ~59–60 vs 52, and ~a decade older than the median registrant, 48). If
local offices are chosen by a markedly older subset of the registered electorate, the
preferences counted at the ballot box differ systematically by age. The gap extends
beyond registrants to the eligible and resident populations: the off-year electorate's
65+ share (~39%) is over **1.7 times** the **22.6%** of citizen voting-age Washingtonians
who are 65+ (ACS 2020–24 CVAP) — and nearly double the 21.1% of all adult residents —
while its 18–29 share (~7.6%) is under two-fifths of the ~20% share in both benchmarks
(§ What the data shows). Whether that is desirable, tolerable, or problematic is a
normative question; the empirical contribution here is to measure its size.

## Appendix B — Data access and privacy

- **What was obtained.** Washington's standard statewide **VRDB extract** — the single
  public extract the Secretary of State publishes (registrants plus cumulative vote
  history), regenerated monthly. This study uses the **April 2026 extract** (requested
  April 8, 2026). By statute the public file is limited to each voter's name, address,
  political jurisdiction, gender, **year of birth**, voting record, registration date,
  and registration number, and **no other information from voter-registration records
  is available for public inspection or copying** (RCW 29A.08.710) — the statutory basis
  for year-of-birth-not-full-date. Its use is restricted to elections and political
  purposes and **may not be used for commercial purposes** (RCW 29A.08.720); the file is
  **not redistributable**, with penalties at RCW 29A.08.740. Full provenance and access
  date: [Data Sources & Reproducibility](data-sources-and-reproducibility.md).
- **Year of birth, not date of birth.** Consistent with the statute, the extract
  supplies **year of birth only**; full date of birth is protected information that
  Washington withholds from the public voter database, and the legislature further
  strengthened voter-data protections in 2026 (SB 5892 / Ch. 213, Laws of 2026, eff.
  Mar. 25, 2026). In our file every birth value resolves to a July-1 sentinel,
  confirming year-only granularity — **no full date of birth was obtained, stored, or
  used.**
- **What is released.** Only aggregate cohort counts, with cell sizes in the thousands
  to millions; no individual-level records, addresses, or names. The analysis scripts
  emit aggregates only, and the repository's product layer additionally enforces a PII
  firewall (`src/wa_analyzer/product/firewall.py`). Only **citations and code, not
  data** are published — the only lawful option for the voter file.

## Appendix C — Methods

- **Source and unit.** `voting_history` (27.1M records) joined to `voters` (year of
  birth, ~100% coverage), cohorts assigned per election. November generals only. The
  unit is **ballot return**, not participation in a specific contest.
- **Age convention.** With year of birth, age = election year − birth year
  (equivalently, birthday assumed reached by November). This is a ±1-year approximation
  of true age; the birth-year-imputation sensitivity (Sensitivity) shows the alternative
  extreme moves the off-year 65+ share by ≤2.4 points and leaves the gap intact.
- **Composition vs rates.** The within-cohort *participation rates* are a current-roll
  reconstruction (denominator = the April 2026 roll, not the election-day registered
  cohort), so they are not official turnout and are reported only to show the mechanism.
  The **share-of-electorate** figures, which need no denominator, carry the finding.
- **Coverage and bounding.** Coverage of the analyzable electorate against certified
  counts is 90.8–99.6%. Two distinct claims: the observable attrition component skews
  old, so the observed estimates are *likely conservative*; and, assuming nothing about
  the residual, a formal worst-case bound (every missing voter under 65) still keeps
  each off-year 65+ share above the presidential one, so the finding does not depend on
  the residual's composition. The Idaho companion reports **no** rates, because a ~13%
  roll contraction since 2024 inflates them past use — a difference in data, not method.
- **Decomposition.** The behavior-vs-rolls split is the symmetric two-factor
  (Kitagawa–Das Gupta) standardization (Appendix D).
- **Reproduction.** `scripts/verify_who_decides_wa.py` re-derives every count in the
  tables above from scratch (validation, survivorship, bounding, finer cohorts,
  imputation, geography, decomposition, habitual-core overlap, snapshot cross-validation,
  gender, representativeness index), independently of the analysis code; the ecological
  roll-off correlation is in `scripts/diag_wa_rolloff_2024.py`.

## Appendix D — Related work

The finding — that low-salience electorates are older and smaller — is well
established; this paper does not claim to discover it. Its contribution is narrower and
twofold. First, it provides a **validated, individual-record** measurement of
Washington's recent November electorates across the full salience gradient
(presidential → midterm → off-year) from ~100% of the state's vote records, in a
**universal vote-by-mail, same-day-registration** state where the usual access-cost
explanation for youth drop-off is weaker. Second, and equally load-bearing, it confronts
a common voter-file problem directly: because historical vote records are reconstructed
from a *current* registration file, past voters who have since died, moved, or been
canceled can be missing — an assumption many voter-file analyses leave implicit. By
benchmarking against certified ballot counts, characterizing the observable attrition,
and formally bounding the full residual, the paper shows the age-composition result is
not an artifact of current-roll survivorship.

- **Turnout composition by salience (surge-and-decline).** Campbell, "Surge and
  Decline: A Study of Electoral Change," *Public Opinion Quarterly* 24(3) (1960):
  397–418. Wolfinger & Rosenstone, *Who Votes?* (Yale, 1980); Leighley & Nagler, *Who
  Votes Now?* (Princeton, 2013) — age is among the most durable turnout predictors.
- **Off-cycle election timing, composition, and representation.** Anzia, *Timing and
  Turnout: How Off-Cycle Elections Favor Organized Groups* (Univ. of Chicago Press,
  2014); Hajnal & Trounstine, "Where Turnout Matters," *Journal of Politics* 67(2)
  (2005): 515–535; Hajnal, Kogan & Markarian, "Who Votes: City Election Timing and
  Voter Composition," *American Political Science Review* 116(1) (2022): 374–383;
  Kogan, Lavertu & Peskowitz, "Election Timing, Electorate Composition, and Policy
  Outcomes: Evidence from School Districts," *American Journal of Political Science*
  62(3) (2018): 637–651; Lucero, Robles, Trounstine & Collins, "What Date Works Best
  for You? Changes in Electorate Demographics and Policy Priorities in Concurrent
  Elections," *Urban Affairs Review* (2025); Einstein, Palmer, Hamilton & Singer, "Age
  and Homeownership Drive the Local Turnout Gap," *Urban Affairs Review* (2025) — the
  closest analog to the age result here.
- **Contested policy effects of timing.** Ornstein, "Election Timing Revisited:
  Evidence from California's Voter Participation Rights Act" (working paper, 2024) —
  turnout/diversity gains but null downstream policy effects.
- **Down-ballot roll-off.** Wattenberg, McAllister & Salvanto, "How Voting Is Like
  Taking an SAT Test: An Analysis of American Voter Rolloff," *American Politics
  Quarterly* 28(2) (2000): 234–250 — roll-off is substantially information-driven.
- **Voter-file / individual-level method.** Ansolabehere & Hersh, "Validation: What
  Big Data Reveal About Survey Misreporting and the Real Electorate," *Political
  Analysis* 20(4) (2012): 437–459; Hersh, *Hacking the Electorate* (Cambridge, 2015).
- **Decomposition method.** Kitagawa, "Components of a Difference Between Two Rates,"
  *JASA* 50(272) (1955): 1168–1194; Das Gupta, *Standardization and Decomposition of
  Rates* (U.S. Census Bureau, P23-186, 1993).

## Appendix E — 65+ share of the electorate by county

The off-cycle senior tilt is not a King County artifact or a rural artifact: the
presidential→off-year shift toward seniors is **positive in all 39 counties**
(`scripts/verify_who_decides_wa.py` #24). Counties are sorted by their 2024
presidential 65+ share; the last column is the average off-year (2023, 2025) share
minus the presidential share. The off-year average uses 2023 and 2025 because those
years have substantially higher analyzable coverage than 2021 (99.6% and 95.9% vs
90.8%); including 2021 does not change the conclusion — averaged over all three
off-years the gap remains positive in every county (King +7.5 to Franklin +16.1).

| County | 2024 Pres | 2023 Off | 2025 Off | Pres→Off | County | 2024 Pres | 2023 Off | 2025 Off | Pres→Off |
|---|--:|--:|--:|--:|---|--:|--:|--:|--:|
| Jefferson | 53.2% | 66.1% | 65.7% | +12.7 | Douglas | 34.3% | 50.8% | 53.2% | +17.7 |
| Pacific | 48.2% | 60.1% | 62.3% | +13.0 | Cowlitz | 32.5% | 46.9% | 49.7% | +15.8 |
| Clallam | 47.3% | 59.9% | 60.9% | +13.1 | Kitsap | 32.2% | 44.1% | 44.5% | +12.1 |
| San Juan | 47.3% | 59.5% | 57.8% | +11.4 | Grant | 32.0% | 47.1% | 48.3% | +15.7 |
| Ferry | 45.4% | 55.7% | 62.1% | +13.5 | Yakima | 31.5% | 47.4% | 48.1% | +16.3 |
| Wahkiakum | 45.0% | 54.0% | 56.9% | +10.5 | Klickitat | 31.3% | 45.0% | 44.5% | +13.4 |
| Island | 43.0% | 54.5% | 60.1% | +14.3 | Thurston | 30.9% | 43.4% | 42.8% | +12.2 |
| Columbia | 42.4% | 51.8% | 55.9% | +11.5 | Adams | 30.2% | 43.2% | 43.5% | +13.1 |
| Garfield | 42.4% | 54.4% | 50.5% | +10.1 | Whatcom | 29.6% | 37.5% | 40.0% | +9.1 |
| Asotin | 40.9% | 57.8% | 58.3% | +17.1 | Spokane | 29.6% | 40.3% | 43.2% | +12.2 |
| Okanogan | 40.9% | 50.2% | 55.1% | +11.8 | Benton | 29.1% | 42.4% | 44.9% | +14.6 |
| Mason | 40.0% | 55.7% | 55.7% | +15.7 | Clark | 27.9% | 44.2% | 42.3% | +15.4 |
| Pend Oreille | 39.9% | 54.8% | 58.6% | +16.8 | Pierce | 26.7% | 39.9% | 40.4% | +13.4 |
| Lincoln | 39.6% | 51.4% | 54.2% | +13.2 | Whitman | 26.3% | 38.5% | 40.4% | +13.1 |
| Grays Harbor | 39.4% | 54.7% | 57.6% | +16.8 | Snohomish | 25.5% | 36.8% | 38.4% | +12.1 |
| Kittitas | 38.6% | 49.8% | 54.1% | +13.3 | Franklin | 24.0% | 39.8% | 42.6% | +17.2 |
| Stevens | 38.4% | 50.3% | 56.0% | +14.7 | King | 23.0% | 32.2% | 30.7% | +8.4 |
| Skagit | 38.3% | 52.3% | 54.3% | +15.0 | | | | | |
| Walla Walla | 35.6% | 48.6% | 52.3% | +14.8 | | | | | |
| Chelan | 35.2% | 45.2% | 51.6% | +13.2 | | | | | |
| Lewis | 34.7% | 50.0% | 51.9% | +16.2 | | | | | |
| Skamania | 34.5% | 48.9% | 49.8% | +14.9 | | | | | |

The off-year 65+ share ranges from **30.7% (King)** to **66% (Jefferson)**, and every
county moves toward seniors off-cycle (gaps +8.4 to +17.7 points). The result is a
statewide phenomenon; King is simply its youngest instance.

## Appendix F — Contest-level roll-off on the even-year ballot

The one thing this paper does *not* measure is whether a voter marked a specific
contest. The obvious sequel — and the live objection to consolidation — is
**down-ballot roll-off**: if local nonpartisan races moved onto the long even-year
ballot, how many returned ballots would skip them? It is estimated from certified 2024
precinct returns (`scripts/diag_wa_rolloff_2024.py`), as (ballots counted − votes cast
in a contest) / ballots counted (official 2024 ballots = 3,961,569).

| Contest type (2024 general) | Example | Roll-off |
|---|---|--:|
| Top of ticket | President | 1.1% |
| Partisan statewide office | Governor … Insurance Comm. | 2.7–6.8% |
| Statewide ballot measure | I-2109 … I-2124 | 4.1–5.6% |
| **Nonpartisan statewide, contested** | Supreme Court Pos. 2; Supt. of Public Instruction | **16.6–17.2%** |
| **Nonpartisan statewide, uncontested** | Supreme Court Pos. 8, 9 | **33.7–34.4%** |

<sub>Court of Appeals (regional — only one division votes) and Lt. Governor (loaded in
only 5,355 of 8,111 precincts / 38 of 39 counties — a partial-load artifact, not
roll-off) are excluded; see the script header.</sub>

Two honest points follow. First, Washington's even-year nonpartisan roll-off is not
trivial: about **17%** in contested statewide nonpartisan contests and about **34%** in
uncontested ones in 2024. These are plausible upper-bound analogs for local nonpartisan
races, not direct estimates of city-council or school-board roll-off; voters generally
have less information about judicial and local nonpartisan contests than about partisan
statewide offices, and the age profile of Washington local-contest roll-off remains
untested.

Second, even under large roll-off assumptions consolidation would probably enlarge the
contest-level electorate — but the *size* of that enlargement depends on whether local
races move onto a **presidential-** or a **midterm-year** ballot. Using Washington's
recent official even-year turnout as the baseline (share of registered casting a vote
in the local contest):

| Scenario (baseline turnout) | 5% roll-off | 17% roll-off | 34% roll-off |
|---|--:|--:|--:|
| Presidential-year, 2024 (~79%) | ~75% | ~66% | ~52% |
| Midterm-year, 2022 (~64%) | ~61% | ~53% | ~42% |
| Odd-year, 2021/23/25 avg (~38%) — current baseline | — | — | — |

The enlargement claim is strongest for presidential-year consolidation, still plausible
for midterm-year consolidation, and weakest for low-information or uncontested local
races placed on a *midterm* ballot (~42% vs the ~38% off-year baseline). The grid also
treats roll-off as *fixed* across scenarios, which it is not: a presidential electorate
contains more low-information peripheral voters — the ones who roll off most — so its
true roll-off is likely higher than a midterm electorate's, making the presidential row
an upper bound and the presidential–midterm gap narrower than shown. The better
conclusion is not that roll-off is second-order in every case, but that even
substantial roll-off does not erase the turnout advantage unless local-contest roll-off
runs far higher than the contested-nonpartisan benchmark.

**Does roll-off skew young? An ecological first look.** The concern behind this
objection is that the young voters consolidation would add are also the ones most likely
to skip a local contest. Cast-vote records cannot answer this directly — ballots are
anonymous and carry no voter age, so the roll-off *age profile* is unmeasurable at the
individual level under secret-ballot rules, and an ecological cut is the ceiling.
Across the 39 counties, roll-off on that contest is if anything *higher* where the
electorate is older (Pearson r ≈ +0.6, **uncorrected for urbanicity**) — that is, the
county pattern does not show younger places skipping the contest more. This is weak
evidence: it is ecological, confounded with the rural/urban gradient (older counties
are rural, with thinner coverage of statewide judicial races), and measured on a
*statewide* judicial race that is an imperfect analog for hyperlocal contests. It
points away from young-concentrated roll-off but cannot establish individual behavior.
A finer precinct-level ecological analysis is the natural sequel, and the next paragraph
runs it; an individual-level administrative test is not available from public cast-vote
records, because ballot secrecy prevents linking contest choices to voter age.

**A closer look, precinct by precinct.** The county number has one real weakness: in
Washington the older counties are also the rural ones, so a county-level correlation can't
tell whether roll-off follows *age* or just *rural*. The +0.6 blends the two — the earlier
county cut said as much. Precincts let us separate them. Across the ~4,900 precincts that
have both a 2024 presidential vote and Census demographics
(`scripts/diag_wa_rolloff_precinct.py`), roll-off in the Supreme Court Pos. 2 race averages
16.4% — in line with the roughly 17% we see statewide once both are measured the same way,
a good check that the precinct data holds together. The county cut's *direction* survives;
its *strength* does not. On the same yardstick the county used — the share of a precinct's
2024 voters who are 65 or older — the correlation falls from +0.6 to about +0.09, under a
sixth as strong, because moving from 39 counties down to thousands of precincts strips out
the lumping-together that had exaggerated it. (Measured against a precinct's older
*residents* instead of its older *voters*, it's about +0.26 — still small, still pointing
the same way.)

The real value of working at the precinct level is that we can finally account for how
urban and how well-off a place is. Put the age figures next to each precinct's income,
education, home values, share of renters, and size — a stand-in for the urban-versus-rural
and rich-versus-poor divide — and ask what age still explains on its own, and almost
nothing is left: about +0.11 in the contested court race and +0.02 for Superintendent. So
the big county number doesn't hold up either way — not when we look closer, and not when we
account for the urban/rural split — and the little that remains still points the *opposite*
way from the worry: if anything, older precincts skip the race slightly *more*, not less.
The takeaway is the same as the county version, just on firmer ground: nothing here
supports the fear that the young voters consolidation would bring in are the ones who'd skip
the local race. The usual cautions still apply, and they stack up rather than fade: this is
a neighborhood-level pattern, not proof about individuals — ballots are anonymous, so
roll-off by a voter's own age can never be measured directly; the urban/rural stand-in is
rough, since precincts are drawn to hold about the same number of people and a real density
measure from the map files would do better; and a statewide court race is only a loose match
for a city-council or school-board contest. But every time we've sharpened the test, it has
come out the same way. (This precinct cut leans on two tables the pipeline builds — Census
figures mapped onto precincts, and a voter-file-to-precinct crosswalk — so it needs more
than the raw public results; see the script header.)

---

## End note — data, reproduction, and series

**Data.** Washington's statewide voter-registration database (April 2026 extract):
the 5.51M-voter roll joined to 27.1M individual vote records and each voter's year of
birth (`data/wa_vrdb.duckdb`); access terms in Appendix B. Official ballot counts are
the certified statewide totals published by the WA Secretary of State
(`results.vote.wa.gov`). Adult-resident age composition is the U.S. Census American
Community Survey 2020–2024 5-year, table B01001 (Washington, FIPS 53).

**Institutional context.** Washington is an unusually informative case because formal
ballot-access costs are lower than in many states: registered voters receive mail
ballots, which can be returned by mail without postage or by drop box; eligible voters
may register or update registration in person through 8 p.m. on Election Day; and
registration is automatic through qualifying agency transactions (WA Secretary of
State). Those rules do not eliminate every participation barrier — information costs,
mobility, local attachment, address stability, and unequal political recruitment still
matter — but they make it harder to attribute the age gap primarily to ballot-access
friction.

**Reproduction.** `scripts/verify_who_decides_wa.py` re-derives every count in the
tables above from scratch (sections #1–#29, incl. the county breakdown, habitual-core
overlap, snapshot cross-validation, gender, and representativeness index); the roll-off
appendix and its ecological age correlation are in `scripts/diag_wa_rolloff_2024.py`, with
the finer precinct-level, urbanicity-controlled cut in `scripts/diag_wa_rolloff_precinct.py`;
`scripts/diag_wa_individual_findings.py` and `scripts/diag_turnout_decomposition.py`
produce the underlying figures; and `scripts/acs_wa_adult_age.py` reproduces the
adult-resident and CVAP rows from the Census API.

**Series.** Lead paper of the electoral-health series (with
[`electoral-health-whitepaper.md`](electoral-health-whitepaper.md) and
[`cross-state-fec-money.md`](cross-state-fec-money.md)). Party-resolved companions in
states that publish party of record:
[`who-decides-new-york.md`](who-decides-new-york.md) (deep blue) and
[`who-decides-idaho.md`](who-decides-idaho.md) (deep red).

**Companion paper: [Safe-Seat Washington](safe-seat-washington.md)** — once in an
off-year general, how often is the contest even a choice? It counts **observed**
competitiveness of every partisan legislative + congressional seat, 2016–2024
(≈85% non-competitive), and extends the count to a four-state lower-chamber map.
