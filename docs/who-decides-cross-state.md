# Who Returns the Ballot?

### Cross-state evidence on age, party, and low-salience electorates — individual-record data from Washington, New York, and Idaho

**DRAFT — pending human/editorial sign-off.** That gate is a person reading the paper end to
end, recorded in [`who-returns-ballot-submission-notes.md`](who-returns-ballot-submission-notes.md)
§Sign-off; `scripts/verify_who_returns_ballot.py` asserts the figures and is not the sign-off.
First assembly 2026-07-22; harmonized and
scoped to three states 2026-08-06. Prose frame, case design, and harmonization protocol are
complete. **Findings 1 and 3 are computed from a single code path** —
`scripts/diag_cross_state_age_harmonized.py` — over the three voter files, with shared age
bins, age measured at each election date, and one ACS vintage for every state's CVAP
benchmark. They are not the three single-state papers' as-reported figures.

**This is a three-state paper by decision, not by omission** (2026-08-06). An earlier draft
described a four-state design with Texas deferred. Texas is now stated as *future work* in
Boundary of inference rather than as a gap in this one: the claim here is about the gradient
within each state's own salience ladder, and three states already span the axes the design
turns on — a high-access no-party-registration state, a blue party-registration state, and a
red closed-primary state. What Texas would add is named precisely, so a reader can judge the
cost of its absence rather than discover it. **The one remaining blocker is the standing
human-verification gate.**

Author: Stephen Kirby (Tikor). Companion to the SSRN-posted lead paper *Who Decides
Washington?* (SSRN Abstract ID 7149263).

---

## The question

A single-state paper answers *what does this state's low-salience electorate look like?*
A multi-state paper answers the general-behavior question: *how far does the off-cycle
age skew travel, and how does it change with party-registration rules and election
administration?* This paper takes the validated, individual-record method of the
Washington lead paper and runs it identically across three states chosen to differ on the
axes that should matter — a high-access no-party-registration state (WA), a blue
party-registration state (NY), and a red party-registration state (ID) — to separate the
part of the pattern that recurs across all three cases from the part that is a feature of a
particular state's institutions.

The two questions this state set can answer, and the one it cannot:

1. Is the off-cycle age skew present across blue, red, and mixed institutional settings?
2. In party-registration states, does off-cycle participation skew toward one party?
3. *Not answerable here.* Where there is no party of record, does the age skew still have
   partisan consequences? Washington is the set's only no-party-registration state and its
   top-two primary records no party ballot, so nothing in this data can resolve it. A state
   with no party of record but a **public party-primary history** — Texas is the obvious
   one — would supply the proxy that makes the question tractable. That is named as future
   work in Boundary of inference, not carried as a placeholder in the design.

## The cases

| State | Party of record | What it contributes | Data on hand |
|---|---|---|---|
| **Washington** | No | High-access baseline: universal vote-by-mail, same-day registration, automatic registration. The clean "access is easy" case; age only. | `data/wa_vrdb.duckdb` (5.51M; year of birth) |
| **New York** | **Yes** | Cleanest blue party-registration comparison. | `data/ny_vrdb.duckdb` (13.54M; party + year of birth) |
| **Idaho** | **Yes** | Red party-registration comparison; a *closed* primary makes party determine which election a voter may even enter. | `data/id_vrdb.duckdb` (1.03M; party + age + primary ballot) |

The three cases were chosen to vary the two institutional axes the argument turns on —
whether the state records party at all, and whether its lowest-salience measured contest is
open to everyone — while holding the method fixed. They do not vary a third axis: **no state here
lacks a party of record *and* publishes a party-primary history**, which is the configuration
that would let the partisan question be asked where party is unrecorded. Texas is that case
and is not loaded; see Boundary of inference.

## Harmonization protocol — the load-bearing methods problem

"Off-year" does not mean the same thing in every state, and pretending it does would
manufacture a false equivalence. This paper therefore compares **election *classes*
defined by salience**, not by calendar:

- **Highest-salience** — the presidential November general. Directly comparable across all
  three states.
- **Midterm** — the even-year non-presidential November general. Directly comparable.
- **Lowest-salience measured contest** — *state-specific by construction, and reported as
  such*:
  - **WA:** the odd-year November local general (RCW 29A.04.321).
  - **NY:** the odd-year November local general.
  - **ID:** there is no odd-year November general; the lowest-salience measured contest is
    the **closed May Republican primary** — the dominant-party nominating electorate.

  *This class was called Idaho's "decisive" contest until 2026-08-17, and that label is
  withdrawn. Whether — and in how many seats — the Republican primary settles the outcome is
  a question about seat decision, not about salience or composition, and this paper measures
  neither. The Idaho companion separates nomination, filing, primary and general as distinct
  stages and declines to call the primary decisive, on its own state's November results —
  see `who-decides-idaho.md` §IV–§V, which owns those figures and gates them. Nothing in
  Findings 1 or 3 depends on the label: the contest enters this
  paper as the lowest-salience electorate each state's file records, and it would enter
  identically if it decided nothing.*

