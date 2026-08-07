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

SCOPE. Findings 4, 5 and 6 — the money/donor findings that restate verified cuts. Findings
1-3 are prospectus items whose realized analyses are covered by their own papers' verifiers.

Finding 6 is checked in two halves, and the split is deliberate. Its **data-ceiling facts**
(the scorable-race count, WA-03's IE dollars, the PDC IE that carries no support/oppose
flag) are re-derived here from scratch — and by the paper's own argument those ARE the
citable result. Its **slope and correlation** are not re-derived: they regress a
fundamentals-net residual that only the forecast model produces, and reimplementing that
here would fork the model rather than check it. Those are instead asserted to agree with
`does-money-move-votes.md`, which is the paper that owns them and whose independent
derivation is `diag_ie_vs_margin.py`. That is a CONSISTENCY check, not a re-derivation, and
it is labelled as such in the output — but it is the check that matters, because the white
paper had drifted to -0.42/-0.43 against the money paper's correct -0.39/-0.39.

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


def _ipw(con):
    """Raw and matcher-bias-reweighted over-representation on the POOLED match."""
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
    don = dict(con.execute("""SELECT w.g,COUNT(*) FROM voter_donor_affiliation a
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


def _party_and_age(state, buckets, dem_key):
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
    out["state_dem_donly"], = con.execute("""
        SELECT 100.0*COUNT(*) FILTER (WHERE d_amount>0 AND r_amount=0)
               /COUNT(*) FILTER (WHERE d_amount+r_amount>0)
        FROM voter_donor_affiliation_state a JOIN vrdb.voters v USING(state_voter_id)
        WHERE v.party='DEM'""").fetchone()
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


def _finding6(d):
    """Finding 6's data-ceiling facts — the part the paper itself calls the citable result."""
    c = duckdb.connect(str(DATA / "wa_statewide.duckdb"), read_only=True)
    # WA-03 2024: the most IE-saturated US House race in the country that cycle.
    tot, net = c.execute("""
        WITH p AS (SELECT DISTINCT election_cycle, UPPER(candidate_name) cn, party
                   FROM candidate_finance WHERE state='WA' AND office='H')
        SELECT SUM(ie.expenditure_amount)/1e6,
               SUM(CASE WHEN (p.party='Democratic' AND ie.support_oppose='S')
                          OR (p.party='Republican' AND ie.support_oppose='O') THEN ie.expenditure_amount
                        ELSE -ie.expenditure_amount END)/1e6
        FROM independent_expenditures ie
        LEFT JOIN p ON p.election_cycle=ie.election_cycle
                   AND p.cn=UPPER(ie.candidate_name)
        WHERE ie.source='FEC' AND ie.office='H' AND ie.state='WA'
          AND ie.support_oppose IN ('S','O')
          AND ie.election_cycle=2024 AND ie.district IN ('03','3')""").fetchone()
    d["wa03_ie_total"], d["wa03_ie_net"] = float(tot), float(net)
    # Directional FEC IE exists for one cycle only — the ceiling itself.
    d["fec_ie_cycles"], = c.execute("""
        SELECT COUNT(DISTINCT election_cycle) FROM independent_expenditures
        WHERE source='FEC' AND office='H' AND state='WA' AND support_oppose IN ('S','O')
    """).fetchone()
    # PDC state-legislative IE: large, and unusable for a directional test because the
    # support/oppose flag is null on every row.
    pdc_m, pdc_flagged = c.execute("""
        SELECT SUM(expenditure_amount)/1e6, COUNT(*) FILTER (WHERE support_oppose IN ('S','O'))
        FROM independent_expenditures WHERE source <> 'FEC'""").fetchone()
    d["pdc_ie_m"], d["pdc_ie_flagged"] = float(pdc_m), int(pdc_flagged)
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
    m = re.search(r"−([\d.]+) points of residual per \$1M net pro-Democratic IE "
                  r"\(Pearson r = −([\d.]+), n = (\d+)\)", t)
    if m:
        d["ie_slope"], d["ie_r"], d["ie_n"] = -float(m.group(1)), -float(m.group(2)), int(m.group(3))
    m = re.search(r"\| \*\*fundraising, log2\(D receipts / R receipts\)\*\* \| \*\*\+([\d.]+)\*\* \|", t)
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
    m = re.search(r"\| allocation shares alone \| ([\d.]+) \*\(r = ", t)
    if m:
        d["money_holdout_alloc"] = float(m.group(1))


def derive():
    d = {}
    wa = duckdb.connect(str(DATA / "wa_statewide.duckdb"), read_only=True)
    wa.execute(f"ATTACH '{DATA / 'wa_vrdb.duckdb'}' AS vrdb (READ_ONLY)")
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
    d["wa_ipw_Silent"], d["wa_ipw_Gen Z"] = ipw["Silent"][1], ipw["Gen Z"][1]
    # The LEFT side of the "1.96→1.91×" arrow, previously unprobed. Taken from _ipw's own
    # raw ratio rather than from _multipliers, so both halves of one sentence sit on one
    # basis (vrdb.voters + birth year, not voter_scores ld-scope). The two agree to 2dp on
    # WA — see _multipliers' docstring — which is why the paper can print the pooled figure
    # from one beside the IPW figure from the other.
    d["wa_raw_Silent"], d["wa_raw_Gen Z"] = ipw["Silent"][0], ipw["Gen Z"][0]
    d["wa_pmatch_lo"], d["wa_pmatch_hi"] = pm_lo, pm_hi
    # The all-tier federal top-1% the F2 line records as its own superseded value. Derived
    # rather than exempted: the retained _alltier snapshot reproduces it to the digit
    # (42.444 -> 42.4), so the withdrawal note is checkable and not just asserted.
    d["wa_fed_alltier_top1"] = _conc(wa, "voter_donor_affiliation_fec_alltier")["top1"]
    _scale(wa, d)
    d.update({f"wa_{k}": v for k, v in _turnout(wa).items()})
    wa.close()

    ny = _party_and_age("ny", "CASE WHEN v.party IN ('DEM','D') THEN 'DEM' ELSE 'X' END", "DEM")
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

    _bootstrap(d)
    _finding6(d)
    _money_paper(d)
    # The prose writes "−0.39"; the capture group yields "0.39". Compare magnitudes.
    if "ie_slope" in d:
        d["_neg_ie_slope"], d["_neg_ie_r"] = -d["ie_slope"], -d["ie_r"]
    return d


# ------------------------------------------------------------------------------ the probes
# (label, regex over the normalised Findings 4-5 text, derived key(s), tolerance)
PROBES = [
    ("pooled matched voters", r"Among the ([\d,]+) matched voters", "wa_pooled_n", 0),
    ("pooled matched voters (F2 restatement)",
     r"pooled ([\d,]+) match", "wa_pooled_n", 0),
    ("IPW match size", r"on the ([\d,]+)-voter match", "wa_pooled_n", 0),
    ("super-voter donor / non-donor %",
     r"\*\*([\d.]+)% are super-voters vs ([\d.]+)%\*\*", ("wa_super_d", "wa_super_n"), 0.05),
    ("super-voter %, F3 restatement",
     r"\*\*([\d.]+)% super-voters vs ([\d.]+)%\*\*", ("wa_super_d", "wa_super_n"), 0.05),
    ("turnout propensity donor / non-donor",
     r"propensity \*\*([\d.]+) vs ([\d.]+)\*\*", ("wa_prop_d", "wa_prop_n"), 0.0005),
    ("super-voter ratio", r"non-donors \(\*\*([\d.]+)×\*\*\)", "wa_ratio", 0.005),
    ("federal panel donors / top-1% / Gini",
     r"\*\*federal\*\* ([\d,]+) donors / top-1% \*\*([\d.]+)%\*\* / Gini \*\*([\d.]+)\*\*",
     ("wa_fed_n", "wa_fed_top1", "wa_fed_gini"), 0.05),
    ("state panel donors / top-1% / Gini",
     r"\*\*state\*\* ([\d,]+) / \*\*([\d.]+)%\*\* / \*\*([\d.]+)\*\*",
     ("wa_state_n", "wa_state_top1", "wa_state_gini"), 0.05),
    ("pooled generation multipliers",
     r"pooled WA: Silent \*\*([\d.]+)×\*\*,\s*Boomer \*\*([\d.]+)×\*\* over-represented; "
     r"Gen Z \*\*([\d.]+)×\*\*, Millennial \*\*([\d.]+)×\*\*",
     ("wa_pooled_mult_Silent", "wa_pooled_mult_Boomer", "wa_pooled_mult_Gen Z",
      "wa_pooled_mult_Millennial"), 0.005),
    ("federal generation multipliers",
     r"— ([\d.]+)× / ([\d.]+)× / ([\d.]+)× / ([\d.]+)× on the federal panel",
     ("wa_fed_mult_Silent", "wa_fed_mult_Boomer", "wa_fed_mult_Gen Z",
      "wa_fed_mult_Millennial"), 0.005),
    ("two-ZIP3 share, pooled", r"\*\*([\d.]+)% of WA donor dollars", "wa_pooled_zip3", 0.05),
    ("two-ZIP3 share, pooled (F2 restatement)",
     r"([\d.]+)% of dollars from two Seattle ZIP3s", "wa_pooled_zip3", 0.05),
    ("two-ZIP3 share, federal", r"([\d.]+)% federal-only", "wa_fed_zip3", 0.05),
    ("two-ZIP3 share, federal (F2 restatement)",
     r"two-ZIP3 share \*\*([\d.]+)%\*\*", "wa_fed_zip3", 0.05),
    ("top-1% pooled then federal",
     r"supply \*\*([\d.]+)%\*\* of matched dollars pooled, \*\*([\d.]+)%\*\* federal",
     ("wa_pooled_top1", "wa_fed_top1"), 0.05),
    ("top-10% pooled / federal",
     r"top 10% \*\*([\d.]+)%\*\* / \*\*([\d.]+)%\*\*", ("wa_pooled_top10", "wa_fed_top10"), 0.05),
    ("pooled top-1% / top-10% (F2 restatement)",
     r"top-1% \*\*([\d.]+)%\*\*, top-10% \*\*([\d.]+)%\*\*, Gini ([\d.]+)",
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
    ("P(matchable) spread across generations",
     r"generations \(([\d.]+)%–([\d.]+)%", ("wa_pmatch_lo", "wa_pmatch_hi"), 0.05),
    ("IPW shift, Silent and Gen Z — BOTH sides of the arrow",
     r"\(Silent ([\d.]+)→([\d.]+)×, Gen Z ([\d.]+)→([\d.]+)×",
     ("wa_raw_Silent", "wa_ipw_Silent", "wa_raw_Gen Z", "wa_ipw_Gen Z"), 0.005),
    ("federal multipliers restated in the panel note",
     r"on the federal panel \(Silent \*\*([\d.]+)×\*\*,\s*Gen Z \*\*([\d.]+)×\*\*\)",
     ("wa_fed_mult_Silent", "wa_fed_mult_Gen Z"), 0.005),
    ("federal top-1% restated in the withdrawal note",
     r"contradicting the ([\d.]+)% in the panel note", "wa_fed_top1", 0.05),
    ("ID state 65+ share restated in the layer caveat",
     r"The ID crossover and ([\d.]+)% figures", "id_state_65", 0.05),
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
    ("ID Democratic own-party crossover", r"([\d.]+)%\*\* ID → own party", "id_state_dem_donly", 0.05),
    ("recall cost of the primary specification",
     r"discards ([\d]+)–([\d]+)% of matched donors", ("discard_lo", "discard_hi"), 0.5),
    # Replaces the "3.5" literal exemption. The range and its three members are probed
    # SEPARATELY against the same derivation, so a range that stopped spanning its own
    # members fails — which is the defect shape all six of the 2026-08-06 author questions
    # had, and the one thing a single probe on a span cannot catch.
    ("donor share of registrants, the cross-state range",
     r"\*\*~([\d.]+)–([\d.]+)% of voters\*\*", ("donor_share_lo", "donor_share_hi"), 0.05),
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
    ("Finding 6 — scorable races (single-cycle ceiling)",
     r"single cycle \(2024 FEC Schedule-E, (\d+) WA U\.S\. House races\)", "ie_n", 0),
    ("Finding 6 — WA-03 total and net IE",
     r"WA-03 2024 \(\$([\d.]+)M total IE, \+\$([\d.]+)M net pro-Dem\)",
     ("wa03_ie_total", "wa03_ie_net"), 0.05),
    ("Finding 6 — PDC IE with no support/oppose flag",
     r"\$([\d.]+)M of PDC state-legislative IE", "pdc_ie_m", 0.05),
    ("Finding 6 — slope and r (vs does-money-move-votes.md)",
     r"\*\*negative\*\* \(−([\d.]+) pp per \$1M net pro-Dem IE, Pearson r −([\d.]+), n=(\d+)\)",
     ("_neg_ie_slope", "_neg_ie_r", "ie_n"), 0.005),
    ("Finding 6 — fundraising correlation (vs does-money-move-votes.md)",
     r"log2\(D/R\) correlates \*\*\+([\d.]+)\*\* with overperformance",
     "money_r_fundraising", 0.005),
    ("Finding 6 — the same correlation restated in the objection",
     r"\+([\d.]+) is exactly what a true causal effect", "money_r_fundraising", 0.005),
    ("Finding 6 — WA-03 residual (vs does-money-move-votes.md)",
     r"finished \+([\d.]+) pp off its fundamentals", "money_wa03_resid", 0.005),
    # Replaces the "0.00" literal exemption (author answered 2026-08-06: drop the tilde and
    # cite the two-decimal round). Tolerance is the paper's printed precision, not a slack
    # wide enough to let 0.00 back through.
    ("Finding 6 — allocation holdout R2 (vs does-money-move-votes.md)",
     r"cross-cycle holdout R² of \*\*([\d.]+)\*\*", "money_holdout_alloc", 0.005),
]


# --- Coverage gate (ported 2026-08-06; see verify_who_decides_wa for the three rules) ----
# The three findings, partitioned so no slice overlaps another — spans are per-section
# coordinates, so a slice that swallows another reports the inner one's probed cells as
# unmapped. Finding 6's end anchor is the horizontal rule that closes the scraped block;
# it occurs exactly once in that block, and vp.slice_with_offset raises if it moves.
AUDIT_BOUNDS = {
    "finding4": ("### 4. Money and votes", "### 5. The donor class"),
    "finding5": ("### 5. The donor class", "### 6. Money marks strength"),
    "finding6": ("### 6. Money marks strength", " --- "),
}

COVERAGE_EXEMPT = [
    (r"^(?:19|20)\d{2}$", "a calendar year, not a result"),
    (r"^\d{1,2}$", "small integer — list ordinals, insight/failure scores, race counts"),
]

# Every literal here names WHERE the figure is checked, or the open question that closes it.
# "Not a result" with no reason is how a real figure hides — see verify_who_decides_wa.
COVERAGE_EXEMPT_LITERAL: dict[str, str] = {
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
    hhits = [float(x) for x in re.findall(r"allocation holdout R² ([\d.]+)", whole)]
    if not hhits:
        fails.append("Appendix guard: no whole-document occurrence of the allocation "
                     "holdout R² matched — the wording moved, so this guard is disarmed")
    for got in hhits:
        if abs(got - hwant) > 0.005:
            fails.append(f"whole-document allocation holdout R²: paper {got} vs "
                         f"does-money-move-votes.md {hwant}")
    print(f"  restated-outside-the-slice guard: {len(hhits)} whole-document occurrence(s) "
          f"of the allocation holdout R², target {hwant}")
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
    m = re.search(r"### 4\. Money and votes.*?(?=\n## )", text, re.S)
    if not m:
        print("FATAL: could not locate Findings 4-6 in the white paper")
        return 1
    norm = vp.normalise(m.group(0))
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
                              COVERAGE_EXEMPT_SECTIONS)
    fails += _restated_outside_the_slice(d)
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
