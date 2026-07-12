# Three States, Three Donor Economies
### Federal individual contributions in Washington, New York, and Texas (FEC, 2018–2026)

*Companion to [the electoral-health prospectus](electoral-health-whitepaper.md). This
realizes that paper's cross-state money thread, which was previously data-blocked
(NY/TX had zero contributions loaded). Source: `scripts/cross_state_fec_money.py`.*

---

## Scope and method (read first)

**Basis: federal individual contributions made by IN-STATE RESIDENTS, 2018–2026.**
NY and TX hold pure FEC bulk data (donor-residence-filtered); Washington's
`individual_contributions` mixes state PDC + federal FEC, so WA is restricted to rows
carrying an FEC committee id (`fec_candidate_id ~ '^[CPHS]'`) with `contributor_state =
'WA'`. All three are therefore the same thing: **how each state's residents fund federal
politics.**

**This is an OUTFLOW-by-donor-residence measure** — it shows where each state's residents
*send* money. It is **not** out-of-state money flowing *into* a state's races (the FEC
ingest is filtered on the donor's state, so inflow is not observable here). The
"non-constituent money" question from the parent paper still needs a recipient-keyed load.

Donor identity is a `name + zip5` proxy (over-merges common names, so concentration is, if
anything, slightly understated). Figures are 2018–2026 federal cycles.

---

## The headline

| Metric | **WA** | **NY** | **TX** |
|---|---:|---:|---:|
| Total federal $ (resident donors) | **$646M** | **$2.07B** | **$1.94B** |
| Contributions | 5.59M | 9.98M | 12.56M |
| Distinct donors (name+zip) | 361,818 | 671,156 | 836,784 |
| Median gift | $25 | $25 | $25 |
| **Gini (donor $)** | 0.800 | **0.848** | 0.818 |
| **Top 1% of donors → share of $** | 39.3% | **47.5%** | 41.7% |
| Top 10% of donors → share of $ | 72.3% | 78.7% | 74.5% |
| Dollars from gifts **< $200** | **25.0%** | 13.8% | 20.3% |
| Dollars from gifts **≥ $5,000** | 20.0% | **34.8%** | 33.3% |
| Dollars from **retired** donors | **24.0%** | 11.8% | 19.5% |

One line: **Washington gives the most retail, New York the most top-heavy, and each
state's money carries a distinct economic fingerprint — Big Tech, Wall Street, Energy.**

---

## Findings

### 1. New York is the most top-heavy; Washington the most retail
- **Defensible claim.** The top 1% of donors supply **47.5%** of New York's federal dollars
  versus **39.3%** in Washington (Gini 0.848 vs 0.800). Conversely, sub-$200 gifts are a
  quarter (**25.0%**) of WA's dollars but only **13.8%** of NY's, and ≥$5,000 gifts are
  **34.8%** of NY's money vs **20.0%** of WA's. New York's federal money is concentrated at
  the top; Washington's is comparatively broad-based.
- **Strongest objection.** The Gini of any voluntary-giving distribution is mechanically
  high everywhere (all three exceed 0.80), so the *level* is not itself pathological — only
  the *gap* between states is informative. And the small-dollar share is sensitive to how
  conduit (ActBlue/WinRed) earmarks are recorded (see Limits) — though the gift-size *amount*
  cut is computed directly from the dollar value and is unaffected by that.

### 2. Participation is broadest, per capita, in Washington
- **Defensible claim.** New York and Texas raise ~3× Washington's federal dollars in
  absolute terms, but Washington has the widest donor *participation* relative to its size:
  ~362K donors in a state of ~7.9M (~4.6%) versus NY ~671K/~19.6M (~3.4%) and TX
  ~837K/~30.5M (~2.7%). Fewer dollars, more givers.
- **Strongest objection.** The name+zip donor proxy over-merges common names unevenly across
  states; population denominators are total residents, not voting-eligible adults; and WA's
  lower dollar total partly just reflects fewer ultra-wealthy households, not broader civic
  habit.

### 3. The retired-donor economy is largest in Washington
- **Defensible claim.** **24.0%** of Washington's federal donor dollars come from donors who
  list their occupation as *retired* — versus **19.5%** in Texas and just **11.8%** in New
  York. WA's federal money leans most heavily on people no longer in the workforce. (A looser
  "non-working" bucket that also folds in *not-employed / none / blank* reaches ~48% in WA,
  but that figure is soft — see objection.)
