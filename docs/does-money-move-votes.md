# Does Money Move Votes in Washington?

### An identification failure, measured: an exceptionally strong money–performance association that no available observational decomposition can separate from selection

**Stephen Kirby** · Tikor Consulting · July 2026

*AI-assisted drafting and analysis review. All reported statistical summaries can be
recomputed from public code and the pinned derived panels cited below. The model-derived
residuals themselves cannot presently be independently regenerated, because the forecast
implementation is not public; the pinned panels carry the residuals so that every slope,
interval and correlation — the contestable part — is recomputable without it. The paper
source, code, and data-acquisition recipe are public at
<https://github.com/skirby359/who-decides>. Contact: kirby@tikorconsulting.com.*

***DRAFT — pending human/editorial sign-off.** `scripts/verify_money_votes.py` scrapes this paper
and asserts its figures against the data, with the exceptions the script names in its own
output; that gate is automated and is not the sign-off.
The sign-off is a person reading the paper end to end, recorded in
[`money-votes-submission-notes.md`](money-votes-submission-notes.md) §Sign-off.*

*Paper #4 of the electoral-health series (companion to
[`who-decides-washington.md`](who-decides-washington.md),
[`safe-seat-washington.md`](safe-seat-washington.md),
[`donor-class-and-the-electorate.md`](donor-class-and-the-electorate.md), and
[`cross-state-fec-money.md`](cross-state-fec-money.md)).*

## Abstract

