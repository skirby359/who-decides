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
