"""Known election dates per state.

WA dates double as URL slugs for results.vote.wa.gov (see the URL helpers
below). NY has no canonical results-export URL — its slugs are identifiers
only: they name the per-election folder where placed OpenElections files
live (``data/raw/ny/<slug>/``) and supply the election_date/type/year stamped
into the DB when loading. Use :func:`get_elections` to fetch the list for the
active (or a named) state; WA consumers may keep importing ``ELECTIONS``.
"""

from dataclasses import dataclass


@dataclass
class ElectionInfo:
    date_slug: str  # YYYYMMDD format used in URLs
    name: str
    election_type: str  # 'primary', 'general', 'special'
    year: int


# WA elections, newest first. The date_slug is both the URL slug and the
# votewa.gov ``publicElectionId``.
#
# TWO SOURCES, split at 2026. Through 20251104 the SoS published static
# CSVs at results.vote.wa.gov (URL helpers below); from 20260804 that path
# 404s and results come from the results.votewa.gov JSON export instead --
# see etl/wa_sos_json.py. WaSosAdapter.download_results tries the CSVs and
# falls back to the export, so both eras load through the same pipeline.
ELECTIONS = [
    # 2026 -- votewa.gov JSON export (no CSV exists for these)
    ElectionInfo("20261103", "2026 General Election", "general", 2026),
    ElectionInfo("20260804", "2026 Primary Election", "primary", 2026),
    # 2025
    ElectionInfo("20251104", "2025 General Election", "general", 2025),
    # 2024
    ElectionInfo("20241105", "2024 General Election", "general", 2024),
    ElectionInfo("20240806", "2024 Primary Election", "primary", 2024),
    # 2023
    ElectionInfo("20231107", "2023 General Election", "general", 2023),
    ElectionInfo("20230801", "2023 Primary Election", "primary", 2023),
    # 2022
    ElectionInfo("20221108", "2022 General Election", "general", 2022),
    ElectionInfo("20220802", "2022 Primary Election", "primary", 2022),
    # 2021
    ElectionInfo("20211102", "2021 General Election", "general", 2021),
    ElectionInfo("20210803", "2021 Primary Election", "primary", 2021),
    # 2020
    ElectionInfo("20201103", "2020 General Election", "general", 2020),
    ElectionInfo("20200804", "2020 Primary Election", "primary", 2020),
    # 2019
    ElectionInfo("20191105", "2019 General Election", "general", 2019),
    ElectionInfo("20190806", "2019 Primary Election", "primary", 2019),
    # 2018
    ElectionInfo("20181106", "2018 General Election", "general", 2018),
    ElectionInfo("20180807", "2018 Primary Election", "primary", 2018),
    # 2017
    ElectionInfo("20171107", "2017 General Election", "general", 2017),
    ElectionInfo("20170801", "2017 Primary Election", "primary", 2017),
    # 2016
    ElectionInfo("20161108", "2016 General Election", "general", 2016),
    ElectionInfo("20160802", "2016 Primary Election", "primary", 2016),
]

SOS_RESULTS_BASE_URL = "https://results.vote.wa.gov/results"


def get_precinct_csv_url(date_slug: str) -> str:
    """Build the URL for the AllStatePrecincts CSV export."""
    return f"{SOS_RESULTS_BASE_URL}/{date_slug}/export/{date_slug}_AllStatePrecincts.csv"


def get_export_page_url(date_slug: str) -> str:
    """Build the URL for the export page (to check availability)."""
    return f"{SOS_RESULTS_BASE_URL}/{date_slug}/export.html"


# New York general elections (first Tuesday after the first Monday in
# November). These cover the presidential PVI cycles (2016/2020/2024) and the
# gubernatorial cycles (2018/2022, plus the 2026 forecast target). NY primaries
# (4th Tuesday in June, with periodic court-ordered splits) are intentionally
# omitted until partisan-primary handling lands in Phase 2 — exact historical
# NY primary dates have varied and are added when that signal is built.
NY_ELECTIONS = [
    ElectionInfo("20261103", "2026 General Election (Governor)", "general", 2026),
    ElectionInfo("20241105", "2024 General Election (President)", "general", 2024),
    ElectionInfo("20221108", "2022 General Election (Governor)", "general", 2022),
    ElectionInfo("20201103", "2020 General Election (President)", "general", 2020),
    ElectionInfo("20181106", "2018 General Election (Governor)", "general", 2018),
    ElectionInfo("20161108", "2016 General Election (President)", "general", 2016),
    # Added to deepen the governor backtest (n=2 → n=3): 2014 governor (Cuomo,
    # a Republican-wave midterm where the D still won ~57% two-party) + its 2012
    # presidential PVI pairing. (2010 has only 2-county OpenElections coverage —
    # not loaded.)
    ElectionInfo("20141104", "2014 General Election (Governor)", "general", 2014),
    ElectionInfo("20121106", "2012 General Election (President)", "general", 2012),
]


