# Safe-Seat Washington

### How often is a Washingtonian's legislative or congressional general election an actual contest? (Observed, 2016–2024)

*Companion to ["Who Decides Washington?"](who-decides-washington.md) and the
[electoral-health white paper](electoral-health-whitepaper.md) (Finding 2). Where
the lead paper showed *who* turns out, this one asks whether their vote in the
general is a real choice. Figures from `scripts/diag_safe_seat_wa.py`, computed
from **observed** precinct results (`precinct_results`), not the forecast model.*

---

## The question, and why "observed" matters

The standard "most seats are safe" claim usually rests on a *projection* — a model's
predicted margin. That invites the obvious rebuttal: *your model could be wrong.* So
this paper throws the projection out and counts the **actual** general-election
result of every partisan legislative and congressional seat on Washington's ballot,
2016–2024. The unit is the **seat** (each State Representative position, each State
Senator race up that cycle, each U.S. House race) — the thing a voter actually marks.

Washington's **top-two primary** sharpens the question. Because the two highest
primary finishers advance regardless of party, a general can be (a) **uncontested**
(one candidate), (b) **same-party** — two Democrats or two Republicans, so the
general offers *no major-party choice at all* — or (c) a real **D-vs-R** contest,
which we then band by two-party margin (Tossup <5 / Lean 5–10 / Likely 10–20 /
Solid ≥20). A seat is **non-competitive** if it is uncontested, same-party, or
D-vs-R by ≥10 points.

---

## What the data shows

**Observed competitiveness of partisan legislative + congressional seats, by even-year general:**

| Year | Seats | Uncontested | Same-party | Tossup | Lean | Likely | Solid | **Non-competitive** |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| 2016 | 107 | 20 | 27 | 4 | 6 | 18 | 32 | **90.7%** |
| 2018 | 100 | 8 | 12 | 16 | 9 | 19 | 36 | **75.0%** |
| 2020 | 132 | 14 | 21 | 10 | 11 | 24 | 52 | **84.1%** |
| 2022 | 132 | 23 | 23 | 9 | 8 | 26 | 43 | **87.1%** |
| 2024 | 133 | 23 | 23 | 10 | 10 | 21 | 46 | **85.0%** |

- **Defensible claim.** In a typical Washington cycle, **roughly 85% of legislative
  and congressional seats are decided before November.** In 2024, of 133 partisan
  seats only **20 (15%) were genuine contests** (within 10 points); **113 were
  non-competitive**, and **46 of them — more than a third of all seats — offered
  voters no D-vs-R choice whatsoever** (23 uncontested + 23 same-party top-two
  generals). The pattern is stable across a decade (84–91%), denting **only** in the
  2018 blue-wave year, when competition briefly rose (non-competitive fell to 75%).
  This is a counting result on real ballots — it does not depend on any model.
- **It is not a one-party artifact.** Among 2024's safe seats, **69 lean Democratic
  and 44 lean Republican** — safe seats are a bipartisan feature of the map, the
  expected product of a geographically sorted electorate, not a gerrymander story.
