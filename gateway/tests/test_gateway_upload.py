"""S2-02 phase 2: Lab Commit release and authenticated HTTPS delivery.

Every network test runs the real `Uploader` against an in-process fake central
server over real TLS (fixtures/test_tls_cert.pem, test-only), never a mock of
`http.client`.
"""

from __future__ import annotations

import json
import logging
import os
import secrets
import sqlite3
import subprocess
import sys
import time
from datetime import timedelta
from pathlib import Path

import pytest
from conftest import GATEWAY, SITE, SRC_BMS, report, snapshot
from fake_central import CERT, DROP, SERVER_INSTANT, FakeCentral, receipt_for, receipt_text

from assetops_contracts.ingestion_receipt_v2 import ReceiptCounts, canonical_receipt_v2_text
from assetops_gateway.credential_protection import restrict_to_current_user
from assetops_gateway.ipc import GatewayServer
from assetops_gateway.service import GatewayRefused, GatewayReader, GatewayService
from assetops_gateway.uploader import (
    UploadConfigInvalid,
    UploadCredentialInvalid,
    Uploader,
    parse_upload_config,
    read_upload_credential,
)

RUN = "run-1"


def _token() -> str:
    return f"aog1.{secrets.token_hex(16)}.{secrets.token_urlsafe(32)}"


@pytest.fixture
def token(tmp_path: Path) -> str:
    value = _token()
    write_credential(tmp_path / "upload.credential", value + "\n")
    return value


def write_credential(path: Path, text: str) -> None:
    """Provisioning's job in production: an owner-only file the gateway will read (Q15)."""
    path.write_text(text, encoding="ascii")
    restrict_to_current_user(path)


def _uploader(service: GatewayService, tmp_path: Path, url: str, **extra) -> Uploader:
    raw = {"server_url": url, "upload_credential_file": "upload.credential", "ca_file": str(CERT), **extra}
    return Uploader(service, parse_upload_config(raw, tmp_path))


def _publish(gateway: GatewayService, sha: str, *, run: str = RUN, count: int = 3, pv: int = 2) -> None:
    texts = [report(at=f"2026-10-01T08:{m:02d}:00Z", key=f"{run}-bms-{m}") for m in range(count)]
    texts += [
        report(device="pv-inverter", signal="ac_power", unit="kW", value="4.2",
               at=f"2026-10-01T08:{m:02d}:00Z", key=f"{run}-pv-{m}")
        for m in range(pv)
    ]
    gateway.admit_texts(texts, snapshot_sha256=sha, lab_run_ref=run)


def _rows(db_path: Path, sql: str, args: tuple = ()) -> list[tuple]:
    db = sqlite3.connect(db_path)
    try:
        return db.execute(sql, args).fetchall()
    finally:
        db.close()


def _batches(db_path: Path) -> dict[str, tuple[str, str]]:
    return {b: (s, t) for b, s, t in _rows(db_path, "SELECT batch_id, state, payload_text FROM upload_batch")}


@pytest.fixture
def released(gateway: GatewayService, active: str) -> dict:
    _publish(gateway, active)
    gateway.seal()
    return gateway.release_run(RUN)


@pytest.fixture
def central():
    servers: list[FakeCentral] = []

    def make(responder) -> FakeCentral:
        server = FakeCentral(responder)
        servers.append(server)
        return server

    yield make
    for server in servers:
        server.close()


def _honest(path: str, headers: dict, body: bytes):
    return 200, receipt_text(body.decode("utf-8"))


# --- release (Lab Commit) -----------------------------------------------------


