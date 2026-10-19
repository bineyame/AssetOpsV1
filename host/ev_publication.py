"""W2-05b commit 3: an EV run's public DeviceReport v2 series (`D-2026-10-18-w2-05-buildspec`).

`ev_channels` reads the selected effective `ev-roles-1` binding rows into the closed
`simulator-lab-gateway-ev/1` channel table: device and signal IDs and the bound connector asset come from
the binding, never from string construction, and a row outside the closed 15-tuple table, a role that
disagrees with it, or a missing tuple refuses (`EvBindingRefused`). `ev_reports` runs the pure `ev-charger/1`
pack over the scenario document, applies `ev-publication/1`/`ev-observation/1`
(`assetops_simulator.observation.transform.ev_public_records`) and adapts each public record to one v2
report. Only public reports cross into product data; no private request, forcing, run ID or oracle.

Commit 4 (q4 Q22/Q23): `verify_ev_inputs` re-reads the exact frozen Foundation revision, binding revision and
scenario, checks every frozen SHA and snapshot row, and maps the Foundation to the closed `EvParameters`; anything
missing, changed or outside the single-rating/single-schedule model refuses `FrozenRunNotReconstructible`
before Stage.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from fractions import Fraction
from typing import Any, Iterable, Mapping

from assetops_backend.runs.models import SimulationRun
from assetops_backend.sites.binding_alignment import binding_content
from assetops_backend.sites.foundation_content import content_digest

from assetops_backend.scenarios.ev_parsing import EvScenarioDefinition
from assetops_contracts.gateway_report import (
    DeviceReportV2,
    device_report_v2_text,
    ev_event_id,
    ev_fault_episode_id,
    ev_report_key,
    parse_device_report_v2_text,
)
from assetops_contracts.source_envelope import canonical_json
from assetops_contracts.source_envelope_v4 import V4_EV_CHANNEL_MAPPINGS
from assetops_simulator.observation.transform import (
    EV_CONNECTOR_CHANNELS,
    EV_SITE_CHANNEL,
    EvChannel,
    EvPublicRecord,
    ev_public_records,
)
from assetops_simulator.packs.errors import PhysicallyUnacceptable
from assetops_simulator.packs.ev_charger import (
    CONNECTORS,
    EvChargerPack,
    EvForcingRow,
    EvParameters,
    EvRun,
    run_window,
)

from execution_adapter import FrozenRunNotReconstructible, execution_path

_INSTANT = "%Y-%m-%dT%H:%M:%SZ"

#: The `ev-roles-1` role each logical public channel serves (05a binding vocabulary).
EV_CHANNEL_ROLES: Mapping[str, str] = {
    "session-event": "ev_session_event",
    "fault-event": "ev_connector_fault",
    "state": "ev_connector_state",
    "requested-power": "ev_requested_power",
    "allocated-limit": "ev_allocated_limit",
    "energy": "ev_connector_energy",
    "power": "ev_connector_power",
    EV_SITE_CHANNEL: "ev_site_import",
}
_CHANNEL_OF_ROLE = {role: channel for channel, role in EV_CHANNEL_ROLES.items()}


class EvBindingRefused(ValueError):
    """The selected binding is not the closed `simulator-lab-gateway-ev/1` table: a typed binding refusal."""


@dataclass(frozen=True)
class EvReport:
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


def ev_channels(rows: Iterable[Mapping[str, Any]]) -> dict[tuple[str | None, str], EvChannel]:
    """The closed channel table from the selected binding rows (`device_id`, `signal_id`, `role`, `asset_code`).

    Exactly the 15 `V4_EV_CHANNEL_MAPPINGS` tuples, each bound once with the table's role; a connector channel
    is bound to `c1` or `c2`, and the Site import to a non-connector asset."""
    channels: dict[tuple[str | None, str], EvChannel] = {}
    seen: set[tuple[str, str]] = set()
    for row in rows:
        key = (row.get("device_id"), row.get("signal_id"))
        entry = V4_EV_CHANNEL_MAPPINGS.get(key)
        if entry is None:
            raise EvBindingRefused(f"{key[0]}/{key[1]} is not a simulator-lab-gateway-ev/1 tuple")
        if key in seen:
            raise EvBindingRefused(f"{key[0]}/{key[1]} is bound twice")
        seen.add(key)
        role = row.get("role")
        if role != entry.role or role not in _CHANNEL_OF_ROLE:
            raise EvBindingRefused(f"{key[0]}/{key[1]} is bound to role {role!r}, not {entry.role!r}")
        channel = _CHANNEL_OF_ROLE[role]
        asset = row.get("asset_code")
        if channel == EV_SITE_CHANNEL:
            if asset in CONNECTORS or not isinstance(asset, str):
                raise EvBindingRefused(f"Site import is bound to {asset!r}, not the Site meter")
            connector = None
            connector_asset = None
        else:
            if asset not in CONNECTORS:
                raise EvBindingRefused(f"{key[0]}/{key[1]} is bound to {asset!r}, not a declared connector")
            connector = asset
            connector_asset = asset
        if (connector, channel) in channels:
            raise EvBindingRefused(f"{connector}/{channel} is bound twice")
        channels[(connector, channel)] = EvChannel(device_id=key[0], signal_id=key[1], connector_id=connector_asset)
    missing = [k for k in V4_EV_CHANNEL_MAPPINGS if k not in seen]
    if missing:
        raise EvBindingRefused(f"the binding lacks {', '.join(f'{d}/{s}' for d, s in sorted(missing))}")
    expected = {(c, name) for c in CONNECTORS for name in EV_CONNECTOR_CHANNELS} | {(None, EV_SITE_CHANNEL)}
    if set(channels) != expected:
        raise EvBindingRefused("the binding does not bind each connector's seven channels and one Site import")
    return channels


def ev_execution(definition: EvScenarioDefinition, parameters: EvParameters) -> EvRun:
    """Execute the scenario's whole window once: 60 minutes and the closing boundary (61 documents)."""
    forcing = tuple(EvForcingRow(at=_at(f.time), kind=f.kind, connector=f.connector, value=f.value)
                    for f in definition.forcing)
    pack = EvChargerPack(parameters, scenario_sha256=definition.scenario_sha256)
    return run_window(pack, start=_at(definition.start), end=_at(definition.end), forcing=forcing)


