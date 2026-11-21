"""3C2 (spec §2.3-§2.4; D-3C2.3, D-3C2.7): the Postgres store of agreed changes.

The sole runtime writer of `agreed_action` (the persistence guard): one plain INSERT, under the tenant's advisory
lock after an identity read. The unique index `agreed_action_once` is the backstop: a violation of it is a re-run
and returns the stored row. It reads `agreed_action`, `operator_account` and `site` and no other table. Driver errors
leave as `StoreUnavailable` with no row text.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Row
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from assetops_backend.actions.agreed import AgreedActionRow, IdentityKey, StoreUnavailable

_ONCE = "agreed_action_once"
_LOCK = text("SELECT pg_advisory_xact_lock(hashtextextended('agreed_action:' || CAST(:tenant_id AS text), 0))")
_SITE = text("SELECT id, site_type, site_code FROM site WHERE tenant_id = :t AND site_code_key = lower(:c)")
_FIND = text(
    "SELECT id, tenant_id, title, site_id, factor_id, owner_person_id, created_by_person_id, created_role, "
    "created_by_script, created_at, due_on, origin FROM agreed_action WHERE tenant_id = :tenant_id "
    "AND created_by_person_id = :created_by_person_id AND owner_person_id = :owner_person_id AND title = :title "
    "AND due_on = :due_on AND site_id IS NOT DISTINCT FROM :site_id AND factor_id IS NOT DISTINCT FROM :factor_id")
_INSERT = text(
    "INSERT INTO agreed_action (id, tenant_id, title, site_id, factor_id, owner_person_id, created_by_person_id, "
    "created_role, created_by_script, created_at, due_on, origin) VALUES (:id, :tenant_id, :title, :site_id, "
    ":factor_id, :owner_person_id, :created_by_person_id, :created_role, :created_by_script, :created_at, :due_on, "
    ":origin)")
_FOR_TENANT = text(
    "SELECT a.id, a.tenant_id, a.title, a.site_id, a.factor_id, a.owner_person_id, a.created_by_person_id, "
    "a.created_role, a.created_by_script, a.created_at, a.due_on, a.origin, s.site_code, o.display_name AS owner_name, "
    "c.display_name AS creator_name FROM agreed_action a "
    "JOIN operator_account o ON o.tenant_id = a.tenant_id AND o.id = a.owner_person_id "
    "JOIN operator_account c ON c.tenant_id = a.tenant_id AND c.id = a.created_by_person_id "
    "LEFT JOIN site s ON s.tenant_id = a.tenant_id AND s.id = a.site_id "
    "WHERE a.tenant_id = :t ORDER BY a.created_at DESC, a.id DESC")


def _key_params(tenant_id: UUID, key: IdentityKey) -> dict:
    return {"tenant_id": tenant_id, "created_by_person_id": key.created_by_person_id,
            "owner_person_id": key.owner_person_id, "title": key.title, "due_on": key.due_on,
            "site_id": key.site_id, "factor_id": key.factor_id}


def _row(r: Row) -> AgreedActionRow:
    return AgreedActionRow(r.id, r.tenant_id, r.title, r.site_id, r.factor_id, r.owner_person_id,
                           r.created_by_person_id, r.created_role, r.created_by_script, r.created_at, r.due_on,
                           r.origin)


class PostgresAgreedActionStore:
    def __init__(self, url: str) -> None:
        self._engine = create_engine(url, pool_pre_ping=True, hide_parameters=True)

    def dispose(self) -> None:
        self._engine.dispose()

    @contextmanager
    def _unavailable(self) -> Iterator[None]:
        try:
            yield
        except SQLAlchemyError:
            raise StoreUnavailable() from None

    def site(self, tenant_id: UUID, site_code: str) -> tuple[UUID, str, str] | None:
        with self._unavailable(), self._engine.connect() as c:
            found = c.execute(_SITE, {"t": tenant_id, "c": site_code}).one_or_none()
        return None if found is None else (found.id, found.site_type, found.site_code)

    def _find(self, c: Connection, tenant_id: UUID, key: IdentityKey) -> AgreedActionRow | None:
        found = c.execute(_FIND, _key_params(tenant_id, key)).one_or_none()
        return None if found is None else _row(found)

    def find(self, tenant_id: UUID, key: IdentityKey) -> AgreedActionRow | None:
        with self._unavailable(), self._engine.connect() as c:
            return self._find(c, tenant_id, key)

    def add(self, row: AgreedActionRow) -> tuple[AgreedActionRow, bool]:
        with self._unavailable():
            try:
                with self._engine.begin() as c:
                    c.execute(_LOCK, {"tenant_id": str(row.tenant_id)})
                    stored = self._find(c, row.tenant_id, row.key)
                    if stored is not None:
                        return stored, True
                    c.execute(_INSERT, {"id": row.id, "tenant_id": row.tenant_id, "title": row.title,
                                        "site_id": row.site_id, "factor_id": row.factor_id,
                                        "owner_person_id": row.owner_person_id,
                                        "created_by_person_id": row.created_by_person_id,
                                        "created_role": row.created_role, "created_by_script": row.created_by_script,
                                        "created_at": row.created_at, "due_on": row.due_on, "origin": row.origin})
                return row, False
            except IntegrityError as error:
                if getattr(getattr(error.orig, "diag", None), "constraint_name", None) != _ONCE:
                    raise
            with self._engine.connect() as c:
                stored = self._find(c, row.tenant_id, row.key)
            if stored is None:
                raise StoreUnavailable()
            return stored, True

    def for_tenant(self, tenant_id: UUID) -> tuple[tuple[AgreedActionRow, str | None, str, str], ...]:
        with self._unavailable(), self._engine.connect() as c:
            rows = c.execute(_FOR_TENANT, {"t": tenant_id}).all()
        return tuple((_row(r), r.site_code, r.owner_name, r.creator_name) for r in rows)
