"""
Tests for Phase 9: Unified Marine Data Service (GET /api/marine/data).

Verifies:
- successful aggregation
- multiple providers
- partial provider failure
- provider timeout
- missing fields / zero fabrication
- invalid latitude and longitude
- source priority (Weather: IMD > NOAA; Waves: Open-Meteo > TidesAtlas > NOAA; Tides: CO-OPS > TidesAtlas)
- conflicting source values preservation (discrepancies)
- normalization into standard sections
- provider filtering
- all providers failing gracefully
"""
import httpx
import pytest

from app.api.deps import (
    get_imd_provider,
    get_nasa_ocean_color_provider,
    get_noaa_coops_provider,
    get_noaa_ndbc_provider,
    get_noaa_weather_provider,
    get_open_meteo_provider,
    get_tidesatlas_provider,
)
from app.core.config import get_settings
from app.main import app
from app.providers.imd_provider import IMDProvider
from app.providers.nasa_ocean_color_provider import NASAOceanColorProvider
from app.providers.noaa_coops_provider import NOAACoOpsProvider
from app.providers.noaa_ndbc_provider import NOAANDBCProvider
from app.providers.noaa_weather_provider import NOAAWeatherProvider
from app.providers.open_meteo_provider import OpenMeteoMarineProvider
from app.providers.tidesatlas_provider import TidesAtlasProvider


def _client_with(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


@pytest.fixture()
def marine_client(client):
    yield client
    app.dependency_overrides.pop(get_open_meteo_provider, None)
    app.dependency_overrides.pop(get_imd_provider, None)
    app.dependency_overrides.pop(get_nasa_ocean_color_provider, None)
    app.dependency_overrides.pop(get_noaa_coops_provider, None)
    app.dependency_overrides.pop(get_noaa_ndbc_provider, None)
    app.dependency_overrides.pop(get_noaa_weather_provider, None)
    app.dependency_overrides.pop(get_tidesatlas_provider, None)


def _mock_open_meteo(wave_height=1.5, wave_dir=240, wave_period=7.0, sst=28.2, cur_vel=0.35, cur_dir=195):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "latitude": float(request.url.params.get("latitude", 0)),
                "longitude": float(request.url.params.get("longitude", 0)),
                "current": {
                    "time": "2026-09-09T16:00",
                    "wave_height": wave_height,
                    "wave_direction": wave_dir,
                    "wave_period": wave_period,
                    "sea_surface_temperature": sst,
                    "ocean_current_velocity": cur_vel,
                    "ocean_current_direction": cur_dir,
                    "sea_level_height_msl": 0.42,
                },
                "current_units": {
                    "wave_height": "m",
                    "wave_direction": "°",
                    "wave_period": "s",
                    "sea_surface_temperature": "°C",
                    "ocean_current_velocity": "m/s",
                    "ocean_current_direction": "°",
                    "sea_level_height_msl": "m",
                },
            },
        )
    return OpenMeteoMarineProvider(_client_with(handler))


def _mock_imd(temp="32.4", humidity="65", wind_spd="18.0", wind_dir="180", mslp="1008.5", rain="5.0"):
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if "/current_wx" in path:
            return httpx.Response(
                200,
                json={
                    "Station Id": "42182",
                    "Station": "MUMBAI/COLABA",
                    "Temperature (deg C)": temp,
                    "Humidity (%)": humidity,
                    "Wind Speed (KMPH)": wind_spd,
                    "Wind Direction (code)": wind_dir,
                    "M.S.L.P (hPa)": mslp,
                    "Last 24 hrs Rainfall (mm)": rain,
                    "Date/Time of Observation": "2026-09-09 12:00:00",
                },
            )
        elif "/coastalbulletin" in path:
            return httpx.Response(
                200,
                json=[{"Layer": "Konkan-Goa coast", "Sea Condition": "Moderate", "Wind": "Westerly 15-20 kts", "Weather": "Scattered rain"}],
            )
        elif "/seabulletin" in path:
            return httpx.Response(200, json=[{"Area": "East Central Arabian Sea", "Bulletin": "Squally weather likely"}])
        elif "/districtnowcast" in path:
            return httpx.Response(200, json=[{"Station": "Mumbai", "message": "Light to moderate rain expected", "validity": "3 hours"}])
        return httpx.Response(404, json={"error": "Not found"})

    return IMDProvider(_client_with(handler))


