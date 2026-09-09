"""
Unified Marine Data routes (Phase 9).

Exposes GET /api/marine/data to aggregate, normalize, and return marine, weather,
oceanographic, wave, current, and tide data from multiple providers.
"""
from fastapi import APIRouter, Depends, Query

from app.api.deps import get_marine_service
from app.schemas.marine import UnifiedMarineDataResponse
from app.services.marine_service import MarineDataService

router = APIRouter(prefix="/api/marine", tags=["Marine Data (Unified)"])


def _csv_to_list(value: str | None) -> list[str] | None:
    if not value:
        return None
    return [v.strip() for v in value.split(",") if v.strip()]


@router.get(
    "/data",
    response_model=UnifiedMarineDataResponse,
    summary="Unified Marine Data Aggregation",
    description=(
        "Aggregates, normalizes, and resolves marine, weather, wave, tide, current, "
        "and oceanographic data from Open-Meteo, IMD, NOAA (NWS, NDBC, CO-OPS), "
        "TidesAtlas, and NASA Ocean Color. Enforces source priority (Weather: IMD > NOAA; "
        "Waves: Open-Meteo > TidesAtlas > NOAA; Tides: NOAA CO-OPS > TidesAtlas; "
        "Chlorophyll/SST: NASA Ocean Color > Open-Meteo > NOAA), detects discrepancies "
        "between conflicting sources, and isolates partial provider failures gracefully."
    ),
)
async def get_unified_marine_data(
    latitude: float = Query(
        ...,
        ge=-90,
        le=90,
        description="Target latitude in decimal degrees (-90 to 90)",
        examples=[19.07],
    ),
    longitude: float = Query(
        ...,
        ge=-180,
        le=180,
        description="Target longitude in decimal degrees (-180 to 180)",
        examples=[72.87],
    ),
    time: str | None = Query(
        default=None,
        description="Optional target ISO timestamp or YYYY-MM-DD date string",
        examples=["2026-09-09T00:00:00Z"],
    ),
    providers: str | None = Query(
        default=None,
        description="Optional comma-separated list of providers to query (e.g. 'open_meteo,imd,noaa,tidesatlas')",
        examples=["open_meteo,imd"],
    ),
    imd_station_id: str | None = Query(
        default=None,
        description="Optional IMD station ID (e.g. '42182')",
        examples=["42182"],
    ),
    noaa_station_id: str | None = Query(
        default=None,
        description="Optional NOAA CO-OPS station ID (e.g. '9414290')",
        examples=["9414290"],
    ),
    noaa_ndbc_station_id: str | None = Query(
        default=None,
        description="Optional NOAA NDBC buoy station ID (e.g. '46042')",
        examples=["46042"],
    ),
    tidesatlas_port: str | None = Query(
        default=None,
        description="Optional TidesAtlas port name or slug",
        examples=["mumbai"],
    ),
    service: MarineDataService = Depends(get_marine_service),
) -> UnifiedMarineDataResponse:
    provider_list = _csv_to_list(providers)
    return await service.get_unified_marine_data(
        latitude=latitude,
        longitude=longitude,
        target_time=time,
        provider_filter=provider_list,
        imd_station_id=imd_station_id,
        noaa_station_id=noaa_station_id,
        noaa_ndbc_station_id=noaa_ndbc_station_id,
        tidesatlas_port=tidesatlas_port,
    )
