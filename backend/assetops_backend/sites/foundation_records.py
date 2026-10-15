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


class BindingOverlap(FoundationStoreError):
    """A write would overlap a currently recorded binding set or channel (S1-02)."""


@dataclass(frozen=True)
class BindingRow:
    """One `signal_binding_revision`: a device channel bound to a role (S1-02).

    It carries no interval of its own in the domain: every row of a binding
    set revision shares that revision's valid and recorded periods, and the
    adapter writes them onto the row so the database can refuse an
    overlapping current channel.
    """

    id: UUID
    gateway_id: UUID
    source_id: UUID
    device_id: str
    signal_id: str
    asset_id: UUID | None
    role: str
    source_unit: str
    canonical_unit: str
    conversion: dict[str, Any]


@dataclass(frozen=True)
class BindingSetRevisionRow:
    """One time-valid version of a Site's signal binding set (S1-02)."""

    id: UUID
    binding_set_id: UUID
    version: int
    role_set: str
    valid_from: datetime
    valid_to: datetime | None
    recorded_at: datetime
    superseded_at: datetime | None
    bindings_sha256: str
    origin: str
    derived_from_revision_id: UUID | None
    change_note: str | None
    bindings: tuple[BindingRow, ...]
    #: The one currently recorded Foundation revision whose valid period
    #: contains this binding period when it was published: binding periods
    #: are aligned to Foundation periods (decision Q5), so each binding set
    #: revision is one acquisition snapshot.
    foundation_revision_id: UUID
    gateway_id: UUID
    #: The pinned snapshot: serializer/schema version and the SHA-256 of the
    #: canonical bytes, persisted in the publishing transaction (decision Q6).
    snapshot_schema: str
    snapshot_sha256: str
    #: The exact canonical bytes that `snapshot_sha256` hashes, kept from the
    #: publishing transaction (S1-02 fix round, review M1). A download serves
    #: these bytes; it never rebuilds them from registration rows, whose
    #: identity fields (site code, gateway external ID, mode, source external
    #: IDs) are not immutable.
    snapshot_canonical: bytes = b""


@dataclass(frozen=True)
class ConfigurationState:
    """Every Foundation and binding set revision of the locked Site."""

    revisions: tuple[RevisionRow, ...]
    binding_sets: tuple[BindingSetRevisionRow, ...]


@dataclass(frozen=True)
class ConfigurationPlan:
    """One joint Foundation-plus-binding publication, written atomically.

    Foundation rows are superseded and inserted first, then binding set
    revisions, in one transaction under the Site lock. Either part may be
    empty; a binding-only change still validates against the Foundation it
    reads under the same lock.
    """

    superseded_at: datetime
    supersede_revision_ids: tuple[UUID, ...]
    revision_inserts: tuple[RevisionRow, ...]
    supersede_binding_set_ids: tuple[UUID, ...]
    binding_set_inserts: tuple[BindingSetRevisionRow, ...]


ConfigurationPlanner = Callable[[ConfigurationState], ConfigurationPlan]


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

    def binding_sets(self, tenant_id: UUID, site_id: UUID) -> Sequence[BindingSetRevisionRow]: ...

    def publish_configuration(
        self, tenant_id: UUID, site_id: UUID, planner: ConfigurationPlanner, *,
        connection: Any = None, then: Callable[[ConfigurationPlan], None] | None = None,
    ) -> ConfigurationPlan:
        """Without `connection`, its own transaction. With a caller-owned `connection` (S6-01a), no begin
        or commit of its own; `then(plan)` runs on that connection after the writes."""
        ...
