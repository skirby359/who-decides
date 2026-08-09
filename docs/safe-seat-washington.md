# Safe-Seat Washington

### Two questions, measured separately: was the general election close, and did it offer a choice between the parties? (Observed, 2016–2024)

**Stephen Kirby** · Tikor Consulting · July 2026

*AI-assisted drafting and analysis review. All figures are reproducible from
public-record data and from the open-source scripts cited below, including
`scripts/diag_seat_competition.py`, which builds the seat universe from certified
statewide returns and fails loudly if any cycle does not reconcile to the statutory
chamber size. The paper source, code, and data-acquisition recipe are public at
<https://github.com/skirby359/who-decides>. Contact: kirby@tikorconsulting.com.*

***DRAFT — pending human/editorial sign-off.** `scripts/verify_safe_seat.py` scrapes this paper
and asserts its figures against the data, with the exceptions the script names in its own output; that gate is automated and is not the sign-off.
The sign-off is a person reading the paper end to end, recorded in
[`safe-seat-submission-notes.md`](safe-seat-submission-notes.md) §Sign-off.*

*Companion to ["Who Decides Washington State?"](who-decides-washington.md) and the
[electoral-health white paper](electoral-health-whitepaper.md) (Finding 2). Where the
lead paper showed *who* turns out, this one asks what their ballot actually offered.*

> **Revision note (2026-07-27).** This paper was substantially rebuilt after an
> adversarial review. Three defects were confirmed and corrected: the seat universe was
> incomplete for 2016 and 2018 (King County was absent from the statewide precinct files,
> costing 24 House seats per year); the "same-party" category was misclassified (the rule
> captured *any* race lacking a D-vs-R pairing, including D-vs-independent); and two
> distinct questions — whether a race was close, and whether it offered a partisan choice
> — were collapsed into one number. Headline figures have changed and Appendix G records
> the before/after. The claim that seats were "decided before November" has been
> withdrawn as unsupported by this design.

> **Revision note (2026-07-28).** A second internal pass, this one auditing the paper
> against its own scripts rather than its argument, corrected five figures and closed one
> reproducibility gap. The 2020 partisan-availability share moves 27.6% → **26.9%** (a
> misspelled party string in the certified file had made a real Democrat-versus-Republican
> race read as no-choice); the 2020 primary/general median moves 61.6% → **61.5%**; New
> York's ≥12-point cell moves 85.2% → **85.9%**; and Appendix E's exploratory seat/vote gaps
> move to **WA +2.1 / TX +3.3**, the Texas figure having been computed on the same imputed
> party split Appendix F retires. The five-cycle primary/general table now has a derivation
> in `diag_seat_competition.py` instead of resting on an unrecorded computation. No headline
> figure changed. Appendix G records the detail.

## Abstract

Claims that most legislative seats are "safe" usually rest on a projected margin, which
invites the rebuttal that the model is wrong. This paper discards the projection and
counts observed general-election results for every partisan legislative and congressional
seat on Washington's ballot from 2016 through 2024, then repeats the count in three
comparison states. It measures two things separately, because they are different
questions. **Candidate competition** asks whether the race was close, using the margin
between the top two candidates regardless of party. **Partisan availability** asks whether
the ballot offered both a Democrat and a Republican. Washington's top-two primary makes
the distinction unavoidable: a general election can be a genuine contest between two
Democrats, and it can also present a single unopposed candidate. In 2024, 111 of 133 seats
(83.5%) were not close — decided by ten points or more, or uncontested — and 46 (34.6%)
offered no Democratic-versus-Republican option. The two overlap but are not the same: of
sixteen same-party generals, fifteen were also lopsided, but one was decided by six
points. Across five cycles the not-close share runs 79–88% and the no-major-choice share
25–49%. The pattern is not confined to Washington: in the lower chambers of three
comparison states, 88–94% of seats were not close. Safe seats are bipartisan, splitting 68
Democratic to 43 Republican in Washington in 2024. The results are insensitive to the
competitiveness threshold, holding between 74% and 98% across cuts from 15 points to 5.
The paper counts contests and margins; it does not establish when the binding choice
occurred, and makes no claim about which party benefits.

**Keywords:** electoral competition; safe seats; uncontested elections; top-two primary;
state legislatures; primary elections; Washington; New York; Texas; Idaho.

---

## The question, and why "observed" matters

The standard "most seats are safe" claim usually rests on a *projection* — a model's
predicted margin. That invites the obvious rebuttal: *your model could be wrong.* So this
paper throws the projection out and counts the **actual** general-election result of every
partisan legislative and congressional seat on Washington's ballot, 2016–2024. The unit is
the **seat** — each State Representative position, each State Senator race up that cycle,
each U.S. House race — the thing a voter actually marks.

Washington's **top-two primary** forces a distinction that most safe-seat work can elide.
Because the two highest primary finishers advance regardless of party, a general election
can be:

- **a single candidate**, with no opponent at all;
- **two candidates of the same party**, offering a real choice between people but none
  between parties;
- **a Democrat against a Republican**, the conventional case;
- **a major-party candidate against a minor-party or independent one.**

A 51–49 general between two Democrats is a contest. It is also a ballot with no
cross-party option. Collapsing those facts into a single "non-competitive" number answers
neither question well, so this paper reports two dimensions throughout:

| dimension | question | measure |
|---|---|---|
| **Candidate competition** | Was it close? | margin between the top two candidates, any party |
| **Partisan availability** | Was there a D-vs-R choice? | which parties appeared on the ballot |

---

## The seat universe

Because an earlier version of this analysis under-counted, the universe is now built from
the **certified statewide summary returns** and asserted against the statutory chamber
size before anything is computed. Washington elects all 98 House positions and 10 U.S.
House members every even year; the Senate is staggered.

