"""Total resident population by state, for the money paper's per-capita cut, pinned to a CSV.

WHY THIS EXISTS. `cross-state-fec-money.md` §2 divides each state's federal donor count by its
population to claim Washington has the broadest participation per capita. The donor counts are
derived and asserted by `verify_cross_state_money.py`'s `outflow()`; the DENOMINATORS were the
only figures in that section external to every database in this repo, which is why §2 sat
"named, not gated" on the coverage audit's backlog with exactly this fix prescribed: pin them
the way `acs_cvap_by_state.py` pins CVAP, then the section is closeable.

WHY A PIN AND NOT A PER-RUN FETCH. Same reason as the CVAP benchmark. The four states are only
comparable if every one is measured against the same ACS release; a per-run fetch would let one
state's denominator move to a newer vintage while the others stayed put, and the published
percentages would drift with nothing downstream saying so. Re-fetching is a deliberate act:
pass `--force`, and expect §2's percentages to move.

FOUR STATES, NOT THREE. `acs_cvap_by_state.py` covers WA/NY/ID because those are the states with
an individual voter file loaded. This paper's federal money layer covers Texas too, so TX is
included here. The two pins are therefore NOT interchangeable and neither is a superset of the
other — different universes (CVAP by age cohort vs total residents) for different sections.

TOTAL RESIDENTS IS THE PAPER'S OWN STATED BASIS, and it is a weaker denominator than
voting-eligible adults: it counts children and non-citizens, so every state's participation rate
is biased downward, unevenly. The paper says so in §2's objection block rather than hiding it.
Do not quietly substitute CVAP here to make the rates look better — that would change a
published claim's meaning while leaving its wording intact.

Table B01003 (Total Population) publishes the single figure this needs, so no bracket arithmetic
is done and none is needed.

Needs a free Census API key in CENSUS_API_KEY (env or repo .env).

Run:  python scripts/acs_state_population.py [--vintage 2024] [--force]
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "reference"

_VAR = "B01003_001E"

# The four states in the paper's federal money layer. Ordered as the paper orders them.
STATES = {"WA": "53", "NY": "36", "TX": "48", "ID": "16"}


def load_key() -> str:
    key = os.environ.get("CENSUS_API_KEY")
    if key:
        return key.strip()
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            m = re.match(r"\s*CENSUS_API_KEY\s*=\s*(.+)", line)
            if m:
                return m.group(1).strip().strip('"').strip("'")
    raise SystemExit("CENSUS_API_KEY not set (env or .env). Sign up: "
                     "https://api.census.gov/data/key_signup.html")


def fetch(vintage: int, fips: str, key: str) -> int:
    url = (f"https://api.census.gov/data/{vintage}/acs/acs5?get={_VAR}"
           f"&for=state:{fips}&key={key}")
    with urllib.request.urlopen(url, timeout=60) as resp:
        data = json.load(resp)
    return int(dict(zip(data[0], data[1]))[_VAR])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vintage", type=int, default=2024,
                    help="ACS 5-year end year (default 2024 = the 2020-2024 release)")
    ap.add_argument("--force", action="store_true",
                    help="overwrite an existing pin. Moves every §2 percentage.")
    args = ap.parse_args()

    out = OUT_DIR / f"state_population_acs{args.vintage}.csv"
    if out.exists() and not args.force:
        print(f"{out.relative_to(ROOT)} already exists — not re-fetching.")
        print("  A pin is meant to be stable; use --force if you mean to move it.")
        return 0

    key = load_key()
    rows = []
    print(f"ACS {args.vintage - 4}-{args.vintage} 5-year, table B01003 "
          f"(total population):\n")
    for st, fips in STATES.items():
        pop = fetch(args.vintage, fips, key)
        print(f"  {st}  {pop:>12,}")
        rows.append({"state": st, "population": pop,
                     "acs_vintage": args.vintage, "table": "B01003"})

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"\npinned -> {out.relative_to(ROOT)}  ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
