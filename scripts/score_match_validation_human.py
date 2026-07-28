"""Score the HUMAN match-validation pass and its agreement with the AI pass.

Companion to `diag_match_validation_human.py`. Written and committed BEFORE the human
rated anything, so the analysis is pre-specified rather than chosen after seeing the
verdicts — the same discipline `score_match_validation.py` follows for the AI pass. If
that ordering is ever broken, this script is worth less than the pass it scores.

Shares `wilson` / `precision` / `bound` / the verdict vocabulary and the frozen tier
shares with `score_match_validation.py` by import, so the two passes are scored by
identical estimators and the human figure is directly comparable to the AI's 93.0%.

THE ONE CONSEQUENTIAL QUESTION, printed first in a banner: does any full-name-tier record
get a non-Y human verdict? The paper's primary specification rests on that tier reading
100% (120/120, Wilson [96.9-100.0]). A single confirmed human NC in that block materially
weakens the specification argument and must not be discoverable only by reading to the
bottom of a table.

ON KAPPA AND PREVALENCE. Cohen's kappa is deflated when one category dominates, and the
full-name block is expected to be ~all-Y. A kappa near zero there would mean "almost
nothing to disagree about", NOT "the raters disagree" — so raw agreement and PABAK are
reported alongside, and the full-name block gets PABAK specifically. Read them together.

Emits a PII-free publishable ledger so the agreement statistic is re-derivable without
the name-bearing sample, exactly as the AI pass's ledger is.

Run:  python scripts/score_match_validation_human.py
"""
from __future__ import annotations

import csv
import io
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

# Same-directory sibling import: `scripts/` is not a package and this may be invoked as
# `python scripts/score_match_validation_human.py` from the repo root, so the script's own
# directory has to be on the path BEFORE the import, not at __main__ time.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from score_match_validation import (  # noqa: E402
    HEADER, PANEL_N_2026_07_27, PANELS, PRIMARY_TIER, TIER_SHARES_2026_07_27, TIERS,
    VALID, line, precision, wilson,
)

ROOT = Path(__file__).resolve().parent.parent
OUTDIR = ROOT / "data" / "validation"
EVIDENCE = OUTDIR / "match_validation_human.csv"
KEYFILE = OUTDIR / "match_validation_human_key.csv"
LEDGER_OUT = (ROOT / "docs" / "reference"
              / f"match_validation_human_verdicts_{date(2026, 7, 27).isoformat()}.csv")

# Y vs "not the same person". U is excluded from the binary and reported separately: it is
# a statement about the evidence, not about identity, so folding it either way would
# misreport agreement.
BINARY = {"Y": "same", "NC": "diff", "NP": "diff"}

# Accepted affirmative marks in the human `partial_merge` column. Raters tick a checkbox
# column however they like — "X" is at least as natural as "yes" — so accept the obvious
# forms rather than silently reading a ticked row as untick ed.
PM_TRUE = {"YES", "Y", "X", "1", "TRUE", "T", "*", "✓", "✔"}


def is_ticked(v: str) -> bool:
    return (v or "").strip().upper() in PM_TRUE


def kappa(pairs: list[tuple[str, str]]) -> tuple[float, float, float]:
    """Cohen's unweighted kappa. Returns (kappa, p_observed, p_expected)."""
    n = len(pairs)
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    cats = sorted({c for p in pairs for c in p})
    po = sum(1 for a, b in pairs if a == b) / n
    ma = Counter(a for a, _ in pairs)
    mb = Counter(b for _, b in pairs)
    pe = sum((ma[c] / n) * (mb[c] / n) for c in cats)
    k = (po - pe) / (1 - pe) if pe < 1 else float("nan")
    return k, po, pe


def pabak(po: float) -> float:
    """Prevalence-and-bias-adjusted kappa: 2*po - 1. Immune to the prevalence problem."""
    return 2 * po - 1


def agree_block(label: str, pairs: list[tuple[str, str]], width: int = 26) -> str:
    k, po, pe = kappa(pairs)
    return (f"  {label:<{width}}{len(pairs):>5}{po * 100:9.1f}%{pe * 100:9.1f}%"
            f"{k:8.3f}{pabak(po):9.3f}")


AGREE_HEADER = (f"  {'':<26}{'n':>5}{'observed':>10}{'expected':>9}"
                f"{'kappa':>8}{'PABAK':>9}")


