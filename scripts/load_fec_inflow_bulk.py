"""Recipient-filtered bulk FEC INFLOW loader (NY/TX federal House + Senate).

The contributor-state bulk loader captures OUTFLOW (a state's residents'
giving). This is its INFLOW mirror: download the FEC bulk individual-
contribution files (indiv{yy}.txt) per cycle and keep every itemized
individual contribution whose RECIPIENT committee maps to a NY or TX U.S.
House/Senate candidate (via the FEC committee + candidate masters). Result
= all-state donors -> NY/TX federal candidates, at bulk speed (no API rate
limit; the API allcycles path would take days).

Definitions match load_fec_individual_contributions_bulk exactly
(entity_tp='IND', transaction_tp IN 15/15E/15J/15T/15Z, memo_cd != 'X',
amount > 0). Writes a standalone data/fec_inflow.duckdb (independent of the
per-state DBs, so it won't lock-conflict with a running API load).
Per-cycle idempotent: skips cycles already loaded — safe to re-run/resume.
"""
import csv
import io
import shutil
import os
import zipfile

import duckdb
import httpx

TMP = "data/_fec_bulk"
CYCLES = [2018, 2020, 2022, 2024, 2026]
# Recipient states to load. Default WA/NY/TX (the original cross-state set);
# override via FEC_INFLOW_STATES (comma-separated) to add a state WITHOUT
# re-loading the others — e.g. FEC_INFLOW_STATES=ID for the Idaho add. The
# recipient map is scoped to TARGET, so the INSERT only adds TARGET rows and
# never duplicates states already in the DB.
TARGET = {s.strip().upper() for s in
          (os.environ.get("FEC_INFLOW_STATES") or "WA,NY,TX").split(",") if s.strip()}
INFLOW_DB = "data/fec_inflow.duckdb"
RECIP_CSV = f"{TMP}/recipient_committees.csv"
TX_TYPES = ["15", "15E", "15J", "15T", "15Z"]
COLS = ["cmte_id", "amndt_ind", "rpt_tp", "transaction_pgi", "image_num",
        "transaction_tp", "entity_tp", "name", "city", "state", "zip_code",
        "employer", "occupation", "transaction_dt", "transaction_amt",
        "other_id", "tran_id", "file_num", "memo_cd", "memo_text", "sub_id"]


def _download(url, path):
    with httpx.stream("GET", url, timeout=300.0, follow_redirects=True) as r:
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_bytes(1 << 20):
                f.write(chunk)


def build_recipient_map() -> int:
    """committee_id -> (recipient_state, office, district) for NY/TX H+S cands."""
    os.makedirs(TMP, exist_ok=True)
    cand = {}  # cand_id -> (state, office, district)
    for cy in CYCLES:
        z = f"{TMP}/cn{cy}.zip"
        if not os.path.exists(z):
            _download(f"https://www.fec.gov/files/bulk-downloads/{cy}/cn{cy % 100:02d}.zip", z)
        with zipfile.ZipFile(z) as zf:
            nm = "cn.txt" if "cn.txt" in zf.namelist() else zf.namelist()[0]
            with zf.open(nm) as fh:
                for raw in io.TextIOWrapper(fh, encoding="latin-1"):
                    p = raw.rstrip().split("|")
                    if len(p) >= 7 and p[5] in ("H", "S") and p[4] in TARGET:
                        cand[p[0]] = (p[4], p[5], p[6])
    # Committee master (cm.txt): committee -> connected candidate (field 14).
    # Download per cycle like cn above — earlier versions assumed the cm zips
    # were already staged in TMP, which silently yields 0 recipients on a fresh
    # run (e.g. adding a new state after the temp dir was cleaned).
    rows = []
    for cy in CYCLES:
        z = f"{TMP}/cm{cy}.zip"
        if not os.path.exists(z):
            _download(f"https://www.fec.gov/files/bulk-downloads/{cy}/cm{cy % 100:02d}.zip", z)
        with zipfile.ZipFile(z) as zf:
            nm = "cm.txt" if "cm.txt" in zf.namelist() else zf.namelist()[0]
            with zf.open(nm) as fh:
                for raw in io.TextIOWrapper(fh, encoding="latin-1"):
                    p = raw.rstrip().split("|")
                    if len(p) >= 15 and p[14] in cand:
                        rows.append((p[0], *cand[p[14]]))
    seen, uniq = set(), []
    for r in rows:
        if r[0] not in seen:
            seen.add(r[0]); uniq.append(r)
    with open(RECIP_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["cmte_id", "recipient_state", "recipient_office", "recipient_district"])
        w.writerows(uniq)
    return len(uniq)


