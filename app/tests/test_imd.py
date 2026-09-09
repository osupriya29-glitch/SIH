"""
IMD route tests. All external calls are mocked via httpx.MockTransport —
per the project's testing rule, no real API calls happen in unit tests.

Fixture data below mirrors the *shape* of IMD's documented sample
responses (see app/providers/imd_provider.py docstrings / IMD's official
API reference) — it is not live data.
"""
import httpx
import pytest

from app.api.deps import get_imd_provider
from app.main import app
from app.providers.base_provider import ProviderError
from app.providers.imd_provider import IMDProvider


def _make_provider(handler) -> IMDProvider:
    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    return IMDProvider(client=client)


@pytest.fixture()
def imd_client(client):
    """Reuses the `client` fixture from conftest.py (DB already overridden);
    each test further overrides get_imd_provider with its own mock handler."""
    yield client
    app.dependency_overrides.pop(get_imd_provider, None)


def test_get_weather_returns_provider_data(imd_client):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/current_wx"
        assert request.url.params.get("id") == "42182"
        return httpx.Response(
            200,
            json={
                "Station Id": "42182",
                "Station": "NEW DELHI/SAFDARJUNG",
                "Temperature": "32.4",
                "Humidity": "48",
            },
        )

    app.dependency_overrides[get_imd_provider] = lambda: _make_provider(handler)
    response = imd_client.get("/api/imd/weather", params={"station_id": "42182"})
    assert response.status_code == 200
    assert response.json()["Station Id"] == "42182"


def test_get_coastal_bulletin_returns_list(imd_client):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/coastalbulletin"
        return httpx.Response(
            200,
            json=[{"Id": "108", "Layer": "South Tamilnadu coast", "Sea Condition": "Smooth to Slight"}],
        )

    app.dependency_overrides[get_imd_provider] = lambda: _make_provider(handler)
    response = imd_client.get("/api/imd/coastal-bulletin")
    assert response.status_code == 200
    assert response.json()[0]["Layer"] == "South Tamilnadu coast"


def test_get_nowcast_district_by_default(imd_client):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/districtnowcast"
        return httpx.Response(200, json=[{"Station": "Adilabad", "message": "No warning"}])

    app.dependency_overrides[get_imd_provider] = lambda: _make_provider(handler)
    response = imd_client.get("/api/imd/nowcast")
    assert response.status_code == 200


def test_get_nowcast_station_mode(imd_client):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/stationnowcast"
        assert request.url.params.get("id") == "Adilabad"
        return httpx.Response(200, json=[{"Station": "Adilabad"}])

    app.dependency_overrides[get_imd_provider] = lambda: _make_provider(handler)
    response = imd_client.get("/api/imd/nowcast", params={"by": "station", "id": "Adilabad"})
    assert response.status_code == 200


def test_provider_timeout_returns_504(imd_client):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out", request=request)

    app.dependency_overrides[get_imd_provider] = lambda: _make_provider(handler)
    response = imd_client.get("/api/imd/weather")
    assert response.status_code == 504
    body = response.json()
    assert body["error"]["code"] == "PROVIDER_ERROR_IMD"


def test_provider_upstream_error_returns_502(imd_client):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="upstream error")

    app.dependency_overrides[get_imd_provider] = lambda: _make_provider(handler)
    response = imd_client.get("/api/imd/sea-area-bulletin")
    assert response.status_code == 502
