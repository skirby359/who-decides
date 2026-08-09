"""District profile system for multi-district political analysis.

Each district (congressional or legislative) is defined by a DistrictProfile
that encapsulates all district-specific parameters: geographic boundaries,
race detection patterns, voter filtering criteria, and historical data.

Hand-tuned profiles exist for CD-05 and LD-03.  Any other valid WA district
(cd01–cd10, ld01–ld49) is auto-generated on first access via
:func:`auto_profile`.

Arbitrary local races (mayors, judges, school boards, etc.) are supported
via :func:`race_profile`, which builds a profile from an exact race name.

Usage::

    from config.districts import get_profile, list_profiles, race_profile

    profile = get_profile("cd05")   # Hand-tuned Congressional District 5
    profile = get_profile("cd03")   # Auto-generated Congressional District 3
    profile = get_profile("ld15")   # Auto-generated Legislative District 15
    profile = race_profile("City of Spokane Mayor")  # Arbitrary local race
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class DistrictProfile:
    """Configuration profile for a single political district.

    Each field parameterizes district-specific behavior that was previously
    hardcoded for WA-05 throughout the codebase.
    """

    # --- Identity ---
    district_id: str               # "cd05", "ld03"
    district_type: str             # "congressional" or "legislative"
    district_number: str           # "05", "03"
    district_label: str            # "WA-05", "WA LD-03"
    district_description: str      # Multi-sentence description for reports

    # --- Geography: SOS county codes ---
    county_codes: set[str]         # All counties fully/partially in district
    split_county_codes: set[str]   # Counties only partially in district
    county_fips: dict[str, str]    # FIPS code -> county name (for Census API)

    # --- Election result filtering ---
    race_pattern: re.Pattern       # Regex to match district-specific races in SOS CSV
    statewide_races: bool = True   # Whether to also load statewide races

    # --- VRDB voter filtering ---
    voter_filter_field: str = "CongressionalDistrict"
    voter_filter_values: list[str] = field(default_factory=lambda: ["5", "05"])

    # --- FEC campaign finance (federal races) ---
    fec_enabled: bool = True       # False for state legislative districts
    fec_district: str = ""         # "05" for congressional, "" for legislative
    fec_office: str = "H"          # "H" for House, "" for legislative

    # --- PDC campaign finance (state races) ---
    pdc_enabled: bool = False      # True for state legislative districts

    # --- Historical district performance ---
    # Maps year -> dem two-party pct.  Empty dict means "compute from data".
    historical_performance: dict[int, float] = field(default_factory=dict)

    # Presidential vote at district level (D two-party %) for Cook PVI.
    # NOT the congressional race results (those are in historical_performance).
    presidential_performance: dict[int, float] = field(default_factory=dict)

    # --- Target election year ---
    # Override to analyze a specific election year (e.g., odd-year local race).
    # None means auto-detect (current year).
    target_year: int | None = None

    # --- Database ---
    db_filename: str = ""          # "wa_cd05.duckdb" or "wa_ld03.duckdb"

    # --- Partisan lean race priority ---
    # SQL CASE fragment for partisan_lean.py best-race selection.
    # Defines what race gets priority 1 for computing precinct lean.
    race_priority_sql: str = ""

    # --- Canvassing geographic context ---
    urban_counties: set[str] = field(default_factory=set)

    # --- Candidate info (optional, enhances forecast + name recognition) ---
    our_candidate: str = ""            # e.g. "Cathy McMorris Rodgers"
    opponent_candidate: str = ""       # e.g. "Carmichael Casto"
    is_incumbent: bool = False         # Is our candidate the incumbent?
    prior_races_in_district: int = 0   # How many prior races our candidate has run here
    name_recognition_override: int = 0 # Manual 1-5 score (0 = auto-derive from data)

    @property
    def finance_enabled(self) -> bool:
        """True if any campaign finance source is available (FEC or PDC)."""
        return self.fec_enabled or self.pdc_enabled

    def voter_filter_sql(self, table_alias: str = "") -> str:
        """Build a SQL WHERE clause fragment for voter district filtering.

        Args:
            table_alias: Optional table alias prefix (e.g., "v." for "v.column").

        Returns:
            SQL fragment like "v.congressional_district IN ('5', '05')".
            For local races (precinct_based), returns "1=1" (no filter).
        """
        if self.voter_filter_field == "precinct_based":
            return "1=1"
        prefix = f"{table_alias}." if table_alias else ""
        col = ("congressional_district"
               if self.voter_filter_field == "CongressionalDistrict"
               else "legislative_district")
        placeholders = ", ".join(f"'{v}'" for v in self.voter_filter_values)
        return f"{prefix}{col} IN ({placeholders})"

    def voter_filter_db_column(self) -> str:
        """Return the DB column name corresponding to the VRDB filter field."""
        if self.voter_filter_field == "precinct_based":
            return ""
        if self.voter_filter_field == "CongressionalDistrict":
            return "congressional_district"
        return "legislative_district"

    # --- candidate_finance scoping --------------------------------------
    # The implementation lives in the module-level functions below so any
    # profile-like object (incl. test SimpleNamespace stubs) can be scoped via
    # ``candidate_finance_scope_sql(profile)``. These wrappers expose it on the
    # profile for convenience / discoverability.

    @property
    def finance_office_codes(self) -> tuple[str, ...]:
        """``candidate_finance.office`` codes identifying THIS district's
        candidates (see :func:`finance_office_codes`)."""
        return finance_office_codes(self.district_type, self.district_id)

    @property
    def finance_district_keys(self) -> tuple[str, ...]:
        """``candidate_finance.district`` value(s) to match for this district
        (see :func:`finance_district_keys`)."""
        return finance_district_keys(self.district_number)

    def candidate_finance_scope_sql(
        self, alias: str = "",
    ) -> tuple[str, list[str]] | None:
        """See :func:`candidate_finance_scope_sql`."""
        return candidate_finance_scope_sql(self, alias)


# ---------------------------------------------------------------------------
# candidate_finance office/district scoping (CD vs LD collision guard)
# ---------------------------------------------------------------------------
# candidate_finance is a SHARED table: federal House filings (office='H',
# district zero-padded e.g. '03') sit alongside state-legislative filings
# (office IN ('SR','SS'), district bare e.g. '3') under the SAME numeric
# `district` column. A query scoped on the number alone therefore conflates a
# congressional district with a same-numbered legislative one — e.g. an ld03
# report keyed on district='03' pulls in WA-03's congressional incumbent
# (Gluesenkamp Perez, $M-scale FEC totals) instead of the LD-3 state-house
# candidates. Always scope by office class too. These are module-level
# functions (reading attributes via getattr) so any profile-like object —
# including test SimpleNamespace stubs — can be scoped. (The neutral product
# layer encodes the same mapping in `_SCAN_FINANCE_OFFICES`; keep in sync.)

def finance_office_codes(district_type: str, district_id: str) -> tuple[str, ...]:
    """``candidate_finance.office`` codes for a district of this type/id.
    Empty => no office scoping (local race-xxx; keyed by county/candidate
    name, not a numeric district)."""
    if district_type == "congressional":
        return ("H",)                           # FEC U.S. House
    if district_type == "legislative":
        did = (district_id or "").lower()
        if did.startswith("sd"):
            return ("SS",)                      # upper chamber only (Senate)
        if did.startswith(("ad", "hd")):
            return ("SR",)                      # lower chamber only (Assembly/House)
        return ("SR", "SS")                     # WA/ID unicameral 'ld': rep + senator
    return ()


def finance_district_keys(district_number: str) -> tuple[str, ...]:
    """``candidate_finance.district`` value(s) to match. Federal rows store the
    number zero-padded ('05'); state-legislative rows store it bare ('5'), and
    the per-district PDC loader pads while the statewide loader leaves it bare —
    so match both forms. Empty when there's no numeric id (local races)."""
    digits = "".join(ch for ch in (district_number or "") if ch.isdigit())
    if not digits:
        return ()
    bare = digits.lstrip("0") or "0"
    padded = bare.zfill(2)
    return (bare,) if bare == padded else (bare, padded)


