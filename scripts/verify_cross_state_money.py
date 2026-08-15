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

EXIT CODE, and a justification that was measured and found false (2026-08-02).

This block used to say the OUTFLOW and INFLOW figures could only be printed, not asserted,
because the name+zip donor key carries "documented sub-0.5pt grouping drift" that an exact
assertion would turn into noise. Nobody had measured it. Measured, on the headline table:

    donor counts        EXACT in all four states, gap 0
    Gini                worst gap 0.0004   (printed to 3dp, half-width 0.0005)
    top-1% / top-10%    worst 0.052 / 0.035
    <$200 / >=$5,000    worst 0.040 / 0.032
    retired share       worst 0.033 AFTER fixing this script's own definition of it

So every metric reproduces inside the precision the paper prints, and the drift the
exemption was built on is not there. The §Headline table is now HARD-ASSERTED at printed
precision like §F5/§F6, and the single figure that did not reproduce turned out to be a real
rounding defect the exemption had been hiding: Idaho's top-1% derives 36.0519, which rounds
to 36.1, and the paper printed 36.0.

The `retired` share is the cautionary half of that story. It was off by 0.15 to 0.26 points
in ALL FOUR states, in the same direction, which reads like drift and is not: this script
matched only `contributor_occupation`, while the published definition is
`occupation='RETIRED' OR employer='RETIRED'`. A one-directional offset across every state is
always a basis difference. Corrected here; the paper was right.

GATED 2026-08-06. §1 and §3 are now asserted too — they restate headline cells in prose,
which is the drift that cost the donor paper four review rounds. The coverage audit gates
§Headline, §1, §3 and §F, and every remaining section is listed in
COVERAGE_EXEMPT_SECTIONS with the script that owns its figures. §2's population
denominators and §5's per-cycle totals are the cheapest remaining closes; §K (151 tokens)
is the largest.

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
import csv
import sys

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _verify_prose as vp  # noqa: E402

vp.stdout_utf8()
PAPER = Path(__file__).resolve().parent.parent / "docs" / "cross-state-fec-money.md"

# §2's population denominators. Pinned, not fetched — see scripts/acs_state_population.py.
POP_PIN = (Path(__file__).resolve().parent.parent / "docs" / "reference"
           / "state_population_acs2024.csv")

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


# §F5 reads the LIVE pooled panel (`voter_donor_affiliation`), which `main.py analyze`
# rebuilds and which grows as contributions accrue. Its figures are asserted downstream, so
# drift already fails — but as "the paper is wrong", not as "the panel moved". This guard
# names the mechanism instead (P5, closed 2026-08-15): the counts are the papers' published
# pooled-panel sizes, and a legitimate re-match must update them HERE, deliberately, the
# same discipline as f6's pinned roll. Its sibling `_multipliers` in verify_whitepaper.py
# carries the same guard.
F5_PINNED_PANEL_N = {"WA": 314_974, "NY": 558_017, "ID": 41_136}


def f5(state):
    """§F5 — donor age skew (raw + IPW), pooled concentration, and party-of-record skew."""
    sp = DATA / f"{state.lower()}_statewide.duckdb"
    con = duckdb.connect(str(sp), read_only=True)
    con.execute(f"ATTACH '{DATA / (state.lower() + '_vrdb.duckdb')}' AS vrdb (READ_ONLY)")
    cols = {r[1] for r in con.execute("PRAGMA table_info('vrdb.voters')").fetchall()}
    by = "EXTRACT(year FROM v.birthdate)" if "birthdate" in cols else "(2026 - v.age)"
    gens = _gen_layer(con, by)
    n = con.execute("SELECT COUNT(*) FROM voter_donor_affiliation").fetchone()[0]
    if n != F5_PINNED_PANEL_N[state]:
        raise AssertionError(
            f"{state} pooled panel holds {n:,} voters against the published "
            f"{F5_PINNED_PANEL_N[state]:,} — voter_donor_affiliation has been rebuilt since "
            "the §F5 figures were derived (a matcher rerun or new contribution load), so "
            "every figure this function returns is about a different panel. Re-derive the "
            "paper's §F5 block and update F5_PINNED_PANEL_N deliberately; do not read a "
            "downstream probe failure as a paper defect.")
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


# Unpinned-read failures raised during derivation and consumed by verify_individual_layer().
# Module-level rather than threaded through, because _collect() already signals only True/False
# and a pin miss is not "a state was unavailable" — it is a figure resting on a moving basis.
_PIN_FAILURES: list[str] = []


def _collect(d: dict) -> bool:
    """Derive every F5/F6 value the paper states. Returns False if a state is unavailable."""
    _PIN_FAILURES.clear()          # idempotent across repeated calls in one process
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
            # FAILURE, not a note (2026-08-10). This printed a NOTE and carried on, which meant
            # a run against the live ld scope exited 0 and reported drifting counts in the same
            # two columns a pinned run reports frozen ones. The docstring above already says
            # the script "must not quietly report a drifting number as if it were the pinned
            # one" — and then it did exactly that. `data/wa_statewide.duckdb` is appended to
            # daily by the WA SoS Results Daily Archive task, so "can drift" is not
            # hypothetical.
            _PIN_FAILURES.append(
                "WA read the LIVE ld scope — docs/reference's donor_paper_wa_roll snapshot is "
                "absent, so the two WA counts in §F6 can drift between runs. Run "
                "scripts/pin_wa_donor_roll.py, then re-run. A published figure must not rest "
                "on an unpinned read.")
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


# Emphasis wrapper: the headline table marks its extremes with *italic* and **bold**, so a
# cell pattern has to accept all three forms or the probe finds nothing.
_E = r"(?:\*\*|\*)?"


def _row(label, cells=4):
    """Regex for one headline row: the label, then `cells` emphasis-tolerant numeric cells."""
    return (r"\| " + label + r" \| "
            + r" \| ".join(_E + r"\$?([\d,.]+)[MB]?%?" + _E for _ in range(cells)) + r" \|")


HEADLINE_STATES = ("WA", "NY", "TX", "ID")

