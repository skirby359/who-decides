"""District profile for Washington's 3rd Legislative District (WA LD-03).

WA LD-03 is located entirely within Spokane County in eastern Washington.
The district covers portions of the city of Spokane and surrounding areas.
It elects two State Representatives and one State Senator.
"""

from __future__ import annotations

import re

from config.districts import DistrictProfile

LD03_PROFILE = DistrictProfile(
    # Identity
    district_id="ld03",
    district_type="legislative",
    district_number="03",
    district_label="WA LD-03",
    district_description=(
        "Washington's 3rd Legislative District is located in Spokane County "
        "in eastern Washington, covering portions of the city of Spokane and "
        "surrounding areas."
    ),

    # Geography — SOS 2-letter county codes
    county_codes={"SP"},                 # Spokane
    split_county_codes={"SP"},           # Spokane split among multiple LDs

    # Census county FIPS codes (state FIPS 53 = WA)
    county_fips={
        "063": "Spokane",
    },

    # Election result filtering — match LD-3 legislative races
    # SOS CSV format: "Legislative District 3 - State Representative Pos. 1"
    race_pattern=re.compile(r"legislative\s+district\s+0?3\b", re.IGNORECASE),
    statewide_races=True,

    # VRDB voter filtering
    voter_filter_field="LegislativeDistrict",
    voter_filter_values=["3", "03"],

    # FEC — not applicable for state legislative races
    fec_enabled=False,
    fec_district="",
    fec_office="",

    # PDC — state-level campaign finance from WA Public Disclosure Commission
    pdc_enabled=True,

    # Historical performance — empty; will be computed from loaded election data
    historical_performance={},

    # Database — separate from CD-05
    db_filename="wa_ld03.duckdb",

    # Partisan lean race priority — LD-3 legislative race is priority 1
    race_priority_sql=(
        "WHEN UPPER(r.race_name) LIKE '%LEGISLATIVE DISTRICT%3%'\n"
        "                    AND (UPPER(r.race_name) LIKE '%REPRESENTATIVE%'\n"
        "                         OR UPPER(r.race_name) LIKE '%SENATOR%')\n"
        "                    THEN 1"
    ),

    # Canvassing geographic context — in Spokane, the state's 2nd-largest city
    urban_counties={"Spokane"},
)
