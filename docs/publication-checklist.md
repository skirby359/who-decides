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

---

## 2. Statute cites

- **WA RCW 29A.08.720** (political use allowed; advertising/solicitation barred) + **29A.08.740**
  (penalties) — verified against current code at app.leg.wa.gov. The appendix cites these
  subsections rather than the bare chapter.
- **Idaho Code §74-120** ("Prohibition on distribution or sale of mailing or telephone number
  lists"; releases registrant age, withholds DOB/DL#/address) — verified at legislature.idaho.gov.
- Remaining human step: one final glance at publication time (statutes can amend).