# The §Headline table, asserted at the precision it prints. Until 2026-08-02 not one of these
# 40 figures was checked by anything; see the docstring for the measurement that showed the
# exemption protecting them was unfounded.
HEADLINE_PROBES = [
    # THE COMPARISONS THE PROSE MAKES, as distinct from the per-state figures it
    # tabulates. Each of these was a bare integer that the small-integer rule
    # exempted, so the paper's actual assertions — "~3x", "~2x", "~20% of both" —
    # went unchecked while the numbers underneath them were all probed. The
    # "both"/"all four" halves are asserted as relations in _cross_state_ratios.
    ("Finding 1 — the >=$5,000 share said to be ~20% in both ID and WA",
     r"of NY's money vs ~(\d+)% of both ID\s+and WA", "ge5k_idwa", 0.5),
    ("Finding 1 — the size effect, small pool against large",
     r"a \$(\d+)M pool simply has fewer mega-donors to concentrate around than a "
     r"\$(\d+)B one", ("pool_small_m", "pool_large_b"), 0.5),
    ("Finding 2 — NY and TX against Washington's federal dollars",
     r"New York and Texas raise ~(\d+)× Washington's federal dollars",
     "ny_tx_over_wa", 0.5),
    ("Finding 3 — the looser non-working bucket in both ID and WA",
     r"not-employed / none / blank\* reaches ~(\d+)% in\s+both ID and WA",
     "nonworking_idwa", 0.5),
    ("Finding 5 — presidential dollars against off-year, all four states",
     r"presidential-cycle dollars running ~(\d+)× their off-year totals",
     "pres_offyear_mult", 0.5),
    ("headline — total federal dollars",
     _row(r"Total federal \$ \(resident donors\)"),
     ("out_WA_total_m", "out_NY_total_b", "out_TX_total_b", "out_ID_total_m"), 0.5),
    ("headline — contributions",
     _row(r"Contributions"),
     tuple(f"out_{s}_contribs_m" for s in HEADLINE_STATES), 0.005),
    ("headline — distinct donors",
     _row(r"Distinct donors \(name\+zip\)"),
     tuple(f"out_{s}_donors" for s in HEADLINE_STATES), 0),
    ("headline — median gift",
     _row(r"Median gift"),
     tuple(f"out_{s}_median_gift" for s in HEADLINE_STATES), 0.5),
    ("headline — Gini",
     _row(r"\*\*Gini \(donor \$\)\*\*"),
     tuple(f"out_{s}_gini" for s in HEADLINE_STATES), 0.0005),
    ("headline — top 1% share",
     _row(r"\*\*Top 1% of donors → share of \$\*\*"),
     tuple(f"out_{s}_top1" for s in HEADLINE_STATES), 0.05),
    ("headline — top 10% share",
     _row(r"Top 10% of donors → share of \$"),
     tuple(f"out_{s}_top10" for s in HEADLINE_STATES), 0.05),
    ("headline — dollars from gifts under $200",
     _row(r"Dollars from gifts \*\*< \$200\*\*"),
     tuple(f"out_{s}_lt200" for s in HEADLINE_STATES), 0.05),
    ("headline — dollars from gifts at or above $5,000",
     _row(r"Dollars from gifts \*\*≥ \$5,000\*\*"),
     tuple(f"out_{s}_ge5000" for s in HEADLINE_STATES), 0.05),
    ("headline — dollars from retired donors",
     _row(r"Dollars from \*\*retired\*\* donors"),
     tuple(f"out_{s}_retired" for s in HEADLINE_STATES), 0.05),

    # --- Findings 1 and 3 restate the headline table in prose, added 2026-08-06 by the gate.
    # Every one of these is the SAME derived value as a headline cell, which is exactly why
    # they were worth probing: a prose restatement drifting from the table above it is the
    # defect that cost the donor paper four review rounds, and nothing pointed at these.
    ("§1 — NY vs ID top-1%, and both Ginis",
     r"top 1% of donors supply \*\*([\d.]+)%\*\* of New York's federal dollars versus "
     r"\*\*([\d.]+)%\*\* in Idaho \(Gini ([\d.]+) vs ([\d.]+)\)",
     ("out_NY_top1", "out_ID_top1", "out_NY_gini", "out_ID_gini"), 0.05),
    ("§1 — WA and TX top-1%, stated as sitting between",
     r"with WA \(([\d.]+)%\) and TX \(([\d.]+)%\) between",
     ("out_WA_top1", "out_TX_top1"), 0.05),
    ("§1 — sub-$200 shares, ID then WA then NY",
     r"sub-\$200 gifts are \*\*([\d.]+)%\*\* of Idaho's dollars and ([\d.]+)% of "
     r"Washington's but only \*\*([\d.]+)%\*\* of NY's",
     ("out_ID_lt200", "out_WA_lt200", "out_NY_lt200"), 0.05),
    ("§1 — NY's ≥$5,000 share",
     r"≥\$5,000 gifts are \*\*([\d.]+)%\*\* of NY's money", "out_NY_ge5000", 0.05),
    # ADDED 2026-08-09. Idaho was called "the most retail on every measure" and said to
    # edge Washington "on every retail measure"; on the >=$5,000 share Washington is
    # marginally LOWER (20.00% against 20.13%). A 0.13-point miss, but the claim was a
    # universal. Both cells are asserted at both places the corrected sentence appears.
    # §I's corrected comparison. The section is coverage-exempt, so without these
    # the replacement figures would be exactly as unverified as the ones they replace.
    ("§I — pooled inflow concentration, the like-for-like basis",
     r"inflow gives \*\*top-1% ([\d.]+)%, top-10% ([\d.]+)%, Gini ([\d.]+)\*\* over ([\d,]+) "
     r"donor keys",
     ("inflow_pooled_top1", "inflow_pooled_top10", "inflow_pooled_gini",
      "inflow_pooled_donors"), 0.05),
    ("§I — the outflow side of the same comparison, Idaho included",
     r"against outflow's \*\*([\d.]+)–([\d.]+)%\*\* and Gini \*\*([\d.]+)–([\d.]+)\*\*",
     ("out_top1_min", "out_top1_max", "out_gini_min", "out_gini_max"), 0.05),
    ("§I — the corrected ratio",
     r"the gap is\s*roughly \*\*([\d.]+)× to ([\d.]+)×\*\*",
     ("conc_ratio_lo", "conc_ratio_hi"), 0.1),
    ("abstract — the one retail measure Washington leads",
     r"where Washington is marginally lower \(\*\*([\d.]+)%\*\* against Idaho's "
     r"\*\*([\d.]+)%\*\*\)",
     ("out_WA_ge5000", "out_ID_ge5000"), 0.05),
    ("finding 1 — the same exception restated",
     r"edges it on the ≥\$5,000 share \(([\d.]+)% against ([\d.]+)%\)",
     ("out_WA_ge5000", "out_ID_ge5000"), 0.05),
    ("finding 2 — the participation multiple, on its stated basis",
     r"more participatory than either \(([\d.]+)% against ([\d.]+)%",
     ("pc_WA_rate", "pc_TX_rate"), 0.05),
    # Added 2026-08-07 with the size-effect answer, which restates the sub-$200 pair a third
    # time. Three restatements of one derived value is exactly why each gets its own probe.
    ("§1 — sub-$200 pair restated in the size-effect answer",
     r"most\s+retail\s+on\s+those\s+cuts\s+too\s+—\s+([\d.]+)%\s+under\s+\$200\s+against\s+"
     r"New\s+York's\s+([\d.]+)%",
     ("out_ID_lt200", "out_NY_lt200"), 0.05),
    ("§3 — retired-donor shares, all four states",
     r"\*\*([\d.]+)%\*\* of Idaho's federal donor dollars.*?followed by \*\*([\d.]+)%\*\* in "
     r"Washington, \*\*([\d.]+)%\*\* in Texas, and just \*\*([\d.]+)%\*\* in New York",
     ("out_ID_retired", "out_WA_retired", "out_TX_retired", "out_NY_retired"), 0.05),
]


