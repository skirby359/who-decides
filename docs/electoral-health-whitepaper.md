# The State of Electoral Health: WA / NY / TX / ID
### A research prospectus built from precinct results, campaign finance, and the individual voter record

*Draft outline — 2026-06-27. Derived from the democracy-insight gauntlet
(`idea-gauntlet/RESULTS-democracy-insight-2026-06-27.md`): 10 research questions
scored on 11 dimensions, V-Dem-anchored, against a pre-registered null.*

---

## Scope and integrity statement (read first)

This program studies the **electoral** dimension of democracy — participation,
representation, political equality, and contestation. It is **silent** on rule of
law, civil liberties, press freedom, and executive constraint, and it makes no
claim about them.

Three commitments govern every section below:

1. **Pre-registered null.** The working hypothesis is that *"Washington's (and the
   comparison states') electoral democracy is functioning."* A finding moves
   against that null only when the evidence earns it.
2. **Accuracy gate.** Each finding contributes to any larger conclusion *only in
   proportion to its data sufficiency × inferential strength.* A striking number
   built on data the warehouse cannot actually carry is reported as a limit, not a
   result.
3. **No verdict.** This document assembles the *components* of a democratic-health
   assessment. It deliberately does **not** declare a "failure of democracy." The
   point is to be the instrument capable of detecting one honestly — not to reach
   for the headline.

**Bottom line of the scan that produced this prospectus:** of 10 questions, **nine
scored "weak-against-null" and one "supports-null"; none reached "moderate" or
"strong" against the null.** The accuracy-weighted failure signal was **22/100**.

<sub>**Three things about that number, all of which a reader should know before weighing it.**
First, it is an **elicited-judgment index, not a measurement**: it is the mean of ten
model-authored 0–100 severity scores, weighted by twenty more model-authored 0–10 scores, and
Appendix A publishes only the first ten — so the figure **cannot be recomputed from this
paper's own table**, which gives an unweighted mean of 18.3. Second, the distribution it
summarises is partly prescribed by the prompt, which instructed the scorer to *"default to
'data-insufficient' or 'weak-against-null' unless the evidence is genuinely strong"*; reading
"nine weak-against-null" as a finding is therefore partly circular. Third, it was computed on
**2026-06-27 against a data description that has since moved** — the scan was told 19
elections, ~$1.3B in contributions and 9.2M voter-score rows, against 22, ~$1.04B and 16.1M
today — and it has not been re-run, although Finding 6's sign has since reversed and Finding
2's Washington figure has moved. Treat it as a snapshot of how a triage step scored a research
agenda, not as a result of the research.</sub>
The honest reading of the present evidence is **measurable electoral stress that is
real, largely known to the literature, reformable, and admits strong benign
readings — not, on this data, systemic failure.** Critically, the findings that
could most strengthen a failure case are precisely the ones the data is currently
blind to (see *Boundary of Inference*).