def _observation_rows(definition: EvScenarioDefinition) -> tuple:
    from types import SimpleNamespace

    return tuple(
        SimpleNamespace(time=_at(o.time), kind=o.kind, connector=o.connector, action=o.action,
                        release_at=None if o.release_at is None else _at(o.release_at))
        for o in definition.observations
    )


def report_of(record: EvPublicRecord, scenario_sha256: str) -> DeviceReportV2:
    """The public v2 report of one EV public record; every schema-2 key present, inapplicable ones null."""
    source_time = _text(record.source_time)
    if record.family == "MEASUREMENT":
        interval_start = _text(record.interval_start)
        return DeviceReportV2(
            report_key=ev_report_key(scenario_sha256=scenario_sha256, device_id=record.device_id,
                                     signal_id=record.signal_id, source_time=source_time, record_kind=None,
                                     event_id=None, interval_start=interval_start),
            device_id=record.device_id, signal_id=record.signal_id, source_time=source_time, family="MEASUREMENT",
            measurement=record.measurement, interval_start=interval_start,
            interval_end=None if interval_start is None else source_time, value=record.value, unit=record.unit,
            quality="GOOD", unavailable_reason=None, record_kind=None, event_id=None, correlation_id=None,
            component_id=None, actor=None, outcome=None, session_id=record.session_id,
            connector_id=record.connector_id,
        )
    event_id = ev_event_id(scenario_sha256=scenario_sha256, device_id=record.device_id, signal_id=record.signal_id,
                           transition_ordinal=record.transition_ordinal)
    return DeviceReportV2(
        report_key=ev_report_key(scenario_sha256=scenario_sha256, device_id=record.device_id,
                                 signal_id=record.signal_id, source_time=source_time,
                                 record_kind=record.record_kind, event_id=event_id, interval_start=None),
        device_id=record.device_id, signal_id=record.signal_id, source_time=source_time, family="EVENT",
        measurement=None, interval_start=None, interval_end=None, value=None, unit=None, quality="GOOD",
        unavailable_reason=None, record_kind=record.record_kind, event_id=event_id,
        correlation_id=_correlation(record, scenario_sha256), component_id=record.component_id, actor="CONTROLLER",
        outcome=record.outcome, session_id=record.session_id, connector_id=record.connector_id,
    )


def _correlation(record: EvPublicRecord, scenario_sha256: str) -> str:
    """q3 Q16: S when the event carries one; otherwise the FAULT/CLEAR's fault-episode identity."""
    if record.session_id is not None:
        return record.session_id
    if record.fault_episode is None:
        raise ValueError(f"{record.record_kind} at {_text(record.source_time)} carries no session or fault episode")
    connector_id, fault_ordinal = record.fault_episode
    return ev_fault_episode_id(scenario_sha256=scenario_sha256, connector_id=connector_id,
                               fault_ordinal=fault_ordinal)


