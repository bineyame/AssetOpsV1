"""S2-01b phase 2: a registered Kobo run publishes through the separate gateway.

A real S2-01a registered Draft (KOBO-001 converted into the in-memory Foundation
store, as `test_registered_kobo_execution` builds it) runs in the Lab host while
a real `python -m assetops_gateway serve` process holds the SQLite outbox. The
host reaches it only over the authenticated local channel.
"""

from __future__ import annotations

import json
import sqlite3
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend" / "tests"))

import test_s2_registered_basis as registered  # noqa: E402
from gateway_process import GatewayProcess, provisioning_from_snapshot, write_config  # noqa: E402
from gateway_publication import (  # noqa: E402
    PublicationRefused,
    RegisteredGatewayPublisher,
    report_texts,
)
from lab_execution import HostLabExecution, YamlExecutionArtifacts, generate_observations  # noqa: E402
from source_stages import JsonSourceStages  # noqa: E402

from assetops_contracts.gateway_report import DEVICE_REPORT_SCHEMA_ID, DeviceReport, device_report_text  # noqa: E402
from assetops_contracts.ingestion_batch_v2 import parse_canonical_batch_v2_text  # noqa: E402
from assetops_contracts.source_envelope_v3 import parse_canonical_envelope_v3_text  # noqa: E402
from assetops_gateway.ipc import GatewayRequestRefused  # noqa: E402

REPORT_KEYS = {
    "schema", "report_key", "device_id", "signal_id", "source_time", "measurement",
    "interval_start", "value", "unit", "quality", "unavailable_reason",
}
PRIVATE = ("cause", "oracle", "intent", "private", "scenario", "world", "kernel")


@pytest.fixture(scope="module")
def draft():
    store, _, _ = registered.converted()
    return registered.setup_service(store).create_draft_run(registered.request())


class RecordingLink:
    """The channel as the host uses it, with every request kept for inspection."""

    def __init__(self, link) -> None:
        self.link = link
        self.requests: list[tuple[str, dict]] = []

    def call(self, op, body=None):
        self.requests.append((op, json.loads(json.dumps(body or {}))))
        return self.link.call(op, body)


@pytest.fixture
def gateway(tmp_path, draft):
    config = write_config(tmp_path / "gateway", provisioning_from_snapshot(draft.registered_basis.snapshot_canonical))
    process = GatewayProcess(config)
    assert process.ready, process.first_line
    yield process
    process.kill()


def host(root: Path, link) -> HostLabExecution:
    return HostLabExecution(
        artifacts=YamlExecutionArtifacts(root),
        stages=JsonSourceStages(root / "stages"),
        gateway=None if link is None else RegisteredGatewayPublisher(link),
    )


def complete(draft, root: Path, link) -> HostLabExecution:
    port = host(root, link)
    port.start(draft)
    assert port.run_to_end(draft).status == "COMPLETED"
    return port


def stage_bytes(view) -> dict:
    return {
        "envelopes": [(e.message_id, e.source_id, e.sequence_epoch, e.sequence, e.envelope_text, e.sha256,
                       e.state, e.batch_id, e.ordinal) for e in view.envelopes],
        "batches": [(b.batch_id, b.source_id, b.payload_text, b.sha256, b.state, b.message_ids) for b in view.batches],
        "holds": [(h.kind, h.field, h.device_id, h.signal_id) for h in view.holds],
        "depth": view.queue_depth_by_state,
    }


