# Who Decides Washington State?

### Who Returns the Ballot? Age Composition in Washington's Odd-Year Electorate, 2021–2025

**Stephen Kirby** · Tikor Consulting · July 2026

*AI-assisted drafting and analysis review. The core voter-file results are reproducible
from public-record data available through lawful request and from the open-source
scripts cited below, including `scripts/verify_who_decides_wa.py`; Appendix F's precinct
analysis additionally depends on project-built ACS-apportionment and precinct-crosswalk
tables described in the reproduction notes (End note). The paper source, code, and
data-acquisition recipe are public at <https://github.com/skirby359/who-decides>; the
underlying voter file is not redistributed. Contact: kirby@tikorconsulting.com.*

## Abstract

Many of Washington's local offices are filled in odd-year November elections, when
turnout runs far below presidential years. This paper asks *who returns those ballots* —
measured, precisely, as who is credited with an accepted ballot, the event the state's
vote history records.
Using Washington's statewide voter-registration database — a 5.51-million-voter roll
carrying each voter's year of birth, linked to 27.1 million individual vote-history
records, of which 26.3 million resolve to a roll row and so to an age — it measures the
age make-up of every November general electorate from 2021 through 2025. The central finding is descriptive: Washington's odd-year electorate is
markedly older than its presidential one. Voters 65 and older were 36.7%, 40.2%, and
40.3% of the 2021, 2023, and 2025 odd-year electorates, against 28.5% in 2024; voters
18–29 fell from 14.2% in 2024 to about 7.6% off-cycle. The result survives
voter-file coverage validation against certified ballot counts, formal bounds for
current-roll survivorship, a closer-in-time roll cross-check that sizes the survivorship
effect, alternative birth-year
assumptions, county-level checks, and exclusion of any single off-year. The off-year electorate is
also older than the registered roll and the citizen voting-age population. Individual
records show it is largely the presidential electorate's *habitual core* (at most 87–96% of
off-year voters also cast a 2024 presidential ballot, after correcting an upward
survivorship bias in that overlap — and a single presidential comparison, not
a regularity across years), while the peripheral voters who drop
off off-cycle skew young. The paper measures ballot return, not votes cast in specific
down-ballot contests, and does not estimate partisan or policy consequences. Its
contribution is a validated, individual-record measurement of age composition across the
presidential–midterm–off-year salience gradient, in a universal vote-by-mail state where
the formal administrative cost of voting is comparatively low.

**Keywords:** election timing; voter turnout; local elections; age representation;
voter files; Washington; vote by mail; off-cycle elections.

---

## The question

Coverage of "turnout" usually asks how *many* people vote. The question that matters
more for how a state is governed is *who*, and the answer shifts depending on which
election you look at. Washington fills many of its most local offices such as city councils,
school boards, port and fire commissions, and many county and judicial seats in
**odd-year, off-cycle Novembers** (RCW 29A.04.321 limits the odd-year statewide general
election chiefly to city, town, and district offices, certain county positions, and
state measures), when only about **38%** of registered voters return a ballot. This
paper looks at who that 38% is, voter by voter.

The short answer: **the odd-year electorate we can observe is markedly older than the
presidential one.** It is not a smaller copy of the presidential electorate; rather, it
is an older one.

**What is measured.** This paper measures **credited participation**: whether the county
credited a registered voter with an **accepted** ballot for a November general, one voter
at a time. Washington assigns voting credit when a ballot is *accepted*, not when it is
returned — a returned ballot rejected for a signature or timing defect never enters the
vote history (Appendix A measures that channel directly and finds it far too small to
carry the age gap). With that definition stated, "ballot return" and "returner" are used
below as readable shorthand for credited participation. It does *not* tell us whether that
voter actually marked a specific city-council, school-board, port, fire, judicial, or
county race; the voter file records that someone voted in an *election*, not in a given
*contest* (Lucero et al. 2025). That gap matters for the **even-year what-if** — if local
races were moved onto the longer even-year ballot, some of the added voters would return a
ballot but skip the local race — and it matters within the odd-year measurement too. It
would be convenient to argue that the odd-year gap is the smaller of the two, on the
reasoning that Washington's odd-year ballot is mostly local and district contests so
ballot return is a close stand-in for local-race participation. **Measured, that holds for
statewide measures and fails for local offices.** Against a conservative per-precinct
ballot floor, odd-year roll-off across 2021/2023/2025 runs about **4–25%** for mayor,
**16–20%** for port commissioner, **10–36%** for city council, **19–36%** for school
director and **30–44%** for fire district — while the statewide item on the odd-year
ballot rolls off only **3.9–5.6%**, about what an even-year statewide measure does
(`scripts/diag_wa_rolloff_oddyear.py`; Appendix F). So the offices this paper is about are
exactly the ones where ballot return is *not* a close stand-in. Every result below is
therefore about **who returns an odd-year ballot**, not about who votes in any particular
local contest. Appendix F takes up roll-off as the live counterargument, on both sides of
the comparison.

---

## Data and validation

**Source.** `voting_history` (27.1M records across 24 election dates, of which 26.3M —
96.9% — resolve to a current-roll voter and therefore to an age) joined to `voters`
(year of birth, ~100% coverage of the roll) from Washington's standard statewide VRDB
extract (April 2026;
provenance and use terms in Appendix B). Age is based on election year − birth year;
cohorts are assigned per election. November generals only, 2021–2025.

The sharpest objection to any voter-file study is: *you did not measure the electorate;
you measured the part of it still visible in your current voter file.* Because the
vote-history table is tied to a current (2026) roll, anyone who voted in 2021–2024 but
has since died, moved, or been dropped is missing. If those departed voters were a random
slice, losing them would not matter; if they skew young, the finding would be overstated.
Both are testable, and the answers favor the finding.

**Coverage is high, and the worst case is bounded directly.** We benchmark the
reconstruction against certified WA Secretary of State ballot counts, from the
per-election turnout pages (`results.vote.wa.gov/results/<yyyymmdd>/turnout.html`;
e.g., November 2021: 1,896,481 ballots counted, 39.38% turnout). "In file" counts distinct voters in the cumulative vote-history
table for an election; "Analyzable" also requires a match to the April 2026 roll with a
year of birth. Analyzable coverage runs from **90.8% in 2021 to 99.6% in 2025**,
improving sharply over time. The weakest year is the 2021 off-year, which is exactly why
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
| Cast a ballot Nov 2023 (n≈44K) | **69.0%** | 4.5% |

Leaving the roll is age-loaded more broadly: of the 504K voters (9.5%) who left the roll
between 2023 and 2026, 33.1% were 65+, versus 23.9% of those who stayed which is consistent with
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
election" filter, whose real effect is about **0.001** points — the two figures are 36.7508
and 36.7497 and straddle a rounding boundary, so the printed tenth of a point is an artifact
of rounding, not the filter). Min/max apply the extreme assumption to
the residual = official − analyzable.</sub>

Even under the most hostile assumption, in which every unobserved off-year ballot was cast by
someone under 65, each off-year electorate (**33.4% / 38.6% / 40.2%** 65+) stays older than the
presidential electorate under *its* most favorable assumption (**≤30.0%**, i.e. even if
every missing 2024 ballot were 65+). The bound's one structural assumption is stated
rather than left to be inferred: the analyzable records must be a **subset** of the
certified-ballot universe, so that the residual is omission rather than offsetting
false-positive and missing records. That is consistent with the reconstruction sitting
below the certified count in all five years, and the verifier fails if any year's
analyzable count ever exceeds its certified one. The conclusion is that the finding does not depend on how the missing
voters are assigned. Two points follow: given the attrition evidence, the observed
estimates are **likely conservative**, and the **formal worst-case bound** keeps the
finding either way.

**Quantifying the attrition: the composition barely moves under a closer-in-time roll.**
The bound above says nothing about the missing residual. This check asks how much the
attrition just described actually costs the composition estimate. It is **not
independent** of that attrition table — its population is the current-roll electorate
plus the very drop-offs tabulated above, so blending those two published numbers
reproduces the snapshot column to within 0.2 points. What it adds is the *size* of the
effect, not a second source of evidence for it. The database's
Sept-2023 snapshot (`voters_20230901`) still holds voters who have since dropped off the
2026 roll, so it rebuilds the 2021–2023 electorates from a roll much closer to those
elections. The two reconstructions agree to within ~1.4 points, and what movement there
is runs *upward*, consistent with the current roll slightly undercounting seniors:

| Election | Current-roll 65+ | Sept-2023-snapshot 65+ | Δ |
|---|--:|--:|--:|
| Nov 2021 (off-year) | 36.8% | 38.1% | +1.4 |
| Nov 2022 (midterm) | 31.0% | 32.4% | +1.4 |
| Nov 2023 (off-year) | 40.2% | 41.1% | +0.9 |

