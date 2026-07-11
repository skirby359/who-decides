# Who Decides New York?

### The off-year electorate, resolved by party — from 13.5 million individual registration and vote records

*Party-resolved companion to [`who-decides-washington.md`](who-decides-washington.md)
and [`who-decides-idaho.md`](who-decides-idaho.md) (the deep-red counterpart).
Washington showed the off-year electorate is **older**; New York publishes each
voter's **party enrollment**, so here we can ask the question Washington could
not — *whose* electorate ages, who is locked out, and where the real decision is
made. **DRAFT — pending the independent-verification gate in
[`publication-checklist.md`](publication-checklist.md).***

*Provenance. All figures from `data/ny_vrdb.duckdb` — New York's NYSVOTER
statewide file (13.54M registrants; individual party enrollment + full DOB +
per-event vote history, all ~100% populated) — via
`scripts/diag_ny_turnout_party.py`, `scripts/diag_ny_primary_participation.py`,
and `scripts/diag_ny_electorate_extras.py`. Competitiveness from
`forecast_predictions`. Each figure below traces to one of these scripts.*

*Load-bearing caveat. The file is the current (2026) roll, so voters who cast a
past ballot but were since purged/moved are absent. Composition **shares** are
robust; turnout **rates** are biased high for older cycles (and cross-party
comparison **within** a year is valid — the bias hits every group equally).
"NOPARTY" = New York's blank/no-party enrollment; its lean is never imputed.*

---

## The question

How *many* people vote is the wrong question for understanding how a state is
governed. The right one is *who* — and in New York the answer changes
dramatically with the calendar, because most local offices are filled in
odd-year Novembers and most legislative seats are settled in low-turnout closed
primaries. New York is the one large state that lets us answer "who" with the
variable that matters most: **individual party of record.**

The short answer: **the people who decide New York are older than the state, and
the gap is not partisan-neutral.** The off-year electorate is not a smaller copy
of the presidential one — it is older, its Republican wing ages hardest, a
quarter of registrants are structurally excluded from the contest that usually
decides, and the rolls are quietly shifting away from both parties.

---

## I. The off-year electorate is older — New York replicates Washington

Share of the general-election electorate by age band:

| Election | Type | 18–29 | 30–44 | 45–64 | 65+ | median |
|---|---|--:|--:|--:|--:|--:|
| Nov 2024 | Presidential | **14.1%** | 23.1% | 34.6% | 28.2% | 53 |
| Nov 2022 | Midterm | 9.8% | 21.1% | 38.5% | 30.6% | 56 |
| Nov 2025 | Off-year | 11.5% | 21.0% | 33.1% | 34.4% | 56 |
| Nov 2023 | Off-year | **6.0%** | 15.8% | 36.5% | **41.6%** | 61 |

As the contest shrinks (presidential → midterm → odd-year), the under-30 share
collapses (14% → 6% by 2023) and the 65+ share swells (28% → 42%); median age
rises from 53 to 61. **Behavior, not rolls.** A Das-Gupta decomposition of the
65+ share rise from 2024 to 2025 attributes it ~5–6× more to differential
**turnout** than to the registration age structure (rate effect +7.5 to +8.7 pts
vs composition +0.6 to +1.5, across parties) — the young *choose not to vote*
off-cycle. This is an institutional, on-cycle-timing-fixable pattern, not a
registration artifact.

---

## II. Now we can see party — and the Republican electorate ages hardest

This is the cut Washington's data cannot make. Share of each party's voters who
are 65+:

| Election | DEM | REP | NOPARTY | OTHER |
|---|--:|--:|--:|--:|
| Nov 2024 (pres) | 28.7% | 32.4% | 22.2% | 27.0% |
| Nov 2025 (odd) | 32.1% | **42.8%** | 30.6% | 35.1% |
| Nov 2023 (odd) | 41.6% | 43.5% | 39.3% | 37.4% |

