"""IngestionBatch V2: one sealed, homogeneous gateway upload unit (S2-01b).

Technical design 3. A V2 batch carries canonical SourceEnvelope V3 TEXTS in
ordinal order, all from one `(site, gateway, source)` stream, one binding-set
version with its snapshot hash, and one Foundation reference. It is a separate
module so the v1 batch reader (`ingestion_batch`) stays exactly as it was.

## Digest

`payload_sha256` is SHA-256 over the UTF-8 bytes of the canonical JSON of the
batch document WITHOUT the `payload_sha256` key (sorted keys, no whitespace,
`ensure_ascii=False`). The parser recomputes it; a sender digest is never
trusted, and a body is never re-formatted before hashing.

## Identity

`batch_id` is SHA-256 over the length-delimited tuple
`(BATCH_ID_V2_DOMAIN, gateway_id, source_id, sequence_epoch, snapshot_sha256,
decimal(first_sequence), decimal(last_sequence), decimal(count))`. A message is
sealed into exactly one batch, so the tuple names one batch; a retry after a
restart carries the same id and the same bytes.

## Homogeneity and bounds

W2-00 (ruling 3): a schema-4 text, or a schema-3 text carrying a V4-only kind, is read by its header
only (message identity and order, source/mapping scope); S2 decides the rest per ordinal.

Every envelope's site/gateway/source and binding set/version equal the batch's,
and it shares one sequence epoch; ordinals follow ascending sequence. A batch
holds 1..`MAX_BATCH_ENVELOPES` envelopes and at most `MAX_BATCH_BYTES` of
canonical text. No field can carry a Lab run id or any private cause: the key
set is exact at every level.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from assetops_contracts.source_envelope import (
    EnvelopeRejected,
    canonical_json,
    load_canonical_json,
)
from assetops_contracts.source_envelope_v3 import (
    SourceEnvelopeV3,
    length_delimited,
    parse_canonical_envelope_v3_text,
    sha256_hex,
    text_sha256,
)
from assetops_contracts.source_envelope_v4 import (
    EnvelopeHeader,
    read_envelope_header,
    uses_v4_header_path,
)

INGESTION_BATCH_V2_SCHEMA_ID = "assetops.ingestion-batch"
INGESTION_BATCH_V2_SCHEMA_VERSION = 2
BATCH_ID_V2_DOMAIN = "assetops.ingestion-batch.batch-id.v2"
SOURCE_MODES_V2 = frozenset({"LIVE", "SIMULATED"})
MAX_BATCH_ENVELOPES = 256
MAX_BATCH_BYTES = 1_048_576

_IDENTIFIER = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]{0,126}[A-Za-z0-9])?")
_DIGEST = re.compile(r"[0-9a-f]{64}")
#: The Foundation validity start is carried as the registered snapshot spells it.
_REGISTERED_INSTANT = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z")


class BatchRejected(ValueError):
    def __init__(self, kind: str, field: str, detail: str) -> None:
        self.kind = kind
        self.field = field
        self.detail = detail
        super().__init__(f"{kind} at {field}: {detail}")


def batch_v2_id(
    *,
    gateway_id: str,
    source_id: str,
    sequence_epoch: str,
    snapshot_sha256: str,
    first_sequence: int,
    last_sequence: int,
    count: int,
) -> str:
    return sha256_hex(
        length_delimited(
            [
                BATCH_ID_V2_DOMAIN,
                gateway_id,
                source_id,
                sequence_epoch,
                snapshot_sha256,
                str(first_sequence),
                str(last_sequence),
                str(count),
            ]
        )
    )


@dataclass(frozen=True)
class IngestionBatchV2:
    batch_id: str
    site_id: str
    gateway_id: str
    source_id: str
    source_mode: str
    foundation_version: int
    foundation_valid_from: str
    binding_set_id: str
    binding_version: int
    snapshot_sha256: str
    envelopes: tuple[str, ...]
    payload_sha256: str


def _body(
    *,
    batch_id: str,
    site_id: str,
    gateway_id: str,
    source_id: str,
    source_mode: str,
    foundation_version: int,
    foundation_valid_from: str,
    binding_set_id: str,
    binding_version: int,
    snapshot_sha256: str,
    envelopes: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "schema": {"id": INGESTION_BATCH_V2_SCHEMA_ID, "version": INGESTION_BATCH_V2_SCHEMA_VERSION},
        "batch_id": batch_id,
        "site_id": site_id,
        "gateway_id": gateway_id,
        "source_id": source_id,
        "source_mode": source_mode,
        "configuration": {
            "foundation_version": foundation_version,
            "foundation_valid_from": foundation_valid_from,
        },
        "mapping": {
            "binding_set_id": binding_set_id,
            "version": binding_version,
            "snapshot_sha256": snapshot_sha256,
        },
        "envelopes": list(envelopes),
    }


def _check_homogeneous(
    parsed: list[SourceEnvelopeV3 | EnvelopeHeader],
    *,
    site_id: str,
    gateway_id: str,
    source_id: str,
    binding_set_id: str,
    binding_version: int,
) -> None:
    epochs = {e.sequence_epoch for e in parsed}
    if len(epochs) != 1:
        raise BatchRejected("NOT_HOMOGENEOUS", "envelopes", "more than one sequence epoch")
    previous = 0
    for ordinal, e in enumerate(parsed):
        where = f"envelopes[{ordinal}]"
        for field, want in (
            ("site_id", site_id),
            ("gateway_id", gateway_id),
            ("source_id", source_id),
            ("binding_set_id", binding_set_id),
            ("binding_version", binding_version),
        ):
            if getattr(e, field) != want:
                raise BatchRejected("NOT_HOMOGENEOUS", f"{where}.{field}", f"{getattr(e, field)!r} is not {want!r}")
        if e.sequence <= previous:
            raise BatchRejected("NOT_ORDERED", f"{where}.sequence", "ordinals follow ascending sequence")
        previous = e.sequence


def seal_batch_v2(
    *,
    site_id: str,
    gateway_id: str,
    source_id: str,
    source_mode: str,
    foundation_version: int,
    foundation_valid_from: str,
    binding_set_id: str,
    binding_version: int,
    snapshot_sha256: str,
    envelope_texts: list[str] | tuple[str, ...],
) -> tuple[IngestionBatchV2, str]:
    """Build one batch and its exact canonical text from canonical envelope texts."""
    texts = tuple(envelope_texts)
    if not texts:
        raise BatchRejected("EMPTY", "envelopes", "a batch holds at least one envelope")
    if len(texts) > MAX_BATCH_ENVELOPES:
        raise BatchRejected("TOO_LARGE", "envelopes", f"more than {MAX_BATCH_ENVELOPES} envelopes")
    if source_mode not in SOURCE_MODES_V2:
        raise BatchRejected("INVALID_FIELD", "source_mode", f"{source_mode!r}")
    if not _REGISTERED_INSTANT.fullmatch(foundation_valid_from):
        raise BatchRejected("INVALID_FIELD", "configuration.foundation_valid_from", foundation_valid_from)
    if not _DIGEST.fullmatch(snapshot_sha256):
        raise BatchRejected("INVALID_FIELD", "mapping.snapshot_sha256", "not a SHA-256 hex digest")
    try:
        # W2-00 ruling 3: ordinary schema-3 texts stay strict; a schema-4 text (or schema 3 carrying a V4-only
        # kind) is admitted by its header only, so S2 decides its payload, timing and bytes per ordinal.
        parsed = [read_envelope_header(t) if uses_v4_header_path(t) else parse_canonical_envelope_v3_text(t)
                  for t in texts]
    except EnvelopeRejected as error:
        raise BatchRejected("INVALID_ENVELOPE", f"envelopes.{error.field}", error.detail) from error
    _check_homogeneous(
        parsed,
        site_id=site_id,
        gateway_id=gateway_id,
        source_id=source_id,
        binding_set_id=binding_set_id,
        binding_version=binding_version,
    )
    batch_id = batch_v2_id(
        gateway_id=gateway_id,
        source_id=source_id,
        sequence_epoch=parsed[0].sequence_epoch,
        snapshot_sha256=snapshot_sha256,
        first_sequence=parsed[0].sequence,
        last_sequence=parsed[-1].sequence,
        count=len(parsed),
    )
    body = _body(
        batch_id=batch_id,
        site_id=site_id,
        gateway_id=gateway_id,
        source_id=source_id,
        source_mode=source_mode,
        foundation_version=foundation_version,
        foundation_valid_from=foundation_valid_from,
        binding_set_id=binding_set_id,
        binding_version=binding_version,
        snapshot_sha256=snapshot_sha256,
        envelopes=texts,
    )
    digest = text_sha256(canonical_json(body))
    text = canonical_json({**body, "payload_sha256": digest})
    if len(text.encode("utf-8")) > MAX_BATCH_BYTES:
        raise BatchRejected("TOO_LARGE", "batch", f"more than {MAX_BATCH_BYTES} bytes")
    batch = IngestionBatchV2(
        batch_id=batch_id,
        site_id=site_id,
        gateway_id=gateway_id,
        source_id=source_id,
        source_mode=source_mode,
        foundation_version=foundation_version,
        foundation_valid_from=foundation_valid_from,
        binding_set_id=binding_set_id,
        binding_version=binding_version,
        snapshot_sha256=snapshot_sha256,
        envelopes=texts,
        payload_sha256=digest,
    )
    return batch, text


_KEYS = {
    "": frozenset(
        {
            "schema",
            "batch_id",
            "site_id",
            "gateway_id",
            "source_id",
            "source_mode",
            "configuration",
            "mapping",
            "envelopes",
            "payload_sha256",
        }
    ),
    "schema": frozenset({"id", "version"}),
    "configuration": frozenset({"foundation_version", "foundation_valid_from"}),
    "mapping": frozenset({"binding_set_id", "version", "snapshot_sha256"}),
}


def _exact(document: object, where: str) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise BatchRejected("WRONG_TYPE", where or "batch", "an object is wanted")
    wanted = _KEYS[where]
    for key in sorted(document):
        if key not in wanted:
            raise BatchRejected("UNKNOWN_FIELD", f"{where}.{key}" if where else key, "not a Batch V2 field")
    for key in sorted(wanted):
        if key not in document:
            raise BatchRejected("MISSING_FIELD", f"{where}.{key}" if where else key, "required")
    return document


def parse_canonical_batch_v2_text(text: object) -> IngestionBatchV2:
    """Exact stored/received bytes back as a batch; every rule re-checked."""
    try:
        document = load_canonical_json(text)
    except EnvelopeRejected as error:
        raise BatchRejected("MALFORMED_TEXT", "batch", error.detail) from error
    top = _exact(document, "")
    schema = _exact(top["schema"], "schema")
    if schema != {"id": INGESTION_BATCH_V2_SCHEMA_ID, "version": INGESTION_BATCH_V2_SCHEMA_VERSION}:
        raise BatchRejected("SCHEMA_UNSUPPORTED", "schema", f"{schema!r}")
    configuration = _exact(top["configuration"], "configuration")
    mapping = _exact(top["mapping"], "mapping")
    for field in ("site_id", "gateway_id", "source_id"):
        if type(top[field]) is not str or not _IDENTIFIER.fullmatch(top[field]):
            raise BatchRejected("INVALID_FIELD", field, "not an identifier")
    if type(top["envelopes"]) is not list or not all(type(t) is str for t in top["envelopes"]):
        raise BatchRejected("WRONG_TYPE", "envelopes", "a list of canonical envelope texts")
    if type(configuration["foundation_version"]) is not int or type(mapping["version"]) is not int:
        raise BatchRejected("WRONG_TYPE", "configuration", "versions are whole numbers")
    batch, rebuilt = seal_batch_v2(
        site_id=top["site_id"],
        gateway_id=top["gateway_id"],
        source_id=top["source_id"],
        source_mode=top["source_mode"],
        foundation_version=configuration["foundation_version"],
        foundation_valid_from=configuration["foundation_valid_from"],
        binding_set_id=mapping["binding_set_id"],
        binding_version=mapping["version"],
        snapshot_sha256=mapping["snapshot_sha256"],
        envelope_texts=top["envelopes"],
    )
    if top["batch_id"] != batch.batch_id:
        raise BatchRejected("INVALID_IDENTITY", "batch_id", "does not match the batch's derived identity")
    if top["payload_sha256"] != batch.payload_sha256:
        raise BatchRejected("DIGEST_MISMATCH", "payload_sha256", "does not match the canonical bytes")
    if rebuilt != text:
        raise BatchRejected("NOT_CANONICAL", "batch", "the text is not its own canonical text")
    return batch
