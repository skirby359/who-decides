"""Safe-Seat Washington — OBSERVED general-election competitiveness of partisan
legislative + congressional seats, 2016-2024 (even-year generals), computed from
precinct_results (not the forecast projection).

Unit = the SEAT (each race): State Representative Pos. 1, State Representative
Pos. 2, State Senator (those up that cycle), and U.S. Representative. For each
seat's general:
  - tally D vs R two-party votes (party via candidates.party_normalized);
  - UNCONTESTED  = a single candidate on the general ballot;
  - SAME-PARTY   = >=2 candidates but no cross-party (D-vs-D or R-vs-R) — WA's
                   top-two primary can send two same-party finalists, so the
                   general offers no major-party choice;
  - CROSS-PARTY  = both a D and an R present -> two-party margin |D-R|/(D+R),
                   banded Tossup<5 / Lean5-10 / Likely10-20 / Solid>=20.
"NON-COMPETITIVE" = uncontested + same-party + (cross-party with margin >=10).

Also: a primary->general turnout ratio (votes cast in the deciding round),
contrasting safe vs competitive seats — the "the primary decides" check.
"""
import duckdb
import json

DB = "data/wa_statewide.duckdb"
OUT = "reports/safe_seat_wa.json"

# even-year generals carry legislative + congressional partisan seats
GENERAL_YEARS = [2016, 2018, 2020, 2022, 2024]
OFFICES = ("State Representative Pos. 1", "State Representative Pos. 2",
           "State Senator", "U.S. Representative")

PARTY_CASE = """CASE
  WHEN party_normalized ILIKE '%democrat%' THEN 'D'
  WHEN party_normalized ILIKE '%republican%' OR party_normalized ILIKE '%gop%' THEN 'R'
  ELSE 'O' END"""


def band(m):
    if m < 5: return "Tossup"
    if m < 10: return "Lean"
    if m < 20: return "Likely"
    return "Solid"


def seat_table(c, year, etype):
    """Per-seat D/R/other vote totals for one election (general or primary)."""
    return c.execute(f"""
        WITH cand AS (
            SELECT r.race_id, r.office,
                   regexp_extract(r.race_name, 'DISTRICT ([0-9]+)', 1) AS district,
                   cd.candidate_id,
                   ({PARTY_CASE}) AS pty
            FROM races r
            JOIN elections e ON e.election_id = r.election_id
            JOIN candidates cd ON cd.race_id = r.race_id
            WHERE e.election_type = '{etype}'
              AND date_part('year', e.election_date) = {year}
              AND r.office IN {OFFICES!r}
              AND COALESCE(cd.is_writein, FALSE) = FALSE
        ),
        votes AS (
            SELECT cand.race_id, cand.office, cand.district, cand.candidate_id, cand.pty,
                   SUM(pr.votes) v
            FROM cand JOIN precinct_results pr ON pr.candidate_id = cand.candidate_id
            GROUP BY 1,2,3,4,5
        )
        SELECT race_id, office, district,
               COUNT(*) FILTER (WHERE v > 0) ncand,
               SUM(v) FILTER (WHERE pty='D') d,
               SUM(v) FILTER (WHERE pty='R') r,
               SUM(v) total
        FROM votes GROUP BY 1,2,3
    """).fetchall()


def classify(rows):
    cats = {"uncontested": 0, "same_party": 0, "Tossup": 0, "Lean": 0,
            "Likely": 0, "Solid": 0}
    d_safe = r_safe = 0
    detail = []
    for race_id, office, district, ncand, d, r, total in rows:
        d = float(d or 0); r = float(r or 0)
        if ncand <= 1:
            cat = "uncontested"
        elif d == 0 or r == 0:
            cat = "same_party"
        else:
            cat = band(abs(d - r) / (d + r) * 100)
        cats[cat] += 1
        # which party holds it (for neutral both-sides framing)
        if cat in ("uncontested", "same_party", "Likely", "Solid"):
            if d >= r:
                d_safe += 1
            else:
                r_safe += 1
        detail.append((race_id, office, district, cat, d, r, total))
    n = sum(cats.values())
    noncomp = cats["uncontested"] + cats["same_party"] + cats["Likely"] + cats["Solid"]
    return cats, n, noncomp, d_safe, r_safe, detail


