# The Donor Class Is Not the Electorate

### Who funds elections in Washington, New York, and Idaho — old, concentrated, and (where party is observable) skewed toward Democrats in a blue state *and* a red one — measured from individual voter-to-donor matches

**Stephen Kirby** · Tikor Consulting · July 2026

*AI-assisted drafting and analysis review. All figures are reproducible from
public-record data available through lawful request and from the open-source scripts
cited below, including `scripts/verify_donor_class.py` and
`scripts/diag_contribution_limits.py`. The paper source, code, and data-acquisition
recipe are public at <https://github.com/skirby359/who-decides>; the underlying voter
files are not redistributed. Contact: kirby@tikorconsulting.com.*

*Paper #3 of the electoral-health series (companion to
[`who-decides-washington.md`](who-decides-washington.md),
[`who-decides-new-york.md`](who-decides-new-york.md),
[`who-decides-idaho.md`](who-decides-idaho.md),
[`safe-seat-washington.md`](safe-seat-washington.md), and
[`cross-state-fec-money.md`](cross-state-fec-money.md)). **DRAFT — pending the
independent-verification gate in [`publication-checklist.md`](publication-checklist.md).***

*Provenance. Each panel is built by a per-state match script run once per money source
(`--source fec` / `--source state`), writing to `voter_donor_affiliation_fec` and
`voter_donor_affiliation_state`; `scripts/verify_donor_class.py` re-derives both from
scratch SQL. Washington figures: `scripts/match_wa_voters_to_donors.py` and
`scripts/diag_wa_individual_findings.py` —
WA's registered roll (5.51M) + 27.1M vote records + birthdates
(`data/wa_vrdb.duckdb`), matched to 172,998 federal and 269,204 state donors. New York
figures: `scripts/match_ny_voters_to_donors.py`,
`scripts/backfill_ny_committee_party.py`, `scripts/diag_ny_match_bias.py`,
`scripts/diag_ny_primary_participation.py`, `scripts/diag_ny_donor_extras.py`,
`scripts/diag_ny_electorate_extras.py` — NY's NYSVOTER roll (13.54M;
individual party enrollment + DOB; `data/ny_vrdb.duckdb`) matched to 10.02M FEC
itemized contributions (`data/ny_statewide.duckdb`, 307,841 voters). Idaho
figures: `scripts/match_id_voters_to_donors.py`,
`scripts/backfill_id_recipient_party.py`,
`scripts/diag_id_electorate_extras.py` — ID's statewide roll (1.03M; individual
party affiliation + age; `data/id_vrdb.duckdb`) matched to both Idaho Sunshine **state**
filings (27,250 voters) and **federal** FEC contributions (27,196 voters), in
`data/id_statewide.duckdb`. Cross-state
dollar concentration: `scripts/cross_state_fec_money.py`. Contribution-limit tests
(Appendix G): `scripts/diag_contribution_limits.py`. Each figure below traces to one
of these scripts.*

*Two panels, read this first. American donors give into two separate money systems
governed by different rules, and a voter roll can be matched to either. Every finding
below is therefore computed **twice**, once per system, and never pooled:*

| panel | what it is | states |
|---|---|---|
| **Federal** *(primary)* | FEC itemized individual contributions | WA, NY, ID |
| **State** *(secondary)* | WA Public Disclosure Commission filings; Idaho Sunshine filings | WA, ID |

*The federal panel is the spine because it is the one comparison available in all three
states under a single rule set. New York appears only there: it publishes no itemized
state contributions (Board of Elections money is disclosed in summary form), so no NY
state panel can be built. Pooling the two systems — which earlier drafts did for
Washington without intending to — inflates measured concentration, because one person's
federal and state giving stacks into a single donor total while a one-system donor's does
not; on Washington's data, pooling reads 46.6% top-1% against 42.4% federal and 43.8%
state. The panels are kept separate for exactly that reason.*

*This is a strength, not a limitation. Federal and state money are capped differently,
solicited by different campaigns, and reported by different agencies. **Every finding in
this paper holds in both** — the donor class is old, top-heavy, metro-concentrated,
partisan-skewed, and stacked with high turnout whether the money is federal or state.
Where the panels differ, they differ informatively: the federal donor class is markedly
older than the state one (in Idaho, 64.7% of federal donors are 65+ against 51.1% of state
donors), and Idaho's federal recipients can be party-resolved at 86.7% against ~52% for
its state filings.*

## Abstract

Campaign money is usually described by how much is raised. This paper asks whose money
it is, and whether the people who fund elections resemble the people who vote in them.
Three state voter-registration files — Washington (5.51M registrants), New York (13.54M,
with individual party enrollment and date of birth), and Idaho (1.03M, with party
affiliation and age) — are linked person by person to itemized campaign contributions
under a conservative uniqueness rule. Because American donors give into two separately
regulated money systems, every result is computed twice and never pooled: a federal
panel (172,998 matched donors in Washington, 307,841 in New York, 27,196 in Idaho) and a
state panel (269,204 in Washington, 27,250 in Idaho). Every finding holds in both. The
matched donor class is markedly older than the electorate that elects the officials it
funds: 47.9% of New York's federal donors and 64.7% of Idaho's are 65 or older, against
a quarter and a third of their rolls, and Washington's Silent Generation gives at 2.6
times its share of the roll while Generation Z gives at one-tenth of its own. Money
concentrates sharply, with the top 1% of matched donors supplying 42.4% of federal
dollars in Washington, 51.2% in New York, and 35.8% in Idaho, and a single metropolitan
area supplying a third to a half of each state's total. Where party of record is
observable, the donor class over-represents registered Democrats and under-represents
the unaffiliated by double digits — in deep-blue New York (+15.0 points Democratic) and
in deep-red Idaho (+8.0) alike, so the tilt is not an artifact of a state's majority
party. The same individuals also vote at far higher rates than non-donors, stacking
financial and electoral voice rather than offsetting them. The age skew survives
inverse-propensity re-weighting for match bias, and hand rating of a 150-record sample
puts match precision near 90%. Contribution caps do not explain the cross-state
differences in concentration. The paper measures itemized giving and registration
records, not policy influence, and its causal claims are limited to association.

**Keywords:** campaign finance; political donors; voter files; record linkage; party of
record; contribution limits; donor concentration; Washington; New York; Idaho.

---

## The question

Campaign money is usually described by *how much* is raised. The more
consequential question for representation is *whose* money it is — and whether
the people who fund elections look anything like the people who vote in them. If
the donor class is a representative cross-section of the electorate, money is
just amplified participation. If it is a narrow, unrepresentative slice, then a
distinct and self-selected population is setting the financial terms of every
race before the first ballot is cast.

This question can be answered at the individual level in three states, by matching the
registered-voter roll to itemized donors, person by person (a conservative name +
ZIP match; see Appendix C). Washington supplies the demographic and
behavioral cut; **New York and Idaho — which, unlike Washington, publish each
voter's party — supply the dimension WA cannot: who the donor class is
*partisan*-ly, and where its money goes.** And they bracket the political
spectrum: New York is ~48% registered Democratic, Idaho ~63% registered
Republican.

