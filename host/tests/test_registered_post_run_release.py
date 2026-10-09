"""S2-01c phase 3a: a delayed report still pending when the world run completes.

`D-2026-10-09-s2-publication-clock-post-run-release` (answers-3 Q3, Q5). The
shipped `kobo-daytime-post-run-publication` v1 holds the closing-boundary
state-of-charge observation - the world's reading at its end instant, source
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

from assetops_gateway.ipc import GatewayUnavailable  # noqa: E402

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

        # The world run is complete and the closing-boundary observation is PENDING.
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
        # The complete-schedule control: no ordinary gap, so the stored-only
        # advance below is not refused PUBLICATION_GAP.
        assert (stored.ordinary_publication(), stored.admitted_through) == ("COMPLETE", END)
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


# --- ordered publication (`D-2026-10-09-s2-ordered-publication-and-closing-boundary`, B1)


def _undelayed_lag(view, schedule) -> list[tuple[str, str]]:
    """(source_time, published_at) pairs that differ, over every undelayed envelope."""
    delayed = {(d.device_id, d.signal_id, d.source_time) for d in schedule.delayed}
    pairs = [
        (env.source_time, env.published_at)
        for env in (parse_canonical_envelope_v3_text(e.envelope_text) for e in view.envelopes)
        if (env.device_id, env.signal_id, env.source_time) not in delayed
    ]
    assert pairs, "the measured set is not empty"
    return [p for p in pairs if p[0] != p[1]]


def _complete(port, draft, how: str) -> None:
    port.start(draft)
    if how == "run_to_end":
        assert port.run_to_end(draft).status == "COMPLETED"
    else:
        at = 0
        while port.step(draft, boundaries=1, from_boundary=at).status != "COMPLETED":
            at += 1
    assert port.advance_publication(draft, PAST_DUE)["publication_refused"] is None


def _published(root: Path, draft, how: str, link_wrapper=None):
    gateway = delay.gateway_for(root / "g", draft)
    try:
        link = gateway.link if link_wrapper is None else link_wrapper(gateway.link)
        port = delay.host(root / "h", link)
        _complete(port, draft, how)
        return port, delay.stage_bytes(port.registered_stage(draft)), port.registered_stage(draft)
    finally:
        gateway.kill()


def test_run_to_end_and_single_steps_publish_the_same_bytes_at_source_instants(draft, tmp_path) -> None:
    """The reviewer's probe: run_to_end used to stamp all 292 at 15:00Z."""
    port, whole, view = _published(tmp_path / "whole", draft, "run_to_end")
    _, stepped, _ = _published(tmp_path / "stepped", draft, "steps")
    assert len(view.envelopes) == MANIFEST["public_expected"]["admitted_envelopes_after_release"]
    assert _undelayed_lag(view, port.publication_schedule(draft)) == [], "an undelayed reading carries an undeclared publication delay"
    late = delay.soc_envelopes(view)[CLOSING]
    assert (late.source_time, late.published_at) == (CLOSING, PAST_DUE)
    assert whole == stepped, "envelope and batch identity/bytes depend on how the operator stepped"
    # Delayed order: released at the first reached boundary at/after its due
    # instant, ahead of the readings first observed at that boundary.
    midday = delay.soc_envelopes(view)["2026-09-30T07:00:00Z"]
    assert midday.published_at == "2026-09-30T07:15:00Z"
    at_release = [  # sequences are per source: compare within the SOC's source
        env.sequence
        for env in (parse_canonical_envelope_v3_text(e.envelope_text) for e in view.envelopes)
        if env.source_time == "2026-09-30T07:15:00Z" and env.source_id == midday.source_id
    ]
    assert at_release and midday.sequence < min(at_release)


class _FailingLink:
    """Answers GATEWAY_UNAVAILABLE on the nth ordered admission, once."""

    def __init__(self, link, fail_at: int) -> None:
        self.link, self.fail_at, self.seen = link, fail_at, 0

    def call(self, op, body=None):
        if op == "admit_at_run_clock":
            self.seen += 1
            if self.seen == self.fail_at:
                raise GatewayUnavailable("injected link loss")
        return self.link.call(op, body)


def test_a_retry_after_a_failed_pass_resumes_in_order_with_the_same_bytes(draft, tmp_path) -> None:
    _, clean, _ = _published(tmp_path / "clean", draft, "run_to_end")
    gateway = delay.gateway_for(tmp_path / "g", draft)
    try:
        link = _FailingLink(gateway.link, fail_at=20)
        port = delay.host(tmp_path / "h", link)
        port.start(draft)
        assert port.run_to_end(draft).status == "COMPLETED"
        notes = port._sessions[draft.run_id].staging_notes
        assert any("registered publication refused" in n for n in notes), notes
        partial = port.publication_schedule(draft)
        assert partial.admitted_through is not None and partial.admitted_through < END
        assert (partial.ordinary_publication(), partial.world_reached_instant) == ("INCOMPLETE", END)
        assert _undelayed_lag(port.registered_stage(draft), port.publication_schedule(draft)) == []
        # Retry at the reached instant, then a host restart and the post-run advance.
        assert port.advance_publication(draft, END)["publication_refused"] is None
        assert port.publication_schedule(draft).admitted_through == END
        assert port.publication_schedule(draft).ordinary_publication() == "COMPLETE"
        restarted = delay.host(tmp_path / "h", gateway.link)
        assert restarted.advance_publication(draft, PAST_DUE)["publication_refused"] is None
        assert delay.stage_bytes(restarted.registered_stage(draft)) == clean
    finally:
        gateway.kill()


