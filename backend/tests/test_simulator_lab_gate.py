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
CREATE_SITE_PATH = "/api/simulator-lab/sites"
SCENARIOS_PATH = "/api/simulator-lab/scenarios"
SCENARIO_DETAIL_PATH = "/api/simulator-lab/scenarios/{scenario_id}"
RUN_PROFILES_PATH = "/api/simulator-lab/run-profiles"
CREATE_RUN_PATH = "/api/simulator-lab/runs"
RUN_DETAIL_PATH = "/api/simulator-lab/runs/{run_id}"

# Every Lab-only path the gate must serve when open and hide when closed. T005
# added the two template paths, T006 added the create path, T017 added the
# two scenario paths, and T019 added run setup and the profiles it selects
# from; the inventory assertions below are extended to name them rather than
# relaxed to tolerate them.
SIMULATOR_LAB_SERVED_PATHS = {
    SIMULATOR_LAB_STATUS_PATH,
    SITE_TEMPLATES_PATH,
    SITE_TEMPLATE_DETAIL_PATH,
    CREATE_SITE_PATH,
    SCENARIOS_PATH,
    SCENARIO_DETAIL_PATH,
    RUN_PROFILES_PATH,
    CREATE_RUN_PATH,
    RUN_DETAIL_PATH,
}

# Paths an operator, a script, or a stale bookmark could plausibly aim at the
# simulator. None of them may be served while the gate is closed.
SIMULATOR_LAB_DIRECT_PATHS = [
    "/api/simulator-lab",
    "/api/simulator-lab/",
    SIMULATOR_LAB_STATUS_PATH,
    SITE_TEMPLATES_PATH,
    "/api/simulator-lab/site-templates/hybrid-mini-grid-100kw",
    CREATE_SITE_PATH,
    SCENARIOS_PATH,
    "/api/simulator-lab/scenarios/fuel-loss-event",
    RUN_PROFILES_PATH,
    CREATE_RUN_PATH,
    "/api/simulator-lab/world",
    "/api/simulator-lab/truth",
    "/api/simulator",
    "/api/simulator/status",
]

# Execution and truth-overlay paths. No slice has implemented these, so they
# must be unserved in BOTH flag states; enabling the gate must not conjure run
# behavior into existence.
#
# `/api/simulator-lab/runs` left this list in T019, which made it a real
# path, and T020 added listing and reading one. What has never been served,
# and is what this list is for, is EXECUTION: a run cannot be started,
# stepped, rerun, or asked for truth. The class at the bottom of this file
# asserts each of those separately rather than letting the arrival of a read
# route relax the rule for the rest.
EXECUTION_PATHS = [
    "/api/simulator-lab/runs/run-1/truth",
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
            CREATE_SITE_PATH,
            RUN_PROFILES_PATH,
            CREATE_RUN_PATH,
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

    def test_the_operator_sites_api_is_served_with_the_gate_closed(self) -> None:
        """Sites are product objects. The gate covers surfaces, not stores."""
        client = TestClient(create_app(DISABLED))

        assert client.get("/api/sites").status_code == 200


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


class TestRunSetupIsSetupAndNothingElse:
    """T019 serves one run path, and it does one thing.

    The scope limit is that run setup creates a Draft. Listing runs, reading
    one, and every execution verb belong to later slices, so the assertions
    are per verb and per path rather than "the runs path is served" - which
    would have been satisfied by a build that also listed and executed them.
    """

    def test_the_setup_path_accepts_a_setup_request_when_the_gate_is_open(
        self,
    ) -> None:
        client = TestClient(create_app(ENABLED))

        # An empty body is refused as a malformed request, which is the point:
        # the route exists and answers, rather than being absent.
        response = client.post(CREATE_RUN_PATH, json={})

        assert response.status_code == 422
        assert response.json()["detail"]["run_created"] is False

    def test_the_run_paths_read_and_create_and_do_nothing_else(self) -> None:
        """T020 adds listing and reading. Nothing else arrived with them.

        The inventory and the detail route are reads, and the only write is
        still setup. A run cannot be started, stepped, rerun or deleted
        through any of these, and the verbs are asserted rather than assumed
        because a router that grew one would serve it silently.
        """
        client = TestClient(create_app(ENABLED))

        assert client.get(CREATE_RUN_PATH).status_code == 200
        # A well-formed identity that is not persisted, and a malformed one:
        # both are not found, and neither is another run.
        assert client.get(f"{CREATE_RUN_PATH}/run-{'0' * 32}").status_code == 404
        assert client.get(f"{CREATE_RUN_PATH}/run-1").status_code == 404

        for request in (client.put, client.patch, client.delete):
            assert request(f"{CREATE_RUN_PATH}/run-1").status_code == 405
        assert client.post(f"{CREATE_RUN_PATH}/run-1").status_code == 405

    def test_no_run_path_is_served_when_the_gate_is_closed(self) -> None:
        client = TestClient(create_app(DISABLED))

        assert client.post(CREATE_RUN_PATH, json={}).status_code == 404
        assert client.get(CREATE_RUN_PATH).status_code == 404
        assert client.get(f"{CREATE_RUN_PATH}/run-1").status_code == 404
        assert client.get(RUN_PROFILES_PATH).status_code == 404

    def test_a_closed_gate_never_touches_the_run_store(self) -> None:
        """The gate decides whether a surface is served, not what a store has.

        A closed build must not open the directory runs would be written to in
        order to discover that it serves no run route.
        """

        class Exploding:
            def create_run(self, record: object) -> object:
                raise AssertionError("the closed gate reached the run store")

            def get_run(self, run_id: str) -> object:
                raise AssertionError("the closed gate reached the run store")

            def list_runs(self) -> object:
                raise AssertionError("the closed gate reached the run store")

        closed = TestClient(create_app(DISABLED, run_repository=Exploding()))

        assert closed.post(CREATE_RUN_PATH, json={}).status_code == 404


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