def test_a_registered_run_stages_source_specific_v3_batches_from_the_real_snapshot(draft, gateway, tmp_path) -> None:
    started = time.perf_counter()
    port = complete(draft, tmp_path / "host", gateway.link)
    elapsed = time.perf_counter() - started
    view = port.registered_stage(draft)
    basis = draft.registered_basis
    assert view.status == "STAGED" and view.upload_state == "PENDING"
    assert view.snapshot_sha256 == basis.snapshot_sha256 and view.site_id == basis.site_record_id
    # Open question `.agent/S2-01b-questions-2.md` Q1: a simulated reading whose
    # exact value is a non-terminating ratio cannot be a V3 canonical decimal.
    # Fail-closed default: it is an inspectable INVALID_VALUE hold, never a
    # rounded (invented) reading, and it allocates no sequence.
    assert view.holds, "the real Kobo series has ratio readings; the hold set must not be empty"
    assert {(h.kind, h.field) for h in view.holds} == {("INVALID_VALUE", "value")}
    assert all("/" in h.detail for h in view.holds)
    assert view.envelopes and view.queue_depth_by_state == {"STAGED": len(view.envelopes)}
    assert {e.snapshot_sha256 for e in view.envelopes} == {basis.snapshot_sha256}
    snapshot = json.loads(basis.snapshot_canonical)
    source_of = {(b["device_id"], b["signal_id"]): b["source_id"] for b in snapshot["bindings"]}
    session = port._sessions[draft.run_id]
    reported = {(s.device_id, s.signal_id) for s in session.reporting.signals}
    sources = {source_of[pair] for pair in reported}
    # Five Kobo devices report in the daytime profile: five source streams.
    assert len(sources) == 5 and {e.source_id for e in view.envelopes} == sources
    for batch in view.batches:
        parsed = parse_canonical_batch_v2_text(batch.payload_text)
        assert parsed.source_id == batch.source_id
        assert {parse_canonical_envelope_v3_text(t).source_id for t in parsed.envelopes} == {batch.source_id}
        assert list(parsed.envelopes) == [e.envelope_text for e in sorted(
            (e for e in view.envelopes if e.batch_id == batch.batch_id), key=lambda e: e.ordinal)]
        assert parsed.foundation_valid_from == json.loads(basis.snapshot_canonical)["foundation"]["valid_from"]
        assert batch.state == "STAGED" and batch.attempt_count == 0
    assert {b.source_id for b in view.batches} == sources
    # Per source, sequences are 1..n with no gap: nothing was allocated twice.
    for source in sources:
        assert sorted(e.sequence for e in view.envelopes if e.source_id == source) == list(
            range(1, 1 + sum(1 for e in view.envelopes if e.source_id == source))
        )
    # No file-backed Stage was written for the registered run.
    assert not (tmp_path / "host" / "stages" / f"{draft.run_id}.json").exists()
    # Full run plus a whole-series replay per step stays fast enough for the Lab.
    assert elapsed < 60, elapsed


def test_replay_and_both_restarts_keep_identity_and_bytes(draft, gateway, tmp_path) -> None:
    port = complete(draft, tmp_path / "host", gateway.link)
    before = stage_bytes(port.registered_stage(draft))
    session = port._sessions[draft.run_id]
    observations = generate_observations(session.execution.boundaries, session.reporting)
    replay = RegisteredGatewayPublisher(gateway.link).publish(
        draft.run_id, draft.registered_basis, observations, interval_minutes=15
    )
    assert replay.admitted == 0 and replay.already_admitted == len(before["envelopes"])
    assert replay.held == len(before["holds"]), "a replayed refused report is the same hold again"
    assert replay.batch_ids == ()
    gateway.kill()
    unavailable = host(tmp_path / "host", gateway.link).registered_stage(draft)
    assert unavailable.status == "GATEWAY_UNAVAILABLE" and unavailable.envelopes == ()
    restarted = GatewayProcess(gateway.config)
    try:
        assert restarted.ready
        # A new host over the same artifacts stands for a host restart.
        after = stage_bytes(host(tmp_path / "host", restarted.link).registered_stage(draft))
        assert after == before
    finally:
        restarted.kill()


def test_only_public_report_text_and_the_frozen_snapshot_cross_the_channel(draft, gateway, tmp_path) -> None:
    recording = RecordingLink(gateway.link)
    complete(draft, tmp_path / "host", recording)
    ops = {op for op, _ in recording.requests}
    assert ops == {"identity", "activate", "admit", "seal"}
    for op, body in recording.requests:
        if op == "activate":
            assert body["snapshot_text"] == draft.registered_basis.snapshot_canonical
            assert body["claimed"]["snapshot_sha256"] == draft.registered_basis.snapshot_sha256
        if op == "admit":
            assert set(body) == {"snapshot_sha256", "lab_run_ref", "reports"}
            for text in body["reports"]:
                report = json.loads(text)
                assert set(report) == REPORT_KEYS and report["schema"]["id"] == DEVICE_REPORT_SCHEMA_ID
                assert draft.run_id not in text
                assert not any(word in text.lower() for word in PRIVATE), text


