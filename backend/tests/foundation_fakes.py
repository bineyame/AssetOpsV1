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
    BindingOverlap,
    BindingSetRevisionRow,
    ConfigurationPlan,
    ConfigurationPlanner,
    ConfigurationState,
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
        self.sets: dict[UUID, list[BindingSetRevisionRow]] = {}

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

    # --- signal bindings (S1-02) ---------------------------------------------

    def binding_sets(self, tenant_id: UUID, site_id: UUID) -> Sequence[BindingSetRevisionRow]:
        self._check()
        if self.find_site_by_id(tenant_id, site_id) is None:
            return ()
        return tuple(sorted(self.sets.get(site_id, []), key=lambda r: r.version))

    def publish_configuration(
        self, tenant_id: UUID, site_id: UUID, planner: ConfigurationPlanner
    ) -> ConfigurationPlan:
        """All-or-nothing, with the schema's exclusion and same-Site rules."""
        self._check()
        if self.find_site_by_id(tenant_id, site_id) is None:
            raise FoundationSiteNotFound("No such Site in this tenant.")
        rows_before = list(self.rows[site_id])
        sets_before = list(self.sets.get(site_id, []))
        plan = planner(
            ConfigurationState(
                revisions=tuple(sorted(rows_before, key=lambda r: r.version)),
                binding_sets=tuple(sorted(sets_before, key=lambda r: r.version)),
            )
        )
        rows_after = _supersede(rows_before, plan.supersede_revision_ids, plan.superseded_at, FoundationOverlap)
        rows_after.extend(plan.revision_inserts)
        _refuse_overlap([r for r in rows_after if r.superseded_at is None], FoundationOverlap)
        sets_after = _supersede(sets_before, plan.supersede_binding_set_ids, plan.superseded_at, BindingOverlap)
        sets_after.extend(plan.binding_set_inserts)
        current = [s for s in sets_after if s.superseded_at is None]
        # Migration 0003: a set revision lies inside one current Foundation revision.
        current_rows = {r.id: r for r in rows_after if r.superseded_at is None}
        for s in plan.binding_set_inserts:
            anchor = current_rows.get(s.foundation_revision_id)
            if anchor is None or s.valid_from < anchor.valid_from or (
                anchor.valid_to is not None and (s.valid_to is None or s.valid_to > anchor.valid_to)
            ):
                raise ValueError("binding_set_within_foundation: not inside a current Foundation revision")
        for role_set in {s.role_set for s in current}:
            _refuse_overlap([s for s in current if s.role_set == role_set], BindingOverlap)
        regs = self.registered[site_id]
        assets = {a.id for a in regs.assets}
        sources = {(s.gateway_id, s.id, s.source_external_id) for s in regs.sources}
        channels: dict[tuple[UUID, str], list[BindingSetRevisionRow]] = {}
        for s in current:
            for b in s.bindings:
                if (b.gateway_id, b.source_id, b.device_id) not in sources:
                    raise ValueError("binding_source_of_gateway: source is not this gateway's device")
                if b.asset_id is not None and b.asset_id not in assets:
                    raise ValueError("binding_asset_same_site: asset is not this Site's")
                channels.setdefault((b.source_id, b.signal_id), []).append(s)
        for owners in channels.values():
            _refuse_overlap(owners, BindingOverlap)
        self.rows[site_id] = rows_after
        self.sets[site_id] = sets_after
        return plan


def _supersede(rows, ids, at, error):
    out = []
    for row in rows:
        if row.id in ids:
            if row.superseded_at is not None:
                raise error("A row this change supersedes is no longer current.")
            row = replace(row, superseded_at=at)
        out.append(row)
    return out


def _refuse_overlap(current, error) -> None:
    for i, a in enumerate(current):
        for b in current[i + 1:]:
            if a.valid_from < (b.valid_to or _END) and b.valid_from < (a.valid_to or _END):
                raise error("The change would overlap a currently recorded period.")
