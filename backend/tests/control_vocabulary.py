"""The breaker and control-state vocabulary this product does not declare.

One answer to what is banned, read by every scan that holds the ban. T014
introduced the rule over the Foundation model; T017 grows it to the scenario
domain, so the words now live here rather than in whichever test happened to be
written first. Two copies would drift, and the drift would show up as a scan
that passes because it is checking a shorter list.

Settled by `D-2026-09-20-breaker-vocabulary`: a breaker is a topology element
and, when instrumented, something a device reports about, but its position is a
time-scoped operational fact, which in this project means evidence. A closed
set of positions or control modes in configuration or in scenario schema would
let a YAML field assert an operating condition nothing ever observed.

`BREAKER` is banned with the position words. Admitting it as a device type or
as a scenario category would answer half the question early, by saying a
breaker is a configured reporting thing in the same sense as a meter.

## Why schema positions, and not the whole document

The rule is about vocabulary, not about prose. A scenario description that
happened to use one of these words in a sentence would be English; a category,
an entry kind, a parameter key or a mapping key that used one would be schema.

So the scan below collects two things from a loaded document: every mapping key
at every depth, and every string value spelled in upper snake case. The second
is not a heuristic in this tree - it is the convention every closed vocabulary
in the product follows, from `MINIGRID` to `PV_ARRAY` to `LOSS_OR_FRAUD` - so
an enumerated value is exactly what it finds and free text is exactly what it
does not.

Comparison is by token rather than by substring, so `breaker_position` and
`BREAKER_TRIPPED` are both caught while a word that merely contains one of them
is not mistaken for one.
"""

from __future__ import annotations

import re
from typing import Any, Iterator, Mapping

#: The banned tokens. Position words, control modes, and the element itself.
BANNED_CONTROL_VOCABULARY = (
    "OPEN",
    "CLOSED",
    "TRIPPED",
    "AUTO",
    "MANUAL",
    "BREAKER",
)

#: How this project spells an enumerated value: upper case, digits and
#: underscores, at least two characters. `MG-001` and a sentence are not this.
ENUMERATED_VALUE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]+$")

_TOKEN_SEPARATOR = re.compile(r"[^A-Za-z0-9]+")


def tokens_of(text: str) -> set[str]:
    """Split an identifier or an enumerated value into upper-case tokens."""
    return {
        part.upper() for part in _TOKEN_SEPARATOR.split(text) if part
    }


def schema_vocabulary(document: Any) -> Iterator[tuple[str, str]]:
    """Yield `(kind, term)` for every schema position in a loaded document.

    `kind` is `"key"` or `"value"`, so a failure message can say which half of
    the schema the banned term arrived in.
    """
    pending: list[Any] = [document]

    while pending:
        node = pending.pop()

        if isinstance(node, Mapping):
            for key, child in node.items():
                if isinstance(key, str):
                    yield ("key", key)
                pending.append(child)
        elif isinstance(node, (list, tuple)):
            pending.extend(node)
        elif isinstance(node, str) and ENUMERATED_VALUE_PATTERN.match(node):
            yield ("value", node)


def banned_terms_in(document: Any) -> list[str]:
    """Return a description of every banned schema term in a document."""
    offences: list[str] = []

    for kind, term in schema_vocabulary(document):
        found = tokens_of(term) & set(BANNED_CONTROL_VOCABULARY)
        if found:
            offences.append(f"{kind} {term!r} contains {sorted(found)}")

    return offences


def refusal(where: str, offences: list[str]) -> str:
    """The message every scan fails with, so the reason reads the same."""
    return (
        f"{where} declares control-state vocabulary: {'; '.join(offences)}. "
        "Breaker position and control mode are evidence, not configuration and "
        "not scenario schema, and no model, document, or fixture may declare "
        "them until a slice adds the topology and evidence contract that makes "
        "such a statement truthful (D-2026-09-20-breaker-vocabulary)."
    )
