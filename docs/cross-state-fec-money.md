# Four States, Four Donor Economies
### Federal individual contributions in Washington, New York, Texas, and Idaho (FEC, 2018–2026)

*Companion to [the electoral-health prospectus](electoral-health-whitepaper.md). This
realizes that paper's cross-state money thread, which was previously data-blocked
(NY/TX had zero contributions loaded). Source: `scripts/cross_state_fec_money.py`.
**Idaho added 2026-07-19** (FEC outflow + inflow loaded to parity) as the small,
deep-red pole; **all sections (headline, Findings 1–5, Tests A–I, and the flow
matrix G) are now four-state** — every table carries WA/NY/TX/ID.*

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

Donor identity is a `name + zip5` proxy (over-merges common names, so concentration is, if
anything, slightly understated). Figures are 2018–2026 federal cycles.

---

## The headline

| Metric | **WA** | **NY** | **TX** | **ID** |
|---|---:|---:|---:|---:|
| Total federal $ (resident donors) | **$646M** | **$2.07B** | **$1.94B** | **$76M** |
| Contributions | 5.59M | 9.98M | 12.56M | 0.77M |
| Distinct donors (name+zip) | 361,818 | 671,488 | 836,784 | 54,155 |
| Median gift | $25 | $25 | $25 | $25 |
| **Gini (donor $)** | 0.800 | **0.848** | 0.818 | *0.775* |
| **Top 1% of donors → share of $** | 39.3% | **47.5%** | 41.7% | *36.0%* |
| Top 10% of donors → share of $ | 72.3% | 78.7% | 74.5% | *69.2%* |
| Dollars from gifts **< $200** | 25.0% | 13.8% | 20.3% | **29.0%** |
| Dollars from gifts **≥ $5,000** | 20.0% | **34.8%** | 33.3% | 20.1% |
| Dollars from **retired** donors | 24.0% | 11.8% | 19.5% | **31.7%** |

*(Bold = most concentrated / top-heavy on that row; italic = least. New York holds
every top-heavy extreme; Idaho now holds every retail extreme.)*

One line: **New York gives the most top-heavy, Idaho the most retail; Washington and
Texas sit between — and each state's money carries a distinct economic fingerprint:
Big Tech (WA), Wall Street (NY), Energy/Industrial (TX), MLM/timber (ID).**

---

## Findings

### 1. New York is the most top-heavy; Idaho the most retail
- **Defensible claim.** The top 1% of donors supply **47.5%** of New York's federal dollars
  versus **36.0%** in Idaho (Gini 0.848 vs 0.775) — with WA (39.3%) and TX (41.7%) between.
  Conversely, sub-$200 gifts are **29.0%** of Idaho's dollars and 25.0% of Washington's but
  only **13.8%** of NY's, and ≥$5,000 gifts are **34.8%** of NY's money vs ~20% of both ID
  and WA. New York's federal money is concentrated at the top; **Idaho's is the most
  broad-based of the four** (it edges out Washington on every retail measure), and it does so
  despite being deep-red — retail-vs-whale structure is not a partisan property. The two
  big-dollar states (NY, TX) are the most top-heavy; the two small-population states (WA
  relative to its dollars, ID absolutely) are the most retail.
- **Strongest objection.** The Gini of any voluntary-giving distribution is mechanically
  high everywhere (all four exceed 0.77), so the *level* is not itself pathological — only
  the *gap* between states is informative. Idaho's low concentration is partly a size effect:
  a $76M pool simply has fewer mega-donors to concentrate around than a $2B one. And the
  small-dollar share is sensitive to how conduit (ActBlue/WinRed) earmarks are recorded (see
  Limits) — though the gift-size *amount* cut is computed directly from the dollar value and
  is unaffected by that.

### 2. Participation is broadest, per capita, in Washington
- **Defensible claim.** New York and Texas raise ~3× Washington's federal dollars in
  absolute terms, but Washington has the widest donor *participation* relative to its size:
  ~362K donors in a state of ~7.9M (~4.6%) versus NY ~671K/~19.6M (~3.4%), TX
  ~837K/~30.5M (~2.7%), and ID ~54K/~1.96M (~2.8%). Fewer dollars, more givers. Idaho sits
  near Texas — small-population but not disproportionately participatory; WA remains the
  standout.
- **Strongest objection.** The name+zip donor proxy over-merges common names unevenly across
  states; population denominators are total residents, not voting-eligible adults; and WA's
  lower dollar total partly just reflects fewer ultra-wealthy households, not broader civic
  habit.

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

