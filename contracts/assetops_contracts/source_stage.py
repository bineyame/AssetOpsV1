"""A Draft's staged source envelopes: immutable, reloadable, and not evidence.

v4 section 11.3, Draft: the world may run, the gateway may generate canonical
envelopes, and they are persisted as staging - and no Site history changes. This
module is the stage as a record, the rule that admits an envelope to it, and the
persisted document it is written as. It opens no file; the composition leaf does.

## Nothing here is accepted evidence, and that is not a label

A stage is what the gateway WOULD release. Releasing it is a Commit (T027), and
acceptance is ingestion's, which stamps `received_at`. Until then a stage is a
Simulator Lab artifact, served only behind the Lab gate, and
`tools/checks/dependency-direction.ps1` keeps every product module except the
gated Lab surface from importing this module at all.

## Immutable by admission rather than by convention

`admit` is the only way content enters a stage, and it only ever appends. An
envelope whose message id is already staged is either byte-identical to the one
staged - an idempotent retry, counted and discarded - or it is a `StageConflict`,
raised, with the staged record untouched. There is no update and no delete here
or in the store that persists this.

## The mapping is frozen into the stage

A stage carries the whole `SourceMappingSet` it was staged under, and reading a
stage reads THAT mapping. Changing the gateway's current mapping therefore cannot
reinterpret an envelope already staged, and an envelope mapped under a different
mapping is refused at admission rather than mixed in.

## Eligibility needs the stage to say how far it was published

A completed execution beside a readable stage does not prove the stage holds
what that execution published: a final write can fail while the process lives
on, and a publication the gateway or the stage refused leaves the stage behind
the world. So a stage records `boundaries_total` - how many boundaries the run
it stages covers - and `published_through`, how many of them have had their
readings published into it successfully. It moves only when an admission is
WRITTEN, and a stage whose watermark is short of its total is not eligible
(`STAGING_INCOMPLETE`), whatever the execution says. This is a progress record,
not T027's seal: it says what was published, and releasing it is still Commit's.

## Integrity, and what a reader sees when it fails

The persisted document carries a BLAKE2b-256 digest over its canonical content,
and every envelope is persisted as its own canonical text. A document that does
not parse, is not canonical, states another schema, holds an envelope the strict
parser refuses, or whose digest does not match its content is `StageUnreadable`:
the inspector shows that and why, and the stage is not eligible for release.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Sequence

from assetops_contracts.identity import DIGEST_NAME, identity_digest
from assetops_contracts.source_envelope import (
    SOURCE_ENVELOPE_SCHEMA_ID,
    SOURCE_ENVELOPE_SCHEMA_VERSION,
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

#: The persisted stage document's own layout. Separate from the envelope schema:
#: the envelope is what crosses to ingestion and the stage is the Lab's container.
#:
#: Two since the T023 fix round, which added the publication watermark. Schema
#: one never left the T023 branch; a stage written in it reads as unreadable
#: rather than as a stage whose completeness is assumed.
SOURCE_STAGE_SCHEMA_VERSION = 2

#: Where a Draft's staging is.
SOURCE_STAGE_STATUSES = frozenset({"NOT_STAGED", "STAGED", "STAGE_UNREADABLE"})

#: Why a stage is not eligible for release. Release itself does not exist in
#: this build; eligibility is the condition a later Commit will require.
RELEASE_BLOCKERS = frozenset(
    {
        "NOTHING_STAGED",
        "EXECUTION_NOT_COMPLETED",
        "INTEGRITY_FAILURE",
        "CONFLICTING_PUBLICATION",
        "STAGING_INCOMPLETE",
    }
)

#: The two kinds of refused admission. A changed payload under a staged message
#: id, and an envelope mapped under a mapping this stage did not freeze.
STAGE_CONFLICT_KINDS = frozenset({"CONTENT_CONFLICT", "MAPPING_CONFLICT"})

SOURCE_STAGE_STATUS_STATEMENTS: dict[str, str] = {
    "NOT_STAGED": (
        "No source envelope has been staged for this draft. Envelopes are staged "
        "as an execution publishes readings, so a draft nothing has executed has "
        "none."
    ),
    "STAGED": (
        "These are the canonical source envelopes the simulated gateway "
        "published for this draft, exactly as persisted and re-read from the "
        "stage. They are staged, not released: nothing has been committed, "
        "nothing has reached ingestion, and no site history, evidence or finding "
        "has been written from them."
    ),
    "STAGE_UNREADABLE": (
        "A stage exists for this draft and it failed its integrity check, so none "
        "of its content is presented as releasable. The stage is left exactly as "
        "it is; the detail names what failed."
    ),
}

RELEASE_BLOCKER_STATEMENTS: dict[str, str] = {
    "NOTHING_STAGED": "There is nothing staged to release.",
    "EXECUTION_NOT_COMPLETED": (
        "The execution that publishes into this stage has not completed, so the "
        "stage may still be missing envelopes a completed run would have "
        "published."
    ),
    "INTEGRITY_FAILURE": (
        "The persisted stage failed its integrity check, and content that cannot "
        "be verified is not releasable."
    ),
    # What the watermark establishes and no more. It is short on every healthy
    # run still executing, so it may not assert that anything failed: the first
    # wording did, and the review (R4) caught it saying so of a run that was
    # merely part way through. A failure is named as a possibility only.
    "STAGING_INCOMPLETE": (
        "The stage has not yet recorded publication through the last boundary "
        "of its run. That is expected while the run is still executing; after "
        "it has finished, it can mean a stage write failed or a publication "
        "was refused. Either way the stage may not hold every envelope the run "
        "publishes, and a stage that may be incomplete is not releasable."
    ),
    "CONFLICTING_PUBLICATION": (
        "The gateway attempted to publish different content under a message id "
        "already staged. The staged envelope was kept and the attempt refused; a "
        "stage with a refused conflicting publication is not releasable."
    ),
}


class StageConflict(Exception):
    """An envelope was refused admission and the stage was left unchanged."""

    def __init__(self, kind: str, message_id: str, detail: str) -> None:
        if kind not in STAGE_CONFLICT_KINDS:
            raise ValueError(f"{kind!r} is not a stage conflict kind.")
        self.kind = kind
        self.message_id = message_id
        self.detail = detail
        super().__init__(f"{kind} for message {message_id}: {detail}")


class StageUnreadable(Exception):
    """A persisted stage that cannot be presented as valid content."""

    def __init__(self, run_id: str, detail: str) -> None:
        self.run_id = run_id
        self.detail = detail
        super().__init__(f"The stage for {run_id} is unreadable: {detail}")


@dataclass(frozen=True)
class RefusedPublication:
    """A publication the stage refused, recorded by id and kind only.

    No content: the refused content is exactly what was NOT admitted, and a
    record of it is not a second place for it to live.
    """

    message_id: str
    kind: str

    def __post_init__(self) -> None:
        if self.kind not in STAGE_CONFLICT_KINDS:
            raise ValueError(f"{self.kind!r} is not a stage conflict kind.")


@dataclass(frozen=True)
class SourceStage:
    """One Draft's staged envelopes, under the mapping they were staged with."""

    run_id: str
    site_id: str
    source_id: str
    gateway_id: str
    mapping: SourceMappingSet
    envelopes: tuple[SourceEnvelope, ...] = ()
    refused: tuple[RefusedPublication, ...] = ()
    #: How many boundaries the staged run covers, and through how many of them
    #: every reading has been published into this stage and written.
    boundaries_total: int = 0
    published_through: int = 0

    def __post_init__(self) -> None:
        for name in ("boundaries_total", "published_through"):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ValueError(f"A stage's {name} is a whole number, not {value!r}.")
        if self.published_through > self.boundaries_total:
            raise ValueError(
                f"The stage for {self.run_id} claims publication through "
                f"{self.published_through} of {self.boundaries_total} boundaries."
            )
        seen: set[str] = set()
        for envelope in self.envelopes:
            if type(envelope) is not SourceEnvelope:
                raise EnvelopeRejected(
                    "NOT_AN_ENVELOPE",
                    "envelope",
                    f"a stage holds SourceEnvelope records and nothing else, not "
                    f"{type(envelope).__name__}",
                )
            _same_publisher(self, envelope)
            check_against_mapping(envelope, self.mapping)
            if envelope.message_id in seen:
                raise ValueError(
                    f"Message {envelope.message_id} is staged twice in the stage "
                    f"for {self.run_id}."
                )
            seen.add(envelope.message_id)

    def envelope(self, message_id: str) -> SourceEnvelope | None:
        for item in self.envelopes:
            if item.message_id == message_id:
                return item
        return None


