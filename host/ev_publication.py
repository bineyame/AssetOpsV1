"""W2-05b commit 3: an EV run's public DeviceReport v2 series (`D-2026-10-18-w2-05-buildspec`).

`ev_channels` reads the selected effective `ev-roles-1` binding rows into the closed
`simulator-lab-gateway-ev/1` channel table: device and signal IDs and the bound connector asset come from
the binding, never from string construction, and a row outside the closed 15-tuple table, a role that
disagrees with it, or a missing tuple refuses (`EvBindingRefused`). `ev_reports` runs the pure `ev-charger/1`
pack over the scenario document, applies `ev-publication/1`/`ev-observation/1`
(`assetops_simulator.observation.transform.ev_public_records`) and adapts each public record to one v2
report. Only public reports cross into product data; no private request, forcing, run ID or oracle.

Re-reading and verifying the frozen Foundation/binding/scenario inputs and host dispatch are commit 4.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

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
from assetops_simulator.packs.ev_charger import (
    CONNECTORS,
    EvChargerPack,
    EvForcingRow,
    EvParameters,
    EvRun,
    run_window,
)

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
    return hashlib.sha256(canonical_json([r.report_text for r in reports]).encode("utf-8")).hexdigest()
