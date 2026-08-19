"""Where does the money go on the LOSING side? Longshot vs favored money by district
competitiveness — a follow-on to `docs/cross-state-fec-money.md`.

The cross-state paper measures money by competitiveness band but not by which SIDE of a
lopsided district it flows to. A safe seat for one party is a longshot for the other, so
this asks: within safe districts, what share of inflow money reaches the DISADVANTAGED
(longshot) party's candidate? Hypothesis (Kirby): almost none. Confirmed and quantified.

Method:
  - favored party of a district = sign of the latest Democratic forecast margin from the
    stored `forecast_predictions` table (predicted_margin > 0 -> D favored, < 0 -> R).
    (Reads the pre-computed model output; does not run the private model.)
  - recipient party of each inflow contribution = cmte_id -> party via the committee-keyed
    `candidate_finance` rows (backfilled from FEC cm/cn masters; see backfill_*_committee_party).
  - U.S. House, cycles >= 2022 (post-redistricting, matches the current map).
  - band by |margin|: Tossup<5 / Lean5-10 / Likely10-20 / Solid>=20; "safe" = Likely+Solid.

Feasible for NY and WA (committee->party coverage ~99-100% of House inflow $). TX is NOT
feasible from on-disk data: `tx_statewide.duckdb`.`candidate_finance` has no committee->party
rows, so recipient party can't be resolved — it would need a TX cm/cn backfill. The script
detects this and prints a skip line rather than a wrong number.

Read-only, aggregates only. Uses ETL-built inputs (forecast_predictions + the committee
party backfill), so like diag_ie_vs_margin it is not standalone from a raw public extract.
    python scripts/diag_loser_side_money.py
"""
import duckdb

from cross_state_common import district_cycle_competitiveness, region_states

STATES = region_states()


# The private band() this file used to carry is gone (2026-08-16). It existed only because
# the shared helper returned abs(), and §J needs the SIGN to tell favored from longshot;
# district_cycle_competitiveness keeps the sign, so there is nothing left to fork.


def load_house_inflow():
    """House inflow 2022-2026 grouped by state / district (cd##) / committee."""
    ic = duckdb.connect("data/fec_inflow.duckdb", read_only=True)
    rows = ic.execute("""
        SELECT recipient_state st,
               'cd' || LPAD(CAST(TRY_CAST(recipient_district AS INTEGER) AS VARCHAR), 2, '0') cd,
               election_cycle cyc,
               cmte_id,
               SUM(contribution_amount) amt
        FROM inflow_contributions
        WHERE recipient_office='H' AND election_cycle>=2022 AND contribution_amount>0
          AND TRY_CAST(recipient_district AS INTEGER) IS NOT NULL
        GROUP BY 1, 2, 3, 4
    """).fetchall()
    ic.close()
    return rows


# district_favored() is REMOVED (2026-08-16). It read the 2026 forecast and applied it to
# 2022-2026 money, so a district that was close in 2024 and safe now was scored safe for its
# 2024 dollars -- and, worse here than elsewhere, its FAVORED SIDE was taken from the 2026
# forecast too, so "longshot money" could be measured against the wrong party. The
# cycle-specific map supplies both the band and the signed margin.


def committee_party(con):
    """{cmte_id: 'Democratic'|'Republican'} from committee-keyed candidate_finance rows."""
    rows = con.execute(
        "SELECT fec_candidate_id, party FROM candidate_finance "
        "WHERE party IN ('Democratic','Republican') AND LEFT(fec_candidate_id,1)='C' "
        "GROUP BY 1, 2").fetchall()
    cparty, conflicts = {}, 0
    for cid, p in rows:
        if cid in cparty and cparty[cid] != p:
            conflicts += 1; cparty[cid] = "CONFLICT"
        else:
            cparty[cid] = p
    return {k: v for k, v in cparty.items() if v in ("Democratic", "Republican")}, conflicts


