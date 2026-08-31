"""Verify docs/electoral-health-whitepaper.md Findings 4 and 5 against the databases.

WHERE THE PROSE-SCRAPING DESIGN CAME FROM. This script invented it. The other verify_*
scripts used to hold each published figure as a Python constant and compare it to a fresh
derivation, which works for a paper whose numbers are computed once and stated once. The
white paper is not that: it *restates* figures computed in the donor-class and cross-state
papers, and its two observed failure modes were drifting out of step with those sources and
contradicting **itself** — Finding 5 once gave the federal top-1% as 41.2% in a panel note
and 42.4% four lines later. A constants table catches neither, because it never reads the
prose: someone can edit the sentence, leave the constant right, and the check still passes.

So this script SCRAPES THE PROSE, and on 2026-08-01 the rest of the series was rebuilt the
same way. The loop itself now lives in `_verify_prose.py` and this file calls it, so the
three rules are defined once: a probe whose anchor matches nothing FAILS rather than
skipping, every occurrence of a figure is checked, and `--coverage` lists what no probe
touched. Keeping a private copy of the loop had made the original the one verifier with no
coverage report.

SCOPE, widened twice in two days. It began at Findings 4-6 — the money/donor results that
restate verified cuts — on the reasoning that Findings 1-3 were prospectus items covered by
their own papers' verifiers. That reasoning was wrong in the way this whole file exists to
catch: a restatement is exactly where a figure drifts, whoever owns the original. Finding 2
came in on 2026-08-15 when it stopped leading with unpinned forecast reads, and Domain 1
(participation) came in on 2026-08-16 with the synthesis conversion — which immediately found
two rates quoted a decimal place finer than the owning paper prints them.

Finding 6 is checked in two halves, and the split is deliberate. Its **panel-inventory
facts** (the scorable-race count, WA-03's IE dollars, and the size of the direction-coded
PDC state-legislative panel) are re-derived here from scratch. Until 2026-08-09 the third
of those was derived the other way round — as the *absence* of direction on PDC rows, which
the paper then cited as a limit of Washington's disclosure. Direction is filed in form C-6
section C6.3 and had simply never been loaded; the derivation now reads `pdc_ie_targets`.
See `docs/pdc-c6-direction-audit.md`. Its **slope and correlation** are not re-derived: they regress a
fundamentals-net residual that only the forecast model produces, and reimplementing that
here would fork the model rather than check it. Those are instead asserted to agree with
`does-money-move-votes.md`, which is the paper that owns them and whose independent
derivation is `diag_ie_vs_margin.py`. That is a CONSISTENCY check, not a re-derivation, and
it is labelled as such in the output — but it is the check that matters, because the white
paper had drifted to -0.42/-0.43 against the money paper's then-correct -0.39/-0.39. Both
figures are now +0.515/+0.186 on a five-cycle panel; the sign reversed when the panel grew,
which is what an n=7 estimate does and why this check reads the owning paper rather than a
constant.

Run:  python scripts/verify_whitepaper.py       (~40s; the bootstrap block dominates)
"""
from pathlib import Path
import re
import sys

import duckdb
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _verify_prose as vp  # noqa: E402

vp.stdout_utf8()

ROOT = vp.ROOT
DATA = vp.DATA
PAPER = vp.DOCS / "electoral-health-whitepaper.md"
MONEY_PAPER = vp.DOCS / "does-money-move-votes.md"
DONOR_PAPER = vp.DOCS / "donor-class-and-the-electorate.md"
SAFE_SEAT_PAPER = vp.DOCS / "safe-seat-washington.md"
WA_PAPER = vp.DOCS / "who-decides-washington.md"
# Added 2026-08-26 with the whole-document window: the "What the evidence does not support"
# section quotes this companion's §E-I flow matrices in ten places and nothing read it.
XSTATE_PAPER = vp.DOCS / "cross-state-fec-money.md"
GENS = ["Silent", "Boomer", "Gen X", "Millennial", "Gen Z"]

# Bootstrap settings, copied from diag_donor_concentration_bootstrap.py. The seed is fixed
# there, so the published CIs are exactly reproducible rather than merely close — but ONLY
# if the panels are resampled in the same ORDER, because one RNG is threaded through all
# three in sequence. Reordering them silently changes every interval.
BOOT_B = 1000
BOOT_SEED = 12345

# Stated, not silently omitted:
UNCHECKED = [
    "Finding 6's slope and Pearson r — regressed on a fundamentals-net residual that only "
    "the forecast model produces. Cross-checked against does-money-move-votes.md instead "
    "of re-derived; the independent derivation is scripts/diag_ie_vs_margin.py",
    "Findings 1-3 — prospectus items; their realized analyses are verified by "
    "verify_who_decides_wa.py and diag_seat_competition.py",
    # DECLARED 2026-08-26, when the whole-document window first exposed them. Not a
    # derivation this file can add: both grids come from scripts/backtest_model.py, which
    # runs the forecast model over every district-cycle, and re-deriving them here would
    # fork the model rather than check it — the same reasoning that keeps Finding 6's slope
    # out of this file.
    "The 'are outcomes pre-determined?' limits item — MAE 6.41 / 94% directional on the "
    "163-cell filtered grid, and 10.12 / 85% on the unfiltered 170-cell grid. Owned by "
    "scripts/backtest_model.py; the 170-cell pair is also stated in METHODOLOGY.md §6 and "
    "CLAUDE.md. ⚠ OPEN FOR THE AUTHOR, and declared rather than quietly exempted: the two "
    "pairs are quoted inside one parenthesis as though they were one backtest, but "
    "METHODOLOGY.md dates 10.12/85% to the May-15 grid expansion while the 163-cell "
    "6.41/94% belongs to the current v-jun17 model. If they are two model versions, the "
    "sentence is comparing a filtered and an unfiltered grid ACROSS a coefficient change "
    "and the contrast it draws is not the one it states. Settling it needs a backtest run, "
    "not a scrape.",
]


# ----------------------------------------------------------------------------- derivations
def _conc(con, tbl):
    t1, t10 = con.execute(f"""
        WITH r AS (SELECT total_donated t, NTILE(100) OVER (ORDER BY total_donated DESC) p
                   FROM {tbl} WHERE total_donated > 0)
        SELECT 100.0*SUM(t) FILTER(WHERE p=1)/SUM(t),
               100.0*SUM(t) FILTER(WHERE p<=10)/SUM(t) FROM r""").fetchone()
    g, = con.execute(f"""
        WITH r AS (SELECT total_donated t, ROW_NUMBER() OVER (ORDER BY total_donated) rn,
                          COUNT(*) OVER () n, SUM(total_donated) OVER () s
                   FROM {tbl} WHERE total_donated > 0)
        SELECT (2.0*SUM(rn*t)/(MAX(n)*MAX(s))) - (MAX(n)+1.0)/MAX(n) FROM r""").fetchone()
    n, = con.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()
    return dict(n=n, top1=float(t1), top10=float(t10), gini=float(g))


def _multipliers(con, panel):
    """Donor share / roll share by generation.

    Roll = voter_scores ld-scope. WA carries every voter in BOTH a cd and an ld scope, so an
    unfiltered roll double-counts; ld is the complete one. Cross-state §F5 uses a different
    roll (all of vrdb.voters, generation from birth year) — checked 2026-07-27, the two agree
    to 2dp on WA, which is why the white paper can put a pooled figure from one beside a
    federal figure from the other in a single sentence without mixing bases.
    """
    roll = dict(con.execute("""
        SELECT age_cohort, COUNT(*) FROM voter_scores
        WHERE LEFT(district_id,2)='ld' AND age_cohort IS NOT NULL GROUP BY 1""").fetchall())
    don = dict(con.execute(f"""
        SELECT s.age_cohort, COUNT(*) FROM voter_scores s JOIN {panel} a USING(state_voter_id)
        WHERE LEFT(s.district_id,2)='ld' AND s.age_cohort IS NOT NULL GROUP BY 1""").fetchall())
    rt, dt = sum(roll.values()), sum(don.values())
    return {g: (don.get(g, 0) / dt * 100) / (roll.get(g, 0) / rt * 100) for g in GENS}


def _zip3_top2(con, panel):
    v, = con.execute(f"""
        WITH d AS (SELECT SUBSTR(v.reg_zip,1,3) z, a.total_donated x FROM {panel} a
                   JOIN vrdb.voters v USING (state_voter_id) WHERE v.reg_zip IS NOT NULL),
        s AS (SELECT z, SUM(x) tot FROM d GROUP BY 1 ORDER BY tot DESC LIMIT 2)
        SELECT 100.0*(SELECT SUM(tot) FROM s)/(SELECT SUM(x) FROM d)""").fetchone()
    return float(v)


def _ipw(con, panel: str = "voter_donor_affiliation"):
    """Raw and matcher-bias-reweighted over-representation, for ONE panel.

    PANELISED 2026-08-24. This was hardcoded to the pooled panel while the sentence it
    answers claims the invariance holds "in both panels" -- so half the claim was
    uncheckable, and the half that was checkable turned out to be false. The caller now runs
    it for pooled and federal and `claim_guards` checks both.
    """
    gen = ("CASE WHEN EXTRACT(year FROM v.birthdate) IS NULL THEN NULL "
           "WHEN EXTRACT(year FROM v.birthdate)<=1945 THEN 'Silent' "
           "WHEN EXTRACT(year FROM v.birthdate)<=1964 THEN 'Boomer' "
           "WHEN EXTRACT(year FROM v.birthdate)<=1980 THEN 'Gen X' "
           "WHEN EXTRACT(year FROM v.birthdate)<=1996 THEN 'Millennial' ELSE 'Gen Z' END")
    con.execute(f"""CREATE OR REPLACE TEMP TABLE _w AS
        SELECT v.state_voter_id sid, {gen} g,
               UPPER(TRIM(v.last_name))||'|'||UPPER(SUBSTR(TRIM(v.first_name),1,1))
                 ||'|'||SUBSTR(v.reg_zip,1,5) k FROM vrdb.voters v""")
    con.execute("CREATE OR REPLACE TEMP TABLE _wk AS SELECT k, COUNT(*) n FROM _w GROUP BY 1")
    roll = dict(con.execute("SELECT g,COUNT(*) FROM _w WHERE g IS NOT NULL GROUP BY 1").fetchall())
    pm = dict(con.execute("""SELECT w.g, 100.0*AVG(CASE WHEN k.n=1 THEN 1.0 ELSE 0 END)
        FROM _w w JOIN _wk k USING(k) WHERE w.g IS NOT NULL GROUP BY 1""").fetchall())
    don = dict(con.execute(f"""SELECT w.g,COUNT(*) FROM {panel} a
        JOIN _w w ON w.sid=a.state_voter_id WHERE w.g IS NOT NULL GROUP BY 1""").fetchall())
    rt, dt = sum(roll.values()), sum(don.values())
    ipw = {g: don.get(g, 0) / (pm[g] / 100) for g in roll if pm.get(g)}
    it = sum(ipw.values())
    out = {}
    for g in GENS:
        rp = roll.get(g, 0) / rt * 100
        out[g] = ((don.get(g, 0) / dt * 100) / rp, (ipw.get(g, 0) / it * 100) / rp)
    return out, min(pm.values()), max(pm.values())


def _turnout(con):
    rows = con.execute("""
        -- The PINNED roll (donor_paper_wa_roll, frozen 2026-07-31), not the live
        -- voter_scores. voter_scores is rebuilt on every ballot load and every
        -- crosswalk improvement, so reading it live made these figures drift
        -- away from the paper by a few thousandths -- and drift in a verifier
        -- reads as "the paper is wrong" when the paper is fine. The pin carries
        -- exactly the three columns this derivation needs and reproduces the
        -- published values to the digit: 87.60 / 50.91 / 0.9670 / 0.7486.
        WITH roll AS (SELECT state_voter_id, is_super_voter, turnout_propensity
                      FROM donor_paper_wa_roll),
        f AS (SELECT r.*, (a.state_voter_id IS NOT NULL) donor
              FROM roll r LEFT JOIN voter_donor_affiliation a USING (state_voter_id))
        SELECT donor, 100.0*AVG(CASE WHEN is_super_voter THEN 1.0 ELSE 0 END),
               AVG(turnout_propensity) FROM f GROUP BY donor""").fetchall()
    d = {("donor" if x else "non"): (float(s), float(p)) for x, s, p in rows}
    return dict(super_d=d["donor"][0], super_n=d["non"][0], prop_d=d["donor"][1],
                prop_n=d["non"][1], ratio=d["donor"][0] / d["non"][0])


def _party_and_age(state, buckets, dem_key, dem_pred="= 'DEM'"):
    """Own-party skew (donor% - roll%) and 65+ donor share, per panel."""
    con = duckdb.connect(str(DATA / f"{state}_statewide.duckdb"), read_only=True)
    con.execute(f"ATTACH '{DATA / (state + '_vrdb.duckdb')}' AS vrdb (READ_ONLY)")
    # Age basis must match the published one exactly: ID publishes its current-roll age
    # snapshot, NY measures age AS OF THE 2024 GENERAL (verify_donor_class.NY_AGE).
    # Using 2026 for NY reads 54.6% against a published 49.9% — a basis error, not drift.
    age = "v.age" if state == "id" else "date_diff('year', v.birthdate, DATE '2024-11-05')"
    out = {}
    for tag, panel in (("fed", "voter_donor_affiliation_fec"),
                       ("state", "voter_donor_affiliation_state")):
        reg = dict(con.execute(
            f"SELECT {buckets},COUNT(*) FROM vrdb.voters v WHERE status_code='A' GROUP BY 1").fetchall())
        don = dict(con.execute(f"""SELECT {buckets},COUNT(*) FROM {panel} a
            JOIN vrdb.voters v USING(state_voter_id) GROUP BY 1""").fetchall())
        rt, dt = sum(reg.values()), sum(don.values())
        out[f"{tag}_skew"] = don.get(dem_key, 0) / dt * 100 - reg.get(dem_key, 0) / rt * 100
        p65, = con.execute(f"""SELECT 100.0*COUNT(*) FILTER (WHERE {age}>=65)/COUNT(*)
            FROM {panel} a JOIN vrdb.voters v USING(state_voter_id)""").fetchone()
        out[f"{tag}_65"] = float(p65)
    # Own-party crossover on BOTH panels. Only the state one used to be derived,
    # and the bullet quotes one figure from each state — Idaho's from the state
    # layer (it says so) and New York's from the federal one (every other NY
    # figure in the same sentence is federal). With one panel derived, the NY
    # half could not be probed at all, and it had gone stale on the retired
    # all-tier specification while the sentence claimed the primary one.
    for tag, panel in (("fed", "voter_donor_affiliation_fec"),
                       ("state", "voter_donor_affiliation_state")):
        out[f"{tag}_dem_donly"], = con.execute(f"""
            SELECT 100.0*COUNT(*) FILTER (WHERE d_amount>0 AND r_amount=0)
                   /COUNT(*) FILTER (WHERE d_amount+r_amount>0)
            FROM {panel} a JOIN vrdb.voters v USING(state_voter_id)
            WHERE v.party {dem_pred}""").fetchone()
    out["state_dem_donly"] = out["state_dem_donly"]
    con.close()
    return out


def _gini_np(x):
    x = np.sort(x)
    n, s = x.size, x.sum()
    return (2.0 * np.sum(np.arange(1, n + 1) * x) / (n * s)) - (n + 1.0) / n


def _topshare_np(x, frac):
    x = np.sort(x)[::-1]
    return x[:max(1, int(round(x.size * frac)))].sum() / x.sum()


