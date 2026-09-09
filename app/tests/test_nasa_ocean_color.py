"""
NASA Ocean Color route tests. file_search calls are mocked via
httpx.MockTransport. The point-value endpoint has no external call to
mock — it should always 501 without ever reaching the network.
"""
import httpx
import pytest

from app.api.deps import get_nasa_ocean_color_provider
from app.main import app
from app.providers.nasa_ocean_color_provider import NASAOceanColorProvider


def _make_provider(handler) -> NASAOceanColorProvider:
    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    return NASAOceanColorProvider(client=client)


@pytest.fixture()
def noc_client(client):
    yield client
    app.dependency_overrides.pop(get_nasa_ocean_color_provider, None)


def test_search_files_posts_form_data(noc_client):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        body = request.content.decode()
        assert "sensor_id=7" in body
        assert "dtype=L3m" in body
        return httpx.Response(
            200,
            json=[
                {
                    "filename": "AQUA_MODIS.20260901.L3m.DAY.CHL.chlor_a.4km.nc",
                    "url": "https://oceandata.sci.gsfc.nasa.gov/cgi/getfile/AQUA_MODIS.20260901.L3m.DAY.CHL.chlor_a.4km.nc",
                }
            ],
        )

    app.dependency_overrides[get_nasa_ocean_color_provider] = lambda: _make_provider(handler)
    response = noc_client.get(
        "/api/nasa-ocean-color/files",
        params={
            "sensor_id": 7,
            "dtype": "L3m",
            "sdate": "2026-09-01 00:00:00",
            "edate": "2026-09-01 23:59:59",
            "suite_id": "CHL",
            "prod_id": "chlor_a",
        },
    )
    assert response.status_code == 200
    assert "AQUA_MODIS" in response.json()[0]["filename"]


def test_search_files_missing_date_bound_returns_400(noc_client):
    response = noc_client.get(
        "/api/nasa-ocean-color/files",
        params={"sensor_id": 7, "dtype": "L3m"},  # no sdate/edate/backdays
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_OCEAN_COLOR_QUERY"


def test_search_files_missing_sensor_returns_400(noc_client):
    response = noc_client.get(
        "/api/nasa-ocean-color/files",
        params={"dtype": "L3m", "backdays": 5},
    )
    assert response.status_code == 400


def test_chlorophyll_point_returns_501_not_implemented(noc_client):
    response = noc_client.get(
        "/api/nasa-ocean-color/chlorophyll",
        params={"latitude": 19.07, "longitude": 72.87, "date": "2026-09-01"},
    )
    assert response.status_code == 501
    body = response.json()
    assert body["error"]["code"] == "NOT_IMPLEMENTED_PENDING"
    assert "not implemented" in body["error"]["message"].lower()
