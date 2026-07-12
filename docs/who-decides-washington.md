# Who Decides Washington?

### Who Returns the Ballot? Age Composition in Washington's Odd-Year Electorate, 2021–2025

**Stephen Kirby** · Tikor Consulting · July 2026

*AI-assisted analysis; every figure is independently reproducible from public records
via the cited open-source scripts (e.g. `scripts/verify_who_decides_wa.py`). Contact:
kirby@tikorconsulting.com.*

## Abstract

Many of Washington's local offices are filled in odd-year November elections, when
turnout runs far below presidential years. This paper asks *who returns those ballots*.
Using Washington's statewide voter-registration database — a 5.51-million-voter roll
linked to 27.1 million individual vote-history records, each with the voter's year of
birth — it measures the age make-up of every November general electorate from 2021
through 2025. The central finding is descriptive: Washington's odd-year electorate is
markedly older than its presidential one. Voters 65 and older were 36.7%, 40.2%, and
40.3% of the 2021, 2023, and 2025 odd-year electorates, against 28.5% in 2024; voters
18–29 fell from 14.2% in 2024 to about 7.6% off-cycle. The result holds up under a full
set of checks: it matches certified ballot counts; it survives a formal worst-case bound
for voters missing from the current-roll reconstruction (cross-checked against a second,
closer-in-time roll snapshot); and it holds under alternative birth-year assumptions,
across all 39 counties, and with any single off-year dropped. The off-year electorate is
also older than the registered roll and the citizen voting-age population. Individual
records show it is largely the presidential electorate's *habitual core* — 92–97% of
off-year voters also vote in presidential years — while the peripheral voters who drop
off off-cycle skew young. The paper measures ballot return, not votes cast in specific
down-ballot contests, and does not estimate partisan or policy consequences. Its
contribution is a validated, individual-record measurement of age composition across the
presidential–midterm–off-year salience gradient, in a universal vote-by-mail state where
the formal cost of voting is comparatively low.

**Keywords:** election timing; voter turnout; local elections; age representation;
voter files; Washington; vote by mail; off-cycle elections.

---

## The question

Coverage of "turnout" usually asks how *many* people vote. The question that matters
more for how a state is governed is *who* — and the answer shifts depending on which
election you look at. Washington fills many of its most local offices — city councils,
school boards, port and fire commissions, and many county and judicial seats — in
**odd-year, off-cycle Novembers** (RCW 29A.04.321 limits the odd-year statewide general
election chiefly to city, town, and district offices, certain county positions, and
state measures), when only about **38%** of registered voters send back a ballot. This
paper looks at who that 38% is, voter by voter.

The short answer: **the odd-year electorate we can observe is markedly older than the
presidential one.** It is not a smaller copy of the presidential electorate — it is an
older one.

**What is measured.** This paper measures **ballot return** — whether a registered
voter cast a November ballot — one voter at a time. It does *not* tell us whether that
voter actually marked a specific city-council, school-board, port, fire, judicial, or
county race; the voter file records that someone voted in an *election*, not in a given
*contest* (Lucero et al. 2025). That gap matters most for the **even-year what-if**: if
local races were moved onto the longer even-year ballot, some of the added voters would
return a ballot but skip the local race. For the **odd-year electorate described here**
the gap is smaller — Washington's odd-year ballot is mostly local and district contests,
with only the occasional statewide measure — so ballot return is a closer stand-in for
local-race participation, though it is still an election-level measure, not a
contest-level one. Appendix F takes up roll-off as the live counterargument.

---

## Data and validation

**Source.** `voting_history` (27.1M records) joined to `voters` (year of birth,
~100% coverage) from Washington's standard statewide VRDB extract (April 2026;
provenance and use terms in Appendix B). Age is taken as election year − birth year;
cohorts are assigned per election. November generals only, 2021–2025.

The sharpest objection to any voter-file study is: *you didn't measure the electorate;
you measured the part of it still visible in your current voter file.* Because the
vote-history table is tied to a current (2026) roll, anyone who voted in 2021–2024 but
has since died, moved, or been dropped is missing. If those departed voters were a random
slice, losing them wouldn't matter; if they skew young, the finding would be overstated.
Both are testable, and the answers favor the finding.

