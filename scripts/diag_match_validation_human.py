"""Draw a blinded HUMAN-review sample from the records the AI already rated.

The 2026-07-27 match-precision pass (docs/reference/match_validation_verdicts_2026-07-27.csv)
was adjudicated by the AI assistant under a blinding protocol. It is seeded, published and
pre-specified, but it is single-rater and by the same system that produced the analysis.
This draws 150 records for an independent human rater so that **inter-rater agreement and
Cohen's kappa are computable** — which is what actually validates or breaks that pass.

EVERY ROW IS A RE-RATE. All 150 are drawn from the 480 sample_ids in the published ledger,
never freshly from the panels. A fresh sample would carry no anchoring risk but would also
yield no agreement statistic, so it could not validate anything.

COMPOSITION — forced inclusions first, then a weighted fill:

  all `partial_merge` records                8   the dollar-attribution residue
  all `NP` + `U` records                     5   the judgment calls the AI found hardest
  STRICT_ZIP5_FULL                          75   the tier whose 100% underpins the paper
  STRICT_ZIP5                               25   47.9%
  RELAXED_ZIP3_MID                          25   50.4%
  STRICT_ZIP5_MID                           25   71.7%

The four tier figures are TOTALS and include the forced inclusions, so they sum to 150.
Half the sample sits on the full-name key deliberately: that block is what either
confirms or breaks the 100% the paper now rests on.

Within the full-name block, top-decile and rest are split evenly — the ledger holds exactly
60 of each and all 120 were rated Y, so a skew there would waste the block. Within each
weak-tier block the fill is balanced across the AI's Y and NC verdicts so the human is not
handed a base rate: an all-NC block would leak the answer through the evidence itself. Each
state is forced to appear so both panel-specific error modes (Idaho Sunshine organisations,
WA PDC name-order) are represented.

BLINDING — the differences from the AI pass matter:

  * **Fresh `H####` ids, never the `S####` ids.** The `S####` ids are published in the
    committed verdict ledger, so reusing them would let the rater look up the AI's answer
    in thirty seconds. This is the single most important difference.
  * No state, panel, tier or dollar band. No AI verdict, error mode or partial-merge flag.
  * Deterministic shuffle BEFORE id assignment, so id order carries no stratum signal.
  * A distinct seed from the AI sampler's, so selection is not correlated with draw order.
  * Evidence rows are copied VERBATIM from the AI pass's file rather than re-queried, so
    the human sees byte-identical evidence. That is what makes the agreement statistic
    mean what it claims: a divergence is a difference in judgement, never a difference in
    what was shown.

As in the AI pass, the rater can partly infer the tier from the evidence itself, because
the tier IS a fact about how the two names relate. That is disclosed, not engineered away.

PII. Evidence and key carry voter and donor names; both go to gitignored data/validation/
and must never be committed. Only counts are printed. The eventual verdicts are publishable
once stripped, as the AI pass's were.

Run:  python scripts/diag_match_validation_human.py
"""
from __future__ import annotations

import csv
import hashlib
import io
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUTDIR = DATA / "validation"
LEDGER = ROOT / "docs" / "reference" / "match_validation_verdicts_2026-07-27.csv"
AI_KEY = OUTDIR / "match_validation_stratified_key.csv"

EVIDENCE = OUTDIR / "match_validation_human.csv"
KEYFILE = OUTDIR / "match_validation_human_key.csv"
INSTRUCTIONS = OUTDIR / "match_validation_human_INSTRUCTIONS.md"

# Distinct from the AI sampler's "2026-07-27" so the two draws are uncorrelated.
SEED = "2026-07-27-human"

TARGET = 150
# Per-tier TOTALS (not additions): the forced inclusions above are absorbed into these
# blocks, so the targets sum to TARGET rather than to TARGET minus the forced count.
TIER_FILL = {"STRICT_ZIP5_FULL": 75, "STRICT_ZIP5": 25,
             "RELAXED_ZIP3_MID": 25, "STRICT_ZIP5_MID": 25}

