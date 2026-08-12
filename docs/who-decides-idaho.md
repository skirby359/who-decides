# Who Decides Idaho?

### The one-party electorate, resolved by party — from 1.03 million individual registration and vote records

**Stephen Kirby** · Tikor Consulting · July 2026

*AI-assisted drafting and analysis review. All figures are reproducible from
public-record data available through lawful request and from the open-source scripts
cited below, including `scripts/verify_who_decides_id.py`. The paper source, code, and
data-acquisition recipe are public at <https://github.com/skirby359/who-decides>; the
underlying voter file is not redistributed. Contact: kirby@tikorconsulting.com.*

*Deep-red companion to [`who-decides-washington.md`](who-decides-washington.md)
and [`who-decides-new-york.md`](who-decides-new-york.md). Washington showed the
off-year electorate is **older**; New York (deep blue) showed *whose* electorate
ages and who is locked out. Idaho completes the set from the other pole: a state
where the **closed Republican primary resolves the great majority of seats** — so the
question "who decides" has a sharper, more literal answer than in any two-party
state. *(This line called the November general "a formality" until 2026-08-11. It is not:
Democrats won 15 of Idaho's 105 legislative seats in November 2024, including nine whose
Republican primary drew a single candidate — see §V, which withdraws that inference
explicitly.)* **DRAFT — pending human/editorial sign-off.
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
1.03M from the ~1.18M registered at the 2024 election (Idaho purges aggressively and
same-day registrants churn). Voters who cast a past ballot but were since
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

In a one-party state, the general election is not where governing choices are made. Idaho is
**63%** Republican and **12%** Democratic by registration, and its officeholders are chosen in a
closed May Republican primary that most of the state cannot or does not enter. Using the
statewide voter file for **1,029,938** registrants, with party of record and the party ballot
each voter actually pulled, this paper measures who enters that decisive contest. Two findings
are specific to Idaho rather than replications of the off-cycle turnout literature. First, the
age gap is party-neutral: Republicans and Democrats among 2024 general voters are within a
fraction of a point on the 65-and-over share, **31.7%** against **31.5%**, and four years apart
on median age, so Idaho's youth sits in the unaffiliated bloc rather than in either party —
inverting the national older-is-more-Republican pattern and reversing what the New York
companion finds. Second, the file records the party ballot each voter pulled, so unaffiliated
participation in the decisive primary is observed directly rather than inferred from
registration alone — with an important qualification developed in Section IV: under Idaho
Code § 34-904A an unaffiliated elector who requests a **Republican** ballot affiliates at
the poll book and is thereafter registered Republican, while a Democratic ballot carries no
such conversion. Because the file is a single 2026 snapshot with no affiliation date, the
unaffiliated shares reported for past primaries are **lower bounds**, and the bound is
tighter the closer the primary is to the snapshot. The May 2024 primary
electorate runs **85.2%** Republican by registration against **62.9%** of the roll, a
Republican-minus-Democratic margin of **76.8** points against **51.1** on the rolls, and its
Republican-ballot voters have a median age of **63** with **46.7%** aged 65 or over. Yet the
primary decides only where it is contested: of **99** Republican legislative primaries in 2024,
**52** were contested and **47** offered a single candidate. Of those 47, **38** were
won by a Republican in November and **9** by a Democrat, so the binding choice occurred at
candidate filing for **38 of the 90 Republican-held seats (42%)** — not for half of them, and
not for all 47. Every one of the **35**
legislative districts leans Republican and none is competitive by registration. The paper
reports composition shares and deliberately reports no turnout rates, because a current-extract
roll that has contracted from about 1.18 to 1.03 million inflates every rate.

**Keywords.** one-party dominance; closed primaries; nominating electorate; voter file; party
registration; unaffiliated voters; uncontested elections; turnout composition; election timing;
Idaho

---

## The question

