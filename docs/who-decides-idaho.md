# Who Decides Idaho?

### Filing, the closed primary, and the general election in a dominant-party state — from 1.03 million individual registration and vote records

**Stephen Kirby** · Tikor Consulting · July 2026

*AI-assisted drafting and analysis review. All figures are reproducible from
public-record data available through lawful request and from the open-source scripts
cited below, including `scripts/verify_who_decides_id.py`. The paper source, code, and
data-acquisition recipe are public at <https://github.com/skirby359/who-decides>; the
underlying voter file is not redistributed. Contact: kirby@tikorconsulting.com.*

*Deep-red companion to [`who-decides-washington.md`](who-decides-washington.md)
and [`who-decides-new-york.md`](who-decides-new-york.md). Washington showed the
off-year electorate is **older**; New York (deep blue) showed *whose* electorate
ages and who is shut out of the nominating contest. Idaho completes the set from the other
pole: a state where the **Republican nomination process — candidate filing and then the
closed May primary — produces the eventual winner of 90 of 105 legislative seats**, a
particularly concentrated nominating structure. That is a
statement about the nomination the winner held, not about a single event the data can point to
(§I). And it is more than the primary electorate's story: that electorate chose among more than
one candidate in **52 of the 105 seats**, and §IV decomposes the rest on two separate variables.
*(Three earlier framings sit behind that sentence and all are withdrawn in place. This line
called the November general "a formality" until 2026-08-11 — it is not; Democrats won 15 of
105 seats, see §V. It said the closed primary "resolves the great majority of seats"
until 2026-08-15, which the paper's own seat counts contradict: 52 of 105 is 49.5%. What
produces the winner in the great majority is the nomination process, of which the primary is
one of two stages. And until 2026-08-16 §IV reported that nomination cut under a definition about
contestation, which is a different variable: 80 of the 105 seats still offered a choice on
the November ballot. Producing the winner's nomination and settling the seat are not the same
event, and the paper now measures both.)* **DRAFT — pending human/editorial sign-off.
`scripts/verify_who_decides_id.py` scrapes this paper and asserts its figures against the voter
file, with the exceptions the script names in its own output; see
[`electoral-health-audit-log.md`](electoral-health-audit-log.md). That gate is automated and is
not the sign-off. The sign-off is a person reading the paper end to end, recorded in
[`id-submission-notes.md`](id-submission-notes.md) §Sign-off.***

*This line previously read "AI-side reproduction verified (all `verify_*` scripts re-run, exit
0)". That formulation is worth nothing and the New York companion says so in its own front
matter: a script with no assertions and no failing exit path returns 0 whatever the data says,
so "exit 0" is a claim about the script, not the paper. What replaces it names the assertion,
which is the thing a reader can check.*

*Provenance. All figures from `data/id_vrdb.duckdb` — Idaho's statewide voter
file with history (1,029,938 registrants; individual party affiliation + age +
per-election vote history incl. the primary ballot each voter pulled, all ~100%
populated) — via `scripts/diag_id_turnout_party.py` and
`scripts/diag_id_electorate_extras.py`. The donor layer joins Idaho Sunshine
state contributions via `scripts/match_id_voters_to_donors.py`. Competitiveness
from `forecast_predictions`. Each figure below traces to one of these scripts.*

*Load-bearing caveats. (1) The file is the current (2026) roll, which has shrunk to
1.03M from the ~1.18M registered at the 2024 election, chiefly through list
maintenance. Voters who cast a past ballot but were since
purged/moved are absent, so any turnout **rate** computed from this file is biased
high — materially: an all-voter 2024 rate comes out near 94% against the official
77.8%. The bias is *larger* for high-churn groups (young, unaffiliated, movers), so
even within-year cross-group rate comparisons are unreliable. This paper therefore
reports **composition shares only** (who the electorate is), which need no
registration denominator, and reports no turnout rates. See Methods. (2) Idaho
publishes **age**, not date of birth; election-time age is
approximated as `age − (2026 − year)`, accurate to ~1 year — fine for bands, and
we never claim exact ages. (3) "UNAFF" = Idaho's unaffiliated registration; its
partisan lean is never imputed.*

---

## Abstract

In a dominant-party state the general election is rarely the whole story of how a legislature is
filled, and the shorthand answer — the primary — is too coarse to capture the rest. Idaho is
**63%** Republican and **12%** Democratic by registration. Using the statewide voter file for
**1,029,938** registrants, with party of record and the party ballot each voter actually pulled,
this paper measures, seat by seat, what the ballot offered and who was present to use it.
**The central result is a three-layer count of Idaho's 2024 legislature: **105** seats, **80**
offering a choice on the ballot, **8** offering a close one** — where "close" is a
general-election margin under ten points. Choice is common and competition is rare, and the
distance between those two layers is the finding.

Two descriptive cuts sit underneath it. The first classifies each seat by the Republican
nomination configuration and the November winner: a **contested** Republican primary won by a
Republican for **52** (**49.5%**); a **sole Republican filer** who won for **38** (**36.2%**); a
**sole Republican filer** beaten by a Democrat for **9** (**8.6%**); and **no Republican filer
at all**, a Democrat winning, for the remaining **6** (**5.7%**). So Republicans won **90 of
105** seats and Democrats **15**, nine of those by beating a lone Republican filer; of the 90
Republican wins, 52 followed a contested Republican nomination and 38 an uncontested one. By **the stage at which a seat stopped being contested**, the
same seats fall very differently: **80** (**76.2%**) still offered two or more candidates on
the general-election ballot, **16** (**15.2%**) were contested only in the primary, and just
**9** (**8.6%**) were unopposed at every stage. The two cuts place **71** of the seats in
non-corresponding cells, because a nomination configuration and a last-contested stage are
different observables — a seat can be uncompetitive without being uncontested.

*(This passage was rebuilt on 2026-08-26, author's decision after an external review, and what
changed is the claim rather than any number. It previously led with the two cuts as "a
decomposition ... on two variables that the phrase 'where a seat is decided' ordinarily
conflates", described the first as "the stage that produced the winner's nomination", and
concluded that "Idaho's dominant party settles who will hold most seats long before November".
Three problems, and they compound. The first cut's own categories include **the November
general**, which cannot produce a nomination. That 90-seat figure is **retrospective**: it
identifies which nomination the eventual winner happened to hold, which does not date when the
seat became binding. And the temporal conclusion is precisely the inference the safe-seat
companion withdrew on 2026-07-27 — an observed margin is an ex-post measure and cannot say
when a contest stopped being live. §IV's own data refutes the strong reading directly: **35 of
the 38** uncontested Republican nominations drew a November opponent and three finished within
ten points. The counts were never in question and none has moved; the paper now states them
without naming an unobserved decision event.)*

Two further findings are specific to Idaho rather than replications of the off-cycle turnout
literature. First, **senior representation is nearly identical across the two parties**:
Republicans and Democrats among 2024 general voters are within a fraction of a point on the
65-and-over share, **31.7%** against **31.5%** — *within-party senior-share parity*. That
parity does not reverse the national older-is-more-Republican pattern in composition: because
Republicans are the far larger base with fewer young voters, the 65-and-over electorate is
**70.4%** Republican against **54.1%** of the under-30s, so older is more Republican here as
elsewhere. What is novel is the equal within-party senior shares, which the New York companion
does not find. What distinguishes Idaho's unaffiliated quarter is the senior end specifically — **21.3%** aged 65 or
over against roughly 31.6% in both parties — and not the young end, where unaffiliated and
Democratic voters are level at **19.6%** and **19.4%** under 30. Second, the file records the
party ballot each voter pulled, so participation in the nominating primary is observed directly
rather than inferred from registration: **83.4%** of 2024 primary participants took a
Republican ballot. That observed measure matters because the registration-based one is
contaminated by the primary itself — under Idaho Code **§ 34-411A** an unaffiliated elector who
requests a Republican ballot may affiliate at the poll book, and the county clerk then records
that affiliation in the statewide registration file, while a Democratic ballot carries no such
conversion. Because the file is a single 2026 snapshot with no affiliation date, the
unaffiliated shares reported for past primaries are **lower bounds**. On the contaminated
measure the May 2024 primary electorate is
**85.2%** Republican by party of record against **62.9%** of the roll, a
Republican-minus-Democratic margin of **76.8** points against **51.1** on the rolls, and its
Republican-ballot voters have a median age of **63** with **46.7%** aged 65 or over. Every one
of the **35** legislative districts carries a Republican registration advantage and none is
near parity. The paper reports composition shares and deliberately reports no turnout rates,
because a current-extract roll that has contracted from about 1.18 to 1.03 million inflates
every rate.