Each state's lowest-salience row is labeled with its class so the comparison is never read
as a shared calendar. Three further comparability controls travel with every figure:

- **Age precision differs** (WA year-of-birth; NY/ID date-of-birth or integer age) — all
  cuts use whole-year age bins to a common definition.
- **Vote-history depth differs** — metrics use each state's available reconstructed
  history and state the window.
- **List-maintenance differs** — Idaho's roll contracted ~13% over the window, which makes
  ID turnout *rates* unusable; ID is therefore reported as **composition shares only**, and
  all states foreground shares over rates (the WA paper's practice).

## Finding 1 — The off-cycle age skew recurs across all three cases

As salience falls, the electorate ages, in each of the three states and regardless of
party-registration regime. The presidential and midterm rows below are directly comparable;
the lowest-salience row is each state's lowest-salience measured class (labeled).

| State | Presidential 65+ / 18–29 | Midterm 65+ / 18–29 | Lowest-salience 65+ / 18–29 (class) |
|---|---|---|---|
| **WA** | 28.5% / 14.2% | 31.0% / 10.4% | 36.8–40.3% / 7.4–8.0% (3 odd-year Nov generals) |
| **NY** | 28.2% / 14.1% | 30.6% / 9.8% | 28.4–41.6% / 6.0–11.5% (5 odd-year Nov generals) |
| **ID** | 29.0% / 15.2% | 34.4% / 8.6% | 41.4–48.6% / 5.0–5.6% (3 closed May GOP primaries)¹ |

<sub>¹ Idaho has no odd-year November general; its lowest-salience measured contest is the
closed May Republican primary, whose electorate is older than any general (Idaho paper
§IV). The midterm column already shows the gradient reaching 34.4% 65+ before the primary
cut. All cells above are computed by `scripts/diag_cross_state_age_harmonized.py` from one
code path over the three voter files — shared age bins, age measured at each election date —
so they are directly comparable to each other rather than transcribed from three papers'
per-state conventions. **The low-salience column uses every such contest in each state's
loaded history**, not a selection: 3 / 5 / 3 contests. An earlier version used 3 / 2 / 1, and
the omissions were doing work — New York's floor read 34.4% rather than 28.4%, and Idaho
appeared as a single point rather than a range.</sub>

**The low-salience column is confounded with distance from the 2026 roll, and the confound is
large.** These are current-roll reconstructions, so a voter who cast a ballot in an earlier
contest appears only if they are still registered in 2026 — and departures skew old. Both
multi-contest series run in exactly that direction:

| | earliest → latest |
|---|---|
| NY odd-year generals, 65+ | **28.4** (2017) → 32.9 (2019) → 36.3 (2021) → **41.6** (2023) → *34.4* (2025) |
| ID closed R primaries, 65+ | **41.4** (2022) → 46.7 (2024) → **48.6** (2026) |

<sub>**New York's 2025 cell is printed in italics because it breaks the pattern, and an
earlier version of this table omitted it.** A recency ladder that drops its most recent
observation, in a paragraph arguing recency drives the pattern, is the omission of the
disconfirming case from the display that establishes the confound. 2025 is genuinely a
different construct from the other four — it POSTDATES the November 2024 reference, so its
reconstruction bias is near zero rather than growing with lag — but that is a reason to
label it, not to leave it out. Read the first four as the lag series and 2025 as the control:
the least-biased cell in the row reads younger than three of the four that precede it.</sub>

New York's odd-year 65+ share climbs 13 points across four contests in near-perfect order of
recency, and Idaho's climbs 7 across three. Some of that is real — 2023 and 2025 were
different contests — but no reading of these series should treat the spread as purely
substantive, and **cross-state comparisons of the low-salience *level* are not safe**, because
the states' cells sit at different lags (Idaho's 2024 primary is 2 years before the snapshot;
New York's cells span 1 to 9). What the confound does not touch is the within-state
*direction* — every low-salience contest is older than its own presidential one — which is
the claim Finding 1 actually makes. The 2025 exception to New York's ladder is discussed
below.</sub>

The three presidential rows are strikingly similar (28–29% 65+, 14–15% 18–29): the states'
electorates *start* from nearly the same age structure at high salience and diverge only as
salience falls, which is the signature of a turnout-composition (surge-and-decline)
mechanism rather than a registration-age artifact. The Washington and New York papers'
Kitagawa/Das Gupta-style decompositions attribute the 65+ rise mostly to differential
turnout, not to the age structure of the roll; the Idaho paper reports its decomposition
as **directionally consistent only** — its roll churn makes the numeric split unreliable
there, and that paper deliberately prints no decomposition figures.

**How far the skew travels is *not* uniform, and the harmonized numbers are what show it.**
The senior-to-youth ratio starts at almost exactly 2:1 in all three states (WA 2.0, NY 2.0,
ID 1.9) and then diverges sharply: to **4.9–5.5:1** in Washington, **3.0–7.0:1** in New York,
and **7.4–9.7:1** in Idaho's closed primaries. So the gradient runs the same way in all three
cases in *direction* — every state's lowest-salience electorate is older than its
presidential one — while its
*magnitude* ranges from a 1.5× to a 5.1× multiplication of the ratio. (These ratios are computed from
unrounded cohort shares, so they need not equal the quotient of the rounded percentages
printed in the table above — the same convention the Idaho paper states for its R−D margins.)

Two consequences follow, and both are only visible once the metrics are computed identically:

- **Idaho's closed primary is the most age-unrepresentative low-salience electorate measured
  here**, not merely "grayest of all" as an earlier draft of this table put it. Its three
  primaries run 41.4–48.6% over 65 against 5.0–5.6% under 30, and its dissimilarity index
  (25.0–27.8) is above every general measured here. The claim is about the *class*: its
  weakest cell, the 2022 primary at 41.4%, sits just below New York's 2023 general at 41.6%,
  so "exceeds every odd-year general" — which an earlier version asserted — is false on the
  full set and is withdrawn.
- **"Odd-year" is not one salience level.** New York's five odd-year generals span 28.4% to
  41.6% over 65, a range of **13.2 points** — as wide as the gap between New York's
  presidential electorate and Idaho's *weakest* primary (13.2), though well short of the gap
  to its strongest (20.4). An earlier version called this range "wider than separates New
  York's presidential electorate from Idaho's closed primary"; on unrounded values it exceeds
  the narrowest of those separations by **0.05 points** and is smaller than every other
  reading of it. That is not a difference this measurement can resolve: the Idaho age-convention
  bracket alone is an order of magnitude larger (see Methods & reproducibility). The comparison
  is restated rather than withdrawn, because the point it makes does not need it.
  Part of the spread is also **window length**: New York's series covers nine years and
  Washington's five, so New York has more room to vary before any substantive heterogeneity.
  2025 carried a high-salience New York City mayoral contest, which is one explanation for
  its being the youngest recent cell; note that **2021 was also a mayoral year and reads
  36.3%** — and so was **2017, at 28.4%**, since New York City runs on a 2013/2017/2021/2025
  cycle. So all three mayoral cells (28.4, 36.3, 34.4) sit below the two non-mayoral ones
  (32.9, 41.6), and "mayoral years run younger" covers both ends of the ladder that lag is
  otherwise asked to explain. With five contests neither reading is testable and the paper
  asserts neither; naming only one would be the error. Either way this is a
  caution against treating the calendar as a proxy for salience — the very substitution this
  paper's harmonization protocol was written to avoid.

## Finding 2 — The *partisan* structure of the skew is state-specific

Where we can see party (NY, ID), the age skew has sharply different partisan consequences —
and this is the paper's general-vs-particular payoff:

**The comparison has to be made within a class, and doing so changes the reading.** An
earlier version put New York's *odd-year* gap beside Idaho's *presidential* one — different
rungs of the salience ladder this paper exists to build. On matched classes:

| | Republican 65+ − Democratic 65+ |
|---|--:|
| NY, Nov 2016 presidential | **+2.7** pts (22.5 vs 19.8) |
| NY, Nov 2020 presidential | **+4.1** pts (26.8 vs 22.7) |
| NY, Nov 2024 presidential | **+3.7** pts (32.4 vs 28.7) |
| NY, Nov 2017 odd-year (NYC mayoral) | **+1.2** pts (30.0 vs 28.8) |
| NY, Nov 2019 odd-year | **+3.7** pts (35.8 vs 32.1) |
| NY, Nov 2021 odd-year (NYC mayoral) | **+1.0** pts (37.5 vs 36.6) |
| NY, Nov 2023 odd-year (its lowest-salience contest) | **+2.0** pts (43.5 vs 41.6) |
| NY, Nov 2025 odd-year (NYC mayoral) | **+10.7** pts (42.8 vs 32.1) |
| ID, Nov 2024 presidential | **+0.2** pts (31.7 vs 31.5) |

<sub>Extended from three New York rows to eight on 2026-08-17. The conclusion below was
reached on three and is unchanged; it is now carried by every general in the file rather
than by the two odd years that happened to be tabulated.</sub>

- **New York — the partisan asymmetry is real at the presidential level and concentrated in
  2025 off-cycle.** At matched presidential salience New York's Republican electorate is 3.7
  points older on the 65+ share where Idaho's is 0.2 — a genuine cross-state difference. But
  the eye-catching version, a 10.7-point gap with the Republican median voter at 62 against
  the Democratic 54, is **New York's 2025 general only**. Its 2023 general — the contest
  Finding 1 identifies as New York's genuinely lowest-salience — is nearly symmetric at 2.0
  points. On the full eight-general set that contrast is now emphatic rather than suggestive.
  **Excluding 2025, New York's four other odd-year
  gaps run +1.0 to +3.7, against +2.7 to +4.1 in its three presidential years**: the ranges
  overlap and the presidential one sits slightly higher, so low salience does not widen the
  partisan age gap at all. 2025 is more than double the widest gap in any other general in the
  file. So "the Republican wing ages hardest as salience falls" does not hold across New
  York's own odd-years; what 2025 shows is that a *particular contest* mobilised Democrats
  young, not that low salience does this generally.

  *What DOES hold, 8 times out of 8, is the level ordering* — the Republican electorate is the
  older of the two in every general New York's file records, and the no-party bloc is younger
  than both in every one. That is the durable claim, and it is the one the New York paper now
  makes.
- **Idaho — senior representation is near-identical across the parties.** The Republican and
  Democratic electorates carry the same 65+ share (**31.7% vs 31.5%** in the 2024 general;
  medians 54 vs 50). The unaffiliated bloc sits ten points below both on that measure (21.3%),
  which is what pulls its median to 46. *Read that as a senior-end result only: on the under-30
  share, unaffiliated (19.6%) and Democratic (19.4%) voters are level, and this bullet said
  Idaho's "youth lives outside the two major parties" until 2026-08-15, when an external referee
  showed that is false against the Idaho paper's own table.* Note that Idaho's own
  lowest-salience contest is the closed
  Republican primary, which is single-party by construction, so **no partisan-gap measurement
  is possible there at all**; the presidential row is the only matched comparison available.
- **The closed primary is a friction, not an exclusion.** Idaho's *Democratic* primary is
  open to unaffiliated voters, and an unaffiliated elector may enter the Republican primary
  by affiliating at the poll book. In May 2024, 8,453 currently-unaffiliated voters pulled a
  Democratic ballot and 1,554 pulled a Republican one. An earlier version said the closed
  primary "locks that youth out by design"; the accurate statement is the Idaho paper's — an
  unaffiliated voter **must first affiliate** to vote in the contest that chooses the
  winner.
- **Washington — age only, by construction.** No party of record; the WA paper deliberately
  makes no partisan claim, which is why it is the clean high-access baseline for the age
  result rather than a partisan one.

The lesson a single state cannot deliver: "low-salience electorates are old *and* skew
Republican" is not a general fact. It fails in Idaho, where the graying is symmetric — and it
fails within New York too, whose lowest-salience general is nearly as symmetric as Idaho's
presidential one. The partisan asymmetry that does survive is smaller and sits at *high*
salience (+3.7 against +0.2), plus one exceptional mayoral contest. The partisan structure
therefore differs across these institutional settings (open vs closed primary; whether a
party of record exists at all) — but this design does not isolate those rules as the cause.
Three purposively chosen states, each differing on several dimensions at once, cannot
separate a registration rule from everything else that distinguishes New York from Idaho.
What the comparison establishes is that the age skew's partisan consequence is *not* a
constant, which is the claim a single state cannot deliver.

## Finding 3 — Comparable representativeness yardsticks

The WA paper's two reusable cross-state metrics — the **age-dissimilarity index vs CVAP**
(½·Σ|electorate-share − CVAP-share| over age bins) and the **habitual-core overlap** (share
of a low-salience electorate that also cast a 2024 presidential ballot) — are designed to
travel. They are now computed *identically* across WA/NY/ID by
`scripts/diag_cross_state_age_harmonized.py`: shared age bins, age measured at each election
date, and one ACS vintage for every state's benchmark (2020–2024 5-year, table B29001,
pinned to `docs/reference/cvap_age_acs2024.csv` by `scripts/acs_cvap_by_state.py`).

