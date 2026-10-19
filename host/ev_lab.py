"""W2-05b commit 4: the EV Lab run's frozen-input port, projections and schema-7 artifact (q4 Q20/Q23-Q25).

An EV run has no `Execution`/`ModelSpec`. `HostLabExecution.start` re-reads the exact frozen Foundation revision,
binding revision and EV scenario document through `EvInputs`, verifies them (`ev_publication.verify_ev_inputs`),
executes the whole window once and stages the public v2 reports. This module holds the read-only input port, the
Draft and terminal EV projections, and the schema-7 artifact (`execution_kind: EV`): one YAML document with the
frozen IDs/SHAs and the ordered public report texts, never a private document, forcing or history.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Protocol
from uuid import UUID

from assetops_backend.runs.models import SimulationRun
from assetops_backend.runs.source_publication import run_identity_sha256
from assetops_backend.scenarios.ev_parsing import EvScenarioDefinition
from assetops_backend.scenarios.ports import ScenarioNotFound
from assetops_backend.scenarios.service import ScenarioCatalogService
from assetops_contracts.execution_contract import (
    EXECUTION_CONTRACT_VERSION,
    NUMERIC_POLICY,
    NUMERIC_POLICY_VERSION,
)
from assetops_contracts.failures import ExecutionFailure
from assetops_contracts.gateway_report import parse_device_report_v2_text
from assetops_contracts.lab_projection import LAB_EXECUTION_STATUS_STATEMENTS, LabProjection
from assetops_contracts.source_envelope import canonical_json
from assetops_simulator.kernel.model import KERNEL_VERSION

from ev_publication import ev_series_digest_of_texts

EV_ARTIFACT_SCHEMA_VERSION = 7
EV_EXECUTION_KIND = "EV"
EV_MODEL_PROFILE = ("ev-charger", 1)
EV_PUBLICATION_PROFILE = ("ev-publication", 1)

#: The empty EV series: SHA-256 of canonical `[]`.
EMPTY_EV_SERIES_DIGEST = hashlib.sha256(canonical_json([]).encode("utf-8")).hexdigest()

#: q4 Q24: the exact visible note on every NOT_STARTED and terminal EV projection.
EV_NOTES = (
    "EV run: only the private trajectory digest is kept in the run artifact. Public device reports pass through "
    "the registered gateway; empty legacy views make no claim about a vehicle or charging session.",
)

_SHA = re.compile(r"[0-9a-f]{64}")
_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
_INSTANT = "%Y-%m-%dT%H:%M:%SZ"


class EvInputs(Protocol):
    """Read-only re-read of an EV run's frozen inputs. Each call answers None when the record is absent."""

    def foundation_revision(self, tenant_id: UUID, site_record_id: UUID, revision_id: UUID) -> Any | None: ...

    def binding_revision(self, tenant_id: UUID, site_record_id: UUID, binding_set_revision_id: UUID
                         ) -> Any | None: ...

    def ev_scenario(self, scenario_id: str, version: int) -> EvScenarioDefinition | None: ...


class StoreEvInputs:
    """`EvInputs` over the Foundation store and scenario repository `create_app` is composed with."""

    def __init__(self, foundation_store: Any | None, scenario_repository: Any) -> None:
        self._foundation = foundation_store
        self._scenarios = ScenarioCatalogService(scenario_repository)

    def foundation_revision(self, tenant_id: UUID, site_record_id: UUID, revision_id: UUID) -> Any | None:
        if self._foundation is None:
            return None
        for revision in self._foundation.revisions(tenant_id, site_record_id):
            if revision.id == revision_id:
                return revision
        return None

    def binding_revision(self, tenant_id: UUID, site_record_id: UUID, binding_set_revision_id: UUID
                         ) -> Any | None:
        """The exact binding set revision by ID, historical and superseded rows included."""
        if self._foundation is None:
            return None
        for revision in self._foundation.binding_sets(tenant_id, site_record_id):
            if revision.id == binding_set_revision_id:
                return revision
        return None

    def ev_scenario(self, scenario_id: str, version: int) -> EvScenarioDefinition | None:
        try:
            definition = self._scenarios.get_scenario(scenario_id)
        except ScenarioNotFound:
            return None
        if not isinstance(definition, EvScenarioDefinition) or definition.version != version:
            return None
        return definition