def test_release_is_one_idempotent_transaction_with_a_manifest(gateway, active, db_path: Path) -> None:
    _publish(gateway, active)
    sealed = gateway.seal()
    assert {s for s, _ in _batches(db_path).values()} == {"STAGED"}
    first = gateway.release_run(RUN)
    assert sorted(first["released_batch_ids"]) == sorted(sealed)
    assert {s for s, _ in _batches(db_path).values()} == {"READY"}
    again = gateway.release_run(RUN)
    assert again["released_now"] == 0 and again["delivery"] == first["delivery"]
    manifest = _rows(db_path, "SELECT lab_run_ref, batch_id FROM release_manifest")
    assert sorted(b for _, b in manifest) == sorted(sealed)
    with pytest.raises(sqlite3.IntegrityError):
        _rows(db_path, "DELETE FROM release_manifest")
    delivery = first["delivery"]
    assert delivery["stage_status"] == "STAGED" and delivery["release_state"] == "PENDING"
    assert delivery["publication_gap"] == "UNKNOWN_TO_GATEWAY" and delivery["gateway_complete"] is False
    assert gateway.release_run("another-run")["delivery"]["release_state"] == "NOT_RELEASED"


def test_a_batch_shared_with_another_run_is_never_released(gateway, active, db_path: Path) -> None:
    _publish(gateway, active, run="run-a", count=2, pv=0)
    gateway.admit(report(at="2026-10-01T09:00:00Z", key="b-1"), snapshot_sha256=active, lab_run_ref="run-b")
    [shared] = gateway.seal()  # one BMS group: both runs' envelopes in one batch
    result = gateway.release_run("run-a")
    assert result["released_now"] == 0
    assert result["delivery"]["shared_batch_ids"] == [shared]
    assert _batches(db_path)[shared][0] == "STAGED"


# --- 200: verified, transactional acknowledgement ------------------------------


def test_a_completed_receipt_is_verified_and_acknowledged_in_one_transaction(
    gateway, released, db_path: Path, tmp_path: Path, token: str, central
) -> None:
    def answer(path, headers, body):
        text = body.decode("utf-8")
        decisions = {1: "REJECTED"} if json.loads(text)["source_id"] == SRC_BMS else {}
        return 200, receipt_text(text, decisions=decisions)

    server = central(answer)
    before = _batches(db_path)
    summary = _uploader(gateway, tmp_path, server.url).deliver()["batches"]
    assert summary["acked"] == 2 and summary["stopped"] is None
    assert summary["credential"].endswith(".<redacted>") and token not in json.dumps(summary)
    for request in server.requests:
        assert request.path == "/api/ingestion/batches"
        assert request.headers["Authorization"] == f"Bearer {token}"
        assert request.headers["Content-Type"] == "application/json"
    assert sorted(r.body for r in server.requests) == sorted(t.encode("utf-8") for _, t in before.values())
    assert {s for s, _ in _batches(db_path).values()} == {"ACKED"}
    acks = _rows(db_path, "SELECT decision, received_at FROM acknowledgement")
    assert len(acks) == 5 and sorted(d for d, _ in acks).count("REJECTED") == 1
    assert {r for _, r in acks} == {SERVER_INSTANT}
    assert len(_rows(db_path, "SELECT * FROM batch_receipt")) == 2
    states = dict(_rows(db_path, "SELECT state, COUNT(*) FROM envelope_outbox GROUP BY state"))
    assert states == {"ACKED": 4, "DEAD_LETTER": 1}
    delivery = gateway.run_delivery(RUN)
    assert delivery["decisions"] == {"ACCEPTED": 4, "DUPLICATE": 0, "REJECTED": 1, "CONFLICT": 0}
    assert delivery["release_state"] == "TERMINAL" and delivery["gateway_complete"] is True
    with pytest.raises(sqlite3.IntegrityError):
        _rows(db_path, "UPDATE acknowledgement SET decision='ACCEPTED'")
    with pytest.raises(sqlite3.IntegrityError):
        _rows(db_path, "UPDATE upload_batch SET state='READY'")