The benchmark those indices are measured against, printed here because it is the
instrument's denominator and appeared nowhere in earlier versions (ACS 2020–2024 5-year,
table B29001, citizen voting-age population):

| CVAP share | 18–29 | 30–44 | 45–64 | 65+ |
|---|--:|--:|--:|--:|
| Washington | 19.8% | 26.7% | 30.9% | 22.6% |
| New York | 20.1% | 24.2% | 32.0% | 23.8% |
| Idaho | 21.3% | 25.5% | 30.2% | 23.0% |

| Metric | WA | NY | ID |
|---|---|---|---|
| Age-dissimilarity vs CVAP (pres → lowest-salience) | 7.5 → 18.6–20.0 | 7.0 → 11.8–22.4 | 8.2 → 25.0–27.8 |
| Habitual-core overlap (low-salience ⊂ 2024 presidential) | 95.5–97.5% | 86.4–95.6% | 94.4–97.8% |

<sub>**Every core cell measured BEFORE November 2024 is an upper bound, and the row is left
uncorrected on purpose.** Each electorate is reconstructed from a roll built after the fact, so
a voter who cast that ballot and has since died or moved is dropped from both sides of the
overlap — and that is exactly the population which could not have voted in 2024. The bias grows
with distance from the reference and is near zero for a contest at or after it. Washington is
the only one of the three states with a retained roll snapshot, so it is the only place the size
can be measured rather than argued: adding back the drop-offs it can still see moves 2021 from
95.5% to **89.9%**, 2023 from 97.5% to **95.0%**, and 2025 — four months from the roll — by
**0.1** points. Those are themselves lower bounds. New York and Idaho have no equivalent
snapshot, so correcting Washington's cell alone would put one column of a comparison row on a
basis the other two are not on, which is the error this table exists to avoid; the cells stay
comparable and the caveat is stated instead. **Read this row as a bound, not as a ranking.**
An earlier version of this note said to read its ordering rather than its levels; that
conflicted with Boundary of inference, which says the cross-state ordering of low-salience
cells is itself not robust to the lag confound, and the note was wrong to carve out an
exception. What can be said is directional and does not need an ordering: New York's low
endpoint is its **2017** contest, seven years before the reference and so the most inflated
number here, while Idaho's is a **2026** primary that postdates the reference and is
essentially unbiased — so correcting every cell would move New York's floor furthest and
Idaho's barely at all.</sub>

