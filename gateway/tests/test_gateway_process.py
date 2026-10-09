"""S2-01b phase 2: the separate gateway process and its authenticated channel.

Every test here talks to a real `python -m assetops_gateway serve` process over
the local pipe/socket, never to the service object.
"""

from __future__ import annotations

import json
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from conftest import EPOCH, GATEWAY, PROVISIONING, SITE, TENANT, report, snapshot

from assetops_gateway.ipc import (
    MAX_MESSAGE_BYTES,
    GatewayLink,
    GatewayRequestRefused,
    GatewayUnavailable,
    ensure_credential,
)


def _address(tmp_path: Path) -> str:
    if sys.platform == "win32":
        return rf"\\.\pipe\assetops-gateway-test-{uuid.uuid4().hex}"
    return str(tmp_path / "gw.sock")


def write_config(tmp_path: Path, *, site: str = SITE, address: str | None = None) -> Path:
    config = tmp_path / "gateway.json"
    config.write_text(
        json.dumps(
            {
                "database": "gateway.sqlite3",
                "credential_file": "gateway.credential",
                "address": address or _address(tmp_path),
                "provisioning": {
                    "tenant_id": TENANT,
                    "site_id": site,
                    "gateway_id": GATEWAY,
                    "source_mode": "SIMULATED",
                    "permitted_source_ids": sorted(PROVISIONING.permitted_source_ids),
                    "sequence_epoch": EPOCH,
                },
            }
        ),
        encoding="utf-8",
    )
    return config