def _same_publisher(stage: SourceStage, envelope: SourceEnvelope) -> None:
    for name in ("site_id", "source_id", "gateway_id"):
        if getattr(envelope, name) != getattr(stage, name):
            raise EnvelopeRejected(
                "INVALID_IDENTITY",
                f"source.{name}",
                f"the envelope names {getattr(envelope, name)!r} and this stage "
                f"publishes for {getattr(stage, name)!r}",
            )


@dataclass(frozen=True)
class Admission:
    """What admitting a batch did: the new stage and what happened to each."""

    stage: SourceStage
    added: int
    already_staged: int


def admit(
    stage: SourceStage,
    envelopes: Sequence[object],
    *,
    published_through: int | None = None,
) -> Admission:
    """Append what is new; accept an identical retry; refuse a conflict.

    Anything that is not a `SourceEnvelope` instance is refused as
    `NOT_AN_ENVELOPE`, whatever it looks like - a dict, a projection, an
    observation. Admission is all or nothing: a conflict anywhere in the batch
    raises before the stage changes at all - including its watermark.

    `published_through` is how many boundaries the batch covers completely. It
    only ever moves forward, so a stale caller cannot make a stage look less
    published than it was - or, by passing nothing, more.
    """
    staged = {item.message_id: item for item in stage.envelopes}
    added: list[SourceEnvelope] = []
    repeated = 0
    for candidate in envelopes:
        if type(candidate) is not SourceEnvelope:
            raise EnvelopeRejected(
                "NOT_AN_ENVELOPE",
                "envelope",
                f"only a SourceEnvelope may be staged, not "
                f"{type(candidate).__name__}",
            )
        if (candidate.mapping_set_id, candidate.mapping_version) != (
            stage.mapping.mapping_set_id,
            stage.mapping.mapping_version,
        ):
            raise StageConflict(
                "MAPPING_CONFLICT",
                candidate.message_id,
                f"mapped under {candidate.mapping_set_id} "
                f"v{candidate.mapping_version}; this stage froze "
                f"{stage.mapping.mapping_set_id} v{stage.mapping.mapping_version}",
            )
        _same_publisher(stage, candidate)
        check_against_mapping(candidate, stage.mapping)
        existing = staged.get(candidate.message_id)
        if existing is not None:
            if canonical_envelope_json(existing) == canonical_envelope_json(
                candidate
            ):
                repeated += 1
                continue
            raise StageConflict(
                "CONTENT_CONFLICT",
                candidate.message_id,
                "a different payload was published under a message id already "
                "staged; the staged envelope is kept and this one refused",
            )
        staged[candidate.message_id] = candidate
        added.append(candidate)
    return Admission(
        stage=replace(
            stage,
            envelopes=stage.envelopes + tuple(added),
            published_through=(
                stage.published_through
                if published_through is None
                else max(stage.published_through, published_through)
            ),
        ),
        added=len(added),
        already_staged=repeated,
    )


