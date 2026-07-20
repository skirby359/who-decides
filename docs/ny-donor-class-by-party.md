# New York: The Donor Class vs the Electorate — by Party-of-Record and Age

*Party-resolved donor-class analysis, 2026-06-29. The NY counterpart of the WA
§F donor findings (donor-class ≠ electorate; whale concentration). New York's
individual **party enrollment** lets us ask which registered voters become
federal donors, and how that donor class compares to the people who actually
vote.*

**Method.** Reuses the production WA matcher `match_voters_to_donors` (4 tiers,
strictest first: full-name+zip5 / first-initial+middle+zip5 / first-initial+zip5
/ zip3+middle, each with a per-key uniqueness guard so siblings aren't
mis-merged) — pointed at NY:
- voters: `data/ny_vrdb.duckdb` `voters` (12.45M **active**; party + DOB),
- donors: `data/ny_statewide.duckdb` `individual_contributions` (10.02M FEC
  itemized individual rows, cycles 2018–2026),
- output: `voter_donor_affiliation`.

**Reproduce.**
```
STATE=NY python scripts/match_ny_voters_to_donors.py
```

**Match result.** **308,032** registered NY voters matched to **6,311,939**
contributions. Tier mix: full-name+zip5 **269,396** (87%, the dominant tier, as
in WA), zip5 29,302, zip3+middle 5,432, zip5+middle 3,902.

**Scope caveats.** (1) Federal **itemized** donors only (sub-$200 unitemized
giving is invisible; state/local PDC-equivalent giving not included). (2)
**Active**-roll voters only (matches WA methodology for cross-state
comparability). (3) Conservative name+zip join — a floor, not a census, of the
donor population. (4) §1–§3 use the donor's **own NY party enrollment** (100%
present); the recipient-lean cut (§4) covers the **79%** of contributions whose
recipient party is resolved (see backfill note below).

**Recipient-party backfill (2026-06-29).** `individual_contributions
.fec_candidate_id` holds the recipient **committee** id (e.g. C00211318), and NY
had no committee→party map (`candidate_finance.party` ~96% Unknown,
`committee_party_override` empty). `scripts/backfill_ny_committee_party.py` runs
the bulk FEC **Committee Master** loader (`load_fec_committee_master`,
`cm{yy}.zip` per cycle → committee-id-keyed `candidate_finance` rows) + the
conduit-PAC overrides, then resolves remaining candidate committees via the
candidate master (`cn{yy}.zip`, committee→candidate→party). D/R-resolved
contribution share went **0.5% → 79.0%**. The unresolved 21% are
genuinely-nonpartisan / unaffiliated PACs.

---

## 1. The donor class is disproportionately Democratic — and the unaffiliated are nearly absent

Share of matched donors and matched dollars by the donor's **own** NY enrollment,
vs the registration baseline:

| party | donors | donor share | registration | **skew** | $ (matched) | $ share |
|---|---:|---:|---:|---:|---:|---:|
| DEM | 193,355 | 62.8% | 47.8% | **+15.0** | $849.2M | 71.0% |
| REP | 65,898 | 21.4% | 22.3% | −0.9 | $197.2M | 16.5% |
| NOPARTY (blank) | 38,601 | 12.5% | 25.5% | **−13.0** | $126.8M | 10.6% |
| OTHER (minor) | 10,178 | 3.3% | 4.4% | −1.1 | $22.8M | 1.9% |

**Finding.** The federal donor class over-represents registered Democrats
(+15 pts vs their share of the roll) and **severely under-represents the
unaffiliated** — NY's "blank" enrollees are a quarter of all registrants but
only an eighth of donors (−13 pts). Republicans donate roughly in proportion to
their registration. Democrats supply **71% of matched dollars**. The donor class
is not a scaled-down electorate; it is a partisan-skewed slice of it — and the
skew runs *against* the largest non-partisan bloc.

## 2. The donor class is far older than even the (already-gray) electorate

Age-band share (age as of 2024-11-05) among matched donors vs all active voters
vs 2024 general-election voters:

| age band | matched donors | all active voters | 2024 GE voters |
|---|---:|---:|---:|
| 18-29 | **3.0%** | 18.0% | 14.1% |
| 30-44 | 14.2% | 25.6% | 23.1% |
| 45-64 | 34.9% | 31.2% | 34.6% |
| 65+ | **47.9%** | 25.2% | 28.2% |

**Finding.** Donors skew dramatically old: **nearly half (48%) of matched donors
are 65+**, versus 25% of the active roll and 28% of 2024 voters; under-30s are
3% of donors versus 14–18% elsewhere. The donor class is older than the off-year
electorate that the turnout study already flagged as gray — a *second*,
compounding age distortion layered on top of who turns out.

*Match-bias validation (`scripts/diag_ny_match_bias.py`).* The skew is **not** a
matching artifact. P(matchable) — the share of active voters whose Tier-0 key
(last, full first, zip5) is unique on the roll — is **94.5–95.4% across every
age band** (0.9-pt spread). Re-weighting the donor age distribution by
1/P(matchable) moves the 65+ share by **0.0 pts** (47.9% → 47.9%). Older voters
are not meaningfully more matchable, so the donor age skew is genuine —
replicating the WA §F result.

## 3. Whale concentration — replicates WA almost exactly

Among matched NY donors:
- **top 1% of donors = 51.2% of matched dollars**
- **top 10% of donors = 81.2% of matched dollars**

This tracks the WA finding (top 1% ≈ 47.7% of matched $) — donor money is
whale-dominated to nearly the same degree in a much larger, bluer state,
suggesting the concentration is structural to federal small-vs-large-dollar
giving rather than state-specific.

## 4. Where the money goes — recipient lean and crossover

Among matched donors whose recipient party is resolved, the share of each
**own-party** group's donations going to Democratic vs Republican recipients:

| own party | donors (resolved) | → Democratic | → Republican | mixed |
|---|---:|---:|---:|---:|
| DEM | 174,330 | **94.2%** | 3.9% | 1.9% |
| REP | 57,342 | 14.2% | **82.6%** | 3.2% |
| NOPARTY (blank) | 30,590 | **65.5%** | 31.0% | 3.5% |
| OTHER (minor) | 8,274 | 40.7% | 57.0% | 2.3% |

**Findings.** (1) Registered Democrats are near-monolithic givers (94% to D);
registered Republicans are loyal but leakier (83% to R) — **registered
Republicans fund Democrats at ~3.6× the rate Democrats fund Republicans**
(14.2% vs 3.9%), consistent with a deep-blue donor ecosystem. (2) The
crucial unaffiliated bloc — invisible to registration-based targeting —
**leans ~2:1 Democratic in its giving** (65.5% → D), so NY's "blank" donors are
not centrist by behavior. (3) Minor-party (OTHER) registrants lean Republican
(57%), consistent with Conservative-line enrollment.

## Why this matters (electoral-health framing)

Combined with the turnout paper, NY now shows **two stacked filters** between the
registered population and political influence: (1) an older, party-asymmetric
*voting* electorate, and (2) an even older, more-Democratic, whale-concentrated
*donor* class from which the unaffiliated quarter of the state is largely
missing. Each is measured with individual party-of-record — the evidence WA
could not supply. This is the donor-class half of the party-resolved §F playbook.

**Open follow-ons:** (1) ~~recipient-party backfill~~ — **DONE** (§4; 79%
resolved via the bulk committee/candidate masters); (2) ~~match-bias
re-weighting~~ — **DONE** (§2 validation note; skew genuine, 0.0-pt shift); (3)
fold §1–§4 into the cross-state "Donor Class" paper (publication sequence #3).
