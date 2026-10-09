"""S2-01c phase 2: the per-run virtual publication clock.

`D-2026-10-09-s2-simulated-publication-clock`: the gateway owns and persists one
forward-only clock per registered Lab run and stamps V3 `published_at` from it at
first admission. Outbox creation (queue age), contact and diagnostics stay on the
gateway's real UTC clock. A replay never re-stamps; an earlier target refuses;
the same target is idempotent; restart keeps the instant.
"""

from __future__ import annotations

import sqlite3
from datetime import timedelta
from pathlib import Path

import pytest
from conftest import EPOCH, GATEWAY, PROVISIONING, SITE, SRC_BMS, SRC_PV, report

from assetops_contracts.source_envelope_v3 import parse_canonical_envelope_v3_text
from assetops_gateway.service import RUN_VIRTUAL, GatewayRefused, GatewayService
from assetops_gateway.snapshot import Provisioning

RUN = "run-delay-1"
SOURCE = "2026-10-01T08:00:00Z"
DUE = "2026-10-01T08:10:00Z"
LATER = "2026-10-01T09:30:00Z"


def _rows(db_path: Path, sql: str, params: tuple = ()) -> list[tuple]:
    with sqlite3.connect(db_path) as db:
        return db.execute(sql, params).fetchall()


def _admit(gateway: GatewayService, active: str, text: str, run: str = RUN):
    return gateway.admit_texts([text], snapshot_sha256=active, lab_run_ref=run, publication_clock=RUN_VIRTUAL)[0]


def test_no_clock_admits_nothing(gateway, active: str, db_path: Path) -> None:
    with pytest.raises(GatewayRefused) as error:
        _admit(gateway, active, report(key="k1"))
    assert error.value.kind == "NO_PUBLICATION_CLOCK"
    assert _rows(db_path, "SELECT COUNT(*) FROM envelope_outbox") == [(0,)]
    assert _rows(db_path, "SELECT COUNT(*) FROM sequence_state") == [(0,)]
    assert _rows(db_path, "SELECT COUNT(*) FROM mapping_hold") == [(0,)]


def test_published_at_is_the_virtual_admission_instant_and_creation_stays_real(
    gateway, active: str, db_path: Path, clock
) -> None:
    assert gateway.advance_publication_clock(RUN, DUE) == {"lab_run_ref": RUN, "instant": DUE, "advanced": True}
    admission = _admit(gateway, active, report(key="k1", at=SOURCE))
    assert admission.outcome == "ADMITTED"
    text, created = _rows(
        db_path, "SELECT envelope_text, created_at FROM envelope_outbox WHERE message_id=?", (admission.message_id,)
    )[0]
    envelope = parse_canonical_envelope_v3_text(text)
    assert (envelope.source_time, envelope.published_at) == (SOURCE, DUE)
    # Real UTC: the gateway clock's NOW, a week after the virtual instants.
    assert created == "2026-10-08T12:00:00Z"
    clock.now += timedelta(seconds=45)
    assert gateway.local_diagnostics()["queue"]["oldest_queue_age_seconds"] == 45


def test_the_clock_moves_forward_only_and_repeats_are_idempotent(gateway, db_path: Path) -> None:
    gateway.advance_publication_clock(RUN, DUE)
    assert gateway.advance_publication_clock(RUN, DUE)["advanced"] is False
    with pytest.raises(GatewayRefused) as error:
        gateway.advance_publication_clock(RUN, "2026-10-01T08:09:59Z")
    assert error.value.kind == "PUBLICATION_CLOCK_BACKWARD"
    assert gateway.publication_clock(RUN) == DUE
    # Clocks are per run: another run's clock is independent.
    gateway.advance_publication_clock("run-other", "2026-01-01T00:00:00Z")
    assert gateway.publication_clock(RUN) == DUE
    # The ledger itself refuses a backward write or a delete.
    for sql in (
        "UPDATE publication_clock SET instant='2000-01-01T00:00:00Z' WHERE lab_run_ref='run-delay-1'",
        "DELETE FROM publication_clock",
    ):
        with pytest.raises(sqlite3.IntegrityError):
            with sqlite3.connect(db_path) as db:
                db.execute(sql)
    for bad in ("2026-10-01 08:10:00", "2026-10-01T08:10:00+00:00", ""):
        with pytest.raises(ValueError):
            gateway.advance_publication_clock(RUN, bad)


def test_a_replay_after_a_later_advance_and_restart_keeps_the_first_stamp(
    db_path: Path, clock, gateway, active: str
) -> None:
    gateway.advance_publication_clock(RUN, DUE)
    first = _admit(gateway, active, report(key="k1", at=SOURCE))
    gateway.seal()
    before = _rows(db_path, "SELECT message_id, sequence, envelope_text, sha256 FROM envelope_outbox")
    batches = _rows(db_path, "SELECT batch_id, payload_text, sha256 FROM upload_batch")
    gateway.close()
    with GatewayService(db_path, clock=clock) as restarted:
        assert restarted.publication_clock(RUN) == DUE  # persisted, not reset or advanced
        restarted.advance_publication_clock(RUN, LATER)
        again = _admit(restarted, active, report(key="k1", at=SOURCE))
        assert (again.outcome, again.message_id, again.sequence) == ("ALREADY_ADMITTED", first.message_id, 1)
        restarted.seal()
    assert _rows(db_path, "SELECT message_id, sequence, envelope_text, sha256 FROM envelope_outbox") == before
    assert _rows(db_path, "SELECT batch_id, payload_text, sha256 FROM upload_batch") == batches