INSTRUCTIONS_TEXT = """# Match-validation review — instructions

You are checking whether a **voter registration record** and the **campaign contribution
record(s)** linked to it belong to the **same human being**.

Open `match_validation_human.csv`, fill the `verdict` column for all 150 rows, and add a
`notes` comment wherever it helps. Nothing else in the file should change.

## The four verdicts

| code | means |
|---|---|
| `Y`  | **Same person.** Includes nicknames and diminutives (Maggie/Margaret, Chuck/Charles, Debbie/Deborah, Tom/Thomas), initial-plus-middle forms (`ELY, J ROYE` for a voter *Jane Roye Ely*), someone going by their middle name (voter *E Eugene Matthews*, donor `MATTHEWS, EUGENE`), spelling variants (Randal/Randall), and a joint gift that names the voter (`PEDERSEN, KEN & TRUDY` for voter *Kenneth Pedersen*). |
| `NC` | **Confirmed different person.** The donor is clearly someone else: a different given name at the same surname and ZIP (voter *Michael Hale*, donor `HALE MATTHEW R` — almost always a relative), an organisation (`MARSHALL MATERIALS GROUP LLC`, `SIMPSON FOR CONGRESS`, `JOHNSON LIVING TRUST`), or a name that has clearly been parsed in the wrong order. |
| `NP` | **Probably different, but not certain.** Use when the names are close enough that you cannot rule out the same person, but you lean against it. |
| `U`  | **Cannot judge from what is here.** |

**`U` means the donor record does not carry enough detail to decide — it does not mean
"I'm unsure".** If you lean one way, use `Y`, `NC` or `NP`. Expect `U` to be rare.

## The columns

- `voter_first` / `voter_middle` / `voter_last` / `voter_zip5` / `voter_city` — the
  registration record.
- `donor_names` — every distinct contributor-name string that was linked to this voter,
  pipe-separated. Several spellings of one person is normal and is not itself a problem.
- `donor_distinct_first_names` — how many different first names appear among those
  strings. **Greater than 1 is itself evidence**: it means the link pulled in more than
  one person's giving.
- `donor_zip5s` — the ZIP(s) on the contributions. These can legitimately differ from the
  voter's ZIP (home vs work, a PO box, or a move).
- `matched_gifts` / `matched_total` — what was attributed to this voter.
- `donor_rows_refound` / `donor_total_refound` — a re-derivation of the donor side.
  **These can legitimately differ from `matched_*`** and a difference is not a defect.
- `partial_merge` — tick `yes` if the voter genuinely *is* one of the donors but the
  linked total clearly also includes **someone else's** gift (a spouse's, or a joint
  filing). This is different from `NC`: the person is right, some of the money is not.

## Two cases that come up often

**A spouse or relative rather than the voter.** The deciding question is whether the
voter's OWN name appears in `donor_names` at all.

- Only a *different given name* at the same surname — voter *Michael Hale*, donor
  `HALE MATTHEW R` — is **`NC`**. Do not soften this to `NP`: a different given name at a
  shared surname and ZIP is a confirmed different person, and it is the commonest real error.
- The voter's name **and** someone else's both appear (watch `donor_distinct_first_names`
  > 1) — e.g. `PRICE, ROGER | PRICE, ROSE-MARIE` for voter *Rose Marie Price* — is
  **`Y`**, and tick **`partial_merge`**. The person is right; some of the money is not.
- A joint filing that names the voter (`PEDERSEN, KEN & TRUDY`, `MOORE, SHIRLEY & DON`,
  `MR AND MRS` forms) is **`Y`** + **`partial_merge`**.

**An LLC, trust or company — even one that looks like a single person.** Mark **`NC`**
and add a note. The unit here is a natural person on the voter roll; an LLC is a distinct
filer and its contribution is the entity's money, not that individual's personal giving.
This holds even when a human's name is embedded in it — `ROY LEWIS EIGUREN LLC`,
`JOHNSON LIVING TRUST`, `TAYLOR CHEVROLET CADILLAC` are all `NC`.

If a specific row feels genuinely 50/50 either way, **`NP` with a note** is better than a
forced verdict you do not believe. The note is what lets it be looked at again.

## Please

- Judge each row only on what is in that row. **Do not look anything up** — not the voter
  file, not FEC or state disclosure sites, not other rows.
- Row order is random and carries no information.
- There is no target rate. Some blocks may be mostly one verdict and some mixed; do not
  try to balance your answers.

When every row has a verdict, save the file in place.
"""


def load_ledger() -> dict[str, dict]:
    with io.open(LEDGER, encoding="utf-8-sig") as fh:
        return {r["sample_id"]: r for r in csv.DictReader(fh)}


def load_ai_key() -> dict[str, dict]:
    with io.open(AI_KEY, encoding="utf-8-sig") as fh:
        return {r["sample_id"]: r for r in csv.DictReader(fh)}


def stable(sid: str) -> str:
    return hashlib.md5((sid + SEED).encode()).hexdigest()


def pick(pool: list[dict], n: int) -> list[dict]:
    """Deterministic pick of n, balanced across AI verdict then state.

    Balancing on verdict keeps the human from being handed a base rate; balancing on
    state keeps both panel-specific error modes in view.
    """
    if n <= 0 or not pool:
        return []
    buckets: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in pool:
        buckets[(r["verdict"], r["state"])].append(r)
    for b in buckets.values():
        b.sort(key=lambda r: stable(r["sample_id"]))
    # Round-robin across (verdict, state) buckets, largest first, so the result is
    # balanced rather than dominated by whichever bucket happens to be biggest.
    order = sorted(buckets, key=lambda k: (-len(buckets[k]), k))
    out: list[dict] = []
    while len(out) < n and any(buckets[k] for k in order):
        for k in order:
            if buckets[k] and len(out) < n:
                out.append(buckets[k].pop(0))
    return out


