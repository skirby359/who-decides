# Corrections and review ledger

### Companion to *Who Gives? The Donor Class and the Registered Electorate*

**Stephen Kirby** · Tikor Consulting · July 2026

The manuscript states its current claims and its live caveats. It does not narrate its own
drafting history, so the record of what changed lives here. **This file is not part of the
submitted manuscript or of its online methods appendix** — a reviewer needs the final methods and
the rationale for withdrawn claims where that rationale is substantive, not every drafting error.
It is kept because a public claim that was withdrawn should stay findable.

Four rounds of external review ran 2026-07-27 to 2026-07-29. The round-by-round detail, including
the defects found by the paper's own verifier, is in
[`electoral-health-audit-log.md`](electoral-health-audit-log.md). The methods themselves are in
[`donor-class-methods-supplement.md`](donor-class-methods-supplement.md).

---

## Claims withdrawn or narrowed under review

The manuscript states its current claims and its live caveats. It does not narrate its own
drafting history, so the record of what changed lives here. Three rounds of external review
ran 2026-07-27 to 2026-07-29; `electoral-health-audit-log.md` rounds 4–7 carry the full detail
including the defects found by the paper's own verifier.

### Claims withdrawn outright

| claim as published | why it fell |
|---|---|
| Cross-state concentration ordering is "a property of these states' donor economies" | Only NY−WA and NY−ID (federal) stay positive across donor resamples; no state-panel pair does |
| "Contribution caps do not explain the cross-state differences" | More than a clipping exercise on an unchanged transaction file can support |
| Idaho shows "single-metro dominance from a state with no large city" | Ada holds 29.3% of the roll, so its 36.8% of federal dollars is 1.26×. The disproportionate county is resort-county Blaine at 7.83× |
| The both-systems group sits "outside the range" in all three states | Fails in Idaho on a common donor-total restriction (48.5 / 66.3 / 63.9) |
| "Republicans fund Democrats at 3.6× the rate Democrats fund Republicans" | Compared two donor-*classification* shares (12.2% against 3.2%) and read as a dollar flow. On the dollar-flow measure the same rows read 18.3% against 4.5%. Neither supports the compact framing |
| Idaho's federal Republican over-representation, +4.2 points | 103.3% of it is age composition: standardized, +4.2 becomes −0.1 |
| Crossover patterns are "stable in both panels and both states" and the unresolved pool "cannot plausibly reverse them" | True of the federal panels, false of the state panels. Every state row but Idaho's registered Democrats fails an extreme bound |
| Itemized-only concentration is an **upper bound** on concentration among all givers | Not a formal bound: adding donors moves the top-1% cutoff as well as the denominator |
| Appendix G's cycle-varying row is "historically exact" | A statutory limit caps a donor's aggregate giving per committee per election; the FEC file pools recipient types with different limits; neither recipient type nor election designation is persisted |
| Appendix G holds the donor population "approximately fixed" | Jaccard 0.14–0.16: the panels are predominantly different people. The design holds the *state* broadly fixed |
| "13.3 points above what pure truncation predicts" | Compared an observed layer against a clipped layer that is not a legally matched counterfactual; the clip level alone moves it four points |
| The $1,000 bunching proves a binding *legislative* cap | $1,000 is the limit for legislative, judicial and local candidates; these rows carry neither recipient type nor election designation |
| Household false merges are "small by construction" | Spouses can differ in first name, so the key does not exclude them. Replaced by a bounding exclusion |
| A "6.6% primary versus 83% general" Idaho rate pair | Current-roll denominators make Idaho rates unreliable, and a rate cannot separate non-participation from election-day affiliation change |
| New York "bars" corporate and LLC contributions, sharing the federal prohibition | § 14-116(2) permits up to $5,000 in the aggregate per calendar year — a limit, not a ban |
| Texas does *not* share the federal corporate prohibition | It does, as a third-degree felony under Tex. Elec. Code § 253.094 — which the same appendix cited two lines above |
| Federal law forbids *PAC* contributions to candidates | It does not; multicandidate committees may give subject to their own per-election limit |
| New York has no ceiling on a donor's total giving | § 14-114(8)'s $150,000 annual aggregate limit is on the books, with enforcement preliminarily enjoined as applied |
| ADGN reports "false negatives under about 1%" | Roughly 2–2.5% discordance in the reported comparison |
| The flat matchability gradient "cannot generate" the age result | It rules out that mechanism only — not donor-side name completeness, mobility, or current-roll survivorship |
| Concentration "does not rest on a handful of top donors" | Resampling shows the estimate remains large; it says nothing about particular extreme donors |

### Figures superseded by the specification change

