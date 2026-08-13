from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_health() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["service"] == "fotobox"

def test_index() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Fotobox" in response.text

