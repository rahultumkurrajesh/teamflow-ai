"""Smoke tests for the health endpoint.

These run without a database because /health does not touch it. The readiness
check and user-flow tests (which need Postgres) arrive in the testing stage,
where we spin up a throwaway database.
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok() -> None:
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_openapi_served() -> None:
    resp = client.get("/api/v1/openapi.json")
    assert resp.status_code == 200
    assert resp.json()["info"]["title"] == "TeamFlow AI"
