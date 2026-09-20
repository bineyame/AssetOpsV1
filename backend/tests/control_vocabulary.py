"""Scanning a stored document for the banned breaker/control vocabulary.

The banned list itself lives in product code, at
`assetops_backend/control_vocabulary.py`, because the scenario parser refuses a
banned identifier at parse time and a parser cannot import from here. This
module is the scanning half: what counts as a schema position in a loaded
document, and how a scan reports what it found. Both halves read one list.

## What a schema position is

Three kinds, and the third was missing until the T017 review found it.

1. **Mapping keys**, at every depth. A key is how a document names a field.
2. **Enumerated values**: string values spelled in upper snake case. That is
   not a heuristic in this tree, it is the convention every closed vocabulary
   in the product follows, from `MINIGRID` to `PV_ARRAY` to `LOSS_OR_FRAUD`.
3. **Identifier values**, at the keys in `IDENTIFIER_VALUED_KEYS`. A scenario
   parameter key is not a YAML mapping key - it is the lowercase identifier in
   the `parameter_id` FIELD - so the first two kinds did not reach it, and
   `parameter_id: breaker-position` passed the scan the slice originally
   shipped. `event_id` and `scenario_id` had the same hole.

The proof that shipped with the slice used `breaker_position: CLOSED` as a
mapping key, and it **passed for the wrong reason**: the strict parser already
refuses unknown mapping keys, so the document was refused before the scan's
coverage was ever exercised. A deliberate violation has to be one the rest of
the system would otherwise accept, or it proves the wrong thing.

## What is deliberately not a schema position

Free text. A description that used one of these words in an English sentence
would be English; a category, an entry kind, a parameter identifier or a
mapping key that used one would be schema. A ban that reached free text would
refuse a legitimate sentence sooner or later, and a guard that blocks something
legitimate is a guard somebody relaxes.

`site_id` and `template_id` are not scanned either. They are references into
other identity spaces whose naming the scenario domain does not own; refusing a
token there would refuse a legitimately-named Site or template rather than
protect scenario vocabulary. A free-text LABEL that named a position without
any identifier doing so would not be caught here; that is a review matter and
is recorded as such, not a hole the scan pretends to cover.
"""

from __future__ import annotations

import re
from typing import Any, Iterator, Mapping

from assetops_backend.control_vocabulary import (
    BANNED_CONTROL_VOCABULARY,
    CONTROL_VOCABULARY_RULE,
    banned_tokens_in,
    tokens_of,
)

__all__ = [
    "BANNED_CONTROL_VOCABULARY",
    "CONTROL_VOCABULARY_RULE",
    "ENUMERATED_VALUE_PATTERN",
    "IDENTIFIER_VALUED_KEYS",
    "banned_terms_in",
    "banned_tokens_in",
    "refusal",
    "schema_vocabulary",
    "tokens_of",
]

#: How this project spells an enumerated value: upper case, digits and
#: underscores, at least two characters. `MG-001` and a sentence are not this.
ENUMERATED_VALUE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]+$")

#: The fields whose VALUE is an identifier the scenario domain coins for one of
#: its own parts. Each is rendered as the name of a thing, so each is
#: vocabulary. Audited rather than guessed: these are exactly the identifiers
#: `scenarios/parsing.py` and `scenarios/identity.py` validate and own.
#:
#: `site_id` and `template_id` are absent on purpose - see the module docstring.
IDENTIFIER_VALUED_KEYS = frozenset(
    {"scenario_id", "event_id", "parameter_id", "expectation_id"}
)


def schema_vocabulary(document: Any) -> Iterator[tuple[str, str]]:
    """Yield `(kind, term)` for every schema position in a loaded document.

    `kind` is `"key"`, `"value"` or `"identifier"`, so a failure message can
    say which part of the schema the banned term arrived in.
    """
    pending: list[Any] = [document]

    while pending:
        node = pending.pop()

        if isinstance(node, Mapping):
            for key, child in node.items():
                if isinstance(key, str):
                    yield ("key", key)
                    if key in IDENTIFIER_VALUED_KEYS and isinstance(child, str):
                        yield ("identifier", child)
                pending.append(child)
        elif isinstance(node, (list, tuple)):
            pending.extend(node)
        elif isinstance(node, str) and ENUMERATED_VALUE_PATTERN.match(node):
            yield ("value", node)


def banned_terms_in(document: Any) -> list[str]:
    """Return a description of every banned schema term in a document."""
    offences: list[str] = []

    for kind, term in schema_vocabulary(document):
        found = banned_tokens_in(term)
        if found:
            offences.append(f"{kind} {term!r} contains {found}")

    return offences


def refusal(where: str, offences: list[str]) -> str:
    """The message every scan fails with, so the reason reads the same."""
    return (
        f"{where} declares control-state vocabulary: {'; '.join(offences)}. "
        f"{CONTROL_VOCABULARY_RULE}"
    )