| year | House (want 98) | Senate | U.S. House (want 10) | total |
|---|--:|--:|--:|--:|
| 2016 | 98 | 26 | 10 | 134 |
| 2018 | 98 | 25 | 10 | 133 |
| 2020 | 98 | 26 | 10 | 134 |
| 2022 | 98 | 25 | 10 | 133 |
| 2024 | 98 | 25 | 10 | 133 |

`scripts/diag_seat_competition.py` exits non-zero if any cycle fails this reconciliation.
The prior approach derived races from the precinct-results table, where a race absent from
the data simply disappeared rather than being detected as missing; Appendix G documents
what that cost.

**Precisely what is and is not independently asserted.** The House and U.S. House counts are
checked against **fixed statutory expectations** — 98 and 10 — that do not come from the file
being checked, so a missing race fails the run. The **Senate count does not have that
property.** Washington's Senate is staggered and its per-cycle expectation depends on which
seats were up plus any special elections, so the diagnostic takes the expected number *from the
certified file itself* and reports it rather than asserting it against an outside figure. A
Senate race missing from a certified file would therefore lower both the expectation and the
count together, and reconcile. This is a real gap in the guarantee and it is stated rather than
glossed, because an under-counted universe is the exact defect that forced this paper's rebuild.
Closing it means enumerating the seats up in each cycle from an independent source; that is not
done here, and until it is, the reconciliation claim above should be read as covering the House
and U.S. House.

---

## Dimension 1 — was the race close?

Margin between the top two candidates, regardless of party. "Not close" means a single
candidate, or a margin of ten points or more.

| year | seats | single candidate | Tossup <5 | Lean 5–10 | Likely 10–20 | Solid 20+ | **not close** |
|---|--:|--:|--:|--:|--:|--:|--:|
| 2016 | 134 | 27 | 8 | 8 | 32 | 59 | **88.1%** |
| 2018 | 133 | 15 | 19 | 9 | 24 | 66 | **78.9%** |
| 2020 | 134 | 14 | 11 | 11 | 28 | 70 | **83.6%** |
| 2022 | 133 | 24 | 10 | 8 | 31 | 60 | **86.5%** |
| 2024 | 133 | 23 | 10 | 12 | 23 | 65 | **83.5%** |

- **Defensible claim.** In a typical Washington cycle **roughly five in six legislative
  and congressional seats are not close**. In 2024, of 133 partisan seats only **22 (16.5%)
  were decided by under ten points**. The share runs 79–88% across a decade, with **2018
  the least foreclosed year** — the blue-wave cycle, when 19 seats landed inside five
  points, more than double any other year in the series.
- **Safe seats are bipartisan.** Among 2024's not-close seats, **68 were won by Democrats
  and 43 by Republicans** — the expected product of a geographically sorted electorate.
  (Winner party is taken from the leading candidate, not inferred from aggregate party
  vote totals; Appendix G explains why that distinction mattered.)

---

## Dimension 2 — did the ballot offer a partisan choice?

| year | seats | D-v-R | D-v-D | R-v-R | D-v-other | R-v-other | single | **no D-v-R** |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| 2016 | 134 | 69 | 4 | 5 | 15 | 14 | 27 | **48.5%** |
| 2018 | 133 | 98 | 6 | 0 | 13 | 1 | 15 | **26.3%** |
| 2020 | 134 | 100 | 8 | 1 | 7 | 4 | 14 | **25.4%** |
| 2022 | 133 | 86 | 10 | 6 | 2 | 5 | 24 | **35.3%** |
| 2024 | 133 | 87 | 8 | 8 | 5 | 2 | 23 | **34.6%** |

- **Defensible claim.** In 2024, **46 of 133 Washington races — more than a third of the
  partisan ballot — offered no Democratic-versus-Republican option**: 23 had a single
  candidate, 16 pitted two candidates of the same party against each other, and 7 set a
  major-party candidate against a minor-party or independent one. This count is
  **threshold-free**: no margin cutoff enters it.
- **The single-candidate count is the hardest number in the paper.** Twenty-three seats in
  2024 presented voters with exactly one name. That is not a judgment about competitiveness;
  it is a headcount. Both implementations exclude candidates with zero recorded votes, so
  "one candidate" and "one name on the ballot" are the same proposition only if no
  ballot-listed, non-write-in candidate drew zero votes. **There are none, in any of the five
  cycles** — the verifier measures it and prints `zero-vote ballot candidates = 0`, and fails
  if that ever stops being true.
- 2016 is the outlier at 48.5%, and partly for a definitional reason — **eight** distinct
  non-major party strings appeared on that year's ballot, six of them Independent-flavoured
  ("Indep't Democrat", "Independent Dem", "Independent Dem.", "Independent GOP",
  "Independent", "Independent Rep") plus **two** hybrids naming two parties at once
  ("GOP/Independent" and "Dem/Working Fmly"). An earlier version of this sentence said seven
  and listed only the first hybrid. See the sensitivity test below.

### The two dimensions are not the same question

Cross-tabulating them for 2024 shows where they agree and where they part:

| | single | Tossup <5 | Lean 5–10 | Likely 10–20 | Solid 20+ |
|---|--:|--:|--:|--:|--:|
| D-v-R | 0 | 10 | 11 | 20 | 46 |
| D-v-D | 0 | 0 | 0 | 1 | 7 |
| R-v-R | 0 | 0 | 1 | 2 | 5 |
| D-v-other | 0 | 0 | 0 | 0 | 5 |
| R-v-other | 0 | 0 | 0 | 0 | 2 |
| single candidate | 23 | 0 | 0 | 0 | 0 |

Most same-party generals are also lopsided — 15 of 16 in 2024 exceeded ten points, and 12
exceeded twenty. But **one was a genuine contest**: Washington's 4th Congressional
District, an R-vs-R general decided by **6.0 points** (Dan Newhouse). Treating that race as
"non-competitive" because it lacked a Democrat would be wrong. It is a competitive election
without a partisan choice, and the two-dimension design is what makes it visible.

### Sensitivity: how party preference is read