- **Strongest objection.** FEC occupation/employer strings are self-reported and noisy. The
  retired-only figure is the defensible one; the broader "non-working" number bundles wealthy
  non-earners and blank/missing fields with the genuinely jobless and carries no income
  signal, so it should be read as a loose upper bound, not a measurement.

### 4. Sector signatures: Tech (WA), Wall Street (NY), Energy/Industrial (TX)
- **Defensible claim.** The largest corporate employers of each state's federal donors are
  unmistakably regional:
  - **WA — Big Tech:** Microsoft ($15.2M), Amazon ($5.0M), University of Washington
    ($4.7M), Zumiez ($4.2M), Fisher Investments ($3.1M).
  - **NY — Wall Street:** Blackstone ($11.1M), Goldman Sachs ($7.9M), KPMG ($6.6M), Jane
    Street ($5.8M), Soros Fund Management ($5.4M).
  - **TX — Energy / Industrial:** BNSF Railway ($8.0M), Valero ($7.0M), Starkey Hearing
    ($5.6M), Beal Bank ($5.1M), Lockheed Martin ($4.6M).

  The economic base that funds federal politics differs sharply by state.
- **Strongest objection.** These employer sums are dominated by a handful of mega-donors at
  each firm, not broad rank-and-file employee giving; and the strings are free-text (Texas's
  single largest "employer" is the generic *"Entrepreneur"*), so firm-level totals are
  indicative, not audited.

### 5. A uniform presidential rhythm
- **Defensible claim.** All three states show presidential-cycle dollars running ~2× their
  off-year totals, in lockstep (WA $202M/2020 vs $79M/2018; NY $612M vs $299M; TX $544M vs
  $266M). Federal giving is paced by the national calendar, not state-specific dynamics.
- **Strongest objection.** This is mechanical (presidential races simply cost more) and says
  nothing distinctive about any state — it's a useful uniformity check, not a finding.

---

## Follow-on tests

*Computed in `scripts/cross_state_fec_tests.py`. Committee master: 44,392 committees;
**100% of recipient dollars matched** in all three states.*

### A. Is the money concentrating over time?

Top-1% donor dollar share, by cycle:

| Cycle | WA | NY | TX |
|---|---:|---:|---:|
| 2018 | 28.2% | 35.3% | 29.2% |
| 2020 | 34.5% | 42.4% | 35.6% |
| 2022 | 30.3% | 36.7% | 34.9% |
| 2024 | 36.2% | **47.4%** | 41.9% |
| 2026* | 30.6% | 40.3% | 37.9% |

- **Defensible claim.** Concentration follows a **presidential sawtooth** (peaks in 2020 and
  2024) with a **mild secular upward drift**. Comparing like cycles: top-1% share rose
  presidential-to-presidential in all three (2020→2024: WA +1.7, NY +5.0, TX +6.3 pts) and
  midterm-to-midterm (2018→2022: TX +5.7, NY +1.4, WA +2.1). New York is both the most
  concentrated and rising fastest; **Washington is the flattest and most stable.**
- **Strongest objection.** Only three presidential and two-to-three midterm points — too few
  to call a secular trend confidently. The 2024 spike is entangled with record presidential
  joint-fundraising activity (see Test B), so "concentrating" is partly a cycle-composition
  artifact, not purely a structural shift. Direction = mildly rising, not a clean climb.
  *(2026 is partial-cycle.)*

### B. Where does each state's money go?

Destination of residents' federal dollars (recipient committee → state/office via the FEC
committee master):

| Destination | WA | NY | TX |
|---|---:|---:|---:|
| **In-state Congress** | 13.4% | 10.1% | 16.0% |
| Out-of-state Congress | 24.1% | 29.5% | 19.4% |
| Presidential | 11.0% | 7.0% | 6.5% |
| PAC / party / other | 51.5% | 53.4% | 58.1% |

- **Defensible claim.** Residents fund **their own congressional delegation least of all** —
  just 10–16% of their federal dollars. They give roughly **2× as much to *out-of-state*
  congressional races** (WA 24%, NY 30%), and the majority (51–58%) flows to **national party
  committees and joint-fundraising vehicles.** Washington's single largest federal
  destination is the Democratic presidential JFC (~$61M) — on par with *all* in-state
  congressional giving combined (~$87M); other top destinations are the DNC, DCCC, DSCC, RNC,
  and the Trump JFCs. Texans are the most "local" (in/out-of-state Congress ratio 0.82); New
  Yorkers the most nationalized (0.34 — over 3× more to out-of-state than to their own
  delegation). This is the **donor-side counterpart to the nationalization-of-money
  literature**: even constituents' own money is overwhelmingly aimed at national / out-of-
  state politics rather than their representatives.