*Computed in `scripts/cross_state_fec_tests.py`. Committee master: 44,606 committees;
**100% of recipient dollars matched** in all four states.*

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
  +5.0, TX +6.3 pts) and midterm-to-midterm (2018→2022: TX +5.7, NY +1.4, WA +2.1). New York
  is both the most concentrated and rising fastest. **Idaho is the exception that sharpens the
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

Destination of residents' federal dollars (recipient committee → state/office via the FEC
committee master):

| Destination | WA | NY | TX | ID |
|---|---:|---:|---:|---:|
| **In-state Congress** | 13.4% | 10.1% | 16.0% | *4.8%* |
| Out-of-state Congress | 24.1% | 29.5% | 19.4% | 25.5% |
| Presidential | 11.0% | 7.0% | 6.5% | 7.8% |
| PAC / party / other | 51.5% | 53.4% | 58.1% | **61.9%** |

- **Defensible claim.** Residents fund **their own congressional delegation least of all** —
  just 10–16% of their federal dollars in WA/NY/TX, and a startling **4.8% in Idaho**. They
  give **2×–5× as much to *out-of-state* congressional races** (WA 24%, NY 30%, ID 25.5%), and
  the majority (51–62%) flows to **national party committees and joint-fundraising vehicles.**
  Washington's single largest federal destination is the Democratic presidential JFC (~$61M) —
  on par with *all* in-state congressional giving combined (~$87M); other top destinations are
  the DNC, DCCC, DSCC, RNC, and the Trump JFCs. **Idaho is the extreme of nationalization:**
  its in/out-of-state Congress ratio is **0.19** (it sends >5× more to other states'
  congressional races than to its own delegation) and 62% goes to national vehicles — a safe,
  small state with few competitive home races gives almost entirely to the national contest.
  Texans are the most "local" (ratio 0.82); New Yorkers 0.34; Idaho the least local of all.
  This is the **donor-side counterpart to the nationalization-of-money literature**: even
  constituents' own money is overwhelmingly aimed at national / out-of-state politics rather
  than their representatives — and the smaller and safer the state, the more so.
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
contributions to each district's competitiveness band (this project's own forecast margin:
Tossup <5 / Lean 5–10 / Likely 10–20 / Solid ≥20). **Full four-state run:** WA/NY/TX/ID donors
→ WA/NY/TX/ID House districts, 2022–2026 (post-redistricting), 76 districts / $298M. (An earlier
version was a partial WA+TX run; the state-agnostic refactor now covers all four.)*

| Band | # districts | % of districts | $ to band | $ / district | % of $ | cross-state $ |
|---|--:|--:|--:|--:|--:|--:|
| Tossup (<5) | 4 | 5.3% | $27.6M | **$6.90M** | 9.3% | $2.4M |
| Lean (5–10) | 4 | 5.3% | $27.9M | **$6.97M** | 9.4% | $1.3M |
| Likely (10–20) | 32 | 42.1% | $123.6M | $3.86M | 41.5% | $9.6M |
| Solid (≥20) | 36 | 47.4% | $118.9M | **$3.30M** | 39.9% | $8.4M |

