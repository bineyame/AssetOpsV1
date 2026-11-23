"""DD5a (D-DD.139, D-DD.91, D-DD.29): seal a world Site's readings into Batch V2 bodies, as the gateway would.

`seal_readings` is pure. It mirrors `gateway/assetops_gateway/service.py` (`_envelope_v3_text`, `_envelope_v4`, `_seal`):
mini-grid rows become `SourceEnvelopeV3`, cold and EV rows `SourceEnvelopeV4`. Envelope `device_id` is the row's
`source_id` (D-DD.72); envelope `source_id` is the bound source UUID from the binding snapshot. `published_at` is the
source time, quality GOOD, times in UTC `Z`. A measurement is STATE_AT_INSTANT when `start` = `end`, INTERVAL_MEAN
otherwise, INTERVAL_DELTA for EV connector energy.

Batches: per (Site, source, local day), split into consecutive batches of at most `MAX_BATCH_ENVELOPES` in reading
order, named `<SITE>.<source>.<day>.<n>.batch.json`; `sequence_epoch` "1" and one sequence per source over the whole
span, so no message id repeats across days. Cold event ids are formed here (D-DD.91); readings files stay id-free.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Iterable, Mapping

from assetops_contracts.gateway_report import cold_correlation_id, cold_event_id, ev_session_id
from assetops_contracts.ingestion_batch_v2 import MAX_BATCH_ENVELOPES, seal_batch_v2
from assetops_contracts.source_envelope_v3 import SourceEnvelopeV3, canonical_envelope_v3_text, v3_message_id
from assetops_contracts.source_envelope_v4 import SourceEnvelopeV4, canonical_envelope_v4_text

SEQUENCE_EPOCH = "1"
#: The one role whose measurement is an interval delta (D-DD.139).
DELTA_ROLES = frozenset({"ev_connector_energy"})


class WorldSealRefused(Exception):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code} {detail}")
        self.code, self.detail = code, detail


@dataclass(frozen=True)
class SealContext:
    """One Site's binding snapshot facts. `bindings` maps `(device_id, signal_id)` to the snapshot's binding row
    (`source_id`, `gateway_id`, `role`, ...). `foundation_digest` is the Site's digest in `F` (D-DD.91). `v4` is
    False for a mini-grid Site (v3 envelopes) and True for cold and EV."""

    site_code: str
    site_id: str
    gateway_id: str
    source_mode: str
    foundation_version: int
    foundation_valid_from: str
    binding_set_id: str
    binding_version: int
    snapshot_sha256: str
    foundation_digest: str
    v4: bool
    bindings: Mapping[tuple[str, str], Mapping[str, Any]]


@dataclass(frozen=True)
class SealedBatch:
    name: str
    source_id: str
    day: str
    count: int
    text: str


def _utc(text: str) -> str:
    moment = datetime.fromisoformat(text)
    if moment.tzinfo is None:
        raise WorldSealRefused("WORLD_TELEMETRY_UNRESOLVED", f"reading time {text!r} has no offset")
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


_DECIMAL_TEXT = re.compile(r"-?[0-9]+(?:\.[0-9]+)?")


def _value(value: Any) -> Any:
    """The readings writer prints a decimal to the millesimal ("4.000"); an envelope carries the same exact value in
    canonical spelling ("4"). Labels (states) and null pass unchanged."""
    if type(value) is not str or not _DECIMAL_TEXT.fullmatch(value):
        return value
    text = format(Decimal(value).normalize(), "f")
    return "0" if text in ("-0", "0") else text


def _measurement(row: Mapping[str, Any], role: str) -> str:
    if role in DELTA_ROLES:
        return "INTERVAL_DELTA"
    return "STATE_AT_INSTANT" if row["start"] == row["end"] else "INTERVAL_MEAN"


def _envelope_text(context: SealContext, row: Mapping[str, Any], binding: Mapping[str, Any], sequence: int) -> str:
    source_id, gateway_id = str(binding["source_id"]), str(binding["gateway_id"])
    end = _utc(row["end"])
    message = dict(
        message_id=v3_message_id(site_id=context.site_id, gateway_id=gateway_id, source_id=source_id,
                                 sequence_epoch=SEQUENCE_EPOCH, sequence=sequence),
        sequence_epoch=SEQUENCE_EPOCH, sequence=sequence, site_id=context.site_id, gateway_id=gateway_id,
        source_id=source_id, device_id=row["source_id"], signal_id=row["signal_id"],
        binding_set_id=context.binding_set_id, binding_version=context.binding_version, source_time=end,
        published_at=end)
    event = row.get("event")
    if not context.v4:
        if event is not None:
            raise WorldSealRefused("WORLD_TELEMETRY_UNRESOLVED",
                                   f"{row['source_id']}/{row['signal_id']} is an event row on a v3 Site")
        measurement = _measurement(row, binding.get("role", ""))
        return canonical_envelope_v3_text(SourceEnvelopeV3(
            **message, interval_start=None if measurement == "STATE_AT_INSTANT" else _utc(row["start"]),
            interval_end=end if measurement == "INTERVAL_MEAN" else None, family="MEASUREMENT",
            measurement=measurement, value=_value(row["value"]), unit=row["unit"], quality="GOOD", unavailable_reason=None))
    common = dict(quality="GOOD", unavailable_reason=None, session_id=None, connector_id=None, record_kind=None,
                  event_id=None, correlation_id=None, component_id=None, actor=None, outcome=None)
    if event is not None:
        if event["record_kind"].startswith("EV_"):
            # The EV half (DD4b's session rows): the session id and connector of an EV event are not formed yet.
            raise WorldSealRefused("WORLD_TELEMETRY_UNRESOLVED",
                                   f"{row['source_id']}/{row['signal_id']} EV events wait for DD4b's session rows")
        kind, ordinal = event["correlation"]
        return canonical_envelope_v4_text(SourceEnvelopeV4(
            **message, interval_start=None, interval_end=None, family="EVENT", value=row["value"],
            unit=None if row["value"] is None else row["unit"], measurement=None,
            **{**common, "record_kind": event["record_kind"], "outcome": event["outcome"], "actor": event["actor"],
               "component_id": event["component_id"],
               "event_id": cold_event_id(scenario_sha256=context.foundation_digest, device_id=row["source_id"],
                                         signal_id=row["signal_id"], transition_ordinal=event["ordinal"]),
               "correlation_id": cold_correlation_id(scenario_sha256=context.foundation_digest,
                                                     correlation_key=(kind, ordinal))}))
    measurement = _measurement(row, binding.get("role", ""))
    session = row.get("session")
    ids = {}
    if session is not None:
        ids = {"session_id": ev_session_id(foundation_digest=context.foundation_digest,
                                           connector_id=session["connector_id"], session_ordinal=session["ordinal"]),
               "connector_id": session["connector_id"]}
    return canonical_envelope_v4_text(SourceEnvelopeV4(
        **message, interval_start=None if measurement == "STATE_AT_INSTANT" else _utc(row["start"]),
        interval_end=None if measurement == "STATE_AT_INSTANT" else end, family="MEASUREMENT",
        value=_value(row["value"]), unit=row["unit"], measurement=measurement, **{**common, **ids}))


def seal_readings(context: SealContext, days: Iterable[tuple[date, list[Mapping[str, Any]]]]) -> list[SealedBatch]:
    """Every batch of one Site's readings, `days` in day order and each day's rows in reading order."""
    sequences: dict[str, int] = {}
    out: list[SealedBatch] = []
    for day, rows in days:
        by_source: dict[str, list[str]] = {}
        for row in rows:
            binding = context.bindings.get((row["source_id"], row["signal_id"]))
            if binding is None:
                raise WorldSealRefused("WORLD_TELEMETRY_UNRESOLVED",
                                       f"{context.site_code} {row['source_id']}/{row['signal_id']} has no binding")
            source_id = str(binding["source_id"])
            sequence = sequences.get(source_id, 0) + 1
            sequences[source_id] = sequence
            by_source.setdefault(source_id, []).append(_envelope_text(context, row, binding, sequence))
        for source_id in sorted(by_source):
            texts = by_source[source_id]
            for n, first in enumerate(range(0, len(texts), MAX_BATCH_ENVELOPES), start=1):
                chunk = texts[first:first + MAX_BATCH_ENVELOPES]
                _, text = seal_batch_v2(
                    site_id=context.site_id, gateway_id=context.gateway_id, source_id=source_id,
                    source_mode=context.source_mode, foundation_version=context.foundation_version,
                    foundation_valid_from=context.foundation_valid_from, binding_set_id=context.binding_set_id,
                    binding_version=context.binding_version, snapshot_sha256=context.snapshot_sha256,
                    envelope_texts=chunk)
                out.append(SealedBatch(name=f"{context.site_code}.{source_id}.{day.isoformat()}.{n}.batch.json",
                                       source_id=source_id, day=day.isoformat(), count=len(chunk), text=text))
    return out
