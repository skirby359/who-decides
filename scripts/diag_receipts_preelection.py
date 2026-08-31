"""Finding 1's fundraising ratio, re-measured on PRE-ELECTION receipts — the re-pull that
`source_availability_claims.csv` row `fec-receipts-preelection-cutoff` registers as owed and
that an external series referee (2026-08-29) called the last important empirical task for
does-money-move-votes.md: with full-cycle receipts, part of the +0.60 association can
literally be outcome -> money (winners retire debt and bank post-election), and the paper's
Appendix C says so without quantifying it.

WHAT THIS MEASURES. The paper's pinned cell frame (overperformance_cells_2026-08-15.csv)
carries each congressional cell's D and R full-cycle receipts, taken from candidate_finance
(FEC candidate summary totals, one row per candidate-cycle, coverage windows that mostly
close AFTER election day). FEC also publishes each committee's individual REPORTS with
per-period receipts and coverage dates, so a pre-election total is the sum of report periods
whose coverage ends on or before election day. That is the same measure family (all
receipts: individual + PAC + party + loans, itemized and not), just cut at the election —
NOT the itemized-only reconstruction a bulk re-pull would give, which would change the
measure as well as the window.

CANDIDATE RESOLUTION uses the frame's own linkage output rather than re-deriving it: each
cell's d_receipts/r_receipts value is located in candidate_finance (office='H', the cell's
padded district, the cell's cycle) by exact amount, which recovers the paper's own
(fec_candidate_id) with no name parsing. If the table was reloaded since the pin and the
amount no longer matches, it falls back to the paper's documented name key (cycle, last
name, first initial, office+district scoped) and says so.

Coverage caveat, stated rather than hidden: the last pre-election report is the 12-day
PRE-GENERAL (coverage typically ends ~17-20 days before election day), so "pre-election"
here means "through the final pre-election filing", and the last covered date is recorded
per candidate in the pin.

TWO MODES:
    --fetch     hit api.open.fec.gov (needs FEC_API_KEY in .env), write the pin:
                docs/reference/fec_receipts_preelection_2026-08-29.csv (~2 API calls per
                candidate, throttled; a few minutes for ~60 candidates)
    (default)   read the pin + the cell frame and print the correlations:
                  r_full_pin      pinned full-cycle ratio (reproduces the paper's
                                  within-congressional r on these cells)
                  r_full_reports  full-cycle ratio rebuilt by summing ALL report periods
                                  (consistency check on the report-summing itself)
                  r_pre           the pre-election ratio — the question

Also attempts the STATE-LEGISLATIVE analogue from loaded data (PDC itemized rows carry
contribution_date), reported separately and clearly labelled itemized-only — a different
measure from the summary receipts, so its full-vs-pre comparison is internally consistent
but not comparable in level to the federal one. Committee/candidate aggregates only.
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
import time
from datetime import date
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))  # config.* lives at the repo root, not beside this script
DATA = ROOT / "data"
CELLS = ROOT / "docs" / "reference" / "overperformance_cells_2026-08-15.csv"
PIN = ROOT / "docs" / "reference" / "fec_receipts_preelection_2026-08-29.csv"
BASE = "https://api.open.fec.gov/v1"

ELECTION_DAY = {2018: date(2018, 11, 6), 2020: date(2020, 11, 3),
                2022: date(2022, 11, 8), 2024: date(2024, 11, 5)}
_SUFFIXES = {"SR", "SR.", "JR", "JR.", "II", "III", "IV", "MR", "MRS", "MS", "DR"}
# Committee-grain sibling of PIN (2026-08-29, second referee pass): one row per
# (candidate-cycle, committee) with the committee's designation AS OF THAT CYCLE from
# /committee/{id}/history/{cycle}/ — because the committees endpoint reports the CURRENT
# designation, and a retired incumbent's principal committee is redesignated afterwards.
# This is what lets the analysis compute the AUTHORIZED-committee universe (at-cycle
# designation P or A) beside the everything-but-J one, which a referee correctly noted is
# too broad as a *rule* even if the reconciliation says it lands on the right money.
CMTE_PIN = ROOT / "docs" / "reference" / "fec_receipts_preelection_committees_2026-08-29.csv"


def _cf_last_first(cf_name: str) -> tuple[str, str]:
    """candidate_finance-style 'LAST, FIRST [M] [SFX]' -> (LAST, first initial)."""
    if "," in (cf_name or ""):
        last_part, _, first_part = cf_name.partition(",")
        last = last_part.strip().split()[-1].upper()
        firsts = [t.strip(" .") for t in first_part.split()
                  if t.strip(" .").upper() not in _SUFFIXES]
        return last, (firsts[0][0].upper() if firsts else "")
    return _last_first(cf_name or "")


def _frame(pred: str) -> list[dict]:
    """Frame rows under the VERIFIER'S OWN predicate (verify_money_votes.derive_finding1):
    `baseline_ok AND fin_log2_dr IS NOT NULL` — the 128-cell Finding 1 population — split
    by the same district test it uses. Read through DuckDB so NULL semantics match."""
    con = duckdb.connect()
    rows = con.execute(
        f"SELECT * FROM read_csv_auto('{CELLS.as_posix()}', header=true) "
        f"WHERE baseline_ok AND fin_log2_dr IS NOT NULL AND {pred}").fetchall()
    cols = [c[0] for c in con.description]
    con.close()
    return [dict(zip(cols, r)) for r in rows]


def _cong_cells() -> list[dict]:
    return _frame("district NOT LIKE 'ld%'")


def _last_first(name: str) -> tuple[str, str]:
    """Frame-style 'FIRST [M.] LAST[, SFX]' -> (LAST, first initial)."""
    toks = [t.strip(" .,") for t in name.replace(",", " ").split()]
    toks = [t for t in toks if t and t.upper() not in _SUFFIXES]
    return toks[-1].upper(), toks[0][0].upper()


def _resolve(con, dist: str, year: int, name: str, amount: float):
    """The frame's candidate_finance row: by exact amount first, name key as fallback."""
    pad = dist[2:].zfill(2)
    rows = con.execute("""
        SELECT fec_candidate_id, candidate_name, total_receipts
        FROM candidate_finance
        WHERE office='H' AND district=? AND election_cycle=? AND state='WA'
    """, [pad, year]).fetchall()
    hit_rows = [r for r in rows if r[2] is not None and abs(float(r[2]) - amount) < 1.0]
    hit = {r[0] for r in hit_rows}
    if len(hit) == 1:          # distinct ids — duplicate summary rows for one id are fine
        return [hit.pop()], "amount"
    if len(hit) > 1:
        # The FEC sometimes carries one PERSON under several candidate ids (measured:
        # H2WA10063 'HEWETT, DON' and H4WA10044 'HEWETT, DON MR', identical totals). When
        # every amount-matched id parses to the same (last name, first initial), treat the
        # set as aliases: fetch all of them and de-duplicate at the committee level.
        # candidate_finance names are 'LAST, FIRST [SFX]' — parse them that way, or
        # 'HEWETT, DON MR' keys on ('MR','H') and the alias set never matches.
        keys = {(_cf_last_first(r[1] or "")) for r in hit_rows}
        if len(keys) == 1:
            return sorted(hit), "amount-alias-ids"
    last, fi = _last_first(name)
    named = [r for r in rows
             if last in (r[1] or "").upper()
             and (r[1] or "").upper().replace(",", " ").split(last)[-1].strip()[:1] in (fi, "")]
    named_ids = {r[0] for r in named
                 if last == (r[1] or "").upper().split(",")[0].strip().split()[-1]}
    if len(named_ids) == 1:
        return [named_ids.pop()], "name"
    return None, (f"unresolved ({len(hit)} amount ids, {len(named_ids)} name ids, "
                  f"{len(rows)} rows)")