def candidate_finance_scope_sql(
    profile, alias: str = "",
) -> tuple[str, list[str]] | None:
    """SQL WHERE fragment + params scoping a ``candidate_finance`` query to this
    district's office class AND numeric district, so a congressional district
    never collides with a same-numbered legislative one.

    Accepts any object exposing ``district_type`` / ``district_id`` /
    ``district_number`` (a full :class:`DistrictProfile` or a duck-typed stub).
    Returns ``None`` when there's no numeric/office scoping (local race-xxx —
    those use a county/name-based finance path). The fragment begins with
    ``AND `` and drops into an existing WHERE clause::

        scope = candidate_finance_scope_sql(profile, "cf")
        if scope is None:
            rows = []                           # no district-scoped finance
        else:
            frag, params = scope
            rows = conn.execute(
                f"SELECT ... FROM candidate_finance cf "
                f"WHERE cf.election_cycle = ? {frag} ...",
                [cycle, *params]).fetchall()
    """
    offices = finance_office_codes(
        getattr(profile, "district_type", "") or "",
        getattr(profile, "district_id", "") or "",
    )
    keys = finance_district_keys(getattr(profile, "district_number", "") or "")
    if not offices or not keys:
        return None
    p = f"{alias}." if alias else ""
    frag = (
        f"AND {p}office IN ({', '.join('?' * len(offices))}) "
        f"AND {p}district IN ({', '.join('?' * len(keys))})"
    )
    return frag, [*offices, *keys]