The snapshot, which recovers older voters the current roll has since dropped, comes out
slightly *higher*, not lower, so the composition finding is not an artifact of building it
from a current roll. The 2021 and 2022 comparisons are the cleanest, because the
September-2023 snapshot comes after those elections. Read the 2023 comparison more
cautiously: the snapshot predates the November-2023 election by two months, so it misses
late-2023 registrants who voted that November, and if those late registrants skew younger,
as new registrants often do, the snapshot's 2023 estimate may run slightly *high*.
Even so, the check reassures: the closer-in-time reconstruction never makes an electorate
younger than the current-roll version, and 2021–2022 point the same way.

---

## What the data shows

The robust cut is **composition**: each age group's share of the ballot-returning
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
- **The senior-to-youth ratio widens by about two and a half times off-cycle**, from
  about **2:1** in the presidential year (28.5/14.2 = 2.0) to about **5:1** off-year
  (39.1/7.6 = 5.1, a 2.55× widening; the individual off-years run 4.9 / 5.5 / 5.0), with
  the midterm in between (31.0% 65+). The
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
| Active registered roll (April 2026) | 16.1% | 26.2% | 30.4% | 27.3% | 49 |
| 2024 presidential ballot-returners | 14.2% | 24.9% | 32.4% | 28.5% | 52 |
| Off-year ballot-returners (2021/23/25 avg) | 7.6% | 19.6% | 33.6% | 39.1% | 59 |

<sub>† Age composition from ACS 2020–24 five-year (the most recent five-year vintage;
the 2024 one-year is consistent), reproduced by `scripts/acs_wa_adult_age.py`: total
18+ residents from table B01001, and the **citizen voting-age population (CVAP)** (the
eligible-electorate benchmark, which excludes non-citizens) from table B29001. Median
ages for the two ACS rows are interpolated from the age brackets and the roll and
ballot-returner medians are computed from year of birth and are integer-year (±1)
approximations. Roll and ballot-returner figures from the VRDB
(`scripts/verify_who_decides_wa.py`).

**The roll row is the ACTIVE roll — the population the word "registered" denotes
everywhere a rate appears in this paper.** Every official turnout rate quoted here —
39.38 / 63.82 / 36.41 / 78.95 / 39.24%, and the headline ~38% — has the active roll as
its denominator, which the arithmetic confirms:
2,001,425 ballots ÷ 39.24% = 5,100,471 against an active roll of 5,098,276, a 0.04% match.
The 5.51M full roll additionally carries 416,492 inactive registrants (7.6%), who are much
younger than active ones (median 38 against 49; 13.2% are 65+ against 27.3%; 25.1% are
under 30 against 16.1%); on that basis the full roll including inactive registrants reads
16.7% / 27.2% / 29.8% / 26.3% with median 48 — about a point younger at each end, which
*widens* the electorate-versus-roll gradient. An earlier version printed the full-roll
row as the headline for consistency with the rest of the series; the active roll is the
sterner comparator and is now primary, with the full-roll figures kept here as the
sensitivity.</sub>

The 65+ share climbs **21.1% → 22.6% → 27.3% → 28.5% → 39.1%** across the five rows; the
18–29 share falls **20.0% → 19.8% → 16.1% → 14.2% → 7.6%**. The median off-year
ballot-returner is **59**, about a decade older than the median registered voter (49),
and more than a decade older than the median citizen-voting-age adult (~47). Residents,
eligible citizens, registrants, and voters are four different populations, and what moves
the composition is participation, not the roll. The roll's senior share is low and steady
(26.3% on the full April 2026 roll; ~22–25% on the per-election eligible roll in these
years) while the off-year returner share reaches ~39%.

**One number for "how unrepresentative."** We can collapse the ladder into a single
dissimilarity index, that is how far each electorate's age distribution sits from the citizen
voting-age population, taken as half the summed absolute differences across cohorts, where
0 means identical. It comes out **7.4** for the 2024 presidential electorate, **13.2** at
the midterm, and **18.5–19.9** across the three off-years. The off-year electorate is
roughly **2.5× as age-unrepresentative** — that is the least favourable of the two natural
readings, the lowest off-year against the presidential year; the three-off-year mean gives
2.6× — of the eligible population as the presidential
one. The index depends on the age bins chosen, so treat its value here as comparative,
not absolute.

<sub>Recorded gender shows a much smaller secondary pattern: the electorate is majority
recorded-female throughout, at 52.5% in the 2024 presidential electorate and
52.5–53.1% across the off-year electorates — 2021 is level with the presidential year,
while 2023 and 2025 sit at 53.0% and 53.1% — concentrated among older voters. Because the
shift is small and administrative gender is not the paper's focus, the analysis treats
age as the primary dimension.</sub>

The mechanism is differential participation. The within-cohort rates below make it
concrete. 18–29 year old participation falls from **58.4%** (2024) to about **16%** off-year,
while 65+ slips only from **88.3%** to **~61%**. These rates *back up* the
composition finding; they do not carry it:

**Within-cohort participation rate (current-roll reconstruction, not official turnout):**

| Election | Type | 18–29 | 30–44 | 45–64 | 65+ | All |
|---|---|--:|--:|--:|--:|--:|
| Nov 2024 | Presidential | 58.4% | 68.6% | 80.1% | 88.3% | 75.0% |
| Nov 2022 | Midterm | 36.4% | 52.5% | 69.6% | 84.6% | 62.4% |
| Nov 2021 | Off-year | 16.5% | 28.6% | 43.1% | 65.6% | 39.4% |
| Nov 2023 | Off-year | 14.5% | 24.6% | 37.1% | 59.0% | 34.9% |
| Nov 2025 | Off-year | 16.4% | 27.0% | 39.0% | 59.3% | 36.7% |

**These are not official turnout rates.** The denominator is the age-eligible **April
2026 roll** filtered to voters registered on or before each election, not the roll as it
stood on election day, and the numerator is the vote-history reconstruction rather than
the certified count. The "All" column sits below Washington's official general-election
turnout in every year (39.38% 2021, 63.82% 2022, 36.41% 2023, 78.95% 2024, 39.24% 2025),
but **not for one single reason**, and three effects are in play at once:

| | roll vs official registered, **as built** | roll vs official registered, **matched (active only)** | voters vs certified ballots | reconstructed rate | official rate |
|---|--:|--:|--:|--:|--:|
| 2021 | −9.2% | **−15.4%** | −9.2% | 39.35% | 39.38% |
| 2022 | −3.9% | **−10.9%** | −6.0% | 62.42% | 63.82% |
| 2023 | +0.2% | **−7.4%** | −4.1% | 34.87% | 36.41% |
| 2024 | +3.1% | **−4.9%** | −2.1% | 74.98% | 78.95% |
| 2025 | +6.4% | **−1.8%** | −0.4% | 36.74% | 39.24% |

Reading the first column alone invites a wrong story, and an earlier version of this
paragraph told it: that the denominator pushes the rate up in 2021–22 and down from 2023,
so the two error sources oppose each other. **The apparent sign flip is a population
mismatch.** The reconstruction's denominator counts every registrant, active or inactive;
official registered counts only active ones (§*Residents, registrants, voters* above shows
the arithmetic). The reconstruction therefore carries 298K–415K inactive registrants the
official figure never had. Put both on the same footing — column two — and the
reconstructed roll is **smaller in all five years**, shrinking monotonically as the
registration-date filter has less history to discard.

So the three effects are: a **numerator** shortfall (vote-history coverage, from the
validation table), a **denominator** shortfall (the registration-date filter, which drops
everyone who registered later), and **inactive inclusion**, which inflates the denominator
by 7.3 to 8.4 points and partly masks the second. On a fully matched active basis the
reconstructed rates run *above* official in every year (41.1 / 65.0 / 37.1 / 79.2 / 39.7%),
which is what a denominator missing later registrants should do.

The table is retained on the as-built basis because that is the denominator the rate table
above actually uses. But 2021's near-exact agreement with the official 39.38% is a
coincidence of three effects cancelling in the year with the weakest coverage (90.8%), not
a validation of anything. Read the table as a current-roll *reconstruction* of within-cohort
participation, not as a turnout estimate. It also rests on a single presidential (2024) and
single midterm (2022) cycle.

---

## Sensitivity

The finding does not hinge on the cohort boundaries, the birth-year assumption, any single
off-year, or King County.

**Finer cohorts.** Splitting the endpoints sharpens the pattern: the 75+ share rises from
**11.8%** in the presidential year to **13.4–18.3%** off-year — 2021 is the low, with 2023
and 2025 at 16.8% and 18.3% — while the 18–24 share falls from **7.7%** to **~3.7–4.0%**.

