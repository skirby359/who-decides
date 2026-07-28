"""Verify docs/electoral-health-whitepaper.md Findings 4 and 5 against the databases.

WHY THIS ONE IS BUILT DIFFERENTLY. The other verify_* scripts hold the published figure as
a Python constant and compare it to a fresh derivation. That works for a paper whose
numbers are computed once and stated once. The white paper is not that: it *restates*
figures computed in the donor-class and cross-state papers, and its two observed failure
modes were (a) drifting out of step with those sources and (b) contradicting **itself** —
Finding 5 once gave the federal top-1% as 41.2% in a panel note and 42.4% four lines later.
A constants table cannot catch either, because it never reads the prose: someone can edit
the sentence and leave the constant right, and the check still passes.

So this script SCRAPES THE PROSE. Each probe is a regex anchored on the surrounding words,
and **every** occurrence of the captured figure must equal the derived value. That makes
the two failure modes structurally impossible to miss: a figure stated twice is checked
twice, so an internal contradiction fails on whichever occurrence is wrong.

A probe whose anchor matches nothing is a FAILURE, not a skip. Rewording the sentence out
from under a check is itself the thing to catch — silence there is how the whitepaper drifted
in the first place.

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

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PAPER = ROOT / "docs" / "electoral-health-whitepaper.md"
MONEY_PAPER = ROOT / "docs" / "does-money-move-votes.md"
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
        WITH roll AS (SELECT DISTINCT state_voter_id, is_super_voter, turnout_propensity
                      FROM voter_scores WHERE district_id LIKE 'ld%'),
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
        g = np.empty(BOOT_B); t1 = np.empty(BOOT_B)
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


def _money_paper(d):
    """Cross-document: the white paper's Finding 6 slope/r must match the paper that owns them."""
    t = re.sub(r"\s+", " ", MONEY_PAPER.read_text(encoding="utf-8"))
    m = re.search(r"−([\d.]+) points of residual per \$1M net pro-Democratic IE "
                  r"\(Pearson r = −([\d.]+), n = (\d+)\)", t)
    if m:
        d["ie_slope"], d["ie_r"], d["ie_n"] = -float(m.group(1)), -float(m.group(2)), int(m.group(3))


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
    d["wa_pmatch_lo"], d["wa_pmatch_hi"] = pm_lo, pm_hi
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
    ("IPW shift, Silent and Gen Z",
     r"Silent [\d.]+→([\d.]+)×, Gen Z [\d.]+→([\d.]+)×",
     ("wa_ipw_Silent", "wa_ipw_Gen Z"), 0.005),
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
]


def main():
    text = PAPER.read_text(encoding="utf-8")
    m = re.search(r"### 4\. Money and votes.*?(?=\n## )", text, re.S)
    if not m:
        print("FATAL: could not locate Findings 4-6 in the white paper")
        return 1
    # Normalise: drop blockquote markers, collapse all whitespace. Lets the anchors span
    # line wraps, so re-flowing a paragraph does not silently disarm a probe.
    norm = re.sub(r"\s+", " ", re.sub(r"(?m)^\s*>\s?", "", m.group(0)))

    d = derive()
    print("=" * 84)
    print("WHITE PAPER — Findings 4-6, prose scraped and asserted against the databases")
    print("=" * 84)
    fails = []
    for label, rx, keys, tol in PROBES:
        keys = (keys,) if isinstance(keys, str) else keys
        hits = re.findall(rx, norm)
        if not hits:
            print(f"  FAIL {label:52} ANCHOR NOT FOUND")
            fails.append(f"{label}: anchor not found — the sentence was reworded, or the "
                         f"figure was removed. Re-point the probe or restore the text.")
            continue
        for hit in hits:
            hit = (hit,) if isinstance(hit, str) else hit
            for got, key in zip(hit, keys):
                want = d.get(key)
                if want is None:
                    print(f"  FAIL {label:52} no derived value for {key}")
                    fails.append(f"{label}: derivation '{key}' unavailable")
                    continue
                val = float(got.replace(",", ""))
                ok = abs(val - float(want)) <= tol
                shown = f"{val:,.0f}" if tol == 0 else f"{val:g}"
                wshown = f"{want:,.0f}" if tol == 0 else f"{want:.4g}"
                print(f"  {'ok  ' if ok else 'FAIL'} {label:52} "
                      f"paper {shown:>10}   derived {wshown}")
                if not ok:
                    fails.append(f"{label}: paper says {shown}, data says {wshown}")
        if len(hits) > 1:
            print(f"       ({len(hits)} occurrences checked — a figure stated more than "
                  f"once must agree with the data every time)")

    print("\n  NOT covered by this script:")
    for u in UNCHECKED:
        print(f"    - {u}")

    print("\n" + "=" * 84)
    if fails:
        print(f"WHITE PAPER: {len(fails)} FAILURE(S)")
        print("=" * 84)
        for f in fails:
            print(f"  - {f}")
        return 1
    print("WHITE PAPER: Findings 4-6 agree with the data")
    print("=" * 84)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
