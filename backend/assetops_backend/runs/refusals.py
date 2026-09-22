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

Two of them are about an initial world value and they are deliberately not
one kind. **An absence and a contradiction are not the same shape**, and the
difference is the whole of why one side of the line can persist a Draft and
the other cannot: a value with no answer is something the frozen identity can
record as absent, and a value with two answers is something it has no shape
for at all. Naming both `INITIALIZATION_INPUT_MISSING` made the kind wrong
about the case it mostly covered and put it one word from the blocking
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
#:   scenario - it is not the Site the scenario declares, or its Foundation
#:   declares no topology for the scenario's causes to sit in.
#: - `COMPONENT_OR_SIGNAL_UNRESOLVED`: a declared observation source names a
#:   device or a signal this Site's Foundation does not configure.
#: - `INITIALIZATION_INPUT_MISSING`: an initial world value whose DECLARED
#:   OWNER did not answer. Today that is one case: a `RUN_OVERRIDE` value the
#:   request did not supply. Nothing is there, and no profile can put it
#:   there, so the run would have to invent a number - the thing a frozen
#:   identity exists to stop. A value the selected PROFILE could not supply
#:   or locate is NOT here: that blocks, because a different profile would
#:   answer.
#: - `INITIAL_VALUE_ANSWERS_DISAGREE`: an initial world value that has TWO
#:   answers and they are not the same number. Today that is a Foundation
#:   rating against the value the scenario states the Foundation declares.
#:   Nothing is missing here, which is why it left the kind above: a run
#:   cannot be frozen with two answers because the frozen identity has no
#:   shape for two, and choosing one is the thing refusing prevents.
#: - `UNIT_INVALID`: a supplied value carries a unit the contract does not
#:   know, a unit the parameter does not use, or a quantity the `invalid-rate`
#:   bound case refuses.
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
        "INITIAL_VALUE_ANSWERS_DISAGREE",
        "UNIT_INVALID",
    }
)


class RunSetupRefused(Exception):
    """One run setup request, refused, with no run allocated.

    The message is product copy: a developer configuring a run meets it, so it
    names what is wrong and what would be acceptable instead. The kind is what
    a client switches on, so neither has to be parsed out of the other.
    """

    def __init__(self, kind: str, message: str) -> None:
        if kind not in RUN_SETUP_REFUSAL_KINDS:
            raise ValueError(
                f"{kind!r} is not a run setup refusal kind. Add it to "
                "RUN_SETUP_REFUSAL_KINDS with what it means, rather than "
                "reporting a new fact under an existing name."
            )
        super().__init__(message)
        self.kind = kind
        self.message = message


def refuse(kind: str, message: str) -> RunSetupRefused:
    """Build a refusal. A function so every raise site reads the same."""
    return RunSetupRefused(kind, message)
