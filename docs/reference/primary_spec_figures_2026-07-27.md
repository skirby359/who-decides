# Donor-class figures under the primary specification (2026-07-27)

Every number below was re-derived after the six paper panels, the two Idaho period-aligned
panels and the three pooled tables were rebuilt on the **full-first-name key alone**
(`tiers=PRIMARY_TIERS`). This file exists so the documentation sweep is resumable and so a
reviewer can see old and new side by side.

Sources: `scripts/verify_donor_class.py`, `scripts/diag_donor_class_revisions.py`,
`scripts/diag_donor_concentration_bootstrap.py`, `scripts/diag_donor_primary_spec_checks.py`.
Transcripts in `reports/` (gitignored): `verify_after.txt`, `revisions_after.txt`,
`bootstrap_after.txt`, `primary_spec_checks.txt`, and the pre-switch baseline in
`reports/before_tier_switch/`.

**All six panels reconcile to the cent** against an independent reconstruction of the
rank-0 key, and every donor count equals the corresponding `_alltier`
`match_quality='STRICT_ZIP5_FULL'` count exactly.

## Panel sizes and concentration

| panel | donors (was) | $M (was) | top 1% (was) | top 10% (was) | Gini (was) |
|---|--:|--:|--:|--:|--:|
| WA federal | **147,745** (172,998) | **346.32** (420.32) | **41.2%** (42.4) | **74.2%** (74.8) | **0.815** (0.820) |
| WA state | **217,114** (269,204) | **122.50** (153.87) | **43.5%** (43.8) | **75.3%** (76.0) | **0.821** (0.827) |
| NY federal | **269,218** (307,841) | **1,015.71** (1,196.10) | **50.7%** (51.2) | **81.2%** (81.4) | **0.865** (0.867) |
| NY state | **378,383** (424,020) | **339.77** (379.46) | **48.6%** (48.5) | **78.2%** (78.3) | **0.845** (0.846) |
| ID federal | **23,303** (27,196) | **42.11** (49.56) | **37.2%** (35.8) | **70.8%** (70.4) | **0.789** (0.786) |
| ID state | **23,613** (27,250) | **13.64** (15.90) | **40.0%** (39.3) | **71.0%** (70.8) | **0.799** (0.798) |

The ordering **NY > WA > ID** survives in both panels. Concentration moved in *both*
directions — down in WA and NY federal, up in Idaho — which is why these had to be
recomputed rather than copied from the old sensitivity table.

**Do not copy from the old Appendix F sensitivity table.** It filtered a built panel on
`match_quality`, which keeps a rank-0 voter's weak-key gifts; the rebuild restricts the
match, which drops them. WA federal reads 42.2% under the filter and **41.2%** as rebuilt.

## The two-definitions dollar delta (must be published)

Donor counts are identical under both definitions in all six panels; dollars are not.

| panel | filter-a-panel $M | restrict-the-match $M | delta | % |
|---|--:|--:|--:|--:|
| WA federal | 375.26 | 346.32 | 28.93 | **7.71%** |
| WA state | 135.26 | 122.50 | 12.76 | **9.44%** |
| NY federal | 1,073.14 | 1,015.71 | 57.43 | **5.35%** |
| NY state | 353.10 | 339.77 | 13.33 | **3.77%** |
| ID federal | 44.75 | 42.11 | 2.64 | **5.89%** |
| ID state | 14.48 | 13.64 | 0.83 | **5.76%** |

## Finding 1 — age

WA generation multipliers (donor share ÷ roll share):

| generation | federal (was) | state (was) |
|---|--:|--:|
| Silent | **2.67×** (2.56) | **1.72×** (1.64) |
| Boomer | **2.04×** (1.97) | **1.59×** (1.51) |
| Gen X | **0.98×** (0.98) | **1.31×** (1.26) |
| Millennial | **0.35×** (0.39) | **0.61×** (0.68) |
| Gen Z | **0.04×** (0.10) | **0.11×** (0.20) |

NY age bands (vs 2024 GE reference): federal 18–29 **1.6%** / 30–44 **13.0%** /
45–64 **35.5%** / 65+ **49.9%** (was 3.0 / 14.1 / 34.9 / 47.9). State: **3.9 / 17.2 / 39.6 /
39.3** (was 4.9 / 17.8 / 38.9 / 38.4).

ID age bands (current-roll): federal 18–29 **0.5%** / 30–44 **6.2%** / 45–64 **26.5%** /
65+ **66.8%** (was 1.4 / 7.1 / 26.8 / 64.7). State: **2.1 / 12.9 / 33.7 / 51.3**
(was 2.6 / 13.1 / 33.2 / 51.1).

WA federal geography: 981xx **37.9%** + 980xx **25.6%** = **63.5%** of matched dollars
(was 37.3 + 26.1 = 63.4).

