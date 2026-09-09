"""
NOAA routes: CO-OPS (tides/currents/water levels), NDBC (buoys), and NWS
(api.weather.gov forecasts/alerts). All three are separate providers with
different transports (JSON GET, plain-text GET, JSON GET+User-Agent) —
see their respective provider modules for what's verified where.
"""
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_noaa_coops_provider, get_noaa_ndbc_provider, get_noaa_weather_provider
from app.providers.noaa_coops_provider import NOAACoOpsProvider
from app.providers.noaa_ndbc_provider import NOAANDBCProvider
from app.providers.noaa_weather_provider import NOAAWeatherProvider

router = APIRouter(prefix="/api/noaa", tags=["NOAA (raw provider)"])


@router.get(
    "/coops",
    summary="NOAA CO-OPS tide/current/water-level/met data",
    description=(
        "Wraps CO-OPS's datagetter endpoint. `datum` is required for all water-level "
        "products except air_gap. Provide one of: (begin_date & end_date), "
        "(begin_date & range), (end_date & range), date, or range."
    ),
)
async def get_coops_data(
    station: str = Query(..., description="7-char station ID, e.g. '9414290', or currents ID like 'cb1401'"),
    product: str = Query(..., description="e.g. 'water_level', 'predictions', 'currents', 'wind'"),
    begin_date: str | None = Query(default=None, description="yyyyMMdd or yyyyMMdd HH:mm"),
    end_date: str | None = Query(default=None),
    date: str | None = Query(default=None, description="'today', 'latest', or 'recent'"),
    range: int | None = Query(default=None, description="Hours back from now, or paired with begin/end_date"),  # noqa: A002
    datum: str | None = Query(default=None, description="e.g. 'MLLW' — required for most water-level products"),
    units: str = Query(default="metric"),
    time_zone: str = Query(default="gmt"),
    interval: str | None = Query(default=None, description="'h', 'hilo', or a minute value"),
    bin: int | None = Query(default=None, description="Required for most currents stations"),  # noqa: A002
    provider: NOAACoOpsProvider = Depends(get_noaa_coops_provider),
) -> Any:
    return await provider.get_data(
        station=station,
        product=product,
        begin_date=begin_date,
        end_date=end_date,
        date=date,
        range=range,
        datum=datum,
        units=units,
        time_zone=time_zone,
        interval=interval,
        bin=bin,
        application="OceanAgenticAI-SIH2026",
    )


@router.get(
    "/ndbc/{station}",
    summary="NOAA/NDBC buoy standard meteorological observations",
    description="Parses the station's realtime2 .txt file (last ~45 days). 'MM' (missing) becomes null.",
)
async def get_ndbc_observations(
    station: str,
    provider: NOAANDBCProvider = Depends(get_noaa_ndbc_provider),
) -> Any:
    return await provider.get_standard_meteorological(station)


@router.get(
    "/weather/forecast",
    summary="NWS forecast for a US coordinate",
    description="Resolves the point via /points then fetches its forecast. US coverage only.",
)
async def get_nws_forecast(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    hourly: bool = Query(default=False),
    provider: NOAAWeatherProvider = Depends(get_noaa_weather_provider),
) -> Any:
    return await provider.get_forecast(latitude=latitude, longitude=longitude, hourly=hourly)


@router.get(
    "/weather/alerts",
    summary="Active NWS alerts",
    description="Filter by `area` (two-letter state/marine zone code) or `point` ('lat,lon'). US coverage only.",
)
async def get_nws_alerts(
    area: str | None = Query(default=None),
    point: str | None = Query(default=None),
    provider: NOAAWeatherProvider = Depends(get_noaa_weather_provider),
) -> Any:
    return await provider.get_active_alerts(area=area, point=point)