- **But the *ratio* doesn't quite match the vote.** "Not one-party" is a claim about
  *direction*. Whether safe seats split the way the *statewide vote* does is a separate
  question, and they don't quite. Measured against each state's 2024 presidential
  two-party vote (`scripts/diag_safe_seat_party_ratio.py`, lower chamber for cross-state
  comparability), safe seats over-represent whichever party runs the state, and the gap
  widens the more lopsided the state gets: WA's House safe seats are 62.1% Democratic
  against a 59.5% Democratic presidential vote (+2.6 points — and the 69–44 all-seats
  split above is +1.6), essentially a match, which is what geographic sorting rather than
  distortion looks like. But Texas safe seats are 63.8% Republican against 56.9%
  presidential (+6.9), and Idaho's are 87.7% Republican against 68.8% (+18.9). That
  widening gap is a packing signature — the minority party's voters concentrated into a
  few districts, so it wins a smaller share of safe *seats* than of the statewide *vote*.
  Whether that reflects deliberate line-drawing or the minority's own geographic
  clustering is exactly what this cut cannot say — a packing signature is consistent with
  both, and separating them needs a partisan-symmetry or map-simulation test (a separate
  question from this paper's).
- **The model that the cross-state work relies on is validated here.** This project's
  forecast independently bands **53 of 59** WA districts as ≥10-pt safe (**90%**) for
  2026 — within a few points of the **85%** measured on actual 2024 results. The
  projection and the observed record agree.

**The operative contest is the lower-turnout primary.** When the November general is
foregone, the binding decision is the August top-two primary — which drew only
**~51% of the general's voters in 2024** (median across seats; ~62% in 2022). So in a
safe seat the effective choice is made by an electorate roughly **half** the size of
the one that shows up to ratify it in November — and, per the lead paper, an
off-cycle *local* primary electorate is smaller and older still.

---

## The strongest objection (and the honest limit)

- **Lopsided ≠ illegitimate.** A Solid-D Seattle seat and a Solid-R rural seat each
  *represent* their electorate; a 40-point margin can simply mean the voters there
  genuinely agree, which is the healthy null ("outcomes reflect voter choice"), not a
  closed shop. The finding is strongest for the **46 no-choice seats** (uncontested +
  same-party), where the general offered no cross-party option at all — and weakest as
  a "democratic failure" reading for the merely-lopsided Solid seats.
- **The threshold is a knob.** "Non-competitive" is sensitive to the 10-point cutoff;
  the *uncontested + same-party* count (35% of 2024 seats) is threshold-free and is
  the hardest part of the claim to argue with.
- **WA's top-two makes "same-party" a Washington-specific category.** In states with
  party primaries the analogue is "no major-party filer." The four-state table below
  folds both into a single comparable bucket — *no major-party choice* — so the cross-
  state counts are apples-to-apples.

---

## The four-state map — observed

Running the **same observed count** against each state's **lower chamber** — the one
body fully up every cycle in all four states, so the count is complete and
apples-to-apples (upper chambers stagger in WA/TX and are reported separately below;
`scripts/diag_safe_seat_states.py`). Most recent loaded general: WA/TX/ID 2024; NY 2022.

| State (chamber) | Seats | No major-party choice | Competitive (<10pt) | **Non-competitive** | Safe D / R | (model proj.) |
|---|--:|--:|--:|--:|--:|--:|
| WA House | 98 | 39 | 11 | **88.8%** | 54 / 33 | 90% |
| NY Assembly | 149 | 48 | 17 | **88.6%** | 89 / 43 | 86% |
| TX House\* | 150 | 61 | 9 | **94.0%** | 51 / 90 | 81% |
| ID House | 70 | 20 | 5 | **92.9%** | 8 / 57 | 92% |

- **Defensible claim.** Safe-seat dominance is **not a Washington peculiarity** — in
  every one of the four states **89–94% of lower-chamber seats were non-competitive** on
  the actual ballot, blue and red alike, and **a third or more offered no D-vs-R choice at
  all** (WA 39, NY 48, TX 61, ID 20). And the observed counts **track the model's
  independent projection** (NY 88.6 observed vs 86 projected; ID 92.9 vs 92; WA 88.8 vs 90)
  — the projection the cross-state work leans on is validated against real ballots. Safe
  seats favor the locally dominant party (WA/NY lean-D, TX/ID lean-R) — partisan geography,
  symmetric: lopsided seats exist on both sides everywhere.
- **TX is the most foreclosed — and the contest gap is *worse* than the map.** Completed to
  all 150 House seats (see below), **94%** were non-competitive and **61 (41%) had no
  major-party opponent.** Strikingly, that 94% *exceeds* what the district lean predicts:
  the 2024 **presidential** result bands only **84%** of TX House districts as ≥10-pt safe
  (close to the model's 81% projection), yet **94%** of the actual House *races* were
  foregone — Texas parties decline to field candidates even in seats their own presidential
  numbers say are winnable. Observed contestation is worse than the partisan geography alone.
- **\*TX backfill.** The TLC canvass-grade VTD returns omit uncontested races (no precinct
  tally is published when a seat is unopposed), so the warehouse carried only 96/150 TX
  House districts. The 54 absent seats are uncontested by construction — confirmed against
  the press-reported 2024 unopposed list (HD 35/36/38/40/42/49/51/75/78/79/90/92/95 D, 81 R,
  …, all in the missing set) — and are backfilled as *no-major-choice*, with holding party
  assigned by each district's 2024 presidential lean from the on-disk TLC r206 report
  (`scripts/diag_tx_safe_seat_backfill.py`). WA/NY/ID lower-chamber coverage was already
  complete. (This table is lower-chamber only for comparability; WA's all-seats figure
  including congressional + both House positions, and the 2016–2024 trend, are above.)

---

## Robustness

*`scripts/diag_safe_seat_robustness.py`.*

**The threshold doesn't matter.** "Non-competitive" uses a 10-pt margin cut; the headline
is flat across the whole plausible range, because the no-major-choice seats (a third or
more of every chamber) are non-competitive at *any* threshold and only the contested seats
move:

| Lower chamber | ≥5pt | ≥8pt | ≥10pt | ≥12pt | ≥15pt |
|---|--:|--:|--:|--:|--:|
| WA House | 95.9% | 91.8% | 88.8% | 80.6% | 78.6% |
| NY Assembly | 94.6% | 92.6% | 88.6% | 85.9% | 82.6% |
| TX House | 98.0% | 96.0% | 94.0% | 91.3% | 86.0% |
| ID House | 95.7% | 92.9% | 92.9% | 91.4% | 90.0% |

Even at a stringent **15-point** cut, **79–90%** of seats are non-competitive; at a loose
5-point cut, 95–98%. There is no threshold at which these chambers look competitive.

**The contest gap — parties leave winnable seats on the table.** Comparing each chamber's
*actual-race* non-competitive share to the share of its districts that are ≥10-pt safe by
**2024 presidential lean** (the partisan geography), where matched-boundary presidential
results exist:

| | Actual-race non-comp | Presidential-lean safe | Gap |
|---|--:|--:|--:|
| WA House | 88.8% | 79.6% | **+9.2 pp** |
| TX House | 94.0% | 84.0% | **+10.0 pp** |
| ID House | 92.9% | 94.3% | −1.4 pp |

In the two states with genuine partisan diversity (WA, TX), actual contestation is ~10 points
*worse* than the map predicts — parties decline to field candidates even where the
presidential numbers say the seat is winnable. In deep-one-party **Idaho** the gap vanishes
(slightly negative): the districts are so lopsided presidentially that contestation cannot
lag the map. So the "foregone-contest" pathology is **strongest where competition is
actually possible** — which is the more troubling reading. (NY can't be tested here: its
loaded presidential data ends in 2020, pre-2022 redistricting, so it can't be matched to the
2022 Assembly lines.)

---

## Why it matters

The lead paper showed the off-year electorate is half-sized and old. This paper shows
that even in the high-turnout even-year general, **most legislative and congressional
seats are not actually in play** — so the real decision migrates to the **primary**,
a round that draws about half the voters. Stack the two: a large share of Washington's
representation is effectively chosen by **small, old, primary electorates**, with the
November general a ratification. The reforms implied are the familiar pair — **on-cycle
timing** (lead paper) to enlarge and rebalance the deciding electorate, and primary
design (top-four / ranked-choice experiments) to put real choice back into the round
that actually decides.

*This paper makes no partisan-consequence claim: it counts contests and margins, not
who benefits. That question needs individual party-of-record (the follow-on study).*

## Methods and limits

*Full provenance + a no-AI reproduction recipe (every source, access path, and the exact
scripts behind each figure): [Data Sources & Reproducibility](data-sources-and-reproducibility.md).*

- **Source.** `precinct_results` summed per candidate per seat; party from
  `candidates.party_normalized` (D = `%democrat%`, R = `%republican%`/`%gop%`),
  write-ins excluded; district parsed from `race_name`. Two-party margin =
  |D−R|/(D+R) among the major-party vote.
- **Seat universe.** State Representative Pos. 1 & 2 (every cycle), State Senator
  (staggered — only districts up that cycle, so the senate seat set varies by year),
  U.S. Representative. Even-year generals only (WA holds no legislative/congressional
  races in odd years).
- **Primary/general ratio** matches each general seat to its same-office, same-district
  August primary; "turnout" = total votes cast in that seat's race.
- Margins are observed two-party vote share, not the forecast. Third-party/independent
  votes are excluded from the margin but a lone third-party challenger still counts the
  seat as "contested" by headcount only if a major-party opponent is also present.
