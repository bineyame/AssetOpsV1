"""TEL-05: Postgres acceptance of profile `gx-system-illustrative-1` (run alone; Q-T56).

GX-shaped emulator (in-process) -> poller subprocess -> real gateway process ->
`FakeCentral` whose batch route is the real `BatchIngestionService` over
`PostgresEvidenceLedger` with the real UTC clock (Q-T47, no decision-clock
override). The Site is KOBO-001 converted inside the `*_test` database only
(owner Q4 / D2). No simulation publication is attached, so the source class
resolves UNKNOWN (D1(c)), and no consequence row may exist (D5).

TEL-05b (amendment 2, N1 replaced; build spec TEL-05b): profile
`gx-system-illustrative-2` over the registered `kobo-mini-grid-prolonged`
run's public observations. The same path; then `process-jobs` and
`match-findings` raise a dispatch Finding citing only this test's evidence,
whose provenance is UNKNOWN / NO_POSITIVE_BINDING; the price timeline is
seeded by the S4 CLI, consequences are recomputed, and every read through the
production app withholds the current amount with `MIXED_OR_UNKNOWN_SOURCE`.

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
from datetime import datetime, timedelta, timezone
from fractions import Fraction
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
from field_emulators.gx_server import GxEmulator, ObservationTimeline, presented_value  # noqa: E402
from gateway_process import GatewayProcess, provisioning_from_snapshot, write_config  # noqa: E402
from gateway_publication import claimed_references  # noqa: E402

from assetops_contracts.observation import quantize_half_even  # noqa: E402

from assetops_field.aggregate import PollOutcome, expected_polls  # noqa: E402
from assetops_field.clock import ReplayClock  # noqa: E402
from assetops_field.profile import load_profile, profile_sha256  # noqa: E402
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

    def emit(*parts) -> None:  # printed past capsys, which the assess call reads (Q-T50)
        with capsys.disabled():
            print(*parts, flush=True)

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
    emit("TEL-05 accepted evidence:", json.dumps({"count": len(rows), "by_role": dict(roles)}))
    for r in rows:
        emit("TEL-05 evidence", r["id"], r["role"], r["device_id"], r["signal_id"], r["source_time"], r["quality"])
    assert BOUND_ROLES <= set(roles), roles
    assert len(rows) == len(envelopes) and ids == receipt_ids
    emit("TEL-05 receipts:", json.dumps({"batches": len(receipts), "batch_ids": sorted(r.batch_id for r in receipts)}))

    # Gate (D1(c), Q-T49): provenance UNKNOWN / NO_POSITIVE_BINDING.
    provenance = build_source_provenance(URL).resolve(UUID(tenant_id), UUID(site_id), sorted(ids))
    emit("TEL-05 provenance:", json.dumps(provenance, default=str, sort_keys=True))
    assert provenance["state"] == "UNKNOWN"
    assert [reason["code"] for reason in provenance["reasons"]] == ["NO_POSITIVE_BINDING"]

    # Gate (Q-T50): the assessment completes over this evidence and records NO_GENERATOR_STATE.
    capsys.readouterr()
    assert assess_dispatch.main(["assess", "--tenant-id", tenant_id, "--site-id", site_id,
                                 "--start", "2026-09-30T03:00:00Z", "--end", "2026-09-30T15:00:00Z",
                                 "--cohort", *field_bench.cohort_members(expect)]) == 0
    assessed = json.loads(capsys.readouterr().out)
    emit("TEL-05 assess:", json.dumps(assessed))
    detail = build_dispatch_read_service(URL).run(UUID(tenant_id), UUID(site_id), UUID(assessed["run_id"]))
    assert detail is not None
    cited = {str(e["evidence_id"]) for e in detail["evidence"]}
    assert cited and cited <= ids, cited - ids
    assert "NO_GENERATOR_STATE" in json.dumps(detail, default=str)

    # Gate (D5): no consequence row for the Site, in any consequence table.
    consequences = _consequence_rows(site_id)
    emit("TEL-05 consequence rows:", json.dumps(consequences, sort_keys=True))
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


# --- TEL-05b: profile -2, a dispatch Finding with no money shown (amendment 2, N1 replaced) -------------------

PROFILE_2_PATH = ROOT / "field" / "profiles" / "gx-system-illustrative-2.json"
JSONL_2 = ROOT / "contract-fixtures" / "telemetry" / "kobo-prolonged-public-observations-v1" / "observations.jsonl"
START_2 = datetime(2026, 10, 13, 3, 0, tzinfo=timezone.utc)
STOP_2 = datetime(2026, 10, 13, 11, 0, tzinfo=timezone.utc)
DISPATCH_ROLES = {"generator_state", "generator_power", "feeder_demand", "pv_available_power",
                  "pcs_discharge_capability", "battery_soc"}
PRICE_FIXTURE = ROOT / "backend" / "conversions" / "demo-diesel-price-publications.json"
SOURCE_WITHHELD = "MIXED_OR_UNKNOWN_SOURCE"


def _snapshot_2():
    """KOBO-001 converted in the test database, the S3 then S6 demo configurations applied as
    `test_s6_verification_publication.configure()`, gateway and sources enabled, the prolonged draft."""
    import test_s1_bindings_postgres as pgb
    import test_s6_verification_publication as s6
    from sqlalchemy import create_engine, text

    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore

    store = PostgresFoundationStore(URL)
    result, _ = pgb.converted(store)
    s6.configure(store, result)
    engine = create_engine(URL)
    try:
        with engine.begin() as connection:  # stand in for credential provisioning (as the S2 ledger tests do)
            connection.execute(text("UPDATE gateway SET disabled_at = NULL WHERE site_id = :s"), {"s": result.site.id})
            connection.execute(text("UPDATE source SET disabled_at = NULL WHERE site_id = :s"), {"s": result.site.id})
    finally:
        engine.dispose()
    run, _ = s6.draft(store)
    return run.registered_basis


def _expected_value_2(timeline: ObservationTimeline, row, instant: datetime):
    """TEL-T1-Q7: unit-101 (ILLUSTRATIVE) rows exactly as published; the unit-100 PV row at its register
    resolution; the ENUM row its state text."""
    observation = timeline.hold_at(row.row_id, instant).observation
    assert observation["outcome"] == "REPORTED"
    if row.decode == "ENUM":
        return observation["reported_value"]
    if row.status == "ILLUSTRATIVE":
        return Fraction(observation["reported_value"])
    return quantize_half_even(presented_value(row, Fraction(observation["reported_value"])), row.output_resolution)


def _expected_run_2(profile, timeline: ObservationTimeline, start: datetime, stop: datetime):
    """The TEL-04 oracle (`tel4.expected_run`, no faults, session start = replay start) over profile -2."""
    reports: dict[tuple[str, str, str], tuple] = {}
    counters: Counter = Counter()
    for row in profile.rows:
        cadence = timedelta(seconds=row.cadence_seconds)
        if row.reading_class == "INTERVAL_SIGNAL":
            span = timedelta(seconds=row.span_seconds)
            end = start + cadence
            while end <= stop:
                polls = expected_polls(row, end - span)
                outcomes = [tel4.oracle_outcome(timeline, row, p, ()) for p in polls]
                counters.update(outcome.value for outcome in outcomes)
                key = (row.device_id, row.signal_id, instant_z(end))
                if not any(o in (PollOutcome.VALUE, PollOutcome.NO_VALUE) for o in outcomes):
                    pass  # no poll answered: nothing is published
                elif all(o is PollOutcome.VALUE for o in outcomes):
                    reports[key] = ("GOOD", None, instant_z(end - span), _expected_value_2(timeline, row, polls[0]))
                else:
                    reports[key] = ("UNAVAILABLE", "NO_MEASUREMENT", instant_z(end - span), None)
                end += cadence
        else:
            boundary = start
            while boundary <= stop:
                read_at = boundary + timedelta(seconds=1)  # B + ceil(skew / 2)
                outcome = tel4.oracle_outcome(timeline, row, read_at, ())
                counters[outcome.value] += 1
                key = (row.device_id, row.signal_id, instant_z(boundary))
                if outcome is PollOutcome.VALUE:
                    reports[key] = ("GOOD", None, None, _expected_value_2(timeline, row, read_at))
                elif outcome is PollOutcome.NO_VALUE:
                    reports[key] = ("UNAVAILABLE", "NO_MEASUREMENT", None, None)
                boundary += cadence
    for name in ("VALUE", "NO_VALUE", "FAILED", "NO_ANSWER", "CONFIG_FAULT", "SKIPPED_LATE"):
        counters.setdefault(name, 0)
    return reports, dict(counters)


def _arrived_2(profile, envelopes) -> dict[tuple[str, str, str], tuple]:
    """`tel4.arrived`, keeping an ENUM row's state text as text."""
    enum_signals = {(row.device_id, row.signal_id) for row in profile.rows if row.decode == "ENUM"}
    out = {}
    for e in envelopes:
        if e.value is None or (e.device_id, e.signal_id) in enum_signals:
            value = e.value
        else:
            value = Fraction(e.value)
        out[(e.device_id, e.signal_id, e.source_time)] = (e.quality, e.unavailable_reason, e.interval_start, value)
    return out


