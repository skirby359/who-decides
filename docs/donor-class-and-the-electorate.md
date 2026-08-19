# Who Gives? The Donor Class and the Registered Electorate in Washington, New York, and Idaho

*"Electorate" throughout means the **registered electorate** — see the definition in
"The question".*

**Stephen Kirby** · Tikor Consulting · July 2026 · <kirby@tikorconsulting.com>

*AI-assistance disclosure.* Anthropic's Claude was used throughout: drafting and editing prose;
generating, modifying and reviewing analysis code, including the SQL producing the published
figures and the verification script that re-derives them; checking citations and statutory
references; and proposing robustness analyses, several of which were adopted. This is AI use
affecting methods, analysis and code, not only language. AI was not an author and did not adjudicate any
match-validation record. **Every verdict in the match-precision validation is a human's and
none was AI-assisted**: the author's on the original pass and the blind re-rate, an independent
rater's on the third pass and the 204-record Idaho sample; the match itself is
deterministic local code.
Verdicts are published at row level and both passes and their divergences are reported
(Appendix F). Assistance operated on code, schemas, aggregate outputs and prose. Person-level data
handling — what the architecture keeps out of a hosted service, where that has rested on practice
rather than enforcement, and one 2026 instance in which an operational command echoed voter rows
into an assisted session — is documented in the project's data-use and research-ethics assessment.
The author independently verified all sources, code and outputs and is solely responsible for
the content and conclusions.*

*Data and code availability.* Paper source, analysis code, and the data-acquisition recipe are
at <https://github.com/skirby359/who-decides>. All inputs are public records — FEC bulk files;
Idaho Sunshine, Washington PDC and New York State Board of Elections filings; and the three
state voter files, obtained under each state's lawful-use terms. The voter files are not
redistributable and are not included. `scripts/verify_donor_class.py` independently re-derives
the designated results below from the built panel tables and runs a numeric coverage audit over
them; a small number of expressly identified tables that depend on specialised
person/organisation classification logic are reproduced by their originating diagnostic scripts
rather than reimplemented, and the supplement names them. The panels themselves are rebuildable
from the raw inputs by an authorised user who independently obtains the restricted voter files
and follows the full dependency-ordered recipe — `scripts/donor_matcher.py` is the
record-linkage stage of that, not the whole of it. Provenance per figure, the
reproduction recipe, and a ledger of claims withdrawn during review are in the companion
[methods and provenance supplement](donor-class-methods-supplement.md). *Before submission this
paper must cite a tagged release and archival DOI rather than a mutable branch.*

*Two panels, read this first.* American donors give into two separately regulated money
systems, and a voter roll can be matched to either. Every result below is therefore computed
**twice**, once per system, and never pooled:

| panel | what it is | matched donors | mandatory itemization trigger |
|---|---|--:|---|
| **Federal** *(primary)* | FEC itemized individual contributions | WA 147,745 · NY 269,218 · ID 23,303 | aggregate **> $200** |
| **State** *(secondary)* | WA Public Disclosure Commission · NY State Board of Elections · Idaho Sunshine | WA 217,114 · NY 378,383 · ID 23,613 | WA **> $25**, **> $100** from Apr. 2023 · NY **> $99** · ID **> $50** |

Pooling the two inflates measured concentration, because one person's federal and state giving
stacks into a single donor total while a one-system donor's does not. On Washington's data, and
on the primary match specification throughout, pooling reads top-1% **46.6%** against **41.2%**
federal and **43.5%** state — a 3.1-point overstatement against the higher of the two panels it
is built from. All three figures are on the same specification; mixing specifications between a
pooled and a single-panel figure is itself an error, and the retired all-tier trio (47.7 / 42.4 /
43.8) appears only in Appendix F, where it is labelled.

*What the panel split does and does not establish.* Where an outcome is observable it is
estimated separately in both panels, and the principal directional patterns — older than the
registered electorate, dollars concentrated at the top, geographically concentrated, coincident with high turnout,
and (where party is observable) tilted toward registered Democrats and against the
unaffiliated — the New York party result robust to detectable match error under both validation
bounds, the Idaho one resting on the per-stratum bound its independent 204-record validation
supports — recur in every state-and-panel combination in which they can be
measured. That is within-state repetition across two separately administered disclosure
systems, not independent replication. Party is **not** observable in Washington, and Idaho's turnout figures are reported
as composition rather than rates, so no claim here is that every finding is measured in every
cell.

The differences *between* the panels are informative but are **descriptive differences between
two datasets**, not identified effects of federal versus state regulation. Four confounds run
alongside the regulatory one, each quantified: the panels have different
disclosure triggers (a $50 Idaho floor reaches far deeper into small-dollar giving than a
$200 federal floor), they can cover different years (Idaho Sunshine holds 2023–2025 against a
2017–2026 federal layer), they are largely **different people** — the federal and state
matched sets overlap by a Jaccard coefficient of only 0.14–0.16 in all three states — and the
linkage reaches them unequally, resolving 39.1% to 56.9% of resident contributor keys depending
on the panel. With that
stated, the most robust panel difference is that federal money is older money: New York's
federal donors are 49.9% over 65 against 39.3% of its state donors, Idaho's 66.8% against
51.3%, and Washington's Silent Generation multiplier runs 2.58× federal against 1.66× state.
In Idaho, the one state where the windows differ, restricting both panels to the shared
2023–2025 window **widens** the gap to 68.5% against 51.3%, so period misalignment is not what
produces it.

## Abstract

Campaign money is usually described by how much is raised; this paper asks whose it is. Three
state voter files — Washington, New York and Idaho, the last two with party of record —
are linked person by person to itemized contributions. The baseline is the
**registered electorate**: each state's active roll, not the voting-eligible population.
Donors give into two separately regulated systems, so every
result is computed twice, federal and state, never pooled.
Matched donors are much older than the roll: 49.9% of New York's federal donors and 66.8% of
Idaho's are 65 or older, against 25.3% and 31.0% of registrants. Matched dollars
are concentrated: the top 1% of donors supply 41.2% of federal dollars in Washington, 50.7% in
New York and 37.2% in Idaho. Where party of record is published, registered Democrats are over-represented and
unaffiliated registrants under-represented relative to registration in both deep-blue New York
and deep-red Idaho. Both persist after adjustment for the roll's joint age and county
distribution, and are not explained by roll-side strict-key matchability (about one
point across parties). **New York's party result survives both validation bounds. Idaho's
survives the design-respecting cell bound — an independent 204-record rating detected no false
match, 95% upper bound 18.4% per party × dollar-band cell — but not the panel-wide
construction.**
Matched donors vote more often than non-donors — in New York and Washington, by 23 to 26
points among registrants eligible for every election in the window, age-standardized; Idaho
is composition-only. A blinded 480-record rating
found precision differs sharply by match tier; the paper uses only the tier with
no detected false match — **the same 75 records read correct in all three ratings, one
independent** — which narrows the donor population as it sharpens it. All findings describe
itemized, matched donors; every association is descriptive.

**Keywords:** campaign finance; political donors; voter files; record linkage; party of
record; contribution limits; donor concentration; Washington; New York; Idaho.

---

## The question

Campaign money is usually described by *how much* is raised. The more
consequential question for representation is *whose* money it is — and whether
the people who fund elections look anything like the people who vote in them. If
the donor class is a representative cross-section of the electorate, money is
just amplified participation. If it is a narrow, self-selected slice, then a
distinct population supplies the money that campaigns run on, before the
first ballot is cast. What that buys is a separate question this paper does not
reach; who supplies it is the question here.

**What "electorate" means here.** The comparison baseline throughout is the **registered
electorate** — each state's active registration roll — with supplementary comparisons to
2024 general-election voters where participation is observable. It is never the
voting-eligible population, the census population, or the electorate of a particular
future contest. Nothing below establishes that donors differ from every conception of the
electorate; the claim is the narrower and measurable one, that matched itemized donors are
not representative of the registered electorate.

This question can be answered at the individual level in three states, by matching the
registered-voter roll to itemized donors, person by person (a conservative name + ZIP
match in four tiers; see Appendix C). Washington supplies the demographic and behavioral
cut; **New York and Idaho — which, unlike Washington, publish each voter's party — supply
the dimension WA cannot: who the donor class is *partisan*-ly, and where its money goes.**
And they bracket the political spectrum: New York is ~48% registered Democratic, Idaho
~63% registered Republican.

The short answer, consistent across all three states: **matched itemized donors are not
representative of the registered electorate.** They are substantially older, financially and geographically concentrated in a
small top tier, and — where party is observable — tilted toward registered Democrats while
substantially under-representing the largest non-partisan bloc. The notable part is that
the Democratic tilt of the donor class relative to registration appears in deep-blue New
York **and in deep-red Idaho**: it is not mechanically attributable to which party holds
the statewide registration plurality. The New York result survives both error bounds the
validation supports; **Idaho's rests on a per-stratum bound from a second,
independent rating** — 204 records, no false match detected, 95% upper bound 18.4% at the
design's party × dollar-band cells — and not
on the panel-wide construction, which it fails. Both are set out in Appendix F §F7.

---

## Prior work, and what this paper adds

That the donor class is small, affluent and unrepresentative is well established, and nothing
below claims to discover it. What the existing record leaves thin is *who* that class is at the
level of the individual person, measured against the population a state actually registers.
Three literatures set the baseline.

**The shape of the donorate.** Bonica (2014) made contributor ideology estimable at scale and
established donors as a distinct population rather than a cross-section of voters; Bonica,
McCarty, Poole and Rosenthal (2013) documented how steeply giving concentrates at the top and
tied it to the broader inequality literature. Schlozman, Verba and Brady (2012), following Verba,
Schlozman and Brady (1995), established money as the most unequally distributed form of political
participation and the one least corrected by mobilization. Gilens (2012) and Gilens and Page
(2014) supply the normative stakes — why the composition of a funding population is a question
about representation and not only about campaigns. Hill and Huber (2017) is the closest
methodological antecedent to this paper: they merge survey respondents to contribution records
and find donors older, wealthier, better educated and more ideologically extreme than non-donors.
Grumbach and Sahn (2020) and Grumbach, Sahn and Staszak (2022) extend the composition question to
race and gender.

**What those designs cannot observe, and this one can.** They divide along a familiar tradeoff.
Survey-linked designs see rich attributes on a sample; administrative-linkage designs see thin
attributes on a population. DIME-style work *infers* an ideological position from the pattern of
a person's giving. That is a productive measure for many questions, but it is not an independent
measure of political affiliation for *this* one: the giving supplies both the behaviour under
study and the yardstick applied to it.
Composition-by-group work must impute race and gender from names and geography, a genuine
measurement problem with its own error. And most of this literature is federal, because the FEC
bulk files are the accessible universe. The studies reviewed here generally do not compare
donors' **observed party of registration** against the registration population itself, on the
same roll that defines the comparison.

**Why observed party of registration is the pivot here.** A registration is not an ideal point
and not an inference; it is an administrative fact the voter supplied and the state published,
available for every registrant rather than for a matched sample. It makes the comparison a
like-for-like one — the donor's recorded party against the recorded party of the electorate they
are drawn from. The advantage over an inferred ideal point is specific, and it is not that one is
falsifiable and the other is not: it is that the measure of the political characteristic under
analysis is not itself derived from contribution behaviour.
Its limits are equally concrete and are carried throughout: it is measured at the extract date
rather than at the time of the gift, and it is a registration rather than a vote or a belief.

**Why federal and state panels are built separately.** American donors give into two separately
regulated systems, and the literature on what regulation does to a donor pool — Barber (2016) on
contribution limits and legislative polarization, La Raja and Schaffner (2015) on limits and
party organizations — is largely about *state* variation, while donor composition is usually
measured *federally*. Pooling the two is not merely untidy. One person's federal and state giving
stacks into a single donor total while a one-system donor's does not, which mechanically inflates
every concentration statistic computed over the result. Building the panels separately is what
lets the same outcome be estimated twice, and what keeps the pooling error out of the estimates.

**Where the linkage sits.** The design is deliberately not the field standard. Fellegi and Sunter
(1969) formalised linkage probabilistically and Enamorado, Fifield and Imai (2019) supply the
current political-science implementation — demonstrated, as it happens, on exactly this problem.
This paper uses a deterministic key with a uniqueness requirement instead, which trades reach for
specificity and moves the uncertainty out of the estimator and into the sample definition. That
choice is defended by direct validation rather than by equivalence, and its cost is quantified
rather than conceded; Appendix D develops the comparison, including Bailey et al.'s (2020)
finding that link error in common algorithms is both large and systematic.

**The contribution, stated narrowly.** A validated record-linkage measurement design comparing
the composition of itemized federal and state donor populations against registered-electorate
baselines in three states, with observed party of record in two. Four things carry it: the
linkage is validated as an instrument rather than asserted, with precision resolved by match key
against a blinded sample, a blinded author re-rate and an independent rater; the two-panel construction prevents a
pooling error that would otherwise arise in this design; the instrument's **operational match
rate is measured and its detectable error estimated and bounded**, rather than acknowledged and
left there — true linkage error is not fully measured, and where the bound is wide the paper says
so; and the party comparison runs in a deep-blue and a deep-red state at once, which is what
separates a finding about donors from a finding about whichever party happens to hold a
registration plurality — securely in New York, and in Idaho on the per-stratum bound
established by the independent rating in Appendix F §F7.

---

## Data, linkage, and validation

The measurement instrument is the record-linkage and panel-construction procedure, so it is
described before the results rather
than after them. Full construction detail, the per-source coverage tests and the complete
validation tables are in Appendices C and F; what follows is what a reader needs in order to
know what the findings are estimates *of*.