# Texas general elections (first Tuesday after the first Monday in November).
# Data source = Texas Legislative Council Capitol Data Portal (canvass-grade VTD
# returns, all 254 counties 2016-2024; see the tlc_capitol_tx adapter). These
# cover:
#   - Presidential PVI: 2016, 2020, 2024
#   - R-INCUMBENCY test (the reason TX is the 3rd state): Abbott (R-inc) governor
#     2018 + 2022; Cruz (R-inc) U.S. Senate 2018; Cornyn (R-inc) U.S. Senate 2020.
# 2024 is clean at TLC (replaces the prior "NYT-2024 + spatial-join" plan; TLC
# also publishes a per-CD 2024 report on the enacted 2025 congressional map). The
# 2026 general is the forecast target (no results file yet). TX primaries (March,
# with May runoffs) are omitted until partisan-primary handling is wired for TX.
TX_ELECTIONS = [
    ElectionInfo("20261103", "2026 General Election (Governor)", "general", 2026),
    ElectionInfo("20241105", "2024 General Election (President)", "general", 2024),
    ElectionInfo("20221108", "2022 General Election (Governor)", "general", 2022),
    ElectionInfo("20201103", "2020 General Election (President)", "general", 2020),
    ElectionInfo("20181106", "2018 General Election (Governor)", "general", 2018),
    ElectionInfo("20161108", "2016 General Election (President)", "general", 2016),
]


# Idaho general elections. Data source = Idaho SoS / VoteIdaho.gov bulk exports:
#   - 2024: a clean long-format precinct XLSX (raw_races_general.xlsx) —
#     County,Precinct,RaceType,Race,Party,Candidate,Votes.
#   - 2022 / 2020: the *_General_Canvass.zip bundles (pivoted precinct XLSX per
#     race-group: Statewide / Legislative / Dist Judge), un-melted by the
#     converter (scripts/download_id_sos.py) into the standard adapter schema.
# Covers presidential PVI (2024, 2020, 2016) + the gubernatorial midterms
# (2022, 2018). Slugs name the per-election folder data/raw/id/<slug>/; ID
# primaries (May, partisan-closed) are omitted until partisan-primary handling
# is wired for ID (mirrors NY/TX).
ID_ELECTIONS = [
    ElectionInfo("20241105", "2024 General Election (President)", "general", 2024),
    ElectionInfo("20221108", "2022 General Election (Governor)", "general", 2022),
    ElectionInfo("20201103", "2020 General Election (President)", "general", 2020),
    ElectionInfo("20181106", "2018 General Election (Governor)", "general", 2018),
    ElectionInfo("20161108", "2016 General Election (President)", "general", 2016),
    # ID closed partisan primaries (third Tuesday in May). Republican + Democratic
    # (+ minor-party) contests are SEPARATE races in the canvass ("... - Republican"
    # / "... - Democratic"), which the loader keys distinctly. Same bulk formats as
    # the generals: 2024 long-format XLSX; 2022/2020 *_Primary_Canvass.zip pivot
    # bundles; 2018/2016 archive per-race workbooks. Converter: download_id_sos.py.
    ElectionInfo("20240521", "2024 Primary Election", "primary", 2024),
    ElectionInfo("20220517", "2022 Primary Election", "primary", 2022),
    ElectionInfo("20200519", "2020 Primary Election", "primary", 2020),
    ElectionInfo("20180515", "2018 Primary Election", "primary", 2018),
    ElectionInfo("20160517", "2016 Primary Election", "primary", 2016),
    # Odd-year COUNTY-CLERK municipal canvass (nonpartisan city/county/school/fire
    # races; loaded by scripts/download_id_county.py). Tagged 'consolidated' — NOT
    # 'general' — so it stays out of partisan-lean/backtest 'general' queries; the
    # turf lean for these local races comes from the statewide partisan cycles.
    ElectionInfo("20251104", "2025 Consolidated Election (Municipal)", "consolidated", 2025),
]


def get_elections(state_code: str | None = None) -> list[ElectionInfo]:
    """Return the known-election list for a state.

    Defaults to the active StateConfig's state. WA returns the
    results.vote.wa.gov-backed ``ELECTIONS`` list; NY returns ``NY_ELECTIONS``.
    Unknown states return an empty list (callers should treat that as
    "no calendar configured" rather than an error).
    """
    if state_code is None:
        try:
            from config.state_config import get_state_config
            state_code = get_state_config().state_code
        except Exception:
            state_code = "WA"
    code = (state_code or "WA").upper()
    if code == "WA":
        return ELECTIONS
    if code == "NY":
        return NY_ELECTIONS
    if code == "TX":
        return TX_ELECTIONS
    if code == "ID":
        return ID_ELECTIONS
    return []