# ---------------------------------------------------------------------------
# County reference data — resolved from StateConfig
# ---------------------------------------------------------------------------

def _get_county_data() -> tuple[dict[str, tuple[str, str]], set[str], dict[str, str]]:
    """Get county data from StateConfig. Falls back to WA if unavailable."""
    try:
        from config.state_config import get_state_config
        sc = get_state_config()
        counties = {code: (info.name, info.fips) for code, info in sc.counties.items()}
        sos_codes = set(counties.keys())
        fips_map = {fips: name for _, (name, fips) in counties.items()}
        return counties, sos_codes, fips_map
    except ImportError:
        return {}, set(), {}


_WA_COUNTIES, _ALL_SOS_CODES, _ALL_COUNTY_FIPS = _get_county_data()

# District counts — resolved from StateConfig at import time
try:
    from config.state_config import get_state_config as _get_sc
    _sc = _get_sc()
    _MAX_CONGRESSIONAL = _sc.congressional_districts
    _MAX_LEGISLATIVE = _sc.legislative_districts
except (ImportError, ValueError):
    _MAX_CONGRESSIONAL = 10   # WA defaults as fallback
    _MAX_LEGISLATIVE = 49


def _chamber_counts() -> tuple[int, int, int | None, str]:
    """Resolve (congressional, lower-chamber, upper-chamber|None, prefix) for
    the *current* state, read dynamically so a mid-process ``STATE`` switch is
    honored (the module-level ``_MAX_*`` constants are import-time snapshots).

    Unicameral states (WA, ID) return ``upper=None`` → enumerate ``cd``/``ld``.
    Bicameral states (NY) return ``upper`` set → enumerate ``cd``/``ad``/``sd``
    where the lower chamber is Assembly (``ad``) and the upper is Senate (``sd``).
    """
    try:
        from config.state_config import get_state_config
        sc = get_state_config()
        return (sc.congressional_districts, sc.legislative_districts,
                sc.upper_chamber_districts, sc.district_prefix)
    except (ImportError, ValueError):
        return (_MAX_CONGRESSIONAL, _MAX_LEGISLATIVE, None, "WA")


# cd/ld are 1-2 digit (WA/ID); bicameral lower chambers (ad=NY Assembly,
# hd=TX House) go to 150 so allow 3 digits. sd=Senate (upper).
_DISTRICT_ID_PATTERN = re.compile(r"^(cd|ld|ad|hd|sd)(\d{1,3})$", re.IGNORECASE)


