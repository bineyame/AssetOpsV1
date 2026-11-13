"""UP-1 (rev 7 section 7.5, D-17N.5): check, preview and send one reading file for a Site; follow it afterwards.

The product never validates or admits a reading itself. Two ports do that outside this process:
- `FileChecker.check(data)`: the whole-file check of `assetops-generic-interval-csv/1` (the field CSV collector, run
  as its own process by the host; `field/` may not be imported here). It returns the dry-run preview or a refusal
  with one of the eight CSV codes.
- `ReadingSender.send(data)`: the same check, then one admission through the demo upload gateway's channel.

Order (spec 7.5 "Steps"): size, the file rules, then the overlap rule (`ALREADY_RECORDED`: any interval ending at or
before the Site's latest accepted reading for that role), then, unless `dry_run`, the send and one `reading_upload`
row. A dry run writes nothing. A refusal on confirm is recorded (state REFUSED) and admits nothing. Attribution is
the server-configured entry service (D-PRICE.1 precedent): "Uploaded by site admin"; the browser never names it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Mapping, Protocol, Sequence
from uuid import UUID, uuid4

from assetops_backend.i18n import Message, message

FORMAT = "assetops-generic-interval-csv/1"
MAX_BYTES = 2 * 1024 * 1024
#: The eight whole-file rules of TEL-06 (`assetops_field.export_csv.CSV_CODES`), restated: the product may not
#: import the field adapters. A test pins the two lists equal.
CSV_CODES = ("ENCODING", "EMPTY_FILE", "HEADER_MISMATCH", "INVALID_TIMING", "SPAN_MISMATCH",
             "DUPLICATE_ROW", "UNSORTED_ROWS", "INVALID_VALUE")
REFUSAL_CODES = CSV_CODES + ("ALREADY_RECORDED", "FILE_TOO_LARGE")
#: The read states, in order (spec 7.5): Checked is the dry run's answer; Refused and Held are outcomes.
STATES = ("CHECKED", "SENT", "ACCEPTED", "PROCESSING", "ANALYSED", "NOT_ANALYSED")
UPLOADED_BY_LABEL_KEY = "reading_upload.uploaded_by_site_admin"
STORED_STATES = ("SENT", "HELD", "REFUSED")


class UploadRefused(Exception):
    """A whole-request refusal: `status`, a stable `code` and its words."""

    def __init__(self, status: int, code: str, words: Message, extra: Mapping[str, Any] | None = None) -> None:
        super().__init__(code)
        self.status, self.code, self.words, self.extra = status, code, words, dict(extra or {})


class GatewayUnavailable(Exception):
    """The demo upload gateway (or its process) did not answer; nothing was recorded."""


@dataclass(frozen=True)
class FileRefusal:
    code: str
    field: str
    detail: str
    profile_sha256: str = ""


@dataclass(frozen=True)
class Preview:
    """The field process's dry-run preview (`assetops_field.csv_upload.preview`), as plain data."""

    profile_sha256: str
    file_sha256: str
    period_start: datetime
    period_end: datetime
    rows: int
    cells: int
    readings: int
    blanks: int
    columns: Sequence[Mapping[str, Any]]
    first_interval_end_by_role: Mapping[str, datetime]


