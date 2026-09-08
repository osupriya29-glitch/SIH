from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_returns_200():
    response = client.get("/health")
    assert response.status_code == 200


def test_health_check_response_shape():
    response = client.get("/health")
    body = response.json()
    assert body["status"] == "ok"
    assert "app_name" in body
    assert "version" in body
    assert "environment" in body


def test_docs_available():
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema_available():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "/health" in response.json()["paths"]


def test_404_returns_consistent_error_shape():
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    body = response.json()
    assert "error" in body
    assert "code" in body["error"]
    assert "message" in body["error"]
