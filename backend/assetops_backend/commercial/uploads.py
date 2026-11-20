"""3A2 (spec §3.2 to §3.4, §5; D-3A2.4 to D-3A2.15): check, submit, accept and decline an operator's export.

- **Check** (`dry_run=true`) reads the file with its reader, keeps the records 2a accepts, pseudonymises them, and
  runs the commercial store as a dry run on that kept batch. It answers what the file would add, correct, already
  hold and refuse, row by row. Nothing is written.
- **Submit** does the same and keeps the upload row (state WAITING): the file's name, SHA-256 and size (never its
  bytes, D-3A2.10), the pseudonymised kept batch, `kept_index`, the refusal arrays and the store basis (D-3A2.13).
  The commercial store is not written (D-3A2.4).
- **Accept** ingests the kept batch with an `Acceptance`, so the store's rows and the decision row are written in one
  transaction under the tenant's lock, and only if the store state equals the checked basis (else `UPLOAD_STALE`).
- **Decline** writes the decision only.

A refused record is dropped before anything is kept; only (file index, code, cut path) remain (D-3A2.14). No answer,
log or error carries a record value, a ref or the batch (D-3A1.10): refusals raised here carry codes, cut paths,
counts and the declared provenance only.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable
from uuid import UUID, uuid4

from assetops_backend.commercial.model import (Acceptance, HeldUpload, UploadAlreadyDecided, UploadDecisionRow,
                                               UploadRecord, UploadRow, UploadStale)
from assetops_backend.commercial.pseudonym import (PseudonymKeyMissing, PseudonymKeys, PseudonymKeyUnusable,
                                                   cut_path, pseudonymise)
from assetops_backend.commercial.readers import DEFAULT_READER, READERS, ReadContext, ReadResult, SourceReader
from assetops_backend.commercial.service import CommercialRecords
from assetops_backend.commercial.store import CommercialStore
from assetops_backend.i18n import Message, message, render
from assetops_contracts.canonical import CanonicalRecordV1, CanonicalRefused, parse_batch

MAX_UPLOAD_BYTES = 8 * 2**20
MAX_LISTED = 50
MAX_REFUSALS_SHOWN = 200
MAX_REASON = 500
#: D-3A2.6: what a path admits, by the real-data switch.
ADMITTED = {False: frozenset({"source-emulated", "demo-simulated"}), True: frozenset({"observed-financial"})}

#: Each refusal code and its words key (`commercial_upload.<key>`).
_WORDS = {
    "UPLOAD_READER_UNKNOWN": "reader_unknown",
    "UPLOAD_UNSUPPORTED_TYPE": "unsupported_type",
    "FILE_TOO_LARGE": "too_large",
    "UPLOAD_FILE_REFUSED": "file_refused",
    "UPLOAD_TENANT_MISMATCH": "tenant_mismatch",
    "UPLOAD_PROVENANCE_NOT_ALLOWED": "provenance_not_allowed",
    "PSEUDONYM_KEY_MISSING": "key_missing",
    "PSEUDONYM_KEY_UNUSABLE": "key_unusable",
    "COMMERCIAL_STORE_FAULT": "store_fault",
    "UPLOAD_NOTHING_NEW": "nothing_new",
    "UPLOAD_NOT_FOUND": "not_found",
    "UPLOAD_ALREADY_DECIDED": "already_decided",
    "UPLOAD_STALE": "stale",
    "UPLOAD_DECISION_INVALID": "decision_invalid",
}


def has_control_character(text: str) -> bool:
    """F3: a character below U+0020 or U+007F (NUL included) is refused in the two free-text inputs."""
    return any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in text)


def reason_words(code: str) -> Message:
    return message(f"commercial_upload.reason.{code.lower()}")


class UploadRefused(Exception):
    """A refusal the routes answer as `{"code", "message", "words", "params"}`. It carries no record value."""

    def __init__(self, status: int, code: str, params: dict[str, Any] | None = None,
                 words: Message | None = None) -> None:
        super().__init__(code)
        self.status = status
        self.code = code
        self.params = dict(params or {})
        self.words = words if words is not None else message(f"commercial_upload.{_WORDS[code]}", **self.params)


@dataclass(frozen=True)
class UploadScope:
    """The path's scope: a Site (`site_id`, `site_code`) or the organisation (both None)."""
    site_id: UUID | None
    site_code: str | None