| Election | Type | 18–24 | 25–29 | 30–44 | 45–64 | 65–74 | 75+ |
|---|---|--:|--:|--:|--:|--:|--:|
| Nov 2024 | Presidential | 7.7% | 6.5% | 24.9% | 32.4% | 16.7% | 11.8% |
| Nov 2022 | Midterm | 5.3% | 5.1% | 22.9% | 35.7% | 19.4% | 11.7% |
| Nov 2021 | Off-year | 3.7% | 3.8% | 19.7% | 36.0% | 23.3% | 13.4% |
| Nov 2023 | Off-year | 3.7% | 3.6% | 19.2% | 33.2% | 23.4% | 16.8% |
| Nov 2025 | Off-year | 4.0% | 4.0% | 19.9% | 31.7% | 22.1% | 18.3% |

**Birth-year assumption.** The file gives year of birth, not the full date, so the main
analysis takes age = election year − birth year to standardize age (We assume the birthday has
already happened by the November election). That can label voters with late-November or
December birthdays as a year older than they really were on Election Day. As a check, we
recompute the 65+ share under the opposite extreme, treating every voter as if their
birthday had *not* yet come (a Dec-31 assumption). That moves the off-year 65+ share by
**≤2.4 points** (e.g., 2021: 36.8% → 34.3%; 2025: 40.3% → 38.2%) and leaves the
presidential/off-year gap intact (the presidential share moves too, 28.5% → 26.7%).
Because November falls late in the year, the true value should sit *closer to the main
convention* than to this all-younger extreme, barring unusual late-year birthday
clustering.

**Off-year stability, and statewide measures.** The three off-years land close together
(65+ share 36.7 / 40.2 / 40.3%) despite statewide ballot content that differs more than
is usually noticed:

- **2021** carried three of the state's non-binding tax "advisory votes" (Nos. 36, 37
  and 38).
- **2023** carried **no statewide contest at all.** Washington abolished advisory votes
  in 2023 (SB 5082, eff. July 2023), so nothing statewide appeared that November — a
  fact confirmed here directly: in the loaded precinct returns the best-covered 2023
  general race reaches 4 counties, against 38 for each of the three 2021 advisory votes and
  38 for SJR 8201; the certified SoS export agrees, carrying no 2023 statewide item at all.
- **2025**'s only statewide item was a single fiscal constitutional amendment (SJR 8201,
  on investing the WA Cares trust fund; approved per the WA Secretary of State's
  certified November 4, 2025 results, `results.vote.wa.gov`).

So the contrast is three low-salience measures, then none, then one — a wider range of
ballot content than "the advisory votes were always there" would suggest, and none of it
a high-salience mobilizing contest. Across that range the 65+ share moves 36.7 → 40.2 →
40.3, a **3.6-point spread**, with the low year (2021) also being the year with the
weakest voter-file coverage (90.8%) and the widest bound (33.4–42.6%). That is
**consistent with** statewide ballot content not driving the composition, and it is what
the paper claims; it is not a test of the proposition, because three off-years with no
counterfactual cannot isolate one. Dropping any one off-year leaves the conclusion
intact.

**Geography.** King County (the largest, and the lowest 65+ share — on median age it is not
the state's youngest county) runs younger than the rest at every
salience level, but the gradient shows up everywhere, and is steeper outside the urban
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

**It is not a compositional story, and the composition in fact runs the other way.** The
obvious alternative reading of a statewide senior tilt is that the older, more rural
counties simply weigh more off-cycle. They do not: King — the largest county and the one
with the lowest 65+ share — is **28.7%** of the 2024 presidential electorate and a *larger*
share of every off-year one, at **29.2–32.7%**. So the state's youngest large electorate
gains weight off-cycle while the statewide electorate ages anyway. The within-county effect
is carrying the entire result, and the statewide figures, if anything, understate it.

---

## Interpretation: mechanism, lever, and policy caution

**The observed shift is a participation-rate difference, not a reconstructed
roll-composition difference.** What changed the 65+ share off-cycle? Are older people
turning out at higher rates, or is the registration roll itself getting older? A standard
decomposition that separates the two (Kitagawa–Das Gupta;
`scripts/diag_turnout_decomposition.py`) puts it almost entirely on participation rates. Of the
**+11.8-point** rise in the 65+ share from 2024 to 2025, **+10.9 points (92%) come from
turnout rates** and only **+0.9 from a changing roll**; for 18–29 the split is **−6.0 of
−6.2 points (96.9%) behavioral.** The pattern holds across all three off-years, and in
2021 and 2023 it holds *more* than completely, because the roll effect there runs the
other way:

| 65+, 2024 → | observed rise | rate effect | roll effect | rate ÷ rise | rate share of total movement |
|---|--:|--:|--:|--:|--:|
| 2025 | +11.8 | +10.9 | **+0.9** | 92.0% | 92.0% |
| 2023 | +11.7 | +12.4 | **−0.7** | **105.9%** | 94.7% |
| 2021 | +8.2 | +11.1 | **−2.9** | **134.8%** | 79.5% |

<sub>Two different ratios, kept apart deliberately. "rate ÷ rise" is the rate effect as
a fraction of the observed change; it exceeds 100% whenever the roll effect is negative,
because behaviour then has to overcome the roll as well as produce the rise. "Rate share
of total movement" is |rate| ÷ (|rate| + |roll|), which is bounded by 100% and is the
comparable figure when the two effects have opposite signs. The two must not be quoted
under one name: a negative roll effect requires the rate share of the *rise* to exceed
100%, so a sub-100% figure described as a share of the rise is self-contradictory.
Both ratio columns are computed on **unrounded** effects, not on the one-decimal cells
printed beside them, so recomputing them from this table will differ in the last digit —
2025's 92.0% is 10.86387/11.80520, not 10.9/11.8. Decomposition for all three off-years by
`scripts/diag_turnout_decomposition.py --off <date>`.</sub>

Note that the 2021 roll effect (−2.9 points against an +8.2-point rise) is not
negligible: a third of the behavioural effect there is spent offsetting a roll that had
grown younger. This is largely robust to the survivorship worry — both years in each
comparison are read off nearly the same recent roll, so much of any current-roll
distortion is shared, and correcting the older-skewing attrition described earlier would
only *raise* the senior turnout rate rather than move weight onto the roll. It is not
fully robust: the decomposition's "roll" is the April-2026 roll filtered by registration
date, so registrants who left between the two election dates are invisible to it, which
biases the roll component toward zero and therefore flatters the behavioural share.

**What the reconstructed roll rests on, and how its one weak field was validated.**
Washington law does not guarantee that the extract's registration date is an *original*
registration date: an update's receipt date can replace it, which would misdate updaters
and the reconstruction with them. Measured, in this extract it rarely does. Of the
**4.78 million** registrants present in both the September-2023 snapshot and the
April-2026 roll, **99.7%** carry a byte-identical registration date across the 31
months between them and only **0.23%** were re-stamped later. Per election, at most
**0.07%** of credited voters carry a registration date later than the election they are
credited in — people whose own ballot credit proves the field wrong — and reclassifying
every provably-registered voter as eligible moves no participation rate in this paper by
more than **0.014** points. What this validation cannot see is a non-voting registrant
re-stamped before September 2023; the snapshot identity rate bounds how common
re-stamping is at all. The rate table and this decomposition are conditional on that
measured behavior of the field, not on an assumption about it.

The skew is, on this evidence, principally a **participation-rate difference rather than
a roll-composition one**. The decomposition is an accounting identity, not a
counterfactual: it does not establish that election timing *causes* the rate
differences — that claim rests on the quasi-experimental literature below — and whether
*changing* the timing would change the electorate is likewise a question for that
literature, not for this table.

**The off-year electorate sits almost wholly inside the 2024 presidential electorate —
and, measured longitudinally, its members are habitual voters.** Because we
can follow individual voters, we can see surge-and-decline directly rather than infer it
from aggregates. At most **87–96%** of each off-year electorate also cast a 2024
presidential ballot (the survivorship-corrected bound derived below; the uncorrected,
roll-visible figures read 92–97%), but only **42–48%** of 2024 presidential voters
showed up in a given off-year. Overlap with 2024 is a single presidential comparison and
does not by itself establish a habit; the vote history does. Off-year voters averaged
**4.1–4.4** of the five 2021–2025 November generals, and **73.5–83.7%** cast a ballot in at
least four of the five, against **3.0** and **41.8%** for the presidential electorate —
measured on the current-roll panel, so the survivorship caveats below apply to it as
well.

<sub>**The uncorrected 92–97% range is biased upward, and the bias is measurable.** Membership in a
measured off-year electorate requires survival on the April 2026 roll, so a voter who cast
a 2021 ballot and then died or moved away is dropped from both the numerator and the
denominator — and that is precisely the population which could not have voted in 2024.
Adding back the drop-offs the September-2023 snapshot can still see moves 2021 from 92.2%
to **87.1%** and 2023 from 97.3% to **94.8%**, while 2025, four months from the roll, moves
**0.1** points. Those are lower bounds: anyone who left before the snapshot is invisible to
it too. So the defensible range is **at most 87–96%**, the 2025 figure is the only one close
to unbiased, and the inflation tracks distance from 2024 rather than anything about the
electorates. The direction of the finding is unaffected — a smaller overlap makes the
off-year electorate *less* purely a subset of the presidential one, not more — but the
range should not be quoted at its published precision.</sub> Sorting 2024 presidential voters by whether they *also* voted in the
2023 off-year shows who stays and who drops off: the **habitual core** (voted both; 1.6M)
is **42.8% 65+ and 6.1% under 30**, while the **presidential-only group** (2.2M) is
**18.0% 65+ and 20.2% under 30**. The voters who mostly turn up when a presidential race
is on the ballot are disproportionately young, and the off-year electorate is what is left
once they fall away. Off-year voters have also been registered longer, a median of about
**16–17 years** since they registered, versus **12** for the presidential electorate.
How long someone has been registered is only a rough proxy for lifelong civic
attachment, and because this comparison is limited to voters still on the current roll,
it should be read next to the survivorship checks above, in which attrition drops some past voters
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
over-55 gap). This paper measures Washington's *gap* (about 39% 65+ off-year versus
about 28.5% presidential) not what consolidation would actually do here. But **if
Washington behaved like the places those studies cover, moving local races onto even-year
Novembers would produce a substantially larger and younger local electorate**. A
reasonable extrapolation from California's experience, not a Washington simulation.

