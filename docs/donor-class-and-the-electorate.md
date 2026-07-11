# The Donor Class Is Not the Electorate

### Who funds elections in Washington, New York, and Idaho — old, concentrated, and (where we can see party) skewed toward Democrats in a blue state *and* a red one — measured from individual voter-to-donor matches

*Paper #3 of the electoral-health series (companion to
[`who-decides-washington.md`](who-decides-washington.md),
[`who-decides-new-york.md`](who-decides-new-york.md),
[`who-decides-idaho.md`](who-decides-idaho.md),
[`safe-seat-washington.md`](safe-seat-washington.md), and
[`cross-state-fec-money.md`](cross-state-fec-money.md)). **DRAFT — pending the
independent-verification gate in [`publication-checklist.md`](publication-checklist.md).***

*Provenance. Washington figures: `scripts/diag_wa_individual_findings.py` —
WA's registered roll (5.51M) + 27.1M vote records + birthdates
(`data/wa_vrdb.duckdb`), matched to FEC donors (382,408 voters). New York
figures: `scripts/match_ny_voters_to_donors.py`,
`scripts/backfill_ny_committee_party.py`, `scripts/diag_ny_match_bias.py`,
`scripts/diag_ny_primary_participation.py` — NY's NYSVOTER roll (13.54M;
individual party enrollment + DOB; `data/ny_vrdb.duckdb`) matched to 10.02M FEC
itemized contributions (`data/ny_statewide.duckdb`, 308,032 voters). Idaho
figures: `scripts/match_id_voters_to_donors.py`,
`scripts/backfill_id_recipient_party.py`,
`scripts/diag_id_electorate_extras.py` — ID's statewide roll (1.03M; individual
party affiliation + age; `data/id_vrdb.duckdb`) matched to Idaho Sunshine **state**
campaign contributions (`data/id_statewide.duckdb`, 27,250 voters). Cross-state
dollar concentration: `scripts/cross_state_fec_money.py`. Each figure below
traces to one of these scripts.*

*One cross-state caveat up front: the WA and NY donor layers are **federal** (FEC
itemized individual contributions); the Idaho layer is **state** (Idaho Sunshine)
because no comparable FEC individual file is loaded for ID. That the same donor-class
shape appears across two different money systems, three state partisan climates, and
two age-measurement methods (DOB in WA/NY, current-roll age in ID) makes the pattern
more robust, not less — but Idaho's dollar figures are not directly comparable in
magnitude to the two federal layers.*

---

## The question

Campaign money is usually described by *how much* is raised. The more
consequential question for representation is *whose* money it is — and whether
the people who fund elections look anything like the people who vote in them. If
the donor class is a representative cross-section of the electorate, money is
just amplified participation. If it is a narrow, unrepresentative slice, then a
distinct and self-selected population is setting the financial terms of every
race before the first ballot is cast.

We can answer this at the individual level in three states by matching the
registered-voter roll to itemized donors, person by person (a conservative name +
ZIP match; see *Boundary of inference*). Washington supplies the demographic and
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

Nearly **half of NY's matched donors are 65 or older**, versus a quarter of the
active roll. **Washington** shows the same shape as generation multipliers
(donor share ÷ roll share): **Silent 1.87×, Boomer 1.64×, Gen X 1.18×,
Millennial 0.59×, Gen Z 0.17×**.

**Idaho** replicates it in a third state (age here is current-roll age, not
election-time DOB, so bands are read against the current roll):

| age band | matched donors | all voters | 2024 GE voters |
|---|--:|--:|--:|
| 18–29 | **2.6%** | 15.2% | 13.1% |
| 30–44 | 13.1% | 22.8% | 22.4% |
| 45–64 | 33.2% | 30.9% | 31.9% |
| 65+ | **51.1%** | 31.0% | 32.6% |