The three preceding papers in this series establish who votes, whether their vote decides
anything, and who funds the candidates. This paper asks the question those invite — does
the money change the result? — and reports that the available public record cannot answer
it, while characterizing precisely *why* it cannot: treatment is endogenous, sparse,
strategically assigned, and observed through several non-equivalent channels. Across 163
Washington legislative and congressional races from 2018 to 2024, the ratio of Democratic
to Republican fundraising correlates with candidate overperformance at **+0.60**, the
strongest of any measured factor, ahead of incumbency (+0.43) and candidate quality
(+0.34) — an ordering that holds when every factor is recomputed on the common
finance-complete sample. The paper then examines **three different observable
manifestations of political money** — candidate receipts, the Democratic campaign's
spending *allocation*, and outside groups' independent expenditure — and none supplies
identification of the causal effect the title asks about; they are different treatments,
not three replications of one null. The allocation cut is exploratory: it measures the mix
of one side's spending, not its level, and its squared holdout correlation of essentially
**zero** cannot rule out an effect of having more money. The directional test — the
observational OLS of fundamentals-net residual on net independent-expenditure advantage —
is estimable across five cycles and thirty-four scorable Washington congressional races,
and returns **+0.5 points of residual per $1M of net pro-Democratic IE with a
case-resampling bootstrap interval spanning −0.6 to +2.8**. That interval is an interval
for the observational slope, not for a causal effect, which confounding can place outside
it; and the slope itself is a single-district leverage result — deleting one race
(WA-08 2018, Cook's distance 0.69) moves it to **−0.04**, and a district-clustered
bootstrap widens the interval to **−1.6 to +1.3**. Extending the same estimator to
Washington's state legislative races — **$51.7M of PDC independent expenditure across 129
scorable district-cycles, direction-coded on 100% of rows** — multiplies the cells but not
the usable treatment variation: every interval still spans zero, and the sign of the point
estimate is **specification-dependent**, running from −3.8 to +4.9 depending on whether
electioneering communication is counted as advocacy and whether money is matched to the
contest it named. The most heavily funded race in the federal panel, Washington's 3rd in
2024, finished 0.06 points from its fundamentals. The honest verdict: money in Washington
is clearly a **marker** of candidate strength; whether it is *also* a mover of votes is
not established either way, because every available observational decomposition fails to
separate selection into spending from an effect of spending. The failure is one of
identification, not merely of data quantity.

**Keywords:** campaign spending; independent expenditures; electoral effects; endogeneity;
null results; data availability; state legislative elections; Washington.

---

## The question, and why it resists an answer

The preceding papers in this series each end at the same edge. The turnout paper shows an
older, smaller electorate decides off-cycle races. The safe-seat paper shows most general
elections are settled before November. The donor paper shows the population funding those
races is not representative of the electorate voting in them — donors skew sharply older,
more geographically concentrated and, where party is observable, more Democratic, while
being *more* likely to vote, not less. Each invites the obvious next question: **so does
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
run the tests that record permits, and state precisely what those tests do and do not
estimate. **The contribution is the identification failure itself, characterized:** the
observational association is exceptionally strong, its estimate is imprecise and
leverage-dependent, and even a perfectly estimated association would not identify the
causal effect, because nothing in this record separates selection into spending from an
effect of spending. A reader looking for a verdict on whether money buys elections will
not find one here, and should be suspicious of anyone offering one from this evidence
base — including from an earlier draft of this paper, whose directional estimate carried
the opposite sign on a seventh of the data.

---

## Finding 1 — Money is the single strongest correlate of overperformance

The starting observation is not subtle. Across the 163 baseline-scorable Washington
legislative and congressional races from 2018 to 2024
(`scripts/diag_overperformance_patterns.py`), *overperformance* — the actual Democratic
two-party share minus the district's fundamentals-based baseline — correlates with the
fundraising ratio more strongly than with anything else measured. Because finance is
present for only **128** of the 163 cells, the competing correlations are reported twice:
on each factor's full available sample, and on the common finance-complete sample, so the
ranking is not an artifact of the factors seeing different races:

| factor | full sample (n=163) | common sample (n=128) |
|---|--:|--:|
| **fundraising, log2(D receipts / R receipts)** | **+0.60** *(n=128)* | **+0.60** |
| incumbency | +0.43 | +0.41 |
| candidate quality index | +0.34 | +0.36 |
| local trend | +0.31 | +0.30 |
| midterm year | ≈0 | +0.13 |

Fundraising leads on either basis. The relationship is monotonic, not driven by a tail.
Sorting races by who out-raised whom: where the Democrat out-raised the Republican, the
Democrat beat the district baseline by an average of **+4.22** points; where funding was
even, **+2.11**; where the Republican out-raised, **−1.77**.

> **The cell frame is pinned, and it has moved twice — each time deliberately, and each
> time recorded here.** The fundraising feature is matched against `candidate_finance`,
> a live table: the frame behind the first draft held **109** both-side cells and gave
> +0.55, +4.20, +2.37 and −1.93; loading more filings took it to 129 and +0.58. An
> external referee then caught the linkage itself resolving candidates by
> `(cycle, last name, first initial)` alone, pooled across all four office codes — and
> the collision audit (`scripts/diag_finance_linkage_audit.py`) found 2 of 326 lookups
> attaching the wrong records, one of them crediting a **different candidate of the same
> name** in another chamber with $190K his namesake never raised. The linkage is now
> scoped to the cell's own office and district, which removes that cell's finance pair
> entirely (**128** both-side cells) and moves the correlation to **+0.60**. The
> universe is unchanged at 163 baseline-scorable cells, and so is every conclusion —
> fundraising remains the largest measured factor on either sample. The frame is frozen
> at `docs/reference/overperformance_cells_2026-08-15.csv` (its predecessor is retained
> for audit), which is what `scripts/verify_money_votes.py` asserts against, so a reader
> re-running the derivation gets the figures this paper prints rather than whatever the
> table holds that week.

Taken alone this looks like a straightforward answer, and it is the number a campaign
consultant would quote. The rest of this paper is about why it is not one.

---

## Finding 2 — Three manifestations of money, and what each can and cannot test

Candidate receipts, a campaign's own spending allocation, and outside groups' independent
expenditure are **three different treatments**, not three measurements of one. A causal
effect of candidate spending can coexist with a null for independent expenditure, and vice
versa. This section examines each manifestation on its own terms and states what its test
does and does not estimate; none of the three supplies identification of the causal effect
the title asks about, and they are not presented as three replications of one null.

### 2a. Spending composition carries no incremental predictive information — an exploratory cut, not a causal test

If spending buys votes, *how* it is spent might matter — a campaign that puts its money
into field organizing might perform differently from one that puts it into television.
Washington's Public Disclosure Commission publishes itemized expenditures with a purpose
code per transaction (Socrata `tijg-9zyp`; 272,320 candidate rows 2018–2024, $286M, ~62% of
dollars carrying a code). From these, `scripts/diag_expenditures_vs_residual.py` derives
each candidate's field, media, and professional *shares* of coded operational spend, and
tests them against the residual.

Two design limits are stated before any number, because they are what demote this cut to
exploratory. **It measures only the Democratic campaign's allocation** — if Republican
field spending moves Democratic vote share, this test cannot see it; a race-level causal
design would need both campaigns, or their difference. And **allocation mix and spending
level are different treatments**: a world where money has a substantial causal effect but
campaigns optimally converge on similar mixes produces exactly the zero correlations below.
What this cut can test is narrow — whether spending *composition* carries predictive
information the core features lack — and that is all it is offered as.

The shares correlate with the residual at essentially zero — field **+0.02**, media
**+0.04**, professional **−0.05**. Total spend correlates at +0.23, but that is the
fundraising scale signal from Finding 1 arriving again, not allocation. The sharper cut is
cross-cycle holdout: fit on 2022, predict 2024. The first metric below is the **squared
holdout correlation** — the square of the Pearson correlation between predictions and
holdout outcomes. An earlier draft called this "holdout R²", which it is not: squaring
discards sign, and three of the four holdout correlations are wrong-signed (r = +0.02,
−0.12, −0.18, −0.17), so the squares flatter the models. The standard **predictive R²**
(1 − SSE/SST) is therefore reported beside it, and it is negative for every
specification — the models predict *worse than the holdout mean*.

| model | squared holdout correlation | predictive R² |
|---|--:|--:|
| core candidate-quality features | 0.000 | −1.09 |
| core + field share | 0.015 | −2.75 |
| core + all allocation shares | 0.031 | −3.00 |
| allocation shares alone | 0.028 | −0.18 |

In-sample squared correlation rises from 0.037 to 0.101 as shares are added while the
holdout numbers worsen — the signature of overfitting, not signal. One leakage
caveat is owed on the word "holdout": the target residual comes from the forecast model,
whose coefficients were tuned on the full residual matrix, so 2024 outcomes participated
in constructing the variable 2024 is here held out on. Allocation itself never enters that
first stage, but a fully clean version would fit the residualization on 2022 alone — one
more reason this cut is exploratory rather than a causal null.

> **This block is pinned too, and eight of its figures moved when it was (2026-08-01).** The
> allocation frame is derived against the forecast model's *residual*, so it shifts whenever
> the model does — and the model has moved since this section was written, while the
> fundamentals baseline behind Finding 1 has not. That is why the two figures computed
> against `overperf` rather than `residual` are unchanged (field-vs-overperformance −0.24,
> and both persistence coefficients) and every figure computed against the residual moved:
> media +0.05 → +0.04, professional −0.03 → −0.05, total spend +0.26 → +0.23, and the four
> holdout cells with the in-sample pair. The 2026-08-15 linkage correction re-pinned the
> residuals a second time, moving the holdout cells again by similar amounts (the
> allocation-alone cell has run 0.041 → 0.022 → 0.028 across the three bases) while every
> correlation held at its printed precision. **Nothing in the finding changes on any
> basis** — the holdout numbers stay at the floor, most holdout correlations are
> wrong-signed, and the shares carry no out-of-sample information. The frame is frozen at
> `docs/reference/expenditures_vs_residual_2026-08-15.csv`, which
> is what `scripts/verify_money_votes.py` asserts the correlations against. Notably, allocation *is* a real and
stable candidate trait: field-share persistence across cycles runs r = 0.83 and media-share
r = 0.998. It is a stable feature that carries no information about the outcome. And the
one directional hint runs against the folk theory: field share correlates **−0.24** with
raw overperformance, so more ground spending is associated with slightly worse results, not
better.

### 2b. The forecast model discards the money term — a forecasting result, not a causal falsification

A second observation comes from an unusual direction: the forecasting model this series
relies on was tuned without reference to this question, and it independently concluded
that fundraising adds no *predictive* information once the baseline is known. What that
does and does not show is stated at the end of this subsection, because an earlier framing
over-claimed it.

In Washington's post-2022 districts, where the redistricting boundary filter collapses
history to a single post-redistricting cycle, the model **zeroes its fundraising-advantage
term entirely**. The reason is that the single-cycle baseline already absorbs it: the
incumbent ran in that cycle, their fundraising advantage manifested in that result, and
adding the term on top double-counts. Before this correction the model predicted a D+28
result in a district whose incumbent's actual history ran D+5 to D+8. The term was not
dropped for ideological reasons but because leaving it in produced worse forecasts.

What this establishes is a **forecasting result**: fundraising adds no incremental
predictive information conditional on the district's own recent result. What it cannot
establish is anything causal, because conditioning on a prior outcome absorbs both signal
and treatment. Two worlds are observationally identical here: one where fundraising is
merely a marker whose information was already present in past results, and one where
fundraising **caused** part of the previous result, so its causal effect is now embedded
in the lagged outcome the model conditions on. An earlier draft counted this as one of
three causal nulls; it is not one, and it is not offered as evidence against a money
effect.

### 2c. The directional test runs, and cannot sign the effect

The third test is the closest thing to a directional design the data permits.
`scripts/diag_ie_vs_margin.py` regresses each race's *fundamentals-net residual* — actual
minus model-predicted Democratic share, not the raw margin — on the net pro-Democratic
independent-expenditure advantage. Using the residual rather than the margin is what makes
this a test of money's marginal effect rather than a restatement of district partisanship.

Across the 34 scorable district-cycles the slope is **+0.515 points of residual per $1M net
pro-Democratic IE, with a 95% bootstrap interval of −0.600 to +2.821 and Pearson r = +0.186**.
Read that interval for what it is: **an interval for the observational OLS slope, not for
the causal effect of $1M of IE.** Under uncontrolled confounding the causal effect can lie
outside it, and even an infinitely narrow interval around zero would not identify a zero
causal effect — a narrower interval around a better-estimated association is still an
association. Within its own terms the interval crosses zero, so no association can be
asserted; it is also wide enough to be compatible with associations that would decide a
close race. The point estimate is not a finding, and neither, on its own, is the width:
the design is what prevents a stronger statement.

**The slope is a single-district leverage result, and that is reported rather than
smoothed over.** The leave-one-out sweep this paper already applies to its placebo and
legislative specifications, applied to this headline regression, runs from **−0.035**
(dropping WA-08 2018) to **+0.832** (dropping WA-03 2024): deleting one race erases the
positive slope entirely. WA-08 2018 pairs the panel's largest net pro-Democratic IE
(+$8.26M) with a +8.78-point residual and carries a Cook's distance of **0.69** in a
34-observation regression; dropping every WA-08 observation gives **−0.065**. The
case-resampling interval also treats race-cycles as iid while the panel measures the same
ten districts repeatedly — in tension with this paper's own placebo discussion of
persistent district traits — so a **district-clustered bootstrap** (10 clusters) is
reported beside it: **−1.595 to +1.268**; clustering on era × district across the 2022
redistricting boundary (20 clusters) gives −1.016 to +1.390. Every version spans zero, and
the clustered intervals are materially wider. On a standardized treatment scale the slope
is **+0.93 points per one standard deviation of net IE** (SD = $1.80M in this panel) —
the scale that makes the legislative comparison below meaningful.

The sign of the point estimate should be treated with particular caution, because it is not
stable. An earlier version of this analysis, run on 2024 alone, reported a *negative* slope
of −0.39 (Pearson r = −0.39, n = 7) and read it as the textbook endogeneity signature:
outside money flowing toward the side that is struggling. Extending the panel to five cycles
reversed the sign. Both readings are consistent with the same underlying truth, which is
that at these sample sizes the sign is a coin flip and the interval is the only honest
summary. Endogeneity remains the correct prior — spending is targeted at expected closeness,
not assigned at random — and it is precisely why a signed estimate from this design would be
uninterpretable even if the interval excluded zero.

The single most instructive case is the most heavily funded. **Washington's 3rd
Congressional District in 2024 attracted $18.61M in total independent expenditure — the
largest in the panel, and 22nd nationally among the 387 U.S. House races drawing any — with
a net $6.09M advantage on the Democratic side. It finished 0.06 points from its
fundamentals-based prediction.** Eighteen million dollars of outside money, and the race
landed almost exactly where the district's underlying partisanship said it would. That is a
single observation and proves nothing on its own, but it is a striking one.

*(A previous draft of this section called WA-03 "the most IE-saturated House race in the
country" at $40.1M. Both halves were artifacts of a data defect: FEC reports most
independent expenditures twice, once as a 24/48-hour notice and again on the periodic
Schedule E, and the loader summed both. At the true $18.61M the race ranks 22nd; at the
doubled $40.1M no race in the country exceeded it, which is what manufactured the
superlative. The defect and its correction are documented in the data section below.)*

---

## Finding 3 — The test runs now, and is still underpowered

The design in 2c is the right one, and until recently it could not be run at all. What has
changed is worth stating precisely, because the limitation that remains is different in kind
from the one it replaced.

**Directional independent-expenditure data now spans five cycles.** FEC Schedule E carries a
support-or-oppose flag and a district, which is what makes a directional test possible at
all. The Washington U.S. House panel holds **2,215 flagged rows across all ten districts and
$75.7M**, distributed as follows:

| cycle | flagged rows | total IE | scorable races |
|---|---:|---:|---:|
| 2018 | 887 | $19.73M | 8 |
| 2020 | 374 | $5.46M | 9 |
| 2022 | 460 | $25.06M | 10 |
| 2024 | **444** | **$25.4M** | 7 |
| 2026 | **50** | **$98K** | 0 |

2026 is a partial current-cycle trickle with no national-environment data to net a residual
against and no result to net it from, so it contributes nothing; the four completed cycles
yield **34 scorable Washington House races**, uncontested districts dropping out.

**Three of those four cycles were absent from an earlier version of this paper**, which
reported a single scorable cycle and seven races and called that limitation its most citable
result. The backfill that removed the limitation is the one the earlier draft itself
prescribed. It took about five minutes of API time — the cost was never the obstacle, and
saying otherwise was the draft's own error. What made the earlier figures wrong was not the
missing cycles but a de-duplication defect described in the data section below, which
inflated every independent-expenditure total by roughly a factor of two.

**The state-legislative money enters the test too, and it does not rescue it.** Washington's
PDC records **$51,723,243.45** of independent expenditure identifying a legislative
candidate across 2018–2024, on **4,653 filed rows carrying a support/oppose direction, a
named candidate, a filer id and a jurisdiction on 100% of them**. Matched to the same
fundamentals-net residual, that yields **129 scorable district-cycles** — close to four
times the 34-race federal panel — and the estimate remains uninformative:

| specification | n | cells with ≥$25K | slope | 95% bootstrap | district-cluster 95% | Pearson r |
|---|---:|---:|---:|---|---|---:|
| **express advocacy, race-matched** | 129 | 17 | **+4.871** | −29.126 to +24.941 | −38.251 to +14.109 | +0.085 |
| express advocacy, district-aggregate | 129 | 53 | −2.043 | −11.170 to +3.203 | −11.278 to +2.816 | −0.053 |
| all directional, race-matched | 129 | 28 | −3.836 | −15.619 to +3.664 | −18.890 to +3.225 | −0.083 |
| all directional, district-aggregate | 129 | 60 | +0.107 | −5.090 to +4.790 | −6.523 to +5.770 | +0.004 |

*Every specification now runs on the full 129-cell scorable universe: a scorable race that
attracted no race-matched IE enters with net IE = 0 rather than dropping out. An earlier
version dropped those cells from the race-matched rows (n = 127), treating zero treatment
as missing data; the correction, prompted by an external referee, moved the primary slope
from +4.890 to +4.871 and no conclusion. The district-cluster column resamples the 37
legislative districts rather than individual race-cycles, for the same reason as the
federal panel's clustered interval.*

**Every interval spans zero and the sign is specification-dependent.** Two of the four
reverse sign on the deletion of a single race. Multiplying the cells by nearly four did
not narrow the answer, and the reason is worth stating exactly, because "the sample was
too small" is not it: **raw cell count is not the binding quantity; usable variation in
treatment is.** Only 13–47% of cells attract any material independent expenditure, so the
slope is identified by a few dozen contests whichever specification is chosen — and those
are exactly the contests money selected for being close. The panels are also not
comparable on raw interval width: a $1M x-unit is an ordinary congressional IE campaign
and an enormous intervention in a legislative contest. On the standardized scale, one
standard deviation of net IE moves the point estimate **+0.93** points in the federal
panel (SD $1.80M) against **+0.33** points in the primary legislative specification
(SD $0.067M) — with every interval, standardized or not, spanning zero.

Two properties of the PDC record decide the specification and are not incidental. **Three
quarters of the directional dollars are electioneering communication, not express
advocacy** — $38.70M against $13.03M — and the two run in opposite directions, express
advocacy 78% *for* candidates and electioneering 61% *against* them. Pooling them inverts
the panel's directional balance, which is why the two are reported apart rather than summed.
And the filing identifies a candidate's *chamber* but not their House position, while the
outcome is a single contest; the race-matched rows count only money naming a candidate on
the ballot in the scored race, and the district-aggregate rows show what attributing all
three seats' money to one seat's residual does instead.

*(An earlier version of this paper reported that this money "carries no support/oppose flag"
on all but 5 of 4,456 rows and "cannot enter a directional test at all", and treated that as
a limitation of Washington's disclosure regime. It was a limitation of our own extraction.
The PDC publishes direction in the **C6.3 "Identified Entities"** section of form C-6, in the
same dataset the loader was already reading and had been reading all along; the loader
consumed only the C6.2 itemized-expenditure section. The correction is documented in
[`pdc-c6-direction-audit.md`](pdc-c6-direction-audit.md), and the ingest is
`load_pdc_ie_targets`. The conclusion this paper draws is unchanged — the point estimate is
still unsignable — but the reason is different in kind, and the earlier reason was wrong.)*

**The data defect, and why it is reported rather than quietly fixed.** FEC files most
independent expenditures **twice** — once as a 24- or 48-hour notice on Form 24, then again
on the committee's periodic Form 3X Schedule E — under different transaction ids. Nothing
about the pair looks duplicated. An earlier loader summed both, which roughly doubled every
total in this paper: WA-03's 2024 IE was reported as $40.1M against a true $18.61M, and the
same factor applied to every district and cycle. It was caught by reconciling against FEC's
own per-candidate aggregate, which returned almost exactly half the loaded figure for every
Washington House candidate checked.

Two consequences deserve stating plainly. The inflated figure is what produced the claim
that WA-03 was the most IE-saturated House race in the country: at $40.1M nothing exceeded
it, and at the correct $18.61M twenty-one races do. And a defect of this shape is invisible
to internal consistency checks, because every figure derived from the contaminated table
agreed with every other. Only an external source could catch it. `scripts/diag_fec_ie_bulk_crosscheck.py`
is that check, and it needs no API key: it reconciles the loaded totals against FEC's public
bulk files, so anyone reproducing this work can verify the independent-expenditure figures
without credentials. All five cycles reconcile to those files exactly.

### The two secondary tests now run, and neither discriminates

An earlier draft named an early-versus-late spending split and a next-cycle placebo as the
tests a multi-cycle panel would unlock. Both were run
(`scripts/diag_ie_early_late.py`, `scripts/diag_ie_next_cycle_placebo.py`). Both return
nothing that survives inspection, and the *reason* they fail has changed: it is no longer
the number of cycles but the number of races within them that attract money at all.

**Early versus late.** Splitting each race's independent expenditure at 30 days before
election day and regressing the residual on both windows jointly gives **−1.128 points per
$1M of early money and +2.129 of late money**, both intervals spanning zero, R² 0.083.
Late exceeds early at every cutoff tried (14, 30 and 60 days), which is the one consistent
pattern — but the early coefficient changes sign across those cutoffs, and at 60 days the
two nearly converge, which is what a split carrying no information looks like as the window
widens toward the pooled total. The deeper problem is identification: of 34 scorable races,
**15 attracted any material independent expenditure and only 11 attracted it in both
windows**, with early and late spending correlated at +0.753 among those. Eleven
observations cannot separate two collinear regressors.

The direction is worth one sentence, and no more. Under the endogeneity account this paper
argues for, late money should look *worse* than early money, because committees move
resources late into races that have visibly deteriorated, so lateness partly encodes bad
news about the recipient. The point estimates run the other way. At these intervals that
observation is decoration, not evidence.

**The next-cycle placebo, and why the redistricting boundary halves it.** Money spent in
2024 cannot have moved a 2022 result, so regressing the cycle-*t* residual on cycle-*(t+1)*
independent expenditure should return zero if the contemporaneous association is causal.
Washington redrew every congressional district for 2022, so a pair spanning that boundary
compares a district label to itself across a redraw and tests nothing about a district's
persistent character; those nine pairs are reported separately and never pooled. That
leaves **14 same-era pairs**, on which the placebo returns **+0.878** against a
contemporaneous **+1.108** estimated on the same cells — future money apparently
"predicting" a past residual at four-fifths the strength of concurrent money, which if
precisely estimated would be a serious problem for any causal reading.

It is not precisely estimated. **Deleting one race reverses the placebo's sign** (dropping
WA-03's 2022 pair moves it from +0.878 to −0.716), and deleting one race quadruples the
contemporaneous comparison (+1.108 to +4.415). Both numbers describe individual contests
rather than a relationship. The placebo therefore cannot discriminate, which is the
underpowered outcome and not a clean bill of health — it neither corroborates the
contemporaneous estimate nor convicts it of confounding.

One incidental result is worth recording because it is cleaner than either regression:
across same-era pairs, a district's net independent expenditure correlates with its own
next-cycle figure at **+0.031**. Washington's outside money does not persist in a seat. It
arrives where a given cycle's contest is expected to be close, and goes elsewhere when it
is not — which is the endogeneity mechanism visible directly, without a regression.

**What more cycles would and would not fix — now partly answered by the legislative panel.**
The natural objection to a null on 34 races is that 34 is too few. The state-legislative
extension is the closest thing to a test of that objection this record affords — with its
scope stated exactly: it holds the **estimator** fixed and multiplies the cells by nearly
four, to 129, but under a **related, non-equivalent measurement system** (PDC C-6 rather
than FEC Schedule E; three-quarters of the directional dollars electioneering rather than
express advocacy; chamber-level House reporting; one scored contest per district-cycle),
so it is an external extension, not a pure sample-size experiment. Within that scope the
answer is informative: the interval did not narrow and the sign did not settle; it became
*specification*-dependent instead, and the standardized comparison above shows why —
usable treatment variation, not cell count, is the binding quantity. More cycles would still narrow the
interval in 2c, which spans −0.600 to +2.821, and would give the placebo enough same-era
pairs to be worth running. They are not freely available. FEC's Schedule-E record extends back well past this panel, but the binding
constraint is the *dependent variable*: the residual requires a fundamentals baseline, the
baseline requires a Cook-style PVI, and PVI requires presidential results from before the
target year. Washington's loaded results begin with the 2016 general, so a 2016 residual is
undefined for want of 2012 presidential precinct data — and the Secretary of State's bulk
export, which serves 2014 and 2016, returns 404 for 2012. Extending backward is therefore a
data-acquisition project against an older and less uniform source, not a re-run of the
loader. Extending forward is automatic but slow: November 2026 adds one cycle.

**And none of it would make the estimate identified.** The panel has no exogenous variation
in spending; spending is aimed at expected closeness. A narrower interval around a
better-estimated association is still an association. Settling the question needs a design
this record cannot supply — a discontinuity, a lottery, or an experiment — and no quantity
of FEC backfill produces one.

---

## What it means

Money in Washington elections is **clearly a marker of candidate strength; whether it is
*also* a mover of votes, this design does not establish either way.** Those are not
mutually exclusive: a strong candidate can attract money and then gain a further point
*because* of the spending, and nothing in an observational record decomposes the two. The
three manifestations examined here each fall short of identification in its own way:
allocation is an exploratory composition cut that predicts nothing out of sample, the
forecast model's discarded term is a forecasting result that cannot separate marker from
embedded effect, and the directional cross-section's positive slope is a single-district
leverage result whose every interval — case-resampled or clustered — spans zero.

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
  cut is observational with no exogenous variation and no instrument. The +0.60 correlation
  is exactly what a real causal effect would also produce; the nulls are consistent with a
  true zero *and* with an effect the data is too thin to detect — and no bootstrap interval
  in this paper bounds a causal effect, only an observational slope.
- **The allocation null is underpowered and tests the wrong thing twice over.** Coverage is
  40 of 129 legislative baseline cells, holdout n runs 15–22, and it tests spend *mix*, not
  spend *level*. It cannot rule out an effect of simply having more money.
- **The IE panel is n = 34, its sign is not stable, and its point estimate is a leverage
  result.** The estimate moved from −0.39 to +0.515 when the panel went from one cycle to
  four, and deleting the single highest-leverage race (WA-08 2018, Cook's distance 0.69)
  moves it to −0.035. Read the intervals — including the wider district-clustered one —
  not the coefficient; a paper quoting either sign as a result would be over-reading its
  own data.
- **State-legislative IE now enters the analysis, and its specification is the live
  limitation.** An earlier version of this bullet said it was excluded entirely for want of a
  directional flag. That was wrong about the record rather than about the analysis: the PDC
  publishes direction in form C-6's C6.3 section, which the loader had not been reading, so the
  $51.7M panel is in and contributes 129 scorable district-cycles (Finding 3). What remains is
  that three quarters of the directional dollars are electioneering communication rather than
  express advocacy and the two run in opposite directions, and that the filing names a
  candidate's chamber but not their House position — so the point estimate's sign is
  specification-dependent rather than merely imprecise.
- **Only the persuasion channel is examined.** Access, agenda-setting, candidate entry
  deterrence, and the effect of money on *who runs in the first place* are all untested and
  all plausible routes by which money could matter without moving a general-election margin.
- **Coverage gaps favor larger campaigns.** PDC mini-reporting excludes the smallest
  campaigns, and 38% of expenditure dollars carry no purpose code.

---

# Appendices

## Appendix A — The objections, in full

**1. "You found +0.60 and then explained it away."** The correlation is real and the paper
leads with it. The objection has force: the burden of proof for dismissing the largest
correlation in the dataset should be high. But nothing here dismisses it, and nothing here
is entitled to: what the paper declines to do is *sign* it causally, because the
observational record cannot separate selection into money from an effect of money.
Allocation carrying no out-of-sample signal and the forecast model finding the term
redundant against the baseline are consistent with money tracking a strength that already
exists — and equally consistent with a real effect whose information is already embedded
in the baselines those tests condition on. The directional cross-section decides nothing
in either direction: its positive point estimate rests on one district and every interval
around it spans zero.

**2. "Absence of evidence is not evidence of absence."** Correct, and the paper's title
question is answered "cannot tell," not "no." The allocation test is underpowered, the IE
interval is too wide to sign, and neither speaks to spend *level* with exogenous variation.
This is stated in the body rather than buried, because the alternative — presenting a null
as a finding of no effect — would be the more serious error.

**3. "The IE slope is just strategic targeting, which you admit."** Yes, and that is the
point rather than a flaw. Whatever its sign, the association is offered as evidence of
*endogeneity*, not of money being harmful or helpful. Spending is aimed at races expected to
be close, so the naive correlation cannot be read causally in either direction — which is
the paper's central methodological claim, and the reason the sign reversing between drafts
changes nothing about the argument.

**4. "WA-03 is one race."** It is, and it carries no inferential weight. It appears because
it is the most extreme case in this panel — the largest independent-expenditure total in
five cycles of Washington House races, landing 0.06 points from its fundamentals — and
because a reader who suspects the null is an artifact of small money should know what the
largest observation looks like. It is not, as an earlier draft claimed, the most
IE-saturated House race in the country; it ranks 22nd.

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
- **Independent expenditures.** FEC Schedule E for the **2018–2026 cycles**, carrying
  support/oppose and district, read with `is_notice=false` so each expenditure is counted once
  (Appendix C); PDC independent-expenditure records for state legislative races, which carry
  amounts, races **and direction** — the support/oppose flag sits in form C-6's C6.3
  "Identified Entities" section (Finding 3). *(This entry read "for the 2024 cycle" and "no
  directional flag" until 2026-08-10. Both were true of the extraction, not of the source, and
  both contradicted Finding 3 in the same document.)*
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
- **A 129 and a 128 appear in this paper, and they are not the same population.** Of the 163
  baseline-scorable cells, **129 are legislative** and 34 congressional; that legislative 129 is
  the denominator in the allocation-coverage limit ("40 of 129") and is the frame Finding 3's
  state-legislative panel is matched to. Separately, **128 of the 163 carry both-side finance**
  and are Finding 1's correlation frame — the two counts were equal by coincidence (both 129)
  until the 2026-08-15 linkage correction removed one wrongly-attached finance pair, and the
  earlier collision of names is recorded as a withdrawn claim in `who-decides-washington.md`.
- **Fundraising feature.** Raw `log2(D receipts / R receipts)` matched against
  `candidate_finance`, **scoped to the cell's own office and district** since 2026-08-15:
  the key is (cycle, last name, first initial) *within* office `H` and the padded district
  for congressional cells, or offices `SR`/`SS` and the bare district for legislative
  ones — the same dual-form office/district rule the codebase's finance queries use. The
  earlier key omitted office and district and took the maximum receipts across all four
  office codes, which is far weaker entity resolution than the companion donor papers
  allow themselves; the collision audit (`scripts/diag_finance_linkage_audit.py`) measured
  the damage at 2 of 326 lookups — one same-key maximum taken from the wrong district, and
  one candidate credited with a **same-name namesake's** $190K from another chamber. The
  feature is computed independently of the model's own capped fundraising term.
- **Allocation shares.** Field, media and professional shares of *coded operational* spend
  per candidate, so the measure is composition rather than level. Cross-cycle holdout fits
  2022 and predicts 2024, the same bar used to reject the candidate-quality index earlier
  in this project.
- **IE residual test.** Net pro-Democratic IE = support-D plus oppose-R minus support-R
  minus oppose-D, per race, from FEC Schedule E. The dependent variable is the
  fundamentals-net residual, not the margin. Uncontested races and races without
  national-cycle data are dropped, leaving 34 of 50 candidate race-cycles scorable.
- **Notice de-duplication.** FEC Schedule E is read with `is_notice=false`, which selects the
  periodic Form 3X filing and excludes the 24/48-hour Form 24 notice restating the same
  expenditure. Memo rows (`memo_code='X'`) are excluded as subtotals of money itemized
  elsewhere. Both exclusions are properties of the summing view, not of the stored table,
  which retains the notice rows so the reporting lag stays observable.
- **Estimator and intervals, everywhere.** Every slope in this paper — the federal IE
  regression, all four state-legislative specifications, the placebo pair, and the early/late
  split — is estimated by **ordinary least squares** (simple bivariate OLS; the early/late
  split is a two-regressor OLS), and every correlation is Pearson's r. Every "95% bootstrap
  interval" is a **case-resampling (pairs) percentile bootstrap with 5,000 replicates and a
  fixed seed**, so the intervals are deterministic and reproduce exactly. No
  heteroskedasticity-robust or weighted variant is used anywhere; at these sample sizes the
  honest summary is the interval, not the standard-error recipe.
- **Inference threshold.** The IE script refuses to report a slope as inferential below 10
  scorable races and prints its data inventory instead. That threshold is now cleared; the
  behavior is deliberate and should be preserved.
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

Every Washington congressional race with FEC Schedule-E data on disk, 2018–2024
(`scripts/diag_ie_vs_margin.py`). "Residual" is actual minus model-predicted Democratic
share; *unscorable* means the race was uncontested or lacked national-cycle data. The 2026
cycle is omitted: it carries 50 flagged rows and no scorable race.

| race | net pro-D IE | total IE | residual (pp) | actual margin |
|---|--:|--:|--:|--:|
| cd01 / 18 | $0.00M | $0.00M | −4.15 | +4.74 |
| cd02 / 18 | $0.00M | $0.00M | — *(unscorable)* | — |
| cd03 / 18 | +$1.06M | $3.18M | +2.18 | −5.36 |
| cd04 / 18 | +$0.03M | $0.03M | −4.62 | −25.55 |
| cd05 / 18 | +$0.03M | $0.23M | −1.45 | −9.46 |
| cd06 / 18 | $0.00M | $0.00M | −4.51 | +27.77 |
| cd07 / 18 | $0.00M | $0.00M | +5.82 | +67.12 |
| cd08 / 18 | +$8.26M | $16.28M | +8.78 | +4.84 |
| cd09 / 18 | +$0.01M | $0.01M | — *(unscorable)* | — |
| cd10 / 18 | $0.00M | $0.00M | −6.07 | +23.09 |
| cd01 / 20 | $0.00M | $0.00M | +1.74 | +17.25 |
| cd02 / 20 | $0.00M | $0.00M | −3.25 | +26.48 |
| cd03 / 20 | −$1.54M | $3.79M | −0.20 | −13.01 |
| cd04 / 20 | +$0.01M | $0.01M | −1.21 | −32.63 |
| cd05 / 20 | −$0.15M | $0.15M | −0.72 | −22.82 |
| cd06 / 20 | $0.00M | $0.00M | −2.84 | +18.90 |
| cd07 / 20 | $0.00M | $0.00M | +8.01 | +66.37 |
| cd08 / 20 | +$0.02M | $0.12M | +0.03 | +3.57 |
| cd09 / 20 | $0.00M | $0.00M | +7.17 | +48.52 |
| cd10 / 20 | +$0.76M | $1.38M | — *(unscorable)* | — |
| cd01 / 22 | $0.00M | $0.00M | +4.91 | +27.13 |
| cd02 / 22 | $0.00M | $0.00M | −3.51 | +20.35 |
| cd03 / 22 | +$1.45M | $5.73M | +9.16 | +0.87 |
| cd04 / 22 | −$0.42M | $1.74M | −2.40 | −36.05 |
| cd05 / 22 | −$0.11M | $0.11M | +1.46 | −19.23 |
| cd06 / 22 | $0.00M | $0.00M | −0.96 | +20.14 |
| cd07 / 22 | $0.00M | $0.00M | +9.19 | +71.49 |
| cd08 / 22 | −$0.20M | $17.47M | +0.38 | +6.90 |
| cd09 / 22 | $0.00M | $0.00M | +5.59 | +43.49 |
| cd10 / 22 | $0.00M | $0.00M | −3.22 | +14.13 |
| cd01 / 24 | $0.00M | $0.00M | +7.59 | +26.35 |
| cd02 / 24 | $0.00M | $0.00M | — *(unscorable)* | — |
| **cd03 / 24** | **+$6.09M** | **$18.61M** | **+0.06** | **+3.92** |
| cd04 / 24 | +$0.99M | $3.35M | — *(unscorable)* | — |
| cd05 / 24 | −$0.09M | $0.23M | +1.55 | −21.25 |
| cd06 / 24 | +$2.74M | $2.74M | −3.52 | +13.67 |
| cd07 / 24 | $0.00M | $0.00M | +13.70 | +68.35 |
| cd08 / 24 | +$0.42M | $0.42M | +6.82 | +8.18 |
| cd09 / 24 | $0.00M | $0.00M | — *(unscorable)* | — |
| cd10 / 24 | $0.00M | $0.00M | −1.17 | +17.35 |

Thirty-four scorable races. Party attribution is effectively complete — $0.03M of the
$75.7M total is unresolvable to a side, so the slope is not a coding artifact. Note how
much of the variation sits in races with **no** independent expenditure at all: cd07's
+13.70 residual in 2024 and +9.19 in 2022 both occur at $0 IE, which is a compact
illustration of why even thirty-four observations cannot separate money's effect from
everything else that varies across districts and cycles.

Note also the two largest totals in the panel, cd08 in 2018 ($16.28M) and 2022 ($17.47M),
which bracket WA-03's 2024 $18.61M. All three landed within nine points of their
fundamentals and two of the three within one point.

## End note — data, reproduction, and series

```
# Finding 1 — money vs overperformance across 163 race-cycles:
python scripts/diag_overperformance_patterns.py

# Finding 2a — spend allocation vs residual, cross-cycle holdout:
python scripts/diag_expenditures_vs_residual.py

# Finding 2c — federal IE vs fundamentals-net residual (34 WA U.S. House cells).
# In the public repo this reads the pinned panel and recomputes the slope, the
# bootstrap interval and Pearson r from it; the residual itself needs the
# forecast model, which is not published.
python scripts/diag_ie_vs_margin.py

# Finding 3 — the same design on WA legislative races (129 cells, PDC C6.3).
# Load the direction data first; it is a separate section of form C-6:
python main.py load --district ld01 --pdc-ie-targets
python scripts/diag_pdc_ie_vs_margin.py

# The C6.3 reconciliation the legislative panel rests on (needs no database):
python scripts/diag_pdc_c63_reconciliation.py

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
