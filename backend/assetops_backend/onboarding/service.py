"""ON1 (spec §3.1; D-ON1.1, D-ON1.6, D-ON1.10, D-ON1.15): check an operator's onboarding file against the stores and
the switches, then apply it.

`check` writes nothing and answers the `Plan`; `apply` compares the confirmed roles digest, runs `check` afresh and
executes only its `create` and `grant` entries, in this order: the tenant, its Sites (through the existing Site
import), the people's accounts (the executive's role with the account), the other roles (by `service:onboarding`),
the pseudonym key. A refusal mid-way stops; the steps done stay, and a rerun's `check` marks them `keep`. A real file
passes the RC4 steps and is then refused before any write until `ON1b` (step 3a). `wrote` tells the command whether
the last `apply` reached a write (exit 3 rather than 2).
"""
from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Protocol
from uuid import UUID

from assetops_backend.accounts.model import EXECUTIVE
from assetops_backend.accounts.service import AccountService
from assetops_backend.onboarding.operator_file import (OnboardRefused, OperatorFile, PersonEntry, roles_digest,
                                                      site_source)
from assetops_backend.sites.foundation_records import FoundationStore, TenantNotFound, TenantRef
from assetops_backend.sites.foundation_service import ImportConflict, import_site


class KeyFiles(Protocol):
    def directory_ok(self) -> bool:
        """The key directory exists, is a directory and is readable by its owner only."""

    def state(self, tenant_id: UUID) -> str:
        """`MISSING`, `PRESENT` or `ERASED`; no key byte is read."""

    def create(self, tenant_id: UUID) -> None: ...


@dataclass
class _Role:
    index: int
    role: str
    site: str | None
    action: str


@dataclass
class Plan:
    slug: str
    tenant_id: UUID | None
    tenant: str
    sites: list[tuple[str, str]] = field(default_factory=list)  # (code, action)
    people: list[tuple[PersonEntry, str]] = field(default_factory=list)
    roles: list[_Role] = field(default_factory=list)
    key: str = "create"
    roles_digest: str = ""

    def as_json(self) -> dict:
        """Spec §3.1: the plan as printed. No email, name or password."""
        return {
            "tenant": {"slug": self.slug, "id": None if self.tenant_id is None else str(self.tenant_id),
                       "action": self.tenant},
            "sites": [{"code": code, "action": action} for code, action in self.sites],
            "people": [{"index": p.index, "action": action, "roles": [role for role, _ in p.roles]}
                       for p, action in self.people],
            "roles": [{"index": r.index, "role": r.role, "site": r.site, "action": r.action} for r in self.roles],
            "key": self.key,
            "roles_digest": self.roles_digest,
        }