> **Status update — 2026-06-28 (first analyses now executed).** This began as a
> prospectus of analyses *to run*. Several have since been run on data already on
> disk, and the realized write-ups exist:
> - **Finding 1 → [`who-decides-washington.md`](who-decides-washington.md)** (gray
>   off-year electorate, from 27.1M VRDB vote records).
> - **Finding 2 → [`safe-seat-washington.md`](safe-seat-washington.md)** — now on
>   **observed** margins, extended to a **complete four-state lower-chamber map**
>   (WA **87.8** / NY 88.0 / TX 94.0 / ID 92.9% not close). The observed counts and the
>   model projection below are in **loose aggregate agreement, which is not a validation** —
>   they are different units (seats against districts), different years, and different
>   denominators, and Texas differs by 13 points (94.0% observed against 81% projected). A
>   validation would predict historical elections without using their outcomes and report
>   calibration and false-safe rates on one unit; that has not been run. *(WA read 88.8% until the
>   seat universe was rebuilt from certified statewide summaries; the old figure came
>   from a results-table universe that silently dropped 24 King County House seats per
>   cycle in 2016 and 2018.)*
> - **Findings 4 & 5 → [`cross-state-fec-money.md`](cross-state-fec-money.md) §F**
>   — and the matcher-bias objection to Finding 5 has been **tested and rejected**
>   (see that finding below); the donor match is **314,974** on the full-name-key
>   specification adopted 2026-07-27 (it was 382K all-tier, and 320K before tier 0).
> - **The "non-constituent money" boundary item is no longer blocked** — NY/TX
>   contributions were loaded and the recipient-anchored inflow built, so the
>   cross-state nationalization test *did* run (`cross-state-fec-money.md` §E–I).
>
> None of this changes the **"stress, not failure"** verdict, but it moves the lead
> findings from *literature-borrowed* to *established in-data*, and resolves one of
> the three boundary blockers. The two that remain — individual party-of-record and
> party-resolved turnout/crossover — **are now answered for New York and Idaho**, whose
> voter files are loaded and whose companions report them; they remain open **for
> Washington**, whose party-of-record window has closed.

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

Function impairment is anchored to the **V-Dem component indices** (electoral,
liberal, participatory, deliberative, egalitarian) so severity is legible and
comparable across states and time.

**Data provenance:** ~5.1M precinct-result rows across 22 elections (WA) plus
NY/TX/ID; ~8.6M individual contributions (FEC + state PDC, **~$1.04B**, 2018–2026) with
employer/occupation/ZIP; ~16.1M voter-score rows (one per voter per district scope,
~5.5M distinct voters); ~27.1M individual VRDB vote
records; and the rare asset — **314,974 voters matched to their donations** at the
person level, on the full-name-key specification adopted 2026-07-27; see §F of the
cross-state money paper).

---

## Findings — the publishable core (write these up first)

Ordered by insight composite. Each carries its single most defensible claim, the
strongest objection to it, the V-Dem function and diagnostic read, and the first
concrete analysis to run.

### 1. Who actually decides? The gray off-year electorate
*Insight 62 · failure-contribution 22 · null: weak-against · V-Dem: participatory, egalitarian, electoral · trajectory: stable*

- **Defensible claim.** The electorate that decides odd-year general elections in
  WA is roughly half the size of the presidential electorate and dramatically
  older. From 27.1M VRDB vote records (~100% birthdate coverage): voters 65+ were
  **~37–40%** of off-year ballots (2021/2023/2025) vs **28.5%** in 2024, while
  18–29 were **7–8%** off-year vs **14.2%** presidential — a **~5:1** senior-to-youth
  ratio off-year vs ~2:1 presidential. Individually, 18–29 turnout collapses
  **58.4% → 15.8%** (presidential → off-year) while 65+ falls only 88.3% → 61.3%.
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

### 2. Safe-seat democracy: the collapse of general-election contestation
*Insight 52 · failure-contribution 34 (highest) · null: weak-against · V-Dem: electoral, participatory, deliberative · trajectory: worsening*

- **Defensible claim.** The large majority of seats are non-competitive. On the
  model's own symmetric Cook-style bands, seats at ≥10-pt margin run **WA 90%
  (53/59), NY 86% (206/240), TX 81% (167/205), ID 92% (34/37)**, with genuine
  Tossups a small minority. When the general is foregone, the operative decision
  moves to lower-turnout primaries. This is a structural counting result that does
  **not** depend on any blocked/weak signal.
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

### 3. Whale-dominated money behind a small-dollar facade
*Insight 48 · failure-contribution 22 · null: weak-against · V-Dem: egalitarian, participatory · trajectory: indeterminate*

