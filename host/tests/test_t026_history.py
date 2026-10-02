"""T026 AC13, host side: records and held publications in persisted history.

History schema 3 adds two families. `records` holds every policy and operational
record that occurred by the boundary reached, at its occurrence, with whether
its channel published it; `publications` holds each publication a declared
delay held, as a new row at the boundary that released it. Both are append
families (`test_lab_history_prefix.py` proves their prefix and delta on the
degraded-evidence fixture). A schema-2 artifact still reads and discloses both
as not recorded.

The new numeric and enum report attempts (capability, generator status) are
`observation_attempts` rows, as every attempt already was; tested here only for
being present after a reload.
"""

from __future__ import annotations

import json

import pytest

from assetops_backend.simulator_lab_api import (
    history_delta_payload,
    history_payload,
)
from assetops_contracts.lab_history import (
    LAB_HISTORY_SCHEMA_VERSION,
    SCHEMA_2_UNRECORDED_STATEMENT,
)
from lab_execution import HostLabExecution, YamlExecutionArtifacts, project
from lab_history import HISTORY_MARKER, history_digest
from source_stages import JsonSourceStages

from test_t026_dispatch_evidence import (
    DEGRADED,
    draft,
    envelopes,
    with_entry,
    without,
)

SOC = ("battery-pcs-controller", "state-of-charge")
#: 07:00Z is offset 240 of the 03:00-11:00Z window; the hold ends at 250.
SOC_SOURCE, SOC_RELEASE = 240, 250


def a_lab(root) -> HostLabExecution:
    return HostLabExecution(
        artifacts=YamlExecutionArtifacts(root),
        stages=JsonSourceStages(root / "stages"),
    )


def finished(run, root):
    lab = a_lab(root)
    lab.start(run)
    lab.run_to_end(run)
    return lab


@pytest.fixture(scope="module")
def degraded_root(tmp_path_factory):
    root = tmp_path_factory.mktemp("t026-history")
    run = draft(DEGRADED)
    lab = finished(run, root)
    return run, root, lab


def test_a_held_publication_is_a_row_at_its_release_not_its_source(
    degraded_root,
) -> None:
    run, _, lab = degraded_root
    history = lab.history(run)
    assert history.history_schema_version == LAB_HISTORY_SCHEMA_VERSION == 3
    assert history.availability("publications") == "RECORDED"
    (held,) = history.publications
    assert (held.kind, held.device_id, held.signal_id) == ("READING", *SOC)
    assert held.source_time == "2026-09-22T07:00:00Z"
    assert held.published_at == "2026-09-22T07:10:03Z"
    assert (held.source_offset_minutes, held.released_offset_minutes) == (
        SOC_SOURCE,
        SOC_RELEASE,
    )
    assert held.held_minutes == 10
    assert held.delay_event_id == "soc-publication-delay"
    # The attempt at the source time is the same row it always was.
    (attempt,) = [
        a
        for a in history.attempts
        if (a.device_id, a.signal_id) == SOC and a.at_offset_minutes == SOC_SOURCE
    ]
    assert attempt.outcome == "REPORTED"
    assert attempt.source_sample_time == held.source_time


def test_a_publication_still_held_is_not_yet_a_fact(tmp_path) -> None:
    run = draft(DEGRADED)
    lab = a_lab(tmp_path)
    lab.start(run)
    session = lab._sessions[run.run_id]
    seen: dict[int, int] = {}
    while not session.execution.is_terminal:
        session.execution.advance(1)
        capture = lab._captured(session, project(session))
        seen[capture.recorded_through_offset] = len(capture.publications)
        if capture.recorded_through_offset == SOC_RELEASE:
            break
    assert seen[SOC_RELEASE - 5] == 0
    assert seen[SOC_RELEASE] == 1


#: Captured before the stage withheld held envelopes: the finished stage of the
#: degraded-evidence run must not change (329 envelopes, repr digest).
FINAL_STAGE_DIGEST = "0774c78ebff205a8323f378fb8776acd7413d4c4c702097c75f1174490abe87d"


def test_the_stage_withholds_a_held_envelope_until_the_run_reaches_its_release(
    tmp_path,
) -> None:
    run = draft(DEGRADED)
    lab = a_lab(tmp_path)
    lab.start(run)
    session = lab._sessions[run.run_id]

    def soc_at_source() -> list:
        return [
            e
            for e in lab.staged_envelopes(run).stage.envelopes
            if (e.device_id, e.signal_id) == SOC
            and e.source_time == "2026-09-22T07:00:00Z"
        ]

    reached = 0
    while reached < SOC_RELEASE:
        session.execution.advance(1)
        lab._stage(session)
        reached = session.execution.boundaries[-1].offset_minutes
        if reached < SOC_SOURCE:
            continue
        if reached < SOC_RELEASE:
            # Mid-hold: its source boundary is published, its release is not.
            assert soc_at_source() == [], reached
            assert all(
                e.published_at <= "2026-09-22T07:10:03Z"
                for e in lab.staged_envelopes(run).stage.envelopes
            )
    (released,) = soc_at_source()
    assert released.published_at == "2026-09-22T07:10:03Z"
    # Stepped to the end, the stage holds exactly the one-shot run's envelopes
    # (same sequences, same bytes); only the arrival order is the stepping's,
    # as it always was for a stepped run.
    lab.run_to_end(run)
    final = lab.staged_envelopes(run).stage.envelopes
    (tmp_path / "one").mkdir()
    whole = (
        finished(run, tmp_path / "one").staged_envelopes(run).stage.envelopes
    )
    assert sorted(final, key=lambda e: e.message_id) == sorted(
        whole, key=lambda e: e.message_id
    )
    assert released in final