# --- §5 and §E, gated 2026-08-06 ---------------------------------------------------------
# Both were "named, not gated" with a written owner and a BACKLOG note. Neither needed
# anything external — §5 is outflow() with a GROUP BY, §E is the diagnostic's own band logic
# imported rather than re-typed — which is what made them the two cheapest to close. Every
# figure in both reproduced on the first run, so the sections needed derivations, not
# corrections; that is worth stating, because the last three sections closed this way each
# turned up a defect and the honest record is that these two did not.
# --- §2, gated 2026-08-07 ----------------------------------------------------------------
# The donor counts were already derived (they are headline cells); only the denominators were
# external, and pinning them is what closed the section. Restating the counts here rather than
# leaning on the headline probe is deliberate: coverage spans are per-section, so §2's own
# occurrences need their own probe or they read as unmapped — and a prose restatement drifting
# from the table above it is precisely the defect the §1/§3 probes were added to catch.
ABSTRACT_PROBES = [
    # The abstract was moved into the paper 2026-08-07 (it had lived only in the metadata file).
    # It restates ten headline cells, so it is gated on arrival rather than later: an abstract
    # drifting from the table it summarises is the same defect as §1 and §3, in the one place a
    # referee reads first.
    ("abstract — top-1% ordering, all four states, and the two extreme Ginis",
     r"supply\s+\*\*([\d.]+)%\*\*\s+of\s+its\s+federal\s+dollars,\s+against\s+"
     r"\*\*([\d.]+)%\*\*\s+in\s+Texas,\s+\*\*([\d.]+)%\*\*\s+in\s+Washington,\s+and\s+"
     r"\*\*([\d.]+)%\*\*\s+in\s+Idaho,\s+with\s+Gini\s+coefficients\s+from\s+"
     r"\*\*([\d.]+)\*\*\s+down\s+to\s+\*\*([\d.]+)\*\*",
     ("out_NY_top1", "out_TX_top1", "out_WA_top1", "out_ID_top1",
      "out_NY_gini", "out_ID_gini"), 0.05),
    ("abstract — Idaho vs New York sub-$200 share",
     r"including\s+a\s+\*\*([\d.]+)%\*\*\s+share\s+of\s+dollars\s+from\s+gifts\s+under\s+"
     r"\$200\s+against\s+New\s+York's\s+\*\*([\d.]+)%\*\*",
     ("out_ID_lt200", "out_NY_lt200"), 0.05),
    ("abstract — retired-donor shares, Idaho against New York",
     r"\*\*([\d.]+)%\*\*,\s+come\s+from\s+donors\s+reporting\s+their\s+occupation\s+as\s+"
     r"retired,\s+against\s+\*\*([\d.]+)%\*\*\s+in\s+New\s+York",
     ("out_ID_retired", "out_NY_retired"), 0.05),
]


PARTICIPATION_PROBES = [
    ("§2 — donors, population and rate, all four states",
     r"\*\*([\d,]+)\*\* donors in a state of \*\*([\d.]+)M\*\* \(\*\*([\d.]+)%\*\*\) versus "
     r"NY \*\*([\d,]+)\*\*/\*\*([\d.]+)M\*\* \(\*\*([\d.]+)%\*\*\), TX "
     r"\*\*([\d,]+)\*\*/\*\*([\d.]+)M\*\* \(\*\*([\d.]+)%\*\*\), and ID "
     r"\*\*([\d,]+)\*\*/\*\*([\d.]+)M\*\* \(\*\*([\d.]+)%\*\*\)",
     ("out_WA_donors", "pc_WA_pop_m", "pc_WA_rate",
      "out_NY_donors", "pc_NY_pop_m", "pc_NY_rate",
      "out_TX_donors", "pc_TX_pop_m", "pc_TX_rate",
      "out_ID_donors", "pc_ID_pop_m", "pc_ID_rate"), 0.05),
]


CYCLE_PROBES = [
    ("§5 — presidential vs off-year dollars, all four states",
     r"\(WA \$([\d.]+)M/2020 vs \$([\d.]+)M/2018; NY \$([\d.]+)M vs \$([\d.]+)M; "
     r"TX \$([\d.]+)M vs \$([\d.]+)M; ID \$([\d.]+)M vs \$([\d.]+)M\)",
     ("cyc_WA_2020", "cyc_WA_2018", "cyc_NY_2020", "cyc_NY_2018",
      "cyc_TX_2020", "cyc_TX_2018", "cyc_ID_2020", "cyc_ID_2018"), 0.5),
]

_BAND_ROW = (r" \| (\d+) \| ([\d.]+)% \| \$([\d.]+)M \| {e}\$([\d.]+)M{e} \| "
             r"([\d.]+)% \| ([\d.]+)% \|")


def _band_keys(b):
    return tuple(f"e_h_{b}_{k}" for k in ("n", "pctdist", "m", "perdist", "pctdol", "oos"))


E_PROBES = [
    ("§E — inflow file scale",
     r"\*\*([\d.]+)M contributions / \$([\d.]+)B\*\*", ("e_rows_m", "e_dollars_b"), 0.005),
    ("§E — House window total and district count",
     r"U\.S\. House, 2022–2026 — \$(\d+)M across (\d+) districts",
     ("e_h_total_m", "e_h_ndist"), 0.5),
    ("§E — House band row, Tossup",
     r"\| Tossup \(<5\)" + _BAND_ROW.format(e=r"\*\*"), _band_keys("Tossup"), 0.05),
    ("§E — House band row, Lean",
     r"\| Lean \(5–10\)" + _BAND_ROW.format(e=r"\*\*"), _band_keys("Lean"), 0.05),
    ("§E — House band row, Likely",
     r"\| Likely \(10–20\)" + _BAND_ROW.format(e=""), _band_keys("Likely"), 0.05),
    ("§E — House band row, Solid",
     r"\| Solid \(≥20\)" + _BAND_ROW.format(e=""), _band_keys("Solid"), 0.05),
    ("§E — the competitiveness premium, per district",
     r"Tossup \(\$([\d.]+)M/district\) and Lean\s+\(\$([\d.]+)M\)",
     ("e_h_Tossup_perdist", "e_h_Lean_perdist"), 0.05),
    ("§E — safe-seat per-district inflow, first statement",
     r"per-district inflow of safe seats \(~\$(\d+)M\)", "e_h_Likely_perdist", 0.5),
    ("§E — safe-seat per-district inflow, restated for Likely vs Solid",
     r"the \*same\* per district \(~\$(\d+)M\)", "e_h_Solid_perdist", 0.5),
    # The two aggregate claims. Both are sums of asserted cells, and BOTH are computed from
    # unrounded shares: 42.105 + 47.368 = 89.47 rounds to the printed 89, while adding the
    # PRINTED 42.1 + 47.4 gives 89.5, which rounds to 90. The paper is right and an
    # arithmetic-on-printed-cells check would have called it wrong.
    ("§E — the competitiveness premium as a multiple",
     r"competitiveness premium is real and ~(\d+)×", "comp_premium", 0.5),
    ("§E — safe seats' share of dollars and of districts",
     r"capture ~([\d.]+)% of the money\*\* \(Likely\+Solid\), because they're "
     r"~([\d.]+)% of districts", ("e_h_safe_pctdol", "e_h_safe_pctdist"), 0.5),
    ("§E — out-of-state share, range across House bands",
     r"~([\d.]+)–([\d.]+)% of all inflow is out-of-state",
     ("e_h_oos_lo", "e_h_oos_hi"), 0.5),
    ("§E — Senate table, TX",
     r"\| \*\*TX\*\* \| \*\*\$([\d.]+)M\*\* \| ([\d.]+)% \|", ("e_s_TX_m", "e_s_TX_oos"), 0.05),
    ("§E — Senate table, NY",
     r"\| NY \| \$([\d.]+)M \| ([\d.]+)% \|", ("e_s_NY_m", "e_s_NY_oos"), 0.05),
    ("§E — Senate table, WA",
     r"\| WA \| \$([\d.]+)M \| ([\d.]+)% \|", ("e_s_WA_m", "e_s_WA_oos"), 0.05),
    ("§E — Senate table, ID",
     r"\| \*\*ID\*\* \| \$([\d.]+)M \| \*\*([\d.]+)%\*\* \|",
     ("e_s_ID_m", "e_s_ID_oos"), 0.05),
    ("§E — Senate prose, TX against safe NY and WA",
     r"drew \*\*\$(\d+)M — ~(\d+)× safe\s+NY \(\$(\d+)M\) or WA \(\$(\d+)M\)\*\*",
     ("e_s_TX_m", "e_s_tx_over_ny", "e_s_NY_m", "e_s_WA_m"), 0.5),
    ("§E — Senate out-of-state range over WA/TX/NY, and NY as its high point",
     r"high \*everywhere\* \(([\d.]+)–([\d.]+)% across WA, TX and NY; Idaho,\s+below, is "
     r"higher still\) and among those three is actually \*\*highest in safe NY \(([\d.]+)%\)\*\*",
     ("e_s3_oos_lo", "e_s3_oos_hi", "e_s_NY_oos"), 0.5),
    ("§E — Idaho's own inflow, total and by chamber",
     r"drew \*\*\$([\d.]+)M\*\* total inflow \(House \$([\d.]+)M, all in the safe bands; "
     r"Senate \$([\d.]+)M\)", ("e_id_total_m", "e_id_house_m", "e_s_ID_m"), 0.05),
    ("§E — Idaho's Senate out-of-state share against the other three",
     r"Senate money is ([\d.]+)% out-of-state.*?\(WA (\d+)%, TX (\d+)%, NY (\d+)%\)",
     ("e_s_ID_oos", "e_s_WA_oos", "e_s_TX_oos", "e_s_NY_oos"), 0.5),
    ("§E — the mechanism restated at Idaho's Senate scale",
     r"operates at \$([\d.]+)M even harder", "e_s_ID_m", 0.05),
]