The short answer, consistent across all three states: **the donor class is not the
electorate.** It is markedly older, geographically and financially concentrated
in a small top tier, and — where party is observable — skewed toward Democrats
while nearly excluding the largest non-partisan bloc. The striking part is that
the Democratic tilt of the donor class relative to the electorate appears in
deep-blue New York **and in deep-red Idaho**: it is not an artifact of a state's
majority party.

---

## Finding 1 — The donor class is old, and the skew is real

In all three states matched donors are far older than the voters they fund.

**New York** (`match_ny_voters_to_donors.py`) — age-band share, age as of
2024-11-05:

| age band | matched donors | all active voters | 2024 GE voters |
|---|--:|--:|--:|
| 18–29 | **3.0%** | 18.0% | 14.1% |
| 30–44 | 14.2% | 25.6% | 23.1% |
| 45–64 | 34.9% | 31.2% | 34.6% |
| 65+ | **47.9%** | 25.2% | 28.2% |

Nearly **half of NY's federal donors are 65 or older**, versus a quarter of the
active roll. **Washington** shows the same shape as generation multipliers
(donor share ÷ roll share), and the skew is sharper in federal money than in state:

| generation | federal panel | state panel |
|---|--:|--:|
| Silent | **2.56×** | 1.64× |
| Boomer | 1.97× | 1.51× |
| Gen X | 0.98× | 1.26× |
| Millennial | 0.39× | 0.68× |
| Gen Z | **0.10×** | 0.20× |

**Idaho** replicates it in a third state, in both money systems (age here is
current-roll age, not election-time DOB, so bands are read against the current roll):

| age band | federal donors | state donors | all voters | 2024 GE voters |
|---|--:|--:|--:|--:|
| 18–29 | **1.4%** | 2.6% | 15.2% | 13.1% |
| 30–44 | 7.1% | 13.1% | 22.8% | 22.4% |
| 45–64 | 26.8% | 33.2% | 30.9% | 31.9% |
| 65+ | **64.7%** | 51.1% | 31.0% | 32.6% |

**Nearly two-thirds of Idaho's federal donors are 65+**, and more than half of its
state donors — against a third of the roll, with the under-30 share reduced to 1.4%
and 2.6% respectively. The donor class is the grayest slice of the electorate in blue
and red states alike.

Note the consistent gap between the panels: in both Washington and Idaho, **federal
money is older money**. State-level giving reaches Gen X and Millennials at roughly
twice the rate federal giving does (WA Gen X 1.26× vs 0.98×, Millennial 0.68× vs 0.39×).
The generational narrowing is most extreme in exactly the layer where the most money
moves.

**The skew is not a matching artifact.** The obvious objection is that the match
key (last name + first name + ZIP5, required to be *unique* on the roll) selects
older, rarer-named, stable-address voters. Tested directly in the two states where
the re-weighting was run (WA and NY), it does not: the probability a voter is
uniquely matchable is **nearly flat across age** — NY **94.5–95.4%** across the
four bands (0.9-pt spread, `diag_ny_match_bias.py`); WA **96.3–97.6%** across
generations (1.4-pt spread). Inverse-propensity re-weighting therefore **does not
move the distribution**: NY's 65+ donor share goes 47.9% → **47.9%** (0.0-pt
shift), and every Washington generation multiplier is **unchanged to two decimal
places in both panels**. The age
skew is a property of who *gives*, not of who the matcher can *find*. (Idaho uses
the identical conservative matcher but was not separately re-weighted; its 65+
donor shares are reported without that adjustment.) Appendix F carries the full
validation.

---

## Finding 2 — The donor class is whale-dominated

Money concentrates at the very top of the matched-donor distribution, in every state
and in both money systems:

| panel | matched donors | matched $ | top 1% → share of $ | top 10% | Gini |
|---|--:|--:|--:|--:|--:|
| **Federal** | | | | | |
| Washington | 172,998 | $420.3M | **42.4%** | 74.8% | 0.820 |
| New York | 307,841 | $1,196.1M | **51.2%** | 81.4% | 0.867 |
| Idaho | 27,196 | $49.6M | **35.8%** | 70.4% | 0.786 |
| **State** | | | | | |
| Washington (PDC) | 269,204 | $153.9M | **43.8%** | 76.0% | 0.827 |
| Idaho (Sunshine) | 27,250 | $15.9M | **39.3%** | 70.8% | 0.798 |

*Estimator: donors are ranked by total matched dollars and split into 100 equal-count
buckets (`NTILE(100)`); "top 1% / 10%" is the top 1 / 10 buckets' dollars ÷ all matched
dollars. Appendix C gives the full definition and the reason equal-count buckets are
used; Appendix E gives the bootstrap confidence intervals.*

Two readings. Within the federal panel the ordering is **New York > Washington > Idaho**
— the same ranking the statewide all-donor figures give, so it is not an artifact of who
the matcher can find. And in *both* states that have both panels, the **state** layer is
slightly *more* concentrated than the federal one (WA 43.8% vs 42.4%; ID 39.3% vs 35.8%),
even though state contributions are capped far lower. Appendix G takes that up directly.

A geographic corollary everywhere. In WA, **63.4%** of federal matched-donor
dollars come from just two Seattle-metro ZIP3s (981xx 37.3% + 980xx 26.1%); the state
panel is a little broader at 55.1% (981xx 32.3% + 980xx 22.8%). NY is
the most concentrated: **Manhattan (New York County) alone supplies 50.3%** of
matched-donor dollars, ZIP3 100 = 46.3%, and the top three ZIP3s (Manhattan +
Westchester + Brooklyn) = **63.4%** (`diag_ny_donor_extras.py`). Idaho shows the
same single-metro dominance from a state with no large city: **Ada County (Boise)
supplies 49.2%** of state matched-donor dollars from 10,037 donors, and 36.4% of federal
dollars from 10,338 — the money mirror of Seattle and Manhattan. Idaho's federal money is
the one case where a second center appears: resort-county **Blaine (Sun Valley) supplies
11.7%** of federal dollars from 1,097 donors — 4.0% of Idaho's federal donors carrying
nearly three times their weight in dollars.

(Idaho is the least concentrated of the three in both panels, and its statutory
per-election caps do visibly bind — 6,797 itemized state gifts land on exactly $1,000,
against 448 at $750. The caps are nonetheless not what makes Idaho less concentrated:
Idaho is the least top-heavy inside the *federal* layer too, under the same federal
limits as Washington and New York, and its far more tightly capped state layer is *more*
top-heavy than its federal one, not less. Appendix G runs the test; Appendix D carries
the statutes and the literature.)

At the statewide level (all itemized donors, not only those matched to a voter), the
same top-heaviness appears across all four states loaded — the top 1% of donors supply
**39.3%** of federal dollars in WA, **47.5%** in NY, **41.7%** in TX, and **36.0%** in ID
(`cross_state_fec_money.py`). Texas enters here and nowhere else in this paper: no Texas
voter file has been obtained, so Texas money can be described in aggregate but cannot be
matched to individual voters. The "small-dollar democratization" narrative coexists with
a money system whose itemized dollars are dominated by a thin top stratum and a single
metro.

