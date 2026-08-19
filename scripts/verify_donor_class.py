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
from decimal import Decimal
from pathlib import Path
import hashlib
import json
import re
import sys
import time

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
# The SUBMISSION-PACKAGE documents. The verifier used to read the paper and its supplement and
# nothing else, which left the memo, cover letter and metadata restating figures with no guard
# at all — and every one of the ten stale figures found on 2026-08-01 was in one of them.
# `check_cross_doc_consistency.py` catches stale COUNTS there by absence; percentages it catches
# only about half the time, because a stale percentage usually coincides with some other figure
# in the paper. These probes close that half: exact assertion against the derivation, on the
# same machinery the paper gets.
MEMO = ROOT / "docs" / "donor-class-submission-memo.md"

# Probe-label prefix -> the operational document it checks. These three never travel to
# the public repository (sync_public_repo.NEVER), so where they are absent their probes
# cannot run and are skipped by name. Keyed on the label prefix because that convention
# already exists in the probe table and is what a reader sees in the output.
_OPERATIONAL = {"Memo:": "donor-class-submission-memo.md",
                "Cover:": "donor-class-cover-letter.md",
                "Metadata:": "donor-class-submission-metadata.md"}
COVER = ROOT / "docs" / "donor-class-cover-letter.md"
METADATA = ROOT / "docs" / "donor-class-submission-metadata.md"

# ---------------------------------------------------------------------------------------
# Connection reuse. The derivation layer used to open a fresh read-only connection per
# derivation — 20 of them across three statewide DBs, 12 re-ATTACHing the same voter roll —
# and then run 29 full-roll GROUP BY passes across those connections. Each new connection
# starts with an empty buffer pool, so every one of those passes re-read the same 5.1M / 12.5M
# / 1.0M row store from disk.
#
# These are all READ-ONLY connections to the same files, so sharing them is semantically
# inert: no derivation can observe another's writes because none of them write. What they DO
# share now is the buffer pool, which is the entire point.
#
# The one hazard is temp-table collision — derivations that used to be alone on a connection
# now share a namespace. Every temp table here is created with CREATE OR REPLACE and the names
# are distinct across derivations (checked);
# `test_donor_verifier_invariants.TestPooledConnectionsStaySafe.test_temp_table_names_are_unique` keeps
# them that way, because a silent collision would be exactly this project's recurring defect
# class: a derivation reading values it did not compute.
_CONNS: dict[str, "duckdb.DuckDBPyConnection"] = {}
_ATTACHED: dict[str, set[str]] = {}
# Per-derivation wall time, populated only under --profile. Kept because "the derivation
# layer is slow" was carried as folklore for weeks with no per-function number behind it,
# and the one refactor anybody proposed was aimed at the wrong thing.
_TIMINGS: dict[str, float] = {}


def _timed(fn):
    """Record a derivation's wall time under --profile. Transparent otherwise."""
    def wrapper(*a, **kw):
        if not _PROFILE:
            return fn(*a, **kw)
        t0 = time.monotonic()
        try:
            return fn(*a, **kw)
        finally:
            dt = time.monotonic() - t0
            _TIMINGS[fn.__name__] = _TIMINGS.get(fn.__name__, 0.0) + dt
            # Printed as it happens, not only in the summary. A cold pass runs for tens of
            # minutes and the summary is useless while you are waiting to find out which
            # derivation is the one costing them.
            if dt >= 1.0:
                print(f"    [profile] {dt:7.1f}s  {fn.__name__}", flush=True)
    wrapper.__name__ = fn.__name__
    wrapper.__doc__ = fn.__doc__
    return wrapper


def _conn(db_stem: str, vrdb_stem: str | None = None, alias: str = "vrdb"):
    """Read-only connection to ``data/<db_stem>.duckdb``, cached for this process.

    Pass ``vrdb_stem`` to have that voter file ATTACHed under ``alias`` — idempotent, so
    call sites need not know whether an earlier derivation already attached it. Call sites
    must NOT close the result; `_close_conns()` does that once at the end of the run.
    """
    con = _CONNS.get(db_stem)
    if con is None:
        con = duckdb.connect(str(DATA / f"{db_stem}.duckdb"), read_only=True)
        _CONNS[db_stem] = con
        _ATTACHED[db_stem] = set()
    if vrdb_stem is not None and alias not in _ATTACHED[db_stem]:
        con.execute(f"ATTACH '{DATA / (vrdb_stem + '.duckdb')}' AS {alias} (READ_ONLY)")
        _ATTACHED[db_stem].add(alias)
    return con


def _drop_temps(con, *names: str) -> None:
    """Drop a derivation's temp tables on a POOLED connection.

    Not optional hygiene. Before pooling, each derivation had its own connection and its
    multi-million-row temp tables died with it. Sharing a connection makes them accumulate
    for the whole run instead — the WA connection alone would hold four roll-sized keyed
    tables at once — and the resident set is large enough to push DuckDB into spilling,
    which costs far more than the connection reuse saves. Measured: leaving them resident
    took a cold pass past 40 minutes of CPU against ~26 before pooling.

    Only ever pass tables the calling derivation created. Blanket-dropping every temp table
    is wrong here: `derive_prose` builds `_vroll` and friends once and several derivations
    read them afterwards.
    """
    for n in names:
        try:
            con.execute(f"DROP TABLE IF EXISTS {n}")
        except Exception:  # noqa: BLE001
            pass


def _close_conns() -> None:
    for con in _CONNS.values():
        try:
            con.close()
        except Exception:  # noqa: BLE001
            pass
    _CONNS.clear()
    _ATTACHED.clear()


FED = "voter_donor_affiliation_fec"
STATE = "voter_donor_affiliation_state"
# Washington's roll is PINNED. `voter_scores` is a live table — `refresh-gotv` rebuilds it on
# every ballot load and each crosswalk improvement pulls newly-scoped voters in, so reading it
# directly means the figure a reviewer recomputes drifts away from the figure the paper prints.
# `scripts/pin_wa_donor_roll.py` freezes the ld scope; re-pinning is deliberate and loud.
_WA_ROLL = "donor_paper_wa_roll"
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
    _drop_temps(con, "_rc_vk")  # pooled connection: see _drop_temps
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
wa = _conn("wa_statewide", "wa_vrdb")
require(wa, "WA", [FED, STATE])

roll = dict(wa.execute(f"SELECT age_cohort,COUNT(*) FROM {_WA_ROLL} WHERE age_cohort IS NOT NULL GROUP BY 1").fetchall())
rt = sum(roll.values())
for _label, _panel in (("FEDERAL", FED), ("STATE (PDC)", STATE)):
    print(f"\nF1 generation multiplier = donor share / roll share, {_label} panel")
    don = dict(wa.execute(f"""SELECT s.age_cohort,COUNT(*) FROM {_WA_ROLL} s JOIN {_panel} a USING(state_voter_id)
                             WHERE s.age_cohort IS NOT NULL GROUP BY 1""").fetchall())
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
        WITH roll AS (SELECT state_voter_id,is_super_voter,turnout_propensity FROM {_WA_ROLL}),
        f AS (SELECT r.*, CASE WHEN a.state_voter_id IS NOT NULL THEN 1 ELSE 0 END d FROM roll r LEFT JOIN {_panel} a USING(state_voter_id))
        SELECT d,COUNT(*),AVG(CASE WHEN is_super_voter THEN 1.0 ELSE 0 END),AVG(turnout_propensity) FROM f GROUP BY d ORDER BY d""").fetchall():
        print(f"    {'matched donor' if donor else 'non-donor':14} n={n2:>10,}  super {sr*100:5.1f}%  avg prop {ap:.3f}")
_FAILURES += integrity(wa, "WA", {"federal": FED, "state": STATE}, None)
print("\nRECONCILIATION  WA (primary-spec panels only)")
_FAILURES += reconcile_primary(wa, "WA", FED, "FEC")
_FAILURES += reconcile_primary(wa, "WA", STATE, "PDC")

# ============================== NEW YORK ==============================
print("\n" + "=" * 78 + "\nNEW YORK  (ny_statewide + ny_vrdb)\n" + "=" * 78)
ny = _conn("ny_statewide", "ny_vrdb")
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

# ============================== IDAHO ==============================
print("\n" + "=" * 78 + "\nIDAHO  (id_statewide + id_vrdb)\n" + "=" * 78)
idc = _conn("id_statewide", "id_vrdb")
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

# ====================== PROSE SCRAPE — derive, then assert ======================
# Age basis. NY's bands and every 65+ cut outside Idaho are measured at the 2024 general,
# matching match_ny_voters_to_donors.py and diag_donor_class_revisions.py. Idaho's roll
# carries a current-age integer instead of a DOB, so ID uses v.age — the paper states the
# difference, and the two are NOT interchangeable (mixing them is defect R? in the Idaho
# paper's own history).
_AGE_2024 = "date_diff('year', v.birthdate, DATE '2024-11-05')"
_GENS = ["Silent", "Boomer", "Gen X", "Millennial", "Gen Z"]
# Washington's roll restriction. Every WA age and turnout cut carries this as of review round
# 15: the article's baseline is the active roll in all three states, with no exception. It is a
# named constant rather than an inline predicate because it has to appear in five WA queries and
# the whole point is that none of them may quietly omit it. `v` is always vrdb.voters.
_WA_ACTIVE = "v.status_code = 'A'"
# The panel-specific match-error ceiling. The blinded sample allocates 20 full-name records to
# each of the six panels, so a panel's own Wilson 95% upper bound on error given 0/20 is this,
# not the 3.1% the POOLED 120 supports. Kept as a constant so the two budgets can never be
# confused for one another again — spending a pooled bound panel-by-panel is exactly the defect
# review round 15 found.
PANEL_BUDGET = 0.1611

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

@_timed
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

@_timed
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
    _drop_temps(con, "_vroll", "_vcmp")  # pooled connection: see _drop_temps

@_timed
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
    _drop_temps(con, "_vm_roll", "_vm_don")  # pooled connection: see _drop_temps

@_timed
def _d_wa_ldscope_crosswalk(con, panels, out):
    """Crosswalk from the paper's active-roll Washington figures to the ld-scope ones.

    Review round 14 disclosed that WA's age and turnout baselines were the `voter_scores`
    ld-scope roll while every other baseline in the paper was `status_code='A'`. Round 15
    resolved it the other way: the article now uses the active roll throughout, which removes
    the inconsistency between the abstract and the methods section.

    The ld-scope figures are still derived, for two reasons. The companion Washington papers
    use that convention, so the article carries a crosswalk rather than leaving a reader to
    wonder why two papers in one series disagree. And the direction is worth keeping on the
    record: inactive registrants vote less, so the ld-scope convention DEPRESSES the non-donor
    rate and WIDENS every WA donor gap relative to the active-roll figures the paper now
    publishes.
    """
    n_roll, n_inact = con.execute(f"""
        WITH roll AS (SELECT state_voter_id FROM {_WA_ROLL})
        SELECT COUNT(*), COUNT(*) FILTER (WHERE v.status_code <> 'A')
        FROM roll r JOIN vrdb.voters v USING (state_voter_id)""").fetchone()
    out["wa_ldroll_n"] = int(n_roll)
    out["wa_ldroll_m"] = n_roll / 1e6
    out["wa_ldroll_inactive"] = int(n_inact)
    out["wa_ldroll_inactive_pct"] = n_inact / n_roll * 100
    out["wa_active_n"] = int(con.execute(
        "SELECT COUNT(*) FROM vrdb.voters WHERE status_code='A'").fetchone()[0])
    out["wa_active_m"] = out["wa_active_n"] / 1e6

    # Headline super-voter share, published (ld-scope) against active-only.
    for tag, panel in panels.items():
        rates = {}
        for restrict, key in (("1=1", "ld"), ("v.status_code = 'A'", "act")):
            for dn, sv in con.execute(f"""
                WITH roll AS (SELECT state_voter_id, is_super_voter FROM {_WA_ROLL})
                SELECT CASE WHEN a.state_voter_id IS NOT NULL THEN 1 ELSE 0 END dn,
                       100.0*AVG(CASE WHEN r.is_super_voter THEN 1.0 ELSE 0 END)
                FROM roll r JOIN vrdb.voters v USING (state_voter_id)
                LEFT JOIN {panel} a ON a.state_voter_id = r.state_voter_id
                WHERE {restrict} GROUP BY 1""").fetchall():
                rates[(key, int(dn))] = float(sv)
        out[f"wa_{tag}_super_n_ldscope"] = rates[("ld", 0)]
        out[f"wa_{tag}_super_gap_delta"] = ((rates[("ld", 1)] - rates[("ld", 0)])
                                            - (rates[("act", 1)] - rates[("act", 0)]))

    # Same comparison on the exact-eligibility restriction, which the paper also quotes.
    for tag, panel in panels.items():
        gaps = {}
        for restrict, key in (("1=1", "ld"), ("v.status_code = 'A'", "act")):
            rows = dict(con.execute(f"""
                WITH roll AS (SELECT state_voter_id FROM {_WA_ROLL}),
                gen AS (SELECT state_voter_id, COUNT(DISTINCT YEAR(election_date)) g
                        FROM vrdb.voting_history
                        WHERE MONTH(election_date)=11 AND YEAR(election_date) IN (2022,2024)
                        GROUP BY 1)
                SELECT CASE WHEN a.state_voter_id IS NOT NULL THEN 1 ELSE 0 END dn,
                       100.0*AVG(CASE WHEN COALESCE(gen.g,0) >= 2 THEN 1.0 ELSE 0.0 END)
                FROM roll r JOIN vrdb.voters v USING (state_voter_id)
                LEFT JOIN gen ON gen.state_voter_id = r.state_voter_id
                LEFT JOIN {panel} a ON a.state_voter_id = r.state_voter_id
                WHERE {_AGE_2024} IS NOT NULL AND {_AGE_2024} >= 18
                  AND v.registration_date <= DATE '2022-11-08' AND {restrict}
                GROUP BY 1""").fetchall())
            gaps[key] = float(rows[1]) - float(rows[0])
        out[f"wa_{tag}_egap_raw_ldscope"] = gaps["ld"]
        out[f"wa_{tag}_egap_delta"] = gaps["ld"] - gaps["act"]


@_timed
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
    _drop_temps(con, "_el", "_elc")  # pooled connection: see _drop_temps

@_timed
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

@_timed
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

@_timed
def _d_rater2(out):
    """Inter-rater agreement, derived from the committed PII-free ledger.

    ADDED 2026-08-06 with the independent rating. Appendix F's new inter-rater block sits in
    `appf_tail`, a section exempt from the coverage audit — so without this the ten figures it
    states would be asserted by nothing, and the exemption's written reason (ceiling figures
    plus a directionless survivorship note) would have quietly become false. Deriving beats
    widening that reason: `reference/match_validation_rater2_verdicts.csv` is committed,
    carries no names, and is exactly what the paper points a reader at.

    Reads a CSV, not a database, so it costs nothing in the derivation layer and cannot be a
    reason for the release gate to be slow.
    """
    path = ROOT / "docs" / "reference" / "match_validation_rater2_verdicts.csv"
    if not path.exists():
        return                      # probes will fail on the missing key, which is correct
    import csv as _csv
    rows = list(_csv.DictReader(path.open(encoding="utf-8")))
    binary = {"Y": "same", "NC": "diff", "NP": "diff"}
    full = [r for r in rows if r["match_tier"] == "STRICT_ZIP5_FULL"]
    out["r2_full_n"] = len(full)
    out["r2_full_y_pass1"] = sum(1 for r in full if r["pass1_verdict"] == "Y")
    out["r2_full_y_rater2"] = sum(1 for r in full if r["rater2_verdict"] == "Y")
    # Four-category observed agreement and kappa over every record. Reported alongside the
    # binary pair because kappa is deflated where one category dominates: on a block that is
    # nearly all-Y a low kappa means "little to disagree about", not "the raters disagree".
    def _kappa(prs):
        m = len(prs)
        cats = sorted({c for pr in prs for c in pr})
        p_o = sum(1 for x, y in prs if x == y) / m
        fa = {c: sum(1 for x, _ in prs if x == c) / m for c in cats}
        fb = {c: sum(1 for _, y in prs if y == c) / m for c in cats}
        p_e = sum(fa[c] * fb[c] for c in cats)
        return p_o, (p_o - p_e) / (1 - p_e)

    obs4, k4 = _kappa([(r["pass1_verdict"], r["rater2_verdict"]) for r in rows])
    out["r2_obs4"] = 100.0 * obs4
    out["_r2_kappa4"] = k4
    # Collapsed to same/different: U leaves the denominator, the published convention.
    pairs = [(binary[a], binary[b]) for a, b in
             ((r["pass1_verdict"], r["rater2_verdict"]) for r in rows)
             if a in binary and b in binary]
    n = len(pairs)
    po = sum(1 for a, b in pairs if a == b) / n
    ma = {c: sum(1 for a, _ in pairs if a == c) / n for c in ("same", "diff")}
    mb = {c: sum(1 for _, b in pairs if b == c) / n for c in ("same", "diff")}
    pe = sum(ma[c] * mb[c] for c in ("same", "diff"))
    out["r2_binary_n"] = n
    out["r2_obs_binary"] = 100.0 * po
    out["r2_kappa_binary"] = (po - pe) / (1 - pe)
    out["r2_pabak_binary"] = 2 * po - 1
    # The direction of disagreement, which is the claim the prose actually makes.
    #
    # THE AXIS IS CERTAINTY, NOT SAMENESS, and getting that wrong is how the first draft of the
    # prose said "35 of 36" where the truth is 34. `Y` and `NC` are both CONFIDENT calls — one
    # confidently same, one confidently different — so a move between them is a substantive
    # flip at equal certainty, not a loss of it. `NP` is a hedge and `U` is no call. On a
    # same-to-different ordering (Y > NP > NC) an `NC -> NP` move reads as *gaining* confidence,
    # which is backwards: it is a confident verdict becoming a hedge.
    certainty = {"Y": 2, "NC": 2, "NP": 1, "U": 0}
    less = more = flip = 0
    for r in rows:
        a, b = r["pass1_verdict"], r["rater2_verdict"]
        if a == b:
            continue
        if certainty[b] < certainty[a]:
            less += 1
        elif certainty[b] > certainty[a]:
            more += 1
        else:
            flip += 1          # equal certainty, opposite substance: NC <-> Y
    out["r2_disagree"] = less + more + flip
    out["r2_toward_less_certain"] = less
    out["r2_toward_more_certain"] = more
    out["r2_flip_same_certainty"] = flip
    out["r2_u_pass1"] = sum(1 for r in rows if r["pass1_verdict"] == "U")
    out["r2_u_rater2"] = sum(1 for r in rows if r["rater2_verdict"] == "U")


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
        con = _conn(db)
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
            # Pooled: `_conn()` owns the lifetime, `_close_conns()` ends it.
            pass
    for i, t in enumerate(tiers):
        out[f"tier{i}_share_lo"] = min(seen[t])
        out[f"tier{i}_share_hi"] = max(seen[t])

@_timed
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

@_timed
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

@_timed
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

@_timed
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

@_timed
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


# Name parse and eligibility for the geographic-selection check. These MUST stay identical to
# `diag_match_rate.py`'s, because that script's denominator is what Appendix F §F8 publishes as
# the match rate, and the check below validates itself against that published figure. A drift
# here would make the reconstruction miss and the panel silently drop out of the check.
_MR_LAST = """CASE WHEN contributor_name LIKE '%,%'
        THEN UPPER(TRIM(SPLIT_PART(contributor_name, ',', 1)))
        ELSE UPPER(TRIM(SPLIT_PART(contributor_name, ' ', -1))) END"""
_MR_FIRST = """CASE WHEN contributor_name LIKE '%,%'
        THEN UPPER(TRIM(SPLIT_PART(TRIM(SPLIT_PART(contributor_name, ',', 2)), ' ', 1)))
        ELSE UPPER(TRIM(SPLIT_PART(contributor_name, ' ', 1))) END"""
_MR_ELIGIBLE = """
    contributor_name IS NOT NULL AND contributor_name <> ''
    AND contributor_zip IS NOT NULL AND contributor_zip <> ''
    AND UPPER(contributor_name) NOT IN
        ('SMALL CONTRIBUTIONS', 'UNITEMIZED', 'ANONYMOUS')
    AND COALESCE(contributor_type, 'UNKNOWN')
        NOT IN ('ORGANIZATION', 'COMMITTEE', 'BUSINESS', 'PAC')
