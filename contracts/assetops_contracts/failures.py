"""Why an execution stopped, as a vocabulary distinct from setup's two.

v4 section 23. Three phases can say no to a run and they are not the same
phase, so they do not share a vocabulary:

- **refusal** happens at run setup, allocates no `run_id`, and lives in
  `assetops_backend.runs.refusals`;
- **blocking** is a fact about a persisted Draft, lives in
  `BLOCKING_REASON_KINDS`, and says the frozen inputs may not execute;
- **execution failure** is what happens while a run is being executed, and is
  the vocabulary here.

`tools/checks` cannot enforce the split, because the three live in packages
that may not import each other. A composing test asserts the three sets are
pairwise disjoint, which is the only place that comparison can be made.

## Every member is reachable, and that is asserted rather than claimed

`OBSERVED_KINDS` records each kind that is ever constructed in a process, and
the simulator suite asserts at the end of the session that every member of
`EXECUTION_FAILURE_KINDS` was reached. A failure vocabulary whose members
cannot be produced is a list of things that look protected, which is the shape
of defect this project has found in guard suites three slices running.

`NOT_COMPARABLE` is deliberately absent. v4 lists it beside these, and it is a
verdict about two runs rather than about one execution: nothing failed, both
runs completed, and the comparison declines. It belongs to the paired
experiment contract, and putting it here would make "execution failed" cover a
case where nothing did.
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: What can stop an execution. Closed, and every member carries a statement.
EXECUTION_FAILURE_KINDS = frozenset(
    {
        "ORDER_DEPENDENT_GROUP",
        "BALANCE_IDENTITY_VIOLATION",
        "PHYSICAL_RESOLUTION_FAILURE",
        "UNSUPPORTED_MODEL_STATE",
        "INTEGRATION_BOUND_FAILURE",
        "TOPOLOGY_INCONSISTENT",
        "INITIAL_STATE_UNANSWERED",
        "FORCING_NOT_AVAILABLE",
        "FORCING_VALUE_AMBIGUOUS",
        "ENTRY_OUTSIDE_INTERVAL",
    }
)

#: What each kind means, and what a reader is being told to look at. A test
#: asserts this covers the vocabulary exactly.
EXECUTION_FAILURE_STATEMENTS: dict[str, str] = {
    "ORDER_DEPENDENT_GROUP": (
        "Two or more causes act on one state at the same instant, and whether "
        "a bound is reached between them depends on the order they are applied "
        "in. The scenario declares them as simultaneous, so no order is the "
        "true one and the kernel will not pick between them. Separating the "
        "offsets in time is what says one happens first."
    ),
    "BALANCE_IDENTITY_VIOLATION": (
        "A step's change in a stock does not equal the flows the world "
        "accepted into and out of it. That is a contradiction inside the "
        "kernel rather than a fact about the scenario, and continuing would "
        "produce a trajectory nothing could be reconciled against."
    ),
    "PHYSICAL_RESOLUTION_FAILURE": (
        "The physical resolver was asked to accept a flow the world cannot "
        "have: a negative dispatched power, or a quantity outside what its "
        "dimension admits. The parser refuses such a value when a document is "
        "read, so reaching this means content arrived without crossing it."
    ),
    "UNSUPPORTED_MODEL_STATE": (
        "The frozen run carries a world state this model has no handler for, "
        "and the run does not record it as an unsupported optional input "
        "either. One of the two has to be true before a kernel may leave a "
        "declared state out, so the run stops rather than silently modelling "
        "part of a scenario."
    ),
    "INTEGRATION_BOUND_FAILURE": (
        "A cause would take a stock past a bound whose policy is to fail the "
        "run. The failure names the entry and the bound case. It does not "
        "continue against an adjusted value, because the authored causes and "
        "the world they produced have contradicted each other."
    ),
    "TOPOLOGY_INCONSISTENT": (
        "The frozen run names more of something than this model can relate. "
        "The narrow fuel model relates one generator to one fuel tank and has "
        "no topology to tell it which tank a second generator burns from, so "
        "it says so rather than pairing whichever it saw first."
    ),
    "INITIAL_STATE_UNANSWERED": (
        "A stock this run changes has no initial value on the frozen run. An "
        "unanswered initial condition never silently becomes zero: a "
        "trajectory beginning from a number nobody supplied is a trajectory "
        "nobody can attribute."
    ),
    "FORCING_NOT_AVAILABLE": (
        "A forcing input this model requires is declared nowhere in the frozen "
        "run, so no window makes it available at any instant. It is not held "
        "at a previous value and it is not taken as zero: both would be a "
        "number the scenario did not supply."
    ),
    "FORCING_VALUE_AMBIGUOUS": (
        "Two declared values force one address in one step, and nothing says "
        "whether they are the two ends of a ramp or two named levels a shape "
        "selects between. The kernel refuses to compose them rather than "
        "inventing one of those two readings."
    ),
    "ENTRY_OUTSIDE_INTERVAL": (
        "A cause or a forcing on the frozen run falls outside the interval the "
        "run covers. Run setup refuses such a document, so reaching this means "
        "the run and the definition it names have drifted apart since it was "
        "frozen."
    ),
}

#: Every kind constructed in this process. See the module docstring: it is what
#: lets a suite prove the vocabulary is reachable rather than decorative.
OBSERVED_KINDS: set[str] = set()


@dataclass(frozen=True)
class ExecutionFailure:
    """One reason an execution stopped, and what it is about.

    `subject` names the address, event or step the failure concerns, for the
    same reason a blocking reason carries one: two failures of one kind are two
    facts rather than one repeated.
    """

    kind: str
    subject: str
    statement: str
    at_offset_minutes: int | None = None
    detail: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.kind not in EXECUTION_FAILURE_KINDS:
            raise ValueError(
                f"{self.kind!r} is not an execution failure. An execution "
                f"stops for one of {sorted(EXECUTION_FAILURE_KINDS)}; a run "
                "that could not be set up is refused and a frozen run that may "
                "not execute is blocked, and those are two other vocabularies."
            )
        OBSERVED_KINDS.add(self.kind)


class KernelExecutionFailed(Exception):
    """Raised with the failure record, for a caller that wants an exception.

    The trajectory carries the same record, so a caller that wants the partial
    result reads it there instead. Both exist because the two callers differ: a
    test asserting a run fails wants to catch something, and the Lab wants to
    show what was produced before it stopped.
    """

    def __init__(self, failure: "ExecutionFailure") -> None:
        super().__init__(f"{failure.kind}: {failure.statement}")
        self.failure = failure


def failure(
    kind: str,
    subject: str,
    *,
    at_offset_minutes: int | None = None,
    detail: tuple[str, ...] = (),
) -> ExecutionFailure:
    """One failure, with the statement read from the vocabulary.

    The statement is never written at the raising site. A message composed
    where it is raised is a message that drifts between two sites meaning the
    same thing, which is what one statement shared by three callers was created
    to stop one layer down.
    """
    return ExecutionFailure(
        kind=kind,
        subject=subject,
        statement=EXECUTION_FAILURE_STATEMENTS[kind],
        at_offset_minutes=at_offset_minutes,
        detail=detail,
    )
