# Who Decides Idaho?

### The one-party electorate, resolved by party — from 1.03 million individual registration and vote records

*Deep-red companion to [`who-decides-washington.md`](who-decides-washington.md)
and [`who-decides-new-york.md`](who-decides-new-york.md). Washington showed the
off-year electorate is **older**; New York (deep blue) showed *whose* electorate
ages and who is locked out. Idaho completes the set from the other pole: a state
where the November general is a formality and the **closed Republican primary is
the real election** — so the question "who decides" has a sharper, more literal
answer than in any two-party state. **DRAFT — AI-side reproduction verified (all `verify_*`
scripts re-run, exit 0; see [`publication-checklist.md`](publication-checklist.md)); pending
human/editorial sign-off.***

*Provenance. All figures from `data/id_vrdb.duckdb` — Idaho's statewide voter
file with history (1,029,938 registrants; individual party affiliation + age +
per-election vote history incl. the primary ballot each voter pulled, all ~100%
populated) — via `scripts/diag_id_turnout_party.py` and
`scripts/diag_id_electorate_extras.py`. The donor layer joins Idaho Sunshine
state contributions via `scripts/match_id_voters_to_donors.py`. Competitiveness
from `forecast_predictions`. Each figure below traces to one of these scripts.*

*Load-bearing caveats. (1) The file is the current (2026) roll, which has shrunk to
1.03M from the ~1.18M registered at the 2024 election (Idaho purges aggressively and
same-day registrants churn). Voters who cast a past ballot but were since
purged/moved are absent, so any turnout **rate** computed from this file is biased
high — materially: an all-voter 2024 rate comes out near 94% against the official
77.8%. The bias is *larger* for high-churn groups (young, unaffiliated, movers), so
even within-year cross-group rate comparisons are unreliable. This paper therefore
reports **composition shares only** (who the electorate is), which need no
registration denominator, and reports no turnout rates. See Methods. (2) Idaho
publishes **age**, not date of birth; election-time age is
approximated as `age − (2026 − year)`, accurate to ~1 year — fine for bands, and
we never claim exact ages. (3) "UNAFF" = Idaho's unaffiliated registration; its
partisan lean is never imputed.*

---

## The question

How *many* people vote is the wrong question for understanding how a state is
governed. The right one is *who* — and in Idaho the answer is unusually stark,
because Idaho is a one-party state by registration (**63% Republican, 12%
Democratic, 24% unaffiliated**) whose officeholders are chosen not in November
but in a **closed May Republican primary** that most of the state cannot or does
not enter.

The short answer: **the people who actually decide Idaho are a gray, Republican,
self-selected slice of an already-Republican state.** In November the electorate
is broadly representative; in the primary that settles nearly every seat it is
older and drawn almost entirely from one party — and the 24% of
registrants who decline a party are, by the design of the closed primary,
standing outside the room where it happens.

Two of these findings are specific to Idaho, not a replication of the off-cycle
turnout literature. First, the age gap here is **party-neutral**: Idaho's
Republicans and Democrats are nearly the same age, and the young sit in the
*unaffiliated* bloc rather than in either party — inverting the national
"older-is-more-Republican" pattern and reversing what the New York companion found.
Second, because the file records the party ballot each voter actually pulled, the
exclusion of the unaffiliated from the decisive primary is **measured, not
inferred**.

---

## I. The off-year electorate is older — Idaho replicates Washington

Share of the general-election electorate by age band:

| Election | Type | 18–29 | 30–44 | 45–64 | 65+ | median |
|---|---|--:|--:|--:|--:|--:|
| Nov 2024 | Presidential | 15.2% | 23.4% | 32.4% | 29.0% | 52 |
| Nov 2022 | Midterm | **8.6%** | 20.7% | 36.3% | **34.4%** | 57 |
| Nov 2020 | Presidential | 13.8% | 23.9% | 36.1% | 26.3% | 52 |
| — | Registration baseline (2026) | 15.2% | 22.8% | 30.9% | 31.0% | 52 |