"""


@_timed
def _d_geo_selection(con, prefix, source, state, counties, out, roll_where="status_code='A'"):
    """Finding 2's geographic-selection check: matched multiplier vs all eligible resident keys.

    Answers the sharpest question available against a geographic finding computed on matched
    donors — whether the geographically-structured non-match (Appendix F's largest bucket is
    keys matching at a DIFFERENT ZIP5) manufactures the county disproportions.

    Both sides are geolocated the same way, by the county of the ZIP5 on the FILING, so the
    comparison isolates selection rather than address source. That is legitimate here precisely
    because the primary specification requires ZIP5 equality: a matched donor's county of
    registration IS the county of their filing ZIP, but for ZIP5s crossing a county line.

    The key rule is reimplemented from the specification rather than read off the panel table,
    which is what makes this an independent check — and it is why `diag_donor_geography_selection.py`
    validates its reconstruction against the published match rate before reporting anything.
    Washington's state panel does not reconstruct (the PDC name-order defect) and is not called
    here; the paper says so and excludes it.
    """
    con.execute("DROP TABLE IF EXISTS _gsz")
    con.execute(f"""
        CREATE TEMP TABLE _gsz AS
        WITH z AS (SELECT SUBSTR(reg_zip,1,5) z5, county_name cty, COUNT(*) n
                   FROM vrdb.voters
                   WHERE {roll_where} AND reg_zip IS NOT NULL AND county_name IS NOT NULL
                   GROUP BY 1,2),
        r AS (SELECT z5, cty, ROW_NUMBER() OVER (PARTITION BY z5 ORDER BY n DESC, cty) rk
              FROM z WHERE LENGTH(z5)=5)
        SELECT z5, cty FROM r WHERE rk=1""")
    con.execute("DROP TABLE IF EXISTS _gsk")
    con.execute(f"""
        CREATE TEMP TABLE _gsk AS
        WITH ids AS (
            SELECT {_MR_LAST} AS last_nm, {_MR_FIRST} AS first_nm,
                   SUBSTR(contributor_zip,1,5) AS z5, SUM(contribution_amount) AS amt
            FROM individual_contributions
            WHERE SPLIT_PART(contribution_id, ':', 1) = '{source}' AND {_MR_ELIGIBLE}
              AND UPPER(TRIM(contributor_state)) = '{state}'
            GROUP BY 1,2,3),
        elig AS (SELECT * FROM ids
                 WHERE last_nm <> '' AND LENGTH(first_nm) > 1 AND LENGTH(z5)=5 AND amt > 0),
        roll AS (SELECT UPPER(TRIM(last_name)) last_nm, UPPER(TRIM(first_name)) first_nm,
                        SUBSTR(reg_zip,1,5) z5, COUNT(*) n_reg
                 FROM vrdb.voters
                 WHERE {roll_where} AND first_name IS NOT NULL AND last_name IS NOT NULL
                   AND reg_zip IS NOT NULL
                 GROUP BY 1,2,3)
        SELECT e.z5, e.amt, COALESCE(r.n_reg,0) = 1 AS matched
        FROM elig e LEFT JOIN roll r USING (last_nm, first_nm, z5)""")

    roll = dict(con.execute(
        f"SELECT county_name, COUNT(*) FROM vrdb.voters WHERE {roll_where} GROUP BY 1").fetchall())
    rt = sum(roll.values())
    shares = {c: (float(m), float(a)) for c, m, a in con.execute("""
        SELECT z.cty,
               100.0*SUM(k.amt) FILTER (WHERE k.matched)
                     /SUM(SUM(k.amt) FILTER (WHERE k.matched)) OVER (),
               100.0*SUM(k.amt)/SUM(SUM(k.amt)) OVER ()
        FROM _gsk k JOIN _gsz z ON z.z5 = k.z5 GROUP BY 1""").fetchall()}
    # The reconstruction's own quality figures, so the footnote's claims are asserted rather
    # than merely described: the match rate this rule reaches, and how pure the ZIP->county
    # assignment is. `diag_donor_geography_selection.py` refuses to report geography for a panel
    # whose rate misses the published one; here they are derived and the paper states them.
    out[f"{prefix}_gs_rate"], = con.execute(
        "SELECT 100.0*SUM(amt) FILTER (WHERE matched)/SUM(amt) FROM _gsk").fetchone()
    out[f"{prefix}_gs_purity"], = con.execute(
        "SELECT 100.0*SUM(modal_n)/SUM(tot) FROM ("
        "  SELECT z5, MAX(n) modal_n, SUM(n) tot FROM ("
        f"    SELECT SUBSTR(reg_zip,1,5) z5, county_name cty, COUNT(*) n FROM vrdb.voters"
        f"    WHERE {roll_where} AND reg_zip IS NOT NULL AND county_name IS NOT NULL"
        "     GROUP BY 1,2) WHERE LENGTH(z5)=5 GROUP BY 1)").fetchone()

    for cty in counties:
        m_pct, a_pct = shares.get(cty, (0.0, 0.0))
        rs = 100.0 * roll.get(cty, 0) / rt if rt else 0.0
        key = cty.lower().replace(" ", "")
        out[f"{prefix}_gs_{key}_m"] = m_pct / rs if rs else 0.0
        out[f"{prefix}_gs_{key}_a"] = a_pct / rs if rs else 0.0
        out[f"{prefix}_gs_{key}_d"] = ((m_pct - a_pct) / rs) if rs else 0.0
    con.execute("DROP TABLE IF EXISTS _gsk")
    con.execute("DROP TABLE IF EXISTS _gsz")


@_timed
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

@_timed
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

@_timed
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
    idc = _conn("id_statewide")
    id_state = (f"contribution_id LIKE 'SUNSHINE:%' AND contribution_amount > 0 "
                f"AND {_G_NOT_UNITEMIZED}")
    # G2 bunching on round Sunshine values
    for amt in (750, 900, 999, 1000, 1001, 1100, 5000, 5001):
        n, = idc.execute(
            f"SELECT COUNT(*) FROM individual_contributions "
            f"WHERE {id_state} AND contribution_amount = {amt}").fetchone()
        out[f"g_bunch_{amt}"] = int(n)

def derive_prose():
    """Every value the prose probes assert. From-scratch SQL, own read-only handles."""
    d = {}

    # ---------------------------------------------------------------- WASHINGTON
    wa = _conn("wa_statewide", "wa_vrdb")
    _d_conc(wa, "wa_fed", FED, d)
    _d_conc(wa, "wa_state", STATE, d)
    _d_conc(wa, "wa_pooled", POOLED, d)
    d["wa_vote_records_m"] = wa.execute(
        "SELECT COUNT(*) / 1e6 FROM vrdb.voting_history").fetchone()[0]
    _d_tier_shares(d)
    _d_rater2(d)
    # Generation multipliers = donor share / roll share. The roll is the ld-scope of
    # voter_scores (one row per voter — the cd scope is still incomplete) RESTRICTED TO ACTIVE
    # REGISTRANTS. The active restriction was added in review round 15: every other baseline in
    # this paper is status_code='A', and Washington's age and turnout cuts were the one
    # exception. `_d_wa_ldscope_crosswalk` retains the unrestricted figures, because the
    # companion Washington papers still use them.
    roll = dict(wa.execute(f"""
        SELECT s.age_cohort, COUNT(*) FROM {_WA_ROLL} s
          JOIN vrdb.voters v USING (state_voter_id)
        WHERE s.age_cohort IS NOT NULL AND {_WA_ACTIVE}
        GROUP BY 1""").fetchall())
    rt = sum(roll.values())
    for tag, panel in (("fed", FED), ("state", STATE)):
        don = dict(wa.execute(f"""
            SELECT s.age_cohort, COUNT(*) FROM {_WA_ROLL} s JOIN {panel} a
              USING(state_voter_id)
              JOIN vrdb.voters v ON v.state_voter_id = s.state_voter_id
            WHERE s.age_cohort IS NOT NULL AND {_WA_ACTIVE}
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
    # Geographic-selection check, Finding 2. WA STATE IS DELIBERATELY ABSENT — its panel does
    # not reconstruct from the bare key rule (PDC name-order defect), so the paper reports
    # federal only for Washington and says why.
    _d_geo_selection(wa, "wa_fed", "FEC", "WA", ("KING",), d)
    # WA state, for its reconstruction RATE only. The paper cites 8.8% against the
    # published 37.1% as the reason this panel is excluded from the check, and a figure
    # cited as a reason has to be derived like any other. No counties are requested.
    _d_geo_selection(wa, "wa_state", "PDC", "WA", (), d)
    # Give<->vote stacking, per panel.
    for tag, panel in (("fed", FED), ("state", STATE)):
        for donor, sup, prop in wa.execute(f"""
            WITH roll AS (SELECT DISTINCT s.state_voter_id, s.is_super_voter,
                                 s.turnout_propensity
                          FROM {_WA_ROLL} s JOIN vrdb.voters v USING (state_voter_id)
                          WHERE {_WA_ACTIVE}),
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
        WITH roll AS (SELECT state_voter_id, is_super_voter FROM {_WA_ROLL})
        SELECT r.state_voter_id, {_std_band_sql(_AGE_2024)} band, {_tenure_sql()} tenure,
               CASE WHEN r.is_super_voter THEN 1.0 ELSE 0.0 END super
        FROM roll r JOIN vrdb.voters v USING (state_voter_id)
        WHERE {_AGE_2024} IS NOT NULL AND {_AGE_2024} >= 18 AND {_WA_ACTIVE}""",
        {"fed": FED, "state": STATE}, d)
    _d_turnout_eligible(wa, "wa", {"fed": FED, "state": STATE}, f"""
        WITH roll AS (SELECT state_voter_id FROM {_WA_ROLL}),
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
        WHERE {_AGE_2024} IS NOT NULL AND {_AGE_2024} >= 18 AND {_WA_ACTIVE}""", d)
    _d_turnout_std(wa, "wa_g2", f"""
        WITH roll AS (SELECT state_voter_id FROM {_WA_ROLL}),
        gen AS (SELECT state_voter_id, COUNT(DISTINCT YEAR(election_date)) g
                FROM vrdb.voting_history
                WHERE MONTH(election_date)=11 AND YEAR(election_date) IN (2022, 2024)
                GROUP BY 1)
        SELECT r.state_voter_id, {_std_band_sql(_AGE_2024)} band, {_tenure_sql()} tenure,
               CASE WHEN COALESCE(gen.g,0) >= 2 THEN 1.0 ELSE 0.0 END super
        FROM roll r JOIN vrdb.voters v USING (state_voter_id)
        LEFT JOIN gen ON gen.state_voter_id = r.state_voter_id
        WHERE {_AGE_2024} IS NOT NULL AND {_AGE_2024} >= 18 AND {_WA_ACTIVE}""",
        {"fed": FED, "state": STATE}, d)
    _d_wa_ldscope_crosswalk(wa, {"fed": FED, "state": STATE}, d)
    # The pin itself. If the snapshot were ever silently re-created, every WA denominator
    # would move and nothing else would notice — so its date and size are probed like any
    # other published figure.
    d["wa_pin_n"], = wa.execute(f"SELECT COUNT(*) FROM {_WA_ROLL}").fetchone()
    d["wa_pin_date"], = wa.execute(
        "SELECT pinned_on FROM donor_paper_wa_roll_meta LIMIT 1").fetchone()

    # ------------------------------------------------------------------ NEW YORK
    ny = _conn("ny_statewide", "ny_vrdb")
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
    # Appendix H1's blocks are ROLL JOINS, so the NY state one carries the 5-row duplicate-id
    # fan-out Appendix C documents: its own-party rows sum to this, not to the panel count.
    d["ny_state_rolljoin_n"] = int(ny.execute(
        f"SELECT COUNT(*) FROM {STATE} a JOIN vrdb.voters v USING (state_voter_id)"
    ).fetchone()[0])
    # Geography: counties, with the roll-share multiplier (the paper's sharpest cut).
    for tag, panel in (("fed", FED), ("state", STATE)):
        _d_counties(ny, f"ny_{tag}", panel, d)
    _d_geo_selection(ny, "ny_fed", "FEC", "NY", ("NEW YORK", "WESTCHESTER"), d)
    _d_geo_selection(ny, "ny_state", "NY", "NY", ("NEW YORK",), d)
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

    # --------------------------------------------------------------------- IDAHO
    ic = _conn("id_statewide", "id_vrdb")
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
    _d_geo_selection(ic, "id_fed", "FEC", "ID", ("ADA", "BLAINE", "BONNEVILLE"), d,
                     roll_where="1=1")
    _d_geo_selection(ic, "id_state", "SUNSHINE", "ID", ("BLAINE",), d, roll_where="1=1")
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
        con = _conn(db)
        n, below = con.execute(f"""
            SELECT COUNT(*), COUNT(*) FILTER (WHERE contribution_amount <= {floor})
            FROM individual_contributions
            WHERE contribution_id LIKE '{prefix}:%' AND contribution_amount > 0""").fetchone()
        d[f"belowfloor_{key}_pct"] = below / n * 100
    # Donor-level, on the built WA state panel — the level the estimator works at.
    wa2 = _conn("wa_statewide")
    n, b100, b25, mn = wa2.execute(f"""
        SELECT COUNT(*), COUNT(*) FILTER (WHERE total_donated <= 100),
               COUNT(*) FILTER (WHERE total_donated <= 25), MIN(total_donated)
        FROM {STATE} WHERE total_donated > 0""").fetchone()
    d["wa_state_donor_le100_pct"] = b100 / n * 100
    d["wa_state_donor_le25_pct"] = b25 / n * 100
    d["wa_state_donor_min"] = float(mn)

    # ---------------------------------------------- harmonized panel comparison ($200)
    # External review item 3. The floors differ, so the panels observe different donor
    # populations; restricting every panel to a donor aggregate above the FEDERAL floor is
    # the direct test. Both the age gap and the layer-concentration ordering move, so these
    # figures are load-bearing and probed rather than left to diag_panel_harmonized.py.
    for st, db, vr, age in (("wa", "wa_statewide", "wa_vrdb", _AGE_2024),
                            ("ny", "ny_statewide", "ny_vrdb", _AGE_2024),
                            ("id", "id_statewide", "id_vrdb", "v.age")):
        con = _conn(db, vr)
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

    # The three roll sizes the "Three populations" paragraph prints, in millions. Derived
    # rather than exempted, because that paragraph is where the paper says what its baseline
    # IS — and it stated the ALL-RECORDS counts for WA and NY while calling them active.
    d["ny_roll_active_m"] = d["ny_roll_active"] / 1e6
    d["id_roll_m"] = d["id_pop_roll_n"] / 1e6

    # Total matched donors across the six panels — the denominator Appendix B's processor
    # disclosure puts its 630 rated rows against.
    d["matched_donors_all_m"] = sum(
        d[f"{s}_{p}_n"] for s in ("wa", "ny", "id") for p in ("fed", "state")) / 1e6

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
    _d_geo_selection_rollup(d)
    _d_residual(d)
    _d_pdc_name_order(d)
    _d_idaho_sample(d)
    _d_sens_summary(d)
    _d_id_primary_ballots(d)
    _d_res_summary(d)
    _d_validation(d)
    _d_appf_panels(d)
    _d_appf_allsix(d)
    # After everything it reads: jaccards (F8 layer), id_state_n/id_fedal_n (panels).
    _d_coverage_extension(d)
    return d