**Coverage is high, and the worst case is bounded directly.** We benchmark the
reconstruction against certified WA Secretary of State ballot counts
(`results.vote.wa.gov`). "In file" counts distinct voters in the cumulative vote-history
table for an election; "Analyzable" also requires a match to the April 2026 roll with a
year of birth. Analyzable coverage runs from **90.8% in 2021 to 99.6% in 2025**,
improving sharply over time. The weakest year is the 2021 off-year — which is exactly why
the analysis reports an explicit worst-case bound (below) instead of assuming the missing
voters look like the ones we can see. The benchmark is *certified ballots counted*; the
vote-history file is a voter-level reconstruction of who got ballot credit, expected to
track that count closely but not to match it exactly.

| Election | Type | Official ballots counted | In file | Analyzable (roll + YOB) | Analyzable / official |
|---|---|--:|--:|--:|--:|
| Nov 2021 | Off-year | 1,896,481 | 1,828,231 (96.4%) | 1,722,262 | **90.8%** |
| Nov 2022 | Midterm | 3,067,686 | 3,025,352 (98.6%) | 2,884,966 | **94.0%** |
| Nov 2023 | Off-year | 1,758,084 | 1,731,431 (98.5%) | 1,686,656 | **95.9%** |
| Nov 2024 | Presidential | 3,961,569 | 3,958,965 (99.9%) | 3,880,070 | **97.9%** |
| Nov 2025 | Off-year | 2,001,425 | 1,995,509 (99.7%) | 1,993,505 | **99.6%** |

**The voters we lose skew old, and the rest is bounded.** A second roll snapshot
(`voters_20230901`, 5.29M rows, Sept 2023) lets us partly describe voters who cast a past
ballot but are gone from the April 2026 roll. Among these visible drop-offs, seniors are
heavily overrepresented:

| Missing-from-current-roll voters | 65+ share | 18–29 share |
|---|--:|--:|
| Cast a ballot Nov 2021 (n≈106K) | **60.4%** | 6.8% |
| Cast a ballot Nov 2022 (n≈140K) | **60.3%** | 7.1% |
| Cast a ballot Nov 2023 (n≈45K) | **69.0%** | 4.5% |

Leaving the roll is age-loaded more broadly: of the 504K voters (9.5%) who left the roll
between 2023 and 2026, 33.1% were 65+, versus 23.9% of those who stayed — consistent with
mortality and age-related moves and cancellations. So the current-roll reconstruction
**likely understates** the senior share of past electorates. But since not every missing
ballot can be pinned down from the second snapshot, we also report a **formal bound** that
assumes nothing about the rest: the 65+ share of the *full certified electorate* first if
every unobserved voter (official − analyzable) were under 65, then if every one were 65+.

| Off-year 65+ share of the certified electorate | all missing < 65 (min) | observed | all missing 65+ (max) |
|---|--:|--:|--:|
| Nov 2021 (residual 9.2%) | **33.4%** | 36.8% | 42.6% |
| Nov 2023 (residual 4.1%) | **38.6%** | 40.2% | 42.6% |
| Nov 2025 (residual 0.4%) | **40.2%** | 40.3% | 40.6% |

