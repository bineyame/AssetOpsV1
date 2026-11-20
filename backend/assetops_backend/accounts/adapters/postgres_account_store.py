"""3C0a (spec §2, §4.1; R5, R6, R7, D-3C0A.11, MB1, MB2): the Postgres account store.

This adapter is the sole runtime writer of the six 0062 tables (registered in
`tools/checks/configuration-persistence.ps1`). It runs exactly these write shapes: one plain INSERT per table, the
session revoke `UPDATE operator_session SET revoked_at = :at WHERE token_sha256 = :h AND revoked_at IS NULL`, and
the attempt purge `DELETE FROM sign_in_attempt WHERE at < :before`. The 0062 triggers refuse every other change.

Locks (transaction-scoped advisory locks, taken first in the writing transaction, the refusal rules re-checked
after them): the per-tenant `role_grant:<tenant>` lock for a grant, a removal, an account created with the
executive grant, and a status set to DISABLED (R6); the per-email `sign_in:<key sha256>` lock across an attempt's
count, verification and insert (R5). While `guarded_attempt` holds its lock, the verification's reads run on the
same connection (a thread-local), so a burst of sign-ins never waits on the pool for a second connection.
"""
from __future__ import annotations

import threading
from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Callable, Iterator
from uuid import UUID, uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError, InterfaceError, OperationalError

from assetops_backend.accounts.model import (ATTEMPT_DAYS, EXECUTIVE, LOCK_FAILURES, LOCK_MINUTES, Account, GrantRow,
                                             PersonView, SessionRow)
from assetops_backend.accounts.store import Attempt, StoreConflict

#: The store errors the routes answer 503 `ACCOUNTS_UNAVAILABLE` (R14); passed to the router by `create_app`.
UNAVAILABLE: tuple[type[BaseException], ...] = (OperationalError, InterfaceError)

_TENANT_LOCK = text("SELECT pg_advisory_xact_lock(hashtextextended('role_grant:' || CAST(:tenant_id AS text), 0))")
_EMAIL_LOCK = text("SELECT pg_advisory_xact_lock(hashtextextended('sign_in:' || :key_sha256, 0))")

_INSERT_ACCOUNT = text(
    "INSERT INTO operator_account (id, tenant_id, email, email_key, display_name, created_at, created_by) "
    "VALUES (:id, :tenant_id, :email, :email_key, :display_name, :created_at, :created_by)")
_INSERT_CREDENTIAL = text(
    "INSERT INTO account_credential (id, tenant_id, person_id, password_hash, set_at, set_by) "
    "VALUES (:id, :tenant_id, :person_id, :password_hash, :set_at, :set_by)")
_INSERT_STATUS = text(
    "INSERT INTO account_status (id, tenant_id, person_id, status, reason, set_at, set_by) "
    "VALUES (:id, :tenant_id, :person_id, :status, :reason, :set_at, :set_by)")
_INSERT_GRANT = text(
    "INSERT INTO role_grant (id, tenant_id, person_id, role, site_id, action, grant_id, by_person_id, by_service, at) "
    "VALUES (:id, :tenant_id, :person_id, :role, :site_id, :action, :grant_id, :by_person_id, :by_service, :at)")
_INSERT_SESSION = text(
    "INSERT INTO operator_session (id, tenant_id, person_id, token_sha256, created_at, expires_at) "
    "VALUES (:id, :tenant_id, :person_id, :token_sha256, :created_at, :expires_at)")
_INSERT_ATTEMPT = text(
    "INSERT INTO sign_in_attempt (id, email_key_sha256, at, succeeded, person_id) "
    "VALUES (:id, :email_key_sha256, :at, :succeeded, :person_id)")
_REVOKE = text("UPDATE operator_session SET revoked_at = :at WHERE token_sha256 = :h AND revoked_at IS NULL")
_PURGE = text("DELETE FROM sign_in_attempt WHERE at < :before")