**The dissimilarity index puts the three states in the same order the ratio did.** All three
presidential electorates sit close to their citizen voting-age population (7.0–8.2 index
points, i.e. ~7–8% of the distribution would have to move cohorts to match it). At lowest
salience Washington reaches 18.6–20.0 and New York 11.8–22.4, while **Idaho's closed
primaries reach 25.0–27.8 — about a quarter again (27.8 / 22.4 = 1.24) as far from the
eligible population as the worst general election measured here.**

**That comparison is between each state's most extreme cell, and those cells sit at lags of
nought to nine years — the confound Finding 1's own footnote says makes cross-state comparison
of *levels* unsafe.** The claim is therefore restated on **lag-matched** cells: each state's
low-salience contest nearest its roll extract, which puts all three on nearly one
reconstruction basis.

| lag-matched cell | n | dissimilarity | 65+ |
|---|--:|--:|--:|
| **ID** — May 2026 closed Republican primary | 247,391 | **27.8** | 48.6% |
| **WA** — Nov 2025 odd-year general | 1,993,489 | 18.6 | 40.3% |
| **NY** — Nov 2025 odd-year general | 4,039,099 | 11.8 | 34.4% |

<sub>Electorate sizes are printed here and in Finding 2 because no earlier version of this
paper stated a single one, and a cross-state comparison of composition with invisible
denominators asks the reader to take the precision on trust. Idaho's primary electorate is
an order of magnitude smaller than the other two, which is itself part of the finding.</sub>