@pytest.mark.parametrize(
    "tamper",
    ["payload_sha256", "batch_id", "message_id", "count", "status", "receipt_hash", "source_id"],
)
def test_a_tampered_receipt_is_never_acknowledged(
    gateway, released, db_path: Path, tmp_path: Path, token: str, central, tamper: str
) -> None:
    def answer(path, headers, body):
        text = body.decode("utf-8")
        honest = receipt_for(text)
        if tamper == "payload_sha256":
            bad = receipt_for(text, payload_sha256="0" * 64)
        elif tamper == "batch_id":
            bad = receipt_for(text, batch_id="other-batch")
        elif tamper == "source_id":
            bad = receipt_for(text, source_id="33333333-3333-4333-8333-333333333339")
        elif tamper == "message_id":
            d = honest.dispositions
            bad = receipt_for(text, dispositions=(d[0].__class__(0, "f" * 64, d[0].decision, d[0].evidence_id, None),) + d[1:])
        elif tamper == "count":
            c = honest.counts
            bad = receipt_for(text, decided=c.total - 1, status="COMPLETED", completed_at=SERVER_INSTANT,
                              counts=ReceiptCounts(c.total - 1, c.total - 1, c.total - 1, 0, 0, 0))
        elif tamper == "status":
            return 200, receipt_text(text, decided=1)  # IN_PROGRESS under a 200
        else:
            raw = canonical_receipt_v2_text(honest)
            return 200, raw.replace(SERVER_INSTANT, "2026-10-09T10:00:01.000000Z", 1).encode("utf-8")
        return 200, canonical_receipt_v2_text(bad).encode("utf-8")

    server = central(answer)
    summary = _uploader(gateway, tmp_path, server.url).upload_pass()
    assert summary["stopped"] == "RECEIPT_MISMATCH" and summary["acked"] == 0
    assert {s for s, _ in _batches(db_path).values()} == {"READY"}
    assert _rows(db_path, "SELECT * FROM acknowledgement") == []
    assert _rows(db_path, "SELECT * FROM batch_receipt") == []
    assert ("RECEIPT_MISMATCH",) in _rows(db_path, "SELECT last_error_code FROM upload_batch")


# --- 202, timeouts, crash after commit, restart -----------------------------------


def test_in_progress_then_completed_retries_identical_bytes(
    gateway, released, db_path: Path, tmp_path: Path, token: str, central
) -> None:
    calls: dict[bytes, int] = {}

    def answer(path, headers, body):
        calls[body] = calls.get(body, 0) + 1
        text = body.decode("utf-8")
        return (202, receipt_text(text, decided=1)) if calls[body] == 1 else (200, receipt_text(text))

    server = central(answer)
    uploader = _uploader(gateway, tmp_path, server.url)
    first = uploader.upload_pass()
    assert first["in_progress"] == 2 and first["acked"] == 0
    assert {s for s, _ in _batches(db_path).values()} == {"READY"}
    assert _rows(db_path, "SELECT * FROM acknowledgement") == []
    second = uploader.upload_pass()  # due again at once: no wait
    assert second["acked"] == 2
    assert set(calls.values()) == {2}  # each batch's exact bytes, twice


def test_a_crash_after_server_commit_is_recovered_by_posting_the_same_bytes(
    gateway, released, db_path: Path, tmp_path: Path, token: str, central, clock
) -> None:
    committed: dict[bytes, bytes] = {}

    def answer(path, headers, body):
        if body not in committed:
            committed[body] = receipt_text(body.decode("utf-8"))  # the server commits...
            return DROP  # ...and the connection drops before the answer
        return 200, committed[body]

    server = central(answer)
    uploader = _uploader(gateway, tmp_path, server.url)
    summary = uploader.upload_pass()
    assert summary["stopped"] == "CONNECTION_FAILED" and summary["attempted"] == 1
    assert "READY" in {s for s, _ in _batches(db_path).values()}
    assert uploader.upload_pass()["attempted"] == 1  # the failed one waits for back-off
    clock.now += timedelta(minutes=10)
    while uploader.upload_pass()["attempted"]:
        clock.now += timedelta(minutes=10)
    assert {s for s, _ in _batches(db_path).values()} == {"ACKED"}
    bodies = [r.body for r in server.requests]
    assert all(bodies.count(b) == 2 for b in set(bodies))  # retried byte-identically