def is_ev_projection(projection: LabProjection) -> bool:
    return (projection.model_profile_id, projection.model_profile_version) == EV_MODEL_PROFILE


def ev_delay_event_id(report_key: str) -> str:
    """q4 Q25: a held EV report's stable private delay event ID, derived from its report key."""
    return "ev-delay-" + hashlib.sha256(report_key.encode("utf-8")).hexdigest()


def _boundaries(start: str, end: str) -> int:
    first = datetime.strptime(start, _INSTANT)
    last = datetime.strptime(end, _INSTANT)
    return int((last - first) / timedelta(minutes=1)) + 1


def _base(run: SimulationRun, *, status: str, start: str, end: str, notes: tuple[str, ...]) -> dict[str, Any]:
    identity = run.deterministic_identity
    profiles = identity.profiles
    return dict(
        run_id=run.run_id,
        status=status,
        statement=LAB_EXECUTION_STATUS_STATEMENTS[status],
        boundaries_total=_boundaries(start, end),
        interval_start_time=start,
        interval_end_time=end,
        timestep_minutes=1,
        seed=identity.seed,
        kernel_version=KERNEL_VERSION,
        model_profile_id=profiles.model_profile_id,
        model_profile_version=profiles.model_profile_version,
        publication_profile_id=profiles.publication_profile_id,
        publication_profile_version=profiles.publication_profile_version,
        numeric_policy=NUMERIC_POLICY,
        numeric_policy_version=NUMERIC_POLICY_VERSION,
        execution_contract_version=EXECUTION_CONTRACT_VERSION,
        inputs_identity=run_identity_sha256(run),
        private_state=(),
        observations=(),
        signals=(),
        reporting_gaps=(),
        recent_reports=(),
        suppressed_by_gap_count=0,
        dropped_count=0,
        notes=notes,
    )


def ev_draft_projection(run: SimulationRun, status: str = "NOT_STARTED", extra_notes: tuple[str, ...] = ()
                        ) -> LabProjection:
    """The Draft (or INTERRUPTED/ARTIFACT_UNREADABLE) EV projection: frozen identities and timing, nothing run."""
    interval = run.deterministic_identity.interval
    fields = _base(run, status=status, start=interval.start_time, end=interval.end_time,
                   notes=EV_NOTES + extra_notes)
    return LabProjection(
        boundaries_completed=0, offset_minutes=0, simulation_time=interval.start_time, content_digest=None,
        observation_series_digest=EMPTY_EV_SERIES_DIGEST, reported_count=0, **fields,
    )


def ev_terminal_projection(
    run: SimulationRun,
    definition: EvScenarioDefinition,
    *,
    content_digest: str,
    series_digest: str,
    reported_count: int,
    failure: ExecutionFailure | None = None,
) -> LabProjection:
    """The complete-window EV projection: COMPLETED, or FAILED with `PUBLICATION_REFUSED`."""
    status = "COMPLETED" if failure is None else "FAILED"
    fields = _base(run, status=status, start=definition.start, end=definition.end, notes=EV_NOTES)
    total = fields["boundaries_total"]
    return LabProjection(
        boundaries_completed=total, offset_minutes=total - 1, simulation_time=definition.end,
        content_digest=content_digest, observation_series_digest=series_digest, reported_count=reported_count,
        failure=failure, **fields,
    )


# --- The schema-7 EV artifact (q4 Q20) ---------------------------------------------------------------------