How *many* people vote is the wrong question for understanding how a state is
governed. The right one is *who* — and in Idaho the answer is unusually stark,
because Idaho is a one-party state by registration (**63% Republican, 12%
Democratic, 24% unaffiliated**) whose officeholders are chosen not in November
but in a **closed May Republican primary** that most of the state cannot or does
not enter.

The short answer: **the people who actually decide Idaho are a gray, Republican,
self-selected slice of an already-Republican state.** In November the electorate
is broadly representative; in the primary that settles nearly every seat it is
older and drawn almost entirely from one party — and the 24% of
registrants who decline a party are, by the design of the closed primary,
standing outside the room where it happens.

Two of these findings are specific to Idaho, not a replication of the off-cycle
turnout literature. First, the age gap here is **party-neutral**: Idaho's
Republicans and Democrats are nearly the same age, and the young sit in the
*unaffiliated* bloc rather than in either party — inverting the national
"older-is-more-Republican" pattern and reversing what the New York companion found.
Second, the file records the party ballot each voter actually pulled, so unaffiliated
participation in the decisive primary is **observed rather than inferred from registration
alone**. It is not, however, cleanly *measured*: the instrument is partly destroyed by the
act it records, for the reason set out in Section IV.

---

## I. The off-year electorate is older — Idaho replicates Washington

Share of the general-election electorate by age band:

| Election | Type | 18–29 | 30–44 | 45–64 | 65+ | median |
|---|---|--:|--:|--:|--:|--:|
| Nov 2024 | Presidential | 15.2% | 23.4% | 32.4% | 29.0% | 52 |
| Nov 2022 | Midterm | **8.6%** | 20.7% | 36.3% | **34.4%** | 57 |
| Nov 2020 | Presidential | 13.8% | 23.9% | 36.1% | 26.3% | 52 |
| — | Registration baseline (2026) | 15.2% | 22.8% | 30.9% | 31.0% | 52 |

