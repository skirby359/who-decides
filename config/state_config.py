"""State configuration dataclass for multi-state support.

Each state's specific knowledge (district counts, FIPS codes, county data,
election system, data source URLs) is encapsulated in a ``StateConfig``
instance.  The analysis engine, reporting, and dashboard remain generic.

Usage::

    from config.state_config import get_state_config
    state = get_state_config("WA")
    print(state.congressional_districts)  # 10
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CountyInfo:
    """County reference data."""
    name: str       # UPPER CASE normalized name
    fips: str       # County FIPS suffix (e.g. "33" for King County, WA)
    sos_code: str   # State SOS abbreviation (e.g. "KI" for WA)


@dataclass
class StateConfig:
    """Encapsulates all state-specific knowledge."""

    # Identity
    state_code: str              # "WA", "ID"
    state_name: str              # "Washington", "Idaho"
    state_fips: str              # "53", "16"

    # Districts
    congressional_districts: int  # 10 for WA, 2 for ID
    legislative_districts: int    # 49 for WA, 35 for ID
    legislative_label: str = "Legislative District"

    # Bicameral legislatures with two *separately* districted chambers
    # (e.g. NY: 150 Assembly + 63 Senate, drawn on independent maps).
    # For these, ``legislative_districts`` holds the LOWER-chamber count
    # and these fields hold the UPPER chamber. States whose single LD
    # scheme nests both chambers (WA's 49 LDs each elect 1 senator + 2
    # reps; ID similarly) leave ``upper_chamber_districts=None``.
    upper_chamber_districts: int | None = None
    upper_chamber_label: str = ""

    # Bicameral LOWER-chamber identity (only used when upper_chamber_districts is
    # set). Different bicameral states name their lower house differently, which
    # changes the auto-profile prefix + the race-name pattern:
    #   NY: Assembly -> prefix "ad", race "ASSEMBLY DISTRICT N"   (defaults)
    #   TX: House    -> prefix "hd", race "HOUSE DISTRICT N"
    # The upper chamber is "Senate" ("sd" / "SENATE DISTRICT N") in both, so it
    # stays hard-coded. Defaults are NY's so NY needs no config change.
    lower_chamber_prefix: str = "ad"
    lower_chamber_race_keyword: str = "assembly"
    lower_chamber_name: str = "Assembly"

    # Race-name → district regexes (one capture group = the number) used by
    # etl/district_mapping.py. Defaults match WA/NY/TX naming ("congressional
    # district N" / "legislative district N"). Idaho names its races differently
    # ("U.S. REPRESENTATIVE DISTRICT N" for CDs; "SENATOR/REPRESENTATIVE DISTRICT
    # N [SEAT x]" for the single nested legislative district), so it overrides
    # these. A race matching the CD regex is treated as congressional ONLY (the
    # mapper skips the LD test for it), so an ID "U.S. REPRESENTATIVE DISTRICT 1"
    # doesn't also register as legislative district 1.
    cd_race_regex: str = r"congressional\s+district\s+(\d+)"
    ld_race_regex: str = r"legislative\s+district\s+(\d+)"

    # Database
    statewide_db_name: str = ""   # "wa_statewide.duckdb"
    vrdb_db_name: str = ""        # "wa_vrdb.duckdb"

    # Election system
    primary_system: str = "top_two"      # "top_two" | "partisan_closed" | "partisan_open"
    voting_method: str = "all_mail"      # "all_mail" | "mixed" | "in_person"
    primary_month: int = 8               # Month number (1-12)
    mail_turnout_bonus: float = 0.0      # Extra turnout from all-mail voting

    # Counties: sos_code -> CountyInfo
    counties: dict[str, CountyInfo] = field(default_factory=dict)

    # Election calendar
    sos_base_url: str = ""
    sos_csv_format: str = ""             # "wa_sos", "id_sos", etc.

    # State campaign finance
    state_finance_enabled: bool = False
    state_finance_api_base: str = ""
    state_finance_datasets: dict[str, str] = field(default_factory=dict)

    # Default district (for fallbacks)
    default_district: str = "cd01"

    # FEC state filter
    fec_state: str = ""                  # "WA", "ID" — for FEC API queries

    # Display
    district_prefix: str = ""            # "WA", "ID" — used in labels like "WA-05"

    # Redistricting cutoff. When set, PVI / down-ballot-drag for
    # congressional + legislative districts drops cycles before this year
    # IF at least one post-cutoff cycle is available. This prevents a
    # 2020 presidential result computed on the *old* boundaries from
    # poisoning Cook PVI for a district whose lines moved at the 2022
    # decennial redraw (e.g. WA-08 went from Pierce-heavy R+9 in 2020
    # to King-heavy D+4 in 2024 — averaging them as Cook normally would
    # produces a misleading R+3 label that fights the SAFE verdict).
    # WA: 2022. Idaho's 2022 maps were minor adjustments, so leave None
    # there for now.
    district_boundary_year: int | None = None

    def __post_init__(self):
        if not self.statewide_db_name:
            self.statewide_db_name = f"{self.state_code.lower()}_statewide.duckdb"
        if not self.vrdb_db_name:
            self.vrdb_db_name = f"{self.state_code.lower()}_vrdb.duckdb"
        if not self.fec_state:
            self.fec_state = self.state_code
        if not self.district_prefix:
            self.district_prefix = self.state_code

    @property
    def county_code_to_name(self) -> dict[str, str]:
        """SOS code -> UPPER county name (backward-compatible with counties.py)."""
        return {code: info.name for code, info in self.counties.items()}

    @property
    def county_name_to_code(self) -> dict[str, str]:
        """UPPER county name -> SOS code."""
        return {info.name: code for code, info in self.counties.items()}

    @property
    def county_fips_to_name(self) -> dict[str, str]:
        """FIPS suffix -> UPPER county name."""
        return {info.fips: info.name for info in self.counties.values()}


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_REGISTRY: dict[str, StateConfig] = {}


def register_state(config: StateConfig) -> None:
    """Register a state configuration."""
    _REGISTRY[config.state_code.upper()] = config


def get_state_config(code: str | None = None) -> StateConfig:
    """Get state configuration by code. Defaults to settings.state."""
    if code is None:
        from config.settings import settings
        code = settings.state
    code = code.upper()
    if code not in _REGISTRY:
        # Lazy-load state modules
        _load_state(code)
    if code not in _REGISTRY:
        raise ValueError(f"Unknown state: {code}. Available: {list(_REGISTRY.keys())}")
    return _REGISTRY[code]


def list_states() -> list[str]:
    """List all registered state codes."""
    # Ensure all known state modules are loaded before enumerating. Keep this in
    # sync with the codes handled in _load_state() — omitting one silently drops
    # it from the enumeration (this loop previously missed "tx").
    for mod in ("wa", "id", "ny", "tx"):
        try:
            _load_state(mod.upper())
        except Exception:
            pass
    return sorted(_REGISTRY.keys())


def _load_state(code: str) -> None:
    """Lazy-load a state config module."""
    code = code.upper()
    if code in _REGISTRY:
        return
    try:
        if code == "WA":
            from config.states.wa import WA_CONFIG
            register_state(WA_CONFIG)
        elif code == "ID":
            from config.states.id import ID_CONFIG
            register_state(ID_CONFIG)
        elif code == "NY":
            from config.states.ny import NY_CONFIG
            register_state(NY_CONFIG)
        elif code == "TX":
            from config.states.tx import TX_CONFIG
            register_state(TX_CONFIG)
    except ImportError:
        pass