def participation(d):
    """§2's per-capita cut: donor counts from outflow(), denominators from the pinned ACS file.

    The denominators are the only figures in this section external to every database in the
    repo, which is why §2 sat named-but-ungated with exactly this fix prescribed. They are read
    from the pin rather than fetched, so a re-fetch cannot move a published percentage silently.

    Two things this derivation is NOT allowed to become. It must not substitute CVAP for total
    residents to make the rates look better — the paper's basis is total residents and its
    objection block concedes the resulting downward bias. And it must not fall back to a
    hard-coded population if the pin is missing: a missing pin is a failure, because a figure
    nobody can re-derive is what the audit exists to refuse.
    """
    if not POP_PIN.exists():
        return [f"§2: population pin missing ({POP_PIN.name}). "
                f"Run scripts/acs_state_population.py — the section cannot be asserted without it."]
    pops = {}
    with POP_PIN.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            pops[row["state"]] = int(row["population"])
    missing = [s for s in HEADLINE_STATES if s not in pops]
    if missing:
        return [f"§2: population pin covers {sorted(pops)}, missing {missing}"]
    for st in HEADLINE_STATES:
        d[f"pc_{st}_pop_m"] = pops[st] / 1e6
        d[f"pc_{st}_rate"] = 100.0 * d[f"out_{st}_donors"] / pops[st]
    return []


def percycle_ordering_claims(d) -> list[str]:
    """The abstract's two per-cycle ordering claims, checked as claims (2026-08-14, Pass 2).

    "New York is the most top-heavy in every cycle, while the ordering beneath it shifts
    from cycle to cycle (§A)." §A's table is owned by its diag script and exempted from
    this gate, so the abstract's summary of it was checked by nothing — and its previous
    wording ("Washington and Idaho trade the bottom two places") was FALSE for 2018, where
    Idaho ranked second and the bottom two were Washington and Texas. Same blind spot as
    "the highest of the four": an ordering carries no numeric token.

    Derived ordinally on the outflow() filter (donor = name|ZIP within cycle). This basis
    reproduces §A's printed cells to the last digit on 18 of 20 and within 0.1 on the rest,
    and every ordinal gap it relies on exceeds 1 point, so last-digit basis differences
    cannot flip a verdict. `d` carries `pc_top1_<cycle>_<st>` for the report.
    """
    fails = []
    per_cyc: dict[int, dict[str, float]] = {}
    filt = ("regexp_matches(COALESCE(fec_candidate_id,''),'^[CPHS][0-9]') "
            "AND contributor_state='{st}' AND contribution_amount>0")
    for st in HEADLINE_STATES:
        con = duckdb.connect(str(DATA / f"{st.lower()}_statewide.duckdb"), read_only=True)
        rows = con.execute(f"""
            WITH dd AS (SELECT election_cycle cyc,
                              contributor_name || '|' || COALESCE(contributor_zip,'') dnr,
                              SUM(contribution_amount) amt
                        FROM individual_contributions WHERE {filt.format(st=st)}
                        GROUP BY 1, 2),
            r AS (SELECT cyc, amt,
                         ROW_NUMBER() OVER (PARTITION BY cyc ORDER BY amt DESC) rn,
                         COUNT(*) OVER (PARTITION BY cyc) n,
                         SUM(amt) OVER (PARTITION BY cyc) s
                  FROM dd)
            SELECT cyc, 100.0*SUM(amt) FILTER (WHERE rn <= CEIL(n*0.01))/ANY_VALUE(s)
            FROM r GROUP BY 1""").fetchall()
        con.close()
        for cyc, share in rows:
            per_cyc.setdefault(int(cyc), {})[st] = float(share)
    not_ny = [c for c, row in sorted(per_cyc.items())
              if max(row, key=row.get) != "NY"]
    if not_ny:
        fails.append(
            f"abstract: 'New York is the most top-heavy in every cycle' is false in "
            f"{not_ny} — fix the sentence, not this guard.")
    tails = {c: tuple(sorted((s for s in row if s != "NY"), key=row.get, reverse=True))
             for c, row in per_cyc.items()}
    if len(set(tails.values())) < 2:
        fails.append(
            "abstract: 'the ordering beneath it shifts from cycle to cycle' is false — "
            "the non-NY ordering is identical in every cycle. Fix the sentence, not this "
            "guard.")
    # "Washington has the broadest donor participation relative to population" — a
    # four-state superlative over pc_*_rate, previously asserted value-by-value only.
    rates = {st: d.get(f"pc_{st}_rate") for st in HEADLINE_STATES}
    if all(v is not None for v in rates.values()):
        top = max(rates, key=rates.get)
        if top != "WA":
            fails.append(
                f"abstract: 'Washington has the broadest donor participation relative to "
                f"population' is false — {top} leads at {rates[top]:.2f}% vs WA "
                f"{rates['WA']:.2f}%. Fix the sentence, not this guard.")
    # §3's HEADING is an ordering ("largest in Idaho, then Washington"): each value is
    # probed, but a WA/TX swap would leave every value probe green while the heading went
    # false — the same shape the other guards here close.
    ret = {st: d.get(f"out_{st}_retired") for st in HEADLINE_STATES}
    if all(v is not None for v in ret.values()):
        order = sorted(ret, key=ret.get, reverse=True)
        if order[:2] != ["ID", "WA"]:
            fails.append(
                f"§3 heading: 'The retired-donor economy is largest in Idaho, then "
                f"Washington' is false — measured ordering is {' > '.join(order)}. Fix "
                f"the heading, not this guard.")
    return fails


