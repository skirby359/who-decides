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
>   (WA 88.8 / NY 88.6 / TX 94.0 / ID 92.9% non-competitive), and the observed
>   counts **validate** the model's projection used below.
> - **Findings 4 & 5 → [`cross-state-fec-money.md`](cross-state-fec-money.md) §F**
>   — and the matcher-bias objection to Finding 5 has been **tested and rejected**
>   (see that finding below); the donor match is now **382K**, not 320K.
> - **The "non-constituent money" boundary item is no longer blocked** — NY/TX
>   contributions were loaded and the recipient-anchored inflow built, so the
>   cross-state nationalization test *did* run (`cross-state-fec-money.md` §E–I).
>
> None of this changes the **"stress, not failure"** verdict, but it moves the lead
> findings from *literature-borrowed* to *established in-data*, and resolves one of
> the three boundary blockers. The two that remain (individual party-of-record;
> party-resolved turnout/crossover) still gate a stronger verdict and await the
> NY/ID voter files.

---

## Method

Each research question was scored 0–10 on eleven dimensions by an independent,
web-searching reviewer instructed to be adversarial toward its own conclusions:

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

**Data provenance:** ~5.1M precinct-result rows across 19 elections (WA) plus
NY/TX/ID; ~8.6M individual contributions (FEC + state PDC, ~$1.3B, 2018–2026) with
employer/occupation/ZIP; ~9.2M voter-score rows; ~27.1M individual VRDB vote
records; and the rare asset — **382K voters matched to their donations** at the
person level (up from 320K after the full-first-name matcher tier; see §F of the
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
  older/whiter); Anzia (*Timing and Turnout*); Lucero et al. 2025 (on-cycle
  consolidation cut California's over-55 local share from ~half to 28%).

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
  most recent general for partisan legislative + congressional offices → two-party
  margin per district → band counts (the "no major-party choice" bucket captures the
  *truly uncontested* / same-party seats). For WA, built the 2016–2024 seat-level trend
  (stable ~85%, dipping only in the 2018 wave) and the primary-to-general turnout ratio
  in safe seats (~0.5) — the one
  place this data *adds* to Cook/Ballotpedia/Unite America by attaching real
  turnout (and the voter-donor join) to the "primary decides" claim.
- **Key literature.** Cook PVI (swing districts 164 in 1997 → ~72 post-2016);
  Ballotpedia Competitiveness Index (38% of state-leg seats uncontested in 2024);
  Unite America (*The Primary Problem*).

### 3. Whale-dominated money behind a small-dollar facade
*Insight 48 · failure-contribution 22 · null: weak-against · V-Dem: egalitarian, participatory · trajectory: indeterminate*

- **Defensible claim.** WA money is broad by headcount but concentrated by dollar.
  For recipient-cycles with ≥100 distinct donors (n=2,821), the **median itemized
  gift is $25** yet single gifts reach **$2.5M**, with a per-recipient Gini ~**0.61**.
  The data can quantify, per race and cycle, the sub-$200 retail share vs. the whale
  layer.
- **Strongest objection.** The recipient key is `fec_candidate_id`, and the
  highest-volume "recipients" are conduits (ActBlue, JFCs), so a naive per-recipient
  Gini measures a *conduit's pass-through book*, not a candidate's race. A true
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

- **Defensible claim (cross-sectional only).** Among the 382,408 matched voters,
  donors are a participation elite: **84.0% are super-voters vs 50.1%** of non-donors
  (average turnout propensity 0.95 vs 0.75; donor-class verifier F4). Financial voice
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
  the cross-sectional benchmark — matched donors are **84.0% super-voters vs 50.1%** of
  non-donors (1.68×), mean turnout propensity 0.953 vs 0.748 — framed strictly as
  association, with the match-bias diagnostic from §F2 (the giving↔voting overlap is real;
  the *causal/longitudinal* version remains out of reach).
- **Key literature.** Verba/Schlozman/Brady (*Voice and Equality*; *Unheavenly
  Chorus*) — money is the most income-skewed form of participation; the donor pool
  is a structural elite (the *constant* against which any worsening must be measured).

### 5. The donor class is not the electorate
*Insight 42 · failure-contribution 22 · null: weak-against · V-Dem: egalitarian, participatory · trajectory: indeterminate*

- **Defensible claim.** At the person level, donors are a narrow slice that does not
  mirror the electorate: **~3.5–6% of voters**, skewed old (Silent 1.87×, Boomer
  1.63× over-represented; Gen Z 0.18×, Millennial 0.60× under-represented),
  overwhelmingly super-voters, geographically concentrated (**~61% of WA donor
  dollars from two Seattle-metro ZIP3s**), and internally top-heavy (top 1% of
  matched donors supply **47.7%** of matched dollars, top 10% supply **80.0%**).
  RETIRED ($221.7M, 21.3%) and NOT EMPLOYED ($147.4M, 14.1%) are the two largest
  occupation blocs. The voter↔donor join makes this *person-level*, not ecological —
  the genuine value-add over the standard FEC-aggregate literature.
- **Strongest objection — now tested and rejected.** The objection was that the skew
  is a **matcher artifact**: the (last name, first initial, ZIP) unique-key over-selects
  the older, rarer-named, stable-address residents it then "finds" over-represented.
  **Tested directly** (cross-state §F2): the probability a voter is uniquely matchable
  on that key is **nearly flat across generations (68.9%–73.1%, a ~4-pt spread)**, so
  inverse-propensity re-weighting **barely moves** the over-representation ratios
  (Silent 1.87→1.83×, Gen Z 0.17→0.17× on the refreshed 382K match). The age skew is a
  real property of *who gives*, not of who the matcher can find. (One residual bias it
  can't observe — donors who moved between giving and now — runs the *same* direction,
  so the raw skew is an upper bound; the named name-commonness mechanism explains almost
  none of it.) The voter file still has **no income and no race**, so the literature's
  richer/whiter claims remain proxied, not tested.
- **First analysis — DONE** ([`cross-state-fec-money.md`](cross-state-fec-money.md) §F2):
  the matcher-bias inverse-propensity re-weighting above; skews reported raw *and*
  re-weighted; income/race labeled untestable. Refreshed concentration on the 382K match:
  top-1% **47.7%**, top-10% **80.0%**, Gini 0.862; ~61% of dollars from two Seattle ZIP3s.
- **Party-resolved — DONE for NY + ID** ([`donor-class-and-the-electorate.md`](donor-class-and-the-electorate.md)):
  with party of record the demographic claim sharpens into a partisan one, and the striking
  result is that it holds **in both directions of the spectrum** — the donor class
  over-represents registered Democrats relative to the electorate in **deep-blue NY (+15
  pts)** *and* **deep-red Idaho (+9 pts)**, under-represents the unaffiliated in both, and
  the age skew replicates (NY 48% / ID 51% of donors are 65+). Crossover: Democrats are
  near-monolithic donors (94% NY / 93.5% ID → own party) and unaffiliated donors lean
  Democratic (~2:1 NY, ~3:1 ID). So the Democratic tilt is a property of who donates, not
  of a state's majority party. (ID is a state-money layer; see that paper's caveats.)
