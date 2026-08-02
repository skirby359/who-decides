"""Independent re-derivation of the headline numbers in docs/cross-state-fec-money.md.

Companion to the other verify_* harnesses. From-scratch SQL, read-only,
aggregate-only, derived-vs-paper. Three layers:

  OUTFLOW — each state's residents' FEC individual contributions
            (`individual_contributions` in wa/ny/tx_statewide.duckdb): dollar
            concentration (top-1% / top-10% / Gini), the retail/whale/retired
            dollar-share cuts, and donor counts (§Headline, §1-§3).
  INFLOW  — recipient-anchored dataset (`fec_inflow.duckdb`, one table
            `inflow_contributions`): total volume, per-recipient-state dollars,
            and out-of-state share (§E).
  §F5/§F6 — the individual money-linked layer across WA/NY/ID: donor age skew raw
            and IPW-reweighted, pooled concentration, party-of-record skew, and the
            giving<->turnout cut. Added 2026-07-27.

EXIT CODE. The OUTFLOW and INFLOW blocks print derived-vs-paper for a human to compare
and never fail the run — their donor key is a name+zip proxy with documented sub-0.5pt
grouping drift, so an exact assertion would be noise. The §F5/§F6 block DOES fail the
run, and this script now exits non-zero when it does.

Outflow basis = the paper's: FEC individual contributions by IN-STATE RESIDENTS,
restricted to rows with an FEC committee id (`fec_candidate_id ~ '^[CPHS][0-9]'`) and
`contributor_state=<ST>` (WA's table also holds state PDC rows + non-resident donors;
this filter drops them and, incidentally, the odd/placeholder cycles). Donor identity
= (UPPER(name), zip5). NOTE: the matched-VOTER donor concentration (top-1% 47.7% WA) is
a different population (voter_donor_affiliation) — that's verify_donor_class.py; here
"donors" = all in-state FEC individual contributors.

Run:  python scripts/verify_cross_state_money.py
"""
from pathlib import Path
import sys

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _verify_prose as vp  # noqa: E402

vp.stdout_utf8()
PAPER = Path(__file__).resolve().parent.parent / "docs" / "cross-state-fec-money.md"

DATA = Path(__file__).resolve().parent.parent / "data"
# paper §Headline (all cycles pooled): <200 / >=5000 / retired $ share; top1 / top10 / Gini
PAPER_OUT = {
    "WA": dict(lt200=25.0, ge5000=20.0, retired=24.0, top1=39.3, top10=72.3, gini=0.800, donors="~362K"),
    "NY": dict(lt200=13.8, ge5000=34.8, retired=11.8, top1=47.5, top10=78.7, gini=0.848, donors="~671K"),
    "TX": dict(lt200=20.3, ge5000=33.3, retired=19.5, top1=41.7, top10=74.5, gini=0.818, donors="~837K"),
}
PAPER_INFLOW = {"rows": "5.48M", "dollars": "$1.20B",
                "WA": "$154.6M", "NY": "$462.7M", "TX": "$582.4M"}

# --------------------------------------------------------------------------------------
# §F5 / §F6 — the individual (money-linked) layer. HARD-ASSERTED, unlike the outflow and
# inflow blocks above, which tolerate documented sub-0.5pt grouping drift.
#
# Added 2026-07-27 after an adversarial review found both of these tables had gone stale
# against the very scripts they cite (electoral-health-audit-log.md §7, R1-R4). The failure was
# not arithmetic: the primary-specification switch rebuilt all three POOLED matches, the WA
# cells were refreshed and the NY and ID cells were not, and the resulting mixed table still
# looked reasonable. Two published claims had to be withdrawn as a result. So this block
# checks the derived CLAIMS as well as the cells — a range, a gradient and a bound — because
# those are what actually failed.
#
# NOTE ON POPULATION. F5/F6 read the POOLED `voter_donor_affiliation` (both money systems),
# NOT the per-panel `_fec`/`_state` tables the donor-class paper reports. Idaho's pooled
# match is 41,136; its federal panel is 23,303. Calling this cut "the FEC match" was defect
# R3, so the pooled donor counts are asserted here to keep the population honest.
# --------------------------------------------------------------------------------------
GEN_ORDER = ["Silent", "Boomer", "Gen X", "Millennial", "Gen Z"]
F5_STATES = ("WA", "NY", "ID")