As the contest shrinks (presidential → midterm), the under-30 share nearly halves
(15.2% → 8.6%) and the 65+ share swells (29% → 34%); median age rises from 52 to
57. **Behavior, not rolls** — the roll's age structure barely moves between the two
elections, so the shift is who *shows up*, not who is registered. A Das-Gupta
decomposition points the same way (attributing the 65+ rise mostly to turnout
rather than to roll composition), though in Idaho that rate-based cut carries the
survivorship caveat above; it is reported here as directionally consistent with
Washington and New York, where the roll is stable and the decomposition is reliable.
The young *choose not to vote* in lower-salience cycles — the classic
**surge-and-decline** pattern (Campbell 1960), measured here across the
presidential-to-midterm drop. (That is distinct from, though it rhymes with, the
*off-cycle / odd-year local-election* timing literature — Anzia 2014; Hajnal &
Trounstine 2005 — which motivates the on-cycle remedy discussed below: Idaho's
local offices, like Washington's, sit off the federal calendar entirely.) As in
Washington and New York, this is an institutional, timing-fixable pattern, not a
registration artifact.

---

## II. In Idaho the age gap is *not* partisan — the youth is in the middle

This is where Idaho diverges sharply from New York. In New York the Republican
electorate ages hardest; in Idaho the two major parties age almost identically.
Share of each party's 2024 general-election voters by age, plus median age:

| Party | share 65+ | share 18–29 | median age |
|---|--:|--:|--:|
| Republican | 31.7% | 12.7% | 54 |
| Democratic | 31.5% | 19.4% | 50 |
| **Unaffiliated** | **21.3%** | **19.6%** | **46** |
| Other (Lib/Con) | 10.0% | 23.0% | 39 |

The Republican and Democratic electorates are within a fraction of a point on the
65+ share and only four years apart on median age. Idaho's **youth lives outside
the two major parties** — in the unaffiliated bloc (median 46) and the minor
parties (median 38). That matters because, as Sections III–IV show, those are
precisely the blocs that vanish from the contest that decides. The generational
sorting that makes "older = redder" a useful heuristic nationally simply does not
hold here: in Idaho, older = *more attached to a party at all*, not more
Republican.

---

## III. The unaffiliated quarter: turns out in November, locked out in May

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

The story is in the last two columns. The unaffiliated are **22.6% of the 2024
general electorate** — essentially their full 23.9% of the roll, so in November they
show up. But they are only **5.9% of the May primary electorate**: a bloc that is
nearly a quarter of the state, and a quarter of the November vote, casts about **one
in seventeen** primary ballots. This is not apathy; it is architecture. Idaho's
Republican primary is **closed**, so an unaffiliated voter must first affiliate to
vote in the contest that actually chooses the winner. A quarter of the state opts to
stay out — and in doing so sits out the decision.

> **A note on the roll itself.** Idaho's registration file shrank from **~1.18M** at
> the November 2024 election to **~1.03M** in this 2026 snapshot — roughly a **13%
> turnover in eighteen months**, from routine list maintenance (inactive-voter
> removal, change-of-address, deaths) compounded by the non-persistence of the
> 121,000 voters who registered same-day on Election Day 2024. That churn is the
> reason historical turnout *rates* cannot be reconstructed from a single snapshot
> (Methods) — but it is also a civic-health datapoint in its own right: a roll that
> turns over this quickly is a moving target for any list-based registration or
> mobilization effort, and it means "the electorate" is a substantially different set
> of people each cycle. Washington's file, by comparison, is markedly more stable.

## IV. The closed primary decides most seats — and its electorate is the grayest measured here

In a state where both congressional districts and all 35 legislative districts
lean Republican **by registration** (Section V), the May Republican primary resolves the
great majority of legislative seats — though not all: Democrats won 15 of Idaho's 105 legislative seats in
November 2024 (Section V). Three facts describe that primary's electorate.

**The primary electorate is far more Republican than November.** Party
composition of each contest, as R-minus-D margin:

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

**But "the primary decides" only where the primary is *contested* — and often it
isn't.** Of the 105 legislative seats, **99 drew a Republican primary in 2024** (the other
six are safe-Democratic seats where no Republican filed); of those 99, just **52
(53%) were contested** and **47 (47%) had a single Republican on the ballot**
(`scripts/diag_id_primary_contested.py`, reconciled seat-by-seat against the
35-district / 105-seat frame — every race maps 1:1 to a seat, no duplicates; the
contested counts match Ballotpedia's independent tallies cycle-by-cycle, exact for
2022 and 2024 and within ±2 for 2016 and 2018). Those 47 single-candidate primaries did not all settle a seat, and the
difference matters: **9 of them were won by a Democrat in November**, while all 52
contested-primary seats went Republican. So the seat was effectively settled at candidate
*filing* — an earlier and narrower gate than the primary electorate itself — for **38 of the
90 Republican-held seats, 42%**. For that 42% of Republican-held seats the "decisive
contest" was no contest at all; for the rest it was either the closed, gray, one-party
electorate described here, or, in fifteen seats, the November general.

**That contest is, however, growing.** Across the loaded cycles the Republican
legislative-primary contested rate has roughly *doubled* — **36% (2016) → 43%
(2018) → 68% (2022) → 53% (2024)** — peaking in 2022, the first post-redistricting
cycle and the height of the state GOP's traditional-vs-hardline fights. (2020 is
not comparable: the SoS published that mail-only cycle's legislative results at
county level only.) Two things are therefore true at once, and both matter: the
decisive Republican primary is *increasingly* a real choice for those who can vote
in it, even as it stays *closed* to the ~24% of registrants who are unaffiliated.
Democratic legislative primaries, by contrast, are almost never contested (2–11%
across these cycles) — the mirror image of one-party dominance.

**The primary electorate is older than even the Republican rolls.** Comparing all
Republican registrants to those who actually pulled a Republican ballot in 2024:

| Group | 18–29 | 30–44 | 45–64 | 65+ | median |
|---|--:|--:|--:|--:|--:|
| Republican registrants (all roll) | 12.6% | 20.4% | 32.5% | 34.5% | 55 |
| Republican-ballot primary voters, 2024 | **5.0%** | 14.2% | 34.1% | **46.7%** | **63** |

