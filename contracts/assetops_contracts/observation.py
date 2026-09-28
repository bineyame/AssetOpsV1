"""What a device reports, as a record that cannot know what was true.

The reporting path, in terms neither side of the barrier owns. The kernel
produces a `PrivateTrajectory`: the actual stock at every boundary and the
interval measurements for every span that ended at one. None of that is a
reading. A reading is what a named device on a named signal published at a
named instant, and this module is the vocabulary for one.

## A `DeviceObservation` carries no truth, and that is the whole seam

There is no `true_value` field below, deliberately, and it is the same
structural argument `FrozenWorldInputs` makes one direction along. A device
cannot know the quantity it is measuring; it knows what it reported. A record
that carried both would let a consumer read the truth off a reading, which is
exactly the confusion the Lab exists to make visible rather than to commit.

Pairing the two is the Lab's business and nothing else's, which is why
`LabProjection` in `lab_projection.py` is the only record where a true value and
a reported value sit in one row - gated, private, and never product input.

## The reasons there is no fresh reading, kept apart

`SAMPLE_OUTCOMES` distinguishes them because they are different facts and a
consumer that merged them would lose the scenario:

- `SUPPRESSED_BY_GAP` - the reporting path was forced unavailable across a
  declared window, so nothing was sampled. The world carried on.
- `DROPPED` - the path was up, the sample was due, and the publication did not
  happen. Drawn, not decided: see the draw contract below.
- `NO_PRECEDING_INTERVAL` - an interval reading at the run's first boundary,
  where no span has completed. `no-interval-signal-at-the-first-boundary` in the
  execution contract is the rule; this is its outcome.
- `NO_VALUE_AT_BOUNDARY` - a span ended and this model measured nothing in it.
  The `BoundaryState` docstring already separates that from "no span ended";
  this keeps the separation on the reporting side.

`REPORTED` is the fifth and is the only one carrying a number.

## The draw contract, and why the stream name is inside the payload

v4 section 9 reserves `assetops-sim-rng-v1` for stochastic draws and separates
it from the identity domain. `identity.py` deliberately did not spell it,
because a domain constant with no consumer is a promise; the first consumer is
the dropout below, so it is spelled here.

A draw is a pure function of the run's seed, a stream name, the step index and
the draw's ordinal within that step - the five fields v4 section 9.2 names, in
the order it names them, and never of how many draws came before it. That is
what makes "adding an unrelated stream changes no existing stream" a structural
property rather than a hope about call order: a new stream has a different stream
name in its payload, so it produces a different set of digests and touches none
of the old ones. A sequential generator would have made the same claim false the
moment a second mechanism drew from it.

`draw_fraction` takes those fields and nothing else. It is not a variadic helper
a caller can hand whatever locates a draw in its own terms, because that is what
it was when it first went to review and what the caller then supplied was an
address and an offset in minutes - deterministic, domain-separated, and a
different contract from the specified one.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from fractions import Fraction

from assetops_contracts.execution_contract import (
    cadence_is_expressible,
    sample_due_at,
)
from assetops_contracts.identity import canonical_payload, identity_digest
from assetops_contracts.world_inputs import ENTRY_SHAPES, FrozenInterval

#: The domain separator every stochastic draw in this product carries, kept
#: apart from `IDENTITY_DOMAIN` so a draw and an identity of the same fields
#: cannot collide. v4 section 9.
RNG_DOMAIN = "assetops-sim-rng-v1"

#: A draw is a 256-bit integer read as a fraction of this. Exact: the draw is a
#: rational and is compared against a rational threshold, so no float decides
#: whether a reading was published.
DRAW_DENOMINATOR = 2**256

#: What happened when a sample was due. Five, and the module docstring says why
#: the four non-reporting ones are not one.
SAMPLE_OUTCOMES = frozenset(
    {
        "REPORTED",
        "SUPPRESSED_BY_GAP",
        "DROPPED",
        "NO_PRECEDING_INTERVAL",
        "NO_VALUE_AT_BOUNDARY",
    }
)

#: What a reader is looking at, at one instant, for one signal.
#:
#: `STALE` is the one that has to exist. A retained last reading is neither a
#: fresh reading nor an absence: it is a real number, published at a real
#: instant, that no longer describes now. A screen showing it without saying so
#: would be stating the world's present value as something a device said some
#: time ago.
READING_QUALITIES = frozenset({"GOOD", "STALE", "UNAVAILABLE"})

#: Which trajectory record a signal reads. The execution contract's
#: `READING_CLASSES` has a third member, `CONTROLLER_INPUT`, and it is absent
#: here on purpose: a controller's view is not published, so no device signal
#: may be declared for it.
REPORTABLE_READING_CLASSES = frozenset({"STATE_SIGNAL", "INTERVAL_SIGNAL"})


class ReportingResolutionUnrepresentable(Exception):
    """A declared cadence cannot be expressed at the run's timestep.

    A sample is due at an INSTANT, and the only instants an execution has are
    its boundaries. A cadence that is not a whole multiple of the timestep would
    be due between two of them, and the two ways to cope with that are both
    lies: moving the sample to the nearest boundary reports a value at a time it
    was not taken, and dropping it silently turns a declared cadence into a
    different one. So it is refused, and the run says which signal and which two
    numbers disagree.
    """


def draw_fraction(
    seed: int, stream: str, step_index: int, ordinal: int = 0
) -> Fraction:
    """One uniform draw in the half-open unit interval, per v4 section 9.2.

    The identity is the one the specification names rather than one this build
    chose:

        digest("assetops-sim-rng-v1", seed, stream_name, step_index, ordinal)

    in that order, over the same length-prefixed canonical encoding every
    identity here uses - which is the "another repository-canonical byte
    encoding" v4 permits beside length-prefixed UTF-8.

    `rng-contract-version` is the `v1` in the domain separator. v4 lists it among
    the things a draw is a function of and then shows a conceptual digest with
    five fields and no separate version, so it is carried where the specification
    carries it rather than added as a sixth field nothing else would agree about.

    ## The signature is the guard, and the first version of this had none

    It used to take `*fields`, and its production caller passed the address and
    the offset in minutes. That is a sound deterministic construction and a
    DIFFERENT contract from the one above. The test meant to catch it recomputed
    the payload the implementation had chosen, so it established determinism
    rather than conformance - the defect shape this milestone has repeated in
    every slice: a check that proves what the code does rather than what the
    contract requires.

    So there is no `*fields` any more. A caller cannot supply an address, a
    timestamp or anything else, because there is nowhere to put one, which is a
    stronger statement than any assertion about what the caller passes today.

    `step_index` is the boundary's own index, which is what the contract names.
    `ordinal` distinguishes several draws by one stream at one step; a mechanism
    drawing once per step passes zero, and it is a parameter rather than a
    constant so the second such mechanism has somewhere to go.
    """
    payload = canonical_payload(
        [RNG_DOMAIN, seed, stream, step_index, ordinal]
    )
    digest = hashlib.blake2b(payload, digest_size=32).digest()
    return Fraction(int.from_bytes(digest, "big"), DRAW_DENOMINATOR)


def draw_selects(
    seed: int,
    stream: str,
    per_thousand: int,
    step_index: int,
    ordinal: int = 0,
) -> bool:
    """Whether a draw falls inside a threshold expressed per thousand.

    Exact throughout. A `per_thousand` of zero selects nothing and one thousand
    selects everything, and both are decided by comparing two rationals rather
    than by short-circuiting - so a signal declaring no dropout still draws, and
    the draw it makes is the draw it would have made with a threshold.

    That matters for one reason: it is what makes the threshold the only thing a
    reader has to change to see the mechanism work, rather than the threshold
    AND whatever call order a short circuit would have altered.
    """
    if not 0 <= per_thousand <= 1000:
        raise ValueError(
            f"A dropout of {per_thousand} per thousand is not a share of "
            "anything. A threshold lies between none and all of them."
        )
    return draw_fraction(seed, stream, step_index, ordinal) < Fraction(
        per_thousand, 1000
    )


def exact_decimal_text(value: Fraction) -> str:
    """One exact rational as text a screen may show.

    A decimal when the rational has one - which every number this build has ever
    produced does, because the denominators are products of twos and fives - and
    the ratio itself when it does not. Never a float: 2799/800 is exactly
    3.49875, and a screen that printed 3.4987499999999997 would be stating a
    precision the arithmetic does not have, in the one product whose numeric
    policy is that it never rounds.
    """
    if value.denominator == 1:
        return str(value.numerator)
    remaining = value.denominator
    twos = 0
    while remaining % 2 == 0:
        remaining //= 2
        twos += 1
    fives = 0
    while remaining % 5 == 0:
        remaining //= 5
        fives += 1
    if remaining != 1:
        return f"{value.numerator}/{value.denominator}"
    places = max(twos, fives)
    scaled = value * (10**places)
    digits = str(abs(scaled.numerator)).rjust(places + 1, "0")
    sign = "-" if value < 0 else ""
    whole, fraction = digits[:-places], digits[-places:]
    fraction = fraction.rstrip("0")
    return f"{sign}{whole}.{fraction}" if fraction else f"{sign}{whole}"


@dataclass(frozen=True)
class DeviceSignalSpec:
    """One configured device signal, and everything its reporting path declares.

    `address` is the `addressed_key` spelling every comparison in this product
    already keys on, so a signal reports about a named state on a named machine
    rather than about a state key that might be two machines' at once.

    The key is the address, the device and the signal, and all three are
    load-bearing. Two devices may report one address - a redundant sensor is
    ordinary - and one device may carry two signals about the same address at
    different cadences. Neither is expressible if the reporting path is keyed on
    the state alone, and criterion 10's "a change to one reporting path leaves
    the others intact" is a claim about exactly that key.

    `dropout_stream` is the stream name the draw contract uses, and it is the
    whole of what identifies this path to the draw - v4 section 9.2's identity is
    seed, stream name, step index and ordinal, with no room for an address. It is
    derived from the device and the signal rather than authored, so two signals
    cannot be given one stream by accident, and the publication profile refuses
    two declarations of one device signal, so the name is unique by construction.

    The device has to be in it. Two devices may report one address with the same
    signal identifier - a redundant sensor is ordinary - and a stream named after
    the address and the signal alone would give both the same draws, which is
    exactly the correlation this name exists to prevent.
    """

    device_id: str
    signal_id: str
    address: str
    state_key: str
    reading_class: str
    canonical_unit: str
    cadence_minutes: int
    bias: Fraction
    dropout_per_thousand: int
    statement: str

    def __post_init__(self) -> None:
        if self.reading_class not in REPORTABLE_READING_CLASSES:
            raise ValueError(
                f"Signal {self.signal_id!r} on {self.device_id!r} reports a "
                f"{self.reading_class!r}, and a published reading is one of "
                f"{sorted(REPORTABLE_READING_CLASSES)}. A controller's view is "
                "not published, so no device signal may be declared for it."
            )
        if self.cadence_minutes <= 0:
            raise ValueError(
                f"Signal {self.signal_id!r} on {self.device_id!r} declares a "
                f"cadence of {self.cadence_minutes} minutes. A cadence is how "
                "often a reading is published, so it has non-zero length."
            )
        if not 0 <= self.dropout_per_thousand <= 1000:
            raise ValueError(
                f"Signal {self.signal_id!r} on {self.device_id!r} declares a "
                f"dropout of {self.dropout_per_thousand} per thousand, which is "
                "not a share of the samples that were due."
            )

    @property
    def key(self) -> tuple[str, str, str]:
        """The address, device and signal this reporting path is keyed by."""
        return (self.address, self.device_id, self.signal_id)

    @property
    def dropout_stream(self) -> str:
        return f"dropout:{self.device_id}:{self.signal_id}"

    def due_at(self, offset_minutes: int) -> bool:
        """Whether a sample is due at an offset.

        Calls the contract's own `sample_due_at` rather than repeating the
        arithmetic, so the rule that publishes the sentence and the code that
        decides it cannot disagree.
        """
        return sample_due_at(offset_minutes, self.cadence_minutes)

    def as_fields(self) -> tuple[object, ...]:
        return (
            self.device_id,
            self.signal_id,
            self.address,
            self.state_key,
            self.reading_class,
            self.canonical_unit,
            self.cadence_minutes,
            self.bias,
            self.dropout_per_thousand,
        )


@dataclass(frozen=True)
class ReportingPathWindow:
    """One span across which one signal's reporting path is forced unavailable.

    The neutral half of `FrozenReportingPathCondition`, whose docstring already
    says its window was frozen for this consumer. It is not a world state and
    carries no magnitude: a path is either carrying readings or it is not.

    **It names the SIGNAL rather than only the address, and that is not
    incidental.** A reporting-path condition is authored against a path -
    `fuel-level-reporting-availability@fuel-tank` - and which configured signals
    that path carries is the publication profile's declaration. Keying on the
    address instead would silence every signal about that tank, including a second
    sensor nobody said anything about; keying on the state key would silence one
    tank's sensor because another tank's path was cut.

    `condition_address` is the path the scenario named, kept beside the signal so
    a screen can say which authored entry did this rather than only that something
    did.

    ## `timing_shape` is carried, and leaving it out collapsed two meanings

    The authored vocabulary has three shapes and the frozen condition carries
    which one it is. The first version of this record did not, and read every
    absent duration as the interval's end - so a POINT condition at offset 1500
    silenced 1500, 1515 and 2400 alike, which is a run-long outage where the
    document declared an instant. Execution had discarded a frozen causal timing
    field, which is the thing freezing the projection exists to prevent.

    So the shape is here and `end_offset_minutes` reads it. Half-open at both
    ends, like every other span in this product, and `covers` is the whole of the
    membership test.
    """

    event_id: str
    condition_address: str
    device_id: str
    signal_id: str
    address: str
    timing_shape: str
    offset_minutes: int
    duration_minutes: int | None
    interval_minutes: int
    timestep_minutes: int

    def __post_init__(self) -> None:
        if self.timing_shape not in ENTRY_SHAPES:
            raise ValueError(
                f"Reporting condition {self.event_id!r} occupies time as "
                f"{self.timing_shape!r}, and an entry is one of "
                f"{sorted(ENTRY_SHAPES)}. A shape with no rule for how long it "
                "lasts would be an outage of a length nobody declared."
            )
        if self.timing_shape == "WINDOW" and self.duration_minutes is None:
            raise ValueError(
                f"Reporting condition {self.event_id!r} is a WINDOW and declares "
                "no length. A window with no length is not a window, and reading "
                "the absence as the rest of the run is how an instant became an "
                "outage."
            )
        if self.timestep_minutes <= 0:
            raise ValueError(
                f"Reporting condition {self.event_id!r} is placed in a run of "
                f"{self.timestep_minutes}-minute steps. A run walks its interval "
                "in spans of non-zero length."
            )

    @property
    def signal_key(self) -> tuple[str, str, str]:
        return (self.address, self.device_id, self.signal_id)

    @property
    def end_offset_minutes(self) -> int:
        """Where the outage stops, decided by the shape the document declared.

        `reporting-path-conditions-occupy-time-by-their-shape` in the execution
        contract, as the arithmetic:

        - a WINDOW ends at its offset plus its declared length;
        - an INTERVAL_WIDE entry holds until the run interval ends, which is what
          `interval-wide-span` already says of every interval-wide entry;
        - a POINT covers the one step whose half-open span contains its offset,
          because `point-applied-once` says an instant belongs to exactly one
          step. Since a cadence is a whole multiple of the timestep, that span
          holds at most one due sample - which is what makes a point outage an
          instant rather than a stretch.
        """
        if self.timing_shape == "WINDOW":
            return self.offset_minutes + (self.duration_minutes or 0)
        if self.timing_shape == "INTERVAL_WIDE":
            return self.interval_minutes
        step_start = (
            self.offset_minutes // self.timestep_minutes
        ) * self.timestep_minutes
        return min(step_start + self.timestep_minutes, self.interval_minutes)

    @property
    def start_offset_minutes(self) -> int:
        """Where the outage starts, which for a POINT is its step's start.

        A point belongs to the step whose span contains it, so the outage is that
        step's span rather than a stretch beginning part way through one.
        """
        if self.timing_shape == "POINT":
            return (
                self.offset_minutes // self.timestep_minutes
            ) * self.timestep_minutes
        return self.offset_minutes

    def covers(self, offset_minutes: int) -> bool:
        return (
            self.start_offset_minutes
            <= offset_minutes
            < self.end_offset_minutes
        )

    def as_fields(self) -> tuple[object, ...]:
        return (
            self.event_id,
            self.condition_address,
            self.device_id,
            self.signal_id,
            self.address,
            self.timing_shape,
            self.start_offset_minutes,
            self.end_offset_minutes,
        )


@dataclass(frozen=True)
class FrozenReportingInputs:
    """Everything the observation transform consumes, and no world quantity.

    The companion to `FrozenWorldInputs` and deliberately a separate record. The
    world's identity excludes the reporting path - `IDENTITY_FIELDS_EXCLUDED`
    says so and says why - so two runs differing only here produce the same
    trajectory. Keeping the two records apart is what makes that structural: the
    kernel is handed no field a cadence, a bias or a dropout could arrive in, so
    changing one cannot move a stock.

    `publication_profile_id` and `publication_profile_version` are here for the
    same reason the model profile's are on the world record. A run freezes which
    publication profile answered; a transform handed another one is generating a
    different experiment's readings under this run's name.
    """

    run_id: str
    publication_profile_id: str
    publication_profile_version: int
    seed: int
    interval: FrozenInterval
    signals: tuple[DeviceSignalSpec, ...]
    gaps: tuple[ReportingPathWindow, ...]

    def __post_init__(self) -> None:
        seen: set[tuple[str, str, str]] = set()
        for signal in self.signals:
            if signal.key in seen:
                raise ValueError(
                    f"Two device signals in run {self.run_id} are keyed "
                    f"{signal.key}. The key is what tells two reporting paths "
                    "apart, so two paths sharing one would be one path with two "
                    "sets of parameters and no rule for which applies."
                )
            seen.add(signal.key)

    def refuse_a_cadence_the_run_cannot_express(self) -> None:
        """Refuse a cadence that is not a whole multiple of the timestep."""
        timestep = self.interval.timestep_minutes
        for signal in self.signals:
            if not cadence_is_expressible(signal.cadence_minutes, timestep):
                raise ReportingResolutionUnrepresentable(
                    f"Signal {signal.signal_id!r} on {signal.device_id!r} "
                    f"publishes every {signal.cadence_minutes} minutes and run "
                    f"{self.run_id} is walked in steps of {timestep}. Samples "
                    "would be due between two boundaries, and neither moving "
                    "them to the nearest one nor dropping them is what the "
                    "cadence says. Choose a timestep the cadence divides."
                )

    def gaps_covering(
        self, signal: DeviceSignalSpec, offset_minutes: int
    ) -> tuple[ReportingPathWindow, ...]:
        """Every declared gap on one signal's path that covers one instant.

        Matched on the signal's whole key rather than on its address, for the
        reason `ReportingPathWindow` records: a second sensor on the same tank is
        a second path, and nothing about one being cut says the other was.
        """
        return tuple(
            window
            for window in self.gaps
            if window.signal_key == signal.key and window.covers(offset_minutes)
        )

    def signal(
        self, address: str, device_id: str, signal_id: str
    ) -> DeviceSignalSpec | None:
        for spec in self.signals:
            if spec.key == (address, device_id, signal_id):
                return spec
        return None


@dataclass(frozen=True)
class DeviceObservation:
    """One sample attempt by one device on one signal, at one instant.

    Carries what was reported and never what was true. `reported_value` is
    present exactly when `outcome` is `REPORTED`, which the constructor holds
    rather than documents: an absent reading with a number beside it would be the
    fabricated value this whole vocabulary exists to refuse.

    `source_sample_time` is the device's own time for the sample, which is the
    simulated instant it was taken at. It is a separate field from the offset
    because a consumer reading a series needs a timestamp rather than a position
    in a run, and a retained reading shown at a later instant needs to be able to
    say when it was actually taken.
    """

    device_id: str
    signal_id: str
    address: str
    state_key: str
    reading_class: str
    at_offset_minutes: int
    source_sample_time: str
    outcome: str
    reported_value: Fraction | None
    canonical_unit: str
    suppression_reason: str | None = None

    def __post_init__(self) -> None:
        if self.outcome not in SAMPLE_OUTCOMES:
            raise ValueError(
                f"A sample attempt ends as one of {sorted(SAMPLE_OUTCOMES)}, "
                f"not {self.outcome!r}."
            )
        if (self.outcome == "REPORTED") != (self.reported_value is not None):
            raise ValueError(
                f"Sample {self.signal_id!r} on {self.device_id!r} at offset "
                f"{self.at_offset_minutes} is {self.outcome} and "
                f"{'carries' if self.reported_value is not None else 'carries no'}"
                " value. A reading that did not happen has no number, and one "
                "that did is not reported without it."
            )
        if (self.outcome == "REPORTED") == (
            self.suppression_reason is not None
        ):
            raise ValueError(
                f"Sample {self.signal_id!r} on {self.device_id!r} at offset "
                f"{self.at_offset_minutes} is {self.outcome} and "
                f"{'names' if self.suppression_reason is not None else 'names no'}"
                " reason. Every absent reading says why it is absent, and a "
                "reading that happened has nothing to explain."
            )

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.address, self.device_id, self.signal_id)

    def as_fields(self) -> tuple[object, ...]:
        return (
            self.device_id,
            self.signal_id,
            self.address,
            self.state_key,
            self.reading_class,
            self.at_offset_minutes,
            self.source_sample_time,
            self.outcome,
            self.reported_value,
            self.canonical_unit,
            self.suppression_reason,
        )


@dataclass(frozen=True)
class ReportedReading:
    """What a consumer of one signal sees at one instant, and nothing more.

    The reporting half of a Lab row, computed entirely from the reading series -
    which is what makes it checkable against the series rather than against the
    world. `value` and `source_sample_time` are the newest published reading at or
    before this instant, carrying that reading's OWN time; `quality` says whether
    that is this instant's reading, an older one retained, or nothing at all.

    `due` and `outcome` are about THIS instant rather than about the value: a
    sample can be due and dropped while a retained reading is still what a
    consumer sees, and separating the two is what lets a screen show both facts
    without either contradicting the other.
    """

    address: str
    device_id: str
    signal_id: str
    reading_class: str
    at_offset_minutes: int
    value: Fraction | None
    source_sample_time: str | None
    source_offset_minutes: int | None
    quality: str
    due: bool
    outcome: str | None
    suppression_reason: str | None

    def __post_init__(self) -> None:
        if self.quality not in READING_QUALITIES:
            raise ValueError(
                f"A reading is one of {sorted(READING_QUALITIES)}, not "
                f"{self.quality!r}."
            )
        if (self.quality == "UNAVAILABLE") != (self.value is None):
            raise ValueError(
                f"The reading of {self.signal_id!r} on {self.device_id!r} at "
                f"offset {self.at_offset_minutes} is {self.quality} and "
                f"{'carries' if self.value is not None else 'carries no'} value. "
                "An unavailable reading has no number to show and an available "
                "one is not shown without it."
            )
        if self.quality == "STALE" and self.source_offset_minutes == (
            self.at_offset_minutes
        ):
            raise ValueError(
                f"The reading of {self.signal_id!r} on {self.device_id!r} at "
                f"offset {self.at_offset_minutes} is STALE and was taken at that "
                "same instant. A reading published now is not a retained one."
            )


def observation_series_digest(
    observations: tuple[DeviceObservation, ...]
) -> str:
    """The identity of one reading series.

    Separate from the trajectory's `content_digest` because the two answer
    different questions, and a single digest would answer neither. The world's
    identity deliberately excludes the reporting path, so two runs whose cadences
    differ have one trajectory digest and must not be said to have produced one
    series - and two runs whose worlds differ have one series digest whenever
    every reading of both was suppressed.
    """
    return identity_digest(
        [
            "observation-series",
            tuple(item.as_fields() for item in observations),
        ]
    )


#: What each outcome means, so a screen places the vocabulary's own copy rather
#: than composing a second one. A test asserts this covers `SAMPLE_OUTCOMES`
#: exactly, so an outcome cannot arrive without saying what it tells a reader.
SAMPLE_OUTCOME_STATEMENTS: dict[str, str] = {
    "REPORTED": (
        "The sample was due, the reporting path was carrying readings, and the "
        "device published a value. The value is what the device reported and "
        "not what the world held: a declared bias is already in it."
    ),
    "SUPPRESSED_BY_GAP": (
        "The sample was due and the reporting path was forced unavailable "
        "across a declared window, so nothing was sampled and nothing was "
        "published. The world carried on through the window; a reader looking "
        "only at readings cannot see what it did."
    ),
    "DROPPED": (
        "The sample was due, the path was carrying readings, and this "
        "publication did not happen. It is drawn from the run's seed rather "
        "than chosen, so the same run drops the same samples every time."
    ),
    "NO_PRECEDING_INTERVAL": (
        "An interval reading was due at the run's first boundary, where no span "
        "has completed. It is unavailable rather than zero and rather than the "
        "first step's own value: both would attribute a number to a span the "
        "run never covered."
    ),
    "NO_VALUE_AT_BOUNDARY": (
        "A span ended at this instant and this model measured nothing in it. "
        "That is a different fact from no span having ended, and from the path "
        "being down: the path was up, the sample was taken, and there was "
        "nothing for it to read."
    ),
}

#: What each quality tells a reader about the row it is on. A test asserts this
#: covers `READING_QUALITIES` exactly.
READING_QUALITY_STATEMENTS: dict[str, str] = {
    "GOOD": (
        "A reading was published at this instant. It is the device's value and "
        "not the world's, and the true value beside it is what the world held."
    ),
    "STALE": (
        "No reading was published at this instant, and the newest one before it "
        "is shown with its own time. It described the world when it was taken "
        "and does not describe the world now."
    ),
    "UNAVAILABLE": (
        "No reading has been published on this signal at or before this "
        "instant, so there is nothing to retain and nothing to show."
    ),
}
