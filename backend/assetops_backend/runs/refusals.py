"""Why a run setup request is refused, and the line refusal sits on.

This is the load-bearing distinction in T019 and it is stated once, here.
Everywhere else points at this file; the last round let a second, sharper
copy grow in `runs/service.py` while this one went stale, which is the worst
of both - two statements, and the one calling itself canonical was the wrong
one.

**The discriminator is who failed to answer**, settled at the T019 user
review and shared with T020A:

- the scenario's **declared owner** has no answer, so nothing can be frozen
  and no profile would help: **refuse**;
- the **selected profile** cannot answer, so a different profile would:
  persist a **`BLOCKED`** Draft.

**A refusal means the request could not be frozen.** Something it names does
not exist, is not well formed, or contradicts something else it names. No
`run_id` is allocated, nothing is written, and there is nothing afterwards to
inspect: the run does not exist, so it has no state to be in.

**`BLOCKED` means everything was frozen and the run still must not execute.**
The request was structurally complete, the Draft exists, it is persisted, and
it carries the reasons the selected profile cannot execute it - including a
value the profile could not supply or locate, which the frozen identity
records as absent. Those reasons live in `BLOCKING_REASON_KINDS` and are a
property of a run that exists.

The two must not be collapsed in either direction. A refusal that persisted a
run would put a record in the store that names inputs nobody could resolve; a
`BLOCKED` run returned as a refusal would lose the frozen inputs a reader has
to be able to inspect in order to decide what to change - and, since the fix
for every blocking reason is to choose a different profile, would leave them
no way to tell which one to try.

The kinds below are the refusal half. Each is a different fact with a
different fix, which is why they are ten rather than one with a message: a
malformed interval and a Site that is not configured are not the same problem
and do not lead a reader to the same place.

One of them is about an initial world value: `INITIALIZATION_INPUT_MISSING`,
the `RUN_OVERRIDE` a request did not supply. It is one rather than two since
T020A, because the contradiction that was the second - two different answers
for one value - can no longer be authored. What the pair established survives
the retirement: **an absence and a contradiction are not the same shape**, and
that is why one side of the line can persist a Draft and the other cannot.
Naming both `INITIALIZATION_INPUT_MISSING` made the kind wrong about the case
it mostly covered and put it one word from the blocking
`INITIAL_VALUE_NOT_RESOLVED`, on the other side of a line this file exists to
keep visible.
"""

from __future__ import annotations