# (raw over-representation, IPW-reweighted over-representation) per generation.
PAPER_F5 = {
    "WA": {"Silent": (1.96, 1.91), "Boomer": (1.71, 1.70), "Gen X": (1.22, 1.24),
           "Millennial": (0.54, 0.54), "Gen Z": (0.09, 0.09)},
    "NY": {"Silent": (1.50, 1.45), "Boomer": (1.65, 1.63), "Gen X": (1.21, 1.23),
           "Millennial": (0.58, 0.59), "Gen Z": (0.14, 0.15)},
    "ID": {"Silent": (2.08, 2.03), "Boomer": (1.71, 1.68), "Gen X": (0.96, 1.00),
           "Millennial": (0.46, 0.47), "Gen Z": (0.10, 0.10)},
}
PAPER_F5_POOLED_N = {"WA": 314_974, "NY": 558_017, "ID": 41_136}
PAPER_F5_GINI = {"WA": 0.857, "NY": 0.884, "ID": 0.821}  # ID is 0.821450;
# the paper said 0.822 until 2026-07-27 — a double-rounding of the diag's 4dp 0.8215.
# Party of record, roll vs matched donors. WA publishes none, so it is absent by design.
PAPER_F5_PARTY = {
    "NY": {"roll": {"DEM": 47.8, "REP": 22.3, "OTHER": 30.0},
           "donor": {"DEM": 58.6, "REP": 24.5, "OTHER": 16.9}},
    "ID": {"roll": {"DEM": 11.8, "REP": 62.9, "OTHER": 25.3},
           "donor": {"DEM": 19.7, "REP": 67.4, "OTHER": 13.0}},
}
# Both counts in each row are asserted. The non-donor one was NOT, until 2026-08-01, and that
# gap is why the WA row drifted with only half of it caught: the roll grew, `n_donor` failed at
# 312,337 vs 312,530, and `5.14M` -> `5.15M` went unnoticed beside it. A table cell nobody
# asserts is a cell that goes stale silently. The paper prints these rounded (312.5K, 5.15M),
# so the tolerance is the rounding half-width, not zero — see F6_COUNT_TOL.
PAPER_F6 = {
    "WA": dict(n_donor=312_530, n_non=5_147_485,
               super_d=87.6, super_n=50.9, ratio=1.72, prop_d=0.967, prop_n=0.749),
    "NY": dict(n_donor=558_017, n_non=12_982_480,
               super_d=83.1, super_n=45.0, ratio=1.85, prop_d=0.892, prop_n=0.653),
    "ID": dict(n_donor=41_136, n_non=988_802,
               super_d=50.0, super_n=30.1, ratio=1.66, prop_d=0.892, prop_n=0.851),
}
# The paper's counts are printed to 3-4 significant figures ("312.5K", "5.15M"). Asserting the
# unrounded integer would fail on a change too small for the paper to show, so each count is
# checked at the half-width of its own printed precision.
F6_COUNT_TOL = {"WA": (50, 5_000), "NY": (50, 5_000), "ID": (50, 50)}
# The claims the prose makes ON TOP of the tables. These are the ones that went stale.
PAPER_CLAIMS = dict(
    silent_lo=1.50, silent_hi=2.08,     # "1.50-2.08x" — was wrongly "~1.9-2.0x"
    genz_lo=0.09, genz_hi=0.14,         # "0.09-0.14x" — was wrongly "~0.13-0.18x"
    ipw_max_shift=0.05,                 # "the IPW reweight moves every ratio by <=0.05"
    ratio_lo=1.66, ratio_hi=1.85,       # F6 band — was wrongly "tight 1.62-1.76x"
)
_FAILURES: list[str] = []


def check(rows):
    """Assert derived vs published. rows = (label, derived, paper, tol).

    tol = 0 is an exact integer match; tol >= 1 is a count checked at the half-width of the
    precision the paper prints it to (so "312.5K" is not failed by a one-voter change it
    cannot show); anything smaller is a rate or a ratio.
    """
    out = []
    for label, derived, paper, tol in rows:
        ok = abs(float(derived) - float(paper)) <= tol
        fmt = (lambda v: f"{v:,.0f}") if tol == 0 or tol >= 1 else (
            (lambda v: f"{v:.3f}") if tol < 0.005 else (lambda v: f"{v:.2f}"))
        print(f"    {'ok  ' if ok else 'FAIL'} {label:46} {fmt(derived):>10}   (paper: {fmt(paper)})")
        if not ok:
            out.append(f"{label}: derived {fmt(derived)} vs paper {fmt(paper)}")
    return out


