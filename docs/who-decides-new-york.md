# Who Decides New York?

### The off-year electorate, resolved by party — from 13.5 million individual registration and vote records

**Stephen Kirby** · Tikor Consulting · July 2026

*AI-assisted drafting and analysis review. All figures are reproducible from
public-record data available through lawful request and from the open-source scripts
cited below, including `scripts/verify_who_decides_ny.py`. The paper source, code, and
data-acquisition recipe are public at <https://github.com/skirby359/who-decides>; the
underlying voter file is not redistributed. Contact: kirby@tikorconsulting.com.*

*Party-resolved companion to [`who-decides-washington.md`](who-decides-washington.md)
and [`who-decides-idaho.md`](who-decides-idaho.md) (the deep-red counterpart).
Washington showed the off-year electorate is **older**; New York publishes each
voter's **party enrollment**, so here we can ask the question Washington could
not — *whose* electorate ages, who is locked out, and where the real decision is
made. **DRAFT — pending human/editorial sign-off. `scripts/verify_who_decides_ny.py` scrapes
this paper and asserts every figure below against the voter file; see
[`electoral-health-audit-log.md`](electoral-health-audit-log.md).***

*An earlier version of this line said the paper had been verified because "all `verify_*`
scripts re-run, exit 0". That was worth nothing: until 2026-08-01 this paper's verifier had
no assertions and no failing exit path, so it printed values for a human to compare and
returned 0 whatever the data said. When it was converted to assert, §II and §III did not
reproduce and have been recomputed — see the note under §III.*

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

The short answer: **the people who decide New York are older than the state, the
graying is not partisan-neutral, and a quarter of registrants are shut out of the
contest that usually decides.** That the off-year electorate is older replicates a
sixty-year-old literature and is established here in **Appendix A**, where it belongs.
What New York's party of record adds — and what no survey-based design has shown at this
scale — is that the graying falls hardest on *one party's* electorate, that the bloc it
excludes is the youngest and least engaged in the state, and that the rolls are shifting
toward exactly that bloc.

---

## I. The graying is not partisan-neutral — the Republican electorate ages hardest

This is the cut Washington's data cannot make, and it is this paper's contribution.
Appendix A establishes the premise the off-cycle literature already predicts: as salience
falls, the electorate ages. The question that premise leaves open is *whose* electorate
ages — and the answer is not symmetric. Share of each party's voters who
are 65+:

| Election | DEM | REP | NOPARTY | OTHER |
|---|--:|--:|--:|--:|
| Nov 2024 (pres) | 28.7% | 32.4% | 22.2% | 27.0% |
| Nov 2025 (odd) | 32.1% | **42.8%** | 30.6% | 35.1% |
| Nov 2023 (odd) | 41.6% | 43.5% | 39.3% | 37.4% |

<sub>Shares are of each party's actual voters. The Das-Gupta decomposition in
[`ny-electorate-extras.md`](ny-electorate-extras.md) §3 uses all-roll-matched bases for the
2024 presidential row (DEM 29.0 / REP 32.7 / NOPARTY 22.4), ~0.3pp higher.</sub>

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

## II. The unaffiliated quarter: young, disengaged, and locked out

A quarter of New York registrants (25.3% of the active roll; 25.5% of the full roll) enroll in no party.
They are not high-information independents holding the balance:

| | median age | %65+ | %18–29 | 2024 turnout | donors / 1k |
|---|--:|--:|--:|--:|--:|
| DEM | 49 | 26.5% | 18.0% | 57.8% | 55.3 |
| REP | 55 | 30.4% | 14.9% | **68.7%** | 48.5 |
| NOPARTY | **42** | 17.4% | **25.6%** | **49.3%** | **22.7** |

The blank bloc is the **youngest, least likely to vote, and least likely to
donate** group in the state. And under New York's **closed** primaries they are
excluded by law from the contest that, in most of the state, *is* the election
(§IV). A quarter of registrants have no voice at the nominating stage.

