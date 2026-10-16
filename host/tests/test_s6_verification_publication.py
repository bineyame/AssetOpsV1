"""S6-02a phase 1: the five-minute verification publication survives the public path.

`D-2026-10-16-s6-verification`, `D-2026-10-16-s602-questions` (S6-02a Q2). A
registered KOBO-001 after the labelled S6 verification demo configuration
(`backend/conversions/kobo-001-s6-verification-demo-config.json`, a
`minigrid-roles-3` basis) runs `mini-grid` v4 under `registered-kobo-publication`
v4 through a real gateway process. Every verification power channel - including
the critical load's requested and delivered power, derived from the kernel's
per-load demand and served power - is published as an ordinary device reading
declaring interval semantics: INTERVAL_MEAN over exactly the UTC five-minute
slot ending at its source time. Battery SOC is a STATE_AT_INSTANT sample at
every five-minute boundary. The critical-load channels exist only where a
roles-3 binding maps them; private simulator state fills no public gap.

The PostgreSQL case (skipped without `ASSETOPS_TEST_DATABASE_URL`) uploads the
gateway's own sealed batches into the real S2 batch ingestion and reads the
accepted_evidence rows: the interval declarations survive acceptance.
"""

from __future__ import annotations

import json
import os
import secrets
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend" / "tests"))
sys.path.insert(0, str(ROOT / "gateway" / "tests"))

import test_s2_registered_basis as registered  # noqa: E402
from gateway_process import GatewayProcess, provisioning_from_snapshot, write_config  # noqa: E402
from gateway_publication import RegisteredGatewayPublisher  # noqa: E402
from lab_execution import HostLabExecution, YamlExecutionArtifacts  # noqa: E402
from source_stages import JsonSourceStages  # noqa: E402

from assetops_backend.runs.profiles import (  # noqa: E402
    CRITICAL_LOAD_DELIVERED_SIGNAL,
    CRITICAL_LOAD_REQUESTED_SIGNAL,
    MINI_GRID_V4_MODEL,
    REGISTERED_KOBO_PUBLICATION_PROFILE_V3,
    REGISTERED_KOBO_PUBLICATION_PROFILE_V4,
)
from assetops_backend.sites.binding_service import BindingService, critical_load_code  # noqa: E402
from assetops_backend.sites.demo_configuration import apply_demo_configuration  # noqa: E402
from assetops_contracts.source_envelope_v3 import parse_canonical_envelope_v3_text  # noqa: E402

V4 = REGISTERED_KOBO_PUBLICATION_PROFILE_V4
S3_DEMO = json.loads((ROOT / "backend" / "conversions" / "kobo-001-s3-dispatch-demo-config.json").read_text("utf-8"))
VERIFICATION = json.loads(
    (ROOT / "backend" / "conversions" / "kobo-001-s6-verification-demo-config.json").read_text("utf-8")
)
FIVE = timedelta(minutes=5)
POWER = {
    "generator_power": ("generator-controller", "ac-power"),
    "pv_available_power": ("pv-inverter-controller", "available-power"),
    "pcs_discharge_capability": ("battery-pcs-controller", "discharge-capability"),
    "critical_load_requested_power": CRITICAL_LOAD_REQUESTED_SIGNAL,
    "critical_load_delivered_power": CRITICAL_LOAD_DELIVERED_SIGNAL,
}
FEEDERS = [(m, "active-power") for m in ("residential-meter", "clinic-meter", "mill-meter")]
SOC = ("battery-pcs-controller", "state-of-charge")
STATUS = ("generator-controller", "status")
CRITICAL = {CRITICAL_LOAD_REQUESTED_SIGNAL, CRITICAL_LOAD_DELIVERED_SIGNAL}
START, END = "2026-10-13T03:00:00Z", "2026-10-13T11:00:00Z"
PROLONGED = registered.parse_scenario_document(
    yaml.safe_load((ROOT / "config" / "scenarios" / "kobo-mini-grid-prolonged.yaml").read_text(encoding="utf-8")),
    source="kobo-mini-grid-prolonged", origin="SHIPPED",
)


