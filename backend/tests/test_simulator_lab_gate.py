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
RUN_EXECUTION_PATH = "/api/simulator-lab/runs/{run_id}/execution"
RUN_EXECUTION_START_PATH = "/api/simulator-lab/runs/{run_id}/execution/start"
RUN_EXECUTION_STEP_PATH = "/api/simulator-lab/runs/{run_id}/execution/step"
RUN_EXECUTION_END_PATH = (
    "/api/simulator-lab/runs/{run_id}/execution/run-to-end"
)

# Every Lab-only path the gate must serve when open and hide when closed. T005
# added the two template paths, T006 added the create path, T017 added the
# two scenario paths, and T019 added run setup and the profiles it selects
# from; the inventory assertions below are extended to name them rather than
# relaxed to tolerate them.
#
# T022 adds the four execution paths and they are the first ones that DO
# something to a run. They are named here rather than tolerated for the same
# reason every other addition was, and the tests below say what each flag state
# does with them: closed, none of the four exists; open, all four exist and a
# build with no execution port composed behind them says so in a typed refusal
# rather than by not serving them. Whether a port is composed is not the gate's
# question, so it may not change the route set.
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
    RUN_EXECUTION_PATH,
    RUN_EXECUTION_START_PATH,
    RUN_EXECUTION_STEP_PATH,
    RUN_EXECUTION_END_PATH,
}

# The same four, with a concrete run identity, for the request-level assertions.
RUN_EXECUTION_REQUEST_PATHS = [
    "/api/simulator-lab/runs/run-1/execution",
    "/api/simulator-lab/runs/run-1/execution/start",
    "/api/simulator-lab/runs/run-1/execution/step",
    "/api/simulator-lab/runs/run-1/execution/run-to-end",
]

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
    *RUN_EXECUTION_REQUEST_PATHS,
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
        # `run_execution` stopped being "not_implemented" in T022, and the two
        # keys are two facts rather than one. `served` says this build serves the
        # execution surface; `run_execution_composed` says whether a kernel is
        # wired behind it, which only the composition leaf can do. A single flag
        # would make a build that serves the controls and cannot execute
        # indistinguishable from one that does neither.
        assert response.json() == {
            "simulator_lab_enabled": True,
            "run_execution": "served",
            "run_execution_composed": False,
            "truth_overlays": "not_implemented",
        }

    def test_operator_and_product_surfaces_still_work(self) -> None:
        client = TestClient(create_app(ENABLED))

        assert client.get("/api/health").status_code == 200

    def test_enabling_the_gate_adds_only_the_simulator_lab_surface(self) -> None:
        added = paths_for(ENABLED) - paths_for(DISABLED)

        assert added == SIMULATOR_LAB_SERVED_PATHS

    def test_the_execution_surface_the_lab_does_not_serve_stays_unserved(
        self,
    ) -> None:
        """T022 serves four execution paths, and these are not among them.

        A run can be started, stepped and run to the end. It cannot be rerun, it
        cannot be asked for truth on its own path, nothing is staged, and no
        operator-facing run or ingestion path exists. The arrival of execution
        did not relax this: the list is the same one, and what left it is named
        in the comment above it.
        """
        client = TestClient(create_app(ENABLED))

        assert EXECUTION_PATHS, "the unserved-path list is empty"
        for path in EXECUTION_PATHS:
            assert client.get(path).status_code == 404, f"{path} served run behavior"

    def test_the_four_execution_paths_are_served_when_the_gate_is_open(
        self,
    ) -> None:
        """The floor under every absence claim in this file.

        Each assertion elsewhere iterates paths or controls, and a build serving
        none of them would satisfy all of them. So this establishes that the
        enabled surface really carries the four, before anything asserts that the
        closed one does not.
        """
        served = paths_for(ENABLED)

        for path in (
            RUN_EXECUTION_PATH,
            RUN_EXECUTION_START_PATH,
            RUN_EXECUTION_STEP_PATH,
            RUN_EXECUTION_END_PATH,
        ):
            assert path in served, f"{path} is not served with the gate open"

    def test_an_uncomposed_execution_port_is_a_typed_refusal_not_an_absence(
        self,
    ) -> None:
        """What `assetops_backend.main:app` serves, and why it is honest.

        Only `host/` may import a kernel and nothing may import `host/`, so a
        build composed from this package alone has no execution port. It still
        SERVES the four paths, because whether a port is composed is not the
        gate's question and a route set that varied with it would make the gate's
        own comparison a comparison between three states.

        What it answers is a typed refusal naming the missing composition, so a
        reader meets the reason rather than a 404 that would say the capability
        does not exist.
        """
        client = TestClient(create_app(ENABLED))

        answers = {
            path: client.post(path) if "execution/" in path else client.get(path)
            for path in RUN_EXECUTION_REQUEST_PATHS
        }
        assert len(answers) == 4
        for path, response in answers.items():
            assert response.status_code == 503, f"{path} answered {response.status_code}"
            detail = response.json()["detail"]
            assert detail["refusal_kind"] == "PORT_NOT_COMPOSED"
            assert detail["advanced"] is False
            assert "composition leaf" in detail["message"]

    def test_no_execution_path_is_served_when_the_gate_is_closed(self) -> None:
        """The same four, and every verb on them, gone with the gate shut.

        Criterion 15 in its narrowest form: with the Lab disabled, execution and
        private inspection are not reachable by any spelling. The test above is
        what stops this one passing over an empty set.
        """
        client = TestClient(create_app(DISABLED))

        assert RUN_EXECUTION_REQUEST_PATHS
        for path in RUN_EXECUTION_REQUEST_PATHS:
            assert client.get(path).status_code == 404
            assert client.post(path).status_code == 404
            assert client.put(path).status_code == 404
            assert client.delete(path).status_code == 404


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
