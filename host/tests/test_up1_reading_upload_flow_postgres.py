"""UP-1 resume point 2 (D-UP.3): the reading-upload flow on its own `*_test` database, end to end.

KOBO-001 converted as TEL-06b does (its gateway and sources enabled, the registered basis), one real gateway process
(the demo upload gateway's role), the host's real field checker and sender processes, the Postgres upload store and
the real batch ingestion behind a fake TLS central. The pinned TEL-06a CSV goes through `ReadingUploadService`:

    Checked (dry run, nothing written) -> Sent -> Accepted n of m -> Still processing -> the drain
    (`assess_dispatch process-jobs`) -> an `analytic_run` row (dispatch, DEFAULT, job_id set) -> Analysed,
    with the board day for the link.

The time from send to Analysed is printed (the demo script fills it).
"""

from __future__ import annotations

import json
import secrets
import sys
import time
from pathlib import Path
from uuid import UUID
from zoneinfo import ZoneInfo

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "host"))
sys.path.insert(0, str(ROOT / "backend" / "tests"))
sys.path.insert(0, str(ROOT / "gateway" / "tests"))
sys.path.insert(0, str(ROOT / "field" / "tests"))

import field_bench  # noqa: E402
import test_field_export_csv_proof as tel6a  # noqa: E402
import test_field_modbus_tcp_acceptance_postgres as tel6b  # noqa: E402
from fake_central import CERT  # noqa: E402
from gateway_process import GatewayProcess, provisioning_from_snapshot, write_config  # noqa: E402
from gateway_publication import claimed_references  # noqa: E402

URL = tel6b.URL


@pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")
def test_an_upload_is_accepted_drained_and_analysed(tmp_path: Path, monkeypatch, capsys) -> None:
    import hashlib

    import pg_harness
    import reading_upload_process as upload_process
    from sqlalchemy import create_engine, text

    from assetops_backend.analytics import assess_dispatch
    from assetops_backend.evidence.ledger import GatewayPrincipal
    from assetops_backend.reading_upload.adapters.postgres_reading_upload_store import PostgresReadingUploadStore
    from assetops_backend.reading_upload.service import ReadingUploadService
    from assetops_backend.work.operational_entry import ENTRY_PRINCIPAL
    from assetops_gateway.credential_protection import restrict_to_current_user

    def emit(*parts) -> None:
        with capsys.disabled():
            print(*parts, flush=True)

    monkeypatch.setenv("DATABASE_URL", URL)
    pg_harness.fresh_database()
    basis = tel6b._snapshot()
    snapshot_text = basis.snapshot_canonical
    snapshot_sha256 = hashlib.sha256(snapshot_text.encode("utf-8")).hexdigest()
    doc = json.loads(snapshot_text)
    tenant_id, site_id = UUID(doc["tenant_id"]), UUID(doc["site"]["site_id"])
    principal = GatewayPrincipal(tenant_id=tenant_id, site_id=site_id, gateway_id=UUID(doc["gateway"]["gateway_id"]),
                                 mode=doc["gateway"]["mode"])
    receipts: list = []
    central = tel6b._central(principal, receipts)
    state = tmp_path / "gateway"
    config = write_config(state, provisioning_from_snapshot(snapshot_text, epoch=tel6b.EPOCH))
    token = f"aog1.{secrets.token_hex(16)}.{secrets.token_urlsafe(32)}"
    (state / "upload.credential").write_text(token, encoding="ascii")
    restrict_to_current_user(state / "upload.credential")
    document = json.loads(config.read_text(encoding="utf-8"))
    document["upload"] = {"server_url": central.url, "upload_credential_file": "upload.credential",
                          "ca_file": str(CERT), "interval_seconds": 3600}  # only the sender's deliver_now delivers
    config.write_text(json.dumps(document), encoding="utf-8")
    expect = state / "expect-identity.json"
    expect.write_text(json.dumps(field_bench.expect_identity_from_snapshot(
        snapshot_text, json.loads(tel6a.PROFILE_PATH.read_text(encoding="utf-8")), tel6b.EPOCH)), encoding="utf-8")
    gateway = {"gateway_address": document["address"], "ipc_credential": str(state / "gateway.credential"),
               "snapshot_sha256": snapshot_sha256, "expect_identity": str(expect)}
    store = PostgresReadingUploadStore(URL)
    service = ReadingUploadService(upload_process.ProcessFileChecker(), upload_process.ProcessReadingSender(gateway),
                                   store, entered_by=ENTRY_PRINCIPAL, template=upload_process.template_csv)
    data = tel6a.FIXTURE.read_bytes()
    process = GatewayProcess(config)
    engine = create_engine(URL)
    try:
        assert process.ready, process.first_line
        activated = process.link.call("activate", {"snapshot_text": snapshot_text, "claimed": claimed_references(basis)})
        assert activated == {"snapshot_sha256": snapshot_sha256}

        status, checked = service.upload(tenant_id, site_id, "kobo-window.csv", data, dry_run=True)
        assert (status, checked["state"]) == (200, "CHECKED"), checked
        with engine.connect() as c:
            assert c.execute(text("SELECT count(*) FROM reading_upload")).scalar_one() == 0  # a dry run writes nothing

        sent_at = time.monotonic()
        status, sent = service.upload(tenant_id, site_id, "kobo-window.csv", data, dry_run=False)
        emit("UP-1 flow sent:", json.dumps({k: sent[k] for k in ("state", "counts")}))
        assert status == 201 and sent["counts"]["admitted"] == tel6a.CELLS and sent["counts"]["held"] == 0
        upload_id = UUID(sent["upload_id"])
    finally:
        process.kill()
        central.close()

    assert receipts and all(r.status == "COMPLETED" for r in receipts), [(r.batch_id, r.status) for r in receipts]
    _, before = service.status(tenant_id, site_id, upload_id)
    emit("UP-1 flow before the drain:", json.dumps({k: before[k] for k in ("state", "counts")}))
    assert before["state"] == "PROCESSING" and before["counts"]["accepted"] == tel6a.CELLS  # Still processing
    with engine.connect() as c:
        jobs = c.execute(text("SELECT domain, status, count(*) FROM recompute_job WHERE site_id = :s "
                              "GROUP BY domain, status ORDER BY domain, status"), {"s": site_id}).all()
    emit("UP-1 flow jobs before the drain:", [tuple(j) for j in jobs])

    capsys.readouterr()
    assert assess_dispatch.main(["process-jobs"]) == 0
    outcomes = json.loads(capsys.readouterr().out)
    emit("UP-1 flow process-jobs:", json.dumps([{k: o[k] for k in ("job_id", "status", "error")} for o in outcomes]))
    assert outcomes and all(o["status"] == "DONE" for o in outcomes), outcomes

    with engine.connect() as c:
        runs = c.execute(text("SELECT analytic_id, selection, job_id IS NOT NULL AS by_job, window_start, window_end, "
                              "knowledge_cutoff FROM analytic_run WHERE site_id = :s ORDER BY window_start"),
                         {"s": site_id}).mappings().all()
        left = c.execute(text("SELECT domain, status FROM recompute_job WHERE site_id = :s "
                              "AND status <> 'DONE'"), {"s": site_id}).all()
    emit("UP-1 flow analytic_run rows:", json.dumps([dict(r) for r in runs], default=str))
    emit("UP-1 flow jobs not DONE after the drain:", [tuple(j) for j in left])
    assert any(r["analytic_id"] == "dispatch" and r["selection"] == "DEFAULT" and r["by_job"] for r in runs), runs

    _, after = service.status(tenant_id, site_id, upload_id)
    elapsed = time.monotonic() - sent_at
    emit("UP-1 flow after the drain:", json.dumps({k: after.get(k) for k in ("state", "counts", "board_day")}),
         f"send-to-Analysed {elapsed:.1f} s (test drain, not the serve tick)")
    assert after["state"] == "ANALYSED", after
    with engine.connect() as c:
        zone, first = c.execute(text("SELECT s.timezone, u.period_start FROM reading_upload u JOIN site s "
                                     "ON s.id = u.site_id WHERE u.id = :u"), {"u": upload_id}).one()
    assert after["board_day"] == first.astimezone(ZoneInfo(zone)).date().isoformat()  # the board link's ?date=
    engine.dispose()
    store.dispose()
