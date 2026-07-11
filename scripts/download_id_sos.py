#!/usr/bin/env python3
"""Download + convert Idaho SoS / VoteIdaho.gov election returns into the
standard adapter schema, placed where the calendar-driven loader finds them
(``data/raw/id/<date_slug>/``; see
:func:`wa_analyzer.etl.election_results.load_all_results_adapter` + the
``id_sos`` adapter). Then::

    STATE=ID python main.py load --elections

Idaho publishes two incompatible bulk formats:
  * **2024** — a clean LONG-format precinct workbook ``raw_races_general.xlsx``:
    County, Precinct, RaceType, Race, Party, Candidate, Votes. Trivial map.
  * **2022 / 2020** — ``*_General_Canvass.zip`` bundles of PIVOTED precinct
    workbooks (one per race-group: Statewide / Legislative / Dist Judge), with a
    4-row stacked header (race-group / office / party / candidate) and county
    sub-header rows interleaved with precinct rows. Un-melted here.

Output is the schema ``id_sos`` expects (party carried in a ``Party`` column):
    Race, Candidate, Party, CountyCode, PrecinctCode, PrecinctName, Votes

Idempotent: skips a slug whose precinct.csv already exists unless --force.
Re-runnable. (download_results() in the adapter stays stubbed by design — this
out-of-band converter is the per-cycle scraper the adapter docstring refers to.)
"""
from __future__ import annotations

import argparse
import io
import re
import sys
import zipfile
from pathlib import Path

import httpx
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))          # for `import config...`
sys.path.insert(0, str(ROOT / "src"))  # for `import wa_analyzer...`
RAW = ROOT / "data" / "raw" / "id"
SRC = RAW / "_source"
_UA = {"User-Agent": "Mozilla/5.0"}

# Core partisan district race types we load for the forecast (president, U.S.
# House/Senate, and the 35 legislative districts). County/Local/Magistrate/
# State Measure are nonpartisan or non-district and dropped.
_KEEP_RACETYPES = {"Federal", "Congressional", "Legislative"}

# Recognized party tokens in the pivot 'party' header row. Used to reject false
# block detections: a real race block's party row carries these; a spurious one
# (a repeated county/precinct line mistaken for a header) carries digits/names.
_KNOWN_PARTIES = {
    "R", "REP", "REPUBLICAN", "D", "DEM", "DEMOCRATIC", "L", "LIB", "LIBERTARIAN",
    "C", "CON", "CONSTITUTION", "I", "IND", "INDEPENDENT", "NP", "NONPARTISAN",
    "W/I", "WRITE-IN",
}

# Primary slugs whose canvass names races by OFFICE only (party in a column),
# so each party's primary must be split into its own race (see main()). The 2024
# long file already carries the party in the race name and is excluded.
_PRIMARY_PARTY_SUFFIX_SLUGS = {"20220517", "20200519", "20180515", "20160517"}
_PARTY_FULL = {
    "REP": "Republican", "R": "Republican",
    "DEM": "Democratic", "D": "Democratic",
    "LIB": "Libertarian", "L": "Libertarian",
    "CON": "Constitution", "C": "Constitution",
}


def _county_code(name: str) -> str:
    """'Ada County' -> 'ADA' (matches config/states/id.py county keys)."""
    return re.sub(r"\s+County$", "", (name or "").strip(), flags=re.I).strip().upper()


def _valid_counties() -> set[str]:
    """The 44 real Idaho county codes — used to drop spurious 'county'
    sub-headers the pivot un-melt can pick up from odd statewide sheets."""
    from config.states.id import _ID_COUNTIES
    return set(_ID_COUNTIES.keys())


def _get(url: str) -> bytes:
    r = httpx.get(url, timeout=120, follow_redirects=True, headers=_UA)
    r.raise_for_status()
    return r.content