def test_a_host_crash_mid_series_resumes_without_reallocating(draft, gateway, tmp_path) -> None:
    port = complete(draft, tmp_path / "host", None)  # executes, but stages nothing
    session = port._sessions[draft.run_id]
    observations = generate_observations(session.execution.boundaries, session.reporting)
    publisher = RegisteredGatewayPublisher(gateway.link)
    half = len(observations) // 2
    first = publisher.publish(draft.run_id, draft.registered_basis, observations[:half], interval_minutes=15)
    # The host dies here; a new one replays the whole series.
    whole = publisher.publish(draft.run_id, draft.registered_basis, observations, interval_minutes=15)
    assert whole.already_admitted == first.admitted and whole.admitted > 0
    view = publisher.stage(draft.run_id, draft.registered_basis, execution_status="COMPLETED")
    by_source: dict[str, list[int]] = {}
    for e in view.envelopes:
        by_source.setdefault(e.source_id, []).append(e.sequence)
    for sequences in by_source.values():
        assert sorted(sequences) == list(range(1, len(sequences) + 1))


def test_a_gateway_killed_after_enqueue_and_after_seal_keeps_rows_and_bytes(draft, gateway, tmp_path) -> None:
    port = complete(draft, tmp_path / "host", None)
    session = port._sessions[draft.run_id]
    observations = generate_observations(session.execution.boundaries, session.reporting)
    texts = report_texts(draft.run_id, draft.registered_basis.snapshot_sha256, observations, 15)
    publisher = RegisteredGatewayPublisher(gateway.link)
    publisher.publish(draft.run_id, draft.registered_basis, [], interval_minutes=15)  # activate only
    admitted = gateway.link.call(
        "admit", {"snapshot_sha256": draft.registered_basis.snapshot_sha256, "lab_run_ref": draft.run_id,
                  "reports": texts[:50]}
    )
    gateway.kill()  # after the enqueue commit, before sealing
    second = GatewayProcess(gateway.config)
    try:
        enqueued = stage_bytes(publisher.__class__(second.link).stage(draft.run_id, draft.registered_basis,
                                                                      execution_status="COMPLETED"))
        expected = sum(a["outcome"] == "ADMITTED" for a in admitted["admissions"])
        assert expected > 0 and len(enqueued["envelopes"]) == expected and enqueued["batches"] == []
        sealed = second.link.call("seal")["batch_ids"]
        assert sealed
        before = stage_bytes(RegisteredGatewayPublisher(second.link).stage(
            draft.run_id, draft.registered_basis, execution_status="COMPLETED"))
        assert [e[:6] for e in before["envelopes"]] == [e[:6] for e in enqueued["envelopes"]]
    finally:
        second.kill()  # after the seal commit
    third = GatewayProcess(gateway.config)
    try:
        after = stage_bytes(RegisteredGatewayPublisher(third.link).stage(
            draft.run_id, draft.registered_basis, execution_status="COMPLETED"))
        assert after == before
    finally:
        third.kill()


def test_a_same_time_distinct_report_and_refused_inputs(draft, gateway, tmp_path) -> None:
    complete(draft, tmp_path / "host", gateway.link)
    basis = draft.registered_basis
    db = sqlite3.connect(gateway.database)
    before = db.execute("SELECT count(*), max(sequence) FROM envelope_outbox").fetchone()
    existing = parse_canonical_envelope_v3_text(
        db.execute("SELECT envelope_text FROM envelope_outbox WHERE envelope_text LIKE '%\"signal_id\":\"state-of-charge\"%' "
                   "ORDER BY sequence LIMIT 1").fetchone()[0]
    )

    def report(**changes) -> str:
        fields = dict(report_key="probe-distinct", device_id=existing.device_id, signal_id=existing.signal_id,
                      source_time=existing.source_time, measurement=existing.measurement,
                      interval_start=existing.interval_start, value="12.5", unit=existing.unit,
                      quality="GOOD", unavailable_reason=None)
        fields.update(changes)
        return device_report_text(DeviceReport(**fields))

    answer = gateway.link.call("admit", {"snapshot_sha256": basis.snapshot_sha256, "lab_run_ref": "probe",
                                         "reports": [report(),
                                                     report(report_key="probe-unknown", signal_id="no-such-signal"),
                                                     report(report_key="probe-unit", unit="MW")]})
    outcomes = answer["admissions"]
    assert outcomes[0]["outcome"] == "ADMITTED" and outcomes[0]["message_id"] != existing.message_id
    assert [(o["outcome"], o["kind"]) for o in outcomes[1:]] == [("HELD", "UNKNOWN_CHANNEL"), ("HELD", "UNIT_INCOMPATIBLE")]
    after = db.execute("SELECT count(*) FROM envelope_outbox").fetchone()[0]
    assert after == before[0] + 1, "a refused input allocated a sequence"
    holds = gateway.link.call("run_stage", {"lab_run_ref": "probe"})["holds"]
    assert {(h["kind"], h["field"]) for h in holds} == {("UNKNOWN_CHANNEL", "device_id/signal_id"), ("UNIT_INCOMPATIBLE", "unit")}
    db.close()