def test_timeout_and_refused_connection_leave_bytes_ready(
    gateway, released, db_path: Path, tmp_path: Path, token: str, central, clock
) -> None:
    def slow(path, headers, body):
        time.sleep(1.5)
        return 200, receipt_text(body.decode("utf-8"))

    server = central(slow)
    summary = _uploader(gateway, tmp_path, server.url, timeout_seconds=0.3).upload_pass()
    assert summary["stopped"] == "TIMEOUT"
    assert {s for s, _ in _batches(db_path).values()} == {"READY"}
    import socket

    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        closed_port = probe.getsockname()[1]
    clock.now += timedelta(minutes=10)
    summary = _uploader(gateway, tmp_path, f"https://127.0.0.1:{closed_port}").upload_pass()
    assert summary["stopped"] == "CONNECTION_FAILED"
    assert {s for s, _ in _batches(db_path).values()} == {"READY"}
    assert _rows(db_path, "SELECT * FROM acknowledgement") == []


def test_an_untrusted_certificate_is_a_tls_failure_not_a_fallback(
    gateway, released, db_path: Path, tmp_path: Path, token: str, central
) -> None:
    server = central(_honest)
    raw = {"server_url": server.url, "upload_credential_file": "upload.credential"}  # system store only
    summary = Uploader(gateway, parse_upload_config(raw, tmp_path)).upload_pass()
    assert summary["stopped"] in ("TLS_ERROR", "CONNECTION_FAILED") and summary["acked"] == 0
    assert server.requests == []


def test_restart_recovers_an_in_flight_batch(
    gateway, released, db_path: Path, tmp_path: Path, token: str, central, clock
) -> None:
    batch_id = gateway.due_batches(1)[0]
    payload = gateway.begin_attempt(batch_id)
    gateway.close()
    reopened = GatewayService(db_path, clock=clock)
    try:
        assert _batches(db_path)[batch_id][0] == "READY"
        server = central(_honest)
        _uploader(reopened, tmp_path, server.url).upload_pass()
        assert server.requests[0].body == payload.encode("utf-8")
        assert {s for s, _ in _batches(db_path).values()} == {"ACKED"}
    finally:
        reopened.close()


# --- credential and terminal refusals -------------------------------------------


@pytest.mark.parametrize("status", [401, 403])
def test_a_credential_refusal_keeps_bytes_ready_and_stops_the_pass(
    gateway, released, db_path: Path, tmp_path: Path, token: str, central, status: int
) -> None:
    server = central(lambda p, h, b: (status, json.dumps({"detail": {"code": "UPLOAD_UNAUTHORIZED"}}).encode()))
    summary = _uploader(gateway, tmp_path, server.url).upload_pass()
    assert summary["stopped"] == "UPLOAD_UNAUTHORIZED" and summary["attempted"] == 1
    assert {s for s, _ in _batches(db_path).values()} == {"READY"}
    assert gateway.run_delivery(RUN)["last_upload_error"]["code"] == "UPLOAD_UNAUTHORIZED"


@pytest.mark.parametrize(("status", "code"), [(409, "BATCH_ID_CONFLICT"), (422, "BATCH_REFUSED"), (413, None)])
def test_an_authenticated_whole_batch_refusal_is_terminal(
    gateway, released, db_path: Path, tmp_path: Path, token: str, central, status: int, code
) -> None:
    body = b"{}" if code is None else json.dumps({"detail": {"code": code, "message": "no"}}).encode()
    server = central(lambda p, h, b: (status, body))
    summary = _uploader(gateway, tmp_path, server.url).upload_pass()
    assert summary["refused"] == 2 and summary["stopped"] is None
    assert {s for s, _ in _batches(db_path).values()} == {"REFUSED"}
    assert {s for (s,) in _rows(db_path, "SELECT state FROM envelope_outbox")} == {"DEAD_LETTER"}
    delivery = gateway.run_delivery(RUN)
    assert {r["code"] for r in delivery["refusals"]} == {code or f"HTTP_{status}"}
    assert delivery["release_state"] == "TERMINAL" and delivery["gateway_complete"] is False
    assert delivery["decisions"]["ACCEPTED"] == 0
    assert _uploader(gateway, tmp_path, server.url).upload_pass()["attempted"] == 0  # never resent