More than **half of Idaho's matched donors are 65+** — the oldest donor layer of
the three — versus a third of the roll, and the under-30 share collapses to 2.6%.
The donor class is the grayest slice of the electorate in blue and red states
alike.

**The skew is not a matching artifact.** The obvious objection is that the match
key (last name + first name + ZIP5, required to be *unique* on the roll) selects
older, rarer-named, stable-address voters. Tested directly in the two states where
we ran the re-weighting (WA and NY), it does not: the probability a voter is
uniquely matchable is **nearly flat across age** — NY **94.5–95.4%** across the
four bands (0.9-pt spread, `diag_ny_match_bias.py`); WA **68.9%–73.1%** across
generations (~4-pt spread). Inverse-propensity re-weighting therefore **barely
moves the distribution**: NY's 65+ donor share goes 47.9% → **47.9%** (0.0-pt
shift); WA's Silent multiplier 1.87 → **1.83×**, Gen Z 0.17 → **0.17×**. The age
skew is a property of who *gives*, not of who the matcher can *find*. (Idaho uses
the identical conservative matcher but was not separately re-weighted; its 51% 65+
donor share is reported without that adjustment.)

---

## Finding 2 — The donor class is whale-dominated

Money concentrates at the very top of the matched-donor distribution, similarly
across three very different states:

| matched-donor concentration | Washington | New York | Idaho |
|---|--:|--:|--:|
| top 1% of donors → share of matched $ | **47.7%** | **51.2%** | **39.3%** |
| top 10% of donors → share of matched $ | **80.0%** | **81.4%** | **70.8%** |

*Estimator (all three states, one method): donors are ranked by total matched dollars
and split into 100 equal-count buckets (`NTILE(100)`) over actual donors
(`total_donated > 0`); "top 1% / 10%" is the top 1 / 10 buckets' dollars ÷ all matched
dollars. Equal-count buckets are robust to ties at round dollar amounts; an earlier
draft computed NY and Idaho with `PERCENT_RANK`, which drifts from an exact decile at
small N — it read Idaho's top-10% as 69.0% rather than 70.8%. Gini coefficients: WA
0.862, NY 0.867, Idaho 0.798.*

A geographic corollary in all three states. In WA, **61.2%** of matched-donor
dollars come from just two Seattle-metro ZIP3s (981xx 35.9% + 980xx 25.2%). NY is
even more concentrated: **Manhattan (New York County) alone supplies 50.3%** of
matched-donor dollars, ZIP3 100 = 46.3%, and the top three ZIP3s (Manhattan +
Westchester + Brooklyn) = **63.4%** (`diag_ny_donor_extras.py`). Idaho shows the
same single-metro dominance: **Ada County (Boise) alone supplies 49.2%** of
matched-donor dollars from 10,037 donors — the money mirror of Seattle and
Manhattan in a state with neither. (Idaho's top-1% concentration, 39%, is
somewhat lower than the two federal layers — expected, since state contribution
limits compress the very top of the state-money distribution.) At the
statewide level (all itemized donors, not only matched), the same top-heaviness
appears across all three states we have loaded — top 1% of donors supply
**39.3%** of dollars in WA, **47.5%** in NY, **41.7%** in TX
(`cross_state_fec_money.py`). The "small-dollar democratization" narrative
coexists with a money system whose itemized dollars are dominated by a thin top
stratum and a single metro.

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
| OTHER (minor) | 10,178 | 3.3% | 0.5% | +2.8 | $22.8M | 1.9% |

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
| DEM | 174,330 | **94.2%** | 3.9% | 1.9% |
| REP | 57,342 | 14.2% | **82.6%** | 3.2% |
| NOPARTY | 30,590 | **65.5%** | 31.0% | 3.5% |
| OTHER | 8,274 | 40.7% | 57.0% | 2.3% |