Washington's top-two system has no nominees, only stated preferences. The published figures
count a string as major when it carries a variant of the party's own name and is not qualified
by independence — so "MAGA Republican" and "Culture Republican" are major, while
"Independent Dem.", "Ind. Republican" and the two-party hybrids "GOP/Independent" and
"Dem/Working Fmly" are counted as other. Folding those remaining strings into the major
parties moves the no-D-v-R share by:

| year | strict (published) | loose | delta |
|---|--:|--:|--:|
| 2016 | 48.5% | 38.1% | 10.4 |
| 2018 | 26.3% | 24.8% | 1.5 |
| 2020 | 25.4% | 23.9% | 1.5 |
| 2022 | 35.3% | 35.3% | 0.0 |
| 2024 | 34.6% | 34.6% | 0.0 |

The rule matters in 2016 and is close to immaterial elsewhere. Both specifications are now
**enumerated string by string** in `docs/reference/wa_party_strings_2016-2024.csv` rather than
expressed as regexes, and the only judgment the test still varies is whether
independence-qualified strings and two-party hybrids fold into a major party. That is why the
2024 delta is 0.0: the faction-qualified strings that used to separate the two specifications
("MAGA Republican", "Culture Republican") are major under both. Deltas are computed on
unrounded shares, so they need not equal the difference of the two printed columns
(2016: 48.5075 − 38.0597 = 10.4478).

Spelling and abbreviation are handled as data, not judgment. The 2020 certified file records
the Democratic candidate in Legislative District 8, Position 1 as preferring the
"Democractic" party — a misspelling, not a distinct preference. Read literally it made a
genuine Democrat-versus-Republican general (Klippert 51,981, Regev 26,979) classify as
Republican-versus-other, and correcting it alone moved the 2020 no-D-v-R share from 27.6% to
26.9%. Such corrections apply in **both** the strict and the loose specification, because the
sensitivity test is only informative if it varies the interpretive rule while holding the
transcription constant. Hybrids like 2016's "GOP/Independent" are real stated preferences and
are left in the *other* bucket, where the loose column prices them.

**That single correction is no longer the whole story, and the reason is worth stating.** A
2026-08-08 audit enumerated every distinct party string in all five certified files — 32 of
them — instead of trusting a regex to match the ones anybody had thought of. It found five
further strings naming a major party that were being counted as minor: `G.O.P.` (2018),
`G.O.P` without the trailing period (2016), `R` twice (2020), `MAGA Republican` (2024) and
`Culture Republican` (2024). Six races were misclassified across four cycles. Correcting them
moves 2018 to **26.3%**, 2020 to **25.4%** and 2024 to **34.6%**, and widens the five-cycle
range to 25–49%. **Dimension 1 is untouched** — margins do not depend on party — so the
headline 111 of 133 stands unchanged.

The defect was never any one pattern; it was that a regex cannot report what it failed to
match. Classification is therefore no longer a regex at all. Both specifications are
enumerated string by string in `docs/reference/wa_party_strings_2016-2024.csv`, each row
carrying its reason, and a string absent from that file is a hard error rather than a silent
"other". The rule the enumeration encodes: a string names a major party iff it carries a
variant of that party's own name and is not qualified by independence. Faction qualifiers do
not disqualify; independence qualifiers and two-party hybrids do. The independence exclusion
is what keeps the classification symmetric — a rule reading any string containing
"Republican" as Republican, while leaving "Independent Dem." as other, would flip nine
Republican-flavoured races and no Democratic ones.

---

## The four-state comparison

The same count against each state's **lower chamber** — the one body fully up every cycle
everywhere, so the comparison is like-for-like. Completeness is reported explicitly
rather than assumed.

| state (chamber) | loaded / expected | not close | no D-v-R |
|---|---|--:|--:|
| WA House 2024 | 98 / 98 | **87.8%** | 39.8% (39) |
| NY Assembly 2022 | 150 / 150 | **88.0%** | 32.0% (48) |
| TX House 2024 | 96 canvass + 54 certified single-candidate | **94.0%** | 40.7% (61) |
| ID House 2024 | 70 / 70 | **92.9%** | 28.6% (20) |

- **Defensible claim.** Foreclosure is **not a Washington peculiarity** — in every state
  examined, **88–94% of lower-chamber seats were not close**, blue and red alike, and
  **more than a quarter offered no D-vs-R option.**
- **New York is now complete, and the one absent seat turned out to be the chamber's
  closest.** The Assembly has 150 districts and the loaded returns carry 149; a check confirms
  the missing one is exactly Assembly District 23 and nothing else. Earlier drafts bounded the
  effect rather than resolving it, reporting 149 of 150 seats and a range wide enough to cover
  either outcome for the absent one. That was
  unnecessary: the seat is not unknowable. The New York State Board of Elections publishes the
  certified contest, and AD-23 was decided by **fifteen votes** — Stacey G. Pheffer Amato
  **16,185** to Thomas P. Sullivan **16,170**, a margin of 0.046 points and the narrowest race
  in the chamber. Supplying it makes the denominator the real 150, and the chamber reads
  **88.0%** not close with **32.0%** offering no D-vs-R option. Figures and provenance are
  pinned in `docs/reference/ny_ad23_2022.csv`; the totals are candidate totals across all
  ballot lines, which is not the same as the Democratic and Republican lines alone.
- **Texas is 64% loaded in the canvass returns**, and its figures depend on a backfill of
  the 54 uncontested seats that source omits. That backfill is now **verified seat by seat
  against the Secretary of State's certified results**, which independently show exactly
  those 54 districts as single-candidate, and supply the observed winning party for each
  (Appendix F). Its not-close seats split **56 D / 85 R**.
