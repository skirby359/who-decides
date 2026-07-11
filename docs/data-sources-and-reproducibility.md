# Data Sources & Reproducibility

*Shared appendix for the electoral-health series — [`who-decides-washington.md`](who-decides-washington.md),
[`safe-seat-washington.md`](safe-seat-washington.md), [`cross-state-fec-money.md`](cross-state-fec-money.md),
and the parent [`electoral-health-whitepaper.md`](electoral-health-whitepaper.md). Every input is a
**public record**; this document lists each source and how to obtain it, so the studies are reproducible
from primary sources rather than from a redistributed dataset.*

---

## Reproducibility statement

These studies are **source-reproducible**: an independent researcher can obtain every input directly
from the issuing agency (links below) and re-run the analysis using the public code repository, and
should arrive at materially the same figures. They are **not bitwise-reproducible**, for two ordinary
reasons that any voter-file study shares:

1. **The voter file is a living snapshot.** State voter rolls and cumulative vote-history files change
   continuously (registrations, cancellations, address changes, each new election appended). A request
   filed on a later date returns a slightly different roll, so exact counts will differ at the margin.
   Cite the **access date** (below) when reporting.
2. **Processing must be re-run, not copied.** Name/county normalization, the precinct-namespace
   crosswalks, and the voter↔donor matcher (`match_voters_to_donors`, with its uniqueness-guarded
   tiers) must be executed on the freshly obtained data. All of this logic is in the public repository.

We therefore publish **citations + code, not data** — which is also the only lawful option for the
voter files (see *Use restrictions*).

**Code:** all loaders, the matcher, and the `scripts/diag_*.py` analysis scripts that produce every
figure in these papers are in the public repository (`github.com/skirby359/wa-political-analyzer`).
Each paper names the exact script under its figures (e.g. `scripts/diag_safe_seat_states.py`,
`scripts/diag_wa_individual_findings.py`, `scripts/diag_cross_state_money_matrix.py`).

---

## Sources by paper

### Washington — voter file, vote history, elections, money

| Asset | Issuing agency | Access | Used in |
|---|---|---|---|
| **Statewide Voter Registration Database (VRDB)** — registrants + cumulative vote history (~5.5M voters, ~27.1M vote records, ~100% **year of birth** — not full date of birth; stored as a July-1 sentinel) | WA Secretary of State | Standard statewide **VRDB extract** (the single public extract; regenerated monthly) via the SoS extract-request form (`sos.wa.gov/washington-voter-registration-database-extract`). Includes year of birth by statute — full DOB withheld (RCW 29A.08.710); use restricted to political/scholarly purposes, not redistributable (RCW 29A.08.720; penalties .740). *April 2026 extract, requested April 8 2026; vote history through the Feb 2026 special.* | Who Decides WA; cross-state §F |
| **Precinct-level election results, 2014–2025** | WA Secretary of State | `results.vote.wa.gov` per-election exports (e.g. `…/results/20241105/export/20241105_AllState.csv`) | Safe-Seat WA |
| **Campaign-finance contributions** | WA Public Disclosure Commission | PDC open data via `data.wa.gov` (Socrata); statewide contributions + the local-candidate Summary dataset (`3h9x-7bvm`). Portal: `pdc.wa.gov/political-disclosure-reporting-data` | cross-state money (WA PDC layer) |
| **King County precinct crosswalk** (`cidw-fyff`) | King County Elections / Open Data | `data.kingcounty.gov` | VRDB precinct bridging |

### Federal money — all states (FEC)

| Asset | Source | Access | Used in |
|---|---|---|---|
| **Individual contributions** (`indiv{yy}.txt`), per cycle 2018–2026 | Federal Election Commission | `fec.gov/files/bulk-downloads/` | cross-state §A–I; inflow |
| **Committee master** (`cm{yy}.zip`) + **Candidate master** (`cn{yy}.zip`) | FEC | same bulk portal | committee→candidate→office-state resolution (§G); inflow recipient anchoring |
| FEC REST API (supplemental per-candidate pulls) | FEC | `api.open.fec.gov/v1` (free API key) | finance backfills |

*Recipient-anchored inflow (`fec_inflow.duckdb`) is the FEC bulk `indiv` files filtered to committees
whose connected candidate's office state is WA/NY/TX — built by `scripts/load_fec_inflow_bulk.py`.*

### New York

| Asset | Source | Access | Used in |
|---|---|---|---|
| Precinct/county election results (incl. Assembly & Senate, 2022) | NYS Board of Elections, via **OpenElections-NY** | `github.com/openelections/openelections-data-ny` | Safe-Seat four-state map |
| NY federal contributions | FEC bulk (donor `state='NY'`) | as above | cross-state money |