# ---------------------------------------------------------------------------- fetch mode


def _get(client, url: str, params: dict) -> dict:
    import httpx  # noqa: F401  (import error surfaces here, near the use)
    for attempt in range(4):
        r = client.get(url, params=params, timeout=30)
        if r.status_code == 429:
            time.sleep(10 * (attempt + 1))
            continue
        r.raise_for_status()
        return r.json()
    raise SystemExit(f"FEC API kept returning 429 for {url}")


def fetch() -> int:
    import httpx
    from config.settings import settings
    key = settings.fec_api_key
    if not key:
        raise SystemExit("FEC_API_KEY not configured (.env) — cannot fetch")

    con = duckdb.connect(str(DATA / "wa_statewide.duckdb"), read_only=True)
    cells = _cong_cells()
    # Incremental: keep pin rows whose (district, year, side) is already fetched, so a
    # resolution fix re-pulls only what it fixed.
    existing: dict[tuple[str, int, str], dict] = {}
    if PIN.exists():
        with PIN.open(encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                existing[(r["district"], int(r["year"]), r["side"])] = r
    todo: dict[tuple[str, int], dict] = {}      # (ids-joined, year) -> row skeleton
    unresolved = []
    for c in cells:
        year = int(c["year"])
        for side, ncol, rcol in (("D", "dem_candidate", "d_receipts"),
                                 ("R", "rep_candidate", "r_receipts")):
            if (c["district"], year, side) in existing:
                continue
            cand_ids, how = _resolve(con, c["district"], year, c[ncol], float(c[rcol]))
            if cand_ids is None:
                unresolved.append((c["district"], year, side, c[ncol], how))
                continue
            todo[("+".join(cand_ids), year)] = dict(
                district=c["district"], year=year, side=side,
                candidate=c[ncol], fec_candidate_id="+".join(cand_ids),
                cand_ids=cand_ids, resolved_by=how)
    con.close()
    if unresolved:
        print("UNRESOLVED candidates (excluded, and the analysis will say so):")
        for u in unresolved:
            print("   ", u)
    print(f"fetching reports for {len(todo)} candidate-cycles "
          f"({len(cells)} congressional cells) ...")

    out_rows = []
    cmte_rows = []
    with httpx.Client() as client:
        for (cand_key, year), row in sorted(todo.items()):
            eday = ELECTION_DAY[year]
            # Committee rule (revised 2026-08-29 after a referee objection). The request
            # is unfiltered; joint-fundraising (J) committees are dropped; and every kept
            # committee's designation is fetched AS OF THE CYCLE from
            # /committee/{id}/history/{cycle}/, because the committees endpoint reports
            # the CURRENT designation and that is not the same object: a retired
            # incumbent's principal committee is redesignated (CMR's C00390476 reads 'U'
            # today), and a campaign committee later converted to a leadership PAC reads
            # 'D' today (Jensen's C00720870). The referee is right that "everything
            # linked except J" is too broad AS A RULE — a genuine at-cycle leadership
            # PAC's receipts are not candidate fundraising — so the committee pin records
            # the at-cycle designation per row and the analysis computes BOTH universes:
            # everything-but-J (comparable to the loaded candidate_finance summary basis,
            # checked by reconciliation) and authorized-only (at-cycle P/A). Alias id
            # sets ('amount-alias-ids') union their committees, de-duplicated by
            # committee id, so one person under two FEC candidate ids is counted once.
            res = []
            for cand_id in row["cand_ids"]:
                js = _get(client, f"{BASE}/candidate/{cand_id}/committees/",
                          dict(api_key=key, cycle=year, per_page=100))
                res.extend(js.get("results", []))
                time.sleep(0.6)
            keep = {c["committee_id"]: c for c in res if c.get("designation") != "J"}
            atcycle: dict[str, tuple[str, str]] = {}   # cid -> (desig_at_cycle, how)
            for cid, c in sorted(keep.items()):
                js = _get(client, f"{BASE}/committee/{cid}/history/{year}/",
                          dict(api_key=key, per_page=10))
                time.sleep(0.6)
                hres = js.get("results", [])
                if hres:
                    atcycle[cid] = (hres[0].get("designation") or "?", f"history/{year}")
                else:
                    # No row for that exact cycle: take the nearest history row at or
                    # before it, flagged, rather than silently trusting the current code.
                    js = _get(client, f"{BASE}/committee/{cid}/history/",
                              dict(api_key=key, per_page=100))
                    time.sleep(0.6)
                    older = [h for h in js.get("results", [])
                             if (h.get("cycle") or 0) <= year]
                    if older:
                        h = max(older, key=lambda x: x.get("cycle") or 0)
                        atcycle[cid] = (h.get("designation") or "?",
                                        f"nearest:{h.get('cycle')}")
                    else:
                        atcycle[cid] = ("?", "no-history")
            cmte_tags = sorted(f"{cid}:{keep[cid].get('designation') or '?'}"
                               f">{atcycle[cid][0]}" for cid in keep)
            pre = full = 0.0
            n_pre = n_all = 0
            last_pre_end = None
            for cid in sorted(keep):
                c_pre = c_full = 0.0
                c_n = 0
                page = 1
                while True:
                    js = _get(client, f"{BASE}/committee/{cid}/reports/",
                              dict(api_key=key, cycle=year, per_page=100, page=page))
                    time.sleep(0.6)
                    for rep in js.get("results", []):
                        if rep.get("most_recent") is False:
                            continue
                        amt = rep.get("total_receipts_period")
                        if amt is None:
                            continue
                        end = (rep.get("coverage_end_date") or "")[:10]
                        if not end:
                            continue
                        end_d = date.fromisoformat(end)
                        c_full += float(amt)
                        c_n += 1
                        n_all += 1
                        if end_d <= eday:
                            c_pre += float(amt)
                            n_pre += 1
                            if last_pre_end is None or end_d > last_pre_end:
                                last_pre_end = end_d
                    pages = js.get("pagination", {}).get("pages", 1)
                    if page >= pages:
                        break
                    page += 1
                pre += c_pre
                full += c_full
                cmte_rows.append(dict(
                    district=row["district"], year=year, side=row["side"],
                    candidate=row["candidate"], fec_candidate_id=row["fec_candidate_id"],
                    committee_id=cid, committee_name=keep[cid].get("name") or "",
                    designation_current=keep[cid].get("designation") or "?",
                    designation_at_cycle=atcycle[cid][0],
                    designation_source=atcycle[cid][1],
                    pre_receipts=f"{c_pre:.2f}", full_receipts_reports=f"{c_full:.2f}",
                    n_reports=c_n,
                    source="api.open.fec.gov /committee/{id}/{history,reports}/",
                    retrieved_on="2026-08-29"))
            rec = {k: v for k, v in row.items() if k != "cand_ids"}
            out_rows.append({**rec, "committees": ";".join(cmte_tags),
                             "pre_receipts": f"{pre:.2f}",
                             "full_receipts_reports": f"{full:.2f}",
                             "last_pre_coverage_end": last_pre_end.isoformat() if last_pre_end else "",
                             "n_reports_pre": n_pre, "n_reports_total": n_all,
                             "source": "api.open.fec.gov /committee/{id}/reports/",
                             "retrieved_on": "2026-08-29"})
            flagged = [f"{cid}={atcycle[cid][0]}" for cid in keep
                       if atcycle[cid][0] not in ("P", "A")]
            print(f"  {row['district']} {year} {row['side']:1} {row['fec_candidate_id']}  "
                  f"pre ${pre:,.0f}  full ${full:,.0f}  ({n_pre}/{n_all} reports, "
                  f"last pre-cov {last_pre_end})"
                  + (f"  ⚠ non-P/A at cycle: {','.join(flagged)}" if flagged else ""))

    PIN.parent.mkdir(parents=True, exist_ok=True)
    cols = ["district", "year", "side", "candidate", "fec_candidate_id", "resolved_by",
            "committees", "pre_receipts", "full_receipts_reports",
            "last_pre_coverage_end", "n_reports_pre", "n_reports_total",
            "source", "retrieved_on"]
    merged = {(r["district"], int(r["year"]), r["side"]): r for r in existing.values()}
    for r in out_rows:
        merged[(r["district"], int(r["year"]), r["side"])] = r
    with PIN.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for k in sorted(merged):
            w.writerow(merged[k])
    ccols = ["district", "year", "side", "candidate", "fec_candidate_id", "committee_id",
             "committee_name", "designation_current", "designation_at_cycle",
             "designation_source", "pre_receipts", "full_receipts_reports", "n_reports",
             "source", "retrieved_on"]
    with CMTE_PIN.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=ccols)
        w.writeheader()
        for r in sorted(cmte_rows, key=lambda x: (x["district"], x["year"], x["side"],
                                                  x["committee_id"])):
            w.writerow(r)
    print(f"\nwrote {PIN}  ({len(merged)} candidate-cycles, {len(out_rows)} fetched now)")
    print(f"wrote {CMTE_PIN}  ({len(cmte_rows)} committee-cycle rows)")
    return 0