def with_refusal(stage: SourceStage, refusal: StageConflict) -> SourceStage:
    """The same stage, recording that one publication was refused."""
    record = RefusedPublication(message_id=refusal.message_id, kind=refusal.kind)
    if record in stage.refused:
        return stage
    return replace(stage, refused=stage.refused + (record,))


def stage_integrity_digest(stage: SourceStage) -> str:
    """The digest over everything a stage asserts, in canonical form."""
    return identity_digest(
        [
            "source-stage",
            SOURCE_STAGE_SCHEMA_VERSION,
            stage.run_id,
            stage.site_id,
            stage.source_id,
            stage.gateway_id,
            canonical_json(mapping_set_document(stage.mapping)),
            tuple(canonical_envelope_json(item) for item in stage.envelopes),
            tuple((item.message_id, item.kind) for item in stage.refused),
            stage.boundaries_total,
            stage.published_through,
        ]
    )


def stage_document(stage: SourceStage) -> dict[str, Any]:
    return {
        "stage_schema_version": SOURCE_STAGE_SCHEMA_VERSION,
        "envelope_schema": {
            "id": SOURCE_ENVELOPE_SCHEMA_ID,
            "version": SOURCE_ENVELOPE_SCHEMA_VERSION,
        },
        "run_id": stage.run_id,
        "site_id": stage.site_id,
        "source_id": stage.source_id,
        "gateway_id": stage.gateway_id,
        "mapping": mapping_set_document(stage.mapping),
        # Each envelope as its own canonical text: what is persisted IS what the
        # inspector shows, byte for byte, rather than a re-rendering of it.
        "envelopes": [canonical_envelope_json(item) for item in stage.envelopes],
        "refused": [
            {"message_id": item.message_id, "kind": item.kind}
            for item in stage.refused
        ],
        "boundaries_total": stage.boundaries_total,
        "published_through": stage.published_through,
        "integrity": {
            "algorithm": DIGEST_NAME,
            "digest": stage_integrity_digest(stage),
        },
    }


