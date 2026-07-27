# Safe-Seat Washington

### Two questions, measured separately: was the general election close, and did it offer a choice between the parties? (Observed, 2016–2024)

**Stephen Kirby** · Tikor Consulting · July 2026

*AI-assisted drafting and analysis review. All figures are reproducible from
public-record data and from the open-source scripts cited below, including
`scripts/diag_seat_competition.py`, which builds the seat universe from certified
statewide returns and fails loudly if any cycle does not reconcile to the statutory
chamber size. The paper source, code, and data-acquisition recipe are public at
<https://github.com/skirby359/who-decides>. Contact: kirby@tikorconsulting.com.*

*Companion to ["Who Decides Washington State?"](who-decides-washington.md) and the
[electoral-health white paper](electoral-health-whitepaper.md) (Finding 2). Where the
lead paper showed *who* turns out, this one asks what their ballot actually offered.*
**DRAFT — pending the independent-verification gate in
[`publication-checklist.md`](publication-checklist.md).**

> **Revision note (2026-07-27).** This paper was substantially rebuilt after an
> adversarial review. Three defects were confirmed and corrected: the seat universe was
> incomplete for 2016 and 2018 (King County was absent from the statewide precinct files,
> costing 24 House seats per year); the "same-party" category was misclassified (the rule
> captured *any* race lacking a D-vs-R pairing, including D-vs-independent); and two
> distinct questions — whether a race was close, and whether it offered a partisan choice
> — were collapsed into one number. Headline figures have changed and Appendix G records
> the before/after. The claim that seats were "decided before November" has been
> withdrawn as unsupported by this design.

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
(83.5%) were not close — decided by ten points or more, or uncontested — and 47 (35.3%)
offered no Democratic-versus-Republican option. The two overlap but are not the same: of
fifteen same-party generals, fourteen were also lopsided, but one was decided by six
points. Across five cycles the not-close share runs 79–88% and the no-major-choice share
27–49%. The pattern is not confined to Washington: in the lower chambers of three
comparison states, 89–94% of seats were not close. Safe seats are bipartisan, splitting 68
Democratic to 43 Republican in Washington in 2024. The results are insensitive to the
competitiveness threshold, holding between 79% and 98% across cuts from 5 to 15 points.
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
| 2018 | 133 | 97 | 6 | 0 | 14 | 1 | 15 | **27.1%** |
| 2020 | 134 | 97 | 8 | 1 | 9 | 5 | 14 | **27.6%** |
| 2022 | 133 | 86 | 10 | 6 | 2 | 5 | 24 | **35.3%** |
| 2024 | 133 | 86 | 8 | 7 | 6 | 3 | 23 | **35.3%** |

- **Defensible claim.** In 2024, **47 of 133 Washington races — more than a third of the
  partisan ballot — offered no Democratic-versus-Republican option**: 23 had a single
  candidate, 15 pitted two candidates of the same party against each other, and 9 set a
  major-party candidate against a minor-party or independent one. This count is
  **threshold-free**: no margin cutoff enters it.
- **The single-candidate count is the hardest number in the paper.** Twenty-three seats in
  2024 presented voters with exactly one name. That is not a judgment about competitiveness;
  it is a headcount.
- 2016 is the outlier at 48.5%, and partly for a definitional reason — six different
  Independent-flavoured party-preference strings appeared that year. See the sensitivity
  test below.

### The two dimensions are not the same question

Cross-tabulating them for 2024 shows where they agree and where they part:

| | single | Tossup <5 | Lean 5–10 | Likely 10–20 | Solid 20+ |
|---|--:|--:|--:|--:|--:|
| D-v-R | 0 | 10 | 11 | 20 | 45 |
| D-v-D | 0 | 0 | 0 | 1 | 7 |
| R-v-R | 0 | 0 | 1 | 2 | 4 |
| D-v-other | 0 | 0 | 0 | 0 | 6 |
| R-v-other | 0 | 0 | 0 | 0 | 3 |
| single candidate | 23 | 0 | 0 | 0 | 0 |

Most same-party generals are also lopsided — 14 of 15 in 2024 exceeded ten points, and 11
exceeded twenty. But **one was a genuine contest**: Washington's 4th Congressional
District, an R-vs-R general decided by **6.0 points** (Dan Newhouse). Treating that race as
"non-competitive" because it lacked a Democrat would be wrong. It is a competitive election
without a partisan choice, and the two-dimension design is what makes it visible.