def _at(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def configure(store, result) -> None:
    clock = registered.Clock(registered.CONVERTED_AT + timedelta(minutes=10))
    foundation, bindings = registered.FoundationService(store, "demo", clock), BindingService(store, clock)
    apply_demo_configuration(store, foundation, bindings, result.tenant, result.site, S3_DEMO)
    applied = apply_demo_configuration(store, foundation, bindings, result.tenant, result.site, VERIFICATION)
    assert applied.periods[-1]["role_set"] == "minigrid-roles-3"


def draft(store, start=START, end=END, publication=V4):
    registry = registered.ImportedSiteRegistry(registered.FoundationService(store, "demo", registered.Clock(registered.NOW)))
    service = registered.RunSetupService(
        registered.FakeRuns(), registered.FakeSites(()), registered.FakeScenarios((PROLONGED,)),
        model_profiles=(MINI_GRID_V4_MODEL,),
        publication_profiles=(REGISTERED_KOBO_PUBLICATION_PROFILE_V3, V4),
        now=lambda: registered.text(registered.NOW),
        registered_bases=registered.RegisteredLabBasis(registry),
    )
    foundation = registered.FoundationService(store, "demo", registered.Clock(registered.NOW))
    tenant = foundation.tenant()
    view = foundation.read(foundation.site(tenant, "KOBO-001"), tenant, _at(start), None)
    body = registered.request(
        foundation_version=view.revision.version, scenario_id=PROLONGED.scenario_id,
        scenario_version=PROLONGED.version.scenario_version,
        interval={"start_time": start, "end_time": end}, timestep_minutes=5,
        model_profile={"profile_id": MINI_GRID_V4_MODEL.model_profile_id,
                       "profile_version": MINI_GRID_V4_MODEL.model_profile_version},
        publication_profile={"profile_id": publication.publication_profile_id,
                             "profile_version": publication.publication_profile_version},
    )
    run = service.create_draft_run(body)
    assert run.execution_status == "READY" and run.blocking_reasons == (), (run.execution_status, run.blocking_reasons)
    return run, view


def _gateway(tmp_path: Path, run, upload: dict | None = None) -> GatewayProcess:
    config = write_config(tmp_path / "gateway", provisioning_from_snapshot(run.registered_basis.snapshot_canonical))
    if upload is not None:
        document = json.loads(config.read_text(encoding="utf-8"))
        config.write_text(json.dumps({**document, "upload": upload}), encoding="utf-8")
    process = GatewayProcess(config)
    assert process.ready, process.first_line
    return process


def _host(root: Path, link) -> HostLabExecution:
    return HostLabExecution(artifacts=YamlExecutionArtifacts(root), stages=JsonSourceStages(root / "stages"),
                            gateway=RegisteredGatewayPublisher(link))


def published(tmp_path: Path, run) -> list:
    process = _gateway(tmp_path, run)
    port = _host(tmp_path / "h", process.link)
    try:
        port.start(run)
        assert port.run_to_end(run).status == "COMPLETED"
        return [parse_canonical_envelope_v3_text(e.envelope_text) for e in port.registered_stage(run).envelopes]
    finally:
        process.kill()


def _boundaries(start=START, end=END) -> list[str]:
    out, t = [], _at(start)
    while t <= _at(end):
        out.append(registered.text(t))
        t += FIVE
    return out


def assert_five_minute_interval(rows, channel, start=START, end=END) -> None:
    """One GOOD INTERVAL_MEAN per UTC five-minute slot ending at its source time."""
    rows = sorted(rows, key=lambda r: r["source_time"])
    good = [r for r in rows if r["quality"] == "GOOD"]
    ends = _boundaries(start, end)[1:]
    assert [r["source_time"] for r in good] == ends, channel
    for r in good:
        assert r["measurement"] == "INTERVAL_MEAN", (channel, r)
        assert r["interval_end"] == r["source_time"], (channel, r)
        lo, hi = _at(r["interval_start"]), _at(r["interval_end"])
        assert hi - lo == FIVE and lo.minute % 5 == 0 and lo.second == 0, (channel, r)
        assert r["value"] is not None


def _row(e) -> dict:
    return {"source_time": e.source_time, "measurement": e.measurement, "interval_start": e.interval_start,
            "interval_end": e.interval_end, "quality": e.quality, "value": e.value}


@pytest.fixture(scope="module")
def configured():
    store, result, _ = registered.converted()
    configure(store, result)
    return store


def test_v4_is_five_minute_and_v1_v3_are_unchanged() -> None:
    assert (V4.publication_profile_id, V4.publication_profile_version) == ("registered-kobo-publication", 4)
    assert (MINI_GRID_V4_MODEL.model_profile_id, MINI_GRID_V4_MODEL.model_profile_version) == ("mini-grid", 4)
    by_key = {d.signal_key: d for d in V4.device_signals}
    for key in [*POWER.values(), *FEEDERS, SOC, STATUS]:
        assert by_key[key].cadence_minutes == 5, key
    assert by_key[SOC].dropout_per_thousand == 0 and by_key[STATUS].dropout_per_thousand == 0
    assert by_key[CRITICAL_LOAD_REQUESTED_SIGNAL].state_key == "load-requested-power"
    assert by_key[CRITICAL_LOAD_DELIVERED_SIGNAL].state_key == "load-served-power"
    v3 = {d.signal_key: d for d in REGISTERED_KOBO_PUBLICATION_PROFILE_V3.device_signals}
    assert not CRITICAL & set(v3) and all(d.cadence_minutes in (15, 60) for d in v3.values())


def test_the_critical_load_is_the_first_critical_load_priority_member(configured) -> None:
    _, view = draft(configured)
    assert critical_load_code(view.revision.content) == "load-clinic"
    assert view.binding_set.role_set == "minigrid-roles-3"
    bound = {(b.device_id, b.signal_id): b.role for b in view.binding_set.bindings}
    assert bound[CRITICAL_LOAD_REQUESTED_SIGNAL] == "critical_load_requested_power"
    assert bound[CRITICAL_LOAD_DELIVERED_SIGNAL] == "critical_load_delivered_power"


def test_roles_3_run_publishes_every_verification_channel_at_five_minutes(configured, tmp_path) -> None:
    run, _ = draft(configured)
    envelopes = published(tmp_path, run)
    by_channel: dict = {}
    for e in envelopes:
        by_channel.setdefault((e.device_id, e.signal_id), []).append(_row(e))
    for role, channel in POWER.items():
        assert_five_minute_interval(by_channel[channel], role)
    for channel in FEEDERS:
        assert_five_minute_interval(by_channel[channel], channel)
    soc = sorted(by_channel[SOC], key=lambda r: r["source_time"])
    assert [r["source_time"] for r in soc] == _boundaries()
    assert all(r["measurement"] == "STATE_AT_INSTANT" and r["quality"] == "GOOD" and r["interval_start"] is None
               for r in soc)
    assert [r["source_time"] for r in sorted(by_channel[STATUS], key=lambda r: r["source_time"])] == _boundaries()
    # Delivered is the clinic's served power: the same value its feeder meter publishes.
    clinic = {r["source_time"]: r["value"] for r in by_channel[("clinic-meter", "active-power")]}
    delivered = {r["source_time"]: r["value"] for r in by_channel[CRITICAL_LOAD_DELIVERED_SIGNAL]}
    assert delivered == clinic
    requested = {r["source_time"]: r["value"] for r in by_channel[CRITICAL_LOAD_REQUESTED_SIGNAL]}
    assert all(float(requested[t]) >= float(delivered[t]) for t in delivered if delivered[t] is not None)


def test_roles_2_basis_publishes_no_critical_load_reading(configured, tmp_path) -> None:
    run, view = draft(configured, "2026-10-03T03:00:00Z", "2026-10-03T11:00:00Z")
    assert view.binding_set.role_set == "minigrid-roles-2"
    channels = {(e.device_id, e.signal_id) for e in published(tmp_path, run)}
    assert not CRITICAL & channels and SOC in channels


# --- through central S2 acceptance (PostgreSQL) -------------------------------------------------

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")


@pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")
def test_interval_declarations_survive_central_acceptance(tmp_path) -> None:
    import test_s1_bindings_postgres as pgb
    from sqlalchemy import create_engine, text

    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.evidence.ledger import GatewayPrincipal
    from assetops_backend.evidence.ledger_service import BatchIngestionService
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore
    from assetops_contracts.ingestion_receipt_v2 import canonical_receipt_v2_text
    from assetops_gateway.credential_protection import restrict_to_current_user
    from fake_central import CERT, FakeCentral
    import pg_harness

    pg_harness.fresh_database()
    engine = create_engine(URL)
    store = PostgresFoundationStore(URL)
    try:
        result, _ = registered_postgres(pgb, store)
        configure(store, result)
        with engine.begin() as connection:  # stand in for credential provisioning (as the S2 ledger tests do)
            connection.execute(text("UPDATE gateway SET disabled_at = NULL WHERE site_id = :s"), {"s": result.site.id})
            connection.execute(text("UPDATE source SET disabled_at = NULL WHERE site_id = :s"), {"s": result.site.id})
        run, _ = draft(store)
        doc = json.loads(run.registered_basis.snapshot_canonical)
        principal = GatewayPrincipal(
            tenant_id=UUID(doc["tenant_id"]), site_id=UUID(doc["site"]["site_id"]),
            gateway_id=UUID(doc["gateway"]["gateway_id"]), mode=doc["gateway"]["mode"],
        )
        received = registered.Clock(datetime(2026, 10, 14, 0, 0, tzinfo=timezone.utc))
        ingestion = BatchIngestionService(PostgresEvidenceLedger(URL, test_decision_clock_override=received), received)

        def respond(path, headers, body):
            answer = ingestion.submit(principal, body)
            return answer.status, canonical_receipt_v2_text(answer.receipt).encode("utf-8")

        token = f"aog1.{secrets.token_hex(16)}.{secrets.token_urlsafe(32)}"
        (tmp_path / "gateway").mkdir(parents=True)
        (tmp_path / "gateway" / "upload.credential").write_text(token, encoding="ascii")
        restrict_to_current_user(tmp_path / "gateway" / "upload.credential")
        central = FakeCentral(respond)
        process = _gateway(tmp_path, run, {"server_url": central.url, "upload_credential_file": "upload.credential",
                                           "ca_file": str(CERT), "interval_seconds": 3600})
        try:
            port = _host(tmp_path / "h", process.link)
            port.start(run)
            assert port.run_to_end(run).status == "COMPLETED"
            port.release_registered(run)
            publisher = RegisteredGatewayPublisher(process.link)
            while publisher.deliver(50)["batches"]["attempted"]:
                pass
        finally:
            process.kill()
            central.close()
        with engine.connect() as connection:
            rows = [dict(r._mapping) for r in connection.execute(text(
                "SELECT role, device_id, signal_id, measurement, source_time, interval_start, interval_end, quality, "
                "normalized_value_text AS value FROM accepted_evidence WHERE site_id = :s"), {"s": result.site.id})]
        assert rows, "nothing was accepted"
        z = registered.text
        by_role: dict = {}
        for r in rows:
            by_role.setdefault((r["role"], r["device_id"]), []).append({
                **r, "source_time": z(r["source_time"]),
                "interval_start": None if r["interval_start"] is None else z(r["interval_start"]),
                "interval_end": None if r["interval_end"] is None else z(r["interval_end"]),
            })
        for role, (device, _) in POWER.items():
            assert_five_minute_interval(by_role[(role, device)], role)
        for device, _ in FEEDERS:
            assert_five_minute_interval(by_role[("feeder_demand", device)], device)
        soc = sorted(by_role[("battery_soc", SOC[0])], key=lambda r: r["source_time"])
        assert [r["source_time"] for r in soc] == _boundaries()
        assert all(r["measurement"] == "STATE_AT_INSTANT" for r in soc)
    finally:
        pg_harness.dispose(store)
        engine.dispose()


def registered_postgres(pgb, store):
    """KOBO-001 imported and converted in PostgreSQL, as the S1 binding tests do."""
    return pgb.converted(store)
