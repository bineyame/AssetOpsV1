"""DS3 (spec `specs/DS3-bulk-loader/spec.md` §2.4; D-DS3.1, D-DS3.5, D-DS3.6, D-DS3.9, D-DS3.12): the bulk evidence load.

A trusted build tool's path into the evidence ledger, for the generated world's SIMULATED telemetry. Each batch goes
through the real path's own admission (`BatchIngestionService.admit`: size, parse, claims, batch-ID conflict, binding
set, basis) and the same pure `decide`, then `PostgresEvidenceLedger.bulk_admit` writes it in one transaction with one
set-based statement per table. Only clean batches are admitted: any rejected ordinal, colliding message, published
slot or Site type parity has not proved refuses the whole batch with nothing written and nothing recorded (a refused
bulk load is a build defect reported by the command, never product evidence).

Residual risk `R-TRUST`: there is no gateway credential here. What keeps the path off live and operator data is the
SIMULATED refusal and `permitted_database` (audit databases and harness clones on the test container only), checked by the
command before any connection. No HTTP module imports this module. The ledger is the PostgreSQL adapter
(`gateway_principal`, `bulk_admit`), composed by the caller through `evidence/composition.py`.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Sequence
from uuid import UUID

from assetops_backend.chain.events import S3_BRACKET, local_days
from assetops_backend.database_target import DatabaseTargetUnclear, database_target, is_operator_name
from assetops_backend.evidence.ledger import (
    BULK_REFUSALS,
    Accepted,
    BulkAdmissionRefused,
    EvidenceLedger,
    Rejected,
    decide,
)
from assetops_backend.evidence.ledger_service import BatchIngestionService, BatchRefused, utc_now
from assetops_contracts.ingestion_batch_v2 import MAX_BATCH_BYTES, BatchRejected, parse_canonical_batch_v2_text

BULK_LOAD_REFUSALS = frozenset({"BULK_NOT_SIMULATED", "BULK_UNKNOWN_GATEWAY", "BULK_REJECTED_ORDINAL",
                                "BULK_DATABASE_NOT_PERMITTED", "BULK_BATCH_GAP_DAYS",
                                "BULK_BATCH_TIME_UNREADABLE"}) | BULK_REFUSALS
#: The container `assetopsv1-postgres-1` publishes on this port (`docker-compose.yml`); D-DS3.12.
DEFAULT_PG_PORT = "55432"
_LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost"})
_AUDIT_NAME = re.compile(r"[a-z0-9_]+_audit[a-z0-9_]*")
#: A name `pg_harness.database_name` makes (DS3's own clones); a bare `*_test` name is not permitted (D-DS3.22).
_CLONE_NAME = re.compile(r"[a-z0-9_]+_pt[0-9a-f]+_[a-z0-9]+_test")
#: Tripwire over the allow: the walkthrough and serve databases are refused even if the allow is ever widened.
_DENIED_NAME = re.compile(r"walk|serve")


class BatchTimeUnreadable(ValueError):
    """An envelope instant that is not an offset-bearing ISO string; `field` names which (D-DS4.17)."""

    def __init__(self, field: str) -> None:
        super().__init__(field)
        self.field = field


def _instant(value: object, field: str) -> datetime:
    if not isinstance(value, str):
        raise BatchTimeUnreadable(field)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise BatchTimeUnreadable(field) from None
    if parsed.tzinfo is None:
        raise BatchTimeUnreadable(field)
    return parsed


def envelope_span(source_time: object, interval_start: object, interval_end: object) -> tuple[datetime, datetime]:
    """The envelope's `[COALESCE(interval_start, source_time), COALESCE(interval_end, source_time)]`, as the outbox's
    `reading.accepted` producer reads it (`0044_chain_events.py`; D-DS4.17)."""
    start = (_instant(interval_start, "interval_start") if interval_start is not None
             else _instant(source_time, "source_time"))
    end = (_instant(interval_end, "interval_end") if interval_end is not None
           else _instant(source_time, "source_time"))
    return start, end


def _days_local(timezone: str) -> Callable[[datetime, datetime], list]:
    return lambda a, b: local_days(a, b, timezone)


def _days_utc(a: datetime, b: datetime) -> list:
    return local_days(a - S3_BRACKET, max(b, a) + S3_BRACKET, "UTC")


def cover_gap(spans: Sequence[tuple[datetime, datetime]], timezone: str) -> str | None:
    """The first grain (`local`, then `utc`) where the envelopes' resolved days differ from the cover's days, using
    `chain.events`'s own day functions; `None` when both agree (D-DS4.17)."""
    if not spans:
        return None
    lo, hi = min(s for s, _ in spans), max(e for _, e in spans)
    for grain, days in (("local", _days_local(timezone)), ("utc", _days_utc)):
        union = set().union(*(days(s, e) for s, e in spans))
        cover = set(days(lo, hi))
        if union != cover:
            return f"{grain} cover {min(cover)}..{max(cover)} differs at {min(union ^ cover)}"
    return None


class BulkLoadRefused(Exception):
    """`code` is a `BULK_LOAD_REFUSALS` code or a real-path kind passed through verbatim (spec §2.4)."""

    def __init__(self, code: str, external_batch_id: str | None, detail: str) -> None:
        super().__init__(f"{code} {external_batch_id or '-'} {detail}")
        self.code = code
        self.external_batch_id = external_batch_id
        self.detail = detail


@dataclass(frozen=True)
class BulkLoaded:
    batches: int
    already_loaded: int
    envelopes: int


def _refuse(principal, external_batch_id, digest, received_at, status, kind, field, detail) -> BulkLoadRefused:
    """`admit`'s refusals, recording nothing (no `batch_refusal` row)."""
    return BulkLoadRefused(kind, external_batch_id, detail)


