"""W5-01b C4: the sole runtime writer of the two migration-0032 cold scenario tables.

`.agent/W5-01-build-spec.md` "C4 rule-8 writer policy" and pre-flight rulings P-C4-2..6. Every write is one INSERT
into `cold_scenario` or `cold_scenario_revision` on the caller's transaction; 0032's `<table>_immutable` triggers
refuse row changes and removals, and this module never issues either, never upserts and writes no other table. An
idempotent replay is a SELECT followed by a caught unique violation. Writer transactions are REPEATABLE READ; the
list snapshot is REPEATABLE READ READ ONLY. This module imports no analytics module and holds only its own SQL.
`created_at`/`recorded_at` are the database `clock_timestamp()` defaults.
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from typing import Any, Callable, Iterator, Mapping, TypeVar
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import DBAPIError, IntegrityError, OperationalError, ProgrammingError

T = TypeVar("T")
#: Serialization failure and deadlock: a retryable write race, like a unique violation.
RETRYABLE_SQLSTATES = ("40001", "40P01")


class ColdScenarioStoreUnavailable(RuntimeError):
    """The cold scenario store could not be reached or queried."""


class ColdScenarioWriteRefused(ValueError):
    """A unique, check or serialization race refused the write; nothing was committed."""


class ColdScenarioReadFailed(RuntimeError):
    """A read composed on the store's connection (the selected cold basis) failed in the database."""


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sqlstate(error: DBAPIError) -> str | None:
    orig = getattr(error, "orig", None)
    return getattr(orig, "sqlstate", None) or getattr(orig, "pgcode", None)


_INSERT_SCENARIO = (
    "INSERT INTO cold_scenario (id, tenant_id, site_id, create_key, create_payload_sha256, create_actor_id, "
    "actor_kind, actor_id) VALUES (:id, :tenant_id, :site_id, :create_key, :create_payload_sha256, "
    ":create_actor_id, :actor_kind, :actor_id) RETURNING public_no"
)
_INSERT_SCENARIO_REVISION = (
    "INSERT INTO cold_scenario_revision (id, tenant_id, site_id, scenario_id, revision_no, supersedes_revision_id, "
    "name, kind, assumptions, authored_basis, basis_sha256, formula_version, correction_reason, actor_kind, "
    "actor_id, authorization_basis, attestation, idempotency_key, payload_sha256) VALUES (:id, :tenant_id, "
    ":site_id, :scenario_id, :revision_no, :supersedes_revision_id, :name, :kind, CAST(:assumptions AS jsonb), "
    "CAST(:authored_basis AS jsonb), :basis_sha256, :formula_version, :correction_reason, :actor_kind, :actor_id, "
    ":authorization_basis, :attestation, :idempotency_key, :payload_sha256)"
)
_REVISION_COLUMNS = (
    "id, scenario_id, revision_no, supersedes_revision_id, name, kind, assumptions, authored_basis, basis_sha256, "
    "idempotency_key, payload_sha256, recorded_at"
)
#: Candidate revisions: every revision, recorded by `scenario_at`, of a root of this tenant and Site whose revision 1
#: fixes exactly the requested window. The evidence-cutoff predicate is applied after the shape check (Q-C5b item 5).
_CANDIDATES = (
    "FROM cold_scenario m JOIN cold_scenario_revision f ON f.tenant_id = m.tenant_id "
    "AND f.site_id = m.site_id AND f.scenario_id = m.id AND f.revision_no = 1 JOIN cold_scenario_revision r "
    "ON r.tenant_id = m.tenant_id AND r.site_id = m.site_id AND r.scenario_id = m.id "
    "WHERE m.tenant_id = :t AND m.site_id = :s AND CAST(f.authored_basis->>'from' AS timestamptz) = :lo "
    "AND CAST(f.authored_basis->>'to' AS timestamptz) = :hi AND r.recorded_at <= :at "
)
#: Whether any candidate revision's stored basis lacks `from`, `to` or `cutoff` (malformed history: 503).
_MALFORMED = (
    "SELECT EXISTS (SELECT 1 " + _CANDIDATES + "AND (r.authored_basis->>'from' IS NULL "
    "OR r.authored_basis->>'to' IS NULL OR r.authored_basis->>'cutoff' IS NULL))"
)
#: Each candidate root at its latest revision with an evidence cutoff no later than `known_at`.
_SELECTED = (
    "SELECT DISTINCT ON (r.scenario_id) r.id, r.scenario_id, m.public_no, "
    "r.revision_no, (SELECT max(x.revision_no) FROM cold_scenario_revision x WHERE x.tenant_id = r.tenant_id "
    "AND x.site_id = r.site_id AND x.scenario_id = r.scenario_id) AS latest_no, r.name, r.kind, r.assumptions, "
    "r.authored_basis, r.recorded_at " + _CANDIDATES
    + "AND CAST(r.authored_basis->>'cutoff' AS timestamptz) <= :k ORDER BY r.scenario_id, r.revision_no DESC"
)
#: The selected heads ordered `(recorded_at DESC, id DESC, scenario_id)`, paged strictly after `(recorded_at, id)`.
_HEADS = (
    "SELECT h.id, h.scenario_id, h.public_no, h.revision_no, h.latest_no, h.name, h.kind, h.assumptions, "
    "h.authored_basis, h.recorded_at FROM (" + _SELECTED + ") h "
    "WHERE CAST(:after_at AS timestamptz) IS NULL OR h.recorded_at < CAST(:after_at AS timestamptz) "
    "OR (h.recorded_at = CAST(:after_at AS timestamptz) AND h.id < CAST(:after_id AS uuid)) "
    "ORDER BY h.recorded_at DESC, h.id DESC, h.scenario_id LIMIT :n"
)
#: Every selected head, before cursor and limit (Q-C5b item 2 `total_pages`).
_COUNT = "SELECT count(*) FROM (" + _SELECTED + ") h"