def _bootstrap(d):
    """Reproduce the published 95% CIs exactly.

    Same estimator, B and seed as diag_donor_concentration_bootstrap.py, and crucially the
    same panel ORDER — federal, then state, then inflow — because a single RNG is consumed
    across all three. Deterministic, so these are asserted at full precision rather than
    with a Monte-Carlo slack. ~35s, which is the whole reason this script is slower than
    its siblings; an earlier note claiming the bootstrap was 'too slow for a verifier' was
    simply wrong and is withdrawn.
    """
    rng = np.random.default_rng(BOOT_SEED)
    wa = duckdb.connect(str(DATA / "wa_statewide.duckdb"), read_only=True)
    pools = []
    for tag, tbl in (("fed", "voter_donor_affiliation_fec"),
                     ("state", "voter_donor_affiliation_state")):
        pools.append((tag, np.array(wa.execute(
            f"SELECT total_donated FROM {tbl} WHERE total_donated > 0").fetchall(),
            dtype=float).ravel()))
    wa.close()
    ic = duckdb.connect(str(DATA / "fec_inflow.duckdb"), read_only=True)
    pools.append(("inflow24", np.array(ic.execute("""
        SELECT SUM(contribution_amount) FROM inflow_contributions
        WHERE recipient_office IN ('H','S') AND contribution_amount > 0
          AND election_cycle = 2024 AND contributor_name IS NOT NULL
        GROUP BY UPPER(TRIM(contributor_name)) || '|' || LEFT(COALESCE(contributor_zip,''),5)
    """).fetchall(), dtype=float).ravel()))
    ic.close()
    for tag, x in pools:
        n = x.size
        g = np.empty(BOOT_B)
        t1 = np.empty(BOOT_B)
        for b in range(BOOT_B):
            s = x[rng.integers(0, n, n)]
            g[b], t1[b] = _gini_np(s), _topshare_np(s, 0.01)
        d[f"{tag}_gini_lo"], d[f"{tag}_gini_hi"] = np.percentile(g, [2.5, 97.5])
        d[f"{tag}_t1_lo"], d[f"{tag}_t1_hi"] = np.percentile(t1 * 100, [2.5, 97.5])
        d[f"{tag}_gini_pt"] = _gini_np(x)


# --- PUBLIC ADAPTATION -------------------------------------------------------------------
# The private script imports StaleIEData / assert_ie_classified from the unpublished
# wa_analyzer package, so the guard is inlined here. It is the SAME check: FEC IE rows
# loaded before the 2026-08-08 notice/periodic split carry is_notice IS NULL, are excluded by
# v_independent_expenditures, and would silently yield $0.0M rather than an inflated total.
# Stopping is safer than reporting a number nobody measured. Kept character-comparable with
# the copy in diag_ie_vs_margin.py so there is one public definition to read.
class StaleIEData(RuntimeError):
    pass


def assert_ie_classified(conn) -> None:
    cols = {r[1] for r in conn.execute("PRAGMA table_info('independent_expenditures')").fetchall()}
    predicate = "is_notice IS NULL" if "is_notice" in cols else "TRUE"
    stale = conn.execute(f"""
        SELECT state, office, district, election_cycle, COUNT(*)
        FROM independent_expenditures
        WHERE COALESCE(source,'') NOT ILIKE 'PDC%' AND {predicate}
        GROUP BY 1,2,3,4 ORDER BY 5 DESC""").fetchall()
    if stale:
        raise StaleIEData(
            "FEC independent-expenditure rows on disk predate the notice/periodic split, so "
            "they are excluded from every total and no IE figure here is measurable. Re-load "
            "per cycle with --fec-ie-replace. Groups affected: "
            + "; ".join(f"{s} {o}-{d} cycle {c}: {n:,} rows" for s, o, d, c, n in stale))
# --- end public adaptation ---------------------------------------------------------------


def _finding6(d):
    """Finding 6's data-ceiling facts — the part the paper itself calls the citable result."""
    c = duckdb.connect(str(DATA / "wa_statewide.duckdb"), read_only=True)
    # Reads go through v_independent_expenditures, which drops FEC's 24/48-hour
    # notice rows (they restate the periodic Schedule E and double the totals)
    # AND any row loaded before that distinction was recorded. Without this stop
    # a stale table asserts $0.0M rather than failing.
    assert_ie_classified(c)
    # WA-03 2024: the most IE-saturated US House race in the country that cycle.
    tot, net = c.execute("""
        WITH p AS (SELECT DISTINCT election_cycle, UPPER(candidate_name) cn, party
                   FROM candidate_finance WHERE state='WA' AND office='H')
        SELECT SUM(ie.expenditure_amount)/1e6,
               SUM(CASE WHEN (p.party='Democratic' AND ie.support_oppose='S')
                          OR (p.party='Republican' AND ie.support_oppose='O') THEN ie.expenditure_amount
                        ELSE -ie.expenditure_amount END)/1e6
        FROM v_independent_expenditures ie
        LEFT JOIN p ON p.election_cycle=ie.election_cycle
                   AND p.cn=UPPER(ie.candidate_name)
        WHERE ie.source='FEC' AND ie.office='H' AND ie.state='WA'
          AND ie.support_oppose IN ('S','O')
          AND ie.election_cycle=2024 AND ie.district IN ('03','3')""").fetchone()
    d["wa03_ie_total"], d["wa03_ie_net"] = float(tot), float(net)
    # Directional FEC IE exists for one cycle only — the ceiling itself.
    d["fec_ie_cycles"], = c.execute("""
        SELECT COUNT(DISTINCT election_cycle) FROM v_independent_expenditures
        WHERE source='FEC' AND office='H' AND state='WA' AND support_oppose IN ('S','O')
    """).fetchone()
    # PDC state-legislative IE, direction-coded. It is NOT unusable for a directional
    # test, and a previous version of this derivation said so: it read
    # `support_oppose` off `independent_expenditures`, found it null, and the
    # whitepaper called that a property of Washington's disclosure regime. Direction
    # is filed in form C-6 section C6.3 and lives in `pdc_ie_targets`, one-to-many
    # against an expenditure. See docs/pdc-c6-direction-audit.md.
    pdc_m, pdc_rows = c.execute("""
        SELECT SUM(portion_of_amount)/1e6, COUNT(*) FROM pdc_ie_targets
        WHERE candidate_office_type = 'Legislative'
          AND election_year BETWEEN 2018 AND 2024""").fetchone()
    d["pdc_c63_m"], d["pdc_c63_rows"] = float(pdc_m), int(pdc_rows)
    c.close()


def _scale(con, d):
    """Dollar scales quoted in Finding 5's two provenance notes.

    THE THREE FIGURES SIT ON THREE DIFFERENT AMOUNT FILTERS, and that is not a defect
    to "tidy up" — each reproduces exactly on one basis and on no other:

        FEC  $646.2M   `FEC:` prefix, every row       (identical with amt>0; the
                                                       negative rows are PDC's)
        PDC  $394.6M   `PDC:` prefix, EVERY row       (amt>0 gives $402.9M — the
                                                       PDC layer carries -$8.3M of
                                                       refunds, so the published
                                                       figure is the net one)
        both $1,050.8M unfiltered, amt>0              (all rows gives $1,042.5M)

    So 646.2 + 394.6 = 1,040.8 does not equal 1,050.8, and the note's parenthetical
    ("FEC plus state PDC plus non-resident donors") is a description of the population
    rather than an equation. Making the filters uniform would break two of the three.
    """
    for key, where in (
            ("fec_m", "contribution_id LIKE 'FEC:%'"),
            ("pdc_m", "contribution_id LIKE 'PDC:%'"),
            ("unfiltered_m", "contribution_amount > 0")):
        v, = con.execute("SELECT SUM(contribution_amount)/1e6 FROM individual_contributions "
                         f"WHERE {where}").fetchone()
        d[f"wa_{key}"] = float(v)


#: The state-disclosure layer inside each state's `individual_contributions`, by the
#: `contribution_id` prefix that CLAUDE.md makes the scoping rule. TX has none — it is
#: FEC-only in this table, which is why it carries no state row in the inventory sum.
_STATE_LAYER = {"wa": "PDC:", "ny": "NY:", "id": "SUNSHINE:", "tx": None}


def _inventory(d):
    """The "Data, and what each state can actually support" table — the paper's scale claims.

    ADDED 2026-08-26 with the whole-document window. This section is the first thing a
    reader meets after the scope statement and it is where the programme states its size:
    row counts, dollar totals, the per-panel matched counts. Nothing asserted any of it.
    That is worse than it sounds, because the paragraph itself says "Every count below is a
    **live read that drifts** as the 2026 cycle accrues" — an explicitly drifting figure with
    no gate is a figure that will be wrong and cannot announce it.

    THREE BASES, and they are NOT interchangeable — writing them down is the point:

      federal layer   `contribution_id LIKE 'FEC:%'`, the BULK loader's rows. This is what
                      every published federal cut in the series is scoped to, and it is what
                      the per-state "WA 5.58M / NY 9.98M / TX 12.56M / ID 0.77M" row is.
      state layer     the per-state disclosure prefix in _STATE_LAYER.
      the table       `COUNT(*)`, which is NOT the sum of the two. WA and NY each hold a
                      further 45,494 rows whose `contribution_id` carries no prefix at all.

    WHAT THOSE 45,494 ROWS ARE, since the number is the same in both databases and that
    looks like a copy: they are not. WA's carry WA candidate ids (H0WA02080, H0WA03187),
    NY's carry NY ones (H0NY09080, H2NY03139); the equal count is a property of the FEC API
    loader's paging, not a shared population. They came from `load-fec-contributions-allcycles`
    rather than the bulk file, and they are donor-residence UNFILTERED — the top contributor
    state in both is California — so they are inflow-shaped rows sitting in a table CLAUDE.md
    defines as outflow. No published cut reads them: every federal figure filters `FEC:%` and
    every panel is built with the matcher's `source_prefixes`.

    They matter to exactly one sentence, which is why this is derived rather than exempted.
    "Adding each state's own finance system takes it to N rows" describes federal + state
    layers, and that sum is 36.0M. 36.1M was `COUNT(*)`, which adds 90,988 rows from neither
    layer. Same digit either way in the dollar total ($6.06B both ways), so the row count is
    the only place the two bases separate — and it separated in the direction that made the
    programme look bigger than the sentence's own description supports.
    """
    wa = duckdb.connect(str(DATA / "wa_statewide.duckdb"), read_only=True)
    wa.execute(f"ATTACH '{DATA / 'wa_vrdb.duckdb'}' AS vrdb (READ_ONLY)")
    # ELECTIONS, on the precinct-results basis and not `COUNT(*) FROM elections`. The two
    # differ by one today and the difference is structural, not a rounding: the 2026 primary
    # is JSON-loaded and has ZERO precinct rows by design (see CLAUDE.md on the votewa.gov
    # migration), so it is a row in `elections` and not an election this figure counts.
    # Taking the easier count would have printed 23 for a "precinct-result rows across N
    # elections" claim whose own denominator has 22.
    d["inv_wa_precinct_m"], d["inv_wa_elections"] = wa.execute(
        "SELECT COUNT(*)/1e6, COUNT(DISTINCT election_id) FROM precinct_results").fetchone()
    d["inv_wa_vs_m"], d["inv_wa_voters_m"] = wa.execute(
        "SELECT COUNT(*)/1e6, COUNT(DISTINCT state_voter_id)/1e6 FROM voter_scores").fetchone()
    d["inv_wa_vrdb_hist_m"], = wa.execute(
        "SELECT COUNT(*)/1e6 FROM vrdb.voting_history").fetchone()
    wa.close()

    fed_rows = fed_usd = all_rows = all_usd = api_extra = 0.0
    star_rows = star_usd = 0.0
    for st in ("wa", "ny", "tx", "id"):
        c = duckdb.connect(str(DATA / f"{st}_statewide.duckdb"), read_only=True)
        n, m = c.execute(
            "SELECT COUNT(*), SUM(contribution_amount)/1e6 FROM individual_contributions "
            "WHERE contribution_id LIKE 'FEC:%'").fetchone()
        d[f"inv_{st}_fed_rows_m"], d[f"inv_{st}_fed_musd"] = n / 1e6, float(m)
        fed_rows += n
        fed_usd += float(m)
        layer = _STATE_LAYER[st]
        sn, sm = (0, 0.0)
        if layer:
            sn, sm = c.execute(
                "SELECT COUNT(*), SUM(contribution_amount)/1e6 FROM individual_contributions "
                f"WHERE contribution_id LIKE '{layer}%'").fetchone()
            # ONLY WASHINGTON'S state layer is stored, because only Washington's is printed
            # ("FEC $646.2M + state PDC $394.6M"). The other three states' state layers feed
            # the four-state totals below as locals. Deriving and storing all four would put
            # six keys nothing probes into the mutation sweep's no-probe bucket, which raises
            # the ceiling without raising the coverage — the sweep counted exactly that on
            # this block's first run.
            # ...and of Washington's pair only the DOLLARS are a key, because the dollars are
            # what the paper prints for the PDC layer ("state PDC `$394.6M`"). Its row count
            # is summed into the 8.6M and never printed alone, so it stays a local: a key the
            # sweep can mutate without any probe noticing is a key that is not being checked,
            # whatever it feeds — the sweep mutates `d` after derive() has already run.
            if st == "wa":
                wa_state_rows = sn
                d["inv_wa_state_musd"] = float(sm)
        # The RETIRED basis, derived rather than transcribed. The correction note has to keep
        # saying what 36.1M was, and a note that quotes a figure the data no longer produces
        # is a worse defect than the one it corrects — so the plain row count is asserted too.
        tot, tot_m = c.execute("SELECT COUNT(*), SUM(contribution_amount)/1e6 "
                               "FROM individual_contributions").fetchone()
        star_rows += tot
        star_usd += float(tot_m)
        api_extra += tot - n - sn
        all_rows += n + sn
        all_usd += float(m) + float(sm)
        # Matched panels, quoted PER PANEL in the same bullet. The pooled WA figure is
        # asserted separately and hard, by the 314,974 guard at the top of derive().
        for tag, tbl in (("fed", "voter_donor_affiliation_fec"),
                         ("state", "voter_donor_affiliation_state")):
            try:
                v, = c.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()
                d[f"inv_{st}_panel_{tag}"] = int(v)
            except duckdb.CatalogException:
                pass                                    # TX has no voter file, so no panel
        c.close()

    d["inv_wa_contrib_rows_m"] = d["inv_wa_fed_rows_m"] + wa_state_rows / 1e6
    # The dollar total is printed in BILLIONS and only in billions, so only the billions key
    # is stored — a millions intermediate beside it is a key no probe can reach.
    d["_inv_wa_contrib_busd"] = (d["inv_wa_fed_musd"] + d["inv_wa_state_musd"]) / 1e3
    d["inv_fed_rows_m"], d["inv_fed_busd"] = fed_rows / 1e6, fed_usd / 1e3
    d["inv_all_rows_m"], d["inv_all_busd"] = all_rows / 1e6, all_usd / 1e3
    d["inv_star_rows_m"], d["inv_star_busd"] = star_rows / 1e6, star_usd / 1e3
    d["inv_api_extra"] = int(api_extra)

    # The two voter-file sizes the paper states, both ROW counts of the loaded roll. NY's is
    # quoted as 13.5M in the support table and 13.54M in the Conclusion, and is pinned at
    # 13,540,505 in the NY paper's own verifier; these are the coarse restatements, so they
    # are checked at the precision printed. WA's roll is NOT derived here — the paper states
    # WA's scale as voter-score rows and distinct voters, not as a roll count, so a wa key
    # would be a derivation with nothing to check it against.
    for st in ("ny", "id"):
        c = duckdb.connect(str(DATA / f"{st}_vrdb.duckdb"), read_only=True)
        d[f"inv_{st}_roll_m"], = c.execute("SELECT COUNT(*)/1e6 FROM voters").fetchone()
        c.close()


#: The current backtest, pinned rather than re-run. A verifier cannot run the forecast model
#: over every district-cycle inside a ten-second gate, and re-implementing it here would fork
#: the model rather than check it — the same reasoning that keeps Finding 6's slope out of this
#: file. So the run is the measurement, the CSV is the frame, and this asserts the paper
#: against the frame. Same pattern as the ACS population pin and the IE current-cycle pin.
BACKTEST_PIN = vp.DOCS / "reference" / "backtest_current_2026-08-26.csv"


def _backtest(d):
    """The backtest metrics the limits section states, read from the pinned run.

    ADDED 2026-08-26, when a re-run settled a question that had been declared in UNCHECKED.
    The section used to quote TWO pairs as one backtest — "MAE 6.41, 94% directional on 163
    filtered cells; 10.12 / 85% on the unfiltered 170-cell grid" — and both halves of that
    framing were wrong: 170 was the VALID-cell count on the May-2026 grid (the same kind of
    quantity as 163, not an unfiltered counterpart), and 10.12/85% belongs to the v-may15 model
    against 6.41/94% for v-jun17. A fresh run gives 163 valid of 236 attempted.

    Pinning rather than declaring is the upgrade: the figures were previously in UNCHECKED with
    the model-version question written out, which is honest but unenforced. A pin makes them
    fail if the paper drifts, and re-pinning is a deliberate act with a dated filename.
    """
    import csv  # noqa: PLC0415
    with BACKTEST_PIN.open(encoding="utf-8", newline="") as fh:
        rows = {r["metric"]: float(r["value"]) for r in csv.DictReader(fh)}
    for k in ("cells_valid", "mae_margin", "directional_accuracy",
              "systematic_bias", "ci_coverage_95"):
        if k not in rows:
            raise SystemExit(
                f"FATAL: {BACKTEST_PIN.name} is missing {k!r}. The limits section states it, so "
                f"a pin without it cannot check the sentence.")
        d[f"bt_{k}"] = rows[k]


