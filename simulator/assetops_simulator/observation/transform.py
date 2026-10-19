"""Generate what each configured device published, and why it sometimes did not.

The observation transform of v4 section 6.1 phase C, as a component the kernel
composes with rather than a branch inside it. It is keyed on
`(address, device_id, signal_id)` - the address being the `addressed_key` the
whole product already keys on, which is a `StateRef`'s own spelling - so two
devices reporting one tank, and one device carrying two signals about it, are
three reporting paths and not one.

## What it is allowed to read, and what that rules out

Two arguments: the boundaries a kernel recorded, and `FrozenReportingInputs`.
There is no `FrozenWorldInputs` here and no `ModelSpec`, so nothing in this module
can move a stock, apply a bound, or run a law - and nothing the kernel is handed
carries a cadence, a bias or a dropout. `reporting-parameters-move-no-world-
quantity` is the rule; these two signatures are why it holds rather than being
remembered.

It reads a boundary's `state_samples` rather than its `stocks`, and that is not
interchangeable. A sample is what the model's `REPORTED_OBSERVATION` handler
answered at that instant, in the sampling phase and after that instant's events.
A stock the model cannot sample is not reportable at all, so reading the stock
would generate a reading out of a state nothing answered for.

## Every rule it applies is published, and it calls the published one

`sample_due_at` and `cadence_is_expressible` live in the execution contract beside
the sentences that describe them, and `draw_selects` lives in the neutral
observation contract beside the draw domain. Nothing here re-derives any of the
three. That is the T020B lesson applied to this slice: four review rounds were
spent on prose that restated a subset of what a formula did, and the formula was
right every time.

## The four reasons a due sample publishes nothing, in the order they are asked

1. the reporting path is forced unavailable across a declared window - the path is
   down, so nothing is sampled and the world carries on unobserved;
2. an interval reading is due at the run's first boundary, where no span has
   completed;
3. the sample was taken and this model measured nothing at that address in the
   span that ended;
4. the draw says this publication did not happen.

The gap is asked first because it is a fact about the path rather than about the
sample: a device on a dead line does not take a reading and then fail to send it.
Nothing about the ORDER changes which samples drop, because a draw is a function
of its own arguments and not of how many draws preceded it - so this is a
statement about what each outcome means rather than about arithmetic.
"""

from __future__ import annotations

import decimal
from dataclasses import dataclass, replace as _replace
from datetime import datetime, timedelta, timezone
from fractions import Fraction

from assetops_contracts.observation import (
    DeviceObservation,
    DeviceSignalSpec,
    FrozenReportingInputs,
    ReportedReading,
    draw_selects,
    quantize_half_even,
)
from assetops_contracts.trajectory import BoundaryState


def world_value(
    boundary: BoundaryState,
    signal: DeviceSignalSpec,
    span_minutes: int | None,
) -> Fraction | str | None:
    """The private quantity one signal would report at one boundary, or nothing.

    A `STATE_SIGNAL` reads the sample taken at this instant and an
    `INTERVAL_SIGNAL` reads the measurement for the span that ended at it. The two
    classes are the execution contract's and the asymmetry is
    `interval-signal-describes-the-preceding-interval`: at one timestamp a stock
    reading describes that instant and an interval reading describes the interval
    before it.

    An interval measurement is divided by the span it accumulated over, which is
    `an-interval-reading-is-a-mean-over-the-span`: 11.25 kWh over fifteen minutes
    is 45 kW, and that is the number a controller's power telemetry carries. The
    division is exact, so the mean of a dispatch forced at 45 kW is 45 kW and not
    44.999999999999996.

    T025b: a discrete signal reads the member the world holds at T -
    `BoundaryState.discrete`, taken after the transitions already due at T and
    before anything a request emitted at T can cause (kernel phase B). So a
    sample coinciding with a due transition observes the new member, and a
    request the controller emits at T is not observed retroactively: its effect
    is a transition at a later boundary, and that boundary's sample sees it.
    The member is returned as the text it is, never a code.
    """
    if signal.is_discrete:
        return boundary.discrete_state(signal.address)
    if signal.reading_class == "STATE_SIGNAL":
        return boundary.state_sample(signal.address)
    measured = boundary.interval_measurement(signal.address)
    if measured is None or span_minutes is None:
        return None
    return measured / Fraction(span_minutes, 60)


