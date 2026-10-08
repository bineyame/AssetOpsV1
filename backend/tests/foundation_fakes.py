"""An in-memory `FoundationStore` for the default (no-database) suite.

It implements the port's contract, including the rules the PostgreSQL
schema enforces that the cutover and publish logic rely on: tenant scoping on
every call, one Site code per tenant, and no overlapping *currently recorded*
validity for a Site (the GiST exclusion constraint). Writes are all-or-nothing:
a publish that would overlap, or a planner that raises, leaves no change.
The database-specific guarantees themselves (constraint, triggers, composite
foreign keys, migrations) are tested against PostgreSQL in
`test_s1_foundation_postgres.py`.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from typing import Sequence
from uuid import UUID, uuid4

from assetops_backend.sites.foundation_records import (
    FoundationOverlap,
    FoundationSiteCodeTaken,
    FoundationSiteNotFound,
    FoundationStoreUnavailable,
    ImportPlan,
    PublishPlan,
    PublishPlanner,
    Registrations,
    RevisionRow,
    StoredSite,
    TenantNotFound,
    TenantRef,
)

_END = datetime.max.replace(tzinfo=timezone.utc)


class InMemoryFoundationStore:
    def __init__(self, *, unavailable: bool = False) -> None:
        self.unavailable = unavailable
        self.tenants: dict[str, TenantRef] = {}
        self.sites: list[StoredSite] = []
        self.registered: dict[UUID, Registrations] = {}
        self.rows: dict[UUID, list[RevisionRow]] = {}

    def _check(self) -> None:
        if self.unavailable:
            raise FoundationStoreUnavailable("The product Foundation store could not be reached.")

    def resolve_tenant(self, slug: str) -> TenantRef:
        self._check()
        if slug not in self.tenants:
            raise TenantNotFound(f"No tenant {slug!r} is registered.")
        return self.tenants[slug]

    def ensure_tenant(self, slug: str, name: str, *, now: datetime) -> TenantRef:
        self._check()
        return self.tenants.setdefault(slug, TenantRef(id=uuid4(), slug=slug, name=name))

    def find_site(self, tenant_id: UUID, site_code: str) -> StoredSite | None:
        self._check()
        return next(
            (s for s in self.sites if s.tenant_id == tenant_id and s.site_code.lower() == site_code.lower()),
            None,
        )

    def find_site_by_id(self, tenant_id: UUID, site_id: UUID) -> StoredSite | None:
        self._check()
        return next((s for s in self.sites if s.tenant_id == tenant_id and s.id == site_id), None)

    def list_sites(self, tenant_id: UUID) -> Sequence[StoredSite]:
        self._check()
        return tuple(sorted((s for s in self.sites if s.tenant_id == tenant_id), key=lambda s: s.site_code))

    def registrations(self, tenant_id: UUID, site_id: UUID) -> Registrations:
        self._check()
        if self.find_site_by_id(tenant_id, site_id) is None:
            return Registrations((), (), ())
        return self.registered[site_id]

    def revisions(self, tenant_id: UUID, site_id: UUID) -> Sequence[RevisionRow]:
        self._check()
        if self.find_site_by_id(tenant_id, site_id) is None:
            return ()
        return tuple(sorted(self.rows[site_id], key=lambda r: r.version))

    def insert_import(self, tenant_id: UUID, plan: ImportPlan) -> None:
        self._check()
        if plan.site.tenant_id != tenant_id:
            raise ValueError("plan belongs to another tenant")
        if self.find_site(tenant_id, plan.site.site_code) is not None:
            raise FoundationSiteCodeTaken("Another Site in this tenant already holds that code.")
        self.sites.append(plan.site)
        self.registered[plan.site.id] = Registrations(plan.assets, (plan.gateway,), plan.sources)
        self.rows[plan.site.id] = [plan.revision]

    def publish(self, tenant_id: UUID, site_id: UUID, planner: PublishPlanner) -> PublishPlan:
        self._check()
        if self.find_site_by_id(tenant_id, site_id) is None:
            raise FoundationSiteNotFound("No such Site in this tenant.")
        before = list(self.rows[site_id])
        plan = planner(tuple(sorted(before, key=lambda r: r.version)))
        after: list[RevisionRow] = []
        for row in before:
            if row.id in plan.supersede_ids:
                if row.superseded_at is not None:
                    raise FoundationOverlap("A revision this change supersedes is no longer current.")
                row = replace(row, superseded_at=plan.superseded_at)
            after.append(row)
        after.extend(plan.inserts)
        current = [r for r in after if r.superseded_at is None]
        for i, a in enumerate(current):
            for b in current[i + 1:]:
                if a.valid_from < (b.valid_to or _END) and b.valid_from < (a.valid_to or _END):
                    raise FoundationOverlap("The change would overlap a currently recorded period.")
        self.rows[site_id] = after
        return plan