**Three populations, kept distinct.** The **registered electorate** is each state's **active**
registration roll — Washington 5.10M, New York 12.45M, Idaho 1.03M — and it is the baseline
for every comparison, in all three states and every cut, without exception (`status_code='A'`;
Idaho's export publishes no status flag, so its roll is active by construction). The companion
Washington papers in this series read against a wider **5.46M** roll that retains **412,361**
inactive registrants; that convention is *not* used here, and Appendix C carries the crosswalk,
because a lead paper should not make a reader reconcile two denominators.
**2024 general-election voters** are a second,
narrower baseline, used where participation is observable. The analytical population is
**matched itemized donors**: contributors whose disclosed record links to exactly one
registrant. That is neither all contributors nor all donors. Giving below a disclosure trigger
need not be itemized at all, and the linkage drops every ambiguous record rather than guessing,
so the matched set is a **floor on identifiable donor–voter matches**. Every estimate below is
therefore a statement about itemized, successfully matched donors, and the word "donors" is
short for that throughout.

**Why these three states.** Washington supplies the demographic and behavioral cut — the
largest roll here paired with 27.1M individual vote records — but does not publish party of
record, so the partisan question cannot be asked there at all. New York and Idaho do publish
it, which is the whole reason they are in the design. They also bracket the spectrum: New York
is roughly 48% registered Democratic, Idaho roughly 63% registered Republican. **These three
states were selected purposively, on data availability and on whether the voter file publishes
party of record. They are not a sample of states**, so nothing here supports an inference to the
other forty-seven, and the two-state party result is a contrast between two cases rather than a
range. That bracketing is load-bearing rather than decorative. A donor class tilted toward registered Democrats in a
deep-blue state is consistent with the trivial explanation that the plurality party gives most;
the same tilt *relative to registration* in a state where Republicans outnumber Democrats better
than five to one is not. Texas appears once, in a statewide aggregate table that needs no voter
file, and nowhere in the linked results.

**Two panels, never pooled.** American donors give into two separately regulated systems, and a
roll can be matched to either. The **federal** panel is FEC itemized individual contributions,
mandatory itemization trigger above a $200 aggregate. The **state** panel is the Washington
Public Disclosure Commission, the New York State Board of Elections and Idaho Sunshine, with
triggers of $25 rising to $100 in April 2023, $99, and $50 respectively. The match runs **once
per source**, and no figure mixes them. Pooling is not merely untidy: one person's federal and
state giving stacks into a single donor total while a one-system donor's does not, which
mechanically inflates measured concentration — on Washington's data, top-1% reads 46.6% pooled
against 41.2% federal and 43.5% state.

What the two panels do and do not license is worth fixing early. They provide **within-state repetition across two separately administered disclosure
systems**, not independent replication: where an outcome is observable it is estimated twice,
and the principal directional patterns recur. The two estimates share a voter roll, a linkage
rule, some donors and every source-parsing limitation, so agreement between them is weaker
evidence than agreement between independent studies would be. They do **not** constitute a controlled comparison of federal against state regulation.
Four things differ between the panels besides the regulatory regime. The two matched sets overlap
by a Jaccard coefficient of only **0.14–0.16** — they are largely different people; the
disclosure triggers differ; the periods differ in Idaho; and, as the match-rate table in Appendix F shows,
**the linkage itself reaches the panels unequally**, from 39.1% to 56.9% of parsed resident
contributor keys. Differences *between* panels are therefore described as differences between two
constructed datasets, and the mechanism behind them is not identified.

**The linkage rule.** Matching is deterministic and proceeds in four tiers, strictest first, on
active registrants only. Every tier carries the same guard: the key must resolve to **exactly
one** voter on the roll and one donor identity, or the record is dropped rather than guessed.
No probabilistic score is assigned and no clerical review resolves near-misses, which is what
makes the matched set a floor and also what makes the tiers unequal:

| tier | key | share of matches |
|---|---|---|
| `STRICT_ZIP5_FULL` *(primary)* | surname + **full** first name + ZIP5 | 80.7–89.2% |
| `STRICT_ZIP5_MID` | surname + first initial + middle initial + ZIP5 | 0.4–2.0% |
| `STRICT_ZIP5` | surname + first initial + ZIP5 | 9.5–12.6% |
| `RELAXED_ZIP3_MID` | surname + first initial + middle initial + **ZIP3** | 0.3–5.0% |

**Where this design sits in the linkage literature.** The probabilistic standard and this paper's
departure from it are described under *Prior work* above; three consequences belong here. The
rule has **not** been calibrated against a probabilistic model, so what supports it is the direct
validation below rather than an equivalence argument. The rule produces **no record-level match probabilities that can be
propagated** through downstream estimates, so its observed error has to be evaluated by
validation and sensitivity analysis instead, and selection into the matched population treated
as a separate question. That is this design's most substantial methodological limitation, and it
does not mean false links are harmless: they are measurement error inside the estimands, bounded
here rather than carried through them. And the key is weaker than the address–DOB–gender–name benchmark of
Ansolabehere & Hersh (2017) by statute rather than by choice: the donor side of a contribution
filing carries no date of birth, no gender and no verified address, only a name and a ZIP.
Appendix D develops all of this, together with Bailey et al.'s (2020) finding that link errors in
common algorithms run 15–37% and are systematically related to record characteristics rather than
random — a result this paper reproduces twice, in which tiers its false merges landed on and in
who its clean-key restriction discards.

**Why the full-name tier alone is the specification.** A stratified blinded rating of **480**
matched records — 120 per tier, each rated without knowing which tier produced it — found that
**detected precision differed sharply by key in the validation sample**, rather than being a
property of the match as a whole.
`STRICT_ZIP5_FULL` returned **100.0%** with a 95% Wilson interval of **[96.9–100.0]**, against
**47.9–71.7%** for the three initial-based keys — substantially lower, with the weakest near
chance. Every one of the
129 household and relative false merges the rating found landed on an initial-based key and
none on the full-name key. The tiers are therefore not interchangeable, and treating the
matched set as one population would import roughly a coin-flip's error on the **11–19%** of
it those keys carry — the same share the restriction discards, below. Each
panel is built from the first tier alone; the superseded all-tier panels are retained and
reported alongside rather than discarded.

**What the validation establishes, and what it cannot.** "No false match detected in 120
records" bounds the error rate at roughly **3%** — the Wilson *upper* bound on the error rate,
equivalently a 96.9% lower bound on precision — and does **not**
establish that it is zero. A true namesake at the same ZIP5 cannot be reliably distinguished
using the fields available to this linkage, at any sample size, because there is no field left
to separate them. Precision is also reported
population-weighted per panel, since the sample deliberately oversamples the weak tiers by
30–300× and its raw mean is not a panel estimate. **No part of the adjudication was
AI-assisted**: the first two passes are the author's, the third an independent rater's. All
three passes are published at row level so they can be re-scored. The second was a **blinded author re-rate** of a subset, which makes its agreement
statistics **test–retest**; the third was an **independent rater** over the same subset
(2026-08-06), which supplies **inter-rater** reliability, and the two are reported separately
rather than pooled. The Idaho panels, where an independent reading mattered most, were rated in
the same round and returned **zero errors in 204 records** (below).

**Spending the error budget against each finding — on a common-rate assumption that is stated,
not assumed.** A bound that is stated but never applied is not much of a bound, so it is applied.
It is applied twice, because there are two defensible bounds and they differ by a factor of five.
Throughout this paper, every such figure is a **95% upper validation bound on *detectable* error
under this protocol**, not a logical ceiling on linkage error: an exact namesake who shares
surname, full first name and ZIP5 is invisible to human adjudication on these fields and lies
structurally outside every bound here.

The blinded sample allocates **20** full-name records to each of the six panels. Zero detected
errors in 20 bounds a *single panel's* error rate at **16.1%** — not 3.1%. The 3.1% figure is the
Wilson bound on the **pooled 120**, and it is a bound on a panel only if the six panels share one
strict-key error rate. That is a real assumption and the paper's own evidence does not fully
support it: linkage error here is systematic, and two panels carry source-specific parsing
defects. It is defensible on the primary key in particular, because both of those defects were
confined to the initial-based tiers this specification excludes. But it is an assumption, so
**the pooled figure is reported as a common-error-rate sensitivity and the panel-specific bound
beside it, never in place of it.**

The primary key eliminates the household-error mechanism **as it was observed**, within a
boundary worth stating: all 129 confirmed household or relative merges landed on an initial-based
key, and a merge on the primary key would need the same surname *and* full first name at the same
ZIP5, which the uniqueness guard drops rather than resolves **when both people appear distinctly
on the current active roll**. What that does not reach is a same-name relative who is inactive,
who has moved, or who is absent from the roll; a jointly reported gift; a misreported name; a
namesake who never registered. The residual is not empty — one **partial merge** was found on the
primary key in the 120 rated records, and a jointly filed gift needs no name difference to produce
one. So the residual is not necessarily a different mechanism, only one the guard cannot see; what
it cannot be is a merge between two people both distinctly on the active roll. Appendix F carries
the roll-collision measurements behind that argument and the full deletion table, computed at the
pooled 3.1% and again at the panel-specific 16.1%.

**The age finding survives both budgets; the Idaho party rows survive the panel-wide
construction only at the pooled budget, and that is stated rather than smoothed over.** At the
pooled 3.1% the 65+ share moves by 1.1 to 2.0
points against baselines 20 to 35 points below it, and the Democratic share by 1.1 to 2.5 points. At the
panel-specific 16.1% every 65+ row still clears its roll baseline — New York's federal donors read
40.2% against a roll of 25.3%, Idaho's 60.4% against 31.0% — and New York's party rows still clear
registration. **Idaho's do not**: 20.4% falls to 5.2% against an 11.8% registration share, and the
state panel likewise. What settles Idaho is the sample that question demanded, and it has now
been drawn *and rated*: an independent rater scored **204** fresh Idaho full-name records —
stratified on party precisely because the vulnerability is party-specific — and detected **zero
errors** in every stratum. On the per-stratum construction that rating supports, Idaho's
Democratic shares stay well above registration under adverse deletion (Appendix F §F7, which
also records the 2026-08-14 correction to the bound's arithmetic); under a panel-wide budget
they do not, and the paper keeps that asymmetry explicit: **New York clears every construction;
Idaho clears the per-stratum one its validation was designed to support.**

Turnout is omitted from the exercise because even a 16.1% deletion cannot close a 23-to-26-point
gap between groups of 269,218 and 12.2 million. Concentration is omitted for a different reason —
adversarial *removal* is degenerate for a top-share statistic, since deleting the largest donors
deletes the top-1% population by construction — and is stress-tested separately in Appendix F by
de-merging the largest donors into equal halves. The top-1% share falls by 6.1 to 8.3 points under
that stipulation, which leaves the finding that matched dollars are extremely top-heavy intact but
makes the *level* the least robust number in this paper. **Read it as a stress test, not as spent
error budget.**

**How far below the ceiling that floor sits.** A floor is only informative with a distance
attached, so the linkage's reach is reported rather than left to the word. Counting the distinct
**contributor keys** in each contribution layer on the primary specification's own key —
`(surname, full first name, ZIP5)`, parsed exactly as the matcher parses it — and the dollars
those keys gave. **These are parsed keys, not verified donor identities**, and the paper does not
call the result recall: one person can occupy several keys through spelling, name-order,
nickname or ZIP variation, two people can share one, and joint or household reporting can merge
two into one. What the table measures is the share of the keys a linkage could address that this
one resolved — an operational **strict-key match rate**. True recall would require knowing how
many real donor–voter correspondences sit among the unmatched records, which nothing here
observes. The per-panel cells are **Appendix F §F8**; the range is what matters here.

So the panels resolve **39.1–56.9%** of resident contributor keys, and **37.1–61.1%** of resident
itemized dollars are attached to a matched key. The dollar share exceeds the key share in four of
the six panels, the expected direction: the keys that fail to resolve are disproportionately
small givers.

**What the shortfall is, and what it is not.** A single match-rate figure invites the reading
that the rule discards half the donors it could reach. It does not. Every eligible resident key
falls into one of five states against the active roll, and several distinct specification choices
— full-name exactness, ZIP5 exactness, the restriction to active registrants, and the name parse
— each produce non-matches. Appendix F carries the full cascade per panel; the shape of it is
this. The **uniqueness guard costs 1.3–2.7%** of eligible resident keys: keys plausibly
corresponding to a registrant but dropped because the roll holds more than one candidate. A key
matching two or more registrants does not establish that the contributor is one of them, only
that the rule declines to choose. A further **1.0–2.3%** match a registrant whose status is not
active, a bucket Idaho's export cannot report.

**Among resident keys, geographic mismatch is the largest identified nonmatch category in most
panels.** A key whose surname *and* full first name do sit on the active roll, at a different
ZIP5, accounts for **13.8% to 26.8%** of eligible resident keys — the largest single bucket after
matching in four of the six panels, though not in the Washington or Idaho state panels, where the
unresolved residual is marginally larger. These records are consistent with mobility between the
gift and the extract, a work address on the filing, a stale address on either side, a second
residence, or an unrelated namesake, and **the available fields do not distinguish among those
explanations** — the bucket is defined by what matches, not by why it fails. Nor are they
"recoverable": they are candidates for a more permissive linkage model, which would trade this
rate against precision, and this paper declines that trade because the fourth match tier that
widens the radius to a ZIP3 measured 50.4% precision. Name-form differences, plausibly nicknames
against legal names, account for a further **4.9% to 12.4%** on the same caveat.

What is left — **15.4% to 26.7%** — has no counterpart on the roll under any of those
relaxations. That is **the residual not resolved by the specific deterministic relaxations tested
here**, and it should not be read as a fixed floor on what any name-and-ZIP linkage could reach:
it still contains materially different name forms the limited relaxation does not catch, parse
failures, incomplete roll records, donor identities split across several keys, and people
recoverable with other fields or a probabilistic model. The distinction that matters is that most
of the shortfall is a consequence of choices the specification makes and could in principle be
traded against precision, while this last column could not be, on these fields.

**Washington's state panel is the low outlier, the cause is a source-format defect, and it is now
measured rather than estimated.** The PDC files **99.9%** of its contributor names *without* a
comma, so the matcher reads the first token as the surname and mis-parses every filer who wrote
their name first-name-first. Rebuilding the primary key both ways against the active roll,
**7.2%** of comma-less PDC keys — 39,755 of **555,107**, carrying **8.4%** of their dollars
($27.0M) — resolve to exactly one active registrant *only* when the name is read
first-name-first, against a **0.18%** coincidence baseline measured on the comma-formatted FEC
layer where the true order is known. Accepting either order would lift this panel's strict-key
match rate from **39.1%** to **46.3%**, in line with the other state panels. The defect is
therefore a **coverage** defect of roughly seven points, and it supersedes the two smaller
estimates this paper previously carried.

*The two denominators reconcile exactly.* The match-rate table in Appendix F §F8 counts **555,922** eligible
resident keys in this layer; this diagnostic counts **555,107**. The difference is the
comma-bearing rows: 846 keys arise from them, 31 of which are also reachable from a comma-less
row, and 555,107 + 846 − 31 = 555,922. Both figures use the matcher's parse character for
character, with no whitespace normalisation, which is what makes them the same universe: an
earlier version of this diagnostic collapsed runs of internal space before splitting, which the
matcher does not do.

**The measured direction runs against the headline age finding, and that is the only outcome it
establishes.** The recoverable donors are *older* than those matched (46.8% aged 65+ against
39.0%), so a repaired parser would move this panel's headline 65+ share from 39.0% to **40.2%**.
The defect understates Finding 1 here rather than producing it. **No equivalent sensitivity was
computed for concentration, county geography, dollars per donor, or turnout**, so nothing here
licenses a general claim that the defect is harmless: for those outcomes the Washington state
panel remains secondary, and the direction of the coverage loss is simply unknown.

The parser is **not** repaired for this paper. Accepting reversed-order keys would add 39,755
matches drawn from a population the blinded validation never rated, and the 0.18% placebo shows
some would be coincidental namesakes; adopting them would require a fresh validation round on a
new specification. The Washington **state** panel is therefore reported as a
**coverage-compromised panel** — its match rate understated by about 7.2 points for an identified
and quantified reason — and read as a secondary, sensitivity panel wherever it appears. Appendix F
§F8 carries the table, the placebo and the two reproduction checks;
`diag_wa_pdc_name_order.py`, re-derived by `verify_donor_class.py`.

**What the restriction costs, stated rather than buried.** Restricting to the clean key
discards **11–19%** of matched donors, and the discarded set is **younger and less Democratic**
than the retained set. So part of the sharpening this specification produces is selection, not
measurement. Both directions are reported: the primary panels are the headline, the all-tier
panels sit beside them, and no figure is copied between specifications.

**What generalizes.** Within each state and panel where an outcome is observable, the direction
and approximate magnitude of the age, party and turnout gaps are the findings. Three things do
**not** generalize, and are not claimed. Levels are not a census of donors, for the coverage and
floor reasons above. Idaho's turnout figures are reported as **composition rather than rates**,
because current-roll denominators make rates unreliable there. And nothing here is causal:
donors are pre-selected for engagement, reverse causation is fully live on the turnout result,
and every association reported is descriptive.

---

## Finding 1 — The donor class is substantially older than the registered electorate

In all three states matched donors are far older than the registration and voting
baselines against which they are measured.

**New York** (`match_ny_voters_to_donors.py`) — age-band share. **Age is 2024 minus birth
year**, not age on a particular day, and the distinction is stated because it is not what an
earlier draft of this line implied. Washington's public file releases **year of birth only**
(RCW 29A.08.710), so a day-exact age was never available there; New York's day and month have
now been generalised as a data-minimisation control (Appendix B). The measure is therefore
uniform across all three states. It runs up to one year high for the **14.9%** of registrants
whose birthday falls after early November, and it does so on **both sides of every comparison**:
New York's roll 65+ share is 25.25% on this measure against 25.00% on completed age, its federal
donors 49.85% against 49.51%, so the donor–roll gap moves by **0.09 points**. No band boundary
or finding turns on it:

| age band | federal donors | state donors | all active voters | 2024 GE voters |
|---|--:|--:|--:|--:|
| 18–29 | **1.6%** | 3.9% | 18.0% | 14.1% |
| 30–44 | 13.0% | 17.2% | 25.5% | 23.1% |
| 45–64 | 35.5% | 39.6% | 31.2% | 34.6% |
| 65+ | **49.9%** | 39.3% | 25.3% | 28.2% |

*Source: `data/ny_statewide.duckdb` (`voter_donor_affiliation_fec` / `_state`) joined to
`data/ny_vrdb.duckdb`; NYSVOTER FOIL production **dated 2026-06-29**; FEC bulk individual
files and NYSBOE `4j2b-6a2j`, both 2017–2026; reference population = active registrants
(`status_code='A'`). Script: `match_ny_voters_to_donors.py`; re-derived by
`verify_donor_class.py`.*

Nearly **half of NY's federal donors are 65 or older**, versus a quarter of the active
roll; its state donors are younger but still tilted, at 39.3%. **Washington** shows the
same shape as generation multipliers (donor share ÷ roll share), and the skew is sharper
in federal money than in state:

| generation | federal panel | state panel |
|---|--:|--:|
| Silent | **2.58×** | 1.66× |
| Boomer | 1.96× | 1.52× |
| Gen X | 0.97× | 1.29× |
| Millennial | 0.36× | 0.63× |
| Gen Z | **0.04×** | 0.12× |

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
donors — against a third of the roll, with the under-30 share reduced to 0.5% and 2.1%
respectively. The donor class is substantially older than the registration baseline in
blue and red states alike.

**The panel gap, and what it is not.** In all three states, federal money is older money:
New York's 65+ donor share falls from 49.9% federal to 39.3% state, Idaho's from 66.8% to
51.3%, and Washington's state giving reaches Gen X and Millennials more readily than its
federal giving does (Gen X 1.29× vs 0.97×, Millennial 0.63× vs 0.36×). Three
alternative explanations were tested, and the gap survives the one that could be tested
directly while remaining exposed to the other two:

- **Period misalignment — ruled out.** Idaho is the only state whose two money systems
  cover different years (Sunshine 2023–2025 against a 2017–2026 federal layer). Rebuilding
  both panels on the shared 2023–2025 window (`diag_donor_class_revisions.py
  --build-aligned`) *widens* the gap: aligned federal 65+ is **68.5%** on 14,848 donors,
  against the state panel's 51.3%. New York's two layers cover exactly the same years;
  Washington's overlap substantially but are not identical — FEC 2017–2026 against PDC
  2016–2026, so the PDC layer carries one extra year at the front. Neither is the Idaho
  mismatch, which is a three-year window against a ten-year one.
- **Small-dollar reach — probed by a common donor-total restriction, which the gap
  survives.** The state panels itemize from a much lower floor ($50 in Idaho, $99 in New
  York, $25 then $100 in Washington) than the federal $200, so they reach deeper into
  small-dollar giving, which is younger. Restricting every panel to donors with **more than
  $200 in total observed giving** (`diag_panel_harmonized.py`) probes that, and it costs
  60–69% of each state panel against 26–27% of each federal one:

  | state | 65+ gap as built | restricted to > $200 total | change under the restriction |
  |---|--:|--:|--:|
  | WA | +16.6 pts | **+9.8** | 41% smaller |
  | NY | +10.6 pts | **+11.7** | the gap *widens* |
  | ID | +15.5 pts | **+12.2** | 21% smaller |

  So the direction survives in all three states — but **the Washington gap is 41% smaller
  under the common donor-total restriction**, so a reader comparing the raw WA panels is
  reading something other than a pure behavioral difference to that extent. Reported
  alongside the as-built figures rather than either alone. **What this restriction is not:**
  it does not isolate a statutory disclosure floor. See the note in Appendix C — it changes
  the analysis population to donors above a common observed total, and at least four
  mechanisms move together when it does.
- **Different people — not ruled out.** The two panels are not the same donors observed
  under two rule sets. They overlap by a Jaccard coefficient of 0.159 in WA, 0.161 in NY,
  and 0.141 in ID; only 23–34% of either panel appears in the other. A within-person read
  makes the point sharply: the 65+ share runs 32.9% among WA state-only donors, 53.6%
  among federal-only, and **59.6% among those in both** — the both-systems group sits
  *outside* the range spanned by the single-system groups, which a pure property of the
  regulatory layer would not produce. NY (34.4 / 47.3 / 55.0) and ID (46.0 / 66.5 / 67.6)
  behave the same way. Giving in more than one system is itself an age-graded behavior.

  **Two limits on that read, both from the common donor-total cut**
  (`diag_panel_harmonized.py`).
  First, note what a within-person design can and cannot do here: age is a property of the
  person, so for a donor present in both systems the federal and state values are *identical
  by construction*. There is no paired within-person test of an age difference to run — the
  comparison above is between groups of people, and the panel-level age gap is inherently a
  between-person comparison. Second, among donors above a common $200 observed total the
  pattern holds in Washington (38.4 / 54.7 / **58.9**) and New York (32.0 / 48.6 / **50.8**)
  but **not in Idaho**, where the both-systems group falls *inside* the range
  (48.5 / 66.3 / 63.9) on 2,805 donors. So "outside the range in all three states" is a
  property of the panels as built and does not hold on a common donor-total restriction;
  Idaho is the state where it fails.

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
dollars. **The "matched donors" column is not in every case the estimator's denominator.**
The estimator excludes donors whose net total is zero or below after refunds and
reattributions; in five of the six panels there are none, and in Washington's state panel
there are **382** (0.176%), so the concentration figures there run on **216,732** donors
rather than 217,114. Appendix E's interval table reports the positive-total count directly
for each panel. Windows: WA FEC 2017–2026 / PDC 2016–2026; NY FEC and NYSBOE both 2017–2026; ID
FEC 2017–2026 / Sunshine 2023–2025. These are **itemized** dollars only, from panels with
different disclosure floors (header table). Appendix C gives the full estimator
definition; Appendix E the bootstrap intervals. Scripts: the per-state match scripts;
re-derived by `verify_donor_class.py`.*

Two readings. The **point estimates** order New York > Washington > Idaho in both panels, and
that ordering matches the statewide all-donor figures. But the ordering is not stable under a
donor-level resampling exercise, which is reported here as a stability check rather than as
inference:

| pair | federal panel | state panel |
|---|---|---|
| NY − WA | **+9.50** pts [+6.30, +12.73] — consistently positive | +5.11 [−0.94, +10.93] — not |
| WA − ID | +4.03 [−3.03, +10.83] — not | +3.51 [−7.07, +13.83] — not |
| NY − ID | **+13.54** pts [+6.09, +20.05] — consistently positive | +8.62 [−0.68, +17.48] — not |

*B=1,000 draws per side, donors resampled with replacement within each panel independently;
`diag_donor_concentration_bootstrap.py`. **What this exercise is.** These panels are not
probability samples — subject to linkage and disclosure limits they are the whole constructed
panel for each state and window — so the difference between two of them is an exact
difference between two datasets, not an estimate with sampling error. The intervals therefore
measure one thing only: how much a difference moves when the donors composing it are
resampled, which is informative because the contribution distribution is extremely
heavy-tailed and a handful of donors can carry a top-1% share. They are **not** confidence
intervals for the study's actual sources of error — record-linkage mistakes, donors who could
not be matched, unitemized giving, current-roll survivorship, variation in disclosure
practice, and recipient-party classification are all outside them, and every one of those is
plausibly larger than the width shown. Interval width also tracks n: Idaho's 23K-donor panels
give a top-1% interval roughly 18 points wide against 5 for Washington's.*

So what the matched panels support is narrow: **New York's federal donors are more
concentrated than Washington's or Idaho's** — the only two gaps that stay positive across
resamples — and no gap in the state panel does. That the full ordering is a property of these
states' donor economies may well be true; the statewide all-donor figures in Appendix E point
the same way on far larger n, and those are not resampled here. But the matched panels do not
establish it.

Second, the state-versus-federal comparison does not run one way **as the panels are
built**, and does run one way **among donors above a common total**. As built, state money
is slightly *more* concentrated in Washington (43.5% vs 41.2%) and Idaho (40.0% vs 37.2%)
but *less* so in New York (48.6% vs 50.7%). Restricting every panel to donors with
more than **$200 in total observed giving** — so the state panels no longer reach further
into small-dollar giving than the federal ones do — makes the ordering consistent:

| state | as built | restricted to > $200 total |
|---|---|---|
| WA | +2.4 pts, state more concentrated | **−2.0 pts, federal more** — flips |
| NY | −2.0 pts, federal more | −6.7 pts, federal more |
| ID | +2.9 pts, state more concentrated | **−0.7 pts, federal more** — flips |

*`diag_panel_harmonized.py`. The restriction drops 26–27% of each federal panel but 60–69%
of each state panel — the difference in small-dollar reach, made visible rather than
assumed.*

Among donors above a common observed total, **federal money is the more concentrated layer
in all three states**. The as-built inconsistency comes from the state panels containing a
mass of small donors that the federal panels never see. Period-alignment is a separate cut
and does not do the same work: on Idaho's aligned panels, unrestricted, state money is still
the more concentrated of the two (aligned federal 34.7% against state 40.0%), so it is the
composition of the donor pool and not the window that produced the as-built inconsistency.

**This is a robustness test, not an identified threshold effect.** Restricting on a donor's
observed total is not the same as applying a statutory itemization rule (Appendix C), and it
changes which donors are in the pool rather than how the law treated them, so it cannot
attribute the difference to disclosure law — still less to contribution caps, which Appendix
G takes up separately.

A geographic corollary everywhere. Money concentrates in one county in each state. Because a
county is a comparable administrative unit across all three, the cut is reported on counties
throughout, and normalized by each county's share of the active roll so that a large county is
not mistaken for a concentrated one:

| panel | largest donor county | share of matched $ | share of active roll | **multiplier** | top 3 counties |
|---|---|--:|--:|--:|--:|
| WA federal | King (Seattle) | 58.2% | 28.3% | **2.06×** | 68.7% |
| WA state | King | 52.0% | 28.3% | **1.84×** | 65.3% |
| NY federal | New York (Manhattan) | 48.5% | 8.1% | **5.96×** | 68.6% |
| NY state | New York | 19.9% | 8.1% | **2.45×** | 46.7% |
| ID federal | Ada (Boise) | 36.8% | 29.3% | **1.26×** | 60.1% |
| ID state | Ada | 50.3% | 29.3% | **1.72×** | 64.4% |

*Source: the six panel tables joined to each roll's county of registration; multiplier =
dollar share ÷ active-roll share, the same estimator form as Finding 1's generation
multipliers. Re-derived by `verify_donor_class.py`.*

**Raw share and disproportion are different questions, and they order the states
differently.** On raw share Washington looks most concentrated (King 58.2% of federal
dollars); on the multiplier it is unremarkable, because King already holds 28.3% of the
state's registered voters. **New York is the extreme case on the measure that controls for
that**: Manhattan holds one voter in twelve and supplies nearly half of all federal matched
dollars, **5.96×** its share of the roll. Any account of "the New York donor class" resting
on the federal file alone is describing one island.

The same normalization changes which Idaho county the finding is about. Ada looks like
single-metro dominance on raw share, but it holds **29.3%** of Idaho's roll, so its 36.8% of
federal dollars is only **1.26×** — barely disproportionate, and mostly population rather than
concentration. Idaho's genuinely disproportionate money is somewhere else entirely:
resort-county **Blaine (Sun Valley)** has
**1.5%** of the roll and supplies **11.4%** of federal dollars, a multiplier of **7.83×** —
the highest of any county in any panel in this paper — from 909 donors.

**And the multiplier itself decomposes, exactly.** A county can be disproportionate because an
unusual share of its residents give at all, or because the ones who give write unusually large
cheques. Those are different claims about a place, and the multiplier is their product:

> multiplier = (county donors ÷ county roll) ÷ (all donors ÷ all roll) **×** (county $ per donor ÷
> all $ per donor) = **participation × intensity**

| panel · county | multiplier | participation | intensity | reads as |
|---|--:|--:|--:|---|
| NY federal · New York (Manhattan) | 5.96 | **2.53** | **2.35** | both, almost equally |
| NY state · New York | 2.45 | 1.22 | **2.00** | mostly intensity |
| WA federal · King | 2.06 | **1.44** | **1.43** | both, evenly |
| WA state · King | 1.84 | **1.52** | 1.21 | mostly participation |
| ID federal · Blaine | 7.83 | **2.67** | **2.93** | both, almost equally |
| ID state · Blaine | 3.48 | **2.59** | 1.34 | mostly participation |
| ID federal · Bonneville | 1.91 | 0.77 | **2.47** | intensity alone — below-average participation |
| WA federal · San Juan | 2.57 | **2.41** | 1.07 | participation alone |
| NY federal · Tompkins | 1.76 | **2.26** | 0.78 | participation alone |

*`diag_county_decomposition.py`; counties with at least 100 matched donors. The two factors
multiply to the published multiplier exactly, so the decomposition adds no assumption — it only
says which half of a county's disproportion it comes from. Re-derived by `verify_donor_class.py`.*

The concentrated metropolitan counties are disproportionate on **both** margins at once, which is
a stronger statement than the multiplier alone makes: Manhattan has two and a half times the
national-panel donor incidence *and* its donors give more than twice as much each. Blaine is the
same shape rather than the pure wealth effect a resort county might suggest — 2.67 × 2.93 — so
"rich people in Sun Valley" understates it: an unusual share of Blaine's registrants are donors as
well. The clean counter-examples run in both directions. **Bonneville** reaches 1.91× on intensity
alone, with donor incidence *below* the state average. **San Juan** and **Tompkins** — an island
county and a university county — are almost pure participation, with donors giving less per head
than average. A multiplier of roughly 2 therefore describes at least three different places, and
the two-factor form says which.

The panel difference runs the same way as the rest of Finding 2 and is largest in New York:
Manhattan's multiplier falls **5.96× → 2.45×** between the federal and state panels, as
suburban **Nassau (15.5%, 1.93×)** and **Suffolk (11.3%, 1.30×)** together overtake it,
which they do not come close to doing federally. Washington's King barely moves
(2.06× → 1.84×) and Idaho's Ada moves the *other* way (1.26× → 1.72×). The top-three-county
share is nearly identical in the two federal panels — WA **68.7%**, NY **68.6%** — and
collapses to **46.7%** in New York's state panel.

**Does the linkage's geographic non-match manufacture any of this?** It is the fair question to
put to a geographic finding computed on matched donors, because Appendix F reports that the
largest identified non-match bucket is keys whose surname and full first name sit on the roll
**at a different ZIP5** — displacement by definition. The answer is no, and the movement runs
the *other* way.

The primary specification requires ZIP5 equality, so a matched donor's county of registration is
the county of the ZIP they filed from, and the question reduces to selection: do the keys that
match distribute across counties like the keys that do not? Holding geography to one source —
the county of the filing ZIP — for both sides:

| panel · county | matched multiplier | all eligible keys | movement |
|---|--:|--:|--:|
| WA federal · King | 2.06 | 2.09 | -0.03 |
| NY federal · New York | **5.96** | **6.87** | -0.91 |
| NY federal · Westchester | 2.59 | 2.01 | +0.58 |
| NY state · New York | 2.45 | 3.64 | -1.19 |
| ID federal · Ada | 1.26 | 1.25 | +0.01 |
| ID federal · Blaine | **7.83** | **8.34** | -0.51 |
| ID state · Blaine | 3.47 | 4.13 | -0.66 |

*`diag_donor_geography_selection.py`, which reimplements the key rule from the specification
rather than importing it, and reports each panel's reconstructed match rate against the
published one before reporting any geography. Five panels reconstruct to within 0.3 points and
their matched multipliers reproduce the published ones above exactly. **Washington's state panel
does not reconstruct** — 8.8% of in-state dollars against the published 37.1%, because the PDC
name-order defect means the naive strict key cannot reach the keys the production matcher does —
so it is excluded rather than reported, consistent with its treatment as a secondary panel
throughout. Across the five, the largest county multiplier movement is 1.19. ZIP5 is assigned to its modal county on each state's own roll; that assignment
covers 98.6–99.3% of registrants in their own ZIP. One cell differs from the multiplier
reported earlier in this section — Idaho's state Blaine reads **3.47** here against **3.48**
above — and the gap is the point rather than a discrepancy: it is the whole effect of
geolocating by filing ZIP instead of county of registration, which is the substitution this
check relies on being small. It is 0.01.*

**Every headline county in this section is understated by the matched panel, not overstated.**
Manhattan's federal multiplier is 5.96× on matched donors and 6.87× across all eligible resident
keys; Blaine's is 7.83× against 8.34×. The keys that fail to match are drawn disproportionately
from the *most* concentrated places — which is what mobility, second residences and work-address
filing would predict — so the concentration reported here is a floor. The two counties that move
the other way, Westchester (+0.58) and Bonneville (+0.42), are suburban and secondary, and
neither carries a claim in this paper.

(Idaho is the least concentrated of the three in both panels, and its state filings bunch
hard on round statutory values — 6,797 itemized state gifts land on exactly $1,000, against 448
at $750 — which is consistent with some donors responding to a salient limit, though these rows
carry neither the recipient's type nor the election designation and so cannot identify which
gifts were legally constrained. Caps are in any case not what makes Idaho less concentrated, and the
reason is a within-layer comparison rather than a cross-layer one: **Idaho is the least
top-heavy of the three inside the *federal* layer, under the identical federal limits that
apply in Washington and New York**, so a limit common to all three cannot explain what
distinguishes Idaho. The cross-layer comparison is deliberately *not* used here — its sign
depends on the small-dollar reach of the state panels and reverses under the common-total
restriction above, so it cannot bear on caps in either direction. Appendix G runs the
mechanical test; Appendix D carries the statutes and the literature.)

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
On an all-records baseline every skew moves by at most 0.4 points. Scripts:
`match_ny_voters_to_donors.py`, `diag_donor_class_revisions.py`; re-derived by
`verify_donor_class.py`. **The skew column is computed on unrounded shares**, so it can differ by 0.1 from the difference of the two rounded shares printed beside it — five cells in this paper do. The unrounded difference is the figure; the printed shares are the rounding.*

Registered Democrats are +16.1 points over their share of the active roll in federal money
and supply **72.5% of federal matched dollars**; Republicans give roughly in proportion. The
constant across both panels is the under-representation of the unaffiliated: NY's "blank"
enrollees are a quarter of all registrants and only an eighth of federal donors, barely
better at a seventh of state donors.

The Democratic tilt itself is substantially a *federal* phenomenon. It falls by roughly
two-fifths in state money (+16.1 → +9.6), where Republicans move from slightly
under-represented to slightly over (−1.1 → +3.2). New York's donor class leans Democratic most sharply where
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

One temporal caveat applies to every row. **"Own party" is enrollment at the roll's
extract date; the contributions span up to nine years.** A donor who changed enrollment
during that window is classified by where they ended up, so a row pairing current
Democrats with past Republican-side gifts (or the reverse) can reflect a party switch
rather than cross-party giving. The tables measure *current enrollees' accumulated giving*,
not giving against enrollment at the time of each gift, which neither voter file records.

Recipient party comes from the bulk FEC committee and candidate masters on the federal
panel (`backfill_ny_committee_party.py`) and, on the state panel, from
`backfill_ny_recipient_party.py` — NYSBOE publishes no party on the filer, so party is
reconstructed from explicit party words in committee names, finance rows that already
carry a party, and the committee→candidate→roster chain.

**New York.**

| own party | matched | resolved | res. rate | D-only *of resolved* | R-only *of resolved* | Mixed *of resolved* | \| | $ to D |
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

Idaho's **minor-party (OTHER) rows are withheld** from the two tables below and from the bound
table that follows, as a disclosure control. Those blocs resolved to 102 and 44 donors, and a
percentage printed over a base that small lets a reader recover a count of a handful of
individuals by arithmetic. No claim in this section rests on them; New York's OTHER rows, over
bases of 7,122 and 5,410, are retained.

| own party | matched | resolved | res. rate | D-only *of resolved* | R-only *of resolved* | Mixed *of resolved* | \| | $ to D |
|---|--:|--:|--:|--:|--:|--:|---|--:|
| *federal panel* | | | | | | | | |
| REP | 15,621 | 13,545 | 86.7% | 17.1% | **82.1%** | 0.8% | | 18.1% |
| DEM | 4,764 | 4,473 | 93.9% | **98.5%** | 0.9% | 0.6% | | 99.1% |
| UNAFF | 2,754 | 2,286 | 83.0% | **78.3%** | 20.6% | 1.1% | | 77.7% |
| *state panel* | | | | | | | | |
| REP | 15,645 | 7,962 | 50.9% | 19.1% | **79.0%** | 1.9% | | 17.6% |
| DEM | 5,097 | 2,985 | 58.6% | **94.6%** | 3.0% | 2.3% | | 97.9% |
| UNAFF | 2,735 | 1,066 | 39.0% | **77.1%** | 20.5% | 2.3% | | 74.3% |

*Source: the four panel tables' `donor_party` classification and `d_amount` / `r_amount`
columns, joined to each state's party of record. All four blocks are on the primary
specification. Idaho's state rows sum to that panel's 23,613 once the withheld minor-party row
is added back. New York's sum to **378,388** rather than the panel's 378,383, the five extra
rows being the duplicate-`state_voter_id` fan-out on a roll join documented in Appendix C. Two
corrections to earlier versions of this table are recorded in the corrections ledger. Aggregate resolution: NY federal **88.8%**,
NY state 37.7%, ID federal **87.6%**, ID state 51.1% of matched donors.
Script:
`diag_donor_class_revisions.py`. Not covered by `verify_donor_class.py` — the crossover
cut depends on the recipient-resolution logic in the backfill scripts.*

**These tables are exploratory, and the unresolved pool is not missing at random.** The
resolution rate varies systematically by donor group — 91.1% for NY federal Democrats
against 80.1% for the unaffiliated, and on the NY state panel 45.5% for Republicans
against 26.9% for the unaffiliated. Whatever is unresolved is disproportionately the
unaffiliated bloc's giving, in the very rows the reader most wants. At 37.7% aggregate
resolution the NY state column should be read as indicative only.

**How much the unresolved pool could change this — a worst-case bound.** Because the
percentages above are of *resolved* donors, they do not tell a reader whether the unresolved
pool is large enough to reverse a row. The test is to assign **every** unresolved donor in a
row to whichever side would overturn it — an adversarial assignment, not a plausible one —
and ask whether the ordering survives. Shares below are of **matched** donors, so they are
comparable across rows (`diag_donor_class_revisions.py`):

| panel · own party | unresolved | D-only (of matched) | R-only (of matched) | adversarial rival | ordering survives? |
|---|--:|--:|--:|--:|:--|
| *NY federal* | | | | | |
| DEM | 8.9% | **86.9%** | 2.9% | 11.7% | **yes** |
| REP | 12.2% | 10.7% | **74.5%** | 22.9% | **yes** |
| NOPARTY | 19.9% | **52.1%** | 25.2% | 45.1% | **yes** |
| OTHER | 18.1% | 32.0% | 48.2% | 50.1% | no |
| *NY state* | | | | | |
| DEM | 63.0% | 32.9% | 3.0% | 66.0% | **no** |
| REP | 54.5% | 4.9% | 39.2% | 59.4% | **no** |
| NOPARTY | 73.1% | 14.2% | 11.7% | 84.8% | **no** |
| OTHER | 67.2% | 11.8% | 19.6% | 78.9% | no |
| *ID federal* | | | | | |
| REP | 13.3% | 14.8% | **71.2%** | 28.1% | **yes** |
| DEM | 6.1% | **92.5%** | 0.9% | 7.0% | **yes** |
| UNAFF | 17.0% | **65.0%** | 17.1% | 34.1% | **yes** |
| *ID state* | | | | | |
| REP | 49.1% | 9.7% | 40.2% | 58.8% | **no** |
| DEM | 41.4% | **55.4%** | 1.8% | 43.2% | **yes** |
| UNAFF | 61.0% | 30.1% | 8.0% | 69.0% | **no** |

**The bound divides the evidence sharply.** It holds for the **federal** panels and fails for
the **state** panels:

- **Federal panels — the primary evidence.** Every headline row survives the extreme bound,
  including the one a reader will care most about: among New York's unaffiliated federal
  donors, D-only donors are 52.1% of all matched donors in the row, more than the 45.1% that
  R-only would reach if *all* 19.9% unresolved were Republican. In Idaho the margin is far
  wider (65.0% against 34.1%). Registered Democrats are near-monolithic on the same basis
  (86.9% and 92.5% D-only of all matched). The one federal row that fails is NY's small
  minor-party bloc, which is not a claim the paper makes.
- **State panels — suggestive among resolved recipients only.** At 37.7% (NY) and 51.1% (ID)
  aggregate resolution, the unresolved pool is large enough to reverse every state row but
  Idaho's registered Democrats. New York's unaffiliated state row is the clearest case: 14.2%
  D-only against 11.7% R-only, with 73.1% unresolved — a modest reallocation of that pool
  overturns the ordering, and no assumption in this paper rules it out. These rows are
  reported because they are what the data contains, and they are not evidence for the
  patterns above.

Read against those limits, and treating the federal panels as the evidence:

- **Among donors whose recipients can be assigned a party, D-only donors outnumber R-only
  donors within the registered-Democratic and unaffiliated blocs, by wide margins, and this
  survives the worst case in both federal panels.** Registered Democrats are near-monolithic
  (95.3% D-only among resolved recipients federally in NY, 98.5% in ID).
- **Among unaffiliated federal donors, D-only donors outnumber R-only donors roughly 2:1 in
  New York and nearly 4:1 in Idaho** among resolved recipients, and the dollar-flow measure
  agrees (75.7% and 77.7% of resolved dollars to Democrats). The state panels point the same
  way but cannot support it. This says the unaffiliated bloc's *party-directed giving* leans
  Democratic. It does not establish that these donors are non-centrist ideologically:
  party-directed giving is one behavior, not a measure of ideological position.

**One asymmetry the paper does not claim.** On the NY federal panel, 12.2% of registered
Republicans with a resolved recipient classify D-only against 3.2% of Democrats classifying
R-only; on the dollar-flow measure the same rows read 18.3% of resolved Republican dollars to
Democrats against 4.5% of Democratic dollars to Republicans. Both are legitimate quantities and
they are not interchangeable — a ratio of the first pair is not a statement about money. Neither
is offered here as a finding.

The Idaho state panel's Republican→Democratic figure carries one further caveat: the
unresolved pool there (local Republican candidates and R-aligned PACs absent from the
roster) skews Republican, so Republican donors' Republican-side giving is
disproportionately the untraced part, making the **19.1%** D-only share of resolved
recipients an **upper bound** on the crossover rate. On the federal panel, at 87.6%
resolution from authoritative party labels, the **17.1%** figure carries no such hedge — and
it lands two points below the state panel's upper bound. Note the interaction with the
worst-case table above: that table's adversarial assignment for this row pushes all 49.1%
unresolved to the *Democratic* side, which is the opposite of the direction the unresolved
pool is documented to skew. So the "no" verdict for ID state REP is the correct verdict for
an assumption-free bound, and the documented skew of that particular pool runs the other
way. The two statements are consistent, and neither licenses treating the state row as
evidence.

### Idaho — the same skew, in the reddest state, in both money systems

A particularly informative test of whether the Democratic tilt of the donor class is a blue-state
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
identical. Re-derived by `verify_donor_class.py`. **The skew column is computed on unrounded shares**, so it can differ by 0.1 from the difference of the two rounded shares printed beside it — five cells in this paper do. The unrounded difference is the figure; the printed shares are the rounding. **These skews are unadjusted for age.** The
Republican row does not survive age standardization — see the subsection below, where the
federal +4.2 becomes −0.1 and is withdrawn. The Democratic and unaffiliated rows do survive.*

Dollar shares track the same way — Republicans supply 68.5% of federal and 72.2% of state
matched dollars, Democrats 21.8% and 20.0%, the unaffiliated 9.3% and 7.6%.

Republicans supply the plurality of Idaho's money, as a 63%-Republican state must — and
Idaho's donors remain predominantly Republican in absolute terms. The finding is
relational: measured against their share of registration, the **most over-represented
donors are registered Democrats** (+8.6 federal, +9.8 state, well over half again their
share of the roll), and the unaffiliated quarter is the most *under*-represented in both
(−12.1, −12.3). Period-aligning the two panels to 2023–2025 does not soften this; on the
aligned federal panel the Democratic share is 21.9% (+10.1) and the unaffiliated 11.1%
(−12.7). The same directional finding as New York, from the opposite end of the spectrum,
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
congressional district's competitiveness (`diag_ny_electorate_extras.py`, recomputed per
panel — that script reads the pooled match), the donor pool's Democratic share **exceeds
the registered Democratic share in every band, in both panels** — federal Tossup 58.7%
donor vs 40.4% registrant and Solid 72.6% vs 56.1%, state 51.3% and 66.9% against the same
baselines — so the donor class is more Democratic than the registration baseline not just
statewide but locally, regardless of how contested the seat is. And **two-thirds of federal
matched donors (177,918 of 269,218) live in Solid districts** — 62% of state ones (233,275
of 378,383) — mostly Solid-D Manhattan: the money
originates in safe seats, consistent with the cross-state finding that safe
seats supply most of it. Idaho shows the same safe-seat origin from the red side, on its
state panel: 14,594 matched donors sit in the 27 Solid-R legislative districts (where
the donor pool runs 78% Republican to 13% Democratic), while the 8 more competitive
districts carry a far more balanced 47% Republican / 35% Democratic across 9,019 donors
(`diag_id_electorate_extras.py`) — the money, in both states, originates
overwhelmingly in the seats that are not in doubt.

### Is this the age skew restated? — party composition standardized on age

Every figure above is unadjusted for age, and Finding 1 establishes that matched donors
are far older than the roll. Party registration is not age-neutral, so a donor class that
old could differ in party composition partly *because* it is old. The question is whether
registered Democrats are still over-represented among donors compared with registrants
**of the same age**. Three cuts, all from
`diag_donor_age_standardization.py`, on active registrants with a usable age of 18 or over
(NY 12,292,685; ID 1,029,938 — slightly narrower than Finding 3's baseline, which does not
require an age, so the skews here are not numerically identical to the table above):

| panel · party | raw skew | age-standardized skew | age share of raw skew |
|---|--:|--:|--:|
| *New York, federal* | | | |
| DEM | +15.9 | **+16.5** | −3.9% |
| REP | −1.2 | −3.7 | −208.3% |
| NOPARTY (blank) | −13.4 | **−11.5** | 14.4% |
| OTHER | −1.3 | −1.4 | −7.1% |
| *New York, state* | | | |
| DEM | +9.4 | **+10.6** | −12.7% |
| REP | +3.1 | +1.0 | 67.3% |
| NOPARTY | −12.4 | **−11.4** | 8.3% |
| OTHER | −0.1 | −0.3 | −81.0% |
| *Idaho, federal* | | | |
| REP | +4.2 | **−0.1** | **103.3%** |
| DEM | +8.6 | **+8.4** | 2.3% |
| UNAFF | −12.1 | **−8.1** | 33.0% |
| OTHER | −0.7 | −0.2 | 69.7% |
| *Idaho, state* | | | |
| REP | +3.4 | +3.5 | −3.2% |
| DEM | +9.8 | **+8.2** | 16.5% |
| UNAFF | −12.3 | **−11.2** | 9.0% |
| OTHER | −0.9 | −0.5 | 45.6% |

*Direct standardization: seven age bands (18–24 / 25–34 / 35–44 / 45–54 / 55–64 / 65–74 /
75+), standard population = that state's active roll, standardized share =
Σ<sub>band</sub> w<sub>band</sub> × (party's share of that band's donors). "Age share of raw
skew" = (raw − standardized) ÷ raw, so **100% means the raw skew was entirely age
composition** and a **negative value means standardization moved the skew further from
zero** — age was working against the raw figure, not producing it. Read those negatives as
"none of it," not as a magnitude: the ratio is unstable when the raw skew is near zero, which
is why NY federal REP reads −208.3% on a raw skew of −1.2. The coarser four-band version
moves every figure by less than a point except Idaho federal REP (+4.2 → −1.1) and is printed
alongside in the script.*

**Two of this section's three claims survive age adjustment; the third is destroyed.** The
Democratic over-representation is not an age artifact in either
state or either panel: it is unchanged or slightly larger after standardization (NY federal
+15.9 → +16.5; ID federal +8.6 → +8.4). The unaffiliated under-representation is genuinely
part age — a third of Idaho's federal figure and about a tenth of the rest — but survives at
−8.1 to −11.5 everywhere. What does *not* survive is the Republican over-representation in
Idaho's federal panel: **+4.2 raw becomes −0.1 standardized**, meaning Idaho's federal
donors are Republican in exactly the proportion their age distribution predicts, and the
raw figure was the age skew restated. The raw figure should not be cited as Republican
over-representation.

The cleanest form of the cut needs no share-of-donors denominator at all — **raw
matched-donor incidence by party**, matched donors per 1,000 registrants of the same party,
which asks directly how often each party's registrants appear as donors:

| panel | DEM | REP | unaffiliated / blank | other |
|---|--:|--:|--:|--:|
| NY federal | **29.2** | 20.8 | 10.2 | 15.7 |
| NY state | **36.8** | 35.0 | 15.6 | 29.8 |
| ID federal | **39.2** | 24.1 | 11.2 | 11.1 |
| ID state | **41.9** | 24.2 | 11.1 | 9.2 |

*Same script and universe. These are **raw** rates, and the ordering holds inside every one of
the seven age bands in all four panels: registered Democrats highest, the unaffiliated at
26.5–42.3% of the Democratic rate. Two things could produce a party difference in this
statistic besides donation behavior — differential matchability and geography — and both are
tested below.*

**Could a party simply be easier to match?** The rate above divides by *all* registrants of a
party, so it confounds donation incidence with the probability that a party's registrants are
uniquely identifiable under the full-name + ZIP5 rule. Measured directly, it does not:
P(matchable) spans just **1.0 point** across New York's parties and **0.8** across Idaho's,
which is a multiplicative difference of about 1.01× against incidence ratios running 1.05× to
1.73×. Re-basing the rate on *uniquely matchable* registrants raises every figure by 3–4% and
changes no ordering. Appendix F reports the table, the within-age-band and within-county
spreads, and the re-based figures.

**And geography?** Giving is geographically concentrated (Finding 2) and party registration is
geographically structured, so age standardization alone does not show the party result is
independent of Manhattan or Ada County. Standardizing incidence directly onto the roll's joint
age × county distribution:

| panel | DEM | REP | unaffiliated | other |
|---|--:|--:|--:|--:|
| NY federal | **27.8** | 19.8 | 12.1 | 16.4 |
| NY state | **38.1** | 29.7 | 16.7 | 26.7 |
| ID federal | **35.1** | 23.0 | 12.5 | 20.0 |
| ID state | **36.9** | 23.7 | 11.5 | 10.2 |

*Direct standardization on the joint stratum, 100% of the standard population retained except
Idaho's small OTHER bloc (99.7%). The Democratic > Republican > unaffiliated ordering survives
in all four panels.*

So in Idaho a registered Democrat appears as a matched donor at **1.62× (federal) and 1.73×
(state)** the Republican rate unadjusted, and at **1.53× and 1.56×** after standardizing on age
and county jointly — in a state where Republicans outnumber Democrats better than five to one
on the roll. The unadjusted ratios are raw rates and are labelled as such; the adjusted ones
are the figures to cite. Age and geography attenuate the gap modestly and do not close it.

Age is the one composition variable adjusted for here. Income, education and turnout
history are not observable on any of these voter files, so this addresses "is the party
skew merely the age skew?" and nothing broader.

---

## Finding 4 — Donors vote at far higher rates than non-donors, and not only because they are older

In both states with the necessary history, the people who give are the people who
reliably vote, and it holds in both money systems — this is the finding least sensitive to
the panel split. New York carries the cleaner measure and is therefore reported first: its
federal matched donors
voted in **3.10 of the last four federal generals on average versus 1.85** for non-donors,
and **75.7% are super-voters (≥3 of 4) versus 39.3%**; the state panel lands within half a
point of that on every measure (3.07 vs 1.84; **75.3% versus 39.0%**), despite
drawing on 109,000 more people. That is a pure count of generals voted.

Washington's export supports only a coarser measure, and **its figures are not comparable
with New York's** — a limitation stated here at first use rather than after the fact.
In Washington, federal matched donors are **88.0% super-voters versus
54.7%** of non-donors (mean turnout propensity 0.977 vs 0.796); the state panel is nearly
identical at **88.9% versus 54.2%** (0.966 vs 0.794). `voter_scores.is_super_voter` carries an
eight-year registration requirement inside its own definition, so it cannot take the tenure
adjustment below and is not a count of elections; the full statement of that defect closes this
section, and the tenure-free Washington substitute used in the adjusted tables is *voted both
the 2022 and 2024 generals*.

*Source: WA `voter_scores` (`ld`-scope) and NY `vrdb.voter_participation`, generals
2018/2020/2022/2024. Non-donor denominators are **active registrants** (`status_code='A'`) in
both states, matching the matcher's universe and the baseline used everywhere else in this
paper. **Crosswalk to the companion Washington papers**, which read against the wider
`voter_scores` roll including its **412,361** inactive registrants: inactive registrants vote
less, so that convention depresses the non-donor rate to **52.0%** federal and **51.5%** state
and widens every Washington gap here by **2.7** points (**3.6** on the exact-eligibility
restriction below). The figures published above are the active-roll ones. Re-derived for both
panels of both states, and the crosswalk with them, by `verify_donor_class.py`.*

The observed donor population also has much higher recorded turnout than the observed
non-donor population — but a large part of that raw gap is age and registration tenure,
not giving. Donors are far older (Finding 1), older registrants vote more, and a recently
registered voter cannot have accumulated a long participation record at all. Standardizing
both groups onto the same age distribution, then onto the same joint age × tenure
distribution (`diag_donor_age_standardization.py`; universe = registrants with a usable age
of 18+, so the raw figures below differ by under a point from the headline ones above):

| measure | raw gap | age-standardized | age × tenure |
|---|--:|--:|--:|
| NY, federal panel — super-voter (≥3 of 4 generals) | +35.9 | **+23.8** | **+20.8** |
| NY, state panel | +35.8 | **+26.8** | **+22.7** |
| WA, federal panel — voted both 2022 and 2024 generals | +39.5 | **+29.2** | **+22.0** |
| WA, state panel | +36.2 | **+27.6** | **+18.7** |

*Direct standardization onto the pooled comparison universe, seven age bands crossed with
five tenure bands (<2 / 2–5 / 6–10 / 11–20 / 20+ years registered as of 5 Nov 2024); 100%
of the standard population is retained in every cell, so no weight is silently dropped. The
non-donor rate barely moves under either adjustment — non-donors are nearly the whole roll —
so the adjustment falls almost entirely on the donor side.*

**Composition explains part of the raw gap and not most of it — how large a part depends on
which adjustment, and the better one attributes less.** On these tenure-band figures age and
tenure account for roughly two-fifths of the raw gap (NY federal 42%, WA federal 44%); on the
exact-eligibility restriction below, which the next subsection shows is the sounder adjustment,
they account for only **9–21%**. The larger attribution is an artifact of over-adjustment, so
the two-fifths figure should not be cited as the composition share. The
figures above are standardized for age and for **broad registration-tenure category**, and that
qualifier is load-bearing: a 2–5-year band mixes registrants who could have voted in three of
New York's four elections with registrants who could have voted in one, and donors and
non-donors need not have the same registration dates inside a band. The gap is positive in
every one of the seven age bands in all four panels (widest in the middle bands — NY federal
+28.9 at 35–44 against +23.2 at 65–74).

**Equalizing opportunity exactly — and it moves the estimate up, not down.** The clean version
of the adjustment is not to standardize on tenure but to remove the opportunity difference by
construction: restrict to registrants who existed *before the first election in the window*, so
every retained person could have voted in all of them. That keeps 69.0% of New York's active
roll (8,484,176 of 12,292,685, the 2018 general as the cutoff) and 86.2% of Washington's
(4,289,179 of 4,975,651, the 2022 general):

| panel | raw gap, eligible-for-all | age-standardized | voted ÷ eligible, donors | non-donors |
|---|--:|--:|--:|--:|
| NY federal | +29.3 | **+25.1** | 84.0% | 58.7% |
| NY state | +29.0 | **+26.3** | 82.8% | 58.5% |
| WA federal | +33.1 | **+26.0** | 96.1% | 71.2% |
| WA state | +29.0 | **+22.9** | 93.1% | 70.9% |

*`diag_donor_review3.py`. The last two columns are an alternative that keeps late registrants:
elections voted ÷ elections for which the registrant existed, computed on the unrestricted
roll.*

**On an exact eligibility restriction the adjusted gaps are larger than the tenure-band
figures — +22.9 to +26.3 against +18.7 to +22.7.** The broad bands were over-adjusting, by
pooling registrants whose opportunity sets differed. Both versions are reported; the
eligible-for-all column is the one that equalizes opportunity, and it is the one to cite. Under
either, the descriptive claim holds: the population that gives votes at substantially higher
rates than comparable registrants who do not.

**One caveat on the tenure variable itself.** `registration_date` is the registration date as
each state publishes it, and neither state documents it as an original-registration date immune
to a county transfer or a re-registration. A mover can therefore appear as a short-tenure
registrant. That cuts two ways and neither is resolved here: it makes the tenure-band
standardization noisier than it looks, and it means the eligible-for-all restriction **excludes**
some voters who were in fact continuously registered — so the restricted sample is a subset of
the truly eligible, which is conservative for eligibility while losing movers. The published
ranges span both treatments for that reason.

**Washington's headline super-voter figures cannot carry the tenure adjustment, and this is
a defect in the measure rather than a result.** `voter_scores.is_super_voter` is defined as
*last voted on or after 1 Jan 2022 **and** registered at least eight years* — registration
tenure is inside the outcome definition, so every registrant of under eight years' standing
is false by construction. Standardizing that variable on tenure conditions on a component
of itself and is not an adjustment (it reads +7.0 / +6.8, and those numbers should not be
quoted as adjusted estimates). Two consequences are stated rather than buried: the WA
88.0% / 88.9% figures above are **not** measure-comparable with New York's 75.7% / 75.3%,
which is a pure count of generals voted; and the WA row of the table above therefore uses a
tenure-free substitute — voted both the 2022 and 2024 generals — because the WA voter-file
export carries only those two generals in its rolling history window, so a four-general
count is unavailable for Washington at any tenure. That substitute is a different measure
from New York's and is never compared to it.

Association only, in every form above. Donors are pre-selected for engagement, so reverse
causation is equally plausible; the benign "donating as a gateway to participation" reading
is fully live, and is treated as objection 3 in Appendix A. Age and tenure are the two
composition variables adjusted for; current-roll survivorship, income and education are
not, and the standardization does not address them.

**A nominating-stage corollary, in both party-of-record states.** Both states gate their
nominating electorates by party of record, and this paper measures **the composition of those
gated electorates** — not the share of seats that are settled in them. NY's **closed**
primaries restrict each party's primary to enrollees, so the **25.3% enrolled "blank" are
excluded by law** (≈0.1–0.6% primary participation), and in blue NY the Democratic primary
draws the higher participation rate of the two (2021 odd-year DEM 16.9% vs REP 5.0%).

Idaho is the mirror image. Republicans hold a 62.9% registration plurality, so its **closed
Republican primary is much the larger of the state's two nominating electorates** — a
statement about where participation concentrates, quantified in the table below, not about
where seats are decided. Neither companion supports the stronger reading: the New York paper expressly
declines to determine the stage at which any individual seat became effectively decided, and
the Idaho paper withdrew the equivalent inference on its own November results. Nothing below
depends on it. Idaho's mechanism differs from New York's, and is reported here as composition
rather than as a participation rate:

| population | people | REP | DEM | UNAFF |
|---|--:|--:|--:|--:|
| registration roll | 1,029,938 | 62.9% | 11.8% | **23.9%** |
| 2024 general electorate | 898,877 | 64.5% | 11.6% | **22.6%** |
| 2024 primary electorate | 274,684 | 85.2% | 8.3% | **5.9%** |

*Source: `data/id_vrdb.duckdb` `voters.party` × `voter_participation`; party at extract
date. Script: `diag_donor_class_revisions.py`; re-derived by `verify_donor_class.py`.
Ballots actually pulled in the 2024 primary: Republican 229,173 (83.7%), Democratic
33,535 (12.2%), unaffiliated 9,567 (3.5%), Libertarian 952, Constitution 657. Those five sum to
**273,884** against the 274,684 in the table above, and the shares in this note are computed on
the smaller total. The **800**-record difference is participants whose `ballot_choice` is blank
in the roll — recorded as having voted in the primary, with no party ballot recorded. The table
counts participants; this note counts party ballots, so neither total is a subset error and the
gap is the unrecorded-ballot bucket rather than a reconciliation failure.*

Unaffiliated registrants are 23.9% of Idaho's roll and 22.6% of its 2024 general
electorate, but **5.9% of its 2024 primary electorate**. Two mechanisms produce that drop
and this design cannot separate them. Idaho's Republican primary is closed to voters who
remain unaffiliated — but **an unaffiliated voter may affiliate with a party up to and
including election day and then vote in that primary.** A voter who does so appears as a
Republican in the later voter-file extract, so part of the 23.9% → 5.9% fall is category
migration rather than non-participation, and the residual 5.9% reflects the unaffiliated
and nonpartisan ballots that remain available. Idaho *rates* are not reported here at all:
current-roll denominators make them unreliable (Appendix C), and a rate could not distinguish
non-participation from affiliation change in any case.

The population that nominates is small and party-gated in both states — and, per Finding
3, funded by a donor class narrower and more skewed still.

---

## What this paper does not claim, and limits

- **The match is a proxy, and a floor.** Voter↔donor identity rests on name + ZIP
  uniqueness across four tiers (Appendix C), not on a shared identifier. It is
  conservative by design (ambiguous keys are dropped, not guessed), so the matched set is
  a **floor on the number of identifiable donor–voter matches**, not a census of donors.
  **"Floor" refers to that count and to nothing else** — it is not a lower bound on donor age,
  on concentration, on party skew, or on any other statistic computed over the matched set,
  each of which can move in either direction as coverage improves. A stratified blinded rating
  of 480 matched records (Appendix F) found that **detected precision differed sharply by
  match tier**, so the
  paper now reports the full-first-name key alone: **no detectable false match** there
  (120/120, Wilson [96.9–100]) against **47.9–71.7%** on the three initial-based keys, whose
  failure mode is the household/relative merge. A **blinded author re-rate** of 150 of
  those records agreed on **75 of 75** full-name-key rows and never contradicted a Y — a
  test–retest result, not an independent one. Under
  the superseded all-tier specification population-weighted precision was **93.0%**, and precision was *lower* in the top dollar
  decile (63.0% vs 72.1% raw). Two costs are carried in the open: 100% is a ceiling on
  *detectable* error — a true namesake is invisible to the rating — and the restriction
  discards 11–19% of matched donors who are **younger and less Democratic** than those
  retained, so part of the sharpened skew is selection rather than precision.
- **Itemized giving only — but the panels are not truncated at their statutory floors.** Each
  source's floor sets when a contributor's identity *must* be itemized: federal aggregate
  **> $200** per cycle, Washington **> $25** rising to **> $100** on 1 April 2023, New York
  **> $99**, Idaho **> $50** (Appendix C). Those floors do **not** describe where each panel
  actually begins. Two mechanisms put identified giving below the floor: the floors
  are per-donor **aggregates**, so every gift from a donor who crosses the floor is itemized
  including the small ones; and committees disclose well below what is required. Measured:
  89.9% of the federal layer's gifts are ≤$200, 62.6% of New York's are ≤$99, and 68.4% of
  Idaho's are ≤$50. At the *donor* level — the level this paper's estimator works at —
  **53.5% of Washington's matched state donors have totals at or below $100 and 17.9% at or
  below $25**, with the smallest at one cent. So the matched panels reach far deeper into
  small-dollar giving than their floors imply. Two consequences run in
  different directions and are separated here: on **dollar concentration**, itemized-only
  top shares are likely higher than the corresponding share of *all* receipts would be,
  since the omitted contributors are expected to be predominantly small-dollar — though
  this is an expectation and not a formal bound, because adding donors moves the top-1%
  cutoff as well as the denominator (Appendix A, objection 5);
  on **donor composition**, excluding small donors makes the observed donor population
  older and narrower than the population of all contributors. Both cut against reading
  these figures as describing all giving. Part of every federal-vs-state panel difference is
  a disclosure-regime artifact rather than a behavioral one — but because the binding
  constraint is below-floor disclosure practice rather than the floors themselves, that
  artifact cannot be removed by comparing the panels at their nominal thresholds, and
  restricting every panel to donors above a common observed total is a choice about the
  analysis universe rather than a correction that makes the panels equivalent, and it does
  not identify the effect of any threshold.
- **Panel comparisons are descriptive, not identified.** Federal and state panels differ
  in disclosure trigger, in years covered (Idaho only), in *who is in them* — they
  overlap by a Jaccard coefficient of 0.14–0.16 — and in how far the linkage reaches into each,
  from 39.1% to 56.9% of resident contributor keys. "Federal money is older money" is a
  robust difference between two datasets that survives period alignment; it is not an
  established effect of federal versus state regulation. State money reaches more donors in all
  three states once the windows are aligned: Idaho's state panel reaches 23,613 against the
  federal panel's 14,848 — 59% more — the same direction as WA and NY.
- **The Washington state panel is coverage-compromised and is read as a sensitivity panel.**
  The PDC files contributor names without a comma, and the matcher's parse takes the first token
  as the surname, so it mis-reads every filer who wrote their name first-name-first. That is
  measured, not estimated: **7.2%** of comma-less resident keys and **8.4%** of their dollars
  resolve to a unique active registrant only when the name is read the other way, against a
  **0.18%** coincidence baseline (Appendix F §F8). The parser is not repaired here, because the
  recovered keys would come from a population the blinded validation never rated. The direction
  is measured too and runs *against* the finding — the lost donors are older — so this panel's
  **age** result is understated rather than manufactured. That is the only outcome for which the
  direction has been established: **effects on concentration, county geography, dollars per
  donor, turnout and the federal–state comparisons other than age were not measured**, so for
  those the Washington state panel is a secondary sensitivity panel and the sign of the coverage
  loss is unknown. Its **match rate** should not be compared with the other panels' at face
  value.
- **Three purposively selected states, not a sample.** Washington, New York and Idaho were
  chosen because their voter files were obtainable and because two of them publish party of
  record — the condition the central comparison requires. They are not representative of the
  states, and no quantity here should be read as a national estimate or as the range a
  fifty-state study would produce.
- **Composition, not rates.** All three matches use the current roll, so turnout *rates*
  for older cycles are biased by survivorship. Share-of-population figures, which need no
  denominator, carry the findings. Idaho's age is a current-roll integer, so its bands are
  current-age, not election-time.
- **Registration baselines are active registrants, measured at the extract date.** Party, age
  and turnout baselines use `status_code='A'` in all three states, the universe the matcher
  draws from — no cut in this paper uses a wider roll. These are
  registration shares, not shares of the eligible or voting population, and party of
  record is not necessarily a donor's party when they gave.
- **Recipient party is partial, differentially missing, and only the federal crossover
  results are load-bearing.** It resolves for **88.8%** of NY federal and **87.6%** of ID
  federal matched donors, where the FEC masters carry party outright, but only **51.1%** of
  ID state and **37.7%** of NY state donors, where it must be reconstructed. Resolution rates
  differ by donor group, so the unresolved pool is not missing at random. A worst-case bound
  (Finding 3) assigns every unresolved donor in a row to the side that would overturn it:
  **every headline federal row survives that assignment, and every state row but Idaho's
  registered Democrats fails it.** The state-panel crossover figures are therefore reported as
  suggestive among resolved recipients and are not treated as evidence for the patterns the
  paper claims. Own-party and age cuts use the 100%-present party of record and are
  unaffected.
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
and across two separately regulated money systems within them — the observed matched donor
populations share several recurring characteristics: **substantially older than the
registration baseline, top-heavy, geographically concentrated, and — where party is
observable — tilted toward registered Democrats relative to registration and away from
the unaffiliated.** The party half of that carries an asymmetry worth restating here rather
than leaving in the appendix: New York's result survives both error bounds the validation
supports, while **Idaho's holds under the per-stratum bound its stratified independent
validation was designed to support, and not under a panel-wide one** — a distinction §F7
states explicitly, because the stratified second draw is what licenses the stratum
construction. That the pattern reappears in every state-and-panel combination where
it can be measured is evidence that the findings are not confined to a single state panel or
disclosure system — with the caveat that the two systems' panels are largely
different people under different disclosure floors, so their *differences* are descriptive
rather than identified.

New York and Idaho's party of record turns the Washington finding from "the matched
itemized donor class is demographically unrepresentative" into the sharper claim that it
is *also* partisan-unrepresentative in a specific direction — and, critically, in the **same**
direction in a deep-blue and a deep-red state, so the result is not mechanically
attributable to which party holds the statewide registration plurality. Whether it
reflects something more general about who gives, this design cannot say.

Combined with the turnout and safe-seat papers, the picture is a series of narrowing
filters between the registered population and the population that acts — who votes, who
participates in the nominating primary, and who pays. Taken together those companion studies identify
several stages at which the politically active population differs from the registration
baseline; they do **not** establish a uniform monotonic ordering across every state and stage,
which would require one set of states, dates, denominators and age definitions that they do not
share. Whether acting translates into influence is not measured here.
This is the evidentiary core of the electoral-health series' "donor class ≠ electorate"
finding, extended to party of record in two politically contrasting party-registration states —
established for New York on either error bound, and for Idaho on the
per-stratum bound the independent rating supports.

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
generation multiplier is unchanged to two decimal places in both panels. (Those two figures
are on the superseded all-tier panels, which is why the 47.9% differs from the 49.9% the
primary specification reports; the test is a property of the roll and the match key, not of
which contributions are used, so it carries over unchanged. Finding 1 states this too.) A
selection gradient that flat cannot produce senior over-representation of 2.6×. What this test covers
is precisely age variation in *unique-key availability*; it does not address false-match
rates, mobility, or survivorship, which are objections 2 and the Appendix F residual.
Full tables in Appendix F.

**2. Household false-merges inflate individual donors.** Because the key is surname plus
ZIP, a married couple sharing both can in principle collapse into one matched voter,
attributing a spouse's giving to their partner. Hand rating of a 150-record sample
(2026-07-10), and a stratified blinded re-rating of 480 records (2026-07-27), both found
this the dominant error mode — and the re-rating localised it precisely: **129 of 152
confirmed false matches are household/relative merges, every one of them on an
initial-based key, none on the full-name key**. The effect is **not** small by
construction, and a shared household does not make it so: spouses can differ in age, party
enrollment and turnout history, and merging two people's contributions into one donor total
directly increases measured concentration. It is bounded instead by an exclusion. Dropping every matched donor who shares a surname and ZIP5 with any other
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
which is all Finding 4 claims: giving and voting are observed on the same people rather
than on complementary populations, and the association survives standardizing both groups
on age and registration tenure.

**4. The crossover tables' unresolved pool is not missing at random.** Recipient party is
reconstructed rather than published on both state panels, resolving 51.1% of ID and 37.7%
of NY state matched donors, and resolution rates differ by donor group by up to 18 points.
The unresolved Idaho pool — local Republican candidates and R-aligned PACs absent from the
Secretary of State roster — skews Republican, so Republican donors' Republican-side giving
is disproportionately untraced and the 19.1% D-only share of resolved recipients is an
upper bound on that crossover rate. The tables are presented as exploratory for this reason.

**On the strength of the two patterns the paper does claim, this objection is partly
sustained.** Those patterns — currently enrolled Democrats' resolved giving being
near-monolithically Democratic-side, and unaffiliated donors' resolved giving leaning
Democratic — survive an
extreme bound on the **federal** panels, where resolution is 87.6–88.8% and where assigning
the entire unresolved pool to the rival side still leaves D-only ahead (NY unaffiliated 52.1%
against 45.1%; ID unaffiliated 65.0% against 34.1%, as shares of matched donors). They do
**not** survive it on the state panels, where 54–73% of a row can be unresolved. An earlier
draft said the unresolved pool "cannot plausibly reverse them" without distinguishing the two
cases; on the state panels it plainly can, and the bound table in Finding 3 now shows exactly
where.

**5. Itemization hides the small-dollar end, so concentration is overstated.** Correct in
direction, and the paper now says so rather than arguing the objection runs the other way —
but the size of the hidden mass is smaller than the statutory floors suggest, and an earlier
draft of this appendix overstated it. The floors (federal > $200 aggregate per cycle; WA
> $25, > $100 from April 2023; NY > $99; ID > $50) govern when identity must be *reported*,
not where the published data begins: because they are per-donor aggregates and because
committees disclose below what is required, 89.9% of federal gifts are ≤$200 and **53.5% of
Washington's matched state donors have totals at or below $100**. What is genuinely missing
is giving by donors whose aggregate never crosses their floor, plus whatever is reported
without an attributable identity. Because those contributors are expected to be
predominantly small-dollar, the itemized-only estimates **likely overstate** concentration
relative to all contributors — but that is an expectation, **not a formal mathematical
bound**. Adding donors changes the
top-1% *cutoff* as well as the denominator: if the number of donors doubles, so does the
headcount inside the top 1%, and the additional ranked donors entering the numerator can in
principle outweigh the small-dollar mass added to the denominator. A genuine bound would
need the aggregate amount of unitemized receipts together with assumptions about how many
omitted contributors there are and where they rank — none of which the disclosed data
supplies. Separately, and in the same direction as the paper's
argument, excluding small donors makes the observed donor population older and narrower
than the population of all contributors. Both consequences run against reading these figures
as describing all giving, and neither runs the other way.

**6. State contribution caps, not donor behavior, explain Idaho's flatter distribution.**
This was the paper's own earlier explanation, and Appendix G shows a mechanical truncation
simulation does not reproduce it. It is retained here as an objection because it is the
intuitive reading, and because the simulation bounds only the mechanical channel, not the
behavioral one.

## Appendix B — Data access and privacy

- **Data minimisation applied to the New York file.** The NYSVOTER FOIL production carries a
  full date of birth. Because every age figure in this paper is a birth-year difference, the day
  and month are **generalised to 1 July of the birth year in the analytical copy** — the same
  representation Washington's file has always had, since RCW 29A.08.710 releases year of birth
  only. The migration was verified lossless: all twelve New York age-band figures are identical
  to six decimal places. The raw production is retained only as the restricted source of record.

- **Washington.** The standard statewide **VRDB extract**, the single public extract the
  Secretary of State publishes. By statute the public file carries name, address,
  political jurisdiction, gender, **year of birth**, voting record, registration date,
  and registration number, and no other registration information is available for public
  inspection (RCW 29A.08.710) — the statutory reason this series uses year of birth
  rather than full date of birth.

  **Permitted use, in the statute's own terms.** The provision is stated here as written,
  because a summary of the form "use is restricted to elections and political purposes and may
  not be commercial" is both broader than the statute and structurally backwards. The section
  **prohibits** using the lists or labels "for the
  purpose of mailing or delivering any advertisement or offer for any property,
  establishment, organization, product, or service or for the purpose of mailing or
  delivering any solicitation for money, services, or anything of value." It then
  **affirmatively permits** use "for any political purpose," which it defines to include
  activity concerned with support of or opposition to any candidate for partisan or
  nonpartisan office or to any ballot proposition or issue — expressly including "advertising
  for or against any candidate or ballot measure or the solicitation of financial support"
  for such purposes. So the operative test is not commerciality in the abstract: commercial
  *advertising and solicitation* are barred, while political solicitation of financial
  support is permitted.

  **The basis this work relies on is therefore documented rather than assumed.** This series'
  use of the file is analysis of electoral participation and campaign finance, published as
  aggregate research; the author is associated with a political consulting company, so the
  distinction matters and is stated rather than left implicit. No advertisement, offer, or
  solicitation for property, product, or service is mailed or delivered from these data, no
  individual-level record is published, and the file is **not redistributable** (penalties at
  RCW 29A.08.740). The full reasoning, the human-subjects determination and the disclosure
  controls are set out in
  [`data-use-and-research-ethics-assessment.md`](data-use-and-research-ethics-assessment.md) — a **self-assessment,
  not an IRB determination**, since the author is not affiliated with an institution that
  operates one; that document states its own limits and the two open items remaining before it
  is signed. Washington further strengthened voter-data
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
  telephone-number lists. It is **not** the source of the age-not-DOB release, and the public
  list **does** include address, subject to separate protections for confidential-address
  registrants.
- **Contribution data are publicly disclosed in every layer used** — FEC bulk individual
  contribution files; Idaho Sunshine state contribution filings; Washington PDC filings; the
  NYSBOE contribution disclosure feed — and none are voter-file derived. **Public disclosure is
  not the same as unrestricted use, and the federal layer carries a use restriction this paper
  relies on a safe harbour for.** 11 C.F.R. § 104.15, implementing 52 U.S.C. § 30111(a)(4),
  provides that information copied from a report filed under the Act "shall not be sold or used
  by any person for the purpose of soliciting contributions or for any commercial purpose,"
  with a narrow exception for using a political committee's own name and address to solicit
  that committee; § 104.15(b) reads "soliciting contributions" to cover any contribution or
  donation. **§ 104.15(c) is the provision this research sits under**: use of such information
  in "newspapers, magazines, books or other similar communications" is permitted so long as the
  principal purpose of the communication is not to convey contributor information for
  solicitation or other commercial purposes. This paper reports aggregates and names no
  contributor, so that test is met. FEC-derived individual records and donor–voter matches are
  not exposed to any solicitation or prospecting function: the tooling that once did so was
  removed on 29 July 2026. The full record of what existed and what went is
  `fec-contributor-data-use-memo.md`, an internal compliance record retained by the author. It is **not published**: it sets out a compliance exposure in the author's commercial tooling and the questions put to counsel, neither of which is research material. The removal itself is verifiable in the
  published code.
- **What is released, and the smallest cell in it.** Aggregate counts and shares only. Most
  published cells describe thousands to millions of people. Because a percentage printed over a
  small base lets a reader recover a count by arithmetic, the binding figure is not the smallest
  printed *base* but the smallest *derivable* cell: after withholding Idaho's minor-party
  crossover rows (Finding 3), that is **25 individuals** — the mixed-recipient share of Idaho's
  unaffiliated donors. Two smaller numbers appear and are not population cells. Appendix F's
  validation tables count **rated sample records**, not people, and those records are already
  published at row level, stripped of every name and voter id. Appendix G's bunching table
  prints a count of **1**, which is one *contribution* at a dollar amount — already public, by
  name, in the Idaho Sunshine filing it comes from. No individual-level records,
  names, or addresses appear in this
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
  concentration — on the primary specification Washington reads top-1% 46.6% pooled against
  41.2% federal and 43.5% state, a 3.1-point overstatement against the higher panel. (The
  corresponding all-tier trio is 47.7 / 42.4 / 43.8; a pooled figure and a panel figure must be
  read on the same specification, and Appendix F keeps the all-tier set separate for that
  reason.) It also matters conceptually, since the two systems are capped and administered
  differently (Appendix G).
- **Disclosure triggers, per panel.** These are **triggers, not floors**, and the paper calls
  them triggers for that reason. A contribution below one *need not* be itemized; it is not
  thereby invisible. Two routes put identified transactions underneath: a contributor's
  **aggregate** crossing the trigger makes the earlier small gifts itemizable, and many
  committees itemize voluntarily from the first dollar. The bullet on below-floor disclosure
  below shows that practice is common, so a contributor beneath the nominal figure may or may
  not be identifiable depending on the committee. Each panel's trigger is
  a property of its own statute. The $200 federal figure is **not** a uniform rule and does
  not apply to the state panels:

  | panel | mandatory itemization trigger | authority |
  |---|---|---|
  | Federal (FEC), all three states | contributor aggregate **> $200** per cycle/year | 52 U.S.C. § 30104(b)(3)(A) |
  | Washington (PDC) | contributor identity required above **$25** aggregate through 31 Mar. 2023, above **$100** from 1 Apr. 2023; occupation/employer above $100 then $250; **mini-reporting** committees exempt (≤$7,000 raised, ≤$500 per contributor) | RCW 29B.25.090(5) / .100(2) (formerly RCW 42.17A.235(5) / .240(2)); adjusted by WAC 390-05-400, WSR 23-07-004, eff. **1 Apr. 2023**; occupation/employer by WAC 390-16-034 |
  | New York (NYSBOE) | aggregate **> $99** must be itemized; $99 or less reportable in the aggregate | N.Y. Elec. Law § 14-102 |
  | Idaho (Sunshine) | aggregate **> $50** itemized by name and address; $50 or less reportable as a single item | Idaho Code § 67-6607 |

  Because every state floor is below the federal one, the state panels reach deeper into
  small-dollar giving. That alone predicts state panels with more donors, younger donors,
  and lower concentration — the direction of two of the three observed panel differences.
  This is a confound on the panel *comparison*; it does not affect any within-panel
  finding.

  **What the floors do and do not describe, measured (2026-07-28).** A statutory reporting
  threshold is not the same thing as the contents of the downloaded file, and this paper
  previously conflated them. Every floor above is a per-donor **aggregate**, so a donor who
  crosses it has *all* their gifts itemized including the sub-floor ones; and committees in
  practice disclose below what is required. The result is that none of the four layers is
  truncated at its floor:

  | layer | nominal floor | gifts at or below it | donor-aggregates at or below it |
  |---|---|--:|--:|
  | Federal (FEC) | > $200 / cycle | 89.9% | — |
  | Washington (PDC) | > $25, then > $100 | 84.5% (≤$100) | **53.5%** of matched panel donors (17.9% ≤ $25) |
  | New York (NYSBOE) | > $99 | 62.6% | — |
  | Idaho (Sunshine) | > $50 | 68.4% | — |

  The smallest matched Washington state donor total is one cent. So the honest statement is
  that this analysis **accepts every itemized record each agency publishes** and does not
  filter by any threshold; what the floors exclude is donors whose aggregate never crosses
  them, not gifts below them. This tightens the itemization bound on concentration (Appendix
  A, objection 5) and it complicates the panel comparison rather than the within-panel
  findings: the federal-vs-state difference cannot be attributed to a clean $200-vs-$100 gap,
  because the binding constraint is disclosure *practice* below the floor, which is not
  characterized by any statute and differs by layer.

  **Washington's floor is not constant across its own panel.** The $100 figure is current,
  but it dates only from 1 April 2023. The
  statutory threshold is **$25** (RCW 29B.25.090(5), the 1982 value), and WAC 390-05-400
  records **no intervening adjustment** — its "previous adjusted value, last set in 2016"
  cell for this row reads *n/a*. So across the WA PDC layer's 2016–2026 span the itemization
  floor was **$25 for roughly the first seven years and $100 for the last three**, and a
  single flat "> $100" describes neither. Three consequences, stated rather than buried.
  (i) The direction runs *toward* the paper's argument, not against it: a $25 floor reaches
  further into small-dollar giving than $100, so the WA state panel reaches deeper than the
  header table implies and the federal-vs-state disclosure gap for most of the period is
  $25-vs-$200, not $100-vs-$200. (ii) It makes the WA disclosure confound **time-varying**,
  which is a further reason the panel comparison is reported as descriptive rather than
  identified — the confound is not a constant offset that a fixed threshold correction could
  absorb. (iii) It is a reason to prefer New York for any panel comparison that has to be
  clean, since NY is the only state whose two layers are both exactly period-aligned and
  governed by one unchanged floor across the window.

  *(The amendment that set this threshold is WSR 23-07-004, effective 1 April 2023. WAC
  390-05-400 has since been amended again, WSR 26-01-209 effective 1 January 2026, without
  changing this row.)*
- **The common donor-total restriction, and what it does and does not identify
  (`diag_panel_harmonized.py`).** Every panel is also cut to donors with **more than $200 in
  total observed giving** — the highest of the four nominal floors — and both headline panel
  differences are re-read on it. This costs 60–69% of each state panel against 26–27% of each
  federal one. Two results, reported in Findings 1 and 2: the **age** gap survives in all
  three states (+9.8 / +11.7 / +12.2 points), 41% smaller in Washington; and the
  **concentration** ordering between layers **flips** in Washington and Idaho, so that federal
  money is the more concentrated layer in all three states among donors above a common total.

  **This restriction does not identify a statutory disclosure-floor effect, and the paper does
  not claim it does.** The cut is on a donor's total across the assembled panel, whereas
  itemization duties attach at the level of a committee, an election cycle, a calendar
  reporting period, or some combination — a person who gave $50 to each of five committees can
  clear $200 in this panel without having crossed the applicable threshold for any single one,
  and committees routinely itemize donors who never crossed it at all (the bullet above
  measures how routinely). At least four mechanisms therefore move together when the
  restriction is applied:

  1. statutory itemization rules;
  2. voluntary below-threshold disclosure, which the sources show is extensive;
  3. differences in how many committees or recipients a donor supports; and
  4. differences in cumulative giving over the panel's window.

  What the cut does supply is a robustness test on a common analysis population, which is how
  it is labelled at both use sites. A closer statutory simulation would build contributor
  totals separately per committee and per applicable reporting period, apply the rule in force
  at that time, and only then assemble the donor panel; even that would remain incomplete,
  because voluntary itemization practice varies by committee and is not recoverable from the
  disclosed data. That simulation is not run here.

  It is also worth stating what *cannot* be equalized this way. For an age difference there is
  no paired within-person comparison to run: age is a property of the person, so a donor present
  in both panels has the same age in both by construction. The panel age gap is inherently between-person. What the both-systems group
  supports is a between-group comparison, and Finding 1 reports it — including that it does
  not survive the restriction in Idaho.
- **Temporal alignment.** Panel comparisons are only identified if both panels cover the
  same years. Contribution-date coverage, by source:

  | state | federal layer | state layer | aligned as built? |
  |---|---|---|---|
  | Washington | FEC 2017–2026 | PDC 2016–2026 | **substantially overlapping, not identical — PDC carries 2016 as well** |
  | New York | FEC 2017–2026 | NYSBOE 2017–2026 | yes |
  | Idaho | FEC 2017–2026 | Sunshine **2023–2025** | **no** |

  Washington's PDC layer opens a year earlier than its FEC layer, so a small part of any WA
  panel difference is that extra 2016 cycle rather than a difference between the money systems.
  Only New York is exactly aligned as built.

  **The trailing edge of each window is not a closed book.** The 2026 cycle was **roughly half
  collected** in the Washington PDC layer when these panels were pinned, and it continues to
  accrue as filings arrive. Idaho's state layer closes in 2025 and is not exposed to this;
  New York's runs to 2026 as Washington's does, and its trailing-edge completeness is not
  separately measured here. Every figure reported in this paper is computed against a **pinned
  frame** rather than a live read, so the numbers here are stable and reproducible as printed.
  The consequence is for replication rather than for the findings: a run against a later PDC
  download will find the Washington state layer larger at its trailing edge than the frame used
  here, concentrated in the final cycle. The pin is deliberate — the alternative is a paper whose
  figures move without anyone editing anything.

  Idaho's Sunshine layer holds three years against the federal layer's ten (the earliest
  Sunshine contribution date is 2023-01-01). Both Idaho panels
  are therefore also rebuilt on the shared 2023–2025 window by
  `diag_donor_class_revisions.py --build-aligned`, which passes `date_min` / `date_max` to
  the matcher. Aligned, the federal panel falls from 23,303 to 14,848 donors and $42.1M to
  $18.4M; the state panel is unchanged, confirming Sunshine lies entirely inside the
  window. Every direction reported for Idaho survives alignment, and two strengthen: the age
  gap widens, and the state panel's donor-count advantage appears.
- **Panel overlap.** The two panels are not the same people under two rule sets:

  | state | federal | state | in both | Jaccard | 65+ state-only / fed-only / both |
  |---|--:|--:|--:|--:|---|
  | Washington | 147,745 | 217,114 | 49,943 | 0.159 | 32.9% / 53.6% / **59.6%** |
  | New York | 269,218 | 378,383 | 89,704 | 0.161 | 34.4% / 47.3% / **55.0%** |
  | Idaho | 23,303 | 23,613 | 5,780 | 0.141 | 46.0% / 66.5% / **67.6%** |

  In all three the both-systems group is *older than either single-system group*, so
  multi-system giving is itself age-graded and the age difference between panels is not a
  clean property of the regulatory layer. Idaho's near-equal panel counts (23,303 and
  23,613) reflect two largely disjoint populations of similar size, not a fixed donor pool —
  the 0.141 Jaccard rules that reading out.