@dataclass(frozen=True)
class Sent:
    session_ref: str
    admitted: int  # ADMITTED + ALREADY_ADMITTED
    held: int
    message_ids: Sequence[str]
    held_by_column: Mapping[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class UploadRow:
    id: UUID
    tenant_id: UUID
    site_id: UUID
    file_name: str
    file_sha256: str
    profile_sha256: str
    state: str
    refusal_code: str | None
    refusal_field: str | None
    refusal_detail: str | None
    period_start: datetime | None
    period_end: datetime | None
    row_count: int
    reading_count: int
    blank_count: int
    admitted_count: int
    held_count: int
    message_ids: Sequence[str]
    session_ref: str | None
    entered_by: str
    entered_at: datetime | None = None


@dataclass(frozen=True)
class Progress:
    accepted: int  # the Site's accepted_evidence rows carrying this upload's message IDs
    analysed: bool  # D-UP.3: an assessment run covers the upload and no work is left
    failed: bool = False  # D-UP.3: a FAILED recompute job overlaps the upload's span, none pending ("Not analysed")
    board_day: str | None = None  # the Site-local day of the first interval start (the "Analysed" link's ?date=)


class FileChecker(Protocol):
    def check(self, data: bytes) -> Preview | FileRefusal: ...


class ReadingSender(Protocol):
    def send(self, data: bytes) -> Sent | FileRefusal: ...


class ReadingUploadStore(Protocol):
    def latest_accepted_by_role(self, tenant_id: UUID, site_id: UUID, roles: Sequence[str]) -> dict[str, datetime]: ...
    def insert(self, row: UploadRow) -> UploadRow: ...
    def get(self, tenant_id: UUID, site_id: UUID, upload_id: UUID) -> UploadRow | None: ...
    def progress(self, row: UploadRow) -> Progress: ...
    def site_timezone(self, tenant_id: UUID, site_id: UUID) -> str: ...


def refusal_words(code: str, **params: Any) -> Message:
    """The refusal's catalogue message; a `role` param is given in words (`reading_upload.role.<role>`)."""
    if "role" in params:
        from assetops_backend.i18n import render
        from assetops_backend.i18n.messages import CATALOGUE

        key = f"reading_upload.role.{params['role']}"
        if key in CATALOGUE["en"]:
            params["role"] = render(message(key))
    return message(f"reading_upload.refused.{code.lower()}", **params)


def _iso(value: datetime | None) -> str | None:
    return None if value is None else value.isoformat().replace("+00:00", "Z")


def _row_number(field_text: str) -> str:
    """`rows[6].timestamp_utc` -> '7' (the file's data row, counted from 1); '' when the field is not a row."""
    if field_text.startswith("rows[") and "]" in field_text:
        return str(int(field_text[5:field_text.index("]")]) + 1)
    return ""


_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def _site_time(iso: str | None, zone: str) -> str:
    """`2026-11-16T20:45:00Z` -> '16 Nov, 23:45' in the Site's time zone (UTC when the zone is unknown)."""
    from zoneinfo import ZoneInfo

    if not iso:
        return ""
    try:
        at = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        local = at.astimezone(ZoneInfo(zone))
    except (ValueError, KeyError, OSError):
        return iso
    return f"{local.day} {_MONTHS[local.month - 1]}, {local:%H:%M}"


def _where(code: str, field_text: str | None) -> str | None:
    """The refusal's place in plain words: `row 7 · timestamp_utc` (the file's data row, counted from 1, and the
    column's name in the file), or `column 3` for a heading; a role in words for ALREADY_RECORDED. No system path."""
    if not field_text:
        return None
    if code == "ALREADY_RECORDED":
        from assetops_backend.i18n import render
        from assetops_backend.i18n.messages import CATALOGUE

        key = f"reading_upload.role_name.{field_text}"
        return render(message(key)) if key in CATALOGUE["en"] else None
    if field_text.startswith("rows[") and "]" in field_text:
        row = _row_number(field_text)
        column = field_text.split("].", 1)[1] if "]." in field_text else ""
        return f"row {row} · {column}" if column else f"row {row}"
    if field_text.startswith("header[") and field_text.endswith("]") and field_text[7:-1].isdigit():
        return f"column {int(field_text[7:-1]) + 1}"
    return None


def _refusal_text(code: str, field_text: str | None, detail: str | None, zone: str) -> Message:
    if code == "ALREADY_RECORDED":
        return refusal_words(code, role=field_text or "", latest=_site_time(detail, zone))
    if code == "INVALID_VALUE" and detail == "FIELD_TOO_LARGE":
        return message("reading_upload.refused.file_unreadable")
    return refusal_words(code, row=_row_number(field_text or ""), where=_where(code, field_text) or "")


class ReadingUploadService:
    def __init__(self, checker: FileChecker, sender: ReadingSender | None, store: ReadingUploadStore,
                 entered_by: str, new_id: Callable[[], UUID] = uuid4,
                 template: Callable[[], bytes] | None = None) -> None:
        self._checker, self._sender, self._store = checker, sender, store
        self._entered_by, self._new_id = entered_by, new_id
        self._template = template

    def template_csv(self) -> bytes | None:
        """The upload template (the profile's header row), from the host; None when none is configured."""
        return None if self._template is None else self._template()

    # --- POST -----------------------------------------------------------------------------------------------

    def upload(self, tenant_id: UUID, site_id: UUID, file_name: str, data: bytes, dry_run: bool) -> tuple[int, dict]:
        if len(data) > MAX_BYTES:
            raise UploadRefused(413, "FILE_TOO_LARGE", refusal_words("FILE_TOO_LARGE", limit_mb=MAX_BYTES // 2**20))
        checked = self._checker.check(data)
        if isinstance(checked, FileRefusal):
            return self._refuse_file(tenant_id, site_id, file_name, data, checked, None, dry_run)
        latest = self._store.latest_accepted_by_role(tenant_id, site_id, sorted(checked.first_interval_end_by_role))
        overlap = self._overlap(checked, latest)
        if overlap is not None:
            return self._refuse_file(tenant_id, site_id, file_name, data, overlap, checked, dry_run)
        if dry_run:
            # `latest_saved`: the Site's latest accepted reading over the file's roles (the page's confirm line).
            return 200, {"dry_run": True, "state": "CHECKED", "preview": self._preview_view(checked),
                         "latest_saved": _iso(max(latest.values())) if latest else None,
                         "words": message("reading_upload.checked", readings=checked.readings + checked.blanks)}
        if self._sender is None:
            raise GatewayUnavailable("no demo upload gateway is configured")
        sent = self._sender.send(data)
        if isinstance(sent, FileRefusal):  # the sender re-checks the same bytes; a refusal here admits nothing
            return self._refuse_file(tenant_id, site_id, file_name, data, sent, checked, dry_run)
        row = self._store.insert(UploadRow(
            id=self._new_id(), tenant_id=tenant_id, site_id=site_id, file_name=file_name,
            file_sha256=checked.file_sha256, profile_sha256=checked.profile_sha256,
            state="HELD" if sent.held else "SENT", refusal_code=None, refusal_field=None, refusal_detail=None,
            period_start=checked.period_start, period_end=checked.period_end, row_count=checked.rows,
            reading_count=checked.readings, blank_count=checked.blanks, admitted_count=sent.admitted,
            held_count=sent.held, message_ids=tuple(m for m in sent.message_ids if m), session_ref=sent.session_ref,
            entered_by=self._entered_by))
        return 201, self._status_view(row, Progress(accepted=0, analysed=False), checked, sent.held_by_column)

    @staticmethod
    def _overlap(checked: Preview, latest: Mapping[str, datetime]) -> FileRefusal | None:
        for role in sorted(checked.first_interval_end_by_role):
            if role in latest and checked.first_interval_end_by_role[role] <= latest[role]:
                return FileRefusal("ALREADY_RECORDED", role, _iso(latest[role]) or "")
        return None

    def _refuse_file(self, tenant_id: UUID, site_id: UUID, file_name: str, data: bytes, refusal: FileRefusal,
                     checked: Preview | None, dry_run: bool) -> tuple[int, dict]:
        import hashlib

        words = _refusal_text(refusal.code, refusal.field, refusal.detail,
                              self._store.site_timezone(tenant_id, site_id))
        body: dict[str, Any] = {"dry_run": dry_run, "state": "REFUSED", "refusal": {
            "code": refusal.code, "where": _where(refusal.code, refusal.field)}, "words": words}
        if not dry_run:
            row = self._store.insert(UploadRow(
                id=self._new_id(), tenant_id=tenant_id, site_id=site_id, file_name=file_name,
                file_sha256=hashlib.sha256(data).hexdigest(),
                profile_sha256=checked.profile_sha256 if checked else refusal.profile_sha256,
                state="REFUSED", refusal_code=refusal.code, refusal_field=refusal.field,
                refusal_detail=refusal.detail,
                period_start=checked.period_start if checked else None,
                period_end=checked.period_end if checked else None,
                row_count=checked.rows if checked else 0, reading_count=0, blank_count=0, admitted_count=0,
                held_count=0, message_ids=(), session_ref=None, entered_by=self._entered_by))
            body["upload_id"] = str(row.id)
        return 422, body

    # --- GET ------------------------------------------------------------------------------------------------

    def status(self, tenant_id: UUID, site_id: UUID, upload_id: UUID) -> tuple[int, dict]:
        row = self._store.get(tenant_id, site_id, upload_id)
        if row is None:
            raise UploadRefused(404, "UPLOAD_NOT_FOUND", message("reading_upload.not_found"))
        progress = Progress(0, False) if row.state == "REFUSED" else self._store.progress(row)
        return 200, self._status_view(row, progress)

    @staticmethod
    def derived_state(row: UploadRow, progress: Progress) -> str:
        if row.state == "REFUSED":
            return "REFUSED"
        if progress.accepted == 0:
            return "SENT"
        if progress.accepted < len(row.message_ids):
            return "ACCEPTED"
        if progress.failed:
            return "NOT_ANALYSED"
        return "ANALYSED" if progress.analysed else "PROCESSING"

    def _status_view(self, row: UploadRow, progress: Progress, checked: Preview | None = None,
                     held_by_column: Mapping[str, int] | None = None) -> dict:
        state = self.derived_state(row, progress)
        total = len(row.message_ids)
        view: dict[str, Any] = {
            "upload_id": str(row.id), "file_name": row.file_name, "file_sha256": row.file_sha256,
            "state": state, "held": row.held_count > 0,
            "counts": {"rows": row.row_count, "readings": row.reading_count, "blanks": row.blank_count,
                       "admitted": row.admitted_count, "held": row.held_count, "accepted": progress.accepted,
                       "accepted_of": total},
            "period_start": _iso(row.period_start), "period_end": _iso(row.period_end),
            "uploaded_by": message(UPLOADED_BY_LABEL_KEY), "entered_at": _iso(row.entered_at),
            "words": self._state_words(
                row, state, progress, total,
                self._store.site_timezone(row.tenant_id, row.site_id) if row.state == "REFUSED" else "UTC"),
        }
        if state == "ANALYSED" and progress.board_day:
            view["board_day"] = progress.board_day
        if row.state == "REFUSED":
            view["refusal"] = {"code": row.refusal_code, "where": _where(row.refusal_code or "", row.refusal_field)}
        if held_by_column:
            view["held_by_column"] = dict(held_by_column)
        if checked is not None:
            view["preview"] = self._preview_view(checked)
        return view

    @staticmethod
    def _state_words(row: UploadRow, state: str, progress: Progress, total: int, zone: str = "UTC") -> Message:
        if state == "REFUSED":
            return _refusal_text(row.refusal_code or "", row.refusal_field, row.refusal_detail, zone)
        if state == "ACCEPTED":
            return message("reading_upload.state.accepted", accepted=progress.accepted, total=total)
        if row.held_count and state in ("PROCESSING", "ANALYSED", "SENT"):
            return message(f"reading_upload.state.{state.lower()}_with_held", held=row.held_count,
                           accepted=progress.accepted, total=total)
        return message(f"reading_upload.state.{state.lower()}", accepted=progress.accepted, total=total)

    @staticmethod
    def _preview_view(checked: Preview) -> dict:
        return {"profile_sha256": checked.profile_sha256, "file_sha256": checked.file_sha256,
                "period_start": _iso(checked.period_start), "period_end": _iso(checked.period_end),
                "rows": checked.rows, "cells": checked.cells, "readings": checked.readings, "blanks": checked.blanks,
                "columns": [{**dict(c), "meter": message(f"reading_upload.meter.{c['device_id']}"),
                             "role_name": message(f"reading_upload.role_name.{c['role']}")} for c in checked.columns]}


def preview_from_document(document: Mapping[str, Any]) -> Preview:
    """The field process's JSON preview as a `Preview` (instants parsed as aware UTC)."""
    def at(text: str) -> datetime:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))

    return Preview(
        profile_sha256=document["profile_sha256"], file_sha256=document["file_sha256"],
        period_start=at(document["period_start"]), period_end=at(document["period_end"]),
        rows=int(document["rows"]), cells=int(document["cells"]), readings=int(document["readings"]),
        blanks=int(document["blanks"]), columns=tuple(document["columns"]),
        first_interval_end_by_role={k: at(v) for k, v in document["first_interval_end_by_role"].items()})