<sub>"Observed" is the 65+ share of the analyzable electorate from the validation
table (2021 = 36.8%; the composition table's 36.7% adds a "registered on/before the
election" filter — a 0.1-point difference). Min/max apply the extreme assumption to
the residual = official − analyzable.</sub>

Even under the most hostile assumption — every unobserved off-year ballot cast by someone
under 65 — each off-year electorate (**33.4% / 38.6% / 40.2%** 65+) stays older than the
presidential electorate under *its* most favorable assumption (**≤30.0%**, i.e. even if
every missing 2024 ballot were 65+). So the finding doesn't depend on how the missing
voters are assigned. Two separate points: given the attrition evidence, the observed
estimates are **likely conservative**, and the **formal worst-case bound** keeps the
finding either way.

**A direct check: the composition barely moves under a closer-in-time roll.** The bound
above says nothing about the missing residual; a separate check asks whether
reconstructing from a *current* roll skews the composition at all. The database's
Sept-2023 snapshot (`voters_20230901`) still holds voters who have since dropped off the
2026 roll, so it rebuilds the 2021–2023 electorates from a roll much closer to those
elections. The two reconstructions agree to within ~1.4 points — and what movement there
is runs *upward*, consistent with the current roll slightly undercounting seniors:

| Election | Current-roll 65+ | Sept-2023-snapshot 65+ | Δ |
|---|--:|--:|--:|
| Nov 2021 (off-year) | 36.8% | 38.1% | +1.4 |
| Nov 2022 (midterm) | 31.0% | 32.4% | +1.4 |
| Nov 2023 (off-year) | 40.2% | 41.1% | +0.9 |

The snapshot — which recovers older voters the current roll has since dropped — comes out
slightly *higher*, not lower, so the composition finding isn't an artifact of building it
from a current roll. The 2021 and 2022 comparisons are the cleanest, because the
September-2023 snapshot comes after those elections. Read the 2023 comparison more
cautiously: the snapshot predates the November-2023 election by two months, so it misses
late-2023 registrants who voted that November, and if those late registrants skew younger
— as new registrants often do — the snapshot's 2023 estimate may run slightly *high*.
Even so, the check reassures: the closer-in-time reconstruction never makes an electorate
younger than the current-roll version, and 2021–2022 point the same way.

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

- **The off-year electorate is a senior-plurality electorate, and stably so.** Voters
  65+ make up **~37–40%** of it (36.7 / 40.2 / 40.3% across 2021 / 2023 / 2025) versus
  **28.5%** in the presidential year; the 18–29 share falls from **14.2%** to **~7.6%**.
- **The senior-to-youth ratio roughly triples off-cycle** — from about **2:1** in the
  presidential year to **~5:1** off-year, with the midterm in between (31.0% 65+). The
  *off-year* figure is stable across three cycles; the presidential and midterm points
  are single elections (2024, 2022), so read the ordering as consistent with a salience
  gradient, not as a smoothly estimated curve.

**Residents, registrants, voters: a rising age ladder.** The off-year electorate is
older than the presidential one, older than the registered roll, older than the citizen
voting-age population, and older than all adult residents. Lining the ballot-returning
electorates up against the roll (April 2026), the citizen voting-age population, and all
adult residents (both ACS 2020–24) gives a ladder that climbs at every rung:

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

The 65+ share climbs **21.1% → 22.6% → 26.3% → 28.5% → 39.1%** across the five rows; the
18–29 share falls **20.0% → 19.8% → 16.7% → 14.2% → 7.6%**. The median off-year
ballot-returner is **59** — about a decade older than the median registered voter (48),
and more than a decade older than the median citizen-voting-age adult (~47). Residents,
eligible citizens, registrants, and voters are four different populations, and what moves
the composition is participation, not the roll: the roll's senior share is low and steady
(26.3% on the full April 2026 roll; ~22–25% on the per-election eligible roll in these
years) while the off-year returner share reaches ~40%.

**One number for "how unrepresentative."** We can collapse the ladder into a single
dissimilarity index — how far each electorate's age distribution sits from the citizen
voting-age population, taken as half the summed absolute differences across cohorts, where
0 means identical. It comes out **7.4** for the 2024 presidential electorate, **13.2** at
the midterm, and **18.5–19.9** across the three off-years — so the off-year electorate is
roughly **2.5× as age-unrepresentative** of the eligible population as the presidential
one. The index depends on the age bins chosen, so treat its value here as comparative,
not absolute.

<sub>Recorded gender shows a much smaller secondary pattern: the electorate is majority
recorded-female throughout, rising from 52.5% in the 2024 presidential electorate to
53.0–53.1% in the off-year electorates, concentrated among older voters. Because the
shift is small and administrative gender is not the paper's focus, the analysis treats
age as the primary dimension.</sub>

The mechanism is differential participation. The within-cohort rates below make it
concrete — 18–29 participation falls from **58.4%** (2024) to about **16%** off-year,
while 65+ slips only from **88.3%** to **~61%** — but these rates *back up* the
composition finding; they don't carry it:

**Within-cohort participation rate — current-roll reconstruction, not official turnout:**

| Election | Type | 18–29 | 30–44 | 45–64 | 65+ | All |
|---|---|--:|--:|--:|--:|--:|
| Nov 2024 | Presidential | 58.4% | 68.6% | 80.1% | 88.3% | 75.0% |
| Nov 2022 | Midterm | 36.4% | 52.5% | 69.6% | 84.6% | 62.4% |
| Nov 2021 | Off-year | 16.5% | 28.6% | 43.1% | 65.6% | 39.4% |
| Nov 2023 | Off-year | 14.5% | 24.6% | 37.1% | 59.0% | 34.9% |
| Nov 2025 | Off-year | 16.4% | 27.0% | 39.0% | 59.3% | 36.7% |

**These are not official turnout rates.** The denominator is the age-eligible **April
2026 roll**, not the roll as it stood on each election day, so a later (larger) roll
mechanically pulls them down — the "All" column (e.g., 75.0% in 2024) sits below
Washington's official general-election turnout (39.38% 2021, 63.82% 2022, 36.41% 2023,
78.95% 2024, 39.24% 2025). Read the table as a current-roll *reconstruction* of
within-cohort participation. It also rests on a single presidential (2024) and single
midterm (2022) cycle.

