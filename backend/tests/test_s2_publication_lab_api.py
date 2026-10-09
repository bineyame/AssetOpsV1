"""S2-01c phase 3a: the post-run release window and the Lab publication/diagnostics API.

`D-2026-10-09-s2-publication-clock-post-run-release`. Run setup admits exactly
one narrow exception to `outside-the-interval`: on a registered `RUN_VIRTUAL`
publication profile, a reporting-path publication-delay WINDOW starting inside
the interval may end at most one timestep after it. Every other entry, profile
and larger overrun keeps `INTERVAL_INVALID`.

The gated Lab API reads the Lab-private schedule, advances the virtual
publication clock through the port, and reads the gateway's local diagnostics;
an unreachable gateway is unavailable, never a healthy zero queue.
"""

from __future__ import annotations

import copy
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
import yaml
from run_fixtures import FakeRuns, FakeScenarios, FakeSites
from test_s1_cutover import ON, StagedExecution, app_for, legacy_root  # noqa: F401
from test_s2_registered_basis import (
    REPOSITORY,
    SCENARIO,
    converted,
    request,
)

from assetops_backend.runs.adapters.yaml_run_store import YamlRunStore
from assetops_backend.runs.profiles import (
    DAYTIME_MINI_GRID_MODEL,
    LAB_PUBLICATION_PROFILE,
    LAB_PUBLICATION_PROFILE_V5,
    REGISTERED_KOBO_PUBLICATION_PROFILE,
    REGISTERED_KOBO_PUBLICATION_PROFILE_V2,
)
from assetops_backend.runs.refusals import RunSetupRefused
from assetops_backend.runs.registered_basis import RegisteredLabBasis
from assetops_backend.runs.service import RunSetupService
from assetops_backend.scenarios.parsing import parse_scenario_document
from assetops_backend.simulator_lab_api import (
    gateway_diagnostics_payload,
    publication_schedule_payload,
)
from assetops_backend.sites.cutover import ImportedSiteRegistry
from assetops_backend.sites.foundation_service import FoundationService
from assetops_contracts.lab_projection import LabControlRefused
from assetops_contracts.publication_schedule import (
    PENDING,
    RELEASED,
    DelayedReport,
    PublicationSchedule,
)

V1, V2 = REGISTERED_KOBO_PUBLICATION_PROFILE, REGISTERED_KOBO_PUBLICATION_PROFILE_V2
POST_RUN_ID = "kobo-daytime-post-run-publication"
POST_RUN_DOCUMENT = yaml.safe_load(
    (REPOSITORY / "config" / "scenarios" / f"{POST_RUN_ID}.yaml").read_text(encoding="utf-8")
)


def scenario(document: dict[str, Any]):
    return parse_scenario_document(document, source=document["scenario_id"], origin="SHIPPED")


def edited(edit) -> dict[str, Any]:
    document = copy.deepcopy(POST_RUN_DOCUMENT)
    edit({entry["event_id"]: entry for entry in document["timeline"]})
    return document


def setup(document: dict[str, Any] = POST_RUN_DOCUMENT, profile=V2):
    from test_s1_cutover import NOW, Clock
    from test_s2_registered_basis import text

    store, _, _ = converted()
    registry = ImportedSiteRegistry(FoundationService(store, "demo", Clock(NOW)))
    parsed = scenario(document)
    service = RunSetupService(
        FakeRuns(),
        FakeSites(()),
        FakeScenarios((SCENARIO, parsed)),
        model_profiles=(DAYTIME_MINI_GRID_MODEL,),
        publication_profiles=(LAB_PUBLICATION_PROFILE, LAB_PUBLICATION_PROFILE_V5, V1, V2),
        now=lambda: text(NOW),
        registered_bases=RegisteredLabBasis(registry),
    )
    return service.create_draft_run(
        request(
            scenario_id=parsed.scenario_id,
            scenario_version=parsed.version.scenario_version,
            publication_profile={
                "profile_id": profile.publication_profile_id,
                "profile_version": profile.publication_profile_version,
            },
        )
    )


def refused_kind(document: dict[str, Any] = POST_RUN_DOCUMENT, profile=V2) -> RunSetupRefused:
    with pytest.raises(RunSetupRefused) as caught:
        setup(document, profile)
    return caught.value


