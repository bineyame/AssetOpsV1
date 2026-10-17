"""W2-02: the cold Lab run's frozen-input port, projections and private artifact (`D-2026-10-17-w2-02-buildspec`).

A cold run has no `Execution`/`ModelSpec`. `HostLabExecution.start` re-reads the exact frozen Foundation
revision and cold scenario document through `ColdInputs`, verifies them, executes the whole inclusive
minute-boundary window once and stages the public v2 reports. This module holds what that needs and the
legacy path does not: the read-only input port, the Draft and terminal cold projections, and the schema-6
cold artifact (`execution_kind: COLD`), rendered and parsed strictly.
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
from assetops_backend.scenarios.cold_parsing import ColdScenarioDefinition
from assetops_backend.scenarios.ports import ScenarioNotFound
from assetops_backend.scenarios.service import ScenarioCatalogService
from assetops_contracts.execution_contract import (
    EXECUTION_CONTRACT_VERSION,
    NUMERIC_POLICY,
    NUMERIC_POLICY_VERSION,
)
from assetops_contracts.failures import ExecutionFailure
from assetops_contracts.lab_projection import LAB_EXECUTION_STATUS_STATEMENTS, LabProjection
from assetops_contracts.source_envelope import canonical_json
from assetops_simulator.kernel.model import KERNEL_VERSION

COLD_ARTIFACT_SCHEMA_VERSION = 6
COLD_EXECUTION_KIND = "COLD"
COLD_MODEL_PROFILE_ID = "cold-thermal"

#: The empty cold series: SHA-256 of canonical `[]`.
EMPTY_COLD_SERIES_DIGEST = hashlib.sha256(canonical_json([]).encode("utf-8")).hexdigest()

COLD_NOTES = (
    "Cold run: the minute records live in the run's private execution artifact and its public reports in "
    "the gateway Stage. The empty legacy views make no claim about the physical trajectory.",
)

_SHA = re.compile(r"[0-9a-f]{64}")
_INSTANT = "%Y-%m-%dT%H:%M:%SZ"


class ColdInputs(Protocol):
    """Read-only re-read of a cold run's frozen inputs. Either call answers None when the record is absent."""

    def foundation_revision(self, tenant_id: UUID, site_record_id: UUID, revision_id: UUID) -> Any | None: ...

    def cold_scenario(self, scenario_id: str, version: int) -> ColdScenarioDefinition | None: ...


class StoreColdInputs:
    """`ColdInputs` over the Foundation store and scenario repository `create_app` is composed with."""

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

    def cold_scenario(self, scenario_id: str, version: int) -> ColdScenarioDefinition | None:
        try:
            definition = self._scenarios.get_scenario(scenario_id)
        except ScenarioNotFound:
            return None
        if not isinstance(definition, ColdScenarioDefinition) or definition.version != version:
            return None
        return definition


def is_cold_projection(projection: LabProjection) -> bool:
    return projection.model_profile_id == COLD_MODEL_PROFILE_ID


def _boundaries(start: str, end: str, timestep: int) -> int:
    first = datetime.strptime(start, _INSTANT)
    last = datetime.strptime(end, _INSTANT)
    return int((last - first) / timedelta(minutes=timestep)) + 1


def _base(run: SimulationRun, *, status: str, start: str, end: str) -> dict[str, Any]:
    identity = run.deterministic_identity
    profiles = identity.profiles
    return dict(
        run_id=run.run_id,
        status=status,
        statement=LAB_EXECUTION_STATUS_STATEMENTS[status],
        boundaries_total=_boundaries(start, end, 1),
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
        notes=COLD_NOTES,
    )


def cold_draft_projection(run: SimulationRun, status: str = "NOT_STARTED", extra_notes: tuple[str, ...] = ()
                          ) -> LabProjection:
    """The Draft (or INTERRUPTED/ARTIFACT_UNREADABLE) cold projection: frozen identities and timing, nothing run."""
    interval = run.deterministic_identity.interval
    fields = _base(run, status=status, start=interval.start_time, end=interval.end_time)
    fields["notes"] = fields["notes"] + extra_notes
    return LabProjection(
        boundaries_completed=0, offset_minutes=0, simulation_time=interval.start_time, content_digest=None,
        observation_series_digest=EMPTY_COLD_SERIES_DIGEST, reported_count=0, **fields,
    )


def cold_terminal_projection(
    run: SimulationRun,
    definition: ColdScenarioDefinition,
    *,
    content_digest: str,
    series_digest: str,
    reported_count: int,
    failure: ExecutionFailure | None = None,
) -> LabProjection:
    """The complete-window cold projection: COMPLETED, or FAILED with `PUBLICATION_REFUSED`."""
    status = "COMPLETED" if failure is None else "FAILED"
    fields = _base(run, status=status, start=definition.start, end=definition.end)
    total = fields["boundaries_total"]
    return LabProjection(
        boundaries_completed=total, offset_minutes=total - 1, simulation_time=definition.end,
        content_digest=content_digest, observation_series_digest=series_digest, reported_count=reported_count,
        failure=failure, **fields,
    )