def test_successful_aggregation(marine_client):
    app.dependency_overrides[get_open_meteo_provider] = lambda: _mock_open_meteo()
    app.dependency_overrides[get_imd_provider] = lambda: _mock_imd()

    response = marine_client.get("/api/marine/data", params={"latitude": 18.9, "longitude": 72.8})
    assert response.status_code == 200
    data = response.json()

    # Location & timestamp
    assert data["location"]["latitude"] == 18.9
    assert data["location"]["longitude"] == 72.8
    assert "timestamp" in data

    # Weather (from IMD)
    assert data["weather"]["temperature"] == 32.4
    assert data["weather"]["temperature_unit"] == "degC"
    assert data["weather"]["source"] == "IMD"
    assert data["weather"]["humidity"] == 65.0
    assert data["weather"]["wind_speed"] == 18.0
    assert data["weather"]["wind_speed_unit"] == "km/h"
    assert data["weather"]["pressure"] == 1008.5

    # Waves (from Open-Meteo)
    assert data["waves"]["height"] == 1.5
    assert data["waves"]["height_unit"] == "m"
    assert data["waves"]["direction"] == 240
    assert data["waves"]["period"] == 7.0
    assert data["waves"]["source"] == "Open-Meteo Marine"

    # Ocean (SST from Open-Meteo)
    assert data["ocean"]["sea_surface_temperature"] == 28.2
    assert data["ocean"]["sst_source"] == "Open-Meteo Marine"

    # Currents (from Open-Meteo)
    assert data["currents"]["velocity"] == 0.35
    assert data["currents"]["velocity_unit"] == "m/s"
    assert data["currents"]["direction"] == 195
    assert data["currents"]["source"] == "Open-Meteo Marine"

    # Bulletins
    assert len(data["bulletins"]) >= 2
    assert any(b["type"] == "coastal_bulletin" for b in data["bulletins"])

    # Sources & Provider Status
    assert "Open-Meteo Marine" in data["sources"]
    assert "IMD" in data["sources"]
    assert data["provider_status"]["open_meteo"]["status"] == "success"
    assert data["provider_status"]["imd"]["status"] == "success"
    assert data["provider_status"]["nasa_ocean_color"]["status"] == "not_implemented"


def test_multiple_providers_with_stations(marine_client, monkeypatch):
    monkeypatch.setattr(get_settings(), "TIDESATLAS_API_KEY", "test-key")

    app.dependency_overrides[get_open_meteo_provider] = lambda: _mock_open_meteo()
    app.dependency_overrides[get_imd_provider] = lambda: _mock_imd()

    # Mock NOAA CO-OPS
    def coops_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": [{"t": "2026-09-09 12:00", "v": "1.32"}]})
    app.dependency_overrides[get_noaa_coops_provider] = lambda: NOAACoOpsProvider(_client_with(coops_handler))

    # Mock NOAA NDBC
    sample_ndbc = (
        "#YY  MM DD hh mm WDIR WSPD GST  WVHT   DPD   APD MWD   PRES  ATMP  WTMP  DEWP  VIS PTDY  TIDE\n"
        "#yr  mo dy hr mn degT  m/s  m/s     m   sec   sec degT   hPa  degC  degC  degC  nmi   hPa    ft\n"
        "2026 09 09 12 00  190  6.2  7.5   1.4   6.5   5.8 185 1012.0  25.0  26.0    MM   MM   MM    MM\n"
    )
    def ndbc_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=sample_ndbc)
    app.dependency_overrides[get_noaa_ndbc_provider] = lambda: NOAANDBCProvider(_client_with(ndbc_handler))

    # Mock NOAA Weather NWS
    def nws_handler(request: httpx.Request) -> httpx.Response:
        if "/points/" in str(request.url):
            return httpx.Response(200, json={"properties": {"forecast": "https://api.weather.gov/gridpoints/MIA/10,10/forecast"}})
        elif "/alerts" in str(request.url):
            return httpx.Response(200, json={"features": [{"properties": {"headline": "Small Craft Advisory", "severity": "Moderate"}}]})
        return httpx.Response(200, json={"properties": {"periods": [{"name": "Today", "temperature": 77, "temperatureUnit": "F", "windSpeed": "10 mph"}]}})
    app.dependency_overrides[get_noaa_weather_provider] = lambda: NOAAWeatherProvider(_client_with(nws_handler))

    # Mock TidesAtlas
    def tides_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"datum": "LAT", "extremes": [{"datetime": "2026-09-09T14:00:00Z", "height_m": 1.15, "type": "high"}]})
    app.dependency_overrides[get_tidesatlas_provider] = lambda: TidesAtlasProvider(_client_with(tides_handler))

    response = marine_client.get(
        "/api/marine/data",
        params={
            "latitude": 25.7,
            "longitude": -80.2,
            "noaa_station_id": "8723214",
            "noaa_ndbc_station_id": "41009",
        },
    )
    assert response.status_code == 200
    data = response.json()

    # Tides: CO-OPS takes priority over TidesAtlas
    assert data["tides"]["water_level"] == 1.32
    assert data["tides"]["source"] == "NOAA CO-OPS"
    assert data["tides"]["datum"] == "MLLW"

    # Observations should include NDBC buoy and CO-OPS water level
    assert len(data["observations"]) >= 2
    params_found = {obs["parameter"] for obs in data["observations"]}
    assert "WVHT" in params_found or "water_level" in params_found


