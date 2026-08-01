"""A12 — SHA-256 digests of the source files the donor paper's panels are built from.

Purpose: a later reconstruction can prove it started from the same inputs. The paper cites each
of these by name and retrieval date; a digest turns that citation into something checkable.

Emits a markdown table to stdout for pasting into the methods supplement, and records size and
modification time alongside each digest so a mismatch can be diagnosed rather than merely
detected.

Two absences are deliberate and are printed rather than hidden.

  * **FEC bulk files are not retained.** `load-fec-contributions-bulk` streams roughly 30 GB
    per cycle and deletes each after loading unless `--keep-files` is passed, so there is
    nothing local to hash. They are re-downloadable from the Commission and are identified by
    cycle rather than by digest; the supplement says so.
  * **Idaho's voter export is a single combined file.** The state ships registration and
    participation together, so there is no separate roll file to hash.

    PYTHONPATH=src python scripts/source_checksums.py

Read-only.
"""
from __future__ import annotations

import hashlib
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

# (label, path relative to data/raw, what the paper calls it)
SOURCES = [
    ("WA voter file",
     "vrdb/20260401_VRDB_Extract.txt",
     "WA SoS standard VRDB extract, April 2026 (requested 2026-04-08)"),
    ("WA voting history 2023–2024",
     "vrdb/2023-2024_Voting_History.txt",
     "participation records feeding the turnout cut"),
    ("WA voting history 2021–2022",
     "vrdb/2021-2022_Voting_History.txt",
     "participation records feeding the turnout cut"),
    ("NY voter file",
     "ny/ALLNYVOTERS20260629.zip",
     "NYSVOTER FOIL production dated 2026-06-29"),
    ("NY state contributions",
     "ny/Campaign_Finance_Disclosure_Reports_Contributions__Beginning_1999_20260605.csv",
     "NYSBOE dataset 4j2b-6a2j, retrieved 2026-06-05"),
    ("ID voter + history",
     "id/id_statewide_voter_history_20260629.csv",
     "ID SoS statewide list under Idaho Code § 34-437A(3), received 2026-07-01"),
    ("ID Sunshine contributions 2024",
     "id/_source/id_2024_TCON.csv", "Idaho Sunshine transaction export"),
    ("ID Sunshine contributions 2025",
     "id/_source/id_2025_TCON.csv", "Idaho Sunshine transaction export"),
]


def sha256(path: Path, chunk: int = 1 << 22) -> tuple[str, float]:
    h = hashlib.sha256()
    t0 = time.monotonic()
    with path.open("rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest(), time.monotonic() - t0


def main() -> None:
    print("| source | file | bytes | SHA-256 |")
    print("|---|---|--:|---|")
    missing = []
    for label, rel, _desc in SOURCES:
        p = RAW / rel
        if not p.exists():
            missing.append((label, rel))
            continue
        digest, secs = sha256(p)
        size = p.stat().st_size
        print(f"| {label} | `{rel}` | {size:,} | `{digest}` |")
        print(f"<!-- hashed in {secs:.1f}s -->", flush=True)

    if missing:
        print()
        print("**Not hashed — absent locally:**")
        for label, rel in missing:
            print(f"- {label} (`{rel}`)")

    print()
    print("**FEC bulk individual-contribution files are not hashed.** The loader streams roughly")
    print("30 GB per cycle and deletes each file after loading unless `--keep-files` is given, so")
    print("no local copy survives. They are re-downloadable from the Commission and are identified")
    print("by cycle (2018 through 2026) rather than by digest.")


if __name__ == "__main__":
    main()