@dataclass(frozen=True)
class Actor:
    person_id: UUID
    role: str


@dataclass(frozen=True)
class _Checked:
    reader: SourceReader
    file_sha256: str
    file_bytes: int
    source_type: str
    source_system: str
    provenance: str
    batch: bytes
    kept_index: tuple[int, ...]
    basis_sha256: str
    rows: tuple[int, ...] | None
    record_count: int
    new: int
    revised: int
    unchanged: int
    refusals: tuple[tuple[int, str, str], ...]
    months: tuple[tuple[str | None, str], ...]


def _file_refused(reader: SourceReader, code: str, path: str) -> UploadRefused:
    field = reader.field_label(cut_path(code, path))
    return UploadRefused(422, "UPLOAD_FILE_REFUSED", {"code": code, "field": field},
                         message("commercial_upload.file_refused", field=field, reason=render(reason_words(code))))


def _counts(records: int, new: int, revised: int, unchanged: int, refused: int) -> dict[str, Any]:
    """D-3A2.18(a): the count sentence is served with the counts, wherever counts appear."""
    words = message("commercial_upload.summary", new=new, revised=revised, unchanged=unchanged, refused=refused)
    return {"records": records, "new": new, "revised": revised, "unchanged": unchanged, "refused": refused,
            "words": words, "text": render(words)}


def _person(person_id: UUID, name: str | None) -> dict[str, str | None]:
    return {"person_id": str(person_id), "display_name": name}


def _with_text(words: Message) -> dict[str, Any]:
    return {"words": words, "text": render(words)}