- **Strongest objection / caveat.** This remains **outflow** (where residents *send* money),
  not money flowing *into* each state's races. The majority "PAC/party/other" bucket is
  genuine national party + JFC money, but **JFCs blur the boundaries** — a presidential JFC
  funds the nominee *and* the party — so the "Presidential" row understates true
  presidential+national giving, and the splits among national vehicles are soft. The in- vs.
  out-of-state *Congress* split is the robust part (direct candidate-committee gifts).

### C. Top donors, top recipients, and the cross-state magnets

*Computed in `scripts/diag_cross_state_donors.py`.*

**Largest individual donors** confirm the sector fingerprint at the person level:
- **WA (tech/VC):** the Cornfields (~$3.3M), Tom Campion/Zumiez ($3.2M), Nick Hanauer (VC),
  Rory & Melinda Gates.
- **NY (finance/philanthropy):** Philip Munger ($4.1M), George Soros ($4.0M), Stephen
  Schwarzman/Blackstone ($3.2M), Agnes Gund/MoMA.
- **TX (energy/industrial):** Syed Anwar/PetroPlex ($5.2M), Paul Foster/Western Refining
  ($3.5M), the Perots, Woody Hunt.

**Largest recipient committees** are national vehicles, with marquee in-state contests
poking through: D-state dollars concentrate in the **Harris Victory Fund** (WA $61M, NY
$176M) and **Fight for the People PAC** (NY $82M); TX dollars in **Trump Victory** ($71M) and
the **RNC** ($67M). In-state contests that surface: Kim Schrier (WA-08, $17M), Patty Murray,
Ted Cruz (TX, $35M).

**Cross-state money magnets.** Of 12,256 committees these donors touch, **4,602 are funded by
donors in all three states.** The top are national party / JFC vehicles (Harris Victory Fund
$290M combined; RNC $111M; DSCC / DNC / DCCC ~$96–99M each). The single cleanest nationalization
signal: **Warnock for Georgia** — a *Georgia* Senate race drawing **WA $7.4M + NY $16.3M + TX
$6.0M**, funded by three states whose residents cannot vote in it.

- **Caveat.** Individual-donor identity is a name+zip proxy (merges across cycles; a few
  employer labels are data-entry quirks). Recipient totals are donor-residence *outflow from
  these three states only* — not the committee's full national haul.

### D. Does money chase competitive races? (money × competitiveness)

*Computed in `scripts/diag_money_vs_competitiveness.py`, joining residents' U.S. House
contributions to each district's competitiveness band (this project's own forecast margin:
Tossup <5 / Lean 5–10 / Likely 10–20 / Solid ≥20). **PARTIAL run:** WA + TX donors → WA + TX
House districts, 2022–2026 (post-redistricting). NY pending (DB was locked by the live inflow
load); the full 3-state + inflow-side version will follow.*

| Band | # districts | % of districts | $ to band | $ / district | % of $ |
|---|--:|--:|--:|--:|--:|
| Tossup (<5) | 3 | 6.2% | $11.3M | **$3.77M** | 7.9% |
| Lean (5–10) | 2 | 4.2% | $5.4M | $2.71M | 3.8% |
| Likely (10–20) | 24 | 50.0% | $76.7M | $3.20M | 53.6% |
| Solid (≥20) | 19 | 39.6% | $49.7M | **$2.62M** | 34.7% |

- **Defensible claim.** Donor money chases competitiveness only **weakly**. Tossup districts
  draw the most per district ($3.77M vs $2.62M in Solid — a ~1.4× premium), but **88% of all
  dollars still flow to safe (Likely + Solid) districts**, because ~90% of districts are safe.
  In-state House money is dominated by support for (mostly safe-seat) candidates, not
  strategic targeting of the marginal race — the donor-side echo of "money follows the
  scoreboard." Cross-state House giving between WA and TX is negligible ($2.4M of $143M):
  residents fund their *own* state's House candidates.
