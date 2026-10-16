"""S4-05b phase 1: the Lab release step publishes a registered run's still-STAGED sealed batches first.

`runs/registered_release.py` (S4-05a carry N-L1). Database-free: the ledger is a fake; the real Postgres path is
covered in `test_s4_power_demo_case_postgres.py`.
"""

from __future__ import annotations

import pytest
from assetops_contracts.lab_projection import LAB_CONTROL_REFUSAL_STATEMENTS, LAB_CONTROL_REFUSALS, LabControlRefused

from assetops_backend.evidence.publication import PublicationRefused, Registered
from assetops_backend.runs import registered_release as rr


class Batch:
    def __init__(self, batch_id, state):
        self.batch_id, self.state = batch_id, state
        self.payload_text, self.sha256, self.message_ids = "{}", "0" * 64, ()


class Stage:
    def __init__(self, *batches):
        self.run_id, self.status, self.envelopes, self.batches = "run-1", "STAGED", (), batches


class Run:
    run_id = "run-1"


def test_the_refusal_kind_has_a_statement() -> None:
    assert rr.SOURCE_PUBLICATION_REFUSED in LAB_CONTROL_REFUSALS
    assert rr.SOURCE_PUBLICATION_REFUSED in LAB_CONTROL_REFUSAL_STATEMENTS


def test_only_unreleased_batches_are_offered_and_an_all_released_run_publishes_nothing(monkeypatch) -> None:
    offered = []

    def attest(run, stage):
        offered.append(tuple(b.batch_id for b in stage.batches))
        return "attestation"

    monkeypatch.setattr(rr, "run_attestation", attest)
    monkeypatch.setattr(rr, "register_run", lambda ledger, a: (Registered(__import__("uuid").uuid4(), True),))
    publisher = rr.RegisteredRunPublisher(lambda: object())
    assert len(publisher.publish(Run(), Stage(Batch("b1", "STAGED"), Batch("b2", "READY")))) == 1
    assert offered == [("b1",)]
    assert publisher.publish(Run(), Stage(Batch("b2", "READY"), Batch("b3", "ACKED"))) == ()
    assert offered == [("b1",)]


@pytest.mark.parametrize("error", [PublicationRefused("RUN_NOT_STAGED", "partial"), RuntimeError("down")])
def test_any_publication_failure_refuses_the_release(monkeypatch, error) -> None:
    def fail(*_):
        raise error

    monkeypatch.setattr(rr, "run_attestation", lambda run, stage: "attestation")
    monkeypatch.setattr(rr, "register_run", fail)
    with pytest.raises(LabControlRefused) as refused:
        rr.RegisteredRunPublisher(lambda: object()).publish(Run(), Stage(Batch("b1", "STAGED")))
    assert refused.value.kind == rr.SOURCE_PUBLICATION_REFUSED


def test_without_a_database_the_composed_publisher_refuses() -> None:
    with pytest.raises(LabControlRefused) as refused:
        rr.publisher_for(None).publish(Run(), Stage(Batch("b1", "STAGED")))
    assert refused.value.detail.startswith("LEDGER_UNAVAILABLE")


@pytest.mark.parametrize("status", ["GATEWAY_UNAVAILABLE", "SEALING_PENDING", "SEALING_REFUSED", ""])
def test_an_unreadable_or_partly_sealed_stage_refuses_the_whole_release(monkeypatch, status) -> None:
    """Review L1 and D-2026-10-16-s405b-label item 2: an unreadable Stage (no batches visible) or a partly sealed
    one is refused before any registration, never released as far as sealed or without a publication."""
    called = []
    monkeypatch.setattr(rr, "run_attestation", lambda run, stage: called.append("attest") or "attestation")
    monkeypatch.setattr(rr, "register_run", lambda ledger, a: called.append("register") or ())
    stage = Stage(Batch("b1", "STAGED")) if status.startswith("SEALING") else Stage()
    stage.status = status
    with pytest.raises(LabControlRefused) as refused:
        rr.RegisteredRunPublisher(lambda: object()).publish(Run(), stage)
    assert refused.value.kind == rr.SOURCE_PUBLICATION_REFUSED
    assert "STAGE_NOT_ATTESTABLE" in refused.value.detail and called == []


@pytest.mark.parametrize("status", ["NOT_STAGED", "HELD"])
def test_a_readable_stage_with_nothing_admitted_publishes_nothing(status) -> None:
    stage = Stage()
    stage.status = status
    assert rr.RegisteredRunPublisher(lambda: object()).publish(Run(), stage) == ()