def test_a_boundary_the_gateway_clock_has_passed_is_refused_not_stamped_late(draft, tmp_path) -> None:
    gateway = delay.gateway_for(tmp_path / "g", draft)
    try:
        port = delay.host(tmp_path / "h", gateway.link)
        port.start(draft)
        port.step(draft, boundaries=4, from_boundary=0)  # 03:00..03:45 published
        admitted = len(port.registered_stage(draft).envelopes)
        assert admitted > 0
        # Something moved this run's gateway clock past boundaries never admitted.
        gateway.link.call("advance_publication_clock", {"lab_run_ref": draft.run_id, "instant": "2026-09-30T05:00:00Z"})
        port.step(draft, boundaries=4, from_boundary=4)  # 04:00..04:45: the clock has passed them
        notes = port._sessions[draft.run_id].staging_notes
        assert any("PUBLICATION_INSTANT_PASSED" in n for n in notes), notes
        view = port.registered_stage(draft)
        assert len(view.envelopes) == admitted, "a missed boundary admitted nothing, and nothing after it"
        assert _undelayed_lag(view, port.publication_schedule(draft)) == []
        schedule = port.publication_schedule(draft)
        assert schedule.admitted_through == "2026-09-30T03:45:00Z"
        assert (schedule.ordinary_publication(), schedule.ordinary_stopped_at) == ("TERMINAL_GAP", "2026-09-30T04:00:00Z")
        gateway_clock = _gateway_run_clock(tmp_path / "g", draft.run_id)
        lab_clock = schedule.clock_instant
        assert port.run_to_end(draft).status == "COMPLETED"  # the world finishes; publication does not move
        assert len(port.registered_stage(draft).envelopes) == admitted
        completed = port.publication_schedule(draft)
        assert completed.world_complete and completed.clock_instant == lab_clock
        assert _gateway_run_clock(tmp_path / "g", draft.run_id) == gateway_clock
        assert any("PUBLICATION_GAP" in n for n in port._sessions[draft.run_id].staging_notes)
        # `D-2026-10-09-s2-terminal-publication-gap-closeout`: a LIVE advance on a
        # terminal run is a typed refusal before either publication clock moves;
        # no admission, seal or release, and no delayed report (07:00 due 07:10,
        # 15:00 due 15:05) leaps the gap.
        assert draft.run_id in port._sessions, "the live session survives"
        stage = delay.stage_bytes(port.registered_stage(draft))
        refusal = delay.refused("PUBLICATION_GAP", lambda: port.advance_publication(draft, PAST_DUE))
        assert "2026-09-30T03:45:00Z" in refusal.detail and "2026-09-30T04:00:00Z" in refusal.detail
        after = port.publication_schedule(draft)
        assert after == completed, "the Lab schedule (clock, watermark, pending reports) did not change"
        assert after.ordinary_publication() == "TERMINAL_GAP"
        assert all(d.state == "PENDING" for d in after.delayed) and after.delayed
        assert _gateway_run_clock(tmp_path / "g", draft.run_id) == gateway_clock
        assert delay.stage_bytes(port.registered_stage(draft)) == stage
        # The same instant again is refused too, never a quiet 200.
        delay.refused("PUBLICATION_GAP", lambda: port.advance_publication(draft, lab_clock))
        # And after a restart the stored-only advance refuses before anything moves.
        restarted = delay.host(tmp_path / "h", gateway.link)
        refusal = delay.refused("PUBLICATION_GAP", lambda: restarted.advance_publication(draft, "2026-09-30T16:00:00Z"))
        assert "2026-09-30T03:45:00Z" in refusal.detail and "2026-09-30T04:00:00Z" in refusal.detail
        assert restarted.publication_schedule(draft).clock_instant == lab_clock
    finally:
        gateway.kill()