- **Defensible claim.** With all four states in, donor money chases competitiveness **more
  clearly than the earlier partial run suggested but still modestly**: Tossup/Lean districts
  pull ~$6.9M each vs $3.3M in Solid — a **~2.1× premium** (up from the WA+TX-only ~1.4×, once
  New York's large donor base is included). Yet **81% of all dollars still flow to safe
  (Likely + Solid) districts**, because ~90% of districts are safe. In-state House money is
  dominated by support for (mostly safe-seat) candidates, not strategic targeting of the
  marginal race — the donor-side echo of "money follows the scoreboard." **Cross-state House
  giving is small (~$21.7M of $298M, ~7%)**: residents overwhelmingly fund their *own* state's
  House candidates. Idaho contributes only to the safe bands (cd02 R+16 → Likely, cd01 R+35 →
  Solid; no ID tossup), reinforcing that safe-state in-district money is a safe-seat phenomenon.
- **Caveats.** Donor-side *outflow*, not inflow (Section E is the inflow counterpart). The
  competitiveness bands are this project's 2026 forecast on current districts. Strategic
  targeting shows up more in PAC/JFC and out-of-state money (Test B's large national-vehicle
  bucket + the inflow side) than in this in-state-resident slice.

### E. Inflow side — does money chase competitive races? (WA+NY+TX+ID House & Senate)

*From the recipient-anchored inflow dataset (`fec_inflow.duckdb`: **5.50M contributions /
$1.21B**, all-state donors → WA/NY/TX/ID federal candidates — ID added 2026-07-19 — built by
`scripts/load_fec_inflow_bulk.py` in minutes; the API path would have taken days), joined to
competitiveness. `scripts/diag_inflow_vs_competitiveness.py`, now four-state.*

**U.S. House, 2022–2026 — $488M across 76 districts:**

| Band | # dists | % dists | $ in | $ / district | % of $ | out-of-state share |
|---|--:|--:|--:|--:|--:|--:|
| Tossup (<5) | 4 | 5.3% | $47.2M | **$11.81M** | 9.7% | 45.0% |
| Lean (5–10) | 4 | 5.3% | $42.3M | **$10.59M** | 8.7% | 36.1% |
| Likely (10–20) | 32 | 42.1% | $192.3M | $6.01M | 39.4% | 40.0% |
| Solid (≥20) | 36 | 47.4% | $206.1M | $5.73M | 42.2% | 44.2% |

- **Defensible claims:**
  1. **The competitiveness premium is real and ~2×.** Tossup ($11.8M/district) and Lean
     ($10.6M) districts pull roughly double the per-district inflow of safe seats (~$6M) —
     money *does* chase the marginal race, far more clearly than the donor-side ~2.1× (Section D).
  2. **But safe seats still capture ~82% of the money** (Likely+Solid), because they're ~89% of
     districts. Likely and Solid draw about the *same* per district (~$6M): once a seat is safe,
     *how* safe barely changes the money — the jump is **between** competitive and safe, not
     within safe.
  3. **~36–45% of all inflow is out-of-state, roughly uniform across every band.**
     Nationalization is **pervasive, not battleground-specific** — roughly two-fifths of the
     money funding these House races comes from people who cannot vote in them, in safe and
     tossup seats alike.

**U.S. Senate, 2018–2026** (the model does not forecast US Senate; competitiveness via actual results):

| State | $ in | out-of-state share | Senate races in window |
|---|--:|--:|---|
| **TX** | **$253.2M** | 45.3% | competitive — Cruz/O'Rourke 2018 (R+2.6), Cruz/Allred 2024 (R+8.8) |
| NY | $55.2M | 53.5% | safe-D — Schumer / Gillibrand |
| WA | $45.0M | 41.1% | safe-D — Murray / Cantwell |
| **ID** | $6.6M | **85.8%** | safe-R — Crapo / Risch |

- **Senate echoes the House, louder.** Competitive **TX** Senate races drew **$253M — ~5× safe
  NY ($55M) or WA ($45M)**: at the statewide level, competition is the single biggest money
  magnet. Yet out-of-state share is high *everywhere* (41–54%) and is actually **highest in
  safe NY (53.5%)** — national donors fund high-profile safe senators (Schumer/Gillibrand) as
  readily as battlegrounds. Same lesson as the House: competition lifts the total, but the
  out-of-state flood is profile-driven and pervasive.
- **Idaho extends the pattern to the bottom of the size distribution — most sharply of all.**
  ID's federal candidates drew **$11.5M** total inflow (House $4.9M, all in the safe bands;
  Senate $6.6M) — ~1/20th of Texas — yet its **Senate money is 85.8% out-of-state, the highest
  of the four** (WA 41%, TX 45%, NY 54%), and its House inflow lands only in Likely/Solid (no ID
  tossup exists). A small, safe, deep-red state's candidate money is *overwhelmingly*
  non-constituent: the "profile/incumbency pulls national money" mechanism operates at $6.6M
  even harder than at $250M — Crapo and Risch are safe, so almost none of their money needs to
  come from Idahoans. Nationalization is most extreme, not least, at the safe bottom.

- **Earmarks ARE attributed (verified — correcting an earlier caveat).** Conduit-routed
  (ActBlue/WinRed) money is **not** lost from these totals: FEC records each earmarked
  individual gift under the *candidate* committee as transaction type `15E` — **$194M for these
  candidates in 2024 alone, more than the $90M of direct `15` gifts** — and the inflow load
  captures it. The conduit-side `24T` records ($150M) are the *same money* seen from the conduit
  and are correctly excluded to avoid double-counting (`scripts/diag_earmark_inspect.py`).