### Sensitivity: how party preference is read

Washington's top-two system has no nominees, only stated preferences. The published figures
count only "Prefers Democratic/Democrat Party" and "Prefers Republican/GOP Party" as major;
"Independent Dem.", "Ind. Republican", "Culture Republican" and "MAGA Republican" are
counted as other. Folding those into the major parties moves the no-D-v-R share by:

| year | strict (published) | loose | delta |
|---|--:|--:|--:|
| 2016 | 48.5% | 45.5% | 3.0 |
| 2018 | 27.1% | 25.6% | 1.5 |
| 2020 | 27.6% | 25.4% | 2.2 |
| 2022 | 35.3% | 35.3% | 0.0 |
| 2024 | 35.3% | 34.6% | 0.8 |

The rule matters in 2016 and is close to immaterial elsewhere.

---

## The four-state comparison

The same count against each state's **lower chamber** — the one body fully up every cycle
everywhere, so the comparison is like-for-like. Completeness is reported explicitly
rather than assumed.

| state (chamber) | loaded / expected | not close | no D-v-R |
|---|---|--:|--:|
| WA House 2024 | 98 / 98 | **87.8%** | 39.8% (39) |
| NY Assembly 2022 | 149 / 150 | **88.6%** | 32.2% (48) |
| TX House 2024 | 96 / 150 + 54 backfilled | **94.0%** | 40.7% (61) |
| ID House 2024 | 70 / 70 | **92.9%** | 28.6% (20) |

- **Defensible claim.** Foreclosure is **not a Washington peculiarity** — in every state
  examined, **88–94% of lower-chamber seats were not close**, blue and red alike, and
  **more than a quarter offered no D-vs-R option.**
- **New York is one seat short.** The Assembly has 150 districts and 149 are loaded; the
  missing district has not been identified and its classification is unknown. At this
  chamber size it cannot move the percentage by more than a point, but "complete" would be
  the wrong word and is not used.
- **Texas is 64% loaded before backfill,** and its figures depend on that backfill
  (Appendix F). The Texas party split is **imputed, not observed** — see below.
- Most recent loaded general: WA/TX/ID 2024, NY 2022.

---

## Why it matters

The lead paper showed the off-year electorate is half-sized and older than the
presidential one. This paper shows that even in the high-turnout even-year general, most
legislative and congressional seats are not close, and a third of the ballot offers no
choice between the parties.

Where a general election is not close, attention naturally turns to the August top-two
primary as the round where the outcome is effectively determined. This paper does not
establish that. Observed November margins can show that a race was not close; they cannot
by themselves show *when* the binding choice was made, or that a primary presented a
meaningful alternative. Establishing that would require tracing each seat through its
primary — whether it was contested, whether the eventual winner faced a credible
same-party rival, and whether the general's finalists were themselves closely matched.
That is the obvious sequel and is not attempted here.

What the evidence does support is narrower and still substantial: **a large share of
Washington's legislative representation is settled in November by margins wide enough that
the result was not in doubt, and for a third of seats without the voter ever being offered
a choice between the two major parties.** Whether alternative primary or general-election
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
- **The Texas party split is imputed.** Holding party for the 54 backfilled seats comes
  from presidential lean, so those D/R counts are not observed, and any comparison between
  them and presidential vote is partly circular. Appendix F says so.
- **New York is a cycle behind** (2022) and one seat short of its chamber.
- **Margins are between candidates, not parties**, in Dimension 1. Third-party votes count
  toward the margin when a minor-party candidate is one of the top two.
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
range: the not-close share moves between 79% and 98% across cuts from 15 points to 5, and
never approaches "competitive" at any setting. Dimension 2 is threshold-free entirely.

**3. Same-party generals are a Washington artifact of top-two.** In states with party
primaries the analogue is a seat with no major-party filer, and the four-state table folds
both into one comparable bucket. But the deeper version of this objection — that a
same-party general may be a real contest — is correct, was mishandled in the earlier
version, and is now measured directly. One of Washington's fifteen same-party generals in
2024 was decided by six points.

