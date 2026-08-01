# Does Money Move Votes in Washington?

### A negative result, and the data ceiling that keeps it from being a stronger one

**Stephen Kirby** · Tikor Consulting · July 2026

*AI-assisted drafting and analysis review. All figures are reproducible from
public-record data and from the open-source scripts cited below. The paper source, code,
and data-acquisition recipe are public at <https://github.com/skirby359/who-decides>.
Contact: kirby@tikorconsulting.com.*

*Paper #4 of the electoral-health series (companion to
[`who-decides-washington.md`](who-decides-washington.md),
[`safe-seat-washington.md`](safe-seat-washington.md),
[`donor-class-and-the-electorate.md`](donor-class-and-the-electorate.md), and
[`cross-state-fec-money.md`](cross-state-fec-money.md)). **DRAFT — pending the
independent-verification gate in [`electoral-health-audit-log.md`](electoral-health-audit-log.md).***

## Abstract

The three preceding papers in this series establish who votes, whether their vote decides
anything, and who funds the candidates. This paper asks the question those invite — does
the money change the result? — and reports that the available public record cannot answer
it, while characterizing precisely how far short it falls. Across 163 Washington
legislative and congressional races from 2018 to 2024, the ratio of Democratic to
Republican fundraising correlates with candidate overperformance at **+0.55**, the
strongest of any measured factor, ahead of incumbency (+0.43) and candidate quality
(+0.34). Three independent attempts to convert that correlation into a causal reading
fail. Spending *allocation* — the field, media, and professional shares of itemized
expenditure — has cross-cycle holdout R² of essentially **zero**, despite being a stable
candidate trait. The forecast model that underpins this series zeroes its fundraising term
in post-redistricting districts because the single-cycle baseline already absorbs it. And
the one design capable of a directional test, regressing fundamentals-net residual on net
independent-expenditure advantage, is not estimable: machine-readable directional IE
exists for a single cycle and seven scorable Washington races, while $70.6M of state
legislative IE carries no support-or-oppose flag at all. The descriptive cross-section
that remains points the wrong way for a purchase story — money is associated with running
*behind* — and the most IE-saturated House race in the country finished 0.06 points from
its fundamentals. The honest verdict is that money in Washington behaves as a marker of
candidate strength rather than a demonstrable mover of votes, and that the public data
cannot presently distinguish the two.

**Keywords:** campaign spending; independent expenditures; electoral effects; endogeneity;
null results; data availability; state legislative elections; Washington.

---

## The question, and why it resists an answer

The preceding papers in this series each end at the same edge. The turnout paper shows an
older, smaller electorate decides off-cycle races. The safe-seat paper shows most general
elections are settled before November. The donor paper shows the people funding those
races are not the people voting in them. Each invites the obvious next question: **so does
the money actually change who wins?**

It is the hardest question in the series, and the reason is structural rather than
technical. Campaign money is *endogenous to candidate strength*. Strong candidates attract
money; money then appears alongside strong results. Donors and independent-expenditure
committees also behave strategically, moving resources toward races they judge close and
toward candidates they judge threatened — which can invert the naive correlation entirely,
making spending look harmful. Untangling this is a fifty-year-old problem in political
science (Jacobson 1978), and the credible answers come from designs this data does not
support: instrumental variables (Gerber 1998), repeat-challenger panels (Levitt 1994), or
randomized field experiments (Kalla & Broockman 2018).

This paper does not solve it. What it does is report what Washington's public record shows,
run the tests that record permits, and state precisely which test would settle the matter
and why it cannot currently be run. **The negative result and the data ceiling are the
contribution.** A reader looking for a verdict on whether money buys elections will not
find one here, and should be suspicious of anyone offering one from this evidence base.

---

## Finding 1 — Money is the single strongest correlate of overperformance

The starting observation is not subtle. Across the 163 baseline-scorable Washington
legislative and congressional races from 2018 to 2024
(`scripts/diag_overperformance_patterns.py`), *overperformance* — the actual Democratic
two-party share minus the district's fundamentals-based baseline — correlates with the
fundraising ratio more strongly than with anything else measured:

| factor | Pearson r with overperformance |
|---|--:|
| **fundraising, log2(D receipts / R receipts)** | **+0.55** |
| incumbency | +0.43 |
| candidate quality index | +0.34 |
| local trend | +0.32 |
| midterm year | ≈0 |