def _ledger_mean(d):
    """The unweighted mean of Appendix A's Failure column, read out of the table itself.

    A DERIVATION WITH NO DATABASE IN IT, and that is the whole point. Appendix A's paragraph
    makes a claim ABOUT its own table — that the published 22/100 "cannot be recomputed from
    the table below, which gives an unweighted mean of 18.3". Nothing outside the document
    can settle that; the table is the only source, so the check has to read the table.

    Written as a parse rather than a constant so that editing a cell moves the derived mean
    and fails the probe. A transcribed 18.3 would agree with a table it no longer describes,
    which is the failure mode the paragraph is itself warning about one sentence earlier.
    """
    rows = re.findall(r"^\| (?!Question|-)[^|]+\| *(\d+) *\| *(\d+) *\|",
                      PAPER.read_text(encoding="utf-8"), re.M)
    fails = [int(f) for _ins, f in rows]
    if len(fails) != 10:
        raise AssertionError(
            f"Appendix A's ledger parsed to {len(fails)} scored questions, not the ten the "
            "paragraph above it describes — the table's shape moved and this derivation is "
            "reading the wrong thing. Fix the parse deliberately, do not widen it.")
    d["ledger_mean"] = sum(fails) / len(fails)


def _companions(d):
    """Figures this synthesis QUOTES rather than owns, scraped from the owning papers.

    ADDED 2026-08-15, and it is the structural answer to the referee round of that date.
    His diagnosis was that the synthesis had become a place where retired estimands went to
    survive: Finding 4 still headlined a pooled super-voter gap the donor paper had replaced
    with an eligible-for-all age-standardized one; Finding 5 quoted the *retired* match key's
    roll-side uniqueness (69-73%) instead of the current key's (94-98%), and rested its
    crossover claim on the state panels, which the owning paper says do NOT survive the
    unresolved-pool bound, while the federal panels, which do, sat unused.

    None of that was a computation error, so nothing caught it. `verify_whitepaper.py` was
    faithfully asserting the synthesis against derivations that still computed the retired
    quantity. **A verifier can establish that prose agrees with code; it cannot establish
    that the code still computes the statistic the research programme has decided is the
    right one.** The remedy is to stop re-deriving these here and read them from the paper
    that owns them, so that improving a companion moves the synthesis or fails loudly.

    An anchor that stops matching FAILS. That is the point: it is how the Finding 6 scrapes
    announced, on this same date, that the money paper's tables had been rebuilt underneath
    them and two figures had drifted unnoticed.
    """
    dn = re.sub(r"\s+", " ", DONOR_PAPER.read_text(encoding="utf-8"))
    mp = re.sub(r"\s+", " ", MONEY_PAPER.read_text(encoding="utf-8"))
    wa = re.sub(r"\s+", " ", WA_PAPER.read_text(encoding="utf-8"))
    ss = re.sub(r"\s+", " ", SAFE_SEAT_PAPER.read_text(encoding="utf-8"))
    xs = re.sub(r"\s+", " ", XSTATE_PAPER.read_text(encoding="utf-8"))

    def grab(text, rx, keys, cast=float, where=""):
        m = re.search(rx, text)
        if not m:
            raise SystemExit(
                f"FATAL: the white paper quotes {keys} from {where}, and the anchor no "
                f"longer matches. The companion was reworded or the figure moved — "
                f"re-point this scrape and re-read the sentence that depends on it. "
                f"Refusing to fall back to a local derivation, which is how the retired "
                f"pooled donor estimands survived here for weeks.")
        for k, g in zip(keys, m.groups()):
            d[k] = cast(g)

    # Finding 4 — the eligible-for-all, age-standardized donor/non-donor turnout gaps.
    # Four rows, and the SPAN across them is what the synthesis prints.
    rows = re.findall(r"\| (NY federal|NY state|WA federal|WA state) \| \+[\d.]+ \| "
                      r"\*\*\+([\d.]+)\*\* \|", dn)
    if len(rows) != 4:
        raise SystemExit(
            f"FATAL: the eligible-for-all turnout table in the donor paper yielded "
            f"{len(rows)} of 4 panel rows. Finding 4's '+22.9 to +26.3 points across the "
            f"four panels' is a span over exactly those rows.")
    for lbl, v in rows:
        d["dn_gap_" + lbl.lower().replace(" ", "_")] = float(v)
    vals = [float(v) for _, v in rows]
    d["dn_gap_lo"], d["dn_gap_hi"] = min(vals), max(vals)

    # Finding 5 — roll-side unique-key matchability on the CURRENT key, both states.
    grab(dn, r"NY \*\*([\d.]+)–([\d.]+)%\*\* across the four bands \(([\d.]+)-pt spread",
         ("dn_pmatch_ny_lo", "dn_pmatch_ny_hi", "dn_pmatch_ny_spread"),
         where="the donor paper's match-bias section")
    grab(dn, r"WA \*\*([\d.]+)–([\d.]+)%\*\* across generations \(([\d.]+)-pt spread",
         ("dn_pmatch_wa_lo", "dn_pmatch_wa_hi", "dn_pmatch_wa_spread"),
         where="the donor paper's match-bias section")
    grab(dn, r"65\+ donor share goes ([\d.]+)% → \*\*([\d.]+)%\*\*",
         ("dn_ipw_ny_raw", "dn_ipw_ny_wtd"),
         where="the donor paper's inverse-propensity re-weighting")

    # Finding 5 — the crossover bound, FEDERAL panels, which is what now carries the claim.
    grab(dn, r"NY unaffiliated ([\d.]+)% against ([\d.]+)%; ID unaffiliated ([\d.]+)% "
             r"against ([\d.]+)%",
         ("dn_xo_ny_d", "dn_xo_ny_r", "dn_xo_id_d", "dn_xo_id_r"),
         where="the donor paper's unresolved-pool bound")

    # Domain 1 — participation. Newly scraped 2026-08-16: this domain sat OUTSIDE the audited
    # slice for as long as the document was a prospectus, so none of its figures was ever
    # gated, and two of them were quoted a decimal place finer than the owning paper prints.
    grab(wa, r"([\d.]+)M (?:individual )?(?:VRDB )?vote records",
         ("wa_vote_records_m",), where="the WA paper's data description")
    grab(wa, r"65 and older were ([\d.]+)%, ([\d.]+)%, and ([\d.]+)% of the 2021, 2023, and "
             r"2025 odd-year electorates, against ([\d.]+)% in 2024; voters 18–29 fell from "
             r"([\d.]+)% in 2024 to about ([\d.]+)% off-cycle",
         ("wa_p65_21", "wa_p65_23", "wa_p65_25", "wa_p65_24", "wa_p1829_24", "wa_p1829_off"),
         where="the WA paper's composition sentence")
    grab(wa, r"18–29 year old participation falls from \*\*([\d.]+)%\*\* \(2024\) to about "
             r"\*\*([\d.]+)%\*\* off-year, while 65\+ slips only from \*\*([\d.]+)%\*\* to "
             r"\*\*~([\d.]+)%\*\*",
         ("wa_r1829_24", "wa_r1829_off", "wa_r65_24", "wa_r65_off"),
         where="the WA paper's within-cohort rate sentence")

    # Finding 6 — the leverage sweep. The money paper derives, publishes and leads its own
    # abstract with this; the synthesis had headlined +0.515 without it, which is the single
    # clearest instance of the propagation problem this block exists to stop.
    grab(mp, r"runs from \*\*−([\d.]+)\*\* \(dropping WA-08 2018\) to \*\*\+([\d.]+)\*\* "
             r"\(dropping WA-03 2024\)",
         ("mp_loo_lo", "mp_loo_hi"), where="the money paper's leave-one-out sweep")
    grab(mp, r"\(\+\$([\d.]+)M\) with a \+([\d.]+)-point residual and carries a Cook's "
             r"distance of \*\*([\d.]+)\*\*",
         ("mp_cd08_net", "mp_cd08_resid", "mp_cd08_cook"),
         where="the money paper's WA-08 2018 leverage cell")
    grab(mp, r"dropping every WA-08 observation gives \*\*−([\d.]+)\*\*",
         ("mp_drop_all_cd08",), where="the money paper's drop-all-WA-08 figure")
    grab(mp, r"reported beside it: \*\*−([\d.]+) to \+([\d.]+)\*\*",
         ("mp_clust_lo", "mp_clust_hi"),
         where="the money paper's district-clustered bootstrap")

    # Finding 5 — the recipient-party resolution rates that decide which panel carries the
    # crossover claim. The synthesis states them to explain why it uses the federal panels.
    grab(dn, r"resolving ([\d.]+)% of ID and ([\d.]+)% of NY state matched donors",
         ("dn_res_id_state", "dn_res_ny_state"),
         where="the donor paper's unresolved-pool objection")
    grab(dn, r"where resolution is ([\d.]+)–([\d.]+)%",
         ("dn_res_fed_lo", "dn_res_fed_hi"),
         where="the donor paper's federal-panel resolution range")

    # The RETIRED Finding 6 pair. Held as explicit constants rather than scraped, because
    # they no longer exist in the owning paper — that is what "retired" means — and the note
    # that retires them has to keep quoting them accurately.
    # The two Domain 1 rates this document used to print more precisely than its own
    # source. Constants, because they exist nowhere else now.
    d["wp_retired_p65_lo"], d["wp_retired_p65_hi"] = 37.0, 40.0
    d["wp_retired_r1829_off"] = 15.8
    d["wp_retired_r65_off"] = 61.3
    d["money_r_fundraising_retired"] = 0.58
    d["money_holdout_alloc_retired"] = 0.02
    # The in-state share the nationalization item retires as an ingestion artifact. Held as
    # a constant for the same reason as the pair above: it exists nowhere else now, because
    # the ingest direction that produced it was corrected, and the note's whole job is to say
    # what the number WAS. Probed so it cannot be "corrected" into a current figure.
    d["wp_retired_instate_share"] = 93.6
    # Idaho's unaffiliated recipient-resolution rate, which decides whether that row can
    # carry a direction. Owned and asserted by verify_who_decides_id.py (xo_UNAFF_resolved_pct);
    # restated here because Finding 5 gives it as the reason the state panel is not used.
    d["id_state_xo_unaff_res"] = 39.0

    # Finding 2 — the OBSERVED four-state not-close shares, and WA's five-cycle range.
    for lbl, key in (("WA House 2024", "ss_wa"), ("NY Assembly 2022", "ss_ny"),
                     ("TX House 2024", "ss_tx"), ("ID House 2024", "ss_id")):
        grab(ss, r"\| " + lbl + r" \| [^|]*\| \*\*([\d.]+)%\*\*", (key,),
             where="the safe-seat paper's four-state lower-chamber table")
    # The two dimensions the safe-seat paper insists must not be merged, and which the
    # synthesis's own closing verdict had merged again until 2026-08-15.
    grab(ss, r"\(([\d.]+)%\) were not close .{0,60}?and \d+ \(([\d.]+)%\)",
         ("ss_wa24_notclose", "ss_wa24_no_dvr"),
         where="the safe-seat paper's WA 2024 headline")
    # WA's five-cycle range, which is why "trajectory: worsening" is withdrawn. Taken from
    # the per-cycle table rather than the rounded prose ("79-88%"), because the synthesis
    # prints one decimal and rounding a rounded range is how this project has been bitten.
    cyc = [float(x) for x in re.findall(
        r"\| 20(?:1[68]|2[024]) \| \d+ \| \d+ \| \d+ \| \d+ \| \d+ \| \d+ \| "
        r"\*\*([\d.]+)%\*\* \|", ss)]
    if len(cyc) != 5:
        raise SystemExit(
            f"FATAL: the safe-seat WA per-cycle table yielded {len(cyc)} of 5 cycles; "
            f"Finding 2's not-close range is a span over exactly those rows.")
    d["ss_wa_cycle_lo"], d["ss_wa_cycle_hi"] = min(cyc), max(cyc)

    # ---- "What the evidence does not support" — the nationalization result (2026-08-26) ---
    # This section reports the ONE blocked question that became answerable, and it does so by
    # quoting ten figures from cross-state-fec-money.md §E-I. It sat outside the scrape
    # window, so none was read. Scraped from the owning paper's own MATRIX ROWS rather than
    # from its prose, for the reason the safe-seat per-cycle scrape gives: the synthesis
    # prints these rounded to whole percent and rounding a rounded number is how this project
    # has been bitten.
    #
    # ⚠ A NEAR-MISS WORTH RECORDING. The synthesis gives "27% (WA) / 41% (NY) / 34% (TX) /
    # 53% (ID)" and the money paper has a sentence reading "(WA 41%, TX 45%, NY 53%)" —
    # overlapping digits, different state order, and it is NOT the same quantity: that
    # sentence is the SENATE-only out-of-state share, while the synthesis is quoting the
    # House+Senate inflow matrix's Rest-of-US column. Anchoring on the prose would have
    # produced a check that passed against the wrong row. Anchor on the table.
    infl = re.findall(r"\| \*\*(WA|NY|TX|ID)\*\* \| \$[\d.]+M \| \*?[\d.]+%\*? \| "
                      r"\*?\*?[\d.]+%\*?\*? \| \*?\*?([\d.]+)%\*?\*? \|", xs)
    if len(infl) != 8:
        raise SystemExit(
            f"FATAL: the cross-state money paper's two flow matrices yielded {len(infl)} of "
            "8 rows (4 inflow + 4 outflow). The synthesis's nationalization paragraph is a "
            "restatement of exactly those Rest-of-US cells; re-point this scrape.")
    for i, (st, rest) in enumerate(infl):
        d[f"xs_{'in' if i < 4 else 'out'}_{st.lower()}"] = float(rest)
    grab(xs, r"`fec_inflow\.duckdb`: \*\*([\d.]+)M contributions / \$([\d.]+)B\*\*",
         ("xs_inflow_rows_m", "xs_inflow_busd"),
         where="the cross-state money paper's Section E provenance line")
    grab(xs, r"Loeffler\) drew ~\$(\d+)M\*\* from residents", ("xs_georgia_musd",),
         where="the cross-state money paper's magnet list")