**4. The safe-seat split proves a gerrymander.** It does not, and the paper declines the
claim. Washington's not-close seats split 68 D to 43 R against a 59.5% Democratic
presidential vote — close to proportionate. Chen & Rodden (2013) is the standing
demonstration that residential geography produces seat/vote bias with nobody drawing it,
and single-member districts have no proportionality expectation to begin with. Appendix E
reports the comparison descriptively and draws no inference about intent.

**5. The Texas number rests on rows you added.** Correct, and Appendix F sets out the
construction, its verification, and its limits. Excluding Texas entirely would not change
the paper's conclusion; it would remove the most extreme case.

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
- **Idaho.** Secretary of State certified returns. **Texas.** Legislative Council
  canvass-grade VTD returns, plus the on-disk TLC r206 report
  (`planh2316_r206_election24g.xls`) used for the Appendix F backfill.
- **Outstanding for publication.** Full dataset citations — file name, release date, access
  date, archived location, checksum, and loader commit — are not yet assembled for every
  source and should be before circulation.

## Appendix C — Methods

- **Universe.** Built from certified statewide summary returns and asserted against the
  statutory chamber size (98 WA House positions, 10 U.S. House, Senate staggered).
  `scripts/diag_seat_competition.py` exits non-zero on any mismatch. Write-ins are excluded;
  candidates with zero votes are excluded.
- **Party.** Taken from the certified "Prefers ___ Party" string. Only
  Democratic/Democrat and Republican/GOP count as major; Independent-, Culture- and
  MAGA-prefixed strings are counted as other, with a sensitivity test reported in the body.
  Because top-two has no nominees, this is a statement about stated preference, not
  nomination.
- **Dimension 1, candidate competition.** Margin between the top two candidates by votes,
  regardless of party: |first − second| / (first + second). Bands: Tossup <5, Lean 5–10,
  Likely 10–20, Solid 20+. "Not close" = single candidate or margin ≥10.
- **Dimension 2, partisan availability.** Classified from the set of parties actually on
  the ballot: D-v-R, D-v-D, R-v-R, D-v-other, R-v-other, other-only, single candidate.
- **Winner party** is the party of the leading candidate. An earlier version inferred it by
  comparing aggregate D and R vote totals, which mislabels a race where both are zero;
  Appendix G records the fix.
- **Primary participation.** Each general seat is matched to its same-office,
  same-district August primary, and the reported figure is the **median ratio of primary
  race votes to general race votes** — a comparison of votes cast in a contest, *not* of
  distinct voters. Roll-off and undervoting affect race totals, so the two are not
  interchangeable. **This figure has not yet been recomputed on the corrected seat
  universe and is therefore not quoted as a headline in this revision.**
