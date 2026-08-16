# Electoral Health in Four States
### Evidence on participation, contestation and political voice, from precinct results, campaign finance and the individual voter record — Washington, New York, Texas and Idaho

*Synthesis of the electoral-health series. **DRAFT — pending human/editorial sign-off.**
`scripts/verify_whitepaper.py` scrapes this document and asserts its figures, including
against the companion papers that own them; that gate is automated and is not the sign-off.*

*This document was a **research prospectus** until 2026-08-16 — an outline of analyses to
run, derived from a 2026-06-27 idea-scoring exercise, carrying a scalar "accuracy-weighted
failure signal" of 22/100 and a ten-question scorecard. The analyses have since been run and
written up as eight companion papers, and an external referee's judgement was that the
document could no longer credibly be both a prospectus and a synthesis: every improvement in
a companion created a propagation problem here, and the scorecard's model-authored scores
were doing work as evidence that elicited judgement cannot do. It is now a synthesis. The
gauntlet, the ten questions, the eleven scoring dimensions and the 22/100 are preserved in
**Appendix A** as the programme's methodological history — which is what they are — and no
longer appear in the argument.*

---

## What this paper claims, and what it does not

This is a synthesis of eight companion papers. It does not re-derive their results: where a
figure belongs to a companion it is **scraped from that companion**, so that improving the
companion moves this document or fails its gate loudly. That mechanism exists because the
opposite happened — until 2026-08-15 this document carried a pooled donor panel, a retired
match key and a headline slope that its companions had all superseded.

**The claim.** The four-state evidence documents persistent inequalities in who participates,
who finances campaigns, and how often general elections are genuinely close. It does **not**
support a scalar diagnosis of democratic failure, and it does **not** identify the causal
electoral effect of campaign spending.

---

## Scope and integrity statement (read first)

This program studies the **electoral** dimension of democracy — participation,
representation, political equality, and contestation. It is **silent** on rule of
law, civil liberties, press freedom, and executive constraint, and it makes no
claim about them.

Three commitments govern every section below:

1. **Pre-specified working null.** The working hypothesis is that *"Washington's (and the
   comparison states') electoral democracy is functioning."* A finding moves against that
   null only when the evidence earns it. *This was called a "pre-registered null" until
   2026-08-16. It is not one: there was no frozen, time-stamped registration of hypotheses,
   estimands, analysis rules and decision criteria before the analyses ran. A general prior
   position is a working null, and calling it pre-registration claims a discipline this
   programme did not exercise.*
2. **Accuracy gate.** Each finding contributes to any larger conclusion *only in
   proportion to its data sufficiency × inferential strength.* A striking number
   built on data the warehouse cannot actually carry is reported as a limit, not a
   result.
3. **A bounded conclusion, not a scalar verdict.** This document assembles the
   *components* of a democratic-health assessment. Its conclusion is that **the analyses
   document several measurable disparities and constraints in electoral participation,
   contestation and political voice, and do not establish system-level democratic
   failure.** What it does not do is reduce that to a number.

   *This commitment read "**No verdict** … deliberately does not declare a failure of
   democracy" until 2026-08-15, while the closing section was titled "The verdict-in-waiting"
   and opened "electoral stress, not failure", and the paragraph below assigned a 22/100
   failure signal. An external referee named the contradiction. Claiming to reach no verdict
   while publishing a scalar failure score is the version that could not be defended; the
   bounded interpretive conclusion above is stated plainly instead.*

---

## Data, and what each state can actually support

**Data provenance.** Every count below is a **live read that drifts** as the 2026 cycle
accrues, and each is scoped to the state or states named — the previous version of this
paragraph was not, and an external referee read its contribution figures as program-wide
when they were Washington's alone.

- **Washington:** ~5.1M precinct-result rows across 22 elections; **8.6M individual
  contributions, $1.04B** (FEC `$646.2M` + state PDC `$394.6M`, 2018–2026) with
  employer/occupation/ZIP; ~16.1M voter-score rows (one per voter per district scope,
  ~5.5M distinct voters); ~27.1M individual VRDB vote records.
- **All four states, federal layer only:** **28.9M contribution rows / $4.73B** of
  resident-donor outflow (WA 5.58M/$646.2M · NY 9.98M/$2,066.6M · TX 12.56M/$1,942.1M ·
  ID 0.77M/$76.2M). Adding each state's own finance system takes it to **36.1M rows /
  $6.06B**.
- **The rare asset:** voters matched to their own donations at the person level. Quote
  these **per panel**, never pooled — WA federal 147,745 / state 217,114; NY federal
  269,218 / state 378,383; ID federal 23,303 / state 23,613. The pooled 314,974 WA figure
  this document used to headline is a **retired estimand**; see the panel note in Finding 5.


**Legal basis for each voter file, since a synthesis is where a reader looks for it.**
Washington under **RCW 29A.08.720**; New York under **NYSVOTER**, obtained by FOIL and used
under the elections-purpose certification of **N.Y. Elec. Law § 3-103(5)**; Idaho under
**Idaho Code § 34-437A**. None is redistributed. Texas publishes no voter file, which is why
it appears in the money and contestation rows below and nowhere else.

**The four states are not four symmetric assessments, and the design should say so first
rather than let a reader discover it.** Texas participates fully in the money and
contestation evidence and has no voter file, so no person-level donor analysis exists for it.
New York and Idaho publish individual party of record; Washington does not. Idaho's roll is a
current extract with a survivorship problem unlike Washington's.

| domain | Washington | New York | Texas | Idaho |
|---|:--|:--|:--|:--|
| Participation — age composition of the electorate | **measured** (27.1M vote records, birthdate) | **measured** (13.5M roll, year of birth) | **unavailable** (no voter file) | **measured**, with a roll-survivorship caveat |
| Participation — *party-resolved* | **unavailable** (no party of record) | **measured** | **unavailable** | **measured** |
| Contestation — observed margins and ballot choice | **measured** | **measured** | **measured** | **measured** |
| Political voice — aggregate money | **measured** (federal + state) | **measured** (federal + state) | **measured** (federal + state) | **measured** (federal + state) |
| Political voice — *person-level* voter↔donor linkage | **measured** | **measured** | **unavailable** (no voter file) | **measured** |
| Campaign effects — directional IE against margin | **measured** (34 federal + 129 state cells) | **unavailable** | **unavailable** | **unavailable** |

