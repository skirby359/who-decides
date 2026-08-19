"""Safe-Seat — OBSERVED LOWER-CHAMBER competitiveness across WA / NY / TX / ID.

The four-state observed counterpart to scripts/diag_safe_seat_wa.py. The unit is
the LOWER-chamber state-legislative seat — the one chamber that is FULLY up every
cycle in all four states (WA House 98 = 49 LD x 2; NY Assembly 150; TX House 150;
ID House 70 = 35 x 2), so the cross-state count is complete and apples-to-apples
(upper chambers stagger in WA/TX, so they are reported separately, not pooled).

Method (party-primary states; WA top-two folds in):
  - Contest structure (has-D / has-R) from the candidates table.
  - NO_MAJOR_CHOICE = not (hasD and hasR): no D-vs-R option (uncontested / one-party /
    WA same-party top-two).
  - else two-party margin |D-R|/(D+R) from precinct_results, banded
    Tossup<5 / Lean5-10 / Likely10-20 / Solid>=20.
  NON-COMPETITIVE = no_major_choice + Likely + Solid.

TX BACKFILL: the TLC VTD returns omit uncontested races, so only 96/150 TX House
districts appear in the warehouse. scripts/diag_tx_safe_seat_backfill.py completes
TX to 150 (the 54 absent seats are uncontested -> no_major_choice; holding party by
2024 presidential lean from the on-disk TLC r206 report). This script imports that
completion so the TX row is the full 150.

!! THREE CELLS HERE ARE SUPERSEDED — do not quote them (2026-07-28; NY added 2026-08-10) !!

  * The WA row (88.8%) reads `precinct_results`, where King County is largely absent
    from the 2016/2018 statewide precinct files, AND scores every no-major-choice seat
    as non-competitive regardless of margin. Both were corrected in the paper. WA's
    published figure is **87.8%** from `diag_seat_competition.py` on the certified
    statewide summaries. The definition above also conflates the paper's two dimensions:
    a CONTESTED same-party general decided by under 10 points is "close" in the paper
    and "non-competitive" here. `diag_safe_seat_robustness.py` section (3) measures
    whether that shortcut changes any comparison state's answer — it does not (0 seats),
    but the WA cell differs for the data reason regardless.
  * The TX safe D/R split (51/90) uses holding party IMPUTED from presidential lean.
    That imputation is retired: it was wrong in 5 of 54 backfilled seats. The observed
    split from certified returns is **56 D / 85 R** — see
    `diag_tx_backfill_verification.py` and `diag_safe_seat_party_ratio.py`.

  * The NY row runs on the 149 districts the loaded returns carry, not the chamber's 150.
    Assembly District 23 is supplied from the certified NYSBOE contest
    (`docs/reference/ny_ad23_2022.csv`) and was decided by **0.046 points**, so it is close
    at every threshold: the not-close COUNT is unchanged and only the denominator moves.
    The published figure is **88.0%** on 150, not the 88.6% printed here. Every New York
    threshold cell in Appendix E rests on that denominator.

The ID row is current. This script is retained because the paper's four-state table cites it,
and because the earlier published numbers stay reproducible for audit.

*(The NY bullet and the NY row label were added 2026-08-10, safe-seat rounds 9 and 10. This
docstring previously read "The NY and ID rows … are current", and the row carried no label,
while Appendix C of the paper claimed "the superseded cells are labelled as such in those
scripts' own output". That was true of WA and TX and false of NY — a claim about coverage the
coverage did not support.)*
"""
import os
import sys

import duckdb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import diag_tx_safe_seat_backfill as txbf  # noqa: E402

PARTY = """CASE
  WHEN cd.party_normalized ILIKE '%democrat%' THEN 'D'
  WHEN cd.party_normalized ILIKE '%republican%' OR cd.party_normalized ILIKE '%gop%' THEN 'R'
  ELSE 'O' END"""