def test_a_gateway_for_another_site_or_none_stages_nothing_and_says_why(draft, tmp_path) -> None:
    provisioning = provisioning_from_snapshot(
        draft.registered_basis.snapshot_canonical, site_id="99999999-9999-4999-8999-999999999999"
    )
    other = GatewayProcess(write_config(tmp_path / "other", provisioning))
    try:
        port = complete(draft, tmp_path / "host", other.link)
        notes = port._sessions[draft.run_id].staging_notes
        assert notes and "WRONG_SITE" in notes[0]
        assert port.registered_stage(draft).status == "NOT_STAGED"
        with pytest.raises(PublicationRefused):
            RegisteredGatewayPublisher(other.link).publish(
                draft.run_id, draft.registered_basis, [], interval_minutes=15
            )
    finally:
        other.kill()
    none = complete(draft, tmp_path / "none", None)
    view = none.registered_stage(draft)
    assert view.status == "GATEWAY_UNAVAILABLE" and view.envelopes == ()
    assert not (tmp_path / "none" / "stages" / f"{draft.run_id}.json").exists()


def test_a_kobo_enum_report_travels_end_to_end_under_the_real_map(draft, gateway) -> None:
    """The daytime profile (publication profile 3) does not report generator
    status, so a public `DeviceObservation` for it is adapted and admitted
    directly, under the real registered snapshot and its ENUM map."""
    from assetops_contracts.observation import DeviceObservation

    basis = draft.registered_basis
    publisher = RegisteredGatewayPublisher(gateway.link)
    publisher.publish(draft.run_id, basis, [], interval_minutes=15)  # activation

    def observed(value: str, at: str) -> DeviceObservation:
        return DeviceObservation(
            device_id="generator-controller", signal_id="status", address="public-status",
            state_key="generator-state", reading_class="STATE_SIGNAL", at_offset_minutes=0,
            source_sample_time=at, outcome="REPORTED", reported_value=value, canonical_unit="state",
        )

    result = publisher.publish(
        "enum-probe", basis,
        [observed("RUNNING", "2026-09-30T05:00:00Z"), observed("STOPPED", "2026-09-30T05:15:00Z"),
         observed("running", "2026-09-30T05:30:00Z")],
        interval_minutes=15,
    )
    assert (result.admitted, result.held) == (2, 1)
    view = publisher.stage("enum-probe", basis, execution_status="COMPLETED")
    values = [parse_canonical_envelope_v3_text(e.envelope_text) for e in view.envelopes]
    assert [(v.value, v.unit, v.family) for v in values] == [("RUNNING", "state", "MEASUREMENT"),
                                                            ("STOPPED", "state", "MEASUREMENT")]
    # A label outside the map is held with its field, never renamed to fit.
    assert [(h.kind, h.field) for h in view.holds] == [("INVALID_ENUM", "value")]


def test_a_later_basis_opens_new_source_batches_and_leaves_the_old_bytes(tmp_path) -> None:
    store, result, _ = registered.converted()
    service = registered.setup_service(store)
    first = service.create_draft_run(registered.request())
    process = GatewayProcess(write_config(tmp_path / "gw", provisioning_from_snapshot(
        first.registered_basis.snapshot_canonical)))
    try:
        assert process.ready
        old = stage_bytes(complete(first, tmp_path / "a", process.link).registered_stage(first))
        registered.publish_reserve(store, result, 40)
        second = service.create_draft_run(registered.request(
            interval={"start_time": "2026-10-05T03:00:00Z", "end_time": "2026-10-05T15:00:00Z"},
            foundation_version=4))
        assert second.registered_basis.snapshot_sha256 != first.registered_basis.snapshot_sha256
        later = complete(second, tmp_path / "b", process.link).registered_stage(second)
        assert later.batches and {b.snapshot_sha256 for b in later.batches} == {second.registered_basis.snapshot_sha256}
        assert not {b.batch_id for b in later.batches} & {b[0] for b in old["batches"]}
        for batch in later.batches:
            assert parse_canonical_batch_v2_text(batch.payload_text).foundation_version == 4
        # Sequences continue per source across the basis change; nothing reused.
        assert min(e.sequence for e in later.envelopes) > 1
        again = stage_bytes(RegisteredGatewayPublisher(process.link).stage(
            first.run_id, first.registered_basis, execution_status="COMPLETED"))
        assert again == old
    finally:
        process.kill()