- **Caveats.** WA+TX only (NY — the largest Democratic-money state — still to add). Donor-side
  *outflow*, not inflow. The "Lean" band has only 2 districts (noisy). Strategic/competitive
  targeting is more likely to surface in PAC/JFC and out-of-state money (the inflow load + the
  large national-vehicle bucket from Test B) than in this in-state-resident slice — which is
  exactly what the inflow load will let us test.

### E. Inflow side — does money chase competitive races? (WA+NY+TX House & Senate)

*From the recipient-anchored inflow dataset (`fec_inflow.duckdb`: **5.48M contributions /
$1.20B**, all-state donors → WA/NY/TX federal candidates, built by
`scripts/load_fec_inflow_bulk.py` in minutes — the API path would have taken days), joined to
competitiveness. `scripts/diag_inflow_vs_competitiveness.py`.*

**U.S. House, 2022–2026 — $485M across 74 districts:**

| Band | # dists | % dists | $ in | $ / district | % of $ | out-of-state share |
|---|--:|--:|--:|--:|--:|--:|
| Tossup (<5) | 4 | 5.4% | $47.2M | **$11.81M** | 9.7% | 45.0% |
| Lean (5–10) | 4 | 5.4% | $42.3M | **$10.59M** | 8.7% | 36.1% |
| Likely (10–20) | 31 | 41.9% | $190.5M | $6.14M | 39.3% | 39.9% |
| Solid (≥20) | 35 | 47.3% | $205.2M | $5.86M | 42.3% | 44.4% |

- **Defensible claims:**
  1. **The competitiveness premium is real and ~2×.** Tossup ($11.8M/district) and Lean
     ($10.6M) districts pull roughly double the per-district inflow of safe seats (~$6M) —
     money *does* chase the marginal race, far more clearly than the donor-side ~1.4× (Section D).
  2. **But safe seats still capture ~82% of the money** (Likely+Solid), because they're ~89% of
     districts. Likely and Solid draw about the *same* per district (~$6M): once a seat is safe,
     *how* safe barely changes the money — the jump is **between** competitive and safe, not
     within safe.
  3. **~40–45% of all inflow is out-of-state, roughly uniform across every band.**
     Nationalization is **pervasive, not battleground-specific** — roughly two-fifths of the
     money funding these House races comes from people who cannot vote in them, in safe and
     tossup seats alike.

**U.S. Senate, 2018–2026** (the model does not forecast US Senate; competitiveness via actual results):

| State | $ in | out-of-state share | Senate races in window |
|---|--:|--:|---|
| **TX** | **$253.2M** | 45.3% | competitive — Cruz/O'Rourke 2018 (R+2.6), Cruz/Allred 2024 (R+8.8) |
| NY | $55.2M | 53.5% | safe-D — Schumer / Gillibrand |
| WA | $45.0M | 41.1% | safe-D — Murray / Cantwell |

- **Senate echoes the House, louder.** Competitive **TX** Senate races drew **$253M — ~5× safe
  NY ($55M) or WA ($45M)**: at the statewide level, competition is the single biggest money
  magnet. Yet out-of-state share is high *everywhere* (41–54%) and is actually **highest in
  safe NY (53.5%)** — national donors fund high-profile safe senators (Schumer/Gillibrand) as
  readily as battlegrounds. Same lesson as the House: competition lifts the total, but the
  out-of-state flood is profile-driven and pervasive.

- **Earmarks ARE attributed (verified — correcting an earlier caveat).** Conduit-routed
  (ActBlue/WinRed) money is **not** lost from these totals: FEC records each earmarked
  individual gift under the *candidate* committee as transaction type `15E` — **$194M for these
  candidates in 2024 alone, more than the $90M of direct `15` gifts** — and the inflow load
  captures it. The conduit-side `24T` records ($150M) are the *same money* seen from the conduit
  and are correctly excluded to avoid double-counting (`scripts/diag_earmark_inspect.py`).

- **Caveats.** House competitiveness = 2026 forecast bands on current districts; Senate banded by
  actual two-party result. WA contributes no congressional Tossups in the 2026 map (its
  competitive seats land in Lean/Likely). State-legislative money still excluded (federal only).

### F. The individual layer — who votes, who gives, and whether the donor skew is real (WA, 382K match)

*Computed in `scripts/diag_wa_individual_findings.py` against `data/wa_statewide.duckdb`
(`voter_scores`, `voter_donor_affiliation`) with `data/wa_vrdb.duckdb` ATTACHed
(`voters`, 5.51M; `voting_history`, 27.1M). WA is the one state here that needs **no
external voter file** — it already has the registered roll, the vote history, and the
person-level voter↔donor match. These refresh the democracy-insight gauntlet's figures on
the improved match (320K → **382,408 voters**, 343,891 of them carrying a generation label).*