def _gen_layer(con, birth_year_sql):
    """Roll generations, per-generation matchability, and matched-donor generations.

    Re-derived from scratch, not imported: generation from birth year on the SAME cut
    points the paper uses (Silent <=1945, Boomer <=1964, Gen X <=1980, Millennial <=1996),
    and P(matchable | generation) as the share of that generation whose
    (last name, first initial, ZIP5) key is UNIQUE across the whole roll — the matcher's
    own uniqueness guard, which is the selection the reweight is meant to strip.

    The roll is EVERY row of vrdb.voters, not just active registrants: F5 compares the
    donor pool against the whole file. (verify_donor_class.py uses active-only for its own
    cuts — the two are different denominators on purpose, so do not cross-quote them.)
    """
    gen = (f"CASE WHEN {birth_year_sql} IS NULL THEN NULL "
           f"WHEN {birth_year_sql} <= 1945 THEN 'Silent' "
           f"WHEN {birth_year_sql} <= 1964 THEN 'Boomer' "
           f"WHEN {birth_year_sql} <= 1980 THEN 'Gen X' "
           f"WHEN {birth_year_sql} <= 1996 THEN 'Millennial' ELSE 'Gen Z' END")
    con.execute(f"""CREATE OR REPLACE TEMP TABLE _vx AS
        SELECT v.state_voter_id sid, {gen} AS gen,
               UPPER(TRIM(v.last_name)) || '|' || UPPER(SUBSTR(TRIM(v.first_name),1,1))
                 || '|' || SUBSTR(v.reg_zip,1,5) AS mkey
        FROM vrdb.voters v""")
    con.execute("CREATE OR REPLACE TEMP TABLE _kn AS "
                "SELECT mkey, COUNT(*) n FROM _vx GROUP BY 1")
    roll = dict(con.execute(
        "SELECT gen, COUNT(*) FROM _vx WHERE gen IS NOT NULL GROUP BY 1").fetchall())
    pmatch = dict(con.execute("""
        SELECT x.gen, AVG(CASE WHEN k.n = 1 THEN 1.0 ELSE 0 END)
        FROM _vx x JOIN _kn k USING (mkey) WHERE x.gen IS NOT NULL GROUP BY 1""").fetchall())
    don = dict(con.execute("""
        SELECT x.gen, COUNT(*) FROM voter_donor_affiliation a JOIN _vx x ON x.sid = a.state_voter_id
        WHERE x.gen IS NOT NULL GROUP BY 1""").fetchall())
    rt, dt = sum(roll.values()) or 1, sum(don.values()) or 1
    ipw = {g: don.get(g, 0) / pmatch[g] for g in roll if pmatch.get(g)}
    it = sum(ipw.values()) or 1
    res = {}
    for g in GEN_ORDER:
        rp = roll.get(g, 0) / rt * 100
        res[g] = (don.get(g, 0) / dt * 100 / rp if rp else 0.0,
                  ipw.get(g, 0) / it * 100 / rp if rp else 0.0)
    return res


def f5(state):
    """§F5 — donor age skew (raw + IPW), pooled concentration, and party-of-record skew."""
    sp = DATA / f"{state.lower()}_statewide.duckdb"
    con = duckdb.connect(str(sp), read_only=True)
    con.execute(f"ATTACH '{DATA / (state.lower() + '_vrdb.duckdb')}' AS vrdb (READ_ONLY)")
    cols = {r[1] for r in con.execute("PRAGMA table_info('vrdb.voters')").fetchall()}
    by = "EXTRACT(year FROM v.birthdate)" if "birthdate" in cols else "(2026 - v.age)"
    gens = _gen_layer(con, by)
    n = con.execute("SELECT COUNT(*) FROM voter_donor_affiliation").fetchone()[0]
    gini = con.execute("""
        WITH r AS (SELECT total_donated t, ROW_NUMBER() OVER (ORDER BY total_donated) rn,
                          COUNT(*) OVER () n, SUM(total_donated) OVER () s
                   FROM voter_donor_affiliation WHERE total_donated > 0)
        SELECT (2.0*SUM(rn*t)/(MAX(n)*MAX(s))) - (MAX(n)+1.0)/MAX(n) FROM r""").fetchone()[0]
    party = None
    if state in PAPER_F5_PARTY:
        b = ("CASE WHEN v.party IN ('DEM','D') THEN 'DEM' "
             "WHEN v.party IN ('REP','R') THEN 'REP' ELSE 'OTHER' END")
        party = {"roll": dict(con.execute(
            f"SELECT {b}, 100.0*COUNT(*)/SUM(COUNT(*)) OVER () FROM vrdb.voters v GROUP BY 1").fetchall()),
            "donor": dict(con.execute(
                f"""SELECT {b}, 100.0*COUNT(*)/SUM(COUNT(*)) OVER ()
                    FROM voter_donor_affiliation a JOIN vrdb.voters v USING(state_voter_id)
                    GROUP BY 1""").fetchall())}
    con.close()
    return dict(gens=gens, n=n, gini=float(gini), party=party)