**A caution on policy.** There is good reason to *expect* that a smaller, older,
more-organized off-cycle electorate yields different policy (Anzia 2014, on
public-employee pay; Kogan, Lavertu & Peskowitz 2018, on school-district spending). But
the downstream evidence is **heterogeneous across outcomes and studies**, not settled in
either direction. **Ornstein (2024)**, looking at California's 2018 on-cycle
mandate (SB 415) across 236 local governments, finds the expected gains in turnout and
diversity but **no** detectable knock-on effect on who gets represented, who runs, the
incumbency advantage, housing policy, or public-employee salaries — while **Hajnal,
Kogan & Markarian (2025)**, using California's timing changes, find that even-year local
elections **increased minority officeholding for some groups**, Latino representation
most, with effects strongest in presidential years. So: strong evidence on turnout and
composition, evidence of descriptive-representation effects in some settings, and null
findings on several other outcomes. **This paper does not
try to settle that debate.** It measures participation and composition, and the
composition result is not, by itself, evidence that policy is being captured. (The full
list of objections is in Appendix A: preference-intensity, ballot dilution / roll-off,
and age-as-proxy.)

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
  (people vote off-cycle more as they age) from a *cohort* effect (a durable high-turnout
  generation that happens to be old right now). The habitual-core result fits either;
  telling them apart needs a longer individual panel. Appendix H's smooth
  single-year-of-age curve is consistent with the life-cycle reading but is subject to
  the same limit.
- **Cycle coverage.** The vote history begins in 2021, so the presidential row rests
  on **2024 alone** and the midterm on **2022 alone**; only the off-year row averages
  three cycles.
- **King County is missing from the results database, though not from the voter file.**
  Two distinct gaps, and the second is the one that constrains this paper. King's 2020
  presidential returns are not loaded, which is moot here because all figures are 2021+.
  The **precinct-level** gap is separate and is ours, not the state's: King publishes no
  precinct detail in the Secretary of State's statewide export in *any* year — its rows
  there are countywide totals — and this project's King precinct rows come from a separate
  county file that exists for the even-year generals only. So every contest-level cut in
  Appendix F's odd-year table runs on 38 of 39 counties, and that is an acquisition gap
  rather than a disclosure gap. The body's composition, rate and habitual-core results are **not** affected: they
  come from the voter file, where King is fully present.
- **Uncertainty.** The VRDB figures are near-complete counts and carry no sampling
  error; the ACS resident/CVAP rows are 5-year *estimates* with margins of error (small
  at this geography and level of aggregation, but not zero); and the county roll-off
  correlation (n=39) is reported without a confidence interval; it is descriptive, not
  inferential.
- **The rates are a current-roll reconstruction**, not official turnout (above); the
  **share-of-electorate** figures, which need no denominator and are bounded and
  validated, are what carry the finding. Methods detail in Appendix C.

---

# Appendices

## Appendix A — The objections, in full

The most obvious objection is also the weakest: **this is voluntary participation, not
disenfranchisement.** Washington votes entirely by mail, postage prepaid, with automatic
and same-day registration, so no one is shut out of the off-year ballot, and the fix, moving
local races onto even-year ballots, is an
ordinary scheduling choice. This is a question of **design**, not rights. Explaining
*why* the off-year electorate is older does not make it any less old: the gap is there
however you judge it.

That claim has one channel that could falsify it, and asserting it is not enough: Washington
credits a vote when a ballot is **accepted**, not when it is returned, so signature-mismatch
and late arrival can shut someone out after they have voted. Rejection does skew young —
**2.89%** of ballots from under-30 voters against **0.76%** from 65+, a ratio of
**3.8**. But the effect on this paper's measure is **0.13 points** on the 18–29 share of the
electorate, against a composition gap of about 6.6 points, so it cannot account for the
finding. Two limits on that check, both real: it runs on the **August 2026 primary**, the
only Washington election with a published per-voter ballot-status file, so it is indicative
of the channel rather than a measurement of it in 2021, 2023 or 2025; and it reads the panel
at its latest snapshot, so ballots cured afterwards still count as rejected and the gap is
if anything overstated. The frame survives the objection, but it survives it by measurement
rather than by assertion. (It is also what makes Washington a useful test case. In a prepaid,
same-day-registration state the usual "too hard to vote" explanation for young
drop-off is weak, so the age gap is hard to pin on friction.)

Three other objections:

**1. Maybe the off-year electorate is a filter for engagement, not a defect.**
Perhaps the people who bother to return a low-salience local ballot are better informed,
more rooted locally, and more directly affected by property taxes, schools, and utility
districts, while presidential-year voters, pulled in by the national race, know *less*
about local contests and lean on national cues. This is the real normative crux, and
three things bound it. (a) It is a claim about the *quality* of the marginal voter, which
a participation study like this one cannot measure or settle. (b) It runs against a large
body of work finding that on-cycle electorates are *more* representative of the
population by age, race, and partisanship (Hajnal, Kogan & Markarian 2022), closer to
the community the government actually serves. (c) The information gap it assumes is
itself partly a product of off-cycle timing (thin news coverage), so it is not cleanly
separate from the scheduling choice.

**2. Ballot dilution / down-ballot roll-off.** If local races move to even years, more
people get the ballot but some skip the local contest, so the number actually voting in
that race grows by less than total turnout does. Appendix F measures this directly for
Washington. In the 2024 even-year general, roll-off, the share of returned ballots that
skip a given contest, was **~3–7%** for partisan statewide offices and ballot measures,
**~16–17%** for *contested* nonpartisan statewide races (Supreme Court, Superintendent of
Public Instruction), and **~34%** for *uncontested* ones. Nonpartisan judicial races are
the closest even-year stand-in — a plausible comparison class, not a bound — for the
local nonpartisan races (city council, school board) that consolidation would add. That is higher than the classic ~2–10% estimate (Wattenberg, McAllister &
Salvanto 2000, who tie roll-off largely to *information*), and we do not assume it is
age-neutral for Washington's local races, as that is untested. **The comparison has to be
made symmetrically, and originally was not:** the ~38% odd-year figure is *ballot return*,
while the even-year figures are contest-level, so subtracting roll-off from one side only
biased the comparison toward enlargement. Odd-year **local** contests roll off too — 4–44%
on a conservative floor, and 30–44% for fire districts (Appendix F). The odd-year
*statewide* item does not, at 3.9–5.6%, so the asymmetry is specific to the class of
contest this paper is about rather than general.
Applied to both sides, the direction survives: at a common 34% the deciding electorate is
~52% of registered voters on a presidential ballot and ~42% on a midterm one, against an
odd-year ~25% rather than the ~38% the one-sided version compared against. **The net
effect is very likely a bigger electorate; the size of the increase is not pinned down
here**, and depends on whether local races land on a presidential or a midterm-year ballot
and on how local-contest roll-off differs from the statewide-judicial analog both columns
are built on.

