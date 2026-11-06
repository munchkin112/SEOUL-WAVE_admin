from fastapi.testclient import TestClient
from app.main import app
from app.database import get_database
from app import main


def test_admin_requires_configured_server_key(monkeypatch):
    monkeypatch.delenv("ADMIN_API_KEY", raising=False)
    with TestClient(app) as client:
        assert client.get("/api/v1/admin/dashboard/summary").status_code == 503


def test_admin_rejects_missing_or_wrong_key_and_accepts_proxy_key(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "test-server-only-key")
    app.dependency_overrides[get_database] = lambda: object()
    monkeypatch.setattr(main.repository, "dashboard_summary", lambda connection, days: {"total": 3})
    try:
        with TestClient(app) as client:
            path = "/api/v1/admin/dashboard/summary"
            assert client.get(path).status_code == 401
            assert client.get(path, headers={"X-Admin-Key": "wrong"}).status_code == 401
            assert client.get(path, headers={"X-Admin-Key": "test-server-only-key"}).json() == {"total": 3}
    finally:
        app.dependency_overrides.clear()
