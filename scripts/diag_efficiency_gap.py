"""Partisan-asymmetry metrics (efficiency gap + mean-median) on the district maps of
WA / NY / TX / ID — the Tier-1 follow-up to the "packing signature" in
`docs/safe-seat-washington.md`.

The safe-seat paper shows safe seats over-represent the locally dominant party (a packing
signature) but can't say whether that's deliberate line-drawing or natural geographic
clustering. The efficiency gap (EG) and the mean-median difference are the standard,
litigated one-number summaries of that asymmetry. They are a step past the raw ratio, but
NOT a resolution: a large EG can arise purely from geography (a party clustered in cities
packs itself). Only a redistricting ENSEMBLE (simulate many neutral maps, test whether the
enacted map is an outlier) separates intent from geography — a separate, larger project.

Design choice: EG is computed on the **2024 presidential two-party vote aggregated to each
district** (precinct returns joined to `precinct_district_map`), NOT the legislative vote.
Every precinct has a presidential vote, so this sidesteps uncontested / same-party-top-two
legislative races (severe in these states) and measures the *map's* geometry against one
consistent statewide baseline. NY uses 2020 (2024 presidential isn't loaded).

Metrics per district set (sign convention: POSITIVE = favors Democrats):
  - Efficiency gap, wasted-votes form:  EG = (wasted_R - wasted_D) / total_votes, where a
    winner wastes votes above 50% and a loser wastes all of them.
  - Efficiency gap, simplified form:    (seat_share_D - 0.5) - 2*(vote_share_D - 0.5).
  - Mean-median: mean(D district share) - median(D district share); ~0 = symmetric.
Rule of thumb: |EG| above ~8% (about two seats in a large chamber) is the level courts and
the literature (Stephanopoulos & McGhee 2015) have treated as a concern.

Read-only, aggregates only. Uses the ETL-built `precinct_district_map`, so it is not
standalone from a raw public extract.
    python scripts/diag_efficiency_gap.py
"""
from statistics import median

import duckdb

PARTY = """CASE
  WHEN cd.party_normalized ILIKE '%democrat%' THEN 'D'
  WHEN cd.party_normalized ILIKE '%republican%' OR cd.party_normalized ILIKE '%gop%' THEN 'R'
  ELSE 'O' END"""

# state -> (db, presidential general date). NY: 2024 not loaded -> 2020 proxy.
STATES = [("WA", "data/wa_statewide.duckdb", "2024-11-05"),
          ("NY", "data/ny_statewide.duckdb", "2020-11-03"),
          ("TX", "data/tx_statewide.duckdb", "2024-11-05"),
          ("ID", "data/id_statewide.duckdb", "2024-11-05")]
DISTRICT_COLS = ["congressional_district", "legislative_district", "senate_district"]


def district_pres(con, col, date):
    """[(d_votes, r_votes)] per district: 2024 presidential two-party vote aggregated to
    `col` via precinct_district_map. Excludes null districts and write-ins."""
    rows = con.execute(f"""
        SELECT dm.{col} district,
               SUM(CASE WHEN {PARTY}='D' THEN pr.votes ELSE 0 END) d,
               SUM(CASE WHEN {PARTY}='R' THEN pr.votes ELSE 0 END) r
        FROM precinct_results pr
        JOIN races ra ON ra.race_id = pr.race_id
        JOIN elections e ON e.election_id = ra.election_id
        JOIN candidates cd ON cd.candidate_id = pr.candidate_id
        JOIN precinct_district_map dm ON dm.precinct_id = pr.precinct_id
        WHERE e.election_date = DATE '{date}' AND ra.office ILIKE '%PRESIDENT%'
          AND COALESCE(cd.is_writein, FALSE) = FALSE
          AND dm.{col} IS NOT NULL AND TRIM(CAST(dm.{col} AS VARCHAR)) <> ''
        GROUP BY 1
    """).fetchall()
    return [(float(d), float(r)) for _dist, d, r in rows if (d or 0) + (r or 0) > 0]


def tx_house_pres():
    """TX's precinct_district_map is an empty shell, so House-district presidential vote
    comes from the on-disk TLC r206 report (the same source diag_tx_safe_seat_backfill and
    the safe-seat paper use for TX). Returns [(harris_D, trump_R)] per House district."""
    import diag_tx_safe_seat_backfill as txbf
    return [(float(hd), float(hr)) for hd, hr in txbf.r206_presidential().values()
            if (hd or 0) + (hr or 0) > 0]


def metrics(dr):
    """Efficiency gap (both forms) + mean-median from [(d,r)] per district.
    Sign convention: positive favors Democrats."""
    n = len(dr)
    tot = sum(d + r for d, r in dr)
    d_tot = sum(d for d, r in dr)
    wasted_d = wasted_r = 0.0
    d_seats = 0
    for d, r in dr:
        half = (d + r) / 2
        if d >= r:
            d_seats += 1
            wasted_d += d - half   # winner surplus
            wasted_r += r          # loser: all wasted
        else:
            wasted_r += r - half
            wasted_d += d
    eg_wasted = (wasted_r - wasted_d) / tot          # + favors D
    v_d = d_tot / tot                                # statewide D two-party share
    s_d = d_seats / n                                # D seat share
    eg_simple = (s_d - 0.5) - 2 * (v_d - 0.5)        # + favors D
    shares = [d / (d + r) for d, r in dr]
    mm = sum(shares) / n - median(shares)            # mean - median of D share
    return n, v_d, s_d, eg_wasted, eg_simple, mm


def fav(x):
    return f"{'D' if x >= 0 else 'R'}+{abs(x)*100:4.1f}%"


def main():
    print("Partisan asymmetry on the district map — presidential two-party vote by district")
    print("(sign: D+ favors Democrats, R+ favors Republicans; |EG|>~8% is the concern level)\n")
    hdr = (f"{'state':5} {'district set':22} {'n':>3} {'D vote%':>7} {'D seat%':>7} "
           f"{'EG(wasted)':>11} {'EG(simple)':>11} {'mean-med':>9}")
    print(hdr); print("-" * len(hdr))
    def row(st, label, dr, note=""):
        if len(dr) < 3:               # EG is meaningless on 1-2 districts (e.g. ID congress)
            return
        n, v_d, s_d, egw, egs, mm = metrics(dr)
        print(f"{st:5} {label:22} {n:>3} {v_d*100:6.1f}% {s_d*100:6.1f}% "
              f"{fav(egw):>11} {fav(egs):>11} {mm*100:+8.1f}{note}")

    for st, db, date in STATES:
        con = duckdb.connect(db, read_only=True)
        note = " [pres=2020]" if st == "NY" else ""
        for col in DISTRICT_COLS:
            try:
                dr = district_pres(con, col, date)
            except duckdb.Error:
                dr = []
            row(st, col, dr, note)
        con.close()
        if st == "TX":                # precinct_district_map empty -> House via r206 report
            row("TX", "house_district (r206)", tx_house_pres())

    print("\nASYMMETRY, NOT INTENT. A large EG is consistent with deliberate gerrymandering")
    print("OR a party's own geographic clustering; distinguishing them needs a redistricting")
    print("ensemble (simulate neutral maps, test the enacted map as an outlier). NY uses the")
    print("2020 presidential vote (2024 not loaded). Districts with <3 units are omitted.")


if __name__ == "__main__":
    main()