@_timed
def _d_sensitivity(out):
    """D1 — the structural household counts, and the adversarial bound on each finding.

    Independent of `diag_match_error_sensitivity.py` by construction: written from the
    specification, not imported. The pooled budget is the Wilson 95% lower bound on 120/120;
    PANEL_BUDGET is the same bound on the 20 full-name records a single panel contributes.
    """
    budget = 0.031
    age24 = "date_diff('year', v.birthdate, DATE '2024-11-05')"

    # --- part 1: the roll-side structural facts -------------------------------
    for st, vrdb in (("wa", "wa_vrdb"), ("ny", "ny_vrdb"), ("id", "id_vrdb")):
        p = DATA / f"{vrdb}.duckdb"
        if not p.exists():
            continue
        con = _conn(vrdb)
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
            # Pooled: `_conn()` owns the lifetime, `_close_conns()` ends it.
            pass
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
        con = _conn(db, vrdb, alias="sv")
        try:

            def share_pair(expr, bud):
                n, k = con.execute(f"""
                    SELECT COUNT(*), COUNT(*) FILTER (WHERE {expr})
                    FROM {panel} a JOIN sv.voters v USING (state_voter_id)
                    WHERE {age} IS NOT NULL""").fetchone()
                if not n:
                    return None, None
                d = min(int(round(n * bud)), k)
                return 100.0 * k / n, 100.0 * (k - d) / (n - d)

            # `_bd` is the POOLED budget the paper's main table spends. `_pbd` is the
            # PANEL-SPECIFIC one (review round 15): the sample is 20 full-name records per
            # panel, and 0/20 bounds the error at ~16.1% rather than the pooled 3.1%. The
            # paper reports both, because spending a pooled bound panel-by-panel assumes a
            # common error rate across panels and that assumption has to be visible.
            for suf, bud in (("_bd", budget), ("_pbd", PANEL_BUDGET)):
                b, a_ = share_pair(f"{age} >= 65", bud)
                out[f"sens_{key}_b65"] = b
                out[f"sens_{key}_b65{suf}"] = a_
                if party_st:
                    b, a_ = share_pair(f"UPPER(TRIM(v.party)) IN {dem[party_st]}", bud)
                    out[f"sens_{key}_dem"] = b
                    out[f"sens_{key}_dem{suf}"] = a_

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
            # Pooled: `_conn()` owns the lifetime, `_close_conns()` ends it.
            pass

@_timed
def _d_sens_summary(out):
    """Ranges the D1 prose quotes, derived from the per-panel cells rather than exempted."""
    # The abstract's turnout-gap span (Pass 2, 2026-08-14): min/max of the four
    # eligible-for-all age-standardized gaps (NY+WA x fed/state — the four cells F4's
    # table prints; Idaho is composition-only and the abstract now says so). Derived
    # from the same keys the F4 probe asserts, so the abstract cannot quote a span the
    # table no longer supports.
    _eg = [out[f"{s}_{t}_egap_age"] for s in ("ny", "wa") for t in ("fed", "state")
           if f"{s}_{t}_egap_age" in out]
    if len(_eg) == 4:
        out["abs_egap_lo"], out["abs_egap_hi"] = min(_eg), max(_eg)
    out["sens_budget_pct"] = 3.1
    # The pooling demonstration's own subtraction. Printed as 3.0 until 2026-08-11; the
    # unrounded difference is 3.06 and rounds to 3.1 either way, so the old figure was wrong on
    # both conventions. Differenced here so it cannot drift from the three figures it summarises.
    if "wa_pooled_top1" in out and "wa_state_top1" in out:
        out["pool_overstate"] = out["wa_pooled_top1"] - out["wa_state_top1"]
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
        con = _conn("wa_statewide")
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
            # Pooled: `_conn()` owns the lifetime, `_close_conns()` ends it.
            pass

@_timed
def _d_pdc_name_order(out):
    """The WA PDC name-order defect, re-derived independently of its diagnostic script.

    Round 17 asked why a panel is published with a known parser defect and three competing
    estimates of its size. The answer is a measurement rather than a fourth estimate: rebuild
    the primary key both ways and count which resolves. This re-derives it here so the paper's
    figure cannot drift from the script's, and so the placebo — the coincidence rate on the
    comma-formatted FEC layer, where the true name order is known — is asserted too. Without
    that control, "resolves when read backwards" would not distinguish a mis-parsed name from
    an unrelated namesake.
    """
    p = DATA / "wa_statewide.duckdb"
    if not p.exists():
        return
    elig = ("contributor_name IS NOT NULL AND contributor_name <> '' "
            "AND contributor_zip IS NOT NULL AND contributor_zip <> '' "
            "AND UPPER(contributor_name) NOT IN "
            "('SMALL CONTRIBUTIONS', 'UNITEMIZED', 'ANONYMOUS') "
            "AND COALESCE(contributor_type, 'UNKNOWN') NOT IN ('ORGANIZATION', 'COMMITTEE') "
            "AND UPPER(TRIM(contributor_state)) = 'WA'")
    con = _conn("wa_statewide", "wa_vrdb", alias="rv")
    try:
        # ONE pass over the roll, not two. `_rk` (the uniqueness-guarded key) and `_ra` (the
        # same key carrying a birth year) were separate GROUP BYs over the same 5.1M rows.
        # They are not the same aggregation — `_rk` counts every active registrant with a
        # name and ZIP, `_ra` counts only those with a birthdate, and a key holding one dated
        # and one undated registrant is unique in the second but not the first — so they are
        # collapsed with two counters rather than by pretending one implies the other.
        # `ANY_VALUE(...) FILTER` is deterministic here because it is only read where
        # n_dated = 1.
        con.execute("""
            CREATE OR REPLACE TEMP TABLE _rkey AS
            SELECT l, f, z,
                   COUNT(*)                                        AS n_all,
                   COUNT(*) FILTER (WHERE bd IS NOT NULL)          AS n_dated,
                   ANY_VALUE(YEAR(bd)) FILTER (WHERE bd IS NOT NULL) AS byr
            FROM (SELECT UPPER(TRIM(last_name)) l, UPPER(TRIM(first_name)) f,
                         SUBSTR(reg_zip, 1, 5) z, birthdate bd
                  FROM rv.voters WHERE status_code = 'A' AND last_name IS NOT NULL
                    AND first_name IS NOT NULL AND reg_zip IS NOT NULL)
            GROUP BY 1, 2, 3""")
        con.execute("CREATE OR REPLACE TEMP TABLE _rk AS "
                    "SELECT l, f, z FROM _rkey WHERE n_all = 1")
        nrows, nocomma = con.execute(f"""
            SELECT COUNT(*), COUNT(*) FILTER (WHERE contributor_name NOT LIKE '%,%')
            FROM individual_contributions
            WHERE SPLIT_PART(contribution_id, ':', 1) = 'PDC' AND {elig}
              AND LENGTH(SUBSTR(contributor_zip, 1, 5)) = 5""").fetchone()
        out["pdcno_rows"] = float(nrows)
        out["pdcno_nocomma_n"] = float(nocomma)
        out["pdcno_nocomma_pct"] = 100.0 * nocomma / max(nrows, 1)

        # The matcher's parse verbatim — NO whitespace collapse. Collapsing runs of internal
        # space (40,400 PDC rows carry one) produced a 560,182-key universe against the
        # match-rate table's 555,107 comma-less keys, so the two tables described a single
        # layer with denominators 5,075 apart. `SPLIT_PART('SMITH  JANE', ' ', 2)` is the
        # empty string, the key fails the `LENGTH(ff) > 1` guard below, and it is absent from
        # BOTH tables — which is the correct behaviour and the reconciliation.
        con.execute(f"""
            CREATE OR REPLACE TEMP TABLE _v AS
            SELECT UPPER(TRIM(SPLIT_PART(nm, ' ', 1))) fl, UPPER(SPLIT_PART(nm, ' ', 2)) ff,
                   UPPER(LIST_EXTRACT(STR_SPLIT(nm, ' '), -1)) rl,
                   UPPER(SPLIT_PART(nm, ' ', 1)) rf, z, SUM(amt) d
            FROM (SELECT TRIM(UPPER(contributor_name)) nm,
                         SUBSTR(contributor_zip, 1, 5) z, contribution_amount amt
                  FROM individual_contributions
                  WHERE SPLIT_PART(contribution_id, ':', 1) = 'PDC' AND {elig}
                    AND contributor_name NOT LIKE '%,%')
            WHERE LENGTH(z) = 5
            GROUP BY 1, 2, 3, 4, 5""")
        # Picking the reversed variant DETERMINISTICALLY, and as a pair.
        #
        # One forward key can carry several reversed variants ("SMITH JOHN" and
        # "SMITH MARY" share the forward key (SMITH, J...)), and the age cut below reads a
        # registrant through whichever one is kept. The original `ANY_VALUE(rl), ANY_VALUE(rf)`
        # picked arbitrarily *per run* — it follows scan and hash order — which made the two
        # age figures wobble in the fourth decimal between otherwise identical passes
        # (43.9853 against 43.9877). A verifier that exists to catch drift must not produce it.
        #
        # Column-wise MIN would be stable but wrong: MIN(rl) and MIN(rf) taken independently
        # can name a pair that no variant of that key actually has. MIN over a STRUCT compares
        # field-wise and returns one real (rl, rf) pair, which is what the join needs.
        con.execute("""
            CREATE OR REPLACE TEMP TABLE _r AS
            SELECT fl, ff, z, d, hf, hr, rv.rl AS rl, rv.rf AS rf FROM (
                SELECT fl, ff, z, SUM(d) d, MAX(hf) hf, MAX(hr) hr,
                       MIN(STRUCT_PACK(rl := rl, rf := rf)) rv FROM (
                    SELECT v.fl, v.ff, v.z, v.d, v.rl, v.rf,
                           CASE WHEN a.l IS NOT NULL THEN 1 ELSE 0 END hf,
                           CASE WHEN b.l IS NOT NULL THEN 1 ELSE 0 END hr
                    FROM _v v
                    LEFT JOIN _rk a ON a.l = v.fl AND a.f = v.ff AND a.z = v.z
                    LEFT JOIN _rk b ON b.l = v.rl AND b.f = v.rf AND b.z = v.z)
                WHERE fl <> '' AND LENGTH(ff) > 1
                GROUP BY 1, 2, 3)""")
        row = con.execute("""
            WITH r AS (SELECT * FROM _r)
            SELECT COUNT(*), SUM(d),
                   COUNT(*) FILTER (WHERE hf = 1 AND hr = 0),
                   COUNT(*) FILTER (WHERE hr = 1 AND hf = 0),
                   COALESCE(SUM(d) FILTER (WHERE hr = 1 AND hf = 0), 0),
                   COUNT(*) FILTER (WHERE hf = 1 AND hr = 1),
                   COUNT(*) FILTER (WHERE hf = 0 AND hr = 0)
            FROM r""").fetchone()
        keys, dollars, fwd, rev, revd, both, neither = (float(x) for x in row)
        out["pdcno_keys"] = keys
        out["pdcno_fwd_only"] = fwd
        out["pdcno_rev_only"] = rev
        out["pdcno_both"] = both
        out["pdcno_neither"] = neither
        out["pdcno_fwd_pct"] = 100.0 * fwd / max(keys, 1)
        out["pdcno_rev_pct"] = 100.0 * rev / max(keys, 1)
        out["pdcno_both_pct"] = 100.0 * both / max(keys, 1)
        out["pdcno_rev_dollars_m"] = revd / 1e6
        out["pdcno_rev_dollar_pct"] = 100.0 * revd / max(dollars, 1.0)
        out["pdcno_reach_either"] = 100.0 * (fwd + rev + both) / max(keys, 1)

        # Placebo: the FEC layer files LAST, FIRST, so swapping the halves is a key known to
        # be wrong. How often it still resolves is the coincidence rate.
        pk, ptrue, pswap = con.execute(f"""
            WITH f AS (
                SELECT UPPER(TRIM(SPLIT_PART(contributor_name, ',', 1))) tl,
                       UPPER(SPLIT_PART(TRIM(SPLIT_PART(contributor_name, ',', 2)), ' ', 1)) tf,
                       SUBSTR(contributor_zip, 1, 5) z
                FROM individual_contributions
                WHERE SPLIT_PART(contribution_id, ':', 1) = 'FEC' AND {elig}
                  AND contributor_name LIKE '%,%' AND LENGTH(SUBSTR(contributor_zip,1,5)) = 5
                GROUP BY 1, 2, 3 HAVING tl <> '' AND LENGTH(tf) > 1)
            SELECT COUNT(*), COUNT(*) FILTER (WHERE a.l IS NOT NULL),
                   COUNT(*) FILTER (WHERE b.l IS NOT NULL AND a.l IS NULL)
            FROM f
            LEFT JOIN _rk a ON a.l = f.tl AND a.f = f.tf AND a.z = f.z
            LEFT JOIN _rk b ON b.l = f.tf AND b.f = f.tl AND b.z = f.z""").fetchone()
        out["pdcno_placebo_keys"] = float(pk)
        out["pdcno_placebo_swap_n"] = float(pswap)
        out["pdcno_placebo_pct"] = 100.0 * pswap / max(pk, 1)
        out["pdcno_excess_pts"] = out["pdcno_rev_pct"] - out["pdcno_placebo_pct"]

        # The reconciliation the paper prints: this diagnostic's comma-less universe plus the
        # comma-bearing keys, less the keys reachable from both, equals the match-rate table's
        # total. Derived rather than asserted, because a reconciliation nobody recomputes is
        # just three numbers that happen to add up today.
        last_c = ("CASE WHEN contributor_name LIKE '%,%' "
                  "THEN UPPER(TRIM(SPLIT_PART(contributor_name, ',', 1))) "
                  "ELSE UPPER(TRIM(SPLIT_PART(TRIM(contributor_name), ' ', 1))) END")
        first_c = ("CASE WHEN contributor_name LIKE '%,%' "
                   "THEN UPPER(SPLIT_PART(TRIM(SPLIT_PART(contributor_name, ',', 2)), ' ', 1)) "
                   "ELSE UPPER(SPLIT_PART(TRIM(contributor_name), ' ', 2)) END")
        base = (f"SPLIT_PART(contribution_id, ':', 1) = 'PDC' AND {elig} "
                f"AND LENGTH(SUBSTR(contributor_zip, 1, 5)) = 5")

        def _keyset(extra):
            return (f"SELECT {last_c} l, {first_c} f, SUBSTR(contributor_zip,1,5) z "
                    f"FROM individual_contributions WHERE {base}{extra} GROUP BY 1,2,3 "
                    f"HAVING l <> '' AND LENGTH(f) > 1")

        n_comma, = con.execute(
            f"SELECT COUNT(*) FROM ({_keyset(" AND contributor_name LIKE '%,%'")})").fetchone()
        n_both, = con.execute(
            f"SELECT COUNT(*) FROM ({_keyset(" AND contributor_name LIKE '%,%'")}) a "
            f"JOIN ({_keyset(" AND contributor_name NOT LIKE '%,%'")}) b USING (l, f, z)"
        ).fetchone()
        out["pdcno_comma_keys"] = float(n_comma)
        out["pdcno_both_form_keys"] = float(n_both)

        # Would repairing it move Finding 1? Age = 2024 - birth year, the paper's convention.
        # Read off `_rkey` rather than re-scanning the roll. `by` is a DuckDB reserved word in
        # alias position (BY NAME) and fails with a bare "syntax error at or near", hence `byr`.
        con.execute("CREATE OR REPLACE TEMP TABLE _ra AS "
                    "SELECT l, f, z, byr FROM _rkey WHERE n_dated = 1")
        mn, m65 = con.execute("""
            SELECT COUNT(*), COUNT(*) FILTER (WHERE 2024 - ra.byr >= 65)
            FROM _r r JOIN _ra ra ON ra.l = r.fl AND ra.f = r.ff AND ra.z = r.z
            WHERE r.hf = 1""").fetchone()
        rn, r65 = con.execute("""
            SELECT COUNT(*), COUNT(*) FILTER (WHERE 2024 - ra.byr >= 65)
            FROM _r r JOIN _ra ra ON ra.l = r.rl AND ra.f = r.rf AND ra.z = r.z
            WHERE r.hf = 0 AND r.hr = 1""").fetchone()
    finally:
        # Pooled connection: `_conn()` owns its lifetime, but NOT its temp tables.
        # These four are roll-sized and would otherwise sit on the shared WA
        # connection for the rest of the run.
        _drop_temps(con, "_rkey", "_rk", "_ra", "_v", "_r")
    out["pdcno_matched_b65"] = 100.0 * m65 / max(mn, 1)
    out["pdcno_recoverable_b65"] = 100.0 * r65 / max(rn, 1)
    out["pdcno_repaired_b65"] = 100.0 * (m65 + r65) / max(mn + rn, 1)


