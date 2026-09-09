"""
Open-Meteo Marine Weather API provider.

Endpoint, parameters, variable names and units below are taken from
Open-Meteo's official docs, verified 2026-09-09:
  - https://open-meteo.com/en/docs/marine-weather-api
  - https://open-meteo.com/en/terms (free-tier rate limits, licensing)

Free tier: no API key required for non-commercial use; rate-limited to
<10,000 calls/day, 5,000/hour, 600/minute per Open-Meteo's terms. Data is
CC BY 4.0 — attribution to Open-Meteo (and DWD, whose ICON Wave forecast
underlies the marine model) is required per their citation notice.

Do not add variable names here without checking the docs above first.
"""
from app.core.config import get_settings
from app.providers.base_provider import BaseProvider

settings = get_settings()

# Exact variable tokens accepted by &hourly= / &current= (Open-Meteo docs,
# "Hourly Parameter Definition" / "Current Conditions" sections).
ALLOWED_HOURLY_VARIABLES = {
    "wave_height",
    "wave_direction",
    "wave_period",
    "wind_wave_height",
    "wind_wave_direction",
    "wind_wave_period",
    "wind_wave_peak_period",
    "swell_wave_height",
    "swell_wave_direction",
    "swell_wave_period",
    "swell_wave_peak_period",
    "secondary_swell_wave_height",
    "secondary_swell_wave_direction",
    "secondary_swell_wave_period",
    "tertiary_swell_wave_height",
    "tertiary_swell_wave_direction",
    "tertiary_swell_wave_period",
    "sea_level_height_msl",
    "sea_surface_temperature",
    "ocean_current_velocity",
    "ocean_current_direction",
    "invert_barometer_height",
}

# "current" accepts the same variable set as "hourly" per the docs.
ALLOWED_CURRENT_VARIABLES = ALLOWED_HOURLY_VARIABLES

# Exact tokens accepted by &daily= (Open-Meteo docs, "Daily Parameter Definition").
ALLOWED_DAILY_VARIABLES = {
    "wave_height_max",
    "wind_wave_height_max",
    "swell_wave_height_max",
    "wave_direction_dominant",
    "wind_wave_direction_dominant",
    "swell_wave_direction_dominant",
    "wave_period_max",
    "wind_wave_period_max",
    "swell_wave_period_max",
    "wind_wave_peak_period_max",
    "swell_wave_peak_period_max",
}


class InvalidMarineVariable(ValueError):
    """Raised when a caller asks for a variable name Open-Meteo doesn't document."""


def _validate(variables: list[str], allowed: set[str], param_name: str) -> None:
    unknown = [v for v in variables if v not in allowed]
    if unknown:
        raise InvalidMarineVariable(
            f"Unknown {param_name} variable(s) for Open-Meteo Marine API: {unknown}"
        )


class OpenMeteoMarineProvider(BaseProvider):
    provider_name = "Open-Meteo Marine"

    def __init__(self, client):
        super().__init__(client)
        self._base_url = settings.OPEN_METEO_MARINE_BASE_URL

    async def get_marine_forecast(
        self,
        latitude: float,
        longitude: float,
        hourly: list[str] | None = None,
        daily: list[str] | None = None,
        current: list[str] | None = None,
        forecast_days: int | None = None,
        past_days: int | None = None,
        timezone: str | None = None,
        cell_selection: str | None = None,
        length_unit: str | None = None,
    ) -> dict:
        """
        GET /v1/marine — hourly/daily/current wave, swell, current and SST
        forecast for a coordinate. Raises InvalidMarineVariable for any
        variable name not in Open-Meteo's documented set — never silently
        drops or guesses at an unsupported parameter.
        """
        if hourly:
            _validate(hourly, ALLOWED_HOURLY_VARIABLES, "hourly")
        if daily:
            _validate(daily, ALLOWED_DAILY_VARIABLES, "daily")
        if current:
            _validate(current, ALLOWED_CURRENT_VARIABLES, "current")

        params: dict = {"latitude": latitude, "longitude": longitude}
        if hourly:
            params["hourly"] = ",".join(hourly)
        if daily:
            params["daily"] = ",".join(daily)
            # Open-Meteo requires timezone whenever daily variables are requested.
            params.setdefault("timezone", timezone or "auto")
        if current:
            params["current"] = ",".join(current)
        if forecast_days is not None:
            params["forecast_days"] = forecast_days
        if past_days is not None:
            params["past_days"] = past_days
        if timezone is not None:
            params["timezone"] = timezone
        if cell_selection is not None:
            params["cell_selection"] = cell_selection
        if length_unit is not None:
            params["length_unit"] = length_unit
        if settings.OPEN_METEO_API_KEY:
            params["apikey"] = settings.OPEN_METEO_API_KEY

        return await self._get(self._base_url, params=params)