EV_ARTIFACT_KEYS = (
    "artifact_schema_version", "execution_kind", "run_id", "run_identity_sha256",
    "scenario_sha256", "observation_sha256", "foundation_revision_id",
    "foundation_content_sha256", "binding_set_revision_id", "snapshot_sha256",
    "status", "boundaries_completed", "boundaries_total", "offset_minutes",
    "simulation_time", "interval_start_time", "interval_end_time", "timestep_minutes",
    "seed", "kernel_version", "model_profile_id", "model_profile_version",
    "publication_profile_id", "publication_profile_version", "numeric_policy",
    "numeric_policy_version", "execution_contract_version", "content_digest",
    "observation_series_digest", "reported_count", "notes", "failure", "public_reports",
)


class EvArtifactUnreadable(ValueError):
    """A schema-7 EV artifact this build cannot verify."""


@dataclass(frozen=True)
class EvArtifact:
    """A parsed schema-7 artifact: the terminal projection, the frozen IDs/SHAs it copied and its public series."""

    projection: LabProjection
    scenario_sha256: str
    observation_sha256: str
    foundation_revision_id: str
    foundation_content_sha256: str
    binding_set_revision_id: str
    snapshot_sha256: str
    #: `(report_key, report_text)` in `ev_reports` series order, held reports included.
    public_reports: tuple[tuple[str, str], ...]


def render_ev_artifact(projection: LabProjection, run: SimulationRun,
                       public_reports: tuple[tuple[str, str], ...]) -> dict[str, object]:
    """A terminal EV projection as its schema-7 artifact mapping, frozen IDs/SHAs copied from the run."""
    if not projection.is_terminal or not is_ev_projection(projection):
        raise ValueError("only a terminal EV projection is written as an EV artifact")
    basis = run.registered_basis
    identity = run.deterministic_identity
    failure = projection.failure
    return {
        "artifact_schema_version": EV_ARTIFACT_SCHEMA_VERSION,
        "execution_kind": EV_EXECUTION_KIND,
        "run_id": projection.run_id,
        "run_identity_sha256": projection.inputs_identity,
        "scenario_sha256": identity.scenario.scenario_sha256,
        "observation_sha256": identity.profiles.observation_sha256,
        "foundation_revision_id": basis.foundation_revision_id,
        "foundation_content_sha256": basis.foundation_content_sha256,
        "binding_set_revision_id": basis.binding_set_revision_id,
        "snapshot_sha256": basis.snapshot_sha256,
        "status": projection.status,
        "boundaries_completed": projection.boundaries_completed,
        "boundaries_total": projection.boundaries_total,
        "offset_minutes": projection.offset_minutes,
        "simulation_time": projection.simulation_time,
        "interval_start_time": projection.interval_start_time,
        "interval_end_time": projection.interval_end_time,
        "timestep_minutes": projection.timestep_minutes,
        "seed": projection.seed,
        "kernel_version": projection.kernel_version,
        "model_profile_id": projection.model_profile_id,
        "model_profile_version": projection.model_profile_version,
        "publication_profile_id": projection.publication_profile_id,
        "publication_profile_version": projection.publication_profile_version,
        "numeric_policy": projection.numeric_policy,
        "numeric_policy_version": projection.numeric_policy_version,
        "execution_contract_version": projection.execution_contract_version,
        "content_digest": projection.content_digest,
        "observation_series_digest": projection.observation_series_digest,
        "reported_count": projection.reported_count,
        "notes": list(projection.notes),
        "failure": None if failure is None else {
            "kind": failure.kind, "subject": failure.subject, "statement": failure.statement,
            "at_offset_minutes": failure.at_offset_minutes, "detail": list(failure.detail),
        },
        "public_reports": [{"report_key": key, "report_text": text} for key, text in public_reports],
    }


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise EvArtifactUnreadable(reason)