@_timed
def _d_idaho_sample(out):
    """Zero-error Wilson bounds the drawn Idaho sample supports, BY STRATUM.

    The first version of this reported a single 3.6% bound from n=102 per panel. That was
    wrong, and an external reviewer caught it: the draw is a deliberately **disproportionate
    stratified** sample — balanced across DEM/REP/UNA and across dollar bands — not a simple
    random sample of the panel, so a pooled binomial bound over its 102 records is not a bound
    on the panel's error rate. Correcting one pooled-bound error and immediately committing
    another would have been the worst possible outcome of the previous round.

    What the design actually supports, and what the party finding actually needs, is the
    **party-stratum** bound: the Idaho vulnerability is specifically whether match error
    inflates the Democratic share, so the relevant quantity is the error rate among the
    Democratic records, at n=34 per panel. The pooled figure survives only as a
    composition-reweighted precision estimate, never as a binomial bound.

    For 0 observed errors the Wilson upper bound reduces to z^2 / (n + z^2).
    """
    z2 = 1.959963985 ** 2

    def wilson_zero(n):
        return 100.0 * z2 / (n + z2)

    # The 2026-08-01 `idaho1` draw: 204 records, 102 per panel, 68 per party across the two
    # panels (34 per party per panel), 51 per dollar band per panel — and, NESTED inside each
    # party stratum, two deliberately balanced dollar-band cells of 17.
    out["idaho_n_total"] = 204.0
    out["idaho_n_panel"] = 102.0
    out["idaho_n_party_panel"] = 34.0
    out["idaho_n_band_panel"] = 51.0
    out["idaho_n_party_cell"] = 17.0
    # THE PARTY-STRATUM BOUND, DESIGN-CORRECTED 2026-08-14 (external referee, publication
    # blocker). The pre-specified plan pooled each party's two dollar-band cells and put a
    # Wilson bound on the pooled n=34 — repeating, one level down, the pooled-bound error
    # the plan was written to avoid: the top decile is ~10% of the donor population but half
    # the party stratum's observations, so the n=34 bound is not a binomial bound on the
    # party stratum's error rate. The design-respecting bound is per party x dollar-band
    # CELL (n=17): with zero errors in both cells, any design weighting of the two equal
    # cell bounds equals the cell bound, and a conservative simultaneous construction
    # (each cell at 97.5%, Bonferroni) is derived beside it. The pooled n=34 figure is
    # retained ONLY as the retired pre-specification, quoted by the correction note.
    out["idaho_bound_party_cell"] = wilson_zero(17)          # 18.43 — the operative bound
    _z975 = 2.2414027276049473
    out["idaho_bound_party_cell_simul"] = 100.0 * _z975**2 / (17 + _z975**2)   # 22.81
    out["idaho_bound_party_panel"] = wilson_zero(34)   # RETIRED pooled construction (10.15)
    out["idaho_bound_band_panel"] = wilson_zero(51)
    out["idaho_bound_panel_pooled"] = wilson_zero(102)  # reweighted estimate only, not a bound
    out["idaho_bound_current"] = wilson_zero(20)        # what 20 full-name records support now

    # Apply the Democratic-stratum bound to the party rows it is there to defend. Worst case:
    # delete that share of the panel's registered Democrats outright — at the corrected cell
    # bound, and at the simultaneous construction so the paper can say both clear.
    for tag in ("fed", "state"):
        dem = out.get(f"sens_id_{tag}_dem")
        if dem is None:
            continue
        out[f"idaho_dem_after_stratum_{tag}"] = (
            dem * (1.0 - out["idaho_bound_party_cell"] / 100.0))
        out[f"idaho_dem_after_simul_{tag}"] = (
            dem * (1.0 - out["idaho_bound_party_cell_simul"] / 100.0))
        # The same deletion at the RETIRED pooled n=34 bound — quoted only by the paper's
        # correction parenthetical ("An earlier version printed ... here"), derived rather
        # than left as a literal so the historical figures stay tied to their construction.
        out[f"idaho_dem_after_retired_{tag}"] = (
            dem * (1.0 - out["idaho_bound_party_panel"] / 100.0))

    # The per-cell confidence of the simultaneous construction: Bonferroni splits the 5%
    # across the party stratum's two cells, so each cell is bounded at 100 - 5/2 = 97.5%.
    out["idaho_simul_cell_conf"] = 100.0 - 5.0 / 2.0

    # THE PANEL-WIDE CONSTRUCTION AT THE SAME CEILING (added 2026-08-11 after external review;
    # recomputed at the corrected cell bound 2026-08-14). F7's deletion table applies the
    # budget PANEL-WIDE — delete `budget x panel` records, all from the bucket supporting the
    # finding — while the stratum defence applies the bound WITHIN the stratum with the panel
    # denominator fixed. Those are different operations, and the Idaho result survives on the
    # second and not the first — at the corrected bound the panel-wide construction fails
    # DECISIVELY rather than narrowly, which the paper now states.
    b = out["idaho_bound_party_cell"] / 100.0
    for tag in ("fed", "state"):
        dem = out.get(f"sens_id_{tag}_dem")
        if dem is None:
            continue
        out[f"idaho_dem_panelwide_at_party_ceiling_{tag}"] = (
            (dem / 100.0 - b) / (1.0 - b) * 100.0)


@_timed
def _d_id_primary_ballots(out):
    """The 2024 Idaho primary: participants, party ballots, and the gap between them.

    F4's footnote lists five party-ballot counts that sum to 273,884 against the 274,684
    participants in the table above it. That 800-record difference was silent until an external
    read caught it, in a paper that reconciles 555,922 against 555,107 down to the individual
    comma-bearing key. It is participants whose `ballot_choice` is blank — recorded as voting in
    the primary with no party ballot recorded — and the footnote now says so, which means the
    number has to be derived.
    """
    p = DATA / "id_vrdb.duckdb"
    if not p.exists():
        return
    con = _conn("id_vrdb")
    rows = dict(con.execute("""
        SELECT COALESCE(NULLIF(TRIM(ballot_choice), ''), '(blank)'),
               COUNT(DISTINCT state_voter_id)
        FROM voter_participation WHERE election_year = 2024 AND kind = 'PRIMARY'
        GROUP BY 1""").fetchall())
    out["id_pri_participants"] = sum(rows.values())
    out["id_pri_party_ballots"] = sum(v for k, v in rows.items() if k != "(blank)")
    out["id_pri_no_ballot"] = rows.get("(blank)", 0)


@_timed
def _d_res_summary(out):
    """Ranges the D3 prose quotes."""
    keys = ("wa_fed", "wa_state", "ny_fed", "ny_state", "id_fed", "id_state")
    # Same convention as _d_sens_summary: the prose summarises the printed table.
    # `guard` joined the list in round 17, when the body's standalone guard table was
    # dropped and its prose range had to come off the resident-basis cascade instead of the
    # unrestricted match-rate derivation — the two differ (1.1-2.3% against 1.3-2.7%) and
    # quoting one beside the other's table is the mixed-basis defect that round flagged.
    for b in ("difzip", "nameform", "none", "guard"):
        vals = sorted(round(out[f"res_{k}_{b}"], 1) for k in keys if f"res_{k}_{b}" in out)
        if vals:
            out[f"res_{b}_lo"], out[f"res_{b}_hi"] = vals[0], vals[-1]
    # Idaho's export carries no status flag, so its inactive bucket is structurally 0.0
    # rather than measured — including it would print a range starting at zero and imply
    # a panel where nobody has lapsed.
    _inact = sorted(round(out[f"res_{k}_inactive"], 1)
                    for k in ("wa_fed", "wa_state", "ny_fed", "ny_state")
                    if f"res_{k}_inactive" in out)
    if _inact:
        out["res_inactive_lo"], out["res_inactive_hi"] = _inact[0], _inact[-1]

@_timed

def _d_geo_selection_rollup(out):
    """Aggregate the geographic-selection check into the figures the prose quotes.

    Derived from the per-panel cells rather than typed, so a change to any cell moves the
    summary with it — the drift this series keeps finding is a summary that outlived the table
    it summarises.
    """
    stems = [k[:-2] for k in out if k.endswith("_m") and "_gs_" in k]
    if stems:
        out["gs_worst_move"] = max(abs(out[f"{st}_d"]) for st in stems if f"{st}_d" in out)
    # WA state carries a purity figure but no counties; it belongs in the range all the same,
    # because the range describes the ZIP->county assignment per STATE, not per panel.
    pur = [v for k, v in out.items() if k.endswith("_gs_purity")]
    if pur:
        out["gs_purity_lo"], out["gs_purity_hi"] = min(pur), max(pur)
    # The one cell that differs from the multiplier reported earlier in the section. That gap
    # IS the address-source effect the check assumes is negligible, so it is derived, not
    # asserted in prose alone.
    if "cty_id_state_blaine_mult" in out and "id_state_gs_blaine_m" in out:
        out["gs_blaine_basis_gap"] = abs(
            out["cty_id_state_blaine_mult"] - out["id_state_gs_blaine_m"])
    # How far the five reconstructable panels sit from their published match rates. The paper
    # says "within 0.3 points"; PUBLISHED is the same table diag_donor_geography_selection.py
    # validates against, and mr_*_cov is this script's own independent re-derivation of it.
    drifts = [abs(out[f"{k}_gs_rate"] - out[f"mr_{k}_cov"])
              for k in ("wa_fed", "ny_fed", "ny_state", "id_fed", "id_state")
              if f"{k}_gs_rate" in out and f"mr_{k}_cov" in out]
    if drifts:
        out["gs_recon_worst"] = max(drifts)

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
        con = _conn(db, vrdb, alias="cv")
        try:
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
            # Pooled: `_conn()` owns the lifetime, `_close_conns()` ends it.
            pass
        for c, mult, part, inten in rows:
            if c in wanted:
                slug = c.lower().replace(" ", "")
                out[f"cty_{key}_{slug}_mult"] = float(mult)
                out[f"cty_{key}_{slug}_part"] = float(part)
                out[f"cty_{key}_{slug}_inten"] = float(inten)