Two patterns: registered **Republicans fund Democrats at ~3.6× the rate
Democrats fund Republicans** (14.2% vs 3.9%) — a deep-blue donor ecosystem; and
the unaffiliated bloc, invisible to registration-based analysis, **leans ~2:1
Democratic in its actual giving** (65.5% → D), so NY's independents are not
centrist by behavior.

**Idaho — the same skew, in the reddest state.** The decisive test of whether the
Democratic tilt of the donor class is real or just a blue-state artifact is to run
it in a state where Republicans hold a 5:1 registration edge. Using each donor's
own Idaho affiliation:

| party | matched donors | donor share | registration | **skew** | matched $ | $ share |
|---|--:|--:|--:|--:|--:|--:|
| REP | 18,115 | 66.5% | 62.9% | +3.6 | $11.31M | 71.1% |
| DEM | 5,685 | 20.9% | 11.8% | **+9.1** | $3.27M | 20.6% |
| UNAFF (unaffiliated) | 3,281 | 12.0% | 23.9% | **−11.8** | $1.27M | 8.0% |
| OTHER (minor) | 169 | 0.6% | 1.4% | −0.8 | $0.04M | 0.3% |

Republicans supply the plurality of Idaho's money, as a 63%-Republican state must
— but relative to their numbers the **most over-represented donors are registered
Democrats** (+9.1 points, nearly double their share of the roll), and the
unaffiliated quarter is again the most *under*-represented (−11.8). The same
directional finding as New York, from the opposite end of the spectrum: the donor
class leans Democratic-of-the-electorate and runs against the unaffiliated,
whether the electorate around it is blue or red.

**Crossover (Idaho).** Idaho Sunshine carries no party on the recipient, so
recipient party is reconstructed from the Secretary of State candidate roster plus
party/committee name patterns (`backfill_id_recipient_party.py`), resolving ~52% of
matched donors and ~66% of candidate-directed dollars. Among donors whose money
reached a party-resolvable recipient:

| own party | donors (resolved) | → Democratic | → Republican | mixed |
|---|--:|--:|--:|--:|
| DEM | 3,365 | **93.5%** | 4.0% | 2.5% |
| REP | 9,420 | 18.8% | **79.3%** | 1.9% |
| UNAFF | 1,303 | **72.8%** | 24.5% | 2.7% |
| OTHER | 59 | 18.6% | 81.4% | 0.0% |

