# who-decides

Open-source code and papers behind **“Who Decides Washington State?”** and its companion
studies of who returns the ballot — the age (and, where the state publishes party of
record, partisan) composition of American electorates across the presidential →
midterm → off-year salience gradient.

**Lead paper:** [`docs/who-decides-washington.md`](docs/who-decides-washington.md)
(Stephen Kirby, Tikor Consulting). Companions cover New York, Idaho, safe-seat
competitiveness, cross-state campaign money, who funds the candidates, and whether that
money moves margins.

Every headline number in the papers is re-derived from scratch by the reproduction script
listed against it below — read-only, aggregate-only, and printed next to the paper's value
for a cell-for-cell check. Since 2026-08-01 every paper has a `verify_*.py`, and each of
them SCRAPES ITS PAPER: the probes are regexes anchored on the surrounding words, so a
figure is compared against the sentence that states it rather than against a constant a
maintainer typed. Consequences worth knowing before you run one — a probe whose anchor
matches nothing FAILS rather than skipping, and every occurrence of a figure is checked, so
a paper that states the same number two different ways fails on whichever one is wrong.
Pass `--coverage` to any of them to list numeric tokens in that paper no probe touches.

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

### What "reproducible" covers, precisely (2026-07-27)

Two different things get conflated, so they are separated here:

- **Re-deriving the published aggregates: fully covered.** Every `verify_*.py` reaches the
  built DuckDB tables with from-scratch SQL and imports no analysis code, so a match
  confirms each finding independently of the build path.
- **Rebuilding the donor panels from raw voter files: also covered, as of 2026-07-27.**
  The record-linkage step is no longer a private dependency. `scripts/donor_matcher.py` is
  a standalone extract of `match_voters_to_donors` — the function body verbatim from
  `src/wa_analyzer/analysis/donor_analysis.py`, with the two `contributor_type` helpers and
  a minimal DDL for the two tables it writes folded in, and its two internal imports
  removed. It depends on nothing but `duckdb` and the standard library, so
  `match_{wa,ny,id}_voters_to_donors.py` now run from a bare clone. Verified by rebuilding
  the Idaho federal panel through the public wrapper and anti-joining it against the
  published one: **0 rows differ in either direction across all 9 columns of all 23,303
  rows**, and the script reprints the paper's Idaho figures (66.8% aged 65+, top 1% = 37.2%
  of matched dollars).

  Two things to know before you rebuild. **Pass the tier restriction.** The published
  panels are the *primary specification* — the full-first-name key alone
  (`--tiers full`, the default; `PRIMARY_TIERS` in code). `--tiers all` reproduces the
  superseded all-tier specification, which carries the initial-based keys measured at
  47.9–71.7% precision. **And `--tiers` is not the same as filtering on `match_quality`.**
  Restricting the match drops a contribution reachable only by a weak key; filtering a
  built panel keeps a full-name donor's whole dollar total. Both give identical donor
  counts, but dollars differ by 3.8–9.4%. Never move a dollar figure between the two.

The match-precision validation is auditable without any of that: the per-record verdicts
for both the 480-record blinded pass and the 150-record independent human re-rating are
published under [`docs/reference/`](docs/reference/), stripped of names — sample id,
stratum, verdict. `docs/reference/match_validation_tier_shares_2026-07-27.csv` carries the
frozen reweighting shares, so the published 93.0% figure re-derives from the ledger alone
with no database at all.

## Quick start

```bash
python -m pip install duckdb          # verifiers need only this
# optional: pip install markdown  + install wkhtmltopdf   (to re-render the PDF)
# optional: a free Census API key in a .env as CENSUS_API_KEY=...  (for the ACS rows)

# with data/ populated (see "Data access"):
python scripts/verify_who_decides_wa.py     # WA lead paper — sections #1–#30
```

Each paper has a reproduction entry point:

| Script | Paper |
|---|---|
| `verify_who_decides_wa.py` | Who Decides Washington State? |
| `verify_who_decides_ny.py` | Who Decides New York? |
| `verify_who_decides_id.py` | Who Decides Idaho? |
| `verify_safe_seat.py` | Safe-Seat Washington |
| `verify_donor_class.py` | The Donor Class Is Not the Electorate |
| `verify_cross_state_money.py` | Four States, Four Donor Economies |
| `verify_money_votes.py` | Does Money Move Votes in Washington? |
| `verify_whitepaper.py` | Electoral Health (Findings 4-6) |

Notes on that table:

- **Safe-Seat Washington.** `verify_safe_seat.py` was rebuilt on 2026-08-01. The version it
  replaces derived the seat universe from the results table, which silently dropped 24 King
  County House seats per cycle in 2016 and 2018; this one builds the universe from the
  certified statewide summary returns and reconciles it against the statutory chamber size
  before computing anything. It parses those returns in SQL, while
  `diag_seat_competition.py` streams them through Python — same inputs, independent
  implementations, so a slip in either would have to be reproduced in the other to survive.
- **Two papers read a PINNED snapshot and fail loudly without it**, because their figures
  are computed against a table that is rebuilt routinely and would otherwise drift out from
  under the published number. `verify_who_decides_ny.py` needs `ny_paper_roll`
  (`scripts/pin_ny_roll.py`); `verify_money_votes.py` needs the two frozen frames under
  `docs/reference/`. Re-pinning either is a deliberate act behind an explicit flag and moves
  published figures.
- **Does Money Move Votes** reports a null and a data ceiling, so most of what there is to
  reproduce is that the tests come back empty and that `diag_ie_vs_margin.py` still declines
  to report a slope at n=7. `verify_money_votes.py` asserts the data-ceiling facts from
  scratch and the correlations against the pinned frames; the cross-cycle holdout R² table
  is the one block it does not check, because scoring that fit needs the candidate-quality
  components and the frame does not carry them. The script says so in its own output.
- **The donor paper's recomputations** — tier and household sensitivities, panel overlap,
  period alignment — are in `diag_donor_class_revisions.py`, alongside the verifier.

The remaining `diag_*.py` scripts are the underlying analyses; the
`load_*/match_*/backfill_*` scripts are **build provenance** (how the DuckDB tables were
assembled) and are not on the verification path — see
[`scripts/README.md`](scripts/README.md).

## Data access

| Input | Source | Notes |
|---|---|---|
| Voter files → `data/{wa,ny,id}_vrdb.duckdb` | State voter-registration extracts (WA VRDB, NYSVOTER, ID SoS) | Not redistributable — obtain your own copy |
| Results / precinct data → `data/{wa,ny,id,tx}_statewide.duckdb` | State SoS certified results | Public |
| FEC inflow → `data/fec_inflow.duckdb` | FEC bulk individual contributions | Public; built by `scripts/load_fec_inflow_bulk.py` |
| Adult / CVAP age composition | U.S. Census ACS (tables B01001, B29001) | Pulled live by `scripts/acs_wa_adult_age.py` |

See [`docs/data-sources-and-reproducibility.md`](docs/data-sources-and-reproducibility.md)
for full provenance and access paths.

## Citing

See [`CITATION.cff`](CITATION.cff). An archival DOI has not been minted yet, so the papers
currently link this repository rather than an immutable tagged tree — cite the commit hash
if you need a stable reference in the meantime.

## License

- **Code:** MIT (`LICENSE`).
- **Papers** (`docs/*.md`, `docs/*.pdf`): CC-BY 4.0.
- **Data:** not included; governed by the source states' voter-file statutes.