The relationship is monotonic, not driven by a tail. Sorting races by who out-raised whom:
where the Democrat out-raised the Republican, the Democrat beat the district baseline by an
average of **+4.20** points; where funding was even, **+2.37**; where the Republican
out-raised, **−1.93**.

Taken alone this looks like a straightforward answer, and it is the number a campaign
consultant would quote. The rest of this paper is about why it is not one.

---

## Finding 2 — Three tests for a causal signature, three nulls

If money moves votes, the effect should leave traces beyond a raw correlation. Three
independent tests look for those traces. None finds one.

### 2a. How money is spent predicts nothing

If spending buys votes, *how* it is spent should matter — a campaign that puts its money
into field organizing should perform differently from one that puts it into television.
Washington's Public Disclosure Commission publishes itemized expenditures with a purpose
code per transaction (Socrata `tijg-9zyp`; 272,320 candidate rows 2018–2024, $286M, ~62% of
dollars carrying a code). From these, `scripts/diag_expenditures_vs_residual.py` derives
each candidate's field, media, and professional *shares* of coded operational spend, and
tests them against the residual.

The shares correlate with the residual at essentially zero — field **+0.02**, media
**+0.05**, professional **−0.03**. Total spend correlates at +0.26, but that is the
fundraising scale signal from Finding 1 arriving again, not allocation. The decisive test
is cross-cycle holdout: fit on 2022, predict 2024.

| model | holdout R² |
|---|--:|
| core candidate-quality features | 0.000 |
| core + field share | 0.006 |
| core + all allocation shares | 0.018 |
| allocation shares alone | 0.041 *(r = −0.20, wrong-signed)* |

In-sample R² rises from 0.049 to 0.144 as shares are added while holdout R² stays at the
floor — the signature of overfitting, not signal. Notably, allocation *is* a real and
stable candidate trait: field-share persistence across cycles runs r = 0.83 and media-share
r = 0.998. It is a stable feature that carries no information about the outcome. And the
one directional hint runs against the folk theory: field share correlates **−0.24** with
raw overperformance, so more ground spending is associated with slightly worse results, not
better.

### 2b. The forecast model discards the money term when it can check it

A second test comes from an unusual direction: the forecasting model this series relies on
was tuned without reference to this question, and it independently concluded that
fundraising carries no information once the baseline is known.

In Washington's post-2022 districts, where the redistricting boundary filter collapses
history to a single post-redistricting cycle, the model **zeroes its fundraising-advantage
term entirely**. The reason is that the single-cycle baseline already absorbs it: the
incumbent ran in that cycle, their fundraising advantage manifested in that result, and
adding the term on top double-counts. Before this correction the model predicted a D+28
result in a district whose incumbent's actual history ran D+5 to D+8. The term was not
dropped for ideological reasons but because leaving it in produced worse forecasts.

This is weaker evidence than a designed test — it is a modelling decision, not an
experiment — but it points the same way. When a predictive system is allowed to check
whether fundraising adds information beyond the district's own recent result, it finds that
it does not.

### 2c. Money flows toward the side that is behind

The third test is the closest thing to a directional design the data permits.
`scripts/diag_ie_vs_margin.py` regresses each race's *fundamentals-net residual* — actual
minus model-predicted Democratic share, not the raw margin — on the net pro-Democratic
independent-expenditure advantage. Using the residual rather than the margin is what makes
this a test of money's marginal effect rather than a restatement of district partisanship.

The association is **negative**: −0.39 points of residual per $1M net pro-Democratic IE
(Pearson r = −0.39, n = 7). Read naively this says money *costs* votes. Read correctly it
is the textbook endogeneity signature: outside money flows toward the side that is
struggling, and arrives in races already moving away from it.

The single most instructive case is the most heavily funded. **Washington's 3rd
Congressional District in 2024 attracted $40.1M in total independent expenditure — the most
IE-saturated House race in the country — with a net $16.2M advantage on the Democratic
side. It finished 0.06 points from its fundamentals-based prediction.** Forty million
dollars of outside money, and the race landed almost exactly where the district's
underlying partisanship said it would. That is a single observation and proves nothing on
its own, but it is a striking one.

---

## Finding 3 — The test that would settle it cannot be run

The design in 2c is the right one. It is also not estimable, and that limitation is the
paper's most citable result.

**Directional independent-expenditure data exists on disk for exactly one cycle.** FEC
Schedule E carries a support-or-oppose flag and a district, which is what makes a
directional test possible at all — but only the 2024 cycle is loaded, yielding **seven
scorable Washington House races**. Three further districts were uncontested and drop out;
2026 has no national-environment data yet.