def _attempt(
    boundary: BoundaryState,
    signal: DeviceSignalSpec,
    reporting: FrozenReportingInputs,
    span_minutes: int | None,
) -> DeviceObservation:
    """One due sample, as what it published or as why it did not."""

    def observation(
        outcome: str,
        *,
        value: Fraction | str | None = None,
        reason: str | None = None,
    ) -> DeviceObservation:
        return DeviceObservation(
            device_id=signal.device_id,
            signal_id=signal.signal_id,
            address=signal.address,
            state_key=signal.state_key,
            reading_class=signal.reading_class,
            at_offset_minutes=boundary.offset_minutes,
            source_sample_time=boundary.simulation_time,
            outcome=outcome,
            reported_value=value,
            canonical_unit=signal.canonical_unit,
            suppression_reason=reason,
        )

    gaps = reporting.gaps_covering(signal, boundary.offset_minutes)
    if gaps:
        window = gaps[0]
        # The AUTHORED instant and the RESOLVED interval, said separately,
        # because for a POINT they differ and the sentence used to give the
        # authored one as the interval's start. A point at offset 1490 in a
        # fifteen-minute run suppresses the sample at 1485, and the explanation
        # for that row read "unavailable from offset 1490" - a span that does not
        # contain the row it was explaining. A reader can only reconcile that by
        # already knowing the containing-step rule, which is the thing the
        # sentence was supposed to tell them.
        resolved = (
            f"offset {window.start_offset_minutes} up to but not including "
            f"{window.end_offset_minutes}"
        )
        if window.start_offset_minutes == window.offset_minutes:
            placement = f"declared at offset {window.offset_minutes}"
        else:
            placement = (
                f"declared at offset {window.offset_minutes}, which falls in "
                f"the step covering {resolved}"
            )
        return observation(
            "SUPPRESSED_BY_GAP",
            reason=(
                f"{window.event_id} forces {window.condition_address} "
                f"unavailable across {resolved} - {placement} - so this signal "
                "took no sample here."
            ),
        )

    if (
        signal.reading_class == "INTERVAL_SIGNAL"
        and not boundary.has_preceding_interval
    ):
        return observation(
            "NO_PRECEDING_INTERVAL",
            reason=(
                "No interval has completed at this instant, so there is no span "
                f"for {signal.signal_id} to summarise."
            ),
        )

    value = world_value(boundary, signal, span_minutes)
    if value is None:
        return observation(
            "NO_VALUE_AT_BOUNDARY",
            reason=(
                f"This model produced no {signal.reading_class} for "
                f"{signal.address} at this instant, so the sample had nothing "
                "to read."
            ),
        )

    # v4 section 9.2's identity: seed, stream name, step index, ordinal. The
    # stream name already identifies the signal - `dropout:<device>:<signal>`,
    # which is the shape of the specification's own `sensor-noise:TANK-001:level`
    # - so the address is not a field of the draw, and since this function was
    # last reviewed there is nowhere to pass one.
    #
    # The ordinal is zero because this mechanism makes exactly one draw per
    # stream per step. A second draw at one step would be one.
    if draw_selects(
        reporting.seed,
        signal.dropout_stream,
        signal.dropout_per_thousand,
        boundary.step_index,
    ):
        return observation(
            "DROPPED",
            reason=(
                f"{signal.dropout_per_thousand} in a thousand of this signal's "
                "due samples do not publish, and the draw for this instant "
                "selected it."
            ),
        )

    if isinstance(value, str):
        # A discrete member is reported as is: the spec refused any bias.
        return observation("REPORTED", value=value)
    published = value + signal.bias
    if signal.resolution is not None:
        # S2-01b: the simulated device publishes at its declared resolution,
        # rounded once, exactly and half-to-even, after its modeled bias. The
        # exact world value never leaves the kernel; only this reading does.
        published = quantize_half_even(published, signal.resolution)
    return observation("REPORTED", value=published)


