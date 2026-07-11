"""Cross-state money-flow MATRIX: donor-state x recipient-state for WA/NY/TX.

Makes the Section-C "Warnock" anecdote systematic. Two complementary matrices:

  INFLOW  (data/fec_inflow.duckdb, recipient-anchored, robust single source):
    for WA/NY/TX U.S. House+Senate candidates, decompose dollars by donor
    ORIGIN — in-state / from the other two in-region states / rest-of-US.
    Answers: how much of each state's candidate money is non-constituent?

  OUTFLOW (per-state individual_contributions + FEC committee master):
    for WA/NY/TX residents' federal CANDIDATE dollars (H/S/P committees),
    classify the RECIPIENT region — in-state / other in-region / rest-of-US.
    Answers: how much does each state's money fund out-of-region races?

  MAGNETS: top out-of-region candidate committees (office state NOT in WA/NY/TX)
    ranked by combined WA+NY+TX resident dollars — the systematic Warnock list.

Recipient state is the CANDIDATE'S OFFICE STATE (cn.txt CAND_OFFICE_ST), resolved
committee->candidate->office-state — NOT the committee's registration state
(CMTE_ST), which is frequently a DC/VA compliance-vendor address (e.g. Smiley-WA
and Cornyn-TX both register in VA). This matches how fec_inflow's recipient_state
was built, so inflow and outflow are apples-to-apples. PAC/party/JFC committees
(no single connected candidate) drop out of the H/S/P candidate cuts by design.
Masters rebuilt from cached cm*.zip + cn*.zip in
data/_fec_bulk (no download)."""
import duckdb
import io
import os
import zipfile
import csv
import json

TMP = "data/_fec_bulk"
CYCLES = [2018, 2020, 2022, 2024, 2026]
CM_NAMED = f"{TMP}/committees_named.csv"
REGION = ("WA", "NY", "TX")
STATES = [("WA", "data/wa_statewide.duckdb"), ("NY", "data/ny_statewide.duckdb"),
          ("TX", "data/tx_statewide.duckdb")]
OUT = "reports/cross_state_matrix.json"


def build_committee_master_named() -> int:
    """cmte_id -> (name, office, office_state) resolved committee->candidate.

    cn.txt: cand_id -> (office, office_state).  cm.txt: cmte_id -> (name, cand_id).
    A committee's recipient state is its connected candidate's OFFICE STATE
    (reliable), not CMTE_ST (registration/treasurer address — unreliable).
    Committees with no connected candidate get office='' / office_st='' and
    fall out of the H/S/P candidate cuts.
    """
    cand: dict[str, tuple[str, str]] = {}   # cand_id -> (office, office_st)
    for cy in CYCLES:
        zpath = f"{TMP}/cn{cy}.zip"
        if not os.path.exists(zpath):
            continue
        with zipfile.ZipFile(zpath) as z:
            name = "cn.txt" if "cn.txt" in z.namelist() else z.namelist()[0]
            with z.open(name) as fh:
                for raw in io.TextIOWrapper(fh, encoding="latin-1"):
                    p = raw.rstrip("\n").split("|")
                    if len(p) < 6:
                        continue
                    cand_id, office_st, office = p[0], p[4], p[5]
                    cand[cand_id] = (office, office_st)
    comm: dict[str, tuple[str, str, str, str]] = {}
    for cy in CYCLES:
        zpath = f"{TMP}/cm{cy}.zip"
        if not os.path.exists(zpath):
            continue
        with zipfile.ZipFile(zpath) as z:
            name = "cm.txt" if "cm.txt" in z.namelist() else z.namelist()[0]
            with z.open(name) as fh:
                for raw in io.TextIOWrapper(fh, encoding="latin-1"):
                    p = raw.rstrip("\n").split("|")
                    if len(p) < 15:
                        continue
                    cmte_id, cmte_nm, dsgn, cand_id = p[0], p[1], p[8], p[14]
                    office, office_st = cand.get(cand_id, ("", ""))
                    comm[cmte_id] = (cmte_nm, office, office_st, dsgn)
    with open(CM_NAMED, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["cmte_id", "cmte_nm", "office", "office_st", "dsgn"])
        for k, (nm, off, ost, dsgn) in comm.items():
            w.writerow([k, nm, off, ost, dsgn])
    return len(comm)