Median age within each party tells the same story — in the 2025 off-year, the
**Republican median voter is 62 vs the Democratic 54**, an 8-year gap that was
only ~5 years in the presidential electorate. The GOP's 65+ share jumps from 32%
(presidential) to 43% (odd-year), and its under-30 participation collapses to
roughly a third of the presidential level. The off-year electorate is not just
older; **its Republican wing ages most.**

That New York's *Republican* wing ages hardest is itself a New York fact, not a
law of nature: the deep-red companion, [`who-decides-idaho.md`](who-decides-idaho.md),
finds the opposite structure — Idaho's Democratic and Republican electorates age
almost identically (65+ share 31.5% vs 31.7% in 2024), and the youth that drops
off in low-salience contests sits in the *unaffiliated* and minor-party blocs, not
in one major party. Whose electorate ages is contingent on the state; *that* the
low-salience electorate is older, and that the young who exit are the least
partisan, recurs in both.

But the *composition* heuristic that "older off-year electorate ⇒ more
Republican" **does not hold in deep-blue New York.** The DEM–REP share gap among
actual voters is event-driven, not turnout-driven — it swings from +15.6 (2023)
to +33.2 (2025) depending on what's on the ballot — and the unaffiliated, not
either party, are the ones who drop out (25.5% of the roll, but only 16–22% of
voters). And in even-year federal contests Republicans out-turn Democrats at
*every* age, yet that discipline inverts off-cycle: in the 2025 general, Democratic
under-30 turnout (30.8%) was nearly **double** Republican (15.9%). Party-resolved,
the signal lives in age structure and youth mobilization, not in a simple
rightward headcount shift.

---

## III. The unaffiliated quarter: young, disengaged, and locked out

A quarter of New York registrants (25.1% of the active roll) enroll in no party.
They are not high-information independents holding the balance:

| | median age | %65+ | %18–29 | 2024 turnout | donors / 1k |
|---|--:|--:|--:|--:|--:|
| DEM | 49 | 26.7% | 17.3% | 58.4% | 33.0 |
| REP | 55 | 30.6% | 14.0% | **69.5%** | 23.6 |
| NOPARTY | **42** | 17.7% | **24.0%** | **50.4%** | **12.5** |

The blank bloc is the **youngest, least likely to vote, and least likely to
donate** group in the state. And under New York's **closed** primaries they are
excluded by law from the contest that, in most of the state, *is* the election
(§V). A quarter of registrants have no voice at the nominating stage.

---

## IV. The nominating electorate is smaller still

New York settles most legislative seats in party primaries that only enrollees
may vote in. Participation rate by enrollment:

| Primary | DEM | REP | NOPARTY | OTHER |
|---|--:|--:|--:|--:|
| 2024 Presidential | 4.8% | 4.9% | 0.1% | 0.2% |
| 2024 State/Congress | 7.7% | 1.7% | 0.1% | 0.6% |
| 2022 State/Congress | 17.9% | 18.4% | 0.6% | 2.0% |
| 2021 (odd-year) | 16.9% | 5.0% | 0.5% | 1.5% |

Two facts: primary turnout runs from single digits to the high teens — the
electorate that *nominates* is a small fraction of the one that *elects* — and
the **25.3% enrolled "blank" are structurally absent** (≈0.1–0.6%, the residual
being nonpartisan/special races). In blue New York the **Democratic primary is
frequently the decisive contest** (2021 odd-year DEM 16.9% vs REP 5.0%; 2024
state DEM 7.7% vs REP 1.7%).

---

## V. Safe-seat New York — where the primary is the election

The reason the primary so often decides: by registration alone, most districts
are not competitive. District counts by registration lean (DEM% − REP%, active
roll):

| Level | Safe D (40+) | Likely D (20–40) | Lean D (5–20) | Competitive (<5) | Lean/Likely R | Safe R (20+) |
|---|--:|--:|--:|--:|--:|--:|
| Congressional (26) | 9 | 3 | 7 | **4** | 3 | 0 |
| Assembly (150) | 55 | 31 | 19 | **17** | 21 | 7 |