def _money_paper(d):
    """Cross-document: white-paper figures OWNED BY does-money-move-votes.md.

    The slope/r pair was here from the start. The fundraising correlation and the WA-03
    residual were added 2026-08-06 by the coverage gate, and the correlation FAILED: the
    white paper said +0.55 in three places while the owning paper says +0.58 and records
    +0.55 as the retired value of a frame that grew from 109 both-side finance cells to
    129. Drift into a restating document, which is the exact failure this script was
    written for, surviving because no probe pointed at it.
    """
    t = re.sub(r"\s+", " ", MONEY_PAPER.read_text(encoding="utf-8"))
    # The owning paper's slope sentence. It was NEGATIVE and single-cycle until
    # 2026-08-08, when a three-cycle backfill reversed the sign; the capture is
    # written to require an explicit sign rather than assuming one, so a future
    # reversal fails here instead of silently flipping a restated figure.
    m = re.search(r"the slope is \*\*\+([\d.]+) points of residual per \$1M net\s*"
                  r"pro-Democratic IE, with a 95% bootstrap interval of −([\d.]+) to "
                  r"\+([\d.]+) and Pearson r = \+([\d.]+)\*\*", t)
    if m:
        d["ie_slope"], d["ie_ci_lo"], d["ie_ci_hi"], d["ie_r"] = (
            float(m.group(1)), -float(m.group(2)), float(m.group(3)), float(m.group(4)))
        d["_ie_ci_lo_abs"] = abs(d["ie_ci_lo"])
    m = re.search(r"Across the (\d+) scorable district-cycles", t)
    if m:
        d["ie_n"] = int(m.group(1))
    # The state-legislative panel, added 2026-08-09 when the PDC C6.3 ingest
    # replaced the retired "no support/oppose flag" ceiling claim. Scraped from
    # the owning paper for the same reason the slope is: this document restates
    # figures it does not derive, and an unprobed restatement is how +0.55
    # survived here after the owning paper moved to +0.58.
    m = re.search(r"that yields \*\*(\d+) scorable district-cycles\*\*", t)
    if m:
        d["leg_n"] = int(m.group(1))
    # The sign range comes from the owning paper's TABLE, not its abstract: the
    # abstract rounds to one decimal ("−3.8 to +4.9") and this document prints
    # three, so scraping the abstract would compare 3.8 against 3.816 and fail
    # on a rounding difference rather than on drift.
    m = re.search(r"\| all directional, race-matched \| \d+ \| \d+ \| −([\d.]+) \|", t)
    if m:
        d["leg_slope_lo_abs"] = float(m.group(1))
    m = re.search(r"\| \*\*express advocacy, race-matched\*\* \| \d+ \| \d+ \| \*\*\+([\d.]+)\*\* \|", t)
    if m:
        d["leg_slope_hi"] = float(m.group(1))
    # RE-ANCHORED 2026-08-15. The money paper's competing-correlations table gained a second
    # column (full sample n=163 against the finance-complete common sample n=128), so the old
    # single-capture pattern stopped matching and the derivation went UNAVAILABLE — which the
    # gate reported as a failure, correctly. The value moved with it: +0.58 -> +0.60. Both
    # columns now read +0.60, and the FULL-SAMPLE column is the one taken, because that is the
    # sample the white paper's sentence describes.
    m = re.search(r"\| \*\*fundraising, log2\(D receipts / R receipts\)\*\* \| "
                  r"\*\*\+([\d.]+)\*\*", t)
    if m:
        d["money_r_fundraising"] = float(m.group(1))
    m = re.search(r"\| \*\*cd03 / 24\*\* \| \*\*\+\$[\d.]+M\*\* \| \*\*\$[\d.]+M\*\* \| "
                  r"\*\*\+([\d.]+)\*\* \|", t)
    if m:
        d["money_wa03_resid"] = float(m.group(1))
    # The allocation-alone cross-cycle holdout cell. Added 2026-08-06 when the white paper
    # stopped saying "~0.00" — the owning paper's cell is 0.022, which rounds to 0.02, so
    # the tilde was rounding a number DOWN to a different claim. Scraped rather than
    # constant so that a re-pin of the money paper's holdout block moves both documents.
    # RE-ANCHORED 2026-08-15, same cause: the holdout block was rebuilt and the cell no longer
    # carries the "*(r = ...)" suffix the old anchor keyed on. The value moved 0.022 -> 0.028,
    # which matters for the prose: 0.022 rounds to 0.02 and 0.028 rounds to 0.03, so the white
    # paper's "R^2 of 0.02" was a stale figure AND a stale rounding.
    m = re.search(r"\| allocation shares alone \| ([\d.]+) \|", t)
    if m:
        d["money_holdout_alloc"] = float(m.group(1))
    # The pre-election cutoff pair (2026-08-29): scraped from the owning paper's Finding 1
    # restatement so a re-pin of fec_receipts_preelection_2026-08-29.csv moves both
    # documents. verify_money_votes.py derives the pair from the pins; this document only
    # restates it. RE-ANCHORED the same day: the owner adopted the authorized-committee
    # universe and the "essentially unchanged" framing after a referee pass.
    m = re.search(r"correlation is essentially unchanged — \*\*\+([\d.]+)\*\* against "
                  r"\*\*\+([\d.]+)\*\*\s*full-cycle on the same\s*report-built basis", t)
    if m:
        d["money_pre_r"] = float(m.group(1))
        d["money_fullrep_r"] = float(m.group(2))


def _finding3(d):
    """Finding 3's whale-vs-retail cut, gated 2026-08-10.

    WHY THIS EXISTS. `docs/reference/withdrawn_claims.csv` recorded the retired "Gini ~0.61"
    claim as `enforcement: unpatternable ... Guarded by verify_whitepaper.py asserting 0.578`.
    That was false: no verifier asserted 0.578, `forbidden_pattern` was empty, and Finding 3
    was not a gated section — so the withdrawn claim had no guard of any kind and its
    replacement figures had no probe. Second instance in this repo of a control documented as
    working that did not exist (CLAUDE.md, 2026-08-01). This function makes the register's
    sentence true.

    POPULATION, declared because it is not the matched panel every other finding here uses:
    recipient-CYCLES over `individual_contributions`, keyed `(fec_candidate_id, election_cycle)`
    and split by money system on the `PDC:` id prefix, restricted to those with >=100 distinct
    (name, zip5) donors. Positive amounts only. Gini is the same estimator the rest of the
    series uses. `pooled` is a genuinely separate grouping — one key per recipient-cycle across
    BOTH systems — so it is NOT the sum of the two: a recipient-cycle under the threshold in
    each system alone can clear it pooled. The paper's own 822 + 1,989 != 2,814 is that, not
    an arithmetic slip.

    These are LIVE reads. The 2026 PDC cycle is still accruing (audit log section 0), so every
    count here drifts upward and a mismatch means "re-read the paper's cell", not "fix the
    tolerance".
    """
    wa = duckdb.connect(str(DATA / "wa_statewide.duckdb"), read_only=True)
    sysexpr = "CASE WHEN contribution_id LIKE 'PDC:%' THEN 'state' ELSE 'federal' END"
    donor = "UPPER(TRIM(contributor_name))||'|'||LEFT(COALESCE(contributor_zip,''),5)"
    wa.execute(f"""CREATE TEMP TABLE _f3 AS
        WITH g AS (
          SELECT fec_candidate_id rid, election_cycle ec, {sysexpr} sys,
                 {donor} donor, SUM(contribution_amount) tot
          FROM individual_contributions WHERE contribution_amount > 0
          GROUP BY 1, 2, 3, 4),
        r AS (SELECT *, ROW_NUMBER() OVER (PARTITION BY rid, ec, sys ORDER BY tot) rn FROM g)
        SELECT sys, COUNT(*) ndonors,
               (2.0*SUM(rn*tot)/(COUNT(*)*SUM(tot))) - (COUNT(*)+1.0)/COUNT(*) gini
        FROM r GROUP BY rid, ec, sys HAVING COUNT(*) >= 100""")
    for sys, n, gini in wa.execute(
            "SELECT sys, COUNT(*), MEDIAN(gini) FROM _f3 GROUP BY 1").fetchall():
        d[f"whale_n_{sys}"] = int(n)
        d[f"whale_gini_{sys}"] = float(gini)
    d["whale_n_pooled"], = wa.execute(f"""
        SELECT COUNT(*) FROM (
          SELECT rid, ec FROM (
            SELECT fec_candidate_id rid, election_cycle ec, {donor} donor
            FROM individual_contributions WHERE contribution_amount > 0
            GROUP BY 1, 2, 3)
          GROUP BY 1, 2 HAVING COUNT(*) >= 100)""").fetchone()
    d["whale_state_share"] = 100.0 * d["whale_n_state"] / d["whale_n_pooled"]
    # Only the keys a probe consumes are stored. `whale_max_state` in dollars and the state
    # median are held locally: a derived-and-never-read key is the `e3938bd` shape, and the
    # probe-mutation roster holds this verifier's no-probe count as a ceiling that may only
    # fall, so an unprobed intermediate would raise it.
    med, mx = {}, {}
    for sys, m, x in wa.execute(f"""
            SELECT {sysexpr} sys, MEDIAN(contribution_amount), MAX(contribution_amount)
            FROM individual_contributions WHERE contribution_amount > 0
            GROUP BY 1""").fetchall():
        med[sys], mx[sys] = float(m), float(x)
    # The paper claims the $25 median holds "in both money systems". That is a structural
    # invariant of the sentence, not a figure with its own cell, so it hard-stops here rather
    # than being carried as a second probed key that restates the first.
    if med["federal"] != med["state"]:
        raise AssertionError(
            f"Finding 3 says the median itemized gift is the same in both money systems; "
            f"federal is ${med['federal']:,.0f} and state ${med['state']:,.0f}. Fix the "
            f"sentence — it can no longer say 'in both money systems'.")
    d["whale_median_gift_federal"] = med["federal"]
    d["whale_max_federal"] = mx["federal"]
    d["whale_max_state_m"] = mx["state"] / 1e6
    wa.execute("DROP TABLE _f3")
    wa.close()


def derive():
    d = {}
    wa = duckdb.connect(str(DATA / "wa_statewide.duckdb"), read_only=True)
    wa.execute(f"ATTACH '{DATA / 'wa_vrdb.duckdb'}' AS vrdb (READ_ONLY)")
    # The pooled panel is LIVE — `main.py analyze` rebuilds it and new contribution loads
    # grow it — while every Finding 5 figure below was derived on the published 314,974-voter
    # panel. Guard it up front with the mechanism named (P5, closed 2026-08-15; same
    # discipline as F5_PINNED_PANEL_N in verify_cross_state_money.py): a drifted panel must
    # read as "the panel moved — re-derive and re-pin deliberately", never as a paper defect.
    n_pooled, = wa.execute("SELECT COUNT(*) FROM voter_donor_affiliation").fetchone()
    if n_pooled != 314_974:
        raise AssertionError(
            f"WA pooled panel holds {n_pooled:,} voters against the published 314,974 — "
            "voter_donor_affiliation has been rebuilt since Finding 5's figures were derived. "
            "Re-derive the whitepaper's Finding 5 block and update this guard deliberately.")
    for tag, tbl in (("pooled", "voter_donor_affiliation"),
                     ("fed", "voter_donor_affiliation_fec"),
                     ("state", "voter_donor_affiliation_state")):
        for k, v in _conc(wa, tbl).items():
            d[f"wa_{tag}_{k}"] = v
    for tag, tbl in (("pooled", "voter_donor_affiliation"), ("fed", "voter_donor_affiliation_fec")):
        for g, m in _multipliers(wa, tbl).items():
            d[f"wa_{tag}_mult_{g}"] = m
    d["wa_pooled_zip3"] = _zip3_top2(wa, "voter_donor_affiliation")
    d["wa_fed_zip3"] = _zip3_top2(wa, "voter_donor_affiliation_fec")
    ipw, pm_lo, pm_hi = _ipw(wa)
    # RAW and INVERSE-PROPENSITY-REWEIGHTED multipliers, ALL FIVE GENERATIONS, because the
    # sentence they answer says "every Washington generation multiplier is unchanged to two
    # decimal places in both panels" (Finding F, the matcher-artifact objection). Read by
    # `claim_guards`, which is the only thing that can check that sentence: a claim of
    # INVARIANCE carries no numeric token for a probe to capture or the coverage audit to
    # see, and the one digit in it ("two") is waived by the small-integer rule.
    #
    # ⚠ THESE KEYS WERE DEAD UNTIL 2026-08-24. Two were added to probe a "1.96 → 1.91×"
    # arrow that has since been removed from the paper -- 0 occurrences of "1.91", "IPW" or
    # "inverse-propensity" remain -- so they were derived, described in a comment as probed,
    # and consumed by nothing. Found by the no-probe triage
    # (scripts/diag_triage_no_probe_keys.py); this is the fix. Storing only Silent and Gen Z
    # would under-check a claim that says "every".
    for _g in GENS:
        d[f"wa_raw_{_g}"], d[f"wa_ipw_{_g}"] = ipw[_g][0], ipw[_g][1]
    # The FEDERAL panel too, because the sentence says "in both panels". pm_lo/pm_hi are a
    # property of the ROLL, not the panel, so they are taken from the pooled call only.
    _ipw_fed, _, _ = _ipw(wa, "voter_donor_affiliation_fec")
    for _g in GENS:
        d[f"wafed_raw_{_g}"], d[f"wafed_ipw_{_g}"] = _ipw_fed[_g][0], _ipw_fed[_g][1]
    # The largest movement in EITHER panel. Printed, so the paper states a measured maximum
    # rather than a threshold nobody checks -- the sentence used to claim invariance to two
    # decimal places, which was false in six of ten cells.
    d["wa_ipw_max_move"] = max(abs(a - b) for _p in (ipw, _ipw_fed)
                               for a, b in (_p[_g] for _g in GENS))
    d["wa_pmatch_lo"], d["wa_pmatch_hi"] = pm_lo, pm_hi
    # The all-tier federal top-1% the F2 line records as its own superseded value. Derived
    # rather than exempted: the retained _alltier snapshot reproduces it to the digit
    # (42.444 -> 42.4), so the withdrawal note is checkable and not just asserted.
    d["wa_fed_alltier_top1"] = _conc(wa, "voter_donor_affiliation_fec_alltier")["top1"]
    _scale(wa, d)
    d.update({f"wa_{k}": v for k, v in _turnout(wa).items()})
    wa.close()
    _inventory(d)
    _ledger_mean(d)
    _backtest(d)

    ny = _party_and_age("ny", "CASE WHEN v.party IN ('DEM','D') THEN 'DEM' ELSE 'X' END", "DEM",
                        dem_pred="IN ('DEM','D')")
    d.update({f"ny_{k}": v for k, v in ny.items()})
    idd = _party_and_age("id", "CASE WHEN v.party='DEM' THEN 'DEM' ELSE 'X' END", "DEM")
    d.update({f"id_{k}": v for k, v in idd.items()})

    # Recall cost of the primary specification, quoted in Finding 5 as "11-19%".
    losses = []
    for st, tbls in (("wa", ("fec", "state")), ("ny", ("fec", "state")), ("id", ("fec", "state"))):
        c = duckdb.connect(str(DATA / f"{st}_statewide.duckdb"), read_only=True)
        for t in tbls:
            try:
                a, = c.execute(f"SELECT COUNT(*) FROM voter_donor_affiliation_{t}_alltier").fetchone()
                p, = c.execute(f"SELECT COUNT(*) FROM voter_donor_affiliation_{t}").fetchone()
                losses.append(100.0 * (a - p) / a)
            except Exception:  # noqa: BLE001
                pass
        c.close()
    if losses:
        d["discard_lo"], d["discard_hi"] = min(losses), max(losses)

    # Finding 5's "share of voters", RESTATED 2026-08-06 on the author's basis call: matched
    # donors on the POOLED panel over ALL registrants in that state's voter file. The retired
    # "~3.5-6%" matched no panel x denominator combination — enumerated in full before the
    # figure was touched, WA shown because it is the widest end of the range:
    #
    #                       pooled  federal  state  pooled_alltier
    #   voter_scores ld      5.75%    2.70%   3.97%      6.99%
    #   donor_paper_wa_roll  5.77%    2.71%   3.98%      7.00%   (the pin)
    #   vrdb.voters all      5.71%    2.68%   3.94%      6.93%   <- the basis now printed
    #   vrdb.voters active   6.18%    2.90%   4.26%      7.50%
    #   super-voters only   10.85%    5.09%   7.48%     13.17%
    #
    # Pin-vs-live cannot move what is printed (5.77 and 5.71 both round to 5.7); ACTIVE-vs-all
    # can, and would give 4.0-6.2. Idaho's extract carries no active flag, so its two bases
    # coincide by construction. Derived per state rather than transcribed, so the range and
    # its three members can never disagree with each other the way the old one did.
    for st in ("wa", "ny", "id"):
        c = duckdb.connect(str(DATA / f"{st}_statewide.duckdb"), read_only=True)
        c.execute(f"ATTACH '{DATA / (st + '_vrdb.duckdb')}' AS vr (READ_ONLY)")
        n, = c.execute("SELECT COUNT(DISTINCT state_voter_id) "
                       "FROM voter_donor_affiliation").fetchone()
        roll, = c.execute("SELECT COUNT(*) FROM vr.voters").fetchone()
        d[f"{st}_donor_share"] = 100.0 * n / roll
        c.close()
    _sh = [d[f"{st}_donor_share"] for st in ("wa", "ny", "id")]
    d["donor_share_lo"], d["donor_share_hi"] = min(_sh), max(_sh)

    # Occupation blocs (Finding 5) — an OUTFLOW cut over individual_contributions on the
    # paper's own federal filter, not the matched layer above. Different population; that
    # is why it needs its own query rather than reusing the panel.
    wa = duckdb.connect(str(DATA / "wa_statewide.duckdb"), read_only=True)
    filt = ("regexp_matches(COALESCE(fec_candidate_id,''),'^[CPHS][0-9]') "
            "AND contributor_state='WA' AND contribution_amount>0")
    for key, needle in (("retired", "retired"), ("notemp", "not employed")):
        m, pct = wa.execute(f"""
            SELECT SUM(contribution_amount) FILTER (WHERE contributor_occupation ILIKE '%{needle}%')/1e6,
                   100.0*SUM(contribution_amount) FILTER (WHERE contributor_occupation ILIKE '%{needle}%')
                       /SUM(contribution_amount)
            FROM individual_contributions WHERE {filt}""").fetchone()
        d[f"occ_{key}_m"], d[f"occ_{key}_pct"] = float(m), float(pct)
    wa.close()

    _finding3(d)
    _bootstrap(d)
    # Not a paper defect and not tolerance-absorbable: Finding 6's IE figures are
    # unmeasurable until the rows are re-loaded. Surfaced as a gate failure with
    # the repair command rather than as a traceback.
    try:
        _finding6(d)
        _companions(d)
    except StaleIEData as exc:
        print("\nIE DERIVATION BLOCKED — Finding 6's IE figures are not verifiable.\n")
        print(exc)
        raise SystemExit(1) from None
    _money_paper(d)
    # The prose writes "−0.39"; the capture group yields "0.39". Compare magnitudes.
    # The negated aliases existed because the money paper's slope and r were both
    # NEGATIVE and the white paper printed the minus sign as prose, outside the
    # capture group. Both are positive since the 2026-08-08 backfill, so the
    # aliases are gone rather than kept as an identity — a "_neg_" name holding a
    # positive number is how a sign error survives review.
    return d


