"""New York State configuration.

New York has 26 congressional districts (post-2022 redistricting, down from
27) and a *bicameral* legislature with two separately-districted chambers:
150 Assembly districts (lower) and 63 State Senate districts (upper). NY runs
closed partisan primaries (June) and uses mixed voting (in-person early +
Election Day + absentee/mail).

Two NY-specific wrinkles the analysis layer must eventually handle (NOT solved
in this config, flagged here so they're not forgotten):

  * Fusion voting. A single candidate can appear on multiple party lines
    (e.g. Democratic + Working Families, Republican + Conservative). Result
    rows must be consolidated per human candidate and votes summed across
    lines. See the fusion-consolidation ETL stage (Phase 1).
  * Bicameral, non-nested chambers. ``legislative_districts`` here is the
    150-seat Assembly; ``upper_chamber_districts`` is the 63-seat Senate.

County identifiers: NYS BOE / OpenElections publish results keyed by county
*name* (NY has no 2-letter SoS code system like WA), so ``sos_code`` is the
UPPER-cased county name, mirroring the Idaho convention. FIPS suffixes are
3-digit zero-padded to match Census/BLS conventions (same as WA).
"""

from config.state_config import CountyInfo, StateConfig

# All 62 New York counties. sos_code == UPPER county name (NY publishes by
# name). FIPS suffixes are 3-digit zero-padded within state FIPS 36.
# Note: the five NYC boroughs are counties — Bronx (Bronx), Kings (Brooklyn),
# New York (Manhattan), Queens (Queens), Richmond (Staten Island). NYC BOE
# reports these separately from the upstate county boards (handled in the
# results adapter, Phase 1).
_NY_COUNTIES = {
    "ALBANY": CountyInfo("ALBANY", "001", "ALBANY"),
    "ALLEGANY": CountyInfo("ALLEGANY", "003", "ALLEGANY"),
    "BRONX": CountyInfo("BRONX", "005", "BRONX"),
    "BROOME": CountyInfo("BROOME", "007", "BROOME"),
    "CATTARAUGUS": CountyInfo("CATTARAUGUS", "009", "CATTARAUGUS"),
    "CAYUGA": CountyInfo("CAYUGA", "011", "CAYUGA"),
    "CHAUTAUQUA": CountyInfo("CHAUTAUQUA", "013", "CHAUTAUQUA"),
    "CHEMUNG": CountyInfo("CHEMUNG", "015", "CHEMUNG"),
    "CHENANGO": CountyInfo("CHENANGO", "017", "CHENANGO"),
    "CLINTON": CountyInfo("CLINTON", "019", "CLINTON"),
    "COLUMBIA": CountyInfo("COLUMBIA", "021", "COLUMBIA"),
    "CORTLAND": CountyInfo("CORTLAND", "023", "CORTLAND"),
    "DELAWARE": CountyInfo("DELAWARE", "025", "DELAWARE"),
    "DUTCHESS": CountyInfo("DUTCHESS", "027", "DUTCHESS"),
    "ERIE": CountyInfo("ERIE", "029", "ERIE"),
    "ESSEX": CountyInfo("ESSEX", "031", "ESSEX"),
    "FRANKLIN": CountyInfo("FRANKLIN", "033", "FRANKLIN"),
    "FULTON": CountyInfo("FULTON", "035", "FULTON"),
    "GENESEE": CountyInfo("GENESEE", "037", "GENESEE"),
    "GREENE": CountyInfo("GREENE", "039", "GREENE"),
    "HAMILTON": CountyInfo("HAMILTON", "041", "HAMILTON"),
    "HERKIMER": CountyInfo("HERKIMER", "043", "HERKIMER"),
    "JEFFERSON": CountyInfo("JEFFERSON", "045", "JEFFERSON"),
    "KINGS": CountyInfo("KINGS", "047", "KINGS"),
    "LEWIS": CountyInfo("LEWIS", "049", "LEWIS"),
    "LIVINGSTON": CountyInfo("LIVINGSTON", "051", "LIVINGSTON"),
    "MADISON": CountyInfo("MADISON", "053", "MADISON"),
    "MONROE": CountyInfo("MONROE", "055", "MONROE"),
    "MONTGOMERY": CountyInfo("MONTGOMERY", "057", "MONTGOMERY"),
    "NASSAU": CountyInfo("NASSAU", "059", "NASSAU"),
    "NEW YORK": CountyInfo("NEW YORK", "061", "NEW YORK"),
    "NIAGARA": CountyInfo("NIAGARA", "063", "NIAGARA"),
    "ONEIDA": CountyInfo("ONEIDA", "065", "ONEIDA"),
    "ONONDAGA": CountyInfo("ONONDAGA", "067", "ONONDAGA"),
    "ONTARIO": CountyInfo("ONTARIO", "069", "ONTARIO"),
    "ORANGE": CountyInfo("ORANGE", "071", "ORANGE"),
    "ORLEANS": CountyInfo("ORLEANS", "073", "ORLEANS"),
    "OSWEGO": CountyInfo("OSWEGO", "075", "OSWEGO"),
    "OTSEGO": CountyInfo("OTSEGO", "077", "OTSEGO"),
    "PUTNAM": CountyInfo("PUTNAM", "079", "PUTNAM"),
    "QUEENS": CountyInfo("QUEENS", "081", "QUEENS"),
    "RENSSELAER": CountyInfo("RENSSELAER", "083", "RENSSELAER"),
    "RICHMOND": CountyInfo("RICHMOND", "085", "RICHMOND"),
    "ROCKLAND": CountyInfo("ROCKLAND", "087", "ROCKLAND"),
    "ST. LAWRENCE": CountyInfo("ST. LAWRENCE", "089", "ST. LAWRENCE"),
    "SARATOGA": CountyInfo("SARATOGA", "091", "SARATOGA"),
    "SCHENECTADY": CountyInfo("SCHENECTADY", "093", "SCHENECTADY"),
    "SCHOHARIE": CountyInfo("SCHOHARIE", "095", "SCHOHARIE"),
    "SCHUYLER": CountyInfo("SCHUYLER", "097", "SCHUYLER"),
    "SENECA": CountyInfo("SENECA", "099", "SENECA"),
    "STEUBEN": CountyInfo("STEUBEN", "101", "STEUBEN"),
    "SUFFOLK": CountyInfo("SUFFOLK", "103", "SUFFOLK"),
    "SULLIVAN": CountyInfo("SULLIVAN", "105", "SULLIVAN"),
    "TIOGA": CountyInfo("TIOGA", "107", "TIOGA"),
    "TOMPKINS": CountyInfo("TOMPKINS", "109", "TOMPKINS"),
    "ULSTER": CountyInfo("ULSTER", "111", "ULSTER"),
    "WARREN": CountyInfo("WARREN", "113", "WARREN"),
    "WASHINGTON": CountyInfo("WASHINGTON", "115", "WASHINGTON"),
    "WAYNE": CountyInfo("WAYNE", "117", "WAYNE"),
    "WESTCHESTER": CountyInfo("WESTCHESTER", "119", "WESTCHESTER"),
    "WYOMING": CountyInfo("WYOMING", "121", "WYOMING"),
    "YATES": CountyInfo("YATES", "123", "YATES"),
}

