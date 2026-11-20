"""3C0a (spec §4.1; MB1, MB2): the account store port.

The Postgres adapter (`adapters/postgres_account_store.py`) is the one runtime implementation; the service tests
carry an in-memory one that re-implements every refusal below.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Protocol
from uuid import UUID

from assetops_backend.accounts.model import Account, GrantRow, PersonView, SessionRow


class StoreConflict(Exception):
    """A write refused under the store's lock: ROLE_ALREADY_HELD, GRANT_ALREADY_REMOVED, LAST_EXECUTIVE, EMAIL_TAKEN
    or EXECUTIVE_EXISTS."""

    def __init__(self, code: str, constraint: str | None = None) -> None:
        super().__init__(code)
        self.code = code
        #: `ACCOUNTS_STORE_REFUSED` only: the database constraint's name, the one thing kept of the driver's error.
        self.constraint = constraint


@dataclass(frozen=True)
class Attempt:
    """The outcome of `guarded_attempt`: locked (with the time the lock lifts), or the verification's result."""
    locked: bool
    retry_at: datetime | None = None
    succeeded: bool = False
    person_id: UUID | None = None


class AccountStore(Protocol):
    def tenant_by_slug(self, slug: str) -> tuple[UUID, str] | None: ...

    def tenant(self, tenant_id: UUID) -> tuple[str, str] | None: ...

    def tenant_slug(self, tenant_id: UUID) -> str | None:
        """3A3 (spec §2.7): the tenant's slug, or None."""

    def site_id(self, tenant_id: UUID, site_code: str) -> UUID | None: ...

    def account_by_email_key(self, key: str) -> Account | None: ...

    def account(self, tenant_id: UUID, person_id: UUID) -> Account | None: ...

    def current_credential(self, person_id: UUID) -> tuple[str, datetime] | None: ...

    def current_status(self, person_id: UUID) -> str | None: ...

    def held_grants(self, tenant_id: UUID, person_id: UUID) -> tuple[GrantRow, ...]: ...

    def guarded_attempt(self, key_sha256: str, now: datetime,
                        verify: Callable[[], tuple[bool, UUID | None]]) -> Attempt: ...

    def grant_row(self, tenant_id: UUID, grant_id: UUID) -> GrantRow | None: ...

    def add_session(self, id: UUID, tenant_id: UUID, person_id: UUID, token_sha256: str, created_at: datetime,
                    expires_at: datetime) -> None: ...

    def session(self, token_sha256: str) -> SessionRow | None: ...

    def revoke(self, token_sha256: str, at: datetime) -> None: ...

    def people(self, tenant_id: UUID) -> tuple[PersonView, ...]: ...

    def grant_rows(self, tenant_id: UUID) -> tuple[GrantRow, ...]: ...

    def add_grant(self, row: GrantRow, actor_person_id: UUID) -> GrantRow: ...

    def add_removal(self, row: GrantRow, actor_person_id: UUID) -> GrantRow: ...

    def create_account(self, account: Account, password_hash: str, created_at: datetime, by: str,
                       executive_grant: GrantRow | None) -> None: ...

    def set_credential(self, tenant_id: UUID, person_id: UUID, password_hash: str, at: datetime, by: str) -> None: ...

    def set_status(self, tenant_id: UUID, person_id: UUID, status: str, reason: str | None, at: datetime,
                   by: str) -> None: ...