# ------------------------------------------------------------------------------ the probes
# (label, regex over the normalised Findings 4-5 text, derived key(s), tolerance)
PROBES = [
    # ---- "Data, and what each state can actually support" (gated 2026-08-26) -------------
    # The paragraph these sit under says every count in it is "a live read that drifts". It
    # was right, and until this block existed nothing read them. See _inventory for the three
    # bases and for what the 36.1M -> 36.0M correction was.
    ("inventory — WA precinct rows and the elections they span",
     r"~([\d.]+)M precinct-result rows across (\d+) elections",
     ("inv_wa_precinct_m", "inv_wa_elections"), 0.05),
    ("inventory — WA contributions, rows and dollars",
     r"\*\*([\d.]+)M individual\s+contributions, \$([\d.]+)B\*\*",
     ("inv_wa_contrib_rows_m", "_inv_wa_contrib_busd"), 0.05),
    ("inventory — WA federal and state dollar layers",
     r"\(FEC `\$([\d.]+)M` \+ state PDC `\$([\d.]+)M`",
     ("inv_wa_fed_musd", "inv_wa_state_musd"), 0.05),
    ("inventory — WA voter-score rows and distinct voters",
     r"~([\d.]+)M voter-score rows \(one per voter per district scope,\s*~([\d.]+)M distinct voters\)",
     ("inv_wa_vs_m", "inv_wa_voters_m"), 0.05),
    ("inventory — WA VRDB vote records",
     r"~([\d.]+)M individual VRDB vote records", "inv_wa_vrdb_hist_m", 0.05),
    ("inventory — four-state federal layer",
     r"\*\*([\d.]+)M contribution rows / \$([\d.]+)B\*\* of\s+resident-donor outflow",
     ("inv_fed_rows_m", "inv_fed_busd"), 0.05),
    ("inventory — per-state federal rows and dollars",
     r"\(WA ([\d.]+)M/\$([\d.]+)M · NY ([\d.]+)M/\$([\d,.]+)M · TX ([\d.]+)M/\$([\d,.]+)M ·\s*"
     r"ID ([\d.]+)M/\$([\d.]+)M\)",
     ("inv_wa_fed_rows_m", "inv_wa_fed_musd", "inv_ny_fed_rows_m", "inv_ny_fed_musd",
      "inv_tx_fed_rows_m", "inv_tx_fed_musd", "inv_id_fed_rows_m", "inv_id_fed_musd"), 0.05),
    # The corrected total AND the row count the correction note retires, as a pair — same
    # discipline as the Finding 6 correction-note probes: a note that retires a figure has to
    # keep stating it, and the live sentence has to keep stating the derived one, so a later
    # drift cannot make the two agree by moving the wrong one.
    ("inventory — federal plus state layers, all four states",
     r"takes it to \*\*([\d.]+)M rows /\s*\$([\d.]+)B\*\*", ("inv_all_rows_m", "inv_all_busd"),
     0.05),
    ("inventory — the retired plain row count, as the correction note states it",
     r"This read \"([\d.]+)M\" until 2026-08-26", "inv_star_rows_m", 0.05),
    ("inventory — the two bases, side by side in the correction note",
     r"their sum is ([\d.]+)M; ([\d.]+)M was a plain row\s+count",
     ("inv_all_rows_m", "inv_star_rows_m"), 0.05),
    ("inventory — the API-loaded rows the 36.1M count had swept in",
     r"picks up ([\d,]+) rows loaded from the FEC \*\*API\*\*", "inv_api_extra", 0),
    # "on either basis" is an equality claim, so BOTH bases are asserted against the one
    # printed digit. Stating it and checking only the basis you kept is how a claim of
    # agreement survives the two sides diverging.
    ("inventory — dollar total, layer basis",
     r"dollar total is \$([\d.]+)B on either basis", "inv_all_busd", 0.005),
    ("inventory — dollar total, plain-row-count basis (the same printed digit)",
     r"dollar total is \$([\d.]+)B on either basis", "inv_star_busd", 0.005),
    ("inventory — matched panels, quoted per panel",
     r"WA federal ([\d,]+) / state ([\d,]+); NY federal\s*([\d,]+) / state ([\d,]+); "
     r"ID federal ([\d,]+) / state ([\d,]+)",
     ("inv_wa_panel_fed", "inv_wa_panel_state", "inv_ny_panel_fed", "inv_ny_panel_state",
      "inv_id_panel_fed", "inv_id_panel_state"), 0),
    ("inventory — the pooled figure it names as retired",
     r"The pooled ([\d,]+) WA figure", "wa_pooled_n", 0),
    ("inventory — support table, WA vote records and NY roll",
     r"\*\*measured\*\* \(([\d.]+)M vote records, birthdate\) \| \*\*measured\*\* "
     r"\(([\d.]+)M roll, year of birth\)",
     ("inv_wa_vrdb_hist_m", "inv_ny_roll_m"), 0.05),
    ("inventory — support table, the campaign-effects cell counts",
     r"\*\*measured\*\* \((\d+) federal \+ (\d+) state cells\)", ("ie_n", "leg_n"), 0),

    # ---- "What the evidence does not support" (gated 2026-08-26) -------------------------
    # The nationalization result, restated from cross-state-fec-money.md §E-I. Tolerance is
    # 0.5 on the whole-percent cells because the synthesis rounds the owning paper's one
    # decimal: 26.7 -> 27, 34.2 -> 34, 53.3 -> 53. That is a rounding the synthesis is
    # entitled to make; what it is not entitled to do is round to a DIFFERENT integer than
    # the current cell, which is what this catches.
    ("limits — inflow Rest-of-US share, all four states",
     r"inflow level: \*\*(\d+)% \(WA\) / (\d+)% \(NY\) / (\d+)% \(TX\) / (\d+)% \(ID\)\*\*",
     ("xs_in_wa", "xs_in_ny", "xs_in_tx", "xs_in_id"), 0.5),
    ("limits — outflow Rest-of-US share, the three named in the sentence",
     r"\(ID (\d+)% — the most — NY (\d+)%, WA ([\d.]+)%\)", ("xs_out_id", "xs_out_ny",
                                                             "xs_out_wa"), 0.5),
    ("limits — outflow, the Texas cell the sentence contrasts",
     r"\*\*Texas sends (\d+)%\*\*", "xs_out_tx", 0.5),
    ("limits — the recipient-anchored inflow dataset",
     r"dataset \(([\d.]+)M gifts / \$([\d.]+)B, all-state donors",
     ("xs_inflow_rows_m", "xs_inflow_busd"), 0.005),
    ("limits — Georgia Senate, the magnet-list anecdote",
     r"Georgia Senate races alone drew ~\$(\d+)M", "xs_georgia_musd", 0.5),
    # The BACKTEST, pinned 2026-08-26 (see _backtest). Previously declared in UNCHECKED with
    # the model-version question written out; a re-run settled it, so it is asserted now.
    ("limits — the backtest, live sentence",
     r"MAE ([\d.]+), (\d+)% directional\s+across (\d+) district-cycles\*\*, bias \+([\d.]+), "
     r"95% interval covering (\d+)%",
     ("bt_mae_margin", "bt_directional_accuracy", "bt_cells_valid", "bt_systematic_bias",
      "bt_ci_coverage_95"), 0.05),
    ("limits — the backtest, restated in the withdrawal note",
     r"(\d+) valid cells of 236 attempted \(73 skipped\), MAE ([\d.]+), (\d+)% directional, "
     r"bias \+([\d.]+), CI coverage (\d+)%",
     ("bt_cells_valid", "bt_mae_margin", "bt_directional_accuracy", "bt_systematic_bias",
      "bt_ci_coverage_95"), 0.05),
    ("limits — the in-state share the item retires as an ingestion artifact",
     r"The earlier \"([\d.]+)% in-state\"", "wp_retired_instate_share", 0.05),

    # ---- Conclusion and appendices (gated 2026-08-26) ------------------------------------
    # Everything here is a RESTATEMENT of a figure owned earlier in this paper or by a
    # companion, which is the one surface this file was built to guard and the one it could
    # not see until the scrape window became the whole document. The Conclusion's own
    # correction note records what that cost: a false "most seats are uncontested" verdict
    # shipped "outside every coverage span, while the finding that corrects it was gated".
    ("conclusion — the safe-seat shares, restated in the closing verdict's correction note",
     r"\*\*([\d.]+)%\*\* of seats were not close and \*\*([\d.]+)%\*\* offered no D-v-R",
     ("ss_wa24_notclose", "ss_wa24_no_dvr"), 0.05),
    ("conclusion — the two voter files, by roll size",
     r"NYSVOTER FOIL, ([\d.]+)M\) and ID \(SoS statewide file, ([\d.]+)M\)",
     ("inv_ny_roll_m", "inv_id_roll_m"), 0.005),
    # Appendix A's "and never re-run" sentence contrasts the 2026-06-27 data description with
    # TODAY's. The historical half cannot be re-derived — that is the point of the sentence —
    # but the CURRENT half is the inventory section restated 40,000 characters later, and a
    # restated inventory is exactly what drifts. Probed against the same keys, so the two
    # cannot disagree.
    ("appendix A — the current data description, restated against the inventory",
     r"against (\d+), \$([\d.]+)B \(Washington\) and ([\d.]+)M today",
     ("inv_wa_elections", "_inv_wa_contrib_busd", "inv_wa_vs_m"), 0.05),
    # The ledger's own arithmetic. The paragraph above the table says the published 22/100
    # "cannot be recomputed from the table below, which gives an unweighted mean of 18.3" —
    # a claim ABOUT the table, checkable from the table and from nothing else. Derived by
    # parsing the ten Failure cells rather than transcribed, so editing a cell moves it.
    ("appendix A — unweighted mean of the ledger's failure column",
     r"unweighted mean of (\d+\.\d+)", "ledger_mean", 0.05),
    ("appendix B — fundraising correlation, restated in the money-series summary",
     r"strongest single correlate of overperformance \(\+([\d.]+)\)",
     "money_r_fundraising", 0.005),
    ("appendix B — allocation squared holdout correlation, restated in the money-series summary",
     # RE-ANCHORED 2026-08-29: the paper stopped calling this quantity "holdout R²" —
     # the owning paper corrected the name to "squared holdout correlation" and the
     # synthesis had kept the old label (an external referee's catch). \s+ because the
     # restatement wraps mid-phrase.
     r"allocation squared\s+holdout correlation ([\d.]+)", "money_holdout_alloc", 0.005),
    ("appendix B — the two directional panels, restated in the money-series summary",
     r"run across (\d+) federal district-cycles and a further (\d+)\s+state-legislative ones",
     ("ie_n", "leg_n"), 0),

    # RE-POINTED 2026-08-15. These five probes used to sit on live claims; the claims are
    # retired and the figures now appear only inside the notes that retire them. Keeping the
    # probes there is deliberate: a retired figure quoted wrongly is still a defect, and the
    # note's whole job is to say what the number WAS.
    ("pooled matched voters (retirement note)",
     r"the \*\*pooled\*\* ([\d,]+)-voter match", "wa_pooled_n", 0),
    ("pooled matched voters (F2 retirement note)",
     r"on the pooled ([\d,]+) match, top-1%", "wa_pooled_n", 0),
    # NB there is a third restatement of this figure, in the Data-provenance block. That
    # comment used to end "which these probes cannot reach: they run over the Findings 3-6
    # slice only" — true when the scrape window was a regex slice, false since 2026-08-26.
    # The window is the whole document now, and that restatement has its own probe
    # ("inventory — the pooled figure it names as retired") rather than relying on wording
    # these two anchors do not match.
    ("super-voter donor / non-donor % (retirement note)",
     r"\"([\d.]+)% are super-voters vs ([\d.]+)%\"", ("wa_super_d", "wa_super_n"), 0.05),
    ("Finding 4 — the eligible-for-all age-standardized gap that REPLACED the super-voter cut",
     r"turnout gap runs \*\*\+([\d.]+) to \+([\d.]+) points\*\*",
     ("dn_gap_lo", "dn_gap_hi"), 0.05),
    ("Finding 4 — the four panel rows behind that span",
     r"NY federal \+([\d.]+), NY state \+([\d.]+), WA federal \+([\d.]+), WA state \+([\d.]+)",
     ("dn_gap_ny_federal", "dn_gap_ny_state", "dn_gap_wa_federal", "dn_gap_wa_state"), 0.05),
    ("turnout propensity donor / non-donor (retirement note)",
     r"propensity \*\*([\d.]+) vs ([\d.]+)\*\*", ("wa_prop_d", "wa_prop_n"), 0.0005),
    ("super-voter ratio (retirement note)",
     r"a ratio of \*\*([\d.]+)×\*\*", "wa_ratio", 0.005),
    ("federal panel donors / top-1% / Gini",
     r"\*\*federal\*\* ([\d,]+) donors / top-1% \*\*([\d.]+)%\*\* / Gini \*\*([\d.]+)\*\*",
     ("wa_fed_n", "wa_fed_top1", "wa_fed_gini"), 0.05),
    ("state panel donors / top-1% / Gini",
     r"\*\*state\*\* ([\d,]+) / \*\*([\d.]+)%\*\* / \*\*([\d.]+)\*\*",
     ("wa_state_n", "wa_state_top1", "wa_state_gini"), 0.05),
    # --- 3c's defensible claim, RE-ANCHORED 2026-08-29: the claim now leads with the
    # federal panel and demotes the superseded pooled figures to trailing context (an
    # external referee found the synthesis still headlining pooled figures its own panel
    # note supersedes). Every number is unchanged; the ORDER swapped, so the two probes
    # whose regex survived the reorder ("top 10%") swap their key tuples — binding the
    # first group to the pooled key after the reorder would fail on a real distinction.
    ("federal generation multipliers (3c lead)",
     r"WA federal panel: Silent \*\*([\d.]+)×\*\*, Boomer \*\*([\d.]+)×\*\* over-represented; "
     r"Gen Z \*\*([\d.]+)×\*\*,\s*Millennial \*\*([\d.]+)×\*\*",
     ("wa_fed_mult_Silent", "wa_fed_mult_Boomer", "wa_fed_mult_Gen Z",
      "wa_fed_mult_Millennial"), 0.005),
    ("pooled generation multipliers (superseded, trailing)",
     r"— ([\d.]+)× / ([\d.]+)× / ([\d.]+)× / ([\d.]+)× on the superseded\s+pooled basis",
     ("wa_pooled_mult_Silent", "wa_pooled_mult_Boomer", "wa_pooled_mult_Gen Z",
      "wa_pooled_mult_Millennial"), 0.005),
    ("two-ZIP3 share, federal (3c lead)",
     r"\*\*([\d.]+)% of WA federal donor\s+dollars", "wa_fed_zip3", 0.05),
    ("two-ZIP3 share, pooled (trailing)",
     r"two Seattle-metro ZIP3s\*\*; ([\d.]+)% pooled", "wa_pooled_zip3", 0.05),
    ("two-ZIP3 share, pooled (F2 retirement note)",
     r"and \*\*([\d.]+)%\*\* of dollars from two Seattle ZIP3s", "wa_pooled_zip3", 0.05),
    ("two-ZIP3 share, federal (F2 restatement)",
     r"two-ZIP3 share \*\*([\d.]+)%\*\*", "wa_fed_zip3", 0.05),
    ("top-1% federal then pooled",
     r"supply \*\*([\d.]+)%\*\* of matched dollars on the federal panel,\s+"
     r"\*\*([\d.]+)%\*\* pooled",
     ("wa_fed_top1", "wa_pooled_top1"), 0.05),
    ("top-10% federal / pooled",
     r"top 10% \*\*([\d.]+)%\*\* / \*\*([\d.]+)%\*\*", ("wa_fed_top10", "wa_pooled_top10"), 0.05),
    ("pooled top-1% / top-10% / Gini (F2 retirement note)",
     r"top-1% \*\*([\d.]+)%\*\*, top-10%\s*\*\*([\d.]+)%\*\*, Gini ([\d.]+)",
     ("wa_pooled_top1", "wa_pooled_top10", "wa_pooled_gini"), 0.05),
    ("federal top-1% (F2 restatement)",
     r"federal panel top-1% \*\*([\d.]+)%\*\*", "wa_fed_top1", 0.05),
    ("federal Gini (F2 restatement)",
     r"federal panel top-1% \*\*[\d.]+%\*\* \[[\d.–-]+\], Gini \*\*([\d.]+)\*\*",
     "wa_fed_gini", 0.0005),
    ("state Gini (F2 restatement)",
     r"state panel top-1% \*\*[\d.]+%\*\* \[[\d.–-]+\], Gini \*\*([\d.]+)\*\*",
     "wa_state_gini", 0.0005),
    ("state top-1% (F2 restatement)",
     r"state panel top-1% \*\*([\d.]+)%\*\*", "wa_state_top1", 0.05),
    ("Finding 5 — roll-side matchability on the CURRENT key, both states",
     r"\*\*NY ([\d.]+)–([\d.]+)%\*\* \(([\d.]+)-pt spread\), \*\*WA ([\d.]+)–([\d.]+)%\*\* "
     r"\(([\d.]+)-pt spread\)",
     ("dn_pmatch_ny_lo", "dn_pmatch_ny_hi", "dn_pmatch_ny_spread",
      "dn_pmatch_wa_lo", "dn_pmatch_wa_hi", "dn_pmatch_wa_spread"), 0.05),
    ("Finding 5 — the retired key's matchability, quoted in the correction note",
     r"quoted\s*\*\*([\d.]+)%–([\d.]+)%\*\* matchability, which is the \*retired\*",
     ("wa_pmatch_lo", "wa_pmatch_hi"), 0.05),
    ("Finding 5 — the re-weighting moves nothing, NY 65+ donor share",
     r"65\+ donor share goes ([\d.]+)% → \*\*([\d.]+)%\*\*",
     ("dn_ipw_ny_raw", "dn_ipw_ny_wtd"), 0.05),
    ("federal multipliers restated in the panel note",
     r"on the federal panel \(Silent \*\*([\d.]+)×\*\*,\s*Gen Z \*\*([\d.]+)×\*\*\)",
     ("wa_fed_mult_Silent", "wa_fed_mult_Gen Z"), 0.005),
    # The re-weighting movement, printed 2026-08-24 in place of a false invariance claim.
    ("Finding F — the largest re-weighting movement and the two cells the paper names",
     r"moves by more than \*\*([\d.]+)\*\*, the largest being Silent on the federal\s+"
     r"panel \(\*\*([\d.]+)\*\* → \*\*([\d.]+)\*\*\)",
     ("wa_ipw_max_move", "wafed_raw_Silent", "wafed_ipw_Silent"), 0.005),
    ("Finding F — Gen X crossing parity on the federal panel",
     r"crosses it on the federal panel\s+\(\*\*([\d.]+)\*\* → \*\*([\d.]+)\*\*\)",
     ("wafed_raw_Gen X", "wafed_ipw_Gen X"), 0.005),
    ("federal top-1% restated in the withdrawal note",
     r"contradicting the ([\d.]+)% in the panel note", "wa_fed_top1", 0.05),
    # RE-POINTED 2026-08-15: the "ID crossover and 51.3% figures are the state-money layer"
    # caveat went with the crossover rewrite, which moved that claim to the federal panels.
    # The 51.3% itself is still printed in the age-skew list, so the check moves there.
    ("ID state 65+ share, in the age-skew list",
     r"ID state\s*\*\*([\d.]+)%\*\*", "id_state_65", 0.05),
    ("withdrawn all-tier federal top-1%",
     r"previously read ([\d.]+)% \[[\d.–-]+\] for the federal panel",
     "wa_fed_alltier_top1", 0.05),
    ("two money systems in individual_contributions — FEC then PDC dollars",
     r"federal \(`FEC:`, \$([\d.]+)M\) \*and\* state \(`PDC:`, \$([\d.]+)M\)",
     ("wa_fec_m", "wa_pdc_m"), 0.05),
    ("federal outflow basis restated in the occupation note",
     r"Washington-resident donors, \$([\d.]+)M", "wa_fec_m", 0.05),
    ("the unfiltered pooled total the occupation note withdraws",
     r"non-resident donors, \$([\d,.]+)M", "wa_unfiltered_m", 0.05),
    ("NY own-party skew, federal then state",
     r"deep-blue NY \(\+([\d.]+)\s*pts federal, \+([\d.]+) state\)",
     ("ny_fed_skew", "ny_state_skew"), 0.05),
    ("ID own-party skew, federal then state",
     r"deep-red Idaho \(\+([\d.]+) federal, \+([\d.]+) state\)",
     ("id_fed_skew", "id_state_skew"), 0.05),
    ("65+ donor shares, NY fed / ID fed / ID state",
     r"NY federal \*\*([\d.]+)%\*\*, ID federal \*\*([\d.]+)%\*\*, ID state\s*\*\*([\d.]+)%\*\*",
     ("ny_fed_65", "id_fed_65", "id_state_65"), 0.05),
    ("Finding 5 — the crossover bound on the FEDERAL panels, all four cells",
     r"NY unaffiliated \*\*([\d.]+)%\*\* against ([\d.]+)%; ID unaffiliated \*\*([\d.]+)%\*\* "
     r"against\s*([\d.]+)%",
     ("dn_xo_ny_d", "dn_xo_ny_r", "dn_xo_id_d", "dn_xo_id_r"), 0.05),
    # The NY half of the same sentence. `ny_state_dem_donly` was DERIVED all
    # along and never probed: it is written as a bare "94%" against Idaho's
    # bolded "94.6%", so the small-integer exemption swallowed it while its twin
    # was checked. A pair of figures where only one is asserted is the shape that
    # lets the unchecked one drift into contradicting its neighbour.
    ("NY Democratic own-party crossover — the FEDERAL panel, as the note says",
     r"near-monolithic donors \(\*\*(\d+)%\*\* NY federal\)", "ny_fed_dem_donly", 0.5),
    ("recall cost of the primary specification",
     r"discards ([\d]+)–([\d]+)% of matched donors", ("discard_lo", "discard_hi"), 0.5),
    # Replaces the "3.5" literal exemption. The range and its three members are probed
    # SEPARATELY against the same derivation, so a range that stopped spanning its own
    # members fails — which is the defect shape all six of the 2026-08-06 author questions
    # had, and the one thing a single probe on a span cannot catch.
    # The anchor said "of voters" until 2026-08-21, and this probe's own LABEL has said
    # "of registrants" since it was written -- the code had the basis right and the paper's
    # bolded lead-in did not. The sentence contradicted itself in one line: "**~4.0-5.7% of
    # voters** -- matched donors as a share of all registrants". The number is the
    # registrants figure and always was, by the author's 2026-08-06 basis call recorded
    # beside the derivation (`vrdb.voters all`); only the label moved. Not a quibble: on a
    # genuine voters reading WA would be 10.85% (super-voters) or 6.18% (active roll).
    ("donor share of registrants, the cross-state range",
     r"\*\*~([\d.]+)–([\d.]+)% of registrants\*\*",
     ("donor_share_lo", "donor_share_hi"), 0.05),
    ("donor share of registrants, the three states named",
     r"ID \*\*([\d.]+)%\*\*, NY \*\*([\d.]+)%\*\*, WA \*\*([\d.]+)%\*\*",
     ("id_donor_share", "ny_donor_share", "wa_donor_share"), 0.05),
    ("occupation blocs, RETIRED and NOT EMPLOYED",
     r"RETIRED \(\$([\d.]+)M, ([\d.]+)%\) and NOT EMPLOYED \(\$([\d.]+)M, ([\d.]+)%\)",
     ("occ_retired_m", "occ_retired_pct", "occ_notemp_m", "occ_notemp_pct"), 0.05),

    # ---- bootstrap CIs (deterministic; same seed, B and panel order as the diag) --------
    ("federal top-1% 95% CI",
     r"federal panel top-1% \*\*[\d.]+%\*\* \[([\d.]+)–([\d.]+)\]",
     ("fed_t1_lo", "fed_t1_hi"), 0.05),
    ("federal Gini 95% CI",
     r"Gini \*\*[\d.]+\*\* \[([\d.]+)–([\d.]+)\], two-ZIP3",
     ("fed_gini_lo", "fed_gini_hi"), 0.0005),
    ("state top-1% 95% CI",
     r"state panel top-1% \*\*[\d.]+%\*\*\s*\[([\d.]+)–([\d.]+)\]",
     ("state_t1_lo", "state_t1_hi"), 0.05),
    ("state Gini 95% CI",
     r"state panel top-1%.*?Gini \*\*[\d.]+\*\* \[([\d.]+)–([\d.]+)\]",
     ("state_gini_lo", "state_gini_hi"), 0.0005),

    # ---- Finding 6 ----------------------------------------------------------------------
    # RE-ANCHORED 2026-08-29: the sentence now states the inventory (five cycles) and the
    # estimator's population (34 races, four completed cycles) SEPARATELY — the owning
    # paper's own 2026-08-25 correction, which this document had not carried.
    ("Finding 6 — scorable races, stated apart from the cycle inventory",
     r"the (\d+) scorable WA U\.S\. House races all sit in the four\s*completed ones",
     "ie_n", 0),
    ("Finding 6 — WA-03 total and net IE",
     r"WA-03 2024 \(\$([\d.]+)M total IE, \+\$([\d.]+)M net pro-Dem\)",
     ("wa03_ie_total", "wa03_ie_net"), 0.05),
    # The corrected total restated inside the correction note. Probed rather than
    # exempted: a correction that quotes a figure the data no longer supports is a
    # worse defect than the one it corrects, so this occurrence is asserted too.
    ("Finding 6 — corrected WA-03 total, in the correction note",
     r"At the true \$([\d.]+)M it ranks 22nd of 387", "wa03_ie_total", 0.05),
    ("Finding 6 — the direction-coded PDC legislative panel",
     r"\*\*\$([\d.]+)M of\s+direction-coded PDC state-legislative IE\*\*", "pdc_c63_m", 0.05),
    ("Finding 6 — legislative scorable cells (vs does-money-move-votes.md)",
     r"adds \*\*(\d+) scorable district-cycles\*\*", "leg_n", 0),
    ("Finding 6 — legislative sign range (vs does-money-move-votes.md)",
     r"specification-dependent\*\* \(−([\d.]+) to \+([\d.]+) across four\s+specifications\)",
     ("leg_slope_lo_abs", "leg_slope_hi"), 0.005),
    ("Finding 6 — slope and r (vs does-money-move-votes.md)",
     r"\*\*\+([\d.]+) pp per\s+\$1M net pro-Dem IE \(Pearson r \+([\d.]+), n=(\d+)\)\*\*",
     ("ie_slope", "ie_r", "ie_n"), 0.005),
    ("Finding 6 — bootstrap interval (vs does-money-move-votes.md)",
     r"bootstrap interval of\s+−([\d.]+) to \+([\d.]+) that spans zero",
     ("_ie_ci_lo_abs", "ie_ci_hi"), 0.005),
    # RE-POINTED 2026-08-15 with the heading rewrite. The claim sentence was recast from
    # "money marks strength" to a non-identification, and the objection no longer needs to
    # restate the figure to make its point. The current-value probe and the retired-value
    # probe are kept as a PAIR, deliberately: the note that retires +0.58 has to keep saying
    # +0.58, and the claim has to keep saying the owning paper's current number, so a future
    # drift cannot quietly make the two agree by moving the wrong one.
    ("Finding 6 — fundraising correlation (vs does-money-move-votes.md)",
     r"log2\(D/R\) receipts correlate \*\*\+([\d.]+)\*\*",
     "money_r_fundraising", 0.005),
    ("Finding 6 — the current pair restated in the retirement note",
     r"current \*\*\+([\d.]+)\*\* and \*\*([\d.]+)\*\*",
     ("money_r_fundraising", "money_holdout_alloc"), 0.005),
    ("Finding 6 — WA-03 residual (vs does-money-move-votes.md)",
     r"finished \+([\d.]+) pp off its fundamentals", "money_wa03_resid", 0.005),
    # Replaces the "0.00" literal exemption (author answered 2026-08-06: drop the tilde and
    # cite the two-decimal round). Tolerance is the paper's printed precision, not a slack
    # wide enough to let 0.00 back through.
    ("Finding 6 — allocation squared holdout correlation (vs does-money-move-votes.md)",
     # RE-ANCHORED 2026-08-29, same cause as the Appendix B probe: the label moved to the
     # owning paper's corrected term.
     r"cross-cycle squared holdout correlation of \*\*([\d.]+)\*\*", "money_holdout_alloc", 0.005),
    ("Finding 6 — the pre-election cutoff pair (vs does-money-move-votes.md, 2026-08-29)",
     r"correlation is\s*essentially unchanged — \*\*\+([\d.]+)\*\* against "
     r"\*\*\+([\d.]+)\*\* full-cycle on the same\s*report-built",
     ("money_pre_r", "money_fullrep_r"), 0.005),
    # --- Finding 3, gated 2026-08-10. See _finding3 for why none of this was asserted.
    ("Finding 3 — median itemized gift, both money systems",
     r"median itemized gift is \$(\d+)\*\* in both money systems",
     "whale_median_gift_federal", 0.5),
    ("Finding 3 — median per-recipient-cycle Gini, both systems",
     r"median Gini \*\*([\d.]+)\*\* federal and \*\*([\d.]+)\*\* state",
     ("whale_gini_federal", "whale_gini_state"), 0.0005),
    ("Finding 3 — qualifying recipient-cycle counts",
     r"≥100 distinct donors \(\*\*([\d,]+)\*\* federal, \*\*([\d,]+)\*\* state\)",
     ("whale_n_federal", "whale_n_state"), 0.5),
    # THE probe the withdrawn-claim register already claimed existed. It anchors on the
    # sentence that retires "~0.61", so rewording that sentence out from under it fails the
    # gate rather than silently unguarding the withdrawal.
    ("Finding 3 — the value that replaced the withdrawn 0.61",
     r"both layers give ([\d.]+)", "whale_gini_federal", 0.0005),
    ("Finding 3 — pooled count and the separated pair restated",
     r"the count is ([\d,]+) today; separated it is ([\d,]+) federal and ([\d,]+) state",
     ("whale_n_pooled", "whale_n_federal", "whale_n_state"), 0.5),
    ("Finding 3 — the state-side maximum single gift",
     r"\*\*\$([\d.]+)M maximum is a PDC state gift\*\*", "whale_max_state_m", 0.05),
    ("Finding 3 — the federal maximum single gift",
     r"the federal maximum is \$([\d,]+)", "whale_max_federal", 0.5),
    ("Finding 3 — the state share of pooled recipient-cycles",
     r"which is ([\d.]+)% of the pooled recipient-cycles", "whale_state_share", 0.5),
    # The $2.5M appears three times: once inside the RETIRED sentence, once attributed
    # correctly, once in the objection. The figure itself was never wrong — only the money
    # system it was paired with — so all three are probed rather than the retired one being
    # exempted. Same discipline as Finding 5's three restatements of the sub-$200 pair.
    ("Finding 3 — the state maximum as quoted in the retired sentence",
     r"single gifts reach \$([\d.]+)M", "whale_max_state_m", 0.05),
    ("Finding 3 — median gift and state maximum restated in the objection",
     r"a Gini that mixes \$(\d+) and \$([\d.]+)M",
     ("whale_median_gift_federal", "whale_max_state_m"), 0.05),
    # The basis note restates all three counts to make the point that pooled is a separate
    # grouping. Probed rather than exempted: the inequality it asserts is only true while the
    # three values are the current ones, so a drift that moved one would otherwise leave a
    # sentence claiming an arithmetic fact about stale numbers.
    ("Finding 3 — the three counts restated in the basis note",
     r"which is why ([\d,]+) \+ ([\d,]+) ≠ ([\d,]+)",
     ("whale_n_federal", "whale_n_state", "whale_n_pooled"), 0.5),
    # Anchored on the prose name, not the register's PATH: citing the path from a published
    # paper trips test_cited_files_are_synced, which requires every path a paper cites to be in
    # the public manifest. The register is a review instrument, not a reproduction input.
    ("Finding 3 — the 0.578 named in the basis note as the register's claimed guard",
     r"including the ([\d.]+) that the series' withdrawn-claim register",
     "whale_gini_federal", 0.0005),

    # ---- Findings 5 & 6, the 2026-08-15 referee round. Every figure the rewrite introduced
    # is probed in the round that writes it, and every figure it RETIRES is probed inside the
    # note that retires it — a retired number quoted wrongly is still a defect.
    ("Finding 5 — the current key's matchability restated in the correction note",
     r"full-name key runs ([\d.]+)–([\d.]+)%",
     ("dn_pmatch_ny_lo", "dn_pmatch_wa_hi"), 0.05),
    ("Finding 5 — the retired ID state crossover figure, in the panel note",
     r"the \*\*state\*\* panels — ID ([\d.]+)%", "id_state_dem_donly", 0.05),
    ("Finding 5 — state-panel resolution, overall and for Idaho's unaffiliated row",
     r"resolution is only ([\d.]+)% for Idaho and ([\d.]+)% for New York "
     r"\(([\d.]+)% for Idaho's unaffiliated",
     ("dn_res_id_state", "dn_res_ny_state", "id_state_xo_unaff_res"), 0.05),
    ("Finding 5 — federal-panel resolution, the reason those panels carry the claim",
     r"where resolution is ([\d.]+)–([\d.]+)%",
     ("dn_res_fed_lo", "dn_res_fed_hi"), 0.05),
    ("Finding 6 — the retired correlation and holdout pair, in the note that retires them",
     r"correlation read \*\*\+([\d.]+)\*\* and the holdout R² \*\*([\d.]+)\*\*",
     ("money_r_fundraising_retired", "money_holdout_alloc_retired"), 0.005),
    ("Finding 6 — the leave-one-out sweep, both ends",
     r"runs from \*\*−([\d.]+)\*\* \(dropping WA-08 2018\) to\s*\*\*\+([\d.]+)\*\*",
     ("mp_loo_lo", "mp_loo_hi"), 0.005),
    ("Finding 6 — the WA-08 2018 leverage cell",
     r"\(\*\*\+\$([\d.]+)M\*\*\) with a\s*\*\*\+([\d.]+)\*\*-point residual and carries a "
     r"Cook's distance of \*\*([\d.]+)\*\*",
     ("mp_cd08_net", "mp_cd08_resid", "mp_cd08_cook"), 0.005),
    ("Finding 6 — dropping every WA-08 observation",
     r"observation gives \*\*−([\d.]+)\*\*", "mp_drop_all_cd08", 0.005),
    ("Finding 6 — the district-clustered interval",
     r"widens the interval to \*\*−([\d.]+) to \+([\d.]+)\*\*",
     ("mp_clust_lo", "mp_clust_hi"), 0.005),
    # ---- Finding 2, gated 2026-08-15 with the switch from forecast to observed.
    ("Domain 2 — the four-state OBSERVED not-close shares",
     r"\*\*WA ([\d.]+)% · NY ([\d.]+)% · TX ([\d.]+)% · ID ([\d.]+)%\*\*",
     ("ss_wa", "ss_ny", "ss_tx", "ss_id"), 0.05),
    ("Finding 2 — WA's five-cycle not-close range, why 'worsening' is withdrawn",
     r"runs \*\*([\d.]+)–([\d.]+)%\*\* across 2016–2024",
     ("ss_wa_cycle_lo", "ss_wa_cycle_hi"), 0.05),
    ("Finding 2 — the same five-cycle range, restated in the first-analysis bullet",
     r"not-close share runs\s*\*\*([\d.]+)–([\d.]+)%\*\* across the five cycles",
     ("ss_wa_cycle_lo", "ss_wa_cycle_hi"), 0.05),
    ("Finding 2 — the two dimensions that must not be merged, WA 2024",
     r"([\d.]+)% of seats\s*were not close and ([\d.]+)% offered no D-v-R option",
     ("ss_wa24_notclose", "ss_wa24_no_dvr"), 0.05),
    ("Finding 6 — the headline slope restated in the withdrawal note",
     r"It also headlined \+([\d.]+) without the leverage", "ie_slope", 0.005),


    # ---- Domain 1, gated for the first time on 2026-08-16 with the synthesis conversion.
    ("Domain 1 — the vote-record base",
     r"From \*\*([\d.]+)M\*\* VRDB vote records", "wa_vote_records_m", 0.05),
    ("Domain 1 — senior and youth shares of the electorate, all six cells",
     r"65 and older were\s*\*\*([\d.]+)%, ([\d.]+)% and ([\d.]+)%\*\* of the 2021, 2023 and "
     r"2025 odd-year electorates against\s*\*\*([\d.]+)%\*\* in 2024, while voters 18–29 fell "
     r"from \*\*([\d.]+)%\*\* in 2024 to about \*\*([\d.]+)%\*\*",
     ("wa_p65_21", "wa_p65_23", "wa_p65_25", "wa_p65_24", "wa_p1829_24", "wa_p1829_off"), 0.05),
    ("Domain 1 — the within-cohort rates, at the owning paper's precision",
     r"falls from \*\*([\d.]+)%\*\* \(2024\) to about \*\*([\d.]+)%\*\*\s*off-year, while "
     r"65\+ slips only from \*\*([\d.]+)%\*\* to \*\*~([\d.]+)%\*\*",
     ("wa_r1829_24", "wa_r1829_off", "wa_r65_24", "wa_r65_off"), 0.05),
    ("Domain 1 — the two retired over-precise rates, quoted in the note that retires them",
     r"\*\*([\d.]+)%\*\* and\s*\*\*([\d.]+)%\*\* — to a decimal place",
     ("wp_retired_r1829_off", "wp_retired_r65_off"), 0.05),

    ("Domain 1 — the retired rounded band, quoted in the note that retires it",
     r"rounded band \(\"~([\d.]+)–([\d.]+)%\"\)",
     ("wp_retired_p65_lo", "wp_retired_p65_hi"), 0.05),
    ("Domain 1 — the owning paper's own precision, quoted back at it",
     r"reports them as \"about ([\d.]+)%\" and \"~([\d.]+)%\"",
     ("wa_r1829_off", "wa_r65_off"), 0.05),

]


