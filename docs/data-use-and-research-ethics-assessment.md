# Data-use and research-ethics assessment

*Self-assessment for the electoral-health research series, in particular
[`donor-class-and-the-electorate.md`](donor-class-and-the-electorate.md), which links three
state voter-registration files to itemized campaign-finance records at the individual level.*

**Author:** Stephen Kirby, Tikor Consulting
**Prepared:** 2026-07-29 · **Revised:** 2026-07-29 · **Status:** DRAFT — requires the author's
signature. **"Determination" is reserved for an external reviewer's letter; this document is an
assessment.**
**Prompted by:** external reviewer item 10, which asked for "a documented data-use and
research-ethics determination, particularly for Washington's restricted voter file and the use
of identifiable administrative records."

---

## 0. What this document is, and what it is not

This is a **self-assessment**, not an Institutional Review Board determination, and not an
official determination of regulatory status. The author is unaffiliated; the project is not
known to be federally funded or conducted under any institution's Federalwide Assurance, and it
has therefore **not been submitted through an institutional IRB process**. That is a statement
about which review requirements have attached, not a claim that no ethics body could evaluate
this work — a commercial IRB or qualified research-ethics committee can, and §8 records that as
the stronger course.

The point is stated first because it is the most important thing a reader needs to know: what
follows is the researcher's own reasoning, documented so it can be checked and contested. OHRP
advises against investigators making their own exemption determinations, precisely because of
the conflict inherent in doing so; that advice is noted here rather than argued with.

Where this could be wrong, and what would change it, is in §7. If a journal requires
institutional or independent review, this document is an input to that process, not a
substitute for it.

---

## 1. The data, and the authority for holding it

| source | contents used | legal basis | restricted? |
|---|---|---|---|
| WA VRDB (Secretary of State standard statewide extract) | name, address, jurisdiction, gender, **year of birth**, voting record, registration date/number | RCW 29A.08.710 (public file contents); RCW 29A.08.720 (permitted use); RCW 29A.08.740 (penalties) | **Yes** — use-restricted, not redistributable |
| NY NYSVOTER statewide file | name, address, **party enrollment**, **full date of birth**, voting record | N.Y. Pub. Off. Law art. 6 (FOIL), subject to the Board's elections-purpose certification | **Yes** — obtained under FOIL with a purpose certification |
| ID statewide voter list | name, address, party affiliation, **age** (not DOB), voting record | Idaho Code § 34-437A — public statewide list; prohibits advertising and solicitation uses, permits political purposes. (§ 74-120 is a *separate*, general restriction on agency distribution or sale of lists for use as mailing or telephone-number lists — not a bar on "derived lists" at large) | **Yes** — use-restricted |
| FEC bulk individual contributions | contributor name, ZIP, employer/occupation, amount, date, recipient | 52 U.S.C. § 30104 — mandatory public disclosure — **and 52 U.S.C. § 30111(a)(4) / 11 C.F.R. § 104.15**, which bar using information copied from a filed report to solicit contributions or for any commercial purpose | **Yes — disclosed but use-restricted.** § 104.15(c) safe harbour for publication; see §2a |
| WA PDC, NY State Board of Elections, Idaho Sunshine | same, per state statute | RCW 29B (formerly 42.17A); N.Y. Elec. Law § 14-102; Idaho Code § 67-6607 | No — open |

Two asymmetries matter for the analysis that follows. The **campaign-finance** records are
public by design: disclosure is the statutory purpose, and the individuals in them are
identified *because* the legislature decided contributions above a threshold should be
attributable. The **voter files** are public in a narrower sense: released by statute, but
subject to use restrictions and, in all three states, not redistributable.

**A correction to how that asymmetry was previously stated.** An earlier version of this table
marked the federal contribution layer "No — open", citing only § 30104. That was wrong, and it
was the only row in the table without a use analysis. Disclosure is not the same as
unrestricted use: the same statute that compels publication also limits what the published
information may be used *for*. The legislature's answer to "public for what" is § 30111(a)(4),
and it is analysed in §2a.

## 2. Permitted use of the Washington file, in the statute's own terms

This was restated in the paper's Appendix B on 2026-07-28 after an earlier draft summarised it
too loosely as "use is restricted to elections and political purposes and may not be
commercial." The statute is narrower and differently shaped than that. RCW 29A.08.720
**prohibits** using the lists or labels

> "for the purpose of mailing or delivering any advertisement or offer for any property,
> establishment, organization, product, or service or for the purpose of mailing or delivering
> any solicitation for money, services, or anything of value"

