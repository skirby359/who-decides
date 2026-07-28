# Publication checklist — electoral-health lead paper

*Assembled 2026-06-29. Turns the human-owned items in
`electoral-health-TODO.md` (private repo) (#3 verify numbers, #4 hand-rate
matches, #5 re-check cites, #6 publish) into a tick-through list. The work is
AI-assisted; **you must independently re-derive the headline numbers before posting
under your name** — this file makes that fast, it does not substitute for it.*

Lead paper for submission: [`who-decides-washington.md`](who-decides-washington.md)
("Who Decides Washington State? The gray off-year electorate"). Companion, post second:
[`safe-seat-washington.md`](safe-seat-washington.md).

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
python scripts/verify_donor_class.py        # donor-class-and-the-electorate.md F1-F4, both panels x 3 states
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
| 11b | WA seats offering no D-v-R (Dimension 2) | 48.5 / 27.1 / 27.6 / 35.3 / **35.3%** — a *separate* question from 11, not a restatement |
| 12 | Four-state lower-chamber not close | WA **87.8** / NY 88.6 / TX 94.0 / ID 92.9% |
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

---

## 2. Statute cites — DONE (re-verified 2026-06-29)

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
- ⚠ **N.Y. Elec. Law § 14-114** (New York's caps) — cited qualitatively ("high") and **not
  independently verified this session**. Confirm the section number before posting, or drop
  to a bare "New York's caps are comparatively high" with no cite.
- **N.Y. Pub. Off. Law art. 6** (FOIL) as the access basis for NYSVOTER in Appendix B —
  the specific NY Election Law provision governing voter-list release was **not** verified;
  Appendix B deliberately cites only FOIL plus the Board's elections-purpose certification.

---

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
| 42 | NY state matched layer | 424,020 donors / $379.5M / top-1% 48.5% / Gini 0.846 |
| 43 | NY state age bands | 4.9 / 17.8 / 38.9 / 38.4 (65+ 38.4% vs 47.9% federal) |
| 44 | NY state own-party skew | DEM +8.9 / REP +3.2 / NOPARTY -12.0 (vs federal +15.0 / -0.9 / -13.0) — **all-records baseline; superseded by #60's active-only figures** |
| 45 | NY state geography | Manhattan 20.6% (vs 50.3% federal), Nassau 15.1%, Suffolk 11.1%; top-3 ZIP3 38.1% |
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
| 58 | D2 no-D-v-R share by year | 48.5 / 27.1 / 27.6 / 35.3 / 35.3% |
| 59 | WA 2024 detail | 133 seats; 111 not close; 47 without D-v-R = 23 single + 15 same-party + 9 major-v-minor |
| 60 | Safe-seat party split, by WINNER not vote totals | 68 D / 43 R (was 69/44 under the old rule) |
| 61 | The one close same-party general | WA CD-4 2024, R-v-R, 6.0-point margin (Newhouse) |
| 62 | Four-state lower chamber, not close | WA 87.8 (98/98) / NY 88.6 (149/150) / TX 94.0 (96/150 + 54 backfill) / ID 92.9 (70/70) |
| 63 | Party-string sensitivity on no-D-v-R | strict vs loose differs 3.0pp in 2016, <=2.2pp elsewhere |

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
> | 68 | Primary/general median ratio | 42.1 / 55.9 / 61.6 / 61.2 / 51.2% (2016-2024) |
> | 69 | TX backfill verification tiers | 14 press-confirmed / 40 inferred from absence |
> | 70 | TX imputed party ERROR RATE | wrong in **4 of 14** checkable (HD 35/36/40/42) |
>
> **Claim 70 is the consequential one.** Presidential lean imputes the holding party for
> the 54 backfilled Texas seats, and where the press-confirmed subset lets that be checked
> it fails 29% of the time — Rio Grande Valley districts held unopposed by Democrats that
> Trump carried in 2024. The Texas **51 D / 90 R split must not be quoted**. The
> non-competitive count (94.0%) is unaffected: it needs only that the seats were
> uncontested, not who held them.
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