# --- The schema-6 cold artifact ------------------------------------------------------------------------------

_COLD_KEYS = (
    "artifact_schema_version", "execution_kind", "run_id", "run_identity_sha256", "scenario_sha256",
    "observation_sha256", "status", "boundaries_completed", "boundaries_total", "offset_minutes",
    "simulation_time", "interval_start_time", "interval_end_time", "timestep_minutes", "seed", "kernel_version",
    "model_profile_id", "model_profile_version", "publication_profile_id", "publication_profile_version",
    "numeric_policy", "numeric_policy_version", "execution_contract_version", "content_digest",
    "observation_series_digest", "reported_count", "notes", "failure",
)


class ColdArtifactUnreadable(ValueError):
    """A schema-6 cold artifact this build cannot verify."""


def render_cold_projection(projection: LabProjection, *, scenario_sha256: str, observation_sha256: str
                           ) -> dict[str, object]:
    """A terminal cold projection as its schema-6 artifact mapping."""
    if not projection.is_terminal or not is_cold_projection(projection):
        raise ValueError("only a terminal cold projection is written as a cold artifact")
    failure = projection.failure
    return {
        "artifact_schema_version": COLD_ARTIFACT_SCHEMA_VERSION,
        "execution_kind": COLD_EXECUTION_KIND,
        "run_id": projection.run_id,
        "run_identity_sha256": projection.inputs_identity,
        "scenario_sha256": scenario_sha256,
        "observation_sha256": observation_sha256,
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
    }


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise ColdArtifactUnreadable(reason)


def parse_cold_projection(document: dict) -> LabProjection:
    """Strictly read a schema-6 cold artifact back into its terminal projection."""
    _require(isinstance(document, dict) and tuple(document) == _COLD_KEYS, "the cold artifact keys are not exact")
    _require(document["artifact_schema_version"] == COLD_ARTIFACT_SCHEMA_VERSION
             and document["execution_kind"] == COLD_EXECUTION_KIND, "not a schema-6 cold artifact")
    for key in ("run_identity_sha256", "scenario_sha256", "observation_sha256", "content_digest",
                "observation_series_digest"):
        _require(isinstance(document[key], str) and bool(_SHA.fullmatch(document[key])), f"{key} is not a SHA-256")
    for key in ("boundaries_completed", "boundaries_total", "offset_minutes", "timestep_minutes", "seed",
                "kernel_version", "model_profile_version", "publication_profile_version", "numeric_policy_version",
                "execution_contract_version", "reported_count"):
        _require(type(document[key]) is int, f"{key} is not an integer")
    for key in ("run_id", "status", "simulation_time", "interval_start_time", "interval_end_time",
                "model_profile_id", "publication_profile_id", "numeric_policy"):
        _require(isinstance(document[key], str), f"{key} is not a string")
    _require(document["status"] in ("COMPLETED", "FAILED"), "a cold artifact is terminal")
    _require(document["model_profile_id"] == COLD_MODEL_PROFILE_ID, "a cold artifact names the cold pack")
    _require(document["boundaries_completed"] == document["boundaries_total"], "a cold artifact is complete")
    notes = document["notes"]
    _require(isinstance(notes, list) and all(isinstance(n, str) for n in notes), "notes are not strings")
    raw = document["failure"]
    _require((raw is None) == (document["status"] == "COMPLETED"), "failure must match status")
    failure = None
    if raw is not None:
        _require(isinstance(raw, dict) and set(raw) == {"kind", "subject", "statement", "at_offset_minutes",
                                                         "detail"}, "the failure keys are not exact")
        _require(raw["kind"] == "PUBLICATION_REFUSED", "a cold failure is a publication refusal")
        _require(isinstance(raw["detail"], list) and all(isinstance(d, str) for d in raw["detail"]),
                 "failure detail is not strings")
        try:
            failure = ExecutionFailure(kind=raw["kind"], subject=raw["subject"], statement=raw["statement"],
                                       at_offset_minutes=raw["at_offset_minutes"], detail=tuple(raw["detail"]))
        except (TypeError, ValueError) as error:
            raise ColdArtifactUnreadable(str(error)) from error
    try:
        return LabProjection(
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
        raise ColdArtifactUnreadable(str(error)) from error


def delay_event_id(report_key: str) -> str:
    """A held report's stable delay event ID, derived from its report key."""
    return "cold-delay-" + hashlib.sha256(report_key.encode("utf-8")).hexdigest()



__all__ = [
    "COLD_ARTIFACT_SCHEMA_VERSION", "COLD_NOTES", "ColdArtifactUnreadable", "ColdInputs", "EMPTY_COLD_SERIES_DIGEST",
    "StoreColdInputs", "cold_draft_projection", "cold_terminal_projection", "delay_event_id",
    "is_cold_projection", "parse_cold_projection", "render_cold_projection",
]