def _assert_exact_against_the_source(profile, timeline: ObservationTimeline, envelopes) -> int:
    """TEL-T1-Q7, independently of the oracle: unit-101 GOOD values equal `Fraction(reported_value)` exactly
    (ENUM: the same text); the unit-100 PV row within half its register quantum."""
    rows = {(row.device_id, row.signal_id): row for row in profile.rows}
    checked = 0
    for e in envelopes:
        if e.quality != "GOOD":
            continue
        row = rows[(e.device_id, e.signal_id)]
        instant = tel4.at(e.source_time) + (timedelta(seconds=-1) if e.interval_start else timedelta(seconds=1))
        observation = timeline.hold_at(row.row_id, instant).observation
        assert observation["outcome"] == "REPORTED", (e, observation)
        if row.decode == "ENUM":
            assert e.value == observation["reported_value"], (e, observation)
        elif row.status == "ILLUSTRATIVE":
            assert Fraction(e.value) == Fraction(observation["reported_value"]), (e, observation)
        else:
            quantum = row.register_quantum * Fraction(10) ** row.exponent
            assert abs(Fraction(e.value) - Fraction(observation["reported_value"])) <= quantum / 2, (e, observation)
        checked += 1
    return checked


def _current_amount_paths(value, path: str = "$") -> list[str]:
    """Every place a read presents an amount as current: `current_amount_shown` or `presented_as_current` true."""
    found: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key in ("current_amount_shown", "presented_as_current") and item is True:
                found.append(f"{path}.{key}")
            found += _current_amount_paths(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found += _current_amount_paths(item, f"{path}[{index}]")
    return found


@pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")
def test_gx_profile_2_raises_a_finding_with_no_money_shown(tmp_path: Path, monkeypatch, capsys) -> None:
    import pg_harness
    from fastapi.testclient import TestClient

    from assetops_backend import main as backend_main
    from assetops_backend import publish_assumption, recompute_consequences
    from assetops_backend.analytics import assess_dispatch
    from assetops_backend.analytics.composition import build_finding_read_service, build_finding_store
    from assetops_backend.evidence.composition import build_source_provenance
    from assetops_backend.evidence.ledger import GatewayPrincipal
    from assetops_gateway.credential_protection import restrict_to_current_user

    def emit(*parts) -> None:  # printed past capsys, which the CLI calls read (Q-T50)
        with capsys.disabled():
            print(*parts, flush=True)

    def cli(module, argv: list[str]):
        capsys.readouterr()
        code = module.main(argv)
        out = capsys.readouterr()
        assert code == 0, (module.__name__, argv, code, out.err)
        return out.out

    monkeypatch.setenv("DATABASE_URL", URL)
    pg_harness.fresh_database()
    basis = _snapshot_2()
    snapshot_text = basis.snapshot_canonical
    snapshot_sha256 = hashlib.sha256(snapshot_text.encode("utf-8")).hexdigest()
    doc = json.loads(snapshot_text)
    tenant_id, site_id = doc["tenant_id"], doc["site"]["site_id"]
    principal = GatewayPrincipal(tenant_id=UUID(tenant_id), site_id=UUID(site_id),
                                 gateway_id=UUID(doc["gateway"]["gateway_id"]), mode=doc["gateway"]["mode"])
    profile_document = json.loads(PROFILE_2_PATH.read_text(encoding="utf-8"))
    profile = load_profile(PROFILE_2_PATH)
    emit("TEL-05b profile:", json.dumps({"profile_id": profile.profile_id, "version": profile.profile_version,
                                          "status": profile.status, "sha256": profile_sha256(profile_document)}))

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
        expect = field_bench.expect_identity_from_snapshot(snapshot_text, profile_document, EPOCH)
        expect_path = tmp_path / "expect-identity.json"
        expect_path.write_text(json.dumps(expect), encoding="utf-8")

        wall_epoch = datetime.now(timezone.utc) + tel4.EPOCH_LEAD
        emulator = GxEmulator(ObservationTimeline(JSONL_2, profile), ReplayClock(START_2, RATE, wall_epoch),
                              host="127.0.0.1", port=0)
        emulator.start()
        poller_dir = tmp_path / "poller"
        command = [
            sys.executable, "-m", "assetops_field.modbus_poller", "--profile", str(PROFILE_2_PATH),
            "--host", "127.0.0.1", "--port", str(emulator.port), "--gateway-address", document["address"],
            "--ipc-credential", str(state / "gateway.credential"), "--snapshot-sha256", snapshot_sha256,
            "--expect-identity", str(expect_path), "--state-dir", str(poller_dir), "--read-timeout-s", "0.25",
            "--replay-start", instant_z(START_2), "--replay-rate", str(RATE),
            "--replay-wall-epoch", tel4.wall_text(wall_epoch), "--stop-at", instant_z(STOP_2),
        ]
        run = tel4.run_poller(command, tmp_path, env=None, tick=None, poller_dir=poller_dir,
                              budget=2 * (STOP_2 - START_2).total_seconds() / RATE + 60)
        assert run.returncode == 0, run.stderr
        assert run.start["session_start"] == instant_z(START_2) and run.holds == []
        assert run.exit_line is not None and run.exit_line[0] == 0
        _deliver_all(process.link)  # TEL-04-Dev2 harness delivery rule
        assert emulator.writes == 0
        with sqlite3.connect(f"file:{process.database.as_posix()}?mode=ro", uri=True) as db:
            envelopes = [tel4.parse_canonical_envelope_v3_text(t) for (t,) in db.execute(
                "SELECT envelope_text FROM envelope_outbox ORDER BY source_id, sequence")]
    finally:
        if emulator is not None:
            emulator.stop()
        process.kill()
        central.close()

    # TEL-T1-Q7: unit-101 rows exactly as the source published them; the PV row at its register resolution.
    timeline = ObservationTimeline(JSONL_2, profile)
    expected, counters = _expected_run_2(profile, timeline, START_2, STOP_2)
    assert _arrived_2(profile, envelopes) == expected
    good = sum(1 for v in expected.values() if v[0] == "GOOD")
    assert _assert_exact_against_the_source(profile, timeline, envelopes) == good > 0
    assert run.exit_line[1]["counters"] == counters

    # Receipts COMPLETED and nothing refused by central (any refusal is a stop; print it).
    refused = [(r.batch_id, d.message_id, d.decision, d.rejection) for r in receipts for d in r.dispositions
               if d.decision not in ("ACCEPTED", "DUPLICATE")]
    assert receipts and all(r.status == "COMPLETED" for r in receipts), [(r.batch_id, r.status) for r in receipts]
    assert refused == [], refused
    receipt_ids = {d.evidence_id for r in receipts for d in r.dispositions if d.decision == "ACCEPTED"}
    rows = _site_rows("SELECT id, role, device_id, signal_id, source_time, quality FROM accepted_evidence "
                      "WHERE site_id = :s ORDER BY role, source_time", site_id)
    ids = {str(r["id"]) for r in rows}
    roles = Counter(r["role"] for r in rows)
    emit("TEL-05b accepted evidence:", json.dumps({"count": len(rows), "by_role": dict(sorted(roles.items()))}))
    emit("TEL-05b receipts:", json.dumps({"batches": len(receipts), "batch_ids": sorted(r.batch_id for r in receipts)}))
    assert DISPATCH_ROLES <= set(roles), roles
    assert len(rows) == len(envelopes) and ids == receipt_ids

    # Step 1 (Q-T51, Q-T54): the jobs ingestion created, then the matcher over the default selection.
    outcomes = json.loads(cli(assess_dispatch, ["process-jobs"]))
    emit("TEL-05b process-jobs:", json.dumps([{k: o[k] for k in ("job_id", "status", "error")} for o in outcomes]))
    assert outcomes and all(o["status"] == "DONE" for o in outcomes), outcomes
    matched = json.loads(cli(assess_dispatch, ["match-findings", "--tenant-id", tenant_id, "--site-id", site_id]))
    emit("TEL-05b match-findings:", json.dumps(matched, default=str, sort_keys=True))

    # Step 2: a dispatch Finding exists; its latest revision cites only this test's evidence; provenance UNKNOWN.
    finding_rows = build_finding_store(URL).rows(UUID(tenant_id), UUID(site_id))
    findings = finding_rows["findings"]
    assert findings, f"STOP: no Finding arose; window_statuses {matched['window_statuses']}"
    reads = build_finding_read_service(URL)
    provenance_reads = build_source_provenance(URL)
    pinned: list[tuple[str, str]] = []
    for finding in findings:
        fid = str(finding["id"])
        frid = str(reads.finding(UUID(tenant_id), UUID(site_id), UUID(fid))["selection"]["latest_revision_id"])
        provenance = provenance_reads.finding_revision(UUID(tenant_id), UUID(site_id), UUID(frid))
        emit("TEL-05b finding:", json.dumps({"finding_id": fid, "finding_revision_id": frid,
                                             "anchor_start": str(finding["anchor_start"])}))
        emit("TEL-05b finding provenance:", json.dumps(provenance, default=str, sort_keys=True))
        assert provenance is not None
        cited = set(provenance["cited_accepted_evidence_ids"])
        assert cited and cited <= ids, sorted(cited - ids)
        assert provenance["state"] == "UNKNOWN"
        assert [reason["code"] for reason in provenance["reasons"]] == ["NO_POSITIVE_BINDING"]
        pinned.append((fid, frid))
    assert any(str(f["anchor_start"])[:10] == "2026-10-13" for f in findings), [f["anchor_start"] for f in findings]

    # Step 3 (Q-T52): the price timeline, by the S4 seeding CLI, every step in order (no --step).
    published = cli(publish_assumption, ["fixture", "--site", "KOBO-001", "--file", str(PRICE_FIXTURE)])
    emit("TEL-05b price publications:", published.strip().replace("\n", " | "))
    # Step 4: the consequence runner, exit 0.
    recomputed = cli(recompute_consequences, ["run", "--tenant", "demo", "--site", "KOBO-001"])
    emit("TEL-05b recompute:", recomputed.strip().replace("\n", " | "))
    revisions = _site_rows("SELECT id, finding_id, finding_revision_id, revision_no, state, price_state, "
                           "price_reason, price_revision_id, amount_low, amount_high, currency FROM "
                           "financial_consequence_revision WHERE site_id = :s ORDER BY finding_id, revision_no",
                           site_id)
    emit("TEL-05b consequence revisions:", json.dumps(revisions, default=str))
    # TEL-05b-Q2: zero consequence revisions, or none PRICED with amounts, is a STOP (the withholding must be
    # shown on a recorded figure by the source gate, not by a missing amount). Report, do not tune.
    stop_report = f"recompute output: {recomputed.strip()!r}; consequence revisions: {revisions}"
    for fid, frid in pinned:
        own = [r for r in revisions if str(r["finding_id"]) == fid and str(r["finding_revision_id"]) == frid]
        assert own, f"STOP (TEL-05b-Q2): no consequence revision for Finding {fid} revision {frid}; {stop_report}"
    assert any(r["state"] == "PRICED" and r["amount_low"] is not None and r["amount_high"] is not None
               for r in revisions), f"STOP (TEL-05b-Q2): no PRICED consequence revision with amounts; {stop_report}"

    # Step 5: API reads through the production composition; no current amount anywhere.
    with TestClient(backend_main.create_app()) as client:
        index = client.get("/api/sites/KOBO-001/finding-index", params={
            "domain": "mini-grid-dispatch", "from": "2026-10-13T00:00:00Z", "to": "2026-10-14T00:00:00Z"})
        emit("TEL-05b finding index:", index.status_code, json.dumps(index.json(), default=str, sort_keys=True))
        index_body = index.json()
        assert index.status_code in (200, 409), index_body  # TEL-05b-Q1: any other status fails
        if index.status_code == 200:
            index_rows = index_body.get("rows") or []
            if index_body.get("status") == "CURRENT":
                assert index_rows, "a CURRENT index page is empty although the 2026-10-13 Finding is in the window"
            assert all(r["amount"]["state"] == "UNAVAILABLE" for r in index_rows), index_rows
        else:
            assert index_body["detail"]["code"] == "PERFORMANCE_CUTOVER_CLOSED"
            assert index_body["detail"]["rows"] is None
        assert _current_amount_paths(index_body) == []

        consequence_reads = []
        for fid, frid in pinned:
            finding_read = client.get(f"/api/sites/KOBO-001/findings/{fid}", params={"revision_id": frid})
            assert finding_read.status_code == 200, finding_read.text
            body = finding_read.json()
            emit("TEL-05b finding read consequence:", json.dumps(body["consequence"], default=str, sort_keys=True))
            assert body["consequence"]["amount"] is None and body["consequence"]["state"] != "PRICED"
            assert _current_amount_paths(body) == []
            head = client.get(f"/api/sites/KOBO-001/findings/{fid}/financial-consequences",
                              params={"revision_id": frid})
            consequence_reads.append((fid, frid, None, head))
        for revision in revisions:
            pinned_read = client.get(f"/api/sites/KOBO-001/findings/{revision['finding_id']}/financial-consequences",
                                     params={"revision_id": str(revision["finding_revision_id"]),
                                             "consequence_revision_id": str(revision["id"])})
            consequence_reads.append((str(revision["finding_id"]), str(revision["finding_revision_id"]),
                                      str(revision["id"]), pinned_read))
        for fid, frid, crid, answer in consequence_reads:
            assert answer.status_code == 200, (fid, frid, crid, answer.text)
            read = answer.json()
            currentness = read["currentness"]
            selected = read["consequence"]
            emit("TEL-05b consequence read:", json.dumps({
                "finding_id": fid, "finding_revision_id": frid, "consequence_revision_id": crid,
                "current_amount_shown": currentness["current_amount_shown"],
                "withheld_reasons": currentness["withheld_reasons"], "source_gate": currentness["source_gate"],
                "consequence": None if selected is None else {
                    k: selected.get(k) for k in ("id", "state", "amount", "presented_as_current")},
                "consequence_provenance_state": None if selected is None
                else (selected.get("source_provenance") or {}).get("state")}, default=str, sort_keys=True))
            # TEL-05b-Q2 (3), (4): a selected revision exists, is not presented as current, and its own
            # source provenance is UNKNOWN.
            assert selected is not None, (fid, frid, crid, read["consequence_selection"])
            assert selected["presented_as_current"] is False, (fid, crid, selected)
            assert selected["source_provenance"]["state"] == "UNKNOWN", (fid, crid, selected["source_provenance"])
            assert currentness["current_amount_shown"] is False, (fid, crid, currentness)
            assert SOURCE_WITHHELD in currentness["withheld_reasons"], (fid, crid, currentness)
            assert _current_amount_paths(answer.json()) == [], (fid, crid)