Adopting the full-first-name match key as the primary specification (2026-07-27) rebuilt every
panel. Superseded totals, retained as `*_alltier` snapshots: WA federal 172,998, WA state
269,204 rows (**268,741** with a positive total — the two differ by 463 and are different
denominators, not a discrepancy); NY federal 307,841, NY state **424,020**; ID federal 27,196,
ID state **27,250**. The pooled WA figure went 382,408 → **314,974**, i.e. *below* the
pre-tier-0 figure of ~320,000, so a count is meaningless without its specification.

Under the all-tier specification, population-weighted precision was **93.0%** and precision
was *lower* in the top dollar decile (63.0% against 72.1% raw). The crossover quartet earlier
reported as 14.2 / 3.9 / 20.2 / 5.5 was all-tier; the primary specification reads
12.2 / 3.2 / 18.3 / 4.5.

Two figures that were arithmetic on a bad basis rather than stale: an Appendix C bullet read
"53 duplicated ids … 378,383 standalone and **424,025** after a roll join", describing a
**45,642**-row expansion that 53 duplicates cannot produce — 424,020 is the retired all-tier
total, and the true join adds **5** rows. And two aggregate resolution rates published as
**87.8%** and **86.7%** were the *Republican row's* rates read off the wrong cell; the panel
aggregates are 88.8% and 87.6%.

### Baselines and estimators that changed

- **Registration baselines** are active registrants (`status_code='A'`), the universe the
  matcher draws from. On an all-records baseline every NY skew moves by at most **0.4** points
  (DEM +15.0, REP −0.9, NOPARTY −13.0) — the figures earlier drafts reported.
- **NY turnout denominators** were all retained records, reading 3.03 vs 1.78 generals and
  73.0% vs 37.1% super-voters; on active registrants they read 3.10 vs 1.85 and 75.7% vs 39.3%.
- **Geography** is reported on counties throughout, normalized by roll share. Earlier drafts
  compared two Seattle ZIP3s against single counties elsewhere.
- **The IPW re-weighted NY senior share (47.9%)** is an all-tier figure and is labelled as
  such wherever it appears.
- **Washington's PDC itemization threshold** is $25 rising to $100 on 1 April 2023 (WSR
  23-07-004), not the "Jan. 8, 2024" date an earlier draft cited — that is a real WAC
  390-05-400 amendment (WSR 24-01-028) but not the one that set this threshold.
- **Washington's two layers** are substantially overlapping, not "aligned": FEC 2017–2026
  against PDC 2016–2026.
- **The estimator** is `NTILE(100)`. An earlier draft using `PERCENT_RANK` drifted from it on
  the heavy ties that capped systems produce; against an exact donor-weight cutoff the top-1%
  figures move −0.001 to −0.046 points, below the printed precision in all six panels.

### Two corrections that landed on new work

Recorded because it is the most transferable lesson in this record. The **common
donor-total restriction** and the **six-panel resampling exercise** were both added *in
response to review*, and both were described more strongly than their designs permitted — the
first as a test of statutory disclosure thresholds, the second as sampling inference. The
coverage audit passed clean on both, because it checks arithmetic and cannot see an
overclaimed interpretation. Separately, **Appendix G's derived tables were added to the
evidence base while the appendix sat outside the audit**, and that is where the next review
found the largest methodological defect — the same thing that had already happened once, with
the crossover tables.

### Corrections carried inline in the paper until 2026-07-29

These three sat in the manuscript itself, narrating its own revision history to a reader who
had no reason to care. Moved here on adversarial re-read; the substance is unchanged.

**The crossover table's two state blocks were on the wrong specification (found 2026-07-27).**
When the panels were rebuilt on the primary full-name key, the two *federal* blocks of Finding
3's crossover table were updated and the two *state* blocks were not — so the table set one
specification beside another and invited exactly the federal-versus-state comparison that a
specification mismatch corrupts. The state rows now sum to the published panels (NY 378,383;
ID 23,613) rather than the retired all-tier totals (424,020; 27,250). No conclusion changed:
Democratic loyalty and the unaffiliated Democratic tilt both held, and the Idaho unaffiliated
lean strengthened from roughly 3:1 to nearly 4:1.

**The aggregate resolution rates were read off the wrong cell.** The source note under the
crossover tables gave 87.8% and 86.7% as the NY-federal and ID-federal *panel aggregate*
resolution rates. Both are the **Republican row's** rate. The aggregates are 88.8% and 87.6%.

**"That reading is now the paper's."** Finding 3's age-standardization passage announced its
own change of position on Idaho's Republican over-representation (+4.2 raw becoming −0.1
standardized). The withdrawal is recorded above under claims withdrawn outright; the paper now
simply states the standardized result and the instruction not to cite the raw figure.

---

### Withdrawn or narrowed in round 17 (2026-08-01)