_TENANT_BY_SLUG = text("SELECT id, name FROM tenant WHERE slug = :slug")
_TENANT = text("SELECT slug, name FROM tenant WHERE id = :t")
_TENANT_SLUG = text("SELECT slug FROM tenant WHERE id = :t")  # 3A3 (spec §2.7)
_SITE = text("SELECT id FROM site WHERE tenant_id = :t AND site_code_key = lower(:code)")
_ACCOUNT_COLUMNS = "SELECT id, tenant_id, email, display_name FROM operator_account "
_ACCOUNT_BY_KEY = text(_ACCOUNT_COLUMNS + "WHERE email_key = :k")
_ACCOUNT = text(_ACCOUNT_COLUMNS + "WHERE tenant_id = :t AND id = :p")
_CREDENTIAL = text("SELECT password_hash, set_at FROM account_credential WHERE person_id = :p "
                   "ORDER BY set_at DESC, id DESC LIMIT 1")
_STATUS = text("SELECT status FROM account_status WHERE person_id = :p ORDER BY set_at DESC, id DESC LIMIT 1")
_SESSION = text("SELECT id, tenant_id, person_id, created_at, expires_at, revoked_at FROM operator_session "
                "WHERE token_sha256 = :h")

#: Every `role_grant` row of a tenant as a `GrantRow`; `grant_id` is the row's own id on a GRANTED row.
_GRANT_SELECT = (
    "SELECT g.id AS row_id, COALESCE(g.grant_id, g.id) AS grant_id, g.tenant_id, g.person_id, a.display_name, g.role, "
    "g.site_id, s.site_code, g.action, g.by_person_id, b.display_name AS by_display_name, g.by_service, g.at "
    "FROM role_grant g JOIN operator_account a ON a.id = g.person_id "
    "LEFT JOIN site s ON s.tenant_id = g.tenant_id AND s.id = g.site_id "
    "LEFT JOIN operator_account b ON b.id = g.by_person_id WHERE g.tenant_id = :t ")
_HELD = ("AND g.action = 'GRANTED' AND NOT EXISTS (SELECT 1 FROM role_grant r WHERE r.grant_id = g.id) ")
_GRANT_ROWS = text(_GRANT_SELECT + "ORDER BY g.at DESC, g.id DESC")
_GRANT_ROW = text(_GRANT_SELECT + "AND g.id = :g")
_HELD_ALL = text(_GRANT_SELECT + _HELD + "ORDER BY g.at, g.id")
_HELD_BY = text(_GRANT_SELECT + _HELD + "AND g.person_id = :p ORDER BY g.at, g.id")
_HELD_SAME = text(
    "SELECT 1 FROM role_grant g WHERE g.tenant_id = :t AND g.person_id = :p AND g.role = :role "
    "AND g.site_id IS NOT DISTINCT FROM :site AND g.action = 'GRANTED' "
    "AND NOT EXISTS (SELECT 1 FROM role_grant r WHERE r.grant_id = g.id)")
_REMOVED = text("SELECT 1 FROM role_grant WHERE grant_id = :g AND action = 'REMOVED'")
#: The persons holding OPERATOR_EXECUTIVE on an ACTIVE account (D-3C0A.5, R7).
_ACTIVE_EXECUTIVES = text(
    "SELECT DISTINCT g.person_id FROM role_grant g WHERE g.tenant_id = :t AND g.role = 'OPERATOR_EXECUTIVE' "
    "AND g.action = 'GRANTED' AND NOT EXISTS (SELECT 1 FROM role_grant r WHERE r.grant_id = g.id) "
    "AND (SELECT s.status FROM account_status s WHERE s.person_id = g.person_id "
    "ORDER BY s.set_at DESC, s.id DESC LIMIT 1) = 'ACTIVE'")
_PEOPLE = text(
    "SELECT a.id, a.display_name, a.email, a.email_key, (SELECT s.status FROM account_status s "
    "WHERE s.person_id = a.id ORDER BY s.set_at DESC, s.id DESC LIMIT 1) AS status "
    "FROM operator_account a WHERE a.tenant_id = :t")
