"""The executable meaning of a run, in terms neither side of the barrier owns.

This module is the versioned semantics a conforming kernel implements and the
product publishes: canonical units, half-open dispatch, the boundary cycle,
what a reading timestamped `T` describes, and what a reached bound commits a
kernel to. It moved here from `assetops_backend.scenarios.execution` in T021,
unchanged in content, because the first conforming kernel lives in
`assetops_simulator` and `simulator/` may not import `assetops_backend` at all
(v4 section 3.2, rule 5, and `.ai/ARCHITECTURE.md` Execution Composition And
Truth Barrier).

What stayed behind is everything that reads a `ScenarioDefinition`:
`initialization_inputs`, `state_transition_inputs`, `declared_bounds` and the
reconciliation reference implementation are projections of a product document
and belong to the product domain. What moved is what both sides must agree
about. The backend re-exports every name below, so a product caller still
reads one module and the screen still renders these objects rather than copies
of them.

## The two formulas are executable here, beside the sentences that publish them

`window-overlap` states a predicate and `window-ramp` states a share formula.
Before T021 both existed only as prose in a rule statement, and the backlog
records what that cost: four review rounds in which every failing sentence
restated a subset of what the formula does, and the formula was right each
time. `step_concerns_window` and `window_share_of_step` are those two lines of
arithmetic, in the same module as the statements that describe them, and the
kernel calls them rather than re-deriving them. A kernel that computed its own
overlap could drift from the published sentence; one that calls this cannot.

The sentences still describe rather than define. Where a reader finds a
difference between a statement and one of these two functions, the function is
what a conforming kernel does, and the statement is what needs correcting.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

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
#: ## Six since T021, and it is the frozen run's shape rather than a rule
#:
#: Version five said what a conforming kernel must do. T021 built the first one,
#: and its independent review found that the run it executed did not determine
#: the experiment: a Draft froze the resolved VALUES a scenario declared and left
#: their TIMING in a mutable document, so the same persisted run, at the same
#: scenario version, with one offset moved from 1500 to 1515, produced a tank of
#: 374.02 L where it had produced 334.02 L. Nothing in the run had changed.
#:
#: The fix is that a run now freezes the whole causal projection - what changes,
#: by how much, in which direction, at which resolved address, over which span -
#: and the component that executes one takes the run and nothing else. That is
#: `D-2026-09-21-causal-runtime-before-golden-traces`' requirement that frozen
#: inputs reconstruct the run, applied to the numbers that decide WHEN.
#:
#: It moves the number under `D-2026-09-22-contract-version-scope`'s own test: a
#: run of an unchanged document freezes differently under six than under five, so
#: the resolved identity of the same experiment is different. Version five HAS
#: been published - it is on `main` and local Drafts carry it - so the
#: unreleased-version doctrine does not apply and this is a move rather than an
#: amendment. Every earlier frozen run keeps its own version, stays readable, and
#: is refused execution rather than reinterpreted.
#:
#: Two things in the same slice deliberately did NOT move it, and saying so is
#: part of applying the policy rather than reciting it. The `TRAJECTORY`
#: expectation kind is a pure widening off every executable path. And this
#: module's relocation from `assetops_backend.scenarios.execution` carries
#: identical objects, which the backend re-exports: `is` holds.
#:
#: ## Six was amended in place after a second review, and that is recorded here
#:
#: A second independent pass found four gaps at the boundary a run is frozen at,
#: and they ride on six rather than spending a seven:
#:
#: - a rate was normalized twice, so a millionth of a litre an hour froze as zero.
#:   `frozen_canonical_value` below does the conversion once, in exact arithmetic,
#:   with the integration inside it, and refuses a value the frozen float cannot
#:   carry. The contract already required one-time normalization, so this is an
#:   implementation conforming rather than a rule changing - but it DOES change
#:   what a run freezes for an unchanged document, which is why it is recorded
#:   here rather than treated as invisible;
#: - a record AT version six could omit the projection version six exists to
#:   carry, and executed anyway. That one is a rule: a record at this version
#:   carries it, and a record below may not;
#: - an unanswered magnitude raised instead of freezing absent beside its blocking
#:   reason;
#: - the unsupported-input exclusion applied to an address rather than to an
#:   `(address, role)` pair, so it suppressed a role the model does support.
#:
#: They ride on six because six has never been published: `main` is at five and no
#: run outside this branch carries six. That is the doctrine versions two and five
#: used, and this paragraph is what stops the amendment being invisible after the
#: merge. Once this merges, the next narrowing is a seven.
#:
#: ## Seven since T021A, and it is the narrowest move this ledger records
#:
#: A `REPORTED_OBSERVATION` carries no `execution_requirement`, and a document
#: that declares one is refused. Nothing reads that field on a reading - which is
#: the whole argument for closing the position - so no kernel behaves differently
#: under seven than under six.
#:
#: It moves the number anyway, and the reason is the one
#: `D-2026-09-22-contract-version-scope` settles: the test is DIRECTION against
#: the documents that already exist, not whether an executor's behaviour changes.
#: This NARROWS. The shipped Fuel Loss Event was valid at six with two readings
#: declared `REQUIRED`, and at seven that same document is refused. Runs were
#: frozen against it, and the artifact can no longer be re-derived from a
#: document that parses - which is exactly the situation the number exists to
#: signal at readback.
#:
#: Six IS published: T021 merged to `main` and the local run store carries
#: Drafts at six. So the unreleased-version doctrine that let five's four
#: amendments and two's three ride in place does not apply, and this spends a
#: number rather than amending one. The paragraph above said as much before the
#: merge: "once this merges, the next narrowing is a seven."
#:
#: One thing it deliberately does NOT change, because the narrowing could be
#: mistaken for it: a reading's ADDRESS is still resolved against the Site and
#: still blocks a run it cannot be placed on. What is gone is the support
#: question - whether a profile must model reporting that state - which was
#: asked on behalf of nothing.
#:
#: ## Eight since T022, and it is the reporting path becoming decidable
#:
#: Version seven declared what happens to the world and left the sentence "the
#: device and reporting transform is applied" in the sampling phase as the only
#: thing it said about readings. Two conforming version-seven implementations
#: could therefore disagree about every reading a run produces: whether a sample
#: is due at an instant, what a forced reporting gap does to one, what a consumer
#: sees when nothing fresh arrived, and whether a stochastic publication failure
#: is drawn or chosen. `REPORTING_RULES` below answers all four, and each answer
#: narrows a space a version-seven implementation was free to occupy.
#:
#: It is a move rather than an amendment. Seven IS published - T021A merged to
#: `main` and the local run store carries Drafts at seven - so the
#: unreleased-version doctrine that let five's four amendments and two's three
#: ride in place does not apply. The paragraph above said as much: "once this
#: merges, the next narrowing is a seven", and the same sentence now says eight.
#:
#: It also passes `D-2026-09-22-contract-version-scope`'s own test on the run
#: rather than only on the rules. The publication profile moves to version two in
#: the same slice, because it now declares which devices and signals report which
#: state, at what cadence, with what bias and with what dropout - content a
#: version-one profile did not have. `frozen_inputs_identity` reads the
#: publication profile's version, so a run of an unchanged document freezes a
#: different identity under eight than under seven. The resolved identity of the
#: same experiment is different, which is exactly what spends a number.
#:
#: Two things in the same slice deliberately did NOT move it, and saying so is
#: part of applying the policy rather than reciting it. `LabProjection` is a gated
#: read of what an execution produced, and no executable path consumes one. And
#: the resumable execution handle changes when a caller may look at a boundary,
#: not what any boundary holds: `execute` is that handle advanced to the end, and
#: a test asserts the trajectory it returns is identical to the one a sequence of
#: single steps produces.
#:
#: ## Eight was amended in place after its review, and that is recorded here
#:
#: An independent review returned three defects, and two of them changed what a
#: conforming implementation does. They ride on eight rather than spending a
#: nine, and this paragraph is what stops the amendment being invisible after
#: the merge - the same doctrine versions two, five and six used, and the same
#: condition: **eight has never been published.** `main` is at seven and no run
#: outside this branch carries eight.
#:
#: - **The stochastic draw's identity was not the one v4 section 9.2 names.** It
#:   hashed the domain, the stream, the seed and whatever the caller found
#:   convenient to key on - in practice an address and an offset in minutes -
#:   where the specification names the domain, the seed, the stream name, the
#:   step index and the ordinal, in that order. It was deterministic and
#:   domain-separated and it was a different contract, which is a narrowing of
#:   the space a conforming implementation may occupy and would move a number
#:   under the policy above. `a-publication-failure-is-drawn-not-chosen` now
#:   states the five fields, and `draw_fraction` has no variadic parameter a
#:   sixth could arrive through.
#: - **A reporting-path condition's declared SHAPE was discarded.** Every absent
#:   duration read as the interval's end, so a POINT condition at an instant
#:   became an outage lasting the rest of the run and POINT and INTERVAL_WIDE
#:   collapsed into one meaning.
#:   `reporting-path-conditions-occupy-time-by-their-shape` states what each of
#:   the three shapes covers, which is a space two conforming implementations
#:   could otherwise have split on.
#:
#: The third defect moved nothing: a cadence this run cannot express was already
#: refused by the rule and by the code, and what was wrong was that the refusal
#: escaped an HTTP boundary untranslated. A translation is not a rule.
#:
#: ### And a third amendment, which the second one caused
#:
#: Carrying the shape changed the persisted artifact's schema, and the reader
#: demanded the new field from records written without it. Four completed runs
#: already on disk became an HTTP 500 on the screen that exists to inspect them.
#: This is the fourth time in this milestone that a change correct going forward
#: was silent going backward - frozen runs reinterpreted by a live document, a
#: version guard that could not separate two builds sharing a number, a narrowing
#: that invalidated four authored documents, and now a schema with no reader for
#: its own past - so the backward path is now a published rule rather than
#: something each slice remembers:
#: `a-record-older-than-a-rule-is-read-as-what-it-recorded`. It narrows what a
#: conforming implementation may do with an old result, which is why it is an
#: amendment and not a footnote.
#:
#: **The rule's first implementation broke the rule, and the amendment says so.**
#: The version marker was added by the build that fixed the shape collapse, so
#: the build BEFORE it had written records with the shape on them and no marker.
#: Assigning every unmarked record to the oldest known shape threw that shape
#: away and printed a note saying it had never been recorded - while it sat in
#: the same file. A version marker is itself a rule change and cannot name what
#: predates it; the shapes that predate it are identified from what they carry.
#: That is now part of the rule rather than a lesson in a commit message, because
#: this is the fifth time in this milestone that a correction was right going
#: forward and silent going backward, and the fourth was the fix for the third.
#:
#: Once this merges, the next narrowing is a nine.
EXECUTION_CONTRACT_VERSION = 8


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
            "span excludes. Which steps it is available to is the overlap rule "
            "and nothing else: every step that concerns the window, which for "
            "an aligned window is every step from the one beginning at its "
            "offset up to but not including the one beginning at its end. A "
            "step the window covers only in part is exposed to the forcing for "
            "that part of the step and no longer: nothing stretches the forcing "
            "across the rest of that step, and nothing blends it with a value "
            "the window does not declare. So a REQUIRED forcing is available in "
            "whichever steps the predicate selects, however brief its window, "
            "rather than silently concerning no step at all - and how many "
            "those are is the predicate's answer, stated once in the overlap "
            "rule and not restated here. Two adjacent short forcings may "
            "therefore be available in the same step, each over its own portion "
            "of it, which is the partial-exposure rule and not an exception to "
            "it."
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


# --- The reporting path -----------------------------------------------------
#
# What the sampling phase's "the device and reporting transform is applied"
# actually commits an implementation to. Until T022 that sentence was the whole
# of it, and it decided nothing: two conforming kernels could have disagreed
# about every reading a run produced. These rules are what version eight
# narrows, and each of them is a question somebody had to answer before a
# reading could be generated at all.
#
# The rules above are about what a reading MEANS once it exists - a stock at T,
# a rate over the span ending at T. These are about WHETHER it exists. Keeping
# the two sets apart is deliberate: a timing convention and a reporting policy
# are different kinds of statement, and one tuple holding both would invite a
# consumer to treat a cadence as a fact about the world.


@dataclass(frozen=True)
class ReportingRule:
    """One rule about whether, and as what, a reading reaches a consumer."""

    rule_id: str
    display_name: str
    statement: str


def sample_due_at(offset_minutes: int, cadence_minutes: int) -> bool:
    """`reporting-cadence-is-counted-from-the-interval-start`, exactly.

    Here as arithmetic beside the sentence that publishes it, for the reason the
    two dispatch formulas are: a transform that computed its own due-ness could
    drift from the published rule, and one that calls this cannot.
    """
    if cadence_minutes <= 0:
        raise ValueError(
            f"A cadence of {cadence_minutes} minutes is not a cadence. How "
            "often a reading is published is a span of non-zero length."
        )
    return offset_minutes % cadence_minutes == 0


def cadence_is_expressible(cadence_minutes: int, timestep_minutes: int) -> bool:
    """Whether every instant a cadence is due at is a boundary of the run.

    `cadence-must-divide-the-timestep`, as the one line that decides it. False
    means some sample would be due between two boundaries, which is the case the
    rule refuses rather than rounds.
    """
    if timestep_minutes <= 0:
        raise ValueError(
            f"A step of {timestep_minutes} minutes is not a step. A run walks "
            "its interval in spans of non-zero length."
        )
    return sample_due_at(cadence_minutes, timestep_minutes)


REPORTING_RULES: tuple[ReportingRule, ...] = (
    ReportingRule(
        rule_id="reporting-cadence-is-counted-from-the-interval-start",
        display_name="When a sample is due",
        statement=(
            "A configured signal's sample is due at every instant whose offset "
            "from the start of the run's interval is a whole multiple of its "
            "declared cadence, and at no other instant. `sample_due_at` is that "
            "line of arithmetic and is what a conforming transform calls. The "
            "origin is the interval's start rather than the first reading or the "
            "first event, because those are properties of the content and a "
            "cadence is a property of the path: two runs of one document over "
            "two intervals would otherwise publish on two grids."
        ),
    ),
    ReportingRule(
        rule_id="cadence-must-divide-the-timestep",
        display_name="A cadence the run's resolution cannot express",
        statement=(
            "A sample is due at an instant, and the only instants an execution "
            "has are its boundaries. A declared cadence that is not a whole "
            "multiple of the run's timestep is therefore refused, naming the "
            "signal and the two numbers. It is not moved to the nearest "
            "boundary, which would report a value at a time it was not taken, "
            "and it is not quietly skipped, which would turn a declared cadence "
            "into a different one. A timestep is chosen at run setup, so this is "
            "a run that cannot express its own publication profile rather than a "
            "profile that is wrong."
        ),
    ),
    ReportingRule(
        rule_id="a-reporting-gap-suppresses-the-sample",
        display_name="A forced reporting gap",
        statement=(
            "While a reporting-path condition forces a signal's path unavailable "
            "across its declared window, a sample due inside that window "
            "produces no reading at all. Nothing is sampled, nothing is "
            "published, and no value is invented for the instant. The window's "
            "membership is the half-open one every span in this contract uses, so "
            "the instant reporting resumes is exactly the instant the window "
            "excludes. **The world is not affected**: a condition on the path "
            "changes no stock, no flow and no bound, which is why the "
            "publication profile answers for it and why it is not a forcing on a "
            "world state. A gap therefore makes a real event unreportable rather "
            "than making it not happen, and a consumer looking only at readings "
            "cannot see what the world did inside one."
        ),
    ),
    ReportingRule(
        rule_id="an-interval-reading-is-a-mean-over-the-span",
        display_name="What an interval reading publishes",
        statement=(
            "An interval reading publishes the mean of the measured quantity over "
            "the span that ended at its timestamp, in the signal's own unit - so "
            "an accumulated 11.25 kWh over a fifteen-minute span is published as "
            "45 kW. The span is the run's timestep and never the signal's "
            "cadence: `interval-signal-describes-the-preceding-interval` says "
            "which interval a reading at T describes, and a signal publishing "
            "hourly at a fifteen-minute timestep therefore publishes a "
            "measurement of the last fifteen minutes, once an hour. **This build "
            "declares the mean and not the accumulation**, because a rate signal "
            "is what it has: a signal that needs the accumulated quantity reopens "
            "this rule with a reason on the record rather than by a reader "
            "assuming the other convention."
        ),
    ),
    ReportingRule(
        rule_id="reporting-path-conditions-occupy-time-by-their-shape",
        display_name="How long a forced reporting outage lasts",
        statement=(
            "A reporting-path condition occupies time by the SHAPE the document "
            "declared, and the three shapes are the three every other entry has. "
            "A WINDOW covers its offset up to but not including its offset plus "
            "its declared length. An INTERVAL_WIDE entry holds until the run "
            "interval ends, which `interval-wide-span` already says of every "
            "interval-wide entry. A POINT covers the one step whose half-open "
            "span contains its offset - `point-applied-once`, unchanged - and "
            "because a cadence is a whole multiple of the timestep that span "
            "holds at most one due sample, which is what makes a point outage an "
            "instant rather than a stretch. **A shape a conforming "
            "implementation does not read is a shape it gets wrong**: reading "
            "every absent duration as the interval's end collapses POINT and "
            "INTERVAL_WIDE into one meaning and turns a declared instant into a "
            "run-long outage, which is a different experiment from the one the "
            "document describes. A WINDOW declaring no length is refused rather "
            "than read as either."
        ),
    ),
    ReportingRule(
        rule_id="a-record-older-than-a-rule-is-read-as-what-it-recorded",
        display_name="What happens to results a rule change left behind",
        statement=(
            "A persisted execution result written before a rule changed is read "
            "as the result it is, not re-derived under the new rule and not "
            "refused for lacking a field the old rule had no name for. Where the "
            "old rule was a function of fields the record still carries, what it "
            "resolved is recoverable exactly, and the record shows that resolved "
            "value and says it was recorded rather than declared. What the record "
            "cannot supply is not invented: a shape that was never written down "
            "is reported as absent, never guessed from the span it produced. "
            "Where even the resolved value is not recoverable, the record is "
            "reported as unreadable, naming the schema it was written in and the "
            "field that is missing - which is an answer a reader can act on, "
            "unlike an error escaping the surface that was meant to show it. "
            "**Rewriting, re-executing or discarding the record are all refused**: "
            "an old result silently replaced by a new one is the loss this rule "
            "exists to prevent, and it is worse than the gap it would paper over. "
            "Every persisted result therefore states the schema version it was "
            "written in, so a reader decides which rule applied by reading it "
            "rather than by noticing that a key is absent. **And a reader must "
            "also identify the results written before that marker existed, from "
            "what those results carry.** A version marker is itself a rule "
            "change, so it cannot name the shapes that predate it; an "
            "implementation that assigns every unmarked record to the oldest "
            "shape it knows will discard fields those records genuinely hold, "
            "which is this rule broken by the mechanism meant to keep it. Where "
            "the unmarked shapes are told apart by what they contain, they are "
            "told apart that way; where a record matches none of them, it is "
            "reported as unreadable rather than assigned to the nearest. A "
            "confident wrong reading is worse than the error it replaced, "
            "because an error is an honest answer."
        ),
    ),
    ReportingRule(
        rule_id="a-retained-reading-carries-its-own-time",
        display_name="What a consumer sees when nothing fresh arrived",
        statement=(
            "At an instant where a signal published nothing - not due, "
            "suppressed, dropped, or with nothing to read - a consumer retaining "
            "the newest reading it has shows that reading's OWN source time and "
            "says the value is stale. It is not restamped to the present instant, "
            "it is not interpolated towards the present value, and it is not "
            "reported as an absence: it is a real number, published at a real "
            "instant, which no longer describes now. Where no reading has ever "
            "been published on that signal there is nothing to retain and the "
            "value is unavailable, which is a different statement from stale and "
            "is kept as one."
        ),
    ),
    ReportingRule(
        rule_id="a-publication-failure-is-drawn-not-chosen",
        display_name="A dropped publication",
        statement=(
            "Where a publication profile declares that a share of a signal's due "
            "samples do not publish, which samples those are is DRAWN rather "
            "than chosen, and the draw's identity is the one v4 section 9.2 "
            "names: the reserved stochastic domain `assetops-sim-rng-v1`, the "
            "run's seed, a stream name, the step index, and the draw's ordinal "
            "within that step - in that order, over a canonical length-prefixed "
            "encoding. **Those fields and no others.** An address, a timestamp, "
            "or anything else a particular mechanism finds convenient to key on "
            "would be a different draw contract wearing the same domain, and a "
            "test that recomputed whatever the implementation chose would "
            "establish determinism rather than conformance. It is therefore "
            "reproducible - the same run drops the same samples in every process "
            "- and independent: a draw is a function of those fields and not of "
            "how many draws preceded it, so introducing a second stochastic "
            "mechanism changes no existing stream's draws. A sequential "
            "generator would satisfy the first and break the second, which is "
            "why the family and the keying are declared rather than left to an "
            "implementation."
        ),
    ),
    ReportingRule(
        rule_id="reporting-parameters-move-no-world-quantity",
        display_name="What a reporting parameter may and may not change",
        statement=(
            "A cadence, a bias and a dropout change which readings exist and what "
            "they say. They change no stock, no accepted flow, no bound and no "
            "controller-local input, so two runs of one document differing only "
            "in them produce the same trajectory and the same world identity. A "
            "declared bias is applied to the reported value and nowhere else, "
            "which is what makes the difference between the true value and the "
            "reported one a property of the instrument rather than of the "
            "installation."
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




# --- The two dispatch formulas, executable ----------------------------------
#
# `window-overlap` and `window-ramp` above state these in words. Here they are
# as arithmetic, so the kernel and the sentence cannot disagree about a number.
#
# Every argument is a whole number of minutes, which is the grain a scenario
# offset, a window length and a run timestep are all authored in. Nothing here
# is approximate: a share is a `Fraction` and the shares over the steps a
# window concerns sum to exactly one.


def window_span(offset_minutes: int, length_minutes: int) -> tuple[int, int]:
    """The half-open span `[offset, offset + length)` a window occupies."""
    if length_minutes <= 0:
        raise ValueError(
            f"A window covering {length_minutes} minutes has no span. A window "
            "with zero or negative length is not a window, and `point-applied-"
            "once` is the rule for something that happens at an instant."
        )
    return offset_minutes, offset_minutes + length_minutes


def overlap_minutes(
    step_start: int, timestep_minutes: int, offset_minutes: int, length_minutes: int
) -> int:
    """How many minutes of the step `[s, s+dt)` the window covers.

    `max(s, o) < min(s+dt, o+length)` is `window-overlap`'s predicate, and this
    is the length of the stretch that comparison is about. Zero means they do
    not meet - including the case where they touch at one instant, which is a
    shared stretch of zero length and is what makes a window and the step
    beginning at its end disjoint.
    """
    start, end = window_span(offset_minutes, length_minutes)
    if timestep_minutes <= 0:
        raise ValueError(
            f"A step of {timestep_minutes} minutes is not a step. A run walks "
            "its interval in spans of non-zero length."
        )
    shared = min(step_start + timestep_minutes, end) - max(step_start, start)
    return shared if shared > 0 else 0


def step_concerns_window(
    step_start: int, timestep_minutes: int, offset_minutes: int, length_minutes: int
) -> bool:
    """`window-overlap`, exactly: the two spans share a non-zero stretch.

    This is the whole of which steps a window concerns and it asks nothing of
    alignment. It is never replaced by reasoning from the window's length: a
    two-minute window concerns one step when it lies inside one and two when a
    step boundary falls inside it, and both answers come from this line.
    """
    return (
        overlap_minutes(step_start, timestep_minutes, offset_minutes, length_minutes)
        > 0
    )


def steps_concerning_window(
    interval_minutes: int,
    timestep_minutes: int,
    offset_minutes: int,
    length_minutes: int,
) -> tuple[int, ...]:
    """Every step start in `[0, interval)` that concerns this window.

    Found by evaluating the predicate at each step start, in order, rather than
    by dividing the window's length by the timestep.
    """
    return tuple(
        step_start
        for step_start in range(0, interval_minutes, timestep_minutes)
        if step_concerns_window(
            step_start, timestep_minutes, offset_minutes, length_minutes
        )
    )


def window_share_of_step(
    step_start: int, timestep_minutes: int, offset_minutes: int, length_minutes: int
) -> Fraction:
    """`window-ramp`'s share: the portion of the window this step covers.

    `(min(s+dt, o+length) - max(s, o)) / length`, as an exact ratio. A step the
    window does not concern gets exactly zero, and the shares over the steps it
    does concern sum to exactly one - which is what makes a declared quantity
    move in full whatever timestep a run chooses.
    """
    return Fraction(
        overlap_minutes(
            step_start, timestep_minutes, offset_minutes, length_minutes
        ),
        length_minutes,
    )


def point_due_at(
    step_starts: tuple[int, ...], timestep_minutes: int, offset_minutes: int
) -> int | None:
    """The step start a point entry is applied at, or nothing if it is outside.

    `point-applied-once`: the one step whose half-open span contains the
    offset, applied at the start of that step. An offset falling exactly on a
    step boundary belongs to the step that begins there.
    """
    for step_start in step_starts:
        if step_start <= offset_minutes < step_start + timestep_minutes:
            return step_start
    return None


# --- Exact arithmetic at the input boundary ---------------------------------


def normalize_authored_float(value: float) -> Fraction:
    """One authored decimal as the rational the author wrote.

    The `EXACT_RATIONAL` input boundary of v4 section 8.3, and the only place a
    denominator is ever limited. A kernel calls this once per authored number
    and then does `Fraction` arithmetic; calling it after an integration step
    would repeatedly approximate the world and make "exact rational runtime"
    false.

    It is the same function `canonical_quantity` above uses, exported under the
    name that says what it is for, so a kernel does not reach for a private
    helper to get the boundary behaviour right.
    """
    return _exact(value)


def canonical_fraction(value: float, unit: str) -> tuple[Fraction, str, str]:
    """An authored quantity in canonical terms, as an exact ratio.

    `canonical_quantity` answers the same question in `float`, because what it
    feeds is a screen and a JSON payload. This answers it in `Fraction`,
    because what it feeds is arithmetic that may not round. Both call the same
    conversion table and the same input-boundary normalization, so the number a
    kernel integrates and the number a screen shows are the same number.

    Raises:
        KeyError: the unit has no canonical conversion.
    """
    canonical = CANONICAL_UNITS[unit]
    converted = _exact(value) * Fraction(
        canonical.numerator, canonical.denominator
    )
    return converted, canonical.canonical_unit, canonical.dimension


class CanonicalValueNotRepresentable(Exception):
    """An exact value cannot survive the float a frozen record carries.

    The numeric policy allows exactly one approximation: an authored decimal
    becomes the rational the author wrote, once, at the input boundary. A frozen
    record then stores that rational as a `float`, and for every number this
    product has ever frozen the round trip back through
    `normalize_authored_float` recovers it - because `limit_denominator`
    recovers any rational whose denominator is within its limit.

    It does not recover one whose denominator is outside it, and that is what
    this exists for. A rate of a millionth of a litre an hour is 1/60000000 of a
    litre a minute; the float is fine and normalizing it back gives ZERO. The
    alternative to refusing is a frozen run carrying a number that is not the
    number the document declared, which is the one thing `EXACT_RATIONAL` is
    supposed to rule out.
    """


def frozen_canonical_value(
    value: float, unit: str, *, times: Fraction = Fraction(1)
) -> tuple[float, str, str]:
    """An authored quantity as the `float` a frozen record may carry.

    One conversion, one normalization, and a checked round trip.

    `times` multiplies the canonical value before it is frozen, which is how a
    rate declared over a window becomes the quantity it moves: 14 L/h over four
    hours is exactly 56 L. It is a parameter rather than something a caller does
    afterwards because **doing it afterwards is the defect this replaces.** The
    projection used to call `canonical_quantity`, which normalizes and returns a
    float, and then normalize that float again before multiplying - so a
    millionth of a litre an hour became a float of 1.67e-08, was normalized to
    zero, and a valid removal reported COMPLETED having moved nothing. One-time
    normalization was the rule and something normalized twice.

    Raises:
        CanonicalValueNotRepresentable: the exact value does not survive the
            float. Refusing is the only honest answer: the record has one number
            field and the true value is not among the numbers it can hold.
    """
    exact, canonical_unit, dimension = canonical_fraction(value, unit)
    exact = exact * times
    frozen = float(exact)
    if normalize_authored_float(frozen) != exact:
        raise CanonicalValueNotRepresentable(
            f"{value} {unit} is exactly {exact.numerator}/{exact.denominator} "
            f"in canonical terms, and the {frozen} a frozen record would carry "
            f"reads back as "
            f"{normalize_authored_float(frozen).numerator}/"
            f"{normalize_authored_float(frozen).denominator}. A frozen run may "
            "not carry a number that is not the number the definition "
            "declared, so this is refused rather than frozen approximately."
        )
    return frozen, canonical_unit, dimension


#: The arithmetic every step of a conforming kernel is done in, named so a
#: trajectory can say which policy produced it. v4 section 8.3.
NUMERIC_POLICY = "EXACT_RATIONAL"
NUMERIC_POLICY_VERSION = 1