- **Defensible claim.** WA money is broad by headcount but concentrated by dollar. The
  **median itemized gift is $25** in both money systems, while per-recipient-cycle
  concentration is substantial: median Gini **0.578** federal and **0.579** state, over
  recipient-cycles with ≥100 distinct donors (**822** federal, **1,989** state). The data can
  quantify, per race and cycle, the sub-$200 retail share against the whale layer.

  <sub>**Corrected 2026-08-10.** These figures were previously given as "n=2,821 … single
  gifts reach $2.5M … Gini ~0.61", which was computed on the **pooled** FEC+PDC table — the
  exact pooling Finding 5's panel note says the series corrected everywhere else. Pooled, the
  count is 2,814 today; separated it is 822 federal and 1,989 state. The **$2.5M maximum is a
  PDC state gift**; the federal maximum is $929,600, so the old sentence paired a median from
  one money system with a maximum from another. The 0.61 does not reproduce on any basis I
  can construct — both layers give 0.578 — and it is withdrawn rather than restated.</sub>
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

### 4. Money and votes stack on the same people
*Insight 47 · failure-contribution 22 · null: weak-against · V-Dem: participatory, egalitarian · trajectory: indeterminate · (most novel: 6)*

- **Defensible claim (cross-sectional only).** Among the 314,974 matched voters,
  donors are a participation elite: **87.6% are super-voters vs 50.9%** of non-donors
  (average turnout propensity **0.967 vs 0.749**; donor-class verifier F4). Financial voice
  and electoral voice concentrate on the same individuals rather than offsetting.
