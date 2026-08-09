"""Appendix G — do contribution limits compress the top of the donor distribution?

The donor paper (`docs/donor-class-and-the-electorate.md`, Finding 2) used to explain
Idaho's lower matched top-1% share (39.3% vs WA 47.7% / NY 51.2%) by saying that "state
contribution limits compress the very top of the state-money distribution." This script
tests that mechanism directly. It does not hold up, and Appendix G reports why.

The test exploits a natural comparison that needs no new data: Idaho residents appear in
TWO money systems at once. Idaho Sunshine state contributions are capped by Idaho Code
sec. 67-6610A ($1,000 per election to a legislative / judicial / local candidate; $5,000
per election statewide; primary and general count separately). The same population's
federal giving is capped per candidate by 52 U.S.C. sec. 30116 ($3,500 per election in
2025-26, indexed) but faces NO ceiling on total giving after McCutcheon v. FEC, 572 U.S.
185 (2014) struck the biennial aggregate limit. Washington gives the same pair (PDC state
money, capped by RCW 42.17A.405, recodified RCW 29B.40.020 eff. Jan 1 2026, vs FEC).

Four sections:
  G1  the statutory regimes, for the paper's table
  G2  does the cap bind? (bunching on the round cap value)
  G3  concentration by layer: state (capped) vs federal, all contributors and persons only
  G4  winsorization counterfactual: how much of the WA-to-ID gap could a cap explain?

House contract (same as the verify_* scripts): read-only connections, from-scratch SQL, no
importing of the match_*/diag_* analysis code, aggregate-only output. Run from repo root:

    python scripts/diag_contribution_limits.py
"""

from __future__ import annotations

import os

import duckdb

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
ID_DB = os.path.join(DATA, "id_statewide.duckdb")
WA_DB = os.path.join(DATA, "wa_statewide.duckdb")

# Organization-name markers, for separating person filers from committee/corporate ones.
#
# The two state files name people differently, so the person test is per-layer:
#   * Idaho Sunshine files people as "LAST, FIRST" and organizations under their legal
#     name, so "has a comma AND carries no org marker" works.
#   * WA PDC files people as "LAST FIRST" with NO comma (only 3,963 of 2.97M rows contain
#     one), so the comma test is inapplicable there and the org-marker test alone is used
#     -- a weaker filter, flagged as such in the output.
# The FEC individual files are persons by construction (the loader filters ENTITY_TP='IND'),
# so their persons-only and all-filer cuts nearly coincide -- which is the check that the
# heuristic is not doing the work.
ORG_RE = (
    r"(LLC|L\.L\.C|INC\b|CORP|COMPANY|CO\.|LP\b|LLP|LTD|PAC\b|COMMITTEE|CAUCUS|UNION|"
    r"ASSOCIATION|ASSN|FUND\b|LOCAL \d|COUNCIL|DEMOCRAT|REPUBLICAN|PARTY|TRUST|"
    r"INSTITUTE|FOUNDATION|SOCIETY|CENTER|CENTRE|SERVICES|GROUP|PARTNERS|HOLDINGS|"
    r"SCHOOL|HOSPITAL|BANK|CLINIC|FARMS|RANCH|PROPERTIES|CONSTRUCTION|ENTERPRISES|"
    r"INDUSTRIES|SYSTEMS|SOLUTIONS|CONSULTING|LOBBY|FOR CONGRESS|FOR SENATE|FRIENDS OF|"
    r"DISTRIBUT|BEVERAGE|NETWORKS|SMALL CONTRIBUTIONS|UNITEMIZED|ANONYMOUS|MISCELLANEOUS)"
)

NO_ORG = f"NOT regexp_matches(UPPER(contributor_name), '{ORG_RE}')"
PERSONS_COMMA = f"(contributor_name LIKE '%,%' AND {NO_ORG})"

# PDC reports unitemized money under a single pseudo-contributor. Left in, it would key as
# one enormous "donor" and inflate every WA state concentration figure, so it is excluded
# from all WA state cuts.
PDC_PSEUDO = (
    "UPPER(contributor_name) NOT IN "
    "('SMALL CONTRIBUTIONS', 'UNITEMIZED', 'ANONYMOUS', 'MISCELLANEOUS RECEIPTS')"
)


def layer_sql(prefix: str, state: str | None) -> str:
    """WHERE fragment selecting one money layer out of individual_contributions."""
    frag = f"contribution_id LIKE '{prefix}:%' AND contribution_amount > 0"
    if state:
        frag += f" AND contributor_state = '{state}'"
    if prefix == "PDC":
        frag += f" AND {PDC_PSEUDO}"
    return frag


