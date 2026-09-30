"""Capture, persist and strictly read back one Lab execution's history (T025c).

The host owns this record for the reason it owns the execution artifact: it is
private simulator truth, and a product store of it would put a filing cabinet
inside the truth barrier. `assetops_contracts.lab_history` is what crosses the
port; this module is how the leaf produces it.

## One capture, from the execution that already ran

`capture` reads the live `Execution` handle - its boundaries, its ledger, its
control steps and the observation attempts the transform already generated -
and copies each recorded fact once. It computes no physical quantity. A
persisted history is that capture, serialized; a read of it parses and
verifies, and never touches a kernel.

## Where it lives on disk

In the same file as the projection, as a second document after
`HISTORY_MARKER`, so the pair is replaced atomically by one rename. The first
document is the projection exactly as every earlier build wrote it - byte for
byte, which is what lets the contract-9 gate keep comparing it - and the second
is canonical JSON (a YAML flow document) holding the history. JSON because a
demo-window history is tens of thousands of rows and `json` reads that in
milliseconds where a YAML loader takes seconds; a projection read splits at the
marker and never parses the history at all.

Only a terminal run's artifact carries a history. A RUNNING artifact is never
read back (it reads as INTERRUPTED), so writing a growing history into it at
every step would cost the square of the boundary count for nothing.

## Integrity

`history_digest` is a blake2b over the canonical JSON of the whole document
with the digest field itself removed: the manifest (run, frozen-input
identity, every version, window, timestep, seed, outcome, recorded extent,
trajectory and observation digests, coverage, and `projection_binding`) and
every record. `projection_binding` (schema 2) is a blake2b over the stored
projection's `signals`, `reporting_gaps` and whole `electrical` view, the
projection-owned data the cockpit draws; editing any of them after the write
makes the history unreadable even though the history text is unchanged. It is a
different digest from the trajectory's `content_digest`, which it carries
rather than replaces: a projected subset cannot claim to be the canonical
trajectory. A reader recomputes it, checks the manifest and `projection_binding`
against the projection it was stored with, and validates ordering, window membership, units, types
and declared coverage before returning anything.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import re
from fractions import Fraction

from assetops_contracts.control import (
    DISCRETE_UNIT,
    AcceptedControl,
    AcceptedFlow,
    AcceptedFlowSet,
    BalanceIdentity,
    ControlIntent,
    ControlRequest,
    ControllerView,
    ControlStep,
    EffectiveControl,
    LoadService,
    StockAccount,
    ViewEntry,
)
from assetops_contracts.failures import ExecutionFailure
from assetops_contracts.lab_history import (
    HISTORY_FAMILIES,
    HISTORY_FAMILY_STATEMENTS,
    LAB_HISTORY_SCHEMA_VERSION,
    LAB_HISTORY_SOURCES,
    SAMPLE_PHASES,
    FamilyCoverage,
    HistoryBoundary,
    HistoryInterval,
    HistorySample,
    LabHistory,
    unavailable_coverage,
)
from assetops_contracts.lab_projection import ElectricalView, LabProjection
from assetops_contracts.observation import (
    SAMPLE_OUTCOMES,
    DeviceObservation,
    FrozenReportingInputs,
)
from assetops_contracts.trajectory import (
    AppliedEvent,
    BoundedTransition,
    DiscreteTransition,
    ForcingExposure,
)
from assetops_contracts.world_inputs import BusAttachmentInput

#: The line that separates the projection document from the history document.
#: A YAML document-start marker with a comment, so the file stays one valid
#: YAML stream; the reader splits on it rather than parsing the whole stream.
HISTORY_MARKER = "--- # assetops-lab-history\n"

#: The digest's domain separator, so it cannot collide with any other digest
#: this product computes over similar bytes.
_DIGEST_DOMAIN = b"assetops-lab-history\x00"

_EXACT = re.compile(r"-?(0|[1-9][0-9]*)(/[1-9][0-9]*)?")
_MEMBER = re.compile(r"[A-Z][A-Z0-9_]*")


class HistoryUnreadable(Exception):
    """A persisted history this build cannot verify. Never overwritten."""


# --- Capture ------------------------------------------------------------------


def _state_key_of(address: str) -> str:
    if address.startswith("site:"):
        return address[len("site:") :]
    return address.split("@")[0]


def capture(
    execution,
    reporting: FrozenReportingInputs,
    observations: tuple[DeviceObservation, ...],
    *,
    run_id: str,
    status: str,
    content_digest: str | None,
    observation_series_digest: str | None,
    electrical: ElectricalView | None,
) -> LabHistory:
    """The history an execution has recorded so far, each fact once.

    `electrical` is the live projection's own electrical view: its step rows
    are joined as `electrical_steps` when intervals are recorded, never
    re-summed here (`electrical_view` owns the totals).
    """
    inputs = execution.inputs
    units: dict[str, str] = {}

    def unit_of(address: str) -> str:
        if address not in units:
            initial = inputs.initial_value(address)
            units[address] = "" if initial is None else initial.canonical_unit
        return units[address]

    boundaries: list[HistoryBoundary] = []
    samples: list[HistorySample] = []
    intervals: list[HistoryInterval] = []
    exposures: list[ForcingExposure] = []
    seen_exposures: set[ForcingExposure] = set()
    for boundary in execution.boundaries:
        offset = boundary.offset_minutes
        boundaries.append(
            HistoryBoundary(
                step_index=boundary.step_index,
                offset_minutes=offset,
                simulation_time=boundary.simulation_time,
                has_preceding_interval=boundary.has_preceding_interval,
            )
        )
        for address, value in boundary.stocks:
            samples.append(
                HistorySample(
                    offset, address, _state_key_of(address), "POST_EVENT",
                    unit_of(address), value,
                )
            )
        for address, value in boundary.discrete:
            samples.append(
                HistorySample(
                    offset, address, _state_key_of(address), "POST_EVENT",
                    DISCRETE_UNIT, value,
                )
            )
        for address, value in boundary.discrete_for_step:
            samples.append(
                HistorySample(
                    offset, address, _state_key_of(address), "FOR_STEP",
                    DISCRETE_UNIT, value,
                )
            )
        for address, value in boundary.interval_measurements:
            samples.append(
                HistorySample(
                    offset, address, _state_key_of(address),
                    "PRECEDING_INTERVAL", "", value,
                )
            )
        for exposure in boundary.forcing_exposures:
            if exposure not in seen_exposures:
                seen_exposures.add(exposure)
                exposures.append(exposure)
        if boundary.control_step is not None:
            accepted = boundary.control_step.accepted
            intervals.append(
                HistoryInterval(
                    from_offset=accepted.from_offset,
                    to_offset=accepted.to_offset,
                    step=boundary.control_step,
                )
            )

    has_controller = getattr(execution.model, "coupling", None) is not None
    attachments = tuple(inputs.bus_attachments)
    coverage = (
        _recorded("state_samples"),
        _recorded("intervals")
        if has_controller
        else FamilyCoverage(
            "intervals",
            "NOT_APPLICABLE",
            "This model has no controller or resolver, so it resolves no "
            "interval; its interval measurements are state samples.",
        ),
        _recorded("observation_attempts"),
        _recorded("timeline"),
        _recorded("drawing")
        if attachments
        else FamilyCoverage(
            "drawing",
            "NOT_APPLICABLE",
            "This run froze no bus attachments, so there is no run-bound "
            "electrical topology to draw.",
        ),
    )
    return LabHistory(
        run_id=run_id,
        status=status,
        source="LIVE_SESSION",
        statement=LAB_HISTORY_SOURCES["LIVE_SESSION"],
        history_schema_version=LAB_HISTORY_SCHEMA_VERSION,
        boundaries_total=execution.boundaries_total,
        inputs_identity=execution.inputs_identity,
        content_digest=content_digest,
        observation_series_digest=observation_series_digest,
        history_digest=None,
        coverage=coverage,
        failure=execution.failure,
        boundaries=tuple(boundaries),
        samples=tuple(samples),
        intervals=tuple(intervals),
        exposures=tuple(exposures),
        attempts=tuple(observations),
        signals=reporting.signals,
        reporting_gaps=reporting.gaps,
        applied_events=execution.applied_events,
        bounded_transitions=execution.bounded_transitions,
        discrete_transitions=execution.discrete_transitions,
        bus_attachments=attachments,
        electrical_steps=_joined_steps(coverage, electrical),
    )


def _joined_steps(
    coverage: tuple[FamilyCoverage, ...], electrical: ElectricalView | None
) -> tuple:
    """The projection's electrical step rows, only where intervals are recorded."""
    recorded = any(
        entry.family == "intervals" and entry.availability == "RECORDED"
        for entry in coverage
    )
    if not recorded or electrical is None:
        return ()
    return electrical.steps