*Read every cross-state statement against this table. "Four states" is true of the money and
contestation evidence; the person-level evidence is three states, and the campaign-effects
evidence is one.*

---

## Method

Each research question was scored 0–10 on eleven dimensions by a **language model**
(`idea-gauntlet/democracy_insight.workflow.js`) prompted to act as a quantitative
methodologist and democratic-theory reviewer, to search the web, and to be adversarial toward
its own conclusions:

- **Insight layer (research quality):** data sufficiency, inferential strength,
  novelty (vs. the existing political-science literature), systemic significance,
  usefulness, robustness.
- **Diagnostic layer (anatomy of a failure claim):** function impairment (severity
  vs. the democratic ideal), trajectory (is it worsening?), entrenchment (does it
  resist self-correction?), counter-thesis strength (how good is the "this is
  actually healthy" reading — *reverse-scored*), convergence (does it triangulate
  with the other findings?).

Function impairment is **conceptually mapped** to the V-Dem component indices (electoral,
liberal, participatory, deliberative, egalitarian) so severity is legible in a familiar
vocabulary.

*This paragraph said "anchored to" until 2026-08-15. An external referee objected that
"anchored" claims a calibration that does not exist, and he is right: these are not V-Dem
component-index observations, no reproducible transformation maps V-Dem indicators onto
these 0–10 scores, and the scores were produced by a language-model workflow. The mapping
is a labelling convention borrowed from V-Dem's conceptual scheme, and nothing about the
scores inherits V-Dem's authority.*

### The four evidence domains, and which of them share data

The evidence below is grouped into four domains rather than the ten scored questions of the
original gauntlet (Appendix A). The regrouping is not cosmetic. **The ten questions were not
ten independent studies**, and counting them as though they were inflated an implicit
evidence count — "convergence" was itself one of the scored dimensions.

| domain | what it measures | companion papers | shares data with |
|---|---|---|---|
| **1. Participation** | who actually votes, by age and party | who-decides-{washington,new-york,idaho}, who-returns-ballot | shares the voter files with Domain 3's linkage |
| **2. Contestation** | whether general elections are close, and whether they offer a major-party choice | safe-seat-washington | shares election outcomes with Domain 4 |
| **3. Political voice** | who funds campaigns, person by person | donor-class-and-the-electorate, cross-state-fec-money | 3a/3b/3c all draw on the same contribution systems; 3b/3c share one voter↔donor linkage |
| **4. Campaign effects** | whether money moves margin | does-money-move-votes | shares election outcomes and the forecast residual with Domain 2 |

So Domains 1 and 3 are not independent of each other, and 2 and 4 are not independent of each
other; within Domain 3, the three results are three transformations of one data-generating
process. Triangulating several estimands from the same data is legitimate and is what this
programme does. Treating the count of results as a count of corroborating studies is not.

---

## The evidence, in four domains

### Domain 1 — Participation: who actually votes

- **Defensible claim.** The electorate that decides odd-year general elections in
  WA is roughly half the size of the presidential electorate and dramatically
  older. From **27.1M** VRDB vote records (~100% birthdate coverage): voters 65 and older were
  **36.7%, 40.2% and 40.3%** of the 2021, 2023 and 2025 odd-year electorates against
  **28.5%** in 2024, while voters 18–29 fell from **14.2%** in 2024 to about **7.6%**
  off-cycle. Individually, 18–29 participation falls from **58.4%** (2024) to about **16%**
  off-year, while 65+ slips only from **88.3%** to **~61%**.

  <sub>*Re-quoted at the owning paper's own precision on 2026-08-16.* This bullet gave the
  off-year senior share as a rounded band ("~37–40%"), and gave two within-cohort rates —
  **15.8%** and **61.3%** — to a decimal place that
  [`who-decides-washington.md`](who-decides-washington.md) does not publish, because that
  paper reports them as "about 16%" and "~61%". A synthesis stating a companion's figure more
  precisely than the companion does is drift waiting to happen, and there is no basis on
  which the extra digit is more correct. All of these are now scraped from the companion.</sub>
- **Strongest objection.** This is *voluntary* differential participation, not
  disenfranchisement. WA has all-mail, postage-paid, automatic/same-day
  registration — the gray electorate reflects who *chose* to vote, and the gap is
  mechanically expected from low salience. The fix is purely institutional (move
  local races on-cycle to even Novembers), which is itself evidence the system is
  responsive, not failing.
- **First analysis — DONE** ([`who-decides-washington.md`](who-decides-washington.md)):
  Join `voting_history` to `voters.birthdate`; classify
  age-as-of-each-election into cohorts; produce a cycle-type × cohort table of both
  (a) within-cohort turnout and (b) cohort *share* of the actual electorate, for
  every general 2021–2025. Report composition shares (denominator-free) alongside
  rates to neutralize the registration-churn objection. **Stop short of any
  partisan-consequence claim** — that needs statewide party-of-record (see §2 of
  the follow-on).
- **Key literature.** Hajnal & Trounstine (off-cycle timing skews the electorate
  older/whiter); Anzia (*Timing and Turnout*); Lucero et al. 2025, surveying cities that
  switched, which puts voters **over 45** at **58.4%** of the off-cycle electorate against
  **49.7%** of the presidential-year one (an earlier version of this line gave the cohort,
  the magnitude and the design wrong, and its "28%" appears to have been Washington's own
  presidential 65+ share); and **Ornstein (2024)** on California's SB 415 across 236 local
  governments, which finds the expected turnout and diversity gains but **no** detectable
  effect on representation, candidacy, incumbency, housing policy or public-employee
  salaries — the disconfirming half of the same literature.

