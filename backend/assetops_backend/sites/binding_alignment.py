"""Binding periods aligned to Foundation periods, and the pinned snapshot (S1-02).

Decision `D-2026-10-08-s1-bindings-roles-and-snapshot`:

* Q5 - binding coverage runs through every Foundation period: each currently
  recorded binding set revision lies inside exactly one currently recorded
  Foundation revision and names it. A publication that splits or replaces a
  Foundation revision (a reserve change, a joint signal declaration) therefore
  also replaces every binding set revision that named it, with unchanged copies
  aligned to the new Foundation periods. Nothing old is edited; the replaced
  rows' recorded periods close.
* Q6 - each binding set revision is one acquisition snapshot. Its canonical
  bytes are produced by a versioned serializer from immutable inputs only (no
  recorded-time closure, request time or gateway status), and their SHA-256
  and the serializer version are persisted on the row in the publishing
  transaction, together with the canonical bytes themselves. The serializer
  reads registration fields (site code, gateway external ID and mode, source
  external IDs) that the schema does not make immutable, so a download serves
  the stored bytes and checks them against the stored hash; it never rebuilds
  them from current registrations (S1-02 fix round, review M1).

Pure: no storage technology is named here.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any, Sequence
from uuid import UUID, uuid4

from assetops_backend.sites.foundation_records import (
    BindingRow,
    BindingSetRevisionRow,
    ConfigurationPlan,
    ConfigurationState,
    Registrations,
    RevisionRow,
    StoredSite,
)

SNAPSHOT_SCHEMA_V1 = "assetops.acquisition-snapshot/1"
#: Placeholder carried by a draft binding set revision until `finalize`
#: aligns it and pins its snapshot.
UNPINNED = "UNPINNED"

_END = datetime.max.replace(tzinfo=timezone.utc)


def _until(value: datetime | None) -> datetime:
    return _END if value is None else value


def _iso(value: datetime | None) -> str | None:
    return None if value is None else value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_bytes(document: Any) -> bytes:
    """Sorted keys, no whitespace, UTF-8, non-ASCII kept: the hashed spelling."""
    return json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def binding_content(row: BindingRow) -> dict[str, Any]:
    return {
        "device_id": row.device_id,
        "signal_id": row.signal_id,
        "source_id": str(row.source_id),
        "gateway_id": str(row.gateway_id),
        "asset_id": None if row.asset_id is None else str(row.asset_id),
        "role": row.role,
        "source_unit": row.source_unit,
        "canonical_unit": row.canonical_unit,
        "conversion": row.conversion,
    }


def snapshot_document_v1(
    tenant_id: UUID,
    site: StoredSite,
    registrations: Registrations,
    foundation: RevisionRow,
    binding_set: BindingSetRevisionRow,
) -> dict[str, Any]:
    """The `assetops.acquisition-snapshot/1` document. Immutable inputs only."""
    gateway = next(g for g in registrations.gateways if g.id == binding_set.gateway_id)
    used = {b.source_id for b in binding_set.bindings}
    return {
        "schema": SNAPSHOT_SCHEMA_V1,
        "tenant_id": str(tenant_id),
        "site": {"site_id": str(site.id), "site_code": site.site_code},
        "gateway": {
            "gateway_id": str(gateway.id),
            "gateway_external_id": gateway.gateway_external_id,
            "mode": gateway.mode,
        },
        "foundation": {
            "revision_id": str(foundation.id),
            "version": foundation.version,
            "valid_from": _iso(foundation.valid_from),
            "valid_to": _iso(foundation.valid_to),
            "content_sha256": foundation.content_sha256,
        },
        "mapping": {
            "binding_set_id": str(binding_set.binding_set_id),
            "binding_set_revision_id": str(binding_set.id),
            "version": binding_set.version,
            "role_set": binding_set.role_set,
            "valid_from": _iso(binding_set.valid_from),
            "valid_to": _iso(binding_set.valid_to),
            "bindings_sha256": binding_set.bindings_sha256,
        },
        "sources": sorted(
            (
                {"source_id": str(s.id), "source_external_id": s.source_external_id}
                for s in registrations.sources
                if s.id in used
            ),
            key=lambda s: s["source_external_id"],
        ),
        "bindings": sorted(
            ({"binding_revision_id": str(b.id), **binding_content(b)} for b in binding_set.bindings),
            key=lambda b: (b["device_id"], b["signal_id"]),
        ),
    }


SERIALIZERS = {SNAPSHOT_SCHEMA_V1: snapshot_document_v1}


def snapshot_bytes(
    schema: str,
    tenant_id: UUID,
    site: StoredSite,
    registrations: Registrations,
    foundation: RevisionRow,
    binding_set: BindingSetRevisionRow,
) -> bytes:
    serializer = SERIALIZERS[schema]
    return canonical_bytes(serializer(tenant_id, site, registrations, foundation, binding_set))


def _copy_rows(bindings: Sequence[BindingRow]) -> tuple[BindingRow, ...]:
    return tuple(replace(b, id=uuid4()) for b in bindings)


def finalize(
    state: ConfigurationState,
    plan: ConfigurationPlan,
    *,
    tenant_id: UUID,
    site: StoredSite,
    registrations: Registrations,
    now: datetime,
) -> tuple[ConfigurationPlan, dict[UUID, tuple[BindingSetRevisionRow, ...]]]:
    """Align every current binding set revision to the post-plan Foundation, and pin snapshots.

    Returns the completed plan and, for each draft binding set revision the
    caller inserted, the aligned revisions it became (a draft spanning several
    Foundation periods becomes one per period).
    """
    superseded_rev = set(plan.supersede_revision_ids)
    foundation_after = [
        r for r in state.revisions if r.superseded_at is None and r.id not in superseded_rev
    ] + list(plan.revision_inserts)
    by_id = {r.id: r for r in foundation_after}
    superseded_sets = set(plan.supersede_binding_set_ids)
    kept = [s for s in state.binding_sets if s.superseded_at is None and s.id not in superseded_sets]

    supersede_more: list[UUID] = []
    pieces: list[tuple[UUID | None, BindingSetRevisionRow, RevisionRow]] = []

    def split(candidate: BindingSetRevisionRow, origin_id: UUID | None, fresh_rows: bool) -> None:
        overlapping = sorted(
            (
                f for f in foundation_after
                if f.valid_from < _until(candidate.valid_to) and candidate.valid_from < _until(f.valid_to)
            ),
            key=lambda f: f.valid_from,
        )
        for index, f in enumerate(overlapping):
            start = max(candidate.valid_from, f.valid_from)
            end_at = min(_until(candidate.valid_to), _until(f.valid_to))
            piece = replace(
                candidate,
                id=candidate.id if (index == 0 and not fresh_rows) else uuid4(),
                valid_from=start,
                valid_to=None if end_at == _END else end_at,
                bindings=candidate.bindings if (index == 0 and not fresh_rows) else _copy_rows(candidate.bindings),
            )
            pieces.append((origin_id, piece, f))

    for current in kept:
        anchor = by_id.get(current.foundation_revision_id)
        if (
            anchor is not None
            and anchor.valid_from <= current.valid_from
            and _until(current.valid_to) <= _until(anchor.valid_to)
        ):
            continue
        # Its Foundation revision was replaced: unchanged copies, aligned.
        supersede_more.append(current.id)
        split(
            replace(
                current,
                origin="SPLIT",
                derived_from_revision_id=current.id,
                change_note=f"Unchanged binding v{current.version}, aligned to the new Foundation periods",
                recorded_at=now,
                superseded_at=None,
            ),
            None,
            fresh_rows=True,
        )
    for draft in plan.binding_set_inserts:
        split(draft, draft.id, fresh_rows=False)

    next_version = max((s.version for s in state.binding_sets), default=0) + 1
    finished: list[BindingSetRevisionRow] = []
    became: dict[UUID, list[BindingSetRevisionRow]] = {}
    for origin_id, piece, foundation in sorted(pieces, key=lambda p: (p[1].valid_from, p[1].version)):
        aligned = replace(
            piece,
            version=next_version,
            foundation_revision_id=foundation.id,
            gateway_id=piece.bindings[0].gateway_id if piece.bindings else registrations.gateways[0].id,
            snapshot_schema=SNAPSHOT_SCHEMA_V1,
            snapshot_sha256=UNPINNED,
        )
        next_version += 1
        body = snapshot_bytes(SNAPSHOT_SCHEMA_V1, tenant_id, site, registrations, foundation, aligned)
        aligned = replace(aligned, snapshot_sha256=hashlib.sha256(body).hexdigest(), snapshot_canonical=body)
        finished.append(aligned)
        if origin_id is not None:
            became.setdefault(origin_id, []).append(aligned)
    completed = replace(
        plan,
        supersede_binding_set_ids=tuple(plan.supersede_binding_set_ids) + tuple(supersede_more),
        binding_set_inserts=tuple(finished),
    )
    return completed, {k: tuple(v) for k, v in became.items()}
