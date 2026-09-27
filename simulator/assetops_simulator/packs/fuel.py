"""The minimal fuel world: one tank, one generator, one law.

The narrow first causal proof. It models the stored volume in a generator fuel
tank, the capacity that bounds it, the generator's specific fuel consumption and
the output a scenario dispatches it at, and nothing else - which is the same
sentence `MINIMAL_FUEL_TANK_MODEL` states on the product side, and the
conformance test is what makes the two one claim rather than two.

## The law

    fuel consumed over a step = specific consumption (L/kWh) x energy delivered

Energy delivered is the forced output times the part of the step the dispatch
window covers. Power comes from forcing: nothing here solves a power flow, and
nothing here decides whether the generator should run. That is the whole of what
`FORCING_INPUT` means and the reason a scenario declaring 45 kW over four hours
needs no electrical dispatch controller to produce a fuel trajectory.

Outside its window the dispatch forcing is UNAVAILABLE, so the law does not run
and the step records no delivered energy. It records no zero either: an absent
entry is this product's spelling of a value it does not have, and a zero would
be a number nobody supplied. The distinction is visible on the trajectory -
`forcings_available` simply has no row for that step - and it is what stops the
law's silence being read as the generator delivering nothing when in fact the
scenario said nothing.

## Why one generator and one tank

The model relates one generator to one fuel tank because it has no topology to
relate two. A frozen run naming two tanks or two generators fails as
`TOPOLOGY_INCONSISTENT` rather than pairing whichever was read first, which is
the honest size of a narrow fuel world: a second tank is a real installation and
what burns from it is a question this model cannot answer. Addressing is not the
missing piece - T020A1 built that - the missing piece is the declared
relationship, and it arrives with the electrical world.

## Why the floor is here

`D-2026-09-22-reconciliation-panel-retirement`: the kernel takes its floor from
the model, never from the validation layer's `IMPLICIT_LOWER_BOUND_DIMENSIONS`.
*A stored volume cannot go below zero* is a model rule, so the stock handler
declares it, with the bound case that says what happens when it is reached -
`insufficient-fuel`, which is `FAIL_RUN`, because a draw the tank cannot supply
means the authored causes and the world they produced have contradicted each
other.
"""

from __future__ import annotations

from fractions import Fraction

from assetops_simulator.kernel.model import ModelLaw, ModelSpec, StateHandler

#: The address of a stored volume, as this pack names the semantic state.
FUEL_TANK_VOLUME = "fuel-tank-volume"
FUEL_TANK_CAPACITY = "fuel-tank-capacity"
GENERATOR_SPECIFIC_CONSUMPTION = "generator-specific-fuel-consumption"
GENERATOR_OUTPUT_POWER = "generator-output-power"


class PhysicallyUnacceptable(ValueError):
    """The resolver was handed a value the world cannot have.

    Raised by a handler rather than by the kernel, because which values a state
    admits is a property of the state the model declares. The kernel turns it
    into `PHYSICAL_RESOLUTION_FAILURE` at the phase the resolver runs in.
    """


def _stored_volume(value: Fraction) -> Fraction:
    """A stored volume, checked for what a volume can be.

    The parser refuses a negative volume when a document is read, which is the
    `invalid-rate` bound case and `REFUSED_AT_PARSE`. This is the same fact one
    phase later, for content that reached a kernel without crossing that
    parser - a hand-edited run document, or a caller building inputs directly.
    A model that trusted the parser would be a model whose only defence against
    an impossible number is that something else usually catches it.
    """
    if value < 0:
        raise PhysicallyUnacceptable(
            f"a stored volume of {value} litres is not a volume the world can "
            "hold"
        )
    return value


def _apply_to_stock(current: Fraction, delta: Fraction) -> Fraction:
    """The stock after a delta, with no bound applied.

    Bounding is the kernel's, because a bound is a relationship between two
    declared states and its policy is the contract's. What this handler owns is
    that a volume is a volume: the arithmetic is exact and the result is a
    rational, never a float.
    """
    return current + delta