def _lower_chamber_meta() -> tuple[str, str, str]:
    """(prefix, race_keyword, chamber_name) for the current state's bicameral
    LOWER chamber, read dynamically from StateConfig so a mid-process ``STATE``
    switch is honored. Defaults to NY's Assembly (``ad``/``assembly``/``Assembly``)
    so unicameral states and NY need no config. TX overrides to House
    (``hd``/``house``/``House``)."""
    try:
        from config.state_config import get_state_config
        sc = get_state_config()
        return (sc.lower_chamber_prefix, sc.lower_chamber_race_keyword,
                sc.lower_chamber_name)
    except (ImportError, ValueError):
        return ("ad", "assembly", "Assembly")


# ---------------------------------------------------------------------------
# Auto-generated profiles
# ---------------------------------------------------------------------------

def auto_profile(district_id: str) -> DistrictProfile:
    """Auto-generate a DistrictProfile from a district ID.

    Accepts IDs in the form ``cdNN`` (congressional) or ``ldNN``
    (legislative), where *NN* is a 1- or 2-digit district number.

    Auto-generated profiles use all 39 WA counties as "split" counties
    so that the ``race_pattern`` regex does all precinct filtering.
    This works correctly without any redistricting/geographic data.

    For hand-tuned profiles with explicit county sets and historical
    performance data, create a separate profile file (see ``cd05.py``
    and ``ld03.py`` for examples).

    Args:
        district_id: District identifier like ``"cd03"`` or ``"ld15"``.

    Returns:
        A fully populated :class:`DistrictProfile`.

    Raises:
        ValueError: If the ID format is invalid or the district number
            is out of range.
    """
    did = district_id.lower().strip()
    m = _DISTRICT_ID_PATTERN.match(did)
    if not m:
        raise ValueError(
            f"Invalid district ID '{district_id}'. "
            f"Expected format: cdNN (congressional) or ldNN (legislative). "
            f"Examples: cd03, ld15"
        )

    prefix = m.group(1).lower()   # "cd", "ld", "ad"/"hd", or "sd"
    num = int(m.group(2))         # district number as integer
    cong, lower, upper, _ = _chamber_counts()
    low_prefix, low_keyword, low_name = _lower_chamber_meta()

    bicameral = upper is not None
    if prefix == "cd":
        if num < 1 or num > cong:
            raise ValueError(
                f"Congressional district {num} out of range (1–{cong})."
            )
        return _build_congressional_profile(num)
    elif prefix == "ld":
        if bicameral:
            raise ValueError(
                f"This state is bicameral — use '{low_prefix}' ({low_name}) or "
                "'sd' (Senate), not 'ld'."
            )
        if num < 1 or num > lower:
            raise ValueError(
                f"Legislative district {num} out of range (1–{lower})."
            )
        return _build_legislative_profile(num)
    elif prefix == low_prefix:
        if not bicameral:
            raise ValueError(
                "This state is unicameral — use 'ld', not "
                f"'{low_prefix}'."
            )
        # Lower chamber (Assembly/House) — count == lower-chamber count.
        if num < 1 or num > lower:
            raise ValueError(
                f"{low_name} district {num} out of range (1–{lower})."
            )
        return _build_chamber_profile(low_prefix, num, low_keyword, low_name)
    elif prefix == "sd":  # upper chamber (Senate)
        if not bicameral:
            raise ValueError(
                "This state is unicameral — use 'ld', not 'sd'."
            )
        cap = upper or 0
        if num < 1 or num > cap:
            raise ValueError(
                f"Senate district {num} out of range (1–{cap})."
            )
        return _build_chamber_profile("sd", num, "senate", "Senate")
    else:  # recognized prefix that isn't valid for this state's chambers
        raise ValueError(
            f"Prefix '{prefix}' is not a valid chamber for this state."
        )


