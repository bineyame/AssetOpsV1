"""The executable meaning of a scenario: units, timing, bounds, reconciliation.

`scenarios/models.py` holds the vocabularies an author writes and the parser
enforces. This module holds the semantics those vocabularies commit the product
to - the parts that are the same for every scenario and are therefore versioned
simulator rules rather than authored content:

- what each unit is in canonical terms, so a consumer converts a quantity
  without parsing the text a screen shows;
- how a point entry and a window entry are dispatched against the run's
  half-open time model, and what "exactly once" means at a boundary;
- what a conforming kernel does at each instant, in order, and where a sample,
  a controller and the physics sit relative to the events due there;
- what a reading timestamped `T` describes, which is not the same answer for a
  stock as for a rate;
- what a kernel must do when a bound is reached, stated as a policy with no
  silent option in it;
- whether each reported observation is accounted for by the causal inputs the
  same scenario declares.

## `reconcile_reported_observations` is a reference implementation

It is labelled as one, with its expiry stated as a condition, in
`backend/tests/test_scenario_execution_contract.py`, per
`D-2026-09-21-specification-reference-implementation`. The short form: it
exercises this contract against a real document because a specification with
no implementation is under-tested, it is not a product feature, and it stops
being an authority the moment a kernel exists to be compared against. Its one
remaining product-path caller is the scenario detail screen's reconciliation
panel, and it leaves the repository when that caller does - which is Open
Question 5 and undecided.

Run setup used to be a second caller. Amendment 1's proposal (e) removed that,
because deciding whether declared causes reach a reading needs a kernel, and
run setup has none.

## This is not a runtime kernel

`reconcile_reported_observations` is contract arithmetic and nothing more. It
has no clock, no timestep, no seed, no state record, no event cursor, and no
output for any instant the scenario did not author an observation at. It never
produces a state trajectory, it is not called by anything that executes, and
removing it would change no behaviour except what the scenario detail screen
can tell a reader.

What it answers is one question the T018 task makes an acceptance criterion:
does the sum of the causal quantities a scenario declares reach the value the
same scenario says a device reported? A contract that cannot answer that lets a
reported number silently prescribe private tank state, which is the thing
`D-2026-09-21-causal-runtime-before-golden-traces` says an authored artifact
must not be able to do. The answer is reported; it is never used to adjust
anything.

The real kernel is T021's. When it exists it owns initialization and the
transition from one private world state to the next, and this module keeps
answering only the contract question.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable

from assetops_backend.scenarios.models import (
    STATE_CHANGING_ROLES,
    ScenarioDefinition,
    ScenarioParameter,
    TimelineEntry,
)
from assetops_backend.state_refs import StateRef

#: The contract this module implements, named so a later run, trace, or payload
#: can say which version of these semantics it was built against. It is not the
#: scenario version and not the simulator version: it is the version of the
#: rules below.
#:
#: **When this moves.** A version moves when the space of behaviours a
#: conforming implementation may exhibit changes, including when it narrows.
#: Wording does not move it.
#:
#: That is a stricter test than "the rule set is what is versioned", which an
#: earlier draft of this comment used, and the difference has a cost
#: downstream. `D-2026-09-21-causal-runtime-before-golden-traces` makes a
#: provenance mismatch REFUSE playback rather than fall back, so a version
#: that moved on a prose edit would force regeneration of golden traces that
#: were never invalid.
#:
#: Two since T019, which declared what happens when two causes complete at one
#: instant. Version one left that unspecified: two conforming version-one
#: kernels could legitimately disagree at that instant, so declaring any rule
#: for it narrows the space, and that is what moved the number. T019's review
#: then replaced the rule's content - authored order gave way to a net effect
#: with an exact ambiguity test - and the version did not move again. Both
#: drafts narrow the same unspecified space, the number identifies the space
#: rather than the wording, and no implementation ever conformed to the first
#: draft: it existed only inside this slice.
#:
#: The same reasoning covers the second amendment, and it is worth spelling
#: out, because the policy above would otherwise read as requiring a third
#: number. T019's review found the statement silent on a group where BOTH
#: extremes reach a bound - a case the code has always abstained on -
#: and specifying it narrows the space a conforming kernel may occupy, which
#: under the policy moves a version. It does not move here for the reason the
#: first amendment did not: version two has never left this branch, nothing
#: has ever conformed to it, and bumping would invent a version no consumer
#: ever saw while spending the golden-trace regeneration the policy exists to
#: avoid. Once this merges, the next narrowing is a three.
#:
#: Three since T020A, and it is the narrowing
#: `D-2026-09-22-foundation-value-declaration` describes: a parameter whose
#: declared owner is the Site's Foundation may no longer state a value. That
#: reaches a document which already exists and was already valid - the shipped
#: Fuel Loss Event as version two accepted it is refused by this parser - so
#: under `D-2026-09-22-contract-version-scope` it moves the number. Version two
#: HAS been published: frozen Drafts in the run store carry it, and they keep
#: it. Nothing reinterprets an earlier frozen run under this version.
#:
#: Four since T020A1, and the narrowing is addressing. A world state is now
#: named by an ADDRESS - a semantic key plus the component it is claimed on -
#: and the change reaches documents that were already valid under three. The
#: same Fuel Loss Event, unedited, against the same single-tank Foundation,
#: freezes `fuel-tank-capacity@fuel-tank` where version three froze
#: `fuel-tank-capacity`: the resolved identity of a run of an unchanged
#: document is different, which is exactly the test
#: `D-2026-09-22-contract-version-scope` sets. The bound a scenario declares,
#: the duplicate-initialization rule and the state a reconciliation compares
#: against all move to the same grain, so two conforming kernels reading one
#: document no longer agree about which tank a reading is about unless they
#: agree about this.
#:
#: Version three HAS been published - the Drafts in the run store carry it -
#: and they keep it. `refuse_incompatible_execution` below is what says so at
#: the moment it would matter: a frozen run stays readable at whatever version
#: it froze, and is refused execution rather than reinterpreted under this one.
#:
#: Five since T020B, and it is three narrowings that arrive together because
#: they are one alignment. Version four IS published - it is on `main`, and
#: local Drafts carry it - so the unreleased-version doctrine that let three
#: amendments share version two does not apply here. This is a move.
#:
#: 1. **A requirement conflict is refused rather than resolved.** One
#:    `(address, role)` declared at two requirement levels used to resolve to
#:    `REQUIRED` by a rule T019 invented. A document that was valid because
#:    the collapse resolved it is now refused, which is exactly the test
#:    `D-2026-09-22-contract-version-scope` sets
#:    (`D-2026-09-22-forcing-state-requirements`, rider one).
#: 2. **Reporting-path support is the publication profile's to declare.** A
#:    state about the reporting path is no longer a state the model profile
#:    answers for, so one document against one pair of profiles reaches a
#:    different outcome. The shipped Fuel Loss Event is the case: under four
#:    its reporting-availability forcing is a state nothing models, and under
#:    five the publication profile answers for it.
#: 3. **The four semantics `D-2026-09-22-kernel-step-semantics` left open are
#:    declared** - the linear window ramp, the boundary cycle's sampling
#:    order, a forcing outside its window being unavailable, and a bounded
#:    change continuing from the bounded value. Each pins a space two
#:    conforming version-four kernels could legitimately have split on, and
#:    narrowing that space is what this number identifies.
#:
#: The lowering of demand and irradiance to `OPTIONAL` is authored content in
#: one document rather than a rule, and moves nothing by itself. It is the
#: other half of the same decision and is why the shipped scenario can now
#: reach `READY`, but a version identifies the rules a document is read under.
#:
#: ## Five was amended in place after its review, and that is recorded here
#:
#: T020B's independent review returned three narrowings that were missing rather
#: than wrong, and they landed on five rather than spending a six:
#:
#: - the sampling phase now says it attaches no interval measurement at the
#:   run's first boundary, where it previously read as attaching one
#:   unconditionally and contradicted the first-boundary reading rule;
#: - that reading rule's exception for a declared historical window is stated as
#:   unreachable in this build, where it previously read as a live branch;
#: - the window ramp now says which step carries a window's final fraction, and
#:   uses "span" for the times it interpolates across rather than "endpoints"
#:   for both the times and the values.
#:
#: A fourth followed from the Codex review, and it is the largest of them: the
#: rules said which steps an ALIGNED window concerns and were silent on every
#: other window, while run setup accepted those documents as `READY`. The
#: shipped Fuel Loss Event is one - its reporting gap `[1490, 1580)` is off the
#: grid at the fifteen-minute timestep the demonstration itself uses, and its
#: removal `[1500, 1545)` is off a legal sixty-minute one. `window-overlap` now
#: states which steps any window concerns at any alignment, the ramp states the
#: share each step applies, and the forcing rule states which steps it is
#: available to. The three agreed before only where a window happened to line
#: up.
#:
#: Each narrows a space two conforming kernels could have split on, so each
#: would move a number under the policy above. They ride on five because five
#: has never left this branch: `main` is at four, no run outside this branch
#: carries five, and nothing has ever conformed to the version as first written.
#: That is the same doctrine version two's three amendments used.
#:
#: **It is recorded rather than done quietly, because the backlog warned about
#: exactly this.** Version four carried three intra-version semantics while
#: unpublished, and the note carrying that fact says it is "not a licence to do
#: it again". The distinction being relied on: four was on a branch and then
#: published, so its amendments became invisible once it merged. Five is being
#: amended before it has ever been published, and this paragraph is what stops
#: the amendment being invisible afterwards. Once this merges, the next
#: narrowing is a six.
EXECUTION_CONTRACT_VERSION = 5


class ExecutionContractIncompatible(Exception):
    """A frozen run was stated against a contract this build cannot execute."""


def refuse_incompatible_execution(frozen_contract_version: int) -> None:
    """Refuse to execute a run frozen against a different contract.

    The half of `D-2026-09-22-contract-version-scope` that is about runs
    rather than about documents. A Draft freezes the contract version its
    inputs were resolved under; when this build's version has moved past it,
    the meanings behind those frozen inputs have changed and executing them
    here would be reinterpretation wearing the old run's identity - the frozen
    address `fuel-tank-capacity` under version three means "whichever tank",
    and under four it would mean a tank called nothing.

    Reading is not execution and is never refused. `runs/parsing.py` accepts
    any version a document carries, the run store serves it, and the detail
    screen renders it, because a run that cannot be executed is still a run
    somebody needs to inspect in order to find out why.

    Nothing in this build executes anything, so the one caller today is
    `runs/provenance.py`, which uses it to say on the run's own frozen-inputs
    table whether this build could execute it. T021's kernel is the second and
    it calls this before it initializes anything.
    """
    if frozen_contract_version != EXECUTION_CONTRACT_VERSION:
        raise ExecutionContractIncompatible(
            f"This run froze its inputs against execution contract version "
            f"{frozen_contract_version} and this build implements version "
            f"{EXECUTION_CONTRACT_VERSION}. The run is preserved exactly as "
            "it was frozen and stays readable; it is not executed, because "
            "executing it here would apply these rules to inputs resolved "
            "under different ones. Set a new run up to execute this scenario "
            "under this build."
        )


@dataclass(frozen=True)
class CanonicalUnit:
    """One authored unit, in canonical terms.

    `factor` is carried as an exact ratio rather than a float so that a rate
    integrated over a window lands on the number an author would write down.
    Fourteen litres an hour over four hours is fifty-six litres; computed
    through a binary float it is fifty-six point zero zero zero zero zero zero
    zero zero zero zero one, and a screen that showed that would be stating a
    precision the scenario does not have.
    """

    dimension: str
    canonical_unit: str
    numerator: int
    denominator: int


#: Every unit a scenario parameter may carry, in canonical terms. A test
#: asserts this covers `PARAMETER_UNITS` exactly, so a unit added to the
#: authoring vocabulary without a conversion fails the build rather than
#: arriving at a consumer as text to parse.
#:
#: No duration unit appears here, and that is the cadence prohibition in its
#: structural form - see `DURATION_UNIT_SPELLINGS` below.
CANONICAL_UNITS: dict[str, CanonicalUnit] = {
    "L": CanonicalUnit("VOLUME", "L", 1, 1),
    "L/h": CanonicalUnit("VOLUME_RATE", "L/min", 1, 60),
    # Specific fuel consumption. A volume per unit of energy delivered, which
    # is a different dimension from a volume per unit of TIME: it is not a
    # rate, it cannot be integrated across a window, and `RATE_INTEGRALS`
    # therefore does not list it. That is what stops it being authored as the
    # magnitude of a windowed state effect.
    "L/kWh": CanonicalUnit("VOLUME_PER_ENERGY", "L/kWh", 1, 1),
    "kW": CanonicalUnit("POWER", "kW", 1, 1),
    "kWh": CanonicalUnit("ENERGY", "kWh", 1, 1),
    "V": CanonicalUnit("VOLTAGE", "V", 1, 1),
    "Hz": CanonicalUnit("FREQUENCY", "Hz", 1, 1),
    "degC": CanonicalUnit("TEMPERATURE", "degC", 1, 1),
    "W/m2": CanonicalUnit("IRRADIANCE", "W/m2", 1, 1),
    "%": CanonicalUnit("FRACTION", "%", 1, 1),
}

#: Spellings of a duration, refused as a parameter unit anywhere.
#:
#: T018 first enforced the cadence prohibition at one position - a duration
#: parameter on a reported observation - and the review found three more the
#: rule did not reach: a top-level duration, a duration on the entry that
#: forces the reporting path, and a reading timed as a window. Closing them
#: one at a time is how the next one gets missed, so the closure is at the
#: vocabulary instead: a duration has no unit to be written in, so there is no
#: position it can occupy as a parameter.
#:
#: This is a narrowing rather than a new field. `min` and `h` were authoring
#: units until this slice moved `run-window-length`, `removal-window-length`
#: and `gap-length` into `timing.duration_minutes`, which is where an entry's
#: length now lives and the only place it may. A duration that is NOT an
#: entry's length has no legitimate home in this product today; if a later
#: slice needs one, it reopens this vocabulary with a reason on the record
#: rather than by an author finding a gap.
#:
#: Listed generously, because the point is the refusal message. A spelling
#: outside this set is refused anyway by the closed unit vocabulary; a
#: spelling inside it is refused with an explanation of where a duration
#: belongs.
DURATION_UNIT_SPELLINGS = frozenset(
    {
        "min",
        "mins",
        "minute",
        "minutes",
        "h",
        "hr",
        "hrs",
        "hour",
        "hours",
        "s",
        "sec",
        "secs",
        "second",
        "seconds",
        "ms",
        "d",
        "day",
        "days",
    }
)

#: Which dimension a rate becomes when it is applied across a window of
#: canonical time. Only the rates this product can integrate are here; a rate
#: outside it cannot be used as a state effect, because the contract would not
#: know what quantity it accumulated to.
RATE_INTEGRALS: dict[str, str] = {"VOLUME_RATE": "VOLUME"}

#: Dimensions whose values cannot be negative. A negative volume, rate, power,
#: energy or irradiance is not a small authoring slip with a defensible
#: reading: it is an invalid input, and the invalid-rate bound case below says
#: it is refused at parse rather than clamped later. Temperature and
#: percentage are deliberately absent, because a negative degC is ordinary.
NON_NEGATIVE_DIMENSIONS = frozenset(
    {"VOLUME", "VOLUME_RATE", "POWER", "ENERGY", "IRRADIANCE"}
)


def canonical_quantity(value: float, unit: str) -> tuple[float, str, str]:
    """Convert an authored quantity into canonical terms.

    Returns the canonical value, the canonical unit, and the dimension.

    Raises:
        KeyError: the unit has no canonical conversion. The parser refuses an
            unsupported unit long before this, so reaching it means the
            authoring vocabulary and this table have drifted apart.
    """
    canonical = CANONICAL_UNITS[unit]
    converted = _exact(value) * Fraction(canonical.numerator, canonical.denominator)
    return float(converted), canonical.canonical_unit, canonical.dimension


def _exact(value: float) -> Fraction:
    """A float as the decimal an author wrote, not as its binary expansion."""
    return Fraction(value).limit_denominator(1_000_000)


# --- Dispatch semantics -----------------------------------------------------
#
# Stated as data rather than prose so the screen, the payload and a later
# kernel read one answer. A run interval is half-open, `[start_time, end_time)`,
# and so is each step, `[t, t + timestep)`. Every rule below follows from
# choosing that consistently, which is the point: a boundary event applied
# twice, or dropped, is what happens when two places choose differently.


@dataclass(frozen=True)
class DispatchRule:
    rule_id: str
    display_name: str
    statement: str


DISPATCH_RULES: tuple[DispatchRule, ...] = (
    DispatchRule(
        rule_id="half-open-interval",
        display_name="Half-open interval and steps",
        statement=(
            "A run covers its start instant up to but not including its end "
            "instant, and each step covers its own start up to but not "
            "including the next. An instant therefore belongs to exactly one "
            "step, which is what makes applying something once a property of "
            "the time model rather than of the code that happens to read it."
        ),
    ),
    DispatchRule(
        rule_id="point-applied-once",
        display_name="A point applies once",
        statement=(
            "A point entry is due in the one step whose half-open span "
            "contains its offset, and is applied at the start of that step. An "
            "offset that falls exactly on a step boundary belongs to the step "
            "that begins there and never to the step that ends there, so it "
            "cannot be applied by both and cannot be skipped by both."
        ),
    ),
    DispatchRule(
        rule_id="window-active-span",
        display_name="A window's active span",
        statement=(
            "A window entry is active for every step that concerns it under "
            "the overlap rule below. The step beginning exactly at the end of "
            "the window is outside it, because the stretch they share has zero "
            "length. Two windows that meet end to start therefore share no "
            "INSTANT - that is what meeting end to start means, and the "
            "half-open span is what guarantees it. They may still both concern "
            "one STEP: exactly the step whose span contains the joining "
            "instant, and none at all when that instant is itself a step "
            "boundary. Disjoint in time and disjoint in selected steps are two "
            "different statements and only the first follows from adjacency. "
            "Where they do share a step, the partial-exposure rule below "
            "already answers it: each applies over its own portion of that "
            "step, neither is stretched across the rest of it, and nothing "
            "blends them."
        ),
    ),
    DispatchRule(
        rule_id="window-overlap",
        display_name="Which steps a window concerns, at any alignment",
        statement=(
            "A step and a window meet when their spans share a stretch of "
            "non-zero length: the step [s, s+dt) concerns the window "
            "[o, o+length) exactly when max(s, o) < min(s+dt, o+length). That "
            "is the whole of which steps a window concerns, and it asks nothing "
            "of alignment - neither a window's edges nor its length need be a "
            "multiple of the timestep a run chooses. Where the edges DO fall on "
            "step boundaries it selects exactly the steps whose starts lie "
            "inside the window, so an aligned window behaves as it always has. "
            "Where they do not it still selects a non-empty set. **How many "
            "steps a window concerns is found by evaluating the predicate, "
            "never by reasoning from the window's length**: a two-minute window "
            "concerns one step when it lies inside one and two when a step "
            "boundary falls inside it, and both answers come from the same "
            "line. A timestep is a resolution chosen after the document was "
            "written, so what it decides is how finely a window is resolved, "
            "never whether the window happened."
        ),
    ),
    DispatchRule(
        rule_id="quantity-across-a-window",
        display_name="A quantity across a window",
        statement=(
            "A window entry that declares a quantity rather than a rate moves "
            "exactly that quantity, and the state at the end of the window is "
            "that quantity applied in full however many steps the window "
            "covers. A rate, by contrast, may only be declared over a window, "
            "because a rate at an instant moves nothing. How much of the "
            "quantity has been applied part way through is not free: the ramp "
            "rule below says."
        ),
    ),
    DispatchRule(
        rule_id="window-ramp",
        display_name="A window ramps linearly",
        statement=(
            "A value a window declares is read at an instant inside it by "
            "linear interpolation across the window's own span, whose two ENDS "
            "are its offset and its offset plus its length. For a declared "
            "quantity the fraction applied by an instant is that instant's "
            "fraction of the span: nothing applied at the offset, all of it "
            "applied by the far end, and proportionally between, rather than "
            "the whole quantity landing at the completion boundary. For a level "
            "a window forces, one declared number applies unchanged across the "
            "span, because interpolating between one value and itself is that "
            "value. This is what an author means by 120 litres over 45 minutes, "
            "and it is the only reading under which retiming or resizing a "
            "window changes the trajectory proportionally. **Which share each "
            "step applies**, at every alignment: the share of the window's span "
            "that the step covers, which is "
            "(min(s+dt, o+length) - max(s, o)) / length for a step [s, s+dt). "
            "Those shares sum to exactly one over the steps the window "
            "concerns, so the declared quantity moves in full whatever the "
            "timestep, and no step is credited with a part of a window it does "
            "not cover. **That formula is the whole answer and no shortcut "
            "from the window's length replaces it**: a two-minute window "
            "contained in one step moves its whole quantity there, and a "
            "two-minute window straddling a step boundary is apportioned "
            "between the two steps in proportion to the part of it each covers "
            "- half and half for [1499, 1501) at a fifteen-minute timestep, so "
            "a declared 120 litres moves 60 in each. Where a window's edges "
            "fall on step boundaries this is the rule as it already stood, and "
            "the last step covering the window applies the last share: the "
            "state AT the far end is the full quantity applied and the forcing "
            "UNAVAILABLE - the value is complete, and the window is over, at "
            "the same instant."
        ),
    ),
    DispatchRule(
        rule_id="forcing-outside-its-window",
        display_name="A forcing outside its window",
        statement=(
            "A forcing input is UNAVAILABLE at every instant outside its "
            "declared window. It is not zero and it is not held at the last "
            "value inside the window: zero is a fabricated number and holding "
            "is an invented persistence rule, while unavailable is already "
            "this product's word for a value it does not have. The window's "
            "membership is the half-open one every rule above uses, so the "
            "instant it stops being available is exactly the instant its own "
            "span excludes. **Which steps it is available to** is the overlap "
            "rule and nothing else: every step that concerns the window, which "
            "for an aligned window is every step from the one beginning at its "
            "offset up to but not including the one beginning at its end. A "
            "step the window covers only in part is exposed to the forcing for "
            "that part of the step and no longer: nothing stretches the forcing "
            "across the rest of that step, and nothing blends it with a value "
            "the window does not declare. So a REQUIRED forcing over a window "
            "too short to contain a step start is available - in whichever "
            "steps the predicate selects, one if the window lies inside a step "
            "and two if a boundary falls inside the window - rather than "
            "silently concerning no step at all. Two adjacent short forcings "
            "may therefore be available in the same step, each over its own "
            "portion of it, which is the partial-exposure rule and not an "
            "exception to it."
        ),
    ),
    DispatchRule(
        rule_id="interval-wide-span",
        display_name="An interval-wide entry",
        statement=(
            "An interval-wide entry starts at offset zero and holds until the "
            "run interval ends. It declares no length, because the length is "
            "the run's and choosing that is run setup."
        ),
    ),
    DispatchRule(
        rule_id="intra-instant-order",
        display_name="Two things at one instant",
        statement=(
            "Entries that take effect on one state at the same instant are a "
            "group with a net effect, and a bound is evaluated on that net "
            "rather than between the members. The order rows are written in "
            "is authoring and display; it is not a fact about the world, so "
            "it decides nothing here. Whether an ordering could have mattered "
            "is decided exactly rather than assumed: every increase first "
            "tests the upper bound, every decrease first tests the lower, and "
            "if neither extreme reaches a bound then no ordering does and the "
            "net stands. If either extreme reaches a bound while the net "
            "itself stays inside, the group is ambiguous and the contract "
            "declines to answer rather than choosing an order - whether one "
            "extreme reaches a bound or both do, since two orderings that "
            "reach different bounds are no more decidable than one that "
            "reaches a bound and one that does not. A scenario that needs "
            "one thing to happen before another says so in time, by "
            "separating the offsets."
        ),
    ),
    DispatchRule(
        rule_id="outside-the-interval",
        display_name="An entry outside the interval",
        statement=(
            "An entry whose offset, or whose window, falls outside the "
            "interval a run chooses is a mismatch between the scenario and the "
            "run. Later run setup refuses it and says which entry; it never "
            "quietly leaves the entry out and executes the rest."
        ),
    ),
)


# --- The boundary cycle -----------------------------------------------------
#
# v4 section 6.1, published here as part of the execution contract rather than
# left in a design document. It replaces the single semantic an earlier draft
# carried - "observe after the step" - which said which side of a step a
# sample falls on and said nothing about where a controller, a physical
# resolver or an invariant check sits relative to it.
#
# The collision it resolves is real and is not a preference. A sample
# timestamped T must never show the pre-event stock state for an event due at
# T, and telemetry is more useful when a rate measurement summarises the
# physical interval that just completed. Both are satisfiable at once, and
# only in one order: events, then the state at T, then the sample - which
# reads the post-event stocks AND attaches an interval measurement for the
# span that has ended - then the controller, then the physics, then the
# evolution of the next span.


@dataclass(frozen=True)
class BoundaryPhase:
    """One phase of the cycle a conforming kernel runs at each instant.

    `sequence` is the contract, not the tuple order. A kernel may not reorder
    two phases and call itself conforming, and a reader comparing an
    implementation against this list needs the ordinal to be a declared fact
    rather than an index somebody counted.
    """

    phase_id: str
    sequence: int
    display_name: str
    statement: str


#: What happens at instant T, in order. Nine phases, and the whole point is
#: that the order is declared: phases C and D both read the world at T and
#: they read it AFTER A, so neither a published reading nor a controller view
#: can see pre-event state. A scenario that needs something seen before an
#: event says so in time, by separating the offsets - the same answer
#: simultaneity got.
BOUNDARY_CYCLE: tuple[BoundaryPhase, ...] = (
    BoundaryPhase(
        phase_id="apply-events",
        sequence=1,
        display_name="Apply what is due at T",
        statement=(
            "Every event and configuration change due exactly at T is applied "
            "first. An entry on a boundary belongs to the step that begins "
            "there, so this is the one phase that decides it, and nothing "
            "later in the cycle sees the world as it was before."
        ),
    ),
    BoundaryPhase(
        phase_id="state-at-t",
        sequence=2,
        display_name="The state at T exists",
        statement=(
            "The post-event stocks and discrete state at T now exist. Every "
            "phase below reads this state, which is what makes 'the state at "
            "T' one thing rather than a question about who is asking."
        ),
    ),
    BoundaryPhase(
        phase_id="sample-and-publish",
        sequence=3,
        display_name="Sample and publish, if either is due at T",
        statement=(
            "If a sample or a publication is due at T, the stock and discrete "
            "state are sampled at T, an interval-rate or interval-energy "
            "measurement for the span [T-dt, T) is attached, the device and "
            "reporting transform is applied, and the result is handed to "
            "gateway staging. The two measurement classes describe different "
            "spans at one timestamp, which the reading rules below state - and "
            "those rules also decide WHETHER an interval measurement exists to "
            "attach. At the run's first boundary no span precedes T, so this "
            "phase attaches none there and the stock sample is unaffected. Read "
            "this phase as what is attached when there is something to attach, "
            "never as every sample carrying an interval measurement."
        ),
    ),
    BoundaryPhase(
        phase_id="controller-view",
        sequence=4,
        display_name="Build the controller view at T",
        statement=(
            "The controller's view is built at T from the local inputs it "
            "declares, after the due events. It is not the published "
            "observation and is not derived from one."
        ),
    ),
    BoundaryPhase(
        phase_id="controller-intent",
        sequence=5,
        display_name="The controller emits intent for [T, T+dt)",
        statement=(
            "The controller emits intent for the span about to be evolved and "
            "mutates no world state. Intent is a request; what the world does "
            "with it is the next phase's answer."
        ),
    ),
    BoundaryPhase(
        phase_id="physical-acceptance",
        sequence=6,
        display_name="Physical acceptance is resolved",
        statement=(
            "The physical resolver returns the flows the world actually "
            "accepts. Intent and acceptance are two records, because a "
            "controller asking for something the installation cannot deliver "
            "is an ordinary and interesting case rather than an error."
        ),
    ),
    BoundaryPhase(
        phase_id="evolve",
        sequence=7,
        display_name="Evolve the world over [T, T+dt)",
        statement=(
            "The accepted flows are integrated over the half-open span "
            "[T, T+dt). This is the only phase that advances the clock, so an "
            "instant is evolved once and by one phase."
        ),
    ),
    BoundaryPhase(
        phase_id="check-invariants",
        sequence=8,
        display_name="Check conservation, bounds and invariants",
        statement=(
            "Conservation, declared bounds and model invariants are checked "
            "after the evolution and before anything is carried forward. What "
            "a reached bound then does is the bound policy's answer and never "
            "a silent clamp."
        ),
    ),
    BoundaryPhase(
        phase_id="carry-forward",
        sequence=9,
        display_name="Carry the result to T+dt",
        statement=(
            "The resulting stocks and discrete state become the state the "
            "next boundary starts from. There is no second copy of the world "
            "and no state that survives outside this hand-off."
        ),
    ),
)


# --- What a timestamped reading means ---------------------------------------


#: The classes of reading this contract distinguishes, and there is no fourth.
#:
#: The pair that matters is the first two: a stock sampled AT T and a rate
#: measured OVER [T-dt, T) are two different timing conventions at one
#: timestamp, and real instrumentation has exactly that asymmetry. It looks
#: wrong only if the two are assumed to mean the same thing, which is why the
#: rules below state each of them rather than leaving the difference to be
#: discovered by whoever first plots them together.
#:
#: The third is not a reading AssetOps ever sees. It is what a controller is
#: permitted to look at, and it is in this vocabulary so that the rule keeping
#: the two apart has somewhere to hang.
READING_CLASSES = frozenset(
    {"STATE_SIGNAL", "INTERVAL_SIGNAL", "CONTROLLER_INPUT"}
)


@dataclass(frozen=True)
class ObservationRule:
    """One rule about what a reading at an instant describes.

    `reading_class` is a member of `READING_CLASSES`, and a test asserts every
    member is named by at least one rule. That is what stops a class from
    sharing an undocumented convention with another: a class nothing states a
    rule for fails the build rather than being read as "presumably the same as
    the other one".
    """

    rule_id: str
    reading_class: str
    display_name: str
    statement: str

    def __post_init__(self) -> None:
        if self.reading_class not in READING_CLASSES:
            raise ValueError(
                f"Observation rule {self.rule_id!r} is about "
                f"{self.reading_class!r}, and a reading is one of "
                f"{sorted(READING_CLASSES)}."
            )


OBSERVATION_RULES: tuple[ObservationRule, ...] = (
    ObservationRule(
        rule_id="state-signal-sampled-after-events",
        reading_class="STATE_SIGNAL",
        display_name="A state reading at T is the state after T's events",
        statement=(
            "A stock or discrete reading timestamped T - a fuel level, a state "
            "of charge, a room temperature, a door position - is sampled after "
            "the events due at T have been applied. It never shows the "
            "pre-event state, so a scenario that wants a reading taken before "
            "a change separates the two offsets."
        ),
    ),
    ObservationRule(
        rule_id="interval-signal-describes-the-preceding-interval",
        reading_class="INTERVAL_SIGNAL",
        display_name="An interval reading at T describes [T-dt, T)",
        statement=(
            "A rate or energy reading timestamped T - average power ending at "
            "T, energy delivered, cooling energy, charger energy - summarises "
            "the half-open span [T-dt, T) that has just ended. So at one "
            "timestamp a stock reading describes that instant and an interval "
            "reading describes the interval before it. That is declared here "
            "rather than left implicit, because the two conventions are "
            "genuinely different and a consumer that assumed one applied to "
            "both would misplace every rate it read."
        ),
    ),
    ObservationRule(
        rule_id="no-interval-signal-at-the-first-boundary",
        reading_class="INTERVAL_SIGNAL",
        display_name="An interval reading is unavailable at the run's start",
        statement=(
            "At the run's first boundary no interval has completed, so every "
            "interval reading there is UNAVAILABLE. It is not zero and it is "
            "not the first step's own value: both would be a number attributed "
            "to a span the run never covered. The sampling phase attaches no "
            "interval measurement there, and says so. **No profile in this "
            "build can declare an initial historical window to measure over "
            "instead** - no profile record carries such a field and nothing "
            "parses one - so at present the rule has no exception. A build that "
            "adds one reopens this rule deliberately, rather than an author "
            "discovering a gap in it."
        ),
    ),
    ObservationRule(
        rule_id="controller-view-is-not-the-published-observation",
        reading_class="CONTROLLER_INPUT",
        display_name="What a controller sees is not what is published",
        statement=(
            "A controller's view is built at T from the local inputs it "
            "declares. What the gateway publishes to AssetOps is a separate "
            "path that may be sparse, noisy, delayed or missing entirely, and "
            "the two are never the same record. Keeping them apart is what "
            "lets a run simulate realistic control and independently test what "
            "the evidence path could have concluded from it."
        ),
    ),
    ObservationRule(
        rule_id="no-cadence-becomes-a-controller-cadence",
        reading_class="CONTROLLER_INPUT",
        display_name="A reporting cadence is not a control cadence",
        statement=(
            "The cadence a publication profile declares is a property of the "
            "reporting path. Nothing turns it into the rate at which a "
            "controller is asked for intent, and nothing turns a control "
            "cadence into a reporting rate. A controller that could only act "
            "as often as a remote sensor published would be an artifact of the "
            "instrumentation rather than of the installation."
        ),
    ),
)


# --- Bound semantics --------------------------------------------------------


@dataclass(frozen=True)
class BoundCase:
    case_id: str
    display_name: str
    policy: str
    statement: str


#: What a kernel is permitted to do when a declared bound is reached.
#:
#: Three policies, and the absent fourth is the one that matters: there is no
#: value meaning "clamp quietly" or "drop the remainder". A bound that is
#: reached is either refused before a run exists, fails the run, or produces a
#: bounded transition that is recorded with the quantity it refused. A kernel
#: that silently clamped would produce a trajectory nothing in the evidence
#: path could account for, and a later analysis would be right to be confused
#: by it.
BOUND_POLICIES = frozenset({"REFUSED_AT_PARSE", "FAIL_RUN", "BOUNDED_AND_RECORDED"})

#: What each policy commits a kernel to, stated per policy rather than only per
#: case. The cases below say WHICH bound behaves which way; this says what the
#: behaviour is, and the two were not separable before: a reader could see that
#: tank capacity is `BOUNDED_AND_RECORDED` without anything telling them
#: whether the run then continues.
#:
#: `BOUNDED_AND_RECORDED` is the one this slice had to pin. A bound that ended
#: the run would be a disguised run failure, and the policy set already has a
#: separate member for that - `insufficient-fuel` is `FAIL_RUN`. Recording the
#: quantity a transition could not accept only means something if there is a
#: rest of the run for it to be recorded in
#: (`D-2026-09-22-kernel-step-semantics`).
#:
#: A test asserts this covers `BOUND_POLICIES` exactly, so a fourth policy
#: cannot arrive without saying what it does.
BOUND_POLICY_STATEMENTS: dict[str, str] = {
    "REFUSED_AT_PARSE": (
        "The definition is refused when it is read, so no run setup and no "
        "kernel ever sees the value. No run exists, which is why this is the "
        "only one of the three that can be decided without executing "
        "anything."
    ),
    "FAIL_RUN": (
        "The run fails and names the entry that reached the bound. It does not "
        "continue against an adjusted value, because the authored causes and "
        "the world they produced have contradicted each other and continuing "
        "would mean inventing the missing quantity."
    ),
    "BOUNDED_AND_RECORDED": (
        "The transition is applied up to the bound, the run CONTINUES, and "
        "every later cause applies to the bounded value rather than to the "
        "unbounded one it would have reached. The quantity that could not be "
        "accepted is recorded as a bounded transition of its own, carrying "
        "that quantity, so a later analysis can see both what was asked for "
        "and what the world took. There is no silent clamp and no dropped "
        "remainder: those are the same thing without the record."
    ),
}

BOUND_CASES: tuple[BoundCase, ...] = (
    BoundCase(
        case_id="fuel-tank-capacity",
        display_name="Tank capacity",
        policy="BOUNDED_AND_RECORDED",
        statement=(
            "The declared capacity bounds the stored volume at every step. A "
            "transition that would take the volume above it fills to capacity "
            "and records the volume it could not accept as a bounded "
            "transition of its own, carrying the quantity refused."
        ),
    ),
    BoundCase(
        case_id="delivery-overflow",
        display_name="Delivery overflow",
        policy="BOUNDED_AND_RECORDED",
        statement=(
            "A delivery is applied up to the space the tank has and the "
            "remainder is recorded as refused, with its quantity. It is never "
            "discarded silently: a delivery that partly did not fit is a fact "
            "a later analysis has to be able to see, because the alternative "
            "is fuel that arrives in the record and never in the tank."
        ),
    ),
    BoundCase(
        case_id="insufficient-fuel",
        display_name="Insufficient fuel",
        policy="FAIL_RUN",
        statement=(
            "A consumption or removal that would take the stored volume below "
            "zero means the authored causes and the world they produced "
            "disagree. The run fails and names the entry. It does not empty "
            "the tank quietly, because that would invent the missing quantity "
            "out of the model instead of reporting the contradiction."
        ),
    ),
    BoundCase(
        case_id="invalid-rate",
        display_name="Invalid rate or quantity",
        policy="REFUSED_AT_PARSE",
        statement=(
            "A rate or quantity that is negative, infinite, or not a number is "
            "refused when the definition is read, so no run setup and no "
            "kernel ever sees one. This is the only bound case the product "
            "already enforces end to end, because it is the only one that can "
            "be decided without executing anything."
        ),
    ),
)


# --- Initialization and the private-state transition surface ----------------


@dataclass(frozen=True)
class InitializationInput:
    """One initial world value, with the owner that answers for it.

    `value` and `canonical_value` are `None` exactly when the declared owner
    is `SITE_FOUNDATION`, because such a parameter states no number
    (`D-2026-09-22-foundation-value-declaration`). This record is a projection
    of the document and the document genuinely does not know the number: the
    Site does, and run setup is the component entitled to hold a document and
    a resolved Site together.

    `unit` and `dimension` are present either way. What kind of quantity the
    state is remains the scenario's to declare, and it is what run setup
    checks the Foundation's own property against.
    """

    parameter_id: str
    display_name: str
    state_ref: StateRef
    owner: str
    value: float | None
    unit: str
    canonical_value: float | None
    canonical_unit: str
    dimension: str

    @property
    def state_key(self) -> str:
        """The semantic state, without its selector."""
        return self.state_ref.state_key

    @property
    def addressed_key(self) -> str:
        """The canonical spelling of the address this concerns."""
        return self.state_ref.addressed_key


@dataclass(frozen=True)
class StateTransitionInput:
    """One declared change to private world state, and where it came from."""

    event_id: str
    state_ref: StateRef
    direction: str
    parameter_id: str
    canonical_value: float
    canonical_unit: str
    dimension: str
    #: The volume, energy or other accumulated quantity this transition
    #: amounts to once a rate has been applied across its window. Equal to
    #: `canonical_value` for a quantity effect.
    applied_value: float
    applied_unit: str
    applied_dimension: str
    #: Where the transition begins, as an offset from the interval start.
    starts_at_offset: int
    #: The offset at which the transition is complete: its own offset for a
    #: point, the end of its window otherwise. `None` for an interval-wide
    #: entry, which never completes inside the scenario.
    complete_at_offset: int | None

    @property
    def state_key(self) -> str:
        """The semantic state, without its selector."""
        return self.state_ref.state_key

    @property
    def addressed_key(self) -> str:
        """The canonical spelling of the address this concerns."""
        return self.state_ref.addressed_key


def _all_parameters(scenario: ScenarioDefinition) -> dict[str, ScenarioParameter]:
    """Every public parameter in the document, by identity.

    Parameter identities are unique across the whole document, enforced by the
    parser, so a state effect that names one names exactly one thing.
    """
    found: dict[str, ScenarioParameter] = {
        parameter.parameter_id: parameter
        for parameter in scenario.public_parameters
    }
    for entry in scenario.timeline:
        for parameter in entry.parameters:
            found[parameter.parameter_id] = parameter
    return found


def initialization_inputs(
    scenario: ScenarioDefinition,
) -> tuple[InitializationInput, ...]:
    """Every initial world value the scenario declares, with its owner.

    Two conditions, and the second is deliberately not a restatement of a
    parser rule. A parameter appears here only if its ownership says it
    initializes AND its role is one of `STATE_CHANGING_ROLES`. The parser
    refuses the combination that would make the second condition matter, so
    this is the layer that keeps holding if that refusal is ever loosened -
    which is exactly what the T018 review found had happened by accident for a
    forcing input.

    A reported observation cannot reach here at all: it carries no ownership
    record, which is the structural form of "a recording may not hide
    initialization".
    """
    inputs: list[InitializationInput] = []

    for parameter in _all_parameters(scenario).values():
        ownership = parameter.ownership
        if ownership is None or not ownership.initializes:
            continue
        if parameter.execution_role not in STATE_CHANGING_ROLES:
            continue
        if parameter.state_ref is None or parameter.unit is None:
            continue
        # A Foundation-owned parameter states no number, by construction
        # (`D-2026-09-22-foundation-value-declaration`), and it still declares
        # an initial world value: the need is what it declares, and run setup
        # resolves the answer from the Site through the profile's binding.
        # Skipping it here on the old float filter would have made the
        # decision's own parameters vanish from initialization, which is the
        # opposite of what it settles.
        if parameter.value is None:
            if ownership.owner != "SITE_FOUNDATION":
                continue
            canonical_value = None
            _, canonical_unit, dimension = canonical_quantity(
                0.0, parameter.unit
            )
            value: float | None = None
        elif isinstance(parameter.value, float):
            value = parameter.value
            canonical_value, canonical_unit, dimension = canonical_quantity(
                parameter.value, parameter.unit
            )
        else:
            continue

        inputs.append(
            InitializationInput(
                parameter_id=parameter.parameter_id,
                display_name=parameter.display_name,
                state_ref=parameter.state_ref,
                owner=ownership.owner,
                value=value,
                unit=parameter.unit,
                canonical_value=canonical_value,
                canonical_unit=canonical_unit,
                dimension=dimension,
            )
        )

    # Sorted by ADDRESS, so two components of one type hold a stable and
    # distinguishable order rather than colliding on one semantic key.
    return tuple(sorted(inputs, key=lambda entry: entry.addressed_key))


def state_transition_inputs(
    scenario: ScenarioDefinition,
) -> tuple[StateTransitionInput, ...]:
    """Every declared change to private world state, in authored order.

    Built only from `CAUSAL_INPUT` entries carrying a state effect. Nothing
    else in the document can reach this list, because no other entry kind has a
    field a state effect could be written in.
    """
    parameters = _all_parameters(scenario)
    transitions: list[StateTransitionInput] = []

    for entry in scenario.timeline:
        effect = entry.state_effect
        if effect is None or entry.state_ref is None:
            continue

        source_id = effect.quantity_parameter_id or effect.rate_parameter_id
        if source_id is None:
            continue
        parameter = parameters.get(source_id)
        if (
            parameter is None
            or parameter.unit is None
            or not isinstance(parameter.value, float)
        ):
            continue

        canonical_value, canonical_unit, dimension = canonical_quantity(
            parameter.value, parameter.unit
        )

        if effect.rate_parameter_id is not None:
            duration = entry.timing.duration_minutes or 0
            applied_value = float(
                _exact(canonical_value) * Fraction(duration)
            )
            applied_dimension = RATE_INTEGRALS[dimension]
            applied_unit = CANONICAL_UNITS[
                _canonical_unit_name(applied_dimension)
            ].canonical_unit
        else:
            applied_value = canonical_value
            applied_unit = canonical_unit
            applied_dimension = dimension

        transitions.append(
            StateTransitionInput(
                event_id=entry.event_id,
                state_ref=entry.state_ref,
                direction=effect.direction,
                parameter_id=parameter.parameter_id,
                canonical_value=canonical_value,
                canonical_unit=canonical_unit,
                dimension=dimension,
                applied_value=applied_value,
                applied_unit=applied_unit,
                applied_dimension=applied_dimension,
                starts_at_offset=entry.offset_minutes,
                complete_at_offset=_complete_at(entry),
            )
        )

    return tuple(transitions)


def _canonical_unit_name(dimension: str) -> str:
    """The authored unit whose canonical form represents a dimension."""
    for unit, canonical in CANONICAL_UNITS.items():
        if canonical.dimension == dimension and canonical.numerator == 1:
            return unit
    raise KeyError(dimension)


def _complete_at(entry: TimelineEntry) -> int | None:
    if entry.timing.shape == "POINT":
        return entry.offset_minutes
    if entry.timing.shape == "WINDOW":
        return entry.offset_minutes + (entry.timing.duration_minutes or 0)
    return None


# --- Reconciling reported observations against the declared causes ----------

#: What a reported observation turned out to be, against the causes the same
#: scenario declares.
#:
#: `ACCOUNTED_FOR` means the declared causal inputs reach the reported value
#: exactly. `NOT_ACCOUNTED_FOR` means they do not, and the difference is
#: reported with its sign so a reader can see which way and by how much.
#: `NOT_RECONCILABLE` means the contract cannot answer, for one of four
#: reasons it names: no declared initial value for the state, a causal window
#: still running when the reading is taken, a declared bound reached before
#: it, or a group of simultaneous causes whose outcome depends on an order the
#: scenario does not declare.
#:
#: The third was the T018 review's finding. Summing every completed transition
#: without consulting a bound reported a declared volume above the capacity
#: the same document declares, under a column headed "declared causes reach" -
#: a number the contract refuses elsewhere. Applying the bound is the kernel's
#: job and out of scope here, so the contract declines to answer instead.
#:
#: The fourth is the same lesson once more, and T019's review found it. An
#: earlier draft of `intra-instant-order` serialised simultaneous causes in
#: authored order and evaluated bounds between them, so a delivery and a draw
#: at one instant could reach a level the tank is never in - an artifact of
#: serialising two things the author declared to happen together. The contract
#: now evaluates the group's net and abstains only when an ordering could
#: genuinely have changed the answer.
#:
#: There is no value meaning "close enough". A reported value that differs from
#: the declared causes differs for a reason, and the reason is either another
#: cause nobody modelled or a reporting behaviour nobody declared. Both are
#: things to decide, not things to round away.
RECONCILIATION_STATES = frozenset(
    {"ACCOUNTED_FOR", "NOT_ACCOUNTED_FOR", "NOT_RECONCILABLE"}
)

#: The reasons, as product copy. Digit-free on purpose: the quantities belong
#: in the record's own columns, and prose that restated them would be a second
#: place for a number to drift.
ACCOUNTED_FOR_REASON = (
    "the causes declared before this reading reach the value it reports"
)
NOT_ACCOUNTED_FOR_REASON = (
    "the causes declared before this reading do not reach the value it "
    "reports, and no declared cause accounts for the difference"
)
NO_DECLARED_INITIAL_VALUE = (
    "no initial value is declared for this state, so there is nothing for the "
    "declared causes to start from"
)
#: Reworded in T020B's correction round, because it had become false.
#:
#: It read "apportioning part of a window would be a transition rule rather
#: than a contract", and `window-ramp` is now exactly a contract statement of
#: how a window apportions - so this string denied what the same module
#: declares two hundred lines up. The reconciler still abstains, and still
#: should: it has no clock and no state, so it cannot evaluate a ramp even
#: though the contract now defines one. What changed is that its reason has to
#: be its own inability rather than a gap in the contract.
OPEN_CAUSAL_WINDOW = (
    "a declared cause is still running when this reading is taken. The contract "
    "states how a window apportions - see the window ramp rule - but this "
    "comparison has no clock and no state to evaluate it with, so it reports "
    "that it cannot answer rather than guessing at the fraction"
)
BOUND_REACHED_UPPER = (
    "a declared cause would take this state above a bound the same definition "
    "declares before the reading. What a run does then is the bounded "
    "transition the bound case names, and computing it belongs to the runtime"
)
BOUND_REACHED_LOWER = (
    "a declared cause would take this state below a bound the same definition "
    "declares before the reading. What a run does then is what the bound case "
    "names, and deciding it belongs to the runtime"
)
ORDER_DEPENDENT_GROUP = (
    "two or more declared causes complete on this state at the same offset, "
    "and whether a bound is reached between them depends on the order they "
    "are applied in. The scenario declares them as simultaneous, so no order "
    "is the true one and the contract will not pick between them. A scenario "
    "that needs one to happen first says so in time, by separating the "
    "offsets"
)

#: The floor every stored quantity has, whether or not a document declares
#: one. The `insufficient-fuel` bound case states it in words - a draw that
#: would take the stored volume below zero - so the contract may rely on it
#: without inventing anything.
IMPLICIT_LOWER_BOUND_DIMENSIONS: dict[str, float] = {"VOLUME": 0.0}


def declared_bounds(
    scenario: ScenarioDefinition,
) -> dict[str, tuple[float | None, float | None]]:
    """The `(lower, upper)` a document declares for each addressed state.

    Keyed on the ADDRESS since T020A1, and on a site with two tanks that is
    the substance of it: the capacity bounding the north tank's volume is the
    north tank's, and a map keyed on `fuel-tank-volume` would have let
    whichever capacity was read last cap both of them.

    Upper bounds come from a `bounds` declaration on an initial world value;
    nothing is inferred from two state keys that happen to share a prefix. The
    lower bound for a stored quantity is the floor the `insufficient-fuel`
    bound case already states in words.

    Everything here is in canonical units, because a bound and the value it
    limits have to be compared in the same terms and an authored unit is not
    guaranteed to be the canonical one.
    """
    lower: dict[str, float] = {}
    upper: dict[str, float] = {}

    for parameter in _all_parameters(scenario).values():
        if parameter.unit is None or not isinstance(parameter.value, float):
            continue

        canonical_value, _, dimension = canonical_quantity(
            parameter.value, parameter.unit
        )

        address = parameter.addressed_key
        if address is not None and dimension in IMPLICIT_LOWER_BOUND_DIMENSIONS:
            lower.setdefault(
                address, IMPLICIT_LOWER_BOUND_DIMENSIONS[dimension]
            )

        bound = parameter.bounds
        if bound is None:
            continue
        if bound.bound_kind == "UPPER":
            upper[bound.state_ref.addressed_key] = canonical_value
        else:
            lower[bound.state_ref.addressed_key] = canonical_value

    return {
        address: (lower.get(address), upper.get(address))
        for address in set(lower) | set(upper)
    }


@dataclass(frozen=True)
class ObservationReconciliation:
    """One reported observation, against the causes declared before it."""

    event_id: str
    source_id: str
    parameter_id: str
    state_ref: StateRef
    offset_minutes: int
    reported_value: float
    declared_value: float | None
    difference: float | None
    unit: str
    state: str
    #: Why the contract answered the way it did. Always present, because a
    #: `NOT_RECONCILABLE` with no reason is four different facts wearing one
    #: name: no declared initial value, an open causal window, a declared
    #: bound reached, and a group of simultaneous causes whose outcome depends
    #: on an order nobody declared are four problems with four different
    #: fixes. The fourth arrived with T019's revised intra-instant rule and
    #: this count did not follow it until the review said so.
    reason: str
    accounted_by: tuple[str, ...]

    @property
    def state_key(self) -> str:
        """The semantic state, without its selector."""
        return self.state_ref.state_key

    @property
    def addressed_key(self) -> str:
        """The canonical spelling of the address this concerns."""
        return self.state_ref.addressed_key


def reconcile_reported_observations(
    scenario: ScenarioDefinition,
) -> tuple[ObservationReconciliation, ...]:
    """Compare each reported observation with the causes declared before it.

    Contract arithmetic over declared quantities, evaluated only at the offsets
    the scenario authored an observation at. It computes no trajectory, holds
    no state, and produces nothing for any other instant. See the module
    docstring: this is not a kernel and must not grow into one.

    A causal effect counts when it is complete at or before the reading. An
    effect whose window is still open when the reading is taken makes the
    reading `NOT_RECONCILABLE`, because apportioning part of a window would be
    a transition rule, and transition rules belong to the kernel.
    """
    parameters = _all_parameters(scenario)
    # Every lookup below is by ADDRESS. Two tanks share one semantic state
    # key, so a map keyed on the key would reconcile the north tank's reading
    # against the south tank's initial value and its causes, and report a
    # discrepancy about a tank nobody touched.
    initial_by_state = {
        entry.addressed_key: entry
        for entry in initialization_inputs(scenario)
    }
    transitions = state_transition_inputs(scenario)
    bounds_by_state = declared_bounds(scenario)

    results: list[ObservationReconciliation] = []

    for entry in scenario.timeline:
        binding = entry.observation
        if binding is None:
            continue
        parameter = parameters.get(binding.reported_parameter_id)
        if (
            parameter is None
            or parameter.state_ref is None
            or parameter.unit is None
            or not isinstance(parameter.value, float)
        ):
            continue

        state_ref = parameter.state_ref
        address = state_ref.addressed_key
        reported_value, reported_unit, _ = canonical_quantity(
            parameter.value, parameter.unit
        )

        initial = initial_by_state.get(address)
        bounds = bounds_by_state.get(address, (None, None))
        relevant = [
            transition
            for transition in transitions
            if transition.addressed_key == address
        ]
        straddling = [
            transition
            for transition in relevant
            if transition.starts_at_offset <= entry.offset_minutes
            and (
                transition.complete_at_offset is None
                or transition.complete_at_offset > entry.offset_minutes
            )
        ]

        def unanswerable(reason: str) -> ObservationReconciliation:
            return ObservationReconciliation(
                event_id=entry.event_id,
                source_id=binding.source_id,
                parameter_id=parameter.parameter_id,
                state_ref=state_ref,
                offset_minutes=entry.offset_minutes,
                reported_value=reported_value,
                declared_value=None,
                difference=None,
                unit=reported_unit,
                state="NOT_RECONCILABLE",
                reason=reason,
                accounted_by=(),
            )

        if initial is None:
            results.append(unanswerable(NO_DECLARED_INITIAL_VALUE))
            continue
        if straddling:
            results.append(unanswerable(OPEN_CAUSAL_WINDOW))
            continue

        applied = [
            transition
            for transition in relevant
            if transition.complete_at_offset is not None
            and transition.complete_at_offset <= entry.offset_minutes
        ]

        lower, upper = bounds

        # Walked instant by instant rather than summed, because a bound is
        # reached at a moment: a delivery that overfills and a draw that
        # empties both land inside the sequence, and a total that happens to
        # come back inside the bounds would hide them.
        #
        # Everything completing at one offset is ONE step, not several. That
        # is the `intra-instant-order` dispatch rule and it is the whole of
        # what this loop assumes about order: nothing here reads the order
        # rows were written in, because that order is authoring rather than
        # physics. Whether it could have mattered is decided exactly, by the
        # two extremes below, and the result of this function does not depend
        # on document order at all.
        declared = _exact(initial.canonical_value)
        reached: str | None = None

        for offset in sorted({item.complete_at_offset for item in applied}):
            group = [
                item for item in applied if item.complete_at_offset == offset
            ]
            increases = sum(
                (
                    _exact(item.applied_value)
                    for item in group
                    if item.direction == "INCREASE"
                ),
                Fraction(0),
            )
            decreases = sum(
                (
                    _exact(item.applied_value)
                    for item in group
                    if item.direction != "INCREASE"
                ),
                Fraction(0),
            )
            after = declared + increases - decreases

            # The net endpoint first. Every ordering reaches it, so a bound
            # broken there is broken however the group is applied, and that is
            # the ordinary bound case rather than an ambiguity.
            if upper is not None and after > _exact(upper):
                reached = BOUND_REACHED_UPPER
                break
            if lower is not None and after < _exact(lower):
                reached = BOUND_REACHED_LOWER
                break

            # Then the two extremes, which bracket every ordering: no ordering
            # peaks above "every increase first" and none troughs below "every
            # decrease first". If neither extreme reaches a bound, no ordering
            # does and the net stands. If either does - one of them or both -
            # the group is ambiguous and the contract will not pick an order.
            #
            # Both is a real case and the statement above names it, because a
            # case a versioned statement leaves unspecified is a case where
            # two conforming kernels may legitimately disagree: a group that
            # overfills applied one way and empties applied the other reaches
            # a bound under every ordering, but not the same bound, so what a
            # kernel does still differs.
            peak = declared + increases
            trough = declared - decreases
            if (upper is not None and peak > _exact(upper)) or (
                lower is not None and trough < _exact(lower)
            ):
                reached = ORDER_DEPENDENT_GROUP
                break

            declared = after

        if reached is not None:
            results.append(unanswerable(reached))
            continue

        difference = _exact(reported_value) - declared

        results.append(
            ObservationReconciliation(
                event_id=entry.event_id,
                source_id=binding.source_id,
                parameter_id=parameter.parameter_id,
                state_ref=state_ref,
                offset_minutes=entry.offset_minutes,
                reported_value=reported_value,
                declared_value=float(declared),
                difference=float(difference),
                unit=reported_unit,
                state="ACCOUNTED_FOR" if difference == 0 else "NOT_ACCOUNTED_FOR",
                reason=(
                    ACCOUNTED_FOR_REASON
                    if difference == 0
                    else NOT_ACCOUNTED_FOR_REASON
                ),
                # Sorted within each instant, because within an instant
                # there is no order to preserve. Across instants the
                # completion offset is the order. Together that makes this
                # tuple - and so the whole record - independent of the order
                # the document happens to list simultaneous entries in, which
                # is what the dispatch rule says and a test measures.
                accounted_by=tuple(
                    transition.event_id
                    for transition in sorted(
                        applied,
                        key=lambda item: (
                            item.complete_at_offset or 0,
                            item.event_id,
                        ),
                    )
                ),
            )
        )

    return tuple(results)


def unaccounted_observations(
    reconciliations: Iterable[ObservationReconciliation],
) -> tuple[ObservationReconciliation, ...]:
    """The reported observations the declared causes do not reach."""
    return tuple(
        result
        for result in reconciliations
        if result.state != "ACCOUNTED_FOR"
    )
