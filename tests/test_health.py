from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "vector12-api"


def test_root_endpoint() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "service": "vector12-api",
        "status": "running",
    }


def test_ready_returns_503_without_supabase(monkeypatch) -> None:
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_PUBLISHABLE_KEY", raising=False)
    get_settings.cache_clear()

    from app import main

    main.settings = get_settings()

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["detail"] == "Supabase configuration is missing"
