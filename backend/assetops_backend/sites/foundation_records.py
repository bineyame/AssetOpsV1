"""The persisted Foundation's records, errors and storage port (S1-01).

These are the product's own rows for an imported Site: tenant, Site identity,
the import registration that names the source document it was migrated from,
assets, the pending gateway and its sources, and time-valid Foundation
revisions. Nothing here names a storage technology; the PostgreSQL adapter in
`sites/adapters/` implements `FoundationStore` and is composed only in
`sites/composition.py`.

Every store method takes the resolved tenant UUID. The tenant is never read
from a client: `foundation_api` resolves the configured development tenant at
the request boundary and passes it down, so a lookup by Site code or by row
UUID cannot reach another tenant's rows.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Protocol, Sequence
from uuid import UUID


class FoundationStoreError(Exception):
    """Base class for the Foundation store's error vocabulary."""


class FoundationStoreUnavailable(FoundationStoreError):
    """The store could not be reached, or no database is configured."""


class TenantNotFound(FoundationStoreError):
    """No tenant with that slug is registered."""


class FoundationSiteNotFound(FoundationStoreError):
    """No Site with that code (or UUID) exists in the resolved tenant."""


class FoundationSiteCodeTaken(FoundationStoreError):
    """Another Site in this tenant already holds the code."""


class FoundationOverlap(FoundationStoreError):
    """A write would overlap currently recorded Foundation validity."""


@dataclass(frozen=True)
class TenantRef:
    id: UUID
    slug: str
    name: str


@dataclass(frozen=True)
class ImportRecord:
    """Which document a Site was migrated from, byte for byte."""

    id: UUID
    source_path: str
    source_sha256: str
    source_format: str
    imported_at: datetime


@dataclass(frozen=True)
class StoredSite:
    id: UUID
    tenant_id: UUID
    site_code: str
    name: str
    site_type: str
    timezone: str
    lifecycle: str
    country: str | None
    locality: str | None
    origin: str
    proposed_source_mode: str
    template_id: str | None
    template_version: int | None
    created_at: datetime
    import_record: ImportRecord | None


@dataclass(frozen=True)
class AssetRow:
    id: UUID
    asset_code: str
    asset_type: str
    attributes: dict[str, Any]


@dataclass(frozen=True)
class GatewayRow:
    id: UUID
    gateway_external_id: str
    mode: str
    credential_ref: str | None
    registered_at: datetime
    disabled_at: datetime | None


@dataclass(frozen=True)
class SourceRow:
    id: UUID
    gateway_id: UUID
    source_external_id: str
    device_kind: str
    asset_id: UUID
    registered_at: datetime
    disabled_at: datetime | None


@dataclass(frozen=True)
class RevisionRow:
    id: UUID
    version: int
    valid_from: datetime
    valid_to: datetime | None
    recorded_at: datetime
    superseded_at: datetime | None
    schema_version: int
    content: dict[str, Any]
    content_sha256: str
    origin: str
    derived_from_revision_id: UUID | None
    change_note: str | None


@dataclass(frozen=True)
class Registrations:
    assets: tuple[AssetRow, ...]
    gateways: tuple[GatewayRow, ...]
    sources: tuple[SourceRow, ...]


@dataclass(frozen=True)
class ImportPlan:
    """Every row one import inserts, in one transaction."""

    site: StoredSite
    assets: tuple[AssetRow, ...]
    gateway: GatewayRow
    sources: tuple[SourceRow, ...]
    revision: RevisionRow


@dataclass(frozen=True)
class PublishPlan:
    """The rows one publish supersedes and inserts, under the Site lock."""

    supersede_ids: tuple[UUID, ...]
    superseded_at: datetime
    inserts: tuple[RevisionRow, ...]


#: Given every revision of the locked Site (current and superseded), return
#: what to write. Raising aborts the transaction with nothing written.
PublishPlanner = Callable[[Sequence[RevisionRow]], PublishPlan]


class FoundationStore(Protocol):
    """Tenant-scoped persistence for imported Sites and their Foundation."""

    def resolve_tenant(self, slug: str) -> TenantRef: ...

    def ensure_tenant(self, slug: str, name: str, *, now: datetime) -> TenantRef: ...

    def find_site(self, tenant_id: UUID, site_code: str) -> StoredSite | None: ...

    def find_site_by_id(self, tenant_id: UUID, site_id: UUID) -> StoredSite | None: ...

    def list_sites(self, tenant_id: UUID) -> Sequence[StoredSite]: ...

    def registrations(self, tenant_id: UUID, site_id: UUID) -> Registrations: ...

    def revisions(self, tenant_id: UUID, site_id: UUID) -> Sequence[RevisionRow]: ...

    def insert_import(self, tenant_id: UUID, plan: ImportPlan) -> None: ...

    def publish(
        self, tenant_id: UUID, site_id: UUID, planner: PublishPlanner
    ) -> PublishPlan: ...
