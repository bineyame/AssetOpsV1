"""The committed artifact: sealed stage content, immutable, verifiable (T027 D1).

Commit seals eligible staged envelopes into one `CommittedArtifact`: the exact
envelopes (as their canonical texts), a manifest naming each one by message id
and content digest, the frozen mapping they were published under, and the
configuration reference (Site Foundation version and validity start) they were
produced against. Its integrity digest covers the whole canonical document, so
a byte edited anywhere is refused on read (`parse_artifact_text`).

Identity is derived, never allocated: `artifact_id` is `commit-` plus the first
32 hex of a BLAKE2b-256 over (`run_id`, `stage_integrity_digest`) under its own
domain. Sealing the same stage again therefore yields the same artifact id,
which is the batch id ingestion resumes under (AC2).

An artifact is released to ingestion only as an ordinary `IngestionBatch`
(`ingestion_batch`): the same interface any live source uses (AC4). Sealing
writes no evidence; only ingestion does.

This module builds an artifact from envelopes and a mapping, never from a
stage, and must not import `source_stage`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable

from assetops_contracts.identity import identity_digest
from assetops_contracts.ingestion_batch import (
    SOURCE_MODES,
    ConfigurationReference,
    IngestionBatch,
    IngestionBatchRejected,
    configuration_document,
    parse_configuration_reference,
)
from assetops_contracts.source_envelope import (
    EnvelopeRejected,
    SourceEnvelope,
    SourceMappingSet,
    canonical_envelope_json,
    canonical_json,
    check_against_mapping,
    load_canonical_json,
    mapping_set_document,
    parse_canonical_envelope_json,
    parse_mapping_set,
)

__all__ = [
    "ARTIFACT_SCHEMA_ID",
    "ARTIFACT_SCHEMA_VERSION",
    "ArtifactUnreadable",
    "CommittedArtifact",
    "ConfigurationReference",
    "artifact_document",
    "artifact_id_for",
    "artifact_text",
    "envelope_content_digest",
    "ingestion_batch",
    "parse_artifact_text",
    "seal_artifact",
]

ARTIFACT_SCHEMA_ID = "assetops.committed-artifact"
ARTIFACT_SCHEMA_VERSION = 1

ARTIFACT_ID_DOMAIN = "committed-artifact-id-v1"
CONTENT_DIGEST_DOMAIN = "source-envelope-content-v1"
INTEGRITY_DOMAIN = "committed-artifact-integrity-v1"

_IDENTIFIER = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]{0,126}[A-Za-z0-9])?")
_DIGEST = re.compile(r"[0-9a-f]{64}")
_INSTANT = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")


class ArtifactUnreadable(ValueError):
    """An artifact (object or persisted text) is not a sound committed artifact."""

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


def envelope_content_digest(text: str) -> str:
    """BLAKE2b-256 of one envelope's canonical text, under its own domain."""
    return identity_digest([CONTENT_DIGEST_DOMAIN, text])


def artifact_id_for(run_id: str, stage_integrity_digest: str) -> str:
    """The derived artifact id: the same stage always seals to the same id."""
    digest = identity_digest([ARTIFACT_ID_DOMAIN, run_id, stage_integrity_digest])
    return "commit-" + digest[:32]


def _require(condition: bool, detail: str) -> None:
    if not condition:
        raise ArtifactUnreadable(detail)