**Keywords.** one-party dominance; closed primaries; nominating electorate; voter file; party
registration; unaffiliated voters; uncontested elections; turnout composition; election timing;
Idaho

---

## The question

How *many* people vote is the wrong question for understanding how a state is
governed. The right one is *who* — and the question after that is *where*: at
what the ballot offered at each stage of the sequence. Idaho is a dominant-party
state by registration (**63% Republican, 12% Democratic, 24% unaffiliated**), and
almost all of its officeholders reach November holding a Republican nomination. But that
nomination comes through **two distinct gates**, and they are not the same gate at all: the
**candidate-filing deadline**, where in more than a third of seats only one Republican comes
forward, and the **closed May Republican primary**, where a much narrower electorate chooses
among those who did.

The short answer: **where Idaho's general elections offer a choice they mostly do not offer a
close one, and the electorate present in the closed May primary is gray, Republican
and self-selected.** *(This read "the people who actually decide Idaho are a gray, Republican,
self-selected slice of an already-Republican state — where anyone decides at all" until
2026-08-26. "Who decides" names an event the data does not identify; what it measures is who is
present at each stage and what the ballot offered at each.)*
In November the electorate is broadly representative; in the primary it is older and
drawn almost entirely from one party; and in **9 of 105 seats (8.6%)** no contested
election of any kind takes place. *(This read "about two-fifths" until 2026-08-26, which
was residue from the retired reading that treated the 38 uncontested Republican
nominations as seats settled at filing. The paper's own §IV records that **35 of those 38
drew a November opponent** — three within ten points — so two-fifths overstated the
no-contest count by more than fourfold. The figure that is about two-fifths is a different
quantity: the **36.2%** of seats whose winner took an uncontested Republican nomination,
which is not the same as no contested election taking place.)* The 24% of registrants who decline a party can enter
the Republican primary, but only by becoming Republicans to do it — an affiliation
requirement, not a locked door.

Two further findings are specific to Idaho, not a replication of the off-cycle
turnout literature. First, **senior representation is nearly identical in the two
parties**: Idaho's Republicans and Democrats are within a fraction of a point on the
65-and-over share — *within-party senior-share parity*. That is a within-party fact and does
not make the older electorate less Republican: Republicans dominate the base, so Idaho's older
electorate is more Republican than its younger one, as elsewhere; what the New York companion
does not find is the equal within-party senior shares. The
unaffiliated bloc is the young one,
but the gap that makes it so is at the senior end — it carries ten fewer points of
over-65s than either party, while being level with Democrats among the under-30s.
Second, the file records the party ballot each voter actually pulled, so participation
in the nominating primary is **observed rather than inferred from registration alone**.
That distinction is load-bearing here rather than decorative, because the
registration-based measure is partly destroyed by the act it records, for the reason
set out in Section IV.

---

## I. The midterm electorate is substantially older than the presidential electorate

Share of the general-election electorate by age band:

| Election | Type | 18–29 | 30–44 | 45–64 | 65+ | median |
|---|---|--:|--:|--:|--:|--:|
| Nov 2024 | Presidential | 15.2% | 23.4% | 32.4% | 29.0% | 52 |
| Nov 2022 | Midterm | **8.6%** | 20.7% | 36.3% | **34.4%** | 57 |
| Nov 2020 | Presidential | 13.8% | 23.9% | 36.1% | 26.3% | 52 |
| — | Registration baseline (2026) | 15.2% | 22.8% | 30.9% | 31.0% | 52 |

From the presidential to the midterm electorate, the under-30 share nearly halves
(15.2% → 8.6%) and the 65+ share swells (29% → 34%); median age rises from 52 to
57. This is consistent with the **surge-and-decline** literature (Campbell 1960) and the wider
work on turnout composition, though this design does not manipulate timing or measure salience
and so cannot identify the mechanism.

**What this section claims is composition, not mechanism, and the distinction is
forced by Idaho's own data.** It says the observed electorate becomes older from the
presidential to the midterm electorate. It does not say that the whole of that change is age-specific
participation *behaviour* rather than change in the registered population, because
this file cannot separate the two: the historical turnout denominators are
unusable, the current roll excludes everyone who has since left it, and
`registration_date` resets on ordinary events (Boundary of inference; §VI). A
rate-based decomposition run on reconstructed historical rolls inherits every one
of those defects.

*This paragraph replaced a stronger one on 2026-08-15. The section previously read
"**Behavior, not rolls**", cited a Das-Gupta decomposition attributing the 65+ rise
mostly to turnout, and said the young "choose not to vote" — while the same paper's
Boundary section establishes that reconstructed historical rolls and rates cannot
carry that weight. An external referee named the contradiction. The composition
finding is unaffected and survives a hostile missing-voter bound (Boundary); the
mechanism claim is withdrawn rather than softened.*

*The section heading changed at the same time, for a second reason. It read "The
off-year electorate is older — Idaho replicates Washington", and this comparison is
2024 presidential against 2022 midterm: two even-year federal general elections. That
is presidential-versus-midterm, not the odd-year/off-cycle timing effect Washington's
companion measures — a distinction the section drew in its own parenthesis and then
undid in its heading, its verb ("replicates") and its conclusion ("timing-fixable",
"on-cycle remedy"). Idaho's voter file does not contain the odd-year local elections
the Washington mechanism would need. The off-cycle literature — Anzia 2014; Hajnal &
Trounstine 2005 — remains relevant to Idaho's local offices, which like Washington's
sit off the federal calendar; it is simply not what this table measures.*

---

## II. Senior representation is the same in both parties — and that is the whole of the finding

This is where Idaho diverges sharply from New York. New York's Republican electorate is
consistently the older of the two; in Idaho the two major parties carry the same senior share.
Share of each party's 2024 general-election voters by age, plus median age:

| Party | share 65+ | share 18–29 | median age |
|---|--:|--:|--:|
| Republican | 31.7% | 12.7% | 54 |
| Democratic | 31.5% | 19.4% | 50 |
| **Unaffiliated** | **21.3%** | **19.6%** | **46** |
| Other (Lib/Con) | 10.0% | 23.0% | 39 |

The Republican and Democratic electorates are within a fraction of a point on the
65+ share and only four years apart on median age. **That within-party parity is the finding.** It does **not** overturn the national "older =
redder" pattern at the level of composition: because Republicans are the dominant base with far
fewer young voters, Idaho's 65-and-over electorate is **70.4%** Republican against **54.1%** of
the under-30s — older *is* more Republican here, as elsewhere. What is distinctive, and what the
New York companion does not show, is that the two parties' own electorates carry the same senior
share despite different median ages and youth shares. The unaffiliated bloc carries ten
fewer points of over-65s than either party (21.3% against 31.7% and 31.5%), which is
what pulls its median down to 46 — and it is the reason Sections III–IV matter, since
that bloc is the one that all but vanishes from the closed primary.

*Read the under-30 column before generalising, because it does not say what the 65+
column says.* Unaffiliated and **Democratic** voters are level there — 19.6% against
19.4%, a fifth of a point apart — while Republicans sit nearly seven points below
both. So on the youth measure the unaffiliated bloc is indistinguishable from the
Democratic electorate, and the two-party contrast is not neutral at all.