def ev_reports(
    definition: EvScenarioDefinition,
    channels: Mapping[tuple[str | None, str], EvChannel],
    run: EvRun,
) -> tuple[EvReport, ...]:
    """The run's public v2 series in the commit 3 order, held reports included; each text reparses."""
    out: list[EvReport] = []
    records = ev_public_records(run, channels=dict(channels), observations=_observation_rows(definition))
    for record in records:
        report = report_of(record, definition.scenario_sha256)
        text = device_report_v2_text(report)
        if parse_device_report_v2_text(text) != report:
            raise ValueError(f"the {record.device_id}/{record.signal_id} report does not round-trip")
        out.append(EvReport(
            report_key=report.report_key, report_text=text, device_id=report.device_id,
            signal_id=report.signal_id, source_time=report.source_time,
            published_at=_text(record.published_at), held=record.held,
        ))
    return tuple(out)


def ev_series_digest(reports: tuple[EvReport, ...]) -> str:
    """SHA-256 of canonical ordered DeviceReport V2 texts, held reports included; `[]` for an empty series."""
    return ev_series_digest_of_texts([r.report_text for r in reports])


def ev_series_digest_of_texts(texts: Iterable[str]) -> str:
    """`ev_series_digest` over the ordered texts themselves (the schema-7 artifact recomputes it on read)."""
    return hashlib.sha256(canonical_json(list(texts)).encode("utf-8")).hexdigest()


# --- Commit 4: the frozen inputs, re-read and verified (q4 Q22/Q23) -----------------------------------------

EV_ROLE_SET = "ev-roles-1"
_WEEKDAYS = ("MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY")
_CLOCK = re.compile(r"([01][0-9]|2[0-3]):([0-5][0-9])")


@dataclass(frozen=True)
class VerifiedEvInputs:
    parameters: EvParameters
    definition: EvScenarioDefinition
    channels: Mapping[tuple[str | None, str], EvChannel]


def _refuse(reason: str) -> FrozenRunNotReconstructible:
    return FrozenRunNotReconstructible(reason)


def _one_property(content: Mapping[str, Any], key: str, component_type: str, unit: str) -> Any:
    found = [(c, p) for c in content.get("components") or () for p in c.get("properties") or ()
             if p.get("property_key") == key]
    if len(found) != 1:
        raise _refuse(f"Foundation property {key} is stated {len(found)} times, not once")
    component, item = found[0]
    if component.get("component_type") != component_type or item.get("unit") != unit:
        raise _refuse(f"Foundation property {key} is not a {unit} property of the {component_type}")
    return item.get("value")


def _kw(value: Any, where: str) -> Fraction:
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise _refuse(f"{where} {value!r} is not a finite nonnegative kW value")
    return Fraction(str(value))


def _clock(value: Any, where: str) -> time:
    match = _CLOCK.fullmatch(value) if isinstance(value, str) else None
    if match is None:
        raise _refuse(f"{where} {value!r} is not an HH:MM local time")
    return time(int(match.group(1)), int(match.group(2)))


