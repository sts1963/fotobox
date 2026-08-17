from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_console_available() -> None:
    response = client.get(
        "/console"
    )

    assert response.status_code == 200

    assert "Servicekonsole" in (
        response.text
    )
