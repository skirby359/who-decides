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

SCOPE. Findings 4 and 5 only — the money/donor findings that restate verified cuts.
Findings 1-3 and 6 are covered by their own papers' verifiers or are prospectus items with
no derivable figure. Two things here are deliberately NOT checked and are listed in
UNCHECKED below, so the gap is stated rather than implied.

Run:  python scripts/verify_whitepaper.py
"""
from pathlib import Path
import re
import sys

import duckdb

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PAPER = ROOT / "docs" / "electoral-health-whitepaper.md"
GENS = ["Silent", "Boomer", "Gen X", "Millennial", "Gen Z"]

# Stated, not silently omitted:
UNCHECKED = [
    "bootstrap CIs ([38.6-43.4] etc.) — B=1,000 resamples, too slow for a verifier; "
    "they are asserted in cross-state-fec-money.md §F4 and re-derived by "
    "diag_donor_concentration_bootstrap.py",
    "the occupation blocs (RETIRED $221.7M / NOT EMPLOYED $147.4M) — an outflow-side cut "
    "over individual_contributions, not the matched layer this script derives",
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
]


def main():
    text = PAPER.read_text(encoding="utf-8")
    m = re.search(r"### 4\. Money and votes.*?(?=### 6\.)", text, re.S)
    if not m:
        print("FATAL: could not locate Findings 4-5 in the white paper")
        return 1
    # Normalise: drop blockquote markers, collapse all whitespace. Lets the anchors span
    # line wraps, so re-flowing a paragraph does not silently disarm a probe.
    norm = re.sub(r"\s+", " ", re.sub(r"(?m)^\s*>\s?", "", m.group(0)))

    d = derive()
    print("=" * 84)
    print("WHITE PAPER — Findings 4 & 5, prose scraped and asserted against the databases")
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
    print("WHITE PAPER: Findings 4 & 5 agree with the data")
    print("=" * 84)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