- **The New York state panel.** NYSBOE publishes contributions as a transaction-level
  feed (data.ny.gov `4j2b-6a2j`, 12.6M rows back to 1999) carrying contributor last name,
  first name, and ZIP — everything the match key needs. `scripts/load_ny_contributions.py`
  loads the per-contribution rows; the repo's older NY adapter read the same feed but kept only
  roll-up columns and discarded contributor identity, which is why a New York state panel was
  once thought unavailable. Scope:
  individual contributors (`CNTRBR_TYPE_DESC = 'Individual'`) on Schedule A (monetary
  receipts, the direct analog of the FEC itemized individual file), NYSBOE **election
  cycles** 2018–2026 to align with the WA PDC window. **Cycle labels and transaction dates
  are not the same thing, and the paper uses both:** NYSBOE labels a cycle by the year of the
  election it funds, so the 2018 cycle carries transaction dates from 2017, which is why the
  panel's *date* coverage is described as 2017–2026 while its *cycle* coverage is 2018–2026.
  The two are the same records. That gives 3,954,090 contributions totalling $880.3M, of which
  $339.8M matches to a registered New York voter on the primary match
  specification ($379.5M on the retired all-tier key). Out-of-state donors are retained, as they
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
  | `STRICT_ZIP5_FULL` | surname + **full** first name + ZIP5 | 80.7–89.2% |
  | `STRICT_ZIP5_MID` | surname + first initial + middle initial + ZIP5 | 0.4–2.0% |
  | `STRICT_ZIP5` | surname + first initial + ZIP5 | 9.5–12.6% |
  | `RELAXED_ZIP3_MID` | surname + first initial + middle initial + **ZIP3** | 0.3–5.0% |

  Blinded validation (Appendix F) detected **no false match** in the 120 reviewed records
  drawn from the first tier — an estimated precision of 100% with a 95% Wilson interval of
  **96.9–100%** — against **47.9–71.7%** for the other three. The tiers are therefore not
  interchangeable, and the first tier alone is the paper's **primary specification**: every
  panel is built from it, and the all-tier figures are reported alongside as the superseded
  comparison rather than as the headline. The fourth tier is the
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
  found it. The WA PDC name-order mode is measured in Appendix F §F8 by rebuilding the key
  both ways against the roll — **7.2% of comma-less resident keys / 8.4% of their dollars**,
  against a 0.18% coincidence baseline — which is a different defect from the 0.1% / 0.8%
  organisation figure and should not be read as its analogue. It is a coverage defect: the
  donors it loses are slightly older than those matched, so it understates rather than
  manufactures Finding 1 in this panel. The key is four tiers, not the single "last name + first name +
  ZIP5" it is sometimes described as: adding the full-first-name tier raised Washington's
  all-tier matched count from 320K to 382K (+19%), and that tier is now the sole primary
  specification. Appendix F reports every headline estimate with the weaker tiers removed.
  Because ambiguity is dropped, the matched set is a floor.
