# scripts/

Two tiers.

## Verification (reproduces the papers — standalone, `duckdb` + stdlib only)

- `verify_*.py` — the six one-per-paper re-derivations; each prints `derived (paper: …)`.
- `diag_*.py` — the underlying analyses cited in the papers (turnout decomposition,
  roll-off, safe-seat counts, cross-state concentration, donor age skew, etc.). All run
  standalone except two, which need build inputs beyond the public extract (see the
  provenance caveat below): `diag_ie_vs_margin.py` (the Finding-6 IE-vs-margin analysis,
  needs the private forecast model) and `diag_wa_rolloff_precinct.py` (the Appendix F
  precinct-level roll-off cut, needs the `precinct_demographics` and
  `vrdb_precinct_crosswalk` tables assembled by the upstream ETL). Its coarser sibling
  `diag_wa_rolloff_2024.py` (county-level) reproduces from public returns + the VRDB alone.
- `acs_wa_adult_age.py` — pulls the ACS/CVAP rows (needs a Census API key).
- `md_to_pdf.py` — renders a paper `.md` to PDF (needs `markdown` + `wkhtmltopdf`).

Run from the repo root with `data/` populated. Side artifacts (JSON) go to `reports/`
(git-ignored).

## Build / provenance (how the DuckDB tables were assembled — NOT on the verification path)

- `download_*.py` — fetch the public certified-results files (Idaho SoS, Texas
  Legislative Council) into `data/raw/` before `load_*` builds the tables.
- `load_*.py` — build the state DuckDB files from raw voter/FEC bulk downloads.
- `match_*.py`, `backfill_*.py` — build the voter↔donor match and recipient-party tables.

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