def test_an_executed_run_without_its_schedule_reads_missing_not_empty(draft, tmp_path) -> None:
    """answers-4 phase-3a Q3: NO_SCHEDULE (None) before a start; afterwards a
    lost schedule refuses the read exactly as it refuses an advance."""
    gateway = delay.gateway_for(tmp_path / "g", draft)
    try:
        port = delay.host(tmp_path / "h", gateway.link)
        assert port.publication_schedule(draft) is None  # not started
        port.start(draft)
        assert port.run_to_end(draft).status == "COMPLETED"
        port._schedules.path(draft.run_id).unlink()
        restarted = delay.host(tmp_path / "h", gateway.link)
        delay.refused("PUBLICATION_SCHEDULE_MISSING", lambda: restarted.publication_schedule(draft))
        delay.refused("PUBLICATION_SCHEDULE_MISSING", lambda: restarted.advance_publication(draft, PAST_DUE))
    finally:
        gateway.kill()


# --- publication gap (`D-2026-10-09-s2-publication-gap-and-batch-boundary`, re-review R1)


def _gateway_run_clock(root: Path, run_id: str) -> str | None:
    """The gateway's persisted publication clock for this run, read directly."""
    import sqlite3

    database = root / "gateway.sqlite3"
    assert database.is_file(), database
    with sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True) as db:
        row = db.execute("SELECT instant FROM publication_clock WHERE lab_run_ref=?", (run_id,)).fetchone()
    return None if row is None else row[0]


def test_a_stored_only_advance_refuses_a_known_ordinary_gap_before_anything_moves(draft, tmp_path) -> None:
    """The reviewer's R1 probe: a failed pass, a host restart, a post-run
    advance. It used to release the 15:00 SOC at 15:10 straight after 07:30,
    skipping 178 ordinary readings for good with no sequence hole."""
    gateway = delay.gateway_for(tmp_path / "g", draft)
    try:
        port = delay.host(tmp_path / "h", _FailingLink(gateway.link, fail_at=20))
        port.start(draft)
        assert port.run_to_end(draft).status == "COMPLETED"
        port.forget(draft.run_id)  # Lab host restart

        recording = delay.RecordingLink(gateway.link)
        restarted = delay.host(tmp_path / "h", recording)
        before = restarted.publication_schedule(draft)
        assert before.world_complete and before.world_reached_instant == END
        assert before.admitted_through is not None and before.admitted_through < END
        assert before.ordinary_publication() == "INCOMPLETE" and before.ordinary_stopped_at is None
        assert before.pending(), "the measured set of delayed reports is not empty"
        stage = delay.stage_bytes(restarted.registered_stage(draft))
        assert stage[0] and stage[1], "the pre-gap envelopes and batches exist"
        gateway_clock = _gateway_run_clock(tmp_path / "g", draft.run_id)
        assert gateway_clock is not None
        recording.requests.clear()

        refusal = delay.refused("PUBLICATION_GAP", lambda: restarted.advance_publication(draft, PAST_DUE))
        assert before.admitted_through in refusal.detail and END in refusal.detail

        # No new envelope, no new batch, no publication-clock movement on either side.
        assert delay.stage_bytes(restarted.registered_stage(draft)) == stage
        assert _gateway_run_clock(tmp_path / "g", draft.run_id) == gateway_clock
        after = restarted.publication_schedule(draft)
        assert after == before, "the Lab schedule (clock, watermark, pending reports) did not change"
        mutating = {"activate", "admit", "admit_at_run_clock", "seal", "advance_publication_clock"}
        assert not [op for op, _ in recording.requests if op in mutating], recording.requests
        # Refused again at the same instant: still nothing, never a quiet release.
        delay.refused("PUBLICATION_GAP", lambda: restarted.advance_publication(draft, END))
        assert delay.stage_bytes(restarted.registered_stage(draft)) == stage
    finally:
        gateway.kill()


def test_a_live_session_that_lost_its_schedule_reads_and_advances_missing(draft, tmp_path) -> None:
    """questions-5 Q5: SCHEDULE_MISSING even with a live session, and a later
    live step does not silently rebuild the schedule."""
    gateway = delay.gateway_for(tmp_path / "g", draft)
    try:
        port = delay.host(tmp_path / "h", gateway.link)
        port.start(draft)
        port.step(draft, boundaries=4, from_boundary=0)
        path = port._schedules.path(draft.run_id)
        path.unlink()
        assert draft.run_id in port._sessions, "the live session survives"
        stage = delay.stage_bytes(port.registered_stage(draft))
        delay.refused("PUBLICATION_SCHEDULE_MISSING", lambda: port.publication_schedule(draft))
        delay.refused("PUBLICATION_SCHEDULE_MISSING", lambda: port.advance_publication(draft, "2026-09-30T03:45:00Z"))
        port.step(draft, boundaries=4, from_boundary=4)
        assert not path.exists(), "a live step rebuilt the lost schedule"
        notes = port._sessions[draft.run_id].staging_notes
        assert any("PUBLICATION_SCHEDULE_MISSING" in n for n in notes), notes
        assert delay.stage_bytes(port.registered_stage(draft)) == stage
        delay.refused("PUBLICATION_SCHEDULE_MISSING", lambda: port.publication_schedule(draft))
    finally:
        gateway.kill()
