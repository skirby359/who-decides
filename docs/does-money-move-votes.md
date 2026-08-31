# Does Money Move Votes in Washington?

### An identification failure, measured: an exceptionally strong money–performance association that no available observational decomposition can separate from selection

**Stephen Kirby** · Tikor Consulting · July 2026

*AI-assisted drafting and analysis review. All reported statistical summaries can be
recomputed from public code and the pinned derived panels cited below. **The
unreproducible step is one column, and `scripts/verify_residual_construction.py` marks the
boundary exactly.** The residual is a subtraction between two published columns —
`residual_pp = actual_dem_pct − predicted_dem_pct`, and all **34** scorable district-cycles
reconcile — the model's equation and its `v-jun17` coefficient set are public in
`config/national_data.py`, and every statistic built on the residual runs from a bare public
clone. What cannot be regenerated is `predicted_dem_pct` itself, because the forecast
implementation is the campaign product this project also sells. That narrows the limitation
rather than removing it: a reader who doubts the *model* still cannot check the model, and
publishing it is the only thing that would. The paper
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
is estimable across **four completed cycles** and thirty-four scorable Washington
congressional races — the inventory spans five, but 2026 contributes no scorable race —
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
is clearly a **marker** — of performance the modeled fundamentals do not capture, with
candidate strength one latent mechanism among several that would produce the same
association; whether money is *also* a mover of votes is
not established either way, because every available observational decomposition fails to
separate selection into spending from an effect of spending. The failure is one of
identification, not merely of data quantity.

**Keywords:** campaign spending; independent expenditures; electoral effects; endogeneity;
null results; data availability; state legislative elections; Washington.

---

## The question, and why it resists an answer

The preceding papers in this series each end at the same edge. The turnout paper shows the
electorate returning odd-year ballots is markedly older and far smaller than the
presidential one. The safe-seat paper shows most general-election results are not close and
that many ballots offer no Democrat-versus-Republican choice at all — while expressly
declining to date when any seat's outcome became fixed. The donor paper shows the population funding those
races is not representative of the electorate voting in them — donors skew sharply older,
more geographically concentrated and, where party is observable, more Democratic, while
being *more* likely to vote, not less. Each invites the obvious next question: **so does
the money actually change who wins?**