---

## Sensitivity

The finding doesn't hinge on the cohort boundaries, the birth-year assumption, any single
off-year, or King County.

**Finer cohorts.** Splitting the endpoints sharpens the pattern: the 75+ share rises from
**11.8%** in the presidential year to **16.8–18.3%** off-year, while the 18–24 share falls
from **7.7%** to **~3.7–4.0%**.

| Election | Type | 18–24 | 25–29 | 30–44 | 45–64 | 65–74 | 75+ |
|---|---|--:|--:|--:|--:|--:|--:|
| Nov 2024 | Presidential | 7.7% | 6.5% | 24.9% | 32.4% | 16.7% | 11.8% |
| Nov 2022 | Midterm | 5.3% | 5.1% | 22.9% | 35.7% | 19.4% | 11.7% |
| Nov 2021 | Off-year | 3.7% | 3.8% | 19.7% | 36.0% | 23.3% | 13.4% |
| Nov 2023 | Off-year | 3.7% | 3.6% | 19.2% | 33.2% | 23.4% | 16.8% |
| Nov 2025 | Off-year | 4.0% | 4.0% | 19.9% | 31.7% | 22.1% | 18.3% |

**Birth-year assumption.** The file gives year of birth, not the full date, so the main
analysis takes age = election year − birth year — in effect assuming the birthday has
already happened by the November election. That can label voters with late-November or
December birthdays as a year older than they really were on Election Day. As a check, we
recompute the 65+ share under the opposite extreme — treating every voter as if their
birthday had *not* yet come (a Dec-31 assumption). That moves the off-year 65+ share by
**≤2.4 points** (e.g., 2021: 36.8% → 34.3%; 2025: 40.3% → 38.2%) and leaves the
presidential/off-year gap intact (the presidential share moves too, 28.5% → 26.7%).
Because November falls late in the year, the true value should sit *closer to the main
convention* than to this all-younger extreme, barring unusual late-year birthday
clustering.

**Off-year stability, and statewide measures.** The three off-years land on the same
result (65+ share 36.7 / 40.2 / 40.3%) despite *different* statewide ballot content: 2021
and 2023 carried only the state's non-binding tax "advisory votes" (since repealed), and
2025's only statewide item was a single fiscal constitutional amendment (SJR 8201, on
investing the WA Cares trust fund — the only statewide measure on the 2025 ballot, per the
WA Secretary of State). None is a high-salience, mobilizing contest, and the fact that the
65+ share barely moves across all three is direct evidence that none of them drives the
composition. Dropping any one off-year leaves the conclusion intact.

**Geography.** King County (the largest and youngest) runs younger than the rest at every
salience level, but the gradient shows up everywhere — and is steeper outside the urban
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

**It's behavior, not the rolls.** What changed the 65+ share off-cycle — older people
turning out at higher rates, or the registration roll itself getting older? A standard
decomposition that separates the two (Kitagawa–Das Gupta;
`scripts/diag_turnout_decomposition.py`) puts it almost entirely on behavior. Of the
**+11.8-point** rise in the 65+ share from 2024 to 2025, **+10.9 points (92%) come from
turnout rates** and only **+0.9 from a changing roll**; for 18–29 the split is **−6.0 of
−6.2 points (97%) behavioral.** The pattern holds across all three off-years — turnout
accounts for **92% (2025), 95% (2023), and 79% (2021)** of the 65+ rise — and in 2021
and 2023 the roll effect is actually slightly *negative* (the roll was marginally
younger, so behavior more than accounts for the shift). This is robust to the
survivorship worry: both years in each comparison are read off nearly the same recent
roll, so any current-roll distortion is shared and largely cancels, and correcting the
older-skewing attrition described earlier would only *raise* the senior turnout rate,
not move weight onto the roll. The skew is a turnout-and-salience story, which is why the
lever is **when you hold the election**, not registration policy.