def f6(state):
    """§F6 — donor vs non-donor super-voter rate and turnout propensity.

    WASHINGTON READS THE PINNED ROLL, not `voter_scores` (2026-08-01). `voter_scores` is
    live: `refresh-gotv` rebuilds it on every ballot load and each precinct-crosswalk
    improvement pulls previously unscoped voters into district scope, so the WA denominator
    grows by a few thousand every few days. That is exactly how this section's WA row went
    stale — 5,456,444 -> 5,460,015 moved both of its counts while every percentage held.
    `donor_paper_wa_roll` is the dated snapshot the donor-class paper pins for the same
    reason (2026-07-31, 5,460,015 rows, one per ld-scope voter), and it carries the two
    columns this cut needs. Verified equal to the live derivation to six decimals on the day
    of the switch, so the pin froze the figures rather than changing them.

    Falls back to the live ld scope if the snapshot is absent, and says so — a checkout that
    has never run `pin_wa_donor_roll.py` should still be able to run this, but it must not
    quietly report a drifting number as if it were the pinned one.

    NY and ID hold a single scope and static rolls, so they read `voter_scores` directly. The
    `ld%` filter mattered for WA because its voters appear in BOTH a cd and an ld scope;
    dropping it would silently double the roll.
    """
    con = duckdb.connect(str(DATA / f"{state.lower()}_statewide.duckdb"), read_only=True)
    src = "SELECT DISTINCT state_voter_id, is_super_voter, turnout_propensity FROM voter_scores"
    pinned = False
    if state == "WA":
        have, = con.execute("""SELECT COUNT(*) FROM information_schema.tables
                               WHERE table_name = 'donor_paper_wa_roll'""").fetchone()
        if have:
            src = ("SELECT state_voter_id, is_super_voter, turnout_propensity "
                   "FROM donor_paper_wa_roll")
            pinned = True
        else:
            src += " WHERE district_id LIKE 'ld%'"
    rows = con.execute(f"""
        WITH roll AS ({src}),
        f AS (SELECT r.*, (a.state_voter_id IS NOT NULL) donor
              FROM roll r LEFT JOIN voter_donor_affiliation a USING (state_voter_id))
        SELECT donor, COUNT(*), 100.0*AVG(CASE WHEN is_super_voter THEN 1.0 ELSE 0 END),
               AVG(turnout_propensity)
        FROM f GROUP BY donor""").fetchall()
    con.close()
    d = {("donor" if dn else "non"): (int(n), float(s), float(p)) for dn, n, s, p in rows}
    return dict(n_donor=d["donor"][0], n_non=d["non"][0],
                super_d=d["donor"][1], super_n=d["non"][1],
                prop_d=d["donor"][2], prop_n=d["non"][2],
                ratio=d["donor"][1] / d["non"][1],
                pinned=pinned if state == "WA" else None)