def generate_observations(
    boundaries: tuple[BoundaryState, ...], reporting: FrozenReportingInputs
) -> tuple[DeviceObservation, ...]:
    """Every sample attempt across the boundaries so far, in order.

    Ordered by instant and then by the order the publication profile declares its
    signals in, so the series is a function of the content rather than of a
    dictionary's iteration. That is what lets `observation_series_digest` be
    compared between two executions at all.

    Safe to call mid-flight, and called mid-flight by the Lab: the boundaries a
    run has reached are the boundaries there are readings for, and a transform
    that needed a finished trajectory would make a stepped run unobservable.

    Raises:
        ReportingResolutionUnrepresentable: a declared cadence is not a whole
            multiple of the run's timestep, so some sample would be due between
            two boundaries.
    """
    reporting.refuse_a_cadence_the_run_cannot_express()
    attempts: list[DeviceObservation] = []
    previous_offset: int | None = None
    for boundary in boundaries:
        # The span that ended at this boundary, read off the boundaries rather
        # than assumed to be the timestep. The last step of an interval the
        # timestep does not divide is shorter than the rest, and a mean taken over
        # the timestep there would be a number divided by a span it did not cover.
        span = (
            None
            if previous_offset is None
            else boundary.offset_minutes - previous_offset
        )
        for signal in reporting.signals:
            if signal.due_at(boundary.offset_minutes):
                attempts.append(_attempt(boundary, signal, reporting, span))
        previous_offset = boundary.offset_minutes
    return tuple(attempts)


def reported_reading(
    observations: tuple[DeviceObservation, ...],
    signal: DeviceSignalSpec,
    at_offset_minutes: int,
) -> ReportedReading:
    """What a consumer of one signal sees at one instant.

    `a-retained-reading-carries-its-own-time` in full. The newest published
    reading at or before this instant is shown with ITS source time, marked `GOOD`
    when that instant is this one and `STALE` when it is earlier. Nothing is
    restamped, nothing is interpolated, and where no reading has ever been
    published the value is `UNAVAILABLE` - which is a different statement from
    stale and is kept as one.

    Computed from the reading series and nothing else. A consumer that could reach
    the world to fill a gap would not be a consumer of readings.
    """
    mine = [
        item
        for item in observations
        if item.key == signal.key and item.at_offset_minutes <= at_offset_minutes
    ]
    attempt = next(
        (item for item in mine if item.at_offset_minutes == at_offset_minutes),
        None,
    )
    published = [item for item in mine if item.outcome == "REPORTED"]
    # By the newest instant rather than by position in the series. The series is
    # already in instant order, and relying on that would make this function's
    # correctness depend on another function's iteration.
    freshest = (
        max(published, key=lambda item: item.at_offset_minutes)
        if published
        else None
    )

    if freshest is None:
        quality = "UNAVAILABLE"
    elif freshest.at_offset_minutes == at_offset_minutes:
        quality = "GOOD"
    else:
        quality = "STALE"

    return ReportedReading(
        address=signal.address,
        device_id=signal.device_id,
        signal_id=signal.signal_id,
        reading_class=signal.reading_class,
        at_offset_minutes=at_offset_minutes,
        value=None if freshest is None else freshest.reported_value,
        source_sample_time=(
            None if freshest is None else freshest.source_sample_time
        ),
        source_offset_minutes=(
            None if freshest is None else freshest.at_offset_minutes
        ),
        quality=quality,
        due=signal.due_at(at_offset_minutes),
        outcome=None if attempt is None else attempt.outcome,
        suppression_reason=None if attempt is None else attempt.suppression_reason,
    )


def outcome_counts(
    observations: tuple[DeviceObservation, ...]
) -> dict[str, int]:
    """How many sample attempts reached each outcome.

    Counted rather than asserted, because "the gap suppressed something" is the
    claim, and a count of zero is what a suppression that never happened looks
    like. A screen showing these numbers is showing whether the mechanism did
    anything at all.
    """
    counts: dict[str, int] = {}
    for item in observations:
        counts[item.outcome] = counts.get(item.outcome, 0) + 1
    return counts


# --- cold-observation/1 (W2-02) ------------------------------------------------------------------------------
#
# A separate, closed transform for the standalone cold pack: it reads only the pack's public records and the
# frozen scenario's observation rows, never the pack state. Zero bias, half-even 0.1 degC quantization, a fixed
# +3 second publication latency. DROP removes the probe report at that instant; HOLD keeps the report's source
# time and publishes it at `release_at`; ADD creates a second GOOD controller START_RESULT (outcome SUCCEEDED)
# with a distinct transition ordinal and the attempt's correlation, without touching physical state.