The people who nominate Idaho's officeholders are a gray subset of an already-red
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
is the paper's central measurement caveat.** Under Idaho Code § 34-904A, an unaffiliated
elector who requests a Republican primary ballot signs a Declaration of Party Affiliation
at the poll book, and is a registered Republican from that moment; requesting a Democratic
ballot does not affiliate anyone, because the Idaho Democratic Party admits unaffiliated
voters. `voters.party` is a **single current snapshot** — the raw file carries a party
description and **no affiliation date** — so an unaffiliated voter who entered the
Republican primary is, by construction, no longer unaffiliated when we look.

The data shows exactly that signature and nothing else explains it. The Republican column
falls monotonically with distance from the snapshot (27.7 → 9.7 → 1.7) while the Democratic
column does not (52.6 → 52.5 → 65.6). Among today's unaffiliated voters who pulled a
**Republican** ballot in 2022, **55.8%** carry a registration date *after* that primary —
they re-registered, reverting to unaffiliated — against **15.2%** of those who pulled a
Democratic ballot. And voters who are Republican today pulled a Republican ballot in
97.3 / 96.9 / 97.7% of cases across the three primaries, a concordance that is definitional
rather than behavioural.

**What this costs the finding.** The 5.9% unaffiliated share of the May 2024 primary
electorate is not a measurement of unaffiliated participation; it is a measurement of
unaffiliated *non-participation in the Republican primary*, since participation there
removes a voter from the category. The honest estimates are the 2026 figures, closest to
the snapshot: unaffiliated registrants are **7.3%** of that primary electorate. The 2024 and
2022 figures are **lower bounds**, and the conversion is unobservable from this source, so
the gap cannot be closed with the data at hand — a defect the New York companion avoids
because enrollment there must precede the primary by months and is bounded at 0.7–1.4%.

**The direction of the lock is also not what an earlier reading suggested.** The Republican
share of *all* primary ballots cast falls across the three cycles — **86.1% (2022), 83.4%
(2024), 79.5% (2026)** — while the Democratic ballot share rises. Whatever is happening to
Idaho's one-party primary, it is not tightening on this measure.

---

## V. Safe-seat Idaho — there is no competitive district by registration

Districts by registration lean (Republican % − Democratic % of registrants):

| Level (n) | Safe R (R+40+) | Likely R (R+20–40) | Lean R (R+5–20) | Competitive | Any D lean |
|---|--:|--:|--:|--:|--:|
| Congressional (2) | **2** | 0 | 0 | 0 | 0 |
| Legislative (35) | **27** | 4 | 4 | **0** | **0** |

Both U.S. House seats and every one of the 35 legislative districts lean
Republican; **none is competitive by registration, and none leans Democratic.**

**Registration lean is not an outcome, and here it is decisively not one.** In the November
2024 general, Democrats won **15 of Idaho's 105 legislative seats** (90 R / 15 D, matching
the seated 2025–26 legislature), including seats in districts this table places outside the
competitive band. Of the 47 seats whose Republican primary drew a single candidate, **nine were won by a
Democrat in November** — so for those the choice was settled by the
general, not at filing. An earlier version of this section wrote that "where the general
election cannot change an outcome" the primary is the only decisive contest; that inference
does not survive its own state's results, and the companion safe-seat paper withdrew a
stronger version of it on *observed margins*, which are better evidence than registration.
It is not reinstated here on weaker evidence.

What the table does support is narrower: **Idaho has no district where registration alone
would lead one to expect a Democratic win**, so the Republican primary is the contest where
the great majority of seats are effectively resolved — a claim about where the action is
concentrated, not about what November can do. The three-state superlative that stood here is
also withdrawn: Washington publishes no party registration at all, so no comparable
registration-lean map exists for it, and comparing this table to the safe-seat paper's
observed margins compares two different measures.

---

## VI. A leading indicator: new registrants are younger and less Republican