def _build_congressional_profile(num: int) -> DistrictProfile:
    """Build an auto-generated profile for a congressional district."""
    padded = f"{num:02d}"
    dn_int = str(num)
    try:
        from config.state_config import get_state_config
        _sc = get_state_config()
        prefix = _sc.district_prefix
        state_name = _sc.state_name
    except Exception:
        prefix, state_name = "WA", "Washington"

    return DistrictProfile(
        district_id=f"cd{padded}",
        district_type="congressional",
        district_number=padded,
        district_label=f"{prefix}-{padded}",
        district_description=(
            f"{state_name}'s {_ordinal(num)} Congressional District."
        ),

        # All counties as split — race_pattern does the real filtering
        county_codes=set(_ALL_SOS_CODES),
        split_county_codes=set(_ALL_SOS_CODES),
        county_fips=dict(_ALL_COUNTY_FIPS),

        race_pattern=re.compile(
            rf"congressional\s+district\s+0?{dn_int}\b", re.IGNORECASE,
        ),
        statewide_races=True,

        voter_filter_field="CongressionalDistrict",
        voter_filter_values=[dn_int, padded],

        fec_enabled=True,
        fec_district=padded,
        fec_office="H",
        pdc_enabled=False,

        historical_performance={},
        db_filename=f"wa_cd{padded}.duckdb",

        race_priority_sql=(
            f"WHEN r.office = 'U.S. Representative'\n"
            f"                    AND regexp_matches(UPPER(r.race_name), '.*DISTRICT\\s+0?{dn_int}\\b')\n"
            f"                    THEN 1"
        ),

        urban_counties=set(),
    )


def _build_legislative_profile(num: int) -> DistrictProfile:
    """Build an auto-generated profile for a legislative district."""
    padded = f"{num:02d}"
    dn_int = str(num)
    try:
        from config.state_config import get_state_config
        _sc = get_state_config()
        prefix = _sc.district_prefix
        state_name = _sc.state_name
    except Exception:
        prefix, state_name = "WA", "Washington"

    return DistrictProfile(
        district_id=f"ld{padded}",
        district_type="legislative",
        district_number=padded,
        district_label=f"{prefix} LD-{padded}",
        district_description=(
            f"{state_name}'s {_ordinal(num)} Legislative District."
        ),

        # All counties as split — race_pattern does the real filtering
        county_codes=set(_ALL_SOS_CODES),
        split_county_codes=set(_ALL_SOS_CODES),
        county_fips=dict(_ALL_COUNTY_FIPS),

        race_pattern=re.compile(
            rf"legislative\s+district\s+0?{dn_int}\b", re.IGNORECASE,
        ),
        statewide_races=True,

        voter_filter_field="LegislativeDistrict",
        voter_filter_values=[dn_int, padded],

        fec_enabled=False,
        fec_district="",
        fec_office="",
        pdc_enabled=True,

        historical_performance={},
        db_filename=f"wa_ld{padded}.duckdb",

        race_priority_sql=(
            f"WHEN regexp_matches(UPPER(r.race_name), '.*LEGISLATIVE DISTRICT\\s+0?{dn_int}\\b')\n"
            f"                    AND (UPPER(r.race_name) LIKE '%REPRESENTATIVE%'\n"
            f"                         OR UPPER(r.race_name) LIKE '%SENATOR%')\n"
            f"                    THEN 1"
        ),

        urban_counties=set(),
    )