and **affirmatively permits** use "for any political purpose," which it defines to include
activity concerned with support of or opposition to any candidate for partisan or nonpartisan
office or to any ballot proposition, expressly including "advertising for or against any
candidate or ballot measure or the solicitation of financial support" for those purposes.

So the operative test is not commerciality in the abstract. **Commercial advertising and
solicitation are barred; political activity, including political fundraising, is permitted.**

**The basis relied on here.** This series' use is research into electoral participation and
campaign finance, published as aggregate findings. No advertisement, offer, or solicitation
for property, establishment, organization, product, or service is mailed or delivered from
these data, and no solicitation for money, services, or anything of value is made from them.
The prohibited purposes are therefore not engaged.

**Why this is stated rather than assumed.** The author is associated with a political
consulting company, and the same underlying database supports candidate-facing tooling
(prospect lists, walk lists, segment messaging) that *is* political-purpose activity within
the statute's permission. That work and this research draw on the same warehouse. The
distinction relied on is not that one is "non-commercial" but that (a) both fall inside the
statute's political-purpose permission rather than its prohibition, and (b) the research
outputs contain no individual-level records at all (§4). A reader is entitled to know the
consulting association exists rather than infer it, which is why the papers disclose it in
their byline blocks and why it is named here.

## 2a. Permitted use of the federal contribution file, in the statute's own terms

**11 C.F.R. § 104.15**, implementing **52 U.S.C. § 30111(a)(4)**, provides that information
copied or otherwise obtained from any report filed under the Act

> shall not be sold or used by any person for the purpose of soliciting contributions or for any
> commercial purpose, except that the name and address of any political committee may be used to
> solicit contributions from such committee.

§ 104.15(b) reads "soliciting contributions" broadly — it reaches any type of contribution or
donation, political or charitable. § 104.15(c) is the publication safe harbour: use of such
information in "newspapers, magazines, books or other similar communications" is permissible so
long as the principal purpose of the communication is not to communicate contributor information
for the purpose of soliciting contributions or for other commercial purposes.

**The basis this research relies on.** The papers report aggregates, name no contributor, and
solicit nothing. Their principal purpose is to describe the composition of the donor population
against a registration baseline. That is squarely within § 104.15(c), and it is the basis relied
on — not a claim that the FEC file carries no use restriction.

**The own-committee exception is not relied on.** Nothing in this work uses a committee's name
and address to solicit that committee.

**What this required changing, and it was not only wording.** Until 29 July 2026 the same
warehouse supported candidate-facing tooling that produced ranked prospect lists: prior donors
with name, address, employer, occupation, giving history and a suggested dollar ask, rendered
under headings describing them as solicit-able and instructing the reader to prioritise re-asks.
Roughly 97% of that output rested on FEC-derived data. That is the use § 104.15 prohibits, and
no permission in a state voter-file statute cures it — Washington's political-purpose permission
(§2) and New York's elections purpose (§2b) both expressly reach fundraising, but neither
governs contributor information copied from a federal report.

**Those features were removed**, for federal and state money alike, rather than
source-segregated. The boundary now implemented is that **no named contributor and no named
matched donor appears in any report, export, or analysis output.** What went, what was kept, the
scale of what existed, and the questions still open are recorded in
`fec-contributor-data-use-memo.md` — an internal compliance record retained by the author. It is **not published**: it sets out a compliance exposure in the author's commercial tooling and the questions put to counsel, neither of which is research material.

**What remains, and is flagged rather than resolved.** Aggregate donor cuts computed from FEC
contributor rows — whale dependency, grassroots breadth, top cities — are still rendered in
briefs that are sold. They name nobody. Whether a paid brief is a "similar communication" within
§ 104.15(c), and so whether any FEC contributor use in a commercial product is a "commercial
purpose" independent of solicitation, is a legal question this assessment does not answer. It is
listed in §8.

## 2b. Permitted use of the New York and Idaho files

**New York.** N.Y. Election Law **§ 3-103(5)** requires that a requester certify the data will
be used for an "elections purpose", and prohibits use of information derived from registration
records for non-election purposes. The State Board of Elections states, in its own published
guidance on such requests, that an elections purpose "has traditionally been interpreted broadly
and among other things includes campaigning, voter outreach, fundraising and academic research."
Academic research is therefore within the certified purpose on the Board's own stated
interpretation — which is what this is, and the citation is to the Board's guidance rather than
to statutory text, because the statute itself does not enumerate. The FOIL production carries
**full date of birth**; §4 records the control applied to it.

