"""
TidesAtlas provider.

Endpoints, parameters and response shapes verified against TidesAtlas's
official docs on 2026-09-09: https://tidesatlas.com/en/api/docs

Unlike the other providers so far, this one requires a real API key
(X-API-Key header) — free tier is 50 one-time credits. If no key is
configured, methods raise ProviderNotConfigured rather than sending a
request that would just 401.

Per the project's source-priority rule (master spec Section 8):
TidesAtlas is an ADDITIONAL source for waves/tides and must never blindly
overwrite NOAA/IMD data — that merge/priority logic belongs in Phase 9's
unified marine data service, not here.
"""
from app.core.config import get_settings
from app.providers.base_provider import BaseProvider, ProviderNotConfigured

settings = get_settings()

VALID_FORMATS = {"json", "csv", "geojson"}
VALID_DATUMS = {"LAT", "MSL"}


class InvalidTidesAtlasQuery(ValueError):
    """Raised when a TidesAtlas query is missing required fields."""


def _require_location(port: str | None, lat: float | None, lon: float | None) -> None:
    if port is None and (lat is None or lon is None):
        raise InvalidTidesAtlasQuery("Provide either `port` or both `lat` and `lon`.")


class TidesAtlasProvider(BaseProvider):
    provider_name = "TidesAtlas"

    def __init__(self, client):
        super().__init__(client)
        self._base_url = settings.TIDESATLAS_BASE_URL

    def _headers(self) -> dict:
        api_key = get_settings().TIDESATLAS_API_KEY
        if not api_key:
            raise ProviderNotConfigured(
                self.provider_name,
                "TIDESATLAS_API_KEY is not set. Get a free key at "
                "https://tidesatlas.com/api/register and set it in .env.",
            )
        return {"X-API-Key": api_key}

    async def get_tides(
        self,
        port: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
        date: str | None = None,
        days: int | None = None,
        format: str | None = None,  # noqa: A002 - matches TidesAtlas param name
    ) -> dict | str:
        """
        GET /tides — high/low tide times & heights. Smart routing: uses a
        calibrated station within 50km if one exists, else the FES2022
        global model at the exact coordinates given.
        """
        _require_location(port, lat, lon)
        if format is not None and format not in VALID_FORMATS:
            raise InvalidTidesAtlasQuery(f"format must be one of {sorted(VALID_FORMATS)}")

        params = self._location_params(port, lat, lon)
        if date is not None:
            params["date"] = date
        if days is not None:
            params["days"] = days
        if format is not None:
            params["format"] = format

        return await self._get(f"{self._base_url}/tides", params=params, headers=self._headers())

    async def get_tides_point(
        self,
        lat: float,
        lon: float,
        date: str | None = None,
        days: int | None = None,
        datum: str | None = None,
        interval: int | None = None,
        heights: bool = False,
    ) -> dict:
        """
        GET /tides/point — always uses the FES2022 model at the exact
        coordinates given (never snaps to a station). 404s if the point is
        on land or outside the ocean mask — surfaced as a normal ProviderError.
        """
        if datum is not None and datum not in VALID_DATUMS:
            raise InvalidTidesAtlasQuery(f"datum must be one of {sorted(VALID_DATUMS)}")
        if interval is not None and not (5 <= interval <= 60):
            raise InvalidTidesAtlasQuery("interval must be between 5 and 60 minutes")

        params: dict = {"lat": lat, "lon": lon}
        if date is not None:
            params["date"] = date
        if days is not None:
            params["days"] = days
        if datum is not None:
            params["datum"] = datum
        if interval is not None:
            params["interval"] = interval
        if heights:
            params["heights"] = 1

        return await self._get(f"{self._base_url}/tides/point", params=params, headers=self._headers())

    async def get_weather(
        self,
        port: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
        days: int | None = None,
    ) -> dict:
        """GET /weather — hourly/daily forecast (temperature, wind, precipitation, UV, condition)."""
        _require_location(port, lat, lon)
        params = self._location_params(port, lat, lon)
        if days is not None:
            params["days"] = days
        return await self._get(f"{self._base_url}/weather", params=params, headers=self._headers())

    async def get_marine(
        self,
        port: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
        days: int | None = None,
    ) -> dict:
        """GET /marine — wave height, swell, wind waves, sea state, sea surface temperature."""
        _require_location(port, lat, lon)
        params = self._location_params(port, lat, lon)
        if days is not None:
            params["days"] = days
        return await self._get(f"{self._base_url}/marine", params=params, headers=self._headers())

    async def search_ports(
        self,
        search: str | None = None,
        country: str | None = None,
        limit: int | None = None,
        format: str | None = None,  # noqa: A002 - matches TidesAtlas param name
    ) -> dict | str:
        """GET /ports — search/list tide stations."""
        if format is not None and format not in VALID_FORMATS:
            raise InvalidTidesAtlasQuery(f"format must be one of {sorted(VALID_FORMATS)}")
        if limit is not None and not (1 <= limit <= 500):
            raise InvalidTidesAtlasQuery("limit must be between 1 and 500")

        params: dict = {}
        if search is not None:
            params["search"] = search
        if country is not None:
            params["country"] = country
        if limit is not None:
            params["limit"] = limit
        if format is not None:
            params["format"] = format

        return await self._get(f"{self._base_url}/ports", params=params, headers=self._headers())

    @staticmethod
    def _location_params(port: str | None, lat: float | None, lon: float | None) -> dict:
        if port is not None:
            return {"port": port}
        return {"lat": lat, "lon": lon}
