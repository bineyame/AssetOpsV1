"""The four execution routes, against a fake port.

The product side of T022, tested where the product side lives. What a kernel
actually computes is `host/tests/`' business, and it has to be: this tree may not
import one by any spelling, which is the whole point of the port.

So the port here is a fake that answers a `LabProjection` the test built. That is
not a weakening - it is the seam being exercised as a seam. What these prove is
what the BACKEND does: which routes exist, what each refusal comes back as, that a
malformed control request is refused without advancing anything, and that every
exact quantity leaves as text rather than as a float.
"""

from __future__ import annotations

from fractions import Fraction

import pytest
from fastapi.testclient import TestClient
from run_fixtures import (
    FakeRuns,
    FakeScenarios,
    FakeSites,
    scenario,
    setup_request,
    site,
)

from assetops_backend.config import FeatureFlags
from assetops_backend.main import create_app
from assetops_backend.runs.models import SimulationRun
from assetops_backend.runs.profiles import (
    LAB_PUBLICATION_PROFILE,
    MINIMAL_FUEL_TANK_MODEL,
)
from assetops_backend.runs.service import RunSetupService

import run_fixtures as profiles
from assetops_contracts.lab_projection import (
    LAB_CONTROL_REFUSALS,
    LabControlRefused,
    LabProjection,
    ObservationView,
    PrivateStateRow,
)
from assetops_contracts.observation import (
    DeviceObservation,
    DeviceSignalSpec,
    ReportingPathWindow,
)

ENABLED = FeatureFlags(simulator_lab_enabled=True)
RUNS_PATH = "/api/simulator-lab/runs"
TANK = "fuel-tank-volume@fuel-tank"

SIGNAL = DeviceSignalSpec(
    device_id="fuel-level-sensor",
    signal_id="fuel-level",
    address=TANK,
    state_key="fuel-tank-volume",
    reading_class="STATE_SIGNAL",
    canonical_unit="L",
    cadence_minutes=15,
    bias=Fraction(-1, 2),
    dropout_per_thousand=40,
    statement="one sensor",
)


def projection(run_id: str, **changes) -> LabProjection:
    """A projection shaped like the one the composed leaf produces.

    The numbers are the shipped scenario's own at offset 1545: the world holds
    254.02 L, the newest reading is the 373.52 L published before the gap opened,
    and they disagree by the 120 L the gap hides.
    """
    fields = dict(
        run_id=run_id,
        status="RUNNING",
        statement="This execution has reached the instant shown.",
        boundaries_completed=104,
        boundaries_total=165,
        offset_minutes=1545,
        simulation_time="2026-09-22T01:45:00Z",
        interval_start_time="2026-09-21T00:00:00Z",
        interval_end_time="2026-09-22T17:00:00Z",
        timestep_minutes=15,
        seed=20260921,
        kernel_version=1,
        model_profile_id="minimal-fuel-tank",
        model_profile_version=1,
        publication_profile_id="simulator-lab-publication",
        publication_profile_version=2,
        numeric_policy="EXACT_RATIONAL",
        numeric_policy_version=1,
        execution_contract_version=8,
        inputs_identity="b" * 64,
        content_digest=None,
        observation_series_digest="c" * 64,
        private_state=(
            PrivateStateRow(
                address=TANK,
                state_key="fuel-tank-volume",
                value=Fraction(12701, 50),
                canonical_unit="L",
                kind="STOCK",
            ),
        ),
        observations=(
            ObservationView(
                address=TANK,
                state_key="fuel-tank-volume",
                device_id="fuel-level-sensor",
                signal_id="fuel-level",
                reading_class="STATE_SIGNAL",
                at_offset_minutes=1545,
                simulation_time="2026-09-22T01:45:00Z",
                canonical_unit="L",
                true_value=Fraction(12701, 50),
                reported_value=Fraction(9338, 25),
                reported_source_time="2026-09-22T00:45:00Z",
                reported_at_offset_minutes=1485,
                quality="STALE",
                due=True,
                outcome="SUPPRESSED_BY_GAP",
                suppression_reason="fuel-level-reporting-gap forces it",
                cadence_minutes=15,
                bias=Fraction(-1, 2),
                dropout_per_thousand=40,
            ),
        ),
        signals=(SIGNAL,),
        reporting_gaps=(
            ReportingPathWindow(
                event_id="fuel-level-reporting-gap",
                condition_address="fuel-level-reporting-availability@fuel-tank",
                device_id="fuel-level-sensor",
                signal_id="fuel-level",
                address=TANK,
                offset_minutes=1490,
                duration_minutes=90,
                interval_minutes=2460,
            ),
        ),
        recent_reports=(
            DeviceObservation(
                device_id="fuel-level-sensor",
                signal_id="fuel-level",
                address=TANK,
                state_key="fuel-tank-volume",
                reading_class="STATE_SIGNAL",
                at_offset_minutes=1485,
                source_sample_time="2026-09-22T00:45:00Z",
                outcome="REPORTED",
                reported_value=Fraction(9338, 25),
                canonical_unit="L",
            ),
        ),
        reported_count=96,
        suppressed_by_gap_count=4,
        dropped_count=5,
    )
    fields.update(changes)
    return LabProjection(**fields)