class GatewayProcess:
    def __init__(self, config: Path) -> None:
        self.config = config
        self.process = subprocess.Popen(
            [sys.executable, "-m", "assetops_gateway", "serve", "--config", str(config)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        self.first_line = self.process.stdout.readline().strip()
        document = json.loads(config.read_text(encoding="utf-8"))
        self.link = GatewayLink(document["address"], config.parent / document["credential_file"])

    def kill(self) -> None:
        if self.process.poll() is None:
            self.process.kill()
        self.process.wait(timeout=30)
        self.process.stdout.close()


@pytest.fixture
def running(tmp_path: Path):
    started = GatewayProcess(write_config(tmp_path))
    assert started.first_line.startswith("READY"), started.first_line
    yield started
    started.kill()


def test_the_process_serves_activation_admission_sealing_and_reads(running: GatewayProcess) -> None:
    link = running.link
    assert link.call("identity")["site_id"] == SITE
    text, claimed = snapshot()
    activated = link.call("activate", {"snapshot_text": text, "claimed": claimed.__dict__})
    sha = activated["snapshot_sha256"]
    reports = [report(key=f"k-{i}", at=f"2026-10-01T08:{i:02d}:00Z") for i in range(3)]
    first = link.call("admit", {"snapshot_sha256": sha, "lab_run_ref": "run-a", "reports": reports})
    assert [a["outcome"] for a in first["admissions"]] == ["ADMITTED"] * 3
    assert [a["sequence"] for a in first["admissions"]] == [1, 2, 3]
    replay = link.call("admit", {"snapshot_sha256": sha, "lab_run_ref": "run-a", "reports": reports})
    assert [a["outcome"] for a in replay["admissions"]] == ["ALREADY_ADMITTED"] * 3
    assert [a["message_id"] for a in replay["admissions"]] == [a["message_id"] for a in first["admissions"]]
    sealed = link.call("seal")["batch_ids"]
    assert len(sealed) == 1
    stage = link.call("run_stage", {"lab_run_ref": "run-a"})
    assert [e["sequence"] for e in stage["envelopes"]] == [1, 2, 3]
    assert stage["batches"][0]["state"] == "STAGED"
    assert stage["queue_depth_by_state"] == {"STAGED": 3}


def test_a_peer_without_the_credential_is_refused_before_any_request(running: GatewayProcess, tmp_path: Path) -> None:
    stranger = tmp_path / "stranger.credential"
    ensure_credential(stranger)
    with pytest.raises(GatewayUnavailable):
        GatewayLink(running.link.address, stranger).call("identity")
    # The real host still gets through, and the stranger changed nothing.
    assert running.link.call("identity")["gateway_id"] == GATEWAY


def test_no_gateway_is_unavailable_not_a_fallback(tmp_path: Path) -> None:
    credential = tmp_path / "c"
    ensure_credential(credential)
    with pytest.raises(GatewayUnavailable):
        GatewayLink(_address(tmp_path), credential).call("identity")


def test_requests_are_exact_and_bounded(running: GatewayProcess) -> None:
    with pytest.raises(GatewayRequestRefused) as refused:
        running.link.call("run_stage", {"lab_run_ref": "run-a", "oracle": "private"})
    assert refused.value.kind == "BAD_REQUEST" and refused.value.field == "body"
    with pytest.raises(GatewayRequestRefused) as refused:
        running.link.call("admit", {"snapshot_sha256": "0" * 64, "lab_run_ref": "r", "reports": ["x"] * 1025})
    assert refused.value.field == "reports"
    with pytest.raises((GatewayUnavailable, ValueError)):
        running.link.call("run_stage", {"lab_run_ref": "r" * (MAX_MESSAGE_BYTES + 1)})


def test_activation_refusals_cross_the_channel_typed(running: GatewayProcess) -> None:
    text, claimed = snapshot(site="99999999-9999-4999-8999-999999999999")
    with pytest.raises(GatewayRequestRefused) as refused:
        running.link.call("activate", {"snapshot_text": text, "claimed": claimed.__dict__})
    assert refused.value.kind == "OUT_OF_SCOPE" and refused.value.field == "site.site_id"
    text, claimed = snapshot()
    changed = text.replace("KOBO", "KOBX")
    with pytest.raises(GatewayRequestRefused) as refused:
        running.link.call("activate", {"snapshot_text": changed, "claimed": claimed.__dict__})
    assert refused.value.kind == "HASH_MISMATCH"


def test_a_ledger_provisioned_for_another_site_refuses_to_start(running: GatewayProcess, tmp_path: Path) -> None:
    running.kill()
    other = GatewayProcess(write_config(tmp_path, site="99999999-9999-4999-8999-999999999999"))
    try:
        assert other.first_line.startswith("REFUSED IDENTITY_FIXED"), other.first_line
        assert other.process.wait(timeout=30) == 2
    finally:
        other.kill()


def test_restart_keeps_identity_and_bytes(running: GatewayProcess, tmp_path: Path) -> None:
    text, claimed = snapshot()
    sha = running.link.call("activate", {"snapshot_text": text, "claimed": claimed.__dict__})["snapshot_sha256"]
    reports = [report(key="k-1")]
    running.link.call("admit", {"snapshot_sha256": sha, "lab_run_ref": "run-a", "reports": reports})
    running.link.call("seal")
    before = running.link.call("run_stage", {"lab_run_ref": "run-a"})
    running.kill()
    again = GatewayProcess(running.config)
    try:
        assert again.first_line.startswith("READY")
        assert again.link.call("run_stage", {"lab_run_ref": "run-a"}) == before
        replay = again.link.call("admit", {"snapshot_sha256": sha, "lab_run_ref": "run-a", "reports": reports})
        assert replay["admissions"][0]["outcome"] == "ALREADY_ADMITTED"
    finally:
        again.kill()


def test_the_process_serves_local_diagnostics_and_a_dead_gateway_is_unavailable(running: GatewayProcess) -> None:
    """S2-01c: the diagnostic read crosses the authenticated channel; a killed
    gateway is unavailable, never a healthy zero queue."""
    link = running.link
    emitted = link.call("emit_diagnostic")
    again = link.call("emit_diagnostic")
    assert emitted["diagnostic_sequence"] >= 1 and emitted["state"] == "READY"
    # inside one 60 s cadence slot a retry is the same identity and bytes
    # (the ticker may have emitted first; either way the slot holds one report)
    if again["diagnostic_sequence"] == emitted["diagnostic_sequence"]:
        assert again == emitted
    read = link.call("diagnostics")
    assert read["site_id"] == SITE and read["upload"] == "PENDING"
    assert read["config"]["emission_cadence_seconds"] == 60
    assert read["diagnostics"][0]["payload_text"] in (emitted["payload_text"], again["payload_text"])
    assert {c["last_contact_at"] for c in read["source_contacts"]} == {None}
    with pytest.raises(GatewayRequestRefused):
        link.call("diagnostics", {"lab_run_ref": "x"})  # exact body
    running.kill()
    with pytest.raises(GatewayUnavailable):
        link.call("diagnostics")
