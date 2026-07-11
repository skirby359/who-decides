"""In-hand money x competitiveness: does donor money chase competitive races?

Uses data already loaded (no inflow needed): contributions from WA/NY/TX
residents to U.S. HOUSE candidate committees in WA/NY/TX, mapped to the
recipient's district via the FEC committee + candidate masters, then joined
to this project's own competitiveness band (from forecast_predictions'
signed two-party margin: Tossup <5 / Lean 5-10 / Likely 10-20 / Solid >=20).

Scope: post-redistricting cycles only (2022-2026), since the competitiveness
map is on current districts. This is the DONOR-SIDE slice (where these three
states' residents send House money); the full picture needs the inflow load.
"""
import duckdb
import glob
import io
import json
import os
import zipfile

import httpx

TMP = "data/_fec_bulk"
CYCLES = [2018, 2020, 2022, 2024, 2026]
STATES = [("WA", "data/wa_statewide.duckdb"), ("NY", "data/ny_statewide.duckdb"), ("TX", "data/tx_statewide.duckdb")]
TARGET_STATES = {"WA", "NY", "TX"}
DEST_CSV = f"{TMP}/house_committee_dest.csv"


def band(margin_abs: float) -> str:
    if margin_abs < 5: return "Tossup"
    if margin_abs < 10: return "Lean"
    if margin_abs < 20: return "Likely"
    return "Solid"


def build_dest_map():
    """committee_id -> (office_state, cd_id) for U.S. House cands in WA/NY/TX."""
    # cn.txt: cand_id(0), office_st(4), office(5), district(6)
    cand_house = {}  # cand_id -> (state, cdNN)
    for cy in CYCLES:
        z = f"{TMP}/cn{cy}.zip"
        if not os.path.exists(z):
            url = f"https://www.fec.gov/files/bulk-downloads/{cy}/cn{cy % 100:02d}.zip"
            with httpx.stream("GET", url, timeout=120.0, follow_redirects=True) as r:
                r.raise_for_status()
                with open(z, "wb") as f:
                    for chunk in r.iter_bytes(1 << 20):
                        f.write(chunk)
        with zipfile.ZipFile(z) as zf:
            nm = "cn.txt" if "cn.txt" in zf.namelist() else zf.namelist()[0]
            with zf.open(nm) as fh:
                for raw in io.TextIOWrapper(fh, encoding="latin-1"):
                    p = raw.rstrip().split("|")
                    if len(p) < 7:
                        continue
                    cid, ost, office, dist = p[0], p[4], p[5], p[6]
                    if office == "H" and ost in TARGET_STATES and dist.isdigit():
                        cand_house[cid] = (ost, f"cd{int(dist):02d}")
    # cm.txt: cmte_id(0), cand_id(14)
    rows = []
    for z in sorted(glob.glob(f"{TMP}/cm*.zip")):
        with zipfile.ZipFile(z) as zf:
            nm = "cm.txt" if "cm.txt" in zf.namelist() else zf.namelist()[0]
            with zf.open(nm) as fh:
                for raw in io.TextIOWrapper(fh, encoding="latin-1"):
                    p = raw.rstrip().split("|")
                    if len(p) >= 15 and p[14] in cand_house:
                        ost, cd = cand_house[p[14]]
                        rows.append((p[0], ost, cd))
    seen, uniq = set(), []
    for cmte, ost, cd in rows:
        if cmte not in seen:
            seen.add(cmte); uniq.append((cmte, ost, cd))
    import csv
    with open(DEST_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["cmte_id", "dest_state", "dest_cd"])
        w.writerows(uniq)
    return len(uniq)


def competitiveness():
    """(state, cd_id) -> (margin_abs, band) from the latest Democratic forecast row."""
    comp = {}
    for st, f in STATES:
        try:
            c = duckdb.connect(f, read_only=True)
        except Exception:
            print(f"  [competitiveness: {st} DB locked — skipping its districts]")
            continue
        rows = c.execute(
            "WITH r AS (SELECT district_id, predicted_margin, "
            "ROW_NUMBER() OVER (PARTITION BY district_id ORDER BY as_of_date DESC) rn "
            "FROM forecast_predictions WHERE party='Democratic' AND district_id LIKE 'cd%') "
            "SELECT district_id, predicted_margin FROM r WHERE rn=1"
        ).fetchall()
        c.close()
        for cd, m in rows:
            comp[(st, cd)] = (abs(float(m)), band(abs(float(m))))
    return comp


def main():
    n = build_dest_map()
    comp = competitiveness()
    print(f"House committee->district map: {n:,} committees | competitiveness districts: {len(comp)}\n")

    # $ to each destination House district, by donor-state (in-state vs cross-state).
    dest = {}  # (dest_state, dest_cd) -> {"in": $, "out": $}
    donor_states = []
    for st, f in STATES:
        try:
            c = duckdb.connect(f, read_only=True)
        except Exception:
            print(f"  [donor {st} DB locked — excluded from this run]")
            continue
        donor_states.append(st)
        rows = c.execute(
            f"SELECT m.dest_state, m.dest_cd, SUM(ic.contribution_amount) amt "
            f"FROM individual_contributions ic "
            f"JOIN read_csv('{DEST_CSV}', header=true) m ON ic.fec_candidate_id = m.cmte_id "
            f"WHERE contributor_state='{st}' AND contribution_amount>0 AND election_cycle>=2022 "
            f"GROUP BY 1,2"
        ).fetchall()
        c.close()
        for ds, cd, amt in rows:
            d = dest.setdefault((ds, cd), {"in": 0.0, "out": 0.0})
            d["in" if ds == st else "out"] += float(amt)

    # Roll up by competitiveness band.
    bands = {b: {"districts": 0, "dollars": 0.0, "in": 0.0, "out": 0.0} for b in ["Tossup", "Lean", "Likely", "Solid"]}
    district_count = {b: 0 for b in bands}
    for key, (mabs, b) in comp.items():
        district_count[b] += 1
    counted = set()
    for (ds, cd), d in dest.items():
        cinfo = comp.get((ds, cd))
        if not cinfo:
            continue
        b = cinfo[1]
        bands[b]["dollars"] += d["in"] + d["out"]
        bands[b]["in"] += d["in"]
        bands[b]["out"] += d["out"]
        counted.add((ds, cd))
    for (ds, cd) in counted:
        bands[comp[(ds, cd)][1]]["districts"] += 1

    total = sum(b["dollars"] for b in bands.values()) or 1.0
    ndist = sum(district_count.values()) or 1

    print("Band     | #Districts | %ofDists | $M to band | $/district | %of$  | in-state$ | cross$")
    print("-" * 92)
    for b in ["Tossup", "Lean", "Likely", "Solid"]:
        x = bands[b]
        nd = district_count[b]
        perdist = x["dollars"] / nd / 1e6 if nd else 0
        print(f"{b:8} | {nd:>10} | {nd/ndist*100:6.1f}% | {x['dollars']/1e6:9.1f} | "
              f"{perdist:9.2f}M | {x['dollars']/total*100:4.1f}% | {x['in']/1e6:8.1f} | {x['out']/1e6:6.1f}")
    print(f"\nTotal House $ ({'+'.join(donor_states)} residents -> readable-state House, 2022-2026): ${total/1e6:,.0f}M across {len(counted)} districts")
    if len(donor_states) < 3:
        print(f"PARTIAL RUN: donor states {donor_states} (others locked by the live load). Rerun when the load finishes for the full 3-state result.")

    out = "reports/money_competitiveness.json"
    json.dump({"bands": bands, "district_count": district_count, "total": total}, open(out, "w"), indent=2)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
