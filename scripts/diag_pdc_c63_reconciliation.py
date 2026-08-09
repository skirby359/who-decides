"""Reconcile PDC C6.3 attributions against C6.2 expenditures.

The question this answers is the one that must be settled before any figure
built on ``pdc_ie_targets`` is published: **``portion_of_amount`` and
``expenditure_amount`` are different measures, and if the C6.3 apportionment
does not close against the C6.2 expenditures it purports to divide, the model
is wrong.**

It also reports two things the loader's docstring asserts and should be able to
demonstrate on demand:

  * the **link between the two origins is ``report_number`` and nothing finer**
    - C6.3 rows carry no expenditure id, line number or parent key, so a target
    apportions a *report*, not an individual itemized payment;
  * ``report_type`` separates **express advocacy** (Independent Expenditure,
    Independent Expenditure Ad) from **Electioneering Communication**, which
    identifies a candidate without necessarily advocating.

Reads the Socrata source directly rather than the warehouse, so it can be run
before a load and does not need the 5 GB DuckDB. Prints aggregates only.

Usage:
    python scripts/diag_pdc_c63_reconciliation.py
    python scripts/diag_pdc_c63_reconciliation.py --cycles 2018 2020 2022 2024
"""

from __future__ import annotations

import argparse
import statistics
import sys
import urllib.parse
from collections import defaultdict

import httpx

DATASET = "67cp-h962"
BASE = f"https://data.wa.gov/resource/{DATASET}.json"
PAGE = 5000
TIMEOUT = 90.0

# The three sections of form C-6 flattened into this one table.
C62 = "C6.2"   # Itemized Expenditures - sponsor, vendor, amount, date
C63 = "C6.3"   # Identified Entities   - candidate, direction, portion

EXPRESS_ADVOCACY = {"Independent Expenditure", "Independent Expenditure Ad"}


_SAFE = "=&(),'"


def _get(params: dict) -> list[dict]:
    url = f"{BASE}?" + "&".join(
        f"{k}={urllib.parse.quote(str(v), safe=_SAFE)}"
        for k, v in params.items()
    )
    r = httpx.get(url, timeout=TIMEOUT, follow_redirects=True)
    r.raise_for_status()
    return r.json()


def _page_all(select: str, where: str) -> list[dict]:
    """Paginate to exhaustion, then assert against the source's own count."""
    expected = int(_get({"$select": "count(1) as n", "$where": where})[0]["n"])
    out: list[dict] = []
    offset = 0
    while True:
        chunk = _get({"$select": select, "$where": where,
                      "$limit": PAGE, "$offset": offset, "$order": "id"})
        out.extend(chunk)
        if len(chunk) < PAGE:
            break
        offset += PAGE
    if len(out) != expected:
        raise RuntimeError(
            f"fetched {len(out)} rows, source counts {expected} - truncated scan"
        )
    return out