# --- Coverage gate (ported 2026-08-06; see verify_who_decides_wa for the three rules) ----
# The three findings, partitioned so no slice overlaps another — spans are per-section
# coordinates, so a slice that swallows another reports the inner one's probed cells as
# unmapped. Finding 6's end anchor is the horizontal rule that closes the scraped block;
# it occurs exactly once in that block, and vp.slice_with_offset raises if it moves.
AUDIT_BOUNDS = {
    # RE-ANCHORED 2026-08-16, when the document became a synthesis paper: the six scored
    # "findings" regrouped into four evidence domains, with the three money results as
    # 3a/3b/3c under Domain 3. Anchors are section IDENTITY and a missing one RAISES rather
    # than skipping, which is what forces this edit rather than letting sections silently drop
    # out of the coverage gate. Domain 1 is now inside the audited slice too — it sat outside
    # it for as long as this was a prospectus, so its participation figures were never gated.
    #
    # domain3_intro exists because spans MUST NOT OVERLAP and must not leave gaps: the prose
    # between Domain 3's heading and 3a would otherwise be audited by nothing.
    #
    # EXTENDED TO THE WHOLE DOCUMENT 2026-08-26. domain3_intro's comment above states the
    # rule — "must not leave gaps" — and the bounds dict then honoured it only BETWEEN the
    # domains. `scripts/diag_audit_span_gaps.py` measured what that cost here: 51.1% of the
    # paper covered, 267 numeric tokens in no span at all, the worst of the ten. The audit
    # printed "fully mapped" seven times over half a document.
    #
    # Two of those gaps were load-bearing, not preamble. "Data, and what each state can
    # actually support" is the paper's inventory table — row counts, dollar totals and the
    # per-panel matched counts a reader takes as the programme's scale — asserted by nothing.
    # And "What the evidence does not support" plus the Conclusion RESTATE companion findings,
    # which is the propagation surface this file exists to guard; the Conclusion's own
    # correction note says an earlier verdict shipped a false claim there "outside every
    # coverage span, while the finding that corrects it was gated". That note described the
    # mechanism accurately and the mechanism was left in place.
    "front_matter": ("# Electoral Health in Four States", "## What this paper claims"),
    "claims": ("## What this paper claims", "## Scope and integrity statement"),
    "scope": ("## Scope and integrity statement", "## Data, and what each state"),
    "data_inventory": ("## Data, and what each state", "## Method Each research question"),
    "method": ("## Method Each research question", "### Domain 1 — Participation"),
    "domain1": ("### Domain 1 — Participation", "### Domain 2 — Contestation"),
    "domain2": ("### Domain 2 — Contestation", "### Domain 3 — Political voice"),
    "domain3_intro": ("### Domain 3 — Political voice", "#### 3a. Small transactions"),
    "money3a": ("#### 3a. Small transactions", "#### 3b. Donors are also"),
    "money3b": ("#### 3b. Donors are also", "#### 3c. The donor class"),
    "money3c": ("#### 3c. The donor class", "### Domain 4 — Campaign effects"),
    "domain4": ("### Domain 4 — Campaign effects", " --- "),
    "not_supported": ("## What the evidence does not support", "## Conclusion"),
    "conclusion": ("## Conclusion", "## Appendix A — Methodological history"),
    "appendix_a": ("## Appendix A — Methodological history",
                   "## Appendix B — The companion papers"),
    # The last span needs a real end anchor — vp.slice_with_offset raises rather than running
    # to end-of-document, which is the discipline that stops a moved heading from silently
    # widening a slice. This is the document's closing clause; nothing numeric follows it.
    "appendix_b": ("## Appendix B — The companion papers",
                   "remains for a future extension."),
}