---

## Finding 3 — The donor class is partisan-skewed toward Democrats (New York *and* Idaho)

This is the cut Washington cannot supply. Using each donor's **own** NY party
enrollment (100% present), the donor class over-represents registered Democrats
and **nearly excludes the unaffiliated**:

| party | matched donors | donor share | registration | **skew** | matched $ | $ share |
|---|--:|--:|--:|--:|--:|--:|
| DEM | 193,355 | 62.8% | 47.8% | **+15.0** | $849.2M | 71.0% |
| REP | 65,898 | 21.4% | 22.3% | −0.9 | $197.2M | 16.5% |
| NOPARTY (blank) | 38,601 | 12.5% | 25.5% | **−13.0** | $126.8M | 10.6% |
| OTHER (minor) | 10,178 | 3.3% | 4.4% | −1.1 | $22.8M | 1.9% |

Registered Democrats are +15 points over their share of the roll and supply
**71% of matched dollars**; Republicans give roughly in proportion; and NY's
"blank" (no-party) enrollees — **a quarter of all registrants** — are only an
eighth of donors. The donor class is not a scaled-down electorate but a
partisan-skewed slice that runs *against* the largest non-partisan bloc.

**Where the money goes — crossover.** After resolving recipient party for 79% of
contributions via the bulk FEC committee + candidate masters
(`backfill_ny_committee_party.py`):

| own party | donors (resolved) | → Democratic | → Republican | mixed |
|---|--:|--:|--:|--:|
| DEM | 174,156 | **94.4%** | 3.9% | 1.7% |
| REP | 57,330 | 14.2% | **82.6%** | 3.1% |
| NOPARTY | 30,568 | **65.6%** | 31.0% | 3.4% |
| OTHER | 8,268 | 40.8% | 57.0% | 2.2% |

Two patterns: registered **Republicans fund Democrats at ~3.6× the rate
Democrats fund Republicans** (14.2% vs 3.9%) — a deep-blue donor ecosystem; and
the unaffiliated bloc, invisible to registration-based analysis, **leans ~2:1
Democratic in its actual giving** (65.6% → D), so NY's independents are not
centrist by behavior.

**Idaho — the same skew, in the reddest state, in both money systems.** The decisive
test of whether the Democratic tilt of the donor class is real or just a blue-state
artifact is to run it in a state where Republicans hold a 5:1 registration edge. Using
each donor's own Idaho affiliation, in each panel separately:

| party | registration | federal donor share | **skew** | state donor share | **skew** |
|---|--:|--:|--:|--:|--:|
| REP | 62.9% | 66.7% | +3.8 | 66.5% | +3.6 |
| DEM | 11.8% | 19.9% | **+8.0** | 20.9% | **+9.1** |
| UNAFF (unaffiliated) | 23.9% | 12.7% | **−11.2** | 12.0% | **−11.8** |
| OTHER (minor) | 1.4% | 0.8% | −0.6 | 0.6% | −0.8 |

Dollar shares track the same way — Republicans supply 68.1% of federal and 71.1% of
state matched dollars, Democrats 21.1% and 20.6%, the unaffiliated 10.3% and 8.0%
(federal $49.6M across 27,196 donors; state $15.9M across 27,250).

Republicans supply the plurality of Idaho's money, as a 63%-Republican state must
— but relative to their numbers the **most over-represented donors are registered
Democrats** (+8.0 federal, +9.1 state, well over half again their share of the roll),
and the unaffiliated quarter is the most *under*-represented in both (−11.2, −11.8). The
same directional finding as New York, from the opposite end of the spectrum, and it does
not depend on which money system is examined: the donor class leans
Democratic-of-the-electorate and runs against the unaffiliated, whether the electorate
around it is blue or red and whether the money is federal or state.

**Crossover (Idaho).** The two panels differ sharply in how well recipient party can be
resolved, and this is where the federal panel earns its place as the spine. Idaho
Sunshine carries no party on the recipient, so for the state panel recipient party must
be reconstructed from the Secretary of State candidate roster plus party/committee name
patterns (`backfill_id_recipient_party.py`), resolving only ~52% of matched donors. The
federal panel needs no reconstruction — the FEC committee and candidate masters carry
party directly — and resolves **86.7%**, comparable to New York's 79%.

| own party | federal: donors | → D | → R | state: donors | → D | → R |
|---|--:|--:|--:|--:|--:|--:|
| DEM | 5,037 | **96.5%** | 2.8% | 3,365 | **93.5%** | 4.0% |
| REP | 15,579 | 17.6% | **81.5%** | 9,420 | 18.8% | **79.3%** |
| UNAFF | 2,819 | **74.0%** | 24.5% | 1,303 | **72.8%** | 24.5% |
| OTHER | 139 | 19.4% | 79.1% | 59 | 18.6% | 81.4% |

The two direction-safe patterns from New York replicate in both panels: registered
**Democrats are near-monolithic donors** (96.5% → D federal, 93.5% state, against NY's
94.4%), and **unaffiliated donors lean Democratic** in their actual giving (roughly 3:1
in Idaho, 2:1 in New York) — independents are not centrist by behavior in either state.

The Republican→Democratic rate is the one figure that needs a caveat, and only for the
state panel: there the unresolved recipient pool (local Republican candidates and
R-aligned PACs absent from the roster) skews Republican, so Republican donors'
Republican-side giving is disproportionately the untraced part, making 18.8% an **upper
bound**. On the federal panel, with 86.7% resolved from authoritative party labels, the
17.6% figure carries no such hedge — and it lands within a point of the state panel's
upper bound, which suggests the state reconstruction was not badly biased after all.

**In-state vs out-of-state, by party.** Money flowing *into* NY's federal races
(`fec_inflow.duckdb`, all-state donors → NY candidates; `diag_ny_donor_extras.py`)
is **44.8% out-of-state for both parties** — nationalization is party-symmetric
at the aggregate, consistent with the cross-state finding that out-of-state
share is uniform across competitiveness (`cross-state-fec-money.md` §G). The one
asymmetry is by office: NY's **Senate Democrats draw 54.1% of their money from
out-of-state** (Schumer/Gillibrand as national magnets) versus ~43–45% for House
candidates of both parties. So the donor class is partisan-skewed in *who it is*
(§3 above) but not in *how far its money travels* — except at the marquee Senate
tier.

**The skew holds in every kind of district.** Mapping matched donors to their
congressional district's competitiveness (`diag_ny_electorate_extras.py`), the
donor pool's Democratic share **exceeds the registered Democratic share in every
band** — Tossup 57.7% donor vs 40% registrant, Solid 71.6% vs 56% — so the
donor class is more Democratic than the electorate not just statewide but
locally, regardless of how contested the seat is. And **two-thirds of donors
(205K of 308K) live in Solid districts** (mostly Solid-D Manhattan): the money
originates in safe seats, consistent with the cross-state finding that safe
seats supply most of it. Idaho shows the same safe-seat origin from the red side:
the great bulk of matched Idaho donors sit in Solid-R legislative districts (where
the donor pool is 71% Republican), while the handful of more competitive districts
carry a far more balanced donor mix (~46% Republican / ~34% Democratic)
(`diag_id_electorate_extras.py`) — the money, in both states, originates
overwhelmingly in the seats that are not in doubt.

