"""Cross-state donor / recipient / magnet cuts on the FEC federal data (WA/NY/TX).

Three views, same basis as scripts/cross_state_fec_money.py (FEC committee
recipients, in-state-resident donors, positive amounts, 2018-2026):

  1. Top individual donors per state (name+zip, lifetime itemized $).
  2. Top recipient committees per state (named via the FEC committee master).
  3. Cross-state "money magnets" — committees funded by donors in ALL THREE
     states, ranked by combined dollars.

Needs the FEC committee master for names; downloads/caches cm{yy}.zip if absent.
"""
import duckdb
import glob
import io
import os
import zipfile

import httpx

from cross_state_common import region_states, region_codes, broadly_funded_min

TMP = "data/_fec_bulk"
CYCLES = [2018, 2020, 2022, 2024, 2026]
STATES = region_states()
W = lambda st: f"regexp_matches(COALESCE(fec_candidate_id,''),'^[CPHS][0-9]') AND contributor_state='{st}' AND contribution_amount>0"


def committee_names() -> dict:
    os.makedirs(TMP, exist_ok=True)
    for cy in CYCLES:
        z = f"{TMP}/cm{cy}.zip"
        if not os.path.exists(z):
            url = f"https://www.fec.gov/files/bulk-downloads/{cy}/cm{cy % 100:02d}.zip"
            with httpx.stream("GET", url, timeout=120.0, follow_redirects=True) as r:
                r.raise_for_status()
                with open(z, "wb") as f:
                    for chunk in r.iter_bytes(1 << 20):
                        f.write(chunk)
    nm = {}
    for z in sorted(glob.glob(f"{TMP}/cm*.zip")):
        with zipfile.ZipFile(z) as zf:
            fn = "cm.txt" if "cm.txt" in zf.namelist() else zf.namelist()[0]
            with zf.open(fn) as fh:
                for raw in io.TextIOWrapper(fh, encoding="latin-1"):
                    p = raw.rstrip().split("|")
                    if len(p) >= 15:
                        nm[p[0]] = p[1]
    return nm


def main():
    CM = committee_names()
    cname = lambda cid: CM.get(cid, "?")

    print("========== TOP 10 INDIVIDUAL DONORS (name+zip, lifetime $) ==========")
    for st, f in STATES:
        c = duckdb.connect(f, read_only=True)
        rows = c.execute(
            f"SELECT UPPER(TRIM(contributor_name)) nm, LEFT(COALESCE(contributor_zip,''),5) z, "
            f"SUM(contribution_amount) amt, MAX(UPPER(COALESCE(contributor_employer,''))) emp "
            f"FROM individual_contributions WHERE {W(st)} GROUP BY 1,2 ORDER BY amt DESC LIMIT 10"
        ).fetchall()
        c.close()
        print(f"\n--- {st} ---")
        for nm, z, amt, emp in rows:
            print(f"  ${float(amt)/1e6:5.2f}M  {nm[:32]:32} ({z}) [{emp[:22]}]")

    print("\n\n========== TOP 10 RECIPIENT COMMITTEES ==========")
    recip = {}
    for st, f in STATES:
        c = duckdb.connect(f, read_only=True)
        rows = c.execute(
            f"SELECT fec_candidate_id, SUM(contribution_amount) amt "
            f"FROM individual_contributions WHERE {W(st)} GROUP BY 1"
        ).fetchall()
        c.close()
        for cid, amt in rows:
            recip.setdefault(cid, {})[st] = float(amt)
        print(f"\n--- {st} ---")
        for cid, amt in sorted(rows, key=lambda r: -float(r[1]))[:10]:
            print(f"  ${float(amt)/1e6:5.1f}M  {cname(cid)[:46]:46} ({cid})")

    codes = region_codes()
    min_states = broadly_funded_min(codes)
    label = "ALL" if min_states >= len(codes) else f">={min_states} of"
    print(f"\n\n========== TOP 18 CROSS-STATE MONEY MAGNETS "
          f"(funded by {label} {'/'.join(codes)}) ==========")
    broad = sorted([(cid, d) for cid, d in recip.items() if len(d) >= min_states],
                   key=lambda x: -sum(x[1].values()))
    for cid, d in broad[:18]:
        percol = " / ".join(f"{code} {d.get(code, 0)/1e6:4.1f}" for code in codes)
        print(f"  ${sum(d.values())/1e6:5.0f}M  {cname(cid)[:40]:40}  [{percol}]")
    print(f"\n  committees funded by donors in {label} {len(codes)} region states: {len(broad):,} "
          f"(of {len(recip):,} touched by any)")


if __name__ == "__main__":
    main()