Five formulations that outran their evidence, all introduced by the *previous* round's own
robustness work — which is the pattern the reviewer named: a correction that generates new theory
generates new overclaims with it.

**"The observed failure mode is structurally unavailable on this key."** Too strong. The
uniqueness guard drops a colliding key only when both people appear distinctly on the **current
active roll**. It does not reach a same-name relative who is inactive, has moved, or is absent
from the roll; a jointly reported gift; a misreported name; or a namesake who never registered.
The paper's own evidence contains the counter-example — one partial merge on the primary key in
the 120 rated records, and a jointly filed gift needs no name difference at all. Now stated as
elimination of the observed mechanism *within that boundary*.

**"Whatever residual remains therefore cannot be that mechanism."** Does not follow. A same-name
relative absent from the active roll is still a household mechanism; it is simply one the guard
cannot detect. Narrowed to: the residual is not necessarily a different mechanism, only one the
guard cannot see, and what it cannot be is a merge between two people both distinctly on the roll.

**"Donors almost certainly on the roll."** A key matching two or more registrants is ambiguous; it
does not establish that the contributor is one of them. Now "keys plausibly corresponding to a
registrant but dropped because the roll holds more than one candidate."

**"Only one of them is the rule's doing."** Contradicted by the paper's own residual table four
paragraphs below it. Full-name exactness, ZIP5 exactness, the active-status restriction and the
name parse all produce non-matches; the uniqueness guard is one of four, not the only one.

**"The real floor on what a name-and-ZIP key can reach."** Not a floor. That residual still
contains out-of-state records, name forms the limited relaxation misses, parse failures,
incomplete roll records, identities split across keys, and people a probabilistic linkage would
recover. Now "the residual not resolved by the specific deterministic relaxations tested here."

**One factual claim corrected rather than narrowed.** "In every panel the biggest bucket after
matching is a key at a different ZIP5" was false in the displayed Washington state row (26.0%
against 30.9%) and in Idaho's. The decomposition is now computed on resident keys — which is also
what puts it on the same denominator as the table immediately above it — and the prose says "the
largest identified nonmatch category in **most** panels", naming the two exceptions.

### Superseded measurements, round 17

**The Washington PDC name-order estimates are withdrawn.** The retired values, recorded here
because the paper no longer restates them: **1.85% of comma-less rows / 2.08% of dollars** from
the originating script's own parser, and **4.7% of rows / 4.1% of dollars** from a
surname-vocabulary heuristic. They disagreed with each other, the
first was labelled in the paper as the one figure the verification pass could not independently
confirm, and neither was the quantity that matters. Replaced by a direct measurement — rebuild the
primary key both ways against the active roll — which puts the defect at **7.6% of comma-less
resident keys and 8.4% of their dollars**, against a **0.18%** coincidence baseline measured on
the comma-formatted FEC layer where the true name order is known.

The measurement also settles the direction, which neither estimate addressed: the donors the
defect loses are *older* than those matched (44.0% aged 65+ against 39.0%), so a repaired parser
would move that panel's 65+ share from 39.0% to 39.8%. The defect understates Finding 1 in the
Washington state panel rather than producing it. The panel is labelled coverage-compromised and
read as a sensitivity panel; the parser is not repaired for this paper, because accepting reversed
keys would add 42,787 matches from a population the blinded validation never rated.

## Deleted 2026-08-03 — `ny-donor-class-by-party.md` (party-resolved NY donor analysis, 2026-06-29)

Superseded 2026-07-27 and carried a "do not cite its numbers" banner from that date; deleted
2026-08-03 once its retraction had been recorded here, because a retracted file left in place is
a standing tripwire for anyone who finds it by search rather than by link.

**What it claimed, and why none of it survives.** A pooled New York match of **308,032** voters
to **6,311,939** contributions, with party and age tables built on it. The match was in fact
FEC-money-only — it predated `scripts/load_ny_contributions.py`, so no NYSBOE state contribution
ever entered it — and the match specification separately changed to the full-first-name key
alone. Either change alone invalidates the counts; both together invalidate every derived table.

**Superseding analysis.** `donor-class-and-the-electorate.md` Finding 3 reports New York as two
separate panels on the current specification — federal **269,218** donors, state **378,383** —
with the party skew measured against an ACTIVE-registrant baseline (federal DEM **+16.1**,
NOPARTY **−13.7**). The corrected pooled count is **558,017**. Current figures for every panel
are in `reference/primary_spec_figures_2026-07-27.md`.

**References repointed** the same day in `electoral-health-TODO.md`, `ny-electorate-extras.md`,
`ny-turnout-by-party-age.md` and `who-decides-new-york.md`. The retired figures may still appear
in this ledger and in `electoral-health-audit-log.md`; recording a withdrawn number is what those
files are for.
