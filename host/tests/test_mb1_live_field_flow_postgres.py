"""MB-1 (D-17N.6): the live Modbus flow on its own `*_test` database, end to end, with an uplink stop.

KOBO-001 converted with the S3 then S6 demo configurations (as TEL-05b), the prolonged basis, one real gateway process
on an edge epoch (the Kobo edge gateway's role), the live-window readings MB-1 generates
(`field_observation_fixtures.generate_live_window`) replayed by the GX-shaped emulator, the real poller CLI with
profile `gx-system-illustrative-2`, and the real batch ingestion behind a fake TLS central.

Gates (TEL-05's, plus the uplink stop and the no-overlap finish check):
- the central is down for a stretch of the run: the gateway's sealed backlog rises, then drains to 0 after recovery;
- every upload receipt COMPLETED, accepted evidence for every profile row, no interval gap across the stop;
- `demo_live_field.OVERLAP_SQL` finds no overlapping (Site, source, interval);
- `assess_dispatch process-jobs` -> an `analytic_run` row (dispatch, DEFAULT, by job): the window is analysed.
The replay runs at rate 60 (2 source hours in 2 wall minutes); the demo runs the same path at rate 1.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

import pytest

ROOT = Path(__file__).resolve().parents[2]
for part in ("tools", "backend/tests", "gateway/tests", "field/tests"):
    sys.path.insert(0, str(ROOT / part))

import demo_live_field as lf  # noqa: E402
import field_bench  # noqa: E402
import field_observation_fixtures as fixtures  # noqa: E402
import test_field_modbus_tcp_acceptance_postgres as tel5  # noqa: E402
import test_field_modbus_tcp_proof as tel4  # noqa: E402
from fake_central import CERT, FakeCentral  # noqa: E402
from field_emulators.gx_server import GxEmulator, ObservationTimeline  # noqa: E402
from gateway_process import GatewayProcess, provisioning_from_snapshot, write_config  # noqa: E402
from gateway_publication import claimed_references  # noqa: E402

from assetops_field.clock import ReplayClock  # noqa: E402
from assetops_field.profile import load_profile  # noqa: E402

URL = tel5.URL
RATE = 60
START = datetime(2026, 10, 13, 3, 0, tzinfo=timezone.utc)
STOP = START + timedelta(hours=2)
EPOCH = "kobo-edge-mb1flowtest"
DOWN = (35.0, 65.0)  # wall seconds after the poller starts: the central answers 503 (the uplink stop)


def _z(instant: datetime) -> str:
    return instant.strftime("%Y-%m-%dT%H:%M:%SZ")


@pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")
def test_live_modbus_is_accepted_across_an_uplink_stop_and_analysed(tmp_path: Path, monkeypatch, capsys) -> None:
    import pg_harness
    from sqlalchemy import create_engine, text

    from assetops_backend.analytics import assess_dispatch
    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.evidence.ledger import GatewayPrincipal
    from assetops_backend.evidence.ledger_service import BatchIngestionService
    from assetops_contracts.ingestion_receipt_v2 import canonical_receipt_v2_text
    from assetops_gateway.credential_protection import restrict_to_current_user

    def emit(*parts) -> None:
        with capsys.disabled():
            print(*parts, flush=True)

    monkeypatch.setenv("DATABASE_URL", URL)
    pg_harness.fresh_database()
    basis = tel5._snapshot_2()
    snapshot_text = basis.snapshot_canonical
    snapshot_sha256 = hashlib.sha256(snapshot_text.encode("utf-8")).hexdigest()
    doc = json.loads(snapshot_text)
    tenant_id, site_id = doc["tenant_id"], doc["site"]["site_id"]
    principal = GatewayPrincipal(tenant_id=UUID(tenant_id), site_id=UUID(site_id),
                                 gateway_id=UUID(doc["gateway"]["gateway_id"]), mode=doc["gateway"]["mode"])

    readings = tmp_path / "readings"
    manifest = fixtures.generate_live_window(readings, _z(START), _z(START + timedelta(hours=lf.MAX_HOURS)))
    emit("MB-1 flow readings:", json.dumps({k: manifest[k] for k in ("window", "observation_count", "sha256")}))
    profile = load_profile(lf.PROFILE)

    ingestion = BatchIngestionService(PostgresEvidenceLedger(URL))
    receipts: list = []
    refused_while_down = [0]
    down = [False]

    def batches(path, headers, body):
        if down[0]:
            refused_while_down[0] += 1
            return 503, b""
        answer = ingestion.submit(principal, body)
        receipts.append(answer.receipt)
        return answer.status, canonical_receipt_v2_text(answer.receipt).encode("utf-8")

    central = FakeCentral(tel4.with_diagnostics(batches))
    state = tmp_path / "gateway"
    config = write_config(state, provisioning_from_snapshot(snapshot_text, epoch=EPOCH))
    token = f"aog1.{secrets.token_hex(16)}.{secrets.token_urlsafe(32)}"
    (state / "upload.credential").write_text(token, encoding="ascii")
    restrict_to_current_user(state / "upload.credential")
    document = json.loads(config.read_text(encoding="utf-8"))
    document["upload"] = {"server_url": central.url, "upload_credential_file": "upload.credential",
                          "ca_file": str(CERT), "interval_seconds": 3600}  # the harness delivers (TEL-04-Dev2)
    config.write_text(json.dumps(document), encoding="utf-8")
    activation = tmp_path / "activation.json"
    activation.write_text(json.dumps({"snapshot_text": snapshot_text, "claimed": claimed_references(basis)}),
                          encoding="utf-8")
    process = GatewayProcess(config)
    emulator = None
    backlog: list[int] = []
    try:
        assert process.ready, process.first_line
        activated = field_bench.activate(document["address"], state / "gateway.credential", activation)
        assert activated == {"snapshot_sha256": snapshot_sha256}
        expect_path = tmp_path / "expect-identity.json"
        expect = field_bench.expect_identity_from_snapshot(
            snapshot_text, json.loads(lf.PROFILE.read_text(encoding="utf-8")), EPOCH)
        expect_path.write_text(json.dumps(expect), encoding="utf-8")

        wall_epoch = datetime.now(timezone.utc) + tel4.EPOCH_LEAD
        emulator = GxEmulator(ObservationTimeline(readings / "observations.jsonl", profile),
                              ReplayClock(START, RATE, wall_epoch), host="127.0.0.1", port=0)
        emulator.start()
        poller_dir = tmp_path / "poller"
        gateway = {"gateway_address": document["address"], "ipc_credential": str(state / "gateway.credential"),
                   "snapshot_sha256": snapshot_sha256}
        command = lf.poller_argv(sys.executable, gateway, expect_path, poller_dir, STOP, port=emulator.port)
        command[command.index("--stop-at"):command.index("--stop-at")] = [
            "--replay-start", _z(START), "--replay-rate", str(RATE), "--replay-wall-epoch", tel4.wall_text(wall_epoch)]
        began = time.monotonic()
        last = [0.0]

        def tick(_: Path) -> None:  # deliver every 2 s, as the gateway's own uploader would; the stop in between
            elapsed = time.monotonic() - began
            down[0] = DOWN[0] <= elapsed < DOWN[1]
            if elapsed - last[0] >= 2.0:
                last[0] = elapsed
                process.link.call("deliver", {"max_batches": 50})
                queue = process.link.call("diagnostics")["queue"]
                backlog.append(queue["sealed_pending_batches"] if down[0] else -1)

        run = tel4.run_poller(command, tmp_path, env=None, tick=tick, poller_dir=poller_dir,
                              budget=2 * (STOP - START).total_seconds() / RATE + 60)
        assert run.returncode == 0, run.stderr
        assert run.exit_line is not None and run.exit_line[0] == 0
        down[0] = False
        tel5._deliver_all(process.link)
        after = process.link.call("diagnostics")["queue"]
        assert emulator.writes == 0
    finally:
        if emulator is not None:
            emulator.stop()
        process.kill()
        central.close()

    during = [b for b in backlog if b >= 0]
    emit("MB-1 flow uplink stop:", json.dumps({"refused_while_down": refused_while_down[0], "backlog_during": during,
                                               "queue_after": after}))
    assert refused_while_down[0] > 0 and during and max(during) > min(during)  # a real backlog formed
    assert after["sealed_pending_batches"] == 0
    assert receipts and all(r.status == "COMPLETED" for r in receipts), [(r.batch_id, r.status) for r in receipts]

    evidence = field_bench.read(URL, "KOBO-001", "evidence", _z(START), _z(STOP))
    emit("MB-1 flow evidence:", json.dumps(evidence, default=str))
    signals = {(e["device_id"], e["signal_id"]) for e in evidence if e["sequence_epoch"] == EPOCH}
    assert signals == {(row.device_id, row.signal_id) for row in profile.rows}

    engine = create_engine(URL)
    with engine.connect() as c:
        intervals = c.execute(text(
            "SELECT device_id, signal_id, interval_start, interval_end FROM accepted_evidence WHERE site_id = :s "
            "AND sequence_epoch = :e AND interval_start IS NOT NULL ORDER BY 1, 2, 3"), {"s": site_id, "e": EPOCH}).all()
        overlaps = c.execute(text(lf.OVERLAP_SQL), {"t": tenant_id, "site": site_id, "epoch": EPOCH,
                                                    "lo": START - timedelta(days=1)}).all()
    gaps = [(a.device_id, a.signal_id, a.interval_end, b.interval_start) for a, b in zip(intervals, intervals[1:])
            if (a.device_id, a.signal_id) == (b.device_id, b.signal_id) and a.interval_end != b.interval_start]
    assert intervals and gaps == [], gaps  # no evidence gap across the stop
    assert overlaps == [], overlaps  # the finish check

    # the tool's own DB reads, on the flow's data
    latest = lf.latest_accepted(expect)
    assert set(latest) == set(expect["row_sources"]), latest  # every profile row, incl. sources shared by two rows
    assert lf.overlap_refusal(latest, START) != [] and lf.overlap_refusal(latest, STOP) == []
    assert lf.disabled_sources(expect) == []  # the flow enabled every source it feeds
    with engine.connect() as c:  # the finish check finds a real overlap: shift one interval, then roll back
        trans = c.begin()  # the ledger is append-only; the trigger is disabled inside this rolled-back transaction only
        c.execute(text("ALTER TABLE accepted_evidence DISABLE TRIGGER USER"))
        victim = c.execute(text(
            "SELECT id FROM accepted_evidence WHERE site_id = :s AND sequence_epoch = :e AND interval_start IS NOT NULL "
            "ORDER BY device_id, signal_id, interval_start LIMIT 1"), {"s": site_id, "e": EPOCH}).scalar_one()
        c.execute(text("UPDATE accepted_evidence SET interval_end = interval_end + interval '150 seconds' "
                       "WHERE id = :i"), {"i": victim})
        shifted = c.execute(text(lf.OVERLAP_SQL), {"t": tenant_id, "site": site_id, "epoch": EPOCH,
                                                   "lo": START - timedelta(days=1)}).all()
        trans.rollback()
    assert shifted, "the overlap check must see a shifted interval"

    capsys.readouterr()
    assert assess_dispatch.main(["process-jobs"]) == 0
    outcomes = json.loads(capsys.readouterr().out)
    assert outcomes and all(o["status"] == "DONE" for o in outcomes), outcomes
    runs = field_bench.read(URL, "KOBO-001", "runs", _z(START), _z(STOP))
    emit("MB-1 flow analytic runs:", json.dumps(runs, default=str))
    assert any(r["analytic_id"] == "dispatch" and r["selection"] == "DEFAULT" and r["by_job"] for r in runs), runs
    engine.dispose()
