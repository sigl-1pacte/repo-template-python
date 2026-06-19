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


def test_ci_languages_lists_supported_and_planned_languages():
    response = client.get("/ci/languages")

    assert response.status_code == 200
    assert response.json() == {
        "supported": ["python"],
        "planned": ["node", "go", "rust", "java"],
    }


def test_ci_preview_generates_python_workflow_only():
    response = client.post(
        "/ci/generate/preview",
        json={
            "project": "my-project",
            "apps": [
                {
                    "name": "app1",
                    "path": "apps/app1",
                    "language": "python",
                    "python_version": "3.12",
                },
                {
                    "name": "app2",
                    "path": "apps/app2",
                    "language": "node",
                    "node_version": 20,
                    "package_manager": "pnpm",
                },
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "preview"
    assert body["warnings"] == [
        "Warning: language 'node' is not implemented yet. Skipping app 'app2'."
    ]
    assert body["generated_files"] == [
        ".github/dependabot.yml",
        ".github/workflows/ci-app1.yml",
        ".github/workflows/ci.yml",
    ]
    assert ".github/workflows/ci-app2.yml" not in body["files"]
    assert "app2:" not in body["files"][".github/workflows/ci.yml"]


def test_ci_preview_returns_validation_error():
    response = client.post(
        "/ci/generate/preview",
        json={
            "apps": [
                {
                    "name": "app1",
                    "path": "apps/app1",
                },
            ],
        },
    )

    assert response.status_code == 422
    assert "language" in response.json()["detail"]
