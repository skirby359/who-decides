# scripts/

Two tiers.

## Verification (reproduces the papers — standalone, `duckdb` + stdlib only)

- `verify_*.py` — the six one-per-paper re-derivations; each prints `derived (paper: …)`.
- `diag_*.py` — the underlying analyses cited in the papers (turnout decomposition,
  roll-off, safe-seat counts, cross-state concentration, donor age skew, etc.). All run
  standalone except `diag_ie_vs_margin.py` (the Finding-6 IE-vs-margin analysis), which
  needs the private forecast model — see the provenance caveat below.
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
