# Methods and provenance supplement

### Companion to *Who Gives? The Donor Class and the Registered Electorate*

**Stephen Kirby** · Tikor Consulting · July 2026 · <kirby@tikorconsulting.com>

This file holds the material a journal article should not carry but a replication package
must: the per-figure script provenance, the verification apparatus, the reproduction recipe,
and a ledger of every claim the paper withdrew or narrowed while it was being reviewed. It is
**not** part of the submitted manuscript. The manuscript is
[`donor-class-and-the-electorate.md`](donor-class-and-the-electorate.md); the durable review
record is [`electoral-health-audit-log.md`](electoral-health-audit-log.md).

Figures quoted here are asserted against the databases by `scripts/verify_donor_class.py`,
which scrapes this file as well as the manuscript.

---

## 1. Provenance — which script produces which figure

Each panel is built by a per-state match script run once per money source (`--source fec` /
`--source state`), writing to `voter_donor_affiliation_fec` and
`voter_donor_affiliation_state`.

**Washington.** `scripts/match_wa_voters_to_donors.py` and
`scripts/diag_wa_individual_findings.py` — WA's registered roll (5.51M) + 27.1M vote records
+ birth years (`data/wa_vrdb.duckdb`), matched to 147,745 federal and 217,114 state donors.

**New York.** `scripts/match_ny_voters_to_donors.py`,
`scripts/backfill_ny_committee_party.py`, `scripts/backfill_ny_recipient_party.py`,
`scripts/diag_ny_match_bias.py`, `scripts/diag_ny_primary_participation.py`,
`scripts/diag_ny_donor_extras.py`, `scripts/diag_ny_electorate_extras.py` — NY's NYSVOTER
roll (13.54M; individual party enrollment + DOB; `data/ny_vrdb.duckdb`) matched to 10.0M FEC
itemized contributions and, via `scripts/load_ny_contributions.py`, to 3.95M NYSBOE **state**
contributions (`data/ny_statewide.duckdb`; 269,218 federal / 378,383 state matched voters).

**Idaho.** `scripts/match_id_voters_to_donors.py`, `scripts/backfill_id_recipient_party.py`,
`scripts/diag_id_electorate_extras.py` — ID's statewide roll (1.03M; individual party
affiliation + age; `data/id_vrdb.duckdb`) matched to both Idaho Sunshine **state** filings
(23,613 voters) and **federal** FEC contributions (23,303 voters), in
`data/id_statewide.duckdb`.

**Cross-cutting.** Cross-state dollar concentration: `scripts/cross_state_fec_money.py`.
Contribution-limit cuts (Appendix G): `scripts/diag_contribution_limits.py`. Denominator
standardisation, match-tier and household sensitivities, panel overlap, period-aligned
panels, Idaho composition shares, the unresolved-recipient bounds:
`scripts/diag_donor_class_revisions.py`. Age-standardized party and turnout cuts:
`scripts/diag_donor_age_standardization.py`. Linkage recall, dollar coverage and the
uniqueness guard's cost: `scripts/diag_match_rate.py`. The Washington PDC name-order defect,
measured by rebuilding the primary key both ways against the roll with a placebo control on
the comma-formatted layer: `scripts/diag_wa_pdc_name_order.py`. Match-error sensitivity at the
validation ceiling: `scripts/diag_match_error_sensitivity.py`. County multipliers split into
participation and intensity: `scripts/diag_county_decomposition.py`. The non-match cascade:
`scripts/diag_residual_decomposition.py`. Party-specific matchability, age × county
standardization, exact election eligibility: `scripts/diag_donor_review3.py`.

## 2. Verification apparatus

### What "reproducible" means here — three tiers, not one

The word does too much work unqualified, so it is split.

**Tier 1 — public computational materials: available now.** Code, schemas, the published
aggregate outputs, and the identifier-free validation verdict CSVs under `docs/reference/`. A
reader can audit every transformation and re-score the match validation without holding any
restricted data. This is what "auditable" means below.

**Tier 2 — authorised reconstruction: available to a researcher who independently obtains the
inputs.** The panels can be rebuilt from raw voter files and contribution files by someone who
obtains each state's voter file under that state's own lawful-use terms and follows §3's
dependency-ordered recipe. This is what "rebuildable by authorised data holders" means. It is not
a one-command operation, and `scripts/donor_matcher.py` is the record-linkage stage of it rather
than the whole.