def concentration(con, where: str, persons: str | None = None) -> tuple:
    """Donor-level top-1% / top-10% / Gini, donor = UPPER(name)|zip5.

    Same NTILE(100) estimator as verify_donor_class.py so Appendix G's numbers are
    computed the way Finding 2's are; equal-count buckets are robust to the heavy ties at
    round dollar amounts that capped systems produce.

    `persons` selects the per-layer person test: "comma" for the LAST, FIRST files
    (Sunshine, FEC), "noorg" for WA PDC's LAST FIRST format, None for all filers.
    """
    if persons == "comma":
        where = f"{where} AND {PERSONS_COMMA}"
    elif persons == "noorg":
        where = f"{where} AND {NO_ORG}"
    donors = f"""
        SELECT UPPER(contributor_name) || '|' || SUBSTR(COALESCE(contributor_zip, ''), 1, 5) AS k,
               SUM(contribution_amount) AS t
        FROM individual_contributions
        WHERE {where}
        GROUP BY 1
    """
    top = con.execute(f"""
        WITH d AS ({donors}),
             r AS (SELECT t, NTILE(100) OVER (ORDER BY t DESC) p FROM d)
        SELECT COUNT(*),
               100.0 * SUM(t) FILTER (WHERE p = 1) / SUM(t),
               100.0 * SUM(t) FILTER (WHERE p <= 10) / SUM(t)
        FROM r""").fetchone()
    gini = con.execute(f"""
        WITH d AS ({donors}),
             r AS (SELECT t, ROW_NUMBER() OVER (ORDER BY t) rn,
                          COUNT(*) OVER () n, SUM(t) OVER () s FROM d)
        SELECT (2.0 * SUM(rn * t) / (MAX(n) * MAX(s))) - (MAX(n) + 1.0) / MAX(n) FROM r""").fetchone()[0]
    rows = con.execute(f"""
        SELECT COUNT(*), SUM(contribution_amount) / 1e6
        FROM individual_contributions WHERE {where}""").fetchone()
    return int(rows[0]), float(rows[1]), int(top[0]), float(top[1]), float(top[2]), float(gini)


def show(label: str, m: tuple, paper: str = "") -> None:
    rows, musd, donors, t1, t10, gini = m
    tail = f"   (paper: {paper})" if paper else ""
    print(f"  {label:<34s} rows {rows:>9,}  ${musd:>7.1f}M  donors {donors:>8,}  "
          f"top-1% {t1:5.1f}%  top-10% {t10:5.1f}%  Gini {gini:.3f}{tail}")


# --------------------------------------------------------------------------------------
print(__doc__.split("\n")[0])
print("=" * 100)

# G1 -----------------------------------------------------------------------------------
print("""
G1. THE STATUTORY REGIMES (individual -> candidate, per election)

  state / layer            legislative        statewide       aggregate ceiling on total giving
  -----------------------  -----------------  --------------  ---------------------------------
  Idaho state (Sunshine)   $1,000             $5,000          none  [Idaho Code 67-6610A]
  Washington state (PDC)   capped, indexed    capped, indexed none  [RCW 42.17A.405 -> 29B.40.020]
  New York state (BOE)     capped, very high  capped          none  [N.Y. Elec. Law 14-114]
  Texas state (TEC)        NO DOLLAR LIMIT    NO DOLLAR LIMIT none  [Tex. Elec. Code 253.094 bars
                                                                     corporate/union gifts only;
                                                                     judicial races are the one
                                                                     capped exception, 253.151-.176]
  Federal (FEC)            $3,500 (2025-26)   $3,500          none since McCutcheon v. FEC (2014)

  Note the direction: Idaho's legislative cap ($1,000) is LOWER than the federal per-election
  limit ($3,500), but neither system caps a donor's total. Idaho also permits direct corporate
  and PAC gifts to candidates, which federal law forbids (52 U.S.C. 30118), and caps nothing at
  all on ballot-measure committees.
""")

# G2 / G3 ------------------------------------------------------------------------------
idc = duckdb.connect(ID_DB, read_only=True)

print("G2. DOES THE CAP BIND? Bunching on the round cap value, Idaho Sunshine state money")
bunch = dict(idc.execute(f"""
    SELECT contribution_amount, COUNT(*) FROM individual_contributions
    WHERE {layer_sql('SUNSHINE', None)}
      AND contribution_amount IN (250, 500, 750, 900, 999, 1000, 1001, 1100, 2500, 5000, 5001)
    GROUP BY 1""").fetchall())
