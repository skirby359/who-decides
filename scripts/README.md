# scripts/

Two tiers.

## Verification (reproduces the papers — standalone, `duckdb` + stdlib only)

- `verify_*.py` — the six one-per-paper re-derivations; each prints `derived (paper: …)`.
- `diag_*.py` — the underlying analyses cited in the papers (turnout decomposition,
  roll-off, safe-seat counts, cross-state concentration, donor age skew, etc.). Most run
  standalone; a few need build inputs beyond the public extract (see the provenance caveat
  below): `diag_ie_vs_margin.py` (Finding-6 IE-vs-margin, needs the private forecast model);
  `diag_wa_rolloff_precinct.py` (Appendix F precinct roll-off) and
  `diag_wa_offcycle_dropoff_demographics.py` (Appendix G race/income drop-off), both needing
  the ETL-built `precinct_demographics` + `vrdb_precinct_crosswalk`; and
  `diag_loser_side_money.py` (cross-state Section J longshot money), needing the stored
  `forecast_predictions` + the committee→party backfill; and `diag_efficiency_gap.py`
  (safe-seat partisan-asymmetry check), needing the ETL-built `precinct_district_map`.
  Standalone additions:
  `diag_safe_seat_party_ratio.py` (safe-seat split vs presidential party ratio; imports the
  safe-seat classifier + public precinct results) and `diag_sector_coverage.py` (Section H
  classifier-coverage audit; reads public FEC inflow). Coarser siblings that reproduce from
  public data alone: `diag_wa_rolloff_2024.py` (county roll-off) + the `diag_safe_seat_*`
  observed-competitiveness scripts.
- `cross_state_common.py` — shared helper the cross-state scripts import: enumerates the
  analysis region by globbing `data/*_statewide.duckdb` (override `CROSS_STATE_REGION`),
  plus the competitiveness-band read and `reports/` JSON writer. Adding a state needs no
  script edits.
- `cross_state_state_money.py` — cross-state Section K: the state-disclosure money layer
  (WA PDC / NY BOE / TX TEC / ID Sunshine in `candidate_finance`).
- `diag_cross_state_donor_representativeness.py` (Section F5) and
  `diag_cross_state_giving_turnout.py` (Section F6) — the cross-state individual layer;
  F6 reads the `voter_scores` built by `populate_ny_id_voter_scores.py` (build tier).
- `acs_wa_adult_age.py` — pulls the ACS/CVAP rows (needs a Census API key).
- `md_to_pdf.py` — renders a paper `.md` to PDF (needs `markdown` + `wkhtmltopdf`).

Run from the repo root with `data/` populated. Side artifacts (JSON) go to `reports/`
(git-ignored).

## Build / provenance (how the DuckDB tables were assembled — NOT on the verification path)

- `download_*.py` — fetch the public certified-results files (Idaho SoS, Texas
  Legislative Council) into `data/raw/` before `load_*` builds the tables.
- `load_*.py` — build the state DuckDB files from raw voter/FEC bulk downloads.
- `match_*.py`, `backfill_*.py` — build the voter↔donor match and recipient-party tables.
- `populate_ny_id_voter_scores.py` — fills the NY/ID `voter_scores` tables from their
  voter files with WA-identical turnout definitions (feeds Section F6).

`match_ny_voters_to_donors.py`, `match_id_voters_to_donors.py`,
`backfill_ny_committee_party.py`, `download_id_sos.py`, and `diag_ie_vs_margin.py`
import helpers from the private product codebase (`wa_analyzer` / `config` / the backtest
model) and will not run standalone here. (`download_tx_tlc.py` is self-contained and does
run.) They are included for transparency; the **paper numbers reproduce entirely from the
built tables via the `verify_*` scripts** — you do not need to rebuild to verify.

`diag_wa_rolloff_precinct.py` is a different case: it imports no private helpers and runs
here as-is, but it reads two ETL-built tables (`precinct_demographics`,
`vrdb_precinct_crosswalk`) that a from-raw rebuild of `wa_statewide.duckdb` would have to
reconstruct (ACS block-group apportionment + the VRDB precinct crosswalk). The Appendix F
*county* roll-off cut (`diag_wa_rolloff_2024.py`) has no such dependency.