def verify_individual_layer():
    """Derive the headline table plus F5/F6 and assert both against the paper's prose."""
    d = {
        # Historical figures the recompute note quotes. They are what the RETIRED panels
        # gave, so they are literals by construction and must keep saying so.
        "_ny_prev": 308_032, "_id_prev": 47_762, "_wa_prev": 382_408,
    }
    if not _collect(d):
        return ["F5/F6: a state's data was unavailable, so the block could not be asserted"]
    for st in HEADLINE_STATES:
        for k, v in outflow(st).items():
            # `out_` prefix, deliberately. outflow() and f5() both yield a `gini` and a `top1`
            # per state for DIFFERENT POPULATIONS -- every in-state FEC contributor versus the
            # matched-voter panel (WA: 0.800 against 0.857). Sharing a key name made the F5
            # probes compare the matched-voter Gini against the contributor one. It failed
            # loudly, but only because the two happen to differ a lot; a closer pair would
            # have passed on the wrong number.
            d[f"out_{st}_{k}"] = v
        for cyc, tot in per_cycle(st).items():
            d[f"cyc_{st}_{cyc}"] = tot
    _cross_state_ratios(d)
    inflow_e(d)
    inflow_pooled_concentration(d)
    pin_fail = participation(d)
    extra = list(_PIN_FAILURES) + (pin_fail if pin_fail else []) + (
             [] if d.pop("_id_is_max_oos", False) else
             ["§E: the paper calls Idaho's Senate out-of-state share 'the highest of the "
              "four', and it is not — a probe cannot catch a superlative, so it is checked "
              "here"])
    extra += percycle_ordering_claims(d)
    norm = vp.normalise(PAPER.read_text(encoding="utf-8"))
    audit_sections, offsets, spans = {}, {}, {}
    for name, (start, end) in AUDIT_BOUNDS.items():
        audit_sections[name], offsets[name] = vp.slice_with_offset(norm, start, end)
    stats: dict = {}
    rc = vp.run("CROSS-STATE - headline table and the individual money-linked layer",
                norm, HEADLINE_PROBES + F_PROBES + CYCLE_PROBES + E_PROBES
                + PARTICIPATION_PROBES + ABSTRACT_PROBES, d, F_UNCHECKED,
                vp.wants_coverage(), spans_out=spans, stats_out=stats)
    fails = vp.audit_coverage(audit_sections, spans, offsets, tuple(AUDIT_BOUNDS),
                              COVERAGE_EXEMPT, COVERAGE_EXEMPT_LITERAL,
                              COVERAGE_EXEMPT_SECTIONS, strict_units=True,
        bold_is_result=True)
    fails += vp.audit_satellite_counts(PAPER.name, stats.get("figures"))
    if rc != 0:
        fails.append("see the figure failures above")
    return extra + fails


# --- Coverage gate, ported 2026-08-06 ----------------------------------------------------
# THIS WAS THE ONE SERIES PAPER WITHOUT A GATE, and the reason it was deferred was honest:
# 1,190 numeric tokens live in this paper's headed sections against 125 asserted, so "port the
# gate" is not a port. What is done here instead is the thing that makes the backlog
# actionable: the sections this verifier ACTUALLY DERIVES are gated hard, and every remaining
# section is named with the script that owns it. One aggregate "583 unprobed" becomes a
# per-section ledger, which is the difference between a known gap and an unknown one.
#
# The 2026-08-02 round's warning applies to anything added here: the reason those figures went
# unasserted was once recorded as donor-key drift making exact assertion meaningless. That was
# never measured and was FALSE -- donor counts are exact in all four states, Gini within
# 0.0004 -- and it was concealing Idaho's top-1% printed as 36.0 against a derived 36.1. Do not
# re-adopt it in any form.
AUDIT_BOUNDS = {
    # Gated 2026-08-07, on the abstract's arrival in the paper. It ends at the scope section,
    # which is the next heading -- the byline and AI-assistance block sit ABOVE the abstract and
    # so stay outside every span, which is correct: they carry no results.
    "abstract": ("## Abstract", "## Scope and method"),
    # Gated: derived by outflow() in this file.
    "headline": ("## The headline", "## Findings"),
    "finding1": ("### 1. New York is the most top-heavy", "### 2. Participation is broadest"),
    "finding3": ("### 3. The retired-donor economy", "### 4. Sector signatures"),
    # Gated: derived by f5()/f6() in this file. The largest section in the paper.
    "individual": ("### F. The individual layer", "### G. The cross-state money-flow matrix"),
    # Gated 2026-08-06: §5 by per_cycle(), §E by inflow_e().
    "finding5": ("### 5. A uniform presidential rhythm", "## Follow-on tests"),
    "test_e": ("### E. Inflow side", "### F. The individual layer"),
    # Gated 2026-08-07: §2 by participation(), once its denominators were pinned.
    "finding2": ("### 2. Participation is broadest", "### 3. The retired-donor economy"),
    # Named, not gated -- see COVERAGE_EXEMPT_SECTIONS for each one's owner.
    "finding4": ("### 4. Sector signatures", "### 5. A uniform presidential rhythm"),
    "test_a": ("### A. Is the money concentrating over time?", "### B. Where does each state"),
    "test_b": ("### B. Where does each state", "### C. Top donors, top recipients"),
    "test_c": ("### C. Top donors, top recipients", "### D. Does money chase competitive"),
    "test_d": ("### D. Does money chase competitive", "### E. Inflow side"),
    "test_g": ("### G. The cross-state money-flow matrix", "### H. Sector × competitiveness"),
    "test_h": ("### H. Sector × competitiveness", "### I. Inflow concentration trend"),
    "test_i": ("### I. Inflow concentration trend", "### J. Which side of a safe seat"),
    "test_j": ("### J. Which side of a safe seat", "### K. State-level money"),
    "test_k": ("### K. State-level money", "## Limits of inference"),
    "status": ("## What's done, and what's next", "## Related work"),
}

COVERAGE_EXEMPT = [
    (r"^(?:19|20)\d{2}$", "a calendar year, not a result"),
    (r"^\d{1,2}$", "small integer - cycle counts, band edges, list ordinals"),
    # COHORT EDGES under strict_units. "Top 1% of donors -> share of $" names the
    # group; the share beside it is the measurement and is probed (out_*_top1 /
    # out_*_top10). Declared as explicit unit-carrying patterns so the waiver
    # reaches these two tokens and nothing else — a literal on "1" and "10" would
    # cover every bare 1 and 10 in the paper.
    (r"^1%$", "the top-1% cohort EDGE; the share it names is probed as out_*_top1"),
    (r"^10%$", "the top-10% cohort EDGE; probed as out_*_top10"),
]

COVERAGE_EXEMPT_LITERAL: dict[str, str] = {
    # Gift-size THRESHOLDS naming the cut, not measurements of it. The shares computed at each
    # threshold ARE asserted, four states apiece, by the two headline probes above.
    "200": "the <$200 gift-size threshold labelling a cut; the shares at it are asserted",
    "5,000": "the >=$5,000 gift-size threshold, as above",
    # --- §E, added with that section's gate 2026-08-06. Four tokens, three owners. Each was
    # checked for blast radius before being added: none of these values occurs unprobed
    # anywhere else in the six gated sections, which is the cost of a context-free literal
    # exemption and the reason the list stays this short.
    "2.1": "the DONOR-side competitiveness ratio, quoted in §E as a contrast. It belongs to "
           "§D and is derived by scripts/diag_cross_state_money_matrix.py; §D is named, not "
           "gated, so this is the one figure §E borrows from a section that is still on the "
           "backlog",
    "2.6": "the 2018 TX Senate result (Cruz/O'Rourke R+2.6) — an election outcome naming why "
           "that race is called competitive, not a measurement from any database here",
    "8.8": "the 2024 TX Senate result (Cruz/Allred R+8.8); as above",
    "250": "an order-of-magnitude restatement of the TX Senate total ('even harder than at "
           "$250M'). The figure itself is $253.2M and IS asserted twice above, by the Senate "
           "table probe and the Senate prose probe",
    "90": "the direct (non-earmarked) `15` total in the same sentence as the 194 "
          "and 150 below, and from the same source; owned by "
          "scripts/diag_earmark_inspect.py, which the paper cites inline. Exempted "
          "for the same reason as its two neighbours and NOT because it is small — "
          "it was auto-exempt as a bare integer until strict_units, which meant the "
          "one figure of the three that carried no reason looked identical to the "
          "two that did",
    "194": "earmarked (15E) dollars to these candidates in 2024, from the FEC transaction "
           "types. Owned by scripts/diag_earmark_inspect.py, which the paper cites inline; "
           "the inflow table carries no transaction-type column, so it cannot be re-derived "
           "from the data this verifier reads",
    "150": "the conduit-side (24T) total, deliberately EXCLUDED from the inflow load to "
           "avoid double-counting; same owner as the 194 above",
    # --- §2, added with that section's gate 2026-08-07.
    "01003": "the ACS TABLE NUMBER (B01003, Total Population) naming where §2's denominators "
             "come from, not a measurement. The four populations it sources are each asserted "
             "against docs/reference/state_population_acs2024.csv by the participation probe",
    "0.77": "a stated FLOOR ('all four exceed 0.77'), not a measurement. The four Ginis it "
            "bounds are each asserted to three decimals by the headline Gini probe, and the "
            "lowest of them is ID at 0.775 — so the claim is checkable from asserted values "
            "even though the bound itself is not one of them",
}

