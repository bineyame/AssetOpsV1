"""Ingestion: the one path that writes evidence (T027 D2, D3).

`IngestionService.ingest(batch)` is THE ingestion entry point. The HTTP route
`POST /api/ingestion/batches` is a thin wrapper over it, and the Lab Commit
route releases a committed artifact by handing `ingestion_batch(artifact)` to
the same method. Simulated and live content therefore cross one validation
and normalization path; `source_mode` is recorded as provenance and checked
against the Site's own source mode, nothing more (AC4).

Algorithm, per batch:
1. Resolve the Site. Unknown, or a source mode other than the Site's -> the
   batch is REFUSED whole and no envelope is read.
2. Register the mapping once, or match its immutable registration; the same
   id/version with other content is REFUSED `MAPPING_CONFLICT`.
3. Resolve the configuration (Site, Foundation version) from the immutable
   basis registry. Absent and equal to the Site's CURRENT Foundation -> a
   snapshot of it is registered; absent otherwise -> REFUSED
   `CONFIGURATION_UNRESOLVED`. A registered basis is never rewritten, so a
   later Foundation edit cannot change how accepted content was read (AC17).
4. Resume: a COMPLETED batch is returned unchanged (idempotent); an
   IN_PROGRESS one continues from its persisted watermark (AC2, AC7).
5. Each envelope text is parsed strictly and checked against the batch, the
   mapping and the configuration basis; a failure is an inspectable
   `Rejection` and never sinks a valid sibling (AC3). Identity: the same
   message id with the same content is a duplicate (counted, not stored
   again); with other content it is a `Conflict` and the original stays (AC6).
   Accepted records get `received_at` from ingestion's clock (AC5).
6. Records and progress are persisted together in chunks, one atomic write
   per chunk, so an interruption leaves a consistent prefix and a watermark
   that says exactly what was decided (AC7).

Normalization is the identity (see `models.NORMALIZATION_STATEMENT`).
"""

from __future__ import annotations

import threading
from dataclasses import replace
from datetime import datetime, timezone
from typing import Callable

from assetops_backend.evidence.models import (
    AcceptedRecord,
    BasisSignal,
    BatchProgress,
    ConfigurationBasis,
    Conflict,
    MappingRegistration,
    Rejection,
    SiteEvidence,
)
from assetops_backend.evidence.ports import EvidenceStore, find_batch
from assetops_backend.sites.models import SiteRecord
from assetops_backend.sites.ports import SiteNotFound, SiteRepository
from assetops_contracts.committed_artifact import envelope_content_digest
from assetops_contracts.identity import identity_digest
from assetops_contracts.ingestion_batch import IngestionBatch, ingestion_batch_document
from assetops_contracts.source_envelope import (
    EnvelopeRejected,
    SourceEnvelope,
    canonical_json,
    check_against_mapping,
    envelope_document,
    instant_text,
    mapping_set_document,
    parse_canonical_envelope_json,
)

Clock = Callable[[], str]

BATCH_DIGEST_DOMAIN = "ingestion-batch-content-v1"
DEFAULT_CHUNK_SIZE = 64

_RECORD_DETAIL_FIELDS = (
    "control",
    "component_id",
    "members",
    "policy_version",
    "policy_source",
    "effective_start",
    "effective_end",
    "record_kind",
    "actor",
)


def system_clock() -> str:
    return instant_text(datetime.now(timezone.utc))


class IngestionInterrupted(RuntimeError):
    """Raised by the test-only `fail_after` hook to simulate a crash mid-batch."""


def batch_digest(batch: IngestionBatch) -> str:
    return identity_digest([BATCH_DIGEST_DOMAIN, canonical_json(ingestion_batch_document(batch))])


def _accepted_record(
    envelope: SourceEnvelope,
    text: str,
    digest: str,
    batch: IngestionBatch,
    received_at: str,
) -> AcceptedRecord:
    payload = envelope_document(envelope)["payload"]
    value = payload.get("value")
    detail = []
    for name in _RECORD_DETAIL_FIELDS:
        item = payload.get(name)
        if item is None:
            continue
        detail.append((name, ",".join(item) if isinstance(item, list) else str(item)))
    return AcceptedRecord(
        message_id=envelope.message_id,
        envelope_text=text,
        content_digest=digest,
        site_id=envelope.site_id,
        source_id=envelope.source_id,
        gateway_id=envelope.gateway_id,
        device_id=envelope.device_id,
        signal_id=envelope.signal_id,
        family=envelope.family,
        measurement=envelope.measurement,
        source_time=envelope.source_time,
        published_at=envelope.published_at,
        received_at=received_at,
        batch_id=batch.batch_id,
        source_mode=batch.source_mode,
        mapping_set_id=envelope.mapping_set_id,
        mapping_version=envelope.mapping_version,
        foundation_version=batch.configuration.foundation_version,
        foundation_valid_from=batch.configuration.foundation_valid_from,
        original_value=value,
        original_unit=envelope.unit,
        # Identity normalization: the mapping refuses conversion.
        normalized_value=value,
        normalized_unit=envelope.unit,
        quality=envelope.quality,
        unavailable_reason=envelope.unavailable_reason,
        interval_start=envelope.interval_start,
        interval_end=envelope.interval_end,
        record_detail=tuple(detail),
    )


