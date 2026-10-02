"""The record transform: which policy and override records occurred, and which published.

The record half of the observation transform (T026). It reads the boundaries a
run has reached - only to know how far the run has got, never a stock, a flow or
an intent - and `FrozenRecordInputs`. A record whose occurrence instant the run
has not reached has not occurred yet and is not returned, so a stepped run's
records grow as its readings do and a retry republishes the same ones.

Policy records occur at the run's first boundary: that is when the gateway first
reports the configuration the controller runs under. Their effective start is
the Foundation's validity start, which may lie before the run - a future or past
effective time is a field, not the key. An override occurs at its window start.

A gap on a record's channel suppresses it; a delay is the gateway's to apply and
does not change what occurred or when.
"""

from __future__ import annotations

from assetops_contracts.operational_records import (
    FrozenRecordInputs,
    RecordObservation,
    offset_instant,
)
from assetops_contracts.trajectory import BoundaryState


def _outcome(
    inputs: FrozenRecordInputs, device_id: str, signal_id: str, offset: int
) -> tuple[str, str | None]:
    for gap in inputs.gaps:
        if (gap.device_id, gap.signal_id) == (device_id, signal_id) and gap.covers(
            offset
        ):
            return "SUPPRESSED_BY_GAP", gap.event_id
    return "REPORTED", None


def generate_records(
    boundaries: tuple[BoundaryState, ...], inputs: FrozenRecordInputs
) -> tuple[RecordObservation, ...]:
    """Every record that has occurred by the last boundary reached, in order.

    Ordered by occurrence and then by declaration order (policies first), so the
    series is a function of the content alone.
    """
    if not boundaries:
        return ()
    reached = boundaries[-1].offset_minutes
    records: list[tuple[int, int, RecordObservation]] = []
    for index, policy in enumerate(inputs.policies):
        outcome, event = _outcome(inputs, policy.device_id, policy.signal_id, 0)
        records.append(
            (
                0,
                index,
                RecordObservation(
                    family="POLICY",
                    device_id=policy.device_id,
                    signal_id=policy.signal_id,
                    at_offset_minutes=0,
                    source_time=offset_instant(inputs.interval, 0),
                    outcome=outcome,
                    control=policy.control,
                    component_id=policy.component_id,
                    value=policy.value,
                    members=policy.members,
                    unit=policy.unit,
                    effective_start=policy.effective_start,
                    effective_end=None,
                    policy_version=policy.policy_version,
                    policy_source=policy.policy_source,
                    event_id=event,
                ),
            )
        )
    for index, command in enumerate(inputs.overrides):
        at = command.occurrence_offset_minutes
        if at > reached:
            continue
        outcome, event = _outcome(inputs, command.device_id, command.signal_id, at)
        records.append(
            (
                at,
                len(inputs.policies) + index,
                RecordObservation(
                    family="OPERATIONAL_RECORD",
                    device_id=command.device_id,
                    signal_id=command.signal_id,
                    at_offset_minutes=at,
                    source_time=offset_instant(inputs.interval, at),
                    outcome=outcome,
                    control=command.control,
                    component_id=command.component_id,
                    value=command.value,
                    members=None,
                    unit=command.unit,
                    effective_start=offset_instant(
                        inputs.interval, command.effective_start_offset_minutes
                    ),
                    effective_end=(
                        None
                        if command.effective_end_offset_minutes is None
                        else offset_instant(
                            inputs.interval, command.effective_end_offset_minutes
                        )
                    ),
                    record_kind="OVERRIDE_COMMAND",
                    actor=command.actor,
                    event_id=event or command.event_id,
                ),
            )
        )
    records.sort(key=lambda item: (item[0], item[1]))
    return tuple(item[2] for item in records)