def parse_ev_artifact(document: dict) -> EvArtifact:
    """Strictly read a schema-7 EV artifact: exact keys, terminal EV pair, 61/60/end projection facts, frozen
    ID/SHA syntax, and an ordered unique public series whose count and digest reproduce."""
    _require(isinstance(document, dict) and tuple(document) == EV_ARTIFACT_KEYS, "the EV artifact keys are not exact")
    _require(type(document["artifact_schema_version"]) is int
             and document["artifact_schema_version"] == EV_ARTIFACT_SCHEMA_VERSION
             and document["execution_kind"] == EV_EXECUTION_KIND, "not a schema-7 EV artifact")
    for key in ("run_identity_sha256", "scenario_sha256", "observation_sha256", "foundation_content_sha256",
                "snapshot_sha256", "content_digest", "observation_series_digest"):
        _require(isinstance(document[key], str) and bool(_SHA.fullmatch(document[key])), f"{key} is not a SHA-256")
    for key in ("foundation_revision_id", "binding_set_revision_id"):
        _require(isinstance(document[key], str) and bool(_UUID.fullmatch(document[key])), f"{key} is not a UUID")
    for key in ("boundaries_completed", "boundaries_total", "offset_minutes", "timestep_minutes", "seed",
                "kernel_version", "model_profile_version", "publication_profile_version", "numeric_policy_version",
                "execution_contract_version", "reported_count"):
        _require(type(document[key]) is int, f"{key} is not an integer")
    for key in ("run_id", "status", "simulation_time", "interval_start_time", "interval_end_time",
                "model_profile_id", "publication_profile_id", "numeric_policy"):
        _require(isinstance(document[key], str), f"{key} is not a string")
    _require(document["status"] in ("COMPLETED", "FAILED"), "an EV artifact is terminal")
    _require((document["model_profile_id"], document["model_profile_version"]) == EV_MODEL_PROFILE
             and (document["publication_profile_id"], document["publication_profile_version"])
             == EV_PUBLICATION_PROFILE, "an EV artifact names the ev-charger/1 + ev-publication/1 pair")
    try:
        total = _boundaries(document["interval_start_time"], document["interval_end_time"])
    except ValueError as error:
        raise EvArtifactUnreadable(f"the EV interval is not UTC instants: {error}") from error
    _require(document["timestep_minutes"] == 1 and document["boundaries_total"] == total == 61
             and document["boundaries_completed"] == 61 and document["offset_minutes"] == 60
             and document["simulation_time"] == document["interval_end_time"],
             "an EV artifact is the complete 61-boundary, 60-minute window ending at its interval end")
    notes = document["notes"]
    _require(isinstance(notes, list) and all(isinstance(n, str) for n in notes), "notes are not strings")
    raw = document["failure"]
    _require((raw is None) == (document["status"] == "COMPLETED"), "failure must match status")
    failure = None
    if raw is not None:
        _require(isinstance(raw, dict) and set(raw) == {"kind", "subject", "statement", "at_offset_minutes",
                                                         "detail"}, "the failure keys are not exact")
        _require(raw["kind"] == "PUBLICATION_REFUSED", "an EV failure is a publication refusal")
        _require(isinstance(raw["detail"], list) and all(isinstance(d, str) for d in raw["detail"]),
                 "failure detail is not strings")
        try:
            failure = ExecutionFailure(kind=raw["kind"], subject=raw["subject"], statement=raw["statement"],
                                       at_offset_minutes=raw["at_offset_minutes"], detail=tuple(raw["detail"]))
        except (TypeError, ValueError) as error:
            raise EvArtifactUnreadable(str(error)) from error
    reports = document["public_reports"]
    _require(isinstance(reports, list), "public_reports is not a list")
    series: list[tuple[str, str]] = []
    for item in reports:
        _require(isinstance(item, dict) and tuple(item) == ("report_key", "report_text")
                 and isinstance(item["report_key"], str) and isinstance(item["report_text"], str),
                 "a public report is not exactly {report_key, report_text}")
        try:
            parsed = parse_device_report_v2_text(item["report_text"])
        except (TypeError, ValueError) as error:
            raise EvArtifactUnreadable(f"a public report text is not a DeviceReport v2: {error}") from error
        _require(parsed.report_key == item["report_key"], "a public report key does not match its text")
        series.append((item["report_key"], item["report_text"]))
    _require(len({key for key, _ in series}) == len(series), "the public report keys are not unique")
    _require(len(series) == document["reported_count"], "the public report count is not reported_count")
    _require(ev_series_digest_of_texts(text for _, text in series) == document["observation_series_digest"],
             "the public reports do not reproduce observation_series_digest")
    try:
        projection = LabProjection(
            run_id=document["run_id"], status=document["status"],
            statement=LAB_EXECUTION_STATUS_STATEMENTS[document["status"]],
            boundaries_completed=document["boundaries_completed"], boundaries_total=document["boundaries_total"],
            offset_minutes=document["offset_minutes"], simulation_time=document["simulation_time"],
            interval_start_time=document["interval_start_time"], interval_end_time=document["interval_end_time"],
            timestep_minutes=document["timestep_minutes"], seed=document["seed"],
            kernel_version=document["kernel_version"], model_profile_id=document["model_profile_id"],
            model_profile_version=document["model_profile_version"],
            publication_profile_id=document["publication_profile_id"],
            publication_profile_version=document["publication_profile_version"],
            numeric_policy=document["numeric_policy"], numeric_policy_version=document["numeric_policy_version"],
            execution_contract_version=document["execution_contract_version"],
            inputs_identity=document["run_identity_sha256"], content_digest=document["content_digest"],
            observation_series_digest=document["observation_series_digest"], private_state=(), observations=(),
            signals=(), reporting_gaps=(), recent_reports=(), reported_count=document["reported_count"],
            suppressed_by_gap_count=0, dropped_count=0, failure=failure, notes=tuple(notes),
        )
    except (TypeError, ValueError) as error:
        raise EvArtifactUnreadable(str(error)) from error
    return EvArtifact(
        projection=projection, scenario_sha256=document["scenario_sha256"],
        observation_sha256=document["observation_sha256"],
        foundation_revision_id=document["foundation_revision_id"],
        foundation_content_sha256=document["foundation_content_sha256"],
        binding_set_revision_id=document["binding_set_revision_id"], snapshot_sha256=document["snapshot_sha256"],
        public_reports=tuple(series),
    )