def test_the_secret_never_reaches_the_ledger_logs_or_answers(
    gateway, released, db_path: Path, tmp_path: Path, token: str, central, caplog
) -> None:
    def echo(path, headers, body):  # a hostile server echoing the header back
        return 401, json.dumps({"detail": {"code": "UPLOAD_UNAUTHORIZED", "message": headers["Authorization"]}}).encode()

    caplog.set_level(logging.DEBUG, logger="assetops_gateway")
    uploader = _uploader(gateway, tmp_path, central(echo).url)
    result = uploader.deliver()
    gateway.emit_diagnostic()
    uploader.deliver()
    secret = token.split(".")[2]
    assert secret not in json.dumps(result) and secret not in caplog.text
    assert secret not in repr(read_upload_credential(tmp_path / "upload.credential"))
    gateway.close()
    for path in db_path.parent.glob(db_path.name + "*"):
        assert secret.encode() not in path.read_bytes(), path


def test_a_malformed_credential_file_stops_without_sending(
    gateway, released, db_path: Path, tmp_path: Path, central
) -> None:
    write_credential(tmp_path / "upload.credential", "not-a-credential-secret-value")
    server = central(_honest)
    summary = _uploader(gateway, tmp_path, server.url).upload_pass()
    assert summary["stopped"] == "UPLOAD_CREDENTIAL_INVALID" and server.requests == []


def test_a_credential_file_readable_by_others_is_refused_before_it_is_read(
    gateway, released, tmp_path: Path, token: str, central
) -> None:
    path = tmp_path / "upload.credential"
    if sys.platform == "win32":  # a protected DACL that also lets Everyone read
        subprocess.run(["icacls", str(path), "/grant", "*S-1-1-0:R"], check=True, capture_output=True)
    else:
        os.chmod(path, 0o644)
    with pytest.raises(UploadCredentialInvalid, match="gateway's user only"):
        read_upload_credential(path)
    server = central(_honest)
    summary = _uploader(gateway, tmp_path, server.url).upload_pass()
    assert summary["stopped"] == "UPLOAD_CREDENTIAL_INVALID" and server.requests == []
    restrict_to_current_user(path)
    assert read_upload_credential(path).authorization() == f"Bearer {token}"


@pytest.mark.skipif(sys.platform != "win32", reason="Windows inheritance")
def test_a_credential_file_inheriting_its_folders_access_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "inherited.credential"
    path.write_text(_token(), encoding="ascii")  # default: inherits the folder's DACL
    with pytest.raises(UploadCredentialInvalid, match="inherits access"):
        read_upload_credential(path)


def test_credential_rotation_needs_no_restart_and_no_reseal(
    gateway, released, db_path: Path, tmp_path: Path, token: str, central
) -> None:
    rotated = _token()
    server = central(
        lambda p, h, b: _honest(p, h, b) if h["Authorization"] == f"Bearer {rotated}" else (401, b"{}")
    )
    uploader = _uploader(gateway, tmp_path, server.url)
    assert uploader.upload_pass()["stopped"] == "HTTP_401"
    before = _batches(db_path)
    (tmp_path / "upload.credential").write_text(rotated, encoding="ascii")
    assert uploader.upload_pass()["acked"] == 2
    assert {b: t for b, (_, t) in _batches(db_path).items()} == {b: t for b, (_, t) in before.items()}


# --- configuration -----------------------------------------------------------------