- **Caveats.** House competitiveness = 2026 forecast bands on current districts; Senate banded by
  actual two-party result. WA contributes no congressional Tossups in the 2026 map (its
  competitive seats land in Lean/Likely). State-legislative money still excluded (federal only).

### F. The individual layer — who votes, who gives, and whether the donor skew is real (WA/NY/ID: donor skew F5 + giving→turnout F6)

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

**F5 — The donor age skew is cross-state and cross-partisan (NY + ID confirm WA), and the
donor class is less unaffiliated than the electorate.**

*Computed in `scripts/diag_cross_state_donor_representativeness.py` — the money-linked
individual layer extended from WA to the two states that now have a voter file + a
voter↔donor match (NY 308K, ID 48K; WA 382K). Generation is derived uniformly from birth year
(WA/NY `birthdate`, ID `age` snapshot) so the states are comparable; `voter_scores` is unused
(empty for NY/ID). Matched-donor share ÷ roll share per generation, RAW and inverse-propensity
re-weighted by P(matchable | generation). TX excluded (no voter file). *(When first written,
`voter_scores` was empty for NY/ID and the turnout-linked cuts were WA-only; that gap is now
closed — see F6.)*

| Generation | WA raw / rwt | NY raw / rwt | ID raw / rwt |
|---|--:|--:|--:|
| Silent | 1.86× / 1.81× | 1.87× / 1.82× | 2.01× / 1.96× |
| Boomer | 1.63× / 1.62× | 1.77× / 1.75× | 1.69× / 1.66× |
| Gen X | 1.19× / 1.21× | 1.07× / 1.09× | 0.96× / 1.00× |
| Millennial | 0.61× / 0.60× | 0.50× / 0.51× | 0.48× / 0.49× |
| Gen Z | 0.18× / 0.18× | 0.13× / 0.14× | 0.14× / 0.15× |

- **Defensible claim 1 — the age skew is a near-universal property of who gives.** In all three
  states the oldest cohort (Silent) is **~1.9–2.0× over-represented** among matched donors and
  the youngest (Gen Z) is **~0.13–0.18×** — a >10× old-to-young gradient that is essentially
  identical in a Democratic mega-state (NY), a swing-ish Pacific state (WA), and a deep-red small
  state (ID). And it **survives the matcher-bias correction everywhere** (the IPW reweight moves
  every ratio by ≤0.05): the WA white paper's answer — the skew is genuine, not an artifact of
  the (last, first-initial, zip5) uniqueness guard over-selecting older, rarer-named voters — now
  holds cross-state and cross-partisan. Donor concentration is likewise high and similar (Gini
  **WA 0.862 / NY 0.867 / ID 0.819**; ID lowest, matching its retail economy from Finding 1.
  ID here is the **FEC** voter↔donor match; the parallel *state*-Sunshine ID match in the
  donor-class companion gives a slightly lower 0.798).
- **Defensible claim 2 — the donor class is less unaffiliated and more Democratic-tilted than
  the electorate** (the party-of-record cut WA cannot do). Matched-donor registered-party vs the
  full roll:
  - **NY:** electorate **D 48% / R 22% / unaffiliated-or-other 30%** → donors **D 63% / R 21% /
    O 16%.** Donors are +15 pts more Democratic and half as unaffiliated — the "donor class older
    *and* more Dem" finding, confirmed at the person level.
  - **ID:** electorate **D 12% / R 63% / O 25%** → donors **D 19% / R 67% / O 14%.** Even in a
    deep-red state the donor pool is *more partisan than the electorate on both sides* (the
    unaffiliated quarter collapses to a seventh), and the Democratic share rises proportionally
    more (12→19%) than the Republican (63→67%).