The two direction-safe patterns from New York replicate: registered **Democrats
are near-monolithic donors** (93.5% → D, essentially identical to NY's 94.2%), and
**unaffiliated donors lean Democratic** in their actual giving (~3:1 in ID, ~2:1 in
NY) — independents are not centrist by behavior in either state. Idaho's apparent
Republican→Democratic crossover (18.8%) is an **upper bound**: the unresolved
recipient pool (local Republican candidates and R-aligned PACs absent from the
roster) skews Republican, so Republican donors' Republican-side giving is
disproportionately the part left untraced, and the ~52% coverage is well below
NY's 79%. We therefore make no cross-state claim about the majority party's
crossover rate — only the Democratic-loyalty and unaffiliated-lean patterns, which
hold in both states.

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

In both states, the people who give are the people who reliably vote. In
Washington, matched donors are **84.0% super-voters versus 50.1%** of non-donors
(mean turnout propensity 0.953 vs 0.748). In New York, matched donors voted in
**3.01 of the last four federal generals on average versus 1.85** for
non-donors, and **72.9% are super-voters (≥3 of 4) versus 39.3%**
(`diag_ny_donor_extras.py`). The same individuals concentrate *both* forms of
influence rather than one offsetting the other. (Association only — donors are
pre-selected for engagement, so reverse causation is equally plausible; the
benign "donating as a gateway to participation" reading is fully live.)

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

## Boundary of inference

- **The match is a proxy.** Voter↔donor identity rests on (last, first, ZIP5)
  uniqueness, not a shared ID. It is conservative by design (ambiguous keys are
  dropped, not guessed), so the matched set is a **floor**, not a census, of the
  donor population. WA bootstrap CIs on concentration are tight; a 150-row
  hand-validation of match precision (2026-07-10, two review rounds) finds **≈90%
  apparent precision** (15/150 flagged on a second, more thorough pass; 9 on the first),
  the dominant error being **spousal/household false-merges** (same surname + ZIP).
  Those barely move the age, geography, or concentration cuts, because the mis-attributed
  partner shares household, ZIP, and typically similar age; some flags were unverifiable
  for missing donor detail, so true precision may be a little higher.
- **Itemized giving; federal for WA/NY, state for ID.** Sub-$200 unitemized
  giving is invisible, so the *small-dollar* end is undercounted — which, if
  anything, **understates** the concentration in Findings 1–2. WA/NY use FEC
  federal itemized contributions; **Idaho uses Idaho Sunshine state
  contributions** (no comparable FEC individual file is loaded for ID), so ID
  dollar *magnitudes* are not comparable to the federal layers — only the
  within-state shares and skews are. That the same shape recurs across the two
  money systems strengthens the finding.
- **Active-roll denominator.** All three matches use the current roll; past-purged
  donors are absent, biasing turnout *rates* (not composition shares) high for
  older cycles. Read shares as the robust cut. Idaho's age is a current-roll
  integer (not DOB), so ID age bands are current-age, not election-time.
- **Recipient party (Finding 3 crossover) covers 79% of NY contributions and ~52%
  of ID matched donors** (~66% of ID candidate-directed dollars); unresolved rows
  are genuinely-nonpartisan PACs / ballot-measure committees in both. The ID
  majority-party crossover rate is an upper bound (see Finding 3); own-party and
  age cuts use the full 100%-present party of record.
- **One residual age bias runs one way.** A donor who moved between giving and
  today fails the ZIP match, and mobility skews young — deflating the young
  donor share. So the raw age skew is an **upper bound**, but the specific
  mechanism the objection names (rare names → easier match for the old) is ruled
  out by the flat P(matchable) above.

---

## What it means

Across three states that differ in size, partisanship, money system, and election
administration, the population that finances campaigns is the same kind of
population: **old, top-heavy, geographically concentrated, and — where party is
observable — skewed toward Democrats relative to the electorate and away from the
unaffiliated.** New York and Idaho's party-of-record turns the Washington finding
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

## Methods & reproducibility

```
# Washington (no external file needed):
python scripts/diag_wa_individual_findings.py

# New York:
python scripts/load_ny_voters.py                 # NYSVOTER FOIL -> ny_vrdb.duckdb
python scripts/diag_ny_turnout_party.py --rebuild # voter_participation table
python scripts/backfill_ny_committee_party.py     # bulk FEC committee/candidate party -> 79%
STATE=NY python scripts/match_ny_voters_to_donors.py    # match + own-party/age/crossover
STATE=NY python scripts/diag_ny_match_bias.py           # age-skew validation
STATE=NY python scripts/diag_ny_primary_participation.py
STATE=NY python scripts/diag_ny_donor_extras.py         # geography, giving<->turnout, in/out-of-state x party

# Idaho (state Sunshine money; party of record + current-roll age):
python scripts/load_id_voters.py                       # ID SoS voter file -> id_vrdb.duckdb
STATE=ID python scripts/backfill_id_recipient_party.py # recipient party from SoS roster + patterns
STATE=ID python scripts/match_id_voters_to_donors.py   # match + own-party/age/concentration/crossover
python scripts/diag_id_electorate_extras.py            # donor-mix x LD competitiveness

# Cross-state dollar concentration:
python scripts/cross_state_fec_money.py
```

All inputs are public records (FEC bulk files; state voter files obtained under
each state's lawful-use terms — NY NYSVOTER FOIL, WA VRDB). See
[`data-sources-and-reproducibility.md`](data-sources-and-reproducibility.md) for
the full source ledger and the matcher/competitiveness method notes.
