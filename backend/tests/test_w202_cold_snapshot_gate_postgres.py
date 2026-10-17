"""W2-02 fix round: the production COLDCHAIN acquisition-snapshot readiness gate (build spec q6).

The registered COLD-LAB-001 basis is installed through the real store; each ruled refusal is produced by
editing the selected revision or binding set read back from it and calling the production
`acquisition_snapshot` (and, for the pass case, the production `RegisteredLabBasis` path's snapshot step).
"""

from __future__ import annotations

import copy
import os
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)"
)

if URL:
    from assetops_backend.sites import binding_service
    from assetops_backend.sites.binding_service import Snapshot, SnapshotUnavailable, acquisition_snapshot
    from assetops_backend.sites.cold_lab import V4_EFFECTIVE_FROM, install_cold_lab
    from test_s1_bindings_postgres import Clock, _alembic, engine, store  # noqa: F401

NOW = datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc)


@pytest.fixture()
def basis(store):
    result = install_cold_lab(store, tenant_slug="demo", clock=Clock(NOW - timedelta(hours=3)))
    revisions = store.revisions(result.tenant.id, result.site.id)
    registrations = store.registrations(result.tenant.id, result.site.id)
    v4 = next(s for s in store.binding_sets(result.tenant.id, result.site.id)
              if s.superseded_at is None and s.valid_from == V4_EFFECTIVE_FROM)
    return result, revisions, registrations, v4


def snapshot(basis, *, revision_edit=None, binding_set=None):
    result, revisions, registrations, v4 = basis
    binding_set = binding_set or v4
    if revision_edit is not None:
        revisions = [replace(r, content=revision_edit(copy.deepcopy(r.content)))
                     if r.id == binding_set.foundation_revision_id else r for r in revisions]
    return acquisition_snapshot(result.tenant.id, result.site, revisions, registrations, binding_set, now=NOW)


def without_roles(v4, *roles):
    kept = tuple(b for b in v4.bindings if b.role not in roles)
    assert len(kept) < len(v4.bindings), roles  # the fixture binds the role being removed
    return replace(v4, bindings=kept)


def refused_codes(outcome) -> str:
    assert isinstance(outcome, SnapshotUnavailable), outcome
    assert (outcome.code, outcome.status) == ("ACQUISITION_SNAPSHOT_UNAVAILABLE", 409)
    return outcome.reason


def test_registered_cold_basis_is_served_without_the_minigrid_rule(basis, monkeypatch) -> None:
    def never(*_args, **_kwargs):
        raise AssertionError("the MINIGRID configuration_gaps rule was applied to a COLDCHAIN Site")

    monkeypatch.setattr(binding_service, "configuration_gaps", never)
    outcome = snapshot(basis)
    assert isinstance(outcome, Snapshot), outcome
    assert outcome.binding_set.id == basis[3].id and outcome.current_gaps == ()


def test_room_missing_refuses(basis) -> None:
    def drop_room(content):
        content["components"] = [c for c in content["components"] if c.get("component_type") != "COLD_ROOM"]
        return content

    assert "ROOM_MISSING" in refused_codes(snapshot(basis, revision_edit=drop_room))


def test_probe_binding_missing_refuses(basis) -> None:
    reason = refused_codes(snapshot(basis, binding_set=without_roles(basis[3], "chamber_temperature")))
    assert "PROBE_MISSING" in reason


def test_policy_missing_refuses(basis) -> None:
    def drop_policy_high(content):
        for component in content["components"]:
            if component.get("component_type") == "COLD_ROOM":
                component["properties"] = [p for p in component["properties"]
                                           if p["property_key"] != "cold-policy-high"]
        return content

    assert "POLICY_MISSING" in refused_codes(snapshot(basis, revision_edit=drop_policy_high))


def test_start_event_missing_refuses(basis) -> None:
    reason = refused_codes(snapshot(basis, binding_set=without_roles(basis[3], "backup_start_event")))
    assert "START_EVENT_MISSING" in reason


@pytest.mark.parametrize("role", ["grid_power_event", "generator_state", "backup_bus_state"])
def test_required_role_unbound_refuses(basis, role) -> None:
    assert "ROLE_UNBOUND" in refused_codes(snapshot(basis, binding_set=without_roles(basis[3], role)))


@pytest.mark.parametrize("roles", [("transfer_result",), ("ambient_temperature",), ("compressor_power",)])
def test_nonblocking_messages_do_not_gate(basis, roles) -> None:
    result, revisions, registrations, v4 = basis
    edited = without_roles(v4, *roles)
    foundation = next(r for r in revisions if r.id == v4.foundation_revision_id)
    assert binding_service.cold_snapshot_gaps(foundation, registrations, edited) == []
    # Past the readiness gate the stored snapshot's pinned rows still refuse an edited set, as they must.
    outcome = snapshot(basis, binding_set=edited)
    assert isinstance(outcome, SnapshotUnavailable) and outcome.code == "ACQUISITION_SNAPSHOT_INCONSISTENT"


def test_unknown_role_set_refuses(basis) -> None:
    reason = refused_codes(snapshot(basis, binding_set=replace(basis[3], role_set="cold-roles-0")))
    assert "BINDING_ROLE_SET_UNKNOWN" in reason


def test_unevaluable_revision_is_unavailable_not_ready(basis) -> None:
    def break_components(content):
        content["components"] = [{"component_type": "COLD_ROOM"}]
        return content

    assert "COLD_FOUNDATION_UNEVALUABLE" in refused_codes(snapshot(basis, revision_edit=break_components))


def test_mismatched_foundation_revision_refuses(basis) -> None:
    from uuid import uuid4

    outcome = snapshot(basis, binding_set=replace(basis[3], foundation_revision_id=uuid4()))
    assert isinstance(outcome, SnapshotUnavailable) and outcome.code == "ACQUISITION_SNAPSHOT_INCONSISTENT"