def _uuid(value: str) -> UUID | None:
    try:
        return UUID(value)
    except ValueError:
        return None


class BulkEvidenceLoad:
    def __init__(self, ledger: EvidenceLedger, *, clock: Callable[[], datetime] = utc_now) -> None:
        self.ledger = ledger
        self.clock = clock
        self._service = BatchIngestionService(ledger, clock)

    def load(self, raws: Sequence[bytes]) -> BulkLoaded:
        """Each batch in the given order, each its own transaction; the first refusal stops the load (earlier
        batches stay, and a re-run counts them as already loaded)."""
        batches = already = envelopes = 0
        for raw in raws:
            loaded = self._one(raw)
            batches += 1
            already += int(loaded.already_loaded)
            envelopes += loaded.total
        return BulkLoaded(batches, already, envelopes)

    def _one(self, raw: bytes):
        received_at = self.clock()
        # 1. Size and strict parse (submit's codes).
        if len(raw) > MAX_BATCH_BYTES:
            raise BulkLoadRefused("TOO_LARGE", None, f"more than {MAX_BATCH_BYTES} bytes")
        try:
            batch = parse_canonical_batch_v2_text(raw.decode("utf-8"))
        except UnicodeDecodeError:
            raise BulkLoadRefused("MALFORMED_TEXT", None, "the body is not UTF-8") from None
        except BatchRejected as error:
            raise BulkLoadRefused(error.kind, None, f"{error.field}: {error.detail}") from None
        # 2. SIMULATED only (D-DS3.6).
        if batch.source_mode != "SIMULATED":
            raise BulkLoadRefused("BULK_NOT_SIMULATED", batch.batch_id,
                                  f"the bulk path loads SIMULATED batches only, not {batch.source_mode}")
        # 3. The registered gateway at that Site.
        site_id, gateway_id = _uuid(batch.site_id), _uuid(batch.gateway_id)
        principal = None if site_id is None or gateway_id is None else self.ledger.gateway_principal(site_id, gateway_id)
        if principal is None:
            raise BulkLoadRefused("BULK_UNKNOWN_GATEWAY", batch.batch_id, "no such gateway is registered at that Site")
        # 4 and 5. The real path's admission; the claims check raises its own refusal (D-DS3.9).
        try:
            admission = self._service.admit(principal, raw, received_at, _refuse)
        except BatchRefused as error:
            raise BulkLoadRefused(error.kind, batch.batch_id, error.detail) from None
        # 6. A stored batch: the same bytes (step 5 refused others) loaded already, or the real path mid-batch.
        if admission.existing is not None:
            if admission.existing.status == "COMPLETED":
                return _Outcome(len(batch.envelopes), True)
            raise BulkLoadRefused("BULK_BATCH_IN_PROGRESS", batch.batch_id,
                                  "this batch is being admitted by the real path")
        # 7. Every ordinal decided by the real path's pure rule; clean batches only (D-DS3.5).
        decisions = [decide(admission.basis, ordinal, text) for ordinal, text in enumerate(batch.envelopes)]
        rejected = next((d for d in decisions if isinstance(d, Rejected)), None)
        if rejected is not None:
            raise BulkLoadRefused("BULK_REJECTED_ORDINAL", batch.batch_id,
                                  f"ordinal {rejected.ordinal} {rejected.kind}: {rejected.detail}")
        accepted: list[Accepted] = decisions  # type: ignore[assignment]
        # 7a. The cover the statement event carries resolves the same days as the envelopes (D-DS4.17).
        timezone = self.ledger.site_timezone(site_id)
        spans = []
        for a in accepted:
            try:
                spans.append(envelope_span(a.envelope.source_time, a.envelope.interval_start,
                                           a.envelope.interval_end))
            except BatchTimeUnreadable as error:
                raise BulkLoadRefused("BULK_BATCH_TIME_UNREADABLE", batch.batch_id,
                                      f"ordinal {a.ordinal} {error.field}") from None
        gap = cover_gap(spans, timezone)
        if gap is not None:
            raise BulkLoadRefused("BULK_BATCH_GAP_DAYS", batch.batch_id, gap)
        # 8. One transaction, one set-based statement per table.
        try:
            admitted = self.ledger.bulk_admit(
                principal,
                external_batch_id=batch.batch_id,
                payload_sha256=batch.payload_sha256,
                source_id=batch.source_id,
                source_mode=batch.source_mode,
                basis=admission.basis,
                batch_text=admission.text,
                decisions=accepted,
                received_at=received_at,
                completed_at=self.clock(),
            )
        except BulkAdmissionRefused as error:
            raise BulkLoadRefused(error.code, batch.batch_id, error.detail) from None
        return _Outcome(admitted.total, admitted.already_loaded)


@dataclass(frozen=True)
class _Outcome:
    total: int
    already_loaded: bool


def permitted_database(url: str, environ: Mapping[str, str] | None = None) -> bool:
    """A `<prefix>_audit*` database or a harness clone (`..._pt<hex>_<tag>_test`), never an operator's, never one
    named walk or serve, on the test container's host and port (D-DS3.6, D-DS3.12, D-DS3.22). Decided from the URL alone; no connection."""
    import os

    env = os.environ if environ is None else environ
    try:
        target = database_target(url, env)
    except DatabaseTargetUnclear:
        return False
    name_ok = (_DENIED_NAME.search(target.name) is None
               and (_AUDIT_NAME.fullmatch(target.name) is not None or _CLONE_NAME.fullmatch(target.name) is not None))
    try:
        port = int(env.get("ASSETOPS_PG_PORT", DEFAULT_PG_PORT))
    except ValueError:
        return False
    return (name_ok and not is_operator_name(target.name) and target.host in _LOCAL_HOSTS
            and target.port is not None and target.port == port)