### Texas

| Asset | Source | Access | Used in |
|---|---|---|---|
| VTD-level general-election returns, 2016–2024 | **Texas Legislative Council** Capitol Data Portal | `data.capitol.texas.gov` (CKAN; exact resource URLs in `scripts/download_tx_tlc.py`) | Safe-Seat |
| **r206 "Election24G" by-district reports** (President/US-Sen per House/Senate/Congressional district; cover *every* district incl. uncontested) | Texas Legislative Council | same portal (`planh2316_…`, `plans2168_…`, `planc2333_r206_election24g.xls`) | TX safe-seat backfill (§ four-state map) |
| TX federal contributions | FEC bulk (donor `state='TX'`) | as above | cross-state money |

*Why the TX backfill is needed and sound: TLC's canvass-grade VTD returns omit **uncontested** races
(no precinct tally is published when a seat is unopposed), so 96/150 House districts appear in the VTD
file. The 54 absent seats are uncontested by construction, cross-checked against the press-reported 2024
unopposed list; the r206 report supplies the partisan lean used to label their holding party.*

### Idaho

| Asset | Source | Access |
|---|---|---|
| Statewide & county election results — **general + primary canvasses, 2016–2024** (loaded via `scripts/download_id_sos.py`; primaries added 2026-07-09) | Idaho Secretary of State | `sos.idaho.gov/elections/data/results/`; archive `archive.sos.idaho.gov/ELECT/results/`; some county PDFs (e.g. Bannock County) |
| Campaign-finance contributions | Idaho SoS **Sunshine** portal | `sunshine.voteidaho.gov` (export API `api-sunshine.voteidaho.gov`) |
| Voter file w/ party affiliation + age + per-election ballot record *(loaded; powers "Who Decides Idaho?")* | Idaho SoS Elections | `forms.sos.idaho.gov/voter-registration-request-form/` ($20/report) |

*Idaho primary coverage: 2024/2022/2018/2016 include the legislative + congressional
primaries (each party's contest is a distinct race); the 2020 primary is
statewide-only (US Senate + US House) — that COVID-era mail-only cycle's legislative
results were published by the SoS at county level only, with no precinct-level file.*

### Auxiliary (warehouse-wide; not core to these three papers)

Census ACS 5-yr (`api.census.gov`; ACS 2020–2024 table B01001 → WA adult-resident age composition in
Who-Decides-WA, via `scripts/acs_wa_adult_age.py`), Census geocoder + TIGER shapefiles
(`www2.census.gov/geo/tiger`), BLS unemployment (`api.bls.gov`), WA precinct shapefiles (`sos.wa.gov`).

---

## Use restrictions (why we cite, not redistribute)

- **WA VRDB** — voter-registration data is obtainable but its use is restricted to non-commercial /
  political/scholarly purposes (WA **RCW 29A.08.720** — the lists "may be used for any political
  purpose" but not for advertising or solicitation; criminal/civil penalties at **RCW 29A.08.740**).
  Not redistributable. The standard public extract carries **year of birth, not full date of birth**:
  WA withholds full DOB as protected information (**RCW 29A.08.710**), and under **2026's SB 5892**
  an election official who discloses a full birthdate faces a class C felony. So no full DOB was ever
  obtainable via this extract.
- **ID voter file** — political/scholarly use only; no use as a mailing or telephone list without
  consent (**Idaho Code §74-120**, which releases registrant age but withholds date of birth, driver's
  license number, and — on a showing of good cause — residence address).
- **NY voter file** — FOIL access for elections purposes; aggregate outputs only.
- **FEC, TLC, SoS election results, PDC, Sunshine** — fully public, redistributable.

Because the voter files carry PII and cannot be redistributed, the studies report only aggregates and
publish the access path, not the data. (The product layer additionally enforces a PII firewall —
`src/wa_analyzer/product/firewall.py`.) *Statute citations verified against the current code 2026-06-29
(WA RCW 29A.08.720/.740; Idaho Code §74-120); confirm once more at formal-publication time.*

---

## How to replicate

1. Obtain the inputs above (file the records requests; download the public bulk files).
2. Clone the repository and load each state per its loader (`README.md` / `CLAUDE.md`).
3. Build the recipient-anchored inflow: `scripts/load_fec_inflow_bulk.py`.
4. Run the matcher: `match_voters_to_donors(conn)`.
5. Re-run the per-paper scripts named under each figure.

Report your VRDB/voter-file **access dates** alongside any replicated counts.