**F1 — The off-year electorate is old, and the young drop out, not down.**
- **Defensible claim.** Within-cohort turnout and electorate composition both swing hard by
  cycle type. Turnout of 18–29s **collapses 58.4% → 15.8%** (2024 presidential → off-year
  generals), while 65+ falls only **88.3% → 61.3%**. As composition: 65+ are **28.5%** of the
  2024 presidential electorate but **~39%** of the off-year electorate, while 18–29 fall from
  **14.2% → 7.6%** — a senior-to-youth ratio that widens from ~2:1 to ~5:1 off-cycle. The
  decision in odd-year local elections is made by a substantially older electorate than the
  one that shows up for president.
- **Strongest objection.** This is *voluntary* differential participation under WA's
  all-mail, postage-paid, automatic-registration system — not disenfranchisement — and the
  fix (move local races on-cycle) is institutional, which is itself evidence of a *responsive*
  system, not a failing one. The within-cohort *rate* also uses a current-roll denominator
  (survivorship-biased), so read the composition **shares** as the robust cut.
- **Caveat.** VRDB vote history begins in 2021, so the presidential figure rests on 2024 alone
  and the midterm on 2022 alone; only the off-year row averages three cycles (2021/2023/2025).

**F2 — The donor age skew is genuine, *not* a matcher artifact (the white paper's open question, answered).**
- **Defensible claim.** Matched donors over-represent the old and under-represent the young —
  raw donor-share ÷ roll-share is **Silent 1.87×, Boomer 1.64×, Gen X 1.18×, Millennial
  0.59×, Gen Z 0.17×**. The white paper's strongest objection was that this is a *matcher*
  artifact (the (last, first-initial, zip5) uniqueness guard over-selects older, rarer-named,
  stable-address voters). Tested directly, **it is not**: the probability a voter is uniquely
  matchable on that key is nearly flat across generations — **68.9% (Gen Z) to 73.1%
  (Silent), a ~4-point spread** — so inverse-propensity re-weighting barely moves the ratios
  (Silent 1.87→**1.83×**, Gen Z 0.17→**0.17×**). The age skew survives the correction; it is a
  real property of who gives, not of who the matcher can find. (Person-level concentration on
  this match: top-1% of matched donors = **47.7%** of matched dollars, top-10% = **80.0%**,
  Gini **0.862**; geographically, **61.2%** of matched-donor dollars come from just two
  Seattle-metro ZIP3s — 981xx 35.9% + 980xx 25.2%.)
- **Strongest objection / residual bias.** The IPW corrects the *name-commonness* channel — the
  matcher's actual uniqueness guard — but cannot correct the one channel it can't observe: a
  donor whose address changed between giving and today fails the zip match, and mobility skews
  young. That residual bias runs in the *same* direction as the raw skew (it deflates the young
  donor share), so raw should be read as an **upper bound** on the true age skew — but the
  mechanism the objection actually named (rare names → easier match for the old) explains
  essentially none of it.

**F3 — Money and votes stack on the same people (association only).**
- **Defensible claim.** Among the 343,891 matched donors carrying a turnout score, **84.0% are
  super-voters versus 50.1%** of non-donors (1.68×), and their mean turnout propensity is
  **0.953 vs 0.748**. Financial voice and electoral voice concentrate on the same individuals
  rather than offsetting.
- **Strongest objection.** This is cross-sectional association, not a causal "giving makes you
  vote" claim: donors are pre-selected for engagement (reverse causation is equally plausible),
  and the matcher itself favors stable-address super-voters, so selection *and* reverse
  causation both inflate the gap. The benign reading — donating as a participation *gateway* —
  is fully live.

**F4 — Robustness: concentration precision + match validation.**
- **Bootstrap CIs on concentration** (`scripts/diag_donor_concentration_bootstrap.py`, B=1000).
  Because donor identity is a name+zip5 *proxy*, the concentration estimates carry
  sampling-style uncertainty — but it is small. Matched-donor **Gini 0.862 [95% CI 0.856–0.868]**,
  **top-1% 47.7% [45.6–50.0]**, **top-10% 80.0% [79.1–80.9]**; the inflow side (2024) is tighter
  still (Gini 0.690 [0.688–0.692]). The concentration is a precise feature of the data, not an
  artifact of which donors landed in the pool. (The proxy's over-merging biases concentration
  *down*, so true figures are, if anything, slightly higher.)
- **Match-precision validation** (`scripts/diag_match_validation_sample.py`). On a seed-fixed
  150-match sample, the matched donor's full first name equals the voter's in **87%** of cases,
  and only **13%** sit on a (last, first-initial, zip5) key shared by a same-key donor namesake
  — the population where a false merge or pooled-attribution is even possible (4 of 150 could not
  be re-found, parsing/PDC edge cases). The sample is emitted as a CSV for human adjudication
  (true precision = Y/(Y+N)); the structural ceiling on false merges is reassuringly low.

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

| Recipient state | Total $ | In-state | In-region (other 2) | Rest-of-US |
|---|--:|--:|--:|--:|
| **WA** | $154.6M | 66.7% | 6.3% | **27.0%** |
| **NY** | $462.7M | 55.1% | 3.8% | **41.1%** |
| **TX** | $582.4M | 59.6% | 5.9% | **34.4%** |

**OUTFLOW — where each state's residents send their H+S candidate money (by recipient region):**

| Donor state | Total $ | In-state | In-region (other 2) | Rest-of-US |
|---|--:|--:|--:|--:|
| **WA** | $198.8M | 43.8% | 5.3% | **50.9%** |
| **NY** | $672.9M | 33.9% | 4.0% | **62.1%** |
| **TX** | $526.6M | 54.1% | 2.5% | **43.4%** |

- **Defensible claims.**
  1. **Every one of these states sends the *majority* (or near it) of its candidate money out
     of region.** NY residents ship **62%** of their House+Senate candidate dollars to
     candidates in other states; even Texas, the most parochial, sends **43%**. This is the
     donor-side engine of nationalization, measured directly rather than inferred.
  2. **In-region cross-funding is negligible — WA/NY/TX barely fund *each other*** (≤6% of
     either matrix in every cell). The out-of-region money is not flowing to neighbors; it is
     aimed at national battlegrounds. NY is the dominant exporter (~$418M leaves), WA the
     dominant net importer relative to its own giving.
  3. **The magnet list is a clean battleground map.** The out-of-region candidate committees
     funded by donors in **all three** states are almost entirely Senate battlegrounds:
     **Warnock-GA ($29.7M from these three states), Ossoff-GA ($19.2M), Kelly-AZ ($19.5M),
     Tester-MT ($12.8M), Harrison-SC ($11.6M)**, with Graham-SC, Perdue/Loeffler-GA,
     Gideon-ME, Rosen/Cortez Masto-NV and McConnell-KY close behind. **Georgia Senate races
     alone (Warnock + Ossoff + Perdue + Loeffler) drew ~$67M** from residents of WA, NY, and TX —
     none of whom can vote in Georgia. The Section-C Warnock anecdote is the rule, not the exception.
- **Strongest objection / caveat.** The two matrices use different committee universes (inflow
  is the recipient-anchored bulk; outflow is per-state authorized committees), so their absolute
  totals are **not** directly subtractable — read the *shares within each*, not the cross-matrix
  difference. "Rest-of-US" inflow is robust (blank donor-state is 0.08% of inflow dollars).
  Out-of-region ≠ "non-constituent and therefore illegitimate": a donor may have ties, and party
  committees (excluded here) carry yet more of the nationalized money.

### H. Sector × competitiveness — does Wall Street chase Tossups while tech/energy fund safe seats?

*Computed in `scripts/diag_sector_vs_competitiveness.py`, crossing the employer/sector
signatures (Sections A/C) against the inflow competitiveness bands (Section E). Each inflow
contribution to a WA/NY/TX U.S. House district (2022–2026, $485M) is classified by a
keyword-on-employer sector and joined to the district's forecast band (Tossup<5 / Lean5–10 /
Likely10–20 / Solid≥20). "Competitive share" = (Tossup+Lean) ÷ sector total.*