*Until 2026-08-15 this section and the abstract said the age gap was "party-neutral"
and that Idaho's youth "sits in the unaffiliated bloc rather than in either party".
The second half was false against the table printed directly above it, and an external
referee read it there. Both claims are narrowed to the one the data carries: senior-share
parity between the parties, and an unaffiliated bloc that is younger than both because
it has fewer seniors — not because it has more young people than Democrats do. The
narrowed claim is the more interesting one anyway, and it is asserted as a relation in
`scripts/verify_who_decides_id.py` rather than merely restated, so it cannot quietly
stop being true.*

---

## III. The unaffiliated quarter: near its roll share in November, much smaller by current classification in May

Idaho's 245,887 unaffiliated registrants (23.9% of the roll) are the recurring
blind spot. Because Idaho's roll cannot support reliable turnout *rates* (Methods),
we follow each bloc by its **share of the electorate** — a denominator-free measure
— across the two contests:

| Bloc | roll % | median age | % 65+ | % 18–29 | share of 2024 **general** electorate | share of 2024 **primary** electorate |
|---|--:|--:|--:|--:|--:|--:|
| Republican | 62.9% | 55 | 34.5% | 12.6% | 64.5% | **85.2%** |
| Unaffiliated | 23.9% | 46 | 22.4% | 19.9% | 22.6% | **5.9%** |
| Democratic | 11.8% | 50 | 32.4% | 19.1% | 11.6% | 8.3% |
| Other | 1.4% | 40 | 11.0% | 21.3% | 1.3% | 0.6% |

The story is in the last two columns. Voters currently classified unaffiliated are **22.6% of
the 2024 general electorate** — essentially their full 23.9% of the roll, so in November the
bloc is present at close to its registration weight. But they are only **5.9% of the May
primary electorate**: voters classified unaffiliated in the 2026 snapshot account for about
**one in seventeen** reconstructed 2024 primary participants. The next paragraphs show why that
primary figure is a lower bound on election-time unaffiliated participation, not a rate.

**The mechanism is an affiliation requirement, not exclusion, and the difference is
worth stating precisely.** Idaho's Republican primary is closed, but an unaffiliated
elector is not barred from it: under Idaho Code § 34-411A they may affiliate with the
party of their choice up to and including election day, by signed form or by declaring
the choice to a poll worker. What they cannot do is **participate in the Republican
primary while remaining unaffiliated** — affiliation is the price of admission, and it
is a price that persists on the roll afterwards (§IV). So the 5.9% is not a measure of
people turned away. Nor is it a measure of unaffiliated participation: affiliating to vote a
Republican ballot reclassifies a voter as Republican, so the current-party count of
unaffiliated primary voters is a lower bound on how many election-time unaffiliated voters took
part, and this single 2026 snapshot cannot recover the true figure (§IV).

*This section, the abstract and the opening described the unaffiliated quarter as
"locked out", "outside the room" and unable to enter, until 2026-08-15. An external
referee pointed out that Idaho's election authorities say the opposite; checking the
statute directly, § 34-411A says it in as many words, and the paper's own §IV already
described the same-day affiliation mechanism the wording was denying. The institutional finding is unchanged and the wording is
now the one that is harder to attack.*

> **A note on the roll itself.** Idaho's registration file shrank from **~1.18M** at
> the November 2024 election to **~1.03M** in this 2026 snapshot — a **net decline of
> 148,812 registrations, 12.6%** of the 2024 total, from routine list maintenance
> (inactive-voter removal, change-of-address, deaths). That contraction is the reason
> historical turnout *rates* cannot be reconstructed from a single snapshot (Methods).
>
> **Two things this figure is not.** First, it is not turnover, and it is not an upper
> bound on turnover: it is a difference between two stocks, so anyone who joined the roll
> after November 2024 is netted against someone who left. Gross departures are therefore
> **at least** 148,812 and could be far more. The direction of that bound was stated
> backwards here until 2026-08-15.
>
> Second, it is not explained by same-day registrants. This note previously attributed
> part of the contraction to "the non-persistence of the 121,000 voters who registered
> same-day on Election Day 2024" — a mechanism that was never measured and that the file
> can measure, because a voter who registered at the polls carries that date. Measured:
> **109,441 of the 121,015 election-day registrants are still on the 2026 roll, at least
> 90.4%**, and 109,233 of them carry a 2024 general vote record. That is a floor rather
> than a rate — `registration_date` records the most recent registration event, so any of
> them who has since moved or changed party carries a later date and is counted here as
> gone — so true retention is higher still. **The claim was wrong and is withdrawn**, not
> softened; whatever produced Idaho's roll contraction, it was not the election-day cohort
> failing to persist.

## IV. The two nomination gates — and how gray the primary electorate is

The Republican nomination process produces the winner in the great majority of Idaho's
legislative seats. The primary electorate does not. Neither statement is the same as saying
the seat was over before November. Those are three different claims and this section
separates them, because conflating them is the error the section has now made twice in
opposite directions; the rest of it describes who is present in the closed Republican primary.

**Two variables, not one.** "Where a seat is decided" hides a distinction that Idaho's own
records can settle — though neither variable below is a "when decided" variable. *What
Republican nomination configuration did each seat have, and who won in November?* and *what was
the last stage at which more than one candidate appeared on a ballot?* are different observables
with different answers, and the tables below report them separately rather than blending them
into a single word.

**Variable 1 — Republican nomination configuration and November winner. All 105 legislative
seats, 2024.** This is a cross-tabulation of the Republican nomination path with which party
won the seat, not a single "stage" variable — two of its four rows (a general-election loss, a
seat with no Republican on the ballot) are outcomes, not nominations. Each seat is classified by
how many Republicans filed and who won in November:

| Republican nomination configuration → November winner | seats | share |
|---|--:|--:|
| **Contested Republican primary → Republican won** — ≥2 Republicans filed | **52** | **49.5%** |
| **Sole Republican filer → Republican won** | **38** | **36.2%** |
| **Sole Republican filer → Democrat won** | **9** | **8.6%** |
| **No Republican filer → Democrat won** | **6** | **5.7%** |

Read across: a Republican won **90 of 105 seats (85.7%)** — **52** with a contested Republican
nomination and **38** with an uncontested one. That is the sense in which "the great majority"
is defensible, and it is a claim about the *nomination configuration*, not about when any seat's
outcome became fixed. Democrats ultimately won **15**, of which **9** came against a sole
Republican filer. Their own
nominations were almost all uncontested in turn: **13** of the 15 drew a single Democratic
filer and only **2** faced a contested Democratic primary.

**Variable 2 — the stage at which the seat stopped being contested.** The same 105 seats,
assigned to the last stage at which more than one candidate was still on a ballot:

| Last contested stage | seats | share |
|---|--:|--:|
| **The November general** — two or more candidates on the general-election ballot | **80** | **76.2%** |
| **The primary** — a contested primary, then an unopposed general | **16** | **15.2%** |
| **Candidate filing** — unopposed at every stage | **9** | **8.6%** |

**The two cuts place 71 of the 105 seats in non-corresponding cells, and that
non-correspondence is the finding.** A nomination configuration and a last-contested stage are
different observables, not rival classifications of one "decision", and treating them as one is
what "where a seat is decided" does. Most Idaho
voters did face a choice on the general ballot; in most cases it was a choice whose outcome was
never close. *(This paragraph asserted that "Idaho's dominant party settles who will hold most
seats months before November" until 2026-08-26. That dates a binding decision the data does not
observe — the safe-seat companion withdrew the identical inference on 2026-07-27 — and §IV's own
figures cut against it: 35 of the 38 uncontested Republican nominations drew a November
opponent, three of them finishing within ten points. What the tables support is a
distributional claim, not a temporal one.)* A seat can be
uncompetitive without being uncontested, and the distinction matters precisely because the
reform arguments in this literature attach to different stages.

**How little of that November contestation was competitive — because the second table counts
ballot presence, not viability.** Of the **80** seats offering two or more candidates in November,
only **8** were decided by fewer than ten points and **6** more by ten to twenty; **18** ran
to twenty-to-forty, **43** to forty or more, and a further **5** offered no two-party choice
at all despite carrying multiple candidates. So the honest summary has three layers rather
than two: **105** seats, **80** with a choice on the ballot, **8** with a close one. That is a
sharper statement of this paper's thesis than either table alone, and it is the reason the 80
must not be read as a competitiveness figure — it measures *ballot access*, and only the
margin column turns it into a statement about contests.