### Domain 2 — Contestation: whether general elections are close

- **Defensible claim, on OBSERVED margins.** The large majority of seats are not close.
  On the most recent general for partisan legislative and congressional offices, the
  not-close share runs **WA 87.8% · NY 88.0% · TX 94.0% · ID 92.9%** of lower-chamber
  seats. This is a structural counting result on certified returns that does **not**
  depend on any blocked/weak signal or on any model.

  <sub>**Two changes here on 2026-08-15, both at an external referee's insistence, and both
  make the finding harder to attack.** *First, the live forecast table is gone.* This bullet
  led with model-projected 2026 margins from the latest `forecast_predictions` snapshot per
  state — figures that were unpinned, unprobed, drifting, due to move wholesale at the
  pre-November re-lock, and disagreeing with the observed count by thirteen points in Texas.
  They are not reproduced here, because enumerating four unpinned live reads is the thing
  the note objects to. The observed result is both stronger and stable. *Second, "trajectory: worsening" is withdrawn.* Washington's
  observed not-close share runs **78.9–88.1%** across 2016–2024 with a dip in the 2018 wave;
  that is persistence, not a monotonic trend, and five cycles cannot carry one.
  *And the sentence "when the general is foregone, the operative decision moves to
  lower-turnout primaries" is removed as an inference the safe-seat companion has expressly
  withdrawn* — an ex-post margin cannot date the binding decision.</sub>
  *(A basis note here described how the four retired band cells were computed from `forecast_predictions` — including that the Texas district count differed between two snapshots four days apart, which is why they were never trustworthy as published figures. It went with the cells.)*
- **Strongest objection.** Those are *model-projected* 2026 margins, sensitive to
  the 10-pt threshold; and "non-competitive" conflates a closed-shop seat with one
  that is lopsided because voters *genuinely* lean that way (self-sorting). A
  Solid-D Seattle seat and a Solid-R rural-ID seat each *represent* their
  electorates — the null's "outcomes reflect voter choice."
- **First analysis — DONE** ([`safe-seat-washington.md`](safe-seat-washington.md)):
  Ran **observed** margins, not the projection: per state, the
  most recent general for partisan legislative + congressional offices → margin per
  district → band counts. **The companion has since split this into two dimensions that
  must not be merged:** *candidate competition* (was the race close, on the top-two margin
  regardless of party) and *partisan availability* (did the ballot offer both a Democrat
  and a Republican). They overlap but are different questions — in WA 2024, 83.5% of seats
  were not close and 34.6% offered no D-v-R option, and of the sixteen same-party generals
  fifteen were also lopsided but **one was decided by six points**. Treating "no major-party
  choice" as automatically non-competitive, as this bullet originally did, is the conflation
  the rewrite removed. For WA, built the 2016–2024 seat-level trend (not-close share runs
  **78.9–88.1%** across the five cycles, dipping in the 2018 wave) and the
  primary-to-general turnout ratio in safe seats (~0.5) — the one
  place this data *adds* to Cook/Ballotpedia/Unite America by attaching real
  turnout (and the voter-donor join) to the "primary decides" claim.
- **Key literature.** Cook PVI (swing districts 164 in 1997 → ~72 post-2016);
  Ballotpedia Competitiveness Index (38% of state-leg seats uncontested in 2024);
  Unite America (*The Primary Problem*).

### Domain 3 — Political voice: who funds campaigns

The three results below share their contribution systems, and the second and third share a
single voter↔donor linkage. They are one body of evidence seen three ways.

#### 3a. Small transactions coexist with high dollar concentration

*Titled "Whale-dominated money behind a small-dollar facade" until 2026-08-16. A low median
gift and a high Gini coexist naturally in any heavy-tailed distribution; neither is a facade
concealing the other, and "facade" asserted a concealment the measurement does not show.
This is also, and only, an **itemized-contribution** finding: a small transaction in an FEC
itemized file is not an observation of the universe of small donors, whom the disclosure
floors keep out of the record entirely.*

- **Defensible claim.** WA money is broad by headcount but concentrated by dollar. The
  **median itemized gift is $25** in both money systems, while per-recipient-cycle
  concentration is substantial: median Gini **0.578** federal and **0.579** state, over
  recipient-cycles with ≥100 distinct donors (**834** federal, **1,997** state). The data can
  quantify, per race and cycle, the sub-$200 retail share against the whale layer.

  <sub>**Corrected 2026-08-10.** These figures were previously given as "n=2,821 … single
  gifts reach $2.5M … Gini ~0.61", which was computed on the **pooled** FEC+PDC table — the
  exact pooling Finding 5's panel note says the series corrected everywhere else. Pooled, the
  count is 2,831 today; separated it is 834 federal and 1,997 state. The **$2.5M maximum is a
  PDC state gift**; the federal maximum is $929,600, so the old sentence paired a median from
  one money system with a maximum from another. The 0.61 does not reproduce on any basis I
  can construct — both layers give 0.578 — and it is withdrawn rather than restated.
  **Basis, and a live-read warning (2026-08-10).** Population: recipient-cycles keyed
  `(fec_candidate_id, election_cycle)` over `individual_contributions`, positive amounts,
  split by money system on the `PDC:` id prefix, restricted to ≥100 distinct (name, zip5)
  donors. *Pooled is a separate grouping, not the sum of the two* — a recipient-cycle below
  the threshold in each system alone can clear it pooled — which is why 834 + 1,997 ≠ 2,831.
  **These three counts are unpinned live reads and they drift upward** as the 2026 PDC cycle
  accrues: they read 822 / 1,989 / 2,814 when this correction was first written, hours
  earlier the same day. All eight figures in this finding are now asserted by
  `scripts/verify_whitepaper.py`, which had asserted none of them — including the 0.578 that
  the series' withdrawn-claim register already recorded as guarded by it.</sub>
