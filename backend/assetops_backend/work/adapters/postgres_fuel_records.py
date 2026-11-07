"""DIESEL-K2 (`.agent/build-sheet-DIESEL-1.md` §9c.2): the read-only as-known fuel records reader (a rule-8 named
PostgreSQL reader, never a writer).

`select_fuel_records` runs on a caller's connection, so K3 reads inside its own snapshot; `PostgresFuelRecords`
implements `FuelRecordsPort` with one `REPEATABLE READ READ ONLY` transaction. Only `SET TRANSACTION READ ONLY` and
`SELECT` are issued here.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import DBAPIError, OperationalError

from assetops_backend.work.fuel_records import FuelRecord, check_window
from assetops_backend.work.model import WorkStoreUnavailable

# The `_OPERATIONAL` root/head shape (postgres_global_read.py): every root recorded by K at its latest version
# recorded by K by `(recorded_at, id)`; membership is the HEAD's kind, tank and occurrence in `[lo, hi)`.
_FUEL_RECORDS = (
    "SELECT CAST(r.id AS text) AS root_id, CAST(h.id AS text) AS head_id, r.public_code AS code, h.kind, "
    "h.occurred_at, h.recorded_at, r.recorded_at AS root_recorded_at, h.quantity, h.source_document_sha256, "
    "h.actor_id, h.body "
    "FROM operational_record r JOIN LATERAL (SELECT * FROM operational_record p WHERE p.tenant_id = r.tenant_id "
    "AND p.site_id = r.site_id AND p.canonical_record_id = r.id AND p.recorded_at <= :k "
    "ORDER BY p.recorded_at DESC, p.id DESC LIMIT 1) h ON true "
    "WHERE r.tenant_id = :t AND r.site_id = :s AND r.supersedes_record_id IS NULL AND r.canonical_record_id = r.id "
    "AND r.recorded_at <= :k AND h.kind IN ('FUEL_DELIVERY', 'TANK_DIP') AND h.asset_id = :a "
    "AND h.occurred_at >= :lo AND h.occurred_at < :hi ORDER BY h.occurred_at, r.id")


def _utc(value: datetime) -> datetime:
    return value.astimezone(timezone.utc)


def select_fuel_records(c: Connection, tenant_id: UUID, site_id: UUID, tank_asset_id: UUID, lo: datetime,
                        hi: datetime, known_at: datetime) -> tuple[FuelRecord, ...]:
    """The fuel records of one tank occurring in `[lo, hi)` as known at `known_at`, on the caller's connection."""
    check_window(lo, hi, known_at)
    rows = c.execute(text(_FUEL_RECORDS), {"t": tenant_id, "s": site_id, "a": tank_asset_id, "lo": lo, "hi": hi,
                                           "k": known_at})
    return tuple(FuelRecord(root_id=r.root_id, head_id=r.head_id, code=r.code, kind=r.kind,
                            occurred_at=_utc(r.occurred_at), recorded_at=_utc(r.recorded_at),
                            root_recorded_at=_utc(r.root_recorded_at), quantity_l=Decimal(r.quantity),
                            ticket_sha256=r.source_document_sha256, actor_id=r.actor_id, body=r.body)
                 for r in rows)


class PostgresFuelRecords:
    """`FuelRecordsPort` over one read-only REPEATABLE READ transaction per call."""

    def __init__(self, database_url: str | None, *, statement_timeout_ms: int = 30_000) -> None:
        self._database_url = database_url
        self._options = f"-c statement_timeout={int(statement_timeout_ms)}"
        self._engine: Engine | None = None

    def _connect(self) -> Engine:
        if not self._database_url:
            raise WorkStoreUnavailable("DATABASE_URL is not set, so the work store cannot be read.")
        if self._engine is None:
            self._engine = create_engine(self._database_url, pool_pre_ping=True,
                                         connect_args={"options": self._options})
        return self._engine

    def dispose(self) -> None:
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None

    def fuel_records(self, tenant_id: UUID, site_id: UUID, tank_asset_id: UUID, lo: datetime, hi: datetime,
                     known_at: datetime) -> tuple[FuelRecord, ...]:
        check_window(lo, hi, known_at)
        try:
            with self._connect().connect().execution_options(isolation_level="REPEATABLE READ") as c, c.begin():
                c.execute(text("SET TRANSACTION READ ONLY"))
                return select_fuel_records(c, tenant_id, site_id, tank_asset_id, lo, hi, known_at)
        except (OperationalError, DBAPIError) as error:
            raise WorkStoreUnavailable(f"The work store could not be read: {error.__class__.__name__}") from error
