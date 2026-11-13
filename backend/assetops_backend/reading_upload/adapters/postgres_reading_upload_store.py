"""UP-1: the `reading_upload` table (0061) and the ledger reads the upload page needs.

This adapter is the sole runtime writer of `reading_upload`, INSERT-only (D-UP.10; registered in
`tools/checks/configuration-persistence.ps1`; the 0061 trigger refuses UPDATE and DELETE).

- `latest_accepted_by_role`: the Site's latest `accepted_evidence.source_time` per role (the overlap rule).
- `insert` / `get`: the append-only upload row.
- `progress`: "Accepted n of m" counts the Site's `accepted_evidence` rows carrying the upload's message IDs.
  Once every admitted reading is accepted, the analysis read (D-UP.3) decides Analysed / Still processing / Not
  analysed: an `analytic_run` (dispatch, DEFAULT, `job_id IS NOT NULL`) whose window covers the first interval start
  and whose `knowledge_cutoff` is at or after the latest ACCEPTED disposition `decided_at` of the upload's message
  IDs; no PENDING/LEASED `recompute_job` in any domain over [period_start, period_end); a FAILED one there is "Not
  analysed". Jobs are never keyed on `cause_evidence_id` (they coalesce).
"""

from __future__ import annotations

from datetime import datetime
from typing import Sequence
from uuid import UUID

from sqlalchemy import bindparam, create_engine, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.types import Text

from assetops_backend.analytics.dispatch import ANALYTIC_ID
from assetops_backend.reading_upload.service import Progress, UploadRow

_COLUMNS = ("id", "tenant_id", "site_id", "file_name", "file_sha256", "profile_sha256", "state", "refusal_code",
            "refusal_field", "refusal_detail", "period_start", "period_end", "row_count", "reading_count",
            "blank_count", "admitted_count", "held_count", "message_ids", "session_ref", "entered_by")

_INSERT = text(
    "INSERT INTO reading_upload (id, tenant_id, site_id, file_name, file_sha256, profile_sha256, state, "
    "refusal_code, refusal_field, refusal_detail, period_start, period_end, row_count, reading_count, "
    "blank_count, admitted_count, held_count, message_ids, session_ref, entered_by) "
    "VALUES (:id, :tenant_id, :site_id, :file_name, :file_sha256, :profile_sha256, :state, "
    ":refusal_code, :refusal_field, :refusal_detail, :period_start, :period_end, :row_count, :reading_count, "
    ":blank_count, :admitted_count, :held_count, :message_ids, :session_ref, :entered_by) "
    "RETURNING entered_at"
).bindparams(bindparam("message_ids", type_=ARRAY(Text)))

_GET = text(
    "SELECT id, tenant_id, site_id, file_name, file_sha256, profile_sha256, state, refusal_code, refusal_field, "
    "refusal_detail, period_start, period_end, row_count, reading_count, blank_count, admitted_count, held_count, "
    "message_ids, session_ref, entered_by, entered_at FROM reading_upload "
    "WHERE tenant_id = :t AND site_id = :s AND id = :id"
)

_LATEST_BY_ROLE = text(
    "SELECT role, max(source_time) AS latest FROM accepted_evidence "
    "WHERE tenant_id = :t AND site_id = :s AND role IN :roles GROUP BY role"
).bindparams(bindparam("roles", expanding=True))

_ACCEPTED_COUNT = text(
    "SELECT count(*) FROM accepted_evidence WHERE tenant_id = :t AND site_id = :s AND message_id = ANY(:ids)"
).bindparams(bindparam("ids", type_=ARRAY(Text)))

_ANALYSIS = text(
    "WITH decided AS (SELECT max(d.decided_at) AS at FROM ingestion_disposition d "
    "JOIN accepted_evidence e ON e.tenant_id = d.tenant_id AND e.site_id = d.site_id AND e.id = d.accepted_evidence_id "
    "WHERE d.tenant_id = :t AND d.site_id = :s AND d.decision = 'ACCEPTED' AND e.message_id = ANY(:ids)) "
    "SELECT EXISTS (SELECT 1 FROM analytic_run r, decided WHERE r.tenant_id = :t AND r.site_id = :s "
    "AND r.analytic_id = :a AND r.selection = 'DEFAULT' AND r.job_id IS NOT NULL "
    "AND r.window_start <= :lo AND r.window_end > :lo AND r.knowledge_cutoff >= decided.at) AS ran, "
    "EXISTS (SELECT 1 FROM recompute_job j WHERE j.tenant_id = :t AND j.site_id = :s "
    "AND j.status IN ('PENDING', 'LEASED') AND j.window_start < :hi AND j.window_end > :lo) AS pending, "
    "EXISTS (SELECT 1 FROM recompute_job j WHERE j.tenant_id = :t AND j.site_id = :s "
    "AND j.status = 'FAILED' AND j.window_start < :hi AND j.window_end > :lo) AS failed, "
    "(SELECT to_char(:lo AT TIME ZONE z.timezone, 'YYYY-MM-DD') FROM site z WHERE z.tenant_id = :t AND z.id = :s) "
    "AS board_day"
).bindparams(bindparam("ids", type_=ARRAY(Text)))


class PostgresReadingUploadStore:
    def __init__(self, url: str) -> None:
        self._engine = create_engine(url, pool_pre_ping=True)

    def dispose(self) -> None:
        self._engine.dispose()

    def latest_accepted_by_role(self, tenant_id: UUID, site_id: UUID, roles: Sequence[str]) -> dict[str, datetime]:
        if not roles:
            return {}
        with self._engine.connect() as c:
            found = c.execute(_LATEST_BY_ROLE, {"t": tenant_id, "s": site_id, "roles": list(roles)})
            return {r.role: r.latest for r in found}

    def insert(self, row: UploadRow) -> UploadRow:
        values = {name: getattr(row, name) for name in _COLUMNS}
        values["message_ids"] = list(row.message_ids)
        with self._engine.begin() as c:
            entered_at = c.execute(_INSERT, values).scalar_one()
        return UploadRow(**{**{name: getattr(row, name) for name in _COLUMNS}, "entered_at": entered_at})

    def get(self, tenant_id: UUID, site_id: UUID, upload_id: UUID) -> UploadRow | None:
        with self._engine.connect() as c:
            found = c.execute(_GET, {"t": tenant_id, "s": site_id, "id": upload_id}).mappings().first()
        if found is None:
            return None
        values = dict(found)
        values["message_ids"] = tuple(values["message_ids"] or ())
        return UploadRow(**values)

    def progress(self, row: UploadRow) -> Progress:
        if not row.message_ids:
            return Progress(accepted=0, analysed=False)
        keys = {"t": row.tenant_id, "s": row.site_id, "ids": list(row.message_ids)}
        with self._engine.connect() as c:
            accepted = int(c.execute(_ACCEPTED_COUNT, keys).scalar_one())
            if accepted < len(row.message_ids) or row.period_start is None or row.period_end is None:
                return Progress(accepted=accepted, analysed=False)
            found = c.execute(_ANALYSIS, {**keys, "a": ANALYTIC_ID, "lo": row.period_start,
                                          "hi": row.period_end}).one()
        if found.pending:
            return Progress(accepted=accepted, analysed=False, board_day=found.board_day)
        return Progress(accepted=accepted, analysed=bool(found.ran) and not found.failed, failed=bool(found.failed),
                        board_day=found.board_day)
