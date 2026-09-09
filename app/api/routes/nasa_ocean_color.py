"""
NASA Ocean Color routes.

/files is real — it searches OB.DAAC for matching data files.
/chlorophyll (and any other point-value endpoint) is intentionally NOT
implemented; see app/providers/nasa_ocean_color_provider.py for why. It
returns 501 rather than fabricated data.
"""
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_nasa_ocean_color_provider
from app.providers.nasa_ocean_color_provider import NASAOceanColorProvider

router = APIRouter(prefix="/api/nasa-ocean-color", tags=["NASA Ocean Color (raw provider)"])


@router.get(
    "/files",
    summary="Search NASA Ocean Color (OB.DAAC) data files",
    description=(
        "Wraps OB.DAAC's file_search API. Returns a list of matching FILES "
        "(e.g. an L3 mapped chlorophyll granule for a date) — not a value at a "
        "coordinate. Provide either (sdate & edate) or backdays. See "
        "https://oceandata.sci.gsfc.nasa.gov/file_search/file_search_help for field details."
    ),
)
async def search_files(
    sensor_id: int | None = Query(default=None, description="e.g. 7 for Aqua-MODIS"),
    sensor: str | None = Query(default=None, description="Alternative to sensor_id, e.g. 'aqua-modis'"),
    dtype: str | None = Query(default=None, description="L0, L1, L2, L3b, L3m, MET, or misc"),
    dtid: int | None = Query(default=None, description="Data type ID — see OB.DAAC's dtid list"),
    sdate: str | None = Query(default=None, description="'YYYY-MM-DD 00:00:00'"),
    edate: str | None = Query(default=None, description="'YYYY-MM-DD 23:59:59'"),
    backdays: int | None = Query(default=None, description="Alternative to sdate/edate"),
    suite_id: str | None = Query(default=None, description="e.g. 'CHL'"),
    prod_id: str | None = Query(default=None, description="e.g. 'chlor_a'"),
    resolution_id: str | None = Query(default=None, description="e.g. '4km'"),
    period: str | None = Query(default=None, description="e.g. 'DAY', 'MO'"),
    provider: NASAOceanColorProvider = Depends(get_nasa_ocean_color_provider),
) -> Any:
    return await provider.search_files(
        sensor_id=sensor_id,
        sensor=sensor,
        dtype=dtype,
        dtid=dtid,
        sdate=sdate,
        edate=edate,
        backdays=backdays,
        suite_id=suite_id,
        prod_id=prod_id,
        resolution_id=resolution_id,
        period=period,
    )


@router.get(
    "/chlorophyll",
    summary="[Not implemented] Chlorophyll-a at a coordinate",
    description=(
        "Not implemented yet — always returns 501. Extracting a point value from "
        "NASA Ocean Color requires downloading the matched NetCDF granule and reading "
        "the nearest pixel, which isn't built. Use /files to find candidate granules."
    ),
)
async def get_chlorophyll_point(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    date: str = Query(..., description="'YYYY-MM-DD'"),
    provider: NASAOceanColorProvider = Depends(get_nasa_ocean_color_provider),
) -> Any:
    return await provider.get_point_value(
        latitude=latitude, longitude=longitude, product="chlor_a", date=date
    )