---

## Finding 4 — Financial voice and electoral voice stack on the same people

In both states, the people who give are the people who reliably vote, and it holds in
both money systems. In Washington, federal matched donors are **85.4% super-voters
versus 51.4%** of non-donors (mean turnout propensity 0.966 vs 0.754); the state panel
is nearly identical at **84.9% versus 50.8%** (0.950 vs 0.751). In New York, matched
donors voted in **3.03 of the last four federal generals on average versus 1.78** for
non-donors, and **73.0% are super-voters (≥3 of 4) versus 37.1%**. The same individuals
concentrate *both* forms of influence rather than one offsetting the other. (Association
only — donors are pre-selected for engagement, so reverse causation is equally
plausible; the benign "donating as a gateway to participation" reading is fully live,
and is treated as objection 3 in Appendix A.)

A closed-primary corollary at the nominating stage, in both party-of-record
states. NY's **closed** primaries restrict each party's primary to its enrollees,
so the **25.3% enrolled "blank" are excluded by law** (≈0.1–0.6% primary
participation), and in blue NY the Democratic primary is frequently the decisive
contest (2021 odd-year DEM 16.9% vs REP 5.0%). Idaho is the mirror image: its
**closed Republican primary is the decisive contest** in nearly every seat
(80–86% of all primary ballots are Republican; see
[`who-decides-idaho.md`](who-decides-idaho.md)), and the unaffiliated quarter is
excluded in practice — **6.6% primary participation vs 83% in the November
general**. The population that nominates is small and party-gated in both states —
and, per Finding 3, funded by a donor class narrower and more skewed still.

---

## What this paper does not claim, and limits

- **The match is a proxy, and a floor.** Voter↔donor identity rests on (last, first,
  ZIP5) uniqueness, not a shared identifier. It is conservative by design (ambiguous
  keys are dropped, not guessed), so the matched set is a **floor**, not a census, of
  the donor population. Hand rating of 150 matched records puts apparent precision at
  **≈90%** (Appendix F).
- **Itemized giving only, and two panels never pooled.** Sub-$200 unitemized
  giving is invisible, so the *small-dollar* end is undercounted — which, if
  anything, **understates** the concentration in Findings 1–2. Federal and state money
  are reported as separate panels (Appendix C); dollar magnitudes are comparable within
  a panel, not across them, and New York has no state panel to compare.
- **Composition, not rates.** All three matches use the current roll, so turnout
  *rates* for older cycles are biased by survivorship. Share-of-population figures,
  which need no denominator, carry the findings. Idaho's age is a current-roll
  integer, so its bands are current-age, not election-time.
- **Recipient party is partial in one panel.** The crossover cut resolves 79% of NY
  contributions and **86.7%** of ID federal matched donors, but only ~52% of ID *state*
  donors, where recipient party has to be reconstructed rather than read off a filing —
  so the majority-party crossover rate on Idaho's state panel is an upper bound. Own-party
  and age cuts use the 100%-present party of record throughout.
- **No policy-influence claim.** This paper measures who gives and who votes. It does
  not measure whether money changes votes, wins elections, or moves policy, and the
  giving↔turnout relationship in Finding 4 is reported as association only.
- **Contribution limits are not the mechanism** behind Idaho's lower concentration
  (Appendix G), and no causal claim is made in either direction about what caps do to
  a donor pool.

Appendix A states each objection in full, with the bound on it.

---

## What it means

Across three states that differ in size, partisanship, and election administration —
and across two separately regulated money systems within them — the population that
finances campaigns is the same kind of
population: **old, top-heavy, geographically concentrated, and — where party is
observable — skewed toward Democrats relative to the electorate and away from the
unaffiliated.** That every finding survives the federal/state split is the strongest
evidence here that it describes donors rather than a quirk of one disclosure regime: the
two systems cap contributions differently, are solicited by different campaigns, and are
reported to different agencies, yet produce the same donor class. New York and Idaho's
party-of-record turns the Washington finding
from "the donor class is demographically unrepresentative" into the sharper,
falsifiable claim that it is *also* partisan-unrepresentative in a specific
direction — and, critically, in the **same** direction in a deep-blue and a
deep-red state, so the Democratic tilt is a property of who donates, not of a
state's majority party. Combined with the turnout and safe-seat papers, the
picture is a series of narrowing filters between the registered population and
actual influence — who votes, who votes in the decisive primary, and who pays —
each one older and less representative than the last. This is the evidentiary core
of the electoral-health series' "donor class ≠ electorate" finding, now resolved
by party across the spectrum.

---

# Appendices

## Appendix A — The objections, in full

The strongest objections to this paper are about the *match*, not the findings, and
three of the four are testable. Each is stated at full strength, then bounded.

**1. The matcher selects old people, so the age skew is manufactured.** The match key
requires a (last name, first name, ZIP5) triple that is *unique* on the roll. Rare
names, stable addresses, and long tenure all correlate with age, so the objection is
that Finding 1 measures matchability rather than giving. This is the one objection that
can be tested head-on, and it fails: the probability that a voter is uniquely matchable
is nearly flat across age (NY 94.5–95.4% across four bands; WA 96.3–97.6% across five
generations), so inverse-propensity re-weighting does not move the distribution — NY's
65+ donor share is unchanged at 47.9%, and every Washington generation multiplier is
unchanged to two decimal places in both panels. A selection mechanism that flat cannot
produce a 2.5× senior over-representation. Full tables in Appendix F.

**2. Household false-merges inflate individual donors.** Because the key is surname plus
ZIP, a married couple sharing both can collapse into one matched voter, attributing a
spouse's giving to their partner. Hand rating of a 150-record sample (2026-07-10, two
review rounds) found this to be the dominant error mode, at ≈90% apparent precision
(15/150 flagged on the second, more thorough pass; 9 on the first). Its effect on the
findings is small by construction: the mis-attributed partner shares household, ZIP, and
typically similar age, so the age, geography, and concentration cuts move very little.
Some flags were unverifiable for missing donor detail, so true precision may be slightly
higher.

**3. Donors vote more because donating is a gateway to participation, not because the
same elite holds both forms of voice.** Finding 4 is an association, and the causal arrow
is genuinely ambiguous: donors are pre-selected for engagement, and a first contribution
plausibly *increases* subsequent turnout. Nothing here distinguishes the two readings,
and the benign one is fully live. What survives either reading is the descriptive point,
which is all Finding 4 claims: the two forms of influence sit on the same people rather
than on complementary populations.

**4. Idaho's crossover rate overstates Republican defection.** Recipient party in Idaho is
reconstructed rather than published, and resolves only ~52% of matched donors. The
unresolved pool — local Republican candidates and R-aligned PACs absent from the
Secretary of State roster — skews Republican, so Republican donors' Republican-side
giving is disproportionately the untraced part. The 18.8% Republican→Democratic figure is
therefore an upper bound, and no cross-state claim is made about majority-party
crossover. The two patterns that *are* claimed (near-monolithic Democratic loyalty;
unaffiliated donors leaning Democratic) are robust to the unresolved pool because it
cannot plausibly reverse them.