# state -> (db, general date, LOWER-chamber office predicate, UPPER-chamber predicate)
STATES = [
    ("WA", "data/wa_statewide.duckdb", "2024-11-05",
     "r.office IN ('State Representative Pos. 1','State Representative Pos. 2')",
     "r.office = 'State Senator'"),
    ("NY", "data/ny_statewide.duckdb", "2022-11-08",
     "r.office ILIKE '%ASSEMBLY DISTRICT%'", "r.office ILIKE '%SENATE DISTRICT%'"),
    ("TX", "data/tx_statewide.duckdb", "2024-11-05",
     "r.office ILIKE '%HOUSE DISTRICT%'", "r.office ILIKE '%SENATE DISTRICT%'"),
    ("ID", "data/id_statewide.duckdb", "2024-11-05",
     "(REGEXP_MATCHES(r.office, '^REPRESENTATIVE DISTRICT [0-9]+ SEAT [AB]$') OR REGEXP_MATCHES(r.office, '^LEGISLATIVE DISTRICT [0-9]+ ST REP [AB]$'))",
     "(REGEXP_MATCHES(r.office, '^SENATOR DISTRICT [0-9]+$') OR REGEXP_MATCHES(r.office, '^LEGISLATIVE DISTRICT [0-9]+ ST SEN$'))"),
]
CHAMBER_NAME = {"WA": ("House", "Senate"), "NY": ("Assembly", "Senate"),
                "TX": ("House", "Senate"), "ID": ("House", "Senate")}


def band(m):
    if m < 5: return "Tossup"
    if m < 10: return "Lean"
    if m < 20: return "Likely"
    return "Solid"


def count(db, date, pred):
    c = duckdb.connect(db, read_only=True)
    rows = c.execute(f"""
        WITH seat AS (
            SELECT r.race_id,
                   MAX(CASE WHEN {PARTY}='D' THEN 1 ELSE 0 END) hasD,
                   MAX(CASE WHEN {PARTY}='R' THEN 1 ELSE 0 END) hasR
            FROM races r JOIN elections e ON e.election_id=r.election_id
            JOIN candidates cd ON cd.race_id=r.race_id
            WHERE e.election_date=DATE '{date}' AND {pred}
              AND COALESCE(cd.is_writein,FALSE)=FALSE GROUP BY 1),
        votes AS (
            SELECT r.race_id,
                   SUM(CASE WHEN {PARTY}='D' THEN pr.votes ELSE 0 END) d,
                   SUM(CASE WHEN {PARTY}='R' THEN pr.votes ELSE 0 END) r
            FROM races r JOIN elections e ON e.election_id=r.election_id
            JOIN candidates cd ON cd.race_id=r.race_id
            JOIN precinct_results pr ON pr.candidate_id=cd.candidate_id
            WHERE e.election_date=DATE '{date}' AND {pred}
              AND COALESCE(cd.is_writein,FALSE)=FALSE GROUP BY 1)
        SELECT s.hasD, s.hasR, COALESCE(v.d,0) d, COALESCE(v.r,0) r
        FROM seat s LEFT JOIN votes v USING (race_id)
    """).fetchall()
    c.close()
    cats = {"no_major_choice": 0, "Tossup": 0, "Lean": 0, "Likely": 0, "Solid": 0}
    d_safe = r_safe = 0
    for hasD, hasR, d, r in rows:
        d = float(d or 0); r = float(r or 0)
        cat = "no_major_choice" if (not (hasD and hasR) or d + r == 0) else band(abs(d - r) / (d + r) * 100)
        cats[cat] += 1
        if cat in ("no_major_choice", "Likely", "Solid"):
            d_safe, r_safe = (d_safe + 1, r_safe) if d >= r else (d_safe, r_safe + 1)
    return cats, d_safe, r_safe


def summarize(cats, d_safe, r_safe):
    n = sum(cats.values())
    noncomp = cats["no_major_choice"] + cats["Likely"] + cats["Solid"]
    return n, noncomp, cats["Tossup"] + cats["Lean"], d_safe, r_safe