**Tier 3 — independent public replication: not possible.** The three voter files cannot be
redistributed, so the linked panels cannot be published and a reader without their own copies
cannot reproduce them. This is stated rather than finessed: the word "replicable" is not used
about this work anywhere.

### The verifier

`scripts/verify_donor_class.py` reaches the databases with from-scratch SQL, imports no
analysis code, and re-derives the designated results independently of the build path. It
**scrapes the manuscript's own prose and tables** and asserts **1,465 figures** against the
databases — over the manuscript, the supplement, and the submission memo, cover letter and metadata,
which restate paper figures and were previously unchecked.

A reader running it from the public repository will see **1,444**, not 1,465, and the
difference is not a discrepancy: the memo, cover letter and metadata are operational documents
that are withheld by design, so the six probes that read them skip with a printed notice. A
missing *paper* still fails the run. The 21-figure gap is exactly those six probes — six probes
rather than 21 figures because three of them assert two values each.

It also runs a **coverage audit**: every numeric token in the **60** designated result
sections must either be captured by an assertion or carry a written exemption naming where it
*is* verified, and the run fails otherwise. So the claim is "nothing in those sections is
unaccounted for", not merely "the figures someone thought to check agree."

**Audited:** the main-body **Data, linkage, and validation** section; the four findings; the crossover tables and their restatements; the limitations
bullets on recipient party and on itemization; the derived parts of Appendices C, D and E;
Appendix F's matchability-by-party block **and its three rating tables — the precision table, the population-weighted precision table and the error-mode table — which are asserted against the frozen verdict CSVs rather than the databases**; and the derived tables of Appendix G.

**Every sliced section is now audited, and the audit distinguishes two kinds of closure.** That
distinction matters, because "nothing unaccounted for" would otherwise be read as "everything
re-derived", and it is not.

**Closed by derivation — 55 sections.** The abstract and the front matter's two-panels block
(both brought under the audit 2026-08-14, when the paper's partition was completed title to
references); the four findings; the main-body methods section and its
match-rate and sensitivity blocks; the crossover tables and their restatements; the
limitations bullets — all of them, not only the two the audit originally reached; "The
question" and "What it means"; Appendices A, B, D and E, including E's four-state statewide
table; the derived parts of C — now including the New York state-panel paragraph — and G;
the data-and-code section; **Appendix F's
three rating tables**; and **Appendix F §§F7–F8**, which hold the error-budget, de-merge,
residual-cascade and name-order tables relocated from the article body in review round 17. The
rating tables are asserted against the frozen verdict CSVs — counts, precision and
Wilson intervals recomputed from the adjudication record rather than trusted.

**Closed by written reason — 5 sections**, each naming the script that owns its figures:
Appendix F's matchability and tier-composition blocks (`diag_ny_match_bias.py`,
`diag_donor_class_revisions.py`), its per-tier donor-side risk and rating design
(`diag_match_validation_stratified.py`), its error-mode tail, Appendix C's match-key section,
and the References (a bibliography: page ranges and DOIs, not quantities).
These are separate **instruments** — inverse-propensity re-weighting, a household over-exclusion,
a persisted-column filter — and reimplementing an instrument inside the verifier copies it instead
of checking it. Appendix G's G3 and G4 tables have been exempt on that basis since review round 9.

The waiver mechanism is deliberately constrained: `tests/test_infrastructure/` requires each
waived section to exist, to be audited, to name a `.py` file, to carry a substantive reason, and
caps the list at six — because past four or five the honest move is to derive instead, which is
exactly why the rating tables were derived rather than added to it.

The audit also reports **literal exemptions that no longer fire**, as a warning rather than a
failure. An exemption is the audit's only escape hatch, so a stale one is dead weight that would
silently absorb a figure if that token reappeared in an audited section. A batch went quiet in the
2026-07-29 compression, when the prose that needed them moved to the corrections ledger.

Two limits worth stating. Appendix G's G3 layer table and G4 clipping table are **exempted
with a written reason rather than probed**: re-deriving them requires
`diag_contribution_limits.py`'s person/organization name heuristic and its residence filter,
and reimplementing those inside the verifier would copy the appendix's own instrument instead
of checking it independently. And a verifier that checks arithmetic cannot see an overclaimed
*interpretation* — two of the corrections in §4 were overclaims on analyses that passed the
audit cleanly.