As the contest shrinks (presidential → midterm), the under-30 share nearly halves
(15.2% → 8.6%) and the 65+ share swells (29% → 34%); median age rises from 52 to
57. **Behavior, not rolls** — the roll's age structure barely moves between the two
elections, so the shift is who *shows up*, not who is registered. A Das-Gupta
decomposition points the same way (attributing the 65+ rise mostly to turnout
rather than to roll composition), though in Idaho that rate-based cut carries the
survivorship caveat above; it is reported here as directionally consistent with
Washington and New York, where the roll is stable and the decomposition is reliable.
The young *choose not to vote* in lower-salience cycles — the classic
**surge-and-decline** pattern (Campbell 1960), measured here across the
presidential-to-midterm drop. (That is distinct from, though it rhymes with, the
*off-cycle / odd-year local-election* timing literature — Anzia 2014; Hajnal &
Trounstine 2005 — which motivates the on-cycle remedy discussed below: Idaho's
local offices, like Washington's, sit off the federal calendar entirely.) As in
Washington and New York, this is an institutional, timing-fixable pattern, not a
registration artifact.

---

## II. In Idaho the age gap is *not* partisan — the youth is in the middle

This is where Idaho diverges sharply from New York. In New York the Republican
electorate ages hardest; in Idaho the two major parties age almost identically.
Share of each party's 2024 general-election voters by age, plus median age:

| Party | share 65+ | share 18–29 | median age |
|---|--:|--:|--:|
| Republican | 31.7% | 12.7% | 54 |
| Democratic | 31.5% | 19.4% | 50 |
| **Unaffiliated** | **21.3%** | **19.6%** | **46** |
| Other (Lib/Con) | 10.0% | 23.0% | 38 |

The Republican and Democratic electorates are within a fraction of a point on the
65+ share and only four years apart on median age. Idaho's **youth lives outside
the two major parties** — in the unaffiliated bloc (median 46) and the minor
parties (median 38). That matters because, as Sections III–IV show, those are
precisely the blocs that vanish from the contest that decides. The generational
sorting that makes "older = redder" a useful heuristic nationally simply does not
hold here: in Idaho, older = *more attached to a party at all*, not more
Republican.

---

## III. The unaffiliated quarter: turns out in November, locked out in May

Idaho's 245,887 unaffiliated registrants (23.9% of the roll) are the recurring
blind spot. Because Idaho's roll cannot support reliable turnout *rates* (Methods),
we follow each bloc by its **share of the electorate** — a denominator-free measure
— across the two contests:

| Bloc | roll % | median age | % 65+ | % 18–29 | share of 2024 **general** electorate | share of 2024 **primary** electorate |
|---|--:|--:|--:|--:|--:|--:|
| Republican | 62.9% | 55 | 34.5% | 12.6% | 64.5% | **85.2%** |
| Unaffiliated | 23.9% | 46 | 22.4% | 19.9% | 22.6% | **5.9%** |
| Democratic | 11.8% | 50 | 32.4% | 19.1% | 11.6% | 8.3% |
| Other | 1.4% | 40 | 11.0% | 21.3% | 1.3% | 0.6% |

The story is in the last two columns. The unaffiliated are **22.6% of the 2024
general electorate** — essentially their full 23.9% of the roll, so in November they
show up. But they are only **5.9% of the May primary electorate**: a bloc that is
nearly a quarter of the state, and a quarter of the November vote, casts about **one
in seventeen** primary ballots. This is not apathy; it is architecture. Idaho's
Republican primary is **closed**, so an unaffiliated voter must first affiliate to
vote in the contest that actually chooses the winner. A quarter of the state opts to
stay out — and in doing so sits out the decision.

> **A note on the roll itself.** Idaho's registration file shrank from **~1.18M** at
> the November 2024 election to **~1.03M** in this 2026 snapshot — roughly a **13%
> turnover in eighteen months**, from routine list maintenance (inactive-voter
> removal, change-of-address, deaths) compounded by the non-persistence of the
> 121,000 voters who registered same-day on Election Day 2024. That churn is the
> reason historical turnout *rates* cannot be reconstructed from a single snapshot
> (Methods) — but it is also a civic-health datapoint in its own right: a roll that
> turns over this quickly is a moving target for any list-based registration or
> mobilization effort, and it means "the electorate" is a substantially different set
> of people each cycle. Washington's file, by comparison, is markedly more stable.

## IV. The closed primary *is* the election — and its electorate is grayest of all

In a state where both congressional districts and all 35 legislative districts
lean Republican (Section V), the November general ratifies a choice the May
Republican primary has already made. Three facts make that literal.

**The primary electorate is far more Republican than November.** Party
composition of each contest, as R-minus-D margin:

| Contest | REP | DEM | UNAFF | R − D |
|---|--:|--:|--:|--:|
| Nov 2024 general | 64.5% | 11.6% | 22.6% | +52.9 |
| Nov 2022 general | 68.6% | 12.1% | 18.2% | +56.5 |
| **May 2024 primary** | **85.2%** | 8.3% | 5.9% | **+76.9** |
| **May 2022 primary** | **85.9%** | 8.2% | 5.3% | **+77.7** |
| — Registration baseline | 62.9% | 11.8% | 23.9% | +51.1 |

The unaffiliated share of the electorate falls from ~24% of the roll to roughly
**5–7%** of the primary; the R−D skew widens from ~+51 in November to ~+77 in the
primary. **80–86% of every primary ballot cast in Idaho is a Republican ballot.**

**But "the primary decides" only where the primary is *contested* — and often it
isn't.** Of the 105 legislative seats, **99 drew a Republican primary in 2024** (the other
six are safe-Democratic seats where no Republican filed); of those 99, just **52
(53%) were contested** and **47 (47%) had a single Republican on the ballot**
(`scripts/diag_id_primary_contested.py`, reconciled seat-by-seat against the
35-district / 105-seat frame — every race maps 1:1 to a seat, no duplicates; the
contested counts match Ballotpedia's independent tallies cycle-by-cycle, exact for
2022 and 2024 and within ±2 for 2016 and 2018). For roughly half of Republican-held
legislative seats, then, even the primary offered no choice — the seat was
effectively settled at candidate *filing*, an earlier and narrower gate than the
primary electorate itself. So the "decisive contest" is, for half the map, no
contest at all; for the other half it is the closed, gray, one-party electorate
described here.

