"""The `SiteRepository` over both Site stores.

Shipped Sites and user-created Sites share one globally unique `site_id`
space. This adapter merges the two stores into that one space, and the way it
merges them is the point: there is no overlay and no precedence. The same
`site_id` present in both stores is refused loudly at load rather than
resolving to either document, because an identity that resolves to different
content depending on store state cannot anchor the history that every later
run, envelope, evidence record, and analytic is keyed on.

Writes go to the user store only. The shipped store has no write path to
delegate to, which is what makes "shipped configuration is read-only at
runtime" structural rather than a convention.

Origin is not encoded into identity. A user `site_id` is not prefixed and
nothing here can tell which store a Site came from by reading its identity;
that is what the `origin` field on the record is for.
"""

from __future__ import annotations

from typing import Protocol, Sequence

from assetops_backend.sites.identity import site_id_key, validate_site_id
from assetops_backend.sites.models import SiteRecord
from assetops_backend.sites.ports import (
    SiteIdentityConflict,
    SiteNotFound,
)


class ReadableSiteStore(Protocol):
    """One half of the identity space. Adapter-internal, never a domain port."""

    @property
    def store_name(self) -> str: ...

    def list_sites(self) -> Sequence[SiteRecord]: ...


class WritableSiteStore(ReadableSiteStore, Protocol):
    def create_site(self, record: SiteRecord) -> SiteRecord: ...


class CompositeSiteRepository:
    """A `SiteRepository` backed by a read-only store and a writable store."""

    def __init__(
        self, shipped: ReadableSiteStore, user: WritableSiteStore
    ) -> None:
        self._shipped = shipped
        self._user = user

    def list_sites(self) -> tuple[SiteRecord, ...]:
        by_identity: dict[str, tuple[str, SiteRecord]] = {}

        for store in (self._shipped, self._user):
            for record in store.list_sites():
                key = site_id_key(record.site_id)
                previous = by_identity.get(key)
                if previous is not None:
                    previous_store, previous_record = previous
                    raise SiteIdentityConflict(
                        f"Site ID {record.site_id!r} is declared in the "
                        f"{previous_store} store as "
                        f"{previous_record.site_id!r} and in the "
                        f"{store.store_name} store. Site identity is globally "
                        "unique across both stores and is compared without "
                        "regard to case; there is no precedence between them, "
                        "so neither document is used."
                    )
                by_identity[key] = (store.store_name, record)

        return tuple(
            record for _, record in sorted(
                by_identity.values(), key=lambda entry: entry[1].site_id
            )
        )

    def get_site(self, site_id: str) -> SiteRecord:
        validate_site_id(site_id)
        key = site_id_key(site_id)

        for record in self.list_sites():
            if site_id_key(record.site_id) == key:
                return record

        raise SiteNotFound(f"No site with site ID {site_id!r} is configured.")

    def create_site(self, record: SiteRecord) -> SiteRecord:
        validate_site_id(record.site_id)
        key = site_id_key(record.site_id)

        # Both stores are checked before the write, so an identity that a
        # shipped document already holds is refused rather than shadowed.
        for existing in self.list_sites():
            if site_id_key(existing.site_id) == key:
                raise SiteIdentityConflict(
                    f"Site ID {record.site_id!r} is already in use by "
                    f"{existing.site_id!r}."
                )

        return self._user.create_site(record)
