"""Backend smoke test for the health route."""

from fastapi.testclient import TestClient
from route_inventory import served_paths

from assetops_backend.main import app

client = TestClient(app)


def test_health_route_reports_service_liveness() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "assetops-backend"}


def test_the_sites_index_is_served_and_no_evidence_surface_is() -> None:
    """The operator Sites API exists; ingestion and Findings still do not.

    T006 makes `/api/sites` a real operator capability and T007 adds the one
    Site addressed by `site_id`, so this no longer asserts either absence. The
    assertions it replaces them with are stricter about what neither slice
    added: no ingestion, no Findings, and exactly one per-Site path rather
    than a family of them. Simulator paths are covered by the gate tests,
    which assert them per flag state; the write verbs are covered below.

    Routes moved onto included routers in T003, which `app.routes` no longer
    reports directly, so this uses the loud route inventory helper.
    """
    paths = served_paths(app)

    assert "/api/health" in paths, "route inventory must not be vacuous"
    assert "/api/sites" in paths
    assert paths & {"/api/findings", "/api/ingestion", "/api/evidence"} == set()
    assert [path for path in paths if "{site_id}" in path] == [
        "/api/sites/{site_id}"
    ]


def test_the_per_site_route_reads_and_nothing_more() -> None:
    """One Site is addressed by `site_id`, and only for reading."""
    schema = client.get("/openapi.json").json()

    assert "/api/sites/{site_id}" in schema["paths"], "the check must not be vacuous"
    assert set(schema["paths"]["/api/sites/{site_id}"]) == {"get"}


def test_the_sites_api_offers_no_write_verb() -> None:
    """Creation is a gated Lab route; the operator Sites API only reads."""
    schema = client.get("/openapi.json").json()

    assert "/api/sites" in schema["paths"], "the schema check must not be vacuous"
    assert set(schema["paths"]["/api/sites"]) == {"get"}