**That contest is, however, growing.** Across the loaded cycles the Republican
legislative-primary contested rate has roughly *doubled* — **36% (2016) → 43%
(2018) → 68% (2022) → 53% (2024)** — peaking in 2022, the first post-redistricting
cycle and the height of the state GOP's traditional-vs-hardline fights. (2020 is
not comparable: the SoS published that mail-only cycle's legislative results at
county level only.) Two things are therefore true at once, and both matter: the
decisive Republican primary is *increasingly* a real choice for those who can vote
in it, even as it stays *closed* to the ~24% of registrants who are unaffiliated.
Democratic legislative primaries, by contrast, are almost never contested (2–14%
across these cycles) — the mirror image of one-party dominance.

**The primary electorate is older than even the Republican rolls.** Comparing all
Republican registrants to those who actually pulled a Republican ballot in 2024:

| Group | 18–29 | 30–44 | 45–64 | 65+ | median |
|---|--:|--:|--:|--:|--:|
| Republican registrants (all roll) | 12.6% | 20.4% | 32.5% | 34.5% | 55 |
| Republican-ballot primary voters, 2024 | **4.9%** | 14.2% | 34.2% | **46.7%** | **63** |

The people who nominate Idaho's officeholders are a gray subset of an already-red
party: **median age 63, nearly half of them 65+.**

**When the unaffiliated do vote in the primary, they pull the Democratic ballot —
and even that door is closing.** Ballot choice among unaffiliated primary voters:

| Primary | → REP | → DEM | → nonpartisan |
|---|--:|--:|--:|
| May 2022 | 27.7% | 52.6% | 19.0% |
| May 2024 | 9.7% | 52.5% | 37.5% |
| May 2026 | **1.7%** | **65.6%** | 32.6% |

Because the Republican primary is closed and the Democratic primary is open to
unaffiliated voters, the independents who do participate increasingly do so on the
Democratic side — the Republican-ballot share of unaffiliated voters fell from 28%
in 2022 to under 2% by 2026, tightening the one-party lock on the decisive contest.

---

## V. Safe-seat Idaho — there is no competitive district by registration

Districts by registration lean (Republican % − Democratic % of registrants):

| Level (n) | Safe R (R+40+) | Likely R (R+20–40) | Lean R (R+5–20) | Competitive | Any D lean |
|---|--:|--:|--:|--:|--:|
| Congressional (2) | **2** | 0 | 0 | 0 | 0 |
| Legislative (35) | **27** | 4 | 4 | **0** | **0** |