## 2a. Environment, seeds, and release identity

Recorded because none of it was pinned before 2026-07-29, and a reconstruction that silently
used different versions would be a different computation.

| item | value |
|---|---|
| Python | **3.13.0** (`pyproject.toml` declares `requires-python = ">=3.11"`; the published figures were produced on 3.13.0) |
| DuckDB | **1.4.4** (`pyproject.toml` declares `duckdb>=1.1,<2`) |
| Operating system | Windows 11 |
| Release commit | recorded in the tagged archival release; **the DOI and tag are still outstanding** and must replace the branch reference in the paper before submission |
| Dependency lock | **`requirements.lock`**, committed 2026-07-29 — a full `pip freeze` of the interpreter that produced the published figures, 303 distributions. It is the whole environment rather than a minimal set, deliberately: a minimal list records what the author believes is needed, a freeze records what was actually present. `pyproject.toml` keeps its ranges for ordinary installation |
| Database schema | created by `init_schema` in `src/wa_analyzer/db.py` at the release commit |
| Storage | ~5 GB `wa_statewide.duckdb`, plus the three voter files; ~20 GB total working set |
| Runtime | a full verifier pass is minutes; a panel rebuild from raw inputs is hours, dominated by the contribution loads |
| Source digests | nine files, SHA-256, in the table below. `scripts/source_checksums.py` regenerates them |

### Source-file digests

So a reconstruction can prove it began from the same inputs rather than from a later refresh of
the same URL. Sizes are bytes; paths are relative to `data/raw/`. Regenerate with
`scripts/source_checksums.py`.

**Washington is pinned at both ends as of 2026-08-01**, which is what the New York row already
did and what this table was previously inconsistent about: the `.zip` is the production as
received, and the `.txt` inside it is what the loaders read and what the panels were built from,
so a reconstruction can verify whichever it holds. The two earlier voting-history files are
pinned individually because they came from a September 2023 production for which no archive was
retained.

| source | file | bytes | SHA-256 |
|---|---|--:|---|
| WA voter file | `vrdb/20260401_VRDB_Extract.txt` | 764,857,851 | `babe545ed9f50696b2c1eacef4dbb9f4bcbd30ff01ee33b8ca5e7be522c5d6ca` |
| WA voter file (production archive) | `vrdb/04.2026.WA.zip` | 219,835,127 | `600dccb9b08dab68ae3910d02203d8682ada056d66ff39143e3e5392925fc909` |
| WA voting history 2023–2024 | `vrdb/2023-2024_Voting_History.txt` | 448,358,084 | `7a51e8e53ab0f78e86ed3cb655de710f83aff9d36a1ad344cf630a12ccb20c7f` |
| WA voting history 2021–2022 | `vrdb/2021-2022_Voting_History.txt` | 347,543,952 | `b3c0c5fc19796bb4d43247275834963856fd71941b322e242999dd8fdf70a831` |
| NY voter file | `ny/ALLNYVOTERS20260629.zip` | 928,142,538 | `ea0b97ccb027b6bfce571d17f7ef19b8135e1c10ed8cbbec136f4b73e3ef4807` |
| NY state contributions | `ny/Campaign_Finance_…Contributions…20260605.csv` | 4,256,024,299 | `3a161b5aa8222bfacd5670c2d73162967460dfcabce20ddeecb24a1c32737c83` |
| ID voter + history | `id/id_statewide_voter_history_20260629.csv` | 423,646,898 | `673b0fceca916604623cf04b8e85e80cc182c7e9483f17f76824f90b5b63a36b` |
| ID Sunshine contributions 2024 | `id/_source/id_2024_TCON.csv` | 22,618,178 | `c69e39c0f896f1485111548a96915d55a2992fa5cb639d9a1a2871f7be6b2d82` |
| ID Sunshine contributions 2025 | `id/_source/id_2025_TCON.csv` | 18,453,071 | `4f8081ad8f6cec3ba1ea56fa7b21e950b0f2e07e0136333baefb5ffde9515cfc` |

