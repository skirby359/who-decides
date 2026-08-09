from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # State selection — set STATE=ID in .env for Idaho, defaults to WA
    state: str = "WA"

    db_path: Path = PROJECT_ROOT / "data" / "wa_statewide.duckdb"
    raw_data_dir: Path = PROJECT_ROOT / "data" / "raw"
    report_output_dir: Path = PROJECT_ROOT / "reports"
    templates_dir: Path = PROJECT_ROOT / "templates"
    census_api_key: str = ""
    fec_api_key: str = ""
    bls_api_key: str = ""
    ai_api_key: str = ""
    ai_provider: str = "anthropic"  # "anthropic" or "openai"
    # Model overrides (optional). Empty string = use library default.
    # Use unversioned aliases (e.g. "claude-sonnet-4-6") so the model
    # auto-resolves to the current dated release. Hard-pin a date only
    # when reproducibility matters more than freshness.
    ai_anthropic_model: str = ""
    ai_openai_model: str = ""
    default_district: str = ""
    default_party: str = "Democratic"
    vrdb_file_pattern: str = "*.txt"

    # White-label branding (optional — set in .env or via CLI flags)
    firm_name: str = ""
    logo_path: str = ""
    analyst_name: str = ""
    client_name: str = ""

    @field_validator("db_path", mode="before")
    @classmethod
    def default_db_path(cls, v):
        """Use default if empty string provided (e.g., DB_PATH= in .env)."""
        if not v or str(v).strip() == "":
            return PROJECT_ROOT / "data" / "wa_statewide.duckdb"
        return v

    @property
    def state_config(self):
        """Get the active StateConfig for the configured state."""
        from config.state_config import get_state_config
        return get_state_config(self.state)

    @property
    def resolved_db_path(self) -> Path:
        """Database path resolved from state config if db_path is default."""
        # If user set a custom DB_PATH, use it; otherwise derive from state
        default = PROJECT_ROOT / "data" / "wa_statewide.duckdb"
        if self.db_path == default:
            sc = self.state_config
            return PROJECT_ROOT / "data" / sc.statewide_db_name
        return self.db_path

    @property
    def resolved_default_district(self) -> str:
        """Default district from state config if not explicitly set."""
        if self.default_district:
            return self.default_district
        return self.state_config.default_district

    @property
    def vrdb_db_path(self) -> Path:
        """Return the path to the shared statewide VRDB database."""
        sc = self.state_config
        return self.db_path.parent / sc.vrdb_db_name

    def db_path_for_district(self, district_id: str) -> Path:
        """Return the database path for a specific district profile.

        .. deprecated:: Statewide refactor
            All districts now share a single statewide DB.  This method
            is kept for backward compatibility but just returns ``db_path``.
        """
        return self.db_path

    def ensure_dirs(self):
        """Create data directories if they don't exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.report_output_dir.mkdir(parents=True, exist_ok=True)
        for subdir in [
            "election_results", "shapefiles", "vrdb",
            "crosswalk", "census", "fec",
        ]:
            (self.raw_data_dir / subdir).mkdir(parents=True, exist_ok=True)


settings = Settings()

# ---------------------------------------------------------------------------
# Election cycles to query for campaign finance data (FEC + PDC).
# Even years only; update this list as new cycles become available.
# ---------------------------------------------------------------------------
ELECTION_CYCLES: list[int] = [2018, 2020, 2022, 2024, 2026]