*(Until 2026-08-29 this paragraph said the safe-seat paper "shows most general elections
are settled before November" and that the turnout paper "shows an older, smaller
electorate decides off-cycle races". Neither is a claim its owner makes: the turnout
paper measures who is credited with an accepted ballot, not who votes in a given contest,
and the safe-seat paper expressly withdrew the temporal inference — an ex-post margin
cannot date the binding decision. Caught by an external referee reading the series end to
end; the companions' own abstracts are the operative statements.)*

It is the hardest question in the series, and the reason is structural rather than
technical. Campaign money is *endogenous to candidate strength*. Strong candidates attract
money; money then appears alongside strong results. Donors and independent-expenditure
committees also behave strategically, moving resources toward races they judge close and
toward candidates they judge threatened — which can invert the naive correlation entirely,
making spending look harmful. Untangling this is a fifty-year-old problem in political
science (Jacobson 1978), and the credible answers come from designs this data does not
support: instrumental variables (Gerber 1998), repeat-challenger panels (Levitt 1994),
randomized field experiments (Kalla & Broockman 2018), or exogenous variation in advertising
*exposure* from the mismatch between media markets and political boundaries (Spenkuch &
Toniatti 2018). The last is the closest to being available here and still is not: Washington
is split across Seattle, Spokane and Portland media markets, two of which cross a state
line, but this paper's treatment is *disclosed dollars* rather than measured exposure, and
the record carries no ad-buy or gross-rating-point data to convert one into the other.

This paper does not solve it. What it does is report what Washington's public record shows,
run the tests that record permits, and state precisely what those tests do and do not
estimate. **The contribution is the identification failure itself, characterized:** the
candidate-receipts association is exceptionally strong, the directional
independent-expenditure estimate is imprecise and leverage-dependent — two different
treatments, kept apart here as everywhere below — and even a perfectly estimated
association would not identify the
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

**The association is not a pooling artifact, and it is not one cycle.** Congressional and
legislative races raise on different scales, so a pooled correlation can be manufactured by
the gap between two groups rather than by anything inside either. That is not what is
happening: within congressional cells r = **+0.508** (n=31), within legislative cells
**+0.553** (n=97), both near the pooled figure. Nor is one cycle carrying it — **+0.514** in
2018, **+0.662** in 2020, **+0.661** in 2022, **+0.611** in 2024. What the table above does
overstate is the *independence* of its rows: an incumbent both raises more and overperforms,
and fundraising correlates with the incumbency term at **+0.631**. Removing incumbency's
linear contribution from both sides takes fundraising from **+0.598** to **+0.480**. About a
fifth of the headline is incumbency wearing a different label. The rest is not, and this is a
partial correlation rather than a causal control — it removes what a straight line in the
incumbency term explains, and nothing else.

**And it does not depend on receipts reported after the election.** Rebuilt from
per-report FEC filings on the cycle-validated authorized-committee universe and cut at the
final pre-election report, the
within-congressional correlation is essentially unchanged — **+0.506** against **+0.507**
full-cycle on the same
report-built basis (Appendix C, added 2026-08-29 — the re-pull an external referee called
this paper's last open empirical task). The cutoff also removes the final three weeks or
so of pre-election money, so this is robustness to the reporting cutoff, not a
decomposition of the post-election component.

**The 128 are not a random 128, and the selection runs one way.** The ratio is undefined
unless both sides have a receipts row, and the **35** cells that lack one average **+3.14**
points of Democratic overperformance against **+1.79** among the 128 that have it. In **25**
of the 35 only the Democrat filed at all, and **32** of the 35 are legislative. So the +0.60
is measured on the subset where both sides raised money — the more contested races — and the
cells it excludes are ones Democrats won by more. Appendix C gives the breakdown. This does
not weaken the correlation within its frame; it narrows what the frame is.

*The cell frame behind this section is pinned, and it has moved twice. The full account — what each frame held, which figures moved and what caught it — is in [Appendix F](#appendix-f--what-has-moved-and-what-caught-it).*

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

*This block is pinned too, and eight of its figures moved when it was. Account in [Appendix F](#appendix-f--what-has-moved-and-what-caught-it).*

Notably, allocation *is* a real and
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
independent-expenditure advantage. Using the residual removes the portion of vote
share the modeled fundamentals already capture, so the regression asks whether net IE is
associated with *departures* from those fundamentals rather than with district partisanship.
It does not make the regression a test of money's marginal *effect*: unobserved candidate
quality, private polling, campaign competence, anticipated closeness and late national
attention all remain inside the residual, which is the whole reason the interval below cannot
be read causally.

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

**The treatment's functional form was itself tested, because influence diagnostics on one
specification cannot tell you whether the specification is the reason for the influence.**
Net advantage assumes a dollar for a Democrat is commensurate with a dollar against a
Republican and that the two cancel linearly. That assumption discards a great deal: gross
IE across these 34 races is **$70.87M** against a summed absolute net of **$22.64M**, so
**68.1%** of the money cancels, and WA-08 2022 turns **$17.47M** of two-sided expenditure into
**−$0.20M** net — **1.1%** surviving — so the panel's second most heavily financed race enters
the regression as though almost untreated. (The **19** races the specification codes as
untreated are *genuine* zeros: none carries any gross IE. The cancellation is concentrated in
six races, and they are the six largest.) Four alternative forms were run on the same panel
(`scripts/diag_ie_functional_form.py`, which reproduces the headline above to the digit):
`asinh(net)`, a signed log, pro-Democratic and pro-Republican dollars entered separately, and
net advantage beside total intensity. **Every one has a 95% interval spanning zero**, so the
inability to exclude zero is a property of the record rather than of this paper's choice of
form. Three things follow that the single specification could not show. The *sign* instability
is partly the raw-dollar tail: under the compressed forms, deleting WA-08 2018 leaves the
point estimate positive (**+0.352**, **+0.496**) rather than flipping it to −0.035. The
cancellation assumption is approximately supported rather than merely assumed — entered
separately, the two sides carry roughly equal and opposite coefficients (**+0.567**
pro-Democratic, **−0.669** pro-Republican), which is what makes net a defensible summary even
though neither side is individually distinguishable from zero. And total intensity adds
nothing beside direction: with both in the model, intensity is **−0.051** with an interval
spanning zero while net advantage is **+0.618**. Whose money, on this record, not how much.

**Three further inference procedures were run, because a percentile cluster bootstrap over
ten clusters is the estimator the few-clusters literature warns about**
(`scripts/diag_ie_inference_sensitivity.py`). Heteroskedasticity-robust HC3 — chosen over
HC1 because it inflates high-leverage residuals, which is this panel's specific problem —
gives **−0.788 to +1.819**. An analytic cluster-robust standard error on the same ten
districts gives **−0.207 to +1.238**, *narrower* than the percentile cluster bootstrap
reported above rather than wider, which is worth stating plainly: the clustered percentile
interval is not conservative because clustering is expensive, it is wide because ten
clusters resample badly. And a wild cluster bootstrap with Rademacher weights on cluster
residuals under the null — the recommended procedure at this number of clusters — returns
**p = 0.49**. Five inference procedures now, none excluding zero. The sign is not pinned
down under any of them, which is a different and stronger claim than one wide interval.

The sign of the point estimate should be treated with particular caution, because it is not
stable. An earlier version of this analysis, run on 2024 alone, reported a *negative* slope
of −0.39 (Pearson r = −0.39, n = 7) and read it as the textbook endogeneity signature:
outside money flowing toward the side that is struggling. Extending the panel to the four
completed cycles reversed the sign. Both readings are consistent with the same underlying truth, which is
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
country" at $40.1M. At the true $18.61M the race ranks 22nd; at the doubled $40.1M no race
in the country exceeded it, which is what manufactured the superlative. The mechanism and
its record are in Finding 3's data-defect block and Appendix F.)*

---

## Finding 3 — The test runs now, and is still underpowered

The design in 2c is the most informative directional observational specification this
record permits — which is not the same as one that identifies the effect — and until
recently it could not be run at all. What has
changed is worth stating precisely, because the limitation that remains is different in kind
from the one it replaced.

**Directional independent-expenditure data now spans five cycles.** FEC Schedule E carries a
support-or-oppose flag and a district, which is what makes a directional test possible at
all. Across the four **completed** cycles the Washington U.S. House panel holds **2,165
flagged rows across all ten districts and $75.62M**, distributed as follows:

| cycle | flagged rows | total IE | scorable races |
|---|---:|---:|---:|
| 2018 | 887 | $19.73M | 8 |
| 2020 | 374 | $5.46M | 9 |
| 2022 | 460 | $25.06M | 10 |
| 2024 | **444** | **$25.37M** | 7 |
| 2026 (as of 2026-08-24) | **69** | **$490K** | 0 |

**The total counts the four completed cycles only, and the 2026 row carries a date because it
is not a closed count.** Filings for an open cycle keep arriving, so that row is an inventory
reading on a stated day rather than a quantity; it is pinned to that day
(`docs/reference/fec_ie_current_cycle_pin.csv`) so it cannot drift under the paper unnoticed.
2026 has no national-environment data to net a residual against and no result to net it from,
so it contributes nothing to any estimate here and is excluded from the total for that reason.
The four completed cycles yield **34 scorable Washington House races**, uncontested districts
dropping out.

**Three of those four cycles were absent from an earlier version of this paper**, which
reported a single scorable cycle and seven races and called that limitation its most citable
result. The backfill that removed the limitation is the one the earlier draft itself
prescribed. It took about five minutes of API time — the cost was never the obstacle, and
saying otherwise was the draft's own error. What made the earlier figures wrong was not the
missing cycles but a de-duplication defect described in the data section below, which
inflated every independent-expenditure total by roughly a factor of two.

**The state-legislative money enters the test too, and it does not rescue it.** Washington's
PDC records **$51,723,243.45** of independent expenditure identifying a legislative
candidate across 2018–2024, on **4,653** filed rows. **Every one carries a support/oppose
direction, a named candidate, a filer id and a jurisdiction — which is true by construction
and therefore not a coverage claim**, since these rows *are* the C6.3 extract and C6.3 is the
section where those four fields live. The coverage question a reader needs is different: what
share of Washington's independent-expenditure record reaches C6.3 at all. Two answers, both
derived. Within this window C6.3 carries **$70.59M** across all offices, so the legislative
slice is **73.3%** of all directionally-coded PDC independent expenditure rather than a
fraction of it. And C6.3 is the universe rather than a codable subset because it *reconciles
against the C6.2 itemised section report by report* — the check is
`scripts/diag_pdc_c63_reconciliation.py`, and it is what licenses treating a C6.3 total as
the record rather than as the part that happened to be coded.
*(An earlier version bolded the 100% as though it measured coverage; it measures the
definition of the extract. This field's history — a draft asserting the flag did not
exist at all — is in Appendix F.)* Matched to the same
fundamentals-net residual, that yields **129 scorable district-cycles** — close to four
times the 34-race federal panel — and the estimate remains uninformative:

| specification | n | cells with ≥$25K | slope | 95% bootstrap | district-cluster 95% | Pearson r |
|---|---:|---:|---:|---|---|---:|
| **express advocacy, race-matched** | 129 | 17 | **+4.871** | −29.126 to +24.941 | −38.251 to +14.109 | +0.085 |
| express advocacy, district-aggregate | 129 | 53 | −2.043 | −11.170 to +3.203 | −11.278 to +2.816 | −0.053 |
| all directional, race-matched | 129 | 28 | −3.836 | −15.619 to +3.664 | −18.890 to +3.225 | −0.083 |
| all directional, district-aggregate | 129 | 60 | +0.107 | −5.090 to +4.790 | −6.523 to +5.770 | +0.004 |

*The two panels handle zero treatment differently, and the asymmetry is deliberate rather
than unnoticed. Every legislative specification runs on the full 129-cell scorable universe: a
scorable race that attracted no race-matched IE enters with net IE = 0 rather than dropping
out. An earlier
version dropped those cells from the race-matched rows (n = 127), treating zero treatment
as missing data; the correction, prompted by an external referee, moved the primary slope
from +4.890 to +4.871 and no conclusion. The district-cluster column resamples the 37
legislative districts rather than individual race-cycles, for the same reason as the
federal panel's clustered interval. The FEDERAL panel drops six races instead of entering
them at zero, and the reason is not the same question: those six have no *outcome* — they were
uncontested or lacked national-cycle data, so the fundamentals-net residual is undefined
rather than zero. An undefined residual cannot be entered at zero the way an absent
expenditure can. ⚠ Two of the six nonetheless carried real money (cd10 2020, +$0.76M; cd04
2024, +$0.99M), so the federal panel discards treated observations for want of a scorable
outcome, which is a loss of power rather than a bias in the retained cells.*

**The obvious design response was tried, and it fails in the direction that makes the point.**
A referee's sharpest suggestion here is to stop leaning on 129 cells and exploit the cleanest
subset instead: PDC identifies a candidate's *chamber* but not their House *position*, so a
district-level expenditure is ambiguous between Position 1 and Position 2, while a Senate
district carries one seat and is unambiguous. Sacrifice cell count for treatment validity.
Carried out (`scripts/diag_ie_inference_sensitivity.py`), the cleanly assigned panel is
**9** district-cycles — below the **10** at which this project already withholds inference —
and its treatment is close to absent rather than merely sparse: on the race-matched
specification the largest net advantage in any Senate cell is about **$62K** and **6** of the
9 sit within a thousand dollars of zero. The descriptive slopes that result run from
**−60.86** to **+5.43** across the four scope-and-specification combinations, changing sign
with the advocacy scope. That is not a cleaner estimate; it is a panel with no usable
treatment variation, and it states the finding below more sharply than the 129-cell headline
can.

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

*(An earlier version treated an extraction bug as a limitation of Washington's disclosure
regime. The block recording that correction stood here until 2026-08-28 and is preserved
whole in Appendix F; the conclusion it reports is unchanged.)*

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

### The design space, searched rather than named

The claim that the contribution is *an identification failure* obliges a search, not a list.
An earlier version of this paper named three canonical designs in its related-work section
and set each aside in a clause, which is naming. This section reports what happens when the
three designs that could in principle be built from this record are actually costed. Counts
first, because a design's feasibility is a countable property and the earlier version never
counted.

**A repeat-challenger design is not available: there are three usable pairs.** Levitt's
design differences out candidate quality using the same two candidates meeting more than
once. Counting D-versus-R match-ups that recur with *both* names unchanged
(`scripts/diag_repeat_matchups.py`): of **39** congressional D-versus-R district-cycles,
**3** are repeats — cd01 and cd06 across 2020–2022, cd07 across 2018–2020 — and each spans
exactly two cycles, so the design yields **3** differenced observations. The state
legislature is no better and it is worth saying why, because the intuition runs the other
way: legislative rematches feel common, and of **214** legislative D-versus-R district-cycles
only **8** are repeats — **7** in the House and **1** in the Senate. Pooling federal with
legislative to reach eleven would pool FEC and PDC measurement systems this paper has
already established are non-equivalent. Three differenced observations is not an
underpowered Levitt design; it is not a design.

**The 2022 redistricting is not an instrument here, and the reason is structural rather than
statistical.** A redraw does change a district's expected closeness for reasons unrelated to
any given candidate's fundraising capacity, which is the right shape for an instrument. But
there is exactly **one** redraw inside this panel, and **all 10** scorable districts are
observed on both sides of it. A shock common to every unit at a single date has no
cross-sectional variation in *timing*, so its effect cannot be separated from a 2022
cycle effect — any instrument built on it is collinear with the year. Distinguishing them
needs either a second redraw or another state redrawn on a different schedule, which is a
cross-state design and not this record. Two further obstacles are specific to Washington and
worth recording: precinct identifiers were renumbered in the redraw, so a cross-2022
precinct join returns zero common precincts, and this paper's own baseline already absorbs
the new geometry through its post-redistricting attenuation. The redraw is not unused here
because it was overlooked; it is unusable because it happened once.

**Filing timing is exploited, and the results are immediately below.** The retained
24/48-hour notice rows make a within-race timing split possible, and that split is run at
three cutoffs in the next subsection. It is reported there rather than here because it
produced a result rather than a feasibility verdict.

**What the search establishes.** Two of the three designs are unavailable for countable
reasons — three differenced observations, one redraw — and the third is run and does not
discriminate. That is the content of "identification failure": not that credible designs
exist elsewhere and were declined, but that the designs this record could support are either
too small to estimate or collinear with a year. A reader who wants the effect identified
needs a different record, and the specific properties that record would need are now stated
rather than gestured at.

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
next-cycle figure at **+0.031** — and its *total* independent expenditure, direction
discarded, at **+0.122**. The distinction is not decorative: a district could draw heavy
outside money in consecutive cycles while the partisan advantage flipped between them, which
would leave the first figure near zero and the second high, and a claim about *money* would
then rest on a measurement of *direction*. It does not happen here. Neither quantity
persists, so Washington's outside money does not persist in a seat in level or in direction.
It arrives where a given cycle's contest is expected to be close, and goes elsewhere when it
is not — which is the endogeneity mechanism visible directly, without a regression.

*Both correlations are computed on the same 14 same-era pairs and are correspondingly
imprecise; what they support is that neither shows persistence, not either figure to a second
digit. (The total-IE line was added 2026-08-28; the record is in Appendix F.)*

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

Money in Washington elections is **an exceptionally strong marker of electoral performance
not captured by the fundamentals baseline; whether it is *also* a mover of votes, this design
does not establish either way.** Candidate strength is one plausible latent mechanism behind
that marker, and it is not the only one — private polling, anticipated competitiveness, party
targeting, donor networks, elite endorsements and media attention would each produce the same
correlation, and this design separates none of them. Marker and mover are not
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
  limitation.** (An earlier version excluded it for want of a directional flag — an
  extraction bug, not a disclosure regime; Appendix F.) Read through C6.3, the
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
  earlier collision of names is recorded in this paper's own **Appendix F** and in the
  collision audit described below. *(This sentence cited `who-decides-washington.md` until
  2026-08-25. Nothing in the turnout paper matches — it carries no candidate-finance content
  at all — so the pointer resolved to a document that could not contain the record.)*
- **Fundraising feature — and its measurement window, which is not aligned to the
  outcome.** The receipts figure is a **full-cycle total**, not a pre-election one.
  `candidate_finance` carries **one summary row per candidate-cycle** (184 of 184 Washington
  House candidate-cycles across the four analysis cycles), and its `coverage_end_date` ranges from thirteen months *before*
  the election to two months *after* it, so for most candidates the window closes after the
  result it is being correlated with. Two consequences follow, and both are now measured
  below (an earlier version said "neither is quantified here" — true when written, stale
  the day the test ran).
  Post-election receipts are plausibly *caused by* the outcome — winners retire debt and
  bank for the next cycle, losers stop — so some part of the association in Finding 1 could
  in principle have been mechanical rather than informational; that concern is what the
  cutoff test below addresses. And the two sides of the ratio are not measured on
  the same day: of 39 district-cycles with both a Democratic and a Republican filer,
  **5** differ by more than 60 days and one by **224**, against a mean gap of **20.1** days.
  A pre-Election-Day cutoff is **not computable from the loaded table** — there is no earlier
  snapshot to fall back on — so testing whether the association survives one required
  re-pulling FEC data, which an external referee elevated to this paper's last open
  empirical task. **Done** 2026-08-29 (`scripts/diag_receipts_preelection.py`; pinned per
  candidate in `fec_receipts_preelection_2026-08-29.csv` and per committee — with each
  committee's designation *as of its cycle* — in
  `fec_receipts_preelection_committees_2026-08-29.csv`): each congressional frame
  candidate's receipts were rebuilt from the FEC's per-report period totals — the same
  all-receipts measure — summed in full and again cut at the last report whose coverage
  ends on or before election day (the pre-general filing, so the cut lands about three
  weeks out). **The association is essentially unchanged under the pre-election cutoff:
  within the 31 congressional cells, r = **+0.506** using receipts through the final
  pre-election report, against **+0.507** on the same report-built full-cycle basis, on
  the authorized-committee universe.** The headline association therefore does not depend
  on receipts reported after that cutoff. Stated with the design's own limits: the cutoff
  removes post-election receipts *and* roughly the final three weeks of pre-election
  money, and correlations do not decompose additively — so this is a robustness result
  about the reporting cutoff, not a measurement of the post-election component's separate
  contribution.

  **The committee universe, validated at the cycle rather than trusted from current
  codes.** The FEC's committees endpoint reports each committee's *current* designation,
  and two of this panel's principal campaign committees read as something else today — a
  retired incumbent's is re-coded 'U', and one challenger's 2020 campaign vehicle, later
  converted to a leadership PAC, reads 'D'. Checked against
  `/committee/{id}/history/{cycle}/`, **66 of the 69 committee-cycle rows were designation
  P or A as of their cycle**, those two included. The three that were not belong to one
  genuine at-cycle leadership PAC (a cd04 incumbent's — $19,500 / $64,250 / $69,500 across
  2018–2022), and it is **excluded**: the figures above are the **authorized universe**,
  at-cycle P or A only. The broader everything-but-J construction — which an earlier
  version of this bullet stated as the rule, and a referee correctly objected is too broad
  *as a rule* even where it lands on the right money — is retained only as the
  summary-basis comparability check: it gives **+0.507 / +0.508** — the second matching
  the pinned frame's own **+0.508** — and reconciles with the loaded `candidate_finance`
  totals at a mean absolute difference of **0.45%** per candidate-cycle (maximum
  **13.18%**), which shows the FEC's own summary rows sweep the same edge cases, not that
  the broader universe is conceptually right. The result is invariant to the choice.

  The state-legislative analogue — computable from the loaded, dated PDC
  itemized rows, an itemized-only measure and so internally consistent rather than
  level-comparable — resolves finance rows by exact amount for **77** of **97** legislative
  cells (**76** usable after one zero-side drop) and moves **+0.376 → +0.370**. These
  values are **not comparable to Finding 1's within-legislative +0.553**: the fall is the
  itemized-only measure and the exactly-resolvable subset, not the cutoff — the cutoff
  itself moves the itemized correlation by **0.006**. One further FEC quirk is recorded in
  the pin: one person can hold two FEC candidate ids, merged at the committee level.
  **Why 35 of the 163 carry no ratio.** `log2(D/R)` is undefined unless both sides have a
  receipts row, and the reason is almost always that one side has none: of the 35, **25**
  carry a row for the Democrat only, **6** for the Republican only, and **4** for neither.
  **32 of the 35 are legislative.** This is a property of who filed rather than of the
  linkage described next — an office-and-district-scoped key either resolves a name or does
  not, and a candidate with no filing has nothing to resolve. The consequence for Finding 1
  is stated there: the excluded cells average more Democratic overperformance than the
  retained ones, so the correlation describes races with two funded candidates.
  Raw `log2(D receipts / R receipts)` is matched against
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
  split is a two-regressor OLS), and every correlation is Pearson's r. The reported point
  estimates are OLS throughout. Unless expressly labelled otherwise, a "95% bootstrap
  interval" is a **case-resampling (pairs) percentile bootstrap with 5,000 replicates and a
  fixed seed**, so the intervals are deterministic and reproduce exactly; where a
  **district-clustered** resampling interval is reported, it is labelled as such at the
  point of use. Finding 2c additionally reports HC3, analytic cluster-robust and
  wild-cluster-bootstrap inference as sensitivity checks. No weighted estimator is used;
  at these sample sizes the
  honest summary is the interval, not the standard-error recipe. *(Until 2026-08-29 this
  bullet said no heteroskedasticity-robust variant is used anywhere — a sentence that
  survived from before the 2026-08-28 inference-sensitivity work and contradicted
  Finding 2c directly. A referee caught the two arguing; same defect family as the
  restated figure that drifts, but for a methods sentence.)*
- **Inference threshold.** The IE script refuses to report a slope as inferential below 10
  scorable races and prints its data inventory instead. That threshold is now cleared; the
  behavior is deliberate and should be preserved.
- **Reproduction.** `scripts/diag_overperformance_patterns.py` (Finding 1),
  `scripts/diag_expenditures_vs_residual.py` (2a), `scripts/diag_ie_vs_margin.py` (2c and
  Finding 3), `scripts/diag_loser_side_money.py` (the §J longshot-share figure).

## Appendix D — Related work

This paper contributes a negative identification result and a data-availability audit, not
a new identification strategy or a finding that money has no effect. It sits in a literature that has been circling the same
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
- **The experimental literature, and its stated scope conditions.** Kalla & Broockman,
  "The Minimal Persuasive Effects of Campaign Contact in General Elections: Evidence from 49
  Field Experiments," *American Political Science Review* 112(1) (2018): 148–166,
  doi:10.1017/S0003055417000363 — average general-election persuasive effects near zero
  across the experiments they synthesize. **The scope conditions are theirs, not a caveat
  added here, and they cut against a naive reading of this paper:** Kalla & Broockman are
  explicit that effects *are* detectable in primaries, in ballot-measure campaigns, and
  where candidates are unfamiliar to voters. This paper's largest cell count sits in state
  legislative races — the low-information end of the ballot, and precisely where their null
  applies least. So their result is a prior for the congressional panel and a weaker one for
  the legislative panel, which is the opposite of the direction cell count would suggest.
- **Credible designs that find the effect is NOT zero.** Spenkuch & Toniatti, "Political
  Advertising and Election Results," *Quarterly Journal of Economics* 133(4) (2018):
  1981–2036, doi:10.1093/qje/qjy010 — exploiting the mismatch between media markets and
  state boundaries as plausibly exogenous variation in political-advertising exposure, and
  finding an economically meaningful positive effect on candidates' vote shares, on the
  order of half a percentage point for a one-standard-deviation partisan advertising
  advantage. **This citation is here because it cuts against this paper's own framing and
  should.** An earlier version of this appendix positioned the Washington nulls beside a
  zero-effect prior alone, which made the literature look more settled than it is.
- **Spending effects are heterogeneous by candidate type, which is why pooled estimates
  disagree.** Green & Krasno, "Salvation for the Spendthrift Incumbent: Re-estimating the
  Effects of Campaign Spending in House Elections," *American Journal of Political Science*
  32(4) (1988): 884–907, and Erikson & Palfrey, "Campaign Spending and Incumbency: An
  Alternative Simultaneous Equations Approach," *Journal of Politics* 60(2) (1998): 355–373
  — challenger and incumbent spending are not interchangeable, and the estimated effect
  depends on which is being measured and on how simultaneity is handled. The Washington
  panels here pool incumbents and challengers, which is one more reason a single slope is
  the wrong object.
- **What the literature actually says, taken together.** Credible designs find effects
  ranging from approximately zero to economically meaningful, and which one you get depends
  on the treatment (contact, advertising, independent expenditure), the channel, the office,
  the information environment, and the identification strategy. **That heterogeneity is the
  reason this paper's contribution is an identification failure rather than a null.** A
  Washington observational record cannot adjudicate between a zero-effect and a
  half-a-point-per-SD world, because the variable that would separate them is chosen by
  committees who observe expected closeness. Positioning these results beside only the
  zero-effect findings would have been the more comfortable framing and the less honest one.
- **What contribution behaviour reveals.** Bonica, "Mapping the Ideological Marketplace,"
  *American Journal of Political Science* 58(2) (2014): 367–386, doi:10.1111/ajps.12062 —
  recovers ideological positions for candidates and donors from the structure of
  contribution relationships, treating giving as a revealed preference about *ideology*.
  ⚠ **Cited for that, and no longer for more.** An earlier version of this appendix filed it
  under "money as information rather than purchase" and called it the reading most
  consistent with these results. It is not primarily evidence for that proposition: it is a
  measurement strategy for ideal points. The information-versus-purchase question is
  addressed by the access literature below, not by Bonica.
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
cycle is omitted: it carries **69** flagged rows as of **2026-08-24** and no scorable race —
the same pinned reading as Finding 3's inventory table.

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

Thirty-four scorable races. Party attribution is effectively complete — **$1,560** of the
**$75.62M** completed-cycle total is unresolvable to a side, across **3** district-cycles, so
the slope is not a coding artifact. That numerator is on the completed-cycle basis for the same
reason the total is: a new filing in an open cycle routinely lands before the candidate record
that resolves it to a party, so an all-cycle figure here measures filing lag rather than
attribution quality. Note how
much of the variation sits in races with **no** independent expenditure at all: cd07's
+13.70 residual in 2024 and +9.19 in 2022 both occur at $0 IE, which is a compact
illustration of why even thirty-four observations cannot separate money's effect from
everything else that varies across districts and cycles.

Note also the two largest totals in the panel, cd08 in 2018 ($16.28M) and 2022 ($17.47M),
which bracket WA-03's 2024 $18.61M. All three landed within nine points of their
fundamentals and two of the three within one point — and the one that did not is **cd08
2018**, the Cook's-distance-**0.69** observation that carries the entire headline slope.
Naming it here rather than leaving a reader to notice: the sentence would otherwise read as
three heavily-financed races all landing near their fundamentals, when one of the three is
the single point the positive slope depends on.

## Appendix F — What has moved, and what caught it

**Why this appendix exists, and why the detail is here rather than in the findings.** This
paper's thesis is that the independent-expenditure estimate is unstable and that Washington's
observational record cannot settle the question. A documented history of the estimate moving —
a sign flipping on a seventh of the data, every dollar figure halving, a claimed disclosure
limitation turning out to be an extraction bug — is that thesis made concrete rather than
asserted, and it is the strongest evidence in the document for its own central claim. Two
referees agreed it should be kept and disagreed about where. It is kept, and it is here: the
findings should read as findings, and the instability should read as the argument, which
fifteen correction blocks scattered through the argument prevented. *(Completed 2026-08-28,
on the author's choice of destination: the detail blocks remaining in Findings 2–3 and the
limitations section were reduced to pointers; current values stay where the argument needs
them; the one block whose full text is not recorded elsewhere is preserved below as it
stood.)*

**Each entry gives the direction, the date where one is recorded, and what caught it.** The
last column is the one worth reading: where the answer is "a human reading the sentence", that
is a gate this project does not have.

### The pinned frames, and the figures that moved with them

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
> is what `scripts/verify_money_votes.py` asserts the correlations against. *(The
> 2026-08-28 consolidation severed a sentence here — its other half sat orphaned at the
> top of Finding 2a's pin note until 2026-08-29, when a referee spotted the two ends. The
> whole sentence now lives in Finding 2a, where its figures are.)*

### The corrections recorded elsewhere in this paper, in one list

| what changed | direction | what caught it |
|---|---|---|
| FEC filed most independent expenditures **twice** — a 24/48-hour notice and again on a periodic Schedule E | every FEC IE total was ~2x its true value | an external bulk-file crosscheck needing no API key (`diag_fec_ie_bulk_crosscheck.py`); **no internal consistency check could see it**, because every figure derived from the contaminated table agreed with every other |
| the directional estimate ran on 2024 alone | sign reversed, −0.39 (n=7) to the four-cycle slope | loading the three missing cycles, which the earlier draft had itself prescribed |
| WA-03 2024 called "the most IE-saturated House race in the country" | withdrawn; it ranks 22nd of 387 | the de-duplication fix above, which halved the figure the superlative rested on |
| PDC legislative IE said to "carry no support/oppose flag" | withdrawn; direction is in form C-6 section **C6.3**, on 100% of rows | reading the source dataset rather than the loader's docstring — the limitation was an extraction bug described as a disclosure regime |
| "holdout R²" | relabelled; it is not a squared correlation of holdout outcomes | a human reading the label against the computation |
| the race-matched legislative rows dropped zero-treatment cells (n=127) | restored to the full 129; primary slope +4.890 → +4.871 | an external referee, who asked why zero treatment was being handled as missing data |
| Finding 2b counted a lagged-outcome term as an independent signal | withdrawn as double-counting | a human reading the model's conditioning set |
| the abstract said the directional test spans "five cycles" | corrected to **four completed** cycles; the inventory spans five | an external referee. ⚠ **A claim guard was actively holding the wrong number**: it compared the abstract to the INVENTORY count in a sentence about the estimator |
| Appendix E restated the open cycle's row | said 50 rows the day after the row was pinned at 69 | an external referee. A second copy of a figure in a section whose blanket exemption hid three figures in total |
| Finding 2c said residualising made the regression "a test of money's marginal effect" | narrowed to an association *conditional on* the modelled fundamentals | an external referee |
| Finding 1 said money is "clearly a marker of candidate strength" | narrowed to a marker of *performance not captured by the baseline*; strength is one latent mechanism among several | an external referee |
| the submission title read "A Negative Result That Survives Quadrupling the Sample" | withdrawn; it asserted a negative causal result this paper refuses to claim, and "quadrupling" contradicted the paper's own statement that the state extension is not a pure sample-size experiment | an external referee |
| the reproducibility statement said "all empirical results are independently reproducible" | narrowed; the residual-generation step needs the unpublished forecast model | an external referee, against the manuscript's own limitation |
| Appendix D positioned these nulls beside a zero-effect prior alone | contrary evidence added (Spenkuch & Toniatti 2018); Kalla & Broockman's own scope conditions stated; Bonica re-described | an external referee |
| the placebo section's "outside money does not persist in a seat" rested on NET IE alone | total-IE persistence measured beside it (+0.122 against +0.031; neither persists) — the sentence now measures money rather than direction | an external referee |
| fifteen correction blocks stood inside the argument | detail consolidated here 2026-08-28; pointers left in place | two external referees, agreeing on consolidation, disagreeing on destination — the author chose the appendix |
| the Finding 1 narrowing (row above) never reached the abstract or the submission metadata, and the opening restated two claims the companion papers had withdrawn — dating general elections' outcomes and equating ballot return with deciding races | abstract and metadata now carry the narrowed marker reading; the opening states what each companion currently establishes, with a dated note | an external referee, 2026-08-29 — a correction applied at its finding is not a correction applied to the paper |

### The one block preserved as it stood

Finding 3's chamber-ambiguity passage carried this parenthetical until 2026-08-28. It is
the only relocated block whose full mechanism is not restated elsewhere in this appendix,
so it moves here whole rather than being reduced to its table row:

*(An earlier version of this paper reported that this money "carries no support/oppose flag"
on all but 5 of 4,456 rows and "cannot enter a directional test at all", and treated that as
a limitation of Washington's disclosure regime. It was a limitation of our own extraction.
The PDC publishes direction in the **C6.3 "Identified Entities"** section of form C-6, in the
same dataset the loader was already reading and had been reading all along; the loader
consumed only the C6.2 itemized-expenditure section. The correction is documented in
[`pdc-c6-direction-audit.md`](pdc-c6-direction-audit.md), and the ingest is
`load_pdc_ie_targets`. The conclusion this paper draws is unchanged — the point estimate is
still unsignable — but the reason is different in kind, and the earlier reason was wrong.)*

**The pattern in the last column is the finding about method.** Of these, the two that no
human read would plausibly have caught — the doubled IE totals and the C6.3 extraction bug —
were both caught by going *outside* the pipeline to an independent source. Everything else was
caught by a person reading a sentence against what the analysis actually did. That is the
argument for the end-to-end read, and against the belief that a sufficiently dense gate
replaces one.

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