class FakeExecution:
    """An execution port that answers what the test told it to.

    It records every call, because several claims below are about what the route
    did NOT do - a refused control must not have asked the port to advance, and a
    malformed request must not have reached it at all.
    """

    def __init__(self, answer=None, refuse: str | None = None) -> None:
        self.answer = answer
        self.refuse = refuse
        self.calls: list[tuple] = []

    def _reply(self, name: str, run: SimulationRun, *rest):
        self.calls.append((name, run.run_id, *rest))
        if self.refuse is not None:
            raise LabControlRefused(self.refuse, run.run_id)
        return self.answer if self.answer is not None else projection(run.run_id)

    def projection(self, run: SimulationRun) -> LabProjection:
        return self._reply("projection", run)

    def start(self, run: SimulationRun) -> LabProjection:
        return self._reply("start", run)

    def step(
        self, run: SimulationRun, *, boundaries: int, from_boundary: int
    ) -> LabProjection:
        return self._reply("step", run, boundaries, from_boundary)

    def run_to_end(self, run: SimulationRun) -> LabProjection:
        return self._reply("run_to_end", run)


def persisted_draft() -> tuple[SimulationRun, FakeRuns]:
    """One Draft, written by the real run setup service into an in-memory store.

    Built rather than hand-written, because a route test over a record somebody
    shaped by hand is a test about the shape its author expected.
    """
    store = FakeRuns()
    target = site()
    definition = scenario()
    record = RunSetupService(
        store,
        FakeSites((target,)),
        FakeScenarios((definition,)),
        model_profiles=(profiles.model_profile(),),
        publication_profiles=(profiles.publication_profile(),),
        now=lambda: "2026-09-21T09:00:00Z",
    ).create_draft_run(setup_request())
    return record, store


def served(execution: FakeExecution):
    """One app with a persisted Draft and the fake port behind the Lab."""
    record, store = persisted_draft()
    client = TestClient(
        create_app(
            ENABLED,
            site_repository=FakeSites((site(),)),
            run_repository=store,
            execution=execution,
        )
    )
    return client, record


class TestTheExecutionReadAndTheThreeControls:
    def test_the_read_returns_the_projection_and_changes_nothing(self) -> None:
        execution = FakeExecution()
        client, record = served(execution)

        response = client.get(f"{RUNS_PATH}/{record.run_id}/execution")

        assert response.status_code == 200
        assert execution.calls == [("projection", record.run_id)]
        body = response.json()["execution"]
        assert body["status"] == "RUNNING"
        assert body["boundaries_completed"] == 104

    def test_each_control_reaches_its_own_method(self) -> None:
        execution = FakeExecution()
        client, record = served(execution)
        base = f"{RUNS_PATH}/{record.run_id}/execution"

        assert client.post(f"{base}/start").status_code == 200
        assert (
            client.post(
                f"{base}/step", json={"boundaries": 4, "from_boundary": 104}
            ).status_code
            == 200
        )
        assert client.post(f"{base}/run-to-end").status_code == 200

        assert execution.calls == [
            ("start", record.run_id),
            ("step", record.run_id, 4, 104),
            ("run_to_end", record.run_id),
        ]

    def test_a_control_on_an_unknown_run_is_a_typed_not_found(self) -> None:
        """Criterion 1's "unknown input yields a typed, inspectable outcome".

        The same `RUN_NOT_FOUND` the detail route already answers, because a
        control about a run that does not exist is not a new kind of fact - and
        the port is never asked about it.
        """
        execution = FakeExecution()
        client, _ = served(execution)
        missing = "run-" + "0" * 32

        for path, verb in (
            (f"{RUNS_PATH}/{missing}/execution", client.get),
            (f"{RUNS_PATH}/{missing}/execution/start", client.post),
            (f"{RUNS_PATH}/{missing}/execution/run-to-end", client.post),
        ):
            response = verb(path)
            assert response.status_code == 404
            assert response.json()["detail"]["code"] == "RUN_NOT_FOUND"

        assert execution.calls == []

    def test_a_malformed_identity_is_not_found_rather_than_refused(
        self,
    ) -> None:
        execution = FakeExecution()
        client, _ = served(execution)

        response = client.get(f"{RUNS_PATH}/not-a-run-identity/execution")

        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "RUN_NOT_FOUND"
        assert execution.calls == []