---

## III. The nominating electorate is smaller still

New York settles most legislative seats in party primaries that only enrollees
may vote in. Participation rate by enrollment:

| Primary | DEM | REP | NOPARTY | OTHER |
|---|--:|--:|--:|--:|
| 2024 Presidential | 4.4% | 4.5% | 0.1% | 0.2% |
| 2024 State/Congress | 7.0% | 1.6% | 0.1% | 0.6% |
| 2022 State/Congress | 15.6% | 16.0% | 0.5% | 1.9% |
| 2021 (odd-year) | 14.3% | 4.2% | 0.4% | 1.4% |

Two facts: primary turnout runs from single digits to the high teens — the
electorate that *nominates* is a small fraction of the one that *elects* — and
the **25.3% enrolled "blank" are structurally absent** (≈0.1–0.5%, the residual
being nonpartisan/special races). In blue New York the **Democratic primary is
frequently the decisive contest** (2021 odd-year DEM 14.3% vs REP 4.2%; 2024
state DEM 7.0% vs REP 1.6%).

> **§II and §III were recomputed on 2026-08-01, and the reason is worth stating.** Both
> tables are **roll-denominated** — a rate or a share whose denominator is the registration
> file — and the file has grown since they were first written. Recent registrants are 39.7%
> Democratic and 35.6% unaffiliated against a roll at 47.6% and 25.3% (§V), they are
> younger, and none of them voted in 2024, so a larger roll mechanically lowers every
> participation rate and raises every youth share. Every deviation ran that way. Appendix A
> and Section I are **electorate**-denominated — the set of people who actually voted in a past
> election cannot change when new registrants arrive — and every one of their thirty-nine
> cells reproduced unchanged, which is what identifies the denominator as the cause.
>
> Direction and size: turnout rates fell 0.6–1.1 points, youth shares rose 0.7–1.6, and the
> primary-participation rates fell most in 2021 and 2022 (16.9 → 14.3 and 17.9 → 15.6),
> which are the oldest cycles and therefore the ones with the most subsequent registration
> behind them. **No finding changes.** The blank bloc is still the youngest, least
> participating and least donating group by a wide margin; the Democratic primary is still
> the decisive contest; the ordering within every column is unchanged.
>
> The donors-per-thousand column moved for a second and unrelated reason: it was still built
> on the pre-2026-07-27 New York match (308,032 voters) rather than the full-name-key
> specification now used throughout the series (558,017). It is rebuilt on the current panel
> here. That change raises all three figures and leaves their ordering and the ratio between
> them substantially intact.
>
> **The roll is now pinned, so this cannot recur silently.** New York had no snapshot on the
> reasoning that a static FOIL extract cannot move; it moved, and a reload is invisible to a
> paper that names no snapshot. `scripts/pin_ny_roll.py` freezes it the way Washington's is:
> **`ny_paper_roll`, taken 2026-08-01 at 13,540,505 registrants, of whom 12,448,034 are
> active.** Every roll-denominated figure in §II and §III is computed against that snapshot,
> and `scripts/verify_who_decides_ny.py` fails rather than falling back if it is absent.
> Appendix A and Section I continue to read the file directly, correctly: an electorate is a set of
> people who already voted, and it does not move. Re-pinning requires an explicit `--force`.
>
> Pinning changed no figure — all 96 asserted values reproduced against the snapshot on the
> day it was taken, which is the check that distinguishes freezing a number from altering one.
>
> One data-quality note the pin surfaced, disclosed because it is checkable: the NYSVOTER
> extract carries **53 registration identifiers twice** (36 of them among active registrants),
> and these are not duplicate copies — 8 of the pairs disagree on party, 25 on congressional
> district, 1 on birth year. The snapshot keeps one record per identifier, chosen
> deterministically, so it holds 13,540,505 registrants against the file's 13,540,558 rows.
> The difference is four orders of magnitude below anything this paper prints and moves no
> figure in it; it is reported rather than absorbed because a roll ought to be one row per
> registrant and the raw file is not.