- **Key literature.** Demos (*Whose Voice, Whose Choice*); Bonica (DIME); and the
  same-state result that tempers the benign reading — **Grumbach, Sahn & Staszak
  (APSR): Seattle's democracy vouchers did *not* diversify the donor pool.**

### 6. Money marks strength; it does not appear to move margin
*Insight 42 · failure-contribution 14 · null: weak-against · V-Dem: egalitarian, electoral, deliberative · trajectory: indeterminate*

- **Defensible claim.** Finance behaves as a marker of pre-existing candidate
  strength, not an independent vote-mover: raw fundraising log2(D/R) correlates
  **+0.55** with overperformance, but spend *allocation* has cross-cycle holdout
  R² ~**0.00**, and the forecast model zeroes the fundraising term post-redistricting
  because the baseline already absorbs it. The honest reading — "money follows the
  scoreboard" — is, on the *vote-buying* axis, consistent with the healthy null,
  while leaving the **access/agenda-setting** channel untested.
- **Strongest objection.** The whole thing is a correlation with no exogenous
  variation — +0.55 is exactly what a true causal effect *would also* produce. The
  allocation-R²-zero null is underpowered and tests spend *mix*, not *level*. So the
  data can neither confirm nor refute vote-buying; it can only show money is
  endogenous to candidate quality.