def main() -> int:
    if not LEDGER.exists() or not AI_KEY.exists():
        print(f"!! need both {LEDGER.name} (committed) and {AI_KEY.name} "
              f"(gitignored; re-run diag_match_validation_stratified.py)")
        return 1

    ledger, aikey = load_ledger(), load_ai_key()
    rows = [dict(L) for sid, L in ledger.items() if sid in aikey]
    ai_ev = OUTDIR / "match_validation_stratified.csv"
    if not ai_ev.exists():
        print(f"!! {ai_ev.name} missing — re-run diag_match_validation_stratified.py")
        return 1

    # ---- selection ----
    chosen: dict[str, dict] = {}
    forced_partial = [r for r in rows if r.get("partial_merge") == "yes"]
    forced_hard = [r for r in rows if r["verdict"] in ("NP", "U")]
    for r in forced_partial + forced_hard:
        chosen[r["sample_id"]] = r
    print(f"forced: {len(forced_partial)} partial-merge, {len(forced_hard)} NP/U "
          f"-> {len(chosen)} unique")

    for tier, want in TIER_FILL.items():
        have = sum(1 for r in chosen.values() if r["match_tier"] == tier)
        pool = [r for r in rows
                if r["match_tier"] == tier and r["sample_id"] not in chosen]
        if tier == "STRICT_ZIP5_FULL":
            # Every full-name record is Y, so balance on dollar band instead.
            top = pick([r for r in pool if r["dollar_band"] == "top10"],
                       max(0, (want - have + 1) // 2))
            rest = pick([r for r in pool if r["dollar_band"] == "rest"],
                        max(0, want - have - len(top)))
            take = top + rest
        else:
            take = pick(pool, max(0, want - have))
        for r in take:
            chosen[r["sample_id"]] = r
        print(f"  {tier:20} target {want:>3}  forced-in {have}  added {len(take):>3}"
              f"  -> {sum(1 for r in chosen.values() if r['match_tier'] == tier):>3}")

    sel = list(chosen.values())
    if len(sel) != TARGET:
        print(f"  note: selected {len(sel)} (target {TARGET}) — pools exhausted or "
              f"forced inclusions overlap the fill")

    # ---- shuffle, THEN assign opaque ids ----
    sel.sort(key=lambda r: stable(r["sample_id"] + "shuffle"))
    for i, r in enumerate(sel, 1):
        r["human_id"] = f"H{i:04d}"

    # ---- evidence: copied verbatim from the AI pass's file ----
    # Deliberately NOT re-queried. Copying guarantees the human sees byte-identical
    # evidence, which is what makes the agreement statistic mean what it claims: any
    # divergence is a difference in judgement, never a difference in what was shown.
    ai_rows = {}
    with io.open(ai_ev, encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            ai_rows[r["sample_id"]] = r
    missing = [r["sample_id"] for r in sel if r["sample_id"] not in ai_rows]
    if missing:
        print(f"!! {len(missing)} selected ids absent from {ai_ev.name}; "
              f"re-run the AI sampler to regenerate it")
        return 1

    ev_cols = ["human_id", "voter_first", "voter_middle", "voter_last", "voter_zip5",
               "voter_city", "matched_gifts", "matched_total", "donor_names",
               "donor_zip5s", "donor_distinct_first_names", "donor_rows_refound",
               "donor_total_refound", "partial_merge", "verdict", "notes"]
    OUTDIR.mkdir(parents=True, exist_ok=True)
    with io.open(EVIDENCE, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=ev_cols, extrasaction="ignore")
        w.writeheader()
        for r in sel:
            src = ai_rows[r["sample_id"]]
            w.writerow({**{c: src.get(c, "") for c in ev_cols},
                        "human_id": r["human_id"], "partial_merge": "",
                        "verdict": "", "notes": ""})

    with io.open(KEYFILE, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["human_id", "sample_id", "state", "panel", "match_tier",
                    "dollar_band", "ai_verdict", "ai_error_mode", "ai_partial_merge"])
        for r in sel:
            w.writerow([r["human_id"], r["sample_id"], r["state"], r["panel"],
                        r["match_tier"], r["dollar_band"], r["verdict"],
                        r.get("error_mode", ""), r.get("partial_merge", "")])

    io.open(INSTRUCTIONS, "w", encoding="utf-8", newline="").write(INSTRUCTIONS_TEXT)

    print(f"\nwrote {len(sel)} rows")
    print(f"  blinded evidence -> {EVIDENCE}")
    print(f"  instructions     -> {INSTRUCTIONS}")
    print(f"  key (DO NOT SHOW THE RATER) -> {KEYFILE}")
    print("  all three are under gitignored data/validation/ and carry PII.")
    print("\ncomposition actually achieved (counts only):")
    for label, keyf in (("tier", lambda r: r["match_tier"]),
                        ("state x panel", lambda r: f"{r['state']} {r['panel']}"),
                        ("dollar band", lambda r: r["dollar_band"]),
                        ("AI verdict", lambda r: r["verdict"])):
        print(f"  by {label}:")
        for k, n in sorted(Counter(keyf(r) for r in sel).items(), key=lambda x: -x[1]):
            print(f"    {k:34} {n:>4}")
    print(f"  partial-merge forced in: "
          f"{sum(1 for r in sel if r.get('partial_merge') == 'yes')}")
    print("\nNEXT: the human fills `verdict` (and ticks `partial_merge`), then")
    print("      python scripts/score_match_validation_human.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