**3. Age is not a clean proxy for whose interests matter.** Seniors are heavily affected
by local taxes, emergency services, transit, utilities, public safety, housing supply,
and school levies, and this paper makes no claim that younger people's interests count
for more. The
narrower claim is about **representation**, and it stays entirely inside the registered
electorate the data covers: among registered voters, off-year ballot-returners are much
older than presidential-year ones (median age ~59–60 vs 52, and about a decade older than
the median registrant at 48). If a markedly older slice of the registered electorate is
choosing local officials, then the preferences recorded at the ballot box differ
systematically by age. The off-year electorate is ~39% 65+, over **1.7 times** the
**22.6%** of citizen voting-age Washingtonians who are 65+ (ACS 2020–24 CVAP) and nearly
double the 21.1% of all adult residents, while its 18–29 share (~7.6%) is under
two-fifths of the ~20% in both benchmarks (§ What the data shows). Whether that is
desirable, tolerable, or a problem is a normative question; what this paper contributes is
a measurement of its size.

## Appendix B — Data access and privacy

- **What was obtained.** Washington's standard statewide **VRDB extract**, the single
  public extract the Secretary of State publishes (registrants plus cumulative vote
  history), regenerated monthly. This study uses the **April 2026 extract** (requested
  April 8, 2026). By statute, the public file is limited to each voter's name, address,
  political jurisdiction, gender, **year of birth**, voting record, registration date,
  and registration number, and **no other information from voter-registration records
  is available for public inspection or copying** (RCW 29A.08.710). This is the statutory
  basis for using year of birth rather than full date of birth. The precise restrictions
  are RCW 29A.08.720's: the registration list is a public record whose use **for
  commercial purposes**, and for mailing or delivering **any advertisement, offer, or
  solicitation for money, services, or anything of value**, is prohibited, while the
  statute expressly contemplates political uses; the file is
  **not redistributable**, with penalties at RCW 29A.08.740. Scholarly analysis of
  aggregates, as here, is none of the prohibited uses. Full provenance, the terms under
  which this extract was obtained, and the access
  date: [Data Sources & Reproducibility](data-sources-and-reproducibility.md).
- **Year of birth, not date of birth.** Consistent with the statute, the extract
  supplies **year of birth only**; full date of birth is protected information that
  Washington withholds from the public voter database, and the legislature further
  strengthened voter-data protections in 2026 (SB 5892 / Ch. 213, Laws of 2026, eff.
  Mar. 25, 2026). In our file every birth value resolves to a July-1 sentinel (a storage
  placeholder marking year-only granularity, not a birthday; ages in this paper are
  computed from birth year alone, as described in Section II), confirming that **no full
  date of birth is stored or used here.** The stronger claim — that none was *obtained*
  — rests on RCW 29A.08.710, which limits what the state releases; a sentinel in the
  loaded table cannot establish it, and is not offered as doing so.
- **What is released.** Only aggregate cohort counts, with cell sizes in the thousands
  to millions; no individual-level records, addresses, or names. The analysis scripts
  emit aggregates only, and the repository's product layer additionally enforces a PII
  firewall (`src/wa_analyzer/product/firewall.py`). Only **citations and code, not
  data** are published.

## Appendix C — Methods

- **Source and unit.** `voting_history` (27.1M records) joined to `voters` (year of
  birth, ~100% coverage), cohorts assigned per election. November generals only. The
  unit is **credited participation** — an accepted ballot, the event Washington's vote
  history records — with "ballot return" as the shorthand defined in "The question";
  it is not participation in a specific contest.
- **Age convention.** With year of birth, age = election year − birth year
  (equivalently, birthday assumed reached by November). This is a ±1-year approximation
  of true age; the birth-year-imputation sensitivity (Sensitivity) shows the alternative
  extreme moves the off-year 65+ share by ≤2.4 points and leaves the gap intact.
- **Composition vs rates.** The within-cohort *participation rates* are a current-roll
  reconstruction (denominator = the age-eligible April 2026 roll restricted to voters
  registered on or before each election, not the election-day registered cohort), so
  they are not official turnout and are reported only to show the mechanism.
  The **share-of-electorate** figures, which need no denominator, carry the finding.
- **Coverage and bounding.** Coverage of the analyzable electorate against certified
  counts is 90.8–99.6%. Two distinct claims: the observable attrition component skews
  old, so the observed estimates are *likely conservative*; and, assuming nothing about
  the residual, a formal worst-case bound (every missing voter under 65) still keeps
  each off-year 65+ share above the presidential one, so the finding does not depend on
  the residual's composition.
- **Decomposition.** The behavior-vs-rolls split is the symmetric two-factor
  (Kitagawa–Das Gupta) standardization (Appendix D).
- **Reproduction.** `scripts/verify_who_decides_wa.py` re-derives the great majority of the counts in the
  tables above from scratch (validation, survivorship, bounding, finer cohorts,
  imputation, geography, decomposition, habitual-core overlap, snapshot cross-validation,
  gender, representativeness index, the 39-county table, and Appendix H's
  banding-robustness ratios), independently of the analysis code. **What it does not
  re-derive it declares, in its own `UNCHECKED` list:** the row-by-row single-year
  retention curve (printed by `scripts/diag_wa_age_curve.py`) and the two external ACS
  benchmark rows. The ecological
  roll-off correlation is in `scripts/diag_wa_rolloff_2024.py`, and the precinct-level
  SES-controlled sequel (Appendix F) in `scripts/diag_wa_rolloff_precinct.py`.

## Appendix D — Related work

The core finding, that low-salience electorates are older and smaller, is well
established, and this paper does not claim to discover it. The contribution is narrower,
and twofold. First, it gives a **validated, individual-record** measurement of
Washington's recent November electorates across the full salience gradient (presidential
→ midterm → off-year), from ~100% of the state's vote records, in a **universal
vote-by-mail, same-day-registration** state where the usual "too hard to vote"
explanation for youth drop-off is weak. Second, and just as important, it tackles a common
voter-file problem head-on: because past vote records are reconstructed from a *current*
registration file, voters who have since died, moved, or been dropped can go missing, an
assumption many voter-file studies leave unstated. By benchmarking against certified
ballot counts, describing the attrition we can see, and formally bounding the rest, the
paper shows the age-composition result is not an artifact of current-roll survivorship.

- **Turnout composition by salience (surge-and-decline).** Campbell, "Surge and
  Decline: A Study of Electoral Change," *Public Opinion Quarterly* 24(3) (1960):
  397–418. Wolfinger & Rosenstone, *Who Votes?* (Yale, 1980); Leighley & Nagler, *Who
  Votes Now?* (Princeton, 2013); age is among the most durable turnout predictors. Plutzer,
  "Becoming a Habitual Voter: Inertia, Resources, and Growth in Young Adulthood,"
  *American Political Science Review* 96(1) (2002): 41–56; turnout is a habit that
  develops over the life cycle, the frame Appendix H's single-year-of-age curve is
  consistent with.
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
  and Homeownership Drive the Local Turnout Gap," *Urban Affairs Review* (2025); the last is the
  closest analog to the age result here.
- **Contested policy effects of timing.** Ornstein, "Election Timing Revisited:
  Evidence from California's Voter Participation Rights Act" (working paper, 2024);
  turnout/diversity gains but null downstream policy effects. Hajnal, Kogan &
  Markarian, "Who Wins When? Election Timing and Descriptive Representation,"
  *American Journal of Political Science* 69(4) (2025): 1454–1468,
  doi:10.1111/ajps.12930; even-year local elections increased minority officeholding
  for some groups, Latinos most, strongest in presidential years — the
  descriptive-representation counterpoint to Ornstein's nulls.
- **Down-ballot roll-off.** Wattenberg, McAllister & Salvanto, "How Voting Is Like
  Taking an SAT Test: An Analysis of American Voter Rolloff," *American Politics
  Quarterly* 28(2) (2000): 234–250, doi:10.1177/1532673X00028002005; roll-off is
  substantially information-driven.
- **Voter-file / individual-level method.** Ansolabehere & Hersh, "Validation: What
  Big Data Reveal About Survey Misreporting and the Real Electorate," *Political
  Analysis* 20(4) (2012): 437–459; Hersh, *Hacking the Electorate* (Cambridge, 2015).
- **Decomposition method.** Kitagawa, "Components of a Difference Between Two Rates,"
  *JASA* 50(272) (1955): 1168–1194; Das Gupta, *Standardization and Decomposition of
  Rates* (U.S. Census Bureau, P23-186, 1993).

## Appendix E — 65+ share of the electorate by county

The off-cycle senior tilt is not a King County artifact or a rural artifact: the
presidential→off-year shift toward seniors is **positive in all 39 counties**
(all 39 rows re-derived by `scripts/verify_who_decides_wa.py`). Counties are sorted by their 2024 presidential
65+ share; the last column is the average off-year (2023, 2025) share minus the
presidential share. The off-year average uses 2023 and 2025 because their analyzable
coverage is much higher than 2021's (99.6% and 95.9% vs 90.8%); adding 2021 does not
change the conclusion: averaged over all three off-years the gap stays positive in every
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

