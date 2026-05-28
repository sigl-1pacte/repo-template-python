from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_content_type():
    response = client.get("/health")
    assert "application/json" in response.headers["content-type"]


def test_index_returns_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_index_contains_service_name():
    response = client.get("/")
    assert "my-service" in response.text


def test_index_contains_health_link():
    response = client.get("/")
    assert "/health" in response.text


def test_docs_available():
    response = client.get("/docs")
    assert response.status_code == 200


def test_redoc_available():
    response = client.get("/redoc")
    assert response.status_code == 200


def test_unknown_route_returns_404():
    response = client.get("/unknown")
    assert response.status_code == 404