- **Registration baselines, and why Washington's is pinned.** Party, age and turnout baselines
  use **active registrants** (`status_code='A'`) throughout — the same universe the matcher
  draws from, in all three states and every cut. **Washington's roll is additionally frozen as a
  dated snapshot**, and the reason is reproducibility rather than method: the table it derives
  from is rebuilt whenever new ballot-return data improves the VRDB precinct crosswalk, which
  brings previously unscoped voters into district scope and moves the denominator by a few
  thousand every few days. Left live, a reader re-running the verification script months from
  now would compute counts this paper does not contain and reasonably conclude it was wrong.
  The snapshot was taken on **2026-07-31** at **5,460,015** registrants
  (`scripts/pin_wa_donor_roll.py`, which refuses to re-pin without an explicit flag); New York
  and Idaho need no equivalent because their rolls are static extracts. NY is 91.9%
  active (12,448,081 of 13,540,558). **Crosswalk to the companion Washington papers.** Those
  read against the `voter_scores` `ld`-scope roll (5,460,015 rows, one per voter), which
  retains 412,361 inactive registrants; this paper deliberately does not, because a lead paper
  whose abstract promises the active roll should not then measure one of its three states
  against a wider one. The difference is small but one-directional, and worth knowing when
  reading the two together: inactive registrants vote less, so the wider roll depresses the
  Washington non-donor turnout rate and widens every Washington donor–non-donor gap by 2.7 to
  3.6 points, while the age multipliers move at most 0.09 — federal Silent 2.67 on the wider
  roll against the 2.58 published here. No direction differs between the two conventions.
  Idaho's statewide export carries **no
  active/inactive flag** — it is a current-roll extract, and the loader sets every row
  active so the shared matcher works — so for Idaho the two baselines coincide by
  construction and no active-only test is possible there. Using one baseline for both cuts
  rather than a different baseline for each moves no NY party skew by more than 0.4 points and no
  ID figure at all. Party of record is
  measured at the voter-file extract date, while contributions span prior years, so it is
  not necessarily the donor's party at the time of the gift.