def inflow_matrix():
    c = duckdb.connect("data/fec_inflow.duckdb", read_only=True)
    rows = c.execute("""
        SELECT recipient_state,
               CASE WHEN contributor_state = recipient_state THEN 'in_state'
                    WHEN contributor_state IN ('WA','NY','TX') THEN 'in_region_other'
                    ELSE 'rest_of_us' END origin,
               SUM(contribution_amount) amt
        FROM inflow_contributions
        WHERE recipient_office IN ('H','S') AND contribution_amount > 0
        GROUP BY 1,2
    """).fetchall()
    # also the full 3x(states) breakdown of in-region cross flow
    cross = c.execute("""
        SELECT recipient_state, contributor_state, SUM(contribution_amount) amt
        FROM inflow_contributions
        WHERE recipient_office IN ('H','S') AND contribution_amount > 0
          AND contributor_state IN ('WA','NY','TX')
        GROUP BY 1,2
    """).fetchall()
    c.close()
    mat = {st: {"in_state": 0.0, "in_region_other": 0.0, "rest_of_us": 0.0} for st in REGION}
    for st, origin, amt in rows:
        if st in mat:
            mat[st][origin] += float(amt)
    crossmat = {st: {} for st in REGION}
    for rst, cst, amt in cross:
        crossmat[rst][cst] = float(amt)
    return mat, crossmat


def outflow_matrix():
    """WA/NY/TX residents' H/S/P candidate dollars, classified by recipient region."""
    mat = {st: {"in_state": 0.0, "in_region_other": 0.0, "rest_of_us": 0.0} for st in REGION}
    crossmat = {st: {} for st in REGION}  # donor st -> recipient st (H/S only, in/region)
    for st, path in STATES:
        c = duckdb.connect(path, read_only=True)
        rows = c.execute(f"""
            SELECT m.office_st recip_st, m.office,
                   SUM(ic.contribution_amount) amt
            FROM individual_contributions ic
            JOIN read_csv('{CM_NAMED}', header=true, auto_detect=true) m
              ON ic.fec_candidate_id = m.cmte_id
            WHERE regexp_matches(COALESCE(ic.fec_candidate_id,''),'^C[0-9]')
              AND ic.contributor_state='{st}' AND ic.contribution_amount > 0
              AND m.office IN ('H','S') AND m.dsgn IN ('P','A')
            GROUP BY 1,2
        """).fetchall()
        c.close()
        for recip_st, office, amt in rows:
            amt = float(amt)
            if recip_st == st:
                mat[st]["in_state"] += amt
            elif recip_st in REGION:
                mat[st]["in_region_other"] += amt
            else:
                mat[st]["rest_of_us"] += amt
            if recip_st in REGION:
                crossmat[st][recip_st] = crossmat[st].get(recip_st, 0.0) + amt
    return mat, crossmat


def magnets():
    """Top out-of-region (non-WA/NY/TX) H/S/P committees by combined WA+NY+TX $."""
    agg: dict[str, dict] = {}
    for st, path in STATES:
        c = duckdb.connect(path, read_only=True)
        rows = c.execute(f"""
            SELECT ic.fec_candidate_id cmte, m.cmte_nm, m.office_st, m.office,
                   SUM(ic.contribution_amount) amt
            FROM individual_contributions ic
            JOIN read_csv('{CM_NAMED}', header=true, auto_detect=true) m
              ON ic.fec_candidate_id = m.cmte_id
            WHERE regexp_matches(COALESCE(ic.fec_candidate_id,''),'^C[0-9]')
              AND ic.contributor_state='{st}' AND ic.contribution_amount > 0
              AND m.office IN ('H','S','P') AND m.dsgn IN ('P','A')
              AND m.office_st NOT IN ('WA','NY','TX')
            GROUP BY 1,2,3,4
        """).fetchall()
        c.close()
        for cmte, nm, cst, off, amt in rows:
            d = agg.setdefault(cmte, {"nm": nm, "st": cst, "off": off,
                                      "WA": 0.0, "NY": 0.0, "TX": 0.0})
            d[st] += float(amt)
    for d in agg.values():
        d["total"] = d["WA"] + d["NY"] + d["TX"]
        d["nstates"] = sum(1 for s in REGION if d[s] > 0)
    # focus on candidate committees (H/S) for the cleanest "race" magnets,
    # funded by all 3 states, ranked by combined $
    cand = [d for d in agg.values() if d["off"] in ("H", "S") and d["nstates"] == 3]
    cand.sort(key=lambda d: d["total"], reverse=True)
    allc = sorted(agg.values(), key=lambda d: d["total"], reverse=True)
    return cand[:15], allc[:15]


