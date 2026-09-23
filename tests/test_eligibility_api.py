from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_schema_endpoint_exposes_v1_schema() -> None:
    response = client.get("/v1/eligibility/schema")
    assert response.status_code == 200
    assert response.json()["schema_version"] == "eligibility-v1"
