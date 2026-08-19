# Four States, Four Donor Economies
### Federal individual contributions in Washington, New York, Texas, and Idaho (FEC, 2018–2026)

**Stephen Kirby** · Tikor Consulting · July 2026

*AI-assisted drafting and analysis review. All figures are reproducible from
public-record data and from the open-source scripts cited below, including
`scripts/verify_cross_state_money.py`. The paper source, code, and data-acquisition recipe
are public at <https://github.com/skirby359/who-decides>; the underlying voter files are
not redistributed. Contact: kirby@tikorconsulting.com.*

***DRAFT — pending human/editorial sign-off.** `scripts/verify_cross_state_money.py` scrapes this
paper and asserts its figures against the data, with the exceptions the script names in its own
output; that gate is automated and is not the sign-off. The sign-off is a person reading the paper end to end, recorded in
[`cross-state-money-submission-notes.md`](cross-state-money-submission-notes.md) §Sign-off.*

*Companion to [the electoral-health prospectus](electoral-health-whitepaper.md). This
realizes that paper's cross-state money thread, which was previously data-blocked
(NY/TX had zero contributions loaded). Source: `scripts/cross_state_fec_money.py`.
**Idaho added 2026-07-19** (FEC outflow + inflow loaded to parity) as the small,
deep-red pole; **all sections (headline, Findings 1–5, Tests A–I, and the flow
matrix G) are now four-state** — every table carries WA/NY/TX/ID.*

---

## Abstract

