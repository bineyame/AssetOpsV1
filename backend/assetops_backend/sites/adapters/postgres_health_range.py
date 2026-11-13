"""SR-6a (rev 10 §10.2 steps 2-3, D-SR.19/D-SR.23): the two grouped per-UTC-day reads of a mini-grid Site's Health
over a range, on the caller's connection (the estate snapshot's one REPEATABLE READ, READ ONLY transaction).

- Diagnostics per gateway per UTC day of receipt, `received_at <= k` (no disposition exists for them, D-SR.19).
- Accepted readings per source per UTC day of `COALESCE(interval_start, source_time)`, with the dispatch read's
  accepted-reading convention (`analytics/adapters/postgres_assessment_store.py` `_EVIDENCE`): the ACCEPTED
  disposition of the same batch and ordinal, decided at or before k. `last_received_at` is the receipt fact.
No reading body is read; nothing is written.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.engine import Connection

_DIAGNOSTICS = (
    "SELECT gateway_id, date_trunc('day', received_at AT TIME ZONE 'UTC') AS day, count(*) AS n, "
    "min(received_at) AS first_at, max(received_at) AS last_at FROM gateway_diagnostic "
    "WHERE tenant_id = :t AND site_id = :s AND received_at >= :lo AND received_at < :hi AND received_at <= :k "
    "GROUP BY 1, 2"
)
_READINGS = (
    "SELECT e.source_id, date_trunc('day', COALESCE(e.interval_start, e.source_time) AT TIME ZONE 'UTC') AS day, "
    "count(*) AS n, max(e.received_at) AS last_at "
    "FROM accepted_evidence e JOIN ingestion_disposition d ON d.batch_id = e.batch_id AND d.ordinal = e.ordinal "
    "WHERE e.tenant_id = :t AND e.site_id = :s AND d.decision = 'ACCEPTED' AND d.accepted_evidence_id = e.id "
    "AND d.decided_at <= :k AND COALESCE(e.interval_start, e.source_time) >= :lo "
    "AND COALESCE(e.interval_start, e.source_time) < :hi GROUP BY 1, 2"
)


def _day(value: Any) -> date:
    return value.date() if isinstance(value, datetime) else value


def health_range_counts(c: Connection, tenant_id: UUID, site_id: UUID, lo: datetime, hi: datetime, k: datetime
                        ) -> tuple[dict[tuple[str, date], dict[str, Any]], dict[tuple[str, date], dict[str, Any]]]:
    """`(diagnostics, readings)`: `{(gateway_id, day): {"n", "first_at", "last_at"}}` and
    `{(source_id, day): {"n", "last_at"}}`, ids as lower-case text, days as UTC dates."""
    params = {"t": tenant_id, "s": site_id, "lo": lo, "hi": hi, "k": k}
    diagnostics = {(str(r.gateway_id), _day(r.day)): {"n": int(r.n), "first_at": r.first_at, "last_at": r.last_at}
                   for r in c.execute(text(_DIAGNOSTICS), params)}
    readings = {(str(r.source_id), _day(r.day)): {"n": int(r.n), "last_at": r.last_at}
                for r in c.execute(text(_READINGS), params)}
    return diagnostics, readings