def _f(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _origin_where(prefix: str, cycles: list[int]) -> str:
    w = f"starts_with(origin, '{prefix}')"
    if cycles:
        w += f" AND election_year in ({','.join(str(c) for c in cycles)})"
    return w


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cycles", nargs="*", type=int,
                    default=[2018, 2020, 2022, 2024],
                    help="Election years to reconcile (default: the money "
                         "paper's window). Pass with no values for all years.")
    args = ap.parse_args()
    cycles = args.cycles or []

    label = ", ".join(str(c) for c in cycles) if cycles else "all years"
    print(f"PDC C-6 reconciliation - {DATASET} - cycles: {label}\n")

    # ---- 1. Is there any link finer than report_number? -------------------
    print("=== 1. Available join keys ===")
    sample62 = _get({"$where": _origin_where(C62, cycles), "$limit": 500})
    sample63 = _get({"$where": _origin_where(C63, cycles), "$limit": 500})
    keys62 = {k for r in sample62 for k, v in r.items() if v not in (None, "")}
    keys63 = {k for r in sample63 for k, v in r.items() if v not in (None, "")}
    shared = sorted(keys62 & keys63)
    print(f"  C6.2 fields: {len(keys62)}   C6.3 fields: {len(keys63)}")
    print(f"  shared: {', '.join(shared)}")
    # Anything that could identify an individual EXPENDITURE rather than a
    # report. Matched against a named list, not a substring heuristic: the
    # shared field `total_unitemized` contains "item" and is a report-level
    # dollar total, so a loose test reports a finer key that does not exist.
    FINER_KEY_NAMES = {
        "expenditure_id", "expenditure_number", "itemized_expenditure_id",
        "line_number", "line_item", "parent_id", "transaction_id",
        "sequence_number", "detail_id",
    }
    finer = sorted(k for k in shared if k.lower() in FINER_KEY_NAMES)
    print(f"  candidate finer-than-report keys: {finer or 'NONE'}")
    if finer:
        print("  !! a finer key appeared - the report-level model may be wrong")
    else:
        print("  -> the only usable link is `report_number`: a C6.3 row "
              "apportions a REPORT, not a line.")

    # ---- 2. Does the apportionment close? --------------------------------
    print("\n=== 2. Per-report reconciliation ===")
    c62 = _page_all("id, report_number, expenditure_amount",
                    _origin_where(C62, cycles))
    c63 = _page_all("id, report_number, portion_of_amount, total_this_report, "
                    "report_type, candidate_office_type, for_or_against",
                    _origin_where(C63, cycles))
    print(f"  C6.2 rows {len(c62):,}   C6.3 rows {len(c63):,}")

    exp: dict[str, float] = defaultdict(float)
    for r in c62:
        exp[r.get("report_number", "")] += _f(r.get("expenditure_amount"))
    por: dict[str, float] = defaultdict(float)
    for r in c63:
        por[r.get("report_number", "")] += _f(r.get("portion_of_amount"))

    only62, only63 = set(exp) - set(por), set(por) - set(exp)
    both = sorted(set(exp) & set(por))
    print(f"  reports: both {len(both):,}   C6.2-only {len(only62):,}   "
          f"C6.3-only {len(only63):,}")

    ratios = sorted(por[k] / exp[k] for k in both if exp[k] > 0)
    if not ratios:
        print("  no reconcilable reports")
        return 1
    exact = sum(1 for k in both if exp[k] > 0 and abs(por[k] - exp[k]) < 0.01)
    print(f"  ratio SUM(portion)/SUM(expenditure) over {len(ratios):,} reports:")
    print(f"    min {ratios[0]:.4f}  median {statistics.median(ratios):.4f}  "
          f"max {ratios[-1]:.4f}")
    for lo, hi in [(0, 0.99), (0.99, 1.01), (1.01, 1.5), (1.5, 1e9)]:
        n = sum(1 for x in ratios if lo <= x < hi)
        print(f"    [{lo:>5}, {hi:>6}) {n:6,}  {100 * n / len(ratios):5.1f}%")
    print(f"  exact to the cent: {exact:,}/{len(both):,} "
          f"({100 * exact / len(both):.1f}%)")
    print(f"\n  window totals:  C6.2 ${sum(exp.values()):,.2f}"
          f"   C6.3 ${sum(por.values()):,.2f}")
    drift = sum(por.values()) - sum(exp.values())
    print(f"  drift ${drift:,.2f} "
          f"({100 * drift / sum(exp.values()):+.4f}% of the C6.2 total)")

    # ---- 3. Advocacy vs electioneering ------------------------------------
    print("\n=== 3. report_type - express advocacy vs electioneering ===")
    print("  A `for_or_against` on an Electioneering Communication row is NOT")
    print("  express advocacy. Report the two apart.\n")
    for scope, pred in (("all offices", lambda r: True),
                        ("Legislative", lambda r: r.get("candidate_office_type") == "Legislative")):
        buckets: dict[tuple[str, str], list[float]] = defaultdict(list)
        for r in c63:
            if not pred(r):
                continue
            buckets[(r.get("report_type") or "", r.get("for_or_against") or "")] \
                .append(_f(r.get("portion_of_amount")))
        total = sum(sum(v) for v in buckets.values())
        print(f"  -- {scope} --   n={sum(len(v) for v in buckets.values()):,}  "
              f"${total:,.2f}")
        for (rt, direction), vals in sorted(buckets.items(),
                                            key=lambda kv: -sum(kv[1])):
            print(f"     {rt:32s} {direction:8s} {len(vals):5,}  "
                  f"${sum(vals):>14,.2f}")
        ec = sum(sum(v) for (rt, _), v in buckets.items()
                 if rt not in EXPRESS_ADVOCACY)
        if total:
            print(f"     -> electioneering share: ${ec:,.2f} "
                  f"({100 * ec / total:.1f}% of directional dollars)\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