def test_partial_provider_failure_does_not_fail_endpoint(marine_client):
    app.dependency_overrides[get_open_meteo_provider] = lambda: _mock_open_meteo(wave_height=2.2)

    # IMD returns HTTP 500 error
    def imd_failing(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Server Error")
    app.dependency_overrides[get_imd_provider] = lambda: IMDProvider(_client_with(imd_failing))

    response = marine_client.get("/api/marine/data", params={"latitude": 15.0, "longitude": 73.0})
    # Endpoint MUST succeed with HTTP 200
    assert response.status_code == 200
    data = response.json()

    # Open-Meteo data is present
    assert data["waves"]["height"] == 2.2
    assert data["waves"]["source"] == "Open-Meteo Marine"
    assert data["provider_status"]["open_meteo"]["status"] == "success"

    # IMD status reflects failure and error is logged in errors list
    assert data["provider_status"]["imd"]["status"] == "failed"
    assert any("IMD" in err["provider"] for err in data["errors"])


def test_provider_timeout_handled_gracefully(marine_client):
    # Open-Meteo times out
    def om_timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("Connection timed out", request=request)
    app.dependency_overrides[get_open_meteo_provider] = lambda: OpenMeteoMarineProvider(_client_with(om_timeout))

    # IMD succeeds
    app.dependency_overrides[get_imd_provider] = lambda: _mock_imd(temp="31.0")

    response = marine_client.get("/api/marine/data", params={"latitude": 12.0, "longitude": 80.0})
    assert response.status_code == 200
    data = response.json()

    # IMD weather data succeeded
    assert data["weather"]["temperature"] == 31.0
    assert data["provider_status"]["imd"]["status"] == "success"

    # Open-Meteo timed out
    assert data["provider_status"]["open_meteo"]["status"] == "failed"
    timeout_errors = [e for e in data["errors"] if e["is_timeout"]]
    assert len(timeout_errors) >= 1
    assert timeout_errors[0]["provider"] == "Open-Meteo Marine"


def test_missing_fields_never_fabricated(marine_client):
    # Open-Meteo without wave_period or direction
    def om_minimal(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "latitude": 10.0,
                "longitude": 75.0,
                "current": {"time": "2026-09-09T00:00", "wave_height": 1.1},
                "current_units": {"wave_height": "m"},
            },
        )
    app.dependency_overrides[get_open_meteo_provider] = lambda: OpenMeteoMarineProvider(_client_with(om_minimal))

    response = marine_client.get(
        "/api/marine/data",
        params={"latitude": 10.0, "longitude": 75.0, "providers": "open_meteo,nasa_ocean_color"},
    )
    assert response.status_code == 200
    data = response.json()

    # Available field
    assert data["waves"]["height"] == 1.1

    # Missing fields MUST be null, not 0 or fabricated defaults
    assert data["waves"]["period"] is None
    assert data["waves"]["direction"] is None
    assert data["waves"]["swell_height"] is None
    assert data["ocean"]["chlorophyll"] is None
    assert data["ocean"]["salinity"] is None
    assert data["provider_status"]["nasa_ocean_color"]["status"] == "not_implemented"


def test_invalid_latitude_returns_422(marine_client):
    response = marine_client.get("/api/marine/data", params={"latitude": 95.0, "longitude": 72.0})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"

    response_low = marine_client.get("/api/marine/data", params={"latitude": -95.0, "longitude": 72.0})
    assert response_low.status_code == 422


def test_invalid_longitude_returns_422(marine_client):
    response = marine_client.get("/api/marine/data", params={"latitude": 10.0, "longitude": 185.0})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"

    response_low = marine_client.get("/api/marine/data", params={"latitude": 10.0, "longitude": -190.0})
    assert response_low.status_code == 422