def ev_parameters(content: Mapping[str, Any], *, window_start: str, window_end: str) -> EvParameters:
    """q4 Q22: the frozen Foundation revision's content as the closed single-rating/single-schedule model.

    `feed-1` AC_BUS `ev-site-import-limit` -> `site_limit_kw`; `charger-1` EV_CHARGER `ev-charger-max-power` ->
    `charger_rating_kw`; c1/c2 `ev-connector-max-power` -> the one `connector_rating_kw` only if equal; both
    connectors ENABLED with the same one weekly TUESDAY 08:00-16:00 Etc/UTC row covering the run date;
    `base_load_kw` is 0 and no base load may be stated. Never averaged, minimised or defaulted."""
    components = content.get("components") or ()
    connectors = sorted(c.get("component_id") for c in components if c.get("component_type") == "EV_CONNECTOR")
    if connectors != sorted(CONNECTORS):
        raise _refuse(f"the Foundation connectors are {connectors}, not {list(CONNECTORS)}")
    for component in components:
        for item in component.get("properties") or ():
            key = str(item.get("property_key"))
            if "base-load" in key or "base_load" in key:
                raise _refuse(f"ev-charger/1 has no base load, and the Foundation states {key}")
    site_limit = _kw(_one_property(content, "ev-site-import-limit", "AC_BUS", "kW"), "ev-site-import-limit")
    charger = _kw(_one_property(content, "ev-charger-max-power", "EV_CHARGER", "kW"), "ev-charger-max-power")
    ratings: list[Fraction] = []
    for code in CONNECTORS:
        component = next(c for c in components if c.get("component_id") == code)
        own: dict[Any, Any] = {}
        for item in component.get("properties") or ():
            if item.get("property_key") in own:
                raise _refuse(f"{code} states {item.get('property_key')} twice")
            own[item.get("property_key")] = item
        rating, enabled = own.get("ev-connector-max-power"), own.get("ev-connector-enabled")
        if rating is None or rating.get("unit") != "kW":
            raise _refuse(f"{code} has no kW ev-connector-max-power")
        if enabled is None or enabled.get("unit") != "state" or enabled.get("value") != "ENABLED":
            raise _refuse(f"{code} is not ev-connector-enabled=ENABLED")
        ratings.append(_kw(rating.get("value"), f"{code} ev-connector-max-power"))
    if len(set(ratings)) != 1:
        raise _refuse(f"the connector ratings {[str(r) for r in ratings]} differ; ev-charger/1 has one")
    schedules = content.get("connector_enable_schedules")
    if not isinstance(schedules, list):
        raise _refuse("the Foundation has no connector enable schedules")
    rows = []
    for code in CONNECTORS:
        mine = [s for s in schedules if isinstance(s, Mapping) and s.get("connector_asset_id") == code]
        if len(mine) != 1:
            raise _refuse(f"{code} has {len(mine)} enable schedules, not one")
        weekly = mine[0].get("weekly")
        if mine[0].get("time_zone") != "Etc/UTC" or not isinstance(weekly, list) or len(weekly) != 1:
            raise _refuse(f"{code} does not have exactly one weekly Etc/UTC enable row")
        row = weekly[0]
        if (not isinstance(row, Mapping) or type(row.get("utc_offset_minutes")) is not int
                or row.get("utc_offset_minutes") != 0 or row.get("weekday") not in _WEEKDAYS):
            raise _refuse(f"{code}'s enable row is not a weekday at UTC offset 0")
        rows.append((row["weekday"], _clock(row.get("local_start"), f"{code} local_start"),
                     _clock(row.get("local_end"), f"{code} local_end")))
    if len(set(rows)) != 1:
        raise _refuse("the connector enable schedules differ; ev-charger/1 has one")
    weekday, enabled_from, enabled_to = rows[0]
    if (weekday, enabled_from, enabled_to) != ("TUESDAY", time(8, 0), time(16, 0)):
        raise _refuse(f"the enable schedule {weekday} {enabled_from}-{enabled_to} is not the ruled TUESDAY "
                      "08:00-16:00")
    start, end = _at(window_start), _at(window_end)
    if _WEEKDAYS[start.weekday()] != weekday or (end - timedelta(seconds=1)).date() != start.date():
        raise _refuse(f"the run window [{window_start}, {window_end}) is not within one {weekday}")
    try:
        return EvParameters(site_limit_kw=site_limit, base_load_kw=Fraction(0), connector_rating_kw=ratings[0],
                            charger_rating_kw=charger, enabled_from=enabled_from, enabled_to=enabled_to)
    except PhysicallyUnacceptable as invalid:
        raise _refuse(f"the frozen Foundation values are not a valid ev-charger/1 world: {invalid}") from invalid


