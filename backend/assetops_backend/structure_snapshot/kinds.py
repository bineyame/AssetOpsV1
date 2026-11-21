"""3B7a unit 2 (spec §3.4; D-3B7A.12): the record kinds a Site holds.

The same call 4b's `CommercialLeafSource._month` makes for `held`, so the kinds frozen with a Site row are the ones
the build judged. The served read compares them with the kinds held now (a freshness check; no value is read).
"""
from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from assetops_backend.commercial.store import CommercialStore


class HeldKinds(Protocol):
    def of(self, tenant_id: UUID, site_id: UUID, known_at: datetime | None = None) -> tuple[str, ...]:
        """The sorted record kinds the Site holds (at `known_at`, else now)."""


class StoreHeldKinds:
    def __init__(self, store: CommercialStore) -> None:
        self._store = store

    def of(self, tenant_id: UUID, site_id: UUID, known_at: datetime | None = None) -> tuple[str, ...]:
        return tuple(sorted({r.kind for r in self._store.latest_revisions(tenant_id, site_id=site_id,
                                                                          known_at=known_at)}))


__all__ = ["HeldKinds", "StoreHeldKinds"]