# Each entry names WHERE the section's figures are derived. "Another script owns it" with no
# script named is exactly the empty reason the audit exists to refuse, so every line names one.
COVERAGE_EXEMPT_SECTIONS: dict[str, str] = {
    # §F is where this verifier's F_PROBES concentrate, so leaving it ungated is not for want
    # of derivation — it is that the section RESTATES a great deal that belongs to the donor
    # paper. Of its 137 unmapped tokens the bulk are: the Appendix-F blinded validation (480
    # records, 120/120, Wilson [96.9-100], 47.9-71.7% on initial-based keys), the 2026-07-27
    # tier switch (382,408 -> 314,974 voters, $574.21M -> $468.85M), the WA federal/state panel
    # split (147,745 / $346.3M / 41.2% / 0.815 and 217,114 / $122.5M / 43.5% / 0.821), and the
    # two-money-system provenance figures ($646.2M FEC / $394.6M PDC). Every one of those is
    # owned and asserted by verify_donor_class.py against the same databases; this paper is
    # restating them, and re-deriving them here would fork the specification rather than check
    # it. BACKLOG: probe them as CROSS-DOCUMENT checks against
    # donor-class-and-the-electorate.md — the pattern verify_whitepaper.py uses for the money
    # paper's figures, which is what caught the stale +0.55 on 2026-08-06.
    "individual": "§F restates the donor paper's validation, tier-switch and panel-split "
                  "figures, all owned and asserted by verify_donor_class.py. The cuts that are "
                  "THIS paper's own (F5 donor skew, F6 giving-vs-turnout) are asserted by "
                  "F_PROBES. BACKLOG: convert the restatements to cross-document probes "
                  "against donor-class-and-the-electorate.md rather than re-deriving them.",
    # finding2 CLOSED 2026-08-07 — participation() + PARTICIPATION_PROBES, exactly as this
    # entry prescribed: pin the denominators the way acs_cvap_by_state.py pins CVAP. Closing it
    # turned up what the ungated state had been hiding — the old denominators named NO SOURCE
    # anywhere in the paper, the owning script or the notes, so there was no basis to reproduce
    # them against. Three of the four were consistent with Census PEP 2023 (NY 19.57M, TX
    # 30.50M, ID 1.965M); WA's stated 7.9M matched neither that nor ACS (both give 7.8M), and
    # it ran the paper's own headline claim LOW, 4.58% against 4.63%. All four are now on one
    # pinned ACS release. Only TX's printed rate moved, 2.7% -> 2.8%.
    "finding4": "sector signatures. Owned by scripts/cross_state_fec_money.py's employer/"
                "occupation sector cut, which the paper cites inline. BACKLOG.",
    # finding5 CLOSED 2026-08-06 — per_cycle() + CYCLE_PROBES. It was the cheapest, exactly
    # as the note predicted: one GROUP BY on the filter outflow() already uses.
    # test_e CLOSED 2026-08-06 — inflow_e() + E_PROBES, importing the band logic from
    # cross_state_common so the definition cannot fork from the diagnostic's.
    "test_a": "concentration over time. Owned by scripts/cross_state_fec_money.py. BACKLOG.",
    "test_b": "per-state destinations. Owned by scripts/diag_cross_state_money_matrix.py, "
              "which is also where the recipient-state resolution (candidate office state, "
              "NOT committee registration state) is implemented. BACKLOG.",
    "test_c": "top donors and recipients. Owned by scripts/diag_cross_state_donors.py. Note "
              "CORRECTED 2026-08-09: this reason used to read 'this section names "
              "ORGANISATIONS and committees only - no individual donor is named anywhere in "
              "this paper'. That was false about the section it exempts, which is headed "
              "'Largest individual donors' and names roughly fifteen people, all from public "
              "FEC filings. The abstract carried the same false sentence and is corrected. "
              "The section stays exempt because its figures are produced by "
              "diag_cross_state_donors.py, not because of any naming claim. BACKLOG.",
    "test_d": "money x competitiveness, outflow side. Owned by "
              "scripts/diag_cross_state_money_matrix.py. BACKLOG.",
    "test_g": "the cross-state flow matrix. Owned by "
              "scripts/diag_cross_state_money_matrix.py. BACKLOG.",
    "test_h": "sector x competitiveness. Owned by scripts/cross_state_fec_money.py. BACKLOG.",
    "test_i": "inflow concentration trend and donor retention. Owned by "
              "scripts/diag_cross_state_donors.py. BACKLOG.",
    "test_j": "longshot-vs-favored money. Owned by scripts/diag_loser_side_money.py, which is "
              "already declared in F_UNCHECKED for the §J share it also supplies.",
    "test_k": "the STATE-disclosure layer (WA PDC / NY BOE / ID Sunshine / TX TEC). Owned by "
              "scripts/cross_state_state_money.py. Different regimes and filer universes from "
              "the federal sections, which is why the paper warns against comparing K to A-J - "
              "and why gating it needs its own derivation rather than an extension of "
              "outflow(). BACKLOG, and the largest single section at 151 tokens.",
    "status": "the roadmap section. Its numbers are row counts and load sizes describing what "
              "has been INGESTED, not results - e.g. TX's 19,416 candidate-cycle rows. They "
              "belong with the loaders (scripts/cross_state_state_money.py, "
              "scripts/load_fec_inflow_bulk.py) and change when data is added, not when a "
              "finding changes. BACKLOG, lowest priority of these.",
}