def main() -> int:
    if not EVIDENCE.exists() or not KEYFILE.exists():
        print("!! human sample missing — run scripts/diag_match_validation_human.py")
        return 1

    key = {r["human_id"]: r for r in
           csv.DictReader(io.open(KEYFILE, encoding="utf-8-sig"))}
    ev = list(csv.DictReader(io.open(EVIDENCE, encoding="utf-8-sig")))

    unrated = [r["human_id"] for r in ev
               if (r.get("verdict") or "").strip().upper() not in VALID]
    if unrated:
        print(f"!! {len(unrated)} of {len(ev)} rows unrated or invalid "
              f"(need Y / NC / NP / U). First few: {', '.join(unrated[:8])}")
        print("   Nothing is scored until every row is rated — a partial pass would give")
        print("   an agreement statistic over a self-selected subset.")
        return 1

    rows = []
    for r in ev:
        k = key[r["human_id"]]
        rows.append({
            "human_id": r["human_id"], "sample_id": k["sample_id"],
            "state": k["state"], "panel": k["panel"], "tier": k["match_tier"],
            "band": k["dollar_band"],
            "ai": k["ai_verdict"].strip().upper(),
            "human": r["verdict"].strip().upper(),
            "ai_pm": k.get("ai_partial_merge", ""),
            "human_pm": "yes" if is_ticked(r.get("partial_merge")) else "",
            "note": (r.get("notes") or "").strip(),
        })

    # ---------- the banner ----------
    full = [r for r in rows if r["tier"] == PRIMARY_TIER]
    full_bad = [r for r in full if r["human"] != "Y"]
    print("=" * 96)
    print("HUMAN MATCH-VALIDATION — PRIMARY SPECIFICATION VERDICT")
    print("=" * 96)
    if not full_bad:
        print(f"  The full-name key holds: {len(full)}/{len(full)} rated Y by the human.")
        lo, hi = wilson(len(full), len(full))
        print(f"  Human-only Wilson 95% on this block: [{lo:.1f}-{hi:.1f}]")
        print("  The paper's primary-specification argument is unchanged.")
    else:
        print(f"  !! {len(full_bad)} of {len(full)} full-name-tier records got a NON-Y")
        print("     human verdict. The 100% / [96.9-100.0] claim and the primary")
        print("     specification argument WEAKEN. Do not publish the current wording.")
        for r in full_bad:
            print(f"       {r['human_id']}  {r['state']} {r['panel']:8} {r['band']:6}"
                  f"  AI={r['ai']:2}  human={r['human']:2}  {r['note'][:44]}")

    # ---------- human precision ----------
    by = defaultdict(Counter)
    for r in rows:
        by["ALL"][r["human"]] += 1
        by[("tier", r["tier"])][r["human"]] += 1
        by[("panel", r["state"], r["panel"])][r["human"]] += 1
        by[("band", r["band"])][r["human"]] += 1
        by[("tp", r["state"], r["panel"], r["tier"])][r["human"]] += 1

    print("\n--- HUMAN PRECISION BY MATCH TIER " + "-" * 62)
    print(HEADER)
    for t in TIERS:
        if sum(by[("tier", t)].values()):
            print(line(t, by[("tier", t)]))

    print("\n--- HUMAN PRECISION BY STATE x PANEL " + "-" * 59)
    print(HEADER)
    for state, panel in PANELS:
        if sum(by[("panel", state, panel)].values()):
            print(line(f"{state} {panel}", by[("panel", state, panel)]))

    print("\n--- HUMAN PRECISION BY DONOR-DOLLAR BAND " + "-" * 55)
    print(HEADER)
    for b, lbl in (("top10", "top decile of matched $"), ("rest", "deciles 2-10")):
        if sum(by[("band", b)].values()):
            print(line(lbl, by[("band", b)]))

    # ---------- human, reweighted on the frozen all-tier shares ----------
    print("\n--- HUMAN PRECISION REWEIGHTED ON THE FROZEN ALL-TIER SHARES " + "-" * 35)
    print("Directly comparable to the AI pass's 93.0% donor-weighted figure. Uses the")
    print("same pinned 2026-07-27 shares, so any gap is rater disagreement, not weights.")
    gn = gd = 0.0
    print(f"\n  {'panel':<16}{'donors':>10}{'weighted':>11}")
    for state, panel in PANELS:
        w = TIER_SHARES_2026_07_27[(state, panel)]
        num = wsum = 0.0
        for t in TIERS:
            c = by[("tp", state, panel, t)]
            p, _lo, _hi, judged = precision(c)
            if judged:
                num += w.get(t, 0.0) * p
                wsum += w.get(t, 0.0)
        if not wsum:
            continue
        wp = num / wsum
        n = PANEL_N_2026_07_27[(state, panel)]
        print(f"  {state + ' ' + panel:<16}{n:>10,}{wp:10.1f}%")
        gn += wp * n
        gd += n
    if gd:
        print(f"\n  Donor-weighted across panels: {gn / gd:.1f}%   "
              f"(AI pass on the same weights: 93.0%)")

    # ---------- agreement ----------
    print("\n--- AGREEMENT: AI vs HUMAN " + "-" * 69)
    print("kappa is deflated where one verdict dominates. On an all-Y block a kappa near")
    print("zero means 'nothing to disagree about', NOT 'the raters disagree' — read the")
    print("observed column and PABAK alongside it.")
    four = [(r["ai"], r["human"]) for r in rows]
    binary = [(BINARY[r["ai"]], BINARY[r["human"]]) for r in rows
              if r["ai"] in BINARY and r["human"] in BINARY]
    n_u = sum(1 for r in rows if "U" in (r["ai"], r["human"]))
    print(f"\n{AGREE_HEADER}")
    print(agree_block("all 4 categories", four))
    print(agree_block("collapsed binary", binary))
    print(f"  ({n_u} row(s) involve a U verdict and are excluded from the binary)")

    print("\n  by tier:")
    print(AGREE_HEADER)
    for t in TIERS:
        tp = [(r["ai"], r["human"]) for r in rows if r["tier"] == t]
        if tp:
            print(agree_block(t, tp))

    # ---------- divergences ----------
    div = [r for r in rows if r["ai"] != r["human"]]
    print(f"\n--- DIVERGENCES ({len(div)} of {len(rows)}) " + "-" * 62)
    if not div:
        print("  none — the two passes agree on every record.")
    else:
        print(f"  {'id':<8}{'tier':<20}{'panel':<14}{'band':<8}{'AI':<4}{'human':<6}note")
        for r in sorted(div, key=lambda r: (r["tier"], r["human_id"])):
            print(f"  {r['human_id']:<8}{r['tier']:<20}"
                  f"{r['state'] + ' ' + r['panel']:<14}{r['band']:<8}"
                  f"{r['ai']:<4}{r['human']:<6}{r['note'][:40]}")

    # ---------- partial merges ----------
    ai_pm = {r["human_id"] for r in rows if r["ai_pm"] == "yes"}
    hu_pm = {r["human_id"] for r in rows if r["human_pm"] == "yes"}
    print(f"\n--- PARTIAL MERGES " + "-" * 76)
    print(f"  AI flagged {len(ai_pm)}, human flagged {len(hu_pm)}, "
          f"both {len(ai_pm & hu_pm)}, AI only {len(ai_pm - hu_pm)}, "
          f"human only {len(hu_pm - ai_pm)}")

    # ---------- publishable ledger ----------
    LEDGER_OUT.parent.mkdir(parents=True, exist_ok=True)
    with io.open(LEDGER_OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["human_id", "sample_id", "state", "panel", "match_tier",
                    "dollar_band", "ai_verdict", "human_verdict", "agree",
                    "partial_merge_ai", "partial_merge_human"])
        for r in sorted(rows, key=lambda r: r["human_id"]):
            w.writerow([r["human_id"], r["sample_id"], r["state"], r["panel"],
                        r["tier"], r["band"], r["ai"], r["human"],
                        "yes" if r["ai"] == r["human"] else "no",
                        "yes" if r["human_id"] in ai_pm else "",
                        "yes" if r["human_id"] in hu_pm else ""])
    # Tolerate a redirected LEDGER_OUT (tests point it at a scratch dir): the file is
    # already written by here, so a path-display error must not mask a successful run.
    try:
        _shown = LEDGER_OUT.relative_to(ROOT)
    except ValueError:
        _shown = LEDGER_OUT
    print(f"\nPII-free ledger -> {_shown}")
    print("Commit it: it makes the agreement statistic re-derivable without the sample.")
    return 1 if full_bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
