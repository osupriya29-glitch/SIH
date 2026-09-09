"""
TidesAtlas routes.

Per the project's source-priority rule, this is an additional/supplementary
source for tides and waves — not a replacement for NOAA CO-OPS or IMD.
That merge logic lives in Phase 9's unified marine data service; these
routes just expose the raw provider for now.
"""
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_tidesatlas_provider
from app.providers.tidesatlas_provider import TidesAtlasProvider

router = APIRouter(prefix="/api/tidesatlas", tags=["TidesAtlas (raw provider)"])


@router.get(
    "/tides",
    summary="Tide predictions (TidesAtlas)",
    description="High/low tide times & heights. Provide `port` or both `lat` and `lon`.",
)
async def get_tides(
    port: str | None = Query(default=None),
    lat: float | None = Query(default=None, ge=-90, le=90),
    lon: float | None = Query(default=None, ge=-180, le=180),
    date: str | None = Query(default=None, description="YYYY-MM-DD"),
    days: int | None = Query(default=None, ge=1, le=14),
    provider: TidesAtlasProvider = Depends(get_tidesatlas_provider),
) -> Any:
    return await provider.get_tides(port=port, lat=lat, lon=lon, date=date, days=days)


@router.get(
    "/tides/point",
    summary="Tide predictions at exact coordinates (FES2022 model)",
    description="Always uses the FES2022 global model at the exact coordinates — never snaps to a station.",
)
async def get_tides_point(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    date: str | None = Query(default=None, description="YYYY-MM-DD"),
    days: int | None = Query(default=None, ge=1, le=14),
    datum: str | None = Query(default=None, description="'LAT' (default) or 'MSL'"),
    interval: int | None = Query(default=None, ge=5, le=60),
    heights: bool = Query(default=False, description="Include an interval-sampled height series"),
    provider: TidesAtlasProvider = Depends(get_tidesatlas_provider),
) -> Any:
    return await provider.get_tides_point(
        lat=lat, lon=lon, date=date, days=days, datum=datum, interval=interval, heights=heights
    )


@router.get(
    "/weather",
    summary="Weather forecast (TidesAtlas)",
    description="Provide `port` or both `lat` and `lon`.",
)
async def get_weather(
    port: str | None = Query(default=None),
    lat: float | None = Query(default=None, ge=-90, le=90),
    lon: float | None = Query(default=None, ge=-180, le=180),
    days: int | None = Query(default=None, ge=1, le=7),
    provider: TidesAtlasProvider = Depends(get_tidesatlas_provider),
) -> Any:
    return await provider.get_weather(port=port, lat=lat, lon=lon, days=days)


@router.get(
    "/marine",
    summary="Wave/marine forecast (TidesAtlas)",
    description="Wave height, swell, wind waves, sea state, sea surface temperature. Provide `port` or `lat`+`lon`.",
)
async def get_marine(
    port: str | None = Query(default=None),
    lat: float | None = Query(default=None, ge=-90, le=90),
    lon: float | None = Query(default=None, ge=-180, le=180),
    days: int | None = Query(default=None, ge=1, le=7),
    provider: TidesAtlasProvider = Depends(get_tidesatlas_provider),
) -> Any:
    return await provider.get_marine(port=port, lat=lat, lon=lon, days=days)


@router.get(
    "/ports",
    summary="Search TidesAtlas tide stations",
)
async def search_ports(
    search: str | None = Query(default=None),
    country: str | None = Query(default=None),
    limit: int | None = Query(default=None, ge=1, le=500),
    provider: TidesAtlasProvider = Depends(get_tidesatlas_provider),
) -> Any:
    return await provider.search_ports(search=search, country=country, limit=limit)