- **Concentration estimator.** Donors are ranked by total matched dollars and split into
  100 **equal-count** buckets (`NTILE(100)`) over donors with `total_donated > 0`; the
  top-1% and top-10% figures are the top 1 and top 10 buckets' dollars divided by all
  matched dollars. Equal-count buckets are used deliberately: capped and round-number
  giving produces heavy ties, and `PERCENT_RANK` drifts from an exact decile at small N —
  it reads Idaho's top-10% as 69.0% rather than 70.8%. Gini is
  computed on the same donor totals by the rank-weighted formula. Appendix G reuses this
  identical estimator so its layer comparisons are commensurable with Finding 2.

  Two properties of `NTILE` are worth stating rather than leaving implicit. First, when the
  donor count is not divisible by 100 the first bucket
  holds ⌈n/100⌉ donors, so "top 1%" is *approximately* 1% — for Idaho's 23,303 federal
  donors, 234 rather than 233.03. Second, `NTILE` breaks ties on `total_donated`
  arbitrarily. Both were quantified rather than argued: against an exact cutoff that takes
  precisely n/100 donors' worth of weight, pro-rating the donor straddling the boundary, the
  top-1% figures move **−0.001 to −0.046 points** — largest in Idaho, where n is smallest.
  That movement is smaller than one decimal place in every panel, but smaller than a decimal
  place is not the same as invisible at one: Idaho's federal cell sits astride a rounding
  boundary, and is the one panel of the six whose printed digit differs between the two
  estimators. The bootstrap note in Appendix E gives that cell both ways. The number of
  donors sharing the boundary value is 1 to 26 depending on the panel, so tie order cannot
  move the estimate materially either. Both comparisons are recomputed and asserted on every
  run of `verify_donor_class.py`, which **fails** if any panel's two estimators ever diverge
  by more than 0.05 points. The published figures are the `NTILE` ones; the point is that the
  choice moves no finding, and in five of the six panels no printed digit either — not that
  it could never matter.
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
  at the cost of silent misassignment. Corporate, labor and trade PACs are left **unclassified**
  by design in both states, and they are a large share of state money. Unclassified is not
  the same as non-partisan: some such committees are strongly and consistently aligned, so
  calling them "genuinely non-partisan" would assert more than the coding supports. What the
  coding establishes is only that
  these recipients carry no party the sources publish and none this design can assign
  without guessing, and that assigning one would manufacture a crossover result rather than
  measure one. The consequence is that the unresolved pool is large and not missing at
  random, which is why the crossover tables are labelled exploratory.
- **The crossover classification, stated exactly.** `donor_party` classifies a *donor* by
  the set of their party-resolved recipients: `D_DONOR` (every resolved recipient
  Democratic), `R_DONOR` (every one Republican), `MIXED` (both), `OTHER` (none resolved).
  The Finding 3 tables report these as D-only / R-only / Mixed shares **of resolved
  donors** — the column headers say so, since a bare "D-only" invites reading the figure as
  a share of the whole row — and report the resolution rate separately. Finding 3 also
  carries a worst-case bound restating every row as a share of *matched* donors, which is
  the form comparable across rows. They are **not** dollar flows; the dollar-flow
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
  standalone and **378,388** after a roll join — 5 extra rows, the 5 duplicated ids that
  actually reach that panel. No reported figure is sensitive at that magnitude. *(An earlier
  draft gave the post-join count as 424,025, which is the retired all-tier panel total plus
  5 — an obsolete figure mistakenly written as fan-out. 53 duplicate ids cannot expand a
  join by 45,642 rows, and the arithmetic was the tell.)*
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

- **The shape of the donor class.** Bonica (2014) and the DIME database; Schlozman, Verba &
  Brady (2012); Hill & Huber (2017) — the donors-skew-old finding (Finding 1), and the closest
  methodological analog to the match used here. Bonica, McCarty, Poole & Rosenthal (2013) — the
  concentration result (Finding 2).
- **Unequal voice and its consequences.** Verba, Schlozman & Brady (1995); Gilens (2012);
  Gilens & Page (2014) — the normative stakes of a participation-and-money elite.
- **Party and the donorate.** Grumbach & Sahn (2020); Grumbach, Sahn & Staszak (2022) —
  donor-pool composition by party and group, the frame for Finding 3 (New York *and* Idaho).
  That article carries a published correction, Grumbach, Sahn & Staszak (2021), which was
  checked before relying on the original; it repairs a mangled character string in the
  introduction and changes no result.
- **Giving and voting as stacked participation.** Verba, Schlozman & Brady (1995) again, on the
  co-occurrence of participatory acts; the giving↔turnout overlap (Finding 4) is the
  individual-record instance, framed strictly as association.
- **Voter-file / individual-level method.** Ansolabehere & Hersh (2012); Hersh (2015). On match
  bias and the current-roll caveat, the tier and household sensitivities and the
  inverse-propensity re-weighting in Appendix F address the
  older/stable-address/uncommon-name skew directly.

### Record linkage as a method, and where this paper's design sits in it

*Every finding here depends on the validity of a person-level match, so the design is located
against the record-linkage literature rather than described on its own terms. The relevant point
is not that linkage is hard, but that the field has established results about **which** design
choices bias **which** downstream quantities — and this paper's choices should be placed against
them rather than defended in isolation.*

- **The probabilistic framework, and this paper's departure from it.** Fellegi & Sunter (1969)
  formalised linkage as a decision problem: estimate, for each candidate pair, the probability
  that it is a true match, and choose thresholds that trade false links against missed ones.
  Herzog, Scheuren & Winkler (2007) is the standard practitioner treatment. In political science
  the current standard implementation is Enamorado, Fifield & Imai (2019), which scales the
  Fellegi–Sunter model to millions of records, handles missing fields, and — most directly
  relevant here — is demonstrated on exactly this problem: **merging campaign-contribution
  records to nationwide voter files.**

  This paper does **not** use that approach. It uses a **deterministic** key (surname + full
  first name + ZIP5) with a **uniqueness requirement** on the roll side. The rule is intended
  to retain a high-specificity subset and to discard the ambiguous middle rather than assign
  it a match probability, but **it has not been calibrated against a probabilistic model**,
  and it should not be assumed to coincide with one: a Fellegi–Sunter-style model could score
  some full-name-plus-ZIP pairs well below certainty on account of common names, address
  mobility, data quality, or the composition of the blocking unit. What supports the rule here
  is the direct validation in Appendix F, not an equivalence argument. Two consequences follow,
  and the paper should be read with both in view. Recall is sacrificed — the matched set is a
  floor, which the paper states — and, more importantly, **the uncertainty is moved out of the
  estimator and into the sample definition.** Probabilistic methods *can* carry match
  probabilities forward into the analysis, though in practice analysts frequently threshold
  them into hard links and so give up the same thing; a deterministic rule forecloses the
  option, producing a set treated as certain whose error cannot be propagated, only bounded by
  validation. That is why Appendix F's hand-rating is load-bearing rather than decorative, and
  it is the most substantial methodological limitation of this design.