**On cells matched for lag, Idaho's closed primary is still the least representative
low-salience electorate measured here, by 9.2 index points over Washington.** That is the claim this paper
makes. It is narrower than a comparison of extremes, and unlike that comparison it is not
retracted by the paper's own boundary section. (An earlier version said
"a third again", which the two figures in the same sentence do not support. The ordering is
the same on both metrics; the *gap between states* is narrower on the dissimilarity index
than on the ratio, not wider, so an earlier "widens the gap" is also withdrawn.) The pattern is not that low-salience electorates
are unrepresentative; it is that a *closed nominating* electorate is unrepresentative in a
way that no general election in either other state approaches.

**The habitual-core figures say the same thing from the other direction.** Between 86% and
98% of every low-salience electorate also voted in the 2024 presidential general, so these
are not different populations — they are the presidential electorate's standing core, with
the peripheral voters stripped away. Idaho's 2024 primary is the *most* core-like (97.8%);
New York's 2017 general is the least (86.4%).

**Read this metric with the lag in mind, because it is not the same construct across the
set.** Every cell measures overlap with the *2024* presidential general, so a contest close
to 2024 is being compared with itself over months while one far from it is compared over
years, and attrition scales with that distance. Idaho's series makes the dependence visible:
94.7% (2022) → **97.8% (2024)** → 94.4% (2026), with the maximum at the primary nearest its
own reference election, six months away. New York's runs 86.4 (2017) → 88.3 → 90.5 → 95.6
(2023) in order of recency. An earlier version read Idaho's 97.8% as showing "a selection
result rather than a turnout-noise result"; the figure cannot carry that on its own, because
the same-cycle proximity would raise it regardless. What survives is the weaker and still
useful statement: every low-salience electorate in every state is drawn overwhelmingly from
the presidential one, so none of them is a different population.

