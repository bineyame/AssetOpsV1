"""3C0a (spec §3, §4; MB1, MB2): the account records' shapes and constants.

Current state is derived, never stored (D-3C0A.2): a person's password is the latest credential row, the status the
latest status row, and a grant is held while its GRANTED row has no REMOVED row naming it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping
from uuid import UUID

#: The manifest's role codes, in the order every sorted list uses (D-3C0A.4).
ROLES = ("OPERATOR_EXECUTIVE", "FINANCE_AND_COMMERCIAL_LEAD", "SITE_MANAGER", "FIELD_TECHNICIAN", "ANALYST")
EXECUTIVE = "OPERATOR_EXECUTIVE"
SITE_ROLE = "SITE_MANAGER"
SESSION_HOURS = 12
LOCK_FAILURES = 5
LOCK_MINUTES = 15
#: Sign-in attempts are purged after this many days (D-3C0A.11).
ATTEMPT_DAYS = 30
COOKIE = "assetops_session"
ONBOARDING = "service:onboarding"


@dataclass(frozen=True)
class Account:
    id: UUID
    tenant_id: UUID
    email: str
    display_name: str


@dataclass(frozen=True)
class PersonPrincipal:
    person_id: UUID
    tenant_id: UUID
    display_name: str
    roles: frozenset[tuple[str, UUID | None]]
    session_id: UUID
    session_expires_at: datetime
    at: datetime

    def has_role(self, role: str, site_id: UUID | None = None) -> bool:
        """A Site manager check needs the Site; any other role ignores `site_id`."""
        if role == SITE_ROLE:
            return site_id is not None and (role, site_id) in self.roles
        return any(held == role for held, _ in self.roles)


@dataclass(frozen=True)
class GrantRow:
    """One `role_grant` row. `grant_id` is the grant the row is about: the row's own id on a GRANTED row, the granted
    row's id on a REMOVED row (the database stores NULL on a GRANTED row)."""
    row_id: UUID
    grant_id: UUID | None
    tenant_id: UUID
    person_id: UUID
    display_name: str
    role: str
    site_id: UUID | None
    site_code: str | None
    action: str
    by_person_id: UUID | None
    by_display_name: str | None
    by_service: str | None
    at: datetime


@dataclass(frozen=True)
class PersonView:
    person_id: UUID
    display_name: str
    email: str
    status: str
    grants: tuple[GrantRow, ...]


@dataclass(frozen=True)
class OnboardPerson:
    """3A3 (spec §2.7): one person as a command-line loader sees them, read by email. No write."""
    person_id: UUID
    tenant_id: UUID
    tenant_slug: str | None
    display_name: str
    active: bool
    roles: frozenset[tuple[str, UUID | None]]


@dataclass(frozen=True)
class SessionRow:
    id: UUID
    tenant_id: UUID
    person_id: UUID
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None


@dataclass(frozen=True)
class SignedIn:
    principal: PersonPrincipal
    token: str
    expires_at: datetime


class AccountRefused(Exception):
    """A refusal with its code (the words key is `accounts.<code lower case>`), HTTP status and word params."""

    def __init__(self, code: str, status: int, params: Mapping[str, Any] | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.status = status
        self.params: dict[str, Any] = dict(params or {})
