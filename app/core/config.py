"""
Application configuration.

Settings are loaded from environment variables (and an optional .env file)
using pydantic-settings. Only Phase 1 settings are defined here — settings
needed for later phases (DB, JWT, external providers, LLM) will be added
in their respective phases.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- App metadata ---
    APP_NAME: str = "Ocean Agentic AI"
    APP_VERSION: str = "0.1.0"
    APP_DESCRIPTION: str = (
        "Backend for a marine ecosystem intelligence platform combining "
        "oceanographic, weather, tide, wave and satellite data with "
        "specialized AI agents."
    )

    # --- Environment ---
    ENVIRONMENT: str = "development"  # development | staging | production
    DEBUG: bool = True

    # --- Logging ---
    LOG_LEVEL: str = "INFO"

    # --- Database ---
    # Local-dev default only; override via .env / real env vars for staging/prod.
    # Never commit real credentials here.
    DATABASE_URL: str = (
        "postgresql+psycopg2://postgres:postgres@localhost:5432/ocean_agentic_ai"
    )
    DB_ECHO: bool = False  # set true to log SQL statements (debug only)

    # --- Auth / JWT ---
    # SECRET_KEY has no safe default — must be set via env/.env in any real
    # deployment. The fallback below is only so local dev doesn't hard-fail
    # on first run; it is not a usable secret.
    SECRET_KEY: str = "CHANGE_ME_INSECURE_DEV_ONLY_SECRET_KEY"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- IMD provider ---
    # Base URL and endpoints verified against IMD's official API reference
    # (https://api.imd.gov.in/public/api_reference.html) on 2026-09-09.
    #
    # IMPORTANT — access model is not fully confirmed:
    # IMD's API portal (https://api.imd.gov.in) requires account
    # registration and mentions IP whitelisting for server-to-server access.
    # The published reference does not show an API-key header or query
    # param on any endpoint, which suggests access may be gated purely by
    # whitelisting the calling server's IP rather than a request-level key.
    # IMD_API_KEY / IMD_API_KEY_HEADER exist so a key can be wired in via
    # env vars if IMD's dashboard turns out to require one — do not assume
    # a value or header name until confirmed via the registered account.
    IMD_API_BASE_URL: str = "https://api.imd.gov.in/api/v1"
    IMD_API_KEY: str | None = None
    IMD_API_KEY_HEADER: str = "Authorization"
    IMD_REQUEST_TIMEOUT_SECONDS: float = 10.0

    # --- Open-Meteo Marine provider ---
    # Verified against https://open-meteo.com/en/docs/marine-weather-api and
    # https://open-meteo.com/en/terms on 2026-09-09.
    # No API key is required for non-commercial use (free tier). Free-tier
    # limits per Open-Meteo's terms: <10,000 calls/day, 5,000/hour, 600/min.
    # apikey is only needed for the paid "customer-api.open-meteo.com" tier —
    # left optional/unset here since this project uses the free tier.
    OPEN_METEO_MARINE_BASE_URL: str = "https://marine-api.open-meteo.com/v1/marine"
    OPEN_METEO_API_KEY: str | None = None
    OPEN_METEO_REQUEST_TIMEOUT_SECONDS: float = 10.0

    # --- NASA Ocean Color (OB.DAAC) provider ---
    # Verified against https://oceandata.sci.gsfc.nasa.gov/file_search/file_search_help
    # on 2026-09-09. Unlike IMD/Open-Meteo, OB.DAAC has no simple lat/lon
    # point-value endpoint — file_search returns a list of matching
    # satellite granule/product FILES (e.g. L3 mapped chlorophyll for a
    # date), not a chlorophyll value at a coordinate. Extracting an actual
    # point value requires downloading the returned NetCDF file (needs an
    # Earthdata Login "appkey") and reading the pixel nearest the requested
    # coordinate — a materially different, heavier integration that is NOT
    # implemented yet (see provider docstring). We do not fabricate that
    # response; the endpoint returns 501 until it's built for real.
    NASA_OCEAN_COLOR_FILE_SEARCH_URL: str = "https://oceandata.sci.gsfc.nasa.gov/file_search"
    # Optional — only needed to search/download restricted (non-public) data.
    # Get one at https://oceandata.sci.gsfc.nasa.gov/appkey/ after registering
    # for an Earthdata Login (https://urs.earthdata.nasa.gov/).
    NASA_OCEAN_COLOR_APPKEY: str | None = None
    NASA_OCEAN_COLOR_REQUEST_TIMEOUT_SECONDS: float = 15.0

    # --- NOAA CO-OPS (Tides & Currents) provider ---
    # Verified against https://api.tidesandcurrents.noaa.gov/api/prod/ on
    # 2026-09-09. Single GET endpoint, no API key required.
    NOAA_COOPS_BASE_URL: str = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
    NOAA_COOPS_REQUEST_TIMEOUT_SECONDS: float = 10.0

    # --- NOAA/NDBC (buoy) provider ---
    # Verified against https://www.ndbc.noaa.gov/faq/rt_data_access.shtml
    # and https://www.ndbc.noaa.gov/faq/measdes.shtml on 2026-09-09. Plain
    # whitespace-delimited text files, no API key.
    NOAA_NDBC_BASE_URL: str = "https://www.ndbc.noaa.gov/data/realtime2"
    NOAA_NDBC_REQUEST_TIMEOUT_SECONDS: float = 10.0

    # --- NOAA National Weather Service (api.weather.gov) provider ---
    # Verified against https://www.weather.gov/documentation/services-web-api
    # and https://weather-gov.github.io/api/general-faqs on 2026-09-09.
    # No API key, but NWS requires a real, identifying User-Agent —
    # override this via env with your own contact info before deploying.
    NOAA_WEATHER_BASE_URL: str = "https://api.weather.gov"
    NOAA_WEATHER_USER_AGENT: str = "OceanAgenticAI-SIH2026 (set-a-real-contact-email@example.com)"
    NOAA_WEATHER_REQUEST_TIMEOUT_SECONDS: float = 10.0

    # --- TidesAtlas provider ---
    # Verified against https://tidesatlas.com/en/api/docs on 2026-09-09.
    # Unlike IMD/Open-Meteo/NOAA, this one requires a real API key — the
    # free tier is 50 one-time credits, no card required. Get one at
    # https://tidesatlas.com/api/register. Per the project's source-priority
    # rule, TidesAtlas is an ADDITIONAL source and must never blindly
    # overwrite NOAA/IMD data — that merge logic belongs in Phase 9.
    TIDESATLAS_BASE_URL: str = "https://tidesatlas.com/api/v1"
    TIDESATLAS_API_KEY: str | None = None
    TIDESATLAS_REQUEST_TIMEOUT_SECONDS: float = 10.0


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (avoids re-parsing env on every call)."""
    return Settings()