class TestPostRunReleaseWindow:
    def test_the_shipped_fixture_ends_one_timestep_after_the_interval(self) -> None:
        closing = {e["event_id"]: e for e in POST_RUN_DOCUMENT["timeline"]}["soc-publication-delay-closing"]
        assert (closing["offset_minutes"], closing["timing"]["duration_minutes"]) == (710, 15)

    def test_a_registered_run_virtual_draft_accepts_it(self) -> None:
        run = setup()
        assert run.execution_status == "READY" and run.blocking_reasons == ()
        reporting = {c.event_id: c for c in run.deterministic_identity.reporting_path_conditions}
        assert (reporting["soc-publication-delay-closing"].offset_minutes,
                reporting["soc-publication-delay-closing"].duration_minutes) == (710, 15)

    def test_a_gateway_utc_profile_keeps_the_refusal(self) -> None:
        assert refused_kind(profile=V1).kind == "INTERVAL_INVALID"

    def test_a_gateway_utc_profile_declaring_the_delay_keeps_the_refusal(self) -> None:
        """`simulator-lab-publication` v5 declares the same delay state on the
        gateway's own clock: the exception is the virtual clock's alone."""
        assert LAB_PUBLICATION_PROFILE_V5.publication_clock == "GATEWAY_UTC"
        assert LAB_PUBLICATION_PROFILE_V5.supported_reporting("battery-soc-publication-delay") is not None
        assert refused_kind(profile=LAB_PUBLICATION_PROFILE_V5).kind == "INTERVAL_INVALID"

    def test_two_timesteps_past_the_end_is_refused(self) -> None:
        def longer(entries):
            entries["soc-publication-delay-closing"]["timing"]["duration_minutes"] = 26  # ends at 736

        assert refused_kind(edited(longer)).kind == "INTERVAL_INVALID"

    def test_a_window_starting_at_the_end_is_refused(self) -> None:
        def at_end(entries):
            entries["soc-publication-delay-closing"]["offset_minutes"] = 720
            entries["soc-publication-delay-closing"]["timing"]["duration_minutes"] = 10

        assert refused_kind(edited(at_end)).kind == "INTERVAL_INVALID"

    def test_a_forcing_window_past_the_end_keeps_the_refusal(self) -> None:
        def forcing(entries):
            last = max(
                (e for e in entries.values() if e["execution_role"] == "FORCING_INPUT"
                 and e["timing"]["shape"] == "WINDOW" and "publication-delay" not in e["state_key"]),
                key=lambda e: e["offset_minutes"] + e["timing"]["duration_minutes"],
            )
            last["timing"]["duration_minutes"] += 15

        assert refused_kind(edited(forcing)).kind == "INTERVAL_INVALID"

    def test_the_in_interval_hold_still_may_not_exceed_the_cadence(self) -> None:
        def earlier(entries):
            entries["soc-publication-delay-closing"]["offset_minutes"] = 705
            entries["soc-publication-delay-closing"]["timing"]["duration_minutes"] = 30

        # [705, 735) would hold both the 705 and the 720 sample and release
        # them together: still the cadence refusal, not a batch release.
        assert refused_kind(edited(earlier)).kind == "PUBLICATION_DELAY_REFUSED"


SNAPSHOT = "ab" * 32


def a_schedule(run_id: str) -> PublicationSchedule:
    return PublicationSchedule(
        run_id=run_id, snapshot_sha256=SNAPSHOT, clock_instant="2026-09-30T15:00:00Z",
        world_reached_instant="2026-09-30T15:00:00Z", world_complete=True,
        delayed=(
            DelayedReport(
                report_key="k-midday", device_id="battery-pcs-controller", signal_id="state-of-charge",
                source_time="2026-09-30T07:00:00Z", scheduled_release_at="2026-09-30T07:10:00Z",
                delay_event_id="soc-publication-delay-midday", report_text="{\"report\":\"SECRET-TEXT\"}",
                state=RELEASED, released_at_clock="2026-09-30T07:15:00Z", message_id="m-1", sequence=7,
                outcome="ADMITTED",
            ),
            DelayedReport(
                report_key="k-closing", device_id="battery-pcs-controller", signal_id="state-of-charge",
                source_time="2026-09-30T15:00:00Z", scheduled_release_at="2026-09-30T15:05:00Z",
                delay_event_id="soc-publication-delay-closing", report_text="{\"report\":\"SECRET-TEXT\"}",
            ),
        ),
    )


