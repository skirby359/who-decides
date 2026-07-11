"""INFLOW-side money x competitiveness for NY/TX U.S. House (2022-2026).

Uses the recipient-anchored inflow (data/fec_inflow.duckdb: all-state donors
-> NY/TX candidates) joined to each district's competitiveness band (this
project's forecast margin). The sharp question the donor-side cut couldn't
answer: does money — especially OUT-OF-STATE money — actually chase the
Tossups the model flags, or pile into safe seats?
"""
import duckdb


def band(m):
    if m < 5: return "Tossup"
    if m < 10: return "Lean"
    if m < 20: return "Likely"
    return "Solid"


def competitiveness():
    comp = {}
    for st, f in [("WA", "data/wa_statewide.duckdb"), ("NY", "data/ny_statewide.duckdb"), ("TX", "data/tx_statewide.duckdb")]:
        c = duckdb.connect(f, read_only=True)  # raises if the API load still locks it
        rows = c.execute(
            "WITH r AS (SELECT district_id, predicted_margin, "
            "ROW_NUMBER() OVER (PARTITION BY district_id ORDER BY as_of_date DESC) rn "
            "FROM forecast_predictions WHERE party='Democratic' AND district_id LIKE 'cd%') "
            "SELECT district_id, predicted_margin FROM r WHERE rn=1"
        ).fetchall()
        c.close()
        for cd, m in rows:
            comp[(st, cd)] = band(abs(float(m)))
    return comp


def main():
    comp = competitiveness()
    ic = duckdb.connect("data/fec_inflow.duckdb", read_only=True)
    rows = ic.execute("""
        SELECT recipient_state,
               'cd' || LPAD(CAST(TRY_CAST(recipient_district AS INTEGER) AS VARCHAR), 2, '0') AS cd,
               SUM(contribution_amount) AS tot,
               SUM(CASE WHEN contributor_state <> recipient_state THEN contribution_amount ELSE 0 END) AS oos
        FROM inflow_contributions
        WHERE recipient_office='H' AND election_cycle >= 2022 AND contribution_amount > 0
          AND TRY_CAST(recipient_district AS INTEGER) IS NOT NULL
        GROUP BY 1, 2
    """).fetchall()
    ic.close()

    bands = {b: {"d": 0, "tot": 0.0, "oos": 0.0} for b in ["Tossup", "Lean", "Likely", "Solid"]}
    dcount = {b: 0 for b in bands}
    for (st, cd), b in comp.items():
        dcount[b] += 1
    matched = 0
    for st, cd, tot, oos in rows:
        b = comp.get((st, cd))
        if not b:
            continue
        matched += 1
        bands[b]["d"] += 1
        bands[b]["tot"] += float(tot)
        bands[b]["oos"] += float(oos)

    total = sum(b["tot"] for b in bands.values()) or 1.0
    ndist = sum(dcount.values()) or 1
    print("INFLOW to WA+NY+TX U.S. House by competitiveness band (2022-2026)\n")
    print("Band   | #dists | %dists | $M in  | $/dist | %of$  | out-of-state$ | OOS share")
    print("-" * 86)
    for b in ["Tossup", "Lean", "Likely", "Solid"]:
        x = bands[b]
        perdist = x["tot"] / x["d"] / 1e6 if x["d"] else 0
        oosshare = x["oos"] / x["tot"] * 100 if x["tot"] else 0
        print(f"{b:6} | {x['d']:>6} | {dcount[b]/ndist*100:5.1f}% | {x['tot']/1e6:6.1f} | "
              f"{perdist:6.2f}M | {x['tot']/total*100:4.1f}% | {x['oos']/1e6:11.1f} | {oosshare:6.1f}%")
    print(f"\nTotal WA+NY+TX House inflow (2022-2026): ${total/1e6:,.0f}M across {matched} districts")

    # --- Senate: per-state inflow + out-of-state share. The model does not forecast
    # US Senate, so competitiveness is noted via actual results in the write-up
    # (TX Senate = competitive: Cruz/O'Rourke 2018 R+2.6, Cruz/Allred 2024 R+8.8;
    # NY/WA Senate = safe-D). ---
    ic = duckdb.connect("data/fec_inflow.duckdb", read_only=True)
    srows = ic.execute("""
        SELECT recipient_state,
               SUM(contribution_amount) AS tot,
               SUM(CASE WHEN contributor_state <> recipient_state THEN contribution_amount ELSE 0 END) AS oos,
               COUNT(*) AS n
        FROM inflow_contributions
        WHERE recipient_office='S' AND contribution_amount > 0
        GROUP BY 1 ORDER BY tot DESC
    """).fetchall()
    ic.close()
    print("\nINFLOW to U.S. SENATE candidates by state (2018-2026)")
    print("state | $M in  | rows      | out-of-state$ | OOS share")
    print("-" * 56)
    for st, tot, oos, n in srows:
        print(f"  {st}  | {float(tot)/1e6:6.1f} | {n:>9,} | {float(oos)/1e6:11.1f} | {float(oos)/float(tot)*100:5.1f}%")


if __name__ == "__main__":
    main()
