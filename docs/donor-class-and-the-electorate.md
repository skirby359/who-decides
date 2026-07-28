# The Donor Class Is Not the Electorate

### Who funds elections in Washington, New York, and Idaho — substantially older and more concentrated than the electorate, with registered Democrats over-represented relative to registration in New York and Idaho — measured from individual voter-to-donor matches

**Stephen Kirby** · Tikor Consulting · July 2026

*AI-assisted drafting and analysis review. Contact: kirby@tikorconsulting.com.*

*Reproducibility, stated precisely. The aggregate results in this paper can be
independently re-derived from the built panel tables by `scripts/verify_donor_class.py`,
which reaches the databases with from-scratch SQL and imports no analysis code.
**Rebuilding those panel tables from the raw voter files is also covered**, as of
2026-07-27: the record-linkage step ships as `scripts/donor_matcher.py`, a standalone
extract of the matcher (function body verbatim from
`src/wa_analyzer/analysis/donor_analysis.py`, with the `contributor_type` helpers and a
minimal DDL folded in) that depends on nothing but `duckdb` and the standard library.
Rebuilding the Idaho federal panel through the public wrapper reproduces the published
panel exactly — 0 differing rows in either direction across all 9 columns of all 23,303
rows. Paper source, code, and the data-acquisition recipe are at
<https://github.com/skirby359/who-decides>; the underlying voter files are not
redistributable and are not included. Before submission this paper must cite a **tagged
release and archival DOI** (Zenodo or OSF) rather than a mutable branch — see
[`publication-checklist.md`](publication-checklist.md).*

*Paper #3 of the electoral-health series (companion to
[`who-decides-washington.md`](who-decides-washington.md),
[`who-decides-new-york.md`](who-decides-new-york.md),
[`who-decides-idaho.md`](who-decides-idaho.md),
[`safe-seat-washington.md`](safe-seat-washington.md), and
[`cross-state-fec-money.md`](cross-state-fec-money.md)). **DRAFT — revised 2026-07-27 in
response to external review, and again 2026-07-27 to fold in a stratified blinded
match-precision re-rating (Appendix F), since **independently re-rated by a human** who
agreed on 75 of 75 full-name-key records. That re-rating found precision is entirely a
function of match tier — no detectable false match on the full-first-name key, 48–72% on
the initial-based keys — and **the full-name key is now the paper's primary
specification**: every panel below was rebuilt on it. The superseded all-tier figures moved every headline *toward* the
null, so they were the conservative ones. One caveat is carried in the open: the restriction
discards 11–19% of matched donors and that discarded set is younger and less Democratic
than the retained set, so part of the sharpened skew is selection rather than precision
(Appendix F).***

*Provenance. Each panel is built by a per-state match script run once per money source
(`--source fec` / `--source state`), writing to `voter_donor_affiliation_fec` and
`voter_donor_affiliation_state`. Washington figures:
`scripts/match_wa_voters_to_donors.py` and `scripts/diag_wa_individual_findings.py` —
WA's registered roll (5.51M) + 27.1M vote records + birth years
(`data/wa_vrdb.duckdb`), matched to 147,745 federal and 217,114 state donors. New York
figures: `scripts/match_ny_voters_to_donors.py`,
`scripts/backfill_ny_committee_party.py`, `scripts/backfill_ny_recipient_party.py`,
`scripts/diag_ny_match_bias.py`, `scripts/diag_ny_primary_participation.py`,
`scripts/diag_ny_donor_extras.py`, `scripts/diag_ny_electorate_extras.py` — NY's
NYSVOTER roll (13.54M; individual party enrollment + DOB; `data/ny_vrdb.duckdb`) matched
to 10.0M FEC itemized contributions and, via `scripts/load_ny_contributions.py`, to 3.95M
NYSBOE **state** contributions (`data/ny_statewide.duckdb`; 269,218 federal / 378,383
state matched voters). Idaho figures: `scripts/match_id_voters_to_donors.py`,
`scripts/backfill_id_recipient_party.py`, `scripts/diag_id_electorate_extras.py` — ID's
statewide roll (1.03M; individual party affiliation + age; `data/id_vrdb.duckdb`) matched
to both Idaho Sunshine **state** filings (23,613 voters) and **federal** FEC
contributions (23,303 voters), in `data/id_statewide.duckdb`. Cross-state dollar
concentration: `scripts/cross_state_fec_money.py`. Contribution-limit tests (Appendix G):
`scripts/diag_contribution_limits.py`. The review-response recomputations — denominator
standardisation, match-tier and household sensitivities, panel overlap, period-aligned
panels, Idaho composition shares: `scripts/diag_donor_class_revisions.py`. Every figure
below traces to one of these scripts.*

*Two panels, read this first. American donors give into two separately regulated money
systems, and a voter roll can be matched to either. Every result below is therefore
computed **twice**, once per system, and never pooled:*

| panel | what it is | matched donors | itemization threshold |
|---|---|--:|---|
| **Federal** *(primary)* | FEC itemized individual contributions | WA 147,745 · NY 269,218 · ID 23,303 | aggregate **> $200** |
| **State** *(secondary)* | WA Public Disclosure Commission · NY State Board of Elections · Idaho Sunshine | WA 217,114 · NY 378,383 · ID 23,613 | WA **> $100** · NY **> $99** · ID **> $50** |

*Pooling the two systems — which earlier drafts did for Washington without intending to —
inflates measured concentration, because one person's federal and state giving stacks
into a single donor total while a one-system donor's does not; on Washington's data,
pooling read 46.6% top-1% against 42.4% federal and 43.8% state on the superseded
all-tier build. The panels are kept separate for that reason.*

*What the panel split does and does not establish.* Where an outcome is observable, it is
estimated separately in the federal and state panels, and the principal directional
patterns — older than the electorate, dollars concentrated at the top, metro-concentrated,
stacked with high turnout, and (where party is observable) tilted toward registered
Democrats and against the unaffiliated — replicate across every state-and-panel
combination in which they can be measured. Party is **not** observable in Washington, and
Idaho's turnout figures are reported as composition rather than rates, so no claim here is
that *every* finding is measured in every cell.

*The differences between the panels are informative but are **descriptive differences
between two datasets**, not identified effects of federal versus state regulation. Three
confounds run alongside the regulatory one, and Appendix C quantifies each: the panels
have **different disclosure thresholds** (a $50 Idaho floor reaches far deeper into
small-dollar giving than a $200 federal floor), they can cover **different years** (Idaho
Sunshine holds 2023–2025 against a 2017–2026 federal layer), and they are largely
**different people** — the federal and state matched sets overlap by a Jaccard coefficient
of only 0.14–0.16 in all three states. With that stated, the most robust panel difference
is that federal money is older money: New York's federal donors are 49.9% over 65 against
39.3% of its state donors, Idaho's 66.8% against 51.3%, and Washington's Silent Generation
multiplier runs 2.67× federal against 1.72× state. In Idaho, the one state where the
windows differ, restricting both panels to the shared 2023–2025 window **widens** the gap
to 67.1% against 51.1%, so period misalignment is not what produces it.*

## Abstract

Campaign money is usually described by how much is raised. This paper asks whose money it
is, and whether the people who fund elections resemble the people who vote in them. Three
state voter-registration files — Washington (5.51M registrants), New York (13.54M, with
individual party enrollment and date of birth), and Idaho (1.03M, with party affiliation
and age) — are linked person by person to itemized campaign contributions under a
conservative uniqueness rule. Because American donors give into two separately regulated
money systems, every result is computed twice and never pooled: a federal panel (147,745
matched donors in Washington, 269,218 in New York, 23,303 in Idaho) and a state panel
(217,114, 378,383, and 23,613). Where an outcome is observable it is estimated in both,
and the principal directional patterns replicate across the available combinations. The
matched donor class is substantially older than the electorate that elects the officials
it funds: 49.9% of New York's federal donors and 66.8% of Idaho's are 65 or older, against
a quarter and a third of their rolls, and Washington's Silent Generation gives at 2.6 times
its share of the roll while Generation Z gives at one-tenth of its own. Dollars are highly
concentrated, with the top 1% of matched donors supplying 41.2% of federal dollars in
Washington, 50.7% in New York, and 37.2% in Idaho, and a single metropolitan area
supplying a fifth to a half of each state's total. Where party of record is observable, the
donor class over-represents registered Democrats and under-represents the unaffiliated by
double digits — in deep-blue New York (+16.1 points Democratic federally, +9.6 in state
money) and in deep-red Idaho (+8.6) alike, so the result is not mechanically attributable
to which party holds the statewide registration plurality. The same individuals also vote
at far higher rates than non-donors, stacking financial and electoral voice rather than
offsetting them. Blinded validation of 480 matched records found precision to be a property
of the match key: **no detectable false match** on the full-first-name key the paper now
uses as its primary specification (120/120; Wilson 95% CI 96.9–100), against 47.9–71.7% on
the three initial-based keys it excludes, which carried 11–19% of matches and every
household false merge. An independent human rater re-rated 150 of those records blind and
**agreed on all 75 drawn from the full-name key** (Cohen's kappa 0.815 on the collapsed
binary overall); every one of the 18 disagreements was on an initial-based key and in the
direction of the human being more permissive, so the reported weak-tier rates are the
conservative ones. The superseded all-tier specification's population-weighted
precision was 93.0%. Adopting the clean key moved every headline away from the null, so the
previously published figures were the conservative ones; it also discards a younger and
less Democratic set of donors, so part of the sharpened skew is selection rather than
precision, and both specifications are reported. The age skew survives inverse-propensity
re-weighting for match bias. Simple mechanical truncation of gifts at
state cap levels does not reproduce the observed ordering of the concentration estimates.
The paper measures itemized giving and registration records, not policy influence, and its
causal claims are limited to association.

**Keywords:** campaign finance; political donors; voter files; record linkage; party of
record; contribution limits; donor concentration; Washington; New York; Idaho.

---

## The question

Campaign money is usually described by *how much* is raised. The more
consequential question for representation is *whose* money it is — and whether
the people who fund elections look anything like the people who vote in them. If
the donor class is a representative cross-section of the electorate, money is
just amplified participation. If it is a narrow, self-selected slice, then a
distinct population is setting the financial terms of every race before the
first ballot is cast.

This question can be answered at the individual level in three states, by matching the
registered-voter roll to itemized donors, person by person (a conservative name + ZIP
match in four tiers; see Appendix C). Washington supplies the demographic and behavioral
cut; **New York and Idaho — which, unlike Washington, publish each voter's party — supply
the dimension WA cannot: who the donor class is *partisan*-ly, and where its money goes.**
And they bracket the political spectrum: New York is ~48% registered Democratic, Idaho
~63% registered Republican.

The short answer, consistent across all three states: **the donor class is not the
electorate.** It is substantially older, financially and geographically concentrated in a
small top tier, and — where party is observable — tilted toward registered Democrats while
substantially under-representing the largest non-partisan bloc. The notable part is that
the Democratic tilt of the donor class relative to registration appears in deep-blue New
York **and in deep-red Idaho**: it is not mechanically attributable to which party holds
the statewide registration plurality.

---

## Finding 1 — The donor class is substantially older than the electorate

In all three states matched donors are far older than the voters they fund.

**New York** (`match_ny_voters_to_donors.py`) — age-band share, age as of
2024-11-05:

| age band | federal donors | state donors | all active voters | 2024 GE voters |
|---|--:|--:|--:|--:|
| 18–29 | **1.6%** | 3.9% | 18.0% | 14.1% |
| 30–44 | 13.0% | 17.2% | 25.6% | 23.1% |
| 45–64 | 35.5% | 39.6% | 31.2% | 34.6% |
| 65+ | **49.9%** | 39.3% | 25.2% | 28.2% |

*Source: `data/ny_statewide.duckdb` (`voter_donor_affiliation_fec` / `_state`) joined to
`data/ny_vrdb.duckdb`; NYSVOTER FOIL production **dated 2026-06-29**; FEC bulk individual
files and NYSBOE `4j2b-6a2j`, both 2017–2026; reference population = active registrants
(`status_code='A'`). Script: `match_ny_voters_to_donors.py`; re-derived by
`verify_donor_class.py`.*

Nearly **half of NY's federal donors are 65 or older**, versus a quarter of the active
roll; its state donors are younger but still tilted, at 38.4%. **Washington** shows the
same shape as generation multipliers (donor share ÷ roll share), and the skew is sharper
in federal money than in state:

