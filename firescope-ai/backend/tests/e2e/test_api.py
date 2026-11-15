from fastapi.testclient import TestClient
from firescope.presentation.api.main import app

def test_health() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["stage"] == "data_foundation"
