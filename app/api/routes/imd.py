"""
IMD routes.

These return IMD's provider-native response shape as-is (raw dict/list) —
normalization into the project's common marine data schema happens in the
service layer, which is Phase 9. If IMD is unreachable or returns an
error, the global ProviderError handler returns a 502/504 with no
fabricated data.
"""
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_imd_provider
from app.providers.imd_provider import IMDProvider

router = APIRouter(prefix="/api/imd", tags=["IMD"])


@router.get(
    "/weather",
    summary="Current weather from IMD",
    description="Wraps IMD's Current Weather API. Omit `station_id` for the default/all-station response.",
)
async def get_weather(
    station_id: str | None = Query(default=None, description="IMD station ID, e.g. '42182'"),
    provider: IMDProvider = Depends(get_imd_provider),
) -> Any:
    return await provider.get_current_weather(station_id=station_id)


@router.get(
    "/coastal-bulletin",
    summary="Coastal bulletin from IMD",
    description="Wraps IMD's Coastal Bulletin API (wind, weather, visibility, sea condition, port signal per coastal stretch).",
)
async def get_coastal_bulletin(provider: IMDProvider = Depends(get_imd_provider)) -> Any:
    return await provider.get_coastal_bulletin()


@router.get(
    "/sea-area-bulletin",
    summary="Sea area bulletin from IMD",
    description="Wraps IMD's Sea Area Bulletin API. Omit `area_id` for the default response.",
)
async def get_sea_area_bulletin(
    area_id: str | None = Query(default=None, description="IMD sea-area ID, e.g. '108'"),
    provider: IMDProvider = Depends(get_imd_provider),
) -> Any:
    return await provider.get_sea_area_bulletin(area_id=area_id)


@router.get(
    "/nowcast",
    summary="Nowcast from IMD (district- or station-wise)",
    description=(
        "Wraps IMD's District-wise and Station-wise Nowcast APIs. "
        "Set `by=district` (default) with a district object ID, or `by=station` with a station name."
    ),
)
async def get_nowcast(
    by: str = Query(default="district", pattern="^(district|station)$"),
    id: str | None = Query(default=None, description="District object ID or station name, depending on `by`"),
    provider: IMDProvider = Depends(get_imd_provider),
) -> Any:
    if by == "station":
        return await provider.get_station_nowcast(station_name=id)
    return await provider.get_district_nowcast(district_id=id)