**The off-year electorate is the presidential electorate's habitual core.** Because we
can follow individual voters, we can see surge-and-decline directly rather than infer it
from aggregates. Roughly **92–97%** of each off-year electorate also cast a 2024
presidential ballot, but only **42–48%** of 2024 presidential voters showed up in a
given off-year — so the off-year electorate is close to a *standing core* of the
presidential one. Sorting 2024 presidential voters by whether they *also* voted in the
2023 off-year shows who stays and who drops off: the **habitual core** (voted both; 1.6M)
is **42.8% 65+ and 6.1% under 30**, while the **presidential-only group** (2.2M) is
**18.0% 65+ and 20.2% under 30**. The voters who mostly turn up when a presidential race
is on the ballot are disproportionately young, and the off-year electorate is what's left
once they fall away. Off-year voters have also been registered longer — a median of about
**16–17 years** since they registered, versus **12** for the presidential electorate —
though how long someone has been registered is only a rough proxy for lifelong civic
attachment. And because this comparison is limited to voters still on the current roll,
it should be read next to the survivorship checks above: attrition drops some past voters
from the panel, especially older ones who died or moved before the 2024 comparison point.

**The lever.** The evidence that on-cycle timing reshapes the electorate is strong, and
much of it is quasi-experimental. Anzia (2014) and Hajnal & Trounstine (2005) show that
off-cycle elections shrink the electorate and make it less representative, tilting
outcomes toward organized, high-turnout groups. Hajnal, Kogan & Markarian (2022), using
individual micro-targeting data, find that California's shift to on-cycle municipal
elections roughly **doubles** local turnout and makes the electorate considerably more
representative by age, race, and partisanship. Lucero et al. (2025), surveying cities
that switched, put voters over 45 at **58.4%** of the off-cycle electorate versus
**49.7%** of the presidential-year one (and, citing Hajnal et al., a roughly **22-point**
over-55 gap). This paper measures Washington's *gap* — about 40% 65+ off-year versus
about 28.5% presidential — not what consolidation would actually do here. But **if
Washington behaved like the places those studies cover, moving local races onto even-year
Novembers would produce a substantially larger and younger local electorate** — a
reasonable extrapolation from California's experience, not a Washington simulation.

**A caution on policy.** There is good reason to *expect* that a smaller, older,
more-organized off-cycle electorate yields different policy (Anzia 2014, on
public-employee pay; Kogan, Lavertu & Peskowitz 2018, on school-district spending). But
the evidence isn't settled. **Ornstein (2024)**, looking at California's 2018 on-cycle
mandate (SB 415) across 236 local governments, finds the expected gains in turnout and
diversity but **no** detectable knock-on effect on who gets represented, who runs, the
incumbency advantage, housing policy, or public-employee salaries. **This paper doesn't
try to settle that debate.** It measures participation and composition — and the
composition result is not, by itself, evidence that policy is being captured. (The full
list of objections — preference-intensity, ballot dilution / roll-off, and age-as-proxy
— is in Appendix A.)

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
- **Age vs cohort.** Five cycles (2021–2025) can't separate a *life-cycle* effect
  (people vote off-cycle more as they age) from a *cohort* effect (a durable high-turnout
  generation that happens to be old right now). The habitual-core result fits either;
  telling them apart needs a longer individual panel.
- **Cycle coverage.** The vote history begins in 2021, so the presidential row rests
  on **2024 alone** and the midterm on **2022 alone**; only the off-year row averages
  three cycles. King County 2020 presidential is not loaded and is excluded (all
  figures are 2021+).
- **Uncertainty.** The VRDB figures are near-complete counts and carry no sampling
  error; the ACS resident/CVAP rows are 5-year *estimates* with margins of error (small
  at this geography and level of aggregation, but not zero); and the county roll-off
  correlation (n=39) is reported without a confidence interval — it's descriptive, not
  inferential.