class TestARefusedControlAdvancesNothing:
    @pytest.mark.parametrize("kind", sorted(LAB_CONTROL_REFUSALS))
    def test_every_refusal_arrives_as_a_typed_409(self, kind: str) -> None:
        """Every member of the vocabulary, not a sample of it.

        A kind with no route mapping would reach a client as an unhandled
        exception, and the parametrization is what stops one being added without
        one.
        """
        execution = FakeExecution(refuse=kind)
        client, record = served(execution)

        response = client.post(
            f"{RUNS_PATH}/{record.run_id}/execution/start"
        )

        assert response.status_code == 409
        detail = response.json()["detail"]
        assert detail["refusal_kind"] == kind
        assert detail["code"] == f"EXECUTION_{kind}"
        assert detail["advanced"] is False
        assert detail["subject"] == record.run_id
        assert len(detail["message"]) > 60

    def test_a_refusal_is_not_a_run_setup_refusal(self) -> None:
        """Four vocabularies, pairwise disjoint, and this is the fourth.

        A run that could not be set up is refused at 422 with no identity
        allocated; a frozen run that may not execute is BLOCKED; an execution that
        started and stopped has FAILED. This is none of those: the request was
        well formed and the run is not in a state where it applies.
        """
        from assetops_backend.runs.models import BLOCKING_REASON_KINDS
        from assetops_backend.runs.refusals import RUN_SETUP_REFUSAL_KINDS
        from assetops_contracts.failures import EXECUTION_FAILURE_KINDS

        vocabularies = [
            LAB_CONTROL_REFUSALS,
            RUN_SETUP_REFUSAL_KINDS,
            BLOCKING_REASON_KINDS,
            EXECUTION_FAILURE_KINDS,
        ]
        for one in vocabularies:
            assert one
        for index, one in enumerate(vocabularies):
            for other in vocabularies[index + 1 :]:
                assert not one & other, sorted(one & other)


class TestTheStepRequestIsParsedStrictly:
    @pytest.mark.parametrize(
        "body",
        [
            None,
            {},
            {"boundaries": 1},
            {"from_boundary": 0},
            {"boundaries": 1, "from_boundary": 0, "force": True},
            {"boundaries": 0, "from_boundary": 0},
            {"boundaries": -1, "from_boundary": 0},
            {"boundaries": 1, "from_boundary": -1},
            {"boundaries": "1", "from_boundary": 0},
            {"boundaries": 1.5, "from_boundary": 0},
            {"boundaries": True, "from_boundary": 0},
        ],
    )
    def test_a_request_that_is_not_one_is_refused_without_advancing(
        self, body
    ) -> None:
        """Strict, like every other request parser here.

        `True` is the one worth naming: it is an `int` in Python and would
        otherwise arrive as a request to advance one boundary, which is a request
        nobody made.
        """
        execution = FakeExecution()
        client, record = served(execution)

        response = client.post(
            f"{RUNS_PATH}/{record.run_id}/execution/step", json=body
        )

        assert response.status_code == 422
        assert (
            response.json()["detail"]["code"] == "EXECUTION_REQUEST_INVALID"
        )
        assert "Nothing was advanced" in response.json()["detail"]["message"]
        assert execution.calls == []

    def test_a_well_formed_request_reaches_the_port_unchanged(self) -> None:
        execution = FakeExecution()
        client, record = served(execution)

        response = client.post(
            f"{RUNS_PATH}/{record.run_id}/execution/step",
            json={"boundaries": 16, "from_boundary": 32},
        )

        assert response.status_code == 200
        assert execution.calls == [("step", record.run_id, 16, 32)]