**5. Itemization hides the small-dollar end, so concentration is overstated.** Sub-$200
giving is unitemized and therefore invisible here. This objection runs the wrong way for
the paper's conclusion: adding the missing small-dollar mass to the denominator would
*lower* every top-1% share, but it would also add the population the findings describe as
absent. As reported, the concentration figures describe the *itemized* universe, and the
direction of the bias is toward understating how thin the top stratum is relative to all
givers.

**6. State contribution caps, not donor behavior, explain Idaho's flatter distribution.**
This was the paper's own earlier explanation, and Appendix G shows it does not survive
testing. It is retained here as an objection because it is the intuitive reading.

## Appendix B — Data access and privacy

- **Washington.** The standard statewide **VRDB extract**, the single public extract the
  Secretary of State publishes. By statute the public file carries name, address,
  political jurisdiction, gender, **year of birth**, voting record, registration date,
  and registration number, and no other registration information is available for public
  inspection (RCW 29A.08.710) — the statutory reason this series uses year of birth
  rather than full date of birth. Use is restricted to elections and political purposes
  and **may not be commercial** (RCW 29A.08.720); the file is **not redistributable**,
  with penalties at RCW 29A.08.740. Washington further strengthened voter-data
  protections in 2026 (SB 5892 / Ch. 213, Laws of 2026, eff. Mar. 25, 2026).
- **New York.** The NYSVOTER statewide file, obtained by public-records request under
  New York's Freedom of Information Law (N.Y. Pub. Off. Law art. 6), subject to the
  elections-purpose certification the State Board of Elections requires. NY publishes
  **individual party enrollment** and **full date of birth**; only aggregate cohort
  counts are released here.
- **Idaho.** The statewide voter file from the Secretary of State. Idaho Code **§ 74-120**
  releases registrant **age** while withholding date of birth, driver's-license number,
  and (for the list product) address detail — the statutory reason Idaho age is a
  current-roll integer rather than an election-time DOB, and the reason Idaho's age bands
  are read against the current roll.
- **Contribution data are public records in every layer used.** FEC bulk individual
  contribution files; Idaho Sunshine state contribution filings; Washington PDC filings.
  No access restriction applies to them, and none are voter-file derived.
- **What is released.** Aggregate counts and shares only, with cell sizes in the
  thousands to millions. No individual-level records, names, or addresses appear in this
  paper, in the verification scripts' output, or in the repository. The one artifact that
  contains individual rows — the 150-record hand-rating sample used in Appendix F — was
  written to a scratch directory and is not committed. Only citations and code are
  published, not data. Full provenance and access dates:
  [Data Sources & Reproducibility](data-sources-and-reproducibility.md).

## Appendix C — Methods

- **Source and unit.** Each state's registration roll is joined to itemized individual
  contributions. The unit of analysis is a **matched voter-donor**: one row per
  registered voter for whom a unique contribution identity could be established.
- **Panels, and why the money systems are never pooled.** A state's contribution table
  can hold more than one money system, distinguished by the source prefix on each
  contribution's identifier: Washington carries federal FEC rows ($646.2M) alongside
  state PDC filings ($394.6M), and Idaho carries FEC rows ($76.2M) alongside Sunshine
  state filings ($53.3M). The match is therefore run **once per source**, writing to a
  separate panel table each time, and no figure in this paper mixes them. This matters
  quantitatively: pooling lets one person's federal and state giving stack into a single
  donor total while a one-system donor's does not, which mechanically raises measured
  concentration — Washington reads top-1% 46.6% pooled against 42.4% federal and 43.8%
  state. It also matters conceptually, since the two systems are capped and administered
  differently (Appendix G). New York has a federal panel only: its Board of Elections
  publishes state money in summary form, not as itemized contributions.
- **The match key and its uniqueness rule.** Matching proceeds in tiers, the first being
  `STRICT_ZIP5_FULL` — (last name, **full** first name, ZIP5) — followed by
  first-initial variants. Every tier carries the same guard: the key must resolve to
  **exactly one** voter on the roll and one donor identity, or the record is dropped
  rather than guessed. Adding the full-first-name tier raised Washington's matched count
  from 320K to 382K (+19%) and it is now the dominant tier. Because ambiguity is dropped,
  the matched set is a floor.
- **Concentration estimator.** Donors are ranked by total matched dollars and split into
  100 **equal-count** buckets (`NTILE(100)`) over donors with `total_donated > 0`; the
  top-1% and top-10% figures are the top 1 and top 10 buckets' dollars divided by all
  matched dollars. Equal-count buckets are used deliberately: capped and round-number
  giving produces heavy ties, and an earlier draft using `PERCENT_RANK` drifted from an
  exact decile at small N, reading Idaho's top-10% as 69.0% rather than 70.8%. Gini is
  computed on the same donor totals by the rank-weighted formula. Appendix G reuses this
  identical estimator so its layer comparisons are commensurable with Finding 2.
- **Match-bias re-weighting.** P(uniquely matchable) is estimated per age band or
  generation directly on the roll, and donor shares are re-weighted by its inverse. This
  is the test in Finding 1 and Appendix F; it was run for WA and NY, not for ID.
- **Age conventions differ by state, by statute.** WA and NY supply birth date (WA
  year-only, per RCW 29A.08.710), so ages are election-time. Idaho supplies a current-roll
  integer age, so Idaho bands are current-age and are compared against the current roll,
  not an election-time cohort.
- **Rates versus shares.** Turnout *rates* computed from a current roll are inflated by
  survivorship wherever the roll has shrunk — acutely in Idaho, whose 2026 roll (1.03M) is
  smaller than the 1.18M registered at the 2024 election. Rate cuts are therefore not
  reported for Idaho, and all headline figures in this paper are denominator-free
  composition shares.
- **Reproduction.** `scripts/verify_donor_class.py` re-derives Findings 1–4 for all three
  states from scratch SQL, without importing the analysis code;
  `scripts/diag_contribution_limits.py` produces Appendix G. Neither imports the other.
  The verifier explicitly does not cover the crossover tables, the re-weighting, or the
  hand-rated sample — those are separate scripts and, in the last case, a human step.

## Appendix D — Related work

That the donor class is small, wealthy, and unrepresentative is well established; the
contribution here is the *voter-file-matched* view — linking individual donors to the
registration roll across three states to show the donor class's age, concentration,
partisan tilt, and turnout overlap on the same records. It sits in these literatures:

- **The shape of the donor class.** Bonica, "Mapping the Ideological Marketplace,"
  *American Journal of Political Science* 58(2) (2014): 367–386, doi:10.1111/ajps.12062,
  and the DIME database; Schlozman, Verba & Brady, *The Unheavenly Chorus: Unequal
  Political Voice and the Broken Promise of American Democracy* (Princeton, 2012); Hill &
  Huber, "Representativeness and Motivations of the Contemporary Donorate: Results from
  Merged Survey and Administrative Records," *Political Behavior* 39(1) (2017): 3–29,
  doi:10.1007/s11109-016-9343-y — the donors-skew-old finding (Finding 1), and the closest
  methodological analog to the match used here. Bonica, McCarty, Poole & Rosenthal, "Why
  Hasn't Democracy Slowed Rising Inequality?" *Journal of Economic Perspectives* 27(3)
  (2013): 103–124, doi:10.1257/jep.27.3.103 — the concentration/whale result (Finding 2).
- **Unequal voice and its consequences.** Verba, Schlozman & Brady, *Voice and
  Equality: Civic Voluntarism in American Politics* (Harvard, 1995); Gilens, *Affluence
  and Influence: Economic Inequality and Political Power in America* (Princeton, 2012);
  Gilens & Page, "Testing Theories of American Politics: Elites, Interest Groups, and
  Average Citizens," *Perspectives on Politics* 12(3) (2014): 564–581,
  doi:10.1017/S1537592714001595 — the normative stakes of a participation-and-money elite.
- **Party and the donorate.** Grumbach & Sahn, "Race and Representation in Campaign
  Finance," *American Political Science Review* 114(1) (2020): 206–221,
  doi:10.1017/S0003055419000637; Grumbach, Sahn & Staszak, "Gender, Race, and
  Intersectionality in Campaign Finance," *Political Behavior* 44 (2022): 319–340,
  doi:10.1007/s11109-020-09619-0 — donor-pool composition by party and group, the frame
  for the Democratic tilt (Finding 3, New York *and* Idaho).
- **Giving and voting as stacked participation.** Verba, Schlozman & Brady (1995) again,
  on the co-occurrence of participatory acts; the giving↔turnout overlap (Finding 4) is
  the individual-record instance, framed strictly as association.
- **Voter-file / individual-level method.** Ansolabehere & Hersh, "Validation: What Big
  Data Reveal About Survey Misreporting and the Real Electorate," *Political Analysis*
  20(4) (2012): 437–459, doi:10.1093/pan/mps023; Hersh, *Hacking the Electorate: How
  Campaigns Perceive Voters* (Cambridge, 2015). On match bias and the current-roll caveat,
  the hand-rated ≈90% match precision and the inverse-propensity re-weighting in
  Appendix F address the older/stable-address/uncommon-name skew directly.
- **Contribution limits and the shape of the donor pool.** The statutory regimes tested in
  Appendix G: Idaho Code § 67-6610A (individual contributions capped at $1,000 per election
  to legislative, judicial, and local candidates and $5,000 per election to statewide
  candidates, with primary and general counted separately and self-funding exempt; 2026
  S.B. 1422 proposed raising these to $1,500 and $6,000 but was retained on the calendar);
  RCW 42.17A.405, recodified as RCW 29B.40.020 effective Jan. 1, 2026 (Washington's caps,
  indexed and administered by the Public Disclosure Commission); N.Y. Elec. Law § 14-114
  (New York's comparatively high caps); Tex. Elec. Code § 253.094 (Texas bars corporate and
  labor-organization contributions but imposes **no dollar limit** on individual gifts to
  non-judicial state candidates; the Judicial Campaign Fairness Act, §§ 253.151–253.176, is
  the exception); 52 U.S.C. § 30116 (the federal per-election individual limit, $3,500 for
  the 2025–26 cycle, indexed for inflation); and 52 U.S.C. § 30118 (federal prohibition on
  corporate contributions, which the Idaho and Texas state systems do not share). On the
  constitutional architecture that leaves per-gift caps standing while removing any ceiling
  on a donor's total giving: *Buckley v. Valeo*, 424 U.S. 1 (1976) (contribution limits
  upheld, expenditure limits struck), and *McCutcheon v. FEC*, 572 U.S. 185 (2014)
  (invalidating the biennial aggregate limit). On the empirical consequence — that limits
  redistribute large-donor influence across vehicles rather than removing it: Barber,
  "Ideological Donors, Contribution Limits, and the Polarization of American Legislatures,"
  *Journal of Politics* 78(1) (2016): 296–310, doi:10.1086/683453; La Raja & Schaffner,
  *Campaign Finance and Political Polarization: When Purists Prevail* (Michigan, 2015).
  Appendix G's result is consistent with that literature.

## Appendix E — Full distribution tables

**Matched-donor concentration, with bootstrap intervals.** Both Washington panels were
bootstrapped at B=1,000 resamples (`diag_donor_concentration_bootstrap.py`). The
intervals are tight enough that the concentration finding does not rest on a handful of
top donors, and the two panels' intervals overlap — the state layer's higher point
estimate is not separable from the federal layer's at this precision:

| Washington, matched donors | federal panel | 95% interval | state panel | 95% interval |
|---|--:|---|--:|---|
| top 1% → share of matched $ | 42.4% | [40.2–44.9] | 43.8% | [39.6–48.9] |
| top 10% → share of matched $ | 74.8% | [73.7–76.0] | 76.0% | [74.2–78.2] |
| Gini | 0.820 | [0.812–0.828] | 0.827 | [0.814–0.843] |

**Statewide (all itemized donors, not only matched), four states.** From
`cross_state_fec_money.py` over each state's FEC individual layer, donor-residence
filtered. This is the one table in the paper where Texas appears, since aggregate donor
figures need no voter file:

| statewide concentration | WA | NY | TX | ID |
|---|--:|--:|--:|--:|
| top 1% → share of $ | 39.3% | 47.5% | 41.7% | 36.0% |
| top 10% → share of $ | 72.3% | 78.7% | 74.5% | 69.2% |
| Gini | 0.800 | 0.848 | 0.818 | 0.775 |

Idaho is the least concentrated of the four on every measure, and the ordering matches
the matched federal panel (NY > WA > ID) — so the panel result is not an artifact of who
the matcher can find. It also cannot be attributed to state contribution caps, since
this table is entirely federal money under identical federal limits; Appendix G develops
that point.

**Candidate money versus total flow.** Concentration is a property of the *uncapped*
vehicles more than of candidate committees. Money reaching candidates (each gift bounded
by the per-election limit) runs top-1% ≈ **16–18%** and Gini ≈ **0.69**, against **39–48%**
and **0.80–0.85** for total outflow including party committees, joint fundraising
committees, and PACs (`cross-state-fec-money.md` §I).

**Geographic concentration of matched dollars, by panel.**

| state / panel | leading geography | share of matched $ | next |
|---|---|--:|---|
| WA federal | ZIP3 981xx (Seattle) | 37.3% | 980xx 26.1% → two ZIP3s = **63.4%** |
| WA state | ZIP3 981xx (Seattle) | 32.3% | 980xx 22.8% → two ZIP3s = **55.1%** |
| NY federal | New York County (Manhattan) | 50.3% | Westchester 12.4%, Kings 6.6%; ZIP3 100 = 46.3%, top-3 ZIP3 = **63.4%** |
| ID federal | Ada County (Boise), 10,338 donors | 36.4% | Blaine 11.7%, Bonneville 11.2% |
| ID state | Ada County (Boise), 10,037 donors | 49.2% | Kootenai 9.0%, Canyon 5.5% |

