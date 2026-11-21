"""3B7a unit 3 (spec §4.2; D-3B7A.9): the structure snapshot store over Postgres, in 3A1's adapter style.

The sole runtime writer of `structure_snapshot` (migration 0066), with one plain `INSERT INTO structure_snapshot
(...) VALUES (...)` per row inside one transaction; a unique violation (23505) rolls the whole put back and raises
`SnapshotExists`. No UPDATE, DELETE or TRUNCATE (the 0005 `ledger_append_only()` trigger refuses them as well).
`held_kinds` and `site_snapshot_ids` are bound as Python lists, never cast (P3); `stamps` is canonical JSON.
"""
from __future__ import annotations

from collections.abc import Sequence
from datetime import timezone
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from assetops_backend.chain.ports import SiteRef
from assetops_backend.structure_snapshot.codec import stamps_from_json, stamps_json
from assetops_backend.structure_snapshot.model import SnapshotRow
from assetops_backend.structure_snapshot.store import SnapshotExists

_COLUMNS = ("id, tenant_id, site_id, period, rules_digest, held_kinds, structure_key, structure_version, format, "
            "as_of, built_by, closed_at_build, stamps, payload, payload_sha256, site_snapshot_ids")
_INSERT = text(
    "INSERT INTO structure_snapshot (id, tenant_id, site_id, period, rules_digest, held_kinds, structure_key, "
    "structure_version, format, as_of, built_by, closed_at_build, stamps, payload, payload_sha256, "
    "site_snapshot_ids) VALUES (:id, :tenant_id, :site_id, :period, :rules_digest, :held_kinds, :structure_key, "
    ":structure_version, :format, :as_of, :built_by, :closed_at_build, :stamps, :payload, :payload_sha256, "
    ":site_snapshot_ids)")
_TENANT = text("SELECT id FROM tenant WHERE slug = :slug")
_SITES = text("SELECT id, site_code, site_type, timezone FROM site WHERE tenant_id = :t")
_LATEST_SITE = text("SELECT " + _COLUMNS + " FROM structure_snapshot WHERE tenant_id = :t AND site_id = :s "
                    "AND period = :p ORDER BY as_of DESC LIMIT 1")
_LATEST_PORTFOLIO = text("SELECT " + _COLUMNS + " FROM structure_snapshot WHERE tenant_id = :t AND site_id IS NULL "
                         "AND period = :p ORDER BY as_of DESC LIMIT 1")
_BY_IDS = text("SELECT " + _COLUMNS + " FROM structure_snapshot WHERE tenant_id = :t AND id = ANY(:ids)")
_UNIQUE_VIOLATION = "23505"


def _values(row: SnapshotRow) -> dict:
    return {"id": row.id, "tenant_id": row.tenant_id, "site_id": row.site_id, "period": row.period,
            "rules_digest": row.rules_digest, "held_kinds": list(row.held_kinds), "structure_key": row.structure_key,
            "structure_version": row.structure_version, "format": row.format, "as_of": row.as_of,
            "built_by": row.built_by, "closed_at_build": row.closed_at_build, "stamps": stamps_json(row.stamps),
            "payload": row.payload, "payload_sha256": row.payload_sha256,
            "site_snapshot_ids": None if row.site_snapshot_ids is None else list(row.site_snapshot_ids)}


def _row(r) -> SnapshotRow:
    return SnapshotRow(
        id=r.id, tenant_id=r.tenant_id, site_id=r.site_id, period=r.period, structure_key=r.structure_key,
        structure_version=r.structure_version, format=r.format, as_of=r.as_of.astimezone(timezone.utc),
        built_by=r.built_by, closed_at_build=r.closed_at_build, rules_digest=r.rules_digest,
        held_kinds=tuple(r.held_kinds), stamps=stamps_from_json(r.stamps), payload=r.payload,
        payload_sha256=r.payload_sha256,
        site_snapshot_ids=None if r.site_snapshot_ids is None else tuple(r.site_snapshot_ids))


class PostgresStructureSnapshotStore:
    def __init__(self, url: str) -> None:
        self._engine = create_engine(url, pool_pre_ping=True, hide_parameters=True)

    def dispose(self) -> None:
        self._engine.dispose()

    def tenant_sites(self, slug: str) -> tuple[UUID, tuple[SiteRef, ...]] | None:
        with self._engine.connect() as c:
            tenant = c.execute(_TENANT, {"slug": slug}).scalar_one_or_none()
            if tenant is None:
                return None
            rows = c.execute(_SITES, {"t": tenant}).all()
        sites = [SiteRef(tenant, r.id, r.site_code, r.site_type, r.timezone) for r in rows]
        return tenant, tuple(sorted(sites, key=lambda s: s.site_code))

    def put(self, rows: Sequence[SnapshotRow]) -> None:
        try:
            with self._engine.begin() as c:
                for row in rows:
                    c.execute(_INSERT, _values(row))
        except IntegrityError as error:
            if getattr(error.orig, "sqlstate", None) == _UNIQUE_VIOLATION:
                raise SnapshotExists() from None
            raise

    def latest_site(self, tenant_id: UUID, site_id: UUID, period: str) -> SnapshotRow | None:
        with self._engine.connect() as c:
            r = c.execute(_LATEST_SITE, {"t": tenant_id, "s": site_id, "p": period}).one_or_none()
        return None if r is None else _row(r)

    def latest_portfolio(self, tenant_id: UUID, period: str) -> SnapshotRow | None:
        with self._engine.connect() as c:
            r = c.execute(_LATEST_PORTFOLIO, {"t": tenant_id, "p": period}).one_or_none()
        return None if r is None else _row(r)

    def get(self, tenant_id: UUID, ids: Sequence[UUID]) -> tuple[SnapshotRow, ...]:
        ids = list(ids)
        if not ids:
            return ()
        with self._engine.connect() as c:
            found = {r.id: _row(r) for r in c.execute(_BY_IDS, {"t": tenant_id, "ids": ids}).all()}
        out = []
        for i in ids:
            if i not in found:
                raise LookupError(f"no snapshot {i}")
            out.append(found[i])
        return tuple(out)


__all__ = ["PostgresStructureSnapshotStore"]