## Finding 3 — party (ACTIVE registrant baseline)

| state / panel | party | reg% | donor% | skew (was) | $ share |
|---|---|--:|--:|--:|--:|
| NY federal | DEM | 47.6 | **63.6** | **+16.1** (+15.2) | **72.5** |
| | REP | 22.6 | **21.5** | **−1.1** (−1.2) | **16.0** |
| | NOPARTY | 25.3 | **11.6** | **−13.7** (−12.8) | **9.8** |
| | OTHER | 4.5 | **3.2** | −1.2 | 1.8 |
| NY state | DEM | 47.6 | **57.1** | **+9.6** (+9.1) | **54.9** |
| | REP | 22.6 | **25.8** | **+3.2** (+2.8) | **27.7** |
| | NOPARTY | 25.3 | **12.7** | **−12.6** (−11.8) | **13.9** |
| ID federal | REP | 62.9 | **67.0** | **+4.2** (+3.8) | **68.5** |
| | DEM | 11.8 | **20.4** | **+8.6** (+8.0) | **21.8** |
| | UNAFF | 23.9 | **11.8** | **−12.1** (−11.2) | **9.3** |
| ID state | REP | 62.9 | **66.3** | **+3.4** (+3.6) | **72.2** |
| | DEM | 11.8 | **21.6** | **+9.8** (+9.1) | **20.0** |
| | UNAFF | 23.9 | **11.6** | **−12.3** (−11.8) | **7.6** |

### Crossover (still exploratory; resolution rates differ by group)

NY federal — DEM 171,349 matched / 156,142 resolved (**91.1%**), D-only **95.3%**,
R-only 3.2%, Mixed 1.5%, $-to-D **95.5%**. REP 57,856 / 50,800 (**87.8%**), D-only
**12.2%**, R-only 84.8%, Mixed 3.0%, $-to-D **18.3%**. NOPARTY 31,319 / 25,074 (**80.1%**),
D-only **65.1%**, R-only 31.4%, Mixed 3.5%, $-to-D **75.7%**. OTHER 8,694 / 7,122 (81.9%),
39.1 / 58.9 / 2.1, $-to-D 48.1%.

ID federal — REP 15,621 / 13,545 (**86.7%**), D-only **17.1%**, R-only 82.1%, Mixed 0.8%,
$-to-D **18.1%**. DEM 4,764 / 4,473 (**93.9%**), D-only **98.5%**, $-to-D **99.1%**.
UNAFF 2,754 / 2,286 (**83.0%**), D-only **78.3%**, R-only 20.6%, $-to-D **77.7%**.
OTHER 164 / 102 (62.2%), 16.7 / 81.4 / 2.0, $-to-D 7.5%.

## Finding 4 — giving and turnout

| measure | donors (was) | non-donors (was) |
|---|--:|--:|
| WA super-voter, federal | **88.0%** (85.5) | **52.0%** (51.4) |
| WA mean propensity, federal | **0.977** (0.966) | **0.755** (0.754) |
| WA super-voter, state | **88.9%** (84.9) | **51.5%** (50.8) |
| WA mean propensity, state | **0.966** (0.950) | **0.753** (0.751) |
| NY generals of 4, federal | **3.10** (3.00) | **1.85** (1.85) |
| NY super-voter, federal | **75.7%** (72.9) | **39.3%** (39.3) |
| NY generals of 4, state | **3.07** (2.99) | **1.84** (1.84) |
| NY super-voter, state | **75.3%** (73.0) | **39.0%** (38.9) |

Idaho composition is **unchanged** (roll-only, no donor join): unaffiliated 23.9% of the
roll / 22.6% of the 2024 general / **5.9%** of the 2024 primary electorate.

## Period-aligned Idaho panels (2023–2025)

| panel | donors | $M | top 1% | top 10% | Gini | 65+ |
|---|--:|--:|--:|--:|--:|--:|
| federal aligned | **14,848** (16,963) | **18.42** (21.09) | **34.7%** (33.1) | **66.5%** (65.9) | **0.752** (0.748) | **68.5%** (67.1) |
| state aligned | **23,613** (27,250) | **13.64** (15.90) | **40.0%** (39.3) | **71.0%** (70.8) | **0.799** (0.798) | **51.3%** (51.1) |

Period-aligned age gap widens to **17.2 points** (68.5 vs 51.3; was 16.0). State money still
reaches **59% more donors** than federal on the shared window, so the apparent Idaho
inversion remains a window artifact.

## Appendix E bootstrap intervals (WA, B=1,000)

| | federal | 95% CI | state | 95% CI |
|---|--:|---|--:|---|
| top 1% | **41.2%** | [38.6–43.4] | **43.5%** | [38.7–48.9] |
| top 10% | **74.2%** | [73.0–75.2] | **75.3%** | [73.2–77.7] |
| Gini | **0.815** | [0.806–0.822] | **0.821** | [0.806–0.838] |

