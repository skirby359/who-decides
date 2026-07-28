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
import duckdb

DATA = Path(__file__).resolve().parent.parent / "data"

FED = "voter_donor_affiliation_fec"
STATE = "voter_donor_affiliation_state"
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
_FAILURES += integrity(idc, "ID", {"federal": FED, "state": STATE}, None)
print("\nRECONCILIATION  ID (primary-spec panels only)")
_FAILURES += reconcile_primary(idc, "ID", FED, "FEC")
_FAILURES += reconcile_primary(idc, "ID", STATE, "SUNSHINE")
idc.close()

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