class CommercialUploads:
    def __init__(self, records: CommercialRecords, store: CommercialStore, keys: PseudonymKeys, *,
                 clock: Callable[[], datetime], real_data: bool) -> None:
        self._records = records
        self._store = store
        self._keys = keys
        self._clock = clock
        self._real_data = bool(real_data)

    # --- step 1: the reader -----------------------------------------------------------------------------------

    @staticmethod
    def reader(reader_id: str | None, media_type: str | None) -> SourceReader:
        """§3.2 step 1 before the body is read: an unknown reader (422), then the media type (415)."""
        reader = READERS.get(reader_id if reader_id is not None else DEFAULT_READER)
        if reader is None:
            raise UploadRefused(422, "UPLOAD_READER_UNKNOWN")
        if (media_type or "").split(";", 1)[0].strip().lower() not in reader.media_types:
            raise UploadRefused(415, "UPLOAD_UNSUPPORTED_TYPE")
        return reader

    # --- check and submit -------------------------------------------------------------------------------------

    def _check(self, tenant_id: UUID, scope: UploadScope, actor: Actor, data: bytes, reader_id: str | None,
               media_type: str | None) -> _Checked:
        reader = self.reader(reader_id, media_type)
        data = bytes(data)
        if len(data) > MAX_UPLOAD_BYTES:
            raise UploadRefused(413, "FILE_TOO_LARGE", {"limit_mb": MAX_UPLOAD_BYTES // 2**20})
        file_sha256 = hashlib.sha256(data).hexdigest()
        slug = self._store.tenant_slug(tenant_id)
        if slug is None:  # 3A3 (spec §2.4, P7): before reading, as the JSON reader's mismatch
            raise UploadRefused(422, "UPLOAD_TENANT_MISMATCH")
        refused: CanonicalRefused | None = None
        try:
            read: ReadResult = reader.read(data, context=ReadContext(slug, self._clock(), self._real_data))
            parsed = parse_batch(read.obj)
        except CanonicalRefused as error:
            refused = error
        if refused is not None:  # raised outside the handler: 2a's path may echo the operator's key text
            raise _file_refused(reader, refused.code, refused.path)
        batch = parsed.batch
        if batch.tenant_code != slug:
            raise UploadRefused(422, "UPLOAD_TENANT_MISMATCH")
        if batch.provenance not in ADMITTED[self._real_data]:
            raise UploadRefused(422, "UPLOAD_PROVENANCE_NOT_ALLOWED", {"provenance": batch.provenance})
        try:
            key = self._keys.key(tenant_id)
        except PseudonymKeyMissing:
            raise UploadRefused(409, "PSEUDONYM_KEY_MISSING") from None
        except PseudonymKeyUnusable:
            raise UploadRefused(503, "PSEUDONYM_KEY_UNUSABLE") from None

        refusals: list[tuple[int, str, str]] = []
        kept: list[int] = []
        if any(index not in range(len(parsed.outcomes)) for index in read.refused):
            raise UploadRefused(500, "COMMERCIAL_STORE_FAULT")  # 3A3 (spec §2.4): a reader bug
        for index, outcome in enumerate(parsed.outcomes):
            if index in read.refused:  # 3A3 (D-3A3.3): the reader's refusal wins over 2a's verdict
                code, path = read.refused[index]
                refusals.append((index, code, cut_path(code, path)))
            elif isinstance(outcome, CanonicalRefused):
                refusals.append((index, outcome.code, cut_path(outcome.code, outcome.path)))
            else:
                kept.append(index)
        raw_records = read.obj["records"]  # parse_batch accepted the envelope, so this is the file's record list
        obj2 = {name: ([pseudonymise(raw_records[i], key, read.personal_paths) for i in kept]
                       if name == "records" else value) for name, value in read.obj.items()}
        data2 = json.dumps(obj2, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

        result = self._records.ingest(tenant_id, data2, entered_by=f"person:{actor.person_id}", dry_run=True,
                                      site_scope=scope.site_id)
        if (result.state != "STORED" or len(result.outcomes) != len(kept) or result.basis_sha256 is None
                or any(o.code is not None and o.code.startswith("CANONICAL_") for o in result.outcomes)):
            raise UploadRefused(500, "COMMERCIAL_STORE_FAULT")
        count = {"NEW": 0, "REVISED": 0, "UNCHANGED": 0}
        months: set[tuple[str | None, str]] = set()
        for k, outcome in enumerate(result.outcomes):
            index = kept[k]
            if outcome.outcome == "REFUSED":
                refusals.append((index, outcome.code or "", outcome.path or "record"))
                continue
            count[outcome.outcome] += 1
            record = parsed.outcomes[index]
            period = record.clocks.get("recognition_period") if isinstance(record, CanonicalRecordV1) else None
            if outcome.outcome in ("NEW", "REVISED") and period is not None:
                months.add((record.site_code, period))
        refusals.sort(key=lambda r: r[0])
        ordered = tuple(sorted(months, key=lambda m: (m[0] is not None, m[0] or "", m[1])))
        return _Checked(reader, file_sha256, len(data), batch.source_type, batch.source_system, batch.provenance,
                        data2, tuple(kept), result.basis_sha256, read.rows, len(parsed.outcomes), count["NEW"],
                        count["REVISED"], count["UNCHANGED"], tuple(refusals), ordered)

    def check(self, tenant_id: UUID, scope: UploadScope, actor: Actor, data: bytes, *,
              reader_id: str | None = None, media_type: str | None = "application/json") -> dict[str, Any]:
        c = self._check(tenant_id, scope, actor, data, reader_id, media_type)
        return {"state": "CHECKED", "source_type": c.source_type, "source_system": c.source_system,
                "provenance": c.provenance,
                "counts": _counts(c.record_count, c.new, c.revised, c.unchanged, len(c.refusals)),
                "months": [{"site_code": s, "period": p} for s, p in c.months],
                **self._refusals(c.reader, c.rows, c.refusals),
                **_with_text(message("commercial_upload.state.checked"))}

    def submit(self, tenant_id: UUID, scope: UploadScope, actor: Actor, data: bytes, *, file_name: str,
               reader_id: str | None = None, media_type: str | None = "application/json") -> dict[str, Any]:
        c = self._check(tenant_id, scope, actor, data, reader_id, media_type)
        if c.new + c.revised == 0:
            raise UploadRefused(422, "UPLOAD_NOTHING_NEW")
        row = UploadRow(
            id=uuid4(), tenant_id=tenant_id, site_id=scope.site_id, file_name=file_name, file_sha256=c.file_sha256,
            file_bytes=c.file_bytes, reader=c.reader.id, source_type=c.source_type, source_system=c.source_system,
            provenance=c.provenance, batch=c.batch.decode("utf-8"), batch_sha256=hashlib.sha256(c.batch).hexdigest(),
            kept_index=c.kept_index, basis_sha256=c.basis_sha256, row_map=c.rows, record_count=c.record_count,
            new_count=c.new, revised_count=c.revised, unchanged_count=c.unchanged, refused_count=len(c.refusals),
            refusal_index=tuple(r[0] for r in c.refusals), refusal_code=tuple(r[1] for r in c.refusals),
            refusal_path=tuple(r[2] for r in c.refusals), month_site_code=tuple(m[0] for m in c.months),
            month_period=tuple(m[1] for m in c.months), submitted_by=actor.person_id, submitted_role=actor.role,
            submitted_at=self._clock())
        self._store.add_upload(row)
        return self.get(tenant_id, scope, str(row.id))

    # --- decide -----------------------------------------------------------------------------------------------

    def decide(self, tenant_id: UUID, scope: UploadScope, actor: Actor, upload_id: str, decision: str,
               reason: object = None) -> dict[str, Any]:
        if decision == "DECLINE":
            if (not isinstance(reason, str) or not 1 <= len(reason.strip()) <= MAX_REASON
                    or has_control_character(reason)):
                raise UploadRefused(422, "UPLOAD_DECISION_INVALID", {"field": "reason"})
            reason = reason.strip()
        elif decision == "ACCEPT":
            if reason is not None:
                raise UploadRefused(422, "UPLOAD_DECISION_INVALID", {"field": "reason"})
        else:
            raise UploadRefused(422, "UPLOAD_DECISION_INVALID", {"field": "decision"})
        record = self._load(tenant_id, scope, upload_id)
        if record.decision is not None:
            raise UploadRefused(409, "UPLOAD_ALREADY_DECIDED")
        upload = record.upload
        try:
            if decision == "ACCEPT":
                self._records.ingest(
                    tenant_id, upload.batch.encode("utf-8"), entered_by=f"person:{actor.person_id}", dry_run=False,
                    site_scope=upload.site_id,
                    acceptance=Acceptance(uuid4(), upload.id, actor.person_id, actor.role, upload.basis_sha256))
            else:
                self._store.write_decline(UploadDecisionRow(uuid4(), tenant_id, upload.id, "DECLINED", reason, None,
                                                            actor.person_id, actor.role, self._clock()))
        except UploadAlreadyDecided:
            raise UploadRefused(409, "UPLOAD_ALREADY_DECIDED") from None
        except UploadStale:
            raise UploadRefused(409, "UPLOAD_STALE") from None
        return self.get(tenant_id, scope, str(upload.id))

    # --- reads ------------------------------------------------------------------------------------------------

    def _load(self, tenant_id: UUID, scope: UploadScope, upload_id: str) -> UploadRecord:
        try:
            parsed = UUID(upload_id)
        except (ValueError, TypeError, AttributeError):
            raise UploadRefused(404, "UPLOAD_NOT_FOUND") from None
        record = self._store.upload(tenant_id, parsed)
        if record is None or record.upload.site_id != scope.site_id:
            raise UploadRefused(404, "UPLOAD_NOT_FOUND")
        return record

    def get(self, tenant_id: UUID, scope: UploadScope, upload_id: str) -> dict[str, Any]:
        record = self._load(tenant_id, scope, upload_id)
        u = record.upload
        reader = READERS.get(u.reader, READERS[DEFAULT_READER])
        refusals = tuple(zip(u.refusal_index, u.refusal_code, u.refusal_path))
        result = None
        if record.intake is not None:
            intake = record.intake.intake
            dropped = u.record_count - len(u.kept_index)  # the upload's 2a refusals, never sent to the store
            result = {"intake_id": str(intake.id), "state": intake.state,
                      "counts": _counts(intake.record_count + dropped, intake.new_count, intake.revised_count,
                                        intake.unchanged_count, intake.refused_count + dropped)}
        return {**self._summary(record, scope),
                "preview": _counts(u.record_count, u.new_count, u.revised_count, u.unchanged_count, u.refused_count),
                "months": [{"site_code": s, "period": p} for s, p in zip(u.month_site_code, u.month_period)],
                **self._refusals(reader, u.row_map, refusals), "result": result}

    def held(self, tenant_id: UUID) -> tuple[HeldUpload, ...]:
        """3A3 (spec §2.8; D-3A3.11): every upload the tenant holds (not declined), one read, no write."""
        return tuple(self._store.held_uploads(tenant_id))

    def list(self, tenant_id: UUID, scope: UploadScope) -> dict[str, Any]:
        records = self._store.uploads_in_scope(tenant_id, scope.site_id, MAX_LISTED)
        return {"uploads": [self._summary(r, scope) for r in records]}

    @staticmethod
    def _summary(record: UploadRecord, scope: UploadScope) -> dict[str, Any]:
        u, d = record.upload, record.decision
        if d is None:
            state, words = "WAITING", message("commercial_upload.state.waiting")
        elif d.decision == "ACCEPTED":
            state, words = "ACCEPTED", message("commercial_upload.state.accepted", name=record.decided_by_name or "")
        else:
            state, words = "DECLINED", message("commercial_upload.state.declined", name=record.decided_by_name or "",
                                               reason=d.reason or "")
        return {"upload_id": str(u.id), "scope": "SITE" if u.site_id is not None else "ORGANISATION",
                "site_code": scope.site_code if u.site_id is not None else None, "file_name": u.file_name,
                "file_sha256": u.file_sha256, "reader": u.reader, "source_type": u.source_type,
                "source_system": u.source_system, "provenance": u.provenance,
                "submitted_by": _person(u.submitted_by, record.submitted_by_name), "submitted_role": u.submitted_role,
                "submitted_at": u.submitted_at.isoformat(), "state": state,
                "decision": None if d is None else {"by": _person(d.decided_by, record.decided_by_name),
                                                    "role": d.decided_role, "at": d.decided_at.isoformat(),
                                                    "reason": d.reason},
                **_with_text(words)}

    @staticmethod
    def _refusals(reader: SourceReader, rows: tuple[int, ...] | None,
                  refusals: tuple[tuple[int, str, str], ...]) -> dict[str, Any]:
        shown = []
        for index, code, path in refusals:
            row = rows[index] if rows is not None else index + 1
            field = reader.field_label(path)
            words = reason_words(code)
            shown.append({"row": row, "field": field, "code": code, "words": words,
                          "text": render(message("commercial_upload.row_refused", row=row, field=field,
                                                 reason=render(words)))})
        shown.sort(key=lambda r: r["row"])
        return {"refusals": shown[:MAX_REFUSALS_SHOWN], "refusals_total": len(refusals)}