NY_CONFIG = StateConfig(
    state_code="NY",
    state_name="New York",
    state_fips="36",
    congressional_districts=26,
    # Lower chamber = 150-seat Assembly; upper chamber declared separately
    # because NY's Senate is drawn on an independent 63-seat map (not nested).
    legislative_districts=150,
    legislative_label="Assembly District",
    upper_chamber_districts=63,
    upper_chamber_label="Senate District",
    primary_system="partisan_closed",
    voting_method="mixed",
    primary_month=6,
    mail_turnout_bonus=0.0,
    counties=_NY_COUNTIES,
    # NYS BOE election results portal. NOTE: NY does not publish a single
    # statewide precinct/election-district CSV like WA's AllStatePrecincts.csv;
    # the results adapter (Phase 1) sources statewide+county from NYS BOE and
    # precinct/ED level from OpenElections-NY + NYC BOE.
    sos_base_url="https://results.elections.ny.gov",
    sos_csv_format="ny_boe",
    # NY State Board of Elections campaign finance on Socrata (data.ny.gov),
    # itemized July 1999–present. Two transaction-level feeds (verified
    # 2026-06-05): contributions (incl. contributor_type for the individual/
    # PAC split) and expenditures. Both share one wide schema; consumed by
    # wa_analyzer.etl.adapters.ny_finance.
    state_finance_enabled=True,
    state_finance_api_base="https://data.ny.gov/resource",
    state_finance_datasets={
        "contributions": "4j2b-6a2j",
        "expenditures": "ajsb-8pni",
    },
    default_district="cd03",
    # NY redrew all districts at the 2022 decennial. Setting boundary_year so
    # PVI / down-ballot-drag ignore pre-2022 cycles when a post-2022 cycle
    # exists. CAVEAT to revisit in the PVI work: NY's *congressional* map was
    # redrawn AGAIN for 2024 (the 2022 special-master map differs from the
    # 2024 legislature-drawn map), while the Assembly/Senate maps stayed put.
    # A single boundary_year can't capture that; congressional PVI may need a
    # 2024 cutoff. Flagged, not resolved here.
    district_boundary_year=2022,
)