COVERAGE_EXEMPT = [
    (r"^(?:19|20)\d{2}$", "a calendar year, not a result"),
    (r"^\d{1,2}$", "small integer — list ordinals, insight/failure scores, race counts"),
    # COHORT EDGES, written with a percent sign but naming a group rather than
    # measuring anything: "the top 1% of donors supplied 41.2%" has one result in
    # it and it is not the 1. Declared as explicit unit-carrying patterns under
    # strict_units so the exception stays this narrow — the alternative was a
    # literal waiver on "1" and "10", which covers every bare 1 and 10 in the
    # paper. The SHARES beside them are probed (wa_fed_top1, top10 and friends).
    (r"^1%$", "the top-1% cohort EDGE, not a measurement; the share it names is probed"),
    (r"^10%$", "the top-10% cohort EDGE, as above"),
    # The slope's money scaling in Finding 6. Finding 6 restates Finding 2c of
    # does-money-move-votes.md, which is declared in UNCHECKED here and owned
    # there — verify_money_votes.py asserts this unit against the pinned panel's
    # `net_pro_dem_musd` denomination.
    (r"^\$1$", "the per-$1M slope scaling; owned by verify_money_votes.py"),
]

# Every literal here names WHERE the figure is checked, or the open question that closes it.
# "Not a result" with no reason is how a real figure hides — see verify_who_decides_wa.
COVERAGE_EXEMPT_LITERAL: dict[str, str] = {
    # --- Statute and docket numbers, exposed 2026-08-26 when the audited slice became the
    # whole document. These are CITATIONS, not measurements: there is nothing in a database
    # to assert them against, and the thing that could go wrong with them (citing the wrong
    # provision) is not a numeric-drift failure. They are listed one by one rather than
    # waived by a pattern, because a pattern loose enough to catch "08.720" would also catch
    # real two-and-three-digit results.
    "08.720": "RCW 29A.08.720, the statute Washington's voter file is obtained under — a "
              "citation. The legal basis is recorded in CLAUDE.md and the ethics assessment",
    "103": "N.Y. Elec. Law § 3-103(5), the elections-purpose certification NYSVOTER is used "
           "under — a citation",
    "437": "Idaho Code § 34-437A, the statute Idaho's voter file is obtained under — a "
           "citation",
    "56.050": "RCW 29A.56.050, the presidential-primary declaration statute — a citation. "
              "The sentence's substantive claim is that it sets no disclosure DURATION, "
              "which is prose, and the '~60-90 day window' it retires is explicitly marked "
              "unverified and is not asserted",
    # ⚠ THE FIRST DRAFT OF THIS REASON SAID check_cross_doc_consistency.py "matches it
    # against the submission metadata". It does not — its only mention of this number is a
    # comment about stripping a trailing comma so the IDENTIFIER ALLOWLIST recognises it,
    # i.e. that checker waives it too. Naming a script that waives a figure as the script
    # that verifies it is precisely the "another script owns it" failure the exemption rule
    # was written against, so the reason states what is actually true.
    "7149263": "the SSRN submission id of the posted Washington companion — an identifier, "
               "not a measurement, and nothing derives it. It is waived as an identifier by "
               "check_cross_doc_consistency.py as well; what IS checked across documents is "
               "that the seven places it appears agree, by that script's orphan pass",
    # --- The backtest, PINNED and PROBED since 2026-08-26 (see _backtest and BACKTEST_PIN).
    # Six exemptions stood here while the figures were declared in UNCHECKED: 6.41, 10.12, 163,
    # 170, 94 and 85. Five are gone because the figures they waived are either asserted now or
    # withdrawn from the paper. What remains is the interval's NOMINAL LEVEL, which is a choice
    # of confidence level and not a measurement of anything -- the coverage it achieves (97%) is
    # the measurement, and that is probed.
    # The WITHDRAWN pair and the current pair, both quoted inside the withdrawal note that
    # explains the difference. A note whose job is to say "this said 10.12/85% on 170 cells and
    # that was two model versions read as one" cannot avoid restating them. The LIVE sentence's
    # figures are probed against the pin; these occurrences are the record of what was removed.
    "10.12": "the WITHDRAWN v-may15 backtest MAE, quoted only inside its withdrawal note. Not "
             "re-derivable on the current model, which is the point the note makes",
    "85": "the WITHDRAWN v-may15 directional accuracy, same note, same reason",
    "170": "the WITHDRAWN valid-cell count from the May-2026 grid. Also the label of "
           "METHODOLOGY.md 6.3's dated 24/46/170-cell table, cited there as history",
    "163": "the CURRENT valid-cell count, restated inside the withdrawal note; the live "
           "sentence's occurrence is probed against bt_cells_valid",
    "94": "the current directional accuracy, in the note's 'v-may15 versus v-jun17' contrast "
          "where it labels a MODEL VERSION's pair rather than restating the result. The two "
          "live occurrences are captured and probed against bt_directional_accuracy",
    "6.41": "the CURRENT backtest MAE, restated inside the withdrawal note; the live "
            "occurrence is probed against bt_mae_margin",
    "95": "the interval's nominal confidence level -- a choice, not a result. The coverage it "
          "actually achieves is 97% and is probed against the pinned backtest",
    # --- Appendix A's 2026-06-27 data description, the HISTORICAL half of a then/now pair.
    # These two are unre-derivable BY CONSTRUCTION: the sentence exists to say the gauntlet
    # was scored against a data description that has since moved, so there is no current
    # query that returns them and producing one would defeat the sentence. The half that CAN
    # drift is the "today" half, and it is probed against the same keys the inventory section
    # uses ("appendix A — the current data description"), so the two cannot disagree.
    "1.3": "the ~$1.3B contribution total as the 2026-06-27 gauntlet described it — a "
           "superseded historical figure quoted to date the scoring exercise. Its current "
           "counterpart in the same sentence is probed against inv_wa_contrib_musd",
    "9.2": "the 9.2M voter-score rows as of 2026-06-27, same then/now pair. The current "
           "counterpart is probed against inv_wa_vs_m",
    "58.4": "Lucero et al. 2025's off-cycle over-45 share. NB it collides numerically with "
            "Washington's own 18-29 presidential participation rate, which is probed as "
            "wa_r1829_24 earlier in the same section — two different quantities that happen "
            "to share a value, which is why this exemption names both",
    # --- Domain 1's literature figures, exposed when the slice widened on 2026-08-16.
    "49.7": "Lucero et al. 2025's presidential-year over-45 share, an external literature "
            "figure quoted as context; not measured here",
    "415": "California SB 415, a statute number in the Ornstein (2024) citation",
    "236": "local governments in Ornstein (2024)'s sample, an external literature figure",
    "28": "the '28%' this bullet's own correction note identifies as a figure an earlier "
          "draft mis-attributed to the literature; quoted only to record the error",
    # --- Finding 2, added 2026-08-15 when the coverage gate first reached this section.
    "38": "Ballotpedia Competitiveness Index share of uncontested state-leg seats in 2024, an external literature figure, not a result of this programme",
    "0.5": "the primary-to-general turnout ratio in safe seats, approximate and owned by "
           "safe-seat-washington.md; quoted here as context for what this data adds, not "
           "measured here",
    "164": "Cook PVI swing-district count in 1997, an external literature figure "
           "(Cook Political Report), not a result of this programme",
    # --- Finding 3, with that section's gate (2026-08-10).
    "100": "the >=100-distinct-donor THRESHOLD selecting the recipient-cycle population, "
           "not a measurement of it. The counts it selects are probed, both systems",
    "2,821": "the WITHDRAWN pooled recipient-cycle count, quoted in the correction note as "
             "what this bullet used to say. It was computed on the pooled FEC+PDC table "
             "before the split; the CURRENT pooled count is probed",
    # The three counts AS FIRST PUBLISHED hours earlier the same day, quoted in the basis note
    # to evidence that they drift. They are history by construction and cannot be re-derived —
    # the table has grown since. Their current values are probed three times over.
    "822": "the federal recipient-cycle count as first published 2026-08-10, quoted to "
           "evidence live-read drift. Current value probed (whale_n_federal)",
    "1,989": "the state count as first published the same day; current value probed",
    "2,814": "the pooled count as first published the same day; current value probed",
    "0.61": "the WITHDRAWN median Gini. Registered in withdrawn_claims.csv as unpatternable "
            "(a bare figure too generic to forbid), so the guard is the probe on the "
            "sentence that retires it — 'both layers give 0.578' — not a forbidden pattern",
    "200": "the sub-$200 / >=$200 gift-size threshold naming a cut this finding proposes "
           "rather than reports; no share at it is stated here",
    # Form C-6's section identifier, not a measurement. It appears in Finding 6
    # because naming the section is what makes the 2026-08-09 correction
    # reproducible — a reader has to know which part of the form carries the
    # direction data that this bullet previously said did not exist. Verified
    # structurally by tests/test_etl/test_pdc_ie_targets.py, which fails if the
    # loader stops reading C6.3 rows.
    "6.3": "form C-6 section identifier (C6.3, Identified Entities), not a figure",
    # --- Finding 6's correction paragraph (2026-08-08). All four are figures the
    # correction EXISTS to record as retired, so they are historical by construction
    # in exactly the sense the Finding 5 withdrawals below are. The replacements are
    # asserted: +0.515 / +0.186 / n=34 by the slope probe, $18.61M by the WA-03 probe.
    "0.39": "the RETIRED single-cycle slope and Pearson r, quoted in the correction "
            "note as what this bullet used to say. The replacements (+0.515, +0.186) "
            "are asserted against does-money-move-votes.md by the slope probe",
    "40.1": "the RETIRED WA-03 IE total, inflated ~2x by the notice/periodic "
            "double-count. Its replacement $18.61M is asserted by the WA-03 probe; "
            "this figure can never be re-derived because the load that produced it "
            "was wrong, which is precisely why the correction states it",
    "387": "count of U.S. House races drawing any IE in 2024, supporting the rank "
           "that replaced the retired 'most IE-saturated in the country' claim. Owned "
           "by scripts/diag_fec_ie_bulk_crosscheck.py --national-rank, which reads "
           "FEC's national bulk file; no warehouse here holds out-of-state IE",
    # --- Finding 5's two WITHDRAWN occupation figures. Deliberately retired values, and
    # the reason they cannot be re-derived is visible in which half still reproduces:
    # `individual_contributions` has GROWN since 2026-07-27, so the scale-invariant
    # percentage survives (21.27% -> 21.3 exactly) while the dollar total does not
    # ($223.5M today against the published $221.7M). The CURRENT values on this basis
    # ($154.0M / 23.8% and $128.8M / 19.9%) ARE asserted, by the occupation-blocs probe.
    "221.7": "withdrawn pre-2026-07-27 RETIRED dollars on the unfiltered pooled table, "
             "which has since grown; today's basis gives $223.5M. The figure that "
             "REPLACED it ($154.0M) is asserted by the occupation-blocs probe",
    "21.3": "the withdrawn RETIRED share on the same retired basis; reproduces (21.27%) "
            "but is recorded as superseded. Replacement 23.8% is asserted",
    "147.4": "withdrawn pre-2026-07-27 NOT EMPLOYED dollars; as above, today $147.5M. "
             "Replacement $128.8M is asserted",
    "14.1": "the withdrawn NOT EMPLOYED share; the two candidate bases now give 14.04% "
            "(amt>0) and 14.15% (all rows), so it reproduces on neither and is history. "
            "Replacement 19.9% is asserted",
    # --- the all-tier bootstrap CI beside the withdrawn 42.4%, which IS derived.
    "40.2": "lower bound of the WITHDRAWN all-tier federal top-1% CI. Not reproducible "
            "standalone: the published intervals come from one RNG threaded through "
            "federal-then-state-then-inflow in that order (see _bootstrap), so an "
            "all-tier panel cannot be inserted into the sequence without changing every "
            "other interval. Owned by cross-state-fec-money.md §F4; the point estimate "
            "42.4% is derived here from voter_donor_affiliation_fec_alltier",
    "44.9": "upper bound of the same withdrawn interval; as above",
    # --- Finding 6's holdout R2 was HERE until 2026-08-06. The exemption noted that the
    # allocation-alone cell is 0.022, which rounds to 0.02 and not to the printed '~0.00';
    # the author answered "drop the tilde, cite the two-decimal round". The paper now says
    # 0.02, the money paper's cell is scraped by _money_paper, and the figure is PROBED
    # ("Finding 6 — allocation holdout R2"). Appendix B's restatement was changed with it
    # and is covered by _restated_outside_the_slice.
}

