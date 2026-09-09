"""
Unified Marine Data Service (Phase 9).

Aggregates data across external providers:
- Open-Meteo Marine
- IMD (India Meteorological Department)
- NOAA CO-OPS
- NOAA/NDBC
- NOAA Weather (NWS)
- TidesAtlas
- NASA Ocean Color

Applies source priorities, conflict/discrepancy detection, independent timeout
and partial failure resilience, and returns a fully normalized marine data payload.
"""
import asyncio
import datetime as dt
import time
from typing import Any

from app.core.logging import get_logger
from app.providers.base_provider import ProviderError, ProviderNotConfigured
from app.providers.imd_provider import IMDProvider
from app.providers.nasa_ocean_color_provider import (
    NASAOceanColorProvider,
    OceanColorExtractionPending,
)
from app.providers.noaa_coops_provider import NOAACoOpsProvider
from app.providers.noaa_ndbc_provider import NOAANDBCProvider
from app.providers.noaa_weather_provider import NOAAWeatherProvider
from app.providers.open_meteo_provider import OpenMeteoMarineProvider
from app.providers.tidesatlas_provider import TidesAtlasProvider
from app.schemas.marine import (
    BulletinItem,
    CurrentsSection,
    DiscrepancyItem,
    LocationSchema,
    ObservationItem,
    OceanSection,
    ProviderErrorItem,
    ProviderStatusItem,
    TidesSection,
    UnifiedMarineDataResponse,
    WavesSection,
    WeatherSection,
)

logger = get_logger(__name__)


def _try_float(val: Any) -> float | None:
    if val is None or val == "" or val == "MM":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