def test_the_one_shot_final_stage_is_byte_identical_to_before_the_withholding(
    degraded_root,
) -> None:
    import hashlib

    run, _, lab = degraded_root
    final = lab.staged_envelopes(run).stage.envelopes
    assert len(final) == 329
    assert hashlib.sha256(repr(list(final)).encode()).hexdigest() == FINAL_STAGE_DIGEST


def test_the_history_agrees_with_the_stage_about_every_held_envelope(
    degraded_root,
) -> None:
    """The gateway's own rule, twice: no held row the stage lacks, none missing."""
    run, _, lab = degraded_root
    history = lab.history(run)
    staged = lab.staged_envelopes(run)
    delayed = {
        (e.device_id, e.signal_id, e.source_time, e.published_at)
        for e in staged.stage.envelopes
        if e.published_at[:-3] != e.source_time[:-3]
    }
    assert delayed == {
        (p.device_id, p.signal_id, p.source_time, p.published_at)
        for p in history.publications
    }


def test_records_are_rows_at_their_occurrence_with_their_outcome(
    degraded_root,
) -> None:
    run, _, lab = degraded_root
    history = lab.history(run)
    assert history.availability("records") == "RECORDED"
    policies = [r for r in history.records if r.family == "POLICY"]
    assert policies and all(r.at_offset_minutes == 0 for r in policies)
    assert all(r.policy_version is not None and r.policy_source for r in policies)
    (override,) = [r for r in history.records if r.family == "OPERATIONAL_RECORD"]
    # The degraded world's override record is missing: it occurred, and its
    # channel published nothing - none observed, not no override.
    assert override.outcome == "SUPPRESSED_BY_GAP"
    assert override.record_kind == "OVERRIDE_COMMAND"
    assert override.actor == "OPERATOR"
    assert not envelopes(staged := lab.staged_envelopes(run), family="OPERATIONAL_RECORD")
    assert staged.stage is not None


def test_a_delayed_override_record_is_a_record_row_and_a_held_row(tmp_path) -> None:
    delay = {
        "event_id": "override-record-delay",
        "sequence": 15,
        "offset_minutes": 120,
        "entry_kind": "EVENT",
        "category": "DATA_QUALITY",
        "description": "The override record is held five minutes.",
        "execution_role": "FORCING_INPUT",
        "state_key": "override-record-publication-delay@generator",
        "execution_requirement": "REQUIRED",
        "timing": {"shape": "WINDOW", "duration_minutes": 5},
    }

    def edit(document):
        without("override-record-missing")(document)
        with_entry(delay)(document)

    run = draft(DEGRADED, document_edit=edit)
    history = finished(run, tmp_path).history(run)
    (override,) = [r for r in history.records if r.family == "OPERATIONAL_RECORD"]
    assert (override.outcome, override.at_offset_minutes) == ("REPORTED", 120)
    (held,) = [p for p in history.publications if p.kind == "RECORD"]
    assert (held.source_offset_minutes, held.released_offset_minutes) == (120, 125)
    assert held.published_at == "2026-09-22T05:05:03Z"


def test_a_reload_reads_the_same_records_publications_and_new_attempts(
    degraded_root,
) -> None:
    run, root, lab = degraded_root
    live = lab.history(run)
    reloaded = a_lab(root).history(run)
    assert reloaded.source == "PERSISTED", reloaded.notes
    assert reloaded.history_schema_version == 3
    assert reloaded.records == live.records
    assert reloaded.publications == live.publications
    assert reloaded.attempts == live.attempts
    signals = {(a.device_id, a.signal_id) for a in reloaded.attempts}
    assert ("battery-pcs-controller", "discharge-capability") in signals
    assert ("pv-inverter-controller", "available-power") in signals
    statuses = [
        a for a in reloaded.attempts if a.canonical_unit == "state" and a.outcome == "REPORTED"
    ]
    assert statuses and all(isinstance(a.reported_value, str) for a in statuses)
    # The capability gap is recorded as suppressed attempts, not as readings.
    gap = [
        a
        for a in reloaded.attempts
        if (a.device_id, a.signal_id)
        == ("battery-pcs-controller", "discharge-capability")
        and a.outcome == "SUPPRESSED_BY_GAP"
    ]
    assert gap and all(a.reported_value is None for a in gap)


