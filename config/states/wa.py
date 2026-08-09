"""Washington State configuration."""

from config.state_config import CountyInfo, StateConfig

# All 39 WA counties with SOS 2-letter codes and FIPS suffixes
# FIPS codes are 3-digit zero-padded (e.g., "063" not "63") to match
# Census and BLS conventions.
_WA_COUNTIES = {
    "AD": CountyInfo("ADAMS", "001", "AD"),
    "AS": CountyInfo("ASOTIN", "003", "AS"),
    "BE": CountyInfo("BENTON", "005", "BE"),
    "CH": CountyInfo("CHELAN", "007", "CH"),
    "CM": CountyInfo("CLALLAM", "009", "CM"),
    "CR": CountyInfo("CLARK", "011", "CR"),
    "CU": CountyInfo("COLUMBIA", "013", "CU"),
    "CZ": CountyInfo("COWLITZ", "015", "CZ"),
    "DG": CountyInfo("DOUGLAS", "017", "DG"),
    "FE": CountyInfo("FERRY", "019", "FE"),
    "FR": CountyInfo("FRANKLIN", "021", "FR"),
    "GA": CountyInfo("GARFIELD", "023", "GA"),
    "GR": CountyInfo("GRANT", "025", "GR"),
    "GY": CountyInfo("GRAYS HARBOR", "027", "GY"),
    "IS": CountyInfo("ISLAND", "029", "IS"),
    "JE": CountyInfo("JEFFERSON", "031", "JE"),
    "KI": CountyInfo("KING", "033", "KI"),
    "KP": CountyInfo("KITSAP", "035", "KP"),
    "KT": CountyInfo("KITTITAS", "037", "KT"),
    "KS": CountyInfo("KLICKITAT", "039", "KS"),
    "LE": CountyInfo("LEWIS", "041", "LE"),
    "LI": CountyInfo("LINCOLN", "043", "LI"),
    "MA": CountyInfo("MASON", "045", "MA"),
    "OK": CountyInfo("OKANOGAN", "047", "OK"),
    "PA": CountyInfo("PACIFIC", "049", "PA"),
    "PE": CountyInfo("PEND OREILLE", "051", "PE"),
    "PI": CountyInfo("PIERCE", "053", "PI"),
    "SJ": CountyInfo("SAN JUAN", "055", "SJ"),
    "SK": CountyInfo("SKAGIT", "057", "SK"),
    "SM": CountyInfo("SKAMANIA", "059", "SM"),
    "SN": CountyInfo("SNOHOMISH", "061", "SN"),
    "SP": CountyInfo("SPOKANE", "063", "SP"),
    "ST": CountyInfo("STEVENS", "065", "ST"),
    "TH": CountyInfo("THURSTON", "067", "TH"),
    "WK": CountyInfo("WAHKIAKUM", "069", "WK"),
    "WL": CountyInfo("WALLA WALLA", "071", "WL"),
    "WM": CountyInfo("WHATCOM", "073", "WM"),
    "WT": CountyInfo("WHITMAN", "075", "WT"),
    "YA": CountyInfo("YAKIMA", "077", "YA"),
}

WA_CONFIG = StateConfig(
    state_code="WA",
    state_name="Washington",
    state_fips="53",
    congressional_districts=10,
    legislative_districts=49,
    legislative_label="Legislative District",
    primary_system="top_two",
    voting_method="all_mail",
    primary_month=8,
    mail_turnout_bonus=0.07,
    counties=_WA_COUNTIES,
    sos_base_url="https://results.vote.wa.gov/results",
    sos_csv_format="wa_sos",
    state_finance_enabled=True,
    state_finance_api_base="https://data.wa.gov/resource",
    state_finance_datasets={
        "summary": "3h9x-7bvm",
        "contributions": "kv7h-kjye",
        "independent_expenditures": "sxzw-4vms",
        "expenditures": "tijg-9zyp",
    },
    default_district="cd05",
    # WA's 2022 redistricting redrew every CD and LD boundary. Most
    # notably, cd08 moved from a Pierce-heavy R+9 footprint (2020 pres)
    # to a King-heavy D+4 footprint (2024 pres). Averaging those two
    # cycles with the standard Cook PVI formula yields R+3, which
    # contradicts Schrier's actual 5-8pt D wins every cycle and fights
    # the model's own SAFE verdict. Setting boundary_year=2022 tells
    # PVI and down-ballot-drag to ignore pre-2022 cycles when at least
    # one post-2022 cycle is available.
    district_boundary_year=2022,
)
