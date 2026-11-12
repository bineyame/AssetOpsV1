"""UP-1: the `reading_upload` table (0061) and the ledger reads the upload page needs.

This adapter is the sole runtime writer of `reading_upload`, INSERT-only (D-UP.10; registered in
`tools/checks/configuration-persistence.ps1`; the 0061 trigger refuses UPDATE and DELETE).

- `latest_accepted_by_role`: the Site's latest `accepted_evidence.source_time` per role (the overlap rule).
- `insert` / `get`: the append-only upload row.
- `progress`: "Accepted n of m" counts the Site's `accepted_evidence` rows carrying the upload's message IDs.
  "Analysed" is the injected `analysed(row)` read (D-UP.3); until that read is built the default never reports
  Analysed.
"""

from __future__ import annotations

from datetime import datetime
from typing import Callable, Sequence
from uuid import UUID

from sqlalchemy import bindparam, create_engine, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.types import Text

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


def _never_analysed(row: UploadRow) -> bool:
    return False


class PostgresReadingUploadStore:
    def __init__(self, url: str, analysed: Callable[[UploadRow], bool] = _never_analysed) -> None:
        self._engine = create_engine(url, pool_pre_ping=True)
        self._analysed = analysed

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
        with self._engine.connect() as c:
            accepted = int(c.execute(_ACCEPTED_COUNT, {"t": row.tenant_id, "s": row.site_id,
                                                       "ids": list(row.message_ids)}).scalar_one())
        done = accepted >= len(row.message_ids) and self._analysed(row)
        return Progress(accepted=accepted, analysed=done)