Party mix and age of each registration cohort still on the current roll, keyed on
`registration_date`:

| Registration dated | registrants | % REP | % DEM | % UNAFF | median age at that date |
|---|--:|--:|--:|--:|--:|
| 2008 | 22,559 | 66.4% | 5.3% | 28.0% | 45 |
| 2012 | 30,843 | 71.5% | 11.8% | 15.9% | 47 |
| 2016 | 61,465 | 65.5% | 12.1% | 21.2% | 46 |
| 2020 | 153,710 | 60.8% | 12.2% | 25.1% | 43 |
| 2022 | 97,593 | 64.8% | 11.3% | 21.8% | 44 |
| 2024 | 263,322 | **57.5%** | 12.4% | **28.3%** | **35** |

**`registration_date` is the date of a voter's most recent registration event, not
their first.** Idaho writes a new date on an address change, a party change — including
the §34-904A poll-book affiliation of Section IV — and an election-day registration.
Of the registrants dated 2024, **36.3% had already voted in an earlier election**; of
those dated 2022, **43.7%** had. Both are floors, because the file's vote history
reaches back only to 2020, so a 2024 registrant who last voted in 2018 is
indistinguishable from a genuinely new one. The 2008–2020 rows cannot be cleaned at
all for the same reason, and the 263,322 registrants dated 2024 — a quarter of the
roll in one year — is a re-registration count, not a count of new voters.

That matters for the label and not for the direction. Dropping the registrants who
are *detectably* re-registered makes the newest cohort **younger, not older** (median
age at registration 35 → **32**, against 45–47 a decade earlier) and leaves the
Republican share where it was (57.5% → **57.7%**, against the high-60s and low-70s of
earlier rows). Re-registrants are by construction people who were already voting, so
their removal sharpens the young skew rather than explaining it.

The dilution flows to **unaffiliated, not Democratic**, and the clean cut strengthens
that too: excluding detectable re-registrants, the 2024 unaffiliated share rises
28.3% → **29.8%** while the Democratic share falls 12.4% → **10.7%**. Across the full
table the Democratic share sits near 12% and the unaffiliated share climbs to 28%,
but the two-decade comparison is between rows built on different amounts of
contamination and should be read as a direction, not a series. The rolls are slowly
loosening the two-party grip, and toward the bloc that Section III showed is
structurally shut out of the primary. Absent a change in primary rules, a growing,
younger, unaffiliated electorate has *less* say in who governs, not more.

---

## VII. The donor class is not the electorate — and leans against the rolls

Matching the roll to Idaho Sunshine state-campaign contributions links **23,613
registered voters to 114,806 donations ($13.64M)**. The match uses the full-name
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
money in absolute terms, as a 63%-Republican state must, but relative to their
numbers the *most* over-represented donors are Democrats.

**More than half of that over-representation comes from three ballot-measure committees,
one of which is this paper's own subject.** Reclaim Idaho, Idahoans for Open Primaries and
Idahoans United for Women and Families together drew gifts from **5,522 of the 23,613
matched donors (23.4%)**; Reclaim Idaho alone is the largest recipient in the Sunshine layer
by gift count, with 36,490 person-gifts. Excluding donors who gave to any of the three, the
Democratic share of matched donors falls from **21.6% to 16.5%** and the Republican share
rises from 66.3% to 72.5% — so the +9.8-point Democratic over-representation becomes
**+4.6**. It does not vanish, and the direction of Finding 3 stands. But *Idahoans for Open
Primaries* is the Proposition 1 campaign this paper analyses in "What it means", and *Reclaim
Idaho* is its parent organisation, so a material part of the measured donor-class tilt is
the mobilisation the paper's own conclusion is about. That is a circularity, and it is
reported here rather than left for a reader to find.

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
- **Geography.** Ada County (Boise) alone accounts for **50%** of matched donor
  dollars — the money mirror of the population-vs-influence gap seen in New York
  (Manhattan) and Washington (Seattle).
