# New York Electorate — Five Party-Resolved Cuts

*Follow-on analyses, 2026-06-29, all from `scripts/diag_ny_electorate_extras.py`
against `data/ny_vrdb.duckdb` (voters, voter_participation) +
`data/ny_statewide.duckdb` (voter_donor_affiliation, forecast_predictions).
Companion to [`ny-turnout-by-party-age.md`](ny-turnout-by-party-age.md),
[`ny-donor-class-by-party.md`](ny-donor-class-by-party.md), and
[`donor-class-and-the-electorate.md`](donor-class-and-the-electorate.md).*

---

## 1. The unaffiliated "blank" bloc is young, disengaged, and donor-light

NY's 25% no-party enrollment is the recurring blind spot of registration-based
analysis. Characterized against the major parties (active roll):

| party | roll % | median age | %65+ | %18-29 | 2024 turnout | donors/1k |
|---|--:|--:|--:|--:|--:|--:|
| DEM | 47.7% | 49 | 26.7% | 17.3% | 58.4% | 33.0 |
| REP | 22.7% | 55 | 30.6% | 14.0% | **69.5%** | 23.6 |
| NOPARTY | 25.1% | **42** | 17.7% | **24.0%** | **50.4%** | **12.5** |

The unaffiliated bloc is the **youngest** (median 42 vs DEM 49, REP 55), the
**least likely to vote** (50.4% in a presidential year vs 69.5% for
Republicans), and the **least likely to donate** (12.5 matched federal donors
per 1,000 vs 33.0 for Democrats). It is not a bloc of high-information
independents holding the balance — it is a younger, more disengaged quarter of
the roll. (Republicans are the oldest and highest-turnout group.)

## 2. The donor class is more Democratic than the electorate in *every* competitiveness band

Mapping each matched donor to their congressional district's competitiveness
(from `forecast_predictions` |margin|):

| CD band | donors | %DEM | %REP | %NOPARTY | (registrant %DEM) |
|---|--:|--:|--:|--:|--:|
| Tossup (<5) | 17,878 | 57.7% | 23.5% | 14.6% | (40%) |
| Lean (5–10) | 16,467 | 45.9% | 32.6% | 16.3% | (31%) |
| Likely (10–20) | 68,341 | 41.7% | 38.8% | 14.8% | (33%) |
| Solid (20+) | **205,346** | 71.6% | 14.5% | 11.3% | (56%) |

Two findings: (1) the donor pool's %DEM **exceeds registration in every band**
(e.g. Solid: 71.6% donor vs 56% registrant; Tossup 57.7% vs 40%) — the donor
class is more Democratic than the electorate everywhere, not just in blue
districts. (2) **The overwhelming majority of donors live in Solid districts**
(205K of 308K, mostly Solid-D Manhattan), so campaign money originates in safe
seats and flows out — consistent with the cross-state finding that safe seats
*supply* most money even as competitive ones receive a premium.

## 3. The gray off-year electorate is behavior, not rolls — and most so for Republicans

Das-Gupta two-factor decomposition of the change in each party's 65+ electorate
share, 2024 presidential → 2025 off-year (rate = differential turnout;
composition = registration age structure):

| party | 65+ share (pres) | 65+ share (off) | observed change | RATE effect | COMP effect |
|---|--:|--:|--:|--:|--:|
| DEM | 29.0% | 32.1% | +3.2 | **+2.5** | +0.7 |
| REP | 32.7% | 42.8% | +10.2 | **+8.7** | +1.5 |
| NOPARTY | 22.4% | 30.6% | +8.2 | **+7.5** | +0.6 |

For every party the **rate effect dominates composition ~5–6×**: the off-year
electorate is older because the young *choose not to vote off-cycle*, not because
the rolls are differently composed. This is the institutional, on-cycle-timing-
fixable diagnosis — and it is **strongest for Republicans**, whose electorate
ages +10.2 points off-cycle (almost entirely behavior).

## 4. New registrants are abandoning party labels — a secular shift to "blank"

Party mix and age of each year's *new* registrants still on the roll:

| reg year | new regs | %DEM | %REP | %NOPARTY | median age at reg |
|---|--:|--:|--:|--:|--:|
| 2004 | 432,683 | 51.5% | 21.5% | 21.6% | 30 |
| 2008 | 559,590 | 57.8% | 16.2% | 20.7% | 29 |
| 2012 | 508,663 | 57.0% | 15.5% | 22.6% | 29 |
| 2016 | 785,520 | 51.5% | 18.5% | 25.6% | 30 |
| 2020 | 903,928 | 40.9% | 21.3% | 33.7% | 30 |
| 2024 | 893,119 | **39.7%** | 22.1% | **35.6%** | 29 |

The Democratic share of new registrants has fallen **~18 points** (57.8% in 2008
→ 39.7% in 2024) while the no-party share rose **~15 points** (20.7% → 35.6%);
Republican share is roughly flat. New entrants register at a stable ~29–30. The
unaffiliated bloc (§1) is not a legacy artifact — it is **growing through new
registration**, a leading indicator that the snapshot electorate understates.
(Caveat: survivorship — only registrants still on the current roll appear, so
older cohorts are thinned by moves/purges; read the *trend in party mix*, which
is composition-based, as the robust cut.)

## 5. Safe-seat New York, from registration alone

District counts by registration lean (DEM% − REP%, active roll):

**Congressional (26):** Safe D (D+40+) **9** · Likely D **3** · Lean D **7** ·
Competitive (<5) **4** · Lean/Likely R **3** · Safe R 0.

**Assembly (150):** Safe D **55** · Likely D **31** · Lean D **19** ·
Competitive (<5) **17** · Lean/Likely R **21** · Safe R **7**.

By registration alone, **only 4 of 26 congressional and 17 of 150 Assembly
districts (11%) are competitive**; 19/26 and 105/150 lean Democratic. This is the
registration-side corroboration of the observed safe-seat map
([`safe-seat-washington.md`](safe-seat-washington.md)): the general election is a
foregone conclusion in the large majority of NY districts, which (per
[`ny-turnout-by-party-age.md`](ny-turnout-by-party-age.md) §E) throws the real
decision to a small, enrollment-gated primary electorate.

---

## Reproduce

```
STATE=NY python scripts/diag_ny_electorate_extras.py
```

Caveats carried from the source memos: turnout *rates* use a current-roll
denominator (survivorship-biased for older cycles; composition shares are
robust); the donor match is a conservative name+ZIP proxy (a floor); CD
competitiveness is the model's predicted margin, not a certified result.