def _write_csv(df: pd.DataFrame, slug: str) -> Path:
    cols = ["Race", "Candidate", "Party", "CountyCode",
            "PrecinctCode", "PrecinctName", "Votes"]
    df = df[cols].copy()
    df = df[(df["Race"].str.strip() != "") & (df["Candidate"].str.strip() != "")]
    # Drop rows whose CountyCode isn't a real Idaho county (spurious sub-headers
    # the pivot un-melt occasionally picks up). No-op for the clean 2024 long file.
    valid = _valid_counties()
    df = df[df["CountyCode"].isin(valid)]
    # Collapse duplicate (Race, Candidate, County, Precinct) rows by SUMMING. Some
    # canvass sheets split one precinct's tally across several batches under a
    # single code (e.g. Boise County reports a separate '90 Absentee' line per
    # legislative district — Trump 432+505+492). The downstream election loader
    # dedups (precinct, candidate) results and would DROP the extra batches,
    # under-counting the race; pre-summing here preserves every ballot (recovers
    # the EXACT 2020 presidential total, 554,119/287,021). Single-batch precincts
    # (the overwhelming majority, and the entire clean 2024 long file) are a no-op.
    df["Votes"] = pd.to_numeric(df["Votes"], errors="coerce").fillna(0).astype(int)
    df = (df.groupby(["Race", "Candidate", "CountyCode", "PrecinctCode"],
                     as_index=False, sort=False)
            .agg({"Party": "first", "PrecinctName": "first", "Votes": "sum"}))
    df = df[cols]
    dest_dir = RAW / slug
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "precinct.csv"
    df.to_csv(dest, index=False, encoding="utf-8")
    return dest


# ---------------------------------------------------------------------------
# 2024 — clean long format
# ---------------------------------------------------------------------------

def convert_2024_long(xlsx_bytes: bytes) -> pd.DataFrame:
    df = pd.read_excel(io.BytesIO(xlsx_bytes), sheet_name=0, dtype=str)
    df.columns = [c.strip() for c in df.columns]
    df = df[df["RaceType"].isin(_KEEP_RACETYPES)].copy()
    out = pd.DataFrame({
        "Race": df["Race"].fillna("").str.strip(),
        "Candidate": df["Candidate"].fillna("").str.strip(),
        "Party": df["Party"].fillna("").str.strip(),
        "CountyCode": df["County"].map(_county_code),
        "PrecinctCode": df["Precinct"].fillna("").str.strip(),
        "PrecinctName": df["Precinct"].fillna("").str.strip(),
        "Votes": pd.to_numeric(df["Votes"], errors="coerce").fillna(0).astype(int),
    })
    return out


# ---------------------------------------------------------------------------
# 2022 / 2020 — pivoted canvass workbooks
# ---------------------------------------------------------------------------