@pytest.mark.parametrize(
    "url", ["http://central.example", "central.example", "https://user:pw@central.example", "https://h/x?q=1"]
)
def test_only_https_is_accepted(tmp_path: Path, url: str) -> None:
    with pytest.raises(UploadConfigInvalid):
        parse_upload_config({"server_url": url, "upload_credential_file": "c"}, tmp_path)


def test_the_gateway_config_refuses_plaintext_and_unknown_upload_keys(tmp_path: Path) -> None:
    from test_gateway_process import write_config

    from assetops_gateway.__main__ import load_config

    path = write_config(tmp_path)
    document = json.loads(path.read_text(encoding="utf-8"))
    for upload in (
        {"server_url": "http://127.0.0.1:1", "upload_credential_file": "c"},
        {"server_url": "https://127.0.0.1:1", "upload_credential_file": "c", "token": "x"},
    ):
        path.write_text(json.dumps({**document, "upload": upload}), encoding="utf-8")
        with pytest.raises(SystemExit):
            load_config(path)
    path.write_text(json.dumps({**document, "upload": {"server_url": "https://h", "upload_credential_file": "c"}}))
    assert load_config(path).upload.host == "h"
    path.write_text(json.dumps(document), encoding="utf-8")
    assert load_config(path).upload is None


# --- scale and partial sealing ------------------------------------------------------


def test_a_bounded_pass_drains_many_batches_over_several_passes(
    gateway, active, db_path: Path, tmp_path: Path, token: str, central
) -> None:
    texts = [report(at=f"2026-10-01T{h:02d}:{m:02d}:00Z", key=f"k-{h}-{m}") for h in range(5) for m in range(49)]
    gateway.admit_texts(texts, snapshot_sha256=active, lab_run_ref=RUN)
    assert len(gateway.seal(max_envelopes=1)) == 245
    gateway.release_run(RUN)
    server = central(_honest)
    uploader = _uploader(gateway, tmp_path, server.url, batches_per_pass=50)
    passes = []
    while (summary := uploader.upload_pass())["attempted"]:
        passes.append(summary["acked"])
    assert passes == [50, 50, 50, 50, 45]
    delivery = gateway.run_delivery(RUN)
    assert delivery["batches_by_state"]["ACKED"] == 245 and delivery["gateway_complete"] is True


def test_a_sibling_batch_uploads_while_another_group_is_sealing_refused(
    gateway, active, db_path: Path, tmp_path: Path, token: str, central, monkeypatch
) -> None:
    import assetops_gateway.service as service_module
    from assetops_contracts.ingestion_batch_v2 import BatchRejected

    _publish(gateway, active)
    gateway.admit(report(device="unknown-device", key="held"), snapshot_sha256=active, lab_run_ref=RUN)
    real = service_module.seal_batch_v2

    def refuse_bms(**kwargs):
        if kwargs["source_id"] == SRC_BMS:
            raise BatchRejected("TOO_LARGE", "batch", "forced for the test")
        return real(**kwargs)

    monkeypatch.setattr(service_module, "seal_batch_v2", refuse_bms)
    with pytest.raises(GatewayRefused):
        gateway.seal()
    result = gateway.release_run(RUN)
    assert result["released_now"] == 1
    server = central(_honest)
    assert _uploader(gateway, tmp_path, server.url).upload_pass()["acked"] == 1
    delivery = gateway.run_delivery(RUN)
    assert delivery["stage_status"] == "SEALING_REFUSED"
    assert delivery["unbatched_envelope_count"] == 3 and delivery["held_report_count"] == 1
    assert delivery["decisions"]["ACCEPTED"] == 2  # the held report is never counted
    assert delivery["release_state"] == "TERMINAL" and delivery["gateway_complete"] is False
    assert gateway.release_run(RUN)["released_now"] == 0


# --- diagnostics ------------------------------------------------------------------