class PostgresColdScenarioStore:
    """Appends 0032 rows on the caller's transaction and reads them in one snapshot."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    @classmethod
    def from_url(cls, database_url: str) -> "PostgresColdScenarioStore":
        return cls(create_engine(database_url, pool_pre_ping=True))

    def dispose(self) -> None:
        self._engine.dispose()

    @contextmanager
    def transaction(self) -> Iterator[Connection]:
        """One REPEATABLE READ write transaction (P-C4-6), begun before the basis is read; a refused or failed
        statement rolls the whole block back."""
        try:
            with self._engine.connect().execution_options(isolation_level="REPEATABLE READ") as c:
                with c.begin():
                    yield c
        except ColdScenarioWriteRefused:
            raise
        except IntegrityError as error:
            raise ColdScenarioWriteRefused(f"The cold scenario write was refused: {error.orig}") from error
        except (OperationalError, ProgrammingError, DBAPIError) as error:
            if _sqlstate(error) in RETRYABLE_SQLSTATES:
                raise ColdScenarioWriteRefused("The cold scenario write lost a concurrent race.") from error
            raise ColdScenarioStoreUnavailable(
                f"The cold scenario store failed: {error.__class__.__name__}") from error

    @contextmanager
    def snapshot(self) -> Iterator[Connection]:
        """One REPEATABLE READ READ ONLY snapshot (P-C4-6); the caller captures DB time first."""
        try:
            with self._engine.connect().execution_options(isolation_level="REPEATABLE READ") as c:
                with c.begin():
                    c.execute(text("SET TRANSACTION READ ONLY"))
                    yield c
        except (OperationalError, ProgrammingError, DBAPIError) as error:
            raise ColdScenarioStoreUnavailable(
                f"The cold scenario read failed: {error.__class__.__name__}") from error

    @staticmethod
    def reading(work: Callable[[], T]) -> T:
        """Run a read composed on this store's connection; a database failure is `ColdScenarioReadFailed`."""
        try:
            return work()
        except (OperationalError, ProgrammingError, DBAPIError) as error:
            raise ColdScenarioReadFailed(f"The selected cold read failed: {error.__class__.__name__}") from error

    @staticmethod
    def db_now(c: Connection) -> Any:
        return c.execute(text("SELECT clock_timestamp()")).scalar_one()

    # --- inserts ----------------------------------------------------------------------------------------------

    @staticmethod
    def insert_scenario(c: Connection, row: Mapping[str, Any]) -> int:
        return c.execute(text(_INSERT_SCENARIO), dict(row)).scalar_one()

    @staticmethod
    def insert_scenario_revision(c: Connection, row: Mapping[str, Any]) -> None:
        values = dict(row)
        for key in ("assumptions", "authored_basis"):
            values[key] = _json(values[key])
        c.execute(text(_INSERT_SCENARIO_REVISION), values)

    # --- reads ------------------------------------------------------------------------------------------------

    @staticmethod
    def scenario_by_create_key(c: Connection, tenant_id: UUID, site_id: UUID, key: str) -> Mapping[str, Any] | None:
        return c.execute(text(
            "SELECT id, public_no, create_payload_sha256 FROM cold_scenario WHERE tenant_id = :t AND site_id = :s "
            "AND create_key = :k"), {"t": tenant_id, "s": site_id, "k": key}).mappings().one_or_none()

    @staticmethod
    def lock_scenario(c: Connection, tenant_id: UUID, site_id: UUID, scenario_id: str) -> Mapping[str, Any] | None:
        """The scenario root of this tenant and Site, row-locked for a correction."""
        return c.execute(text(
            "SELECT id, public_no FROM cold_scenario WHERE tenant_id = :t AND site_id = :s AND id = :id FOR UPDATE"),
            {"t": tenant_id, "s": site_id, "id": scenario_id}).mappings().one_or_none()

    @staticmethod
    def scenario_revisions(c: Connection, tenant_id: UUID, site_id: UUID, scenario_id: Any) -> list[Mapping[str, Any]]:
        return list(c.execute(text(
            f"SELECT {_REVISION_COLUMNS} FROM cold_scenario_revision WHERE tenant_id = :t AND site_id = :s "
            "AND scenario_id = :id ORDER BY revision_no"), {"t": tenant_id, "s": site_id, "id": scenario_id}).mappings())

    @staticmethod
    def heads(c: Connection, tenant_id: UUID, site_id: UUID, lo: Any, hi: Any, known: Any, scenario_at: Any,
              after: tuple[Any, str] | None, limit: int) -> list[Mapping[str, Any]]:
        return list(c.execute(text(_HEADS), {
            "t": tenant_id, "s": site_id, "lo": lo, "hi": hi, "k": known, "at": scenario_at,
            "after_at": None if after is None else after[0], "after_id": None if after is None else after[1],
            "n": limit}).mappings())

    @staticmethod
    def malformed_candidates(c: Connection, tenant_id: UUID, site_id: UUID, lo: Any, hi: Any,
                             scenario_at: Any) -> bool:
        return bool(c.execute(text(_MALFORMED), {
            "t": tenant_id, "s": site_id, "lo": lo, "hi": hi, "at": scenario_at}).scalar_one())

    @staticmethod
    def count_heads(c: Connection, tenant_id: UUID, site_id: UUID, lo: Any, hi: Any, known: Any,
                    scenario_at: Any) -> int:
        return int(c.execute(text(_COUNT), {
            "t": tenant_id, "s": site_id, "lo": lo, "hi": hi, "k": known, "at": scenario_at}).scalar_one())


__all__ = ["ColdScenarioReadFailed", "ColdScenarioStoreUnavailable", "ColdScenarioWriteRefused",
           "PostgresColdScenarioStore"]
