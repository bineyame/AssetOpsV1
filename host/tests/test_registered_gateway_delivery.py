"""S2-02 phase 2: Lab Commit of a registered Kobo run through the real gateway.

A real registered Draft runs in the Lab host; a real `python -m assetops_gateway
serve` process holds the outbox and, when configured, uploads over real TLS to
an in-process fake central server. The host only ever asks the gateway to
release and to report: it never holds the upload secret.
"""

from __future__ import annotations

import json
import secrets
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend" / "tests"))
sys.path.insert(0, str(ROOT / "gateway" / "tests"))

import test_s2_registered_basis as registered  # noqa: E402
from fake_central import CERT, FakeCentral, receipt_text  # noqa: E402
from gateway_process import GatewayProcess, provisioning_from_snapshot, write_config  # noqa: E402
from gateway_publication import RegisteredGatewayPublisher  # noqa: E402
from lab_execution import HostLabExecution, YamlExecutionArtifacts  # noqa: E402
from source_stages import JsonSourceStages  # noqa: E402

from assetops_contracts.lab_projection import LabControlRefused  # noqa: E402
from assetops_gateway.ipc import GatewayRequestRefused  # noqa: E402


@pytest.fixture(scope="module")
def draft():
    store, _, _ = registered.converted()
    return registered.setup_service(store).create_draft_run(registered.request())


def _gateway(tmp_path: Path, draft, upload: dict | None = None) -> GatewayProcess:
    config = write_config(tmp_path / "gateway", provisioning_from_snapshot(draft.registered_basis.snapshot_canonical))
    if upload is not None:
        document = json.loads(config.read_text(encoding="utf-8"))
        config.write_text(json.dumps({**document, "upload": upload}), encoding="utf-8")
    process = GatewayProcess(config)
    assert process.ready, process.first_line
    return process


def _host(root: Path, link) -> HostLabExecution:
    return HostLabExecution(
        artifacts=YamlExecutionArtifacts(root),
        stages=JsonSourceStages(root / "stages"),
        gateway=RegisteredGatewayPublisher(link),
    )


def test_commit_releases_the_sealed_batches_once_and_reports_pending(draft, tmp_path) -> None:
    process = _gateway(tmp_path, draft)
    try:
        port = _host(tmp_path / "host", process.link)
        port.start(draft)
        with pytest.raises(LabControlRefused) as early:
            port.release_registered(draft)  # the world run has not completed
        assert early.value.kind == "COMMIT_NOT_READY"
        assert {b.state for b in port.registered_stage(draft).batches} <= {"STAGED"}
        assert port.run_to_end(draft).status == "COMPLETED"
        view = port.release_registered(draft)
        delivery = view["delivery"]
        assert view["released_now"] == delivery["batch_count"] > 0
        assert delivery["stage_status"] == "STAGED" and delivery["release_state"] == "PENDING"
        assert delivery["held_report_count"] > 0 and delivery["decisions"]["ACCEPTED"] == 0
        assert view["fully_released"] is False and "RECEIPTS_PENDING" in view["release_blockers"]
        assert {(r["state"], r["released"], r["receipt"]) for r in delivery["batches"]} == {("READY", True, None)}
        assert {b.state for b in port.registered_stage(draft).batches} == {"READY"}
        again = port.release_registered(draft)
        assert again["released_now"] == 0 and again["delivery"] == delivery
        assert port.registered_delivery(draft)["delivery"] == delivery
        with pytest.raises(GatewayRequestRefused) as refused:
            RegisteredGatewayPublisher(process.link).deliver(10)
        assert refused.value.kind == "UPLOAD_NOT_CONFIGURED"
    finally:
        process.kill()


def test_the_gateway_uploads_every_batch_and_the_run_reads_fully_released(draft, tmp_path) -> None:
    token = f"aog1.{secrets.token_hex(16)}.{secrets.token_urlsafe(32)}"
    (tmp_path / "gateway").mkdir(parents=True)
    (tmp_path / "gateway" / "upload.credential").write_text(token, encoding="ascii")
    central = FakeCentral(lambda path, headers, body: (200, receipt_text(body.decode("utf-8"))))
    upload = {
        "server_url": central.url,
        "upload_credential_file": "upload.credential",
        "ca_file": str(CERT),
        "interval_seconds": 3600,
    }
    process = _gateway(tmp_path, draft, upload)
    try:
        port = _host(tmp_path / "host", process.link)
        port.start(draft)
        assert port.run_to_end(draft).status == "COMPLETED"
        released = port.release_registered(draft)
        publisher = RegisteredGatewayPublisher(process.link)
        while publisher.deliver(50)["batches"]["attempted"]:
            pass
        view = port.registered_delivery(draft)
        delivery = view["delivery"]
        assert delivery["batches_by_state"]["ACKED"] == released["delivery"]["batch_count"]
        assert delivery["decisions"]["ACCEPTED"] == delivery["envelope_count"]
        assert view["fully_released"] is True and view["release_blockers"] == []
        # Phase 3: one row per batch with its verified receipt, and the structured
        # schedule completeness the Lab Commit view reads beside Stage STAGED.
        rows = delivery["batches"]
        assert len(rows) == delivery["batch_count"] > 1
        assert all(r["state"] == "ACKED" and r["released"] and not r["shared_with_another_run"] for r in rows)
        assert all(r["receipt"]["server_received_at"] and r["receipt"]["receipt_sha256"] for r in rows)
        assert sum(r["decisions"]["ACCEPTED"] for r in rows) == delivery["envelope_count"]
        assert sum(r["item_count"] for r in rows) == delivery["envelope_count"]
        # A gateway-UTC run has no Lab publication schedule (its terminal and
        # incomplete RUN_VIRTUAL readings are covered in test_registered_post_run_release).
        assert view["publication_gap"] == "NOT_APPLICABLE" and view["publication_schedule"] is None
        assert all(r.headers["Authorization"] == f"Bearer {token}" for r in central.requests)
        stage = port.registered_stage(draft)
        assert {b.state for b in stage.batches} == {"ACKED"}
        assert token.split(".")[2] not in json.dumps(view)
    finally:
        process.kill()
        central.close()
