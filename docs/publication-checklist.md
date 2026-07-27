# Publication checklist — independent-verification gate

*This is the verification gate the papers cite: the exact scripts and expected
values needed to independently re-derive every headline number. The analysis is
AI-assisted; **the headline numbers must be independently re-derived before
posting under an author's name** — this file makes that fast, it does not
substitute for it.*

Lead paper: [`who-decides-washington.md`](who-decides-washington.md)
("Who Decides Washington State? The gray off-year electorate"). Companion:
[`safe-seat-washington.md`](safe-seat-washington.md).

---

## 1. Verification ledger — re-derive each headline number

**Independent verifiers (the preferred §1 vehicle).** These hit the DBs with
from-scratch SQL — NOT by importing the diag/match code — and print
derived-vs-paper side by side, so a match confirms each finding independently of
the analysis code. Read-only, aggregate-only. Run and eyeball the two columns:

```bash
python scripts/verify_who_decides_wa.py     # who-decides-washington.md  #1-#10   (all match)
python scripts/verify_who_decides_id.py     # who-decides-idaho.md §I-§V          (all match)
python scripts/verify_who_decides_ny.py     # who-decides-new-york.md §I-§VI       (§I/II/V/VI + §III comp match;
                                            #   §III turnout & §IV primary RATES ~1-2pp under = current-roll denom)
python scripts/verify_donor_class.py        # donor-class-and-the-electorate.md F1-F4 (WA/NY/ID)
python scripts/verify_safe_seat.py          # safe-seat-washington.md (WA by-year + 4-state)  (all match)
python scripts/verify_cross_state_money.py  # cross-state-fec-money.md (inflow + outflow)  (all match)
```

**Status — all six re-run, exit 0, reproduce.** WA outflow reconciles exactly (see
below). One known, self-reported divergence remains (flagged inline by the script,
not a paper error):
- **NY §III turnout / §IV primary participation** run ~1-2pp under the paper — current-roll
  denominator sensitivity (the paper's own soft cut); composition/structural cuts match exactly.
- **‡‡ WA outflow concentration.** The verifier was recomputing on the
  raw WA `individual_contributions` (state PDC + non-WA donors + odd cycles → 1.12M / 47.5%);
  applying the paper's own filter (`fec_candidate_id ~ '^[CPHS][0-9]'` AND `contributor_state='WA'`,
  matching `cross_state_fec_money.py`) reproduces the paper **exactly: 361,818 donors / top-1%
  39.3% / top-10% 72.3% / Gini 0.800** (cycles resolve to clean 2018–2026 even years; total $646M).
  NY tightened to 671,488 (was 699K raw), TX unchanged — all three reproduce.

The diag scripts (what the papers were built from) for any remaining ledger cells.
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
| 11 | WA leg+cong seats non-competitive 2016–2024 | ~85% |
| 12 | Four-state lower-chamber non-competitive | WA 88.8 / NY 88.6 / TX 94.0 / ID 92.9% |
| 13 | Donor concentration (cross-state §F) | top-1% 47.7%, Gini 0.862 [.856–.868] |

**"Who Decides Idaho?" — re-derive (needs `data/id_vrdb.duckdb` from `load_id_voters.py`):**