| Sector | $ (House, 3 states) | Competitive share | Out-of-state share |
|---|--:|--:|--:|
| Real estate | $8.0M | **22.0%** | 32.2% |
| **Finance / Wall St** | $18.4M | **21.7%** | 44.4% |
| Law | $17.6M | 20.1% | 33.1% |
| Healthcare | $8.4M | 16.1% | 35.7% |
| **Energy** | $3.5M | **14.3%** | 26.0% |
| **Tech** | $7.1M | **11.7%** | 51.8% |
| *[all sectors baseline]* | $485M | *18.5%* | *~43%* |

<sub>Sector keyword map extended after a coverage audit (`scripts/diag_sector_coverage.py`)
surfaced major law firms, hedge funds, and tech names as unclassified; the additions lifted
classified dollars from ~14% to ~15% and left the pattern below intact.</sub>

- **Defensible claim.** The hypothesis is **partially borne out, with a twist.** Finance money
  does tilt toward competition (**21.7%** of its dollars to Tossup/Lean vs an 18.5% baseline),
  and **tech is now the single least competition-seeking sector (11.7%)**, with energy next at
  14.3% — both disproportionately fund safe seats. But the cleanest contrast is in *travel*, not
  band: **energy money is strikingly local** (only **26%** out-of-state vs ~43% baseline) — it
  funds its own state's (Texas) incumbents — while **tech money travels the farthest (52%
  out-of-state) yet lands in safe seats** (national safe-D House members). Finance both travels
  (44%) and tilts competitive. So: Wall Street chases the marginal race somewhat; tech funds
  safe co-partisans at a distance; energy funds the home-state incumbent.