class PublicationExecution(StagedExecution):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.schedule_answer: object = None
        self.advance_answer: object = None
        self.diagnostics_answer: dict = {"status": "GATEWAY_UNAVAILABLE", "detail": "connection refused", "diagnostics": None}

    def publication_schedule(self, run):
        self.calls.append(("publication_schedule", run.run_id))
        if isinstance(self.schedule_answer, Exception):
            raise self.schedule_answer
        return self.schedule_answer

    def advance_publication(self, run, instant):
        self.calls.append(("advance_publication", run.run_id, instant))
        if isinstance(self.advance_answer, Exception):
            raise self.advance_answer
        return self.advance_answer

    def gateway_diagnostics(self):
        self.calls.append(("gateway_diagnostics",))
        return self.diagnostics_answer


class TestPublicationApi:
    def client_with_draft(self, tmp_path, legacy_root, profile=V2):
        store, _, _ = converted()
        execution = PublicationExecution()
        runs = YamlRunStore(tmp_path / "runs")
        client = app_for(
            store, legacy_root, flags=ON, run_repository=runs, execution=execution,
            scenario_repository=FakeScenarios((SCENARIO, scenario(POST_RUN_DOCUMENT))),
        )
        body = request(
            scenario_id=POST_RUN_ID, scenario_version=1,
            publication_profile={"profile_id": profile.publication_profile_id,
                                 "profile_version": profile.publication_profile_version},
        )
        created = client.post("/api/simulator-lab/runs", json=body)
        assert created.status_code == 201, created.text
        return client, execution, created.json()["run"]["run_id"]

    def test_the_profile_list_names_each_publication_clock(self, tmp_path, legacy_root) -> None:
        client, _, _ = self.client_with_draft(tmp_path, legacy_root)
        profiles = client.get("/api/simulator-lab/run-profiles").json()["publication_profiles"]
        clocks = {(p["publication_profile_id"], p["publication_profile_version"]): p["publication_clock"] for p in profiles}
        assert clocks[(V2.publication_profile_id, 2)] == "RUN_VIRTUAL"
        assert clocks[(V1.publication_profile_id, 1)] == "GATEWAY_UTC"

    def test_the_schedule_read_labels_each_clock_and_omits_private_fields(self, tmp_path, legacy_root) -> None:
        client, execution, run_id = self.client_with_draft(tmp_path, legacy_root)
        execution.schedule_answer = a_schedule(run_id)
        response = client.get(f"/api/simulator-lab/runs/{run_id}/publication")
        assert response.status_code == 200, response.text
        publication = response.json()["publication"]
        assert (publication["status"], publication["publication_clock"]) == ("AVAILABLE", "RUN_VIRTUAL")
        assert (publication["pending_count"], publication["released_count"], publication["world_complete"]) == (1, 1, True)
        assert publication["clock_labels"]["scheduled_release_at"] == "RUN_VIRTUAL_SCHEDULED"
        assert publication["clock_labels"]["published_at"] == "GATEWAY_STAMPED_RUN_VIRTUAL"
        closing = publication["reports"][1]
        assert (closing["state"], closing["scheduled_release_at"], closing["published_at"]) == (
            PENDING, "2026-09-30T15:05:00Z", None,
        )
        # The stub Stage has no envelope for m-1, so the actual instant is
        # unknown (null) - never the scheduled instant standing in for it.
        assert publication["reports"][0]["published_at"] is None
        assert "SECRET-TEXT" not in response.text and "soc-publication-delay" not in response.text

    def test_an_unreadable_schedule_is_not_an_empty_queue(self, tmp_path, legacy_root) -> None:
        client, execution, run_id = self.client_with_draft(tmp_path, legacy_root)
        execution.schedule_answer = LabControlRefused("PUBLICATION_SCHEDULE_UNREADABLE", run_id, "bad json")
        publication = client.get(f"/api/simulator-lab/runs/{run_id}/publication").json()["publication"]
        assert (publication["status"], publication["detail"], publication["reports"]) == ("UNREADABLE", "bad json", [])

    def test_an_executed_run_without_its_schedule_reads_schedule_missing(self, tmp_path, legacy_root) -> None:
        """answers-4 phase-3a Q3: lost durable state, distinct from NO_SCHEDULE."""
        client, execution, run_id = self.client_with_draft(tmp_path, legacy_root)
        execution.schedule_answer = LabControlRefused("PUBLICATION_SCHEDULE_MISSING", run_id, "schedule gone")
        publication = client.get(f"/api/simulator-lab/runs/{run_id}/publication").json()["publication"]
        assert (publication["status"], publication["detail"], publication["reports"]) == (
            "SCHEDULE_MISSING", "schedule gone", [],
        )
        execution.schedule_answer = None  # not yet started
        publication = client.get(f"/api/simulator-lab/runs/{run_id}/publication").json()["publication"]
        assert publication["status"] == "NO_SCHEDULE"

    def test_a_gateway_utc_run_has_no_schedule_to_read(self, tmp_path, legacy_root) -> None:
        payload = publication_schedule_payload("r", None, publication_clock="GATEWAY_UTC", status="NOT_SUPPORTED")
        assert payload["status"] == "NOT_SUPPORTED" and payload["reports"] == []

    def test_advance_reaches_the_port_and_reports_the_release_basis(self, tmp_path, legacy_root) -> None:
        client, execution, run_id = self.client_with_draft(tmp_path, legacy_root)
        execution.advance_answer = {"schedule": a_schedule(run_id), "publication_refused": None,
                                    "release_basis": "STORED_SCHEDULE_ONLY"}
        response = client.post(f"/api/simulator-lab/runs/{run_id}/publication/advance",
                               json={"instant": "2026-09-30T15:10:00Z"})
        assert response.status_code == 200, response.text
        body = response.json()
        assert ("advance_publication", run_id, "2026-09-30T15:10:00Z") in execution.calls
        assert body["release_basis"] == "STORED_SCHEDULE_ONLY"
        assert "does not regenerate" in body["release_basis_statement"]
        assert body["publication"]["pending_count"] == 1

    @pytest.mark.parametrize(
        "kind",
        ["PUBLICATION_AHEAD_OF_WORLD", "PUBLICATION_CLOCK_BACKWARD", "PUBLICATION_SCHEDULE_MISSING", "PUBLICATION_GAP"],
    )
    def test_a_refused_advance_is_a_typed_409(self, tmp_path, legacy_root, kind) -> None:
        client, execution, run_id = self.client_with_draft(tmp_path, legacy_root)
        execution.advance_answer = LabControlRefused(kind, run_id, "detail")
        response = client.post(f"/api/simulator-lab/runs/{run_id}/publication/advance",
                               json={"instant": "2026-09-30T15:10:00Z"})
        assert response.status_code == 409, response.text
        detail = response.json()["detail"]
        assert (detail["refusal_kind"], detail["advanced"]) == (kind, False)

    def test_a_publication_gap_refusal_names_both_instants(self, tmp_path, legacy_root) -> None:
        """`D-2026-10-09-s2-publication-gap-and-batch-boundary`: the 409 says
        where ordinary publication stopped and where the world reached."""
        client, execution, run_id = self.client_with_draft(tmp_path, legacy_root)
        execution.advance_answer = LabControlRefused(
            "PUBLICATION_GAP", run_id,
            "Ordinary publication is admitted through 2026-09-30T07:30:00Z; the world reached 2026-09-30T15:00:00Z.",
        )
        response = client.post(f"/api/simulator-lab/runs/{run_id}/publication/advance",
                               json={"instant": "2026-09-30T15:10:00Z"})
        assert response.status_code == 409, response.text
        detail = response.json()["detail"]
        assert detail["code"] == "EXECUTION_PUBLICATION_GAP"
        assert "2026-09-30T07:30:00Z" in detail["message"] and "2026-09-30T15:00:00Z" in detail["message"]
        assert "new run" in detail["message"]

    @pytest.mark.parametrize(
        ("through", "stopped", "complete", "state"),
        [
            ("2026-09-30T15:00:00Z", None, True, "COMPLETE"),
            ("2026-09-30T15:00:00Z", None, False, "CONTIGUOUS"),
            ("2026-09-30T07:30:00Z", None, True, "INCOMPLETE"),
            (None, None, True, "INCOMPLETE"),
            ("2026-09-30T03:45:00Z", "2026-09-30T04:00:00Z", True, "TERMINAL_GAP"),
        ],
    )
    def test_the_schedule_read_carries_the_ordinary_watermark(
        self, tmp_path, legacy_root, through, stopped, complete, state
    ) -> None:
        client, execution, run_id = self.client_with_draft(tmp_path, legacy_root)
        execution.schedule_answer = replace(
            a_schedule(run_id), admitted_through=through, ordinary_stopped_at=stopped,
            world_complete=complete, world_boundaries_completed=49,
        )
        publication = client.get(f"/api/simulator-lab/runs/{run_id}/publication").json()["publication"]
        assert (
            publication["admitted_through"], publication["ordinary_stopped_at"],
            publication["world_reached_instant"], publication["ordinary_publication"],
        ) == (through, stopped, "2026-09-30T15:00:00Z", state)
        assert publication["clock_labels"]["admitted_through"] == "RUN_VIRTUAL"
        # The advance answer carries the same read.
        execution.advance_answer = {"schedule": execution.schedule_answer, "publication_refused": None,
                                    "release_basis": "LIVE_SESSION"}
        body = client.post(f"/api/simulator-lab/runs/{run_id}/publication/advance",
                           json={"instant": "2026-09-30T15:10:00Z"}).json()
        assert (body["publication"]["ordinary_publication"], body["publication"]["admitted_through"]) == (state, through)

    def test_no_schedule_has_no_ordinary_state(self) -> None:
        payload = publication_schedule_payload("r", None, publication_clock="RUN_VIRTUAL")
        assert (payload["ordinary_publication"], payload["admitted_through"]) == (None, None)

    @pytest.mark.parametrize("body", [None, {}, {"instant": 5}, {"instant": "x", "extra": 1}])
    def test_a_malformed_advance_is_refused_before_the_port(self, tmp_path, legacy_root, body) -> None:
        client, execution, run_id = self.client_with_draft(tmp_path, legacy_root)
        response = client.post(f"/api/simulator-lab/runs/{run_id}/publication/advance", json=body)
        assert response.status_code == 422, response.text
        assert not any(call[0] == "advance_publication" for call in execution.calls)

    def test_an_unreachable_gateway_is_unavailable_not_a_zero_queue(self, tmp_path, legacy_root) -> None:
        client, _, _ = self.client_with_draft(tmp_path, legacy_root)
        gateway = client.get("/api/simulator-lab/gateway/diagnostics").json()["gateway"]
        assert gateway["status"] == "GATEWAY_UNAVAILABLE" and gateway["detail"] == "connection refused"
        assert gateway["current"] is None and gateway["last_emitted"] is None

    def test_an_available_read_keeps_current_and_last_emitted_apart(self) -> None:
        read = {"status": "AVAILABLE", "detail": None, "diagnostics": {
            "site_id": "KOBO-001", "gateway_id": "g", "observed_at": "2026-10-09T10:00:00Z",
            "queue": {"queue_count": 3}, "clock_offset": {"value_ms": None, "provenance": None},
            "disk_pressure": {"level": "WARN", "provenance": "INJECTED_FAULT_FIXTURE"},
            "config": {"text": "{...}", "sha256": "cd" * 32, "cadence_seconds": 60},
            "diagnostics": [{"diagnostic_sequence": 2}, {"diagnostic_sequence": 1}],
            "upload": "PENDING",
        }}
        payload = gateway_diagnostics_payload(read)
        assert payload["status"] == "AVAILABLE" and payload["observed_at_clock"] == "GATEWAY_REAL_UTC"
        assert payload["last_emitted"] == {"diagnostic_sequence": 2}
        assert payload["current"]["disk_pressure"]["provenance"] == "INJECTED_FAULT_FIXTURE"
        assert payload["current"]["clock_offset"]["value_ms"] is None
        assert "text" not in payload["current"]["config"]
        assert "not that a physical device or asset is healthy" in payload["statement"]
