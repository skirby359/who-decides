# Audit log — electoral-health series

*Assembled 2026-06-29 as a publication checklist; now a historical record. The work is
AI-assisted; **you must independently re-derive the headline numbers before posting
under your name** — this file makes that fast, it does not substitute for it.*

> **⚠ Read the hierarchy here as historical.** This file opened by naming
> [`who-decides-washington.md`](who-decides-washington.md) as the lead paper for submission,
> and entries written before 2026-07-29 assume that. **The lead paper is now the donor-class
> article**, *Who Gives? The Donor Class and the Registered Electorate in Washington, New York,
> and Idaho* ([`donor-class-and-the-electorate.md`](donor-class-and-the-electorate.md)). Older
> entries are preserved unedited because they are the record of how the analysis got here, but
> **their ordering does not govern current release decisions** — the binary gates are in
> [`donor-class-release-checklist.md`](donor-class-release-checklist.md) and the live
> submission state is in
> [`donor-class-submission-memo.md`](donor-class-submission-memo.md).

## Series index — what each paper is for

| paper | role | question it answers |
|---|---|---|
| [`donor-class-and-the-electorate.md`](donor-class-and-the-electorate.md) | **Lead article.** Journal submission in preparation | Who funds campaigns, measured person-by-person against the registered electorate in three states |
| [`who-decides-washington.md`](who-decides-washington.md) | Companion | Composition of Washington's off-year electorate |
| [`who-decides-new-york.md`](who-decides-new-york.md) | Companion | New York's registration, party and primary electorate structure |
| [`who-decides-idaho.md`](who-decides-idaho.md) | Companion | Idaho's closed-primary electorate, the deep-red pole |
| [`safe-seat-washington.md`](safe-seat-washington.md) | Companion | Seat competitiveness and where uncontested outcomes concentrate |
| [`cross-state-fec-money.md`](cross-state-fec-money.md) | Companion | Interstate money flows and aggregate concentration, four states |
| [`electoral-health-whitepaper.md`](electoral-health-whitepaper.md) | Synthesis | The series-level "stress, not failure" argument |

Each companion cites the lead article for the donor-linkage instrument rather than restating
it, and the lead article summarizes rather than reproduces their analyses.

---

## 0. The freeze rule — series-wide, in force 2026-08-10

**Read this before adding anything to any paper in the series.** It governs all eight, not one.
Everything below §1 is a record of work done; this section is a constraint on work still to do.

### Why, measured

A freeze rule was put in force on 2026-08-01 for the donor article alone, after reviewer #6's
verdict — *"not cycling yet, but very close."* The nine days that followed ran roughly twenty
further open-ended adversarial rounds across the other seven papers, and **three consecutive
rounds' sharpest finding was against the previous round's own fix**. Each says so in its own
commit body:

| commit | its own summary of itself |
|---|---|
| `69ae5af` | "the most important finding is against yesterday's work in this same session" |
| `e3938bd` | "again the sharpest finding is against the previous round's own work" |
| `1eeb978` | "third consecutive round whose sharpest finding is against a previous round's fix, and this is the worst of them" |

That is cycling, and the rule that would have caught it existed and covered one paper.

The mechanism is not model drift — every one of those rounds ran on the same model. It is that
**both sides of every check are written in the same round by the same author.** When a
derivation and a sentence disagree, the round decides which is wrong, with no prior authority to
appeal to. So the paper tracks the newest derivation, and the next round's newest derivation
moves it back. The clean instance: `df91534` changed Idaho's May-2024 R−D from **+76.8 to +76.9**;
`5a7992b` changed it **back**, because one round rounded from the printed column and the other
from unrounded shares. Neither was wrong on its own basis. **The basis was never declared.**

### The rules

1. **Only cut, relocate, clarify, and prepare for submission.** Admit a new analysis only if it
   (a) could reverse a headline conclusion, (b) answers an actual editor or referee, (c) closes a
   documented legal, ethical or reproducibility gate, or (d) **replaces** a weaker analysis.
   *"Another way of showing the same finding is robust" does not qualify.* This is the
   2026-08-01 wording, now applied to the series.

2. **A round must close its own additions before it ends.** Every probe or gate a round adds must
   be shown **failing** under `scripts/mutation_probe_verifiers.py` before the round is
   committed. This project has twice shipped a gate that could not fail and documented it as
   working (`1eeb978`, `e3938bd`); a passing gate carries no information until something has seen
   it fail. Reasoning about whether a check works is not evidence that it does.

3. **Declare the basis, and never re-round a printed cell.** A figure's population (full roll /
   active roll / matched panel), county footprint, source prefix, tier specification and cycle
   window belong in `docs/reference/derivation-bases.csv` next to the derivation, not in the
   round's head. Any column computed from other figures is computed on **unrounded** values.
   Every flip in the table below was a basis or rounding ambiguity, not a data change:

   | commit | the flip | the actual cause |
   |---|---|---|
   | `69ae5af` | odd-year roll-off 34.7–36.0% → 4.9–6.6% | 38-county numerator over a statewide denominator |
   | `e3938bd` | a "sign flip at 2023" given a causal reading | full-roll reconstruction against an active-roll official figure |
   | `487091e` | Section I's inferred cap | per-cycle inflow compared against pooled outflow |
   | `0b6f7c1` | three state donor tables | the three panels were never on one basis |
   | `5470f7f` | express advocacy "69% for" → 78% | 69% was not a direction: it was the *Independent Expenditure Ad* filing-type share |

4. **The next review is a narrowly scoped pre-submission audit** — consistency, journal
   compliance, citations, anonymity, package sync — not another open-ended critical read.

### The one thing that is genuinely still moving

`data/wa_statewide.duckdb` is appended to daily by the "WA SoS Results Daily Archive" task, and
the 2026 PDC cycle is roughly half collected and still accruing. So a subset of figures does move
under a finished paper without anyone editing anything. Pinned panels
(`scripts/pin_wa_donor_roll.py`, `scripts/pin_ny_roll.py`, the dated
`docs/reference/*_2026-08-*.csv` frames) are immune; unpinned live reads are not. A submission-
ready paper must not depend on an unpinned read, and a verifier that cannot find its pin must
**exit non-zero rather than warn** — reporting a drifting number as though it were the pinned one
is the failure mode, and `verify_cross_state_money.py` described that risk in its own docstring
while only printing a warning.

---

## 1. Verification ledger — re-derive each headline number

**Independent verifiers (the preferred §1 vehicle).** These hit the DBs with
from-scratch SQL — NOT by importing the diag/match code — and print
derived-vs-paper side by side, so a match confirms each finding independently of
the analysis code. Read-only, aggregate-only. Run and eyeball the two columns:

```bash
python scripts/verify_who_decides_wa.py     # who-decides-washington.md  #1-#30  (all match)
python scripts/verify_who_decides_id.py     # who-decides-idaho.md §I-§V          (all match)
python scripts/verify_who_decides_ny.py     # who-decides-new-york.md §I-§VI       (§I/II/V/VI + §III comp match;
                                            #   §III turnout & §IV primary RATES ~1-2pp under = current-roll denom)
python scripts/verify_donor_class.py        # donor-class-and-the-electorate.md F1-F4, both panels x 3 states,
                                            #   PLUS it SCRAPES the paper's prose and tables and asserts
                                            #   309 figures (exits non-zero) — see review log round 4
python scripts/diag_seat_competition.py     # safe-seat-washington.md (WA 5 cycles, both dimensions)
python scripts/verify_cross_state_money.py  # cross-state-fec-money.md — outflow + inflow (advisory),
                                            #   plus §F5/§F6 as 88 HARD assertions (exits non-zero)
python scripts/verify_whitepaper.py         # electoral-health-whitepaper.md Findings 4 & 5 —
                                            #   SCRAPES the prose and asserts it (exits non-zero)
```

> A seventh check, `verify_public_matcher_extract.py`, runs in the **private repo only** —
> it is inherently cross-repo, loading the public `donor_matcher.py` from a sibling
> checkout and anti-joining its rebuilt Idaho federal panel against the one the private
> matcher built (0 differing rows across all 9 columns of all 23,303). It is not published
> because it exists to compare the two trees.

> **`verify_safe_seat.py` is superseded — do not use it for sign-off.** It derived the
> seat universe from the results table, which silently dropped 24 King County House seats
> per cycle in 2016 and 2018. `diag_seat_competition.py` builds the universe from certified
> statewide summaries and **exits non-zero if any cycle fails to reconcile to the statutory
> chamber size**. The old script is retained only so the paper's Appendix G can reproduce
> its own superseded figures.

**Status — all six above, plus the private cross-repo check, re-run 2026-07-27; exit 0, all reproduce.** This supersedes the
2026-07-10 run, which predated the primary-specification switch, the Idaho Sunshine
reload, the NY state panel, and the seat-universe rebuild. `diag_seat_competition.py`
additionally reports "All cycles match the statutory seat universe."

> **Run the verifiers one at a time.** Several attach the same DuckDB file, and running
> them concurrently fails with `IO Error: ... used by another process` — an artifact of the
> lock, not a reproduction failure.

WA outflow reconciles exactly (see below). One known, self-reported divergence remains
(flagged inline by the script, not a paper error):
- **NY §III turnout / §IV primary participation** run ~1-2pp under the paper — current-roll
  denominator sensitivity (the paper's own soft cut); composition/structural cuts match exactly.
- **‡‡ WA outflow concentration — RESOLVED 2026-07-10.** The verifier was recomputing on the
  raw WA `individual_contributions` (state PDC + non-WA donors + odd cycles → 1.12M / 47.5%);
  applying the paper's own filter (`fec_candidate_id ~ '^[CPHS][0-9]'` AND `contributor_state='WA'`,
  matching `cross_state_fec_money.py`) reproduces the paper **exactly: 361,818 donors / top-1%
  39.3% / top-10% 72.3% / Gini 0.800** (cycles resolve to clean 2018–2026 even years; total $646M).
  NY tightened to 671,488 (was 699K raw), TX unchanged — all three now reproduce.

The diag scripts (what the papers were built from) for any remaining ledger cells:

Run from repo root. The WA individual numbers need the VRDB attached, which
`diag_wa_individual_findings.py` handles. Tick each cell once you've reproduced it.

```bash
python scripts/diag_wa_individual_findings.py      # §F1 turnout-by-age + composition + donor layer
python scripts/diag_turnout_decomposition.py       # behavior-vs-rolls split
python scripts/diag_safe_seat_wa.py                # companion paper: observed WA competitiveness
python scripts/diag_safe_seat_states.py            # four-state observed legislative count
python scripts/diag_tx_safe_seat_backfill.py       # TX completion (r206 backfill)
```

**"Who Decides Washington State?" — claims to confirm against `diag_wa_individual_findings.py`:**

| # | Claim in paper | Expected | Source |
|---|---|---|---|
| 1 | 18–29 turnout, 2024 presidential | 58.4% | within-cohort rate table |
| 2 | 18–29 turnout, off-year average (2021/23/25) | ~15.8% | rate table, mean of 3 off-years |
| 3 | 65+ turnout, presidential → off-year | 88.3% → ~61.3% | rate table |
| 4 | 65+ share of electorate, presidential vs off-year | 28.5% → ~40% | composition table |
| 5 | 18–29 share, presidential vs off-year | 14.2% → ~7.6% | composition table |
| 6 | Senior:youth ratio, share basis, pres → off | ~2:1 → ~5:1 | composition table |
| 7 | Roll size: 5.51M registrants / 27.1M vote records / ~100% birthdate | as stated | header line of script output |

**Decomposition — confirm against `diag_turnout_decomposition.py`:**

| # | Claim | Expected |
|---|---|---|
| 8 | 65+ share rise 2024→2025 is behavior, not rolls | +11.8pp total; +10.9pp (92%) turnout-rate, +0.9pp rolls |
| 9 | 18–29 share fall | −6.2pp total; −6.0pp (97%) behavior |
| 10 | Retention off-cycle | 65+ keep 67% of presidential turnout; 18–29 keep 28% |

**Companion (Safe-Seat) — confirm against `diag_safe_seat_*.py`:**

| # | Claim | Expected |
|---|---|---|
| 11 | WA seats not close (Dimension 1), by cycle | 88.1 / 78.9 / 83.6 / 86.5 / **83.5%** (2016→2024); **`diag_seat_competition.py`** |
| 11b | WA seats offering no D-v-R (Dimension 2) | 48.5 / 27.1 / **26.9** / 35.3 / **35.3%** — a *separate* question from 11, not a restatement (2020 corrected 2026-07-28, claim 71) |
| 12 | Four-state lower-chamber not close | WA **87.8** / NY 88.6 / TX 94.0 / ID 92.9% — WA from `diag_seat_competition.py`, NOT the 88.8% that `diag_safe_seat_states.py` still prints |
| 13 | Outflow concentration by state (cross-state §F) | WA top-1% **39.3%** / Gini **0.800**; NY **47.5%** / **0.848**; TX **41.7%** / **0.818** |

> **Claims 11–13 were restated 2026-07-27.** The old row 11 ("~85%") predated the paper's
> split into two dimensions and conflated them; row 12's WA cell read 88.8% from the
> superseded seat universe; row 13 cited a single pooled 47.7% / 0.862 pair that appears
> nowhere in the current paper. Do not sign off against the old values.

**"Who Decides Idaho?" — re-derive (needs `data/id_vrdb.duckdb` from `load_id_voters.py`):**

```bash
python scripts/load_id_voters.py                        # -> id_vrdb.duckdb (voters 1,029,938)
python scripts/diag_id_turnout_party.py                 # turnout by age x party + closed primary
STATE=ID python scripts/backfill_id_recipient_party.py  # recipient party (crossover)
STATE=ID python scripts/match_id_voters_to_donors.py --source state   # donor class x party
#   --source state is the Sunshine panel §VII reports (rows 21-23b); --source fec builds
#   the federal panel. Both default to the full-name key (the primary specification).
python scripts/diag_id_electorate_extras.py             # safe-seat, unaffiliated bloc, cohorts
```

| # | Claim in paper | Expected | Source |
|---|---|---|---|
| 14 | Registration mix | REP 62.9% / UNAFF 23.9% / DEM 11.8% | load_id_voters summary |
| 15 | GOP-ballot share of all primary ballots | 80–86% (2022–2026) | diag_id_turnout_party E1 |
| 16 | Primary party skew vs general | +77 R (primary) vs +51 R (general) | diag_id_turnout_party C |
| 17 | Unaffiliated share of the electorate: roll → general → primary | 23.9% → 22.6% → 5.9% (2024) | diag_id_turnout_party §C (composition, not a turnout rate — see ‡) |
| 18 | GOP-primary electorate age | median 55→63, 65+ 34.5%→46.7% | diag_id_turnout_party E4 |
| 19 | Age gap party-neutral | REP 65+ 31.7% ≈ DEM 31.5% (2024) | diag_id_turnout_party B |
| 20 | Safe-seat map | 2/2 CD + all 35 LD Safe/Likely/Lean R; 0 competitive | diag_id_electorate_extras s5 |
| 21 | Donor class by party (ID **state** panel) | 23,613 donors / $13.64M; DEM **+9.8** skew; UNAFF **−12.3**; donors **51.3%** 65+ | `match_id_voters_to_donors.py --source state` |
| 22 | Donor concentration / geography | top-1% **40.0%**; top-10% **71.0%**; Ada/Boise **50.3%** of $ | same |
| 23 | Crossover (resolved **51%** of donors / 41% of $) | DEM **94.6%**→D; UNAFF **77.1%**→D; REP **79.0%**→R (REP→D upper bound) | same |
| 23b | Donor mix by district safety | 27 Solid-R LDs hold 14,594 donors at **78% R / 13% D**; the 8 Likely/Lean-R LDs hold 9,019 at **47% / 35%** | same |

**"The Donor Class Is Not the Electorate" Appendix G — confirm against
`diag_contribution_limits.py`** (read-only over `id_statewide.duckdb` + `wa_statewide.duckdb`;
no voter file needed):

| # | Claim in paper | Expected | Source |
|---|---|---|---|
| 24 | Idaho's legislative cap binds (bunching) | 6,797 gifts at exactly $1,000 vs 448 at $750, 94 at $999, 1 at $1,001 | G2 |
| 25 | Capped ID state layer is MORE concentrated than ID federal | persons-only top-1% 39.7% vs 36.1%; all-filers 56.4% vs 36.1% | G3 |
| 26 | Same pattern in WA | WA state all-filers top-1% 44.4% vs WA federal 39.3% | G3 |
| 27 | Pure truncation WOULD compress (so the puzzle is real) | WA federal top-1% 39.3% → 32.2% at $5,000 → 26.4% at $1,000 | G4 |
| 27b | Truncation at the federal limit as it actually stood (2026-07-28) | **cycle-specific** limits ($2,700 / $2,800 / $2,900 / $3,300 / $3,500 for 2017-18 → 2025-26) give top-1% **30.9%** / top-10% **67.4%** / **$548M** retained, against the flat-$3,500 row's 31.2 / 67.7 / $554M. The anachronism moved top-1% by 0.3 pts, so it was not load-bearing — but the flat row must not be called "the federal limit" | G4 |
| 28 | Estimator cross-check: ID state persons ≈ the matched layer | 39.7% / Gini 0.800 vs paper's matched 39.3% / 0.798 | G3 vs Finding 2 |
| 29 | Uncapped tail is where ID concentration lives | 41.9% of Sunshine $ in gifts > $5,000; largest single gift $1,245,000 | G2 |

> Appendix G supersedes the earlier Finding-2 parenthetical attributing Idaho's lower
> top-1% share to state contribution limits. That explanation is **disconfirmed** — do not
> reinstate it. Two data hygiene points the script enforces and any re-derivation must
> match: PDC's `SMALL CONTRIBUTIONS` unitemized pseudo-contributor is **excluded** from all
> WA state cuts (left in, it keys as one enormous donor), and the person/organization split
> is a per-layer name heuristic (comma test for Sunshine/FEC `LAST, FIRST`; org-marker test
> only for PDC's `LAST FIRST`, which is why no persons-only WA state figure is published).

> **‡ Claim 17 — Idaho turnout RATES dropped (2026-07-09 turnout sanity pass).** Idaho rates
> computed from the voter file are survivorship-inflated: the 2026 roll (1.03M) is smaller
> than the **1.18M registered at the 2024 election**, so our all-voter 2024 rate comes out
> ~94% against the official **77.8%** (and 2020 computes >100% via `registration_date`
> mutation — re-registrants drop from the denominator but stay in the numerator). The bias is
> non-uniform (young/unaffiliated churn faster), so no rate cut is reliable. §III was reframed
> onto **composition shares** (denominator-free): unaffiliated go 23.9% of roll → 22.6% of the
> 2024 general electorate → **5.9%** of the primary electorate — a cleaner "locked out" than
> the old rate, and directionally conservative (true unaffiliated participation is even lower).
> **WA and NY were checked and are NOT inflated** (our 2024 overall 75.9% vs official 78.9%;
> NY 58.3% vs 60.4% of eligible) — their rolls are stable, so those papers' rates stand. This
> is an Idaho-only fix; the rate columns were removed from `who-decides-idaho.md` §III and the
> diag scripts' rate outputs carry a survivorship caveat.
>
> The two new NY drafts and the cross-state donor-class paper carry their own
> reproducibility blocks; add their headline rows here when you run their verification
> pass (TODO #3). ID donor figures are Idaho Sunshine **state** money (not FEC).

> If any cell disagrees with the paper, the paper is wrong, not the script — fix the
> prose (these scripts are the single source of truth and are re-runnable).

> ### RESOLVED 2026-07-26 — the donor paper now runs on TWO PANELS
>
> **What was wrong.** `match_voters_to_donors` read the whole of
> `individual_contributions` with no money-source filter. Harmless when a state's table
> holds one source; silently wrong when it holds two — and two states hold two: WA carries
> `FEC:` ($646.2M) alongside `PDC:` ($394.6M), and ID carries `FEC:` ($76.2M) alongside
> `SUNSHINE:` ($53.3M) since the 2026-07-19 ID FEC load. Pooling stacks one person's
> federal and state giving into a single donor total, inflating concentration (WA read
> top-1% 46.6% pooled vs 42.4% federal / 43.8% state). WA had been pooled all along; Idaho
> only since 7/19. The paper's old label — "WA and NY are federal, ID is state" — was
> wrong for WA and stale for ID.
>
> **The fix.** `match_voters_to_donors` gained keyword-only `source_prefixes` and
> `output_table`, both defaulting to the historical behavior (all sources ->
> `voter_donor_affiliation`), so the campaign tooling reading that table is untouched.
> Panels are built one source at a time by
> `scripts/match_{wa,ny,id}_voters_to_donors.py --source {fec,state}` into
> `voter_donor_affiliation_fec` / `_state`. Locked in by
> `TestMatchVotersToDonorsSourceScoping` in `tests/test_analysis/test_donor_analysis.py`
> (5 assertions incl. a default-pools-everything regression and an identifier-injection
> guard). `verify_donor_class.py` now verifies both panels.
>
> **The old Idaho figures were right for the specification they were built on** — they were
> the Sunshine panel, and at the time `--source state` reproduced 27,250 voters / top-1%
> 39.3% / Ada 49.2% / DEM +9.1 / UNAFF -11.8 exactly.
>
> ⚠ **Superseded 2026-07-27 by the primary-specification switch.** Rebuilt on the
> full-name key, the ID state panel reads **23,613 / 40.0% / Ada 50.3% / DEM +9.8 /
> UNAFF -12.3**. The sentence that used to stand here — "ledger claims 21/22 describe the
> ID state panel and still hold as written" — **is no longer true**; rows 21-23 have been
> restated above and row 23b added. `docs/who-decides-idaho.md` §VII was still carrying the
> old all-tier figures unflagged and was rewritten on the same date, along with the ID and
> NY donor-mix bullet in `cross-state-fec-money.md` §F5 (NY pooled had moved furthest,
> 308,032 -> 558,017).
>
> Appendix G is unaffected: `diag_contribution_limits.py` selects layers by
> `contribution_id` prefix and never reads `voter_donor_affiliation`.

**Donor paper — panel expected values (`verify_donor_class.py`, both panels):**

| # | Claim | Expected | Panel |
|---|---|---|---|
| 30 | WA federal matched layer | **147,745** donors / **$346.3M** / top-1% **41.2%** / top-10% **74.2%** / Gini **0.815** | federal |
| 31 | WA state matched layer | **217,114** donors / **$122.5M** / top-1% **43.5%** / top-10% **75.3%** / Gini **0.821** | state |
| 32 | NY federal matched layer | **269,218** donors / **$1,015.7M** / top-1% **50.7%** / top-10% **81.2%** / Gini **0.865** | federal |
| 32b | NY state matched layer | **378,383** donors / **$339.8M** / top-1% **48.6%** / top-10% **78.2%** / Gini **0.845** | state |
| 33 | ID federal matched layer | **23,303** donors / **$42.1M** / top-1% **37.2%** / top-10% **70.8%** / Gini **0.789** | federal |
| 34 | ID state matched layer | **23,613** donors / **$13.6M** / top-1% **40.0%** / top-10% **71.0%** / Gini **0.799** | state |
| 35 | WA generation multipliers | federal Silent **2.67x** .. Gen Z **0.04x**; state Silent **1.72x** .. Gen Z **0.11x** | both |
| 36 | ID 65+ donor share | federal **66.8%**, state **51.3%** (roll 31.0%) | both |
| 37 | ID own-party skew replicates | federal DEM **+8.6** / UNAFF **-12.1**; state DEM **+9.8** / UNAFF **-12.3** | both |
| 38 | ID recipient-party resolution | federal **86.7%** vs state ~52% (only the state REP->D rate is an upper bound) | both |
| 39 | WA give<->vote | federal **88.0%** vs **52.0%** super; state **88.9%** vs **51.5%** | both |
| 40 | WA bootstrap CIs (B=1,000) | federal top-1% **41.2% [38.6-43.4]**, Gini **0.815 [0.806-0.822]**; state **43.5% [38.7-48.9]** | both |

**Added 2026-07-27 in response to external review.** All re-derived by
`verify_donor_class.py` except where noted; the recomputations themselves are in
`scripts/diag_donor_class_revisions.py`.

| # | Claim | Expected | Panel |
|---|---|---|---|
| 60 | NY own-party skew, **ACTIVE** baseline | federal DEM **+16.1** / NOPARTY **-13.7**; state DEM **+9.6** / NOPARTY **-12.6** | both |
| 61 | NY active roll | 12,448,081 active of 13,540,558 records (91.9%); every ID record active | — |
| 62 | NY give<->vote, active denominator | federal **3.10** vs 1.85 generals, **75.7%** vs 39.3% super; state **3.07** vs 1.84, **75.3%** vs 39.0% | both |
| 63 | ID unaffiliated composition | roll 23.9% / 2024 general 22.6% / 2024 primary **5.9%**; primary ballots pulled REP 83.7% / DEM 12.2% / UNA 3.5% | — |
| 64 | ID period-aligned panels (2023-2025) | federal **14,848** donors / **$18.4M** / top-1% **34.7%** / 65+ **68.5%**; state **23,613 / $13.6M / 40.0% / 51.3%** | both |
| 65 | Panel overlap (Jaccard) | WA **0.159**, NY **0.161**, ID **0.141**; both-systems donors older than either single-system group in all three | both |
| 66 | Match-tier mix (in the retained `_alltier` snapshots) | `STRICT_ZIP5_FULL` **80.7-89.2%** of matches; weakest `RELAXED_ZIP3_MID` 0.3-5% | both |
| 67 | Tier sensitivity (full-name tier only) | every headline survives; 65+ *rises* in all six panels (e.g. NY fed 47.9% -> 49.9%); top-1% moves <=1.3 pts | both |
| 68 | Household bounding exclusion | surname+ZIP5 drop removes 75-83% of donors; top-1% moves <=4.7 pts, 65+ rises in all six | both |
| 69 | Crossover resolution rates (differential) | NY fed DEM 90.1% vs NOPARTY 79.2%; NY state REP 45.2% vs NOPARTY 27.7% — not missing at random | both |
| 70 | Aggregate recipient-party resolution | NY fed **87.8%**, NY state 37.7%, ID fed 86.7%, ID state **51.9%** (the "79%" in earlier drafts was stale) | both |
| 71 | Itemization thresholds | federal >$200; WA >$100; NY >$99; ID >$50 — *not* a uniform $200 rule | — |
| 72 | Match precision by tier (`score_match_validation.py`) | `STRICT_ZIP5_FULL` **100.0%** (120/120, Wilson [96.9-100]); `STRICT_ZIP5_MID` 71.7%; `STRICT_ZIP5` **47.9%**; `RELAXED_ZIP3_MID` **50.4%** | both |
| 73 | Population-weighted precision | WA fed 93.3 / WA state 90.4 / NY fed 93.1 / NY state 94.3 / ID fed 92.6 / ID state 96.5; donor-weighted **93.0%** (bound 92.9%) | both |
| 74 | Precision by dollar band | top decile 63.0% vs deciles 2-10 72.1% (raw, tier-confounded) — lower at the top | both |
| 75 | Error modes of 152 confirmed-false | 129 household/relative (initial-based keys only, **0** on full-name key); 14 organisation-as-person (**all ID Sunshine**); 9 name-order parse (**all WA PDC**) | both |
| 76 | Sunshine organisation contamination | 4.7% of rows but **32.6% of dollars** look like organisations, vs 0.1% / 0.8% for WA PDC | state |

**Added 2026-07-27 (second pass) — the primary-specification switch.** Panels rebuilt on the
full-first-name key; see `docs/reference/primary_spec_figures_2026-07-27.md`.

| # | Claim | Expected | Panel |
|---|---|---|---|
| 80 | Reconciliation, all six panels | an independent rank-0 reconstruction reproduces each panel's donor count and `SUM(total_donated)` **to the cent** (asserted by `verify_donor_class.py`) | both |
| 81 | Two-definitions dollar delta | filter-a-panel vs restrict-the-match: **7.71%** WA fed, **9.44%** WA state, **5.35%** NY fed, **3.77%** NY state, **5.89%** ID fed, **5.76%** ID state; donor counts identical in all six | both |
| 82 | Pooled tables | WA 382,408 -> **314,974** ($574.21M -> **$468.85M**); ID 47,762 -> **41,136**; NY 308,032 -> **558,017** (tier switch PLUS correction of a stale FEC-only build — two causes, do not conflate) | pooled |
| 83 | Full-name-key namesake collision | middle-initial signal **0.03-2.14%** of donors, and **0.00% at one gift in every panel** rising to 0.36-8.33% at 20+ gifts = recording noise, not two people. The paper's old 7-9% was computed on a first-initial join and is withdrawn | both |
| 84 | Roll-side inactive namesakes | **0.21-0.40%** (WA fed 0.24%, NY fed 0.40%); not measurable for ID | both |
| 85 | Recall cost / selection bias | discards **10.8-19.3%** of donors; discarded set younger in all six panels (WA fed 40.5% vs 55.7% over-65) and less Democratic in all four party panels (NY fed 56.6% vs 63.6%) | both |
| 86 | Joint filings | 0.06-0.25% of dollars everywhere except **ID Sunshine 1.87% of rows / 3.27% of dollars** (~20x outlier; explains 6 of 8 partial merges) | both |
| 87 | WA PDC name-order parse failure | **1.85%** of comma-less rows / **2.08%** of dollars — NOT the 0.1%/0.8% organisation figure the paper cited as its analogue | state |
| 88 | NY duplicate voter ids in panels | 0 of 53 reach the federal panel, **5** reach the state panel, all on the rank-0 key; NY state reads 378,383 standalone / 378,388 after a roll join | both |
| 89 | contributor_type backfill | WA 8,599,537 PERSON; NY 13,974,685; TX 12,563,547; ID 770,765 PERSON + **216,700 NULL** (Sunshine, awaiting its deferred reload) | — |
| 90 | ID Sunshine reload (2026-07-27) | returns exactly 216,700 contributions / 2,067 candidate_finance / 1,139 IE; Appendix G byte-identical ($53,256,865.38 layer, max gift $1,245,000, 668 gifts >$5k = 41.9% of layer $) | state |
| 91 | ID Sunshine contributor_type | PERSON **181,749** / UNKNOWN **17,374** / ORGANIZATION **14,273** / COMMITTEE **3,304**; org+cttee = 8.1% of rows but **53.9% of dollars** | state |
| 92 | Reload effect on panels | **none** — ID state 23,613 / $13.64M, pooled 41,136 / $55.75M, aligned state 23,613 / $13.64M all unchanged; **zero** org rows can match rank-0 | both |
| 93 | Human re-rating, primary spec | **75/75** full-name-key records rated Y, Wilson [95.1-100]; zero divergences in that block | both |
| 94 | Inter-rater agreement | 4-category observed 88.0% / kappa **0.656** / PABAK 0.760; collapsed binary 93.9% / kappa **0.815** / PABAK 0.878; full-name block kappa undefined (no variance), PABAK 1.000 | both |
| 95 | Divergence direction | all 18 on initial-based keys; 6 NC->Y, 7 NC->NP, 3 NP->Y, 2 U->Y, and **zero** AI-Y -> human-non-Y. Human donor-weighted precision **95.7%** vs AI 93.0% | both |
| 96 | Human weak-tier rates | 64-68% against the AI's 47.9-71.7%; qualitative finding robust, exact rates rater-dependent | both |
| 97 | Geography of matched dollars, **primary spec** (2026-07-28) | WA fed 981xx **37.9%** + 980xx 25.6% = **63.5%** (state 31.6+23.8 = 55.4%); NY fed Manhattan **48.5%** / top-3 ZIP3 62.4% (state **19.9%** / 37.6%, Nassau 15.5%, Suffolk 11.3%); ID state Ada **50.3%** (8,812 donors), fed Ada 36.8% (8,865) with **Bonneville 11.9% now ahead of Blaine 11.4%** | both |
| 98 | NY donor pool by CD competitiveness, **per panel** (2026-07-28) | federal Tossup **58.7%** D / Solid **72.6%** D; state 51.3% / 66.9%; registrants 40.4% / 56.1%. D share of the donor pool exceeds registration in every band in **both** panels; Solid districts hold 177,918 of 269,218 federal and 233,275 of 378,383 state donors | both |

---

## 2. Statute cites — DONE (re-verified 2026-06-29)

**Added 2026-07-29 (round 9): 52 U.S.C. § 30111(a)(4) / 11 C.F.R. § 104.15** — the FEC "sale or
use restriction". Information copied from a filed report may not be sold or used to solicit
contributions or for any commercial purpose; § 104.15(b) reads "soliciting contributions" to
cover any contribution or donation; § 104.15(c) is the publication safe harbour this research
relies on. Verified against the eCFR text. **This was the round's most consequential finding: the
repo had cited only § 30104 (the disclosure mandate) and classified the FEC layer as
unrestricted, while shipping FEC-derived fundraising prospect lists.** See
`fec-contributor-data-use-memo.md` (internal; not published).

**Also verified 2026-07-29:** N.Y. Election Law **§ 3-103(5)** (elections-purpose certification;
NYSBOE's published guidance states the purpose "has traditionally been interpreted broadly and
among other things includes campaigning, voter outreach, fundraising and academic research" —
which closes the NY open item); **Idaho Code § 34-437A** as the operative Idaho provision, with
§ 74-120 correctly demoted to a general restriction on agency mailing/telephone lists.

- **WA RCW 29A.08.720** (political use allowed; advertising/solicitation barred) + **29A.08.740**
  (penalties) — verified against current code at app.leg.wa.gov. Appendix sharpened from the bare
  chapter cite to these subsections.
- **Idaho Code §74-120** ("Prohibition on distribution or sale of mailing or telephone number
  lists"; releases registrant age, withholds DOB/DL#/address) — verified at legislature.idaho.gov.
- Remaining human step: one final glance at publication time (statutes can amend).

**Campaign-finance statutes added 2026-07-26** for the donor paper's Appendix D / Appendix G.
Verified against the primary sources noted; the two flagged items need a human glance before
posting:

- **Idaho Code § 67-6610A** — individual contributions capped at **$1,000/election**
  (legislative, judicial, local) and **$5,000/election** (statewide); primary and general are
  separate elections; candidate self-funding exempt. Verified at legislature.idaho.gov.
- ⚠ **Idaho S.B. 1422 (2026)** would have raised those to $1,500 / $6,000 (a full rewrite of
  Chapter 66 into Title 74, Ch. 3). Bill history at legislature.idaho.gov ends **"04/01
  Retained on calendar"** with no passage or signature recorded. Cited in the paper as
  *proposed only*. **HUMAN: confirm it died before publication** — if it was enacted, the
  Appendix D figures need the effective date and both regimes.
- **52 U.S.C. § 30116** — federal individual-to-candidate limit **$3,500/election** for the
  2025–26 cycle (was $3,300 in 2023–24); indexed. Also **§ 30118** (corporate contribution
  prohibition, which ID and TX state law do not share).
- ***McCutcheon v. FEC*, 572 U.S. 185 (2014)** — struck the biennial **aggregate** limit, so
  no federal ceiling on a donor's total giving. Load-bearing for Appendix G's mechanism.
  ***Buckley v. Valeo*, 424 U.S. 1 (1976)** for the contribution/expenditure asymmetry.
- **Tex. Elec. Code § 253.094** — bars corporate/labor contributions; **no dollar limit** on
  individual gifts to non-judicial state candidates. Judicial Campaign Fairness Act,
  §§ 253.151–253.176, is the capped exception. This replaces the previously uncited "no
  contribution limits" assertion in `cross-state-fec-money.md` K1.
- ⚠ **WA RCW 42.17A.405**, recodified **RCW 29B.40.020** eff. **Jan. 1, 2026**. Cited without
  a dollar figure. **HUMAN: if a specific per-election amount is ever quoted, confirm it
  against the PDC's current indexed schedule** — the amounts are adjusted, not statutory.

**WA PDC itemization threshold — CHECKED 2026-07-28, reviewer was right, and the real problem
was bigger.** The reviewer flagged the paper's "effective Jan. 8, 2024" and said the PDC's
material gives **April 1, 2023**. Verified against WAC 390-05-400 as certified 1/14/2026 and
the PDC's own release:

- The **$100** contributor-identity threshold took effect **1 April 2023** (WSR 23-07-004,
  filed 3/1/23). The rule's own table reports the current values as "last set in 2023".
- **Jan. 8, 2024 is a real amendment date** for WAC 390-05-400 (WSR 24-01-028, filed
  12/8/23) — so the paper's date was not invented — but it is not the amendment that set
  this threshold. A later amendment, WSR 26-01-209 eff. 1/1/26, also left the row unchanged.
- **The consequential finding the reviewer did not reach: the threshold was $25 before that.**
  The statutory value is **$25** (1982) and WAC 390-05-400's "previous adjusted value, last
  set in 2016" cell for this row is ***n/a*** — no intervening adjustment. The WA PDC layer
  spans **2016–2026**, so the floor was $25 for roughly seven of ten years and $100 for
  three. The paper had a flat "> $100" in five places.
- Also corrected: occupation/employer was **> $100** before April 2023 and **> $250** after
  (WAC 390-16-034); the mini-reporting limit went $5,000 → **$7,000** while the **$500**
  per-contributor figure is unchanged.

**And the floors do not describe the data at all — measured, not assumed.** Prompted by the
reviewer's point that a statutory threshold is not the contents of the file. Every floor is a
per-donor **aggregate**, so a donor who crosses it has all their gifts itemized including
sub-floor ones, and committees disclose below what is required. Measured: **89.9%** of federal
gifts are ≤$200, **84.5%** of WA PDC gifts ≤$100, **62.6%** of NY ≤$99, **68.4%** of ID ≤$50;
at the donor level **53.5%** of WA's matched state donors have totals ≤$100 and **17.9%**
≤$25, smallest one cent. The paper's "each panel omits giving below its own threshold" was
false for all four layers and is replaced by the accurate statement: the analysis accepts
every itemized record each agency publishes and filters by no threshold; what the floors
exclude is donors whose *aggregate* never crosses them. Two downstream effects, both now in
the paper: the itemization bound on concentration is **tighter** than a floor-based reading
implies (Appendix A objection 5), and the federal-vs-state confound **cannot** be removed by
comparing at nominal floors — which is a direct answer to the reviewer's suggestion to
harmonize at $200. All of these figures are now probed and audited (`limits_itemization`,
`appd_belowfloor`).

**The three remaining legal citations — ALL FIXED 2026-07-28, and one of them exposed a
contradiction the reviewer did not reach.**

1. **Federal cap across cycles.** ✅ The limit is indexed biennially: **$2,700** (2017–18),
   **$2,800** (2019–20), **$2,900** (2021–22), **$3,300** (2023–24), **$3,500** (2025–26),
   per the FEC's archived limit charts. Appendix G4 was trimming a 2017–2026 layer at a flat
   $3,500 and calling it "the federal limit". `diag_contribution_limits.py` now also computes
   a **cycle-specific** row (claim 27b) and the flat rows are relabelled as counterfactual
   thresholds. Appendix D states all five cycle values.
2. **RCW 29A.08.720.** ✅ Verified against the statute. "Use is restricted to elections and
   political purposes and may not be commercial" was broader than the text and had its
   structure backwards. The section *prohibits* using the lists to mail or deliver "any
   advertisement or offer for any property, establishment, organization, product, or service"
   or "any solicitation for money, services, or anything of value", and *affirmatively
   permits* use "for any political purpose", expressly including "advertising for or against
   any candidate or ballot measure or **the solicitation of financial support**". So the test
   is not commerciality in the abstract. Appendix B now quotes the operative language and
   documents the permitted-use basis this work relies on, which matters because the author is
   associated with a consulting company. A documented data-use determination is still open
   (§5 gate).
3. **N.Y. Elec. Law § 14-116.** ✅ The reviewer was right that it does not establish the
   individual limits. It is "Political contributions by certain organizations" — New York's
   **corporate and LLC contribution ban**, with a narrow $5,000 annual exception and an LLC
   ownership-disclosure requirement. § 14-114 ("Contribution and receipt limitations") is the
   limits provision; its ceilings are cycle totals split evenly between primary and general,
   which is why the per-contest figures are $3,000 / $5,000 / $9,000 against cycle limits of
   $6,000 / $10,000 / $18,000. Both are now cited for what they actually do.

⚠ **And a contradiction this surfaced.** Once § 14-116 was correctly identified as a
corporate ban, the paper's claim that "the Idaho and Texas state systems do not share" the
federal corporate prohibition became visibly wrong — **Texas bars corporate and
labor-organization contributions as a third-degree felony** (Tex. Elec. Code § 253.094),
which this same appendix cited two lines above. Appendix G1 made the same error ("Idaho and
Texas also permit direct corporate and PAC contributions"), and additionally said federal law
forbids *PAC* contributions to candidates, which it does not — federal multicandidate
committees may give subject to their own limit. Corrected in both places: the corporate
prohibition is shared by federal law, **New York and Texas**; **Idaho** is the one system
here that permits direct corporate contributions to candidates.
- ⚠ **N.Y. Elec. Law § 14-114** (New York's caps) — cited qualitatively ("high") and **not
  independently verified this session**. Confirm the section number before posting, or drop
  to a bare "New York's caps are comparatively high" with no cite.
- **N.Y. Pub. Off. Law art. 6** (FOIL) as the access basis for NYSVOTER in Appendix B —
  the specific NY Election Law provision governing voter-list release was **not** verified;
  Appendix B deliberately cites only FOIL plus the Board's elections-purpose certification.

---

### Record-linkage literature — added 2026-07-28, and it changed how the design is described

The external reviewer called the absence of linkage methodology "the significant omission,
because the principal contribution depends on matching validity." Appendix D now carries a
subsection on it. Six citations, each verified against the publisher (not recalled), and the
section is framed as *locating* this design rather than defending it:

| citation | why it is in the paper |
|---|---|
| Fellegi & Sunter, *JASA* 64(328) (1969): 1183–1210 | the probabilistic framework this paper's deterministic key is a restrictive special case of |
| Herzog, Scheuren & Winkler, *Data Quality and Record Linkage Techniques* (Springer, 2007) | standard practitioner treatment |
| Enamorado, Fifield & Imai, *APSR* 113(2) (2019): 353–371 | the political-science standard implementation — and demonstrated on **exactly this problem**, campaign contributions merged to voter files |
| Ansolabehere & Hersh, "ADGN", *Statistics and Public Policy* 4(1) (2017) | the linkage-key benchmark (A/D/G/N, false negatives <1%) this design cannot reach, for legal not technical reasons |
| Bailey, Cole, Henderson & Massey, *JEL* 58(4) (2020): 997–1044 | measured false-match rates of **15–37%**, error **systematically** related to record characteristics, downstream attenuation up to 29% |
| Lahiri & Larsen, *JASA* 100(469) (2005): 222–230 | bias from analysing linked data as error-free, and the correction this design cannot use |

**Three admissions the section makes that earlier drafts did not.** (1) A deterministic key
moves the linkage uncertainty *out of the estimator and into the sample definition* — a
probabilistic linkage carries match probabilities into the analysis, this one cannot, so its
error can only be bounded by validation. That is now stated as the design's most substantial
methodological limitation. (2) The ADGN benchmark is out of reach because **the donor side has
no DOB, gender or verified address** — a property of what disclosure regimes publish, not of
the method. (3) Bailey et al.'s finding that linkage error is *systematic* rather than random
is exactly what this paper observes twice: all 129 household/relative false merges sat on
initial-based keys, and the clean-key restriction discards younger, less-Democratic donors.
The second is a selection effect on the estimand, which is why both specifications are
reported.

Still an inventory rather than a review, and flagged as such in the submission notes: the
other three literatures (donor composition; small-donor and itemization selection;
concentration and geographic donor networks). The novelty claim is the author's to make.

## 3. Hand-rate the match sample (TODO #4) — needed only for the money/donor papers

> **REOPENED 2026-07-27 after external review.** The 2026-07-10 rating stands as an
> *indication* but not as a validated precision estimate, and two things previously
> recorded here were wrong:
>
> - **The verdicts were not retained, deliberately.** `data/validation/match_validation_sample.csv`
>   exists but its `is_same_person(Y/N/?)` column was empty: the rating sheet pairs voter
>   names with donor names, and the project's rule is not to keep individual-level rows.
>   Sound PII hygiene, and the earlier "filled CSV" note was simply inaccurate about it. The
>   consequence stands either way " — the confirmed/probable/unverifiable split and precision
>   by dollar decile cannot be re-derived from that pass. A list regenerated 2026-07-27
>   reproduces 15/150 (90.0%) with spousal notes, corroborating the reported figure, but a
>   reconstruction is not a preserved artifact and the paper says so.
>   **This is now moot for every published claim:** the 480-record AI pass and the 150-record
>   human re-rating supersede it, and both publish PII-free verdict ledgers under
>   `docs/reference/`, which is how the persistence problem is solved going forward.
> - **"Spousal mis-attributions barely move the cuts" is withdrawn.** Spouses can differ
>   in age, party enrollment and turnout history, and merging two people's giving into one
>   donor total directly *raises* measured concentration. The argument was asserted, not
>   tested.
>
> What the 2026-07-10 pass does say: first pass 9 flagged, second more thorough pass 15
> flagged → **≈90% apparent precision** (135/150), dominant error spousal/household
> false-merge. Its limits: drawn from the **pooled** `voter_donor_affiliation` table,
> **Washington only**, **unstratified** (130/13/4/3 across the four tiers, so 3-4 records
> in the weak tiers), **not blinded**, single rater.
>
> **What now stands in its place** (done, `diag_donor_class_revisions.py`): per-tier and
> household sensitivity on every headline estimate in all six panels, plus a per-tier
> donor-side collision rate over the full panels (7-9% on the dominant tier, which
> brackets ≈90% independently). See donor-class paper Appendix F.
>
> **DONE 2026-07-27 — stratified blinded re-rating complete.**
> `scripts/diag_match_validation_stratified.py` + `scripts/score_match_validation.py`.
> 480 records, **20 per state x panel x tier cell**, split 10/10 top-dollar-decile vs
> deciles 2-10. Evidence file carries NO stratum labels and is shuffled before opaque ids
> are assigned; the key is joined only after verdicts are recorded. The scorer was written
> BEFORE the verdicts, so the analysis was pre-specified. Verdicts published PII-free at
> `docs/reference/match_validation_verdicts_2026-07-27.csv`.
>
> **HEADLINE: precision is entirely a function of match tier.**
>
> | tier | share of matches | precision | Wilson 95% CI |
> |---|--:|--:|---|
> | `STRICT_ZIP5_FULL` | 81-89% | **100.0%** (120/120) | [96.9-100.0] |
> | `STRICT_ZIP5_MID` | 0.4-2% | 71.7% | [63.0-79.0] |
> | `STRICT_ZIP5` | 9-13% | **47.9%** | [39.1-56.8] |
> | `RELAXED_ZIP3_MID` | 0.3-5% | **50.4%** | [41.6-59.2] |
>
> Population-weighted (each tier by its share of the panel): WA fed 93.3 / WA state 90.4 /
> NY fed 93.1 / NY state 94.3 / ID fed 92.6 / ID state 96.5; **donor-weighted 93.0%**,
> bound 92.9%. So the old ~90% was roughly right at panel level but concealed the
> structure. The raw sample mean (67.6%) is NOT a panel estimate — weak tiers are
> oversampled 30-300x.
>
> Precision is LOWER in the top dollar decile (63.0% vs 72.1% raw) — the direction the
> reviewer worried about. Error modes, of 152 confirmed-false: **129 household/relative
> merges, all on initial-based keys, ZERO on the full-name key**; **14 organisations parsed
> as people, all Idaho Sunshine**; **9 name-order parse failures, all WA PDC**. Both
> format defects follow from those files having no comma, so the parser takes token 1 as
> the surname.
>
> **ACTION IMPLIED (author decision):** make `STRICT_ZIP5_FULL` the paper's **primary
> specification**. It carries 81-89% of matches, has no detectable false match, and moves
> every headline AWAY from the null (65+ rises in all six panels, DEM skew rises in all
> four party panels, concentration moves <=1.3 pts). The all-tier figures currently in the
> paper are therefore conservative. Cost: discards 11-19% of matched donors. Separately,
> the Idaho Sunshine loader needs a person/organisation filter regardless of tier choice.
>
> **CAVEAT, disclosed in the paper:** the adjudication was performed by the AI assistant
> under the blinding protocol, not an independent human rater. It is seeded, published and
> pre-specified — auditable in a way the 2026-07-10 pass was not — but it is single-rater
> and by the same system that produced the analysis. Remaining item: a human spot-check,
> ideally a second rater on the initial-based tiers where judgments are hardest.

Not on the critical path for the lead turnout paper (no name-matching in it), but
required before the donor-class paper:

```bash
python scripts/diag_match_validation_sample.py   # writes data/validation/match_validation_sample.csv (gitignored; PII)
```

Fill `is_same_person` (Y/N) by hand; precision = Y / (Y+N). Structural ceiling is
already known low (87% full-name agreement, 13% namesake risk), so the hand rate
calibrates the donor-overlap figures, not the turnout finding. **Sample generated to
`data/validation/` 2026-07-10** (seed-42 deterministic — the same 150 rows already
hand-rated; the file is gitignored so the PII never enters the repo).

---

## 4. SSRN + SocArXiv submission package

Both are free, citable, **not peer review** — discoverability + a timestamp + a DOI
(SocArXiv). Submit the lead paper as a single PDF (render via `scripts/md_to_pdf.py`).

**Metadata (reuse for both):**

- **Title:** *Who Decides Washington State? The Gray Off-Year Electorate, Measured from 27 Million Individual Vote Records*
- **Author:** [your name], Tikor Consulting. Note "AI-assisted analysis; all figures independently reproducible from public records via the cited open-source scripts."
- **Abstract (draft, ~150 words):**
  > Washington holds its most local offices — city councils, school boards, port and
  > fire commissions, many county and judicial seats — in odd-numbered, off-cycle
  > Novembers, when about a third of registered voters return a ballot. Joining the
  > state's 5.5-million-voter registration roll to 27.1 million individual vote
  > records and each voter's birthdate, this paper measures who that third is. The
  > off-year electorate is not a smaller copy of the presidential one; it is an older
  > one. Turnout among voters 18–29 collapses from 58.4% in 2024 to roughly 16%
  > off-cycle — a 42-point drop — while voters 65+ fall only from 88% to about 61%.
  > Seniors make up ~40% of off-year voters versus 28.5% presidentially; the
  > senior-to-youth ratio roughly triples. A behavior-vs-rolls decomposition shows
  > 92% of the skew is turnout, not registration — pointing to on-cycle election
  > timing as the lever.
- **Keywords:** off-cycle elections; voter turnout; local elections; election timing; age and participation; Washington State; democratic representation.
- **SocArXiv subject:** Social and Behavioral Sciences → Political Science → American Politics. **License:** CC-BY 4.0 (recommended) or CC0.
- **SSRN classification:** Political Science Network → Elections, Voting, Public Opinion.

**Mechanical steps:**

1. Render the lead paper to PDF (`python scripts/md_to_pdf.py docs/who-decides-washington.md`); proof it.
2. **SocArXiv:** osf.io/preprints/socarxiv → "Add a preprint" → upload PDF → paste metadata → submit (gets a DOI in ~1 day).
3. **SSRN:** papers.ssrn.com author login → "Submit a paper" → same metadata → submit (review queue ~1–2 weeks).
4. After both are live, drop the links into the white-paper header and notify the timing-reform audience (Sightline, Unite America) per TODO #7.

---

## 5. Pre-publication gate (do not post until all checked)

- [ ] §1 verification ledger fully reproduced by you (the non-negotiable) — **AI-side
  re-confirmed 2026-07-27: all seven verifiers re-run, exit 0, reproduce (see §1 status),
  and every panel reconciles to the cent; the independent human sign-off under your name
  still remains.** This is the one gate no amount of AI verification can close.
- [x] §2 statute cites re-verified (2026-06-29)
- [x] §6 full sanity pass complete — turnout / composition / safe-seat / money / match, all
  done (2026-07-10)
- [~] §4 PDFs **all re-rendered and current as of 2026-07-27** — every `docs/*.md` with a
  PDF counterpart was checked against its source timestamp in both repos and re-rendered
  where it lagged. Final proof (table layout, first page, author block) = **HUMAN**
- [x] Author byline + AI-assistance disclosure present on **all seven** papers
  (2026-07-27). Washington, donor-class, safe-seat and money-moves-votes already carried
  the block; `who-decides-idaho.md`, `who-decides-new-york.md` and
  `cross-state-fec-money.md` were missing it entirely and now carry the same standard
  block, each naming its own verifier. Wording is **HUMAN** to approve, but no paper is
  now unattributed.
- [x] (donor papers only) §3 match sample re-rated **stratified + blinded, 2026-07-27**
  (480 records, 20/cell; verdicts published PII-free). Per-tier precision: full-name key
  **100%**, initial-based keys 48-72%; donor-weighted **93.0%**. See §3.
- [x] (donor papers only) **Author decision TAKEN 2026-07-27: `STRICT_ZIP5_FULL` is the
  primary specification.** All six panels and the three pooled tables were rebuilt on it;
  the all-tier panels are retained as `*_alltier` snapshots (they are the superset and
  cannot be re-derived) and carry the tier/household/donor-risk sensitivities. Every
  affected paper, the donor submission metadata, and the ledger rows above were moved onto
  the new figures. The selection cost — the discarded donors are younger and less
  Democratic — is disclosed in the paper rather than buried. See §3 and claims 80-96.
- [x] (donor papers only) **Human re-rating DONE 2026-07-27.** Independent rater, 150 of the
  480 records, blind (fresh ids, no stratum labels, no AI verdict), scorer committed first.
  **75 of 75 full-name-key records agreed** — the primary specification holds. Cohen's kappa
  0.815 collapsed-binary / 0.656 four-category overall; all 18 divergences on initial-based
  keys and all in the direction of the human being MORE permissive, so the published
  weak-tier rates are conservative. Verdicts at
  `docs/reference/match_validation_human_verdicts_2026-07-27.csv`.
- [x] Person/organisation filter on the Idaho Sunshine loader **DONE 2026-07-27**, from the
  real `Contributor Type` field rather than a name heuristic. Reload verified against a file
  backup plus in-DB snapshots of all three replaced tables; every Appendix G figure is
  byte-identical. Organisations + committees are **8.1% of Sunshine rows but 53.9% of its
  dollars** ($28.70M of $53.26M), well above the 32.6% the heuristic estimated. It changed
  **no** panel figure — zero organisation rows can match on the full-name key — so it is
  defence-in-depth for the retained all-tier panels and any future source.
- [ ] (donor papers only) **Tagged release + archival DOI** for the public repo (Zenodo or
  OSF), cited in the paper in place of a mutable branch — **HUMAN**. Every paper's byline
  block links `github.com/skirby359/who-decides` without a commit pin, so a reader cites a
  moving branch. **Prepared 2026-07-27:** `CITATION.cff` is committed in the public repo
  with the author block, abstract, keywords and licence filled in, and carries the four
  mechanical steps inline. What remains is genuinely human: sign in to Zenodo, enable the
  repository, tag a release, then paste the concept DOI into `identifiers` and into the
  seven byline blocks. Zenodo only archives releases created *after* the hook is enabled,
  so enable it before tagging.
- [x] (donor papers only) **The public release is rebuildable from raw inputs**
  (2026-07-27). Rather than publishing `src/wa_analyzer/db.py` — the product's entire schema
  definition — the matcher was **extracted**: `who-decides/scripts/donor_matcher.py` carries
  `match_voters_to_donors` verbatim plus the two `contributor_type` helpers, the backfill,
  and a minimal DDL for the two tables it writes (`voter_donor_affiliation`,
  `committee_party_override`). Its only import is `duckdb`. The five public scripts that
  previously reached into `wa_analyzer` — `match_{wa,ny,id}_voters_to_donors.py`,
  `backfill_contributor_type.py`, `diag_donor_class_revisions.py` — now import it as a
  sibling and run from a bare clone. **Verified end-to-end:** the public wrapper rebuilt the
  Idaho federal panel and an anti-join against the published table found 0 differing rows in
  either direction across all 9 columns of all 23,303 rows, with the script reprinting the
  paper's Idaho figures (66.8% aged 65+; top 1% = 37.2% of matched dollars). Paper §
  reproducibility statement and the public README updated from "not yet covered" to covered.
- [~] **Data-use and research-ethics determination DRAFTED 2026-07-29** —
  [`data-use-and-research-ethics-assessment.md`](data-use-and-research-ethics-assessment.md). Self-assessment, not
  IRB: no board has jurisdiction. Concludes not-human-subjects (no intervention; registration
  and itemized giving are published *by statute*, so not "private information" under 45 CFR
  46.102(e)(4)), with 46.104(d)(4) secondary-research exemption in the alternative — and states
  its own weak point, that the "publicly available" limb fits the FEC file but not the
  use-restricted voter files. Disclosure controls documented as implemented: smallest published
  cell **44 individuals**, `data/` gitignored wholesale, published reference CSVs identifier-free.
  **HUMAN to sign**, and two gaps to close first: NY's FOIL elections-purpose certification and
  Idaho Code § 74-120 need the statutory analysis WA's RCW 29A.08.720 received.
- [ ] Posted to SocArXiv + SSRN; links folded back into the white paper — **HUMAN**

---

## 6. Sanity-pass log

Running record of independent checks against official/external sources. Prompted by
two defects found during validation (claim #17 denominator; Idaho turnout inflation).

**Turnout rates vs official — DONE 2026-07-09.** The method computes turnout as
past-voters ÷ current-roll, which inflates when the roll has shrunk since the
election. Checked all three voter-file states:

| State | our 2024 overall | official | verdict |
|---|--:|--:|---|
| WA | 75.9% | 78.9% of registered | sound (ours slightly low — stable roll) |
| NY | 58.3% | 60.4% of eligible (higher on registered basis) | sound (ours low) |
| ID | ~94% | **77.8% of registered** | **inflated** — roll shrank 1.18M→1.03M |

Action: `who-decides-idaho.md` reframed onto composition shares (no rate claims);
WA/NY rates stand (both papers already lead with composition). See ‡ above.

**Composition robustness — DONE 2026-07-09.** Using WA's two roll snapshots
(`voters_20230901` vs current `voters`), the 504K voters who *left* the roll skew
**older** (33.1% 65+ vs 23.9% retained; median 50 vs 48 — deaths dominate). So a past
electorate reconstructed from the current roll *under-counts* older voters → the
"gray electorate" finding is **conservative (a lower bound), not inflated**. Within-
contest comparisons (general vs primary) use the same surviving population, so those
contrasts are unaffected. Direction confirmed empirically for WA (anchors the series);
ID has larger attrition but the same death-dominated mechanism.

**Safe-seat counts — DONE 2026-07-09.** `diag_safe_seat_states.py` reproduces exactly:
WA 88.8 / NY 88.6 / TX 94.0 / ID 92.9% non-competitive (lower chamber).

**Cross-state money — DONE 2026-07-09 (independent recompute).** Every headline verified:
WA concentration top-1% 47.74% / top-10% 79.98% / Gini 0.8617 / 382,408 voters ($574.2M
matched base); FEC inflow 5,480,513 rows / $1.20B (WA $154.6M / NY $462.7M / TX $582.4M);
ID top-1% 39.3% / Gini 0.798 / ADA 49.2%. **One real error fixed:** `who-decides-idaho.md`
ID donor top-10% read "69%" — corrected to **71%** (data = 70.8%; cross-state doc was already right).
- Follow-ups: ~~"$128M matched" is a stale pre-Tier-0 figure~~ **FIXED 2026-07-10** (memory
  index + donor_prospects.md now read 382K / $574.2M; the WA lead paper never carried it).
  ~~WA resident-donor outflow "$646M" vs raw `individual_contributions` $1.04B — confirm the
  filter~~ **CONFIRMED 2026-07-10**: the filter is `fec_candidate_id ~ '^[CPHS][0-9]'` AND
  `contributor_state='WA'` (drops PDC + non-WA + odd cycles); it reproduces the paper's donors
  (361,818) and concentration (39.3/72.3/0.800) exactly, so the same-population $646M stands.
  The verifier now applies it (WA outflow divergence resolved above).

**Verifier full re-run — DONE 2026-07-10.** All six `verify_*.py` re-run, **exit 0,
reproduce** derived-vs-paper. **WA outflow concentration reconciled** (the last
divergence): the paper's filter (`fec_candidate_id ~ '^[CPHS][0-9]'` +
`contributor_state='WA'`) yields 361,818 / 39.3% / 72.3% / 0.800 exactly; NY tightened to
671,488, TX unchanged. Only remaining self-flagged note is NY §III/§IV rate cuts ~1–2pp
under (current-roll denominator; composition cuts match exactly). Lead-paper PDF
re-rendered (`docs/who-decides-washington.pdf`).

**Still to check:**
- [x] Match precision — hand-rated 2026-07-10 (2 rounds): **≈90%** (15/150 flagged on the
  second pass; spousal/household false-merges dominant, some unverifiable). Folded into
  donor-class *Boundary of inference*; filled CSV in `data/validation/` (gitignored).


**Donor paper — New York state panel (added 2026-07-26).** NYSBOE publishes
transaction-level contributions (data.ny.gov `4j2b-6a2j`, 12.6M rows) carrying
contributor last/first name and ZIP; the repo's NY adapter read that feed but kept only
roll-up columns, which is why NY had no state donor panel. `scripts/load_ny_contributions.py`
now loads the per-contribution rows (Individual contributors, Schedule A, cycles
2018-2026): **3,954,090 contributions / $880.3M**, of which **$379.5M** matches a
registered voter.

| # | Claim | Expected |
|---|---|---|
| 41 | NY state contributions loaded | 3,954,090 rows / $880.3M, 9 cycles 2018-2026 |
| 42 | NY state matched layer | 424,020 donors / $379.5M / top-1% 48.5% / Gini 0.846 — **all-tier build as loaded; superseded by the primary spec (378,383 / $339.8M / 48.6% / 0.845)** |
| 43 | NY state age bands | 4.9 / 17.8 / 38.9 / 38.4 (65+ 38.4% vs 47.9% federal) — **all-tier; superseded, primary spec reads 65+ 39.3% state vs 49.9% federal** |
| 44 | NY state own-party skew | DEM +8.9 / REP +3.2 / NOPARTY -12.0 (vs federal +15.0 / -0.9 / -13.0) — **all-records baseline; superseded by #60's active-only figures** |
| 45 | NY state geography | Manhattan 20.6% (vs 50.3% federal), Nassau 15.1%, Suffolk 11.1%; top-3 ZIP3 38.1% — **all-tier; superseded by #97** |
| 46 | NY state give<->vote | 3.02 generals / 73.1% super vs 1.77 / 36.8% — **all-records denominator; superseded by #62's active-only figures** |

| 47 | NY state crossover (after backfill) | resolution 25.9% -> **37.7%**; DEM 88.3->D, REP 84.7->R, NOPARTY 54.8->D |

> NY state crossover is the thinnest cut in the paper at **37.7%** resolution
> (`backfill_ny_recipient_party.py`). Stability check: lifting coverage from 25.9% to
> 37.7% moved the rates by 1.0 / 4.5 / -2.1 points, so directions hold but magnitudes are
> approximate. A bare-surname tier was built and REJECTED (it read "FRIENDS OF DAVID
> KNAPP" as Republican via *David*) — do not reinstate it. Corporate/labor PACs stay
> unresolved by design.


---

**"Does Money Move Votes in Washington?" (`does-money-move-votes.md`, drafted 2026-07-26)**

No dedicated verifier: this paper reports a *null* and a *data ceiling*, so the thing to
re-derive is that the tests come back empty and that the IE script still refuses to
infer. Run the three diagnostics and check the numbers below.

```bash
python scripts/diag_overperformance_patterns.py   # Finding 1
python scripts/diag_expenditures_vs_residual.py   # Finding 2a
python scripts/diag_ie_vs_margin.py               # Findings 2c + 3
```

| # | Claim | Expected |
|---|---|---|
| 48 | Fundraising is the strongest correlate of overperformance | r = +0.55 (incumbency +0.43, quality +0.34, local trend +0.32) |
| 49 | Monotonic by funding side | D out-raised +4.20 / even +2.37 / R out-raised -1.93 |
| 50 | Allocation shares carry no signal | field +0.02, media +0.05, professional -0.03; total spend +0.26 (scale, not mix) |
| 51 | Cross-cycle holdout (fit 2022 -> predict 2024) | core 0.000 / +field 0.006 / +all shares 0.018 / shares alone 0.041 (r=-0.20, wrong-signed); in-sample 0.049 -> 0.144 = overfit |
| 52 | IE cross-section runs negative | slope -0.39 pp per $1M net pro-D IE, Pearson r = -0.39, n = 7 |
| 53 | WA-03 2024, the saturation case | $40.08M total IE, +$16.18M net pro-D, residual +0.06 pp |
| 54 | The data ceiling | directional IE = FEC Schedule-E 2024 only, 7 scorable WA races; PDC's $70.6M legislative IE has a NULL support/oppose flag |
| 55 | Party attribution is complete | $0.00M of $53.94M unresolvable, so the negative slope is not a coding artifact |

> The IE script **withholds inference below 10 scorable races** and prints its data-ceiling
> notice instead. That behavior is deliberate — at n=7 the sign flips on one race. If a
> Schedule-E backfill (2018/2020/2022) later lifts n past the threshold, the script will
> start reporting a slope; treat that as a NEW result requiring its own review, not as
> confirmation of the descriptive number above.

---

**"Safe-Seat Washington" — REBUILT 2026-07-27 after adversarial review.**

Claims 11/12 above are SUPERSEDED. The prior figures came from a seat universe derived
from `precinct_results`, which silently dropped 24 King County House seats per cycle in
2016 and 2018 (King is largely absent from WA's statewide PRECINCT files those years) plus
2020 LD15 on a race-name format variant. The universe is now built from certified
statewide summary returns and asserted against the statutory chamber size.

```bash
python scripts/diag_seat_competition.py    # exit 0 == all cycles reconcile to 98 House / 10 US House
```

| # | Claim | Expected |
|---|---|---|
| 56 | Universe reconciles every cycle | 2016 98/26/10=134; 2018 98/25/10=133; 2020 98/26/10=134; 2022 98/25/10=133; 2024 98/25/10=133 |
| 57 | D1 not-close share by year | 88.1 / 78.9 / 83.6 / 86.5 / 83.5% (2016-2024) |
| 58 | D2 no-D-v-R share by year | 48.5 / 27.1 / **26.9** / 35.3 / 35.3% (2020 corrected 2026-07-28) |
| 59 | WA 2024 detail | 133 seats; 111 not close; 47 without D-v-R = 23 single + 15 same-party + 9 major-v-minor |
| 60 | Safe-seat party split, by WINNER not vote totals | 68 D / 43 R (was 69/44 under the old rule) |
| 61 | The one close same-party general | WA CD-4 2024, R-v-R, 6.0-point margin (Newhouse) |
| 62 | Four-state lower chamber, not close | WA 87.8 (98/98) / NY 88.6 (149/150) / TX 94.0 (96/150 + 54 backfill) / ID 92.9 (70/70) |
| 63 | Party-string sensitivity on no-D-v-R | strict vs loose differs 3.0pp in 2016, **<=1.5pp** elsewhere (deltas computed unrounded) |

> **Changes from the prior published figures** (paper Appendix G): 2016 90.7 -> 88.1;
> **2018 75.0 -> 78.9**; 2020 84.1 -> 83.6; 2022 87.1 -> 86.5; **2024 85.0 -> 83.5**. The
> 2018 "blue-wave dip" was materially exaggerated by the missing King County seats, which
> are disproportionately safe and Democratic.
>
> **Withdrawn claims:** that seats were "decided before November" (observed November
> margins cannot date the binding decision); and that the safe-seat/vote gap is a "packing
> signature" (now descriptive, consistent with several mechanisms). The forecast comparison
> is relabelled a loose aggregate consistency check, not a validation.
>
> **The four items above were closed 2026-07-27.** Appendix E recomputed (WA rows now share
> the headline code path; contest gap +8.2pp). NY's missing seat identified as **AD-23**,
> effect bounded to 88.0-88.7%. Primary/general ratio recomputed: 51.2% (2024) / 61.2%
> (2022), confirming the published figures. Texas district-level audit built
> (`diag_tx_backfill_verification.py`).
>
> | # | Claim | Expected |
> |---|---|---|
> | 64 | Threshold table, WA all seats 2024 | 92.5 / 88.0 / 83.5 / 77.4 / 73.7% at >=5/8/10/12/15pt |
> | 65 | Threshold table, WA House 2024 | 95.9 / 91.8 / 87.8 / 80.6 / 76.5% |
> | 66 | Contest gap | WA +8.2pp (87.8 vs 79.6); TX +10.0; ID -1.4 |
> | 67 | NY missing seat | Assembly District 23; bound 88.0-88.7% |
> | 68 | Primary/general median ratio | 42.1 / 55.9 / **61.5** / 61.2 / 51.2% (2016-2024); **`diag_seat_competition.py`**, which also asserts every seat matched |
> | 69 | TX backfill verification coverage | **all 54 verified** against certified returns — exactly the 54 the TLC omits, no extras, none missed |
> | 70 | TX imputed party ERROR RATE | wrong in **5 of 54** (HD 35/36/40/42/**144**); observed backfill split 36 D / 18 R vs 31 D / 23 R imputed |
>
> **Claims 69 and 70 were superseded 2026-07-27 by the certified-source build**
> (`build_tx_house_candidates.py` -> `data/raw/tx/2024_tx_house_candidates.csv`), which
> covers all 150 districts. The earlier "14 press-confirmed / 4-of-14 wrong" values came
> from the partial press cross-check that preceded it; do not sign off against them. Holding
> party is now OBSERVED, so the quotable chamber split is **56 D / 85 R** (not-close seats)
> and **62 D / 88 R** (whole chamber, matching the seated House). The **51 D / 90 R
> imputation must not be quoted** anywhere, including in the Appendix E seat/vote gap, which
> was recomputed on observed party (TX +6.9 -> **+3.3**). The non-competitive count (94.0%)
> was never affected: it needs only that the seats were uncontested, not who held them.
>
> **Second internal pass, 2026-07-28 — five figures corrected, one derivation added.**
> The paper was audited against its own scripts rather than its argument. No headline moved.
>
> | # | Claim | Expected |
> |---|---|---|
> | 71 | D2 no-D-v-R share, **2020** | **26.9%** (not 27.6%) — D-v-R 98, R-v-other 4; loose delta 1.5 |
> | 72 | The 2020 misspelled party string | `(Prefers Democractic Party)`, LD-8 Pos. 1 (Regev vs Klippert) normalized to major D in BOTH specs; `SOURCE_MISSPELLINGS` in `diag_seat_competition.py` |
> | 73 | Threshold table, NY >=12pt | **85.9%** (not 85.2%) |
> | 74 | Appendix E seat/vote gaps | WA **+2.1** (House, 53/33) or **+1.8** (all seats, 68/43) vs 59.5% pres; TX **+3.3** (observed 56/85); ID +18.9 |
> | 75 | Cross-state definition check | 0 no-major-choice seats under 10pt top-two margin in NY (0/48), TX (0/61), ID (0/20) — four-state column identical under either rule; `diag_safe_seat_robustness.py` section 3 |
> | 76 | Superseded script cells, labelled not deleted | `diag_safe_seat_states.py` prints WA 88.8% + TX 51/90 with SUPERSEDED markers; authoritative WA = 87.8% from `diag_seat_competition.py` |
>
> **Claim 72 is the one to re-check after any certified-file reload.** A misspelling in the
> source silently defeated the party matcher and turned a genuine D-vs-R general into a
> no-choice seat. `diag_seat_competition.py` now prints every normalization it applies under
> the universe table — if that line changes, a new source typo has appeared and the affected
> cycle's Dimension 2 figure must be rechecked before publication.
>
> **CLOSED 2026-07-27.** The Texas backfill is now verified against the Secretary of
> State's certified election-night results (`build_tx_house_candidates.py` ->
> `data/raw/tx/2024_tx_house_candidates.csv`). Its 54 single-candidate districts are
> EXACTLY the 54 the TLC omits, so every backfilled seat is externally confirmed; holding
> party is observed rather than imputed.
>
> | # | Claim | Expected |
> |---|---|---|
> | 71 | Certified source covers the chamber | 150 districts; 54 single-candidate |
> | 72 | Backfill set matches certified uncontested set | exact match, 0 extra / 0 missed |
> | 73 | Retired imputation error rate | wrong in **5 of 54** (HD 35/36/40/42/144, all D-held seats Trump carried) |
> | 74 | Backfilled seats, observed party | **36 D / 18 R** (imputation said 31 D / 23 R) |
> | 75 | TX not-close, certified | 141/150 = **94.0%** — unchanged from the backfilled figure |
> | 76 | TX not-close split, corrected | **56 D / 85 R** (was 51 D / 90 R) |
> | 77 | External sanity check | certified chamber 62 D / 88 R matches the seated 2024 TX House |
>
> Also established: the TLC dataset omits uncontested races at EVERY stage — all 14
> press-confirmed unopposed districts appear in neither 2024 primary — so no work inside
> that source could have distinguished "uncontested" from "missing".




---

## 7. Adversarial review log

**2026-07-27 — cross-paper consistency pass.** Attacked the papers as a hostile reviewer
would: not re-deriving each headline (§1 does that) but hunting for figures that
**contradict each other across documents**, claims **stronger than the data now supports**,
and **base/denominator mismatches**. Everything below was found by recomputing from the
databases, and all of it is fixed.

The dominant finding is one failure mode, not eight unrelated slips. The
primary-specification switch rebuilt every panel *and* the three pooled tables. The
donor-class paper and the WA-facing cuts were updated; **the NY and ID cuts in the
downstream documents were not.** Because a partial update leaves plausible-looking
numbers, nothing failed loudly.

| # | Document | Defect | Resolution |
|---|---|---|---|
| R1 | `cross-state-fec-money.md` §F5 | The whole generation table disagreed with the script it cites — NY Silent read 1.87× against an actual **1.50×** | Table replaced with the script's current output |
| R2 | §F5 claim 1 | Claimed Silent "~1.9–2.0×" and a gradient "essentially identical" across states. Actual range **1.50–2.08×**; gradient ~21× in WA/ID but **~11× in NY** | Range corrected; "essentially identical" **withdrawn** |
| R3 | §F5 | Called the Idaho cut "the **FEC** voter↔donor match" — it is the **pooled** match (41,136, not 23,303) | Relabelled; the same mislabel fixed in `who-decides-idaho.md` |
| R4 | §F6 | NY and ID rows still on pre-switch matches (308.0K / 47.8K); "tight **1.62–1.76×** band" | Rows recomputed (**1.66–1.85×**); "tight" withdrawn |
| R5 | §F4 | Match-precision bullet described the unadjudicated 150-record sample as pending human review — superseded by the 480-record blinded study, and those verdicts were never retained | Replaced with the tier-resolved result (full-name key **100%**, weighted **93.0%**) |
| R6 | **`donor-class-and-the-electorate.md`** crossover tables | **Federal blocks primary-spec, state blocks all-tier, in the same table** — inviting precisely the federal-vs-state comparison that mismatch corrupts | Both state blocks recomputed; rows now sum to 378,383 / 23,613 |
| R7 | Same section, footnote | "Aggregate resolution: NY federal 87.8%, ID federal 86.7%" — both are the **Republican row's** rate, read off the wrong cell. Aggregates are **88.8%** / **87.6%** | Corrected, with the cause stated |
| R8 | Same section, prose | Prose disagreed with its own adjacent tables (90.1/79.2 vs 91.1/80.1; 94.4% vs 95.3%; ID unaffiliated "3:1" vs **3.8:1**; ID $-to-D 71.9% vs **77.7%**) | Prose reconciled to the tables |
| R9 | `electoral-health-whitepaper.md` Finding 5 | **Self-contradictory**: federal top-1% given as 41.2% in the panel note and **42.4%** two bullets later; Gen Z as 0.18× in one bullet and 0.09× in another | Both resolved to the verified values; stale CI [40.2–44.9] → **[38.6–43.4]** |
| R10 | Whitepaper Findings 2 & 4 | WA four-state cell still **88.8%** (dropped-King-County universe); ratio 1.68× and propensity 0.953 stale; "no major-party choice" treated as automatically non-competitive — the conflation the safe-seat rewrite removed | Corrected to **87.8%** / **1.72×** / **0.967**; two-dimension distinction restored |
| R11 | `who-decides-idaho.md` §VII | Spec-dependent age and party claims carried no selection caveat, though the restriction discards 11–19% of donors who are **younger and less Democratic** | Caveat added where the findings are read, not in a methods note |

**Checked and found clean:** the lead WA paper (all cells verify, and its bounding /
imputation / geography sensitivity sections are intact); the safe-seat paper (rebuilt and
reconciling to statutory chamber size every cycle); the donor paper's own all-tier
references, which are **all** explicitly labelled "all tiers" / "all matched" / "superseded"
in sensitivity tables — that paper never mixed specifications in its own prose, which is why
R6 stood out.

**Reviewer's note on what this says about the process.** Every defect above is a
*propagation* failure, not an analysis error: the recomputations were right, and the
documents downstream of them were not revisited.

**Both gaps are now closed by machine checks (2026-07-27).**

- `verify_donor_class.py` — 47 hard-failing assertions over Idaho §VII.
- `verify_cross_state_money.py` — 88 hard-failing assertions over §F5/§F6: every cell of
  the generation table (raw *and* IPW), the pooled donor counts, Gini, the party-of-record
  skew, and the full F6 table. The script previously had no exit code at all; it now
  returns non-zero. Its OUTFLOW/INFLOW blocks stay advisory by design — their name+zip
  donor key carries documented sub-0.5pt grouping drift, so asserting them would be noise.

**The F5/F6 checks assert the derived CLAIMS, not only the cells**, because R2 and R4 were
sentences that stayed wrong while their tables were being fixed: the cross-state range of
the Silent and Gen Z ratios, the maximum raw-vs-IPW shift, each state's old-to-young
gradient, and the F6 ratio band. There is also a guard that re-raises the withdrawn
"essentially identical" claim if the gradients ever converge within 1.5×, so the withdrawal
is revisited on evidence rather than forgotten.

Each check was negative-tested by reinstating the actual defect: the stale NY Silent 1.87×
cell, the pre-switch ID pooled count 47,762, the withdrawn "~1.9–2.0× / ~0.13–0.18×" range,
and the withdrawn "tight 1.62–1.76×" band all fail the run. Building the checks also caught
one more, unrelated to the tier switch: **Idaho's pooled Gini is 0.821450, and the paper's
0.822 was a double-rounding of the diagnostic's 4-decimal 0.8215.** Corrected to 0.821.

**The whitepaper gap is now closed too (`verify_whitepaper.py`).** It is built differently
on purpose. Findings 4 and 5 do not compute anything — they *restate* figures from the
donor-class and cross-state papers, and their two observed failure modes were drift from
those sources and **self-contradiction** (the federal top-1% given as 41.2% in a panel note
and 42.4% four lines later). A constants table cannot catch either, because it never reads
the prose: the sentence can be edited while the constant stays right. So this verifier
**scrapes the prose** — each probe is a regex anchored on the surrounding words, and every
occurrence of a figure must equal the derived value, so a number stated twice is checked
twice. **An anchor that matches nothing is a failure, not a skip**, because rewording a
sentence out from under a check is itself the thing to catch.

Negative-tested against all three modes: reinstating the 42.4% contradiction, deleting the
figure from a sentence, and a single stale digit each fail the run. Two things are listed
in the script's `UNCHECKED` rather than quietly omitted — the bootstrap CIs (B=1,000, too
slow) and the occupation blocs (an outflow-side cut).

Building it caught three more, all now fixed:

| # | Where | Defect |
|---|---|---|
| R12 | `cross-state-fec-money.md` §F2 | Raw multipliers gave Millennial **0.59×** and Gen Z **0.17×** against 0.54× / 0.09× — and **contradicted the "Gen Z 0.09→0.09×" in the same bullet**. Missed by the first review pass, which read F5's table but not F2's sentence |
| R13 | §F2 + whitepaper Finding 5 | P(matchable) published as 68.9%–73.1%; the roll has since grown and it is **69.1%–73.3%**. Not a tier-switch defect — ordinary drift in a figure nothing was watching |
| R14 | — | My own first derivation of NY's 65+ donor share read 54.6% against a published 49.9%, because NY publishes age **as of the 2024 general** and I measured at 2026. The published figure was right; the check was wrong. Recorded because a verifier that silently adopts the wrong basis is worse than no verifier |

**The last three were wired in the same day**, so `UNCHECKED` is now down to items that
cannot be re-derived here rather than items nobody got to:

- **Bootstrap CIs.** My earlier note called B=1,000 "too slow for a verifier". That was
  simply wrong — the whole block runs in ~35s. Because
  `diag_donor_concentration_bootstrap.py` fixes its seed, the published intervals are
  *exactly* reproducible, so they are asserted at full precision instead of with a
  Monte-Carlo slack. One caveat is now recorded in the code: a single RNG is threaded
  through federal → state → inflow in sequence, so **the panel order is load-bearing** and
  reordering them silently changes every interval.
- **Finding 6**, in two halves. Its data-ceiling facts — scorable-race count, WA-03's IE
  dollars, the $70.6M of PDC IE carrying no support/oppose flag — are re-derived from
  scratch, and by the paper's own argument those *are* the citable result. Its slope and
  Pearson r are not re-derived: they regress a fundamentals-net residual only the forecast
  model produces, and reimplementing it here would fork the model rather than check it.
  They are instead asserted against `does-money-move-votes.md`, the paper that owns them.
  That is a consistency check, labelled as such — and it immediately earned its keep.
- **The occupation blocs**, which I had listed as out of scope and which turned out to be
  the most substantive find of the three.

| # | Where | Defect |
|---|---|---|
| R15 | whitepaper Finding 6 | Slope and r read **−0.42 / −0.43** against `does-money-move-votes.md`'s correct **−0.39 / −0.39**. The white paper had drifted from the paper it summarises — the exact failure this verifier was built for, found the moment it was pointed at Finding 6 |
| R16 | whitepaper Finding 5 | The occupation blocs (RETIRED, NOT EMPLOYED) were computed on the **unfiltered pooled** contributions table — FEC + state PDC + non-resident donors, $1,050.8M — inside a finding whose every other figure is panel-scoped. **The same two-money-system pooling this series corrected everywhere else, still sitting in the white paper.** Restated on the documented outflow basis (FEC, WA-resident, $646.2M): RETIRED **$154.0M / 23.8%**, NOT EMPLOYED **$128.8M / 19.9%** — both a *larger* share, so the point sharpens |

Remaining in `UNCHECKED`, and each for a stated reason rather than convenience: Finding 6's
slope/r (cross-checked, not re-derived) and Findings 1-3 (prospectus items whose realized
analyses are verified by `verify_who_decides_wa.py` and `diag_seat_competition.py`).

### Round 4 (2026-07-28) — the donor paper's prose, scraped

`verify_donor_class.py` held every published figure as a Python constant and never opened
the paper, so it could only catch DATA drift. Rebuilt in the `verify_whitepaper.py` idiom:
it now scrapes the paper's own prose and tables and asserts **309 figures**, with a
missing anchor counted as a failure so that rewording a sentence out from under a check
trips it. The first run failed 52 of them.

The pattern is one thing, not eight: **the 2026-07-27 tier switch rebuilt every panel and
every table, and left the prose behind.** Each defect below was confirmed by reproducing the
published number exactly on the retained `_alltier` snapshot — so these were provably
stale figures, not basis disagreements. Every table in the paper was already correct, which
is why an eyeball pass sustained them: each stale sentence sat inches beneath a table that
contradicted it.

| # | Where | Defect |
|---|---|---|
| R17 | donor paper F1 prose | NY state 65+ read **38.4%** against its own table's 39.3%; Idaho's under-30 pair **1.4% / 2.6%** against 0.5% / 2.1%; WA's Gen X / Millennial panel comparison **1.26× / 0.68× / 0.39×** against 1.31× / 0.61× / 0.35×. The "roughly twice" claim attached to the last was false at the corrected values (1.34×) and was withdrawn |
| R18 | donor paper F1 prose | All **nine** within-person overlap shares stale (WA 31.3/51.3/57.5 → 32.9/53.6/59.6; NY and ID likewise) — while **Appendix C's table carried the right ones**. Two statements of the same cut, disagreeing, in one paper |
| R19 | donor paper F3 prose | The Democratic skew had silently reverted to the **all-records baseline** (+15 points, 71% of dollars) inside a paper whose tables and source note both specify the **active-registrant** baseline (+16.1, 72.5%); REP's panel move read −1.2 → +2.8 against −1.1 → +3.2. "Falls by a third" also understated a 40% fall |
| R20 | donor paper F4 + Appendix E | F4's entire WA and NY **donor-side** block was pre-switch (WA 85.5/84.9% super-voters vs 88.0/88.9%; NY 3.00/72.9% vs 3.10/75.7%) — and **Appendix E's turnout table already had the correct values**, so the two contradicted each other. The non-donor figures matched, which is the tell: only panel membership changed. Two derived claims broke with them — "within a tenth of a point" (now 0.4) and "116,000 more people" (109,165) |
| R21 | donor paper Appendix E geography | The whole table stale (WA ZIP3s, Manhattan **50.3%** vs 48.5%, Ada **49.2%**/10,037 vs 50.3%/8,812), and the ordering had flipped: **Bonneville 11.9% now exceeds Blaine 11.4%**, so the prose's "above all resort-county Blaine" was wrong about which county leads, not just by how much |
| R22 | donor paper Appendix E + F3 subsection | The NY competitiveness bands were computed on the **POOLED** match (`diag_ny_electorate_extras.py` reads `voter_donor_affiliation`) — the two-money-system pooling this series corrected everywhere else, exactly as R16 found in the white paper — and were stated **twice**, in Appendix E and in Finding 3's subsection, both on 205K of 308K. Recomputed per panel; the finding *strengthens* (the D share now exceeds registration in every band in **both** panels). Idaho's district-safety sentence was likewise on the retired unbanded ~71% figure while `who-decides-idaho.md` had been rebuilt to 78%/13% |
| R23 | donor paper header | The Idaho period-aligned gap read **67.1% / 51.1%** — the all-tier aligned pair — against the panel-gap paragraph's correct 68.5% / 51.3%, forty lines below it |
| R24 | donor paper NY age table | The all-active-voters column's 30-44 cell read 25.6% against 25.54%, and 65+ read 25.2% against 25.250122%, which rounds to **25.3**. Ordinary last-digit rounding errors, found only because the tolerance was left at the paper's printed precision instead of being widened to make them pass |

**One defect was mine, and it is the one worth recording.** My first derivation of the NY
"all active voters" age column disagreed with the paper on all four cells, and I nearly
reported four defects. The paper was right: its column excludes the ~155K active
pre-registrants under 18 (1.25% of the roll), as an electorate baseline should. The tell was
that only *one* of the table's four columns diverged — the donor columns and the
2024-general column reproduced exactly — and a basis error shows up as a whole-column
offset, not a scattered one. This is R14's lesson a second time: a verifier that silently
adopts the wrong basis is worse than no verifier. The `>= 18` floor and the reasoning are
now comments in `_d_refbands`.

### Post-review work plan, step 1 (2026-07-28/29) — four more claims moved

Not a review round: the reviewer's own recommended revision order, items we chose to build.
Recorded here because the durable ledger is this file, not the commit log. Author decisions
that scoped it: journal-ready restructure targeted at **Election Law Journal**, the reviewer's
title, **counties everywhere** for geography, plan-before-execute on the restructure, and a
fresh full-name-key validation draw. Repro package, Zenodo and submission metadata were
DROPPED as publication mechanics once another review was expected.

| # | Item | Outcome |
|---|---|---|
| S1 | Geography on counties, roll-normalized (`39f37be`) | Two ZIP3s vs single counties was not like-for-like. Rebuilt on counties + a dollar-share/roll-share multiplier, since raw share confuses a LARGE county with a CONCENTRATED one. **NY remains the extreme case only on the multiplier** (Manhattan 5.96x); on raw share WA would lead. **Idaho's "single-metro dominance" WITHDRAWN** — Ada is 1.26x, mostly population; the real concentration is Blaine at **7.83x** (1.5% of roll, 11.4% of federal dollars), so the old framing named the wrong county |
| S2 | Bootstrap all six panels (`39f37be`) | Was WA-only, leaving the paper's most prominent result with uncertainty quantified for a third of the evidence. APPEND-ONLY — one RNG threads the sequence, so inserting a panel would silently move the published WA intervals that `verify_whitepaper.py` asserts; WA verified unchanged to 3dp |
| S3 | Ordering test (`39f37be`) | Bootstrapping the DIFFERENCE (overlapping CIs are not a test) **falsified a Finding 2 claim**: of the NY>WA>ID ordering only NY−WA and NY−ID are separable, and in the STATE panel no pairwise gap is. Interval width tracks n — ID's 23K panels give a ~18pt top-1% interval vs ~5 for WA. Concentration ITSELF is robust everywhere (lowest lower bound 30.7%) |
| S4 | Harmonized $200 floor (`3e0f348`, `diag_panel_harmonized.py`) | Age gap **survives** in all three (+9.8/+11.7/+12.2) but **41% of WA's was the floor**; NY's widens. **Layer-concentration ordering FLIPS in WA and ID** — federal is more concentrated in all three on a common floor, so "does not run one way" was a disclosure artifact. And the both-systems-group "outside the range" claim **fails in Idaho** when harmonized. Costs 60-69% of each state panel vs 26-27% of each federal one |
| S5 | Record-linkage literature (`db0d708`) | The reviewer's "significant omission". Six publisher-verified citations. Concedes three things: a deterministic key moves uncertainty **out of the estimator into the sample definition** (boundable by validation, not propagatable); ADGN is unreachable for **legal** not technical reasons (donor side has no DOB/gender/address); and Bailey et al.'s 15-37% error range with **systematic** error calibrates this paper's own 47.9-71.7% weak tiers and its younger/less-Democratic discard |
| S6 | Ethics determination (`f3af5c7`, `data-use-and-research-ethics-assessment.md`) | Self-assessment, no IRB jurisdiction. Not-human-subjects + 46.104(d)(4) alternative, and **names its own weak point**: "publicly available" fits the FEC file, not the use-restricted voter files. Smallest published cell measured at **44 individuals**. HUMAN to sign; NY FOIL certification and Idaho Code § 74-120 still need WA's statutory treatment |

**Not done, and deliberately:** the restructure. Two consecutive passes moved published numbers,
and re-anchoring 623 assertions twice is avoidable cost — hold it until the next review returns.
Also open from the reviewer's list: the other three literatures (donor composition;
small-donor/itemization selection; concentration and geographic networks), human adjudication of
the fresh sample (sampler is ready: `--seed`, `--tiers`, `--live-panels`, `--exclude-rated`), and
the title change.

**Verifier state after step 1: 623 asserted figures across 20 audited sections.** Two probes had
to be re-pointed mid-step because a rewrite reworded the sentences they anchored on, and the
overlap trap bit twice more (a section nested inside `f2`; a section whose end anchor preceded
its start). Both failure modes are documented in CLAUDE.md.

### Round 5 (2026-07-28) — external reviewer, and the coverage control they demanded

An external reviewer returned **major revision before submission**. Their verdict on the
substance was favourable ("the principal problem is no longer the underlying thesis; it is
manuscript control"), and their central criticism was aimed at round 4's claim: *"Do not
claim that all 309 figures have been verified while obvious stale figures remain. Either
expand the verifier or narrow the claim to exactly what it checks."* That criticism was
correct. Round 4 probed the findings and Appendices C and E; the crossover tables, the
limitations bullet and Appendix A were never in scope, and that is precisely where the
reviewer found four more contradictions.

Every specific defect they named was reproduced and fixed:

| # | Where | Defect |
|---|---|---|
| R25 | Appendix C data-quality bullet | "53 duplicated ids … 378,383 standalone and **424,025** after a roll join" — a 45,642-row expansion 53 duplicates cannot produce. The reviewer's diagnosis was exactly right: 424,020 is the **retired all-tier panel total**, and it had been written as join fan-out. True figure **378,388** (5 rows) |
| R26 | limitations + Appendix A | The crossover section's resolution rates were corrected in round 3 (R7) and the correction was **never propagated**: both still read 87.8% / 86.7% / 51.9% against the corrected **88.8% / 87.6% / 51.1%** |
| R27 | Idaho crossover prose | Quoted **17.6% / 18.8%** D-only against its own table's 17.1% / 19.1% — and 17.6% is the table's *dollar* column, so the prose had also crossed two different quantities. "Within a point and a half" was 2.0 points |
| R28 | Idaho party-skew prose | Unaffiliated skew given as **−11.2 / −11.8** against the table's −12.1 / −12.3 (all-tier leftovers) |
| R29 | Appendix F | Still said the full-name tier **"should be"** primary and described the all-tier figures as those "reported throughout", months after the switch; the methods section still called the full-name results a **"sensitivity"** |
| R30 | Appendix F | Corrupted punctuation throughout — `95.1" –100.0`, `68" –80%`, `NC" → Y` — a stray ASCII quote glued in front of every en dash and arrow in that section |
| R31 | Appendix C alignment table | Washington marked temporally **"aligned"** while the same row reports FEC 2017–2026 against PDC 2016–2026. Only New York is exactly aligned |
| R32 | throughout | Precision language stronger than the evidence: "the full-name key is **clean**", "leaves **essentially no room for error**", precision "at 100%" without the interval. Restated everywhere as *no false match detected in 120 reviewed records; estimated precision 100%, Wilson 95% CI 96.9–100%*, and the human re-rating is now explicitly a re-rating of a **subset** of those 120, not an additional sample |
| R33 | abstract | "The previously published figures were the conservative ones" attributed the whole movement to improved precision. It cannot be: the restriction also discards a younger, less-Democratic 11–19%, so part of the movement is a change in target population |

**The coverage audit — the control, not another round of spot fixes.** `verify_donor_class.py`
now records the character span of every figure it asserts, then audits **sixteen designated
result sections**: any numeric token not covered by an assertion must carry a written
exemption naming where it *is* verified, and the run fails otherwise. Getting it to green
found **four further defects nobody had reported**, which is the point of building it:

| # | Where | Defect |
|---|---|---|
| R34 | Finding 3, Idaho dollar shares | 68.1 / 71.1 / 21.1 / 20.6 / 10.3 / 8.0 all reproduce exactly on the **all-tier** panels; primary spec reads 68.5 / 72.2 / 21.8 / 20.0 / 9.3 / 7.6 |
| R35 | Finding 3, Idaho aligned panel | Aligned-panel Democratic and unaffiliated figures stale (21.4/+9.6, 11.7/−12.2 against 21.9/+10.1, 11.1/−12.7) |
| R36 | withdrawn-"3.6×" note | Its quartet (14.2 / 3.9 / 20.2 / 5.5) was the **all-tier** panel's, inside the paragraph explaining why an earlier figure was withdrawn |
| R37 | Appendix C overlap prose | "which the **0.140** Jaccard contradicts" against the table's 0.141 |

Coverage is now **508 asserted figures** plus a written exemption for every remaining token.
Sections deliberately **outside** the audit, and now said so in the paper rather than implied:
Appendices A, B, D, F and G, whose numbers come from the frozen validation ledgers and the
statutory sources rather than from the panels. Three of my own bugs surfaced while building
it and are recorded because each would have produced a false clean bill of health: coverage
tested containment instead of overlap (reporting every probed table cell as unmapped),
`f3_money` overlapped the crossover slices (165 false positives), and `xover_id`'s end anchor
preceded its start anchor so the slice ran to the end of the document (629 false positives).

**The estimator objection, measured rather than argued.** The reviewer is right that
`NTILE(100)` yields approximately rather than exactly 1% and breaks ties arbitrarily.
Quantified against an exact donor-weight cutoff with fractional boundary weighting: the
top-1% figures move **−0.001 to −0.046 points**, largest in Idaho where n is smallest, and
below the printed precision in all six panels; 1 to 26 donors share the boundary value. So
the published figures stand, Appendix C now documents both properties and the measured
agreement, and the verifier **fails** if any panel's two estimators ever diverge by more
than 0.05 points. Not done: bootstrap intervals for all six panels (only Washington's two are
bootstrapped today) — see the open items below.

Also corrected while re-reading rather than carried over: Appendix A's objection 1 quoted the
IPW result's **47.9%** with no note that it is an all-tier figure, so a referee reading that
appendix alone would see it contradict the abstract's 49.9%. Finding 1 already carried the
caveat; Appendix A now does too. And `ny-electorate-extras.md`, the supporting write-up,
still reports the pooled all-tier donor cuts — retained as the record of what that script
outputs, but now headed with a warning not to quote it.

### Round 6 (2026-07-29) — external reviewer #2, and two overclaims in the *new* work

The same reviewer returned **major revision, "but the paper is now substantially closer to
submission."** They credited round 5 with substantially fixing the numerical-control problem,
disciplining the match-validation language, repairing the geography, and correcting the
Washington threshold history and the contribution-limit appendix; they spot-checked the NYSBOE
limits independently and found them supported. Their standing judgment moved to *working
paper — nearly ready after targeted corrections; journal — not yet.*

**The lesson of this round: two of their six substantive hits landed on analyses round 5
added.** The common-$200 cut and the six-panel bootstrap were both introduced *in response to
review* and both were described more strongly than their designs permitted. New work is where
new overclaiming appears, and a verifier that checks arithmetic cannot see it — the coverage
audit passed clean on both while the *interpretation* of each was wrong.

| # | Defect | Fix |
|---|---|---|
| R51 | The common-$200 cut was said to "test disclosure thresholds directly", show the amount "attributable to the floor", and establish that 41% of WA's age gap "was" the threshold. It cuts on a donor's total **across the assembled panel**, while itemization duties attach per committee, cycle and reporting period — so a $50-to-five-committees donor clears it without crossing any threshold, and committees itemize below the floor anyway | Relabelled a **common donor-total restriction** at all four use sites; the four confounded mechanisms enumerated in Appendix C; what a real statutory simulation needs, stated and declared not run |
| R52 | Bootstrap differences called "separable from zero", which asserts sampling inference over what are (subject to linkage and disclosure limits) **complete constructed panels** — and the intervals exclude every error source that actually dominates this study | Recast as a donor-**resampling stability** exercise; the six excluded error sources named at both use sites, with the note that each is plausibly larger than the interval width |
| R53 | Finding 3's party result was unadjusted for age, while Finding 1's headline is that donors are far older | Age standardization added — and **it destroyed one published claim**: Idaho's federal Republican over-representation is 103.3% age composition (+4.2 → −0.1) and is withdrawn. Democratic over-representation survives intact (+15.9 → +16.5 NY, +8.6 → +8.4 ID); unaffiliated under-representation survives at −8.1 to −11.5 |
| R54 | Finding 4's turnout gap was unadjusted for age or registration tenure | Age and joint age × tenure standardization; raw +35.8 to +42.8 falls to +20.8 to +24.7. **Found a defect of our own in the process:** WA's `voter_scores.is_super_voter` requires ≥8 years' registration *inside its definition*, so it cannot carry a tenure adjustment and is not measure-comparable with NY's 3-of-4 count. Disclosed in Finding 4; WA rows use a tenure-free substitute (both 2022 and 2024 generals — the only two in the VRDB's rolling window) |
| R55 | "Principal crossover patterns are stable in both panels and both states" and the unresolved pool "cannot plausibly reverse them" — with 54–73% of some state rows unresolved | Worst-case bound added, assigning **every** unresolved donor to the side that would overturn the row. Every headline **federal** row survives; every **state** row but Idaho's registered Democrats fails. Federal is now the primary evidence; state is "suggestive among resolved recipients"; the sentence is withdrawn |
| R56 | Itemized-only concentration called a mathematical **upper bound** on concentration among all givers | Not a bound — adding donors moves the top-1% *cutoff* as well as the denominator. Both statements now say the direction is expected, not bounded, and name what a real bound would require |
| R57 | Four linkage overstatements: "accepts only pairs a probabilistic model would score at or near certainty"; probability propagation as universal practice; Lahiri–Larsen "not required" because the estimands are descriptive; "precision is entirely a function of match tier"; "confirmed from both directions" | All five reworded. The Lahiri–Larsen one was conceptually wrong, not merely strong: linkage error biases shares, means and concentration measures too. The appendix now concedes that and says what this design does instead |
| R58 | Household sensitivity ran only on the retired `_alltier` snapshots | Run on the primary panels. Conclusion holds and the **age finding strengthens** — the senior share rises in all six panels under the surname+ZIP5 exclusion, by up to 7.6 points |
| R59 | The concentration table's donor count implied it was the estimator's denominator | Five of six panels match; **WA state has 382 non-positive totals (0.176%)**, so its concentration runs on 216,732. Footnoted at the table and probed |
| R60 | Eight specific corrections: unclosed quotation at the withdrawn 3.6× note; "contributions below a threshold are reported only in aggregate" contradicting the below-floor itemization finding one subsection later; "both specifications are reported throughout"; WA/NY described as covering the "same years" (FEC 2017–2026 vs PDC 2016–2026); NY cycle labels vs transaction dates; Idaho as "the decisive test"; the Republican primary "decisive in nearly every seat"; and influence language ("actual influence", "setting the financial terms of every race") | All corrected. Finding 4 retitled so it no longer claims influence |

Abstract cut from ~430 to ~290 words. The Grumbach/Sahn/Staszak correction was checked and
cited (*Political Behavior* 43 (2021): 905) — it repairs a mangled character string and
changes no result, and the paper says so rather than implying it mattered.

**Verifier: 623 → 804 figures**, coverage clean across all 20 result sections. Three anchors
broke on rewording and were repaired, which is the control working as intended. Two new traps
recorded: `matched` cannot be a DuckDB column alias (parser error, same class as `rows` and
`returning`), and the paper's U+2212 minus sign is not `float()`-parseable, so the comparator
normalises it rather than forcing ASCII hyphens into typeset tables.

**Left open, deliberately.** Their item 7 — reduce the manuscript and add a formal
bibliography. The paper is ~26,700 words and *grew* during this pass. The mechanism is a
companion methods-and-provenance supplement, since the reviewer explicitly allows that
material to live in the repository. Not attempted here: it re-anchors all 802 assertions, and
a third review is expected. Their item 8 — archival DOI and the two open ethics items — is
the author's.

### Round 7 (2026-07-29) — external reviewer #3, and the appendix that sat outside the audit

**Verdict: targeted major revision, not another redesign.** The reviewer accepted every round-6
correction and stopped asking for new robustness sections: *"The core results no longer need
another state, a different matching architecture, or a wholesale redesign."* They also stopped
treating manuscript length as a defect. Four required actions, all completed.

**The lesson of this round.** Round 6 added Appendix G's derived tables to the paper's evidence
base but left the appendix **outside the coverage audit** — and that is exactly where the
reviewer found this round's largest methodological defect. Same lesson as round 5's crossover
tables, learned twice. Appendix G's derived tables are now audited (23 sections, up from 20).

| # | Defect | Fix |
|---|---|---|
| R61 | The party incidence table divides by *all* registrants of a party, confounding donation behavior with the chance a party's registrants are uniquely matchable — parties differ in surname and ZIP concentration | Measured. **P(matchable) spread across parties is 1.0 pt (NY) and 0.8 pt (ID)** — ~1.01× against incidence ratios of 1.05–1.73×, two orders of magnitude too small. Re-basing on matchable registrants raises every figure 3–4% and changes no ordering |
| R62 | Age standardization does not show the party result is independent of Manhattan or Ada County, since giving is geographically concentrated and party registration geographically structured | Incidence standardized on the joint **age × county** stratum. Ordering survives in all four panels (NY fed DEM 27.8 / REP 19.8 / blank 12.1; ID fed 35.1 / 23.0 / 12.5). Idaho's DEM÷REP ratio 1.62/1.73 raw → **1.53/1.56 adjusted**; the raw ones are now labelled raw and the adjusted ones are the figures to cite |
| R63 | The five tenure bands are too coarse for the outcome: a 2–5-year band mixes registrants who could have voted in three of four elections with registrants who could have voted in one | Redone by **restricting to registrants who existed before the first election in the window**, which equalizes opportunity by construction. **It moves the adjusted gap UP** — +25.1 to +29.3 against the tenure-band +20.8 to +24.7 — so the broad bands were over-adjusting. Also reported as voted ÷ eligible (donors 82.8–96.1% against non-donors 58.5–67.7%). `registration_date` semantics disclosed: neither state documents it as immune to a county transfer, so a mover reads as short-tenure |
| R64 | Appendix G clips each **transaction**, but a statutory limit caps a donor's **aggregate** giving to one committee **per election**; and the FEC file pools recipient types governed by different limits. So "cycle-specific federal limit (historically exact)" is wrong, an "Idaho legislative cap" applied to WA federal transactions is not Idaho law, the $1,000 bunching does not prove a binding legislative cap, and "13.3 points above what pure truncation predicts" does not follow | **Cannot be rebuilt exactly** — neither recipient type nor election designation is persisted (`fec_candidate_id` holds the committee id). Took the reviewer's stated fallback: relabelled a **stylized transaction-clipping exercise**, all statutory labels removed, all four derived claims withdrawn. One real improvement added: a **donor × committee × cycle aggregate** variant, which bites **2.1–4.3 points harder** than per-transaction clipping |
| R65 | "holding the donor population approximately fixed" — with Jaccard 0.14–0.16 | Withdrawn. The design holds the **state** broadly fixed; the panels are predominantly different people |
| R66 | G3 concludes the capped layer is more concentrated in "both" states while combining Idaho's persons-only comparison with Washington's all-filer one | Narrowed: Idaho supports a like-for-like persons-only comparison (39.7% vs 36.1%); **Washington does not** (44.4% all-filer vs 39.3% persons-only). Same direction, not equal evidence |
| R67 | Appendix F reports WA's all-tier state panel as 269,204 in two tables and 268,741 in a third, with no denominator qualification | **A labelling gap, not a stale figure.** 269,204 is rows; 268,741 is donors with a positive total — the all-tier analogue of the 382 disclosed at Finding 2. Difference 463; no other panel differs. Heading now says which is which |
| R68 | New York described as "barring" corporate and LLC contributions and sharing the federal prohibition | Wrong. § 14-116(2) permits up to **$5,000 in the aggregate per calendar year** — a limit, not a ban — and § 14-116(1) names LLCs alongside corporations. Rewritten as federal prohibits / Texas prohibits / **New York limits** / Idaho permits |
| R69 | Appendix D says "an annual aggregate ceiling"; Appendix G's table said "none" | § 14-114(8)'s **$150,000** annual aggregate limit is still on the books; enforcement was preliminarily enjoined as applied to independent-expenditure-only committees, *New York Progress and Protection PAC v. Walsh*, 733 F.3d 483 (2d Cir. 2013). Both places now say statutory-but-not-fully-operative. **The reviewer's further claim of a 2016 NYSBOE opinion of general unenforceability is NOT asserted — no primary source was located, and it is flagged as a citation to confirm** |
| R70 | ADGN reported as "false negatives under about 1%" | Overstated. ~**2–2.5% discordance** in the reported comparison |
| R71 | "the flat matchability gradient cannot generate the age result"; "does not rest on a handful of top donors"; "all of the error sits in the initial-based keys"; "the top decile is also 100%"; abstract's "a property of the match key"; "the matched set is a floor" | All six bounded. The gradient rules out that mechanism only, not donor-side name completeness, mobility or survivorship. Resampling shows the estimate "remains large", nothing about particular donors. "All **detected** errors … none was **detected**". Top decile: **no error detected among the 60 records sampled there**. Abstract now says "detected precision differed sharply by match tier". "Floor" now specified as a floor on the **count of identifiable donor–voter matches** and explicitly not a bound on any statistic |
| R72 | Stale checklist reference listing the stratified re-rating as outstanding; missing closing quotation mark in Appendix G's withdrawal sentence | Both fixed |

**Verifier: 804 → 883 figures; audited sections 20 → 23.** One honest limit recorded: G3's layer
table and G4's clipping table are **exempted with a reason** rather than probed, because
re-deriving them needs `diag_contribution_limits.py`'s ORG_RE person/organization heuristic and
its residence filter — reimplementing those would copy the appendix's own instrument into the
verifier instead of checking it. A first attempt disagreed with every cell and **the basis error
was mine**, which is CLAUDE.md's suspect-your-own-basis rule working. G2's bunching counts need no
heuristic and are probed.

**Still open, and now the whole remaining list:** manuscript compression and a conventional
reference list in the target journal's style; the archival release and DOI; the two open items in
the ethics/data-use self-assessment. The reviewer's closing position is that after this round
"Findings 1–3 and the raw/adjusted association in Finding 4 should be stable enough to proceed to
manuscript compression and journal selection."

### Round 8 (2026-07-29) — manuscript compression and a formal bibliography

Not a review round: the last outstanding item from reviewers #2 and #3, executed. Reviewer #2's
strip list applied, reviewer #3's bibliography added.

**The split.** A companion
[`donor-class-methods-supplement.md`](donor-class-methods-supplement.md) now carries the material
a journal article should not hold but a replication package must: per-figure script provenance,
the verification apparatus and its coverage limits, the full reproduction recipe in dependency
order, and a **corrections ledger** of every claim withdrawn or narrowed across review rounds
4–7. The reviewer explicitly permitted that material to live in the repository.

**Removed from the manuscript:**

| what | effect |
|---|---|
| Pre-abstract matter — provenance block, verifier figure counts, revision chronology, "Paper #3 of the series" | 1,196 → 583 words; **116 → 55 lines before the abstract** |
| The dependency-ordered shell reproduction block and script inventory | ~620 words |
| Every "earlier drafts said X" / "an external reviewer found Y" narrative — **60+ passages across the body and all seven appendices** | ~1,100 words, and the article no longer narrates its own drafting history |
| Finding 3's matchability-by-party table (methodological) → Appendix F, with a two-sentence summary and cross-reference left in place | ~350 words out of the body |

**Added:** a conventional `## References` section — 19 scholarly works with volumes, pages and
DOIs; 3 cases; 17 statutes and regulations including the three WAC amendment notices; 11 agency
datasets and administrative sources; software and code. Appendix D's inline full citations became
author-year short cites against it.

Net: 28,915 → **27,827** words *including* ~970 words of new references, so roughly 2,000 words
of prose came out. Body (title through "What it means") is **10,925**; the appendices carry
**15,930** as supplementary material, which is where a long methods discussion belongs. Honest
note on that split: the compression is real but modest in total-word terms, because the bulk of
this document has always been its appendices, and reviewer #3 explicitly stopped treating length
as a defect. What changed is the *shape* — the article now opens like an article.

**Verifier changes, and one new control.**

- It now **scrapes both documents**. `SECTION_BOUNDS` entries take an optional third element
  naming the file; section-less probes search a joined haystack. Without this, every probe whose
  sentence moved to the supplement would have gone blind rather than failed — the dangerous
  direction.
- **Appendix F's matchability block is now audited** (24 sections, up from 23). It moved out of
  Finding 3, and letting a reviewer-required derived table land in an unaudited appendix is
  exactly the mistake rounds 5 and 7 both punished.
- The audit now **reports literal exemptions that no longer fire**, as a warning. An exemption is
  the only escape hatch, so a stale one would silently absorb a figure if its token reappeared in
  an audited section. **32 went quiet** in this pass, because the prose that needed them moved to
  the supplement.

**Verifier: 883 → 888 figures, all passing; 1,777 tests pass; all six public verifiers exit 0.**
Four anchors broke on rewording and were re-pointed — the control working as designed.

**One unrelated defect found and fixed while verifying this pass.** The full suite went red on
`TestRaceFlagUsesRegistry::test_race_flag_matches_district_flag`, which passed in isolation.
Cause: `load_race_registry` memoises per state in the module-level `_RACE_REGISTRY_BY_STATE`, and
`TestRobustness`'s two tests deliberately load a broken or absent registry — caching `{}` for WA.
`monkeypatch` restores `_RACE_REGISTRY_ROOT` but cannot un-poison that dict, so any later test
needing the real WA registry saw an empty one. Fixed with an `isolated_registry_cache` fixture
that swaps the dict itself, keeping the poison local. Pre-existing, unrelated to the donor paper,
and the kind of flake that teaches a team to ignore a red suite.

**Open:** the archival release and DOI, and the two open items in the ethics/data-use
self-assessment. Both the author's. No analytical or editorial item remains.

### Round 9 (2026-07-29) — external reviewer #4: the package, not the paper

Verdict: **analysis freeze go; preprint no-go; journal submission no-go.** The reviewer stopped
asking for robustness work — "I would not add another broad robustness exercise unless a journal
referee identifies a specific defect" — and turned to the submission package: the ethics document,
the submission notes, this checklist, the methods supplement, plus targeted paper corrections.
Their component verdicts: main paper conditional pass; supplement strong but overstating public
reproducibility; **ethics determination not sign-ready**; submission notes strategically outdated;
this file valuable as history and unsafe as an operational checklist.

**The round's largest finding was not in their letter.** Tracing their FEC citation point found a
live exposure: FEC-derived individual contributor records — name, address, employer, occupation,
giving history, a modelled donor-likelihood score and a suggested dollar ask — were flowing into
the fundraising prospect CSVs and into `templates/donor.html` sections headed "Top Solicit-Able
Donors" and "Use this list to prioritize re-asks of past givers." **11 C.F.R. § 104.15**
(52 U.S.C. § 30111(a)(4)) bars using information copied from FEC reports to solicit contributions
or for any commercial purpose. The repo had cited only § 30104 and analysed § 104.15 nowhere.
**~97% of the 16,900-row prospect output was FEC-derived**; 459 rows were not.

Owner's decision: **remove the solicitation and individual-level donor features outright**, both
federal and state money, rather than segregate by source. Boundary implemented: **no named
contributor and no named matched donor appears in any report, export or analysis output.**

| # | Defect | Fix |
|---|---|---|
| R73 | Appendix B asserted "No access restriction applies" to all four contribution layers | Rewritten: publicly *disclosed* is not unrestricted use; § 104.15 stated; **§ 104.15(c)** named as the basis this research actually relies on |
| R74 | The ethics doc's §1 table marked the FEC layer `No — open`, citing only § 30104 — the only row in the table with no use analysis | Corrected, plus a new §2a giving FEC the statutory treatment RCW 29A.08.720 already had |
| R75 | Solicitation features shipping FEC contributor data | **Removed**: `donor_prospects.py`, the `donor-prospects` command, the `donor_prospects` table, `get_top_donors`, `compute_donor_overlap`, `_build_top_donors_by_candidate`, the top-20 named matched voters, template sections in three files, and the vitals prospect metrics. 16,900 rows and 52 CSVs purged by `scripts/drop_donor_prospects.py` — **after** capturing the only surviving inventory of them into the memo, since `reports/prospects/**` was gitignored and the table was wipe-and-insert per slice |
| R76 | The ethics doc claimed 45 CFR 46.104(d)(4)'s de-identified-recording limb was satisfied because "no output contains an identifier" | **Not what the provision requires** — it asks how the investigator *records* the data, and this project retains names, addresses, voter ids and linked tables. Claim withdrawn; replaced with a Common Rule **coverage** argument (unaffiliated, unfunded, no FWA) |
| R77 | "No IRB has jurisdiction", and a prediction that a board "would most likely" agree | Both replaced. Jurisdiction becomes: no institutional requirement has attached. The prediction is deleted as exactly the self-serving forecast an unaffiliated researcher should not make |
| R78 | **Found by us, not the reviewer:** the crossover tables printed percentages over bases of 102 and 44, from which cells of **2** and **8 individuals** were recoverable by arithmetic. The ethics doc claimed the smallest cell was 44 and that "none reports a cell of one"; Appendix B claimed "thousands to millions" | Idaho's minor-party crossover and bound rows **withheld** as a disclosure control. Smallest derivable population cell now **25**, restated in the paper, the assessment and the metadata. Appendix F's smaller counts are blinded *sample records*, already published at row level; Appendix G's `1` is one *contribution*, public by name in Sunshine. Both distinctions now stated |
| R79 | NY and Idaho use analyses missing | **New York closed**: § 3-103(5)'s elections purpose, which NYSBOE's guidance states includes academic research. **Idaho corrected**: § 34-437A is operative; § 74-120 was overstated as barring "derived lists" |
| R80 | "Every aggregate is independently re-derived" contradicted the supplement's own Appendix G exemption | Narrowed at both statements: designated results re-derived plus a coverage audit; the specialised-classification tables named as reproduced by their originating script |
| R81 | "Rebuildable by `donor_matcher.py`" implied clone-and-run | Recast as authorised reconstruction; three explicit reproducibility tiers in the supplement, with **independent public replication stated as not possible** |
| R82 | "G2 — the cap binds" asserted what its own body denied four lines later; main text said caps "visibly bind" | Heading becomes "bunching at statutory values"; the causal attribution is dropped from both |
| R83 | "itemization threshold" mislabelled a trigger the paper itself shows is routinely undershot | **NOT ACTUALLY APPLIED IN THIS ROUND — see R99.** This row claimed the relabel was done; the paper's two table headers still read "itemization threshold" until round 10 found it. Left standing rather than quietly corrected, because a log that silently repairs its own false entries is worse than one that shows them |
| R84 | Supplement had no environment lock and no seed record | §2a added: Python 3.13.0, DuckDB 1.4.4, both seeds documented (the `"2026-07-27"` md5 draw; bootstrap `SEED = 12345` with its append-only hazard named), and the **missing** lockfile and checksums recorded as outstanding rather than implied |
| R85 | Corrections ledger inside the submitted supplement | Split to `donor-class-corrections-ledger.md`; the supplement is now a clean online methods appendix |
| R86 | This file used as an operational checklist | Renamed **`electoral-health-audit-log.md`**; a new two-page `donor-class-release-checklist.md` holds current binary gates with owners |
| R87 | Overstated submission-note positions | Retired: "every finding replicated across both systems"; "same matched individuals" (Jaccard 0.14–0.16); the absolute novelty claim; "lead with Appendix G"; "caps bind but do not compress"; Appendix G as a direct contribution on limits. Venue ranking becomes ELJ, SPPQ, Political Behavior; Interest Groups & Advocacy dropped |
| R88 | AI disclosure read "AI-assisted drafting and analysis review" | Expanded to SAGE's standard in the paper, the metadata and the title page: systems named; code, methods, citation-checking and analysis-proposal uses disclosed; AI not an author. **Twice-corrected (round 16, 2026-07-30): the clause "no PII-bearing record submitted to any hosted service" is CORRECT and was wrongly retracted in round 15.** That retraction assumed the 480-record validation had been AI-adjudicated, on the strength of this paper's own wording; the author confirms every verdict is theirs. The disclosure now also drops the false claim in the other direction — that AI performed a first rating pass. It performed none |
| R89 | Article and appendices in one 27,800-word file | Split by `scripts/build_elj_submission.py` — anonymised manuscript (**body 8,565 words excluding tables**, against ELJ's 15,000 preferred), supplementary appendices, and a title page carrying all four declarations. Counts are derived, not hardcoded. Abstract trimmed to **297** against the 300 cap, and its turnout range corrected to the exact-eligibility figures the paper says to cite |
| R90 | Ethics doc emphasised `.gitignore` as governance | Replaced with a status table naming **five unimplemented controls** — NY full-DOB minimisation, encryption at rest, controlled backups, retention/destruction dates, audit logging — because an aspirational list is worse than a short honest one. COI expanded with six explicit unanswered financial and operational questions, left visible |

**One place we deliberately did not follow the reviewer.** They stated that NYSBOE Formal Opinion
2016 #1 conclusively settles § 14-114(8). The opinion exists and the paper's "no primary source
located" hedge is gone — but the published index lists 2016 #1 under a caption about the **$5,000**
aggregate limit as to I-E committees, which reads more like § 14-116(2) than § 14-114(8), and a
NYSBOE source states no court has so held as to candidates and other political committees, calling
it "only an opinion of the Board." The PDFs are 403 to automated fetching. The paper now states the
careful version and carries an explicit scope note for the author to check against the primary
text. This appendix has already carried four wrong legal claims; a fifth adopted from a reviewer
would be the worst outcome.

**Verifier: 888 to 868 figures** (the suppressed Idaho rows), 24 audited sections, exit 0.
**Tests 1,788 to 1,767** — exactly the 21 removed with the feature (12 + 4 + 1 + 4), verified so
nothing else regressed. All six public verifiers exit 0. All eight report variants render, and
every one greps clean of solicitation language.

**Left open, and all the author's:** counsel review of the memo's §5; reading Formal Opinion
2016 #1; the numeric sign-off; the lockfile and checksums; the tagged release and DOI; the
external ethics determination; the six COI answers; the five governance controls; and the
public-repo sync.

### Round 10 (2026-07-29) — external reviewer #4, second letter: structure, not substance

Verdict: **analysis freeze go; preprint go after the ethics, release and wording gates; journal
manuscript major structural revision; two-paper substantive split NO.** The reviewer's summary
is the useful one: *the paper is analytically stronger than its presentation.* It still read as
several related papers compressed into one result narrative while the actual measurement
contribution — linkage, validation, sample selection — sat in appendices.

Their reasoning against splitting into two articles is worth keeping, because it is the same
reasoning that would kill the second paper on its own merits: a federal-versus-state article
would carry confounded comparisons (Jaccard 0.14–0.16, different disclosure triggers, different
periods), a stylized clipping exercise that is no longer a test of contribution limits, and no
institutional estimand — one publishable paper and one under-theorized research note, both
leaning on the same linkage apparatus. Deferred to a future paper that adds states, period
alignment, election-designation data and an actual design.

**The reviewer read paper `(5)`, which predates round 9**, so three of their wording items were
already closed: the "every aggregate" narrowing, the expanded AI disclosure, and the
`§ 104.15` treatment. One was **not**, and that is the round's first finding about ourselves.

**Three defects found by us, not in their letter.**

1. **R83 was recorded as done in this log on 2026-07-29 and was never applied to the paper.**
   The itemization-trigger relabel existed only as a table row here. Both table headers still
   said "itemization threshold". A logged fix that does not exist is worse than an open one,
   because the log is what a later session trusts.
2. **The opening pooled-concentration sentence was mixed-specification** — worse than the
   reviewer diagnosed. They assumed all three figures were retired all-tier numbers. Measured:
   46.6% is the **primary** pooled figure while 42.4% and 43.8% are the **all-tier** panel
   figures, and the all-tier pooled figure is 47.7%. So the sentence whose whole purpose is to
   warn against mixing specifications was itself mixing them. Now a like-for-like primary triple:
   46.6 pooled against 41.2 federal and 43.5 state, a 3.0-point overstatement.
3. **The primary tier's share of matches was stated three different ways** — 85–89% in
   Appendix C, 81–89% in Appendix F's table, 80.7–89.2% in Appendix F's prose. Found only by
   choosing to *derive* the tier shares rather than exempt them from the coverage audit: the
   true range is 80.7–89.2%, so Appendix C was wrong and had excluded Washington's state panel.
   The new methods section had already copied Appendix C's version, which is how a wrong figure
   propagates. All copies now print one decimal, because integer rounding of a range endpoint is
   ambiguous in direction — 9.515 had been rounded *down* to 9 as a floor while 12.6 was rounded
   *up* to 13 as a ceiling, and no single tolerance can accept both.

| # | Defect | Fix |
|---|---|---|
| R91 | Two titles, neither describing the paper's actual scope | Journal title becomes **Who Gives? The Demographic and Partisan Composition of Matched Campaign Donors in Washington, New York, and Idaho**. *The Donor Class Is Not the Electorate* is a claim about one comparison, not a description, and is now preprint-only |
| R92 | "Electorate" sliding between registration roll, actual voters, voting-eligible population and "the population that elects officials" | Defined at first use in **both** the abstract and the introduction as the **registered electorate**; the short answer restated as "matched itemized donors are not representative of the registered electorate"; Finding 1's heading qualified. Also "matched donors are far older than the voters they fund" — donors fund candidates and committees, not voters |
| R93 | Framed as a measurement paper, measurement contribution in Appendices C, D and F | New main-body section **Data, linkage, and validation** (1,264 words) before Finding 1, covering the eight things a referee needs first: the three populations, why these three states, panel construction, the deterministic rule, why the full-name tier, what validation does and cannot establish, what the restriction costs, and what generalizes — plus the linkage-literature positioning against Fellegi–Sunter, Enamorado et al., Ansolabehere & Hersh and Bailey et al. Added to the coverage audit rather than trusted |
| R94 | ~50 lines of declarations and panel framing before the abstract | The journal artifact is title → abstract → keywords → text. The pre-abstract block is **dropped from it**, not moved: nothing in it is absent from the new methods section or Finding 1's panel-gap subsection. Declarations live on the title page |
| R95 | Finding 3 at 3,901 words carrying five distinct inquiries | Recipient-party crossover, and the in-state/out-of-state and safe-seat-origin passages, relocated to **Appendix H**, with a one-sentence pointer left at each excision. Body 8,565 → **7,879** words excluding tables |
| R96 | Finding 4's nominating-stage corollary is a separate institutional argument | Relocated to Appendix H3. The donor-turnout result never rested on it |
| R97 | Federal–state comparison too prominent to be secondary | "Two panels, read this first" no longer opens the article. The hierarchy is stated once, in the methods section: primary = donors differ from the registration baseline within each panel; replication = the direction recurs in both; secondary = the panels differ from each other; **not identified** = why |
| R98 | **Ours.** Mixed-specification pooled concentration in the opening and in Appendix C | Recomputed; all three legs on the primary specification, with the all-tier trio confined to Appendix F and labelled. `wa_pooled_top1` is now a real derivation — it had been a remembered number |
| R99 | **Ours.** R83 logged as done, never applied | Applied. Both table headers become **mandatory itemization trigger**, with the two routes that put identified transactions below it — aggregate-crossing and voluntary itemization — stated in the bullet rather than implied |
| R100 | **Ours.** The primary tier's share stated three ways, one of them wrong | Derived across the six retained all-tier panels; Appendix C corrected; every copy prints one decimal and is asserted by a section-less probe plus a methods-scoped one for coverage credit |
| R101 | Abstract cited age standardization but not the two cuts that answer the obvious objection | Swapped for joint age × county standardization and party-specific matchability differing by ~1 point. The Idaho Republican withdrawal leaves the abstract and stays in Finding 3. **299** words against the 300 cap |
| R102 | Submission notes unusable as an operational document — stale status header above later work, the contribution stated twice, historical instructions beside current ones, a pre-SSRN checklist contradicting the release checklist, and the retired "no IRB has jurisdiction" | New two-page **`donor-class-submission-memo.md`** holds current state only. The notes are retitled a **review log**, the duplicate checklist retired rather than updated, and the IRB wording corrected in place with a note on why |

**What was deliberately not done.** The reviewer's structural items apply to the *journal
manuscript*; their own verdict on the preprint is "suitable after the remaining gates". So the
relocations (R95–R97) are performed by `build_elj_submission.py` and the canonical manuscript
keeps the complete descriptive record. The wording and numerical items (R91–R92, R98–R101) are
in the canonical file, because those are defects rather than presentation choices.

**Verifier: 868 → 904 figures, 25 audited sections** (the new methods section), exit 0. Two new
derivations, `wa_pooled_top1` and the four tier shares. Ruff on the two edited scripts: clean;
the repo-wide 432 findings are the unchanged pre-existing baseline, verified against HEAD.

### Round 11 (2026-07-29) — adversarial re-read, and the match rate

Self-directed, not a reviewer letter. Six presentation and consistency defects fixed
(commit `d181544`), then the largest gap closed: **the paper described its matched set as "a
floor" throughout without ever saying how far below the ceiling that floor sits.** For a paper
whose asserted contribution is the instrument, the match rate is the first thing a referee asks
for, and it was absent.

| # | Defect | Fix |
|---|---|---|
| R103 | The "electorate" definition added in round 10 split a two-sentence contrast, orphaning "If it is a narrow, self-selected slice" three sentences from its antecedent | Contrast restored; definition follows it |
| R104 | Finding 2's Idaho parenthetical argued caps do not explain Idaho's flatter distribution, leaning partly on the as-built state-vs-federal comparison — the comparison the same section shows reverses under the common-total restriction | Rebuilt on the within-layer leg alone: Idaho is least top-heavy *inside* the federal layer, under limits identical in all three states. The cross-layer leg is now explicitly declined |
| R105 | Finding 4 opened with `is_super_voter`, the one measure the paper calls "a defect in the measure rather than a result", and disclosed that eighty lines later | Leads with New York's count of generals voted; Washington's non-comparability stated at first use |
| R106 | "A large minority of the raw gap is composition" quoted the tenure-band adjustment (42%) that the paper goes on to reject; the preferred exact-eligibility restriction attributes 14–20% | Heading tracks the preferred specification and says why the larger figure should not be cited |
| R107 | "A coin-flip's error on an eighth of it" understated the paper's own figure — the initial-based keys carry 10.8–19.3% | Stated as 11–19%, matching the restriction-cost paragraph |
| R108 | Three inline errata narrating the paper's own revision history | Moved to the corrections ledger. Two exemptions covering the known-WRONG resolution rates (87.8 / 86.7) were **deleted rather than replaced**: an exemption for a value known to be false would absorb it silently if reintroduced |
| R109 | **The match rate was never reported.** | New subsection with two tables. Recall **39.1–56.9%** of resident donor identities, dollar coverage **37.1–61.1%**, both on residence-restricted denominators — necessary because the FEC layers are residence-filtered at load and the state layers are not (NYSBOE 23.6% out-of-state). Identities and dollars are restricted the same way so the columns share a basis |
| R110 | A single recall figure invites "the rule discards half the donors it could reach" | Decomposed. The **uniqueness guard costs only 1.1–2.3%** of eligible identities; the large residual is identities with *no* active registrant under that surname, first name and ZIP5, which no uniqueness rule could recover. That residual is explicitly not decomposed further and is labelled a coverage property, not an error rate |
| R111 | A confound the paper had not named | **Recall differs across panels**, so part of any federal-versus-state difference is differential linkage reach. Confound count goes three → four in the preamble, the methods section and the limitations bullet |
| R112 | Washington's state panel is the low outlier on both measures | Cause identified and stated: the PDC files **99.9%** of contributor names *without* a comma, so the parser takes the first token as the surname. A source-format defect in one layer, not a behavioural difference — and a reason not to read WA state as "harder to reach" than New York |
| R113 | **Ours, caught by the verifier.** Idaho's out-of-state share was published as 5.7% | The independent derivation returned 6.1%. The gap was a basis difference — the ad-hoc figure counted rows with no contributor name. Paper corrected and the basis now stated, per the standing rule that a mismatch means fixing the paper or the derivation, never the tolerance |

**The new figures are derived twice, independently.** `scripts/diag_match_rate.py` produces
them; `verify_donor_class.py` re-derives all of them from the specification without importing
that script, because importing the originating script would make the agreement circular. The
verifier also carries a standing cross-check: the count of identities resolving to exactly one
registrant must equal the published panel's row count, and it does in all six panels — which is
what establishes that the denominator describes the same universe the matcher used.

**Verifier: 904 → 976 figures**, **27** audited sections (the methods section is now three
adjacent non-overlapping slices), exit 0. Tests 1,767. All six public verifiers exit 0. Ruff
clean on both edited scripts.

**Three items raised and deliberately left open**, because they add empirical content rather
than disclosure: a worked sensitivity showing what the ~3% match-error bound does to a headline
figure; decomposing the county dollar multipliers into participation × intensity (Blaine's 7.83×
on 909 donors is almost certainly an intensity story); and the residual's own decomposition into
unregistered / moved / work-ZIP / nickname components.

### Round 12 (2026-07-29) — the deferred analyses, and four mechanical gates

Author decision: pursue the three items round 11 raised and deferred, overriding the reviewer's
freeze. The freeze advice predated the re-read that found them, and two of the three are questions
a referee would ask. All three landed, and **two of them contradicted what I predicted.**

#### D1 — match error at the validation ceiling

Two parts, because a bound and a mechanism answer different objections.

**The mechanism.** All 129 confirmed household/relative false merges landed on an initial-based
key, and that is structural rather than lucky. A household merge needs the contributor's name to
equal the matched registrant's, which on the primary key means the same surname *and* full first
name at the same ZIP5 — a Jr./Sr. collision — and the uniqueness guard **drops** those keys, so
they yield non-matches, never false matches. Measured: registrants in such colliding keys are
**3.03%** of Washington's active roll, **5.11%** of New York's, **2.75%** of Idaho's. The pool the
initial-based keys faced — surname and ZIP5 shared with a different first name — is **76.7%,
77.0%, 82.6%**. That ratio is the quantitative form of "129 of 129".

**The bound.** Whatever residual survives cannot be that mechanism, so removal is the right model,
and the whole 3.1% Wilson budget is spent adversarially against each finding. Age moves **1.1–2.0**
points, party **1.1–2.5**, concentration **6.1–8.3**. The compositional findings are insensitive;
**concentration is the exception and is now reported as such** — expected rather than surprising,
since it is a statistic about the top of the distribution.

**A modelling trap found and documented rather than worked around.** Adversarial *removal* is
degenerate for a top-share statistic: deleting the largest 3.1% of donors deletes three times the
top-1% population by construction, so the surviving top 1% is a different and far smaller set. It
reads 41.2% → 9.2% on WA federal, which is arithmetic about the estimator, not a statement about
match error. The concentration column therefore uses a **de-merge** — split the largest 3.1% into
two halves each, leaving total dollars unchanged. The rejected model and the reason are both in the
paper, because a reader who reaches for the obvious model deserves to know why it was not used.

#### D2 — county multipliers, and a prediction that was wrong

The multiplier decomposes exactly and multiplicatively into participation × intensity. I predicted
Blaine's 7.83× was "almost certainly intensity". It is **2.67 × 2.93 — both factors, nearly
equally**, and Manhattan's 5.96× is **2.53 × 2.35**, likewise. So the concentrated counties are
disproportionate on *both* margins at once, which is a stronger claim than the multiplier alone
makes and the opposite of the wealth-effect reading. Clean counter-examples now published in both
directions: **Bonneville** reaches 1.91× on intensity alone with *below*-average participation,
while **San Juan** (2.57×) and **Tompkins** (1.76×) are almost pure participation with
below-average gifts. A multiplier near 2 describes at least three different kinds of place.

#### D3 — the residual, and the largest cause is not what the bare figure suggests

A priority cascade over the "no active registrant" bucket. **The largest single cause of non-match
is geography, not non-registration**: 15.1–30.1% of eligible identities match an active registrant
on surname *and* full first name at a different ZIP5 — movers and work addresses. Name-form
mismatches add 4.5–11.2%. Genuinely unreachable is **15.7–30.9%**, not the 49–65% the undecomposed
bucket implied. Most of the shortfall is a specification choice that could be traded against
precision; only the last column could not.

#### Mechanical gates

| gate | outcome |
|---|---|
| A11 | `requirements.lock` committed — a full 303-distribution freeze of the interpreter that produced the figures, not a minimal list. Supplement §2a row replaced |
| A12 | SHA-256 for eight source files in the supplement, regenerable via `scripts/source_checksums.py`. FEC bulk files carry no digest and the reason is stated rather than left blank |
| B5 | Anonymisation became a **test** — `test_elj_anonymisation.py`, 8 checks, a wider needle list than the builder's table, plus the inverse property that the title page still carries the declarations. **It caught a real leak on its first run**: the repository name survived in the software citation, where no URL substitution reached it |
| A14 | Public repo **staged, not committed** — 22 files copied, 11 new, the renamed `publication-checklist.md` removed, all internal doc links resolve. Verifiers cannot run there because `data/` is git-ignored by design |

**A publication defect found while staging A14.** The paper, the ethics assessment and the audit log
all hyperlinked `fec-contributor-data-use-memo.md`, which is marked *"Internal. Not for
publication."* — it records a compliance exposure in commercial tooling and the questions put to
counsel. A public paper would have shipped a dead link to a document that must not exist publicly.
All three now name it as an unpublished internal record instead. A link-integrity sweep of the
staged public checkout is what surfaced it, and a second broken link with it (the ethics assessment
pointing at the private review log).

**Verifier: 976 → 1,095 figures** over **29** audited sections. The methods section is now three
adjacent non-overlapping slices and Finding 2 is two, because carving a slice out of an audited
section orphaned two probes the first time. Three new derivations, all written from the
specification rather than imported from the diagnostics that produce the paper's figures — the
verifier's independence is the whole basis of its claim.

**One convention worth recording.** The D1 and D3 summary ranges are differenced from cells
**rounded to the paper's printed precision**, not from raw values. The prose claim is a summary of
the table above it, so raw differencing answers a slightly different question and disagreed in the
last digit (1.163 against the table's 1.1). Stated in the derivation rather than absorbed by a
widened tolerance.


### Round 13 (2026-07-30) — the coverage audit extended, and New York's date of birth minimised

#### The audit

Appendices **A, B and D are now 100% audited with zero unmapped tokens**, Appendix F's three
rating tables are asserted against the frozen verdict CSVs, and Appendix E's and G's tails are
closed. Verifier **1,179 → 1,203 figures over 44 sections**, up from 24 sections a week ago.

Appendix A's figures are all restatements of figures probed elsewhere, so they were **probed, not
exempted** — that is the round-10 lesson applied, since a restatement drifting from its original
is exactly what produced three different published values for the primary tier's share of matches.

**The exemption cap was respected rather than raised.** The invariant test caps the exemption list
at 170 on the principle that the audit is only as strong as that list is short; the additions took
it to 184. Rather than raise the cap, **27 exemptions that had stopped firing were pruned** — which
is what the supplement says should happen to a stale one, and a dead exemption is a hazard because
it would absorb a returning token silently. Two guards fired on my own edits along the way: the
duplicate-key check caught `12.2` being shadowed (three different figures share that token, and it
now carries one merged reason), and the overlap check caught three slices swallowing others.

**What is still not audited is recorded with exact counts** in the verifier's `PENDING_AUDIT`,
which the invariant test now reads rather than duplicating — two lists would drift, and the one
that drifted would be the test's. Remaining: Appendix F's matchability and household tables (192
tokens), its per-tier donor-side risk block (28), its error-mode tail (15), and the unsliced middle
of Appendix C. The name is PENDING, not BY_DESIGN, because it is unfinished rather than deliberate.

**One published figure could not be independently confirmed and now says so.** WA PDC's name-order
misparse rate is published as 1.85% of comma-less rows; a from-scratch heuristic measures 4.7%.
That is a different instrument rather than a check of the same one and is expected to over-detect.
Flagged in the paper for re-derivation from its originating script.

#### New York's date of birth

B10's one implement item, and it turned out to be free. The FOIL production carries a full date of
birth; the analysis only ever read the **year**, because DuckDB's `date_diff('year', a, b)` returns
`b.year - a.year` rather than a completed age. So day and month are generalised to **1 July of the
birth year** — Washington's existing convention, since RCW 29A.08.710 releases year of birth only —
and the two state files now share one representation. `load_ny_voters.py` produces the generalised
column so a rebuild cannot reintroduce the exact date; the raw production stays in the restricted
enclave with its digest recorded.

Verified lossless before and after: all twelve New York age-band figures identical to six decimal
places, then all six public verifiers green.

**It also surfaced a labelling defect.** The paper called the measure "age as of 2024-11-05". It is
not — it is 2024 minus birth year, which runs one year high for the **14.9%** of registrants whose
birthday falls after early November. Relabelled, with the magnitude disclosed: New York's roll 65+
share is 25.25% on this measure against 25.00% on completed age, its federal donors 49.85% against
49.51%, so the **donor–roll gap moves 0.09 points**. It applies to both sides of every comparison
and no finding turns on it. Washington was never day-exact either, so the correction is
paper-wide rather than New York's alone.

**A consequence worth naming: minimisation removed the ability to re-derive the figures that
justify it.** The completed-age comparison cannot be recomputed from the minimised copy — that is
the point of the control. Those four figures are exempted with a reason saying exactly that, and
were measured once, before the migration.

Also this round: the county decomposition moved to the online appendix as **H4** (a Finding 2
detail, and the article was already carrying too much), and **A3b closed by counsel**.

Tests **1,775**. Six public verifiers green. Public repo re-staged, still uncommitted.

### Round 14 (2026-07-30) — reviewer read of the two generated ELJ files

Read `donor-class-elj-manuscript.md` and `-supplementary.md` end to end as a referee would, then
checked every suspect against the databases. Every headline finding reproduced; six defects.

**The substantive one: Washington's baselines are not active registrants, and four places said
they were.** The manuscript's Finding 4 source note and limitations bullet, Appendix C's
"Registration baselines" and Appendix E's turnout table all asserted `status_code='A'`. True for
New York. Washington's age and turnout cuts run on the `voter_scores` `ld`-scope roll — 5,456,444
rows, of which **411,935 are inactive** — because that is the roll this series' WA tooling is
built on. Inactive registrants vote less, so leaving them in the non-donor denominator depresses
the WA non-donor rate and **widens** every WA gap:

| WA figure | published | active-only |
|---|--:|--:|
| federal super-voter, donors vs non-donors | 88.0 / 52.0 → +36.0 | 88.0 / 54.7 → **+33.3** |
| state super-voter | 88.9 / 51.5 → +37.3 | 88.9 / 54.2 → **+34.6** |
| federal eligible-for-all raw gap | +36.7 | **+33.1** |
| state eligible-for-all raw gap | +32.6 | **+29.0** |

**The `ld`-scope universe was kept and the direction disclosed**, rather than re-running WA on
`status_code='A'`. It is the roll the WA panels were matched through and the one the rest of the
series uses; switching it would change four published figures and three ranges to strengthen
nothing. All four sites now state the exception, Finding 4 carries the size, and the active-only
comparison is **derived** by `verify_donor_class.py` rather than asserted. The WA age multipliers
are barely affected — largest move 0.09, federal Silent 2.67 against 2.58.

**Five more.**

1. **The paragraph that defines the baseline gave the all-records counts.** "The registered
   electorate is each state's *active* registration roll — Washington 5.51M, New York 13.54M" —
   NY's active roll is 12,448,081, which Appendix C states correctly 1,600 lines later, and WA's
   is 5,098,276. The literal exemption `"5.51M": "WA roll size, same"` is exactly why it survived:
   **an exemption cannot catch a mislabelled figure.** All three roll sizes are now probed.
2. **Appendix F's reconciliation of the WA multipliers named the wrong cause.** It attributed the
   gap to a narrower denominator, "a few hundredths below Finding 1's". Computed on all four
   bases, the driver is the **panel**: that block runs on the retained all-tier snapshots, which
   take federal Silent from 2.67 to 2.56 and federal Gen Z from 0.04 *up* to 0.10; the denominator
   adds 0.08 more on Silent, giving 2.48. So the gap reaches 0.19 on one generation and runs
   upward on two. Gen Z was the tell — a denominator change cannot move one generation up and
   another down. This block is `appf_head`, one of the four sections closed by written reason, and
   **that reason already said "computed on the RETAINED all-tier snapshots"** — the correct
   explanation was in the verifier and not in the paper.
3. **A sheared sentence** in Appendix F's survivorship note: "Calling the raw age skew an 'upper
   bound' on this basis; that assigned a direction the evidence does not support." No main clause —
   collateral from round 8's removal of drafting history.
4. **H1's footnote claimed the NY state rows "sum to the published panels (NY 378,383)".** They
   sum to **378,388** — the five-row duplicate-`state_voter_id` fan-out on a roll join that
   Appendix C documents. The probe on that sentence asserted the panel count and passed, because
   the panel count is real; what was wrong was the claim that the rows sum to it.
5. **The article's reference list carries 20 works of which the article cites five**; the rest are
   cited in the appendices, which the split moves to a file with no reference list of its own. Now
   labelled in the builder as one list serving both artifacts, with a pointer in the supplement.
   Also fixed there: the supplement header said Appendix H holds three analyses; it holds four.

**Bookkeeping that did not reproduce.** The verifier reports **45** audited sections (41 by
derivation, 4 by written reason); A10 recorded 40, D7 recorded 44, `CLAUDE.md` recorded 44. The
suite collects **1,783**, not the 1,775 recorded — on the same commit, so that was already stale.
The memo still listed D7 as open after it closed.

**A10 is reopened.** The sign-off was given on a document this round changed. It needs one fresh
`--refresh` run and a re-signature before A14.

Verifier **1,220** figures over 45 sections, cold `--refresh`, exit 0. Tests **1,783**. Six public
verifiers green. Ruff clean on both edited scripts.

### Round 15 (2026-07-30) — external reviewer #5: the validation bound, and the submission package

Verdict: keep donor-class as the series lead, do not split it, no new robustness cycle — but one
targeted validation issue, one disclosure contradiction, and a submission package that was still
an internal draft. Every checkable claim in the letter was verified before acting; all held.

**1. A pooled error bound was being spent panel-by-panel.** The blinded sample allocates **20**
full-name records per panel, so 0/20 bounds a single panel's error at **16.1%**; the 3.1% figure
is the Wilson bound on the pooled 120 and is a panel bound only under a common-error-rate
assumption the paper never stated. Now stated, with both budgets reported. At 16.1% every 65+ row
still clears its roll baseline and so do New York's party rows; **Idaho's do not** — 20.4 → 5.2
against 11.8% registration. The insensitivity claim is withdrawn for Idaho and the unrun remedy
named. Concentration left the budget table: equal two-person de-merging is a stylized stress
test, not spent error budget. Partial merges are now split by tier, and **1 of the 8 is on the
primary key** — unlike identity errors, this mode is not structurally absent there, because a
jointly-filed gift does not require the two names to differ.

**2. The "no PII to hosted AI" control was never in force.** Committed separately at `5f1f857`.
The 480-record validation extract pairs registrant names with contributor names and was submitted
for adjudication; five documents said otherwise, including the ethics assessment's control table.
Corrected with its scale, new §5a, new counsel gate A15, R88 corrected in place.

**3. Washington's baseline switched to the active roll**, reversing round 14. Committed at
`616ba7a`. 46 figures moved; no direction changed. The round-14 disclosure survives only as a
crosswalk for the companion papers.

**4. "Recall" was never measured.** The denominator is parsed `(surname, first name, ZIP5)` keys,
not verified identities. Renamed to **strict-key match rate** throughout. The residual
decomposition stops asserting that the different-ZIP bucket is movers and work addresses and
lists the explanations the fields cannot separate.

**5. The article had no literature.** All of it sat in Appendix D, so a referee could not judge
novelty from the manuscript. New 809-word **Prior work, and what this paper adds** section,
sliced and audited like everything else.

**6. Five formulations pulled back**: replication → within-state repetition; the abstract's
"account for"; purposive state selection stated in methods and limitations; the measurement
instrument is the linkage procedure, not the contribution; precision is a property of the key →
detected precision differed by key in the sample; and the conclusion's monotonic
who-votes/who-nominates/who-pays ordering, which no companion set jointly demonstrates.

**7. The submission package.** One formal title for both artifacts. Title page rebuilt to SAGE
structure — Statements and Declarations, CRediT, consent headings, ethics statement no longer
labelled "Incomplete", conflict disclosure cut to five lines, and the data statement's
every-figure-re-derived claim corrected against the four written-reason sections. Eight detailed
tables moved to a new **Appendix I** (article 19 → 13 tables). H2 and H3 dropped from the
submission as companion-paper duplication; **Appendix G condensed to a stub rather than cut**,
because fourteen cross-references point at it and orphaning all of them to save a referee some
reading trades one defect for a worse one. Supplement relative links delinked — they resolve to
nothing once SAGE hosts the file. New cover letter with the SAGE-required companion-study overlap
matrix. Audit log re-headed: it still named the Washington paper as series lead.

Three new tests guard the generated artifacts: relocated-table pointers resolve, dropped blocks
name a companion rather than a missing appendix, and the supplement carries no relative links.

Verifier **1,242** figures / 45 sections cold, exit 0. Tests **1,786**. Six public verifiers
green. Ruff clean. Body 10,826 of 15,000; abstract 289 of 300.

**Left for the author:** A10 re-signature (the paper changed again), A15 counsel question, the
five title-page fields, three cover-letter status cells, then A14 → A13 → B9.

### Round 16 (2026-07-30) — my round-15 correction was itself wrong

**The author rated all 480 validation records, and every other pass. No adjudication in this
project was ever AI-assisted, and no person-level record went to a hosted model.**

Round 15 concluded the opposite. The chain was: Appendix F said "adjudicated by the AI
assistant"; the AI-assistance disclosure said "AI-assisted verdicts constitute the first rating
pass"; the sampler's docstring said the evidence file carries voter and donor names; no rating
script exists, so a session must have filled the verdict column. Every link was real. The
conclusion was false, because the paper's own wording about who rated was wrong and I treated a
document as evidence of what a past session did instead of asking the person who was there.

That error propagated into five documents, a new ethics assessment §5a, a counsel gate (A15) and
a commit message, in the space of an hour. **A confident wrong correction costs more than the
defect it corrects**, and the rule now recorded at project and user scope is: never state what a
past session did as fact — ask.

**Withdrawn:** ethics §5a in full; gate A15; Appendix B's processor-disclosure bullet; the
"one PII-bearing artifact was submitted" paragraph in the paper front matter, the title page, the
metadata, the memo and the cover letter. R88's original clause — *no PII-bearing record submitted
to any hosted service* — was **correct all along** and is restored, now with the sharper point
that no mechanism enforces it because an agent reading a file *is* submission.

**Corrected in the other direction, which is the substantive part.** The paper had been claiming
an AI first pass checked by an independent human. Neither is true. It is **one rater, twice** —
an original pass and a blind re-rate with fresh opaque ids. So the agreement statistics are
**test–retest, not inter-rater**: 88.0% four-category, 93.9% binary, kappa 0.815, 75/75 on the
full-name block. That bounds how consistently one reader applies the criteria and cannot detect a
criterion applied wrongly but applied the same way twice. Appendix F now says so, labels the
coefficients, and names an independent rater as an open item rather than implying one exists.
The same correction propagates to the methods supplement, the metadata abstract, the cross-state
paper and both scoring scripts.

Nothing numeric moved. The verdicts are the verdicts; what changed is who produced them and what
the agreement between two passes can support.

**New:** `docs/second-rater-instructions.md` — a self-contained brief for a genuinely independent
rater, with the id-space trap called out (the `H####` ids are published *with their verdicts*, so
a third rater handed them can look up both prior answers in a minute).

Verifier **1,239** figures cold, exit 0. Tests **1,786**. Infrastructure 92.

---

### Round 17 (2026-08-01) — external reviewer #6: "not cycling yet, but very close"

The letter's own verdict is the important part: the previous round's corrections were real, but
the paper had grown to ~35,400 words with a 3,900-word methods section, and **each new robustness
analysis was generating its own qualifications and, in three places, its own overclaims.** The
recommendation was one targeted validation, one reconciliation pass, then freeze. That is what
this round does. No new robustness analysis was added; one measurement replaced three estimates,
and one sample was drawn.

**The one new measurement — Washington's PDC name-order parser, settled rather than described.**
The paper carried **three** competing figures for how badly the parser mis-reads comma-less names
(1.85% of rows from the originating script's own parser, explicitly unconfirmable; 4.7% from a
surname-vocabulary heuristic; a dollar analogue of the first), and a referee would reasonably ask
why a panel ships with a known defect and no settled size. `diag_wa_pdc_name_order.py` answers it
by rebuilding the primary key **both ways** against the active roll under the same uniqueness
guard:

| | measured |
|---|--:|
| comma-less keys resolving only when read first-name-first | **7.6%** (42,787 of 560,182) |
| their dollars | **8.4%** ($27.1M) |
| coincidence baseline, FEC layer where true order is known | **0.18%** (523 of 298,645) |
| WA state strict-key match rate, either order accepted | 38.8% → **46.4%** |

Two controls make it a measurement rather than a fourth estimate. The forward column reproduces
the published panel exactly — 217,121 keys against 217,114 matched donors, 65+ share 39.0% against
the published 39.0% — so the instrument is measuring the matcher. And the **placebo** rules out
coincidence: swapping the halves of a name whose true order is known resolves uniquely only 0.18%
of the time.

**The parser was NOT repaired, and the reason is on the record.** Accepting reversed keys would
add 42,787 matches from a population the blinded validation never rated, and the placebo shows
some would be coincidental namesakes — so it needs a fresh validation round on a new
specification, which is the cycling the reviewer warned against. Instead the WA **state** panel is
labelled coverage-compromised, by a quantified 7.6 points, and the direction is measured too: the
donors the defect loses are *older* (44.0% 65+ against 39.0%), so a repaired parser would move
that panel's headline from 39.0% to **39.8%**. The defect understates Finding 1 there; it does not
manufacture it. Both superseded estimates are withdrawn from Appendix C and Appendix F.

**The one targeted validation — Idaho, drawn and outstanding.** Idaho's party rows are the single
result that fails the panel-specific 16.1% bound. A fresh sample was drawn: **204 records, 102 per
Idaho panel**, all on the primary full-name key, balanced across DEM/REP/UNA (68 each) and across
the top dollar decile and the rest, excluding by voter id all 450 distinct registrants rated in
the 480-record pass, in an unpublished `I####` id space. At zero detected errors that supports a
per-panel ceiling of **3.6%** against the current 16.1%. Brief:
`docs/idaho-validation-rater-instructions.md`. **No figure in the paper reflects it**, and the
abstract now carries the qualification instead of resting silently on the pooled assumption.

The exclusion list was *regenerated from the seed* rather than trusted: `--label priorids`
reproduces the 2026-07-27 selection exactly (120 per tier, 80 per state x panel), which is the
only way to prove a "fresh" draw is fresh.

**Structure — the methods section stops being a paper inside the paper.** The error-budget table,
the roll-collision measurements, the equal-halves de-merge, the uniqueness-guard split and the
residual cascade moved out of the article body into new Appendix F **§F7** and **§F8**. The body
keeps the linkage rule, the tier validation, the selection cost, the match-rate table, a concise
error sensitivity and one sentence on the unresolved Idaho issue. The two relocated blocks fell
from 1,208 and 867 words to 654 and 743. The ELJ builder's own I1–I3 relocations were deleted —
the canonical paper now does that work — and I4–I8 renumbered.

| id | defect | resolution |
|---|---|---|
| R114 | Dual-title paragraph survived the round-15 switch to one formal title, contradicting the line above it | Deleted |
| R115 | Main methods still said "the first rating pass was AI-assisted", contradicting the front matter, Appendix F and round 16's correction | Removed; replaced with the accurate statement that every verdict is the author's and the second pass is a blinded author re-rate |
| R116 | "Independent human re-rating" in the contribution list, limitations and memo, against Appendix F's own test–retest labelling | "Blinded author re-rate" throughout; "independent" reserved for the outside rater, who has not yet worked |
| R117 | DIME-style work called "circular" | Recast: contribution behaviour is not an *independent* measure of affiliation for this question — the giving supplies both the behaviour and the yardstick |
| R118 | "What none of it reads is a party the state itself records" — a systematic-search claim with no systematic search behind it | "The studies reviewed here generally do not compare…" |
| R119 | Party registration claimed to make the result "falsifiable in a way an inferred position is not" | Replaced with the real advantage: the measure of the characteristic under analysis is not derived from contribution behaviour |
| R120 | "The two-panel construction prevents a pooling error the literature is otherwise exposed to" — unevidenced claim about the literature | "…that would otherwise arise in this design" |
| R121 | "The instrument's reach and its error are both measured" — true linkage error is not measured | "Its operational match rate is measured and its detectable error estimated and bounded", with the limit stated |
| R122 | "The observed failure mode is **structurally unavailable** on this key" | Bounded to what the guard can actually see: it eliminates the observed mechanism where both people appear distinctly on the current active roll, and does not reach inactive or absent relatives, joint filings, misreported names or unregistered namesakes — the one partial merge on the primary key is the standing counter-example |
| R123 | "Whatever residual remains therefore **cannot** be that mechanism" — does not follow; a same-name relative off the roll is still a household mechanism | "Not necessarily a different mechanism, only one the guard cannot see; what it cannot be is a merge between two people both distinctly on the active roll" |
| R124 | Guard-dropped keys described as "donors **almost certainly on the roll**" | "Keys plausibly corresponding to a registrant but dropped because the roll holds more than one candidate" — an ambiguous key does not establish which, or any, of them gave |
| R125 | "Only one of them is the rule's doing" — contradicted by the paper's own residual table four paragraphs later | Rewritten to name the four specification choices that produce non-matches, with the guard as one of them |
| R126 | "In **every** panel the biggest bucket is same-name-different-ZIP" — false in the displayed WA state row (26.0% against 30.9%) | Two fixes. The decomposition is **recomputed on resident keys** in both the script and the verifier, which is the reviewer's preferred remedy and also removes a mixed-basis defect: the table sat on an unrestricted denominator directly below a residence-restricted one, and its matched column disagreed with the match-rate table by up to 14 points. It now reconciles to within 0.1. The prose becomes "the largest identified nonmatch category in most panels", naming the two where it is not |
| R127 | "The **real floor** on what a name-and-ZIP key can reach" | "The residual not resolved by the specific deterministic relaxations tested here", with the six things it still contains listed |
| R128 | Three competing WA PDC name-order estimates, one unconfirmable | One measurement with a placebo control; both estimates withdrawn (above) |
| R129 | Abstract asserted the Idaho party result without the panel-specific qualification the methods disclose | Abstract states which bound each party result survives and that a fresh Idaho sample is outstanding. Re-trimmed to **300** words against the cap |
| R130 | Methods section had become a treatise on deterministic linkage | Six blocks relocated to Appendix F §§F7–F8 (above) |

**Verifier.** 1,305 figures / 48 sections, exit 0. Tests 1,791. Six probes retargeted from `sensitivity` and
`matchrate` to the new `appf_budget` / `appf_reach` slices — a probe's section field records
*where* a figure is asserted, so leaving them behind would have reported the same cells as
unmapped in one section and unprobed in the other. Six "Guard cost" probes and one out-of-state
restatement probe deleted with their table. Nine probes added for the name-order measurement and
the Idaho ceiling, both **derived** rather than exempted, per the standing preference. One
rounding defect caught by the tolerance and fixed in the paper, not the tolerance: the placebo
excess prints 7.5, not 7.4.

**A reserved word, for the list.** `by` fails in DuckDB alias position with a bare "syntax error
at or near" — same class as `rows`, `returning`, `matched`, `resolved`, `nulls`. Now in CLAUDE.md.

**What was NOT done, deliberately.** No new robustness analysis. The reviewer's closing stopping
rule is adopted: from here, only cut, relocate, clarify and prepare the submission, and admit new
analysis only if it could reverse a headline, answers a real editor or referee, closes a
documented gate, or *replaces* a weaker analysis.

---

### Round 18 (2026-08-01) — external reviewer #7: release control, and one statistical error

Verdict: "close — final validation and release-control, not major analytical revision." Two
substantive findings, the rest synchronization and governance. The reviewer was reading the
pre-correction copy for several items already fixed in round 17 (the five retired terms, the
Idaho qualification in intro/Finding 3/conclusion, and the PDC figure, which they quote at 7.6%
against the corrected 7.2%) — checked before acting rather than re-fixing.

**The statistical error, and it was mine.** Round 17 said the drawn Idaho sample would support a
**3.6%** panel bound from 102 records. That treats a deliberately **disproportionate stratified**
sample as a simple random one. Correcting a pooled-bound error and then committing a second one
in the same appendix would have been the worst available outcome of the previous round.

What the design actually supports, at zero detected errors:

| stratum | records | Wilson 95% ceiling |
|---|--:|--:|
| one party, one panel | 34 | **10.2%** |
| one dollar band, one panel | 51 | 7.0% |
| one panel, composition-reweighted | 102 | 3.6% — an estimate, not a binomial bound |
| what the current evidence supports | 20 | 16.1% |

**The party-stratum bound is the one the finding needs**, because the vulnerability is
specifically whether error inflates the *Democratic* share. Applied as a worst case it takes
Idaho federal 20.4% → **18.4%** and state 21.6% → **19.4%**, both far above the 11.8%
registration share — a stronger and more directly relevant defence than a panel average. All of
it is derived by `_d_idaho_sample` and probed, not written down.

**Verdict handling is now pre-specified too**, which the reviewer flagged as a remaining gap:
`NC`/`NP` count as errors, `U` leaves the denominator but is reported, `partial_merge` is a
dollar-attribution issue rather than a misidentification, and **NC-only** and **NC+NP+U** are
pre-committed as sensitivities. That mirrors `score_match_validation.py`, so the Idaho result
stays comparable to the published 480.

**The PDC denominators did not reconcile, and the cause was a defect in my own diagnostic.** The
match-rate table said 555,922 keys; the name-order diagnostic said 560,182. The diagnostic was
**collapsing runs of internal whitespace before splitting, which the matcher does not do** —
40,400 PDC rows carry a doubled space. Removing the collapse aligned it to the matcher character
for character and the reconciliation is now exact and printed: **555,107 comma-less + 846
comma-bearing − 31 reachable from both = 555,922**. The corrected measurement moves several
figures (7.6% → **7.2%**, 38.8% → **39.1%** which removes the second mismatch the reviewer
flagged, recoverable 65+ 44.0% → **46.8%**, repaired headline 39.8% → **40.2%**), and the diag
and the verifier now agree to four decimals on all nine shared metrics.

**Scope narrowed on the parser defect.** The measured direction runs against the age finding, and
that is the *only* outcome established: concentration, county geography, dollars per donor,
turnout and the non-age federal–state comparisons were not measured, so the WA state panel stays
a secondary sensitivity panel for those and the sign is unknown. Said in both the methods and the
limitations bullet.

| id | defect | resolution |
|---|---|---|
| R131 | 0/102 reported as a 3.6% panel-specific binomial bound on a stratified sample | Replaced with the per-stratum table above; the pooled figure survives only as a composition-reweighted precision estimate, explicitly labelled |
| R132 | Verdict handling not pre-specified — `partial_merge`, `U`, `NP` undecided before rating | Fixed table in Appendix F §F7 and the rater brief, with two sensitivities pre-committed |
| R133 | PDC 555,922 vs 560,182, and 39.1% vs 38.8%, presented as the same population | Diagnostic aligned to the matcher's parse; reconciliation derived, printed and probed |
| R134 | Parser defect implied harmless in general | Direction established for age only; the other five outcomes named as unmeasured |
| R135 | "the population that finances campaigns is the same kind of population" | "the observed matched donor populations share several recurring characteristics" — three purposive states do not support the stronger reading |
| R136 | "strongest evidence that it describes donors rather than a quirk of one disclosure regime" | "evidence that the findings are not confined to a single state panel or disclosure system" — the two panels are not independent |
| R137 | Deterministic linkage described as moving uncertainty "out of the estimator", too absolute | Recast: no record-level probabilities to propagate, so error is evaluated by validation and sensitivity — and false links are still measurement error inside the estimands, bounded rather than carried through |
| R138 | "AI made no autonomous adjudication" — "autonomous" is ambiguous | "did not adjudicate any match-validation record" |
| R139 | Memo said "Analysis frozen" while four gates including the Idaho rating were open | "Core analysis complete; final Idaho validation and release sign-off outstanding." Frozen is reserved for after A9x is scored and its consequences verified |
| R140 | Memo §5 said A10 first, §7 began at A14 and asserted "the analysis is signed off" while A10 was reopened | §7 rewritten as a 13-step sequence beginning at A9x, with "do not sync, tag or mint a DOI before the Idaho analysis is resolved" stated |
| R141 | The Idaho rating was described as outstanding but was not a formal gate | New gate **A9x**, preprint-blocking, with **A10 depending on it** |
| R142 | "Nine gates" against six numbered categories | All ten listed individually with status and dependency |
| R143 | Word-count table said Appendices A–I, artifact table said A–H | The generated supplement carries **nine** appendices, A–I; both tables corrected |
| R144 | Memo blurred expected, last-observed and signed build outputs | Three-row table separating them; the signed row is empty because A10 is reopened |
| R145 | Ethics declaration headed "Incomplete by design" | "Researcher assessment complete; no external determination obtained" — the old wording reads as knowingly filing an incomplete declaration |
| R146 | Data-security items treated as parallel housekeeping | Free-space wipe, documented restore test and access review promoted to **preprint-blocking**; retention/destruction before submission. **Not** stated as "enable encryption": volume C: is already encrypted and the reviewer assumed otherwise — the real residual is the Used-Space-Only conversion leaving deleted content in free space |
| R147 | 21,000-word supplement had no map | One-page roadmap, **generated from the assembled headings** so it cannot drift — the same package had already shipped an A–H range against an A–I file |

**Verifier 1,305 figures / 48 sections.** Retitling F8 to carry the relocated match-rate table
broke two section anchors at once — `appf_reach` starts at that heading and `appf_budget` *ends*
at it — so twelve probes reported SECTION NOT FOUND and the budget slice swallowed all of F8,
reporting 109 tokens unmapped in the wrong section. Both anchors fixed, with a comment on the
bound. A section anchor is matched literally: **retitling a heading silently unmoors every probe
scoped to it.**

---

## 2026-08-06 — Coverage gate ported to four more papers; New York reordered

**The gate.** `--coverage` had been an advisory report on six of the eight paper verifiers, so
their figure counts were floors with no ceiling. `vp.audit_coverage` is now shared and gates
`verify_whitepaper` (74 → **88** figures), `verify_who_decides_ny` (96 → **135**),
`verify_who_decides_id` (96 → **210**) and `verify_who_returns_ballot` (21 → **25**), joining
the donor, WA, safe-seat and money verifiers. Series total **910 → 1,081** excluding the donor
paper. `verify_cross_state_money` is **deliberately not gated** — 583 unprobed tokens across
~10 sections is a project, not a port — and that decision is recorded in
`test_series_verifier_invariants.py::TestEveryPaperGatesCoverage.UNGATED` rather than left
silent. A new guard also asserts that every other series verifier calls the gate and that its
result reaches the exit status.

**What the first gated run found, which is the argument for the gate.**

| paper | defect | resolution |
|---|---|---|
| white paper | fundraising correlation **+0.55** in three places against `does-money-move-votes.md`'s **+0.58** | corrected. The money paper retired +0.55 on 2026-08-01 when its frame grew 109 → 129 both-side finance cells, and says so in its own pin note |
| Idaho §IV | primary-electorate under-30 **4.9 → 5.0** and 45–64 **34.2 → 34.1** | corrected. Derived 4.967 / 34.105; the two errors ran in **opposite** directions, which is what ruled out a basis difference, and four age-filter variants agreed to three decimals |
| Idaho | three complete result tables unprobed (§IV's two, §VI's six cohorts) | derived; §VII also re-derived independently rather than deferred to `verify_donor_class.py` |

One occurrence of the stale +0.55 sat in the white paper's Appendix B, *outside* the verified
slice, so a gate scoped to Findings 4–6 would have left it wrong and reported green. A narrow
whole-document guard (`_restated_outside_the_slice`) now covers figures that script sources
from another paper.

**Four open author questions, all the same shape: a stated value that no basis reproduces.**
Each is left in the paper with the full enumeration recorded in the verifier rather than
silently re-pointed. NY §II (now §I) 2025 under-30 turnout `30.8 / 15.9` — fourteen bases, none
reproduces, closest 30.95 / 15.81; the "nearly double" claim holds on all fourteen. White paper
Finding 5 `~3.5–6% of voters` — no panel × denominator basis, closest 4.0–5.7. Idaho §VI 2024
cohort count `263,315` — thirteen bases, all give 263,322. White paper Finding 6
`holdout R² ~0.00` — the money paper's allocation cell is 0.022, which rounds to 0.02. A
duplicate-identifier hypothesis for the Idaho count fitted its evidence exactly and was **false
on checking**; the coincidence was the whole case for it.

**🔴 Still open, and outside the gate's reach.** `money-votes-submission-metadata.md`'s
paste-ready abstract and `money-votes-submission-notes.md`'s objection heading both still carry
the retired **+0.55**. `check_cross_doc_consistency.py` reports them clean, and this was
measured rather than assumed: its orphan check works by **absence**, and +0.55 *is* present in
the money paper — inside the note that labels it retired. **A paper that honestly documents its
own superseded figures immunises its satellites against that check.** The script's own
`--self-test` puts recall at ~52% on one-decimal percentages against ~98% on counts, which is
independent confirmation. Author's call.

### New York reordered — section numbers changed, nothing else did

The paper now opens on its party-resolved result; the age-composition replication moved to
**Appendix A**, and §II–§VI became **§I–§V**. All 135 figures reproduced unchanged through the
move, which is the check that it was a reordering and not a revision.

**Every reference to NY sections in this log predates the change and means the OLD numbering.**
This log is append-only, so those entries are not edited. The map, also carried in the paper's
own Appendix B:

| before | after |
|---|---|
| §I | Appendix A |
| §II | §I |
| §III | §II |
| §IV | §III |
| §V | §IV |
| §VI | §V |

So the recurring note in this log about "NY §III/§IV rate cuts running ~1–2pp under" refers to
what are now **§II and §III**.

**The gate caught the reorder itself**, which is the behaviour to keep: `slice_with_offset`
raised `section start anchor not found` on the first run against the restructured paper rather
than silently auditing the wrong text. Same lesson as the F8 retitling above — a section anchor
is matched literally, and moving a heading unmoors every probe scoped to it.

**Submission metadata drafted** for *Who Decides New York?*, *Who Decides Idaho?* and *Four
States, Four Donor Economies*, plus submission notes for New York. All are registered in
`check_cross_doc_consistency.py`'s pairing table the same day they were written — the +0.55
lesson applied, since an abstract is the highest-consequence place for a figure to go stale.
The white paper is **not** getting submission metadata: it is a research prospectus whose
Appendix B is a publication sequence for the other papers, not an article.

**Suite 1,997 passed / 7 skipped; all eight paper verifiers exit 0.**

---

## 2026-08-06 (second pass) — the harmonizer, and the last coverage gate

**The cross-state synthesis is no longer a draft in the part that mattered.**
`scripts/diag_cross_state_age_harmonized.py` now computes Findings 1 and 3 of
`who-decides-cross-state.md` from one code path across the three voter files, and
`scripts/acs_cvap_by_state.py` pins the CVAP benchmark for all three states at one ACS vintage
(2020–2024 5-year, table B29001 → `docs/reference/cvap_age_acs2024.csv`). The harmonizer
refuses to run without that pin: a per-run fetch would let one state's benchmark move to a
newer release while the others stayed, and the dissimilarity index would quietly stop being
comparable. Finding 3's ten `[recompute]` placeholders are gone; verifier 21 → **74 figures**.

**Three conventions were measured rather than assumed, and one of them tightens a caveat.**
WA and NY birthdates are BOTH normalised to July 1 of the birth year — every row of 5.5M and
13.5M — so `date_diff('year', …)` returns the year difference and nothing finer exists in
either file. Idaho stores a current integer age. So all three states are **year-resolution**,
which is what makes shared bins legitimate; the paper's "age precision differs" caveat is true
but understated, and now says so.

**Filling the placeholders contradicted one of the paper's own claims, which is the argument
for computing rather than transcribing.** Finding 1 said the senior-to-youth ratio "roughly
triples from presidential to lowest-salience in every state". Harmonized, the multiplier runs
**1.5× to 4.9×** — it does not triple in Idaho (×4.9) or in New York's 2025 odd-year (×1.5).
Corrected, with the per-state ratios now stated. Two further results only visible once the
metrics shared a definition:

- **Idaho's closed May primary is the most age-unrepresentative decisive electorate in the
  study** — dissimilarity **27.6** against the worst general measured anywhere here (NY 2023 at
  22.4), and 46.7% over 65 against 5.0% under 30. Its cell was the prose phrase "grayest of
  all" before this; it is now a number, and the phrase was right.
- **"Odd-year" is not one salience level.** New York's two odd-year generals differ more from
  each other (34.4% vs 41.6% over 65) than New York's presidential electorate differs from
  Washington's — 2025 carried a New York City mayoral contest and 2023 did not. That is a
  caution against the calendar-as-salience substitution the harmonization protocol exists to
  avoid.

**A one-directional offset caught the one real basis question, and a loose tolerance nearly hid
it.** The first run reported WA as 7.5 / 13.3 / 18.6–20.0 against the WA paper's
7.4 / 13.2 / 18.5–19.9 — every value 0.1 high, in the same direction. Two suspects were wrong:
the WA paper also filters on `registration_date <= election_date` and has no upper age bound,
and both variants give dissimilarity identical to three decimals. The cause is the
**benchmark's rounding** — the single-state paper differences against its published 1-decimal
CVAP row, this pin carries the unrounded shares. Both are now computed; the unrounded value is
published and the rounded one exists to prove the definition reproduces the WA paper **exactly
at its printed precision**, asserted on every run. The initial cross-check used `< 0.1` and
passed while sitting 0.07 high, which is precisely the systematic offset a tolerance is worst
at catching; it is now an exact rounding test.

**My own error, of the documented kind.** The per-state ratios were first computed from the
paper's ROUNDED table cells rather than the unrounded shares — 4.9–5.4 where the data gives
4.9–5.5, 3.0–6.9 where it gives 3.0–7.0, 9.3 where it gives 9.4. The Idaho paper states that
convention explicitly for its own R−D margins, and the cross-state paper now does too. Caught
by the probes on the first run.

**`verify_who_returns_ballot.py` changed premise.** It was built on the reasoning that a
synthesis paper has nothing of its own to re-derive, so the sources were the ground truth and
transcription drift was the only failure mode. Findings 1 and 3 now HAVE a derivation, so the
script imports the harmonizer and asserts the paper against it, while Finding 2 stays
transcription-checked against the source papers. Both regimes coexist and every probe says
which it belongs to. It now opens the three voter DuckDBs and takes ~60s rather than 0.2s; the
old docstring's "opens no database" claim is retired. The circularity is avoided because the
harmonizer separately guards the shared DEFINITION against the single-state paper.

### The last ungated verifier is gated

`verify_cross_state_money.py` — 125 → **139 figures**. The audit hard-gates **§Headline, §1, §3
and §F**, and names the owning script for each of **fifteen** remaining sections in
`COVERAGE_EXEMPT_SECTIONS`. One aggregate "583 unprobed" is now a per-section ledger, which is
the difference between a known gap and an unknown one. `TestEveryPaperGatesCoverage.UNGATED` is
empty.

**It justified itself on the first run: §1 and §3 are pure prose restatements of headline cells
and nothing pointed at them** — the same drift class that cost the donor paper four review
rounds. Fourteen figures added, all of them values `outflow()` already computed.

**Still open there, in priority order and recorded in the ledger:** §E's inflow layer (93
tokens, and the derivation already exists in `main()`); §5's per-cycle totals and §2's
population denominators, which need a Census population pin the way `acs_cvap_by_state.py` pins
CVAP; §K's state-disclosure layer (151 tokens, the largest); and §F's restatements of the donor
paper's validation and tier-switch figures, which belong as **cross-document** probes against
`donor-class-and-the-electorate.md` rather than re-derivations here — the pattern that caught
the stale +0.55 earlier the same day.

**The submission metadata and notes written earlier today were themselves corrected**, because
they said this paper had no coverage gate and quoted 583 unprobed tokens. Both were true when
written and false four hours later. That is the drift these documents exist to guard against,
found by the guard: `check_cross_doc_consistency.py` flagged the stale counts.

**Suite 1,997 passed / 7 skipped; infra 244; all eight paper verifiers exit 0. Series total
1,081 → 1,153 asserted figures.**

---

## 2026-08-06 (third pass) — the stale +0.55 in the money paper's satellites: CLOSED

Both entries above recorded this as open and author-owned. It is now fixed, on author
instruction:

| file | was | now |
|---|---|---|
| `money-votes-submission-metadata.md` | abstract: "correlates with candidate overperformance at **+0.55**" | **+0.58** |
| `money-votes-submission-notes.md` | objection heading quoted as *"You found **+0.55** and then explained it away"* | **+0.58**, now verbatim with the paper's Appendix A |

**The basis was re-enumerated before the edit rather than taken from the earlier entry**, which
is the standing rule after the 2026-08-06 white-paper incident. Against the pinned frame
(`docs/reference/overperformance_cells_2026-08-01.csv`) the correlation derives **0.5803**, which
`verify_money_votes.py` asserts as +0.58. The candidates ruled out: the retired 109-cell frame
(+0.55, and the paper's own pin note labels it retired); a different correlate row (+0.43
incumbency, +0.34 quality, +0.31 local trend — none is 0.55); a change in the 163-cell universe
(unchanged — what moved is the both-side-finance subset); a pinned-roll basis (inapplicable, the
figure is not roll-denominated); and rounding (0.5803 never rounds to 0.55).

**Checked for siblings before editing, and there were none.** The retired frame also moved three
fundraising-position means (+4.20 → +4.22, +2.37 → +2.32, −1.93 → −1.77). Neither satellite
quotes any of them, so +0.55 was the whole of the contamination. The paper's other two abstract
correlations, +0.43 and +0.34, did not move.

**The one surviving +0.55 in the document set is correct and must stay:** the paper's own pin
note at `does-money-move-votes.md`, which records the retired value in order to withdraw it.
That sentence is also precisely why `check_cross_doc_consistency.py` could not catch this — its
orphan check works by ABSENCE, and the figure *was* present in the paper. **The guard hole is
NOT fixed by this correction**, and closing it needs a design change: exclude a paper's
retirement-note spans from the text that grounds its satellites. Until then, a satellite figure
that a paper explicitly retires remains invisible to that check. Its own `--self-test` puts
recall at ~52% on one-decimal percentages against ~98% on counts.

`verify_money_votes.py` green (59 figures, three sections mapped);
`check_cross_doc_consistency.py` 0 findings.

---

## 2026-08-06 (fourth pass) — both independent ratings scored; A9x CLOSED

**Gate A9x is closed with nothing to bound.** The 204-record Idaho draw was rated by someone
other than the author under the blinded protocol and scored by `scripts/score_idaho_validation.py`,
written and committed before any verdict existed. **All 204 records rated Y — zero identity errors
in every stratum**, on the published convention and on both pre-committed sensitivities, including
the one that counts every `U` against the match. Three `partial_merge` ticks on the Idaho state
panel, reported separately as dollar attribution. The design's 10.2% per-party-stratum ceiling is
unchanged — it is a property of the draw, not the verdicts — and is now the operative bound rather
than a floor. §F7, Finding 3's heading and the release checklist are updated; the worst-case Idaho
figures (18.4% federal / 19.4% state) are the same numbers but now rest on a **measured** clean
Democratic stratum rather than an assumed one.

**The paper is no longer single-rater.** A third pass over the same 150 records by an independent
rater — confirmed by the author as a different person — supplies **inter-rater** reliability,
reported separately from the test–retest figures rather than pooled with them. The full-name block
is **75/75 Y in both** that pass and the first, so the primary specification is confirmed
unanimously by a rater with no stake in it. Agreement is **97.6% on the collapsed binary
(κ 0.935, PABAK 0.952)** and 76.0% on all four verdicts (κ 0.516). Appendix F's "an independent
rater … is not yet in hand" is retired.

**The most useful thing the pass produced is a bracket.** The author's re-rate diverged *more
permissively* than the published figure (95.7% donor-weighted); the independent rater diverges
*more cautiously* (91.0%). The published **93.0%** sits between them. Two repeat readings that
disagree with the original in opposite directions is much better evidence that the published
figure is not systematically optimistic than either reading alone.

**A correction to my own first draft of that prose, caught by deriving it.** I wrote "35 of the 36
disagreements run toward less certainty". It is **34**. The axis is *certainty*, not sameness:
`Y` and `NC` are both confident calls, so `NC → Y` is a substantive flip at unchanged certainty,
and `U → NP` moves toward *more* certainty. On a same-to-different ordering an `NC → NP` move
reads as gaining confidence, which is backwards. The classifier in `_d_rater2` now uses
`{Y: 2, NC: 2, NP: 1, U: 0}` and the comment says why.

**Two script bugs, both a change that did not propagate.** `--rater rater2` had never been
runnable: it died on `KeyError 'ai_verdict'` because the two key files name the prior-verdict
columns differently (`ai_verdict/ai_error_mode/ai_partial_merge` against `verdict/error/merge`).
And three references still used the module-level `LEDGER_OUT` after `--rater` was added, so the
run *reported* writing to the published 2026-07-27 ledger while correctly writing elsewhere — a
false alarm about a published artifact, whose obvious response is to restore something never
touched. Labelling was corrected with them: the output said "AI vs HUMAN", and **neither pass is
AI** (withdrawn in round 16; the author rated all 480 and every pass since). The label is now set
per run, and an unrecognised rater prints "reliability type unconfirmed" rather than guessing.

**The new figures are DERIVED, not exempted.** Appendix F's inter-rater block sits in `appf_tail`,
a section the coverage audit exempts — so ten result figures would have been asserted by nothing,
and that exemption's written reason (ceiling analysis plus a directionless survivorship note)
would have quietly become false. `_d_rater2` derives them from the committed PII-free ledger
`reference/match_validation_rater2_verdicts.csv` and eleven probes assert them. The exemption now
states explicitly that it does *not* cover them. Verifier **1,305 → 1,324 figures**.

### 🔴 A pre-existing defect A14 had never exercised: the public verifier could not run

`verify_donor_class.py` reads the submission memo, cover letter and metadata to extend its
section-less probes over them. All three are in `sync_public_repo.NEVER` and correctly never
travel — so in the public checkout the flagship verifier **crashed with FileNotFoundError**. The
repository shipped that script, and a paper telling readers to run it, and it could not run.

**This predates today** — the previously published copy references the memo identically — and it
had never been caught because A14's "run the verifiers there" step had only ever been exercised on
the other seven. Measured before fixing: exactly **six probes** target those documents, and they
are the only failures.

Absent is now empty rather than fatal, and those six probes are **skipped with a printed notice**
naming the documents. Skipping is right only because the documents are withheld *by design*; a
missing PAPER still fails loudly, because `PAPER` and `SUPPLEMENT` are not in the `_OPERATIONAL`
map. Public run: **1,305 figures, all assertions pass**, against 1,324 privately — the 19-figure
gap is exactly the withheld documents' probes, which is the honest number for a repository that
does not carry them.

Also: `.verify_cache/` was ignored privately but not publicly, and running the verifiers there
created it. Added to the public `.gitignore` before it could be committed.

**A14 verified: all eight verifiers exit 0 in the public checkout.** Suite 2,003 passed / 7
skipped privately at the point of the ELJ rebuild; the generated ELJ artifacts were regenerated
by `build_elj_submission.py` rather than hand-edited (abstract 287 words, body 11,370, no
anonymisation leaks).

**`docs/open-author-questions.md` now collects all six unresolved figure questions** in one place
with an `ANSWER:` line each, since they were spread across three verifiers and a corrections
ledger. It is in `NEVER`: it lists open defects in an already-public paper, and publishing that
before the answers exist invites a reader to treat unanswered as unanswerable.

## 2026-08-06 (fifth pass) — all six author figure questions ANSWERED and APPLIED

The author answered "fix" on every one of the six questions in `docs/open-author-questions.md`,
and all six are applied. Every one had the same shape — **a stated range or approximation that
no basis reproduced** — and the fix for each is the same in structure: the paper now states a
value that a derivation reproduces, and the **written exemption that held the question has been
replaced by a probe**. Series figure counts: WA 242 → **246**, NY 135 → **137**, ID 210 → **211**,
white paper 88 → **94**. All eight verifiers still exit 0.

**Enumeration first, edit second — the rule that came out of editing a correct paper earlier the
same day.** Every basis in every enumeration was recomputed before the figure was touched, not
read back from the previous session's comment. Two of the recomputations mattered: the white
paper's cross-state shares (WA 5.71 / NY 4.12 / ID 3.99 on the full roll) reproduced exactly,
and Washington's pinned roll (5.77%) and live roll (5.71%) were shown to print the *same* 5.7,
so the pin-versus-live axis could not have moved the chosen range whichever way it was answered.
The axis that could was active-versus-all registrants (4.0–6.2 against 4.0–5.7), which is why
the question put to the author named it explicitly.

| # | paper | was | now | how it is held |
|---|---|---|---|---|
| 1 | WA (POSTED) | 75+ off-year `16.8–18.3%` | `13.4–18.3%`, 2021 named as the low | probe on off-year min/max **and** a second probe on the two named endpoints |
| 2 | WA (POSTED) | recorded-female `53.0–53.1%` | `52.5–53.1%`, "rising from" replaced | probe on off-year min/max + the two that do rise |
| 3 | NY | 2025 under-30 `30.8 / 15.9` | `31.5 / 16.1`, basis named in the sentence | probe against §II's own convention (pinned active roll, age = 2025 − birth year, kind GENERAL) |
| 4 | white paper | `~3.5–6% of voters` | `~4.0–5.7%`, ID/NY/WA named | probe on the range **and** on its three members, from one derivation |
| 5 | white paper | `holdout R² ~0.00` | `0.02` | probe against the money paper's scraped allocation cell (0.022) |
| 6 | ID | 2024 cohort `263,315` | `263,322` | the count is now asserted like the other five cohort rows |

**Two of these are corrections to a POSTED paper (SSRN 7149263) and the posted artifact is
unchanged.** `who-decides-washington.md` carries the corrected sentences; the PDF and the SSRN
version do not, and per the batching decision they wait for the next revision round together
with the Appendix D → References and Appendix E rendering items.
`who-decides-wa-corrections-ledger.md` records C1 and C2 as applied-to-source, not-yet-posted,
and says plainly which two sentences now differ between source and the public version.

**Where a fix reached past the audited slice.** Finding 6's holdout R² is restated in the white
paper's Appendix B publication sequence, outside the findings slice the coverage gate can see —
the same blind spot the retired +0.55 hid in. It read "≈ 0" and would have stayed a rounding-down
claim after the finding itself was fixed. `_restated_outside_the_slice` now guards that figure
too, and prints its occurrence count so a wording change that disarms the guard shows up as a
failure rather than as silence.

**The satellites were updated with the papers, the same day.** `ny-submission-metadata.md` and
`-notes.md` and `id-submission-metadata.md` and `-notes.md` each carried the open question as a
blocking checklist item; all four now record the correction and what it was verified against.
A satellite that still called a resolved question open would be exactly the hours-old staleness
`check_cross_doc_consistency.py` was pointed at satellites to catch.

**What the enumerations bought, and why they are kept rather than deleted.** Each verifier keeps
its full basis table as a comment beside the derivation. For Idaho the enumeration is the evidence
that the *convention* was right and one cell was seven registrants wrong — the opposite of a basis
defect, and not something recoverable from the corrected paper. For the white paper it is the
record that the original basis is genuinely unrecoverable (the prospectus predates both the panel
split and the Idaho load), which is why the figure was restated on a current basis rather than
"corrected" to a reconstructed original.

### The money paper's §5 and §E gated — and §E's Senate paragraph was stale

`cross-state-fec-money.md` was gated over four of nineteen sections with the other fifteen
named-with-their-owner. The two the ledger called cheapest are now closed, and the verifier
goes **139 → 208 figures**, six sections hard-gated. Series total across the eight papers:
**1,226**.

- **§5 (the presidential rhythm) needed one `GROUP BY election_cycle`** on the filter
  `outflow()` already uses — the ledger predicted exactly that, and all eight of its dollar
  figures reproduced to the printed digit. A section can be unverified without being wrong.
- **§E (the inflow layer) imported the band logic** from `cross_state_common` rather than
  re-typing it, so the competitiveness definition cannot fork from the one
  `diag_inflow_vs_competitiveness.py` publishes. The House band table, its two aggregate
  claims and the Senate table all reproduced.

**Two defects in one Senate paragraph, both from a state being added after the sentence was
written.** It read "out-of-state share is high *everywhere* (41–54%) and is actually
**highest in safe NY (53.5%)**". That was a three-state statement. Idaho was loaded
2026-07-19 at **85.8%** out-of-state, and the paper's *own next bullet* calls Idaho "the
highest of the four" — so the paragraph contradicted the one after it. Second, NY's share is
**53.4978%**, which prints 53.5 at one decimal (the table cell, correct) but **53** at whole
percent; it was printed as 54 twice. The range is now scoped to WA/TX/NY and reads 41–53%.

**A superlative cannot be probed, so it is checked in code.** "The highest of the four" has
no numeric token for a regex to capture, which is precisely how it survived a coverage gate
whose unit is the number. `inflow_e()` now computes whether Idaho's share is the maximum and
the verifier fails if it is not. Worth generalising: the gate's blind spot is *claims about*
figures — ranges were the last one found, and superlatives are the same shape.

**Four §E tokens stay exempt, each naming its owner:** the donor-side 2.1× ratio (§D's, still
on the backlog), the two TX Senate results (election outcomes, not measurements), the $250M
order-of-magnitude restatement of an asserted $253.2M, and the earmark 15E/24T totals, which
the inflow table cannot re-derive because it carries no transaction-type column. Each was
checked against the other gated sections before being added, because a context-free literal
exemption applies document-wide.

**Still open on this paper**, in order: §2 (needs a Census population pin, the way
`acs_cvap_by_state.py` pins CVAP), §K (151 tokens, largest), the §A–§D and §G–§J follow-on
tests, and §F's donor-paper restatements as cross-document probes.

## 2026-08-06 (sixth pass) — the TX decision: *Who Returns the Ballot?* is a three-state paper

**Decided by the author: publish as three states; Texas becomes named future work.** The
earlier draft carried a four-way design with TX "deferred (not yet loaded)", which is a
placeholder wearing the clothes of a plan. Three things drove the decision, and they are
recorded here because a scope choice that is not written down gets re-litigated:

1. The paper's claim is about **the gradient within each state's own salience ladder**,
   harmonized on the two directly comparable classes. Three states already vary both
   institutional axes the design turns on — whether the state records party of record, and
   whether its decisive contest is open to every voter.
2. **A primary-history proxy is not party of record.** Slotting Texas in as a fourth column
   would put two different measurements in one row; it needs its own validation, which makes
   it a next paper rather than a fourth case.
3. The binding constraint on this batch is the **human-verification gate on five unposted
   papers**, not analytical coverage.

**What changed in the paper.** The Texas row is out of The cases table, replaced by a
statement of which axis the set does *not* vary. The third research question is now marked
*not answerable here*, with the reason — Washington is the set's only no-party-registration
state and its top-two primary records no party ballot, so the question is not merely
unanswered but unanswerable with this data. Boundary of inference carries Texas as future work
with what it would add named precisely, so a reader can price its absence instead of
discovering it. Finding 2 is stated as a claim about **party-registration states**, which is
what the data supports. The verifier still passes at 74 figures with all five sections mapped.

**Two satellites written and registered the same day** — `who-returns-ballot-submission-
metadata.md` and `-notes.md`, added to `check_cross_doc_consistency.py`'s pairing table in the
same commit, per the rule that came out of a money-paper satellite going stale within hours.
Both are in `sync_public_repo.NEVER` as operational. The paper's own PENDING entry was
**rewritten rather than ticked**: its release condition was "release when the TX decision
lands — load, or a documented proxy section", and neither happened. The decision was to scope
the paper instead, so the condition is *spent*, not met. Whether a pre-human-gate draft
travels to the public repo is left to the author; New York and Idaho do, on the same footing.

**Group registration carries a caveat worth stating.** `verify_who_returns_ballot.py` grounds
Findings 1 and 3 against the harmonizer's recomputation but Finding 2 against the three
single-state **papers' prose**, so a figure this group calls "verified" is, for Finding 2,
verified one step removed. That is the weaker case the `Group` docstring already describes,
and it is recorded in the entry rather than glossed.

### Three stale satellite claims found while doing it

None was in scope; all three were false when read.

- **`money-votes-submission-metadata.md` said the paper has "no dedicated verifier".**
  `verify_money_votes.py` was written 2026-08-01 and asserts 59 figures under a coverage gate.
  The sentence was three defects out of date the day it was written — building that verifier
  found five stale Finding 1 figures on a live frame and two overstated claims about the IE
  record. Corrected, with the correction visible rather than silent.
- **The NY and ID notes both described the synthesis as a draft that "transcribes rather than
  recomputes" with "its harmonised-metrics section unbuilt".** True until 2026-08-06, false
  after the harmonizer landed that morning.
- **`verify_who_returns_ballot.py`'s own docstring still said it "opens no database"** three
  paragraphs after explaining that it now opens three through the harmonizer. Corrected rather
  than deleted: a stale claim about data handling is the kind that gets believed.

**And one maintenance trap closed.** The cross-doc allowlist enumerated verifier figure counts
(`88|125|135|210`) behind an "of them" needle. Four of those moved in a single day, so the
enumeration failed loudly for the right reason and the wrong cause. It is now the category —
any count behind that needle — which is what the neighbouring "figures" and "tests" waivers
already were. Series figure counts after this pass: WA 246, NY 137, ID 211, safe-seat 197,
money-votes 59, cross-state money 208, white paper 94, who-returns-ballot 74.

## 2026-08-06 (seventh pass) — who owns a satellite's figure count

**The question this answers: how do you stop a submission document from stating a figure
count the verifier no longer produces?** The count is the sentence that reaches a journal
form — "asserts **211 figures**" — and on 2026-08-06 three of them were wrong at once: the New
York satellites said 135 against 137, Idaho's said 210 against 211, and the cross-state money
data-availability statement said **125 against 208**.

**Why the cross-doc checker could never have caught it.** Its orphan pass asks "does this
number appear in the paper?" A verifier's figure count is a property of the RUN and appears
nowhere in the paper, so it is absent by construction and an allowlist waives it. The waiver,
not the check, was carrying seven of the eight papers — by not looking.

**The intermediate fix that looked like a fix.** The allowlist ENUMERATED the counts it waived
(`88|125|135|210`). A changed count therefore failed the checker — loudly, for the right
reason, at the wrong layer: it reported a *correct* document as unguarded rather than a stale
one as stale, and four of those counts moved in a single day. Widening it to the category
stopped the false alarms and widened the blindness. Neither direction is a fix, because the
orphan pass is structurally the wrong instrument for this class of claim.

**The fix: the verifier owns it.** `_verify_prose.audit_satellite_counts` compares every
present-tense count claim in a paper's registered satellites against the figure count that run
just produced, and fails the verifier. The verifier is the only thing that knows the number, it
already runs in every pre-upload checklist, and the check costs nothing. On its first run it
found the 125-against-208. Seventeen claims across seven papers are now checked at the moment
the count changes, which is the one moment somebody is looking.

**Three design points, each of which bit or nearly bit:**

1. **Whitespace must be `\s+`, never a literal space.** These files hard-wrap at 96 columns, so
   any two words in a claim can be split by a newline — and by `> ` inside a blockquote. The
   first version used literal spaces and reported "no claim found" for safe-seat, whose
   sentence wraps between "asserts" and "**197 figures**". A silent downgrade from checked to
   unchecked is the exact failure the guard exists to stop.
2. **Only PRESENT-TENSE claims are checked.** A checklist line recording what a past run
   produced ("Verifier 125 → **139 figures**") is history and must keep saying what it said —
   the rule the corrections ledgers and this log already live by.
3. **A missing satellite is a SKIP with a notice, not a failure**, because all of these files
   are in `sync_public_repo.NEVER` and the public checkout legitimately has none of them. A
   test asserts the registered names exist in the private tree, so the skip path cannot double
   as cover for a typo.

`TestSatelliteCountsAreOwnedByTheVerifier` locks in all of it: every series verifier calls the
guard, its result reaches the exit status, `stats_out=` is passed so it has a count to compare,
every paper is registered (an empty tuple is a valid answer — the white paper is a prospectus
with no submission metadata), and every registered satellite exists. The probe-count ratchet
was raised to the counts measured today: WA 246, NY 137, ID 211, cross-state money 208, white
paper 94, money-votes 59.

**Two more gate descriptions were false, both found by pointing the guard at them.**
`safe-seat-submission-metadata.md` named only `diag_seat_competition.py` and never mentioned
`verify_safe_seat.py` or its 197 figures. `submission-metadata.md` (the posted WA paper's)
said "every figure is reproduced from scratch" without a count, so there was nothing to check.
Both now state the count, and both are checked.

**And the donor paper's own counts were stale in four documents** — 1,305 against a build of
1,324, plus a body word count of 11,337 against 11,370. These are A10's input, so they are
corrected rather than left for the sign-off to trip over. The methods supplement now also
explains the 1,305: it is what the PUBLIC checkout produces, where the memo, cover letter and
metadata are withheld by design and their six probes skip. The 19-figure gap is exactly those
six probes, and a missing *paper* still fails.

**Measured after the seventh pass.** Full suite **2,030 passed / 7 skipped** (the 7 are the
opt-in SoS network endpoint tests). All nine verifiers exit 0 — donor 1,324, WA 246, NY 137,
ID 211, safe-seat 197, money-votes 59, cross-state money 208, white paper 94,
who-returns-ballot 74; series total **1,226**. `check_cross_doc_consistency.py` reports
**0 findings** for the first time: every stated build count matches the build, and no satellite
states a figure the verified documents do not. The six findings it carried at the start of the
day were the donor counts corrected above.

---

## 2026-08-08 — New York external review: a repair that broke a denominator, and five other defects

An outside reviewer read `who-decides-new-york.md` and returned twelve objections. Ten hold in
some form. The largest finding of the round is not among them: it was found while checking the
reviewer's arithmetic, and it is that **the 2026-08-01 recomputation of §III introduced the
defect it was correcting for, and recorded a mechanism the artifacts do not support.**

### The denominator, and why the paper was right before it was fixed

A participation rate is voters over the people who *could* have voted — active registrants
enrolled on or before the contest. On 2026-08-01 §II and §III were recomputed against the
whole current active roll instead, which counts a 2025 registrant as a 2021-primary
non-voter. **20.55%** of the active roll registered after the 2021 primary. Restoring the
cutoff raises the eight major-party primary cells by **+0.13 to +2.67 points** and §I's
under-30 pair from 31.53/16.07 to **32.84/16.63**.

Three checks, all now derived in the verifier rather than argued:

1. The contemporaneous basis reproduces the figures the paper carried *before* 2026-08-01 —
   **16.9** and **17.9** — exactly, on two independent cells.
2. Roll growth explains none of the gap. Pinned and live rolls both return the uncorrected
   **14.26%**, to the last digit. The recorded mechanism ("the file has grown") cannot be what
   moved those cells.
3. `diag_ny_primary_participation.py` — named in the paper's own Methods block as §III's
   provenance — has applied the cutoff since its first commit and was never edited. So the
   paper and its cited script disagreed by up to 2.67 points for a week, **and both are
   published in the public reproduction repo**, where a reader following the Methods block
   would have hit it. `ny-turnout-by-party-age.md`, generated from that script, carried the
   correct figures throughout.

Two rules come out of this, and they are the reason the round is logged at length.

**When a paper and a verifier disagree, the verifier is not automatically right.** The existing
convention — *fix the paper or fix the derivation, never the tolerance* — is silent on which of
the two is wrong. Here it was the derivation, and the paper was edited to match it.

**A caveat carrying a number is a result, and must be probed.** The 2026-08-01 note explained
itself in prose the coverage gate could not reach: "the roll has grown" is a sentence, and no
assertion can contradict a sentence. Its figures were held by six literal exemptions on the
reasoning that a delta against a vanished roll state cannot be re-derived. It could — by
dropping the cutoff. All six exemptions are deleted and the uncorrected values are now derived
(`raw_*`), so the replacement note is asserted end to end.

### What the pin actually froze

`ny_paper_roll` carried party, birth year and active status but **not** registration date, so
the correct denominator was unavailable to the verifier by construction. Re-pinned 2026-08-08
with `registration_date` (100% populated; 0 nulls). The re-pin is **value-identical** on every
column it already carried — verified by fingerprinting party × active-status × birth-year
aggregates before and after — because the new field was *appended* to the `MIN(STRUCT_PACK(…))`
tie-break key rather than inserted into it, so it can only break ties the old key resolved
arbitrarily among identical triples.

### The reviewer's other objections

| # | Objection | Disposition |
|---|---|---|
| 1 | Party of record is 2026 party, not party at the election | **Holds.** Unrecoverable from one extract — the loader reads a single `enrollment` field and the 47-field layout carries no enrollment history. **Bounded rather than conceded**: a closed primary admits only enrollees, so 0.7–1.4% of each primary's voters being blank today caps drift *out of* the major parties at well under half a point a year among primary participants. D↔R movement is unbounded and is now disclosed as such in the front matter. |
| 2 | "Composition shares are robust / bias hits every group equally" | **Holds — replaced with a measurement.** Using inactive status as the visible pre-purge state: across parties the spread is 0.35pp (3.23–3.58% among 2021 voters), which supports within-year cross-party comparison. Across age it does not hold — 2.69% of the under-30 band against 1.34% of 45–64 — so age shares **understate** youth in past electorates. Disclosed because it runs against the headline. |
| 3, 4 | Post-election registrants in the 2025 and primary denominators | **Holds — this is the denominator defect above.** |
| 5 | "The primary is the election" repeats the withdrawn safe-seat inference | **Holds, and it was the stronger error.** Safe-seat withdrew "decided before November" on *observed margins*; NY asserted it on *registration*, which is weaker evidence. §IV retitled "The registration map", the inference withdrawn, and the seat-tracing test that would settle it named as future work. |
| 6 | Chapter 741 makes the conclusion outdated | **Holds, and more strongly than stated.** Not "partially done": effective 2025-01-01, upheld unanimously by the Court of Appeals in *County of Onondaga v. State of New York* (2025-10-16), cert denied 2026-03-23, federal challenge dismissed 2026-06-29, first operative cycle 2026. NYC and the constitutionally-fixed offices are excluded. Rewritten as the paper's ending: the 2023 and 2025 electorates are the **pre-transition baseline** for a live natural experiment. |
| 7 | "Largest state whose voter file records party" | **False; deleted.** California 23,155,447 and Florida 15,042,734 both record party, DOB and vote history against New York's ~13.5M. Note the fallback also fails — Florida is a closed-primary state and is larger — so there is no narrowing on size, and none was attempted. |
| 8 | Asymmetric competitiveness bands | **Holds, and symmetrising favours the paper.** Was 40+/20–40/5–20 on the D side against 5–20/20+ on the R. **No New York district at either level is R+40**, so on the same threshold that makes 64 seats safe for Democrats, none is safe for Republicans; the old table showed seven. The ±5 count — the actual finding — is unchanged at 21 of 176. |
| 9 | Citation conflates two papers | **Holds.** Huber, Meredith, Morse & Steele, *Science Advances* 7(8):eabe4498 (2021) is the list-maintenance-errors paper; Feder & Miller, *American Politics Research* 48(6):687–692 (2020) is "Voter Purges After *Shelby*". Zero shared authors. Both now cited, and Feder & Miller is the apter one for differential attrition. |
| 10 | "The young choose not to vote off-cycle" is causal | **Holds, and the paper's own table refutes the premise.** 2023 turned out 2,336,272 voters at 41.6% aged 65+; 2025 turned out 4,039,285 — **1.73×** — at 34.4%. "Odd year" is a bundle, not a treatment. Narrowed to consistency with the literature; Chapter 741 named as the design that would identify it. |
| 11 | The pin does not cover §IV, §V or Appendix A | **Holds.** Adopted the reviewer's fix rather than more pinning: the dated FOIL extract is now identified in the paper — `ALLNYVOTERS20260629.zip`, 928,142,538 bytes, SHA-256 `ea0b97cc…4807` — which covers every section that reads the file directly, without redistributing restricted data. The byte count is asserted live against the file on disk; the digest carries a written exemption naming the one-line command that reproduces it. |
| 12 | Six claims overstated | **Five hold and are narrowed** — "not high-information independents" (never measured; removed), "least likely to donate" to lowest rate of appearing in matched contribution records, "abandoning party labels" to recent cohorts less likely to enroll, "what no survey-based design has shown" to "what we have not found shown", "locked out" to ineligible while unaffiliated, with the February re-enrollment deadline stated. **One does not hold**: the donor gap is not an artifact of the full-name match key, a fair worry since that key discards younger donors and NOPARTY is the youngest bucket. Measured on both panels — NOPARTY-to-DEM 0.412 on the current panel against 0.375 on the retired all-tier one. It widens. Now a probed footnote. |

### State after the round

`verify_who_decides_ny.py` asserts **179 figures** (was 137), coverage fully mapped across all
eight audited sections, exit 0. Every figure introduced by this round is probed, including the
correction's own before-and-after values. The satellite count guard caught all four stale
restatements of the old total, which is the behaviour it was built for.

**Still open, and it is the fork the reviewer named:** individual party enrollment at the time
of each historical election cannot be recovered from a single extract. NYSBOE publishes
aggregate enrollment by county, Assembly, Senate and Congressional district twice yearly back
to at least 2006, split active/inactive, which is the external validation target — the paper's
own file gives DEM 48.99 / REP 23.50 / NOPARTY 22.61 / OTHER 4.90 among actives registered on
or before 2021-02-14, and the gap against NYSBOE's February 2021 publication is the combined
party-drift-and-differential-survivorship signal. Not yet incorporated; `elections.ny.gov`
blocks scripted fetches, so it needs a browser-driven or manual pull.

### Appendix C added the same round: the external validation, and what it settles

The open item above was closed the same day. NYSBOE's published enrollment series was pulled for
five snapshot dates and compared against the file, giving the paper a new **Appendix C**.

**The control row is the reason to believe the rest.** At 2026-02-20 — about four months before
the extract — the gaps between published shares and the file's are -0.26 to +0.33 points. A
mis-specified method (wrong active filter, wrong party bucketing, wrong denominator) would show
up there, and it does not.

| Snapshot | DEM | REP | NOPARTY | OTHER | file/published actives |
|---|--:|--:|--:|--:|--:|
| 2026-02-20 (control) | -0.17 | +0.10 | -0.26 | +0.33 | 98.08% |
| 2025-11-01 | -0.17 | +0.10 | -0.24 | +0.31 | 96.63% |
| 2024-02-27 | -0.34 | +0.57 | -0.16 | -0.07 | 91.89% |
| 2022-02-21 | -1.02 | +1.15 | +0.20 | -0.33 | 84.89% |
| 2021-02-21 | -1.06 | **+1.39** | +0.11 | -0.44 | **78.64%** |

Three results, and the second is the one to carry forward.

1. **The combined drift-plus-survivorship bound is 1.39 points**, five and a half years back.
   Gaps grow monotonically with lookback, which is what the mechanism predicts and a coding
   error would not.
2. **The direction runs WITH the paper's headline, so it is a caution and not a comfort.** The
   surviving sample under-represents Democrats and over-represents Republicans at every
   historical date, so a 2026-labelled reconstruction makes past electorates look slightly more
   Republican — and §I's finding is that the Republican electorate ages hardest. It is an order
   of magnitude smaller than the effects §I reports (1.39 points of share against an eight-year
   median-age gap), and it is why §I leads with within-party median age and 65+ share rather
   than with the parties' relative sizes. Stated in the paper in those terms.
3. **Attrition is large and composition is not.** Only **78.64%** of the registrants NYSBOE
   counted active in February 2021 are active in this file — over a fifth of that roll is gone —
   yet composition moved at most 1.39 points. That is the evidence the retired word "robust"
   was asserting without.

What it does not do is recover any individual's party at a past election. Aggregate enrollment
validates composition; it cannot close the reviewer's fork. That remains genuinely open.

**Mechanics worth keeping.** `elections.ny.gov` returns 403 to every scripted client, including
a browser-User-Agent urllib request, so the workbooks were read through the in-app browser: the
`/voters-registered-county-<date>` URLs serve .xlsx directly, and the zip was parsed in-page
with `DecompressionStream('deflate-raw')` to pull the "Statewide Total / Active" row. Two traps.
The 2024 workbook uses **unprefixed** SpreadsheetML tags where the others use `x:`, so a parser
anchored on `<x:row>` returns zero rows and looks like an empty file rather than an error. And
the published constants live in ONE place — `scripts/diag_ny_enrollment_validation.py` — which
`verify_who_decides_ny.py` imports rather than transcribing a second time; two hand-typed copies
of an external constant is a drift this series has already been bitten by more than once.

`verify_who_decides_ny.py` now asserts **210 figures** across nine audited sections, all
coverage mapped, exit 0.

**One more stale artifact, found by sweeping rather than by the gate.** The paste-ready SSRN
abstract in `ny-submission-metadata.md` was still the pre-round text — superlative, "least
donating", "in most of the state is decisive", the old competitiveness phrasing. The verifier
scrapes the PAPER, so a stale copy of the abstract in a satellite is invisible to it, and the
orphan check could not see it either because every number in it still appears somewhere in the
paper. It is corrected and now carries an instruction to edit both copies in one action. **This
is a real gap in the gate**: a satellite that restates prose rather than figures is unchecked.

## 2026-08-08 (second pass) — the money paper: a 2x data defect, a backfill, and a sign that reversed

`does-money-move-votes.md` had every independent-expenditure figure inflated by roughly a
factor of two, and the defect was invisible to every check this series runs. Fixing it made
the paper's own prescribed backfill cheap, the backfill reversed the sign of its headline
coefficient, and the correction chain reached the white paper's Finding 6. The verdict —
*cannot confirm or refute* — is the one thing that survived unchanged.

### FEC files most independent expenditures twice

The same expenditure appears as a 24/48-hour notice (Form 24) and again on the committee's
periodic Schedule E (Form 3X), under different `sub_id`s. Nothing about the pair looks
duplicated: different ids, different filing dates, different forms. The loader pulled both
and summed them.

Measured against FEC's own `schedules/schedule_e/by_candidate/` aggregate, every Washington
House candidate checked came out at **2.0–2.2x**:

| candidate | FEC's aggregate | loaded | ratio |
|---|--:|--:|--:|
| H2WA03100 | $11.75M | $24.91M | 2.1x |
| H2WA03217 | $6.56M | $14.55M | 2.2x |
| H2WA04165 | $2.00M | $3.98M | 2.0x |
| H4WA06117 | $2.68M | $5.56M | 2.1x |

The mechanism is exact rather than approximate: H2WA03100's 2024 Schedule E holds 223 rows,
**132 with `is_notice=false` and 91 with `is_notice=true`**, and the 132 sum to $11.78M
against FEC's $11.75M — the three-cent-scale gap being seven `memo_code='X'` subtotal rows.

**Why no internal check could have caught it.** Every figure derived from the contaminated
table agreed with every other figure derived from it. The verifier's probes passed, the
coverage audit passed, the cross-document consistency check passed. A doubling that is
uniform across a table is invisible to any test that compares the table to itself. It took
an external source — first FEC's per-candidate aggregate, then its bulk files — and the
reproduction path added this round exists because of that: `diag_fec_ie_bulk_crosscheck.py`
reconciles loaded totals against FEC's public bulk downloads and **needs no API key**, so it
does not share the warehouse's assumptions and a reader can run it.

### A truncation that had been silently discarding the earliest spending

`max_per_candidate` defaulted to 200. WA-03 2024 has 223 periodic rows, so the cap bound —
and because the fetch sorts `-expenditure_date`, the discarded rows were the **earliest**,
which is precisely the axis the early-versus-late spending split the paper contemplates
would need. The row count simply read 200 and nothing said otherwise. The default is now
uncapped; a binding cap warns and is reported in the loader's return value.

### The backfill the paper prescribed, and what it did to the finding

With the double-count fixed, the 2018/2020/2022 Schedule-E backfill — which the paper called
"the single highest-value data acquisition remaining in this series" and framed as a
rate-limited API job — was run. **It took about five minutes.** The cost framing was wrong;
the difficulty was always the de-duplication, and the paper now says so.

The panel went from one scorable cycle to five cycles, 2,215 countable rows and $75.7M, all
five reconciling exactly to FEC's bulk `pas2` files. `diag_ie_vs_margin.py` crossed its own
`MIN_N_FOR_SLOPE=10` floor and began reporting inference:

| | before (n=7, 2024 only) | after (n=34) |
|---|--:|--:|
| slope | **−0.39** pp per $1M net pro-D IE | **+0.515** |
| Pearson r | −0.39 | +0.186 |
| 95% bootstrap CI | withheld | [−0.600, +2.821] |

**The sign reversed.** The paper had predicted exactly this in its own words — *"at n = 7 the
sign flips on a single race"* — and then reported the n=7 sign anyway, as "the textbook
endogeneity signature". Both readings are consistent with the truth, which is that the
interval is the only honest summary at these sample sizes. The conclusion is unchanged
because the interval still spans zero; everything supporting it was rewritten.

### The superlative was manufactured by the defect

The paper called WA-03 2024 "the most IE-saturated House race in the country". Against FEC's
national bulk file it ranks **22nd of 387** House races drawing any IE, behind CA-45 at
$34.46M. But at the doubled $40.1M, **no race in the country exceeded it** — so the
double-count did not merely inflate the claim, it created it. This is the second superlative
in the series to fail on checking (after §E's "highest of the four" in the cross-state
paper), and the shape is identical: a claim about figures, with no token a numeric probe can
capture.

### What was rewritten

Finding 3 is retitled **"The test runs now, and is still underpowered"**. The limitation
changed in kind — not missing data, but an interval too wide to sign — and that reframing
propagated to the subtitle, the abstract, Finding 2c's heading, two rebuttals, the
limitations, the methods, and Appendix E (one cycle → four, 40 rows). The white paper's
Finding 6 was rewritten in step. Retired figures are stated in correction notes and asserted
as historical literals, the same pattern as the pinned Finding 1 correlations — a correction
that quotes a figure the data no longer supports is worse than the error it corrects.

### Three gate gaps, all closed

Every numeric probe passed throughout this episode while the sentences built on them went
false. That is the finding of the round, not an aside.

1. **Spelled-out numbers are invisible to the gate.** The abstract's "exists for a single
   cycle and seven scorable Washington races" carried no digit for a probe to capture or the
   coverage audit to demand. `verify_money_votes._claim_checks` now parses the spelled-out
   cycle count against the derived one, and blocks the superlative from returning.
2. **The cycle inventory derived only the cycles that happened to be on disk** (2024 and
   2026), so after the backfill the paper's table was three rows wider than anything asserted
   against it. It now derives every cycle in the panel.
3. **A diagnostic stated its own data inventory in a hardcoded string** and went on
   announcing "2024 only (~7 WA House races)" beneath a four-cycle table. Derived now. A
   script that narrates its inventory cannot notice when the inventory changes — the same
   defect the verifiers exist to catch in prose, one layer down.

A fourth is structural and worth naming: **the warehouse holds no out-of-state IE**, so any
"most expensive race in the country"-shaped claim is unfalsifiable from in-repo data.
`diag_fec_ie_bulk_crosscheck.py --national-rank` now owns that class of claim.

### An unrelated credential exposure, found by running the load

`httpx` logs every request at INFO as the full URL, and the FEC API takes its credential in
the query string, so `main.py load --fec-ie` printed a **live API key several hundred times**
— to the terminal, to any redirected log, and into the session transcript. `httpx` and
`httpcore` are now raised to WARNING, pinned by
`tests/test_infrastructure/test_no_credential_logging.py`. Silenced rather than redacted: a
redacting filter must enumerate every parameter name that is ever secret and is wrong the
first time a loader adds one. **The exposed key has been rotated** (owner, 2026-08-08), which
closes the exposure; the logging fix is what stops it recurring.

### State after the round

`verify_money_votes.py` asserts **76 figures** (was 59), coverage fully mapped across
Findings 1–3, exit 0. `verify_whitepaper.py` exit 0. Full suite 2,048 passed. All five IE
cycles reconcile to FEC's bulk files at 0.0%. Committed as `3d3db52`.

**Still open.** The rewrite was a figures-and-framing revision by an assistant; the DRAFT
markers stand and the human sign-off in `money-votes-submission-notes.md` §Sign-off has not
been done. The early-versus-late spending split and the next-cycle placebo are now runnable
for the first time and are the obvious next tests — neither was attempted this round.

### §V's "new registrants" was the wrong label, and measuring it strengthened the finding

Drafting the FOIL request surfaced a defect in §V that has nothing to do with the Board.
`registration_date` is the most recent registration TRANSACTION, not an original registration:
**3.16%** of 2021 primary voters carry a registration date *after* the primary they voted in,
which is only explicable as re-registration. §V read `year(registration_date)` as "new
registrants".

The test is exact rather than inferential. Voting requires being registered, so a cohort member
with a participation record predating their own `registration_date` was registered earlier. On
that test **at least 9.96% of the 2020 cohort and 13.91% of the 2024 cohort are
re-registrations** — lower bounds, since a re-registrant who never voted before leaves no trace.

**Those two percentages are not comparable to each other**, and the paper says so, because
otherwise they read as a rise. 2024 has an eight-year detection window against 2020's four. The
2008 and 2016 rows cannot be tested at all: this file's vote history begins in 2016, so a
computed "0.00%" would be an artifact printed as a fact. The verifier does not compute them.

**The bias runs against the finding, which is what makes this a clarification rather than a
correction.** In the 2024 cohort, re-registrants are **48.9%** Democratic and **25.1%** no-party
against **38.2%** and **37.3%** for the rest, at a median registration age of 38 against 28.
They pull the printed figures toward the party column and away from the blank one, so the
genuine first-time trend is *steeper* than §V's table shows, not shallower.

**The table stays on the whole-cohort basis, deliberately.** Splitting only the two testable
rows would publish a four-row table on two different bases — a worse defect than the imprecision
it fixed, and the same shape as the tier/panel confusions the donor paper has already been
burned by. §V is relabelled "registration cohort", the measurement is stated inline, and every
figure in it is probed.

Also worth recording: this is the second defect in this paper found by *drafting a document
about it* rather than by running a check. The first was the paste-ready abstract, found by
sweeping the satellites after the gate went green. Neither was reachable by the coverage gate —
one because a satellite restating prose carries no unmapped token, the other because "new
registrants" is a label, not a figure. **The gate cannot see a wrong noun.**

`verify_who_decides_ny.py`: **219 figures**, nine sections coverage-mapped, exit 0.

### Also this round: the suite now fails fast on a locked warehouse

A `load --fec-ie` backfill in a second terminal took an exclusive lock on
`data/wa_statewide.duckdb` mid-suite, and every module-scoped read-only fixture failed at setup
— **3 failures and 39 errors** across `test_reports/`, none real. CLAUDE.md already records the
same shape costing ten minutes and producing a false regression report.

`pytest_sessionstart` now probes each warehouse database read-only and aborts with one sentence.
It does **not** enforce "never touch data/ while the suite runs" — nothing in-process can, and a
scheduled job or a second terminal will always win the race. It removes the misleading failure,
not the collision. Session start only; a missing database is not an error.

One trap, caught by its own test: the lock markers must be PHRASES, not the bare word "lock".
DuckDB puts the full path in its message, so any checkout or temp directory containing "lock"
reads as a conflict — which fired immediately, because pytest names `tmp_path` after the test
function and the test is called `test_a_non_lock_error_is_not_reported_as_a_lock`. That test now
asserts its own path carries the trap, so a rename cannot silently remove the coverage.
`scripts/refresh_sos_results.py` still carries the looser list; there a false positive only
defers a load, which is harmless.

Verified both ways against the real warehouse: clean run unaffected, genuine cross-process write
lock aborts with exit 4 and no spurious errors. On Windows the conflict arrives as a plain
`IO Error`, not anything catchable by exception type.


---

## 2026-08-08 (third pass) — the AI data-handling claim asserted more than could be verified

**The defect.** Four submission documents and the ethics assessment carried an unqualified
negative: *"No individual-level voter, contribution or linkage record was submitted to any hosted
AI service."* On 2026-08-03 the `cure-list` and `chase-list` commands were found to print a
preview block of individual voters — name, precinct, rejection reason — to standard output, which
an agentic session returns verbatim; roughly 41 voter rows across five runs. The claim was false
from that date. The tooling is campaign GOTV software, feeds no figure in any paper, and no
published output contains those rows, but the sentence did not say so.

**Two things were wrong with it, and the second is the one worth keeping.** The first is the
factual error. The second is that *no version of that sentence was ever verifiable.* It asserts
the complete absence of an event across many sessions, with no log to audit — and the author's
confidence in it was formed under a mistaken model of the mechanism, since the preview went
unnoticed precisely because it looked like a local terminal display. Confidence formed that way
does not transfer to "and there were no others." **Scoping the claim to the paper, or qualifying
it with the known exception, would both have left an unverifiable negative at the front of the
sentence.** Both were drafted and both were rejected for that reason.

**The fix inverts what is claimed.** The submission documents now assert only what is checkable
by reading the code — what assistance operated on, and that the restricted files, contribution
tables, linked panels and validation evidence are not analysed through a hosted service — then
name the one known instance in a clause and point to the data-use assessment for the account. The
cover letter's trailing clause was deleted outright rather than reworded: that sentence's logic
was that the adjudication was single-rater and the matcher deterministic, and the data-handling
claim had been bolted onto a "so" that never carried it.

**A second reason to move the discussion, raised by the author.** A data-handling-to-hosted-model
clause is not a standard element of journal AI disclosure — SAGE, Elsevier and ICMJE ask for the
tool, the use, and the authorship affirmation. It is justified here because the inputs are
restricted voter files. What was not justified was *"Because the tooling does not enforce this,
it is a statement of practice rather than a technical control"* sitting in a title page: an
unprompted admission in a vocabulary reviewers have no frame for, which reads as unusual rigor to
one reader and as a flag to another. That discussion belongs in the assessment, at length, and
now lives only there.

**The ethics assessment row is rewritten rather than annotated**, and its header changes from
*"Implemented as practice, not as a technical control"* to a control for the enumerable shapes
and practice for the rest. Two layers now stand where a standing instruction stood alone: the
previews are withheld unless `--preview` is passed, and a `PreToolUse` hook refuses the dangerous
command shapes at the session level — harness-executed, so it holds against intent rather than
relying on it, which is the distinction that row is about. Both are locked in by
`tests/test_infrastructure/test_person_level_stdout_guard.py`. The round-15 entry withdrawn
earlier is a *different* claim about AI adjudication and stays withdrawn.

**The title page is generated.** `docs/donor-class-elj-title-page.md` carries a do-not-edit-by-hand
header; the edit went into `scripts/build_elj_submission.py` and the file was regenerated.
Editing the artifact would have survived exactly until the next build.

**A10 is not reopened.** The 2026-08-08 signature covers 1,324 figures over 48 sections, and a
disclosure sentence carries no figure — the verifier and the cross-doc checker were both checked
and neither anchors on this text. Recorded here so the sequence is legible rather than inferred.
**Where this change actually landed, recorded because the commit messages do not say.** It was
one edit across six files in two halves, and neither half is committed under a message that
describes it. The builder hunk — `scripts/build_elj_submission.py`, which regenerates the title
page — is in **`64ed221`** ("ADAPTED must report drift..."). The five documents and this entry
are in **`43e889b`** ("PDC C-6 audit..."). Both commits are about the independent-expenditure
work and mention none of this. Nothing is lost and the content is complete, but `git log` on the
disclosure wording leads to two unrelated subjects, so the mapping is written here instead.
Verified at `43e889b`: the retired sentence survives nowhere under `docs/` except as the
quotation above.

---

## 2026-08-09 — Adversarial review program, round 1: `who-decides-washington.md`

**Why this round exists.** Two adversarial reviews of `safe-seat-washington.md` and two of
`does-money-move-votes.md` each found real defects that no gate caught, and the second
money-paper review overturned a central claim (the "$70.6M WA IE data ceiling" was our ETL,
not Washington's disclosure regime — `pdc-c6-direction-audit.md`). The verifiers assert
~2,350 figures and are strong on exactly one axis: does the number in the paper match the
number in the database. They are blind to four other classes — a claim *about* figures, a
wrong noun, a pipeline property asserted as a property of the world, and a check that cannot
fail. **Five of the nine papers had never had an adversarial pass, and this one is the only
paper on SSRN (7149263).** So it goes first.

**Method.** A fresh reviewer agent, given the paper, the verifier and read access to the
databases, and deliberately **not** given the audit log, the corrections ledger or the
reviewer-response file — anchoring a reviewer to defects already found is why an in-house
pass under-performs an outside one. Every finding was then re-measured here before anything
was edited. That step earned its keep twice this round (below).

### Confirmed defects, with what the measurement changed

| # | claim | verdict |
|---|---|---|
| 1 | "2021 and 2023 carried only the state's non-binding tax advisory votes" | **False for 2023.** Zero 2023 general races reach statewide precinct coverage, against three in 2021 and one in 2025; advisory votes were repealed by SB 5082 (eff. July 2023). The ballot-content variation the sentence downplays is *wider* than claimed: three items, then none, then one. |
| 2 | "turnout accounts for **92% (2025), 95% (2023), and 79% (2021)** of the 65+ rise… and in 2021 and 2023 the roll effect is actually slightly negative" | **Self-refuting, and two quantities under one name.** rate / rise is 92.0 / **105.9** / **134.8**%; the printed 95 and 79 are abs(rate)/(abs(rate)+abs(roll)). A negative roll effect *requires* the share of the rise to exceed 100%. Also the 2021 roll effect is −2.9 points against an +8.2 rise, which is not "slightly". |
| 3 | Appendix H: "A **monotone** curve means every possible cut of the age axis preserves the ordering; **no alternative bracket scheme could reverse it**" | **Premise false and withdrawn eight lines earlier**, and the inference is a non sequitur — composition depends on roll size, not only behaviour. The reviewer's counterexample (75–79 vs 80+) was **wrong**: measured, the off-year/presidential share ratio still rises (1.54 → 1.57). The real reversal is 85–89 vs 90+, by 0.007. Replaced the argument with the measured composition ratios. |
| 4 | "The senior-to-youth ratio **roughly triples** off-cycle… from about 2:1 to ~5:1" | **2.55×**, and the sentence's own two figures give 2.5. |
| 5 | precinct roll-off "16.4%, in line with the roughly 17% we see statewide **once both are measured the same way**" | **Not the same way.** 17.2% is the certified-ballots basis; on the precinct cut's own presidential basis, statewide is **16.3%**. The fix makes the paper's check *better* than it claimed. |
| 6 | abstract: "27.1 million individual vote-history records **with the voter's year of birth**" | **26.3M (96.9%)** carry an age; 827,980 rows match no roll row. The old probe's capture groups stopped before the qualifier, so it was structurally uncheckable. |
| 7 | "**A direct check** … a separate check asks whether reconstructing from a current roll skews the composition" | **Not independent.** Blending the two figures already published three paragraphs earlier reproduces the snapshot column to within 0.2 points. It sizes the attrition; it is not a second source of evidence for it. |
| 8 | "a later (larger) roll mechanically pulls them down… the exception is 2021" | **Wrong mechanism for three of five years.** The reconstructed roll is −9.2% in 2021 and −3.9% in 2022, +0.2/+3.1/+6.4% after. The rate sits low in all five years because the *numerator* is short. 2021's agreement with the official 39.38% is two 9.2% shortfalls cancelling, in the year with the weakest coverage. |
| 9 | precinct paragraph: raw +0.09 → "under that analysis almost nothing is left… about +0.11" | **Predictor switched mid-argument.** +0.11 is the partial on the ACS *resident* 65+ series (raw +0.26); the electorate series had **no** controlled counterpart at all. Computed it: **−0.02**. |
| 10 | "race… is **unmeasurable at the individual level** in Washington at any geography" | Pipeline stated as world. BISG (Imai & Khanna 2016) produces individual-level estimates from surname + geocode and is standard on voter files. Narrowed to "not observed", with the imputation route named. |
| 11 | Appendix F's grid applies 5–34% roll-off to both even-year rows and **none** to the odd-year baseline | **Confirmed, and much larger than the reviewer's estimate.** They put SJR 8201 at 17.0% on a per-precinct floor. On the paper's *own* denominator (certified ballots) the statewide item rolls off **34.7–36.0%** across 2021 and 2025; local offices run 4–44% on a conservative floor. The claim that odd-year ballot return is "a closer stand-in for local-race participation" was asserted, never measured, and does not hold. |
| 12 | "The skew is a turnout-and-salience story, **which is why the lever is when you hold the election**" | Causal conclusion from an accounting identity. Narrowed; the counterfactual now rests only on the quasi-experimental literature, where it already did. |
| 13 | "the fact that the 65+ share barely moves across all three is **direct evidence** that none of them drives the composition" | 3.6-point spread is about 30% of the headline gap, three observations, no counterfactual, and the low year is the weakest-coverage year. Narrowed to "consistent with". |

**Two findings where measuring first changed the answer**, which is the whole reason the step
is mandatory: #3 (the reviewer's counterexample failed, but a different real defect stood) and
#11 (the true figure is roughly double what the reviewer computed, because they used a
different denominator from the one the paper's own table uses).

### The gate could not have caught any of these, and one reason is now fixed

`COVERAGE_EXEMPT`'s `^\d{1,2}$` ("small integer — ordinals, cohort edges, counts") was matched
against the token with its unit **stripped**, so it silently exempted every integer
*percentage* in the audited sections — including the headline off-year band "~37–40%", the
"2:1" and "~5:1" ratios, "about 16%" and "~61%". Same shape as the retired `^\d{1,2}\.\d$`
skip that `_verify_prose`'s own docstring records. `vp.audit_coverage` gained
`strict_units=True`: a pattern must now match the token **as written** as well as stripped, so
`16` stays exempt and `16%` does not. Opt-in, and turned on **for this paper only** — enabling
it everywhere reopens coverage for eight papers at once, so each adopts it as its turn comes.

### What was built

- `scripts/diag_wa_rolloff_oddyear.py` — the odd-year roll-off the grid assumed away, on two
  denominators, both conservative. Added to the sync manifest (the cited-files test caught the
  omission immediately, which is the test working).
- `scripts/diag_turnout_decomposition.py` — `--off` / `--all-off-years`. The dates were module
  constants, so the paper's 2023 and 2021 decomposition figures **had no reproducible path in
  the repo at all**; the script it cited could only ever produce the 2025 pair. That is how
  they stayed wrong.
- `scripts/diag_wa_rolloff_precinct.py` — the missing partial correlation on the electorate-65+
  predictor.
- `verify_who_decides_wa.py` — the decomposition moved out of `UNCHECKED` (both ratios, all
  three off-years), plus the reconstruction table, the senior-to-youth multiplier, the
  banding-robustness ratios, the off-year spread and the year-of-birth qualifier.

### State after round 1

`verify_who_decides_wa.py` **311 figures** (was 246), all four audited sections fully mapped
under the stricter exemption; `tests/test_infrastructure/` 331 passed;
`check_cross_doc_consistency.py --skip-metadata` 0 findings. `docs/submission-metadata.md`
re-pointed 246 to 311.

**The SSRN re-upload debt grows.** It already covered two corrected sentences; it now covers
thirteen items, two of which (#11, #2) change an argument rather than a number. Author's step,
unchanged.

**Round 2 is a fresh reviewer on the corrected text.** A paper is done when a full round
produces no confirmed defect in the four gate-blind classes; round 1 is not that round.

---

## 2026-08-09 (second pass) — WA round 2: the round-1 fix was itself a partial-load artifact

A fresh reviewer on the corrected text, same brief, again without the log or the ledger.
**Not a clean round**, and the most important finding is against round 1's own work.

### The round-1 correction was wrong, in the way the appendix already warned about

Round 1 measured odd-year statewide roll-off at **34.7–36.0%** and used it to overturn the
paper's reasoning. That figure divided a **38-county numerator by a statewide denominator**.

Measured: `precinct_results` holds **zero King County rows for the 2021 and 2023 generals**,
and for 2025 holds only `CITY OF SEATTLE MAYOR` (3,051 rows) — no SJR 8201. King is 29–33%
of each odd-year electorate. Scaling the denominator by King's ballot share gives
**4.9–6.6%**.

This is the identical defect Appendix F already excludes Lt. Governor for, in a sentence
three paragraphs away: *"loaded in only 5,355 of 8,111 precincts / 38 of 39 counties, a
partial-load artifact, not roll-off."* Round 1 read that sentence and did not apply it.

**The correction reverses the reading.** A statewide measure on an odd-year ballot rolls off
about what a statewide measure on an even-year ballot does (4.1–5.6%) — so for that class of
contest the paper's original reasoning was right. What survives, and is the finding that
matters, is Cut 2: **local** offices roll off 4–44% on a conservative floor, 30–44% for fire
districts. Those are the contests consolidation would move. The grid's odd-year row still
should not be blank; the sentence justifying it was wrong about local offices and right about
statewide measures, and the paper now says both.

Two consequences beyond the number. The 2025 mayor cell was **13.3%** because Seattle Mayor,
being King's only loaded 2025 race, was by construction the ballot floor in all 1,017 King
precincts — 0% roll-off there by definition. Excluding King it is **25.2%**. And the three
odd-year columns had been three different populations (4,973 / 5,328 / 6,438 precincts); they
are now one 38-county footprint. `diag_wa_rolloff_oddyear.py` gained a guard that **raises**
if King is ever loaded, because the scaling would then be wrong.

The limits section said "King County 2020 presidential is not loaded and is excluded (all
figures are 2021+)", which reads as confining the gap to 2020. There are two gaps and the
second is the binding one. Both are now named, with the body's VRDB-based results explicitly
exempted — King is complete in the voter file.

### The verifier was describing itself falsely

The paper cited `verify_who_decides_wa.py` "#23 / #24 / #30" and "sections #1–#30". **The
verifier has no numbered sections** — they were removed when it became an asserting script.
Worse, two of the three cited the verifier for tables its own `UNCHECKED` list disclaims, and
`UNCHECKED` pointed at `scripts/diag_offyear_age.py`, **which does not exist**.

Both `UNCHECKED` entries were false on inspection:

- *"the 39-county table … a probe per cell would triple this file for no additional failure
  mode."* One derivation and one row-loop. **All 39 rows are now derived and asserted** —
  156 figures. The reviewer reported six wrong cells across four rows; re-derived here, **all
  39 reconcile exactly**, so those were a basis difference in their query, not paper defects.
  Recorded as a **reviewer error** — but nothing in the file could previously have told the
  difference, which is the actual point.
- *"the Das-Gupta decomposition — a derived quantity of the composition and roll figures
  already asserted here."* It is a separate construction over four counterfactual
  electorates, and two of its three off-years had been published under the wrong definition.

**The generalisable rule, now written into the file: an `UNCHECKED` entry is a claim about
coverage, and nothing checks it. Adding one needs the same evidence as adding a probe.**

### Confirmed defects from round 2, beyond the above

| claim | verdict |
|---|---|
| Ladder row "Registered roll (April 2026)" | **Undisclosed basis mixing.** That row is the FULL 5.51M roll; every turnout rate in the paper has the **active** roll as its denominator — confirmed arithmetically, 2,001,425 over 39.24% = 5,100,471 against an active roll of 5,098,276. The 416,492 inactive registrants are far younger (median 38 vs 49), so the published row runs about a point younger at each end **in the direction that widens the contrast the table exists to show.** Now disclosed and derived. |
| "18-to-20-year-olds participate at slightly *higher* rates than voters in their mid-20s" | **False for 19.** Age 19 is 50.8%, *below* the mid-20s (52.1%) and the minimum of the young range — lower than the early-20s trough the sentence says comes after. Only age 20 exceeds it. |
| Appendix G's eight correlations | **Six truncated toward zero rather than rounded**, systematically: % college +0.18 vs +0.19, % Hispanic −0.20 vs −0.21, income −0.08 vs −0.09, partial white +0.10 vs +0.11, partial Hispanic −0.12 vs −0.13, partial college ~+0.20 vs +0.21. A reader running the cited script sees six mismatches. |
| "Court of Appeals (regional; **only one division votes**)" | **False.** Eight contests across all three divisions in 2024. The exclusion is right; the reason was not — each is voted only within its own district, so none spans the state. |
| "King County (the largest and **youngest**)" | True on 65+ share, false on median age (Franklin and Whitman are younger on both the roll and the 2024 electorate). |
| "**every test comes out the same way**" two lines after "depends on which yardstick is used" | Mutually exclusive. They agree on magnitude (about zero), not sign. Also: the appendix printed the three predictors with the *smallest* partials and omitted median age (+0.16, the largest surviving) and under-30 (−0.11, the only raw predictor pointing toward the worry). Both now reported. |
| "no full date of birth was **obtained**, stored, or used" | A sentinel in the loaded table establishes storage and use, not acquisition. Narrowed; the statute carries the rest. |
| "declines from 80 onward, **essentially monotonically**" | Three upward steps in the tail, the largest ten times the 51-to-52 dip the same paragraph calls noise. Now attributed to small cells rather than smoothed over. |
| `diag_wa_age_curve.py` docstring | Still carried the retracted "smooth, **monotone** age ramp … decline from ~84", contradicting both the paper and the verifier. It is a **published** script. Rewritten. |

### Reviewer errors, recorded

- The 39-county last-digit errors (six cells) — do not reproduce; all 39 rows reconcile.
- Round 1's Appendix H counterexample (75–79 vs 80+) had already failed the same way.

Two rounds, two reviewer errors, both caught by re-measuring. The rule holds.

### State after round 2

`verify_who_decides_wa.py` **489 figures** (was 311, was 246), four sections fully mapped;
`tests/test_infrastructure/` 331 passed — and it earned its keep twice this round, catching
both a new script missing from the sync manifest and a citation to a script that does not
exist. `check_cross_doc_consistency.py --skip-metadata` 0 findings.
`docs/submission-metadata.md` re-pointed to 489 **and its SSRN abstract updated**, which had
still carried the pre-correction "27.1 million … with the voter's year of birth".

**Round 3 is required.** Round 2 found confirmed defects in all four gate-blind classes,
including one this session introduced.

---

## 2026-08-09 (third pass) — WA round 3: the round-2 fix made a false coverage claim

Third fresh reviewer, same brief, no log and no `git log`. **Not a clean round.** Again the
most instructive finding is against the previous round's own work, and this time it is the
exact defect that round's comment was written to warn about.

### Round 2 added a warning and then committed the thing it warned about

Round 2 rewrote the verifier's `UNCHECKED` list and added a 23-line comment ending: *"an
`UNCHECKED` entry is a claim about coverage, and nothing checks it. Treat adding one as
needing the same evidence as adding a probe."*

The same edit **derived** `bandratio_*` for Appendix H and **wired it to no probe**, then
wrote in three places — the appendix, the end note, and the new `UNCHECKED` entry — that the
appendix's "load-bearing claims (the 65-boundary step, the peak, the tail decline and the
banding-robustness ratios)" were asserted. None of them was. `--coverage` listed every one of
those tokens as unprobed; the values were correct, so nothing failed.

Now genuinely asserted: the peak (72.0% at 79), the 64→66 step against the 60→64 step, the
five tail points, and all seven band ratios plus the 0.007 reversal — **18 figures** where
there had been a claim.

**The rule generalises past `UNCHECKED`: a derivation nothing reads is not coverage.** A
`derive()` key with no probe is indistinguishable, from the outside, from a figure that is
checked.

### The reconstruction table compared two different populations

Round 2 added a table of reconstruction-vs-official deltas and an explanation: the numerator
shortfall depresses the rate in all five years, while the denominator "only pushes the same
way from 2023 on". **The sign flip at 2023 is a population mismatch, not a mechanism.** The
reconstruction counts every registrant; official registered counts only active ones — which
round 2's own disclosure, 60 lines earlier, had just established. Matched:

| | as built (full roll) | matched (active only) |
|---|--:|--:|
| 2021 | −9.2% | **−15.4%** |
| 2022 | −3.9% | **−10.9%** |
| 2023 | +0.2% | **−7.4%** |
| 2024 | +3.1% | **−4.9%** |
| 2025 | +6.4% | **−1.8%** |

Like for like the roll is smaller in **every** year, shrinking monotonically as the
registration-date filter has less history to discard, and on a fully matched basis the
reconstructed rates run *above* official in all five (41.1 / 65.0 / 37.1 / 79.2 / 39.7%
against 39.38 / 63.82 / 36.41 / 78.95 / 39.24). There are three effects, not two: numerator
coverage, the registration-date filter, and **inactive inclusion**, which inflates the
as-built denominator by 7.3–8.4 points and masks the second. The table now carries both
bases and both are asserted.

### The paper's own figure count was never checked

The end note said the verifier "re-derives **311 figures**" while it asserted 489 — live in
the public record on a posted paper, with `submission-metadata.md` correctly saying 489 and
**passing its guard**. `vp.audit_satellite_counts` read only the files in `SATELLITES`, never
the paper, and `_COUNT_CLAIMS` had no anchor for the papers' own "re-derives N figures"
phrasing.

Both fixed: the guard now scans the paper itself, and the phrasing is an anchor. Two things
that fell out of doing it, both worth the record:

- The loose `— N of them` anchor is a **satellite idiom** and false-positives on a paper:
  `safe-seat-washington.md` says "every distinct party string in the five certified files —
  32 of them", which counts party strings. Scoped to satellites rather than dropped, since it
  is the only anchor their boilerplate offers. All eight verifiers re-run green after.
- A patch that located the probe block by `str.index` on two anchors **silently deleted 20
  probe blocks**, because the second anchor's first occurrence sat before the first's. Caught
  by the figure count dropping 489 → 433 with no probe reporting a failure. Reverted and
  redone by explicit line range. A count that only ever goes up is not a check.

### Confirmed defects from round 3, beyond the above

| claim | verdict |
|---|---|
| "under a coverage gate that fails on any unprobed number in a result section" | The gate audits **four** slices. The abstract, the validation section, the interpretation, the limits list and all eight appendices are outside it. Figures there are probed where a probe exists; nothing fails if one does not. Now stated. |
| "steepest through the early sixties (about 1.4 points per year from 60 to 65)" | The parenthetical is right (1.36); the superlative is not. **65→70 is 1.54/yr**, the steepest five-year stretch — and it sits above 65, two paragraphs from the no-discontinuity argument. |
| "upward steps at 93→94, 96→97 and 98→99, the largest of them ten times the size of the 51→52 dip" | Ages 96–99 are **outside the 18–95 curve the reader is pointed to**, and the largest of the three is +2.10 — thirty times, not ten. Inside the curve's range there is one step, 93→94 (+0.70). |
| Appendix H's young tail | Described on **2024 turnout** inside a paragraph whose stated measure is retention. On retention the young ages run the other way and are nearly flat (23.4 / 23.0 / 23.1 at 19/20/21), so the first-election bump is a turnout phenomenon retention does not show. The measure is now named at both tails. |
| "the composition table's 36.7% adds a registered-on-or-before filter, **a 0.1-point difference**" | The filter's real effect is about **0.001** points — 36.7508 against 36.7497, straddling a rounding boundary. The printed tenth is an artifact of rounding, not of the filter. |
| "Across the **~4,900 precincts** that have both a 2024 presidential vote and Census demographics" | Every one of the 8,111 precincts has a presidential vote; ACS availability is the only binding constraint, so the sample is **60% of the state** — a 40% loss the paper did not state, while it *did* flag the smaller crosswalk subset. |
| "roughly **2.5×** as age-unrepresentative" | The min-based reading; the sentence's subject is the three-cycle mean everywhere else, which gives **2.6**. Both are now printed and both asserted, closing a round-exemption rather than tolerating it. |
| Appendix C's reproduction bullet | Listed the single-year curve among what is re-derived, contradicting `UNCHECKED` and the end note three sections away. |

### State after round 3

`verify_who_decides_wa.py` **521 figures** (489 → 503 → 521 across this round's fixes), four
sections fully mapped; all **eight** paper verifiers green; `tests/test_infrastructure/` 331
passed; `check_cross_doc_consistency.py --skip-metadata` 0 findings.

**Round 4 is required.** Three rounds, three sets of confirmed defects, and in two of them the
defect was introduced by the previous round's fix. That pattern is itself the finding: the
edits that add a check are as defect-prone as the prose they check, and nothing was reviewing
them until now.

---

## 2026-08-09 (fourth pass) — WA round 4: the round-1 gate fix was a no-op

Fourth fresh reviewer, same brief, no log and no `git log`. **Not a clean round**, and for the
third consecutive time the sharpest finding is against a previous round's fix. This one is
the worst of them.

### `strict_units=True` did nothing, and shipped with a comment naming five figures it caught

Round 1 found that `COVERAGE_EXEMPT`'s `^\d{1,2}$` was swallowing every integer *percentage*
in the audited sections, and added `strict_units` to `vp.audit_coverage`: a pattern must
match the token **as written** as well as stripped, so `16` stays exempt and `16%` does not.

`_NUMBER` is `r"\d[\d,]*(?:\.\d+)?(?<![,.])"`. **It never captures `%`, `M`, `×` or `$`.** So
`tok == bare` for every token that exists, the added conjunct was satisfied whenever the base
pattern was, and the whole thing was a no-op. Verified directly: a synthetic section
containing `~37-40%`, `about 16%`, `~61%` and `2:1` with zero probe spans reports "fully
mapped" under `strict_units=True` and `False` alike.

**A check that cannot fail, added to close a check that cannot fail, documented as working
and naming the exact five figures it did not catch.** That is the fourth instance of this
defect class in this repo and the first one written by the process built to find it.

The unit lives in the source text, not in the token, so the fix reads `hay[m.end()]`. Turned
on, the gate immediately caught precisely the five figures the false comment had claimed —
the headline band `~37-40%`, `~38%`, `~22-25%`, `about 16%`, `~61%` — plus the off-year
returner share. All six are now probed; the last of them was **printed as `~40%` against a
derived 39.09**, which `check_rounding` caught the moment a probe pointed at it.

### 180 derived keys that no probe consumes — including the hinge of the bounding argument

The reviewer instrumented `build_probes()`. Four mattered:

| key | value | the published sentence resting on it |
|---|--:|---|
| `e24_max65` | 29.9931 | *"the presidential electorate under its most favorable assumption (**≤30.0%**)"* |
| `cty_n` | 39 | *"positive in **all 39 counties**"* |
| `cty_gap2_min/max` | 8.42 / 17.73 | *"gaps +8.4 to +17.7 points"* |
| `cty_gap3_min/max` | 7.51 / 16.11 | *"(King +7.5 to Franklin +16.1)"* |

`e24_max65` is what makes the worst-case bound a *bound* rather than an assertion, and it was
computed and thrown away. All four are correct; all four are now asserted. **The rule stated
in round 3 — a derivation nothing reads is not coverage — was not enough on its own, because
nothing enforced it. It is now four probes.**

### King is in the certified record; the gap is ours

Rounds 2 and 3 wrote *"King County is absent from the odd-year precinct returns"* and built
an estimated denominator around it. Measured on the raw certified exports: King is present in
all three odd-year files (1,688 / 1,610 / 1,728 rows) **including all three 2021 advisory
votes and SJR 8201** — on two pseudo-precincts, `Countywide` and `Total`.

The true statement is narrower and is about us: **King publishes no precinct detail in the
SoS statewide export in any year**, and this project's even-year King precinct rows come from
a separate county file (`data/raw/king/<YYYY>GenKingfinal-results-report.csv`) that exists
for the 2016/2020/2022/2024 generals only. The odd-year gap is an **acquisition** gap, not a
disclosure gap — the same world-versus-pipeline confusion that started this whole programme,
committed while correcting an instance of it.

**Open item, not closed here:** King's certified countywide totals for these contests would
make Appendix F's estimated denominator exact. De-duplicating the `Total` / `Countywide`
rows correctly is its own small job and getting it wrong would be precisely this defect class
again, so it is recorded rather than half-done. The paper now says the source has it.

### Other confirmed defects

| claim | verdict |
|---|---|
| *"ACS availability is the only binding constraint"* on the precinct sample | **False, and the label is on the wrong set.** 5,355 precincts carry demographics; a 50-presidential-vote floor removes a further 496. 4,859/8,111 = 60% is right, of a different population. The 4,650 electorate subset meets **four** constraints, not one. |
| Appendix E *"ranges from **30.7% (King)** to **66% (Jefferson)**"* | Mixes a 2025 cell with a 2023 cell, and sits **above the paper's own body table** (King 2021 = 28.7%). Now both bases: two-off-year county averages 31.4–65.9, all-cells 28.7–66.1. |
| The gate's four audited sections, as described in the end note | `tail` runs from the birth-year assumption to `## Interpretation` — it also covers the whole Geography subsection and the county table. The description named one sub-part and omitted two. |
| *"Ages 18–19 are omitted … so that retention cell is an empty-denominator artifact"* | The empty-denominator argument applies to **18 only**; 19 has 38K 2024 voters and a retention of 23.4%, printed in the next clause. 19 is absent because the table steps in fives. |
| Abstract: *"92–97% of off-year voters also vote in presidential **years**"* | All three figures are against **2024 alone**, which the body says correctly. The plural asserts a regularity the data cannot carry. |
| Appendix H slopes 1.54 / 1.43 | Computed off the table's **rounded** cells; true values 1.524 and 1.4225. The superlative itself is true (65→70 is the largest five-year gain on the curve, +7.62). Left as printed, now flagged as derived from the displayed table. |

### State after round 4

`verify_who_decides_wa.py` **539 figures** (246 → 311 → 489 → 521 → 539), four sections fully
mapped under a coverage gate that now actually fails; all **eight** paper verifiers green;
`tests/test_infrastructure/` 331 passed; `check_cross_doc_consistency.py --skip-metadata` 0
findings.

**Round 5 is required**, and the reason to keep going is now itself the finding: four rounds,
four sets of confirmed defects, and in three of them the defect was introduced by the
previous round's fix — twice inside the verification machinery rather than the prose. The
edits that add a check are at least as defect-prone as the prose they check, and until this
programme nothing was reviewing them.

---

## 2026-08-09 (fifth pass) — `who-decides-idaho.md`, round 1: the flagship claim withdrawn

First adversarial pass on the Idaho companion. Same method: a fresh reviewer given the paper,
the verifier and the databases, and **not** the audit log or the corrections ledger. Author
approved the rewrite before it was made, because it changes what the paper claims to
contribute rather than a figure.

### The instrument is destroyed by the act it measures

The paper's stated second contribution was that *"because the file records the party ballot
each voter actually pulled, the exclusion of the unaffiliated from the decisive primary is
**measured, not inferred**."*

Under **Idaho Code § 34-904A** an unaffiliated elector who requests a **Republican** primary
ballot signs a Declaration of Party Affiliation at the poll book and is thereafter a
registered Republican. A **Democratic** ballot affiliates nobody, because the Idaho Democratic
Party admits unaffiliated voters. `voters.party` is a single 2026 snapshot and the raw file
carries **no affiliation date**. So an unaffiliated voter who entered the Republican primary
is, by construction, not unaffiliated when we look.

Measured — and the signature is unambiguous:

| ballot pulled, by voters unaffiliated on the 2026 roll | 2022 (4.1y) | 2024 (2.1y) | 2026 (0.1y) |
|---|--:|--:|--:|
| → Republican | 27.7% | 9.7% | **1.7%** |
| → Democratic | 52.6% | 52.5% | 65.6% |

The Republican column falls monotonically with **distance from the snapshot**; the Democratic
column does not. Confirming tests: **55.8%** of the 2022 Republican-ballot pullers carry a
registration date *after* that primary — they re-registered and reverted to unaffiliated —
against **15.2%** of Democratic-ballot pullers. And voters who are Republican *today* pulled
a Republican ballot in **97.3 / 96.9 / 97.7%** of cases, a concordance that is definitional.

**So the 5.9% unaffiliated share of the 2024 primary electorate is not a measurement of
unaffiliated participation. It is a measurement of unaffiliated non-participation in the
Republican primary**, since participating there removes a voter from the category. The
honest estimate is the 2026 figure, closest to the snapshot: **7.3%**. Earlier cycles are
**lower bounds**, and the conversion is unobservable from this source, so the gap cannot be
closed with the data at hand.

**The New York companion already handles exactly this** and bounds its switching at 0.7–1.4%,
because NY enrollment must precede the primary by months. Idaho inherited the framing without
the caveat, in the one state where the caveat is load-bearing.

### The trend ran the other way

§IV read the same table as behaviour: *"even that door is closing … tightening the one-party
lock."* The Republican share of **all** primary ballots cast is **falling** — 86.1% (2022),
83.4% (2024), 79.5% (2026) — while the Democratic ballot share rises. Withdrawn.

### §V argued from registration to an outcome its own state refutes

*"Where the general election cannot change an outcome, the closed primary of Section IV is
not merely *a* decisive contest — it is the *only* one."*

In November 2024 Democrats won **15 of Idaho's 105 legislative seats** (90 R / 15 D, matching
the seated 2025–26 legislature). Of the 47 seats whose Republican primary drew a single
candidate, **9 were won by a Democrat**; all 52 contested-primary seats went Republican. So
filing settled **38 of the 90 Republican-held seats (42%)**, not "roughly half of
Republican-held seats" and not all 47 — a denominator error the paper made twice.

The companion safe-seat paper had already withdrawn a stronger version of this inference on
**observed margins**, which are better evidence than registration. It is not reinstated here.
The three-state superlative ("the starkest safe-seat map of the three states studied") is also
withdrawn: Washington publishes no party registration at all, so the comparison was across two
different measures.

### §VII: a circularity, and a superlative that contradicted §IV

**More than half of the Democratic donor tilt is three progressive ballot-measure
committees, one of them this paper's own subject.** Reclaim Idaho, Idahoans for Open
Primaries and Idahoans United for Women and Families drew gifts from **5,522 of the 23,613
matched donors (23.4%)**; Reclaim Idaho alone is the largest recipient in the Sunshine layer
by gift count (109,551 person-gifts). Excluding donors to any of the three, the Democratic
share falls **21.6% → 16.5%** and the Republican share rises 66.3% → 72.5%, so the
over-representation goes from **+9.8 to +4.6 points**. The direction of Finding 3 survives;
the magnitude is half what was printed, and *Idahoans for Open Primaries* is the Proposition 1
campaign the paper analyses in §VIII. Now disclosed in the paper.

**"The donor class is the oldest layer of all"** contradicted §IV's heading, *"its electorate
is grayest of all"*. On the shared current-roll basis §VII itself insists on, the primary
electorate is at least as old: **51.9%** of 2024 primary voters are 65+ (51.8% Republican-
ballot, 52.0% in 2022) against **51.3%** of matched donors, all four at median age 65. §VII's
superlative withdrawn; §IV's heading narrowed to "the grayest measured here".

### One reviewer error, and how it was caught

The reviewer reported the unaffiliated ballot-choice table as reproducing at 27.6 / 52.3 /
18.9 rather than the printed 27.7 / 52.6 / 19.0. A first attempt at this fix **changed the
paper to match** — and then the verifier's own pre-existing probes for that table failed,
because they derive it on the established basis that excludes NULL `ballot_choice`. The
paper was right and both the reviewer and the first fix were wrong. Reverted, and the new
derivation now carries a comment saying not to re-derive those shares on a second
denominator.

That is the third reviewer error caught by re-measuring before fixing, and the first one
caught by an *existing* probe rather than by hand.

### State

`verify_who_decides_id.py` **275 figures** (was 220), all sections fully mapped; the four
satellite counts re-pointed; all **eight** paper verifiers green; `tests/test_infrastructure/`
331 passed; cross-doc 0 findings.

**Round 2 required.** Not yet reviewed against the corrected text, and several round-1
findings were not reached: §VI's registration-cohort "new registrants" label (the party field
is a current snapshot, and Idaho had no party registration before 2011–12), §I's 2020 row
(built from 74.6% of that electorate against 98.0% for 2024), the "13% turnover in eighteen
months" figure (a net contraction over ~20 months), and the §VII "upper bound" argument whose
stated reason contradicts the backfill script it cites.

---

## 2026-08-09 (sixth pass) — `who-decides-cross-state.md`, round 1: the selection was the finding

First adversarial pass on the synthesis. The verifier was green at 74 figures and every cell
reproduced; the problems were all in the layer it cannot see, and the largest of them was
**which contests the harmonizer was asked to look at**.

### Two of three states were using a subset of their loaded history

`LOW` selected 3 Washington odd-year generals, **2 of New York's 5**, and **1 of Idaho's 3**
Republican primaries. Washington used everything it had; the other two did not, and nothing
said so. Widened to every loaded contest, three published claims move:

| | as published (subset) | all loaded contests |
|---|---|---|
| NY low-salience 65+ | 34.4–41.6% | **28.4–41.6%** |
| ID low-salience 65+ | 46.7% (a point) | **41.4–48.6%** |
| ID senior-to-youth ratio | 9.4:1 | 7.4–9.7:1 |
| ID dissimilarity | 27.6 | 25.0–27.8 |
| habitual-core floor | 87.7% | **86.4%** |

**"At 46.7% over 65 … it exceeds every odd-year general measured here" is false on the full
set**: Idaho's 2022 primary is 41.4%, just under New York's 2023 general at 41.6%. Withdrawn
and replaced with the class-level claim, which holds — Idaho's dissimilarity floor (25.0) is
above every general in the study.

### The low-salience column is confounded with distance from the 2026 roll

Widening the set made a confound visible that a single point per state had hidden. These are
current-roll reconstructions, so departures — which skew old — remove seniors from older
contests. Both multi-contest series run in exactly that order:

- **NY odd-year 65+:** 28.4 (2017) → 32.9 (2019) → 36.3 (2021) → 41.6 (2023)
- **ID primary 65+:** 41.4 (2022) → 46.7 (2024) → 48.6 (2026)

A 13-point climb across four New York contests in near-perfect order of recency. The
Boundary-of-inference bullet said the survivorship caveat was survivable because "the
cross-state claim rests on the direction and universality of the skew" — but Finding 1's
actual second-order claims are about **magnitude** and **ordering**, neither of which that
protects, and the states' cells sit at different lags. Worse, the bias direction differs by
state: Washington's attrition is older-skewing, Idaho's is larger for the young. The state
supplying the study's extreme is the one whose reconstruction most over-retains seniors.
Now stated, with the ladders printed.

The same lag drives the habitual-core metric, which measures overlap with the **2024**
presidential in every cell — so Idaho's 97.8% is its primary six months from its own
reference election. Its series is 94.7 → **97.8** → 94.4, maximum at the nearest contest.
The paper had read that 97.8% as showing "a selection result rather than a turnout-noise
result"; the figure cannot carry that.

### Finding 2 compared two different rungs of its own ladder

The partisan payoff put New York's **odd-year** gap beside Idaho's **2024 presidential** one
— in a paper whose entire method section exists to prevent that. And the striking New York
number is its **2025** general, which Finding 1 itself identifies as the *high*-salience
odd-year. Matched:

| | Republican 65+ − Democratic 65+ |
|---|--:|
| NY, Nov 2024 presidential | +3.7 |
| NY, Nov 2023 odd-year (its lowest-salience) | **+2.0** |
| NY, Nov 2025 odd-year (NYC mayoral) | +10.7 |
| ID, Nov 2024 presidential | +0.2 |

So "low-salience electorates are old *and* skew Republican is a New York fact" fails **within
New York too**: its lowest-salience general is nearly as symmetric as Idaho's presidential.
What survives is smaller and sits at high salience (+3.7 against +0.2), plus one exceptional
mayoral contest. Also recorded: Idaho's own lowest-salience contest is single-party by
construction, so no partisan gap is measurable there at all.

### Three more

- **"The closed primary locks that youth out by design"** — false. Idaho's *Democratic*
  primary is open to unaffiliated voters, and the Republican one admits them on affiliating
  at the poll book. In May 2024, **8,453** currently-unaffiliated voters pulled a Democratic
  ballot and **1,554** a Republican one.
- **Party of record is a 2026 snapshot in both party states and the paper never said so** —
  both companions flag it as their largest limitation, and Idaho's is *reactive* (§ 34-904A
  reclassifies the very voters Finding 2 discusses). Now a Boundary bullet.
- **"A third again"** is 27.8/22.4 = **1.24**, about a quarter — with both figures in the
  same sentence. And the dissimilarity index *narrows* the between-state gap relative to the
  ratio rather than widening it, so "widens the gap" is withdrawn too.
- **"Texas is that case"** — Washington is a near-miss the paper should name: its
  presidential primary does produce a per-voter party declaration, disclosable only inside
  the RCW 29A.84.730 window, which closed for 2024 with only Pierce captured.

### State after round 1

`verify_who_returns_ballot.py` **131 figures** (was 74), all five audited sections fully
mapped. The per-contest ladders are now derived cell by cell rather than as spans, and the
New York party-by-class table is derived for all three classes so the comparison cannot
revert to one of them. All **eight** paper verifiers green; `tests/test_infrastructure/` 331
passed; `check_cross_doc_consistency.py --skip-metadata` 0 findings after both satellites
were re-pointed.

**Round 2 required.** Findings not reached this round: the guard the paper says "asserts on
every run" is never called by any automated path and compares against hardcoded literals
rather than reading the WA paper; `structural_guards()` cannot fail; the verifier's
`UNCHECKED` list is stale in three of four items; the coverage gate still runs without
`strict_units`; and Idaho's age is computed as `age − (2026 − year)`, which ignores the
election month and puts Idaho about half a year young against WA/NY at the November generals.

---

## 2026-08-09 (seventh pass) — `cross-state-fec-money.md`, round 1

First adversarial pass on the money paper, triaged over three commits. The verifier was green
at 232 figures and every probed number reproduced; **every finding below is a claim ABOUT
figures, a wrong noun, or a check that could not fail** — the three classes it cannot see.

### The abstract contradicted Section C, and the verifier repeated it

The abstract said the paper "identifies no individual donor". Section C is headed **Largest
individual donors … at the person level** and names roughly fifteen people with dollar
figures. Worse, the verifier's coverage exemption for that section gave as its written reason
"this section names ORGANISATIONS and committees only — no individual donor is named anywhere
in this paper, which is the 11 C.F.R. § 104.15 boundary". An exemption whose stated reason is
contradicted by the text it exempts is the same defect as a false `UNCHECKED` entry.

**Author decision, same day:** the § 104.15 boundary is about *solicitation use*, so §C stays
and `CLAUDE.md`'s sentence — "no named contributor or named matched donor appears in any
report, export or analysis output" — is narrowed to campaign-facing products, which is what it
was written about when the prospect lists were removed. The distinction is the use, not the
fact of naming.

### Two checks that could not fail, in one query

**"100% of recipient dollars matched in all four states"** was true of any input: the
destination `CASE` has no branch for an unmatched committee, so a `LEFT JOIN` miss falls
through to `PAC/party/other`. No residual bucket can ever be non-empty. Whatever share fails
to match is inside the 51–62% cell that §B's conclusion rests on. **Fourth instance of this
class in the series**, after the empty-key probe, the "0 missing" manifest and the
`strict_units` no-op.

**And the same query resolves recipient state by `cmte_st`** — the committee's *registration*
state, which the abstract declares invalid two hundred lines earlier, in the sentence
explaining why. Bounded against §G's office-state outflow: WA −0.5%, ID 0%, NY −8.5%, TX
+9.1%. Single-digit, undisclosed, and load-bearing for every §B conclusion.

### Section I compared two different bases and read the gap as a mechanism

Per-cycle inflow concentration set against pooled outflow concentration, with the difference
attributed to the per-election contribution cap. Pooled like-for-like, inflow is **top-1%
23.4%, Gini 0.726** against outflow's 36.1–47.5% and 0.775–0.848 — a gap of ~1.5–2.0×, not
2.1–2.6×. The outflow ranges quoted ("39–48%", "0.80–0.85") also dropped Idaho at both ends.
A second confound survives the fix and is now disclosed: the inflow pool is all-state (887K
keys) against one state's residents (54K–837K), and pool size alone lowers a top-1% share.
Direction holds; the causal attribution does not.

§I is coverage-exempt, so the replacements are **derived and probed** — otherwise they would
be as unverified as what they replaced, which is how the mismatch survived.

### Six superlatives and a category error

| claim | verdict |
|---|---|
| Idaho "most retail on **every** measure" (×3) | Washington leads on ≥$5,000, 20.00% against 20.13% |
| "New York … most concentrated **and rising fastest**" | Texas rose faster on both comparisons the same sentence supplies |
| "**2×–5×** as much to out-of-state congressional races" | 1.2×–5.3×; two states below the floor, including the one named |
| "**a third again** more participatory" | two-thirds again (4.6% against 2.8%) |
| "$61M **on par with** $87M" | 70% |
| "the concentration ordering **is stable**" | true of New York only; WA and ID trade places across cycles |
| "WA and ID are **net importers**" | both are net exporters on the paper's own tables, and it is a cross-matrix subtraction the paper's own caveat forbids |
| Idaho "the **only** state whose out-of-region giving funds both parties" | §C records TX $6.0M to Warnock, 20× Idaho's |

**The category error:** a 2026-08-02 check was cited as an "independent derivation" proving
the donor key does not drive the concentration ordering. It groups by the **same key** on the
same data — two implementations agreeing, not two keys. The direction comes from the donor
paper's de-merging exercise (−6.1 to −8.3 points); the magnitude is unmeasured. Said so.

The paper also stated its donor-proxy bias **in two opposite directions** — "slightly
understated" in the scope note, "overstates concentration" in Limitations. The de-merging
evidence settles it: over-merging inflates, so the scope note was wrong.

`ZUMIEZ` removed from the tech sector keyword list — a teen-apparel retailer §C itself
identifies as one. 78 rows / $158,100, 2.2% of the tech row, so no printed figure moves.

The headline table's legend said bold marks the most top-heavy on every row; on the retail
rows it marks the most *retail*, the opposite direction, and the dollar row bolds all four.

### State after round 1

`verify_cross_state_money.py` **248 figures** (was 232), all audited sections fully mapped;
eight verifiers green; `tests/test_infrastructure/` 338; cross-doc 0 findings.

**Round 2 required.** Not reached: §F5's cross-state Gini comparison runs on differently-pooled
panels; the inflow recipient map has no `dsgn IN ('P','A')` filter while §G's stated method
claims one; amendment handling (`amndt_ind`) is unaudited on both loaders; §K1's
Texas-vs-congressional comparison fails on the paper's own inflow window; and §E's "cannot
vote in them" measures out-of-**state**, not out-of-district.

---

## 2026-08-10 — DISCLOSURE: one person-level contribution row reached a hosted model

**Reported immediately, per the standing rule in `CLAUDE.md` ("Say so immediately and plainly —
what file, how many rows, which fields. Do not minimise").**

### What happened

During the round-2 adversarial review of `who-decides-idaho.md`, the reviewing subagent ran an
aggregate `GROUP BY` over `data/raw/id/_source/id_2024_TCON.csv`. DuckDB's CSV parser hit an
**unterminated quote** in the file and raised an error that **echoed the offending source line
verbatim** into that session's transcript.

- **File:** `data/raw/id/_source/id_2024_TCON.csv` (Idaho Sunshine contribution export)
- **Rows surfaced:** **one (1)**
- **Fields on that row:** filing-entity id and name, campaign name, registration type,
  transaction id / type / sub-type, contributor type, **contributor last name, first name**,
  contributor company name, **street address, city, state, ZIP**, transaction date, amount,
  description.

It was not requested and was not produced by any `SELECT` the agent wrote — the parser
exception carried it. The agent stopped querying raw contribution CSVs at that point, opened
no `data/validation/*` file, and surfaced no voter rows; all VRDB work was
`COUNT`/`SUM`/`GROUP BY`/`DESCRIBE`.

### Why it happened, and whose fault it is

The subagent's brief carried the hard rule and the agent followed it as written — the rule
names `SELECT * LIMIT 5` as the hazard and says aggregates are safe. **Aggregates are not safe
on a malformed CSV**, and the brief did not say so because the orchestrator (me) did not know
it. The instruction was mine, so the gap is mine.

The orchestrator's own earlier reads of these same files did not trigger it, by luck rather
than design: the `duckdb` reads happened to pass `ignore_errors=true`, and the `pandas` reads
happened to pass `usecols=` limited to non-person columns.

### The generalisable finding

**`read_csv_auto` over a raw person-level file is a disclosure channel independent of what you
SELECT.** A parser exception can print a source row regardless of the projection, so the
projection is not the control. The control is `ignore_errors=true` / `strict_mode=false`, or
not reading the raw file at all.

This is the same shape as the rest of this programme's findings: a control written down
("query aggregates, not rows") that does not cover the mechanism it was believed to cover.

### What was changed

- `CLAUDE.md`'s hard-rule section now names this channel explicitly and requires
  `ignore_errors=true` on any read of a raw person-level file.
- The subagent brief template used for these reviews carries the same instruction.

### What is NOT claimed

No assertion is made here about what any *earlier* session did with these files. Per the
standing rule, a past session's behaviour is not inferable from its artifacts and must be
asked, not assumed.

### Author's decisions still open

Whether this warrants any further step — the row was one contribution record from a public
state disclosure file, not a voter-roll record — is the author's call, not the assistant's.
It is recorded here in full so that the call can be made on facts.

---

## 2026-08-10 — strict_units backlog cleared: 8 verifiers, 116 probes, 3 defects

**What this round was.** Not an adversarial review of a paper. The 2026-08-10 round-2 pass
found that `strict_units` — the coverage-gate fix added on 2026-08-09 — was wired to **one of
nine callers**, and converted the gap into a roster test (`ENABLED` / `BACKLOG`) rather than
enabling it blind, because doing so would have left six release gates red with no way to
separate a real regression from the expected backlog. This round works that backlog off.

**Result: `BACKLOG` is empty.** All eight callers run the coverage gate at full strictness.
116 probes added. Three defects found, plus one figure declared unverifiable.

### The three defects, all the same shape

Each is a **result written as a bare integer percentage**. The near-universal exemption
`^\d{1,2}$` is matched against the numeric token with its unit stripped, so `69%` looked like
an ordinal to every gate in the series.

**1. `does-money-move-votes.md` §3 — a wrong noun.** "express advocacy 69% *for* candidates
and electioneering 61% *against* them". 61% is right. **68.8% is `$8.96M / $13.03M` — the
share of express-advocacy dollars filed as *Independent Expenditure Ad* rather than
*Independent Expenditure*.** It is not a direction at all. The For share is **78%**
($10.11M of $13.02M). The identical sentence sat in `docs/pdc-c6-direction-audit.md`
**contradicting the table four lines above it**, which prints the components. Both corrected;
the audit doc carries an inline correction note naming the arithmetic.

The sentence is load-bearing — it is the stated reason express advocacy and electioneering are
reported apart rather than summed — so the relation is now asserted **in code**, not just
numerically: two probes on 69 and 61 would both still pass if both report types ran the same
way.

**2. `electoral-health-whitepaper.md` Finding 5 — a stale specification.** The NY own-party
crossover read **94%**. It reproduces on the **retired all-tier panels** (94.15 pooled / 94.40
federal) and on **no primary panel** — in a sentence that ends "**These are the primary
(full-name-key) specification.**" The federal primary panel gives **95.3%**, and the bullet's
every other NY figure is federal. Corrected to 95%.

Why it survived: only `state_dem_donly` was derived, for both states. Idaho's crossover *is*
the state layer and was probed; New York's is the federal one and **had no key to probe
against**. A two-figure sentence with one figure asserted is how the unasserted half drifts
into contradicting its neighbour. Both panels are now derived for both states.

**3. `who-decides-idaho.md` — two, one against its own table.** §VII: "they are 12% of the roll
but **21% of donors and give 21% of the money**", against a table **two lines above** printing
21.6% and 20.0%. Corrected to 22% / 20%. §IV: the Democratic contested-primary range read
**2–14%**; the four cycles the sentence names run **2.2% – 11.3%**. Corrected to 2–11%.

The Republican series in the same sentence — 36% (2016) → 43% → 68% → 53% — reproduces
**exactly**, and only its 2024 cell had been derived. The trend claim the section is built on
rested on one point.

### The mechanism changed, narrowly — and got the test it never had

Strictness first meant *a unit-carrying token cannot be pattern-exempted at all*. That is too
strong: **"the top 1% of donors supply 41.2%" has one result in it and it is not the 1.** With
no way to declare that, the only remaining route was a literal waiver on `"1"` — which covers
every bare 1 in the document. *A blanket waiver used to express a narrow exception is how
coverage gaps get built.*

It now means: **the pattern must match the token AS WRITTEN.** `^\d{1,2}$` still fails on
`16%`; a caller that means it can write `^1%$`, which reaches that token and nothing else.
Verified behaviour-preserving on all five papers already cleared before the change.

**The flag had no behavioural test.** `test_strict_units_rollout.py` checked *which* verifiers
pass it and never *what passing it does* — a roster for a flag nothing exercised, which is the
same defect one level up. It has been written twice and was wrong once, and the wrong version
was caught by an adversarial pass rather than by a test.
`tests/test_infrastructure/test_strict_units_semantics.py` (13 tests) pins the semantics
against a synthetic document, **with the historic defect as an explicit control** so the suite
cannot pass on a broken gate.

### One exemption deliberately names no owner

Idaho's roll-churn parenthetical — "33% are 65+ vs 24% of those retained" — needs the **2023
Idaho roll snapshot** beside the 2026 one. Only 2026 is loaded, and voters who left the rolls
are absent from it *by construction*, so no query over `id_vrdb.duckdb` can reproduce either
figure. The project's rule is that an exemption must name where the figure IS verified;
**here there is nowhere**, and the exemption says so rather than inventing an owner — which
would be a false claim of coverage, the exact defect class this gate exists to catch.

**Author's decision:** re-acquire the 2023 snapshot, attribute the two figures in the paper to
the run that produced them, or drop the parenthetical.

### Comparisons that were built on probed figures but were not themselves probed

A recurring shape, closed in this round: the per-state figures were asserted while **the
sentence's actual claim about them** was not, because a multiple or a band is written as a bare
integer. Now derived from the components rather than restated — "~3× Washington's federal
dollars", "~2× their off-year totals", "~20% of both ID and WA", the ~48% non-working bucket,
the ~2× competitiveness premium, the four-cycle contested series, the 5–7% unaffiliated primary
share, the 42% of Republican-held seats settled at filing, the 13% roll turnover, and the ~94%
inflated all-voter rate.

Each **"both" / "all four"** is asserted as a **relation in code**, so the word has to keep
being true: if two states stop rounding alike, the derivation raises rather than letting one
approximation silently stand for both.

### State

Figures per verifier: WA 539 · Idaho 275 → **306** · cross-state money 243 → **255** ·
money-votes 106 → **116** · NY 219 → **228** · whitepaper **101** · who-returns-ballot **139** ·
safe-seat **210**. Infrastructure tests 364 → **372**. Nine verifiers green, harmonizer green,
`check_cross_doc_consistency` **0 findings**.

Commit `49041e5`.

---

## 2026-08-10 — round-2 triage: two confirmed, one of mine reversed

Three findings from the round-2 passes, triaged against the data. The `~40 smaller items`
those reports also carried are **not recoverable** — the session transcript was compacted and
the reports lived only in it. That is a process failure worth naming: a reviewer's findings
must be written to disk when received, not held in context. Going forward each pass writes its
report to `docs/reviews/` before triage begins.

### Reversed — a defect of mine, not the paper's

The previous commit exempted Idaho's roll-churn figures ("33% are 65+ vs 24% of those
retained") as **not verifiable in this repo**, at length, naming a 2023 *Idaho* snapshot that
does not exist. They are **Washington's** figures, and the sentence containing them says so.
Washington retains `voters_20230901` — the only place in this project where a *departed* voter
can still be aged — and the pair reproduces exactly: of the 2023 snapshot's voters, the
**504,103** since departed are **33.15% 65+** against **23.93%** of the **4,782,028** retained.

Now derived in the Idaho verifier, with a guard that raises if departing voters ever stop
skewing older, since the boundary section rests a *direction* on it. **Read the sentence before
writing the reason.** The exemption was three sentences of confident, specific, wrong
provenance — the same shape as the round-15 error this log already records.

### Confirmed — §VI's cohort table is not a cohort table

`registration_date` is the date of a voter's **most recent registration event**. Idaho rewrites
it on an address change, on a party change — including the § 34-904A poll-book affiliation that
Section III is about — and on an election-day registration. Measured: of registrants dated
**2024, 36.3%** had already voted in an earlier election; of those dated **2022, 43.7%** had.
Both are **floors** — the file's vote history begins in 2020, so a 2024 registrant who last
voted in 2018 is indistinguishable from a new one, and the 2008–2020 rows cannot be cleaned at
all. The tell was on the page: **263,322 registrants dated 2024**, a quarter of the roll in one
year.

**The direction survives and sharpens.** Dropping detectably re-registered voters makes the
newest cohort *younger* (median age at registration **35 → 32**) and leaves the Republican
share flat (**57.5% → 57.7%**). Re-registrants are by construction people who were already
voting, so their removal cannot be what produces the young skew.

**What does not survive is one clause.** "The Democratic share is flat near 12% across two
decades" — on the clean cut the 2024 Democratic share is **10.7%**, not 12.4%, while the
unaffiliated share rises **28.3% → 29.8%**. §VI now states the re-registration shares, reports
both cuts, and presents the two-decade comparison as a direction rather than a series, because
its rows carry different amounts of contamination and cannot be a like-for-like trend.

### The bound that replaces an analogy

The boundary section argued the *direction* of survivorship bias from Washington because Idaho
has no prior snapshot. Idaho's own data bounds the *magnitude*. A reconstructed electorate is
the set of **current** registrants carrying a vote record for that election, so the Secretary of
State's certified ballots-cast count measures the gap directly — and the age composition follows
as arithmetic, because the missing voters are at worst all 65+ or none of them:

| election | ballots cast | reconstructed | coverage | 65+ measured | 65+ bounded |
|---|--:|--:|--:|--:|:--|
| Nov 2024 | 917,608 | 898,877 | 98.0% | 29.0% | 28.4 – 30.5% |
| Nov 2022 | 595,602 | 571,868 | 96.0% | 34.4% | 33.0 – 37.0% |
| Nov 2020 | 878,527 | 647,029 | **73.6%** | 26.3% | **19.4 – 45.7%** |

**2022 and 2024 are tight enough that Section I's finding survives them** — the intervals do
not overlap, so the 65+ share genuinely rises as salience falls, whoever the missing voters
were. **2020 is not**, and Section I's 2020 row is now marked indicative. That row is the only
place in the paper where roll attrition is large enough to carry a result, and nothing said so.

Denominators verified against the Idaho SoS canvasses rather than remembered: 2020 878,527 /
1,082,417 (81.2%); 2022 595,602 / 1,048,263 (56.8%); 2024 917,608 / 1,178,750 (77.8%), of which
121,015 registered on election day. The `~13% turnover` sentence now says the Idaho extract
carries no active/inactive flag, so the figure is an upper bound on turnover rather than a
measurement of it.

### Confirmed — the age clock is worth two points, and it runs one way

All three states are year-of-birth resolution **but not on the same clock**, which the synthesis
had already half-documented and then dismissed. WA and NY publish a birth *year*, materialised
as **July 1 on every row** (verified), so a calendar-year difference against a November election
implicitly assumes the birthday has happened. Idaho publishes a current integer *age*, which
already accounts for whether it has. The two disagree by a year for every Idahoan whose 2026
birthday falls after the extract date, and **an integer age cannot say who that is** — so
Idaho's figure is a one-sided bracket, not a point.

Measured across Idaho's five classes: **1.7–2.6 points of the 65+ share** and **1.3–1.4 points
of the dissimilarity index**. One single-year cohort near 65 is **1.8%** of the Idaho roll,
which is why one year of resolution is worth that much. The synthesis called this "accurate to
about a year" and added that the comparability caveat "understates how close the three are." It
does not.

**The published figures are the low end**, so the closed-primary electorate's dissimilarity of
**27.6** is the conservative reading against **29.0** at the other end — the correction runs
*toward* the finding, not against it. There is nothing to correct *to*, because the point
estimate is unrecoverable from an integer age; what is reportable is the size and the direction,
and `id_convention_sensitivity` in the harmonizer now recomputes both on every run and refuses
to finish if the bracket stops being one-sided.

One noun fell out of this: the synthesis's case table described the NY file as **"party + DOB"**.
It carries a birth year. A verifier probe was anchored on that cell and failed the moment it was
corrected — the machine working as designed.

### State

Idaho 306 → **339** figures. Nine verifiers green, harmonizer green,
`check_cross_doc_consistency` **0 findings**, 372 infrastructure tests.
Commit `3ec6fb2`.

---

## 2026-08-10 — the cycling itself, diagnosed and instrumented

**What this round was.** Not a review of a paper. The author asked why the papers keep mutating
— fixes applied and then undone, data elements found wrong with no change to the underlying
data — and whether this is model drift. It is not. The answer and the instruments are below;
the governing rules that came out of it are in **§0**, at the top of this file.

### It is not model drift

Every one of the rounds that produced the flip-flopping ran on the same model: at the time of
measurement, 78 of the last 80 commits carried `Co-Authored-By: Claude Opus 5`. A changing model
cannot explain a same-model oscillation.

The mechanism is that **both sides of every check are authored in the same round.** When a
derivation and a sentence disagree, that round decides which is wrong, with no prior authority
to appeal to — so the paper tracks whichever derivation is newest, and the next round's newest
derivation moves it back. Idaho's R−D `+76.8 → +76.9 → +76.8` (`df91534`, then `5a7992b`) is the
clean case: one round differenced the printed columns, the other the unrounded shares, and
neither was wrong on its own basis. **The basis was never written down.** Four more reversals of
the same shape are tabulated in §0, rule 3.

Two secondary contributors, both real and both smaller:

* **Every new round mints new probes**, and each is a fresh chance to mislabel a basis. Figure
  counts churn as a direct consequence (NY 219→228, safe-seat 205→210, ballot 131→139 in one
  day), and `audit_satellite_counts` makes each count a load-bearing anchor, so one added probe
  forces edits across the paper, its metadata and its notes.
* **A subset of figures genuinely moves under a finished paper.** `data/wa_statewide.duckdb` is
  appended to daily by the WA SoS Results Daily Archive task, and the 2026 PDC cycle is about
  half collected. Pinned panels are immune; unpinned live reads are not.

### The instrument: can a gate fail?

This project has twice shipped a gate that could not fail and documented it as working
(`1eeb978`, `e3938bd`). Reasoning about whether a check works is not evidence that it does, so
the question is now asked mechanically: **if this derived value were wrong, would the gate say
so?**

* `tests/test_infrastructure/test_gates_can_fail.py` — 22 tests, 0.7s, synthetic text and no
  database. Proves the shared harness fails on a wrong value, a missing anchor, an unavailable
  derivation, a second occurrence that disagrees, a rounding violation, a capture-count
  mismatch, an over-greedy capture and an undefined section — each with a passing control beside
  it, so the differential is real rather than assumed.
* `scripts/mutation_probe_verifiers.py` — the per-verifier sweep. Spies on `vp.run`, lets each
  verifier compute its `derived` dict once (the expensive part), then re-invokes the assertion
  pass with one key perturbed per iteration. One derivation, N cheap regex passes.
* `docs/reference/probe_mutation_<date>.csv` — the pinned result, gated by
  `tests/test_infrastructure/test_probe_mutation_roster.py`, whose `ARTIFACT` constant names the
  current frame. **Currently `probe_mutation_2026-08-11.csv`.** Earlier rounds re-measured *into*
  the `2026-08-10` name rather than writing a new one, which made the date stop being the
  provenance the script's own `--date` requirement says it is; from 2026-08-11 a re-measure
  writes its own dated file and the superseded one is dropped.

**Result: 1,541 derived keys caught, 0 UNCAUGHT, 396 no-probe, across the eight verifiers on the
shared harness.** Zero uncaught is the reassuring part and it is now measured rather than
believed: every value assertion in those eight gates does fail when its data is wrong.

`no-probe` counts keys no probe consumes; it is held as a per-verifier ceiling that may only
fall, not driven to zero, because some legitimately feed structural guards (safe-seat's
`zerovote_*` drive `if d["zerovote_total"]:`). Its largest entry is **181 on the WA paper** —
`e3938bd` recorded an instrumented `build_probes()` finding "180 derived keys that no probe
consumes, four of them carrying published sentences" and asserted those four. The rest are still
there, presumed intermediates. Presumed is not measured; the ceiling stops the number drifting up.

**The lead article's gate cannot be swept, and that is a real gap.** `verify_donor_class.py` never
adopted the shared harness: 4,942 lines with its own `prose_probes()`, its own coverage audit, a
module-level `_FAILURES` accumulator and no `main()` — importing it *is* running it. So the one
paper under journal submission is gated by machinery this instrument structurally cannot
interrogate. Recorded in the roster test rather than left as an absence, because a sweep that
silently omits the lead article reads as covering the series.

### The basis registry

`docs/reference/derivation-bases.csv` declares population, county footprint, source prefix, tier
spec, cycle window and rounding source per key **family** — 25 patterns cover safe-seat's 203
numeric keys, where one row per key would have been ~1,900 rows of mostly-guessed metadata across
the series. `vp.require_bases` fails on a numeric derived key matching no pattern;
`vp.audit_basis_consistency` fails when two rows naming the same `quantity` disagree on a basis
column without naming where the paper discloses the difference.

Rolled out on the `ENABLED`/`BACKLOG` roster pattern, safe-seat as the pilot (203/203 declared),
seven verifiers still owing — the same judgement the `strict_units` rollout made, and for the
same reason: a registry filled in at speed is worse than none, because it looks like a record.

**It fired a real finding on its first run.** The four-state seat comparison puts Texas on a
backfilled footprint, because its canvass returns omit uncontested seats. That is disclosed in
Appendix F, so the row now names the disclosure — the check was not loosened to accept it.

What the registry does **not** do is evaluate composite arithmetic. The composites are built
through f-string key families and there is no honest static way to reconstruct them, so
`computed_on` is a **declaration, not a check**, and is labelled as one in all three places it
appears. What is enforced is that a paper with unrounded composites tells its reader so.

### Four defects found on the way, and one of mine

1. **`tests/test_infrastructure/` was red at HEAD.** The claim scan flagged a comment added by
   `5470f7f` — "the cell claimed a precision the source does not publish" — with no registry row
   behind it. The claim is TRUE and is now measured and registered as
   `ny-vrdb-birth-precision`: all 13,540,558 NY rows carry a birthdate whose month-day is
   `07-01`, one distinct value across 146 birth years, so the source publishes a birth year and
   the month-day is a materialised placeholder. Aggregate query only; no row was read.
2. **`verify_cross_state_money.py` printed a NOTE where it needed to fail.** Its own docstring
   said the script "must not quietly report a drifting number as if it were the pinned one", and
   then a missing WA roll pin produced a note and exit 0. Now a hard failure.
3. **Two verifiers could not be run by the command their own docstrings give.**
   `verify_money_votes.py` and `verify_whitepaper.py` import `wa_analyzer`, which is on the path
   for pytest only, so a bare `python scripts/verify_money_votes.py` died with
   ModuleNotFoundError. Every real caller sets `PYTHONPATH=src`, so nothing noticed. Both now put
   `src` on `sys.path` themselves. A gate whose documented invocation does not run is a gate that
   silently does not run.
4. **Mine: I read a piped exit code as success.** The first full sweep crashed on verifier 1 of 9
   and I reported it as passing, because I had run it through `| tail -60` and read `tail`'s exit
   status. Exactly the defect class this round exists to close, committed while closing it. The
   sweep's import is now inside its error guard, and its exit code is read directly.

### The question that was asked, and the author's answer

Four commits landed on `master` **during** this session — `49041e5`, `6b9a7c6`, `3ec6fb2`,
`6bc5a55`, between 12:43 and 13:24 — moving HEAD off the `5470f7f` it started from and clearing
the `strict_units` backlog that was open when it began. Concurrent authorship would have been a
fifth mechanism for "a fix that came undone", and the one mechanism none of the instruments here
can see, so it was raised rather than assumed either way.

**Asked and answered 2026-08-10: a single session, confirmed by the author.** Recorded because
this file's own rule is to ask the human who was there rather than infer from artifacts — and the
inference available here (HEAD moved, therefore something else was committing) would have been
wrong. The concurrency mechanism is closed.

What the episode did leave is a real defect in the instrument: the first probe-mutation artifact
carried **no record of which tree it measured**, so whether it straddled those commits was
unanswerable from the artifact. It was re-measured on the settled tree with HEAD recorded either
side and came back identical. Stamping the HEAD into the artifact itself is still owed.

### State

**Not a release gate.** No paper figure was changed by this round; the changes are to the gates,
the registry and §0. `tests/test_infrastructure/` **410 passed, 1 skipped, 50s**. Eight harness
verifiers swept, 0 UNCAUGHT. `verify_cross_state_money`, `verify_who_returns_ballot`,
`verify_money_votes`, `verify_whitepaper`, `verify_safe_seat` re-run individually, all exit 0.
The full suite and `check_cross_doc_consistency` were NOT re-run — this round touched no paper
prose, and the freeze rule's own discipline is to spend the 21-minute gate at a stage boundary
rather than after each edit.

---

## 2026-08-10 (second pass) — the lead article's gate, and a claims audit that came back clean

### The donor gate is now swept

`verify_donor_class.py` was the only gate in the series never asked whether its probes can fail,
while gating the paper under journal submission. `sweep_donor_class()` reaches its actual seam —
`cached_derive()` memoises into the module global `_DERIVED`, `prose_probes()` reads it — so a
perturbed copy runs the REAL comparison loop. Nothing is reimplemented; a hand-rolled copy of the
loop would have tested the copy.

**All nine gates: 2,465 keys caught, 0 UNCAUGHT, 909 no-probe, 9 passing baselines**, at HEAD
`3c54672`. The donor gate contributes **924 caught, 0 uncaught** at 8m20s import + 1.6 min sweep.

**A hole in the instrument shipped in `3c54672`, found and fixed here.** `caught` is inferred from
a non-zero exit under perturbation — so a gate that already fails unperturbed exits non-zero for
every perturbation and every key reports `caught`. A sweep that measures nothing while printing a
perfect score. There was no baseline check. Both sweeps now record one, mark keys `UNTRUSTED`
rather than `caught` when it fails, and exit non-zero. All nine baselines pass, so the previous
artifact was sound; it was not entitled to say so.

The donor gate's **513 of 1,437** numeric derivations are consumed by no probe — 36%, the largest
in the series. Its coverage audit independently guarantees no *published* figure is unprobed, so
these are presumed intermediates; `e3938bd` is the round where four such keys turned out to carry
published sentences. Held as a ceiling that may only fall.

### The claims audit — 20 comparison-class claims, none false

The documented blind spot is **claims about figures**: a superlative, ordering or comparative has
no numeric token for a probe to anchor on. It has been false twice here — "the highest of the
four" (§E, now guarded by `_id_is_max_oos`) and "the most IE-saturated House race in the country"
(22nd of 387, now owned by `diag_fec_ie_bulk_crosscheck.py --national-rank`).

Scanned all nine documents for a superlative paired with an explicit comparison class ("of the
four", "in the country", "than any", "no other state"). **20 claims. Every one checks out.** The
strongest were verified by hand against their own tables:

| claim | verdict |
|---|---|
| "Idaho is the least concentrated of the four on every measure" | true — ID lowest on all three (top-1% 36.0, top-10% 69.2, Gini 0.775) |
| "the ordering matches the matched federal panel (NY > WA > ID)" | true — 47.5 > 39.3 > 36.0 |
| retired share "the highest of the four" | true — ID 31.7 > WA 24.0 > TX 19.5 > NY 11.8 |
| "Idaho ships the most of all — 68%" | true — outflow rest-of-US 68.0 vs WA 50.8, NY 62.0, TX 43.3 |
| "the highest external dependence of the four" | true — inflow rest-of-US 53.3 vs WA 26.7, NY 41.0, TX 34.2 |
| "even Texas, the most parochial" | true — TX in-state 54.1%, the highest |

**What the audit did find is uneven protection, and one paper is the outlier.** Most of these
claims are *transitively* protected: the paper prints every comparator adjacent to the claim, each
comparator is probed, so a value could not drift without failing its own probe before the ordering
sentence went quietly false. That protection depends entirely on the comparators being **probed**,
not merely printed — and section coverage is where that is decided:

| verifier | sections | exempt | gated |
|---|--:|--:|--:|
| `verify_cross_state_money.py` | 19 | 12 | **37%** |
| `verify_donor_class.py` | 48 | 4 | 92% |
| the other seven | 37 | 0 | 100% |

`cross-state-fec-money.md` is the outlier by a wide margin, and §G — where "ships the most of
all" and "the highest external dependence of the four" live — is one of the twelve exempt
sections. Its 24 flow-matrix cells are printed but unprobed, so those two superlatives have
**neither a boolean guard nor transitive protection**. They are true today; nothing would catch
them becoming false. That is the same exposure that produced the §E defect one section away.

The twelve exemptions are documented, each naming an owning script and marked BACKLOG, so this is
a recorded state rather than a hidden one. What was not recorded is that it concentrates the
series' entire claims exposure in one paper. **Recommended, and NOT done here:** probe §G's flow
matrix and add boolean guards for its three superlatives — admissible under §0 rule 1(c) as
closing a documented gate, and it asserts figures the paper already prints rather than adding an
analysis.

One correction to my own measurement, caught before it was written down: a first pass reported
`verify_who_decides_wa.py` as gating 0 sections. It gates **4 of 4**. The regex looked for a dict
and that file declares `AUDITED_SECTIONS` as a tuple with an empty exempt dict. The instrument was
wrong, not the paper.

### State

`tests/test_infrastructure/` **418 passed, 1 skipped, 47s**. Nine gates swept, 0 UNCAUGHT, all
baselines passing. No paper prose changed in this pass — the claims audit found nothing to fix.

---

## 2026-08-10 (third pass) — Wave 1, `safe-seat-washington.md` round 1: four defects, three withdrawn flags

**First dedicated adversarial round on this paper.** It had none: 9,028 words, 68 table rows, on
the release path. Run under the twelve-lens protocol, which replaces the open-ended critical read
that produced the cycling. Verdict: **NOT clean.** Four defects and one wording overstatement.
Under the two-consecutive-clean-rounds exit rule this paper stands at zero.

### The four defects

1. **A false comparative, and the paper's own table disproved it.** Dimension 1 said 2018's 19
   seats inside five points were *"more than double any other year in the series."* The Tossup
   column is 2016: 8, 2018: **19**, 2020: 11, 2022: 10, 2024: 10. Nineteen is **1.7×** the next
   highest, and 2 × 10 = 20 > 19, so the claim held only against 2016. It was false against three
   of the four other cycles — and **every comparator was already asserted** by the per-year
   probes, so the sentence contradicted a table three rows above it. Nothing caught it because a
   comparative carries no numeric token for `audit_coverage` to inspect; the 19 itself was probed
   and correct. Now *"the most in the series and nearly double the next highest, 11 in 2020"*,
   with the comparator probed and the ordering asserted in code via `claim_guards()` — the
   `_id_is_max_oos` pattern. The guard is bounded on both sides: below 1.5× neither wording is
   honest, at ≥2.0× "more than double" becomes sayable, so the sentence and the check cannot
   drift apart in the direction that produced the defect.

2. **Two coverage exemptions carried false reasons**, both stale since the 2026-08-08
   party-string audit moved 2020's no-D-v-R share to 25.4%. `"26.9"` was waived as *"the adopted
   2020 no-D-v-R share … asserted at its table cell"* — it is neither; the adopted share is 25.4%
   and that is what the Dimension-2 table asserts. `"27.6"` was waived on the ground that *"the
   adopted figure beside it is asserted"*, and the figure beside it is 26.9, which is itself
   exempt. **One stale figure was waived by pointing at an assertion that did not exist, and a
   second was waived by pointing at the first.** Both reasons now say what each figure actually
   is — an intermediate in a two-step correction — and name 25.4% as the current asserted value.

3. **A stale restatement the satellite checker could not see.** The figure count moved 210 → 211
   with the new comparator probe. `audit_satellite_counts` caught
   `safe-seat-submission-metadata.md`; it did **not** catch `safe-seat-submission-notes.md:95`
   ("it asserts 210 figures"), which is a live present-tense restatement in a different document.
   Both corrected. The checker's reach is narrower than the restatement surface.

4. **A defect in my own basis registry, one commit old.** Four rows written in `3c54672` declared
   the four-state comparison's cycle window as *"general 2024"*. **New York is 2022** — the paper
   says so three times. Corrected to `general 2022` for `fs_ny_*` and to explicit two-cycle spans
   for `fs_all_*` / `fs_cmp_*` / `ny_ad23*`. Worth recording *why* the new consistency check
   missed it: `audit_basis_consistency` fires on **divergence** within a quantity group, and all
   four rows were uniformly wrong, so there was nothing to diverge from. A registry catches a
   *disagreement* about a basis; it does not catch a shared mistake. Correcting NY then made it
   the minority value and the check demanded a disclosure — which the paper supplies, now named.

### One wording overstatement

The abstract said *"The results are insensitive to the competitiveness threshold, holding between
74% and 98%."* A quantity that ranges 74–98 is not insensitive to the knob — WA all-seats moves
92.5% → 73.7% across the cuts, 18.8 points. Appendix A already had the accurate framing ("moves
between … and never approaches 'competitive' at any setting"). The abstract now says the
conclusion does not turn on the threshold and that a large majority are not close at every
setting tested, which is what the table supports.

### Three flags raised and WITHDRAWN after measurement

Recorded because the triage step is the round's most load-bearing rule, and it fired three times
in one round:

- **"in every state examined, 88–94% … not close"** against WA House's 87.8%. Looked like a range
  that fails to cover its own data. It is probed — `verify_safe_seat.py:644` captures both bounds
  — and 87.8 rounds to 88 at zero decimals, so the printed figure is correct and the abstract's
  narrower "three comparison states" scoping is separately checked against NY/TX/ID, whose true
  minimum is 88.0. **Both sentences are defensible.**
- **Appendix E's threshold sweep unverified.** There are indeed no probes and no derived keys for
  it — but it is **declared** in the verifier's `UNCHECKED` list with `diag_safe_seat_robustness.py`
  named as owner, and running that script reproduces the paper's table **exactly**: WA
  95.9/91.8/87.8/80.6/76.5, NY 94.0/92.0/88.0/85.3/82.0, TX 98.0/96.0/94.0/91.3/86.0, ID
  95.7/92.9/92.9/91.4/90.0, the contest gaps +8.2/+10.0/−1.4, and the 0-of-48/61/20 re-scoring.
  Declared *and* accurate.
- **The abstract is outside `AUDIT_BOUNDS`.** True, and unlike every other paper in the series.
  But its figures are reached by whole-document probes (a `section=None` probe checks every
  occurrence), and the one figure appearing only there — the 74–98% range — is the declared
  `UNCHECKED` entry above. Gating the abstract is worth doing and is **not** done here: it would
  leave the gate red pending the threshold derivation, and the `strict_units` precedent is to
  record a measured backlog rather than ship a red gate.

### One series-wide hardening item, not a defect

`^\d{1,2}$` exempts the **lower** bound of every range written `N–M%`, because `strict_units`
reads the unit character immediately after the token and in a range that character is the dash.
Measured: **87 such ranges across the nine documents** (donor 32, WA 18, safe-seat 12, cross-state
money 12, Idaho 5, synthesis 3, whitepaper 3, NY 1, money-votes 1). Safe-seat's are separately
probed, so nothing is wrong here — but coverage is not what protects them, and that is the fifth
instance of the `^\d{1,2}$` defect class. Fixing it means letting a pattern see a following dash.

### State

`verify_safe_seat.py` exit 0, **211 figures**, 205/205 keys with a declared basis.
`tests/test_infrastructure/` **425 passed, 1 skipped, 43s** — including seven new tests that show
`claim_guards()` failing four distinct ways, so the round closes its own additions per §0 rule 2.
Appendix E re-verified against its owning script. **Round 2 required.**

---

## 2026-08-10 (fourth pass) — safe-seat round 2: the withdrawn claims were live in the cover letter

**Round 2 opens on round 1's own changes.** That step is mandatory because three consecutive
rounds in this repo found the prior round's fix defective. It found three, and then the fresh
lens pass found five more in a document that had never been reviewed at all. **NOT clean.**

### Against round 1's own fix — three

1. **A disclosure citation that did not resolve.** Round 1 recorded the NY cycle divergence as
   disclosed and quoted three places in the paper. One quote — "New York is a cycle behind
   (2022)" — dropped the paper's bold markers, so `grep -F` found nothing. The substance was
   right and the citation was not. A registry cell that names where a disclosure lives is only
   worth having if the pointer resolves.
2. **The comparator probe asserted the value but not the YEAR.** Round 1 added
   `r"nearly double the next highest, (\d+) in 2020"` — with 2020 as a *literal in the anchor*.
   That checks the sentence still says 2020, not that 2020 holds the maximum. Had 2020 slipped
   to 9 while another cycle rose to 11, `tossup18_next` would still be 11 and the probe would
   pass on a wrong attribution. The year is now captured and compared to `tossup18_next_year`,
   and a tie for the maximum is a failure rather than an arbitrary pick.
3. **A ZeroDivisionError where a failure belonged.** `tossup18 / max(other)` was unguarded. A
   verifier that crashes reads as a broken run rather than as a defect in the paper.

### New — five, all in `safe-seat-submission-notes.md`

The paper is careful. Its satellite was never adversarially reviewed, and it carried **three
claims the paper had formally withdrawn** — in the document whose job is to shape the journal
framing:

4. **"111 of 133 seats were decided before November"**, as the *recommended cover-note framing*.
   The paper withdrew this on 2026-07-27 as unsupported by an ex-post margin and names the
   withdrawal in its own limits section.
5. **The candidate-non-entry reading of the contest gap** — "parties decline to field candidates
   in seats their own presidential numbers say are winnable … the pathology is strongest where
   competition *could* exist" — presented as **"the most publishable single finding here."**
   Appendix E withdrew exactly that reading: *"an earlier version of this passage read the gap as
   candidate non-entry … and that is more than the statistic supports."* The same bullet also
   said competition in Idaho is "genuinely not possible", which the paper does not claim.
6. **The same withdrawn claim again in the block marked "use verbatim-ish"** for the cover
   letter — "parties leave winnable seats unfielded precisely where competition remains
   possible." One copy-paste from a submission.
7. **"flat from 79% to 98% across 15-point to 5-point cuts."** The threshold sweep's floor is
   73.7%, printed as 74%. The 79 is the floor of the five-cycle Dimension 1 range — a different
   quantity, borrowed into the wrong sentence.
8. **The Texas verification attributed to the "press-reported unopposed list."** The actual check
   is seat by seat against the Texas Secretary of State's certified results, 54/54 exact; the
   press list covers 14 districts and Appendix F uses it only for the subsidiary point that TLC
   omits uncontested races at the primary stage too. This one *understates* the paper's rigour,
   which is the rarer direction and still a false statement in a submission document.

### The gate that did not exist

Nothing anywhere checked whether a withdrawn claim reappears. `audit_satellite_counts` compares
figure **counts**; `check_cross_doc_consistency` compares **figures**, and deliberately excludes
the ledgers and audit log as append-only history. A withdrawal was recorded in prose and enforced
by nothing — and a withdrawn claim is *usually* withdrawn because it is not checkable, so there is
no derivation to compare it against. That is precisely why it survives.

New: **`docs/reference/withdrawn_claims.csv`** (8 claims across four papers, each with why and
where) and **`tests/test_infrastructure/test_withdrawn_claims.py`**, which asserts a sentence is
**absent** rather than that a number matches. Quoting a withdrawn claim is allowed where the
surrounding 700 characters mark it as retired — this register does, and so do the ledgers — and a
bare restatement fails.

**Shown failing on the real defect, not synthetically**: replayed against round 1's verbatim text,
the gate catches all three restatements by claim id. Run across the other eight documents it finds
**zero** further live restatements, which is the first evidence that this defect is confined to the
one unreviewed satellite. One tightening: the whitepaper was whole-document exempt in the first
draft because it narrates the WA-03 correction; removing that exemption was tested and the
retirement-marker window handles it with zero violations, so the blanket waiver came out.

### State

`verify_safe_seat.py` exit 0, **212 figures**, 205/205 keys with a declared basis.
`tests/test_infrastructure/` **441 passed, 1 skipped, 43s** — including 13 withdrawn-claim tests
and 10 `claim_guards` tests. **Round 3 required**; the paper stands at 0 of 2 consecutive clean
rounds, and rounds 1 and 2 between them produced nine defects on a paper whose own prose is among
the most careful in the series.

---

## 2026-08-10 (fifth pass) — safe-seat round 3: the gate I shipped yesterday was 56% effective

**Round 3 opened on round 2's changes and its sharpest finding is against round 2's own new gate.**
Fourth consecutive round in this repo to do that, and the second such gate I have written. **NOT
clean.**

### The gate was nearly a no-op, and it was hiding a live violation

Round 2's withdrawn-claim gate permitted a quotation wherever the surrounding **700 characters**
contained any of nineteen "retirement marker" words — including `rather than`, `corrected`, `no
longer`. It shipped with a demonstration that it caught all three real defects. **That
demonstration used the phrases in isolation, with no surrounding document.** It tested the matcher,
not the mechanism.

Measured properly — injecting the withdrawn phrase at every paragraph boundary of every
non-history document, 3,481 positions — round 2's gate caught **55.8%**. Where it mattered most it
was far worse:

| document | caught |
|---|--:|
| `safe-seat-washington.md` | **15.9%** |
| `donor-class-submission-notes.md` | **3.4%** |
| `donor-class-cover-letter.md` | 32.1% |
| `safe-seat-submission-notes.md` | 46.7% |

The mechanism inverted itself: these papers have been revised heavily, so correction language is
everywhere, so a marker was almost always within 700 characters. **The documents most likely to
carry a stale claim were the ones the gate protected least.**

**And it was hiding a real violation present when it shipped.**
`ensemble-gerrymander-proposal.md` opened its premise with *"The safe-seat paper established two
facts: ~85% of Washington's legislative + congressional seats are **decided before November**"* —
the withdrawn claim, asserted as an established fact, in the foundation of a proposal. Waived
because "rather than" appeared 700 characters away. Corrected to the observed measure (79–88%
finished ten points apart or uncontested; 83.5% in 2024).

No window setting fixes this. A sweep of six window/vocabulary configurations traded catch rate
against breaking legitimate quotations at every setting (narrow vocab at 120 chars reached 97.6%
but broke eight real ones). **Inference from nearby wording is the wrong mechanism.**

### The replacement

`docs/reference/withdrawn_claim_quotations.csv` records each permitted quotation by a verbatim
44-character `anchor_before` plus a written reason; everything else fails. That is the repo's
standing exemption rule applied to sentences, and it is **prose-free** — no markers go into
published text, so the papers read as written. Twelve sites recorded, each judged individually.

**Measured: 3,481 of 3,481 injections caught, 100%, zero waived.** The cost is that reflowing a
paragraph can break an anchor — the same discipline the prose probes already carry, where an
anchor matching nothing FAILS rather than skipping.

### A second real violation, in the lead article's satellite

`donor-class-submission-notes.md` item 7 restated the reviewer's premise that the 480-record
blinded pass "was AI-adjudicated". The repo's own record — `CLAUDE.md`, the A15 row in the release
checklist, round 16 — states that **the author rated all 480 records and every pass since**, and
that the AI-adjudication claim was inferred from the paper's wording and was wrong. The *action*
(an independent second rating) was taken and is closed as A9x; the *reason recorded for it* was a
withdrawn claim, restated as fact in a submission document. Corrected, and the correction is
anchored rather than asserted.

### Round 2's other changes, re-examined

The year-capturing comparator probe, the tie guard and the zero-division guard all hold, and the
corrected NY disclosure quote now resolves verbatim at all three cited sites. No further defects
there.

### State

`verify_safe_seat.py` exit 0, **212 figures**, 205/205 keys with a declared basis.
`tests/test_infrastructure/` **443 passed, 1 skipped, 44s**. **Round 4 required.** Three rounds
have produced eleven defects, and the two most serious were both in gates or satellites rather
than in the paper's own prose — which is the round-3 lesson worth carrying: *this paper's argument
is holding up better than the machinery built to check it.*

---

## 2026-08-10 (sixth pass) — safe-seat round 4: the register was half the surface

**Round 4 opened on round 3's changes and asked the completeness question**: does the register
cover every withdrawal the nine papers document, or only the ones somebody happened to notice?
**NOT clean**, and the answer is the finding.

### 100% effective on 44% of the surface

Round 3 measured its rebuilt gate at **3,481/3,481 injections caught** and reported that as the
headline. It is true and it was the wrong number to lead with. A sweep of all nine papers for
withdrawal language — "has been withdrawn", "is retired", "an earlier version claimed", "was
false", "must not be quoted" — finds **16 withdrawal sentences across nine papers**, against the
**8 claims** rounds 2 and 3 had registered, drawn from only four papers.

So the gate was precise over half the surface, and **precision without coverage reads exactly like
coverage.** It is the same shape as the satellite-count allowlist that carried seven of eight
papers by not looking at them, and as `_COVERAGE_SKIP`'s `^\d{1,2}\.\d$` that was blind to most of
what it existed to find.

The register is now **19 rows: 15 pattern-enforced, 4 unpatternable**, with 23 anchored quotation
records. The additions came from every paper that had a withdrawal, not just the ones already
represented — donor-class, cross-state money (three), the synthesis (two), safe-seat.

### Four withdrawals cannot be guarded by a pattern, and one reason is actionable

Recorded with `enforcement: unpatternable: <why>` so the gap is countable rather than absent:

- **`who-decides-idaho.md` records that a three-state registration superlative was withdrawn but
  never quotes the withdrawn wording.** There is no phrase to forbid. **Convention going forward:
  when withdrawing a claim, quote it** — a withdrawal that does not preserve its own text cannot
  be enforced against, only remembered.
- The donor paper's Republican federal skew (+4.2 → −0.1 under age standardization) is a *number
  in a table*, guarded by the verifier asserting the standardized value instead.
- `who-decides-washington.md`'s rate-share defect is a **naming collision between two live
  measures**, not a retired phrase.
- The whitepaper's 0.61 correlation is a bare figure too generic to forbid without false positives;
  `verify_whitepaper.py` asserts 0.578.

### One more real violation, again in paste-ready metadata

`safe-seat-submission-metadata.md` carried, as a **completed checklist item**: *"New York's
missing seat identified as Assembly District 23; effect bounded to 88.0–88.7%."* That bound was
**retired** — AD-23 was resolved from the certified NYSBOE contest rather than estimated, the
chamber is complete at 150, and it reads a single 88.0%. The paper's limits section says so. The
retired range was still standing in the document whose fields get pasted into a submission form.

That is the third defect in three rounds found in a **satellite** rather than in the paper. The
pattern is now unambiguous enough to state as a rule: *the papers are in better shape than the
documents that describe them.*

### State

`verify_safe_seat.py` exit 0, **212 figures**, 205/205 keys with a declared basis.
`tests/test_infrastructure/` **452 passed, 1 skipped, 42s**. **Round 5 required.** Four rounds,
thirteen defects; rounds 3 and 4 each found their predecessor's gate materially weaker than
claimed, which is the argument for the two-consecutive-clean-rounds exit rule rather than a
one-pass sign-off.

---

## 2026-08-10 (seventh pass) — safe-seat round 5: CLEAN on the paper, and a scope decision

**First clean round for `safe-seat-washington.md`.** No finding that changes a number, a claim or
a stated limit, in the paper or its satellites. One of the two the exit rule requires.

### Where round 5 looked, because a clean round has to say what it examined

Round 4 swept the nine **papers** for withdrawal language. It never read the two corrections
ledgers or the audit log — the documents whose entire purpose is to record withdrawn claims. A
claim withdrawn there but still live in a paper would have been invisible to every round so far.
Swept now: 11 withdrawal sentences in the donor ledger, 1 in the WA ledger, four candidates checked
against every live document.

**One unregistered withdrawn claim, and it is not live anywhere**: *"In every panel the biggest
bucket after matching is a key at a different ZIP5"* — false in the displayed Washington state row,
where the unresolved residual is larger. Present only in the ledger. Registered as
`donor-biggest-bucket-different-zip5`; the register is now **21 rows, 16 patterned**.

### The scope decision, recorded because round 5 nearly got it wrong

The ledger retires the all-tier totals **424,020** (NY state) and **27,250** (ID state), and both
appear in **live** Appendix F/G rows of the donor paper. That looks exactly like the defect this
register exists for. It is not: this series **deliberately retains** retired specifications as
sensitivity comparisons, and those rows are explicitly labelled *"all tiers"*. Reporting the
retired figure there is the paper doing the right thing, and forbidding the number would have
failed the paper for it.

The ledger's actual defect was narrower — Appendix C had used 424,020 as the *current* post-join
total, describing a 45,642-row expansion that 53 duplicate ids cannot produce — and that is a
**figure** defect, which the prose verifiers own.

**So: this register guards CLAIMS (phrases). Figures are out of scope, and are guarded by the
verifiers.** Recorded as its own row, `POLICY-retired-figures-are-out-of-scope`, so the next round
cannot rediscover it as a finding. It also explains three of the five unpatternable rows: their
withdrawn content is a number, not a phrase.

### Five flags raised and withdrawn across rounds 1–5

Worth tallying, because it is the clearest evidence that the protocol's **triage step** is doing
more work than its lens list. Round 1: the "88–94%" range (probed, and 87.8 rounds to 88);
Appendix E's threshold sweep (declared in `UNCHECKED`, and its owning script reproduces the table
exactly, gaps and re-scoring included); the ungated abstract (its figures are reached by
whole-document probes). Round 5: the retired all-tier totals, above; and **Appendix G's 2024
count**, which states the figure moved "from 46 to 47" while Dimension 2 says 46 — and then marks
its own supersession in detail, naming that both counts are 46 and that *"the two 46s do not
describe the same set of seats."* Five findings that were not.

### State

`verify_safe_seat.py` exit 0, **212 figures**, 205/205 keys with a declared basis.
`tests/test_infrastructure/` **453 passed, 1 skipped, 45s**.

**Round 6 required for the exit, and it must open on round 5's own changes** — the two new register
rows and the scope policy — because round 5 changed machinery even though it changed no paper text.
The clock is on the paper: **safe-seat is at 1 of 2 consecutive clean rounds.**

---

## 2026-08-10 (eighth pass) — safe-seat round 6: the clean round was one section short

**NOT clean, and the clock resets to zero.** Round 5 was clean; round 6 found a defect in a
section rounds 1-5 never opened. That is the two-consecutive-clean-rounds rule doing exactly the
work it was written for — a single-clean-round sign-off would have shipped this.

### Against round 5's own change

Round 5 recorded its claims-versus-figures scope decision as a **row in the withdrawn-claims
register**, with `paper` = "(all)" and `withdrawn_on` = the day it was written. Every column was
misused: `why_withdrawn` opened with "NOT A CLAIM", and a dated register carried a **withdrawal
date for something that was never withdrawn**. Prose was put in a data table because a table was
more convenient than a docstring. Removed; the scope decision now lives in the gate's docstring,
and `test_every_row_is_an_actual_withdrawn_claim` stops the shortcut recurring — it rejects
POLICY/NOTE ids, a blank or "(all)" paper, a malformed date, and a `why_withdrawn` that begins by
denying it is a claim.

### The paper defect: an incomplete supersession record

`### The second pass, 2026-07-28` item 4 reads *"New York's ≥12-point cell was mistranscribed,
85.2% for 85.9% (127 seats for 128)"*. Appendix E's live table prints **85.3%**. Both are right on
their own basis and nothing said so:

| | count | denominator | printed |
|---|--:|--:|--:|
| 2026-07-28 pass | 128 | 149 | 85.9% |
| after AD-23 supplied | 128 | **150** | **85.3%** |

Supplying Assembly District 23 changed the denominator, not the count — the seat was decided by
**0.046 points** and is close at every threshold. So it moved **all five** New York threshold
cells: ≥5 94.6% → 94.0%, ≥8 92.6% → 92.0%, ≥10 88.6% → 88.0%, ≥12 85.9% → 85.3%, ≥15 82.6% →
82.0%. The 2026-08-08 revision note recorded **only the ≥10 change**, because that is the one the
four-state table surfaces. The other four went unrecorded, which left 85.9% standing in one section
while the table two hundred lines away printed 85.3%.

Both places now say so: item 4 carries its basis and its supersession, and the revision note
records the full set.

**Why no gate could see it.** Appendix E and the second-pass section are outside `AUDIT_BOUNDS`,
and the threshold sweep is a declared `UNCHECKED` entry owned by `diag_safe_seat_robustness.py`.
Neither figure is probed, so nothing compared them — and they are separated by 200 lines, which is
the distance at which a human reader stops noticing either. This is the same shape as round 2's
finding, one level deeper: **not a stale figure, but an incomplete record of what a correction
moved.**

### The generalisable lesson

A correction that changes a **denominator** moves every figure computed on it, and the revision
note will tend to record only the one the headline surfaces. Worth stating as a convention: *when a
denominator changes, enumerate every figure that rests on it before writing the revision note.*

### State

`verify_safe_seat.py` exit 0, **212 figures**, 205/205 keys with a declared basis.
`tests/test_infrastructure/` **454 passed, 1 skipped, 51s**. Register 20 rows, 16 patterned.
**Safe-seat is at 0 of 2 consecutive clean rounds.** Six rounds, fifteen defects, six flags raised
and withdrawn.

---

## 2026-08-10 (ninth pass) — safe-seat round 7: I am now the defect source

**NOT clean, and the only defect was one round 6 introduced.** No pre-existing paper defect was
found. That combination is the finding.

### Against round 6

Round 6 wrote five historical figures into the paper — the New York threshold cells on the 149-seat
denominator — and presented all five as what moved. **Two are recorded in the paper's own text
(≥10 88.6%, ≥12 85.9%). Three are not recorded anywhere**: ≥5 94.6%, ≥8 92.6%, ≥15 82.6% exist
only in the note round 6 wrote. They are sound arithmetic — each published 150-based percentage
determines its count uniquely (94.0% ⇒ 141, since 140/150 = 93.3% and 142/150 = 94.7%) — but
arithmetic is not history, and whether the 2026-07-28 pass ever printed them is not something this
record can establish. The same rule CLAUDE.md states for sessions applies to figures: *do not assert
what a past pass did.*

Rewritten as a table of **counts** — which is what the source actually fixes — with the provenance
of every cell stated and the two corroborated ones named. One garbled cell (`82.0%→82.6%`) fixed in
the same pass.

### The denominator lens, run across every recorded correction

Round 6's lesson generalised into a check. Six corrections examined:

| correction | denominator change | enumerated? |
|---|---|---|
| WA universe rebuild 2026-07-27 | 74/98 House → 98; totals → 134/133 | **yes** — Appendix G's full before/after table, no-choice count, decade range, headline; second pass adds the primary/general medians and Appendix E's WA gaps |
| TX backfill | none — 54 before and after, verified 54/54 | n/a; what changed was *attribution* (51D/90R → 56D/85R), count 141 unchanged |
| TX party imputation retired | none | yes, second-pass item 3 |
| **NY AD-23 supplied** | **149 → 150** | **no** — found in round 6, now recorded in full |
| ID | none | n/a |
| WA party-string audit | none (133 throughout) | yes — and it states Dimension 1 did not move, because margins do not depend on party |

So the AD-23 case was the only unenumerated denominator change in the paper, and it is now closed.
The lens found nothing further.

### The pattern that matters more than the defect

Seven rounds, sixteen defects, six flags raised and withdrawn. By origin:

| where the defect was | count |
|---|--:|
| the paper's own prose, pre-existing | **3** |
| satellites and adjacent documents, pre-existing | 6 |
| **introduced by this review process** | **7** |

Rounds 5 and 7 found **no pre-existing paper defect at all**. Every defect in the last three rounds
was either in machinery this process added or in text this process wrote. The marginal round is no
longer converging on the paper; it is converging on my own edits.

**Recommendation, and it is a change to the protocol rather than to the paper: round 8 must be
READ-ONLY.** No edits to the paper, no new gates, no register rows — verification and reading only.
If a read-only round finds nothing, the paper is done, and the two-clean-round rule can be satisfied
without the process generating the very defects it then reports. A round that may edit cannot
produce a clean result about a paper it is simultaneously changing.

### State

`verify_safe_seat.py` exit 0, **212 figures**, 205/205 keys with a declared basis.
`tests/test_infrastructure/` **454 passed, 1 skipped, 45s**. Register 20 rows, 16 patterned.
**Safe-seat is at 0 of 2 consecutive clean rounds** — but the paper itself has been clean for two
rounds running.

---

## 2026-08-10 (tenth pass) - safe-seat round 8, READ-ONLY: CLEAN, no findings

**The first round that could not contaminate its own result.** Rounds 1-7 both examined and
modified the paper, so each round's output became the next round's defect surface - 7 of the 16
defects to date were introduced by this process. Round 8 was run strictly read-only.

**Proof of the discipline, not a claim about it:** `git status --porcelain` was **empty** at the end
of the round. No paper, satellite, script, test, register or gate was touched. The only writes were
two gitignored derived artifacts (`reports/seat_competition.csv`,
`reports/tx_backfill_verification.csv`) regenerated by running the owning scripts, plus this log
entry, which is the append-only record the protocol requires.

### What was run, including three scripts no previous round had run

`scripts/diag_seat_competition.py` - **the authoritative source for every Washington figure in the
paper, and never executed in rounds 1-7.** Rounds 1 and 5 checked Appendix E against
`diag_safe_seat_robustness.py` and the party-ratio script, which left the paper's headline
machinery unverified end to end. It reproduces **everything, exactly**:

- the seat universe, 134 / 133 / 134 / 133 / 133, reconciled against statutory sizes;
- Dimension 1, all five rows and all five not-close shares (88.1 / 78.9 / 83.6 / 86.5 / 83.5);
- Dimension 2, all five rows and shares (48.5 / 26.3 / 25.4 / 35.3 / 34.6);
- the 2024 cross-tab, cell for cell, and the one same-party contest under ten points - **USH4,
  R-v-R, margin 6.0, Dan Newhouse**;
- the threshold sweep, WA all seats 92.5 / 88.0 / 83.5 / 77.4 / 73.7 and WA House 95.9 / 91.8 /
  87.8 / 80.6 / 76.5;
- all three party-string specifications, literal / family / expansive, every cell;
- the primary/general medians 42.1 / 55.9 / 61.5 / 61.2 / 51.2 with all five cycles fully matched;
- and the eight 2016 non-major party strings the paper enumerates - six independence-flavoured plus
  the two hybrids - printed by the script itself, plus the `Democractic` normalisation.

`scripts/diag_tx_backfill_verification.py` - also never run before. 150 districts in the certified
source, **54 uncontested, 54 backfilled, exact match**; the retired presidential-lean imputation
wrong in **5 of 54** (all five Trump-carried seats a Democrat held, in South Texas); 141/150 =
**94.0%**; not-close split **56 D / 85 R**. Every figure as published.

`scripts/diag_efficiency_gap.py` - also never run before. The largest efficiency gap is **Texas at
6.5%** on the wasted-vote form, and no state exceeds the ~8-point level the paper cites from
Stephanopoulos & McGhee. As published.

### The gates, read rather than added to

`verify_safe_seat.py` exit 0, **212 figures**; all four gated sections **fully mapped**; **206/206**
derived keys with a declared basis. Mutation sweep on it: **191 keys caught, 0 UNCAUGHT, 0 failing
baselines, 15 no-probe** (at its recorded ceiling).

The advisory report lists **224 unprobed numeric tokens** document-wide. Every result-shaped one was
read: each is either a historical figure inside a revision note (27.6, 26.9, 61.6, 85.2, 85.9, 88.8
- all correctly present as history) or a live figure verified against its owning script in this
round (the primary/general medians, Appendix E's threshold rows, Appendix A's 61.3 / 59.5 / +1.8,
AD-23's 0.046, the Texas 94.0). **Nothing unprobed is an unverified result.**

### Internal consistency, checked mechanically

Every table re-derived from its own cells: chamber sums, Dimension 1 band sums and shares,
Dimension 2 category sums and shares, the cross-tab's row marginals against Dimension 2 and its
**column marginals against Dimension 1** (23 / 10 / 12 / 23 / 65), the same-party lopsided count
(15) and over-twenty count (12), and the family-versus-expansive deltas bounded by 1.5 outside 2016.
**All pass.**

One incidental confirmation worth recording: the throwaway checker written for this produced a false
failure by matching the primary/general table's year header as a universe row - independently
rediscovering the exact ambiguity `verify_safe_seat.py` solves with a section-scoped probe for the
universe table. The verifier's design decision is corroborated by an independent implementation
walking into the trap it was written to avoid.

### State

**Round 8 is CLEAN. Safe-seat is at 1 of 2 consecutive clean rounds**, and the paper itself has now
been clean for three rounds running (5 and 7 found no pre-existing defect; 8 found nothing at all).
`tests/test_infrastructure/` 454 passed, 1 skipped. **Round 9 must also be read-only** - on the same
reasoning, and because a second clean read-only round is what the exit rule is for.

---

## 2026-08-10 (eleventh pass) - safe-seat round 9, READ-ONLY: NOT clean, two findings in the scripts

**Read-only, verified: `git status --porcelain` empty.** Findings are recorded, not fixed - a round
that may edit cannot produce a clean result about a paper it is changing, and the same applies to
its scripts. Both findings go to a round 10 that may edit.

Round 9 ran the last supporting script no round had executed, and read the paper's provenance and
methods appendices as text. Two real defects, both in `scripts/`, both invisible to every gate.

### 1. Appendix C makes a labelling claim that is false for New York

Appendix C says of the superseded supporting scripts: *"the superseded cells are labelled as such in
those scripts' own output rather than removed, so the earlier published numbers remain reproducible
for audit."*

`diag_safe_seat_states.py` labels two cells - WA House `88.8%` (superseded by the certified 87.8%)
and the TX safe split `51/90` (superseded by the observed 56/85). It does **not** label New York,
which it reports on the **retired 149-seat chamber**: `NY Assembly 2022-11-08  149 seats ... 88.6%`.
The paper's four-state table reports **150 / 150 and 88.0%**, and Appendix E states both NY rows are
"now on the complete 150-seat chamber".

So a third cell is superseded and unlabelled, and Appendix C's sentence asserts that it is labelled.
Same shape as round 4's finding: a claim *about* coverage that the coverage does not support.

### 2. The withdrawn candidate-non-entry reading is live in script output, at three sites

Appendix E withdrew the non-entry interpretation of the contest gap - *"that is more than the
statistic supports"* - and round 2 found and removed it from the submission notes, where it had been
the recommended cover-letter framing. It is still asserted, as a conclusion, in the printed output
and docstrings of two scripts the paper cites for reproduction:

- `scripts/diag_safe_seat_states.py:164` - *"parties leave winnable seats uncontested"*
- `scripts/diag_safe_seat_robustness.py:244` - *"A POSITIVE gap = parties leave
  presidentially-winnable seats uncontested (worse than the map)"*
- `scripts/diag_safe_seat_robustness.py:11` - the same reading in the module docstring

**Two reasons no gate could see it, and both are gaps rather than accidents.**

First, **the withdrawn-claims register's scan surface is `docs/*.md` only.** Scripts are not scanned
at all, so a withdrawn claim asserted in a script is outside the gate by construction - and these
scripts print their conclusion to anyone following the paper's own reproduction instructions.

Second, **the registered patterns do not match the wording.** The register holds `winnable seats
unfielded` and `(parties|they) (decline|declines|declined) to field`; the scripts say *"leave
winnable seats **uncontested**"*. Neither pattern fires. The register was built from the phrasings
the *papers* used, so it inherited the papers' vocabulary and missed the scripts'.

**And I read one of these sites in round 1 without flagging it.** `diag_safe_seat_robustness.py`'s
output was quoted into round 1's notes to confirm Appendix E's table; the non-entry sentence was two
lines below the numbers I was checking, and I did not see it. That is the failure mode the lens list
exists to prevent and did not.

### The other checks, all clean

All **nine** scripts cited anywhere in the paper exist. Appendices B, C and D read end to end;
provenance, methods and the reference list are internally consistent, and Appendix B's two
outstanding-for-publication caveats (the New York loader intermediary, and full dataset citations)
are still accurate statements of what is not done. The NY Assembly seat/vote figures (89/43) are
counts and so unaffected by the 149/150 denominator question above.

### State

`git status --porcelain` empty; no paper, satellite, script, test or register touched.
**Round 9 is NOT clean, so safe-seat returns to 0 of 2 consecutive clean rounds.**

The two findings are the strongest argument yet for the read-only discipline: eight prior rounds
missed both, and round 9 found them by *running the one thing nobody had run* rather than by writing
anything. Nine rounds, eighteen defects, six flags raised and withdrawn - and the defect surface has
now moved from the paper (3 pre-existing) to its satellites (6) to its scripts (2), with 7 introduced
by this process.

---

## 2026-08-10 (twelfth pass) - round 10: the round-9 fixes, and the checks swept across all nine

### The two round-9 findings, closed

**1. `diag_safe_seat_states.py` now labels its New York cell.** Appendix C claims the superseded
cells in that script "are labelled as such in those scripts' own output"; WA and TX were labelled
and NY was not, while the script reported the retired 149-seat chamber at 88.6% against the paper's
150 / 88.0%. The row now carries `(149 = loaded returns; SUPERSEDED -> 150 with AD-23, 88.0%)`, the
docstring header went from TWO to THREE superseded cells, and a bullet explains that AD-23 was
decided by 0.046 points so the not-close count is unchanged and only the denominator moves.

The docstring also said, in the same breath, *"The NY and ID rows ... are current."* It was false
about NY and is corrected. Appendix C's sentence is now true of all three cells.

**2. The withdrawn candidate-non-entry reading is out of both scripts.** Three sites replaced with
the measured statement Appendix E uses - the gap compares two aggregate shares and does not observe
who filed, with non-entry named as one mechanism among several. Each carries what it replaced, so the
withdrawal stays findable.

### The structural fix: the gate now scans code

`test_withdrawn_claims.py` scanned `docs/*.md` only, so a withdrawn claim asserted in a **script**
was outside it by construction - and these scripts print their conclusion to anyone following the
paper's own reproduction instructions. The scan surface is now `docs/*.md` **plus** `scripts/*.py`,
and the two non-entry patterns were widened from the papers' vocabulary (`unfielded`, `decline to
field`) to cover the scripts' (`uncontested`).

Widening it immediately surfaced **11 further sites in 7 scripts**, every one triaged:

- `verify_money_votes.py` x2 - the verifier's own guard text for the WA-03 superlative, which quotes
  the withdrawn claim in order to fail on it. Legitimate.
- `score_match_validation_human.py` x3 and `diag_match_validation_human.py` - all four are the
  scripts' own record that **neither rating pass was AI**, explaining why `ai_`-prefixed legacy
  column names survive in one published ledger. Legitimate, and a good sign: the rating scripts were
  already careful about the claim CLAUDE.md is most emphatic on.
- `verify_cross_state_money.py` - the pinned expected values annotating the corrected 1.66-1.85x band
  against the withdrawn "tight 1.62-1.76x". Legitimate.
- the two round-10 correction notes above. Legitimate.

**No further real violations.** 34 anchored quotations now, 11 of them in scripts.

### The sweep across all nine papers

| check | result |
|---|---|
| **withdrawn-claim register** | 20 claims (16 enforced, 4 unpatternable), spanning **8 of 9 papers**; 0 live violations across `docs/` + `scripts/` |
| **probe mutation, all nine gates** | 2,465 caught, **0 UNCAUGHT**, 909 no-probe, 9 passing baselines |
| **basis registry** | 1 of 9 gates ENABLED; ~1,900 keys undeclared across the other eight - **the largest open item** |
| **coverage gating** | 8 of 9 run `strict_units`; `cross-state-fec-money` gates **7 of 19 sections (37%)**, donor-class 44/48, the other seven 100% |
| **range lower bounds** | **87** across nine papers still exempted by `^\d{1,2}$` - open, task 16 |
| **denominator lens** | run across all nine; see below |

### The denominator lens found no new defect, and one paper does it better than safe-seat did

Swept every paper for denominator language. The notable case is **`who-decides-new-york.md`**, whose
own text opens: *"The denominator of this table has been wrong twice, in opposite directions, and the
record of both is kept here."* That is the round-6 defect class by name - and New York enumerates it
properly where safe-seat did not:

- it names the affected set - **the eight major-party cells** - rather than the one the headline shows;
- it bounds the movement, **+0.13 to +2.67 points**, largest on the oldest cycles;
- it separates **roll-denominated** figures (all of §III, the under-30 pair in §I) from
  **electorate-denominated** ones (Appendix A, the rest of §I), and explains that the split is what
  identifies the denominator as the cause when figures move;
- it quantifies the mechanism - **20.55%** of today's active roll registered after the 2021 primary;
- and it records that its own cited script had applied the correct cutoff since its first commit, so
  *"for one week the paper and its own cited script disagreed by up to 2.67 points, and both were
  public."*

The lesson it draws is the one this series keeps relearning from the other direction: **when a
verifier and a paper disagree, the verifier is not automatically right.**

`who-decides-washington.md` and `cross-state-fec-money.md` also carry denominator corrections, and
both enumerate - cross-state explicitly states that after its drift *"every percentage in the WA row
is identical"*, which is the pattern to copy.

### State

`verify_safe_seat.py` exit 0, **212 figures**; both edited scripts run green; `tests/test_infrastructure/`
**454 passed, 1 skipped**. Safe-seat has had **two paper-affecting fixes in round 10**, so it returns
to **0 of 2** and needs two consecutive clean rounds - which, on the round-7/8 reasoning, should both
be read-only.

---

## 2026-08-10 (thirteenth pass) - safe-seat round 11, READ-ONLY: CLEAN

**Read-only, verified: `git status --porcelain` empty.** No findings.

### Round 10's changes, checked against the scripts' own output

All four four-state cells re-derived and each label confirmed against the arithmetic:

| cell | count / denominator | printed | label |
|---|--:|--:|---|
| WA House | 86 / 98 | 87.8% | superseded from 88.8%, safe D/R 54/33 -> 53/33 |
| NY Assembly | 132 / 150 | 88.0% | **149 loaded -> 150 with AD-23** (added round 10) |
| TX House | 141 / 150 | 94.0% | backfilled to 150, safe D/R 51/90 -> 56/85 |
| ID House | 65 / 70 | 92.9% | correctly **unlabelled** - it is current |

Appendix C's claim that "the superseded cells are labelled as such in those scripts' own output"
is now true of all three superseded cells. The rewritten contest-gap legend prints the measured
statement and carries what it replaced.

### The check no previous round had run

`scripts/check_cross_doc_consistency.py --tests 0`: **0 findings.**

- build metadata against computed ground truth - abstract 287, body 11,370, figures 1,324,
  sections 48 - every stated count matches the build;
- release gates - no duplicate ids, header tallies match, every open gate sequenced; 33 gates,
  29 closed, 2 open (A13, B9), 2 deferred;
- **and the orphan pass across all eight grounded paper groups: every figure stated in a
  satellite document also appears in the paper it describes.**

That last one matters more than a clean line usually does. Round 2's worst finding was in a
satellite, and rounds 2-4 found six defects there. This says the *figures* in the satellites
reconcile - which is consistent with, and sharpens, what those rounds actually found: the
satellite defects were **claims and framing**, not numbers. The figure-level cross-document
machinery was working the whole time; what was missing was anything checking sentences, which is
what the withdrawn-claims register now does.

### The rest

`verify_safe_seat.py` exit 0, **212 figures**, **206/206** keys with a declared basis. Mutation
sweep on it: **191 caught, 0 UNCAUGHT, 0 failing baselines, 15 no-probe** at its ceiling.
`tests/test_infrastructure/` **454 passed, 1 skipped**.

### State

**Round 11 is CLEAN. Safe-seat is at 1 of 2 consecutive clean rounds.** One more clean read-only
round closes it.

---

## 2026-08-10 (fourteenth pass) - safe-seat round 12, READ-ONLY: NOT clean - the public repo serves the pre-review text

**Read-only, verified: `git status --porcelain` empty in the private repo, and nothing was written
to the public one.** Findings recorded, not fixed - and the fix here is a push to a **public**
repository, which is the author's call and not a review action.

Round 12 looked **outward**, which nine prior rounds had not. Every earlier round examined the
private repo; the paper's own byline block says *"The paper source, code, and data-acquisition
recipe are public at https://github.com/skirby359/who-decides."*

### The finding

**The public repository currently serves the pre-review safe-seat paper and scripts.** Four of the
five safe-seat files differ from the private ones, and the differences are exactly the defects the
last ten rounds removed:

| defect | fixed privately | still live in the public repo |
|---|---|---|
| *"more than double any other year in the series"* - **provably false** from the paper's own table (19 tossups is 1.7x the next highest, and 2 x 10 = 20 > 19) | round 1 | **yes** |
| the withdrawn candidate-non-entry reading, `diag_safe_seat_states.py` | round 10 | **yes** |
| the withdrawn candidate-non-entry reading, `diag_safe_seat_robustness.py` | round 10 | **yes** |
| *"insensitive to the competitiveness threshold"* over a 74-98% span | round 1 | **yes** |
| the NY supersession label (149 loaded -> 150 with AD-23) | round 10 | absent |

Mechanically: the public repo is **clean and level with its own origin** (`master...origin/master`,
nothing ahead or behind), last synced from private `f41413c` (2026-08-09). Every safe-seat review
round is 2026-08-10 - `a0c5b52`, `8aa7884`, `bc4ee44`, `0435487`. So the public copy is not
mid-sync or unpushed; it is **fully published, in the pre-review state**, and has been all day.

`diag_seat_competition.py` - the authoritative source for every Washington figure - is byte-identical
in both, which is worth stating: the public *numbers* are reproducible. What is stale is the paper's
prose and two scripts' conclusions.

### The second finding, and it is the one to generalise

`docs/safe-seat-submission-notes.md` line 127 reads:

> `- [x] Public-repo copy synced (2026-07-27); the 26-line drift is closed.`

A **checked** checklist item, and false. Not merely stale - the paper has been through ten review
rounds since it was ticked, and the item carries no mechanism that would notice. This is the
`donor-class-release-checklist.md` principle - *"Every row is binary. A row that cannot be closed
stays open - do not soften it"* - failing in the one direction that principle does not cover: a row
that was **truly** closed and then silently reopened by later work.

There is a real control gap behind it. `tests/test_infrastructure/test_cited_files_are_synced.py`
exists and checks the **manifest's completeness**; nothing checks that the public copies are
**current**. A sync claim is exactly the kind of thing this series has repeatedly found written down
and unenforced.

### Everything else in round 12

`verify_safe_seat.py` exit 0, **212 figures**, 206/206 keys. `tests/test_infrastructure/` **454
passed, 1 skipped**. The four four-state cells and their labels re-verified. No new defect inside
the private repo.

### State

**Round 12 is NOT clean, so safe-seat returns to 0 of 2 consecutive clean rounds** - but the two
findings are outside the paper, and one of them is the most consequential of the whole exercise:
**ten rounds of corrections exist only privately, while the public repository the paper cites as its
source still carries a claim its own table disproves.**

Awaiting the author on the public sync. It is a push to a public repo and will not be done as part
of a review round.

---

## 2026-08-10 (fifteenth pass) - cross-state money, passes 1-3 of the four-pass protocol

First paper after safe-seat, taken risk-first: `cross-state-fec-money.md` gated 7 of 19 sections
(37%) against 92-100% elsewhere and holds 4 of the 20 withdrawn claims. Passes 1-3 of the protocol
in `session_restart_2026-08-10`; pass 4 (read-only) follows this commit.

### What the passes found, by origin

| origin | findings |
|---|--:|
| satellites (pass 1) | 5 |
| the paper's own prose, pre-existing (pass 2) | 8 |
| gate geometry / gate seams (pass 3) | 2 |
| **introduced by this round, caught before commit** | **1** |

### Pass 1 - satellites, read with the paper

The gated-section count was stated **three different ways in one file**: the notes' verdict said
"six of nineteen" and its soft-spots said "six sections", while its own checklist said "Seven
sections hard-gated". Truth is **7 gated / 12 named**, which the run prints. Both satellites said
"thirteen" remaining. The figure count read **220** in the notes' verdict and **208** under
objection 7 against a true **255**.

Three places asserted that **§F is gated**. It is not, and both files also say so elsewhere - the
notes' objection 7, and two entries in the metadata, one of them inside the **paste-ready
data-availability statement** bound for the SSRN form, which also carried "gated over §Headline,
§1, §3 and §F only; fifteen further sections" from the 2026-08-06 state. §F has never been gated:
it has carried a `COVERAGE_EXEMPT_SECTIONS` entry since the gate was ported, and the "Gated"
comment above it in `AUDIT_BOUNDS` is what misleads.

### Pass 2 - run every cited script

This is where the paper's own defects were, and every one came from running a script rather than
re-reading prose. `cross_state_state_money.py` (§K, the largest ungated section) had not been run
in the round that wrote §K's prose.

| § | figure | was | is |
|---|---|--:|--:|
| Follow-on tests preamble | committee master | 44,606 | **44,746** |
| K header + K3 | ID roster resolution, person-filer $ | 65% | **55.7%** |
| K header | TX roster resolution, legislative $ | 59% | **61.0%** |
| K2 | NY party campaign cmtes in the top 10 | "DACC/DSCC/NYSSRCC/RACC are 4, $33-43M each" | **3** of them; RACC is **$8.7M** and not in the top 10 |
| K5 | WA committee share | "69% of all WA state money ($1.05B of $1.52B)" | 69% **of the classified base**, $1.01B of $1.46B |
| G outflow | WA / NY / TX totals | $198.7M / $672.8M / $526.5M | **$198.6M / $672.5M / $526.4M** |
| H | tech $ / competitive / out-of-state | $7.1M / 11.6% / 51.9% | **$7.0M / 11.7% / 52.2%** |
| H | healthcare competitive / out-of-state | 16.1% / 35.7% | **16.0% / 35.6%** |
| K5 | the two WA ballot committees | "nine-figure-fight" | eight-figure ($31.6M, $22.4M) |

Two of these are worth more than their size. **K2's RACC claim was the mechanism sentence for
K2's headline finding** - NY's inverted 0.85x premium explained by battleground money routing
through party committees. Naming the Republican Assembly committee made the routing look
symmetric across both parties and chambers; in fact only the Democrats route Assembly money at
scale ($28.3M against RACC's $8.7M), so the routing is party- and chamber-asymmetric and the
sentence now says so.

**K5's WA committee share is a pure basis defect**, the class §0 rule 3 exists for. The 69% is
`org / (org + person)` computed over `election_cycle <= 2025`; the $1.52B denominator it was paired
with runs through 2026. Org money is $1.007B, so the printed numerator $1.05B - which is
`0.69 x 1516.4` back-computed - corresponds to no cut in the data. The sibling TX sentence in the
same bullet list uses the classified base correctly, so one bullet list carried two bases.

**§C was deliberately not run.** `diag_cross_state_donors.py` prints named individual donors with
dollar totals, which is a contribution record about identifiable people; under `CLAUDE.md`'s hard
rule that is not a script to run into a session. §C's figures are therefore unconfirmed by this
pass and it is flagged rather than silently skipped.

### Pass 3 - the mechanical sweeps, and two gate seams

**Seam 1 - four blocks sit outside every `AUDIT_BOUNDS` span.** Measured: **77 numeric tokens**
are in no slice at all, so they are neither gated nor named with an owner - the byline block (9),
§Scope and method (10, including the 6.1-8.3-point de-merging figures the concentration direction
rests on), the **"Follow-on tests" preamble (29)**, §Limits of inference (21, including the 0.0004
donor-key Gini gap), and Related work (8, publication years). The satellites' central claim - that
the remaining surface is "a per-section ledger rather than one aggregate number, the difference
between a known gap and an unknown one" - is false for these. It is a geometry gap, not an
exemption gap: `finding5` ends at `## Follow-on tests` and `test_a` starts at `### A.`, so the
preamble between them is unreachable. The stale committee-master count was sitting in it.

**Seam 2 - a stale figure count that neither gate could reach, because each defers to the other.**
The cross-doc orphan pass waives every figure-count token with the recorded reason *"verifier
figure count - checked by metadata_drift"*. But `metadata_drift` iterates `CHECKED`, which holds
**only the donor-class document set**, so it never opens this paper's satellites - the reason
names a check that is not looking, for 7 of 8 papers. The verifier's own
`audit_satellite_counts` does open them, but anchored only `asserts **N figures**`, `asserting`,
`re-derives` and `exit 0 = N figures agree`; the notes' two live claims were an arrow progression
and a passive "N figures are asserted", matching none. And the compounding part, which is the
generalisable bit: because the *metadata* file carried two claims that did match and were correct,
`n_claims` was non-zero, so the guard's "no present-tense claim found - re-anchor `_COUNT_CLAIMS`"
notice never fired. **A partially-anchored satellite set prints exactly like a fully-anchored
one.** "The guard said ok" was not evidence it had read anything.

Closed three ways: `_COUNT_CLAIMS` gained the passive phrasing; the live claim was rewritten into
the already-anchored `asserts **N figures**` form; the allowlist reason now names
`vp.audit_satellite_counts` as the owner. The arrow progression is left un-anchored on purpose -
it is history, and anchoring a progression makes every past count a failure.

Per §0 rule 2 the new anchor was shown failing before commit, and shown to be the difference
between caught and uncaught: the synthetic case yields **1 failure with it and 0 without**. Three
tests in `test_gates_can_fail.py`, one of them for the compounding case above.

**The basis registry is still 1 of 9 gates** and this paper is not the one. Both basis defects
this pass found (K5, and §I's two-basis quotation below) are exactly what `require_bases` is for.
Rolling it out here remains the higher-value work, unchanged from the restart note.

Sweeps run: withdrawn claims 26 passed; coverage audit 7 ok / 12 by reason; cross-doc 0 findings;
`tests/test_infrastructure/` **457 passed** (454 + 3 new), 1 skipped; mutation probe baseline
200 caught / 0 UNCAUGHT / 29 no-probe. Verifier **255 figures agree**, exit 0.

### The defect this round introduced, and how it was caught

**I called §I's pooled figures unreproducible and wrong. They were right.** Grepping `scripts/`
for the literal `887,201` returned nothing, and the section's named owner
(`diag_inflow_concentration_retention.py`) gives 888,230 keys and top-1% 23.3% on its own key, so
I recorded "no owning derivation" and edited the paper to the latter.

The verifier then failed on its own probe: `inflow_pooled_concentration()` in
`verify_cross_state_money.py` derives **887,201 / 23.42%** independently and asserts all four
values. The figures had an owner all along - it derives them rather than hardcoding them, so the
literal was absent from the source while the check was present. **Absence of the literal is not
absence of a derivation**, and this is the second half of this log's existing rule: before calling
a mismatch a paper defect, reproduce the published number, and suspect your own basis first.
Reverted in full.

What survives is smaller and real, and is a basis declaration rather than a correction: §I's
pooled sentence and the per-cycle table above it are on **different bases** - all recipient
offices versus House and Senate only, and a `LEFT(zip,5)` key that goes NULL on a missing zip
(collapsing those rows into the single bucket that is the `+1` in the key count) versus one that
keeps a blank zip as an empty string. Both are correct on their own basis; the paper now says so,
in the same words `who-decides-washington.md` uses for its own naming collision: the two must not
be quoted under one name.

### State

Passes 1-3 done, 15 findings, 1 of them this round's own and caught by the paper's own gate before
commit. Pass 4 is read-only and follows. The paper's remaining known gaps are unchanged and
disclosed: §K ungated, §C unrun by policy, the four unspanned blocks, and the basis registry off.

---

## 2026-08-10 (sixteenth pass) - the white paper, four-pass protocol, first review round ever

Second paper in the risk-first order. It had **0 review rounds**, is a synthesis whose content is
almost entirely restatements of the other seven papers, and turned out to be the least-gated
document in the series.

### The headline: a control the register said existed, and did not

`docs/reference/withdrawn_claims.csv` carried the retired "median Gini ~0.61" claim with an
**empty `forbidden_pattern`** and this `enforcement`: *"unpatternable: a bare figure too generic
to forbid without false positives. Guarded by verify_whitepaper.py asserting 0.578."*

No verifier asserted 0.578. `verify_whitepaper.py` scraped `### 4. Money and votes` onward, so
Finding 3 sat outside both its probes and its coverage audit; `grep -rn "0\.578" scripts/verify_*.py`
returns nothing. So for two days the withdrawn claim had **no guard of any kind** — not a
pattern, not a probe — while the register recorded one. **Second instance in this repo of a
control written down as working that did not exist**, after the two BitLocker/dropboxignore
controls of 2026-08-01, and the first inside the instrument built to stop retired claims
returning.

Closed by making the sentence true rather than by softening it: the scrape now begins at Finding
3, the section is in `AUDIT_BOUNDS`, and eleven probes assert its figures — including one
anchored on the very sentence that retires the 0.61, so rewording the withdrawal out from under
it fails the gate. Verifier **101 -> 120 figures**.

### Coverage was 35% of the paper, with no ledger for the rest

The span-complement census (built last pass, reused here as intended) found **312 of 482 numeric
tokens outside every `AUDIT_BOUNDS` span** — and unlike every other paper in the series,
`COVERAGE_EXEMPT_SECTIONS` is **empty**, so the ungated remainder is not even named with an
owner. Two contiguous blocks: everything from the title through Finding 3 (177 tokens), and
everything from Boundary of inference to the end (135). That includes the 22/100 headline index,
the whole data-provenance block, Findings 1-3, the boundary section, and all eighty cells of
Appendix A. Finding 3's gate brings this to 4 of 4 findings gated; the Scope, Method, Boundary,
Verdict and Appendix blocks remain, and closing them is the recommended next step rather than
something this round attempted.

### Finding 3's figures had drifted, and nothing could see it

Derived on the section's own basis, against what the paper printed hours earlier the same day:

| figure | paper | derived |
|---|--:|--:|
| federal recipient-cycles (>=100 donors) | 822 | **834** |
| state recipient-cycles | 1,989 | **1,997** |
| pooled recipient-cycles | 2,814 | **2,831** |

Every other cell reproduced exactly: median Gini 0.5784 / 0.5795, the $25 median in both money
systems, the $2.5M state maximum, the $929,600 federal maximum, the 71% state share. All three
drifts are **upward**, which is the direction the accruing 2026 PDC cycle predicts — this is
audit-log section 0's "one thing that is genuinely still moving", landing in the one finding with
no probe on it. The counts are corrected and the basis is now declared in the paper, including
the point that **pooled is a separate grouping and not the sum** (834 + 1,997 != 2,831, because a
recipient-cycle below the threshold in each system alone can clear it pooled) — which explains
the paper's own 822 + 1,989 != 2,814 as a property of the design rather than an arithmetic slip.

### Finding 2's projected band counts are correct, and rest on an unpinned "latest snapshot"

WA 53/59, NY 206/240, TX 167/205, ID 34/37 all reproduce **exactly** — but only against the
latest `as_of_date` per state. `forecast_predictions` holds several snapshots per district: TX has
220 districts on 2026-06-08 and 205 on 2026-06-12, and pooling both gives 181/220 = 82% instead
of 167/205 = 81%. Nothing probes these four cells, and the memory note schedules a **final
pre-November re-lock of all three states**, at which point all four move silently and the stated
"Texas differs by 13 points" moves with them. Recorded as a disclosure item, not a defect.

### What the cross-document instrument does not cover, and why registering it is not trivial

**The white paper is in no `check_cross_doc_consistency.py` group** — neither as a `verified`
document nor as a satellite of one. The single paper in the series whose content is restatements
of the other seven is the one paper the cross-document checker never opens. Its own verifier
scans it (`audit_satellite_counts` reports "no satellite documents registered; scanning the paper
itself only"), but that compares figure COUNTS, not figures.

Measured what registering it would cost, rather than assuming: of the white paper's numeric
tokens, **27 appear in none of the eight source papers**. Most are legitimate — Finding 3's and
Finding 5's own derivations, retired values quoted in correction notes, literature figures from
Cook and Ornstein, a statute number, the backtest MAEs. So a naive registration reports ~27
findings, and silencing them needs broad numeric entries in `ALLOWLIST`, which
`_allowlisted(value, excerpt)` applies **globally across every group** — waiving those values in
the other seven papers' satellites too. **Not registered this round for that reason**, which is a
design limitation worth stating plainly: the orphan pass compares document text, so it cannot
express "verified by this paper's own verifier", and that is exactly what a synthesis paper's own
derivations are. The fix is a per-group allowlist, not a bigger global one.

### Everything that reproduced

Worth recording, because it is most of the paper. The Method/Scope inventory is exact on every
cell: 8,599,537 contributions (~8.6M) at $1.042B (~$1.04B), 16,086,508 voter-score rows (~16.1M),
5,474,670 distinct ld-scope voters (~5.5M), 314,974 matched donors, 27,112,653 VRDB vote records
(~27.1M), 5,122,520 precinct rows (~5.1M). Finding 1's turnout figures all trace to
`who-decides-washington.md`. Findings 4-6 were already gated and pass. The boundary section's
inflow/outflow shares match `cross-state-fec-money.md` section G. Appendix A's unweighted mean
reproduces at 18.3 from its own column.

**"22 elections" is correct and I nearly called it wrong.** The warehouse holds 23; the 23rd is
the 2026-08-04 primary, which the JSON path writes to `contest_results` and not to
`precinct_results`. The sentence says "~5.1M precinct-result rows across 22 elections", and
exactly 22 elections have precinct rows. Third time this pass that checking the basis before
editing prevented a false report — the other two were the TX 205 denominator and the Finding 3
counts, where the basis check confirmed the drift instead.

### Rule 2

The nine new probed keys were swept before commit: **9 caught, 0 UNCAUGHT**. The two
intermediates the first version left unprobed (`whale_max_state` in dollars, the state median
gift) were removed rather than waived — an unprobed derived key is the `e3938bd` shape, and this
verifier's `no-probe` ceiling in `test_probe_mutation_roster.py` may only fall. It is back at 16.
The state median is now a hard-stop assertion instead: the paper claims $25 "in both money
systems", so a divergence must break the gate rather than sit in a second cell restating the
first. `probe_mutation_2026-08-10.csv` re-measured across all nine gates.

### A finding from re-measuring the artifact, which is not about this paper

Re-sweeping all nine gates turned up `verify_safe_seat.py` at **15 `no-probe` keys against a
pinned ceiling of 14**, with nothing in this session having touched that verifier.

The 15th key is **`_tossup18_ratio`**, found by diffing the old artifact's no-probe key list
against the new one. It is legitimate: the safe-seat round-1/2 work that found *"more than double
any other year"* false replaced it with *"nearly double"* and added this key to keep the weaker
wording honest, guarded at `1.5 <= ratio < 2.0` inside `claim_guards()`. It is consumed by that
guard rather than by a probe — the same category as `zerovote_*`.

**It is not uncatchable, and that was checked rather than argued.** Feeding `claim_guards` the
sweep's own `perturb(1.7) = 12.1` returns one failure naming the sentence. The sweep reports it
as `no-probe` only because the harness re-runs the PROBES after perturbing a key, not `main()`'s
structural guards. So for guard-consumed keys, `no-probe` means "not probe-reachable", not
"corruptible in silence" — a distinction the roster test's docstring already draws for
`zerovote_*` and which now has a second instance.

**Why it went unnoticed is the transferable part.** The artifact was measured at `6bc5a55`, and
three commits touched `scripts/verify_safe_seat.py` afterwards (`3c54672`, `a0c5b52`, `ed51566`).
Nothing forces a re-measure when a verifier changes, so the ceiling read 14 against a real 15 for
the entire twelve-round safe-seat review and `test_no_probe_counts_have_not_grown` went green on a
stale frame. This is the concrete instance of the handoff's open item that
`probe_mutation_*.csv` carries no git HEAD. Ceiling raised to 15 with the key named and the
evidence recorded; **the staleness gate that would have caught it — fail when
`git log <artifact-head>..HEAD -- scripts/verify_*.py` is non-empty — is deliberately NOT built
in this round**, because it needs the artifact to carry its HEAD first and this round has already
changed enough.

### State

Passes 1-4 done. Findings: 1 false control, 1 coverage gap at 65% of tokens, 3 drifted figures,
2 disclosure items, 1 uncovered cross-document surface, and 1 stale-ceiling breach in another
paper's gate. No defect introduced by this round.
Remaining for this paper: gate the Scope/Method/Boundary/Verdict/Appendix blocks, pin or probe
Finding 2's snapshot basis, and give the orphan pass a per-group allowlist so a synthesis paper
can be registered without weakening the others.

---

## 2026-08-10 (seventeenth pass) - does-money-move-votes, four-pass protocol

Third paper in the risk-first order. **The body is the cleanest in the series so far and every
defect was outside it** - in the Limits section, Appendix B, and above all the satellites, which
still described the paper as it stood before the 2026-08-08 backfill and the C6.3 ingest.

### Where the 13 findings were

| origin | count |
|---|--:|
| satellites (pass 1) | 9 |
| the paper's Limits / Appendix B (pass 1) | 3 |
| a naming collision spanning body and Limits | 1 |
| the paper's cited scripts (pass 2) | **0** |
| introduced by this round | 0 |

### The paper: three live assertions of a claim it withdraws in its own Finding 3

Finding 3 states plainly that the PDC publishes support/oppose in form C-6's C6.3 section, that
the earlier "carries no support/oppose flag" reading "was a limitation of our own extraction", and
uses the resulting $51.7M / 129-cell panel. Two other sections had not been revised with it:

- **Limits:** *"State-legislative IE is excluded entirely for want of a directional flag, so the
  largest available body of Washington IE never enters the analysis."* The largest available body
  of Washington IE is Finding 3.
- **Appendix B:** *"PDC independent-expenditure records for state legislative races, which carry
  amounts and races but no directional flag."* Same claim, in the provenance appendix a
  replicator reads.
- **Appendix B, separately:** *"FEC Schedule E for the 2024 cycle"* - the panel spans five cycles
  and has since 2026-08-08.

**The register had a row for this withdrawal and it could not reach any of them.**
`wa-pdc-ie-no-direction` carries only the cross-state paper's phrasing (`does not include the
target candidate`), which appears nowhere in this paper. This is the round-10 lesson recurring in
a second paper: the register held the wording of the document where the claim was first caught,
not the wording of every document that made it. New row `money-votes-pdc-ie-no-flag` with a
wrap-tolerant pattern - `\s+` throughout, because the register matches RAW file text and both
retired sentences hard-wrap mid-phrase, so a literal-space pattern would have matched neither.
Two permitted quotations anchor the correction notes. **Shown failing before commit** (rule 2):
reinstating the Appendix B wording verbatim trips the test and names the claim id.

### The naming collision: two different 129s

Verified against the pinned frame `overperformance_cells_2026-08-01.csv`:

- **129 legislative** baseline cells (of 163 baseline-scorable; the other 34 are congressional).
  This is the denominator in the allocation limit "40 of 129" and the frame Finding 3's
  legislative panel is matched to.
- **129 of the 163 carry both-side finance** - Finding 1's correlation frame. **Only 98 of those
  are legislative.**

Equal by coincidence, different populations, and the paper never distinguished them. Same class as
`wa-rate-share-quoted-under-one-name`, already a registered withdrawn claim in the WA paper.
Declared in Appendix C.

### The satellites: nine items, all pre-backfill

The notes file described a paper that no longer exists. "A null with n=7"; "Appendix E prints the
full 10-row cross-section so the reader can see n=7 directly" (it is 40 rows and n=34); "n = 7 …
the script refuses to infer from it"; a bottom-line verdict that "a fourth cannot be run"; and an
entire prospective section, *If the IE backfill happens later*, describing as future work
something done on 2026-08-08 - which also re-quoted the retired negative slope in a live framing.

Two are worse than stale because they are **instructions**:

- Both satellites told the pre-upload reader to *"confirm `diag_ie_vs_margin.py` still prints
  INFERENCE WITHHELD"*. The n>=10 threshold was deliberately crossed by the backfill, and the
  paper says so in Appendix C. Following that instruction today means treating the paper's central
  result as a failure - the check had inverted.
- The notes' Deferred list called **"the PDC support/oppose flag … the single highest-value fix in
  this whole series"**, worth "a separate short note to the Commission". There was nothing for the
  Commission to fix. That is a recommendation to a state agency resting on our own extraction
  error, still live in a submission document after the paper had withdrawn the premise. Struck
  through and recorded rather than deleted.
- The metadata's checklist defended the second data-availability paragraph on the grounds that
  "the PDC flag gap is a finding, not boilerplate" - defending the withdrawn version of the claim
  while the paragraph itself now records the correction.

### Pass 2 found nothing, and that is the result

Every cited script was run and every figure diffed. **Zero mismatches.**

- **Appendix E's full cross-section: 160 cells across 40 rows, all exact.** This is the paper's
  largest table and sits in an ungated section.
- Federal 2c: n=34, slope +0.515, bootstrap [-0.600, +2.821], r +0.186, $0.03M unresolvable of
  $75.72M - all exact.
- Legislative Finding 3: all four specifications exact, including the materiality counts 17/53/28/60
  and the 13-47% band.
- Both secondary tests exact: early -1.128 / late +2.129 / R2 0.083, 15 material and 11 in both
  windows, corr +0.753; placebo n=14 +0.878 flipping to -0.716 on cd03/22, contemporaneous +1.108
  to +4.415 on cd08/18, persistence +0.031.

**One apparent defect was mine, for the fourth time this session.** The live
`diag_pdc_ie_vs_margin.py` prints the express/race-matched upper bootstrap bound as **+22.408**
where the paper prints **+22.409**, and the bootstrap is deterministically seeded, so that looked
like a transcription error inside a gated section that a 0.005 tolerance would hide. It is not:
the paper is asserted against the **pinned** panel `pdc_ie_vs_residual_2026-08-09.csv`, and
recomputing the bootstrap from the pin gives 22.409 exactly. The live figure has drifted by 0.001
in one day as the PDC table accrued - the pin doing precisely the job it exists for. Compare a
figure against its DECLARED basis, not against whatever the script prints today.

### Coverage

37% of numeric tokens are inside a gated span (376 of 599 outside), on the same span-complement
census used for the previous two papers. `AUDIT_BOUNDS` covers Findings 1-3 only, so the Abstract,
"What it means", Limits and all five appendices are ungated - which is where all three paper
defects were, and where Appendix E's 160 cells sit. The Abstract restates nine headline figures
and was checked by hand against the body this round: consistent. Gating it and the appendices is
the recommended next step.

### Also swept

The **enforcement-column audit** generalised from the white-paper round, run across all four
unpatternable register rows: `whitepaper-0-61-correlation` was the false one and was fixed last
round; `donor-republican-federal-skew-survives` genuinely is guarded (`_age_std_probes` asserts
the Republican federal standardized cell for both states and both panels); the other two honestly
claim no script control. 1 of 4 false, now 0.

Verifier 116 figures, exit 0. `tests/test_infrastructure/` 458 passed. Cross-doc 0 findings.
Withdrawn claims 27 passed.

### State

Passes 1-4 done, 13 findings, none introduced by this round. Remaining for this paper: gate the
Abstract and the appendices, and the standing human sign-off.

---

## 2026-08-10 (eighteenth pass) - who-decides-new-york, four-pass protocol

Fourth paper in the risk-first order, and **the best-gated document in the series by a wide
margin**: 84% of its numeric tokens sit inside an `AUDIT_BOUNDS` span (against 37% for the money
paper and 41% for the white paper), across nine spans including the Abstract and both appendices.
Only 81 tokens are outside any span. The §III denominator blockquote deserves its reputation as
the model to copy - it records the denominator being wrong *twice, in opposite directions*, names
which sections are roll-denominated against electorate-denominated, and states why the split
identifies the denominator as the cause.

### Eight findings

| origin | count |
|---|--:|
| satellites (pass 1) | 6 |
| the paper's own prose | 2 |
| the paper's cited scripts (pass 2) | 0 |
| introduced by this round | 0 |

### The paper: a claim its own table contradicts, and an undeclared scope

**1. "(Republican roughly flat)" in §V.** The cohort table runs REP 16.2% → 18.5% → 21.3% →
22.1%: a monotonic **+5.9 points**, a rise of a third on its own 2008 level, and the third-largest
of the three movements the sentence describes. It was also the only one of the three that made the
accounting close - with Republicans genuinely flat, a −18.1 Democratic fall could not sit beside a
+14.9 no-party rise.

Two things made it invisible. It is a **word, not a token**, so no probe or coverage rule could
see it. And the two movements it sits beside were carried as bare "~18 points" and "~15 points" -
written in POINTS rather than with a percent sign, so `strict_units` never demanded them and
`^\d{1,2}$` waived both as small integers. **All three are now derived and probed**
(`new_DEM_fall`, `new_REP_rise`, `new_NOPARTY_rise`), which closes the claim and the exemption in
one move.

**2. §III's duplicate-identifier disclosure had an undeclared scope.** The paper reports that
NYSVOTER carries 53 identifiers twice, "36 of them among active registrants", and that "8 of the
pairs disagree on party, 25 on congressional district, 1 on birth year". Measured: the three
disagreement counts are exact **only when scoped to the 36 pairs whose BOTH rows are active**.
Across all 53 pairs they are **13, 41 and 2**. The sentence read as though 8/25/1 described the 53.

Both scopes are now stated and all eight figures asserted. They had been exempt: every number in
the disclosure is a one- or two-digit integer, so `^\d{1,2}$` waived an entire data-quality caveat
the paper had gone out of its way to publish. This is the repo's own `derive, don't exempt`
principle applied to a section the coverage audit already called "fully mapped" - a reminder that
"fully mapped" means every token is probed *or exempted*, and a section can be fully mapped while
its load-bearing sentence is neither.

I nearly filed a third defect here and it was mine. Reading "36 of them among active registrants"
naturally, then measuring, I got 50 ids with at least one active row, and 13/41/2 for the
disagreements - so the paper looked wrong twice. It is not: "both rows active" is 36 exactly, and
the disagreement counts reproduce on that subset to the digit. **Fifth time this session that
measuring the basis before writing prevented a false report.** The pattern is stable enough now to
state as a rule: when a paper's figure does not reproduce, enumerate the candidate scopes before
concluding anything.

### The satellites: six, four of them from the paper's own reorder

The 2026-08-06 reorder (§II-§VI became §I-§V, the replication demoted to Appendix A) is documented
in the paper's Appendix B precisely so old citations keep resolving. The notes file was not fully
migrated with it:

- Objection 3's answer cites **§VI**, which the reorder eliminated.
- The pin checklist item cites **§IV's** recompute blockquote; it is §III, and line 176 of the same
  file says §III. The file used both conventions with nothing saying which.
- The coverage-gate item claims the gate covers "§I-§V, Boundary and Appendix A" - seven spans
  against the actual nine, omitting the **Abstract** and **Appendix C**. The metadata file has the
  full list, so the two satellites disagreed.
- The Deferred "causal design on timing" bullet rests on **"2019 legislation"** while the paper's
  "What it means" and this file's own item 5 both rest the natural-experiment framing on **Chapter
  741 of the Laws of 2023**. They may both be true of different offices; nothing here establishes
  that, and the bullet reads as pre-Chapter-741 text that survived the round which added it.
  **Flagged for the author rather than silently rewritten** - it is a claim about New York statute,
  not a figure, and guessing which statute a difference-in-differences would exploit is not mine
  to do.

And two in the metadata's pre-upload checklist, which is the class this session has learned to
read as *instructions*:

- **"[ ] §I's under-30 turnout pair resolved (see the open author question above)"** sat unchecked
  while the front matter of the same file, and the notes' checklist, both recorded it closed on
  2026-08-08 at 32.8 / 16.6. An open item that is actually shut is an instruction to redo settled
  work.
- The roll-pin item was dated **2026-08-01** only; the pin was re-taken 2026-08-08 to add
  registration dates, which is what the corrected denominators require.

### Pass 2

Every figure the verifier asserts reproduced, and the internal arithmetic of the ungated §IV band
table checks out by hand: both chamber rows sum to 26 and 150, the D-leaning counts are 19 and 105,
the ±5 count is 21, the D+40 total is 64, and both R+40 cells are zero - so "no New York district
at either level is R+40" and "64 seats safe for Democrats, none for Republicans" are both exactly
what the table says. Appendix A's 1.73x odd-year turnout ratio, Appendix C's 1.39-point ceiling and
78.64% survival, and the pin's 13,540,505 / 12,448,034 against the raw file's 13,540,558 /
12,448,081 all reproduce.

### Rule 2

Eleven new probed keys, swept before commit: **11 caught, 0 UNCAUGHT**, and this verifier's
`no-probe` count held at its 65 ceiling. Verifier **228 → 239 figures**; the satellite guard caught
all four stale "228" claims on the first re-run, which is the guard doing exactly what it was
widened for two rounds ago.

### State

Passes 1-4 done, 8 findings, none introduced by this round, one referred to the author (the 2019 /
Chapter 741 statute conflict). Remaining for this paper: gate the three small uncovered blocks
(byline, "What it means", Appendix B - 81 tokens), the statute reconciliation, and the human
sign-off.

---

## 2026-08-11 (nineteenth pass) - who-decides-idaho, four-pass protocol

Fifth paper in the risk-first order, and the best-gated yet: **90% of numeric tokens inside an
`AUDIT_BOUNDS` span** (against NY's 84%, the money paper's 37%), nine spans, only 59 tokens
outside — the byline, "The question", and "What it means".

**Every one of the paper's own defects was in those uncovered blocks or in a cross-reference.**
That is the sharpest illustration yet of what the coverage gate does and does not do: it audits
numbers inside spans, and this round's findings were an inference, a section number, and two
series sharing a description.

### Nine findings

| origin | count |
|---|--:|
| the paper's ungated blocks | 3 |
| the paper's cross-references | 2 |
| the paper's gated §IV (two series, one description) | 1 |
| its verifier's runnability | 1 |
| satellites | 2 |
| introduced by this round | 0 |

### The gate itself did not run

`python scripts/verify_who_decides_id.py` — the invocation the paper's front matter and
`id-submission-metadata.md`'s pre-upload checklist both give — **died with
`ModuleNotFoundError: No module named 'wa_analyzer'`**. `derive()` reaches
`from wa_analyzer.db import contributor_type_person_sql`, `pyproject.toml` puts `src` on the path
for pytest only, and this file never got the `sys.path` insert that
`verify_money_votes.py` and `verify_whitepaper.py` both received on 2026-08-10 — with a comment,
in both, ending "a gate whose documented invocation does not run is a gate that silently does not
run." Idaho was the third file that needed it and the one that was missed. Everything that
actually ran it (the release checklist, `check_cross_doc_consistency.py`, the mutation sweep) sets
`PYTHONPATH=src`, so nothing saw it — and the traceback reads like a verification failure rather
than a missing path.

Fixed with the same two-line insert. The PUBLIC copy needs no equivalent and must not gain one:
it is ADAPTED to inline that predicate, so it never imports `wa_analyzer` at all.

### A withdrawn inference, live in three places, with no register row

§V withdraws it explicitly and on the state's own results: *"An earlier version of this section
wrote that 'where the general election cannot change an outcome' the primary is the only decisive
contest; that inference does not survive its own state's results."* Democrats won **15 of 105**
legislative seats in November 2024, and **9 of the 47** single-candidate Republican primaries were
won by a Democrat.

It was live in three places, all outside every coverage span:

- **Front matter:** "a state where the November general is **a formality**".
- **Conclusion:** "in districts where the **general cannot overturn it**".
- **Conclusion:** "the **only contest that counts**".

The register's only Idaho row covers a *different* claim — the three-state registration
superlative — and is unpatternable by its own admission, so nothing reached this one. New row
`idaho-general-cannot-overturn`, `\s+` throughout because the conclusion's phrase **wraps
mid-sentence**: a literal `grep "cannot overturn"` missed it, which is the third round running
where wrapping defeated a naive search. Five permitted quotations (§V's record, the two
correction notes, the note asserting the opposite, and the verifier's own comment). Shown FAILING
before commit: reinstating the front-matter wording trips it and names the claim id.

### §IV published two series under one description

Both are asserted and both pass, which is why nothing looked wrong:

| description in the paper | 2022 | 2024 | 2026 | denominator |
|---|--:|--:|--:|---|
| "every primary ballot cast … is a Republican ballot" | 86.5 | — | 79.6 | ballots **whose choice is recorded** |
| "the Republican share of *all* primary ballots cast" | 86.1 | 83.4 | 79.5 | **all** primary participants |

They differ by 0.11 to 0.39 points — enough to print two numbers for one cycle, small enough to
pass unnoticed. Same class as the WA paper's retired rate-share-under-one-name defect and the
money paper's two 129s. Both denominators are now named in the paper and all nine cells probed.

**And the source-availability gate caught me making the money paper's mistake.** My note said
those voters' ballot choice is what "the file does not record" — a claim about the SOURCE, when
what I had measured was NULLs in the loaded table. `test_source_availability_claims.py` refused it,
correctly: the identical shape of claim was FALSE for Washington's PDC direction flag, where the
gap was our own extraction. So I checked the raw export — guarded read, `ignore_errors=true`, no
person-level column projected — and it holds exactly: **1,379 / 800 / 436** blank
`SelectedBallotChoice` against non-blank `VoteDate`, identical to the loaded NULL counts. The
loader drops nothing. Registered as `id-primary-ballot-choice-blank`, verdict `ABSENT_AT_SOURCE`.

### Two dangling cross-references

- §VI cited "the §34-904A poll-book affiliation of **Section III**". It is Section IV; the abstract
  cites IV correctly.
- §VII said *Idahoans for Open Primaries* "is the Proposition 1 campaign this paper analyses in
  **Section VIII**". **There is no Section VIII** — the paper runs I–VII and the Prop 1 discussion
  is in "What it means". A section number is not a numeric token, so no coverage rule sees it.

### Satellites

- The notes dated Proposition 1 to **November 2026**; the paper dates it **2024** in three places,
  which is correct.
- The notes' coverage-gate item enumerated "§I–§VII and Boundary" — eight spans against nine,
  omitting the **Abstract**. Exactly the omission the New York notes carried, in the same line of
  the same checklist template.

### Rule 2

Four new probed keys, swept before commit: **4 caught, 0 UNCAUGHT**, `no-probe` held at its 35
ceiling. Verifier **339 → 350 figures**; the satellite guard caught all four stale "339" claims.

### State

Passes 1-4 done, 9 findings, none introduced by this round. Remaining: gate the three uncovered
blocks (59 tokens — and they are where this round's inference defects lived), and the human
sign-off.

---

## 2026-08-11 (twentieth pass) - who-decides-cross-state, four-pass protocol

Sixth paper in the risk-first order. **77% of numeric tokens gated** across five spans; the 77
outside sit in three blocks, and 59 of them are one block running from "What it means" to the end
of the document — which therefore contains the conclusion, all of Methods & reproducibility,
Related work and the Status list. Every finding below is in that block. Fifth paper in a row where
the defects were outside the spans.

### Five findings, and four near-misses that were mine

| origin | count |
|---|--:|
| the paper's ungated tail block | 4 |
| the verifier's own docstring + its satellite | 1 |
| the paper's cited scripts | 0 |
| introduced by this round | 0 |

**1. A mangled sentence in Boundary of inference.** *"Loading Texas would: loading it would test
whether Washington's silence on party is a data limit…"* — a duplicated clause, in the paragraph
that carries the paper's central scope decision.

**2. The Status list contradicted Finding 1 on the headline multiplier.** It recorded the
2026-08-06 harmonization as producing a senior-to-youth multiplier of "1.5× to 4.9×"; Finding 1
says **1.5× to 5.1×** and is right (derived 1.499 / 5.071). Both figures were true on their own
day — the low-salience column was widened within the same round to use every contest on file
(3 / 5 / 3 rather than 3 / 2 / 1), which moved the maximum — but a status bullet reads as current
fact. Same for its "Idaho's lowest-salience cell is a number (46.7% / 5.0%)", which is now a range.

**3. The Idaho age-convention bracket named a class and meant a cell.** *"the closed-primary
electorate's dissimilarity is 27.6 on the convention used here and 29.0 on the other end"* — 27.6
is the **May 2024** primary; the tables three paragraphs earlier report the class as **25.0–27.8**,
where 27.8 is the 2026 cell. Both numbers are real (the harmonizer prints 24.96 / 27.60 / 27.80)
and the +1.4 bracket is exact for 2024, so nothing here is wrong — but "the closed-primary
electorate's dissimilarity" reads as the range's top, which is a different number. Fourth instance
this week of the same class: WA's rate-share-under-one-name, the money paper's two 129s, Idaho's
two ballot-share denominators, and now this.

**4. The verifier's docstring understated its own coverage, and the satellite repeated it.**
Both said Finding 2 "has no derivation of its own". True of the party cuts — `id_rep_65`,
`id_dem_65` and New York's per-class shares are all *scraped* from the companion papers — and not
true of the finding: Idaho's two May-2024 unaffiliated ballot counts are computed from
`id_vrdb.duckdb`, and they are what the corrected "friction, not an exclusion" sentence rests on.
A control description that is wrong in the SAFE direction is still wrong, and this session has
now found one in each direction.

### The generalisation from the Idaho round, run to completion

Idaho's verifier could not run the way its paper documented it. So all ten `verify_*.py` were
executed with the **bare documented invocation and no `PYTHONPATH`**: **ten of ten exit 0.**
Idaho was the only gap, and it is closed. Recording the negative result because it is what makes
the Idaho finding a fixed bug rather than an open class.

### Four near-misses, all mine, all resolved by measuring the basis first

Worth recording as a block, because the ratio is now stark: this pass produced five findings and
four false alarms, every one dissolved by checking a scope or a source before writing.

1. **27.6 against 27.8** looked like a stale figure; both are real cells of one ladder.
2. **The Status list's 4.9× against Finding 1's 5.1×** looked like one of them being wrong; both
   were right on their own day, which is why the fix is a date rather than a number.
3. **"Finding 2 has no derivation of its own"** looked stale because the run prints "derived"
   values for it; `derived` there means "the value this verifier computed for comparison", and for
   Finding 2 that value comes from scraping the source paper. Only the unaffiliated counts are
   data.
4. **§IV of the Idaho paper**, last round, and **NY's 36 duplicate pairs**, the round before.

**The rule this settles:** when a figure does not reproduce, enumerate the candidate scopes and
the candidate sources before concluding anything. Five for five this session, and it has never
once been the paper.

### State

Passes 1-4 done, 5 findings, none introduced by this round. Verifier **139 figures**, exit 0; the
four satellite count claims all match. Remaining: gate the tail block (59 tokens, and it is where
all four paper findings lived — the same recommendation the Idaho and money rounds made), and the
human sign-off, which is this paper's only stated blocker.

### Cross-state, second sitting — the shared metric that was not shared

Continued after the first commit, and the finding is the one the harmonization was built to
surface, so it is worth its own entry.

**The habitual-core column is not `verify_who_decides_wa.py`'s construction, although the
harmonizer's docstring says it is.** Finding 3 reads WA at 95.5–97.5%; `who-decides-washington.md`
says **92–97%** of the same three off-years, in its abstract and again in Interpretation. Both are
asserted by their own verifiers and both pass — 92.2 / 97.28 against 95.47 / 97.54 — so this is a
fifth instance this week of one description over two quantities, and the first that spans two
papers.

The mechanism, measured: the WA verifier counts every `voting_history` row for the contest, while
the harmonizer is age-banded throughout and therefore joins `voters` and requires a usable birth
year. That drops **105,969** voters from the 2021 electorate — people with a 2021 vote record and
no usable roll record — and they overlap the 2024 presidential far less, so the floor moves 92.2 →
95.5. 2023 moves 0.3 and 2025 moves 0.002.

Both figures are right for their own purpose: the harmonized one is the only cross-state-comparable
version because it is the same population in all three states, and the single-state one is right
for Washington's own paper. What was wrong was the description — the harmonizer's docstring claimed
WA's construction, and the synthesis reconciled the *dissimilarity* column's 0.05-point convention
difference in a dedicated sub-note while leaving a 3.3-point difference on the same table
undocumented. Both are now stated, and the reconciliation is **probed** rather than described:
`wa_core_lo_paperbasis` and `wa_2021_dropped` are derived here and asserted against the new
sentence, so a future revision of either paper cannot quietly re-open the gap.

Three more satellite defects, all from the same 3/2/1 → 3/5/3 widening that this round's Status-list
finding came from:

- "New York's **two** odd-year generals differ more from each other than…" — there are **five**, and
  the paper's version of that sentence uses all of them.
- The same bullet gave the 2025 NYC mayoral race as the whole explanation for that spread. The paper
  qualifies it: **2021 was also a mayoral year and reads 36.3%**, so mayoral salience does not by
  itself reproduce 2025.
- "**The habitual core is 88–98 percent everywhere**" — the derived span is 86.4–97.8, which the
  paper states correctly as 86–98.

Rule 2: two new probed keys, **2 caught, 0 UNCAUGHT**, `no-probe` unchanged at 23. Verifier
139 → 141 figures; the satellite guard caught all four stale counts.

**Round total: 9 findings** (5 in the first sitting, 4 here), one of them cross-paper, none
introduced by the round.

### Sizing the recommendation the last five rounds all made

Five consecutive papers had every defect outside a coverage span, so "extend `AUDIT_BOUNDS` over
the conclusion and appendix blocks" has been the standing recommendation. It was never costed.
Costed here for the worst-covered and only POSTED paper, `who-decides-washington.md`, which gates
**30%** of its numeric tokens — two uncovered blocks, 970 tokens, **521 of them substantive** once
calendar years and bare small integers are set aside:

| block | substantive tokens | already asserted by a probe | to do |
|---|--:|--:|--:|
| front matter + abstract + methods | 93 | 11 (abstract) | ~82 |
| Interpretation | 38 | much of it, via the 167 `prose` probes | small |
| Appendix A–D, G, End note | 54 | 0 | 54 |
| **Appendix E — 65+ by county** | **167** | **160** | **~7** |
| Appendix F — contest roll-off | 74 | 0 | 74 |
| Appendix H — one year at a time | 95 | 18 | ~77 |

**The order this implies is not the order the recommendation implied.** Appendix E is 167 tokens
and 160 of them are ALREADY asserted — the probes exist, the section simply is not in a span, so
the coverage audit never requires completeness there. Gating it costs about seven tokens of work
and converts the paper's single largest table from "probed in practice" to "probed by
construction". Interpretation is the highest-risk block — it carries the decomposition, the
lever argument and the policy caution, which is exactly where this session found claim-class
defects in five other papers — and it is the smallest at 38.

So: **Appendix E and Interpretation first**, cheap and high-value; Appendices A–D/G and the front
matter next; Appendices F and H last, because those two are the only genuine table-probe builds
(~150 tokens between them). A note for whoever does it: "probes exist" and "coverage is enforced"
are different states, and the gap between them is exactly where this paper's risk sits.

---

## 2026-08-11 (twenty-first pass) — who-decides-washington, PARTIAL round

**This round is not complete and should not be recorded as one.** What was done: the coverage
census, the verifier and its satellite guard, the two uncovered blocks read (front matter/abstract
and Interpretation/Limits), Appendix F read in full, and the corrections ledger audited. **Not
done:** Appendices A–E, G, H; the submission notes and metadata satellites; pass 2 on this paper's
cited scripts; the read-only pass. The donor article is untouched.

Recorded now because the findings are in the paper's most consequential satellite and because this
is the POSTED paper.

### The corrections ledger was the one satellite nobody registered

`who-decides-wa-corrections-ledger.md` is the document that records what SSRN 7149263 still gets
wrong. It was **not in `_verify_prose.SATELLITES`**, so nothing checked it, and it said:

> `verify_who_decides_wa.py` now asserts **246** figures (was 242)

Present tense, four rounds stale, against a real **539**. Registering it failed the gate on the
first run — which is rule 2 satisfied by the defect itself rather than by a synthetic case.

**It took a third anchor to see it, and that is the transferable part.** `_COUNT_CLAIMS` required
the `**` to span the number *and* the word "figures"; the ledger writes `asserts **246** figures`,
with the emphasis one word shorter. That is the third phrasing variant this review series has had
to add — after the money paper's `→ **N figures**` progression and its passive "N figures are
asserted". Each document invents its own emphasis, so the anchor set has to be about the WORDS and
tolerant of the markup between them. Pinned by a synthetic case in `test_gates_can_fail.py`,
because the real occurrence is now corrected and nothing in the corpus exercises it.

Two further ledger statements had moved:

- *"it has completed exactly one paper of nine"* — the condition the SSRN deferral turns on. As of
  today it is **seven of nine**. Worth keeping current precisely because the author's decision is
  gated on it.
- Of the four ranges it named as unprobed, **two since gained probes**: the habitual core (92–97%)
  and the eligible-roll senior share (~22–25%). Still unprobed: the carryover (42–48%) and
  registration tenure (16–17 years).

### The two apparent figure defects were not defects

Both dissolved on inspection, and both for the reason this session keeps rediscovering.

**The 65+ 2021 cell reads 36.7 in three places and 36.8 in two.** That looked like the
`+76.8 → +76.9 → +76.8` defect that started the cycling diagnosis. It is not: the paper documents
it at the point of use — there are two derivations, **36.7508** and **36.7497**, differing by the
composition table's `registered on or before the election` filter, and they straddle the rounding
boundary, so each printing is the correct rounding of its own basis. `check_rounding` passes on
both because both are right.

**The synthesis prints 36.8 where this paper's composition table prints 36.7.** Same story: the
harmonizer does not apply the registration filter, so it is on the 36.7508 basis. Both correct.
This is the third divergence between these two papers on the same tables — after the dissimilarity
ladder (documented) and the habitual core (documented yesterday) — and the only one still
undocumented. Worth a clause in the synthesis when someone next touches it; not worth reopening a
committed round for 0.1 on a boundary the WA paper already explains.

That makes **nine** figure mismatches this series that turned out to be scope or basis, against
zero that turned out to be the paper. The check is cheap and the prior should now be strong.

### What the census says about finishing this paper

`who-decides-washington.md` gates **30%** of its numeric tokens — the worst in the series, in the
only posted paper. 970 uncovered tokens, **521 substantive**. The costing is in the previous
entry and the order it implies is Appendix E and Interpretation first: E is 167 tokens with 160
already asserted, so gating it is nearly free, and Interpretation is the highest-risk block at 38.

Appendix F was read in full because it is 74 substantive tokens with **zero** asserted and it
carries the paper's own stated counterargument. It reproduces internally and against the body's
restatement of it — the odd-year roll-off ranges quoted in "The question" (4–25% mayor, 16–20%
port, 10–36% council, 19–36% school, 30–44% fire, against 4.9–6.6% for the statewide item) match
its table on all six. No defect, but nothing is asserting it either.

### State

Partial. Verifier **539 figures**, exit 0, three satellite claims now checked instead of two.
`tests/test_infrastructure/` **460 passed**. Cross-doc 0 findings. The paper still needs the
appendices, both satellites, pass 2 and a read-only pass before this can be called a round.

---

## WA, second sitting — the gate reported "fully mapped" over three waived results (2026-08-11)

Executed the costed order from the previous entry: **Appendix E and Interpretation into
`AUDIT_BOUNDS`**, not largest-gap-first. Verifier **539 → 563 figures**, six audited sections,
all fully mapped, exit 0.

### The finding, which is about the instrument rather than the paper

Adding `interpretation` to the bounds surfaced 18 unmapped tokens and adding `appendixE`
surfaced 3. Those were closed. **The section then reported "fully mapped" while still waiving
three real results** — "a median of about **16–17 years** since they registered, versus **12**
for the presidential electorate" is three bare integers with no unit suffix, so `^\d{1,2}$` took
all three. `strict_units`, added 2026-08-09 for exactly this class, only reaches tokens written
with `%` or `×`, and none of these is. This paper's own corrections ledger had carried
registration tenure on its unprobed list since 2026-08-06; gating the section did not clear it
and would not have.

So the lens from the Idaho round generalises and should be standing practice: **check what a
gated section EXEMPTS, not only that it passes.** Derived and probed — presidential median 12,
off-years 16 / 16 / 17, exact.

### Three literature figures that could not be closed by exemption

Lucero et al.'s 58.4 / 49.7 and Ornstein's SB 415 are external, so the reflex is
`COVERAGE_EXEMPT_LITERAL`. A literal exemption matches the BARE token **document-wide**, and all
three collide with real results in this same paper: 58.4 is also the 18–29 participation rate
(probed, in `rates`) and an Appendix H cell; 49.7 is also **Cowlitz's 2025 off-year 65+ share in
Appendix E itself**; 415 is also the upper end of the 298K–415K inactive-registrant bound. Each
waiver would have punched a hole through a section the audit calls fully mapped. They are
transcribed constants asserted at tolerance 0 instead — the treatment this file already gives the
SoS turnout benchmarks, and the right one for a figure whose only failure mode is a typo.

### Both overlap spans were computed on both bases before a word was written

|  | raw vote history | roll-joined (aged) |
|---|---|---|
| off → pres (habitual core) | 92.20–97.28 | 95.47–97.54 |
| pres → off (returned off-year) | 42.55–48.25 | 42.37–49.18 |

The paper prints 92–97 and 42–48, so both are **raw**. That settles the fifth "two quantities
under one name" on the record: the cross-state harmonizer's 95.5–97.5 is the *aged* basis of the
habitual core. Both correct, neither paper may quote the other's. Registered in
`derivation-bases.csv` with `divergence_disclosed` naming it.

### Referred to the author, not edited

Two, both recorded in `who-decides-wa-corrections-ledger.md` and both gated with the convention
they appear to use, so a later round cannot silently pick the other reading:

1. **"42–48%" is truncated, not rounded.** 42.5455 floors to 42 and half-up rounds to 43.
   `check_rounding` is right to object; widening a tolerance is forbidden here, so the truncation
   is encoded in the derivation (`presret_lo_tr`), where a genuine drift still fails.
2. **"about 40% 65+ off-year"** is the quantity printed as ~39% at line 255 and ~37–40% at line
   202. Three descriptions, one 39.07. A `round_exempt` with the reason.

Also recorded as **not** a defect, so it is not "fixed" later: Appendix E prints the
analyzable-coverage figures descending (99.6 is 2025, 95.9 is 2023) while naming the years
ascending. Nothing claims the pair is respective; the probe pins each figure to its year.

### The round's own additions, closed

Every one of the 16 new keys is `caught` under `mutation_probe_verifiers.py`, and the coverage
extension itself was seen FAILING (21 unmapped tokens) before the probes went in.

**The correction inside this round.** The first sweep read WA `no-probe` **181 → 187**: the new
derivations stored three per-year `*_presret` and three per-year `*_tenure` intermediates that no
probe consumes. That is the `e3938bd` shape precisely — derived, never read — and the tempting
move was a six-point ceiling bump with a note that they were "just intermediates", which is what
`e3938bd`'s four published-sentence keys also looked like. They are function locals now; only the
published span endpoints are keys. Ceiling held at 181.

### State

Verifier **563 figures**, exit 0, six sections fully mapped, three satellite claims matching.
Sweep re-measured across all nine gates: **2,509 caught / 0 UNCAUGHT / 910 no-probe / 3,428
rows** — WA 458 → 474 caught, every other verifier row-identical. `tests/test_infrastructure/`
**460 passed, 1 skipped**. Six basis rows registered for the WA verifier (261 of its 655 keys);
it stays in `BACKLOG` and does not call `require_bases`, because that gate demands all 655.

**Still open on this paper:** Appendices A–D, F, G, H (F is 74 substantive tokens with zero
asserted, read in full last sitting and clean), front matter and abstract, both submission
satellites, pass 2 on its cited scripts, and the read-only pass. **And the public checkout is 11
files behind** — pre-existing, from the 08-10/08-11 rounds, gate A14.

---

## WA, third sitting — Appendix H, and three slopes rounded off a rounded table (2026-08-11)

`appendixH` into `AUDIT_BOUNDS`. **Seven** audited sections, all fully mapped, verifier
**563 → 643 figures**.

### The defect: freeze rule 3, in the paper this series wrote the rule for

Three of Appendix H's per-year slopes reproduce **exactly** by differencing the appendix's own
one-decimal table cells, and not by differencing the curve those cells are rounded from:

| sentence | printed | from printed cells | from the curve |
|---|--:|--:|--:|
| 60→65 | 1.36 | (58.6 − 51.8)/5 = 1.36 | 1.3668 → **1.37** |
| 65→70 | 1.54 | (66.3 − 58.6)/5 = 1.54 | 1.5244 → **1.52** |
| 60→64 per year | 1.43 | 5.7/4 = 1.425 → 1.43 | 1.42143 → **1.42** |

§0 rule 3 says a figure computed from other figures is computed on unrounded values, and names
`df91534`/`5a7992b` — Idaho's +76.8 → +76.9 → +76.8 — as the flip it exists to prevent. That is
this, in the paper the rule was written next to. **Applied to source rather than referred**,
because the rule is the author's own standing decision on precisely this question and applying it
is not a fresh judgment; recorded as ledger item C3 so it reverts as easily as any other.

Everything the sentences argue survives: 65→70 is still the steepest five-year stretch, 1.50
against 1.42 is still "the same per-year slope", the sixties still run at roughly double the
0.83-point average. The cost is real and is stated in the ledger — a reader recomputing 1.37 from
the rounded table above it will get 1.36.

### Two claims no probe can anchor on, now checked in code

`claim_guards()`, the pattern from `verify_safe_seat.py`. Appendix H says 65→70 is **"the
steepest five-year stretch on the curve"** and that the 93→94 step is **"about ten times"** the
51→52 dip. A superlative and an order-of-magnitude carry no numeric token, so `audit_coverage`
cannot see them and a regex has nothing to capture — the blind spot that let safe-seat publish
"more than double any other year in the series" while every value it compared was asserted and
correct. Both now derived (steepest stretch begins at 65; ratio 9.72) and shown FAILING in
`tests/test_infrastructure/test_wa_claim_guards.py`, eight tests in 0.6s.

One of those tests guards a trap this round hit: an unfiltered `max()` over the retention curve
returns **age 18**, because an 18-year-old in November 2025 was 17 at the 2024 general and the
cell divides by a near-empty count. The search starts at 19, and the test asserts it still does.

### The UNCHECKED entry was wrong the same way its twin was

It covered all of Appendix H on the argument that "78 rows at a granularity where a probe per
cell buys no additional failure mode". The appendix **prints fifteen** rows, not 78 — so this was
60 cells, one derivation and one row loop, the same cost as the Appendix E table whose identical
exemption was found wrong in round 3. Narrowed to what is genuinely unchecked: the 63 unprinted
ages. The paper's own sentence describing the verifier's coverage of this appendix was stale in
the same direction and is corrected.

### State

Verifier **643 figures**, exit 0, seven sections fully mapped. Sweep re-measured across all
nine gates: **2,584 caught / 0 UNCAUGHT / 912 no-probe / 3,505 rows** — WA 474 → 549 caught,
every other verifier row-identical. The WA ceiling rises 181 → 183 for the two guard-consumed
keys, with the justification written next to it. `tests/test_infrastructure/` **468 passed, 1
skipped**. Cross-doc **0 findings**. Seven basis rows registered.

**Appendix F is what remains on this paper, and it is scoped rather than started: 104 substantive
tokens, zero asserted.** Unlike E, H and Interpretation it cannot be derived from the voter file
— three scripts, `wa_statewide.duckdb` precinct returns, apportioned ACS block-group
demographics, a precinct crosswalk, and a closing table of **partial** correlations net of five
covariates needing a residualization step no other derivation here performs. Its caveats (the
King County absence, the per-precinct ballot floor as a lower bound, contested pooled with
uncontested) are each a basis that must be reproduced exactly, not approximated. Starting it and
leaving it half-gated would breach rule 2, so it is left whole.

---

## WA, fourth sitting — Appendix F, and a caveat that paired two bases (2026-08-11)

`appendixF` into `AUDIT_BOUNDS`. **Eight** audited sections, all fully mapped, verifier
**643 → 750 figures**. This was the last and largest uncovered block in the paper: 104
substantive tokens, none previously asserted, and the only section that cannot be derived from
the voter file.

### What it took, and why the estimate held

Certified precinct returns from `wa_statewide.duckdb` for the even- and odd-year roll-off
tables; the VRDB for King's ballot share and the county-level age cut; apportioned ACS
block-group demographics and the VRDB→results precinct crosswalk for the closing table, whose
partial correlations are residual-on-residual net of five covariates and needed a Gaussian
solver this verifier did not previously carry. **Every figure reproduced on the first attempt
except two**, both halves of one parenthesis.

The verifier now **raises** if `precinct_demographics` or `vrdb_precinct_crosswalk` is absent,
rather than skipping. A reader reproducing from raw public sources can rebuild every other
section and gets a refusal on this one, which is the honest outcome — a skipped section reports
as "all figures agree" about something nothing looked at.

### The defect: a coverage caveat with a foot in two bases, one of them stale

> The crosswalk is the one of the four known to be non-randomly incomplete (86.7% statewide, and
> only 35.7% in Okanogan).

35.7% reproduced to two decimals. 86.7% would not reproduce on any basis:

| basis | statewide | Okanogan |
|---|--:|--:|
| precinct count | 91.1% | 12.1% |
| **active registrants** | **99.3%** | **35.7%** |

So the parenthesis paired a statewide **precinct-count** figure with an Okanogan
**active-voter** one — the sixth "two quantities under one name" in this series — and the
statewide half was also **stale**, being the 2026-05-16 measurement (`CLAUDE.md`: 7,135 / 8,233)
taken before the King, Whitman and Okanogan crosswalk additions. Put on one basis and the basis
named in the sentence. Ledger item **C4**, which also records the precinct-count pair in case
the author prefers the more conservative-reading version.

### Two more comparatives moved into code

`claim_guards` grows from two to four. **The grid's 17% and 34% columns are presented as the
measured contested and uncontested roll-off**, and nothing tied them together: the column says
17, the appendix says 17.2, each is asserted against its own derivation, and if the measurement
moved the grid would quietly model a scenario the paper no longer reports. Also **"Court of
Appeals (eight contests…)"**, a count spelled as a word, which is the stated reason those
contests are excluded. Both shown failing; the guard file is now 17 tests.

A third check went in on the data side of an anchor: the odd-year table prints *"none on the
ballot"* for 2023 because SB 5082 repealed the advisory votes. The probe's anchor is that
literal phrase, so it catches the paper changing but not the returns — `f_odd_statewide_2023_n`
closes the other half.

### Two filter thresholds stopped being invisible

The precinct cut's 50-vote floor was being waived by the small-integer coverage rule and its
100-voter crosswalk threshold was simply unmapped. Both are now derived parameters that the SQL
itself reads, so a threshold changed in code but not in prose (or the reverse) fails. This is
the same lesson as the registration-tenure find in the second sitting: **the small-integer
exemption is where real parameters hide.**

### The ceiling, twice in one day

WA `no-probe` measured 191 before settling at **185**. The excess was again intermediates no
consumer of any kind read — Superintendent's unpublished n and mean, a duplicate `_hi` for a
single-valued table row, per-year statewide-item counts. Made locals. Only the two keys
`claim_guards` actually reads were allowed to raise the ceiling, 183 → 185. **Both sittings today
first measured high and were brought down rather than justified**, which is the discipline the
ceiling exists to force.

### State

Verifier **750 figures**, exit 0, eight sections fully mapped. Sweep re-measured across all
nine gates: **2,661 caught / 0 UNCAUGHT / 914 no-probe / 3,584 rows** — WA 549 → 626 caught,
every other verifier row-identical. `tests/test_infrastructure/` **477 passed, 1 skipped**.
Cross-doc **0 findings**. Eight basis rows registered.

Over the three sittings of this extension the WA gate went from **246 figures over four
sections to 750 over eight**, and its sweep from 458 caught to 626.

**Appendix F was the last big block. What remains on this paper is small:** Appendices A–D and
G, the front matter and abstract, both submission satellites, pass 2 on its cited scripts, and
the read-only pass. The public checkout is still behind — pre-existing, gate A14.

---

## WA, fifth sitting — the appendices are finished, and one cited a withdrawn figure (2026-08-11)

A, B, C, D, G and the End note into `AUDIT_BOUNDS`. **Fourteen** audited sections, verifier
**750 → 797 figures**. **Every appendix in this paper is now gated**, and the ungated remainder
is the abstract, the front matter, the validation section and the limits list.

### The defect: a cross-paper citation to a number its own source had corrected

The End note described the companion safe-seat paper as counting "**≈85% non-competitive**".
`safe-seat-washington.md` records in its own corrections section that this headline moved **from
"roughly 85%" to "roughly 84%"**, and the decade range from 75–91% to **79–88%**, once 24 missing
King County seats were loaded. The framing was withdrawn as well: that correction's third item is
that "two questions were collapsed into one" — same-party generals scored non-competitive
regardless of margin, which describes **partisan availability**, not competitiveness. The
companion now reports "not close" and "no major-party choice" separately. So the sentence cited a
figure that had moved *and* a concept that had been retired. Ledger item **C5**.

**This class is invisible to every gate either paper has.** The WA verifier scrapes the WA paper,
the safe-seat verifier scrapes safe-seat, neither reads the other, and
`check_cross_doc_consistency.py` returns 0 findings because the figure is not an orphan — it is
simply wrong. Fourth defect in the series to sit in a cross-reference; first in this paper.

### Appendix B's strongest claim had nothing checking it

"In our file **every** birth value resolves to a July-1 sentinel … confirming that **no full date
of birth is stored or used here**." That is the paper's hardest privacy claim and it is
falsifiable by a single row. Nothing could see it: the only digit in the sentence is the 1 of
"July-1", which the small-integer rule waives, and "every" is a word. Counted — 5,514,767 of
5,514,767 — and guarded, with the failure message reporting the SCALE of any breach, because "one
row is not" and "twelve thousand rows are not" are different problems.

**Third instance in one day of the small-integer exemption hiding something load-bearing**, after
registration tenure and the two precinct-cut thresholds. The pattern is now explicit in the
comment above the exemption.

### Appendix A restates the body, and four of its restatements were new quantities

A is almost entirely re-quotation, which is the position a contradiction occupies: correct table,
correct appendix, and a sentence between them reporting neither. Four of its spans exist nowhere
else in the paper and so could not have been checked against anything — a **pooled**
partisan+measure roll-off range, an **all-office** odd-year range, the off-year median-age
**span** (the body reports their mean), and a **ratio** of two figures each separately asserted.
All four now derived. A fifth, "~16–17%", is a second instance of the truncated-span convention
recorded as open item 1 — 16.568 half-up rounds to 17, so the low endpoint is a floor.

### Appendix D is closed by reason, and the reason names where its figures live

A bibliography: nineteen tokens, all volume, issue, page and DOI numbers. The exemption states
where each cited work's figures ARE asserted — Lucero and Hajnal in the interpretation section,
Wattenberg in Appendix A, Kitagawa–Das Gupta as the decomposition table itself — per rule 1.

### One mechanism fixed rather than patched

The End note states how many figures this verifier asserts, which no probe can capture because
the value IS the result of the probe pass. A hardcoded literal exemption went stale within the
same sitting. It is now generated at run time from whatever the paper claims, with
`vp.audit_satellite_counts` remaining the thing that actually checks it — an exemption that
cannot go stale and start waiving a different number.

### State

Verifier **797 figures**, exit 0, fourteen sections (thirteen mapped, Appendix D closed by
reason). Sweep re-measured across all nine gates: **2,682 caught / 0 UNCAUGHT / 916 no-probe /
3,607 rows** — WA 626 → 647 caught, every other verifier row-identical. The WA ceiling rises
185 → 187 for the two sentinel-guard keys. `claim_guards` is six checks, 19 tests.
`tests/test_infrastructure/` **479 passed, 1 skipped**. Cross-doc **0 findings**. Nine basis
rows registered.

Across the four sittings of this extension the WA gate went from **246 figures over four
sections to 797 over fourteen**, and its sweep from 458 caught to 647.

**The appendices are done. What remains on this paper** is the abstract and front matter, the
validation and limits sections, both submission satellites, pass 2 on its cited scripts, and the
read-only pass. Public checkout still behind — gate A14.

---

## WA, sixth sitting — the paper is fully gated, and a number hid inside a regex (2026-08-11)

Front matter, abstract, the question, the validation section and the limits list into
`AUDIT_BOUNDS`. **Nineteen sections — every section of the paper — verifier 797 → 820 figures.**
Nothing in `who-decides-washington.md` now sits outside the coverage gate.

Front matter, abstract and limits were already fully mapped when the bounds were drawn, which is
the expected result for blocks that only restate probed figures. The work was in two places.

### A number written into a regex anchor looks probed and is not

The survivorship table's cohort sizes were pattern text — `\(n≈45K\)` — rather than capture
groups. That catches the paper being reworded out from under the probe, which is what anchors
are for, but it never compares the number to the data. Measured: 105,953 / 140,346 / **44,455**,
which to the nearest thousand is 106K / 140K / **44K**. The first two were printed exactly right,
so the convention is nearest-1K and **45K was simply wrong** — ledger C6.

The three keys had been derived and read by nothing, sitting in the `no-probe` count as dead
weight. Capturing them asserted the figures and **lowered the ceiling 187 → 184**, the first fall
in this whole extension. **Any time an anchor contains a number, ask whether it should be a
capture group.**

### The small-integer rule, a fourth time

"The question" quotes five odd-year office ranges — 4–25% mayor, 16–20% port, 10–36% council,
19–36% school, 30–44% fire. Every LOW endpoint is one or two digits, so the gate could see only
the upper half of all five. Per-office spans are now derived. That is the fourth instance in one
day, after registration tenure, the two precinct-cut thresholds and Appendix B's sentinel; the
lesson has stopped being a surprise and should now be the default assumption when a section
reports "fully mapped".

### What was deliberately NOT touched

The validation sub-note explaining that 2021 reads 36.8% on the coverage basis and 36.7% on the
composition basis — 36.7508 against 36.7497, straddling a rounding boundary — is **correct and
documented at the point of use**, and the restart notes flag it explicitly as a thing not to
"fix". Both derivations and the 0.001-point gap between them are now asserted, so the
explanation is pinned rather than merely believed. The "reproduces the snapshot column to within
0.2 points" bound also checks out: the blend of the two published numbers lands 0.170 from the
snapshot column, its true maximum across the three cycles.

### State

Verifier **820 figures**, exit 0, nineteen sections (eighteen mapped, Appendix D closed by
reason). Sweep re-measured across all nine gates: **2,695 caught / 0 UNCAUGHT / 913 no-probe /
3,617 rows** — WA 647 → 660 caught, every other verifier row-identical.
`tests/test_infrastructure/` **479 passed, 1 skipped**. Cross-doc **0 findings**.

Across the five sittings of this extension the WA gate went from **246 figures over four
sections to 820 over nineteen**, and its sweep from 458 caught to 660.

**The paper is fully gated.** What remains is not coverage work: both submission satellites,
pass 2 on its cited scripts, the read-only pass, three items referred to the author, and the
public checkout (gate A14).

---

## Series harness — a bolded small integer is a result (2026-08-11)

Two things, one of them series-wide.

### Ledger open item 2, resolved

The interpretation section's "about 40% 65+ off-year" is the 39.07% the ladder discussion calls
"~39%" and the headline bullet calls "~37–40%" — three descriptions of one quantity, which is the
shape freeze rule 3 exists to stop. Changed to **"about 39%"**. The probe's `round_exempt` is
gone and its tolerance is back to 0.5, so the figure is checked like any other rather than
tolerated.

### `bold_is_result`, and why the first version of it was wrong

`^\d{1,2}$` — "small integer, ordinals and cohort edges" — is the most useful exemption in the
harness and the most dangerous. `strict_units` closed the case where it swallowed an integer
PERCENTAGE, but it reaches `%` and `×` and nothing else. On 2026-08-11 the bare-integer case
turned out to be hiding something load-bearing **four times in one paper in one day**:
registration tenure, the precinct cut's 50-vote floor, the low endpoint of five odd-year ranges,
and Appendix B's July-1 sentinel. Every one had been **bolded by the author**.

So: a token inside a `**...**` run is ineligible for PATTERN exemption. It can still be closed by
a LITERAL with a reason — that distinction is the design, since a pattern waives a class
sight-unseen and a literal names one token and says why.

**The first implementation matched any bold run, and it was too blunt: 25 tokens on the pilot
paper, three of them real.** The rest were figures sitting inside a bolded *phrase* — `**April
2026 roll**`, `**positive in all 39 counties**`, `**42.8% 65+ and 6.1% under 30**`, `**1. Maybe
the off-year electorate…**`. Emphasis on a phrase is emphasis on the sentence; emphasis on one or
two words is emphasis on the number. Limiting the run to **two words**, and the token to **one or
two digits** (so a bolded year keeps its exemption automatically, rather than needing a second
special case), took the pilot to **6 — all six genuine**, and the series-wide cost from ~84
tokens to **24**.

**What it found on the pilot, all previously unchecked:** the senior-to-youth ratio restated as
`**2:1**` and `**5:1**` (the decimal form beside it *was* asserted, the ratio notation was not),
the median off-year ballot-returner `**59**` against the median registrant `**48**`, and the age
`**80**` at which Appendix H's tail decline begins. WA 820 → **827 figures**.

### Rolled out the way `strict_units` was, for the reason that precedent records

Four callers `ENABLED`: the pilot, plus `verify_safe_seat.py`, `verify_money_votes.py` and
`verify_cross_state_money.py`, which **measured at zero** newly-unmapped tokens — enabling them
cost nothing and leaving them out would have been a rollout that stopped for no reason. Four in
`BACKLOG` with measured counts: Idaho 11, New York 6, the whitepaper 4, who-returns-ballot 3.

Thirteen tests in `tests/test_infrastructure/test_bold_is_result_rollout.py`, including the four
real sentences and the five real phrases that must NOT fire. `tests/test_infrastructure/` **492
passed, 1 skipped**. Sweep re-measured across all nine gates: **2,697 caught / 0 UNCAUGHT / 913
no-probe / 3,619 rows** — WA 660 → 662, every other verifier row-identical, so enabling the flag
on three further callers changed no derivation anywhere. Cross-doc **0 findings**.
