"""Backend smoke test for the health route."""

from fastapi.testclient import TestClient
from route_inventory import served_paths

from assetops_backend.main import app

client = TestClient(app)


def test_health_route_reports_service_liveness() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "assetops-backend"}


def test_no_site_or_findings_routes_are_served_yet() -> None:
    """No Site, ingestion, or Findings surface exists in any flag state.

    Routes moved onto included routers in T003, which `app.routes` no longer
    reports directly, so this uses the loud route inventory helper. Simulator
    paths are covered by the gate tests, which assert them per flag state.
    """
    paths = served_paths(app)

    assert "/api/health" in paths, "route inventory must not be vacuous"
    assert paths & {"/api/sites", "/api/findings", "/api/ingestion"} == set()
