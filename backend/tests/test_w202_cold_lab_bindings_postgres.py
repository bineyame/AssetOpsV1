"""W2-02 COLD-LAB-001: historical v3-compatible conversion plus the immutable v4 binding revision.

`D-2026-10-17-w2-02-buildspec` "Registered fixture and frozen identity". Needs `ASSETOPS_TEST_DATABASE_URL`
naming a `*_test` database; skipped (never passed) without it.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from fractions import Fraction

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)"
)

if URL:
    from assetops_contracts.source_envelope_v4 import V4_CHANNEL_MAPPINGS

    from assetops_backend.sites.binding_alignment import V4_BINDING_KEYS
    from assetops_backend.sites.binding_service import BindingRefused, BindingRequest, BindingService
    from assetops_backend.sites.cold_lab import V4_EFFECTIVE_FROM, install_cold_lab
    from test_s1_bindings_postgres import Clock, _alembic, engine, store  # noqa: F401
    from test_w201_cold_foundation_postgres import imported

NOW = datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc)
THIRTEEN = {
    ("room-1", "cold-thermal-capacity"): ("1.2", "kWh/degC"), ("room-1", "cold-heat-leak"): ("0.08", "kW/degC"),
    ("room-1", "cold-door-heat"): ("0.02", "kWh/min"), ("room-1", "cold-control-low"): ("2", "degC"),
    ("room-1", "cold-control-high"): ("4", "degC"), ("room-1", "cold-policy-low"): ("2", "degC"),
    ("room-1", "cold-policy-high"): ("4", "degC"), ("room-1", "cold-min-excursion"): ("15", "min"),
    ("room-1", "cold-return-hysteresis"): ("0.2", "degC"), ("probe-1", "cold-probe-error"): ("0.1", "degC"),
    ("compressor-1", "cold-cooling-capacity"): ("3", "kW"),
    ("compressor-1", "cold-compressor-start-delay"): ("1", "min"),
    ("generator-1", "cold-start-timeout"): ("5", "min"),
}


def _snapshot_bindings(binding_set) -> list[dict]:
    return json.loads(binding_set.snapshot_canonical)["bindings"]


def test_cold_lab_publishes_v4_revision_after_v3_conversion(store) -> None:
    result = install_cold_lab(store, tenant_slug="demo", clock=Clock(NOW - timedelta(hours=3)))
    [revision] = store.revisions(result.tenant.id, result.site.id)
    props = {(c["component_id"], p["property_key"]): (Fraction(str(p["value"])), p["unit"], p["source"],
                                                      p["source_version"])
             for c in revision.content["components"] for p in c.get("properties") or ()}
    assert props == {k: (Fraction(v), u, "SITE", 1) for k, (v, u) in THIRTEEN.items()}
    sets = sorted(store.binding_sets(result.tenant.id, result.site.id), key=lambda s: s.version)
    current = [s for s in sets if s.superseded_at is None]
    first = next(s for s in current if s.valid_to == V4_EFFECTIVE_FROM)
    v4 = next(s for s in current if s.valid_from == V4_EFFECTIVE_FROM)
    assert first.origin in {"CONVERSION", "SPLIT"} and v4.valid_to is None
    assert len(first.bindings) == len(v4.bindings) == 11
    assert ("operator-log", "temperature-event") not in {(b.device_id, b.signal_id) for b in v4.bindings}
    # The historical revision states no v4 key; the v4 revision states exactly the closed tuple's five keys,
    # in the persisted snapshot and in the rows read back.
    assert all(not set(V4_BINDING_KEYS) & set(b) for b in _snapshot_bindings(first))
    assert all(b.v4_mapping is None for b in first.bindings)
    for entry in _snapshot_bindings(v4):
        assert {k: entry[k] for k in V4_BINDING_KEYS} == V4_CHANNEL_MAPPINGS[
            (entry["device_id"], entry["signal_id"])].metadata()
    for row in v4.bindings:
        assert row.v4_mapping == V4_CHANNEL_MAPPINGS[(row.device_id, row.signal_id)].metadata()
    # Idempotent: a second install writes nothing.
    install_cold_lab(store, tenant_slug="demo", clock=Clock(NOW - timedelta(hours=2)))
    assert len(store.binding_sets(result.tenant.id, result.site.id)) == len(sets)


def test_cold_001_conversion_carries_no_v4_keys(store) -> None:
    result = imported(store, "COLD-001")
    [binding_set] = store.binding_sets(result.tenant.id, result.site.id)
    assert all(not set(V4_BINDING_KEYS) & set(b) for b in _snapshot_bindings(binding_set))


def test_mismatched_v4_tuple_refused_before_publication(store) -> None:
    result = install_cold_lab(store, tenant_slug="demo", clock=Clock(NOW - timedelta(hours=3)))
    tenant, site = result.tenant, result.site
    assets = {a.asset_code: str(a.id) for a in store.registrations(tenant.id, site.id).assets}
    before = len(store.binding_sets(tenant.id, site.id))

    def request(device, signal, asset, role, unit):
        return BindingRequest(device_id=device, signal_id=signal, asset_id=assets[asset], role=role,
                              source_unit=unit, canonical_unit=unit,
                              conversion={"kind": "IDENTITY", "parameters": {}})

    service = BindingService(store, Clock(NOW))
    # The chamber probe's tuple carries the chamber role only; binding it as ambient is refused.
    with pytest.raises(BindingRefused) as refused:
        service.publish(tenant, site, requests=[request("chamber-probe", "temperature", "probe-1",
                                                        "ambient_temperature", "degC")],
                        effective_from=datetime(2026, 10, 2, tzinfo=timezone.utc), note="wrong role")
    assert refused.value.code == "BINDING_CHANNEL_ROLE_MISMATCH"
    assert len(store.binding_sets(tenant.id, site.id)) == before