#: - `REQUEST_INVALID`: the request is not a well-formed setup request - a
#:   missing field, a wrong type, an unknown key, a malformed identity, a
#:   timestep or seed outside its bounds.
#: - `VERSION_UNAVAILABLE`: the Site, the scenario, or a profile it names
#:   does not exist at the version it names. Naming a version that is not
#:   there is not the same as naming nothing.
#: - `INTERVAL_INVALID`: the interval is malformed, or a scenario entry falls
#:   outside it. `DISPATCH_RULES` already commits the product to refusing the
#:   second and naming the entry rather than quietly leaving it out.
#: - `TIMEZONE_NOT_IANA`: the target Site's time zone is not a real zone, so
#:   the run could not be placed in local time.
#: - `TIMEZONE_DATABASE_UNAVAILABLE`: the zone database could not be read, so
#:   nothing is known about the Site's time zone. Deliberately not the same
#:   fact as the one above.
#: - `TARGET_TOPOLOGY_UNSUPPORTED`: the selected Site cannot host this
#:   scenario because its Foundation declares no topology for the scenario's
#:   causes to sit in. Since `D-2026-10-01-run-binds-scenario-to-site` a site
#:   is never refused for not being one the scenario document names.
#: - `COMPONENT_OR_SIGNAL_UNRESOLVED`: a declared observation source names a
#:   device or a signal this Site's Foundation does not configure.
#: - `INITIALIZATION_INPUT_MISSING`: an initial world value whose DECLARED
#:   OWNER did not answer. Today that is one case: a `RUN_OVERRIDE` value the
#:   request did not supply. Nothing is there, and no profile can put it
#:   there, so the run would have to invent a number - the thing a frozen
#:   identity exists to stop. A value the selected PROFILE could not supply
#:   or locate is NOT here: that blocks, because a different profile would
#:   answer.
#:
#: `INITIAL_VALUE_ANSWERS_DISAGREE` was here and is retired. It named an
#: initial world value with TWO answers - a Foundation rating against the
#: number the scenario stated the Foundation declares - and it had exactly one
#: producer. After `D-2026-09-22-foundation-value-declaration` no document can
#: state that number, so nothing can produce the kind, and it went with its
#: producer under `D-2026-09-22-expiry-follows-the-condition`. A vocabulary
#: member nothing can produce claims a failure mode that cannot occur.
#:
#: Its structural argument survives it and is worth keeping: an absence and a
#: contradiction are different shapes, and only one of them is something a
#: frozen identity can hold. What changed is that the contradiction can no
#: longer arise, so **every failure of a Foundation-owned value now blocks and
#: none refuses**. A reader meeting that should not take it for an oversight.
#: - `UNIT_INVALID`: a supplied value carries a unit the contract does not
#:   know, a unit the parameter does not use, or a quantity the `invalid-rate`
#:   bound case refuses.
#: - `EXECUTION_REQUIREMENT_CONFLICT`: the scenario declares one RESOLVED
#:   address and role at two requirement levels, so it states two answers to
#:   whether that input must be modelled. A CONTRADICTION and not an absence,
#:   which is what puts it on this side of the line: whichever level were
#:   frozen would be one the product chose rather than one the document
#:   states. Until T020B the stricter level won silently, which turned an
#:   author's mistake into the product's behaviour and made a lowered
#:   requirement unobservable wherever a second position still said `REQUIRED`
#:   (`D-2026-09-22-forcing-state-requirements`, rider one). Two levels on one
#:   AUTHORED address are refused earlier still, by the scenario parser, and
#:   never reach a run; what reaches here is two spellings that resolve to one
#:   address, which cannot be seen without the Site that resolves them.
RUN_SETUP_REFUSAL_KINDS = frozenset(
    {
        "REQUEST_INVALID",
        "VERSION_UNAVAILABLE",
        "INTERVAL_INVALID",
        "TIMEZONE_NOT_IANA",
        "TIMEZONE_DATABASE_UNAVAILABLE",
        "TARGET_TOPOLOGY_UNSUPPORTED",
        "COMPONENT_OR_SIGNAL_UNRESOLVED",
        "INITIALIZATION_INPUT_MISSING",
        "UNIT_INVALID",
        "EXECUTION_REQUIREMENT_CONFLICT",
        # T026 (`D-2026-10-02-delay-is-a-reporting-path-cause`). A declared
        # publication hold that would hold more than one publication of a path
        # and release them together. Release order, buffering and recovery are
        # T026A's, so such a hold is refused rather than modelled.
        "PUBLICATION_DELAY_REFUSED",
        # S1-01: the Site was imported into the product Foundation store, and
        # the Lab cannot set up against it until it uses the registered
        # Foundation and gateway snapshot.
        "SITE_AWAITING_MIGRATION",
        # S2-01a (D-2026-10-08-s2-lab-snapshot-selection-and-run-boundary):
        # no registered Foundation + SignalBinding basis can be selected for
        # an imported Site at the requested source start and knowledge
        # instant - never registered then, content gaps, a current gap on a
        # current basis, missing bytes, a hash mismatch or an unsupported
        # schema. The message names the specific reason; nothing falls back
        # to the YAML Site or another revision.
        "REGISTERED_BASIS_UNAVAILABLE",
        # S2-01a: the selected basis's original validity ends inside the run
        # interval or exactly at its end_time, where the kernel can still
        # stamp a public reading. One run cites one basis.
        "REGISTERED_BASIS_BOUNDARY",
        # S2-01b (D-2026-10-08-s2-simulated-device-resolution-and-delay-boundary):
        # a publication profile whose simulated device resolution is stated
        # against registered binding source units, selected for a Site with
        # no registered basis to check it against.
        "PUBLICATION_PROFILE_REQUIRES_REGISTERED_SITE",
        # S2-01b: a declared device resolution's unit differs from the
        # registered binding's source unit for that signal. Nothing rounds in
        # a unit the binding does not publish.
        "PUBLICATION_UNIT_MISMATCH",
        # DIESEL-1-R3f §9f.2 (8): a request naming an operational-action log.
        # Named on a cold or EV document draft, or a legacy YAML Site: only a
        # registered timeline run takes operational actions.
        "OPERATIONAL_ACTIONS_UNSUPPORTED_PATH",
        # No log port is wired, or the named log file is missing or unreadable.
        "OPERATIONAL_ACTION_LOG_UNAVAILABLE",
        # The log's document has a missing, unknown or mistyped key.
        "OPERATIONAL_ACTION_LOG_INVALID",
        # The log's inner id, version or site code differs from what was named.
        "OPERATIONAL_ACTION_LOG_MISMATCH",
        # An action names a component the run's Site does not have.
        "OPERATIONAL_ACTION_COMPONENT_UNKNOWN",
        # The model has no CAUSAL_INPUT stock for the action's state, or the run
        # froze no initial tank volume or tank capacity to bound it by.
        "OPERATIONAL_ACTION_STATE_NOT_CAUSAL",
        # The model's stock is not in litres. Reachable only by a model profile (or scenario id grammar) not
        # shipped today; tested by a direct loader call.
        "OPERATIONAL_ACTION_UNIT",
        # An action's physical span is not wholly inside the run, or is not
        # aligned the way a scenario entry must be.
        "OPERATIONAL_ACTION_SPAN_OUTSIDE_RUN",
        # Initial stock plus the run's deliveries so far exceeds the tank's
        # frozen capacity: refused, never clamped.
        "OPERATIONAL_ACTION_OVER_CAPACITY",
        # A removal exceeds initial stock plus the run's earlier deliveries.
        "OPERATIONAL_ACTION_OVER_STOCK",
        # An action's event id equals one already frozen from the scenario. Reachable only by a model profile
        # (or scenario id grammar) not shipped today; tested by a direct loader call.
        "OPERATIONAL_ACTION_EVENT_ID_CONFLICT",
    }
)


class RunSetupRefused(Exception):
    """One run setup request, refused, with no run allocated.

    The message is product copy: a developer configuring a run meets it, so it
    names what is wrong and what would be acceptable instead. The kind is what
    a client switches on, so neither has to be parsed out of the other.
    """

    def __init__(self, kind: str, message: str, *, reason_code: str | None = None) -> None:
        if kind not in RUN_SETUP_REFUSAL_KINDS:
            raise ValueError(
                f"{kind!r} is not a run setup refusal kind. Add it to "
                "RUN_SETUP_REFUSAL_KINDS with what it means, rather than "
                "reporting a new fact under an existing name."
            )
        super().__init__(message)
        self.kind = kind
        self.message = message
        #: S2-01a: the specific registered-basis reason under a
        #: `REGISTERED_BASIS_*` kind (for example
        #: `ACQUISITION_SNAPSHOT_HASH_MISMATCH`), so a client need not parse
        #: the message. None for every other refusal.
        self.reason_code = reason_code


def refuse(kind: str, message: str) -> RunSetupRefused:
    """Build a refusal. A function so every raise site reads the same."""
    return RunSetupRefused(kind, message)
