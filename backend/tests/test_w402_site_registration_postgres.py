"""W4-02 closure 5: MG-W402-001 is a registered MINIGRID Site with its own `minigrid-roles-4` binding publication.

Proves the isolated demonstration Site is actually installed before the authored Batch V2 replay (registry
membership alone does not create a Site), that an identical rerun publishes nothing, and that the KOBO-001 S6
verification demo configuration cannot touch it. q1 ruling 1: the publish path pins v4 metadata on exactly the three
authored tuples, and an authored v4 envelope is accepted or refused against that pinned snapshot.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import NOW, Clock, converted, engine, store  # noqa: F401

    from assetops_backend.evidence.adapters.authored_fixture_specs import AuthoredFixtureSpecs
    from assetops_backend.sites.binding_service import BindingService
    from assetops_backend.sites.demo_configuration import apply_demo_configuration
    from assetops_backend.sites.foundation_service import FoundationService
    from assetops_backend.sites.w402_demo import MG_W402_SITE_CODE, install_mg_w402_site
    from assetops_contracts.source_envelope_v4 import V4_MINI_CHANNEL_MAPPINGS
    from test_s2_evidence_ledger_postgres import enable
    from assetops_contracts.source_envelope import canonical_json
    from test_w402_authored_v4_postgres import cases, ingestion, principal

CONVERSIONS = Path(__file__).resolve().parents[1] / "conversions"
INSTALLED = datetime(2026, 10, 2, 8, 0, tzinfo=timezone.utc)
V4_ROLES = {"site_supply_state", "mini_backup_start_event", "mini_backup_bus_state"}


def install(store):
    return install_mg_w402_site(store, tenant_slug="demo", clock=Clock(INSTALLED))


def snapshot(engine, revision_id) -> dict:
    with engine.connect() as c:
        return json.loads(bytes(c.execute(text(
            "SELECT snapshot_canonical FROM signal_binding_set_revision WHERE id = :id"), {"id": revision_id}
        ).scalar_one()))


def test_mg_w402_import_binding_and_kobo_rerun_isolation(store, engine) -> None:
    first = install(store)
    assert first.published
    tenant, site = first.result.tenant, first.result.site

    # Reload by (tenant, site code): the registered MINIGRID Site in Nairobi with its own gateway and sources.
    reloaded = store.find_site(tenant.id, MG_W402_SITE_CODE)
    assert reloaded is not None and reloaded.id == site.id
    assert (reloaded.site_type, reloaded.timezone) == ("MINIGRID", "Africa/Nairobi")
    regs = store.registrations(tenant.id, site.id)
    assert len(regs.gateways) == 1 and regs.gateways[0].mode == "SIMULATED"
    assert {s.gateway_id for s in regs.sources} == {regs.gateways[0].id}
    assert {"mini-primary-bus-meter", "mini-generator-controller", "mini-backup-bus-meter"} <= {
        s.source_external_id for s in regs.sources}
    sets = store.binding_sets(tenant.id, site.id)
    assert len(sets) == 1 and sets[0].role_set == "minigrid-roles-4" and sets[0].id == first.binding_set.id

    # q1 ruling 1: v4 metadata on exactly the three authored tuples, each its table row's metadata; no other row.
    doc = snapshot(engine, first.binding_set.id)
    pinned = {(b["device_id"], b["signal_id"]): b for b in doc["bindings"] if b.get("allowed_record_kinds") is not None}
    assert set(pinned) == set(V4_MINI_CHANNEL_MAPPINGS)
    for key, row in pinned.items():
        entry = V4_MINI_CHANNEL_MAPPINGS[key]
        assert row["role"] == entry.role
        assert {k: row[k] for k in entry.metadata()} == entry.metadata()
    v3 = [b for b in doc["bindings"] if (b["device_id"], b["signal_id"]) not in pinned]
    assert {"generator_power", "feeder_demand"} <= {b["role"] for b in v3}
    assert not V4_ROLES & {b["role"] for b in v3}

    # An identical rerun returns the same Site, Foundation and binding revision and publishes nothing.
    again = install(store)
    assert not again.published
    assert (again.result.site.id, again.result.revision.id, again.binding_set.id) == (
        site.id, first.result.revision.id, first.binding_set.id)
    assert len(store.binding_sets(tenant.id, site.id)) == 1

    # The KOBO-001 S3 then S6 demo configuration path, on an independently imported KOBO-001, leaves MG-W402-001's
    # binding ID, role set and snapshot digest unchanged.
    kobo, _ = converted(store)
    clock = Clock(NOW + timedelta(minutes=10))
    for name in ("kobo-001-s3-dispatch-demo-config.json", "kobo-001-s6-verification-demo-config.json"):
        apply_demo_configuration(store, FoundationService(store, "demo", clock), BindingService(store, clock),
                                 kobo.tenant, kobo.site, json.loads((CONVERSIONS / name).read_text(encoding="utf-8")))
    after = store.binding_sets(tenant.id, site.id)
    assert [(s.id, s.role_set, s.snapshot_sha256) for s in after] == [
        (sets[0].id, "minigrid-roles-4", sets[0].snapshot_sha256)]

    # The authored fixture registry declares the spec's schema ID/version and refuses an unregistered fixture.
    specs = AuthoredFixtureSpecs()
    assert specs.declared("assetops.w4-mini-depth-cases") == ("assetops.w4-mini-depth-cases", "1")
    assert specs.declared("assetops.w4-not-registered") is None

    # q1 ruling 1: against the pinned snapshot, an authored v4 STATE envelope on its tuple is ACCEPTED and the same
    # v4 envelope on a v3-only channel (no pinned metadata) is refused.
    enable(engine, site.id)
    with engine.connect() as c:
        sha = __import__("hashlib").sha256(bytes(c.execute(text(
            "SELECT snapshot_canonical FROM signal_binding_set_revision WHERE id = :id"),
            {"id": first.binding_set.id}).scalar_one())).hexdigest()
    outcomes = []
    for device, signal in (("mini-primary-bus-meter", "state"), ("generator-controller", "ac-power")):
        b = next(r for r in doc["bindings"] if (r["device_id"], r["signal_id"]) == (device, signal))
        planned = cases.Planned(device, signal, datetime(2026, 10, 6, 9, 0, tzinfo=timezone.utc), "STATE",
                                "ENERGIZED", "state")
        envelope = cases._envelope(doc, b, "w402-registration", 1, planned)
        if device == "generator-controller":  # the same v4 STATE document on the v3-only channel
            forced = json.loads(envelope)
            forced["schema"]["version"] = 4
            forced["payload"].update(session_id=None, connector_id=None)
            envelope = canonical_json(forced)
        receipt = ingestion().submit(principal(doc), cases.seal_for(doc, sha, b, [envelope]).encode("utf-8"))
        (d,) = receipt.receipt.dispositions
        outcomes.append((d.decision, None if d.rejection is None else d.rejection.kind))
    assert outcomes == [("ACCEPTED", None), ("REJECTED", "MAPPING_INCOMPATIBLE")]