---

## IV. Safe-seat New York — where the primary is the election

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
decision is thrown to the small, enrollment-gated primary electorate of §III.

---

## V. A leading indicator: new registrants are abandoning party labels

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
but is **increasingly choosing no party** — and, per §II–III, that choice is
also a choice to sit out the nominating stage. (Survivorship caveat: only
registrants still on today's roll appear; read the *trend in party mix*, which is
composition-based, as the robust cut.)

---

## Boundary of inference

- **Turnout rates vs shares.** The current-roll denominator inflates turnout
  *rates* for older cycles; composition *shares* (Appendix A and §I) and within-year
  cross-party comparisons (§I–§III) are the robust cuts. An independent
  reproduction of the §II turnout and §III primary figures runs about **1–2
  points under** the rate values reported here — the expected sensitivity to
  the choice of denominator (current roll vs. contemporaneous roll), not a
  discrepancy in the underlying counts. The direction and ordering are
  identical, and the **composition shares — the cuts this paper's argument
  rests on — reproduce exactly**. Read the rate figures as directional, with
  the shares carrying the inference.
- **NOPARTY lean is never imputed.** The blank bloc's partisan sympathies are
  unobserved; we describe its age, turnout, and donation behavior, not its
  hidden preference (its federal *giving*, separately, leans ~2:1 Democratic —
  see [`donor-class-and-the-electorate.md` Finding 3](donor-class-and-the-electorate.md)).
- **Vote-history formats.** NYSVOTER mixes ~6 county-specific history formats per
  election; the normalized parser is validated against known turnout (2024
  presidential ≈ 7.4M, the credible figure for the current roll).