COLD_OBSERVATION_PROFILE = ("cold-observation", 1)
COLD_BIAS_DEG_C = Fraction(0)
COLD_LATENCY_SECONDS = 3
_TENTH = decimal.Decimal("0.1")


@dataclass(frozen=True)
class ColdObservation:
    """One public cold report before its gateway v2 serialization: the pack record plus public text/timing."""

    record: object  # assetops_simulator.packs.cold.PublicRecord
    value_text: str | None
    published_at: datetime
    transition_ordinal: int | None
    held: bool = False
    added: bool = False


def cold_value_text(value: object, unit: str | None) -> str | None:
    """Canonical public text: degC half-even to 0.1 after the zero bias; kW exact; a state member as is."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if unit == "degC":
        with decimal.localcontext() as ctx:
            ctx.prec = 60
            biased = value + COLD_BIAS_DEG_C
            exact = decimal.Decimal(biased.numerator) / decimal.Decimal(biased.denominator)
            q = exact.quantize(_TENTH, rounding=decimal.ROUND_HALF_EVEN)
    else:
        q = decimal.Decimal(value.numerator) / decimal.Decimal(value.denominator)
        if Fraction(q) != value:
            raise ValueError(f"{value} {unit} has no exact decimal text")
    text = format(q.normalize(), "f")
    return "0" if text in ("-0", "0") else text


def cold_observations(records: tuple, observations: tuple = ()) -> tuple[ColdObservation, ...]:
    """Apply `cold-observation/1` to the pack's public records and the scenario's observation rows.

    `observations` rows carry `at`, `kind`, `device_id`, `action`, `outcome`, `release_at` (datetimes for the
    instants), as the strict cold scenario parser produced them.
    """
    latency = timedelta(seconds=COLD_LATENCY_SECONDS)
    drops = {o.at for o in observations if o.kind == "PROBE_REPORT" and o.action == "DROP"}
    holds = {o.at: o.release_at for o in observations if o.kind == "PROBE_REPORT" and o.action == "HOLD"}
    out: list[ColdObservation] = []
    for r in records:
        if r.device_id == "chamber-probe":
            if r.source_time in drops:
                continue
            if r.source_time in holds:
                out.append(ColdObservation(r, cold_value_text(r.value, r.unit), holds[r.source_time],
                                           r.transition_ordinal, held=True))
                continue
        out.append(ColdObservation(r, cold_value_text(r.value, r.unit), r.source_time + latency,
                                   r.transition_ordinal))
    for o in observations:
        if o.kind != "START_RESULT" or o.action != "ADD":
            continue
        channel = [r for r in records if r.device_id == "generator-controller" and r.signal_id == "start-event"]
        prior = [r for r in channel if r.source_time <= o.at]
        if not prior:
            raise ValueError(f"an added START_RESULT at {o.at} has no attempt to correlate with")
        ordinal = max(r.transition_ordinal for r in channel) + 1 + sum(
            1 for x in out if x.added)
        added = _replace(prior[-1], source_time=o.at, record_kind="START_RESULT", outcome=o.outcome,
                         transition_ordinal=ordinal)
        out.append(ColdObservation(added, None, o.at + latency, ordinal, added=True))
    out.sort(key=lambda x: (x.published_at, x.record.source_time, x.record.device_id, x.record.signal_id,
                            x.transition_ordinal or 0))
    return tuple(out)


# --- ev-publication/1 and ev-observation/1 (W2-05b) ------------------------------------------------------------
#
# A closed public transform for the `ev-charger/1` pack (`D-2026-10-18-w2-05-buildspec` commit 3). It reads only
# the pack's boundary documents and emitted events plus the scenario's observation rows; private requests,
# forcing and the oracle never leave it except as the mapped observed channels. Device/signal IDs and the bound
# connector asset are inputs from the effective binding, never constructed here.
#
# - Connector state at every boundary (61 for one hour, closing boundary included), one per connector per
#   boundary: transitions at one instant collapse into the boundary's observed state.
# - Session START/END/ABORT and connector FAULT/CLEAR at their boundary, with the scoped session token.
# - Connector energy `INTERVAL_DELTA` on aligned five-minute half-open slots, split at the connector's session
#   boundaries, only for started-session subintervals (zero while a started session pauses): cumulative kWh is
#   rounded half-even to 0.001 at both ends before differencing.
# - Connector power, requested power, allocated limit and Site import `INTERVAL_MEAN` on the same slots, split
#   at session boundaries (the connector's for connector channels, any connector's for Site import).
# - `published_at = source_time + 3 s`. `ev-observation/1`: DROP removes an energy report after it is built
#   (its 300 s stay unknown); HOLD keeps source time, ordinal and identity and publishes at `release_at`; ADD
#   creates a distinct GOOD `EV_SESSION_END` for the active scoped session on the next session-event ordinal.

_UTC = timezone.utc
EV_PUBLICATION_PROFILE = ("ev-publication", 1)
EV_OBSERVATION_PROFILE = ("ev-observation", 1)
EV_LATENCY_SECONDS = 3
EV_SLOT = timedelta(minutes=5)
_MILLI = decimal.Decimal("0.001")
#: The logical connector channels of `simulator-lab-gateway-ev/1`, in the commit 3 equal-time order.
EV_CONNECTOR_CHANNELS = ("state", "session-event", "fault-event", "energy", "power", "requested-power",
                         "allocated-limit")
EV_SITE_CHANNEL = "import"
_EV_CHANNEL_RANK = {name: rank for rank, name in enumerate(EV_CONNECTOR_CHANNELS + (EV_SITE_CHANNEL,))}
_EV_SESSION_KIND = {"START": ("EV_SESSION_START", "STARTED"), "END": ("EV_SESSION_END", "COMPLETED"),
                    "ABORT": ("EV_SESSION_ABORT", "ABORTED")}
_EV_FAULT_KIND = {"FAULT": ("EV_CONNECTOR_FAULT", "FAULTED"), "CLEAR": ("EV_CONNECTOR_CLEAR", "CLEARED")}
#: The private mean source of each connector mean channel (connector power is the allocated draw).
_EV_MEAN_KEYS = (("power", "allocated_kw"), ("requested-power", "requested_kw"), ("allocated-limit", "allocated_kw"))


@dataclass(frozen=True)
class EvChannel:
    """One bound public channel: the binding's device/signal and the bound connector asset (None for the Site)."""

    device_id: str
    signal_id: str
    connector_id: str | None


