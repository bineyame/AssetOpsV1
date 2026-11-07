"""DIESEL-1-R3f §9f.2 (5): operational actions frozen into a run as causes and reporting-path conditions.

Owner decision, verbatim (`.agent/owner-scenario-data-2026-11-07.md`): fuel events "are injected through
operational actions". A fuel delivery, an unrecorded removal and the unplugged sensor are an operator's (or an
unidentified person's) acts, never scenario entries. A run that names a log by its exact version freezes each
effect-bearing action's physical effect here, at run setup, with `origin="OPERATIONAL_ACTION"` and an `action_ref`
of `"{action_id}:{content_sha256}"`, and lists it in `intervention_history`. The scenario keeps only the world's own
conditions.

Pure: no I/O. The log arrives through `OperationalActionLogPort` as a parsed mapping and its file hash. Every
refusal is typed and raised before anything is allocated or written.

Effects (DIESEL-1-R3 §9.3 item 2, unchanged from §8.2a):
- `FUEL_DELIVERY` -> INCREASE POINT on `fuel-tank-volume@{component}` at `at`;
- `FUEL_REMOVAL_UNRECORDED` -> DECREASE WINDOW over `[at, at + duration_minutes)`, plus, with
  `sensor_disconnected`, a `fuel-level-reporting-availability@{component}` WINDOW condition over its span;
- `TANK_DIP`, `TANK_SEALED`, `SENSOR_POWER_PROTECTED` -> validated, nothing frozen.

The setup bound replaces "a delivery fits free capacity at `at`", which cannot be known before dispatch: initial
stock plus the run's deliveries up to and including this one must not exceed the frozen capacity, and a removal must
not exceed initial stock plus the run's earlier deliveries (exact `Fraction`). Refused, never clamped. The kernel's
`insufficient-fuel` floor stays the run-time backstop.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import replace
from datetime import datetime, timezone
from fractions import Fraction
from typing import Any

from assetops_backend.runs.models import (
    EFFECT_BEARING_ACTION_KINDS,
    DeterministicIdentity,
    FrozenCause,
    FrozenOperationalAction,
    FrozenOperationalActionLog,
    FrozenReportingPathCondition,
)
from assetops_backend.runs.parsing import (
    RunSetupRequest,
    check_operational_action_cross_reference,
)
from assetops_backend.runs.ports import OperationalActionLogSource
from assetops_backend.runs.profiles import ModelProfile
from assetops_backend.runs.refusals import refuse
from assetops_backend.state_refs import component_state

ACTION_KINDS = frozenset(
    {"FUEL_DELIVERY", "FUEL_REMOVAL_UNRECORDED", "TANK_DIP", "TANK_SEALED", "SENSOR_POWER_PROTECTED"}
)
LOG_KEYS = frozenset({"log_id", "log_version", "site_code", "timezone", "actions"})
COMMON_KEYS = frozenset({"action_id", "kind", "at", "actor", "component_id"})
REQUIRED_BY_KIND: dict[str, frozenset[str]] = {
    "FUEL_DELIVERY": frozenset({"volume_l", "ticket", "recorded_after_minutes"}),
    "FUEL_REMOVAL_UNRECORDED": frozenset({"volume_l", "duration_minutes"}),
    "TANK_DIP": frozenset(),
    "TANK_SEALED": frozenset(),
    "SENSOR_POWER_PROTECTED": frozenset(),
}
OPTIONAL_BY_KIND: dict[str, frozenset[str]] = {
    "FUEL_DELIVERY": frozenset(),
    "FUEL_REMOVAL_UNRECORDED": frozenset({"sensor_disconnected"}),
    "TANK_DIP": frozenset(),
    "TANK_SEALED": frozenset({"note"}),
    "SENSOR_POWER_PROTECTED": frozenset({"note"}),
}
ACTION_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
AT_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

TANK_STATE = "fuel-tank-volume"
CAPACITY_STATE = "fuel-tank-capacity"
REPORTING_STATE = "fuel-level-reporting-availability"
HISTORY_PREFIX = "OPERATIONAL_ACTION"


def content_sha256(action: Mapping[str, Any]) -> str:
    """sha256 of the action's canonical JSON: sorted keys, compact separators, ASCII (F0 `load_actions`)."""
    canonical = json.dumps(action, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("ascii")).hexdigest()


def _invalid(message: str) -> Exception:
    return refuse("OPERATIONAL_ACTION_LOG_INVALID", f"The operational-action log is not valid: {message}")


def _instant(text: str) -> datetime:
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def _positive_number(value: Any) -> bool:
    return type(value) in (int, float) and value > 0


