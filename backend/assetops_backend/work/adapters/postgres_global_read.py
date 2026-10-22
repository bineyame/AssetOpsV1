"""W6-01a: the read-only global work reader (A1Q G1/G2; a rule-8 named PostgreSQL reader, never a writer).

One caller-owned **read-only REPEATABLE READ** connection selects every authorized imported Site of the tenant and
hands each Site's per-Site W4 reads (`_ReadTx` of the sibling `postgres_work_read.py`) the same connection, so a
global list is one snapshot with no Site HTTP fan-out. The read time is the unrounded DB `clock_timestamp()` taken
once per snapshot (A1Q Q6; a private test may inject `test_read_clock_override`, called once instead; no request,
env or `main.py` path supplies it). Only `SET TRANSACTION READ ONLY` and `SELECT` are issued here.

The authorized-Site candidate SQL is the W3 estate predicate and order, copied (A1Q Q5): rule 1 refuses a
cross-domain adapter import, so `estate/adapters/postgres_estate_read.py` is not imported.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import DBAPIError, OperationalError

from assetops_backend.work.adapters.postgres_work_read import LinkReadPorts, _ReadTx
from assetops_backend.work.model import WorkStoreUnavailable

# A1Q Q5: verbatim estate predicate and order; no `known_at` predicate (W3 parity); inactive imported Sites included.
_IMPORTED_SITES = (
    "SELECT s.id, s.site_code, s.name, s.site_type, s.site_code_key FROM site s WHERE s.tenant_id = :t AND EXISTS ("
    "SELECT 1 FROM site_import i WHERE i.tenant_id = s.tenant_id AND i.site_id = s.id AND i.imported_at < :to) "
    "ORDER BY s.site_code_key, s.id")
# A1Q Q7: scoped request codes whose stored `incident_id` is this case, at the cutoff, with no window filter.
_LINKED_REQUEST_CODES = (
    "SELECT c.public_code FROM maintenance_work_request r JOIN work_case c ON c.tenant_id = r.tenant_id "
    "AND c.site_id = r.site_id AND c.id = r.id WHERE r.tenant_id = :t AND r.site_id = :s AND r.incident_id = :i "
    "AND c.kind = 'MAINTENANCE_REQUEST' AND c.created_at <= :k AND EXISTS (SELECT 1 FROM work_case_revision v "
    "WHERE v.tenant_id = c.tenant_id AND v.site_id = c.site_id AND v.case_id = c.id AND v.recorded_at <= :k) "
    "ORDER BY c.created_at, c.id")


class GlobalReadTx:
    """One global read: every method reads on the snapshot connection; per-Site reads go through W4 `_ReadTx`."""

    def __init__(self, c: Connection, read_at: datetime,
                 link_rows: Callable[[Connection, UUID, UUID, list[str]], list[Any]] | None,
                 ports: LinkReadPorts | None) -> None:
        self._c, self.read_at = c, read_at
        self._link_rows, self._ports = link_rows, ports

    def imported_sites(self, tenant_id: UUID, to: datetime) -> list[dict[str, Any]]:
        rows = self._c.execute(text(_IMPORTED_SITES), {"t": tenant_id, "to": to}).all()
        return [{"site_id": r[0], "site_code": r[1], "site_name": r[2], "site_type": r[3], "site_code_key": r[4]}
                for r in rows]

    def site(self, tenant_id: UUID, site_id: UUID, site_code: str) -> _ReadTx:
        return _ReadTx(self._c, tenant_id, site_id, site_code, self.read_at, self._link_rows, self._ports)

    def linked_request_codes(self, tenant_id: UUID, site_id: UUID, case_id: str, known_at: datetime) -> list[str]:
        return list(self._c.execute(text(_LINKED_REQUEST_CODES),
                                    {"t": tenant_id, "s": site_id, "i": case_id, "k": known_at}).scalars())


class PostgresGlobalWorkRead:
    def __init__(self, database_url: str | None, *,
                 link_rows: Callable[[Connection, UUID, UUID, list[str]], list[Any]] | None = None,
                 ports: LinkReadPorts | None = None, statement_timeout_ms: int = 30_000,
                 test_read_clock_override: Callable[[], datetime] | None = None) -> None:
        self._database_url = database_url
        self.test_read_clock_override = test_read_clock_override
        self._link_rows, self._ports = link_rows, ports
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

    def snapshot(self, work: Callable[[GlobalReadTx], Any]) -> Any:
        """One read-only REPEATABLE READ transaction; `work` receives the global read handle with the DB read time."""
        try:
            with self._connect().connect().execution_options(isolation_level="REPEATABLE READ") as c, c.begin():
                c.execute(text("SET TRANSACTION READ ONLY"))
                # A1Q Q6: one read instant per snapshot; a private test clock replaces only this upper bound.
                if self.test_read_clock_override is not None:
                    read_at = self.test_read_clock_override()
                    assert read_at.tzinfo is not None and read_at.utcoffset() == timedelta(0)
                else:
                    read_at = c.execute(text("SELECT clock_timestamp()")).scalar_one().astimezone(timezone.utc)
                return work(GlobalReadTx(c, read_at, self._link_rows, self._ports))
        except (OperationalError, DBAPIError) as error:
            raise WorkStoreUnavailable(f"The work store could not be read: {error.__class__.__name__}") from error