class TestThePayloadCarriesNoFloatAndNoSimulatorType:
    def body(self) -> dict:
        client, record = served(FakeExecution())
        return client.get(f"{RUNS_PATH}/{record.run_id}/execution").json()[
            "execution"
        ]

    def test_every_exact_quantity_is_text(self) -> None:
        """The numeric policy, held at the wire.

        `EXACT_RATIONAL` never rounds, so a payload carrying a binary float would
        be the one place the policy stopped holding - and it would hold the screen
        responsible for a number the wire had already spoiled.
        """
        body = self.body()
        row = body["observations"][0]

        assert body["private_state"][0]["value"] == "254.02"
        assert row["true_value"] == "254.02"
        assert row["reported_value"] == "373.52"
        assert row["bias"] == "-0.5"
        assert body["signals"][0]["bias"] == "-0.5"
        assert body["recent_reports"][0]["reported_value"] == "373.52"

        for quantity in (
            body["private_state"][0]["value"],
            row["true_value"],
            row["reported_value"],
            row["bias"],
        ):
            assert isinstance(quantity, str)

    def test_no_float_appears_anywhere_in_the_payload(self) -> None:
        """Checked over the whole tree rather than field by field.

        A field-by-field assertion protects the fields somebody thought of. This
        one fails on a float wherever it appears, including one added later.
        """
        found: list[str] = []

        def walk(node, path: str) -> None:
            if isinstance(node, dict):
                for key, value in node.items():
                    walk(value, f"{path}.{key}")
            elif isinstance(node, list):
                for index, value in enumerate(node):
                    walk(value, f"{path}[{index}]")
            elif isinstance(node, float):
                found.append(path)

        body = self.body()
        assert body, "the payload is empty, so this scan proves nothing"
        walk(body, "execution")

        assert found == []

    def test_the_five_facts_the_screen_needs_are_five_fields(self) -> None:
        """Criterion 5 at the wire, so a screen cannot be blamed for merging them."""
        row = self.body()["observations"][0]

        assert row["device_id"] == "fuel-level-sensor"
        assert row["signal_id"] == "fuel-level"
        assert row["true_value"] == "254.02"
        assert row["reported_value"] == "373.52"
        assert row["reported_source_time"] == "2026-09-22T00:45:00Z"
        assert row["quality"] == "STALE"
        assert row["outcome"] == "SUPPRESSED_BY_GAP"
        # The vocabularies' own copy, placed rather than composed on a screen.
        assert len(row["quality_statement"]) > 60
        assert len(row["outcome_statement"]) > 60

    def test_the_payload_names_no_simulator_type(self) -> None:
        """The port's promise, at its own boundary.

        `tools/checks/dependency-direction.ps1` holds that this tree cannot import
        `assetops_simulator` at all, so a route could not name a trajectory even
        if it wanted to. This is the payload half: what leaves is a projection,
        and no trace record, world state or model spec is anywhere in it.
        """
        body = self.body()

        for banned in (
            "trajectory",
            "boundaries",
            "applied_events",
            "bounded_transitions",
            "handlers_exercised",
            "forcing_exposures",
            "state_samples",
            "stocks",
        ):
            assert banned not in body, banned

    def test_a_terminal_projection_carries_its_content_digest(self) -> None:
        execution = FakeExecution(
            answer=projection(
                "run-" + "1" * 32,
                status="COMPLETED",
                statement="This execution covered its whole interval.",
                content_digest="d" * 64,
                boundaries_completed=165,
                offset_minutes=2460,
            )
        )
        client, record = served(execution)

        body = client.post(
            f"{RUNS_PATH}/{record.run_id}/execution/run-to-end"
        ).json()["execution"]

        assert body["status"] == "COMPLETED"
        assert body["content_digest"] == "d" * 64
        assert body["observation_series_digest"] == "c" * 64


class TestTheProfilesTheRunSelectsAreTheOnesShipped:
    def test_the_shipped_profiles_are_the_ones_this_payload_names(self) -> None:
        """A fixture that named a profile this build has not got would be a test
        about a build nobody runs."""
        body = TestThePayloadCarriesNoFloatAndNoSimulatorType().body()

        assert body["model_profile_id"] == (
            MINIMAL_FUEL_TANK_MODEL.model_profile_id
        )
        assert body["publication_profile_id"] == (
            LAB_PUBLICATION_PROFILE.publication_profile_id
        )
        assert body["publication_profile_version"] == (
            LAB_PUBLICATION_PROFILE.publication_profile_version
        )
