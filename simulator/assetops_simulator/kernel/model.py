"""What a model can do, as a table of executable handlers rather than a claim.

A model profile in `assetops_backend.runs.profiles` DECLARES which world states
a build can model and in which roles. Until T021 nothing could contradict it:
the backlog records that `supported_states` "has no falsifier", so `READY` was
computed from a promise about a kernel that did not exist.

This module is the other side of that. A `ModelSpec` holds one `StateHandler`
per `(state_key, role)` the model can actually consume, each carrying the
callable that consumes it, and `advertised_supported_states` is **derived by
grouping the handler table** rather than written beside it. Deleting a handler
narrows the advertised set; adding an advertised pair without a handler is
unspellable, because there is no field to write one in.

That makes the conformance test in `host/tests` a falsifier rather than a
second declaration: it compares the derived set against the product profile's
own, and it then executes a real frozen run and asserts every advertised pair
was reached. A table that merely agreed with another table would be two
declarations; a table whose every entry is called during an execution is a
claim with evidence under it.

## Two things a handler deliberately holds

`kind` says what sort of thing the handler consumes, because the five are
consumed at different phases and a reader needs to know which: a `STOCK` is
initialized and moved, a `BOUND_SOURCE` supplies a limit, a `COEFFICIENT` is
read by a law, a `FORCING` is read by a law only in the steps its window
concerns, and a `STATE_SAMPLE` answers what the state is at an instant.

A `STOCK` handler also carries its own `floor`. That is
`D-2026-09-22-reconciliation-panel-retirement`'s instruction to this slice: the
kernel takes its floor from the model, never from the validation layer's
`IMPLICIT_LOWER_BOUND_DIMENSIONS`. *Volume is non-negative* is a model rule, so
the model says it, and the simulator cannot reach that constant anyway because
it may not import the backend at all.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Callable

#: The kinds of thing a handler consumes. Five, each consumed at a different
#: phase of the boundary cycle.
HANDLER_KINDS = frozenset(
    {"STOCK", "BOUND_SOURCE", "COEFFICIENT", "FORCING", "STATE_SAMPLE"}
)

#: This kernel's own version, part of every trajectory's identity. A kernel
#: change that could move a number moves this, so a golden trace bound to the
#: old number refuses playback rather than being reinterpreted.
KERNEL_VERSION = 1


@dataclass(frozen=True)
class StateHandler:
    """One `(state_key, role)` this model can consume, and what consumes it.

    `consume` is the callable. It is not decoration: the kernel calls it, the
    value it returns is what enters the world, and the execution ledger records
    that it was called. A handler whose callable is never reached is an
    advertised capability with no evidence, which the conformance test fails on.
    """

    handler_id: str
    state_key: str
    scope: str
    role: str
    kind: str
    statement: str
    consume: Callable[..., object]
    #: For a `STOCK`, the callable that accepts an initial value. Separate from
    #: `consume`, which computes the stock after a change: what a value has to
    #: satisfy to BE a stored volume and what arithmetic moves one are two
    #: questions, and a single callable answering both would have to validate
    #: the candidate a bound check has not yet seen - which would turn every
    #: bound failure into a resolution failure.
    initialize: Callable[..., object] | None = None
    dimension: str | None = None
    floor: Fraction | None = None
    floor_bound_case_id: str | None = None

    def __post_init__(self) -> None:
        if self.kind not in HANDLER_KINDS:
            raise ValueError(
                f"Handler {self.handler_id!r} is of kind {self.kind!r}, and a "
                f"handler consumes one of {sorted(HANDLER_KINDS)}."
            )
        if self.floor is not None and self.kind != "STOCK":
            raise ValueError(
                f"Handler {self.handler_id!r} declares a floor and is not a "
                "STOCK. A floor is a bound on something that persists across "
                "steps; a coefficient or a forcing has nothing to accumulate."
            )
        if (self.kind == "STOCK") != (self.initialize is not None):
            raise ValueError(
                f"Handler {self.handler_id!r} is of kind {self.kind!r} and "
                f"{'declares no' if self.initialize is None else 'declares an'} "
                "initializer. A STOCK is initialized from the frozen run and "
                "nothing else is: a coefficient, a bound and a forcing are read "
                "where they are used."
            )
        if (self.floor is None) != (self.floor_bound_case_id is None):
            raise ValueError(
                f"Handler {self.handler_id!r} has a floor without the bound "
                "case that says what happens when it is reached, or the "
                "reverse. A floor with no policy is a silent clamp waiting to "
                "be written."
            )


@dataclass(frozen=True)
class ModelLaw:
    """One physical relationship this model computes.

    `reads` and `writes` name handler identities rather than state keys, so a
    law cannot read something the model does not declare it can consume - the
    constructor checks it against the spec. That is what stops a law from being
    the place an undeclared capability creeps in.
    """

    law_id: str
    statement: str
    reads: tuple[str, ...]
    writes: tuple[str, ...]
    compute: Callable[..., Fraction]
    direction: str


@dataclass(frozen=True)
class ComponentRelation:
    """One machine this model relates several state keys on.

    A stored volume and the capacity that bounds it are two facts about ONE
    tank; a forced output and a specific fuel consumption are two facts about
    ONE generator. Saying so here is what lets the kernel resolve a law's
    operands without knowing which pack produced the law, and it is what moved
    the fuel-specific pairing out of `kernel/execute.py`, where T021's
    independent review found it.

    `display_name` is how a failure names the relation when the frozen run
    declares none of its states or more than one component carrying them - "no
    fuel tank", or two component ids. A relation with no `display_name` would
    make that failure say a state key instead, which is not what a reader needs
    to know.

    **This is a relation and not a topology.** It says which facts belong to one
    machine, not which machine feeds which. A model that needs the second - which
    tank a given generator burns from - needs a declared connection, and this
    model has none, which is why it relates exactly one of each and fails when a
    frozen run names two.
    """

    relation_id: str
    display_name: str
    state_keys: frozenset[str]
    statement: str


@dataclass(frozen=True)
class AdvertisedState:
    """One state this model advertises, and the roles it advertises it in.

    Derived, never authored. `ModelSpec.advertised_supported_states` builds
    these by grouping the handler table, which is why the set cannot claim a
    role no handler implements.
    """

    state_key: str
    scope: str
    supported_roles: frozenset[str]


@dataclass(frozen=True)
class ModelSpec:
    """One versioned model: its handlers, its laws, and what that adds up to."""

    model_profile_id: str
    model_profile_version: int
    statement: str
    handlers: tuple[StateHandler, ...]
    laws: tuple[ModelLaw, ...]
    component_relations: tuple[ComponentRelation, ...] = ()

    def __post_init__(self) -> None:
        seen: set[str] = set()
        for handler in self.handlers:
            if handler.handler_id in seen:
                raise ValueError(
                    f"Model {self.model_profile_id!r} declares two handlers "
                    f"called {handler.handler_id!r}. A ledger keyed on that "
                    "identity could not tell which of them was reached."
                )
            seen.add(handler.handler_id)

        by_pair: set[tuple[str, str]] = set()
        for handler in self.handlers:
            pair = (handler.state_key, handler.role)
            if pair in by_pair:
                raise ValueError(
                    f"Model {self.model_profile_id!r} declares two handlers "
                    f"for {handler.state_key!r} in role {handler.role!r}. The "
                    "advertised set is derived by grouping this table, so two "
                    "handlers for one pair would be one advertised role with "
                    "two implementations and no rule for which runs."
                )
            by_pair.add(pair)

        scopes: dict[str, str] = {}
        for handler in self.handlers:
            claimed = scopes.setdefault(handler.state_key, handler.scope)
            if claimed != handler.scope:
                raise ValueError(
                    f"Model {self.model_profile_id!r} claims "
                    f"{handler.state_key!r} at both {claimed!r} and "
                    f"{handler.scope!r}. Whether a state is a fact about one "
                    "component or about the installation is a property of the "
                    "state, so it cannot differ between two of its roles."
                )

        for law in self.laws:
            for handler_id in law.reads + law.writes:
                if handler_id not in seen:
                    raise ValueError(
                        f"Law {law.law_id!r} names handler {handler_id!r}, "
                        f"which model {self.model_profile_id!r} does not "
                        "declare. A law may only consume what the model "
                        "advertises, or the advertised set would not be what "
                        "the model actually does."
                    )

        # Every component-scoped state belongs to exactly one relation, and a
        # site-wide one to none. Checked here rather than remembered, because a
        # state in no relation is a state the kernel cannot address a law's
        # operand at, and a state in two is a machine the model cannot identify.
        for handler in self.handlers:
            owning = [
                relation
                for relation in self.component_relations
                if handler.state_key in relation.state_keys
            ]
            if handler.scope == "COMPONENT" and len(owning) != 1:
                raise ValueError(
                    f"Model {self.model_profile_id!r} claims "
                    f"{handler.state_key!r} on a component and "
                    f"{len(owning)} component relation(s) name it. A "
                    "component-scoped state belongs to exactly one machine, "
                    "or nothing can say which asset a law's operand is on."
                )
            if handler.scope == "SITE" and owning:
                raise ValueError(
                    f"Model {self.model_profile_id!r} claims "
                    f"{handler.state_key!r} site-wide and a component relation "
                    "names it. A fact about the installation is not a fact "
                    "about one machine."
                )

    def advertised_supported_states(self) -> tuple[AdvertisedState, ...]:
        """What this model can model, derived from the handler table.

        Sorted by state key, so a comparison against the product profile's
        declaration is about content rather than order.
        """
        roles: dict[str, set[str]] = {}
        scopes: dict[str, str] = {}
        for handler in self.handlers:
            roles.setdefault(handler.state_key, set()).add(handler.role)
            scopes[handler.state_key] = handler.scope
        return tuple(
            AdvertisedState(
                state_key=state_key,
                scope=scopes[state_key],
                supported_roles=frozenset(roles[state_key]),
            )
            for state_key in sorted(roles)
        )

    def advertised_pairs(self) -> frozenset[tuple[str, str]]:
        """Every `(state_key, role)` this model advertises."""
        return frozenset(
            (handler.state_key, handler.role) for handler in self.handlers
        )

    def handler(
        self, state_key: str, role: str, scope: str
    ) -> StateHandler | None:
        """The handler for one state, one role and one SCOPE, or nothing.

        `scope` is not optional and was not a parameter until T021's independent
        review found what its absence did. A reference to
        `site:generator-specific-fuel-consumption` matched the handler for the
        COMPONENT-scoped state of the same name, so a declaration the run had
        explicitly recorded as unsupported at that scope was treated as
        something this model carries - and it invented a second machine out of
        it. Whether a state is a fact about one component or about the
        installation is part of what a handler claims, so it is part of the
        lookup.
        """
        for handler in self.handlers:
            if (
                handler.state_key == state_key
                and handler.role == role
                and handler.scope == scope
            ):
                return handler
        return None

    def relation_of(self, state_key: str) -> ComponentRelation | None:
        for relation in self.component_relations:
            if state_key in relation.state_keys:
                return relation
        return None

    def handlers_of_kind(self, kind: str) -> tuple[StateHandler, ...]:
        return tuple(
            handler for handler in self.handlers if handler.kind == kind
        )

    def handler_by_id(self, handler_id: str) -> StateHandler:
        for handler in self.handlers:
            if handler.handler_id == handler_id:
                return handler
        raise KeyError(handler_id)

    def models_state(self, state_key: str, scope: str | None = None) -> bool:
        """Whether this model claims a state, optionally at one scope only."""
        return any(
            handler.state_key == state_key
            and (scope is None or handler.scope == scope)
            for handler in self.handlers
        )


class ExecutionLedger:
    """Which handlers and laws an execution actually reached.

    The evidence half of the conformance claim. The derived advertised set says
    what the table contains; this says what a real run of a real document
    called. An advertised pair missing from a completed run's ledger is a
    capability nothing exercised, and the conformance test treats that as a
    failure rather than as coverage nobody got round to.
    """

    def __init__(self) -> None:
        self._handlers: list[str] = []
        self._laws: list[str] = []

    def record_handler(self, handler: StateHandler) -> None:
        if handler.handler_id not in self._handlers:
            self._handlers.append(handler.handler_id)

    def record_law(self, law: ModelLaw) -> None:
        if law.law_id not in self._laws:
            self._laws.append(law.law_id)

    @property
    def handlers(self) -> tuple[str, ...]:
        return tuple(self._handlers)

    @property
    def laws(self) -> tuple[str, ...]:
        return tuple(self._laws)

    def pairs_reached(self, model: ModelSpec) -> frozenset[tuple[str, str]]:
        reached = set()
        for handler_id in self._handlers:
            handler = model.handler_by_id(handler_id)
            reached.add((handler.state_key, handler.role))
        return frozenset(reached)
