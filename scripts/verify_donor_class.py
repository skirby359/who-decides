"""Independent re-derivation of the headline numbers in docs/donor-class-and-the-electorate.md.

Hits the state DBs directly with from-scratch SQL (not by importing the match/diag
scripts). Read-only; aggregate output only (voter files carry PII).

COVERAGE (be precise about this — the paper cites it). For BOTH panels of every
state, this script re-derives:
  F1  donor age skew         WA generation multipliers; NY & ID age bands
  F2  whale concentration    top-1% / top-10% / Gini of matched $   (+ WA geography)
  F3  partisan skew          own-party donor share vs registration  (NY & ID only —
                             WA publishes no party of record)
  F4  give<->vote stacking   WA super-voter rate + propensity; NY generals-voted
  F4c Idaho primary gate     unaffiliated COMPOSITION share of roll / general /
                             primary electorate (denominator-free)

Plus, for Idaho only, a §VII block covering every published figure in
`docs/who-decides-idaho.md`'s donor section — the party table with donor counts, the
age comparison, concentration, Ada County, the district-safety cut and the crossover
table. Unlike F1-F4, which print derived-vs-paper for a human to compare, these HARD
FAIL on divergence. Added 2026-07-27 because §VII had been published for weeks on the
retired all-tier panel with nothing flagging it: the numbers looked plausible, so an
eyeball pass sustained them. Seeding the old count (27,250) now exits non-zero.

PROSE SCRAPING (2026-07-28). Everything above compares a fresh derivation against a figure
held here as a Python CONSTANT. That catches DATA drift — a rebuilt panel that no longer
produces the published number — but it is structurally blind to PROSE drift: someone can
edit a sentence in the paper and leave the constant right, and the check still passes. That
is not hypothetical. The 2026-07-27 tier switch rebuilt every panel and every TABLE in the
paper, but left seven prose restatements on the retired all-tier figures, each one
contradicting the table printed inches above it (Finding 1's NY state 65+ share, its WA
Gen X / Millennial panel comparison, its Idaho under-30 pair, its nine panel-overlap
shares; Finding 3's Democratic skew, federal dollar share, and Republican panel move).
Every one of those is invisible to a constants table and would have been caught by reading
the paper.

So the final section SCRAPES THE PAPER, in the idiom of `verify_whitepaper.py`: each probe
is a regex anchored on the surrounding words, and **every** occurrence of a captured figure
must equal the derived value. A figure stated in a table and restated in prose is therefore
checked twice, which makes a table-vs-prose contradiction fail on whichever occurrence is
wrong. A probe whose anchor matches nothing is a FAILURE, not a skip — rewording a sentence
out from under a check is itself the thing to catch.

NOT covered here, and the paper says so: the recipient-party CROSSOVER tables, the
inverse-propensity re-weighting, the match-tier and household sensitivities, and the
150-record hand rating. The first four are reproduced by their own scripts
(`match_{ny,id}_voters_to_donors.py`, `diag_ny_match_bias.py`,
`diag_donor_class_revisions.py`); the last is a human step.

REGISTRATION BASELINE (2026-07-27). Party and age baselines both use ACTIVE
registrants (`status_code='A'`). That is the universe the matcher itself draws from,
so it is the only denominator commensurable with the matched set. An earlier version
used all retained records for party but active-only for age; the two baselines differ
by at most 0.4 points on any NY cell, and not at all in ID — the Idaho export carries no
active/inactive flag, so `load_id_voters.py` sets every row 'A' and the two baselines
coincide by construction there.

TWO PANELS (2026-07-26). A state's individual_contributions can hold more than one
money system, so the matched layer is built one source at a time and each panel gets
its own table (see docs/donor-class-and-the-electorate.md):

  voter_donor_affiliation_fec     federal (FEC) money  — WA, NY, ID   [primary panel]
  voter_donor_affiliation_state   state money          — WA (PDC), ID (Sunshine)
  voter_donor_affiliation         legacy POOLED match  — what the campaign tooling
                                  reads; NOT a paper panel, since pooling stacks one
                                  person's federal and state giving into a single
                                  donor total and inflates measured concentration.

All three states have BOTH panels. (New York's state panel was added by
`scripts/load_ny_contributions.py`, which loads the NYSBOE per-contribution feed;
before that the NY adapter kept only roll-up columns and the state layer was
genuinely unavailable.)

PERIOD ALIGNMENT. WA and NY carry both money systems over the same years (2016/17-2026),
so their panel comparisons are period-aligned as built. Idaho Sunshine covers only
2023-2025 against a 2017-2026 federal layer, so ID additionally verifies the
period-aligned panels when they exist (`diag_donor_class_revisions.py --build-aligned`).

Run:  python scripts/verify_donor_class.py
"""
from pathlib import Path
import re
import sys

import duckdb

# The coverage audit echoes context from the paper, which contains en dashes and arrows.
# Windows' default cp1252 stdout raises on those, which would crash the run at the point
# it is reporting a real finding.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PAPER = ROOT / "docs" / "donor-class-and-the-electorate.md"
# The manuscript no longer carries its own provenance, reproduction recipe or drafting
# history — those moved to a companion supplement (2026-07-29, manuscript compression).
# The verifier scrapes BOTH, because figures live in both and a probe must not go blind
# just because its sentence changed file.
SUPPLEMENT = ROOT / "docs" / "donor-class-methods-supplement.md"

FED = "voter_donor_affiliation_fec"
STATE = "voter_donor_affiliation_state"
# The pooled table. Never a result in this paper — it is derived here only so the claim that
# pooling INFLATES concentration is checked rather than asserted, and so all three legs of
# that comparison are read off one specification. Pairing a pooled figure with a panel
# figure from a different specification is the error this derivation exists to catch.
POOLED = "voter_donor_affiliation"
# The retained pre-switch snapshots (scripts/snapshot_alltier_panels.py). Reported
# alongside the primaries so a reader sees both specifications in one run.
FED_ALL = FED + "_alltier"
STATE_ALL = STATE + "_alltier"

TIER_LABELS = ("STRICT_ZIP5_FULL", "STRICT_ZIP5_MID", "STRICT_ZIP5", "RELAXED_ZIP3_MID")
_FAILURES: list[str] = []

def has_table(con, t):
    return con.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?", [t]
    ).fetchone()[0] > 0

def require(con, state, tables):
    missing = [t for t in tables if not has_table(con, t)]
    if missing:
        print(f"  !! {state}: missing panel table(s) {', '.join(missing)} — rebuild with "
              f"scripts/match_{state.lower()}_voters_to_donors.py --source {{fec,state}}")
    return not missing

def concentration(con, vda):
    top1, top10 = con.execute(f"""
        WITH r AS (SELECT total_donated t, NTILE(100) OVER (ORDER BY total_donated DESC) p
                   FROM {vda} WHERE total_donated > 0)
        SELECT SUM(t) FILTER (WHERE p=1)/SUM(t), SUM(t) FILTER (WHERE p<=10)/SUM(t) FROM r
    """).fetchone()
    gini = con.execute(f"""
        WITH r AS (SELECT total_donated t, ROW_NUMBER() OVER (ORDER BY total_donated) rn,
                          COUNT(*) OVER () n, SUM(total_donated) OVER () s
                   FROM {vda} WHERE total_donated > 0)
        SELECT (2.0*SUM(rn*t)/(MAX(n)*MAX(s))) - (MAX(n)+1.0)/MAX(n) FROM r
    """).fetchone()[0]
    n, tot = con.execute(
        f"SELECT COUNT(*), SUM(total_donated)/1e6 FROM {vda}").fetchone()
    return int(n), float(tot), top1 * 100, top10 * 100, gini

def conc_line(con, label, vda, paper=""):
    n, tot, t1, t10, g = concentration(con, vda)
    tail = f"   (paper: {paper})" if paper else ""
    print(f"    {label:<16} {n:>9,} donors  ${tot:>8.2f}M   "
          f"top-1% {t1:5.1f}%  top-10% {t10:5.1f}%  Gini {g:.3f}{tail}")

def party_skew(con, vda, bucket_sql, order):
    """Registration share vs matched-donor own-party share, using bucket_sql on vrdb.voters.party.

    The baseline is ACTIVE registrants — the matcher only draws donors from
    status_code='A' voters, so an all-records denominator would compare an
    active-only numerator against a partly-inactive denominator.
    """
    reg = dict(con.execute(f"""
        SELECT {bucket_sql} b, COUNT(*) FROM vrdb.voters WHERE status_code = 'A' GROUP BY 1
    """).fetchall())
    don = dict(con.execute(f"""
        SELECT {bucket_sql} b, COUNT(*) FROM {vda} a JOIN vrdb.voters USING(state_voter_id) GROUP BY 1
    """).fetchall())
    dol = dict(con.execute(f"""
        SELECT {bucket_sql} b, SUM(a.total_donated) FROM {vda} a JOIN vrdb.voters USING(state_voter_id) GROUP BY 1
    """).fetchall())
    rt, dt, lt = sum(reg.values()), sum(don.values()), sum(v for v in dol.values() if v)
    print(f"    {'bucket':9}{'reg%':>8}{'donor%':>8}{'skew':>8}{'$ share':>9}")
    for b in order:
        rp = reg.get(b, 0) / rt * 100
        dp = don.get(b, 0) / dt * 100
        sp = (dol.get(b, 0) or 0) / lt * 100
        print(f"    {b:9}{rp:7.1f}%{dp:7.1f}%{dp-rp:+7.1f}{sp:8.1f}%")

def integrity(con, state, panels, source_prefix):
    """Standing assertions on each rebuilt panel. Prints PASS/FAIL, returns failures.

    These are tripwires, not findings. The reconciliation one is the check that would have
    caught, on its own, the fact that "full-name only" has two non-equivalent definitions:
    filtering a built panel on `match_quality` keeps a rank-0 voter's whole dollar total
    including weak-key gifts, while restricting the MATCH to rank 0 drops them. The panels
    use the latter, so an independently reconstructed rank-0 key must reproduce each
    panel's SUM(total_donated) to the cent.
    """
    fails = []
    print(f"\nINTEGRITY  {state}")
    for label, panel in panels.items():
        if not has_table(con, panel):
            continue
        # 1. No UNKNOWN tier label. Unreachable today (best_tier_rank is always 0-3), so
        #    its value is as a tripwire on a future tier addition.
        n_unk = con.execute(
            f"SELECT COUNT(*) FROM {panel} WHERE match_quality = 'UNKNOWN'").fetchone()[0]
        # 2. Every label is one of the four declared tiers — the check that actually fires
        #    on a `tiers=` typo producing a garbage panel.
        bad = [q for (q,) in con.execute(
            f"SELECT DISTINCT match_quality FROM {panel}").fetchall()
            if q not in TIER_LABELS]
        for cond, msg in ((n_unk, f"{n_unk:,} rows labelled UNKNOWN"),
                          (bad, f"undeclared tier label(s): {bad}")):
            if cond:
                fails.append(f"{state} {label}: {msg}")
                print(f"    FAIL {label:16} {msg}")
        if not (n_unk or bad):
            print(f"    ok   {label:16} tier labels are all declared tiers")

        # REFUND RESIDUE — reported, not failed. WA PDC files contribution refunds as
        # negative amounts, so `total_donated` is a NET figure while d_amount/r_amount sum
        # only the party-resolved gifts. A donor whose refunds exceed their giving nets
        # negative, and a donor with a refund can have d+r above their net total. Neither
        # is corruption. It is confined to WA PDC (every other layer reads zero), and the
        # concentration estimator already filters `total_donated > 0`, so it cannot reach
        # any published concentration figure. The counts are printed so a CHANGE is
        # visible; an earlier version of this check asserted d+r <= total unscoped and
        # flagged 233 WA rows that were simply refunds.
        neg, zero, excess = con.execute(f"""
            SELECT COUNT(*) FILTER (WHERE total_donated < 0),
                   COUNT(*) FILTER (WHERE total_donated = 0),
                   COUNT(*) FILTER (WHERE total_donated > 0
                       AND COALESCE(d_amount,0) + COALESCE(r_amount,0)
                           > total_donated + 0.005)
            FROM {panel}""").fetchone()
        if neg or zero or excess:
            print(f"    note {label:16} refund residue: {neg:,} net-negative, "
                  f"{zero:,} net-zero, {excess:,} with d+r above a positive net")
    return fails

def reconcile_primary(con, state, panel, source_prefix):
    """Assert a panel's dollars equal an independent rank-0 reconstruction, to the cent."""
    if not has_table(con, panel):
        return []
    tiers = {q for (q,) in con.execute(
        f"SELECT DISTINCT match_quality FROM {panel}").fetchall()}
    if tiers != {"STRICT_ZIP5_FULL"}:
        print(f"    --   {panel}: not a primary-spec panel (tiers={sorted(tiers)}), "
              f"reconciliation skipped")
        return []
    con.execute("""CREATE OR REPLACE TEMP TABLE _rc_vk AS
        SELECT UPPER(TRIM(last_name)) lk, UPPER(TRIM(first_name)) ff,
               SUBSTR(reg_zip,1,5) z5, ANY_VALUE(state_voter_id) svid
        FROM vrdb.voters WHERE status_code='A' AND first_name IS NOT NULL
          AND last_name IS NOT NULL AND reg_zip IS NOT NULL
        GROUP BY 1,2,3 HAVING COUNT(*)=1""")
    got = con.execute(f"""
        WITH ck AS (
            SELECT CASE WHEN contributor_name LIKE '%,%'
                        THEN UPPER(TRIM(SPLIT_PART(contributor_name,',',1)))
                        ELSE UPPER(TRIM(SPLIT_PART(TRIM(contributor_name),' ',1))) END lk,
                   CASE WHEN contributor_name LIKE '%,%'
                        THEN UPPER(SPLIT_PART(TRIM(SPLIT_PART(contributor_name,',',2)),' ',1))
                        ELSE UPPER(SPLIT_PART(TRIM(contributor_name),' ',2)) END ff,
                   SUBSTR(contributor_zip,1,5) z5, contribution_amount amt
            FROM individual_contributions
            WHERE contribution_id LIKE '{source_prefix}:%'
              AND contributor_name IS NOT NULL AND contributor_zip IS NOT NULL
              AND UPPER(contributor_name) NOT IN
                  ('SMALL CONTRIBUTIONS','UNITEMIZED','ANONYMOUS')
              AND COALESCE(contributor_type,'UNKNOWN')
                  NOT IN ('ORGANIZATION','COMMITTEE'))
        SELECT COUNT(DISTINCT v.svid), COALESCE(SUM(k.amt),0)
        FROM ck k JOIN _rc_vk v ON v.lk=k.lk AND v.ff=k.ff AND v.z5=k.z5
        WHERE LENGTH(k.ff) >= 2""").fetchone()
    exp = con.execute(
        f"SELECT COUNT(*), COALESCE(SUM(total_donated),0) FROM {panel}").fetchone()
    dn, dd = exp[0] - got[0], abs(float(exp[1]) - float(got[1]))
    ok = (dn == 0) and (dd < 0.01)
    print(f"    {'ok  ' if ok else 'FAIL'} {panel:38} "
          f"donors {exp[0]:>8,} vs {got[0]:>8,}   "
          f"${float(exp[1])/1e6:8.2f}M vs ${float(got[1])/1e6:8.2f}M")
    return [] if ok else [
        f"{state} {panel}: reconciliation off by {dn} donors / ${dd:,.2f}"]

def check(rows):
    """Assert derived values against published ones. rows = (label, derived, paper, tol).

    Unlike the F1-F4 cuts above, which print derived-vs-paper for a human to eyeball,
    these HARD FAIL. The Idaho section they cover was published for weeks carrying figures
    from a retired panel specification with nothing marking them stale (see
    docs/electoral-health-audit-log.md rows 21-23b), which is exactly the failure an eyeball
    pass does not catch. Tolerances match the precision the paper prints at: counts are
    exact, one-decimal table cells 0.05, and prose figures rounded to whole percents 0.5.
    """
    fails = []
    for label, derived, paper, tol in rows:
        ok = abs(float(derived) - float(paper)) <= tol
        shown = f"{derived:,.0f}" if tol == 0 else f"{derived:.1f}"
        want = f"{paper:,.0f}" if tol == 0 else f"{paper:.1f}"
        print(f"    {'ok  ' if ok else 'FAIL'} {label:44} {shown:>10}   (paper: {want})")
        if not ok:
            fails.append(f"ID §VII {label}: derived {shown} vs paper {want}")
    return fails

def section_vii(con):
    """Idaho paper §VII — every published figure in the donor section, machine-checked.

    §VII reports the STATE (Sunshine) panel; the federal panel is the cross-state
    comparison's, not this section's. Ada County, the district-safety cut and the
    crossover table are unique to this section and are covered nowhere else.
    """
    print("\n§VII who-decides-idaho.md — published figures (STATE panel), asserted")
    if not has_table(con, STATE):
        print("    -- state panel absent, skipped")
        return []
    P = ("CASE WHEN v.party='REP' THEN 'REP' WHEN v.party='DEM' THEN 'DEM' "
         "WHEN v.party='UNA' THEN 'UNAFF' ELSE 'OTHER' END")
    rows = []

    n, gifts, usd = con.execute(
        f"SELECT COUNT(*), SUM(donation_count), SUM(total_donated) FROM {STATE}").fetchone()
    rows += [("matched donors", n, 23_613, 0), ("donations", gifts, 114_806, 0),
             ("matched dollars ($M)", float(usd) / 1e6, 13.64, 0.005)]

    # Party table: donors, donor share, registration share, skew, dollar share.
    pub = {"REP": (15_645, 66.3, 62.9, 3.4, 72.2), "DEM": (5_097, 21.6, 11.8, 9.8, 20.0),
           "UNAFF": (2_735, 11.6, 23.9, -12.3, 7.6), "OTHER": (136, 0.6, 1.4, -0.9, 0.2)}
    reg = dict(con.execute(
        f"SELECT {P} b, COUNT(*) FROM vrdb.voters v WHERE status_code='A' GROUP BY 1").fetchall())
    rt = sum(reg.values())
    for b, dn, dp, sp in con.execute(f"""
        SELECT {P} b, COUNT(*), 100.0*COUNT(*)/SUM(COUNT(*)) OVER (),
               100.0*SUM(a.total_donated)/SUM(SUM(a.total_donated)) OVER ()
        FROM {STATE} a JOIN vrdb.voters v USING(state_voter_id) GROUP BY 1""").fetchall():
        pn, pdp, prp, psk, pdl = pub[b]
        rows += [(f"{b} donors", dn, pn, 0), (f"{b} donor share %", dp, pdp, 0.05),
                 (f"{b} reg share %", reg.get(b, 0) / rt * 100, prp, 0.05),
                 (f"{b} skew", dp - reg.get(b, 0) / rt * 100, psk, 0.05),
                 (f"{b} dollar share %", sp, pdl, 0.05)]

    # Age. All three populations on CURRENT-ROLL age — the paper says so explicitly,
    # because Section I's table is age-at-election and the two are not interchangeable.
    d65, d30 = con.execute(f"""
        SELECT 100.0*COUNT(*) FILTER (WHERE v.age>=65)/COUNT(*),
               100.0*COUNT(*) FILTER (WHERE v.age<30)/COUNT(*)
        FROM {STATE} a JOIN vrdb.voters v USING(state_voter_id)""").fetchone()
    r65, r30 = con.execute("""
        SELECT 100.0*COUNT(*) FILTER (WHERE age>=65)/COUNT(*),
               100.0*COUNT(*) FILTER (WHERE age<30)/COUNT(*)
        FROM vrdb.voters WHERE status_code='A'""").fetchone()
    g65, = con.execute("""
        SELECT 100.0*COUNT(*) FILTER (WHERE v.age>=65)/COUNT(*)
        FROM vrdb.voters v JOIN vrdb.voter_participation p USING(state_voter_id)
        WHERE p.election_year=2024 AND p.kind='GENERAL'""").fetchone()
    rows += [("donors 65+ %", d65, 51, 0.5), ("donors under-30 %", d30, 2.1, 0.05),
             ("roll 65+ %", r65, 31, 0.5), ("roll under-30 %", r30, 15, 0.5),
             ("2024 general 65+ % (current-roll age)", g65, 33, 0.5)]

    t1, t10 = con.execute(f"""
        WITH r AS (SELECT total_donated t, NTILE(100) OVER (ORDER BY total_donated DESC) p
                   FROM {STATE} WHERE total_donated>0)
        SELECT 100.0*SUM(t) FILTER(WHERE p=1)/SUM(t),
               100.0*SUM(t) FILTER(WHERE p<=10)/SUM(t) FROM r""").fetchone()
    ada, = con.execute(f"""
        SELECT 100.0*SUM(a.total_donated) FILTER (WHERE v.county_name='ADA')
               /SUM(a.total_donated)
        FROM {STATE} a JOIN vrdb.voters v USING(state_voter_id)""").fetchone()
    rows += [("top-1% share of $", t1, 40, 0.5), ("top-10% share of $", t10, 71, 0.5),
             ("Ada County share of $", ada, 50, 0.5)]

    # District safety, on Section V's own registration bands so the cut is reproducible.
    bands = {r[0]: r[1:] for r in con.execute(f"""
        WITH ld AS (SELECT legislative_district d,
               100.0*COUNT(*) FILTER(WHERE party='REP')/COUNT(*)
             - 100.0*COUNT(*) FILTER(WHERE party='DEM')/COUNT(*) net
            FROM vrdb.voters WHERE legislative_district IS NOT NULL GROUP BY 1),
        b AS (SELECT d, CASE WHEN net>=40 THEN 'solid' ELSE 'competitive-adjacent' END band
              FROM ld)
        SELECT b.band, COUNT(DISTINCT b.d), COUNT(*),
               100.0*COUNT(*) FILTER (WHERE v.party='REP')/COUNT(*),
               100.0*COUNT(*) FILTER (WHERE v.party='DEM')/COUNT(*)
        FROM {STATE} a JOIN vrdb.voters v USING(state_voter_id)
        JOIN b ON b.d = v.legislative_district GROUP BY 1""").fetchall()}
    for band, (plds, pn, prep, pdem) in (("solid", (27, 14_594, 78, 13)),
                                         ("competitive-adjacent", (8, 9_019, 47, 35))):
        lds, dn, rp, dp = bands[band]
        rows += [(f"{band} LDs", lds, plds, 0), (f"{band} donors", dn, pn, 0),
                 (f"{band} donors % REP", rp, prep, 0.5),
                 (f"{band} donors % DEM", dp, pdem, 0.5)]

    # Crossover. Denominators matter here: resolution is a share of ALL matched donors
    # and of ALL matched dollars, while the D-only/R-only/mixed rates are shares of the
    # RESOLVED donors only. The paper states both bases.
    rd, rdol = con.execute(f"""
        SELECT 100.0*COUNT(*) FILTER (WHERE d_amount+r_amount>0)/COUNT(*),
               100.0*SUM(d_amount+r_amount)/SUM(total_donated) FROM {STATE}""").fetchone()
    rows += [("recipient resolved, % of donors", rd, 51, 0.5),
             ("recipient resolved, % of dollars", rdol, 41, 0.5)]
    xpub = {"REP": (19.1, 79.0), "DEM": (94.6, 3.0), "UNAFF": (77.1, 20.5)}
    for b, d_only, r_only in con.execute(f"""
        SELECT {P} b,
          100.0*COUNT(*) FILTER (WHERE d_amount>0 AND r_amount=0)/COUNT(*),
          100.0*COUNT(*) FILTER (WHERE r_amount>0 AND d_amount=0)/COUNT(*)
        FROM {STATE} a JOIN vrdb.voters v USING(state_voter_id)
        WHERE d_amount+r_amount>0 GROUP BY 1""").fetchall():
        if b in xpub:
            rows += [(f"{b} gave only to D %", d_only, xpub[b][0], 0.05),
                     (f"{b} gave only to R %", r_only, xpub[b][1], 0.05)]
    return check(rows)

def age_bands(con, vda, age_expr, ref_voters_sql):
    """donor% vs reference-population% by 18-29/30-44/45-64/65+."""
    band = (f"CASE WHEN {age_expr}<30 THEN '18-29' WHEN {age_expr}<45 THEN '30-44' "
            f"WHEN {age_expr}<65 THEN '45-64' ELSE '65+' END")
    don = dict(con.execute(f"""
        SELECT {band} b, COUNT(*) FROM {vda} a JOIN vrdb.voters v USING(state_voter_id)
        WHERE {age_expr} IS NOT NULL GROUP BY 1""").fetchall())
    ref = dict(con.execute(f"""
        SELECT {band} b, COUNT(*) FROM vrdb.voters v WHERE {age_expr} IS NOT NULL AND ({ref_voters_sql}) GROUP BY 1""").fetchall())
    dt, rt = sum(don.values()), sum(ref.values())
    print(f"    {'band':7}{'donor%':>9}{'refpop%':>9}")
    for b in ["18-29", "30-44", "45-64", "65+"]:
        print(f"    {b:7}{don.get(b,0)/dt*100:8.1f}%{ref.get(b,0)/rt*100:8.1f}%")

# ============================== WASHINGTON ==============================
print("=" * 78 + "\nWASHINGTON  (wa_statewide + wa_vrdb)\n" + "=" * 78)
wa = duckdb.connect(str(DATA / "wa_statewide.duckdb"), read_only=True)
wa.execute(f"ATTACH '{DATA / 'wa_vrdb.duckdb'}' AS vrdb (READ_ONLY)")
require(wa, "WA", [FED, STATE])

roll = dict(wa.execute("SELECT age_cohort,COUNT(*) FROM voter_scores WHERE LEFT(district_id,2)='ld' AND age_cohort IS NOT NULL GROUP BY 1").fetchall())
rt = sum(roll.values())
for _label, _panel in (("FEDERAL", FED), ("STATE (PDC)", STATE)):
    print(f"\nF1 generation multiplier = donor share / roll share, {_label} panel")
    don = dict(wa.execute(f"""SELECT s.age_cohort,COUNT(*) FROM voter_scores s JOIN {_panel} a USING(state_voter_id)
                             WHERE LEFT(s.district_id,2)='ld' AND s.age_cohort IS NOT NULL GROUP BY 1""").fetchall())
    dt = sum(don.values())
    for g in ["Silent", "Boomer", "Gen X", "Millennial", "Gen Z"]:
        rp, dp = roll.get(g, 0) / rt * 100, don.get(g, 0) / dt * 100
        print(f"    {g:11}{dp/rp:5.2f}x   (roll {rp:4.1f}%  donor {dp:4.1f}%)")

print("\nF2 concentration by panel:")
conc_line(wa, "federal", FED)
conc_line(wa, "state (PDC)", STATE)
zip3 = wa.execute(f"""WITH z AS (SELECT SUBSTR(v.reg_zip,1,3) z3, SUM(a.total_donated) tot
    FROM {FED} a JOIN vrdb.voters v USING(state_voter_id)
    WHERE a.total_donated>0 AND v.reg_zip IS NOT NULL GROUP BY 1)
    SELECT z3, tot/SUM(tot) OVER () sh FROM z ORDER BY tot DESC LIMIT 3""").fetchall()
print("    federal geography: " + "  ".join(f"{z}xx {s*100:.1f}%" for z, s in zip3))

for _label, _panel in (("FEDERAL", FED), ("STATE (PDC)", STATE)):
    print(f"\nF4 give<->vote stacking, {_label} panel")
    for donor, n2, sr, ap in wa.execute(f"""
        WITH roll AS (SELECT DISTINCT state_voter_id,is_super_voter,turnout_propensity FROM voter_scores WHERE LEFT(district_id,2)='ld'),
        f AS (SELECT r.*, CASE WHEN a.state_voter_id IS NOT NULL THEN 1 ELSE 0 END d FROM roll r LEFT JOIN {_panel} a USING(state_voter_id))
        SELECT d,COUNT(*),AVG(CASE WHEN is_super_voter THEN 1.0 ELSE 0 END),AVG(turnout_propensity) FROM f GROUP BY d ORDER BY d""").fetchall():
        print(f"    {'matched donor' if donor else 'non-donor':14} n={n2:>10,}  super {sr*100:5.1f}%  avg prop {ap:.3f}")
_FAILURES += integrity(wa, "WA", {"federal": FED, "state": STATE}, None)
print("\nRECONCILIATION  WA (primary-spec panels only)")
_FAILURES += reconcile_primary(wa, "WA", FED, "FEC")
_FAILURES += reconcile_primary(wa, "WA", STATE, "PDC")
wa.close()

# ============================== NEW YORK ==============================
print("\n" + "=" * 78 + "\nNEW YORK  (ny_statewide + ny_vrdb)\n" + "=" * 78)
ny = duckdb.connect(str(DATA / "ny_statewide.duckdb"), read_only=True)
ny.execute(f"ATTACH '{DATA / 'ny_vrdb.duckdb'}' AS vrdb (READ_ONLY)")
require(ny, "NY", [FED, STATE])
NY_AGE = "date_diff('year', v.birthdate, DATE '2024-11-05')"
NY_REF = ("v.state_voter_id IN (SELECT state_voter_id FROM vrdb.voter_participation "
          "WHERE kind='GENERAL' AND election_year=2024)")
NY_PARTY = ("CASE WHEN party='DEM' THEN 'DEM' WHEN party='REP' THEN 'REP' "
            "WHEN party='BLK' THEN 'NOPARTY' ELSE 'OTHER' END")

print("\nF1 age bands, FEDERAL panel (2024 GE voters ref)")
age_bands(ny, FED, NY_AGE, NY_REF)
print("\nF1 age bands, STATE panel (2024 GE voters ref)")
age_bands(ny, STATE, NY_AGE, NY_REF)
print("\nF2 concentration by panel:")
conc_line(ny, "federal", FED)
conc_line(ny, "state (NYSBOE)", STATE)
print("\nF3 own-party skew, FEDERAL panel")
party_skew(ny, FED, NY_PARTY, ["DEM", "REP", "NOPARTY", "OTHER"])
print("\nF3 own-party skew, STATE panel")
party_skew(ny, STATE, NY_PARTY, ["DEM", "REP", "NOPARTY", "OTHER"])

# F4: generals voted of the last four, donors vs non-donors, per panel. The
# denominator is active registrants — the matcher's own universe.
for _label, _panel in (("FEDERAL", FED), ("STATE (NYSBOE)", STATE)):
    print(f"\nF4 give<->vote stacking, {_label} panel")
    for donor, n2, avg, sup in ny.execute(f"""
        WITH gen AS (
            SELECT state_voter_id, COUNT(DISTINCT election_year) g
            FROM vrdb.voter_participation
            WHERE kind='GENERAL' AND election_year IN (2018,2020,2022,2024)
            GROUP BY 1),
        roll AS (
            SELECT v.state_voter_id, COALESCE(gen.g,0) g,
                   CASE WHEN a.state_voter_id IS NOT NULL THEN 1 ELSE 0 END d
            FROM vrdb.voters v
            LEFT JOIN gen USING (state_voter_id)
            LEFT JOIN {_panel} a USING (state_voter_id)
            WHERE v.status_code='A')
        SELECT d, COUNT(*), AVG(g), AVG(CASE WHEN g>=3 THEN 1.0 ELSE 0 END)
        FROM roll GROUP BY d ORDER BY d""").fetchall():
        print(f"    {'matched donor' if donor else 'non-donor':14} n={n2:>10,}  "
              f"generals {avg:.2f} of 4  super(>=3) {sup*100:5.1f}%")
_FAILURES += integrity(ny, "NY", {"federal": FED, "state": STATE}, None)
print("\nRECONCILIATION  NY (primary-spec panels only)")
_FAILURES += reconcile_primary(ny, "NY", FED, "FEC")
_FAILURES += reconcile_primary(ny, "NY", STATE, "NY")
ny.close()

# ============================== IDAHO ==============================
print("\n" + "=" * 78 + "\nIDAHO  (id_statewide + id_vrdb)\n" + "=" * 78)
idc = duckdb.connect(str(DATA / "id_statewide.duckdb"), read_only=True)
idc.execute(f"ATTACH '{DATA / 'id_vrdb.duckdb'}' AS vrdb (READ_ONLY)")
require(idc, "ID", [FED, STATE])

print("\nF1 age bands, current-roll age, FEDERAL panel (all voters ref)")
age_bands(idc, FED, "v.age", "1=1")
print("\nF1 age bands, current-roll age, STATE panel (all voters ref)")
age_bands(idc, STATE, "v.age", "1=1")

print("\nF2 concentration by panel:")
conc_line(idc, "federal", FED)
conc_line(idc, "state (Sunshine)", STATE)

print("\nF3 own-party skew, FEDERAL panel")
party_skew(idc, FED, "CASE WHEN party='REP' THEN 'REP' WHEN party='DEM' THEN 'DEM' WHEN party='UNA' THEN 'UNAFF' ELSE 'OTHER' END",
           ["REP", "DEM", "UNAFF", "OTHER"])
print("\nF3 own-party skew, STATE panel")
party_skew(idc, STATE, "CASE WHEN party='REP' THEN 'REP' WHEN party='DEM' THEN 'DEM' WHEN party='UNA' THEN 'UNAFF' ELSE 'OTHER' END",
           ["REP", "DEM", "UNAFF", "OTHER"])

# F4c: the primary gate, as COMPOSITION shares. Turnout RATES off a current roll are
# survivorship-inflated in Idaho (the 2026 roll is smaller than the 2024 electorate),
# so the paper reports each population's party mix instead — no denominator needed.
print("\nF4c unaffiliated share of roll / 2024 general / 2024 primary electorate")
for pop, n, rep, dem, una in idc.execute("""
    WITH roll AS (SELECT state_voter_id, party FROM vrdb.voters),
    ge AS (SELECT DISTINCT state_voter_id FROM vrdb.voter_participation
           WHERE election_year=2024 AND kind='GENERAL'),
    pr AS (SELECT DISTINCT state_voter_id FROM vrdb.voter_participation
           WHERE election_year=2024 AND kind='PRIMARY'),
    pops AS (
      SELECT '1 registration roll' pop, party FROM roll
      UNION ALL SELECT '2 2024 general', r.party FROM roll r JOIN ge USING (state_voter_id)
      UNION ALL SELECT '3 2024 primary', r.party FROM roll r JOIN pr USING (state_voter_id))
    SELECT pop, COUNT(*),
           100.0*COUNT(*) FILTER (WHERE party='REP')/COUNT(*),
           100.0*COUNT(*) FILTER (WHERE party='DEM')/COUNT(*),
           100.0*COUNT(*) FILTER (WHERE party='UNA')/COUNT(*)
    FROM pops GROUP BY 1 ORDER BY 1""").fetchall():
    print(f"    {pop:22} n={n:>9,}  REP {rep:5.1f}%  DEM {dem:5.1f}%  UNAFF {una:5.1f}%")