The two panels do not order the same way here, and the difference is instructive.
Washington's federal money is the *more* metro-concentrated of its two (top-two ZIP3s
63.4% federal vs 55.1% state): state races run in all 49 legislative districts, so state
money is raised everywhere, while federal money pools in Seattle. Idaho inverts it — Ada
County's grip *loosens* from 49.2% of state dollars to 36.4% of federal — not because
federal money is broadly spread, but because it relocates to wealthy enclaves outside the
capital, above all resort-county Blaine at 11.7% from 1,097 donors. Concentration is the
constant; which geography does the concentrating depends on the money system.

**Donor pool versus registration, by district competitiveness (NY).** The Democratic
share of the donor pool exceeds the Democratic share of registrants in every band, and
two-thirds of all matched donors (205K of 308K) live in Solid districts:

| band | donor pool, D share | registrants, D share |
|---|--:|--:|
| Tossup | 57.7% | ~40% |
| Solid | 71.6% | ~56% |

Idaho shows the mirror image from the red side: the bulk of matched donors sit in Solid-R
legislative districts, where the donor pool is ~71% Republican, while the few more
competitive districts carry a far more balanced mix (~46% R / ~34% D)
(`diag_id_electorate_extras.py`).

**Giving and turnout, side by side.**

| | donors | non-donors |
|---|--:|--:|
| WA super-voter share, federal panel | 85.4% | 51.4% |
| WA mean turnout propensity, federal panel | 0.966 | 0.754 |
| WA super-voter share, state panel | 84.9% | 50.8% |
| WA mean turnout propensity, state panel | 0.950 | 0.751 |
| NY generals voted, of last 4 | 3.03 | 1.78 |
| NY super-voter share (≥3 of 4) | 73.0% | 37.1% |

The give↔vote overlap is the finding least sensitive to which money system is examined:
Washington's two panels differ by half a point.

## Appendix F — Match validation and robustness

**Is matchability age-dependent?** This is objection 1, tested directly. P(a voter is
uniquely matchable) is computed on the roll itself, then donor shares are re-weighted by
its inverse:

| state | spread of P(matchable) | re-weighted result |
|---|---|---|
| NY, four age bands | **94.5%–95.4%** (0.9-pt spread) | 65+ donor share 47.9% → **47.9%** |
| WA, five generations | **96.3%–97.6%** (1.4-pt spread) | every multiplier unchanged to 2 d.p., **both panels** (federal Silent 2.48 → 2.48×, Gen Z 0.10 → 0.10×; state Silent 1.59 → 1.59×) |

A selection gradient that flat cannot generate the observed senior
over-representation. Two notes on the Washington row. First, P(uniquely matchable) is a
property of the *roll* and the match key, not of which contributions are used, so the
same propensities re-weight both panels; only the multipliers they act on are
panel-specific. Second, the WA test uses a slightly narrower denominator than Finding 1
(active registrants carrying a ZIP), so its raw multipliers sit a few hundredths below
Finding 1's — the quantity of interest is the raw-to-re-weighted *difference*, which is
zero to two decimals either way. An earlier draft, computed on the pooled match and a
stricter matchability definition, reported a 68.9–73.1% spread and reached the same null
result (Silent 1.87 → 1.83×). Idaho was not separately re-weighted, so its 64.7% and
51.1% figures carry no such adjustment.

**Hand-rated match precision.** A 150-record sample was rated by hand on 2026-07-10 in
two rounds (`diag_match_validation_sample.py`): 9 records flagged on the first pass and
**15 on the second, more thorough pass**, i.e. **≈90% apparent precision**. The dominant
error mode is spousal or household false-merge (shared surname and ZIP). Several flags
were unverifiable for want of donor detail, so true precision may be slightly higher. The
sample contains individual-level rows and is deliberately not committed to the repository.

**How much of the donor side is reachable at all?** Ceiling analysis on the donor files
(`diag_donor_match_ceiling.py`) — the share of donors whose key could in principle resolve
to a unique voter, on the first-initial key and the full-name key:

| | WA | NY | TX | ID |
|---|--:|--:|--:|--:|
| initial key | 65% | 69% | 61% | 86% |
| full-name key | 72% | 76% | 68% | 96% |

Idaho's ceiling is far higher (smaller roll, fewer name collisions), which is worth
keeping in view when comparing matched counts across states: the three matched sets are
not equally complete samples of their donor populations.

**One residual bias, and its direction.** A donor who moved between giving and the
extract date fails the ZIP match, and mobility skews young — deflating the young donor
share. The raw age skew in Finding 1 is therefore an **upper bound**. What that leaves
untouched is the specific mechanism objection 1 names (rare names make the old easier to
match), which the flat P(matchable) above rules out.

## Appendix G — Contribution limits and the top of the distribution

Earlier drafts of Finding 2 explained Idaho's lower matched top-1% share by asserting that
state contribution limits "compress the very top of the state-money distribution." The
explanation is intuitive, and it is wrong. This appendix tests it
(`diag_contribution_limits.py`) and reports what replaces it.

The test does not require new data. Idaho residents appear in **two money systems at
once**, under two different rule sets, so the regime can be varied while holding the donor
population nearly fixed. Washington supplies the same pair.

**G1 — the statutory regimes.** Individual contributions to a candidate, per election:

| layer | legislative | statewide | ceiling on a donor's *total* giving |
|---|---|---|---|
| Idaho state (Sunshine) | **$1,000** | **$5,000** | none |
| Washington state (PDC) | capped, indexed | capped, indexed | none |
| New York state (BOE) | capped, high | capped | none |
| Texas state (TEC) | **no dollar limit** | **no dollar limit** | none |
| Federal (FEC) | **$3,500** (2025–26) | $3,500 | none since 2014 |

Note the direction of the caps: Idaho's legislative limit is *lower* than the federal
per-election limit, but **no** system caps a donor's total, the federal aggregate ceiling
having been struck in *McCutcheon v. FEC*, 572 U.S. 185 (2014). Idaho and Texas also permit
direct corporate and PAC contributions to candidates, which federal law forbids, and Idaho
caps nothing at all on ballot-measure committees. Statutes in Appendix D.

**G2 — the cap binds.** Bunching on the round statutory value is unmistakable in Idaho's
state filings:

| gift amount | itemized gifts |
|---|--:|
| $750 | 448 |
| $900 | 190 |
| $999 | 94 |
| **$1,000** (legislative cap) | **6,797** |
| $1,001 | 1 |
| $1,100 | 18 |
| **$5,000** (statewide cap) | **734** |
| $5,001 | 0 |

A 15× spike on the cap value and a cliff immediately above it is what a binding constraint
looks like. So the premise of the original explanation holds: the cap is real and donors
hit it.

**G3 — and yet capped layers are not less concentrated.** Applying Finding 2's estimator to
each layer separately (donor = name + ZIP5):

