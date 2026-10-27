"""TEL-05: Postgres acceptance of profile `gx-system-illustrative-1` (run alone; Q-T56).

GX-shaped emulator (in-process) -> poller subprocess -> real gateway process ->
`FakeCentral` whose batch route is the real `BatchIngestionService` over
`PostgresEvidenceLedger` with the real UTC clock (Q-T47, no decision-clock
override). The Site is KOBO-001 converted inside the `*_test` database only
(owner Q4 / D2). No simulation publication is attached, so the source class
resolves UNKNOWN (D1(c)), and no consequence row may exist (D5).

Skipped without `ASSETOPS_TEST_DATABASE_URL`.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import sqlite3
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend" / "tests"))
sys.path.insert(0, str(ROOT / "gateway" / "tests"))
sys.path.insert(0, str(ROOT / "field" / "tests"))

import field_bench  # noqa: E402
import test_field_modbus_tcp_proof as tel4  # noqa: E402
import test_s2_registered_basis as registered  # noqa: E402
from fake_central import CERT, FakeCentral  # noqa: E402
from field_emulators.gx_server import GxEmulator, ObservationTimeline  # noqa: E402
from gateway_process import GatewayProcess, provisioning_from_snapshot, write_config  # noqa: E402
from gateway_publication import claimed_references  # noqa: E402

from assetops_field.clock import ReplayClock  # noqa: E402
from assetops_field.profile import load_profile  # noqa: E402
from assetops_field.report import instant_z  # noqa: E402

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
PROFILE_PATH = tel4.PROFILE_PATH
RATE = 60
START = datetime(2026, 9, 30, 3, 0, tzinfo=timezone.utc)
STOP = datetime(2026, 9, 30, 15, 0, tzinfo=timezone.utc)
EPOCH = tel4.EPOCH
BOUND_ROLES = {"pv_power", "battery_soc"}


def _central(principal, receipts: list):
    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.evidence.ledger_service import BatchIngestionService
    from assetops_contracts.ingestion_receipt_v2 import canonical_receipt_v2_text

    ingestion = BatchIngestionService(PostgresEvidenceLedger(URL))  # the real UTC clock (Q-T47)

    def batches(path, headers, body):
        answer = ingestion.submit(principal, body)
        receipts.append(answer.receipt)
        return answer.status, canonical_receipt_v2_text(answer.receipt).encode("utf-8")

    return FakeCentral(tel4.with_diagnostics(batches))  # TEL-04-Dev1: diagnostics answered beside ingestion


def _snapshot():
    """KOBO-001 converted in the test database, its gateway and sources enabled, the registered daytime draft."""
    import test_s1_bindings_postgres as pgb
    from sqlalchemy import create_engine, text

    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore

    store = PostgresFoundationStore(URL)
    result, _ = pgb.converted(store)
    engine = create_engine(URL)
    try:
        with engine.begin() as connection:  # stand in for credential provisioning (as the S2 ledger tests do)
            connection.execute(text("UPDATE gateway SET disabled_at = NULL WHERE site_id = :s"), {"s": result.site.id})
            connection.execute(text("UPDATE source SET disabled_at = NULL WHERE site_id = :s"), {"s": result.site.id})
    finally:
        engine.dispose()
    draft = registered.setup_service(store).create_draft_run(registered.request())
    assert draft.execution_status == "READY", draft.blocking_reasons
    return draft.registered_basis


def _site_rows(sql: str, site_id: str) -> list[dict]:
    from sqlalchemy import create_engine, text

    engine = create_engine(URL)
    try:
        with engine.connect() as connection:
            return [dict(r._mapping) for r in connection.execute(text(sql), {"s": site_id})]
    finally:
        engine.dispose()


def _consequence_rows(site_id: str) -> dict[str, int]:
    """Row counts for the Site in every table whose name holds `consequence` and that has a `site_id` column."""
    from sqlalchemy import create_engine, text

    engine = create_engine(URL)
    try:
        with engine.connect() as connection:
            tables = [t for (t,) in connection.execute(text(
                "SELECT table_name FROM information_schema.columns WHERE table_schema = 'public' "
                "AND column_name = 'site_id' AND table_name LIKE '%consequence%' ORDER BY table_name"))]
            return {t: connection.execute(text(f'SELECT COUNT(*) FROM "{t}" WHERE site_id = :s'),
                                          {"s": site_id}).scalar_one() for t in tables}
    finally:
        engine.dispose()


@pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")
def test_gx_profile_1_lands_as_accepted_evidence(tmp_path: Path, monkeypatch, capsys) -> None:
    import pg_harness
    from assetops_backend.analytics import assess_dispatch
    from assetops_backend.analytics.composition import build_dispatch_read_service
    from assetops_backend.evidence.composition import build_source_provenance
    from assetops_backend.evidence.ledger import GatewayPrincipal
    from assetops_gateway.credential_protection import restrict_to_current_user

    monkeypatch.setenv("DATABASE_URL", URL)
    pg_harness.fresh_database()
    basis = _snapshot()
    snapshot_text = basis.snapshot_canonical
    snapshot_sha256 = hashlib.sha256(snapshot_text.encode("utf-8")).hexdigest()
    doc = json.loads(snapshot_text)
    tenant_id, site_id = doc["tenant_id"], doc["site"]["site_id"]
    principal = GatewayPrincipal(tenant_id=UUID(tenant_id), site_id=UUID(site_id),
                                 gateway_id=UUID(doc["gateway"]["gateway_id"]), mode=doc["gateway"]["mode"])

    receipts: list = []
    central = _central(principal, receipts)
    state = tmp_path / "gateway"
    config = write_config(state, provisioning_from_snapshot(snapshot_text, epoch=EPOCH))
    token = f"aog1.{secrets.token_hex(16)}.{secrets.token_urlsafe(32)}"
    (state / "upload.credential").write_text(token, encoding="ascii")
    restrict_to_current_user(state / "upload.credential")
    document = json.loads(config.read_text(encoding="utf-8"))
    document["upload"] = {"server_url": central.url, "upload_credential_file": "upload.credential",
                          "ca_file": str(CERT), "interval_seconds": 3600}
    config.write_text(json.dumps(document), encoding="utf-8")
    process = GatewayProcess(config)
    emulator = None
    try:
        assert process.ready, process.first_line
        activated = process.link.call("activate", {"snapshot_text": snapshot_text, "claimed": claimed_references(basis)})
        assert activated == {"snapshot_sha256": snapshot_sha256}
        expect = field_bench.expect_identity_from_snapshot(
            snapshot_text, json.loads(PROFILE_PATH.read_text(encoding="utf-8")), EPOCH)
        expect_path = tmp_path / "expect-identity.json"
        expect_path.write_text(json.dumps(expect), encoding="utf-8")

        wall_epoch = datetime.now(timezone.utc) + tel4.EPOCH_LEAD
        emulator = GxEmulator(ObservationTimeline(tel4.JSONL, load_profile(PROFILE_PATH)),
                              ReplayClock(START, RATE, wall_epoch), host="127.0.0.1", port=0)
        emulator.start()
        poller_dir = tmp_path / "poller"
        command = [
            sys.executable, "-m", "assetops_field.modbus_poller", "--profile", str(PROFILE_PATH),
            "--host", "127.0.0.1", "--port", str(emulator.port), "--gateway-address", document["address"],
            "--ipc-credential", str(state / "gateway.credential"), "--snapshot-sha256", snapshot_sha256,
            "--expect-identity", str(expect_path), "--state-dir", str(poller_dir), "--read-timeout-s", "0.25",
            "--replay-start", instant_z(START), "--replay-rate", str(RATE),
            "--replay-wall-epoch", tel4.wall_text(wall_epoch), "--stop-at", instant_z(STOP),
        ]
        run = tel4.run_poller(command, tmp_path, env=None, tick=None, poller_dir=poller_dir,
                              budget=2 * (STOP - START).total_seconds() / RATE + 60)
        assert run.returncode == 0, run.stderr
        assert run.start["session_start"] == instant_z(START) and run.holds == []
        assert run.exit_line is not None and run.exit_line[0] == 0
        # TEL-04-Dev2 harness delivery rule.
        _deliver_all(process.link)
        assert emulator.writes == 0
        with sqlite3.connect(f"file:{process.database.as_posix()}?mode=ro", uri=True) as db:
            envelopes = [tel4.parse_canonical_envelope_v3_text(t) for (t,) in db.execute(
                "SELECT envelope_text FROM envelope_outbox ORDER BY source_id, sequence")]
    finally:
        if emulator is not None:
            emulator.stop()
        process.kill()
        central.close()

    # TEL-T1-Q7: outcomes and values exactly at the emulator register resolution.
    profile = load_profile(PROFILE_PATH)
    expected, counters = tel4.expected_run(profile, START, STOP, replay_start=START)
    assert tel4.arrived(envelopes) == expected
    good = sum(1 for v in expected.values() if v[0] == "GOOD")
    assert tel4.assert_values_at_register_resolution(profile, envelopes) == good > 0
    assert run.exit_line[1]["counters"] == counters

    # Gate: receipts COMPLETED, nothing refused by central (a timing refusal is a stop; print it).
    refused = [(r.batch_id, d.message_id, d.decision, d.rejection) for r in receipts for d in r.dispositions
               if d.decision not in ("ACCEPTED", "DUPLICATE")]
    assert receipts and all(r.status == "COMPLETED" for r in receipts), [(r.batch_id, r.status) for r in receipts]
    assert refused == [], refused
    receipt_ids = {d.evidence_id for r in receipts for d in r.dispositions if d.decision == "ACCEPTED"}

    # Gate: accepted evidence for both bound roles.
    rows = _site_rows("SELECT id, role, device_id, signal_id, source_time, quality FROM accepted_evidence "
                      "WHERE site_id = :s ORDER BY role, source_time", site_id)
    ids = {str(r["id"]) for r in rows}
    roles = Counter(r["role"] for r in rows)
    print("TEL-05 accepted evidence:", json.dumps({"count": len(rows), "by_role": dict(roles)}))
    for r in rows:
        print("TEL-05 evidence", r["id"], r["role"], r["device_id"], r["signal_id"], r["source_time"], r["quality"])
    assert BOUND_ROLES <= set(roles), roles
    assert len(rows) == len(envelopes) and ids == receipt_ids
    print("TEL-05 receipts:", json.dumps({"batches": len(receipts), "batch_ids": sorted(r.batch_id for r in receipts)}))

    # Gate (D1(c), Q-T49): provenance UNKNOWN / NO_POSITIVE_BINDING.
    provenance = build_source_provenance(URL).resolve(UUID(tenant_id), UUID(site_id), sorted(ids))
    print("TEL-05 provenance:", json.dumps(provenance, default=str, sort_keys=True))
    assert provenance["state"] == "UNKNOWN"
    assert [reason["code"] for reason in provenance["reasons"]] == ["NO_POSITIVE_BINDING"]

    # Gate (Q-T50): the assessment completes over this evidence and records NO_GENERATOR_STATE.
    capsys.readouterr()
    assert assess_dispatch.main(["assess", "--tenant-id", tenant_id, "--site-id", site_id,
                                 "--start", "2026-09-30T03:00:00Z", "--end", "2026-09-30T15:00:00Z",
                                 "--cohort", *field_bench.cohort_members(expect)]) == 0
    assessed = json.loads(capsys.readouterr().out)
    print("TEL-05 assess:", json.dumps(assessed))
    detail = build_dispatch_read_service(URL).run(UUID(tenant_id), UUID(site_id), UUID(assessed["run_id"]))
    assert detail is not None
    cited = {str(e["evidence_id"]) for e in detail["evidence"]}
    assert cited and cited <= ids, cited - ids
    assert "NO_GENERATOR_STATE" in json.dumps(detail, default=str)

    # Gate (D5): no consequence row for the Site, in any consequence table.
    consequences = _consequence_rows(site_id)
    print("TEL-05 consequence rows:", json.dumps(consequences, sort_keys=True))
    assert consequences and not any(consequences.values()), consequences


def _deliver_all(link, deadline_s: float = 120) -> None:
    """TEL-04-Dev2: `deliver` until nothing is attempted, then again after any back-off, until none is pending."""
    deadline = time.monotonic() + deadline_s
    while True:
        while link.call("deliver", {"max_batches": 50})["batches"]["attempted"]:
            pass
        if link.call("diagnostics")["queue"]["sealed_pending_batches"] == 0:
            return
        assert time.monotonic() < deadline, "batches still pending after the delivery deadline"
        time.sleep(1.0)