# Period-aligned panels, when built. Idaho is the only state whose two money systems
# cover different years, so it is the only one where alignment can change a panel
# comparison (see docs/donor-class-and-the-electorate.md Appendix C).
if has_table(idc, FED + "_aligned") and has_table(idc, STATE + "_aligned"):
    print("\nF1/F2 PERIOD-ALIGNED panels (both money systems restricted to 2023-2025)")
    for label, panel in (("federal aligned", FED + "_aligned"),
                         ("state aligned", STATE + "_aligned")):
        conc_line(idc, label, panel)
        age_bands(idc, panel, "v.age", "1=1")
else:
    print("\n  (aligned ID panels not built — run "
          "scripts/diag_donor_class_revisions.py --build-aligned)")
_FAILURES += section_vii(idc)
_FAILURES += integrity(idc, "ID", {"federal": FED, "state": STATE}, None)
print("\nRECONCILIATION  ID (primary-spec panels only)")
_FAILURES += reconcile_primary(idc, "ID", FED, "FEC")
_FAILURES += reconcile_primary(idc, "ID", STATE, "SUNSHINE")
idc.close()

# ====================== PROSE SCRAPE — derive, then assert ======================
# Age basis. NY's bands and every 65+ cut outside Idaho are measured at the 2024 general,
# matching match_ny_voters_to_donors.py and diag_donor_class_revisions.py. Idaho's roll
# carries a current-age integer instead of a DOB, so ID uses v.age — the paper states the
# difference, and the two are NOT interchangeable (mixing them is defect R? in the Idaho
# paper's own history).
_AGE_2024 = "date_diff('year', v.birthdate, DATE '2024-11-05')"
_GENS = ["Silent", "Boomer", "Gen X", "Millennial", "Gen Z"]

def _exact_top_share(con, panel, pct):
    """Top-`pct`% dollar share on an EXACT donor-weight cutoff, fractional at the boundary.

    `NTILE(100)` splits donors into 100 buckets of near-equal count; when n is not divisible
    by 100 the first bucket holds ceil(n/100) donors, so "top 1%" is approximately rather
    than exactly 1%. It also breaks ties on `total_donated` arbitrarily. Both are real
    objections (external review, 2026-07-28). This computes the alternative — sort
    descending, take exactly n*pct/100 donors' worth of weight, pro-rating the donor who
    straddles the boundary — so the two can be compared instead of argued about.

    Returns (exact_share, n_tied_at_boundary). The tie count is reported because that is the
    part no cutoff rule fixes: where k donors share the boundary value, which of them lands
    inside is arbitrary under any ordering.
    """
    vals = [float(v) for (v,) in con.execute(
        f"SELECT total_donated FROM {panel} WHERE total_donated > 0 "
        f"ORDER BY total_donated DESC").fetchall()]
    n, tot = len(vals), sum(vals)
    if not n or not tot:
        return 0.0, 0
    k = n * pct / 100.0
    whole = int(k)
    share = sum(vals[:whole]) + (vals[whole] * (k - whole) if whole < n else 0.0)
    boundary = vals[whole] if whole < n else vals[-1]
    return share / tot * 100, sum(1 for v in vals if v == boundary)

_STD_BANDS = ["18-24", "25-34", "35-44", "45-54", "55-64", "65-74", "75+"]
_TENURE_BANDS = ["<2y", "2-5y", "6-10y", "11-20y", "20y+"]

def _std_band_sql(age_expr):
    return (f"CASE WHEN {age_expr}<25 THEN '18-24' WHEN {age_expr}<35 THEN '25-34' "
            f"WHEN {age_expr}<45 THEN '35-44' WHEN {age_expr}<55 THEN '45-54' "
            f"WHEN {age_expr}<65 THEN '55-64' WHEN {age_expr}<75 THEN '65-74' "
            f"ELSE '75+' END")

def _tenure_sql(reg_expr="v.registration_date"):
    y = f"date_diff('year', {reg_expr}, DATE '2024-11-05')"
    return (f"CASE WHEN {y}<2 THEN '<2y' WHEN {y}<6 THEN '2-5y' WHEN {y}<11 THEN '6-10y' "
            f"WHEN {y}<21 THEN '11-20y' ELSE '20y+' END")

def _d_age_std_party(con, prefix, panels, age_expr, party_case, parties, out, fine=True):
    """Age-standardized donor party shares (Finding 3's standardization subsection).

    Direct standardization: standard population = active registrants with a usable age of
    18+; the standardized share of party p is sum_band w_band * (p's share of that band's
    donors). Reported as raw skew, standardized skew, and the share of the raw skew that is
    age composition. Written from scratch here — `diag_donor_age_standardization.py` computes
    the same quantities independently, which is the point of this file.
    """
    band = _std_band_sql(age_expr) if fine else (
        f"CASE WHEN {age_expr}<30 THEN '18-29' WHEN {age_expr}<45 THEN '30-44' "
        f"WHEN {age_expr}<65 THEN '45-64' ELSE '65+' END")
    bands = _STD_BANDS if fine else ["18-29", "30-44", "45-64", "65+"]
    reg = {(b, p): int(n) for b, p, n in con.execute(f"""
        SELECT {band} b, {party_case} p, COUNT(*) FROM vrdb.voters v
        WHERE status_code='A' AND {age_expr} IS NOT NULL AND {age_expr} >= 18
        GROUP BY 1, 2""").fetchall()}
    reg_band = {b: sum(n for (bb, _), n in reg.items() if bb == b) for b in bands}
    reg_total = sum(reg_band.values())
    out[f"{prefix}_stdpop_n"] = reg_total
    for tag, panel in panels.items():
        don = {(b, p): int(n) for b, p, n in con.execute(f"""
            SELECT {band} b, {party_case} p, COUNT(*)
            FROM {panel} a JOIN vrdb.voters v USING (state_voter_id)
            WHERE v.status_code='A' AND {age_expr} IS NOT NULL AND {age_expr} >= 18
            GROUP BY 1, 2""").fetchall()}
        don_band = {b: sum(n for (bb, _), n in don.items() if bb == b) for b in bands}
        don_total = sum(don_band.values())
        for p in parties:
            reg_p = sum(n for (_, pp), n in reg.items() if pp == p)
            roll_pct = reg_p / reg_total * 100 if reg_total else float("nan")
            raw = (sum(n for (_, pp), n in don.items() if pp == p) / don_total * 100
                   if don_total else float("nan"))
            std = sum(reg_band[b] / reg_total * (don.get((b, p), 0) / don_band[b])
                      for b in bands if don_band.get(b)) * 100
            k = f"{prefix}_{tag}_std_{p}"
            out[f"{k}_rawskew"] = raw - roll_pct
            out[f"{k}_stdskew"] = std - roll_pct
            # share of the raw skew that is age composition; negative means standardization
            # moved the skew FURTHER from zero (age was working against the raw figure).
            rs = raw - roll_pct
            out[f"{k}_expl"] = ((rs - (std - roll_pct)) / rs * 100
                                if abs(rs) > 1e-9 else float("nan"))
            # prevalence: matched donors per 1,000 registrants of the same party
            out[f"{k}_prev"] = (sum(n for (_, pp), n in don.items() if pp == p)
                                / reg_p * 1000) if reg_p else float("nan")

def _d_turnout_std(con, prefix, roll_sql, panels, out):
    """Age- and age x tenure-standardized donor / non-donor turnout gaps (Finding 4).

    roll_sql yields (state_voter_id, band, tenure, super). Standard population = the pooled
    comparison universe, so each group is reweighted onto the roll's own composition.
    """
    con.execute(f"CREATE OR REPLACE TEMP TABLE _vroll AS {roll_sql}")
    for tag, panel in panels.items():
        con.execute(f"""
            CREATE OR REPLACE TEMP TABLE _vcmp AS
            SELECT r.*, CASE WHEN a.state_voter_id IS NOT NULL THEN 1 ELSE 0 END dn
            FROM _vroll r LEFT JOIN {panel} a USING (state_voter_id)""")
        raw = {int(dn): float(s) for dn, s in con.execute(
            "SELECT dn, AVG(super) FROM _vcmp GROUP BY 1").fetchall()}
        out[f"{prefix}_{tag}_tgap_raw"] = (raw[1] - raw[0]) * 100

        cell = {(b, int(dn)): (int(n), float(s)) for b, dn, n, s in con.execute(
            "SELECT band, dn, COUNT(*), AVG(super) FROM _vcmp GROUP BY 1, 2").fetchall()}
        # Standardization weights. Only the RATIO of band weights matters — a common total
        # cancels in num/den below — so no overall population size is needed here.
        pop = {b: sum(n for (bb, _), (n, _) in cell.items() if bb == b) for b in _STD_BANDS}

        def _std(who):
            num = sum(pop[b] * cell[(b, who)][1] for b in _STD_BANDS
                      if pop.get(b) and (b, who) in cell)
            den = sum(pop[b] for b in _STD_BANDS if pop.get(b) and (b, who) in cell)
            return num / den if den else float("nan")
        out[f"{prefix}_{tag}_tgap_age"] = (_std(1) - _std(0)) * 100
        # per-band gaps, for the "widest in the middle bands" sentence
        for b_ in _STD_BANDS:
            if (b_, 1) in cell and (b_, 0) in cell:
                out[f"_{prefix}_{tag}_bandgap_{b_.replace('-', '').replace('+', 'p')}"] = (
                    cell[(b_, 1)][1] - cell[(b_, 0)][1]) * 100

        jc = {(b, t, int(dn)): (int(n), float(s)) for b, t, dn, n, s in con.execute(
            "SELECT band, tenure, dn, COUNT(*), AVG(super) FROM _vcmp "
            "WHERE tenure IS NOT NULL GROUP BY 1, 2, 3").fetchall()}
        jpop = {}
        for (b, t, _), (n, _) in jc.items():
            jpop[(b, t)] = jpop.get((b, t), 0) + n
        keys = [k for k in jpop if (k[0], k[1], 1) in jc and (k[0], k[1], 0) in jc]

        def _jstd(who):
            if not keys:
                return float("nan")
            return sum(jpop[k] * jc[(k[0], k[1], who)][1] for k in keys) \
                / sum(jpop[k] for k in keys)
        out[f"{prefix}_{tag}_tgap_ten"] = (_jstd(1) - _jstd(0)) * 100
        out[f"{prefix}_{tag}_tgap_ten_kept"] = (
            sum(jpop[k] for k in keys) / sum(jpop.values()) * 100 if jpop else float("nan"))