- **Strongest objection.** The registered-party comparison mixes states with different party
  registration regimes (NY closed-primary registration vs ID's open system), so the *levels*
  aren't directly comparable across states — only the within-state donor-vs-roll *gap* is. And
  the match itself (Section F4) favors stable-address voters, who skew older and more partisan;
  the age IPW corrects the name-uniqueness channel but not residential mobility, so the age skew
  is an **upper bound** (as in WA). The direction and cross-state consistency are the robust part.

**F6 — Giving→turnout replicates cross-state under identical definitions: donors are
super-voters at ~1.6–1.8× the non-donor rate in all three voter-file states.**

*Computed in `scripts/diag_cross_state_giving_turnout.py` on `voter_scores` populated for
NY/ID (2026-07-19, `scripts/populate_ny_id_voter_scores.py`) with WA-identical definitions —
`is_super_voter` = voted 2022+ AND registered ≥8 years; `turnout_propensity` = the WA
step/history blend. This closes the F1/F3 gap flagged in F5: the earlier NY giving↔turnout cut
used a different metric ("3 of last 4 generals"), so the ratios weren't comparable. Now they
are.*

| State | Donors super-voter % | Non-donors | Ratio | Avg propensity (donor / non) |
|---|--:|--:|--:|--:|
| WA | 84.0% (343.9K) | 50.1% (4.70M) | **1.68×** | 0.953 / 0.748 |
| NY | 80.6% (308.0K) | 45.8% (13.23M) | **1.76×** | 0.883 / 0.658 |
| ID | 48.7% (47.8K) | 30.0% (982K) | **1.62×** | 0.890 / 0.851 |

- **Defensible claim.** The engagement gap between the donor class and the rest of the roll is
  a **constant of the system, not a state peculiarity**: with identical definitions the
  donor/non-donor super-voter ratio lands in a tight **1.62–1.76×** band across a blue
  mega-state, a Pacific vote-by-mail state, and a deep-red closed-primary state. Within the
  donor class the gradient is generational everywhere (donor super-voter rates: Silent/Boomer
  ~0.55–0.93 vs Gen Z ~0.03–0.17) — the "money-linked electorate" is the same doubly-selected
  (old + habitual) slice in all three states.
- **Strongest objection.** Association only — donors are pre-selected for civic engagement, and
  the matcher favors stable-address voters (who are also habitual voters), so the ratio blends
  behavior with selection in every state (consistently, which is why the *cross-state
  comparison* is informative even though the *level* is inflated). ID's absolute rates aren't
  comparable to WA/NY: its roll is a survivorship-biased current extract (who-decides-idaho
  §III) — the propensity floor is inflated (non-donor avg 0.851) and its 8-year-registration
  super-voter clause bites harder on a churned roll, which is why ID's levels sit lower while
  its *ratio* matches.

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
| **WA** | $198.7M | 43.8% | 5.4% | 50.8% |
| **NY** | $672.8M | 33.9% | 4.1% | 62.0% |
| **TX** | $526.5M | 54.1% | 2.6% | 43.3% |
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
     absolute dollars). NY is the dominant exporter (~$418M leaves); WA and ID are net
     importers relative to their own giving.
  3. **The magnet list is a clean battleground map — and Idaho rides along.** The out-of-region
     candidate committees funded broadly across the region are almost entirely Senate
     battlegrounds: **Warnock-GA ($30.0M, incl. ID $0.33M), Kelly-AZ ($19.9M, ID $0.42M),
     Ossoff-GA ($19.5M), Tester-MT ($13.2M, ID $0.40M), Harrison-SC ($11.8M)**, with Graham-SC,
     Perdue/Loeffler-GA, Gideon-ME, Rosen/Cortez Masto-NV and McConnell-KY close behind.
     **Georgia Senate races alone (Warnock + Ossoff + Perdue + Loeffler) drew ~$68M** from
     residents of the four states — none of whom can vote in Georgia. Idaho's contributions are
     small ($0.1–0.4M per race) but present across the same marquee list, and they **split both
     ways** — ID money shows up on the Democratic magnets (Warnock/Kelly/Ossoff/Tester) *and*
     the Republican ones (Graham, Perdue, Loeffler, McConnell), the only state here whose
     out-of-region giving visibly funds both parties' Senate battlegrounds. The Section-C
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
contribution to a WA/NY/TX/ID U.S. House district (2022–2026, $488M) is classified by a
keyword-on-employer sector and joined to the district's forecast band (Tossup<5 / Lean5–10 /
Likely10–20 / Solid≥20). "Competitive share" = (Tossup+Lean) ÷ sector total.*

| Sector | $ (House, 4 states) | Competitive share | Out-of-state share |
|---|--:|--:|--:|
| Real estate | $8.0M | **21.9%** | 32.1% |
| **Finance / Wall St** | $18.4M | **21.6%** | 44.4% |
| Law | $17.7M | 20.0% | 33.3% |
| Academia / public | $8.1M | 17.6% | 48.3% |
| Healthcare | $8.4M | 16.1% | 35.7% |
| **Energy** | $3.6M | **14.1%** | 26.6% |
| **Tech** | $7.1M | **11.6%** | 51.9% |
| *[all sectors baseline]* | $488M | *18.4%* | *~43%* |