def _build_chamber_profile(
    prefix: str, num: int, race_keyword: str, chamber_name: str,
) -> DistrictProfile:
    """Build an auto-generated profile for a bicameral legislative chamber.

    Used for NY's ``ad`` (Assembly, lower) and ``sd`` (Senate, upper). Mirrors
    :func:`_build_legislative_profile` (state-finance race, no FEC) but with a
    chamber-specific race pattern (``ASSEMBLY DISTRICT N`` / ``SENATE DISTRICT
    N``) and label. Assembly is zero-padded to 3 digits (counts to 150) so IDs
    sort correctly; Senate to 2.
    """
    # Lower chamber (ad/hd) counts to 150 -> 3 digits; Senate (sd) -> 2.
    width = 2 if prefix == "sd" else 3
    padded = f"{num:0{width}d}"
    dn_int = str(num)
    try:
        from config.state_config import get_state_config
        _sc = get_state_config()
        state_prefix = _sc.district_prefix
        state_name = _sc.state_name
    except Exception:
        state_prefix, state_name = "NY", "New York"

    return DistrictProfile(
        district_id=f"{prefix}{padded}",
        district_type="legislative",
        district_number=padded,
        district_label=f"{state_prefix} {prefix.upper()}-{padded}",
        district_description=(
            f"{state_name}'s {_ordinal(num)} {chamber_name} District."
        ),

        # All counties as split — race_pattern does the real filtering.
        county_codes=set(_ALL_SOS_CODES),
        split_county_codes=set(_ALL_SOS_CODES),
        county_fips=dict(_ALL_COUNTY_FIPS),

        race_pattern=re.compile(
            rf"{race_keyword}\s+district\s+0?{dn_int}\b", re.IGNORECASE,
        ),
        statewide_races=True,

        # Voter-file filtering is unused for NY (forecast-only this cycle); keep
        # the legislative column so the profile is well-formed.
        voter_filter_field="LegislativeDistrict",
        voter_filter_values=[dn_int, padded],

        fec_enabled=False,
        fec_district="",
        fec_office="",
        pdc_enabled=True,

        historical_performance={},
        db_filename=f"{state_prefix.lower()}_{prefix}{padded}.duckdb",

        race_priority_sql=(
            f"WHEN regexp_matches(UPPER(r.race_name), "
            f"'.*{race_keyword.upper()} DISTRICT\\s+0?{dn_int}\\b')\n"
            f"                    THEN 1"
        ),

        urban_counties=set(),
    )


def _ordinal(n: int) -> str:
    """Return an ordinal string for an integer: 1 → '1st', 2 → '2nd', etc."""
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


# ---------------------------------------------------------------------------
# Arbitrary race profiles
# ---------------------------------------------------------------------------

def _slugify(text: str) -> str:
    """Convert a race name to a URL-safe slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower().strip())
    return slug.strip("-")


def race_profile(
    race_name: str,
    variants: list[str] | None = None,
) -> DistrictProfile:
    """Build a DistrictProfile for an arbitrary race name.

    The resulting profile uses all 39 WA counties so that geography is
    auto-detected from which precincts have results for the race.

    Args:
        race_name: Display name for the race (used in labels/reports).
        variants: Optional list of all raw SOS race name strings that
            represent this race across years.  When provided, the
            ``race_pattern`` matches *any* variant.  When ``None``,
            falls back to exact (case-insensitive) matching on
            *race_name* alone.

    Returns:
        A fully populated :class:`DistrictProfile` with ``district_type="local"``.
    """
    slug = _slugify(race_name)
    district_id = f"race-{slug}"

    # Build a regex that matches any variant (or just the single name)
    all_names = variants if variants else [race_name]
    escaped_alts = [re.escape(n) for n in all_names]
    if len(escaped_alts) == 1:
        pattern = re.compile(escaped_alts[0], re.IGNORECASE)
    else:
        pattern = re.compile("|".join(escaped_alts), re.IGNORECASE)

    # SQL CASE: match any variant as priority 1
    sql_conditions = " OR ".join(
        f"LOWER(r.race_name) = LOWER('{n.replace(chr(39), chr(39)+chr(39))}')"
        for n in all_names
    )
    race_priority_sql = (
        f"WHEN ({sql_conditions})\n"
        f"                    THEN 1"
    )

    return DistrictProfile(
        district_id=district_id,
        district_type="local",
        district_number="",
        district_label=race_name,
        district_description=f"Local race analysis: {race_name}.",

        county_codes=set(_ALL_SOS_CODES),
        split_county_codes=set(_ALL_SOS_CODES),
        county_fips=dict(_ALL_COUNTY_FIPS),

        race_pattern=pattern,
        statewide_races=True,

        voter_filter_field="precinct_based",
        voter_filter_values=[],

        fec_enabled=False,
        fec_district="",
        fec_office="",
        pdc_enabled=False,

        historical_performance={},
        db_filename=f"wa_race_{slug}.duckdb",

        race_priority_sql=race_priority_sql,
        urban_counties=set(),
    )


# ---------------------------------------------------------------------------
# Profile registry
# ---------------------------------------------------------------------------

# Runtime registry: race-xxx profiles + auto-generated cache for the active
# state. Single-state-per-process (STATE env), so this is the active state's.
_PROFILES: dict[str, DistrictProfile] = {}

# Hand-tuned built-ins are STATE-SCOPED — WA's CD05/LD03 must not leak into NY
# (where they'd shadow the auto-generated NY profile or add a bogus ld03).
_BUILTIN_BY_STATE: dict[str, dict[str, DistrictProfile]] = {}

# Auto-generated profile cache, STATE-SCOPED so a process that touches more than
# one state (tests, dashboards, sequential record_predictions) never returns a
# cd05 it built for the wrong state.
_AUTO_CACHE_BY_STATE: dict[str, dict[str, DistrictProfile]] = {}


def _current_state_code() -> str:
    try:
        from config.state_config import get_state_config
        return get_state_config().state_code
    except Exception:
        return "WA"


def _register_builtin(state_code: str, profile: DistrictProfile) -> None:
    """Register a hand-tuned profile scoped to a single state."""
    _BUILTIN_BY_STATE.setdefault(state_code, {})[profile.district_id] = profile


# ---------------------------------------------------------------------------
# Persisted race-profile registry
# ---------------------------------------------------------------------------

# Race profiles are otherwise runtime-only: race_profile() builds one and
# register_profile() puts it in _PROFILES, which dies with the process. Any
# later job that reads a race-xxx district_id back out of the database then
# cannot rebuild it. The YAML registry makes them resolvable from a clean
# process, and — more importantly — pins each race's `variants` list, since
# rebuilding from the display name alone silently drops cycles filed under a
# different name (see config/race_profiles/WA.yml).
_RACE_REGISTRY_ROOT = Path(__file__).resolve().parents[1] / "race_profiles"
_RACE_REGISTRY_BY_STATE: dict[str, dict[str, dict]] = {}


def race_registry_path(state_code: str | None = None) -> Path:
    """Path to the active (or given) state's race-profile registry file."""
    return _RACE_REGISTRY_ROOT / f"{state_code or _current_state_code()}.yml"