- **The comparison states are scored by a shortcut, and it was checked rather than
  assumed.** Washington's "not close" comes from the top-two margin, so a *contested*
  same-party general under ten points counts as close — the WA-04 case above. The
  comparison-state code takes any seat with no D-vs-R option as not close whatever its
  margin, which would inflate their figures if such a seat were ever competitive.
  Re-scoring every no-major-choice seat in the three states on its top-two margin finds
  **none under ten points** — 0 of 48 in New York, 0 of 61 in Texas, 0 of 20 in Idaho — so
  the three percentages are identical under either rule and the comparison is like-for-like
  in fact and not merely in intent. This is a measured result, not a property of the
  definitions, and `diag_safe_seat_robustness.py` re-measures it on every run.
- Most recent loaded general: WA/TX/ID 2024, NY 2022.

---

## Why it matters

The lead paper showed the off-year electorate is half-sized and older than the
presidential one. This paper shows that even in the high-turnout even-year general, most
legislative and congressional seats are not close, and a third of the ballot offers no
choice between the parties.

Where a general election is not close, attention naturally turns to the August top-two
primary as the round where the outcome is effectively determined. **The primary is much
the smaller round.** Matching every seat to its own August primary on the corrected
universe, the median primary race drew this share of the votes cast in the same seat's
general:

| 2016 | 2018 | 2020 | 2022 | 2024 |
|--:|--:|--:|--:|--:|
| 42.1% | 55.9% | 61.5% | 61.2% | **51.2%** |

Read this as a ratio of **votes cast in a contest**, not of distinct voters: roll-off and
undervoting mean a race's vote total is not a headcount of participants. So in 2024 the
median legislative or congressional primary recorded about half as many votes as the
November contest for the same seat.

That the primary is smaller does not establish that it is where the decision was made.
Observed November margins can show a race was not close; they cannot show *when* the
binding choice occurred, or that a primary presented a meaningful alternative.
Establishing that would require tracing each seat through its primary — whether it was
contested, whether the eventual winner faced a credible same-party rival, and whether the
general's finalists were themselves closely matched. That is the obvious sequel and is not
attempted here.

What the evidence does support is narrower and still substantial: **a large share of
Washington's legislative general elections ended with margins of ten points or more, and for
roughly a third of seats the ballot offered no choice between the two major parties.** The
earlier wording here said those seats were "settled in November by margins wide enough that
the result was not in doubt" — which smuggles an *ex ante* claim about expectations back into
an *ex post* measure. A race that was genuinely uncertain in September can finish 60–40; the
margin records how it ended, not what was in doubt. Whether alternative primary or general-election
structures — top-four, ranked choice — would increase candidate competition or cross-party
choice is a question these findings motivate, not one they answer.

---

## What this paper does not claim, and limits

- **It does not establish that seats were "decided before November."** That inference
  appeared in an earlier version and has been withdrawn. Observed general-election margins
  cannot date the binding decision.
- **"Not close" is not "illegitimate."** A forty-point margin can mean the voters there
  genuinely agree. The finding is strongest for the 23 single-candidate seats and the 15
  same-party generals, and weakest as a democratic-deficit reading for lopsided D-vs-R
  contests. Appendix A takes this at full strength.
- **The partisan analysis is descriptive.** Safe-seat party totals and the seat/vote
  comparison in Appendix E describe patterns; they do not establish causation, intent, or
  gerrymandering. An earlier version claimed to make "no partisan-consequence claim" while
  analysing exactly that — the contradiction is resolved by scoping the claim rather than
  denying the analysis.
- **The Texas backfill is verified and its party split is now observed.** Earlier versions
  imputed holding party from presidential lean, which proved wrong in 5 of 54 seats. Party
  now comes from certified returns, and the split is 56 D / 85 R rather than the previously
  reported 51 D / 90 R. Appendix F documents the correction.
- **New York is a cycle behind** (2022). It is no longer missing Assembly District 23: that
  seat is supplied from the certified NYSBOE contest, so the chamber is complete at 150 and
  the former 88.0–88.7% bound is retired.
- **Margins are between candidates, not parties**, in Dimension 1. Third-party votes count
  toward the margin when a minor-party candidate is one of the top two, and are excluded
  from the denominator otherwise — which can only arise in the comparison states, since a
  Washington general carries exactly two candidates.
- **Primary participation is measured in race votes, not voters** — see Appendix C.

---

# Appendices

## Appendix A — The objections, in full

**1. Not-close seats still represent their voters.** A Solid-D Seattle seat and a Solid-R
rural seat each *represent* the electorate that produced them; a wide margin can be
agreement rather than foreclosure. This is the strongest objection and it is substantially
correct for lopsided D-vs-R contests. It has far less force against the 23 seats that
offered one name: no degree of voter agreement explains the absence of an alternative to
agree or disagree with. The two-dimension design exists so that these cases are counted
separately instead of averaged together.

**2. The ten-point threshold is a knob.** True, and Appendix E tests the whole plausible
range: the not-close share moves between 74% and 98% across cuts from 15 points to 5, and
never approaches "competitive" at any setting. Dimension 2 is threshold-free entirely.

**3. Same-party generals are a Washington artifact of top-two.** In states with party
primaries the analogue is a seat with no major-party filer, and the four-state table folds
both into one comparable bucket. But the deeper version of this objection — that a
same-party general may be a real contest — is correct, was mishandled in the earlier
version, and is now measured directly. One of Washington's sixteen same-party generals in
2024 was decided by six points.

**4. The safe-seat split proves a gerrymander.** It does not, and the paper declines the
claim. Washington's not-close seats split 68 D to 43 R — 61.3% Democratic — against a 59.5%
Democratic share of the two-party presidential vote, a gap of 1.8 points, close to
proportionate. Chen & Rodden (2013) is the standing
demonstration that residential geography produces seat/vote bias with nobody drawing it,
and single-member districts have no proportionality expectation to begin with. Appendix E
reports the comparison descriptively and draws no inference about intent.

**5. The Texas number rests on rows you added.** It did, and the objection prompted a
proper check. The backfilled 54 have since been verified one by one against the Secretary
of State's certified results, which independently identify exactly those districts as
single-candidate and supply each winner's party. The headline was unchanged by the check
(94.0% either way); the party split was not, and has been corrected. Appendix F sets out
both. Excluding Texas entirely would still not change the paper's conclusion; it would
remove the most extreme case.