def _unmelt_pivot_sheet(raw: pd.DataFrame) -> pd.DataFrame:
    """Un-melt one pivoted Idaho precinct workbook (read with header=None).

    Idaho stacks MANY pivot blocks VERTICALLY down a sheet — one per legislative
    district, or one per statewide office. Each block anchors on a candidate row
    (col 0 starts with 'Precinct'); reading upward from that row P:
      P-3 (ffill): race-group ('UNITED STATES', 'LEGISLATIVE DIST 1')
      P-2 (ffill): office ('SENATOR', 'ST SEN', 'ST REP A')
      P-1:         party per candidate column (DEM/REP/CON/LIB/IND/...)
      P:           'Precinct' + candidate names
      P+1..:       a county name alone (blank votes) OR a precinct row, until the
                   next block's header (≈ next Precinct row − 3 rows).
    """
    # Anchor row: col0 EXACTLY 'Precinct' (2022) or 'Counties' (2020 Federal).
    # Must be exact, not startswith — some counties (e.g. Clark) name precincts
    # 'PRECINCT #1', which startswith() mistook for block headers, cutting the
    # main block off early (the statewide-sheet under-capture) and spawning junk
    # blocks.
    pcts = [i for i in range(len(raw))
            if str(raw.iloc[i, 0]).strip().lower() in ("precinct", "counties")]
    if not pcts:
        return pd.DataFrame()

    records: list[dict] = []
    for k, p in enumerate(pcts):
        if p < 2:
            continue
        end = (pcts[k + 1] - 3) if k + 1 < len(pcts) else len(raw)
        end = max(end, p + 1)

        cand = raw.iloc[p]
        party = raw.iloc[p - 1]
        office = raw.iloc[p - 2].ffill()
        # Group label ('LEGISLATIVE DIST N' or a statewide office name) normally
        # sits at p-3, but some tabs (2022 'Leg Dist 11'/'12') shift it up one row,
        # leaving p-3 blank — then the race name loses its district number ('ST SEN'
        # instead of 'LEGISLATIVE DIST 11 ST SEN'). Scan upward from p-3 (bounded by
        # the previous block's anchor) for the first row carrying content in cols 1+.
        prev = pcts[k - 1] if k > 0 else -1
        group = pd.Series([""] * raw.shape[1])
        for gr in range(p - 3, prev, -1):
            if gr >= 0 and raw.iloc[gr, 1:].notna().any():
                group = raw.iloc[gr].ffill()
                break

        # Reject false blocks: a real race block's party row carries recognized
        # party tokens. A spurious 'Precinct'-matching row (e.g. a county/precinct
        # line) has digits/names there — skip it (this killed the 'CLARK N' /
        # numeric-party artifacts from the heterogeneous statewide sheets).
        ptoks = {str(party.iloc[ci]).strip().upper()
                 for ci in range(1, raw.shape[1]) if pd.notna(party.iloc[ci])}
        if not (ptoks & _KNOWN_PARTIES):
            continue

        cur_county = ""
        for _, row in raw.iloc[p + 1:end].iterrows():
            first = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
            if not first or first.lower() == "nan":
                continue
            fu = first.upper()
            # Skip explicit total rows ('STATE TOTAL', 'CO. TOTAL', ...).
            if "TOTAL" in fu:
                continue
            # County sub-header (blank vote cells). Strip the page-break
            # '(Continued)' suffix so continuation precincts attribute to the same
            # county (else they land under 'ADA (CONTINUED)' and get dropped by the
            # valid-county filter — the 2020 under-count). A 'STATEWIDE' header
            # marks the start of the trailing summary section that RE-LISTS every
            # precinct (the 2020 2x over-count) — stop the block there. NB: do not
            # skip rows merely ending ' COUNTY' — some precincts are named that way
            # (e.g. '001 N Blaine County').
            if row.iloc[1:].isna().all() and not first.isdigit():
                # Strip page-break continuation suffixes — '(Continued)' AND
                # ', cont.' / ', continued' (the 2022 statewide sheets use the
                # latter) — so continuation-page precincts attribute to the base
                # county instead of an invalid 'ADA, CONT.' that the valid-county
                # filter would drop (the statewide under-capture).
                cc = re.sub(r"[,(]\s*cont(?:inued)?\.?\s*\)?\s*$", "", fu,
                            flags=re.I).strip()
                if cc == "STATEWIDE":
                    break
                cur_county = cc
                continue
            for ci in range(1, raw.shape[1]):
                cn = str(cand.iloc[ci]).strip() if pd.notna(cand.iloc[ci]) else ""
                if not cn or cn.lower() == "nan":
                    continue
                v = row.iloc[ci]
                if pd.isna(v) or str(v).strip() == "":
                    continue
                grp = (str(group.iloc[ci]).strip()
                       if ci < len(group) and pd.notna(group.iloc[ci]) else "")
                off = str(office.iloc[ci]).strip() if pd.notna(office.iloc[ci]) else ""
                pty = str(party.iloc[ci]).strip() if pd.notna(party.iloc[ci]) else ""
                race = " ".join(t for t in (grp, off)
                                if t and t.lower() != "nan").strip()
                records.append({
                    "Race": race,
                    "Candidate": re.sub(r"\s*\(W/I\)\s*$", "", cn, flags=re.I).strip().upper(),
                    "Party": pty,
                    "CountyCode": cur_county,
                    "PrecinctCode": first,
                    "PrecinctName": first,
                    "Votes": pd.to_numeric(v, errors="coerce"),
                })
    out = pd.DataFrame.from_records(records)
    if not out.empty:
        out["Votes"] = out["Votes"].fillna(0).astype(int)
    return out