**Idaho.** **Idaho Code § 34-437A** governs the public statewide list of registered electors.
It is the operative provision: it prohibits using the list for advertising or solicitation
purposes and permits political purposes, a structure close to Washington's. **§ 74-120 is a
different provision** — a general restriction on an agency distributing or selling lists for use
as mailing or telephone-number lists — and an earlier version of §1 above described it as barring
"sale/distribution of derived lists", which overstates it. This work publishes no list, sells no
list, and mails and telephones nobody, so neither provision is engaged by it.

**Both are now analysed rather than merely cited**, which closes open item 1 as it previously
stood in §8.

## 3. Human-subjects determination

**Assessment: this work is very likely outside the Common Rule's coverage, and on the
researcher's reading is not human-subjects research requiring IRB review.** Both limbs are set
out, with the weak points, and neither is offered as a determination — see §0 and §8.

1. **No intervention or interaction.** No individual is contacted, surveyed, recruited,
   observed, or manipulated. The work is secondary analysis of records that already exist.
2. **The records are not "private information" in the Common Rule's sense.** 45 CFR
   46.102(e)(4) defines private information as information about behavior in a context where
   an individual can reasonably expect no observation or recording, or information provided
   for specific purposes that the individual can reasonably expect will not be made public.
   Voter registration and itemized contributions are the opposite: the individual's
   registration and giving are recorded and published *pursuant to statute*, and the
   expectation established by law is that they are attributable. Voting *choices* are secret;
   the fact of registration, party enrollment where applicable, the fact of having voted, and
   contributions above a disclosure threshold are not.
3. **Coverage, not exemption, is the more likely answer.** The Common Rule applies to research
   conducted or supported by a federal department or agency, or otherwise brought within an
   institution's Federalwide Assurance. This project is neither: unaffiliated, unfunded by any
   federal source, and not covered by any FWA. That is a question about **regulatory coverage**,
   and it is a cleaner answer than an exemption claim.

**Where the previous version of this section was wrong, corrected.** It asserted that the
secondary-research exemption at 45 CFR 46.104(d)(4) was independently satisfied "regardless of"
the publicly-available limb, on the ground that no *output* contains an identifier. **That is
not what the provision requires.** The de-identified-recording limb asks whether the
investigator **records** the information such that the subjects' identity cannot readily be
ascertained, directly or through identifiers linked to them, and additionally requires that the
investigator not re-identify or contact them. This project does the opposite of de-identified
recording: it retains names, addresses, state voter identifiers, linked donor–voter tables, and
a PII-bearing validation evidence file. Aggregate-only *publication* does not satisfy a
condition about *recording*, and the claim is withdrawn.

What is left, stated honestly. If the exemption were reached at all, it would have to rest on
the **publicly available** limb — and that limb is a poor fit for the voter files, which are
released under statute but carry use restrictions and cannot be redistributed. So the position
is: limbs 1 and 2 above, plus the coverage point, plus the disclosure controls in §4. A reviewer
who rejected limb 2 for the voter files would be making a defensible argument, and the honest
response is the coverage question, not a de-identification claim this project cannot make.

## 4. Disclosure controls, as implemented rather than as intended

These are properties of the code and the published artifacts, and each is checkable:

- **No individual-level record is published.** Every figure in the papers is a share, count,
  mean, or concentration statistic over a group.
- **The smallest *derivable* cell describes 25 individuals**, and that is the figure that
  matters. An earlier version of this document said 44 and that no published cell reported one.
  Both were wrong. 44 was the smallest printed *base*, not the smallest cell: a percentage
  printed over a small base lets a reader recover a count by multiplication, and Idaho's
  minor-party crossover rows — bases of 102 and 44 — disclosed cells of **2** and **8
  individuals** that way. Those rows were **withheld from the paper on 29 July 2026** as a
  disclosure control. After that suppression the smallest derivable population cell is 25.
  Two smaller printed numbers are not population cells and are not disclosures of new
  individual information: Appendix F's validation tables count **rated sample records**, which
  are themselves already published at row level stripped of every identifier, and Appendix G's
  bunching table prints a count of 1 *contribution* at a dollar amount, already public by name
  in the Idaho Sunshine filing it came from.
- **The raw data never enters the repository.** `.gitignore` excludes `data/` wholesale plus
  `*.duckdb`. The three voter files and all contribution extracts live only on the author's
  machine.