def stage_text(stage: SourceStage) -> str:
    """The exact text a stage is persisted as."""
    return canonical_json(stage_document(stage))


_STAGE_KEYS = frozenset(
    {
        "stage_schema_version",
        "envelope_schema",
        "run_id",
        "site_id",
        "source_id",
        "gateway_id",
        "mapping",
        "envelopes",
        "refused",
        "boundaries_total",
        "published_through",
        "integrity",
    }
)


def parse_stage_text(text: str, run_id: str) -> SourceStage:
    """A persisted stage, verified, or `StageUnreadable` saying why not.

    Every failure is the same exception carrying a reason, because to a reader
    they are one fact - this content cannot be presented as valid - and the
    reason is what they act on.
    """
    try:
        document = load_canonical_json(text)
    except EnvelopeRejected as error:
        raise StageUnreadable(
            run_id,
            f"the persisted stage is not complete, well-formed JSON "
            f"({error.detail}); a truncated or partly written stage reads as "
            "this and never as a shorter valid one",
        ) from error
    if not isinstance(document, dict):
        raise StageUnreadable(run_id, "the persisted stage is not an object")
    # The schema first: a stage from another schema is reported as that, not
    # as a list of the fields this schema would have wanted from it.
    stated = document.get("stage_schema_version")
    if type(stated) is not int or stated != SOURCE_STAGE_SCHEMA_VERSION:
        raise StageUnreadable(
            run_id,
            f"it states stage schema {stated!r} and this build reads "
            f"{SOURCE_STAGE_SCHEMA_VERSION} only",
        )
    unknown = sorted(set(document) - _STAGE_KEYS)
    missing = sorted(_STAGE_KEYS - set(document))
    if unknown or missing:
        raise StageUnreadable(
            run_id,
            f"the persisted stage carries {unknown or 'nothing'} beyond its "
            f"schema and lacks {missing or 'nothing'}",
        )
    if document["stage_schema_version"] != SOURCE_STAGE_SCHEMA_VERSION or (
        type(document["stage_schema_version"]) is not int
    ):
        raise StageUnreadable(
            run_id,
            f"it states stage schema {document['stage_schema_version']!r} and "
            f"this build reads {SOURCE_STAGE_SCHEMA_VERSION} only",
        )
    if document["envelope_schema"] != {
        "id": SOURCE_ENVELOPE_SCHEMA_ID,
        "version": SOURCE_ENVELOPE_SCHEMA_VERSION,
    }:
        raise StageUnreadable(
            run_id,
            f"it states envelope schema {document['envelope_schema']!r} and this "
            f"build reads {SOURCE_ENVELOPE_SCHEMA_ID} "
            f"v{SOURCE_ENVELOPE_SCHEMA_VERSION} only",
        )
    if document["run_id"] != run_id:
        raise StageUnreadable(
            run_id, f"it declares run {document['run_id']!r}, not this run"
        )
    try:
        mapping = parse_mapping_set(document["mapping"])
        envelopes = document["envelopes"]
        refused = document["refused"]
        if not isinstance(envelopes, list) or not isinstance(refused, list):
            raise StageUnreadable(run_id, "its envelopes or refusals are not lists")
        stage = SourceStage(
            run_id=run_id,
            site_id=document["site_id"],
            source_id=document["source_id"],
            gateway_id=document["gateway_id"],
            mapping=mapping,
            envelopes=tuple(parse_canonical_envelope_json(item) for item in envelopes),
            refused=tuple(
                RefusedPublication(
                    message_id=str(item["message_id"]), kind=str(item["kind"])
                )
                for item in refused
            ),
            boundaries_total=document["boundaries_total"],
            published_through=document["published_through"],
        )
    except EnvelopeRejected as error:
        raise StageUnreadable(
            run_id, f"a staged record fails the strict schema: {error}"
        ) from error
    except (KeyError, TypeError, ValueError) as error:
        raise StageUnreadable(
            run_id, f"a staged record is malformed: {error}"
        ) from error
    integrity = document["integrity"]
    expected = stage_integrity_digest(stage)
    if integrity != {"algorithm": DIGEST_NAME, "digest": expected}:
        raise StageUnreadable(
            run_id,
            "its integrity digest does not match its content, so the content "
            "was changed after it was staged",
        )
    if stage_text(stage) != text:
        raise StageUnreadable(
            run_id,
            "it is not in canonical form, so it was not written by a stage writer",
        )
    return stage