<sub>Sector keyword map extended after a coverage audit (`scripts/diag_sector_coverage.py`)
surfaced major law firms, hedge funds, and tech names as unclassified; the additions lifted
classified dollars from ~14% to ~15% and left the pattern below intact.</sub>

- **Defensible claim.** The hypothesis is **partially borne out, with a twist.** Finance money
  does tilt toward competition (**21.6%** of its dollars to Tossup/Lean vs an 18.4% baseline),
  and **tech is the least competition-seeking sector (11.6%)**, with energy next (14.1%) — they
  do disproportionately fund safe seats. But the cleanest contrast is in *travel*, not band:
  **energy money is strikingly local** (only **26.6%** out-of-state vs ~43% baseline) — it funds
  its own state's (Texas) incumbents — while **tech money travels farthest (51.9% out-of-state)
  yet lands in safe seats** (national safe-D House members). Finance both travels (44%) and
  tilts competitive. So: Wall Street chases the marginal race somewhat; tech funds safe
  co-partisans at a distance; energy funds the home-state incumbent.
- **Strongest objection.** The effect is **modest and partly mechanical.** The competitive-share
  spread is only ~10 points (real-estate 22% to tech 12%), and tech (WA) and energy (TX)
  are concentrated in their home states, whose *own* House seats happen to be safe (Solid-D
  Seattle, Solid-R Texas) — so "tech/energy fund safe seats" is in part just "their in-state
  seats are safe," not a strategic preference for safety.
- **Caveat.** Even after extending the keyword map with the biggest missing law firms, hedge
  funds, and tech names (`scripts/diag_sector_coverage.py`), classified sectors are still a
  **thin slice — only ~14% of inflow dollars**; "retired / not-employed / blank" is 46.8% and
  "unclassified" 38.6%, and tech ($7.1M) and energy ($3.6M) volumes in these four states' House
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
recipient party from the committee→party map (97.9–100% of dollars resolvable per state),
favored party from the forecast margin. Four-state since 2026-07-19 — TX needed only its FEC
committee master loaded (data parity, no code change); the script is state-agnostic via
`cross_state_common.py`.*

A safe seat for one party is a longshot for the other, so we can ask which side the money
actually reaches. Almost all of it goes to the favored side, and the safer the seat, the
more lopsided the split. In New York the longshot party's share of House inflow falls from
74% in the lone tossup to 27% in Likely seats to just **5.5%** in Solid (≥20-point) seats;
Texas runs the same staircase from the other side (57.3% Tossup → 24.2% Lean → 14.0% Likely
→ **2.8%** Solid, on $159.9M), and Washington matches (24.6% Likely → **4.8%** Solid). Put
plainly: in a truly safe district the disadvantaged party's candidate raises about a nickel
on the dollar and the favored side takes the rest. (Caveats: this is money entering the
race, House only; leadership PACs tied to safe incumbents can pad the favored side;
"favored" is only meaningful once a seat is actually safe — in a real tossup the challenger
can out-raise the nominal favorite, which is why the tossup rows look inverted; and Idaho's
two districts carry too little money — $2.8M total — to read, its Solid row being a single
small district where one funded longshot flips the percentage.)

### K. State-level money — the first cut over the state-disclosure layer

*Computed in `scripts/cross_state_state_money.py` (state-agnostic via `cross_state_common.py`)
on the STATE-disclosure rows now in each state's `candidate_finance`: WA PDC (`PDC:` prefix),
NY BOE (`NY:`), TX TEC (`TX:`), ID Sunshine (`SUNSHINE:`). Every section above is federal;
this is the first analysis of the state layer. The apples-to-apples core is **state-HOUSE
candidate money** (every lower chamber is fully up each cycle; senates are staggered
heterogeneously), pooled over the 2022+2024 cycles (post-redistricting maps; 2026 is
in-cycle and excluded). Gap-filling mirrors the donor-side backfills: TX legislative party
and ALL of ID's office/district/party are resolved by joining filer names to the SoS
candidates roster (unique-party guard); ID resolves 65% of person-filer dollars, TX 59%
of legislative dollars.*

**What each state's system captures** (not the same universe — read before comparing):