On the two high-coverage off-years this table reports, the county 65+ share averages
**31.4% (King)** to **65.9% (Jefferson)**; taking all three off-years cell by cell the
span widens to **28.7%** (King 2021) to **66.1%** (Jefferson 2023). Every
county moves toward seniors off-cycle (gaps +8.4 to +17.7 points). The result is a
statewide phenomenon; King is simply its youngest instance.

## Appendix F — Contest-level roll-off on the even-year ballot

The one thing this paper does *not* measure is whether a voter marked a specific
contest. The obvious sequel, and the live objection to consolidation, is
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

<sub>Court of Appeals (eight contests across all three divisions in 2024, but each voted only
within its own district, so none spans the state) and Lt. Governor (loaded in
only 5,355 of 8,111 precincts / 38 of 39 counties, a partial-load artifact, not
roll-off) are excluded; see the script header.</sub>

Two honest points follow. First, Washington's even-year nonpartisan roll-off is not
trivial: about **17%** in contested statewide nonpartisan contests and about **34%** in
uncontested ones in 2024. These are plausible upper-bound analogs for local nonpartisan
races, not direct estimates of city-council or school-board roll-off; voters generally
have less information about judicial and local nonpartisan contests than about partisan
statewide offices, and the age profile of Washington local-contest roll-off remains
untested.

Second, even under large roll-off assumptions consolidation would probably enlarge the
contest-level electorate but the *size* of that enlargement depends on whether local
races move onto a **presidential-** or a **midterm-year** ballot. Using Washington's
recent official even-year turnout as the baseline (share of registered casting a vote
in the local contest):

| Scenario (baseline turnout) | 5% roll-off | 17% roll-off | 34% roll-off |
|---|--:|--:|--:|
| Presidential-year, 2024 (~79%) | ~75% | ~66% | ~52% |
| Midterm-year, 2022 (~64%) | ~61% | ~53% | ~42% |
| Odd-year, 2021/23/25 avg (~38%), current baseline | ~36% | ~32% | ~25% |

**The odd-year row is the one that used to be blank, and leaving it blank was the grid's
worst flaw.** It applied 5–34% roll-off to the two hypothetical rows and zero to the
status-quo row it was being compared against — an asymmetry that flatters the enlargement
claim by construction, and one the paper had justified in prose rather than measured.
Measuring it (`scripts/diag_wa_rolloff_oddyear.py`) shows the assumption was wrong:

**King County is absent from this project's odd-year precinct data, and every figure below
is scoped around it.** `precinct_results` holds no King rows at all for the 2021 and 2023
generals, and for 2025 only the Seattle mayoral race, so King — 29–33% of each odd-year
electorate — contributes no votes to any odd-year contest measured here, and all three
columns run on the same 38-county footprint. **This is a limitation of our acquisition, not
of the public record.** King publishes no precinct detail in the SoS statewide export in any
year (its rows there are countywide totals), and the project's even-year King precincts come
from a separate county file that was never obtained for odd years. The statewide row's
denominator is **exact**: the certified statewide count minus King's certified countywide
ballots, both from the same SoS turnout pages that supply this paper's official
benchmarks (King: 607,869 in 2021, 516,012 in 2023, 654,742 in 2025; pinned with source
URLs and retrieval date in `docs/reference/wa_county_turnout_king_oddyears.csv`, whose
statewide column must reconcile with the official constants or the verifier stops). An
earlier version scaled the statewide count by King's reconstructed ballot share instead,
which made the row an estimate.

| odd-year contest | 2021 | 2023 | 2025 | denominator |
|---|--:|--:|--:|---|
| Statewide item (advisory votes / SJR 8201) | 3.9–5.6% | *none on the ballot* | 4.9% | non-King certified ballots (exact) |
| Fire district | 32.7% | 30.3% | 44.1% | per-precinct ballot floor |
| School director | 21.5% | 19.1% | 35.6% | per-precinct ballot floor |
| City council | 9.6% | 13.0% | 35.6% | per-precinct ballot floor |
| Port commissioner | 17.8% | 16.3% | 19.6% | per-precinct ballot floor |
| Mayor | 4.2% | 3.8% | 25.2% | per-precinct ballot floor |

<sub>The floor is the best-attended contest in each precinct, which itself rolls off, so
those rows are **lower bounds** — and the bias is **not a common shift, so the rows are not
comparable with one another.** A contest that is itself frequently the best-attended one has
its measured roll-off forced toward zero by construction, and how often that happens varies
about twentyfold across these five offices: at worst mayor defines the floor in **53.7%** of
its precincts and city council in **27.9%**, against **29.9%** for school director,
**11.3%** for port commissioner and **9.6%** for fire district. That ordering is close to
the inverse of the measured one, so the *ranking* below is substantially an artifact of the
estimator and should not be read as one office rolling off more than another. What survives
the objection is the only thing the row is used for: odd-year local roll-off is not zero,
and for several offices it is large. They also pool contested with uncontested races, which
the even-year table above deliberately separates (16.6–17.2% contested against 33.7–34.4%
uncontested), so they are not like-for-like with the 17% column — a large part of the
2025 city-council and school-director figures is uncontested races, which is this
series' companion subject.</sub>

**The two rows say different things, and only one of them is a problem for the grid.** A
*statewide measure* on an odd-year ballot rolls off 3.9–5.6%, which is essentially what a
statewide measure on an even-year ballot does (4.1–5.6%) — so for that class of contest the
paper's original reasoning was right. *Local offices* are the ones this paper is about, and
several of them roll off far more: fire district 30–44%, school director and city council up
to 36%. Those are the contests consolidation would move, and treating their odd-year
participation as equal to ballot return is the assumption that does not survive.

**What this does to the conclusion.** Applying roll-off to both sides rather than one
narrows every comparison but does not reverse the direction: at a common 17%, presidential
consolidation still reads ~66% against an odd-year ~32%, and midterm consolidation ~53%
against ~32%. What it removes is the *margin of safety*. On the old one-sided grid the
midterm/uncontested worst case (~42%) still beat the odd-year baseline (~38%); on a
symmetric reading the comparison is between two numbers carrying the same unmeasured
uncertainty about how local-contest roll-off differs from the statewide-judicial analog
each column is built on. The grid also treats roll-off as *fixed* across scenarios, which
it is not: a presidential electorate contains more peripheral voters — people who turn out
only for the highest-salience contest and skip down-ballot races at higher rates — so its
true roll-off is likely higher than a midterm electorate's, making the presidential row an
upper bound and the presidential–midterm gap narrower than shown. The defensible
conclusion is narrower than "consolidation enlarges the contest-level electorate": it is
that the turnout advantage is large enough to survive symmetric roll-off assumptions,
while the size of the enlargement is not pinned down by anything in this paper.

**Does roll-off skew young? An ecological first look.** The concern behind this
objection is that the young voters consolidation would add are also the ones most likely
to skip a local contest. Cast-vote records cannot answer this directly as ballots are
anonymous and carry no voter age, so the roll-off *age profile* is unmeasurable at the
individual level under secret-ballot rules, and an ecological cut is the ceiling.
Across the 39 counties, roll-off on that contest is if anything *higher* where the
electorate is older (a correlation, Pearson's r, the standard linear correlation
coefficient, of **+0.57**, ≈+0.6, **uncorrected for urbanicity**); that is, the
county pattern does not show younger places skipping the contest more. This is weak
evidence: it is ecological, confounded with the rural/urban gradient (older counties
are rural, with thinner coverage of statewide judicial races), and measured on a
*statewide* judicial race that is an imperfect analog for hyperlocal contests. It
points away from young-concentrated roll-off but cannot establish individual behavior.
A finer precinct-level ecological analysis is the natural sequel, and the next paragraph
runs it; an individual-level administrative test is not available from public cast-vote
records, because ballot secrecy prevents linking contest choices to voter age.

**A closer look, precinct by precinct.** The county number has one real weakness: in
Washington the older counties are also the rural ones, so a county-level correlation cannot
tell whether roll-off follows *age* or just *rural*. The +0.6 blends the two; the earlier
county cut said as much. Precincts let us separate them. Across 4,859 precincts — **60% of the state's 8,111**. Every precinct has a 2024
presidential vote, so the losses are two: 5,355 precincts carry apportioned Census
demographics, and a floor of 50 presidential votes removes a further 496 of those
(`scripts/diag_wa_rolloff_precinct.py`), roll-off in the Supreme Court Pos. 2 race averages
**16.4%**. The statewide comparison has to be made carefully, because the two cuts use
different denominators: the table above divides by *certified ballots counted* (giving
17.2% for this race), while the precinct cut divides by *President votes in the same
precinct*. Put statewide on the precinct cut's own basis — 3,279,291 Supreme Court votes
against 3,918,934 presidential votes — and it is **16.3%**, against the precinct mean of
16.4%. The two agree closely; what does not transfer between them is the 17.2% figure,
which belongs to the ballots basis. (President itself rolls off 1.1% against ballots,
which is the whole of the difference.)

