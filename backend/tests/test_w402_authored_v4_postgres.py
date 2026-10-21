"""W4-02 closure 4 B2 and q1 ruling 1: the authored `authored-mini-depth-cases/1` v4 table, the mixed v3/v4
`minigrid-roles-4` binding check, and the authored MG-W402-001 batches through the ledger (N4: accepted IDs and
binding/profile identity only; selection seqs are unit 4's).
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

TOOLS = Path(__file__).resolve().parents[2] / "tools"

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import Clock, engine, store  # noqa: F401
    from test_s2_evidence_ledger_postgres import enable

    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.evidence.ledger import GatewayPrincipal
    from assetops_backend.evidence.ledger_service import BatchIngestionService
    from assetops_backend.sites.binding_conversion import plan_requests
    from assetops_backend.sites.binding_roles import COLD_ROLES_1
    from assetops_backend.sites.binding_service import BindingRefused, BindingService, v4_mapping_profile
    from assetops_backend.sites.w402_demo import binding_fixture, install_mg_w402_site
    from assetops_contracts.source_envelope import canonical_json
    from assetops_contracts.source_envelope_v4 import (
        V4_CHANNEL_MAPPINGS,
        V4_CHANNEL_MAPPINGS_BY_PROFILE,
        V4_COLD_CHANNEL_MAPPINGS,
        V4_MINI_CHANNEL_MAPPINGS,
    )

    sys.path.insert(0, str(TOOLS))
    import w402_mini_depth_cases as cases  # noqa: E402

INSTALLED = datetime(2026, 10, 2, 8, 0, tzinfo=timezone.utc)
RECEIVED = datetime(2026, 10, 13, 8, 0, tzinfo=timezone.utc)
EXPECTED_ROWS = {
    ("mini-primary-bus-meter", "state"): ("MEASUREMENT", "STATE_AT_INSTANT", (), False, ("state",),
                                          "site_supply_state"),
    ("mini-generator-controller", "start-event"): ("EVENT", None, ("START_REQUEST", "START_RESULT"), True, (),
                                                   "mini_backup_start_event"),
    ("mini-backup-bus-meter", "state"): ("MEASUREMENT", "STATE_AT_INSTANT", (), False, ("state",),
                                         "mini_backup_bus_state"),
}


def install(store):
    return install_mg_w402_site(store, tenant_slug="demo", clock=Clock(INSTALLED))


def snapshot(engine, revision_id) -> tuple[dict, str]:
    with engine.connect() as c:
        body = bytes(c.execute(text("SELECT snapshot_canonical FROM signal_binding_set_revision WHERE id = :id"),
                               {"id": revision_id}).scalar_one())
    return json.loads(body), __import__("hashlib").sha256(body).hexdigest()


def principal(doc) -> GatewayPrincipal:
    return GatewayPrincipal(tenant_id=UUID(doc["tenant_id"]), site_id=UUID(doc["site"]["site_id"]),
                            gateway_id=UUID(doc["gateway"]["gateway_id"]), mode=doc["gateway"]["mode"])


def ingestion() -> BatchIngestionService:
    return BatchIngestionService(PostgresEvidenceLedger(URL, test_decision_clock_override=Clock(RECEIVED)),
                                 Clock(RECEIVED))


def rows(engine, sql, **params):
    with engine.connect() as c:
        return c.execute(text(sql), params).mappings().all()


def test_w402_v4_mapping_exact_rows_and_metadata(store, engine) -> None:
    # Exactly these three authored rows, as their own profile table, also present in the global union.
    got = {k: (e.family, e.measurement, e.allowed_record_kinds, e.requires_correlation, e.allowed_units, e.role)
           for k, e in V4_MINI_CHANNEL_MAPPINGS.items()}
    assert got == EXPECTED_ROWS
    assert all(not e.requires_session for e in V4_MINI_CHANNEL_MAPPINGS.values())
    assert V4_MINI_CHANNEL_MAPPINGS[("mini-generator-controller", "start-event")].metadata()["allowed_outcomes"] == {
        "START_REQUEST": ["REQUESTED"], "START_RESULT": ["FAILED", "SUCCEEDED"]}
    assert V4_CHANNEL_MAPPINGS_BY_PROFILE[("authored-mini-depth-cases", 1)] is V4_MINI_CHANNEL_MAPPINGS
    assert all(V4_CHANNEL_MAPPINGS[k] == v for k, v in V4_MINI_CHANNEL_MAPPINGS.items())
    assert v4_mapping_profile("minigrid-roles-4") == ("authored-mini-depth-cases", 1)
    # Cold is byte-for-byte unchanged: its own names and POWERED|UNPOWERED bus enum, twelve rows.
    cold = {r.role: r for r in COLD_ROLES_1}
    assert "backup_start_event" in cold and cold["backup_bus_state"].states == ("POWERED", "UNPOWERED")
    assert len(V4_COLD_CHANNEL_MAPPINGS) == 12
    assert V4_COLD_CHANNEL_MAPPINGS[("backup-bus-meter", "state")].role == "backup_bus_state"
    assert V4_COLD_CHANNEL_MAPPINGS[("generator-controller", "start-event")].role == "backup_start_event"

    # The published snapshot pins exactly the table's five-key metadata on exactly those rows.
    doc, _ = snapshot(engine, install(store).binding_set.id)
    pinned = {(b["device_id"], b["signal_id"]): {k: b[k] for k in V4_MINI_CHANNEL_MAPPINGS[
        ("mini-primary-bus-meter", "state")].metadata()} for b in doc["bindings"] if b.get("allowed_units") is not None}
    assert pinned == {k: e.metadata() for k, e in V4_MINI_CHANNEL_MAPPINGS.items()}


def test_w402_mixed_v3_v4_binding_publish_refusals(store, engine) -> None:
    """q1 ruling 1: a missing, wrong-role or substituted v4 tuple is refused; an authored v4 tuple cannot be bound
    as a v3 role. Each refusal writes nothing."""
    installed = install(store)
    tenant, site = installed.result.tenant, installed.result.site
    asset_ids = {a.asset_code: str(a.id) for a in store.registrations(tenant.id, site.id).assets}
    base, declared, _ = plan_requests(binding_fixture(), site, (), asset_ids)
    service = BindingService(store, Clock(INSTALLED + timedelta(days=1)))
    at = INSTALLED + timedelta(hours=12)

    def refused(requests) -> set[str]:
        with pytest.raises(BindingRefused) as caught:
            service.publish(tenant, site, requests=requests, declare=declared, effective_from=at, note="probe",
                            role_set="minigrid-roles-4")
        return {p["code"] for p in caught.value.problems}

    def swap(role: str, **change):
        return [replace(r, **change) if r.role == role else r for r in base]

    # Missing tuple: the supply state bound to a declared channel that is not its authored tuple.
    assert "BINDING_CHANNEL_V4_UNKNOWN" in refused(swap("site_supply_state", device_id="generator-controller",
                                                        signal_id="status"))
    # Substituted/wrong-role tuple: two v4 roles exchange their authored channels.
    exchanged = [replace(r, device_id="mini-backup-bus-meter") if r.role == "site_supply_state"
                 else replace(r, device_id="mini-primary-bus-meter") if r.role == "mini_backup_bus_state" else r
                 for r in base]
    assert "BINDING_CHANNEL_ROLE_MISMATCH" in refused(exchanged)
    # Cross-role: an authored v4 tuple bound as a v3 role (and the v4 role left without it).
    v3_on_v4 = [r for r in base if r.role != "mini_backup_bus_state"]
    v3_on_v4 = [replace(r, device_id="mini-backup-bus-meter", signal_id="state") if r.role == "generator_state"
                else r for r in v3_on_v4]
    assert "BINDING_CHANNEL_ROLE_MISMATCH" in refused(v3_on_v4)
    # Nothing was written by any refusal.
    assert [s.id for s in store.binding_sets(tenant.id, site.id)] == [installed.binding_set.id]


def test_w402_authored_backup_batch_accepted(store, engine) -> None:
    installed = install(store)
    site_id = installed.result.site.id
    enable(engine, site_id)
    doc, sha = snapshot(engine, installed.binding_set.id)
    spec = cases.load_spec()
    service = ingestion()

    accepted: dict[str, list[str]] = {}
    for variant in ("positive", "missing-conflicting"):
        batches = cases.build_batches(spec, doc, sha, variant)
        for b in batches:
            service.submit(principal(doc), b.body.encode("utf-8"))
        with engine.connect() as c:
            accepted[variant] = cases.accepted_ids(c, doc["site"]["site_id"], cases.message_ids(batches))
        assert len(accepted[variant]) == sum(b.count for b in batches), variant  # every authored row ACCEPTED

    # The correlated chain: accepted v4 EVENT rows under one correlation, and the STATE rows of both buses.
    events = rows(engine, "SELECT record_kind, outcome, correlation_id FROM accepted_evidence WHERE site_id = :s "
                  "AND role = 'mini_backup_start_event' ORDER BY source_time, record_kind", s=site_id)
    positive = [e for e in events if e["correlation_id"] == "w402-backup-1"]
    assert [(e["record_kind"], e["outcome"]) for e in positive] == [("START_REQUEST", "REQUESTED"),
                                                                    ("START_RESULT", "SUCCEEDED")]
    states = rows(engine, "SELECT role, count(*) AS n FROM accepted_evidence WHERE site_id = :s "
                  "AND role IN ('site_supply_state', 'mini_backup_bus_state') GROUP BY role", s=site_id)
    assert {r["role"]: r["n"] for r in states} == {"site_supply_state": 5, "mini_backup_bus_state": 1}
    # Mini work only: the backup hour is queued, no cold_chain job exists.
    jobs = rows(engine, "SELECT domain, count(*) AS n FROM recompute_job WHERE site_id = :s GROUP BY domain",
                s=site_id)
    by = {j["domain"]: j["n"] for j in jobs}
    assert by.get("cold_chain", 0) == 0 and by.get("mini_backup", 0) >= 1 and by.get("mini_renewable", 0) >= 5

    # Incompatible channels are refused against the pinned snapshot: a v4 EVENT on a STATE tuple, and a v4
    # envelope on a v3-only channel (no pinned metadata, no global entry).
    gen = next(b for b in doc["bindings"] if b["device_id"] == "generator-controller" and b["signal_id"] == "ac-power")
    bus = next(b for b in doc["bindings"] if b["device_id"] == "mini-primary-bus-meter")

    def v4_event(b, signal):
        return canonical_json({
            "schema": {"id": "assetops.source-envelope", "version": 4},
            "message": {"message_id": cases.v3_message_id_for(doc, b, "w402-refused", 1),
                        "sequence_epoch": "w402-refused", "sequence": 1},
            "source": {"site_id": doc["site"]["site_id"], "gateway_id": b["gateway_id"], "source_id": b["source_id"],
                       "device_id": b["device_id"], "signal_id": signal},
            "mapping": {"binding_set_id": doc["mapping"]["binding_set_id"], "version": doc["mapping"]["version"]},
            "timing": {"source_time": "2026-10-12T09:30:00Z", "published_at": "2026-10-12T09:30:00Z",
                       "interval_start": None, "interval_end": None},
            "payload": {"family": "EVENT", "record_kind": "START_REQUEST", "event_id": "w402-refused-1",
                        "correlation_id": "w402-refused", "component_id": "generator", "actor": "CONTROLLER",
                        "outcome": "REQUESTED", "unit": None, "value": None, "quality": "GOOD", "session_id": None,
                        "connector_id": None}})

    for b, signal in ((bus, "state"), (gen, "ac-power")):
        body = cases.seal_for(doc, sha, b, [v4_event(b, signal)])
        receipt = service.submit(principal(doc), body.encode("utf-8"))
        (d,) = receipt.receipt.dispositions
        assert d.decision == "REJECTED" and d.rejection.kind == "MAPPING_INCOMPATIBLE", (signal, d)