- **Published validation artifacts are identifier-free by construction.** All four CSVs under
  `docs/reference/` key on a synthetic `sample_id`; none carries a name, address, or
  `state_voter_id`. The match-validation *evidence* file, which necessarily pairs voter names
  with donor names for a human rater to judge, is written only under gitignored
  `data/validation/` and is not published.
- **The sample_id → state_voter_id map added 2026-07-28 is PII-adjacent and gitignored.** It
  exists so a later validation draw can exclude already-rated records; it links a sample row
  to a real registrant and must never be committed or published. This is recorded here because
  it is the newest disclosure-relevant artifact and the one most likely to be mishandled.
- **Individual-level donor output was removed from the tooling on 29 July 2026** (§2a). This is
  the newest and largest control, and it is a removal rather than a filter: no named contributor
  or named matched donor is produced by any report, export, or analysis path.
- **The customer-facing product layer has independent controls** (`src/wa_analyzer/product/`):
  a query-time default-deny allowlist that makes individual voter and donor tables unreachable
  from report builders, and a render-time scrub. Two honest limits on how much weight that
  carries. It protects the *neutral product layer* only — the partisan campaign tooling takes a
  raw connection and the allowlist cannot reach it. And two keys declared in its config,
  `restricted_file_globs` and `restricted_column_patterns`, are **not read by any code**, so the
  config overstates what is enforced. Both are recorded here rather than left for a reader to
  discover, and making those keys live is tracked separately.

### Data governance, and where it is incomplete

Stated as implemented or not implemented, because an aspirational list is worse than a short
honest one.

