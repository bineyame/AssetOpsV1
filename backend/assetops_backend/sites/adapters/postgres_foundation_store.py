"""PostgreSQL adapter for the persisted Foundation (S1-01).

The sole writer for imported product Sites. It never creates schema: Alembic
migrations in `backend/migrations` own the DDL, and a database that has not
been migrated answers as unavailable rather than being repaired here.

Every statement carries the resolved tenant UUID in its predicate, so a Site
code or row UUID belonging to another tenant is simply not found. Publishing
locks the Site row (`FOR UPDATE`) and the GiST exclusion constraint on
currently recorded validity is the final guard against a concurrent mistake.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Callable, Sequence
from uuid import UUID, uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import DBAPIError, IntegrityError, OperationalError, ProgrammingError

from assetops_backend.sites.binding_alignment import V4_BINDING_KEYS
from assetops_backend.sites.foundation_records import (
    AssetRow,
    BindingOverlap,
    BindingRow,
    BindingSetRevisionRow,
    ConfigurationPlan,
    ConfigurationPlanner,
    ConfigurationState,
    FoundationOverlap,
    FoundationSiteCodeTaken,
    FoundationSiteNotFound,
    FoundationStoreUnavailable,
    GatewayRow,
    ImportPlan,
    ImportRecord,
    PublishPlan,
    PublishPlanner,
    Registrations,
    RevisionRow,
    SourceRow,
    StoredSite,
    TenantNotFound,
    TenantRef,
)

_SITE_COLUMNS = """
    s.id, s.tenant_id, s.site_code, s.name, s.site_type, s.timezone, s.lifecycle,
    s.country, s.locality, s.origin, s.proposed_source_mode, s.template_id,
    s.template_version, s.created_at,
    i.id AS import_id, i.source_path, i.source_sha256, i.source_format, i.imported_at
"""

_REVISION_COLUMNS = """
    id, version, valid_from, valid_to, recorded_at, superseded_at, schema_version,
    content, content_sha256, origin, derived_from_revision_id, change_note