Campaign-finance concentration is usually reported nationally, which conceals that states
differ in the shape of their donor economies and not merely in their size. This paper measures
federal individual contributions made by residents of four deliberately dissimilar states —
Washington, New York, Texas, and Idaho — across the 2018 through 2026 cycles, from Federal
Election Commission bulk records, and then measures the money flowing the other way, into those
states' congressional races, from a recipient-anchored dataset built for the purpose. The
pooled concentration ordering does not track partisanship, though it is only partly stable
across cycles: New York is the most top-heavy in every cycle, while the ordering beneath it
shifts from cycle to cycle (§A). New York is the most
top-heavy: its top one percent of donors supply **47.5%** of its federal dollars, against
**41.7%** in Texas, **39.3%** in Washington, and **36.1%** in Idaho, with Gini coefficients from
**0.848** down to **0.775**. Idaho, the smallest and reddest of the four, is the most retail on
almost every measure, including a **29.0%** share of dollars from gifts under $200 against New
York's **13.8%** — the exception is the ≥$5,000 share, where Washington is marginally lower
(**20.0%** against Idaho's **20.1%**) — so across these four cases donor concentration does
not align with state partisanship. Washington has the
broadest donor participation relative to population. Nearly a third of Idaho's donor dollars,
**31.7%**, come from donors reporting their occupation as retired, against **11.8%** in New
York, and each state carries a distinct sector signature. Two methodological points are
load-bearing. A committee's recipient state must be resolved through the candidate's office
state rather than the committee's registration address, because compliance vendors cluster
registrations in Washington DC and Virginia. And earmarked conduit gifts are recorded by the
Commission under the candidate committee, so a conduit's share of receipts cannot be read as
conduit reliance even though the money itself is fully captured. The paper reports
distributional structure, not influence. It **does** name the largest individual donors in
each state (Section C), all of them identified from public FEC disclosure filings; what it
does not do is attribute motive or effect to any of them.

**Keywords.** campaign finance; political contributions; donor concentration; small-dollar
donors; out-of-state money; Federal Election Commission; inequality; state comparison;
Washington; New York; Texas; Idaho

---

## Scope and method (read first)

**Basis: federal individual contributions made by IN-STATE RESIDENTS, 2018–2026.**
NY and TX hold pure FEC bulk data (donor-residence-filtered); Washington and Idaho
mix state finance (WA=PDC, ID=Sunshine) + federal FEC in `individual_contributions`,
so both are restricted to rows carrying an FEC committee id (`fec_candidate_id ~
'^[CPHS]'`, which excludes the state-finance rows) with `contributor_state = <st>`. All
four are therefore the same thing: **how each state's residents fund federal
politics.**

**Findings 1–5 and Tests A–D are an OUTFLOW-by-donor-residence measure** — they show where
each state's residents *send* money (the per-state FEC ingest is donor-state-filtered). The
complementary **INFLOW** side — out-of-state money flowing *into* each state's races, the
"non-constituent money" question from the parent paper — is answered in **Tests E–I and the
flow matrix G**, built from the recipient-anchored `fec_inflow.duckdb`. Both directions now
exist; they use different committee universes, so read shares *within* each rather than
subtracting one from the other.

**The four states are a PURPOSIVE selection, not a sample.** They were chosen to spread the
design across access and partisanship — high-access blue (WA), large blue (NY), large red (TX),
small red (ID) — so the claim throughout is about *variation in shape* across a deliberately
dissimilar set, never about a population of states from which these were drawn. No inference to
the other forty-six is offered or supported.

Donor identity is a `name + zip5` proxy. It over-merges common names, which **overstates**
concentration — the direction the donor paper's de-merging stress test establishes, where
splitting the largest merged donors into equal halves lowers the top-1% share by 6.1 to 8.3
points. (An earlier version of this sentence said "understated", contradicting the Limitations
section; the de-merging evidence settles it.) Figures are 2018–2026 federal cycles.

---

## The headline

| Metric | **WA** | **NY** | **TX** | **ID** |
|---|---:|---:|---:|---:|
| Total federal $ (resident donors) | **$646M** | **$2.07B** | **$1.94B** | **$76M** |
| Contributions | 5.59M | 9.98M | 12.56M | 0.77M |
| Distinct donors (name+zip) | 361,818 | 671,488 | 836,784 | 54,155 |
| Median gift | $25 | $25 | $25 | $25 |
| **Gini (donor $)** | 0.800 | **0.848** | 0.818 | *0.775* |
| **Top 1% of donors → share of $** | 39.3% | **47.5%** | 41.7% | *36.1%* |
| Top 10% of donors → share of $ | 72.3% | 78.7% | 74.5% | *69.2%* |
| Dollars from gifts **< $200** | 25.0% | 13.8% | 20.3% | **29.0%** |
| Dollars from gifts **≥ $5,000** | 20.0% | **34.8%** | 33.3% | 20.1% |
| Dollars from **retired** donors | 24.0% | 11.8% | 19.5% | **31.7%** |

*(Emphasis marks each row's **extreme**, not a single direction: on the concentration rows
bold is the most top-heavy and italic the least, while on the retail rows — under-$200 and
retired — bold marks the most retail, which is the least top-heavy. The dollar row bolds all
four because they are the scale of the study, not a ranking. New York holds every top-heavy
extreme; Idaho holds the retail extremes except the ≥$5,000 share, where Washington is
marginally lower and nothing is marked.)*

One line: **New York gives the most top-heavy, Idaho the most retail; Washington and
Texas sit between — and each state's money carries a distinct economic fingerprint:
Big Tech (WA), Wall Street (NY), Energy/Industrial (TX), MLM/timber (ID).**

---

## Findings

### 1. New York is the most top-heavy; Idaho the most retail
- **Defensible claim.** The top 1% of donors supply **47.5%** of New York's federal dollars
  versus **36.1%** in Idaho (Gini 0.848 vs 0.775) — with WA (39.3%) and TX (41.7%) between.
  Conversely, sub-$200 gifts are **29.0%** of Idaho's dollars and 25.0% of Washington's but
  only **13.8%** of NY's, and ≥$5,000 gifts are **34.8%** of NY's money vs ~20% of both ID
  and WA. New York's federal money is concentrated at the top; **Idaho's is the most
  broad-based of the four** on the small-gift and concentration measures, though Washington
  edges it on the ≥$5,000 share (20.0% against 20.1%), and it does so
  despite being deep-red — so in these four cases retail-vs-whale structure does not align
  monotonically with partisanship. The two
  big-dollar states (NY, TX) are the most top-heavy; the two small-population states (WA
  relative to its dollars, ID absolutely) are the most retail. **This is four purposively
  chosen states, not a sample.** It is enough to defeat the intuitive prediction that redder
  means more retail *as a general rule*, because a single deep-red state at the retail pole
  does that. It is not enough to establish that partisanship has no relationship to donor
  concentration across states, and the paper does not claim it. The competing explanation
  the four cases actually suggest — that concentration tracks the structure of a state's
  economy — is a hypothesis for a fifty-state test, not a result of this one.
- **Strongest objection.** The Gini of any voluntary-giving distribution is mechanically
  high everywhere (all four exceed 0.77), so the *level* is not itself pathological — only
  the *gap* between states is informative. Idaho's low concentration is partly a size effect:
  a $76M pool simply has fewer mega-donors to concentrate around than a $2B one. And the
  small-dollar share is sensitive to how conduit (ActBlue/WinRed) earmarks are recorded (see
  Limits) — though the gift-size *amount* cut is computed directly from the dollar value and
  is unaffected by that.
- **Why the size effect does not carry the Idaho result.** The concession above is real for the
  top-1%, top-10% and Gini measures alike — all three are rank statistics over a donor pool and
  therefore do depend on how many donors there are to rank. It does not extend to the **gift-size** cuts, which are
  ratios of dollars to dollars at a fixed threshold: the share of money arriving in gifts under
  $200, or in gifts of $5,000 and up, is computed from the amounts themselves and has no
  mechanical dependence on pool size. Idaho is the most retail on those cuts too — 29.0% under
  $200 against New York's 13.8%. So the finding survives the objection on the measure the
  objection cannot reach, which is the reason to report both kinds of cut rather than only the
  concentration statistics.

### 2. Distinct donor keys per resident are highest in Washington
- **Defensible claim.** New York and Texas raise ~3× Washington's federal dollars in
  absolute terms, but Washington carries the most **distinct donor keys per resident over the
  2018–2026 window**: **361,818** keys in a state of **7.82M** residents (**4.6%**) versus NY
  **671,488**/**19.85M** (**3.4%**), TX **836,784**/**30.19M** (**2.8%**), and ID
  **54,155**/**1.93M** (**2.8%**).
  Fewer dollars, more givers. Texas and Idaho land level with each other — small-population
  is not the same as disproportionately participatory — while WA remains the standout, **two-thirds again**
  more participatory than either (4.6% against 2.8%; the "a third again" an earlier version
  gave is the WA-to-NY comparison, not the WA-to-TX/ID one this sentence makes).
- **Read that as a ratio, not a participation rate.** *(Relabelled 2026-08-16.)* The numerator
  is donor **keys** accumulated over five cycles, not people in one; the denominator is total
  residents including children and non-citizens. So **4.6% is not "4.6% of eligible adults
  donated"** — it is higher than the per-cycle share of people and lower than the share of
  eligible adults, and the two errors do not cancel. The cross-state *ordering* is what this
  finding rests on, and it is robust because the same construction is applied to all four.
- **The denominators, stated rather than assumed.** Total resident population, ACS 2020–2024
  5-year (table B01003), pinned to `docs/reference/state_population_acs2024.csv` by
  `scripts/acs_state_population.py` — the same ACS release the series' CVAP benchmark uses.
  Earlier drafts of this section carried denominators with no source recorded; they are
  restated here on a basis that can be re-fetched and diffed.
- **Strongest objection.** The name+zip donor proxy over-merges common names unevenly across
  states; population denominators are total residents, not voting-eligible adults, so every
  rate is biased downward and by an amount that varies with each state's share of children
  and non-citizens; and WA's lower dollar total partly just reflects fewer ultra-wealthy
  households, not broader civic habit.

### 3. The retired-donor economy is largest in Idaho, then Washington
- **Defensible claim.** **31.7%** of Idaho's federal donor dollars come from donors who list
  their occupation as *retired* — the highest of the four — followed by **24.0%** in
  Washington, **19.5%** in Texas, and just **11.8%** in New York. Idaho's and Washington's
  federal money leans most heavily on people no longer in the workforce, consistent with both
  states' older donor bases; New York's Wall Street money is overwhelmingly still-earning. (A
  looser "non-working" bucket that also folds in *not-employed / none / blank* reaches ~48% in
  both ID and WA, but that figure is soft — see objection.)
- **Strongest objection.** FEC occupation/employer strings are self-reported and noisy. The
  retired-only figure is the defensible one; the broader "non-working" number bundles wealthy
  non-earners and blank/missing fields with the genuinely jobless and carries no income
  signal, so it should be read as a loose upper bound, not a measurement. Idaho's high retired
  share also partly reflects its retiree-destination demographics (Coeur d'Alene, north Idaho),
  not only a donor-composition effect.

### 4. Sector signatures: Tech (WA), Wall Street (NY), Energy/Industrial (TX), MLM/timber (ID)
- **Defensible claim.** The largest corporate employers of each state's federal donors are
  unmistakably regional:
  - **WA — Big Tech:** Microsoft ($15.2M), Amazon ($5.0M), University of Washington
    ($4.7M), Zumiez ($4.2M), Fisher Investments ($3.1M).
  - **NY — Wall Street:** Blackstone ($11.1M), Goldman Sachs ($7.9M), KPMG ($6.6M), Jane
    Street ($5.8M), Soros Fund Management ($5.4M).
  - **TX — Energy / Industrial:** BNSF Railway ($8.0M), Valero ($7.0M), Starkey Hearing
    ($5.6M), Beal Bank ($5.1M), Lockheed Martin ($4.6M).
  - **ID — MLM / timber / regional:** Melaleuca (~$2.8M across name variants — the Idaho
    Falls direct-marketing giant), Ball Ventures ($0.8M), Idaho Forest Group ($0.6M),
    University of Idaho ($0.3M). A distinct small-state signature: consumer-MLM, timber, and
    regional development capital, at one-fifth to one-tenth the dollar scale of the big three.

  The economic base that funds federal politics differs sharply by state.
- **Strongest objection.** These employer sums are dominated by a handful of mega-donors at
  each firm, not broad rank-and-file employee giving; and the strings are free-text (Texas's
  single largest "employer" is the generic *"Entrepreneur"*; Idaho's Melaleuca total is split
  across three spelling variants), so firm-level totals are indicative, not audited.

### 5. A uniform presidential rhythm
- **Defensible claim.** All four states show presidential-cycle dollars running ~2× their
  off-year totals, in lockstep (WA $202M/2020 vs $79M/2018; NY $612M vs $299M; TX $544M vs
  $266M; ID $22.5M vs $7.6M). Federal giving is paced by the national calendar, not
  state-specific dynamics — Idaho, at 1/25th the scale, keeps the identical rhythm.
- **Strongest objection.** This is mechanical (presidential races simply cost more) and says
  nothing distinctive about any state — it's a useful uniformity check, not a finding.

---

## Follow-on tests

*Computed in `scripts/cross_state_fec_tests.py`. Committee master: 44,746 committees.*

> **Two method defects were disclosed here on 2026-08-09 and both are now REPAIRED
> (2026-08-16) rather than merely disclosed.** The record is kept because the paper shipped
> for a week knowing §B ran on a construction its own abstract calls invalid.
>
> **Recipient state now comes from the candidate's OFFICE state.** Test B resolved it from
> the committee's registration address (`cmte_st`) — a Washington Senate candidate whose
> committee registers in Virginia was scored out-of-state. §G had moved to the office-state
> resolution (`diag_cross_state_money_matrix.py`, `dsgn IN ('P','A')`) and §B was left
> behind; the divergence was bounded at the time (in-state congressional dollars WA $86.6M
> against $87.0M, ID $3.66M against $3.66M, NY $208.7M against $228.1M, TX $310.7M against
> $284.8M) and disclosed as single-digit, which was true and was not a reason to publish it.
> Both sections now read the **same** resolved committee master, so the two cannot fork
> again. §B's table and one of its conclusions changed; see the note there.
>
> **The unmatched residual is now measured instead of hidden.** The block claimed "100% of
> recipient dollars matched in all four states", which could not have been otherwise: the
> destination `CASE` ended in `ELSE 'PAC/party/other'`, so a `LEFT JOIN` miss fell through to
> the largest cell and no residual could ever be non-empty. There is now an explicit
> `Unmatched committee` bucket, and it holds **$0.13M of $4.73B (0.003%)**. The old claim was
> approximately correct; the point is that nothing about the old construction could have told
> anyone that.

> **Idaho scope (2026-07-19, completed).** All tests A–I and the flow matrix G are now
> four-state. The analysis scripts were made **state-agnostic**: the region is discovered by
> globbing `data/*_statewide.duckdb` (overridable with `CROSS_STATE_REGION`) via the shared
> `scripts/cross_state_common.py`, so adding a state needs no script edits — load its data and
> re-run. ID's federal money is small ($76M outflow, $11.5M inflow, vs $0.6–2.1B and $155–582M
> for the big three), so it doesn't move the *qualitative* conclusions, but it sharpens the
> poles (most retail, most retired, most nationalized) and its Senate money is the most
> out-of-state of the four (85.8%).

### A. Is the money concentrating over time?

Top-1% donor dollar share, by cycle:

| Cycle | WA | NY | TX | ID |
|---|---:|---:|---:|---:|
| 2018 | 28.2% | 35.3% | 29.2% | 30.9% |
| 2020 | 34.5% | 42.4% | 35.6% | 34.4% |
| 2022 | 30.3% | 36.8% | 34.9% | 31.0% |
| 2024 | 36.2% | **47.4%** | 41.9% | *30.0%* |
| 2026* | 30.6% | 40.3% | 37.9% | 31.1% |

- **Defensible claim.** Concentration follows a **presidential sawtooth** (peaks in 2020 and
  2024) with a **mild secular upward drift** — in three of the four states. Comparing like
  cycles: top-1% share rose presidential-to-presidential in WA/NY/TX (2020→2024: WA +1.7, NY
  +5.0, TX +6.3 pts) and midterm-to-midterm (2018→2022: TX +5.7, NY +1.4, WA +2.1). New York is the most concentrated;
  **Texas is rising fastest**, on both of the comparisons this sentence supplies (+6.3 against
  NY's +5.0 presidential-to-presidential, +5.7 against +1.4 midterm-to-midterm). An earlier
  version credited New York with both. **Idaho is the exception that sharpens the
  rule:** it is the *flattest* of the four and its top-1% share actually *fell* into 2024
  (34.4%→30.0%) rather than spiking — its money base has no whale layer thickening at the top.
  So the secular concentration is a big-money-state phenomenon; the small retail state doesn't
  show it.
- **Strongest objection.** Only three presidential and two-to-three midterm points — too few
  to call a secular trend confidently. The 2024 spike is entangled with record presidential
  joint-fundraising activity (see Test B), so "concentrating" is partly a cycle-composition
  artifact, not purely a structural shift. Direction = mildly rising, not a clean climb.
  Idaho's flatness is also partly a small-n effect (fewer donors → noisier per-cycle top-1%).
  *(2026 is partial-cycle.)*

### B. Where does each state's money go?

Destination of residents' federal dollars. Recipient state is the connected candidate's
**office state**, resolved committee → candidate → `cn.txt CAND_OFFICE_ST` and restricted to
**authorized** committees (`dsgn IN ('P','A')`) — the same construction §G uses:

| Destination | WA | NY | TX | ID |
|---|---:|---:|---:|---:|
| **In-state Congress** | 13.5% | 11.0% | 14.7% | *4.8%* |
| Out-of-state Congress | 17.3% | 21.5% | 12.4% | 17.6% |
| Presidential (authorized committee) | 2.5% | 1.9% | 2.0% | 1.2% |
| PAC / party / JFC / other | 66.7% | 65.5% | 70.9% | **76.5%** |
| *Unmatched committee* | *0.01%* | *0.00%* | *0.00%* | *0.00%* |

> **REBUILT 2026-08-16, and the previous version of this table should not be cited.** It
> resolved recipient state from the committee's own **registration address** (`cmte_st`) —
> the construction this paper's abstract calls invalid, and for the reason it gives: a
> Washington Senate candidate whose committee registers in Virginia was scored out-of-state.
> §G moved to the office-state resolution and §B was simply left behind. It also inferred
> office from the candidate-id prefix rather than from `cn.txt`, and applied no `dsgn`
> restriction, so leadership PACs and joint-fundraising committees — one connected candidate,
> raising nationally — were attributed to that candidate's state.
>
> **The retired "100% of recipient dollars matched" claim is replaced by a measurement.** The
> old `CASE` ended in `ELSE 'PAC/party/other'`, so an unmatched committee fell silently into
> the largest cell; the statement was therefore true of any input and informative about none.
> Measured now: **$0.13M of $4.73B, 0.003%**, across ten committee ids in three states. The
> old claim was approximately right and entirely unfalsifiable, which are different things.
>
> **Two rows moved a lot, and the reason is the `dsgn` restriction, not the state fix.**
> Presidential falls from 6.5–11.0% to 1.2–2.5% and PAC/party/JFC rises correspondingly,
> because "Presidential" now means the authorized presidential campaign committee only.
> Presidential JFC money — which funds the nominee *and* the party, and which the caveat below
> always flagged as blurred — now sits in the residual bucket where its ambiguity is visible
> rather than resolved by assumption.

- **Defensible claim.** Residents fund **their own congressional delegation least of all** —
  11–15% of their federal dollars in WA/NY/TX, and a startling **4.8% in Idaho** — while
  roughly two-thirds to three-quarters (**65.5–76.5%**) flows to **national party committees
  and joint-fundraising vehicles.** Washington's single largest federal destination is the
  Democratic presidential JFC (~$61M), about **70%** of *all* in-state congressional giving
  combined (~$87M); other top destinations are the DNC, DCCC, DSCC, RNC, and the Trump JFCs.
  **Idaho is the extreme of nationalization:** its in/out-of-state Congress ratio is **0.27**
  — it sends **3.7×** more to other states' congressional races than to its own delegation —
  and 76.5% goes to national vehicles: a safe, small state with few competitive home races
  gives almost entirely to the national contest. This is the **donor-side counterpart to the
  nationalization-of-money literature**: even constituents' own money is overwhelmingly aimed
  at national politics rather than at their own representatives.
- **One finding reversed on the corrected construction, and it is the interesting one.**
  Under the old committee-registration resolution every state sent more to out-of-state
  congressional races than to its own delegation. On office state, **Texas does not**: its
  in/out ratio is **1.18**, so Texans give *more* to their own delegation than to everyone
  else's. Washington sits at **0.78**, New York **0.51**, Idaho **0.27**. The ordering — TX
  most local, then WA, NY, ID least — is unchanged; the *sign* for Texas is not. Any earlier
  statement that residents everywhere give more out-of-state than in-state is withdrawn.
- **Strongest objection / caveat.** This remains **outflow** (where residents *send* money),
  not money flowing *into* each state's races. The dominant PAC/party/JFC bucket is genuine
  national money, but its internal splits are soft, and JFCs in particular fund a nominee and
  a party at once. The in- vs. out-of-state *Congress* split is the robust part — direct
  gifts to authorized candidate committees, resolved by office state.

### C. Top donors, top recipients, and the cross-state magnets

*Computed in `scripts/diag_cross_state_donors.py`.*

**Largest individual donors** confirm the sector fingerprint at the person level:
- **WA (tech/VC):** the Cornfields (~$3.3M), Tom Campion/Zumiez ($3.2M), Nick Hanauer (VC),
  Rory & Melinda Gates.
- **NY (finance/philanthropy):** Philip Munger ($4.1M), George Soros ($4.0M), Stephen
  Schwarzman/Blackstone ($3.2M), Agnes Gund/MoMA.
- **TX (energy/industrial):** Syed Anwar/PetroPlex ($5.2M), Paul Foster/Western Refining
  ($3.5M), the Perots, Woody Hunt.
- **ID (MLM/one-family dominance):** the **VanderSloot family** (Frank L. & Belinda,
  Melaleuca founder) supply ~$4M+ across name/zip variants — the single dominant force in
  Idaho's federal giving — followed by the **Ball family** (Allen/Connie, Ball Group) and
  William Parks. Idaho's top-donor list is more concentrated in one household than any of the
  big three, the individual-level counterpart to its small, safe donor economy.

**Largest recipient committees** are national vehicles, with marquee in-state contests
poking through: D-state dollars concentrate in the **Harris Victory Fund** (WA $61M, NY
$176M) and **Fight for the People PAC** (NY $82M); TX dollars in **Trump Victory** ($71M) and
the **RNC** ($67M). In-state contests that surface: Kim Schrier (WA-08, $17M), Patty Murray,
Ted Cruz (TX, $35M).

**Cross-state money magnets.** Of 12,361 committees these donors touch, **4,894 are funded by
donors in ≥3 of the four states.** The top are national party / JFC vehicles (Harris Victory
Fund $292M combined; Fight for the People PAC $171M; RNC $115M; Trump Victory $109M; DSCC / DNC
/ DCCC ~$97–100M each). The single cleanest nationalization signal: **Warnock for Georgia** — a
*Georgia* Senate race drawing **WA $7.4M + NY $16.3M + TX $6.0M + ID $0.3M**, funded by four
states whose residents cannot vote in it. Idaho appears on essentially every magnet at small
scale, and — unlike the D-heavy WA/NY or R-heavy TX top lists — its own top recipients split
cleanly both ways (Idaho State Democratic Party $4.3M *and* RNC $3.6M / Trump JFC $3.0M).

- **Caveat.** Individual-donor identity is a name+zip proxy (merges across cycles; a few
  employer labels are data-entry quirks). Recipient totals are donor-residence *outflow from
  these four states only* — not the committee's full national haul.

### D. Does money chase competitive races? (money × competitiveness)

*Computed in `scripts/diag_money_vs_competitiveness.py`, joining residents' U.S. House
contributions to the competitiveness band of **the cycle each contribution was made in**
(Tossup <5 / Lean 5–10 / Likely 10–20 / Solid ≥20, on the observed two-party margin for 2022
and 2024 and the locked forecast for 2026). **Full four-state run:** WA/NY/TX/ID donors
→ WA/NY/TX/ID House districts, 2022–2026 (post-redistricting), **210 district-cycles /
$288.2M**.*

| Band | # district-cycles | % of d-c | $ to band | $ / district-cycle | % of $ | cross-state $ |
|---|--:|--:|--:|--:|--:|--:|
| Tossup (<5) | 15 | 7.1% | $52.2M | **$3.48M** | 18.1% | $3.6M |
| Lean (5–10) | 13 | 6.2% | $35.5M | **$2.73M** | 12.3% | $2.2M |
| Likely (10–20) | 47 | 22.3% | $55.8M | $1.19M | 19.4% | $4.5M |
| Solid (≥20) | 136 | 64.5% | $144.7M | **$1.06M** | 50.2% | $10.4M |

<sub>A further **$9.8M (3.3%)** falls outside these bands — district-cycles with no
major-party choice or no published canvass — and is reported rather than absorbed into Solid.
Same treatment as §E.</sub>

- **Defensible claim.** Donor money chases competitiveness, and on the cycle-specific basis it
  does so **more sharply than the retired 2026-label run suggested**: Tossup district-cycles
  pull **$3.48M** each and Lean **$2.73M**, against **$1.06M** in Solid — a **3.3×**
  Tossup-vs-Solid premium, and **2.9×** comparing competitive to safe as blocks, where the
  retired basis reported ~2.1×. Yet **69.6% of all dollars still flow to safe (Likely + Solid)
  district-cycles**, because **86.7%** of district-cycles are safe. In-state House money is
  still dominated by support for (mostly safe-seat) candidates rather than strategic targeting
  of the marginal race — the donor-side echo of "money follows the scoreboard."
  **Cross-state House giving is small ($20.8M of $288.2M, 7.2%)**: residents overwhelmingly
  fund their *own* state's House candidates. Idaho contributes only to the safe bands,
  reinforcing that safe-state in-district money is a safe-seat phenomenon.
- **Caveats.** Donor-side *outflow*, not inflow (Section E is the inflow counterpart).
  Strategic targeting shows up more in PAC/JFC and out-of-state money (Test B's large
  national-vehicle bucket + the inflow side) than in this in-state-resident slice.
- **Basis note, 2026-08-16.** This table previously banded all 2022–2026 money by the project's
  **2026** forecast, which answers "did districts forecast competitive in 2026 receive more
  money?" rather than the question in the heading. It also keyed on the district rather than
  the district-cycle, pooling three cycles of money into one row. Both are corrected; the
  premium rose rather than fell, because the 2026 labels were miscounting districts that were
  genuinely competitive in 2022 or 2024 as safe.

### E. Inflow side — does money chase competitive races? (WA+NY+TX+ID House & Senate)

*From the recipient-anchored inflow dataset (`fec_inflow.duckdb`: **5.50M contributions /
$1.21B**, all-state donors → WA/NY/TX/ID federal candidates — ID added 2026-07-19 — built by
`scripts/load_fec_inflow_bulk.py` in minutes; the API path would have taken days), joined to
competitiveness. `scripts/diag_inflow_vs_competitiveness.py`, now four-state.*

**U.S. House, 2022–2026 — $470.7M across 210 district-cycles.** Each contribution is banded
by **its own cycle's** competitiveness: the observed two-party margin for 2022 and 2024, the
locked pre-election forecast for 2026. The unit is the district-*cycle*, so a district
appearing in all three windows contributes three observations:

| Band | # district-cycles | % of d-c | $ in | $ / district-cycle | % of $ | out-of-state share |
|---|--:|--:|--:|--:|--:|--:|
| Tossup (<5) | 15 | 7.1% | $83.3M | **$5.55M** | 17.7% | 40.8% |
| Lean (5–10) | 13 | 6.2% | $51.7M | **$3.97M** | 11.0% | 34.6% |
| Likely (10–20) | 47 | 22.3% | $89.4M | $1.90M | 19.0% | 41.2% |
| Solid (≥20) | 135 | 64.5% | $246.4M | $1.83M | 52.3% | 43.6% |

<sub>A further **$17.3M (3.6%)** of House inflow falls outside these bands and is excluded
from the table rather than absorbed into it: district-cycles whose general offered no
major-party choice (a same-party general has no two-party margin — Washington's top-two
produces them routinely), and those with no published canvass (Texas publishes no precinct
returns for uncontested races). Reported because a silent residual reads as coverage it does
not have. *(It was $18.4M / 3.8% until 2026-08-16, when Idaho's two 2022 district-cycles moved
out of it — their margins are now resolved from the Secretary of State's canvass rather than
left blank in the pin. Both are Solid.)*</sub>

> **REBUILT 2026-08-16, and the headline moved. Do not cite the previous table.** Every cycle's
> money used to be banded by the project's **2026** forecast. That answers "did districts
> *forecast* competitive in 2026 receive more money across 2022–2026?" — a different question
> from the one this section asks, and a worse one, because a district can be safe in 2022,
> close in 2024 and safe again in 2026. The retired table also treated the district as the
> unit, which pools three cycles of money into one row and makes "$ per district" a quantity
> no race ever experienced.
>
> The correction **strengthens** the finding rather than dissolving it, which is worth saying
> because the round that made it expected the opposite: the competitiveness premium rises from
> the retired **~2×** to **2.6×**. The 2026 labels were attenuating it — districts that were
> genuinely competitive in 2022 or 2024 and are safe now were being counted as safe.

- **Defensible claims:**
  1. **The competitiveness premium is real and ~2.6×.** Tossup ($5.55M per district-cycle) and
     Lean ($3.97M) pull about two and a half times the inflow of a safe district-cycle
     (~$1.83–1.90M) — money *does* chase the marginal race, and more sharply than the
     donor-side figure in Section D.

     **It is not driven by one cycle, and the cycles are not equal.** Computed within each
     cycle separately: **2.66×** in 2022, **3.28×** in 2024, **1.46×** in 2026. The direction
     holds in all three, which is the robustness point. But 2026 is much the weakest, and 2026
     is the one cycle banded on a **forecast** rather than an outcome, and the only one whose
     money is still accruing. On the two **observed** cycles alone the premium is **2.94×**.
     The pooled 2.6× is therefore a conservative figure, and the honest reading is that a
     forecast band is a weaker instrument than a result — which is the same lesson the rebuild
     of this section taught in the first place.

     ⚠ **Read the premium as a description, not an estimate.** The unit is the district-cycle,
     so a district appearing in all three windows contributes three observations that are
     plainly not independent of one another — the same seat, largely the same donors, often the
     same incumbent. That is fine for the ratio of totals reported here, which is an accounting
     statement about where money went. It does **not** support a standard error, a significance
     claim, or any language about the premium being "estimated"; none is offered.
  2. **But safe seats still capture 71.3% of the money** (Likely+Solid), because they are
     **86.7%** of district-cycles. Likely and Solid draw almost exactly the same per
     district-cycle (**$1.90M** against **$1.83M**): once a seat is safe, *how* safe barely
     changes the money — the jump is **between** competitive and safe, not within safe. This
     is the claim the rebuild left most intact.
  3. **34.6–43.6% of all inflow is out-of-state, and the range is narrow across every band.**
     Nationalization is **pervasive, not battleground-specific** — roughly two-fifths of the
     money funding these House races comes from people who cannot vote in them, in safe and
     tossup seats alike. Notably the *safest* band is at the top of that range, not the bottom.

**U.S. Senate, 2018–2026** (the model does not forecast US Senate; competitiveness via actual results):

| State | $ in | out-of-state share | Senate races in window |
|---|--:|--:|---|
| **TX** | **$253.2M** | 45.3% | competitive — Cruz/O'Rourke 2018 (R+2.6), Cruz/Allred 2024 (R+8.8) |
| NY | $55.2M | 53.5% | safe-D — Schumer / Gillibrand |
| WA | $45.0M | 41.1% | safe-D — Murray / Cantwell |
| **ID** | $6.6M | **85.8%** | safe-R — Crapo / Risch |

- **Senate echoes the House, louder — descriptively.** Competitive **TX** Senate races drew
  **$253M — ~5× safe NY ($55M) or WA ($45M)**. *(Wording narrowed 2026-08-16: this bullet used
  to conclude "competition is the single biggest money magnet", which the comparison cannot
  support. Texas differs from New York and Washington in population, incumbency, candidate
  profile, national salience and the number of contested Senate cycles in the window, all at
  once. What the four states show is that the competitive Senate contests here drew
  dramatically more than the safe ones — a large descriptive gap with several candidate
  explanations, not an isolated effect of competition.)* Yet out-of-state share is high
  *everywhere* (41–53% across WA, TX and NY; Idaho,
  below, is higher still) and among those three is actually **highest in safe NY (53.5%)** —
  national donors fund high-profile safe senators (Schumer/Gillibrand) as
  readily as battlegrounds. Same lesson as the House: competition lifts the total, but the
  out-of-state flood is profile-driven and pervasive.
- **Idaho extends the pattern to the bottom of the size distribution — most sharply of all.**
  ID's federal candidates drew **$11.5M** total inflow (House $4.9M, all in the safe bands;
  Senate $6.6M) — ~1/20th of Texas — yet its **Senate money is 85.8% out-of-state, the highest
  of the four** (WA 41%, TX 45%, NY 53%), and its House inflow lands only in Likely/Solid (no ID
  tossup exists). A small, safe, deep-red state's candidate money is *overwhelmingly*
  non-constituent. The natural reading is that profile and incumbency pull national money
  regardless of competition — Crapo and Risch are safe, so almost none of their money needs to
  come from Idahoans — but that is an **interpretation of one state's share, not an identified
  mechanism**: Idaho's small donor base alone would push its out-of-state share up even if
  national donors behaved identically everywhere. What the number establishes is the
  descriptive fact, which is striking on its own: nationalization is most extreme, not least,
  at the safe bottom of the size distribution.

- **Earmarks ARE attributed (verified — correcting an earlier caveat).** Conduit-routed
  (ActBlue/WinRed) money is **not** lost from these totals: FEC records each earmarked
  individual gift under the *candidate* committee as transaction type `15E` — **$194M for these
  candidates in 2024 alone, more than the $90M of direct `15` gifts** — and the inflow load
  captures it. The conduit-side `24T` records ($150M) are the *same money* seen from the conduit
  and are correctly excluded to avoid double-counting (`scripts/diag_earmark_inspect.py`).

- **Caveats.** House competitiveness is banded **per cycle on its own basis** — observed
  two-party results for 2022 and 2024, the locked 2026 forecast for 2026 — with the
  district-cycle as the unit; Senate is banded by actual two-party result throughout. The 2026
  cycle is therefore the only one resting on a forecast, and its premium is the weakest of the
  three, as the bullet above states. WA contributes no congressional Tossups in the 2026 map
  (its competitive seats land in Lean/Likely). State-legislative money is excluded here — it
  moved to `cross-state-state-money-note.md` on 2026-08-16 — so this paper is federal only.
  *(This caveat read "House competitiveness = 2026 forecast bands on current districts" until
  2026-08-17, describing the table the 2026-08-16 rebuild retired.)*

### F. The individual layer — moved to the donor-class companion

*Person-level representativeness, the donor-vs-electorate age and party skew, and the
giving→turnout relation are analysed in
[`donor-class-and-the-electorate.md`](donor-class-and-the-electorate.md), which maintains
**separate federal and state panels** and is the paper those claims belong to.*

*This section is REMOVED as of 2026-08-16 rather than revised, and the reason is a design
contradiction it could not resolve in place.* This paper's substantive basis is federal
individual contributions, but §F began from the **pooled** WA voter↔donor match — FEC money
and PDC money in one donor total — which inflates measured concentration, as the section
itself said before presenting pooled figures anyway. It then carried a second contradiction:
its preamble stated that every figure below had been recomputed on the full-first-name
specification, while §F4 stated that the pooled F1–F3 figures were the all-tier match at
93.0% precision. Both cannot be true. Maintaining a person-level layer on a third panel
specification, inside a paper whose other nineteen sections are federal aggregate money, is
a standing source of drift for no analytic gain the companion does not already deliver.

*Nothing is lost.* The donor paper reports WA as two panels — federal **147,745** donors /
**$346.3M** / top-1% **41.2%** / Gini **0.815**; state (PDC) **217,114** / **$122.5M** /
**43.5%** / **0.821** — and those supersede any pooled figure for a donor-level claim.

### G. The cross-state money-flow matrix — the "Warnock" picture, made systematic

*Computed in `scripts/diag_cross_state_money_matrix.py`. INFLOW from
`data/fec_inflow.duckdb` (recipient-anchored, robust). OUTFLOW and the magnet list from the
per-state `individual_contributions` joined to a committee→candidate master rebuilt from
cached `cm*.zip`+`cn*.zip`. Recipient state = the candidate's **office state** (`cn.txt
CAND_OFFICE_ST`), resolved committee→candidate — **not** the committee's registration state
(`CMTE_ST`), which is often a DC/VA compliance-vendor address (Smiley-WA and Cornyn-TX both
register in VA). Outflow and magnets are restricted to **authorized candidate committees**
(designation P/A), so JFCs and leadership PACs — which carry one connected candidate but raise
nationally — don't misattribute a recipient state. U.S. House+Senate; all cycles 2018–2026.*

**INFLOW — who funds each state's H+S candidates (by donor origin):**

| Recipient state | Total $ | In-state | In-region (other 3) | Rest-of-US |
|---|--:|--:|--:|--:|
| **WA** | $154.6M | 66.7% | 6.6% | 26.7% |
| **NY** | $462.7M | 55.1% | 3.9% | 41.0% |
| **TX** | $582.4M | 59.6% | 6.1% | 34.2% |
| **ID** | $11.5M | *31.9%* | **14.8%** | **53.3%** |

**OUTFLOW — where each state's residents send their H+S candidate money (by recipient region):**

| Donor state | Total $ | In-state | In-region (other 3) | Rest-of-US |
|---|--:|--:|--:|--:|
| **WA** | $198.6M | 43.8% | 5.4% | 50.8% |
| **NY** | $672.5M | 33.9% | 4.1% | 62.0% |
| **TX** | $526.4M | 54.1% | 2.6% | 43.3% |
| **ID** | $17.1M | *21.4%* | 10.6% | **68.0%** |

- **Defensible claims.**
  1. **Every one of these states sends the *majority* (or near it) of its candidate money out
     of region.** NY residents ship **62%** of their House+Senate candidate dollars to
     candidates in other states; **Idaho ships the most of all — 68%**; even Texas, the most
     parochial, sends **43%**. This is the donor-side engine of nationalization, measured
     directly rather than inferred.
  2. **Idaho is the only net money-*importer* for its own candidates.** ID candidates raise
     just **31.9%** of their money in-state (vs 55–67% for the big three) and **53.3% from the
     rest of the US** — the highest external dependence of the four. But ID residents also send
     **68% of their money out** ($17.1M out vs $11.5M in): a small, safe, deep-red state whose
     handful of federal races draw national R money while its own donors chase the national
     contest. **In-region cross-funding stays negligible** — the four states barely fund *each
     other* (≤6–7% of any big-state cell; ID's 14.8% in-region inflow is just $1.7M of tiny
     absolute dollars). NY sends the largest absolute sum out of region
     (~$417M of its $672.5M). **No net-flow claim is made here**: the inflow and outflow
     matrices use different committee universes, so the difference between them is not a
     quantity this design produces — see the caveat below. An earlier version called WA and
     ID "net importers relative to their own giving", which is both a cross-matrix
     subtraction the caveat rules out and, on these tables, backwards: WA shows $198.6M out
     against $154.6M in, and ID $17.1M against $11.5M.
  3. **The magnet list is a clean battleground map — and Idaho rides along.** The out-of-region
     candidate committees funded broadly across the region are almost entirely Senate
     battlegrounds: **Warnock-GA ($30.0M, incl. ID $0.33M), Kelly-AZ ($19.9M, ID $0.42M),
     Ossoff-GA ($19.5M), Tester-MT ($13.2M, ID $0.40M), Harrison-SC ($11.8M)**, with Graham-SC,
     Perdue/Loeffler-GA, Gideon-ME, Rosen/Cortez Masto-NV and McConnell-KY close behind.
     **Georgia Senate races alone (Warnock + Ossoff + Perdue + Loeffler) drew ~$68M** from
     residents of the four states — none of whom can vote in Georgia. Idaho's contributions are
     small ($0.1–0.4M per race) but present across the same marquee list, and they **split both
     ways** — ID money shows up on the Democratic magnets (Warnock/Kelly/Ossoff/Tester) *and*
     the Republican ones (Graham, Perdue, Loeffler, McConnell). Idaho is the most *balanced*
     two-way giver, not the only one: Section C records **TX $6.0M to Warnock**, twenty times
     Idaho's $0.33M on the same race, and Texas necessarily funds the Republican magnets
     too. An earlier version said "the only state here whose out-of-region giving visibly
     funds both parties' Senate battlegrounds", which its own Section C contradicts. The Section-C
     Warnock anecdote is the rule, not the exception.
- **Strongest objection / caveat.** The two matrices use different committee universes (inflow
  is the recipient-anchored bulk; outflow is per-state authorized committees), so their absolute
  totals are **not** directly subtractable — read the *shares within each*, not the cross-matrix
  difference. "Rest-of-US" inflow is robust (blank donor-state is 0.08% of inflow dollars).
  Out-of-region ≠ "non-constituent and therefore illegitimate": a donor may have ties, and party
  committees (excluded here) carry yet more of the nationalized money.

### H. Sector × competitiveness — does Wall Street chase Tossups while tech/energy fund safe seats?

*Computed in `scripts/diag_sector_vs_competitiveness.py`, crossing the employer/sector
signatures (Sections A/C) against the inflow competitiveness bands (Section E). Each inflow
contribution to a WA/NY/TX/ID U.S. House district (2022–2026, $470.7M) is classified by a
keyword-on-employer sector and joined to the band of **the cycle it was made in** (Tossup<5 /
Lean5–10 / Likely10–20 / Solid≥20). "Competitive share" = (Tossup+Lean) ÷ sector total.*

| Sector | $ (House, 4 states) | Competitive share | Out-of-state share |
|---|--:|--:|--:|
| Law | $17.3M | **31.2%** | 32.9% |
| Real estate | $7.8M | 30.4% | 31.9% |
| Academia / public | $7.9M | 30.3% | 47.8% |
| Healthcare | $8.1M | 29.7% | 35.9% |
| **Finance / Wall St** | $18.0M | 28.2% | 44.1% |
| **Tech** | $6.8M | **26.9%** | 52.8% |
| **Energy** | $3.3M | **18.4%** | 27.3% |
| *[all sectors baseline]* | $470.7M | *28.7%* | *~43%* |

<sub>Sector keyword map extended after a coverage audit (`scripts/diag_sector_coverage.py`)
surfaced major law firms, hedge funds, and tech names as unclassified; the additions lifted
classified dollars from ~14% to ~15% and left the pattern below intact.</sub>

- **Defensible claim, and it is now mostly a NULL.** On the cycle-specific basis the section's
  own hypothesis is **not borne out.** Finance sits essentially *at* the baseline (**28.2%**
  against **28.7%**) rather than tilting toward competition, and tech — previously the
  headline "least competition-seeking sector" — is also near it at **26.9%**. Five of the seven
  classified sectors fall within about two points of the baseline in either direction. Whatever
  sorts these sectors, it is not a preference for marginal races.
  - **The one survivor is energy, at 18.4%**, roughly ten points below the baseline and the
    only sector clearly outside the pack. It is also the most *local* money in the set
    (**27.3%** out-of-state against ~43% baseline): it funds its own state's incumbents.
  - **The travel result survives, and unlike the competitive-share result it was TESTED rather
    than asserted.** Tech money travels farthest (**52.8%** out-of-state) while landing in
    ordinary bands, and energy travels least (**27.3%**). Sector differences in this data are
    about *distance*, not about *competitiveness*.

    The test is that the two columns respond very differently to the basis change. Moving from
    the retired 2026-label bands to cycle-specific ones shifted every sector's **out-of-state**
    share by **at most 0.7 points** (tech 52.2→52.8, energy 26.6→27.3, finance 44.4→44.1, law
    33.3→32.9, real estate 32.1→31.9, academia 48.3→47.8, healthcare 35.6→35.9), while the
    **competitive-share** column moved by as much as **15.2 points** (tech 11.7→26.9, law
    20.0→31.2, finance 21.6→28.2). The travel figures are near-invariant to the banding because
    they barely depend on it; the competitiveness figures were largely produced by it. That
    asymmetry is the reason to keep one finding and withdraw the other, and it is measured,
    not argued.
- **Strongest objection — and it now cuts the other way.** The previous version of this bullet
  argued the effect was "modest and partly mechanical", noting the competitive-share spread was
  only ~10 points. On the corrected basis the spread is ~13 points but almost all of it is one
  sector (energy), and the mechanical explanation is *stronger*: tech (WA) and energy (TX)
  concentrate in home states whose own House seats are largely safe, so what remains of the
  pattern is plausibly "their in-state seats are safe" rather than any strategic preference.
- **Basis note, 2026-08-16.** The retired version banded 2022–2026 money by the **2026**
  forecast, and its headline numbers should not be cited: finance 21.6%, tech 11.7%, energy
  14.1% against an 18.4% baseline. Both the levels and the *ordering* changed. This is the
  section the rebuild damaged most, and that is the honest outcome — a finding that dissolves
  when each cycle is scored against its own competitiveness was an artifact of the labels.
- **Caveat.** Even after extending the keyword map with the biggest missing law firms, hedge
  funds, and tech names (`scripts/diag_sector_coverage.py`), classified sectors are still a
  **thin slice — only ~15% of inflow dollars**; "retired / not-employed / blank" is 46.7% and
  "unclassified" 38.7%, and tech ($6.8M) and energy ($3.3M) volumes in these four states' House
  races are small enough to be noisy. Employer strings are self-reported free text; the keyword
  map is indicative, not audited. House-only (Senate competitiveness isn't model-forecast).

### I. Inflow concentration trend + donor retention — is the candidate-money base democratizing?

*Computed in `scripts/diag_inflow_concentration_retention.py` on the inflow side (all-state
donors → WA/NY/TX/ID H+S candidates; donor = name+zip5 proxy). Section A measured concentration
on the **outflow**; this measures it on the **inflow**, and adds repeat-vs-one-time retention.
State-agnostic: it simply reflects whatever states are in `fec_inflow.duckdb` (ID folded in
2026-07-19 — its ~$12M barely moves these all-state figures).*

| Cycle | Inflow $ | Donors | Top-1% $ | Top-10% $ | Gini |
|---|--:|--:|--:|--:|--:|
| 2018 | $254M | 246K | 16.2% | 52.4% | 0.651 |
| 2020 | $251M | 226K | 17.2% | 54.2% | 0.672 |
| 2022 | $250M | 219K | 15.8% | 55.8% | 0.688 |
| 2024 | $285M | 311K | 18.4% | 58.5% | 0.690 |
| 2026* | $170M | 168K | 16.5% | 58.2% | 0.686 |

- **Defensible claim 1 — candidate-directed money is *less* concentrated than the total
  flow, though by less than an earlier version of this bullet said.** The comparison has to be
  made on one basis, and it was not. The per-cycle inflow figures in the table above rank
  donors **within each cycle**; the outflow figures they were set against are **pooled across
  all cycles**, which stacks repeat large donors and raises concentration. Pooled on the same
  key, inflow gives **top-1% 23.4%, top-10% 62.1%, Gini 0.726** over 887,201 donor keys —
  against outflow's **36.1–47.5%** and Gini **0.775–0.848** (the headline table; an earlier
  version quoted "39–48%" and "0.80–0.85", which drop Idaho at both ends). So the gap is
  roughly **1.5× to 2.0×**, not the 2.1–2.6× the mismatched bases implied. *(Basis of the pooled
  figures, which is **not** the basis of the per-cycle table above them: the pooled cut ranks
  every donor key in `fec_inflow.duckdb` across all cycles at once, over **all recipient
  offices** and positive amounts, keyed on `UPPER(TRIM(contributor_name))` + `LEFT(zip,5)` — a
  key that is NULL where the zip is, so those rows collapse into a single bucket, which is the
  `+1` in 887,201. The per-cycle table restricts to House and Senate recipients and keeps a
  blank zip as an empty string; on that basis the pooled equivalents are 888,230 keys and
  top-1% 23.3%. Both are correct on their own basis; the two must not be quoted under one
  name. Derived by `inflow_pooled_concentration()` in `scripts/verify_cross_state_money.py`,
  which asserts all four values.)*

  A second confound is not removed by fixing the basis and is disclosed rather than adjusted:
  the inflow pool is **all-state** (887K keys) while each outflow pool is one state's
  residents (54K–837K). A larger and more heterogeneous donor pool mechanically lowers a
  top-1% share, so some of the remaining gap is pool size rather than the contribution cap.
  The direction of the finding survives both corrections — candidate-directed money really is
  less concentrated — but its attribution to the per-election cap is **not identified** by
  this comparison. The system's dollar concentration does sit disproportionately in the
  **party/JFC layer** rather than in direct candidate giving. There is a **mild secular rise even within
  candidate money** (Gini 0.651→0.690, top-10% 52→59% across 2018→2024), but no presidential
  sawtooth — concentration here drifts up gently and plateaus.
- **Defensible claim 2 — a churning, mostly one-time base funds the candidates, but a persistent
  minority supplies most of the dollars.** Across 2018–2026, **78.2% of donors give in only one
  cycle** (supplying **41.6%** of dollars); the **21.8%** who give in ≥2 cycles supply **58.4%**.
  And cycle-over-cycle retention is **low and flat — ~21–25%** of a cycle's donors gave in the
  immediately prior cycle (2020 23.4%, 2022 25.0%, 2024 21.2%), with **no rising trend.** Roughly
  three-quarters of each cycle's candidate donors are new-or-returned-from-the-past, not a stable
  subscription base. The "small-dollar democratization" picture — broad, churning participation —
  holds by *headcount*; the "thin layer over a concentrated core" picture holds by *dollars*.
- **Strongest objection / caveat.** The naive "returning %" *looks* like it rises (23→39%), but
  that is a **look-back-window artifact** — later cycles have more prior cycles to match against;
  the fixed one-cycle look-back (above) removes it and shows flatness. The name+zip5 donor proxy
  **over-merges** common names, which inflates "repeat" and deflates one-time counts, so true
  churn is, if anything, *higher* than reported. **2026 is a partial cycle** (its elevated
  retention reflects early givers skewing toward committed repeat donors before the late
  small-dollar surge). Capped candidate giving ≠ the whole money system — the uncapped layer
  (Section A) is where concentration concentrates.

### J. Which side of a safe seat gets the money? (longshot vs favored)

*New cut in `scripts/diag_loser_side_money.py`; WA/NY/TX/ID U.S. House inflow 2022–2026,
recipient party from the committee→party map (97.9–100% of dollars resolvable per state).
**Band and favored side both come from the cycle each contribution was made in** (2026-08-16):
the observed two-party margin for 2022 and 2024, the locked forecast for 2026. The script is
state-agnostic via `cross_state_common.py`.*

A safe seat for one party is a longshot for the other, so we can ask which side the money
actually reaches. Almost all of it goes to the favored side, and the safer the seat, the
more lopsided the split. In New York the longshot party's share of House inflow falls from
**40.3%** in Likely seats to just **5.6%** in Solid (≥20-point) seats; Texas runs the same
staircase from the other side (**19.7%** Likely → **5.6%** Solid, on $159.9M), and Washington
matches (**15.6%** Likely → **10.4%** Solid). Put plainly: in a truly safe district the
disadvantaged party's candidate raises around a nickel to a dime on the dollar and the
favored side takes the rest.

*(Caveats: this is money entering the race, House only; leadership PACs tied to safe
incumbents can pad the favored side; **"favored" is only meaningful once a seat is actually
safe** — in a real tossup the challenger routinely out-raises the nominal favorite, which is
why the Tossup and Lean rows sit near or above 50% and should not be read as a staircase
step; and Idaho's districts carry too little money — $2.8M total — to read.)*

*Basis note, 2026-08-16.* This section previously took **both** the band and the favored side
from the **2026** forecast and applied them to 2022–2026 money. That is a sharper error here
than in §D or §E: a district whose 2026 forecast favours the opposite party from its 2024
result would have had its 2024 dollars scored against the wrong side, so "longshot money" was
not merely mis-banded but potentially mis-signed. The staircase survives on the corrected
basis and the safe-seat conclusion is unchanged; the specific percentages moved, and the
previously printed Tossup figures (NY 74%, TX 57.3%) should not be cited.

### K. State-level money — moved to its own research note

*The first cut over the state-disclosure layer — WA PDC, NY BOE, TX TEC, ID Sunshine —
now lives in [`cross-state-state-money-note.md`](cross-state-state-money-note.md).*

*Moved 2026-08-16.* Every other section of this paper is federal FEC money on one
disclosure regime with one set of rules. §K is state money across **four** regimes with
four different contribution limits, filing thresholds, entity taxonomies and coverage
windows, and it was the largest ungated section in the article. Those are not defects —
they are what makes the state layer its own subject — but they mean a reader cannot
compare a §K figure to an §A–J figure without a paragraph of caveat, and an article should
not spend a paragraph explaining why one of its own sections should not be compared to the
rest. The submission notes reached the same conclusion independently: *"the state-money
layer is not this paper."*

---

## Limits of inference

*Full provenance + a no-AI reproduction recipe (every source, access path, and the exact
scripts behind each figure): [Data Sources & Reproducibility](data-sources-and-reproducibility.md).*

- **Both directions now exist (Findings 1–5 + Tests A–D are outflow; Tests E–I add inflow).**
  The early findings measure where residents *send* money (outflow by donor residence); the
  recipient-anchored inflow load (Sections E–I) measures money *entering* WA/NY/TX/ID races. The
  cross-state matrix (G) reports both. They use different committee universes, so read shares
  within each rather than subtracting one from the other.
- **This paper is federal only; the state layer is a separate note.** State-legislative and
  local money is loaded for all four states (WA PDC, NY BOE, ID Sunshine, TX TEC — item 7),
  but the first cut over it **moved out of this article on 2026-08-16** to
  [`cross-state-state-money-note.md`](cross-state-state-money-note.md), which is still in
  development and not yet gated. The two layers use different disclosure regimes and filer
  universes (WA's is legislative-candidates-only), so a state-layer figure is not comparable
  to an A–J dollar figure and none is cited here. *(This bullet said "K is the state layer"
  until 2026-08-17, after §K had already moved.)*
- **Conduit-*reliance* metric is unreadable (but the money is captured).** ActBlue/WinRed
  appear as recipients of <0.5% of dollars — because, as the 2024 earmark inspection confirmed
  (Section E), FEC records each earmarked gift under the *candidate* committee as type `15E`,
  not under the conduit. So you cannot measure conduit *usage* from the recipient field — but
  the **money itself is fully captured** (under the candidates). **Do not read the
  ActBlue/WinRed-as-recipient share as "conduit reliance."** The sub-$200 *amount* share
  (Finding 1) is computed from the dollar value and is unaffected.
- **Donor proxy, and how much it actually moves.** name+zip5 over-merges common names, so it
  understates donor counts and overstates concentration, and the bias runs the same direction
  in all four states — which is why the *ordering* is robust even where the levels are not.
  **The direction is measured; the magnitude is not.** The direction comes from the donor
  paper's de-merging exercise, which splits the largest merged donors into equal halves and
  moves the top-1% share down by 6.1 to 8.3 points — so over-merging inflates concentration.
  What has *not* been measured is how much of this paper's own key does that.

  A 2026-08-02 check is sometimes cited here as having settled it and does not. That check
  re-derived the same quantities in `verify_cross_state_money.py` and found donor counts exact
  in all four states with a worst Gini gap of 0.0004 — but it groups by
  `UPPER(TRIM(contributor_name))` and `LEFT(contributor_zip, 5)`, **the same key**, on the same
  data. Two implementations of one key agreeing shows the implementations agree; it says
  nothing about whether that key merges distinct people. An earlier version of this bullet read
  it as evidence that "the key is not doing the work", which it cannot support.

  What would settle it is a genuinely different key — name plus full address, name plus ZIP9,
  or a within-cycle contributor-id join — and a report of how the four Ginis and the ordering
  move under it. That is unbuilt, and the ordering claim should be read as resting on the
  bias running the same direction in all four states rather than on its being small.
- **WA & ID composition.** WA's FEC subset draws from both a donor-filtered bulk load and an
  earlier per-candidate load; ID's is bulk-only (donor-filtered, loaded 2026-07-19) and shares
  its `individual_contributions` table with state Sunshine rows, which the FEC-committee-id
  regex filters out. Both are restricted here to in-state residents, but completeness may
  differ slightly from NY/TX pure-bulk.
- **No income/race.** Occupation/employer is the only socioeconomic signal, and it is
  self-reported.

---

## What's done, and what's next

Tests A–I are run. Status:
0. **Idaho fully integrated — DONE 2026-07-19** (all sections A–I + matrix G): ID FEC outflow +
   inflow loaded to parity; it is the small, deep-red,
   most-retail, most-retired, most-nationalized pole (safe-R Senate money 85.8% out-of-state).
   The analysis scripts were made **state-agnostic** in the same pass (item 8).
1. **True inflow — DONE for WA+NY+TX+ID, House + Senate** (Section E): recipient-anchored *bulk*
   load (`scripts/load_fec_inflow_bulk.py` → `fec_inflow.duckdb`, **5.50M contributions /
   $1.21B** of all-state money into WA/NY/TX/ID federal candidates) — built in minutes vs. the
   API path's days.
2. **Conduit/earmark attribution — DONE/verified** (Section E): earmarked ActBlue/WinRed money
   is attributed to candidates via FEC `15E` and already counted ($194M in 2024); conduit-side
   `24T` duplicates correctly excluded. No fix needed.
3. **Individual voter-file study — DONE, and MOVED 2026-08-16 to
   [`donor-class-and-the-electorate.md`](donor-class-and-the-electorate.md)**, which keeps
   federal and state panels separate and is where person-level claims belong. It was §F of this
   paper until that date; the removal note under §F says why. The work itself is complete for
   all three voter-file states and its two withdrawals are recorded here because they were
   made here. The donor age skew runs in the same direction and survives the IPW correction in
   WA, NY and ID — but its *steepness* does not replicate (old-to-young
   gradient 21.6× WA / 21.8× ID against 10.5× NY, so an "essentially identical" or
   "near-identical" gradient is withdrawn) — and the party-of-record cut shows
   donors less unaffiliated / more Dem-tilted in NY and ID. On the turnout half, NY/ID
   `voter_scores` were populated with WA-identical definitions
   (`scripts/populate_ny_id_voter_scores.py` — NY 13.54M
   rows from the parsed history, ID 1.03M from the melted participation table), and the
   giving→turnout cut replicates at a substantial donor/non-donor super-voter ratio in every
   state (WA **1.72×** / NY **1.85×** / ID **1.66×**; "near-constant" overstated it
   and is withdrawn).
4. **Cross-state flow matrix — DONE, now four-state** (Section G): inflow provenance + outflow
   destination + the systematic out-of-region magnet list (Georgia Senate ~$68M from
   WA/NY/TX/ID residents). ID is the biggest out-of-region exporter (68%) and the only net
   candidate-money importer.
5. **Sector × competitiveness — DONE, and largely a NULL after the 2026-08-16 rebuild**
   (Section H): on cycle-specific bands, finance and tech both sit at the baseline and only
   energy is clearly below it. What survives is the *travel* result — tech money goes farthest,
   energy stays home. The earlier "finance tilts competitive, tech/energy fund safe seats"
   reading was an artifact of banding every cycle with the 2026 forecast.
6. **Inflow concentration + retention — DONE** (Section I): candidate money is far less
   concentrated than total flow (Gini ~0.69 vs ~0.80); base is churning/one-time by headcount,
   concentrated-core by dollars; cycle-over-cycle retention flat ~21–25%.
7. **State-level money — DONE for all four states** (2026-07-19). WA (PDC), NY (NYSBOE
   `ny_finance.py`, 20,349 rows), ID (Sunshine), and now **TX** are all in `candidate_finance`.
   The new **TEC adapter** (`etl/adapters/tx_tec.py`) streams the Texas Ethics Commission bulk
   zip (`TEC_CF_CSV.zip` → `contribs_##.csv`/`expend_##.csv`/`filers.csv`/`cover.csv`) via DuckDB
   into the `StateFinanceAdapter` framework with a `TX:` id prefix: **19,416 candidate-cycle rows,
   2014–2026, ~$5.2B receipts** (top: Texans for Greg Abbott $120M/2022, Beto for Texas $98.6M,
   ActBlue Texas $100M). Individual/PAC split from `contributorPersentTypeCd`; party is mostly
   Unknown (TX has no party registration) and resolved downstream. Tests in
   `tests/test_etl/test_tx_tec_adapter.py`.
8. **State-agnostic scripts — DONE 2026-07-19**: all 8 cross-state scripts now enumerate the
   region via `scripts/cross_state_common.py` (glob `data/*_statewide.duckdb`, or a
   `CROSS_STATE_REGION` override) instead of hardcoded state lists; the competitiveness read and
   the reports/ output path are shared, and the magnet "broadly funded" threshold scales with
   the region. **Adding a state N needs no script edits** — load `data/N_statewide.duckdb` (+
   VRDB) via the existing loaders, run `FEC_INFLOW_STATES=N python scripts/load_fec_inflow_bulk.py`,
   then re-run the 8 scripts.
9. **State-level money analysis — DONE 2026-07-19, and MOVED OUT of this paper 2026-08-16**
   (`scripts/cross_state_state_money.py`): first cut over the state-disclosure layer loaded in
   item 7, now in [`cross-state-state-money-note.md`](cross-state-state-money-note.md).
   Headlines: house seats cost 26× more in TX than ID; statehouse money is PAC-funded
   (~31–38% individual) vs Congress's ~65% individual; TX/ID's biggest state-money filers are
   a governor's committee ($424.5M) and a ballot-measure committee respectively.
   ⚠ *This item also read "the federal ~2× competitiveness premium holds only in TX/ID (WA
   flat, NY inverted)" until 2026-08-17. **That conclusion is superseded and should not be
   cited.** It was an artifact of banding 2022+2024 money with a 2026 forecast — the same
   defect item 10 corrected in the federal sections. On cycle-specific bands the note reports
   positive premiums in WA, NY and ID, and treats Texas as unresolved because its unbanded
   residual is concentrated in uncontested seats. The note is not gated; read it there, not
   here.* **Follow-on completed same day:** the full WA PDC
   filer universe (statewide execs, party/caucus cmtes, PACs, ballot cmtes) bulk-loaded via
   the new `load-pdc-filer-universe` CLI (one Socrata CSV export request — 43K filer-years,
   ~13s; WA 1,559→16,604 rows / $1.52B), giving WA its K5 panorama row (top filer = SEIU's
   PAC; committees hold 69% of WA state money) and quantifying the caucus-committee routing
   layer ($36.2M ≈ half the candidate layer, 2022+2024).

---

## Related work

The building blocks — donor concentration, out-of-district money, whether money chases
competitive races — are established individually; the contribution here is the
recipient-anchored, four-state, federal-and-state comparison built from bulk FEC and
state-disclosure records on one harmonized frame. It sits in these literatures:

- **Mapping the donor universe.** Bonica, "Mapping the Ideological Marketplace" (2014)
  and the DIME database — the individual-contribution infrastructure this paper rebuilds
  from bulk filings and joins to voter files (Section F).
- **How much money, and why so little.** Ansolabehere, de Figueiredo & Snyder, "Why Is
  There So Little Money in U.S. Politics?" *Journal of Economic Perspectives* (2003) —
  the framing for the money-and-competitiveness cuts (Sections D, E, H): contributions
  behave more like consumption/participation than investment.
- **Cross-district and out-of-state money.** Gimpel, Lee & Pearson-Merkowitz, "The Check
  Is in the Mail: Interdistrict Funding Flows in Congressional Elections," *American
  Journal of Political Science* (2008) — the direct antecedent to the inflow/outflow
  matrix and the out-of-region magnet list (Sections B, E, G).
- **Donors, polarization, and influence.** Barber, "Ideological Donors, Contribution
  Limits, and the Polarization of American Legislatures," *Journal of Politics* (2016);
  Schlozman, Verba & Brady, *The Unheavenly Chorus* (2012); Bonica, McCarty, Poole &
  Rosenthal, "Why Hasn't Democracy Slowed Rising Inequality?" *JEP* (2013) — the
  concentration and Gini results (Sections F, I).
- **State campaign finance.** La Raja & Schaffner, *Campaign Finance and Political
  Polarization: When Purists Prevail* (2015) — context for the state-disclosure layer
  and the PAC-vs-individual split across statehouses (Section K).
- **Party and the donorate.** Grumbach & Sahn, "Race and Representation in Campaign
  Finance," *American Political Science Review* (2020) — the donor-composition frame for
  the individual layer (Section F).
