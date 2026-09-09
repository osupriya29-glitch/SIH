"""
Unified Marine Data Service schemas (Phase 9).

Normalized schemas representing aggregated marine, oceanographic, weather, wave,
tide, current, and satellite observations and forecasts with complete source
traceability and discrepancy tracking.
"""
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class LocationSchema(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")


class DiscrepancyItem(BaseModel):
    """Preserves conflicting values across providers for auditability and AI reasoning."""
    parameter: str = Field(..., description="Parameter name, e.g. 'wave_height', 'temperature'")
    primary: dict[str, Any] = Field(..., description="Selected primary provider value and unit")
    candidates: list[dict[str, Any]] = Field(..., description="All candidate values from different providers")
    delta: float | None = Field(default=None, description="Absolute difference between candidates when numeric")


class WeatherSection(BaseModel):
    temperature: float | None = Field(default=None, description="Air temperature")
    temperature_unit: str | None = Field(default=None, description="e.g. 'degC' or '°C'")
    wind_speed: float | None = Field(default=None, description="Wind speed")
    wind_speed_unit: str | None = Field(default=None, description="e.g. 'm/s' or 'km/h'")
    wind_direction: float | None = Field(default=None, description="Wind direction in degrees (0-360)")
    humidity: float | None = Field(default=None, description="Relative humidity in %")
    humidity_unit: str | None = Field(default=None, description="e.g. '%'")
    pressure: float | None = Field(default=None, description="Mean sea level pressure")
    pressure_unit: str | None = Field(default=None, description="e.g. 'hPa'")
    precipitation: float | None = Field(default=None, description="Precipitation / rainfall")
    precipitation_unit: str | None = Field(default=None, description="e.g. 'mm'")
    visibility: float | None = Field(default=None, description="Visibility distance")
    visibility_unit: str | None = Field(default=None, description="e.g. 'nmi' or 'km'")
    condition: str | None = Field(default=None, description="General weather summary / code")
    source: str | None = Field(default=None, description="Selected primary source provider name")
    data_type: str | None = Field(default=None, description="'observation' or 'forecast'")
    timestamp: str | None = Field(default=None, description="Observation or forecast timestamp")
    sources: dict[str, Any] = Field(default_factory=dict, description="Raw/extracted candidate values by provider")
    discrepancies: list[DiscrepancyItem] = Field(default_factory=list, description="Conflicting candidate provider values")


class OceanSection(BaseModel):
    sea_surface_temperature: float | None = Field(default=None, description="Sea surface temperature")
    sst_unit: str | None = Field(default=None, description="e.g. 'degC' or '°C'")
    sst_source: str | None = Field(default=None, description="Source provider for SST")
    sst_data_type: str | None = Field(default=None, description="'observation' or 'forecast'")
    chlorophyll: float | None = Field(default=None, description="Chlorophyll-a concentration (null if extraction pending)")
    chlorophyll_unit: str | None = Field(default=None, description="e.g. 'mg/m^3'")
    chlorophyll_source: str | None = Field(default=None, description="Source provider for chlorophyll")
    salinity: float | None = Field(default=None, description="Salinity if available")
    salinity_unit: str | None = Field(default=None, description="e.g. 'PSU'")
    salinity_source: str | None = Field(default=None, description="Source provider for salinity")
    sources: dict[str, Any] = Field(default_factory=dict, description="Candidate ocean readings by provider")
    discrepancies: list[DiscrepancyItem] = Field(default_factory=list, description="Conflicting candidate provider values")


class WavesSection(BaseModel):
    height: float | None = Field(default=None, description="Significant wave height")
    height_unit: str | None = Field(default=None, description="e.g. 'm'")
    direction: float | None = Field(default=None, description="Dominant wave direction in degrees")
    period: float | None = Field(default=None, description="Wave period in seconds")
    period_unit: str | None = Field(default=None, description="e.g. 's'")
    swell_height: float | None = Field(default=None, description="Swell wave height")
    swell_height_unit: str | None = Field(default=None, description="e.g. 'm'")
    swell_direction: float | None = Field(default=None, description="Swell wave direction in degrees")
    swell_period: float | None = Field(default=None, description="Swell wave period in seconds")
    source: str | None = Field(default=None, description="Selected primary source provider name")
    data_type: str | None = Field(default=None, description="'observation' or 'forecast'")
    timestamp: str | None = Field(default=None, description="Observation or forecast timestamp")
    sources: dict[str, Any] = Field(default_factory=dict, description="Candidate wave readings by provider")
    discrepancies: list[DiscrepancyItem] = Field(default_factory=list, description="Conflicting candidate provider values")


class CurrentsSection(BaseModel):
    velocity: float | None = Field(default=None, description="Ocean current velocity / speed")
    velocity_unit: str | None = Field(default=None, description="e.g. 'm/s' or 'knots'")
    direction: float | None = Field(default=None, description="Ocean current direction in degrees")
    source: str | None = Field(default=None, description="Selected primary source provider name")
    data_type: str | None = Field(default=None, description="'observation' or 'forecast'")
    timestamp: str | None = Field(default=None, description="Observation or forecast timestamp")
    sources: dict[str, Any] = Field(default_factory=dict, description="Candidate current readings by provider")


class TidesSection(BaseModel):
    water_level: float | None = Field(default=None, description="Observed or predicted water level")
    water_level_unit: str | None = Field(default=None, description="e.g. 'm' or 'ft'")
    prediction: str | None = Field(default=None, description="Tide prediction state, e.g. 'high', 'low'")
    datum: str | None = Field(default=None, description="Vertical datum, e.g. 'MLLW', 'LAT', 'MSL'")
    extremes: list[dict[str, Any]] = Field(default_factory=list, description="Upcoming high and low tide extremes")
    source: str | None = Field(default=None, description="Selected primary source provider name")
    data_type: str | None = Field(default=None, description="'prediction' or 'observation'")
    timestamp: str | None = Field(default=None, description="Timestamp for tide data")
    sources: dict[str, Any] = Field(default_factory=dict, description="Candidate tide readings by provider")
    discrepancies: list[DiscrepancyItem] = Field(default_factory=list, description="Conflicting candidate provider values")


class ObservationItem(BaseModel):
    """Discrete single sensor or station observation."""
    parameter: str = Field(..., description="Observed metric, e.g. 'WVHT', 'ATMP', 'WTMP'")
    value: float | str | None = Field(..., description="Observed value (null if missing from sensor)")
    unit: str | None = Field(default=None, description="Measurement unit")
    source: str = Field(..., description="Source provider or station, e.g. 'NOAA/NDBC'")
    timestamp: str | None = Field(default=None, description="Measurement time")
    station_id: str | None = Field(default=None, description="Station or buoy identifier")
    latitude: float | None = Field(default=None)
    longitude: float | None = Field(default=None)


class BulletinItem(BaseModel):
    """Coastal bulletin, sea area warning, nowcast or marine weather alert."""
    title: str = Field(..., description="Bulletin or alert headline/title")
    text: str = Field(..., description="Full bulletin/alert message body")
    type: str = Field(..., description="'coastal_bulletin', 'sea_area_bulletin', 'nowcast', or 'weather_alert'")
    source: str = Field(..., description="Originating agency, e.g. 'IMD' or 'NOAA Weather (NWS)'")
    area: str | None = Field(default=None, description="Applicable geographic stretch or sea zone")
    severity: str | None = Field(default=None, description="Severity rating if present")
    timestamp: str | None = Field(default=None, description="Issuance or validity time")


class ProviderStatusItem(BaseModel):
    """Operational status of an individual provider query."""
    status: str = Field(
        ...,
        description="'success' | 'partial' | 'failed' | 'not_configured' | 'not_implemented' | 'skipped'",
    )
    latency_ms: float | None = Field(default=None, description="Provider query latency in milliseconds")
    message: str | None = Field(default=None, description="Status detail or reason if failed/skipped")


class ProviderErrorItem(BaseModel):
    """Structured error payload for failed or timed-out providers."""
    provider: str = Field(..., description="Provider name")
    error_code: str = Field(..., description="Error classification code")
    message: str = Field(..., description="Human-readable error description")
    is_timeout: bool = Field(default=False, description="True if failure was due to network timeout")


class UnifiedMarineDataResponse(BaseModel):
    """Top-level normalized marine data response for GET /api/marine/data."""
    model_config = ConfigDict(extra="ignore")

    location: LocationSchema = Field(..., description="Target geographic coordinate")
    timestamp: str = Field(..., description="Aggregation response UTC timestamp (ISO 8601)")
    weather: WeatherSection = Field(..., description="Normalized weather section")
    ocean: OceanSection = Field(..., description="Normalized oceanographic conditions (SST, chlorophyll, salinity)")
    waves: WavesSection = Field(..., description="Normalized sea wave and swell conditions")
    currents: CurrentsSection = Field(..., description="Normalized ocean currents")
    tides: TidesSection = Field(..., description="Normalized tide heights and predictions")
    observations: list[ObservationItem] = Field(default_factory=list, description="Station or buoy sensor observations")
    bulletins: list[BulletinItem] = Field(default_factory=list, description="Official coastal and sea area bulletins/alerts")
    sources: list[str] = Field(default_factory=list, description="List of providers that contributed valid data")
    provider_status: dict[str, ProviderStatusItem] = Field(
        default_factory=dict,
        description="Execution status per provider (success, failed, not_configured, etc.)",
    )
    errors: list[ProviderErrorItem] = Field(
        default_factory=list,
        description="Detailed errors from providers that failed or timed out",
    )
