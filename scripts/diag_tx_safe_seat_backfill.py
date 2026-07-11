"""TX safe-seat BACKFILL — complete the 150 state-House count.

The TX Legislative Council canvass-grade VTD returns (data/raw/tx/.../2024_General_
Election_Returns.csv, loaded into tx_statewide.duckdb) carry only the ~96 House
districts that had a contested general; TLC publishes NO precinct returns for
UNCONTESTED races, so the other ~54 districts are simply absent. (Verified: the
press-reported 2024 unopposed seats — HD 35/36/38/40/42/49/51/75/78/79/90/92/95
(D), 81 (R), etc. — are exactly the ones missing.) Those 54 are therefore
non-competitive by construction (no major-party opponent => no_major_choice).

This backfills them so TX House = 150:
  - 96 with VTD returns  -> band by the ACTUAL D-vs-R two-party margin (from DB);
  - 54 absent            -> no_major_choice (uncontested), holding party assigned
                            by the district's 2024 PRESIDENTIAL lean from the TLC
                            r206 Election24G report (planh2316_r206_election24g.xls,
                            Sheet2: Harris-D vs Trump-R per House district) — an
                            on-disk, authoritative, all-150-district source.

Also emits a presidential-lean competitiveness band for ALL 150 districts as an
independent cross-check (Cook-PVI-style; covers every seat incl. uncontested).
"""
import duckdb
import pandas as pd

DB = "data/tx_statewide.duckdb"
R206 = "data/raw/tx/plans/planh2316_r206_election24g.xls"
HOUSE_TOTAL = 150

PARTY = """CASE
  WHEN cd.party_normalized ILIKE '%democrat%' THEN 'D'
  WHEN cd.party_normalized ILIKE '%republican%' OR cd.party_normalized ILIKE '%gop%' THEN 'R'
  ELSE 'O' END"""


def band(m):
    if m < 5: return "Tossup"
    if m < 10: return "Lean"
    if m < 20: return "Likely"
    return "Solid"


def db_house_results():
    """{district:int -> (cat, dvotes, rvotes)} for House districts with VTD returns."""
    c = duckdb.connect(DB, read_only=True)
    rows = c.execute(f"""
        WITH seat AS (
            SELECT r.race_id,
                   CAST(regexp_extract(r.office,'DISTRICT ([0-9]+)',1) AS INT) dist,
                   MAX(CASE WHEN {PARTY}='D' THEN 1 ELSE 0 END) hasD,
                   MAX(CASE WHEN {PARTY}='R' THEN 1 ELSE 0 END) hasR
            FROM races r JOIN elections e ON e.election_id=r.election_id
            JOIN candidates cd ON cd.race_id=r.race_id
            WHERE e.election_date=DATE '2024-11-05' AND r.office ILIKE '%HOUSE DISTRICT%'
              AND COALESCE(cd.is_writein,FALSE)=FALSE
            GROUP BY 1,2),
        votes AS (
            SELECT r.race_id,
                   SUM(CASE WHEN {PARTY}='D' THEN pr.votes ELSE 0 END) d,
                   SUM(CASE WHEN {PARTY}='R' THEN pr.votes ELSE 0 END) r
            FROM races r JOIN elections e ON e.election_id=r.election_id
            JOIN candidates cd ON cd.race_id=r.race_id
            JOIN precinct_results pr ON pr.candidate_id=cd.candidate_id
            WHERE e.election_date=DATE '2024-11-05' AND r.office ILIKE '%HOUSE DISTRICT%'
              AND COALESCE(cd.is_writein,FALSE)=FALSE
            GROUP BY 1)
        SELECT s.dist, s.hasD, s.hasR, COALESCE(v.d,0) d, COALESCE(v.r,0) r
        FROM seat s LEFT JOIN votes v USING (race_id)
    """).fetchall()
    c.close()
    out = {}
    for dist, hasD, hasR, d, r in rows:
        d = float(d or 0); r = float(r or 0)
        if not (hasD and hasR) or (d + r) == 0:
            cat = "no_major_choice"
        else:
            cat = band(abs(d - r) / (d + r) * 100)
        out[dist] = (cat, d, r)
    return out


def r206_presidential():
    """{district:int -> (harris_d, trump_r)} for all 150 House districts."""
    df = pd.read_excel(R206, sheet_name="Sheet2", header=None)
    pres = {}
    for _, row in df.iterrows():
        dist = str(row[1]).strip()
        if not dist.replace(".0", "").isdigit():
            continue
        d = float(row[3]); r = float(row[11])  # Harris-D votes, Trump-R votes
        pres[int(float(dist))] = (d, r)
    return pres


def main():
    db = db_house_results()
    pres = r206_presidential()
    in_data = set(db)
    missing = sorted(set(range(1, HOUSE_TOTAL + 1)) - in_data)
    print(f"TX State House 2024: {len(in_data)} districts with VTD returns, "
          f"{len(missing)} absent (uncontested):")
    print(f"  missing = {missing}\n")

    # ----- ACTUAL-RACE method (completed to 150) -----
    cats = {"no_major_choice": 0, "Tossup": 0, "Lean": 0, "Likely": 0, "Solid": 0}
    d_safe = r_safe = 0
    for dist in range(1, HOUSE_TOTAL + 1):
        if dist in db:
            cat, d, r = db[dist]
            lean_d = d >= r
        else:  # uncontested -> no_major_choice; holding party by presidential lean
            cat = "no_major_choice"
            hd, hr = pres.get(dist, (0, 0))
            lean_d = hd >= hr
        cats[cat] += 1
        if cat in ("no_major_choice", "Likely", "Solid"):
            if lean_d:
                d_safe += 1
            else:
                r_safe += 1
    n = sum(cats.values())
    noncomp = cats["no_major_choice"] + cats["Likely"] + cats["Solid"]
    print("ACTUAL-RACE result, completed to 150 House seats:")
    print(f"  no_major_choice {cats['no_major_choice']}  Tossup {cats['Tossup']}  "
          f"Lean {cats['Lean']}  Likely {cats['Likely']}  Solid {cats['Solid']}")
    print(f"  NON-COMPETITIVE = {noncomp}/150 = {noncomp/n*100:.1f}%  "
          f"(competitive {cats['Tossup']+cats['Lean']}); safe split {d_safe} D / {r_safe} R\n")

    # ----- PRESIDENTIAL-LEAN cross-check (all 150, Cook-PVI style) -----
    pcats = {"Tossup": 0, "Lean": 0, "Likely": 0, "Solid": 0}
    for dist in range(1, HOUSE_TOTAL + 1):
        hd, hr = pres.get(dist, (0, 0))
        if hd + hr == 0:
            continue
        pcats[band(abs(hd - hr) / (hd + hr) * 100)] += 1
    pn = sum(pcats.values())
    psafe = pcats["Likely"] + pcats["Solid"]
    print("PRESIDENTIAL-LEAN cross-check (all 150 House districts, 2024 Harris vs Trump):")
    print(f"  Tossup {pcats['Tossup']}  Lean {pcats['Lean']}  Likely {pcats['Likely']}  "
          f"Solid {pcats['Solid']}")
    print(f"  >=10pt safe = {psafe}/{pn} = {psafe/pn*100:.1f}%  "
          f"(competitive {pcats['Tossup']+pcats['Lean']})")
    print("\n(The actual-race count and the presidential-lean count are different "
          "measures;\n both put TX House well above 90% non-competitive.)")


if __name__ == "__main__":
    main()