- **First analysis — DONE** (`scripts/diag_ie_vs_margin.py`). For FEC-attributed
  races (Schedule E carries support/oppose + district), it regresses the
  *fundamentals-net residual* (actual − model-predicted Dem %, **not** the raw
  margin) on the net pro-Dem IE advantage. The run surfaced a harder boundary than
  the design assumed: **directional IE on disk exists for a single cycle (2024 FEC
  Schedule-E, 7 WA U.S. House races)**, and the $70.6M of PDC state-legislative IE
  carries a NULL support/oppose flag — so it cannot enter a directional test at all.
  One cross-section of 7 races cannot bear the bootstrap CI, the early-vs-late split,
  or the next-cycle placebo, so **inference is withheld** (the script says so rather
  than reporting a coin-flip slope). What the descriptive cross-section *shows* still
  cuts toward the null: the association is, if anything, **negative** (−0.42 pp per
  $1M net pro-Dem IE, Pearson r −0.43, n=7) — money flowing toward the side that is
  *behind*, the textbook endogeneity signature — and the single most IE-saturated
  House race in the country, **WA-03 2024 ($40.1M total IE, +$16.2M net pro-Dem),
  finished +0.06 pp off its fundamentals: dead-on.** The citable Finding-6 result for
  WA today is therefore the *data ceiling itself*: the public machine-readable IE
  record is too thin to move the verdict off "cannot confirm or refute." Unlock =
  multi-cycle FEC Schedule-E backfill (`load_fec_independent_expenditures(cycle=…)`,
  rate-limited, federal House only); even then n stays small and uninstrumented.
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
  out-of-region, and on the **outflow** side each state sends the *majority* of its
  candidate money out of region (NY 62%, ID 68% — the most — TX 43%) — Georgia Senate
  races alone drew ~$68M from residents of the four states. The earlier "93.6% in-state"
  was indeed the ingestion artifact this item warned about. (State-level money — WA PDC,
  NY BOE, ID Sunshine, TX TEC — is now also loaded, though not yet folded into these
  federal cross-state cuts.)
- **Straight-ticket lock-in / candidate accountability (insight 28, data-sufficiency 3).**
  Individual ticket-splitting is **unmeasurable** (cross-party matchback fires for
  ~0 voters), and the precinct ticket-split tables can't yield a 19-election trend
  (epoch-versioned precincts; 2022 renumbering → 0 common precincts). The only
  defensible cut is an *ecological* county-level cross-office consistency trend.
- **Is there a persuadable middle? (insight 28, the one "supports-null" finding).**
  `voter_party_choice` is Pierce-only, 2024-only; **exactly 0 voters** appear in two
  party-primary cycles. WA has no party registration. The honest result is a
  limits-and-null finding that *converges with* the gold-standard literature
  (Abramowitz & Webster; Kuriwaki's cast-vote-record work), not against it.
- **Are outcomes pre-determined? (insight 38).** The notarized backtest (MAE ~6.4,
  ~94% directional) bounds how much aggregate campaigning moves results — but
  predictability is **not** causal inertness (Gelman & King: predictability is the
  *footprint* of effective deliberation), the headline is safe-seat-inflated, and
  the data has no counterfactual.

**The pattern that matters:** of the three pieces of evidence that would most
strengthen a failure case, **one is now in hand** — the *true cross-state money-flow
test* ran (`cross-state-fec-money.md` §E–I) and shows pervasive nationalization. The
remaining two — the *partisan consequence* of the turnout skew and *individual*
cross-party behavior — still trace to a single missing asset: **individual
party-of-record**, which Washington does not publish. That asset is the sole
remaining gate on a stronger verdict.

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
of the headline numbers and posting to SSRN/SocArXiv
([`publication-checklist.md`](publication-checklist.md)).

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

1. **Lead paper:** "Who Decides Washington?" (Finding 1) — **DRAFTED**
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
4. **Methods/curiosity piece:** Finding 6 — "Does Money Move Votes in Washington?" —
   **analysis executed** (`diag_ie_vs_margin.py`; see Finding 6 above). The story is the
   honest near-null *and* the data ceiling: directional IE is one cycle deep, so the
   verdict stays "cannot confirm or refute." Prose write-up still to assemble.
5. **Party-of-record boundary questions — DONE** (NY + ID voter files loaded); the
   longitudinal/causal version of Finding 4 remains for a future extension.