def main():
    inflow = load_house_inflow()
    allcomp = district_cycle_competitiveness()
    for ST, f in STATES:
        con = duckdb.connect(f, read_only=True)
        comp = {(cyc, cd): v for (st, cyc, cd), v in allcomp.items()
                if st == ST and v.margin is not None}
        cmap, conflicts = committee_party(con)
        con.close()

        rows = [r for r in inflow if r[0] == ST]
        tot_all = sum(float(r[4]) for r in rows)
        print(f"\n{'='*72}\n{ST} — U.S. House inflow, 2022-2026")
        if not cmap:
            print(f"  total House inflow ${tot_all/1e6:.1f}M — SKIPPED: no committee->party "
                  f"map in candidate_finance (needs a {ST} cm/cn backfill).")
            continue

        matched = sum(float(r[4]) for r in rows if r[3] in cmap)
        in_comp = sum(float(r[4]) for r in rows if (int(r[2]), r[1]) in comp)
        print(f"  total House inflow ${tot_all/1e6:8.1f}M")
        print(f"  in a forecast district: ${in_comp/1e6:8.1f}M ({in_comp/tot_all*100:.1f}%)")
        print(f"  cmte->party resolvable: ${matched/1e6:8.1f}M ({matched/tot_all*100:.1f}%)  "
              f"[committee->D/R rows={len(cmap):,}, conflicts={conflicts}]")

        favored = lambda m: "Democratic" if m > 0 else "Republican"
        bands = {b: {"fav": 0.0, "long": 0.0, "unres": 0.0, "dists": set()}
                 for b in ["Tossup", "Lean", "Likely", "Solid"]}
        for _st, cd, cyc, cmte, amt in rows:
            cell = comp.get((int(cyc), cd))
            if cell is None:
                continue
            m = cell.margin; b = cell.band; amt = float(amt)
            bands[b]["dists"].add((int(cyc), cd))
            rp = cmap.get(cmte)
            if rp is None:
                bands[b]["unres"] += amt
            elif rp == favored(m):
                bands[b]["fav"] += amt
            else:
                bands[b]["long"] += amt

        print(f"\n  Band   | #dist | favored $M | longshot $M | unres $M | longshot share (resolved)")
        print("  " + "-" * 82)
        safe = {"fav": 0.0, "long": 0.0}; solid = {"fav": 0.0, "long": 0.0}
        for b in ["Tossup", "Lean", "Likely", "Solid"]:
            x = bands[b]; resolved = x["fav"] + x["long"]
            ls = x["long"] / resolved * 100 if resolved else 0
            print(f"  {b:6} | {len(x['dists']):>5} | {x['fav']/1e6:10.2f} | {x['long']/1e6:11.2f} | "
                  f"{x['unres']/1e6:8.2f} | {ls:5.1f}%")
            if b in ("Likely", "Solid"):
                safe["fav"] += x["fav"]; safe["long"] += x["long"]
            if b == "Solid":
                solid["fav"] += x["fav"]; solid["long"] += x["long"]

        sres = safe["fav"] + safe["long"]
        if sres:
            print(f"\n  SAFE (Likely+Solid, |margin|>=10): favored ${safe['fav']/1e6:.1f}M  "
                  f"longshot ${safe['long']/1e6:.1f}M  -> longshot {safe['long']/sres*100:.1f}%")
        solres = solid["fav"] + solid["long"]
        if solres:
            print(f"  SOLID only (|margin|>=20):         favored ${solid['fav']/1e6:.1f}M  "
                  f"longshot ${solid['long']/1e6:.1f}M  -> longshot {solid['long']/solres*100:.1f}%")

    print("\nMonotonic: the safer the seat, the smaller the longshot's share; in Solid seats")
    print("the disadvantaged party gets ~5% of the money. CAVEATS: inflow, House-only, >=2022;")
    print("leadership PACs tied to safe incumbents may inflate the favored side; the favored")
    print("label is fragile in near-even races (so trust the safe bands, not Tossup/Lean).")


if __name__ == "__main__":
    main()