**The state-legislative money is worse.** Washington's PDC records **$70.6M** of
independent expenditure in legislative races, which would multiply the sample severalfold.
It carries a **null support/oppose flag**. The database records that money was spent
regarding a race, not which side it was spent for. It therefore cannot enter a directional
test at all without re-derivation from sponsor-level data.

Seven cross-sectional observations cannot bear the analysis the question requires. The
bootstrap confidence interval, the early-versus-late spending split, and the next-cycle
placebo all need either more races or more cycles. So the script **withholds inference
rather than reporting a coefficient** — at n = 7 the sign flips on a single race, and a
slope reported from it would be a coin flip dressed as a finding. The descriptive number
above is labelled descriptive in the script's own output for that reason.

**What would unlock it.** Backfilling FEC Schedule E for 2018, 2020, and 2022 via
`load_fec_independent_expenditures(conn, cycle=YYYY, …)` would take the sample to roughly
30 race-cycles. That is a rate-limited API job against federal House races only, and it is
the single highest-value data acquisition remaining in this series. Even then the sample
stays small and uninstrumented — 30 observations with no exogenous variation still cannot
identify a causal effect, only sharpen the descriptive picture. Genuinely settling the
question needs a design this record cannot supply.

---

## What it means

Money in Washington elections behaves like a **marker of candidate strength rather than a
demonstrable mover of votes**. It correlates with winning more strongly than any other
measured factor, and every attempt here to find the fingerprint a causal effect should
leave comes up empty: allocation predicts nothing out of sample, the forecast model
discards the term when the baseline is available, and the directional cross-section points
the wrong way.

Two things follow, and they pull in opposite directions.

The first is a caution against the strong reform claim. "Money buys elections" is not
supported by this evidence, and the donor paper's findings should not be read as implying
it. What the donor paper establishes is that a narrow, old, geographically concentrated
population *funds* campaigns — which matters for whose calls get returned and whose
concerns reach an agenda, whether or not it moves a single vote. The companion cut in
`cross-state-fec-money.md` §J sharpens this: in Washington's Solid seats the longshot party
receives just **4.8%** of House inflow. Money overwhelmingly reaches candidates who were
going to win anyway. That is a finding about *access*, not persuasion.

The second is a caution against the strong null. This paper has not shown money does not
matter. It has shown that Washington's public record cannot demonstrate that it does, on
the vote-moving axis specifically, at the sample sizes available. The **access and
agenda-setting channel is entirely untested here** — it is the channel the donor paper's
findings actually bear on, and the one most likely to matter. An honest reader should
leave with the question open and a clear sense of what it would take to close it.

---

## What this paper does not claim, and limits

- **This is not a causal estimate, and no causal claim is made in either direction.** Every
  cut is observational with no exogenous variation and no instrument. The +0.55 correlation
  is exactly what a real causal effect would also produce; the nulls are consistent with a
  true zero *and* with an effect the data is too thin to detect.
- **The allocation null is underpowered and tests the wrong thing twice over.** Coverage is
  40 of 129 legislative baseline cells, holdout n runs 15–22, and it tests spend *mix*, not
  spend *level*. It cannot rule out an effect of simply having more money.
- **The IE cross-section is n = 7.** It is reported as description and should not be read
  as an estimate of anything. Its sign can change on one race.
- **State-legislative IE is excluded entirely** for want of a directional flag, so the
  largest available body of Washington IE never enters the analysis.
- **Only the persuasion channel is examined.** Access, agenda-setting, candidate entry
  deterrence, and the effect of money on *who runs in the first place* are all untested and
  all plausible routes by which money could matter without moving a general-election margin.
- **Coverage gaps favor larger campaigns.** PDC mini-reporting excludes the smallest
  campaigns, and 38% of expenditure dollars carry no purpose code.

---

# Appendices

## Appendix A — The objections, in full

**1. "You found +0.55 and then explained it away."** The correlation is real and the paper
leads with it. The objection has force: the burden of proof for dismissing the largest
correlation in the dataset should be high. What justifies not treating it as causal is not
the correlation's size but the *pattern of everything around it* — allocation carrying no
out-of-sample signal, the forecast model finding the term redundant against the baseline,
and outside money associating with running behind. Any one of those alone would be weak.
Together they describe money tracking a strength that already exists.

**2. "Absence of evidence is not evidence of absence."** Correct, and the paper's title
question is answered "cannot tell," not "no." The allocation test is underpowered, the IE
test is not estimable, and neither speaks to spend *level* with exogenous variation. This
is stated in the body rather than buried, because the alternative — presenting a null as a
finding of no effect — would be the more serious error.