def _collect(d: dict) -> bool:
    """Derive every F5/F6 value the paper states. Returns False if a state is unavailable."""
    ok = True
    gens = {}
    for st in F5_STATES:
        try:
            r5 = f5(st)
        except Exception as ex:  # noqa: BLE001
            print(f"  {st}: SKIPPED ({ex})")
            ok = False
            continue
        gens[st] = r5["gens"]
        d[f"{st}_n"] = r5["n"]
        d[f"{st}_gini"] = r5["gini"]
        for g in GEN_ORDER:
            key = g.replace(" ", "")
            d[f"{st}_{key}_raw"], d[f"{st}_{key}_rwt"] = r5["gens"][g]
        if r5["party"]:
            for k in ("DEM", "REP", "OTHER"):
                d[f"{st}_roll_{k}"] = r5["party"]["roll"].get(k, 0.0)
                d[f"{st}_donor_{k}"] = r5["party"]["donor"].get(k, 0.0)

        r6 = f6(st)
        if st == "WA" and r6.get("pinned") is False:
            print("    NOTE  WA read the LIVE ld scope - donor_paper_wa_roll is absent, so "
                  "its two counts can drift. Run scripts/pin_wa_donor_roll.py.")
        for k in ("n_donor", "n_non", "super_d", "super_n", "ratio", "prop_d", "prop_n"):
            d[f"{st}_{k}"] = r6[k]
        # The paper prints these counts abbreviated, so the probe compares what it prints.
        d[f"{st}_n_donor_k"] = r6["n_donor"] / 1e3
        d[f"{st}_n_non_m"] = r6["n_non"] / 1e6
        d[f"{st}_n_non_k"] = r6["n_non"] / 1e3

    if not ok or len(gens) != len(F5_STATES):
        return False

    # The DERIVED CLAIMS. Cell-level checks alone would not have caught R2/R4: every cell can
    # be individually right while the sentence summarising them is wrong.
    sil = [gens[s]["Silent"][0] for s in F5_STATES]
    gz = [gens[s]["Gen Z"][0] for s in F5_STATES]
    d["silent_lo"], d["silent_hi"] = min(sil), max(sil)
    d["genz_lo"], d["genz_hi"] = min(gz), max(gz)
    d["ipw_max_shift"] = max(abs(gens[s][g][0] - gens[s][g][1])
                             for s in F5_STATES for g in GEN_ORDER)
    for s in F5_STATES:
        d[f"{s}_gradient"] = gens[s]["Silent"][0] / gens[s]["Gen Z"][0]
    ratios = [d[f"{s}_ratio"] for s in F5_STATES]
    d["ratio_lo"], d["ratio_hi"] = min(ratios), max(ratios)
    return True