def verify_ev_artifact(artifact: EvArtifact, run: SimulationRun) -> None:
    """The artifact's copied identity against the persisted run, which stays the authority (corruption check)."""
    basis = run.registered_basis
    identity = run.deterministic_identity
    projection = artifact.projection
    _require(basis is not None, "an EV run is registered")
    _require(projection.run_id == run.run_id, f"the EV artifact names run {projection.run_id}")
    _require(projection.inputs_identity == run_identity_sha256(run), "the EV artifact's run identity has changed")
    _require((artifact.scenario_sha256, artifact.observation_sha256)
             == (identity.scenario.scenario_sha256, identity.profiles.observation_sha256),
             "the EV artifact's scenario or observation SHA is not the run's")
    _require((artifact.foundation_revision_id, artifact.foundation_content_sha256, artifact.binding_set_revision_id,
              artifact.snapshot_sha256)
             == (basis.foundation_revision_id, basis.foundation_content_sha256, basis.binding_set_revision_id,
                 basis.snapshot_sha256), "the EV artifact's frozen revision IDs or SHAs are not the run's")
    _require((projection.interval_start_time, projection.interval_end_time, projection.seed)
             == (identity.interval.start_time, identity.interval.end_time, identity.seed),
             "the EV artifact's window or seed is not the run's")


__all__ = [
    "EMPTY_EV_SERIES_DIGEST", "EV_ARTIFACT_KEYS", "EV_ARTIFACT_SCHEMA_VERSION", "EV_EXECUTION_KIND", "EV_NOTES",
    "EvArtifact", "EvArtifactUnreadable", "EvInputs", "StoreEvInputs", "ev_delay_event_id", "ev_draft_projection",
    "ev_terminal_projection", "is_ev_projection", "parse_ev_artifact", "render_ev_artifact", "verify_ev_artifact",
]
