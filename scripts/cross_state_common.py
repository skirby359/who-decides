"""Shared state enumeration + competitiveness helpers for the cross-state FEC
money analysis scripts (docs/cross-state-fec-money.md).

State-agnostic by design: the analysis region is discovered by globbing
``data/*_statewide.duckdb`` — any state whose statewide DB is on disk is
included — overridable with the ``CROSS_STATE_REGION`` env var (comma-separated
codes, e.g. ``WA,ID``). Adding a state needs NO edits here or in the analysis
scripts: load its ``data/<code>_statewide.duckdb`` (+ ``FEC_INFLOW_STATES=<code>``
for the shared inflow DB) and re-run.

The 2-letter code equals ``contributor_state`` / ``recipient_state`` for these
states, so no ``config/`` dependency is needed for the SQL filters.
"""
from __future__ import annotations

import glob
import json
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"


def region_states() -> list[tuple[str, str]]:
    """``[(CODE, statewide_db_abspath)]`` for the analysis region, sorted by code.

    ``CROSS_STATE_REGION`` (comma-separated codes) overrides discovery; otherwise
    every ``data/*_statewide.duckdb`` present on disk is included. Absolute paths
    are returned so callers work regardless of cwd.
    """
    override = os.environ.get("CROSS_STATE_REGION", "").strip()
    if override:
        codes = [c.strip().upper() for c in override.split(",") if c.strip()]
        pairs = [(c, str(DATA_DIR / f"{c.lower()}_statewide.duckdb")) for c in codes]
        return sorted(((c, p) for c, p in pairs if Path(p).exists()), key=lambda cp: cp[0])
    out = []
    for p in sorted(glob.glob(str(DATA_DIR / "*_statewide.duckdb"))):
        code = Path(p).stem.replace("_statewide", "").upper()
        out.append((code, p))
    return sorted(out, key=lambda cp: cp[0])


def region_codes() -> list[str]:
    return [c for c, _ in region_states()]


def region_sql(codes: list[str] | None = None) -> str:
    """SQL literal list of region codes, e.g. ``'WA','NY','TX','ID'``."""
    codes = codes if codes is not None else region_codes()
    return ",".join(f"'{c}'" for c in codes)


def broadly_funded_min(codes: list[str] | None = None) -> int:
    """Min # of region states for a "broadly funded" magnet = all but at most one.

    Replaces the old hardcoded ``>= 3`` / ``== 3`` thresholds so the "funded
    across the region" concept scales as states are added.
    """
    n = len(codes if codes is not None else region_codes())
    return max(1, n - 1)


def band(margin_abs: float) -> str:
    """Cook-style competitiveness band from the ABSOLUTE two-party margin (pts)."""
    if margin_abs < 5:
        return "Tossup"
    if margin_abs < 10:
        return "Lean"
    if margin_abs < 20:
        return "Likely"
    return "Solid"


def competitiveness_bands(states: list[tuple[str, str]] | None = None) -> dict:
    """``{(state, cd_id): (margin_abs, band)}`` from each state's latest Democratic
    congressional-district forecast.

    Reads ``forecast_predictions`` (party='Democratic', ``district_id LIKE 'cd%'``,
    latest ``as_of_date`` per district) from each state's statewide DB. States
    whose DB is locked or carries no ``cd`` rows are skipped, so the map contains
    whatever is available. This is the single copy of the logic that used to be
    duplicated inside each competitiveness script.
    """
    import duckdb

    states = states if states is not None else region_states()
    comp: dict = {}
    for st, f in states:
        try:
            c = duckdb.connect(f, read_only=True)
        except Exception:
            continue
        try:
            rows = c.execute(
                "WITH r AS (SELECT district_id, predicted_margin, "
                "ROW_NUMBER() OVER (PARTITION BY district_id ORDER BY as_of_date DESC) rn "
                "FROM forecast_predictions WHERE party='Democratic' AND district_id LIKE 'cd%') "
                "SELECT district_id, predicted_margin FROM r WHERE rn=1"
            ).fetchall()
        finally:
            c.close()
        for cd, m in rows:
            comp[(st, cd)] = (abs(float(m)), band(abs(float(m))))
    return comp


def write_json(name: str, obj) -> str:
    """Write ``obj`` as JSON to ``reports/<name>``; return the path.

    Replaces the stale per-session scratchpad paths several scripts hardcoded.
    """
    out_dir = REPO_ROOT / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / name
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, default=str)
    return str(out)