def _capacity_as_upper_bound(value: Fraction) -> Fraction:
    """The capacity, as the number that bounds the stored volume.

    It is a handler rather than a constant because the capacity is the SITE's
    answer, resolved through the profile's binding and frozen on the run
    (`D-2026-09-22-capacity-bound-source`). The document declares WHICH state
    caps which; this is where the model accepts the number and says it is a
    bound on a volume.
    """
    return _stored_volume(value)


def _specific_consumption(value: Fraction) -> Fraction:
    """The litres per kilowatt-hour this generator burns.

    A property of the machine alone, which is why it is `L/kWh` and not `L/h`
    (`D-2026-09-22-consumption-coefficient-unit`). Negative is impossible and
    zero is a generator that burns nothing, which is odd but not unphysical, so
    only the first is refused.
    """
    if value < 0:
        raise PhysicallyUnacceptable(
            f"a specific fuel consumption of {value} L/kWh is not a "
            "consumption the machine can have"
        )
    return value


def _delivered_energy(
    forced_power_kw: Fraction, exposed_minutes: int
) -> Fraction:
    """The energy a forced output delivers over the part of a step it covers.

    The forcing declares a LEVEL over a window, and `window-ramp` says one
    declared number applies unchanged across the span. So the energy is the
    level times the exposure, and the exposure is the overlap the contract's own
    predicate computes - never the whole step, because a step a window covers
    only in part is exposed to the forcing for that part and no longer.
    """
    if forced_power_kw < 0:
        raise PhysicallyUnacceptable(
            f"a dispatched output of {forced_power_kw} kW is not an output a "
            "generator can deliver"
        )
    return forced_power_kw * Fraction(exposed_minutes, 60)


def _sample_state_signal(value: Fraction, phase_id: str) -> Fraction:
    """The stored volume at an instant, sampled after that instant's events.

    The handler that makes `fuel-tank-volume` supported in the
    `REPORTED_OBSERVATION` role, and the phase check is the substance of it.
    `state-signal-sampled-after-events` says a stock reading timestamped T is
    the state after T's events, and the only way a handler can hold that rule is
    to refuse to answer anywhere else in the cycle. Called from
    `apply-events` it would be reading a world mid-change; called from `evolve`
    it would be reading a span rather than an instant.

    What this is NOT is a published reading. There is no device here, no
    sampling error, no cadence, no dropout and no envelope: the value goes on
    the private trajectory and nowhere else. What a gateway does with it is the
    observation transform's, and that is a later slice.
    """
    if phase_id != "sample-and-publish":
        raise PhysicallyUnacceptable(
            f"a stock reading was asked for during {phase_id!r}. A reading "
            "timestamped T is the state after T's events, so it is taken in "
            "the sampling phase and nowhere else in the cycle."
        )
    return value


def _fuel_consumed(
    coefficient: Fraction, delivered_energy: Fraction
) -> Fraction:
    """The minimum law: consumption is specific consumption times energy.

    Exact rational throughout. 311/1000 L/kWh times 45/4 kWh is 2799/800 L, and
    that is the number the tank loses - not 3.49875 as a binary float, which is
    a different number and would compound over sixteen steps.
    """
    return coefficient * delivered_energy


STOCK_HANDLER = StateHandler(
    handler_id="fuel-tank-volume-stock",
    state_key=FUEL_TANK_VOLUME,
    scope="COMPONENT",
    role="CAUSAL_INPUT",
    kind="STOCK",
    dimension="VOLUME",
    floor=Fraction(0),
    floor_bound_case_id="insufficient-fuel",
    statement=(
        "The stored volume in a fuel tank persists across steps, is initialized "
        "from the frozen run, and is moved by every declared cause and by the "
        "consumption law. It cannot go below zero, which is a model rule and "
        "not an assumption the validation layer injects."
    ),
    consume=_apply_to_stock,
    initialize=_stored_volume,
)