class OperatorOnboarding:
    def __init__(self, foundation: FoundationStore, accounts: AccountService, keys: KeyFiles, *,
                 clock: Callable[[], datetime], real_data: bool, served_slug: str) -> None:
        self._foundation = foundation
        self._accounts = accounts
        self._keys = keys
        self._clock = clock
        self._real_data = real_data
        self._served_slug = served_slug
        self.wrote = False

    def _tenant(self, slug: str) -> TenantRef | None:
        try:
            return self._foundation.resolve_tenant(slug)
        except TenantNotFound:
            return None

    def check(self, f: OperatorFile) -> Plan:
        # 0. the key directory
        if not self._keys.directory_ok():
            raise OnboardRefused("ONBOARD_KEY_DIR")
        # 1. RC4 (D-ON1.6): the file's data and the real-data switch agree
        if f.real != self._real_data:
            raise OnboardRefused("ONBOARD_DATA_MISMATCH", "data")
        # 2. the server serves this tenant
        if self._served_slug != f.slug:
            raise OnboardRefused("ONBOARD_TENANT_NOT_SERVED", "operator.slug")
        if f.real:
            # 3. one operator per operator database
            if tuple(self._foundation.tenant_slugs()) not in ((), (f.slug,)):
                raise OnboardRefused("ONBOARD_DATABASE_NOT_EMPTY")
            # 3a. D-ON1.15: a real file waits for the executive's approval (ON1b), before any store read or write
            raise OnboardRefused("ONBOARD_REAL_AWAITS_APPROVAL", "data")
        # 4. the tenant and its key
        tenant = self._tenant(f.slug)
        if tenant is not None and tenant.name != f.operator.name:
            raise OnboardRefused("ONBOARD_TENANT_DIFFERS", "operator.name")
        plan = Plan(f.slug, None if tenant is None else tenant.id, "create" if tenant is None else "keep",
                    roles_digest=roles_digest(f))
        if tenant is not None:
            state = self._keys.state(tenant.id)
            if state == "ERASED":
                raise OnboardRefused("ONBOARD_KEY_ERASED")
            plan.key = "keep" if state == "PRESENT" else "create"
        # 5. the Sites
        site_ids: dict[str, UUID] = {}
        for site in f.sites:
            found = None if tenant is None else self._foundation.find_site(tenant.id, site.code)
            if found is None:
                plan.sites.append((site.code, "create"))
                continue
            source = site_source(f, site)
            registered = found.import_record
            if registered is None or registered.source_path != source.path or registered.source_sha256 != source.sha256:
                raise OnboardRefused("ONBOARD_SITE_CHANGED", f"sites[{site.index}]")
            site_ids[site.code] = found.id
            plan.sites.append((site.code, "keep"))
        # 6. the people, and the executive (R10)
        held: dict[int, frozenset] = {}
        for person in f.people:
            found = self._accounts.onboard_person(person.email)
            if found is None:
                plan.people.append((person, "create"))
                continue
            if found.tenant_slug != f.slug:
                raise OnboardRefused("ONBOARD_EMAIL_TAKEN", f"people[{person.index}]")
            if found.display_name != person.name or not found.active:
                raise OnboardRefused("ONBOARD_PERSON_DIFFERS", f"people[{person.index}]")
            held[person.index] = found.roles
            plan.people.append((person, "keep"))
        executive = next(p for p in f.people if p.executive)
        current = self._accounts.executive_of(f.slug)
        if current is not None:
            found = self._accounts.onboard_person(executive.email)
            if found is None or found.person_id != current:
                raise OnboardRefused("ONBOARD_EXECUTIVE_DIFFERS", f"people[{executive.index}]")
        # 7. the other roles
        closed: str | None = None
        for person in f.people:
            for role, site in person.roles:
                if role == EXECUTIVE:
                    continue
                site_id = None if site is None else site_ids.get(site)
                kept = person.index in held and (role, site_id) in held[person.index] and (
                    site is None or site_id is not None)
                plan.roles.append(_Role(person.index, role, site, "keep" if kept else "grant"))
                if not kept and closed is None:
                    closed = f"people[{person.index}]"
        if closed is not None and not self._accounts.onboarding_may_grant(f.slug):
            raise OnboardRefused("ONBOARDING_CLOSED", closed)
        return plan

    @property
    def foundation(self):
        return self._foundation

    def apply(self, f: OperatorFile, *, confirmed_digest: str) -> Plan:
        self.wrote = False
        if confirmed_digest != roles_digest(f):
            raise OnboardRefused("ONBOARD_DIGEST_DIFFERS")
        plan = self.check(f)
        if plan.tenant == "create":
            self.wrote = True
            self._foundation.ensure_tenant(f.slug, f.operator.name, now=self._clock())
        tenant = self._foundation.resolve_tenant(f.slug)
        plan.tenant_id = tenant.id
        for site, (code, action) in zip(f.sites, plan.sites):
            if action != "create":
                continue
            self.wrote = True
            refused = False
            try:
                import_site(self._foundation, tenant_slug=f.slug, configured_tenant_slug=f.slug,
                            source=site_source(f, site), legacy_documents=(), clock=self._clock)
            except ImportConflict:
                refused = True
            if refused:  # raised outside the handler: the conflict's message quotes paths and digests
                raise OnboardRefused("ONBOARD_SITE_CHANGED", f"sites[{site.index}]")
        for person, action in plan.people:
            if action == "create":
                self.wrote = True
                self._accounts.onboard_create(f.slug, person.email, person.name, secrets.token_urlsafe(32),
                                              executive=person.executive)
        emails = {p.index: p.email for p in f.people}
        for role in plan.roles:
            if role.action == "grant":
                self.wrote = True
                self._accounts.onboard_grant(f.slug, emails[role.index], role.role, role.site)
        if plan.key == "create":
            self.wrote = True
            self._keys.create(tenant.id)
        return plan