def pct(d):
    t = sum(d.values()) or 1.0
    return {k: v / t * 100 for k, v in d.items()}


def main():
    n = build_committee_master_named()
    print(f"committee master (named): {n:,} committees\n")

    inflow, inflow_cross = inflow_matrix()
    outflow, outflow_cross = outflow_matrix()

    print("=" * 72)
    print("INFLOW MATRIX — WA/NY/TX U.S. House+Senate candidate money, by donor ORIGIN")
    print("=" * 72)
    print(f"{'recipient':10} {'total $M':>10} {'in-state':>10} {'in-region':>11} {'rest-of-US':>11}")
    for st in REGION:
        p = pct(inflow[st]); t = sum(inflow[st].values())
        print(f"{st:10} {t/1e6:9.1f} {p['in_state']:9.1f}% {p['in_region_other']:10.1f}% {p['rest_of_us']:10.1f}%")
    print("\n  (in-region cross detail — $M from each region state into each recipient state)")
    print(f"  {'recip\\donor':12}" + "".join(f"{s:>10}" for s in REGION))
    for rst in REGION:
        print(f"  {rst:12}" + "".join(f"{inflow_cross[rst].get(s,0)/1e6:9.1f}" for s in REGION))

    print("\n" + "=" * 72)
    print("OUTFLOW MATRIX — WA/NY/TX residents' H+S CANDIDATE money, by recipient REGION")
    print("=" * 72)
    print(f"{'donor':10} {'total $M':>10} {'in-state':>10} {'in-region':>11} {'rest-of-US':>11}")
    for st in REGION:
        p = pct(outflow[st]); t = sum(outflow[st].values())
        print(f"{st:10} {t/1e6:9.1f} {p['in_state']:9.1f}% {p['in_region_other']:10.1f}% {p['rest_of_us']:10.1f}%")
    print("\n  (in-region cross detail — $M from each donor state to each recipient state)")
    print(f"  {'donor\\recip':12}" + "".join(f"{s:>10}" for s in REGION))
    for dst in REGION:
        print(f"  {dst:12}" + "".join(f"{outflow_cross[dst].get(s,0)/1e6:9.1f}" for s in REGION))

    cand, allc = magnets()
    print("\n" + "=" * 72)
    print("SYSTEMATIC MAGNETS — out-of-region H/S candidate committees funded by ALL 3 states")
    print("=" * 72)
    print(f"{'committee':42} {'st':3} {'off':3} {'WA$M':>6} {'NY$M':>6} {'TX$M':>6} {'tot$M':>7}")
    for d in cand:
        print(f"{d['nm'][:42]:42} {d['st']:3} {d['off']:3} "
              f"{d['WA']/1e6:6.2f} {d['NY']/1e6:6.2f} {d['TX']/1e6:6.2f} {d['total']/1e6:7.2f}")

    out = {
        "inflow": {st: {**inflow[st], "pct": pct(inflow[st])} for st in REGION},
        "outflow": {st: {**outflow[st], "pct": pct(outflow[st])} for st in REGION},
        "inflow_cross": inflow_cross, "outflow_cross": outflow_cross,
        "magnets_cand": [{k: d[k] for k in ("nm", "st", "off", "WA", "NY", "TX", "total")} for d in cand],
    }
    json.dump(out, open(OUT, "w"), indent=2, default=str)
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