Both U.S. House seats and every one of the 35 legislative districts lean
Republican; **none is competitive by registration, and none leans Democratic.**
This is the starkest safe-seat map of the three states studied. Where the general
election cannot change an outcome, the closed primary of Section IV is not merely
*a* decisive contest — it is the *only* one.

---

## VI. A leading indicator: new registrants are younger and less Republican

Party mix and age of each registration cohort still on the current roll:

| First registered | new regs | % REP | % DEM | % UNAFF | median age at reg |
|---|--:|--:|--:|--:|--:|
| 2008 | 22,559 | 66.4% | 5.3% | 28.0% | 45 |
| 2012 | 30,843 | 71.5% | 11.8% | 15.9% | 47 |
| 2016 | 61,465 | 65.5% | 12.1% | 21.2% | 46 |
| 2020 | 153,710 | 60.8% | 12.2% | 25.1% | 43 |
| 2022 | 97,593 | 64.8% | 11.3% | 21.8% | 44 |
| 2024 | 263,315 | **57.5%** | 12.4% | **28.3%** | **35** |

Idaho's newest voters are markedly younger (median age at registration 35 vs
45–47 a decade earlier) and less Republican (57.5% vs the high-60s/low-70s of
earlier cohorts). But the dilution flows to **unaffiliated, not Democratic** — the
Democratic share is flat near 12% across two decades while the unaffiliated share
climbs to 28%. The rolls are slowly loosening the two-party grip, but toward the
bloc that Section III showed is structurally shut out of the primary. Absent a
change in primary rules, a growing, younger, unaffiliated electorate has *less*
say in who governs, not more.

---

## VII. The donor class is not the electorate — and leans against the rolls

Matching the roll to Idaho Sunshine state-campaign contributions links **27,250
registered voters to 131,466 donations ($15.9M)**. Characterized by the donor's
own party of record:

| Party | donors | donor share | reg share | skew | $ share |
|---|--:|--:|--:|--:|--:|
| Republican | 18,115 | 66.5% | 62.9% | +3.6 | 71.1% |
| Democratic | 5,685 | 20.9% | 11.8% | **+9.1** | 20.6% |
| Unaffiliated | 3,281 | 12.0% | 23.9% | **−11.9** | 8.0% |
| Other | 169 | 0.6% | 1.4% | −0.8 | 0.3% |

Even in a state this red, the donor class **over-represents registered Democrats**
— they are 12% of the roll but 21% of donors and give 21% of the money, nearly
double their registration weight — while the unaffiliated quarter is again nearly
absent (12% of donors, 8% of dollars). Republicans still supply the plurality of
money in absolute terms, as a 63%-Republican state must, but relative to their
numbers the *most* over-represented donors are Democrats.

The donor class is also **grayer and more concentrated** than the electorate:

- **Age.** 51% of matched donors are 65+, versus 31% of the roll and 33% of 2024
  general voters; the under-30 share is 2.6% versus 15% of the roll. The donor
  class is the oldest layer of all.
- **Concentration.** The top 1% of matched donors supply **39%** of the matched
  dollars; the top 10% supply **71%**.
- **Geography.** Ada County (Boise) alone accounts for **49%** of matched donor
  dollars — the money mirror of the population-vs-influence gap seen in New York
  (Manhattan) and Washington (Seattle).
- **Where the money sits.** Donor party mix tracks district safety: in Solid-R
  legislative districts (which hold the bulk of donors, ~22,000) donors are 71%
  Republican, but in the handful of more competitive districts the mix is far more
  balanced (~46% Republican / ~34% Democratic).

**Crossover — where the money goes.** Idaho Sunshine carries no party on the
recipient record, but recipient party can be reconstructed from data on hand (the
Secretary of State candidate roster plus party/committee name patterns), which
resolves the recipient for ~52% of matched donors and ~66% of candidate-directed
dollars (`scripts/backfill_id_recipient_party.py`). Among donors whose money
reached a party-resolvable recipient:

| Donor's registration | → gave only to D | → gave only to R | mixed |
|---|--:|--:|--:|
| Republican | 18.8% | 79.3% | 1.9% |
| Democratic | **93.5%** | 4.0% | 2.5% |
| Unaffiliated | **72.8%** | 24.5% | 2.7% |

