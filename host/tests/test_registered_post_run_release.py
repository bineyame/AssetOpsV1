"""S2-01c phase 3a: a delayed report still pending when the world run completes.

`D-2026-10-09-s2-publication-clock-post-run-release` (answers-3 Q3, Q5). The
shipped `kobo-daytime-post-run-publication` v1 holds the last in-interval
state-of-charge sample - the world's reading at its last instant, source
15:00 - until 15:05, after the world end. A real registered KOBO-001 Draft on `registered-kobo-publication`
v2 runs to completion through a real gateway process with that report PENDING
(no V3 envelope, no sequence). Only an explicit post-run publication-clock
advance releases it - here after a Lab host restart with no live session, from
the durable Lab-private schedule's stored text - with its source time and value
unchanged and the gateway's actual virtual admission instant as `published_at`.
Retries and a gateway restart reuse the same identity and bytes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_registered_publication_delay as delay  # noqa: E402
from gateway_process import GatewayProcess  # noqa: E402
from publication_schedule import RELEASED  # noqa: E402

from assetops_contracts.source_envelope_v3 import parse_canonical_envelope_v3_text  # noqa: E402

registered = delay.registered
MANIFEST = json.loads(
    (Path(__file__).resolve().parents[1] / "fixtures" / "gateway-fault-scenarios.v2.json").read_text(encoding="utf-8")
)
POST_RUN = registered.parse_scenario_document(
    yaml.safe_load(
        (registered.REPOSITORY / "config" / "scenarios" / "kobo-daytime-post-run-publication.yaml").read_text(
            encoding="utf-8"
        )
    ),
    source="kobo-daytime-post-run-publication",
    origin="SHIPPED",
)
CLOSING, DUE, END = "2026-09-30T15:00:00Z", "2026-09-30T15:05:00Z", "2026-09-30T15:00:00Z"
BEFORE_DUE, PAST_DUE = "2026-09-30T15:03:00Z", "2026-09-30T15:10:00Z"


@pytest.fixture(scope="module")
def draft():
    store, _, _ = registered.converted()
    registry = registered.ImportedSiteRegistry(
        registered.FoundationService(store, "demo", registered.Clock(registered.NOW))
    )
    service = registered.RunSetupService(
        registered.FakeRuns(),
        registered.FakeSites(()),
        registered.FakeScenarios((registered.SCENARIO, POST_RUN)),
        model_profiles=(registered.DAYTIME_MINI_GRID_MODEL,),
        publication_profiles=(delay.LAB_PUBLICATION_PROFILE, delay.REGISTERED_KOBO_PUBLICATION_PROFILE, delay.V2),
        now=lambda: registered.text(registered.NOW),
        registered_bases=registered.RegisteredLabBasis(registry),
    )
    run = service.create_draft_run(
        registered.request(
            scenario_id=POST_RUN.scenario_id,
            scenario_version=POST_RUN.version.scenario_version,
            publication_profile={"profile_id": delay.V2.publication_profile_id, "profile_version": 2},
        )
    )
    assert run.execution_status == "READY" and run.blocking_reasons == (), run.blocking_reasons
    return run


def test_the_v2_manifest_describes_the_post_run_draft(draft, tmp_path) -> None:
    setup = MANIFEST["run_setup"]
    assert (MANIFEST["version"], MANIFEST["supersedes"]) == (2, 1)
    assert (setup["scenario"]["scenario_id"], setup["scenario"]["scenario_version"]) == (POST_RUN.scenario_id, 1)
    port = delay.host(tmp_path / "h", delay.RecordingLink(None))
    windows = [(w.event_id, w.start_offset_minutes, w.end_offset_minutes) for w in port._reporting_for(draft).delays]
    assert windows == [
        (w["event_id"], w["start_offset_minutes"], w["end_offset_minutes"])
        for w in MANIFEST["private_oracle"]["delay_windows"]
    ]
    public = json.dumps([MANIFEST["public_expected"], MANIFEST["delayed_cases"]])
    for window in MANIFEST["private_oracle"]["delay_windows"]:
        assert window["event_id"] not in public and window["scheduled_release_at"] not in public


def test_pending_at_completion_then_released_after_restart(draft, tmp_path) -> None:
    [_, case] = MANIFEST["delayed_cases"]
    assert (case["source_time"], case["advance_before_due"], case["advance_past_due"]) == (CLOSING, BEFORE_DUE, PAST_DUE)
    gateway = delay.gateway_for(tmp_path / "g", draft)
    recording = delay.RecordingLink(gateway.link)
    try:
        port = delay.host(tmp_path / "h", recording)
        port.start(draft)
        assert port.run_to_end(draft).status == "COMPLETED"

        # The world run is complete and the last in-interval sample is PENDING.
        schedule = port.publication_schedule(draft)
        assert schedule.world_complete and schedule.clock_instant == END
        [pending] = schedule.pending()
        assert (pending.source_time, pending.scheduled_release_at) == (CLOSING, DUE)
        view = port.registered_stage(draft)
        assert CLOSING not in delay.soc_envelopes(view), "a pending report has no envelope"
        assert len(view.envelopes) == MANIFEST["public_expected"]["admitted_envelopes_after_release"] - 1
        completed = delay.stage_bytes(view)
        sequences = sorted(e.sequence for e in view.envelopes)

        # Before due, with the live session: nothing released, no kernel step.
        early = port.advance_publication(draft, BEFORE_DUE)
        assert (early["publication_refused"], early["release_basis"]) == (None, "LIVE_SESSION")
        assert early["schedule"].pending() == (pending,)
        assert delay.stage_bytes(port.registered_stage(draft)) == completed
        assert port._sessions[draft.run_id].execution.boundaries[-1].offset_minutes == 720
        port.forget(draft.run_id)  # Lab host restart: no live session survives
    finally:
        gateway.kill()

    restarted = GatewayProcess(gateway.config)
    try:
        assert restarted.ready
        again = delay.host(tmp_path / "h", delay.RecordingLink(restarted.link))
        stored = again.publication_schedule(draft)
        assert stored.clock_instant == BEFORE_DUE and stored.pending() == (pending,)
        assert delay.stage_bytes(again.registered_stage(draft)) == completed

        # Skip past due: released from the stored schedule only, stamped with
        # the actual virtual admission instant, never the scheduled 15:15.
        answer = again.advance_publication(draft, PAST_DUE)
        assert (answer["publication_refused"], answer["release_basis"]) == (None, "STORED_SCHEDULE_ONLY")
        view = again.registered_stage(draft)
        late = delay.soc_envelopes(view)[CLOSING]
        assert (late.source_time, late.published_at) == (CLOSING, case["expected_published_at"])
        assert late.published_at != DUE
        submitted = json.loads(pending.report_text)  # stored before the world completed
        assert (submitted["source_time"], submitted["value"]) == (late.source_time, str(late.value))
        assert len(view.envelopes) == MANIFEST["public_expected"]["admitted_envelopes_after_release"]
        assert (len(view.holds), sorted(e.sequence for e in view.envelopes)[:-1]) == (0, sequences)
        [released] = [d for d in again.publication_schedule(draft).delayed if d.source_time == CLOSING]
        assert (released.state, released.released_at_clock, released.message_id, released.report_text) == (
            RELEASED, PAST_DUE, late.message_id, pending.report_text,
        )
        # The world was not re-run: the stored artifact still ends at 720.
        assert again.projection(draft).status == "COMPLETED"

        # Repeat and later advances, and another gateway restart: same bytes.
        once = delay.stage_bytes(view)
        assert again.advance_publication(draft, PAST_DUE)["publication_refused"] is None
        assert again.advance_publication(draft, "2026-09-30T16:00:00Z")["publication_refused"] is None
        assert delay.stage_bytes(again.registered_stage(draft)) == once
    finally:
        restarted.kill()

    third = GatewayProcess(gateway.config)
    try:
        assert third.ready
        reread = delay.host(tmp_path / "h", third.link)
        assert delay.stage_bytes(reread.registered_stage(draft)) == once
        for e in reread.registered_stage(draft).envelopes:
            text = e.envelope_text
            assert "soc-publication-delay" not in text and DUE not in text
            envelope = parse_canonical_envelope_v3_text(text)
            assert envelope.published_at >= envelope.source_time
    finally:
        third.kill()

    sent = json.dumps(recording.requests)
    for private in ("soc-publication-delay", "scheduled_release", DUE, "delay_event"):
        assert private not in sent


def test_an_executed_run_without_a_stored_schedule_refuses(draft, tmp_path) -> None:
    """Q5: nothing is reconstructed from the scenario when the schedule is gone."""
    gateway = delay.gateway_for(tmp_path / "g", draft)
    try:
        port = delay.host(tmp_path / "h", gateway.link)
        port.start(draft)
        port.step(draft, boundaries=4, from_boundary=0)
        port.forget(draft.run_id)
        again = delay.host(tmp_path / "h", gateway.link)
        path = again._schedules.path(draft.run_id)
        assert path.exists()
        path.unlink()
        before = delay.stage_bytes(again.registered_stage(draft))
        delay.refused("PUBLICATION_SCHEDULE_MISSING", lambda: again.advance_publication(draft, "2026-09-30T04:00:00Z"))
        assert delay.stage_bytes(again.registered_stage(draft)) == before
    finally:
        gateway.kill()
