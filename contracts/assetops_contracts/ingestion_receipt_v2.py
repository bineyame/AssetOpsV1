"""Receipt V2: the durable central answer to one sealed Batch V2 (S2-02).

The server builds one receipt from its ledger rows; the gateway (S2-02 phase 2)
verifies `receipt_sha256`, the batch identity and digest, and every ordinal's
message ID before it records an acknowledgement. A receipt is never a claim
that an envelope is healthy or analysed; it says only what the ledger decided.

Text: canonical JSON (sorted keys, no whitespace, UTF-8). `receipt_sha256` is
the SHA-256 of the canonical document without that key. Instants are server
real-UTC text `YYYY-MM-DDTHH:MM:SS.ffffffZ` (exactly six fractional digits).

`status` is `IN_PROGRESS` while some ordinal is undecided (HTTP 202) and
`COMPLETED` once every ordinal's decision is durable (HTTP 200). A partial
receipt lists only the decided ordinals, in order, from ordinal 0.

Decisions: `ACCEPTED` and `DUPLICATE` carry the accepted evidence ID (for a
duplicate, the first accepted record of that message); `REJECTED` carries a
rejection; `CONFLICT` carries a rejection naming the first accepted record it
conflicts with.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from assetops_contracts.source_envelope import EnvelopeRejected, canonical_json, load_canonical_json
from assetops_contracts.source_envelope_v3 import text_sha256

INGESTION_RECEIPT_V2_SCHEMA_ID = "assetops.ingestion-receipt"
INGESTION_RECEIPT_V2_SCHEMA_VERSION = 2

RECEIPT_STATUSES = ("IN_PROGRESS", "COMPLETED")
RECEIPT_DECISIONS = ("ACCEPTED", "DUPLICATE", "REJECTED", "CONFLICT")

_DIGEST = re.compile(r"[0-9a-f]{64}")
_SERVER_INSTANT = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z")
_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


class ReceiptRejected(ValueError):
    def __init__(self, kind: str, field: str, detail: str) -> None:
        super().__init__(f"{kind} at {field}: {detail}")
        self.kind = kind
        self.field = field
        self.detail = detail


@dataclass(frozen=True)
class ReceiptRejection:
    rejection_id: str
    kind: str
    field: str
    detail: str
    conflicts_with_evidence_id: str | None


@dataclass(frozen=True)
class ReceiptDisposition:
    ordinal: int
    message_id: str
    decision: str
    evidence_id: str | None
    rejection: ReceiptRejection | None


@dataclass(frozen=True)
class ReceiptCounts:
    total: int
    processed: int
    accepted: int
    duplicate: int
    rejected: int
    conflict: int


@dataclass(frozen=True)
class IngestionReceiptV2:
    batch_id: str
    payload_sha256: str
    site_id: str
    gateway_id: str
    source_id: str
    status: str
    received_at: str
    completed_at: str | None
    counts: ReceiptCounts
    dispositions: tuple[ReceiptDisposition, ...]

    def __post_init__(self) -> None:
        _validate(self)


def _fail(kind: str, field: str, detail: str) -> None:
    raise ReceiptRejected(kind, field, detail)


def _validate(r: IngestionReceiptV2) -> None:
    if not _DIGEST.fullmatch(r.payload_sha256):
        _fail("INVALID_FIELD", "payload_sha256", "not a SHA-256 hex digest")
    if r.status not in RECEIPT_STATUSES:
        _fail("INVALID_FIELD", "status", repr(r.status))
    if not _SERVER_INSTANT.fullmatch(r.received_at):
        _fail("INVALID_FIELD", "received_at", "not a server instant")
    c = r.counts
    if c.processed != len(r.dispositions) or not 0 < c.total or c.processed > c.total:
        _fail("INVALID_COUNTS", "counts", "processed must equal the listed ordinals, within total")
    tallies = {d: sum(1 for x in r.dispositions if x.decision == d) for d in RECEIPT_DECISIONS}
    if (c.accepted, c.duplicate, c.rejected, c.conflict) != (
        tallies["ACCEPTED"], tallies["DUPLICATE"], tallies["REJECTED"], tallies["CONFLICT"]
    ):
        _fail("INVALID_COUNTS", "counts", "decision counts do not match the dispositions")
    complete = c.processed == c.total
    if (r.status == "COMPLETED") != complete:
        _fail("INVALID_FIELD", "status", "COMPLETED exactly when every ordinal is decided")
    if complete != (r.completed_at is not None):
        _fail("INVALID_FIELD", "completed_at", "set exactly when the receipt is complete")
    if r.completed_at is not None and not _SERVER_INSTANT.fullmatch(r.completed_at):
        _fail("INVALID_FIELD", "completed_at", "not a server instant")
    for index, d in enumerate(r.dispositions):
        where = f"dispositions[{index}]"
        if d.ordinal != index:
            _fail("NOT_ORDERED", f"{where}.ordinal", "ordinals are listed from 0 without gaps")
        if not _DIGEST.fullmatch(d.message_id):
            _fail("INVALID_FIELD", f"{where}.message_id", "not a message ID")
        if d.decision not in RECEIPT_DECISIONS:
            _fail("INVALID_FIELD", f"{where}.decision", repr(d.decision))
        has_evidence = d.decision in ("ACCEPTED", "DUPLICATE")
        if has_evidence != (d.evidence_id is not None) or has_evidence == (d.rejection is not None):
            _fail("INVALID_FIELD", where, f"{d.decision} carries the wrong reference")
        if d.evidence_id is not None and not _UUID.fullmatch(d.evidence_id):
            _fail("INVALID_FIELD", f"{where}.evidence_id", "not a UUID")
        if d.rejection is not None:
            conflict = d.decision == "CONFLICT"
            if conflict != (d.rejection.conflicts_with_evidence_id is not None):
                _fail("INVALID_FIELD", f"{where}.rejection", "only a CONFLICT names the evidence it conflicts with")
            if not _UUID.fullmatch(d.rejection.rejection_id):
                _fail("INVALID_FIELD", f"{where}.rejection.rejection_id", "not a UUID")


def _document_body(r: IngestionReceiptV2) -> dict[str, Any]:
    return {
        "schema": {"id": INGESTION_RECEIPT_V2_SCHEMA_ID, "version": INGESTION_RECEIPT_V2_SCHEMA_VERSION},
        "batch_id": r.batch_id,
        "payload_sha256": r.payload_sha256,
        "site_id": r.site_id,
        "gateway_id": r.gateway_id,
        "source_id": r.source_id,
        "status": r.status,
        "received_at": r.received_at,
        "completed_at": r.completed_at,
        "counts": {
            "total": r.counts.total,
            "processed": r.counts.processed,
            "accepted": r.counts.accepted,
            "duplicate": r.counts.duplicate,
            "rejected": r.counts.rejected,
            "conflict": r.counts.conflict,
        },
        "dispositions": [
            {
                "ordinal": d.ordinal,
                "message_id": d.message_id,
                "decision": d.decision,
                "evidence_id": d.evidence_id,
                "rejection": None
                if d.rejection is None
                else {
                    "rejection_id": d.rejection.rejection_id,
                    "kind": d.rejection.kind,
                    "field": d.rejection.field,
                    "detail": d.rejection.detail,
                    "conflicts_with_evidence_id": d.rejection.conflicts_with_evidence_id,
                },
            }
            for d in r.dispositions
        ],
    }


def receipt_v2_sha256(r: IngestionReceiptV2) -> str:
    return text_sha256(canonical_json(_document_body(r)))


def receipt_v2_document(r: IngestionReceiptV2) -> dict[str, Any]:
    body = _document_body(r)
    return {**body, "receipt_sha256": text_sha256(canonical_json(body))}


def canonical_receipt_v2_text(r: IngestionReceiptV2) -> str:
    return canonical_json(receipt_v2_document(r))


_KEYS = frozenset(
    {"schema", "batch_id", "payload_sha256", "site_id", "gateway_id", "source_id", "status",
     "received_at", "completed_at", "counts", "dispositions", "receipt_sha256"}
)
_COUNT_KEYS = frozenset({"total", "processed", "accepted", "duplicate", "rejected", "conflict"})
_DISPOSITION_KEYS = frozenset({"ordinal", "message_id", "decision", "evidence_id", "rejection"})
_REJECTION_KEYS = frozenset({"rejection_id", "kind", "field", "detail", "conflicts_with_evidence_id"})


def _exact(document: object, keys: frozenset[str], where: str) -> dict[str, Any]:
    if not isinstance(document, dict) or set(document) != keys:
        _fail("WRONG_SHAPE", where, f"exactly the keys {sorted(keys)}")
    return document  # type: ignore[return-value]


def _int(value: object, where: str) -> int:
    if type(value) is not int or value < 0:
        _fail("WRONG_TYPE", where, "a whole number")
    return value  # type: ignore[return-value]


def _str(value: object, where: str, *, optional: bool = False) -> Any:
    if value is None and optional:
        return None
    if type(value) is not str:
        _fail("WRONG_TYPE", where, "text")
    return value


def parse_canonical_receipt_v2_text(text: object) -> IngestionReceiptV2:
    """Exact received bytes back as a receipt; shape, digest and canonical spelling checked."""
    try:
        document = load_canonical_json(text)
    except EnvelopeRejected as error:
        raise ReceiptRejected("MALFORMED_TEXT", "receipt", error.detail) from error
    top = _exact(document, _KEYS, "receipt")
    if top["schema"] != {"id": INGESTION_RECEIPT_V2_SCHEMA_ID, "version": INGESTION_RECEIPT_V2_SCHEMA_VERSION}:
        _fail("SCHEMA_UNSUPPORTED", "schema", repr(top["schema"]))
    counts = _exact(top["counts"], _COUNT_KEYS, "counts")
    if type(top["dispositions"]) is not list:
        _fail("WRONG_TYPE", "dispositions", "a list")
    dispositions = []
    for index, raw in enumerate(top["dispositions"]):
        where = f"dispositions[{index}]"
        d = _exact(raw, _DISPOSITION_KEYS, where)
        rejection = None
        if d["rejection"] is not None:
            rj = _exact(d["rejection"], _REJECTION_KEYS, f"{where}.rejection")
            rejection = ReceiptRejection(
                rejection_id=_str(rj["rejection_id"], f"{where}.rejection.rejection_id"),
                kind=_str(rj["kind"], f"{where}.rejection.kind"),
                field=_str(rj["field"], f"{where}.rejection.field"),
                detail=_str(rj["detail"], f"{where}.rejection.detail"),
                conflicts_with_evidence_id=_str(
                    rj["conflicts_with_evidence_id"], f"{where}.rejection.conflicts_with_evidence_id", optional=True
                ),
            )
        dispositions.append(
            ReceiptDisposition(
                ordinal=_int(d["ordinal"], f"{where}.ordinal"),
                message_id=_str(d["message_id"], f"{where}.message_id"),
                decision=_str(d["decision"], f"{where}.decision"),
                evidence_id=_str(d["evidence_id"], f"{where}.evidence_id", optional=True),
                rejection=rejection,
            )
        )
    receipt = IngestionReceiptV2(
        batch_id=_str(top["batch_id"], "batch_id"),
        payload_sha256=_str(top["payload_sha256"], "payload_sha256"),
        site_id=_str(top["site_id"], "site_id"),
        gateway_id=_str(top["gateway_id"], "gateway_id"),
        source_id=_str(top["source_id"], "source_id"),
        status=_str(top["status"], "status"),
        received_at=_str(top["received_at"], "received_at"),
        completed_at=_str(top["completed_at"], "completed_at", optional=True),
        counts=ReceiptCounts(**{k: _int(counts[k], f"counts.{k}") for k in sorted(_COUNT_KEYS)}),
        dispositions=tuple(dispositions),
    )
    if top["receipt_sha256"] != receipt_v2_sha256(receipt):
        _fail("DIGEST_MISMATCH", "receipt_sha256", "does not match the canonical receipt")
    if canonical_receipt_v2_text(receipt) != text:
        _fail("NOT_CANONICAL", "receipt", "the text is not its own canonical text")
    return receipt
