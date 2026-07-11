"""Backfill recipient-party for NY FEC contributions (bulk FEC Committee Master).

The NY individual_contributions store the recipient COMMITTEE id in
`fec_candidate_id` (e.g. C00211318), but candidate_finance was keyed on
candidate ids — so the matcher's recipient-party join missed ~all rows and
`donation_lean` was unusable. This runs the bulk `load_fec_committee_master`
(downloads cm{yy}.zip per cycle from FEC and inserts committee-id-keyed
candidate_finance rows with party from CMTE_PTY_AFFILIATION) plus the
conduit-PAC overrides, then MEASURES D/R coverage. If candidate-committee
coverage is poor (their CMTE_PTY_AFFILIATION is usually blank — party lives on
the candidate record), it additionally resolves committee -> candidate ->
candidate party via the bulk candidate master (cn{yy}.zip).

Usage:
    STATE=NY python scripts/backfill_ny_committee_party.py
"""
import io
import os
import sys
import zipfile

import duckdb
import httpx

os.environ.setdefault("STATE", "NY")
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "src"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from wa_analyzer.etl.fec import (  # noqa: E402
    load_fec_committee_master,
    seed_committee_party_overrides,
)

NY_STATEWIDE = "data/ny_statewide.duckdb"
TMP = "data/_fec_bulk_ny"  # outside Dropbox
CYCLES = (2018, 2020, 2022, 2024, 2026)


def coverage(con) -> None:
    """Print D/R-resolvable share of individual_contributions."""
    df = con.execute("""
        WITH cf AS (SELECT fec_candidate_id, ANY_VALUE(party) p
                    FROM candidate_finance GROUP BY 1)
        SELECT COALESCE(COALESCE(ov.party, cf.p), 'Unknown') party,
               count(*) n, round(sum(ic.contribution_amount)/1e6, 1) usd_m
        FROM individual_contributions ic
        LEFT JOIN cf ON cf.fec_candidate_id = ic.fec_candidate_id
        LEFT JOIN committee_party_override ov ON ov.fec_candidate_id = ic.fec_candidate_id
        GROUP BY 1 ORDER BY n DESC
    """).df()
    tot = df["n"].sum()
    print(df.to_string(index=False))
    dr = df[df.party.isin(["Democratic", "Republican"])]["n"].sum()
    print(f"  --> D/R-resolved: {dr:,} / {tot:,} = {100.0 * dr / tot:.1f}% of contributions")


def _download(url, path):
    with httpx.stream("GET", url, timeout=180.0, follow_redirects=True) as r:
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_bytes(1 << 20):
                f.write(chunk)


def resolve_via_candidate_master(con) -> None:
    """Map committee -> candidate (cm.txt CAND_ID) -> candidate party (cn.txt
    CAND_PTY_AFFILIATION), and UPDATE candidate_finance rows still 'Unknown'.

    This catches candidate authorized committees, which carry most individual
    money but have a blank committee-level party affiliation.
    """
    os.makedirs(TMP, exist_ok=True)
    cmte_to_cand: dict[str, str] = {}   # cmte_id -> cand_id
    cand_party: dict[str, str] = {}     # cand_id -> Democratic/Republican
    PMAP = {"DEM": "Democratic", "DFL": "Democratic", "D": "Democratic",
            "REP": "Republican", "GOP": "Republican", "R": "Republican"}
    for cy in CYCLES:
        yy = cy % 100
        cm = f"{TMP}/cm{cy}.zip"
        cn = f"{TMP}/cn{cy}.zip"
        if not os.path.exists(cm):
            _download(f"https://www.fec.gov/files/bulk-downloads/{cy}/cm{yy:02d}.zip", cm)
        if not os.path.exists(cn):
            _download(f"https://www.fec.gov/files/bulk-downloads/{cy}/cn{yy:02d}.zip", cn)
        with zipfile.ZipFile(cm) as zf:
            nm = next(n for n in zf.namelist() if n.lower().endswith(".txt"))
            with zf.open(nm) as fh:
                for raw in io.TextIOWrapper(fh, encoding="latin-1"):
                    p = raw.rstrip("\n").split("|")
                    if len(p) >= 15 and p[0] and p[14]:  # cmte_id, cand_id
                        cmte_to_cand.setdefault(p[0], p[14])
        with zipfile.ZipFile(cn) as zf:
            nm = next(n for n in zf.namelist() if n.lower().endswith(".txt"))
            with zf.open(nm) as fh:
                for raw in io.TextIOWrapper(fh, encoding="latin-1"):
                    p = raw.rstrip("\n").split("|")
                    if len(p) >= 3 and p[0]:  # cand_id, cand_name, cand_pty
                        party = PMAP.get(p[2].strip().upper())
                        if party:
                            cand_party.setdefault(p[0], party)

    # cmte_id -> party (via its candidate)
    rows = [(c, cand_party[cmte_to_cand[c]]) for c in cmte_to_cand
            if cmte_to_cand[c] in cand_party]
    print(f"[cand-master] resolved {len(rows):,} committees -> candidate party")
    con.execute("CREATE OR REPLACE TEMP TABLE _cmte_cand_party (cmte_id VARCHAR, party VARCHAR)")
    con.executemany("INSERT INTO _cmte_cand_party VALUES (?, ?)", rows)
    # Fill only rows still Unknown (don't override an explicit committee party).
    con.execute("""
        UPDATE candidate_finance cf
        SET party = m.party
        FROM _cmte_cand_party m
        WHERE cf.fec_candidate_id = m.cmte_id
          AND (cf.party IS NULL OR cf.party = 'Unknown')
          AND cf.recipient_type = 'committee'
    """)
    con.execute("DROP TABLE IF EXISTS _cmte_cand_party")


def main() -> int:
    con = duckdb.connect(NY_STATEWIDE)

    print("=== BEFORE backfill ===")
    coverage(con)

    print("\n[bulk] load_fec_committee_master (cm{yy}.zip per cycle) ...")
    res = load_fec_committee_master(con, cycles=CYCLES, download_dir=TMP)
    print(f"  committee-master rows touched: {res['rows_loaded']:,}; "
          f"download_failures={res['download_failures']}")
    seed = seed_committee_party_overrides(con)
    print(f"  conduit overrides seeded: {seed['seeded']} (table total {seed['total']})")

    print("\n=== AFTER committee-master + overrides ===")
    coverage(con)

    print("\n[bulk] resolving candidate-committee party via candidate master (cn{yy}.zip) ...")
    resolve_via_candidate_master(con)
    print("\n=== AFTER candidate-master resolution ===")
    coverage(con)

    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