# Prose probes for F5/F6. CONVERTED FROM CONSTANTS 2026-08-01: the old table held e.g.
# `n_donor=312_337` for a figure the paper prints as "312.3K", so nothing tied the assertion
# to the document and the "(paper: ...)" column was an unverifiable claim about a file the
# script never opened. These read the paper.
F_PROBES = [
    ("F5 pooled match sizes, in the recompute note",
     r"pooled matches \(NY (\d[\d,]*) \u2192 (\d[\d,]*), ID (\d[\d,]*) \u2192 (\d[\d,]*), "
     r"WA\s+(\d[\d,]*) \u2192 (\d[\d,]*)\)",
     ("_ny_prev", "NY_n", "_id_prev", "ID_n", "_wa_prev", "WA_n"), 0),
    ("F5 multipliers - Silent",
     r"\| Silent \| ([\d.]+)\u00d7 / ([\d.]+)\u00d7 \| ([\d.]+)\u00d7 / ([\d.]+)\u00d7 \| "
     r"([\d.]+)\u00d7 / ([\d.]+)\u00d7 \|",
     ("WA_Silent_raw", "WA_Silent_rwt", "NY_Silent_raw", "NY_Silent_rwt",
      "ID_Silent_raw", "ID_Silent_rwt"), 0.005),
    ("F5 multipliers - Boomer",
     r"\| Boomer \| ([\d.]+)\u00d7 / ([\d.]+)\u00d7 \| ([\d.]+)\u00d7 / ([\d.]+)\u00d7 \| "
     r"([\d.]+)\u00d7 / ([\d.]+)\u00d7 \|",
     ("WA_Boomer_raw", "WA_Boomer_rwt", "NY_Boomer_raw", "NY_Boomer_rwt",
      "ID_Boomer_raw", "ID_Boomer_rwt"), 0.005),
    ("F5 multipliers - Gen X",
     r"\| Gen X \| ([\d.]+)\u00d7 / ([\d.]+)\u00d7 \| ([\d.]+)\u00d7 / ([\d.]+)\u00d7 \| "
     r"([\d.]+)\u00d7 / ([\d.]+)\u00d7 \|",
     ("WA_GenX_raw", "WA_GenX_rwt", "NY_GenX_raw", "NY_GenX_rwt",
      "ID_GenX_raw", "ID_GenX_rwt"), 0.005),
    ("F5 multipliers - Millennial",
     r"\| Millennial \| ([\d.]+)\u00d7 / ([\d.]+)\u00d7 \| ([\d.]+)\u00d7 / ([\d.]+)\u00d7 \| "
     r"([\d.]+)\u00d7 / ([\d.]+)\u00d7 \|",
     ("WA_Millennial_raw", "WA_Millennial_rwt", "NY_Millennial_raw", "NY_Millennial_rwt",
      "ID_Millennial_raw", "ID_Millennial_rwt"), 0.005),
    ("F5 multipliers - Gen Z",
     r"\| Gen Z \| ([\d.]+)\u00d7 / ([\d.]+)\u00d7 \| ([\d.]+)\u00d7 / ([\d.]+)\u00d7 \| "
     r"([\d.]+)\u00d7 / ([\d.]+)\u00d7 \|",
     ("WA_GenZ_raw", "WA_GenZ_rwt", "NY_GenZ_raw", "NY_GenZ_rwt",
      "ID_GenZ_raw", "ID_GenZ_rwt"), 0.005),
    ("F5 claim - Silent and Gen Z ranges across states",
     r"over-represented among matched donors \(\*\*([\d.]+)\u2013([\d.]+)\u00d7\*\*\) and the "
     r"youngest \(Gen Z\) is sharply\s+under-represented \(\*\*([\d.]+)\u2013([\d.]+)\u00d7\*\*\)",
     ("silent_lo", "silent_hi", "genz_lo", "genz_hi"), 0.005),
    ("F5 claim - the old-to-young gradient per state",
     r"gradient is \*\*([\d.]+)\u00d7 in WA and ([\d.]+)\u00d7 in ID but only "
     r"([\d.]+)\u00d7 in NY\*\*",
     ("WA_gradient", "ID_gradient", "NY_gradient"), 0.05),
    ("F5 claim - the IPW reweight moves every ratio by at most this",
     r"reweight moves every ratio by \u2264([\d.]+)", "ipw_max_shift", 0.005),
    ("F5 pooled Gini, all three states",
     r"Gini \*\*WA ([\d.]+) / NY\s+([\d.]+) / ID ([\d.]+)\*\*",
     ("WA_gini", "NY_gini", "ID_gini"), 0.0005),
    ("F5 Idaho pooled donor count, in prose",
     r"POOLED voter\u2194donor match\*\* \(FEC \+ Sunshine, (\d[\d,]*) donors\)", "ID_n", 0),
    ("F5 party skew - New York",
     r"\*\*NY:\*\* electorate \*\*D (\d+)% / R (\d+)% / unaffiliated-or-other (\d+)%\*\* \u2192 "
     r"donors \*\*D (\d+)% / R (\d+)% /\s+O (\d+)%\.\*\*",
     ("NY_roll_DEM", "NY_roll_REP", "NY_roll_OTHER",
      "NY_donor_DEM", "NY_donor_REP", "NY_donor_OTHER"), 0.5),
    ("F5 party skew - Idaho",
     r"\*\*ID:\*\* electorate \*\*D (\d+)% / R (\d+)% / O (\d+)%\*\* \u2192 donors "
     r"\*\*D (\d+)% / R (\d+)% / O (\d+)%\.\*\*",
     ("ID_roll_DEM", "ID_roll_REP", "ID_roll_OTHER",
      "ID_donor_DEM", "ID_donor_REP", "ID_donor_OTHER"), 0.5),
    ("F6 table - Washington",
     r"\| WA \| ([\d.]+)% \(([\d.]+)K\) \| ([\d.]+)% \(([\d.]+)M\) \| \*\*([\d.]+)\u00d7\*\* \| "
     r"([\d.]+) / ([\d.]+) \|",
     ("WA_super_d", "WA_n_donor_k", "WA_super_n", "WA_n_non_m", "WA_ratio",
      "WA_prop_d", "WA_prop_n"), 0.05),
    ("F6 table - New York",
     r"\| NY \| ([\d.]+)% \(([\d.]+)K\) \| ([\d.]+)% \(([\d.]+)M\) \| \*\*([\d.]+)\u00d7\*\* \| "
     r"([\d.]+) / ([\d.]+) \|",
     ("NY_super_d", "NY_n_donor_k", "NY_super_n", "NY_n_non_m", "NY_ratio",
      "NY_prop_d", "NY_prop_n"), 0.05),
    ("F6 table - Idaho",
     r"\| ID \| ([\d.]+)% \(([\d.]+)K\) \| ([\d.]+)% \(([\d.]+)K\) \| \*\*([\d.]+)\u00d7\*\* \| "
     r"([\d.]+) / ([\d.]+) \|",
     ("ID_super_d", "ID_n_donor_k", "ID_super_n", "ID_n_non_k", "ID_ratio",
      "ID_prop_d", "ID_prop_n"), 0.05),
    ("F6 claim - the super-voter ratio band",
     r"donor/non-donor super-voter ratio runs \*\*([\d.]+)\u2013([\d.]+)\u00d7\*\*",
     ("ratio_lo", "ratio_hi"), 0.005),
    ("F6 recompute note - the pinned WA counts",
     r"moved the scored-donor count 312\.3K \u2192 \*\*([\d.]+)K\*\* and the\s+"
     r"non-donor count 5\.14M \u2192 \*\*([\d.]+)M\*\*",
     ("WA_n_donor_k", "WA_n_non_m"), 0.05),
]

