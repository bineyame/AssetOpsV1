"""PostgreSQL trial cost-check store (OUT-E E3, migration 0037).

The sole writer of `trial_cost_comparison_revision` (configuration-persistence guard): INSERT only, never an UPDATE,
DELETE, upsert or DDL (the 0037 trigger refuses UPDATE and DELETE). One append runs in one transaction under the
outcome's advisory lock:

- the same `(action_id, idempotency_key)` with the same `payload_sha256` answers the stored row (`inserted=False`);
  a different payload under that key is refused `IDEMPOTENCY_KEY_REUSED`;
- the same `(verification_outcome_id, basis_sha256)` answers the stored row;
- otherwise revision head+1 is inserted, superseding the head, at `clock_timestamp()`.
"""

from __future__ import annotations

import json
from typing import Any, Mapping
from uuid import UUID, uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import OperationalError, ProgrammingError

COLUMNS = ("id, tenant_id, site_id, action_id, verification_outcome_id, revision_no, supersedes_revision_id, "
           "formula, state, reason, result, intervention_cost, price_revision_id, basis_sha256, actor_kind, actor_id, "
           "source_channel, authorization_basis, triggering_service, triggering_fixture, idempotency_key, "
           "payload_sha256, recorded_at")
#: what the caller supplies (the store adds id, revision_no, supersedes_revision_id and recorded_at)
FIELDS = ("tenant_id", "site_id", "action_id", "verification_outcome_id", "formula", "state", "reason", "result",
          "intervention_cost", "price_revision_id", "basis_sha256", "actor_kind", "actor_id", "source_channel",
          "authorization_basis", "triggering_service", "triggering_fixture", "idempotency_key", "payload_sha256")


class TrialComparisonStoreUnavailable(RuntimeError):
    pass


class TrialComparisonRefused(Exception):
    def __init__(self, status: int, code: str, detail: str) -> None:
        super().__init__(detail)
        self.status, self.code, self.detail = status, code, detail


def _row(r) -> dict[str, Any]:
    return dict(r._mapping)


class PostgresTrialComparisonStore:
    def __init__(self, database_url: str | None) -> None:
        self._database_url = database_url
        self._engine: Engine | None = None

    def _connect(self) -> Engine:
        if not self._database_url:
            raise TrialComparisonStoreUnavailable("DATABASE_URL is not set, so the cost-check store cannot be reached.")
        if self._engine is None:
            self._engine = create_engine(self._database_url, pool_pre_ping=True)
        return self._engine

    def dispose(self) -> None:
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None

    def _run(self, work):
        try:
            with self._connect().connect() as c:
                with c.begin():
                    return work(c)
        except (OperationalError, ProgrammingError) as error:
            raise TrialComparisonStoreUnavailable(f"The cost-check store failed: {error.orig}") from error

    def latest(self, tenant_id: UUID, site_id: UUID, outcome_id: UUID) -> dict[str, Any] | None:
        """The newest revision of this outcome's cost check, or None."""
        r = self._run(lambda c: c.execute(text(
            f"SELECT {COLUMNS} FROM trial_cost_comparison_revision WHERE tenant_id = :t AND site_id = :s "
            "AND verification_outcome_id = :o ORDER BY revision_no DESC LIMIT 1"),
            {"t": tenant_id, "s": site_id, "o": outcome_id}).first())
        return None if r is None else _row(r)

    def history(self, tenant_id: UUID, site_id: UUID, action_id: UUID) -> list[dict[str, Any]]:
        return self._run(lambda c: [_row(r) for r in c.execute(text(
            f"SELECT {COLUMNS} FROM trial_cost_comparison_revision WHERE tenant_id = :t AND site_id = :s "
            "AND action_id = :a ORDER BY recorded_at, id"), {"t": tenant_id, "s": site_id, "a": action_id})])

    def append(self, row: Mapping[str, Any]) -> tuple[dict[str, Any], bool]:
        """(stored row, inserted)."""
        values = {k: row[k] for k in FIELDS}

        def work(c: Connection) -> tuple[dict[str, Any], bool]:
            c.execute(text("SELECT pg_advisory_xact_lock(hashtextextended('trial_cost_comparison:' || :o, 0))"),
                      {"o": str(values["verification_outcome_id"])})
            same = c.execute(text(f"SELECT {COLUMNS} FROM trial_cost_comparison_revision WHERE action_id = :a "
                                  "AND idempotency_key = :k"),
                             {"a": values["action_id"], "k": values["idempotency_key"]}).first()
            if same is not None:
                if same.payload_sha256 != values["payload_sha256"]:
                    raise TrialComparisonRefused(409, "IDEMPOTENCY_KEY_REUSED",
                                                 f"Idempotency key {values['idempotency_key']!r} already recorded "
                                                 f"cost check {same.id} with a different payload.")
                return _row(same), False
            basis = c.execute(text(f"SELECT {COLUMNS} FROM trial_cost_comparison_revision "
                                   "WHERE verification_outcome_id = :o AND basis_sha256 = :b"),
                              {"o": values["verification_outcome_id"], "b": values["basis_sha256"]}).first()
            if basis is not None:
                return _row(basis), False
            head = c.execute(text("SELECT id, revision_no FROM trial_cost_comparison_revision "
                                  "WHERE verification_outcome_id = :o ORDER BY revision_no DESC LIMIT 1"),
                             {"o": values["verification_outcome_id"]}).first()
            stored = c.execute(text(
                f"INSERT INTO trial_cost_comparison_revision ({COLUMNS}) VALUES (:id, :tenant_id, :site_id, "
                ":action_id, :verification_outcome_id, :revision_no, :supersedes_revision_id, :formula, :state, "
                ":reason, CAST(:result AS jsonb), CAST(:intervention_cost AS jsonb), :price_revision_id, "
                ":basis_sha256, :actor_kind, :actor_id, :source_channel, :authorization_basis, :triggering_service, "
                ":triggering_fixture, :idempotency_key, :payload_sha256, clock_timestamp()) "
                f"RETURNING {COLUMNS}"),
                {**values, "id": uuid4(), "revision_no": 1 if head is None else head.revision_no + 1,
                 "supersedes_revision_id": None if head is None else head.id,
                 "result": json.dumps(values["result"], sort_keys=True),
                 "intervention_cost": json.dumps(values["intervention_cost"], sort_keys=True)}).one()
            return _row(stored), True

        return self._run(work)