class _Refused(Exception):
    def __init__(self, kind: str, detail: str) -> None:
        self.kind = kind
        self.detail = detail
        super().__init__(f"{kind}: {detail}")


class IngestionService:
    """The one ingestion entry point. `fail_after` is a test-only fault hook."""

    def __init__(
        self,
        store: EvidenceStore,
        sites: SiteRepository,
        clock: Clock = system_clock,
        *,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        fail_after: int | None = None,
    ) -> None:
        if chunk_size < 1:
            raise ValueError("chunk_size is at least 1")
        self._store = store
        self._sites = sites
        self._clock = clock
        self._chunk_size = chunk_size
        self._fail_after = fail_after
        self._lock = threading.Lock()

    @property
    def store(self) -> EvidenceStore:
        return self._store

    # --- whole-batch resolution --------------------------------------------
    def _site(self, batch: IngestionBatch) -> SiteRecord:
        try:
            site = self._sites.get_site(batch.site_id)
        except SiteNotFound as error:
            raise _Refused("SITE_UNKNOWN", f"no Site {batch.site_id} is configured") from error
        if site.site_id != batch.site_id:
            raise _Refused(
                "SITE_MISMATCH",
                f"the batch names {batch.site_id} and the Site is {site.site_id}",
            )
        if site.source.mode != batch.source_mode:
            raise _Refused(
                "SOURCE_MODE_MISMATCH",
                f"the batch is {batch.source_mode} and Site {site.site_id}'s "
                f"source mode is {site.source.mode}",
            )
        return site

    def _mapping(self, batch: IngestionBatch) -> None:
        text = canonical_json(mapping_set_document(batch.mapping))
        registered = self._store.register_mapping(
            MappingRegistration(
                mapping_set_id=batch.mapping.mapping_set_id,
                mapping_version=batch.mapping.mapping_version,
                document_text=text,
                registered_at=self._clock(),
            )
        )
        if registered.document_text != text:
            raise _Refused(
                "MAPPING_CONFLICT",
                f"{batch.mapping.mapping_set_id} v{batch.mapping.mapping_version} is "
                "already registered with other content; a mapping version is immutable",
            )

    def _configuration(self, batch: IngestionBatch, site: SiteRecord) -> ConfigurationBasis:
        reference = batch.configuration
        basis = self._store.get_configuration(site.site_id, reference.foundation_version)
        if basis is None:
            current = site.foundation
            if (current.version, current.valid_from) != (
                reference.foundation_version,
                reference.foundation_valid_from,
            ):
                raise _Refused(
                    "CONFIGURATION_UNRESOLVED",
                    f"Foundation v{reference.foundation_version} of {site.site_id} is "
                    f"not registered and is not the current Foundation "
                    f"(v{current.version}), so nothing says how to read this content",
                )
            basis = self._store.register_configuration(
                ConfigurationBasis(
                    site_id=site.site_id,
                    foundation_version=current.version,
                    foundation_valid_from=current.valid_from,
                    site_type=site.site_type,
                    signals=tuple(
                        BasisSignal(
                            device_id=device.device_id,
                            signal_id=signal.signal_id,
                            unit=signal.unit,
                            component_id=device.component_id,
                        )
                        for device in (current.devices or ())
                        for signal in device.signals
                    ),
                    registered_at=self._clock(),
                )
            )
        if basis.foundation_valid_from != reference.foundation_valid_from:
            raise _Refused(
                "CONFIGURATION_UNRESOLVED",
                f"Foundation v{reference.foundation_version} is registered as valid "
                f"from {basis.foundation_valid_from}, not {reference.foundation_valid_from}",
            )
        return basis

    # --- per-envelope decision ---------------------------------------------
    def _check(
        self,
        text: str,
        batch: IngestionBatch,
        basis: ConfigurationBasis,
    ) -> SourceEnvelope:
        envelope = parse_canonical_envelope_json(text)
        if (envelope.site_id, envelope.source_id, envelope.gateway_id) != (
            batch.site_id,
            batch.source_id,
            batch.gateway_id,
        ):
            raise _Rejected(
                "SITE_MISMATCH",
                "source",
                "the envelope names another Site, source or gateway than its batch",
                envelope.message_id,
            )
        try:
            check_against_mapping(envelope, batch.mapping)
        except EnvelopeRejected as refusal:
            raise _Rejected(
                refusal.kind, refusal.field, refusal.detail, envelope.message_id
            ) from refusal
        if envelope.family == "MEASUREMENT":
            signal = basis.signal(envelope.device_id, envelope.signal_id)
            if signal is None:
                raise _Rejected(
                    "SIGNAL_NOT_IN_CONFIGURATION",
                    "source.signal_id",
                    f"{envelope.device_id}/{envelope.signal_id} is not a signal of "
                    f"Foundation v{basis.foundation_version}",
                    envelope.message_id,
                )
            if signal.unit != envelope.unit:
                raise _Rejected(
                    "UNIT_INCOMPATIBLE",
                    "payload.unit",
                    f"Foundation v{basis.foundation_version} declares "
                    f"{signal.unit!r} for this signal and the envelope carries "
                    f"{envelope.unit!r}; nothing converts at ingestion",
                    envelope.message_id,
                )
        if envelope.source_time < basis.foundation_valid_from:
            raise _Rejected(
                "BEFORE_CONFIGURATION_EFFECTIVE",
                "timing.source_time",
                f"{envelope.source_time} precedes Foundation "
                f"v{basis.foundation_version}'s validity ({basis.foundation_valid_from})",
                envelope.message_id,
            )
        return envelope

    # --- entry point --------------------------------------------------------
    def ingest(self, batch: IngestionBatch) -> BatchProgress:
        """Ingest one batch, resuming it if it was interrupted. Returns its progress."""
        with self._lock:
            return self._ingest(batch)

    def _refused(
        self, batch: IngestionBatch, digest: str, refusal: _Refused, persist: bool
    ) -> BatchProgress:
        now = self._clock()
        progress = BatchProgress(
            batch_id=batch.batch_id,
            site_id=batch.site_id,
            source_id=batch.source_id,
            gateway_id=batch.gateway_id,
            source_mode=batch.source_mode,
            batch_digest=digest,
            total=len(batch.envelopes),
            processed=0,
            accepted=0,
            duplicates=0,
            rejected=0,
            conflicts=0,
            status="REFUSED",
            refusal_kind=refusal.kind,
            refusal_detail=refusal.detail,
            started_at=now,
            completed_at=now,
            window_start=None,
            window_end=None,
        )
        if persist:
            evidence = self._store.load_site(batch.site_id)
            others = tuple(p for p in evidence.batches if p.batch_id != batch.batch_id)
            self._store.save_site(replace(evidence, batches=others + (progress,)))
        return progress

    def _conflict(
        self, evidence: SiteEvidence, batch: IngestionBatch, digest: str, other_site: str | None = None
    ) -> BatchProgress:
        detail = (
            f"this batch id was released at {other_site}; a batch id names one release "
            "in the whole store, so this one is refused"
            if other_site is not None
            else "this batch id was released with other content; the original "
            "release is kept and this one is refused"
        )
        # One rejection per distinct refusal (batch id, content digest), so a
        # retried post does not inflate the Site's rejection count (T027 N5).
        seen = any(
            r.kind == "BATCH_ID_CONFLICT"
            and r.batch_id == batch.batch_id
            and r.content_digest == digest
            for r in evidence.rejections
        )
        if not seen:
            rejection = Rejection(
                batch_id=batch.batch_id,
                index=None,
                message_id=None,
                kind="BATCH_ID_CONFLICT",
                field="batch_id",
                detail=detail,
                received_at=self._clock(),
                content_digest=digest,
            )
            self._store.save_site(replace(evidence, rejections=evidence.rejections + (rejection,)))
        return self._refused(batch, digest, _Refused("BATCH_ID_CONFLICT", detail), persist=False)

    def _ingest(self, batch: IngestionBatch) -> BatchProgress:
        digest = batch_digest(batch)
        try:
            site = self._site(batch)
        except _Refused as refusal:
            # No Site document to write to: the refusal is answered, not stored.
            return self._refused(batch, digest, refusal, persist=False)

        evidence = self._store.load_site(site.site_id)
        existing = next((p for p in evidence.batches if p.batch_id == batch.batch_id), None)
        elsewhere = find_batch(self._store, batch.batch_id) if existing is None else None
        if elsewhere is not None and elsewhere.site_id != site.site_id:
            # A batch id names one release in the whole store, because
            # GET /api/ingestion/batches/{id} looks it up without a Site (T027 N4).
            return self._conflict(evidence, batch, digest, other_site=elsewhere.site_id)
        if existing is not None and existing.status != "REFUSED":
            if existing.batch_digest != digest:
                return self._conflict(evidence, batch, digest)
            if existing.status == "COMPLETED":
                return existing

        try:
            self._mapping(batch)
            basis = self._configuration(batch, site)
        except _Refused as refusal:
            return self._refused(batch, digest, refusal, persist=True)

        if existing is None or existing.status == "REFUSED":
            progress = BatchProgress(
                batch_id=batch.batch_id,
                site_id=site.site_id,
                source_id=batch.source_id,
                gateway_id=batch.gateway_id,
                source_mode=batch.source_mode,
                batch_digest=digest,
                total=len(batch.envelopes),
                processed=0,
                accepted=0,
                duplicates=0,
                rejected=0,
                conflicts=0,
                status="IN_PROGRESS",
                refusal_kind=None,
                refusal_detail=None,
                started_at=self._clock(),
                completed_at=None,
                window_start=None,
                window_end=None,
            )
            evidence = _with_progress(evidence, progress)
            self._store.save_site(evidence)
        else:
            progress = existing

        records = {record.message_id: record for record in evidence.records}
        new_records: list[AcceptedRecord] = []
        new_rejections: list[Rejection] = []
        new_conflicts: list[Conflict] = []
        handled_this_call = 0

        for index in range(progress.processed, len(batch.envelopes)):
            if self._fail_after is not None and handled_this_call >= self._fail_after:
                raise IngestionInterrupted(
                    f"test fault: interrupted after {handled_this_call} envelopes"
                )
            text = batch.envelopes[index]
            content = envelope_content_digest(text)
            now = self._clock()
            try:
                envelope = self._check(text, batch, basis)
            except EnvelopeRejected as refusal:
                new_rejections.append(
                    Rejection(batch.batch_id, index, None, refusal.kind, refusal.field,
                              refusal.detail, now, content)
                )
                progress = replace(progress, rejected=progress.rejected + 1)
            except _Rejected as refusal:
                new_rejections.append(
                    Rejection(batch.batch_id, index, refusal.message_id, refusal.kind,
                              refusal.field, refusal.detail, now, content)
                )
                progress = replace(progress, rejected=progress.rejected + 1)
            else:
                known = records.get(envelope.message_id)
                if known is None:
                    record = _accepted_record(envelope, text, content, batch, now)
                    records[record.message_id] = record
                    new_records.append(record)
                    progress = _widen(replace(progress, accepted=progress.accepted + 1), envelope)
                elif known.content_digest == content:
                    progress = _widen(replace(progress, duplicates=progress.duplicates + 1), envelope)
                else:
                    new_conflicts.append(
                        Conflict(envelope.message_id, batch.batch_id, known.content_digest,
                                 content, now)
                    )
                    progress = replace(progress, conflicts=progress.conflicts + 1)
            progress = replace(progress, processed=index + 1)
            handled_this_call += 1
            if (index + 1) % self._chunk_size == 0:
                evidence = self._flush(evidence, progress, new_records, new_rejections, new_conflicts)

        progress = replace(progress, status="COMPLETED", completed_at=self._clock())
        evidence = self._flush(evidence, progress, new_records, new_rejections, new_conflicts)
        return progress

    def _flush(
        self,
        evidence: SiteEvidence,
        progress: BatchProgress,
        records: list[AcceptedRecord],
        rejections: list[Rejection],
        conflicts: list[Conflict],
    ) -> SiteEvidence:
        evidence = _with_progress(
            replace(
                evidence,
                records=evidence.records + tuple(records),
                rejections=evidence.rejections + tuple(rejections),
                conflicts=evidence.conflicts + tuple(conflicts),
            ),
            progress,
        )
        self._store.save_site(evidence)
        records.clear()
        rejections.clear()
        conflicts.clear()
        return evidence


class _Rejected(Exception):
    def __init__(self, kind: str, field: str, detail: str, message_id: str | None) -> None:
        self.kind = kind
        self.field = field
        self.detail = detail
        self.message_id = message_id
        super().__init__(f"{kind} at {field}: {detail}")


def _with_progress(evidence: SiteEvidence, progress: BatchProgress) -> SiteEvidence:
    batches = tuple(p for p in evidence.batches if p.batch_id != progress.batch_id)
    return replace(evidence, batches=batches + (progress,))


def _widen(progress: BatchProgress, envelope: SourceEnvelope) -> BatchProgress:
    start = progress.window_start
    end = progress.window_end
    return replace(
        progress,
        window_start=envelope.source_time if start is None else min(start, envelope.source_time),
        window_end=envelope.source_time if end is None else max(end, envelope.source_time),
    )
