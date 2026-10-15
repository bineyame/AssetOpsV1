"""Batch V2 ingestion over the central evidence ledger (S2-02 phase 1).

Order of checks (technical design section 4 "Receive batch" / "Decide records",
`D-2026-10-09-s2-pilot-gateway-upload-credential`):

1. The caller has already resolved an authenticated `GatewayPrincipal`; an
   unauthenticated request never reaches this service.
2. Size bound before parsing (413). The batch is then parsed strictly
   (`parse_canonical_batch_v2_text`); a malformed batch from an authenticated
   gateway is a whole-batch `batch_refusal` row (422), distinct from any
   per-ordinal rejection.
3. Claims (Site, gateway, mode) are compared with the principal, and the
   batch's source must be **currently** registered to that gateway and Site and
   enabled, on every upload including identical retries (403, no row).
4. Same external ID with different bytes is 409 and leaves the stored batch
   untouched (an audit `batch_refusal` row records the attempt).
5. The configuration reference must name a registered binding set version
   whose pinned snapshot matches the batch exactly (422 refusal row otherwise).
6. Ordinals are decided in short chunk transactions from the persisted
   watermark. A retry of the same bytes resumes; a terminal receipt (200) is
   returned only when every ordinal is durable, otherwise 202 `IN_PROGRESS`.

`received_at` is the server's real UTC at first receipt; envelope `source_time`
and `published_at` are kept as sent (virtual instants for a RUN_VIRTUAL run).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from assetops_backend.evidence.ledger import (
    BatchHandle,
    ConfigurationRefused,
    EvidenceLedger,
    GatewayPrincipal,
    basis_from_snapshot,
    decide,
)
from assetops_backend.evidence.publication import PublicationMismatch
from assetops_contracts.ingestion_batch_v2 import (
    MAX_BATCH_BYTES,
    BatchRejected,
    parse_canonical_batch_v2_text,
)
from assetops_contracts.ingestion_receipt_v2 import IngestionReceiptV2
from assetops_contracts.source_envelope_v3 import sha256_hex

DEFAULT_CHUNK_SIZE = 64


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class BatchRefused(Exception):
    """A whole-batch answer that is not a receipt."""

    status: int
    code: str
    kind: str
    field: str
    detail: str
    refusal_id: str | None = None


@dataclass(frozen=True)
class Submitted:
    status: int  # 200 terminal, 202 in progress
    receipt: IngestionReceiptV2


class SimulatedCrash(RuntimeError):
    """Test hook: the process 'dies' after a committed chunk."""


class BatchIngestionService:
    def __init__(
        self,
        ledger: EvidenceLedger,
        clock: Callable[[], datetime] = utc_now,
        *,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        max_chunks_per_request: int | None = None,
        crash_after_chunks: int | None = None,
    ) -> None:
        if chunk_size < 1:
            raise ValueError("chunk_size must be positive")
        self.ledger = ledger
        self.clock = clock
        self.chunk_size = chunk_size
        self.max_chunks_per_request = max_chunks_per_request
        self.crash_after_chunks = crash_after_chunks

    # --- submit -------------------------------------------------------------

    def submit(self, principal: GatewayPrincipal, raw: bytes) -> Submitted:
        received_at = self.clock()
        digest = sha256_hex(raw)
        if len(raw) > MAX_BATCH_BYTES:
            raise self._refuse(principal, None, digest, received_at, 413, "TOO_LARGE", "batch",
                               f"more than {MAX_BATCH_BYTES} bytes")
        try:
            text = raw.decode("utf-8")
            batch = parse_canonical_batch_v2_text(text)
        except UnicodeDecodeError:
            raise self._refuse(principal, None, digest, received_at, 422, "MALFORMED_TEXT", "batch",
                               "the body is not UTF-8") from None
        except BatchRejected as error:
            raise self._refuse(principal, None, digest, received_at, 422, error.kind, error.field,
                               error.detail) from None

        self._check_claims(principal, batch.site_id, batch.gateway_id, batch.source_mode, batch.source_id)

        existing = self.ledger.find_batch(principal, batch.batch_id)
        if existing is not None and existing.payload_sha256 != batch.payload_sha256:
            raise self._refuse(principal, batch.batch_id, batch.payload_sha256, received_at, 409,
                               "BATCH_ID_CONFLICT", "batch_id",
                               "this batch ID was received with different bytes; the stored batch is unchanged")

        stored = self.ledger.binding_set(principal, batch.binding_set_id, batch.binding_version)
        if stored is None:
            raise self._refuse(principal, batch.batch_id, batch.payload_sha256, received_at, 422,
                               "CONFIGURATION_UNREGISTERED", "mapping",
                               f"binding set {batch.binding_set_id} v{batch.binding_version} is not registered "
                               "for this Site")
        try:
            basis = basis_from_snapshot(
                stored,
                foundation_version=batch.foundation_version,
                foundation_valid_from=batch.foundation_valid_from,
                binding_set_id=batch.binding_set_id,
                binding_version=batch.binding_version,
                snapshot_sha256=batch.snapshot_sha256,
            )
        except ConfigurationRefused as error:
            raise self._refuse(principal, batch.batch_id, batch.payload_sha256, received_at, 422,
                               error.kind, error.field, error.detail) from None
        if basis.gateway_id != str(principal.gateway_id):
            raise self._refuse(principal, batch.batch_id, batch.payload_sha256, received_at, 422,
                               "CONFIGURATION_MISMATCH", "mapping",
                               "the referenced binding set was published for another gateway")

        try:
            handle = existing or self.ledger.open_batch(
                principal,
                external_batch_id=batch.batch_id,
                payload_sha256=batch.payload_sha256,
                source_id=batch.source_id,
                source_mode=batch.source_mode,
                basis=basis,
                batch_text=text,
                total=len(batch.envelopes),
                received_at=received_at,
            )
        except PublicationMismatch as error:
            # S4-05a: a matching slot with a different preauthorized commitment fails; it never degrades to an
            # unbound (unknown-source) admission.
            raise self._refuse(principal, batch.batch_id, batch.payload_sha256, received_at, 409,
                               "PUBLICATION_MISMATCH", "batch_id", error.detail) from None
        if handle.payload_sha256 != batch.payload_sha256:  # lost an insert race to other bytes
            raise self._refuse(principal, batch.batch_id, batch.payload_sha256, received_at, 409,
                               "BATCH_ID_CONFLICT", "batch_id",
                               "this batch ID was received with different bytes; the stored batch is unchanged")
        self._drive(handle, batch.envelopes, basis)
        receipt = self.ledger.receipt(principal, batch.batch_id)
        assert receipt is not None
        return Submitted(200 if receipt.status == "COMPLETED" else 202, receipt)

    def receipt(self, principal: GatewayPrincipal, external_batch_id: str) -> IngestionReceiptV2 | None:
        return self.ledger.receipt(principal, external_batch_id)

    # --- internals ----------------------------------------------------------

    def _drive(self, handle: BatchHandle, envelopes: tuple[str, ...], basis) -> None:
        status = handle.status
        chunks = 0
        while status != "COMPLETED":
            if self.max_chunks_per_request is not None and chunks >= self.max_chunks_per_request:
                return
            status = self.ledger.decide_chunk(
                handle,
                envelopes,
                lambda ordinal, text: decide(basis, ordinal, text),
                limit=self.chunk_size,
                completed_at=self.clock(),  # receipt field (app clock); decisions take DB time (S4-07)
            )
            chunks += 1
            if self.crash_after_chunks is not None and chunks >= self.crash_after_chunks and status != "COMPLETED":
                raise SimulatedCrash(f"crashed after {chunks} committed chunk(s)")

    def _check_claims(
        self, principal: GatewayPrincipal, site_id: str, gateway_id: str, mode: str, source_id: str
    ) -> None:
        if site_id != str(principal.site_id) or gateway_id != str(principal.gateway_id):
            raise BatchRefused(403, "SCOPE_FORBIDDEN", "SCOPE_MISMATCH", "site_id",
                               "the batch names a Site or gateway this credential does not hold")
        if mode != principal.mode:
            raise BatchRefused(403, "SCOPE_FORBIDDEN", "MODE_MISMATCH", "source_mode",
                               f"the registered gateway is {principal.mode}, not {mode}")
        scope = self.ledger.registered_scope(principal, source_id)
        if scope.gateway_site_id != principal.site_id or scope.gateway_mode != principal.mode:
            raise BatchRefused(403, "SCOPE_FORBIDDEN", "GATEWAY_NOT_REGISTERED", "gateway_id",
                               "the gateway registration does not match this credential")
        if scope.gateway_disabled:
            raise BatchRefused(403, "SCOPE_FORBIDDEN", "GATEWAY_DISABLED", "gateway_id",
                               "the registered gateway is disabled")
        if scope.source_gateway_id != principal.gateway_id or scope.source_site_id != principal.site_id:
            raise BatchRefused(403, "SCOPE_FORBIDDEN", "SOURCE_NOT_AFFILIATED", "source_id",
                               "the source is not registered to this gateway and Site")
        if scope.source_disabled:
            raise BatchRefused(403, "SCOPE_FORBIDDEN", "SOURCE_DISABLED", "source_id",
                               "the registered source is disabled")

    def _refuse(
        self,
        principal: GatewayPrincipal,
        external_batch_id: str | None,
        digest: str,
        received_at: datetime,
        status: int,
        kind: str,
        field: str,
        detail: str,
    ) -> BatchRefused:
        refusal_id = self.ledger.record_refusal(
            principal,
            external_batch_id=external_batch_id,
            payload_sha256=digest,
            kind=kind,
            field=field,
            detail=detail,
            received_at=received_at,
        )
        code = "BATCH_CONFLICT" if status == 409 else "BATCH_REFUSED"
        return BatchRefused(status, code, kind, field, detail, str(refusal_id))