| generation | federal panel | state panel |
|---|--:|--:|
| Silent | **2.67×** | 1.72× |
| Boomer | 2.04× | 1.59× |
| Gen X | 0.98× | 1.31× |
| Millennial | 0.35× | 0.61× |
| Gen Z | **0.04×** | 0.11× |

*Source: `data/wa_statewide.duckdb` + `data/wa_vrdb.duckdb`; WA SoS standard VRDB
extract, **April 2026** (requested 2026-04-08); roll share from `voter_scores` `ld`-scope
(one row per voter); FEC 2017–2026 and PDC 2016–2026. Scripts:
`match_wa_voters_to_donors.py`, `diag_wa_individual_findings.py`; both panels re-derived
by `verify_donor_class.py`.*

**Idaho** replicates it in a third state, in both money systems (age here is
current-roll age, not election-time DOB, so bands are read against the current roll):

| age band | federal donors | state donors | all voters | 2024 GE voters |
|---|--:|--:|--:|--:|
| 18–29 | **0.5%** | 2.1% | 15.2% | 13.1% |
| 30–44 | 6.2% | 12.9% | 22.8% | 22.4% |
| 45–64 | 26.5% | 33.7% | 30.9% | 31.9% |
| 65+ | **66.8%** | 51.3% | 31.0% | 32.6% |

*Source: `data/id_statewide.duckdb` + `data/id_vrdb.duckdb`; ID SoS statewide voter list
(Idaho Code § 34-437A(3)), **received 2026-07-01**; FEC 2017–2026 and Idaho Sunshine
2023–2025. Idaho's export
carries no active/inactive flag, so the roll and active-roll baselines coincide by
construction rather than as a fact about the roll. Script:
`match_id_voters_to_donors.py`; re-derived by `verify_donor_class.py`.*

**Nearly two-thirds of Idaho's federal donors are 65+**, and more than half of its state
donors — against a third of the roll, with the under-30 share reduced to 1.4% and 2.6%
respectively. The donor class is substantially older than the registration baseline in
blue and red states alike.

**The panel gap, and what it is not.** In all three states, federal money is older money:
New York's 65+ donor share falls from 49.9% federal to 39.3% state, Idaho's from 66.8% to
51.3%, and Washington's state giving reaches Gen X and Millennials at roughly twice the
rate federal giving does (Gen X 1.26× vs 0.98×, Millennial 0.68× vs 0.39×). Three
alternative explanations were tested, and the gap survives the one that could be tested
directly while remaining exposed to the other two:

- **Period misalignment — ruled out.** Idaho is the only state whose two money systems
  cover different years (Sunshine 2023–2025 against a 2017–2026 federal layer). Rebuilding
  both panels on the shared 2023–2025 window (`diag_donor_class_revisions.py
  --build-aligned`) *widens* the gap: aligned federal 65+ is **68.5%** on 14,848 donors,
  against the state panel's 51.3%. WA and NY carry both systems over the same years
  already.
- **Disclosure thresholds — not ruled out.** The state panels itemize from a much lower
  floor ($50 in Idaho, $99 in New York, $100 in Washington) than the federal $200, so they
  reach deeper into small-dollar giving, which is younger. Part of the panel gap is very
  likely this, and nothing here separates it from a behavioral difference.
- **Different people — not ruled out.** The two panels are not the same donors observed
  under two rule sets. They overlap by a Jaccard coefficient of 0.159 in WA, 0.161 in NY,
  and 0.141 in ID; only 23–34% of either panel appears in the other. A within-person read
  makes the point sharply: the 65+ share runs 31.3% among WA state-only donors, 51.3%
  among federal-only, and **57.5% among those in both** — the both-systems group sits
  *outside* the range spanned by the single-system groups, which a pure property of the
  regulatory layer would not produce. NY (33.7 / 45.2 / 53.4) and ID (45.9 / 63.9 / 67.2)
  behave the same way. Giving in more than one system is itself an age-graded behavior.

**The skew is not explained by age variation in matchability.** The obvious objection is
that the match key (surname + first name + ZIP5, required to be *unique* on the roll)
selects older, rarer-named, stable-address voters. Tested directly in the two states where
the re-weighting was run (WA and NY), it does not: the probability a voter is uniquely
matchable is **nearly flat across age** — NY **94.5–95.4%** across the four bands (0.9-pt
spread, `diag_ny_match_bias.py`); WA **96.3–97.6%** across generations (1.4-pt spread).
Inverse-propensity re-weighting therefore **does not move the distribution**: NY's 65+
donor share goes 47.9% → **47.9%** (0.0-pt shift), and every Washington generation
multiplier is **unchanged to two decimal places in both panels**. (Those figures were
computed on the superseded all-tier panels; the test is a property of the roll and the
match key, not of which contributions are used, so it carries over.) What this rules out is
specifically age variation in unique-key availability; it does not test false-match
probability, donor-side name completeness, residential mobility, or survivorship on the
current roll, which are treated separately in Appendix F. (Idaho uses the identical
matcher but was not separately re-weighted.)

**And it is not a product of the weaker match tiers — which is why they are gone.** The
figures above are the full-first-name key alone. Adding the three initial-based keys back,
as the superseded all-tier specification did, *lowers* the senior share in all three states
(WA federal 55.7% → 53.4%, NY federal 49.9% → 47.9%, ID federal 66.8% → 64.7%), so the
previously published figures understated the skew. Appendix F carries the full
tier-by-tier comparison, and the countervailing point: the discarded donors are younger,
so some of that difference is selection rather than measurement error.

---

## Finding 2 — Dollars are highly concentrated at the top

Money concentrates at the very top of the matched-donor distribution, in every state
and in both money systems:

| panel | matched donors | matched $ | top 1% → share of $ | top 10% | Gini |
|---|--:|--:|--:|--:|--:|
| **Federal** | | | | | |
| Washington | 147,745 | $346.3M | **41.2%** | 74.2% | 0.815 |
| New York | 269,218 | $1,015.7M | **50.7%** | 81.2% | 0.865 |
| Idaho | 23,303 | $42.1M | **37.2%** | 70.8% | 0.789 |
| **State** | | | | | |
| Washington (PDC) | 217,114 | $122.5M | **43.5%** | 75.3% | 0.821 |
| New York (NYSBOE) | 378,383 | $339.8M | **48.6%** | 78.2% | 0.845 |
| Idaho (Sunshine) | 23,613 | $13.6M | **40.0%** | 71.0% | 0.799 |

*Source: the six panel tables named in the header. Estimator: donors ranked by total
matched dollars, split into 100 equal-count buckets (`NTILE(100)`) over donors with
`total_donated > 0`; "top 1% / 10%" is the top 1 / 10 buckets' dollars ÷ all matched
dollars. Windows: WA FEC 2017–2026 / PDC 2016–2026; NY FEC and NYSBOE both 2017–2026; ID
FEC 2017–2026 / Sunshine 2023–2025. These are **itemized** dollars only, from panels with
different disclosure floors (header table). Appendix C gives the full estimator
definition; Appendix E the bootstrap intervals. Scripts: the per-state match scripts;
re-derived by `verify_donor_class.py`.*

Two readings. First, the ordering **New York > Washington > Idaho** holds in *both*
panels, and matches the statewide all-donor figures — so it is a property of these states'
donor economies, not of who the matcher can find or which money system is examined.

Second, the state-versus-federal comparison does **not** run one way. State money is
slightly *more* concentrated in Washington (43.5% vs 41.2%) and Idaho (40.0% vs 37.2%),
but *less* so in New York (48.6% vs 50.7%) — even though state contributions are capped
far lower than federal ones in all three. In Idaho, period-aligning the two panels leaves
the direction intact (aligned federal 34.7% against state 40.0%). Whatever caps do, they
do not produce a consistent ordering between the two layers. Appendix G takes that up.

A geographic corollary everywhere — and the sharpest panel difference in the paper.
In WA, **63.4%** of federal matched-donor dollars come from two Seattle-metro ZIP3s
(981xx 37.3% + 980xx 26.1%); the state panel is broader at 55.1% (32.3% + 22.8%).

New York is the extreme case. **Manhattan (New York County) supplies 50.3%** of the
state's *federal* matched-donor dollars — top three ZIP3s **63.4%** — but only **20.6%**
of its *state* dollars, where the top three ZIP3s take just **38.1%**. Manhattan remains
the single largest county in the state panel too; what changes is that suburban **Nassau
(15.1%)** and **Suffolk (11.1%)** together exceed it, which they do not come close to
doing federally. Any account of "the New York donor class" resting on the federal file
alone is describing one island.

Idaho shows single-metro dominance from a state with no large city: **Ada County (Boise)
supplies 49.2%** of state matched-donor dollars from 10,037 donors, and 36.4% of federal
dollars from 10,338. Idaho's federal money is the one case where a second center appears:
resort-county **Blaine (Sun Valley) supplies 11.7%** of federal dollars from 1,097
donors — 4.0% of Idaho's federal donors carrying nearly three times their weight.

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
a money system whose *itemized* dollars are dominated by a thin top stratum and a single
metro.

---

## Finding 3 — Registered Democrats are over-represented relative to registration (New York *and* Idaho)

This is the cut Washington cannot supply. Using each donor's **own** NY party
enrollment (100% present), the donor class over-represents registered Democrats
and substantially under-represents the unaffiliated — in both money systems:

| party | registration | federal donor share | **skew** | federal $ share | state donor share | **skew** | state $ share |
|---|--:|--:|--:|--:|--:|--:|--:|
| DEM | 47.6% | 63.6% | **+16.1** | 72.5% | 57.1% | **+9.6** | 54.9% |
| REP | 22.6% | 21.5% | −1.1 | 16.0% | 25.8% | +3.2 | 27.7% |
| NOPARTY (blank) | 25.3% | 11.6% | **−13.7** | 9.8% | 12.7% | **−12.6** | 13.9% |
| OTHER (minor) | 4.5% | 3.2% | −1.2 | 1.8% | 4.4% | −0.1 | 3.6% |

*Source: `data/ny_vrdb.duckdb` `voters.party`, measured at the NYSVOTER extract date,
against the two NY panel tables. **Baseline = active registrants** (`status_code='A'`;
12,448,081 of 13,540,558 records), which is the universe the matcher itself draws from.
On an all-records baseline every skew moves by at most 0.4 points (`DEM +15.0`,
`REP −0.9`, `NOPARTY −13.0`) — earlier drafts reported those figures. Scripts:
`match_ny_voters_to_donors.py`, `diag_donor_class_revisions.py`; re-derived by
`verify_donor_class.py`.*

Registered Democrats are +15 points over their share of the active roll in federal money
and supply **71% of federal matched dollars**; Republicans give roughly in proportion. The
constant across both panels is the under-representation of the unaffiliated: NY's "blank"
enrollees are a quarter of all registrants and only an eighth of federal donors, barely
better at a seventh of state donors.

The Democratic tilt itself is substantially a *federal* phenomenon. It falls by a third in
state money (+16.1 → +9.6), where Republicans move from slightly under-represented to
slightly over (−1.2 → +2.8). New York's donor class leans Democratic most sharply where
the money is nationalized; its state-level donor pool is closer to — though still not —
the electorate. The unaffiliated bloc is under-represented either way.

Two caveats attach to every cell above. Party of record is measured at the **voter-file
extract date**, while contributions span the prior decade, so a donor's recorded party is
not necessarily their party when they gave. And these are **registration** shares, not
shares of the eligible or voting population.

### Where the money goes — an exploratory donor classification

The table below is frequently misread, so its content is stated exactly. It classifies
**donors**, not dollars. A donor is `D-only` if every recipient of theirs whose party
could be resolved was a Democrat, `R-only` if every one was a Republican, and `Mixed` if
they gave to both. Donors none of whose recipients could be assigned a party are
*unresolved* and fall out of the percentage base; the resolution rate is therefore
reported for every row, and D-only + R-only + Mixed = 100%. A separate final column gives
the genuine **dollar-flow** measure: the share of a group's party-resolved dollars that
reached Democratic recipients.

Recipient party comes from the bulk FEC committee and candidate masters on the federal
panel (`backfill_ny_committee_party.py`) and, on the state panel, from
`backfill_ny_recipient_party.py` — NYSBOE publishes no party on the filer, so party is
reconstructed from explicit party words in committee names, finance rows that already
carry a party, and the committee→candidate→roster chain.