def _unmelt_2020_leg_sheet(raw: pd.DataFrame) -> pd.DataFrame:
    """Un-melt the 2020 legislative 'Sheet1' format (different from the per-tab
    2022 layout). Vertically stacked 'Leg. Dist. N' blocks (one per district per
    county-page); for each block at row k:
      k   : 'Leg. Dist. N' (col0) + office labels across candidate columns
            ('ST SEN','ST REP A','ST REP B'), sparse → ffill.
      k+1 : party-prefixed FIRST names ('D-Vera','R-Jim', ...).
      k+2 : LAST names ('Gadman','Woodward', ...).
      k+3..: county sub-header (blank votes) / precinct rows until the next block.
    Party = the single-letter prefix (D/R/...); the id_sos adapter maps it on load.
    """
    blocks = [i for i in range(len(raw))
              if re.match(r"leg\.?\s*dist", str(raw.iloc[i, 0]).strip(), re.I)]
    if not blocks:
        return pd.DataFrame()
    records = []
    for bi, k in enumerate(blocks):
        m = re.search(r"(\d+)", str(raw.iloc[k, 0]))
        if not m or k + 3 > len(raw):
            continue
        dist = int(m.group(1))
        end = blocks[bi + 1] if bi + 1 < len(blocks) else len(raw)
        office = raw.iloc[k].ffill()
        first, last = raw.iloc[k + 1], raw.iloc[k + 2]
        cur_county = ""
        for r in range(k + 3, end):
            v0 = str(raw.iloc[r, 0]).strip() if pd.notna(raw.iloc[r, 0]) else ""
            if not v0 or v0.lower() == "nan" or "TOTAL" in v0.upper():
                continue
            if raw.iloc[r, 1:].isna().all():
                cur_county = v0.upper()
                continue
            for ci in range(1, raw.shape[1]):
                fn = str(first.iloc[ci]).strip() if pd.notna(first.iloc[ci]) else ""
                ln = str(last.iloc[ci]).strip() if pd.notna(last.iloc[ci]) else ""
                fn = "" if fn.lower() == "nan" else fn
                ln = "" if ln.lower() == "nan" else ln
                if not fn and not ln:
                    continue
                val = pd.to_numeric(raw.iloc[r, ci], errors="coerce")
                if pd.isna(val):
                    continue
                party = ""
                pm = re.match(r"^([A-Za-z])-\s*(.*)$", fn)
                if pm:
                    party, fn = pm.group(1).upper(), pm.group(2).strip()
                off = str(office.iloc[ci]).strip() if pd.notna(office.iloc[ci]) else ""
                records.append({
                    "Race": f"LEGISLATIVE DIST {dist} {off}".strip(),
                    "Candidate": f"{fn} {ln}".strip().upper(),
                    "Party": party,
                    "CountyCode": cur_county,
                    "PrecinctCode": v0,
                    "PrecinctName": v0,
                    "Votes": val,
                })
    out = pd.DataFrame.from_records(records)
    if not out.empty:
        out["Votes"] = out["Votes"].fillna(0).astype(int)
    return out