**6. Your earlier numbers were wrong.** Also correct. Appendix G documents what changed and
why, rather than quietly restating.

## Appendix B — Data access and provenance

- **What the figures are computed from.** Certified statewide general-election summary
  returns, one row per candidate per race, carrying race name, candidate, party preference
  and vote total. These are **published aggregate election results** — this paper touches
  no voter file and no personal data, and carries no privacy surface.
- **Washington.** Secretary of State certified statewide summaries, files
  `20161108_AllState.csv`, `20181106_AllState.csv`, `20201103_AllState.csv`,
  `20221108_AllState.csv`, `20241105_AllState.csv`. These are the authoritative source for
  the seat universe. The corresponding `_AllStatePrecincts.csv` files are **not** used for
  the universe, because King County is largely absent from them in 2016 and 2018 — the
  defect Appendix G describes.
- **New York.** State Board of Elections returns as ingested into the project warehouse.
  *Provenance note: the repository's loader path for New York results involves an
  intermediary; the exact ingested artifact and its transformation commit should be cited
  alongside the originating authority before publication.*
- **Idaho.** Secretary of State certified returns.
- **Texas.** Two sources, because one is insufficient. The Legislative Council's
  canvass-grade VTD returns supply precinct-level results but **omit uncontested races at
  every stage**, carrying 96 of 150 House districts. The **Texas Secretary of State's
  election-night results service** (`results.texas-election.com`, read 2026-07-27)
  publishes all 150 including uncontested ones with candidate, party and votes; it is the
  seat universe and the source of holding party, captured to
  `data/raw/tx/2024_tx_house_candidates.csv`. The TLC r206 report
  (`planh2316_r206_election24g.xls`) is retained only for district presidential lean in
  Appendix E.
- **Outstanding for publication.** Full dataset citations — release date, access date,
  archived location, checksum, and loader commit — are not yet assembled for every source
  and should be before circulation.

## Appendix C — Methods

- **Universe.** Built from certified statewide summary returns and asserted against the
  statutory chamber size (98 WA House positions, 10 U.S. House, Senate staggered).
  `scripts/diag_seat_competition.py` exits non-zero on any mismatch. Write-ins are excluded;
  candidates with zero votes are excluded.
- **Party.** Taken from the certified "Prefers ___ Party" string. Only
  Democratic/Democrat and Republican/GOP count as major; Independent-, GOP/Independent-,
  Culture- and MAGA-prefixed strings are counted as other, with a sensitivity test reported
  in the body. Outright misspellings of a major party's own name are normalized first, in
  both specifications — one such string exists, "Democractic" in 2020, and the body explains
  it. Because top-two has no nominees, this is a statement about stated preference, not
  nomination.
- **"Safe seat"** is used throughout as shorthand for *a seat that was not close in the
  observed result*. It carries no forward-looking claim; nothing here projects a future
  margin, which is the point of the design.
- **Dimension 1, candidate competition.** Margin between the top two candidates by votes,
  regardless of party: |first − second| / (first + second). Bands: Tossup <5, Lean 5–10,
  Likely 10–20, Solid 20+. "Not close" = single candidate or margin ≥10. In Washington the
  general has exactly two candidates, so this is the whole field; in the comparison states,
  where three or more can appear, votes for candidates below second place are outside the
  denominator and margins are correspondingly slightly wider.
- **Dimension 2, partisan availability.** Classified from the set of parties actually on
  the ballot: D-v-R, D-v-D, R-v-R, D-v-other, R-v-other, other-only, single candidate.
- **Winner party** is the party of the leading candidate. An earlier version inferred it by
  comparing aggregate D and R vote totals, which mislabels a race where both are zero;
  Appendix G records the fix.
- **Primary participation.** Each general seat is matched to its same-office,
  same-district August primary, and the reported figure is the **median ratio of primary
  race votes to general race votes** — a comparison of votes cast in a contest, *not* of
  distinct voters. Roll-off and undervoting affect race totals, so the two are not
  interchangeable. Recomputed on the corrected universe by
  `scripts/diag_seat_competition.py`, which reports the matched-seat count alongside each
  median and fails the run if any seat is unmatched (all five cycles match completely):
  42.1 / 55.9 / 61.5 / 61.2 / 51.2% for 2016–2024. The 2024 and 2022 figures are within a
  point of the previously published ~51% and ~62%, so the correction to the seat universe
  did not move this measure.