**Two absences, stated rather than left to be noticed.** The **FEC bulk individual-contribution
files carry no digest**: the loader streams roughly 30 GB per cycle and deletes each after loading
unless `--keep-files` is passed, so no local copy survives. They are re-downloadable from the
Commission and are identified by cycle (2018 through 2026). And **Idaho ships registration and
participation in one combined export**, so there is no separate roll file to hash.

**Random seeds.** Two computations draw randomly, and both are seeded and deterministic given the
same call order:

- **Match-validation sampling** — `scripts/diag_match_validation_stratified.py`,
  `DEFAULT_SEED = "2026-07-27"`. The draw is `md5(state_voter_id || SEED)`, so it is stable and
  re-runnable; `--seed` draws a different sample deliberately.
- **Concentration bootstrap** — `scripts/diag_donor_concentration_bootstrap.py`, `SEED = 12345`,
  `numpy.random.default_rng(SEED)`. **One generator is threaded through every panel in sequence**,
  which is why that script's panel list is append-only: inserting or reordering a panel changes
  every interval computed after it. This is a real reproducibility hazard and is flagged rather
  than silently relied upon.

**Checksums.** Source-file checksums for the raw inputs are not currently recorded. They should be
captured at the archival release, because the state voter files are re-issued periodically and a
future reconstruction has no other way to confirm it holds the same extract.

## 2b. Validation provenance — who judged what

The match-precision result rests on human and AI judgement, so the provenance of that judgement
is part of the method.

- **The stratified sample.** 480 matched records, 20 per stratum across 4 match tiers × 2 dollar
  bands × 3 states, drawn by the seeded procedure above.
- **What an adjudicator saw.** A blinded evidence extract pairing the voter-file name and the
  contributor name with the shared ZIP, and nothing else — no state, no panel, no match tier, no
  dollar decile. The stratum key is held in a separate file and joined only after verdicts are
  recorded, so a rater cannot know which tier they are judging.
- **First pass — AI-assisted.** The initial 480 verdicts were produced with AI assistance under
  the author's review, against the blinded extract. Published as
  `docs/reference/match_validation_verdicts_2026-07-27.csv`, keyed on a synthetic `sample_id`.
- **Second pass — blind re-rate by the same rater.** 150 of those records were re-rated by the
  author, blind to the first pass, from the same blinded evidence — so this is test–retest and
  not inter-rater reliability. Published as
  `docs/reference/match_validation_human_verdicts_2026-07-27.csv`. Agreement and the direction of
  every disagreement are reported in Appendix F. Because both passes saw the same evidence, this
  is inter-rater reliability, **not** ground truth.
- **Confidentiality.** The human rater worked from the blinded extract, which pairs real names. No
  written confidentiality undertaking was obtained — a gap recorded in the ethics assessment's
  open items rather than left implicit.
- **Retention.** The PII-bearing evidence file and the `sample_id → state_voter_id` map live only
  under gitignored `data/validation/` and are never published. **No destruction date is set**;
  setting one is an open item.

## 3. Reproduction, in dependency order

Each match script builds ONE panel per run, selected with `--source`; the two panels are
never pooled.