- **Where the money sits.** Donor party mix tracks district safety. Grouping the
  35 districts by the same registration lean used in Section V, the 27 Solid-R
  districts hold 14,594 donors who are **78% Republican / 13% Democratic**, while
  the eight Likely-R and Lean-R districts hold 9,019 donors at a far more balanced
  **47% / 35%**. Idaho's competitive-adjacent seats are where the two parties'
  donor bases actually meet.

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
Democratic** when their money can be traced, echoing the blank-bloc donor lean in
New York. Republicans predominantly fund Republicans (79%); the apparent ~19%
giving only to Democrats is an **upper bound** — the unresolved recipient pool
(local Republican candidates and R-aligned PACs not in the roster) skews
Republican, so Republican donors' Republican-side giving is disproportionately the
part left untraced. The robust, direction-safe reads are the Democratic loyalty
and the unaffiliated Democratic tilt.

---

## Boundary of inference

- **Age is imputed from a single integer.** Idaho gives current age, not DOB, so
  election-time ages are ±1 year and we report only bands and medians, never exact
  ages. This cannot manufacture the effects shown — the primary/general and
  cohort gaps are far larger than a one-year imputation error.
- **How complete each reconstructed electorate is, and what that bounds.** A
  "reconstructed" electorate here is the set of *current* registrants carrying a vote
  record for that election. Everyone who has since left the roll is absent from it by
  construction, so the right question is how many that is — and the Secretary of
  State's certified ballot counts answer it directly:

  | election | ballots cast (SoS) | reconstructed | coverage | 65+ share, measured | 65+ share, bounded |
  |---|--:|--:|--:|--:|:--|
  | Nov 2024 | 917,608 | 898,877 | **98.0%** | 29.0% | **28.4 – 30.5%** |
  | Nov 2022 | 595,602 | 571,868 | **96.0%** | 34.4% | **33.0 – 37.0%** |
  | Nov 2020 | 878,527 | 647,029 | **73.6%** | 26.3% | **19.4 – 45.7%** |

  The bound is arithmetic, not a model: the missing voters can be at worst all 65+ or
  none of them. **For 2022 and 2024 it is narrow enough that Section I's finding
  survives it** — the two intervals do not overlap, so the 65+ share genuinely rises
  as salience falls, whoever the missing voters were. **For 2020 it is not**, and
  Section I's 2020 row should be read as indicative only. That row is the one place
  in this paper where roll attrition is large enough to carry the result.

- **Survivorship — why this paper reports no turnout rates.** The 2026 roll (1.03M)
  is smaller than the ~1.18M registered at the 2024 election, because Idaho purges
  inactive registrations and same-day registrants churn — 121,015 of that 1.18M
  registered on election day itself. (Idaho's extract carries no active/inactive
  flag, so we cannot confirm the two figures are on the same base; the ~13% gap is
  an upper bound on turnover, not a measurement of it.) Dividing past voters by this
  shrunken roll inflates every turnout rate: our all-voter 2024 general rate is ~94%
  against the official **77.8%** (917,608 ballots / 1,178,750 registered, Idaho SoS),
  and 2020 even computes above 100% — voters who re-registered after 2020 carry a
  later `registration_date`, dropping out of the denominator while staying in the
  numerator. The bias is not uniform (larger for the young, unaffiliated, and movers),
  so cross-group rate comparisons are unreliable too. We therefore report **composition
  shares** — each group's share of the actual electorate — throughout, which need no
  registration denominator.
- **And within that bound, the bias runs *against* the gray finding.** The table
  above says how much room the missing voters have; this says which way they lean.
  Comparing Washington's September-2023 and 2026 roll snapshots — Idaho retains no
  prior snapshot, and a departed voter can only be aged from one — the 504,103 voters
  who left the rolls are **33.1% 65+ against 23.9% of the 4,782,028 retained**.
  Attrition dominated by mortality is a general mechanism, so reconstructing a past
  electorate from a current roll *under-counts* its oldest members. The true past
  electorates were, if anything, grayer than measured here: the age findings sit
  toward the low end of their intervals, not the middle.
