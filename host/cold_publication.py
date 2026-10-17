"""W2-02: a cold run's verified inputs and its public DeviceReport v2 series (`D-2026-10-17-w2-02-buildspec`).

The frozen run identity carries the Foundation revision ID and content SHA, the scenario SHA and the
observation SHA - never the thirteen property values or the document's rows. At execution the host re-reads
the exact revision and cold document, and `verify_cold_inputs` checks them against what the run froze before
anything is published: a missing, changed or mismatched input refuses (`FrozenRunNotReconstructible`), with no
current-revision or fixture-default substitution.

`cold_reports` then runs `ColdExecution` over the verified inputs, applies `cold-observation/1`
(`cold_observations`) and adapts each public observation to one v2 report. Only the public report adapter
crosses into product data; no private world state, run ID or cause is in a report.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from fractions import Fraction
from typing import Any, Mapping

from assetops_backend.runs.models import SimulationRun
from assetops_backend.scenarios.cold_parsing import ColdScenarioDefinition, observation_sha256
from assetops_backend.sites.foundation_content import content_digest
from assetops_contracts.source_envelope import canonical_json
from assetops_contracts.gateway_report import (
    DeviceReportV2,
    cold_event_id,
    cold_report_key,
    device_report_v2_text,
)
from assetops_simulator.kernel.execute import ColdExecution
from assetops_simulator.observation.transform import ColdObservation, cold_observations
from assetops_simulator.packs.cold import PROPERTY_FIELDS, ColdForcingRow, ColdPack, ColdParameters, run_window
from assetops_simulator.packs.errors import PhysicallyUnacceptable

from execution_adapter import FrozenRunNotReconstructible, execution_path

_INSTANT = "%Y-%m-%dT%H:%M:%SZ"


@dataclass(frozen=True)
class VerifiedColdInputs:
    parameters: ColdParameters
    definition: ColdScenarioDefinition


@dataclass(frozen=True)
class ColdReport:
    """One public v2 report, its retransmission key and the instant it is published at."""

    report_key: str
    report_text: str
    device_id: str
    signal_id: str
    source_time: str
    published_at: str
    held: bool


def _at(text: str) -> datetime:
    return datetime.strptime(text, _INSTANT).replace(tzinfo=timezone.utc)


def _text(moment: datetime | None) -> str | None:
    return None if moment is None else moment.strftime(_INSTANT)


def _properties(content: Mapping[str, Any]) -> dict[str, tuple[str, str]]:
    found: dict[str, tuple[str, str]] = {}
    for component in content.get("components") or ():
        for item in component.get("properties") or ():
            key = item.get("property_key")
            if key not in PROPERTY_FIELDS:
                continue
            if key in found:
                raise FrozenRunNotReconstructible(f"Foundation property {key} is stated twice")
            found[key] = (str(item.get("value")), str(item.get("unit")))
    return found


def verify_cold_inputs(
    run: SimulationRun, revision: Any, definition: ColdScenarioDefinition | None
) -> VerifiedColdInputs:
    """Check the re-read Foundation revision and cold document against the frozen run, then extract.

    `revision` is the exact stored revision the run froze (`id`, `content`, `content_sha256`), or None."""
    if execution_path(run) != "COLD":
        raise FrozenRunNotReconstructible("not a cold run")
    basis = run.registered_basis
    identity = run.deterministic_identity
    if basis is None:
        raise FrozenRunNotReconstructible("a cold run is registered")
    if revision is None or str(revision.id) != basis.foundation_revision_id:
        raise FrozenRunNotReconstructible(f"Foundation revision {basis.foundation_revision_id} is unavailable")
    if (revision.content_sha256 != basis.foundation_content_sha256
            or content_digest(revision.content) != basis.foundation_content_sha256):
        raise FrozenRunNotReconstructible("the Foundation revision content does not match the frozen SHA")
    if definition is None:
        raise FrozenRunNotReconstructible(f"cold scenario {identity.scenario.scenario_id} is unavailable")
    if (definition.scenario_id, definition.version) != (identity.scenario.scenario_id,
                                                        identity.scenario.scenario_version):
        raise FrozenRunNotReconstructible("the cold document is not the frozen scenario version")
    if identity.scenario.scenario_sha256 is None or definition.scenario_sha256 != identity.scenario.scenario_sha256:
        raise FrozenRunNotReconstructible("the cold document does not match the frozen scenario SHA")
    frozen_observation = identity.profiles.observation_sha256
    if frozen_observation is None or observation_sha256(definition) != frozen_observation:
        raise FrozenRunNotReconstructible("the cold observation rows do not match the frozen observation SHA")
    try:
        parameters = ColdParameters.from_properties(_properties(revision.content))
    except (PhysicallyUnacceptable, ValueError, ZeroDivisionError) as invalid:
        raise FrozenRunNotReconstructible(f"the frozen Foundation revision has no valid cold parameters: {invalid}")
    return VerifiedColdInputs(parameters=parameters, definition=definition)


def _observation_rows(definition: ColdScenarioDefinition) -> tuple:
    from types import SimpleNamespace

    return tuple(
        SimpleNamespace(at=_at(o.at), kind=o.kind, device_id=o.device_id, action=o.action, outcome=o.outcome,
                        release_at=None if o.release_at is None else _at(o.release_at))
        for o in definition.observations
    )


def cold_correlation_id(*, scenario_sha256: str, correlation_key: tuple[str, int]) -> str:
    """The outage/attempt or door-cycle correlation of a cold event: `cold:` + SHA-256 of canonical
    `(scenario_sha256, correlation kind, ordinal)` (open question: see the phase-3 handoff)."""
    kind, ordinal = correlation_key
    return "cold:" + hashlib.sha256(canonical_json([scenario_sha256, kind, ordinal]).encode("utf-8")).hexdigest()


def report_of(observation: ColdObservation, scenario_sha256: str) -> DeviceReportV2:
    """The public v2 report of one cold observation."""
    r = observation.record
    source_time = _text(r.source_time)
    if r.measurement is not None:
        interval_start = _text(r.interval_start)
        return DeviceReportV2(
            report_key=cold_report_key(scenario_sha256=scenario_sha256, device_id=r.device_id,
                                       signal_id=r.signal_id, source_time=source_time, record_kind=None,
                                       event_id=None, interval_start=interval_start),
            device_id=r.device_id, signal_id=r.signal_id, source_time=source_time, family="MEASUREMENT",
            measurement=r.measurement, interval_start=interval_start,
            interval_end=source_time if r.measurement == "INTERVAL_MEAN" else None,
            value=observation.value_text, unit=r.unit, quality=r.quality, unavailable_reason=r.unavailable_reason,
            record_kind=None, event_id=None, correlation_id=None, component_id=None, actor=None, outcome=None,
            session_id=None, connector_id=None,
        )
    event_id = cold_event_id(scenario_sha256=scenario_sha256, device_id=r.device_id, signal_id=r.signal_id,
                             transition_ordinal=observation.transition_ordinal)
    return DeviceReportV2(
        report_key=cold_report_key(scenario_sha256=scenario_sha256, device_id=r.device_id, signal_id=r.signal_id,
                                   source_time=source_time, record_kind=r.record_kind, event_id=event_id,
                                   interval_start=None),
        device_id=r.device_id, signal_id=r.signal_id, source_time=source_time, family="EVENT", measurement=None,
        interval_start=None, interval_end=None, value=None, unit=None, quality=r.quality, unavailable_reason=None,
        record_kind=r.record_kind, event_id=event_id,
        correlation_id=cold_correlation_id(scenario_sha256=scenario_sha256, correlation_key=r.correlation_key),
        component_id=r.component_id, actor=r.actor, outcome=r.outcome, session_id=None, connector_id=None,
    )


def cold_reports(verified: VerifiedColdInputs) -> tuple[ColdReport, ...]:
    """Execute the verified cold run and return its public v2 series in publication order."""
    d = verified.definition
    execution = ColdExecution(
        ColdPack(verified.parameters, backup_enabled=d.backup_enabled), runner=run_window,
        start=_at(d.start), end=_at(d.end),
        initial_temperature=Fraction(d.initial_temperature_deg_c), ambient=Fraction(d.ambient_deg_c),
        forcings=tuple(ColdForcingRow(at=_at(f.at), kind=f.kind, asset=f.asset, value=f.value) for f in d.forcings),
    )
    out: list[ColdReport] = []
    for observation in cold_observations(execution.records, _observation_rows(d)):
        report = report_of(observation, d.scenario_sha256)
        out.append(ColdReport(
            report_key=report.report_key, report_text=device_report_v2_text(report), device_id=report.device_id,
            signal_id=report.signal_id, source_time=report.source_time,
            published_at=_text(observation.published_at), held=observation.held,
        ))
    return tuple(out)