- **The rates are a current-roll reconstruction**, not official turnout (above); it's
  the **share-of-electorate** figures — which need no denominator and are bounded and
  validated — that carry the finding. Methods detail in Appendix C.

---

# Appendices

## Appendix A — The objections, in full

The most obvious objection is also the weakest: **this is voluntary participation, not
disenfranchisement.** That's true, and it's the right frame. Washington votes entirely by
mail, postage prepaid, with automatic and same-day registration; no one is shut out of
the off-year ballot, and the fix — moving local races onto even-year ballots — is an
ordinary scheduling choice. This is a question of **design**, not rights. But explaining
*why* the off-year electorate is older doesn't make it any less old: the gap is there
however you judge it. (It's also what makes Washington a useful test case. In a prepaid,
same-day-registration state the usual "it's too hard to vote" explanation for young
drop-off is weak, so the age gap is hard to pin on friction.) Three stronger objections
deserve a direct answer.

**1 — Maybe the off-year electorate is a filter for engagement, not a defect.**
Perhaps the people who bother to return a low-salience local ballot are better informed,
more rooted locally, and more directly affected by property taxes, schools, and utility
districts — while presidential-year voters, pulled in by the national race, know *less*
about local contests and lean on national cues. This is the real normative crux, and
three things bound it. (a) It's a claim about the *quality* of the marginal voter, which
a participation study like this one can't measure or settle. (b) It runs against a large
body of work finding that on-cycle electorates are *more* representative of the
population by age, race, and partisanship (Hajnal, Kogan & Markarian 2022) — closer to
the community the government actually serves. (c) The information gap it assumes is
itself partly a product of off-cycle timing (thin news coverage), so it isn't cleanly
separate from the scheduling choice.

**2 — Ballot dilution / down-ballot roll-off.** If local races move to even years, more
people get the ballot but some skip the local contest, so the number actually voting in
that race grows by less than total turnout does. Appendix F measures this directly for
Washington. In the 2024 even-year general, roll-off — the share of returned ballots that
skip a given contest — was **~3–7%** for partisan statewide offices and ballot measures,
**~16–17%** for *contested* nonpartisan statewide races (Supreme Court, Superintendent of
Public Instruction), and **~34%** for *uncontested* ones. Nonpartisan judicial races are
the closest even-year stand-in for the local nonpartisan races (city council, school
board) that consolidation would add, and probably an upper bound, since voters know least
about judges. That is higher than the classic ~2–10% estimate (Wattenberg, McAllister &
Salvanto 2000, who tie roll-off largely to *information*), and we don't assume it's
age-neutral for Washington's local races — that's untested. **Even so, the net effect is
almost certainly a bigger electorate**, though how much bigger depends on whether local
races land on a presidential- or a midterm-year ballot (Appendix F): even at the worst
roll-off we observe (34%), the electorate actually deciding the race is ~52% of
registered voters on a presidential ballot and ~42% on a midterm one — both above the
~38% who turn out off-cycle today. The gain survives heavy roll-off unless local roll-off
runs far above the contested-nonpartisan mark.

**3 — Age isn't a clean proxy for whose interests matter.** Seniors are heavily affected
by local taxes, emergency services, transit, utilities, public safety, housing supply,
and school levies, and this paper makes no claim that younger people's interests count
for more (an earlier draft's "most affected" phrasing overreached and is withdrawn). The
narrower claim is about **representation**, and it stays entirely inside the registered
electorate the data covers: among registered voters, off-year ballot-returners are much
older than presidential-year ones (median age ~59–60 vs 52, and about a decade older than
the median registrant at 48). If a markedly older slice of the registered electorate is
choosing local officials, then the preferences recorded at the ballot box differ
systematically by age. And the gap doesn't stop at registrants — it reaches the eligible
and resident populations too: the off-year electorate is ~39% 65+, over **1.7 times** the
**22.6%** of citizen voting-age Washingtonians who are 65+ (ACS 2020–24 CVAP) and nearly
double the 21.1% of all adult residents, while its 18–29 share (~7.6%) is under
two-fifths of the ~20% in both benchmarks (§ What the data shows). Whether that's
desirable, tolerable, or a problem is a normative question; what this paper contributes is
a measurement of its size.

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

The core finding — that low-salience electorates are older and smaller — is well
established, and this paper doesn't claim to discover it. The contribution is narrower,
and twofold. First, it gives a **validated, individual-record** measurement of
Washington's recent November electorates across the full salience gradient (presidential
→ midterm → off-year), from ~100% of the state's vote records, in a **universal
vote-by-mail, same-day-registration** state where the usual "too hard to vote"
explanation for youth drop-off is weak. Second, and just as important, it tackles a common
voter-file problem head-on: because past vote records are reconstructed from a *current*
registration file, voters who have since died, moved, or been dropped can go missing — an
assumption many voter-file studies leave unstated. By benchmarking against certified
ballot counts, describing the attrition we can see, and formally bounding the rest, the
paper shows the age-composition result isn't an artifact of current-roll survivorship.

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