The two panels' intervals still overlap, so the paper's "not separable at this precision"
claim stands.

## Panel overlap (Jaccard barely moves; the finding holds)

| state | federal | state | both | Jaccard (was) | 65+ state-only / fed-only / both |
|---|--:|--:|--:|--:|---|
| WA | 147,745 | 217,114 | 49,943 | **0.159** (0.157) | 32.9% / 53.6% / **59.6%** |
| NY | 269,218 | 378,383 | 89,704 | **0.161** (0.160) | 34.4% / 47.3% / **55.0%** |
| ID | 23,303 | 23,613 | 5,780 | **0.141** (0.140) | 46.0% / 66.5% / **67.6%** |

The both-systems group remains **older than either single-system group** in all three
states, so "federal money is older money" is still not a clean property of the layer.

## Pooled tables — two different causes, do not conflate

| pooled table | before | after | cause |
|---|--:|--:|---|
| WA | 382,408 / $574.21M | **314,974 / $468.85M** | tier switch only |
| ID | 47,762 / $65.46M | **41,136** | tier switch only |
| NY | 308,032 / $1,196.16M | **558,017** | tier switch (down) **plus** correction of a stale FEC-only build predating `load_ny_contributions` (up, dominant) |

## Residual-risk checks

- **Namesake collision on the full-name key.** The paper's published 7–9% was computed on
  a *first-initial* join and does not describe this key. On the correct key the
  middle-initial signal is 0.03–2.14% of donors, but the gift-count control is decisive:
  **0.00% at one gift in every panel**, rising monotonically to 0.36–8.33% at 20+ gifts —
  the signature of inconsistent within-person recording, not of two people. The employer
  discriminator is unusable (NY federal flags 31.9% of donors) and NY state / ID state do
  not populate it at all. City sits between at 1.28–4.97%.
- **Roll-side inactive namesakes** 0.21–0.40% (WA fed 0.24%, NY fed 0.40%). Small, and it
  strengthens the claim. Not measurable for Idaho — its export carries no active flag.
- **Recall cost / selection bias.** The restriction discards 10.8–19.3% of donors, and the
  discarded set is **younger in all six panels** (WA fed 40.5% vs 55.7% over-65; NY fed
  34.2% vs 49.9%; ID fed 52.2% vs 66.8%) and **less Democratic in all four party panels**
  (NY fed 56.6% vs 63.6%; ID fed 16.3% vs 20.4%). So part of the primary spec's stronger
  skews is selection, not precision. The counter-argument is equally real — roughly half
  the discarded records were false matches — so neither specification is unbiased and both
  belong in the paper.
- **Joint filings** 0.06–0.25% of dollars everywhere except **Idaho Sunshine at 1.87% of
  rows / 3.27% of dollars**, a ~20× outlier that explains why 6 of 8 partial merges are ID
  state.
- **WA PDC name-order parse failure** 1.85% of comma-less rows / 2.08% of dollars. The
  paper currently cites the 0.1% / 0.8% organisation figure as this mode's analogue, which
  measures something else.
- **Multi-token first names** (unreachable by the rank-0 key) 0.50% WA / 1.50% NY / 0.26%
  ID — recall loss only, no precision effect.
- **NY duplicate voter ids**: of the 53 on the roll, 0 reach the federal panel and 5 reach
  the state panel, all on the rank-0 key. So the fan-out survives: NY state reads 378,383
  standalone and 378,388 after a roll join.

## Pooled-table figures (recomputed 2026-07-27, second pass)

The seven diagnostics that read the POOLED table were re-run after the rebuild. These are
the figures the companion papers quote.

| measure | WA (was) | NY (was) | ID (was) |
|---|--:|--:|--:|
| matched voters | **314,974** (382,408) | **558,017** (308,032) | **41,136** (47,762) |
| top 1% of matched $ | **46.6%** (47.7) | **54.5%** (n/a) | **40.6%** (n/a) |
| top 10% | **79.3%** (80.0) | **83.8%** | **74.4%** |
| Gini | **0.857** (0.862) | **0.884** (0.867) | **0.822** (0.819) |
| super-voter, donor vs non | **87.6% / 50.9%** (84.0 / 50.1) | **83.1% / 45.0%** | **50.0% / 30.1%** |
| ratio | **1.72x** (1.68) | **1.85x** | **1.66x** |
| mean propensity | **0.967 / 0.749** (0.953 / 0.748) | **0.892 / 0.653** | **0.892 / 0.851** |

