"""W2-05a EV-LAB-001: Foundation import, the complete `ev-roles-1` v4 binding revision, the EV Draft gate and
same-Site gap revisions, persisted and reloaded.

`D-2026-10-18-w2-05-buildspec` Q1/Q2/Q6/Q8. Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database;
skipped (never passed) without it.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)"
)

if URL:
    from assetops_contracts.source_envelope_v4 import V4_EV_CHANNEL_MAPPINGS

    from assetops_backend.sites.binding_service import (
        BindingRefused,
        BindingRequest,
        BindingService,
        Snapshot,
        SnapshotUnavailable,
        acquisition_snapshot,
    )
    from assetops_backend.sites.ev_lab import binding_fixture, install_ev_lab
    from assetops_backend.sites.foundation_service import FoundationService
    from test_s1_bindings_postgres import Clock, _alembic, engine, store  # noqa: F401

NOW = datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc)
ORIGINAL_FROM = datetime(2026, 10, 1, tzinfo=timezone.utc)
#: Q6: gap revisions start after the 6 October complete-run window.
MISSING_METER_FROM = datetime(2026, 10, 8, tzinfo=timezone.utc)
MISSING_LIMIT_FROM = datetime(2026, 10, 12, tzinfo=timezone.utc)


def install(store):
    return install_ev_lab(store, tenant_slug="demo", clock=Clock(NOW - timedelta(hours=3)))


def selected(store, result, at: datetime):
    sets = [s for s in store.binding_sets(result.tenant.id, result.site.id) if s.superseded_at is None
            and s.valid_from <= at and (s.valid_to is None or at < s.valid_to)]
    assert len(sets) == 1, sets
    return sets[0]


def snapshot_at(store, result, at: datetime):
    return acquisition_snapshot(
        result.tenant.id, result.site, store.revisions(result.tenant.id, result.site.id),
        store.registrations(result.tenant.id, result.site.id), selected(store, result, at),
    )


def complete_requests(store, result) -> list[BindingRequest]:
    asset_ids = {a.asset_code: str(a.id) for a in store.registrations(result.tenant.id, result.site.id).assets}
    return [BindingRequest(device_id=b["device_id"], signal_id=b["signal_id"], asset_id=asset_ids[b["asset_code"]],
                           role=b["role"], source_unit=b["source_unit"], canonical_unit=b["canonical_unit"],
                           conversion=b["conversion"]) for b in binding_fixture()["bindings"]]


def test_install_persists_the_complete_basis_and_reloads(store) -> None:
    result = install(store)
    [revision] = store.revisions(result.tenant.id, result.site.id)
    assert (revision.valid_from, revision.valid_to) == (ORIGINAL_FROM, None)
    assert revision.content["connector_enable_schedules"][0]["time_zone"] == "Etc/UTC"
    [binding_set] = store.binding_sets(result.tenant.id, result.site.id)
    assert (binding_set.role_set, binding_set.origin, binding_set.valid_from) == ("ev-roles-1", "PUBLISH",
                                                                                  ORIGINAL_FROM)
    assert binding_set.foundation_revision_id == revision.id
    assert len(binding_set.bindings) == 15
    codes = {a.id: a.asset_code for a in store.registrations(result.tenant.id, result.site.id).assets}
    for b in binding_set.bindings:
        entry = V4_EV_CHANNEL_MAPPINGS[(b.device_id, b.signal_id)]
        assert b.role == entry.role
        assert b.v4_mapping == entry.metadata()
        assert codes[b.asset_id] == ("site-meter-1" if b.device_id == "site-meter" else b.device_id[:2])
    snapshot = snapshot_at(store, result, datetime(2026, 10, 6, 12, tzinfo=timezone.utc))
    assert isinstance(snapshot, Snapshot), snapshot
    pinned = {(r["device_id"], r["signal_id"]): r for r in json.loads(snapshot.body)["bindings"]}
    assert set(pinned) == set(V4_EV_CHANNEL_MAPPINGS)
    # Idempotent: a second install neither re-imports nor republishes.
    install_ev_lab(store, tenant_slug="demo", clock=Clock(NOW - timedelta(hours=2)))
    assert len(store.binding_sets(result.tenant.id, result.site.id)) == 1


def test_missing_meter_revision_blocks_draft_and_keeps_the_original(store) -> None:
    result = install(store)
    requests = [r for r in complete_requests(store, result)
                if (r.device_id, r.signal_id) != ("c2-connector-meter", "energy")]
    BindingService(store, Clock(NOW - timedelta(hours=1))).publish(
        result.tenant, result.site, requests=requests, effective_from=MISSING_METER_FROM,
        note="W2-05a test: connector 2 energy meter not bound.", role_set="ev-roles-1")
    gap = snapshot_at(store, result, MISSING_METER_FROM + timedelta(hours=1))
    assert isinstance(gap, SnapshotUnavailable) and "METER_NOT_BOUND" in gap.reason, gap
    assert isinstance(snapshot_at(store, result, datetime(2026, 10, 6, 12, tzinfo=timezone.utc)), Snapshot)


@pytest.mark.parametrize("drop,code", [(("c1-charger-controller", "session-event"), "SESSION_EVENTS_NOT_BOUND"),
                                       (("c1-connector-controller", "state"), "STATUS_NOT_BOUND")])
def test_missing_event_or_status_revision_blocks_draft(store, drop, code) -> None:
    result = install(store)
    requests = [r for r in complete_requests(store, result) if (r.device_id, r.signal_id) != drop]
    BindingService(store, Clock(NOW - timedelta(hours=1))).publish(
        result.tenant, result.site, requests=requests, effective_from=MISSING_METER_FROM,
        note=f"W2-05a test: {code}.", role_set="ev-roles-1")
    gap = snapshot_at(store, result, MISSING_METER_FROM + timedelta(hours=1))
    assert isinstance(gap, SnapshotUnavailable) and code in gap.reason, gap


def test_optional_role_absence_does_not_block(store) -> None:
    result = install(store)
    optional = {("site-meter", "import"), ("c1-connector-controller", "fault-event"),
                ("c1-connector-meter", "power"), ("c1-connector-controller", "requested-power"),
                ("c1-connector-controller", "allocated-limit")}
    requests = [r for r in complete_requests(store, result) if (r.device_id, r.signal_id) not in optional]
    BindingService(store, Clock(NOW - timedelta(hours=1))).publish(
        result.tenant, result.site, requests=requests, effective_from=MISSING_METER_FROM,
        note="W2-05a test: optional channels absent.", role_set="ev-roles-1")
    assert isinstance(snapshot_at(store, result, MISSING_METER_FROM + timedelta(hours=1)), Snapshot)


def test_missing_limit_foundation_revision_blocks_draft(store) -> None:
    result = install(store)

    def without_limit(content, _version):
        changed = json.loads(json.dumps(content))
        feed = next(c for c in changed["components"] if c["component_type"] == "AC_BUS")
        feed.pop("properties")
        return changed

    FoundationService(store, "demo", Clock(NOW - timedelta(hours=1)))._publish_content_change(
        result.tenant, result.site, effective_from=MISSING_LIMIT_FROM,
        note="W2-05a test: site import limit not declared.", unchanged=lambda _c: None, change=without_limit)
    revisions = store.revisions(result.tenant.id, result.site.id)
    assert any(r.valid_from == MISSING_LIMIT_FROM for r in revisions)
    gap = snapshot_at(store, result, MISSING_LIMIT_FROM + timedelta(hours=1))
    assert isinstance(gap, SnapshotUnavailable) and "FEED_OR_LIMIT_MISSING" in gap.reason, gap
    assert isinstance(snapshot_at(store, result, datetime(2026, 10, 6, 12, tzinfo=timezone.utc)), Snapshot)


@pytest.mark.parametrize("change,code", [
    (lambda r: BindingRequest(**{**r.__dict__, "role": "ev_connector_power"}), "BINDING_CHANNEL_ROLE_MISMATCH"),
    (lambda r: BindingRequest(**{**r.__dict__, "conversion": {"kind": "IDENTITY", "parameters": {}}}),
     "BINDING_CONVERSION_INVALID"),
])
def test_energy_channel_refusals(store, change, code) -> None:
    result = install(store)
    requests = [change(r) if (r.device_id, r.signal_id) == ("c1-connector-meter", "energy") else r
                for r in complete_requests(store, result)]
    with pytest.raises(BindingRefused) as caught:
        BindingService(store, Clock(NOW - timedelta(hours=1))).publish(
            result.tenant, result.site, requests=requests, effective_from=MISSING_METER_FROM, note="refused",
            role_set="ev-roles-1")
    assert code in {p["code"] for p in caught.value.problems}