@dataclass(frozen=True)
class CommittedArtifact:
    """One sealed release. Invalid ones cannot be constructed."""

    artifact_id: str
    run_id: str
    site_id: str
    source_id: str
    gateway_id: str
    #: The run's Site source mode. Provenance only.
    source_mode: str
    configuration: ConfigurationReference
    mapping: SourceMappingSet
    stage_integrity_digest: str
    envelopes: tuple[SourceEnvelope, ...]
    #: (message_id, content_digest) per envelope, in envelope order.
    manifest: tuple[tuple[str, str], ...]
    sealed_at: str

    def __post_init__(self) -> None:
        for name in ("run_id", "site_id", "source_id", "gateway_id"):
            value = getattr(self, name)
            _require(
                type(value) is str and bool(_IDENTIFIER.fullmatch(value)),
                f"{name} {value!r} is not an identifier",
            )
        _require(
            self.source_mode in SOURCE_MODES,
            f"source_mode {self.source_mode!r} is not one of {sorted(SOURCE_MODES)}",
        )
        _require(
            type(self.configuration) is ConfigurationReference,
            "configuration is a ConfigurationReference",
        )
        _require(
            self.configuration.site_id == self.site_id,
            "the configuration reference names another Site",
        )
        _require(type(self.mapping) is SourceMappingSet, "mapping is a SourceMappingSet")
        _require(
            type(self.stage_integrity_digest) is str
            and bool(_DIGEST.fullmatch(self.stage_integrity_digest)),
            "stage_integrity_digest is 64 lowercase hex",
        )
        _require(
            type(self.sealed_at) is str and bool(_INSTANT.fullmatch(self.sealed_at)),
            "sealed_at is a UTC instant",
        )
        _require(
            self.artifact_id == artifact_id_for(self.run_id, self.stage_integrity_digest),
            "artifact_id is not the id derived from the run and stage digest",
        )
        _require(type(self.envelopes) is tuple, "envelopes is a tuple")
        seen: set[str] = set()
        for envelope in self.envelopes:
            _require(type(envelope) is SourceEnvelope, "every envelope is a SourceEnvelope")
            _require(
                (envelope.site_id, envelope.source_id, envelope.gateway_id)
                == (self.site_id, self.source_id, self.gateway_id),
                f"envelope {envelope.message_id} names another site, source or gateway",
            )
            _require(
                envelope.message_id not in seen,
                f"envelope {envelope.message_id} is sealed twice",
            )
            seen.add(envelope.message_id)
            try:
                check_against_mapping(envelope, self.mapping)
            except EnvelopeRejected as refusal:
                raise ArtifactUnreadable(
                    f"envelope {envelope.message_id} is not what the frozen "
                    f"mapping publishes: {refusal}"
                ) from refusal
        _require(
            self.manifest == _manifest(self.envelopes),
            "the manifest does not name exactly these envelopes and their content",
        )

    @property
    def envelope_texts(self) -> tuple[str, ...]:
        return tuple(canonical_envelope_json(envelope) for envelope in self.envelopes)

    @property
    def integrity_digest(self) -> str:
        return identity_digest(
            [INTEGRITY_DOMAIN, canonical_json(_unsigned_document(self))]
        )


def _manifest(envelopes: Iterable[SourceEnvelope]) -> tuple[tuple[str, str], ...]:
    return tuple(
        (envelope.message_id, envelope_content_digest(canonical_envelope_json(envelope)))
        for envelope in envelopes
    )


def seal_artifact(
    *,
    run_id: str,
    site_id: str,
    source_id: str,
    gateway_id: str,
    source_mode: str,
    configuration: ConfigurationReference,
    mapping: SourceMappingSet,
    envelopes: Iterable[SourceEnvelope],
    stage_integrity_digest: str,
    sealed_at: str,
) -> CommittedArtifact:
    """Seal envelopes (stage order) into an artifact. Raises `ArtifactUnreadable`."""
    sealed = tuple(envelopes)
    return CommittedArtifact(
        artifact_id=artifact_id_for(run_id, stage_integrity_digest),
        run_id=run_id,
        site_id=site_id,
        source_id=source_id,
        gateway_id=gateway_id,
        source_mode=source_mode,
        configuration=configuration,
        mapping=mapping,
        stage_integrity_digest=stage_integrity_digest,
        envelopes=sealed,
        manifest=_manifest(sealed),
        sealed_at=sealed_at,
    )