*Both tables are new on 2026-08-16 and they replace a single table that carried the first
one's numbers under the second one's definition.* That table was headed "the decision venue"
and defined as "the last stage at which more than one candidate was still in contention",
but it was computed from the Republican primary's shape and the general's winner and never
looked at who else was on the November ballot. A second external referee caught the mismatch,
and the data is emphatic: of the **38** seats the old table assigned to candidate filing,
**35 faced an opponent in November**, **32** of them a major-party opponent, and **3** were
decided by a margin under ten points. Calling those "decided once the filing period closed"
was wrong, and it is withdrawn rather than softened. *(The same referee suspected the
six no-Republican seats had the mirror-image problem — that a contested Democratic
nomination might sit behind them. Measured, they do not: all six drew a **sole** Democratic
filer and all six were unopposed in November, so filing genuinely did settle them. That row
survives the objection.)*

*The first table's counts are unchanged, and its own history is worth keeping.* It replaced
the section's headline claim on 2026-08-15 at an earlier referee's insistence, and he was
right on the paper's own numbers: 52 of 105 is 49.5%, so
"the closed primary resolves the great majority of seats" was contradicted by the counts
printed three paragraphs below it.
His decomposition put all fifteen Democratic seats in the November column; six had no
Republican filing at all, so the count that genuinely turned on the general is nine. What
neither he nor this paper noticed until the following day was that the corrected table was
still answering a question the surrounding prose was not asking.

Three facts describe the primary electorate itself.

**The primary electorate is far more Republican than November.** Party of record on the
2026 roll, by contest, as R-minus-D margin:

| Contest | REP | DEM | UNAFF | R − D |
|---|--:|--:|--:|--:|
| Nov 2024 general | 64.5% | 11.6% | 22.6% | +52.9 |
| Nov 2022 general | 68.6% | 12.1% | 18.2% | +56.5 |
| **May 2024 primary** | **85.2%** | 8.3% | 5.9% | **+76.8** |
| **May 2022 primary** | **85.9%** | 8.2% | 5.3% | **+77.7** |
| — Registration baseline | 62.9% | 11.8% | 23.9% | +51.1 |

The unaffiliated share of the electorate falls from ~24% of the roll to roughly
**5–7%** of the primary; the R−D skew widens from ~+51 in November to ~+77 in the
primary. **80–86% of every primary ballot cast in Idaho is a Republican ballot** — the
range spans every primary cycle in the file, from 79.6% in 2026 to 86.5% in 2022.

