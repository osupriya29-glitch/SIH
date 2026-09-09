"""
Open-Meteo Marine route tests. All external calls are mocked via
httpx.MockTransport — no real network calls in unit tests.

Response fixtures mirror the *shape* of Open-Meteo's documented sample
response (see open-meteo.com/en/docs/marine-weather-api) — not live data.
"""
import httpx
import pytest

from app.api.deps import get_open_meteo_provider
from app.main import app
from app.providers.open_meteo_provider import OpenMeteoMarineProvider


def _make_provider(handler) -> OpenMeteoMarineProvider:
    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    return OpenMeteoMarineProvider(client=client)


@pytest.fixture()
def om_client(client):
    yield client
    app.dependency_overrides.pop(get_open_meteo_provider, None)


def test_get_marine_forecast_hourly(om_client):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params.get("latitude") == "52.52"
        assert request.url.params.get("longitude") == "13.419"
        assert request.url.params.get("hourly") == "wave_height,wave_period"
        return httpx.Response(
            200,
            json={
                "latitude": 52.52,
                "longitude": 13.419,
                "timezone": "GMT",
                "hourly": {
                    "time": ["2026-09-09T00:00", "2026-09-09T01:00"],
                    "wave_height": [1.2, 1.4],
                    "wave_period": [6.1, 6.3],
                },
                "hourly_units": {"wave_height": "m", "wave_period": "s"},
            },
        )

    app.dependency_overrides[get_open_meteo_provider] = lambda: _make_provider(handler)
    response = om_client.get(
        "/api/open-meteo/marine",
        params={"latitude": 52.52, "longitude": 13.419, "hourly": "wave_height,wave_period"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["hourly"]["wave_height"] == [1.2, 1.4]
    assert body["hourly_units"]["wave_height"] == "m"


def test_get_marine_forecast_daily_adds_default_timezone(om_client):
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["timezone"] = request.url.params.get("timezone")
        return httpx.Response(200, json={"daily": {"time": ["2026-09-09"], "wave_height_max": [2.1]}})

    app.dependency_overrides[get_open_meteo_provider] = lambda: _make_provider(handler)
    response = om_client.get(
        "/api/open-meteo/marine",
        params={"latitude": 19.07, "longitude": 72.87, "daily": "wave_height_max"},
    )
    assert response.status_code == 200
    # Open-Meteo requires a timezone whenever `daily` is used — provider fills a default.
    assert captured["timezone"] == "auto"


def test_invalid_variable_returns_400(om_client):
    response = om_client.get(
        "/api/open-meteo/marine",
        params={"latitude": 1, "longitude": 1, "hourly": "not_a_real_variable"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_MARINE_VARIABLE"


def test_upstream_error_returns_502(om_client):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": True, "reason": "bad params"})

    app.dependency_overrides[get_open_meteo_provider] = lambda: _make_provider(handler)
    response = om_client.get(
        "/api/open-meteo/marine",
        params={"latitude": 1, "longitude": 1, "hourly": "wave_height"},
    )
    assert response.status_code == 502
    assert response.json()["error"]["code"] == "PROVIDER_ERROR_OPEN_METEO_MARINE"