<sub>**Why the WA column is not character-identical to the WA paper's own ladder** (7.4 →
18.5–19.9). It differs by 0.05 index points and the cause is entirely the benchmark's
precision: the single-state paper differences against its *published* CVAP row, rounded to
one decimal, while the harmonized version uses the unrounded ACS shares. Computed against the
paper's rounded row this script reproduces 7.4 / 13.2 / 18.5–19.9 exactly, and it asserts
that on every run — so the WA column is a reconciliation of the two conventions, not a
revision of the single-state result.

**And the same is true of the WA habitual-core column, by more than a rounding step** (recorded
2026-08-11). Its floor sits above the Washington paper's, which reads **92.2**% for the same
three off-years, and both are asserted by their own verifiers. The gap is a population
difference, not a disagreement: the WA paper counts every voter carrying a history record for the
contest, while every cut in this study is age-banded and therefore joins the roll and requires a
usable birth year. In 2021 that drops **105,969** voters whose overlap with the 2024 presidential
is much lower, which lifts that year's figure by about three points; the other two off-years
barely move. The harmonized column is the right one for cross-state comparison — it is the same
population in all three states — and the single-state figure is the right one for Washington's own
paper. As with the dissimilarity ladder, neither is a revision of the other.</sub>

## Boundary of inference

- **Current-roll survivorship.** Past electorates are reconstructed from a *current*
  registration file, so voters who since died, moved, or were purged go missing. The WA
  paper benchmarks against certified counts and formally bounds the effect (the age result
  survives the worst case); NY and ID inherit the same caveat.

  **This protects the direction, and only the direction.** Finding 1's second-order claims —
  the magnitude spread, and the cross-state *ordering* of low-salience levels — are not
  robust to it, because the reconstruction bias runs with lag and the states' cells sit at
  different lags (see the ladders under Finding 1: NY 28.4 → 41.6 across 2017–2023, ID 41.4 →
  48.6 across 2022–2026, both near-monotone in recency). Worse, the direction of the bias
  differs by state: Washington's attrition is older-skewing, so correcting it would raise its
  senior share, while Idaho's is larger for the young, unaffiliated and movers, so correcting
  it would lower its senior share. The state supplying the study's extreme is the one whose
  reconstruction most over-retains seniors relative to youth. Nothing here tests that.

  **This is why Finding 3 no longer rests on a comparison of extremes.** An earlier version
  stated the headline on each state's most extreme cell and then retracted the basis for it
  here, which left the paper arguing both sides in different sections. Finding 3 is now made
  on **lag-matched** cells — each state's low-salience contest nearest its roll extract — and
  the ordering survives that restriction with Idaho ahead by 9.2 index points. The comparison
  of extremes stays in the text as context and is explicitly not the claim.
- **Idaho rates are unusable, and shares are not immune.** The roll contraction inflates ID
  turnout rates, so Idaho is composition-shares only and all cross-state comparisons are
  share-based. That does not neutralise the problem: the Idaho paper states the bias is
  *larger* for high-churn groups — the young, the unaffiliated, movers — and a bias larger
  for the young **is** a bias in the age composition. Switching to shares removes the rate
  artifact, not the differential one.
- **Party of record is a 2026 snapshot in both party states, and Idaho's is reactive.** New
  York's enrollment and Idaho's party are read from a current extract, not as of each
  analysed election, so every Finding 2 figure describes *today's* partisans' past behaviour.
  Both companions flag this as their largest limitation. Idaho's case is worse than a
  staleness problem: under Idaho Code § 34-904A an unaffiliated elector who requests a
  Republican primary ballot is thereafter registered Republican, so the snapshot
  mechanically reclassifies the very voters whose absence Finding 2 discusses, and the Idaho
  paper reports its unaffiliated primary shares as **lower bounds** for that reason.
- **Three states, and what the third axis would have added.** The set varies party of
  record (WA no; NY and ID yes) and openness of the lowest-salience measured contest (ID's
  closed primary against three open generals). It does **not** contain a state that lacks a party of record
  yet publishes, durably, which party's primary each voter pulled — the configuration that
  would let Finding 2's partisan question be asked where party is unrecorded. **Texas is that
  case** (no party registration; primary participation is public record), and it is future
  work rather than a gap here. Washington is a near-miss worth naming rather than a
  counterexample: its presidential primary *does* produce a per-voter party declaration, but
  it is publicly disclosable only inside the post-primary window of RCW 29A.84.730, the 2024
  window has closed, and only Pierce County was captured in time — so the asset exists in
  principle and not in hand. Loading Texas would test whether Washington's silence on party is a
  data limit or a real absence of partisan structure, and it would add the one large,
  low-access, Southern case the set otherwise lacks. Until then, Finding 2 is stated as a
  claim about **party-registration states**, which is what the data supports, and Finding 1's
  recurrence claim rests on three states rather than four.