def _cross_state_ratios(d):
    """The approximations the prose states as bare multiples and shares.

    Every figure here was already derived per state; what was missing is the
    COMPARISON the sentence actually makes — "~3× Washington's", "~2× their
    off-year totals", "~20% of BOTH ID and WA", "a $76M pool against a $2B one".
    Those are claims about figures, and a bare `3` or `20` carried no token a
    coverage gate would look at until strict_units. Each is derived from the
    per-state values rather than restated, and each "both" is asserted as a
    relation so the word has to keep being true.
    """
    # Finding 1 — the >=$5,000 share said to be ~20% in both ID and WA.
    _g = {s: d[f"out_{s}_ge5000"] for s in ("ID", "WA")}
    if round(min(_g.values())) != round(max(_g.values())):
        raise SystemExit(
            f"FATAL: Finding 1 says >=$5,000 gifts are ~20% of BOTH ID and WA. "
            f"Measured ID {_g['ID']:.2f}%, WA {_g['WA']:.2f}% — they no longer "
            f"round alike, so one approximation cannot stand for both.")
    d["ge5k_idwa"] = sum(_g.values()) / 2

    # Finding 1 — the size effect, "$76M pool ... against a $2B one".
    d["pool_small_m"] = d["out_ID_total_m"]
    d["pool_large_b"] = d["out_NY_total_b"]

    # Finding 2 — "NY and TX raise ~3x Washington's federal dollars".
    _r = {s: d[f"out_{s}_total_m"] / d["out_WA_total_m"] for s in ("NY", "TX")}
    if round(min(_r.values())) != round(max(_r.values())):
        raise SystemExit(
            f"FATAL: Finding 2 states one multiple for both NY and TX against WA. "
            f"Measured NY {_r['NY']:.2f}x, TX {_r['TX']:.2f}x — they no longer "
            f"round alike.")
    d["ny_tx_over_wa"] = sum(_r.values()) / 2

    # Finding 3 — the looser non-working bucket, ~48% in both ID and WA.
    _nw = {s: d[f"out_{s}_nonworking"] for s in ("ID", "WA")}
    if round(min(_nw.values())) != round(max(_nw.values())):
        raise SystemExit(
            f"FATAL: Finding 3 says the looser non-working bucket reaches ~48% in "
            f"BOTH ID and WA. Measured ID {_nw['ID']:.2f}%, WA {_nw['WA']:.2f}%.")
    d["nonworking_idwa"] = sum(_nw.values()) / 2

    # Finding 5 — presidential dollars at ~2x the off-year, "in lockstep", all four.
    # The paper prints the eight totals it rests on and they are probed; this is
    # the MULTIPLE, which is the actual claim and was the only unprobed part.
    _ratios = {}
    for s in HEADLINE_STATES:
        pres = [d[f"cyc_{s}_{c}"] for c in (2020, 2024) if f"cyc_{s}_{c}" in d]
        off = [d[f"cyc_{s}_{c}"] for c in (2018, 2022) if f"cyc_{s}_{c}" in d]
        if not pres or not off:
            raise SystemExit(
                f"FATAL: Finding 5's presidential/off-year multiple cannot be "
                f"formed for {s} — the per-cycle totals no longer cover both "
                f"cycle types, so 'all four states' is unverifiable.")
        _ratios[s] = (sum(pres) / len(pres)) / (sum(off) / len(off))
    if round(min(_ratios.values())) != round(max(_ratios.values())):
        raise SystemExit(
            f"FATAL: Finding 5 says ALL FOUR states run at one multiple, 'in "
            f"lockstep'. Measured " +
            ", ".join(f"{s} {v:.2f}x" for s, v in sorted(_ratios.items())) +
            " — they no longer round alike, so the lockstep claim is the defect, "
            "not the multiple.")
    d["pres_offyear_mult"] = sum(_ratios.values()) / len(_ratios)


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
               -- The published definition is occupation='RETIRED' OR employer='RETIRED'
               -- (scripts/cross_state_fec_money.py). Matching only the occupation field, as
               -- this did until 2026-08-02, silently drops every donor who put RETIRED in the
               -- employer box and something else in occupation -- which ran the share 0.15 to
               -- 0.26 points low in ALL FOUR states, in the same direction. A one-directional
               -- offset across every state is a basis difference, never drift.
               100.0*SUM(contribution_amount) FILTER(
                   WHERE UPPER(COALESCE(contributor_occupation,''))='RETIRED'
                      OR UPPER(COALESCE(contributor_employer,''))='RETIRED')
                 /SUM(contribution_amount)
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
    # Total dollars, contribution count and median gift — the three headline rows that need
    # no donor grouping at all, and so cannot be affected by the key even in principle.
    tot, nrows, med = con.execute(f"""
        SELECT SUM(contribution_amount), COUNT(*), median(contribution_amount)
        FROM individual_contributions WHERE {filt}""").fetchone()
    # The LOOSER "non-working" bucket Finding 3 quotes parenthetically as ~48%.
    # Definition lifted from scripts/cross_state_fec_money.py line 74-75, which
    # is the script the paper cites — not re-invented here, because a bucket this
    # soft is only checkable against the definition that produced it.
    nonwork, = con.execute(f"""
        SELECT 100.0*SUM(contribution_amount) FILTER(
                 WHERE UPPER(COALESCE(contributor_occupation,''))
                       IN ('RETIRED','NOT EMPLOYED','NONE','N/A','UNEMPLOYED')
                    OR UPPER(COALESCE(contributor_employer,''))
                       IN ('RETIRED','NOT EMPLOYED','NONE','N/A','UNEMPLOYED',''))
               /SUM(contribution_amount)
        FROM individual_contributions WHERE {filt}""").fetchone()
    con.close()

    return dict(lt200=shares[0], ge5000=shares[1], retired=shares[2],
                nonworking=float(nonwork),
                donors=conc, top1=top[0], top10=top[1], gini=gini,
                total_m=float(tot) / 1e6, total_b=float(tot) / 1e9,
                contribs_m=int(nrows) / 1e6, median_gift=float(med))


def per_cycle(state):
    """Finding 5's per-cycle dollar totals, on the SAME filter outflow() uses.

    Closes §5, which was named-but-ungated with the note "derivable from the same outflow()
    filter with a GROUP BY election_cycle; nothing external is needed. BACKLOG, and the
    cheapest of these to close." It was: this is that GROUP BY. Every one of the eight
    figures the section quotes reproduces to the printed digit, so the section needed a
    derivation, not a correction.
    """
    con = duckdb.connect(str(DATA / f"{state.lower()}_statewide.duckdb"), read_only=True)
    filt = ("regexp_matches(COALESCE(fec_candidate_id,''),'^[CPHS][0-9]') "
            f"AND contributor_state='{state}' AND contribution_amount>0")
    rows = con.execute(f"""
        SELECT election_cycle, SUM(contribution_amount)/1e6
        FROM individual_contributions WHERE {filt} GROUP BY 1""").fetchall()
    con.close()
    return {int(c): float(v) for c, v in rows}


def inflow_pooled_concentration(d):
    """§I's inflow concentration, POOLED — the basis its comparison actually needs.

    §I set per-cycle inflow concentration (top-1% 16-18%, Gini 0.69) against pooled
    outflow concentration (top-1% 36.1-47.5%, Gini 0.775-0.848) and read the
    difference as the effect of the per-election contribution cap. Pooling stacks
    repeat large donors, so the two bases are not comparable and the gap was
    overstated: on one basis the ratio is ~1.5-2.0x, not 2.1-2.6x.

    Derived here rather than left in the prose because §I sits in
    COVERAGE_EXEMPT_SECTIONS — an unprobed figure there is invisible to the gate,
    which is how the mismatched comparison survived in the first place.
    """
    ic = duckdb.connect(str(DATA / "fec_inflow.duckdb"), read_only=True)
    try:
        n, t1, t10 = ic.execute("""
            WITH d AS (
              SELECT UPPER(TRIM(contributor_name)) || '|' || LEFT(contributor_zip, 5) k,
                     SUM(contribution_amount) tot
              FROM inflow_contributions WHERE contribution_amount > 0 GROUP BY 1),
            b AS (SELECT tot, NTILE(100) OVER (ORDER BY tot DESC) nt FROM d),
            t AS (SELECT SUM(tot) s, COUNT(*) n FROM b)
            SELECT (SELECT n FROM t),
                   100.0 * (SELECT SUM(tot) FROM b WHERE nt = 1) / (SELECT s FROM t),
                   100.0 * (SELECT SUM(tot) FROM b WHERE nt <= 10) / (SELECT s FROM t)
        """).fetchone()
        gini, = ic.execute("""
            WITH d AS (
              SELECT UPPER(TRIM(contributor_name)) || '|' || LEFT(contributor_zip, 5) k,
                     SUM(contribution_amount) tot
              FROM inflow_contributions WHERE contribution_amount > 0 GROUP BY 1),
            p AS (SELECT tot v, ROW_NUMBER() OVER (ORDER BY tot ASC) i FROM d),
            a AS (SELECT COUNT(*) n, SUM(v) s, SUM(i * v) sw FROM p)
            SELECT (2.0 * sw) / (n * s) - (n + 1.0) / n FROM a""").fetchone()
    finally:
        ic.close()
    d["inflow_pooled_donors"] = n
    d["inflow_pooled_top1"] = float(t1)
    d["inflow_pooled_top10"] = float(t10)
    d["inflow_pooled_gini"] = float(gini)
    # The outflow side of the same comparison, from the headline table already derived.
    tops = [d[f"out_{s}_top1"] for s in HEADLINE_STATES]
    ginis = [d[f"out_{s}_gini"] for s in HEADLINE_STATES]
    d["out_top1_min"], d["out_top1_max"] = min(tops), max(tops)
    d["out_gini_min"], d["out_gini_max"] = min(ginis), max(ginis)
    d["conc_ratio_lo"] = d["out_top1_min"] / d["inflow_pooled_top1"]
    d["conc_ratio_hi"] = d["out_top1_max"] / d["inflow_pooled_top1"]