```bash
# Washington — both panels:
python scripts/match_wa_voters_to_donors.py --source fec
python scripts/match_wa_voters_to_donors.py --source state
python scripts/diag_wa_individual_findings.py

# New York — both panels:
python scripts/load_ny_voters.py                  # NYSVOTER FOIL -> ny_vrdb.duckdb
python scripts/diag_ny_turnout_party.py --rebuild # voter_participation table
python scripts/backfill_ny_committee_party.py     # bulk FEC committee/candidate party
python scripts/load_ny_contributions.py           # NYSBOE per-contribution rows (state layer)
python scripts/backfill_ny_recipient_party.py     # state recipient party
STATE=NY python scripts/match_ny_voters_to_donors.py --source fec
STATE=NY python scripts/match_ny_voters_to_donors.py --source state
STATE=NY python scripts/diag_ny_match_bias.py           # age-skew validation
STATE=NY python scripts/diag_ny_primary_participation.py
STATE=NY python scripts/diag_ny_donor_extras.py

# Idaho — both panels (party of record + current-roll age):
python scripts/load_id_voters.py                       # ID SoS voter file -> id_vrdb.duckdb
STATE=ID python scripts/backfill_id_recipient_party.py
STATE=ID python scripts/match_id_voters_to_donors.py --source fec
STATE=ID python scripts/match_id_voters_to_donors.py --source state
python scripts/diag_id_electorate_extras.py

# Cross-state concentration and the appendices:
python scripts/cross_state_fec_money.py                # Appendix E statewide table
python scripts/diag_donor_concentration_bootstrap.py   # Appendix E intervals
python scripts/diag_donor_match_ceiling.py             # Appendix F ceilings
python scripts/diag_contribution_limits.py             # Appendix G

# Review recomputations:
python scripts/diag_donor_class_revisions.py
python scripts/diag_donor_class_revisions.py --build-aligned   # period-aligned ID panels
python scripts/diag_donor_age_standardization.py
python scripts/diag_donor_review3.py

# Match-precision validation (Appendix F). The sampler writes a BLINDED evidence file
# (no state / panel / tier / decile) plus a separate stratum key; the scorer joins them
# only after verdicts are recorded. Both files are PII-bearing and gitignored; the
# verdicts alone are published at docs/reference/match_validation_verdicts_2026-07-27.csv.
python scripts/diag_match_validation_stratified.py     # 480 records, 20 per stratum
python scripts/score_match_validation.py               # per-tier precision + reweighting

# Independent re-derivation of every published figure:
python scripts/verify_donor_class.py
```

Rebuilding the panel tables from raw voter files is covered separately, by the extracted
matcher the release ships as `scripts/donor_matcher.py` — a standalone extract (function body
verbatim from `src/wa_analyzer/analysis/donor_analysis.py`, with the `contributor_type`
helpers and a minimal DDL folded in) depending on nothing but `duckdb` and the standard
library. Rebuilding the Idaho federal panel through it reproduces the published panel
exactly: 0 differing rows in either direction across all 9 columns of all 23,303 rows.

```bash
# --tiers full is the default and is the primary specification; --tiers all reproduces
# the superseded all-tier specification.
python scripts/match_id_voters_to_donors.py --source fec --tiers full
```

**Two cautions for a replicator.** `--tiers` restricts which tier joins fire, so a
contribution reachable only by a weaker key is dropped; filtering an all-tier panel on
`match_quality` instead keeps a full-name donor's entire dollar total. The two give identical
donor counts but dollar totals differing by 3.8–9.4%, so a figure must not be moved between
them. And the ranks are absolute: renumbering them for a restricted call would label a
`RELAXED_ZIP3_MID` panel `STRICT_ZIP5_FULL`.

All inputs are public records (FEC bulk files; Idaho Sunshine, Washington PDC and NYSBOE
filings; state voter files obtained under each state's lawful-use terms — NY NYSVOTER FOIL,
WA VRDB, ID SoS statewide list under Idaho Code § 34-437A(3)). See
[`data-sources-and-reproducibility.md`](data-sources-and-reproducibility.md) for the full
source ledger.

## 4. Corrections and review history

Moved out of this file on 2026-07-29. A reviewer needs the final methods and the rationale for
withdrawn claims where that rationale is substantive — both of which are above and in the paper's
own limitations section — not a catalogue of drafting errors. The catalogue is preserved at
[`donor-class-corrections-ledger.md`](donor-class-corrections-ledger.md), and the round-by-round
review record at [`electoral-health-audit-log.md`](electoral-health-audit-log.md).

Three withdrawn claims are load-bearing enough that the manuscript carries the reasoning itself
rather than delegating it: why the state-panel crossover results are suggestive only (an
adversarial bound on the unresolved recipient pool overturns every state row but one), why
Appendix G carries no statutory label on any row (recipient type and election designation are not
persisted, so no row is a legal counterfactual), and why the common donor-total restriction is a
robustness check rather than a threshold experiment (at least four mechanisms move together).

## 5. Series

Paper #3 of the electoral-health series:
[`who-decides-washington.md`](who-decides-washington.md) (the gray off-year electorate),
[`who-decides-new-york.md`](who-decides-new-york.md) and
[`who-decides-idaho.md`](who-decides-idaho.md) (party-resolved electorates),
[`safe-seat-washington.md`](safe-seat-washington.md) (observed competitiveness), and
[`cross-state-fec-money.md`](cross-state-fec-money.md) (the four-state money layer).