- **Reproduction.** `scripts/diag_seat_competition.py` builds the classification and writes
  `reports/seat_competition.csv` (one row per seat, both dimensions). Supporting scripts:
  `diag_safe_seat_states.py` (four-state), `diag_tx_safe_seat_backfill.py` (Appendix F),
  `diag_safe_seat_robustness.py` (Appendix E), `diag_safe_seat_party_ratio.py` and
  `diag_efficiency_gap.py` (Appendix E's exploratory cuts).

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

**Threshold sensitivity.** The not-close share across margin cutoffs
(`scripts/diag_safe_seat_robustness.py`, lower chambers):

| lower chamber | ≥5pt | ≥8pt | ≥10pt | ≥12pt | ≥15pt |
|---|--:|--:|--:|--:|--:|
| WA House | 95.9% | 91.8% | 88.8% | 80.6% | 78.6% |
| NY Assembly | 94.6% | 92.6% | 88.6% | 85.9% | 82.6% |
| TX House | 98.0% | 96.0% | 94.0% | 91.3% | 86.0% |
| ID House | 95.7% | 92.9% | 92.9% | 91.4% | 90.0% |

There is no threshold at which these chambers look competitive. *(These figures were
computed on the prior classification and are being recomputed on the corrected universe;
the WA row will shift by roughly a point.)*

**The contest gap.** Comparing each chamber's actual not-close share with the share of its
districts that are ≥10-point safe by 2024 presidential lean:

| | actual | presidential-lean safe | gap |
|---|--:|--:|--:|
| WA House | 88.8% | 79.6% | **+9.2 pp** |
| TX House | 94.0% | 84.0% | **+10.0 pp** |
| ID House | 92.9% | 94.3% | −1.4 pp |

In the two states with genuine partisan diversity, actual contestation runs about ten
points worse than the map predicts — parties decline to field candidates where the
presidential numbers say a seat is winnable — while in deep-one-party Idaho the gap
vanishes. The pathology is strongest where competition is possible. (New York cannot be
tested: its loaded presidential data predates the 2022 Assembly lines.)

**Exploratory: seat/vote ratio and partisan symmetry.** *This section is descriptive and
should be read as a prompt for further work rather than a finding.* Measured against each
state's 2024 presidential two-party vote, not-close seats over-represent the locally
dominant party, and the gap widens with the state's lopsidedness: Washington +2.6 points,
Texas +6.9, Idaho +18.9. That pattern is **consistent with** packing, and equally
consistent with residential geography, district-boundary effects, turnout differences, and
the definition of "safe" used here; single-member districts carry no proportionality
expectation, and this comparison examines only safe seats rather than the whole
distribution. It cannot distinguish those mechanisms or establish a counterfactual seat
distribution. Under the efficiency-gap specifications reported by
`scripts/diag_efficiency_gap.py`, no state exceeds the ~8-point level Stephanopoulos &
McGhee (2015) discuss; the script computes more than one formulation and the values differ,
the metric is sensitive to turnout distribution, and none of this determines whether a map
is an outlier against neutral ensembles or was drawn with intent. Establishing that
requires map-simulation work this paper does not attempt.

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

**The construction.** The 54 absent districts are backfilled as *no major-party choice*,
with holding party assigned from each district's 2024 presidential lean using the on-disk
TLC r206 report (`planh2316_r206_election24g.xls`). Script:
`scripts/diag_tx_safe_seat_backfill.py`. The results database was not mutated.

**Two limits, stated plainly.**

1. **Verification is partial.** The missing set was cross-checked against press-reported
   2024 unopposed races — HD 35, 36, 38, 40, 42, 49, 51, 75, 78, 79, 90, 92, 95 (D) and 81
   (R) among others — and each falls in the absent set. That demonstrates *some* of the 54
   were uncontested; it does not verify all 54 individually. A district-level table giving
   certified candidates, party, and source for each of the 54 is required before
   publication, along with a specific citation for the press-reported list.
2. **The party split is imputed and partly circular.** Holding party comes from presidential
   lean, so the Texas D/R counts are **imputed, not observed** — and any comparison between
   those counts and presidential vote (Appendix E) uses presidential lean on both sides.
   Party should be taken from certified candidate or incumbent records before the Texas
   seat/vote figure is relied on.

**What it changes.** With the backfill Texas reads 150 seats, 94.0% not close, 61 with no
major-party opponent. Without it, on the 96 contested-skewed districts, Texas reads 90.6%
and just 7.3% without a D-vs-R option — visibly biased toward competitiveness. Readers who
reject the backfill should read the four-state table as three states plus a lower bound.

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

## End note — data, reproduction, and series

```
# The rebuilt classification — universe assertion + both dimensions + sensitivity:
python scripts/diag_seat_competition.py        # writes reports/seat_competition.csv

# Four-state lower-chamber count and the Texas completion:
python scripts/diag_safe_seat_states.py
python scripts/diag_tx_safe_seat_backfill.py   # Appendix F

# Robustness and the exploratory cuts:
python scripts/diag_safe_seat_robustness.py    # Appendix E thresholds + contest gap
python scripts/diag_safe_seat_party_ratio.py   # seat/vote ratio
python scripts/diag_efficiency_gap.py          # partisan-symmetry diagnostic
```

All inputs are published election returns. See
[`data-sources-and-reproducibility.md`](data-sources-and-reproducibility.md) for the source
ledger and [`publication-checklist.md`](publication-checklist.md) for the verification
ledger of expected values.

Companion to the electoral-health series lead,
[`who-decides-washington.md`](who-decides-washington.md), with
[`who-decides-new-york.md`](who-decides-new-york.md) and
[`who-decides-idaho.md`](who-decides-idaho.md) (party-resolved electorates),
[`donor-class-and-the-electorate.md`](donor-class-and-the-electorate.md) (who funds them),
[`cross-state-fec-money.md`](cross-state-fec-money.md) (the four-state money layer), and
[`does-money-move-votes.md`](does-money-move-votes.md) (whether that money moves margins).