Registered Democrats are near-monolithic donors (94% give only to Democrats — the
same loyalty seen in New York), and unaffiliated donors lean roughly **3:1
Democratic** when their money can be traced, echoing the blank-bloc donor lean in
New York. Republicans predominantly fund Republicans (79%); the apparent ~19%
giving only to Democrats is an **upper bound** — the unresolved recipient pool
(local Republican candidates and R-aligned PACs not in the roster) skews
Republican, so Republican donors' Republican-side giving is disproportionately the
part left untraced. The robust, direction-safe reads are the Democratic loyalty
and the unaffiliated Democratic tilt.

---

## Boundary of inference

- **Age is imputed from a single integer.** Idaho gives current age, not DOB, so
  election-time ages are ±1 year and we report only bands and medians, never exact
  ages. This cannot manufacture the effects shown — the primary/general and
  cohort gaps are far larger than a one-year imputation error.
- **Survivorship — why this paper reports no turnout rates.** The 2026 roll (1.03M)
  is smaller than the ~1.18M registered at the 2024 election, because Idaho purges
  inactive registrations and same-day registrants churn. Dividing past voters by this
  shrunken roll inflates every turnout rate: our all-voter 2024 general rate is ~94%
  against the official **77.8%** (917,608 ballots / 1,178,750 registered, Idaho SoS),
  and 2020 even computes above 100% — voters who re-registered after 2020 carry a
  later `registration_date`, dropping out of the denominator while staying in the
  numerator. The bias is not uniform (larger for the young, unaffiliated, and movers),
  so cross-group rate comparisons are unreliable too. We therefore report **composition
  shares** — each group's share of the actual electorate — throughout, which need no
  registration denominator.
- **The survivorship bias runs *against* the gray finding.** Comparing Washington's
  2023 and 2026 roll snapshots, the voters who leave the rolls skew *older* (33% are
  65+ vs 24% of those retained — deaths dominate). Reconstructing a past electorate
  from the current roll therefore *under-counts* its oldest members: the true past
  electorates were, if anything, grayer than measured here, so the age findings are a
  lower bound. (Idaho has no prior snapshot to measure directly, but attrition
  dominated by mortality is a general mechanism.)
- **This is a claim about composition and closure, not ideological extremism.**
  Sides, Tausanovitch, Vavreck & Warshaw (2020) find primary electorates are not
  dramatically more extreme than their party's rank-and-file, and that openness rules
  do not change that — a result that rebuts a *polarization* argument. It does not
  bear on the argument here, which is about *who is in the room* (one party, older,
  the unaffiliated excluded) and who is shut out, not about the ideology of those who
  show up. We make no claim that Idaho's primary voters are more extreme than other
  Republicans.
- **The donor layer here is state (Idaho Sunshine) by design.** It characterizes the
  people who fund Idaho's *state* campaigns — the relevant layer for state
  electoral health. (Idaho's **federal** FEC contributions were since loaded too —
  770,765 rows / $76.2M outflow + inflow, with 47,762 FEC voter↔donor matches — and the
  cross-state donor comparison uses that FEC match; see
  [`cross-state-fec-money.md`](cross-state-fec-money.md) §F5, whose ID donor mix
  D 19% / R 67% / O 14% closely tracks the Sunshine mix below. The age skew survives the
  matcher-bias re-weighting in ID as in WA/NY.) Recipient party is not in the feed; it is
  reconstructed for
  ~52% of matched donors (candidate roster + committee-name patterns), so the
  crossover table above is limited to party-resolvable recipients and the
  majority-party crossover rate is an upper bound (see §VII).
- **Lean is never imputed for the unaffiliated.** Every "unaffiliated" figure is a
  registration fact, not an inferred partisanship.

---

## What it means

Idaho is the limiting case of the on-cycle-timing argument. Washington showed the
off-year electorate is older; New York showed the shrinkage is party-shaped and
excludes a young unaffiliated bloc; Idaho shows what happens when a single closed
primary, not November, is the entire game. The decision is made by a Republican
electorate grayer than the Republican rolls, in districts where the general cannot
overturn it and — for about half of seats — where even the primary is uncontested,
while a growing quarter of the state stands outside the only contest that counts.

