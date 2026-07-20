from apps.api.main import app
from fastapi.testclient import TestClient


def test_liveness_returns_ok() -> None:
    client = TestClient(app)

    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_liveness_sets_correlation_id_header() -> None:
    client = TestClient(app)

    response = client.get("/health/live")

    assert "X-Request-ID" in response.headers