def _positive_int(value: Any) -> bool:
    return type(value) is int and value > 0


def _validate_at(value: Any, where: str) -> None:
    if not isinstance(value, str) or not AT_PATTERN.match(value):
        raise _invalid(f"{where} is not a UTC instant spelled YYYY-MM-DDTHH:MM:SSZ.")
    try:
        _instant(value)
    except ValueError as error:
        raise _invalid(f"{where} {value!r} is not a real instant.") from error


def _validate_document(document: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """Step 1: exact keys and types, or `OPERATIONAL_ACTION_LOG_INVALID`."""
    if set(document) != LOG_KEYS:
        raise _invalid(f"its top-level keys are {sorted(document)}; expected exactly {sorted(LOG_KEYS)}.")
    if not isinstance(document["log_id"], str) or type(document["log_version"]) is not int:
        raise _invalid("'log_id' must be text and 'log_version' a whole number.")
    if not isinstance(document["site_code"], str) or not isinstance(document["timezone"], str):
        raise _invalid("'site_code' and 'timezone' must be text.")
    actions = document["actions"]
    if not isinstance(actions, list):
        raise _invalid("'actions' must be a list.")
    seen: set[str] = set()
    for index, action in enumerate(actions):
        where = f"actions[{index}]"
        if not isinstance(action, Mapping):
            raise _invalid(f"{where} is not an object.")
        kind = action.get("kind")
        if kind not in ACTION_KINDS:
            raise _invalid(f"{where} has kind {kind!r}; expected one of {sorted(ACTION_KINDS)}.")
        required = COMMON_KEYS | REQUIRED_BY_KIND[kind]
        allowed = required | OPTIONAL_BY_KIND[kind]
        if not required <= set(action) or not set(action) <= allowed:
            raise _invalid(f"{where} ({kind}) has keys {sorted(action)}; it needs {sorted(required)} and may also "
                           f"have {sorted(OPTIONAL_BY_KIND[kind])}.")
        action_id = action["action_id"]
        if not isinstance(action_id, str) or not ACTION_ID_PATTERN.match(action_id):
            raise _invalid(f"{where} has action_id {action_id!r}, which is not lower-case letters, digits, hyphens.")
        if action_id in seen:
            raise _invalid(f"action_id {action_id!r} appears twice.")
        seen.add(action_id)
        _validate_at(action["at"], f"{action_id}.at")
        for key in ("actor", "component_id"):
            if not isinstance(action[key], str) or not action[key]:
                raise _invalid(f"{action_id}.{key} must be non-empty text.")
        if "note" in action and (not isinstance(action["note"], str) or not action["note"]):
            raise _invalid(f"{action_id}.note must be non-empty text.")
        if kind in EFFECT_BEARING_ACTION_KINDS and not _positive_number(action["volume_l"]):
            raise _invalid(f"{action_id}.volume_l must be a number above 0.")
        if kind == "FUEL_DELIVERY":
            ticket = action["ticket"]
            if (not isinstance(ticket, Mapping) or set(ticket) != {"reference", "volume_l"}
                    or not isinstance(ticket["reference"], str) or not ticket["reference"]
                    or not _positive_number(ticket["volume_l"])):
                raise _invalid(f"{action_id}.ticket must be exactly a non-empty 'reference' and a 'volume_l' above 0.")
            if type(action["recorded_after_minutes"]) is not int or action["recorded_after_minutes"] < 0:
                raise _invalid(f"{action_id}.recorded_after_minutes must be a whole number from 0.")
        if kind == "FUEL_REMOVAL_UNRECORDED":
            if not _positive_int(action["duration_minutes"]):
                raise _invalid(f"{action_id}.duration_minutes must be a whole number above 0.")
            span = action.get("sensor_disconnected")
            if span is not None:
                if not isinstance(span, Mapping) or set(span) != {"at", "duration_minutes"}:
                    raise _invalid(f"{action_id}.sensor_disconnected must be exactly 'at' and 'duration_minutes'.")
                _validate_at(span["at"], f"{action_id}.sensor_disconnected.at")
                if not _positive_int(span["duration_minutes"]):
                    raise _invalid(f"{action_id}.sensor_disconnected.duration_minutes must be a whole number above 0.")
    return list(actions)


def _offset(start: datetime, text: str, action_id: str) -> int:
    """Whole minutes from the run start; a non-zero seconds field is refused, as a scenario offset would be."""
    moment = _instant(text)
    if moment.second != 0:
        raise refuse("OPERATIONAL_ACTION_SPAN_OUTSIDE_RUN",
                     f"Operational action {action_id} is placed at {text}, which is not on a whole minute. A run "
                     "places every cause on a whole-minute offset from its start.")
    return int((moment - start).total_seconds()) // 60


def _inside(action_id: str, what: str, offset: int, duration: int | None, length: int) -> None:
    """The scenario-entry interval rule (`_refuse_entries_outside_the_interval`): half-open, start inside, end ≤ length."""
    end = offset + (duration or 0)
    if offset < 0 or offset >= length or end > length:
        raise refuse("OPERATIONAL_ACTION_SPAN_OUTSIDE_RUN",
                     f"Operational action {action_id}'s {what} spans minutes [{offset}, {end}) and the run covers "
                     f"[0, {length}). An action's physical span must lie wholly inside the run: it is refused, "
                     "never clipped.")


def _stock_facts(identity: DeterministicIdentity, model: ModelProfile, component_id: str, action_id: str):
    """The initial tank volume and the frozen capacity, both in litres, or a typed refusal."""
    state = next((s for s in model.supported_states if s.state_key == TANK_STATE), None)
    if state is None or "CAUSAL_INPUT" not in state.supported_roles or state.scope != "COMPONENT":
        raise refuse("OPERATIONAL_ACTION_STATE_NOT_CAUSAL",
                     f"Operational action {action_id} moves {TANK_STATE}@{component_id}, and model profile "
                     f"{model.model_profile_id} v{model.model_profile_version} has no CAUSAL_INPUT stock for it.")
    address = component_state(TANK_STATE, component_id).addressed_key
    initial = next((i for i in identity.initialization_inputs if i.state_ref.addressed_key == address), None)
    capacity_address = component_state(CAPACITY_STATE, component_id).addressed_key
    # A model-owned need (mini-grid) or a scenario-initialized value answered by the Foundation (minimal tank).
    capacity = next((n for n in (*identity.model_needs, *identity.initialization_inputs)
                     if n.state_ref.addressed_key == capacity_address), None)
    if (initial is None or not isinstance(initial.canonical_value, (int, float))
            or capacity is None or not isinstance(capacity.canonical_value, (int, float))):
        raise refuse("OPERATIONAL_ACTION_STATE_NOT_CAUSAL",
                     f"Operational action {action_id} moves {address}, and the run froze no initial value for it or "
                     f"no {capacity_address}, so no bound can be computed for the action.")
    if initial.canonical_unit != "L" or capacity.canonical_unit != "L":
        raise refuse("OPERATIONAL_ACTION_UNIT",
                     f"Operational action {action_id} is in litres and the run's {address} is in "
                     f"{initial.canonical_unit} with capacity in {capacity.canonical_unit}.")
    return initial, Fraction(initial.canonical_value), Fraction(capacity.canonical_value)


def freeze_operational_actions(
    request: RunSetupRequest,
    identity: DeterministicIdentity,
    log_source: OperationalActionLogSource,
    *,
    model: ModelProfile,
    start: str,
    end: str,
    component_ids: frozenset[str],
) -> DeterministicIdentity:
    """Steps 1-8 of §9f.2 (5): validate, select, check, build, and return the identity with the actions frozen."""
    named = request.operational_actions
    assert named is not None, "freeze_operational_actions is called only for a request naming a log"
    document = log_source.document
    actions = _validate_document(document)

    if (document["log_id"] != named.log_id or document["log_version"] != named.log_version
            or document["site_code"] != request.site_id):
        raise refuse("OPERATIONAL_ACTION_LOG_MISMATCH",
                     f"Operational-action log {named.log_id} v{named.log_version} says it is "
                     f"{document['log_id']!r} v{document['log_version']!r} for Site {document['site_code']!r}; the run "
                     f"named {named.log_id!r} v{named.log_version} for Site {request.site_id!r}.")

    run_start, run_end = _instant(start), _instant(end)
    length = int((run_end - run_start).total_seconds()) // 60
    hashed = [(action, content_sha256(action)) for action in actions]
    selected = [(a, h) for a, h in hashed if run_start <= _instant(a["at"]) < run_end]

    facts: dict[str, Any] = {}
    for action, _ in selected:
        action_id, kind = action["action_id"], action["kind"]
        if action["component_id"] not in component_ids:
            raise refuse("OPERATIONAL_ACTION_COMPONENT_UNKNOWN",
                         f"Operational action {action_id} names component {action['component_id']!r}, which Site "
                         f"{request.site_id} does not have.")
        if kind not in EFFECT_BEARING_ACTION_KINDS:
            _inside(action_id, "instant", _offset(run_start, action["at"], action_id), None, length)
            continue
        facts[action_id] = _stock_facts(identity, model, action["component_id"], action_id)
        offset = _offset(run_start, action["at"], action_id)
        _inside(action_id, "window" if kind == "FUEL_REMOVAL_UNRECORDED" else "instant", offset,
                action.get("duration_minutes"), length)
        span = action.get("sensor_disconnected")
        if span is not None:
            _inside(action_id, "sensor span", _offset(run_start, span["at"], action_id), span["duration_minutes"],
                    length)

    effect_bearing = sorted(((a, h) for a, h in selected if a["kind"] in EFFECT_BEARING_ACTION_KINDS),
                            key=lambda pair: (_instant(pair[0]["at"]), pair[0]["action_id"]))
    delivered: dict[str, Fraction] = {}
    for action, _ in effect_bearing:
        component = action["component_id"]
        _, initial, capacity = facts[action["action_id"]]
        so_far = delivered.get(component, Fraction(0))
        volume = Fraction(action["volume_l"])
        if action["kind"] == "FUEL_DELIVERY":
            so_far += volume
            delivered[component] = so_far
            if initial + so_far > capacity:
                raise refuse("OPERATIONAL_ACTION_OVER_CAPACITY",
                             f"Operational action {action['action_id']} delivers {action['volume_l']} L: the run's "
                             f"initial {float(initial)} L plus its deliveries so far ({float(so_far)} L) exceeds the "
                             f"tank's frozen capacity of {float(capacity)} L. It is refused, never clamped.")
        elif volume > initial + so_far:
            raise refuse("OPERATIONAL_ACTION_OVER_STOCK",
                         f"Operational action {action['action_id']} removes {action['volume_l']} L, more than the "
                         f"run's initial {float(initial)} L plus its earlier deliveries ({float(so_far)} L).")

    causes: list[FrozenCause] = []
    conditions: list[FrozenReportingPathCondition] = []
    for action, sha in effect_bearing:
        action_id, component = action["action_id"], action["component_id"]
        initial_input = facts[action_id][0]
        ref = f"{action_id}:{sha}"
        removal = action["kind"] == "FUEL_REMOVAL_UNRECORDED"
        causes.append(FrozenCause(
            event_id=f"{action_id}/{'tank-decrease' if removal else 'tank-increase'}",
            state_ref=component_state(TANK_STATE, component),
            direction="DECREASE" if removal else "INCREASE",
            parameter_id=f"{action_id}-volume",
            canonical_value=float(action["volume_l"]),
            canonical_unit=initial_input.canonical_unit,
            dimension=initial_input.dimension,
            timing_shape="WINDOW" if removal else "POINT",
            offset_minutes=_offset(run_start, action["at"], action_id),
            duration_minutes=action["duration_minutes"] if removal else None,
            origin="OPERATIONAL_ACTION",
            action_ref=ref,
        ))
        span = action.get("sensor_disconnected")
        if span is not None:
            conditions.append(FrozenReportingPathCondition(
                event_id=f"{action_id}/sensor-disconnected",
                state_ref=component_state(REPORTING_STATE, component),
                timing_shape="WINDOW",
                offset_minutes=_offset(run_start, span["at"], action_id),
                duration_minutes=span["duration_minutes"],
                origin="OPERATIONAL_ACTION",
                action_ref=ref,
            ))

    existing = {item.event_id for item in (*identity.causes, *identity.forcings, *identity.reporting_path_conditions)}
    for item in (*causes, *conditions):
        if item.event_id in existing:
            raise refuse("OPERATIONAL_ACTION_EVENT_ID_CONFLICT",
                         f"Operational action event {item.event_id} has the same event id as an entry the run already "
                         "froze from its scenario.")

    frozen = replace(
        identity,
        causes=identity.causes + tuple(causes),
        reporting_path_conditions=identity.reporting_path_conditions + tuple(conditions),
        intervention_history=identity.intervention_history
        + tuple(f"{HISTORY_PREFIX}:{a['action_id']}:{h}" for a, h in effect_bearing),
        operational_action_log=FrozenOperationalActionLog(
            log_id=named.log_id,
            log_version=named.log_version,
            sha256=log_source.sha256,
            actions=tuple(
                FrozenOperationalAction(action_id=a["action_id"], kind=a["kind"], actor=a["actor"], at=a["at"],
                                        content_sha256=h)
                for a, h in effect_bearing
            ),
        ),
    )
    broken = check_operational_action_cross_reference(frozen)
    assert broken is None, f"run setup froze an inconsistent operational-action identity: {broken}"
    return frozen