for amt in (250, 500, 750, 900, 999, 1000, 1001, 1100, 2500, 5000, 5001):
    star = "   <-- statutory legislative cap" if amt == 1000 else (
        "   <-- statutory statewide cap" if amt == 5000 else "")
    print(f"    ${amt:>6,}: {int(bunch.get(amt, 0)):>7,}{star}")

share = idc.execute(f"""
    SELECT 100.0 * SUM(CASE WHEN contribution_amount >= 1000 THEN contribution_amount ELSE 0 END)
             / SUM(contribution_amount),
           100.0 * SUM(CASE WHEN contribution_amount > 5000 THEN contribution_amount ELSE 0 END)
             / SUM(contribution_amount),
           MAX(contribution_amount)
    FROM individual_contributions WHERE {layer_sql('SUNSHINE', None)}""").fetchone()
print(f"\n    Share of Sunshine dollars in gifts >= $1,000: {share[0]:.1f}%")
print(f"    Share of Sunshine dollars in gifts >  $5,000: {share[1]:.1f}%")
print(f"    Largest single Sunshine contribution:         ${float(share[2]):,.0f}"
      "   (i.e. the caps do not bind the committee layer)")

print("\nG3. CONCENTRATION BY LAYER  (donor = name + zip5; NTILE(100), as in Finding 2)")
print("\n  IDAHO -- same donor population, two regimes:")
id_state_all = concentration(idc, layer_sql("SUNSHINE", None))
id_state_ppl = concentration(idc, layer_sql("SUNSHINE", None), persons="comma")
id_fed_all = concentration(idc, layer_sql("FEC", "ID"))
id_fed_ppl = concentration(idc, layer_sql("FEC", "ID"), persons="comma")
show("ID state (capped), all filers", id_state_all)
show("ID state (capped), persons only", id_state_ppl, "39.3% matched top-1%, Gini 0.798")
show("ID federal, all filers", id_fed_all)
show("ID federal, persons only", id_fed_ppl, "36.0% statewide top-1%, Gini 0.775")
idc.close()

wa = duckdb.connect(WA_DB, read_only=True)
print("\n  WASHINGTON -- the same pair:")
wa_state_all = concentration(wa, layer_sql("PDC", None))
wa_state_ppl = concentration(wa, layer_sql("PDC", None), persons="noorg")
wa_fed_ppl = concentration(wa, layer_sql("FEC", "WA"), persons="comma")
show("WA state (capped), all filers", wa_state_all)
show("WA state (capped), persons (weak)", wa_state_ppl)
show("WA federal, persons only", wa_fed_ppl, "39.3% statewide top-1%, Gini 0.800")

# G4 -----------------------------------------------------------------------------------
print("""
G4. STYLIZED TRANSACTION CLIPPING -- NOT a simulation of any contribution limit.
    Re-run WA's federal layer with each transaction trimmed at a series of thresholds.
    A statutory limit caps a donor's AGGREGATE giving to one recipient committee PER
    ELECTION, and the FEC individual file pools recipient types governed by different
    limits; neither recipient type nor election designation is persisted here. So these
    rows are arithmetic on an unchanged file and carry no statutory label (review #3,
    2026-07-29). See G4c for the aggregate-level variant.""")
wins = {}
for cap in (5000, 3500, 1000):
    m = wa.execute(f"""
        WITH d AS (SELECT UPPER(contributor_name) || '|' ||
                          SUBSTR(COALESCE(contributor_zip, ''), 1, 5) AS k,
                          SUM(LEAST(contribution_amount, {cap})) AS t
                   FROM individual_contributions
                   WHERE {layer_sql('FEC', 'WA')} AND {PERSONS_COMMA}
                   GROUP BY 1),
             r AS (SELECT t, NTILE(100) OVER (ORDER BY t DESC) p FROM d)
        SELECT 100.0 * SUM(t) FILTER (WHERE p = 1) / SUM(t),
               100.0 * SUM(t) FILTER (WHERE p <= 10) / SUM(t), SUM(t) / 1e6
        FROM r""").fetchone()
    wins[cap] = (float(m[0]), float(m[1]), float(m[2]))
    note = "  <-- threshold only; not Idaho law applied to Idaho recipients" if (
        cap in (1000, 5000)) else (
        "  <-- flat threshold; the federal amount varied by cycle, see G4b")
    print(f"    per-gift cap ${cap:>6,}:  top-1% {m[0]:5.1f}%   top-10% {m[1]:5.1f}%   "
          f"${m[2]:.0f}M retained{note}")
print(f"    uncapped (actual):     top-1% {wa_fed_ppl[3]:5.1f}%   top-10% {wa_fed_ppl[4]:5.1f}%")