def test_the_wire_carries_both_families_and_the_delta_sends_a_release_once(
    degraded_root,
) -> None:
    run, _, lab = degraded_root
    history = lab.history(run)
    full = history_payload(history, run)
    assert full["publications"][0]["held_minutes"] == 10
    assert full["publications"][0]["released_offset_minutes"] == SOC_RELEASE
    assert {r["family"] for r in full["records"]} == {"POLICY", "OPERATIONAL_RECORD"}
    release_boundary = SOC_RELEASE // 5
    before = history_delta_payload(history, release_boundary, run)
    after = history_delta_payload(history, release_boundary + 1, run)
    assert len(before["publications"]) == 1
    assert after["publications"] == []


def _as_schema_2(path) -> None:
    """Rewrite one terminal artifact's history as schema 2 wrote it."""
    text = path.read_text(encoding="utf-8")
    head, tail = text.split(HISTORY_MARKER)
    document = json.loads(tail)
    document["history_schema_version"] = 2
    del document["records"], document["publications"]
    document["manifest"]["coverage"] = document["manifest"]["coverage"][:5]
    document["manifest"]["history_digest"] = history_digest(document)
    path.write_text(
        head + HISTORY_MARKER + json.dumps(document, sort_keys=True, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
    )


def test_a_schema_2_artifact_reads_and_discloses_both_as_not_recorded(
    tmp_path,
) -> None:
    run = draft(DEGRADED)
    live = finished(run, tmp_path).history(run)
    _as_schema_2(tmp_path / f"{run.run_id}.yaml")
    reloaded = a_lab(tmp_path).history(run)
    assert reloaded.source == "PERSISTED", reloaded.notes
    assert reloaded.history_schema_version == 2
    assert (reloaded.records, reloaded.publications) == ((), ())
    for family in ("records", "publications"):
        assert reloaded.availability(family) == "UNAVAILABLE"
    assert {
        c.statement for c in reloaded.coverage if c.availability == "UNAVAILABLE"
    } == {SCHEMA_2_UNRECORDED_STATEMENT}
    assert reloaded.attempts == live.attempts
    assert reloaded.samples == live.samples


@pytest.mark.parametrize("damage", ["schema-2-with-records", "schema-4"])
def test_a_history_claiming_another_schema_is_unreadable(tmp_path, damage) -> None:
    run = draft(DEGRADED)
    finished(run, tmp_path)
    path = tmp_path / f"{run.run_id}.yaml"
    head, tail = path.read_text(encoding="utf-8").split(HISTORY_MARKER)
    document = json.loads(tail)
    if damage == "schema-4":
        document["history_schema_version"] = 4
    else:
        document["history_schema_version"] = 2
        document["manifest"]["coverage"] = document["manifest"]["coverage"][:5]
    document["manifest"]["history_digest"] = history_digest(document)
    path.write_text(head + HISTORY_MARKER + json.dumps(document) + "\n", encoding="utf-8")
    before = path.read_bytes()
    reloaded = a_lab(tmp_path).history(run)
    assert reloaded.source == "HISTORY_UNREADABLE"
    assert path.read_bytes() == before


def test_a_profile_without_record_channels_states_records_not_applicable(
    tmp_path,
) -> None:
    run = draft("kobo-mini-grid-prolonged", model_version=2, profile_version=4)
    history = finished(run, tmp_path).history(run)
    assert history.availability("records") == "NOT_APPLICABLE"
    assert history.records == ()
    assert history.availability("publications") == "RECORDED"
    assert history.publications == ()
    reloaded = a_lab(tmp_path).history(run)
    assert reloaded.source == "PERSISTED", reloaded.notes
    assert reloaded.availability("records") == "NOT_APPLICABLE"


# --- AC14: no Lab disclosure says a staged status awaits staging -------------


def test_a_run_that_stages_its_status_no_longer_says_it_awaits_staging(
    tmp_path,
) -> None:
    from assetops_contracts.lab_projection import (
        GENERATOR_STATUS_REPORTED_NOT_STAGED,
        GENERATOR_STATUS_REPORTED_STAGED,
    )

    run = draft(DEGRADED)
    lab = a_lab(tmp_path)
    lab.start(run)
    generator = lab.run_to_end(run).electrical.generator
    assert generator.reported_status == GENERATOR_STATUS_REPORTED_STAGED
    assert generator.reported_status != GENERATOR_STATUS_REPORTED_NOT_STAGED
    assert "T026" not in generator.reported_status
    assert "not yet staged" not in generator.reported_status
    # Staged is not committed or accepted, and it does not claim to be.
    assert "not committed or accepted" in generator.reported_status
    staged = {
        (e.device_id, e.signal_id)
        for e in lab.staged_envelopes(run).stage.envelopes
    }
    assert ("generator-controller", "status") in staged