The county cut's *direction* survives; its *strength* does not. On the same yardstick the
county used (the share of a precinct's 2024 voters who are 65 or older), the correlation
falls from +0.6 to about **+0.09**, under a sixth as strong, because moving from 39
counties down to thousands of precincts strips out the lumping-together that had
exaggerated it. A second, different predictor — a precinct's older *residents* rather than
its older *voters*, from the Census — gives **+0.26**, also small and pointing the same
way. The two are not interchangeable, and the next paragraph controls both separately.

The real value of working at the precinct level is that we can account for how
urban and how well-off a place is. Put the age figures next to each precinct's income,
education, home values, share of renters, and size as a stand-in for the urban-versus-rural
and rich-versus-poor divide, and ask what age still explains on its own. Almost nothing is
left, on either yardstick:

| predictor | raw r | partial r, net of income / education / home value / renter share / log(pop) |
|---|--:|--:|
| Precinct **electorate** 65+ share (the county cut's own yardstick) | +0.09 | **−0.02** |
| Precinct **resident** 65+ share (ACS), contested court race | +0.26 | **+0.11** |
| Precinct **resident** 65+ share (ACS), Superintendent | +0.19 | **+0.02** |

So the big county number does not hold up on any measure. What little survives depends on
which yardstick is used and is small enough that its sign is not worth reading: on the
resident measure it points the *opposite* way from the worry (older precincts skip the
race slightly more), and on the electorate measure — the one the county cut actually
used — it is −0.02, which is nothing. The takeaway is the same as the county version, just
on firmer ground: nothing in these ecological checks supports the fear that the young
voters consolidation would bring in are the ones who would skip a local race, and nothing
in them supports a confident claim in the other direction either. The usual cautions still apply, and they stack up rather than fade: this is
a neighborhood-level pattern, so
roll-off by a voter's own age can never be measured directly; the urban/rural stand-in is
rough, since precincts are drawn to hold about the same number of people and a real density
measure from the map files would do better; and a statewide court race is only a loose match
for a city-council or school-board contest. And the electorate-65+ figures rest on
**4,650** precincts rather than 4,859 — those meeting all four constraints (Census
demographics, 50+ presidential votes, a VRDB crosswalk row, and 100+ precinct voters). The
crosswalk is the one of the four known to be non-randomly incomplete: it bridges **99.3%**
of active registrants statewide but only **35.7%** in Okanogan. **Every test agrees that the effect is near zero; they do not all agree on
its sign**, and at these magnitudes the sign is not information. Two further predictors
the same script produces are reported here rather than left out, since selecting the three
smallest partials would not be a test: ACS median age is the largest surviving partial at
**+0.16** (raw +0.28), and the ACS under-30 share is the only raw predictor pointing toward
the worry, at **−0.11**. Neither changes the reading. (This precinct cut leans on two
tables: Census figures mapped onto precincts, and a voter-file-to-precinct crosswalk; see
the script header.)

## Appendix G — Off-cycle drop-off by precinct race, income, and education (ecological)

Appendix G is exploratory and is not used to carry the paper's main finding. The body
of this paper measures age because the voter file carries each voter's birth
year. It carries no race, income, or education (Washington does not publish them), so
those can only be looked at *ecologically*, through the Census make-up of a voter's
precinct, with the same ceiling as Appendix F: a precinct-level pattern is not proof
about individuals.

With that caveat, the question is whether the precincts that drop off most between a
presidential and an off-year are also the more nonwhite, lower-income, or less-college
ones. Using off-cycle *retention*, the share of a
precinct's 2024 presidential voters who came back for the 2025 off-year
(`scripts/diag_wa_offcycle_dropoff_demographics.py`, ~4,700 precincts), the raw picture
is what one would expect: whiter, more-college, older precincts hold onto more of their voters
off-cycle (Pearson r ≈ +0.25 on % white, +0.19 on % college, +0.27 on the 65+ share),
more-Hispanic precincts hold onto fewer (−0.21), and income is nearly flat (−0.09).

The sharper question is whether any of that survives the age story, since older precincts
are also whiter. Holding the precinct's 65+ share constant, **education stays the
strongest** as more-college precincts retain more voters off-cycle regardless of age
(partial r ≈ +0.21) while race attenuates but does not vanish (+0.11 on % white, −0.13 on
% Hispanic) and income stays near zero (+0.04). These are ecological patterns about places, not
individual-level estimates about voters. They point to a representation gap worth
studying more directly, not to a settled race- or education-level voter finding.

Every caveat from Appendix F applies and then some. This describes precincts, not people;
it cannot show that any individual nonwhite or less-educated voter is likelier to skip an
off-year. Retention is measured off the current voter file (survivorship applies), the
precinct demographics are apportioned ACS estimates, and race in particular is not
**observed** at the individual level in Washington at any geography, because the voter
file has no race field. That is a statement about what the record contains, not about
what is estimable: probabilistic methods such as Bayesian Improved Surname Geocoding
(Imai & Khanna 2016) do produce individual-level race *estimates* from surname and
geocoded address, and are standard on voter files in states that do not collect race. A
BISG-based cut is a reasonable sequel; it is not attempted here, and it would remain an
imputation rather than an observation, with its own well-documented error structure. It
points to a gap worth a dedicated, better-controlled study, not a settled finding.

## Appendix H — The age gradient, one year at a time

The body of this paper reports composition in conventional age bands (the Census
reporting brackets, plus the 18–29 and 65+ lines the turnout literature uses). Bands
are a presentation choice, and a fair question is whether any banding choice
manufactures, or hides, the result. Because the voter file carries every voter's year
of birth, the question can be answered directly: this appendix drops the banding
entirely and reports the gradient one year of age at a time
(`scripts/diag_wa_age_curve.py` prints the full 78-row curve; the verifier asserts every cell of the fifteen rows printed below, the prose figures read off the ages between them, and this appendix's load-bearing claims — the 65-boundary step, the peak, the tail decline, the banding-robustness ratios, and, in code rather than by regex, the two comparative claims no probe can anchor on. The 63 unprinted ages are declared UNCHECKED).

For each single year of age from 18 to 95, the table shows the April 2026 roll count,
participation in the November 2024 presidential general and the November 2025 off-year
general (current-roll reconstructions on the body rate table's own basis: each turnout
denominator counts only registrants at that age enrolled on or before that election, so
the Roll column — the full April 2026 count at that age — is a descriptive column, not
the turnout denominator), and off-year **retention**: the share of that age's 2024
voters who returned a ballot in 2025. Retention is the cleanest of the three measures
here, because both events are read off the same roll, so the current-roll denominator
largely cancels.

| Age | Roll | 2024 turnout | 2025 turnout | Retention |
|--:|--:|--:|--:|--:|
| 20 | 75,896 | 60.5% | 14.6% | 23.0% |
| 25 | 91,312 | 56.8% | 15.9% | 26.3% |
| 30 | 96,668 | 60.3% | 20.6% | 32.9% |
| 35 | 106,887 | 65.9% | 25.8% | 38.4% |
| 40 | 99,309 | 71.1% | 29.8% | 41.6% |
| 45 | 92,301 | 74.5% | 32.6% | 43.6% |
| 50 | 78,068 | 77.0% | 35.2% | 45.5% |
| 55 | 86,879 | 79.9% | 38.4% | 47.9% |
| 60 | 78,167 | 81.7% | 42.5% | 51.8% |
| 65 | 84,252 | 85.3% | 50.1% | 58.6% |
| 70 | 77,479 | 88.4% | 58.7% | 66.3% |
| 75 | 62,085 | 89.9% | 63.4% | 70.5% |
| 80 | 39,097 | 90.0% | 64.5% | 71.4% |
| 85 | 22,346 | 87.2% | 60.5% | 68.9% |
| 90 | 10,165 | 83.1% | 54.5% | 64.6% |

<sub>Five-year steps shown; the script prints all 78 single ages. Ages 18–19 are
omitted from the table for different reasons: an 18-year-old in November 2025 was 17 at
the November 2024 general, so that retention cell has no denominator at all, while 19 simply
falls between the five-year steps shown. 19-year-olds retain at 23.4%, marginally the highest of ages 19-21 — the first-election pattern described below is
visible in presidential *turnout*, not in retention.</sub>

Four features of the full curve matter for reading the body of the paper.

**First, the gradient is a smooth age ramp, not a set of cohort steps.** Retention
rises steadily from 23.0% at age 20 to a peak of 72.0% at age 79 — an average of about
**0.8 points per year of age**, but not an even one: the ramp is shallowest through the
forties and fifties (about 0.4 points per year from 40 to 50) and steepest across the
sixties — 1.37 points per year from 60 to 65 and **1.52 from 65 to 70**, the steepest
five-year stretch on the curve. What matters for the banding
question is that it climbs without a visible breakpoint at the conventional cohort
boundaries used in the body of the paper, and with no birth-year cohort standing out
from its neighbors. That pattern shows that the main result is not manufactured by the
choice of age bands. It is also consistent with a life-cycle interpretation, but it
does not prove one: a durable high-turnout cohort currently concentrated in older ages
could produce a similar cross-section, and separating age from cohort requires a
longer panel.

**Second, there is no discontinuity at 65.** If the senior tilt reflected something
categorical about retirement (time freed for civic life, or a benefits-driven interest
spike), the curve should step upward near 65. It does not: retention moves from 57.5%
at 64 to 60.5% at 66, a two-year step of 3.0 points, against a 5.7-point step across
the four years from 60 to 64. Those are the same per-year slope (1.50 against 1.42
points), so nothing happens *at* 65. This whole stretch is the steep part of the ramp,
running at roughly double the 0.8-point-per-year average — the claim is the absence of a
step at the boundary, not that the sixties climb at the same rate as the forties. "65+"
is a reporting convention, not a behavioral boundary.

**Third, the only material non-monotonic features sit at the two tails — and the two
tails are read off different measures, which has to be said.** At the young end the
non-monotonicity is in **2024 presidential turnout**, not retention: age 20 is a local peak
(60.5%), above both 19 (59.8%) and the mid-20s trough — the familiar first-election bump —
with the minimum of the whole young range at 25 (56.8%). On **retention** the young
ages run the other way and are nearly flat (23.4% at 19, 23.0% at 20, 23.1% at 21), so the
first-election bump is a turnout phenomenon that retention does not show. (Age 18 is
omitted from both: an 18-year-old in November 2025 was 17 in November 2024, so the
retention cell has no denominator.) At the old end, on retention, the curve peaks at **72.0% at age 79** and declines from **80**
onward (71.4% at 80, 69.8% at 84, 64.6% at 90, 59.5% at 95). The decline is not perfectly
smooth — there is one upward step inside the curve's range, 93→94 (+0.70), about ten times the size
of the 51→52 dip described below — but roll counts above 90 fall to the low
thousands, so those steps are noise on small cells rather than structure.
The body's 75+ band blends the plateau and this decline. Along the ramp itself the only
reversal is a 0.07-point dip from 51 to 52, which is noise.

**Fourth, the composition findings are robust to any plausible banding — but not because
the curve is monotone, since it is not.** Retention falls after 79, so an argument from
monotonicity would not be available even if it were the right argument, and it is not:
composition depends on how many people are at each age as well as on how they behave, so
a monotone behaviour curve would not by itself force a monotone composition ordering.
The question has to be answered on the composition measure directly. Doing that — the
ratio of each band's 2025 off-year share to its 2024 presidential share, on five-year
bands — gives 65–69 **1.25**, 70–74 **1.41**, 75–79 **1.54**, 80–84 **1.57**, 85–89
**1.58**, 90+ **1.58**, against 0.83 for everyone under 65. The over-representation rises
across every band and then flattens; the only reversal anywhere is 85–89 against 90+, by
0.007, on the smallest band in the file. So no bracketing a reader would plausibly choose
reverses the ordering the paper reports, and the finding does not depend on the bands
used. It also means data-driven
clustering (for example, k-means on the age axis) would not recover natural behavioral
cohorts: with no internal breakpoints, such methods would split the curve at densities
of the *roll* (the largest birth cohorts), not at changes in behavior. The single-year
curve is also the most suggestive evidence in this paper for a **life-cycle**
interpretation of the senior tilt, subject to the age-cohort-period limit stated
above and in the body's limits section. The habit-formation literature (Plutzer
2002, in Appendix D) points the same way.

---

## End note — data, reproduction, and series

**Data.** Washington's statewide voter-registration database (April 2026 extract):
the 5.51M-voter roll joined to 27.1M individual vote records and each voter's year of
birth (`data/wa_vrdb.duckdb`); access terms in Appendix B. Official ballot counts are
the certified statewide totals published by the WA Secretary of State
(`results.vote.wa.gov`, per-election `turnout.html` pages). Adult-resident and
citizen-voting-age composition are the U.S. Census American Community Survey 2020–2024
5-year, tables B01001 (sex by age) and B29001 (citizen voting-age population by age),
Washington (FIPS 53), retrieved through the Census API and reproduced by
`scripts/acs_wa_adult_age.py`.

**Institutional context.** Washington is an unusually informative case because the
formal administrative cost of voting is lower than in many states: registered voters are mailed a
ballot, which they can return by mail without postage or drop in a box; eligible voters
can register or update their registration in person up to 8 p.m. on Election Day; and
registration is automatic through qualifying agency transactions (WA Secretary of State).
Those rules do not remove every barrier as information costs, mobility, local attachment,
address stability, and uneven political recruitment are still factors, but they make it
hard to chalk the age gap up mainly to the friction of voting.

**Reproduction.** `scripts/verify_who_decides_wa.py` re-derives **873 figures** from
scratch, including the composition, rate and finer-cohort tables, the coverage and
bounding tables, the habitual-core overlap, the snapshot cross-validation, the
representativeness index, the turnout decomposition and Appendix H's banding-robustness
ratios, under a coverage gate that fails on any unprobed number in **every section of this
paper** — the title block, the abstract, the question, the data-and-validation section, the
composition, rate and finer-cohort tables, the sensitivity block, the interpretation
section, the limits list, every appendix A through H, and this end note: nineteen sections
in all. Appendix D is closed by a written reason rather than a derivation, because it is a
bibliography and its page ranges are not quantities; the figures those works are cited
*for* are asserted where the paper uses them. Six claims that carry no numeric token are
asserted in code instead, because a superlative, a spelled-out count or the word "every"
is exactly what a regex gate cannot see: that 65–70 is Appendix H's steepest five-year
stretch, the size of its 93→94 step against the 51→52 dip, that the enlargement grid's
17% and 34% columns still match the measured contested and uncontested roll-off, that the
Court of Appeals had "eight contests" in 2024, that 2023 really carried no statewide
contest, and that every birth value in the loaded file is the July-1 sentinel Appendix B's
privacy argument depends on. Nothing in the paper now sits outside it.

Appendix F is the one section that needs more than the voter file: its figures come from
certified precinct returns, and its closing partial-correlation table also needs ACS
block-group demographics apportioned to precincts and the voter-file-to-precinct
crosswalk. Those are build inputs rather than raw public files, so a reader reproducing
from raw sources can rebuild every other section but will find that one refuses to run
rather than silently skipping.
**Two things it does not re-derive, and says so in its own `UNCHECKED` list rather than
leaving a reader to assume otherwise:** the row-by-row single-year retention curve of
Appendix H (printed by `scripts/diag_wa_age_curve.py`; that appendix's load-bearing claims
are asserted individually), and the two ACS benchmark rows, which are external Census
estimates reproduced by `scripts/acs_wa_adult_age.py` rather than derivable from the voter
file. Appendix E's 39-county table **is** re-derived, all 39 rows. The roll-off
appendix and its ecological age correlation are in `scripts/diag_wa_rolloff_2024.py`, with
the finer precinct-level, SES- and urban-proxy-adjusted cut in
`scripts/diag_wa_rolloff_precinct.py`;
`scripts/diag_wa_individual_findings.py` and `scripts/diag_turnout_decomposition.py`
produce the underlying figures; and `scripts/acs_wa_adult_age.py` reproduces the
adult-resident and CVAP rows from the Census API. All scripts, the paper source, and
the data-acquisition recipe are public at <https://github.com/skirby359/who-decides>.

**Series.** Lead paper of the electoral-health series (with
[`electoral-health-whitepaper.md`](electoral-health-whitepaper.md) and
[`cross-state-fec-money.md`](cross-state-fec-money.md)). Party-resolved companions in
states that publish party of record:
[`who-decides-new-york.md`](who-decides-new-york.md) (deep blue) and
[`who-decides-idaho.md`](who-decides-idaho.md) (deep red).

**Companion paper: [Safe-Seat Washington](safe-seat-washington.md).** Once in an
off-year general, how often is the contest even a choice? It counts **observed**
competitiveness of every partisan legislative + congressional seat, 2016–2024
(**79–88% not close** across the five cycles, 83.5% in 2024), and extends the count to a
four-state lower-chamber map.