@_timed
def _d_residual(out):
    """D3 — the non-match cascade, as shares of eligible **resident** donor identities.

    Residence-restricted since round 17. An out-of-state key cannot match the state's own
    roll, so under an unrestricted denominator it falls into the final "no roll counterpart"
    bucket and inflates it — enough that the bucket was the largest in the WA and ID state
    panels, contradicting the sentence above the table. It also put this table on a
    different denominator from the strict-key match-rate table immediately preceding it.
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
            "AND COALESCE(contributor_type, 'UNKNOWN') NOT IN ('ORGANIZATION', 'COMMITTEE')")
    panels = [("wa_fed", "wa_statewide", "wa_vrdb", "FEC", True, "WA"),
              ("wa_state", "wa_statewide", "wa_vrdb", "PDC", True, "WA"),
              ("ny_fed", "ny_statewide", "ny_vrdb", "FEC", True, "NY"),
              ("ny_state", "ny_statewide", "ny_vrdb", "NY", True, "NY"),
              ("id_fed", "id_statewide", "id_vrdb", "FEC", False, "ID"),
              ("id_state", "id_statewide", "id_vrdb", "SUNSHINE", False, "ID")]
    for key, db, vrdb, pfx, has_status, st in panels:
        p = DATA / f"{db}.duckdb"
        if not p.exists():
            continue
        con = _conn(db, vrdb, alias="rv")
        try:
            src = (f"SPLIT_PART(contribution_id, ':', 1) = '{pfx}' "
                   f"AND UPPER(TRIM(contributor_state)) = '{st}'")
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
            # Pooled: `_conn()` owns the lifetime, `_close_conns()` ends it.
            pass
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

@_timed
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
        con = _conn(db)
        try:
            rows, pos = con.execute(
                f"SELECT COUNT(*), COUNT(*) FILTER (WHERE total_donated > 0) "
                f"FROM {tbl}").fetchone()
        finally:
            # Pooled: `_conn()` owns the lifetime, `_close_conns()` ends it.
            pass
        out[f"appf_{key}_rows"] = rows
        out[f"appf_{key}_pos"] = pos
    if "appf_wa_state_rows" in out:
        out["appf_wa_state_gap"] = out["appf_wa_state_rows"] - out["appf_wa_state_pos"]

    # Idaho Sunshine's organisation share, from the persisted contributor_type field rather
    # than a name heuristic — which is the whole point of the sentence that quotes it.
    p = DATA / "id_statewide.duckdb"
    if p.exists():
        con = _conn("id_statewide")
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
            # Pooled: `_conn()` owns the lifetime, `_close_conns()` ends it.
            pass
        out["appf_id_org_pct"] = 100.0 * no / n if n else 0.0
        out["appf_id_org_dollar_pct"] = 100.0 * float(amto) / float(amt) if amt else 0.0
        out["appf_id_org_m"] = float(amto) / 1e6
        out["appf_id_total_m"] = float(amt) / 1e6

    # The surname-vocabulary name-order heuristic that used to live here was REMOVED in round
    # 17. It measured 4.7% / 4.1% against a published 1.85% / 2.08%, was a different instrument
    # rather than a check on that one, and was expected to over-detect (a genuinely rare surname
    # is absent from the roll's vocabulary too). Both figures are withdrawn from the paper and
    # the mode is now measured directly by `_d_pdc_name_order`, which rebuilds the key both ways
    # and carries a placebo control. Deleting it also removes a full-roll scan from every cold
    # derive; nothing references its two output keys.


@_timed
def _d_coverage_extension(out):
    """Derivations for the sections brought under the audit on 2026-08-14 (full-paper
    coverage): the front matter's two-panels block, the limits bullets, Appendix C's
    New York state-panel paragraph, and Appendix E's four-state statewide table.

    Two of these derivations exist because writing them found live defects:
      * Appendix C said "$379.5M matches to a registered New York voter" — that is the
        RETIRED all-tier panel's dollars (measured 379.46 on
        voter_donor_affiliation_state_alltier); the primary specification is 339.8. The
        paragraph survived the tier-switch prose sweep (audit-log R17–R24) by sitting
        outside every slice. The paper now states both, labelled.
      * Appendix E's statewide table printed Idaho's top-1% as 36.0 against an unrounded
        36.0519 (→ 36.1) — the same stale last digit verify_cross_state_money.py's
        2026-08-02 round corrected in ITS paper, surviving here as an unsliced copy.
    """
    # --- WA retired all-tier trio, quoted in the front matter's pooling demonstration.
    wa = _conn("wa_statewide")
    for tag, tbl in (("pooled", "voter_donor_affiliation_alltier"),
                     ("fed", "voter_donor_affiliation_fec_alltier"),
                     ("state", "voter_donor_affiliation_state_alltier")):
        v, = wa.execute(f"""
            WITH r AS (SELECT total_donated t, NTILE(100) OVER (ORDER BY total_donated DESC) p
                       FROM {tbl} WHERE total_donated > 0)
            SELECT 100.0*SUM(t) FILTER (WHERE p=1)/SUM(t) FROM r""").fetchone()
        out[f"wa_{tag}_alltier_top1"] = float(v)

    # --- Jaccard span, quoted as a range in the front matter and the limits bullet.
    _j = [out[k] for k in ("wa_jaccard", "ny_jaccard", "id_jaccard") if k in out]
    if len(_j) == 3:
        out["jaccard_lo"], out["jaccard_hi"] = min(_j), max(_j)

    # --- Idaho state-vs-aligned-federal reach ("59% more", the limits bullet).
    if "id_state_n" in out and "id_fedal_n" in out:
        out["id_state_reach_gain_pct"] = (
            100.0 * (out["id_state_n"] - out["id_fedal_n"]) / out["id_fedal_n"])

    # --- Appendix C's New York state-panel paragraph: the feed, the two match totals,
    # and the no-prefix residue. All from ny_statewide, which this gate already opens.
    ny = _conn("ny_statewide")
    out["ny_feed_rows"], out["ny_feed_m"] = (
        float(x) for x in ny.execute("""
            SELECT COUNT(*), SUM(contribution_amount)/1e6 FROM individual_contributions
            WHERE contribution_id LIKE 'NY:%'""").fetchone())
    out["ny_state_alltier_m"], = (float(x) for x in ny.execute(
        "SELECT SUM(total_donated)/1e6 FROM voter_donor_affiliation_state_alltier"
    ).fetchone())
    out["ny_noprefix_rows"], out["ny_noprefix_m"] = (
        float(x) for x in ny.execute("""
            SELECT COUNT(*), SUM(contribution_amount)/1e6 FROM individual_contributions
            WHERE contribution_id NOT LIKE 'NY:%' AND contribution_id NOT LIKE 'FEC:%'
        """).fetchone())

    # --- Appendix E's statewide (all-itemized-donor) concentration table, four states.
    # Same donor proxy (name|ZIP within the outflow filter) verify_cross_state_money.py
    # asserts its paper's copies with, at the same 0.05 tolerance; the two papers print
    # the same quantity and must not drift apart again. TX has no other use in this gate,
    # so its connection is local rather than pooled.
    for st in ("wa", "ny", "id", "tx"):
        con = (duckdb.connect(str(DATA / "tx_statewide.duckdb"), read_only=True)
               if st == "tx" else _conn(f"{st}_statewide"))
        t1, t10, g = con.execute(f"""
            WITH dd AS (SELECT contributor_name || '|' || COALESCE(contributor_zip,'') dnr,
                               SUM(contribution_amount) amt
                        FROM individual_contributions
                        WHERE regexp_matches(COALESCE(fec_candidate_id,''),'^[CPHS][0-9]')
                          AND contributor_state='{st.upper()}' AND contribution_amount>0
                        GROUP BY 1),
            r AS (SELECT amt, NTILE(100) OVER (ORDER BY amt DESC) p,
                         ROW_NUMBER() OVER (ORDER BY amt) rn,
                         COUNT(*) OVER () n, SUM(amt) OVER () s
                  FROM dd)
            SELECT 100.0*SUM(amt) FILTER (WHERE p=1)/ANY_VALUE(s),
                   100.0*SUM(amt) FILTER (WHERE p<=10)/ANY_VALUE(s),
                   (2.0*SUM(rn*amt)/(MAX(n)*MAX(s))) - (MAX(n)+1.0)/MAX(n)
            FROM r""").fetchone()
        out[f"sw_{st}_top1"], out[f"sw_{st}_top10"], out[f"sw_{st}_gini"] = (
            float(t1), float(t10), float(g))
        if st == "tx":
            con.close()


@_timed
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

@_timed
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

        # Partial merges by tier (review round 15). The paper reported the total of 8 without
        # the split, and the split is the informative part: one of them is on the PRIMARY
        # full-name key, which is the only detected dollar-total inflation on the specification
        # the concentration finding runs on.
        for i, tier in enumerate(_TIER_ORDER):
            n, = con.execute(f"""SELECT COUNT(*) FROM {v}
                WHERE COALESCE(TRIM(CAST(partial_merge AS VARCHAR)), '') <> ''
                  AND match_tier = '{tier}'""").fetchone()
            out[f"val_pm_t{i}"] = n
        out["val_pm_total"] = sum(out[f"val_pm_t{i}"] for i in range(len(_TIER_ORDER)))

        # The PANEL-SPECIFIC Wilson ceiling on the primary key (review round 15). The paper's
        # 3.1% budget is the POOLED bound over 120 full-name records; the sample is 20 per
        # panel, and 0/20 bounds the error at ~16.1%, not 3.1%. Both are derived so the paper
        # cannot state one and mean the other.
        n_pp, = con.execute(f"""
            SELECT COUNT(*) FROM {v}
            WHERE match_tier = 'STRICT_ZIP5_FULL' AND state = 'WA' AND panel = 'federal'"""
        ).fetchone()
        # _wilson returns PERCENTAGES, so the error ceiling is 100 minus the precision floor.
        out["val_t0_panel_n"] = n_pp
        out["val_t0_panel_err_hi"] = 100.0 - _wilson(n_pp, n_pp)[0]
        out["val_t0_pooled_err_hi"] = 100.0 - out["val_t0_lo"]

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

@_timed
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
        con = _conn(db, vrdb, alias="mrv")
        try:
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
            # Pooled: `_conn()` owns the lifetime, `_close_conns()` ends it.
            pass

    _rc = sorted(out[f"mr_{k}_recall"] for k, *_ in panels if f"mr_{k}_recall" in out)
    _cv = sorted(out[f"mr_{k}_cov"] for k, *_ in panels if f"mr_{k}_cov" in out)
    _gd = sorted(out[f"mr_{k}_guard_pct"] for k, *_ in panels if f"mr_{k}_guard_pct" in out)
    if _rc:
        out["_mr_recall_lo"], out["_mr_recall_hi"] = _rc[0], _rc[-1]
        out["_mr_cov_lo"], out["_mr_cov_hi"] = _cv[0], _cv[-1]
        out["_mr_guard_lo"], out["_mr_guard_hi"] = _gd[0], _gd[-1]

# ============================== DERIVATION CACHE ==============================
# The derivation layer runs 29 full-roll aggregations across eight DuckDB files, and a full run
# now exceeds ten minutes. During a review it is re-run after every PROSE edit, when its inputs
# have not changed at all — the 2026-07-29/30 session ran it about twenty times against two
# database writes, so roughly nine runs in ten recomputed a bit-identical answer.
#
# The key is this file's own source hash plus (size, mtime_ns) for every input, so editing a
# derivation or reloading data invalidates it. That is the standard build-cache heuristic and it
# has the standard limit, stated rather than hidden: a file rewritten in place to an identical
# byte length AND mtime would not be detected. `--refresh` forces recomputation and is what to
# use before any release, or whenever a load is in doubt.
_CACHE_DIR = ROOT / ".verify_cache"
_CACHE_FILE = _CACHE_DIR / "donor_class_derivations.json"
_REFRESH = "--refresh" in sys.argv
_PROFILE = "--profile" in sys.argv

def _cache_key() -> str:
    h = hashlib.sha256()
    h.update(Path(__file__).read_bytes())
    for p in sorted(list(DATA.glob("*.duckdb"))
                    + list((ROOT / "docs" / "reference").glob("*.csv"))):
        st = p.stat()
        h.update(f"{p.name}:{st.st_size}:{st.st_mtime_ns}".encode())
    return h.hexdigest()

def _jsonable(v):
    """Decimal arrives from SUM(); the warning keys hold lists of strings."""
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (list, tuple)):
        return [_jsonable(x) for x in v]
    return v

_DERIVED: dict | None = None


def cached_derive():
    """`derive_prose()`, memoised on this file plus every input's fingerprint.

    Two layers, and the in-process one is not redundant. This is called twice per run — once
    by the prose probes and once by the coverage audit — and `--refresh` deliberately skips
    the on-disk cache. Without the in-process memo, `--refresh` therefore ran the ENTIRE
    derivation layer twice: ~6.5 minutes of it, doubled, which is most of why a release-gate
    run took upward of 40 minutes against a plain cold run's 8 and made the gate something
    to avoid. `--refresh` means "do not trust the file", not "recompute per caller".
    """
    global _DERIVED
    if _DERIVED is not None:
        return _DERIVED
    key = _cache_key()
    if not _REFRESH and _CACHE_FILE.exists():
        try:
            blob = json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            blob = {}
        if blob.get("key") == key:
            print(f"  (derivations reused from {_CACHE_FILE.name}: this file and every input "
                  f"are unchanged. --refresh recomputes.)")
            _DERIVED = blob["derived"]
            return _DERIVED
    t0 = time.monotonic()
    d = derive_prose()
    # NOT closed here. `derive_prose` binds three module-level handles (`wa`, `ny`, `idc`) to
    # the same objects the pool holds, so closing mid-run leaves those names pointing at dead
    # connections — harmless only for as long as the memo guarantees one derive pass, and a
    # trap for whoever next touches the caching. They are closed once at the end of the run.
    if _PROFILE and _TIMINGS:
        print("\n  derivation profile (slowest first):")
        for name, secs in sorted(_TIMINGS.items(), key=lambda kv: -kv[1])[:20]:
            print(f"    {secs:7.1f}s  {name}")
        print(f"    {sum(_TIMINGS.values()):7.1f}s  total in timed derivations")
    try:
        _CACHE_DIR.mkdir(exist_ok=True)
        _CACHE_FILE.write_text(
            json.dumps({"key": key, "derived": {k: _jsonable(v) for k, v in d.items()}}),
            encoding="utf-8")
        print(f"  (derivations computed in {time.monotonic() - t0:.0f}s and cached)")
    except (OSError, TypeError) as e:
        print(f"  (derivations computed in {time.monotonic() - t0:.0f}s; NOT cached: {e})")
    _DERIVED = d
    return d

# Sections of the paper. A probe is scoped to one so that a row shape repeated across
# states (the "18-29" age row appears in both the NY and the ID table) cannot be asserted
# against the wrong state's derivation.
SECTION_BOUNDS = {
    # The ABSTRACT, added 2026-08-14 (Pass 2 of the calculation review). It was the one
    # result-bearing block of this paper outside every slice — the coverage gate audited
    # nineteen sections of the WA paper including its abstract while the lead article's
    # abstract carried a single probe. The scope doc weights abstracts first for exactly
    # this reason: an abstract restates four sections and is what an editor reads.
    "abstract": ("## Abstract", "## The question"),
    # The main-body methods section, added 2026-07-29 for review #10. Every figure in it
    # but two restates one published elsewhere in the paper, which is exactly why it is
    # audited rather than trusted.
    # The methods section is cut into three ADJACENT, non-overlapping slices that together
    # cover it end to end. Spans are per-section coordinates, so an overlap reports one
    # slice's probed cells as the other's unmapped ones — the failure that cost review rounds
    # 5 and 7 a section each. Splitting rather than nesting also means the tail of the section
    # stays audited: an earlier attempt ended `methods` at the match-rate heading and left
    # everything after it in no slice at all, which silently dropped the tier table.
    # The literature section, added round 15. Sliced and audited like everything else: it is
    # prose rather than results, but an unaudited section is where the last three reviewers
    # found defects, and any figure that migrates into it must be probed.
    "priorwork": ("## Prior work, and what this paper adds", "## Data, linkage, and validation"),
    "methods": ("## Data, linkage, and validation",
                "**Spending the error budget against each finding"),
    # D1, added 2026-07-29. Adjacent to `methods`, which now ends at its heading.
    "sensitivity": ("**Spending the error budget against each finding",
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
    "appc_mid": ("- **Temporal alignment.**", "Idaho's Sunshine layer holds three years"),
    "appc_tail2": ("**The match key and its four tiers.**", "## Appendix D — Related work"),
    "appe_head": ("## Appendix E — Full distribution tables",
                  "**Matched-donor concentration, with bootstrap interv"),
    "appe_mid": ("**Candidate money versus total flow.**",
                 "**Geographic concentration of matched dollars, by pa"),
    "appf_head": ("## Appendix F — Match validation and robustness",
                  "**Matchability by party, and why the party finding d"),
    "appf_mid": ("**Per-tier false-merge risk on the donor side.**",
                 "**Result — detected precision differs sharply by mat"),
    # Round 17 moved the error-budget tables, the roll-collision measurements, the
    # de-merge stress test and the residual cascade out of the article body and into
    # Appendix F sections F7/F8. The slices follow them: a probe's section field records
    # WHERE the figure is asserted, so leaving these pointing at `sensitivity` would report
    # their cells as unmapped there and as unprobed here — the overlap failure twice over.
    "appf_tail": ("**What follows for the paper, and what was done.**",
                  "### F7 — Error budget, spent against each finding"),
    "appf_budget": ("### F7 — Error budget, spent against each finding",
                    "### F8 — How far the linkage reaches, and what it does not"),
    # F8 was retitled when the strict-key match-rate table moved into it: the section now
    # covers how far the linkage reaches as well as what it misses. A section anchor is matched
    # literally, so retitling a heading silently unmoors every probe scoped to it — twelve of
    # them here, all reporting "SECTION NOT FOUND" rather than a wrong figure.
    "appf_reach": ("### F8 — How far the linkage reaches, and what it does not",
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
    # ------------------------------------------------------------------
    # FULL-PAPER COVERAGE, 2026-08-14. These eleven slices close every gap between the
    # slices above, so the audit now partitions the paper from title to the last
    # reference — the WA paper's standard. The census that drove this found two live
    # defects INSIDE the gaps (Appendix C's all-tier $379.5M and Appendix E's stale 36.0),
    # which is the whole argument for partitioning rather than slicing the parts one
    # thought of.
    "frontmatter": ("# Who Gives?", "## Abstract"),
    "question": ("## The question", "## Prior work, and what this paper adds"),
    "f1_intro": ("## Finding 1 —", "**New York** (`match_ny_voters_to_donors.py`)"),
    "limits_head": ("## What this paper does not claim",
                    "- **Itemized giving only — but the panels are not truncated"),
    "limits_mid": ("- **Panel comparisons are descriptive",
                   "**Recipient party is partial, differentially missing"),
    "limits_tail": ("- **No policy-influence claim.**", "## What it means"),
    "meaning": ("## What it means", "# Appendices"),
    "appc_nystate": ("**The New York state panel.**", "**The match key and its four tiers.**"),
    "appe_statewide": ("**Statewide (all itemized donors",
                       "**Candidate money versus total flow.**"),
    "datacode": ("## Data, code, and reproduction", "## References"),
    "references": ("## References", "must replace this branch reference before submission."),
}

# ------------------------------------------------------------------------- probes
# (label, section or None for the whole paper, regex, derived key(s), tolerance)
# Bold markers are written `\*{0,2}` so re-bolding a figure does not disarm a probe;
# the anchor is the surrounding WORDS.
PROBES = [
    # --- Finding 2's geographic-selection check, added 2026-08-11 after external review.
    # Every cell of the table is probed: it is the paper's answer to the sharpest objection
    # available against a geographic finding computed on matched donors, so an unchecked cell
    # here would be an unchecked defence. The two prose restatements are probed separately,
    # because a table and its summary are exactly where a summary drifts.
    ("Finding 2 geo-selection — WA federal King", "f2_tail",
     r"\| WA federal · King \| ([\d.]+) \| ([\d.]+) \| (-[\d.]+) \|",
     ("wa_fed_gs_king_m", "wa_fed_gs_king_a", "wa_fed_gs_king_d"), 0.005),
    ("Finding 2 geo-selection — NY federal Manhattan", "f2_tail",
     r"\| NY federal · New York \| \*\*([\d.]+)\*\* \| \*\*([\d.]+)\*\* \| (-[\d.]+) \|",
     ("ny_fed_gs_newyork_m", "ny_fed_gs_newyork_a", "ny_fed_gs_newyork_d"), 0.005),
    ("Finding 2 geo-selection — NY federal Westchester", "f2_tail",
     r"\| NY federal · Westchester \| ([\d.]+) \| ([\d.]+) \| (\+[\d.]+) \|",
     ("ny_fed_gs_westchester_m", "ny_fed_gs_westchester_a", "ny_fed_gs_westchester_d"), 0.005),
    ("Finding 2 geo-selection — NY state Manhattan", "f2_tail",
     r"\| NY state · New York \| ([\d.]+) \| ([\d.]+) \| (-[\d.]+) \|",
     ("ny_state_gs_newyork_m", "ny_state_gs_newyork_a", "ny_state_gs_newyork_d"), 0.005),
    ("Finding 2 geo-selection — ID federal Ada", "f2_tail",
     r"\| ID federal · Ada \| ([\d.]+) \| ([\d.]+) \| (\+[\d.]+) \|",
     ("id_fed_gs_ada_m", "id_fed_gs_ada_a", "id_fed_gs_ada_d"), 0.005),
    ("Finding 2 geo-selection — ID federal Blaine", "f2_tail",
     r"\| ID federal · Blaine \| \*\*([\d.]+)\*\* \| \*\*([\d.]+)\*\* \| (-[\d.]+) \|",
     ("id_fed_gs_blaine_m", "id_fed_gs_blaine_a", "id_fed_gs_blaine_d"), 0.005),
    ("Finding 2 geo-selection — ID state Blaine", "f2_tail",
     r"\| ID state · Blaine \| ([\d.]+) \| ([\d.]+) \| (-[\d.]+) \|",
     ("id_state_gs_blaine_m", "id_state_gs_blaine_a", "id_state_gs_blaine_d"), 0.005),
    ("Finding 2 geo-selection — the Manhattan pair restated in prose", "f2_tail",
     r"Manhattan's federal multiplier is ([\d.]+)× on matched donors and ([\d.]+)× across all",
     ("ny_fed_gs_newyork_m", "ny_fed_gs_newyork_a"), 0.005),
    ("Finding 2 geo-selection — Bonneville's movement, quoted in prose", "f2_tail",
     r"Westchester \(\+([\d.]+)\) and Bonneville \(\+([\d.]+)\)",
     ("ny_fed_gs_westchester_d", "id_fed_gs_bonneville_d"), 0.005),
    ("Finding 2 geo-selection — WA state's reconstruction against the published rate", "f2_tail",
     r"reconstruct\*\* — ([\d.]+)% of in-state dollars against the published ([\d.]+)%",
     ("wa_state_gs_rate", "mr_wa_state_cov"), 0.05),
    ("Finding 2 geo-selection — the ZIP5 purity range across panels", "f2_tail",
     r"covers ([\d.]+)–([\d.]+)% of registrants in their own ZIP",
     ("gs_purity_lo", "gs_purity_hi"), 0.05),
    ("Finding 2 geo-selection — the ID state Blaine basis gap", "f2_tail",
     r"reads \*\*([\d.]+)\*\* here against \*\*([\d.]+)\*\* above",
     ("id_state_gs_blaine_m", "cty_id_state_blaine_mult"), 0.005),
    ("Finding 2 geo-selection — that gap stated as a number", "f2_tail",
     r"check relies on being small\. It is ([\d.]+)\.", "gs_blaine_basis_gap", 0.005),
    ("Finding 2 geo-selection — the largest movement, quoted in prose", "f2_tail",
     r"the largest county multiplier movement is ([\d.]+)\.", "gs_worst_move", 0.005),
    ("Finding 2 geo-selection — the reconstruction tolerance", "f2_tail",
     r"Five panels reconstruct to within ([\d.]+) points", "gs_recon_worst", 0.05),
    ("Finding 2 geo-selection — the Blaine pair restated in prose", "f2_tail",
     r"Blaine's is ([\d.]+)× against ([\d.]+)×",
     ("id_fed_gs_blaine_m", "id_fed_gs_blaine_a"), 0.005),

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

    # --- The registration baselines themselves. The "Three populations" paragraph is where
    # the paper says what its comparison baseline IS, and it printed the ALL-RECORDS counts
    # for WA and NY while calling them active. Probed, not exempted, for that reason.
    ("Three populations, the three roll sizes", "methods",
     r"registration roll — Washington ([\d.]+)M, New York ([\d.]+)M, Idaho ([\d.]+)M",
     ("wa_active_m", "ny_roll_active_m", "id_roll_m"), 0.005),
    ("Appendix C, the pinned WA roll size", "appc_tail2",
     r"at \*\*([\d,]+)\*\* registrants", ("wa_pin_n",), 0),
    ("Three populations, the companion-paper crosswalk", "methods",
     r"read against a wider \*{0,2}([\d.]+)M\*{0,2} roll that retains \*{0,2}([\d,]+)\*{0,2}\s+"
     r"inactive registrants", ("wa_ldroll_m", "wa_ldroll_inactive"), 0.005),
    # Appendix A restates the WA senior multiplier as the thing a flat matchability gradient
    # cannot produce. It moved with the active-roll switch, so it is probed rather than left to
    # drift away from Finding 1's table.
    ("Appendix A WA senior multiplier restatement", "appa",
     r"cannot produce senior over-representation of ([\d.]+)×",
     ("wa_fed_mult_silent",), 0.05),
    # The crosswalk to the companion WA papers' wider roll. These are NOT the published
    # figures — the published ones are active-roll — so the probe asserts the crosswalk values
    # and would fail if someone re-swapped the two conventions.
    ("F4 WA ld-scope crosswalk", "f4",
     r"`voter_scores` roll including its \*{0,2}([\d,]+)\*{0,2} inactive registrants: inactive "
     r"registrants vote\s+less, so that convention depresses the non-donor rate to "
     r"\*{0,2}([\d.]+)%\*{0,2} federal and \*{0,2}([\d.]+)%\*{0,2} state\s+"
     r"and widens every Washington gap here by \*{0,2}([\d.]+)\*{0,2} points "
     r"\(\*{0,2}([\d.]+)\*{0,2} on the exact-eligibility",
     ("wa_ldroll_inactive", "wa_fed_super_n_ldscope", "wa_state_super_n_ldscope",
      "wa_fed_super_gap_delta", "wa_fed_egap_delta"), 0.05),
    # The panel-specific ceiling and the rows it breaks (review round 15). The whole point of
    # this block is that a pooled bound was being spent panel-by-panel, so both budgets and
    # every cell they produce are derived.
    ("D1 panel-specific ceiling, the assumption", "sensitivity",
     r"allocates \*{0,2}([\d]+)\*{0,2}\s+full-name records to each of the six panels\. Zero "
     r"detected\s+errors in \d+ bounds a \*?single panel's\*? error rate at \*{0,2}([\d.]+)%",
     ("val_t0_panel_n", "val_t0_panel_err_hi"), 0.05),
    ("D1 the Idaho draw restated in the budget prose", "sensitivity",
     r"an independent rater scored \*\*(\d+)\*\* fresh Idaho full-name records",
     ("idaho_n_total",), 0),
    ("D1 sensitivity table, panel-specific column", "appf_budget",
     r"\| WA federal \| [\d.]+ → \*{0,2}[\d.]+\*{0,2} \| → ([\d.]+) \|.*?"
     r"\| WA state \| [\d.]+ → \*{0,2}[\d.]+\*{0,2} \| → ([\d.]+) \|.*?"
     r"\| NY federal \| [\d.]+ → \*{0,2}[\d.]+\*{0,2} \| → ([\d.]+) \| [\d.]+ → "
     r"\*{0,2}[\d.]+\*{0,2} \| → ([\d.]+) \|.*?"
     r"\| NY state \| [\d.]+ → \*{0,2}[\d.]+\*{0,2} \| → ([\d.]+) \| [\d.]+ → "
     r"\*{0,2}[\d.]+\*{0,2} \| → ([\d.]+) \|.*?"
     r"\| ID federal \| [\d.]+ → \*{0,2}[\d.]+\*{0,2} \| → ([\d.]+) \| [\d.]+ → "
     r"\*{0,2}[\d.]+\*{0,2} \| → \*{0,2}([\d.]+)\*{0,2} \|.*?"
     r"\| ID state \| [\d.]+ → \*{0,2}[\d.]+\*{0,2} \| → ([\d.]+) \| [\d.]+ → "
     r"\*{0,2}[\d.]+\*{0,2} \| → \*{0,2}([\d.]+)\*{0,2} \|",
     ("sens_wa_fed_b65_pbd", "sens_wa_state_b65_pbd",
      "sens_ny_fed_b65_pbd", "sens_ny_fed_dem_pbd",
      "sens_ny_state_b65_pbd", "sens_ny_state_dem_pbd",
      "sens_id_fed_b65_pbd", "sens_id_fed_dem_pbd",
      "sens_id_state_b65_pbd", "sens_id_state_dem_pbd"), 0.05),
    ("D1 panel-specific prose, the rows that break", "sensitivity",
     r"read\s+([\d.]+)% against a roll of ([\d.]+)%, Idaho's ([\d.]+)% against ([\d.]+)%.*?"
     r"\*{0,2}([\d.]+)% falls to ([\d.]+)% against an ([\d.]+)% registration share",
     ("sens_ny_fed_b65_pbd", "ny_active_b65", "sens_id_fed_b65_pbd", "id_roll_b65",
      "sens_id_fed_dem", "sens_id_fed_dem_pbd", "id_fed_reg_DEM"), 0.05),
    ("F partial merges by tier", "appf_tail",
     r"([\d]+) on `STRICT_ZIP5`, ([\d]+) on `RELAXED_ZIP3_MID`, ([\d]+) on "
     r"`STRICT_ZIP5_MID`, and\s+\*{0,2}([\d]+) on `STRICT_ZIP5_FULL`",
     ("val_pm_t2", "val_pm_t3", "val_pm_t1", "val_pm_t0"), 0),
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
    ("D1 budget, both stated", "sensitivity",
     r"at the pooled ([\d.]+)% and again at the\s+panel-specific ([\d.]+)%",
     ("sens_budget_pct", "val_t0_panel_err_hi"), 0.05),
    ("D1 degenerate removal illustration", "appf_budget",
     r"reading ([\d.]+)% → ([\d.]+)% on Washington's federal panel",
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
    ("D3 different-ZIP range", "matchrate",
     r"ZIP5, accounts for \*\*([\d.]+)% to ([\d.]+)%\*\* of eligible resident keys",
     ("res_difzip_lo", "res_difzip_hi"), 0.05),
    ("D3 name-form range", "matchrate",
     r"account for a further \*\*([\d.]+)% to ([\d.]+)%\*\*", ("res_nameform_lo", "res_nameform_hi"),
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
    # --- added 2026-08-11 after external review ------------------------------------------
    ("AppC pooling overstatement, differenced", "appc_head",
     r"a ([\d.]+)-point overstatement against the higher panel",
     ("pool_overstate",), 0.05),
    ("Front-matter copy of the same overstatement", None,
     r"a ([\d.]+)-point overstatement against the higher of the two panels",
     ("pool_overstate",), 0.05),
    ("F7 panel-wide construction at the party-stratum bound", "appf_budget",
     r"fails decisively at the corrected bound\*\*: at ([\d.]+)% it\s*"
     r"takes Idaho's federal registered-Democrat share to \*\*([\d.]+)%\*\* and the state "
     r"panel to \*\*([\d.]+)%\*\*,\s*both far below the ([\d.]+)% registration baseline",
     ("idaho_bound_party_cell", "idaho_dem_panelwide_at_party_ceiling_fed",
      "idaho_dem_panelwide_at_party_ceiling_state", "id_fed_reg_DEM"), 0.05),
    ("F7 the panel-wide row it contrasts with", "appf_budget",
     r"Idaho's federal row falls to \*\*([\d.]+)%\*\* at a ([\d.]+)% budget",
     ("sens_id_fed_dem_pbd", "val_t0_panel_err_hi"), 0.05),
    ("F4 Idaho primary ballots against participants", "f4",
     r"Those five sum to\s+\*\*([\d,]+)\*\* against the ([\d,]+) in the table above",
     ("id_pri_party_ballots", "id_pri_participants"), 0),
    ("F4 the unrecorded-ballot bucket", "f4",
     r"The \*\*([\d,]+)\*\*-record difference is participants whose `ballot_choice` is blank",
     ("id_pri_no_ballot",), 0),
    ("AppF the primary tier's share of matches, restated in the two-stage note", "appf_weighted",
     r"The full-name key carries \*\*([\d.]+)–([\d.]+)%\*\* of matches",
     ("tier0_share_lo", "tier0_share_hi"), 0.05),

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
    # Replaced the retired 4.7%/4.1% surname-vocabulary heuristic in round 17. The name-order
    # mode is now MEASURED (_d_pdc_name_order) rather than estimated, and Appendix F's error-mode
    # section restates the measurement, so the restatement is probed rather than exempted.
    ("AppF name-order mode, superseding measurement restated", "appf_modes",
     r"finds \*\*([\d.]+)% of\s+comma-less resident keys\*\* affected, against a ([\d.]+)% "
     r"coincidence baseline",
     ("pdcno_rev_pct", "pdcno_placebo_pct"), 0.05),
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
    ("D1 structural, colliding-key share of roll", "appf_budget",
     r"are \*\*([\d.]+)%\*\* of Washington's active roll, \*\*([\d.]+)%\*\* of New "
     r"York's and \*\*([\d.]+)%\*\* of Idaho's",
     ("sens_wa_collide_pct", "sens_ny_collide_pct", "sens_id_collide_pct"), 0.05),
    ("D1 structural, household pool share", "appf_budget",
     r"is \*\*([\d.]+)%, ([\d.]+)% and ([\d.]+)%\*\* of those rolls",
     ("sens_wa_pool_pct", "sens_ny_pool_pct", "sens_id_pool_pct"), 0.05),
    # The pooled-budget cells. Concentration left this table in round 15 — it is a stylized
    # de-merge, not spent error budget — so it is probed separately below.
    ("D1 bound, WA rows", "appf_budget",
     r"\| WA federal \| ([\d.]+) → \*\*([\d.]+)\*\* \| → [\d.]+ \| \*party unpublished\*[\s\S]{0,60}?"
     r"\| WA state \| ([\d.]+) → \*\*([\d.]+)\*\* \| → [\d.]+ \| \*party unpublished\*",
     ("sens_wa_fed_b65", "sens_wa_fed_b65_bd",
      "sens_wa_state_b65", "sens_wa_state_b65_bd"), 0.05),
    ("D1 bound, NY rows", "appf_budget",
     r"\| NY federal \| ([\d.]+) → \*\*([\d.]+)\*\* \| → [\d.]+ \| ([\d.]+) → \*\*([\d.]+)\*\*"
     r"[\s\S]{0,60}?"
     r"\| NY state \| ([\d.]+) → \*\*([\d.]+)\*\* \| → [\d.]+ \| ([\d.]+) → \*\*([\d.]+)\*\*",
     ("sens_ny_fed_b65", "sens_ny_fed_b65_bd", "sens_ny_fed_dem", "sens_ny_fed_dem_bd",
      "sens_ny_state_b65", "sens_ny_state_b65_bd",
      "sens_ny_state_dem", "sens_ny_state_dem_bd"), 0.05),
    ("D1 bound, ID rows", "appf_budget",
     r"\| ID federal \| ([\d.]+) → \*\*([\d.]+)\*\* \| → [\d.]+ \| ([\d.]+) → \*\*([\d.]+)\*\*"
     r"[\s\S]{0,60}?"
     r"\| ID state \| ([\d.]+) → \*\*([\d.]+)\*\* \| → [\d.]+ \| ([\d.]+) → \*\*([\d.]+)\*\*",
     ("sens_id_fed_b65", "sens_id_fed_b65_bd", "sens_id_fed_dem", "sens_id_fed_dem_bd",
      "sens_id_state_b65", "sens_id_state_b65_bd",
      "sens_id_state_dem", "sens_id_state_dem_bd"), 0.05),
    ("D1 stylized de-merge table", "appf_budget",
     r"\| WA federal \| ([\d.]+) \| \*\*([\d.]+)\*\* \|\s*"
     r"\| WA state \| ([\d.]+) \| \*\*([\d.]+)\*\* \|\s*"
     r"\| NY federal \| ([\d.]+) \| \*\*([\d.]+)\*\* \|\s*"
     r"\| NY state \| ([\d.]+) \| \*\*([\d.]+)\*\* \|\s*"
     r"\| ID federal \| ([\d.]+) \| \*\*([\d.]+)\*\* \|\s*"
     r"\| ID state \| ([\d.]+) \| \*\*([\d.]+)\*\* \|",
     ("sens_wa_fed_top1", "sens_wa_fed_top1_bd",
      "sens_wa_state_top1", "sens_wa_state_top1_bd",
      "sens_ny_fed_top1", "sens_ny_fed_top1_bd",
      "sens_ny_state_top1", "sens_ny_state_top1_bd",
      "sens_id_fed_top1", "sens_id_fed_top1_bd",
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
    ("D3 cascade, WA federal", "appf_reach",
     r"\| WA federal \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \| ([\d.]+)% \|",
     ("res_wa_fed_matched", "res_wa_fed_guard", "res_wa_fed_inactive", "res_wa_fed_difzip", "res_wa_fed_nameform", "res_wa_fed_none"), 0.05),
    ("D3 cascade, WA state", "appf_reach",
     r"\| WA state \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \| ([\d.]+)% \|",
     ("res_wa_state_matched", "res_wa_state_guard", "res_wa_state_inactive", "res_wa_state_difzip", "res_wa_state_nameform", "res_wa_state_none"), 0.05),
    ("D3 cascade, NY federal", "appf_reach",
     r"\| NY federal \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \| ([\d.]+)% \|",
     ("res_ny_fed_matched", "res_ny_fed_guard", "res_ny_fed_inactive", "res_ny_fed_difzip", "res_ny_fed_nameform", "res_ny_fed_none"), 0.05),
    ("D3 cascade, NY state", "appf_reach",
     r"\| NY state \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \| ([\d.]+)% \|",
     ("res_ny_state_matched", "res_ny_state_guard", "res_ny_state_inactive", "res_ny_state_difzip", "res_ny_state_nameform", "res_ny_state_none"), 0.05),
    ("D3 cascade, ID federal", "appf_reach",
     r"\| ID federal \| ([\d.]+)% \| ([\d.]+)% \| — \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \| ([\d.]+)% \|",
     ("res_id_fed_matched", "res_id_fed_guard", "res_id_fed_difzip", "res_id_fed_nameform", "res_id_fed_none"), 0.05),
    ("D3 cascade, ID state", "appf_reach",
     r"\| ID state \| ([\d.]+)% \| ([\d.]+)% \| — \| \*\*([\d.]+)%\*\* \| ([\d.]+)% \| ([\d.]+)% \|",
     ("res_id_state_matched", "res_id_state_guard", "res_id_state_difzip", "res_id_state_nameform", "res_id_state_none"), 0.05),
    # --- the match-rate tables. Every cell asserted; the recall figures are the
    # paper's answer to "how big is the floor" and had no derivation before today.
    ("Match rate, WA federal", "appf_reach",
     r"\| WA federal \| ([\d,]+) \| ([\d,]+) \| \*\*([\d.]+)%\*\* \| \$([\d,.]+)M \| \$([\d,.]+)M \| \*\*([\d.]+)%\*\* \|",
     ("mr_wa_fed_ids", "mr_wa_fed_matched", "mr_wa_fed_recall", "mr_wa_fed_amt_m",
      "mr_wa_fed_matched_m", "mr_wa_fed_cov"), 0.05),
    ("Match rate, WA state", "appf_reach",
     r"\| WA state \| ([\d,]+) \| ([\d,]+) \| \*\*([\d.]+)%\*\* \| \$([\d,.]+)M \| \$([\d,.]+)M \| \*\*([\d.]+)%\*\* \|",
     ("mr_wa_state_ids", "mr_wa_state_matched", "mr_wa_state_recall", "mr_wa_state_amt_m",
      "mr_wa_state_matched_m", "mr_wa_state_cov"), 0.05),
    ("Match rate, NY federal", "appf_reach",
     r"\| NY federal \| ([\d,]+) \| ([\d,]+) \| \*\*([\d.]+)%\*\* \| \$([\d,.]+)M \| \$([\d,.]+)M \| \*\*([\d.]+)%\*\* \|",
     ("mr_ny_fed_ids", "mr_ny_fed_matched", "mr_ny_fed_recall", "mr_ny_fed_amt_m",
      "mr_ny_fed_matched_m", "mr_ny_fed_cov"), 0.05),
    ("Match rate, NY state", "appf_reach",
     r"\| NY state \| ([\d,]+) \| ([\d,]+) \| \*\*([\d.]+)%\*\* \| \$([\d,.]+)M \| \$([\d,.]+)M \| \*\*([\d.]+)%\*\* \|",
     ("mr_ny_state_ids", "mr_ny_state_matched", "mr_ny_state_recall", "mr_ny_state_amt_m",
      "mr_ny_state_matched_m", "mr_ny_state_cov"), 0.05),
    ("Match rate, ID federal", "appf_reach",
     r"\| ID federal \| ([\d,]+) \| ([\d,]+) \| \*\*([\d.]+)%\*\* \| \$([\d,.]+)M \| \$([\d,.]+)M \| \*\*([\d.]+)%\*\* \|",
     ("mr_id_fed_ids", "mr_id_fed_matched", "mr_id_fed_recall", "mr_id_fed_amt_m",
      "mr_id_fed_matched_m", "mr_id_fed_cov"), 0.05),
    ("Match rate, ID state", "appf_reach",
     r"\| ID state \| ([\d,]+) \| ([\d,]+) \| \*\*([\d.]+)%\*\* \| \$([\d,.]+)M \| \$([\d,.]+)M \| \*\*([\d.]+)%\*\* \|",
     ("mr_id_state_ids", "mr_id_state_matched", "mr_id_state_recall", "mr_id_state_amt_m",
      "mr_id_state_matched_m", "mr_id_state_cov"), 0.05),
    ("Methods, recall range restated in the confound list", "methods",
     r"reaches the panels unequally\*\*, from ([\d.]+)% to ([\d.]+)% of parsed resident",
     ("_mr_recall_lo", "_mr_recall_hi"), 0.05),
    ("Match rate, out-of-state shares by layer", "appf_reach",
     r"NYSBOE layer is \*\*([\d.]+)%\*\* out-of-state, WA PDC ([\d.]+)% and Idaho "
     r"Sunshine ([\d.]+)%",
     ("mr_ny_state_outstate_pct", "mr_wa_state_outstate_pct",
      "mr_id_state_outstate_pct"), 0.05),
    ("Match rate, PDC comma-less name share", "matchrate",
     r"The PDC files \*\*([\d.]+)%\*\* of its contributor names",
     ("mr_wa_state_nocomma_pct",), 0.05),
    # --- the WA PDC name-order measurement, round 17. Body statement then F8 table. ---
    ("PDC name order, body statement", "matchrate",
     r"\*\*([\d.]+)%\*\* of comma-less PDC keys — ([\d,]+) of \*\*([\d,]+)\*\*, carrying\s*"
     r"\*\*([\d.]+)%\*\* of their dollars\s*\n?\(\$([\d.]+)M\) —",
     ("pdcno_rev_pct", "pdcno_rev_only", "pdcno_keys", "pdcno_rev_dollar_pct",
      "pdcno_rev_dollars_m"), 0.05),
    ("PDC name order, placebo and reach", "matchrate",
     r"\*\*([\d.]+)%\*\* coincidence baseline[\s\S]{0,200}?strict-key match rate from "
     r"\*\*([\d.]+)%\*\* to\s*\*\*([\d.]+)%\*\*",
     ("pdcno_placebo_pct", "pdcno_fwd_pct", "pdcno_reach_either"), 0.05),
    ("PDC name order, age direction", "matchrate",
     r"\(([\d.]+)% aged 65\+ against ([\d.]+)%\)[\s\S]{0,120}?"
     r"from ([\d.]+)% to \*\*([\d.]+)%\*\*",
     ("pdcno_recoverable_b65", "pdcno_matched_b65", "pdcno_matched_b65",
      "pdcno_repaired_b65"), 0.05),
    # Restatements. Probed rather than exempted: each repeats a figure the probes above
    # already assert, and a restatement drifting from its table is the exact defect the
    # 2026-07-27 tier switch left behind in seven places.
    ("PDC name order, decision restated", "matchrate",
     r"would add ([\d,]+) matches drawn from a population[\s\S]{0,120}?the ([\d.]+)% placebo",
     ("pdcno_rev_only", "pdcno_placebo_pct"), 0.05),
    ("PDC name order, understatement restated", "matchrate",
     r"match rate understated by about ([\d.]+) points", ("pdcno_rev_pct",), 0.05),
    ("PDC name order, F8 excess", "appf_reach",
     r"The observed ([\d.]+)% therefore exceeds the coincidence rate by ([\d.]+) points",
     ("pdcno_rev_pct", "pdcno_excess_pts"), 0.05),
    ("F7 Idaho sample, stratum table", "appf_budget",
     r"\| one party × dollar-band cell, one panel — \*\*the operative bound\*\* \| (\d+) \| "
     r"\*\*([\d.]+)%\*\* \|\s*"
     r"\| one registered party, one panel — \*retired: pools its two dollar-band cells\* \| "
     r"(\d+) \| ([\d.]+)% \|\s*"
     r"\| one dollar band, one panel \| (\d+) \| ([\d.]+)% \|\s*"
     r"\| one panel, composition-reweighted \| (\d+) \| ([\d.]+)% [^|]*\|\s*"
     r"\| \*what the current evidence supports\* \| \*(\d+)\* \| \*([\d.]+)%\* \|",
     ("idaho_n_party_cell", "idaho_bound_party_cell",
      "idaho_n_party_panel", "idaho_bound_party_panel",
      "idaho_n_band_panel", "idaho_bound_band_panel",
      "idaho_n_panel", "idaho_bound_panel_pooled",
      "val_t0_panel_n", "idaho_bound_current"), 0.05),
    # The design-correction paragraph, 2026-08-14 (external referee, publication blocker).
    # Every figure it argues from is tied back to the draw's design constants and the two
    # corrected constructions, so the correction cannot drift from the bound it installs.
    ("F7 correction, the pooled n it retires", "appf_budget",
     r"bounded each party stratum at its pooled n = (\d+) anyway",
     ("idaho_n_party_panel",), 0),
    ("F7 correction, the cell decomposition", "appf_budget",
     r"two deliberately balanced dollar-band cells of \*\*(\d+)\*\*",
     ("idaho_n_party_cell",), 0),
    ("F7 correction, the over-weighting arithmetic", "appf_budget",
     r"the (\d+) records over-weight the top decile about five-fold, so an\s*"
     r"n = (\d+) binomial bound is not a bound",
     ("idaho_n_party_panel", "idaho_n_party_panel"), 0),
    ("F7 correction, the refused pool", "appf_budget",
     r"the plan refused to pool the (\d+)", ("idaho_n_panel",), 0),
    ("F7 correction, the two corrected bounds", "appf_budget",
     r"equals the cell bound, \*\*([\d.]+)%\*\*; a conservative simultaneous construction\s*"
     r"\(each cell at ([\d.]+)%\) gives \*\*([\d.]+)%\*\*",
     ("idaho_bound_party_cell", "idaho_simul_cell_conf",
      "idaho_bound_party_cell_simul"), 0.05),
    ("F7 Idaho sample, Democratic-stratum worst case", "appf_budget",
     r"federal panel from ([\d.]+)% to\s*\*\*([\d.]+)%\*\* and its state panel from ([\d.]+)% "
     r"to \*\*([\d.]+)%\*\* at the ([\d.]+)% bound — and to \*\*([\d.]+)%\*\* and\s*"
     r"\*\*([\d.]+)%\*\* at the simultaneous ([\d.]+)% — all still well above the ([\d.]+)%\s*"
     r"registration share",
     ("sens_id_fed_dem", "idaho_dem_after_stratum_fed", "sens_id_state_dem",
      "idaho_dem_after_stratum_state", "idaho_bound_party_cell",
      "idaho_dem_after_simul_fed", "idaho_dem_after_simul_state",
      "idaho_bound_party_cell_simul", "id_fed_reg_DEM"), 0.05),
    ("F7 correction, the earlier printed deletion", "appf_budget",
     r"\(An earlier version printed ([\d.]+)% and ([\d.]+)% here: the same deletion at the\s*"
     r"retired ([\d.]+)% pooled bound\.\)",
     ("idaho_dem_after_retired_fed", "idaho_dem_after_retired_state",
      "idaho_bound_party_panel"), 0.05),
    ("F7 Idaho sample, total drawn", "appf_budget",
     r"\*\*(\d+) records, \d+ per panel\*\*", ("idaho_n_total",), 0),
    # The zero-error result, 2026-08-06. These three are RESTATEMENTS in the prose that reports
    # the rating, pointed at the same derived keys as the table and the deletion exercise above
    # — which is the whole reason to probe them: a paragraph that restates a bound while
    # announcing a result is exactly where the restated bound drifts from the bound.
    ("F7 Idaho rated, worst-case figures restated", "appf_budget",
     r"worst-case Idaho figures of \*\*([\d.]+)%\*\* federal and \*\*([\d.]+)%\*\* state",
     ("idaho_dem_after_stratum_fed", "idaho_dem_after_stratum_state"), 0.05),
    ("F7 Idaho rated, cell bound restated", "appf_budget",
     r"95% upper validation\s*bound of ([\d.]+)% per party × dollar-band cell",
     ("idaho_bound_party_cell",), 0.05),
    ("F7 Idaho rated, cell n restated", "appf_budget",
     r"A\s*sample of (\d+) per cell cannot\s*establish that",
     ("idaho_n_party_cell",), 0),
    # --- the independent rater's pass, 2026-08-06 ----------------------------------------
    # Section None: this block sits in `appf_tail`, which the coverage audit exempts for its
    # ceiling analysis and survivorship note. Rather than widen that exemption to cover ten
    # result figures — which would have made its written reason false — the figures are derived
    # from the committed PII-free ledger by _d_rater2 and asserted here.
    ("Appendix F inter-rater, full-name block both passes", None,
     r"full-name block \| \*\*(\d+)/(\d+) Y in both\*\*",
     ("r2_full_y_rater2", "r2_full_n"), 0),
    ("Appendix F inter-rater, full-name block in prose", None,
     r"full-name block is (\d+)/(\d+) Y in both the first pass",
     ("r2_full_y_rater2", "r2_full_n"), 0),
    ("Appendix F inter-rater, four-category agreement", None,
     r"all four verdicts \| ([\d.]+)% observed", ("r2_obs4",), 0.05),
    # Split by PRINTED PRECISION, not for convenience: the observed share is printed to one
    # decimal (half-width 0.05) and the two coefficients to three (half-width 0.0005). One
    # tolerance covering both would have to be the looser of the two, which is how a tolerance
    # stops discriminating between a rounding difference and a defect.
    ("Appendix F inter-rater, binary observed agreement", None,
     r"same/different \| \*\*([\d.]+)% observed", ("r2_obs_binary",), 0.05),
    ("Appendix F inter-rater, binary coefficients", None,
     r"observed, κ ([\d.]+)\*\*, PABAK ([\d.]+)",
     ("r2_kappa_binary", "r2_pabak_binary"), 0.0005),
    ("Appendix F inter-rater, four-category kappa restated", None,
     r"four-category κ of ([\d.]+) and", ("_r2_kappa4",), 0.0005),
    ("Appendix F inter-rater, binary kappa restated", None,
     r"the binary κ of ([\d.]+) are not in tension", ("r2_kappa_binary",), 0.0005),
    ("Appendix F inter-rater, U counts each pass", None,
     r"used `U` on \*\*(\d+)\*\* records against the first pass's \*\*(\d+)\*\*",
     ("r2_u_rater2", "r2_u_pass1"), 0),
    ("Appendix F inter-rater, disagreement direction", None,
     r"of the \*\*(\d+)\*\* disagreements\s*\*\*(\d+) move toward less certainty\*\*",
     ("r2_disagree", "r2_toward_less_certain"), 0),
    ("Appendix F inter-rater, the 34-of-36 restatement", None,
     r"one-sided across (\d+) of (\d+) cases",
     ("r2_toward_less_certain", "r2_disagree"), 0),
    # The limitations bullet restating the parser measurement. Section `None`: the bullet sits
    # in a gap between the two audited limitations slices, so recording a span would put it in
    # the wrong section's coordinates. The figures are still asserted, which is the point —
    # three retired rates survived in exactly this bullet list until round 13 found them.
    ("PDC name order, limitations bullet", None,
     r"\*\*([\d.]+)%\*\* of comma-less resident keys and \*\*([\d.]+)%\*\* of their dollars"
     r"[\s\S]{0,200}?\*\*([\d.]+)%\*\* coincidence baseline \(Appendix F §F8\)",
     ("pdcno_rev_pct", "pdcno_rev_dollar_pct", "pdcno_placebo_pct"), 0.05),
    # --- submission-package restatements (2026-08-01) -------------------------------
    # Each of these repeats a paper figure in a document the verifier did not read until now.
    # The memo's uniqueness-guard range was stale when this was written — it still carried the
    # pre-resident-basis 1.1-2.3% against the paper's 1.3-2.7% — and no existing check could
    # see it, because both endpoints appear elsewhere in the paper for other reasons.
    ("Memo: strict-key match rate and dollar coverage", None,
     r"match rate is ([\d.]+)[–-]([\d.]+)% of resident parsed contributor keys, with "
     r"([\d.]+)[–-]([\d.]+)% of resident",
     ("_mr_recall_lo", "_mr_recall_hi", "_mr_cov_lo", "_mr_cov_hi"), 0.05),
    ("Memo: uniqueness-guard range", None,
     r"uniqueness guard costs only ([\d.]+)[–-]([\d.]+)% of eligible resident keys",
     ("res_guard_lo", "res_guard_hi"), 0.05),
    ("Memo: adversarial movement ranges", None,
     r"moves age by\s*([\d.]+)[–-]([\d.]+) points and party by ([\d.]+)[–-]([\d.]+)",
     ("sens_move_b65_lo", "sens_move_b65_hi", "sens_move_dem_lo", "sens_move_dem_hi"), 0.05),
    ("Metadata: headline age shares", None,
     r"([\d.]+)% of New York's federal donors and ([\d.]+)% of Idaho's are 65",
     ("ny_fed_b65", "id_fed_b65"), 0.05),
    ("Metadata: headline top-1% shares", None,
     r"top 1% of matched donors supplying ([\d.]+)% of federal dollars in Washington, "
     r"([\d.]+)% in New York, and ([\d.]+)% in Idaho",
     ("wa_fed_top1", "ny_fed_top1", "id_fed_top1"), 0.05),
    ("Metadata: weak-tier precision range", None,
     r"against ([\d.]+)[–-]([\d.]+)% on the initial-based",
     ("val_t2_prec", "val_t1_prec"), 0.05),
    ("PDC denominators reconcile, body", "matchrate",
     r"match-rate table in Appendix F §F8 counts \*\*([\d,]+)\*\* eligible\s*resident keys in this layer; "
     r"this diagnostic counts \*\*([\d,]+)\*\*[\s\S]{0,120}?(\d+) keys arise from them, (\d+) of "
     r"which are also reachable from a comma-less\s*row, and ([\d,]+) \+ (\d+) − (\d+) = ([\d,]+)",
     ("mr_wa_state_ids", "pdcno_keys", "pdcno_comma_keys", "pdcno_both_form_keys",
      "pdcno_keys", "pdcno_comma_keys", "pdcno_both_form_keys", "mr_wa_state_ids"), 0.05),
    ("PDC denominators reconcile, F8", "appf_reach",
     r"\*The ([\d,]+) keys here and the ([\d,]+) in the match-rate table[\s\S]{0,140}?"
     r"(\d+) keys arise from comma-bearing rows, (\d+) of those[\s\S]{0,80}?"
     r"([\d,]+) \+ (\d+) − (\d+) = ([\d,]+)",
     ("pdcno_keys", "mr_wa_state_ids", "pdcno_comma_keys", "pdcno_both_form_keys",
      "pdcno_keys", "pdcno_comma_keys", "pdcno_both_form_keys", "mr_wa_state_ids"), 0.05),
    ("PDC name order, F8 table", "appf_reach",
     r"\| comma-less rows, of all PDC person rows \| ([\d,]+) \| \*\*([\d.]+)%\*\* \|\s*"
     r"\| distinct resident keys \| ([\d,]+) \| \|\s*"
     r"\| resolve forward only \(matched today\) \| ([\d,]+) \| \*\*([\d.]+)%\*\* \|\s*"
     r"\| resolve reversed only \| ([\d,]+) \| \*\*([\d.]+)%\*\* \|\s*"
     r"\| resolve both \(ambiguous\) \| ([\d,]+) \| ([\d.]+)% \|\s*"
     r"\| resolve neither \| ([\d,]+) \|",
     ("pdcno_nocomma_n", "pdcno_nocomma_pct", "pdcno_keys", "pdcno_fwd_only",
      "pdcno_fwd_pct", "pdcno_rev_only", "pdcno_rev_pct", "pdcno_both", "pdcno_both_pct",
      "pdcno_neither"), 0.05),
    ("PDC name order, F8 dollars and placebo", "appf_reach",
     r"reversed-only keys are \*\*\$([\d.]+)M\*\*, \*\*([\d.]+)%\*\*[\s\S]{0,400}?"
     r"([\d,]+) keys against the panel's ([\d,]+) matched donors, and a 65\+ share of "
     r"([\d.]+)% against the published ([\d.]+)%[\s\S]{0,300}?"
     r"only \*\*([\d.]+)%\*\*\s*of keys \(([\d,]+) of ([\d,]+)\)",
     ("pdcno_rev_dollars_m", "pdcno_rev_dollar_pct", "pdcno_fwd_only", "wa_state_n",
      "pdcno_matched_b65", "wa_state_b65", "pdcno_placebo_pct", "pdcno_placebo_swap_n",
      "pdcno_placebo_keys"), 0.05),
    ("Match rate, prose ranges", "matchrate",
     r"resolve \*\*([\d.]+)[–-]([\d.]+)%\*\* of resident contributor keys, and "
     r"\*\*([\d.]+)[–-]([\d.]+)%\*\*",
     ("_mr_recall_lo", "_mr_recall_hi", "_mr_cov_lo", "_mr_cov_hi"), 0.05),
    ("Guard cost, prose range", "matchrate",
     r"uniqueness guard costs ([\d.]+)[–-]([\d.]+)%\*\* of eligible resident keys",
     ("res_guard_lo", "res_guard_hi"), 0.05),
    ("D3 inactive range, prose", "matchrate",
     r"A further \*\*([\d.]+)[–-]([\d.]+)%\*\* match a registrant whose status is not",
     ("res_inactive_lo", "res_inactive_hi"), 0.05),
    # --- the methods section. Mostly restatement, asserted so it cannot drift. ---
    ("Methods, pooled vs panel top-1%", "methods",
     r"top-1% reads ([\d.]+)% pooled\s*against ([\d.]+)% federal and ([\d.]+)% state",
     ("wa_pooled_top1", "wa_fed_top1", "wa_state_top1"), 0.05),
    ("Methods, WA vote records", "methods",
     r"([\d.]+)M individual vote records", ("wa_vote_records_m",), 0.05),
    # --- The abstract, sliced and audited 2026-08-14 (Pass 2). Section-scoped, because a
    # probe that matches but is not attributed to a section proves nothing to the audit.
    ("abstract top-1% by state", "abstract",
     r"top 1% of donors suppl(?:y|ying) ([\d.]+)% of\s+federal dollars in Washington, "
     r"([\d.]+)% in New York and ([\d.]+)% in Idaho",
     ("wa_fed_top1", "ny_fed_top1", "id_fed_top1"), 0.05),
    ("abstract, donor vs roll 65+", "abstract",
     r"([\d.]+)% of New York's federal donors and ([\d.]+)% of\s+Idaho's are 65 or older, "
     r"against ([\d.]+)% and ([\d.]+)% of registrants",
     ("ny_fed_b65", "id_fed_b65", "ny_active_b65", "id_roll_b65"), 0.05),
    # The anchor names the CELL, not the "party stratum". Until 2026-08-17 the abstract said
    # "18.4% per party stratum" and this probe's anchor embedded that phrase — so the gate
    # asserted the right number under the label §F7 retires (the pooled n=34 party stratum is
    # 10.2%). A regex that quotes a mislabel cannot catch it; the anchor is the claim.
    ("abstract, the Idaho design-respecting cell bound", "abstract",
     r"an independent (\d+)-record rating detected no false\s+match,\s*"
     r"95% upper bound ([\d.]+)% per party × dollar-band cell",
     ("idaho_n_total", "idaho_bound_party_cell"), 0.05),
    # Integer restatement of F4's unrounded 22.89-26.28 span, so tol 0.5.
    ("abstract, eligible-for-all turnout gap span", "abstract",
     r"in New York and Washington, by (\d+) to (\d+)\s+points among registrants "
     r"eligible for every election in the window",
     ("abs_egap_lo", "abs_egap_hi"), 0.5),

    # --- Full-paper coverage, 2026-08-14: the front matter's two-panels block. Every
    # figure here restates one asserted deeper in the paper, which is exactly why it is
    # probed rather than trusted — a restatement is where the tier switch's stale copies
    # survived.
    ("front matter, disclosure — the Idaho sample size", "frontmatter",
     r"an independent\s+rater's on the third pass and the (\d+)-record Idaho sample",
     ("idaho_n_total",), 0),
    ("front matter, panel table — federal row", "frontmatter",
     r"\| \*\*Federal\*\* \*\(primary\)\* \| FEC itemized individual contributions \| "
     r"WA ([\d,]+) · NY ([\d,]+) · ID ([\d,]+) \|",
     ("wa_fed_n", "ny_fed_n", "id_fed_n"), 0),
    ("front matter, panel table — state row", "frontmatter",
     r"\| \*\*State\*\* \*\(secondary\)\* \| [^|]+ \| WA ([\d,]+) · NY ([\d,]+) · "
     r"ID ([\d,]+) \|",
     ("wa_state_n", "ny_state_n", "id_state_n"), 0),
    ("front matter — the pooling demonstration", "frontmatter",
     r"pooling reads top-1% \*\*([\d.]+)%\*\* against \*\*([\d.]+)%\*\*\s+federal and "
     r"\*\*([\d.]+)%\*\* state — a ([\d.]+)-point overstatement",
     ("wa_pooled_top1", "wa_fed_top1", "wa_state_top1", "pool_overstate"), 0.05),
    ("front matter — the retired all-tier trio, labelled", "frontmatter",
     r"the retired all-tier trio \(([\d.]+) / ([\d.]+) /\s+([\d.]+)\)",
     ("wa_pooled_alltier_top1", "wa_fed_alltier_top1", "wa_state_alltier_top1"), 0.05),
    ("front matter — the Jaccard overlap span", "frontmatter",
     r"overlap by a Jaccard coefficient of only ([\d.]+)–([\d.]+) in all three states",
     ("jaccard_lo", "jaccard_hi"), 0.005),
    ("front matter — the operational match-rate span", "frontmatter",
     r"resolving ([\d.]+)% to ([\d.]+)% of resident contributor keys",
     ("_mr_recall_lo", "_mr_recall_hi"), 0.05),
    ("front matter — federal money is older money, all four cells", "frontmatter",
     r"federal donors are ([\d.]+)% over 65 against ([\d.]+)% of its state donors, "
     r"Idaho's ([\d.]+)% against\s+([\d.]+)%",
     ("ny_fed_b65", "ny_state_b65", "id_fed_b65", "id_state_b65"), 0.05),
    ("front matter — WA Silent multipliers, both panels", "frontmatter",
     r"Silent Generation multiplier runs ([\d.]+)× federal against ([\d.]+)× state",
     ("wa_fed_mult_silent", "wa_state_mult_silent"), 0.005),
    ("front matter — the aligned-window widening", "frontmatter",
     r"widens\*\* the gap to ([\d.]+)% against ([\d.]+)%",
     ("id_fedal_b65", "id_state_b65"), 0.05),

    # --- "The question": restates the Idaho bound the abstract states.
    ("question — the Idaho per-stratum bound restated", "question",
     r"independent rating\*\* — (\d+) records, no false match detected, 95% upper bound "
     r"([\d.]+)% at the\s+design's party × dollar-band cells",
     ("idaho_n_total", "idaho_bound_party_cell"), 0.05),

    # --- The limits bullets brought under audit.
    ("limits — full-name key rating, restated", "limits_head",
     r"no detectable false match\*\* there\s+\(120/120, Wilson \[([\d.]+)–100\]\) against "
     r"\*\*([\d.]+)–([\d.]+)%\*\* on the three initial-based keys",
     ("val_t0_lo", "val_t2_prec", "val_t1_prec"), 0.05),
    ("limits — all-tier weighted precision and the decile pair", "limits_head",
     r"population-weighted precision was \*\*([\d.]+)%\*\*, and precision was \*lower\* in "
     r"the top dollar\s+decile \(([\d.]+)% vs ([\d.]+)% raw\)",
     ("val_wprec_all", "val_band_top", "val_band_rest"), 0.05),
    ("limits — the Jaccard span restated", "limits_mid",
     r"overlap by a Jaccard coefficient of ([\d.]+)–([\d.]+)",
     ("jaccard_lo", "jaccard_hi"), 0.005),
    ("limits — the match-reach span restated", "limits_mid",
     r"from ([\d.]+)% to ([\d.]+)% of resident contributor keys",
     ("_mr_recall_lo", "_mr_recall_hi"), 0.05),
    ("limits — Idaho state reach vs aligned federal", "limits_mid",
     r"state panel reaches ([\d,]+) against\s+the\s+federal panel's ([\d,]+) — (\d+)% more",
     ("id_state_n", "id_fedal_n", "id_state_reach_gain_pct"), 0.5),
    ("limits — the WA state-panel parser mode, three figures", "limits_mid",
     r"\*\*([\d.]+)%\*\* of comma-less resident keys and \*\*([\d.]+)%\*\* of their dollars"
     r"[^.]*?against a\s+\*\*([\d.]+)%\*\* coincidence baseline",
     ("pdcno_rev_pct", "pdcno_rev_dollar_pct", "pdcno_placebo_pct"), 0.05),

    # --- Appendix C's New York state-panel paragraph.
    ("Appendix C, NY state panel — the feed and both match totals", "appc_nystate",
     r"gives ([\d,]+) contributions totalling \$([\d.]+)M, of which\s+\$([\d.]+)M matches "
     r"to a registered New York voter on the primary match\s+specification "
     r"\(\$([\d.]+)M on the retired all-tier key\)",
     ("ny_feed_rows", "ny_feed_m", "ny_state_m", "ny_state_alltier_m"), 0.05),
    ("Appendix C, NY state panel — the no-prefix residue", "appc_nystate",
     r"A further ([\d,]+) rows \(\$([\d.]+)M\) in the NY contribution table carry no source",
     ("ny_noprefix_rows", "ny_noprefix_m"), 0.05),

    # --- Appendix E's statewide four-state table: the same quantity
    # verify_cross_state_money.py asserts in ITS paper, derived here on the same proxy so
    # the two papers cannot drift apart again (they had: this table carried Idaho's
    # pre-correction 36.0).
    ("Appendix E — statewide concentration, all twelve cells", "appe_statewide",
     r"\| top 1% → share of \$ \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| "
     r"\| top 10% → share of \$ \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| "
     r"\| Gini \| ([\d.]+) \| ([\d.]+) \| ([\d.]+) \| ([\d.]+) \|",
     ("sw_wa_top1", "sw_ny_top1", "sw_tx_top1", "sw_id_top1",
      "sw_wa_top10", "sw_ny_top10", "sw_tx_top10", "sw_id_top10",
      "sw_wa_gini", "sw_ny_gini", "sw_tx_gini", "sw_id_gini"), 0.05),

    # --- Data, code, and reproduction: the public-matcher reproduction count.
    ("datacode — the Idaho federal reproduction row count", "datacode",
     r"0 differing rows across all 9 columns of all ([\d,]+)\s+rows",
     ("id_fed_n",), 0),
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
    # H1's blocks are roll joins. The NY state rows sum to the ROLL-JOINED count, not the
    # panel count — the +5 duplicate-id fan-out Appendix C documents. This probe asserted the
    # panel count and passed, because the panel count is real; what was wrong was the claim
    # that the rows sum to it.
    ("crossover, ID state rows sum to its panel", "xover_id",
     r"Idaho's state rows sum to that panel's ([\d,]+)", ("id_state_n",), 0),
    ("crossover, NY state rows sum to the roll join", "xover_id",
     r"New York's sum to \*{0,2}([\d,]+)\*{0,2} rather than the panel's ([\d,]+)",
     ("ny_state_rolljoin_n", "ny_state_n"), 0),
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
    "abstract",
    "methods",
    "sensitivity",
    "matchrate",
    "priorwork",
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
    "appf_head", "appf_mid", "appf_tail",
    "appf_budget", "appf_reach",
    "appc_mid", "appc_tail2",
    # Full-paper coverage, 2026-08-14 — see the SECTION_BOUNDS note.
    "frontmatter", "question", "f1_intro",
    "limits_head", "limits_mid", "limits_tail", "meaning",
    "appc_nystate", "appe_statewide", "datacode", "references",
)

# Sliced but NOT YET audited, with the count of unmapped numeric tokens each still carries.
# This is not "by design" — it is unfinished, and it is recorded here with exact numbers so the
# remaining work is specified rather than rediscovered. Adding one of these to AUDITED_SECTIONS
# is the next step; the slices already exist, so the audit will report precisely what is left.
# Sliced but not audited. EMPTY as of 2026-07-30 — every sliced section is audited. The
# mechanism stays because it is the only honest way to record an unfinished section, and the
# invariant test reads it so a future omission cannot be silent.
PENDING_AUDIT: dict[str, str] = {}


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

    # 5.51M was exempted here as "WA roll size, same" and was the ALL-RECORDS count printed
    # under the words "active registration roll". An exemption cannot catch a mislabelled
    # figure; the three roll sizes are now probed in `methods` instead.
    # 1.03M was exempted alongside it and is now probed in `methods` too, so it is pruned.
    "96.9": "Wilson lower bound from the frozen verdict CSV (Appendix F), not a DB figure",
    "3.1%": "the error budget, derived as sens_budget_pct and probed once in `sensitivity`; "
            "the section restates the same constant four more times",
    "16.1%": "the panel-specific ceiling, derived as val_t0_panel_err_hi from the frozen "
             "verdict CSV's 20 full-name records per panel and probed twice in `sensitivity`; "
             "the section restates the same constant in both table headers and twice in prose",
    "50.4%": "ZIP3-tier precision from the frozen verdict CSV (Appendix F), same class as 96.9",
    "12.6M": "the size of the FULL NYSBOE feed as published (data.ny.gov 4j2b-6a2j, rows back "
             "to 1999) — a property of the source, not of what this paper loads. The loaded "
             "slice's count and dollars are derived (ny_feed_rows / ny_feed_m) and probed in "
             "appc_nystate",
    "0.66%": "the content-level duplicate-dollar residue in the NYSBOE feed, owned by "
             "scripts/sanity_check_ny_contributions.py, which the paragraph cites and which "
             "audits the load on every run",
    "269,204": "all-tier WA state row count, probed once in `appf_weighted`; the denominator "
               "note restates it a second time in the same sentence",
    "32.6%": "the RETIRED name-heuristic estimate of Idaho's organisation dollar share, quoted "
             "only to say the measured 53.9% is well above it. Historical, superseded, and "
             "not recomputable — the heuristic it came from was deleted",
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
    # "3.0" (arithmetic on the pooled trio) pruned 2026-08-14: the overstatement is now
    # derived as pool_overstate and probed in both appc_head and frontmatter, so the token
    # stopped firing — the 2026-08-14 gate run flagged the exemption as stale.
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
                   "181,539", "47,356", "39.7%", "71.2%", "0.800",
                   "770,765", "$76.2M", "54,155", "36.1%", "69.2%", "0.775",
                   "770,128", "54,088",
                   "2,816,398", "$348.3M", "728,255", "44.4%", "75.5%", "0.823",
                   "5,578,905", "$645.6M", "361,184", "72.3%")},
    **{tok: "Appendix G4 clipping table cell — same script, same heuristic"
       for tok in ("32.2%", "30.1%", "68.7%", "$571M", "31.2%", "28.4%", "67.7%", "$554M",
                   "30.9%", "67.4%", "$548M", "26.4%", "62.9%", "$454M",
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

# Sections whose figures are accounted for by a WRITTEN REASON rather than by derivation.
#
# This is a deliberately uncomfortable mechanism and it is kept small. It exists because three of
# Appendix F's robustness blocks are separate INSTRUMENTS — inverse-propensity re-weighting, the
# household over-exclusion, and the persisted-`match_quality` filter — and reimplementing an
# instrument inside the verifier copies it rather than checks it. That is the same basis on which
# Appendix G's G3/G4 tables have been exempt since review round 9, and the supplement states which
# sections are closed which way, so "nothing unaccounted for" is never read as "everything
# re-derived".
#
# The bar for adding a section here: the block must compute something this verifier cannot
# independently reproduce without duplicating a classification or weighting scheme, AND the
# originating script must be named. A block that is merely tedious arithmetic does not qualify —
# Appendix F's three RATING tables were derived from the frozen verdict CSVs for that reason.
COVERAGE_EXEMPT_SECTIONS = {
    "references":
        "A bibliography. Its numeric tokens are page ranges, volume/issue numbers and DOIs — "
        "citations, not quantities — and the figures those works are cited FOR are asserted "
        "by verify_donor_class.py's own probes where the paper uses them (the Related-work "
        "and prior-work sections are audited by derivation). The same closure the WA paper's "
        "Appendix D carries.",
    "appf_head":
        "Appendix F's matchability and tier-composition blocks. The P(matchable) spreads and the "
        "inverse-propensity re-weighted multipliers come from diag_ny_match_bias.py and its WA "
        "counterpart, computed on the RETAINED all-tier snapshots; the tier-composition and "
        "match_quality-filter tables come from diag_donor_class_revisions.py. Re-deriving the "
        "re-weighting or the persisted-column filter here would reimplement those instruments "
        "rather than check them. Several figures in the block are additionally labelled in the "
        "paper as superseded or as an earlier draft's, and are quoted only to record that.",
    "appf_mid":
        "Per-tier false-merge risk on the donor side, and the rating design. Both are properties "
        "of diag_match_validation_stratified.py's sampling frame rather than of the panels; the "
        "rating RESULTS it produced are derived and probed in appf_precision / appf_weighted / "
        "appf_modes.",
    "appf_tail":
        "The error-mode tail: the donor-side ceiling analysis, the current-roll survivorship "
        "note, and (since 2026-08-06) the independent rater's inter-rater block. The ceiling "
        "figures come from diag_donor_class_revisions.py's reachability pass; the survivorship "
        "note is explicitly a statement about what CANNOT be assigned a direction, and carries "
        "no estimate to check. THE INTER-RATER FIGURES ARE NOT COVERED BY THIS EXEMPTION — they "
        "are derived by _d_rater2 from the committed PII-free ledger "
        "reference/match_validation_rater2_verdicts.csv and asserted by ten section-less probes, "
        "because widening a written reason to swallow ten new result figures is how a reason "
        "that was true when written becomes false. The two donor-weighted precisions it also "
        "states (91.0% independent, 95.7% re-rate, against the published 93.0%) are owned by "
        "score_match_validation_human.py, which applies the frozen tier shares.",
    "appc_tail2":
        "Appendix C's match-key section. Its tier shares are probed by the section-less tier-share "
        "probe (which asserts every copy in the paper); the remaining figures are the parser "
        "defect rates and contributor-type shares owned by diag_donor_class_revisions.py and the "
        "Idaho Sunshine loader, and the panel-specific name-order rate the paper itself now "
        "discloses as not independently confirmed.",
}


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
        if name in COVERAGE_EXEMPT_SECTIONS:
            # Printed distinctly from "fully mapped" on purpose: a reader must be able to see
            # at a glance which sections were re-derived and which were accounted for by reason.
            print(f"  reason {name:16} closed by written reason, not derivation")
            continue
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
    if not path.exists():
        # An OPERATIONAL document that deliberately does not travel to the public repository —
        # the submission memo, the cover letter, the metadata. Until 2026-08-06 this raised
        # FileNotFoundError, so the flagship verifier CRASHED in the public checkout: the repo
        # shipped `verify_donor_class.py` and a paper telling readers to run it, and it could
        # not run. That was pre-existing and had never been caught, because A14's "run the
        # verifiers there" step had only ever been exercised on the other seven.
        #
        # Absent is now empty, and the six probes that target these documents are SKIPPED with
        # a printed notice rather than failing. Skipping is right only because the documents are
        # withheld by design (sync_public_repo.NEVER); a MISSING PAPER still fails loudly,
        # because `PAPER` and `SUPPLEMENT` are not in _OPERATIONAL below.
        return ""
    return re.sub(r"\s+", " ", re.sub(r"(?m)^\s*>\s?", "", path.read_text(encoding="utf-8")))

def prose_probes():
    """Scrape the manuscript and its supplement, asserting every figure against the DBs."""
    docs = {"paper": _normalise(PAPER), "supp": _normalise(SUPPLEMENT),
            "memo": _normalise(MEMO), "cover": _normalise(COVER),
            "meta": _normalise(METADATA)}
    # Section-less probes search both documents. The separator carries no digits and no letters
    # a probe could match, so a pattern cannot span the join.
    # The submission package joins the section-less haystack. A `section=None` probe checks
    # every occurrence it finds, so this does not merely carry the new memo/metadata probes —
    # it extends every existing section-less probe to the memo, cover letter and metadata,
    # which until now restated paper figures with nothing checking them.
    norm = "  ###  ".join((docs["paper"], docs["supp"], docs["memo"], docs["cover"],
                           docs["meta"]))

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

    d = cached_derive()
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
    absent = {pre: name for pre, name in _OPERATIONAL.items()
              if not (ROOT / "docs" / name).exists()}
    if absent:
        print("  operational documents absent (they do not travel to the public repo); the "
              "probes that check them are SKIPPED, not failed: "
              + ", ".join(sorted(absent.values())))
    skipped = 0
    for label, section, rx, keys, tol in PROBES:
        pre = next((p for p in absent if label.startswith(p)), None)
        if pre is not None:
            skipped += 1
            continue
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


def check_pin_date() -> list[str]:
    """Appendix C's pin date must equal the snapshot's own metadata.

    Separate from the numeric probes because a date is not a float. It matters as much as the
    count: a silent re-pin moves every Washington denominator, and a stale date in the paper
    would be the only visible symptom.
    """
    d = cached_derive()
    stated = re.search(r"snapshot was taken on \*\*([\d-]+)\*\*", PAPER.read_text(encoding="utf-8"))
    if not stated:
        return ["pin date: Appendix C no longer states when the WA roll was pinned"]
    if stated.group(1) != d.get("wa_pin_date"):
        return [f"pin date: paper says {stated.group(1)}, snapshot says {d.get('wa_pin_date')} "
                f"— the roll was re-pinned without updating the paper"]
    print(f"  ok   WA roll pinned {d['wa_pin_date']}, {d['wa_pin_n']:,} registrants")
    return []


_FAILURES += prose_probes()
_FAILURES += check_pin_date()

# ============================== INTEGRITY SUMMARY ==============================
print("\n" + "=" * 78)
if _FAILURES:
    print(f"INTEGRITY: {len(_FAILURES)} FAILURE(S)")
    print("=" * 78)
    for f in _FAILURES:
        print(f"  - {f}")
    _close_conns()
    raise SystemExit(1)
print("INTEGRITY: all assertions pass")
print("=" * 78)
_close_conns()
