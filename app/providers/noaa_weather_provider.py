"""
NOAA National Weather Service (api.weather.gov) provider.

Verified 2026-09-09 against:
  - https://www.weather.gov/documentation/services-web-api
  - https://weather-gov.github.io/api/general-faqs

No API key. NWS does require every request to carry an identifying
User-Agent header (their docs' own recommended format: app name + contact
email) — set NOAA_WEATHER_USER_AGENT to your own contact before deploying,
the shipped default is a placeholder, not a real contact.

US-only coverage (NWS is a US government agency) — points outside the US
will return an upstream error, which surfaces as a normal ProviderError.
"""
from app.core.config import get_settings
from app.providers.base_provider import BaseProvider

settings = get_settings()


class NOAAWeatherProvider(BaseProvider):
    provider_name = "NOAA Weather (NWS)"

    def __init__(self, client):
        super().__init__(client)
        self._base_url = settings.NOAA_WEATHER_BASE_URL
        self._headers = {"User-Agent": settings.NOAA_WEATHER_USER_AGENT}

    async def get_point_metadata(self, latitude: float, longitude: float) -> dict:
        """
        GET /points/{lat},{lon} — resolves a coordinate to its NWS forecast
        office/grid and the forecast/forecastHourly/observationStations URLs.
        """
        url = f"{self._base_url}/points/{latitude},{longitude}"
        return await self._get(url, headers=self._headers)

    async def get_forecast(self, latitude: float, longitude: float, hourly: bool = False) -> dict:
        """
        Resolves the point, then fetches the forecast (or hourly forecast)
        from the URL NWS returns for that grid — two real calls chained,
        exactly as NWS's own docs describe doing this.
        """
        point = await self.get_point_metadata(latitude, longitude)
        properties = point.get("properties", {})
        url = properties.get("forecastHourly" if hourly else "forecast")
        if not url:
            from app.providers.base_provider import ProviderError

            raise ProviderError(self.provider_name, "No forecast URL returned for this point")
        return await self._get(url, headers=self._headers)

    async def get_active_alerts(self, area: str | None = None, point: str | None = None) -> dict:
        """
        GET /alerts/active — optionally filtered by `area` (two-letter state/
        marine zone code, e.g. 'FL') or `point` ('lat,lon').
        """
        params = {}
        if area is not None:
            params["area"] = area
        if point is not None:
            params["point"] = point
        url = f"{self._base_url}/alerts/active"
        return await self._get(url, params=params or None, headers=self._headers)
