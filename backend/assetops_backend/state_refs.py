"""How a world state is addressed: a semantic key, and which asset it is on.

A mini-grid has more than one of most things. Two fuel tanks, two generators,
two loads - and every one of them has a stored volume, a capacity, a specific
fuel consumption. `fuel-tank-volume` names *what kind of fact* that is; it does
not name *whose*. Before T020A1 the product had only the first half, so a site
with two tanks had one `fuel-tank-volume` and a run had to block rather than
choose between them.

A `StateRef` is the whole address: the semantic key, the scope it is claimed
at, and - for a component-scoped claim - which component. The semantic key
stays semantic. Component identity lives in the selector beside it and never
inside the key, because a key that grew an identity would be an identity every
comparison in the product had to remember to strip off again.

## Why this module sits at the package root

The same reason `document_bounds.py` does: the rule is about addressing, not
about scenarios, profiles or runs. All three speak it. A scenario declares an
address, a model profile declares the scope a state is claimed at, and a run
freezes the address it resolved. A shared vocabulary reached through one
domain's package would be a dependency saying the wrong thing about who owns
it - and `runs/profiles.py` may not import the Site record family at all
(`tools/checks/run-setup.ps1`), so the addressing vocabulary cannot live
anywhere near a Site either.

This module reads no document, opens nothing, and resolves nothing against a
Site. It validates shape and holds the canonical spelling. WHICH component an
unqualified reference means is a question only a Foundation can answer, and
run setup is the component entitled to ask it.

## The authored spelling

One string, three forms:

    fuel-tank-volume                  a component-scoped claim, unqualified
    fuel-tank-volume@north-tank       a component-scoped claim, addressed
    site:site-load-demand             a site-wide claim
    component:fuel-tank-volume        the unqualified form, said out loud

The bare form means COMPONENT and not SITE, and the direction of that default
is the whole of why it is safe. An unqualified component reference is the
WEAKER claim: it must still find exactly one candidate before a run is READY,
so a bare key that should have been site-wide fails visibly at resolution. The
other direction would not: a bare key silently meaning "the site's" would let
a statement about one machine become a statement about the installation, with
nothing left to catch it.

`component:` exists so an author who wants the scope written down can write it.
It is the same reference as the bare form and renders back as the bare form.

Malformed combinations are refused here rather than resolved generously. A
site-wide state has no component to select, so `site:x@y` is a document
claiming two different things about the same value; an empty key or an empty
selector is an address with a hole in it. Each refusal names the position and
says what the form is for, because a parser that only says "invalid" leaves the
author guessing which half of the address was wrong.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, NoReturn

#: The two scopes a world state can be claimed at, and there is no third.
#:
#: A state belongs to one component, or it is a fact about the installation
#: that no single component owns. "Whichever one is convenient" is the answer
#: this vocabulary exists to make unspellable.
STATE_SCOPES = frozenset({"SITE", "COMPONENT"})

#: The scope marker an author may write, and what it means.
SCOPE_MARKERS = {"site": "SITE", "component": "COMPONENT"}

#: The character that attaches a component selector to a semantic key.
SELECTOR = "@"

#: The character that separates a scope marker from the key it scopes.
SCOPE_MARK = ":"

#: Lowercase alphanumeric words separated by single hyphens - the spelling
#: every identity in an authored document uses.
#:
#: Stated here rather than imported from the scenario parser on purpose. This
#: module is beneath both document families and may not depend on either, and
#: neither `@` nor `:` matches it, which is what makes the two selector
#: characters unambiguous separators rather than characters a key might
#: legitimately contain.
STATE_REF_TOKEN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

#: An address longer than this is refused before it is split. A state key and a
#: component id are both short identities; a kilobyte of them is a document
#: doing something other than naming a value.
MAX_STATE_REF_LENGTH = 160


@dataclass(frozen=True)
class StateRef:
    """One addressed world state: what kind of fact, and whose.

    `state_key` is semantic and stays semantic. It says a stored fuel volume is
    a stored fuel volume; it never says which tank's.

    `component_id` is the selector. It is present only for a component-scoped
    reference, and it may legitimately be absent there: an author who writes
    `fuel-tank-volume` against a site with one tank has said something
    unambiguous, and run setup resolves it to that tank's identity before the
    run is READY. An absent selector is therefore a reference that is not yet
    an answer, which is exactly what `is_addressed` reports.

    A site-scoped reference has no component id, enforced here rather than
    remembered by every caller. The refusal is the structural half of "SITE
    references have no component id": a record that cannot hold the
    combination cannot be passed one.
    """

    state_key: str
    scope: str
    component_id: str | None = None

    def __post_init__(self) -> None:
        if self.scope not in STATE_SCOPES:
            raise ValueError(
                f"A state reference is claimed at one of "
                f"{sorted(STATE_SCOPES)}, not {self.scope!r}."
            )
        if not STATE_REF_TOKEN.match(self.state_key):
            raise ValueError(
                f"A state key is lowercase alphanumeric words separated by a "
                f"hyphen, not {self.state_key!r}. Component identity lives in "
                "the selector beside the key, never inside it."
            )
        if self.scope == "SITE" and self.component_id is not None:
            raise ValueError(
                f"A site-wide state has no component to select, and this "
                f"reference to {self.state_key!r} names "
                f"{self.component_id!r}. A fact about the installation and a "
                "fact about one machine are two different claims."
            )
        if self.component_id is not None and not STATE_REF_TOKEN.match(
            self.component_id
        ):
            raise ValueError(
                f"A component selector names a component the site's "
                f"foundation declares, spelled as lowercase alphanumeric "
                f"words separated by a hyphen, not {self.component_id!r}."
            )

    @property
    def addressed_key(self) -> str:
        """The canonical spelling of this address, and its identity.

        This is what every comparison, lookup, deduplication and blocking
        reason in the product keys on once addressing exists. Two components of
        the same type using one semantic state are two of these, which is the
        whole point: keying on `state_key` would make them one row and one of
        the two answers would disappear.

        It round-trips through `parse_state_ref` exactly, which is what lets a
        frozen run record store its resolved address as text and read the same
        address back.
        """
        if self.scope == "SITE":
            return f"site{SCOPE_MARK}{self.state_key}"
        if self.component_id is None:
            return self.state_key
        return f"{self.state_key}{SELECTOR}{self.component_id}"

    @property
    def is_addressed(self) -> bool:
        """Whether this reference already names exactly one thing.

        A site-wide reference does: there is one installation. A component
        reference does only once a selector is present, resolved or authored.
        """
        return self.scope == "SITE" or self.component_id is not None

    def resolved_to(self, component_id: str) -> "StateRef":
        """The same claim, now naming the component that answered it.

        Used once run setup has decided which component an unqualified
        reference meant, so the frozen record carries the address that was
        actually used rather than the question that was asked.
        """
        if self.scope != "COMPONENT":
            raise ValueError(
                f"A {self.scope} reference to {self.state_key!r} is not "
                "resolved to a component; there is no component in the claim."
            )
        return StateRef(
            state_key=self.state_key,
            scope="COMPONENT",
            component_id=component_id,
        )


def site_state(state_key: str) -> StateRef:
    """A site-wide reference, spelled once so callers do not repeat the scope."""
    return StateRef(state_key=state_key, scope="SITE", component_id=None)


def component_state(
    state_key: str, component_id: str | None = None
) -> StateRef:
    """A component-scoped reference, addressed or not."""
    return StateRef(
        state_key=state_key, scope="COMPONENT", component_id=component_id
    )


def parse_state_ref(
    value: object,
    *,
    where: str,
    source: str,
    invalid: Callable[[str], NoReturn],
) -> StateRef:
    """Validate one authored state reference into an address.

    One parser, used by both document families. The scenario parser reads the
    reference an author declared and the run document parser reads the address
    a run froze, and they are the same grammar because they are the same thing
    said at two moments - which is what makes a frozen record reconstruct to
    the address it was written from rather than to something that merely looks
    like it.

    Args:
        value: the authored text. Anything else is refused by type.
        where: the document position, used in the message only.
        source: the document name, used in the message only.
        invalid: raises the caller's configuration-invalid error. Passing the
            raiser rather than an exception class is what lets the scenario
            and run parsers keep their own error vocabularies while sharing
            one implementation of the grammar.

    Returns:
        The address. A bare key is component-scoped and unqualified; it is not
        yet resolved and is not treated as one.
    """
    if not isinstance(value, str) or not value:
        invalid(
            f"'{where}' must name the world state it concerns as text in "
            f"{source}, got {value!r}. A state reference is a semantic state "
            "key, optionally addressed to the component it is about."
        )

    if len(value) > MAX_STATE_REF_LENGTH:
        invalid(
            f"'{where}' is {len(value)} characters long in {source}, above "
            f"the limit of {MAX_STATE_REF_LENGTH}. A state key and a "
            "component identity are both short names."
        )

    scope = "COMPONENT"
    remainder = value

    if SCOPE_MARK in value:
        marker, _, remainder = value.partition(SCOPE_MARK)
        resolved_scope = SCOPE_MARKERS.get(marker)
        if resolved_scope is None:
            invalid(
                f"'{where}' declares the scope {marker!r} in {source}, and a "
                f"world state is claimed at one of {sorted(SCOPE_MARKERS)}. "
                "Write 'site:' for a fact about the installation, or leave "
                "the marker off for a fact about one component."
            )
        scope = resolved_scope

    if SELECTOR in remainder:
        state_key, _, component_id = remainder.partition(SELECTOR)
        if SELECTOR in component_id:
            invalid(
                f"'{where}' carries more than one {SELECTOR!r} in {source}, "
                f"got {value!r}. A state reference selects one component, so "
                "there is one selector or none."
            )
        if scope == "SITE":
            invalid(
                f"'{where}' declares a site-wide state and also selects "
                f"component {component_id!r} in {source}. A fact about the "
                "installation and a fact about one machine are two different "
                "claims; drop the 'site:' marker to address the component, or "
                "drop the selector to keep the claim site-wide."
            )
        if not component_id:
            invalid(
                f"'{where}' ends in {SELECTOR!r} with no component after it "
                f"in {source}, got {value!r}. An empty selector is an address "
                "with a hole in it: leave the selector off to mean "
                "'whichever component of the bound type this site declares', "
                "or name one."
            )
    else:
        state_key = remainder
        component_id = None

    if not state_key:
        invalid(
            f"'{where}' names no state in {source}, got {value!r}. A "
            "reference addresses a semantic world state; the selector says "
            "whose it is and cannot stand on its own."
        )

    if not STATE_REF_TOKEN.match(state_key):
        invalid(
            f"'{where}' must name a world state as lowercase alphanumeric "
            f"words separated by a hyphen in {source}, got {state_key!r}."
        )

    if component_id is not None and not STATE_REF_TOKEN.match(component_id):
        invalid(
            f"'{where}' selects component {component_id!r} in {source}, and a "
            "component selector names a component the target site's "
            "foundation declares, spelled as lowercase alphanumeric words "
            "separated by a hyphen."
        )

    return StateRef(
        state_key=state_key, scope=scope, component_id=component_id
    )