def _convert_workbook(xl: pd.ExcelFile) -> pd.DataFrame:
    """Un-melt every partisan precinct sheet in one pivot workbook.

    Each workbook holds MANY pivot sheets — one per legislative district (2022:
    35 'Leg Dist N' tabs), per statewide office (US Sen, US Rep 1, Gov, ...), or
    all legislative districts stacked in a single sheet (2020/2018/2016, handled
    by the party-prefixed multi-block un-melt). Skip non-partisan tabs (judicial
    retention, ballot measures, voting-stats) and the COMBINED multi-office
    statewide tabs (2022 'Lt Gov & SoS' / 'SC & ST' / 'AG & SOPI'; 2018 'Gov to
    St Con' / 'St Treasurer to Superintendent'). Those stack several offices in
    one tab and the un-melt mis-attributes the trailing offices' candidates into
    the first office's race (the Lt-Gov field bled Scott Bedke et al. into race
    'GOVERNOR', doubling it). All are down-ballot, NON-forecast/NON-backtest
    offices — the single-office tabs (US Sen, US Rep, Gov, President) + the
    per-district legislative tabs carry every race the model actually reads.
    """
    frames = []
    for sheet in xl.sheet_names:
        s = sheet.lower()
        if any(k in s for k in ("amend", "stat", "measure")) or "&" in s or " to " in s:
            continue
        raw = xl.parse(sheet, header=None, dtype=str)
        frame = _unmelt_pivot_sheet(raw)
        if frame.empty:
            # Fall back to the 'Leg. Dist.' party-prefixed format (2020/2018/2016).
            frame = _unmelt_2020_leg_sheet(raw)
        frames.append(frame)
    frames = [f for f in frames if not f.empty]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def convert_pivot_zip(zip_bytes: bytes) -> pd.DataFrame:
    """Un-melt the Statewide + Legislative precinct workbooks from a canvass ZIP
    (Dist Judge is nonpartisan/retention — skipped)."""
    zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    frames = []
    for entry in zf.namelist():
        base = entry.lower().rsplit("/", 1)[-1]
        if entry.endswith("/") or not base.endswith((".xls", ".xlsx")):
            continue
        is_precinct = "precinct" in base or "pct" in base
        is_group = any(k in base for k in ("statewide", "stwd", "legislative", "leg"))
        excluded = any(k in base for k in ("county", "cnty", "stats", "judge"))
        if not (is_precinct and is_group) or excluded:
            continue
        frames.append(_convert_workbook(pd.ExcelFile(io.BytesIO(zf.read(entry)))))
    frames = [f for f in frames if not f.empty]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def convert_pivot_files(file_bytes: list[bytes]) -> pd.DataFrame:
    """Un-melt one or more STANDALONE pivot workbooks (2018/2016 = separate
    statewide + legislative .xls/.xlsx files, not a ZIP) and concatenate."""
    frames = [_convert_workbook(pd.ExcelFile(io.BytesIO(b))) for b in file_bytes]
    frames = [f for f in frames if not f.empty]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

