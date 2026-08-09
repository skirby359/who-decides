"""Does money move votes? The WASHINGTON LEGISLATIVE directional test.

The state-legislative counterpart to ``diag_ie_vs_margin.py``, which runs the
same design on the 34 FEC-attributed U.S. House district-cycles. Same outcome,
same estimator, different money:

  residual_pp        = actual_dem_pct - model predicted_dem_pct   (per race)
  net_pro_dem_IE_$M  = (For a Democrat + Against a Republican)
                       - (For a Republican + Against a Democrat)  (per race)

**Why this script exists.** The money paper stated that Washington's $70.6M of
legislative independent expenditure "cannot enter a directional test at all"
because the support/oppose flag is empty on all but 5 of 4,456 rows. That was a
fact about our ETL, not about Washington. The PDC publishes direction in the
**C6.3 "Identified Entities"** section of form C-6, which ``load_pdc_ie_targets``
now reads into ``pdc_ie_targets``: 4,653 legislative rows, $51,723,243.45,
candidate name / filer id / jurisdiction / direction on 100% of them. See
``docs/pdc-c6-direction-audit.md``.

**Three properties of the PDC data this design has to respect**, none of which
apply to the FEC panel:

1. **``portion_of_amount`` apportions a REPORT, not a line.** C6.3 rows carry no
   expenditure id; the only link to the C6.2 itemized rows is ``report_number``.
   It reconciles - per report the portions sum to the expenditures to the cent
   on 2,197 of 2,210 reports - so the totals are trustworthy, but the unit is
   the report. Never sum ``portion_of_amount`` with ``expenditure_amount``.
2. **Electioneering Communication is 74.8% of the directional dollars.** It names
   a candidate without necessarily advocating for or against them, so its
   ``for_or_against`` is not express advocacy. It is also directionally
   *opposite*: express advocacy is 69% For, electioneering is 61% Against.
   Pooling them would invert the panel's balance. **This script reports the two
   panels separately and treats express advocacy as primary.**
3. **The outcome is a single race, so the money must be too.** The backtest
   scores one contest per legislative district - State Representative Pos. 1 by
   preference, then Pos. 2, then Senator. But C6.3's ``candidate_jurisdiction``
   resolves only to "LEG DISTRICT nn - HOUSE|SENATE", which does not separate the
   two House positions. Attributing a district's whole IE to one of its three
   seats would be a mismatch, not a measurement. So the primary panel is
   **race-matched**: IE counts only where the named candidate is on the ballot in
   the contest the residual scores. The district-aggregate version is reported
   beside it as a sensitivity, explicitly labelled as the mismatched one.

Endogeneity is the same here as there: outside money is targeted at expected
closeness, not assigned at random (Jacobson 1990). A signed estimate from this
design is not causal with or without an instrument. The interval is the result.

Reproducible, public-record inputs only (PDC C-6 filings + SoS results). No PII,
no voter file.

Usage:
    python scripts/diag_pdc_ie_vs_margin.py
    python scripts/diag_pdc_ie_vs_margin.py --json out.json
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys

import duckdb

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, os.path.dirname(__file__))

from config.districts import get_profile  # noqa: E402

DB = "data/wa_statewide.duckdb"

# Below this, inference is withheld and only a descriptive slope is shown.
# Same floor as the federal script, for the same reason: a slope on n<10 is a
# coin flip dressed as a coefficient.
MIN_N_FOR_SLOPE = 10

# The C6.3 report_type values that constitute EXPRESS ADVOCACY. The third value,
# "Electioneering Communication", identifies a candidate without necessarily
# advocating, and is 74.8% of the legislative directional dollars.
EXPRESS_ADVOCACY = ("Independent Expenditure", "Independent Expenditure Ad")

CYCLES = (2018, 2020, 2022, 2024)

_JURIS = re.compile(r"^LEG DISTRICT\s+0*(\d+)\s*-\s*(HOUSE|SENATE)$")


# ---------------------------------------------------------------------------
# Panel construction
# ---------------------------------------------------------------------------

def _norm_name(name: str) -> str:
    """Fold a candidate name to a comparable key.

    PDC and the SoS both publish "First Last", but differ on middle names,
    nicknames in quotes, suffixes and punctuation. Reduce to
    (last, first-initial), which is what the repo's other name joins use --
    with the caveat that it is a WEAK key. It is acceptable here only because
    the comparison is already scoped to one race in one cycle, where a
    collision would require two same-initial same-surname candidates in the
    same contest.
    """
    s = re.sub(r'"[^"]*"', " ", (name or "").upper())
    s = re.sub(r"\b(JR|SR|II|III|IV)\b\.?", " ", s)
    s = re.sub(r"[^A-Z\s]", " ", s)
    toks = [t for t in s.split() if len(t) > 1]
    if len(toks) < 2:
        return " ".join(toks)
    return f"{toks[-1]}|{toks[0][0]}"


def load_targets(conn, express_only: bool) -> list[dict]:
    """C6.3 legislative target rows, parsed to (cycle, district, chamber)."""
    where_type = ""
    if express_only:
        placeholders = ",".join(f"'{t}'" for t in EXPRESS_ADVOCACY)
        where_type = f"AND report_type IN ({placeholders})"
    rows = conn.execute(f"""
        SELECT election_year, candidate_jurisdiction, candidate_name,
               candidate_party, for_or_against, portion_of_amount, report_type
        FROM pdc_ie_targets
        WHERE candidate_office_type = 'Legislative'
          AND election_year IN ({",".join(str(c) for c in CYCLES)})
          AND for_or_against IN ('For', 'Against')
          {where_type}
    """).fetchall()

    out, unparsed = [], 0
    for year, juris, name, party, direction, amount, rtype in rows:
        m = _JURIS.match((juris or "").strip())
        if not m:
            unparsed += 1
            continue
        out.append({
            "cycle": int(year),
            "district_id": f"ld{int(m.group(1)):02d}",
            "chamber": m.group(2),
            "name": name or "",
            "name_key": _norm_name(name or ""),
            "pdc_party": (party or "").strip().upper(),
            "direction": direction,
            "amount": float(amount or 0),
            "report_type": rtype,
        })
    if unparsed:
        print(f"  [note] {unparsed} legislative row(s) had an unparseable "
              f"jurisdiction and are excluded.")
    return out


def ballot_parties(conn) -> dict[tuple[int, str, str], str]:
    """(cycle, race_name, name_key) -> party, from the SoS candidate roster.

    The filing's own ``candidate_party`` is used first; this is the fallback and
    the cross-check. Reads ``v_candidates`` so party overrides apply.
    """
    rows = conn.execute("""
        SELECT EXTRACT(YEAR FROM e.election_date) AS yr,
               r.race_name, c.candidate_name, c.party_normalized
        FROM v_candidates c
        JOIN races r  ON r.race_id = c.race_id
        JOIN elections e ON e.election_id = r.election_id
        WHERE e.election_type = 'general'
          AND r.race_name LIKE '%LEGISLATIVE DISTRICT%'
          AND c.party_normalized IN ('Democratic', 'Republican')
    """).fetchall()
    return {(int(y), rn, _norm_name(cn)): p for y, rn, cn, p in rows}


def scored_race(conn, district_id: str, year: int):
    """The contest the backtest residual actually scores, plus the residual.

    Returns (info dict, None) or (None, reason).
    """
    from backtest_model import run_single_backtest
    try:
        r = run_single_backtest(conn, get_profile(district_id), year, "Democratic")
    except Exception as e:  # noqa: BLE001
        return None, f"forecast error: {e}"
    if r.get("skipped"):
        return None, r.get("skip_reason", "skipped")
    if "actual_dem_pct" not in r or "predicted_dem_pct" not in r:
        return None, "no actual (unscorable)"
    return {
        "residual_pp": round(float(r["actual_dem_pct"]) - float(r["predicted_dem_pct"]), 2),
        "actual_dem_pct": float(r["actual_dem_pct"]),
        "predicted_dem_pct": float(r["predicted_dem_pct"]),
        "actual_margin": float(r.get("actual_margin", 0.0)),
        # `race_used` is the contest query_actual_results actually scored --
        # State Representative Pos. 1 by preference, then Pos. 2, then Senator.
        # Getting this key wrong would silently match zero IE rows and report an
        # empty panel as a null result.
        "race_name": r.get("race_used") or "",
    }, None


def _chamber_of(race_name: str) -> str:
    low = (race_name or "").lower()
    if "senator" in low:
        return "SENATE"
    if "representative" in low:
        return "HOUSE"
    return ""


def build_panel(conn, express_only: bool) -> dict:
    """Assemble race-matched and district-aggregate panels."""
    targets = load_targets(conn, express_only)
    roster = ballot_parties(conn)

    cells = sorted({(t["cycle"], t["district_id"]) for t in targets})
    by_cell: dict[tuple[int, str], list[dict]] = {}
    for t in targets:
        by_cell.setdefault((t["cycle"], t["district_id"]), []).append(t)

    matched, aggregate, skipped = [], [], []
    unresolved_party = 0.0
    total_seen = 0.0

    for cycle, did in cells:
        info, why = scored_race(conn, did, cycle)
        if info is None:
            skipped.append({"cycle": cycle, "district_id": did, "reason": why})
            continue

        target_chamber = _chamber_of(info["race_name"])
        pro_d_m = pro_r_m = 0.0        # race-matched
        pro_d_a = pro_r_a = 0.0        # district-aggregate
        n_matched = 0

        for t in by_cell[(cycle, did)]:
            total_seen += t["amount"]
            # Party: the filing's own value first, the ballot roster second.
            party = ""
            if t["pdc_party"].startswith("DEMOCRAT"):
                party = "Democratic"
            elif t["pdc_party"].startswith("REPUBLICAN"):
                party = "Republican"
            else:
                party = roster.get((cycle, info["race_name"], t["name_key"]), "")
            if party not in ("Democratic", "Republican"):
                unresolved_party += t["amount"]
                continue

            pro_dem = ((party == "Democratic" and t["direction"] == "For")
                       or (party == "Republican" and t["direction"] == "Against"))
            if pro_dem:
                pro_d_a += t["amount"]
            else:
                pro_r_a += t["amount"]

            # Race-matched: the named candidate must be on the ballot in the
            # contest the residual scores. This is what stops Senate money being
            # attributed to a House Pos. 1 residual.
            on_ballot = (cycle, info["race_name"], t["name_key"]) in roster
            if on_ballot and t["chamber"] == target_chamber:
                n_matched += 1
                if pro_dem:
                    pro_d_m += t["amount"]
                else:
                    pro_r_m += t["amount"]

        row = {
            "cycle": cycle, "district_id": did,
            "race_name": info["race_name"],
            "residual_pp": info["residual_pp"],
            "actual_margin": info["actual_margin"],
            "n_matched_rows": n_matched,
            # A Senate contest is the ONLY cell type where C6.3's granularity
            # matches the outcome exactly: there is one Senate seat per district
            # per cycle, so "LEG DISTRICT nn - SENATE" money maps 1:1 to the race
            # the residual scores. House money cannot be split between Pos. 1 and
            # Pos. 2, so a House cell always involves an attribution choice.
            "is_senate": target_chamber == "SENATE",
        }
        aggregate.append({**row, "pro_dem": pro_d_a, "pro_rep": pro_r_a,
                          "net_m": (pro_d_a - pro_r_a) / 1e6,
                          "total_m": (pro_d_a + pro_r_a) / 1e6})
        if n_matched:
            matched.append({**row, "pro_dem": pro_d_m, "pro_rep": pro_r_m,
                            "net_m": (pro_d_m - pro_r_m) / 1e6,
                            "total_m": (pro_d_m + pro_r_m) / 1e6})

    return {"matched": matched, "aggregate": aggregate, "skipped": skipped,
            "unresolved_party": unresolved_party, "total_seen": total_seen,
            "n_target_rows": len(targets)}


# ---------------------------------------------------------------------------
# Estimation (identical to diag_ie_vs_margin.py, deliberately)
# ---------------------------------------------------------------------------

def ols_slope(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return 0.0, my, 0.0
    slope = sxy / sxx
    return slope, my - slope * mx, sxy / math.sqrt(sxx * syy)


def bootstrap_slope_ci(xs, ys, iters=5000, seed=12345):
    import random
    rng = random.Random(seed)
    n = len(xs)
    idx = list(range(n))
    slopes = []
    for _ in range(iters):
        samp = [rng.choice(idx) for _ in range(n)]
        s, _, _ = ols_slope([xs[i] for i in samp], [ys[i] for i in samp])
        slopes.append(s)
    slopes.sort()
    return slopes[int(0.025 * iters)], slopes[int(0.975 * iters)]


# A cell carrying less than this in total directional IE is, for regression
# purposes, a zero. Reporting n=127 when 100 of those cells sit at $0 overstates
# the panel: the slope is identified only by the cells with variation in x. The
# federal panel has the same problem and states it ("15 attracted any material
# independent expenditure"); so must this one.
MATERIAL_IE = 25_000.0


def estimate(rows, label):
    n = len(rows)
    material = [r for r in rows if r["total_m"] * 1e6 >= MATERIAL_IE]
    print(f"\n{label}  (n={n})")
    if n:
        print(f"  cells with >= ${MATERIAL_IE:,.0f} total directional IE: "
              f"{len(material)} of {n}  "
              f"({100 * len(material) / n:.0f}%)")
    if n < 3:
        print("  too few cells to estimate.")
        return {"n": n, "inference": "none"}
    xs = [r["net_m"] for r in rows]
    ys = [r["residual_pp"] for r in rows]
    slope, _, rho = ols_slope(xs, ys)
    if n < MIN_N_FOR_SLOPE:
        print(f"  [DESCRIPTIVE ONLY] slope {slope:+.3f} pp per $1M net pro-Dem IE, "
              f"Pearson r={rho:+.3f}. Sign can flip on one race at this n.")
        return {"n": n, "inference": "withheld", "slope": slope, "pearson_r": rho}
    lo, hi = bootstrap_slope_ci(xs, ys)
    crosses = lo <= 0 <= hi
    print(f"  slope    = {slope:+.3f} pp per $1M net pro-Dem IE")
    print(f"  95% boot = [{lo:+.3f}, {hi:+.3f}]  "
          f"{'(crosses 0 - cannot reject no effect)' if crosses else '(excludes 0)'}")
    print(f"  Pearson r= {rho:+.3f}")

    out = {"n": n, "n_material": len(material), "inference": "reported",
           "slope": slope, "ci": [lo, hi], "pearson_r": rho,
           "crosses_zero": crosses}

    # Re-estimate on the cells that actually carry money. If the two disagree,
    # the full-panel slope is being set by the zero mass rather than by any
    # money-outcome relationship, and that is worth knowing before it is quoted.
    if len(material) >= 3:
        mxs = [r["net_m"] for r in material]
        mys = [r["residual_pp"] for r in material]
        ms, _, mr = ols_slope(mxs, mys)
        if len(material) >= MIN_N_FOR_SLOPE:
            mlo, mhi = bootstrap_slope_ci(mxs, mys)
            print(f"  -- material cells only (n={len(material)}): "
                  f"slope {ms:+.3f}, 95% boot [{mlo:+.3f}, {mhi:+.3f}], r={mr:+.3f}")
            out["material"] = {"n": len(material), "slope": ms,
                               "ci": [mlo, mhi], "pearson_r": mr}
        else:
            print(f"  -- material cells only (n={len(material)}): "
                  f"slope {ms:+.3f}, r={mr:+.3f}  [DESCRIPTIVE, below n={MIN_N_FOR_SLOPE}]")
            out["material"] = {"n": len(material), "slope": ms, "pearson_r": mr}

    # Leverage: does one cell carry the estimate? The federal panel's placebo
    # reversed sign on a single deletion, and that is the reason its numbers
    # "describe individual contests rather than a relationship".
    if n >= 4:
        worst_delta, worst_cell = 0.0, None
        for i in range(n):
            s_i, _, _ = ols_slope(xs[:i] + xs[i + 1:], ys[:i] + ys[i + 1:])
            if abs(s_i - slope) > abs(worst_delta):
                worst_delta, worst_cell = s_i - slope, rows[i]
        flips = (slope > 0) != (slope + worst_delta > 0)
        print(f"  -- most influential cell: {worst_cell['district_id']}/"
              f"{str(worst_cell['cycle'])[2:]} moves the slope to "
              f"{slope + worst_delta:+.3f}"
              f"{'  <-- SIGN FLIPS on one deletion' if flips else ''}")
        out["leverage"] = {"cell": f"{worst_cell['district_id']}/{worst_cell['cycle']}",
                           "slope_without": slope + worst_delta,
                           "sign_flips_on_one_deletion": flips}
    return out


# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", dest="json_out", default=None,
                    help="write the result dict to this path")
    ap.add_argument("--cells-csv", dest="cells_csv", default=None,
                    help="write the per-cell panel to this path. This is the "
                         "reproduction artifact the paper verifier re-derives "
                         "from — it pins the CELLS, not the coefficients, so a "
                         "verifier run recomputes the slope rather than reading "
                         "back an answer that could have gone stale.")
    args = ap.parse_args()

    conn = duckdb.connect(DB, read_only=True)
    n_targets = conn.execute("SELECT COUNT(*) FROM pdc_ie_targets").fetchone()[0]
    if not n_targets:
        print("pdc_ie_targets is EMPTY. Load it first:\n"
              "  python main.py load --district ld01 --pdc-ie-targets")
        conn.close()
        return 1

    print("=" * 78)
    print("WA LEGISLATIVE directional test - net PDC IE advantage vs model residual")
    print("=" * 78)

    result = {}
    cells_out: list[dict] = []
    for express_only, label in ((True, "EXPRESS ADVOCACY ONLY (primary)"),
                                (False, "ALL DIRECTIONAL (incl. electioneering)")):
        print(f"\n{'=' * 78}\n{label}\n{'=' * 78}")
        panel = build_panel(conn, express_only)
        key = "express" if express_only else "all"

        print(f"  C6.3 legislative target rows in window: {panel['n_target_rows']:,}")
        print(f"  district-cycles with a scorable residual: "
              f"{len(panel['aggregate'])}  (skipped {len(panel['skipped'])})")
        if panel["total_seen"]:
            print(f"  party unresolved: ${panel['unresolved_party']:,.0f} of "
                  f"${panel['total_seen']:,.0f} "
                  f"({100 * panel['unresolved_party'] / panel['total_seen']:.1f}%)")

        hdr = (f"{'cell':>10} | {'net pro-D':>11} | {'total':>9} | "
               f"{'resid pp':>8} | {'margin':>8} | race")
        print("\n  " + hdr)
        print("  " + "-" * (len(hdr) + 20))
        for r in sorted(panel["matched"], key=lambda x: (x["cycle"], x["district_id"])):
            print(f"  {r['district_id'] + '/' + str(r['cycle'])[2:]:>10} | "
                  f"{r['net_m']:>+9.3f}M | {r['total_m']:>7.3f}M | "
                  f"{r['residual_pp']:>+8.2f} | {r['actual_margin']:>+8.2f} | "
                  f"{r['race_name'][:44]}")

        for spec, rows_ in (("race_matched", panel["matched"]),
                            ("district_aggregate", panel["aggregate"])):
            for r in rows_:
                cells_out.append({
                    "advocacy_scope": key, "specification": spec,
                    "cycle": r["cycle"], "district_id": r["district_id"],
                    "race_name": r["race_name"], "is_senate": int(r["is_senate"]),
                    "pro_dem_usd": round(r["pro_dem"], 2),
                    "pro_rep_usd": round(r["pro_rep"], 2),
                    "net_pro_dem_musd": round(r["net_m"], 6),
                    "total_directional_musd": round(r["total_m"], 6),
                    "residual_pp": r["residual_pp"],
                    "actual_margin": r["actual_margin"],
                })

        senate = [r for r in panel["matched"] if r["is_senate"]]
        result[key] = {
            "race_matched": estimate(panel["matched"],
                                     "RACE-MATCHED (primary - IE on the scored contest)"),
            "senate_only": estimate(
                senate,
                "SENATE-ONLY (cleanest - one seat per district-cycle, so "
                "chamber-level money maps 1:1 to the scored race)"),
            "district_aggregate": estimate(
                panel["aggregate"],
                "DISTRICT-AGGREGATE (sensitivity - MISMATCHED: all three seats' "
                "money against one seat's residual)"),
            "n_cells_matched": len(panel["matched"]),
            "n_cells_aggregate": len(panel["aggregate"]),
            "unresolved_party_share": (panel["unresolved_party"] / panel["total_seen"]
                                       if panel["total_seen"] else 0.0),
        }

    conn.close()

    print("\n" + "=" * 78)
    print("READ THIS BEFORE QUOTING A NUMBER")
    print("=" * 78)
    print("  * The RACE-MATCHED express-advocacy panel is the primary result.")
    print("    The district-aggregate rows put all three seats' money against one")
    print("    seat's residual and are reported only to show what that does.")
    print("  * Electioneering Communication is not express advocacy. The 'ALL")
    print("    DIRECTIONAL' block is a superset, not a better-powered version of")
    print("    the same thing.")
    print("  * Endogeneity is unaddressed. IE is targeted at expected closeness,")
    print("    so no estimate here is causal. The interval is the finding.")

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)
        print(f"\nwrote {args.json_out}")

    if args.cells_csv:
        import csv
        cols = list(cells_out[0].keys())
        # Deterministic order: the file is checked in, so an unstable sort would
        # produce a spurious diff on every regeneration.
        cells_out.sort(key=lambda r: (r["advocacy_scope"], r["specification"],
                                      r["cycle"], r["district_id"]))
        with open(args.cells_csv, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
            w.writeheader()
            w.writerows(cells_out)
        print(f"wrote {args.cells_csv}  ({len(cells_out)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