def main():
    print("OBSERVED LOWER-CHAMBER competitiveness (fully up every cycle in all four)\n")
    hdr = (f"{'st':3} {'chamber':9} {'gen':10} {'seats':>5} | {'no-choice':>9} {'Tossup':>6} "
           f"{'Lean':>5} {'Likely':>6} {'Solid':>5} | {'non-comp':>8} {'%':>6} {'safe D/R':>10}")
    print(hdr); print("-" * len(hdr))
    for st, db, date, lower, _upper in STATES:
        cats, d_safe, r_safe = count(db, date, lower)
        if st == "TX":  # complete 96 -> 150 with the uncontested backfill
            dbres = txbf.db_house_results()
            pres = txbf.r206_presidential()
            cats = {"no_major_choice": 0, "Tossup": 0, "Lean": 0, "Likely": 0, "Solid": 0}
            d_safe = r_safe = 0
            for dist in range(1, txbf.HOUSE_TOTAL + 1):
                if dist in dbres:
                    cat, d, r = dbres[dist]; lean_d = d >= r
                else:
                    cat = "no_major_choice"; hd, hr = pres.get(dist, (0, 0)); lean_d = hd >= hr
                cats[cat] += 1
                if cat in ("no_major_choice", "Likely", "Solid"):
                    d_safe, r_safe = (d_safe + 1, r_safe) if lean_d else (d_safe, r_safe + 1)
        n, noncomp, comp, ds, rs = summarize(cats, d_safe, r_safe)
        note = {"TX": "  (backfilled to 150; safe D/R SUPERSEDED -> 56/85 observed)",
                "WA": "  (% SUPERSEDED -> 87.8% certified; safe D/R -> 53/33)",
                # Added 2026-08-10 (safe-seat round 9/10). This row was UNLABELLED while
                # Appendix C claimed "the superseded cells are labelled as such in those
                # scripts' own output" — true of WA and TX, false of NY. The chamber has 150
                # districts; the loaded returns carry 149, and AD-23 is supplied from the
                # certified NYSBOE contest in docs/reference/ny_ad23_2022.csv. AD-23 was
                # decided by 0.046 points, so it is CLOSE at every threshold: the not-close
                # count is unchanged and only the denominator moves.
                "NY": "  (149 = loaded returns; SUPERSEDED -> 150 with AD-23, 88.0%)"}.get(st, "")
        print(f"{st:3} {CHAMBER_NAME[st][0]:9} {date:10} {n:>5} | {cats['no_major_choice']:>9} "
              f"{cats['Tossup']:>6} {cats['Lean']:>5} {cats['Likely']:>6} {cats['Solid']:>5} | "
              f"{noncomp:>8} {noncomp/n*100:5.1f}% {f'{ds}/{rs}':>10}{note}")

    print("\nUpper chambers (NY/ID fully up; WA/TX staggered — partial, not pooled above):")
    for st, db, date, _lower, upper in STATES:
        cats, d_safe, r_safe = count(db, date, upper)
        n, noncomp, comp, ds, rs = summarize(cats, d_safe, r_safe)
        if n:
            stag = " [staggered: seats up only]" if st in ("WA", "TX") else ""
            print(f"  {st} {CHAMBER_NAME[st][1]}: {noncomp}/{n} non-comp ({noncomp/n*100:.0f}%), "
                  f"{comp} competitive{stag}")

    print("\nNon-competitive = no-major-choice + Likely + Solid (>=10pt). "
          "Competitive = Tossup+Lean (<10pt).")
    print("NB: that definition scores a no-major-choice seat as non-competitive at ANY "
          "margin,\nwhich is NOT the paper's Dimension 1 — a contested same-party general "
          "under 10 pts is\nCLOSE in the paper. It changes no comparison state's answer "
          "(0 such seats; see\ndiag_safe_seat_robustness.py section 3), but the WA cell "
          "above is superseded for a\nseparate DATA reason: use 87.8% from "
          "diag_seat_competition.py.")
    print("TX House: actual-race contestation (94% non-comp) is WORSE than the district "
          "presidential lean (84% >=10pt safe). The gap compares two AGGREGATE shares and "
          "does NOT observe who filed: non-entry is one mechanism consistent with it, and "
          "incumbency, candidate quality, spending, differential turnout and office-specific "
          "ticket-splitting are others. (Was 'parties leave winnable seats uncontested' until "
          "2026-08-10 — the candidate-non-entry reading the paper's Appendix E withdrew as "
          "'more than the statistic supports'.) "
          "See scripts/diag_tx_safe_seat_backfill.py.")


if __name__ == "__main__":
    main()