"""


def _site(row: Any) -> StoredSite:
    record = None
    if row.import_id is not None:
        record = ImportRecord(
            id=row.import_id,
            source_path=row.source_path,
            source_sha256=row.source_sha256,
            source_format=row.source_format,
            imported_at=row.imported_at,
        )
    return StoredSite(
        id=row.id,
        tenant_id=row.tenant_id,
        site_code=row.site_code,
        name=row.name,
        site_type=row.site_type,
        timezone=row.timezone,
        lifecycle=row.lifecycle,
        country=row.country,
        locality=row.locality,
        origin=row.origin,
        proposed_source_mode=row.proposed_source_mode,
        template_id=row.template_id,
        template_version=row.template_version,
        created_at=row.created_at,
        import_record=record,
    )


def _revision(row: Any) -> RevisionRow:
    return RevisionRow(
        id=row.id,
        version=row.version,
        valid_from=row.valid_from,
        valid_to=row.valid_to,
        recorded_at=row.recorded_at,
        superseded_at=row.superseded_at,
        schema_version=row.schema_version,
        content=row.content,
        content_sha256=row.content_sha256,
        origin=row.origin,
        derived_from_revision_id=row.derived_from_revision_id,
        change_note=row.change_note,
    )


class PostgresFoundationStore:
    """`FoundationStore` over a migrated PostgreSQL database."""

    def __init__(self, database_url: str | None) -> None:
        self._database_url = database_url
        self._engine: Engine | None = None

    # --- plumbing -----------------------------------------------------------

    def _connect_engine(self) -> Engine:
        if not self._database_url:
            raise FoundationStoreUnavailable(
                "DATABASE_URL is not set, so the product Foundation store cannot be "
                "reached. See backend/README-db.md."
            )
        if self._engine is None:
            self._engine = create_engine(self._database_url, pool_pre_ping=True)
        return self._engine

    def _run(self, work, *, write: bool = False, connection: Connection | None = None):
        try:
            if connection is not None:
                # S6-01a: a caller-owned transaction; this store neither begins nor commits on it.
                return work(connection)
            engine = self._connect_engine()
            if write:
                with engine.begin() as connection:
                    return work(connection)
            with engine.connect() as connection:
                return work(connection)
        except (
            FoundationSiteNotFound, FoundationOverlap, BindingOverlap, FoundationSiteCodeTaken, TenantNotFound
        ):
            raise
        except IntegrityError as error:
            message = str(error.orig)
            if "binding_set_no_current_overlap" in message or "binding_no_current_channel_overlap" in message:
                raise BindingOverlap(
                    "The change would overlap a currently recorded binding set or channel "
                    "binding for this Site; nothing was written."
                ) from error
            if "foundation_revision_no_current_overlap" in message:
                raise FoundationOverlap(
                    "The change would overlap a currently recorded Foundation period "
                    "for this Site; nothing was written."
                ) from error
            if "site_tenant_code_unique" in message:
                raise FoundationSiteCodeTaken(
                    "Another Site in this tenant already holds that code."
                ) from error
            raise
        except (OperationalError, ProgrammingError) as error:
            raise FoundationStoreUnavailable(
                f"The product Foundation store could not be read or written: {error.orig}"
            ) from error
        except DBAPIError as error:
            raise FoundationStoreUnavailable(str(error.orig)) from error

    # --- tenant -------------------------------------------------------------

    def resolve_tenant(self, slug: str) -> TenantRef:
        def work(connection: Connection) -> TenantRef:
            row = connection.execute(
                text("SELECT id, slug, name FROM tenant WHERE slug = :slug"),
                {"slug": slug},
            ).first()
            if row is None:
                raise TenantNotFound(f"No tenant {slug!r} is registered.")
            return TenantRef(id=row.id, slug=row.slug, name=row.name)

        return self._run(work)

    def ensure_tenant(self, slug: str, name: str, *, now: datetime) -> TenantRef:
        def work(connection: Connection) -> TenantRef:
            connection.execute(
                text(
                    "INSERT INTO tenant (id, slug, name, created_at) "
                    "VALUES (:id, :slug, :name, :now) ON CONFLICT (slug) DO NOTHING"
                ),
                {"id": uuid4(), "slug": slug, "name": name, "now": now},
            )
            row = connection.execute(
                text("SELECT id, slug, name FROM tenant WHERE slug = :slug"),
                {"slug": slug},
            ).one()
            return TenantRef(id=row.id, slug=row.slug, name=row.name)

        return self._run(work, write=True)

    # --- reads --------------------------------------------------------------

    def _select_sites(self, connection: Connection, where: str, params: dict) -> list[StoredSite]:
        rows = connection.execute(
            text(
                f"SELECT {_SITE_COLUMNS} FROM site s "
                "LEFT JOIN site_import i ON i.tenant_id = s.tenant_id AND i.site_id = s.id "
                f"WHERE s.tenant_id = :tenant_id AND {where} ORDER BY s.site_code"
            ),
            params,
        ).all()
        return [_site(row) for row in rows]

    def find_site(self, tenant_id: UUID, site_code: str) -> StoredSite | None:
        def work(connection: Connection) -> StoredSite | None:
            found = self._select_sites(
                connection,
                "s.site_code_key = :key",
                {"tenant_id": tenant_id, "key": site_code.lower()},
            )
            return found[0] if found else None

        return self._run(work)

    def find_site_by_id(self, tenant_id: UUID, site_id: UUID) -> StoredSite | None:
        def work(connection: Connection) -> StoredSite | None:
            found = self._select_sites(
                connection, "s.id = :site_id", {"tenant_id": tenant_id, "site_id": site_id}
            )
            return found[0] if found else None

        return self._run(work)

    def record_no_legacy_evidence_basis(self, tenant_id: UUID, site_id: UUID, *, now: datetime) -> None:
        """q12-6: persist the explicit `NO_LEGACY_EVIDENCE` cutover basis for the Site's current import. Only an
        installer whose import carries no legacy documents calls this; idempotent for the same import."""
        params = {"tenant_id": tenant_id, "site_id": site_id, "now": now}

        def work(connection: Connection) -> None:
            imported = connection.execute(
                text("SELECT id, source_sha256 FROM site_import WHERE tenant_id = :tenant_id AND site_id = :site_id"),
                params,
            ).one_or_none()
            if imported is None:
                raise ValueError("A cutover basis needs the Site's import record.")
            connection.execute(
                text(
                    "INSERT INTO site_cutover_basis (tenant_id, site_id, site_import_id, source_sha256, basis, recorded_at) "
                    "VALUES (:tenant_id, :site_id, :import_id, :sha, 'NO_LEGACY_EVIDENCE', :now) "
                    "ON CONFLICT (tenant_id, site_id) DO NOTHING"
                ),
                {**params, "import_id": imported.id, "sha": imported.source_sha256},
            )

        self._run(work, write=True)

    def no_legacy_evidence_basis(self, tenant_id: UUID, site_id: UUID) -> bool:
        """q12-6: True only when a persisted `NO_LEGACY_EVIDENCE` basis names the Site's current import row and
        digest. A missing basis (or one for another import) is False; it is never inferred from a comparison."""

        def work(connection: Connection) -> bool:
            return connection.execute(
                text(
                    "SELECT EXISTS (SELECT 1 FROM site_cutover_basis b JOIN site_import i "
                    "ON i.id = b.site_import_id AND i.tenant_id = b.tenant_id AND i.site_id = b.site_id "
                    "AND i.source_sha256 = b.source_sha256 "
                    "WHERE b.tenant_id = :tenant_id AND b.site_id = :site_id AND b.basis = 'NO_LEGACY_EVIDENCE')"
                ),
                {"tenant_id": tenant_id, "site_id": site_id},
            ).scalar_one()

        return bool(self._run(work))

    def list_sites(self, tenant_id: UUID) -> Sequence[StoredSite]:
        return tuple(
            self._run(lambda connection: self._select_sites(connection, "TRUE", {"tenant_id": tenant_id}))
        )

    def registrations(self, tenant_id: UUID, site_id: UUID) -> Registrations:
        params = {"tenant_id": tenant_id, "site_id": site_id}

        def work(connection: Connection) -> Registrations:
            assets = connection.execute(
                text(
                    "SELECT id, asset_code, asset_type, attributes FROM asset "
                    "WHERE tenant_id = :tenant_id AND site_id = :site_id ORDER BY created_at, asset_code"
                ),
                params,
            ).all()
            gateways = connection.execute(
                text(
                    "SELECT id, gateway_external_id, mode, credential_ref, registered_at, disabled_at "
                    "FROM gateway WHERE tenant_id = :tenant_id AND site_id = :site_id "
                    "ORDER BY gateway_external_id"
                ),
                params,
            ).all()
            sources = connection.execute(
                text(
                    "SELECT id, gateway_id, source_external_id, device_kind, asset_id, "
                    "registered_at, disabled_at FROM source "
                    "WHERE tenant_id = :tenant_id AND site_id = :site_id ORDER BY registered_at, source_external_id"
                ),
                params,
            ).all()
            return Registrations(
                assets=tuple(
                    AssetRow(id=r.id, asset_code=r.asset_code, asset_type=r.asset_type, attributes=r.attributes)
                    for r in assets
                ),
                gateways=tuple(
                    GatewayRow(
                        id=r.id,
                        gateway_external_id=r.gateway_external_id,
                        mode=r.mode,
                        credential_ref=r.credential_ref,
                        registered_at=r.registered_at,
                        disabled_at=r.disabled_at,
                    )
                    for r in gateways
                ),
                sources=tuple(
                    SourceRow(
                        id=r.id,
                        gateway_id=r.gateway_id,
                        source_external_id=r.source_external_id,
                        device_kind=r.device_kind,
                        asset_id=r.asset_id,
                        registered_at=r.registered_at,
                        disabled_at=r.disabled_at,
                    )
                    for r in sources
                ),
            )

        return self._run(work)

    def revisions(self, tenant_id: UUID, site_id: UUID) -> Sequence[RevisionRow]:
        def work(connection: Connection) -> tuple[RevisionRow, ...]:
            return self._select_revisions(connection, tenant_id, site_id)

        return self._run(work)

    @staticmethod
    def _select_revisions(connection: Connection, tenant_id: UUID, site_id: UUID) -> tuple[RevisionRow, ...]:
        rows = connection.execute(
            text(
                f"SELECT {_REVISION_COLUMNS} FROM foundation_revision "
                "WHERE tenant_id = :tenant_id AND site_id = :site_id ORDER BY version"
            ),
            {"tenant_id": tenant_id, "site_id": site_id},
        ).all()
        return tuple(_revision(row) for row in rows)

    # --- writes -------------------------------------------------------------

    @staticmethod
    def _insert_revision(connection: Connection, tenant_id: UUID, site_id: UUID, revision: RevisionRow) -> None:
        connection.execute(
            text(
                "INSERT INTO foundation_revision (id, tenant_id, site_id, version, valid_from, "
                "valid_to, recorded_at, superseded_at, schema_version, content, content_sha256, "
                "origin, derived_from_revision_id, change_note) VALUES (:id, :tenant_id, :site_id, "
                ":version, :valid_from, :valid_to, :recorded_at, NULL, :schema_version, "
                "CAST(:content AS jsonb), :content_sha256, :origin, :derived_from, :change_note)"
            ),
            {
                "id": revision.id,
                "tenant_id": tenant_id,
                "site_id": site_id,
                "version": revision.version,
                "valid_from": revision.valid_from,
                "valid_to": revision.valid_to,
                "recorded_at": revision.recorded_at,
                "schema_version": revision.schema_version,
                "content": json.dumps(revision.content),
                "content_sha256": revision.content_sha256,
                "origin": revision.origin,
                "derived_from": revision.derived_from_revision_id,
                "change_note": revision.change_note,
            },
        )

    def insert_import(self, tenant_id: UUID, plan: ImportPlan) -> None:
        site = plan.site
        if site.tenant_id != tenant_id or site.import_record is None:
            raise ValueError("An import plan must belong to the resolved tenant and name its source.")

        def work(connection: Connection) -> None:
            connection.execute(
                text(
                    "INSERT INTO site (id, tenant_id, site_code, site_code_key, name, site_type, "
                    "timezone, lifecycle, country, locality, origin, proposed_source_mode, "
                    "template_id, template_version, created_at) VALUES (:id, :tenant_id, :code, "
                    ":key, :name, :type, :tz, :lifecycle, :country, :locality, :origin, :mode, "
                    ":template_id, :template_version, :created_at)"
                ),
                {
                    "id": site.id,
                    "tenant_id": tenant_id,
                    "code": site.site_code,
                    "key": site.site_code.lower(),
                    "name": site.name,
                    "type": site.site_type,
                    "tz": site.timezone,
                    "lifecycle": site.lifecycle,
                    "country": site.country,
                    "locality": site.locality,
                    "origin": site.origin,
                    "mode": site.proposed_source_mode,
                    "template_id": site.template_id,
                    "template_version": site.template_version,
                    "created_at": site.created_at,
                },
            )
            record = site.import_record
            connection.execute(
                text(
                    "INSERT INTO site_import (id, tenant_id, site_id, source_path, source_sha256, "
                    "source_format, imported_at) VALUES (:id, :tenant_id, :site_id, :path, :sha, "
                    ":format, :at)"
                ),
                {
                    "id": record.id,
                    "tenant_id": tenant_id,
                    "site_id": site.id,
                    "path": record.source_path,
                    "sha": record.source_sha256,
                    "format": record.source_format,
                    "at": record.imported_at,
                },
            )
            for asset in plan.assets:
                connection.execute(
                    text(
                        "INSERT INTO asset (id, tenant_id, site_id, asset_code, asset_type, "
                        "attributes, created_at) VALUES (:id, :tenant_id, :site_id, :code, :type, "
                        "CAST(:attributes AS jsonb), :created_at)"
                    ),
                    {
                        "id": asset.id,
                        "tenant_id": tenant_id,
                        "site_id": site.id,
                        "code": asset.asset_code,
                        "type": asset.asset_type,
                        "attributes": json.dumps(asset.attributes),
                        "created_at": site.created_at,
                    },
                )
            gateway = plan.gateway
            connection.execute(
                text(
                    "INSERT INTO gateway (id, tenant_id, site_id, gateway_external_id, mode, "
                    "credential_ref, registered_at, disabled_at) VALUES (:id, :tenant_id, :site_id, "
                    ":external_id, :mode, :credential_ref, :registered_at, :disabled_at)"
                ),
                {
                    "id": gateway.id,
                    "tenant_id": tenant_id,
                    "site_id": site.id,
                    "external_id": gateway.gateway_external_id,
                    "mode": gateway.mode,
                    "credential_ref": gateway.credential_ref,
                    "registered_at": gateway.registered_at,
                    "disabled_at": gateway.disabled_at,
                },
            )
            for source in plan.sources:
                connection.execute(
                    text(
                        "INSERT INTO source (id, tenant_id, site_id, gateway_id, source_external_id, "
                        "device_kind, asset_id, registered_at, disabled_at) VALUES (:id, :tenant_id, "
                        ":site_id, :gateway_id, :external_id, :kind, :asset_id, :registered_at, "
                        ":disabled_at)"
                    ),
                    {
                        "id": source.id,
                        "tenant_id": tenant_id,
                        "site_id": site.id,
                        "gateway_id": source.gateway_id,
                        "external_id": source.source_external_id,
                        "kind": source.device_kind,
                        "asset_id": source.asset_id,
                        "registered_at": source.registered_at,
                        "disabled_at": source.disabled_at,
                    },
                )
            self._insert_revision(connection, tenant_id, site.id, plan.revision)

        self._run(work, write=True)

    def publish(self, tenant_id: UUID, site_id: UUID, planner: PublishPlanner) -> PublishPlan:
        def work(connection: Connection) -> PublishPlan:
            locked = connection.execute(
                text("SELECT id FROM site WHERE tenant_id = :tenant_id AND id = :site_id FOR UPDATE"),
                {"tenant_id": tenant_id, "site_id": site_id},
            ).first()
            if locked is None:
                raise FoundationSiteNotFound("No such Site in this tenant.")
            plan = planner(self._select_revisions(connection, tenant_id, site_id))
            for revision_id in plan.supersede_ids:
                result = connection.execute(
                    text(
                        "UPDATE foundation_revision SET superseded_at = :at WHERE tenant_id = :tenant_id "
                        "AND site_id = :site_id AND id = :id AND superseded_at IS NULL"
                    ),
                    {"at": plan.superseded_at, "tenant_id": tenant_id, "site_id": site_id, "id": revision_id},
                )
                if result.rowcount != 1:
                    raise FoundationOverlap(
                        "A revision this change supersedes is no longer current; nothing was written."
                    )
            for revision in plan.inserts:
                self._insert_revision(connection, tenant_id, site_id, revision)
            self._enqueue_mini_configuration(
                connection, tenant_id, site_id, [(r.valid_from, r.valid_to) for r in plan.inserts],
                plan.superseded_at)
            return plan

        return self._run(work, write=True)

    # --- signal bindings (S1-02) --------------------------------------------

    @staticmethod
    def _select_binding_sets(
        connection: Connection, tenant_id: UUID, site_id: UUID
    ) -> tuple[BindingSetRevisionRow, ...]:
        params = {"tenant_id": tenant_id, "site_id": site_id}
        rows = connection.execute(
            text(
                "SELECT id, binding_set_id, version, role_set, valid_from, valid_to, recorded_at, "
                "superseded_at, bindings_sha256, origin, derived_from_revision_id, change_note, "
                "foundation_revision_id, gateway_id, snapshot_schema, snapshot_sha256, snapshot_canonical "
                "FROM signal_binding_set_revision WHERE tenant_id = :tenant_id AND site_id = :site_id "
                "ORDER BY version"
            ),
            params,
        ).all()
        bindings = connection.execute(
            text(
                "SELECT id, binding_set_revision_id, gateway_id, source_id, device_id, signal_id, "
                "asset_id, role, source_unit, canonical_unit, conversion FROM signal_binding_revision "
                "WHERE tenant_id = :tenant_id AND site_id = :site_id ORDER BY device_id, signal_id"
            ),
            params,
        ).all()
        # W2-02 (`D-2026-10-17-w2-02-buildspec`): a v4 row's five metadata keys live in the immutable
        # snapshot document the set revision persisted; read them back from there (no column, no migration).
        v4_by_binding: dict[str, dict] = {}
        for r in rows:
            if r.snapshot_canonical is None:
                continue
            for entry in json.loads(bytes(r.snapshot_canonical)).get("bindings") or ():
                if all(k in entry for k in V4_BINDING_KEYS):
                    v4_by_binding[entry["binding_revision_id"]] = {k: entry[k] for k in V4_BINDING_KEYS}
        by_set: dict[UUID, list[BindingRow]] = {}
        for b in bindings:
            by_set.setdefault(b.binding_set_revision_id, []).append(
                BindingRow(
                    id=b.id,
                    gateway_id=b.gateway_id,
                    source_id=b.source_id,
                    device_id=b.device_id,
                    signal_id=b.signal_id,
                    asset_id=b.asset_id,
                    role=b.role,
                    source_unit=b.source_unit,
                    canonical_unit=b.canonical_unit,
                    conversion=b.conversion,
                    v4_mapping=v4_by_binding.get(str(b.id)),
                )
            )
        return tuple(
            BindingSetRevisionRow(
                id=r.id,
                binding_set_id=r.binding_set_id,
                version=r.version,
                role_set=r.role_set,
                valid_from=r.valid_from,
                valid_to=r.valid_to,
                recorded_at=r.recorded_at,
                superseded_at=r.superseded_at,
                bindings_sha256=r.bindings_sha256,
                origin=r.origin,
                derived_from_revision_id=r.derived_from_revision_id,
                change_note=r.change_note,
                bindings=tuple(by_set.get(r.id, ())),
                foundation_revision_id=r.foundation_revision_id,
                gateway_id=r.gateway_id,
                snapshot_schema=r.snapshot_schema,
                snapshot_sha256=r.snapshot_sha256,
                snapshot_canonical=bytes(r.snapshot_canonical),
            )
            for r in rows
        )

    def binding_sets(self, tenant_id: UUID, site_id: UUID) -> Sequence[BindingSetRevisionRow]:
        return self._run(lambda connection: self._select_binding_sets(connection, tenant_id, site_id))

    @staticmethod
    def _insert_binding_set(
        connection: Connection, tenant_id: UUID, site_id: UUID, row: BindingSetRevisionRow
    ) -> None:
        connection.execute(
            text(
                "INSERT INTO signal_binding_set_revision (id, tenant_id, site_id, binding_set_id, version, "
                "role_set, valid_from, valid_to, recorded_at, superseded_at, bindings_sha256, origin, "
                "derived_from_revision_id, change_note, foundation_revision_id, gateway_id, snapshot_schema, "
                "snapshot_sha256, snapshot_canonical) VALUES (:id, :tenant_id, :site_id, :set_id, "
                ":version, :role_set, :valid_from, :valid_to, :recorded_at, NULL, :sha, :origin, "
                ":derived_from, :note, :foundation_revision_id, :gateway_id, :snapshot_schema, :snapshot_sha256, "
                ":snapshot_canonical)"
            ),
            {
                "id": row.id,
                "tenant_id": tenant_id,
                "site_id": site_id,
                "set_id": row.binding_set_id,
                "version": row.version,
                "role_set": row.role_set,
                "valid_from": row.valid_from,
                "valid_to": row.valid_to,
                "recorded_at": row.recorded_at,
                "sha": row.bindings_sha256,
                "origin": row.origin,
                "derived_from": row.derived_from_revision_id,
                "note": row.change_note,
                "foundation_revision_id": row.foundation_revision_id,
                "gateway_id": row.gateway_id,
                "snapshot_schema": row.snapshot_schema,
                "snapshot_sha256": row.snapshot_sha256,
                "snapshot_canonical": row.snapshot_canonical,
            },
        )
        for b in row.bindings:
            connection.execute(
                text(
                    "INSERT INTO signal_binding_revision (id, tenant_id, site_id, binding_set_revision_id, "
                    "binding_set_id, version, gateway_id, source_id, device_id, signal_id, asset_id, role, "
                    "source_unit, canonical_unit, conversion, valid_from, valid_to, recorded_at, "
                    "superseded_at) VALUES (:id, :tenant_id, :site_id, :set_revision_id, :set_id, :version, "
                    ":gateway_id, :source_id, :device_id, :signal_id, :asset_id, :role, :source_unit, "
                    ":canonical_unit, CAST(:conversion AS jsonb), :valid_from, :valid_to, :recorded_at, NULL)"
                ),
                {
                    "id": b.id,
                    "tenant_id": tenant_id,
                    "site_id": site_id,
                    "set_revision_id": row.id,
                    "set_id": row.binding_set_id,
                    "version": row.version,
                    "gateway_id": b.gateway_id,
                    "source_id": b.source_id,
                    "device_id": b.device_id,
                    "signal_id": b.signal_id,
                    "asset_id": b.asset_id,
                    "role": b.role,
                    "source_unit": b.source_unit,
                    "canonical_unit": b.canonical_unit,
                    "conversion": json.dumps(b.conversion),
                    "valid_from": row.valid_from,
                    "valid_to": row.valid_to,
                    "recorded_at": row.recorded_at,
                },
            )

    def publish_configuration(
        self, tenant_id: UUID, site_id: UUID, planner: ConfigurationPlanner, *,
        connection: Connection | None = None, then: Callable[[ConfigurationPlan], None] | None = None,
    ) -> ConfigurationPlan:
        """One joint Foundation-plus-binding publication under the Site lock.

        Without `connection` it runs in its own transaction. With a caller-owned `connection` (S6-01a, the
        Action adapter's transaction, which already holds the Action row lock) it neither begins nor commits:
        it takes the Site lock on that connection, writes, then calls `then(plan)` on the same connection,
        and the caller's commit or rollback covers everything.
        """

        def work(connection: Connection) -> ConfigurationPlan:
            locked = connection.execute(
                text("SELECT id FROM site WHERE tenant_id = :tenant_id AND id = :site_id FOR UPDATE"),
                {"tenant_id": tenant_id, "site_id": site_id},
            ).first()
            if locked is None:
                raise FoundationSiteNotFound("No such Site in this tenant.")
            plan = planner(
                ConfigurationState(
                    revisions=self._select_revisions(connection, tenant_id, site_id),
                    binding_sets=self._select_binding_sets(connection, tenant_id, site_id),
                )
            )
            scope = {"at": plan.superseded_at, "tenant_id": tenant_id, "site_id": site_id}
            for revision_id in plan.supersede_revision_ids:
                result = connection.execute(
                    text(
                        "UPDATE foundation_revision SET superseded_at = :at WHERE tenant_id = :tenant_id "
                        "AND site_id = :site_id AND id = :id AND superseded_at IS NULL"
                    ),
                    {**scope, "id": revision_id},
                )
                if result.rowcount != 1:
                    raise FoundationOverlap(
                        "A revision this change supersedes is no longer current; nothing was written."
                    )
            for revision in plan.revision_inserts:
                self._insert_revision(connection, tenant_id, site_id, revision)
            for set_id in plan.supersede_binding_set_ids:
                result = connection.execute(
                    text(
                        "UPDATE signal_binding_set_revision SET superseded_at = :at WHERE "
                        "tenant_id = :tenant_id AND site_id = :site_id AND id = :id AND superseded_at IS NULL"
                    ),
                    {**scope, "id": set_id},
                )
                if result.rowcount != 1:
                    raise BindingOverlap(
                        "A binding set revision this change supersedes is no longer current; "
                        "nothing was written."
                    )
            for row in plan.binding_set_inserts:
                self._insert_binding_set(connection, tenant_id, site_id, row)
            self._enqueue_ev_configuration(connection, tenant_id, site_id, plan)
            self._enqueue_mini_configuration(
                connection, tenant_id, site_id,
                [(r.valid_from, r.valid_to) for r in plan.revision_inserts]
                + [(r.valid_from, r.valid_to) for r in plan.binding_set_inserts],
                plan.superseded_at)
            if then is not None:
                then(plan)
            return plan

        return self._run(work, write=True, connection=connection)

    @staticmethod
    def _enqueue_mini_configuration(
        connection: Connection, tenant_id: UUID, site_id: UUID,
        changed: Sequence[tuple[datetime, datetime | None]], at: datetime,
    ) -> None:
        """W4-02 closure 2 / closure 4 S2: on a MINIGRID Site, every inserted Foundation or binding-set revision
        enqueues the mini-depth hours of its `[valid_from, valid_to)` within the configured retention, through the
        SQL `mini_enqueue_configuration` on this publishing connection after the publish and before commit, so a
        failed enqueue rolls the publication back. The SQL function itself enqueues nothing for another Site type."""
        if not changed:
            return
        site_type = connection.execute(
            text("SELECT site_type FROM site WHERE tenant_id = :tenant_id AND id = :site_id"),
            {"tenant_id": tenant_id, "site_id": site_id},
        ).scalar_one()
        if site_type != "MINIGRID":
            return
        for valid_from, valid_to in changed:
            connection.execute(
                text("SELECT mini_enqueue_configuration(:tenant_id, :site_id, :valid_from, :valid_to, :at)"),
                {"tenant_id": tenant_id, "site_id": site_id, "valid_from": valid_from, "valid_to": valid_to,
                 "at": at},
            )

    @staticmethod
    def _enqueue_ev_configuration(
        connection: Connection, tenant_id: UUID, site_id: UUID, plan: ConfigurationPlan
    ) -> None:
        """W2-06 q3 P7 as amended by r5 R5-2: on an EV_CHARGING Site, every inserted Foundation or binding-set
        revision (including an equal-SHA split, whose new revision ID still replaces the selected identity) dirties
        the EV assessment over its `[valid_from, valid_to)` through the SQL `ev_enqueue_configuration`, on this
        publishing connection, so publication and enqueue commit or roll back together. No analytics import."""
        if not (bool(plan.revision_inserts) or bool(plan.binding_set_inserts)):
            return
        site_type = connection.execute(
            text("SELECT site_type FROM site WHERE tenant_id = :tenant_id AND id = :site_id"),
            {"tenant_id": tenant_id, "site_id": site_id},
        ).scalar_one()
        if site_type != "EV_CHARGING":
            return
        changed = [(r.valid_from, r.valid_to) for r in plan.revision_inserts] + [
            (r.valid_from, r.valid_to) for r in plan.binding_set_inserts
        ]
        for valid_from, valid_to in changed:
            connection.execute(
                text("SELECT ev_enqueue_configuration(:tenant_id, :site_id, :valid_from, :valid_to, :at)"),
                {"tenant_id": tenant_id, "site_id": site_id, "valid_from": valid_from, "valid_to": valid_to,
                 "at": plan.superseded_at},
            )
