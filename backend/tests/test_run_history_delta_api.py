"""The history route's live-follow read (T025e AC1), against a fake port.

`?since_boundary=n` is a selection over the `LabHistory` the port hands the
route: every append family narrowed to the rows recorded after the caller's n
boundaries, the static families left out, the manifest and `exposures` whole,
and a sibling `delta` envelope. The composing proof over a real live session -
every boundary, every family, folded back to the full read - is in
`host/tests/test_lab_history_prefix.py`.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction

import pytest
from fastapi.testclient import TestClient

from assetops_backend.config import FeatureFlags
from assetops_backend.main import create_app
from assetops_backend.runs.models import SimulationRun
from assetops_backend.simulator_lab_api import (
    HISTORY_APPEND_FAMILY_KEYS,
    HISTORY_STATIC_FAMILIES,
    history_payload,
)
from assetops_contracts.lab_history import (
    ForcingExposure,
    HistoryBoundary,
    HistorySample,
    LabHistory,
)
from assetops_contracts.observation import DeviceObservation, DeviceSignalSpec

from test_run_history_api import a_history, an_interval
from test_run_stage_api import RUNS_PATH, served


def an_attempt(at: int) -> DeviceObservation:
    return DeviceObservation(
        device_id="pv-meter", signal_id="ac-power",
        address="pv-ac-power@pv-inverter", state_key="pv-ac-power",
        reading_class="INTERVAL_SIGNAL", at_offset_minutes=at,
        source_sample_time=f"2026-09-22T03:{at:02d}:00Z", outcome="REPORTED",
        reported_value=Fraction(at), canonical_unit="kW",
    )


def a_growing_history(run_id: str) -> LabHistory:
    """Three boundaries, each recording a sample and an attempt, two intervals.

    The first interval is decided at 0 and closes at 5; the second is decided
    at 5. Selecting after boundary 1 (offset 0) must keep the interval decided
    at 5 only - which a key on `to_offset` would get wrong.
    """
    base = a_history(run_id)
    first = an_interval((), ())
    second = replace(first, from_offset=5, to_offset=10)
    return replace(
        base,
        status="RUNNING",
        source="LIVE_SESSION",
        history_digest="should-never-reach-a-delta",
        boundaries_total=4,
        boundaries=(
            HistoryBoundary(0, 0, "2026-09-22T03:00:00Z", False),
            HistoryBoundary(1, 5, "2026-09-22T03:05:00Z", True),
            HistoryBoundary(2, 10, "2026-09-22T03:10:00Z", True),
        ),
        samples=tuple(
            HistorySample(at, "fuel-tank-volume@fuel-tank", "fuel-tank-volume",
                          "POST_EVENT", "L", Fraction(400 - at))
            for at in (0, 5, 10)
        ),
        attempts=tuple(an_attempt(at) for at in (0, 5, 10)),
        intervals=(first, second),
        exposures=(
            ForcingExposure("pv-irradiance@site", "e-1", "irradiance",
                            Fraction(1), 0, 5),
        ),
        signals=(
            DeviceSignalSpec("pv-meter", "ac-power", "pv-ac-power@pv-inverter", "pv-ac-power",
                             "INTERVAL_SIGNAL", "kW", 5, Fraction(0), 0, "A meter."),
        ),
    )


class GrowingHistoryPort:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def history(self, run: SimulationRun) -> LabHistory:
        self.calls.append(("history", run.run_id))
        return a_growing_history(run.run_id)


def read(client, record, query: str = ""):
    return client.get(f"{RUNS_PATH}/{record.run_id}/execution/history{query}")


def selected(full: dict, family: str, after: int | None) -> list:
    key = HISTORY_APPEND_FAMILY_KEYS[family]
    return [row for row in full[family] if after is None or row[key] > after]


class TestTheDeltaRead:
    def test_without_the_parameter_the_read_is_unchanged(self) -> None:
        client, record = served(GrowingHistoryPort())

        body = read(client, record).json()

        assert set(body) == {"history"}
        assert body["history"] == history_payload(
            a_growing_history(record.run_id), record
        )

    @pytest.mark.parametrize("since", [0, 1, 2, 3])
    def test_a_delta_is_the_full_read_selected_by_time_key(self, since) -> None:
        port = GrowingHistoryPort()
        client, record = served(port)
        full = read(client, record).json()["history"]

        response = read(client, record, f"?since_boundary={since}")

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["delta"] == {"since_boundary": since, "through_boundary": 3}
        delta = body["history"]
        after = None if since == 0 else full["boundaries"][since - 1]["offset_minutes"]
        for family in HISTORY_APPEND_FAMILY_KEYS:
            assert delta[family] == selected(full, family, after), family
        # The manifest, coverage and exposures are whole, the digest is not.
        whole = set(full) - set(HISTORY_APPEND_FAMILY_KEYS) - set(
            HISTORY_STATIC_FAMILIES
        ) - {"history_digest"}
        assert "exposures" in whole and "boundaries_recorded" in whole
        for key in whole:
            assert delta[key] == full[key], key
        assert full["history_digest"] == "should-never-reach-a-delta"
        assert delta["history_digest"] is None
        # The static families are the full read's alone.
        assert delta["drawing_context"] is None
        for family in set(HISTORY_STATIC_FAMILIES) - {"drawing_context"}:
            assert delta[family] == [], family
        assert full["signals"] and full["sample_phases"]
        assert set(delta) == set(full)

    def test_the_interval_is_keyed_by_the_boundary_that_decided_it(self) -> None:
        client, record = served(GrowingHistoryPort())

        delta = read(client, record, "?since_boundary=1").json()["history"]

        assert [i["from_offset"] for i in delta["intervals"]] == [5]
        assert [b["offset_minutes"] for b in delta["boundaries"]] == [5, 10]
        assert delta["boundaries_recorded"] == 3
        assert delta["recorded_through_offset_minutes"] == 10

    def test_a_delta_at_the_edge_is_empty_but_whole_in_its_manifest(self) -> None:
        client, record = served(GrowingHistoryPort())

        body = read(client, record, "?since_boundary=3").json()

        assert body["delta"] == {"since_boundary": 3, "through_boundary": 3}
        for family in HISTORY_APPEND_FAMILY_KEYS:
            assert body["history"][family] == [], family
        assert body["history"]["boundaries_recorded"] == 3


class TestRefusals:
    @pytest.mark.parametrize(
        "raw", ["-1", "1.5", "abc", "", "true", "+1", " 1", "1e1", "²"]
    )
    def test_a_value_that_is_not_a_whole_count_is_a_typed_refusal(self, raw) -> None:
        client, record = served(GrowingHistoryPort())

        response = client.get(
            f"{RUNS_PATH}/{record.run_id}/execution/history",
            params={"since_boundary": raw},
        )

        assert response.status_code == 422, response.text
        assert response.json()["detail"]["code"] == "EXECUTION_REQUEST_INVALID"

    def test_a_count_ahead_of_the_record_is_refused_with_its_own_code(self) -> None:
        client, record = served(GrowingHistoryPort())

        response = read(client, record, "?since_boundary=4")

        assert response.status_code == 409, response.text
        detail = response.json()["detail"]
        assert detail["code"] == "HISTORY_SINCE_AHEAD"
        assert "3 boundaries" in detail["message"]

    def test_an_unknown_run_is_still_not_found(self) -> None:
        port = GrowingHistoryPort()
        client, _ = served(port)

        response = client.get(
            f"{RUNS_PATH}/run-00000000000000000000000000000000/execution/history"
            "?since_boundary=0"
        )

        assert response.status_code == 404
        assert port.calls == []

    def test_the_gate_closed_serves_no_delta_route(self) -> None:
        port = GrowingHistoryPort()
        client = TestClient(
            create_app(FeatureFlags(simulator_lab_enabled=False), execution=port)
        )

        response = client.get(
            f"{RUNS_PATH}/run-00000000000000000000000000000001/execution/history"
            "?since_boundary=0"
        )

        assert response.status_code == 404
        assert port.calls == []
