"""Empirically locate earmarked (conduit-routed) money in FEC bulk Schedule A.

Question: my recipient-anchored inflow filters CMTE_ID in {candidate committees}
and memo_cd != 'X'. Where does ActBlue/WinRed-earmarked money to those candidates
actually live in the bulk file — under the candidate (as 15E or memo_cd='X'),
or under the conduit (CMTE_ID=conduit, with OTHER_ID = the candidate)? Measures
the buckets on 2024 so attribution is correct, not guessed.

Keeps itcont2024.txt for reuse by the reload.
"""
import csv, glob, io, os, zipfile
import duckdb, httpx

TMP = "data/_fec_bulk"
CY = 2024
TARGET = {"WA", "NY", "TX"}
CONDUITS = ("C00401224", "C00694323")  # ActBlue, WinRed
COLS = ["cmte_id","amndt_ind","rpt_tp","transaction_pgi","image_num","transaction_tp",
        "entity_tp","name","city","state","zip_code","employer","occupation",
        "transaction_dt","transaction_amt","other_id","tran_id","file_num","memo_cd","memo_text","sub_id"]

os.makedirs(TMP, exist_ok=True)
# recipient (candidate-committee) set for WA/NY/TX H+S
cand = {}
for cy in [2018,2020,2022,2024,2026]:
    z=f"{TMP}/cn{cy}.zip"
    if not os.path.exists(z):
        with httpx.stream("GET", f"https://www.fec.gov/files/bulk-downloads/{cy}/cn{cy%100:02d}.zip", timeout=300, follow_redirects=True) as r:
            r.raise_for_status(); open(z,"wb").write(r.read())
    with zipfile.ZipFile(z) as zf:
        with zf.open("cn.txt" if "cn.txt" in zf.namelist() else zf.namelist()[0]) as fh:
            for raw in io.TextIOWrapper(fh, encoding="latin-1"):
                p=raw.rstrip().split("|")
                if len(p)>=7 and p[5] in ("H","S") and p[4] in TARGET: cand[p[0]]=(p[4],p[5])
cmte2cand={}
for z in sorted(glob.glob(f"{TMP}/cm*.zip")):
    with zipfile.ZipFile(z) as zf:
        with zf.open("cm.txt" if "cm.txt" in zf.namelist() else zf.namelist()[0]) as fh:
            for raw in io.TextIOWrapper(fh, encoding="latin-1"):
                p=raw.rstrip().split("|")
                if len(p)>=15 and p[14] in cand: cmte2cand[p[0]]=p[14]
recip_csv=f"{TMP}/_earmark_recip.csv"
with open(recip_csv,"w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["cmte_id"]); w.writerows([(c,) for c in cmte2cand])
print(f"WA/NY/TX candidate committees: {len(cmte2cand):,}", flush=True)

# download + keep 2024 itcont
zip_path, txt_path = f"{TMP}/indiv{CY}.zip", f"{TMP}/itcont{CY}.txt"
if not os.path.exists(txt_path):
    if not os.path.exists(zip_path):
        print("downloading indiv24.zip ...", flush=True)
        with httpx.stream("GET", f"https://www.fec.gov/files/bulk-downloads/{CY}/indiv{CY%100:02d}.zip", timeout=600, follow_redirects=True) as r:
            r.raise_for_status()
            with open(zip_path,"wb") as f:
                for ch in r.iter_bytes(1<<20): f.write(ch)
    with zipfile.ZipFile(zip_path) as zf:
        inner="itcont.txt" if "itcont.txt" in zf.namelist() else zf.namelist()[0]
        with zf.open(inner) as s, open(txt_path,"wb") as d: d.write(s.read())

c=duckdb.connect()
coldefs=", ".join(f"'{x}': 'VARCHAR'" for x in COLS)
c.execute(f"CREATE VIEW ic AS SELECT * FROM read_csv('{txt_path}', delim='|', header=false, columns={{{coldefs}}}, quote='', strict_mode=false) WHERE entity_tp='IND' AND TRY_CAST(transaction_amt AS DECIMAL(14,2))>0")
c.execute(f"CREATE VIEW rc AS SELECT * FROM read_csv('{recip_csv}', header=true)")
def m(q): return c.execute(q).fetchall()

print("\n=== A) CMTE_ID in CANDIDATE committees (the inflow recipients) ===", flush=True)
print("by memo_cd, transaction_tp:")
for row in m("""SELECT (ic.memo_cd='X') AS is_memo, ic.transaction_tp,
  COUNT(*) n, ROUND(SUM(TRY_CAST(ic.transaction_amt AS DECIMAL(14,2)))/1e6,1) M
  FROM ic JOIN rc ON ic.cmte_id=rc.cmte_id GROUP BY 1,2 ORDER BY M DESC LIMIT 12"""):
    print("  memo=%s tt=%-4s n=%-9s $%sM" % (row[0],row[1],f"{row[2]:,}",row[3]))

print("\n=== B) CMTE_ID in CONDUITS (ActBlue/WinRed), OTHER_ID -> our candidates ===", flush=True)
for row in m(f"""SELECT ic.cmte_id, (ic.memo_cd='X') is_memo, ic.transaction_tp,
  COUNT(*) n, ROUND(SUM(TRY_CAST(ic.transaction_amt AS DECIMAL(14,2)))/1e6,1) M
  FROM ic JOIN rc ON ic.other_id=rc.cmte_id
  WHERE ic.cmte_id IN {CONDUITS} GROUP BY 1,2,3 ORDER BY M DESC LIMIT 12"""):
    print("  cmte=%s memo=%s tt=%-4s n=%-9s $%sM" % (row[0],row[1],row[2],f"{row[3]:,}",row[4]))

print("\n=== C) ALL rows whose OTHER_ID -> our candidates (any cmte), by memo ===", flush=True)
for row in m("""SELECT (ic.memo_cd='X') is_memo, ic.transaction_tp, COUNT(*) n,
  ROUND(SUM(TRY_CAST(ic.transaction_amt AS DECIMAL(14,2)))/1e6,1) M
  FROM ic JOIN rc ON ic.other_id=rc.cmte_id GROUP BY 1,2 ORDER BY M DESC LIMIT 12"""):
    print("  memo=%s tt=%-4s n=%-9s $%sM" % (row[0],row[1],f"{row[2]:,}",row[3]))
c.close()
print("\n(kept itcont2024.txt for reuse)", flush=True)