def load_race_registry(state_code: str | None = None,
                       *, refresh: bool = False) -> dict[str, dict]:
    """Load ``{race-slug: {name, variants}}`` for a state, cached per state.

    Missing file, empty file, or unreadable YAML all yield ``{}`` — a broken
    registry must not take down every ``get_profile`` call in the process.
    """
    state = state_code or _current_state_code()
    if not refresh and state in _RACE_REGISTRY_BY_STATE:
        return _RACE_REGISTRY_BY_STATE[state]

    entries: dict[str, dict] = {}
    path = race_registry_path(state)
    if path.exists():
        try:
            import yaml
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            for row in (data.get("races") or []):
                name = (row or {}).get("name")
                if not name:
                    continue
                variants = list(row.get("variants") or [name])
                if name not in variants:
                    variants.insert(0, name)
                entries[f"race-{_slugify(name)}"] = {
                    "name": name, "variants": variants,
                }
        except Exception:  # noqa: BLE001 - registry is best-effort
            entries = {}
    _RACE_REGISTRY_BY_STATE[state] = entries
    return entries


def race_profile_from_registry(district_id: str) -> DistrictProfile | None:
    """Rebuild a race profile from the persisted registry, or None."""
    entry = load_race_registry().get(district_id.lower().strip())
    if not entry:
        return None
    return race_profile(entry["name"], variants=entry["variants"])


def register_profile(profile: DistrictProfile) -> None:
    """Register a district profile in the runtime registry (race profiles,
    auto-cache). For state-specific hand-tuned profiles use ``_register_builtin``."""
    _PROFILES[profile.district_id] = profile