| | WA (PDC) | NY (BOE) | TX (TEC) | ID (Sunshine) |
|---|---:|---:|---:|---:|
| Rows / $ | 1,559 / $151M | 20,349 / $1.73B | 19,416 / $5.17B | 2,067 / $55M |
| Cycles | 2018–2026 | 2014–2026 | 2014–2026 | 2020–2025 |
| Universe | legislative + curated locals **only** | full filer universe | full filer universe | full filer universe |
| Office labels | native | native (partial) | native (partial) | none → roster join |
| Party labels | native | native | mostly Unknown → roster join | none → roster join |

**K1 — The price of a house seat varies 26× across the four states.** Per-seat-per-cycle
candidate receipts (2022+2024): **TX $978K ≫ WA $253K > NY $138K > ID $37K**. Median
candidate raise: TX $85.5K ≈ WA $83.6K > NY $45.0K > ID $13.7K (TX's mean, $353K, is 4×
its median — no contribution limits produce a whale-candidate layer WA's capped system
lacks). A competitive TX house seat costs more than most **congressional** seats' inflow;
an ID house seat costs less than a WA school-board race.

**K2 — Does state money chase competitiveness the way federal money does (~2×, Section D)?
Only in the red states.** Per-district house-candidate $ by forecast band, with the
(Tossup+Lean)/Solid premium:

| Band ($/district) | WA | NY | TX | ID |
|---|---:|---:|---:|---:|
| Tossup | $0.99M | $0.30M | $3.52M | $0.37M |
| Lean | $1.28M | $0.23M | $2.13M | $0.23M |
| Likely | $1.16M | $0.18M | $1.65M | $0.17M |
| Solid | $0.93M | $0.31M | $1.68M | $0.13M |
| **Premium** | **1.12×** | **0.85×** | **1.72×** | **2.49×** |

