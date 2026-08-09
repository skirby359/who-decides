"""District profile for Washington's 5th Congressional District (WA-05).

WA-05 covers eastern Washington, including Spokane (the state's second-largest
city), the Palouse, and the agricultural communities of the Columbia Basin.
After 2022 redistricting, the district encompasses 12 counties, with Spokane
and Grant counties split between CD-05 and CD-04.
"""

from __future__ import annotations

import re

from config.districts import DistrictProfile

CD05_PROFILE = DistrictProfile(
    # Identity
    district_id="cd05",
    district_type="congressional",
    district_number="05",
    district_label="WA-05",
    district_description=(
        "Washington's 5th Congressional District covers eastern Washington, "
        "including Spokane (the state's second-largest city), the Palouse, "
        "and the agricultural communities of the Columbia Basin."
    ),

    # Geography — SOS 2-letter county codes
    county_codes={
        "AD", "AS", "CU", "FE", "GA", "GR", "LI", "PE", "SP", "ST", "WL", "WT",
    },
    split_county_codes={"SP", "GR"},  # Spokane and Grant split with CD-04

    # Census county FIPS codes (state FIPS 53 = WA)
    county_fips={
        "001": "Adams",
        "003": "Asotin",
        "013": "Columbia",
        "019": "Ferry",
        "023": "Garfield",
        "025": "Grant",
        "043": "Lincoln",
        "051": "Pend Oreille",
        "063": "Spokane",
        "065": "Stevens",
        "071": "Walla Walla",
        "075": "Whitman",
    },

    # Election result filtering — match CD-5 congressional races
    race_pattern=re.compile(r"congressional\s+district\s+0?5\b", re.IGNORECASE),
    statewide_races=True,

    # VRDB voter filtering
    voter_filter_field="CongressionalDistrict",
    voter_filter_values=["5", "05"],

    # FEC campaign finance
    fec_enabled=True,
    fec_district="05",
    fec_office="H",

    # Historical WA-05 D two-party % (from congressional race results)
    historical_performance={
        2016: 38.6,   # Lisa Brown didn't run; proxy from presidential
        2018: 45.2,   # Lisa Brown vs CMR
        2020: 42.0,   # Dave Wilson vs CMR
        2022: 47.6,   # Natasha Hill vs CMR
        2024: 43.8,   # Carmichael Casto vs Michael Baumgartner
    },

    # Presidential vote at district level (D two-party %) for Cook PVI.
    # Left empty so compute_pvi() falls through to
    # _compute_district_presidential_performance(), which aggregates
    # the actual cd05 precinct results. The previously hand-coded 2016
    # value of 36.9% was sourced from Wikipedia against pre-2022 district
    # boundaries; under the current redistricting the same year's two-party
    # D% is 42.88% from precinct data. Hand-coding froze the wrong value
    # in for backtest PVI (R+14 instead of R+6) and over-penalized
    # WA-05 forecasts by ~9 points on D vote share.
    presidential_performance={},

    # Database — uses legacy filename for backward compatibility
    db_filename="wa_political.duckdb",

    # Partisan lean race priority — CD-5 congressional race is priority 1
    race_priority_sql=(
        "WHEN r.office = 'U.S. Representative'\n"
        "                    AND UPPER(r.race_name) LIKE '%DISTRICT%5%'\n"
        "                    THEN 1"
    ),

    # Canvassing geographic context
    urban_counties={"Spokane"},
)