The off-cycle senior tilt isn't a King County artifact or a rural artifact: the
presidential→off-year shift toward seniors is **positive in all 39 counties**
(`scripts/verify_who_decides_wa.py` #24). Counties are sorted by their 2024 presidential
65+ share; the last column is the average off-year (2023, 2025) share minus the
presidential share. The off-year average uses 2023 and 2025 because their analyzable
coverage is much higher than 2021's (99.6% and 95.9% vs 90.8%); adding 2021 doesn't
change the conclusion — averaged over all three off-years the gap stays positive in every
county (King +7.5 to Franklin +16.1).

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

## Appendix G — Off-cycle drop-off by precinct race, income, and education (ecological)

The body of this paper measures age because the voter file carries each voter's birth
year. It carries no race, income, or education — Washington doesn't publish them — so
those can only be looked at *ecologically*, through the Census make-up of a voter's
precinct, with the same ceiling as Appendix F: a precinct-level pattern is not proof
about individuals.

With that caveat, the question is whether the precincts that drop off most between a
presidential and an off-year are also the more nonwhite, lower-income, or less-college
ones — a representation gap beyond age. Using off-cycle *retention* — the share of a
precinct's 2024 presidential voters who came back for the 2025 off-year
(`scripts/diag_wa_offcycle_dropoff_demographics.py`, ~4,700 precincts) — the raw picture
is what you'd expect: whiter, more-college, older precincts hold onto more of their voters
off-cycle (Pearson r ≈ +0.25 on % white, +0.18 on % college, +0.27 on the 65+ share),
more-Hispanic precincts hold onto fewer (−0.20), and income is nearly flat (−0.08).

The sharper question is whether any of that survives the age story, since older precincts
are also whiter. Holding the precinct's 65+ share constant, **education stays the
strongest** — more-college precincts retain more voters off-cycle regardless of age
(partial r ≈ +0.20) — while race attenuates but doesn't vanish (+0.10 on % white, −0.12 on
% Hispanic) and income stays near zero. So there's a modest representation gap on
education, and more weakly race, on top of the age gap the paper documents: the off-cycle
electorate isn't only older, it's also somewhat more educated and whiter than the
presidential one, even comparing precincts of similar age.

Every caveat from Appendix F applies and then some. This describes precincts, not people;
it cannot show that any individual nonwhite or less-educated voter is likelier to skip an
off-year. Retention is measured off the current voter file (survivorship applies), the
precinct demographics are apportioned ACS estimates, and race in particular is
unmeasurable at the individual level in Washington at any geography, because the voter
file has no race field. It points to a gap worth a dedicated, better-controlled study —
not a settled finding.

---

## End note — data, reproduction, and series

**Data.** Washington's statewide voter-registration database (April 2026 extract):
the 5.51M-voter roll joined to 27.1M individual vote records and each voter's year of
birth (`data/wa_vrdb.duckdb`); access terms in Appendix B. Official ballot counts are
the certified statewide totals published by the WA Secretary of State
(`results.vote.wa.gov`). Adult-resident age composition is the U.S. Census American
Community Survey 2020–2024 5-year, table B01001 (Washington, FIPS 53).

**Institutional context.** Washington is an unusually informative case because the
formal cost of voting is lower than in many states: registered voters are mailed a
ballot, which they can return by mail without postage or drop in a box; eligible voters
can register or update their registration in person up to 8 p.m. on Election Day; and
registration is automatic through qualifying agency transactions (WA Secretary of State).
Those rules don't remove every barrier — information costs, mobility, local attachment,
address stability, and uneven political recruitment all still matter — but they make it
hard to chalk the age gap up mainly to the friction of voting.

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