- **Strongest objection.** The recipient key is `fec_candidate_id`, which holds **two
  identifier systems**: FEC committee ids and `PDC:`-prefixed state filer ids. On the federal
  side the highest-volume "recipients" are conduits (ActBlue, JFCs), so a naive per-recipient
  Gini measures a *conduit's pass-through book*, not a candidate's race; on the state side —
  which is 71% of the pooled recipient-cycles — that objection does not apply, and a different
  one does. A true
  per-race figure needs an earmark-attribution layer that does not yet exist and
  must be validated against double-counting. And a Gini that mixes $25 and $2.5M is
  mechanically high regardless of democratic health.
- **First analysis.** Build the conduit-attribution layer *first* (partition
  direct-to-candidate vs. conduit-routed; verify whether ActBlue/WinRed rows carry
  attributable earmark memos). Then compute, per ultimate-recipient × cycle: Gini,
  top-1%/top-10% dollar share, and sub-$200 vs. ≥$200 split — reported **with and
  without** conduit pass-throughs, since that toggle determines the answer.
- **Key literature.** Bonica & Rosenthal (wealth-elasticity of giving); Bouton &
  Cagé (*Small Campaign Donors*); Brennan Center (small-dollar grew, megadonors grew
  faster — "thin layer over a concentrated core").

#### 3b. Donors are also high-frequency voters

- **Defensible claim (cross-sectional only).** Donors are a participation elite. On the
  measure the owning paper now treats as clean — registrants who existed before the first
  election in the window, so every retained person could have voted in all of them, then
  age-standardized — the donor/non-donor turnout gap runs **+22.9 to +26.3 points** across
  the four panels (NY federal +25.1, NY state +26.3, WA federal +26.0, WA state +22.9).
  Financial voice and electoral voice concentrate on the same individuals rather than
  offsetting.

  <sub>**Retired 2026-08-15: "87.6% are super-voters vs 50.9%" of non-donors, at an average
  turnout propensity **0.967 vs 0.749** and a ratio of **1.72×**.** Those figures came from
  the **pooled** 314,974-voter match, an estimand the
  donor paper has since replaced with per-source panels. Worse, the measure itself is
  defective for this comparison: `voter_scores.is_super_voter` is defined as *last voted on
  or after 1 Jan 2022 **and** registered at least eight years*, so registration tenure sits
  inside the outcome definition — every registrant of under eight years' standing is false by
  construction, the variable cannot carry a tenure adjustment, and it is not
  measure-comparable with New York's plain count of generals voted. The owning paper says all
  of this and publishes the eligible-for-all figures above instead. An external referee
  caught the synthesis still headlining the dramatic superseded metric, which is precisely
  what a synthesis must not do.</sub>
