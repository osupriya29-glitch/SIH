"""
Open-Meteo Marine routes.

These expose the raw provider response for verification during
development — normalization into the project's common marine schema and
merging with other sources (NOAA/NDBC, TidesAtlas) happens in the service
layer, which is Phase 9. Not the final /api/ocean/* public surface from
the master spec — that's built once every wave/current/tide provider
exists and can be prioritized/merged.
"""
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_open_meteo_provider
from app.providers.open_meteo_provider import OpenMeteoMarineProvider

router = APIRouter(prefix="/api/open-meteo", tags=["Open-Meteo (raw provider)"])


def _csv_to_list(value: str | None) -> list[str] | None:
    if not value:
        return None
    return [v.strip() for v in value.split(",") if v.strip()]


@router.get(
    "/marine",
    summary="Marine forecast from Open-Meteo (raw)",
    description=(
        "Wraps Open-Meteo's Marine Weather API (/v1/marine). Pass comma-separated "
        "variable names for `hourly`, `daily`, and/or `current` — see Open-Meteo's "
        "docs for the full list (wave_height, swell_wave_height, sea_surface_temperature, etc)."
    ),
)
async def get_marine_forecast(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    hourly: str | None = Query(default=None, description="Comma-separated, e.g. 'wave_height,wave_period'"),
    daily: str | None = Query(default=None, description="Comma-separated, e.g. 'wave_height_max'"),
    current: str | None = Query(default=None, description="Comma-separated, e.g. 'wave_height,sea_surface_temperature'"),
    forecast_days: int | None = Query(default=None, ge=0, le=8),
    past_days: int | None = Query(default=None, ge=0, le=92),
    timezone: str | None = Query(default=None, description="e.g. 'auto' or 'Asia/Kolkata'"),
    provider: OpenMeteoMarineProvider = Depends(get_open_meteo_provider),
) -> Any:
    return await provider.get_marine_forecast(
        latitude=latitude,
        longitude=longitude,
        hourly=_csv_to_list(hourly),
        daily=_csv_to_list(daily),
        current=_csv_to_list(current),
        forecast_days=forecast_days,
        past_days=past_days,
        timezone=timezone,
    )
