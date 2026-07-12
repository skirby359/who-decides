"""Safe-seat partisan split vs statewide PRESIDENTIAL party ratio — WA / NY / TX / ID.

Sequel to the "not a one-party artifact" claim in `docs/safe-seat-washington.md`. That
claim is *directional*: both parties hold safe seats (WA 2024: 69 D / 44 R), so safe
seats are a bipartisan feature of a geographically sorted map, not a one-party gerrymander
story. True in all four states. This script asks the sharper question the paper does NOT
answer: does the safe-seat R:D ratio *match* the state's underlying party ratio?

Party proxy = the statewide two-party PRESIDENTIAL vote. We compare, per state, the share
of SAFE (non-competitive) lower-chamber seats held/favored by the locally dominant party
against that party's presidential two-party share.

Finding (see output): the direction always matches, but the *ratio* does not — safe seats
systematically OVER-represent the locally dominant party relative to its presidential
vote, and the gap widens as the state gets more lopsided (WA ~+2pp -> ID ~+19pp). That is
the geographic-packing signature: the minority party's votes concentrate in a few
districts, so it wins a smaller share of safe seats than of the statewide vote.

Universe = LOWER chamber, matching `diag_safe_seat_states.py` (whose classification and
TX backfill this script reuses verbatim). Read-only, aggregates only.
    python scripts/diag_safe_seat_party_ratio.py

CAVEATS:
  - NY 2024 presidential is not loaded, so NY uses the 2020 presidential vote against the
    2022 Assembly lines — the comparison crosses a redistricting and is the weakest row.
  - TX's 54 uncontested House seats have their holding party assigned from 2024
    presidential lean (via diag_tx_safe_seat_backfill), so the TX safe-seat split is mildly
    circular with the presidential number for those seats.
  - Also for WA the paper's headline "69 D / 44 R" is the ALL leg+cong universe (61.1% D);
    the lower-chamber-only figure here (WA House) is the apples-to-apples cross-state cut.
"""
import diag_safe_seat_states as ss  # reuse STATES, PARTY, band, count, txbf
import duckdb

# Presidential general per state. NY 2024 not loaded -> 2020 proxy (see caveat).
PRES_DATE = {"WA": "2024-11-05", "NY": "2020-11-03", "TX": "2024-11-05", "ID": "2024-11-05"}


def pres_two_party(db, date):
    """Statewide (D, R) presidential two-party vote totals, summed from precinct_results."""
    c = duckdb.connect(db, read_only=True)
    d, r = c.execute(f"""
        SELECT SUM(CASE WHEN {ss.PARTY}='D' THEN pr.votes ELSE 0 END),
               SUM(CASE WHEN {ss.PARTY}='R' THEN pr.votes ELSE 0 END)
        FROM races r JOIN elections e ON e.election_id = r.election_id
        JOIN candidates cd ON cd.race_id = r.race_id
        JOIN precinct_results pr ON pr.candidate_id = cd.candidate_id
        WHERE e.election_date = DATE '{date}' AND r.office ILIKE '%PRESIDENT%'
          AND COALESCE(cd.is_writein, FALSE) = FALSE
    """).fetchone()
    c.close()
    return float(d or 0), float(r or 0)


def safe_dr(st, db, date, lower):
    """(d_safe, r_safe) safe-seat counts for a state's lower chamber, reusing the exact
    classification in diag_safe_seat_states — including the TX 96->150 backfill."""
    cats, d_safe, r_safe = ss.count(db, date, lower)
    if st == "TX":
        dbres = ss.txbf.db_house_results()
        pres = ss.txbf.r206_presidential()
        d_safe = r_safe = 0
        for dist in range(1, ss.txbf.HOUSE_TOTAL + 1):
            if dist in dbres:
                cat, d, r = dbres[dist]; lean_d = d >= r
            else:
                cat = "no_major_choice"; hd, hr = pres.get(dist, (0, 0)); lean_d = hd >= hr
            if cat in ("no_major_choice", "Likely", "Solid"):
                d_safe, r_safe = (d_safe + 1, r_safe) if lean_d else (d_safe, r_safe + 1)
    return d_safe, r_safe


def main():
    print("Safe-seat partisan split vs statewide presidential party ratio — LOWER chamber\n")
    hdr = (f"{'st':3} {'chamber':9} {'safe D/R':>9} {'safe %dom':>9} {'pres %dom':>9} "
           f"{'gap pp':>7} {'safe ratio':>10} {'pres ratio':>10}")
    print(hdr); print("-" * len(hdr))
    for st, db, date, lower, _upper in ss.STATES:
        d_safe, r_safe = safe_dr(st, db, date, lower)
        pd, pr = pres_two_party(db, PRES_DATE[st])
        safe_tot = d_safe + r_safe
        pres_tot = pd + pr
        dom = "D" if pd >= pr else "R"                       # presidentially dominant party
        pres_dom = (pd if dom == "D" else pr) / pres_tot * 100
        safe_dom = (d_safe if dom == "D" else r_safe) / safe_tot * 100
        gap = safe_dom - pres_dom
        # dominant:minority ratios
        safe_ratio = (max(d_safe, r_safe) / min(d_safe, r_safe)) if min(d_safe, r_safe) else float("inf")
        pres_ratio = (max(pd, pr) / min(pd, pr)) if min(pd, pr) else float("inf")
        pnote = " (2020!)" if st == "NY" else ""
        print(f"{st:3} {ss.CHAMBER_NAME[st][0]:9} {f'{d_safe}/{r_safe}':>9} "
              f"{safe_dom:8.1f}%{dom} {pres_dom:8.1f}%{dom} {gap:+6.1f} "
              f"{safe_ratio:9.2f} {pres_ratio:8.2f}{pnote}")

    print("\nDirection matches everywhere (safe-seat majority party = presidential winner);")
    print("but safe seats OVER-represent the dominant party vs its presidential vote, and")
    print("the gap grows with lopsidedness (packing signature). NY pres = 2020 (2024 not")
    print("loaded) vs 2022 Assembly — weakest row. TX uncontested-seat party from pres lean.")


if __name__ == "__main__":
    main()
