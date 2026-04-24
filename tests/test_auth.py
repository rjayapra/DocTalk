"""Tests for Entra ID auth middleware in the FastAPI API."""
import unittest
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app, raise_server_exceptions=False)


class TestHealthNoAuth(unittest.TestCase):
    """The /health endpoint must be publicly accessible (no auth dependency)."""

    def test_health_no_auth_required(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "healthy"
        assert "version" in body


class TestAuthEnforced(unittest.TestCase):
    """When ENTRA_APP_ID is set, endpoints must reject unauthenticated requests."""

    @patch("src.api.auth.Config")
    def test_endpoint_returns_401_without_token(self, mock_config):
        mock_config.ENTRA_APP_ID = "fake-app-id"
        mock_config.ENTRA_TENANT_ID = "fake-tenant-id"

        # POST /generate should require auth
        resp = client.post("/generate", json={"url": "https://example.com"})
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"

        # GET /jobs should require auth
        resp = client.get("/jobs")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"

        # GET /jobs/{id} should require auth
        resp = client.get("/jobs/some-id")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"


class TestAuthBypassed(unittest.TestCase):
    """When ENTRA_APP_ID is empty, auth is skipped (local dev mode)."""

    @patch("src.api.auth.Config")
    def test_auth_bypassed_when_no_entra_config(self, mock_config):
        mock_config.ENTRA_APP_ID = ""
        mock_config.ENTRA_TENANT_ID = ""

        # /health always works
        resp = client.get("/health")
        assert resp.status_code == 200

        # /jobs should NOT return 401 when auth is disabled
        # (it may fail for other reasons like missing Azure Storage, but not 401)
        resp = client.get("/jobs")
        assert resp.status_code != 401, "Auth should be bypassed when ENTRA_APP_ID is empty"


if __name__ == "__main__":
    unittest.main()
