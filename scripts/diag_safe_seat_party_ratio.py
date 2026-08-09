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

Universe = LOWER chamber. NY and ID reuse the classification in `diag_safe_seat_states.py`;
WA and TX do NOT — see the two corrections below. Read-only, aggregates only.
    python scripts/diag_safe_seat_party_ratio.py

CORRECTED 2026-07-28 (both rows the paper quotes were stale):
  - WA now comes from `reports/seat_competition.csv` (certified universe, written by
    `diag_seat_competition.py`), not from `diag_safe_seat_states.py`. The latter reads
    `precinct_results` under the retired conflated definition and gives 54 D / 33 R on an
    88.8% universe; the certified House figure is **53 D / 33 R** on 87.8%, which moved
    the WA gap from +2.6 to +2.1. Both WA bases are printed, because the paper uses the
    all-seats split (68 D / 43 R) in Appendix A and the House split cross-state, and those
    are different numbers that must not be quoted interchangeably.
  - TX party is now **observed** from the certified candidate list
    (`data/raw/tx/2024_tx_house_candidates.csv`), not imputed from presidential lean.
    The imputation was wrong in 5 of 54 backfilled seats, gave 51 D / 90 R instead of the
    observed **56 D / 85 R**, and — being an imputation FROM presidential lean, then
    compared AGAINST presidential lean — was circular. TX's gap moves +6.9 -> +3.4.

CAVEATS:
  - NY 2024 presidential is not loaded, so NY uses the 2020 presidential vote against the
    2022 Assembly lines — the comparison crosses a redistricting and is the weakest row.
  - This whole comparison is descriptive. A gap is consistent with packing AND with
    residential geography, turnout differences, and the definition of "safe" used here;
    single-member districts carry no proportionality expectation. See the paper's
    Appendix E, which reports it as an exploratory cut and draws no inference about intent.
"""
import csv
import os

import diag_safe_seat_states as ss  # reuse STATES, PARTY, band, count, txbf
import duckdb

SEATS_CSV = os.path.join("reports", "seat_competition.csv")
TX_CANDS = os.path.join("data", "raw", "tx", "2024_tx_house_candidates.csv")

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


def wa_safe_dr(house_only: bool) -> tuple[int, int]:
    """(d, r) among WA 2024 NOT-CLOSE seats, from the certified universe.

    "Not close" is the paper's Dimension 1: a single candidate, or a top-two margin >= 10.
    Winner party is the LEADING CANDIDATE's, never inferred from aggregate D/R totals.
    """
    if not os.path.exists(SEATS_CSV):
        raise SystemExit(f"{SEATS_CSV} missing — run scripts/diag_seat_competition.py first")
    d = r = 0
    with open(SEATS_CSV, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["year"] != "2024":
                continue
            if house_only and row["chamber"] != "HSE":
                continue
            m = row["cand_margin"]
            not_close = row["cand_band"] == "single candidate" or (m and float(m) >= 10)
            if not not_close:
                continue
            if row["winner_party"] == "D":
                d += 1
            elif row["winner_party"] == "R":
                r += 1
    return d, r


def tx_safe_dr() -> tuple[int, int]:
    """(d, r) among TX 2024 House not-close seats, party OBSERVED from certified returns."""
    if not os.path.exists(TX_CANDS):
        raise SystemExit(f"{TX_CANDS} missing — run scripts/build_tx_house_candidates.py")
    d = r = 0
    with open(TX_CANDS, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            uncontested = row["uncontested"] == "True"
            margin = float(row["margin_pct"]) if row["margin_pct"] else None
            if not (uncontested or (margin is not None and margin >= 10)):
                continue
            if row["winner_party"] == "D":
                d += 1
            elif row["winner_party"] == "R":
                r += 1
    return d, r


def safe_dr(st, db, date, lower):
    """(d_safe, r_safe) safe-seat counts for a state's lower chamber."""
    if st == "WA":
        return wa_safe_dr(house_only=True)
    if st == "TX":
        return tx_safe_dr()
    cats, d_safe, r_safe = ss.count(db, date, lower)
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

    # WA on the ALL leg+cong universe — the basis the paper's Appendix A uses. Printed
    # separately because 61.6% (House) and 61.3% (all seats) are DIFFERENT numbers against
    # the same 59.5% presidential share, and quoting one gap with the other's split is
    # exactly the mismatch this correction removes.
    wd, wr = wa_safe_dr(house_only=False)
    pd_, pr_ = pres_two_party("data/wa_statewide.duckdb", PRES_DATE["WA"])
    dom_share = pd_ / (pd_ + pr_) * 100
    all_share = wd / (wd + wr) * 100
    print(f"\nWA, ALL leg+cong seats (Appendix A basis): {wd}/{wr} safe "
          f"= {all_share:.1f}%D vs {dom_share:.1f}%D presidential -> {all_share-dom_share:+.1f} pp")
    print(f"WA, House only  (cross-state basis, row above): "
          f"{'/'.join(map(str, wa_safe_dr(house_only=True)))} safe")

    print("\nDirection matches everywhere (safe-seat majority party = presidential winner);")
    print("but safe seats OVER-represent the dominant party vs its presidential vote, and")
    print("the gap grows with lopsidedness (WA ~+2pp -> ID ~+19pp). CONSISTENT WITH packing")
    print("and equally consistent with residential geography, turnout, and the 'safe'")
    print("definition — it cannot distinguish them. NY pres = 2020 (2024 not loaded) vs 2022")
    print("Assembly — weakest row. WA = certified universe; TX party = certified returns.")


if __name__ == "__main__":
    main()
