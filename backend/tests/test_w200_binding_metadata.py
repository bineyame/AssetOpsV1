"""W2-00 ruling 4: optional v4 snapshot binding keys in the serializer and S2's BindingBasis reader (pure)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from uuid import uuid4

from assetops_backend.evidence.ledger import StoredBindingSet, basis_from_snapshot, decide
from assetops_backend.sites.binding_alignment import V4_BINDING_KEYS, binding_content
from assetops_backend.sites.foundation_records import BindingRow
from assetops_contracts.source_envelope_v4 import V4_CHANNEL_MAPPINGS

ROW = BindingRow(id=uuid4(), gateway_id=uuid4(), source_id=uuid4(), device_id="door-sensor", signal_id="event",
                 asset_id=None, role="door", source_unit="none", canonical_unit="none",
                 conversion={"kind": "IDENTITY", "parameters": {}})
META = V4_CHANNEL_MAPPINGS[("door-sensor", "event")].metadata()


def test_binding_content_serializes_v4_keys_only_when_supplied() -> None:
    v3 = binding_content(ROW)
    assert not set(V4_BINDING_KEYS) & set(v3)
    v4 = binding_content(replace(ROW, v4_mapping=META))
    assert {k: v4[k] for k in V4_BINDING_KEYS} == META
    assert {k: v for k, v in v4.items() if k not in V4_BINDING_KEYS} == v3


def _stored(rows: list[dict]) -> tuple[StoredBindingSet, dict]:
    foundation_id, set_id = uuid4(), uuid4()
    doc = {
        "schema": "assetops.acquisition-snapshot/1",
        "foundation": {"revision_id": str(foundation_id), "version": 1, "valid_from": "2026-10-01T00:00:00Z",
                       "valid_to": None},
        "mapping": {"binding_set_id": "set-1", "version": 1, "valid_from": "2026-10-01T00:00:00Z", "valid_to": None},
        "gateway": {"gateway_id": "gw"},
        "bindings": rows,
    }
    body = json.dumps(doc, sort_keys=True, separators=(",", ":")).encode("utf-8")
    sha = hashlib.sha256(body).hexdigest()
    return StoredBindingSet(set_id, foundation_id, sha, body, False, False), {
        "foundation_version": 1, "foundation_valid_from": "2026-10-01T00:00:00Z", "binding_set_id": "set-1",
        "binding_version": 1, "snapshot_sha256": sha}


def _row(device, signal, **extra) -> dict:
    return {"binding_revision_id": str(uuid4()), "device_id": device, "signal_id": signal, "source_id": "src",
            "asset_id": None, "role": "r", "source_unit": "none", "canonical_unit": "none",
            "conversion": {"kind": "IDENTITY", "parameters": {}}, **extra}


def test_basis_reads_absent_v4_keys_as_none_and_present_keys_exactly() -> None:
    stored, kw = _stored([_row("pv", "power"), _row("door-sensor", "event", **META)])
    basis = basis_from_snapshot(stored, **kw)
    v3, v4 = basis.bindings[("pv", "power")], basis.bindings[("door-sensor", "event")]
    assert (v3.allowed_record_kinds, v3.allowed_outcomes, v3.requires_correlation, v3.requires_session,
            v3.allowed_units) == (None,) * 5
    assert v3.v4_metadata() is None
    assert v4.v4_metadata() == META


def test_decide_accepts_a_closed_tuple_only_when_the_pinned_row_matches() -> None:
    from assetops_contracts.source_envelope import canonical_json
    from assetops_contracts.source_envelope_v3 import v3_message_id

    def envelope(signal="event") -> str:
        return canonical_json({
            "schema": {"id": "assetops.source-envelope", "version": 4},
            "message": {"message_id": v3_message_id(site_id="site", gateway_id="gw", source_id="src",
                                                    sequence_epoch="e", sequence=1),
                        "sequence_epoch": "e", "sequence": 1},
            "source": {"site_id": "site", "gateway_id": "gw", "source_id": "src", "device_id": "door-sensor",
                       "signal_id": signal},
            "mapping": {"binding_set_id": "set-1", "version": 1},
            "timing": {"source_time": "2026-10-06T19:10:00Z", "published_at": "2026-10-06T19:10:00Z",
                       "interval_start": None, "interval_end": None},
            "payload": {"family": "EVENT", "record_kind": "DOOR_OPEN", "event_id": "d-1", "correlation_id": "c-1",
                        "component_id": "door-1", "actor": "SENSOR", "outcome": "OPEN", "unit": None,
                        "value": None, "quality": "GOOD", "session_id": None, "connector_id": None},
        })

    stored, kw = _stored([_row("door-sensor", "event", **{**META, "role": "door_event"})])
    accepted = decide(basis_from_snapshot(stored, **kw), 0, envelope())
    assert type(accepted).__name__ == "Accepted" and accepted.is_v4 and accepted.conversion_kind is None
    stored, kw = _stored([_row("door-sensor", "event", role="door_event")])  # pinned without v4 metadata
    refused = decide(basis_from_snapshot(stored, **kw), 0, envelope())
    assert (refused.kind, refused.field) == ("MAPPING_INCOMPATIBLE", "mapping")
    # W2-01 (W2-00 review Low 2): the closed table names the channel's role; a pinned row naming
    # another role is refused even when its five v4 keys match.
    stored, kw = _stored([_row("door-sensor", "event", **{**META, "role": "manual_temperature"})])
    refused = decide(basis_from_snapshot(stored, **kw), 0, envelope())
    assert (refused.kind, refused.field) == ("MAPPING_INCOMPATIBLE", "mapping")
    assert "serves door_event" in refused.detail