- **What linkage keys are available is set by statute, not by method.** Ansolabehere & Hersh
  (2017) show that address, date of birth, gender and name — any three of the four — link voter
  records at a rate close to nine-digit Social Security linkage, with roughly **2–2.5%
  discordance** in the reported comparison (about 98% of SSN-linked records also match on ADGN
  combinations, and the paper's later figures read ~97.5% against ~97.8%). That is the benchmark
  this paper cannot reach, and the reason is legal rather than technical: **the donor side has no date of birth, no gender and no verified address**, only
  a name and a ZIP from the contribution filing. Even on the roll side, Washington releases
  year of birth and not full date of birth (RCW 29A.08.710; Appendix B). So the key here is
  weaker than ADGN by construction, and the gap is a property of what disclosure regimes
  publish about donors.

- **Measured false-match rates, and the direction of their bias.** Bailey, Cole, Henderson &
  Massey (2020) is the most useful external calibration available. Hand-checking links from
  widely used algorithms, they find **15–37% are errors**; false links are **systematically related to
  the characteristics of the records being linked**, not random; and in their application the
  combined effect attenuates an intergenerational elasticity by up to **29%**.

  Both halves of that map onto this paper's own results and are the reason its numbers are
  reported the way they are. The measured precision of this paper's three initial-based keys
  (47.9–71.7%, Appendix F) sits at and beyond the bad end of Bailey et al.'s range, which is
  why they were dropped rather than reported alongside. And their finding that error is
  *systematic* is precisely what this paper observes twice over: every one of its 129
  confirmed household/relative false merges landed on an initial-based key, and the donors
  the clean-key restriction discards are **younger and less Democratic** than those it
  retains. That second fact is a selection effect on the estimand, not a measurement error,
  and it is why the paper reports both specifications instead of only the cleaner one.

- **Downstream bias, and what this design does not attempt.** Lahiri & Larsen (2005) show that
  naively analysing a linked file as though it were error-free biases regression estimates, and
  give an unbiased estimator conditional on known link probabilities. That correction is unavailable here by
  construction — a deterministic key produces no per-link probabilities to condition on.
  **Their specific regression correction is not directly applicable to these estimands, but
  the broader downstream-error problem is not thereby escaped.** Linkage error can bias shares,
  means, distributions and concentration measures just as it can bias slopes; descriptive
  quantities are not exempt.
  What differs is the available remedy. Since every finding here is a **descriptive share,
  mean or concentration statistic** on the matched set rather than a coefficient from a model
  fitted to linked data, this paper addresses the problem through validation of the match key,
  restriction to the key that validated, and sensitivity analysis — the blinded rating and
  by-tier precision estimates, the household-exclusion bounds, and the inverse-propensity
  re-weighting with its flat P(matchable) result, all in Appendix F — rather than through
  probability-weighted estimation. A future version of this design that fitted models to the
  linked file would need the Lahiri–Larsen machinery, and would therefore need probabilistic
  rather than deterministic linkage.
- **Contribution limits and the shape of the donor pool.** The statutory regimes tested in
  Appendix G, with individual per-election limits for the 2025–26 cycle:
  Idaho Code § 67-6610A (**$1,000** per election to legislative, judicial, and local
  candidates and **$5,000** to statewide candidates, primary and general counted
  separately, self-funding exempt; 2026 S.B. 1422 proposed raising these to $1,500 and
  $6,000 but was retained on the calendar);
  RCW 42.17A.405, recodified as RCW 29B.40.020 effective Jan. 1, 2026 — Washington's caps,
  indexed and administered by the Public Disclosure Commission, currently **$1,200** per
  contest to a legislative candidate and **$2,400** to a state executive candidate;
  **N.Y. Elec. Law § 14-114** ("Contribution and receipt limitations") — the provision that
  establishes New York's limits. Its non-family individual ceilings are stated as
  cycle totals divided equally between the primary and the general, so **per contest** they
  are **$3,000** Assembly, **$5,000** Senate and **$9,000** statewide (from cycle limits of
  $6,000, $10,000 and $18,000), alongside an extensive separate family-limit schedule
  computed on voter-enrolment multipliers, and a cost-of-living adjustment every four years.
  **§ 14-114(8)** separately provides that "[n]o person may contribute, loan or guarantee in
  excess of one hundred fifty thousand dollars within the state … in any one calendar year" —
  a **$150,000 annual aggregate ceiling that remains on the books but is not enforced**. Two
  things establish that, and they are not the same thing.

  *The judicial holdings are narrow.* The Second Circuit directed a preliminary injunction
  against §§ 14-114(8) and 14-126 as applied to an independent-expenditure-only committee and
  its donors in *New York Progress and Protection PAC v. Walsh*, 733 F.3d 483, 489 (2d Cir.
  2013), which the District Court then made permanent on the same as-applied basis, 17
  F. Supp. 3d 319, 323 (S.D.N.Y. 2014). A second court enjoined §§ 14-114(8) and 14-116(2) as
  applied to a 501(c)(4) and a recipient independent-expenditure committee in *Hispanic
  Leadership Fund v. Walsh*, 42 F. Supp. 3d 365 (N.D.N.Y. 2014). Neither reaches ordinary
  contributions to candidates.

  *The Board's non-enforcement is broader.* **NYSBOE Formal Opinion 2016 #1** (12 July 2016)
  presents as its first question whether the § 14-114(8) $150,000 aggregate limit is
  enforceable and concludes that it is not, recording that the Board "could no longer enforce"
  it "for contributions from individuals to independent expenditure committees, **candidates or
  other political committees**" — memorialising two directives of 22 May 2014, the second of
  which covers candidates and other political committees expressly. The Board's stated basis
  for reaching past the injunctions is its own forecast rather than a holding: the § 14-114(8)
  ceiling is "similar in function" to the federal aggregate limit invalidated in *McCutcheon
  v. FEC*, 572 U.S. 185 (2014), and "would likely be determined unconstitutional if
  challenged."

  So the ceiling is unenforced across the board as a matter of administrative practice, while
  the judicial invalidation is confined to independent-expenditure applications. Appendix G's
  table records it as **statutory but not operative in practice** on that basis, rather than as
  absent or as struck.
  **N.Y. Elec. Law § 14-116** is cited separately and for what it actually does — "Political
  contributions by certain organizations". It is **not** a categorical prohibition:
  § 14-116(2) permits a corporation, or an organization
  financially supported by one, to make political expenditures including contributions "in an
  amount not to exceed five thousand dollars" in the aggregate per calendar year, and
  § 14-116(1) names **limited liability companies** alongside corporations within the same
  section. So the New York rule is a $5,000 annual corporate ceiling plus an LLC
  ownership-disclosure requirement, not the state analogue of 52 U.S.C. § 30118. It is also not
  a source of the individual limits, which § 14-114 alone establishes;
  Tex. Elec. Code § 253.094, which bars corporate and labor-organization contributions —
  and, separately, the absence of any dollar limit on individual gifts to **non-judicial**
  Texas candidates, which § 253.094 does not address and which rests instead on the Texas
  Ethics Commission's *Campaign Finance Guide for Candidates and Officeholders*; the
  Judicial Campaign Fairness Act, §§ 253.151–253.176, is the exception that does impose
  limits;
  52 U.S.C. § 30116 (the federal per-election individual limit, **indexed biennially** —
  **$3,500** for 2025–26, and $3,300 / $2,900 / $2,800 / $2,700 for 2023–24 / 2021–22 /
  2019–20 / 2017–18, the earlier cycles this paper's federal layer also covers; Appendix G's
  truncation test uses the cycle-specific values as well as flat counterfactual ones); and
  52 U.S.C. § 30118 (federal prohibition on corporate contributions). **The three state
  systems relate to that prohibition in three different ways.** Federal law generally prohibits
  corporate treasury contributions to federal
  candidates. **Texas** generally prohibits corporate candidate contributions, as a
  third-degree felony under Tex. Elec. Code § 253.094 (with narrow exceptions for a
  general-purpose committee's administrative costs and for ballot-measure giving). **New York
  does not prohibit them — it limits them**, to $5,000 in the aggregate per calendar year
  under § 14-116(2), subject to the non-enforcement noted above for independent-expenditure
  committees. **Idaho permits** direct corporate contributions to candidates, subject to its
  candidate limits. New York in particular must not be grouped with Texas as a prohibition
  state; the § 14-116(2) text does not support it. On the constitutional architecture that
  leaves per-gift caps standing while removing any ceiling on a donor's total giving:
  *Buckley v. Valeo*, 424 U.S. 1 (1976) (contribution limits upheld, expenditure limits
  struck), and *McCutcheon v. FEC*, 572 U.S. 185 (2014) (invalidating the biennial
  aggregate limit). On the empirical consequence — that limits redistribute large-donor
  influence across vehicles rather than removing it: Barber (2016); La Raja & Schaffner
  (2015). Appendix G's result is consistent with that literature.

## Appendix E — Full distribution tables

**Matched-donor concentration, with bootstrap intervals — all six panels.** B=1,000
resamples per panel (`diag_donor_concentration_bootstrap.py`). All six panels are resampled;
quantifying only Washington's two would leave the paper's most prominent result with
uncertainty characterized for a third of the evidence, and the full set changes a claim — see
Finding 2's ordering test.

| panel | n resampled | top 1% | 95% interval | top 10% | 95% interval | Gini | 95% interval |
|---|--:|--:|---|--:|---|--:|---|
| WA federal | 147,745 | 41.2% | [38.6–43.4] | 74.2% | [73.0–75.2] | 0.815 | [0.806–0.822] |
| WA state | 216,732 | 43.5% | [38.7–48.9] | 75.3% | [73.2–77.7] | 0.821 | [0.806–0.838] |
| NY federal | 269,218 | 50.7% | [49.0–52.4] | 81.2% | [80.5–81.9] | 0.865 | [0.860–0.870] |
| NY state | 378,383 | 48.6% | [46.0–51.8] | 78.2% | [77.0–79.5] | 0.845 | [0.837–0.855] |
| ID federal | 23,303 | 37.2% | [30.7–43.8] | 70.8% | [67.7–74.0] | 0.789 | [0.767–0.812] |
| ID state | 23,613 | 40.0% | [31.7–49.4] | 71.0% | [66.8–75.4] | 0.799 | [0.770–0.829] |

*Two bookkeeping notes, both of which the verifier caught rather than an eyeball. **"n
resampled" is donors with a positive total**, which is why Washington's state panel reads
216,732 against the 217,114 in Finding 2: 382 PDC rows net to zero or below after refunds,
and the concentration estimator excludes them in both places. And the **point estimates in
this table are Finding 2's**, computed with `NTILE(100)`; the resampling routine uses a
rounded rank cutoff instead, which differs by at most 0.05 points (Appendix C quantifies the
estimator choice) — Idaho's federal top-1% is the one cell where that difference is visible
at one decimal, 37.16% against 37.12%. The intervals are the resampling routine's.*

Two things to read off this. **The concentration finding itself is robust everywhere** — the
lowest lower bound on any top-1% interval is 30.7%, so "a thin top stratum supplies a large
minority of matched dollars" holds in all six panels and **remains large under donor-level
resampling**. That is all resampling shows: the top 1% is itself a thin group, and an earlier
draft's gloss that the result "does not rest on a handful of top donors" does not follow from
these intervals, which say nothing about whether particular extreme donors matter. But **interval width tracks n**, and Idaho's panels are an order of magnitude
smaller than New York's: Idaho's state top-1% interval spans 17.7 points against 4.8 for
Washington's federal. That is why the cross-state *ordering* is testable only in part, and
why Idaho's point estimates should not be compared to the others as though they carried
equal precision. Within-panel comparisons and the two panels of a single state are
unaffected — Washington's state layer sits above its federal layer by less than the width of
either resampling interval, so that gap is not one this exercise can distinguish from
resampling noise. As in Finding 2, these intervals bound sensitivity to donor composition
under resampling and not linkage, coverage or disclosure error.

**Statewide (all itemized donors, not only matched), four states.** From
`cross_state_fec_money.py` over each state's FEC individual layer, donor-residence
filtered, FEC bulk files 2017–2026, mandatory itemization trigger > $200 throughout. This is the
one table in the paper where Texas appears, since aggregate donor figures need no voter
file:

| statewide concentration | WA | NY | TX | ID |
|---|--:|--:|--:|--:|
| top 1% → share of $ | 39.3% | 47.5% | 41.7% | 36.1% |
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
| WA federal | King (Seattle), 60,004 donors | 58.2% | Snohomish 5.3% (0.50×), Pierce 5.2% (0.45×); top 3 = **68.7%** |
| WA state | King, 92,886 donors | 52.0% | Pierce 7.8% (0.68×), Snohomish 5.4% (0.51×); top 3 = **65.3%** |
| NY federal | New York (Manhattan), 55,515 donors | 48.5% | Westchester 13.2% (2.59×), Kings 6.9% (0.56×); top 3 = **68.6%** |
| NY state | New York, 37,665 donors | 19.9% | Nassau 15.5% (1.93×), Suffolk 11.3% (1.30×); top 3 = **46.7%** |
| ID federal | Ada (Boise), 8,865 donors | 36.8% | Bonneville 11.9% (1.91×), Blaine 11.4% (**7.83×**); top 3 = **60.1%** |
| ID state | Ada, 8,812 donors | 50.3% | Kootenai 9.0% (0.84×), Canyon 5.1% (0.45×); top 3 = **64.4%** |

*Source: the six panel tables joined to each roll's county of registration; parenthesised
multipliers are dollar share ÷ active-roll share. Counties are used for all three states so
the comparison is between like units.
Re-derived by `verify_donor_class.py`.*

Two of the three states put federal money in a tighter geographic box than state money,
and in New York the gap is enormous — Manhattan's share of matched dollars falls by nearly
**29 points**, from about half of the federal layer to a fifth of the state one, with suburban
Nassau and Suffolk together overtaking it. Manhattan nonetheless remains the largest
single county in the state panel. Idaho inverts the pattern — Ada County's grip *loosens*
from 50.3% of state dollars to 36.8% of federal — not because Idaho's federal money is
broadly spread, but because it relocates to a second tier of counties outside the capital:
Bonneville (Idaho Falls) at 11.9% and resort-county Blaine at 11.4% from 909 donors, whose
**7.83×** multiplier is the largest single-county disproportion anywhere in this paper.
Concentration is the constant; which
geography does the concentrating depends on the money system. A plausible mechanism is
that state legislative seats are contested across far more of a state's territory than
its federal seats, so state money is raised more widely while federal money pools where
national donors live; this paper does not test it, and it should not be read as implying
that state legislative races are meaningfully contested everywhere — many are not (see
[`safe-seat-washington.md`](safe-seat-washington.md)).

**Donor pool versus registration, by district competitiveness (NY).** The Democratic
share of the donor pool exceeds the Democratic share of registrants in every band, in
*both* panels, and two-thirds of federal matched donors (177,918 of 269,218) — 62% of
state ones (233,275 of 378,383) — live in Solid districts:

| band | federal donor pool, D share | state donor pool, D share | registrants, D share |
|---|--:|--:|--:|
| Tossup | 58.7% | 51.3% | 40.4% |
| Solid | 72.6% | 66.9% | 56.1% |

*Bands are |predicted margin| over `forecast_predictions` NY CDs (Tossup <5, Solid ≥20),
registrant baseline = active registrants. Script: `diag_ny_electorate_extras.py`, which
reads the pooled match; the figures above are recomputed per panel, since a pooled read
would mix the two money systems this paper keeps separate everywhere else.*

Idaho shows the mirror image from the red side, on its state panel: 27 Solid-R legislative
districts hold 14,594 matched donors whose pool is **78% Republican to 13% Democratic**,
while the 8 Likely/Lean-R districts carry a far more balanced 47% R / 35% D across 9,019
donors (`diag_id_electorate_extras.py`; bands are Section V's registration bands, and the
same cut is asserted by `verify_donor_class.py`).

**Giving and turnout, side by side.** Non-donor denominators are active registrants in both
states.

| | donors | non-donors |
|---|--:|--:|
| WA super-voter share, federal panel | 88.0% | 54.7% |
| WA mean turnout propensity, federal panel | 0.977 | 0.796 |
| WA super-voter share, state panel | 88.9% | 54.2% |
| WA mean turnout propensity, state panel | 0.966 | 0.794 |
| NY generals voted, of last 4, federal panel | 3.10 | 1.85 |
| NY super-voter share (≥3 of 4), federal panel | 75.7% | 39.3% |
| NY generals voted, of last 4, state panel | 3.07 | 1.84 |
| NY super-voter share (≥3 of 4), state panel | 75.3% | 39.0% |

The give↔vote overlap is the finding least sensitive to which money system is examined:
on the super-voter share Washington's two panels differ by nine-tenths of a point and New
York's by four-tenths — even though New York's state panel draws on 109,000 more people
than its federal panel.

## Appendix F — Match validation and robustness

**Is matchability age-dependent?** This is objection 1, tested directly. P(a voter is
uniquely matchable) is computed on the roll itself, then donor shares are re-weighted by
its inverse:

| state | spread of P(matchable) | re-weighted result |
|---|---|---|
| NY, four age bands | **94.5%–95.4%** (0.9-pt spread) | 65+ donor share 47.9% → **47.9%** |
| WA, five generations | **96.3%–97.6%** (1.4-pt spread) | every multiplier unchanged to 2 d.p., **both panels** (federal Silent 2.48 → 2.48×, Gen Z 0.10 → 0.10×; state Silent 1.59 → 1.59×) |

A selection gradient that flat cannot generate the observed senior over-representation
**through this mechanism** — the claim is bounded, not categorical. What the test rules out is
age variation in *roll-side unique-key availability*. It does not rule out donor-side name completeness (how a contributor writes
their own name on a filing), residential mobility between the filing and the extract,
current-roll survivorship, or any other age-related selection operating outside the roll-side
key.
Two notes on the Washington row. First, P(uniquely matchable) is a property of the *roll*
and the match key, not of which contributions are used, so the same propensities re-weight
both panels; only the multipliers they act on are panel-specific. Second, **this row's raw
multipliers are not Finding 1's, and the whole of the difference is the panel.** Like the New
York row, it is computed on the **retained all-tier snapshots**, which are younger than the
primary panels: that takes the federal Silent multiplier from Finding 1's 2.58 to the 2.48
printed above, and the federal Gen Z multiplier from 0.04 *up* to 0.10. The denominators now
agree — both are active registrants, the test's additionally requiring a ZIP, which changes no
multiplier at two decimals. So the gap runs to a tenth on Silent and *upward* on Gen Z and
Millennial, and these multipliers should not be read against Finding 1's. What the test turns
on is the raw-to-re-weighted *difference* on a single basis, which is zero to two decimals
either way. An earlier
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
**80.7–89.2%** of matches there; the weakest ZIP3 tier carries 0.3–5.0%.

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

**Household false-merge sensitivity — run on both specifications.** A bounding exclusion,
replacing the withdrawn "small by construction" argument. A matched donor is flagged when
another active registrant shares their surname and ZIP5 — the configuration in which a
spouse's gift could be attributed to the wrong person. The exclusion is deliberately severe:
because the match key already required a unique first name, most flagged matches are correct,
so these rows bound the false-merge effect rather than correcting for it.

It is run on the **primary full-name panels** as well as the retained `_alltier` snapshots.
Household risk is lower on the primary specification by construction — all 129
household/relative false merges in the 480-record validation landed on an initial-based key, and
the primary specification contains none of those keys. But *no detected household error in a
480-record sample* does not establish that the sensitivity is unnecessary on the panels the
paper actually publishes, so both are reported.

**Primary specification (full-name key) — the published panels.**

| panel | variant | donors | top 1% | 65+ |
|---|---|--:|--:|--:|
| WA federal | all matched | 147,745 | 41.2% | 55.7% |
| | excl. surname+ZIP5 shared | 33,571 | 40.0% | 55.9% |
| | excl. surname+address shared | 69,336 | 39.2% | 56.1% |
| WA state | all matched | 217,114 | 43.5% | 39.0% |
| | excl. surname+ZIP5 shared | 42,333 | 43.6% | 41.3% |
| | excl. surname+address shared | 92,963 | 41.4% | 40.6% |
| NY federal | all matched | 269,218 | 50.7% | 49.9% |
| | excl. surname+ZIP5 shared | 70,770 | 48.3% | 50.2% |
| | excl. surname+address shared | 135,987 | 50.5% | 49.1% |
| NY state | all matched | 378,383 | 48.6% | 39.3% |
| | excl. surname+ZIP5 shared | 80,580 | 52.5% | 42.4% |
| | excl. surname+address shared | 165,145 | 49.2% | 40.4% |
| ID federal | all matched | 23,303 | 37.2% | 66.8% |
| | excl. surname+ZIP5 shared | 4,184 | 29.8% | 71.7% |
| | excl. surname+address shared | 9,025 | 33.0% | 70.7% |
| ID state | all matched | 23,613 | 40.0% | 51.3% |
| | excl. surname+ZIP5 shared | 4,037 | 37.2% | 58.9% |
| | excl. surname+address shared | 8,647 | 47.7% | 57.4% |

**On the primary panels the conclusion is the same as on the snapshots, and slightly
stronger for the age finding.** The senior share **rises** in all six panels under the
surname+ZIP5 exclusion — by up to 7.6 points (ID state) — so the age skew is not a household
artifact; excluding the at-risk configuration sharpens it. The top-1% share moves by at most
7.4 points (ID federal, the smallest panel) and rises in one of six. Every direction survives
in every panel.

**Superseded all-tier specification, for comparison.** Computed on the retained `_alltier`
snapshots, so it bounds the effect for the specification the paper no longer reports.

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

**Matchability by party, and why the party finding does not rest on it.** Finding 3's
incidence rates divide by all registrants of a party, so they confound donation behavior with
the chance that a party's registrants are uniquely identifiable under the full-name + ZIP5
rule. Parties differ in surname concentration, ZIP concentration and county distribution, and
age standardization does nothing about that. Measured directly (`diag_donor_review3.py`),
P(matchable) = P(record carries a first name, last name and ZIP) × P(that key is unique on the
roll):

| state | DEM | REP | unaffiliated | other | spread |
|---|--:|--:|--:|--:|--:|
| New York | 94.9% | 94.5% | 95.5% | 94.6% | **1.0 pt** |
| Idaho | 97.7% | 97.0% | 97.3% | 96.9% | **0.8 pt** |

*Active roll, age 18+. Name-and-ZIP completeness is ≥99.9% in every party of both states, so
the variation is almost entirely key uniqueness. The widest party gap inside any single age
band is 2.8 points in New York and 1.2 in Idaho; across the eight largest counties of each
state the party gap never exceeds 2.4 points.*

A 1.0-point spread is a multiplicative difference of about 1.01×, against
Democratic-to-Republican incidence ratios running 1.05× (NY state) to 1.73× (ID state) — so
differential matchability is roughly two orders of magnitude too small to account for them.
Re-basing the rate on *uniquely matchable* registrants rather than all registrants confirms it:
every figure rises by 3–4% and the ordering is untouched (NY federal DEM 29.2 → 30.8, REP
20.8 → 22.0; ID federal DEM 39.2 → 40.1, REP 24.1 → 24.9).

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
also the smallest (0.4–2.0% of matches). Row counts here sit a few dozen below the tier
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
its ≈90% stands as a single unstratified indication rather than an auditable estimate. It was rated by the author, as every pass in this appendix was. A
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

**Result — detected precision differs sharply by match tier in the validation sample.**

| tier | share of matches | n | Y | NC | NP | U | precision | Wilson 95% CI |
|---|--:|--:|--:|--:|--:|--:|--:|---|
| `STRICT_ZIP5_FULL` | 80.7–89.2% | 120 | 120 | 0 | 0 | 0 | **100.0%** | [96.9–100.0] |
| `STRICT_ZIP5_MID` | 0.4–2.0% | 120 | 86 | 33 | 1 | 0 | 71.7% | [63.0–79.0] |
| `STRICT_ZIP5` | 9.5–12.6% | 120 | 57 | 61 | 1 | 1 | **47.9%** | [39.1–56.8] |
| `RELAXED_ZIP3_MID` | 0.3–5.0% | 120 | 60 | 58 | 1 | 1 | **50.4%** | [41.6–59.2] |

*Y = same person; NC = confirmed different person; NP = probably different;
U = indeterminate. `precision` = Y/(Y+NC+NP); the sensitivity bound treating every
U as an error moves each tier by ≤0.5 points, because only 2 of 480 records were
indeterminate.*

No false match was detected on the full-name key, while the initial-based keys are closer to
coin flips. Requiring the complete first name, the surname, the ZIP5 and roll-uniqueness is
a far more restrictive identity condition than a first initial — but "none detected in 120
records" bounds the error rate at roughly 3% (Wilson 95% lower bound 96.9%); it does not
establish that the rate is zero, and a true namesake cannot be reliably distinguished by this linkage
regardless of sample size.

**Population-weighted precision, per panel.** The sample deliberately oversamples the weak
tiers by 30–300×, so its raw mean (67.6%) is *not* a panel estimate. Reweighting each
tier's precision by that tier's actual share of the panel:

**The 480-record design answered the question it was built for, and that is why a second draw
was needed.** Its purpose was to test whether precision differs *by match key*, and for that
question oversampling the weak tiers by 30–300× is the correct allocation: the tiers with the
least population carry the most uncertainty, so that is where the records belong. It answered
that question decisively — 100% on the full-name key against 47.9–71.7% on the initial-based
ones — and the answer retired three of the four tiers.

But allocation optimal for *discriminating between* tiers is not allocation optimal for
*validating* the one that wins. The full-name key carries **80.7–89.2%** of matches and received
25% of the sample: **20 records per panel**. That is the whole reason the panel-specific bound
is 16.1% rather than something tighter, and the whole reason Idaho needed a second draw. Read
that way the Idaho 204 is not a patch on a defect but the second stage of a two-stage design —
stage one locates the specification, stage two validates it at the population the specification
actually reaches.

**The same logic says what is still owed.** Washington and New York remain at 20 primary-key
records per panel, so **16.1% remains their operative panel-specific bound**, and only Idaho
has been carried to the second stage. That is stated here rather than left for a reader to infer
from the sample sizes: Idaho's party rows were taken to stage two because they were the rows that
failed, not because the other panels are finished.

| panel | donors with a positive total | weighted precision | bound (all U wrong) |
|---|--:|--:|--:|
| WA federal | 172,998 | **93.3%** | 93.3% |
| WA state | 268,741 | 90.4% | 90.4% |
| NY federal | 307,841 | 93.1% | 93.1% |
| NY state | 424,020 | 94.3% | 94.1% |
| ID federal | 27,196 | 92.6% | 92.6% |
| ID state | 27,250 | 96.5% | 96.5% |
| **donor-weighted, all six** | | **93.0%** | **92.9%** |

*One denominator note. The all-tier WA **state** panel appears in this appendix as
**269,204** in the tier and household tables and as **268,741** here, a difference of **463**.
These are two different denominators, not a discrepancy: 269,204 is the row count, and 268,741
is the count of donors with a **positive** net total, which is what the weighting runs over —
the all-tier analogue of the 382 non-positive rows disclosed at Finding 2's table for the
primary WA state panel. `diag_donor_review3.py` reproduces both. No other panel differs; the
remaining five have no non-positive rows.*

So the ≈90% figure the earlier pass reported was, at the panel level, roughly right — and
slightly conservative. But it concealed the structure that matters: **all detected errors in
the validation sample were on the ~11–19% of matches made on a first initial; none was detected
in the full-name tier.**

**By dollar band, precision is *lower* at the top.** 63.0% in the top decile of matched
dollars against 72.1% in deciles 2–10 (raw sample, tier-confounded). The gap runs the
direction that matters most — false matches are commoner among the largest
attributed totals — which is a further reason to prefer the full-name specification, in whose
top decile **no error was detected among the 60 records sampled there** (60 of 60 rated Y). As everywhere in this
appendix, that is a statement about detection in a sample, not an estimate of literal
population precision.

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
Idaho state layer. The equivalent name-order figure for WA PDC is now **measured rather than
estimated** — §F8 below rebuilds the key both ways against the active roll and finds **7.2% of
comma-less resident keys** affected, against a 0.18% coincidence baseline. Two earlier estimates
of that mode, both previously carried in this appendix, are withdrawn: they disagreed
with each other and neither could be independently confirmed.

**What follows for the paper, and what was done.** On this evidence the full-first-name tier
**was adopted as the primary specification**, and every panel in this paper was rebuilt on
it: it carries 80.7–89.2% of every panel, had no detected false match in the 120 blinded records
drawn from it, and — per the tier-sensitivity table above — moves every headline finding
*away* from the null rather than toward it (65+ share rises in all six panels, the
Democratic skew rises in all four party panels, concentration moves ≤1.3 points). The
superseded all-tier figures were therefore the ones closer to the null; they are retained as
`*_alltier` snapshots and reported alongside throughout, and where this paper quotes one it
says so. Two limitations are stated rather than buried, and the first is **not** a
measurement-error argument: the restriction discards 11–19% of matched donors, and that
discarded set is younger and less Democratic than the retained set, so **part of the movement
away from the null is a change in the target population rather than removal of error**. The
restriction also does not fix the Idaho organisation contamination for the two
middle-initial tiers, which needed a person/organisation filter on the Sunshine loader
independently (done 2026-07-27, from the source's own `Contributor Type` field).

**What this design cannot detect.** The rating catches "the donor is a different person
*with a different name*". It cannot catch a true namesake — a different person with the
*same* full first name, surname and ZIP5 — so the full-name tier's 100% is a ceiling on
detectable error, not proof of zero error. The complementary population measure is the
donor-side collision rate above (7–9% of full-name-tier matches sit on a key that also
pulls a different first name). A separate 8 records were flagged **partial merges**: the
matched voter genuinely is a donor, but the attributed total also includes a relative's
gift or a jointly-filed one. Those count as correct for identity — and therefore for the
age, party and composition findings — but they inflate that individual's dollar total,
which is the concentration-relevant residue. **Their tier split matters and was previously
not given**: 3 on `STRICT_ZIP5`, 3 on `RELAXED_ZIP3_MID`, 1 on `STRICT_ZIP5_MID`, and
**1 on `STRICT_ZIP5_FULL`** — so unlike the identity errors, this mode is *not* absent from
the primary key. One in 120 is a rate this sample cannot pin down, and the honest reading is
that a jointly-filed gift does not need the two names to differ, so the structural argument
that protects the primary key against household *identity* errors does not protect it here.
That single record is the only detected dollar-inflation event on the specification the
concentration finding runs on, and it is why the de-merge exercise above is retained despite
being stylized. The blind re-rate ticked the column on 1 record against the first pass's 8, so
the count rests on a single reading and should be read as indicative.

**Who adjudicated, and what the re-rating does and does not establish.** **The first two passes
of this validation are the author's; the third pass and the 204-record Idaho sample were rated
by an independent rater** (both below). No part of any adjudication was AI-assisted: the
match itself is deterministic local code, and the rating is a human reading two names and
deciding whether they are one person. The AI assistance disclosed for this project covers prose,
analysis code, citation checking and proposed robustness tests — it does not extend to any
judgement recorded here.

Two of the three passes are the author's, and the consequence has to be stated rather than
softened: **a second rating by the same person is test–retest reliability, not inter-rater
reliability.** It bounds how consistently one reader applies the criteria. It cannot detect a
criterion that reader applies wrongly but applies the same way twice, and no agreement statistic
computed between two passes by one person can.

**A third pass by an independent rater closed that gap on 2026-08-06**, and it is reported below
as inter-rater reliability rather than folded into the test–retest figures. It was previously
named here as an open item; it no longer is.

*Protocol for the re-rate.* 150 of the 480 records, drawn to put **75 on the full-name key** —
the block the primary specification rests on — and 25 on each initial-based key, with all 8
partial-merge and all 5 NP/U judgment calls forced in and every state-and-panel represented. The
second pass ran **blind to the first**: fresh opaque ids rather than the published `S####` ids,
so an earlier verdict could not be looked up; no stratum label and no first-pass verdict shown;
and evidence rows copied verbatim, so a divergence is a difference in judgement and never in what
was shown. The scorer was committed before any rating. Verdicts published at
[`reference/match_validation_human_verdicts_2026-07-27.csv`](reference/match_validation_human_verdicts_2026-07-27.csv).

*Result on the primary specification: it reproduces.* **75 of 75 full-name-key records were rated
Y on the second pass**, Wilson 95% [95.1–100.0], matching the first exactly. Zero divergences in
that block.

*Consistency overall.*

| scale | n | observed | Cohen's kappa | PABAK |
|---|--:|--:|--:|--:|
| four categories | 150 | 88.0% | 0.656 | 0.760 |
| collapsed binary (Y vs not) | 148 | 93.9% | **0.815** | 0.878 |
| — full-name key alone | 75 | **100.0%** | n/a (no variance) | 1.000 |
| — initial-based keys | 75 | 68–80% | 0.457–0.638 | 0.360–0.600 |

**These are test–retest coefficients and are labelled so wherever they appear.** Kappa is
undefined on the full-name block because both passes returned all-Y — zero variance, not zero
agreement, which is the prevalence artifact PABAK is reported for; PABAK there is 1.000.

*Every divergence runs in one direction.* All 18 disagreements are on initial-based keys, and in
**every** one the second pass was the more permissive: 6 NC → Y, 7 NC → NP, 3 NP → Y, 2 U → Y,
and **zero** cases where the second pass called a record worse than the first. Two things follow,
and neither is confirmation. The full-name block reproduced perfectly across two blind passes,
which shows the criterion is applied stably there — the records are not close calls. And on the
weak tiers the **published figures are the conservative ones**: reweighted on the same frozen
shares, the second pass gives donor-weighted precision **95.7%** against the published 93.0%, and
per-tier 64–68% against the published 47.9–71.7%. The qualitative finding — initial-based keys
are far less reliable than the full-name key — survives both passes. The exact weak-tier rates do
not, and are to be read as a range.

*Three limitations, stated.* Only 150 of the 480 were re-rated, so 345 records carry a single
reading. The 75 full-name rows are a subset of the original 120 rather than an addition, so that
block stands at 120 rated with 75 reproduced. And the second pass ticked `partial_merge` on 1
record against the first pass's 8 — most likely under-use of an unfamiliar column rather than
substantive disagreement, but it means the partial-merge count rests on one pass.

*What settled it — an independent rater, 2026-08-06.* The same 150 records were rated a third
time by someone other than the author, from outside the project, under the same blinded protocol
and in an unpublished id space, because `S####` and `H####` appear in committed files beside
their verdicts. This is **inter-rater** reliability, and it is reported separately from the
test–retest figures above rather than pooled with them. Scored by
`scripts/score_match_validation_human.py --rater rater2`; row-level ledger at
`reference/match_validation_rater2_verdicts.csv`.

**The full-name block is 75/75 Y in both the first pass and the independent pass.** The primary
specification's tier is confirmed unanimously by a rater with no stake in it, which is a stronger
statement than either the original pass or the author's re-rate could make alone.

| | first pass vs independent rater |
|---|---|
| full-name block | **75/75 Y in both**; Wilson [95.1–100.0] on the independent pass alone |
| agreement, all four verdicts | 76.0% observed, κ 0.516 |
| agreement, collapsed to same/different | **97.6% observed, κ 0.935**, PABAK 0.952 |
| donor-weighted precision, frozen shares | **91.0%** against the published 93.0% |
| the same, `NC`+`NP`+`U` all counted against | **90.4%** |

**Read the two agreement figures together, and in that order.** The four-category κ of 0.516 and
the binary κ of 0.935 are not in tension: they measure different things. The independent rater
used `U` on **23** records against the first pass's **2**, and of the **36** disagreements
**34 move toward less certainty** — 17 Y→U, 10 NC→NP, 5 NC→U, 2 Y→NP. Exactly one moves the other
way (U→NP) and exactly one is a substantive flip at unchanged certainty (NC→Y, on an
initial-based key). The axis there is *certainty*, not sameness: `Y` and `NC` are both confident
calls, so a move between them is a flip rather than a loss of confidence, while `NP` is a hedge
and `U` is no call. A shift that one-sided across 34 of 36 cases is a threshold convention, not a
disagreement about who is who. **The two raters agree about identity and differ about how to
label uncertainty**, and it is the binary coefficient that measures the first.

**That reading is testable on the paper's own pre-committed sensitivity, and it holds.** If the
eleven-fold rise in `U` were concealing disagreement about identity rather than expressing a
different threshold, counting every `U` against the match would move the donor-weighted figure a
long way. It moves it **0.6 points**, from 91.0% to **90.4%**, because the `U` verdicts sit
almost entirely in the weak tiers, which carry little donor weight. The **primary specification
is unmoved at 100.0% under both conventions**: all 75 of its records are confident `Y`, so the
harsh convention has nothing there to reclassify. The `NC`+`NP`+`U` sensitivity was fixed in the
scoring plan before any verdict existed; what was missing until now was its donor-weighted
aggregate, which is the one figure that could have tested this reading.

**The published figure is now bracketed from both sides, which is the most useful thing this pass
produced — and the bracket belongs to the RETIRED all-tier specification, not to the one this
paper runs on.** All three of 95.7%, 93.0% and 91.0% are donor-weighted across every tier,
including the initial-based keys the paper no longer uses. The author's re-rate diverged *more
permissively* than the published pass (95.7% donor-weighted); the independent rater diverges
*more cautiously* (91.0%). The published **93.0%** sits between them. **The primary specification
has no bracket because it has no spread**: the full-name block reads 75/75 `Y` in the original
pass, 75/75 in the author's blinded re-rate and 75/75 in the independent rater's — three
readings, one of them by someone with no stake in the result, unanimous. Two repeat readings that disagree with the original in opposite directions is
much better evidence that the published figure is not systematically optimistic than either
reading alone, and it is evidence the paper could not offer before this pass existed. The range
the weak-tier rates should be read across accordingly widens rather than narrows — which is the
honest direction for it to move.

The 204-record Idaho draw described in §F7 was rated in the same round and is scored there.

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
removed from the roll — deflating the old donor share. Neither mechanism can be shown to
dominate here, so the raw age skew cannot be called an "upper bound" on this basis: that
would assign a direction the evidence does not
support. Without a historical-roll or address-history analysis the net sign is unknown, so
the skew is described here as potentially biased by current-roll survivorship in an
undetermined direction. What remains ruled out is the specific mechanism objection 1
names — that rare names make the old easier to match — which the flat P(matchable) above
addresses.

### F7 — Error budget, spent against each finding

The main text states the two bounds and reports which findings survive which. This section
carries the tables and the measurements behind them. Nothing here is new analysis: it is the
cell-level detail behind results the article reports in a sentence, collected here so that the
article does not read principally as a treatise on deterministic linkage.

**The collision populations behind the mechanism argument.** Measured on the rolls, the
registrants sitting in colliding full-name-and-ZIP5 keys — the configuration a household merge
would require on the primary key, and which the uniqueness guard drops rather than resolves —
are **3.03%** of Washington's active roll, **5.11%** of New York's and **2.75%** of Idaho's. By
contrast the pool the initial-based keys were exposed to, registrants sharing a surname and ZIP5
with someone whose first name differs, is **76.7%, 77.0% and 82.6%** of those rolls. That ratio is
the quantitative form of "129 of 129 landed on the weaker keys." It bounds the mechanism where
both parties appear distinctly on the current active roll and says nothing about a namesake who is
inactive, has moved, or was never registered.

**Adversarial deletion, at both budgets.** Each statistic is recomputed after deleting the budget
share of the panel entirely from the bucket that supports the finding.

| panel | 65+ share, 3.1% | at 16.1% | registered-D share, 3.1% | at 16.1% |
|---|--:|--:|--:|--:|
| WA federal | 55.7 → **54.2** | → 47.1 | *party unpublished* | |
| WA state | 39.0 → **37.1** | → 27.3 | *party unpublished* | |
| NY federal | 49.9 → **48.2** | → 40.2 | 63.6 → **62.5** | → 56.7 |
| NY state | 39.3 → **37.3** | → 27.6 | 57.1 → **55.8** | → 48.9 |
| ID federal | 66.8 → **65.7** | → 60.4 | 20.4 → **17.9** | → **5.2** |
| ID state | 51.3 → **49.7** | → 41.9 | 21.6 → **19.1** | → **6.5** |

*`diag_match_error_sensitivity.py`; re-derived at both budgets by `verify_donor_class.py`. Each
cell is a worst case, not an estimate. At 16.1% that is a worst case of a worst case — for
Idaho's federal panel it deletes about four in five of the panel's registered Democrats.*

**Why concentration is not in that table.** Adversarial *removal* is degenerate for a top-share
statistic: deleting the largest 3.1% of donors deletes three times the top-1% population by
construction, and the surviving top 1% is a different, far smaller set, reading 41.2% → 9.2% on
Washington's federal panel. That is arithmetic about the estimator rather than a statement about
match error. Concentration is therefore stressed a different way — **de-merge the largest 3.1% of
donors into two equal halves each**, leaving total dollars unchanged and only reordering the
ranking:

| panel | top 1% of dollars | under equal two-person de-merging |
|---|--:|--:|
| WA federal | 41.2 | **33.8** |
| WA state | 43.5 | **36.9** |
| NY federal | 50.7 | **42.4** |
| NY state | 48.6 | **41.2** |
| ID federal | 37.2 | **30.5** |
| ID state | 40.0 | **33.9** |

**Read this as a stress test, not as spent error budget**, and the distinction is not pedantic:
the residual errors the budget bounds need not be household merges at all, the equal-halves split
is a stipulation rather than a measurement, and the household mechanism it imitates was detected
on the weak tiers rather than on the primary key. What the primary key did produce is one
**partial merge** in 120 rated records — the matched voter is genuinely a donor but the attributed
total includes another person's gift — which is the one detected instance of exactly the
dollar-inflation this exercise models.

**The second Idaho draw, and why the design needed one.** Because Idaho's party rows are the one
result that fails the panel-wide bound, a fresh strict-key sample was drawn on 2026-08-01 for each
Idaho panel: **204 records, 102 per panel**, all on the primary full-name key, balanced across
registered Democrats, Republicans and unaffiliated registrants (68 each) and across the top dollar
decile and the rest (102 each). It excludes by voter id every record rated in the 480-record pass,
and it uses a fresh opaque id space, because the published `S####` and `H####` ids appear in
committed files *beside their verdicts* — a rater handed either could look up a prior answer. It
was rated by someone other than the author under the same blinded protocol, and the result is
reported at the end of this subsection.

**The analysis was pre-specified — and the pre-specified plan itself contained the pooled-bound
error, one level down. Found by an external referee; corrected 2026-08-14.** The draw is a
deliberately **disproportionate stratified** sample, not a simple random sample of the panel, so
pooling its 102 records into one binomial bound would not bound the panel's error rate — the plan
said so, and then bounded each party stratum at its pooled n = 34 anyway. But the party stratum
is itself two deliberately balanced dollar-band cells of **17**, while the top decile is roughly
a tenth of the donor population: the 34 records over-weight the top decile about five-fold, so an
n = 34 binomial bound is not a bound on the party stratum's error rate, for exactly the reason
the plan refused to pool the 102. The design-respecting construction is per **party ×
dollar-band cell**. With zero errors in both of a party's cells, any design weighting of the two
equal cell bounds equals the cell bound, **18.4%**; a conservative simultaneous construction
(each cell at 97.5%) gives **22.8%**. What the design supports:

| stratum | records | zero-error Wilson 95% upper bound |
|---|--:|--:|
| one party × dollar-band cell, one panel — **the operative bound** | 17 | **18.4%** |
| one registered party, one panel — *retired: pools its two dollar-band cells* | 34 | 10.2% |
| one dollar band, one panel | 51 | 7.0% |
| one panel, composition-reweighted | 102 | 3.6% — an estimate, not a binomial bound |
| *what the current evidence supports* | *20* | *16.1%* |

(The dollar-band row is licensed the same way the cell row is — the draw balanced the two
bands by design, so a within-band bound is a construction the design supports. It is reported
for completeness: no finding in this paper rests on a dollar-band error rate.)

**A party-specific bound is the one the Idaho finding needs** — and on this design that means
the party × dollar-band cell bound in the row above, not the retired pooled party stratum —
because the vulnerability is specifically whether match error inflates the *Democratic* share
rather than the panel as a whole. Applied directly, and as a worst case that deletes that share of the panel's registered
Democrats outright, a clean Democratic stratum would take Idaho's federal panel from 20.4% to
**16.7%** and its state panel from 21.6% to **17.6%** at the 18.4% bound — and to **15.8%** and
**16.7%** at the simultaneous 22.8% — all still well above the 11.8%
registration share. (An earlier version printed 18.4% and 19.4% here: the same deletion at the
retired 10.2% pooled bound.)

**This is a different construction from the deletion table above, and the difference is what the
Idaho result turns on.** The table applies the budget *panel-wide*: it deletes
`budget × panel size` records, all of them from the bucket supporting the finding, which is why
Idaho's federal row falls to **5.2%** at a 16.1% budget — that deletion removes about four in
five of the panel's registered Democrats. The stratum construction applies the bound *within
the stratum*, holding the panel denominator fixed. The two are not the same operation on a
smaller budget, and the panel-wide one **fails decisively at the corrected bound**: at 18.4% it
takes Idaho's federal registered-Democrat share to **2.5%** and the state panel to **3.9%**,
both far below the 11.8% registration baseline.

So the Idaho party result stands on the licence to bound per stratum, and that licence
should be stated rather than assumed. It rests on the design: the second draw was stratified on
registered party *precisely because* the vulnerability is party-specific, 34 records were rated
in each party cell of each panel — 17 in each of its dollar-band cells — and a bound computed
within those cells is the quantity the design was built to produce. A panel-wide budget assumes
instead that every error the panel
could contain lands on Democrats — defensible as a stress test, which is what the table above
is for, but not the bound this sample supports. A reader who prefers the panel-wide construction
should read both Idaho party rows as unresolved; New York's
result is unaffected either way, and clears both constructions at both budgets.

The scoring plan is fixed before the rater begins, so it cannot be chosen after the verdicts are
seen: errors reported by panel × party stratum and by dollar band, intervals computed within
stratum, the pooled panel figure reported only after reweighting to the panel's actual party
composition and labelled a precision estimate, and the Democratic-stratum bound applied to the
party result. Verdict handling is fixed with it, on the same convention that scored the published
480: `NC` and `NP` count as errors and `U` is excluded from the denominator but reported, with
**NC only** and **NC + NP + U** pre-committed as sensitivities; a `partial_merge` tick is a
dollar-attribution issue rather than a misidentification and is reported separately, since the
party result turns on identities. The plan committed in advance that if the rating found an error, the "no detected false match on
the primary key" claim would become a measured low rate rather than an undetected zero — a larger
revision than it sounds, and one that would have reached the abstract. It found none. The sample is drawn by
`diag_match_validation_stratified.py`, restricted to Idaho and to the primary key, stratified on
registered party, and excluding every previously rated record by voter id; the rater's brief and
the full scoring plan are in `idaho-validation-rater-instructions.md`.

**Rated and scored, 2026-08-06: zero errors.** The draw was rated by someone other than the
author under the blinded protocol above and scored by `scripts/score_idaho_validation.py`, which
was written and committed before any verdict existed. **All 204 records were rated Y.** There is
no error in any stratum, on the published convention or on either pre-committed sensitivity —
including the harshest, in which every `U` is counted against the match. Three records on the
Idaho state panel carry a `partial_merge` tick and are reported here separately, as the plan
requires: the matched voter genuinely is a donor and the attributed dollar total sweeps in
another person's gift, which is a dollar-attribution problem and not a misidentification.

**What that changes, and what it does not.** The stratum bounds in the table above are
properties of the design, not of the verdicts, and a zero-error result is
what makes them the operative bound rather than a floor to be raised. So the deletion exercise
rests on a **measured** clean Democratic stratum rather than an assumed one: the
worst-case Idaho figures of **16.7%** federal and **17.6%** state are
the consequence of a rating that found nothing rather than of a bound applied in the
absence of one. The claim that survives is deliberately the weaker of the two available: **no
false match was detected on the primary key in 204 Idaho records**, with a 95% upper validation
bound of 18.4% per party × dollar-band cell, rather than a claim that the error rate is zero. A
sample of 17 per cell cannot
establish that, and the bound is reported precisely because it cannot — and, like every bound in
this appendix, it bounds *detectable* error under this protocol, not the structurally
unobservable exact-namesake case.

### F8 — How far the linkage reaches, and what it does not

**The strict-key match rate, per panel.** Distinct contributor keys in each contribution layer
on the primary specification's own key — `(surname, full first name, ZIP5)`, parsed exactly as
the matcher parses it — and the dollars those keys gave. These are **parsed keys, not verified
donor identities**, which is why the paper does not call the result recall.

| panel | distinct parsed in-state contributor keys | matched | **strict-key match rate** | in-state itemized $ | matched $ | **$ attached to matched keys** |
|---|--:|--:|--:|--:|--:|--:|
| WA federal | 298,645 | 147,745 | **49.5%** | $646.1M | $346.3M | **53.6%** |
| WA state | 555,922 | 217,114 | **39.1%** | $330.0M | $122.5M | **37.1%** |
| NY federal | 570,600 | 269,218 | **47.2%** | $2,066.2M | $1,015.7M | **49.2%** |
| NY state | 786,372 | 378,383 | **48.1%** | $725.4M | $339.8M | **46.8%** |
| ID federal | 43,194 | 23,303 | **53.9%** | $76.2M | $42.1M | **55.3%** |
| ID state | 41,497 | 23,613 | **56.9%** | $22.3M | $13.6M | **61.1%** |

*Both denominators are restricted to **in-state** keys and in-state dollars, and they must
be: the per-state FEC loads filter on donor residence and are 100% in-state, while the
state-disclosure loads do not — the NYSBOE layer is **23.6%** out-of-state, WA PDC 5.9% and
Idaho Sunshine 6.1%, measured over rows carrying a contributor name, which is the only
universe a linkage could reach. An out-of-state key cannot match the state's own roll, so an
unrestricted denominator would charge the state panels for keys no linkage could reach.
Keys and dollars are restricted the same way so the two columns share a basis. Script:
`diag_match_rate.py`; re-derived by `verify_donor_class.py`.*

**The non-match cascade, over resident keys.** Relaxing exactly one condition at a time, as a
priority cascade so the buckets partition the residual. Denominators are restricted to **in-state**
keys, matching the strict-key match-rate table above. An out-of-state key has no
counterpart on that state's roll by construction, so an unrestricted denominator inflates the
final column and puts this table on a different basis from the one above it.

| panel | matched | 2+ on roll (guard) | inactive or removed | same name, different ZIP | name-form mismatch | no roll counterpart |
|---|--:|--:|--:|--:|--:|--:|
| WA federal | 49.5% | 1.6% | 1.2% | **25.2%** | 6.7% | 15.7% |
| WA state | 39.0% | 1.3% | 1.0% | **25.1%** | 6.9% | 26.7% |
| NY federal | 47.2% | 2.3% | 2.3% | **26.8%** | 4.9% | 16.5% |
| NY state | 48.1% | 2.7% | 1.4% | **24.6%** | 6.4% | 16.7% |
| ID federal | 53.9% | 1.8% | — | **17.7%** | 9.0% | 17.5% |
| ID state | 56.9% | 1.6% | — | **13.8%** | 12.4% | 15.4% |

*`diag_residual_decomposition.py`; re-derived by `verify_donor_class.py`. Each key is assigned
to the first bucket it satisfies, so rows sum to 100%. "Inactive or removed" means the same key
matches a registrant whose status is not active — unavailable in Idaho, whose export carries no
status flag, so those keys fall through to later buckets. "Same name, different ZIP" means
surname and full first name match an active registrant at another ZIP5. "Name-form mismatch" means
surname, first *initial* and ZIP5 match but the full first names differ. On this resident basis
the matched column reconciles with the match-rate table to within 0.1 point in every panel; under
the earlier unrestricted denominator it did not.*

**The Washington PDC name-order measurement.** The defect and the decision are stated in the main
text; the instrument is this. Every comma-less PDC contributor key is rebuilt both ways — forward
`(token 1 = surname, token 2 = first name)`, which is what the matcher does, and reversed
`(last token = surname, token 1 = first name)` — and each is resolved against the active roll
under the same uniqueness guard the primary specification uses.

| | keys | share |
|---|--:|--:|
| comma-less rows, of all PDC person rows | 2,628,373 | **99.9%** |
| distinct resident keys | 555,107 | |
| resolve forward only (matched today) | 216,977 | **39.1%** |
| resolve reversed only | 39,755 | **7.2%** |
| resolve both (ambiguous) | 65 | 0.01% |
| resolve neither | 298,310 | |

*The 555,107 keys here and the 555,922 in the match-rate table are the same universe counted
either side of the comma: 846 keys arise from comma-bearing rows, 31 of those are also reachable
from a comma-less row, and 555,107 + 846 − 31 = 555,922. Both use the matcher's parse verbatim,
with no whitespace normalisation.*

Dollars on the reversed-only keys are **$27.0M**, **8.4%** of the layer's resident itemized
dollars. Two controls make the figure interpretable. The forward column reproduces the published
panel — 216,977 keys against the panel's 217,114 matched donors, and a 65+ share of 39.0% against
the published 39.0% — so the instrument is measuring the matcher and not something adjacent. And
the **placebo** rules out coincidence: on the FEC layer, whose names are filed `LAST, FIRST` so the
true order is known, deliberately swapping the halves still resolves uniquely for only **0.18%**
of keys (523 of 298,645). The observed 7.2% therefore exceeds the coincidence rate by 7.0 points.

This supersedes two earlier estimates of the same mode, both **withdrawn**: one produced by the
originating script's own parser, which the verification pass could not independently confirm, and
one from a surname-vocabulary heuristic that measured a different thing and was expected to
over-detect, since a genuinely rare surname is absent from the roll's vocabulary too. Their values
are recorded in the corrections ledger rather than restated here, so that no retired figure sits
in the paper beside the measurement that replaced it. `diag_wa_pdc_name_order.py`.

## Appendix G — Contribution limits and the top of the distribution

A natural explanation for Idaho's lower matched top-1% share is that state contribution
limits compress the very top of the state-money distribution. This appendix tests the
mechanical version of that claim (`diag_contribution_limits.py`), finds it does not hold, and
sets out at the end how narrow the surviving conclusion is.

The test does not require new data. Idaho residents appear in **two money systems at
once**, under two different rule sets, so the regime can be varied while the state context
is held broadly fixed. **It does not hold the donor population fixed**, even approximately:
the two panels overlap by a Jaccard coefficient of only 0.14–0.16 (Appendix C), so they are
predominantly different people. What is common to the two layers is the state, not the
donors.

**G1 — the statutory regimes.** Individual contributions to a candidate, per election,
2025–26 cycle:

| layer | legislative | statewide | ceiling on a donor's *total* giving |
|---|---|---|---|
| Idaho state (Sunshine) | **$1,000** | **$5,000** | none |
| Washington state (PDC) | **$1,200** | **$2,400** (state exec.) | none |
| New York state (BOE) | **$3,000** Assembly / **$5,000** Senate | **$9,000** | **$150,000/yr on the books** — N.Y. Elec. Law § 14-114(8), enforcement preliminarily enjoined as applied (below) |
| Texas state (TEC) | **no dollar limit** | **no dollar limit** | none |
| Federal (FEC) | **$3,500** (2025–26; $2,700–$3,300 in earlier cycles of this layer) | same | none since 2014 |

Note the direction of the caps: Idaho's and Washington's legislative limits are *lower*
than the federal per-election limit. The federal aggregate ceiling was struck in
*McCutcheon v. FEC*, 572 U.S. 185 (2014). **New York's aggregate limit is the one row that
needs care, and reads neither as a plain figure nor as "none".** N.Y. Elec. Law
§ 14-114(8) still provides that "[n]o person may contribute, loan or guarantee in excess of
one hundred fifty thousand dollars within the state … in any one calendar year," but the
Second Circuit reversed the denial of a preliminary injunction against it as applied to
contributions to an independent-expenditure-only committee in *New York Progress and
Protection PAC v. Walsh*, 733 F.3d 483 (2d Cir. 2013). So the ceiling is statutory and
partly unenforced; the paper treats New York as having no *operative* ceiling on a donor's
total for the purposes of this appendix, and says so rather than describing the statute as
absent.

**Corporate treatment.** The three systems differ, and New York is the one most often
described wrongly. Federal law generally prohibits corporate treasury contributions to federal
candidates (52 U.S.C. § 30118). **New
York instead imposes a limit**: § 14-116(2) permits a corporation, or an organization
financially supported by one, to make political expenditures including contributions "in an
amount not to exceed five thousand dollars" in the aggregate in a calendar year — a ceiling,
not a ban. **Limited liability companies are named in § 14-116(1) alongside corporations**
and are treated within that section rather than under a separate categorical rule; the
statutory treatment of LLCs is stated here separately from the corporate rule because the two
have been amended on different tracks. Texas generally prohibits corporate candidate
contributions, as a third-degree felony under Tex. Elec. Code § 253.094. **Idaho permits
corporate candidate contributions subject to its candidate limits**, and caps nothing at all
on ballot-measure committees. (Federal law does **not** forbid *PAC* contributions to
candidates — multicandidate committees may give, subject to their own per-election limit. The
corporate rule is the real distinction.) Statutes and authorities in Appendix D.

**G2 — bunching at statutory values.** Bunching on the round statutory value is unmistakable
in Idaho's state filings:

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

A 15× spike on the round value and a cliff immediately above it is what a binding constraint
looks like, and the premise of the original explanation holds to that extent: **some** cap is
real and donors hit it. **What the table does not establish is which cap.** Idaho's $1,000
figure is the limit for legislative, judicial and local candidates; a $1,000 gift to a PAC or
a state party committee is not governed by it, and the Sunshine rows carried here do not
identify the recipient's type or the election designation. So the spike is evidence of
bunching on a round statutory value, not proof that every one of those 6,797 gifts sat against
a binding *legislative* cap, and the row is not labelled that way.

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

Two readings, both against the original explanation. First, the capped *state* layer is
**more** top-heavy than the *federal* layer — but the two states' comparisons are not
equivalent units and are no longer presented as equal evidence. **Idaho supports a
persons-only comparison: 39.7% state against 36.1% federal**, like for like. **Washington does
not**: its PDC file names people as "LAST FIRST", so no reliable persons-only cut exists, and
its 44.4% is an **all-filer** figure including organizations set against a persons-only federal
39.3%. So: *Idaho's persons-only comparison and Washington's all-filer comparison both point
the same way, although the Washington units are not equivalent.* Idaho's all-filer figure
(56.4% against 36.1%) points the same way again, on the same non-equivalence caveat. Second,
the persons-only Idaho state figure (39.7%, Gini 0.800) sits close to Finding 2's matched
**40.0% / 0.799**, a reasonable check that these layer definitions match the paper's. The
two are no longer expected to coincide exactly: this appendix's layer cut spans every
itemized filer, while the matched panel is now restricted to the full-first-name key.
Restricting the Idaho federal layer to Sunshine's 2023–2025 window leaves the direction
intact (matched federal aligned top-1% **34.7%** against state **40.0%**).

**G4 — a stylized clipping exercise, and why it carries no statutory label.** This section
trims dollar amounts in Washington's federal layer at a series of thresholds. **It is a
winsorization exercise on an unchanged transaction file, not a simulation of any contribution
limit**, and its rows therefore carry no statutory label. The reason is structural: a statutory limit caps a donor's **aggregate** giving to one recipient committee
**per election**, not each transaction independently, and the FEC individual file pools
recipients — candidate committees, PACs, state party committees and national party committees
— that are governed by **different** limits. Two fields needed to respect any of that are
absent from the loaded data: the recipient's **type**, and the primary/general **election
designation**. So no row below is "the law as it stood", and the cycle-varying row in
particular is not historically exact.

| threshold | per-transaction top 1% | per-aggregate top 1% | top 10% (per-tx) | $ retained (per-tx) |
|---|--:|--:|--:|--:|
| unclipped (actual) | 39.3% | 39.3% | 72.3% | $646M |
| $5,000 | 32.2% | **30.1%** | 68.7% | $571M |
| $3,500 (flat) | 31.2% | **28.4%** | 67.7% | $554M |
| cycle-varying federal amount | 30.9% | — | 67.4% | $548M |
| $1,000 | 26.4% | **22.0%** | 62.9% | $454M |

*`diag_contribution_limits.py` G4/G4b/G4c. **Per-aggregate** clips donor × recipient-committee
× cycle totals before summing, which is materially closer to how a limit attaches; it is the
column that matters for reading the exercise at all. Clipping the aggregate bites **2.1 to 4.3 points
harder** than clipping transactions, because a donor who splits a large sum into several gifts
to the same committee is untouched by per-transaction clipping. Even the aggregate column is
stylized: it clips per **cycle**, whereas a candidate committee's primary and general count
separately (so it overstates the bite there), and it applies one number to every recipient type
(so it misstates the bite for PACs and party committees). The cycle-varying row uses the federal
individual per-election amount in force in each cycle — $2,700 in 2017–18, $2,800 in 2019–20,
$2,900 in 2021–22, $3,300 in 2023–24, $3,500 in 2025–26, from the FEC's archived charts — which
corrects a flat-$3,500 anachronism but does **not** make the row a legal counterfactual, for the
aggregation and recipient-type reasons above.*

Read only as arithmetic, clipping is not a small operation: at a $1,000 threshold the top-1%
share falls from 39.3% to 22.0–26.4% depending on the level at which the clip is applied.

**What that number cannot be used for.** Comparing Idaho's observed 39.7% against Washington's
clipped federal figure, and reporting the difference as points "above what pure truncation
predicts", would treat the clipped figure as a legally matched counterfactual for Idaho's
regime. It is not: the threshold is not Idaho's law applied to Idaho's recipients, the two
layers are different people in different years under different disclosure floors, and the clip
level itself moves the answer by four points. No difference between an observed layer and a
clipped layer is quoted in this paper.

**What replaces the original explanation.** The account below is offered as a reading
consistent with the evidence, not as something G4 demonstrates. A cap binds at the moment of
the gift, and its compression can be undone downstream. Nothing in Idaho limits a donor's
*total*, so the same people can reach the cap again and again across many recipients; and the
tail can displace into vehicles the state does not cap — 41.9% of Idaho's state dollars sit in gifts above $5,000,
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
mechanical clipping of dollar amounts does not reproduce the observed ordering of the state and
federal concentration estimates.** G4 varies a ceiling on an unchanged transaction file; it
therefore speaks to arithmetic, not to law or to behavior. Real contribution limits also change
how many recipients a donor gives to, when, through which vehicle, and in what amounts, and
none of that is held fixed in the world G4 describes. Two stronger claims are **not** made:
that contribution caps do not explain the cross-state differences, and that G4 quantifies what
a cap would do. Neither follows from this design.

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

## Data, code, and reproduction

`scripts/verify_donor_class.py` re-derives the designated results in this paper from the built
panel tables, reaching the databases with from-scratch SQL and importing no analysis code, and
runs a numeric coverage audit over the sections it designates. A small number of expressly
identified tables — Appendix G's layer and clipping cuts — depend on a person/organisation name
heuristic and a residence filter that belong to their originating script; reimplementing those
inside the verifier would copy the instrument rather than check it, so they are reproduced by
that script and marked as such in the supplement.

The panels are rebuildable from the raw voter files and contribution files by an **authorised
user who independently obtains the restricted inputs** and follows the full dependency-ordered
recipe; `scripts/donor_matcher.py` is a standalone extract of the record-linkage stage of that
recipe, not a one-command reconstruction. Rebuilding the Idaho federal panel through it
reproduces the published panel exactly — 0 differing rows across all 9 columns of all 23,303
rows. Independent *public* replication is not possible: the voter files cannot be
redistributed.

The companion [methods and provenance supplement](donor-class-methods-supplement.md) carries
the per-figure script provenance, the full reproduction recipe in dependency order, the
verification apparatus and its coverage limits, and a ledger of every claim withdrawn or
narrowed during review. The source ledger for the underlying data is
[`data-sources-and-reproducibility.md`](data-sources-and-reproducibility.md).

## References

### Scholarly works

Ansolabehere, Stephen, and Eitan Hersh. 2012. "Validation: What Big Data Reveal About Survey
Misreporting and the Real Electorate." *Political Analysis* 20 (4): 437–459.
doi:10.1093/pan/mps023.

Ansolabehere, Stephen, and Eitan Hersh. 2017. "ADGN: An Algorithm for Record Linkage Using
Address, Date of Birth, Gender, and Name." *Statistics and Public Policy* 4 (1): 1–10.
doi:10.1080/2330443X.2017.1389620.

Bailey, Martha J., Connor Cole, Morgan Henderson, and Catherine Massey. 2020. "How Well Do
Automated Linking Methods Perform? Lessons from US Historical Data." *Journal of Economic
Literature* 58 (4): 997–1044. doi:10.1257/jel.20191526.

Barber, Michael J. 2016. "Ideological Donors, Contribution Limits, and the Polarization of
American Legislatures." *Journal of Politics* 78 (1): 296–310. doi:10.1086/683453.

Bonica, Adam. 2014. "Mapping the Ideological Marketplace." *American Journal of Political
Science* 58 (2): 367–386. doi:10.1111/ajps.12062.

Bonica, Adam, Nolan McCarty, Keith T. Poole, and Howard Rosenthal. 2013. "Why Hasn't Democracy
Slowed Rising Inequality?" *Journal of Economic Perspectives* 27 (3): 103–124.
doi:10.1257/jep.27.3.103.

Enamorado, Ted, Benjamin Fifield, and Kosuke Imai. 2019. "Using a Probabilistic Model to Assist
Merging of Large-Scale Administrative Records." *American Political Science Review* 113 (2):
353–371. doi:10.1017/S0003055418000783.

Fellegi, Ivan P., and Alan B. Sunter. 1969. "A Theory for Record Linkage." *Journal of the
American Statistical Association* 64 (328): 1183–1210. doi:10.1080/01621459.1969.10501049.

Gilens, Martin. 2012. *Affluence and Influence: Economic Inequality and Political Power in
America*. Princeton, NJ: Princeton University Press.

Gilens, Martin, and Benjamin I. Page. 2014. "Testing Theories of American Politics: Elites,
Interest Groups, and Average Citizens." *Perspectives on Politics* 12 (3): 564–581.
doi:10.1017/S1537592714001595.

Grumbach, Jacob M., and Alexander Sahn. 2020. "Race and Representation in Campaign Finance."
*American Political Science Review* 114 (1): 206–221. doi:10.1017/S0003055419000637.

Grumbach, Jacob M., Alexander Sahn, and Sarah Staszak. 2021. "Correction to: Gender, Race, and
Intersectionality in Campaign Finance." *Political Behavior* 43: 905.
doi:10.1007/s11109-021-09693-y.

Grumbach, Jacob M., Alexander Sahn, and Sarah Staszak. 2022. "Gender, Race, and
Intersectionality in Campaign Finance." *Political Behavior* 44: 319–340.
doi:10.1007/s11109-020-09619-0.

Hersh, Eitan D. 2015. *Hacking the Electorate: How Campaigns Perceive Voters*. New York:
Cambridge University Press.

Herzog, Thomas N., Fritz J. Scheuren, and William E. Winkler. 2007. *Data Quality and Record
Linkage Techniques*. New York: Springer. ISBN 978-0-387-69502-0.

Hill, Seth J., and Gregory A. Huber. 2017. "Representativeness and Motivations of the
Contemporary Donorate: Results from Merged Survey and Administrative Records." *Political
Behavior* 39 (1): 3–29. doi:10.1007/s11109-016-9343-y.

Lahiri, Partha, and Michael D. Larsen. 2005. "Regression Analysis with Linked Data." *Journal
of the American Statistical Association* 100 (469): 222–230. doi:10.1198/016214504000001277.

La Raja, Raymond J., and Brian F. Schaffner. 2015. *Campaign Finance and Political
Polarization: When Purists Prevail*. Ann Arbor: University of Michigan Press.

Schlozman, Kay Lehman, Sidney Verba, and Henry E. Brady. 2012. *The Unheavenly Chorus: Unequal
Political Voice and the Broken Promise of American Democracy*. Princeton, NJ: Princeton
University Press.

Verba, Sidney, Kay Lehman Schlozman, and Henry E. Brady. 1995. *Voice and Equality: Civic
Voluntarism in American Politics*. Cambridge, MA: Harvard University Press.

### Cases

*Buckley v. Valeo*, 424 U.S. 1 (1976).

*Hispanic Leadership Fund, Inc. v. Walsh*, 42 F. Supp. 3d 365 (N.D.N.Y. 2014).

*McCutcheon v. Federal Election Commission*, 572 U.S. 185 (2014).

*New York Progress and Protection PAC v. Walsh*, 17 F. Supp. 3d 319 (S.D.N.Y. 2014).

*New York Progress and Protection PAC v. Walsh*, 733 F.3d 483 (2d Cir. 2013).

### Statutes and regulations

52 U.S.C. § 30116 (federal contribution limits, indexed biennially).

52 U.S.C. § 30118 (prohibition on corporate and labor-organization contributions).

Idaho Code § 34-437A (statewide voter-list release and permitted use).

Idaho Code § 67-6610A (individual contribution limits).

Idaho Code § 74-120 (restriction on agency lists used as mailing or telephone lists).

N.Y. Elec. Law § 14-114 (contribution and receipt limitations; § 14-114(8), annual aggregate
limit).

N.Y. Elec. Law § 14-116 (political contributions by certain organizations; § 14-116(1), LLCs;
§ 14-116(2), $5,000 annual corporate ceiling).

Tex. Elec. Code § 253.094 (corporate and labor-organization contributions prohibited).

Tex. Elec. Code §§ 253.151–253.176 (Judicial Campaign Fairness Act).

Wash. Rev. Code § 29A.08.710 (voter-registration records; year of birth).

Wash. Rev. Code § 29A.08.720 (permitted and prohibited use of voter lists).

Wash. Rev. Code § 29B.25.090 (contribution itemization threshold; § 29B.25.090(5)).

Wash. Rev. Code § 42.17A.405, recodified as § 29B.40.020 effective Jan. 1, 2026 (contribution
limits).

Wash. Admin. Code § 390-05-400 (adjusted dollar amounts). Amendments: WSR 23-07-004 (eff.
Apr. 1, 2023, setting the $100 itemization threshold); WSR 24-01-028 (filed Dec. 8, 2023);
WSR 26-01-209 (eff. Jan. 1, 2026).

### Agency datasets and administrative sources

Federal Election Commission. *Bulk Data: Contributions by Individuals (`indiv{yy}`), Committee
Master (`cm`), Candidate Master (`cn`)*, cycles 2018–2026.
<https://www.fec.gov/data/browse-data/?tab=bulk-data>.

Federal Election Commission. *Contribution Limits*, archived charts for cycles 2017–18 through
2025–26. <https://www.fec.gov/help-candidates-and-committees/candidate-taking-receipts/contribution-limits/>.

Idaho Secretary of State. *Sunshine Portal campaign-finance contribution filings*, 2023–2025.

Idaho Secretary of State. *Statewide voter registration list*, released under Idaho Code
§ 34-437A(3).

New York State Board of Elections. *Campaign Financial Disclosure — Schedule A monetary
contributions received*, data.ny.gov dataset `4j2b-6a2j`, election cycles 2018–2026.

New York State Board of Elections. *NYSVOTER statewide voter registration file*, obtained by
FOIL request.

New York State Board of Elections. *Contribution Limits* schedule.
<https://elections.ny.gov/contribution-limits>.

Washington Public Disclosure Commission. *Contributions to candidates and political
committees*, 2016–2026.

Washington Secretary of State. *Voter Registration Database (VRDB) statewide extract*.

### Software and code

DuckDB (in-process analytical database). <https://duckdb.org>.

Kirby, Stephen. 2026. *who-decides: analysis code and reproduction recipe for the
electoral-health series*. <https://github.com/skirby359/who-decides>. *A tagged release and
archival DOI must replace this branch reference before submission.*