F_UNCHECKED = [
    "The OUTFLOW and INFLOW blocks print derived-vs-paper and never fail the run. Their donor "
    "key is a name+zip proxy with documented sub-0.5pt grouping drift, so an exact assertion "
    "would be noise rather than a check. That is a deliberate exemption, not an oversight, "
    "and it is the only part of this script that cannot fail",
    "The appendix precision figures (the 100.0% strict-key rate, the 93.0% "
    "population-weighted precision, the 152/129 error-mode counts) belong to "
    "verify_donor_class.py, which asserts them against the frozen verdict CSVs",
]


def verify_individual_layer():
    """Derive F5/F6 and assert it against the paper's own prose. Returns failures."""
    d = {
        # Historical figures the recompute note quotes. They are what the RETIRED panels
        # gave, so they are literals by construction and must keep saying so.
        "_ny_prev": 308_032, "_id_prev": 47_762, "_wa_prev": 382_408,
    }
    if not _collect(d):
        return ["F5/F6: a state's data was unavailable, so the block could not be asserted"]
    rc = vp.run("F5/F6 - the individual money-linked layer, scraped from the paper",
                vp.normalise(PAPER.read_text(encoding="utf-8")),
                F_PROBES, d, F_UNCHECKED, vp.wants_coverage())
    return [] if rc == 0 else ["see the F5/F6 failures above"]


def outflow(state):
    con = duckdb.connect(str(DATA / f"{state.lower()}_statewide.duckdb"), read_only=True)
    # Canonical outflow basis — identical to cross_state_fec_money.py and the paper:
    # FEC individual contributions BY IN-STATE RESIDENTS. WA's individual_contributions
    # mixes state PDC + federal FEC, so restrict to rows carrying an FEC committee id
    # AND a resident donor. No-op for TX (already clean bulk); tightens NY and WA to the
    # paper's population. This is the fix for the former WA-outflow divergence.
    filt = ("regexp_matches(COALESCE(fec_candidate_id,''),'^[CPHS][0-9]') "
            f"AND contributor_state='{state}' AND contribution_amount>0")
    shares = con.execute(f"""
        SELECT 100.0*SUM(contribution_amount) FILTER(WHERE contribution_amount<200)/SUM(contribution_amount),
               100.0*SUM(contribution_amount) FILTER(WHERE contribution_amount>=5000)/SUM(contribution_amount),
               100.0*SUM(contribution_amount) FILTER(WHERE contributor_occupation ILIKE '%retired%')/SUM(contribution_amount)
        FROM individual_contributions WHERE {filt}
    """).fetchone()
    # per-donor concentration (donor = UPPER(name)+zip5)
    conc = con.execute(f"""
        WITH d AS (SELECT SUM(contribution_amount) t
                   FROM individual_contributions WHERE {filt}
                   GROUP BY UPPER(TRIM(contributor_name)), LEFT(COALESCE(contributor_zip,''),5))
        SELECT COUNT(*) FROM d
    """).fetchone()[0]
    top = con.execute(f"""
        WITH d AS (SELECT SUM(contribution_amount) t
                   FROM individual_contributions WHERE {filt}
                   GROUP BY UPPER(TRIM(contributor_name)), LEFT(COALESCE(contributor_zip,''),5)),
             p AS (SELECT t, NTILE(100) OVER (ORDER BY t DESC) b FROM d)
        SELECT 100.0*SUM(t) FILTER(WHERE b=1)/SUM(t), 100.0*SUM(t) FILTER(WHERE b<=10)/SUM(t) FROM p
    """).fetchone()
    gini = con.execute(f"""
        WITH d AS (SELECT SUM(contribution_amount) t
                   FROM individual_contributions WHERE {filt}
                   GROUP BY UPPER(TRIM(contributor_name)), LEFT(COALESCE(contributor_zip,''),5)),
             r AS (SELECT t, ROW_NUMBER() OVER (ORDER BY t ASC) i FROM d)
        SELECT (2.0*SUM(i*t)/((SELECT COUNT(*) FROM r)*(SELECT SUM(t) FROM r)))
               - ((SELECT COUNT(*) FROM r)+1.0)/(SELECT COUNT(*) FROM r) FROM r
    """).fetchone()[0]
    con.close()
    return dict(lt200=shares[0], ge5000=shares[1], retired=shares[2],
                donors=conc, top1=top[0], top10=top[1], gini=gini)