# G4b — the historically exact version. Added 2026-07-28 on external review: the federal
# individual per-election limit is INDEXED and changed every cycle, so trimming a
# 2017-2026 layer at a flat $3,500 applies a limit that did not exist for most of the
# window. The flat rows above are counterfactual thresholds and are relabelled as such;
# this row trims each gift at the limit in force in ITS OWN cycle.
#   2017-18 $2,700 | 2019-20 $2,800 | 2021-22 $2,900 | 2023-24 $3,300 | 2025-26 $3,500
# (FEC archived limit charts; 2015-16 was also $2,700 but predates this layer.)
FED_LIMIT_BY_CYCLE = {2018: 2700, 2020: 2800, 2022: 2900, 2024: 3300, 2026: 3500}
_cycle = ("CASE WHEN EXTRACT(year FROM contribution_date) % 2 = 0 "
          "THEN EXTRACT(year FROM contribution_date) "
          "ELSE EXTRACT(year FROM contribution_date) + 1 END")
_limit_case = " ".join(
    f"WHEN {y} THEN {v}" for y, v in sorted(FED_LIMIT_BY_CYCLE.items()))
hist = wa.execute(f"""
    WITH g AS (SELECT UPPER(contributor_name) || '|' ||
                      SUBSTR(COALESCE(contributor_zip, ''), 1, 5) AS k,
                      LEAST(contribution_amount,
                            CASE {_cycle} {_limit_case} ELSE 3500 END) AS amt
               FROM individual_contributions
               WHERE {layer_sql('FEC', 'WA')} AND {PERSONS_COMMA}
                 AND contribution_date IS NOT NULL),
         d AS (SELECT k, SUM(amt) t FROM g GROUP BY 1),
         r AS (SELECT t, NTILE(100) OVER (ORDER BY t DESC) p FROM d)
    SELECT 100.0 * SUM(t) FILTER (WHERE p = 1) / SUM(t),
           100.0 * SUM(t) FILTER (WHERE p <= 10) / SUM(t), SUM(t) / 1e6
    FROM r""").fetchone()
print(f"""
    Cycle-varying amount: each transaction trimmed at the federal individual per-election
    amount in force in its own cycle -- 2017-18 $2,700 / 2019-20 $2,800 / 2021-22 $2,900 /
    2023-24 $3,300 / 2025-26 $3,500. This removes a flat-$3,500 anachronism but does NOT
    make the row historically exact, because the amount still attaches per transaction
    rather than per donor-committee-election, and to every recipient type alike.
    cycle-specific limit:  top-1% {float(hist[0]):5.1f}%   top-10% {float(hist[1]):5.1f}%   """
      f"${float(hist[2]):.0f}M retained")

# G4c -- the AGGREGATE variant. Added 2026-07-29 on external review #3, whose criticism is
# correct and is the reason none of the rows above may carry a statutory label: a statutory
# limit caps a donor's AGGREGATE giving to one recipient committee per election, not each
# transaction independently. Clipping transactions therefore under-counts the bite of a real
# cap on a donor who splits a large sum into several gifts to the same committee.
#
# This row aggregates by donor x recipient committee x cycle FIRST, then clips. It is
# materially closer to the statutory structure. TWO GAPS REMAIN and cannot be closed from the
# loaded data, so this is still a stylized exercise and not a simulation of any law:
#   (1) recipient TYPE is not persisted. `fec_candidate_id` holds the recipient COMMITTEE id
#       (C00...), and candidate committees, PACs, state party committees and national party
#       committees are governed by DIFFERENT limits. Applying one number to all of them is
#       not the law.
#   (2) the primary/general ELECTION designation is not persisted, so a per-election cap
#       cannot be separated from a per-cycle one. Clipping per cycle applies roughly half the
#       headroom a candidate committee actually has (primary and general count separately),
#       so this row OVER-states the bite for candidate committees while under-stating it for
#       recipients whose limit is annual.
# Reported so the direction and rough size of the aggregation effect are visible, with both
# gaps named at the point of use rather than in a caveat paragraph.
print("""
G4c. AGGREGATE-LEVEL CLIPPING -- donor x recipient committee x cycle, then clip.
     Closer to how a statutory limit actually attaches. Still NOT a statutory simulation:
     recipient TYPE and the primary/general ELECTION designation are both absent from the
     loaded data (see the comment above this block for what each omission does).""")