def _recorded(family: str) -> FamilyCoverage:
    return FamilyCoverage(family, "RECORDED", HISTORY_FAMILY_STATEMENTS[family])


def without_history(
    projection: LabProjection, source: str, reason: str | None = None
) -> LabHistory:
    """A history that states why there is none, and carries no record."""
    statement = LAB_HISTORY_SOURCES[source]
    return LabHistory(
        run_id=projection.run_id,
        status=projection.status,
        source=source,
        statement=statement,
        history_schema_version=None,
        boundaries_total=projection.boundaries_total,
        inputs_identity=projection.inputs_identity,
        content_digest=projection.content_digest,
        observation_series_digest=projection.observation_series_digest,
        history_digest=None,
        coverage=unavailable_coverage(reason or statement),
        failure=projection.failure,
        signals=projection.signals,
        reporting_gaps=projection.reporting_gaps,
        notes=() if reason is None else (reason,),
    )


# --- Serialization --------------------------------------------------------------


def _q(value: Fraction) -> str:
    return str(value)


def _typed(value: Fraction | str | None) -> str | None:
    return None if value is None else str(value)


def _plain(value: object):
    """A projection value as canonical JSON data: ratios exact, tuples lists."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {f.name: _plain(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    if isinstance(value, Fraction):
        return str(value)
    return value


def projection_binding(projection: LabProjection) -> str:
    """A digest of the projection-owned data the cockpit reads beside history.

    The reader takes the signal catalogue and reporting gaps, and the chart's
    PV and battery values (the electrical steps), from the projection rather
    than from the appended history. The history digest cannot cover a document
    it does not contain, so the manifest carries this digest of those fields
    and the reader recomputes it from the projection it loaded: editing the
    projection alone no longer leaves a verified-looking history.
    """
    body = _canonical(
        {
            "signals": _plain(projection.signals),
            "reporting_gaps": _plain(projection.reporting_gaps),
            "electrical": _plain(projection.electrical),
        }
    )
    return hashlib.blake2b(
        b"assetops-lab-history-projection\x00" + body, digest_size=32
    ).hexdigest()


def _manifest(history: LabHistory, projection: LabProjection) -> dict:
    failure = history.failure
    return {
        "projection_binding": projection_binding(projection),
        "run_id": projection.run_id,
        "status": projection.status,
        "inputs_identity": projection.inputs_identity,
        "kernel_version": projection.kernel_version,
        "model_profile_id": projection.model_profile_id,
        "model_profile_version": projection.model_profile_version,
        "publication_profile_id": projection.publication_profile_id,
        "publication_profile_version": projection.publication_profile_version,
        "numeric_policy": projection.numeric_policy,
        "numeric_policy_version": projection.numeric_policy_version,
        "execution_contract_version": projection.execution_contract_version,
        "interval_start_time": projection.interval_start_time,
        "interval_end_time": projection.interval_end_time,
        "timestep_minutes": projection.timestep_minutes,
        "seed": projection.seed,
        "boundaries_total": projection.boundaries_total,
        "boundaries_recorded": len(history.boundaries),
        "recorded_through_offset_minutes": history.recorded_through_offset,
        "content_digest": projection.content_digest,
        "observation_series_digest": projection.observation_series_digest,
        "failure": None
        if failure is None
        else {
            "kind": failure.kind,
            "subject": failure.subject,
            "statement": failure.statement,
            "at_offset_minutes": failure.at_offset_minutes,
            "detail": list(failure.detail),
        },
        "coverage": [
            [entry.family, entry.availability, entry.statement]
            for entry in history.coverage
        ],
    }


def _interval_row(interval: HistoryInterval) -> dict:
    step = interval.step
    view, intent, accepted = step.view, step.intent, step.accepted
    return {
        "view": [
            view.at_offset_minutes,
            view.for_until_offset,
            [[e.name, e.address, _typed(e.value), e.unit] for e in view.entries],
        ],
        "intent": [
            intent.from_offset,
            intent.to_offset,
            [
                [r.address, r.quantity, _typed(r.requested), r.unit, r.reason]
                for r in intent.requests
            ],
        ],
        "accepted": {
            "from": accepted.from_offset,
            "to": accepted.to_offset,
            "segments": [list(s) for s in accepted.segments],
            "flows": [
                [f.flow_id, f.from_address, f.to_address, _q(f.energy), _q(f.mean_power)]
                for f in accepted.flows
            ],
            "controls": [
                [
                    c.address, c.quantity, _typed(c.requested), _typed(c.accepted),
                    c.unit, list(c.limited_by),
                ]
                for c in accepted.controls
            ],
            "loads": [
                [
                    l.address, l.priority_rank, _q(l.demand_energy),
                    _q(l.served_energy), _q(l.unserved_energy), _q(l.demand_power),
                    _q(l.served_power), _q(l.unserved_power),
                ]
                for l in accepted.loads
            ],
            "effective": [
                [
                    e.address, e.from_offset, e.to_offset, _q(e.value), e.unit,
                    e.origin, e.provenance,
                ]
                for e in accepted.effective_controls
            ],
            "balances": [
                [b.identity_id, list(b.sources), list(b.sinks)]
                for b in accepted.balances
            ],
            "stock_accounts": [
                [
                    s.address, _q(s.delta), _q(s.energy_per_unit),
                    list(s.inflows), list(s.outflows),
                ]
                for s in accepted.stock_accounts
            ],
            "interval_energies": [[k, _q(v)] for k, v in accepted.interval_energies],
            "notes": list(accepted.notes),
        },
    }


def render_history(history: LabHistory, projection: LabProjection) -> dict:
    """The persisted history document, digest included."""
    document = {
        "history_schema_version": LAB_HISTORY_SCHEMA_VERSION,
        "manifest": _manifest(history, projection),
        "boundaries": [
            [b.step_index, b.offset_minutes, b.simulation_time, b.has_preceding_interval]
            for b in history.boundaries
        ],
        "samples": [
            [s.offset_minutes, s.address, s.phase, s.unit, _typed(s.value)]
            for s in history.samples
        ],
        "intervals": [_interval_row(i) for i in history.intervals],
        "exposures": [
            [x.address, x.event_id, x.parameter_id, _q(x.value), x.from_offset, x.to_offset]
            for x in history.exposures
        ],
        "attempts": [
            [
                o.at_offset_minutes, o.address, o.device_id, o.signal_id,
                o.state_key, o.reading_class, o.source_sample_time, o.outcome,
                _typed(o.reported_value), o.canonical_unit, o.suppression_reason,
            ]
            for o in history.attempts
        ],
        "applied_events": [
            [
                e.event_id, e.address, e.direction, e.at_offset_minutes,
                _q(e.share), _q(e.declared), e.origin, e.phase_id,
            ]
            for e in history.applied_events
        ],
        "bounded_transitions": [
            [
                t.address, t.at_offset_minutes, t.bound_case_id, t.bound_kind,
                _q(t.bound_value), _q(t.requested), _q(t.accepted), _q(t.refused),
                list(t.event_ids),
            ]
            for t in history.bounded_transitions
        ],
        "discrete_transitions": [
            [
                t.address, t.state_key, t.previous, t.next, t.phase, t.cause,
                t.controller_ref, t.at_offset_minutes, t.simulation_time,
            ]
            for t in history.discrete_transitions
        ],
        "bus_attachments": [
            [a.role, a.component_id, a.via_component_id, a.bus_component_id]
            for a in history.bus_attachments
        ],
    }
    document["manifest"]["history_digest"] = history_digest(document)
    return document


def write_failed_document(projection: LabProjection, reason: str) -> dict:
    """What is written in place of a history that could not be built."""
    return {
        "history_schema_version": LAB_HISTORY_SCHEMA_VERSION,
        "write_failed": {"run_id": projection.run_id, "reason": reason},
    }


def _canonical(document: dict) -> bytes:
    return json.dumps(
        document, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def history_digest(document: dict) -> str:
    """The integrity digest of a history document, excluding its own field."""
    manifest = dict(document["manifest"])
    manifest.pop("history_digest", None)
    body = _canonical({**document, "manifest": manifest})
    return hashlib.blake2b(_DIGEST_DOMAIN + body, digest_size=32).hexdigest()


def history_text(document: dict) -> str:
    return HISTORY_MARKER + _canonical(document).decode("utf-8") + "\n"


# --- Strict read -----------------------------------------------------------------


def _fail(message: str) -> HistoryUnreadable:
    return HistoryUnreadable(message)


def _int(value: object, where: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise _fail(f"{where} is {value!r}; a whole number was written there.")
    return value


def _str(value: object, where: str, *, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    if not isinstance(value, str):
        raise _fail(f"{where} is {value!r}; text was written there.")
    return value


def _exact(value: object, where: str) -> Fraction:
    if not isinstance(value, str) or not _EXACT.fullmatch(value):
        raise _fail(f"{where} is {value!r}; an exact ratio was written there.")
    parsed = Fraction(value)
    if str(parsed) != value:
        raise _fail(f"{where} is {value!r}, which is not in lowest terms.")
    return parsed


def _value(value: object, unit: str, where: str, *, optional: bool = False):
    if value is None and optional:
        return None
    if unit == DISCRETE_UNIT:
        if not isinstance(value, str) or not _MEMBER.fullmatch(value):
            raise _fail(f"{where} is {value!r}; a discrete member was written there.")
        return value
    return _exact(value, where)


def _rows(document: dict, key: str, width: int) -> list[list]:
    rows = document.get(key)
    if not isinstance(rows, list):
        raise _fail(f"The history has no {key!r} list.")
    for index, row in enumerate(rows):
        if not isinstance(row, list) or len(row) != width:
            raise _fail(f"{key}[{index}] is not a row of {width} fields.")
    return rows


def _strs(value: object, where: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise _fail(f"{where} is not a list.")
    return tuple(_str(item, where) for item in value)


def _check_order(offsets: list[int], family: str) -> None:
    if any(later < earlier for earlier, later in zip(offsets, offsets[1:])):
        raise _fail(f"The {family} records are out of time order.")


_MANIFEST_FROM_PROJECTION = (
    "run_id",
    "status",
    "inputs_identity",
    "kernel_version",
    "model_profile_id",
    "model_profile_version",
    "publication_profile_id",
    "publication_profile_version",
    "numeric_policy",
    "numeric_policy_version",
    "execution_contract_version",
    "interval_start_time",
    "interval_end_time",
    "timestep_minutes",
    "seed",
    "boundaries_total",
    "content_digest",
    "observation_series_digest",
)


def parse_history(document: object, projection: LabProjection) -> LabHistory:
    """Read one persisted history strictly, against the projection beside it.

    Raises `HistoryUnreadable` for an unknown schema, a digest that does not
    match, a manifest that disagrees with the projection, or any record out of
    order, outside the window, or of the wrong type. A write-failure document
    is returned as the stated WRITE_FAILED history rather than raised.
    """
    if not isinstance(document, dict):
        raise _fail("The history is not a document.")
    schema = document.get("history_schema_version")
    if schema != LAB_HISTORY_SCHEMA_VERSION:
        raise _fail(
            f"The history is schema {schema!r} and this build reads schema "
            f"{LAB_HISTORY_SCHEMA_VERSION}."
        )
    if "write_failed" in document:
        failed = document["write_failed"]
        if not isinstance(failed, dict) or failed.get("run_id") != projection.run_id:
            raise _fail("The history write-failure record names another run.")
        reason = _str(failed.get("reason"), "write_failed.reason")
        return without_history(projection, "WRITE_FAILED", reason)

    manifest = document.get("manifest")
    if not isinstance(manifest, dict):
        raise _fail("The history has no manifest.")
    stored_digest = manifest.get("history_digest")
    if stored_digest != history_digest(document):
        raise _fail(
            "The history's integrity digest does not match its content; it was "
            "changed or damaged after it was written."
        )
    for key in _MANIFEST_FROM_PROJECTION:
        if manifest.get(key) != getattr(projection, key):
            raise _fail(
                f"The history's manifest says {key} is {manifest.get(key)!r} and "
                f"the execution record beside it says {getattr(projection, key)!r}."
            )
    if manifest.get("projection_binding") != projection_binding(projection):
        raise _fail(
            "The execution record beside the history no longer matches the "
            "signals, reporting gaps and electrical steps the history was "
            "written with; it was changed after the history was written."
        )
    try:
        return _parse_records(document, manifest, projection, stored_digest)
    except HistoryUnreadable:
        raise
    except (ValueError, TypeError, KeyError) as error:
        raise _fail(f"A history record is not valid: {error}") from error


def _parse_records(
    document: dict, manifest: dict, projection: LabProjection, digest: str
) -> LabHistory:
    timestep = projection.timestep_minutes
    last_offset = (projection.boundaries_total - 1) * timestep

    boundaries = []
    for index, row in enumerate(_rows(document, "boundaries", 4)):
        step_index = _int(row[0], f"boundaries[{index}] step")
        offset = _int(row[1], f"boundaries[{index}] offset")
        if step_index != index or offset != index * timestep:
            raise _fail(
                f"Boundary {index} is recorded at step {step_index}, offset "
                f"{offset}; the run's boundaries are one timestep apart from zero."
            )
        if not isinstance(row[3], bool) or row[3] != (index > 0):
            raise _fail(
                f"Boundary {index} says a preceding interval "
                f"{'did' if row[3] else 'did not'} end there."
            )
        boundaries.append(
            HistoryBoundary(step_index, offset, _str(row[2], "simulation_time"), row[3])
        )
    if manifest.get("boundaries_recorded") != len(boundaries):
        raise _fail("The manifest's recorded boundary count disagrees with the records.")
    if boundaries and offset > last_offset:
        raise _fail("A boundary is recorded beyond the run's window.")
    through = boundaries[-1].offset_minutes if boundaries else None
    if manifest.get("recorded_through_offset_minutes") != through:
        raise _fail("The manifest's recorded-through offset disagrees with the records.")
    if projection.status == "COMPLETED" and len(boundaries) != projection.boundaries_total:
        raise _fail("A COMPLETED history does not record every boundary of its window.")
    recorded = {b.offset_minutes for b in boundaries}

    def at_boundary(value: object, where: str) -> int:
        offset = _int(value, where)
        if offset not in recorded:
            raise _fail(f"{where} is offset {offset}, which is not a recorded boundary.")
        return offset

    def in_window(value: object, where: str) -> int:
        offset = _int(value, where)
        if offset < 0 or through is None or offset > through + timestep:
            raise _fail(f"{where} is offset {offset}, outside the recorded window.")
        return offset

    samples = []
    for index, row in enumerate(_rows(document, "samples", 5)):
        where = f"samples[{index}]"
        address = _str(row[1], where)
        phase = _str(row[2], where)
        unit = _str(row[3], where)
        if phase not in SAMPLE_PHASES:
            raise _fail(f"{where} has phase {phase!r}.")
        offset = at_boundary(row[0], where)
        if phase == "PRECEDING_INTERVAL" and offset == 0:
            raise _fail(f"{where} measures an interval before the run began.")
        samples.append(
            HistorySample(
                offset, address, _state_key_of(address), phase, unit,
                _value(row[4], unit, where),
            )
        )
    _check_order([s.offset_minutes for s in samples], "sample")

    intervals = [_parse_interval(row, i) for i, row in enumerate(_intervals(document))]
    for interval in intervals:
        if interval.from_offset not in recorded or interval.to_offset > (
            through or 0
        ) + timestep or interval.to_offset <= interval.from_offset:
            raise _fail(
                f"Interval [{interval.from_offset}, {interval.to_offset}) is not "
                "a step of the recorded window."
            )
    _check_order([i.from_offset for i in intervals], "interval")

    exposures = tuple(
        ForcingExposure(
            address=_str(row[0], "exposure"),
            event_id=_str(row[1], "exposure"),
            parameter_id=_str(row[2], "exposure"),
            value=_exact(row[3], f"exposures[{index}] value"),
            from_offset=in_window(row[4], f"exposures[{index}] from"),
            to_offset=in_window(row[5], f"exposures[{index}] to"),
        )
        for index, row in enumerate(_rows(document, "exposures", 6))
    )

    attempts = []
    for index, row in enumerate(_rows(document, "attempts", 11)):
        where = f"attempts[{index}]"
        outcome = _str(row[7], where)
        if outcome not in SAMPLE_OUTCOMES:
            raise _fail(f"{where} ends as {outcome!r}.")
        unit = _str(row[9], where)
        attempts.append(
            DeviceObservation(
                device_id=_str(row[2], where),
                signal_id=_str(row[3], where),
                address=_str(row[1], where),
                state_key=_str(row[4], where),
                reading_class=_str(row[5], where),
                at_offset_minutes=at_boundary(row[0], where),
                source_sample_time=_str(row[6], where),
                outcome=outcome,
                reported_value=_value(row[8], unit, where, optional=True),
                canonical_unit=unit,
                suppression_reason=_str(row[10], where, optional=True),
            )
        )
    _check_order([a.at_offset_minutes for a in attempts], "observation attempt")

    applied = tuple(
        AppliedEvent(
            event_id=_str(row[0], "applied event"),
            address=_str(row[1], "applied event"),
            direction=_str(row[2], "applied event"),
            at_offset_minutes=in_window(row[3], f"applied_events[{index}]"),
            share=_exact(row[4], f"applied_events[{index}] share"),
            declared=_exact(row[5], f"applied_events[{index}] declared"),
            origin=_str(row[6], "applied event"),
            phase_id=_str(row[7], "applied event"),
        )
        for index, row in enumerate(_rows(document, "applied_events", 8))
    )
    bounded = tuple(
        BoundedTransition(
            address=_str(row[0], "bounded transition"),
            at_offset_minutes=in_window(row[1], f"bounded_transitions[{index}]"),
            bound_case_id=_str(row[2], "bounded transition"),
            bound_kind=_str(row[3], "bounded transition"),
            bound_value=_exact(row[4], "bound value"),
            requested=_exact(row[5], "bound requested"),
            accepted=_exact(row[6], "bound accepted"),
            refused=_exact(row[7], "bound refused"),
            event_ids=_strs(row[8], "bound event ids"),
        )
        for index, row in enumerate(_rows(document, "bounded_transitions", 9))
    )
    discrete = tuple(
        DiscreteTransition(
            address=_str(row[0], "discrete transition"),
            state_key=_str(row[1], "discrete transition"),
            previous=_str(row[2], "discrete transition"),
            next=_str(row[3], "discrete transition"),
            phase=_str(row[4], "discrete transition"),
            cause=_str(row[5], "discrete transition"),
            controller_ref=_str(row[6], "discrete transition", optional=True),
            at_offset_minutes=in_window(row[7], f"discrete_transitions[{index}]"),
            simulation_time=_str(row[8], "discrete transition"),
        )
        for index, row in enumerate(_rows(document, "discrete_transitions", 9))
    )
    for family, records in (
        ("applied event", applied),
        ("bounded transition", bounded),
        ("discrete transition", discrete),
    ):
        _check_order([r.at_offset_minutes for r in records], family)
    attachments = tuple(
        BusAttachmentInput(
            role=_str(row[0], "bus attachment"),
            component_id=_str(row[1], "bus attachment"),
            via_component_id=_str(row[2], "bus attachment", optional=True),
            bus_component_id=_str(row[3], "bus attachment"),
        )
        for row in _rows(document, "bus_attachments", 4)
    )

    coverage_rows = manifest.get("coverage")
    if not isinstance(coverage_rows, list) or len(coverage_rows) != len(HISTORY_FAMILIES):
        raise _fail("The manifest does not state coverage for every family.")
    coverage = tuple(
        FamilyCoverage(
            _str(row[0], "coverage"), _str(row[1], "coverage"), _str(row[2], "coverage")
        )
        for row in coverage_rows
    )
    stated = {entry.family: entry.availability for entry in coverage}
    for family, present in (
        ("intervals", bool(intervals)),
        ("drawing", bool(attachments)),
    ):
        if stated.get(family) != "RECORDED" and present:
            raise _fail(f"The manifest says {family} is not recorded and records exist.")
    if any(value == "UNAVAILABLE" for value in stated.values()):
        raise _fail("A persisted history declares a family it did not record.")

    failure = _parse_failure(manifest.get("failure"))
    if (projection.status == "FAILED") != (failure is not None):
        raise _fail("The history's failure disagrees with the run's outcome.")

    return LabHistory(
        run_id=projection.run_id,
        status=projection.status,
        source="PERSISTED",
        statement=LAB_HISTORY_SOURCES["PERSISTED"],
        history_schema_version=LAB_HISTORY_SCHEMA_VERSION,
        boundaries_total=projection.boundaries_total,
        inputs_identity=projection.inputs_identity,
        content_digest=projection.content_digest,
        observation_series_digest=projection.observation_series_digest,
        history_digest=digest,
        coverage=coverage,
        failure=failure,
        boundaries=tuple(boundaries),
        samples=tuple(samples),
        intervals=tuple(intervals),
        exposures=exposures,
        attempts=tuple(attempts),
        signals=projection.signals,
        reporting_gaps=projection.reporting_gaps,
        applied_events=applied,
        bounded_transitions=bounded,
        discrete_transitions=discrete,
        bus_attachments=attachments,
        electrical_steps=_joined_steps(coverage, projection.electrical),
    )


def _intervals(document: dict) -> list[dict]:
    rows = document.get("intervals")
    if not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows):
        raise _fail("The history's intervals are not a list of records.")
    return rows


def _parse_interval(row: dict, index: int) -> HistoryInterval:
    where = f"intervals[{index}]"
    view_at, view_until, entries = row["view"]
    intent_from, intent_to, requests = row["intent"]
    accepted = row["accepted"]
    view = ControllerView(
        at_offset_minutes=_int(view_at, where),
        for_until_offset=_int(view_until, where),
        entries=tuple(
            ViewEntry(
                name=_str(e[0], where),
                address=_str(e[1], where),
                value=_value(e[2], _str(e[3], where), where, optional=True),
                unit=e[3],
            )
            for e in entries
        ),
    )
    intent = ControlIntent(
        from_offset=_int(intent_from, where),
        to_offset=_int(intent_to, where),
        requests=tuple(
            ControlRequest(
                address=_str(r[0], where),
                quantity=_str(r[1], where),
                requested=_value(r[2], _str(r[3], where), where),
                unit=r[3],
                reason=_str(r[4], where),
            )
            for r in requests
        ),
    )
    flow_set = AcceptedFlowSet(
        from_offset=_int(accepted["from"], where),
        to_offset=_int(accepted["to"], where),
        segments=tuple(
            (_int(a, where), _int(b, where)) for a, b in accepted["segments"]
        ),
        flows=tuple(
            AcceptedFlow(
                _str(f[0], where), _str(f[1], where), _str(f[2], where),
                _exact(f[3], where), _exact(f[4], where),
            )
            for f in accepted["flows"]
        ),
        controls=tuple(
            AcceptedControl(
                address=_str(c[0], where),
                quantity=_str(c[1], where),
                requested=_value(c[2], _str(c[4], where), where),
                accepted=_value(c[3], c[4], where),
                unit=c[4],
                limited_by=_strs(c[5], where),
            )
            for c in accepted["controls"]
        ),
        loads=tuple(
            LoadService(
                _str(l[0], where), _int(l[1], where),
                *(_exact(v, where) for v in l[2:8]),
            )
            for l in accepted["loads"]
        ),
        effective_controls=tuple(
            EffectiveControl(
                _str(e[0], where), _int(e[1], where), _int(e[2], where),
                _exact(e[3], where), _str(e[4], where), _str(e[5], where),
                _str(e[6], where),
            )
            for e in accepted["effective"]
        ),
        balances=tuple(
            BalanceIdentity(_str(b[0], where), _strs(b[1], where), _strs(b[2], where))
            for b in accepted["balances"]
        ),
        stock_accounts=tuple(
            StockAccount(
                _str(s[0], where), _exact(s[1], where), _exact(s[2], where),
                _strs(s[3], where), _strs(s[4], where),
            )
            for s in accepted["stock_accounts"]
        ),
        interval_energies=tuple(
            (_str(k, where), _exact(v, where)) for k, v in accepted["interval_energies"]
        ),
        notes=_strs(accepted["notes"], where),
    )
    return HistoryInterval(
        from_offset=flow_set.from_offset,
        to_offset=flow_set.to_offset,
        step=ControlStep(view=view, intent=intent, accepted=flow_set),
    )


def _parse_failure(raw: object) -> ExecutionFailure | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise _fail("The history's failure is not a record.")
    at = raw.get("at_offset_minutes")
    return ExecutionFailure(
        kind=_str(raw.get("kind"), "failure kind"),
        subject=_str(raw.get("subject"), "failure subject"),
        statement=_str(raw.get("statement"), "failure statement"),
        at_offset_minutes=None if at is None else _int(at, "failure offset"),
        detail=_strs(raw.get("detail"), "failure detail"),
    )
