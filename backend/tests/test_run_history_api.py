"""The recorded-history route (T025c), against a port that answers what it is told.

The composing proof - a real kernel, a persisted artifact, a host restart and a
strict read - is in `host/tests/test_lab_history.py`. This is the product half:
the route serves the neutral `LabHistory` it is handed and nothing else, it is a
read, it keeps exact text exact and an absent reading `null`, and it exists only
while the Lab gate is open.
"""

from __future__ import annotations

from fractions import Fraction

from fastapi.testclient import TestClient

from assetops_backend.config import FeatureFlags
from assetops_backend.main import create_app
from assetops_backend.runs.models import SimulationRun
from assetops_contracts.lab_history import (
    HISTORY_FAMILIES,
    FamilyCoverage,
    HistoryBoundary,
    HistorySample,
    LabHistory,
)
from assetops_contracts.observation import DeviceObservation

from test_run_stage_api import RUNS_PATH, served


def a_history(run_id: str) -> LabHistory:
    return LabHistory(
        run_id=run_id,
        status="COMPLETED",
        source="PERSISTED",
        statement="Read back.",
        history_schema_version=1,
        boundaries_total=2,
        inputs_identity="inputs",
        content_digest="trajectory",
        observation_series_digest="observations",
        history_digest="history",
        coverage=tuple(
            FamilyCoverage(family, "RECORDED", "Recorded.")
            for family in HISTORY_FAMILIES
        ),
        boundaries=(
            HistoryBoundary(0, 0, "2026-09-22T03:00:00Z", False),
            HistoryBoundary(1, 5, "2026-09-22T03:05:00Z", True),
        ),
        samples=(
            HistorySample(0, "fuel-tank-volume@fuel-tank", "fuel-tank-volume",
                          "POST_EVENT", "L", Fraction(2799, 800)),
            HistorySample(5, "generator-state@generator", "generator-state",
                          "FOR_STEP", "state", "RUNNING"),
        ),
        attempts=(
            DeviceObservation(
                device_id="pv-meter", signal_id="ac-power",
                address="pv-ac-power@pv-inverter", state_key="pv-ac-power",
                reading_class="INTERVAL_SIGNAL", at_offset_minutes=5,
                source_sample_time="2026-09-22T03:05:00Z", outcome="REPORTED",
                reported_value=Fraction(0), canonical_unit="kW",
            ),
            DeviceObservation(
                device_id="pv-meter", signal_id="ac-power",
                address="pv-ac-power@pv-inverter", state_key="pv-ac-power",
                reading_class="INTERVAL_SIGNAL", at_offset_minutes=0,
                source_sample_time="2026-09-22T03:00:00Z", outcome="DROPPED",
                reported_value=None, canonical_unit="kW",
                suppression_reason="DROPOUT",
            ),
        ),
    )


class FakeHistoryPort:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def history(self, run: SimulationRun) -> LabHistory:
        self.calls.append(("history", run.run_id))
        return a_history(run.run_id)


class TestTheHistoryRoute:
    def test_it_serves_the_history_it_is_handed_exactly(self) -> None:
        port = FakeHistoryPort()
        client, record = served(port)

        response = client.get(f"{RUNS_PATH}/{record.run_id}/execution/history")

        assert response.status_code == 200, response.text
        assert port.calls == [("history", record.run_id)]
        body = response.json()["history"]
        assert body["source"] == "PERSISTED"
        assert body["boundaries_recorded"] == 2
        assert body["recorded_through_offset_minutes"] == 5
        assert [c["family"] for c in body["coverage"]] == list(HISTORY_FAMILIES)
        fuel, state = body["samples"]
        assert fuel["value"] == "3.49875" and fuel["phase"] == "POST_EVENT"
        assert state["value"] == "RUNNING" and state["unit"] == "state"
        zero, dropped = body["attempts"]
        # A valid zero and a missing reading are two different wire values.
        assert zero["reported_value"] == "0"
        assert dropped["reported_value"] is None
        assert dropped["outcome"] == "DROPPED"

    def test_it_is_a_read_and_nothing_else(self) -> None:
        client, record = served(FakeHistoryPort())
        path = f"{RUNS_PATH}/{record.run_id}/execution/history"

        for method in ("post", "put", "patch", "delete"):
            assert getattr(client, method)(path).status_code == 405, method

    def test_an_unknown_run_is_not_found_and_the_port_is_not_asked(self) -> None:
        port = FakeHistoryPort()
        client, _ = served(port)

        response = client.get(
            f"{RUNS_PATH}/run-00000000000000000000000000000000/execution/history"
        )

        assert response.status_code == 404
        assert port.calls == []

    def test_no_composed_port_is_the_typed_refusal(self) -> None:
        client, record = served(None)

        response = client.get(f"{RUNS_PATH}/{record.run_id}/execution/history")

        assert response.status_code == 503, response.text
        assert response.json()["detail"]["refusal_kind"] == "PORT_NOT_COMPOSED"

    def test_the_gate_closed_serves_no_history_route(self) -> None:
        port = FakeHistoryPort()
        client = TestClient(
            create_app(FeatureFlags(simulator_lab_enabled=False), execution=port)
        )

        response = client.get(
            f"{RUNS_PATH}/run-00000000000000000000000000000001/execution/history"
        )

        assert response.status_code == 404
        assert port.calls == []