The obvious remedies are institutional: open the primary, or move the decisive
contest onto the high-turnout November calendar. But Idaho has just weighed and
rejected the first. **Proposition 1 (2024)** — which would have replaced the closed
primary with a single top-four open primary and added ranked-choice voting in
November — **lost 69.6% to 30.4%.** That result does not refute this paper; it
illustrates its mechanism. A reform that would enlarge and de-close the electorate
is itself decided *by the existing electorate*, through the very turnout-and-general
structure the reform targets — and the people currently outside the room do not,
from outside it, have the numbers to open the door. The finding here is therefore
less a policy recommendation than the description of a **self-reinforcing
equilibrium**: a closed, gray, one-party primary (contested in only about half of
seats) selects the officials, and the broader electorate that might change the rules
is precisely the one the rules leave least able to.

---

## Related work

This paper documents, with unusually rich individual-level data, mechanisms that
are largely established; its contribution is the measurement and the party-neutral
age result, not the discovery of the mechanisms. It sits in these literatures:

- **The one-party primary as the real election.** V.O. Key, *Southern Politics in
  State and Nation* (1949) — in a one-party polity the dominant party's primary is
  the decisive contest; the general ratifies it. This paper is a modern,
  individual-level instance.
- **Surge-and-decline / turnout composition by salience.** Campbell, "Surge and
  Decline" (1960); Wolfinger & Rosenstone, *Who Votes?* (1980); Leighley & Nagler,
  *Who Votes Now?* (2013). Section I's presidential→midterm falloff is this.
- **Off-cycle / election-timing and representation.** Anzia, *Timing and Turnout*
  (2014); Hajnal & Trounstine (2005); Kogan, Lavertu & Peskowitz (2018, on school
  boards); Einstein et al., "The Gray Vote" (2024) — the closest analog to the age
  result. Motivates the on-cycle remedy.
- **Primary-electorate representativeness (the tension).** Sides, Tausanovitch,
  Vavreck & Warshaw, "On the Representativeness of Primary Electorates" (2020) —
  primaries are not dramatically more *extreme*; distinguished here (our claim is
  composition/closure, not extremism).
- **Independents / the unaffiliated.** Klar & Krupnikov, *Independent Politics* (2016).
- **Voter-file / individual-level method.** Ansolabehere & Hersh, "Validation…"
  (2012); Hersh, *Hacking the Electorate* (2015). On the roll-churn caveat: Feder &
  Miller, "The Racial Burden of Voter List Maintenance Errors," *Science Advances*
  (2020).
- **The donor class.** Bonica, DIME / "Mapping the Ideological Marketplace" (2014);
  Schlozman, Verba & Brady, *The Unheavenly Chorus* (2012); Hill & Huber, "…the
  Contemporary Donorate" (2017, on donors' older skew); Grumbach, Sahn & Staszak
  (2022).
- **The reform just rejected.** Idaho Proposition 1 (2024), top-four open primary +
  ranked-choice voting, defeated 69.6%–30.4% (Idaho SoS).

---

## Methods & reproducibility

```bash
# 1. Load the Idaho voter file -> data/id_vrdb.duckdb (voters + voter_participation)
python scripts/load_id_voters.py

# 2. Turnout by age x party + the closed-primary flagship (Sections I–IV)
python scripts/diag_id_turnout_party.py

# 2b. Contested vs uncontested primaries (Section IV) — SoS 2024 primary canvass
python scripts/diag_id_primary_contested.py

# 3. Donor class x party (Section VII) — resolve recipient party (crossover),
#    then match; writes committee_party_override + voter_donor_affiliation
STATE=ID python scripts/backfill_id_recipient_party.py
STATE=ID python scripts/match_id_voters_to_donors.py

# 4. Electorate extras: unaffiliated bloc, decomposition, cohort trend,
#    safe-seat map, donor-mix x competitiveness (Sections I, III, V, VI, VII)
python scripts/diag_id_electorate_extras.py
```

Source: `data/raw/id/id_statewide_voter_history_20260629.csv` (Idaho SoS
statewide voter file with history, 2026-06-29 export; public record). Party
buckets: REP / DEM / UNAFF (unaffiliated) / OTHER (Libertarian + Constitution).
All headline numbers above are re-derivable by running the scripts in this block.