- **Reproduction.** `scripts/diag_seat_competition.py` builds the classification and writes
  `reports/seat_competition.csv` (one row per seat, both dimensions). Supporting scripts:
  `diag_safe_seat_states.py` (four-state), `diag_tx_safe_seat_backfill.py` (Appendix F),
  `diag_safe_seat_robustness.py` (Appendix E), `diag_safe_seat_party_ratio.py` and
  `diag_efficiency_gap.py` (Appendix E's exploratory cuts).
- **Where the scripts disagree with each other, and why.** Two of the supporting scripts
  predate the universe rebuild and still print their old Washington cell:
  `diag_safe_seat_states.py` reads the precinct table under the retired conflated definition
  and reports WA House at 88.8%. Every Washington figure in this paper comes from
  `diag_seat_competition.py` on the certified universe (87.8%), which is authoritative; the
  superseded cells are labelled as such in those scripts' own output rather than removed, so
  the earlier published numbers remain reproducible for audit. `diag_safe_seat_party_ratio.py`
  was corrected in place, since the paper quotes it directly.

## Appendix D — Related work

- **The primary as the real election under one-party dominance.** V. O. Key Jr., with the
  assistance of Alexander Heard, *Southern Politics in State and Nation* (New York: Alfred
  A. Knopf, 1949). Hirano & Snyder, *Primary Elections in the United States* (Cambridge
  University Press, 2019), doi:10.1017/9781139946537.
- **The decline of competition in general elections.** Abramowitz, Alexander & Gunning,
  "Incumbency, Redistricting, and the Decline of Competition in U.S. House Elections,"
  *Journal of Politics* 68(1) (2006): 75–88, doi:10.1111/j.1468-2508.2006.00371.x.
- **Uncontested seats as their own phenomenon.** Squire, "Uncontested Seats in State
  Legislative Elections," *Legislative Studies Quarterly* 25(1) (2000): 131–146. Burden &
  Snyder, "Explaining Uncontested Seats in Congress and State Legislatures," *American
  Politics Research* 49(3) (2021): 247–258, doi:10.1177/1532673X20960565 — on why parties
  decline to field candidates, the mechanism behind Appendix E's contest gap.
- **Political geography versus intentional gerrymandering.** Chen & Rodden, "Unintentional
  Gerrymandering: Political Geography and Electoral Bias in Legislatures," *Quarterly
  Journal of Political Science* 8(3) (2013): 239–269 — residential concentration produces
  seat/vote bias without deliberate line-drawing. Stephanopoulos & McGhee, "Partisan
  Gerrymandering and the Efficiency Gap," *University of Chicago Law Review* 82 (2015):
  831–900 — the source of the efficiency-gap measure and of the benchmark Appendix E
  reports against.
- **Off-cycle timing and who is left deciding.** Anzia, *Timing and Turnout: How Off-Cycle
  Elections Favor Organized Groups* (University of Chicago Press, 2014).
- **Top-two and primary reform.** McGhee & Shor, "Has the Top Two Primary Elected More
  Moderates?" *Perspectives on Politics* 15(4) (2017): 1053–1066,
  doi:10.1017/S1537592717002158 — addresses candidate *moderation* under top-two, with
  mixed and jurisdiction-dependent findings; it is cited here for institutional context and
  does not speak directly to whether top-two restores general-election competition.
- **Safe-seat prevalence, advocacy literature.** FairVote's *Monopoly Politics* series
  reports projected House competitiveness. *A specific edition, year, report title and
  archived location must be supplied before publication; the series is cited here as
  background only.*

## Appendix E — Robustness, and exploratory cuts

**Threshold sensitivity.** The not-close share across margin cutoffs. The Washington rows
come from `scripts/diag_seat_competition.py` on the corrected universe, using the same
code path as the headline, so the ≥10 column reproduces Dimension 1 exactly; the other
chambers come from `scripts/diag_safe_seat_robustness.py`.

| scope | ≥5pt | ≥8pt | ≥10pt | ≥12pt | ≥15pt | seats |
|---|--:|--:|--:|--:|--:|--:|
| WA all seats | 92.5% | 88.0% | **83.5%** | 77.4% | 73.7% | 133 |
| WA House | 95.9% | 91.8% | **87.8%** | 80.6% | 76.5% | 98 |
| NY Assembly | 94.0% | 92.0% | 88.0% | 85.3% | 82.0% | 150 |
| TX House | 98.0% | 96.0% | 94.0% | 91.3% | 86.0% | 150 |
| ID House | 95.7% | 92.9% | 92.9% | 91.4% | 90.0% | 70 |

Even at a stringent 15-point cut, **74–90%** of seats are not close; at a loose 5-point
cut, 93–98%. There is no threshold at which these chambers look competitive.

Both New York rows — this sweep and the four-state table above — are now on the complete
150-seat chamber, and their ≥10-point cells agree at **88.0%**. `diag_safe_seat_robustness.py`
reads the same pinned AD-23 file as the verifier rather than carrying its own copy, so the two
code paths cannot drift to different denominators; each also refuses to run if the gap it is
closing is ever not exactly one seat.

**The contest gap.** Comparing each chamber's actual not-close share with the share of its
districts that are ≥10-point safe by 2024 presidential lean. The Washington figure uses
the corrected House number:

| | actual | presidential-lean safe | gap |
|---|--:|--:|--:|
| WA House | 87.8% | 79.6% | **+8.2 pp** |
| TX House | 94.0% | 84.0% | **+10.0 pp** |
| ID House | 92.9% | 94.3% | −1.4 pp |

In the two states with genuine partisan diversity, legislative contests are substantially less
competitive than presidential lean alone would predict — about ten points less — while in
deep-one-party Idaho the gap vanishes. (New York cannot be tested: its loaded presidential data
predates the 2022 Assembly lines.)

**What this comparison does not identify.** An earlier version of this passage read the gap as
candidate non-entry — "parties decline to field candidates where the presidential numbers say a
seat is winnable" — and that is more than the statistic supports. The gap compares two
aggregate shares; it does not observe who filed. A district can carry both major parties on the
ballot and still finish twenty points apart for reasons that have nothing to do with entry:
incumbency, candidate quality, spending, differential turnout, or simple office-specific voting
by people who split their ticket. Non-entry is *one* mechanism consistent with the gap, and the
uncontested-seat literature (Squire 2000; Burden & Snyder 2021) establishes that it operates
somewhere — but it does not establish that it produces *this* +8.2 and +10.0. Decomposing the
gap by whether the district was single-candidate, lacked one major party, or ran both parties
to a wide margin would test it directly, on data already loaded. That is the sequel, and it is
not attempted here.

**Exploratory: seat/vote ratio and partisan symmetry.** *This section is descriptive and
should be read as a prompt for further work rather than a finding.* Measured against each
state's 2024 presidential two-party vote, not-close seats over-represent the locally
dominant party, and the gap widens with the state's lopsidedness: Washington **+2.1**
points, Texas **+3.3**, Idaho **+18.9**. Two basis notes, because the same comparison has
been stated two ways. These are **lower-chamber** figures, so Washington is its House (53
D / 33 R of 86 not-close seats = 61.6% D against a 59.5% Democratic presidential share); on
the all-seats universe Appendix A quotes, the split is 68 D / 43 R = 61.3% D, a **+1.8**
gap. Texas's holding party is the **observed** party from certified returns, not the
retired presidential-lean imputation — that imputation gave 51 D / 90 R and a +6.9 gap, and
was additionally circular, since it derived party *from* presidential lean and then
compared it *against* presidential lean. That pattern is **consistent with** packing, and
equally consistent with residential geography, district-boundary effects, turnout
differences, and the definition of "safe" used here; single-member districts carry no
proportionality expectation, and this comparison examines only safe seats rather than the
whole distribution. It cannot distinguish those mechanisms or establish a counterfactual
seat distribution. New York is omitted from the series: its only loaded presidential vote
is 2020, against 2022 Assembly lines. Under the efficiency-gap specifications reported by
`scripts/diag_efficiency_gap.py`, no state exceeds the ~8-point level Stephanopoulos &
McGhee (2015) discuss (the largest is Texas at 6.5% on the wasted-vote form). Those values
are computed from **district-level presidential two-party vote**, as a measure of asymmetry
in the map, rather than from each chamber's own legislative returns as in the original
specification; the script computes more than one formulation and the values differ (Texas
is 6.5% wasted-vote against 0.1% simple), the metric is sensitive to turnout distribution,
New York's row again crosses a redistricting, and none of this determines whether a map is
an outlier against neutral ensembles or was drawn with intent. Establishing that requires
map-simulation work this paper does not attempt.

**Exploratory: comparison with the project's forecast.** This project's forecast bands 53
of 59 Washington districts (90%) as ≥10-point safe for 2026, against 83.5% of seats
measured as not-close on 2024 results. These are **different units, different years, and
different denominators** — districts versus seats — so the similarity is a loose
aggregate consistency check, **not a validation**. A real validation would predict
historical elections without using their outcomes and report classification accuracy,
calibration, and false-safe rates on the same unit.

## Appendix F — The Texas backfill

Texas is the one state where this paper adds rows rather than only counting them.

**The problem.** The Texas Legislative Council's canvass-grade VTD returns omit uncontested
races: when a seat is unopposed no precinct tally is published. The warehouse therefore
carried **96 of 150** TX House districts, and the missing 54 were missing *because* they
were uncontested — exactly the category this paper counts. Left alone, the omission biases
Texas toward looking more competitive than it is.

**The original construction, now retired.** The 54 absent districts were backfilled as *no
major-party choice*, with holding party assigned from each district's 2024 presidential lean
using the on-disk TLC r206 report (`planh2316_r206_election24g.xls`). Script:
`scripts/diag_tx_safe_seat_backfill.py`. The results database was not mutated. The
uncontested classification from that step survives verification below; the imputed party
does not, and no figure in this paper now depends on it.

**Verified against a certified source.** The backfill was checked seat by seat against the
Texas Secretary of State's election-night results service, which publishes every race
including uncontested ones with candidate name, party and votes
(`scripts/build_tx_house_candidates.py` → `data/raw/tx/2024_tx_house_candidates.csv`;
audit in `scripts/diag_tx_backfill_verification.py` →
`reports/tx_backfill_verification.csv`).

**The match is exact.** The certified source shows **54 single-candidate districts**, and
they are precisely the 54 the TLC returns omit — no district was backfilled that was
actually contested, and no uncontested district was missed. The backfill is confirmed in
full, not merely for a named subset. As an external check on the extraction, the certified
data also puts the 2024 chamber at 62 D / 88 R, matching the seated Texas House.

**Why the TLC data could never have settled this.** It omits uncontested races at *every*
stage, not just the general: all 14 districts on the press-reported unopposed list appear
in **neither** 2024 party primary, because those candidates were unopposed there too.
Absence is a property of the whole dataset, so no amount of work inside it could
distinguish "uncontested" from "missing".

**Holding party is now observed, and the old imputation was wrong.** Party for the 54 comes
from the certified returns rather than presidential lean. Retrospectively, the retired
imputation was **wrong in 5 of 54** — HD 35, 36, 40, 42 and 144, every one a district Trump
carried while a Democrat held the seat, mostly Rio Grande Valley. The observed split of
the backfilled seats is **36 D / 18 R**, against 31 D / 23 R imputed. Correcting it moves
the chamber's not-close split from the previously reported 51 D / 90 R to **56 D / 85 R**.

**The headline was unaffected throughout.** Not-close remains **141 of 150 = 94.0%** on
certified data, identical to the backfilled figure, because that count needs only the
seats to have been uncontested — which is exactly what the certified source confirms.
Without the backfill, on the 96 contested-skewed districts, Texas would read 90.6% and
just 7.3% without a D-vs-R option, visibly biased toward competitiveness.

## Appendix G — What changed in this revision, and why

An adversarial review of the prior version identified three defects. All were confirmed
against the code and data, and all are corrected here.

**1. The seat universe was incomplete.** The prior analysis derived races from the
precinct-results table. King County is essentially absent from Washington's statewide
*precinct* files for 2016 and 2018 — about 190 of 330,845 rows in 2016 — so every King
legislative race silently vanished: 24 House seats per year, districts 5, 11, 33, 34, 36,
37, 41, 43, 45, 46, 47 and 48. The warehouse held 74 of 98 House seats in both years. A
separate format variant (2020 LD15 spelled "Representative, Position N" rather than "State
Representative Pos. N") dropped two more. The certified summary files carry every race and
were already on disk, so the fix required no new data — only building the universe from a
certified race list and asserting it against the statutory chamber size.

**2. "Same-party" was misclassified.** The rule was `same_party if (d == 0 or r == 0)`,
which captures *any* race lacking a D-vs-R pairing — including D-vs-independent and
R-vs-Libertarian. Of the 23 races the prior version labelled same-party in 2024, **seven
were not same-party at all.** Relatedly, winner party was inferred by comparing aggregate D
and R totals, so a race with neither would have been scored Democratic; no such race
occurred in 2024, but the rule was wrong and is now taken from the leading candidate.

**3. Two questions were collapsed into one.** Every same-party general was scored
non-competitive regardless of margin. That is a statement about partisan availability
presented as a statement about competitiveness.

**Effect on the headline figures:**

| year | prior "non-competitive" | corrected "not close" | change |
|---|--:|--:|--:|
| 2016 | 90.7% | 88.1% | −2.6 |
| 2018 | **75.0%** | **78.9%** | **+3.9** |
| 2020 | 84.1% | 83.6% | −0.5 |
| 2022 | 87.1% | 86.5% | −0.6 |
| 2024 | **85.0%** | **83.5%** | **−1.5** |

The most consequential change is 2018. The prior version reported a dramatic dip to 75% in
the blue-wave year; on the complete universe the dip is to **78.9%** — still the least
foreclosed cycle in the series, but a good part of the apparent drop was 24 missing King
County seats, which are disproportionately safe and Democratic. The headline moves from
"roughly 85%" to **"roughly 84%"**, and the decade range tightens from 75–91% to 79–88%.

The 2024 no-major-choice count moves from 46 to **47**, and is now correctly described:
23 single-candidate, 15 same-party, 9 major-versus-minor.

**Also withdrawn:** the claim that seats were "decided before November," which observed
November margins cannot establish; and the assertion that the safe-seat ratio is a
"packing signature," now reported as a descriptive comparison consistent with several
mechanisms.

### The second pass, 2026-07-28

The rebuild above fixed the argument. A later pass audited every printed figure against the
script that claims to produce it — a different exercise, and it found five numbers that no
longer matched their own derivation, plus one table that had none.

**1. A misspelled party string made a real two-party race read as no-choice.** The 2020
certified file records Legislative District 8's Position 1 Democrat as preferring the
"Democractic" party. The strict rule matches "Democratic" and "Democrat", so the string fell
through to *other* and a Klippert-versus-Regev general — 51,981 to 26,979, a Republican
against a Democrat — was classified Republican-versus-other. The 2020 no-D-v-R share moves
**27.6% → 26.9%**, D-v-R from 97 to 98, R-v-other from 5 to 4, and the loose-rule delta from
2.2 to 1.5. Dimension 1 is untouched: the seat was a 31.7-point blowout either way. The fix
is applied in both specifications, because a transcription error is not the kind of thing a
strict-versus-loose sensitivity test is meant to be sensitive to.

**2. The primary/general table had no derivation.** The five-cycle series was reported as
"recomputed on the corrected universe," but the recomputation lived in no script:
`diag_seat_competition.py` had no primary logic at all, and the only script that computed the
ratio was the superseded pre-rebuild one, which covered two cycles on the old universe. The
computation is now part of `diag_seat_competition.py`, which also reports how many seats
matched and fails the run if any did not. Four of the five cycles reproduce the published
figures exactly; 2020 comes out **61.5%** rather than 61.6%.

**3. Appendix E carried two stale exploratory gaps.** Washington's +2.6 came from the retired
88.8% universe; on the certified one it is **+2.1** (House basis) or **+1.8** (all seats),
and the paper now states which basis each figure uses, because Appendix A quotes the
all-seats split against the same presidential share. Texas's +6.9 was computed on the 51 D /
90 R imputation that Appendix F retires as wrong in 5 of 54 seats; on observed party it is
**+3.3**. The ordering the section describes — the gap widening with a state's lopsidedness —
survives both corrections.

**4. New York's ≥12-point cell was mistranscribed**, 85.2% for 85.9% (127 seats for 128).

**5. The comparison states are scored by a shortcut that had not been checked.** Their code
treats any seat lacking a D-vs-R option as not close regardless of margin — the conflation
defect #3 removes for Washington. Re-scoring all 129 such seats on their top-two margin finds
**none under ten points**, so every comparison-state percentage is identical under either
rule. The check now runs as part of `diag_safe_seat_robustness.py` rather than being assumed,
and the four-state section states the result.

Nothing in the abstract changed. The 2016–2024 not-close series, the 2024 headline of 111 of
133 seats, the 47-seat no-choice count, the cross-tab, and Appendix F's Texas verification
all reproduce unchanged.

## End note — data, reproduction, and series

```
# The rebuilt classification — universe assertion, both dimensions, sensitivity,
# and the primary/general medians. Every Washington figure in the paper comes from here.
python scripts/diag_seat_competition.py        # writes reports/seat_competition.csv

# Four-state lower-chamber count and the Texas completion:
python scripts/diag_safe_seat_states.py        # NB: its WA cell (88.8%) and TX safe split
                                               # (51/90) are SUPERSEDED and labelled so in
                                               # its output; see Appendix C
python scripts/diag_tx_safe_seat_backfill.py       # Appendix F backfill
python scripts/build_tx_house_candidates.py        # certified TX candidate list (all 150)
python scripts/diag_tx_backfill_verification.py    # Appendix F seat-by-seat verification
                                                   # -> reports/tx_backfill_verification.csv

# Robustness and the exploratory cuts:
python scripts/diag_safe_seat_robustness.py    # Appendix E thresholds + contest gap
python scripts/diag_safe_seat_party_ratio.py   # seat/vote ratio
python scripts/diag_efficiency_gap.py          # partisan-symmetry diagnostic
```

All inputs are published election returns. See
[`data-sources-and-reproducibility.md`](data-sources-and-reproducibility.md) for the source
ledger and [`electoral-health-audit-log.md`](electoral-health-audit-log.md) for the verification
ledger of expected values.

Companion to the electoral-health series lead,
[`who-decides-washington.md`](who-decides-washington.md), with
[`who-decides-new-york.md`](who-decides-new-york.md) and
[`who-decides-idaho.md`](who-decides-idaho.md) (party-resolved electorates),
[`donor-class-and-the-electorate.md`](donor-class-and-the-electorate.md) (who funds them),
[`cross-state-fec-money.md`](cross-state-fec-money.md) (the four-state money layer), and
[`does-money-move-votes.md`](does-money-move-votes.md) (whether that money moves margins).