- **This is a claim about composition and closure, not ideological extremism.**
  Sides, Tausanovitch, Vavreck & Warshaw (2020) find primary electorates are not
  dramatically more extreme than their party's rank-and-file, and that openness rules
  do not change that — a result that rebuts a *polarization* argument. It does not
  bear on the argument here, which is about *who is in the room* (one party, older,
  the unaffiliated excluded) and who is shut out, not about the ideology of those who
  show up. We make no claim that Idaho's primary voters are more extreme than other
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

Idaho is the limiting case of the on-cycle-timing argument. Washington showed the
off-year electorate is older; New York showed the shrinkage is party-shaped and
excludes a young unaffiliated bloc; Idaho shows what happens when a single closed
primary, not November, is the entire game for most seats. The decision is made by a Republican
electorate grayer than the Republican rolls, in districts where the general rarely — but not
never — overturns it, and for 47 of the 99 Republican primaries the ballot carried a single
name, while a growing quarter of the state stands outside the contest that resolves most seats.

*(Two phrases here restated an inference §V withdraws, and are corrected as of 2026-08-11: "in
districts where the general cannot overturn it" and "the only contest that counts". §V records
why — Democrats won 15 of 105 legislative seats in November 2024, and nine of the 47
single-candidate Republican primaries were won by a Democrat, so the general demonstrably can
change the outcome and the primary is not the only contest that counts. Both sat in this
conclusion, which is outside every coverage span, while the section they contradict was gated.)*

The obvious remedies are institutional: open the primary, or move the decisive
contest onto the high-turnout November calendar. But Idaho has just weighed and
rejected the first. **Proposition 1 (2024)** — which would have replaced the closed
primary with a single top-four open primary and added ranked-choice voting in
November — **lost 69.6% to 30.4%.** That result does not refute this paper; it
illustrates its mechanism. A reform that would enlarge and de-close the electorate
is itself decided *by the existing electorate*, through the very turnout-and-general
structure the reform targets — and the people currently outside the room do not,
from outside it, have the numbers to open the door. The finding here is therefore
less a policy recommendation than the description of a **self-reinforcing
equilibrium**: a closed, gray, one-party primary (contested in only about half of
seats) selects the officials, and the broader electorate that might change the rules
is precisely the one the rules leave least able to.

---

## Related work

This paper documents, with unusually rich individual-level data, mechanisms that
are largely established; its contribution is the measurement and the party-neutral
age result, not the discovery of the mechanisms. It sits in these literatures:

- **The one-party primary as the real election.** V.O. Key, *Southern Politics in
  State and Nation* (1949) — in a one-party polity the dominant party's primary is
  the decisive contest; the general ratifies it. This paper is a modern,
  individual-level instance.
- **Surge-and-decline / turnout composition by salience.** Campbell, "Surge and
  Decline" (1960); Wolfinger & Rosenstone, *Who Votes?* (1980); Leighley & Nagler,
  *Who Votes Now?* (2013). Section I's presidential→midterm falloff is this.
- **Off-cycle / election-timing and representation.** Anzia, *Timing and Turnout*
  (2014); Hajnal & Trounstine (2005); Kogan, Lavertu & Peskowitz (2018, on school
  boards); Einstein et al., "The Gray Vote" (2024) — the closest analog to the age
  result. Motivates the on-cycle remedy.
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

# 4. Electorate extras: unaffiliated bloc, decomposition, cohort trend,
#    safe-seat map, donor-mix x competitiveness (Sections I, III, V, VI, VII)
python scripts/diag_id_electorate_extras.py
```

Source: `data/raw/id/id_statewide_voter_history_20260629.csv` (Idaho SoS
statewide voter file with history, 2026-06-29 export; public record). Party
buckets: REP / DEM / UNAFF (unaffiliated) / OTHER (Libertarian + Constitution).
All headline numbers above are re-derivable by running the scripts in this block.