class MarineDataService:
    """Coordinates multi-provider marine data acquisition and normalization."""

    def __init__(
        self,
        open_meteo: OpenMeteoMarineProvider,
        imd: IMDProvider,
        nasa_ocean_color: NASAOceanColorProvider,
        noaa_coops: NOAACoOpsProvider,
        noaa_ndbc: NOAANDBCProvider,
        noaa_weather: NOAAWeatherProvider,
        tidesatlas: TidesAtlasProvider,
    ):
        self._open_meteo = open_meteo
        self._imd = imd
        self._nasa_ocean_color = nasa_ocean_color
        self._noaa_coops = noaa_coops
        self._noaa_ndbc = noaa_ndbc
        self._noaa_weather = noaa_weather
        self._tidesatlas = tidesatlas

    async def get_unified_marine_data(
        self,
        latitude: float,
        longitude: float,
        target_time: str | None = None,
        provider_filter: list[str] | None = None,
        imd_station_id: str | None = None,
        noaa_station_id: str | None = None,
        noaa_ndbc_station_id: str | None = None,
        tidesatlas_port: str | None = None,
    ) -> UnifiedMarineDataResponse:
        now_utc = dt.datetime.now(dt.timezone.utc).isoformat()
        filter_set = {p.lower().strip() for p in provider_filter} if provider_filter else None

        # Helper to check if provider is active
        def is_enabled(key: str) -> bool:
            if not filter_set:
                return True
            # Support grouped tokens e.g. "noaa" covers all noaa services
            return key in filter_set or ("noaa" in filter_set and key.startswith("noaa_"))

        provider_status: dict[str, ProviderStatusItem] = {}
        errors: list[ProviderErrorItem] = []
        sources: list[str] = []

        # Containers for candidate data across providers
        weather_candidates: list[dict[str, Any]] = []
        ocean_candidates: list[dict[str, Any]] = []
        wave_candidates: list[dict[str, Any]] = []
        current_candidates: list[dict[str, Any]] = []
        tide_candidates: list[dict[str, Any]] = []
        observations: list[ObservationItem] = []
        bulletins: list[BulletinItem] = []

        # --- Concurrency Runner Tasks ---

        async def run_open_meteo():
            if not is_enabled("open_meteo"):
                provider_status["open_meteo"] = ProviderStatusItem(status="skipped", message="Filtered out by user")
                return
            t0 = time.perf_counter()
            try:
                res = await self._open_meteo.get_marine_forecast(
                    latitude=latitude,
                    longitude=longitude,
                    current=[
                        "wave_height",
                        "wave_direction",
                        "wave_period",
                        "sea_surface_temperature",
                        "ocean_current_velocity",
                        "ocean_current_direction",
                        "sea_level_height_msl",
                    ],
                )
                latency = round((time.perf_counter() - t0) * 1000, 2)
                provider_status["open_meteo"] = ProviderStatusItem(status="success", latency_ms=latency)
                sources.append("Open-Meteo Marine")

                curr = res.get("current", {})
                curr_units = res.get("current_units", {})
                obs_time = curr.get("time")

                # Wave candidate
                if curr.get("wave_height") is not None:
                    wave_candidates.append({
                        "source": "Open-Meteo Marine",
                        "priority": 1,  # Highest for waves
                        "height": _try_float(curr.get("wave_height")),
                        "height_unit": curr_units.get("wave_height", "m"),
                        "direction": _try_float(curr.get("wave_direction")),
                        "period": _try_float(curr.get("wave_period")),
                        "period_unit": curr_units.get("wave_period", "s"),
                        "swell_height": None,
                        "data_type": "forecast",
                        "timestamp": obs_time,
                    })

                # Ocean candidate (SST)
                if curr.get("sea_surface_temperature") is not None:
                    ocean_candidates.append({
                        "source": "Open-Meteo Marine",
                        "priority": 2,  # After NASA Ocean Color
                        "sst": _try_float(curr.get("sea_surface_temperature")),
                        "sst_unit": curr_units.get("sea_surface_temperature", "°C"),
                        "chlorophyll": None,
                        "salinity": None,
                        "data_type": "forecast",
                        "timestamp": obs_time,
                    })

                # Currents candidate
                if curr.get("ocean_current_velocity") is not None:
                    current_candidates.append({
                        "source": "Open-Meteo Marine",
                        "priority": 1,
                        "velocity": _try_float(curr.get("ocean_current_velocity")),
                        "velocity_unit": curr_units.get("ocean_current_velocity", "m/s"),
                        "direction": _try_float(curr.get("ocean_current_direction")),
                        "data_type": "forecast",
                        "timestamp": obs_time,
                    })

                # Tide candidate (Sea level height MSL)
                if curr.get("sea_level_height_msl") is not None:
                    tide_candidates.append({
                        "source": "Open-Meteo Marine",
                        "priority": 3,
                        "water_level": _try_float(curr.get("sea_level_height_msl")),
                        "water_level_unit": curr_units.get("sea_level_height_msl", "m"),
                        "datum": "MSL",
                        "prediction": None,
                        "extremes": [],
                        "data_type": "forecast",
                        "timestamp": obs_time,
                    })

            except ProviderError as exc:
                latency = round((time.perf_counter() - t0) * 1000, 2)
                provider_status["open_meteo"] = ProviderStatusItem(
                    status="failed", latency_ms=latency, message=exc.detail
                )
                errors.append(ProviderErrorItem(
                    provider="Open-Meteo Marine",
                    error_code="PROVIDER_ERROR_OPEN_METEO_MARINE",
                    message=exc.detail,
                    is_timeout=exc.is_timeout,
                ))
            except Exception as exc:
                latency = round((time.perf_counter() - t0) * 1000, 2)
                provider_status["open_meteo"] = ProviderStatusItem(status="failed", latency_ms=latency, message=str(exc))
                errors.append(ProviderErrorItem(
                    provider="Open-Meteo Marine",
                    error_code="OPEN_METEO_ERROR",
                    message=str(exc),
                ))

        async def run_imd():
            if not is_enabled("imd"):
                provider_status["imd"] = ProviderStatusItem(status="skipped", message="Filtered out by user")
                return
            t0 = time.perf_counter()
            try:
                # Concurrently fetch IMD weather, coastal bulletin, sea bulletin, nowcast
                wx_task = self._imd.get_current_weather(station_id=imd_station_id)
                coastal_task = self._imd.get_coastal_bulletin()
                sea_task = self._imd.get_sea_area_bulletin()
                nowcast_task = self._imd.get_district_nowcast()

                results = await asyncio.gather(wx_task, coastal_task, sea_task, nowcast_task, return_exceptions=True)
                latency = round((time.perf_counter() - t0) * 1000, 2)
                wx_res, coastal_res, sea_res, nowcast_res = results

                any_success = False

                # Process Weather
                if isinstance(wx_res, (dict, list)):
                    any_success = True
                    wx_data = wx_res[0] if isinstance(wx_res, list) and wx_res else wx_res
                    if isinstance(wx_data, dict):
                        temp = _try_float(wx_data.get("Temperature (deg C)") or wx_data.get("Temperature"))
                        humidity = _try_float(wx_data.get("Humidity (%)") or wx_data.get("Humidity"))
                        wind_spd = _try_float(wx_data.get("Wind Speed (KMPH)"))
                        wind_dir = _try_float(wx_data.get("Wind Direction (code)"))
                        mslp = _try_float(wx_data.get("M.S.L.P (hPa)"))
                        rain = _try_float(wx_data.get("Last 24 hrs Rainfall (mm)"))
                        obs_time = wx_data.get("Date/Time of Observation")
                        station_id = wx_data.get("Station Id") or imd_station_id

                        weather_candidates.append({
                            "source": "IMD",
                            "priority": 1,  # Highest for weather
                            "temperature": temp,
                            "temperature_unit": "degC" if temp is not None else None,
                            "wind_speed": wind_spd,
                            "wind_speed_unit": "km/h" if wind_spd is not None else None,
                            "wind_direction": wind_dir,
                            "humidity": humidity,
                            "humidity_unit": "%" if humidity is not None else None,
                            "pressure": mslp,
                            "pressure_unit": "hPa" if mslp is not None else None,
                            "precipitation": rain,
                            "precipitation_unit": "mm" if rain is not None else None,
                            "visibility": None,
                            "visibility_unit": None,
                            "condition": str(wx_data.get("Weather Code")) if wx_data.get("Weather Code") else None,
                            "data_type": "observation",
                            "timestamp": obs_time,
                        })

                        if temp is not None:
                            observations.append(ObservationItem(
                                parameter="Temperature",
                                value=temp,
                                unit="degC",
                                source="IMD",
                                timestamp=obs_time,
                                station_id=str(station_id) if station_id else None,
                                latitude=latitude,
                                longitude=longitude,
                            ))
                elif isinstance(wx_res, ProviderError):
                    errors.append(ProviderErrorItem(
                        provider="IMD",
                        error_code="PROVIDER_ERROR_IMD",
                        message=f"Current weather error: {wx_res.detail}",
                        is_timeout=wx_res.is_timeout,
                    ))

                # Process Coastal Bulletins
                if isinstance(coastal_res, list):
                    any_success = True
                    for item in coastal_res:
                        if isinstance(item, dict):
                            layer = item.get("Layer", "Coastal Stretch")
                            sea_cond = item.get("Sea Condition", "")
                            wind_info = item.get("Wind", "")
                            weather_info = item.get("Weather", "")
                            bulletins.append(BulletinItem(
                                title=f"Coastal Bulletin: {layer}",
                                text=f"Sea condition: {sea_cond}. Wind: {wind_info}. Weather: {weather_info}",
                                type="coastal_bulletin",
                                source="IMD",
                                area=layer,
                                severity="Informational",
                            ))

                # Process Sea Area Bulletins
                if isinstance(sea_res, list):
                    any_success = True
                    for item in sea_res:
                        if isinstance(item, dict):
                            area = item.get("Area") or item.get("Sea Area", "Sea Area")
                            text_desc = item.get("Bulletin") or item.get("Description") or str(item)
                            bulletins.append(BulletinItem(
                                title=f"Sea Area Bulletin: {area}",
                                text=text_desc,
                                type="sea_area_bulletin",
                                source="IMD",
                                area=area,
                                severity="Advisory",
                            ))

                # Process Nowcast
                if isinstance(nowcast_res, list):
                    any_success = True
                    for item in nowcast_res:
                        if isinstance(item, dict) and (item.get("message") or item.get("Station")):
                            stn = item.get("Station", "District")
                            msg = item.get("message", "No active warning")
                            validity = item.get("validity")
                            bulletins.append(BulletinItem(
                                title=f"Nowcast: {stn}",
                                text=msg,
                                type="nowcast",
                                source="IMD",
                                area=stn,
                                severity="Warning" if "warning" in msg.lower() else "Notice",
                                timestamp=validity,
                            ))

                if any_success:
                    sources.append("IMD")
                    provider_status["imd"] = ProviderStatusItem(status="success", latency_ms=latency)
                else:
                    first_err = next((r for r in results if isinstance(r, Exception)), None)
                    msg = str(first_err) if first_err else "No data returned from IMD"
                    provider_status["imd"] = ProviderStatusItem(status="failed", latency_ms=latency, message=msg)

            except Exception as exc:
                latency = round((time.perf_counter() - t0) * 1000, 2)
                provider_status["imd"] = ProviderStatusItem(status="failed", latency_ms=latency, message=str(exc))
                errors.append(ProviderErrorItem(
                    provider="IMD",
                    error_code="IMD_ERROR",
                    message=str(exc),
                ))

        async def run_noaa_weather():
            if not is_enabled("noaa_weather"):
                provider_status["noaa_weather"] = ProviderStatusItem(status="skipped", message="Filtered out by user")
                return
            t0 = time.perf_counter()
            try:
                # NWS forecast + alerts
                fc_task = self._noaa_weather.get_forecast(latitude, longitude)
                al_task = self._noaa_weather.get_active_alerts(point=f"{latitude},{longitude}")

                results = await asyncio.gather(fc_task, al_task, return_exceptions=True)
                latency = round((time.perf_counter() - t0) * 1000, 2)
                fc_res, al_res = results

                any_success = False

                if isinstance(fc_res, dict):
                    any_success = True
                    periods = fc_res.get("properties", {}).get("periods", [])
                    if periods:
                        p0 = periods[0]
                        raw_temp = _try_float(p0.get("temperature"))
                        temp_unit = p0.get("temperatureUnit", "F")
                        # If F, convert to degC for standard comparison while preserving unit
                        temp_c = round((raw_temp - 32) * 5 / 9, 2) if (raw_temp is not None and temp_unit == "F") else raw_temp

                        # parse wind speed e.g. "10 mph"
                        raw_wind = p0.get("windSpeed", "")
                        wind_parts = raw_wind.split()
                        wind_val = _try_float(wind_parts[0]) if wind_parts else None

                        weather_candidates.append({
                            "source": "NOAA Weather (NWS)",
                            "priority": 2,  # After IMD
                            "temperature": temp_c,
                            "temperature_unit": "degC" if temp_c is not None else None,
                            "wind_speed": wind_val,
                            "wind_speed_unit": "mph" if wind_val is not None else None,
                            "wind_direction": None,
                            "humidity": None,
                            "humidity_unit": None,
                            "pressure": None,
                            "pressure_unit": None,
                            "precipitation": None,
                            "precipitation_unit": None,
                            "visibility": None,
                            "visibility_unit": None,
                            "condition": p0.get("shortForecast"),
                            "data_type": "forecast",
                            "timestamp": p0.get("startTime"),
                        })

                if isinstance(al_res, dict):
                    any_success = True
                    features = al_res.get("features", [])
                    for feat in features:
                        prop = feat.get("properties", {})
                        bulletins.append(BulletinItem(
                            title=prop.get("headline") or prop.get("event") or "NWS Marine Alert",
                            text=prop.get("description") or "Active weather alert",
                            type="weather_alert",
                            source="NOAA Weather (NWS)",
                            area=prop.get("areaDesc"),
                            severity=prop.get("severity"),
                            timestamp=prop.get("sent"),
                        ))

                if any_success:
                    sources.append("NOAA Weather (NWS)")
                    provider_status["noaa_weather"] = ProviderStatusItem(status="success", latency_ms=latency)
                else:
                    first_err = next((r for r in results if isinstance(r, Exception)), None)
                    msg = str(first_err) if first_err else "No data returned (likely outside US coverage)"
                    provider_status["noaa_weather"] = ProviderStatusItem(status="failed", latency_ms=latency, message=msg)
                    if isinstance(first_err, ProviderError):
                        errors.append(ProviderErrorItem(
                            provider="NOAA Weather (NWS)",
                            error_code="PROVIDER_ERROR_NOAA_WEATHER",
                            message=first_err.detail,
                            is_timeout=first_err.is_timeout,
                        ))

            except Exception as exc:
                latency = round((time.perf_counter() - t0) * 1000, 2)
                provider_status["noaa_weather"] = ProviderStatusItem(status="failed", latency_ms=latency, message=str(exc))
                errors.append(ProviderErrorItem(
                    provider="NOAA Weather (NWS)",
                    error_code="NOAA_WEATHER_ERROR",
                    message=str(exc),
                ))

        async def run_noaa_ndbc():
            if not is_enabled("noaa_ndbc"):
                provider_status["noaa_ndbc"] = ProviderStatusItem(status="skipped", message="Filtered out by user")
                return
            if not noaa_ndbc_station_id:
                provider_status["noaa_ndbc"] = ProviderStatusItem(
                    status="skipped", message="No NOAA NDBC buoy station ID provided"
                )
                return
            t0 = time.perf_counter()
            try:
                res = await self._noaa_ndbc.get_standard_meteorological(noaa_ndbc_station_id)
                latency = round((time.perf_counter() - t0) * 1000, 2)
                provider_status["noaa_ndbc"] = ProviderStatusItem(status="success", latency_ms=latency)
                sources.append("NOAA/NDBC")

                obs_list = res.get("observations", [])
                if obs_list:
                    obs0 = obs_list[0]
                    obs_time = obs0.get("timestamp")

                    # Wave candidate
                    wvht = obs0.get("WVHT")
                    dpd = obs0.get("DPD")
                    mwd = obs0.get("MWD")
                    if wvht is not None:
                        wave_candidates.append({
                            "source": "NOAA/NDBC",
                            "priority": 3,
                            "height": _try_float(wvht),
                            "height_unit": "m",
                            "direction": _try_float(mwd),
                            "period": _try_float(dpd),
                            "period_unit": "s",
                            "swell_height": None,
                            "data_type": "observation",
                            "timestamp": obs_time,
                        })
                        observations.append(ObservationItem(
                            parameter="WVHT",
                            value=wvht,
                            unit="m",
                            source="NOAA/NDBC",
                            timestamp=obs_time,
                            station_id=noaa_ndbc_station_id,
                            latitude=latitude,
                            longitude=longitude,
                        ))

                    # Weather candidate
                    atmp = obs0.get("ATMP")
                    wspd = obs0.get("WSPD")
                    wdir = obs0.get("WDIR")
                    pres = obs0.get("PRES")
                    if any(v is not None for v in (atmp, wspd, wdir, pres)):
                        weather_candidates.append({
                            "source": "NOAA/NDBC",
                            "priority": 2,
                            "temperature": _try_float(atmp),
                            "temperature_unit": "degC" if atmp is not None else None,
                            "wind_speed": _try_float(wspd),
                            "wind_speed_unit": "m/s" if wspd is not None else None,
                            "wind_direction": _try_float(wdir),
                            "humidity": None,
                            "humidity_unit": None,
                            "pressure": _try_float(pres),
                            "pressure_unit": "hPa" if pres is not None else None,
                            "precipitation": None,
                            "precipitation_unit": None,
                            "visibility": _try_float(obs0.get("VIS")),
                            "visibility_unit": "nmi" if obs0.get("VIS") is not None else None,
                            "condition": None,
                            "data_type": "observation",
                            "timestamp": obs_time,
                        })

                    # Ocean SST candidate
                    wtmp = obs0.get("WTMP")
                    if wtmp is not None:
                        ocean_candidates.append({
                            "source": "NOAA/NDBC",
                            "priority": 3,
                            "sst": _try_float(wtmp),
                            "sst_unit": "degC",
                            "chlorophyll": None,
                            "salinity": None,
                            "data_type": "observation",
                            "timestamp": obs_time,
                        })
                        observations.append(ObservationItem(
                            parameter="WTMP",
                            value=wtmp,
                            unit="degC",
                            source="NOAA/NDBC",
                            timestamp=obs_time,
                            station_id=noaa_ndbc_station_id,
                            latitude=latitude,
                            longitude=longitude,
                        ))

            except ProviderError as exc:
                latency = round((time.perf_counter() - t0) * 1000, 2)
                provider_status["noaa_ndbc"] = ProviderStatusItem(status="failed", latency_ms=latency, message=exc.detail)
                errors.append(ProviderErrorItem(
                    provider="NOAA/NDBC",
                    error_code="PROVIDER_ERROR_NOAA_NDBC",
                    message=exc.detail,
                    is_timeout=exc.is_timeout,
                ))
            except Exception as exc:
                latency = round((time.perf_counter() - t0) * 1000, 2)
                provider_status["noaa_ndbc"] = ProviderStatusItem(status="failed", latency_ms=latency, message=str(exc))
                errors.append(ProviderErrorItem(
                    provider="NOAA/NDBC",
                    error_code="NOAA_NDBC_ERROR",
                    message=str(exc),
                ))

        async def run_noaa_coops():
            if not is_enabled("noaa_coops"):
                provider_status["noaa_coops"] = ProviderStatusItem(status="skipped", message="Filtered out by user")
                return
            if not noaa_station_id:
                provider_status["noaa_coops"] = ProviderStatusItem(
                    status="skipped", message="No NOAA CO-OPS station ID provided"
                )
                return
            t0 = time.perf_counter()
            try:
                res = await self._noaa_coops.get_data(
                    station=noaa_station_id,
                    product="water_level",
                    date="latest",
                    datum="MLLW",
                    units="metric",
                )
                latency = round((time.perf_counter() - t0) * 1000, 2)
                provider_status["noaa_coops"] = ProviderStatusItem(status="success", latency_ms=latency)
                sources.append("NOAA CO-OPS")

                data_entries = res.get("data", []) if isinstance(res, dict) else []
                if data_entries:
                    d0 = data_entries[0]
                    wl = _try_float(d0.get("v"))
                    tide_time = d0.get("t")
                    tide_candidates.append({
                        "source": "NOAA CO-OPS",
                        "priority": 1,  # Highest for tides
                        "water_level": wl,
                        "water_level_unit": "m",
                        "datum": "MLLW",
                        "prediction": None,
                        "extremes": [],
                        "data_type": "observation",
                        "timestamp": tide_time,
                    })
                    observations.append(ObservationItem(
                        parameter="water_level",
                        value=wl,
                        unit="m",
                        source="NOAA CO-OPS",
                        timestamp=tide_time,
                        station_id=noaa_station_id,
                        latitude=latitude,
                        longitude=longitude,
                    ))

            except ProviderError as exc:
                latency = round((time.perf_counter() - t0) * 1000, 2)
                provider_status["noaa_coops"] = ProviderStatusItem(status="failed", latency_ms=latency, message=exc.detail)
                errors.append(ProviderErrorItem(
                    provider="NOAA CO-OPS",
                    error_code="PROVIDER_ERROR_NOAA_COOPS",
                    message=exc.detail,
                    is_timeout=exc.is_timeout,
                ))
            except Exception as exc:
                latency = round((time.perf_counter() - t0) * 1000, 2)
                provider_status["noaa_coops"] = ProviderStatusItem(status="failed", latency_ms=latency, message=str(exc))
                errors.append(ProviderErrorItem(
                    provider="NOAA CO-OPS",
                    error_code="NOAA_COOPS_ERROR",
                    message=str(exc),
                ))

        async def run_tidesatlas():
            if not is_enabled("tidesatlas"):
                provider_status["tidesatlas"] = ProviderStatusItem(status="skipped", message="Filtered out by user")
                return
            t0 = time.perf_counter()
            try:
                tides_task = self._tidesatlas.get_tides_point(lat=latitude, lon=longitude)
                marine_task = self._tidesatlas.get_marine(lat=latitude, lon=longitude)
                weather_task = self._tidesatlas.get_weather(lat=latitude, lon=longitude)

                results = await asyncio.gather(tides_task, marine_task, weather_task, return_exceptions=True)
                latency = round((time.perf_counter() - t0) * 1000, 2)
                tides_res, marine_res, wx_res = results

                any_success = False

                # Tides
                if isinstance(tides_res, dict):
                    any_success = True
                    extremes = tides_res.get("extremes", [])
                    tide_candidates.append({
                        "source": "TidesAtlas",
                        "priority": 2,  # After NOAA CO-OPS
                        "water_level": _try_float(extremes[0].get("height_m")) if extremes else None,
                        "water_level_unit": "m",
                        "datum": tides_res.get("datum", "LAT"),
                        "prediction": extremes[0].get("type") if extremes else None,
                        "extremes": extremes,
                        "data_type": "prediction",
                        "timestamp": extremes[0].get("datetime") if extremes else None,
                    })

                # Marine (Waves & SST)
                if isinstance(marine_res, dict):
                    any_success = True
                    daily = marine_res.get("daily", [])
                    if daily:
                        d0 = daily[0]
                        wvht = _try_float(d0.get("wave_height_max_m") or d0.get("wave_height"))
                        wave_candidates.append({
                            "source": "TidesAtlas",
                            "priority": 2,  # After Open-Meteo
                            "height": wvht,
                            "height_unit": "m",
                            "direction": _try_float(d0.get("wave_direction")),
                            "period": _try_float(d0.get("wave_period")),
                            "period_unit": "s",
                            "swell_height": _try_float(d0.get("swell_height_m")),
                            "swell_height_unit": "m" if d0.get("swell_height_m") is not None else None,
                            "data_type": "forecast",
                            "timestamp": d0.get("date"),
                        })

                        sst = _try_float(d0.get("sea_surface_temperature_c") or d0.get("sst"))
                        if sst is not None:
                            ocean_candidates.append({
                                "source": "TidesAtlas",
                                "priority": 3,
                                "sst": sst,
                                "sst_unit": "degC",
                                "chlorophyll": None,
                                "salinity": None,
                                "data_type": "forecast",
                                "timestamp": d0.get("date"),
                            })

                # Weather
                if isinstance(wx_res, dict):
                    any_success = True
                    daily = wx_res.get("daily", [])
                    if daily:
                        w0 = daily[0]
                        temp = _try_float(w0.get("temperature_max_c") or w0.get("temperature"))
                        wind = _try_float(w0.get("wind_speed_max_kmh") or w0.get("wind_speed"))
                        weather_candidates.append({
                            "source": "TidesAtlas",
                            "priority": 3,
                            "temperature": temp,
                            "temperature_unit": "degC" if temp is not None else None,
                            "wind_speed": wind,
                            "wind_speed_unit": "km/h" if wind is not None else None,
                            "wind_direction": None,
                            "humidity": _try_float(w0.get("humidity")),
                            "humidity_unit": "%" if w0.get("humidity") is not None else None,
                            "pressure": None,
                            "pressure_unit": None,
                            "precipitation": _try_float(w0.get("precipitation_mm")),
                            "precipitation_unit": "mm" if w0.get("precipitation_mm") is not None else None,
                            "visibility": None,
                            "visibility_unit": None,
                            "condition": w0.get("condition"),
                            "data_type": "forecast",
                            "timestamp": w0.get("date"),
                        })

                if any_success:
                    sources.append("TidesAtlas")
                    provider_status["tidesatlas"] = ProviderStatusItem(status="success", latency_ms=latency)
                else:
                    first_err = next((r for r in results if isinstance(r, Exception)), None)
                    if isinstance(first_err, ProviderNotConfigured):
                        provider_status["tidesatlas"] = ProviderStatusItem(
                            status="not_configured", latency_ms=latency, message=first_err.detail
                        )
                    elif isinstance(first_err, ProviderError):
                        provider_status["tidesatlas"] = ProviderStatusItem(
                            status="failed", latency_ms=latency, message=first_err.detail
                        )
                        errors.append(ProviderErrorItem(
                            provider="TidesAtlas",
                            error_code="PROVIDER_ERROR_TIDESATLAS",
                            message=first_err.detail,
                            is_timeout=first_err.is_timeout,
                        ))
                    else:
                        provider_status["tidesatlas"] = ProviderStatusItem(
                            status="failed", latency_ms=latency, message=str(first_err) if first_err else "No data"
                        )

            except ProviderNotConfigured as exc:
                latency = round((time.perf_counter() - t0) * 1000, 2)
                provider_status["tidesatlas"] = ProviderStatusItem(
                    status="not_configured", latency_ms=latency, message=exc.detail
                )
            except ProviderError as exc:
                latency = round((time.perf_counter() - t0) * 1000, 2)
                provider_status["tidesatlas"] = ProviderStatusItem(status="failed", latency_ms=latency, message=exc.detail)
                errors.append(ProviderErrorItem(
                    provider="TidesAtlas",
                    error_code="PROVIDER_ERROR_TIDESATLAS",
                    message=exc.detail,
                    is_timeout=exc.is_timeout,
                ))
            except Exception as exc:
                latency = round((time.perf_counter() - t0) * 1000, 2)
                provider_status["tidesatlas"] = ProviderStatusItem(status="failed", latency_ms=latency, message=str(exc))
                errors.append(ProviderErrorItem(
                    provider="TidesAtlas",
                    error_code="TIDESATLAS_ERROR",
                    message=str(exc),
                ))

        async def run_nasa_ocean_color():
            if not is_enabled("nasa_ocean_color"):
                provider_status["nasa_ocean_color"] = ProviderStatusItem(status="skipped", message="Filtered out by user")
                return
            t0 = time.perf_counter()
            try:
                date_str = (target_time or now_utc)[:10]
                await self._nasa_ocean_color.get_point_value(
                    latitude=latitude, longitude=longitude, product="chlor_a", date=date_str
                )
                latency = round((time.perf_counter() - t0) * 1000, 2)
                provider_status["nasa_ocean_color"] = ProviderStatusItem(status="success", latency_ms=latency)
                sources.append("NASA Ocean Color")
            except OceanColorExtractionPending as exc:
                latency = round((time.perf_counter() - t0) * 1000, 2)
                provider_status["nasa_ocean_color"] = ProviderStatusItem(
                    status="not_implemented",
                    latency_ms=latency,
                    message=str(exc),
                )
            except ProviderError as exc:
                latency = round((time.perf_counter() - t0) * 1000, 2)
                provider_status["nasa_ocean_color"] = ProviderStatusItem(
                    status="failed", latency_ms=latency, message=exc.detail
                )
                errors.append(ProviderErrorItem(
                    provider="NASA Ocean Color",
                    error_code="PROVIDER_ERROR_NASA_OCEAN_COLOR",
                    message=exc.detail,
                    is_timeout=exc.is_timeout,
                ))
            except Exception as exc:
                latency = round((time.perf_counter() - t0) * 1000, 2)
                provider_status["nasa_ocean_color"] = ProviderStatusItem(
                    status="failed", latency_ms=latency, message=str(exc)
                )
                errors.append(ProviderErrorItem(
                    provider="NASA Ocean Color",
                    error_code="NASA_OCEAN_COLOR_ERROR",
                    message=str(exc),
                ))

        # Launch all provider tasks concurrently
        await asyncio.gather(
            run_open_meteo(),
            run_imd(),
            run_noaa_weather(),
            run_noaa_ndbc(),
            run_noaa_coops(),
            run_tidesatlas(),
            run_nasa_ocean_color(),
        )

        # --- Section Resolution with Priority & Discrepancies ---

        # 1. WEATHER: IMD (priority 1) > NOAA (priority 2) > TidesAtlas (priority 3)
        weather_sec = self._resolve_weather(weather_candidates)

        # 2. WAVES: Open-Meteo (priority 1) > TidesAtlas (priority 2) > NOAA NDBC (priority 3)
        waves_sec = self._resolve_waves(wave_candidates)

        # 3. OCEAN: NASA Ocean Color (priority 1) > Open-Meteo (priority 2) > NOAA / TidesAtlas (priority 3)
        ocean_sec = self._resolve_ocean(ocean_candidates)

        # 4. CURRENTS: Open-Meteo (priority 1) > NOAA CO-OPS (priority 2)
        currents_sec = self._resolve_currents(current_candidates)

        # 5. TIDES: NOAA CO-OPS (priority 1) > TidesAtlas (priority 2) > Open-Meteo (priority 3)
        tides_sec = self._resolve_tides(tide_candidates)

        # Remove duplicates from sources preserving order
        unique_sources = list(dict.fromkeys(sources))

        return UnifiedMarineDataResponse(
            location=LocationSchema(latitude=latitude, longitude=longitude),
            timestamp=now_utc,
            weather=weather_sec,
            ocean=ocean_sec,
            waves=waves_sec,
            currents=currents_sec,
            tides=tides_sec,
            observations=observations,
            bulletins=bulletins,
            sources=unique_sources,
            provider_status=provider_status,
            errors=errors,
        )

    def _resolve_weather(self, candidates: list[dict[str, Any]]) -> WeatherSection:
        if not candidates:
            return WeatherSection()

        # Sort candidates by priority (lowest number = highest priority)
        sorted_cands = sorted(candidates, key=lambda c: c.get("priority", 99))
        primary = sorted_cands[0]

        # Sources map
        sources_map = {c["source"]: c for c in candidates}

        # Check for discrepancies on key metrics: temperature, wind_speed
        discrepancies: list[DiscrepancyItem] = []

        temp_cands = [
            {"source": c["source"], "value": c["temperature"], "unit": c["temperature_unit"]}
            for c in candidates
            if c.get("temperature") is not None
        ]
        if len(temp_cands) > 1:
            vals = [c["value"] for c in temp_cands]
            max_diff = max(vals) - min(vals)
            if max_diff > 0.5:  # Noticeable difference
                discrepancies.append(DiscrepancyItem(
                    parameter="temperature",
                    primary=temp_cands[0],
                    candidates=temp_cands,
                    delta=round(max_diff, 2),
                ))

        wind_cands = [
            {"source": c["source"], "value": c["wind_speed"], "unit": c["wind_speed_unit"]}
            for c in candidates
            if c.get("wind_speed") is not None
        ]
        if len(wind_cands) > 1:
            vals = [c["value"] for c in wind_cands]
            max_diff = max(vals) - min(vals)
            if max_diff > 1.0:
                discrepancies.append(DiscrepancyItem(
                    parameter="wind_speed",
                    primary=wind_cands[0],
                    candidates=wind_cands,
                    delta=round(max_diff, 2),
                ))

        return WeatherSection(
            temperature=primary.get("temperature"),
            temperature_unit=primary.get("temperature_unit"),
            wind_speed=primary.get("wind_speed"),
            wind_speed_unit=primary.get("wind_speed_unit"),
            wind_direction=primary.get("wind_direction"),
            humidity=primary.get("humidity"),
            humidity_unit=primary.get("humidity_unit"),
            pressure=primary.get("pressure"),
            pressure_unit=primary.get("pressure_unit"),
            precipitation=primary.get("precipitation"),
            precipitation_unit=primary.get("precipitation_unit"),
            visibility=primary.get("visibility"),
            visibility_unit=primary.get("visibility_unit"),
            condition=primary.get("condition"),
            source=primary.get("source"),
            data_type=primary.get("data_type"),
            timestamp=primary.get("timestamp"),
            sources=sources_map,
            discrepancies=discrepancies,
        )

    def _resolve_waves(self, candidates: list[dict[str, Any]]) -> WavesSection:
        if not candidates:
            return WavesSection()

        sorted_cands = sorted(candidates, key=lambda c: c.get("priority", 99))
        primary = sorted_cands[0]
        sources_map = {c["source"]: c for c in candidates}

        discrepancies: list[DiscrepancyItem] = []
        height_cands = [
            {"source": c["source"], "value": c["height"], "unit": c["height_unit"]}
            for c in candidates
            if c.get("height") is not None
        ]
        if len(height_cands) > 1:
            vals = [c["value"] for c in height_cands]
            max_diff = max(vals) - min(vals)
            if max_diff > 0.1:  # Discrepancy > 10 cm
                discrepancies.append(DiscrepancyItem(
                    parameter="wave_height",
                    primary=height_cands[0],
                    candidates=height_cands,
                    delta=round(max_diff, 3),
                ))

        return WavesSection(
            height=primary.get("height"),
            height_unit=primary.get("height_unit"),
            direction=primary.get("direction"),
            period=primary.get("period"),
            period_unit=primary.get("period_unit"),
            swell_height=primary.get("swell_height"),
            swell_height_unit=primary.get("swell_height_unit"),
            swell_direction=primary.get("swell_direction"),
            swell_period=primary.get("swell_period"),
            source=primary.get("source"),
            data_type=primary.get("data_type"),
            timestamp=primary.get("timestamp"),
            sources=sources_map,
            discrepancies=discrepancies,
        )

    def _resolve_ocean(self, candidates: list[dict[str, Any]]) -> OceanSection:
        if not candidates:
            return OceanSection()

        sorted_cands = sorted(candidates, key=lambda c: c.get("priority", 99))
        primary = sorted_cands[0]
        sources_map = {c["source"]: c for c in candidates}

        discrepancies: list[DiscrepancyItem] = []
        sst_cands = [
            {"source": c["source"], "value": c["sst"], "unit": c["sst_unit"]}
            for c in candidates
            if c.get("sst") is not None
        ]
        if len(sst_cands) > 1:
            vals = [c["value"] for c in sst_cands]
            max_diff = max(vals) - min(vals)
            if max_diff > 0.2:
                discrepancies.append(DiscrepancyItem(
                    parameter="sea_surface_temperature",
                    primary=sst_cands[0],
                    candidates=sst_cands,
                    delta=round(max_diff, 2),
                ))

        return OceanSection(
            sea_surface_temperature=primary.get("sst"),
            sst_unit=primary.get("sst_unit"),
            sst_source=primary.get("source"),
            sst_data_type=primary.get("data_type"),
            chlorophyll=primary.get("chlorophyll"),
            chlorophyll_unit=None,
            chlorophyll_source=None,
            salinity=primary.get("salinity"),
            salinity_unit=None,
            salinity_source=None,
            sources=sources_map,
            discrepancies=discrepancies,
        )

    def _resolve_currents(self, candidates: list[dict[str, Any]]) -> CurrentsSection:
        if not candidates:
            return CurrentsSection()

        sorted_cands = sorted(candidates, key=lambda c: c.get("priority", 99))
        primary = sorted_cands[0]
        sources_map = {c["source"]: c for c in candidates}

        return CurrentsSection(
            velocity=primary.get("velocity"),
            velocity_unit=primary.get("velocity_unit"),
            direction=primary.get("direction"),
            source=primary.get("source"),
            data_type=primary.get("data_type"),
            timestamp=primary.get("timestamp"),
            sources=sources_map,
        )

    def _resolve_tides(self, candidates: list[dict[str, Any]]) -> TidesSection:
        if not candidates:
            return TidesSection()

        sorted_cands = sorted(candidates, key=lambda c: c.get("priority", 99))
        primary = sorted_cands[0]
        sources_map = {c["source"]: c for c in candidates}

        discrepancies: list[DiscrepancyItem] = []
        level_cands = [
            {"source": c["source"], "value": c["water_level"], "unit": c["water_level_unit"]}
            for c in candidates
            if c.get("water_level") is not None
        ]
        if len(level_cands) > 1:
            vals = [c["value"] for c in level_cands]
            max_diff = max(vals) - min(vals)
            if max_diff > 0.05:
                discrepancies.append(DiscrepancyItem(
                    parameter="water_level",
                    primary=level_cands[0],
                    candidates=level_cands,
                    delta=round(max_diff, 3),
                ))

        return TidesSection(
            water_level=primary.get("water_level"),
            water_level_unit=primary.get("water_level_unit"),
            prediction=primary.get("prediction"),
            datum=primary.get("datum"),
            extremes=primary.get("extremes", []),
            source=primary.get("source"),
            data_type=primary.get("data_type"),
            timestamp=primary.get("timestamp"),
            sources=sources_map,
            discrepancies=discrepancies,
        )