- **Strongest objection.** The effect is **modest and partly mechanical.** The competitive-share
  spread is only ~10 points (real-estate 22% to tech 12%), and tech (WA) and energy (TX)
  are concentrated in their home states, whose *own* House seats happen to be safe (Solid-D
  Seattle, Solid-R Texas) — so "tech/energy fund safe seats" is in part just "their in-state
  seats are safe," not a strategic preference for safety.
- **Caveat.** Even after extending the keyword map with the biggest missing law firms, hedge
  funds, and tech names, classified sectors are still a **thin slice — only ~15% of inflow
  dollars**; "retired / not-employed / blank" is 46.8% and "unclassified" ~39%, and tech
  ($7.1M) and energy ($3.5M) volumes in these three states' House races are small enough to be
  noisy. Employer strings are self-reported free text; the keyword map is indicative, not
  audited (`scripts/diag_sector_coverage.py`). House-only (Senate competitiveness isn't
  model-forecast).

### I. Inflow concentration trend + donor retention — is the candidate-money base democratizing?

*Computed in `scripts/diag_inflow_concentration_retention.py` on the inflow side (all-state
donors → WA/NY/TX H+S candidates; donor = name+zip5 proxy). Section A measured concentration on
the **outflow**; this measures it on the **inflow**, and adds repeat-vs-one-time retention.*

| Cycle | Inflow $ | Donors | Top-1% $ | Top-10% $ | Gini |
|---|--:|--:|--:|--:|--:|
| 2018 | $252M | 244K | 16.2% | 52.4% | 0.651 |
| 2020 | $249M | 225K | 17.2% | 54.2% | 0.672 |
| 2022 | $248M | 218K | 15.8% | 55.9% | 0.689 |
| 2024 | $284M | 310K | 18.4% | 58.5% | 0.690 |
| 2026* | $167M | 166K | 16.5% | 58.3% | 0.686 |

- **Defensible claim 1 — candidate-directed money is far *less* concentrated than the total
  flow.** Inflow to candidates (gifts capped at the per-election limit) runs **top-1% ≈ 16–18%,
  Gini ≈ 0.69** — against the **outflow** figures of top-1% **39–48%** and Gini **0.80–0.85**
  (Sections A & F, which include uncapped JFC/PAC/party money). The system's dollar
  concentration lives in the **party/JFC layer, not in direct candidate giving**, which is
  structurally egalitarian by the contribution cap. There is a **mild secular rise even within
  candidate money** (Gini 0.651→0.690, top-10% 52→59% across 2018→2024), but no presidential
  sawtooth — concentration here drifts up gently and plateaus.
- **Defensible claim 2 — a churning, mostly one-time base funds the candidates, but a persistent
  minority supplies most of the dollars.** Across 2018–2026, **78.2% of donors give in only one
  cycle** (supplying **41.7%** of dollars); the **21.8%** who give in ≥2 cycles supply **58.3%**.
  And cycle-over-cycle retention is **low and flat — ~21–25%** of a cycle's donors gave in the
  immediately prior cycle (2020 23.4%, 2022 25.0%, 2024 21.1%), with **no rising trend.** Roughly
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

