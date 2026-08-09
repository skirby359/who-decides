"""Washington State county code / name / FIPS mappings.

Centralised county reference data used by election-results ETL, VRDB
processing, Census data loading, and district profile resolution.

County names are stored in UPPER CASE to ensure consistent joins
across data sources.

Three lookup dictionaries are provided:

- ``COUNTY_CODE_TO_NAME`` -- SOS 2-letter abbreviation -> UPPER county name
- ``COUNTY_NAME_TO_CODE`` -- UPPER county name -> 2-letter code
- ``COUNTY_FIPS_TO_NAME`` -- odd-numbered FIPS suffix -> UPPER county name
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# SOS 2-letter county code -> full county name (UPPER CASE)
# ---------------------------------------------------------------------------

COUNTY_CODE_TO_NAME: dict[str, str] = {
    "AD": "ADAMS",
    "AS": "ASOTIN",
    "BE": "BENTON",
    "CH": "CHELAN",
    "CM": "CLALLAM",
    "CR": "CLARK",
    "CU": "COLUMBIA",
    "CZ": "COWLITZ",
    "DG": "DOUGLAS",
    "FE": "FERRY",
    "FR": "FRANKLIN",
    "GA": "GARFIELD",
    "GR": "GRANT",
    "GY": "GRAYS HARBOR",
    "IS": "ISLAND",
    "JE": "JEFFERSON",
    "KI": "KING",
    "KP": "KITSAP",
    # KNOWN BUG (2026-04-30): WA SoS source CSVs actually use KT for
    # Klickitat (precinct names like ALDER CREEK, CENTERVILLE, E
    # KLICKITAT) and KS for Kittitas (CLE ELUM, ELLENSBURG, EASTON) —
    # verified against 2020/2022/2024 source files. The mapping below
    # is INVERTED relative to the source. We're keeping it inverted
    # for now because the existing DB was loaded under this mapping;
    # swapping in code without re-loading produces duplicate precinct
    # rows (DuckDB FK constraint blocks UPDATE on precincts.county_name
    # since every precinct_id has incoming FKs from precinct_results,
    # precinct_turnout, etc.). End-user impact is cosmetic — county
    # labels in display tables show "KLICKITAT" when the underlying
    # precincts are Kittitas (correctly part of cd08 via precinct_id
    # JOIN), and vice versa. Fix path: side-table override pattern
    # (mirroring candidate_party_override) — see docs/known_issues.md.
    "KT": "KITTITAS",
    "KS": "KLICKITAT",
    "LE": "LEWIS",
    "LI": "LINCOLN",
    "MA": "MASON",
    "OK": "OKANOGAN",
    "PA": "PACIFIC",
    "PE": "PEND OREILLE",
    "PI": "PIERCE",
    "SJ": "SAN JUAN",
    "SK": "SKAGIT",
    "SM": "SKAMANIA",
    "SN": "SNOHOMISH",
    "SP": "SPOKANE",
    "ST": "STEVENS",
    "TH": "THURSTON",
    "WK": "WAHKIAKUM",
    "WL": "WALLA WALLA",
    "WM": "WHATCOM",
    "WT": "WHITMAN",
    "YA": "YAKIMA",
}

# ---------------------------------------------------------------------------
# Reverse lookup: UPPER county name -> 2-letter SOS code
# ---------------------------------------------------------------------------

COUNTY_NAME_TO_CODE: dict[str, str] = {
    v: k for k, v in COUNTY_CODE_TO_NAME.items()
}

# ---------------------------------------------------------------------------
# FIPS county code suffix (odd numbers, no leading zero) -> UPPER county name
# Used by VRDB files where county is identified by FIPS code.
# ---------------------------------------------------------------------------

COUNTY_FIPS_TO_NAME: dict[str, str] = {
    "1": "ADAMS",
    "3": "ASOTIN",
    "5": "BENTON",
    "7": "CHELAN",
    "9": "CLALLAM",
    "11": "CLARK",
    "13": "COLUMBIA",
    "15": "COWLITZ",
    "17": "DOUGLAS",
    "19": "FERRY",
    "21": "FRANKLIN",
    "23": "GARFIELD",
    "25": "GRANT",
    "27": "GRAYS HARBOR",
    "29": "ISLAND",
    "31": "JEFFERSON",
    "33": "KING",
    "35": "KITSAP",
    "37": "KITTITAS",
    "39": "KLICKITAT",
    "41": "LEWIS",
    "43": "LINCOLN",
    "45": "MASON",
    "47": "OKANOGAN",
    "49": "PACIFIC",
    "51": "PEND OREILLE",
    "53": "PIERCE",
    "55": "SAN JUAN",
    "57": "SKAGIT",
    "59": "SKAMANIA",
    "61": "SNOHOMISH",
    "63": "SPOKANE",
    "65": "STEVENS",
    "67": "THURSTON",
    "69": "WAHKIAKUM",
    "71": "WALLA WALLA",
    "73": "WHATCOM",
    "75": "WHITMAN",
    "77": "YAKIMA",
}
