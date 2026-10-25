"""W6-01a/b/c/e: the read-only global work reader (A1Q G1/G2; a rule-8 named PostgreSQL reader, never a writer).

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
# Post-W6 W6 Q4 (R359): the same selection also yields each request's ID for its exact Overview destination.
_LINKED_REQUEST_CODES = (
    "SELECT c.public_code, CAST(c.id AS text) FROM maintenance_work_request r JOIN work_case c "
    "ON c.tenant_id = r.tenant_id AND c.site_id = r.site_id AND c.id = r.id "
    "WHERE r.tenant_id = :t AND r.site_id = :s AND r.incident_id = :i "
    "AND c.kind = 'MAINTENANCE_REQUEST' AND c.created_at <= :k AND EXISTS (SELECT 1 FROM work_case_revision v "
    "WHERE v.tenant_id = c.tenant_id AND v.site_id = c.site_id AND v.case_id = c.id AND v.recorded_at <= :k) "
    "ORDER BY c.created_at, c.id")

# B1 (P-B1-10): DRAFT plan roots whose own root `occurred_at` is in `[from, to)` and whose root is recorded by K, each
# with the last head of its lineage recorded by K by `(recorded_at, id)`; the Asset label inputs follow `_ELIGIBLE`.
_PLANS = (
    "SELECT CAST(r.id AS text) AS root_id, r.public_code AS root_code, r.occurred_at AS root_occurred_at, "
    "r.recorded_at AS root_recorded_at, CAST(h.id AS text) AS head_id, h.title, h.trigger_kind, h.next_due_at, "
    "h.next_due_hours, h.state, CAST(h.asset_id AS text) AS asset_id, h.occurred_at, h.recorded_at, "
    "CAST(h.supersedes_plan_id AS text) AS supersedes_plan_id, h.correction_reason, a.asset_code, a.asset_type "
    "FROM maintenance_plan r JOIN LATERAL (SELECT * FROM maintenance_plan p WHERE p.tenant_id = r.tenant_id "
    "AND p.site_id = r.site_id AND p.canonical_plan_id = r.id AND p.recorded_at <= :k "
    "ORDER BY p.recorded_at DESC, p.id DESC LIMIT 1) h ON true "
    "LEFT JOIN asset a ON a.tenant_id = h.tenant_id AND a.site_id = h.site_id AND a.id = h.asset_id "
    "WHERE r.tenant_id = :t AND r.site_id = :s AND r.supersedes_plan_id IS NULL AND r.canonical_plan_id = r.id "
    "AND r.occurred_at >= :lo AND r.occurred_at < :hi AND r.recorded_at <= :k")

# W6-01c C1 (pre-flight ruling "C1 outer wire and selection"): operational-record roots whose immutable root
# `case_id` is this request and that are recorded by K, each with its latest correction head recorded by K by
# `(recorded_at, id)` (the head may name another case; a later head never admits a root). Ordered by root occurrence.
_CASE_OPERATIONAL = (
    "SELECT CAST(r.id AS text) AS canonical_record_id, r.public_code AS code, r.occurred_at AS root_occurred_at, "
    "CAST(h.id AS text) AS head_id, h.kind, h.body, h.occurred_at, h.recorded_at "
    "FROM operational_record r JOIN LATERAL (SELECT * FROM operational_record p WHERE p.tenant_id = r.tenant_id "
    "AND p.site_id = r.site_id AND p.canonical_record_id = r.id AND p.recorded_at <= :k "
    "ORDER BY p.recorded_at DESC, p.id DESC LIMIT 1) h ON true "
    "WHERE r.tenant_id = :t AND r.site_id = :s AND r.supersedes_record_id IS NULL AND r.canonical_record_id = r.id "
    "AND r.case_id = :c AND r.recorded_at <= :k ORDER BY r.occurred_at, r.id")
# W6-01e E1 (P-E1-3): operational-record roots whose immutable root `occurred_at` is in `[from, to)` and that are
# recorded by K, each with its latest correction head recorded by K by `(recorded_at, id)`, which supplies every
# displayed field except the root code and occurrence (the C1 `_CASE_OPERATIONAL` root/head shape).
_OPERATIONAL = (
    "SELECT CAST(r.id AS text) AS root_id, r.public_code AS root_code, r.occurred_at AS root_occurred_at, "
    "CAST(h.id AS text) AS head_id, h.kind, h.body, h.occurred_at, h.recorded_at, h.period_end, h.actor_kind, "
    "h.actor_id, h.quantity, h.unit, h.source_document_sha256, CAST(h.case_id AS text) AS case_id, h.state, "
    "CAST(h.supersedes_record_id AS text) AS supersedes_record_id, h.correction_reason "
    "FROM operational_record r JOIN LATERAL (SELECT * FROM operational_record p WHERE p.tenant_id = r.tenant_id "
    "AND p.site_id = r.site_id AND p.canonical_record_id = r.id AND p.recorded_at <= :k "
    "ORDER BY p.recorded_at DESC, p.id DESC LIMIT 1) h ON true "
    "WHERE r.tenant_id = :t AND r.site_id = :s AND r.supersedes_record_id IS NULL AND r.canonical_record_id = r.id "
    "AND r.occurred_at >= :lo AND r.occurred_at < :hi AND r.recorded_at <= :k")
# Post-W6 W6 Q10 (R366): the stored public `ACT-` code of each linked Action root, W1 `action` or domain
# `domain_action` (one shared code namespace), scoped to this tenant and Site. Codes are immutable root values.
_ACTION_CODES = (
    "SELECT CAST(a.id AS text), a.action_code FROM action a WHERE a.tenant_id = :t AND a.site_id = :s "
    "AND CAST(a.id AS text) = ANY(:ids) UNION ALL SELECT CAST(d.id AS text), d.action_code FROM domain_action d "
    "WHERE d.tenant_id = :t AND d.site_id = :s AND CAST(d.id AS text) = ANY(:ids)")
# Post-W6 W6 Q2/Q3 (R352/R353): the selected Site's stored `site_type`, for the detail domain and Site home.
_SITE_TYPE = "SELECT site_type FROM site WHERE tenant_id = :t AND id = :s"
# W6-01c C1: the scoped Asset code/type of a case's stored `asset_id` (the W4 `_ELIGIBLE` label inputs).
_ASSET = "SELECT asset_code, asset_type FROM asset WHERE tenant_id = :t AND site_id = :s AND id = :a"


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

    def linked_requests(self, tenant_id: UUID, site_id: UUID, case_id: str,
                        known_at: datetime) -> list[dict[str, str]]:
        """A1Q Q7 order `(created_at, id)`: `{code, id}` of each scoped request linked to this incident at K."""
        rows = self._c.execute(text(_LINKED_REQUEST_CODES), {"t": tenant_id, "s": site_id, "i": case_id, "k": known_at})
        return [{"code": r[0], "id": str(r[1]).lower()} for r in rows]

    def linked_request_codes(self, tenant_id: UUID, site_id: UUID, case_id: str, known_at: datetime) -> list[str]:
        return [r["code"] for r in self.linked_requests(tenant_id, site_id, case_id, known_at)]

    def action_codes(self, tenant_id: UUID, site_id: UUID, action_ids: list[str]) -> dict[str, str]:
        """Post-W6 W6 Q10: `{action_id: ACT-code}` for the stored Action roots among `action_ids` at this Site."""
        if not action_ids:
            return {}
        rows = self._c.execute(text(_ACTION_CODES), {"t": tenant_id, "s": site_id,
                                                     "ids": sorted({str(x).lower() for x in action_ids})})
        return {str(r[0]).lower(): r[1] for r in rows}

    def site_type(self, tenant_id: UUID, site_id: UUID) -> str | None:
        return self._c.execute(text(_SITE_TYPE), {"t": tenant_id, "s": site_id}).scalar()

    def plans(self, tenant_id: UUID, site_id: UUID, lo: datetime, hi: datetime,
              known_at: datetime) -> list[dict[str, Any]]:
        return [dict(r._mapping) for r in self._c.execute(
            text(_PLANS), {"t": tenant_id, "s": site_id, "lo": lo, "hi": hi, "k": known_at})]

    def case_operational_records(self, tenant_id: UUID, site_id: UUID, case_id: str,
                                 known_at: datetime) -> list[dict[str, Any]]:
        return [dict(r._mapping) for r in self._c.execute(
            text(_CASE_OPERATIONAL), {"t": tenant_id, "s": site_id, "c": case_id, "k": known_at})]

    def operational_records(self, tenant_id: UUID, site_id: UUID, lo: datetime, hi: datetime,
                            known_at: datetime) -> list[dict[str, Any]]:
        return [dict(r._mapping) for r in self._c.execute(
            text(_OPERATIONAL), {"t": tenant_id, "s": site_id, "lo": lo, "hi": hi, "k": known_at})]

    def asset(self, tenant_id: UUID, site_id: UUID, asset_id: str) -> dict[str, Any] | None:
        row = self._c.execute(text(_ASSET), {"t": tenant_id, "s": site_id, "a": asset_id}).first()
        return None if row is None else {"code": row[0], "type": row[1]}


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