**New York.**

| own party | matched | resolved | res. rate | D-only | R-only | Mixed | \| | $ to D |
|---|--:|--:|--:|--:|--:|--:|---|--:|
| *federal panel* | | | | | | | | |
| DEM | 171,349 | 156,142 | 91.1% | **95.3%** | 3.2% | 1.5% | | 95.5% |
| REP | 57,856 | 50,800 | 87.8% | 12.2% | **84.8%** | 3.0% | | 18.3% |
| NOPARTY | 31,319 | 25,074 | 80.1% | **65.1%** | 31.4% | 3.5% | | 75.7% |
| OTHER | 8,694 | 7,122 | 81.9% | 39.1% | 58.9% | 2.1% | | 48.1% |
| *state panel* | | | | | | | | |
| DEM | 216,244 | 80,010 | 37.0% | **89.0%** | 8.2% | 2.8% | | 91.8% |
| REP | 97,632 | 44,443 | 45.5% | 10.8% | **86.2%** | 3.0% | | 22.2% |
| NOPARTY | 48,024 | 12,931 | 26.9% | **52.9%** | 43.5% | 3.6% | | 66.9% |
| OTHER | 16,488 | 5,410 | 32.8% | 35.8% | 59.8% | 4.3% | | 51.6% |

**Idaho.** Idaho Sunshine carries no party on the recipient either, so state recipient
party is reconstructed from the Secretary of State candidate roster plus party/committee
name patterns (`backfill_id_recipient_party.py`). The federal panel needs no
reconstruction — the FEC masters carry party directly.

| own party | matched | resolved | res. rate | D-only | R-only | Mixed | \| | $ to D |
|---|--:|--:|--:|--:|--:|--:|---|--:|
| *federal panel* | | | | | | | | |
| REP | 15,621 | 13,545 | 86.7% | 17.1% | **82.1%** | 0.8% | | 18.1% |
| DEM | 4,764 | 4,473 | 93.9% | **98.5%** | 0.9% | 0.6% | | 99.1% |
| UNAFF | 2,754 | 2,286 | 83.0% | **78.3%** | 20.6% | 1.1% | | 77.7% |
| OTHER | 164 | 102 | 62.2% | 16.7% | 81.4% | 2.0% | | 7.5% |
| *state panel* | | | | | | | | |
| REP | 15,645 | 7,962 | 50.9% | 19.1% | **79.0%** | 1.9% | | 17.6% |
| DEM | 5,097 | 2,985 | 58.6% | **94.6%** | 3.0% | 2.3% | | 97.9% |
| UNAFF | 2,735 | 1,066 | 39.0% | **77.1%** | 20.5% | 2.3% | | 74.3% |
| OTHER | 136 | 44 | 32.4% | 18.2% | 81.8% | 0.0% | | 36.5% |

> **Both state blocks were recomputed 2026-07-27.** They had been left on the all-tier
> match when the panels were rebuilt on the primary specification, while the two federal
> blocks above them were updated — so the table silently set one specification beside
> another and invited exactly the federal-vs-state comparison that mismatch corrupts. The
> state rows now sum to the published panels (NY 378,383; ID 23,613), not to the retired
> all-tier totals (424,020; 27,250). No conclusion in this section changes: Democratic
> loyalty and the unaffiliated Democratic tilt both hold, and the Idaho unaffiliated lean
> strengthens from ~3:1 to nearly 4:1.