# (slug, kind, source filename, source URL)
# Loaded + verified vs the SoS canvass: 2024 (president 68.8% two-party = actual;
# US House; legislative), 2022 (Governor Little 358,598 / Heidt 120,160 / Bundy
# 101,835 = EXACT; U.S. Senate 590,890; all 35 legislative districts), 2020
# (president Biden 287,021 / Trump 554,119 = EXACT; U.S. Senate; U.S. House —
# its 'Federal' sheet uses a 'Counties' anchor + a trailing 'Statewide' summary
# section that re-lists every precinct, now stopped at; legislative parsed via the
# party-prefixed two-row format). The single-office statewide tabs (US Sen, US Rep
# 1/2, Gov) + per-district legislative tabs all parse cleanly. KNOWN GAP: the
# COMBINED two-office 2022 statewide tabs ('Lt Gov & SoS', 'SC & ST', 'AG & SOPI')
# are SKIPPED — the single-block un-melt mis-attributes the second office's
# candidates into the first office's race; these are down-ballot, non-forecast,
# non-backtest offices, so they're dropped rather than mis-loaded. 2018/2016
# (archive XLS per race) are a fourth format, not started.
# 2018/2016 live on the legacy archive host as STANDALONE precinct workbooks
# (statewide + legislative as separate files, not a ZIP) — kind 'files', with
# parallel filename/URL lists. Same pivot layout as 2020/2022 (statewide:
# 'Counties' anchor; legislative: party-prefixed 'Leg. Dist.' two-row format),
# so the shared un-melt handles them. Both predate the 2022 redistricting, so
# they carry NO 2026-forecast weight (boundary filter); 2016 (a presidential
# cycle) adds within-cycle backtest cells, 2018 (midterm, no president) is
# dataset completeness only.
_ARCH = "https://archive.sos.idaho.gov/ELECT/results/"
PLACEMENTS = [
    ("20241105", "long", "2024_raw_races.xlsx",
     "https://sos.idaho.gov/elections/data/results/2024/raw_races_general.xlsx"),
    ("20221108", "pivot", "2022_General_Canvass.zip",
     "https://sos.idaho.gov/elections/data/results/2022/2022_General_Canvass.zip"),
    ("20201103", "pivot", "2020_General_Canvass.zip",
     "https://sos.idaho.gov/elections/data/results/2020/2020_General_Canvass.zip"),
    ("20181106", "files",
     ["2018_stwd.xls", "2018_leg.xls"],
     [_ARCH + "2018/General/18Gen_Stwd_pct.xls",
      _ARCH + "2018/General/18Gen_leg_pct.xls"]),
    ("20161108", "files",
     ["2016_stwd.xlsx", "2016_leg.xlsx"],
     [_ARCH + "2016/General/16gen_stwd_pct.xlsx",
      _ARCH + "2016/General/16gen_leg_pct.xlsx"]),
    # --- Closed partisan PRIMARIES (third Tuesday in May). Same bulk formats as
    # the generals above; R/D/minor contests are separate races in the canvass.
    ("20240521", "long", "2024_raw_races_primary.xlsx",
     "https://sos.idaho.gov/elections/data/results/2024/raw_races_primary.xlsx"),
    ("20220517", "pivot", "2022_Primary_Canvass.zip",
     "https://sos.idaho.gov/elections/data/results/2022/2022_Primary_Canvass.zip"),
    ("20200519", "pivot", "2020_Primary_Canvass.zip",
     "https://sos.idaho.gov/elections/data/results/2020/2020_Primary_Canvass.zip"),
    ("20180515", "files",
     ["2018_pri_stwd.xls", "2018_pri_leg.xls"],
     [_ARCH + "2018/Primary/18pri_stwd_pct.xls",
      _ARCH + "2018/Primary/18pri_leg_pct.xls"]),
    ("20160517", "files",
     ["2016_pri_stwd.xlsx", "2016_pri_leg.xlsx"],
     [_ARCH + "2016/Primary/16pri_stwd_pct.xlsx",
      _ARCH + "2016/Primary/16pri_leg_pct.xlsx"]),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force", action="store_true", help="re-convert even if precinct.csv exists")
    ap.add_argument("--only", help="only this slug (e.g. 20241105)")
    args = ap.parse_args()
    SRC.mkdir(parents=True, exist_ok=True)

    for slug, kind, fname, url in PLACEMENTS:
        if args.only and slug != args.only:
            continue
        dest = RAW / slug / "precinct.csv"
        if dest.exists() and not args.force:
            print(f"{slug}: precinct.csv exists — skip (use --force).")
            continue
        # 'files' carries parallel filename/URL lists; the others a single string.
        fnames = fname if isinstance(fname, list) else [fname]
        urls = url if isinstance(url, list) else [url]
        blobs = []
        failed = False
        for fn_, u_ in zip(fnames, urls):
            src_path = SRC / fn_
            if not src_path.exists() or args.force:
                print(f"{slug}: downloading {fn_} ...")
                try:
                    src_path.write_bytes(_get(u_))
                except Exception as e:
                    print(f"{slug}: DOWNLOAD FAILED ({e}) — skipping.")
                    failed = True
                    break
            blobs.append(src_path.read_bytes())
        if failed:
            continue
        if kind == "long":
            df = convert_2024_long(blobs[0])
        elif kind == "files":
            df = convert_pivot_files(blobs)
        else:
            df = convert_pivot_zip(blobs[0])
        if df.empty:
            print(f"{slug}: converter produced 0 rows — skipping.")
            continue
        # PRIMARY party-suffix: the pivot/archive canvasses name races by OFFICE
        # only ("LEGISLATIVE DIST 1 ST SEN"), carrying party in a column — so a
        # seat's Republican and Democratic primaries would merge into one race.
        # Append the (correct) party to the race name so each party's primary is a
        # distinct contest. (The 2024 long file already names races by party, so it
        # is excluded.)
        if slug in _PRIMARY_PARTY_SUFFIX_SLUGS:
            suffix = df["Party"].str.upper().map(_PARTY_FULL).fillna(df["Party"])
            df = df.copy()
            df["Race"] = df["Race"].str.rstrip() + " - " + suffix
        out = _write_csv(df, slug)
        print(f"{slug}: wrote {len(df):,} rows -> {out.relative_to(ROOT)} "
              f"({df['Race'].nunique()} races, {df['CountyCode'].nunique()} counties, "
              f"{df['PrecinctCode'].nunique()} precincts)")


if __name__ == "__main__":
    main()