def get_profile(district_id: str | None = None) -> DistrictProfile:
    """Look up a district profile by its ID.

    Hand-tuned profiles (e.g. CD-05, LD-03) are checked first.  If the
    ID is not in the registry, :func:`auto_profile` attempts to generate
    one.  Auto-generated profiles are cached for subsequent lookups.

    Args:
        district_id: Profile identifier such as ``"cd05"``, ``"cd03"``,
            or ``"ld15"``.  If ``None``, the active state's default district
            (``StateConfig.default_district``) is returned — a STATE-AWARE
            fallback for callers that have no specific profile to pass.
            (Replaces a hardcoded ``get_profile("cd05")`` that raised
            "district 5 out of range" for states with fewer CDs, e.g. ID.)

    Returns:
        The matching DistrictProfile.

    Raises:
        ValueError: If *district_id* is not a valid district for the state.
    """
    if district_id is None:
        try:
            from config.state_config import get_state_config
            district_id = get_state_config().default_district
        except Exception:
            district_id = "cd05"
    did = district_id.lower().strip()
    if did in _PROFILES:
        return _PROFILES[did]

    state = _current_state_code()
    # State-scoped hand-tuned built-ins (e.g. WA CD05/LD03) — only for the
    # current state, so they never shadow another state's auto profile.
    builtins = _BUILTIN_BY_STATE.get(state, {})
    if did in builtins:
        return builtins[did]

    # State-scoped auto-generated cache.
    auto_cache = _AUTO_CACHE_BY_STATE.setdefault(state, {})
    if did in auto_cache:
        return auto_cache[did]

    # Race profiles are runtime-built, so fall back to the checked-in registry
    # before giving up — that is what lets a fresh process resolve a race-xxx
    # district_id read back out of the database, with its full variant set.
    if did.startswith("race-"):
        from_registry = race_profile_from_registry(did)
        if from_registry is not None:
            _PROFILES[did] = from_registry
            return from_registry
        raise ValueError(
            f"Race profile '{district_id}' not found. "
            f"Use --race \"Race Name\" to create and register a local race profile, "
            f"then 'python main.py save-race-profile --race \"Race Name\"' to "
            f"persist it in {race_registry_path().as_posix()}, "
            f"or use 'python main.py search \"keyword\"' to find race names."
        )

    # Try auto-generating a profile (cached per-state, not in the shared
    # runtime registry, to avoid cross-state cache bleed).
    profile = auto_profile(did)
    auto_cache[did] = profile
    return profile


def list_profiles() -> list[str]:
    """Return a sorted list of all available district IDs for the current state.

    Unicameral states (WA: cd01–cd10, ld01–ld49; ID): ``cd`` + ``ld``.
    Bicameral states (NY): ``cd`` + ``ad`` (Assembly, lower) + ``sd`` (Senate,
    upper). Counts are resolved dynamically from ``StateConfig`` so a mid-process
    ``STATE`` switch is honored.
    """
    cong, lower, upper, _ = _chamber_counts()
    # Only race-xxx (local) profiles from the runtime registry — cd/ld/ad/sd are
    # covered by enumeration below, and the auto-cache is state-scoped elsewhere.
    all_ids = {k for k in _PROFILES if k.startswith("race-")}
    # Persisted race profiles are available even in a process that has not
    # built them yet, so list them alongside the runtime-registered ones.
    all_ids.update(load_race_registry().keys())
    all_ids.update(_BUILTIN_BY_STATE.get(_current_state_code(), {}).keys())
    for i in range(1, cong + 1):
        all_ids.add(f"cd{i:02d}")
    if upper:  # bicameral → lower chamber (Assembly/House) + Senate
        low_prefix, _, _ = _lower_chamber_meta()
        for i in range(1, lower + 1):
            all_ids.add(f"{low_prefix}{i:03d}")
        for i in range(1, upper + 1):
            all_ids.add(f"sd{i:02d}")
    else:      # unicameral → single legislative chamber
        for i in range(1, lower + 1):
            all_ids.add(f"ld{i:02d}")
    return sorted(all_ids)


# ---------------------------------------------------------------------------
# Auto-register built-in profiles on import
# ---------------------------------------------------------------------------

from config.districts.cd05 import CD05_PROFILE  # noqa: E402
from config.districts.ld03 import LD03_PROFILE  # noqa: E402

# WA-only hand-tuned profiles — scoped to WA so they don't leak into NY/ID.
_register_builtin("WA", CD05_PROFILE)
_register_builtin("WA", LD03_PROFILE)