- **Comparability is bounded by the protocol, not eliminated.** The lowest-salience class
  is genuinely different across states; the paper's claim is about the *gradient within
  each state's own salience ladder*, harmonized on the two directly-comparable classes.

## What it means

Across three states spanning the partisan and institutional map, the same structural fact
holds: the lower the salience, the older and smaller the electorate that turns out.

The inference from that to *timing as the lever* is weaker than it reads, and is stated here
at the strength it can carry. The presidential electorates being nearly identical is close to
mechanical — three states with similar CVAP age structures and near-ceiling senior turnout at
high salience will converge at the top of any such ladder — so the convergence confirms a weak
prior rather than identifying a mechanism. More importantly the three low-salience classes are
**not the same treatment**: Washington's is a local general, New York's is a local general that
in three of five years contains a New York City mayoral race, and Idaho's is a closed party
primary. Contest content varies with the state, so divergence across them cannot isolate
timing. What the data support is the weaker and still useful statement that **every one of
these low-salience contests is older than its own state's presidential electorate**, which is a
within-state comparison and immune to the objection.

The partisan consequences are not portable either: they vary with institutional setting, and
this design cannot say which feature of that setting produces the variation. On the policy implication the WA paper draws — moving
low-salience local contests on-cycle — this study shows the *composition* problem it addresses
is present in all three states; it does not show the remedy transfers, and Ornstein (2024)
found the turnout and diversity gains without a detectable downstream effect on representation
or policy. The assumption that off-cycle electorates tilt uniformly toward one party does not
survive at all.

## Methods & reproducibility

**Findings 1 and 3 come from one script, not from three papers.**
`scripts/diag_cross_state_age_harmonized.py` — the age twin of
`scripts/diag_cross_state_giving_turnout.py` — reads `data/{wa,ny,id}_vrdb.duckdb` read-only
and computes every cell in both tables with the same age bins, the same band boundaries, and
age measured at each election's own date. It emits aggregates only and never a row; the three
files are used under RCW 29A.08.720, New York FOIL lawful-use terms, and Idaho Code
§ 34-437A respectively.

Three conventions in that script are load-bearing, and each was measured rather than assumed:

