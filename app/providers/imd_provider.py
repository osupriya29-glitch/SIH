"""
IMD (India Meteorological Department) provider.

Every endpoint/param/field below is taken from IMD's official, published
API reference: https://api.imd.gov.in/public/api_reference.html
(verified 2026-09-09). Only endpoints relevant to this project's scope
(current weather, coastal bulletin, sea area bulletin, nowcast) are wired
up here — IMD publishes ~28 APIs total; the rest are out of scope for now.

Do not add endpoints here without checking the reference doc first — see
project rule in the master spec (Section 3, "CRITICAL API RULE").
"""
from app.core.config import get_settings
from app.providers.base_provider import BaseProvider

settings = get_settings()


class IMDProvider(BaseProvider):
    provider_name = "IMD"

    def __init__(self, client):
        super().__init__(client)
        self._base_url = settings.IMD_API_BASE_URL.rstrip("/")

    async def get_current_weather(self, station_id: str | None = None) -> dict | list:
        """
        Current Weather API.
        GET /current_wx or /current_wx?id=<station_id>
        Fields (per IMD docs): Station Id, Station, Date/Time of Observation,
        M.S.L.P (hPa), Wind Direction (code), Wind Speed (KMPH),
        Temperature (deg C), Weather Code, Nebulosity (0-8), Humidity (%),
        Last 24 hrs Rainfall (mm).
        """
        params = {"id": station_id} if station_id else None
        return await self._get(f"{self._base_url}/current_wx", params=params)

    async def get_coastal_bulletin(self) -> dict | list:
        """
        Coastal Bulletin API.
        GET /coastalbulletin
        Returns a list of coastal-stretch bulletins (wind, weather,
        visibility, sea condition, port signal, etc). No `id` param is
        documented for this endpoint.
        """
        return await self._get(f"{self._base_url}/coastalbulletin")

    async def get_sea_area_bulletin(self, area_id: str | None = None) -> dict | list:
        """
        Sea Area Bulletin API.
        GET /seabulletin or /seabulletin?id=<area_id>
        Returns wind/weather/visibility/sea-condition bulletins per sea
        area (e.g. "South West Bay").
        """
        params = {"id": area_id} if area_id else None
        return await self._get(f"{self._base_url}/seabulletin", params=params)

    async def get_district_nowcast(self, district_id: str | None = None) -> dict | list:
        """
        District-wise Nowcast API.
        GET /districtnowcast or /districtnowcast?id=<district_object_id>
        Returns short-range hazard categories (Cat1-Cat19) with a
        consolidated warning message and validity window.
        """
        params = {"id": district_id} if district_id else None
        return await self._get(f"{self._base_url}/districtnowcast", params=params)

    async def get_station_nowcast(self, station_name: str | None = None) -> dict | list:
        """
        Station-wise Nowcast API.
        GET /stationnowcast or /stationnowcast?id=<station_name>
        Same category scheme as district nowcast, but per station.
        """
        params = {"id": station_name} if station_name else None
        return await self._get(f"{self._base_url}/stationnowcast", params=params)