```bash
python scripts/load_id_voters.py                        # -> id_vrdb.duckdb (voters 1,029,938)
python scripts/diag_id_turnout_party.py                 # turnout by age x party + closed primary
STATE=ID python scripts/backfill_id_recipient_party.py  # recipient party (crossover)
STATE=ID python scripts/match_id_voters_to_donors.py    # donor class x party
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
| 21 | Donor class by party | DEM +9.1 skew; UNAFF −11.8; donors 51% 65+ | match_id_voters_to_donors |
| 22 | Donor concentration / geography | top-1% 39.2%; Ada/Boise 49.2% of $ | match_id_voters_to_donors |
| 23 | Crossover (resolved ~52%) | DEM 93.5%→D; UNAFF 72.8%→D; REP 79.3%→R (REP→D upper bound) | match_id_voters_to_donors |

**"The Donor Class Is Not the Electorate" Appendix G — confirm against
`diag_contribution_limits.py`** (read-only over `id_statewide.duckdb` +
`wa_statewide.duckdb`; no voter file needed):

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
> reinstate it. Two data-hygiene points the script enforces and any re-derivation must
> match: PDC's `SMALL CONTRIBUTIONS` unitemized pseudo-contributor is **excluded** from all
> WA state cuts (left in, it keys as one enormous donor), and the person/organization split
> is a per-layer name heuristic (comma test for Sunshine/FEC `LAST, FIRST`; org-marker test
> only for PDC's `LAST FIRST`, which is why no persons-only WA state figure is published).

> **‡ Claim 17 — Idaho turnout RATES dropped (turnout sanity pass).** Idaho rates
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
> diag scripts' rate outputs carry a survivorship caveat. ID donor figures are Idaho Sunshine
> **state** money (not FEC).

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
> **The old Idaho figures were right all along** — they were the Sunshine panel.
> `--source state` reproduces 27,250 voters / top-1% 39.3% / Ada 49.2% / DEM +9.1 /
> UNAFF -11.8 exactly. NY is likewise unchanged (its `_fec` panel reads 51.2% / 81.4% /
> +15.0 / -0.9 / -13.0); only its matched count moves, 308,032 -> 307,841, from dropping
> 45,494 un-prefixed legacy rows.
>
> Ledger claims **21/22** describe the **ID state panel** and still hold as written.
> Appendix G is unaffected: `diag_contribution_limits.py` selects layers by
> `contribution_id` prefix and never reads `voter_donor_affiliation`.

**Donor paper — panel expected values (`verify_donor_class.py`, both panels):**

| # | Claim | Expected | Panel |
|---|---|---|---|
| 30 | WA federal matched layer | 172,998 donors / $420.3M / top-1% 42.4% / top-10% 74.8% / Gini 0.820 | federal |
| 31 | WA state matched layer | 269,204 donors / $153.9M / top-1% 43.8% / top-10% 76.0% / Gini 0.827 | state |
| 32 | NY federal matched layer | 307,841 donors / $1,196.1M / top-1% 51.2% / top-10% 81.4% / Gini 0.867 | federal |
| 33 | ID federal matched layer | 27,196 donors / $49.6M / top-1% 35.8% / top-10% 70.4% / Gini 0.786 | federal |
| 34 | ID state matched layer | 27,250 donors / $15.9M / top-1% 39.3% / top-10% 70.8% / Gini 0.798 | state |
| 35 | WA generation multipliers | federal Silent 2.56x .. Gen Z 0.10x; state Silent 1.64x .. Gen Z 0.20x | both |
| 36 | ID 65+ donor share | federal 64.7%, state 51.1% (roll 31.0%) | both |
| 37 | ID own-party skew replicates | federal DEM +8.0 / UNAFF -11.2; state DEM +9.1 / UNAFF -11.8 | both |
| 38 | ID recipient-party resolution | federal **86.7%** vs state ~52% (only the state REP->D rate is an upper bound) | both |
| 39 | WA give<->vote | federal 85.4% vs 51.4% super; state 84.9% vs 50.8% | both |
| 40 | WA bootstrap CIs (B=1,000) | federal top-1% [40.2-44.9], Gini [0.812-0.828]; state top-1% [39.6-48.9] | both |
| 32b | NY state matched layer | 424,020 donors / $379.5M / top-1% 48.5% / top-10% 78.3% / Gini 0.846 | state |

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
| 44 | NY state own-party skew | DEM +8.9 / REP +3.2 / NOPARTY -12.0 (vs federal +15.0 / -0.9 / -13.0) |
| 45 | NY state geography | Manhattan 20.6% (vs 50.3% federal), Nassau 15.1%, Suffolk 11.1%; top-3 ZIP3 38.1% |
| 46 | NY state give<->vote | 3.02 generals / 73.1% super vs 1.77 / 36.8% |
| 47 | NY state crossover (after backfill) | resolution 25.9% -> **37.7%**; DEM 88.3->D, REP 84.7->R, NOPARTY 54.8->D |

> NY state crossover is the thinnest cut in the paper at **37.7%** resolution
> (`backfill_ny_recipient_party.py`). Stability check: lifting coverage from 25.9% to
> 37.7% moved the rates by 1.0 / 4.5 / -2.1 points — directions hold, magnitudes are
> approximate. A bare-surname tier was built and REJECTED (it read "FRIENDS OF DAVID
> KNAPP" as Republican via *David*); do not reinstate it. Corporate/labor PACs stay
> unresolved by design.

---

## 2. Statute cites

- **WA RCW 29A.08.720** (political use allowed; advertising/solicitation barred) + **29A.08.740**
  (penalties) — verified against current code at app.leg.wa.gov. The appendix cites these
  subsections rather than the bare chapter.
- **Idaho Code §74-120** ("Prohibition on distribution or sale of mailing or telephone number
  lists"; releases registrant age, withholds DOB/DL#/address) — verified at legislature.idaho.gov.
- Remaining human step: one final glance at publication time (statutes can amend).

**Campaign-finance statutes added 2026-07-26** for the donor paper's Appendix D / Appendix G.
Two flagged items need a human glance before posting:

- **Idaho Code § 67-6610A** — individual contributions capped at **$1,000/election**
  (legislative, judicial, local) and **$5,000/election** (statewide); primary and general are
  separate elections; candidate self-funding exempt. Verified at legislature.idaho.gov.
- ⚠ **Idaho S.B. 1422 (2026)** would have raised those to $1,500 / $6,000. Bill history ends
  **"04/01 Retained on calendar"** with no passage recorded; cited in the paper as *proposed
  only*. **HUMAN: confirm it died before publication.**
- **52 U.S.C. § 30116** — federal individual-to-candidate limit **$3,500/election** for the
  2025–26 cycle (was $3,300 in 2023–24), indexed. Also **§ 30118** (corporate contribution
  prohibition, which Idaho and Texas state law do not share).
- ***McCutcheon v. FEC*, 572 U.S. 185 (2014)** — struck the biennial **aggregate** limit, so
  there is no federal ceiling on a donor's total giving; load-bearing for Appendix G's
  mechanism. ***Buckley v. Valeo*, 424 U.S. 1 (1976)** for the contribution/expenditure
  asymmetry.
- **Tex. Elec. Code § 253.094** — bars corporate/labor contributions; **no dollar limit** on
  individual gifts to non-judicial state candidates (Judicial Campaign Fairness Act,
  §§ 253.151–253.176, is the capped exception). Replaces the previously uncited "no
  contribution limits" assertion in `cross-state-fec-money.md` K1.
- ⚠ **WA RCW 42.17A.405**, recodified **RCW 29B.40.020** eff. **Jan. 1, 2026**. Cited without a
  dollar figure; the amounts are PDC-indexed, not statutory. **HUMAN: confirm against the
  current PDC schedule if any amount is ever quoted.**
- ⚠ **N.Y. Elec. Law § 14-114** — cited qualitatively and **not independently verified**;
  confirm the section number before posting, or drop to an uncited phrasing.
- **N.Y. Pub. Off. Law art. 6** (FOIL) is the access basis cited for NYSVOTER in Appendix B;
  the specific NY Election Law provision governing voter-list release was not verified, so
  Appendix B cites only FOIL plus the Board's elections-purpose certification.

