from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_backgrounds_page_available() -> None:
    response = client.get(
        "/backgrounds"
    )

    assert response.status_code == 200

    assert (
        "Fotobox Hintergründe"
        in response.text
    )
