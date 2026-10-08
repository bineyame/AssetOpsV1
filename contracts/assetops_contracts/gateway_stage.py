"""The registered-run Stage as the durable gateway ledger holds it (S2-01b).

A neutral read model, so the gated Lab API can present a registered run's Stage
without importing the gateway or the host. It carries exactly what the ledger
stored: canonical SourceEnvelope V3 and Batch V2 text with their digests,
source/epoch/sequence, ordinals, local queue state and typed holds. Nothing in it
is accepted evidence: upload is pending until S2-02, and there is no receipt.

The historical file-backed Stage (`source_stage.SourceStageView`) is a separate
type and stays the read for pre-import YAML runs.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Where a registered run's Stage comes from. Pre-import runs say LEGACY_FILE.
GATEWAY_LEDGER_STORE = "GATEWAY_LEDGER"

REGISTERED_STAGE_STATUSES = ("STAGED", "NOT_STAGED", "GATEWAY_UNAVAILABLE")
REGISTERED_STAGE_STATEMENTS = {
    "STAGED": (
        "The gateway sealed this run's public reports into its local outbox. "
        "Upload is pending: nothing has been sent or accepted."
    ),
    "NOT_STAGED": "The gateway holds nothing for this run yet.",
    "GATEWAY_UNAVAILABLE": (
        "The gateway could not be reached over its authenticated local channel, "
        "so this Stage cannot be read. Nothing is shown from any other store."
    ),
}
#: Until S2-02 adds authenticated upload, every registered batch is pending.
UPLOAD_PENDING = "PENDING"
UPLOAD_STATEMENT = "Upload pending: no batch has been sent and no receipt exists."


@dataclass(frozen=True)
class GatewayEnvelope:
    message_id: str
    source_id: str
    sequence_epoch: str
    sequence: int
    source_time: str
    snapshot_sha256: str
    envelope_text: str
    sha256: str
    state: str
    batch_id: str | None
    ordinal: int | None


@dataclass(frozen=True)
class GatewayBatch:
    batch_id: str
    source_id: str
    sequence_epoch: str
    snapshot_sha256: str
    payload_text: str
    sha256: str
    state: str
    attempt_count: int
    message_ids: tuple[str, ...]


@dataclass(frozen=True)
class GatewayHold:
    hold_id: int
    kind: str
    field: str
    detail: str
    device_id: str | None
    signal_id: str | None
    source_time: str | None
    seen_count: int


@dataclass(frozen=True)
class RegisteredStageView:
    run_id: str
    status: str
    statement: str
    execution_status: str
    snapshot_sha256: str
    site_id: str | None
    gateway_id: str | None
    sequence_epoch: str | None
    envelopes: tuple[GatewayEnvelope, ...]
    batches: tuple[GatewayBatch, ...]
    holds: tuple[GatewayHold, ...]
    queue_depth_by_state: dict[str, int]
    upload_state: str = UPLOAD_PENDING
    unavailable_detail: str | None = None
    #: What publishing this run through the gateway had to say (refusals).
    publication_notes: tuple[str, ...] = ()