| control | status |
|---|---|
| Raw data outside the repository | **Implemented** — `.gitignore` excludes `data/` and `*.duckdb` wholesale |
| Aggregate-only publication | **Implemented** — §4 above |
| Single-operator access | **Implemented in effect** — the files exist on one workstation; no shared account, no server, no third-party analytics platform. **Considered and declined 2026-08-01:** relocating `data/` to the household network-attached storage volume, whose directory is shared inside the house, was evaluated and rejected. It would have falsified all three clauses above — adding a server, on a share, reachable by other household accounts — in exchange for removing a contractually bound processor, which is the wrong trade. Local full-volume encryption with the data resident on the workstation is the retained arrangement, and this row is the reason. **Enumerated 2026-08-01 rather than asserted** — one enabled local account of seven, one enabled administrator, no explicit SMB shares, Remote Desktop disabled, a private git remote with no data tracked, and the sync provider's devices and sessions reviewed clean. The two residuals, and why each is accepted rather than remediated, are recorded at gate B10c |
| No PII to hosted AI services | **A technical control for the shapes that can violate it, and practice for the rest — and this row previously overstated the position.** The research pipeline is unaffected and always was: the matcher is deterministic local code, every match-validation verdict is the author's, and the PII-bearing evidence file was rated outside any assistant. **What this row asserted too broadly is that no record had reached a hosted model at all.** On 2026-08-03 the `cure-list` and `chase-list` commands were found to print a preview block of individual voters — name, precinct and rejection reason — to standard output, which an agentic session returns verbatim; roughly 41 voter rows were transmitted across five runs. The operator's belief, and the reason it went unnoticed, was that the preview was a local terminal display. No paper figure derives from that tooling and no published output contains those rows, but the unqualified claim was false from 2026-08-03 and is corrected here rather than left to a later round. **Two layers now stand where the standing instruction stood alone.** The previews are withheld unless `--preview` is passed, and a `PreToolUse` hook refuses the dangerous command shapes at the session level — harness-executed, so it holds against intent rather than relying on it, which is the distinction this row is otherwise about. Both are locked in by `tests/test_infrastructure/test_person_level_stdout_guard.py`. The standing instruction added 2026-07-30 at both project and user scope remains for everything the hook cannot enumerate, and that residue is still practice. Review round 15 separately recorded a breach here on the strength of the paper's own wording; the author confirmed no AI adjudication ever occurred, and that entry is withdrawn — a different claim, and it stays withdrawn |
| NY full date of birth minimised | **Implemented 2026-07-30.** Day and month are generalised to 1 July of the birth year in the analytical copy — Washington's existing convention, since RCW 29A.08.710 releases year of birth only. Provably lossless: the analysis only ever read the year, because `date_diff('year', a, b)` returns the year difference rather than a completed age, and all twelve NY age-band figures are identical to six decimal places after the migration. `load_ny_voters.py` produces the generalised column, so a rebuild cannot reintroduce the exact date. The raw FOIL production remains in the restricted source enclave (`data/raw/`, digest recorded in the supplement) |
| Encryption at rest | **Implemented and verified 2026-07-30** from a `manage-bde -status` capture, re-confirmed 2026-08-01: volume C:, which holds the working tree and every database, reports Protection On, XTS-AES 128, 100% encrypted, with TPM and numerical-password key protectors. **The residual point recorded here on 2026-07-30 was overstated, and is corrected rather than quietly dropped.** It said that because the conversion is *Used Space Only*, the 52 prospect CSVs deleted in the 2026-07-29 purge could persist as **plaintext** in free space. They cannot. BitLocker encrypts on write, so only free space that predates *enablement* can hold plaintext — and the System log records a V2 TPM protector unlocking C: at the earliest boot it retains, **2026-03-12**, four and a half months before the purge. Those files were written and deleted under encryption; their remnants are ciphertext. Both logs are full and wrapping (BitLocker Management at its 1 MB cap; System 20 MB of 20 MB, oldest record 2026-03-11), so 2026-03-12 is a **floor** on how long the volume has been protected, not the enablement date — which is all this comparison needs. What remains is pre-enablement free space of unknown age, for which a wipe was run on 2026-08-01 as belt-and-braces. **It is not tracked further and nothing depends on it**, since the artifact that motivated the concern was never in the clear. **The former second residual point is withdrawn 2026-08-01:** external volume E: was styled a backup drive and recorded here as needing encryption before use, but it is a recovery-only device being removed from the system, so it is not the backup target and the question does not arise |
| Encrypted backups | **Partially implemented, and the scope is narrower than an earlier version of this row implied. Stated plainly here rather than left to inference.** The working tree syncs to a consumer cloud provider with a one-year version history, giving an off-site versioned copy of `data/raw/` — the irreplaceable part, including a voter file obtained by FOIL request. **Restricted source data is therefore held by a third party by deliberate decision, not by oversight.** The decision, taken 2026-08-01 and recorded so a reader need not reconstruct it: off-site survival of an irreplaceable FOIL production outweighs the custody cost of a provider holding it. **What the `*.duckdb` ignore rule does and does not do** is the part previously stated too broadly. It is a rule in the provider's `rules.dropboxignore` at the sync root; it correctly matches every `.duckdb` at any depth; and it keeps ~13 GB of *derived* data out of the sync path, which is a **file-locking and disk-space fix, not a disclosure control** — **but only for databases that were never uploaded, which is a qualification this row previously carried in one sentence and contradicted in another.** The rule does not stop the provider touching a file it had already synced, so those files kept being locked. That was not theoretical: on 2026-08-02 the test suite failed with `wa_statewide.duckdb` held open by the provider's client, and the client's own file-info dialog reported `wa_vrdb.duckdb` as "matches ignore rule *.duckdb but is still syncing — it was synced before the rule was added". The caveat and the benefit were both stated in this cell and were never read against each other. It does not reach `data/raw/` — the three raw voter productions — and it did not reach `data/validation/`, the PII-bearing evidence file and the `sample_id` → `state_voter_id` maps, which needed a rule of their own. And by the provider's own documentation the rule "will not apply to files already synced online", so any database uploaded before it took effect remained server-side, within one-year versioning, until manually removed there. **That removal took two passes, and saying so matters more than the tidy version.** The 2026-08-01 pass did not clear every database: on 2026-08-02 the provider still held `.duckdb` files, and they were removed from the cloud that day. Verified by mechanism rather than by the dialog alone — the test that had been failing on a provider file lock passed immediately afterwards. **The exposure this closed was small and is worth naming as small:** every database here is derived from `data/raw/`, which the provider holds by the deliberate decision recorded above, so removing the derived copies changed the file-locking behaviour and left the data custody position where it already was. The one non-equivalence, stated rather than glossed: `voter_donor_affiliation` is a pre-computed voter-to-donor linkage, and a join is a more sensitive artifact than its separable inputs — though with the matcher published and both inputs already provider-held, the difference is pre-computed versus reconstructible. Three things are named rather than glossed. The provider holds the encryption keys, so a third party holds restricted voter data at rest — and as of 2026-08-01 **there is no author-key-encrypted target and no candidate device**, external volume E: having been withdrawn as a recovery-only unit due off the system. That makes the provider copy the sole off-site copy rather than a redundant one, which is a disclosed limitation and not a pending step. **A restore has now been tested, 2026-08-01** — `vrdb/04.2026.WA/2025-2026_Voting_History.txt` pulled back from the provider's web interface and verified byte-identical (SHA-256 `ba9b28c5…eed901`, 185,678,211 bytes) against two independent references: a retained sibling copy unmodified since 2026-04-25, and a digest taken before the duplicate was deleted earlier that day. It establishes provider round-trip for a file **in** the sync path, and no more: not `*.duckdb` recovery, which the ignore rule excludes and the loaders can rebuild, and not version-history recovery of a long-deleted file. And `data/validation/` was **carved out of the sync path 2026-08-01** by a rule at the sync root, closing what this row previously listed as open — the reasoning is under *Retention* below, and it is that the class is regenerable, its ratings survive identifier-free in `docs/reference/`, and it is the only artifact here whose disclosure would retroactively de-anonymise already-published material |
| Retention | **Policy adopted 2026-08-01 — see *Retention* below.** No destruction date is set, and the reasoning for not setting one is stated rather than left as an omission: no source term requires one, and a fixed date would conflict with a longitudinal design. Retention is condition-based on a three-year review cycle, next due 2029-08-01. The one class carrying a short life is the PII-bearing validation evidence, tracked at §8 item 5 |
| Audit logging | **Not implemented, and accepted on the record 2026-07-30 rather than left open.** A per-file access log on a single-operator workstation with no shared account and no server would record one principal accessing their own files, which is not a control so much as a diary. The exposures it would detect — insider misuse and credential sharing — do not arise in this configuration, and the ones that do arise (device theft, provider compromise) are addressed by full-volume encryption and by what is excluded from sync. This row is a deliberate non-implementation with a stated reason, not an oversight |
| Incident response | **Not documented** |
| Human-rater confidentiality | **Informal.** The independent re-rating was performed on a blinded evidence extract; no written confidentiality undertaking was obtained, and §4's evidence file is PII-bearing |
| Confidential-address registrants | **Relies on the source.** Each state withholds protected addresses before release; no additional screen is applied here |