# --- F1 (fix round 1): the Stage claims sealing only when the ledger shows it ---


class _LedgerLink:
    """A stand-in channel answering with a fixed ledger document."""

    def __init__(self, document: dict, *, seal_refused: bool = False) -> None:
        self.document, self.seal_refused = document, seal_refused

    def call(self, op: str, body: dict | None = None) -> dict:
        if op == "identity":
            return {"tenant_id": "t", "site_id": "s", "gateway_id": "g"}
        if op == "seal" and self.seal_refused:
            raise GatewayRequestRefused("SEAL_REFUSED", None, "TOO_LARGE at batch")
        if op == "seal":
            return {"batch_ids": []}
        if op == "run_stage":
            return self.document
        return {"admissions": []}


class _Basis:
    tenant_id, site_record_id, snapshot_sha256, snapshot_canonical = "t", "s", "ab" * 32, "{}"
    foundation_revision_id = binding_set_id = binding_set_revision_id = "x"
    foundation_version = binding_set_version = 1


def _envelope(sequence: int, batch_id: str | None) -> dict:
    return {
        "message_id": f"m-{sequence}", "source_id": "src", "sequence_epoch": "1", "sequence": sequence,
        "source_time": "2026-10-01T08:00:00Z", "snapshot_sha256": "ab" * 32, "envelope_text": "{}",
        "sha256": "cd" * 32, "state": "STAGED", "batch_id": batch_id, "ordinal": None if batch_id is None else 0,
    }


_HOLD = {"hold_id": 1, "kind": "INVALID_VALUE", "field": "value", "detail": "d", "device_id": "d",
         "signal_id": "s", "source_time": None, "seen_count": 1}
_REFUSAL = {"source_id": "src", "sequence_epoch": "1", "snapshot_sha256": "ab" * 32, "message_id": "m-2",
            "kind": "TOO_LARGE", "field": "batch", "detail": "more than 1048576 bytes",
            "last_seen_at": "2026-10-01T09:00:00Z", "seen_count": 1, "outbox_state": "STAGED"}


def _document(envelopes, holds=(), refusals=()) -> dict:
    return {"lab_run_ref": "run", "sequence_epoch": "1", "envelopes": list(envelopes), "batches": [],
            "holds": list(holds), "queue_depth_by_state": {}, "seal_refusals": list(refusals)}


@pytest.mark.parametrize(
    ("document", "status"),
    [
        (_document([_envelope(1, "b-1")], [_HOLD]), "STAGED"),
        (_document([_envelope(1, "b-1"), _envelope(2, None)]), "SEALING_PENDING"),
        (_document([_envelope(1, "b-1"), _envelope(2, None)], refusals=[_REFUSAL]), "SEALING_REFUSED"),
        (_document([], [_HOLD]), "HELD"),
        (_document([]), "NOT_STAGED"),
    ],
)
def test_the_stage_status_follows_what_the_ledger_sealed(document, status) -> None:
    from assetops_contracts.gateway_stage import REGISTERED_STAGE_STATEMENTS

    view = RegisteredGatewayPublisher(_LedgerLink(document)).stage("run", _Basis(), execution_status="COMPLETED")
    assert view.status == status
    assert view.statement == REGISTERED_STAGE_STATEMENTS[status]
    if status != "STAGED":
        assert "sealed this run" not in view.statement
    assert [r.kind for r in view.seal_refusals] == [r["kind"] for r in document["seal_refusals"]]


def test_a_seal_refusal_is_a_typed_publication_refusal() -> None:
    publisher = RegisteredGatewayPublisher(_LedgerLink(_document([]), seal_refused=True))
    with pytest.raises(PublicationRefused) as refused:
        publisher.publish("run", _Basis(), [], interval_minutes=15)
    assert refused.value.kind == "SEAL_REFUSED"