def main():
    nrec = build_recipient_map()
    print(f"recipient committees ({'/'.join(sorted(TARGET))} House+Senate): {nrec:,}\n", flush=True)

    conn = duckdb.connect(INFLOW_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS inflow_contributions(
            recipient_state VARCHAR, recipient_office VARCHAR, recipient_district VARCHAR,
            cmte_id VARCHAR, contributor_name VARCHAR, contributor_state VARCHAR,
            contributor_zip VARCHAR, contributor_employer VARCHAR, contributor_occupation VARCHAR,
            contribution_amount DECIMAL(12,2), contribution_date DATE, election_cycle INTEGER)
    """)
    # State-aware skip: only skip a cycle already loaded FOR THE TARGET states,
    # so adding a new state (e.g. ID) loads all its cycles instead of the
    # global check skipping every cycle already present for WA/NY/TX.
    _ph = ", ".join("?" for _ in TARGET)
    done = {r[0] for r in conn.execute(
        f"SELECT DISTINCT election_cycle FROM inflow_contributions "
        f"WHERE recipient_state IN ({_ph})", list(TARGET)).fetchall()}
    coldefs = ", ".join(f"'{c}': 'VARCHAR'" for c in COLS)
    txin = ", ".join(f"'{t}'" for t in TX_TYPES)

    for cy in CYCLES:
        if cy in done:
            print(f"cycle {cy}: already loaded — skip", flush=True)
            continue
        yy = cy % 100
        zip_path, txt_path = f"{TMP}/indiv{cy}.zip", f"{TMP}/itcont{cy}.txt"
        if not os.path.exists(txt_path):
            if not os.path.exists(zip_path):
                print(f"cycle {cy}: downloading indiv{yy:02d}.zip ...", flush=True)
                _download(f"https://www.fec.gov/files/bulk-downloads/{cy}/indiv{yy:02d}.zip", zip_path)
            with zipfile.ZipFile(zip_path) as zf:
                inner = "itcont.txt" if "itcont.txt" in zf.namelist() else zf.namelist()[0]
                # Stream the decompressed file to disk in chunks. Reading it
                # whole via src.read() pulls the entire ~5GB+ file into RAM and
                # OOMs (MemoryError), especially under any concurrent load.
                with zf.open(inner) as src, open(txt_path, "wb") as dst:
                    shutil.copyfileobj(src, dst, 1 << 20)
        print(f"cycle {cy}: filtering -> inflow ...", flush=True)
        conn.execute(f"""
            INSERT INTO inflow_contributions
            SELECT rc.recipient_state, rc.recipient_office, rc.recipient_district,
                   ic.cmte_id, ic.name, ic.state, SUBSTR(ic.zip_code, 1, 5),
                   ic.employer, ic.occupation,
                   TRY_CAST(ic.transaction_amt AS DECIMAL(12,2)),
                   TRY_STRPTIME(ic.transaction_dt, '%m%d%Y')::DATE, {cy}
            FROM read_csv('{txt_path}', delim='|', header=false,
                          columns={{{coldefs}}}, quote='', strict_mode=false) ic
            JOIN read_csv('{RECIP_CSV}', header=true) rc ON ic.cmte_id = rc.cmte_id
            WHERE ic.entity_tp = 'IND'
              AND ic.transaction_tp IN ({txin})
              AND (ic.memo_cd IS NULL OR ic.memo_cd != 'X')
              AND TRY_CAST(ic.transaction_amt AS DECIMAL(12,2)) > 0
        """)
        n = conn.execute(f"SELECT COUNT(*) FROM inflow_contributions WHERE election_cycle={cy}").fetchone()[0]
        print(f"cycle {cy}: +{n:,} inflow rows", flush=True)
        for p in (zip_path, txt_path):
            if os.path.exists(p):
                os.remove(p)

    tot, totM = conn.execute("SELECT COUNT(*), ROUND(SUM(contribution_amount)/1e6,0) FROM inflow_contributions").fetchone()
    byst = conn.execute("SELECT recipient_state, recipient_office, COUNT(*), ROUND(SUM(contribution_amount)/1e6,0) "
                        "FROM inflow_contributions GROUP BY 1,2 ORDER BY 1,2").fetchall()
    conn.close()
    print(f"\n=== INFLOW LOAD COMPLETE: {tot:,} rows, ${totM}M ===", flush=True)
    for rs, ro, n, m in byst:
        print(f"  {rs} {ro}: {n:,} rows  ${m}M", flush=True)


if __name__ == "__main__":
    main()
