"""Two follow-on cross-state tests on FEC federal contributions (WA/NY/TX).

Test A — Concentration TREND: per-cycle top-1% / top-10% donor dollar share,
         2018-2026, to see whether each state's money is concentrating.

Test B — Recipient DESTINATION: classify where each state's residents send
         their federal dollars, by joining the FEC committee master
         (cm.txt: committee -> state + candidate id). Buckets:
           In-state Congress / Out-of-state Congress / Presidential /
           PAC-party-other.
         NOTE: this is still donor-residence OUTFLOW (where residents send
         money), now resolved by destination — NOT out-of-state money
         flowing into a state (that needs all-state donors).

Basis matches scripts/cross_state_fec_money.py: FEC committee recipients,
in-state-resident donors, positive amounts.
"""
import duckdb
import io
import os
import zipfile
import json
import csv

import httpx

from cross_state_common import region_states, write_json

TMP = "data/_fec_bulk"
os.makedirs(TMP, exist_ok=True)
CYCLES = [2018, 2020, 2022, 2024, 2026]
COMMITTEES_CSV = f"{TMP}/committees_master.csv"
STATES = region_states()


def build_committee_master() -> int:
    """Download cm{yy}.zip per cycle, union into cmte_id -> (state, office)."""
    committees: dict[str, tuple[str, str]] = {}
    for cy in CYCLES:
        yy = cy % 100
        zpath = f"{TMP}/cm{cy}.zip"
        if not os.path.exists(zpath):
            url = f"https://www.fec.gov/files/bulk-downloads/{cy}/cm{yy:02d}.zip"
            with httpx.stream("GET", url, timeout=120.0, follow_redirects=True) as r:
                r.raise_for_status()
                with open(zpath, "wb") as f:
                    for chunk in r.iter_bytes(1 << 20):
                        f.write(chunk)
        with zipfile.ZipFile(zpath) as z:
            name = "cm.txt" if "cm.txt" in z.namelist() else z.namelist()[0]
            with z.open(name) as fh:
                for raw in io.TextIOWrapper(fh, encoding="latin-1"):
                    p = raw.rstrip("\n").split("|")
                    if len(p) < 15:
                        continue
                    cmte_id, cmte_st, cand_id = p[0], p[6], p[14]
                    office = cand_id[0] if cand_id else ""   # H / S / P or ""
                    # later cycles overwrite earlier (most-recent state wins)
                    committees[cmte_id] = (cmte_st, office)
    with open(COMMITTEES_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["cmte_id", "cmte_st", "office"])
        for k, (stt, off) in committees.items():
            w.writerow([k, stt, off])
    return len(committees)


def run():
    n = build_committee_master()
    print(f"committee master: {n:,} committees\n")

    trend = {}
    dest = {}
    for st, path in STATES:
        c = duckdb.connect(path, read_only=True)
        where = (
            "regexp_matches(COALESCE(fec_candidate_id,''),'^[CPHS][0-9]') "
            f"AND contributor_state='{st}' AND contribution_amount > 0"
        )
        # --- Test A: per-cycle concentration ---
        rows = c.execute(
            "WITH d AS (SELECT election_cycle ec, "
            "UPPER(TRIM(contributor_name)) nm, LEFT(COALESCE(contributor_zip,''),5) z, "
            f"SUM(contribution_amount) tot FROM individual_contributions WHERE {where} "
            "GROUP BY 1,2,3), "
            "ranked AS (SELECT ec, tot, NTILE(100) OVER (PARTITION BY ec ORDER BY tot DESC) p FROM d) "
            "SELECT ec, SUM(tot) FILTER (WHERE p=1)/SUM(tot) top1, "
            "SUM(tot) FILTER (WHERE p<=10)/SUM(tot) top10 FROM ranked GROUP BY 1 ORDER BY 1"
        ).fetchall()
        trend[st] = [(int(ec), round(float(t1), 4), round(float(t10), 4)) for ec, t1, t10 in rows]

        # --- Test B: recipient destination ---
        drows = c.execute(
            f"SELECT CASE "
            f"  WHEN m.office='P' THEN 'Presidential' "
            f"  WHEN m.office IN ('H','S') AND m.cmte_st='{st}' THEN 'In-state Congress' "
            f"  WHEN m.office IN ('H','S') THEN 'Out-of-state Congress' "
            f"  ELSE 'PAC/party/other' END bucket, "
            f"SUM(ic.contribution_amount) amt "
            f"FROM individual_contributions ic "
            f"LEFT JOIN read_csv('{COMMITTEES_CSV}', header=true, auto_detect=true) m "
            f"  ON ic.fec_candidate_id = m.cmte_id "
            f"WHERE {where} GROUP BY 1"
        ).fetchall()
        c.close()
        tot = sum(float(a) for _, a in drows) or 1.0
        dest[st] = {b: round(float(a) / tot, 4) for b, a in drows}

    out = write_json("cross_state_fec_tests.json", {"trend": trend, "dest": dest})
    print(f"wrote {out}\n")

    print("=== TEST A: concentration trend — top 1% donor dollar share by cycle ===")
    print("cycle".ljust(8) + "".join(s.rjust(10) for s, _ in STATES))
    for cy in CYCLES:
        line = str(cy).ljust(8)
        for st, _ in STATES:
            v = next((t1 for ec, t1, _ in trend[st] if ec == cy), None)
            line += (f"{v*100:.1f}%" if v is not None else "-").rjust(10)
        print(line)
    print("\n(top 10% share by cycle)")
    print("cycle".ljust(8) + "".join(s.rjust(10) for s, _ in STATES))
    for cy in CYCLES:
        line = str(cy).ljust(8)
        for st, _ in STATES:
            v = next((t10 for ec, _, t10 in trend[st] if ec == cy), None)
            line += (f"{v*100:.1f}%" if v is not None else "-").rjust(10)
        print(line)

    print("\n=== TEST B: where each state's residents send federal dollars ===")
    buckets = ["In-state Congress", "Out-of-state Congress", "Presidential", "PAC/party/other"]
    print("bucket".ljust(24) + "".join(s.rjust(10) for s, _ in STATES))
    for b in buckets:
        line = b.ljust(24)
        for st, _ in STATES:
            line += f"{dest[st].get(b,0)*100:.1f}%".rjust(10)
        print(line)


if __name__ == "__main__":
    run()
