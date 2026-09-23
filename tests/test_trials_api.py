from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_trial_import_rejects_invalid_nct_id() -> None:
    response = client.get("/v1/trials/clinicaltrials-gov/not-an-nct")

    assert response.status_code == 422
    assert "NCT ID must match" in response.json()["detail"]