def _d_party_matchability(con, prefix, panels, age_expr, party_case, parties, out):
    """P(matchable) by party, incidence re-based on it, and age x county standardization.

    Review #3 asked whether the party incidence table confounds donation behavior with the
    probability that a party's registrants are uniquely matchable under the full-name key, and
    separately whether age standardization leaves a geographic confound (giving is
    geographically concentrated; party registration is geographically structured). Both are
    derived here from scratch — `diag_donor_review3.py` computes the same quantities
    independently.
    """
    band = _std_band_sql(age_expr)
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE _vm_roll AS
        WITH base AS (
            SELECT v.state_voter_id, {party_case} AS party, {band} AS band, v.county_name,
                   (v.first_name IS NOT NULL AND v.last_name IS NOT NULL
                    AND v.reg_zip IS NOT NULL) AS complete,
                   UPPER(TRIM(v.last_name)) l, UPPER(TRIM(v.first_name)) f,
                   SUBSTR(v.reg_zip, 1, 5) z
            FROM vrdb.voters v
            WHERE v.status_code='A' AND {age_expr} IS NOT NULL AND {age_expr} >= 18)
        SELECT state_voter_id, party, band, county_name, complete,
               CASE WHEN complete
                    THEN COUNT(*) FILTER (WHERE complete) OVER (PARTITION BY l, f, z)
                    END AS keycount
        FROM base""")
    # completeness floor across parties, tracked as a running minimum over both states so the
    # paper's ">= X% in every party of both states" claim is checkable rather than asserted.
    for (cmin,) in con.execute("""
        SELECT MIN(pct) FROM (SELECT 100.0*COUNT(*) FILTER (WHERE complete)/COUNT(*) pct
                              FROM _vm_roll GROUP BY party)""").fetchall():
        prev = out.get("_pmatch_complete_min")
        out["_pmatch_complete_min"] = float(cmin) if prev is None else min(prev, float(cmin))
    pm = {}
    for party, pmatch in con.execute("""
        SELECT party, 100.0*COUNT(*) FILTER (WHERE keycount=1)/COUNT(*)
        FROM _vm_roll GROUP BY 1""").fetchall():
        pm[party] = float(pmatch)
        out[f"{prefix}_pmatch_{party}"] = float(pmatch)
    if pm:
        out[f"{prefix}_pmatch_spread"] = max(pm.values()) - min(pm.values())
    # widest party gap inside a single age band
    cells = {(pp, b): float(v) for pp, b, v in con.execute("""
        SELECT party, band, 100.0*COUNT(*) FILTER (WHERE keycount=1)/COUNT(*)
        FROM _vm_roll GROUP BY 1, 2""").fetchall()}
    out[f"{prefix}_pmatch_band_spread"] = max(
        max(cells.get((pp, b), 0) for pp in parties) - min(cells.get((pp, b), 0) for pp in parties)
        for b in _STD_BANDS)
    # widest party gap inside any of the 8 largest counties
    top = [c for (c,) in con.execute(
        "SELECT county_name FROM _vm_roll GROUP BY 1 ORDER BY COUNT(*) DESC LIMIT 8").fetchall()]
    ccells = {(pp, c): float(v) for pp, c, v in con.execute("""
        SELECT party, county_name, 100.0*COUNT(*) FILTER (WHERE keycount=1)/COUNT(*)
        FROM _vm_roll GROUP BY 1, 2""").fetchall()}
    out[f"{prefix}_pmatch_county_spread"] = max(
        max(ccells.get((pp, c), 0) for pp in parties) - min(ccells.get((pp, c), 0) for pp in parties)
        for c in top)

    for tag, panel in panels.items():
        con.execute(f"""
            CREATE OR REPLACE TEMP TABLE _vm_don AS
            SELECT r.* FROM _vm_roll r
            WHERE r.state_voter_id IN (SELECT state_voter_id FROM {panel})""")
        for party, n_all, n_uniq, n_don in con.execute("""
            SELECT r.party, COUNT(*), COUNT(*) FILTER (WHERE r.keycount=1),
                   (SELECT COUNT(*) FROM _vm_don d WHERE d.party = r.party)
            FROM _vm_roll r GROUP BY 1""").fetchall():
            k = f"{prefix}_{tag}_inc_{party}"
            out[f"{k}_all"] = n_don / n_all * 1000 if n_all else float("nan")
            out[f"{k}_matchable"] = n_don / n_uniq * 1000 if n_uniq else float("nan")
        # incidence standardized on the joint age x county stratum
        for party, sr in con.execute("""
            WITH pop AS (SELECT band, county_name, party, COUNT(*) n FROM _vm_roll GROUP BY ALL),
            dn AS (SELECT band, county_name, party, COUNT(*) nd FROM _vm_don GROUP BY ALL),
            j AS (SELECT pop.*, COALESCE(dn.nd, 0) nd
                  FROM pop LEFT JOIN dn USING (band, county_name, party)),
            w AS (SELECT band, county_name, SUM(n) wn FROM j GROUP BY ALL)
            SELECT j.party, 1000.0*SUM(w.wn * j.nd / j.n)/SUM(w.wn)
            FROM j JOIN w USING (band, county_name) WHERE j.n > 0 GROUP BY 1""").fetchall():
            out[f"{prefix}_{tag}_inc_{party}_agecty"] = float(sr)
        # share of the standard population a party's strata actually cover — the paper quotes
        # Idaho's small OTHER bloc, the only cell below 100%.
        for party, kept in con.execute("""
            WITH pop AS (SELECT band, county_name, party, COUNT(*) n FROM _vm_roll GROUP BY ALL),
            w AS (SELECT band, county_name, SUM(n) wn FROM pop GROUP BY ALL)
            SELECT pop.party, 100.0*SUM(w.wn)/(SELECT SUM(wn) FROM w)
            FROM pop JOIN w USING (band, county_name) WHERE pop.n > 0 GROUP BY 1""").fetchall():
            out[f"{prefix}_{tag}_inc_{party}_kept"] = float(kept)

def _d_turnout_eligible(con, prefix, panels, roll_sql, out):
    """Turnout gaps under an EXACT eligibility restriction (review #3, action 2).

    roll_sql yields (state_voter_id, band, super, eligible_all, voted, n_eligible). The
    restriction keeps only registrants who existed before the first election in the window, so
    every retained person could have voted in all of them — equalizing opportunity by
    construction rather than by standardizing on a broad tenure band.
    """
    con.execute(f"CREATE OR REPLACE TEMP TABLE _el AS {roll_sql}")
    n_tot, n_pre = con.execute(
        "SELECT COUNT(*), COUNT(*) FILTER (WHERE eligible_all) FROM _el").fetchone()
    out[f"{prefix}_elig_n"] = int(n_pre)
    out[f"{prefix}_elig_tot"] = int(n_tot)
    out[f"{prefix}_elig_pct"] = n_pre / n_tot * 100 if n_tot else float("nan")
    for tag, panel in panels.items():
        con.execute(f"""
            CREATE OR REPLACE TEMP TABLE _elc AS
            SELECT e.*, CASE WHEN a.state_voter_id IS NOT NULL THEN 1 ELSE 0 END dn
            FROM _el e LEFT JOIN {panel} a USING (state_voter_id)""")
        raw = {int(dn): float(sv) for dn, sv in con.execute(
            "SELECT dn, AVG(super) FROM _elc WHERE eligible_all GROUP BY 1").fetchall()}
        out[f"{prefix}_{tag}_egap_raw"] = (raw[1] - raw[0]) * 100
        cell = {(b, int(dn)): float(sv) for b, dn, sv in con.execute(
            "SELECT band, dn, AVG(super) FROM _elc WHERE eligible_all GROUP BY 1, 2").fetchall()}
        pop = {b: n for b, n in con.execute(
            "SELECT band, COUNT(*) FROM _elc WHERE eligible_all GROUP BY 1").fetchall()}

        def _std(who):
            num = sum(pop[b] * cell[(b, who)] for b in _STD_BANDS
                      if pop.get(b) and (b, who) in cell)
            den = sum(pop[b] for b in _STD_BANDS if pop.get(b) and (b, who) in cell)
            return num / den if den else float("nan")
        out[f"{prefix}_{tag}_egap_age"] = (_std(1) - _std(0)) * 100
        for dn, r in con.execute("""
            SELECT dn, AVG(voted*1.0/NULLIF(n_eligible,0)) FROM _elc
            WHERE n_eligible > 0 GROUP BY 1""").fetchall():
            out[f"{prefix}_{tag}_ratio_{'d' if dn else 'n'}"] = float(r) * 100

def _d_xover_bounds(con, prefix, panels, party_case, parties, out):
    """Worst-case bound on the unresolved recipient pool (Finding 3's bound table).

    Every share is of MATCHED donors. The adversarial rival assigns the WHOLE unresolved pool
    to whichever side trails, so `survives` is an assumption-free bound on the row's ordering.

    NB: `matched` cannot be used as a column alias in DuckDB (parser error), which is the same
    class of trap as `rows` and `returning` noted in CLAUDE.md. Aliases here are n_*.
    """
    for tag, panel in panels.items():
        rows = con.execute(f"""
            SELECT {party_case} own, COUNT(*) n_matched,
                   COUNT(*) FILTER (WHERE donor_party <> 'OTHER') n_resolved,
                   COUNT(*) FILTER (WHERE donor_party = 'D_DONOR') n_donly,
                   COUNT(*) FILTER (WHERE donor_party = 'R_DONOR') n_ronly
            FROM {panel} a JOIN vrdb.voters v USING (state_voter_id)
            GROUP BY 1""").fetchall()
        for own, matched, resolved, d1, r1 in rows:
            if own not in parties or not matched:
                continue
            k = f"{prefix}_{tag}_bnd_{own}"
            d_m, r_m = d1 / matched * 100, r1 / matched * 100
            u_m = (matched - resolved) / matched * 100
            out[f"{k}_unres"] = u_m
            out[f"{k}_donly"] = d_m
            out[f"{k}_ronly"] = r_m
            out[f"{k}_adverse"] = (r_m + u_m) if d1 >= r1 else (d_m + u_m)

def _d_conc(con, prefix, panel, out):
    n, tot, t1, t10, g = concentration(con, panel)
    out.update({f"{prefix}_n": n, f"{prefix}_m": tot, f"{prefix}_top1": t1,
                f"{prefix}_top10": t10, f"{prefix}_gini": g})
    out[f"{prefix}_npos"], = con.execute(
        f"SELECT COUNT(*) FROM {panel} WHERE total_donated > 0").fetchone()
    ex1, ties = _exact_top_share(con, panel, 1.0)
    out[f"{prefix}_top1_exact"] = ex1
    out[f"{prefix}_top1_ties"] = ties
    # Standing assertion, not a printed curiosity: if the published NTILE figure and the
    # exact-weight cutoff ever diverge by more than the paper's printed precision, the
    # estimator choice has started to matter and the paper must say which one it used.
    if abs(ex1 - t1) > 0.05:
        out.setdefault("_estimator_warnings", []).append(
            f"{panel}: NTILE top-1% {t1:.3f}% vs exact {ex1:.3f}% "
            f"(delta {ex1 - t1:+.3f} pts) — exceeds the paper's printed precision")

def _d_tier_shares(out):
    """Share of matches contributed by each tier, min-max across the six all-tier panels.

    Read off the RETAINED all-tier panels, which are the only place tier composition is
    observable: the primary panels are single-tier by construction, so a share computed on
    them would be 100% by definition and would check nothing.

    These shares are load-bearing rather than descriptive. The paper's argument for
    dropping the initial-based keys is that they carry near-coin-flip precision on about an
    eighth of all matches, and that eighth is this table.
    """
    tiers = ("STRICT_ZIP5_FULL", "STRICT_ZIP5_MID", "STRICT_ZIP5", "RELAXED_ZIP3_MID")
    seen = {t: [] for t in tiers}
    for db in ("wa_statewide", "ny_statewide", "id_statewide"):
        con = duckdb.connect(str(DATA / f"{db}.duckdb"), read_only=True)
        try:
            for panel in ("voter_donor_affiliation_fec_alltier",
                          "voter_donor_affiliation_state_alltier"):
                rows = dict(con.execute(
                    f"SELECT match_quality, COUNT(*) FROM {panel} GROUP BY 1").fetchall())
                tot = sum(rows.values())
                if not tot:
                    continue
                for t in tiers:
                    seen[t].append(rows.get(t, 0) / tot * 100)
        finally:
            con.close()
    for i, t in enumerate(tiers):
        out[f"tier{i}_share_lo"] = min(seen[t])
        out[f"tier{i}_share_hi"] = max(seen[t])

def _d_bands(con, prefix, panel, age_expr, out):
    """Age-band shares of a matched panel: 18-29 / 30-44 / 45-64 / 65+."""
    band = (f"CASE WHEN {age_expr}<30 THEN 'b1829' WHEN {age_expr}<45 THEN 'b3044' "
            f"WHEN {age_expr}<65 THEN 'b4564' ELSE 'b65' END")
    rows = dict(con.execute(f"""
        SELECT {band} b, COUNT(*) FROM {panel} a JOIN vrdb.voters v USING(state_voter_id)
        WHERE {age_expr} IS NOT NULL GROUP BY 1""").fetchall())
    tot = sum(rows.values())
    for b in ("b1829", "b3044", "b4564", "b65"):
        out[f"{prefix}_{b}"] = rows.get(b, 0) / tot * 100

def _d_refbands(con, prefix, age_expr, where, out):
    """Same bands over a reference population (active roll, or 2024 general voters).

    The `>= 18` floor is load-bearing and was got wrong first time round. NY's roll
    carries ~155K active pre-registrants under 18 at the 2024 general (1.25% of the
    active roll). Leaving them in reads the paper's "all active voters" column as
    19.0/25.2/30.8/24.9 against a published 18.0/25.6/31.2/25.2 — four apparent defects
    that are entirely an artifact of the denominator. The paper's column is an
    *electorate* baseline and excludes them; excluding them here reproduces all four
    cells. The 2024-general columns are unaffected (everyone who voted was 18), which is
    why only one column diverged, and that asymmetry is the tell.
    """
    band = (f"CASE WHEN {age_expr}<30 THEN 'b1829' WHEN {age_expr}<45 THEN 'b3044' "
            f"WHEN {age_expr}<65 THEN 'b4564' ELSE 'b65' END")
    rows = dict(con.execute(f"""
        SELECT {band} b, COUNT(*) FROM vrdb.voters v
        WHERE {age_expr} IS NOT NULL AND {age_expr} >= 18 AND ({where}) GROUP BY 1""").fetchall())
    tot = sum(rows.values())
    for b in ("b1829", "b3044", "b4564", "b65"):
        out[f"{prefix}_{b}"] = rows.get(b, 0) / tot * 100

def _d_overlap(con, state, age_expr, out):
    """Panel overlap: Jaccard, and the within-person 65+ read the paper leans on."""
    f_n, s_n, both = con.execute(f"""
        SELECT (SELECT COUNT(*) FROM {FED}), (SELECT COUNT(*) FROM {STATE}),
               (SELECT COUNT(*) FROM (SELECT state_voter_id FROM {FED}
                 INTERSECT SELECT state_voter_id FROM {STATE}))""").fetchone()
    out[f"{state}_both_n"] = both
    out[f"{state}_jaccard"] = both / (f_n + s_n - both)
    rows = dict((g, p) for g, p in con.execute(f"""
        WITH f AS (SELECT state_voter_id FROM {FED}),
             s AS (SELECT state_voter_id FROM {STATE}),
        grp AS (
          SELECT 'fedonly' g, f.state_voter_id FROM f
            LEFT JOIN s USING (state_voter_id) WHERE s.state_voter_id IS NULL
          UNION ALL SELECT 'stateonly', s.state_voter_id FROM s
            LEFT JOIN f USING (state_voter_id) WHERE f.state_voter_id IS NULL
          UNION ALL SELECT 'both', f.state_voter_id FROM f JOIN s USING (state_voter_id))
        SELECT g, 100.0*COUNT(*) FILTER (WHERE {age_expr} >= 65)/COUNT(*)
        FROM grp JOIN vrdb.voters v USING (state_voter_id)
        WHERE {age_expr} IS NOT NULL GROUP BY 1""").fetchall())
    for g in ("stateonly", "fedonly", "both"):
        out[f"{state}_ovl_{g}"] = float(rows[g])

def _d_xover(con, prefix, panel, bucket_sql, out):
    """Crossover cut: matched / resolved / rate / D-only / R-only / Mixed / $-to-D.

    CONSISTENCY, not independent re-derivation. The recipient-party assignment itself comes
    from the backfill scripts (`backfill_{ny,id}_recipient_party.py`); this reads the
    `d_amount` / `r_amount` columns they wrote. So it cannot validate that assignment — it
    exists to stop the TABLE, the prose beneath it, the limitations bullet and Appendix A
    from disagreeing with each other, which is precisely what happened: the crossover
    section was corrected in July 2026 and three retired resolution rates survived
    downstream of it.

    Denominators, which is where this cut goes wrong: `res_rate` is a share of ALL matched
    donors in the party; D-only / R-only / Mixed are shares of the RESOLVED subset only;
    `$-to-D` is a share of party-resolved DOLLARS. Mixing them is how the paper once read
    a Republican-row rate as the panel aggregate.
    """
    for b, matched, resolved, d_only, r_only, mixed, dol_d in con.execute(f"""
        SELECT {bucket_sql} b, COUNT(*), COUNT(*) FILTER (WHERE d_amount+r_amount>0),
               100.0*COUNT(*) FILTER (WHERE d_amount>0 AND r_amount=0)
                   /NULLIF(COUNT(*) FILTER (WHERE d_amount+r_amount>0),0),
               100.0*COUNT(*) FILTER (WHERE r_amount>0 AND d_amount=0)
                   /NULLIF(COUNT(*) FILTER (WHERE d_amount+r_amount>0),0),
               100.0*COUNT(*) FILTER (WHERE d_amount>0 AND r_amount>0)
                   /NULLIF(COUNT(*) FILTER (WHERE d_amount+r_amount>0),0),
               100.0*SUM(d_amount)/NULLIF(SUM(d_amount+r_amount),0)
        FROM {panel} a JOIN vrdb.voters v USING(state_voter_id) GROUP BY 1""").fetchall():
        out[f"{prefix}_x_{b}_matched"] = int(matched)
        out[f"{prefix}_x_{b}_resolved"] = int(resolved)
        out[f"{prefix}_x_{b}_rate"] = resolved / matched * 100
        out[f"{prefix}_x_{b}_donly"] = float(d_only or 0)
        out[f"{prefix}_x_{b}_ronly"] = float(r_only or 0)
        out[f"{prefix}_x_{b}_mixed"] = float(mixed or 0)
        out[f"{prefix}_x_{b}_dold"] = float(dol_d or 0)
    agg, = con.execute(f"""
        SELECT 100.0*COUNT(*) FILTER (WHERE d_amount+r_amount>0)/COUNT(*)
        FROM {panel}""").fetchone()
    out[f"{prefix}_x_agg"] = float(agg)
    # The complement of DEM's $-to-D: the share of resolved Democratic dollars that went to
    # Republicans. The paper quotes it directly in the withdrawn-"3.6x" note.
    if f"{prefix}_x_DEM_dold" in out:
        out[f"_{prefix}_dem_dol_to_r"] = 100.0 - out[f"{prefix}_x_DEM_dold"]

def _d_counties(con, prefix, panel, out, roll_where="status_code='A'"):
    """Largest-donor-county cut: dollar share, roll share, multiplier, top-3 share.

    Counties for every state (2026-07-28, external review). Earlier drafts compared two
    Seattle ZIP3s against single counties in NY and ID, which is not a like-for-like unit.
    The multiplier — dollar share / active-roll share — is the load-bearing number, because
    raw share confuses a LARGE county with a CONCENTRATED one: King holds 28.3% of
    Washington's roll, so its 58.2% of federal dollars is 2.06x, while Manhattan holds 8.1%
    of New York's and its 48.5% is 5.96x.
    """
    roll = dict(con.execute(f"""
        SELECT county_name, COUNT(*) FROM vrdb.voters WHERE {roll_where} GROUP BY 1
    """).fetchall())
    rt = sum(roll.values())
    rows = con.execute(f"""
        SELECT v.county_name,
               100.0*SUM(a.total_donated)/SUM(SUM(a.total_donated)) OVER () pct,
               COUNT(*) n
        FROM {panel} a JOIN vrdb.voters v USING(state_voter_id)
        WHERE a.total_donated > 0 GROUP BY 1 ORDER BY pct DESC LIMIT 3""").fetchall()
    out[f"{prefix}_cty_top3"] = sum(float(p) for _, p, _ in rows)
    for i, (cty, pct, n) in enumerate(rows):
        rs = roll.get(cty, 0) / rt * 100
        out[f"{prefix}_cty{i}_pct"] = float(pct)
        out[f"{prefix}_cty{i}_roll"] = rs
        out[f"{prefix}_cty{i}_mult"] = float(pct) / rs if rs else 0.0
        out[f"{prefix}_cty{i}_n"] = int(n)

def _d_named_county(con, prefix, panel, county, out, roll_where="status_code='A'"):
    """Same cut for one named county — Blaine's 7.83x is the paper's sharpest single figure."""
    rs, = con.execute(f"""
        SELECT 100.0*COUNT(*) FILTER (WHERE county_name='{county}')/COUNT(*)
        FROM vrdb.voters WHERE {roll_where}""").fetchone()
    pct, n = con.execute(f"""
        SELECT 100.0*SUM(a.total_donated) FILTER (WHERE v.county_name='{county}')
               /SUM(a.total_donated),
               COUNT(*) FILTER (WHERE v.county_name='{county}')
        FROM {panel} a JOIN vrdb.voters v USING(state_voter_id)
        WHERE a.total_donated > 0""").fetchone()
    key = county.lower().replace(" ", "")
    out[f"{prefix}_{key}_pct"] = float(pct)
    out[f"{prefix}_{key}_roll"] = float(rs)
    out[f"{prefix}_{key}_mult"] = float(pct) / float(rs) if rs else 0.0
    out[f"{prefix}_{key}_n"] = int(n)

def _d_party(con, prefix, panel, bucket_sql, out):
    """Registration / donor / skew / dollar share by party of record, one panel."""
    reg = dict(con.execute(f"""
        SELECT {bucket_sql} b, COUNT(*) FROM vrdb.voters v WHERE status_code='A'
        GROUP BY 1""").fetchall())
    don = dict(con.execute(f"""
        SELECT {bucket_sql} b, COUNT(*) FROM {panel} a
        JOIN vrdb.voters v USING(state_voter_id) GROUP BY 1""").fetchall())
    dol = dict(con.execute(f"""
        SELECT {bucket_sql} b, SUM(a.total_donated) FROM {panel} a
        JOIN vrdb.voters v USING(state_voter_id) GROUP BY 1""").fetchall())
    rt, dt = sum(reg.values()), sum(don.values())
    lt = sum(float(v) for v in dol.values() if v)
    for b in reg:
        rp, dp = reg[b] / rt * 100, don.get(b, 0) / dt * 100
        out[f"{prefix}_reg_{b}"] = rp
        out[f"{prefix}_don_{b}"] = dp
        out[f"{prefix}_skew_{b}"] = dp - rp
        out[f"{prefix}_dol_{b}"] = float(dol.get(b, 0) or 0) / lt * 100

_G_NOT_UNITEMIZED = ("UPPER(contributor_name) NOT IN "
                     "('SMALL CONTRIBUTIONS', 'UNITEMIZED', 'ANONYMOUS')")

def _d_appendix_g(out):
    """Appendix G's G2 bunching counts — the heuristic-free part of that appendix.

    G3's layer table and G4's clipping table are NOT re-derived here. Reproducing them
    requires diag_contribution_limits.py's ORG_RE person/organization name heuristic and its
    `contributor_state` residence filter, and reimplementing those would copy the appendix's
    own instrument into the verifier rather than check it independently — the failure mode this
    file exists to avoid. A first attempt at it disagreed with every published cell, and the
    basis error was mine, not the paper's (see CLAUDE.md's rule about suspecting your own basis
    before calling a mismatch a defect). Those cells are therefore covered by written
    exemptions naming that script, the same convention used for the bootstrap intervals and the
    frozen validation ledgers. The bunching counts below need no heuristic: they are exact
    amount matches on one layer.
    """
    idc = duckdb.connect(str(DATA / "id_statewide.duckdb"), read_only=True)
    id_state = (f"contribution_id LIKE 'SUNSHINE:%' AND contribution_amount > 0 "
                f"AND {_G_NOT_UNITEMIZED}")
    # G2 bunching on round Sunshine values
    for amt in (750, 900, 999, 1000, 1001, 1100, 5000, 5001):
        n, = idc.execute(
            f"SELECT COUNT(*) FROM individual_contributions "
            f"WHERE {id_state} AND contribution_amount = {amt}").fetchone()
        out[f"g_bunch_{amt}"] = int(n)
    idc.close()

def derive_prose():
    """Every value the prose probes assert. From-scratch SQL, own read-only handles."""
    d = {}

    # ---------------------------------------------------------------- WASHINGTON
    wa = duckdb.connect(str(DATA / "wa_statewide.duckdb"), read_only=True)
    wa.execute(f"ATTACH '{DATA / 'wa_vrdb.duckdb'}' AS vrdb (READ_ONLY)")
    _d_conc(wa, "wa_fed", FED, d)
    _d_conc(wa, "wa_state", STATE, d)
    _d_conc(wa, "wa_pooled", POOLED, d)
    d["wa_vote_records_m"] = wa.execute(
        "SELECT COUNT(*) / 1e6 FROM vrdb.voting_history").fetchone()[0]
    _d_tier_shares(d)
    # Generation multipliers = donor share / roll share, roll from the ld-scope of
    # voter_scores (one row per voter — the cd scope is still incomplete).
    roll = dict(wa.execute("""
        SELECT age_cohort, COUNT(*) FROM voter_scores
        WHERE LEFT(district_id,2)='ld' AND age_cohort IS NOT NULL GROUP BY 1""").fetchall())
    rt = sum(roll.values())
    for tag, panel in (("fed", FED), ("state", STATE)):
        don = dict(wa.execute(f"""
            SELECT s.age_cohort, COUNT(*) FROM voter_scores s JOIN {panel} a
              USING(state_voter_id)
            WHERE LEFT(s.district_id,2)='ld' AND s.age_cohort IS NOT NULL
            GROUP BY 1""").fetchall())
        dt = sum(don.values())
        for g in _GENS:
            key = g.lower().replace(" ", "")
            d[f"wa_{tag}_mult_{key}"] = (don.get(g, 0) / dt) / (roll.get(g, 0) / rt)
    _d_overlap(wa, "wa", _AGE_2024, d)
    # 65+ share per panel, and on the retained all-tier snapshot. Finding 1's
    # tier-sensitivity sentence quotes the primary -> all-tier move in all three states, so
    # both halves have to be derivable or that sentence is unverifiable.
    for tag, panel in (("fed", FED), ("state", STATE),
                       ("fedall", FED_ALL), ("stateall", STATE_ALL)):
        if has_table(wa, panel):
            _d_bands(wa, f"wa_{tag}", panel, _AGE_2024, d)
    # Largest-donor-COUNTY cut, per panel (counties for all three states since 2026-07-28).
    for tag, panel in (("fed", FED), ("state", STATE)):
        _d_counties(wa, f"wa_{tag}", panel, d)
    # Give<->vote stacking, per panel.
    for tag, panel in (("fed", FED), ("state", STATE)):
        for donor, sup, prop in wa.execute(f"""
            WITH roll AS (SELECT DISTINCT state_voter_id, is_super_voter, turnout_propensity
                          FROM voter_scores WHERE LEFT(district_id,2)='ld'),
            f AS (SELECT r.*, CASE WHEN a.state_voter_id IS NOT NULL THEN 1 ELSE 0 END dn
                  FROM roll r LEFT JOIN {panel} a USING(state_voter_id))
            SELECT dn, 100.0*AVG(CASE WHEN is_super_voter THEN 1.0 ELSE 0 END),
                   AVG(turnout_propensity) FROM f GROUP BY dn""").fetchall():
            who = "d" if donor else "n"
            d[f"wa_{tag}_super_{who}"] = float(sup)
            d[f"wa_{tag}_prop_{who}"] = float(prop)
    # Finding 2's positive-total denominator note: WA's state panel is the only one where the
    # matched count and the estimator's denominator differ.
    for tag in ("fed", "state"):
        gap = d[f"wa_{tag}_n"] - d[f"wa_{tag}_npos"]
        d[f"wa_{tag}_nonpos"] = gap
        d[f"wa_{tag}_nonpos_pct"] = gap / d[f"wa_{tag}_n"] * 100
    # Finding 4's standardization. The published `is_super_voter` bakes in an 8-year tenure
    # requirement, so a tenure standardization on it conditions on part of its own definition;
    # the paper's table therefore uses a tenure-free WA measure (voted both the 2022 and 2024
    # generals — the only two the VRDB export's rolling window carries). Both are derived so
    # the paper's disclosure of the problem is checkable.
    _d_turnout_std(wa, "wa_sv", f"""
        WITH roll AS (SELECT DISTINCT state_voter_id, is_super_voter
                      FROM voter_scores WHERE LEFT(district_id,2)='ld')
        SELECT r.state_voter_id, {_std_band_sql(_AGE_2024)} band, {_tenure_sql()} tenure,
               CASE WHEN r.is_super_voter THEN 1.0 ELSE 0.0 END super
        FROM roll r JOIN vrdb.voters v USING (state_voter_id)
        WHERE {_AGE_2024} IS NOT NULL AND {_AGE_2024} >= 18""",
        {"fed": FED, "state": STATE}, d)
    _d_turnout_eligible(wa, "wa", {"fed": FED, "state": STATE}, f"""
        WITH roll AS (SELECT DISTINCT state_voter_id
                      FROM voter_scores WHERE LEFT(district_id,2)='ld'),
        gen AS (SELECT state_voter_id, COUNT(DISTINCT YEAR(election_date)) g
                FROM vrdb.voting_history
                WHERE MONTH(election_date)=11 AND YEAR(election_date) IN (2022,2024)
                GROUP BY 1)
        SELECT r.state_voter_id, {_std_band_sql(_AGE_2024)} band,
               CASE WHEN COALESCE(gen.g,0) >= 2 THEN 1.0 ELSE 0.0 END super,
               (v.registration_date <= DATE '2022-11-08') eligible_all,
               COALESCE(gen.g, 0) voted,
               (CASE WHEN v.registration_date <= DATE '2022-11-08' THEN 2
                     WHEN v.registration_date <= DATE '2024-11-05' THEN 1
                     ELSE 0 END) n_eligible
        FROM roll r JOIN vrdb.voters v USING (state_voter_id)
        LEFT JOIN gen ON gen.state_voter_id = r.state_voter_id
        WHERE {_AGE_2024} IS NOT NULL AND {_AGE_2024} >= 18""", d)
    _d_turnout_std(wa, "wa_g2", f"""
        WITH roll AS (SELECT DISTINCT state_voter_id
                      FROM voter_scores WHERE LEFT(district_id,2)='ld'),
        gen AS (SELECT state_voter_id, COUNT(DISTINCT YEAR(election_date)) g
                FROM vrdb.voting_history
                WHERE MONTH(election_date)=11 AND YEAR(election_date) IN (2022, 2024)
                GROUP BY 1)
        SELECT r.state_voter_id, {_std_band_sql(_AGE_2024)} band, {_tenure_sql()} tenure,
               CASE WHEN COALESCE(gen.g,0) >= 2 THEN 1.0 ELSE 0.0 END super
        FROM roll r JOIN vrdb.voters v USING (state_voter_id)
        LEFT JOIN gen ON gen.state_voter_id = r.state_voter_id
        WHERE {_AGE_2024} IS NOT NULL AND {_AGE_2024} >= 18""",
        {"fed": FED, "state": STATE}, d)
    wa.close()

    # ------------------------------------------------------------------ NEW YORK
    ny = duckdb.connect(str(DATA / "ny_statewide.duckdb"), read_only=True)
    ny.execute(f"ATTACH '{DATA / 'ny_vrdb.duckdb'}' AS vrdb (READ_ONLY)")
    _d_conc(ny, "ny_fed", FED, d)
    _d_conc(ny, "ny_state", STATE, d)
    _d_bands(ny, "ny_fed", FED, _AGE_2024, d)
    _d_bands(ny, "ny_state", STATE, _AGE_2024, d)
    if has_table(ny, FED_ALL):
        _d_bands(ny, "ny_fedall", FED_ALL, _AGE_2024, d)
    d["ny_roll_active"], d["ny_roll_total"] = ny.execute(
        "SELECT COUNT(*) FILTER (WHERE status_code='A'), COUNT(*) FROM vrdb.voters"
    ).fetchone()
    _d_refbands(ny, "ny_active", _AGE_2024, "v.status_code='A'", d)
    _d_refbands(ny, "ny_ge24", _AGE_2024,
                "v.state_voter_id IN (SELECT state_voter_id FROM vrdb.voter_participation "
                "WHERE kind='GENERAL' AND election_year=2024)", d)
    _d_overlap(ny, "ny", _AGE_2024, d)
    NYP = ("CASE WHEN v.party='DEM' THEN 'DEM' WHEN v.party='REP' THEN 'REP' "
           "WHEN v.party='BLK' THEN 'NOPARTY' ELSE 'OTHER' END")
    _d_party(ny, "ny_fed", FED, NYP, d)
    _d_party(ny, "ny_state", STATE, NYP, d)
    _d_xover(ny, "ny_fed", FED, NYP, d)
    _d_xover(ny, "ny_state", STATE, NYP, d)
    # Geography: counties, with the roll-share multiplier (the paper's sharpest cut).
    for tag, panel in (("fed", FED), ("state", STATE)):
        _d_counties(ny, f"ny_{tag}", panel, d)
    # Appendix E's competitiveness bands. |predicted margin| over the NY CDs, the same
    # construction as diag_ny_electorate_extras.py — except that script reads the POOLED
    # match, so these are recomputed per panel.
    _NY_BAND = """
        WITH cd_comp AS (
            SELECT TRY_CAST(regexp_extract(district_id,'[0-9]+') AS INT) cd,
                   AVG(ABS(predicted_margin)) absm
            FROM forecast_predictions WHERE state='NY' AND district_id LIKE 'cd%'
            GROUP BY 1),
        band AS (SELECT cd, CASE WHEN absm<5 THEN 'tossup' WHEN absm<10 THEN 'lean'
                                 WHEN absm<20 THEN 'likely' ELSE 'solid' END b
                 FROM cd_comp)"""
    for tag, panel in (("fed", FED), ("state", STATE)):
        for b, n, dp in ny.execute(f"""{_NY_BAND},
            donors AS (SELECT TRY_CAST(v.congressional_district AS INT) cd, {NYP} party
                       FROM {panel} a JOIN vrdb.voters v USING(state_voter_id)
                       WHERE v.congressional_district IS NOT NULL)
            SELECT b.b, COUNT(*), 100.0*COUNT(*) FILTER (WHERE party='DEM')/COUNT(*)
            FROM donors d JOIN band b ON b.cd = d.cd GROUP BY 1""").fetchall():
            d[f"ny_{tag}_band_{b}_n"] = int(n)
            d[f"ny_{tag}_band_{b}_d"] = float(dp)
    for b, dp in ny.execute(f"""{_NY_BAND}
        SELECT b.b, 100.0*COUNT(*) FILTER (WHERE {NYP}='DEM')/COUNT(*)
        FROM vrdb.voters v JOIN band b ON b.cd = TRY_CAST(v.congressional_district AS INT)
        WHERE v.status_code='A' GROUP BY 1""").fetchall():
        d[f"ny_reg_band_{b}_d"] = float(dp)
    # Generals voted of the last four, donors vs non-donors, per panel.
    for tag, panel in (("fed", FED), ("state", STATE)):
        for donor, avg, sup in ny.execute(f"""
            WITH gen AS (SELECT state_voter_id, COUNT(DISTINCT election_year) g
                         FROM vrdb.voter_participation
                         WHERE kind='GENERAL' AND election_year IN (2018,2020,2022,2024)
                         GROUP BY 1),
            roll AS (SELECT COALESCE(gen.g,0) g,
                            CASE WHEN a.state_voter_id IS NOT NULL THEN 1 ELSE 0 END dn
                     FROM vrdb.voters v LEFT JOIN gen USING (state_voter_id)
                     LEFT JOIN {panel} a USING (state_voter_id)
                     WHERE v.status_code='A')
            SELECT dn, AVG(g), 100.0*AVG(CASE WHEN g>=3 THEN 1.0 ELSE 0 END)
            FROM roll GROUP BY dn""").fetchall():
            who = "d" if donor else "n"
            d[f"ny_{tag}_gen_{who}"] = float(avg)
            d[f"ny_{tag}_sup_{who}"] = float(sup)
    _NYPV = NY_PARTY.replace("party=", "v.party=")
    _d_age_std_party(ny, "ny", {"fed": FED, "state": STATE}, _AGE_2024, _NYPV,
                     ("DEM", "REP", "NOPARTY", "OTHER"), d)
    _d_xover_bounds(ny, "ny", {"fed": FED, "state": STATE}, _NYPV,
                    ("DEM", "REP", "NOPARTY", "OTHER"), d)
    _d_party_matchability(ny, "ny", {"fed": FED, "state": STATE}, _AGE_2024, _NYPV,
                          ("DEM", "REP", "NOPARTY", "OTHER"), d)
    _d_turnout_eligible(ny, "ny", {"fed": FED, "state": STATE}, f"""
        WITH gen AS (SELECT state_voter_id, COUNT(DISTINCT election_year) g
                     FROM vrdb.voter_participation
                     WHERE kind='GENERAL' AND election_year IN (2018,2020,2022,2024)
                     GROUP BY 1)
        SELECT v.state_voter_id, {_std_band_sql(_AGE_2024)} band,
               CASE WHEN COALESCE(gen.g,0) >= 3 THEN 1.0 ELSE 0.0 END super,
               (v.registration_date <= DATE '2018-11-06') eligible_all,
               COALESCE(gen.g, 0) voted,
               (CASE WHEN v.registration_date <= DATE '2018-11-06' THEN 4
                     WHEN v.registration_date <= DATE '2020-11-03' THEN 3
                     WHEN v.registration_date <= DATE '2022-11-08' THEN 2
                     WHEN v.registration_date <= DATE '2024-11-05' THEN 1
                     ELSE 0 END) n_eligible
        FROM vrdb.voters v LEFT JOIN gen USING (state_voter_id)
        WHERE v.status_code='A' AND {_AGE_2024} IS NOT NULL AND {_AGE_2024} >= 18""", d)
    _d_turnout_std(ny, "ny", f"""
        WITH gen AS (SELECT state_voter_id, COUNT(DISTINCT election_year) g
                     FROM vrdb.voter_participation
                     WHERE kind='GENERAL' AND election_year IN (2018,2020,2022,2024)
                     GROUP BY 1)
        SELECT v.state_voter_id, {_std_band_sql(_AGE_2024)} band, {_tenure_sql()} tenure,
               CASE WHEN COALESCE(gen.g,0) >= 3 THEN 1.0 ELSE 0.0 END super
        FROM vrdb.voters v LEFT JOIN gen USING (state_voter_id)
        WHERE v.status_code='A' AND {_AGE_2024} IS NOT NULL AND {_AGE_2024} >= 18""",
        {"fed": FED, "state": STATE}, d)
    ny.close()

    # --------------------------------------------------------------------- IDAHO
    ic = duckdb.connect(str(DATA / "id_statewide.duckdb"), read_only=True)
    ic.execute(f"ATTACH '{DATA / 'id_vrdb.duckdb'}' AS vrdb (READ_ONLY)")
    _d_conc(ic, "id_fed", FED, d)
    _d_conc(ic, "id_state", STATE, d)
    _d_bands(ic, "id_fed", FED, "v.age", d)
    _d_bands(ic, "id_state", STATE, "v.age", d)
    if has_table(ic, FED_ALL):
        _d_bands(ic, "id_fedall", FED_ALL, "v.age", d)
    _d_refbands(ic, "id_roll", "v.age", "1=1", d)
    _d_refbands(ic, "id_ge24", "v.age",
                "v.state_voter_id IN (SELECT state_voter_id FROM vrdb.voter_participation "
                "WHERE kind='GENERAL' AND election_year=2024)", d)
    _d_overlap(ic, "id", "v.age", d)
    IDP = ("CASE WHEN v.party='REP' THEN 'REP' WHEN v.party='DEM' THEN 'DEM' "
           "WHEN v.party='UNA' THEN 'UNAFF' ELSE 'OTHER' END")
    _d_party(ic, "id_fed", FED, IDP, d)
    _d_party(ic, "id_state", STATE, IDP, d)
    if has_table(ic, FED + "_aligned"):
        _d_party(ic, "id_fedal", FED + "_aligned", IDP, d)
    _d_xover(ic, "id_fed", FED, IDP, d)
    _d_xover(ic, "id_state", STATE, IDP, d)
    _d_age_std_party(ic, "id", {"fed": FED, "state": STATE}, "v.age", IDP,
                     ("REP", "DEM", "UNAFF", "OTHER"), d)
    _d_party_matchability(ic, "id", {"fed": FED, "state": STATE}, "v.age", IDP,
                          ("REP", "DEM", "UNAFF", "OTHER"), d)
    # Four-band version, for the paper's note on how much the band choice matters.
    _d_age_std_party(ic, "idc", {"fed": FED, "state": STATE}, "v.age", IDP,
                     ("REP", "DEM", "UNAFF", "OTHER"), d, fine=False)
    _d_xover_bounds(ic, "id", {"fed": FED, "state": STATE}, IDP,
                    ("REP", "DEM", "UNAFF", "OTHER"), d)
    for tag, panel in (("fed", FED), ("state", STATE)):
        _d_counties(ic, f"id_{tag}", panel, d, roll_where="1=1")
    # Blaine is named explicitly: 1.5% of the roll against 11.4% of federal dollars is the
    # largest single-county disproportion in the paper, and it is not the largest county so
    # the top-3 cut would not always surface it.
    _d_named_county(ic, "id_fed", FED, "BLAINE", d, roll_where="1=1")
    # F4c composition shares — denominator-free, so survivorship on the current roll
    # cannot inflate them the way a turnout RATE would.
    for pop, n, rep, dem, una in ic.execute("""
        WITH roll AS (SELECT state_voter_id, party FROM vrdb.voters),
        ge AS (SELECT DISTINCT state_voter_id FROM vrdb.voter_participation
               WHERE election_year=2024 AND kind='GENERAL'),
        pr AS (SELECT DISTINCT state_voter_id FROM vrdb.voter_participation
               WHERE election_year=2024 AND kind='PRIMARY'),
        pops AS (
          SELECT 'roll' pop, party FROM roll
          UNION ALL SELECT 'ge', r.party FROM roll r JOIN ge USING (state_voter_id)
          UNION ALL SELECT 'pr', r.party FROM roll r JOIN pr USING (state_voter_id))
        SELECT pop, COUNT(*),
               100.0*COUNT(*) FILTER (WHERE party='REP')/COUNT(*),
               100.0*COUNT(*) FILTER (WHERE party='DEM')/COUNT(*),
               100.0*COUNT(*) FILTER (WHERE party='UNA')/COUNT(*)
        FROM pops GROUP BY 1""").fetchall():
        d[f"id_pop_{pop}_n"] = int(n)
        d[f"id_pop_{pop}_rep"] = float(rep)
        d[f"id_pop_{pop}_dem"] = float(dem)
        d[f"id_pop_{pop}_una"] = float(una)
    # Appendix E's Idaho district-safety cut, on Section V's registration bands (net R-D
    # >= 40 = Solid R). State panel, matching who-decides-idaho.md §VII.
    for band, lds, n, rep, dem in ic.execute(f"""
        WITH ld AS (SELECT legislative_district dd,
               100.0*COUNT(*) FILTER (WHERE party='REP')/COUNT(*)
             - 100.0*COUNT(*) FILTER (WHERE party='DEM')/COUNT(*) net
            FROM vrdb.voters WHERE legislative_district IS NOT NULL GROUP BY 1),
        b AS (SELECT dd, CASE WHEN net>=40 THEN 'solid' ELSE 'adj' END band FROM ld)
        SELECT b.band, COUNT(DISTINCT b.dd), COUNT(*),
               100.0*COUNT(*) FILTER (WHERE v.party='REP')/COUNT(*),
               100.0*COUNT(*) FILTER (WHERE v.party='DEM')/COUNT(*)
        FROM {STATE} a JOIN vrdb.voters v USING(state_voter_id)
        JOIN b ON b.dd = v.legislative_district GROUP BY 1""").fetchall():
        d[f"id_{band}_lds"] = int(lds)
        d[f"id_{band}_n"] = int(n)
        d[f"id_{band}_rep"] = float(rep)
        d[f"id_{band}_dem"] = float(dem)
    # Period-aligned federal panel, when built — the paper's period-misalignment rebuttal.
    if has_table(ic, FED + "_aligned"):
        _d_conc(ic, "id_fedal", FED + "_aligned", d)
        _d_bands(ic, "id_fedal", FED + "_aligned", "v.age", d)
    ic.close()

    # ---------------------------------------------- below-floor disclosure practice
    # A statutory reporting threshold is not the same thing as the contents of the file.
    # Every floor is a per-donor AGGREGATE, so a donor who crosses it has all their gifts
    # itemized including sub-floor ones, and committees also disclose below what is
    # required. The paper previously said each panel "omits giving below its own threshold",
    # which is false for all four layers — these are the figures that establish it.
    for st, db, prefix, floor, key in (
        ("WA", "wa_statewide", "FEC", 200, "fed"),
        ("WA", "wa_statewide", "PDC", 100, "wa_pdc"),
        ("NY", "ny_statewide", "NY", 99, "ny_state"),
        ("ID", "id_statewide", "SUNSHINE", 50, "id_state"),
    ):
        con = duckdb.connect(str(DATA / f"{db}.duckdb"), read_only=True)
        n, below = con.execute(f"""
            SELECT COUNT(*), COUNT(*) FILTER (WHERE contribution_amount <= {floor})
            FROM individual_contributions
            WHERE contribution_id LIKE '{prefix}:%' AND contribution_amount > 0""").fetchone()
        d[f"belowfloor_{key}_pct"] = below / n * 100
        con.close()
    # Donor-level, on the built WA state panel — the level the estimator works at.
    wa2 = duckdb.connect(str(DATA / "wa_statewide.duckdb"), read_only=True)
    n, b100, b25, mn = wa2.execute(f"""
        SELECT COUNT(*), COUNT(*) FILTER (WHERE total_donated <= 100),
               COUNT(*) FILTER (WHERE total_donated <= 25), MIN(total_donated)
        FROM {STATE} WHERE total_donated > 0""").fetchone()
    d["wa_state_donor_le100_pct"] = b100 / n * 100
    d["wa_state_donor_le25_pct"] = b25 / n * 100
    d["wa_state_donor_min"] = float(mn)
    wa2.close()

    # ---------------------------------------------- harmonized panel comparison ($200)
    # External review item 3. The floors differ, so the panels observe different donor
    # populations; restricting every panel to a donor aggregate above the FEDERAL floor is
    # the direct test. Both the age gap and the layer-concentration ordering move, so these
    # figures are load-bearing and probed rather than left to diag_panel_harmonized.py.
    for st, db, vr, age in (("wa", "wa_statewide", "wa_vrdb", _AGE_2024),
                            ("ny", "ny_statewide", "ny_vrdb", _AGE_2024),
                            ("id", "id_statewide", "id_vrdb", "v.age")):
        con = duckdb.connect(str(DATA / f"{db}.duckdb"), read_only=True)
        con.execute(f"ATTACH '{DATA / (vr + '.duckdb')}' AS vrdb (READ_ONLY)")
        for tag, panel in (("fed", FED), ("state", STATE)):
            n, p65 = con.execute(f"""
                SELECT COUNT(*), 100.0*COUNT(*) FILTER (WHERE {age} >= 65)/COUNT(*)
                FROM {panel} a JOIN vrdb.voters v USING(state_voter_id)
                WHERE a.total_donated > 200 AND {age} IS NOT NULL""").fetchone()
            t1, = con.execute(f"""
                WITH r AS (SELECT total_donated t,
                                  NTILE(100) OVER (ORDER BY total_donated DESC) p
                           FROM {panel} WHERE total_donated > 200)
                SELECT 100.0*SUM(t) FILTER (WHERE p=1)/SUM(t) FROM r""").fetchone()
            d[f"{st}_{tag}_h200_n"] = int(n)
            d[f"{st}_{tag}_h200_b65"] = float(p65)
            d[f"{st}_{tag}_h200_top1"] = float(t1)
        # within-person group 65+ shares under the same floor
        for g, n, p in con.execute(f"""
            WITH f AS (SELECT state_voter_id FROM {FED} WHERE total_donated > 200),
                 s AS (SELECT state_voter_id FROM {STATE} WHERE total_donated > 200),
            grp AS (
              SELECT 'stateonly' g, s.state_voter_id FROM s
                LEFT JOIN f USING (state_voter_id) WHERE f.state_voter_id IS NULL
              UNION ALL SELECT 'fedonly', f.state_voter_id FROM f
                LEFT JOIN s USING (state_voter_id) WHERE s.state_voter_id IS NULL
              UNION ALL SELECT 'both', f.state_voter_id FROM f JOIN s USING (state_voter_id))
            SELECT g, COUNT(*), 100.0*COUNT(*) FILTER (WHERE {age} >= 65)/COUNT(*)
            FROM grp JOIN vrdb.voters v USING (state_voter_id)
            WHERE {age} IS NOT NULL GROUP BY 1""").fetchall():
            d[f"{st}_h200_{g}_b65"] = float(p)
            d[f"{st}_h200_{g}_n"] = int(n)
        con.close()
    # Gaps and ordering deltas the paper states directly.
    for st in ("wa", "ny", "id"):
        d[f"{st}_gap_built"] = d[f"{st}_fed_b65"] - d[f"{st}_state_b65"]
        d[f"{st}_gap_h200"] = d[f"{st}_fed_h200_b65"] - d[f"{st}_state_h200_b65"]
        d[f"{st}_conc_built"] = d[f"{st}_state_top1"] - d[f"{st}_fed_top1"]
        d[f"{st}_conc_h200"] = d[f"{st}_state_h200_top1"] - d[f"{st}_fed_h200_top1"]
        if d[f"{st}_gap_built"]:
            d[f"{st}_gap_floorpct"] = abs(
                d[f"{st}_gap_built"] - d[f"{st}_gap_h200"]) / d[f"{st}_gap_built"] * 100
        d[f"_neg_{st}_conc_h200"] = -d[f"{st}_conc_h200"]
        d[f"_neg_{st}_conc_built"] = -d[f"{st}_conc_built"]

    # ---- Appendix G's derived tables (added to the audit 2026-07-29).
    # Layer concentration on the raw contribution files (donor = name + zip5), and the
    # stylized clipping cuts. Derived here rather than trusted to
    # diag_contribution_limits.py, which is the script the appendix cites.
    _d_appendix_g(d)

    # Appendix E's "state panel draws on N more people" claim.
    d["ny_panel_gap_k"] = d["ny_state_n"] - d["ny_fed_n"]

    # Some prose sets a negative figure as "−8.1", so the probe's capture group holds the
    # MAGNITUDE with the sign consumed by the surrounding literal. Mirror every standardization
    # key as an `_abs` twin rather than teaching the comparator about signs it cannot see.
    for k in [k for k in d if "_std_" in k or "_bnd_" in k]:
        v = d[k]
        if isinstance(v, (int, float)):
            d[f"_{k}_abs"] = abs(v)
    # Idaho's prevalence ratio: registered Democrats vs Republicans, per 1,000 registrants,
    # across the two panels. The paper quotes the range.
    for _t in ("fed", "state"):
        d[f"_id_{_t}_prev_ratio"] = (d[f"id_{_t}_std_DEM_prev"]
                                     / d[f"id_{_t}_std_REP_prev"])
    for _t in ("fed", "state"):
        d[f"_id_{_t}_inc_ratio_agecty"] = (d[f"id_{_t}_inc_DEM_agecty"]
                                           / d[f"id_{_t}_inc_REP_agecty"])
    # DEM/REP raw incidence ratios, and the matchability spread expressed multiplicatively
    for _st in ("ny", "id"):
        for _t in ("fed", "state"):
            d[f"_{_st}_{_t}_inc_ratio"] = (d[f"{_st}_{_t}_inc_DEM_all"]
                                           / d[f"{_st}_{_t}_inc_REP_all"])
        d[f"_{_st}_pmatch_spread_mult"] = 1.0 + d[f"{_st}_pmatch_spread"] / 100.0
    # unaffiliated-to-Democratic raw incidence ratio, across all four panels
    _ud = sorted(d[f"{st}_{tg}_inc_{ua}_all"] / d[f"{st}_{tg}_inc_DEM_all"] * 100
                 for st, ua in (("ny", "NOPARTY"), ("id", "UNAFF"))
                 for tg in ("fed", "state"))
    d["_unaff_dem_ratio_lo"], d["_unaff_dem_ratio_hi"] = _ud[0], _ud[-1]
    # the two adjusted-gap ranges the prose contrasts
    _eg = sorted(d[f"{s_}_{t_}_egap_age"] for s_ in ("ny", "wa") for t_ in ("fed", "state"))
    d["_egap_age_lo"], d["_egap_age_hi"] = _eg[0], _eg[-1]
    _tg = sorted([d["ny_fed_tgap_ten"], d["ny_state_tgap_ten"],
                  d["wa_g2_fed_tgap_ten"], d["wa_g2_state_tgap_ten"]])
    d["_tgap_ten_lo"], d["_tgap_ten_hi"] = _tg[0], _tg[-1]
    _r = sorted(d[f"_id_{t}_prev_ratio"] for t in ("fed", "state"))
    d["_id_prev_ratio_lo"], d["_id_prev_ratio_hi"] = _r[0], _r[-1]

    _d_match_rate(d)
    _d_sensitivity(d)
    _d_county_split(d)
    _d_residual(d)
    _d_sens_summary(d)
    _d_res_summary(d)
    _d_validation(d)
    _d_appf_panels(d)
    _d_appf_allsix(d)
    return d

def _d_sensitivity(out):
    """D1 — the structural household counts, and the adversarial bound on each finding.

    Independent of `diag_match_error_sensitivity.py` by construction: written from the
    specification, not imported. The budget is the Wilson 95% lower bound on 120/120.
    """
    budget = 0.031
    age24 = "date_diff('year', v.birthdate, DATE '2024-11-05')"

    # --- part 1: the roll-side structural facts -------------------------------
    for st, vrdb in (("wa", "wa_vrdb"), ("ny", "ny_vrdb"), ("id", "id_vrdb")):
        p = DATA / f"{vrdb}.duckdb"
        if not p.exists():
            continue
        con = duckdb.connect(str(p), read_only=True)
        try:
            base = ("status_code = 'A' AND first_name IS NOT NULL "
                    "AND last_name IS NOT NULL AND reg_zip IS NOT NULL")
            n_roll, = con.execute(f"SELECT COUNT(*) FROM voters WHERE {base}").fetchone()
            n_coll, = con.execute(f"""
                SELECT COALESCE(SUM(n), 0) FROM (
                    SELECT COUNT(*) n FROM voters WHERE {base}
                    GROUP BY UPPER(TRIM(last_name)), UPPER(TRIM(first_name)),
                             SUBSTR(reg_zip, 1, 5)
                    HAVING COUNT(*) > 1)""").fetchone()
            n_pool, = con.execute(f"""
                SELECT COUNT(*) FILTER (WHERE k > 1) FROM (
                    SELECT COUNT(*) OVER (PARTITION BY UPPER(TRIM(last_name)),
                                                       SUBSTR(reg_zip, 1, 5)) k
                    FROM voters WHERE {base})""").fetchone()
        finally:
            con.close()
        out[f"sens_{st}_collide_pct"] = 100.0 * n_coll / n_roll
        out[f"sens_{st}_pool_pct"] = 100.0 * n_pool / n_roll

    # --- part 2: the adversarial bound ---------------------------------------
    dem = {"ny": "('DEM')", "id": "('DEM', 'DEMOCRAT', 'DEMOCRATIC')"}
    panels = [
        ("wa_fed", "wa_statewide", "wa_vrdb", FED, age24, None),
        ("wa_state", "wa_statewide", "wa_vrdb", STATE, age24, None),
        ("ny_fed", "ny_statewide", "ny_vrdb", FED, age24, "ny"),
        ("ny_state", "ny_statewide", "ny_vrdb", STATE, age24, "ny"),
        ("id_fed", "id_statewide", "id_vrdb", FED, "v.age", "id"),
        ("id_state", "id_statewide", "id_vrdb", STATE, "v.age", "id"),
    ]
    for key, db, vrdb, panel, age, party_st in panels:
        p = DATA / f"{db}.duckdb"
        if not p.exists():
            continue
        con = duckdb.connect(str(p), read_only=True)
        try:
            con.execute(f"ATTACH '{DATA / (vrdb + '.duckdb')}' AS sv (READ_ONLY)")

            def share_pair(expr):
                n, k = con.execute(f"""
                    SELECT COUNT(*), COUNT(*) FILTER (WHERE {expr})
                    FROM {panel} a JOIN sv.voters v USING (state_voter_id)
                    WHERE {age} IS NOT NULL""").fetchone()
                if not n:
                    return None, None
                d = min(int(round(n * budget)), k)
                return 100.0 * k / n, 100.0 * (k - d) / (n - d)

            b, a_ = share_pair(f"{age} >= 65")
            out[f"sens_{key}_b65"], out[f"sens_{key}_b65_bd"] = b, a_
            if party_st:
                b, a_ = share_pair(f"UPPER(TRIM(v.party)) IN {dem[party_st]}")
                out[f"sens_{key}_dem"], out[f"sens_{key}_dem_bd"] = b, a_

            n_pos, = con.execute(
                f"SELECT COUNT(*) FROM {panel} WHERE total_donated > 0").fetchone()
            sp = int(round(n_pos * budget))
            t0, t1 = con.execute(f"""
                WITH r AS (SELECT total_donated amt,
                                  ROW_NUMBER() OVER (ORDER BY total_donated DESC) rn
                           FROM {panel} WHERE total_donated > 0),
                b AS (SELECT amt, rn, COUNT(*) OVER () n1, SUM(amt) OVER () s1 FROM r),
                dm AS (SELECT CASE WHEN rn <= {sp} THEN amt / 2 ELSE amt END amt FROM r
                       UNION ALL SELECT amt / 2 FROM r WHERE rn <= {sp}),
                d AS (SELECT amt, ROW_NUMBER() OVER (ORDER BY amt DESC) rn2,
                             COUNT(*) OVER () n2, SUM(amt) OVER () s2 FROM dm)
                SELECT (SELECT 100.0*SUM(amt) FILTER (WHERE rn <= CEIL(n1*0.01))
                               / ANY_VALUE(s1) FROM b),
                       (SELECT 100.0*SUM(amt) FILTER (WHERE rn2 <= CEIL(n2*0.01))
                               / ANY_VALUE(s2) FROM d)""").fetchone()
            out[f"sens_{key}_top1"] = float(t0)
            out[f"sens_{key}_top1_bd"] = float(t1)
        finally:
            con.close()

def _d_sens_summary(out):
    """Ranges the D1 prose quotes, derived from the per-panel cells rather than exempted."""
    out["sens_budget_pct"] = 3.1
    # Differenced from the cells ROUNDED to the paper's printed precision, not from the raw
    # values. The prose claim is a summary of the table above it — "the numbers in that table
    # span 1.1 to 2.0" — so differencing raw values answers a slightly different question and
    # disagrees in the last digit (dem_lo 1.163 vs the table's 1.1, top1_hi 8.206 vs 8.3).
    for stat in ("b65", "dem", "top1"):
        moves = [round(out[f"sens_{k}_{stat}"], 1) - round(out[f"sens_{k}_{stat}_bd"], 1)
                 for k in ("wa_fed", "wa_state", "ny_fed", "ny_state", "id_fed", "id_state")
                 if f"sens_{k}_{stat}" in out]
        if moves:
            out[f"sens_move_{stat}_lo"] = min(moves)
            out[f"sens_move_{stat}_hi"] = max(moves)
    # The degenerate removal figure the paper quotes to explain why that model is rejected.
    # Derived rather than asserted, because a number used to justify a methodological choice
    # is exactly the kind that should not be a remembered one.
    p = DATA / "wa_statewide.duckdb"
    if p.exists():
        con = duckdb.connect(str(p), read_only=True)
        try:
            n_pos, = con.execute(
                f"SELECT COUNT(*) FROM {FED} WHERE total_donated > 0").fetchone()
            drop = int(round(n_pos * 0.031))
            v, = con.execute(f"""
                WITH r AS (SELECT total_donated amt,
                                  ROW_NUMBER() OVER (ORDER BY total_donated DESC) rn
                           FROM {FED} WHERE total_donated > 0),
                k AS (SELECT amt, ROW_NUMBER() OVER (ORDER BY amt DESC) rn2,
                             COUNT(*) OVER () n2, SUM(amt) OVER () s2
                      FROM r WHERE rn > {drop})
                SELECT 100.0*SUM(amt) FILTER (WHERE rn2 <= CEIL(n2*0.01))
                       / ANY_VALUE(s2) FROM k""").fetchone()
            out["sens_wa_fed_top1_removal"] = float(v)
        finally:
            con.close()

def _d_res_summary(out):
    """Ranges the D3 prose quotes."""
    keys = ("wa_fed", "wa_state", "ny_fed", "ny_state", "id_fed", "id_state")
    # Same convention as _d_sens_summary: the prose summarises the printed table.
    for b in ("difzip", "nameform", "none"):
        vals = sorted(round(out[f"res_{k}_{b}"], 1) for k in keys if f"res_{k}_{b}" in out)
        if vals:
            out[f"res_{b}_lo"], out[f"res_{b}_hi"] = vals[0], vals[-1]

def _d_county_split(out):
    """D2 — participation and intensity factors of each named county's dollar multiplier."""
    named = {
        ("wa_fed", "KING"), ("wa_state", "KING"), ("wa_fed", "SAN JUAN"),
        ("ny_fed", "NEW YORK"), ("ny_state", "NEW YORK"), ("ny_fed", "TOMPKINS"),
        ("id_fed", "BLAINE"), ("id_state", "BLAINE"), ("id_fed", "BONNEVILLE"),
    }
    panels = [("wa_fed", "wa_statewide", "wa_vrdb", FED, "status_code = 'A'"),
              ("wa_state", "wa_statewide", "wa_vrdb", STATE, "status_code = 'A'"),
              ("ny_fed", "ny_statewide", "ny_vrdb", FED, "status_code = 'A'"),
              ("ny_state", "ny_statewide", "ny_vrdb", STATE, "status_code = 'A'"),
              ("id_fed", "id_statewide", "id_vrdb", FED, "1=1"),
              ("id_state", "id_statewide", "id_vrdb", STATE, "1=1")]
    for key, db, vrdb, panel, active in panels:
        p = DATA / f"{db}.duckdb"
        if not p.exists():
            continue
        wanted = [c for k, c in named if k == key]
        if not wanted:
            continue
        con = duckdb.connect(str(p), read_only=True)
        try:
            con.execute(f"ATTACH '{DATA / (vrdb + '.duckdb')}' AS cv (READ_ONLY)")
            rows = con.execute(f"""
                WITH roll AS (SELECT UPPER(TRIM(county_name)) c, COUNT(*) r
                              FROM cv.voters WHERE {active} AND county_name IS NOT NULL
                              GROUP BY 1),
                don AS (SELECT UPPER(TRIM(v.county_name)) c, COUNT(*) d,
                               SUM(a.total_donated) sm
                        FROM {panel} a JOIN cv.voters v USING (state_voter_id)
                        WHERE v.county_name IS NOT NULL GROUP BY 1),
                t AS (SELECT (SELECT SUM(r) FROM roll) R, (SELECT SUM(d) FROM don) D,
                             (SELECT SUM(sm) FROM don) S)
                SELECT o.c,
                       (o.sm / t.S) / (CAST(l.r AS DOUBLE) / t.R),
                       (CAST(o.d AS DOUBLE) / l.r) / (CAST(t.D AS DOUBLE) / t.R),
                       (o.sm / o.d) / (t.S / CAST(t.D AS DOUBLE))
                FROM don o JOIN roll l USING (c) CROSS JOIN t t""").fetchall()
        finally:
            con.close()
        for c, mult, part, inten in rows:
            if c in wanted:
                slug = c.lower().replace(" ", "")
                out[f"cty_{key}_{slug}_mult"] = float(mult)
                out[f"cty_{key}_{slug}_part"] = float(part)
                out[f"cty_{key}_{slug}_inten"] = float(inten)

def _d_residual(out):
    """D3 — the non-match cascade, as shares of eligible donor identities."""
    last = ("CASE WHEN contributor_name LIKE '%,%' "
            "THEN UPPER(TRIM(SPLIT_PART(contributor_name, ',', 1))) "
            "ELSE UPPER(TRIM(SPLIT_PART(TRIM(contributor_name), ' ', 1))) END")
    first = ("CASE WHEN contributor_name LIKE '%,%' "
             "THEN UPPER(SPLIT_PART(TRIM(SPLIT_PART(contributor_name, ',', 2)), ' ', 1)) "
             "ELSE UPPER(SPLIT_PART(TRIM(contributor_name), ' ', 2)) END")
    elig = ("contributor_name IS NOT NULL AND contributor_name <> '' "
            "AND contributor_zip IS NOT NULL AND contributor_zip <> '' "
            "AND UPPER(contributor_name) NOT IN "
            "('SMALL CONTRIBUTIONS', 'UNITEMIZED', 'ANONYMOUS') "
            "AND COALESCE(contributor_type, 'UNKNOWN') NOT IN ('ORGANIZATION', 'COMMITTEE')")
    panels = [("wa_fed", "wa_statewide", "wa_vrdb", "FEC", True),
              ("wa_state", "wa_statewide", "wa_vrdb", "PDC", True),
              ("ny_fed", "ny_statewide", "ny_vrdb", "FEC", True),
              ("ny_state", "ny_statewide", "ny_vrdb", "NY", True),
              ("id_fed", "id_statewide", "id_vrdb", "FEC", False),
              ("id_state", "id_statewide", "id_vrdb", "SUNSHINE", False)]
    for key, db, vrdb, pfx, has_status in panels:
        p = DATA / f"{db}.duckdb"
        if not p.exists():
            continue
        con = duckdb.connect(str(p), read_only=True)
        try:
            con.execute(f"ATTACH '{DATA / (vrdb + '.duckdb')}' AS rv (READ_ONLY)")
            src = f"SPLIT_PART(contribution_id, ':', 1) = '{pfx}'"
            act = "status_code = 'A'"
            inact = "status_code <> 'A'" if has_status else "1=0"
            row = con.execute(f"""
                WITH e AS (
                    SELECT * FROM (
                        SELECT {last} l, {first} f, SUBSTR(contributor_zip, 1, 5) z
                        FROM individual_contributions WHERE {src} AND {elig}
                        GROUP BY 1, 2, 3)
                    WHERE l <> '' AND LENGTH(f) > 1 AND LENGTH(z) = 5),
                ka AS (SELECT UPPER(TRIM(last_name)) l, UPPER(TRIM(first_name)) f,
                              SUBSTR(reg_zip, 1, 5) z, COUNT(*) n FROM rv.voters
                       WHERE {act} AND first_name IS NOT NULL AND last_name IS NOT NULL
                         AND reg_zip IS NOT NULL GROUP BY 1, 2, 3),
                ki AS (SELECT DISTINCT UPPER(TRIM(last_name)) l, UPPER(TRIM(first_name)) f,
                              SUBSTR(reg_zip, 1, 5) z FROM rv.voters
                       WHERE {inact} AND first_name IS NOT NULL AND last_name IS NOT NULL
                         AND reg_zip IS NOT NULL),
                kz AS (SELECT DISTINCT UPPER(TRIM(last_name)) l, UPPER(TRIM(first_name)) f
                       FROM rv.voters WHERE {act} AND first_name IS NOT NULL
                         AND last_name IS NOT NULL),
                kn AS (SELECT DISTINCT UPPER(TRIM(last_name)) l,
                              UPPER(SUBSTR(TRIM(first_name), 1, 1)) fi,
                              SUBSTR(reg_zip, 1, 5) z FROM rv.voters
                       WHERE {act} AND first_name IS NOT NULL AND last_name IS NOT NULL
                         AND reg_zip IS NOT NULL),
                t AS (SELECT e.*, ka.n na, ki.l IS NOT NULL ina, kz.l IS NOT NULL anyz,
                             kn.l IS NOT NULL initm
                      FROM e LEFT JOIN ka USING (l, f, z) LEFT JOIN ki USING (l, f, z)
                             LEFT JOIN kz USING (l, f)
                             LEFT JOIN kn ON kn.l = e.l AND kn.fi = SUBSTR(e.f, 1, 1)
                                         AND kn.z = e.z)
                SELECT COUNT(*),
                       COUNT(*) FILTER (WHERE na = 1),
                       COUNT(*) FILTER (WHERE na > 1),
                       COUNT(*) FILTER (WHERE na IS NULL AND ina),
                       COUNT(*) FILTER (WHERE na IS NULL AND NOT ina AND anyz),
                       COUNT(*) FILTER (WHERE na IS NULL AND NOT ina AND NOT anyz AND initm),
                       COUNT(*) FILTER (WHERE na IS NULL AND NOT ina AND NOT anyz
                                          AND NOT initm)
                FROM t""").fetchone()
        finally:
            con.close()
        tot = row[0] or 1
        for name, v in zip(("matched", "guard", "inactive", "difzip", "nameform", "none"),
                           row[1:]):
            out[f"res_{key}_{name}"] = 100.0 * v / tot

REFDIR = ROOT / "docs" / "reference"
VERDICTS = REFDIR / "match_validation_verdicts_2026-07-27.csv"
HUMAN = REFDIR / "match_validation_human_verdicts_2026-07-27.csv"
TIER_SHARES = REFDIR / "match_validation_tier_shares_2026-07-27.csv"

_TIER_ORDER = ("STRICT_ZIP5_FULL", "STRICT_ZIP5_MID", "STRICT_ZIP5", "RELAXED_ZIP3_MID")

def _wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval, as percentages, clipped to [0, 100].

    Written out rather than pulled from a stats package: the interval is a published figure in
    Appendix F's precision table, and a verifier that imported the same helper the paper's
    scripts use would be checking the helper against itself. Verified by hand against all four
    published rows before use.
    """
    if n <= 0:
        return 0.0, 100.0
    p = k / n
    d = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = (z / d) * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    return max(0.0, 100.0 * (centre - half)), min(100.0, 100.0 * (centre + half))

def _d_appf_panels(out):
    """All-tier panel sizes, and the two source-format rates Appendix F's error modes rest on.

    The weighted-precision table's first column is donors with a POSITIVE total, which differs
    from the row count in exactly one panel (WA state). The paper devotes a note to that
    difference, so both numbers are derived rather than one of them trusted.
    """
    panels = [("wa_fed", "wa_statewide", FED + "_alltier"),
              ("wa_state", "wa_statewide", STATE + "_alltier"),
              ("ny_fed", "ny_statewide", FED + "_alltier"),
              ("ny_state", "ny_statewide", STATE + "_alltier"),
              ("id_fed", "id_statewide", FED + "_alltier"),
              ("id_state", "id_statewide", STATE + "_alltier")]
    for key, db, tbl in panels:
        p = DATA / f"{db}.duckdb"
        if not p.exists():
            continue
        con = duckdb.connect(str(p), read_only=True)
        try:
            rows, pos = con.execute(
                f"SELECT COUNT(*), COUNT(*) FILTER (WHERE total_donated > 0) "
                f"FROM {tbl}").fetchone()
        finally:
            con.close()
        out[f"appf_{key}_rows"] = rows
        out[f"appf_{key}_pos"] = pos
    if "appf_wa_state_rows" in out:
        out["appf_wa_state_gap"] = out["appf_wa_state_rows"] - out["appf_wa_state_pos"]

    # Idaho Sunshine's organisation share, from the persisted contributor_type field rather
    # than a name heuristic — which is the whole point of the sentence that quotes it.
    p = DATA / "id_statewide.duckdb"
    if p.exists():
        con = duckdb.connect(str(p), read_only=True)
        try:
            n, no, amt, amto = con.execute("""
                SELECT COUNT(*),
                       COUNT(*) FILTER (WHERE contributor_type IN
                                        ('ORGANIZATION', 'COMMITTEE')),
                       SUM(contribution_amount),
                       SUM(contribution_amount) FILTER (WHERE contributor_type IN
                                        ('ORGANIZATION', 'COMMITTEE'))
                FROM individual_contributions
                WHERE SPLIT_PART(contribution_id, ':', 1) = 'SUNSHINE'""").fetchone()
        finally:
            con.close()
        out["appf_id_org_pct"] = 100.0 * no / n if n else 0.0
        out["appf_id_org_dollar_pct"] = 100.0 * float(amto) / float(amt) if amt else 0.0
        out["appf_id_org_m"] = float(amto) / 1e6
        out["appf_id_total_m"] = float(amt) / 1e6

    # WA PDC's name-order misparse rate, over comma-less rows — the denominator the paper names.
    p = DATA / "wa_statewide.duckdb"
    if p.exists():
        con = duckdb.connect(str(p), read_only=True)
        try:
            con.execute(f"ATTACH '{DATA / 'wa_vrdb.duckdb'}' AS vrdb (READ_ONLY)")
            # A comma-less row is misparsed when its FIRST token is not a surname on the roll
            # but its LAST token is. Measured on the roll's surname vocabulary.
            n, bad, amt, amtbad = con.execute("""
                WITH sur AS (SELECT DISTINCT UPPER(TRIM(last_name)) l FROM vrdb.voters
                             WHERE last_name IS NOT NULL),
                c AS (SELECT contribution_amount amt,
                             UPPER(TRIM(SPLIT_PART(TRIM(contributor_name), ' ', 1))) t1,
                             UPPER(TRIM(REGEXP_EXTRACT(TRIM(contributor_name),
                                        '([^ ]+)$', 1))) tl
                      FROM individual_contributions
                      WHERE SPLIT_PART(contribution_id, ':', 1) = 'PDC'
                        AND contributor_name IS NOT NULL
                        AND contributor_name NOT LIKE '%,%')
                SELECT COUNT(*),
                       COUNT(*) FILTER (WHERE t1 NOT IN (SELECT l FROM sur)
                                          AND tl IN (SELECT l FROM sur)),
                       SUM(amt),
                       SUM(amt) FILTER (WHERE t1 NOT IN (SELECT l FROM sur)
                                          AND tl IN (SELECT l FROM sur))
                FROM c""").fetchone()
        finally:
            con.close()
        out["appf_wa_nameorder_pct"] = 100.0 * bad / n if n else 0.0
        out["appf_wa_nameorder_dollar_pct"] = (
            100.0 * float(amtbad) / float(amt) if amt else 0.0)

def _d_appf_allsix(out):
    """The donor-weighted all-six row: each panel's weighted precision, weighted by its own
    positive-total donor count. Depends on both _d_validation and _d_appf_panels, so it runs
    after them rather than inside either."""
    keys = ("wa_fed", "wa_state", "ny_fed", "ny_state", "id_fed", "id_state")
    for suffix, out_key in (("", "val_wprec_all"), ("_u", "val_wprec_all_u")):
        num = den = 0.0
        for k in keys:
            w = out.get(f"appf_{k}_pos")
            p = out.get(f"val_wprec_{k}{suffix}")
            if w and p is not None:
                num += w * p
                den += w
        if den:
            out[out_key] = num / den

def _d_validation(out):
    """Appendix F's rating tables, derived from the frozen verdict CSVs.

    The CSVs are the record of a human/AI adjudication that cannot be recomputed from the
    databases, so they are the primary source here — but every table the paper builds ON them
    is arithmetic and is checked.
    """
    if not VERDICTS.exists():
        return
    con = duckdb.connect(":memory:")
    try:
        v = f"read_csv_auto('{VERDICTS.as_posix()}')"

        # --- the precision table, one row per tier -------------------------------
        for i, tier in enumerate(_TIER_ORDER):
            n_all, y, nc, np_, u = con.execute(f"""
                SELECT COUNT(*),
                       COUNT(*) FILTER (WHERE verdict = 'Y'),
                       COUNT(*) FILTER (WHERE verdict = 'NC'),
                       COUNT(*) FILTER (WHERE verdict = 'NP'),
                       COUNT(*) FILTER (WHERE verdict = 'U')
                FROM {v} WHERE match_tier = '{tier}'""").fetchone()
            base = y + nc + np_          # precision excludes indeterminates
            out[f"val_t{i}_n"] = n_all
            out[f"val_t{i}_y"] = y
            out[f"val_t{i}_nc"] = nc
            out[f"val_t{i}_np"] = np_
            out[f"val_t{i}_u"] = u
            out[f"val_t{i}_prec"] = 100.0 * y / base if base else 0.0
            lo, hi = _wilson(y, base)
            out[f"val_t{i}_lo"], out[f"val_t{i}_hi"] = lo, hi

        # raw sample mean — deliberately NOT a panel estimate, and the paper says so
        ry, rbase = con.execute(f"""
            SELECT COUNT(*) FILTER (WHERE verdict = 'Y'),
                   COUNT(*) FILTER (WHERE verdict IN ('Y', 'NC', 'NP')) FROM {v}""").fetchone()
        out["val_raw_mean"] = 100.0 * ry / rbase if rbase else 0.0
        out["val_total_n"], = con.execute(f"SELECT COUNT(*) FROM {v}").fetchone()
        out["val_indeterminate"], = con.execute(
            f"SELECT COUNT(*) FILTER (WHERE verdict = 'U') FROM {v}").fetchone()

        # --- error modes ---------------------------------------------------------
        # NC only. "Confirmed" excludes NP ("probably different"), and the three error-mode
        # counts sum to exactly the NC total, which is what settles the reading.
        out["val_confirmed_false"], = con.execute(
            f"SELECT COUNT(*) FROM {v} WHERE verdict = 'NC'").fetchone()
        for label, col in (("household", "different_person"),
                           ("org", "organisation_as_person"),
                           ("nameorder", "name_order_parse")):
            n, = con.execute(
                f"SELECT COUNT(*) FROM {v} WHERE error_mode = '{col}'").fetchone()
            out[f"val_mode_{label}"] = n
        # The household mode's tier split, which the paper prints inline.
        for i, tier in enumerate(_TIER_ORDER):
            n, = con.execute(f"""SELECT COUNT(*) FROM {v}
                WHERE error_mode = 'different_person' AND match_tier = '{tier}'""").fetchone()
            out[f"val_household_t{i}"] = n

        # --- by dollar band, raw and on the primary tier -------------------------
        for band, tag in (("top10", "top"), ("rest", "rest")):
            y, base = con.execute(f"""
                SELECT COUNT(*) FILTER (WHERE verdict = 'Y'),
                       COUNT(*) FILTER (WHERE verdict IN ('Y', 'NC', 'NP'))
                FROM {v} WHERE dollar_band = '{band}'""").fetchone()
            out[f"val_band_{tag}"] = 100.0 * y / base if base else 0.0
        out["val_full_top_y"], out["val_full_top_n"] = con.execute(f"""
            SELECT COUNT(*) FILTER (WHERE verdict = 'Y'), COUNT(*)
            FROM {v} WHERE match_tier = 'STRICT_ZIP5_FULL' AND dollar_band = 'top10'""").fetchone()

        # --- population-weighted precision, per panel ---------------------------
        if TIER_SHARES.exists():
            t = f"read_csv_auto('{TIER_SHARES.as_posix()}')"
            # Panel-specific precision: the sample is stratified 20 per state x panel x tier,
            # so each panel's weighting uses its own strata rather than the pooled per-tier
            # figure. Pooling reproduces four panels to a tenth but misses Idaho's state panel
            # by 3.3 points; this basis reproduces all six to within 0.04.
            pp, ppu = {}, {}
            for st, panel, tier, y, nc, np_, u in con.execute(f"""
                    SELECT state, panel, match_tier,
                           COUNT(*) FILTER (WHERE verdict = 'Y'),
                           COUNT(*) FILTER (WHERE verdict = 'NC'),
                           COUNT(*) FILTER (WHERE verdict = 'NP'),
                           COUNT(*) FILTER (WHERE verdict = 'U')
                    FROM {v} GROUP BY 1, 2, 3""").fetchall():
                base = y + nc + np_
                pp[(st, panel, tier)] = 100.0 * y / base if base else 0.0
                ppu[(st, panel, tier)] = 100.0 * y / (base + u) if base + u else 0.0
            acc: dict = {}
            for st, panel, tier, share in con.execute(
                    f"SELECT state, panel, match_tier, tier_share FROM {t}").fetchall():
                key = f"{st.lower()}_{'fed' if panel == 'federal' else 'state'}"
                a = acc.setdefault(key, [0.0, 0.0])
                a[0] += float(share) * pp.get((st, panel, tier), 0.0)
                a[1] += float(share) * ppu.get((st, panel, tier), 0.0)
            for key, (w, wu) in acc.items():
                out[f"val_wprec_{key}"] = w
                out[f"val_wprec_{key}_u"] = wu
            # The stratum size is what the per-panel column actually rests on, and the paper
            # does not currently state it.
            # the all-six donor-weighted row, weighted by each panel's positive-total donors
            out["val_stratum_n"], = con.execute(f"""
                SELECT MIN(n) FROM (SELECT COUNT(*) n FROM {v}
                                    GROUP BY state, panel, match_tier)""").fetchone()
            # The largest shift from treating every indeterminate as an error, which the
            # precision table's footnote bounds at "<= 0.5 points".
            out["val_u_shift"] = max(
                abs(out[f"val_t{i}_prec"] - (100.0 * out[f"val_t{i}_y"]
                    / (out[f"val_t{i}_y"] + out[f"val_t{i}_nc"] + out[f"val_t{i}_np"]
                       + out[f"val_t{i}_u"])))
                for i in range(4))

        # --- the independent human re-rating ------------------------------------
        if HUMAN.exists():
            h = f"read_csv_auto('{HUMAN.as_posix()}')"
            out["val_human_n"], = con.execute(f"SELECT COUNT(*) FROM {h}").fetchone()
            out["val_human_full_y"], out["val_human_full_n"] = con.execute(f"""
                SELECT COUNT(*) FILTER (WHERE human_verdict = 'Y'), COUNT(*)
                FROM {h} WHERE match_tier = 'STRICT_ZIP5_FULL'""").fetchone()
            out["val_human_contradict_y"], = con.execute(f"""
                SELECT COUNT(*) FROM {h}
                WHERE ai_verdict = 'Y' AND human_verdict IN ('NC', 'NP')""").fetchone()
    finally:
        con.close()

def _d_match_rate(out):
    """Linkage recall, dollar coverage, and the uniqueness guard's cost, per panel.

    Deliberately NOT imported from `scripts/diag_match_rate.py`, which produces the paper's
    figures. This verifier's whole claim is that it re-derives results independently of the
    build path, and importing the originating script would make the agreement circular. The
    SQL below is written from the specification — the primary key is
    (surname, FULL first name, ZIP5); an identity is eligible if the name and ZIP are present
    and non-empty, the name is not one of the three aggregator pseudo-names, and the
    contributor type is not a known organisation, with the COALESCE so NULL-typed rows are
    KEPT; and the donor-side name parse handles the comma and comma-less filing conventions.

    Denominators are residence-restricted, matching the paper's table: the FEC layers are
    residence-filtered at load and the state layers are not, so an unrestricted denominator
    is not comparable across panels. Identities and dollars are restricted the same way.
    """
    last = ("CASE WHEN contributor_name LIKE '%,%' "
            "THEN UPPER(TRIM(SPLIT_PART(contributor_name, ',', 1))) "
            "ELSE UPPER(TRIM(SPLIT_PART(TRIM(contributor_name), ' ', 1))) END")
    first = ("CASE WHEN contributor_name LIKE '%,%' "
             "THEN UPPER(SPLIT_PART(TRIM(SPLIT_PART(contributor_name, ',', 2)), ' ', 1)) "
             "ELSE UPPER(SPLIT_PART(TRIM(contributor_name), ' ', 2)) END")
    elig = ("contributor_name IS NOT NULL AND contributor_name <> '' "
            "AND contributor_zip IS NOT NULL AND contributor_zip <> '' "
            "AND UPPER(contributor_name) NOT IN "
            "('SMALL CONTRIBUTIONS', 'UNITEMIZED', 'ANONYMOUS') "
            "AND COALESCE(contributor_type, 'UNKNOWN') "
            "NOT IN ('ORGANIZATION', 'COMMITTEE')")

    panels = [
        ("wa_fed", "wa_statewide", "wa_vrdb", "FEC", "WA", FED),
        ("wa_state", "wa_statewide", "wa_vrdb", "PDC", "WA", STATE),
        ("ny_fed", "ny_statewide", "ny_vrdb", "FEC", "NY", FED),
        ("ny_state", "ny_statewide", "ny_vrdb", "NY", "NY", STATE),
        ("id_fed", "id_statewide", "id_vrdb", "FEC", "ID", FED),
        ("id_state", "id_statewide", "id_vrdb", "SUNSHINE", "ID", STATE),
    ]
    for key, db, vrdb, pfx, st, panel in panels:
        path = DATA / f"{db}.duckdb"
        if not path.exists():
            continue
        con = duckdb.connect(str(path), read_only=True)
        try:
            con.execute(f"ATTACH '{DATA / (vrdb + '.duckdb')}' AS mrv (READ_ONLY)")
            src = f"SPLIT_PART(contribution_id, ':', 1) = '{pfx}'"
            resid = f"UPPER(TRIM(contributor_state)) = '{st}'"

            n_ids, = con.execute(f"""
                SELECT COUNT(*) FROM (
                    SELECT {last} AS l, {first} AS f, SUBSTR(contributor_zip, 1, 5) AS z
                    FROM individual_contributions WHERE {src} AND {elig} AND {resid}
                    GROUP BY 1, 2, 3)
                WHERE l <> '' AND LENGTH(f) > 1 AND LENGTH(z) = 5""").fetchone()
            amt, = con.execute(f"""
                SELECT SUM(contribution_amount) FROM individual_contributions
                WHERE {src} AND {elig} AND {resid}""").fetchone()
            n_matched, matched_amt = con.execute(
                f"SELECT COUNT(*), SUM(total_donated) FROM {panel}").fetchone()

            out[f"mr_{key}_ids"] = n_ids
            out[f"mr_{key}_matched"] = n_matched
            out[f"mr_{key}_recall"] = 100.0 * n_matched / n_ids if n_ids else 0.0
            out[f"mr_{key}_amt_m"] = float(amt or 0) / 1e6
            n_named, n_out, n_nocomma = con.execute(f"""
                SELECT COUNT(*),
                       COUNT(*) FILTER (WHERE contributor_state IS NOT NULL
                                          AND TRIM(contributor_state) <> ''
                                          AND UPPER(TRIM(contributor_state)) <> '{st}'),
                       COUNT(*) FILTER (WHERE contributor_name NOT LIKE '%,%')
                FROM individual_contributions
                WHERE {src} AND contributor_name IS NOT NULL
                  AND contributor_name <> ''""").fetchone()
            out[f"mr_{key}_outstate_pct"] = 100.0 * n_out / n_named if n_named else 0.0
            out[f"mr_{key}_nocomma_pct"] = 100.0 * n_nocomma / n_named if n_named else 0.0
            out[f"mr_{key}_matched_m"] = float(matched_amt or 0) / 1e6
            out[f"mr_{key}_cov"] = (100.0 * float(matched_amt or 0) / float(amt)
                                    if amt else 0.0)

            # The guard's cost: identities whose key lands on 2+ active registrants. The
            # paper's second table is unrestricted by residence so its three columns sum,
            # so this one is too.
            rows = dict(con.execute(f"""
                WITH e AS (
                    SELECT {last} AS l, {first} AS f, SUBSTR(contributor_zip, 1, 5) AS z
                    FROM individual_contributions WHERE {src} AND {elig}
                    GROUP BY 1, 2, 3
                ), k AS (
                    SELECT * FROM e WHERE l <> '' AND LENGTH(f) > 1 AND LENGTH(z) = 5
                ), r AS (
                    SELECT UPPER(TRIM(last_name)) l, UPPER(TRIM(first_name)) f,
                           SUBSTR(reg_zip, 1, 5) z, COUNT(*) n
                    FROM mrv.voters
                    WHERE status_code = 'A' AND first_name IS NOT NULL
                      AND last_name IS NOT NULL AND reg_zip IS NOT NULL
                    GROUP BY 1, 2, 3)
                SELECT CASE WHEN r.n IS NULL THEN 'none'
                            WHEN r.n = 1 THEN 'one' ELSE 'many' END, COUNT(*)
                FROM k LEFT JOIN r USING (l, f, z) GROUP BY 1""").fetchall())
            tot = sum(rows.values()) or 1
            out[f"mr_{key}_guard_n"] = rows.get("many", 0)
            out[f"mr_{key}_none_n"] = rows.get("none", 0)
            out[f"mr_{key}_guard_pct"] = 100.0 * rows.get("many", 0) / tot
            # Independent cross-check of the numerator: the count of identities resolving to
            # exactly ONE registrant must equal the published panel's row count. If these
            # ever disagree the denominator has stopped describing the same universe the
            # matcher used, which would silently invalidate every recall figure.
            if rows.get("one", 0) != n_matched:
                out.setdefault("_match_rate_warnings", []).append(
                    f"{key}: {rows.get('one', 0):,} identities resolve to exactly one "
                    f"registrant but the panel holds {n_matched:,} rows")
        finally:
            con.close()

    _rc = sorted(out[f"mr_{k}_recall"] for k, *_ in panels if f"mr_{k}_recall" in out)
    _cv = sorted(out[f"mr_{k}_cov"] for k, *_ in panels if f"mr_{k}_cov" in out)
    _gd = sorted(out[f"mr_{k}_guard_pct"] for k, *_ in panels if f"mr_{k}_guard_pct" in out)
    if _rc:
        out["_mr_recall_lo"], out["_mr_recall_hi"] = _rc[0], _rc[-1]
        out["_mr_cov_lo"], out["_mr_cov_hi"] = _cv[0], _cv[-1]
        out["_mr_guard_lo"], out["_mr_guard_hi"] = _gd[0], _gd[-1]

# Sections of the paper. A probe is scoped to one so that a row shape repeated across
# states (the "18-29" age row appears in both the NY and the ID table) cannot be asserted
# against the wrong state's derivation.
SECTION_BOUNDS = {
    # The main-body methods section, added 2026-07-29 for review #10. Every figure in it
    # but two restates one published elsewhere in the paper, which is exactly why it is
    # audited rather than trusted.
    # The methods section is cut into three ADJACENT, non-overlapping slices that together
    # cover it end to end. Spans are per-section coordinates, so an overlap reports one
    # slice's probed cells as the other's unmapped ones — the failure that cost review rounds
    # 5 and 7 a section each. Splitting rather than nesting also means the tail of the section
    # stays audited: an earlier attempt ended `methods` at the match-rate heading and left
    # everything after it in no slice at all, which silently dropped the tier table.
    "methods": ("## Data, linkage, and validation",
                "**Spending the whole error budget against each finding.**"),
    # D1, added 2026-07-29. Adjacent to `methods`, which now ends at its heading.
    "sensitivity": ("**Spending the whole error budget against each finding.**",
                    "**How far below the ceiling that floor sits.**"),
    "matchrate": ("**How far below the ceiling that floor sits.**",
                  "**What the restriction costs, stated rather than buried.**"),
    "methods_tail": ("**What the restriction costs, stated rather than buried.**",
                     "## Finding 1 —"),
    "f1_ny": ("**New York** (`match_ny_voters_to_donors.py`)",
              "**Washington** shows the same shape"),
    "f1_wa": ("**Washington** shows the same shape",
              "**Idaho** replicates it in a third state"),
    "f1_id": ("**Idaho** replicates it in a third state",
              "**The panel gap, and what it is not.**"),
    "f1_gap": ("**The panel gap, and what it is not.**", "## Finding 2 —"),
    "f2": ("## Finding 2 —", "**And the multiplier itself decomposes, exactly.**"),
    # D2, added 2026-07-29. Carved out of `f2` rather than nested inside it: spans are
    # per-section coordinates and an overlap misreports both slices.
    "f2_tail": ("**And the multiplier itself decomposes, exactly.**", "## Finding 3 —"),
    "f3": ("## Finding 3 —", "### Where the money goes"),
    # Sections must NOT overlap. Coverage spans are recorded in each section's own
    # coordinate system, so a slice that swallows another (an earlier "f3_money" spanning
    # the whole subsection INCLUDING both crossover tables) reports 165 already-probed
    # cells as unmapped. Finding 3's subsection is therefore cut into four adjacent slices.
    "f3_xover_intro": ("### Where the money goes", "**New York.** | own party"),
    # Finding 3's subsection states the competitiveness bands a SECOND time. Both copies
    # were all-tier-and-pooled; both are now probed, so they cannot drift apart again.
    "f3_id_skew": ("### Idaho — the same skew", "## Finding 4 —"),
    "f4": ("## Finding 4 —", "## What this paper does not claim"),
    # The crossover tables and the limitations bullet that restates their resolution rates.
    # Uncovered until 2026-07-28, which is how three retired rates (87.8 / 86.7 / 51.9)
    # survived in the limitations and Appendix A after the crossover section itself was
    # corrected — the reviewer found all three.
    "xover_ny": ("**New York.** | own party | matched | resolved", "**Idaho.** Idaho Sunshine"),
    # End anchor must come AFTER the start, or `find(end, start)` returns -1 and the slice
    # runs to the end of the document — which reported 629 unmapped tokens from the rest of
    # the paper. It used to point at "### Where the money goes", which precedes this block.
    "xover_id": ("**Idaho.** Idaho Sunshine", "### Idaho — the same skew"),
    "limits_xover": ("**Recipient party is partial, differentially missing",
                     "- **No policy-influence claim.**"),
    # The itemization bullet and Appendix D's below-floor table. Added to the audit
    # 2026-07-28 because the figures in them are DB-derived, not statutory — the rest of
    # Appendix D is statutory and stays out of scope.
    "limits_itemization": ("- **Itemized giving only — but the panels are not truncated",
                           "- **Panel comparisons are descriptive"),
    "appd_belowfloor": ("**What the floors do and do not describe, measured",
                        "- **Temporal alignment.**"),
    # Appendix G's DERIVED tables, added to the audit 2026-07-29. Review #3 found this
    # appendix's largest defect while it sat outside the audit, which is the same lesson round
    # 5 learned about the crossover tables: unprobed sections are where bad figures live. G1
    # stays out because it is statutory, and G2's bunching counts come from the same script but
    # are covered by the probe below.
    # Appendix F's rating tables, added 2026-07-30. The appendix was 6% audited with 542
    # unprobed numeric tokens and it holds the paper's own instrument-validation evidence —
    # the pattern that lost the crossover tables in round 5 and Appendix G in round 7. Sliced
    # adjacently so the whole run of tables is covered rather than the parts I thought of.
    # The remaining appendices, added 2026-07-30 to finish the coverage audit. Sliced whole:
    # the point is to be told what is unaccounted for, not to carve out the parts I thought of.
    # Remainder slices, added 2026-07-30 to finish the audit. Each is fitted into a GAP
    # between the existing slices above, because overlapping spans make the audit report one
    # slice's probed cells as the other's unmapped ones.
    "appc_head": ("## Appendix C — Methods",
                  "**What the floors do and do not describe, measured"),
    "appe_head": ("## Appendix E — Full distribution tables",
                  "**Matched-donor concentration, with bootstrap interv"),
    "appe_mid": ("**Candidate money versus total flow.**",
                 "**Geographic concentration of matched dollars, by pa"),
    "appf_head": ("## Appendix F — Match validation and robustness",
                  "**Matchability by party, and why the party finding d"),
    "appf_mid": ("**Per-tier false-merge risk on the donor side.**",
                 "**Result — detected precision differs sharply by mat"),
    "appf_tail": ("**What follows for the paper, and what was done.**",
                  "## Appendix G — Contribution limits"),
    "appg_head": ("## Appendix G — Contribution limits",
                  "**G2 — bunching at statutory values.**"),
    "appg_tail": ("**What replaces the original explanation.**",
                  "## Data, code, and reproduction"),
    "appa": ("## Appendix A — The objections, in full", "## Appendix B — Data access"),
    "appb": ("## Appendix B — Data access", "## Appendix C — Methods"),
    "appd_all": ("## Appendix D — Related work", "## Appendix E — Full distribution tables"),
    "appf_precision": ("**Result — detected precision differs sharply by match tier",
                       "**Population-weighted precision, per panel.**"),
    "appf_weighted": ("**Population-weighted precision, per panel.**",
                      "**Three distinct error modes, separately identified.**"),
    "appf_modes": ("**Three distinct error modes, separately identified.**",
                   "**What follows for the paper, and what was done.**"),
    "appf_matchability": ("**Matchability by party, and why the party finding does not rest",
                          "**Per-tier false-merge risk on the donor side.**"),
    "appg_bunch": ("**G2 — bunching at statutory values.**", "**G3 — and yet capped layers"),
    "appg_layers": ("**G3 — and yet capped layers", "**G4 — a stylized clipping exercise"),
    "appg_clip": ("**G4 — a stylized clipping exercise",
                  "**What replaces the original explanation.**"),
    # Appendix E's bootstrap table and Finding 2's ordering test. The INTERVALS are owned by
    # diag_donor_concentration_bootstrap.py (1,000 resamples per panel, and an RNG sequence
    # that must not be perturbed), so reproducing them here would both double the runtime and
    # duplicate that fragility — they are exempted by owner. The POINT ESTIMATES are probed,
    # because a bootstrap table drifting from Finding 2's concentration table is exactly the
    # internal contradiction that has bitten this paper repeatedly.
    "appe_bootstrap": ("**Matched-donor concentration, with bootstrap intervals — all six",
                       "**Statewide (all itemized donors"),
    "appc_aligned": ("Idaho's Sunshine layer holds three years", "**Panel overlap.**"),
    "appc_ovl": ("**Panel overlap.** The two panels are not the same people",
                 "**The New York state panel.**"),
    # Appendix E restates the geography and turnout cuts in full. It was the last stale
    # surface found (2026-07-28): its turnout table had been moved onto the primary spec
    # but its geography table was still all-tier, and its NY competitiveness table was
    # computed on the POOLED match. Sectioned separately so both get checked.
    "appe_geo": ("**Geographic concentration of matched dollars, by panel.**",
                 "**Donor pool versus registration, by district competitiveness (NY).**"),
    "appe_bands": ("**Donor pool versus registration, by district competitiveness (NY).**",
                   "**Giving and turnout, side by side.**"),
    "appe_turnout": ("**Giving and turnout, side by side.**",
                     "## Appendix F —"),
}

# ------------------------------------------------------------------------- probes
# (label, section or None for the whole paper, regex, derived key(s), tolerance)
# Bold markers are written `\*{0,2}` so re-bolding a figure does not disarm a probe;
# the anchor is the surrounding WORDS.
PROBES = [
    # --- panel sizes, stated in the header table, the abstract and the provenance note
    ("header table, federal donors", None,
     r"FEC itemized individual contributions \| WA ([\d,]+) · NY ([\d,]+) · ID ([\d,]+) \|",
     ("wa_fed_n", "ny_fed_n", "id_fed_n"), 0),
    ("header table, state donors", None,
     r"Idaho Sunshine \| WA ([\d,]+) · NY ([\d,]+) · ID ([\d,]+) \|",
     ("wa_state_n", "ny_state_n", "id_state_n"), 0),
    ("provenance, WA panel sizes", None,
     r"matched to ([\d,]+) federal and ([\d,]+) state donors",
     ("wa_fed_n", "wa_state_n"), 0),
    ("provenance, NY panel sizes", None,
     r"([\d,]+) federal / ([\d,]+) state matched voters\)",
     ("ny_fed_n", "ny_state_n"), 0),
    ("provenance, ID panel sizes", None,
     r"filings \(([\d,]+) voters\) and \*{0,2}federal\*{0,2} FEC contributions "
     r"\(([\d,]+) voters\)", ("id_state_n", "id_fed_n"), 0),

    # --- the header's "federal money is older money" block. Uncovered until 2026-07-28,
    #     and it was carrying the all-tier ALIGNED pair (67.1/51.1 against a primary-spec
    #     68.5/51.3) while the panel-gap paragraph forty lines down had the right one.
    ("header, federal-vs-state 65+ and WA Silent", None,
     r"New York's federal donors are ([\d.]+)% over 65 against ([\d.]+)% of its state "
     r"donors, Idaho's ([\d.]+)% against ([\d.]+)%, and Washington's Silent Generation "
     r"multiplier runs ([\d.]+)× federal against ([\d.]+)× state",
     ("ny_fed_b65", "ny_state_b65", "id_fed_b65", "id_state_b65",
      "wa_fed_mult_silent", "wa_state_mult_silent"), 0.05),
    ("header, ID period-aligned gap", None,
     r"shared 2023[–-]2025 window \*{0,2}widens\*{0,2} the gap to ([\d.]+)% against "
     r"([\d.]+)%", ("id_fedal_b65", "id_state_b65"), 0.05),

    # --- Finding 1: the three age tables
    ("F1 NY age bands, federal + state", "f1_ny",
     r"\| 18[–-]29 \| \*{0,2}([\d.]+)%\*{0,2} \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| "
     r"\| 30[–-]44 \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| "
     r"\| 45[–-]64 \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| "
     r"\| 65\+ \| \*{0,2}([\d.]+)%\*{0,2} \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \|",
     ("ny_fed_b1829", "ny_state_b1829", "ny_active_b1829", "ny_ge24_b1829",
      "ny_fed_b3044", "ny_state_b3044", "ny_active_b3044", "ny_ge24_b3044",
      "ny_fed_b4564", "ny_state_b4564", "ny_active_b4564", "ny_ge24_b4564",
      "ny_fed_b65", "ny_state_b65", "ny_active_b65", "ny_ge24_b65"), 0.05),
    ("F1 NY 65+ prose, federal", "f1_ny",
     r"Nearly \*{0,2}half of NY's federal donors are 65 or older", (), None),
    ("F1 NY 65+ prose, state", "f1_ny",
     r"its state donors are younger but still tilted, at ([\d.]+)%", "ny_state_b65", 0.05),
    ("F1 WA generation multipliers", "f1_wa",
     r"\| Silent \| \*{0,2}([\d.]+)×\*{0,2} \| ([\d.]+)× \| "
     r"\| Boomer \| ([\d.]+)× \| ([\d.]+)× \| "
     r"\| Gen X \| ([\d.]+)× \| ([\d.]+)× \| "
     r"\| Millennial \| ([\d.]+)× \| ([\d.]+)× \| "
     r"\| Gen Z \| \*{0,2}([\d.]+)×\*{0,2} \| ([\d.]+)× \|",
     ("wa_fed_mult_silent", "wa_state_mult_silent",
      "wa_fed_mult_boomer", "wa_state_mult_boomer",
      "wa_fed_mult_genx", "wa_state_mult_genx",
      "wa_fed_mult_millennial", "wa_state_mult_millennial",
      "wa_fed_mult_genz", "wa_state_mult_genz"), 0.005),
    ("F1 ID age bands, federal + state", "f1_id",
     r"\| 18[–-]29 \| \*{0,2}([\d.]+)%\*{0,2} \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| "
     r"\| 30[–-]44 \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| "
     r"\| 45[–-]64 \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| "
     r"\| 65\+ \| \*{0,2}([\d.]+)%\*{0,2} \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \|",
     ("id_fed_b1829", "id_state_b1829", "id_roll_b1829", "id_ge24_b1829",
      "id_fed_b3044", "id_state_b3044", "id_roll_b3044", "id_ge24_b3044",
      "id_fed_b4564", "id_state_b4564", "id_roll_b4564", "id_ge24_b4564",
      "id_fed_b65", "id_state_b65", "id_roll_b65", "id_ge24_b65"), 0.05),
    ("F1 ID under-30 prose, both panels", "f1_id",
     r"under-30 share reduced to \*{0,2}([\d.]+)% and ([\d.]+)%\*{0,2} respectively",
     ("id_fed_b1829", "id_state_b1829"), 0.05),

    # --- harmonized comparison at the common $200 floor (external review item 3)
    ("F1 harmonized age-gap table", "f1_gap",
     r"\| WA \| \+([\d.]+) pts \| \*{0,2}\+([\d.]+)\*{0,2} \| \*{0,2}([\d.]+)% smaller"
     r"\*{0,2} \| "
     r"\| NY \| \+([\d.]+) pts \| \*{0,2}\+([\d.]+)\*{0,2} \| the gap \*widens\* \| "
     r"\| ID \| \+([\d.]+) pts \| \*{0,2}\+([\d.]+)\*{0,2} \| ([\d.]+)% smaller \|",
     ("wa_gap_built", "wa_gap_h200", "wa_gap_floorpct",
      "ny_gap_built", "ny_gap_h200",
      "id_gap_built", "id_gap_h200", "id_gap_floorpct"), 0.5),
    ("F1 within-person groups under harmonization", "f1_gap",
     r"Washington\s+\(([\d.]+) / ([\d.]+) / \*{0,2}([\d.]+)\*{0,2}\) and New York "
     r"\(([\d.]+) / ([\d.]+) / \*{0,2}([\d.]+)\*{0,2}\).*?inside\* the range "
     r"\(([\d.]+) / ([\d.]+) / ([\d.]+)\) on ([\d,]+) donors",
     ("wa_h200_stateonly_b65", "wa_h200_fedonly_b65", "wa_h200_both_b65",
      "ny_h200_stateonly_b65", "ny_h200_fedonly_b65", "ny_h200_both_b65",
      "id_h200_stateonly_b65", "id_h200_fedonly_b65", "id_h200_both_b65",
      "id_h200_both_n"), 0.05),
    ("F2 harmonized concentration ordering", "f2",
     r"\| WA \| \+([\d.]+) pts, state more concentrated \| \*{0,2}[−-]([\d.]+) pts, federal "
     r"more\*{0,2} — flips \| "
     r"\| NY \| [−-]([\d.]+) pts, federal more \| [−-]([\d.]+) pts, federal more \| "
     r"\| ID \| \+([\d.]+) pts, state more concentrated \| \*{0,2}[−-]([\d.]+) pts, federal "
     r"more\*{0,2} — flips \|",
     ("wa_conc_built", "_neg_wa_conc_h200", "_neg_ny_conc_built", "_neg_ny_conc_h200",
      "id_conc_built", "_neg_id_conc_h200"), 0.05),

    # --- Finding 1: the panel-gap paragraph
    ("F1 panel gap, NY + ID 65+", "f1_gap",
     r"New York's 65\+ donor share falls from ([\d.]+)% federal to ([\d.]+)% state, "
     r"Idaho's from ([\d.]+)% to ([\d.]+)%",
     ("ny_fed_b65", "ny_state_b65", "id_fed_b65", "id_state_b65"), 0.05),
    ("F1 panel gap, WA Gen X + Millennial", "f1_gap",
     r"Gen X ([\d.]+)× vs ([\d.]+)×, Millennial ([\d.]+)× vs ([\d.]+)×",
     ("wa_state_mult_genx", "wa_fed_mult_genx",
      "wa_state_mult_millennial", "wa_fed_mult_millennial"), 0.005),
    ("F1 panel gap, ID aligned federal 65+", "f1_gap",
     r"aligned federal 65\+ is \*{0,2}([\d.]+)%\*{0,2} on ([\d,]+) donors, against the "
     r"state panel's ([\d.]+)%",
     ("id_fedal_b65", "id_fedal_n", "id_state_b65"), 0.05),
    ("F1 panel gap, Jaccard", "f1_gap",
     r"Jaccard coefficient of ([\d.]+) in WA, ([\d.]+) in NY, and ([\d.]+) in ID",
     ("wa_jaccard", "ny_jaccard", "id_jaccard"), 0.0005),
    ("F1 panel gap, WA within-person 65+", "f1_gap",
     r"the 65\+ share runs ([\d.]+)% among WA state-only donors, ([\d.]+)% among "
     r"federal-only, and \*{0,2}([\d.]+)%\*{0,2} among those in both",
     ("wa_ovl_stateonly", "wa_ovl_fedonly", "wa_ovl_both"), 0.05),
    ("F1 panel gap, NY + ID within-person 65+", "f1_gap",
     r"NY \(([\d.]+) / ([\d.]+) / ([\d.]+)\) and ID \(([\d.]+) / ([\d.]+) / ([\d.]+)\)",
     ("ny_ovl_stateonly", "ny_ovl_fedonly", "ny_ovl_both",
      "id_ovl_stateonly", "id_ovl_fedonly", "id_ovl_both"), 0.05),

    ("F1 tier sensitivity, primary vs all-tier 65+", "f1_gap",
     r"WA federal ([\d.]+)% → ([\d.]+)%, NY federal ([\d.]+)% → ([\d.]+)%, ID federal "
     r"([\d.]+)% → ([\d.]+)%",
     ("wa_fed_b65", "wa_fedall_b65", "ny_fed_b65", "ny_fedall_b65",
      "id_fed_b65", "id_fedall_b65"), 0.05),
    ("F3 NY active-roll counts", "f3",
     r"`status_code='A'`; ([\d,]+) of ([\d,]+) records",
     ("ny_roll_active", "ny_roll_total"), 0),
    ("F3 ID party table", "f3_id_skew",
     r"\| REP \| ([\d.]+)% \| ([\d.]+)% \| \+([\d.]+) \| ([\d.]+)% \| \+([\d.]+) \| "
     r"\| DEM \| ([\d.]+)% \| ([\d.]+)% \| \*{0,2}\+([\d.]+)\*{0,2} \| ([\d.]+)% \| "
     r"\*{0,2}\+([\d.]+)\*{0,2} \| "
     r"\| UNAFF \(unaffiliated\) \| ([\d.]+)% \| ([\d.]+)% \| \*{0,2}[−-]([\d.]+)\*{0,2} \| "
     r"([\d.]+)% \| \*{0,2}[−-]([\d.]+)\*{0,2} \| "
     r"\| OTHER \(minor\) \| ([\d.]+)% \| ([\d.]+)% \| [−-]([\d.]+) \| ([\d.]+)% \| "
     r"[−-]([\d.]+) \|",
     ("id_fed_reg_REP", "id_fed_don_REP", "id_fed_skew_REP",
      "id_state_don_REP", "id_state_skew_REP",
      "id_fed_reg_DEM", "id_fed_don_DEM", "id_fed_skew_DEM",
      "id_state_don_DEM", "id_state_skew_DEM",
      "id_fed_reg_UNAFF", "id_fed_don_UNAFF", "_neg_id_fed_skew_UNAFF",
      "id_state_don_UNAFF", "_neg_id_state_skew_UNAFF",
      "id_fed_reg_OTHER", "id_fed_don_OTHER", "_neg_id_fed_skew_OTHER",
      "id_state_don_OTHER", "_neg_id_state_skew_OTHER"), 0.05),
    ("F3 ID dollar shares", "f3_id_skew",
     r"Republicans supply ([\d.]+)% of federal and ([\d.]+)% of state matched dollars, "
     r"Democrats ([\d.]+)% and ([\d.]+)%, the unaffiliated ([\d.]+)% and ([\d.]+)%",
     ("id_fed_dol_REP", "id_state_dol_REP", "id_fed_dol_DEM", "id_state_dol_DEM",
      "id_fed_dol_UNAFF", "id_state_dol_UNAFF"), 0.05),
    ("F3 ID skew prose + aligned panel", "f3_id_skew",
     r"registered Democrats\*{0,2} \(\+([\d.]+) federal, \+([\d.]+) state.*?"
     r"\([−-]([\d.]+), [−-]([\d.]+)\).*?the Democratic share is ([\d.]+)% \(\+([\d.]+)\) "
     r"and the unaffiliated ([\d.]+)% \([−-]([\d.]+)\)",
     ("id_fed_skew_DEM", "id_state_skew_DEM",
      "_neg_id_fed_skew_UNAFF", "_neg_id_state_skew_UNAFF",
      "id_fedal_don_DEM", "id_fedal_skew_DEM",
      "id_fedal_don_UNAFF", "_neg_id_fedal_skew_UNAFF"), 0.05),
    ("F4 NY panel-size gap", "f4",
     r"drawing on ([\d,]+) more people", "ny_panel_gap_k", 500),
    ("Appendix C overlap prose, ID panel counts", "appc_ovl",
     r"near-equal panel counts \(([\d,]+) and ([\d,]+)\)", ("id_fed_n", "id_state_n"), 0),
    ("Appendix C overlap prose, ID Jaccard", "appc_ovl",
     r"the ([\d.]+) Jaccard rules that reading out", "id_jaccard", 0.0005),

    # --- Finding 2: concentration table, then every prose restatement of it
    ("F2 table, WA federal", "f2",
     r"\| Washington \| ([\d,]+) \| \$([\d,.]+)M \| \*{0,2}([\d.]+)%\*{0,2} \| ([\d.]+)% "
     r"\| ([\d.]+) \|",
     ("wa_fed_n", "wa_fed_m", "wa_fed_top1", "wa_fed_top10", "wa_fed_gini"), 0.05),
    ("F2 table, NY federal", "f2",
     r"\| New York \| ([\d,]+) \| \$([\d,.]+)M \| \*{0,2}([\d.]+)%\*{0,2} \| ([\d.]+)% "
     r"\| ([\d.]+) \|",
     ("ny_fed_n", "ny_fed_m", "ny_fed_top1", "ny_fed_top10", "ny_fed_gini"), 0.05),
    ("F2 table, ID federal", "f2",
     r"\| Idaho \| ([\d,]+) \| \$([\d,.]+)M \| \*{0,2}([\d.]+)%\*{0,2} \| ([\d.]+)% "
     r"\| ([\d.]+) \|",
     ("id_fed_n", "id_fed_m", "id_fed_top1", "id_fed_top10", "id_fed_gini"), 0.05),
    ("F2 table, WA state", "f2",
     r"\| Washington \(PDC\) \| ([\d,]+) \| \$([\d,.]+)M \| \*{0,2}([\d.]+)%\*{0,2} \| "
     r"([\d.]+)% \| ([\d.]+) \|",
     ("wa_state_n", "wa_state_m", "wa_state_top1", "wa_state_top10", "wa_state_gini"),
     0.05),
    ("F2 table, NY state", "f2",
     r"\| New York \(NYSBOE\) \| ([\d,]+) \| \$([\d,.]+)M \| \*{0,2}([\d.]+)%\*{0,2} \| "
     r"([\d.]+)% \| ([\d.]+) \|",
     ("ny_state_n", "ny_state_m", "ny_state_top1", "ny_state_top10", "ny_state_gini"),
     0.05),
    ("F2 table, ID state", "f2",
     r"\| Idaho \(Sunshine\) \| ([\d,]+) \| \$([\d,.]+)M \| \*{0,2}([\d.]+)%\*{0,2} \| "
     r"([\d.]+)% \| ([\d.]+) \|",
     ("id_state_n", "id_state_m", "id_state_top1", "id_state_top10", "id_state_gini"),
     0.05),
    # The four tier shares, asserted in EVERY copy (section-less): the paper states the
    # primary tier's share twice, and on 2026-07-29 the two copies disagreed (85-89 in
    # Appendix C against 81-89 in Appendix F, true value 80.7-89.2).
    ("Tier shares, all four rows", None,
     r"\| `STRICT_ZIP5_FULL`[^|]*\| surname \+ \*\*full\*\* first name \+ ZIP5 \| "
     r"([\d.]+)[–-]([\d.]+)% \|[\s\S]{0,120}?"
     r"\| `STRICT_ZIP5_MID` \|[^|]*\| ([\d.]+)[–-]([\d.]+)% \|[\s\S]{0,120}?"
     r"\| `STRICT_ZIP5` \|[^|]*\| ([\d.]+)[–-]([\d.]+)% \|[\s\S]{0,120}?"
     r"\| `RELAXED_ZIP3_MID` \|[^|]*\| ([\d.]+)[–-]([\d.]+)% \|",
     ("tier0_share_lo", "tier0_share_hi", "tier1_share_lo", "tier1_share_hi",
      "tier2_share_lo", "tier2_share_hi", "tier3_share_lo", "tier3_share_hi"), 0.05),
    # The same probe scoped to `methods`. Coverage spans are only recorded for
    # section-scoped probes, so the section-less form above asserts the values everywhere
    # but earns the methods section no coverage credit — without this duplicate the audit
    # reports its own asserted cells as unmapped.
    ("Tier shares, methods-section copy", "methods",
     r"\| `STRICT_ZIP5_FULL`[^|]*\| surname \+ \*\*full\*\* first name \+ ZIP5 \| "
     r"([\d.]+)[–-]([\d.]+)% \|[\s\S]{0,120}?"
     r"\| `STRICT_ZIP5_MID` \|[^|]*\| ([\d.]+)[–-]([\d.]+)% \|[\s\S]{0,120}?"
     r"\| `STRICT_ZIP5` \|[^|]*\| ([\d.]+)[–-]([\d.]+)% \|[\s\S]{0,120}?"
     r"\| `RELAXED_ZIP3_MID` \|[^|]*\| ([\d.]+)[–-]([\d.]+)% \|",
     ("tier0_share_lo", "tier0_share_hi", "tier1_share_lo", "tier1_share_hi",
      "tier2_share_lo", "tier2_share_hi", "tier3_share_lo", "tier3_share_hi"), 0.05),
    # Appendix F's validation table carries the same four shares in a different row shape.
    # It was the copy that happened to be RIGHT when Appendix C was wrong, which is only
    # luck until it is asserted.
    ("Tier shares, Appendix F validation table", None,
     r"\| `STRICT_ZIP5_FULL` \| ([\d.]+)[–-]([\d.]+)% \|[\s\S]{0,200}?"
     r"\| `STRICT_ZIP5_MID` \| ([\d.]+)[–-]([\d.]+)% \|[\s\S]{0,200}?"
     r"\| `STRICT_ZIP5` \| ([\d.]+)[–-]([\d.]+)% \|[\s\S]{0,200}?"
     r"\| `RELAXED_ZIP3_MID` \| ([\d.]+)[–-]([\d.]+)% \|",
     ("tier0_share_lo", "tier0_share_hi", "tier1_share_lo", "tier1_share_hi",
      "tier2_share_lo", "tier2_share_hi", "tier3_share_lo", "tier3_share_hi"), 0.05),
    ("D1 budget, stated four times", "sensitivity",
     r"budget is ([\d.]+)% — the Wilson bound", ("sens_budget_pct",), 0.05),
    ("D1 degenerate removal illustration", "sensitivity",
     r"it reads ([\d.]+)% → ([\d.]+)% on Washington's federal panel",
     ("sens_wa_fed_top1", "sens_wa_fed_top1_removal"), 0.05),
    ("D1 movement ranges, age and party", "sensitivity",
     r"the 65\+ share moves by ([\d.]+) to ([\d.]+) points against baselines[\s\S]{0,80}?"
     r"Democratic share by ([\d.]+) to ([\d.]+) points",
     ("sens_move_b65_lo", "sens_move_b65_hi",
      "sens_move_dem_lo", "sens_move_dem_hi"), 0.05),
    ("D1 movement range, concentration", "sensitivity",
     r"top-1% share falls by ([\d.]+) to ([\d.]+) points",
     ("sens_move_top1_lo", "sens_move_top1_hi"), 0.05),
    ("D1 turnout omission, NY federal n", "sensitivity",
     r"between groups of ([\d,]+) and 12\.2 million", ("ny_fed_n",), 0),
    ("D3 out-of-state restatement", "matchrate",
     r"the NYSBOE layer is ([\d.]+)% out-of-state\.\*",
     ("mr_ny_state_outstate_pct",), 0.05),
    ("D3 different-ZIP range", "matchrate",
     r"at a different ZIP5: \*\*([\d.]+)% to ([\d.]+)%\*\*",
     ("res_difzip_lo", "res_difzip_hi"), 0.05),
    ("D3 name-form range", "matchrate",
     r"account for a further ([\d.]+)% to ([\d.]+)%", ("res_nameform_lo", "res_nameform_hi"),
     0.05),
    ("D3 no-counterpart range", "matchrate",
     r"What is left — \*\*([\d.]+)% to ([\d.]+)%\*\*",
     ("res_none_lo", "res_none_hi"), 0.05),
    ("D2 Blaine restated in prose", "f2_tail",
     r"a resort county might suggest — ([\d.]+) × ([\d.]+)",
     ("cty_id_fed_blaine_part", "cty_id_fed_blaine_inten"), 0.005),
    ("D2 Bonneville restated in prose", "f2_tail",
     r"\*\*Bonneville\*\* reaches ([\d.]+)× on intensity alone",
     ("cty_id_fed_bonneville_mult",), 0.005),
    ("F1 age-measure disclosure, the two derivable legs", "f1_ny",
     r"roll 65\+ share is ([\d.]+)% on this measure against [\d.]+% on completed age, its federal\s+"
     r"donors ([\d.]+)% against",
     ("ny_active_b65", "ny_fed_b65"), 0.05),
    # --- Appendix C's pooled-concentration and below-floor restatements -------------
    ("AppC pooled trio restated", "appc_head",
     r"reads top-1% ([\d.]+)% pooled against\s+([\d.]+)% federal and ([\d.]+)% state",
     ("wa_pooled_top1", "wa_fed_top1", "wa_state_top1"), 0.05),
    ("AppC below-floor trigger table", "appd_belowfloor",
     r"\| Federal \(FEC\) \| > \$200 / cycle \| ([\d.]+)% \|[\s\S]{0,120}?"
     r"\| ([\d.]+)% \(≤\$100\) \| \*\*([\d.]+)%\*\* of matched panel donors \(([\d.]+)% ≤ \$25\) \|"
     r"[\s\S]{0,90}?\| > \$99 \| ([\d.]+)% \|[\s\S]{0,90}?\| > \$50 \| ([\d.]+)% \|",
     ("belowfloor_fed_pct", "belowfloor_wa_pdc_pct", "wa_state_donor_le100_pct",
      "wa_state_donor_le25_pct", "belowfloor_ny_state_pct", "belowfloor_id_state_pct"), 0.05),
    # --- Appendix A: every figure is a restatement, so every one is probed ---
    ("AppA all-tier vs primary NY 65+", "appa",
     r"why the ([\d.]+)% differs from the ([\d.]+)% the primary specification",
     ("ny_fedall_b65", "ny_fed_b65"), 0.05),
    ("AppA resolution rates restated", "appa",
     r"resolving ([\d.]+)% of ID and ([\d.]+)% of NY state matched donors",
     ("id_state_x_agg", "ny_state_x_agg"), 0.05),
    ("AppA federal resolution range restated", "appa",
     r"resolution is ([\d.]+)[–-]([\d.]+)%", ("id_fed_x_agg", "ny_fed_x_agg"), 0.05),
    ("AppA bound figures restated", "appa",
     r"NY unaffiliated ([\d.]+)% against ([\d.]+)%; ID unaffiliated ([\d.]+)% against "
     r"([\d.]+)%",
     ("ny_fed_bnd_NOPARTY_donly", "ny_fed_bnd_NOPARTY_adverse",
      "id_fed_bnd_UNAFF_donly", "id_fed_bnd_UNAFF_adverse"), 0.05),
    ("AppA Idaho state crossover restated", "appa",
     r"untraced and the ([\d.]+)% D-only share of resolved",
     ("id_state_x_REP_donly",), 0.05),
    ("AppA below-floor figures restated", "appa",
     r"([\d.]+)% of federal gifts are ≤\$200 and \*\*([\d.]+)% of Washington's matched",
     ("belowfloor_fed_pct", "wa_state_donor_le100_pct"), 0.05),
    # --- Appendix F: the rating tables, against the frozen verdict CSVs ---
    ("AppF precision table tier shares", "appf_precision",
     r"\| `STRICT_ZIP5_FULL` \| ([\d.]+)[–-]([\d.]+)% \|[\s\S]{0,200}?"
     r"\| `STRICT_ZIP5_MID` \| ([\d.]+)[–-]([\d.]+)% \|[\s\S]{0,200}?"
     r"\| `STRICT_ZIP5` \| ([\d.]+)[–-]([\d.]+)% \|[\s\S]{0,200}?"
     r"\| `RELAXED_ZIP3_MID` \| ([\d.]+)[–-]([\d.]+)% \|",
     ("tier0_share_lo", "tier0_share_hi", "tier1_share_lo", "tier1_share_hi",
      "tier2_share_lo", "tier2_share_hi", "tier3_share_lo", "tier3_share_hi"), 0.05),
    ("AppF weighted-precision panel n, WA federal", "appf_weighted",
     r"\| WA federal \| ([\d,]+) \|", ("appf_wa_fed_rows",), 0),
    ("AppF weighted-precision panel n, WA state", "appf_weighted",
     r"\| WA state \| ([\d,]+) \|", ("appf_wa_state_pos",), 0),
    ("AppF weighted-precision panel n, NY federal", "appf_weighted",
     r"\| NY federal \| ([\d,]+) \|", ("appf_ny_fed_rows",), 0),
    ("AppF weighted-precision panel n, NY state", "appf_weighted",
     r"\| NY state \| ([\d,]+) \|", ("appf_ny_state_rows",), 0),
    ("AppF weighted-precision panel n, ID federal", "appf_weighted",
     r"\| ID federal \| ([\d,]+) \|", ("appf_id_fed_rows",), 0),
    ("AppF weighted-precision panel n, ID state", "appf_weighted",
     r"\| ID state \| ([\d,]+) \|", ("appf_id_state_rows",), 0),
    ("AppF donor-weighted total and its U bound", "appf_weighted",
     r"donor-weighted, all six\*\* \| \| \*\*([\d.]+)%\*\* \| \*\*([\d.]+)%\*\*",
     ("val_wprec_all", "val_wprec_all_u"), 0.05),
    ("AppF the two WA-state denominators and their gap", "appf_weighted",
     r"as \*\*([\d,]+)\*\* in the tier and household tables and as \*\*([\d,]+)\*\* here, a difference of \*\*([\d,]+)\*\*",
     ("appf_wa_state_rows", "appf_wa_state_pos", "appf_wa_state_gap"), 0),
    ("AppF dollar-band precision", "appf_weighted",
     r"([\d.]+)% in the top decile of matched\s+dollars against ([\d.]+)% in deciles",
     ("val_band_top", "val_band_rest"), 0.05),
    ("AppF full-name top-decile detection", "appf_weighted",
     r"\*\*no error was detected among the (\d+) records sampled there\*\* \((\d+) of (\d+) rated Y\)",
     ("val_full_top_n", "val_full_top_y", "val_full_top_n"), 0),
    # The from-scratch heuristic's own output, quoted in the paper's disclosure that the
    # published 1.85% / 2.08% pair could not be independently confirmed. Probed rather than
    # exempted: it is this verifier's number, so it is exactly the kind that must not drift.
    ("AppF independent name-order heuristic", "appf_modes",
     r"measures ([\d.]+)% of rows and ([\d.]+)% of dollars",
     ("appf_wa_nameorder_pct", "appf_wa_nameorder_dollar_pct"), 0.05),
    ("AppF Idaho organisation shares", "appf_modes",
     r"\*\*([\d.]+)% of Idaho Sunshine rows but ([\d.]+)%\s+of its dollars\*\* \(\$([\d.]+)M of \$([\d.]+)M\)",
     ("appf_id_org_pct", "appf_id_org_dollar_pct", "appf_id_org_m",
      "appf_id_total_m"), 0.05),
    ("AppF precision row, STRICT_ZIP5_FULL", "appf_precision",
     r"\| `STRICT_ZIP5_FULL` \| [\d.–-]+% \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| \*{0,2}([\d.]+)%\*{0,2} \| \[([\d.]+)[–-]([\d.]+)\] \|",
     ("val_t0_n", "val_t0_y", "val_t0_nc", "val_t0_np", "val_t0_u",
      "val_t0_prec", "val_t0_lo", "val_t0_hi"), 0.05),
    ("AppF precision row, STRICT_ZIP5_MID", "appf_precision",
     r"\| `STRICT_ZIP5_MID` \| [\d.–-]+% \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| \*{0,2}([\d.]+)%\*{0,2} \| \[([\d.]+)[–-]([\d.]+)\] \|",
     ("val_t1_n", "val_t1_y", "val_t1_nc", "val_t1_np", "val_t1_u",
      "val_t1_prec", "val_t1_lo", "val_t1_hi"), 0.05),
    ("AppF precision row, STRICT_ZIP5", "appf_precision",
     r"\| `STRICT_ZIP5` \| [\d.–-]+% \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| \*{0,2}([\d.]+)%\*{0,2} \| \[([\d.]+)[–-]([\d.]+)\] \|",
     ("val_t2_n", "val_t2_y", "val_t2_nc", "val_t2_np", "val_t2_u",
      "val_t2_prec", "val_t2_lo", "val_t2_hi"), 0.05),
    ("AppF precision row, RELAXED_ZIP3_MID", "appf_precision",
     r"\| `RELAXED_ZIP3_MID` \| [\d.–-]+% \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| \*{0,2}([\d.]+)%\*{0,2} \| \[([\d.]+)[–-]([\d.]+)\] \|",
     ("val_t3_n", "val_t3_y", "val_t3_nc", "val_t3_np", "val_t3_u",
      "val_t3_prec", "val_t3_lo", "val_t3_hi"), 0.05),
    ("AppF indeterminate count", "appf_precision",
     r"because only (\d+) of (\d+) records were\s+indeterminate",
     ("val_indeterminate", "val_total_n"), 0),
    ("AppF raw sample mean", "appf_weighted",
     r"its raw mean \(([\d.]+)%\)", ("val_raw_mean",), 0.05),
    ("AppF weighted precision, WA federal", "appf_weighted",
     r"\| WA federal \| [\d,]+ \| \*{0,2}([\d.]+)%\*{0,2} \| ([\d.]+)% \|",
     ("val_wprec_wa_fed", "val_wprec_wa_fed_u"), 0.05),
    ("AppF weighted precision, WA state", "appf_weighted",
     r"\| WA state \| [\d,]+ \| \*{0,2}([\d.]+)%\*{0,2} \| ([\d.]+)% \|",
     ("val_wprec_wa_state", "val_wprec_wa_state_u"), 0.05),
    ("AppF weighted precision, NY federal", "appf_weighted",
     r"\| NY federal \| [\d,]+ \| \*{0,2}([\d.]+)%\*{0,2} \| ([\d.]+)% \|",
     ("val_wprec_ny_fed", "val_wprec_ny_fed_u"), 0.05),
    ("AppF weighted precision, NY state", "appf_weighted",
     r"\| NY state \| [\d,]+ \| \*{0,2}([\d.]+)%\*{0,2} \| ([\d.]+)% \|",
     ("val_wprec_ny_state", "val_wprec_ny_state_u"), 0.05),
    ("AppF weighted precision, ID federal", "appf_weighted",
     r"\| ID federal \| [\d,]+ \| \*{0,2}([\d.]+)%\*{0,2} \| ([\d.]+)% \|",
     ("val_wprec_id_fed", "val_wprec_id_fed_u"), 0.05),
    ("AppF weighted precision, ID state", "appf_weighted",
     r"\| ID state \| [\d,]+ \| \*{0,2}([\d.]+)%\*{0,2} \| ([\d.]+)% \|",
     ("val_wprec_id_state", "val_wprec_id_state_u"), 0.05),
    ("AppF error-mode totals", "appf_modes",
     r"Of the (\d+) confirmed false matches", ("val_confirmed_false",), 0),
    ("AppF household mode and its tier split", "appf_modes",
     r"household / relative\) \| (\d+) \| initial-based tiers only — (\d+) `STRICT_ZIP5`, (\d+) `RELAXED_ZIP3_MID`, (\d+) `STRICT_ZIP5_MID`",
     ("val_mode_household", "val_household_t2", "val_household_t3",
      "val_household_t1"), 0),
    ("AppF organisation mode", "appf_modes",
     r"parsed as a person \| (\d+) \|", ("val_mode_org",), 0),
    ("AppF name-order mode", "appf_modes",
     # The paper's row quotes the misparse in typographic quotes; matched by class rather
     # than by escaping, so the probe survives a quote-style change.
     r"read as .Last First.\) \| (\d+) \|", ("val_mode_nameorder",), 0),
    # --- D1: the structural counts and the adversarial bound ---
    ("D1 structural, colliding-key share of roll", "sensitivity",
     r"are \*\*([\d.]+)%\*\* of Washington's active roll, \*\*([\d.]+)%\*\* of New "
     r"York's and \*\*([\d.]+)%\*\* of Idaho's",
     ("sens_wa_collide_pct", "sens_ny_collide_pct", "sens_id_collide_pct"), 0.05),
    ("D1 structural, household pool share", "sensitivity",
     r"is \*\*([\d.]+)%, ([\d.]+)% and ([\d.]+)%\*\* of those rolls",
     ("sens_wa_pool_pct", "sens_ny_pool_pct", "sens_id_pool_pct"), 0.05),
    ("D1 bound, WA federal", "sensitivity",
     r"\| WA federal \| ([\d.]+) → \*\*([\d.]+)\*\* \| \*party unpublished\* \| ([\d.]+) → \*\*([\d.]+)\*\* \|",
     ("sens_wa_fed_b65", "sens_wa_fed_b65_bd", "sens_wa_fed_top1", "sens_wa_fed_top1_bd"), 0.05),
    ("D1 bound, WA state", "sensitivity",
     r"\| WA state \| ([\d.]+) → \*\*([\d.]+)\*\* \| \*party unpublished\* \| ([\d.]+) → \*\*([\d.]+)\*\* \|",
     ("sens_wa_state_b65", "sens_wa_state_b65_bd", "sens_wa_state_top1", "sens_wa_state_top1_bd"), 0.05),
    ("D1 bound, NY federal", "sensitivity",
     r"\| NY federal \| ([\d.]+) → \*\*([\d.]+)\*\* \| ([\d.]+) → \*\*([\d.]+)\*\* \| ([\d.]+) → \*\*([\d.]+)\*\* \|",
     ("sens_ny_fed_b65", "sens_ny_fed_b65_bd", "sens_ny_fed_dem", "sens_ny_fed_dem_bd",
      "sens_ny_fed_top1", "sens_ny_fed_top1_bd"), 0.05),
    ("D1 bound, NY state", "sensitivity",
     r"\| NY state \| ([\d.]+) → \*\*([\d.]+)\*\* \| ([\d.]+) → \*\*([\d.]+)\*\* \| ([\d.]+) → \*\*([\d.]+)\*\* \|",
     ("sens_ny_state_b65", "sens_ny_state_b65_bd", "sens_ny_state_dem", "sens_ny_state_dem_bd",
      "sens_ny_state_top1", "sens_ny_state_top1_bd"), 0.05),
    ("D1 bound, ID federal", "sensitivity",
     r"\| ID federal \| ([\d.]+) → \*\*([\d.]+)\*\* \| ([\d.]+) → \*\*([\d.]+)\*\* \| ([\d.]+) → \*\*([\d.]+)\*\* \|",
     ("sens_id_fed_b65", "sens_id_fed_b65_bd", "sens_id_fed_dem", "sens_id_fed_dem_bd",
      "sens_id_fed_top1", "sens_id_fed_top1_bd"), 0.05),
    ("D1 bound, ID state", "sensitivity",
     r"\| ID state \| ([\d.]+) → \*\*([\d.]+)\*\* \| ([\d.]+) → \*\*([\d.]+)\*\* \| ([\d.]+) → \*\*([\d.]+)\*\* \|",
     ("sens_id_state_b65", "sens_id_state_b65_bd", "sens_id_state_dem", "sens_id_state_dem_bd",
      "sens_id_state_top1", "sens_id_state_top1_bd"), 0.05),
    # --- D2: the county decomposition ---
    ("D2 NY federal · New York (Manhattan)", "f2_tail",
     r"\| NY federal · New York \(Manhattan\) \| ([\d.]+) \| \*{0,2}([\d.]+)\*{0,2} \| \*{0,2}([\d.]+)\*{0,2} \|",
     ("cty_ny_fed_newyork_mult", "cty_ny_fed_newyork_part", "cty_ny_fed_newyork_inten"), 0.005),
    ("D2 NY state · New York", "f2_tail",
     r"\| NY state · New York \| ([\d.]+) \| \*{0,2}([\d.]+)\*{0,2} \| \*{0,2}([\d.]+)\*{0,2} \|",
     ("cty_ny_state_newyork_mult", "cty_ny_state_newyork_part", "cty_ny_state_newyork_inten"), 0.005),
    ("D2 WA federal · King", "f2_tail",
     r"\| WA federal · King \| ([\d.]+) \| \*{0,2}([\d.]+)\*{0,2} \| \*{0,2}([\d.]+)\*{0,2} \|",
     ("cty_wa_fed_king_mult", "cty_wa_fed_king_part", "cty_wa_fed_king_inten"), 0.005),
    ("D2 WA state · King", "f2_tail",
     r"\| WA state · King \| ([\d.]+) \| \*{0,2}([\d.]+)\*{0,2} \| \*{0,2}([\d.]+)\*{0,2} \|",
     ("cty_wa_state_king_mult", "cty_wa_state_king_part", "cty_wa_state_king_inten"), 0.005),
    ("D2 ID federal · Blaine", "f2_tail",
     r"\| ID federal · Blaine \| ([\d.]+) \| \*{0,2}([\d.]+)\*{0,2} \| \*{0,2}([\d.]+)\*{0,2} \|",
     ("cty_id_fed_blaine_mult", "cty_id_fed_blaine_part", "cty_id_fed_blaine_inten"), 0.005),
    ("D2 ID state · Blaine", "f2_tail",
     r"\| ID state · Blaine \| ([\d.]+) \| \*{0,2}([\d.]+)\*{0,2} \| \*{0,2}([\d.]+)\*{0,2} \|",
     ("cty_id_state_blaine_mult", "cty_id_state_blaine_part", "cty_id_state_blaine_inten"), 0.005),
    ("D2 ID federal · Bonneville", "f2_tail",
     r"\| ID federal · Bonneville \| ([\d.]+) \| \*{0,2}([\d.]+)\*{0,2} \| \*{0,2}([\d.]+)\*{0,2} \|",
     ("cty_id_fed_bonneville_mult", "cty_id_fed_bonneville_part", "cty_id_fed_bonneville_inten"), 0.005),
    ("D2 WA federal · San Juan", "f2_tail",
     r"\| WA federal · San Juan \| ([\d.]+) \| \*{0,2}([\d.]+)\*{0,2} \| \*{0,2}([\d.]+)\*{0,2} \|",
     ("cty_wa_fed_sanjuan_mult", "cty_wa_fed_sanjuan_part", "cty_wa_fed_sanjuan_inten"), 0.005),
    ("D2 NY federal · Tompkins", "f2_tail",
     r"\| NY federal · Tompkins \| ([\d.]+) \| \*{0,2}([\d.]+)\*{0,2} \| \*{0,2}([\d.]+)\*{0,2} \|",
     ("cty_ny_fed_tompkins_mult", "cty_ny_fed_tompkins_part", "cty_ny_fed_tompkins_inten"), 0.005),
    # --- D3: the non-match cascade ---
    ("D3 cascade, WA federal", "matchrate",
     r"\| WA federal \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \| ([\d.]+)% \|",
     ("res_wa_fed_matched", "res_wa_fed_guard", "res_wa_fed_inactive", "res_wa_fed_difzip", "res_wa_fed_nameform", "res_wa_fed_none"), 0.05),
    ("D3 cascade, WA state", "matchrate",
     r"\| WA state \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \| ([\d.]+)% \|",
     ("res_wa_state_matched", "res_wa_state_guard", "res_wa_state_inactive", "res_wa_state_difzip", "res_wa_state_nameform", "res_wa_state_none"), 0.05),
    ("D3 cascade, NY federal", "matchrate",
     r"\| NY federal \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \| ([\d.]+)% \|",
     ("res_ny_fed_matched", "res_ny_fed_guard", "res_ny_fed_inactive", "res_ny_fed_difzip", "res_ny_fed_nameform", "res_ny_fed_none"), 0.05),
    ("D3 cascade, NY state", "matchrate",
     r"\| NY state \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \| ([\d.]+)% \|",
     ("res_ny_state_matched", "res_ny_state_guard", "res_ny_state_inactive", "res_ny_state_difzip", "res_ny_state_nameform", "res_ny_state_none"), 0.05),
    ("D3 cascade, ID federal", "matchrate",
     r"\| ID federal \| ([\d.]+)% \| ([\d.]+)% \| — \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \| ([\d.]+)% \|",
     ("res_id_fed_matched", "res_id_fed_guard", "res_id_fed_difzip", "res_id_fed_nameform", "res_id_fed_none"), 0.05),
    ("D3 cascade, ID state", "matchrate",
     r"\| ID state \| ([\d.]+)% \| ([\d.]+)% \| — \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \| ([\d.]+)% \|",
     ("res_id_state_matched", "res_id_state_guard", "res_id_state_difzip", "res_id_state_nameform", "res_id_state_none"), 0.05),
    # --- the match-rate tables. Every cell asserted; the recall figures are the
    # paper's answer to "how big is the floor" and had no derivation before today.
    ("Match rate, WA federal", "matchrate",
     r"\| WA federal \| ([\d,]+) \| ([\d,]+) \| \*\*([\d.]+)%\*\* \| \$([\d,.]+)M \| \$([\d,.]+)M \| \*\*([\d.]+)%\*\* \|",
     ("mr_wa_fed_ids", "mr_wa_fed_matched", "mr_wa_fed_recall", "mr_wa_fed_amt_m",
      "mr_wa_fed_matched_m", "mr_wa_fed_cov"), 0.05),
    ("Match rate, WA state", "matchrate",
     r"\| WA state \| ([\d,]+) \| ([\d,]+) \| \*\*([\d.]+)%\*\* \| \$([\d,.]+)M \| \$([\d,.]+)M \| \*\*([\d.]+)%\*\* \|",
     ("mr_wa_state_ids", "mr_wa_state_matched", "mr_wa_state_recall", "mr_wa_state_amt_m",
      "mr_wa_state_matched_m", "mr_wa_state_cov"), 0.05),
    ("Match rate, NY federal", "matchrate",
     r"\| NY federal \| ([\d,]+) \| ([\d,]+) \| \*\*([\d.]+)%\*\* \| \$([\d,.]+)M \| \$([\d,.]+)M \| \*\*([\d.]+)%\*\* \|",
     ("mr_ny_fed_ids", "mr_ny_fed_matched", "mr_ny_fed_recall", "mr_ny_fed_amt_m",
      "mr_ny_fed_matched_m", "mr_ny_fed_cov"), 0.05),
    ("Match rate, NY state", "matchrate",
     r"\| NY state \| ([\d,]+) \| ([\d,]+) \| \*\*([\d.]+)%\*\* \| \$([\d,.]+)M \| \$([\d,.]+)M \| \*\*([\d.]+)%\*\* \|",
     ("mr_ny_state_ids", "mr_ny_state_matched", "mr_ny_state_recall", "mr_ny_state_amt_m",
      "mr_ny_state_matched_m", "mr_ny_state_cov"), 0.05),
    ("Match rate, ID federal", "matchrate",
     r"\| ID federal \| ([\d,]+) \| ([\d,]+) \| \*\*([\d.]+)%\*\* \| \$([\d,.]+)M \| \$([\d,.]+)M \| \*\*([\d.]+)%\*\* \|",
     ("mr_id_fed_ids", "mr_id_fed_matched", "mr_id_fed_recall", "mr_id_fed_amt_m",
      "mr_id_fed_matched_m", "mr_id_fed_cov"), 0.05),
    ("Match rate, ID state", "matchrate",
     r"\| ID state \| ([\d,]+) \| ([\d,]+) \| \*\*([\d.]+)%\*\* \| \$([\d,.]+)M \| \$([\d,.]+)M \| \*\*([\d.]+)%\*\* \|",
     ("mr_id_state_ids", "mr_id_state_matched", "mr_id_state_recall", "mr_id_state_amt_m",
      "mr_id_state_matched_m", "mr_id_state_cov"), 0.05),
    ("Guard cost, WA federal", "matchrate",
     r"\| WA federal \| ([\d,]+) \| ([\d,]+) \(\*\*([\d.]+)%\*\*\) \| ([\d,]+) \|",
     ("mr_wa_fed_matched", "mr_wa_fed_guard_n", "mr_wa_fed_guard_pct", "mr_wa_fed_none_n"), 0.05),
    ("Guard cost, WA state", "matchrate",
     r"\| WA state \| ([\d,]+) \| ([\d,]+) \(\*\*([\d.]+)%\*\*\) \| ([\d,]+) \|",
     ("mr_wa_state_matched", "mr_wa_state_guard_n", "mr_wa_state_guard_pct", "mr_wa_state_none_n"), 0.05),
    ("Guard cost, NY federal", "matchrate",
     r"\| NY federal \| ([\d,]+) \| ([\d,]+) \(\*\*([\d.]+)%\*\*\) \| ([\d,]+) \|",
     ("mr_ny_fed_matched", "mr_ny_fed_guard_n", "mr_ny_fed_guard_pct", "mr_ny_fed_none_n"), 0.05),
    ("Guard cost, NY state", "matchrate",
     r"\| NY state \| ([\d,]+) \| ([\d,]+) \(\*\*([\d.]+)%\*\*\) \| ([\d,]+) \|",
     ("mr_ny_state_matched", "mr_ny_state_guard_n", "mr_ny_state_guard_pct", "mr_ny_state_none_n"), 0.05),
    ("Guard cost, ID federal", "matchrate",
     r"\| ID federal \| ([\d,]+) \| ([\d,]+) \(\*\*([\d.]+)%\*\*\) \| ([\d,]+) \|",
     ("mr_id_fed_matched", "mr_id_fed_guard_n", "mr_id_fed_guard_pct", "mr_id_fed_none_n"), 0.05),
    ("Guard cost, ID state", "matchrate",
     r"\| ID state \| ([\d,]+) \| ([\d,]+) \(\*\*([\d.]+)%\*\*\) \| ([\d,]+) \|",
     ("mr_id_state_matched", "mr_id_state_guard_n", "mr_id_state_guard_pct", "mr_id_state_none_n"), 0.05),
    ("Methods, recall range restated in the confound list", "methods",
     r"reaches the panels unequally\*\*, from ([\d.]+)% to ([\d.]+)% of resident",
     ("_mr_recall_lo", "_mr_recall_hi"), 0.05),
    ("Match rate, out-of-state shares by layer", "matchrate",
     r"NYSBOE layer is \*\*([\d.]+)%\*\* out-of-state, WA PDC ([\d.]+)% and Idaho "
     r"Sunshine ([\d.]+)%",
     ("mr_ny_state_outstate_pct", "mr_wa_state_outstate_pct",
      "mr_id_state_outstate_pct"), 0.05),
    ("Match rate, PDC comma-less name share", "matchrate",
     r"the PDC files \*\*([\d.]+)%\*\* of its contributor names",
     ("mr_wa_state_nocomma_pct",), 0.05),
    ("Match rate, prose ranges", "matchrate",
     r"capture \*\*([\d.]+)[–-]([\d.]+)%\*\* of resident donor identities and \*\*([\d.]+)[–-]([\d.]+)%\*\*",
     ("_mr_recall_lo", "_mr_recall_hi", "_mr_cov_lo", "_mr_cov_hi"), 0.05),
    ("Guard cost, prose range", "matchrate",
     r"uniqueness guard costs ([\d.]+)[–-]([\d.]+)%",
     ("_mr_guard_lo", "_mr_guard_hi"), 0.05),
    # --- the methods section. Mostly restatement, asserted so it cannot drift. ---
    ("Methods, pooled vs panel top-1%", "methods",
     r"top-1% reads ([\d.]+)% pooled\s*against ([\d.]+)% federal and ([\d.]+)% state",
     ("wa_pooled_top1", "wa_fed_top1", "wa_state_top1"), 0.05),
    ("Methods, WA vote records", "methods",
     r"([\d.]+)M individual vote records", ("wa_vote_records_m",), 0.05),
    ("abstract top-1% by state", None,
     r"top 1% of donors suppl(?:y|ying) ([\d.]+)% of\s+federal dollars in Washington, "
     r"([\d.]+)% in New York and ([\d.]+)% in Idaho",
     ("wa_fed_top1", "ny_fed_top1", "id_fed_top1"), 0.05),
    ("F2 prose, state-vs-federal top-1%", "f2",
     r"more\*{0,2} concentrated in Washington \(([\d.]+)% vs ([\d.]+)%\) and Idaho "
     r"\(([\d.]+)% vs ([\d.]+)%\) but \*{0,2}less\*{0,2} so in New York "
     r"\(([\d.]+)% vs ([\d.]+)%\)",
     ("wa_state_top1", "wa_fed_top1", "id_state_top1", "id_fed_top1",
      "ny_state_top1", "ny_fed_top1"), 0.05),
    ("F2 prose, ID aligned top-1%", "f2",
     r"aligned federal ([\d.]+)% against state ([\d.]+)%",
     ("id_fedal_top1", "id_state_top1"), 0.05),
    # --- Finding 2 geography, on counties with roll-share multipliers
    ("F2 geography table, all six panels", "f2",
     r"\| WA federal \| King \(Seattle\) \| ([\d.]+)% \| ([\d.]+)% \| \*{0,2}([\d.]+)×"
     r"\*{0,2} \| ([\d.]+)% \| "
     r"\| WA state \| King \| ([\d.]+)% \| ([\d.]+)% \| \*{0,2}([\d.]+)×\*{0,2} \| "
     r"([\d.]+)% \| "
     r"\| NY federal \| New York \(Manhattan\) \| ([\d.]+)% \| ([\d.]+)% \| "
     r"\*{0,2}([\d.]+)×\*{0,2} \| ([\d.]+)% \| "
     r"\| NY state \| New York \| ([\d.]+)% \| ([\d.]+)% \| \*{0,2}([\d.]+)×\*{0,2} \| "
     r"([\d.]+)% \| "
     r"\| ID federal \| Ada \(Boise\) \| ([\d.]+)% \| ([\d.]+)% \| \*{0,2}([\d.]+)×"
     r"\*{0,2} \| ([\d.]+)% \| "
     r"\| ID state \| Ada \| ([\d.]+)% \| ([\d.]+)% \| \*{0,2}([\d.]+)×\*{0,2} \| "
     r"([\d.]+)% \|",
     ("wa_fed_cty0_pct", "wa_fed_cty0_roll", "wa_fed_cty0_mult", "wa_fed_cty_top3",
      "wa_state_cty0_pct", "wa_state_cty0_roll", "wa_state_cty0_mult", "wa_state_cty_top3",
      "ny_fed_cty0_pct", "ny_fed_cty0_roll", "ny_fed_cty0_mult", "ny_fed_cty_top3",
      "ny_state_cty0_pct", "ny_state_cty0_roll", "ny_state_cty0_mult", "ny_state_cty_top3",
      "id_fed_cty0_pct", "id_fed_cty0_roll", "id_fed_cty0_mult", "id_fed_cty_top3",
      "id_state_cty0_pct", "id_state_cty0_roll", "id_state_cty0_mult", "id_state_cty_top3"),
     0.05),
    ("F2 geography prose, WA raw vs multiplier", "f2",
     r"King ([\d.]+)% of federal\s+dollars\).*?King already holds ([\d.]+)% of the",
     ("wa_fed_cty0_pct", "wa_fed_cty0_roll"), 0.05),
    ("F2 geography prose, Manhattan extreme", "f2",
     r"dollars, \*{0,2}([\d.]+)×\*{0,2} its share of the roll",
     "ny_fed_cty0_mult", 0.005),
    ("F2 geography prose, Ada is population not concentration", "f2",
     r"it holds \*{0,2}([\d.]+)%\*{0,2} of Idaho's roll, so its ([\d.]+)% of federal "
     r"dollars is only \*{0,2}([\d.]+)×\*{0,2}",
     ("id_fed_cty0_roll", "id_fed_cty0_pct", "id_fed_cty0_mult"), 0.05),
    ("F2 geography prose, Blaine", "f2",
     r"has\s+\*{0,2}([\d.]+)%\*{0,2} of the roll and supplies \*{0,2}([\d.]+)%\*{0,2} of "
     r"federal dollars, a multiplier of \*{0,2}([\d.]+)×\*{0,2}.*?from ([\d,]+) donors",
     ("id_fed_blaine_roll", "id_fed_blaine_pct", "id_fed_blaine_mult", "id_fed_blaine_n"),
     0.05),
    ("F2 geography prose, panel moves", "f2_tail",
     r"multiplier falls \*{0,2}([\d.]+)× → ([\d.]+)×\*{0,2} between the federal and state "
     r"panels, as\s+suburban \*{0,2}Nassau \(([\d.]+)%, ([\d.]+)×\)\*{0,2} and "
     r"\*{0,2}Suffolk \(([\d.]+)%, ([\d.]+)×\)",
     ("ny_fed_cty0_mult", "ny_state_cty0_mult", "ny_state_cty1_pct", "ny_state_cty1_mult",
      "ny_state_cty2_pct", "ny_state_cty2_mult"), 0.05),
    ("F2 geography prose, WA and ID panel moves + top-3", "f2_tail",
     r"\(([\d.]+)× → ([\d.]+)×\) and Idaho's Ada moves the \*other\* way "
     r"\(([\d.]+)× → ([\d.]+)×\).*?WA \*{0,2}([\d.]+)%\*{0,2}, NY \*{0,2}([\d.]+)%"
     r"\*{0,2} — and\s+collapses to \*{0,2}([\d.]+)%\*{0,2}",
     ("wa_fed_cty0_mult", "wa_state_cty0_mult", "id_fed_cty0_mult", "id_state_cty0_mult",
      "wa_fed_cty_top3", "ny_fed_cty_top3", "ny_state_cty_top3"), 0.05),

    # --- Appendix E's bootstrap table: point estimates probed, intervals exempt by owner
    ("Appendix E bootstrap note, the two WA state counts", "appe_bootstrap",
     r"state panel reads ([\d,]+) against the ([\d,]+) in Finding 2",
     ("wa_state_npos", "wa_state_n"), 0),
    ("Appendix E bootstrap table, point estimates", "appe_bootstrap",
     r"\| WA federal \| ([\d,]+) \| ([\d.]+)% \| \[[\d.–-]+\] \| ([\d.]+)% \| \[[\d.–-]+\] \| "
     r"([\d.]+) \| \[[\d.–-]+\] \| "
     r"\| WA state \| ([\d,]+) \| ([\d.]+)% \| \[[\d.–-]+\] \| ([\d.]+)% \| \[[\d.–-]+\] \| "
     r"([\d.]+) \| \[[\d.–-]+\] \| "
     r"\| NY federal \| ([\d,]+) \| ([\d.]+)% \| \[[\d.–-]+\] \| ([\d.]+)% \| \[[\d.–-]+\] \| "
     r"([\d.]+) \| \[[\d.–-]+\] \| "
     r"\| NY state \| ([\d,]+) \| ([\d.]+)% \| \[[\d.–-]+\] \| ([\d.]+)% \| \[[\d.–-]+\] \| "
     r"([\d.]+) \| \[[\d.–-]+\] \| "
     r"\| ID federal \| ([\d,]+) \| ([\d.]+)% \| \[[\d.–-]+\] \| ([\d.]+)% \| \[[\d.–-]+\] \| "
     r"([\d.]+) \| \[[\d.–-]+\] \| "
     r"\| ID state \| ([\d,]+) \| ([\d.]+)% \| \[[\d.–-]+\] \| ([\d.]+)% \| \[[\d.–-]+\] \| "
     r"([\d.]+) \| \[[\d.–-]+\] \|",
     ("wa_fed_npos", "wa_fed_top1", "wa_fed_top10", "wa_fed_gini",
      "wa_state_npos", "wa_state_top1", "wa_state_top10", "wa_state_gini",
      "ny_fed_npos", "ny_fed_top1", "ny_fed_top10", "ny_fed_gini",
      "ny_state_npos", "ny_state_top1", "ny_state_top10", "ny_state_gini",
      "id_fed_npos", "id_fed_top1", "id_fed_top10", "id_fed_gini",
      "id_state_npos", "id_state_top1", "id_state_top10", "id_state_gini"), 0.05),

    # --- Finding 3: party of record (NY), table then prose
    ("F3 NY party table", "f3",
     r"\| DEM \| ([\d.]+)% \| ([\d.]+)% \| \*{0,2}\+([\d.]+)\*{0,2} \| ([\d.]+)% \| "
     r"([\d.]+)% \| \*{0,2}\+([\d.]+)\*{0,2} \| ([\d.]+)% \| "
     r"\| REP \| ([\d.]+)% \| ([\d.]+)% \| [−-]([\d.]+) \| ([\d.]+)% \| ([\d.]+)% \| "
     r"\+([\d.]+) \| ([\d.]+)% \| "
     r"\| NOPARTY \(blank\) \| ([\d.]+)% \| ([\d.]+)% \| \*{0,2}[−-]([\d.]+)\*{0,2} \| "
     r"([\d.]+)% \| ([\d.]+)% \| \*{0,2}[−-]([\d.]+)\*{0,2} \| ([\d.]+)% \| "
     r"\| OTHER \(minor\) \| ([\d.]+)% \| ([\d.]+)% \| [−-]([\d.]+) \| ([\d.]+)% \| "
     r"([\d.]+)% \| [−-]([\d.]+) \| ([\d.]+)% \|",
     ("ny_fed_reg_DEM", "ny_fed_don_DEM", "ny_fed_skew_DEM", "ny_fed_dol_DEM",
      "ny_state_don_DEM", "ny_state_skew_DEM", "ny_state_dol_DEM",
      "ny_fed_reg_REP", "ny_fed_don_REP", "_neg_ny_fed_skew_REP", "ny_fed_dol_REP",
      "ny_state_don_REP", "ny_state_skew_REP", "ny_state_dol_REP",
      "ny_fed_reg_NOPARTY", "ny_fed_don_NOPARTY", "_neg_ny_fed_skew_NOPARTY",
      "ny_fed_dol_NOPARTY", "ny_state_don_NOPARTY", "_neg_ny_state_skew_NOPARTY",
      "ny_state_dol_NOPARTY",
      "ny_fed_reg_OTHER", "ny_fed_don_OTHER", "_neg_ny_fed_skew_OTHER",
      "ny_fed_dol_OTHER", "ny_state_don_OTHER", "_neg_ny_state_skew_OTHER",
      "ny_state_dol_OTHER"), 0.05),
    ("F3 NY prose, DEM skew + dollar share", "f3",
     r"Registered Democrats are \+([\d.]+) points over their share of the active roll in "
     r"federal money and supply \*{0,2}([\d.]+)% of federal matched dollars",
     ("ny_fed_skew_DEM", "ny_fed_dol_DEM"), 0.05),
    ("F3 NY prose, DEM skew falls federal->state", "f3",
     r"falls by roughly two-fifths in state money \(\+([\d.]+) → \+([\d.]+)\)",
     ("ny_fed_skew_DEM", "ny_state_skew_DEM"), 0.05),
    ("F3 NY prose, REP panel move", "f3",
     r"Republicans move from slightly under-represented to slightly over "
     r"\([−-]([\d.]+) → \+([\d.]+)\)",
     ("_neg_ny_fed_skew_REP", "ny_state_skew_REP"), 0.05),

    # --- the crossover tables' resolution rates, restated in three places
    ("crossover, state rows sum to the published panels", "xover_id",
     r"sum to the published panels \(NY ([\d,]+); ID ([\d,]+)\)",
     ("ny_state_n", "id_state_n"), 0),
    ("crossover, NY state indicative-only rate", "xover_id",
     r"At ([\d.]+)% aggregate resolution the NY state column", "ny_state_x_agg", 0.05),
    ("crossover, DEM near-monolithic prose", "xover_id",
     r"near-monolithic\s+\(([\d.]+)% D-only among resolved recipients federally in NY, "
     r"([\d.]+)% in ID\)",
     ("ny_fed_x_DEM_donly", "id_fed_x_DEM_donly"), 0.05),
    ("crossover, unaffiliated dollar-flow prose", "xover_id",
     r"dollar-flow measure agrees \(([\d.]+)% and ([\d.]+)% of resolved dollars",
     ("ny_fed_x_NOPARTY_dold", "id_fed_x_UNAFF_dold"), 0.05),
    ("crossover, withdrawn-ratio quartet on the primary spec", "xover_id",
     r"([\d.]+)% of registered\s+Republicans with a resolved recipient classify D-only "
     r"against ([\d.]+)% of Democrats classifying\s+R-only.*?read ([\d.]+)% of resolved "
     r"Republican dollars to\s+Democrats against ([\d.]+)% of Democratic dollars",
     ("ny_fed_x_REP_donly", "ny_fed_x_DEM_ronly",
      "ny_fed_x_REP_dold", "_ny_fed_dem_dol_to_r"), 0.05),
    ("crossover aggregate resolution, all four panels", "xover_id",
     r"Aggregate resolution: NY federal \*{0,2}([\d.]+)%\*{0,2}, NY state ([\d.]+)%, "
     r"ID federal \*{0,2}([\d.]+)%\*{0,2}, ID state ([\d.]+)%",
     ("ny_fed_x_agg", "ny_state_x_agg", "id_fed_x_agg", "id_state_x_agg"), 0.05),
    ("crossover, differential resolution prose", "xover_id",
     r"([\d.]+)% for NY federal Democrats against ([\d.]+)% for the unaffiliated, and on "
     r"the NY state panel ([\d.]+)% for Republicans against ([\d.]+)% for the unaffiliated",
     ("ny_fed_x_DEM_rate", "ny_fed_x_NOPARTY_rate",
      "ny_state_x_REP_rate", "ny_state_x_NOPARTY_rate"), 0.05),
    ("crossover, ID REP D-only bound prose", "xover_id",
     r"making the \*{0,2}([\d.]+)%\*{0,2} D-only share of resolved\s+recipients an "
     r"\*{0,2}upper bound\*{0,2}.*?at ([\d.]+)% resolution from authoritative party labels, "
     r"the \*{0,2}([\d.]+)%\*{0,2} figure", ("id_state_x_REP_donly", "id_fed_x_agg", "id_fed_x_REP_donly"), 0.05),
    ("limitations, below-floor disclosure", "limits_itemization",
     r"([\d.]+)% of the federal layer's gifts are ≤\$200, ([\d.]+)% of New York's are "
     r"≤\$99, and ([\d.]+)% of Idaho's are ≤\$50.*?\*{0,2}([\d.]+)% of Washington's matched "
     r"state donors have totals at or below \$100 and ([\d.]+)% at or below\s+\$25",
     ("belowfloor_fed_pct", "belowfloor_ny_state_pct", "belowfloor_id_state_pct",
      "wa_state_donor_le100_pct", "wa_state_donor_le25_pct"), 0.05),
    ("Appendix C harmonization restatement", "appd_belowfloor",
     r"survives in all three states \(\+([\d.]+) / \+([\d.]+) / \+([\d.]+) points\)",
     ("wa_gap_h200", "ny_gap_h200", "id_gap_h200"), 0.05),
    ("Appendix D below-floor table", "appd_belowfloor",
     r"\| Federal \(FEC\) \| > \$200 / cycle \| ([\d.]+)% \| — \| "
     r"\| Washington \(PDC\) \| > \$25, then > \$100 \| ([\d.]+)% \(≤\$100\) \| "
     r"\*{0,2}([\d.]+)%\*{0,2} of matched panel donors \(([\d.]+)% ≤ \$25\) \| "
     r"\| New York \(NYSBOE\) \| > \$99 \| ([\d.]+)% \| — \| "
     r"\| Idaho \(Sunshine\) \| > \$50 \| ([\d.]+)% \| — \|",
     ("belowfloor_fed_pct", "belowfloor_wa_pdc_pct", "wa_state_donor_le100_pct",
      "wa_state_donor_le25_pct", "belowfloor_ny_state_pct", "belowfloor_id_state_pct"),
     0.05),
    ("Appendix A objection 5, below-floor", None,
     r"([\d.]+)% of federal gifts are ≤\$200 and \*{0,2}([\d.]+)% of\s+Washington's matched "
     r"state donors have totals at or below \$100",
     ("belowfloor_fed_pct", "wa_state_donor_le100_pct"), 0.05),
    ("limitations, resolution rates", "limits_xover",
     r"resolves for \*{0,2}([\d.]+)%\*{0,2} of NY federal and \*{0,2}([\d.]+)%\*{0,2} of ID "
     r"federal matched donors.*?only \*{0,2}([\d.]+)%\*{0,2} of ID state and "
     r"\*{0,2}([\d.]+)%\*{0,2} of NY state",
     ("ny_fed_x_agg", "id_fed_x_agg", "id_state_x_agg", "ny_state_x_agg"), 0.05),

    # --- Finding 3's subsection: the competitiveness bands, stated a second time
    ("F3 subsection, NY bands both panels", "f3_id_skew",
     r"federal Tossup ([\d.]+)% donor vs ([\d.]+)% registrant and Solid ([\d.]+)% vs "
     r"([\d.]+)%, state ([\d.]+)% and ([\d.]+)% against the same baselines",
     ("ny_fed_band_tossup_d", "ny_reg_band_tossup_d", "ny_fed_band_solid_d",
      "ny_reg_band_solid_d", "ny_state_band_tossup_d", "ny_state_band_solid_d"), 0.05),
    ("F3 subsection, NY Solid counts", "f3_id_skew",
     r"federal\s+matched donors \(([\d,]+) of ([\d,]+)\) live in Solid districts.*?"
     r"\(([\d,]+)\s+of ([\d,]+)\)",
     ("ny_fed_band_solid_n", "ny_fed_n", "ny_state_band_solid_n", "ny_state_n"), 0),
    ("F3 subsection, ID district-safety cut", "f3_id_skew",
     r"([\d,]+) matched donors sit in the ([\d,]+) Solid-R legislative districts \(where "
     r"the donor pool runs ([\d.]+)% Republican to ([\d.]+)% Democratic\), while the "
     r"([\d,]+) more competitive districts carry a far more balanced ([\d.]+)% Republican "
     r"/ ([\d.]+)% Democratic across ([\d,]+) donors",
     ("id_solid_n", "id_solid_lds", "id_solid_rep", "id_solid_dem",
      "id_adj_lds", "id_adj_rep", "id_adj_dem", "id_adj_n"), 0.5),

    # --- Finding 4: give <-> vote stacking
    ("F4 WA super-voter + propensity, both panels", "f4",
     r"federal matched donors are \*{0,2}([\d.]+)% super-voters versus ([\d.]+)%\*{0,2} of "
     r"non-donors \(mean turnout propensity ([\d.]+) vs ([\d.]+)\); the state panel is "
     r"nearly identical at \*{0,2}([\d.]+)% versus ([\d.]+)%\*{0,2} \(([\d.]+) vs "
     r"([\d.]+)\)",
     ("wa_fed_super_d", "wa_fed_super_n", "wa_fed_prop_d", "wa_fed_prop_n",
      "wa_state_super_d", "wa_state_super_n", "wa_state_prop_d", "wa_state_prop_n"),
     0.05),
    ("F4 NY generals + super-voters, both panels", "f4",
     r"voted in \*{0,2}([\d.]+) of the last four federal generals on average versus "
     r"([\d.]+)\*{0,2} for non-donors, and \*{0,2}([\d.]+)% are super-voters \(≥3 of 4\) "
     r"versus ([\d.]+)%\*{0,2}.*?\(([\d.]+) vs ([\d.]+); \*{0,2}([\d.]+)% versus "
     r"([\d.]+)%\*{0,2}\)",
     ("ny_fed_gen_d", "ny_fed_gen_n", "ny_fed_sup_d", "ny_fed_sup_n",
      "ny_state_gen_d", "ny_state_gen_n", "ny_state_sup_d", "ny_state_sup_n"), 0.05),
    ("F4 ID composition table", "f4",
     r"\| registration roll \| ([\d,]+) \| ([\d.]+)% \| ([\d.]+)% \| \*{0,2}([\d.]+)%"
     r"\*{0,2} \| \| 2024 general electorate \| ([\d,]+) \| ([\d.]+)% \| ([\d.]+)% \| "
     r"\*{0,2}([\d.]+)%\*{0,2} \| \| 2024 primary electorate \| ([\d,]+) \| ([\d.]+)% \| "
     r"([\d.]+)% \| \*{0,2}([\d.]+)%\*{0,2} \|",
     ("id_pop_roll_n", "id_pop_roll_rep", "id_pop_roll_dem", "id_pop_roll_una",
      "id_pop_ge_n", "id_pop_ge_rep", "id_pop_ge_dem", "id_pop_ge_una",
      "id_pop_pr_n", "id_pop_pr_rep", "id_pop_pr_dem", "id_pop_pr_una"), 0.05),
    ("F4 ID unaffiliated prose", "f4",
     r"Unaffiliated registrants are ([\d.]+)% of Idaho's roll and ([\d.]+)% of its 2024 "
     r"general electorate, but \*{0,2}([\d.]+)% of its 2024 primary electorate",
     ("id_pop_roll_una", "id_pop_ge_una", "id_pop_pr_una"), 0.05),

    # --- Appendix E: the geography / band / turnout restatements
    ("Appendix E geography table", "appe_geo",
     r"\| WA federal \| King \(Seattle\), ([\d,]+) donors \| ([\d.]+)% \| Snohomish "
     r"([\d.]+)% \(([\d.]+)×\), Pierce ([\d.]+)% \(([\d.]+)×\); top 3 = \*{0,2}([\d.]+)%"
     r"\*{0,2} \| "
     r"\| WA state \| King, ([\d,]+) donors \| ([\d.]+)% \| Pierce ([\d.]+)% \(([\d.]+)×\), "
     r"Snohomish ([\d.]+)% \(([\d.]+)×\); top 3 = \*{0,2}([\d.]+)%\*{0,2} \| "
     r"\| NY federal \| New York \(Manhattan\), ([\d,]+) donors \| ([\d.]+)% \| Westchester "
     r"([\d.]+)% \(([\d.]+)×\), Kings ([\d.]+)% \(([\d.]+)×\); top 3 = \*{0,2}([\d.]+)%"
     r"\*{0,2} \| "
     r"\| NY state \| New York, ([\d,]+) donors \| ([\d.]+)% \| Nassau ([\d.]+)% "
     r"\(([\d.]+)×\), Suffolk ([\d.]+)% \(([\d.]+)×\); top 3 = \*{0,2}([\d.]+)%\*{0,2} \| "
     r"\| ID federal \| Ada \(Boise\), ([\d,]+) donors \| ([\d.]+)% \| Bonneville ([\d.]+)% "
     r"\(([\d.]+)×\), Blaine ([\d.]+)% \(\*{0,2}([\d.]+)×\*{0,2}\); top 3 = \*{0,2}([\d.]+)%"
     r"\*{0,2} \| "
     r"\| ID state \| Ada, ([\d,]+) donors \| ([\d.]+)% \| Kootenai ([\d.]+)% \(([\d.]+)×\), "
     r"Canyon ([\d.]+)% \(([\d.]+)×\); top 3 = \*{0,2}([\d.]+)%\*{0,2} \|",
     ("wa_fed_cty0_n", "wa_fed_cty0_pct", "wa_fed_cty1_pct", "wa_fed_cty1_mult",
      "wa_fed_cty2_pct", "wa_fed_cty2_mult", "wa_fed_cty_top3",
      "wa_state_cty0_n", "wa_state_cty0_pct", "wa_state_cty1_pct", "wa_state_cty1_mult",
      "wa_state_cty2_pct", "wa_state_cty2_mult", "wa_state_cty_top3",
      "ny_fed_cty0_n", "ny_fed_cty0_pct", "ny_fed_cty1_pct", "ny_fed_cty1_mult",
      "ny_fed_cty2_pct", "ny_fed_cty2_mult", "ny_fed_cty_top3",
      "ny_state_cty0_n", "ny_state_cty0_pct", "ny_state_cty1_pct", "ny_state_cty1_mult",
      "ny_state_cty2_pct", "ny_state_cty2_mult", "ny_state_cty_top3",
      "id_fed_cty0_n", "id_fed_cty0_pct", "id_fed_cty1_pct", "id_fed_cty1_mult",
      "id_fed_blaine_pct", "id_fed_blaine_mult", "id_fed_cty_top3",
      "id_state_cty0_n", "id_state_cty0_pct", "id_state_cty1_pct", "id_state_cty1_mult",
      "id_state_cty2_pct", "id_state_cty2_mult", "id_state_cty_top3"), 0.05),
    ("Appendix E geography prose, ID Ada + Blaine", "appe_geo",
     r"loosens\*{0,2} from ([\d.]+)% of state dollars to ([\d.]+)% of federal.*?Bonneville "
     r"\(Idaho Falls\) at ([\d.]+)% and resort-county Blaine at ([\d.]+)% from ([\d,]+) "
     r"donors, whose\s+\*{0,2}([\d.]+)×\*{0,2} multiplier",
     ("id_state_cty0_pct", "id_fed_cty0_pct", "id_fed_cty1_pct", "id_fed_blaine_pct",
      "id_fed_blaine_n", "id_fed_blaine_mult"), 0.05),
    ("Appendix E NY competitiveness bands", "appe_bands",
     r"\| Tossup \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| "
     r"\| Solid \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \|",
     ("ny_fed_band_tossup_d", "ny_state_band_tossup_d", "ny_reg_band_tossup_d",
      "ny_fed_band_solid_d", "ny_state_band_solid_d", "ny_reg_band_solid_d"), 0.05),
    ("Appendix E NY Solid-district counts", "appe_bands",
     r"two-thirds of federal matched donors \(([\d,]+) of ([\d,]+)\) — 62% of state ones "
     r"\(([\d,]+) of ([\d,]+)\)",
     ("ny_fed_band_solid_n", "ny_fed_n", "ny_state_band_solid_n", "ny_state_n"), 0),
    ("Appendix E ID district-safety cut", "appe_bands",
     r"([\d,]+) Solid-R legislative districts hold ([\d,]+) matched donors whose pool is "
     r"\*{0,2}([\d.]+)% Republican to ([\d.]+)% Democratic\*{0,2}, while the ([\d,]+) "
     r"Likely/Lean-R districts carry a far more balanced ([\d.]+)% R / ([\d.]+)% D across "
     r"([\d,]+) donors",
     ("id_solid_lds", "id_solid_n", "id_solid_rep", "id_solid_dem",
      "id_adj_lds", "id_adj_rep", "id_adj_dem", "id_adj_n"), 0.5),
    ("Appendix E turnout table", "appe_turnout",
     r"\| WA super-voter share, federal panel \| ([\d.]+)% \| ([\d.]+)% \| "
     r"\| WA mean turnout propensity, federal panel \| ([\d.]+) \| ([\d.]+) \| "
     r"\| WA super-voter share, state panel \| ([\d.]+)% \| ([\d.]+)% \| "
     r"\| WA mean turnout propensity, state panel \| ([\d.]+) \| ([\d.]+) \| "
     r"\| NY generals voted, of last 4, federal panel \| ([\d.]+) \| ([\d.]+) \| "
     r"\| NY super-voter share \(≥3 of 4\), federal panel \| ([\d.]+)% \| ([\d.]+)% \| "
     r"\| NY generals voted, of last 4, state panel \| ([\d.]+) \| ([\d.]+) \| "
     r"\| NY super-voter share \(≥3 of 4\), state panel \| ([\d.]+)% \| ([\d.]+)% \|",
     ("wa_fed_super_d", "wa_fed_super_n", "wa_fed_prop_d", "wa_fed_prop_n",
      "wa_state_super_d", "wa_state_super_n", "wa_state_prop_d", "wa_state_prop_n",
      "ny_fed_gen_d", "ny_fed_gen_n", "ny_fed_sup_d", "ny_fed_sup_n",
      "ny_state_gen_d", "ny_state_gen_n", "ny_state_sup_d", "ny_state_sup_n"), 0.05),
    ("Appendix E turnout prose, NY panel-size gap", "appe_turnout",
     r"draws on ([\d,]+) more people", "ny_panel_gap_k", 500),

    # --- Appendix C: the period-alignment bullet and the overlap table
    ("Appendix C aligned federal panel", "appc_aligned",
     r"the federal panel falls from ([\d,]+) to ([\d,]+) donors and \$([\d,.]+)M to "
     r"\$([\d,.]+)M", ("id_fed_n", "id_fedal_n", "id_fed_m", "id_fedal_m"), 0.05),
    ("Appendix C overlap table", "appc_ovl",
     r"\| Washington \| ([\d,]+) \| ([\d,]+) \| ([\d,]+) \| ([\d.]+) \| ([\d.]+)% / "
     r"([\d.]+)% / \*{0,2}([\d.]+)%\*{0,2} \| "
     r"\| New York \| ([\d,]+) \| ([\d,]+) \| ([\d,]+) \| ([\d.]+) \| ([\d.]+)% / "
     r"([\d.]+)% / \*{0,2}([\d.]+)%\*{0,2} \| "
     r"\| Idaho \| ([\d,]+) \| ([\d,]+) \| ([\d,]+) \| ([\d.]+) \| ([\d.]+)% / "
     r"([\d.]+)% / \*{0,2}([\d.]+)%\*{0,2} \|",
     ("wa_fed_n", "wa_state_n", "wa_both_n", "wa_jaccard",
      "wa_ovl_stateonly", "wa_ovl_fedonly", "wa_ovl_both",
      "ny_fed_n", "ny_state_n", "ny_both_n", "ny_jaccard",
      "ny_ovl_stateonly", "ny_ovl_fedonly", "ny_ovl_both",
      "id_fed_n", "id_state_n", "id_both_n", "id_jaccard",
      "id_ovl_stateonly", "id_ovl_fedonly", "id_ovl_both"), 0.05),
]

# ---------------------------------------------------------------- coverage audit
# The reviewer's required control (2026-07-28): it is not enough to fix the contradictions
# that happen to be noticed. Every numeric token in a designated RESULT section must either
# be captured by a probe (and therefore asserted against the databases) or be explicitly
# exempted here with a reason. Anything else is an unmapped number and fails the run.
#
# Without this, the honest claim is only "the figures I wrote probes for agree" — which is
# exactly the overclaim that let the crossover tables, the limitations section and Appendix
# A keep three retired resolution rates while the paper said 309 figures were verified.
#
# Sections audited for coverage. A section can be probed but not audited (audit is the
# stronger requirement); every audited section must appear in SECTION_BOUNDS.
AUDITED_SECTIONS = (
    "methods",
    "sensitivity",
    "matchrate",
    "methods_tail",
    "f2_tail",
    "f1_ny", "f1_wa", "f1_id", "f1_gap", "f2", "f3", "f3_xover_intro", "f3_id_skew", "f4",
    "appc_aligned", "appc_ovl", "appe_geo", "appe_bands", "appe_turnout",
    "xover_ny", "xover_id", "limits_xover", "limits_itemization",
    "appe_bootstrap",
    "appd_belowfloor",
    "appg_bunch", "appg_layers", "appg_clip",
    "appf_matchability",
    "appf_precision",
    "appf_weighted",
    "appf_modes",
    "appa",
    "appb",
    "appd_all",
    "appc_head",
    "appe_head", "appe_mid",
    "appg_head", "appg_tail",
)

# Sliced but NOT YET audited, with the count of unmapped numeric tokens each still carries.
# This is not "by design" — it is unfinished, and it is recorded here with exact numbers so the
# remaining work is specified rather than rediscovered. Adding one of these to AUDITED_SECTIONS
# is the next step; the slices already exist, so the audit will report precisely what is left.
PENDING_AUDIT = {
    "appf_head": "192 tokens — the matchability-by-age tables, tier composition, and the "
                 "household false-merge sensitivity tables on both specifications. Largest "
                 "remaining block; mostly wide numeric tables needing per-row probes",
    "appc_mid": "the stretch of Appendix C between the disclosure-trigger table and the panel "
                "overlap block, not yet sliced — the two slices around it are audited",
    "appf_mid": "28 tokens — per-tier false-merge risk on the donor side, and the rating design",
    "appf_tail": "15 tokens — the error-mode tail from 'what follows for the paper' onward, "
                 "including the ceiling analysis and the survivorship note",
}

# Numeric tokens that are legitimately not result figures. Each needs a reason: this list
# is the audit's escape hatch and the only place a number can hide.
COVERAGE_EXEMPT = [
    (r"^(19|20)\d{2}$", "calendar year"),
    (r"^(19|20)\d{2}[–-](19|20)\d{2}$", "year range"),
    (r"^\d{1,2}$", "small integer: list ordinal, band count, table column, 'of 4'"),
    (r"^100$", "a percentage total, or 'of 100 buckets'"),
    (r"^\d{2,3}xx$", "ZIP3 prefix, not a measurement"),
    (r"^(200|100|99|50|250|1,000|5,000|3,500|9,000|3,000|7,000|500)$",
     "statutory threshold or contribution cap — verified in Appendix D, not derived here"),
    (r"^(480|150|120|75|25|53|18|8|5|2)$",
     "validation sample size or rating count — from the frozen verdict CSVs, Appendix F"),
    (r"^\d{2,3}(?=A?\(?\d*\)?$)", "statute or code section number (e.g. Idaho Code 34-437A)"),
    # `29B.25.090(5)` yields the token `25.090`. Three digits after the point is a section
    # number, not a result — this paper prints every derived percentage to one decimal.
    (r"^\d{2}\.\d{3}$", "RCW/WAC section-number fragment, e.g. 29B.25.090"),
    (r"^(437|720|740|710|710A|114|116|6610A|30116|30118|29B|1422|5892)$",
     "statute or bill number cited in Appendix B/D, verified there rather than derived"),
    (r"^\d+\.\d+%?$", None),   # placeholder, replaced below — decimals must be COVERED
]
# Decimals are the figures that drift, so they are never exempt by shape. Drop the
# placeholder; a decimal must be captured by a probe or the run fails.
COVERAGE_EXEMPT = [(p, why) for p, why in COVERAGE_EXEMPT if why is not None]

# Specific tokens that recur in prose as descriptive rather than derived quantities.
COVERAGE_EXEMPT_LITERAL = {
    # NOTE: 27 exemptions that had stopped firing were pruned on 2026-07-30. The
    # supplement calls a stale exemption prunable once the prose that needed it has
    # settled, and this round rewrote a great deal of prose. If one of these tokens
    # returns to an audited section the audit fails loudly and it gets a fresh reason,
    # which is the right failure mode — a dead exemption would absorb it silently.

    "5.51M": "WA roll size, same",
    "1.03M": "ID roll size, same",
    "96.9": "Wilson lower bound from the frozen verdict CSV (Appendix F), not a DB figure",
    "3.1%": "the error budget, derived as sens_budget_pct and probed once in `sensitivity`; "
            "the section restates the same constant four more times",
    "50.4%": "ZIP3-tier precision from the frozen verdict CSV (Appendix F), same class as 96.9",
    "269,204": "all-tier WA state row count, probed once in `appf_weighted`; the denominator "
               "note restates it a second time in the same sentence",
    "32.6%": "the RETIRED name-heuristic estimate of Idaho's organisation dollar share, quoted "
             "only to say the measured 53.9% is well above it. Historical, superseded, and "
             "not recomputable — the heuristic it came from was deleted",
    "1.85%": "WA PDC name-order misparse rate, produced by diag_donor_class_revisions.py's own "
             "parser. NOT independently re-derived: a from-scratch heuristic here (first token "
             "absent from the roll's surname vocabulary, last token present) measures 4.7% / "
             "4.1%, which is a DIFFERENT instrument rather than a check of this one — see the "
             "note in the supplement. Flagged for re-derivation from the originating script",
    "2.08%": "the dollar half of the same pair, same reason",
    "0.5": "a stated upper BOUND, not a value: the largest shift from counting every "
           "indeterminate as an error. Derived as val_u_shift and measured at 0.42 points, so "
           "the bound holds. Exempt because the probe machinery compares equality",
    # --- Appendix C's layer totals and the harmonised age gaps ------------------------
    "$646.2M": "the WA federal contribution layer's total, a raw SUM over "
               "individual_contributions quoted to show the table holds two money systems. "
               "Probed at panel level as mr_wa_fed_amt_m in `matchrate`",
    "$394.6M": "the WA state layer's total, same",
    "42.4": "the federal leg of the retired all-tier trio quoted in Appendix C. Probed on "
            "the all-tier panels in Appendix F; quoted here only so the paper can label it "
            "retired and warn against comparing it with a primary-spec figure",
    "43.8": "the state leg of the same retired trio, same reason",
    "47.7": "pooled top-1% on the RETIRED all-tier specification, quoted only to label it as "
            "retired. Appendix F carries the all-tier panels; not re-derived here because the "
            "paper's point is that it must not be compared with a primary-spec figure",
    "3.0": "arithmetic on the three pooled-trio figures probed immediately above",
    # --- Appendix E's candidate-money cut and Appendix G's displacement tail ----------
    "0.69": "Gini of candidate-committee inflow, owned and asserted by verify_cross_state_money.py "
            "against fec_inflow.duckdb — a different database this verifier does not open",
    "0.80": "low end of the total-outflow Gini range, same source and same verifier",
    "0.85": "high end of the same range, same source",
    "41.9%": "Idaho state dollars in uncapped vehicles, produced by diag_contribution_limits.py's "
             "recipient-type classification — the same instrument Appendix G's G3/G4 tables are "
             "exempted for, and reimplementing it here would copy it rather than check it",
    "$1,245,000": "largest single Sunshine contribution, a raw maximum from the same "
                  "classification pass; public by name in Idaho Sunshine",
    # --- Appendix A's two household-exclusion bounds -------------------------------
    "4.7": "top-1% movement under the surname+ZIP5 over-exclusion, from Appendix F's household "
           "sensitivity table. Not re-derived here: the exclusion drops 75-83% of each panel and "
           "reimplementing it would copy the instrument rather than check it, the same reason "
           "Appendix G's classification tables are exempt",
    "6.1": "the surname+address variant of the same bound, same table and same reason",
    # --- Appendix B: a regulation number, not a measurement -------------------------
    "104.15": "the FEC regulation number (11 C.F.R. § 104.15), verified against the C.F.R. "
              "in Appendix B's own text rather than derived",
    "30111": "the enabling statute number (52 U.S.C. § 30111(a)(4)), same",
    # --- Appendix D: figures from the cited literature ------------------------------
    "2.5%": "upper end of the ADGN-vs-SSN discordance range reported by Ansolabehere & Hersh "
            "(2017); a figure from the cited paper, not from these data",
    "97.5%": "the same paper's later comparison figure, cited as published",
    "97.8%": "its counterpart in the same comparison, cited as published",
    # --- Appendix D: statutory contribution limits and section numbers --------------
    "$1,500": "a limit proposed by 2026 S.B. 1422 and not enacted; legislative text, not data",
    "$6,000": "a Washington statutory cycle limit (RCW 42.17A.405 as recodified), cited to the "
              "statute",
    "$10,000": "the same schedule's Senate cycle limit, cited to the statute",
    "$18,000": "the same schedule's statewide cycle limit, cited to the statute",
    "42.17": "fragment of the RCW section number 42.17A.405",
    "253.094": "Texas Election Code section number",
    "253.151": "Texas Election Code section number (Judicial Campaign Fairness Act range)",
    "253.176": "the upper bound of the same section range",
    "268,741": "positive-total count for the all-tier WA state panel, probed once in "
               "`appf_weighted`; the denominator note restates it a second time",
    # The data-minimisation control removed the ability to re-derive the figures that justify
    # it, which is worth saying rather than papering over. Day and month are generalised to
    # 1 July of the birth year in the analytical copy, so a completed-age figure can no longer
    # be computed from it. These four were measured ONCE, before the 2026-07-30 migration, and
    # are recorded in the supplement with the query that produced them. Recomputing them would
    # mean re-parsing the raw FOIL production out of the restricted enclave.
    "14.9%": "share of NY registrants whose birthday falls after early November — measured "
             "pre-migration; no longer derivable from the minimised analytical copy by design",
    "25.00%": "NY roll 65+ on completed age, measured pre-migration; see above",
    "49.51%": "NY federal donors 65+ on completed age, measured pre-migration; see above",
    "0.09": "the donor-roll gap shift between the two age measures, arithmetic on the four "
            "figures above",
    "100.0%": "full-name-tier precision from the frozen verdict CSV, probed in appf_matchability",
    "71.7%": "weakest initial-tier precision, same frozen CSV and same section",
    "0.14": "low end of the Jaccard range; the three exact per-state coefficients are "
            "probed cell by cell in f1_gap",
    "0.16": "high end of the same range, verified in the same place",
    # The inverse-propensity / P(matchable) block. These are properties of the ROLL and the
    # match key, produced by diag_ny_match_bias.py and its WA counterpart on the all-tier
    # panels — not derivable from the six published panels, which is why they are exempt
    # here rather than probed. The paper says both things: that they were computed on the
    # superseded panels, and why they carry over. If that reasoning is ever challenged the
    # fix is to re-run those scripts, not to widen this list.
    "94.5": "P(matchable) lower bound, NY — diag_ny_match_bias.py, not re-derived here",
    "95.4": "P(matchable) upper bound, NY — same",
    "96.3": "P(matchable) lower bound, WA — diag_wa_individual_findings.py, same",
    "97.6": "P(matchable) upper bound, WA — same",
    "1.4": "spread of the WA P(matchable) range, in points",
    "47.9": "IPW-reweighted NY 65+ share on the all-tier panel, labelled as such",
    "2.7": "the senior over-representation multiplier quoted as a round figure",
    "0.0": "the IPW shift, which is zero to one decimal — that IS the result",
    "0.05": "the paper's own printed precision, and the estimator tolerance Appendix C "
            "quantifies — a statement about rounding, not a measurement",
    # Figures owned by another paper and another verifier. Each names where it is checked.
    "39.3": "statewide (all-itemized) WA top-1% — verify_cross_state_money.py, Appendix E",
    "47.5": "statewide NY top-1% — same",
    "41.7": "statewide TX top-1% — same",
    "36.0": "statewide ID top-1% — same",
    "6,797": "Appendix G cap-bunching count — diag_contribution_limits.py",
    # Superseded figures the paper quotes in order to label them superseded.
    "0.4": "max movement on the all-records baseline, stated as the reason it is not used",
    "0.9": "two figures share this token: the all-records REP skew (attributed to "
           "earlier drafts) and the spread of the NY P(matchable) range, in points",
    # NY closed-primary participation and ID primary ballot mix: separate diagnostics.
    "25.3": "NY blank-enrollee share of registrants (also the F1 reference 65+ cell)",
    "0.1": "NY blank-enrollee primary participation, lower bound of a stated range",
    "0.6": "upper bound of the same range — diag_ny_primary_participation.py",
    "16.9": "NY 2021 odd-year DEM primary turnout — same script",
    "5.0": "NY 2021 odd-year REP primary turnout — same script",
    "229,173": "ID 2024 primary Republican ballots pulled — the ID roll's ballot-type field",
    "33,535": "ID Democratic ballots pulled, same",
    "9,567": "ID unaffiliated ballots pulled, same",
    "952": "ID Libertarian ballots pulled, same",
    "657": "ID Constitution ballots pulled, same",
    "83.7": "share of ID primary ballots that were Republican, same",
    "12.2": "three different figures share this token, which is why it carries one merged reason: "
            "Idaho's Democratic primary-ballot share, the NY federal REP D-only cell, and the "
            "ID leg of the common-donor-total age comparison in Appendix C "
            "(diag_panel_harmonized.py, which this verifier does not rebuild)",
    "3.5": "unaffiliated share, same",
    # Finding 2's ordering test: bootstrapped DIFFERENCES between states, owned by
    # diag_donor_concentration_bootstrap.py's ordering_test().
    "9.50": "NY-WA top-1% difference, federal panel — bootstrap ordering test",
    "5.11": "NY-WA difference, state panel — same",
    "4.03": "WA-ID difference, federal panel — same",
    "3.51": "WA-ID difference, state panel — same",
    "13.54": "NY-ID difference, federal panel — same",
    "8.62": "NY-ID difference, state panel — same",
    "17.7": "width of Idaho's state top-1% interval, in points — same",
    "4.8": "width of Washington's federal top-1% interval, in points — same",
    "37.16": "ID federal top-1% on NTILE — probed in the Finding 2 table",
    "37.12": "the same on the resampling routine's rank cutoff — Appendix C owns the delta",
    "382": "WA PDC rows netting to zero or below after refunds — reported by the "
           "integrity block of this script every run",
    "30.7": "lowest lower bound across the six top-1% intervals — same",
    "1,029,938": "ID roll size — verify_who_decides_id.py owns it",
    "44.8": "NY out-of-state share of matched dollars — diag_ny_donor_extras.py",
    "54.1": "NY Senate-Democrat out-of-state share — same",
    "23.9": "ID unaffiliated roll share, probed in the composition table above",
    "5.9": "ID unaffiliated primary share, probed in the same table",
    # 87.8 / 86.7 were exempted while the paper quoted them to record that they were wrong.
    # The erratum moved to the corrections ledger on 2026-07-29, so they no longer appear in
    # any audited section — and an exemption for a known-WRONG value is the worst kind to
    # leave standing: if either figure were ever reintroduced, the audit would absorb it
    # silently instead of failing. Deliberately not replaced.
    # ---- Appendix G, added to the audit 2026-07-29 after review #3 found this appendix's
    # largest defect while it sat outside the audit. Its DERIVED cells split in two:
    #
    #  * G2's bunching counts need no heuristic and ARE probed above.
    #  * G3's layer table and G4's clipping table rest on
    #    diag_contribution_limits.py's ORG_RE person/organization NAME HEURISTIC and its
    #    `contributor_state` residence filter. Reimplementing those here would copy the
    #    appendix's own instrument into the verifier instead of checking it, so they are
    #    exempted with that script named — the convention already used for the bootstrap
    #    intervals and the frozen validation ledgers. A first attempt to re-derive them
    #    disagreed with every cell and the basis error was mine.
    #
    # These are the tokens those two tables contribute. Every one is a cell of, or a prose
    # restatement of, a row of the G3 layer table or the G4 clipping table.
    **{tok: "Appendix G3 layer table cell — diag_contribution_limits.py owns the "
            "person/organization name heuristic and residence filter these depend on"
       for tok in ("216,700", "$53.3M", "54,019", "56.4%", "81.6%", "0.872",
                   "181,539", "$23.9M", "47,356", "39.7%", "71.2%", "0.800",
                   "770,765", "$76.2M", "54,155", "36.1%", "69.2%", "0.775",
                   "770,128", "54,088",
                   "2,816,398", "$348.3M", "728,255", "44.4%", "75.5%", "0.823",
                   "5,578,905", "$645.6M", "361,184", "39.3%", "72.3%")},
    **{tok: "Appendix G4 clipping table cell — same script, same heuristic"
       for tok in ("32.2%", "30.1%", "68.7%", "$571M", "31.2%", "28.4%", "67.7%", "$554M",
                   "30.9%", "67.4%", "$548M", "26.4%", "22.0%", "62.9%", "$454M",
                   "$646M", "2.1", "4.3")},
    # G2's prose restatements around the probed bunching table.
    "$1,001": "a bunching-table row label, probed as a count in the same table",
    "$1,100": "same",
    "$5,001": "same",
    "15×": "the bunching spike expressed as a round ratio, 6,797/448 — both probed",
    # Appendix G cross-references to figures this verifier probes elsewhere, or to a
    # withdrawn one quoted in order to withdraw it.
    "0.799": "ID state matched Gini — probed in Finding 2's concentration table",
    "40.0": "ID state matched top-1% — probed in Finding 2's concentration table",
    # In "22.0-26.4%" the en-dash splits the range, so the first bound arrives without its
    # percent sign and does not match the "22.0%" key above.
    "22.0": "G4 aggregate-clip top-1% at $1,000 — the same cell as '22.0%' above",
    "34.7": "ID aligned federal top-1% — probed in Appendix C's aligned-panel section",
    # The cycle-varying federal amounts are statutory values from the FEC's archived charts,
    # verified in Appendix D rather than derived from any database.
    **{tok: "federal per-election statutory amount by cycle — Appendix D, FEC charts"
       for tok in ("$2,700", "$2,800", "$2,900", "$3,300", "$3,500", "$1,000", "$5,000",
                   "$3,000", "$9,000", "$1,200", "$2,400", "$150,000")},
}

def _assert_no_duplicate_exemptions():
    """Fail at import if COVERAGE_EXEMPT_LITERAL repeats a key.

    A dict literal silently keeps the LAST value for a repeated key, so a duplicate throws
    away a written exemption reason — and this dict is the coverage audit's only escape hatch.
    The collapse happens at parse time and is invisible in the built dict, so the keys are read
    back off this file's own source. `**{...}` comprehension blocks make the mistake easy: a
    token in a comprehension tuple can collide with an explicit key hundreds of lines away.
    """
    import ast
    node = None
    for n in ast.walk(ast.parse(Path(__file__).read_text(encoding="utf-8"))):
        if isinstance(n, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "COVERAGE_EXEMPT_LITERAL"
                for t in n.targets):
            node = n.value
    if node is None:                      # renamed or restructured; nothing to check
        return
    seen, dupes = {}, {}
    for k, v in zip(node.keys, node.values):
        found = []
        if k is None:                     # **{...} unpacking
            if isinstance(v, ast.Dict):
                found = [(e.value, e.lineno) for e in v.keys
                         if isinstance(e, ast.Constant)]
            elif isinstance(v, ast.DictComp):
                for gen in v.generators:
                    if isinstance(gen.iter, ast.Tuple):
                        found += [(e.value, e.lineno) for e in gen.iter.elts
                                  if isinstance(e, ast.Constant)]
        elif isinstance(k, ast.Constant):
            found = [(k.value, k.lineno)]
        for tok, line in found:
            if tok in seen:
                dupes.setdefault(tok, [seen[tok]]).append(line)
            else:
                seen[tok] = line
    if dupes:
        detail = "; ".join(f"{t!r} at lines {ls}" for t, ls in sorted(dupes.items()))
        raise AssertionError(
            f"COVERAGE_EXEMPT_LITERAL has {len(dupes)} duplicated key(s) — the later value "
            f"silently discards the earlier reason. Merge them: {detail}")

_assert_no_duplicate_exemptions()

# Require digits AFTER a decimal point, so "PDC 2016-2026. Scripts:" yields the token
# `2026` (an exempt year) rather than `2026.` (which matches no exemption pattern). Also
# forbid a trailing comma, or "the federal $200, so" yields `$200,` and "ZIP5, required"
# yields `5,` — neither of which any exemption pattern can sensibly match.
_NUM_RX = re.compile(r"\$?\d(?:[\d,]*\d)?(?:\.\d+)?(?:%|M|×|xx)?")

# Bracketed ranges in this paper are always confidence intervals — [38.6-43.4], Wilson
# [96.9-100], [+6.09, +20.05]. Their bounds come from
# diag_donor_concentration_bootstrap.py and score_match_validation.py, which own 1,000-
# resample sequences this verifier deliberately does not duplicate (it would double the
# runtime and clone an RNG-order fragility). Tokens inside such a bracket are therefore
# exempt by rule, with that ownership as the reason. The character class admits only
# digits, separators and sign glyphs, so a markdown link's `[text](url)` can never match.
_INTERVAL_RX = re.compile(r"\[[\s\d.,+−–—-]+\]")

def _audit_coverage(sections, covered):
    """Fail on any numeric token in an audited section that no probe captured.

    Also reports exemptions that no longer fire. A written exemption is the audit's only escape
    hatch, so a stale one is dead weight that would silently absorb a figure if that token ever
    reappeared in an audited section. Reported as a WARNING, not a failure: an exemption can
    legitimately go quiet when prose moves to the unaudited supplement, which is what the
    2026-07-29 manuscript compression did to a dozen of them.
    """
    print("\n" + "-" * 78)
    print("COVERAGE AUDIT — every number in a result section must be probed or exempt")
    print("-" * 78)
    fails = []
    used_exempt = set()
    for name in AUDITED_SECTIONS:
        hay = sections.get(name)
        if hay is None:
            fails.append(f"coverage: audited section '{name}' not found in the paper")
            print(f"  FAIL {name:16} SECTION NOT FOUND")
            continue
        spans = covered.get(name, [])
        intervals = [m.span() for m in _INTERVAL_RX.finditer(hay)]
        unmapped = []
        for m in _NUM_RX.finditer(hay):
            tok = m.group(0)
            if any(a <= m.start() and m.end() <= b for a, b in intervals):
                continue  # confidence-interval bound; see _INTERVAL_RX
            # OVERLAP, not containment: a capture group holds the numeric core (`1.6`)
            # while the token includes its suffix (`1.6%`), so the token's end runs past
            # the group's. Containment reported every probed table cell as unmapped.
            if any(m.start() < b and a < m.end() for a, b in spans):
                continue
            bare = tok.lstrip("$").rstrip("%M×")
            if bare in COVERAGE_EXEMPT_LITERAL or tok in COVERAGE_EXEMPT_LITERAL:
                used_exempt.add(bare if bare in COVERAGE_EXEMPT_LITERAL else tok)
                continue
            if any(re.match(p, bare) for p, _ in COVERAGE_EXEMPT):
                continue
            ctx = re.sub(r"\s+", " ", hay[max(0, m.start() - 45):m.end() + 25])
            unmapped.append((tok, ctx))
        if unmapped:
            print(f"  FAIL {name:16} {len(unmapped)} unmapped numeric token(s)")
            for tok, ctx in unmapped[:40]:
                print(f"         {tok:>12}   …{ctx}…")
            if len(unmapped) > 40:
                print(f"         … and {len(unmapped) - 40} more")
            fails.append(f"coverage [{name}]: {len(unmapped)} unmapped numeric token(s) — "
                         f"first is {unmapped[0][0]!r}. Probe it or exempt it with a reason.")
        else:
            print(f"  ok   {name:16} fully mapped")
    stale = sorted(set(COVERAGE_EXEMPT_LITERAL) - used_exempt)
    if stale:
        print(f"\n  note {len(stale)} literal exemption(s) no longer fire in any audited "
              f"section — prunable once the prose that needed them has settled:")
        print("       " + ", ".join(stale))
    return fails

# The four crossover tables are 28 cells each, and both blocks of a state share a row shape
# — so a hand-written pattern for the federal block silently matches the state block too and
# asserts one panel's values against the other's keys. (It did, on the first run.) Generated
# instead, each scoped to its own `*federal panel*` / `*state panel*` marker row.
_XN = r"\*{0,2}([\d.]+)%\*{0,2}"
_XCELLS = ("matched", "resolved", "rate", "donly", "ronly", "mixed", "dold")

def _crossover_probes():
    out = []
    for sect, block, prefix, order in (
        ("xover_ny", "federal", "ny_fed", ("DEM", "REP", "NOPARTY", "OTHER")),
        ("xover_ny", "state", "ny_state", ("DEM", "REP", "NOPARTY", "OTHER")),
        ("xover_id", "federal", "id_fed", ("REP", "DEM", "UNAFF")),
        ("xover_id", "state", "id_state", ("REP", "DEM", "UNAFF")),
    ):
        # Idaho's minor-party (OTHER) rows were WITHHELD from the crossover and bound
        # tables 2026-07-29 as a disclosure control: they resolved to 102 and 44 donors,
        # and a percentage over a base that small lets a reader recover a count of a few
        # individuals. New York's OTHER rows (bases 7,122 and 5,410) are retained, so the
        # orders differ by state on purpose — do not "tidy" them back into symmetry.

        rows, keys = [], []
        for p in order:
            rows.append(rf"\| {p} \| ([\d,]+) \| ([\d,]+) \| {_XN} \| {_XN} \| {_XN} \| "
                        rf"{_XN} \| \| {_XN} \|")
            keys += [f"{prefix}_x_{p}_{c}" for c in _XCELLS]
        # `[^A-Za-z]*` spans the marker row's empty cells and cannot cross into the other
        # block, whose marker contains letters.
        rx = rf"\*{block} panel\*[^A-Za-z]*" + " ".join(rows)
        out.append((f"crossover table, {prefix}", sect, rx, tuple(keys), 0.05))
    return out

PROBES += _crossover_probes()

# Finding 3's age-standardization table, Finding 3's worst-case bound table, and Finding 4's
# turnout-standardization table. All three are generated rather than hand-written for the same
# reason the crossover probes are: the row shapes repeat across states and panels, so a
# hand-written pattern for one block silently matches another and asserts one panel's values
# against another's keys.
_SN = r"([+−-]?[\d.]+)"

def _age_std_probes():
    """Finding 3's raw / standardized / age-share table, one probe per panel block."""
    out = []
    for st, tag, marker, order in (
        ("ny", "fed", r"\*New York, federal\*",
         ("DEM", "REP", r"NOPARTY \(blank\)", "OTHER")),
        ("ny", "state", r"\*New York, state\*", ("DEM", "REP", "NOPARTY", "OTHER")),
        ("id", "fed", r"\*Idaho, federal\*", ("REP", "DEM", "UNAFF", "OTHER")),
        ("id", "state", r"\*Idaho, state\*", ("REP", "DEM", "UNAFF", "OTHER")),
    ):
        rows, keys = [], []
        for lbl in order:
            party = lbl.split(" ")[0]
            rows.append(rf"\| {lbl} \| {_SN} \| \*{{0,2}}{_SN}\*{{0,2}} \| "
                        rf"\*{{0,2}}{_SN}%\*{{0,2}} \|")
            keys += [f"{st}_{tag}_std_{party}_{c}"
                     for c in ("rawskew", "stdskew", "expl")]
        rx = rf"{marker} \| \| \| \| " + " ".join(rows)
        out.append((f"F3 age-standardized party, {st} {tag}", "f3_id_skew", rx,
                    tuple(keys), 0.05))
    return out

def _prevalence_probes():
    """Finding 3's donors-per-1,000-registrants table (one row per panel)."""
    rows = (("NY federal", "ny", "fed", ("DEM", "REP", "NOPARTY", "OTHER")),
            ("NY state", "ny", "state", ("DEM", "REP", "NOPARTY", "OTHER")),
            ("ID federal", "id", "fed", ("DEM", "REP", "UNAFF", "OTHER")),
            ("ID state", "id", "state", ("DEM", "REP", "UNAFF", "OTHER")))
    pats, keys = [], []
    for lbl, st, tag, order in rows:
        pats.append(rf"\| {lbl} \| \*{{0,2}}([\d.]+)\*{{0,2}} \| ([\d.]+) \| "
                    rf"([\d.]+) \| ([\d.]+) \|")
        keys += [f"{st}_{tag}_std_{pp}_prev" for pp in order]
    lead = r"which asks directly how often each party's registrants appear as donors: "
    return [("F3 donation prevalence per 1,000 registrants", "f3_id_skew",
             lead + r"\| panel \| DEM \| REP \|[^|]*\| other \| \|[-:| ]+\| " + " ".join(pats),
             tuple(keys), 0.05)]

def _bound_probes():
    """Finding 3's worst-case unresolved-pool bound, one probe per panel block."""
    out = []
    for st, tag, marker, order in (
        ("ny", "fed", r"\*NY federal\*", ("DEM", "REP", "NOPARTY", "OTHER")),
        ("ny", "state", r"\*NY state\*", ("DEM", "REP", "NOPARTY", "OTHER")),
        ("id", "fed", r"\*ID federal\*", ("REP", "DEM", "UNAFF")),
        ("id", "state", r"\*ID state\*", ("REP", "DEM", "UNAFF")),
    ):
        rows, keys = [], []
        for party in order:
            rows.append(rf"\| {party} \| ([\d.]+)% \| \*{{0,2}}([\d.]+)%\*{{0,2}} \| "
                        rf"\*{{0,2}}([\d.]+)%\*{{0,2}} \| ([\d.]+)% \| "
                        rf"\*{{0,2}}(?:yes|no)\*{{0,2}} \|")
            keys += [f"{st}_{tag}_bnd_{party}_{c}"
                     for c in ("unres", "donly", "ronly", "adverse")]
        rx = rf"{marker} \| \| \| \| \| \| " + " ".join(rows)
        out.append((f"F3 unresolved-pool bound, {st} {tag}", "xover_id", rx,
                    tuple(keys), 0.05))
    return out

def _matchability_probes():
    """Finding 3's P(matchable)-by-party table and the age x county incidence table."""
    out = []
    pm_rows, pm_keys = [], []
    for lbl, st, order in (("New York", "ny", ("DEM", "REP", "NOPARTY", "OTHER")),
                           ("Idaho", "id", ("DEM", "REP", "UNAFF", "OTHER"))):
        pm_rows.append(rf"\| {lbl} \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| "
                       rf"([\d.]+)% \| \*{{0,2}}([\d.]+) pt\*{{0,2}} \|")
        pm_keys += [f"{st}_pmatch_{p}" for p in order] + [f"{st}_pmatch_spread"]
    out.append(("F P(matchable) by party", "appf_matchability", " ".join(pm_rows),
                tuple(pm_keys), 0.05))

    inc_rows, inc_keys = [], []
    for lbl, st, tag, order in (("NY federal", "ny", "fed", ("DEM", "REP", "NOPARTY", "OTHER")),
                                ("NY state", "ny", "state", ("DEM", "REP", "NOPARTY", "OTHER")),
                                ("ID federal", "id", "fed", ("DEM", "REP", "UNAFF", "OTHER")),
                                ("ID state", "id", "state", ("DEM", "REP", "UNAFF", "OTHER"))):
        inc_rows.append(rf"\| {lbl} \| \*{{0,2}}([\d.]+)\*{{0,2}} \| ([\d.]+) \| "
                        rf"([\d.]+) \| ([\d.]+) \|")
        inc_keys += [f"{st}_{tag}_inc_{p}_agecty" for p in order]
    lead = r"age × county distribution: "
    out.append(("F3 age x county standardized incidence", "f3_id_skew",
                lead + r"\| panel \| DEM \| REP \| unaffiliated \| other \| \|[-:| ]+\| "
                + " ".join(inc_rows), tuple(inc_keys), 0.05))
    return out

PROBES += _age_std_probes() + _prevalence_probes() + _bound_probes()
PROBES += _matchability_probes()

PROBES += [
    ("F3 matchability summary sentence", "f3_id_skew",
     r"P\(matchable\) spans just \*{0,2}([\d.]+) point\*{0,2} across New York's parties and "
     r"\*{0,2}([\d.]+)\*{0,2} across Idaho's, which is a multiplicative difference of about "
     r"([\d.]+)× against incidence ratios running ([\d.]+)× to ([\d.]+)×",
     ("ny_pmatch_spread", "id_pmatch_spread", "_ny_pmatch_spread_mult",
      "_ny_state_inc_ratio", "_id_state_inc_ratio"), 0.05),
    ("F3 unaffiliated-to-Democratic incidence range", "f3_id_skew",
     r"the unaffiliated at\s+([\d.]+)–([\d.]+)% of the Democratic rate",
     ("_unaff_dem_ratio_lo", "_unaff_dem_ratio_hi"), 0.05),
    ("F matchability completeness floor", "appf_matchability",
     r"Name-and-ZIP completeness is ≥([\d.]+)% in every party of both",
     ("_pmatch_complete_min",), 0.05),
    ("F3 age x county retained weight", "f3_id_skew",
     r"except Idaho's small OTHER bloc \(([\d.]+)%\)",
     ("id_fed_inc_OTHER_kept",), 0.05),
    ("F matchability band and county spreads", "appf_matchability",
     r"band is ([\d.]+) points in New York and ([\d.]+) in Idaho; across the eight largest "
     r"counties of each\s+state the party gap never exceeds ([\d.]+) points",
     ("ny_pmatch_band_spread", "id_pmatch_band_spread", "ny_pmatch_county_spread"), 0.05),
    ("F matchability spread vs incidence ratios", "appf_matchability",
     r"A ([\d.]+)-point spread is a multiplicative difference of about ([\d.]+)×, against\s+"
     r"Democratic-to-Republican incidence ratios running ([\d.]+)× \(NY state\) to "
     r"([\d.]+)× \(ID state\)",
     ("ny_pmatch_spread", "_ny_pmatch_spread_mult", "_ny_state_inc_ratio",
      "_id_state_inc_ratio"), 0.05),
    ("F re-based incidence examples", "appf_matchability",
     r"NY federal DEM\s+([\d.]+) → ([\d.]+), REP ([\d.]+) → ([\d.]+); ID federal DEM "
     r"([\d.]+) → ([\d.]+), REP ([\d.]+) → ([\d.]+)\)",
     ("ny_fed_inc_DEM_all", "ny_fed_inc_DEM_matchable",
      "ny_fed_inc_REP_all", "ny_fed_inc_REP_matchable",
      "id_fed_inc_DEM_all", "id_fed_inc_DEM_matchable",
      "id_fed_inc_REP_all", "id_fed_inc_REP_matchable"), 0.05),
    ("F3 ID adjusted incidence ratios", "f3_id_skew",
     r"\*{0,2}([\d.]+)× \(federal\) and ([\d.]+)×\s+\(state\)\*{0,2} the Republican rate "
     r"unadjusted, and at \*{0,2}([\d.]+)× and ([\d.]+)×\*{0,2}",
     ("_id_fed_prev_ratio", "_id_state_prev_ratio",
      "_id_fed_inc_ratio_agecty", "_id_state_inc_ratio_agecty"), 0.05),
    # --- Appendix G's derived tables
    ("Appendix G2 bunching table", "appg_bunch",
     r"\| \$750 \| ([\d,]+) \| \| \$900 \| ([\d,]+) \| \| \$999 \| ([\d,]+) \| "
     r"\| \*{0,2}\$1,000\*{0,2}[^|]*\| \*{0,2}([\d,]+)\*{0,2} \| \| \$1,001 \| ([\d,]+) \| "
     r"\| \$1,100 \| ([\d,]+) \| \| \*{0,2}\$5,000\*{0,2}[^|]*\| \*{0,2}([\d,]+)\*{0,2} \| "
     r"\| \$5,001 \| ([\d,]+) \|",
     ("g_bunch_750", "g_bunch_900", "g_bunch_999", "g_bunch_1000", "g_bunch_1001",
      "g_bunch_1100", "g_bunch_5000", "g_bunch_5001"), 0),
    ("F4 eligibility restriction retention", "f4",
     r"keeps ([\d.]+)% of New York's active\s+roll \(([\d,]+) of ([\d,]+),.*?and "
     r"([\d.]+)% of Washington's\s+\(([\d,]+) of ([\d,]+),",
     ("ny_elig_pct", "ny_elig_n", "ny_elig_tot",
      "wa_elig_pct", "wa_elig_n", "wa_elig_tot"), 0.05),
    ("F4 eligible-for-all turnout table", "f4",
     r"\| NY federal \| \+([\d.]+) \| \*{0,2}\+([\d.]+)\*{0,2} \| ([\d.]+)% \| "
     r"([\d.]+)% \| "
     r"\| NY state \| \+([\d.]+) \| \*{0,2}\+([\d.]+)\*{0,2} \| ([\d.]+)% \| "
     r"([\d.]+)% \| "
     r"\| WA federal \| \+([\d.]+) \| \*{0,2}\+([\d.]+)\*{0,2} \| ([\d.]+)% \| "
     r"([\d.]+)% \| "
     r"\| WA state \| \+([\d.]+) \| \*{0,2}\+([\d.]+)\*{0,2} \| ([\d.]+)% \| "
     r"([\d.]+)% \|",
     ("ny_fed_egap_raw", "ny_fed_egap_age", "ny_fed_ratio_d", "ny_fed_ratio_n",
      "ny_state_egap_raw", "ny_state_egap_age", "ny_state_ratio_d", "ny_state_ratio_n",
      "wa_fed_egap_raw", "wa_fed_egap_age", "wa_fed_ratio_d", "wa_fed_ratio_n",
      "wa_state_egap_raw", "wa_state_egap_age", "wa_state_ratio_d", "wa_state_ratio_n"), 0.05),
    ("F4 eligible-vs-band adjusted range", "f4",
     r"tenure-band\s+figures — \+([\d.]+) to \+([\d.]+) against \+([\d.]+) to "
     r"\+(\d+(?:\.\d+)?)",
     ("_egap_age_lo", "_egap_age_hi", "_tgap_ten_lo", "_tgap_ten_hi"), 0.05),
]

PROBES += [
    ("F4 turnout standardization table", "f4",
     r"generals\) \| \+([\d.]+) \| \*{0,2}\+([\d.]+)\*{0,2} \| "
     r"\*{0,2}\+([\d.]+)\*{0,2} \| "
     r"\| NY, state panel \| \+([\d.]+) \| \*{0,2}\+([\d.]+)\*{0,2} \| "
     r"\*{0,2}\+([\d.]+)\*{0,2} \| "
     r"\| WA, federal panel — voted both 2022 and 2024 generals \| \+([\d.]+) \| "
     r"\*{0,2}\+([\d.]+)\*{0,2} \| \*{0,2}\+([\d.]+)\*{0,2} \| "
     r"\| WA, state panel \| \+([\d.]+) \| \*{0,2}\+([\d.]+)\*{0,2} \| "
     r"\*{0,2}\+([\d.]+)\*{0,2} \|",
     ("ny_fed_tgap_raw", "ny_fed_tgap_age", "ny_fed_tgap_ten",
      "ny_state_tgap_raw", "ny_state_tgap_age", "ny_state_tgap_ten",
      "wa_g2_fed_tgap_raw", "wa_g2_fed_tgap_age", "wa_g2_fed_tgap_ten",
      "wa_g2_state_tgap_raw", "wa_g2_state_tgap_age", "wa_g2_state_tgap_ten"), 0.05),
    ("F4 WA endogenous-tenure disclosure", "f4",
     r"it reads \+([\d.]+) / \+([\d.]+), and those numbers should not be",
     ("wa_sv_fed_tgap_ten", "wa_sv_state_tgap_ten"), 0.05),
    ("F4 standardization retained weight", "f4",
     r"five tenure bands.*?; ([\d]+)% of the standard population is retained",
     ("ny_fed_tgap_ten_kept",), 0.05),
    ("F3 standardization universe", "f3_id_skew",
     r"of 18 or over \(NY ([\d,]+); ID ([\d,]+)",
     ("ny_stdpop_n", "id_stdpop_n"), 0),
    ("F4 NY federal band gap examples", "f4",
     r"NY federal \+([\d.]+) at 35–44 against \+([\d.]+) at 65–74",
     ("_ny_fed_bandgap_3544", "_ny_fed_bandgap_6574"), 0.05),
    # --- Finding 3's standardization prose, restating table cells
    ("F3 std prose, unstable ratio note", "f3_id_skew",
     r"NY federal REP reads −([\d.]+)% on a raw skew of −(\d+(?:\.\d+)?)",
     ("_ny_fed_std_REP_expl_abs", "_ny_fed_std_REP_rawskew_abs"), 0.05),
    ("F3 std prose, coarse-band exception", "f3_id_skew",
     r"except Idaho federal REP \(\+([\d.]+) → −([\d.]+)\)",
     ("id_fed_std_REP_rawskew", "_idc_fed_std_REP_stdskew_abs"), 0.05),
    ("F3 std prose, DEM unchanged", "f3_id_skew",
     r"NY federal \+([\d.]+) → \+([\d.]+); ID federal \+([\d.]+) → \+([\d.]+)\)",
     ("ny_fed_std_DEM_rawskew", "ny_fed_std_DEM_stdskew",
      "id_fed_std_DEM_rawskew", "id_fed_std_DEM_stdskew"), 0.05),
    ("F3 std prose, unaffiliated range", "f3_id_skew",
     r"survives at −([\d.]+) to −([\d.]+) everywhere",
     ("_id_fed_std_UNAFF_stdskew_abs", "_ny_fed_std_NOPARTY_stdskew_abs"), 0.05),
    ("F3 std prose, ID REP destroyed", "f3_id_skew",
     r"\*{0,2}\+([\d.]+) raw becomes −([\d.]+) standardized\*{0,2}",
     ("id_fed_std_REP_rawskew", "_id_fed_std_REP_stdskew_abs"), 0.05),
    # The forward pointer on the Idaho skew table, so the two statements of the same pair
    # cannot drift apart (the table itself is unadjusted; this note says what happens to it).
    ("F3 ID skew table, age-standardization forward pointer", "f3_id_skew",
     r"where the\s+federal \+([\d.]+) becomes −([\d.]+) and is withdrawn",
     ("id_fed_std_REP_rawskew", "_id_fed_std_REP_stdskew_abs"), 0.05),
    # --- Finding 4's prose restatements
    ("F4 prose, WA vs NY measure incomparability", "f4",
     r"the WA ([\d.]+)% / ([\d.]+)% figures above are \*{0,2}not\*{0,2} "
     r"measure-comparable with New York's ([\d.]+)% / ([\d.]+)%",
     ("wa_fed_super_d", "wa_state_super_d", "ny_fed_sup_d", "ny_state_sup_d"), 0.05),
    ("F4 prose, ID registration plurality", "f4",
     r"Republicans hold a ([\d.]+)% registration plurality",
     ("id_pop_roll_rep",), 0.05),
    # --- Finding 3's bound prose, restating the bound table
    ("F3 bound prose, NY unaffiliated federal", "xover_id",
     r"D-only donors are ([\d.]+)% of all matched donors in the row, more than the "
     r"([\d.]+)% that R-only would reach if \*all\* ([\d.]+)% unresolved",
     ("ny_fed_bnd_NOPARTY_donly", "ny_fed_bnd_NOPARTY_adverse",
      "ny_fed_bnd_NOPARTY_unres"), 0.05),
    ("F3 bound prose, ID unaffiliated federal", "xover_id",
     r"margin is far wider \(([\d.]+)% against ([\d.]+)%\)",
     ("id_fed_bnd_UNAFF_donly", "id_fed_bnd_UNAFF_adverse"), 0.05),
    ("F3 bound prose, DEM near-monolithic on matched", "xover_id",
     r"on the same basis \(([\d.]+)% and ([\d.]+)% D-only of all matched\)",
     ("ny_fed_bnd_DEM_donly", "id_fed_bnd_DEM_donly"), 0.05),
    ("F3 bound prose, state resolution rates", "xover_id",
     r"At ([\d.]+)% \(NY\) and ([\d.]+)% \(ID\) aggregate resolution",
     ("ny_state_x_agg", "id_state_x_agg"), 0.05),
    ("F3 bound prose, NY state unaffiliated row", "xover_id",
     r"clearest case: ([\d.]+)% D-only against ([\d.]+)% R-only, with ([\d.]+)% unresolved",
     ("ny_state_bnd_NOPARTY_donly", "ny_state_bnd_NOPARTY_ronly",
      "ny_state_bnd_NOPARTY_unres"), 0.05),
    ("F3 suppression note, retained NY OTHER bases", "xover_id",
     r"New York's OTHER rows, over bases of ([\d,]+) and ([\d,]+), are retained",
     ("ny_fed_x_OTHER_resolved", "ny_state_x_OTHER_resolved"), 0),
    ("F3 bound prose, ID state REP adversarial direction", "xover_id",
     r"pushes all ([\d.]+)% unresolved to the \*Democratic\*",
     ("id_state_bnd_REP_unres",), 0.05),
    ("F2 positive-total denominator", "f2",
     r"there are \*{0,2}([\d,]+)\*{0,2} \(([\d.]+)%\), so the concentration figures "
     r"there run on \*{0,2}([\d,]+)\*{0,2} donors rather than ([\d,]+)",
     ("wa_state_nonpos", "wa_state_nonpos_pct", "wa_state_npos", "wa_state_n"), 0.05),
]

def _normalise(path):
    """Drop blockquote markers, collapse all whitespace.

    Anchors then span line wraps and table rows, so re-flowing a paragraph does not silently
    disarm a probe.
    """
    return re.sub(r"\s+", " ", re.sub(r"(?m)^\s*>\s?", "", path.read_text(encoding="utf-8")))

def prose_probes():
    """Scrape the manuscript and its supplement, asserting every figure against the DBs."""
    docs = {"paper": _normalise(PAPER), "supp": _normalise(SUPPLEMENT)}
    # Section-less probes search both documents. The separator carries no digits and no letters
    # a probe could match, so a pattern cannot span the join.
    norm = docs["paper"] + "  ###  " + docs["supp"]

    sections = {}
    for name, bounds in SECTION_BOUNDS.items():
        start, end = bounds[0], bounds[1]
        hay = docs[bounds[2] if len(bounds) > 2 else "paper"]
        i = hay.find(start)
        if i < 0:
            sections[name] = None
            continue
        j = hay.find(end, i + len(start))
        sections[name] = hay[i:j if j > 0 else len(hay)]

    d = derive_prose()
    # Negative skews print with a minus sign the capture group does not take, so every
    # skew key gets a magnitude twin. Cheaper and less error-prone than deciding per cell
    # which sign the table happens to show.
    for k in list(d):
        if "_skew_" in k:
            d[f"_neg_{k}"] = -d[k]

    print("\n" + "=" * 78)
    print("PROSE SCRAPE — donor-class paper, every figure asserted against the databases")
    print("=" * 78)
    fails, checked = [], 0
    # section name -> list of (start, end) char spans this run actually asserted. Feeds
    # the coverage audit, which is the control that turns "the figures I probed agree"
    # into "no number in a result section is unaccounted for".
    covered: dict[str, list[tuple[int, int]]] = {}
    for label, section, rx, keys, tol in PROBES:
        keys = (keys,) if isinstance(keys, str) else keys
        hay = norm if section is None else sections.get(section)
        if hay is None:
            print(f"  FAIL {label:52} SECTION '{section}' NOT FOUND")
            fails.append(f"{label}: section '{section}' not found — a heading was renamed")
            continue
        matches = list(re.finditer(rx, hay))
        if not matches:
            print(f"  FAIL {label:52} ANCHOR NOT FOUND")
            fails.append(f"{label}: anchor not found — the sentence was reworded or the "
                         f"figure removed. Re-point the probe or restore the text.")
            continue
        if section is not None:
            for m in matches:
                for gi in range(1, (m.re.groups or 0) + 1):
                    if m.span(gi) != (-1, -1):
                        covered.setdefault(section, []).append(m.span(gi))
        if not keys:  # presence-only probe (a qualitative claim, no figure to check)
            print(f"  ok   {label:52} present")
            continue
        for m in matches:
            hit = m.groups()
            if len(hit) != len(keys):
                print(f"  FAIL {label:52} captured {len(hit)}, expected {len(keys)}")
                fails.append(f"{label}: capture/key arity mismatch")
                continue
            for got, key in zip(hit, keys):
                want = d.get(key)
                if want is None:
                    print(f"  FAIL {label:52} no derived value for {key}")
                    fails.append(f"{label}: derivation '{key}' unavailable")
                    continue
                # The paper sets signed figures with U+2212 MINUS SIGN, which float()
                # rejects; normalise it (and the two dash glyphs that can stand in for it)
                # rather than forcing ASCII hyphens into the typeset tables.
                val = float(got.replace(",", "").replace("−", "-")
                            .replace("–", "-").replace("—", "-"))
                # Epsilon is a float-representation guard only. It is deliberately far
                # too small to absorb a last-digit rounding error: NY's 65+ active-roll
                # share is 25.250122%, which rounds to 25.3 and failed here against a
                # published 25.2 until the CELL was corrected. Widening tol to swallow
                # that class of miss is how a verifier stops being one.
                ok = abs(val - float(want)) <= tol + 1e-9
                checked += 1
                if not ok:
                    print(f"  FAIL {label:52} {key:26} paper {val:>12,.4g}   "
                          f"data {float(want):,.4g}")
                    fails.append(f"{label} [{key}]: paper says {val:,.4g}, "
                                 f"data says {float(want):,.4g}")
        if not any(f.startswith(label) for f in fails):
            print(f"  ok   {label:52} {len(matches)} occurrence(s), all agree")
    print(f"\n  {checked} figures scraped and compared")

    # Estimator robustness, reported every run so it cannot quietly start to matter.
    print("\n  top-1% estimator: published NTILE(100) vs an exact donor-weight cutoff")
    for tag in ("wa_fed", "wa_state", "ny_fed", "ny_state", "id_fed", "id_state"):
        if f"{tag}_top1_exact" in d:
            print(f"    {tag:10} NTILE {d[tag + '_top1']:6.3f}%   "
                  f"exact {d[tag + '_top1_exact']:6.3f}%   "
                  f"delta {d[tag + '_top1_exact'] - d[tag + '_top1']:+.3f} pts   "
                  f"{d[tag + '_top1_ties']:>3} donor(s) tied at the boundary")
    for w in d.get("_estimator_warnings", []):
        print(f"    FAIL {w}")
        fails.append(f"estimator: {w}")

    fails += _audit_coverage(sections, covered)
    return fails

_FAILURES += prose_probes()

# ============================== INTEGRITY SUMMARY ==============================
print("\n" + "=" * 78)
if _FAILURES:
    print(f"INTEGRITY: {len(_FAILURES)} FAILURE(S)")
    print("=" * 78)
    for f in _FAILURES:
        print(f"  - {f}")
    raise SystemExit(1)
print("INTEGRITY: all assertions pass")
print("=" * 78)
