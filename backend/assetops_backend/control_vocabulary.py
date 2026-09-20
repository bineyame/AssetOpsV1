"""The breaker and control-state vocabulary this product does not declare.

One answer to what is banned, in product code, so that the rule is enforced by
a value and not only by a test. T014 introduced it over the Foundation model,
T017 grew it to the scenario domain, and the review of T017 moved it here: the
scenario parser refuses a banned identifier at parse time, and a parser cannot
import from `backend/tests/`.

Settled by `D-2026-09-20-breaker-vocabulary`: a breaker is a topology element
and, when instrumented, something a device reports about, but its position is a
time-scoped operational fact, which in this project means evidence. A closed
set of positions or control modes in configuration or in scenario schema would
let a document assert an operating condition nothing ever observed.

`BREAKER` is banned with the position words. Admitting it as a device type or
as a scenario category would answer half the question early, by saying a
breaker is a configured reporting thing in the same sense as a meter.

## What counts as vocabulary, and what does not

Vocabulary is what the product uses to NAME a kind of thing: a closed enum
value, a mapping key in a stored document, and an identifier a domain coins for
one of its own parts. Prose is not vocabulary. A description that used one of
these words in an English sentence would be English; a category, an entry kind,
a parameter identifier or a mapping key that used one would be schema.

That line is drawn deliberately rather than conservatively. A ban that reached
free text would refuse a legitimate sentence sooner or later, and a guard that
blocks something legitimate is a guard somebody relaxes. A ban on identifiers
is precise, and an identifier is where the T017 task actually places the
prohibition: "event types, enum values, parameter keys, badges, columns, or
filters".

Comparison is by token rather than by substring, so `breaker_position`,
`breaker-position` and `BREAKER_TRIPPED` are all caught while a longer word
that merely contains one of them is not mistaken for one.
"""

from __future__ import annotations

import re

#: The banned tokens. Position words, control modes, and the element itself.
BANNED_CONTROL_VOCABULARY = (
    "OPEN",
    "CLOSED",
    "TRIPPED",
    "AUTO",
    "MANUAL",
    "BREAKER",
)

_TOKEN_SEPARATOR = re.compile(r"[^A-Za-z0-9]+")

#: What a refusal tells the author. Stated once so the parser and the scans
#: cannot describe the rule differently.
CONTROL_VOCABULARY_RULE = (
    "Breaker position and control mode are evidence, not configuration and not "
    "scenario schema. No model, document, or fixture may name one until a "
    "slice adds the topology and evidence contract that makes such a statement "
    "truthful (D-2026-09-20-breaker-vocabulary). Name the authored cause or "
    "action instead."
)


def tokens_of(text: str) -> set[str]:
    """Split an identifier or an enumerated value into upper-case tokens."""
    return {part.upper() for part in _TOKEN_SEPARATOR.split(text) if part}


def banned_tokens_in(text: str) -> list[str]:
    """Return the banned tokens `text` is built from, in a stable order.

    Empty for anything that is not control vocabulary, which is the normal
    case and the one the parser takes.
    """
    found = tokens_of(text) & set(BANNED_CONTROL_VOCABULARY)
    return sorted(found)