*New cut in `scripts/diag_loser_side_money.py`; NY + WA U.S. House inflow 2022–2026,
recipient party from the committee→party map, favored party from the forecast margin.
TX omitted — its committee→party map isn't built.*

A safe seat for one party is a longshot for the other, so we can ask which side the money
actually reaches. Almost all of it goes to the favored side, and the safer the seat, the
more lopsided the split. In New York the longshot party's share of House inflow falls from
74% in the lone tossup to 27% in Likely seats to just **5.5%** in Solid (≥20-point) seats;
Washington runs the same way (24.6% Likely → **4.8%** Solid). Put plainly: in a truly safe
district the disadvantaged party's candidate raises about a nickel on the dollar and the
favored side takes the rest. (Caveats: this is money entering the race, House only;
leadership PACs tied to safe incumbents can pad the favored side; and "favored" is only
meaningful once a seat is actually safe — in a real tossup the challenger can out-raise
the nominal favorite, which is why the tossup row looks inverted.)

---

## Limits of inference

*Full provenance + a no-AI reproduction recipe (every source, access path, and the exact
scripts behind each figure): [Data Sources & Reproducibility](data-sources-and-reproducibility.md).*

- **Both directions now exist (Findings 1–5 + Tests A–D are outflow; Tests E–I add inflow).**
  The early findings measure where residents *send* money (outflow by donor residence); the
  recipient-anchored inflow load (Sections E–I) measures money *entering* WA/NY/TX races. The
  cross-state matrix (G) reports both. They use different committee universes, so read shares
  within each rather than subtracting one from the other.
- **Federal only.** State-legislative and local money (NYSBOE / Texas Ethics Commission) is
  not included — those need the adapter work flagged in the white paper.
- **Conduit-*reliance* metric is unreadable (but the money is captured).** ActBlue/WinRed
  appear as recipients of <0.5% of dollars — because, as the 2024 earmark inspection confirmed
  (Section E), FEC records each earmarked gift under the *candidate* committee as type `15E`,
  not under the conduit. So you cannot measure conduit *usage* from the recipient field — but
  the **money itself is fully captured** (under the candidates). **Do not read the
  ActBlue/WinRed-as-recipient share as "conduit reliance."** The sub-$200 *amount* share
  (Finding 1) is computed from the dollar value and is unaffected.
- **Donor proxy.** name+zip5 over-merges common names, modestly understating donor counts and
  overstating concentration.
- **WA composition.** WA's FEC subset draws from both a donor-filtered bulk load and an
  earlier per-candidate load; both are filtered here to WA residents, but completeness may
  differ slightly from NY/TX pure-bulk.
- **No income/race.** Occupation/employer is the only socioeconomic signal, and it is
  self-reported.

---

## What's done, and what's next

Tests A–I are run. Status:
1. **True inflow — DONE for WA+NY+TX, House + Senate** (Section E): recipient-anchored *bulk*
   load (`scripts/load_fec_inflow_bulk.py` → `fec_inflow.duckdb`, **5.48M contributions /
   $1.20B** of all-state money into WA/NY/TX federal candidates) — built in minutes vs. the API
   path's days.
2. **Conduit/earmark attribution — DONE/verified** (Section E): earmarked ActBlue/WinRed money
   is attributed to candidates via FEC `15E` and already counted ($194M in 2024); conduit-side
   `24T` duplicates correctly excluded. No fix needed.
3. **WA individual voter-file study — DONE** (Section F): turnout-by-age, donor
   representativeness *with* the matcher-bias re-weighting (the skew survives → genuine, not an
   artifact), and giving↔turnout, all on the 382K match. WA needs no external file. The **ID/NY
   individual** versions are still gated on acquiring those voter files.
4. **Cross-state flow matrix — DONE** (Section G): inflow provenance + outflow destination +
   the systematic out-of-region magnet list (Georgia Senate ~$67M from WA/NY/TX residents).
5. **Sector × competitiveness — DONE** (Section H): finance tilts mildly competitive; tech/energy
   fund safe seats; energy money is distinctively local. Modest, on a thin classified slice.
6. **Inflow concentration + retention — DONE** (Section I): candidate money is far less
   concentrated than total flow (Gini ~0.69 vs ~0.80); base is churning/one-time by headcount,
   concentrated-core by dollars; cycle-over-cycle retention flat ~21–25%.
7. **State-level money** — NYSBOE (~½ day) + TEC (new adapter) to extend below the federal layer.