def release_blockers(
    status: str, execution_status: str, stage: SourceStage | None
) -> tuple[str, ...]:
    """Every reason a stage is not eligible for release, or none.

    Eligible means: the stage verified, it holds something, nothing was refused
    into it, the execution publishing into it completed, AND the stage itself
    records that every boundary of that run was published into it. The last
    condition is the one a completed execution cannot vouch for. It does NOT mean
    released - nothing in this build releases anything.
    """
    if status == "STAGE_UNREADABLE":
        return ("INTEGRITY_FAILURE",)
    blockers: list[str] = []
    if stage is None or not stage.envelopes:
        blockers.append("NOTHING_STAGED")
    if execution_status != "COMPLETED":
        blockers.append("EXECUTION_NOT_COMPLETED")
    if stage is not None and stage.refused:
        blockers.append("CONFLICTING_PUBLICATION")
    if stage is not None and stage.published_through < stage.boundaries_total:
        blockers.append("STAGING_INCOMPLETE")
    return tuple(blockers)


@dataclass(frozen=True)
class SourceStageView:
    """What the gated inspector is handed: the verified stage, or why not.

    `stage` is the content re-read from persistence and verified - never a live
    runtime object - so what the inspector shows as releasable is what a reload
    reads.
    """

    run_id: str
    status: str
    statement: str
    execution_status: str
    release_blockers: tuple[str, ...]
    stage: SourceStage | None
    integrity_digest: str | None
    unreadable_detail: str | None = None
    notes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.status not in SOURCE_STAGE_STATUSES:
            raise ValueError(f"{self.status!r} is not a stage status.")
        for blocker in self.release_blockers:
            if blocker not in RELEASE_BLOCKERS:
                raise ValueError(f"{blocker!r} is not a release blocker.")
        if (self.status == "STAGED") != (self.stage is not None):
            raise ValueError(
                f"A stage view is {self.status} and "
                f"{'carries' if self.stage is not None else 'carries no'} stage."
            )
        if (self.status == "STAGE_UNREADABLE") != (
            self.unreadable_detail is not None
        ):
            raise ValueError("Only an unreadable stage names what failed.")

    @property
    def release_eligible(self) -> bool:
        return not self.release_blockers
