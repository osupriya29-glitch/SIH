"""
NOAA route tests. All external calls mocked via httpx.MockTransport.
"""
import httpx
import pytest

from app.api.deps import get_noaa_coops_provider, get_noaa_ndbc_provider, get_noaa_weather_provider
from app.main import app
from app.providers.noaa_coops_provider import NOAACoOpsProvider
from app.providers.noaa_ndbc_provider import NOAANDBCProvider
from app.providers.noaa_weather_provider import NOAAWeatherProvider


def _client_with(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


@pytest.fixture()
def noaa_client(client):
    yield client
    app.dependency_overrides.pop(get_noaa_coops_provider, None)
    app.dependency_overrides.pop(get_noaa_ndbc_provider, None)
    app.dependency_overrides.pop(get_noaa_weather_provider, None)


# --- CO-OPS ---

def test_coops_water_level_requires_datum(noaa_client):
    response = noaa_client.get(
        "/api/noaa/coops",
        params={"station": "9414290", "product": "water_level", "date": "today"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_COOPS_QUERY"


def test_coops_water_level_with_datum_succeeds(noaa_client):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params.get("station") == "9414290"
        assert request.url.params.get("datum") == "MLLW"
        return httpx.Response(
            200,
            json={"data": [{"t": "2026-09-09 00:00", "v": "1.234", "s": "0.010", "f": "0,0,0,0", "q": "p"}]},
        )

    app.dependency_overrides[get_noaa_coops_provider] = lambda: NOAACoOpsProvider(_client_with(handler))
    response = noaa_client.get(
        "/api/noaa/coops",
        params={"station": "9414290", "product": "water_level", "date": "today", "datum": "MLLW"},
    )
    assert response.status_code == 200
    assert response.json()["data"][0]["v"] == "1.234"


def test_coops_missing_date_params_returns_400(noaa_client):
    response = noaa_client.get(
        "/api/noaa/coops",
        params={"station": "8724580", "product": "wind"},  # no date/range/begin/end
    )
    assert response.status_code == 400


# --- NDBC ---

def test_ndbc_parses_stdmet_text(noaa_client):
    sample = (
        "#YY  MM DD hh mm WDIR WSPD GST  WVHT   DPD   APD MWD   PRES  ATMP  WTMP  DEWP  VIS PTDY  TIDE\n"
        "#yr  mo dy hr mn degT  m/s  m/s     m   sec   sec degT   hPa  degC  degC  degC  nmi   hPa    ft\n"
        "2026 09 09 00 00  180  5.0  6.0   1.2   7.0   6.0 175 1013.0  24.5  25.0    MM   MM   MM    MM\n"
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/46042.txt")
        return httpx.Response(200, text=sample)

    app.dependency_overrides[get_noaa_ndbc_provider] = lambda: NOAANDBCProvider(_client_with(handler))
    response = noaa_client.get("/api/noaa/ndbc/46042")
    assert response.status_code == 200
    body = response.json()
    obs = body["observations"][0]
    assert obs["WVHT"] == 1.2
    assert obs["VIS"] is None  # "MM" -> null, never fabricated
    assert obs["timestamp"] == "2026-09-09T00:00:00+00:00"


# --- NWS ---

def test_nws_forecast_chains_points_then_forecast(noaa_client):
    def handler(request: httpx.Request) -> httpx.Response:
        assert "User-Agent" in request.headers
        if "/points/" in str(request.url):
            return httpx.Response(
                200,
                json={"properties": {"forecast": "https://api.weather.gov/gridpoints/TOP/31,80/forecast"}},
            )
        return httpx.Response(200, json={"properties": {"periods": [{"name": "Tonight", "temperature": 60}]}})

    app.dependency_overrides[get_noaa_weather_provider] = lambda: NOAAWeatherProvider(_client_with(handler))
    response = noaa_client.get("/api/noaa/weather/forecast", params={"latitude": 39.7, "longitude": -97.1})
    assert response.status_code == 200
    assert response.json()["properties"]["periods"][0]["name"] == "Tonight"