**Which of those two measures to believe, stated once.** Every party column in the table
above is **party of record on the 2026 roll**, not party at the time of the election. The
file carries no affiliation date, so a voter who changed party at any point between the
contest and June 2026 — including through the poll-book affiliation described below, but
also through any ordinary change — is classified here by where they ended up. "85.2% of
the 2024 primary electorate was Republican" therefore means, exactly, *85.2% of
reconstructed 2024 primary participants are classified Republican on the 2026 roll*.
**The ballot column has no such defect**: it records which party's ballot the voter
actually took, at the time, and it is populated for 99.6–99.9% of participants. Where the
two disagree, the ballot is the measurement and the registration is the residue —
Republican ballots were **83.4%** of 2024 primary participants against 85.2% classified
Republican, and **86.1%** in 2022 against 85.9%. This basis note was added on 2026-08-15
after an external referee observed, correctly, that the paper knew about the contamination
in one direction (§IV's conversion mechanism) and had not applied it to ordinary party
switching.

*Two denominators appear in this section, a fraction of a point apart, so which one a figure uses
is stated rather than left to be inferred. The 79.6 / 86.5 range above is the Republican
share of ballots **whose party choice is recorded**. The falling series later in this section —
86.1% / 83.4% / 79.5% — is the Republican share of **all primary participants**, including the
0.1–0.4% of them (436 to 1,379 voters a cycle) whose ballot choice
`id-primary-ballot-choice-blank` records that the file does not carry. Both are asserted; neither
is wrong; they are not interchangeable. That those blanks are the source's rather than our
loader's was checked against the raw export rather than inferred from the loaded table — the same
claim shape was false for Washington's PDC direction flag, where the gap turned out to be our own
extraction.*

The R−D column is computed on **unrounded** shares, so it need not equal the difference of
the two printed columns. The May 2024 row is the one where that shows: 85.17 − 8.34 = 76.82,
against 85.2 − 8.3 = 76.9 read off the table. The unrounded figure is the one printed.

**The underlying counts, and how they were checked.** Of the 105 legislative seats, **99
drew a Republican primary in 2024** (the other six are the safe-Democratic seats where no
Republican filed); of those 99, just **52 (53%) were contested** and **47 (47%) had a
single Republican on the ballot** (`scripts/diag_id_primary_contested.py`, reconciled
seat-by-seat against the 35-district / 105-seat frame — every race maps 1:1 to a seat, no
duplicates; the contested counts match Ballotpedia's independent tallies cycle-by-cycle,
exact for 2022 and 2024 and within ±2 for 2016 and 2018). Those 47 single-candidate
primaries did not all settle a seat: **9 of them were won by a Democrat in November**,
while all 52 contested-primary seats went Republican. That is the arithmetic behind the
decomposition above, and behind the narrower statement that for **38 of the 90
Republican-held seats, 42%**, the eventual winner's *nomination* was fixed at candidate
filing — a fact about the nomination stage, not a date on the seat's outcome: most of
those 38 drew a November opponent (§I's rebuild note gives the arithmetic).

**Contestation rose to a 2022 peak and then fell.** Across the loaded cycles the
Republican legislative-primary contested rate runs **36% (2016) → 43% (2018) → 68% (2022)
→ 53% (2024)**. 2022 was the first post-redistricting cycle; 2024 sits a sixth below it
and still well above 2016. (2020 is not comparable: the SoS published that mail-only
cycle's legislative results at county level only.) With four comparable observations and a
missing 2020, **this paper claims no trend** — only that the contested share is materially
higher in the 2020s than in the 2010s and that it did not continue rising. Democratic
legislative primaries, by contrast, are almost never contested (2–11% across these cycles)
— the mirror image of one-party dominance.

*Two things came out of this paragraph on 2026-08-15. It said the rate had "roughly
doubled across the decade", which its own series contradicts on any endpoint reading: 36 →
53 is 1.4×, and the 1.9× is 2016 to the 2022 peak, from which the series then falls. And
it attributed the 2022 peak to "the height of the state GOP's traditional-vs-hardline
fights" — a post-hoc political reading with no source, which is now dropped rather than
left standing on assertion. The shape of the series is asserted in code
(`rprim_peak_ratio`, `rprim_endpoint_ratio`), because a trend word has no numeric token a
coverage gate can catch.*

**The primary electorate is older than even the Republican rolls.** Comparing all
Republican registrants to those who actually pulled a Republican ballot in 2024:

| Group | 18–29 | 30–44 | 45–64 | 65+ | median |
|---|--:|--:|--:|--:|--:|
| Republican registrants (all roll) | 12.6% | 20.4% | 32.5% | 34.5% | 55 |
| Republican-ballot primary voters, 2024 | **5.0%** | 14.2% | 34.1% | **46.7%** | **63** |

Idaho's Republican-ballot primary voters are a gray subset of an already-red
party: **median age 63, nearly half of them 65+.**

**When today's unaffiliated registrants voted in a past primary, they mostly pulled the
Democratic ballot — but this table cannot be read as a trend.** Ballot choice among voters
who are unaffiliated *on the 2026 roll*:

| Primary | → REP | → DEM | → nonpartisan | years before the snapshot |
|---|--:|--:|--:|--:|
| May 2022 | 27.7% | 52.6% | 19.0% | 4.1 |
| May 2024 | 9.7% | 52.5% | 37.5% | 2.1 |
| May 2026 | **1.7%** | **65.6%** | 32.6% | 0.1 |

**The Republican column is an artifact of the snapshot, not a behavioural trend, and this
is the paper's central measurement caveat.** Two statutes do the work, and the paper cited
only the first of them until 2026-08-15. **Idaho Code § 34-904A** governs *eligibility*: an
elector who has designated a party affiliation may vote only in that party's primary, which
is the legal framework under which the Republican Party closes its primary. **Idaho Code § 34-411A** supplies the
*mechanism and its trace*: an unaffiliated elector may affiliate up to and including
election day, may do so by declaring the choice to a poll worker, who records it in the poll
book — and "after the primary election, the county clerk shall record the party affiliation
so recorded in the poll book as part of such elector's record within the voter registration
system." That last clause is the measurement problem in the statute's own words: **the act
of voting a Republican ballot writes itself into the field this paper reads.** Requesting a
Democratic ballot does not affiliate anyone, because the Idaho Democratic Party admits
unaffiliated voters. `voters.party` is a **single current snapshot** — the raw file carries a
party description and **no affiliation date** — so an unaffiliated voter who entered the
Republican primary is, by construction, no longer unaffiliated when we look.

*An external referee flagged the § 34-904A citation as misplaced. He was right that
§ 34-411A is where the same-day mechanism lives, and it is a better citation than the one
it replaces because it also contains the registration-system recording clause the caveat
depends on. He was not right that § 34-904A is the wrong statute for this passage — it is
the closure rule the whole section is about — so both are now cited, each for what it
actually says.*

The data exhibit the pattern the statutory mechanism predicts. The Republican column
falls monotonically with distance from the snapshot (27.7 → 9.7 → 1.7) while the Democratic
column does not (52.6 → 52.5 → 65.6). Among today's unaffiliated voters who pulled a
**Republican** ballot in 2022, **55.8%** carry a registration date *after* that primary —
they re-registered, reverting to unaffiliated — against **15.2%** of those who pulled a
Democratic ballot. And voters who are Republican today pulled a Republican ballot in
97.3 / 96.9 / 97.7% of cases across the three primaries, a concordance that is definitional
rather than behavioural.

**What this costs the finding.** The 5.9% unaffiliated share of the May 2024 primary
electorate is neither a measurement of unaffiliated participation nor of non-participation. It
is the share of reconstructed 2024 primary participants who are classified unaffiliated on the
2026 snapshot, and it is a **lower bound** on the share who were unaffiliated *before*
participating: voting a Republican ballot can rewrite the recorded affiliation (§ 34-411A), and
a later re-registration can rewrite it again — the re-registration rates below show both
channels are live. The 2026 figure — unaffiliated registrants are **7.3%** of that primary
electorate — is the least temporally contaminated observation, closest to the snapshot, but it
is still not an estimate of election-time unaffiliated participation. The 2024 and 2022 figures
are lower bounds, and the conversion is unobservable from this source, so the gap cannot be
closed with the data at hand — a defect the New York companion avoids because enrollment there
must precede the primary by months and is bounded at 0.7–1.4%.

**The direction of the lock is also not what an earlier reading suggested.** The Republican
share of *all* primary ballots cast falls across the three cycles — **86.1% (2022), 83.4%
(2024), 79.5% (2026)** — while the Democratic ballot share rises. Whatever is happening to
Idaho's one-party primary, it is not tightening on this measure.

---

## V. Every district carries a Republican registration advantage

Districts by **registration advantage** (Republican % − Democratic % of registrants):

| Level (n) | R+40 or more | R+20 to 40 | R+5 to 20 | Within 5 points | Any D advantage |
|---|--:|--:|--:|--:|--:|
| Congressional (2) | **2** | 0 | 0 | 0 | 0 |
| Legislative (35) | **27** | 4 | 4 | **0** | **0** |

Both U.S. House seats and every one of the 35 legislative districts carry a Republican
registration advantage; **none is within five points, and none advantages Democrats.**

*The bands were labelled "Safe R / Likely R / Lean R / Competitive" until 2026-08-15. An
external referee objected that those are election-outcome labels attached to a registration
measure that demonstrably does not map onto outcomes — the paragraph immediately below says
so — and he is right. Cook-style names import a prediction the measure cannot make. The
bands are now named for what they are: intervals of R-minus-D registration.*

**Registration advantage is not an outcome, and here it is decisively not one.** In the
November 2024 general, Democrats won **15 of Idaho's 105 legislative seats** (90 R / 15 D,
matching the seated 2025–26 legislature), including seats this table places in its widest
band. Of the 47 seats whose Republican primary drew a single candidate, **nine were won by
a Democrat in November** — so for those the choice was settled by the general, not at
filing. An earlier version of this section wrote that "where the general election cannot
change an outcome" the primary is the only decisive contest; that inference does not
survive its own state's results, and the companion safe-seat paper withdrew a stronger
version of it on *observed margins*, which are better evidence than registration. It is not
reinstated here on weaker evidence.

What the table does support is narrower: **every one of the 35 legislative districts carries a
Republican registration advantage, and none is within five points.** That is a fact about the
rolls, not about outcomes — the fifteen Democratic wins above, several in this table's widest
band, make the point — so it says nothing about what November can do. The three-state
superlative that stood here is also
withdrawn: Washington publishes no party registration at all, so no comparable
registration-advantage map exists for it, and comparing this table to the safe-seat paper's
observed margins compares two different measures.

---

## VI. Recently-dated registration records are younger and less Republican

Party mix and age of the registrants on the current roll, grouped by the year their
`registration_date` falls in:

| Registration dated | registrants | % REP | % DEM | % UNAFF | median age at that date |
|---|--:|--:|--:|--:|--:|
| 2008 | 22,559 | 66.4% | 5.3% | 28.0% | 45 |
| 2012 | 30,843 | 71.5% | 11.8% | 15.9% | 47 |
| 2016 | 61,465 | 65.5% | 12.1% | 21.2% | 46 |
| 2020 | 153,710 | 60.8% | 12.2% | 25.1% | 43 |
| 2022 | 97,593 | 64.8% | 11.3% | 21.8% | 44 |
| 2024 | 263,322 | **57.5%** | 12.4% | **28.3%** | **35** |

**These are not cohorts, and the table must not be read as one.** `registration_date`
is the date of a voter's most recent registration *event*, not their first. Idaho
writes a new date on an address change, a party change — including the § 34-411A
poll-book affiliation of Section IV — and an election-day registration. The rows are
therefore structurally different populations rather than successive intakes of new
voters: a record dated 2008 belongs to someone who has avoided every
registration-resetting event for eighteen years, and a record dated 2024 mixes genuinely
new registrants with movers, party changers, poll-book affiliates and re-registrants.
Of the registrants dated 2024, **36.3% had already voted in an earlier election**; of
those dated 2022, **43.7%** had. Both are floors, because the file's vote history
reaches back only to 2020, so a 2024 registrant who last voted in 2018 is
indistinguishable from a genuinely new one. The 2008–2020 rows cannot be cleaned at
all for the same reason, and the 263,322 registrants dated 2024 — a quarter of the
roll in one year — is a registration-event count, not a count of new voters.

Removing the *detectably* re-registered does not repair this, and the paper does not
claim it does: the filter cannot see a voter registered before 2020 who did not vote in
the observed history, an address change by someone with no prior observed vote, or a party
change. It is reported because it shows the direction is not an artifact of the detectable
part of the contamination — dropping those registrants makes the newest group **younger,
not older** (median age at registration 35 → **32**, against 45–47 a decade earlier) and
leaves the Republican share where it was (57.5% → **57.7%**, against the high-60s and
low-70s of earlier rows). The dilution flows to **unaffiliated, not Democratic**: excluding
detectable re-registrants, the 2024 unaffiliated share rises 28.3% → **29.8%** while the
Democratic share falls 12.4% → **10.7%**. Across the full table the Democratic share sits
near 12% and the unaffiliated share climbs to 28%.

**So what the table shows is descriptive and bounded:** voters whose most recent
registration event is recent are younger, and more often unaffiliated, than voters whose
recorded registration event is much older. That is interesting — it is consistent with an
unaffiliated bloc that is young, which §III showed must adopt a party label to enter the closed
primary — but it is not a measurement of who is entering Idaho's
electorate, and nothing here licenses a projection.

*Three claims were removed from this section on 2026-08-15, after an external referee
pointed out that they all rest on a cohort reading the section itself had already
disavowed two paragraphs earlier: "a leading indicator" (the heading), "new registrants
are younger and less Republican", and "the rolls are slowly loosening the two-party grip".
The concession about `registration_date` had been added in an earlier round without
propagating to the conclusions built on top of it — the recurring failure mode in this
series, where a correction lands in one paragraph and the paragraph it invalidates
survives. The figures are unchanged; only what may be inferred from them is.*

---

## VII. The donor class is not the electorate — and leans against the rolls

Matching the roll to Idaho Sunshine state-campaign contributions links **23,613
registered voters to 114,806 donations ($13.64M)**, all falling in Idaho Sunshine's
**2023–2025** contribution window. Each donor is characterised by their **2026 party of
record**, not their party at the time of the gift — the two can differ, including through the
poll-book affiliation described in §IV — so the party rows below carry the same
current-classification caveat the electorate cuts do. The match uses the full-name
key alone (last name + full first name + ZIP5), the specification adopted across
this series on 2026-07-27 after a stratified blinded validation measured it at
100% precision (120/120) while initial-based keys ran 48–72%; see the donor-class
companion, Appendix F. The restriction buys that precision at a cost worth stating
where the findings are read rather than in a methods note: it **discards 11–19% of
matched donors, who are younger and less Democratic than those retained**, so some
part of the age and party skews below is selection rather than measurement. The
superseded all-tier figures are the more conservative ones and are reported in the
companion. Characterized by the donor's own party of record:

| Party | donors | donor share | reg share | skew | $ share |
|---|--:|--:|--:|--:|--:|
| Republican | 15,645 | 66.3% | 62.9% | +3.4 | 72.2% |
| Democratic | 5,097 | 21.6% | 11.8% | **+9.8** | 20.0% |
| Unaffiliated | 2,735 | 11.6% | 23.9% | **−12.3** | 7.6% |
| Other | 136 | 0.6% | 1.4% | −0.9 | 0.2% |

Even in a state this red, the donor class **over-represents registered Democrats**
— they are 12% of the roll but 22% of donors and give 20% of the money, nearly
double their registration weight — while the unaffiliated quarter is again nearly
absent (12% of donors, 8% of dollars). Republicans still supply the plurality of
money in absolute terms — **72.2%** of matched dollars — but relative to their
numbers the *most* over-represented donors are Democrats.

**That over-representation is heavily concentrated among donors to three ballot-measure
committees, one of which is this paper's own subject.** Reclaim Idaho, Idahoans for Open
Primaries and Idahoans United for Women and Families together drew gifts from **5,522 of
the 23,613 matched donors (23.4%)**; Reclaim Idaho alone is the largest recipient in the
Sunshine layer by gift count, with 36,490 person-gifts. Excluding donors who gave to any of
the three, the Democratic share of matched donors falls from **21.6% to 16.5%** and the
Republican share rises from 66.3% to 72.5% — so the +9.8-point Democratic
over-representation becomes **+4.6**. It does not vanish, and the direction of the over-representation
stands. But *Idahoans for Open Primaries* is the Proposition 1 campaign this paper analyses
in "What it means", and *Reclaim Idaho* is its parent organisation, so a material part of
the measured donor-class tilt sits with the mobilisation the paper's own conclusion is
about. That is a circularity, and it is reported here rather than left for a reader to
find.

*This paragraph said "more than half of that over-representation **comes from**" those
three committees until 2026-08-15. Excluding everyone who ever gave to them changes the
donor population — it does not decompose the original skew into causal parts, and the
people excluded differ from those retained in more ways than the exclusion criterion. The
figures are unchanged; the verb is now the one the design supports.*

The donor class is also **grayer and more concentrated** than the electorate:

- **Age.** 51% of matched donors are 65+, versus 31% of the roll and 33% of 2024
  general voters; the under-30 share is 2.1% versus 15% of the roll. (All three
  are computed on current-roll age, so they share one basis; the age-at-election
  figures in Section I are not interchangeable with them.) On that same basis the donor
  class is **not** the oldest layer measured here — the closed-primary electorate is at
  least as old: 51.9% of 2024 primary voters are 65+ (51.8% of Republican-ballot voters,
  52.0% of 2022 primary voters), against 51.3% of matched donors, all four at median age
  65. Donors and primary voters are effectively the same age; both are twenty points older
  than the roll.
- **Concentration.** The top 1% of matched donors supply **40%** of the matched
  dollars; the top 10% supply **71%**.
- **Geography.** Ada County (Boise) accounts for **50.3%** of matched donor dollars
  against **29.3%** of the roll — **1.72×** its registration weight. (On donors rather
  than dollars it is 37.3%, or 1.28×, so the concentration is in gift size more than in
  donor counts.) The bare 50% stood alone here until 2026-08-15, which reads as more
  geographically extreme than it is: Ada is also Idaho's largest county on the roll. The
  ratio is the measure the donor-class companion already uses for county concentration,
  so this is now consistent across the series as well as more honest — the money mirror of
  the population-vs-influence gap seen in New York (Manhattan) and Washington (Seattle).
- **Where the money sits.** Donor party mix tracks registration advantage. Grouping the
  35 districts by the same bands used in Section V, the 27 districts at R+40 or more hold
  14,594 donors who are **78% Republican / 13% Democratic**, while the eight districts
  between R+5 and R+40 hold 9,019 donors at a far more balanced **47% / 35%**. Those
  eight are where the two parties' donor bases meet — but note that none of them is
  within five points, so "smaller Republican advantage" is all this says; they were
  called "competitive-adjacent" here until 2026-08-15, which is the same
  outcome-semantics problem §V's band names had.

**Crossover — where the money goes.** Idaho Sunshine carries no party on the
recipient record, but recipient party can be reconstructed from data on hand (the
Secretary of State candidate roster plus party/committee name patterns), which
resolves the recipient for **51% of matched donors and 41% of matched dollars**
(`scripts/backfill_id_recipient_party.py`). Among donors whose money reached a
party-resolvable recipient:

| Donor's registration | → gave only to D | → gave only to R | mixed |
|---|--:|--:|--:|
| Republican | 19.1% | 79.0% | 1.9% |
| Democratic | **94.6%** | 3.0% | 2.3% |
| Unaffiliated | **77.1%** | 20.5% | 2.3% |

Registered Democrats are near-monolithic donors (95% give only to Democrats — the
same loyalty seen in New York), and unaffiliated donors lean nearly **4:1
Democratic** among the resolvable. Republicans predominantly fund Republicans (79%).

**Missingness is not uniform across these rows, and it decides which of them survive.**
Recipient party resolves for **50.9%** of Republican donors, **58.6%** of Democratic
donors and only **39.0%** of unaffiliated donors — the row with the strongest apparent
tilt is the least resolved. The paper's own explanation for the unresolved pool (local
Republican candidates and R-aligned PACs absent from the roster, so it skews Republican)
applies to *every* donor group, not only to Republicans. Assigning every unresolved donor
in a group to Republican-only giving — the hostile assignment for a Democratic-tilt
claim — gives:

| Donor's registration | resolved | D-only, observed | D-only under the hostile bound | R-only under the hostile bound | direction |
|---|--:|--:|--:|--:|:--|
| Registered Republican | 50.9% | 19.1% | 9.7% | 89.3% | — (the 19.1% is an upper bound) |
| Registered Democratic | 58.6% | 94.6% | **55.4%** | 43.2% | **survives** |
| Registered unaffiliated | 39.0% | 77.1% | 30.1% | 69.0% | **does not survive** |

So **Democratic donor loyalty is direction-safe and the unaffiliated Democratic tilt is
not.** The unaffiliated row is reported as descriptive: among unaffiliated donors whose
recipients can be resolved, giving runs about 4:1 Democratic, and a hostile assignment of
the unresolved 61% reverses that. Nothing here says the tilt is false — the hostile bound
is deliberately extreme — only that this design cannot rule its reversal out.

*Both bounds were added on 2026-08-15. The section previously called the Democratic loyalty
and the unaffiliated tilt "the robust, direction-safe reads", having already conceded in
the sentence before that non-random missingness inflates the Republican row. An external
referee pointed out that the concession applies to the unaffiliated row too and asked for
the party-specific bound. It was computed and one of the two claims did not survive it.*

---

## Boundary of inference

- **Age is imputed from a single integer.** Idaho gives current age, not DOB, so
  election-time ages are ±1 year and we report only bands and medians, never exact
  ages. This cannot manufacture the effects shown — the primary/general and
  registration-date-group gaps are far larger than a one-year imputation error.
- **How complete each reconstructed electorate is, and what that bounds.** A
  "reconstructed" electorate here is the set of *current* registrants carrying a vote
  record for that election. Everyone who has since left the roll is absent from it by
  construction, so the right question is how many that is — and the Secretary of
  State's certified ballot counts answer it directly:

  | election | ballots cast (SoS) | reconstructed | coverage | 65+ share, measured | 65+ share, bounded |
  |---|--:|--:|--:|--:|:--|
  | Nov 2024 | 917,469 | 898,877 | **98.0%** | 29.0% | **28.4 – 30.5%** |
  | Nov 2022 | 599,493 | 571,868 | **95.4%** | 34.4% | **32.8 – 37.4%** |
  | Nov 2020 | 878,527 | 647,029 | **73.6%** | 26.3% | **19.4 – 45.7%** |

  *Two of those ballot counts were wrong until 2026-08-15 — 2024 read 917,608 and 2022
  read 595,602, against the Secretary of State's 917,469 and 599,493. An external referee
  caught it against the SoS's current voter-statistics table. They are now pinned, with
  source and retrieval date, in
  [`reference/id_sos_turnout_history_2026-08-15.csv`](reference/id_sos_turnout_history_2026-08-15.csv),
  and read from there rather than typed into the verifier. **The verifier could not have
  caught this and no verifier of its design can**: asserting a paper against a constant
  checks the paper, and says nothing about whether the constant matches the world. Worse,
  the 2022 count *was* probed — against the same wrong literal, so the probe compared a
  number to itself and passed forever; and the 2024 count appeared only inside a regex
  anchor, where a figure looks probed and is not. Both shapes are fixed. The correction
  moves 2022's coverage from 96.0% to 95.4% and its bound from 33.0–37.0 to 32.8–37.4;
  the 2024 row's coverage and bound are unchanged at this precision.*

  The bound is arithmetic, not a model: the missing voters can be at worst all 65+ or
  none of them. **For 2022 and 2024 it is narrow enough that Section I's finding
  survives it** — the two intervals do not overlap, so the 65+ share genuinely rises
  from the presidential to the midterm electorate, whoever the missing voters were. **For 2020 it is not**, and
  Section I's 2020 row should be read as indicative only. That row is the one place
  in this paper where roll attrition is large enough to carry the result.

- **Survivorship — why this paper reports no turnout rates.** The 2026 roll (1.03M)
  is smaller than the ~1.18M registered at the 2024 election, because Idaho purges
  inactive registrations. (Idaho's extract carries no active/inactive
  flag, so we cannot confirm the two figures are on the same base; the ~13% gap is a
  net change between two stocks — **a lower bound on gross departures**, since anyone
  who joined since is netted against someone who left — and it is not turnover. It
  was described here as an upper bound on turnover until 2026-08-15, which inverts
  what a stock difference can support. The clause attributing part of the gap to the
  churn of the 121,015 election-day registrants was removed at the same time: at least
  90.4% of them are still on the roll, see §III.) Dividing past voters by this
  shrunken roll inflates every turnout rate: our all-voter 2024 general rate is ~94%
  against the official **77.8%** (917,469 ballots / 1,178,750 registered, Idaho SoS),
  and 2020 even computes above 100% — voters who re-registered after 2020 carry a
  later `registration_date`, dropping out of the denominator while staying in the
  numerator. The bias is not uniform (larger for the young, unaffiliated, and movers),
  so cross-group rate comparisons are unreliable too. We therefore report **composition
  shares** — each group's share of the actual electorate — throughout, which need no
  registration denominator.
- **The DIRECTION of the survivorship bias is not established here, and the claim that it
  ran against the gray finding is withdrawn (2026-08-26, author's decision).** The table
  above says how much room the missing voters have; nothing in this file says which way they
  lean. What stood here was an inference from **Washington's** September-2023 and 2026 roll
  snapshots — where departing voters do skew older — generalised to Idaho on the grounds that
  mortality-dominated attrition is a general mechanism, and concluding that Idaho's true past
  electorates "were, if anything, grayer than measured". **Washington's snapshot is evidence
  about Washington's attrition.** Idaho retains no prior snapshot, so the direction is simply
  not observable here, and the cross-state companion reaches the opposite conclusion for Idaho
  from the load's own churn profile: attrition larger among the young, the unaffiliated and
  movers means the reconstruction over-retains seniors, so correcting it would *lower* Idaho's
  senior share. That companion is the better-grounded of the two and says in as many words that
  nothing in it tests the direction either. **The finding does not need a direction**: the
  arithmetic bounds above already show the 2022 and 2024 results survive any composition of
  the missing voters, while the 2020 estimate does not — which is a stronger statement than a
  signed guess, and it is the one the paper now makes.
  *(Treat `who-decides-cross-state.md`'s survivorship treatment as canonical for this series.)*
- **This is a claim about composition and closure, not ideological extremism.**
  Sides, Tausanovitch, Vavreck & Warshaw (2020) find primary electorates are not
  dramatically more extreme than their party's rank-and-file, and that openness rules
  do not change that — a result that rebuts a *polarization* argument. It does not
  bear on the argument here, which is about *who takes part* (one party, older, the
  unaffiliated bloc almost absent) and what it costs them to, not about the ideology of
  those who show up. We make no claim that Idaho's primary voters are more extreme than other
  Republicans.
- **The donor layer here is state (Idaho Sunshine) by design.** It characterizes the
  people who fund Idaho's *state* campaigns — the relevant layer for state
  electoral health. (Idaho's **federal** FEC contributions were since loaded too —
  770,765 rows / $76.2M outflow + inflow, with 23,303 FEC voter↔donor matches on the
  full-name key. The cross-state comparison in
  [`cross-state-fec-money.md`](cross-state-fec-money.md) §F5 uses the **pooled** Idaho
  match instead — both money systems in one table, 41,136 donors — and its mix
  D 20% / R 67% / O 13% closely tracks the Sunshine-only mix below. The age skew survives
  the matcher-bias re-weighting in ID as in WA/NY.) Recipient party is not in the feed; it
  is reconstructed for
  ~51% of matched donors (candidate roster + committee-name patterns), so the
  crossover table above is limited to party-resolvable recipients and the
  majority-party crossover rate is an upper bound (see §VII).
- **Lean is never imputed for the unaffiliated.** Every "unaffiliated" figure is a
  registration fact, not an inferred partisanship.

---

## What it means

Idaho is the deep-red pole of this series. Washington showed the off-year electorate is
older; New York showed the shrinkage is party-shaped and excludes a young unaffiliated
bloc; Idaho shows what happens when November choices are common but November competition
is rare. **In 2024 the Republican nomination process produced the winner of 90 of Idaho's
105 legislative seats — but the venue was split: 52 at a contested Republican primary and
38 at candidate filing, while Democrats took the remaining 15 in November, nine of them by
beating a single-filer Republican.** Republican-ballot primary voters were substantially older
than the presidential electorate and than the registration
base: median 63, with 46.7% aged 65 or over. And a quarter of the state, young, can take part
in that primary only by adopting a party label first.

*(Two phrases here restated an inference §V withdraws, and are corrected as of 2026-08-11: "in
districts where the general cannot overturn it" and "the only contest that counts". §V records
why — Democrats won 15 of 105 legislative seats in November 2024, and nine of the 47
single-candidate Republican primaries were won by a Democrat, so the general demonstrably can
change the outcome and the primary is not the only contest that counts. Both sat in this
conclusion, which is outside every coverage span, while the section they contradict was gated.)*

*(A second sweep, 2026-08-29, after an external series review: this paper still used
"resolved", "decisive" and "binding" as empirical labels for a decision event its own §I
rebuild says the data cannot identify — "the binding choice was candidate filing" (§IV),
"where most seats are resolved" (§V and this section's opening), "move the decisive
contest" and "Idaho's decisive stages" (both below, in the remedies sentence and the
Proposition 1 note). All are reworded to the observable taxonomy — nomination venue, last
contested stage, ballot availability, observed margin — with every count unchanged. Key's
own formulation in Related work stays, as another author's theory in that author's words.)*

*(A further correction the same day, 2026-08-29, after the external reviewer returned for a
second pass. It found four things the first sweep left, all prose and no figure moved. (1) The
"Variable 1" cut in §IV and the abstract was still framed as a single "nomination" variable,
although two of its four rows — a general-election loss to a Democrat, a seat with no Republican
on the ballot — are outcomes, not nominations; it is now stated as the cross-tabulation it is,
Republican nomination configuration against the November winner, and the 90-seat count is
derived from it separately. (2) The decision-event construct the first sweep retired survived in
a wider family the four register literals did not reach — "the contest that decides" (§§II and
VI), "the stage that does the most work" (§IV and the conclusion), and the abstract's "where
governing choices are made"; each is reworded to name the observable stage, and the
`id-decision-stage-labels` register pattern is widened to forbid the family. (3) The opening and
§III had claimed that almost all unaffiliated voters decline the affiliation cost, and that
their primary share "is a measure of how few pay that price" — a participation rate this paper's
refusal of turnout rates cannot support; §IV's narrower reading, a lower bound unrecoverable
from one snapshot, is the one that stands. (4) "growing and young" is cut to "young" here and in
§VI, because §VI itself proves this file cannot support a stock-change claim. Each of the last
three is now guarded by a register pattern shown failing before it was applied.)*

Two reforms directly target the institutional features measured here: dropping the
party-affiliation requirement at the primary, or sending a wider candidate field on to the
high-turnout November ballot. Idaho has recently
weighed and rejected a measure that would have done both. **Proposition 1 (2024)** — which would have replaced the closed
primary with a single top-four open primary and added ranked-choice voting in
November — **lost 69.6% to 30.4%** (269,960 Yes to 618,753 No, Idaho SoS).

**This paper cannot say which voters produced that result, or why.** Proposition 1 was
decided in the November general — the electorate this paper's own §III shows returns the
unaffiliated bloc to roughly its registration weight. They were not shut out of that
decision, and no individual-level Proposition 1 vote is linked here to age or registration
party. The No majority is consistent with Republican primary voters defending the closed
primary, with unaffiliated voters declining it, with Democrats declining it, with hostility
to ranked-choice voting specifically, with objection to the two reforms being bundled, or
with some mixture. The result is reported; the mechanism is not identified.

*What stood here until 2026-08-15 was a stronger claim: that the result "illustrates
[the paper's] mechanism", and that Idaho is a **self-reinforcing equilibrium** in which
"the people currently outside the room do not, from outside it, have the numbers to open
the door". An external referee identified this as the paper's most serious interpretive
overreach, and it is — it argues against §III on the paper's own evidence, since the venue
that rejected Proposition 1 is precisely the one where §III finds the excluded bloc is not
excluded. The paragraph is withdrawn rather than hedged. What survives is narrower and
still worth saying: the stages where Idaho's Republican candidate fields narrow are the filing
deadline and a closed primary
whose electorate is markedly older than the roll — a median of **63** against **52**, and a
65-and-over share twenty points higher — and the reform that would have changed the second of
those was put to the voters and defeated.*

---

## Related work

This paper documents, with unusually rich individual-level data, mechanisms that
are largely established; its contribution is the measurement, the senior-share parity
between the two parties, and the separation of nomination stage from contestation stage —
not the discovery of the mechanisms. It sits in these literatures:

- **The one-party primary as the real election.** V.O. Key, *Southern Politics in
  State and Nation* (1949) — in a one-party polity the dominant party's primary is
  the decisive contest; the general ratifies it. This paper measures a modern case at
  the individual level, while finding on Idaho's own results that the frame's
  "ratifies" half does not hold here — §V records where it fails.
- **Surge-and-decline / turnout composition by salience.** Campbell, "Surge and
  Decline" (1960); Wolfinger & Rosenstone, *Who Votes?* (1980); Leighley & Nagler,
  *Who Votes Now?* (2013). Section I's presidential→midterm falloff is this.
- **Off-cycle / election-timing and representation.** Anzia, *Timing and Turnout*
  (2014); Hajnal & Trounstine (2005); Kogan, Lavertu & Peskowitz (2018, on school
  boards); Einstein, Palmer, Hamilton & Singer, "Age and Homeownership Drive the
  Local Turnout Gap," *Urban Affairs Review* (2025) — the closest analog to the age
  result. Provides relevant background for Idaho's local elections but is not tested by the
  presidential–midterm comparison here.
- **Primary-electorate representativeness (the tension).** Sides, Tausanovitch,
  Vavreck & Warshaw, "On the Representativeness of Primary Electorates" (2020) —
  primaries are not dramatically more *extreme*; distinguished here (our claim is
  composition/closure, not extremism).
- **Independents / the unaffiliated.** Klar & Krupnikov, *Independent Politics* (2016).
- **Voter-file / individual-level method.** Ansolabehere & Hersh, "Validation…"
  (2012); Hersh, *Hacking the Electorate* (2015). On the roll-churn caveat: Feder &
  Miller, "The Racial Burden of Voter List Maintenance Errors," *Science Advances*
  (2020).
- **The donor class.** Bonica, DIME / "Mapping the Ideological Marketplace" (2014);
  Schlozman, Verba & Brady, *The Unheavenly Chorus* (2012); Hill & Huber, "…the
  Contemporary Donorate" (2017, on donors' older skew); Grumbach, Sahn & Staszak
  (2022).
- **The reform just rejected.** Idaho Proposition 1 (2024), top-four open primary +
  ranked-choice voting, defeated 69.6%–30.4% (Idaho SoS).

---

## Methods & reproducibility

```bash
# 1. Load the Idaho voter file -> data/id_vrdb.duckdb (voters + voter_participation)
python scripts/load_id_voters.py

# 2. Turnout by age x party + the closed-primary flagship (Sections I–IV)
python scripts/diag_id_turnout_party.py

# 2b. Contested vs uncontested primaries (Section IV) — SoS 2024 primary canvass
python scripts/diag_id_primary_contested.py

# 3. Donor class x party (Section VII) — resolve recipient party (crossover),
#    then match; writes committee_party_override + voter_donor_affiliation_state.
#    --source state is the Sunshine layer this section reports; --source fec builds
#    the federal panel used by the cross-state comparison. Both default to the
#    full-name key (the primary specification).
STATE=ID python scripts/backfill_id_recipient_party.py
STATE=ID python scripts/match_id_voters_to_donors.py --source state

# 4. Electorate extras: unaffiliated bloc, decomposition, registration-date groups,
#    registration-advantage map, donor-mix x competitiveness (Sections I, III, V, VI, VII)
python scripts/diag_id_electorate_extras.py
```

Source: `data/raw/id/id_statewide_voter_history_20260629.csv` (Idaho SoS
statewide voter file with history, 2026-06-29 export; public record). Party
buckets: REP / DEM / UNAFF (unaffiliated) / OTHER (Libertarian + Constitution).
All headline numbers above are re-derivable by running the scripts in this block.
