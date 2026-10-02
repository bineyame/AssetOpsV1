"""The one ingestion interface every source uses: an `IngestionBatch` (T027).

A batch is what a source hands AssetOps ingestion. A committed Simulator Lab
artifact becomes one (`committed_artifact.ingestion_batch`), and an ordinary
live gateway posts one; ingestion cannot tell them apart except by the
`source_mode` the batch states, which it records as provenance and checks
against the Site's own source mode. That is `D2` of the T027 plan and the
reason SIMULATED provenance survives as source provenance and nothing more
(AC4).

The batch document is read strictly (`parse_ingestion_batch_document`): exact
keys at every level, so a document that carries anything beyond the canonical
fields - a `truth`, a `lab_projection`, an `observation`, any private object -
is refused WHOLE with `UNKNOWN_FIELD` (AC16). The envelopes inside are canonical
envelope TEXTS and are not parsed here: ingestion parses them one by one, so a
bad envelope is an inspectable per-record rejection and never sinks its valid
siblings (AC3).

`ConfigurationReference` lives here because both the batch and the committed
artifact carry it: the Site's Foundation version and validity start the
content was produced under, which ingestion resolves against an immutable
configuration registry rather than the Site's current Foundation (AC17).

Must not import `source_stage`: a batch is not staged content.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from assetops_contracts.source_envelope import (
    EnvelopeRejected,
    SourceMappingSet,
    mapping_set_document,
    parse_mapping_set,
)

INGESTION_BATCH_SCHEMA_ID = "assetops.ingestion-batch"
INGESTION_BATCH_SCHEMA_VERSION = 1

#: Where a source's content comes from. Provenance only: it never changes how
#: content is validated or normalized.
SOURCE_MODES = frozenset({"SIMULATED", "LIVE"})

#: Why a whole batch document was refused before any envelope was read.
BATCH_REJECTION_KINDS = frozenset(
    {
        "NOT_A_BATCH",
        "UNKNOWN_FIELD",
        "MISSING_FIELD",
        "WRONG_TYPE",
        "SCHEMA_UNSUPPORTED",
        "INVALID_IDENTITY",
        "INVALID_TIMING",
        "MAPPING_INCOMPATIBLE",
    }
)

_IDENTIFIER = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]{0,126}[A-Za-z0-9])?")
_INSTANT = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")


class IngestionBatchRejected(ValueError):
    """A batch document is not a canonical ingestion batch; refused whole."""

    def __init__(self, kind: str, field: str, detail: str) -> None:
        if kind not in BATCH_REJECTION_KINDS:
            raise ValueError(f"{kind!r} is not a batch rejection kind.")
        self.kind = kind
        self.field = field
        self.detail = detail
        super().__init__(f"{kind} at {field}: {detail}")


def _identifier(value: object, field: str) -> str:
    if type(value) is not str:
        raise IngestionBatchRejected(
            "WRONG_TYPE", field, f"an identifier is text, not {type(value).__name__}"
        )
    if not _IDENTIFIER.fullmatch(value):
        raise IngestionBatchRejected(
            "INVALID_IDENTITY", field, f"{value!r} is not an identifier"
        )
    return value


def _instant(value: object, field: str) -> str:
    if type(value) is not str or not _INSTANT.fullmatch(value):
        raise IngestionBatchRejected(
            "INVALID_TIMING", field, f"{value!r} is not a UTC instant (YYYY-MM-DDTHH:MM:SSZ)"
        )
    return value


@dataclass(frozen=True)
class ConfigurationReference:
    """The Site Foundation version (and its validity start) content was produced under."""

    site_id: str
    foundation_version: int
    foundation_valid_from: str

    def __post_init__(self) -> None:
        _identifier(self.site_id, "configuration.site_id")
        if type(self.foundation_version) is not int or self.foundation_version < 1:
            raise IngestionBatchRejected(
                "WRONG_TYPE",
                "configuration.foundation_version",
                "a Foundation version is a whole number from 1",
            )
        _instant(self.foundation_valid_from, "configuration.foundation_valid_from")


def configuration_document(reference: ConfigurationReference) -> dict[str, Any]:
    return {
        "site_id": reference.site_id,
        "foundation_version": reference.foundation_version,
        "foundation_valid_from": reference.foundation_valid_from,
    }


@dataclass(frozen=True)
class IngestionBatch:
    """One release of canonical envelopes from one source, under one mapping."""

    batch_id: str
    site_id: str
    source_id: str
    gateway_id: str
    source_mode: str
    configuration: ConfigurationReference
    mapping: SourceMappingSet
    #: Canonical envelope TEXTS, in release order. Parsed by ingestion, one by
    #: one, so each is accepted or rejected on its own.
    envelopes: tuple[str, ...]

    def __post_init__(self) -> None:
        _identifier(self.batch_id, "batch_id")
        _identifier(self.site_id, "site_id")
        _identifier(self.source_id, "source_id")
        _identifier(self.gateway_id, "gateway_id")
        if self.source_mode not in SOURCE_MODES:
            raise IngestionBatchRejected(
                "WRONG_TYPE",
                "source_mode",
                f"{self.source_mode!r} is not one of {sorted(SOURCE_MODES)}",
            )
        if type(self.configuration) is not ConfigurationReference:
            raise IngestionBatchRejected(
                "WRONG_TYPE", "configuration", "a ConfigurationReference is wanted"
            )
        if self.configuration.site_id != self.site_id:
            raise IngestionBatchRejected(
                "INVALID_IDENTITY",
                "configuration.site_id",
                "the configuration belongs to another Site than the batch",
            )
        if type(self.mapping) is not SourceMappingSet:
            raise IngestionBatchRejected(
                "WRONG_TYPE", "mapping", "a SourceMappingSet is wanted"
            )
        if type(self.envelopes) is not tuple or any(
            type(text) is not str for text in self.envelopes
        ):
            raise IngestionBatchRejected(
                "WRONG_TYPE",
                "envelopes",
                "envelopes are canonical envelope texts, never objects",
            )


_BATCH_KEYS = frozenset(
    {
        "schema",
        "batch_id",
        "site_id",
        "source_id",
        "gateway_id",
        "source_mode",
        "configuration",
        "mapping",
        "envelopes",
    }
)
_SCHEMA_KEYS = frozenset({"id", "version"})
_CONFIGURATION_KEYS = frozenset({"site_id", "foundation_version", "foundation_valid_from"})


def _exact(document: object, keys: frozenset[str], where: str) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise IngestionBatchRejected("WRONG_TYPE", where, "an object is wanted")
    unknown = sorted(set(document) - keys)
    if unknown:
        raise IngestionBatchRejected(
            "UNKNOWN_FIELD",
            f"{where}.{unknown[0]}" if where else unknown[0],
            f"{unknown} is not part of the canonical ingestion batch; a batch "
            "carrying anything else is refused whole",
        )
    missing = sorted(keys - set(document))
    if missing:
        raise IngestionBatchRejected(
            "MISSING_FIELD",
            f"{where}.{missing[0]}" if where else missing[0],
            f"{missing} is required",
        )
    return document


def ingestion_batch_document(batch: IngestionBatch) -> dict[str, Any]:
    """The canonical batch document a source posts."""
    return {
        "schema": {
            "id": INGESTION_BATCH_SCHEMA_ID,
            "version": INGESTION_BATCH_SCHEMA_VERSION,
        },
        "batch_id": batch.batch_id,
        "site_id": batch.site_id,
        "source_id": batch.source_id,
        "gateway_id": batch.gateway_id,
        "source_mode": batch.source_mode,
        "configuration": configuration_document(batch.configuration),
        "mapping": mapping_set_document(batch.mapping),
        "envelopes": list(batch.envelopes),
    }


def parse_configuration_reference(document: object, where: str) -> ConfigurationReference:
    fields = _exact(document, _CONFIGURATION_KEYS, where)
    return ConfigurationReference(
        site_id=fields["site_id"],
        foundation_version=fields["foundation_version"],
        foundation_valid_from=fields["foundation_valid_from"],
    )


def parse_ingestion_batch_document(document: object) -> IngestionBatch:
    """A posted batch, read strictly. Raises `IngestionBatchRejected`."""
    if not isinstance(document, dict):
        raise IngestionBatchRejected("NOT_A_BATCH", "", "a batch is a JSON object")
    fields = _exact(document, _BATCH_KEYS, "")
    schema = _exact(fields["schema"], _SCHEMA_KEYS, "schema")
    if (schema["id"], schema["version"]) != (
        INGESTION_BATCH_SCHEMA_ID,
        INGESTION_BATCH_SCHEMA_VERSION,
    ) or type(schema["version"]) is not int:
        raise IngestionBatchRejected(
            "SCHEMA_UNSUPPORTED",
            "schema",
            f"this build reads {INGESTION_BATCH_SCHEMA_ID} "
            f"v{INGESTION_BATCH_SCHEMA_VERSION} only",
        )
    configuration = parse_configuration_reference(
        fields["configuration"], "configuration"
    )
    try:
        mapping = parse_mapping_set(fields["mapping"])
    except EnvelopeRejected as refusal:
        kind = (
            refusal.kind
            if refusal.kind in BATCH_REJECTION_KINDS
            else "MAPPING_INCOMPATIBLE"
        )
        raise IngestionBatchRejected(kind, refusal.field, refusal.detail) from refusal
    envelopes = fields["envelopes"]
    if not isinstance(envelopes, list):
        raise IngestionBatchRejected("WRONG_TYPE", "envelopes", "a list is wanted")
    return IngestionBatch(
        batch_id=fields["batch_id"],
        site_id=fields["site_id"],
        source_id=fields["source_id"],
        gateway_id=fields["gateway_id"],
        source_mode=fields["source_mode"],
        configuration=configuration,
        mapping=mapping,
        envelopes=tuple(envelopes),
    )