Only **4 of 26 congressional and 17 of 150 Assembly districts (11%) are
competitive** by registration; 19/26 and 105/150 lean Democratic. In the large
majority of New York, the November general is a foregone conclusion and the real
decision is thrown to the small, enrollment-gated primary electorate of §IV.

---

## VI. A leading indicator: new registrants are abandoning party labels

The blank bloc is not a legacy artifact — it is *growing through new
registration*. Party mix of each year's new registrants still on the roll:

| reg year | %DEM | %REP | %NOPARTY | median age at reg |
|---|--:|--:|--:|--:|
| 2008 | 57.8% | 16.2% | 20.7% | 29 |
| 2016 | 51.5% | 18.5% | 25.6% | 30 |
| 2020 | 40.9% | 21.3% | 33.7% | 30 |
| 2024 | **39.7%** | 22.1% | **35.6%** | 29 |

The Democratic share of new registrants has fallen ~18 points since 2008 while
the no-party share has risen ~15 points (Republican roughly flat). The
electorate that will decide future off-years is registering at a steady ~29–30
but is **increasingly choosing no party** — and, per §III–IV, that choice is
also a choice to sit out the nominating stage. (Survivorship caveat: only
registrants still on today's roll appear; read the *trend in party mix*, which is
composition-based, as the robust cut.)

---

## Boundary of inference

- **Turnout rates vs shares.** The current-roll denominator inflates turnout
  *rates* for older cycles; composition *shares* (§I–II) and within-year
  cross-party comparisons (§II–IV) are the robust cuts.
- **NOPARTY lean is never imputed.** The blank bloc's partisan sympathies are
  unobserved; we describe its age, turnout, and donation behavior, not its
  hidden preference (its federal *giving*, separately, leans ~2:1 Democratic —
  see [`ny-donor-class-by-party.md`](ny-donor-class-by-party.md)).
- **Vote-history formats.** NYSVOTER mixes ~6 county-specific history formats per
  election; the normalized parser is validated against known turnout (2024
  presidential ≈ 7.4M, the credible figure for the current roll).
- **Competitiveness (§V uses registration; the safe-seat paper uses observed
  margins).** Registration lean is a structural proxy, not a vote result; it
  corroborates the observed map rather than replacing it.

---

## What it means

New York lets us put a party label on every filter between the registered
population and the decision: an older general electorate, an older-still and
asymmetrically-Republican off-year electorate, a closed primary that excludes a
young, disengaged quarter of the state, and a district map on which that primary
is the real election almost everywhere. The reform implication is the same one
Washington's data pointed to — **move local elections on-cycle** — but New York
adds the evidence that the off-year distortion is not partisan-neutral and that
the unaffiliated, fastest-growing slice of the electorate is precisely the slice
most excluded by the current calendar and primary structure. Combined with the
donor-class paper, the picture is a series of narrowing, increasingly
unrepresentative gates — who registers, who votes, who votes in the primary, and
who pays.

---

## Methods & reproducibility

```
python scripts/load_ny_voters.py                        # NYSVOTER FOIL -> ny_vrdb.duckdb
python scripts/diag_ny_turnout_party.py --rebuild       # turnout by age x party (I, II)
STATE=NY python scripts/diag_ny_primary_participation.py # closed-primary participation (IV)
STATE=NY python scripts/diag_ny_electorate_extras.py     # blank bloc / decomposition / trend / safe-seat (II-VI)
```

All inputs are public records (NY NYSVOTER under its lawful-use FOIL terms). See
[`data-sources-and-reproducibility.md`](data-sources-and-reproducibility.md) for
the source ledger and method notes, and
[`ny-turnout-by-party-age.md`](ny-turnout-by-party-age.md) /
[`ny-electorate-extras.md`](ny-electorate-extras.md) for the full underlying
tables.
