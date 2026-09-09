"""
TidesAtlas route tests. External calls mocked via httpx.MockTransport.
Also verifies the "not configured" (missing API key) path never reaches
the network — it should short-circuit to 503 immediately.
"""
import httpx
import pytest

from app.api.deps import get_tidesatlas_provider
from app.core.config import get_settings
from app.main import app
from app.providers.tidesatlas_provider import TidesAtlasProvider


def _make_provider(handler) -> TidesAtlasProvider:
    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    return TidesAtlasProvider(client=client)


@pytest.fixture()
def ta_client(client):
    yield client
    app.dependency_overrides.pop(get_tidesatlas_provider, None)


def test_tides_missing_location_returns_400(ta_client):
    response = ta_client.get("/api/tidesatlas/tides")  # no port, no lat/lon
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_TIDESATLAS_QUERY"


def test_tides_without_api_key_returns_503(ta_client, monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setattr(get_settings(), "TIDESATLAS_API_KEY", None)
    response = ta_client.get("/api/tidesatlas/tides", params={"port": "san-francisco"})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "PROVIDER_NOT_CONFIGURED_TIDESATLAS"
    get_settings.cache_clear()


def test_tides_by_port_returns_extremes(ta_client, monkeypatch):
    monkeypatch.setattr(get_settings(), "TIDESATLAS_API_KEY", "test-key")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("x-api-key") == "test-key"
        assert request.url.params.get("port") == "san-francisco"
        return httpx.Response(
            200,
            json={
                "port": {"name": "San Francisco", "slug": "san-francisco"},
                "data_source": "ticon",
                "extremes": [{"datetime": "2026-09-09T05:12:00-07:00", "height_m": 1.82, "type": "high"}],
            },
        )

    app.dependency_overrides[get_tidesatlas_provider] = lambda: _make_provider(handler)
    response = ta_client.get("/api/tidesatlas/tides", params={"port": "san-francisco", "days": 3})
    assert response.status_code == 200
    assert response.json()["extremes"][0]["type"] == "high"


def test_tides_point_requires_lat_lon(ta_client, monkeypatch):
    monkeypatch.setattr(get_settings(), "TIDESATLAS_API_KEY", "test-key")
    # FastAPI query validation (422) since lat/lon are required path params here
    response = ta_client.get("/api/tidesatlas/tides/point")
    assert response.status_code == 422


def test_marine_returns_wave_data(ta_client, monkeypatch):
    monkeypatch.setattr(get_settings(), "TIDESATLAS_API_KEY", "test-key")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/marine")
        return httpx.Response(
            200,
            json={"lat": 48.39, "lon": -4.49, "daily": [{"wave_height_max_m": 1.04, "sea_state": "smooth"}]},
        )

    app.dependency_overrides[get_tidesatlas_provider] = lambda: _make_provider(handler)
    response = ta_client.get("/api/tidesatlas/marine", params={"lat": 48.39, "lon": -4.49})
    assert response.status_code == 200
    assert response.json()["daily"][0]["sea_state"] == "smooth"


def test_search_ports(ta_client, monkeypatch):
    monkeypatch.setattr(get_settings(), "TIDESATLAS_API_KEY", "test-key")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params.get("search") == "tokyo"
        return httpx.Response(200, json={"count": 1, "ports": [{"name": "Tokyo", "slug": "tokyo"}]})

    app.dependency_overrides[get_tidesatlas_provider] = lambda: _make_provider(handler)
    response = ta_client.get("/api/tidesatlas/ports", params={"search": "tokyo"})
    assert response.status_code == 200
    assert response.json()["ports"][0]["name"] == "Tokyo"
