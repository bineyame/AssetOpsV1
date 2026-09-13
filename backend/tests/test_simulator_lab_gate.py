"""Serving-boundary tests for the `simulator_lab.enabled` gate.

These tests issue real requests against apps built in both flag states. They
deliberately do not check navigation or rendering: the failure mode this guards
is simulator truth or execution staying reachable by direct URL after the
feature is "disabled".
"""

from fastapi.testclient import TestClient
from route_inventory import served_paths

from assetops_backend.config import FeatureFlags
from assetops_backend.main import create_app

DISABLED = FeatureFlags(simulator_lab_enabled=False)
ENABLED = FeatureFlags(simulator_lab_enabled=True)

SIMULATOR_LAB_STATUS_PATH = "/api/simulator-lab/status"
SITE_TEMPLATES_PATH = "/api/simulator-lab/site-templates"
SITE_TEMPLATE_DETAIL_PATH = "/api/simulator-lab/site-templates/{template_id}"

# Every Lab-only path the gate must serve when open and hide when closed. T005
# added the two template paths; the inventory assertions below are extended to
# name them rather than relaxed to tolerate them.
SIMULATOR_LAB_SERVED_PATHS = {
    SIMULATOR_LAB_STATUS_PATH,
    SITE_TEMPLATES_PATH,
    SITE_TEMPLATE_DETAIL_PATH,
}

# Paths an operator, a script, or a stale bookmark could plausibly aim at the
# simulator. None of them may be served while the gate is closed.
SIMULATOR_LAB_DIRECT_PATHS = [
    "/api/simulator-lab",
    "/api/simulator-lab/",
    SIMULATOR_LAB_STATUS_PATH,
    SITE_TEMPLATES_PATH,
    "/api/simulator-lab/site-templates/hybrid-mini-grid-100kw",
    "/api/simulator-lab/world",
    "/api/simulator-lab/truth",
    "/api/simulator",
    "/api/simulator/status",
]

# Execution and truth-overlay paths. No slice has implemented these, so they
# must be unserved in BOTH flag states; enabling the gate must not conjure run
# behavior into existence.
EXECUTION_PATHS = [
    "/api/simulator-lab/runs",
    "/api/simulator-lab/runs/run-1",
    "/api/simulator-lab/runs/run-1/truth",
    "/api/simulator-lab/runs/run-1/rerun",
    "/api/simulator-lab/execute",
    "/api/simulator-lab/staging",
    "/api/runs",
    "/api/ingestion",
]


def paths_for(flags: FeatureFlags) -> set[str]:
    return served_paths(create_app(flags))


class TestRouteInventoryIsNotVacuous:
    """Guard the guard: the structural assertions below must be able to fail."""

    def test_inventory_sees_both_the_health_and_simulator_lab_routes(self) -> None:
        served = paths_for(ENABLED)

        assert "/api/health" in served
        assert SIMULATOR_LAB_SERVED_PATHS <= served


class TestGateDisabled:
    def test_simulator_lab_paths_are_not_served(self) -> None:
        client = TestClient(create_app(DISABLED))

        for path in SIMULATOR_LAB_DIRECT_PATHS:
            response = client.get(path)
            assert response.status_code == 404, f"{path} was served while disabled"

    def test_simulator_lab_paths_reject_non_get_methods(self) -> None:
        """A closed gate must not leave a write verb reachable on a simulator path."""
        client = TestClient(create_app(DISABLED))

        for path in (
            SIMULATOR_LAB_STATUS_PATH,
            SITE_TEMPLATES_PATH,
            "/api/simulator-lab/site-templates/hybrid-mini-grid-100kw",
            "/api/simulator-lab/execute",
        ):
            for request in (client.post, client.put, client.patch, client.delete):
                response = request(path)
                assert response.status_code == 404, f"{path} accepted a write verb"

    def test_no_route_mentioning_the_simulator_is_registered(self) -> None:
        """Structural check: a future ungated simulator router fails here."""
        assert [path for path in paths_for(DISABLED) if "simulator" in path] == []

    def test_openapi_does_not_advertise_simulator_surfaces(self) -> None:
        """The served API description must not document an unserved surface."""
        client = TestClient(create_app(DISABLED))
        schema = client.get("/openapi.json").json()

        assert [path for path in schema["paths"] if "simulator" in path] == []

    def test_operator_and_product_surfaces_still_work(self) -> None:
        """The gate controls simulator surfaces only."""
        client = TestClient(create_app(DISABLED))
        response = client.get("/api/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok", "service": "assetops-backend"}


class TestGateEnabled:
    def test_simulator_lab_status_is_served(self) -> None:
        client = TestClient(create_app(ENABLED))
        response = client.get(SIMULATOR_LAB_STATUS_PATH)

        assert response.status_code == 200
        assert response.json() == {
            "simulator_lab_enabled": True,
            "run_execution": "not_implemented",
            "truth_overlays": "not_implemented",
        }

    def test_operator_and_product_surfaces_still_work(self) -> None:
        client = TestClient(create_app(ENABLED))

        assert client.get("/api/health").status_code == 200

    def test_enabling_the_gate_adds_only_the_simulator_lab_surface(self) -> None:
        added = paths_for(ENABLED) - paths_for(DISABLED)

        assert added == SIMULATOR_LAB_SERVED_PATHS

    def test_no_execution_surface_exists_yet(self) -> None:
        """T003 scope limit: the enabled shell has no run behavior."""
        client = TestClient(create_app(ENABLED))

        for path in EXECUTION_PATHS:
            assert client.get(path).status_code == 404, f"{path} served run behavior"


class TestExecutionPathsInBothStates:
    def test_execution_paths_are_unserved_regardless_of_the_flag(self) -> None:
        for flags in (DISABLED, ENABLED):
            client = TestClient(create_app(flags))
            for path in EXECUTION_PATHS:
                assert client.get(path).status_code == 404


class TestDefaultApp:
    def test_the_module_level_app_is_built_from_the_repository_config(self) -> None:
        """The shipped app must reflect the file, not a hardcoded default."""
        from assetops_backend.config import load_feature_flags
        from assetops_backend.main import app

        expected = load_feature_flags().simulator_lab_enabled
        simulator_paths = [
            path for path in served_paths(app) if "simulator" in path
        ]

        assert bool(simulator_paths) is expected
