"""Generated device observations to canonical source envelopes.

What this is handed is the whole of what it can see: the reading series the
observation transform produced, the frozen mapping, the run's interval, and the
three publication identities the Draft froze. No world state, no trajectory, no
projection and no scenario - so there is no private value this function could
copy into an envelope even by mistake. It reads a `DeviceObservation`, which by
its own construction carries no true value.

## What is published, and what is not

- a `REPORTED` sample on an allowlisted signal is a `GOOD` envelope carrying the
  reported value - bias included, because that is what the device said;
- a sample that was TAKEN and had nothing to read - no completed interval, or no
  measurement - is an `UNAVAILABLE` envelope with a closed reason, and only on a
  signal whose mapping says it publishes unavailability;
- a sample that was never taken (`SUPPRESSED_BY_GAP`) or never arrived
  (`DROPPED`) publishes nothing. There is no envelope for a message that did not
  exist, and in particular no value is invented to fill the gap;
- a signal not on the allowlist publishes nothing at all.

The sentence that explains a suppression names the scenario's event, and it is
never copied: an envelope has no field it could go in.

## Identity and order

The message id is derived from the publication identity (`envelope_message_id`),
so republishing the same series yields the same ids - a retry is recognisable as
one. `sequence` counts one signal's publications from one, in source-time order,
so it too is a function of the series and not of how often it was published.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from assetops_contracts.observation import DeviceObservation
from assetops_contracts.source_envelope import (
    EnvelopeRejected,
    SourceEnvelope,
    SourceMappingSet,
    envelope_message_id,
    instant_text,
    refuse_an_enum_under_schema_1,
)
from assetops_contracts.world_inputs import FrozenInterval

#: The transform's reading classes, in wire terms.
MEASUREMENT_OF_READING_CLASS = {
    "STATE_SIGNAL": "STATE_AT_INSTANT",
    "INTERVAL_SIGNAL": "INTERVAL_MEAN",
}

#: Sample outcomes that published nothing, because nothing was published.
NOT_PUBLISHED = frozenset({"SUPPRESSED_BY_GAP", "DROPPED"})

#: Sample outcomes that published a typed absence, and the closed reason each is.
UNAVAILABLE_REASON_OF_OUTCOME = {
    "NO_PRECEDING_INTERVAL": "NO_COMPLETED_INTERVAL",
    "NO_VALUE_AT_BOUNDARY": "NO_MEASUREMENT",
}


def _parse(instant: str) -> datetime:
    return datetime.strptime(instant, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )


def _span_start(interval: FrozenInterval, at_offset_minutes: int) -> str | None:
    """The instant the span ending at this boundary began, or none at the first.

    Read off the interval's own boundaries rather than assumed to be one
    timestep, because the last step of an interval the timestep does not divide
    is shorter than the rest.
    """
    previous = [
        offset for offset in interval.boundaries if offset < at_offset_minutes
    ]
    if not previous:
        return None
    return instant_text(
        _parse(interval.start_time) + timedelta(minutes=previous[-1])
    )


def publish(
    observations: tuple[DeviceObservation, ...],
    mapping: SourceMappingSet,
    interval: FrozenInterval,
    *,
    site_id: str,
    source_id: str,
    gateway_id: str,
) -> tuple[SourceEnvelope, ...]:
    """Every envelope the gateway publishes for a reading series, in order.

    Raises:
        EnvelopeRejected: an allowlisted signal's observation disagrees with its
            mapping about the measurement class or the unit, or something that
            is not a `DeviceObservation` was handed in. The gateway refuses to
            publish it rather than relabel it.
    """
    sequences: dict[tuple[str, str], int] = {}
    published: list[SourceEnvelope] = []
    for item in observations:
        if type(item) is not DeviceObservation:
            raise EnvelopeRejected(
                "NOT_AN_ENVELOPE",
                "envelope",
                "the gateway converts DeviceObservation records and nothing "
                f"else, not {type(item).__name__}",
            )
        entry = mapping.entry(item.device_id, item.signal_id)
        if entry is None or item.outcome in NOT_PUBLISHED:
            continue
        # T025b: an allowlisted enum signal is refused, not converted - schema
        # 1 has no way to carry `RUNNING` - whatever unit the entry claims.
        refuse_an_enum_under_schema_1(
            item.device_id, item.signal_id, item.canonical_unit
        )
        measurement = MEASUREMENT_OF_READING_CLASS[item.reading_class]
        if measurement != entry.measurement:
            raise EnvelopeRejected(
                "MAPPING_INCOMPATIBLE",
                "payload.measurement",
                f"{item.device_id}/{item.signal_id} produced a "
                f"{item.reading_class} and is mapped as {entry.measurement}",
            )
        if item.canonical_unit != entry.unit:
            raise EnvelopeRejected(
                "UNIT_INCOMPATIBLE",
                "payload.unit",
                f"{item.device_id}/{item.signal_id} reports in "
                f"{item.canonical_unit!r} and is mapped as {entry.unit!r}",
            )

        if item.outcome == "REPORTED":
            quality, value, reason = "GOOD", item.reported_value, None
        else:
            if not entry.publishes_unavailable:
                continue
            quality, value = "UNAVAILABLE", None
            reason = UNAVAILABLE_REASON_OF_OUTCOME[item.outcome]

        if measurement == "INTERVAL_MEAN" and reason != "NO_COMPLETED_INTERVAL":
            interval_start = _span_start(interval, item.at_offset_minutes)
            interval_end = item.source_sample_time
        else:
            interval_start = interval_end = None

        key = (item.device_id, item.signal_id)
        sequences[key] = sequences.get(key, 0) + 1
        published.append(
            SourceEnvelope(
                message_id=envelope_message_id(
                    site_id=site_id,
                    gateway_id=gateway_id,
                    source_id=source_id,
                    device_id=item.device_id,
                    signal_id=item.signal_id,
                    source_time=item.source_sample_time,
                ),
                sequence=sequences[key],
                site_id=site_id,
                source_id=source_id,
                gateway_id=gateway_id,
                device_id=item.device_id,
                signal_id=item.signal_id,
                mapping_set_id=mapping.mapping_set_id,
                mapping_version=mapping.mapping_version,
                source_time=item.source_sample_time,
                published_at=instant_text(
                    _parse(item.source_sample_time)
                    + timedelta(seconds=mapping.publication_latency_seconds)
                ),
                measurement=measurement,
                value=value,
                unit=entry.unit,
                quality=quality,
                unavailable_reason=reason,
                interval_start=interval_start,
                interval_end=interval_end,
            )
        )
    return tuple(published)