- **Strongest objection.** The *causal/longitudinal* version ("giving *makes* people
  vote more; inequality *deepens*") is unsupportable here: donors are pre-selected
  for engagement (reverse causation is equally plausible), the match is biased
  toward older/stable-address/super-voting/uncommon-named people (inflating the
  gap), and `voter_donor_affiliation` collapses each voter to one row, so
  first-gift-then-vote sequencing can't be reconstructed on a shallow 2021–2026
  history. The benign reading — donating as a *gateway* that broadens participation
  — is live.
- **First analysis — DONE**, and superseded by
  [`donor-class-and-the-electorate.md`](donor-class-and-the-electorate.md), which is the
  citable owner of this result. Framed strictly as association: the giving↔voting overlap is
  real, the *causal/longitudinal* version remains out of reach, and the eligible-for-all
  age-standardized gaps above are the figures to quote.
- **Key literature.** Verba/Schlozman/Brady (*Voice and Equality*; *Unheavenly
  Chorus*) — money is the most income-skewed form of participation; the donor pool
  is a structural elite (the *constant* against which any worsening must be measured).

#### 3c. The donor class is not the electorate

> **⚠ Panel note (2026-07-26).** The WA figures in this finding were computed on a
> **pooled** voter↔donor match, before it was discovered that WA's
> `individual_contributions` holds federal (`FEC:`, $646.2M) *and* state (`PDC:`,
> $394.6M) money and the matcher had no source filter. Pooling stacks one person's
> federal and state giving into a single donor total and inflates concentration.
> [`donor-class-and-the-electorate.md`](donor-class-and-the-electorate.md) now reports
> two panels — **federal** 147,745 donors / top-1% **41.2%** / Gini **0.815**, **state**
> 217,114 / **43.5%** / **0.821** — which supersede the pooled numbers below. Every
> finding survives, and the age skew *strengthens* on the federal panel (Silent
> **2.67×**, Gen Z **0.04×**).

- **Defensible claim.** At the person level, donors are a narrow slice that does not
  mirror the electorate: **~4.0–5.7% of voters** — matched donors as a share of all
  registrants on the pooled panels, ID **4.0%**, NY **4.1%**, WA **5.7%** — skewed old
  (pooled WA: Silent **1.96×**,
  Boomer **1.71×** over-represented; Gen Z **0.09×**, Millennial **0.54×**
  under-represented — 2.67× / 2.04× / 0.04× / 0.35× on the federal panel),
  overwhelmingly super-voters, geographically concentrated (**61.4% of WA donor
  dollars from two Seattle-metro ZIP3s**; 63.5% federal-only), and internally top-heavy
  (top 1% of matched donors supply **46.6%** of matched dollars pooled, **41.2%**
  federal; top 10% **79.3%** / **74.2%**).
  RETIRED ($154.0M, 23.8%) and NOT EMPLOYED ($128.8M, 19.9%) are the two largest
  occupation blocs. *(These are contribution-level, not matched-donor, figures — occupation
  is on the gift, not the voter — and they are stated on the series' documented outflow
  basis: FEC rows, Washington-resident donors, $646.2M. Until 2026-07-27 they read $221.7M
  / 21.3% and $147.4M / 14.1%, computed on the **unfiltered pooled** table — FEC plus state
  PDC plus non-resident donors, $1,050.8M — i.e. the same two-money-system pooling this
  series corrected everywhere else, sitting inside a finding whose every other number is
  panel-scoped. On the federal basis both blocs are a LARGER share, so the point sharpens.)*
  The voter↔donor join makes this *person-level*, not ecological —
  the genuine value-add over the standard FEC-aggregate literature.
- **Strongest objection — one mechanism tested and excluded, the objection not closed.**
  The objection is that the skew is a **matcher artifact**: the unique-key over-selects the
  older, rarer-named, stable-address residents it then "finds" over-represented. What has
  been tested is the **roll-side** half of that. On the current full-name key the probability
  a voter is uniquely matchable is nearly flat across age — **NY 94.5–95.4%** (0.9-pt
  spread), **WA 96.3–97.6%** (1.4-pt spread) — so inverse-propensity re-weighting does not
  move the distribution: NY's 65+ donor share goes 47.9% → **47.9%**, and every Washington
  generation multiplier is unchanged to two decimal places in both panels.

  The defensible conclusion is therefore **"measured roll-side strict-key matchability does
  not explain the age skew"** — not "matcher bias has been rejected". The test says nothing
  about donor-side selection: how a contributor writes their own name on a filing,
  residential mobility between the filing and the extract, work or second addresses,
  stale addresses, or namesakes. The owning paper enumerates those and leaves them open.
  The voter file still has **no income and no race**, so the literature's richer/whiter
  claims remain proxied, not tested.

  <sub>**Corrected 2026-08-15.** This bullet said the objection was "tested and rejected" and
  that the skew "is a real property of *who gives*, not of who the matcher can find" — a
  categorical claim the owning paper explicitly declines to make. It also quoted
  **69.1%–73.3%** matchability, which is the *retired* (last name, first initial, ZIP) key;
  the current full-name key runs 94.5–97.6%. An external referee caught both.</sub>
- **First analysis — DONE** ([`cross-state-fec-money.md`](cross-state-fec-money.md) §F2):
  the matcher-bias inverse-propensity re-weighting above; skews reported raw *and*
  re-weighted; income/race labeled untestable. *(Retired estimand, kept only as the thing
  the per-panel figures replaced: on the pooled 314,974 match, top-1% **46.6%**, top-10%
  **79.3%**, Gini 0.857, and **61.4%** of dollars from two Seattle ZIP3s.)*
  Per panel — federal panel top-1% **41.2%** [38.6–43.4],
  Gini **0.815** [0.806–0.822], two-ZIP3 share **63.5%**; state panel top-1% **43.5%**
  [38.7–48.9], Gini **0.821** [0.806–0.838]. *(This line previously read 42.4% [40.2–44.9]
  for the federal panel — the all-tier value, contradicting the 41.2% in the panel note
  directly above it. The bootstrap CIs are the per-panel re-runs in
  [`cross-state-fec-money.md`](cross-state-fec-money.md) §F4; the panels are full
  populations, so read the intervals as resampling sensitivity to donor composition,
  not sampling error.)*
- **Party-resolved — DONE for NY + ID** ([`donor-class-and-the-electorate.md`](donor-class-and-the-electorate.md)):
  with party of record the demographic claim sharpens into a partisan one, and the striking
  result is that it holds **in both directions of the spectrum** — the donor class
  over-represents registered Democrats relative to the electorate in **deep-blue NY (+16.1
  pts federal, +9.6 state)** *and* **deep-red Idaho (+8.6 federal, +9.8 state)**,
  under-represents the unaffiliated in both, and
  the age skew replicates (65+: NY federal **49.9%**, ID federal **66.8%**, ID state
  **51.3%**). **Crossover, on the federal panels only:** currently enrolled Democrats are
  near-monolithic donors (**95%** NY federal), and unaffiliated donors' resolved giving
  leans Democratic — and both survive assigning the *entire* unresolved pool to the rival
  side (NY unaffiliated **52.1%** against 45.1%; ID unaffiliated **65.0%** against
  34.1%, as shares of matched donors). So the Democratic tilt is a property of who donates,
  not of a state's majority party.

  <sub>**Panel corrected 2026-08-15.** This sentence quoted the **state** panels — ID 94.6%
  and "nearly 4:1" — where recipient party is reconstructed rather than published and
  resolution is only 51.1% for Idaho and 37.7% for New York (39.0% for Idaho's unaffiliated row). The owning paper's
  bound analysis says in terms that the two patterns **do not survive** the extreme
  unresolved-pool assignment on the state panels, and **do** survive it on the federal panels,
  where resolution is 87.6–88.8%. The synthesis was resting a headline on the panel that
  fails the test while the panel that passes it sat unused. State-panel crossover is
  suggestive and is reported as such in the companion.</sub> **These are the primary (full-name-key) specification.**
  It discards 11–19% of matched donors who are younger and less Democratic than those
  retained, so part of the sharpened skew is selection rather than precision — the
  all-tier figures, which are the more conservative ones, are reported alongside in the
  donor-class paper.
- **Key literature.** Demos (*Whose Voice, Whose Choice*); Bonica (DIME); and the
  same-state result that tempers the benign reading — **Yorgason (*APSR* 2024/25),
  "Campaign Finance Vouchers Do Not Expand the Diversity of Donors: Evidence from Seattle":
  the voucher recipients were the same wealthier, whiter, older, more civically engaged
  people who dominated before the reform.** (An earlier version attributed this to Grumbach,
  Sahn & Staszak, who wrote a different paper on a different question.)

### Domain 4 — Campaign effects: money and margin

- **Defensible claim.** Fundraising is the single strongest correlate of
  overperformance in the panel — raw log2(D/R) receipts correlate **+0.60** — while
  spend *allocation* carries a cross-cycle holdout R² of **0.028**, and the forecast
  model zeroes the fundraising term post-redistricting because the baseline already
  absorbs it. **What none of that establishes is direction.** The association is
  equally consistent with money buying votes and with money chasing candidates who
  were already going to win, and no design available here separates them. The
  citable result is a **non-identification**: the public record can measure the
  association precisely and cannot sign the causal effect.

  <sub>**This finding was titled "Money marks strength; it does not appear to move margin"
  until 2026-08-15, and an external referee was right that the title contradicted the bullet
  beneath it** — which already conceded that the correlation "is exactly what a true causal
  effect *would also* produce". A heading cannot assert non-effect while the text concedes
  non-identification. Two figures were stale at the same time: the correlation read **+0.58**
  and the holdout R² **0.02**, against the owning paper's current **+0.60** and **0.028** —
  and the retired R² also rounded to a different first decimal than the current one, so the
  old cell carried a stale rounding on top of a stale figure. Both are scraped from
  [`does-money-move-votes.md`](does-money-move-votes.md) rather than restated; the scrapes
  had silently broken when that paper's tables were rebuilt, which is how the figures
  drifted unnoticed.</sub>
- **Strongest objection — and it is sustained.** The whole thing is a correlation with no
  exogenous variation. The allocation-R² null is underpowered and tests spend *mix*, not
  *level*. So the data can neither confirm nor refute vote-buying; it can only show money
  is endogenous to candidate quality.
- **First analysis — DONE** (`scripts/diag_ie_vs_margin.py`). For FEC-attributed
  races (Schedule E carries support/oppose + district), it regresses the
  *fundamentals-net residual* (actual − model-predicted Dem %, **not** the raw
  margin) on the net pro-Dem IE advantage. **Directional IE on disk spans five cycles
  (2018–2026 FEC Schedule-E, 34 scorable WA U.S. House races)**, and the **$51.7M of
  direction-coded PDC state-legislative IE** (form C-6 section C6.3, ingested 2026-08-09)
  adds **129 scorable district-cycles** on the same design — see
  `scripts/diag_pdc_ie_vs_margin.py`. That extension does not settle the question: every
  interval still spans zero and the **sign becomes specification-dependent** (−3.836 to
  +4.871 across four specifications), which is evidence the constraint is structural
  rather than a shortage of cells. The regression **now runs**: the slope is **+0.515 pp per
  $1M net pro-Dem IE (Pearson r +0.186, n=34)**, with a bootstrap interval of
  −0.600 to +2.821 that spans zero.

  **That positive sign rests on one observation, and the owning paper says so.** Its
  leave-one-out sweep over the same 34 races runs from **−0.035** (dropping WA-08 2018) to
  **+0.832** (dropping WA-03 2024): deleting a single race erases the positive slope
  entirely. WA-08 2018 pairs the panel's largest net pro-Democratic IE (**+$8.26M**) with a
  **+8.78**-point residual and carries a Cook's distance of **0.69**; dropping every WA-08
  observation gives **−0.065**. A district-clustered bootstrap, which respects the fact that
  the panel measures ten districts repeatedly, widens the interval to **−1.595 to +1.268**.

  <sub>**What this bullet claimed until 2026-08-15, and why it is withdrawn.** It said "the
  public record can *bound* the persuasion effect but not sign it". A bootstrap interval
  around an observational coefficient under endogenous treatment bounds the *association*,
  not the persuasion effect; calling it the latter smuggles back the identification the same
  sentence denies. It also headlined +0.515 without the leverage result — which the owning
  paper had already derived, published and led its own abstract with. That is the
  propagation failure this document was carrying in miniature: the companion did the
  careful work and the synthesis kept the dramatic version.</sub> The most heavily funded
  race in the panel, **WA-03 2024 ($18.61M total IE, +$6.09M net pro-Dem), finished
  +0.06 pp off its fundamentals: dead-on.**
  **Two corrections against the earlier version of this bullet, both material.** It
  reported a single cycle and 7 races; three further cycles were simply not loaded,
  and the backfill took about five minutes. And it reported a *negative* slope
  (−0.39, r −0.39, n=7) read as the endogeneity signature; the sign reversed on the
  fuller panel, which is what a coin-flip estimate does. It also called WA-03 the
  most IE-saturated House race in the country at $40.1M — an artifact of a
  notice/periodic double-count that inflated every IE total roughly twofold. At the
  true $18.61M it ranks 22nd of 387.
- **Key literature.** Jacobson (spending endogeneity); Kalla & Broockman (≈zero
  average general-election persuasion across 49 experiments); Bonica (money as
  information, not purchase).

---

## What the evidence does not support

These questions are *significant* but the warehouse cannot currently carry them.
They are reported as limits — and they map the data we would need to say more.

- **Elections financed by non-constituents (insight 31) — NO LONGER BLOCKED; the
  test ran.** This was reported as un-runnable because only donor-residence *outflow*
  was loaded and NY/TX contributions were absent. Both are now fixed: NY+TX+ID FEC
  contributions were loaded, and a **recipient-anchored inflow** dataset (5.50M gifts /
  $1.21B, all-state donors → WA/NY/TX/ID federal candidates) was built, so the
  nationalization test *did* run ([`cross-state-fec-money.md`](cross-state-fec-money.md)
  §E–I). The result is **not** null-supporting at the inflow level: **27% (WA) / 41%
  (NY) / 34% (TX) / 53% (ID)** of these states' U.S.-House+Senate candidate money is
  out-of-region, and on the **outflow** side three of the four send half or more of
  their candidate money out of region (ID 68% — the most — NY 62%, WA 50.8%), while **Texas
  sends 43%** — Georgia Senate
  races alone drew ~$68M from residents of the four states. The earlier "93.6% in-state"
  was indeed the ingestion artifact this item warned about. (State-level money — WA PDC,
  NY BOE, ID Sunshine, TX TEC — is now also loaded, though not yet folded into these
  federal cross-state cuts.)
- **Straight-ticket lock-in / candidate accountability (insight 28, data-sufficiency 3).**
  Individual ticket-splitting is **unmeasurable** (cross-party matchback fires for
  ~0 voters), and the precinct ticket-split tables can't yield a 22-election trend
  (epoch-versioned precincts; 2022 renumbering → 0 common precincts). The only
  defensible cut is an *ecological* county-level cross-office consistency trend.
- **Is there a persuadable middle? (insight 28, the one "supports-null" finding).**
  `voter_party_choice` is Pierce-only and holds **one** party-primary cycle
  (2024), so no voter can appear in two — that is a property of the load, not a measured
  null, and an earlier version reported it as "exactly 0 voters" as though it were evidence. WA has no party registration. The honest result is a
  limits-and-null finding that *converges with* the gold-standard literature
  (Abramowitz & Webster; Kuriwaki's cast-vote-record work), not against it.
- **Are outcomes pre-determined? (insight 38).** The backtest (MAE 6.41, 94% directional on
  163 filtered cells; **10.12 / 85% on the unfiltered 170-cell grid**) bounds how much
  aggregate campaigning moves results. It is a **retrospective fit**, not a notarized
  out-of-sample result — what is notarized is the locked 2026 forward prediction set, which
  scores in November — and the model's coefficients were tuned against a residual matrix, so
  the figure is not pre-registered. Further —
  predictability is **not** causal inertness (Gelman & King: predictability is the
  *footprint* of effective deliberation), the headline is safe-seat-inflated, and
  the data has no counterfactual.

**The pattern that matters:** of the three pieces of evidence that would most
strengthen a failure case, **one is now in hand** — the *true cross-state money-flow
test* ran (`cross-state-fec-money.md` §E–I) and shows pervasive nationalization. The
remaining two — the *partisan consequence* of the turnout skew and *individual*
cross-party behavior — still trace to a single missing asset for Washington: **individual
party-of-record**. Washington publishes it only for presidential-primary declarants and only
under **RCW 29A.56.050**, which directs the Secretary of State to prescribe rules for
providing the declarations, or a list of the voters who participated, to the state and county
committees of that party. The statute sets no public-disclosure duration; the "~60–90 day
window" this project has worked from is **unverified** (`wa-pp-party-of-record-pra-scope.md`
flags it as needing confirmation, twice) and is not asserted here. What is certain is that
only Pierce County was obtained in time for 2024, which
is why the holding is Pierce-County-only; it is a collection-timing constraint, not a
disclosure-regime one. New York and Idaho do publish party of record, and both voter files
are now loaded, so the two questions are answerable there and are answered in the
companions — what remains gated is the *Washington* version.

---

## Conclusion

**The four-state evidence documents persistent inequalities in who participates, who
finances campaigns, and how often general elections are genuinely close. It does not support
a scalar diagnosis of democratic failure, and it does not identify the causal electoral
effect of campaign spending.**

Concretely, and in the order of the domains above: turnout is steeply age-skewed, and
sharply more so as salience falls; the donor class is narrow, old and top-heavy, and
over-represents the same party at both partisan poles; general elections are mostly not
close, while a smaller share offer no major-party choice at all; and money is strongly
associated with candidate performance by a design that cannot say which way the association
runs. Each is real and quantifiable here.

Each also has a benign reading that survives the evidence assembled. Differential
participation is voluntary in states with all-mail, postage-paid, same-day registration. A
lopsided seat may be lopsided because voters genuinely lean that way. A heavy-tailed
contribution distribution is what any voluntary funding system produces. And a correlation
between money and performance is exactly what a world in which money follows expected winners
would look like. **The evidence here does not adjudicate between the concerning and the
benign reading of any of the four**, which is why the conclusion is bounded rather than
scored.

*Two things left this section on 2026-08-15 and 2026-08-16. It opened "On present evidence:
electoral stress, not failure" and closed by saying "the accuracy gate holds the whole back
from a stronger verdict" — both of which read the gauntlet's scores as evidence about
electoral health, which is a use elicited judgement cannot support; those scores are now
Appendix A. And it said "most seats are uncontested in the general", which is false under
the series' own definitions: in Washington 2024, **83.5%** of seats were not close and
**34.6%** offered no D-v-R option. "Not close" is not "uncontested", and the safe-seat paper
split the two precisely because merging them was the original conflation. The synthesis had
reintroduced it in its own closing verdict — outside every coverage span, while the finding
that corrects it was gated.*

**On the data itself, two acquisition gaps that once bounded this programme are closed:**

1. ~~**Party-of-record** (statewide)~~ — **DONE.** The NY (NYSVOTER FOIL, 13.54M) and
   ID (SoS statewide file, 1.03M) voter files were received and loaded, each with
   individual party of record. The partisan consequence of turnout inequality and the
   individual donor crossover are now tested party-resolved in a deep-blue and a
   deep-red state ([`who-decides-new-york.md`](who-decides-new-york.md),
   [`who-decides-idaho.md`](who-decides-idaho.md),
   [`donor-class-and-the-electorate.md`](donor-class-and-the-electorate.md)). WA itself
   still lacks party of record before a possible 2028 PRA.
2. ~~A genuine multi-state money panel~~ — **DONE.** NY/TX contributions loaded, the
   FEC ingest direction corrected with a recipient-anchored inflow build, and the
   nationalization test run (`cross-state-fec-money.md` §E–I).

**The major acquisition gaps for the present analyses are largely closed.** What remains is
not only human sign-off, and this paragraph said it was until 2026-08-15. Still open and not
delegable to a signature: Washington still lacks individual party of record (see *Boundary of
inference*); the four states do not have equivalent coverage, so the cross-state claims are
not symmetric (Texas has no voter file and therefore no person-level donor analysis; NY and
ID publish party registration and WA does not; Idaho's roll carries a survivorship problem
unlike Washington's); and the model-generated diagnostic scores in Appendix A are stale
against the data as it now stands. The genuinely human-owned items are independent
verification of the headline numbers and posting the papers not yet posted — the Washington
companion is already on SSRN (7149263) and owes a revision, not a first upload
([`electoral-health-audit-log.md`](electoral-health-audit-log.md)).

---

## Appendix A — Methodological history: the 2026-06-27 idea gauntlet

**None of what follows is evidence about electoral health, and it is preserved because it is
the honest record of how this programme chose what to study.**

The programme began with a scoring exercise. Ten candidate research questions were each
scored 0–10 on eleven dimensions by a **language model**
(`idea-gauntlet/democracy_insight.workflow.js`) prompted to act as a quantitative
methodologist and democratic-theory reviewer, to search the web, and to be adversarial toward
its own conclusions:

- **Insight layer (research quality):** data sufficiency, inferential strength, novelty,
  systemic significance, usefulness, robustness.
- **Diagnostic layer (anatomy of a failure claim):** function impairment, trajectory,
  entrenchment, counter-thesis strength (*reverse-scored*), convergence.

Of the ten, nine scored "weak-against-null" and one "supports-null"; none reached "moderate"
or "strong" against the null. The exercise reported an **accuracy-weighted failure signal of
22/100**.

**Why that number is not in the paper.** It is an **elicited-judgement index, not a
measurement**: the mean of ten model-authored 0–100 severity scores, weighted by twenty more
model-authored 0–10 scores, of which only the first ten were ever published — so it **cannot
be recomputed from the table below**, which gives an unweighted mean of 18.3. The
distribution it summarises is partly prescribed by the prompt, which instructed the scorer to
*"default to 'data-insufficient' or 'weak-against-null' unless the evidence is genuinely
strong"*, so reading "nine weak-against-null" as a finding is partly circular. And it was
computed on 2026-06-27 against a data description that has since moved — 19 elections,
~$1.3B in contributions and 9.2M voter-score rows, against 22, $1.04B (Washington) and 16.1M
today — and never re-run, although Domain 4's sign has since reversed and Domain 2's
Washington figure has moved.

An external referee's verdict was that this is "a pseudo-quantitative statistic that adds
false precision to what is properly a qualitative synthesis", and that no additional
disclaimer cures it. That is right, and the same applies to the impairment, trajectory,
entrenchment, counter-thesis and convergence columns below: they are a useful internal
research-prioritisation rubric and they are not evidence about a state's electoral health.

**The ledger, as scored on 2026-06-27:**

| Question | Insight | Failure | Null | Impair | Traj | Entrench | Counter↓ | Converge |
|---|---|---|---|---|---|---|---|---|
| Who decides (turnout skew) | 62 | 22 | weak | 5 | 4 | 7 | 8 | 6 |
| Safe-seat democracy | 52 | 34 | weak | 6 | 5 | 8 | 8 | 7 |
| Whale vs small-dollar | 48 | 22 | weak | 4 | 4 | 6 | 8 | 6 |
| Donors are also high-frequency voters | 47 | 22 | weak | 5 | 3 | 7 | 7 | 7 |
| Donor class ≠ electorate | 42 | 22 | weak | 5 | 4 | 7 | 7 | 6 |
| Money moves margin? | 42 | 14 | weak | 3 | 4 | 5 | 8 | 6 |
| Outcomes pre-determined? | 38 | 14 | weak | 3 | 5 | 6 | 9 | 5 |
| Non-constituent money | 31 | 11 | weak | 4 | 3 | 6 | 7 | 4 |
| Straight-ticket lock-in | 28 | 17 | weak | 5 | 7 | 8 | 8 | 6 |
| Persuadable middle | 28 | 5 | supports-null | 2 | 2 | 4 | 9 | 5 |

*Counter↓ = counter-thesis strength (reverse): high values discount the failure
signal. Accuracy-weighted failure signal across all findings = **22/100**.*

---

## Appendix B — The companion papers, and their status

1. **Lead paper:** "Who Decides Washington State?" (Finding 1) — **DRAFTED**
   ([`who-decides-washington.md`](who-decides-washington.md)).
2. **Companion:** "Safe-Seat Washington / the Four-State Map" (Finding 2) — **DRAFTED**
   ([`safe-seat-washington.md`](safe-seat-washington.md)); observed margins, complete
   four-state lower-chamber map, primary-turnout cut. (Uncontested-filer join folded in
   as the "no major-party choice" bucket.)
   Party-resolved companions now drafted: "Who Decides New York?"
   ([`who-decides-new-york.md`](who-decides-new-york.md), deep blue) and "Who Decides
   Idaho?" ([`who-decides-idaho.md`](who-decides-idaho.md), deep red).
3. **Money series:** Findings 3 + 5 — **DRAFTED** as
   [`donor-class-and-the-electorate.md`](donor-class-and-the-electorate.md) (WA + NY + ID,
   party-resolved donor class, whale concentration, crossover), building on
   [`cross-state-fec-money.md`](cross-state-fec-money.md) (§F donor-class + matcher-bias
   correction; §A/E whale-vs-small-dollar + concentration). *(This line read "Conduit/earmark
   attribution verified (§E)" until 2026-08-15, which contradicted Finding 3's own objection
   bullet — that a true per-race figure "needs an earmark-attribution layer that does not yet
   exist". What §E verified is that FEC records earmarked gifts under the candidate committee
   as transaction type 15E, so the conduit-side 24T rows are correctly excluded and nothing is
   double-counted. That is an ingest correctness check, not the ultimate-recipient attribution
   Finding 3 says it lacks. An external referee found the two sentences arguing with each
   other.)*
4. **Methods/curiosity piece:** Finding 6 — **DRAFTED** as
   [`does-money-move-votes.md`](does-money-move-votes.md) (2026-07-26). The story is the
   honest non-identification: money is the strongest single correlate of overperformance
   (+0.60) yet leaves no causal fingerprint that this design can read — allocation holdout R²
   0.028, the forecast model discards the term against a known baseline, and the directional
   test, run across 34 federal district-cycles and a further 129 state-legislative ones,
   returns intervals that span zero on every specification and a headline slope that one
   deleted race reverses. The verdict stays "cannot confirm or refute," and the citable
   result is that the limit is the **design** — outside money concentrates in a few races and
   is targeted at expected closeness — not the disclosure record.
5. **Party-of-record boundary questions — DONE** (NY + ID voter files loaded); the
   longitudinal/causal version of Finding 4 remains for a future extension.