| layer | rows | $ | donors | top 1% | top 10% | Gini |
|---|--:|--:|--:|--:|--:|--:|
| ID state (capped), all filers | 216,700 | $53.3M | 54,019 | **56.4%** | 81.6% | 0.872 |
| ID state (capped), persons only | 181,539 | $23.9M | 47,356 | **39.7%** | 71.2% | 0.800 |
| ID federal, all filers | 770,765 | $76.2M | 54,155 | **36.1%** | 69.2% | 0.775 |
| ID federal, persons only | 770,128 | $76.2M | 54,088 | **36.1%** | 69.2% | 0.775 |
| WA state (capped), all filers | 2,816,398 | $348.3M | 728,255 | **44.4%** | 75.5% | 0.823 |
| WA federal, persons only | 5,578,905 | $645.6M | 361,184 | **39.3%** | 72.3% | 0.800 |

Two readings, both against the original explanation. First, in **both** states the capped
*state* layer is **more** top-heavy than the uncapped-aggregate *federal* layer — Idaho
39.7% vs 36.1% among persons, and 56.4% vs 36.1% with committees included; Washington 44.4%
vs 39.3%. Second, the persons-only Idaho state figure (39.7%, Gini 0.800) closely
reproduces Finding 2's matched 39.3% / 0.798, which is an independent check that these
layer definitions match the paper's.

**G4 — what a cap *would* do, mechanically.** Trimming every gift in Washington's federal
layer to Idaho's caps isolates pure truncation, holding the donor population fixed:

| per-gift cap | top 1% | top 10% | $ retained |
|---|--:|--:|--:|
| uncapped (actual) | 39.3% | 72.3% | $646M |
| $5,000 (ID statewide cap) | 32.2% | 68.7% | $571M |
| $3,500 (federal limit) | 31.2% | 67.7% | $554M |
| $1,000 (ID legislative cap) | **26.4%** | 62.9% | $454M |

So truncation is *not* a small effect: an Idaho-style legislative cap applied mechanically
would cut the top-1% share by 12.9 points. That sharpens the puzzle rather than resolving
it. Idaho's actually-capped state layer sits at 39.7%, **13.3 points above** what pure
truncation predicts.

**What replaces the original explanation.** The cap binds at the moment of the gift, and
then its compression is undone downstream. Nothing limits a donor's *total*, so the same
people reach the cap again and again across many recipients; and the tail displaces into
vehicles the state does not cap — 41.9% of Idaho's state dollars sit in gifts above $5,000,
the largest single Sunshine contribution is $1,245,000, and with committees included the
state layer reaches 56.4%. This is the displacement the limits literature describes (Barber
2016; La Raja & Schaffner 2015), and it matches the rest of the series: Idaho's state
legislative money is ~50% PAC-funded and its single largest filer is a ballot-measure
committee (`cross-state-fec-money.md` K4, K5), while capped candidate-side inflow runs
top-1% ≈ 16–18% against 39–48% for total outflow (§I).

Independently, the state-versus-federal distinction could not have explained the gap it was
invoked for. Idaho is the least concentrated of the four states **inside the federal layer
too** (36.0% statewide, against WA 39.3% and NY 47.5%), under identical federal rules
(Appendix E). Idaho's flatter distribution is a property of its small, retail donor base,
not of its state caps.

**Caveats.** The Sunshine layer covers cycles 2022–2025 (odd years included) while the
federal layers cover 2018–2026, so the windows are not identical. Separating people from
organizations relies on a name heuristic, and the two state files differ: Idaho Sunshine
files people as "LAST, FIRST", so a comma test works, whereas Washington PDC files them as
"LAST FIRST", so no reliable persons-only cut is available for the WA state layer and its
all-filer row is the one to read. PDC's "SMALL CONTRIBUTIONS" unitemized pseudo-contributor
is excluded from all Washington state cuts; left in, it keys as a single enormous donor and
inflates every figure. The FEC files are persons by construction, which is why their two
cuts nearly coincide — itself a check that the heuristic is not driving the result. No
causal claim is made about what caps do to a donor pool; the claim is the narrower one that
caps do not account for the cross-state differences in Finding 2.

## End note — data, reproduction, and series

Reproduction, in dependency order:

Each match script builds ONE panel per run, selected with `--source`; the two panels are
written to `voter_donor_affiliation_fec` and `voter_donor_affiliation_state` and are
never pooled (Appendix C).

```
# Washington — both panels:
python scripts/match_wa_voters_to_donors.py --source fec
python scripts/match_wa_voters_to_donors.py --source state
python scripts/diag_wa_individual_findings.py

# New York (federal only — NY publishes no itemized state contributions):
python scripts/load_ny_voters.py                 # NYSVOTER FOIL -> ny_vrdb.duckdb
python scripts/diag_ny_turnout_party.py --rebuild # voter_participation table
python scripts/backfill_ny_committee_party.py     # bulk FEC committee/candidate party -> 79%
STATE=NY python scripts/match_ny_voters_to_donors.py    # match + own-party/age/crossover
STATE=NY python scripts/diag_ny_match_bias.py           # age-skew validation
STATE=NY python scripts/diag_ny_primary_participation.py
STATE=NY python scripts/diag_ny_donor_extras.py         # geography, giving<->turnout, in/out-of-state x party

# Idaho — both panels (party of record + current-roll age):
python scripts/load_id_voters.py                       # ID SoS voter file -> id_vrdb.duckdb
STATE=ID python scripts/backfill_id_recipient_party.py # state recipient party from SoS roster + patterns
STATE=ID python scripts/match_id_voters_to_donors.py --source fec
STATE=ID python scripts/match_id_voters_to_donors.py --source state
python scripts/diag_id_electorate_extras.py            # donor-mix x LD competitiveness

# Cross-state dollar concentration, and the appendices:
python scripts/cross_state_fec_money.py                # Appendix E statewide table
python scripts/diag_donor_concentration_bootstrap.py   # Appendix E intervals (both WA panels)
python scripts/diag_donor_match_ceiling.py             # Appendix F ceilings
python scripts/diag_contribution_limits.py             # Appendix G

# Independent re-derivation of Findings 1-4 across both panels
# (from-scratch SQL, imports no analysis code):
python scripts/verify_donor_class.py
```

All inputs are public records (FEC bulk files; Idaho Sunshine and Washington PDC filings;
state voter files obtained under each state's lawful-use terms — NY NYSVOTER FOIL, WA VRDB,
ID SoS). See [`data-sources-and-reproducibility.md`](data-sources-and-reproducibility.md)
for the full source ledger and the matcher/competitiveness method notes, and
[`publication-checklist.md`](publication-checklist.md) for the verification ledger of
expected values.

This is Paper #3 of the electoral-health series:
[`who-decides-washington.md`](who-decides-washington.md) (the gray off-year electorate),
[`who-decides-new-york.md`](who-decides-new-york.md) and
[`who-decides-idaho.md`](who-decides-idaho.md) (party-resolved electorates),
[`safe-seat-washington.md`](safe-seat-washington.md) (observed competitiveness), and
[`cross-state-fec-money.md`](cross-state-fec-money.md) (the four-state money layer).