# ------------------------------------------------------------------------- analysis mode


def _pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy)


def analyse() -> int:
    if not PIN.exists():
        raise SystemExit(f"pin missing: {PIN} — run with --fetch first")
    with PIN.open(encoding="utf-8-sig", newline="") as fh:
        pin = list(csv.DictReader(fh))
    by_cell: dict[tuple[str, int], dict] = {}
    for r in pin:
        k = (r["district"], int(r["year"]))
        by_cell.setdefault(k, {})[r["side"]] = r

    cells = _cong_cells()
    rows = []
    dropped_pre = []
    recon = []
    for c in cells:
        k = (c["district"], int(c["year"]))
        sides = by_cell.get(k, {})
        if set(sides) != {"D", "R"}:
            dropped_pre.append((k, "candidate unresolved at fetch"))
            continue
        d, r = sides["D"], sides["R"]
        d_full, r_full = float(d["full_receipts_reports"]), float(r["full_receipts_reports"])
        d_pre, r_pre = float(d["pre_receipts"]), float(r["pre_receipts"])
        # reconciliation of report-summed full-cycle vs the frame's summary totals
        for side_row, frame_amt in ((d, float(c["d_receipts"])), (r, float(c["r_receipts"]))):
            if frame_amt > 0:
                recon.append(abs(float(side_row["full_receipts_reports"]) - frame_amt) / frame_amt)
        row = dict(district=c["district"], year=int(c["year"]),
                   overperf=float(c["overperformance"]),
                   full_pin=float(c["fin_log2_dr"]))
        row["full_rep"] = (math.log2(d_full / r_full)
                           if d_full > 0 and r_full > 0 else None)
        row["pre"] = (math.log2(d_pre / r_pre)
                      if d_pre > 0 and r_pre > 0 else None)
        if row["pre"] is None:
            dropped_pre.append((k, f"pre-window receipts zero on a side "
                                   f"(D ${d_pre:,.0f} / R ${r_pre:,.0f})"))
        rows.append(row)

    print("FINDING 1'S FUNDRAISING RATIO — full-cycle vs PRE-ELECTION, congressional cells")
    print(f"(cells with both-side finance in the pinned frame: {len(rows)}; "
          f"election-day cutoffs {sorted(set(ELECTION_DAY.values()))[0].year}-"
          f"{sorted(set(ELECTION_DAY.values()))[-1].year})\n")
    hdr = (f"{'cell':11}{'overperf':>9}{'log2 full(pin)':>15}{'full(reports)':>14}"
           f"{'pre-election':>13}")
    print(hdr)
    print("-" * len(hdr))
    for row in sorted(rows, key=lambda x: (x["district"], x["year"])):
        fr = f"{row['full_rep']:.2f}" if row["full_rep"] is not None else "—"
        pr = f"{row['pre']:.2f}" if row["pre"] is not None else "—"
        print(f"{row['district']+'/'+str(row['year']):11}{row['overperf']:>9.2f}"
              f"{row['full_pin']:>15.2f}{fr:>14}{pr:>13}")

    frame_all = _cong_cells()          # the paper's full within-congressional frame
    r_paper = _pearson([float(c["fin_log2_dr"]) for c in frame_all],
                       [float(c["overperformance"]) for c in frame_all])
    ok_full = [r for r in rows if r["full_rep"] is not None]
    ok_pre = [r for r in rows if r["pre"] is not None]
    r_full_pin_all = _pearson([r["full_pin"] for r in rows], [r["overperf"] for r in rows])
    r_full_pin = _pearson([r["full_pin"] for r in ok_pre], [r["overperf"] for r in ok_pre])
    r_full_rep = _pearson([r["full_rep"] for r in ok_full], [r["overperf"] for r in ok_full])
    r_pre = _pearson([r["pre"] for r in ok_pre], [r["overperf"] for r in ok_pre])
    print(f"\n  r  full-cycle, pinned (the paper's frame)  {r_paper:+.3f}   (n={len(frame_all)})")
    print(f"  r  full-cycle, pinned, pin-joined cells    {r_full_pin_all:+.3f}   (n={len(rows)})")
    print(f"  r  full-cycle, report-period sums          {r_full_rep:+.3f}   (n={len(ok_full)})")
    print(f"  r  PRE-ELECTION report periods             {r_pre:+.3f}   (n={len(ok_pre)})"
          f"{'' if len(ok_pre) == len(rows) else '  <- same-cell full-cycle r: %+.3f' % r_full_pin}")
    if recon:
        print(f"\n  report-sum vs summary-total reconciliation: mean |diff| "
              f"{100 * sum(recon) / len(recon):.2f}%, max {100 * max(recon):.2f}% "
              f"over {len(recon)} candidate-cycles")
    if dropped_pre:
        print("\n  cells outside r_pre, and why:")
        for k, why in dropped_pre:
            print(f"    {k[0]}/{k[1]}: {why}")

    # ---- committee-universe validation (2026-08-29, second referee pass) --------------
    # The everything-but-J universe above is the summary-basis-comparable one; a referee
    # correctly objected that as a RULE it could sweep in a genuine at-cycle leadership
    # PAC. The committee pin carries each committee's designation AS OF the cycle, so the
    # AUTHORIZED universe (at-cycle P/A) is computed here beside it.
    if CMTE_PIN.exists():
        with CMTE_PIN.open(encoding="utf-8-sig", newline="") as fh:
            crows = list(csv.DictReader(fh))
        flagged = [r for r in crows if r["designation_at_cycle"] not in ("P", "A")]
        print(f"\nCOMMITTEE-UNIVERSE VALIDATION ({len(crows)} committee-cycle rows):")
        if not flagged:
            print("  every included committee was designation P or A AS OF ITS CYCLE — the "
                  "everything-but-J and authorized universes are identical, and the "
                  "current-designation oddities were redesignations after the fact.")
        else:
            print("  committees NOT P/A at cycle (excluded from the authorized universe):")
            for r in flagged:
                print(f"    {r['district']}/{r['year']} {r['side']} {r['committee_id']} "
                      f"{r['committee_name'][:34]:34} now={r['designation_current']} "
                      f"at-cycle={r['designation_at_cycle']} ({r['designation_source']}) "
                      f"full ${float(r['full_receipts_reports']):,.0f}")
            auth: dict[tuple[str, int, str], tuple[float, float]] = {}
            for r in crows:
                if r["designation_at_cycle"] not in ("P", "A"):
                    continue
                k = (r["district"], int(r["year"]), r["side"])
                p0, f0 = auth.get(k, (0.0, 0.0))
                auth[k] = (p0 + float(r["pre_receipts"]),
                           f0 + float(r["full_receipts_reports"]))
            xs_f, xs_p, ys2 = [], [], []
            for c in _cong_cells():
                kd = (c["district"], int(c["year"]), "D")
                kr = (c["district"], int(c["year"]), "R")
                if kd not in auth or kr not in auth:
                    continue
                dv, rv = auth[kd], auth[kr]
                if min(dv[0], rv[0], dv[1], rv[1]) <= 0:
                    continue
                xs_f.append(math.log2(dv[1] / rv[1]))
                xs_p.append(math.log2(dv[0] / rv[0]))
                ys2.append(float(c["overperformance"]))
            if len(ys2) >= 10:
                print(f"  r  full-cycle, AUTHORIZED (at-cycle P/A) universe "
                      f"{_pearson(xs_f, ys2):+.3f}   (n={len(ys2)})")
                print(f"  r  PRE-ELECTION, AUTHORIZED universe              "
                      f"{_pearson(xs_p, ys2):+.3f}   (n={len(ys2)})")

    # ---- the state-legislative analogue, itemized-only, from loaded PDC rows ----------
    print("\nSTATE-LEGISLATIVE analogue (itemized PDC rows, contribution_date — a DIFFERENT")
    print("measure from summary receipts; internally consistent full-vs-pre only):")
    con = duckdb.connect(str(DATA / "wa_statewide.duckdb"), read_only=True)
    leg = _frame("district LIKE 'ld%'")
    resolved = {}
    for c in leg:
        year = int(c["year"])
        for side, ncol, rcol in (("D", "dem_candidate", "d_receipts"),
                                 ("R", "rep_candidate", "r_receipts")):
            dist = c["district"][2:].lstrip("0")
            rows_cf = con.execute("""
                SELECT fec_candidate_id, total_receipts FROM candidate_finance
                WHERE office IN ('SR','SS') AND district=? AND election_cycle=?
            """, [dist, year]).fetchall()
            hit = [r for r in rows_cf
                   if r[1] is not None and abs(float(r[1]) - float(c[rcol])) < 1.0]
            if len(hit) == 1:
                resolved[(c["district"], year, side)] = hit[0][0]
    n_pairs = sum(1 for c in leg
                  if (c["district"], int(c["year"]), "D") in resolved
                  and (c["district"], int(c["year"]), "R") in resolved)
    print(f"  cells with both sides resolved by exact amount: {n_pairs} of {len(leg)}")
    if n_pairs < 0.6 * len(leg):
        print("  SKIPPED: resolution coverage too low for a same-frame comparison — the "
              "federal result above is the registered deliverable; the state analogue "
              "needs its own linkage work.")
        con.close()
        return 0
    xs_full, xs_pre, ys = [], [], []
    zero_dropped = 0
    for c in leg:
        year = int(c["year"])
        kd, kr = (c["district"], year, "D"), (c["district"], year, "R")
        if kd not in resolved or kr not in resolved:
            continue
        eday = ELECTION_DAY[year].isoformat()
        vals = {}
        for side, key in (("D", kd), ("R", kr)):
            full, pre = con.execute("""
                SELECT COALESCE(SUM(contribution_amount),0),
                       COALESCE(SUM(contribution_amount)
                                FILTER (WHERE contribution_date <= CAST(? AS DATE)),0)
                FROM individual_contributions
                WHERE fec_candidate_id = ? AND election_cycle = ? AND contribution_amount > 0
            """, [eday, resolved[key], year]).fetchone()
            vals[side] = (float(full), float(pre))
        if min(vals["D"][0], vals["R"][0]) <= 0 or min(vals["D"][1], vals["R"][1]) <= 0:
            zero_dropped += 1
            continue
        xs_full.append(math.log2(vals["D"][0] / vals["R"][0]))
        xs_pre.append(math.log2(vals["D"][1] / vals["R"][1]))
        ys.append(float(c["overperformance"]))
    con.close()
    if len(ys) >= 10:
        print(f"  r  itemized full-cycle   {_pearson(xs_full, ys):+.3f}   (n={len(ys)}"
              f", {zero_dropped} dropped for a zero side)")
        print(f"  r  itemized PRE-ELECTION {_pearson(xs_pre, ys):+.3f}   (n={len(ys)})")
    else:
        print(f"  SKIPPED: only {len(ys)} usable cells after zero-side drops")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fetch", action="store_true",
                    help="pull per-report totals from the FEC API and write the pin")
    args = ap.parse_args()
    return fetch() if args.fetch else analyse()


if __name__ == "__main__":
    raise SystemExit(main())