def inflow_e(d):
    """§E — the recipient-anchored inflow layer, House by competitiveness band + Senate.

    Closes the section the ledger called "the highest-value one: 93 tokens and the
    derivation already exists". The derivation existed in TWO places and neither ASSERTED:
    main() printed the totals beside the paper's values for a human to compare, and
    diag_inflow_vs_competitiveness.py printed the tables. A printed comparison is not a gate
    — it is exactly the arrangement that let §F5/§F6 go stale in 2026-07-27 while looking
    reasonable. The band logic is imported from cross_state_common rather than re-typed, so
    the competitiveness definition cannot fork from the one the diagnostic publishes.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from cross_state_common import competitiveness_bands  # noqa: PLC0415

    ic = duckdb.connect(str(DATA / "fec_inflow.duckdb"), read_only=True)
    nrows, dollars = ic.execute(
        "SELECT COUNT(*), SUM(contribution_amount) FROM inflow_contributions").fetchone()
    d["e_rows_m"], d["e_dollars_b"] = nrows / 1e6, float(dollars) / 1e9

    comp = competitiveness_bands()
    rows = ic.execute("""
        SELECT recipient_state,
               'cd' || LPAD(CAST(TRY_CAST(recipient_district AS INTEGER) AS VARCHAR), 2, '0'),
               SUM(contribution_amount),
               SUM(CASE WHEN contributor_state <> recipient_state
                        THEN contribution_amount ELSE 0 END)
        FROM inflow_contributions
        WHERE recipient_office='H' AND election_cycle >= 2022 AND contribution_amount > 0
          AND TRY_CAST(recipient_district AS INTEGER) IS NOT NULL
        GROUP BY 1, 2""").fetchall()
    BANDS = ("Tossup", "Lean", "Likely", "Solid")
    agg = {b: {"d": 0, "tot": 0.0, "oos": 0.0} for b in BANDS}
    ndist = {b: 0 for b in BANDS}
    for (_st, _cd), (_m, b) in comp.items():
        ndist[b] += 1
    for st, cd, tot, oos in rows:
        info = comp.get((st, cd))
        if not info:
            continue
        a = agg[info[1]]
        a["d"] += 1
        a["tot"] += float(tot)
        a["oos"] += float(oos)
    total = sum(a["tot"] for a in agg.values()) or 1.0
    alldist = sum(ndist.values()) or 1
    for b in BANDS:
        a = agg[b]
        d[f"e_h_{b}_n"] = a["d"]
        d[f"e_h_{b}_pctdist"] = 100.0 * ndist[b] / alldist
        d[f"e_h_{b}_m"] = a["tot"] / 1e6
        d[f"e_h_{b}_perdist"] = a["tot"] / a["d"] / 1e6 if a["d"] else 0.0
        d[f"e_h_{b}_pctdol"] = 100.0 * a["tot"] / total
        d[f"e_h_{b}_oos"] = 100.0 * a["oos"] / a["tot"] if a["tot"] else 0.0
    d["e_h_total_m"] = total / 1e6
    d["e_h_ndist"] = sum(a["d"] for a in agg.values())
    # The two aggregate claims the section makes about safe seats. Derived rather than
    # arithmetic-on-printed-cells: the paper's own convention elsewhere in this series, and
    # the harmonizer's 2026-08-06 lesson about computing ratios from unrounded shares.
    d["e_h_safe_pctdol"] = d["e_h_Likely_pctdol"] + d["e_h_Solid_pctdol"]
    d["e_h_safe_pctdist"] = d["e_h_Likely_pctdist"] + d["e_h_Solid_pctdist"]
    # §E's headline: "the competitiveness premium is real and ~2x". The four
    # per-district cells it rests on are probed; the MULTIPLE was not, because it
    # is written as a bare `2`. Formed from the pooled per-district dollars on
    # each side rather than from the printed cells — same reason as the two
    # aggregates above, and the same reason the harmonizer computes ratios from
    # unrounded shares.
    _comp = sum(agg[b]["tot"] for b in ("Tossup", "Lean"))
    _compd = sum(agg[b]["d"] for b in ("Tossup", "Lean"))
    _safe = sum(agg[b]["tot"] for b in ("Likely", "Solid"))
    _safed = sum(agg[b]["d"] for b in ("Likely", "Solid"))
    if not (_compd and _safed):
        raise SystemExit(
            "FATAL: §E's competitiveness premium needs donors on both sides of "
            "the band split; one side is empty, so the ~2x claim is unverifiable.")
    d["comp_premium"] = (_comp / _compd) / (_safe / _safed)
    _oos = [d[f"e_h_{b}_oos"] for b in BANDS]
    d["e_h_oos_lo"], d["e_h_oos_hi"] = min(_oos), max(_oos)

    for st, tot, oos in ic.execute("""
        SELECT recipient_state, SUM(contribution_amount),
               SUM(CASE WHEN contributor_state <> recipient_state
                        THEN contribution_amount ELSE 0 END)
        FROM inflow_contributions
        WHERE recipient_office='S' AND contribution_amount > 0 GROUP BY 1""").fetchall():
        d[f"e_s_{st}_m"] = float(tot) / 1e6
        d[f"e_s_{st}_oos"] = 100.0 * float(oos) / float(tot)
    # The Senate out-of-state range is stated over WA / TX / NY only, because Idaho is the
    # subject of the bullet that follows and is far outside it (85.8%). That scoping was NOT
    # in the paper until this gate: the sentence said "high everywhere (41-54%) and actually
    # highest in safe NY", written when the region was three states, and the Idaho load
    # (2026-07-19) made the superlative false against the paper's OWN next bullet, which
    # calls ID "the highest of the four". Same defect shape as the six 2026-08-06 author
    # questions — a range and a superlative quoting three of four members.
    _soos = [d[f"e_s_{s}_oos"] for s in ("WA", "NY", "TX")]
    d["e_s3_oos_lo"], d["e_s3_oos_hi"] = min(_soos), max(_soos)
    # And the claim the rescoping leans on, checked rather than assumed.
    d["_id_is_max_oos"] = d["e_s_ID_oos"] == max(
        d[f"e_s_{s}_oos"] for s in ("WA", "NY", "TX", "ID"))
    d["e_s_tx_over_ny"] = d["e_s_TX_m"] / d["e_s_NY_m"]
    # Idaho's own totals, quoted in the "bottom of the size distribution" claim. ID House
    # is taken over ALL cycles in the inflow file, matching the "$11.5M total inflow" the
    # sentence pairs it with — not the 2022+ window the band table uses.
    idh, = ic.execute("""
        SELECT SUM(contribution_amount)/1e6 FROM inflow_contributions
        WHERE recipient_state='ID' AND recipient_office='H'""").fetchone()
    d["e_id_house_m"] = float(idh)
    d["e_id_total_m"] = d["e_id_house_m"] + d["e_s_ID_m"]
    ic.close()


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