The four rows that remain unimplemented, informal, or dependent on the source are the substance
of what an external reviewer would ask about, and they are listed so the question is not left to
be discovered.

### Retention

**Adopted 2026-08-01, in place of the destruction dates this row previously said were owed.** No
provision of RCW 29A.08.720–.740, Idaho Code § 34-437A, N.Y. Election Law § 3-103(5), or
11 C.F.R. § 104.15 prescribes a retention period or a destruction deadline for a private
recipient, and none of the three voter-file productions was obtained under a use agreement
promising deletion. A fixed disposal date would therefore be an invention, and one that conflicts
with a longitudinal design whose value depends on holding successive extracts of the same rolls.
The policy is a condition and a review cycle instead:

> Identifiable source files and linked research records are retained for longitudinal electoral
> research for as long as they remain necessary for reproducibility, historical comparison, and
> lawful follow-on analysis. **Retention is reviewed every three years** — next review due
> 2029-08-01. Records are deleted when they are no longer required for those purposes, when
> continued possession would no longer be lawful under the applicable source terms, or when the
> project is permanently discontinued.

Retention classes differ, and the working extracts are the ones with a short life:

| class | treatment |
|---|---|
| Original voter-file productions (`data/raw/`) | Long-term restricted archive, with each production's use-restriction documentation retained alongside it — for Washington that is the `Washington Laws regarding use of VRDB data.pdf` shipped with the extract |
| Original campaign-finance files | Long-term archive, subject to the § 104.15 use restriction analysed in §2a |
| Linked voter–donor tables | Long-term, highest-security tier. Rebuildable from `data/raw/` by the loaders, so they are held for the cost of rebuilding rather than because they are irreplaceable |
| PII-bearing validation evidence and the `sample_id` → `state_voter_id` maps (`data/validation/`) | **Shortest life of anything here.** Deleted once the rating pass each one supports is signed off. The ratings themselves survive identifier-free in `docs/reference/`, so deletion loses no published result — which is what makes this class safe to delete and is the reason it should be. §8 item 5 tracks it |
| Published aggregate tables and figures | Retained permanently |

**What this does not claim.** A review cycle is a commitment to revisit, not a technical control.
Nothing in the workflow enforces the 2029 date; it is a diary entry, and following the
distinction this document draws elsewhere, it is recorded as one rather than as a control.

## 5. Risks considered

The risks divide in two, and the previous version of this section ran them together. **Risk in
the published papers is low. Risk in the linked research database is materially higher.** They
have different mitigations and deserve separate statements.

**In the papers.**

