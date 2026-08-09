"""Idaho State configuration.

Idaho has 2 congressional districts, 35 legislative districts,
a closed partisan primary (May), and mixed voting (absentee + in-person).
"""

from config.state_config import CountyInfo, StateConfig

# All 44 Idaho counties with FIPS codes
# Idaho SoS uses full county names (no 2-letter codes)
_ID_COUNTIES = {
    "ADA": CountyInfo("ADA", "1", "ADA"),
    "ADAMS": CountyInfo("ADAMS", "3", "ADAMS"),
    "BANNOCK": CountyInfo("BANNOCK", "5", "BANNOCK"),
    "BEAR LAKE": CountyInfo("BEAR LAKE", "7", "BEAR LAKE"),
    "BENEWAH": CountyInfo("BENEWAH", "9", "BENEWAH"),
    "BINGHAM": CountyInfo("BINGHAM", "11", "BINGHAM"),
    "BLAINE": CountyInfo("BLAINE", "13", "BLAINE"),
    "BOISE": CountyInfo("BOISE", "15", "BOISE"),
    "BONNER": CountyInfo("BONNER", "17", "BONNER"),
    "BONNEVILLE": CountyInfo("BONNEVILLE", "19", "BONNEVILLE"),
    "BOUNDARY": CountyInfo("BOUNDARY", "21", "BOUNDARY"),
    "BUTTE": CountyInfo("BUTTE", "23", "BUTTE"),
    "CAMAS": CountyInfo("CAMAS", "25", "CAMAS"),
    "CANYON": CountyInfo("CANYON", "27", "CANYON"),
    "CARIBOU": CountyInfo("CARIBOU", "29", "CARIBOU"),
    "CASSIA": CountyInfo("CASSIA", "31", "CASSIA"),
    "CLARK": CountyInfo("CLARK", "33", "CLARK"),
    "CLEARWATER": CountyInfo("CLEARWATER", "35", "CLEARWATER"),
    "CUSTER": CountyInfo("CUSTER", "37", "CUSTER"),
    "ELMORE": CountyInfo("ELMORE", "39", "ELMORE"),
    "FRANKLIN": CountyInfo("FRANKLIN", "41", "FRANKLIN"),
    "FREMONT": CountyInfo("FREMONT", "43", "FREMONT"),
    "GEM": CountyInfo("GEM", "45", "GEM"),
    "GOODING": CountyInfo("GOODING", "47", "GOODING"),
    "IDAHO": CountyInfo("IDAHO", "49", "IDAHO"),
    "JEFFERSON": CountyInfo("JEFFERSON", "51", "JEFFERSON"),
    "JEROME": CountyInfo("JEROME", "53", "JEROME"),
    "KOOTENAI": CountyInfo("KOOTENAI", "55", "KOOTENAI"),
    "LATAH": CountyInfo("LATAH", "57", "LATAH"),
    "LEMHI": CountyInfo("LEMHI", "59", "LEMHI"),
    "LEWIS": CountyInfo("LEWIS", "61", "LEWIS"),
    "LINCOLN": CountyInfo("LINCOLN", "63", "LINCOLN"),
    "MADISON": CountyInfo("MADISON", "65", "MADISON"),
    "MINIDOKA": CountyInfo("MINIDOKA", "67", "MINIDOKA"),
    "NEZ PERCE": CountyInfo("NEZ PERCE", "69", "NEZ PERCE"),
    "ONEIDA": CountyInfo("ONEIDA", "71", "ONEIDA"),
    "OWYHEE": CountyInfo("OWYHEE", "73", "OWYHEE"),
    "PAYETTE": CountyInfo("PAYETTE", "75", "PAYETTE"),
    "POWER": CountyInfo("POWER", "77", "POWER"),
    "SHOSHONE": CountyInfo("SHOSHONE", "79", "SHOSHONE"),
    "TETON": CountyInfo("TETON", "81", "TETON"),
    "TWIN FALLS": CountyInfo("TWIN FALLS", "83", "TWIN FALLS"),
    "VALLEY": CountyInfo("VALLEY", "85", "VALLEY"),
    "WASHINGTON": CountyInfo("WASHINGTON", "87", "WASHINGTON"),
}

ID_CONFIG = StateConfig(
    state_code="ID",
    state_name="Idaho",
    state_fips="16",
    congressional_districts=2,
    legislative_districts=35,
    legislative_label="Legislative District",
    primary_system="partisan_closed",
    voting_method="mixed",
    primary_month=5,
    # Idaho redrew its CD + LD maps in 2021 for the 2022 cycle (post-2020
    # census), so pre-2022 precinct footprints don't compare to 2022+. Mirrors
    # WA: PVI/drag drop pre-cutoff cycles once a post-cutoff cycle exists, and a
    # single post-2022 presidential cycle (2024) suffices for PVI.
    district_boundary_year=2022,
    # Idaho race-name conventions differ from WA/NY/TX: CDs are "U.S.
    # REPRESENTATIVE DISTRICT N"; the single nested legislative district appears
    # as "SENATOR DISTRICT N" and "REPRESENTATIVE DISTRICT N SEAT A/B" (no
    # separate senate-district column — both fold into ld). The CD regex is
    # matched first + exclusively (see etl/district_mapping.py) so the U.S. House
    # race isn't also read as a legislative district.
    cd_race_regex=r"u\.s\.\s+representative\s+district\s+(\d+)",
    ld_race_regex=r"(?:senator|representative)\s+district\s+(\d+)",
    mail_turnout_bonus=0.0,
    counties=_ID_COUNTIES,
    sos_base_url="https://sos.idaho.gov/elections-division/results",
    sos_csv_format="id_sos",
    state_finance_enabled=True,  # Idaho Sunshine portal — etl/adapters/id_sunshine.py
    state_finance_api_base="https://api-sunshine.voteidaho.gov/api",
    state_finance_datasets={"cycles": (2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018)},
    default_district="cd01",
)