SAMPLE_HANDLER = StateHandler(
    handler_id="fuel-tank-volume-state-signal",
    state_key=FUEL_TANK_VOLUME,
    scope="COMPONENT",
    role="REPORTED_OBSERVATION",
    kind="STATE_SAMPLE",
    dimension="VOLUME",
    statement=(
        "The stored volume can be sampled at an instant, after that instant's "
        "events, which is what makes it reportable at all. This answers what "
        "the world holds; whether anything publishes that answer, at what "
        "cadence and with what error, is the reporting path and not this model."
    ),
    consume=_sample_state_signal,
)

CAPACITY_HANDLER = StateHandler(
    handler_id="fuel-tank-capacity-bound",
    state_key=FUEL_TANK_CAPACITY,
    scope="COMPONENT",
    role="CAUSAL_INPUT",
    kind="BOUND_SOURCE",
    dimension="VOLUME",
    statement=(
        "The capacity is the number that bounds the stored volume. The "
        "definition declares which state it caps and the site's foundation "
        "answers for how large it is, so the model consumes a frozen number "
        "rather than reading one out of a document."
    ),
    consume=_capacity_as_upper_bound,
)

CONSUMPTION_COEFFICIENT_HANDLER = StateHandler(
    handler_id="generator-specific-fuel-consumption-coefficient",
    state_key=GENERATOR_SPECIFIC_CONSUMPTION,
    scope="COMPONENT",
    role="CAUSAL_INPUT",
    kind="COEFFICIENT",
    dimension="VOLUME_PER_ENERGY",
    statement=(
        "How much fuel this generator burns per kilowatt-hour delivered. A "
        "property of the machine alone, which is why it carries no operating "
        "point; the operating point is the forcing beside it."
    ),
    consume=_specific_consumption,
)

DISPATCH_FORCING_HANDLER = StateHandler(
    handler_id="generator-output-power-forcing",
    state_key=GENERATOR_OUTPUT_POWER,
    scope="COMPONENT",
    role="FORCING_INPUT",
    kind="FORCING",
    dimension="POWER",
    statement=(
        "The output the generator is dispatched at, forced across a declared "
        "window and turned into the energy delivered over the part of each step "
        "that window covers. Nothing here solves a power flow and nothing here "
        "decides whether the generator should run."
    ),
    consume=_delivered_energy,
)

FUEL_CONSUMPTION_LAW = ModelLaw(
    law_id="fuel-consumption-follows-delivered-energy",
    statement=(
        "Fuel consumed over a step is the generator's specific fuel "
        "consumption times the energy it delivered over that step. It runs only "
        "in the steps the dispatch window concerns: outside them the forcing is "
        "unavailable, so there is no delivered energy for the coefficient to "
        "multiply and the law does not run rather than multiplying a zero "
        "nobody declared."
    ),
    reads=(
        DISPATCH_FORCING_HANDLER.handler_id,
        CONSUMPTION_COEFFICIENT_HANDLER.handler_id,
    ),
    writes=(STOCK_HANDLER.handler_id,),
    compute=_fuel_consumed,
    direction="DECREASE",
)

#: The model the first causal kernel implements, and the falsifier for the
#: product profile that declares the same four states.
MINIMAL_FUEL_MODEL = ModelSpec(
    model_profile_id="minimal-fuel-tank",
    model_profile_version=1,
    statement=(
        "Models the stored volume in a generator fuel tank, the capacity that "
        "bounds it, the generator's specific fuel consumption and the output it "
        "is dispatched at, and nothing else. It relates one generator to one "
        "fuel tank, because it has no declared topology with which to relate "
        "two. Site demand and plane-of-array irradiance have no handler here, "
        "so this model does not consume them in any role."
    ),
    handlers=(
        STOCK_HANDLER,
        SAMPLE_HANDLER,
        CAPACITY_HANDLER,
        CONSUMPTION_COEFFICIENT_HANDLER,
        DISPATCH_FORCING_HANDLER,
    ),
    laws=(FUEL_CONSUMPTION_LAW,),
)