for cap in (5000, 3500, 1000):
    m = wa.execute(f"""
        WITH pairagg AS (
            SELECT UPPER(contributor_name) || '|' ||
                   SUBSTR(COALESCE(contributor_zip, ''), 1, 5) AS k,
                   fec_candidate_id AS cmte, election_cycle AS cyc,
                   SUM(contribution_amount) AS pair_total
            FROM individual_contributions
            WHERE {layer_sql('FEC', 'WA')} AND {PERSONS_COMMA}
            GROUP BY 1, 2, 3),
        clipped AS (SELECT k, LEAST(pair_total, {cap}) AS amt FROM pairagg),
        d AS (SELECT k, SUM(amt) t FROM clipped GROUP BY 1),
        r AS (SELECT t, NTILE(100) OVER (ORDER BY t DESC) p FROM d)
        SELECT 100.0 * SUM(t) FILTER (WHERE p = 1) / SUM(t),
               100.0 * SUM(t) FILTER (WHERE p <= 10) / SUM(t), SUM(t) / 1e6
        FROM r""").fetchone()
    pertx = wins[cap][0]
    print(f"    cap ${cap:>6,}:  aggregate top-1% {float(m[0]):5.1f}%   "
          f"top-10% {float(m[1]):5.1f}%   ${float(m[2]):.0f}M retained   "
          f"(per-transaction was {pertx:5.1f}%, diff {float(m[0]) - pertx:+5.1f})")
wa.close()

# Read-out ------------------------------------------------------------------------------
print(f"""
{"=" * 100}
READ-OUT

  1. SOME cap binds, visibly. {int(bunch.get(1000, 0)):,} Idaho state gifts land on exactly $1,000 against
     {int(bunch.get(750, 0)):,} at $750 and {int(bunch.get(999, 0)):,} at $999 -- a spike on a round statutory value, which
     is what a binding constraint looks like. Only {int(bunch.get(1001, 0)):,} gift sits at $1,001. WHICH cap is not
     established: $1,000 is Idaho's legislative/judicial/local candidate limit, and these rows
     carry neither the recipient's type nor the election designation, so a $1,000 gift to a
     PAC or a party committee is not governed by it (review #3, 2026-07-29).

  2. Clipping compresses the top, arithmetically. Trimming WA's federal transactions at
     $1,000 pulls the top-1% share from {wa_fed_ppl[3]:.1f}% to {wins[1000][0]:.1f}%; at $5,000, to {wins[5000][0]:.1f}%.
     These are thresholds, NOT Idaho law applied to Idaho recipients, and the aggregate-level
     variant (G4c) bites 2-4 points harder still. No difference between an observed layer and
     a clipped layer is quoted, because the clipped layer is not a legally matched
     counterfactual for any regime.

  3. Observed capped layers are NOT compressed relative to their federal counterparts.
     Idaho supports the like-for-like comparison: its state money runs top-1% {id_state_ppl[3]:.1f}% among
     persons, ABOVE its own federal layer's {id_fed_ppl[3]:.1f}% persons-only figure. Washington does NOT
     support one -- its persons split is a weak heuristic, so its state row is all-filer
     against a persons-only federal row, and the two states must not be pooled as equal
     evidence. A reading consistent with this, though not demonstrated here: nothing limits a
     donor's TOTAL (McCutcheon), so the same people can reach a cap across many recipients,
     and the tail can displace into vehicles Idaho does not cap at all -- {share[1]:.0f}% of Sunshine
     dollars sit in gifts above $5,000, and with committees included the state layer reaches
     {id_state_all[3]:.1f}%.

  4. So the paper's original explanation fails twice over. Beyond (3), the state/federal
     distinction cannot explain the gap it was invoked for: Idaho is the least concentrated
     of the four states INSIDE the federal layer too ({id_fed_ppl[3]:.1f}% vs WA {wa_fed_ppl[3]:.1f}%), under identical
     federal limits. Low Idaho concentration is a property of Idaho's small retail donor
     base, not of Idaho's state caps.

  CAVEATS. Sunshine covers cycles 2022-2025 (odd years included); the FEC layers cover
  2018-2026, so the windows are not identical. Person/organization separation is a name
  heuristic: Sunshine files people as "LAST, FIRST" so the comma test works there, but WA
  PDC files them as "LAST FIRST", so its persons row uses the org-marker test alone and is
  reported as weak -- the WA state comparison should be read on the all-filer row. PDC's
  "SMALL CONTRIBUTIONS" unitemized pseudo-contributor is excluded from all WA state cuts;
  left in, it keys as a single enormous donor. The FEC files are persons by construction,
  which is why their two cuts nearly coincide. Finding 2's matched layer is persons-only by
  construction, so the persons-only rows are its right comparison -- and ID state persons
  ({id_state_ppl[3]:.1f}% / Gini {id_state_ppl[5]:.3f}) closely reproduces the matched 39.3% / 0.798, an independent
  check that these layer definitions match the paper's.
""")