_RECENT_FAILURES = text(
    "SELECT at FROM sign_in_attempt WHERE email_key_sha256 = :k AND NOT succeeded AND at > greatest(:since, "
    "COALESCE((SELECT max(at) FROM sign_in_attempt WHERE email_key_sha256 = :k AND succeeded), :since)) "
    "ORDER BY at DESC, id DESC LIMIT :n")


def _grant(row) -> GrantRow:
    return GrantRow(**dict(row._mapping))


def _grant_values(row: GrantRow) -> dict:
    return {"id": row.row_id, "tenant_id": row.tenant_id, "person_id": row.person_id, "role": row.role,
            "site_id": row.site_id, "action": row.action,
            "grant_id": row.grant_id if row.action == "REMOVED" else None,
            "by_person_id": row.by_person_id, "by_service": row.by_service, "at": row.at}


class PostgresAccountStore:
    def __init__(self, url: str) -> None:
        self._engine = create_engine(url, pool_pre_ping=True, hide_parameters=True)
        self._local = threading.local()

    def dispose(self) -> None:
        self._engine.dispose()

    @contextmanager
    def _begin(self, known: dict[str, str] | None = None) -> Iterator[Connection]:
        """A write transaction. An integrity error leaves as a `StoreConflict` carrying only the constraint name: the
        driver's message and `DETAIL` (which print the failing row) never survive, not as text, cause or context."""
        try:
            with self._engine.begin() as c:
                yield c
        except IntegrityError as error:
            name = getattr(getattr(error.orig, "diag", None), "constraint_name", None)
            code = (known or {}).get(name or "")
            if code is not None:
                raise StoreConflict(code) from None
            raise StoreConflict("ACCOUNTS_STORE_REFUSED", name) from None

    @contextmanager
    def _read(self) -> Iterator[Connection]:
        held = getattr(self._local, "connection", None)
        if held is not None:
            yield held
            return
        with self._engine.connect() as c:
            yield c

    def _lock_tenant(self, c: Connection, tenant_id: UUID) -> None:
        c.execute(_TENANT_LOCK, {"tenant_id": str(tenant_id)})

    @staticmethod
    def _active_executives(c: Connection, tenant_id: UUID) -> set[UUID]:
        return set(c.execute(_ACTIVE_EXECUTIVES, {"t": tenant_id}).scalars())

    @classmethod
    def _require_executive(cls, c: Connection, tenant_id: UUID, actor_person_id: UUID) -> None:
        """RV1-R2: under the tenant lock, the actor still holds OPERATOR_EXECUTIVE on an ACTIVE account."""
        if actor_person_id not in cls._active_executives(c, tenant_id):
            raise StoreConflict("ROLE_REQUIRED")

    # --- reads ------------------------------------------------------------------------------------------------------

    def tenant_by_slug(self, slug: str) -> tuple[UUID, str] | None:
        with self._read() as c:
            found = c.execute(_TENANT_BY_SLUG, {"slug": slug}).first()
        return None if found is None else (found.id, found.name)

    def tenant(self, tenant_id: UUID) -> tuple[str, str] | None:
        with self._read() as c:
            found = c.execute(_TENANT, {"t": tenant_id}).first()
        return None if found is None else (found.slug, found.name)

    def tenant_slug(self, tenant_id: UUID) -> str | None:
        with self._read() as c:
            return c.execute(_TENANT_SLUG, {"t": tenant_id}).scalar()

    def site_id(self, tenant_id: UUID, site_code: str) -> UUID | None:
        with self._read() as c:
            return c.execute(_SITE, {"t": tenant_id, "code": site_code}).scalar()

    def account_by_email_key(self, key: str) -> Account | None:
        with self._read() as c:
            found = c.execute(_ACCOUNT_BY_KEY, {"k": key}).first()
        return None if found is None else Account(*found)

    def account(self, tenant_id: UUID, person_id: UUID) -> Account | None:
        with self._read() as c:
            found = c.execute(_ACCOUNT, {"t": tenant_id, "p": person_id}).first()
        return None if found is None else Account(*found)

    def current_credential(self, person_id: UUID) -> tuple[str, datetime] | None:
        with self._read() as c:
            found = c.execute(_CREDENTIAL, {"p": person_id}).first()
        return None if found is None else (found.password_hash, found.set_at)

    def current_status(self, person_id: UUID) -> str | None:
        with self._read() as c:
            return c.execute(_STATUS, {"p": person_id}).scalar()

    def held_grants(self, tenant_id: UUID, person_id: UUID) -> tuple[GrantRow, ...]:
        with self._read() as c:
            return tuple(_grant(r) for r in c.execute(_HELD_BY, {"t": tenant_id, "p": person_id}))

    def grant_row(self, tenant_id: UUID, grant_id: UUID) -> GrantRow | None:
        with self._read() as c:
            found = c.execute(_GRANT_ROW, {"t": tenant_id, "g": grant_id}).first()
        return None if found is None else _grant(found)

    def grant_rows(self, tenant_id: UUID) -> tuple[GrantRow, ...]:
        with self._read() as c:
            return tuple(_grant(r) for r in c.execute(_GRANT_ROWS, {"t": tenant_id}))

    def people(self, tenant_id: UUID) -> tuple[PersonView, ...]:
        with self._read() as c:
            accounts = c.execute(_PEOPLE, {"t": tenant_id}).all()
            held: dict[UUID, list[GrantRow]] = defaultdict(list)
            for r in c.execute(_HELD_ALL, {"t": tenant_id}):
                held[r.person_id].append(_grant(r))
        views = sorted(accounts, key=lambda a: (a.display_name.casefold(), a.email_key))  # P13: not a collation
        return tuple(PersonView(a.id, a.display_name, a.email, a.status, tuple(held[a.id])) for a in views)

    def session(self, token_sha256: str) -> SessionRow | None:
        with self._read() as c:
            found = c.execute(_SESSION, {"h": token_sha256}).first()
        return None if found is None else SessionRow(*found)

    # --- sign-in ----------------------------------------------------------------------------------------------------

    def guarded_attempt(self, key_sha256: str, now: datetime,
                        verify: Callable[[], tuple[bool, UUID | None]]) -> Attempt:
        with self._begin() as c:
            c.execute(_EMAIL_LOCK, {"key_sha256": key_sha256})
            failures = c.execute(_RECENT_FAILURES, {"k": key_sha256, "since": now - timedelta(minutes=LOCK_MINUTES),
                                                    "n": LOCK_FAILURES}).scalars().all()
            if len(failures) >= LOCK_FAILURES:
                return Attempt(locked=True, retry_at=failures[-1] + timedelta(minutes=LOCK_MINUTES))
            self._local.connection = c
            try:
                succeeded, person_id = verify()
            finally:
                self._local.connection = None
            person = person_id if succeeded else None
            c.execute(_INSERT_ATTEMPT, {"id": uuid4(), "email_key_sha256": key_sha256, "at": now,
                                        "succeeded": succeeded, "person_id": person})
            c.execute(_PURGE, {"before": now - timedelta(days=ATTEMPT_DAYS)})
        return Attempt(locked=False, succeeded=succeeded, person_id=person)

    def add_session(self, id: UUID, tenant_id: UUID, person_id: UUID, token_sha256: str, created_at: datetime,
                    expires_at: datetime) -> None:
        with self._begin() as c:
            c.execute(_INSERT_SESSION, {"id": id, "tenant_id": tenant_id, "person_id": person_id,
                                        "token_sha256": token_sha256, "created_at": created_at,
                                        "expires_at": expires_at})

    def revoke(self, token_sha256: str, at: datetime) -> None:
        with self._begin() as c:
            c.execute(_REVOKE, {"at": at, "h": token_sha256})

    # --- grants -----------------------------------------------------------------------------------------------------

    def add_grant(self, row: GrantRow, actor_person_id: UUID) -> GrantRow:
        with self._begin() as c:
            self._lock_tenant(c, row.tenant_id)
            self._require_executive(c, row.tenant_id, actor_person_id)
            if c.execute(_HELD_SAME, {"t": row.tenant_id, "p": row.person_id, "role": row.role,
                                      "site": row.site_id}).first() is not None:
                raise StoreConflict("ROLE_ALREADY_HELD")
            c.execute(_INSERT_GRANT, _grant_values(row))
        recorded = self.grant_row(row.tenant_id, row.row_id)
        assert recorded is not None
        return recorded

    def add_removal(self, row: GrantRow, actor_person_id: UUID) -> GrantRow:
        with self._begin() as c:
            self._lock_tenant(c, row.tenant_id)
            self._require_executive(c, row.tenant_id, actor_person_id)
            if c.execute(_REMOVED, {"g": row.grant_id}).first() is not None:
                raise StoreConflict("GRANT_ALREADY_REMOVED")
            if row.role == EXECUTIVE and not (self._active_executives(c, row.tenant_id) - {row.person_id}):
                raise StoreConflict("LAST_EXECUTIVE")
            c.execute(_INSERT_GRANT, _grant_values(row))
        recorded = self.grant_row(row.tenant_id, row.row_id)
        assert recorded is not None
        return recorded

    # --- the onboarding writes --------------------------------------------------------------------------------------

    def create_account(self, account: Account, password_hash: str, created_at: datetime, by: str,
                       executive_grant: GrantRow | None) -> None:
        key = account.email.lower()
        with self._begin({"operator_account_email_key_key": "EMAIL_TAKEN"}) as c:
            if executive_grant is not None:
                self._lock_tenant(c, account.tenant_id)
            if c.execute(_ACCOUNT_BY_KEY, {"k": key}).first() is not None:
                raise StoreConflict("EMAIL_TAKEN")
            if executive_grant is not None and self._active_executives(c, account.tenant_id):
                raise StoreConflict("EXECUTIVE_EXISTS")
            c.execute(_INSERT_ACCOUNT, {"id": account.id, "tenant_id": account.tenant_id, "email": account.email,
                                        "email_key": key, "display_name": account.display_name,
                                        "created_at": created_at, "created_by": by})
            c.execute(_INSERT_CREDENTIAL, {"id": uuid4(), "tenant_id": account.tenant_id, "person_id": account.id,
                                           "password_hash": password_hash, "set_at": created_at, "set_by": by})
            c.execute(_INSERT_STATUS, {"id": uuid4(), "tenant_id": account.tenant_id, "person_id": account.id,
                                       "status": "ACTIVE", "reason": None, "set_at": created_at, "set_by": by})
            if executive_grant is not None:
                c.execute(_INSERT_GRANT, _grant_values(executive_grant))

    def set_credential(self, tenant_id: UUID, person_id: UUID, password_hash: str, at: datetime, by: str) -> None:
        with self._begin() as c:
            c.execute(_INSERT_CREDENTIAL, {"id": uuid4(), "tenant_id": tenant_id, "person_id": person_id,
                                           "password_hash": password_hash, "set_at": at, "set_by": by})

    def set_status(self, tenant_id: UUID, person_id: UUID, status: str, reason: str | None, at: datetime,
                   by: str) -> None:
        with self._begin() as c:
            if status == "DISABLED":
                self._lock_tenant(c, tenant_id)
                active = self._active_executives(c, tenant_id)
                if person_id in active and not (active - {person_id}):
                    raise StoreConflict("LAST_EXECUTIVE")
            c.execute(_INSERT_STATUS, {"id": uuid4(), "tenant_id": tenant_id, "person_id": person_id,
                                       "status": status, "reason": reason, "set_at": at, "set_by": by})