- **Strongest objection.** The *causal/longitudinal* version ("giving *makes* people
  vote more; inequality *deepens*") is unsupportable here: donors are pre-selected
  for engagement (reverse causation is equally plausible), the match is biased
  toward older/stable-address/super-voting/uncommon-named people (inflating the
  gap), and `voter_donor_affiliation` collapses each voter to one row, so
  first-gift-then-vote sequencing can't be reconstructed on a shallow 2021–2026
  history. The benign reading — donating as a *gateway* that broadens participation
  — is live.
- **First analysis — DONE** ([`cross-state-fec-money.md`](cross-state-fec-money.md) §F3):
  the cross-sectional benchmark — matched donors are **87.6% super-voters vs 50.9%** of
  non-donors (**1.72×**), mean turnout propensity **0.967 vs 0.749** — framed strictly as
  association, with the match-bias diagnostic from §F2 (the giving↔voting overlap is real;
  the *causal/longitudinal* version remains out of reach).
- **Key literature.** Verba/Schlozman/Brady (*Voice and Equality*; *Unheavenly
  Chorus*) — money is the most income-skewed form of participation; the donor pool
  is a structural elite (the *constant* against which any worsening must be measured).

### 5. The donor class is not the electorate
*Insight 42 · failure-contribution 22 · null: weak-against · V-Dem: egalitarian, participatory · trajectory: indeterminate*

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
- **Strongest objection — now tested and rejected.** The objection was that the skew
  is a **matcher artifact**: the (last name, first initial, ZIP) unique-key over-selects
  the older, rarer-named, stable-address residents it then "finds" over-represented.
  **Tested directly** (cross-state §F2): the probability a voter is uniquely matchable
  on that key is **nearly flat across generations (69.1%–73.3%, a ~4-pt spread)**, so
  inverse-propensity re-weighting **barely moves** the over-representation ratios
  (Silent 1.96→1.91×, Gen Z 0.09→0.09× on the 314,974-voter match). The age skew is a
  real property of *who gives*, not of who the matcher can find. (One residual bias it
  can't observe — donors who moved between giving and now — runs the *same* direction,
  so the raw skew is an upper bound; the named name-commonness mechanism explains almost
  none of it.) The voter file still has **no income and no race**, so the literature's
  richer/whiter claims remain proxied, not tested.
- **First analysis — DONE** ([`cross-state-fec-money.md`](cross-state-fec-money.md) §F2):
  the matcher-bias inverse-propensity re-weighting above; skews reported raw *and*
  re-weighted; income/race labeled untestable. Concentration on the pooled 314,974 match:
  top-1% **46.6%**, top-10% **79.3%**, Gini 0.857; 61.4% of dollars from two Seattle ZIP3s.
  Superseded per the panel note above — federal panel top-1% **41.2%** [38.6–43.4],
  Gini **0.815** [0.806–0.822], two-ZIP3 share **63.5%**; state panel top-1% **43.5%**
  [38.7–48.9], Gini **0.821** [0.806–0.838]. *(This line previously read 42.4% [40.2–44.9]
  for the federal panel — the all-tier value, contradicting the 41.2% in the panel note
  directly above it. The bootstrap CIs are the per-panel re-runs in
  [`cross-state-fec-money.md`](cross-state-fec-money.md) §F4.)*
- **Party-resolved — DONE for NY + ID** ([`donor-class-and-the-electorate.md`](donor-class-and-the-electorate.md)):
  with party of record the demographic claim sharpens into a partisan one, and the striking
  result is that it holds **in both directions of the spectrum** — the donor class
  over-represents registered Democrats relative to the electorate in **deep-blue NY (+16.1
  pts federal, +9.6 state)** *and* **deep-red Idaho (+8.6 federal, +9.8 state)**,
  under-represents the unaffiliated in both, and
  the age skew replicates (65+: NY federal **49.9%**, ID federal **66.8%**, ID state
  **51.3%**). Crossover: Democrats are
  near-monolithic donors (**95%** NY / **94.6%** ID → own party) and unaffiliated donors lean
  Democratic (~2:1 NY, nearly **4:1** ID). So the Democratic tilt is a property of who donates,
  not of a state's majority party. (The ID crossover and 51.3% figures are the state-money
  layer; see that paper's caveats.) **These are the primary (full-name-key) specification.**
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

### 6. Money marks strength; it does not appear to move margin
*Insight 42 · failure-contribution 14 · null: weak-against · V-Dem: egalitarian, electoral, deliberative · trajectory: indeterminate*

- **Defensible claim.** Finance behaves as a marker of pre-existing candidate
  strength, not an independent vote-mover: raw fundraising log2(D/R) correlates
  **+0.58** with overperformance, but spend *allocation* has cross-cycle holdout
  R² of **0.02**, and the forecast model zeroes the fundraising term post-redistricting
  because the baseline already absorbs it. The honest reading — "money follows the
  scoreboard" — is, on the *vote-buying* axis, consistent with the healthy null,
  while leaving the **access/agenda-setting** channel untested.
- **Strongest objection.** The whole thing is a correlation with no exogenous
  variation — +0.58 is exactly what a true causal effect *would also* produce. The
  allocation-R²-zero null is underpowered and tests spend *mix*, not *level*. So the
  data can neither confirm nor refute vote-buying; it can only show money is
  endogenous to candidate quality.
- **First analysis — DONE** (`scripts/diag_ie_vs_margin.py`). For FEC-attributed
  races (Schedule E carries support/oppose + district), it regresses the
  *fundamentals-net residual* (actual − model-predicted Dem %, **not** the raw
  margin) on the net pro-Dem IE advantage. **Directional IE on disk spans five cycles
  (2018–2026 FEC Schedule-E, 34 scorable WA U.S. House races)**, and the **$51.7M of
  direction-coded PDC state-legislative IE** (form C-6 section C6.3, ingested 2026-08-09)
  adds **129 scorable district-cycles** on the same design — see
  `scripts/diag_pdc_ie_vs_margin.py`. That extension does not settle the question: every
  interval still spans zero and the **sign becomes specification-dependent** (−3.816 to
  +4.890 across four specifications), which is evidence the constraint is structural
  rather than a shortage of cells. The regression **now runs**: the slope is **+0.515 pp per
  $1M net pro-Dem IE (Pearson r +0.186, n=34)**, with a bootstrap interval of
  −0.600 to +2.821 that spans zero. The interval is the result — it admits both no
  effect and effects large enough to decide a close race. The most heavily funded
  race in the panel, **WA-03 2024 ($18.61M total IE, +$6.09M net pro-Dem), finished
  +0.06 pp off its fundamentals: dead-on.** The citable Finding-6 result for WA is
  therefore that the public record can *bound* the persuasion effect but not sign it,
  and that endogeneity — spending aimed at expected closeness — makes even a narrower
  interval an association rather than an effect.
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

## Boundary of inference — what this data cannot (yet) support

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

## The verdict-in-waiting, and what gates it

On present evidence: **electoral stress, not failure.** Turnout is steeply
age-skewed; the donor class is narrow, old, and top-heavy; most seats are
uncontested in the general; money tracks candidate strength. Each is real and
quantifiable here. But each also has a strong benign reading that survives, the
trajectories are mostly borrowed from the national literature rather than
established in-data, and the accuracy gate holds the whole back from a stronger
verdict.

To move past "weak-against-null," the program needed to close two gaps. **Both are now
closed:**

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

With both data gaps closed, the remaining work is human-owned: independent verification
of the headline numbers, and posting the papers that are not yet posted — the Washington
companion is already on SSRN (7149263) and owes a revision, not a first upload — to
SSRN/SocArXiv
([`electoral-health-audit-log.md`](electoral-health-audit-log.md)).

---

## Appendix A — Diagnostic ledger (all 10 questions)

| Question | Insight | Failure | Null | Impair | Traj | Entrench | Counter↓ | Converge |
|---|---|---|---|---|---|---|---|---|
| Who decides (turnout skew) | 62 | 22 | weak | 5 | 4 | 7 | 8 | 6 |
| Safe-seat democracy | 52 | 34 | weak | 6 | 5 | 8 | 8 | 7 |
| Whale vs small-dollar | 48 | 22 | weak | 4 | 4 | 6 | 8 | 6 |
| Giving reinforces voting | 47 | 22 | weak | 5 | 3 | 7 | 7 | 7 |
| Donor class ≠ electorate | 42 | 22 | weak | 5 | 4 | 7 | 7 | 6 |
| Money moves margin? | 42 | 14 | weak | 3 | 4 | 5 | 8 | 6 |
| Outcomes pre-determined? | 38 | 14 | weak | 3 | 5 | 6 | 9 | 5 |
| Non-constituent money | 31 | 11 | weak | 4 | 3 | 6 | 7 | 4 |
| Straight-ticket lock-in | 28 | 17 | weak | 5 | 7 | 8 | 8 | 6 |
| Persuadable middle | 28 | 5 | supports-null | 2 | 2 | 4 | 9 | 5 |

*Counter↓ = counter-thesis strength (reverse): high values discount the failure
signal. Accuracy-weighted failure signal across all findings = **22/100**.*

## Appendix B — Suggested publication sequence (status as of 2026-06-28)

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
   correction; §A/E whale-vs-small-dollar + concentration). Conduit/earmark attribution
   verified (§E).
4. **Methods/curiosity piece:** Finding 6 — **DRAFTED** as
   [`does-money-move-votes.md`](does-money-move-votes.md) (2026-07-26). The story is the
   honest near-null: money is the strongest single correlate of overperformance (+0.58) yet
   leaves no causal fingerprint — allocation holdout R² 0.02, the forecast model discards
   the term against a known baseline, and the directional test, run across 34 federal
   district-cycles and a further 129 state-legislative ones, returns intervals that span
   zero on every specification. The verdict stays "cannot confirm or refute," and the
   citable result is that the limit is the **design** — outside money concentrates in a few
   races and is targeted at expected closeness — not the disclosure record.
5. **Party-of-record boundary questions — DONE** (NY + ID voter files loaded); the
   longitudinal/causal version of Finding 4 remains for a future extension.