**3. "The negative IE slope is just strategic targeting, which you admit."** Yes, and that
is the point rather than a flaw. The negative association is offered as evidence of
*endogeneity*, not of money being harmful. It demonstrates that the naive correlation
cannot be read causally in either direction, which is the paper's central methodological
claim.

**4. "WA-03 is one race."** It is, and it carries no inferential weight. It appears because
it is the most extreme case available — the most IE-saturated House race in the country
landing 0.06 points from its fundamentals — and because a reader who suspects the null is
an artifact of small money should know what the largest observation looks like.

**5. "Your baseline is model-derived, so you are testing your own model."** Partly true and
worth stating plainly. Overperformance and the IE residual are both measured against a
fundamentals baseline this project built. That baseline is validated independently
(`safe-seat-washington.md` shows its safe-seat projection matching observed results within a
few points), but a reader who rejects the model should read Finding 1's correlation, which
uses the neutral PVI baseline, and discount Findings 2b and 2c accordingly.

## Appendix B — Data access and provenance

- **Election results.** Certified precinct-level returns from the Washington Secretary of
  State, aggregated to the seat. Public aggregate records.
- **Candidate finance.** Washington PDC candidate summaries and itemized C4 Schedule-A
  expenditures (Socrata `tijg-9zyp`), plus FEC candidate summaries for congressional races.
  Public disclosure records.
- **Independent expenditures.** FEC Schedule E for the 2024 cycle, carrying support/oppose
  and district; PDC independent-expenditure records for state legislative races, which
  carry amounts and races but **no directional flag**.
- **No personal data.** This paper uses candidate- and race-level aggregates only. It
  touches no voter file and releases no individual record.
- Full provenance and reproduction recipe:
  [Data Sources & Reproducibility](data-sources-and-reproducibility.md).

## Appendix C — Methods

- **Overperformance.** `actual_dem_two_party_pct − baseline_dem_pct`, where the baseline is
  the model's neutral PVI plus down-ballot-drag figure, *not* the full prediction. Positive
  means the Democrat beat the district's fundamentals. Universe: the backtest grid of 10
  congressional and 49 legislative districts across 2018–2024, restricted to the **163
  baseline-scorable cells** — cells whose PVI fell back to a default for want of district
  presidential data are excluded, the same 163 used by the published backtest.
- **Fundraising feature.** Raw `log2(D receipts / R receipts)` matched by name tokens
  against `candidate_finance` for offices H/S/SR/SS, computed independently of the model's
  own capped fundraising term.
- **Allocation shares.** Field, media and professional shares of *coded operational* spend
  per candidate, so the measure is composition rather than level. Cross-cycle holdout fits
  2022 and predicts 2024, the same bar used to reject the candidate-quality index earlier
  in this project.
- **IE residual test.** Net pro-Democratic IE = support-D plus oppose-R minus support-R
  minus oppose-D, per race, from FEC Schedule E. The dependent variable is the
  fundamentals-net residual, not the margin. Uncontested races and races without
  national-cycle data are dropped, leaving 7 of 17 candidate race-cycles scorable.
- **Inference threshold.** The IE script refuses to report a slope as inferential below 10
  scorable races and prints its data-ceiling notice instead. That behavior is deliberate and
  should be preserved if the script is re-run after a backfill.
- **Reproduction.** `scripts/diag_overperformance_patterns.py` (Finding 1),
  `scripts/diag_expenditures_vs_residual.py` (2a), `scripts/diag_ie_vs_margin.py` (2c and
  Finding 3), `scripts/diag_loser_side_money.py` (the §J longshot-share figure).

## Appendix D — Related work

This paper contributes a negative result and a data-availability audit, not a new
identification strategy. It sits in a literature that has been circling the same
endogeneity problem for five decades:

- **The endogeneity problem itself.** Jacobson, "The Effects of Campaign Spending in
  Congressional Elections," *American Political Science Review* 72(2) (1978): 469–491 — the
  founding observation that incumbent spending appears ineffective because incumbents raise
  and spend most when threatened. Jacobson, "The Effects of Campaign Spending in House
  Elections: New Evidence for Old Arguments," *American Journal of Political Science* 34(2)
  (1990): 334–362. The Washington pattern in Finding 2c is this problem reappearing in
  independent-expenditure data.
