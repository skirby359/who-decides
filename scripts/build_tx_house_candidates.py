"""Build the certified 2024 Texas House candidate list — the source that closes the
backfill-verification gap in docs/safe-seat-washington.md Appendix F.

WHY THIS EXISTS. The Texas Legislative Council's VTD returns omit uncontested races
entirely, at every stage: the 2024 general file carries 96 of 150 House districts, and
the party primaries omit them too (all 14 press-confirmed unopposed districts appear in
NEITHER 2024 primary, because those candidates were unopposed there as well). The TLC
dataset therefore structurally cannot see an uncontested race. Earlier revisions worked
around this by backfilling the 54 absent districts and imputing their holding party from
presidential lean — an imputation that proved wrong in 4 of the 14 districts where it
could be checked.

THE SOURCE. The Texas Secretary of State's election-night results service
(https://results.texas-election.com) publishes every race including uncontested ones,
with candidate name, party and votes. Read from there on 2026-07-27, it independently
confirms all 150 House districts, and its 54 single-candidate districts are exactly the
54 the TLC file omits — a complete, external verification of the backfill rather than the
partial press cross-check that preceded it. It also supplies the OBSERVED winning party,
replacing the presidential-lean imputation.

Note the SoS summary view lists the top two finishers per race, which is sufficient here:
a race showing one candidate had exactly one, and the winner is the leader. Races with
three or more candidates show only the top two, so this file is not a complete candidate
roster for contested seats — it is a complete record of the *seat universe*, the winner,
and the runner-up.

Usage:  python scripts/build_tx_house_candidates.py --from-extract <file>
        python scripts/build_tx_house_candidates.py            # uses the committed copy
Writes: data/raw/tx/2024_tx_house_candidates.csv
"""
from __future__ import annotations

import argparse
import csv
import os
import sys

OUT = os.path.join("data", "raw", "tx", "2024_tx_house_candidates.csv")
FIELDS = ["district", "n_candidates", "winner_party", "winner_name", "winner_votes",
          "runner_party", "runner_votes", "uncontested", "margin_pct"]


def parse(lines) -> list[dict]:
    rows = []
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        p = ln.split("|")
        if len(p) != 7:
            raise ValueError(f"expected 7 fields, got {len(p)}: {ln!r}")
        d, n, wp, wn, wv, rp, rv = p
        wv_i, rv_i = int(wv or 0), int(rv or 0)
        tot = wv_i + rv_i
        rows.append({
            "district": int(d),
            "n_candidates": int(n),
            "winner_party": wp,
            "winner_name": wn,
            "winner_votes": wv_i,
            "runner_party": rp,
            "runner_votes": rv_i,
            "uncontested": int(n) == 1,
            "margin_pct": None if int(n) == 1 or not tot
            else round(100.0 * (wv_i - rv_i) / tot, 2),
        })
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--from-extract", help="pipe-delimited extract to ingest")
    args = ap.parse_args(argv)

    if args.from_extract:
        with open(args.from_extract, encoding="utf-8") as fh:
            rows = parse(fh)
    elif os.path.exists(OUT):
        print(f"{OUT} already exists; pass --from-extract to rebuild it.")
        return 0
    else:
        print("ERROR: no extract supplied and no committed copy present.")
        return 1

    seen = {r["district"] for r in rows}
    missing = sorted(set(range(1, 151)) - seen)
    if missing:
        print(f"ERROR: districts missing from extract: {missing}")
        return 1

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: r["district"]))

    unc = [r for r in rows if r["uncontested"]]
    ud = sum(1 for r in unc if r["winner_party"] == "D")
    ur = sum(1 for r in unc if r["winner_party"] == "R")
    print(f"wrote {OUT}  ({len(rows)} districts)")
    print(f"  uncontested: {len(unc)}  ->  {ud} D / {ur} R  (OBSERVED, not imputed)")
    print(f"  contested  : {len(rows) - len(unc)}")
    nc = sum(1 for r in rows
             if r["uncontested"] or (r["margin_pct"] is not None and r["margin_pct"] >= 10))
    print(f"  not close (uncontested or >=10pt): {nc}/150 = {100.0*nc/150:.1f}%")
    wd = sum(1 for r in rows if r["winner_party"] == "D")
    print(f"  chamber won: {wd} D / {len(rows)-wd} R")
    ncd = sum(1 for r in rows if r["winner_party"] == "D"
              and (r["uncontested"] or (r["margin_pct"] is not None and r["margin_pct"] >= 10)))
    print(f"  not-close seats by winner: {ncd} D / {nc-ncd} R")
    return 0


if __name__ == "__main__":
    sys.exit(main())