def test_a_diagnostic_is_acknowledged_with_the_server_receive_time(
    gateway, db_path: Path, tmp_path: Path, token: str, central
) -> None:
    row = gateway.emit_diagnostic()

    def answer(path, headers, body):
        assert body == row.payload_text.encode("utf-8")
        return 201, json.dumps(
            {"diagnostic_id": "d-1", "received_at": SERVER_INSTANT, "payload_sha256": row.sha256}
        ).encode()

    server = central(answer)
    summary = _uploader(gateway, tmp_path, server.url).diagnostics_pass()
    assert summary["acked"] == 1
    assert server.requests[0].path == f"/api/gateways/{GATEWAY}/diagnostics"
    assert _rows(db_path, "SELECT state, server_received_at FROM diagnostic_outbox") == [("ACKED", SERVER_INSTANT)]


@pytest.mark.parametrize("status", [409, 422])
def test_a_refused_diagnostic_is_recorded_and_not_retried(
    gateway, db_path: Path, tmp_path: Path, token: str, central, clock, status: int
) -> None:
    gateway.emit_diagnostic()
    server = central(lambda p, h, b: (status, json.dumps({"detail": {"code": "DIAGNOSTIC_CONFLICT"}}).encode()))
    uploader = _uploader(gateway, tmp_path, server.url)
    assert uploader.diagnostics_pass()["refused"] == 1
    clock.now += timedelta(hours=1)
    assert uploader.diagnostics_pass()["attempted"] == 0
    assert _rows(db_path, "SELECT state, refusal_code, server_received_at FROM diagnostic_outbox") == [
        ("READY", "DIAGNOSTIC_CONFLICT", None)
    ]


def test_a_diagnostic_answer_for_other_bytes_is_not_acknowledged(
    gateway, db_path: Path, tmp_path: Path, token: str, central
) -> None:
    gateway.emit_diagnostic()
    server = central(lambda p, h, b: (200, json.dumps(
        {"diagnostic_id": "d", "received_at": SERVER_INSTANT, "payload_sha256": "0" * 64}).encode()))
    assert _uploader(gateway, tmp_path, server.url).diagnostics_pass()["stopped"] == "RECEIPT_MISMATCH"
    assert _rows(db_path, "SELECT state, server_received_at FROM diagnostic_outbox") == [("READY", None)]


# --- IPC -------------------------------------------------------------------------


def _handle(server: GatewayServer, op: str, body: dict) -> dict:
    raw = json.dumps({"protocol": "assetops.gateway-local-ipc", "version": 1, "op": op, "body": body})
    return server.handle(raw.encode("utf-8"))


def test_release_delivery_and_deliver_cross_the_channel(
    gateway, active, db_path: Path, tmp_path: Path, token: str, central
) -> None:
    from test_gateway_process import _address

    _publish(gateway, active)
    gateway.seal()
    server = GatewayServer(gateway, db_path, _address(tmp_path), b"k" * 32)
    try:
        refused = _handle(server, "deliver", {"max_batches": 5})
        assert refused["ok"] is False and refused["kind"] == "UPLOAD_NOT_CONFIGURED"
        assert _handle(server, "release_run", {"lab_run_ref": RUN, "extra": 1})["kind"] == "BAD_REQUEST"
        assert _handle(server, "release_run", {"lab_run_ref": RUN})["body"]["released_now"] == 2
        assert _handle(server, "deliver", {"max_batches": 0})["kind"] == "BAD_REQUEST"
        server.attach_uploader(_uploader(gateway, tmp_path, central(_honest).url), background=False)
        answer = _handle(server, "deliver", {"max_batches": 5})
        assert answer["ok"] and answer["body"]["batches"]["acked"] == 2
        assert token.split(".")[2] not in json.dumps(answer)
        delivery = _handle(server, "run_delivery", {"lab_run_ref": RUN})["body"]
        assert delivery["gateway_complete"] is True and delivery["lab_run_ref"] == RUN
    finally:
        server.close()
