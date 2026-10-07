"""The S1-01 Foundation-only cutover at composition (D-2026-10-07).

Two pieces, both tenant-scoped through the configured development tenant:

* `ProductSiteDirectory` is the product read router behind `GET /api/sites`
  and `GET /api/sites/{id}`. A code registered as imported in the Postgres
  Foundation store is served from Postgres and listed once; its matching
  legacy YAML row is suppressed only when that row is the registered source
  document with the registered digest. Any other same-code row is a
  conflict, not a store precedence. Unregistered codes keep the legacy YAML
  behavior.

* `LegacySiteGate` is the `SiteRepository` the legacy file-backed surfaces
  (Evidence, Overview, dispatch/Performance, ingestion/Commit and Lab) are
  given. For an imported code it refuses with `SiteAwaitingMigration` rather
  than serving YAML state beside a newer Postgres Foundation; it refuses to
  create a Site with an imported code; and it fails closed if the Foundation
  store cannot be asked.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

from assetops_backend.sites.foundation_content import record_at
from assetops_backend.sites.foundation_records import (
    FoundationStoreError,
    StoredSite,
    TenantRef,
)
from assetops_backend.sites.foundation_service import (
    FoundationService,
    LegacyDocument,
    revision_at,
)
from assetops_backend.sites.identity import site_id_key, validate_site_id
from assetops_backend.sites.models import SiteRecord
from assetops_backend.sites.ports import (
    SiteAwaitingMigration,
    SiteIdentityConflict,
    SiteNotFound,
    SiteRepository,
    SiteStoreUnavailable,
)


class ImportedSiteRegistry:
    """Which codes the configured tenant has imported into Postgres.

    `service` is None only in a legacy-only test composition (a caller that
    injected its own Site repository and no Foundation store): no code is
    imported there. The product composition always supplies a service, and a
    service that cannot be reached raises rather than answering "not imported".
    """

    def __init__(self, service: FoundationService | None) -> None:
        self._service = service

    @property
    def service(self) -> FoundationService | None:
        return self._service

    def tenant(self) -> TenantRef | None:
        if self._service is None:
            return None
        try:
            return self._service.tenant()
        except FoundationStoreError as error:
            raise SiteStoreUnavailable(
                f"The product Foundation store could not be asked which Sites are imported: {error}"
            ) from error

    def imported_sites(self) -> tuple[StoredSite, ...]:
        if self._service is None:
            return ()
        tenant = self.tenant()
        try:
            return tuple(
                site
                for site in self._service.store.list_sites(tenant.id)
                if site.import_record is not None
            )
        except FoundationStoreError as error:
            raise SiteStoreUnavailable(str(error)) from error

    def imported(self, site_code: str) -> StoredSite | None:
        key = site_id_key(site_code)
        for site in self.imported_sites():
            if site_id_key(site.site_code) == key:
                return site
        return None


def _awaiting(site_code: str) -> SiteAwaitingMigration:
    return SiteAwaitingMigration(
        f"Site {site_code} has moved to the persisted Foundation store. This legacy "
        "file-backed surface is awaiting evidence migration and does not serve or "
        "change its state."
    )


class LegacySiteGate:
    """`SiteRepository` over the legacy YAML repository, minus imported codes."""

    def __init__(self, legacy: SiteRepository, registry: ImportedSiteRegistry) -> None:
        self._legacy = legacy
        self._registry = registry

    def is_imported(self, site_code: str) -> bool:
        return self._registry.imported(site_code) is not None

    def refuse_if_imported(self, site_code: str) -> None:
        if self.is_imported(site_code):
            raise _awaiting(site_code)

    def list_sites(self) -> Sequence[SiteRecord]:
        imported = {site_id_key(site.site_code) for site in self._registry.imported_sites()}
        return tuple(
            record for record in self._legacy.list_sites() if site_id_key(record.site_id) not in imported
        )

    def get_site(self, site_id: str) -> SiteRecord:
        validate_site_id(site_id)
        self.refuse_if_imported(site_id)
        return self._legacy.get_site(site_id)

    def create_site(self, record: SiteRecord) -> SiteRecord:
        validate_site_id(record.site_id)
        if self.is_imported(record.site_id):
            raise SiteIdentityConflict(
                f"Site ID {record.site_id!r} is registered in the product Foundation "
                "store; a legacy Site with that identity cannot be created."
            )
        return self._legacy.create_site(record)


@dataclass(frozen=True)
class ProductSiteEntry:
    """One Site in the product index: from Postgres, or from the legacy store."""

    store: str  # "POSTGRES" | "LEGACY_FILE"
    record: SiteRecord | None
    stored: StoredSite | None = None
    revision_id: str | None = None


class ProductSiteDirectory:
    """The tenant-scoped product read router for the Sites index and detail."""

    def __init__(
        self,
        legacy: SiteRepository,
        registry: ImportedSiteRegistry,
        legacy_documents: Callable[[], Sequence[LegacyDocument]],
    ) -> None:
        self._legacy = legacy
        self._registry = registry
        self._legacy_documents = legacy_documents

    def _check_collisions(self, imported: Sequence[StoredSite]) -> None:
        if not imported:
            return
        documents = self._legacy_documents()
        for site in imported:
            record = site.import_record
            for document in documents:
                if site_id_key(document.site_code) != site_id_key(site.site_code):
                    continue
                if document.path != record.source_path:
                    raise SiteIdentityConflict(
                        f"Site code {site.site_code!r} is imported from {record.source_path} "
                        f"but is also declared by {document.path}. A code collision outside "
                        "the registered import is an error, not a store precedence."
                    )
                if document.sha256 != record.source_sha256:
                    raise SiteIdentityConflict(
                        f"{record.source_path} has changed since Site {site.site_code} was "
                        "imported. The migration needs explicit reconciliation; neither "
                        "document is served."
                    )

    def _current(self, site: StoredSite) -> ProductSiteEntry:
        service = self._registry.service
        tenant = self._registry.tenant()
        try:
            revisions = service.store.revisions(tenant.id, site.id)
        except FoundationStoreError as error:
            raise SiteStoreUnavailable(str(error)) from error
        now = service.now()
        revision = revision_at(revisions, now, now)
        if revision is None:
            return ProductSiteEntry("POSTGRES", None, site, None)
        return ProductSiteEntry("POSTGRES", record_at(site, revision), site, str(revision.id))

    def list_sites(self) -> tuple[ProductSiteEntry, ...]:
        imported = self._registry.imported_sites()
        self._check_collisions(imported)
        keys = {site_id_key(site.site_code) for site in imported}
        entries = [self._current(site) for site in imported]
        entries.extend(
            ProductSiteEntry("LEGACY_FILE", record)
            for record in self._legacy.list_sites()
            if site_id_key(record.site_id) not in keys
        )
        return tuple(
            sorted(entries, key=lambda entry: (entry.stored.site_code if entry.stored else entry.record.site_id))
        )

    def get_site(self, site_id: str) -> ProductSiteEntry:
        validate_site_id(site_id)
        site = self._registry.imported(site_id)
        if site is None:
            return ProductSiteEntry("LEGACY_FILE", self._legacy.get_site(site_id))
        self._check_collisions((site,))
        entry = self._current(site)
        if entry.record is None:
            raise SiteNotFound(f"Site {site.site_code} has no Foundation revision effective now.")
        return entry