- **Designs that address it — and that this data cannot support.** Levitt, "Using Repeat
  Challengers to Estimate the Effect of Campaign Spending on Election Outcomes in the U.S.
  House," *Journal of Political Economy* 102(4) (1994): 777–798, doi:10.1086/261954 —
  differencing out candidate quality using repeated identical match-ups, and finding
  spending effects far smaller than naive estimates. Gerber, "Estimating the Effect of
  Campaign Spending on Senate Election Outcomes Using Instrumental Variables," *American
  Political Science Review* 92(2) (1998): 401–411 — the instrumental-variables approach.
  Both require panel structure or an instrument this record lacks.
- **The experimental literature.** Kalla & Broockman, "The Minimal Persuasive Effects of
  Campaign Contact in General Elections: Evidence from 49 Field Experiments," *American
  Political Science Review* 112(1) (2018): 148–166, doi:10.1017/S0003055417000363 — the
  best available evidence that general-election persuasion effects are approximately zero
  on average, which is the prior this paper's nulls are consistent with.
- **Money as information rather than purchase.** Bonica, "Mapping the Ideological
  Marketplace," *American Journal of Political Science* 58(2) (2014): 367–386,
  doi:10.1111/ajps.12062 — contributions as a revealed-preference signal about candidates,
  the reading most consistent with the results here.
- **Access rather than votes.** Kalla & Broockman, "Campaign Contributions Facilitate Access
  to Congressional Officials: A Randomized Field Experiment," *American Journal of Political
  Science* 60(3) (2016): 545–558, doi:10.1111/ajps.12180 — the channel this paper explicitly
  does *not* test, and the one where an experimental effect has actually been demonstrated.
  Any reader inclined to conclude "money doesn't matter" from this paper should read that
  one.

## Appendix E — The full IE cross-section

Every Washington congressional race with FEC Schedule-E data on disk, 2024 cycle
(`scripts/diag_ie_vs_margin.py`). "Residual" is actual minus model-predicted Democratic
share; a blank means the race was not scorable.

| race | net pro-D IE | total IE | residual (pp) | actual margin |
|---|--:|--:|--:|--:|
| cd01 / 24 | $0.00M | $0.00M | +7.59 | +26.35 |
| cd02 / 24 | $0.00M | $0.00M | — *(uncontested)* | — |
| **cd03 / 24** | **+$16.18M** | **$40.08M** | **+0.06** | **+3.92** |
| cd04 / 24 | +$1.88M | $6.77M | — *(uncontested)* | — |
| cd05 / 24 | −$0.20M | $0.46M | −0.45 | −21.25 |
| cd06 / 24 | +$5.69M | $5.69M | −3.52 | +13.67 |
| cd07 / 24 | $0.00M | $0.00M | +13.70 | +68.35 |
| cd08 / 24 | +$0.75M | $0.75M | +6.82 | +8.18 |
| cd09 / 24 | $0.00M | $0.00M | — *(uncontested)* | — |
| cd10 / 24 | $0.00M | $0.00M | −1.17 | +17.35 |

Seven scorable races. Party attribution is complete — $0 of the $53.94M total is
unresolvable to a side, so the negative slope is not a coding artifact. Note how much of
the variation sits in races with **no** independent expenditure at all: cd07's +13.70
residual and cd01's +7.59 both occur at $0 IE, which is a compact illustration of why seven
observations cannot separate money's effect from everything else that varies across
districts.

## End note — data, reproduction, and series

```
# Finding 1 — money vs overperformance across 163 race-cycles:
python scripts/diag_overperformance_patterns.py

# Finding 2a — spend allocation vs residual, cross-cycle holdout:
python scripts/diag_expenditures_vs_residual.py

# Findings 2c and 3 — IE vs fundamentals-net residual, and the data ceiling:
python scripts/diag_ie_vs_margin.py

# The longshot-share figure quoted in "What it means":
python scripts/diag_loser_side_money.py
```

All inputs are public records: certified election returns, WA PDC disclosure, and FEC bulk
and API data. See
[`data-sources-and-reproducibility.md`](data-sources-and-reproducibility.md) for the full
source ledger.

This is Paper #4 of the electoral-health series:
[`who-decides-washington.md`](who-decides-washington.md) (who votes),
[`safe-seat-washington.md`](safe-seat-washington.md) (whether the vote decides anything),
[`donor-class-and-the-electorate.md`](donor-class-and-the-electorate.md) (who funds it),
and [`cross-state-fec-money.md`](cross-state-fec-money.md) (the four-state money layer).