def _unsigned_document(artifact: CommittedArtifact) -> dict[str, Any]:
    return {
        "schema": {"id": ARTIFACT_SCHEMA_ID, "version": ARTIFACT_SCHEMA_VERSION},
        "artifact_id": artifact.artifact_id,
        "run_id": artifact.run_id,
        "site_id": artifact.site_id,
        "source_id": artifact.source_id,
        "gateway_id": artifact.gateway_id,
        "source_mode": artifact.source_mode,
        "configuration": configuration_document(artifact.configuration),
        "mapping": mapping_set_document(artifact.mapping),
        "stage_integrity_digest": artifact.stage_integrity_digest,
        "envelopes": list(artifact.envelope_texts),
        "manifest": [
            {"message_id": message_id, "content_digest": digest}
            for message_id, digest in artifact.manifest
        ],
        "sealed_at": artifact.sealed_at,
    }


def artifact_document(artifact: CommittedArtifact) -> dict[str, Any]:
    document = _unsigned_document(artifact)
    document["integrity_digest"] = artifact.integrity_digest
    return document


def artifact_text(artifact: CommittedArtifact) -> str:
    """The canonical persisted text of an artifact, integrity digest included."""
    return canonical_json(artifact_document(artifact))


_ARTIFACT_KEYS = frozenset(
    {
        "schema",
        "artifact_id",
        "run_id",
        "site_id",
        "source_id",
        "gateway_id",
        "source_mode",
        "configuration",
        "mapping",
        "stage_integrity_digest",
        "envelopes",
        "manifest",
        "sealed_at",
        "integrity_digest",
    }
)


def parse_artifact_text(text: object) -> CommittedArtifact:
    """A persisted artifact, verified byte for byte. Raises `ArtifactUnreadable`."""
    try:
        document = load_canonical_json(text)
    except EnvelopeRejected as refusal:
        raise ArtifactUnreadable(f"not artifact JSON: {refusal.detail}") from refusal
    _require(isinstance(document, dict), "an artifact is a JSON object")
    _require(set(document) == _ARTIFACT_KEYS, "the artifact's keys are not exactly the canonical keys")
    _require(
        document["schema"] == {"id": ARTIFACT_SCHEMA_ID, "version": ARTIFACT_SCHEMA_VERSION},
        f"this build reads {ARTIFACT_SCHEMA_ID} v{ARTIFACT_SCHEMA_VERSION} only",
    )
    _require(canonical_json(document) == text, "the artifact text is not canonical")
    texts = document["envelopes"]
    manifest = document["manifest"]
    _require(isinstance(texts, list) and isinstance(manifest, list), "envelopes and manifest are lists")
    try:
        configuration = parse_configuration_reference(document["configuration"], "configuration")
        mapping = parse_mapping_set(document["mapping"])
        envelopes = tuple(parse_canonical_envelope_json(item) for item in texts)
    except (EnvelopeRejected, IngestionBatchRejected) as refusal:
        raise ArtifactUnreadable(f"artifact content refused: {refusal}") from refusal
    stated_manifest = []
    for row in manifest:
        _require(
            isinstance(row, dict) and set(row) == {"message_id", "content_digest"},
            "a manifest row is exactly {message_id, content_digest}",
        )
        stated_manifest.append((row["message_id"], row["content_digest"]))
    artifact = CommittedArtifact(
        artifact_id=document["artifact_id"],
        run_id=document["run_id"],
        site_id=document["site_id"],
        source_id=document["source_id"],
        gateway_id=document["gateway_id"],
        source_mode=document["source_mode"],
        configuration=configuration,
        mapping=mapping,
        stage_integrity_digest=document["stage_integrity_digest"],
        envelopes=envelopes,
        manifest=tuple(stated_manifest),
        sealed_at=document["sealed_at"],
    )
    _require(
        document["integrity_digest"] == artifact.integrity_digest,
        "the integrity digest does not match the artifact's content",
    )
    _require(artifact_text(artifact) == text, "the artifact does not round-trip to its own text")
    return artifact


def ingestion_batch(artifact: CommittedArtifact) -> IngestionBatch:
    """The artifact as an ordinary ingestion batch: the only thing release hands ingestion."""
    return IngestionBatch(
        batch_id=artifact.artifact_id,
        site_id=artifact.site_id,
        source_id=artifact.source_id,
        gateway_id=artifact.gateway_id,
        source_mode=artifact.source_mode,
        configuration=artifact.configuration,
        mapping=artifact.mapping,
        envelopes=artifact.envelope_texts,
    )