def main():
    c = duckdb.connect(DB, read_only=True)
    out = {}
    print("Safe-Seat Washington — OBSERVED general competitiveness of partisan")
    print("legislative + congressional SEATS, by even-year general\n")
    hdr = (f"{'year':5} {'seats':>5} | {'uncont':>6} {'same-pty':>8} {'Tossup':>6} "
           f"{'Lean':>5} {'Likely':>6} {'Solid':>5} | {'non-comp':>8} {'%':>6}")
    print(hdr); print("-" * len(hdr))
    for y in GENERAL_YEARS:
        rows = seat_table(c, y, "general")
        cats, n, noncomp, d_safe, r_safe, _ = classify(rows)
        print(f"{y:5} {n:>5} | {cats['uncontested']:>6} {cats['same_party']:>8} "
              f"{cats['Tossup']:>6} {cats['Lean']:>5} {cats['Likely']:>6} {cats['Solid']:>5} | "
              f"{noncomp:>8} {noncomp/n*100:5.1f}%")
        out[y] = {"seats": n, "cats": cats, "noncompetitive": noncomp,
                  "noncomp_pct": round(noncomp / n * 100, 1),
                  "d_safe": d_safe, "r_safe": r_safe}

    # focus year detail
    fy = 2024
    rows = seat_table(c, fy, "general")
    cats, n, noncomp, d_safe, r_safe, detail = classify(rows)
    print(f"\n{fy} detail: {n} seats, {noncomp} non-competitive ({noncomp/n*100:.1f}%); "
          f"of the safe seats, {d_safe} lean D / {r_safe} lean R (both sides).")
    comp = [d for d in detail if d[3] in ("Tossup", "Lean")]
    print(f"  the {len(comp)} genuinely competitive (<10pt) seats:")
    for race_id, office, district, cat, d, r, total in sorted(comp, key=lambda x: abs(x[4]-x[5])/(x[4]+x[5])):
        m = abs(d - r) / (d + r) * 100
        lean = "D" if d > r else "R"
        print(f"     LD/CD {district:>3} {office:28} {cat:6} {lean}+{m:4.1f}")

    # ---- primary -> general turnout ratio (the deciding-round check) ----
    # For each seat, total votes in the general vs the same office+district primary
    # that year. Safe seats: the primary is the operative round.
    print("\nPrimary vs general participation (total votes cast in the seat's race):")
    for y in [2024, 2022]:
        gen = {(o, dist): tot for _, o, dist, _, _, _, tot in seat_table(c, y, "general")}
        pri = {}
        for _, o, dist, _, _, _, tot in seat_table(c, y, "primary"):
            pri[(o, dist)] = (pri.get((o, dist), 0) or 0) + float(tot or 0)
        gcats = {(d[1], d[2]): d[3] for d in classify(seat_table(c, y, "general"))[5]}
        safe_ratios, comp_ratios = [], []
        for k, g in gen.items():
            if k in pri and g:
                ratio = pri[k] / float(g)
                if gcats.get(k) in ("Tossup", "Lean"):
                    comp_ratios.append(ratio)
                else:
                    safe_ratios.append(ratio)
        def med(xs):
            xs = sorted(xs)
            return xs[len(xs) // 2] if xs else float("nan")
        print(f"  {y}: median primary/general vote ratio — "
              f"safe seats {med(safe_ratios):.2f} (n={len(safe_ratios)}), "
              f"competitive {med(comp_ratios):.2f} (n={len(comp_ratios)})")
        out.setdefault("primary_general", {})[y] = {
            "safe_median_ratio": round(med(safe_ratios), 3),
            "competitive_median_ratio": round(med(comp_ratios), 3),
            "n_safe": len(safe_ratios), "n_comp": len(comp_ratios)}

    c.close()
    json.dump(out, open(OUT, "w"), indent=2, default=str)
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