@dataclass(frozen=True)
class EvPublicRecord:
    """One public EV report before its gateway v2 serialization. `connector` is the pack connector (`c1`/`c2`)
    or None for the Site meter; `channel` a logical channel name; `transition_ordinal` is one-based per channel."""

    connector: str | None
    channel: str
    device_id: str
    signal_id: str
    source_time: datetime
    family: str
    measurement: str | None
    interval_start: datetime | None
    value: str | None
    unit: str | None
    record_kind: str | None
    outcome: str | None
    session_id: str | None
    connector_id: str | None
    component_id: str | None
    transition_ordinal: int
    published_at: datetime
    held: bool = False
    added: bool = False
    #: q3 Q16: a FAULT/CLEAR without an active session correlates with its fault episode, named here as
    #: `(bound connector asset_code, zero-based count of actual FAULT transitions on it)`; the report mapping
    #: hashes it with the scenario SHA. None for every other record, and for a FAULT/CLEAR that carries S.
    fault_episode: tuple[str, int] | None = None


def ev_decimal_text(value: Fraction) -> str:
    """Canonical public decimal of an exact value; a value without a finite decimal is refused."""
    with decimal.localcontext() as ctx:
        ctx.prec = 60
        q = decimal.Decimal(value.numerator) / decimal.Decimal(value.denominator)
    if Fraction(q) != value:
        raise ValueError(f"{value} has no exact decimal text")
    text = format(q.normalize(), "f")
    return "0" if text in ("-0", "0") else text


def ev_rounded_kwh(value: Fraction) -> decimal.Decimal:
    """Cumulative kWh rounded half-even to 0.001 (the meter bound at each boundary)."""
    with decimal.localcontext() as ctx:
        ctx.prec = 60
        exact = decimal.Decimal(value.numerator) / decimal.Decimal(value.denominator)
        return exact.quantize(_MILLI, rounding=decimal.ROUND_HALF_EVEN)


def _ev_at(text: str) -> datetime:
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=_UTC)


def _ev_split(start: datetime, end: datetime, cuts: set) -> list[tuple[datetime, datetime]]:
    points = [start] + sorted(c for c in cuts if start < c < end) + [end]
    return list(zip(points, points[1:]))