def test_source_priority_weather_imd_over_noaa(marine_client):
    # IMD reports 33.0 degC
    app.dependency_overrides[get_imd_provider] = lambda: _mock_imd(temp="33.0")

    # NOAA reports 26.0 degC (78.8 F)
    def nws_handler(request: httpx.Request) -> httpx.Response:
        if "/points/" in str(request.url):
            return httpx.Response(200, json={"properties": {"forecast": "https://api.weather.gov/forecast"}})
        return httpx.Response(200, json={"properties": {"periods": [{"temperature": 78.8, "temperatureUnit": "F"}]}})
    app.dependency_overrides[get_noaa_weather_provider] = lambda: NOAAWeatherProvider(_client_with(nws_handler))

    response = marine_client.get(
        "/api/marine/data",
        params={"latitude": 20.0, "longitude": 70.0, "providers": "imd,noaa_weather"},
    )
    assert response.status_code == 200
    data = response.json()

    # IMD has priority 1, NOAA has priority 2
    assert data["weather"]["temperature"] == 33.0
    assert data["weather"]["source"] == "IMD"
    assert "IMD" in data["weather"]["sources"]
    assert "NOAA Weather (NWS)" in data["weather"]["sources"]


def test_source_priority_waves_open_meteo_over_tidesatlas_and_ndbc(marine_client, monkeypatch):
    monkeypatch.setattr(get_settings(), "TIDESATLAS_API_KEY", "test-key")

    # Open-Meteo reports wave_height 1.8 m
    app.dependency_overrides[get_open_meteo_provider] = lambda: _mock_open_meteo(wave_height=1.8)

    # TidesAtlas reports wave_height 1.3 m
    def tides_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"daily": [{"wave_height_max_m": 1.3}]})
    app.dependency_overrides[get_tidesatlas_provider] = lambda: TidesAtlasProvider(_client_with(tides_handler))

    response = marine_client.get(
        "/api/marine/data",
        params={"latitude": 18.0, "longitude": 72.0, "providers": "open_meteo,tidesatlas"},
    )
    assert response.status_code == 200
    data = response.json()

    # Open-Meteo has priority 1
    assert data["waves"]["height"] == 1.8
    assert data["waves"]["source"] == "Open-Meteo Marine"


def test_conflicting_source_values_preserved_in_discrepancies(marine_client, monkeypatch):
    monkeypatch.setattr(get_settings(), "TIDESATLAS_API_KEY", "test-key")

    # Open-Meteo reports wave height 2.5 m
    app.dependency_overrides[get_open_meteo_provider] = lambda: _mock_open_meteo(wave_height=2.5)

    # TidesAtlas reports wave height 1.5 m (difference 1.0 m)
    def tides_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"daily": [{"wave_height_max_m": 1.5}]})
    app.dependency_overrides[get_tidesatlas_provider] = lambda: TidesAtlasProvider(_client_with(tides_handler))

    response = marine_client.get(
        "/api/marine/data",
        params={"latitude": 18.0, "longitude": 72.0, "providers": "open_meteo,tidesatlas"},
    )
    assert response.status_code == 200
    data = response.json()

    # Primary value is selected via priority (Open-Meteo)
    assert data["waves"]["height"] == 2.5
    assert data["waves"]["source"] == "Open-Meteo Marine"

    # Discrepancy is recorded and preserved!
    assert len(data["waves"]["discrepancies"]) == 1
    discrepancy = data["waves"]["discrepancies"][0]
    assert discrepancy["parameter"] == "wave_height"
    assert discrepancy["primary"]["source"] == "Open-Meteo Marine"
    assert discrepancy["primary"]["value"] == 2.5
    assert discrepancy["delta"] == 1.0
    assert len(discrepancy["candidates"]) == 2


def test_provider_filtering(marine_client):
    app.dependency_overrides[get_open_meteo_provider] = lambda: _mock_open_meteo()
    app.dependency_overrides[get_imd_provider] = lambda: _mock_imd()

    # Query with filter "open_meteo" only
    response = marine_client.get(
        "/api/marine/data",
        params={"latitude": 19.0, "longitude": 72.0, "providers": "open_meteo"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["provider_status"]["open_meteo"]["status"] == "success"
    assert data["provider_status"]["imd"]["status"] == "skipped"
    assert data["provider_status"]["noaa_weather"]["status"] == "skipped"
    assert data["weather"]["temperature"] is None  # IMD was skipped


def test_all_providers_failing_returns_graceful_200(marine_client):
    def error_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Downstream Outage")

    app.dependency_overrides[get_open_meteo_provider] = lambda: OpenMeteoMarineProvider(_client_with(error_handler))
    app.dependency_overrides[get_imd_provider] = lambda: IMDProvider(_client_with(error_handler))

    response = marine_client.get(
        "/api/marine/data",
        params={"latitude": 10.0, "longitude": 70.0, "providers": "open_meteo,imd"},
    )
    # Endpoint does NOT 500/502 — returns 200 with error diagnostics
    assert response.status_code == 200
    data = response.json()

    assert data["provider_status"]["open_meteo"]["status"] == "failed"
    assert data["provider_status"]["imd"]["status"] == "failed"
    assert len(data["errors"]) >= 2
    assert data["waves"]["height"] is None
    assert data["weather"]["temperature"] is None