WA pooled generation multipliers, raw then inverse-propensity re-weighted: Silent
**1.96x -> 1.91x** (was 1.87 -> 1.83), Boomer 1.71 -> 1.70, Gen X 1.22 -> 1.24,
Millennial 0.54 -> 0.54, Gen Z **0.09x -> 0.09x** (was 0.17 -> 0.17). Two-ZIP3 share of
matched dollars **61.4%** (981xx 36.2% + 980xx 25.1%). NY IPW: 65+ share raw 41.9% ->
corrected 41.9%, P(matchable) spread 0.9 pts.

Pooled party mix: ID roll D 11.8 / R 62.9 / other 25.3 against donors D **19.7** / R
**67.4** / other **13.0**; NY roll D 47.8 / R 22.3 / other 30.0 against donors D **58.6** /
R **24.5** / other **16.9**.

## Downstream refresh done (2026-07-27, second pass)

Rebuilding the pooled table made its copies stale. Refreshed:

- `compute_political_preference` re-run for **cd03** (588,825 scored) and **cd10** (212,411)
  — the only WA districts carrying a preference. ~7,690 voters across the two had a
  preference built on a donor signal the switch removed (67,434 donor rows dropped
  statewide), so those values were stale.
- `donor-prospects` regenerated for all 14 district scopes it covers; the table now holds
  **16,900** rows across 16 scopes.
- `voter_segments` (cd05, 564,283 rows) checked and **not** refreshed: cd05 carries no
  `political_preference` and segments key off `turnout_propensity`, so the donor rebuild
  does not reach them. `narrative_ai_cache` messaging entries therefore need no
  invalidation either.

## Idaho Sunshine reload (done 2026-07-27, third pass)

The deferred reload — the one irreversible step in this change — has been run, and it
confirmed the prediction: **no primary-spec figure moved.**

Safety: file-level backup plus in-DB snapshots of all three tables `_replace_scoped`
touches (`individual_contributions`, `candidate_finance`, `independent_expenditures`),
with row counts and dollar sums compared before the snapshots were dropped. Ran with
`force=False`, so the cached 2023-2025 CSVs were used and no data was re-fetched; 2018/2019
404 gracefully as designed.

Reload returned exactly the baseline counts: **216,700** contributions, **2,067**
candidate_finance rows, **1,139** independent expenditures. Appendix G's figures are
byte-identical — $53,256,865.38 layer total, max gift **$1,245,000**, **668** gifts above
$5,000 totalling $22,309,558.29 = **41.9%** of the layer's dollars.

`contributor_type` is now populated for the Sunshine layer from the real source field:

| type | rows | share of rows | $M | 
|---|--:|--:|--:|
| PERSON | 181,749 | 83.87% | 23.95 |
| UNKNOWN (source blank) | 17,374 | 8.02% | 0.61 |
| ORGANIZATION | 14,273 | 6.59% | 23.76 |
| COMMITTEE | 3,304 | 1.52% | 4.93 |

**Organisations and committees are 8.1% of Sunshine rows but 53.9% of its dollars**
($28.70M of $53.26M) — far more than the 32.6% the name heuristic estimated, which is the
case for having used the real field.

**Effect on the panels: none.** ID state stays 23,613 / $13.64M, pooled 41,136 / $55.75M,
aligned state 23,613 / $13.64M. Tested directly: **zero** organisation rows would ever have
matched on the full-name key, so the tier switch had already eliminated the contamination by
construction — consistent with all 14 organisation false matches in the 480-record
validation landing on initial-based keys. The filter is genuine defence-in-depth: it protects
the retained `_alltier` panels' interpretation and any future all-tier work, and it means a
new source with organisation rows cannot silently contaminate a panel.

## Unchanged — do not edit these

Verified by reading the producing script, not inferred:

- **Appendix G in full** (`diag_contribution_limits.py` selects layers by
  `contribution_id` prefix and never reads a panel) — except its two cross-references to
  matched-panel figures.
- **Appendix E's statewide all-donor table** (WA 39.3% / NY 47.5% / TX 41.7% / ID 36.0%)
  from `cross_state_fec_money.py`. This sits adjacent to the panel figures and looks
  identical in kind; editing it would introduce an error.
- **Appendix F ceiling table** (`diag_donor_match_ceiling.py`, computed on the donor files).
- **Idaho composition shares** and the NY active-roll counts (roll-only).
- **The 480-record verdict ledger** and everything derived only from it: per-tier precision
  100.0 / 71.7 / 47.9 / 50.4, the Wilson intervals, the 152-confirmed-false error-mode
  split, the 8 partial merges, the 4.7% / 32.6% Sunshine organisation figures, the raw
  sample mean 67.6%, the dollar-band 63.0% / 72.1%.
- **The frozen 93.0%** weighted precision, which describes the superseded all-tier
  specification and is pinned in `score_match_validation.py`.
- Itemization thresholds, all statute citations, safe-seat counts, every forecast figure.