def _snapshot_rows(run: SimulationRun, binding_revision: Any, revision: Any) -> list[dict[str, Any]]:
    """q4 Q23: the exact re-read binding revision equals the frozen snapshot, row by row; each row's
    `asset_code` comes from the run's frozen signal mappings, cross-checked against the frozen Foundation."""
    basis = run.registered_basis
    if binding_revision is None or str(binding_revision.id) != basis.binding_set_revision_id:
        raise _refuse(f"binding revision {basis.binding_set_revision_id} is unavailable")
    frozen = basis.snapshot_canonical.encode("utf-8")
    stored = binding_revision.snapshot_canonical
    stored = stored.encode("utf-8") if isinstance(stored, str) else bytes(stored)
    if (binding_revision.snapshot_sha256 != basis.snapshot_sha256 or stored != frozen
            or hashlib.sha256(stored).hexdigest() != basis.snapshot_sha256):
        raise _refuse("the binding revision snapshot does not match the frozen snapshot bytes and SHA")
    try:
        document = json.loads(frozen)
        mapping, foundation, snapshot_rows = document["mapping"], document["foundation"], document["bindings"]
    except (ValueError, KeyError, TypeError) as damaged:
        raise _refuse(f"the frozen snapshot is not an acquisition snapshot: {damaged}") from damaged
    if (mapping.get("binding_set_revision_id") != basis.binding_set_revision_id
            or foundation.get("revision_id") != basis.foundation_revision_id
            or foundation.get("content_sha256") != basis.foundation_content_sha256
            or mapping.get("role_set") != EV_ROLE_SET or binding_revision.role_set != EV_ROLE_SET):
        raise _refuse("the frozen snapshot does not name the frozen revisions and the ev-roles-1 role set")
    reread = sorted(({"binding_revision_id": str(b.id), **binding_content(b)} for b in binding_revision.bindings),
                    key=lambda b: (b["device_id"], b["signal_id"]))
    if reread != snapshot_rows:
        raise _refuse("the re-read binding revision rows differ from the frozen snapshot rows")
    codes = {m.mapping_id: m.component_id for m in run.deterministic_identity.signal_mappings}
    types = {c.get("component_id"): c.get("component_type") for c in revision.content.get("components") or ()}
    devices = list(revision.content.get("devices") or ())
    code_of_asset: dict[Any, str] = {}
    asset_of_code: dict[str, Any] = {}
    rows = []
    for row in snapshot_rows:
        code = codes.get(row["binding_revision_id"])
        if code is None or code not in types:
            raise _refuse(f"binding {row['binding_revision_id']} has no frozen Foundation component")
        # q5 N13: the frozen Foundation's own device declaration owns the component, so a consistent c1/c2
        # swap in the run mappings disagrees with it and refuses before Stage.
        declared = [d for d in devices if isinstance(d, dict) and d.get("device_id") == row["device_id"]]
        signals = [] if len(declared) != 1 else [
            s for s in declared[0].get("signals") or () if isinstance(s, dict) and s.get("signal_id") == row["signal_id"]]
        if len(declared) != 1 or len(signals) != 1:
            raise _refuse(f"device {row['device_id']} signal {row['signal_id']} is not declared exactly once "
                          "in the frozen Foundation")
        if declared[0].get("component_id") != code:
            raise _refuse(f"binding {row['binding_revision_id']} maps {row['device_id']} to {code}, but the frozen "
                          f"Foundation declares it on {declared[0].get('component_id')}")
        connector_role = row["role"] != "ev_site_import"
        if connector_role != (types[code] == "EV_CONNECTOR"):
            raise _refuse(f"binding {row['binding_revision_id']} ({row['role']}) is bound to {code}, a {types[code]}")
        asset = row["asset_id"]
        if code_of_asset.setdefault(asset, code) != code or asset_of_code.setdefault(code, asset) != asset:
            raise _refuse(f"asset {asset} and component {code} disagree across the frozen bindings")
        rows.append({"device_id": row["device_id"], "signal_id": row["signal_id"], "role": row["role"],
                     "asset_code": code})
    return rows


def verify_ev_inputs(
    run: SimulationRun, revision: Any, binding_revision: Any, definition: EvScenarioDefinition | None
) -> VerifiedEvInputs:
    """Check the re-read Foundation revision, binding revision and EV document against the frozen run, then
    extract the closed parameters and channel table (q4 Q22/Q23). Never reads current or fixture values."""
    if execution_path(run) != "EV":
        raise _refuse("not an EV run")
    basis = run.registered_basis
    identity = run.deterministic_identity
    if basis is None:
        raise _refuse("an EV run is registered")
    if revision is None or str(revision.id) != basis.foundation_revision_id:
        raise _refuse(f"Foundation revision {basis.foundation_revision_id} is unavailable")
    if (revision.content_sha256 != basis.foundation_content_sha256
            or content_digest(revision.content) != basis.foundation_content_sha256):
        raise _refuse("the Foundation revision content does not match the frozen SHA")
    if definition is None:
        raise _refuse(f"EV scenario {identity.scenario.scenario_id} is unavailable")
    if (definition.scenario_id, definition.version) != (identity.scenario.scenario_id,
                                                        identity.scenario.scenario_version):
        raise _refuse("the EV document is not the frozen scenario version")
    if identity.scenario.scenario_sha256 is None or definition.scenario_sha256 != identity.scenario.scenario_sha256:
        raise _refuse("the EV document does not match the frozen scenario SHA")
    frozen_observation = identity.profiles.observation_sha256
    if frozen_observation is None or definition.observation_sha256 != frozen_observation:
        raise _refuse("the EV observation rows do not match the frozen observation SHA")
    if (identity.interval.start_time, identity.interval.end_time) != (definition.start, definition.end):
        raise _refuse("the frozen interval is not the EV document's window")
    parameters = ev_parameters(revision.content, window_start=definition.start, window_end=definition.end)
    try:
        channels = ev_channels(_snapshot_rows(run, binding_revision, revision))
    except EvBindingRefused as refused:
        raise _refuse(f"the frozen EV binding is not the closed channel table: {refused}") from refused
    return VerifiedEvInputs(parameters=parameters, definition=definition, channels=channels)
