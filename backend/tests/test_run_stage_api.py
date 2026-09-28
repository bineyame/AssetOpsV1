"""The stage inspector's route, against a port that answers what it is told.

The composing proof - a real kernel, gateway and stage behind this route - is in
`host/tests/test_source_staging.py`. This is the product half: the route serves
the neutral `SourceStageView` it is handed and nothing else, it is a read, and it
answers the same typed refusal as every execution route when no port is composed.

It also proves criterion 15's backend half by construction: this module builds a
stage from the neutral contracts alone, and nothing here can import a simulator.
"""

from __future__ import annotations

import json
from fractions import Fraction

from fastapi.testclient import TestClient
from run_fixtures import (
    FakeRuns,
    FakeScenarios,
    FakeSites,
    scenario,
    setup_request,
    site,
)

import run_fixtures as profiles
from assetops_backend.config import FeatureFlags
from assetops_backend.main import create_app
from assetops_backend.runs.models import SimulationRun
from assetops_backend.runs.service import RunSetupService
from assetops_contracts.source_envelope import (
    SourceEnvelope,
    SourceMappingEntry,
    SourceMappingSet,
    canonical_envelope_json,
    envelope_message_id,
)
from assetops_contracts.source_stage import (
    SOURCE_STAGE_STATUS_STATEMENTS,
    SourceStage,
    SourceStageView,
    release_blockers,
)

ENABLED = FeatureFlags(simulator_lab_enabled=True)
RUNS_PATH = "/api/simulator-lab/runs"

MAPPING = SourceMappingSet(
    mapping_set_id="simulator-lab-gateway-fuel",
    mapping_version=1,
    publication_latency_seconds=3,
    entries=(
        SourceMappingEntry(
            device_id="fuel-level-sensor",
            signal_id="fuel-level",
            measurement="STATE_AT_INSTANT",
            unit="L",
            publishes_unavailable=True,
        ),
    ),
)


def an_envelope() -> SourceEnvelope:
    identity = dict(
        site_id="MG-001",
        gateway_id="simulator-lab-gateway",
        source_id="simulator-lab-source",
        device_id="fuel-level-sensor",
        signal_id="fuel-level",
        source_time="2026-09-22T00:45:00Z",
    )
    return SourceEnvelope(
        message_id=envelope_message_id(**identity),
        sequence=91,
        mapping_set_id="simulator-lab-gateway-fuel",
        mapping_version=1,
        published_at="2026-09-22T00:45:03Z",
        measurement="STATE_AT_INSTANT",
        value=Fraction("373.52"),
        unit="L",
        quality="GOOD",
        unavailable_reason=None,
        interval_start=None,
        interval_end=None,
        **identity,
    )


def a_view(run_id: str) -> SourceStageView:
    stage = SourceStage(
        run_id=run_id,
        site_id="MG-001",
        source_id="simulator-lab-source",
        gateway_id="simulator-lab-gateway",
        mapping=MAPPING,
        envelopes=(an_envelope(),),
    )
    return SourceStageView(
        run_id=run_id,
        status="STAGED",
        statement=SOURCE_STAGE_STATUS_STATEMENTS["STAGED"],
        execution_status="RUNNING",
        release_blockers=release_blockers("STAGED", "RUNNING", stage),
        stage=stage,
        integrity_digest="a" * 64,
    )


class FakeStagePort:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def staged_envelopes(self, run: SimulationRun) -> SourceStageView:
        self.calls.append(("staged_envelopes", run.run_id))
        return a_view(run.run_id)


def served(execution=None):
    store = FakeRuns()
    record = RunSetupService(
        store,
        FakeSites((site(),)),
        FakeScenarios((scenario(),)),
        model_profiles=(profiles.model_profile(),),
        publication_profiles=(profiles.publication_profile(),),
        now=lambda: "2026-09-21T09:00:00Z",
    ).create_draft_run(setup_request())
    client = TestClient(
        create_app(
            ENABLED,
            site_repository=FakeSites((site(),)),
            run_repository=store,
            execution=execution,
        )
    )
    return client, record


class TestTheStageRoute:
    def test_it_serves_the_view_it_is_handed_with_the_exact_text(self) -> None:
        port = FakeStagePort()
        client, record = served(port)

        response = client.get(f"{RUNS_PATH}/{record.run_id}/stage")

        assert response.status_code == 200, response.text
        assert port.calls == [("staged_envelopes", record.run_id)]
        body = response.json()["stage"]
        (envelope,) = body["envelopes"]
        assert envelope["canonical"] == canonical_envelope_json(an_envelope())
        assert envelope["source_time"] == "2026-09-22T00:45:00Z"
        assert envelope["published_at"] == "2026-09-22T00:45:03Z"
        assert envelope["value"] == "373.52"
        assert body["release_eligible"] is False
        assert [item["kind"] for item in body["release_blockers"]] == [
            "EXECUTION_NOT_COMPLETED"
        ]
        assert body["envelope_schema_version"] == 1
        assert body["mapping"]["mapping_set_id"] == "simulator-lab-gateway-fuel"
        assert "received_at" not in json.dumps(body)

    def test_it_is_a_read_and_nothing_else(self) -> None:
        client, record = served(FakeStagePort())
        path = f"{RUNS_PATH}/{record.run_id}/stage"

        for method in ("post", "put", "patch", "delete"):
            assert getattr(client, method)(path).status_code == 405, method

    def test_an_unknown_run_is_not_found(self) -> None:
        client, _ = served(FakeStagePort())

        response = client.get(f"{RUNS_PATH}/run-00000000000000000000000000000000/stage")

        assert response.status_code == 404

    def test_no_composed_port_is_the_same_typed_refusal_as_execution(
        self,
    ) -> None:
        client, record = served(None)

        response = client.get(f"{RUNS_PATH}/{record.run_id}/stage")

        assert response.status_code == 503, response.text
        assert response.json()["detail"]["refusal_kind"] == "PORT_NOT_COMPOSED"