- **All three states are year-of-birth resolution, but not on the same clock — and the
  difference is worth two points of the 65+ share.** WA and NY publish a birth *year*,
  normalised to July 1 — every row, verified — so `date_diff('year', …)` against a November
  election is the calendar-year difference, which implicitly assumes the birthday has already
  happened. Idaho publishes a current integer *age*, which already accounts for whether it
  has, and `age − (2026 − year)` inherits that. The two conventions therefore disagree by a
  year for every Idahoan whose 2026 birthday falls after the extract date, and an integer age
  cannot say who that is.

  So Idaho's figure is a bracket, not a point, and **the bracket is one-sided**: `age` is its
  low end and `age + 1` its high. Measured across Idaho's five classes it is **1.7–2.6 points
  of the 65+ share** — more than it sounds, because one single-year cohort near 65 is about
  1.8% of the Idaho roll — and **1.3–1.4 points of the dissimilarity index**. The figures
  reported throughout this paper are the low end, so Idaho's position is stated
  conservatively: **the May 2024 primary's** dissimilarity is 27.6 on the convention used here
  and 29.0 on the other end. *(That names one cell rather than the class, and the distinction
  matters because the tables above report the primaries' range as 25.0–27.8 — the 2024 cell is
  27.6 and the 2026 cell 27.8, so an undeclared "the closed-primary electorate's dissimilarity"
  reads as the range's top and is a different number. Scope stated 2026-08-11.)* There is nothing to correct to, because the point estimate
  is not recoverable from an integer age — but the correction runs one way, and it runs toward
  the finding rather than against it. `scripts/diag_cross_state_age_harmonized.py` recomputes
  the bracket on every run and refuses to finish if it stops being one-sided.
- **Idaho's lowest-salience class is selected on the ballot the voter actually pulled**
  (`ballot_choice = 'REP'`), not on party of record. That is the field that makes Idaho's
  exclusion a measurement rather than an inference, and no other state in the set has it.
- **The CVAP benchmark is pinned, not fetched.** `scripts/acs_cvap_by_state.py` writes
  `docs/reference/cvap_age_acs2024.csv` (ACS 2020–2024 5-year, table B29001) for all three
  states at one vintage; the harmonizer refuses to run without it. A per-run fetch would let
  one state's benchmark move to a newer release while the others stayed, and the
  dissimilarity index would quietly stop being comparable.

`derive()` **reads the dissimilarity ladder out of
`who-decides-washington.md`** and raises unless its own definition reproduces that ladder
exactly at the paper's printed precision — on the paper's own rounded benchmark, so the test
isolates the definition rather than the benchmark's precision. It runs inside `derive()`
rather than in the script's `main()`, which is what makes "on every run" true: every
automated consumer, including this paper's verifier, calls `derive()`. A missing anchor is a
failure, not a skip, so rewording the sentence out from under the check trips it. Both
failure modes — a changed ladder in the paper and a drifted definition here — are
mutation-tested in `tests/test_infrastructure/test_harmonizer_wa_crosscheck.py`.

<sub>An earlier version of this paragraph described a guard that did not exist as described:
the check sat in `main()`, which no automated path called; it compared against hardcoded
literals and never opened the WA paper, so it could not see the decoupling it was said to
prevent; and it signalled by return code. All three are fixed, and the mutation tests exist
so that "this guard works" is a tested claim rather than a written one.</sub>

## Related work

- **Turnout composition by salience (surge-and-decline).** Campbell, "Surge and Decline"
  (1960); Wolfinger & Rosenstone, *Who Votes?* (1980); Leighley & Nagler, *Who Votes Now?*
  (2013); Plutzer, "Becoming a Habitual Voter" (2002).
- **Off-cycle election timing, composition, and representation.** Anzia, *Timing and
  Turnout* (2014); Hajnal & Trounstine (2005); Hajnal, Kogan & Markarian (2022); Kogan,
  Lavertu & Peskowitz (2018); Einstein, Palmer, Hamilton & Singer, "Age and Homeownership
  Drive the Local Turnout Gap," *Urban Affairs Review* (2025); Lucero, Robles, Trounstine
  & Collins, "What Date Works Best?" (2025).
- **Contested policy effects of timing.** Ornstein, "Election Timing Revisited" (2024) —
  finds the expected turnout and diversity gains from California's on-cycle mandate but
  **no** detectable downstream effect on representation, incumbency or policy. Cited here
  because this paper's "What it means" section reaches a policy implication and the
  companion Washington paper treats this null as the main counterweight to it; dropping it
  from the list while keeping the implication would be selective.
- **The primary as the real election under one-party dominance.** V.O. Key, *Southern
  Politics in State and Nation* (1949); Hirano & Snyder, *Primary Elections in the United
  States* (2019).
- **Primary-electorate representativeness.** Sides, Tausanovitch, Vavreck & Warshaw,
  "On the Representativeness of Primary Electorates" (2020).
- **Independents / the unaffiliated.** Klar & Krupnikov, *Independent Politics* (2016).
- **Voter-file / individual-level method.** Ansolabehere & Hersh, "Validation…" (2012);
  Hersh, *Hacking the Electorate* (2015); Feder & Miller, "The Racial Burden of Voter List
  Maintenance Errors," *Science Advances* (2020).

## Status / next actions

- [x] Harmonization protocol (comparable election classes per state).
- [x] Finding 2 party contrast.
- [x] **Harmonized-metrics script written** (2026-08-06):
      `scripts/diag_cross_state_age_harmonized.py` + `scripts/acs_cvap_by_state.py`. Findings 1
      and 3 now come from one code path; Finding 3's placeholders are filled. Filling them
      changed two things in Finding 1's prose, both recorded there: the senior-to-youth ratio
      does **not** "roughly triple in every state", and Idaho's lowest-salience cell became a
      measured value rather than the phrase "grayest of all". *(This bullet quoted that day's
      figures — a 1.5×–4.9× multiplier and a single Idaho cell of 46.7% / 5.0% — and both were
      superseded within the same round, when the low-salience column was widened to use every
      such contest on file (3 / 5 / 3 rather than 3 / 2 / 1). Finding 1 now carries the current
      values: the multiplier runs **1.5× to 5.1×** and Idaho's cell is a range. Corrected here
      2026-08-11, because a status bullet reads as current fact.)*
- [x] **TX decision made 2026-08-06: publish as a three-state paper.** Texas moves from a
      deferred fourth case to named future work in Boundary of inference. The reasoning is on
      the record in `docs/electoral-health-audit-log.md`: the paper's claim is about the
      gradient within each state's own salience ladder, three states already vary both
      institutional axes it turns on, and a Texas primary-history *proxy* is not the same
      measurement as party of record — it would need its own validation rather than slotting
      into the existing tables. It is a good next paper, not a blocker for this one.
- [x] **Submission metadata + notes written** (2026-08-06):
      `who-returns-ballot-submission-metadata.md` and `-notes.md`, registered in
      `scripts/check_cross_doc_consistency.py` the day they were written.
- [ ] Independent human verification pass (per `electoral-health-audit-log.md`) before external
      review; target venue State Politics & Policy Quarterly. **This is now the only blocker.**
- [ ] Future work, not blocking: load the Texas voter file and add a primary-history party
      proxy, with the validation that a proxy requires. See Boundary of inference.