# --- ✅ RESOLVED 2026-08-06 — author chose the cross-state pooled, full-roll basis -------
# Finding 5's "defensible claim" used to read "~3.5-6% of voters" and NO basis reproduced
# it; the full panel x denominator enumeration now sits beside the derivation in derive(),
# where it documents the basis actually chosen rather than an open question. The claim reads
# "~4.0-5.7% of voters" with ID / NY / WA named, and all five numbers are probed.
#
# Why the original was unrecoverable rather than merely wrong: the prospectus predates BOTH
# the federal/state panel split and the Idaho load (2026-07-19), so the tables it was
# computed against no longer exist in that form. That is the honest reason it was restated
# on a current basis instead of being "corrected" to some reconstructed original.

COVERAGE_EXEMPT_SECTIONS: dict[str, str] = {}


def _restated_outside_the_slice(d) -> list[str]:
    """Guard the ONE surface this script verifies nothing of: the rest of the document.

    Added 2026-08-06, because the stale +0.55 it was written to catch appears THREE times
    in this paper and only two are inside Findings 4-6. The third is in Appendix B's
    publication sequence, where a coverage gate scoped to the findings can never see it —
    so a fix driven by the gate alone would have left one occurrence wrong and the
    verifier green, which is worse than not having looked.

    Deliberately narrow: it re-checks whole-document occurrences of figures this script
    already sources from does-money-move-votes.md, rather than becoming a second verifier
    for a prospectus whose Findings 1-3 belong to other papers.
    """
    if "money_r_fundraising" not in d:
        return ["Appendix guard: could not scrape the fundraising correlation from "
                "does-money-move-votes.md — the anchor moved"]
    whole = vp.normalise(PAPER.read_text(encoding="utf-8"))
    want = d["money_r_fundraising"]
    fails = []
    hits = re.findall(r"overperformance \(\+([\d.]+)\)|correlates \*\*\+([\d.]+)\*\* with "
                      r"overperformance|\+([\d.]+) is exactly what a true causal", whole)
    flat = [float(x) for tup in hits for x in tup if x]
    if not flat:
        fails.append("Appendix guard: no whole-document occurrence of the fundraising "
                     "correlation matched — the wording moved, so this guard is disarmed")
    for got in flat:
        if abs(got - want) > 0.005:
            fails.append(f"whole-document fundraising correlation: paper +{got} vs "
                         f"does-money-move-votes.md +{want}")
    print(f"\n  restated-outside-the-slice guard: {len(flat)} whole-document occurrence(s) "
          f"of the fundraising correlation, target +{want}")

    # Second figure under the same guard, added 2026-08-06 with the '~0.00' correction: the
    # allocation holdout R2 is restated in Appendix B's publication sequence, outside the
    # findings slice — the same blind spot the +0.55 hid in. The Appendix B occurrence was
    # "≈ 0" before this and would have stayed a rounding-down claim after the finding itself
    # was fixed, which is exactly the half-fix this guard exists to prevent.
    if "money_holdout_alloc" not in d:
        return fails + ["Appendix guard: could not scrape the allocation holdout cell from "
                        "does-money-move-votes.md — the anchor moved"]
    hwant = d["money_holdout_alloc"]
    # RE-ANCHORED 2026-08-29: the restatement's label moved to the owning paper's corrected
    # term ("squared holdout correlation", not "holdout R²"); \s+ because it wraps.
    hhits = [float(x) for x in
             re.findall(r"allocation squared\s+holdout correlation ([\d.]+)", whole)]
    if not hhits:
        fails.append("Appendix guard: no whole-document occurrence of the allocation "
                     "squared holdout correlation matched — the wording moved, so this "
                     "guard is disarmed")
    for got in hhits:
        if abs(got - hwant) > 0.005:
            fails.append(f"whole-document allocation squared holdout correlation: paper {got} vs "
                         f"does-money-move-votes.md {hwant}")
    print(f"  restated-outside-the-slice guard: {len(hhits)} whole-document occurrence(s) "
          f"of the allocation squared holdout correlation, target {hwant}")
    return fails


def claim_guards(d: dict) -> list[str]:
    """Assert the comparative claims no probe can anchor on.

    A claim of INVARIANCE has no numeric token: "every Washington generation multiplier is
    unchanged to two decimal places in both panels" is checkable arithmetic stated in words,
    so `audit_coverage` cannot see it and a regex probe has nothing to capture. That is the
    blind spot that let safe-seat ship "more than double any other year in the series" false
    for a round while every value it compared was individually asserted.

    A module-level function of the derived dict so it can be shown FAILING without a full
    verifier run. Tested in tests/test_infrastructure/test_whitepaper_claim_guards.py.
    """
    fails = []
    # Finding F, the matcher-artifact objection. The paper's defensible conclusion rests on
    # this invariance: if re-weighting DID move a multiplier, "measured roll-side strict-key
    # matchability does not explain the age skew" would no longer follow from it.
    # The paper's conclusion, not its arithmetic: re-weighting must not overturn the skew.
    # This replaced a check that re-weighting leaves every multiplier "unchanged to two
    # decimal places", which the paper asserted and which was FALSE in six of ten cells
    # (2026-08-24) -- pooled Silent 1.96->1.91, Boomer 1.71->1.70, Gen X 1.22->1.24; federal
    # Silent 2.67->2.61, Boomer 2.04->2.03, Gen X 0.98->1.01. The sentence now states the
    # measured maximum instead, and what has to hold is the DIRECTION and RANK, which is what
    # "matchability does not explain the age skew" actually rests on.
    for _pfx, _label in (("wa", "pooled"), ("wafed", "federal")):
        if f"{_pfx}_raw_Silent" not in d:
            continue
        raw = [d[f"{_pfx}_raw_{g}"] for g in GENS]
        rw = [d[f"{_pfx}_ipw_{g}"] for g in GENS]
        # GENS runs oldest -> youngest, so both series must be strictly decreasing.
        for name, series in (("raw", raw), ("re-weighted", rw)):
            if any(series[i] <= series[i + 1] for i in range(len(series) - 1)):
                fails.append(
                    f"claim: Finding F says every cohort 'keeps its direction and its rank' "
                    f"under re-weighting, but the {name} {_label} multipliers are not "
                    f"monotonically decreasing oldest-to-youngest: "
                    f"{dict(zip(GENS, [round(x, 4) for x in series]))}. The age skew this "
                    f"paragraph defends is a ranking claim; if the ranking breaks the "
                    f"paragraph is wrong, not the tolerance.")
        # Silent and Boomer over-represented, Millennial and Gen Z under. Gen X is EXCLUDED
        # on purpose: it sits at parity and the paper says so, naming the federal crossing.
        for g, want_over in (("Silent", True), ("Boomer", True),
                             ("Millennial", False), ("Gen Z", False)):
            for name, val in (("raw", d[f"{_pfx}_raw_{g}"]), ("re-weighted", d[f"{_pfx}_ipw_{g}"])):
                if (val > 1.0) != want_over:
                    fails.append(
                        f"claim: Finding F rests on {g} being "
                        f"{'over' if want_over else 'under'}-represented, but the {name} "
                        f"{_label} multiplier is {val:.4f}. Re-weighting overturning a "
                        f"direction would defeat the matcher-artifact rebuttal.")
    return fails


def main():
    """Slice Findings 4-6, hand the probes to the shared harness, then GATE coverage.

    FOLDED ONTO `_verify_prose` 2026-08-01. This script invented the prose-scraping design
    and the rest of the series was built from it; keeping a private copy of the loop meant
    the original was the one verifier with no `--coverage` report, and any fix to the shared
    rules had to be made twice.

    COVERAGE BECAME A GATE 2026-08-06. `--coverage` was an advisory report nobody had to
    act on, so "74 figures agree" was a floor with no ceiling. Closing the 22 unprobed
    tokens found a real defect on the first pass — the fundraising correlation stale at
    +0.55 against the owning paper's +0.58, in three places.
    """
    text = PAPER.read_text(encoding="utf-8")
    # WIDENED TO FINDING 3 on 2026-08-10. It began at Finding 4, which is why Finding 3's
    # figures — including the 0.578 that the withdrawn-claim register already recorded as
    # "guarded by verify_whitepaper.py asserting 0.578" — were outside every slice and
    # outside the scraped text the probes even see.
    # WIDENED to Finding 2 on 2026-08-15. Finding 2 used to lead with unpinned, unprobed,
    # drifting forecast-snapshot band counts, so there was nothing worth gating; it now
    # leads with the safe-seat paper's OBSERVED shares, which are scraped and must not
    # drift underneath it.
    # WIDENED TO THE WHOLE DOCUMENT 2026-08-26, and this line was the real gap.
    #
    # The two widenings above moved a REGEX WINDOW, and the window was doing more than
    # scoping the coverage audit: `norm` is what `vp.run` matches every probe against, so a
    # figure outside it could not be probed even by a probe written for it. The audit then
    # reported "fully mapped" on seven spans that together were 51.1% of the paper
    # (`scripts/diag_audit_span_gaps.py`), and the other half was not merely unaudited — it
    # was unreadable to this script. `_restated_outside_the_slice` exists precisely because
    # someone noticed one figure in that half and hand-wrote a guard for it; that fix
    # treated the symptom.
    #
    # Widening the window is what makes the paper's own restatements checkable: `vp.run`
    # asserts EVERY occurrence of a figure, so the inventory table, the limits section, the
    # Conclusion and both appendices are now held to the same values as the domains.
    norm = vp.normalise(text)
    audit_sections, offsets, spans = {}, {}, {}
    for name, (start, end) in AUDIT_BOUNDS.items():
        audit_sections[name], offsets[name] = vp.slice_with_offset(norm, start, end)
    d = derive()
    stats: dict = {}
    rc = vp.run("WHITE PAPER — Findings 4-6, prose scraped and asserted against the data",
                norm, PROBES, d, UNCHECKED, vp.wants_coverage(), spans_out=spans,
                stats_out=stats)
    fails = vp.audit_coverage(audit_sections, spans, offsets, tuple(AUDIT_BOUNDS),
                              COVERAGE_EXEMPT, COVERAGE_EXEMPT_LITERAL,
                              COVERAGE_EXEMPT_SECTIONS, strict_units=True)
    fails += _restated_outside_the_slice(d)
    fails += claim_guards(d)
    fails += vp.audit_satellite_counts(PAPER.name, stats.get("figures"))
    if fails:
        print("\n" + "=" * 78)
        print(f"WHITE PAPER: {len(fails)} coverage/consistency FAILURE(S)")
        print("=" * 78)
        for f in fails:
            print(f"  - {f}")
        return 1
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