*Source: the four panel tables' `donor_party` classification and `d_amount` / `r_amount`
columns, joined to each state's party of record. Aggregate resolution: NY federal **88.8%**,
NY state 37.7%, ID federal **87.6%**, ID state 51.1% of matched donors. *(This line
previously gave 87.8% and 86.7% for the two federal panels; both are the **Republican
row's** resolution rate, not the panel aggregate — read straight off the wrong cell.)*
Script:
`diag_donor_class_revisions.py`. Not covered by `verify_donor_class.py` — the crossover
cut depends on the recipient-resolution logic in the backfill scripts.*

**These tables are exploratory, and the unresolved pool is not missing at random.** The
resolution rate varies systematically by donor group — 91.1% for NY federal Democrats
against 80.1% for the unaffiliated, and on the NY state panel 45.5% for Republicans
against 26.9% for the unaffiliated. Whatever is unresolved is disproportionately the
unaffiliated bloc's giving, in the very rows the reader most wants. At 37.7% aggregate
resolution the NY state column should be read as indicative only.

Read against those limits, two patterns are stable in both panels and both states:

- **Among donors whose recipients can be assigned a party, D-only donors outnumber R-only
  donors within the registered-Democratic and unaffiliated blocs, by wide margins.**
  Registered Democrats are near-monolithic (95.3% D-only federally in NY, 98.5% in ID).
- **Among unaffiliated donors, D-only donors outnumber R-only donors roughly 2:1 in New
  York and nearly 4:1 in Idaho**, and the dollar-flow measure agrees (75.7% and 77.7% of
  resolved dollars to Democrats). This says the unaffiliated bloc's *party-directed giving* leans
  Democratic. It does not establish that these donors are non-centrist ideologically:
  party-directed giving is one behavior, not a measure of ideological position.

The comparison earlier drafts drew — "Republicans fund Democrats at 3.6× the rate
Democrats fund Republicans" — is withdrawn as stated. It compared two donor
*classification* shares (14.2% R-only-party-Republicans classified D-only against 3.9% of
Democrats classified R-only) and read as a dollar-flow statistic. On the dollar-flow
measure the same rows read 20.2% of resolved Republican dollars to Democrats against 5.5%
of Democratic dollars to Republicans. Both are legitimate quantities; neither supports the
compact "3.6×" framing, and the underlying asymmetry is not the paper's claim.

The Idaho state panel's Republican→Democratic figure carries one further caveat: the
unresolved pool there (local Republican candidates and R-aligned PACs absent from the
roster) skews Republican, so Republican donors' Republican-side giving is
disproportionately the untraced part, making the 18.8% D-only rate an **upper bound**. On
the federal panel, at 86.7% resolution from authoritative party labels, the 17.6% figure
carries no such hedge — and it lands within a point and a half of the state panel's upper
bound.

### Idaho — the same skew, in the reddest state, in both money systems

The decisive test of whether the Democratic tilt of the donor class is a blue-state
artifact is to run it where Republicans hold a 5:1 registration edge. Using each donor's
own Idaho affiliation, in each panel separately:

| party | registration | federal donor share | **skew** | state donor share | **skew** |
|---|--:|--:|--:|--:|--:|
| REP | 62.9% | 67.0% | +4.2 | 66.3% | +3.4 |
| DEM | 11.8% | 20.4% | **+8.6** | 21.6% | **+9.8** |
| UNAFF (unaffiliated) | 23.9% | 11.8% | **−12.1** | 11.6% | **−12.3** |
| OTHER (minor) | 1.4% | 0.7% | −0.7 | 0.6% | −0.9 |

*Source: `data/id_vrdb.duckdb` `voters.party` at extract date against the two ID panels.
All 1,029,938 ID records are active, so the active and all-records baselines are
identical. Re-derived by `verify_donor_class.py`.*

Dollar shares track the same way — Republicans supply 68.1% of federal and 71.1% of state
matched dollars, Democrats 21.1% and 20.6%, the unaffiliated 10.3% and 8.0%.

Republicans supply the plurality of Idaho's money, as a 63%-Republican state must — and
Idaho's donors remain predominantly Republican in absolute terms. The finding is
relational: measured against their share of registration, the **most over-represented
donors are registered Democrats** (+8.6 federal, +9.8 state, well over half again their
share of the roll), and the unaffiliated quarter is the most *under*-represented in both
(−11.2, −11.8). Period-aligning the two panels to 2023–2025 does not soften this; on the
aligned federal panel the Democratic share is 21.4% (+9.6) and the unaffiliated 11.7%
(−12.2). The same directional finding as New York, from the opposite end of the spectrum,
in both money systems.

**In-state vs out-of-state, by party.** Money flowing *into* NY's federal races
(`fec_inflow.duckdb`, all-state donors → NY candidates; `diag_ny_donor_extras.py`)
is **44.8% out-of-state for both parties** — nationalization is party-symmetric
at the aggregate, consistent with the cross-state finding that out-of-state
share is uniform across competitiveness (`cross-state-fec-money.md` §G). The one
asymmetry is by office: NY's **Senate Democrats draw 54.1% of their money from
out-of-state** (Schumer/Gillibrand as national magnets) versus ~43–45% for House
candidates of both parties. So the donor class is skewed in *who it is* (above) but not
in *how far its money travels* — except at the marquee Senate tier.

**The skew holds in every kind of district.** Mapping matched donors to their
congressional district's competitiveness (`diag_ny_electorate_extras.py`), the
donor pool's Democratic share **exceeds the registered Democratic share in every
band** — Tossup 57.7% donor vs ~40% registrant, Solid 71.6% vs ~56% — so the
donor class is more Democratic than the registration baseline not just statewide but
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

In both states with the necessary history, the people who give are the people who
reliably vote, and it holds in both money systems — this is the finding least sensitive to
the panel split. In Washington, federal matched donors are **85.5% super-voters versus
51.4%** of non-donors (mean turnout propensity 0.966 vs 0.754); the state panel is nearly
identical at **84.9% versus 50.8%** (0.950 vs 0.751). In New York, federal matched donors
voted in **3.00 of the last four federal generals on average versus 1.85** for non-donors,
and **72.9% are super-voters (≥3 of 4) versus 39.3%**; the state panel lands within a
tenth of a point of that on every measure (2.99 vs 1.84; **73.0% versus 38.9%**), despite
drawing on 116,000 more people.

*Source: WA `voter_scores` (`ld`-scope) and NY `vrdb.voter_participation`, generals
2018/2020/2022/2024. Non-donor denominators are **active registrants**, matching the
matcher's universe; earlier drafts used all retained NY records and read 3.03 vs 1.78 and
73.0% vs 37.1%. Re-derived for both panels of both states by `verify_donor_class.py`.*

The same individuals concentrate *both* forms of influence rather than one offsetting the
other. (Association only — donors are pre-selected for engagement, so reverse causation is
equally plausible; the benign "donating as a gateway to participation" reading is fully
live, and is treated as objection 3 in Appendix A.)

**A nominating-stage corollary, in both party-of-record states.** NY's **closed**
primaries restrict each party's primary to enrollees, so the **25.3% enrolled "blank" are
excluded by law** (≈0.1–0.6% primary participation), and in blue NY the Democratic primary
is frequently the decisive contest (2021 odd-year DEM 16.9% vs REP 5.0%).

Idaho is the mirror image — its **closed Republican primary is the decisive contest** in
nearly every seat — but Idaho's mechanism is different from New York's and is reported
here as composition rather than as a participation rate:

| population | people | REP | DEM | UNAFF |
|---|--:|--:|--:|--:|
| registration roll | 1,029,938 | 62.9% | 11.8% | **23.9%** |
| 2024 general electorate | 898,877 | 64.5% | 11.6% | **22.6%** |
| 2024 primary electorate | 274,684 | 85.2% | 8.3% | **5.9%** |

*Source: `data/id_vrdb.duckdb` `voters.party` × `voter_participation`; party at extract
date. Script: `diag_donor_class_revisions.py`; re-derived by `verify_donor_class.py`.
Ballots actually pulled in the 2024 primary: Republican 229,173 (83.7%), Democratic
33,535 (12.2%), unaffiliated 9,567 (3.5%), Libertarian 952, Constitution 657.*

Unaffiliated registrants are 23.9% of Idaho's roll and 22.6% of its 2024 general
electorate, but **5.9% of its 2024 primary electorate**. Two mechanisms produce that drop
and this design cannot separate them. Idaho's Republican primary is closed to voters who
remain unaffiliated — but **an unaffiliated voter may affiliate with a party up to and
including election day and then vote in that primary.** A voter who does so appears as a
Republican in the later voter-file extract, so part of the 23.9% → 5.9% fall is category
migration rather than non-participation, and the residual 5.9% reflects the unaffiliated
and nonpartisan ballots that remain available. Earlier drafts reported a "6.6% primary
versus 83% general" rate pair; those are withdrawn, both because current-roll denominators
make Idaho rates unreliable (Appendix C) and because a rate cannot distinguish
non-participation from affiliation change.

The population that nominates is small and party-gated in both states — and, per Finding
3, funded by a donor class narrower and more skewed still.

---

## What this paper does not claim, and limits

- **The match is a proxy, and a floor.** Voter↔donor identity rests on name + ZIP
  uniqueness across four tiers (Appendix C), not on a shared identifier. It is
  conservative by design (ambiguous keys are dropped, not guessed), so the matched set is
  a **floor**, not a census, of the donor population. A stratified blinded rating of 480
  matched records (Appendix F) found precision to be a property of the match KEY, so the
  paper now reports the full-first-name key alone: **no detectable false match** there
  (120/120, Wilson [96.9–100]) against **47.9–71.7%** on the three initial-based keys, whose
  failure mode is the household/relative merge. An independent human re-rating of 150 of
  those records agreed on **75 of 75** full-name-key rows and never contradicted a Y. Under
  the superseded all-tier specification population-weighted precision was **93.0%**, and precision was *lower* in the top dollar
  decile (63.0% vs 72.1% raw). Two costs are carried in the open: 100% is a ceiling on
  *detectable* error — a true namesake is invisible to the rating — and the restriction
  discards 11–19% of matched donors who are **younger and less Democratic** than those
  retained, so part of the sharpened skew is selection rather than precision.
- **Itemized giving only, from panels with different disclosure floors.** Each panel omits
  giving below its own itemization threshold — federal aggregate **> $200**, Washington
  **> $100**, New York **> $99**, Idaho **> $50** (Appendix C). Two consequences run in
  different directions and are separated here: on **dollar concentration**, itemized-only
  top shares are higher than the corresponding share of *all* receipts would be, since
  adding the missing small-dollar mass to the denominator would lower every top-1% figure;
  on **donor composition**, excluding small donors makes the observed donor population
  older and narrower than the population of all contributors. Both cut against reading
  these figures as describing all giving. Because the federal floor is 2–4× the state
  floors, part of every federal-vs-state panel difference is a disclosure-regime artifact
  rather than a behavioral one.
- **Panel comparisons are descriptive, not identified.** Federal and state panels differ
  in disclosure threshold, in years covered (Idaho only), and in *who is in them* — they
  overlap by a Jaccard coefficient of 0.14–0.16. "Federal money is older money" is a
  robust difference between two datasets that survives period alignment; it is not an
  established effect of federal versus state regulation. The apparent Idaho exception in
  earlier drafts — that state money did *not* reach more donors there — was a window
  artifact: period-aligned, Idaho's state panel reaches 23,613 donors against the federal
  panel's 14,848 — 59% more — the same direction as WA and NY.
- **Composition, not rates.** All three matches use the current roll, so turnout *rates*
  for older cycles are biased by survivorship. Share-of-population figures, which need no
  denominator, carry the findings. Idaho's age is a current-roll integer, so its bands are
  current-age, not election-time.
- **Registration baselines are active registrants, measured at the extract date.** Party
  and age baselines use `status_code='A'`, the universe the matcher draws from. These are
  registration shares, not shares of the eligible or voting population, and party of
  record is not necessarily a donor's party when they gave.
- **Recipient party is partial, differentially missing, and the crossover tables are
  exploratory.** It resolves for **87.8%** of NY federal and **86.7%** of ID federal
  matched donors, where the FEC masters carry party outright, but only **51.9%** of ID
  state and **37.7%** of NY state donors, where it must be reconstructed. Resolution rates
  differ by donor group, so the unresolved pool is not missing at random. Own-party and
  age cuts use the 100%-present party of record and are unaffected.
- **No policy-influence claim.** This paper measures who gives and who votes. It does not
  measure whether money changes votes, wins elections, or moves policy, and the
  giving↔turnout relationship in Finding 4 is reported as association only.
- **Contribution limits.** Simple mechanical per-gift truncation does not reproduce the
  observed ordering of the state and federal concentration estimates (Appendix G). That is
  a statement about a mechanical simulation, not about the behavioral effect of real
  limits, and no causal claim is made in either direction about what caps do to a donor
  pool.

Appendix A states each objection in full, with the bound on it.

---

## What it means

Across three states that differ in size, partisanship, and election administration —
and across two separately regulated money systems within them — the population that
finances campaigns is the same kind of population: **substantially older than the
registration baseline, top-heavy, geographically concentrated, and — where party is
observable — tilted toward registered Democrats relative to registration and away from
the unaffiliated.** That the pattern reappears in every state-and-panel combination where
it can be measured is the strongest evidence here that it describes donors rather than a
quirk of one disclosure regime — with the caveat that the two systems' panels are largely
different people under different disclosure floors, so their *differences* are descriptive
rather than identified.

New York and Idaho's party of record turns the Washington finding from "the donor class is
demographically unrepresentative" into the sharper, falsifiable claim that it is *also*
partisan-unrepresentative in a specific direction — and, critically, in the **same**
direction in a deep-blue and a deep-red state, so the result is not mechanically
attributable to which party holds the statewide registration plurality. Whether it
reflects something more general about who gives, this design cannot say.

Combined with the turnout and safe-seat papers, the picture is a series of narrowing
filters between the registered population and actual influence — who votes, who votes in
the decisive primary, and who pays — each one older and less representative than the last.
This is the evidentiary core of the electoral-health series' "donor class ≠ electorate"
finding, now resolved by party across the spectrum.

---

# Appendices

## Appendix A — The objections, in full

The strongest objections to this paper are about the *match*, not the findings. Six are
stated below at full strength, then bounded. Objections 1, 2, 5 and 6 can be tested with
data in hand and are; objection 3 is not identifiable from this design and is conceded as
live; objection 4 is bounded by the direction of the missingness.

**1. The matcher selects old people, so the age skew is manufactured.** The match key
requires a name + ZIP triple that is *unique* on the roll. Rare names, stable addresses,
and long tenure all correlate with age, so the objection is that Finding 1 measures
matchability rather than giving. This is testable head-on, and it fails: the probability
that a voter is uniquely matchable is nearly flat across age (NY 94.5–95.4% across four
bands; WA 96.3–97.6% across five generations), so inverse-propensity re-weighting does not
move the distribution — NY's 65+ donor share is unchanged at 47.9%, and every Washington
generation multiplier is unchanged to two decimal places in both panels. A selection
gradient that flat cannot produce a 2.5× senior over-representation. What this test covers
is precisely age variation in *unique-key availability*; it does not address false-match
rates, mobility, or survivorship, which are objections 2 and the Appendix F residual.
Full tables in Appendix F.

**2. Household false-merges inflate individual donors.** Because the key is surname plus
ZIP, a married couple sharing both can in principle collapse into one matched voter,
attributing a spouse's giving to their partner. Hand rating of a 150-record sample
(2026-07-10), and a stratified blinded re-rating of 480 records (2026-07-27), both found
this the dominant error mode — and the re-rating localised it precisely: **129 of 152
confirmed false matches are household/relative merges, every one of them on an
initial-based key, none on the full-name key**. Earlier drafts
asserted that the effect on the findings is "small by construction" because spouses share
household, ZIP and approximate age. **That argument is withdrawn**: spouses can differ in
age, party enrollment and turnout history, and merging two people's contributions into one
donor total directly increases measured concentration. It is replaced by a bounding
exclusion. Dropping every matched donor who shares a surname and ZIP5 with any other
active registrant — a deliberate over-exclusion that removes 75–83% of matched donors,
most of them correctly matched — moves the top-1% share by at most 4.7 points in either
direction and *raises* the senior share in all six panels. A tighter surname+address
variant moves the top-1% share by up to 6.1 points, again in both directions. Neither
variant reverses any finding, but neither shows the effect to be uniformly small either;
the full table is in Appendix F.

**3. Donors vote more because donating is a gateway to participation, not because the
same elite holds both forms of voice.** Finding 4 is an association, and the causal arrow
is genuinely ambiguous: donors are pre-selected for engagement, and a first contribution
plausibly *increases* subsequent turnout. Nothing here distinguishes the two readings,
and the benign one is fully live. What survives either reading is the descriptive point,
which is all Finding 4 claims: the two forms of influence sit on the same people rather
than on complementary populations.

**4. The crossover tables' unresolved pool is not missing at random.** Recipient party is
reconstructed rather than published on both state panels, resolving 51.9% of ID and 37.7%
of NY state matched donors, and resolution rates differ by donor group by up to 18 points.
The unresolved Idaho pool — local Republican candidates and R-aligned PACs absent from the
Secretary of State roster — skews Republican, so Republican donors' Republican-side giving
is disproportionately untraced and the 18.8% D-only figure is an upper bound. The tables
are presented as exploratory for this reason. The two patterns that *are* claimed
(near-monolithic Democratic loyalty; unaffiliated donors' resolved giving leaning
Democratic) are robust to the unresolved pool because it cannot plausibly reverse them,
and they hold on the federal panels where resolution is 86.7–87.8%.

**5. Itemization hides the small-dollar end, so concentration is overstated.** Correct,
and the paper now says so rather than arguing the objection runs the other way. Each panel
omits giving below its own threshold (federal > $200; WA > $100; NY > $99; ID > $50).
Adding the missing small-dollar mass to the denominator would **lower** every top-1%
share, so the reported figures describe the *itemized* universe and are upper bounds on
concentration among all givers. Separately, and in the same direction as the paper's
argument, excluding small donors makes the observed donor population older and narrower
than the population of all contributors. Earlier drafts said the omission "understates"
concentration; that was wrong, and Appendix A and the limitations section previously
contradicted each other on it.

**6. State contribution caps, not donor behavior, explain Idaho's flatter distribution.**
This was the paper's own earlier explanation, and Appendix G shows a mechanical truncation
simulation does not reproduce it. It is retained here as an objection because it is the
intuitive reading, and because the simulation bounds only the mechanical channel, not the
behavioral one.

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
  elections-purpose certification the State Board of Elections requires. The extract as
  delivered carries **individual party enrollment** and **full date of birth**; that is a
  statement about the columns in the production received under this request, not a
  statutory entitlement — the Board's public request page does not document the delivered
  layout, and the FOIL citation alone does not establish it. Only aggregate cohort counts
  are released here.
- **Idaho.** The statewide voter file from the Secretary of State. **Idaho Code
  § 34-437A(3)** governs the publicly available statewide list of registered electors,
  which includes name, street and mailing address, county, gender, **age (not date of
  birth)**, declared party affiliation, and a record of which elections the elector
  participated in — the statutory reason Idaho age is a current-roll integer rather than
  an election-time DOB, and the reason Idaho's age bands are read against the current
  roll. Protected registration-card information (including date of birth and
  driver's-license data) is governed separately. **Idaho Code § 74-120** is a distinct
  provision: it restricts distribution or sale of agency lists for use as mailing or
  telephone-number lists. Earlier drafts cited § 74-120 as the source of the age-not-DOB
  release and stated that address detail is withheld; both were wrong — the public list
  includes address, subject to separate protections for confidential-address registrants.
- **Contribution data are public records in every layer used.** FEC bulk individual
  contribution files; Idaho Sunshine state contribution filings; Washington PDC filings;
  the NYSBOE contribution disclosure feed. No access restriction applies to them, and
  none are voter-file derived.
- **What is released.** Aggregate counts and shares only, with cell sizes in the
  thousands to millions. No individual-level records, names, or addresses appear in this
  paper, in the verification scripts' output, or in the repository. The one artifact that
  contains individual rows — the match-validation samples used in Appendix F — lives
  under gitignored `data/` and is not committed. The 480 blinded **verdicts** are
  published, stripped of every name and voter id, at
  `docs/reference/match_validation_verdicts_2026-07-27.csv`, so the precision result is
  independently re-scorable without redistributing any voter data. Only citations and code are published,
  not data. Full provenance and access dates:
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
  differently (Appendix G).
- **Disclosure thresholds, per panel.** Contributions below a threshold are reported only
  in aggregate and cannot be attributed to a person, so each panel's small-dollar floor is
  a property of its own statute — the $200 federal figure is **not** a uniform rule and
  earlier drafts wrongly applied it to all six panels:

  | panel | itemization threshold | authority |
  |---|---|---|
  | Federal (FEC), all three states | contributor aggregate **> $200** per cycle/year | 52 U.S.C. § 30104(b)(3)(A) |
  | Washington (PDC) | contributor identity required above **$100** aggregate; occupation/employer above $250; **mini-reporting** committees exempt (≤$7,000 raised, ≤$500 per contributor) | RCW 29B (formerly RCW 42.17A.240); PDC threshold effective Jan. 8, 2024 |
  | New York (NYSBOE) | aggregate **> $99** must be itemized; $99 or less reportable in the aggregate | N.Y. Elec. Law § 14-102 |
  | Idaho (Sunshine) | aggregate **> $50** itemized by name and address; $50 or less reportable as a single item | Idaho Code § 67-6607 |

  Because every state floor is below the federal one, the state panels reach deeper into
  small-dollar giving. That alone predicts state panels with more donors, younger donors,
  and lower concentration — the direction of two of the three observed panel differences.
  This is a confound on the panel *comparison*; it does not affect any within-panel
  finding.
- **Temporal alignment.** Panel comparisons are only identified if both panels cover the
  same years. Contribution-date coverage, by source:

  | state | federal layer | state layer | aligned as built? |
  |---|---|---|---|
  | Washington | FEC 2017–2026 | PDC 2016–2026 | yes |
  | New York | FEC 2017–2026 | NYSBOE 2017–2026 | yes |
  | Idaho | FEC 2017–2026 | Sunshine **2023–2025** | **no** |

  Idaho's Sunshine layer holds three years against the federal layer's ten (earlier drafts
  said 2022–2025; the earliest Sunshine contribution date is 2023-01-01). Both Idaho panels
  are therefore also rebuilt on the shared 2023–2025 window by
  `diag_donor_class_revisions.py --build-aligned`, which passes `date_min` / `date_max` to
  the matcher. Aligned, the federal panel falls from 23,303 to 14,848 donors and $42.1M to
  $18.4M; the state panel is unchanged, confirming Sunshine lies entirely inside the
  window. Every direction reported for Idaho survives alignment, and two strengthen (the
  age gap widens; the state panel's donor-count advantage appears, removing what earlier
  drafts described as an Idaho inversion).
- **Panel overlap.** The two panels are not the same people under two rule sets:

  | state | federal | state | in both | Jaccard | 65+ state-only / fed-only / both |
  |---|--:|--:|--:|--:|---|
  | Washington | 147,745 | 217,114 | 49,943 | 0.159 | 32.9% / 53.6% / **59.6%** |
  | New York | 269,218 | 378,383 | 89,704 | 0.161 | 34.4% / 47.3% / **55.0%** |
  | Idaho | 23,303 | 23,613 | 5,780 | 0.141 | 46.0% / 66.5% / **67.6%** |

  In all three the both-systems group is *older than either single-system group*, so
  multi-system giving is itself age-graded and the age difference between panels is not a
  clean property of the regulatory layer. Idaho's near-equal panel counts (23,303 and
  23,613) reflect two largely disjoint populations of similar size, not a fixed donor
  pool; earlier drafts read them as evidence the donor population is "nearly fixed," which
  the 0.140 Jaccard contradicts.
- **The New York state panel.** NYSBOE publishes contributions as a transaction-level
  feed (data.ny.gov `4j2b-6a2j`, 12.6M rows back to 1999) carrying contributor last name,
  first name, and ZIP — everything the match key needs. Earlier drafts reported that New
  York had no state panel; that was a tooling gap, not a data gap, and the claim survived
  in one limitation bullet after the panel was built. The repo's NY adapter read the same
  feed but kept only roll-up columns for `candidate_finance` and discarded contributor
  identity. `scripts/load_ny_contributions.py` now loads the per-contribution rows. Scope:
  individual contributors (`CNTRBR_TYPE_DESC = 'Individual'`) on Schedule A (monetary
  receipts, the direct analog of the FEC itemized individual file), cycles 2018–2026 to
  align with the WA PDC window — 3,954,090 contributions totalling $880.3M, of which
  $379.5M matches to a registered New York voter. Out-of-state donors are retained, as they
  are in the WA and ID state panels; the voter-roll join drops them. Odd cycles are
  included deliberately: New York runs odd-year municipal and county elections, and the
  Washington state panel likewise spans its odd years.
  `scripts/sanity_check_ny_contributions.py` audits the load and passes. Two findings from
  it are worth stating. **Amended filings do not double-count**: 44% of rows sit on amended
  reports, but amended reports carry fresh transaction numbers, and a content-level test
  (same filer, contributor, date and amount) finds only **0.66%** of dollars in duplicate
  groups — a residue that on inspection is sequential same-day repeat gifts, not
  restatements. And the even-cycle slice comes to 84% of the independently-aggregated
  `candidate_finance` individual total for the same cycles, the expected relationship given
  that this panel takes Schedule A alone while the aggregate also counts Schedules B, C and
  G. A few hundred `SCHED_DATE` values are transcription errors (years 206, 1900, 1919); no
  figure in this paper reads that column — cycle, amount and identity all come from other
  fields. A further 45,494 rows ($1.7M) in the NY contribution table carry no source
  prefix and are excluded from both panels by construction.
- **The match key and its four tiers.** Matching proceeds in tiers, strictest first. Every
  tier carries the same guard: the key must resolve to **exactly one** voter on the roll
  and one donor identity, or the record is dropped rather than guessed. Only active
  registrants (`status_code='A'`) are eligible on the roll side.

  | tier | key | share of matches (federal / state, pooled across states) |
  |---|---|---|
  | `STRICT_ZIP5_FULL` | surname + **full** first name + ZIP5 | 85–89% |
  | `STRICT_ZIP5_MID` | surname + first initial + middle initial + ZIP5 | 0.4–2% |
  | `STRICT_ZIP5` | surname + first initial + ZIP5 | 9–13% |
  | `RELAXED_ZIP3_MID` | surname + first initial + middle initial + **ZIP3** | 0.3–5% |

  Blinded validation (Appendix F) measures precision at **100%** for the first tier and
  **47.9-71.7%** for the other three, so the tiers are not interchangeable and the paper
  reports a full-name-only sensitivity for every headline number. The fourth tier is the
  weakest — it widens the geography from a ZIP5 to a ZIP3 and leans on the middle initial
  alone to disambiguate — and it fires only when both sides carry a middle initial.
  Two further defects are **panel-specific and follow from file format**: WA PDC and Idaho
  Sunshine file people without a comma, so the parser takes the first token as the surname.
  In the Idaho state panel that lets **organisations** (committees, LLCs, trusts) match as
  people, and in the WA state panel it mis-matches records genuinely filed
  first-name-first. Both are confined to the initial-based tiers in the validation sample.

  Both are now measured from source fields rather than name shapes. Idaho Sunshine's
  `Contributor Type` was loaded on 2026-07-27, and it shows organisations and committees are
  **8.1% of its rows but 53.9% of its dollars** ($28.70M of $53.26M) — well above the
  32.6% a name heuristic had estimated. The matcher now excludes them from a real field. That
  changed **no** figure in this paper: tested directly, **zero** organisation rows could ever
  have matched on the full-first-name key, so the primary specification never contained the
  contamination. It remains in the retained all-tier panels, which is where the validation
  found it. The WA PDC name-order mode measures **1.85% of comma-less rows / 2.08% of its
  dollars** — not the 0.1% / 0.8% organisation figure an earlier draft cited as its
  analogue, which measures a different defect. Earlier drafts described the key as "last name + first name +
  ZIP5" without disclosing the initial-based or ZIP3 tiers. Adding the full-first-name
  tier raised Washington's matched count from 320K to 382K (+19%) and it is now dominant.
  Appendix F reports every headline estimate with the weaker tiers removed. Because
  ambiguity is dropped, the matched set is a floor.
- **Registration baselines.** Party and age baselines use **active registrants**
  (`status_code='A'`) throughout — the same universe the matcher draws from. NY is 91.9%
  active (12,448,081 of 13,540,558). Idaho's statewide export carries **no
  active/inactive flag** — it is a current-roll extract, and the loader sets every row
  active so the shared matcher works — so for Idaho the two baselines coincide by
  construction and no active-only test is possible there. An earlier version used
  all retained records for the party baseline and active-only for age; standardising moves
  no NY party skew by more than 0.4 points and no ID figure at all. Party of record is
  measured at the voter-file extract date, while contributions span prior years, so it is
  not necessarily the donor's party at the time of the gift.
- **Concentration estimator.** Donors are ranked by total matched dollars and split into
  100 **equal-count** buckets (`NTILE(100)`) over donors with `total_donated > 0`; the
  top-1% and top-10% figures are the top 1 and top 10 buckets' dollars divided by all
  matched dollars. Equal-count buckets are used deliberately: capped and round-number
  giving produces heavy ties, and an earlier draft using `PERCENT_RANK` drifted from an
  exact decile at small N, reading Idaho's top-10% as 69.0% rather than 70.8%. Gini is
  computed on the same donor totals by the rank-weighted formula. Appendix G reuses this
  identical estimator so its layer comparisons are commensurable with Finding 2.
- **Reconstructing recipient party on the state panels.** Neither NYSBOE nor Idaho
  Sunshine publishes the recipient's party, so the crossover cut needs it inferred.
  `backfill_ny_recipient_party.py` works in four uniqueness-guarded tiers — an explicit
  party word in the committee name (dropped if a name claims both), a party already
  present on the finance row, a committee→candidate→roster chain, and containment of a
  roster candidate's full name — reaching 37.7% of matched state donors. A fifth,
  bare-surname tier of the kind Idaho can use was built and **rejected**: Idaho's
  recipient strings are "LAST, FIRST" candidate names, whereas New York's are free-text
  committee names, so searching for a surname inside a phrase misfires — it read "FRIENDS
  OF DAVID KNAPP" as Republican via the surname *David* and "SARATOGA COUNTY GREEN PARTY"
  as Republican via *Green*. It would have added roughly $67M of apparently-resolved money
  at the cost of silent misassignment. Corporate, labor and trade PACs are left unresolved
  by design in both states: they are genuinely non-partisan recipients and a large share
  of state money, and giving them a party would manufacture a crossover result rather than
  measure one. The consequence is that the unresolved pool is large and not missing at
  random, which is why the crossover tables are labelled exploratory.
- **The crossover classification, stated exactly.** `donor_party` classifies a *donor* by
  the set of their party-resolved recipients: `D_DONOR` (every resolved recipient
  Democratic), `R_DONOR` (every one Republican), `MIXED` (both), `OTHER` (none resolved).
  The Finding 3 tables report these as D-only / R-only / Mixed shares of *resolved donors*,
  and report the resolution rate separately. They are **not** dollar flows; the dollar-flow
  column is computed separately from the panels' `d_amount` / `r_amount` sums. Earlier
  drafts printed the classification shares under "→ D" / "→ R" headers, omitted the Mixed
  column that is part of the base, and described the result in dollar-flow language.
- **Match-bias re-weighting.** P(uniquely matchable) is estimated per age band or
  generation directly on the roll, and donor shares are re-weighted by its inverse. This
  is the test in Finding 1 and Appendix F; it was run for WA and NY, not for ID. It
  addresses age variation in unique-key availability only.
- **Age conventions differ by state, by statute.** WA and NY supply birth date (WA
  year-only, per RCW 29A.08.710), so ages are election-time. Idaho supplies a current-roll
  integer age (Idaho Code § 34-437A(3)), so Idaho bands are current-age and are compared
  against the current roll, not an election-time cohort.
- **Rates versus shares.** Turnout *rates* computed from a current roll are inflated by
  survivorship wherever the roll has shrunk — acutely in Idaho, whose 2026 roll (1.03M) is
  smaller than the 1.18M registered at the 2024 election. Rate cuts are therefore not
  reported for Idaho, and all headline figures in this paper are denominator-free
  composition shares.
- **Known data-quality residue.** `ny_vrdb.voters` contains 53 duplicated
  `state_voter_id` values out of 13.54M records (0.0004%); joins on that key can therefore
  fan out by a handful of rows, which is why the NY state panel reads 378,383 rows
  standalone and 424,025 after a roll join. No reported figure is sensitive at that
  magnitude.
- **Reproduction.** `scripts/verify_donor_class.py` re-derives Findings 1, 2 and 4 for
  both panels of all three states, Finding 3 for both panels of NY and ID (Washington
  publishes no party), the Idaho primary-composition corollary, and the period-aligned
  Idaho panels — from scratch SQL, importing no analysis code.
  `scripts/diag_contribution_limits.py` produces Appendix G;
  `scripts/diag_donor_class_revisions.py` produces the denominator, tier, household,
  overlap and composition tables. The verifier explicitly does **not** cover the crossover
  tables, the inverse-propensity re-weighting, the tier and household sensitivities, or the
  hand-rated sample; the first three are reproduced by the scripts just named, and the
  last by `diag_match_validation_stratified.py` + `score_match_validation.py`, whose
  published verdict ledger makes it re-scorable without the PII-bearing sample.

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
  (2013): 103–124, doi:10.1257/jep.27.3.103 — the concentration result (Finding 2).
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
  for Finding 3 (New York *and* Idaho).
- **Giving and voting as stacked participation.** Verba, Schlozman & Brady (1995) again,
  on the co-occurrence of participatory acts; the giving↔turnout overlap (Finding 4) is
  the individual-record instance, framed strictly as association.
- **Voter-file / individual-level method.** Ansolabehere & Hersh, "Validation: What Big
  Data Reveal About Survey Misreporting and the Real Electorate," *Political Analysis*
  20(4) (2012): 437–459, doi:10.1093/pan/mps023; Hersh, *Hacking the Electorate: How
  Campaigns Perceive Voters* (Cambridge, 2015). On match bias and the current-roll caveat,
  the tier and household sensitivities and the inverse-propensity re-weighting in
  Appendix F address the older/stable-address/uncommon-name skew directly.
- **Contribution limits and the shape of the donor pool.** The statutory regimes tested in
  Appendix G, with individual per-election limits for the 2025–26 cycle:
  Idaho Code § 67-6610A (**$1,000** per election to legislative, judicial, and local
  candidates and **$5,000** to statewide candidates, primary and general counted
  separately, self-funding exempt; 2026 S.B. 1422 proposed raising these to $1,500 and
  $6,000 but was retained on the calendar);
  RCW 42.17A.405, recodified as RCW 29B.40.020 effective Jan. 1, 2026 — Washington's caps,
  indexed and administered by the Public Disclosure Commission, currently **$1,200** per
  contest to a legislative candidate and **$2,400** to a state executive candidate;
  N.Y. Elec. Law §§ 14-114 and 14-116 — New York's non-family individual limits per
  contest, **$3,000** Assembly, **$5,000** Senate, **$9,000** statewide, alongside an
  extensive separate family-limit schedule (earlier drafts characterised these as
  "comparatively high" without stating them);
  Tex. Elec. Code § 253.094, which bars corporate and labor-organization contributions —
  and, separately, the absence of any dollar limit on individual gifts to **non-judicial**
  Texas candidates, which § 253.094 does not address and which rests instead on the Texas
  Ethics Commission's *Campaign Finance Guide for Candidates and Officeholders*; the
  Judicial Campaign Fairness Act, §§ 253.151–253.176, is the exception that does impose
  limits;
  52 U.S.C. § 30116 (the federal per-election individual limit, **$3,500** for 2025–26,
  indexed); and 52 U.S.C. § 30118 (federal prohibition on corporate contributions, which
  the Idaho and Texas state systems do not share). On the constitutional architecture that
  leaves per-gift caps standing while removing any ceiling on a donor's total giving:
  *Buckley v. Valeo*, 424 U.S. 1 (1976) (contribution limits upheld, expenditure limits
  struck), and *McCutcheon v. FEC*, 572 U.S. 185 (2014) (invalidating the biennial
  aggregate limit). On the empirical consequence — that limits redistribute large-donor
  influence across vehicles rather than removing it: Barber, "Ideological Donors,
  Contribution Limits, and the Polarization of American Legislatures," *Journal of
  Politics* 78(1) (2016): 296–310, doi:10.1086/683453; La Raja & Schaffner, *Campaign
  Finance and Political Polarization: When Purists Prevail* (Michigan, 2015). Appendix G's
  result is consistent with that literature.

## Appendix E — Full distribution tables

**Matched-donor concentration, with bootstrap intervals.** Both Washington panels were
bootstrapped at B=1,000 resamples (`diag_donor_concentration_bootstrap.py`). The
intervals are tight enough that the concentration finding does not rest on a handful of
top donors, and the two panels' intervals overlap — the state layer's higher point
estimate is not separable from the federal layer's at this precision:

| Washington, matched donors | federal panel | 95% interval | state panel | 95% interval |
|---|--:|---|--:|---|
| top 1% → share of matched $ | 41.2% | [38.6–43.4] | 43.5% | [38.7–48.9] |
| top 10% → share of matched $ | 74.2% | [73.0–75.2] | 75.3% | [73.2–77.7] |
| Gini | 0.815 | [0.806–0.822] | 0.821 | [0.806–0.838] |

**Statewide (all itemized donors, not only matched), four states.** From
`cross_state_fec_money.py` over each state's FEC individual layer, donor-residence
filtered, FEC bulk files 2017–2026, itemization threshold > $200 throughout. This is the
one table in the paper where Texas appears, since aggregate donor figures need no voter
file:

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
| NY federal | New York County (Manhattan) | 50.3% | Westchester 12.4%, Kings 6.6%; top-3 ZIP3 = **63.4%** |
| NY state | New York County (Manhattan) | 20.6% | Nassau 15.1%, Suffolk 11.1%; top-3 ZIP3 = **38.1%** |
| ID federal | Ada County (Boise), 10,338 donors | 36.4% | Blaine 11.7%, Bonneville 11.2% |
| ID state | Ada County (Boise), 10,037 donors | 49.2% | Kootenai 9.0%, Canyon 5.5% |

*Source: the six panel tables joined to each roll's ZIP or county of registration.
Scripts: the per-state match and `diag_*_donor_extras` scripts; WA federal ZIP3s
re-derived by `verify_donor_class.py`.*

Two of the three states put federal money in a tighter geographic box than state money,
and in New York the gap is enormous — Manhattan's share of matched dollars falls by
**30 points**, from half of the federal layer to a fifth of the state one, with suburban
Nassau and Suffolk together overtaking it. Manhattan nonetheless remains the largest
single county in the state panel. Idaho inverts the pattern — Ada County's grip *loosens*
from 49.2% of state dollars to 36.4% of federal — not because Idaho's federal money is
broadly spread, but because it relocates to wealthy enclaves outside the capital, above
all resort-county Blaine at 11.7% from 1,097 donors. Concentration is the constant; which
geography does the concentrating depends on the money system. A plausible mechanism is
that state legislative seats are contested across far more of a state's territory than
its federal seats, so state money is raised more widely while federal money pools where
national donors live; this paper does not test it, and it should not be read as implying
that state legislative races are meaningfully contested everywhere — many are not (see
[`safe-seat-washington.md`](safe-seat-washington.md)).

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

**Giving and turnout, side by side.** Non-donor denominators are active registrants.

| | donors | non-donors |
|---|--:|--:|
| WA super-voter share, federal panel | 88.0% | 52.0% |
| WA mean turnout propensity, federal panel | 0.977 | 0.755 |
| WA super-voter share, state panel | 88.9% | 51.5% |
| WA mean turnout propensity, state panel | 0.966 | 0.753 |
| NY generals voted, of last 4, federal panel | 3.10 | 1.85 |
| NY super-voter share (≥3 of 4), federal panel | 75.7% | 39.3% |
| NY generals voted, of last 4, state panel | 3.07 | 1.84 |
| NY super-voter share (≥3 of 4), state panel | 75.3% | 39.0% |

The give↔vote overlap is the finding least sensitive to which money system is examined:
Washington's two panels differ by half a point, and New York's by a tenth of one — even
though New York's state panel draws on 116,000 more people than its federal panel.

## Appendix F — Match validation and robustness

**Is matchability age-dependent?** This is objection 1, tested directly. P(a voter is
uniquely matchable) is computed on the roll itself, then donor shares are re-weighted by
its inverse:

| state | spread of P(matchable) | re-weighted result |
|---|---|---|
| NY, four age bands | **94.5%–95.4%** (0.9-pt spread) | 65+ donor share 47.9% → **47.9%** |
| WA, five generations | **96.3%–97.6%** (1.4-pt spread) | every multiplier unchanged to 2 d.p., **both panels** (federal Silent 2.48 → 2.48×, Gen Z 0.10 → 0.10×; state Silent 1.59 → 1.59×) |

A selection gradient that flat cannot generate the observed senior over-representation.
Two notes on the Washington row. First, P(uniquely matchable) is a property of the *roll*
and the match key, not of which contributions are used, so the same propensities re-weight
both panels; only the multipliers they act on are panel-specific. Second, the WA test uses
a slightly narrower denominator than Finding 1 (active registrants carrying a ZIP), so its
raw multipliers sit a few hundredths below Finding 1's — the quantity of interest is the
raw-to-re-weighted *difference*, which is zero to two decimals either way. An earlier
draft, computed on the pooled match and a stricter matchability definition, reported a
68.9–73.1% spread and reached the same null result (Silent 1.87 → 1.83×). Idaho was not
separately re-weighted. **What this test does and does not cover:** it establishes that the
observed age skew is not explained by age variation in unique-key availability in the WA
and NY voter files. It does not test false-match probability, donor-side name
completeness, residential mobility, party-classification error, or survivorship on the
current roll.

**Match-tier composition and the inverted sensitivity.** This table is computed on the
**retained `_alltier` snapshots** — the pre-switch panels, kept precisely so this comparison
remains possible once the primaries became single-tier. `STRICT_ZIP5_FULL` carries
**80.7–89.2%** of matches there; the weakest ZIP3 tier carries 0.3–5%.

Read it in the direction the paper now runs: the `full-first-name only` row **is** the
primary specification, and the rows above it show what **adding the weak tiers back** would
do. Doing so lowers the senior share in all six panels and the Democratic share in all four
party panels — i.e. moves every finding *toward* the null.

**One caveat on this table specifically.** It restricts by the persisted `match_quality`
column, which keeps a full-tier donor's *entire* dollar total including gifts that only
matched on a weak key. The rebuilt panels restrict at match time and therefore hold
**3.8–9.4% fewer dollars** (WA federal $375.26M under the filter against $346.32M as
rebuilt). Donor counts are identical either way, and the senior/party shares below are
person-level so they carry across — but the concentration figures in this table are **not**
the published ones. Finding 2's come from the rebuilt panels.

| panel | subset | donors | top 1% | Gini | 65+ | key party share |
|---|---|--:|--:|--:|--:|--:|
| WA federal | all tiers | 172,998 | 42.4% | 0.820 | 53.4% | — |
| | drop ZIP3 tier | 168,953 | 42.5% | 0.820 | 53.8% | — |
| | full-first-name only | 147,745 | 42.2% | 0.821 | **55.7%** | — |
| WA state | all tiers | 269,204 | 43.8% | 0.827 | 37.1% | — |
| | drop ZIP3 tier | 255,758 | 43.8% | 0.825 | 38.0% | — |
| | full-first-name only | 217,114 | 44.5% | 0.829 | **39.0%** | — |
| NY federal | all tiers | 307,841 | 51.2% | 0.867 | 47.9% | DEM 62.8% |
| | drop ZIP3 tier | 302,410 | 51.2% | 0.867 | 48.2% | DEM 63.0% |
| | full-first-name only | 269,218 | 51.0% | 0.867 | **49.9%** | DEM **63.6%** |
| NY state | all tiers | 424,020 | 48.5% | 0.846 | 38.4% | DEM 56.7% |
| | drop ZIP3 tier | 422,594 | 48.5% | 0.846 | 38.5% | DEM 56.7% |
| | full-first-name only | 378,383 | 48.8% | 0.847 | **39.3%** | DEM **57.1%** |
| ID federal | all tiers | 27,196 | 35.8% | 0.786 | 64.7% | DEM 19.9% |
| | drop ZIP3 tier | 26,529 | 36.1% | 0.787 | 65.1% | DEM 20.0% |
| | full-first-name only | 23,303 | 37.1% | 0.792 | **66.8%** | DEM **20.4%** |
| ID state | all tiers | 27,250 | 39.3% | 0.798 | 51.1% | DEM 20.9% |
| | drop ZIP3 tier | 27,167 | 39.4% | 0.798 | 51.2% | DEM 20.9% |
| | full-first-name only | 23,613 | 40.4% | 0.802 | **51.3%** | DEM **21.6%** |

Every finding survives, and restricting to the strictest tier moves the age and party
skews *away* from the null in all six panels: the weaker tiers are slightly younger and
slightly less Democratic than the strict tier, so including them is conservative.
Concentration moves by at most 1.3 points (Idaho federal, where N is smallest).

**Household false-merge sensitivity.** A bounding exclusion, replacing the withdrawn
"small by construction" argument. Like the tier table above, this is computed on the
**retained `_alltier` snapshots**, so it bounds the effect for the *superseded* all-tier
specification — which is the conservative place to measure it. On the primary
specification the household risk is lower by construction: all 129 household/relative false
merges in the 480-record validation landed on an initial-based key, and the primary
specification contains none of those keys. A matched donor is flagged when another active
registrant shares their surname and ZIP5 — the configuration in which a spouse's gift
could be attributed to the wrong person. The exclusion is deliberately severe: because the
match key already required a unique first name, most flagged matches are correct, so these
rows bound the false-merge effect rather than correcting for it.

| panel | variant | donors | top 1% | 65+ |
|---|---|--:|--:|--:|
| WA federal | all matched | 172,998 | 42.4% | 53.4% |
| | excl. surname+ZIP5 shared | 37,688 | 40.1% | 55.2% |
| | excl. surname+address shared | 81,593 | 39.7% | 53.6% |
| WA state | all matched | 269,204 | 43.8% | 37.1% |
| | excl. surname+ZIP5 shared | 51,021 | 43.0% | 39.2% |
| | excl. surname+address shared | 119,264 | 41.6% | 37.4% |
| NY federal | all matched | 307,841 | 51.2% | 47.9% |
| | excl. surname+ZIP5 shared | 77,477 | 48.1% | 49.3% |
| | excl. surname+address shared | 156,888 | 50.6% | 46.8% |
| NY state | all matched | 424,020 | 48.5% | 38.4% |
| | excl. surname+ZIP5 shared | 87,972 | 52.1% | 41.9% |
| | excl. surname+address shared | 188,094 | 49.0% | 39.1% |
| ID federal | all matched | 27,196 | 35.8% | 64.7% |
| | excl. surname+ZIP5 shared | 4,740 | 31.1% | 70.8% |
| | excl. surname+address shared | 10,529 | 32.3% | 68.3% |
| ID state | all matched | 27,250 | 39.3% | 51.1% |
| | excl. surname+ZIP5 shared | 4,579 | 36.5% | 58.9% |
| | excl. surname+address shared | 9,958 | 45.4% | 56.4% |

Under the surname+ZIP5 exclusion the top-1% share moves by at most 4.7 points and rises in
one of six panels; under the tighter surname+address exclusion it moves by up to 6.1 points
and rises in two of six. The senior share rises in all six panels under the ZIP5 exclusion
and in five of six under the address exclusion (NY federal falls 1.1 points). So household
merging is not what produces either finding — every direction survives — but its effect on
measured concentration is panel-specific in both sign and size rather than uniformly small,
which is why the earlier "small by construction" claim was withdrawn rather than restated
with a smaller number.

**Per-tier false-merge risk on the donor side.** Two indicators computed over every
matched donor, needing no human step:

| panel | tier | donors | donor full first name agrees | key also pulls a different first name |
|---|---|--:|--:|--:|
| WA federal | `STRICT_ZIP5_FULL` | 147,745 | 100.0% | **8.6%** |
| | `STRICT_ZIP5` | 18,476 | 1.0% | 3.0% |
| | `STRICT_ZIP5_MID` | 2,715 | 32.6% | 22.8% |
| | `RELAXED_ZIP3_MID` | 4,045 | 0.3% | 0.3% |
| NY federal | `STRICT_ZIP5_FULL` | 269,218 | 100.0% | **7.2%** |
| | `STRICT_ZIP5` | 29,292 | 4.3% | 3.8% |
| | `STRICT_ZIP5_MID` | 3,857 | 49.9% | 18.0% |
| | `RELAXED_ZIP3_MID` | 5,430 | 0.6% | 0.5% |
| ID federal | `STRICT_ZIP5_FULL` | 23,303 | 100.0% | **7.6%** |
| | `STRICT_ZIP5` | 2,678 | 1.3% | 2.0% |
| | `STRICT_ZIP5_MID` | 544 | 31.1% | 16.7% |
| | `RELAXED_ZIP3_MID` | 667 | 0.3% | 0.0% |

The final column is the population genuinely at risk of a relative/household merge: the
match key also pulls contributions carrying a *different* full first name. On the dominant
tier that is 7–9% of matches. That is the residual risk the blinded rating below cannot
see — a same-name namesake — and it is the reason the full-name tier's measured 100% is a
ceiling on detectable error rather than proof of zero error. The `STRICT_ZIP5_MID` tier is the riskiest at 17–23%, and it is
also the smallest (0.4–2% of matches). Row counts here sit a few dozen below the tier
composition in the table above because this query additionally requires a non-null roll
name and ZIP. Note that 100% full-name agreement on `STRICT_ZIP5_FULL` is true by
construction — that tier *is* the full-name key — so the informative column is the
collision rate; the agreement column is diagnostic for the initial-based tiers, which by
construction fire when the full names do not match.

**Match precision — stratified, blinded, and recorded.** The 2026-07-10 pass could not
support a per-tier estimate: it was drawn from the *pooled* table, Washington only,
unstratified (130/13/4/3 across the four tiers), and unblinded. Its per-record verdicts were
also not retained — deliberately, since the rating sheet pairs voter names with donor
names and the project's rule is that no individual-level row is kept where it could be
committed. That is defensible PII hygiene, but it does mean the pass cannot be re-scored, so
its ≈90% stands as a single unstratified indication rather than an auditable estimate. A
list regenerated later reproduces 15 flags in 150 (90.0%) with spousal notes on most of
them, consistent with what was reported, but a reconstruction cannot substitute for a
preserved artifact. It has been replaced by a stratified blinded re-rating
(`diag_match_validation_stratified.py`, scored by `score_match_validation.py`), and the
result changes what the paper should treat as its primary specification.

**Protocol.** 480 matched voter-donor records, allocated **20 to each of the 24
state × panel × tier cells**, and within each cell split 10/10 between the top decile of
matched dollars and deciles 2–10 (top-decile errors matter most, since they drive the
concentration finding). Sampling is deterministic (seeded md5). The rater's file carries
**no stratum labels at all** — no state, no panel, no tier, no decile — and rows are
shuffled before opaque ids are assigned, so no cell can be identified or treated
differently; labels live in a separate key joined only after every verdict was recorded.
The scoring script was written *before* the verdicts, so the analysis was fixed in
advance. Verdicts are published, PII-free, at
[`reference/match_validation_verdicts_2026-07-27.csv`](reference/match_validation_verdicts_2026-07-27.csv).

**Result — precision is entirely a function of match tier.**

| tier | share of matches | n | Y | NC | NP | U | precision | Wilson 95% CI |
|---|--:|--:|--:|--:|--:|--:|--:|---|
| `STRICT_ZIP5_FULL` | 81–89% | 120 | 120 | 0 | 0 | 0 | **100.0%** | [96.9–100.0] |
| `STRICT_ZIP5_MID` | 0.4–2% | 120 | 86 | 33 | 1 | 0 | 71.7% | [63.0–79.0] |
| `STRICT_ZIP5` | 9–13% | 120 | 57 | 61 | 1 | 1 | **47.9%** | [39.1–56.8] |
| `RELAXED_ZIP3_MID` | 0.3–5% | 120 | 60 | 58 | 1 | 1 | **50.4%** | [41.6–59.2] |

*Y = same person; NC = confirmed different person; NP = probably different;
U = indeterminate. `precision` = Y/(Y+NC+NP); the sensitivity bound treating every
U as an error moves each tier by ≤0.5 points, because only 2 of 480 records were
indeterminate.*

The full-name key is clean and the initial-based keys are close to coin flips. Requiring
the complete first name, the surname, the ZIP5 and roll-uniqueness leaves essentially no
room for error; dropping to a first initial does not.

**Population-weighted precision, per panel.** The sample deliberately oversamples the weak
tiers by 30–300×, so its raw mean (67.6%) is *not* a panel estimate. Reweighting each
tier's precision by that tier's actual share of the panel:

| panel | matched donors | weighted precision | bound (all U wrong) |
|---|--:|--:|--:|
| WA federal | 172,998 | **93.3%** | 93.3% |
| WA state | 268,741 | 90.4% | 90.4% |
| NY federal | 307,841 | 93.1% | 93.1% |
| NY state | 424,020 | 94.3% | 94.1% |
| ID federal | 27,196 | 92.6% | 92.6% |
| ID state | 27,250 | 96.5% | 96.5% |
| **donor-weighted, all six** | | **93.0%** | **92.9%** |

So the ≈90% figure the earlier pass reported was, at the panel level, roughly right — and
slightly conservative. But it concealed the structure that matters: **all of the error sits
in the ~11–19% of matches made on a first initial**, and none of it in the full-name tier.

**By dollar band, precision is *lower* at the top.** 63.0% in the top decile of matched
dollars against 72.1% in deciles 2–10 (raw sample, tier-confounded). The gap runs the
direction the reviewer worried about — false matches are commoner among the largest
attributed totals — which is a further reason to prefer the full-name specification, where
the top decile is also 100%.

**Three distinct error modes, separately identified.** Of the 152 confirmed false matches:

| error mode | n | where it occurs |
|---|--:|---|
| different person, shared surname + ZIP (household / relative) | 129 | initial-based tiers only — 57 `STRICT_ZIP5`, 43 `RELAXED_ZIP3_MID`, 29 `STRICT_ZIP5_MID`; **zero** in the full-name tier |
| an **organisation** parsed as a person | 14 | **Idaho Sunshine state panel only**, all in the two middle-initial tiers |
| **name-order parse failure** ("First Middle Last" read as "Last First") | 9 | **WA PDC state panel only** |

The two panel-specific modes follow from file format. Sunshine and PDC file people without
a comma, so the matcher takes the first token as the surname; a committee, LLC or trust
name then parses as a person (`WEST ADA … REPUBLICAN CLUB` → surname `WEST`, first name
`ADA`), and a record genuinely filed first-name-first matches the wrong voter. At
population scale — and now measured from Idaho's own `Contributor Type` field rather than
from name shapes — organisations and committees are **8.1% of Idaho Sunshine rows but 53.9%
of its dollars** ($28.70M of $53.26M). That is well above the 32.6% a name heuristic had
estimated, and it is consistent with Appendix G's all-filer vs persons-only gap for the
Idaho state layer. The equivalent name-order figure for WA PDC is 1.85% of comma-less rows
/ 2.08% of its dollars.

**What follows for the paper.** On this evidence the **full-first-name tier should be the
primary specification**: it carries 81–89% of every panel, has no detectable false match in
120 blinded records, and — per the tier-sensitivity table above — moves every headline
finding *away* from the null rather than toward it (65+ share rises in all six panels, the
Democratic skew rises in all four party panels, concentration moves ≤1.3 points). The
all-tier figures reported throughout this paper are therefore the **conservative** ones,
and restricting to the clean tier would strengthen every claim while raising precision to
≈100%. Two limitations on that recommendation are stated rather than buried: it discards
11–19% of matched donors, and it does not fix the Idaho organisation contamination for the
two middle-initial tiers, which needs a person/organisation filter on the Sunshine loader
independently.

**What this design cannot detect.** The rating catches "the donor is a different person
*with a different name*". It cannot catch a true namesake — a different person with the
*same* full first name, surname and ZIP5 — so the full-name tier's 100% is a ceiling on
detectable error, not proof of zero error. The complementary population measure is the
donor-side collision rate above (7–9% of full-name-tier matches sit on a key that also
pulls a different first name). A separate 8 records were flagged **partial merges**: the
matched voter genuinely is a donor, but the attributed total also includes a relative's
gift or a jointly-filed one. Those count as correct for identity — and therefore for the
age, party and composition findings — but they inflate that individual's dollar total,
which is the concentration-relevant residue.

**Who adjudicated, and the independent human re-rating.** The 480-record pass was
adjudicated by the AI assistant under the blinding protocol above. It is seeded, published
and pre-specified, but it is a single-rater pass by the same system that produced the
analysis, so an **independent human rater** re-rated a stratified subsample.

*Protocol.* 150 of the 480 records, drawn to put **75 on the full-name key** " — the block
the primary specification rests on " — and 25 on each initial-based key, with all 8
partial-merge and all 5 NP/U judgment calls forced in and every state-and-panel represented.
The human saw **fresh opaque ids**, not the published `S####` ids, so the AI's answer could
not be looked up; no stratum label, no AI verdict; and evidence rows copied verbatim from
the AI's file, so a divergence is a difference in judgement and never in what was shown.
The scorer was committed before any rating. Verdicts published at
[`reference/match_validation_human_verdicts_2026-07-27.csv`](reference/match_validation_human_verdicts_2026-07-27.csv).

*Result on the primary specification: it holds.* **75 of 75 full-name-key records were rated
Y by the human**, Wilson 95% [95.1" –100.0], in perfect agreement with the AI pass. Zero
divergences in that block.

*Agreement overall.*

| scale | n | observed | Cohen's kappa | PABAK |
|---|--:|--:|--:|--:|
| four categories | 150 | 88.0% | 0.656 | 0.760 |
| collapsed binary (Y vs not) | 148 | 93.9% | **0.815** | 0.878 |
| " — full-name key alone | 75 | **100.0%** | n/a (no variance) | 1.000 |
| " — initial-based keys | 75 | 68" –80% | 0.457" –0.638 | 0.360" –0.600 |

Kappa is undefined on the full-name block because both raters returned all-Y " — zero
variance, not zero agreement. That is exactly the prevalence artifact PABAK is reported for,
and PABAK there is 1.000.

*Every divergence runs in one direction.* All 18 disagreements are on initial-based keys,
and in **every** one the human was the more permissive rater: 6 NC" → Y, 7 NC" → NP,
3 NP" → Y, 2 U" → Y, and **zero** cases where the human called a record worse than the
AI did. The AI never rated Y a record the human rejected. Two consequences follow. The
full-name key's 100% is confirmed from both directions rather than merely reproduced. And on
the weak tiers the AI's figures are the **conservative** ones: reweighted on the same frozen
shares, the human's donor-weighted precision is **95.7%** against the AI's 93.0%, and
per-tier the human reads 64" –68% where the AI read 47.9" –71.7%. The qualitative
finding " — initial-based keys are far less reliable than the full-name key " — is robust
across raters; the exact weak-tier rates are not, and should be read as a range.

*Two limitations, stated.* The human rated 150 of the 480, so 345 records carry a single
rating; the 75 full-name rows are a subset of the AI's 120 rather than an addition, so the
block stands at 120 rated with 75 independently confirmed and no disagreement. And the
human ticked `partial_merge` on 1 record against the AI's 8 " — almost certainly under-use
of an unfamiliar column rather than substantive disagreement, but it means the
partial-merge count rests on the AI pass alone.

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

**Current-roll survivorship, and why its direction is not assignable.** All three matches
run against the current roll, and two mechanisms push the observed age distribution in
*opposite* directions. A donor who moved between giving and the extract date fails the ZIP
match, and mobility skews young — deflating the young donor share. But over a contribution
window reaching back to 2017, older donors are also more likely to have died or been
removed from the roll — deflating the old donor share. Earlier drafts called the raw age
skew an "upper bound" on this basis; that assigned a direction the evidence does not
support. Without a historical-roll or address-history analysis the net sign is unknown, so
the skew is described here as potentially biased by current-roll survivorship in an
undetermined direction. What remains ruled out is the specific mechanism objection 1
names — that rare names make the old easier to match — which the flat P(matchable) above
addresses.

## Appendix G — Contribution limits and the top of the distribution

Earlier drafts of Finding 2 explained Idaho's lower matched top-1% share by asserting that
state contribution limits "compress the very top of the state-money distribution." This
appendix tests the mechanical version of that claim (`diag_contribution_limits.py`) and
reports what replaces it. The conclusion is narrower than earlier drafts stated, and the
narrowing is set out at the end.

The test does not require new data. Idaho residents appear in **two money systems at
once**, under two different rule sets, so the regime can be varied while holding the donor
population approximately fixed. Washington supplies the same pair. (Approximately, not
exactly: the two panels overlap by a Jaccard coefficient of only 0.14–0.16, per Appendix
C — a limitation on this design that earlier drafts did not state.)

**G1 — the statutory regimes.** Individual contributions to a candidate, per election,
2025–26 cycle:

| layer | legislative | statewide | ceiling on a donor's *total* giving |
|---|---|---|---|
| Idaho state (Sunshine) | **$1,000** | **$5,000** | none |
| Washington state (PDC) | **$1,200** | **$2,400** (state exec.) | none |
| New York state (BOE) | **$3,000** Assembly / **$5,000** Senate | **$9,000** | none |
| Texas state (TEC) | **no dollar limit** | **no dollar limit** | none |
| Federal (FEC) | **$3,500** | $3,500 | none since 2014 |

Note the direction of the caps: Idaho's and Washington's legislative limits are *lower*
than the federal per-election limit, but **no** system caps a donor's total, the federal
aggregate ceiling having been struck in *McCutcheon v. FEC*, 572 U.S. 185 (2014). Idaho
and Texas also permit direct corporate and PAC contributions to candidates, which federal
law forbids, and Idaho caps nothing at all on ballot-measure committees. Statutes and
authorities in Appendix D.

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
*state* layer is **more** top-heavy than the *federal* layer — Idaho 39.7% vs 36.1% among
persons, and 56.4% vs 36.1% with committees included; Washington 44.4% vs 39.3%. Second,
the persons-only Idaho state figure (39.7%, Gini 0.800) sits close to Finding 2's matched
**40.0% / 0.799**, a reasonable check that these layer definitions match the paper's. The
two are no longer expected to coincide exactly: this appendix's layer cut spans every
itemized filer, while the matched panel is now restricted to the full-first-name key.
Restricting the Idaho federal layer to Sunshine's 2023–2025 window leaves the direction
intact (matched federal aligned top-1% **34.7%** against state **40.0%**).

**G4 — what a per-gift cap would do, mechanically.** Trimming every gift in Washington's
federal layer to Idaho's caps isolates pure truncation, holding the donor population and
every other behavior fixed:

| per-gift cap | top 1% | top 10% | $ retained |
|---|--:|--:|--:|
| uncapped (actual) | 39.3% | 72.3% | $646M |
| $5,000 (ID statewide cap) | 32.2% | 68.7% | $571M |
| $3,500 (federal limit) | 31.2% | 67.7% | $554M |
| $1,000 (ID legislative cap) | **26.4%** | 62.9% | $454M |

So mechanical truncation is *not* a small effect: an Idaho-style legislative cap applied
to an unchanged transaction file would cut the top-1% share by 12.9 points. That sharpens
the puzzle rather than resolving it. Idaho's actually-capped state layer sits at 39.7%,
**13.3 points above** what pure truncation predicts.

**What replaces the original explanation.** The cap binds at the moment of the gift, and
its compression is then undone downstream. Nothing limits a donor's *total*, so the same
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
(Appendix E). Idaho's flatter distribution is better read as a property of its small,
retail donor base than of its state caps.

**What this design supports, stated narrowly.** The defensible conclusion is that **simple
mechanical per-gift truncation does not reproduce the observed ordering of the state and
federal concentration estimates.** G4 varies a per-gift ceiling on an unchanged
transaction file; it therefore identifies the mechanical channel only. Real contribution
limits also change how many recipients a donor gives to, when, through which vehicle, and
in what amounts, and none of that is held fixed in the world G4 simulates. The stronger
claim in earlier drafts — that "contribution caps do not explain the cross-state
differences" — is more than the design supports and is withdrawn.

**Caveats.** The Sunshine layer covers 2023–2025 while the federal layers cover 2017–2026,
so the unwindowed rows above are not period-aligned; the aligned matched-panel comparison
is reported in Appendix C and leaves every direction intact. Separating people from
organizations relies on a name heuristic, and the two state files differ: Idaho Sunshine
files people as "LAST, FIRST", so a comma test works, whereas Washington PDC files them as
"LAST FIRST", so no reliable persons-only cut is available for the WA state layer and its
all-filer row is the one to read. PDC's "SMALL CONTRIBUTIONS" unitemized pseudo-contributor
is excluded from all Washington state cuts; left in, it keys as a single enormous donor and
inflates every figure. The FEC files are persons by construction, which is why their two
cuts nearly coincide — itself a check that the heuristic is not driving the result. The
layers also carry different disclosure floors (Appendix C), so the state layers include
smaller gifts than the federal ones, which pushes their measured concentration down rather
than up and therefore cuts against G3's finding rather than producing it. No causal claim
is made about what caps do to a donor pool.

## End note — data, reproduction, and series

Reproduction, in dependency order. Each match script builds ONE panel per run, selected
with `--source`; the two panels are written to `voter_donor_affiliation_fec` and
`voter_donor_affiliation_state` and are never pooled (Appendix C).

```
# Washington — both panels:
python scripts/match_wa_voters_to_donors.py --source fec
python scripts/match_wa_voters_to_donors.py --source state
python scripts/diag_wa_individual_findings.py

# New York — both panels:
python scripts/load_ny_voters.py                  # NYSVOTER FOIL -> ny_vrdb.duckdb
python scripts/diag_ny_turnout_party.py --rebuild # voter_participation table
python scripts/backfill_ny_committee_party.py     # bulk FEC committee/candidate party -> 87.8%
python scripts/load_ny_contributions.py           # NYSBOE per-contribution rows (state layer)
python scripts/backfill_ny_recipient_party.py     # state recipient party -> 37.7%
STATE=NY python scripts/match_ny_voters_to_donors.py --source fec
STATE=NY python scripts/match_ny_voters_to_donors.py --source state
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

# Review-response recomputations: denominators, crossover labels + MIXED + dollar flow,
# match-tier and household sensitivities, panel overlap, Idaho composition shares.
python scripts/diag_donor_class_revisions.py
python scripts/diag_donor_class_revisions.py --build-aligned   # period-aligned ID panels

# Match-precision validation (Appendix F). The sampler writes a BLINDED evidence file
# (no state / panel / tier / decile) plus a separate stratum key; the scorer joins them
# only after verdicts are recorded. Both files are PII-bearing and gitignored; the
# verdicts alone are published at docs/reference/match_validation_verdicts_2026-07-27.csv.
python scripts/diag_match_validation_stratified.py     # 480 records, 20 per stratum
python scripts/score_match_validation.py               # per-tier precision + reweighting

# Independent re-derivation of Findings 1-4 across both panels of all three states
# (from-scratch SQL, imports no analysis code):
python scripts/verify_donor_class.py
```

The verifier reaches the databases directly and imports no analysis code, so it re-derives
the aggregates independently of the build path. Rebuilding the panel tables from raw voter
files is covered separately, by the extracted matcher the release ships as
`scripts/donor_matcher.py`:

```bash
# Rebuild a panel from the raw inputs (needs the voter file ATTACHable as vrdb).
# --tiers full is the default and is the primary specification; --tiers all reproduces
# the superseded all-tier specification.
python scripts/match_id_voters_to_donors.py --source fec --tiers full
```

Two cautions for a replicator. `--tiers` restricts which tier joins fire, so a
contribution reachable only by a weaker key is dropped; filtering an all-tier panel on
`match_quality` instead keeps a full-name donor's entire dollar total. The two give
identical donor counts but dollar totals differing by 3.8–9.4% (Appendix F6), so a figure
must not be moved between them. And the ranks are absolute: renumbering them for a
restricted call would label a `RELAXED_ZIP3_MID` panel `STRICT_ZIP5_FULL`.

All inputs are public records (FEC bulk files; Idaho Sunshine, Washington PDC and NYSBOE
filings; state voter files obtained under each state's lawful-use terms — NY NYSVOTER
FOIL, WA VRDB, ID SoS statewide list under Idaho Code § 34-437A(3)). See
[`data-sources-and-reproducibility.md`](data-sources-and-reproducibility.md) for the full
source ledger and the matcher/competitiveness method notes, and
[`publication-checklist.md`](publication-checklist.md) for the verification ledger of
expected values and the outstanding pre-submission items (tagged release + archival DOI;
stratified match-precision re-rating).

This is Paper #3 of the electoral-health series:
[`who-decides-washington.md`](who-decides-washington.md) (the gray off-year electorate),
[`who-decides-new-york.md`](who-decides-new-york.md) and
[`who-decides-idaho.md`](who-decides-idaho.md) (party-resolved electorates),
[`safe-seat-washington.md`](safe-seat-washington.md) (observed competitiveness), and
[`cross-state-fec-money.md`](cross-state-fec-money.md) (the four-state money layer).