def test_a_jump_past_due_stamps_the_later_instant(gateway, active: str, db_path: Path) -> None:
    gateway.advance_publication_clock(RUN, LATER)
    admission = _admit(gateway, active, report(key="k1", at=SOURCE))
    text = _rows(db_path, "SELECT envelope_text FROM envelope_outbox WHERE message_id=?", (admission.message_id,))
    assert parse_canonical_envelope_v3_text(text[0][0]).published_at == LATER


def test_an_early_report_is_held_without_a_sequence(gateway, active: str, db_path: Path) -> None:
    gateway.advance_publication_clock(RUN, "2026-10-01T07:59:59Z")
    held = _admit(gateway, active, report(key="k1", at=SOURCE))
    assert (held.outcome, held.kind) == ("HELD", "SOURCE_TIME_IN_FUTURE")
    assert _rows(db_path, "SELECT COUNT(*) FROM sequence_state") == [(0,)]


def test_the_real_clock_admission_is_unchanged(gateway, active: str, db_path: Path) -> None:
    gateway.advance_publication_clock(RUN, DUE)
    admission = gateway.admit(report(key="k1", at=SOURCE), snapshot_sha256=active, lab_run_ref=RUN)
    text = _rows(db_path, "SELECT envelope_text FROM envelope_outbox WHERE message_id=?", (admission.message_id,))
    assert parse_canonical_envelope_v3_text(text[0][0]).published_at == "2026-10-08T12:00:00Z"


def test_stop_refuses_virtual_admission_before_any_write(gateway, active: str, db_path: Path) -> None:
    gateway.advance_publication_clock(RUN, DUE)
    gateway.inject_disk_pressure("STOP")
    with pytest.raises(GatewayRefused) as error:
        _admit(gateway, active, report(key="k1", at=SOURCE))
    assert error.value.kind == "DISK_PRESSURE_STOP"
    assert _rows(db_path, "SELECT COUNT(*) FROM envelope_outbox") == [(0,)]


def test_a_live_gateway_has_no_lab_publication_clock(tmp_path: Path, clock) -> None:
    live = Provisioning(
        tenant_id=PROVISIONING.tenant_id,
        site_id=SITE,
        gateway_id=GATEWAY,
        source_mode="LIVE",
        permitted_source_ids=frozenset({SRC_BMS, SRC_PV}),
    )
    with GatewayService(tmp_path / "live.sqlite3", clock=clock) as service:
        service.provision(live, sequence_epoch=EPOCH)
        with pytest.raises(GatewayRefused) as error:
            service.advance_publication_clock(RUN, DUE)
        assert error.value.kind == "NOT_SIMULATED"


# --- ordered admission at a reached boundary (`D-2026-10-09-s2-ordered-publication-and-closing-boundary`)


def _admit_at(gateway: GatewayService, active: str, texts: list[str], at: str, run: str = RUN):
    return gateway.admit_texts(
        texts, snapshot_sha256=active, lab_run_ref=run, publication_clock=RUN_VIRTUAL, at_instant=at
    )


def test_an_admission_instant_moves_the_clock_with_the_admission(gateway, active: str, db_path: Path) -> None:
    first = _admit_at(gateway, active, [report(key="b1", at=SOURCE)], SOURCE)[0]
    assert gateway.publication_clock(RUN) == SOURCE
    second = _admit_at(gateway, active, [report(key="b2", at=DUE)], DUE)[0]
    assert gateway.publication_clock(RUN) == DUE
    stamped = {
        parse_canonical_envelope_v3_text(t).source_time: parse_canonical_envelope_v3_text(t).published_at
        for (t,) in _rows(db_path, "SELECT envelope_text FROM envelope_outbox")
    }
    assert stamped == {SOURCE: SOURCE, DUE: DUE}
    assert (first.sequence, second.sequence) == (1, 2)


def test_a_passed_instant_replays_but_never_stamps_a_new_admission_later(
    gateway, active: str, db_path: Path
) -> None:
    admitted = _admit_at(gateway, active, [report(key="b1", at=SOURCE)], SOURCE)[0]
    gateway.advance_publication_clock(RUN, LATER)
    # Already admitted at its boundary: answered with its first identity.
    again = _admit_at(gateway, active, [report(key="b1", at=SOURCE)], SOURCE)[0]
    assert (again.outcome, again.message_id) == ("ALREADY_ADMITTED", admitted.message_id)
    # Never admitted, and the clock is past its boundary: the whole chunk refuses.
    with pytest.raises(GatewayRefused) as error:
        _admit_at(gateway, active, [report(key="b1", at=SOURCE), report(key="missed", at=DUE)], DUE)
    assert error.value.kind == "PUBLICATION_INSTANT_PASSED"
    assert _rows(db_path, "SELECT COUNT(*) FROM envelope_outbox") == [(1,)]
    assert _rows(db_path, "SELECT COUNT(*) FROM report_admission WHERE report_key='missed'") == [(0,)]
    assert gateway.publication_clock(RUN) == LATER