- **Re-identification from published aggregates.** Assessed as low. The smallest derivable cell
  is 25 after the suppression recorded in §4, and the published cuts (age band, party of record,
  county, dollar decile) are coarse.
- **What a reader can newly learn.** An earlier version said a reader learns "nothing from these
  papers that the source files do not already state publicly." That is not quite true and is
  withdrawn as stated. What the *papers* publish is aggregate. But the **linkage itself creates
  new combined information** that appears in no single public source: that a particular
  registrant and a particular contributor are probably the same person; that person's cumulative
  giving across committees and across two separately regulated money systems; giving joined to
  party of record; giving joined to turnout history; and a derived recipient-party
  classification. The papers report that combined information only in aggregate — but it exists,
  and the database that holds it is a genuinely new artifact rather than a view onto public
  files.

**In the research database.** Consequently the higher-risk surface is not publication but
holding: insider misuse, device compromise, loss of the workstation or the sync folder, and
onward use of the linked tables for a purpose this assessment does not cover. The mitigations
are the governance controls in §4 — including the five that are **not** implemented. This is the
part of the assessment most likely to be found wanting, and it is stated in those terms.
- **Attribution of a party to a person.** The papers report party *of record* — a datum the
  state publishes about that person — never an inferred or imputed party for an individual.
  Party is imputed only for *recipients* (committees), never for donors.
- **False attribution through linkage error.** The most consequential individual-level risk in
  this design, and the reason Appendix F exists. A household false merge attributes a
  relative's giving to the wrong person. Measured, quantified, and mitigated by adopting the
  key on which no false match was detected; the residual is that a true namesake is
  undetectable. No individual is named in any output, so the harm is to the accuracy of an
  aggregate rather than to a person's reputation.
- **Use of the research to target individuals.** Not a use these papers enable — they publish
  no lists. The consulting tooling produces voter *contact* lists for canvassing and GOTV under
  the state statutes' political-purpose permission. It no longer produces **donor solicitation**
  lists: those were removed on 29 July 2026 (§2a), because the political-purpose permission in a
  voter-file statute does not reach contributor information copied from a federal report. One
  derived signal does still cross from the donor layer into contact targeting — `donation_lean`
  contributes to a modelled voter preference score — and that is flagged in §8 rather than
  treated as settled.

## 6. Conflict of interest

The author is the principal of **Tikor Consulting**, a political consulting company whose work
is Democratic-oriented, and of **Kirby Law Office, PLLC**. The paper reports a finding — that
registered Democrats are over-represented among matched donors relative to registration — that a
skeptical reader could attribute to motivated reasoning.