- **Defensible claim.** TX and ID look federal-like (competitive seats draw ~1.7–2.5× the
  candidate money of safe ones), but **WA is nearly flat (1.12×) and NY inverts (0.85× —
  safe Assembly seats out-raise the battlegrounds per district).** The likely mechanism is
  visible in K5: in NY the battleground money runs through the **party campaign committees**
  (DACC/DSCC/NYSSRCC/RACC are 4 of NY's top-10 filers, $33–43M each) rather than through
  candidate committees, and safe-seat incumbents (leadership, chairs) raise heavily anyway;
  the candidate-committee lens undercounts exactly the competitive spending NY routes
  around it.
- **Strongest objection.** The forecast bands are 2026 labels applied to 2022+2024 money
  (bands are stable, but not identical, across cycles); WA's Lean band holds a single
  district; and NY's office classification is partial — if BOE office-coding is biased
  toward incumbents, safe-seat money is inflated. Read the WA/NY numbers as "no large
  candidate-level premium," not as precise ratios.

**K3 — State-legislative money mirrors chamber control, hard.** Democratic share of
party-resolved legislative receipts (2022+2024): **NY 74.8% D, WA 60.9% D, TX 27.4% D,
ID 23.5% D.** Unlike federal inflow (which both parties export to the same national
battlegrounds), state money stays home and tracks who holds/contests the chamber.
(TX carries $130M party-unresolved after the roster join; ID resolves 65% of person-$ —
directional reads only for those two.)

**K4 — State legislatures are PAC-funded; Congress is individual-funded.** Individual
share of legislative candidate receipts (2022+2024): **WA 31.4% (PACs 62.4%), TX 35.8%
(entities 64.2%), NY 38.2% (PACs 29.5% + party/other transfers 32.3%), ID 49.9%.** The
federal benchmark from the same DBs: House candidate committees run **~65% individual /
16–25% PAC** (WA H 64.6%/25.3% on $104M; NY H 67.2%/15.7% on $369M). The individual
small-donor era documented in Sections A–I is a *federal* phenomenon — statehouse
campaigns are still funded chiefly by organized money. (TEC's split is
individual-vs-entity by construction; "PAC" there means all non-individual money.)

**K5 — The panorama: what the full filer universe shows (NY/TX/ID; WA can't).**
- **TX:** Texans for Greg Abbott has raised **$424.5M across 6 cycles** — 1.4× the entire
  TX House candidate universe over 2022+2024 combined. ActBlue Texas ($168.6M) and Dan
  Patrick ($106.9M) follow; Texans for Lawsuit Reform ($105.5M) is the biggest
  non-candidate PAC. Org-name filers hold 2/3 of all TX state money ($2.9B vs $1.5B).
- **NY:** Hochul $68.5M and Cuomo $48.7M top the list, but the signature is the
  **committee layer**: the state Democratic Committee, both Senate campaign committees,
  and three union PACs (NYSUT, SEIU, UNITE HERE) occupy most of the top 10.
- **ID:** the top filer is a **ballot-measure committee** (Idahoans for Open Primaries,
  $5.6M — more than any Idaho candidate; the sitting governor raised $1.2M over 3 cycles),
  and orgs hold 2/3 of ID state money. Consistent with Section F5's picture of a small
  retail donor base: even Idaho's biggest money fights are initiative fights, not
  candidate fights.
- **WA (caveat):** the PDC load covers legislative + curated local candidates only — no
  statewide execs, party committees, or PACs — so WA appears in K1–K4 but has no panorama
  row. Loading the full PDC filer universe is the natural follow-on.

---

## Limits of inference

*Full provenance + a no-AI reproduction recipe (every source, access path, and the exact
scripts behind each figure): [Data Sources & Reproducibility](data-sources-and-reproducibility.md).*

- **Both directions now exist (Findings 1–5 + Tests A–D are outflow; Tests E–I add inflow).**
  The early findings measure where residents *send* money (outflow by donor residence); the
  recipient-anchored inflow load (Sections E–I) measures money *entering* WA/NY/TX/ID races. The
  cross-state matrix (G) reports both. They use different committee universes, so read shares
  within each rather than subtracting one from the other.
- **Sections A–J are federal; K is the state layer.** State-legislative and local money is
  loaded for all four states (WA PDC, NY BOE, ID Sunshine, TX TEC — item 7) and Section K is
  the first cut over it. The two layers use different disclosure regimes and filer universes
  (WA's is legislative-candidates-only) — compare *within* K, not K against A–J dollar
  figures.
- **Conduit-*reliance* metric is unreadable (but the money is captured).** ActBlue/WinRed
  appear as recipients of <0.5% of dollars — because, as the 2024 earmark inspection confirmed
  (Section E), FEC records each earmarked gift under the *candidate* committee as type `15E`,
  not under the conduit. So you cannot measure conduit *usage* from the recipient field — but
  the **money itself is fully captured** (under the candidates). **Do not read the
  ActBlue/WinRed-as-recipient share as "conduit reliance."** The sub-$200 *amount* share
  (Finding 1) is computed from the dollar value and is unaffected.
- **Donor proxy.** name+zip5 over-merges common names, modestly understating donor counts and
  overstating concentration.
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
3. **Individual voter-file study — DONE, WA + cross-state donor layer** (Section F): WA has the
   full stack (turnout-by-age F1, donor representativeness F2 with matcher-bias re-weighting,
   giving↔turnout F3). **F5 (2026-07-19) extends the donor-representativeness cut to NY + ID**
   (voter files + matches now loaded): the donor age skew is near-identical and survives the IPW
   correction in all three, and the party-of-record cut shows donors less unaffiliated / more
   Dem-tilted in NY and ID. **F6 (2026-07-19) closes the turnout half**: NY/ID `voter_scores`
   populated with WA-identical definitions (`scripts/populate_ny_id_voter_scores.py` — NY 13.54M
   rows from the parsed history, ID 1.03M from the melted participation table), and the
   giving→turnout cut replicates at a near-constant donor/non-donor super-voter ratio
   (WA 1.68× / NY 1.76× / ID 1.62×). The individual layer is now complete for all three
   voter-file states.
4. **Cross-state flow matrix — DONE, now four-state** (Section G): inflow provenance + outflow
   destination + the systematic out-of-region magnet list (Georgia Senate ~$68M from
   WA/NY/TX/ID residents). ID is the biggest out-of-region exporter (68%) and the only net
   candidate-money importer.
5. **Sector × competitiveness — DONE** (Section H): finance tilts mildly competitive; tech/energy
   fund safe seats; energy money is distinctively local. Modest, on a thin classified slice.
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
9. **State-level money analysis — DONE 2026-07-19** (Section K,
   `scripts/cross_state_state_money.py`): first cut over the state-disclosure layer loaded in
   item 7. Headlines: house seats cost 26× more in TX than ID; the federal ~2× competitiveness
   premium holds only in TX/ID (WA flat, NY inverted — party committees route around candidate
   committees); statehouse money is PAC-funded (~31–38% individual) vs Congress's ~65%
   individual; TX/ID's biggest state-money filers are a governor's committee ($424.5M) and a
   ballot-measure committee respectively. Follow-on: load the full WA PDC filer universe
   (party cmtes/PACs) so WA gets a J5 panorama row.