- **Competitiveness (§IV uses registration; the safe-seat paper uses observed
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

## Related work

This paper's mechanisms are established; the contribution is the party-resolved,
individual-record measurement on 13.5M New York registration and vote records, and
the finding that the Republican electorate ages hardest. It sits in these literatures:

- **Turnout composition by salience (surge-and-decline).** Campbell, "Surge and
  Decline" (1960); Wolfinger & Rosenstone, *Who Votes?* (1980); Leighley & Nagler,
  *Who Votes Now?* (2013). Appendix A's presidential→off-year age gradient is this,
  measured directly. Plutzer, "Becoming a Habitual Voter" (2002) frames the young-adult
  drop-off in Appendix A.
- **Off-cycle election timing, composition, and representation.** Anzia, *Timing and
  Turnout* (2014); Hajnal & Trounstine, "Where Turnout Matters" (2005); Hajnal, Kogan
  & Markarian, "Who Votes: City Election Timing and Voter Composition" (2022); Einstein
  et al., "The Gray Vote" (2024) — the closest analog to the age result. Motivates the
  on-cycle remedy.
- **The primary as the real election under one-party dominance.** V.O. Key, *Southern
  Politics in State and Nation* (1949); Hirano & Snyder, *Primary Elections in the
  United States* (2019). Section IV's safe-seat map is a modern, party-resolved instance.
- **Primary-electorate representativeness (the tension).** Sides, Tausanovitch, Vavreck
  & Warshaw, "On the Representativeness of Primary Electorates" (2020) — distinguished
  here: our claim is composition and closure (Section III), not ideological extremism.
- **Independents / the unaffiliated.** Klar & Krupnikov, *Independent Politics* (2016);
  Fiorina, "The (Re)Nationalization of Congressional Elections" and the broader
  dealignment literature — the frame for the young, disengaged, locked-out unaffiliated
  quarter (Section II) and the new-registrant abandonment of party labels (Section V).
- **Voter-file / individual-level method.** Ansolabehere & Hersh, "Validation: What Big
  Data Reveal About Survey Misreporting and the Real Electorate" (2012); Hersh, *Hacking
  the Electorate* (2015). On the current-roll survivorship caveat (Boundary of
  inference): Feder & Miller, "The Racial Burden of Voter List Maintenance Errors,"
  *Science Advances* (2020).

---

## Methods & reproducibility

```
python scripts/load_ny_voters.py                        # NYSVOTER FOIL -> ny_vrdb.duckdb
python scripts/diag_ny_turnout_party.py --rebuild       # turnout by age x party (App. A, I)
STATE=NY python scripts/diag_ny_primary_participation.py # closed-primary participation (II)
STATE=NY python scripts/diag_ny_electorate_extras.py     # blank bloc / decomposition / trend / safe-seat (I-V, App. A)
```

All inputs are public records (NY NYSVOTER under its lawful-use FOIL terms). See
[`data-sources-and-reproducibility.md`](data-sources-and-reproducibility.md) for
the source ledger and method notes, and
[`ny-turnout-by-party-age.md`](ny-turnout-by-party-age.md) /
[`ny-electorate-extras.md`](ny-electorate-extras.md) for the full underlying
tables.

---

## Appendix A — Validation: the off-year electorate is older

**This is a replication, and it is placed here for that reason.** That the electorate ages
as salience falls has been established since Campbell (1960) and measured for local
elections by Anzia (2014); New York adds scale and individual records, not a new claim. The
paper's contribution begins at Section I, which asks the question this literature leaves
open — *whose* electorate ages. This appendix exists so that premise is measured rather
than assumed, and so a reader can check it against the sources in Related work.

Share of the general-election electorate by age band:

| Election | Type | 18–29 | 30–44 | 45–64 | 65+ | median |
|---|---|--:|--:|--:|--:|--:|
| Nov 2024 | Presidential | **14.1%** | 23.1% | 34.6% | 28.2% | 53 |
| Nov 2022 | Midterm | 9.8% | 21.1% | 38.5% | 30.6% | 56 |
| Nov 2025 | Off-year | 11.5% | 21.0% | 33.1% | 34.4% | 56 |
| Nov 2023 | Off-year | **6.0%** | 15.9% | 36.5% | **41.6%** | 61 |

As the contest shrinks (presidential → midterm → odd-year), the under-30 share
collapses (14% → 6% by 2023) and the 65+ share swells (28% → 42%); median age
rises from 53 to 61. **Behavior, not rolls.** A Das-Gupta decomposition of the
65+ share rise from 2024 to 2025 attributes it several times more to differential
**turnout** than to the registration age structure (rate effect **+2.5 to +8.7 pts**
vs composition +0.6 to +1.5, depending on party — a 3.6× ratio for Democrats up to
12.5× for the unaffiliated) — the young *choose not to vote*
off-cycle. This is an institutional, on-cycle-timing-fixable pattern, not a
registration artifact.

Like Section I, this table is **electorate**-denominated: it describes the set of people who
actually cast a ballot in a past election, which cannot change when new registrants are
added to the roll. That is why all of its cells reproduced unchanged through the
2026-08-01 recomputation that moved Sections II and III — see the note under Section III.

---

## Appendix B — Section numbering, before and after 2026-08-06

The paper was reordered on 2026-08-06 to open on its party-resolved result rather than on
its replication. **Only the order and the numbering changed; no figure, table cell, or claim
was altered by the reordering.** This map is recorded because earlier documents in this
series — including the append-only
[`electoral-health-audit-log.md`](electoral-health-audit-log.md) — cite these sections by
number, and a silent renumbering would re-point those citations at different content.

| Before | After | Content |
|---|---|---|
| §I | **Appendix A** | The off-year electorate is older (replication / validation) |
| §II | **§I** | The graying is not partisan-neutral |
| §III | **§II** | The unaffiliated quarter |
| §IV | **§III** | The nominating electorate |
| §V | **§IV** | Safe-seat New York |
| §VI | **§V** | New registrants abandoning party labels |

So a pre-2026-08-06 reference to "NY §III/§IV" — the roll-denominated blocks recomputed on
2026-08-01 — is a reference to what are now **§II and §III**.