**Analytical management of that conflict** is disclosure plus design, not assertion: the finding
is reported in both directions, replicated in states of opposite partisan control, reported as
*weaker* where the data make it weaker (New York's state panel), and accompanied by the
disclosure that the specification chosen on precision grounds discards a less-Democratic set of
donors.

**Financial and operational disclosure**, which the analytical safeguards do not substitute for.
Each of the following must be answered explicitly before signature, and left answered in the
submitted declaration rather than implied:

| question | answer |
|---|---|
| Did Tikor, any client, or any other party fund data acquisition, computing, or author time for this research? | No |
| Did any campaign, committee, or political client review the analysis or any draft before publication? | No |
| Have the matched donor–voter records been used commercially, and will they be? | No |
| Were any of these findings developed for, or at the request of, a client? | No |
| Has the author, Tikor, or Kirby Law Office worked for any candidate or committee appearing in the finance data analysed here? | **Yes** — the author has been involved with the Conroy for Congress Committee (Carmela Conroy, Washington's 5th congressional district). See the note below |
| What is the precise nature of the author's political-consulting activity? | Acting as an agency encouraging candidates to advertise digitally |

**All six answered 2026-07-30.** Five are No. The fifth is Yes and is set out here rather than
left as a one-word entry, because it is the disclosure a reviewer of this paper most needs.

**The affirmative answer, and what can and cannot be said about its reach.** The author has been
involved with the Conroy for Congress Committee — Carmela Conroy, a candidate in Washington's 5th
congressional district. She appears in this project's `candidate_finance` table for the 2024 and
2026 cycles and in `independent_expenditures`; both feed the **forecasting** product rather than
this paper.

Whether her committee's itemized receipts sit inside the contribution layer this paper analyses
**cannot be established from that layer**, and the reason is worth stating precisely because the
naive reading points the wrong way. No contributions in the Washington federal layer are
attributed to her candidate identifier — but none are attributed to **any** 5th-district House
candidate, so the zero is an artifact of how committee-to-candidate attribution populates in the
bulk load, not evidence that her donors are absent from the panel. Some of them are very likely
in it, as donors to other recipients.

**What limits the conflict is structural rather than evidentiary.** This paper names no
contributor, reports only aggregates, and computes nothing at the level of a candidate,
committee or race. Its findings are compositional — the age, party, turnout and concentration
profile of matched donors measured against registration — and no single committee's receipts can
move them. The forecasting product, where a specific candidate's finances do matter, is a
separate artifact and is not what this assessment covers.

An unanswered row would be visible; a glossed one would not. Neither applies now, but the
principle stood while they were open.

## 7. What would change this determination

- A finding that any of the three voter files' terms of release prohibit research use, or
  require a use agreement not obtained. *Now checked for all three — Washington in §2, New York
  and Idaho in §2b.*
- A determination that § 104.15(c)'s safe harbour does not reach this publication, or that any
  FEC contributor use in a commercially sold report is a "commercial purpose" independent of
  solicitation (§2a, §8).
- Any output containing an individual-level record, or a cell small enough to isolate a
  person.
- Any contact with, or targeting of, an individual on the basis of a research-derived
  inference.
- A journal or funder requiring institutional review, in which case this document is an input
  and not a conclusion.

## 8. Open items before this is signed

**Author decision, 2026-07-29: an external determination is not being sought at this stage.** It
will be pursued if a journal asks for one. Until then the position disclosed everywhere in this
package is the one stated in §3 — the project is unaffiliated, unfunded and not conducted under
any institution's Federalwide Assurance, so no institutional requirement has attached and none
has reviewed it; the author's assessment is that the work falls outside Common Rule coverage on
that basis and is not human-subjects research; and it does **not** claim the secondary-research
exemption at 45 CFR 46.104(d)(4), because that provision's de-identified-recording limb is not
satisfied by a project that retains identifiers.

**The risk this leaves is real and is recorded rather than argued away.** The target journal's
instructions require the reviewing committee to be named or an express statement that approval
was not required. An express statement is available and is what the title page carries. Whether
an editor accepts it in place of a named body is not within the author's control, so a
revise-for-compliance request is a foreseeable outcome and the determination may have to be
obtained then. Nothing in the analysis changes if it is: the route recommended in the release
checklist is a *not-human-subjects-research* determination, which is a review of the design as
already described, not a redesign.

Remaining items before signature, unchanged:

1. **Obtain an independent determination.** Previously listed third and hedged with a prediction
   that an IRB service "would most likely" agree with §3. **That prediction is withdrawn** — it
   is exactly the kind of self-serving forecast §0 says an unaffiliated researcher should not
   make. The target venue requires an ethical-approval statement naming the reviewing body, or an
   express statement that approval was not required. A commercial IRB or qualified
   research-ethics committee should be asked for one of: not human-subjects research; exempt
   secondary research; outside Common Rule coverage but ethically reviewed; or approval or waiver
   under an identified protocol. Until that letter exists, the question is **unresolved**, and
   this document says so rather than predicting the answer.
2. **Answer the §6 financial and operational disclosure rows.** They are blank on purpose.
3. **Close the remaining governance controls in §4**, or accept and record them. Of the five
   originally listed here, four are now closed or accepted on the record: NY full-DOB
   minimisation (2026-07-30), encryption at rest (verified 2026-07-30), audit logging (accepted
   with a stated reason 2026-07-30), and retention (condition-based policy adopted 2026-08-01,
   in place of the destruction dates this item used to ask for). **Backups remain partially
   implemented**, and the residue is not a missing step but a disclosed trade: a third party
   holds restricted source data by deliberate decision, and no restore has been tested.
4. **Resolve the two § 104.15 questions in §2a** — whether a paid brief falls inside
   § 104.15(c), and whether the surviving aggregate donor sections and the `donation_lean` signal
   are affected. These need counsel, not further self-assessment.
5. **Obtain a written confidentiality undertaking** from any future human rater, and set a
   destruction date for the PII-bearing validation evidence.
6. **Author signature and date.** This document is an assessment either way; signature records
   that the author adopts it.

---

*Prepared as part of the response to external review, and substantially revised on 2026-07-29
in response to a fourth round which found two material errors in it: the misapplied
secondary-research exemption (§3) and the federal contribution file recorded as unrestricted
(§1, §2a). The durable record of both is in
[`electoral-health-audit-log.md`](electoral-health-audit-log.md).*