def _ev_mean(boundaries: list[datetime], a: datetime, b: datetime, value) -> Fraction:
    """The exact time mean over `[a, b)` of a value constant across each minute `[boundary, next)`."""
    ia, ib = boundaries.index(a), boundaries.index(b)
    return sum((value(i) for i in range(ia, ib)), Fraction(0)) / (ib - ia)


def ev_public_records(
    run: object,
    *,
    channels: dict,
    observations: tuple = (),
) -> tuple[EvPublicRecord, ...]:
    """Apply `ev-publication/1` and `ev-observation/1` to one `EvRun`.

    `run` is `assetops_simulator.packs.ev_charger.EvRun`; its boundary documents are one minute apart, the last
    the closing snapshot. `channels` maps `(connector, channel)` (and `(None, "import")`) to the bound
    `EvChannel`. `observations` rows carry `time`, `kind`, `connector`, `action`, `release_at` (datetimes).
    Returns the series in the commit 3 order: source time, connector (c1, c2, then the Site), channel rank,
    per-channel ordinal.
    """
    documents = run.documents
    if len(documents) < 2:
        raise ValueError("an EV run has at least one minute and its closing boundary")
    boundaries = [_ev_at(d["boundary"]) for d in documents]
    start, end = boundaries[0], boundaries[-1]
    connectors = tuple(c["connector"] for c in documents[0]["connectors"])
    latency = timedelta(seconds=EV_LATENCY_SECONDS)
    ordinals: dict = {}
    built: list[EvPublicRecord] = []

    def bound(connector, name: str) -> EvChannel:
        try:
            return channels[(connector, name)]
        except KeyError:
            raise ValueError(f"no bound channel for {connector}/{name}") from None

    def emit(connector, name: str, source_time: datetime, **fields) -> EvPublicRecord:
        b = bound(connector, name)
        ordinal = ordinals.get((connector, name), 0) + 1
        ordinals[(connector, name)] = ordinal
        values = {"family": "MEASUREMENT", "measurement": None, "interval_start": None, "value": None,
                  "unit": None, "record_kind": None, "outcome": None, "session_id": None, "connector_id": None,
                  "component_id": None}
        values.update(fields)
        record = EvPublicRecord(connector=connector, channel=name, device_id=b.device_id, signal_id=b.signal_id,
                                source_time=source_time, transition_ordinal=ordinal,
                                published_at=source_time + latency, **values)
        built.append(record)
        return record

    def doc(index: int, connector: str) -> dict:
        return next(c for c in documents[index]["connectors"] if c["connector"] == connector)

    # Started-session spans per connector: [start boundary, terminal boundary or None, session token].
    spans: dict = {c: [] for c in connectors}
    for event in run.events:
        if event.kind == "START":
            spans[event.connector].append([event.at, None, event.session_id])
        elif event.kind in ("END", "ABORT"):
            open_spans = [s for s in spans[event.connector] if s[2] == event.session_id and s[1] is None]
            if not open_spans:
                raise ValueError(f"{event.kind} at {event.at} closes no started session")
            open_spans[0][1] = event.at
    cuts = {c: {t for span in spans[c] for t in span[:2] if t is not None} for c in connectors}
    all_cuts = set().union(*cuts.values())

    fault_counts: dict = {c: 0 for c in connectors}
    latched_episode: dict = {}
    events_at: dict = {}
    for event in run.events:
        events_at.setdefault(event.at, []).append(event)
    for index, at in enumerate(boundaries):
        for connector in connectors:
            emit(connector, "state", at, measurement="STATE_AT_INSTANT", value=doc(index, connector)["state"],
                 unit="state")
            for event in events_at.get(at, ()):
                if event.connector != connector:
                    continue
                if event.kind in _EV_SESSION_KIND:
                    (kind, outcome), name = _EV_SESSION_KIND[event.kind], "session-event"
                elif event.kind in _EV_FAULT_KIND:
                    (kind, outcome), name = _EV_FAULT_KIND[event.kind], "fault-event"
                else:
                    raise ValueError(f"{event.kind} is not an ev-charger/1 event")
                asset = bound(connector, name).connector_id
                episode = None
                if event.kind == "FAULT":
                    # q3 Q16: every actual FAULT transition opens an episode; the ordinal counts them per connector.
                    latched_episode[connector] = (asset, fault_counts[connector])
                    fault_counts[connector] += 1
                if event.kind in _EV_FAULT_KIND and event.session_id is None:
                    if connector not in latched_episode:
                        raise ValueError(f"{event.kind} at {event.at} on {connector} follows no FAULT")
                    episode = latched_episode[connector]
                emit(connector, name, at, family="EVENT", record_kind=kind, outcome=outcome,
                     session_id=event.session_id, connector_id=asset, component_id=asset, fault_episode=episode)

    slot_start = start
    while slot_start < end:
        slot_end = min(slot_start + EV_SLOT, end)
        for connector in connectors:
            asset = bound(connector, "energy").connector_id
            for a, b in _ev_split(slot_start, slot_end, cuts[connector]):
                for span_start, span_end, session in spans[connector]:
                    if span_start <= a and (span_end is None or b <= span_end):
                        before = Fraction(doc(boundaries.index(a), connector)["energy_kwh"])
                        after = Fraction(doc(boundaries.index(b), connector)["energy_kwh"])
                        delta = ev_rounded_kwh(after) - ev_rounded_kwh(before)
                        if delta < 0:
                            raise ValueError(f"{connector} energy decreases over [{a}, {b})")
                        emit(connector, "energy", b, measurement="INTERVAL_DELTA", interval_start=a,
                             value=ev_decimal_text(Fraction(delta)), unit="kWh", session_id=session,
                             connector_id=asset)
        for connector in connectors:
            for name, key in _EV_MEAN_KEYS:
                for a, b in _ev_split(slot_start, slot_end, cuts[connector]):
                    mean = _ev_mean(boundaries, a, b, lambda i, c=connector, k=key: Fraction(doc(i, c)[k]))
                    emit(connector, name, b, measurement="INTERVAL_MEAN", interval_start=a, unit="kW",
                         value=ev_decimal_text(mean))
        for a, b in _ev_split(slot_start, slot_end, all_cuts):
            mean = _ev_mean(boundaries, a, b, lambda i: Fraction(documents[i]["site_import_kw"]))
            emit(None, EV_SITE_CHANNEL, b, measurement="INTERVAL_MEAN", interval_start=a, unit="kW",
                 value=ev_decimal_text(mean))
        slot_start = slot_end

    # ev-observation/1: public reports only, never the world.
    drops = {(o.time, o.connector) for o in observations if o.kind == "ENERGY_REPORT" and o.action == "DROP"}
    holds = {(o.time, o.connector): o.release_at for o in observations
             if o.kind == "EV_SESSION_END" and o.action == "HOLD"}
    used: set = set()
    out: list[EvPublicRecord] = []
    for record in list(built):
        key = (record.source_time, record.connector)
        if record.channel == "energy" and key in drops:
            used.add(("DROP",) + key)
            continue
        if record.channel == "session-event" and record.record_kind == "EV_SESSION_END" and key in holds:
            used.add(("HOLD",) + key)
            out.append(_replace(record, published_at=holds[key], held=True))
            continue
        out.append(record)
    for o in observations:
        if o.action in ("DROP", "HOLD"):
            if (o.action, o.time, o.connector) not in used:
                raise ValueError(f"{o.action} {o.kind} at {o.time} on {o.connector} matches no public report")
            continue
        if o.kind != "EV_SESSION_END" or o.action != "ADD":
            raise ValueError(f"{o.kind}/{o.action} is not an ev-observation/1 row")
        if o.time not in boundaries:
            raise ValueError(f"an added EV_SESSION_END at {o.time} is not on a boundary")
        session = doc(boundaries.index(o.time), o.connector)["session_id"]
        if session is None:
            raise ValueError(f"an added EV_SESSION_END at {o.time} on {o.connector} has no active session")
        asset = bound(o.connector, "session-event").connector_id
        added = emit(o.connector, "session-event", o.time, family="EVENT", record_kind="EV_SESSION_END",
                     outcome="COMPLETED", session_id=session, connector_id=asset, component_id=asset)
        out.append(_replace(added, added=True))
    rank = {c: i for i, c in enumerate(connectors)}
    out.sort(key=lambda r: (r.source_time, rank.get(r.connector, len(connectors)), _EV_CHANNEL_RANK[r.channel],
                            r.transition_ordinal))
    return tuple(out)
