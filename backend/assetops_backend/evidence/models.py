"""Evidence records: what ingestion accepted, refused, and how far it got (T027 D3).

Every record here is a product fact that exists only because ingestion wrote
it. Nothing is built from a stage, a world, a LabProjection or a scenario
expectation, and the read model reads accepted records only (AC8).

Overlapping records (AC9). A record's identity is its envelope `message_id`,
which is derived from (Site, gateway, source, device, signal, source_time).
Two DISTINCT ids at the same (device, signal, source_time) - the same signal
reported by two gateways, say - are both accepted and kept as they are: the
read model reports them as `overlapping` in coverage and lists both in the
inspector. Nothing sums them, nothing picks one, and no later one replaces an
earlier one. The SAME id is one record: identical content is an idempotent
duplicate, different content is a `Conflict` that leaves the original
accepted record untouched (AC6).

Normalization is the identity in this build: the frozen mapping refuses any
unit conversion (`check_against_mapping`), so `normalized_*` always equals
`original_*`, and the inspector says so rather than implying a conversion.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Ingestion-side rejection kinds, beyond the envelope contract's own kinds.
INGESTION_REJECTION_KINDS = frozenset(
    {
        "SITE_MISMATCH",
        "SIGNAL_NOT_IN_CONFIGURATION",
        "UNIT_INCOMPATIBLE",
        "BEFORE_CONFIGURATION_EFFECTIVE",
        "BATCH_ID_CONFLICT",
    }
)

#: Whole-batch refusals: no envelope of a refused batch is read.
BATCH_REFUSAL_KINDS = frozenset(
    {
        "SITE_UNKNOWN",
        "SITE_MISMATCH",
        "SOURCE_MODE_MISMATCH",
        "MAPPING_CONFLICT",
        "CONFIGURATION_UNRESOLVED",
        "BATCH_ID_CONFLICT",
    }
)

BATCH_STATUSES = frozenset({"IN_PROGRESS", "COMPLETED", "REFUSED"})

NORMALIZATION = "IDENTITY"
NORMALIZATION_STATEMENT = (
    "Normalization is the identity in this build: the mapping refuses unit "
    "conversion, so the normalized value and unit are the published ones."
)


@dataclass(frozen=True)
class AcceptedRecord:
    """One accepted envelope, with the basis it was accepted under."""

    message_id: str
    #: The canonical envelope text exactly as released.
    envelope_text: str
    content_digest: str
    site_id: str
    source_id: str
    gateway_id: str
    device_id: str
    signal_id: str
    family: str
    measurement: str | None
    source_time: str
    published_at: str
    #: Assigned by ingestion's clock, never by the source.
    received_at: str
    batch_id: str
    source_mode: str
    mapping_set_id: str
    mapping_version: int
    foundation_version: int
    foundation_valid_from: str
    original_value: str | None
    original_unit: str
    normalized_value: str | None
    normalized_unit: str
    quality: str | None
    unavailable_reason: str | None
    interval_start: str | None
    interval_end: str | None
    #: Record-family fields (control, component, effective time, kind, actor),
    #: as published, non-null ones only. Empty for a measurement.
    record_detail: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class Rejection:
    """One envelope (or one batch attempt) ingestion refused, inspectable."""

    batch_id: str
    #: The envelope's position in its batch; None for a whole-batch refusal.
    index: int | None
    message_id: str | None
    kind: str
    field: str
    detail: str
    received_at: str
    content_digest: str


@dataclass(frozen=True)
class Conflict:
    """Same message id, different content. The original is never touched."""

    message_id: str
    batch_id: str
    original_digest: str
    conflicting_digest: str
    received_at: str


@dataclass(frozen=True)
class BatchProgress:
    """Release status of one batch: what was actually processed and accepted."""

    batch_id: str
    site_id: str
    source_id: str
    gateway_id: str
    source_mode: str
    #: Digest of the batch content, so the same id with other content is refused.
    batch_digest: str
    total: int
    #: Index watermark: envelopes [0, processed) have been decided and persisted.
    processed: int
    accepted: int
    duplicates: int
    rejected: int
    conflicts: int
    status: str
    refusal_kind: str | None
    refusal_detail: str | None
    started_at: str
    completed_at: str | None
    window_start: str | None
    window_end: str | None


@dataclass(frozen=True)
class BasisSignal:
    device_id: str
    signal_id: str
    unit: str
    component_id: str


@dataclass(frozen=True)
class ConfigurationBasis:
    """Immutable snapshot of one Foundation version, keyed by (site, version)."""

    site_id: str
    foundation_version: int
    foundation_valid_from: str
    site_type: str
    signals: tuple[BasisSignal, ...]
    registered_at: str

    def signal(self, device_id: str, signal_id: str) -> BasisSignal | None:
        for item in self.signals:
            if (item.device_id, item.signal_id) == (device_id, signal_id):
                return item
        return None


@dataclass(frozen=True)
class MappingRegistration:
    """Immutable by (mapping_set_id, mapping_version): its canonical document text."""

    mapping_set_id: str
    mapping_version: int
    document_text: str
    registered_at: str


@dataclass(frozen=True)
class SiteEvidence:
    """Everything ingestion has written for one Site."""

    site_id: str
    records: tuple[AcceptedRecord, ...] = ()
    rejections: tuple[Rejection, ...] = ()
    conflicts: tuple[Conflict, ...] = ()
    batches: tuple[BatchProgress, ...] = ()
