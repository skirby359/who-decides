# who-decides

Open-source code and papers behind **“Who Decides Washington?”** and its companion
studies of who returns the ballot — the age (and, where the state publishes party of
record, partisan) composition of American electorates across the presidential →
midterm → off-year salience gradient.

**Lead paper:** [`docs/who-decides-washington.md`](docs/who-decides-washington.md)
(Stephen Kirby, Tikor Consulting). Companions cover New York, Idaho, safe-seat
competitiveness, and cross-state campaign money.

Every headline number in the papers is re-derived from scratch by the `verify_*.py`
scripts here — read-only, aggregate-only, printed next to the paper's value for a
cell-for-cell check.

## The reproducibility model (read first)

**Code and citations are shared; the raw voter file is not.** Washington's statewide
voter database (VRDB) — and the other states' voter files — may not be redistributed
(e.g. RCW 29A.08.720), so this repo does **not** ship voter data. It ships the exact,
auditable code plus a data-access recipe:

1. **Obtain the data yourself** from the public sources (below) — the same standard
   state extracts the papers used.
2. **Place the DuckDB files in `data/`** (git-ignored).
3. **Run the verifiers** — each prints `derived value  (paper: …)`; a match confirms
   the finding independently of the analysis code.

The papers and scripts emit **aggregate cohort counts only** (cells in the thousands to
millions); no individual records are published.

## Quick start

```bash
python -m pip install duckdb          # verifiers need only this
# optional: pip install markdown  + install wkhtmltopdf   (to re-render the PDF)
# optional: a free Census API key in a .env as CENSUS_API_KEY=...  (for the ACS rows)

# with data/ populated (see "Data access"):
python scripts/verify_who_decides_wa.py     # WA lead paper — sections #1–#29
```

Run any of the six verifiers; each maps to one paper:

| Script | Paper |
|---|---|
| `verify_who_decides_wa.py` | Who Decides Washington? |
| `verify_who_decides_ny.py` | Who Decides New York? |
| `verify_who_decides_id.py` | Who Decides Idaho? |
| `verify_safe_seat.py` | Safe-Seat Washington |
| `verify_donor_class.py` | The Donor Class Is Not the Electorate |
| `verify_cross_state_money.py` | Three States, Three Donor Economies |

The `diag_*.py` scripts are the underlying analyses; the `load_*/match_*/backfill_*`
scripts are **build provenance** (how the DuckDB tables were assembled) and are not on
the verification path — see [`scripts/README.md`](scripts/README.md).

## Data access

| Input | Source | Notes |
|---|---|---|
| Voter files → `data/{wa,ny,id}_vrdb.duckdb` | State voter-registration extracts (WA VRDB, NYSVOTER, ID SoS) | Not redistributable — obtain your own copy |
| Results / precinct data → `data/{wa,ny,id,tx}_statewide.duckdb` | State SoS certified results | Public |
| FEC inflow → `data/fec_inflow.duckdb` | FEC bulk individual contributions | Public; built by `scripts/load_fec_inflow_bulk.py` |
| Adult / CVAP age composition | U.S. Census ACS (tables B01001, B29001) | Pulled live by `scripts/acs_wa_adult_age.py` |

See [`docs/data-sources-and-reproducibility.md`](docs/data-sources-and-reproducibility.md)
for full provenance and access paths.

## License

- **Code:** MIT (`LICENSE`).
- **Papers** (`docs/*.md`, `docs/*.pdf`): CC-BY 4.0.
- **Data:** not included; governed by the source states' voter-file statutes.