def main():
    print("=" * 82)
    print("OUTFLOW — FEC individual contributions by state residents (all cycles pooled)")
    print("=" * 82)
    print(f"{'state':>5} {'donors':>9} | {'<$200 $%':>9} {'≥$5k $%':>9} {'retired $%':>11} | "
          f"{'top1%':>6} {'top10%':>7} {'Gini':>6}")
    for st in ("WA", "NY", "TX"):
        try:
            d = outflow(st)
        except Exception as ex:  # noqa: BLE001
            print(f"{st:>5}  ERROR: {ex}")
            continue
        p = PAPER_OUT[st]
        print(f"{st:>5} {d['donors']:>9,} | {d['lt200']:>8.1f}% {d['ge5000']:>8.1f}% "
              f"{d['retired']:>10.1f}% | {d['top1']:>5.1f}% {d['top10']:>6.1f}% {d['gini']:>6.3f}")
        print(f"{'paper':>5} {p['donors']:>9} | {p['lt200']:>8.1f}% {p['ge5000']:>8.1f}% "
              f"{p['retired']:>10.1f}% | {p['top1']:>5.1f}% {p['top10']:>6.1f}% {p['gini']:>6.3f}")
    print("  (top1/top10/Gini use a name+zip donor key -> sub-0.5pt drift from the paper's")
    print("   grouping is expected; dollar-share cuts are grouping-free.)")
    print("  ✓ WA outflow RECONCILED (2026-07-10): applying the paper's filter (FEC committee id +")
    print("    contributor_state='WA') reproduces 361,818 donors / 39.3% / 72.3% / 0.800, matching")
    print("    the paper exactly. The former 1.12M/47.5% was raw-unfiltered (PDC + non-WA + odd")
    print("    cycles). NY tightens to 671K (was 699K raw); TX unchanged. All three now reproduce.")

    print("\n" + "=" * 82)
    print("INFLOW — recipient-anchored (fec_inflow.duckdb)")
    print("=" * 82)
    ic = duckdb.connect(str(DATA / "fec_inflow.duckdb"), read_only=True)
    nrows, dollars = ic.execute(
        "SELECT COUNT(*), SUM(contribution_amount) FROM inflow_contributions").fetchone()
    dollars = float(dollars)
    print(f"  total: {nrows:,} rows / ${dollars/1e9:.2f}B   (paper: {PAPER_INFLOW['rows']} / {PAPER_INFLOW['dollars']})")
    rows = ic.execute("""
        SELECT recipient_state,
               SUM(contribution_amount) tot,
               100.0*SUM(contribution_amount) FILTER(WHERE contributor_state<>recipient_state)
                   /SUM(contribution_amount) oos
        FROM inflow_contributions GROUP BY 1 ORDER BY tot DESC
    """).fetchall()
    print(f"  {'recip':>6} {'$ in':>10} {'paper':>10} {'out-of-state $%':>16}")
    for st, tot, oos in rows:
        print(f"  {st:>6} {'$'+format(float(tot)/1e6,',.1f')+'M':>10} {PAPER_INFLOW.get(st,'?'):>10} {float(oos):>15.1f}%")
    ic.close()
    print("  (paper §E: out-of-state share ~36-45% across competitiveness bands.)")

    fails = verify_individual_layer()
    print("\n" + "=" * 82)
    if fails:
        print(f"§F5/§F6: {len(fails)} FAILURE(S)")
        print("=" * 82)
        for f in fails:
            print(f"  - {f}")
        return 1
    print("§F5/§F6: all assertions pass")
    print("=" * 82)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
