"""Backend smoke test for the health route."""

from fastapi.testclient import TestClient

from assetops_backend.main import app

client = TestClient(app)


def test_health_route_reports_service_liveness() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "assetops-backend"}


def test_no_site_or_simulator_routes_are_served_yet() -> None:
    """T001 must not serve Site, simulator, ingestion, or Findings surfaces."""
    served_paths = {route.path for route in app.routes if hasattr(route, "path")}

    assert served_paths & {"/api/sites", "/api/simulator", "/api/findings"} == set()
