"""The strict grammar for an addressed world state.

One parser, two document families. A scenario declares an address and a frozen
run records the one it resolved, and both cross this, which is what makes a
frozen record reconstruct to the address it was written from rather than to
something that merely looks like it.

Every refusal below is asserted on a phrase the message could not carry by
accident. `fuel-tank-volume@` and `fuel-tank-volume` differ by one character,
so a test that only checked "it raised" would pass against a parser that
refused everything, and a test that checked for the state key in the message
would pass against a parser that refused nothing useful.
"""

from __future__ import annotations

from typing import NoReturn

import pytest

from assetops_backend.state_refs import (
    MAX_STATE_REF_LENGTH,
    STATE_SCOPES,
    StateRef,
    component_state,
    parse_state_ref,
    site_state,
)


class Refused(Exception):
    """The caller's own error vocabulary, which the parser raises through."""


def refuse(message: str) -> NoReturn:
    raise Refused(message)


def parse(value: object) -> StateRef:
    return parse_state_ref(
        value, where="parameter.state_key", source="a test", invalid=refuse
    )


class TestTheThreeFormsItAccepts:
    def test_a_bare_key_is_an_unqualified_component_reference(self) -> None:
        """Not site-wide, and the direction of that default is the point.

        An unqualified component reference is the weaker claim: it has to
        find exactly one candidate before a run is READY, so a bare key that
        should have been site-wide fails visibly at resolution. A bare key
        quietly meaning "the site's" would turn a statement about one machine
        into a statement about the installation with nothing left to catch it.
        """
        ref = parse("fuel-tank-volume")

        assert ref == StateRef(
            state_key="fuel-tank-volume", scope="COMPONENT", component_id=None
        )
        assert ref.is_addressed is False

    def test_a_selector_names_the_component(self) -> None:
        ref = parse("fuel-tank-volume@north-tank")

        assert ref.state_key == "fuel-tank-volume"
        assert ref.scope == "COMPONENT"
        assert ref.component_id == "north-tank"
        assert ref.is_addressed is True

    def test_a_site_marker_makes_it_site_wide(self) -> None:
        ref = parse("site:plane-of-array-irradiance")

        assert ref.scope == "SITE"
        assert ref.component_id is None
        assert ref.state_key == "plane-of-array-irradiance"
        # A site-wide claim names exactly one thing already: the site.
        assert ref.is_addressed is True

    def test_the_component_marker_is_the_bare_form_said_out_loud(self) -> None:
        assert parse("component:fuel-tank-volume") == parse(
            "fuel-tank-volume"
        )
        assert parse("component:fuel-tank-volume@north-tank") == parse(
            "fuel-tank-volume@north-tank"
        )

    def test_the_scope_vocabulary_has_exactly_two_members(self) -> None:
        """A third scope is a third thing every comparison must handle."""
        assert STATE_SCOPES == {"SITE", "COMPONENT"}


class TestWhatItRefuses:
    """Malformed scope and selector combinations, each with its own reason."""

    def test_a_site_reference_may_not_select_a_component(self) -> None:
        """The combination acceptance criterion 1 names.

        A fact about the installation and a fact about one machine are two
        different claims, and a document stating both is a document that has
        to be adjudicated by whoever reads it next.
        """
        with pytest.raises(Refused) as raised:
            parse("site:example-demand@load-res")

        assert "site-wide state and also selects component" in str(
            raised.value
        )

    def test_an_empty_selector_is_not_an_omitted_one(self) -> None:
        """Two different documents, and only one of them is legal.

        `x` means "whichever component of the bound type this site declares".
        `x@` means the author started naming one and stopped, which is a hole
        rather than a shorthand.
        """
        with pytest.raises(Refused) as raised:
            parse("fuel-tank-volume@")

        assert "no component after it" in str(raised.value)

    def test_a_selector_with_no_state_is_refused(self) -> None:
        with pytest.raises(Refused) as raised:
            parse("@north-tank")

        assert "names no state" in str(raised.value)

    def test_two_selectors_select_nothing(self) -> None:
        with pytest.raises(Refused) as raised:
            parse("fuel-tank-volume@north-tank@south-tank")

        assert "more than one" in str(raised.value)

    def test_an_unknown_scope_marker_is_refused(self) -> None:
        with pytest.raises(Refused) as raised:
            parse("device:fuel-tank-volume")

        assert "declares the scope 'device'" in str(raised.value)

    def test_an_empty_scope_marker_is_refused(self) -> None:
        with pytest.raises(Refused) as raised:
            parse(":fuel-tank-volume")

        assert "declares the scope ''" in str(raised.value)

    def test_a_scope_marker_with_no_state_is_refused(self) -> None:
        with pytest.raises(Refused) as raised:
            parse("site:")

        assert "names no state" in str(raised.value)

    @pytest.mark.parametrize(
        "value",
        [
            "Fuel-Tank-Volume",
            "fuel tank volume",
            "fuel--tank",
            "-fuel-tank",
            "fuel_tank_volume",
        ],
    )
    def test_a_misspelled_state_key_is_refused(self, value: str) -> None:
        with pytest.raises(Refused) as raised:
            parse(value)

        assert "lowercase alphanumeric words" in str(raised.value)

    @pytest.mark.parametrize(
        "value", ["fuel-tank-volume@North-Tank", "fuel-tank-volume@a b"]
    )
    def test_a_misspelled_selector_is_refused(self, value: str) -> None:
        with pytest.raises(Refused) as raised:
            parse(value)

        assert "selects component" in str(raised.value)

    @pytest.mark.parametrize(
        "value",
        [
            "fuel-tank-volume\n",
            "site:example-demand\n",
            "fuel-tank-volume@north-tank\n",
            "\nfuel-tank-volume",
            "fuel-tank-volume\r",
            "fuel-tank-volume\n@north-tank",
        ],
    )
    def test_a_line_feed_does_not_slip_into_an_identity(
        self, value: str
    ) -> None:
        """The hole an independent review found in this grammar.

        The token was anchored with `^` and `$` and matched with `.match`,
        and Python's `$` also matches just before a FINAL newline - so
        `north-tank` followed by a line feed satisfied it and kept that
        character inside the canonical identity. The result looks like
        `north-tank` in every message, is not equal to it in any comparison,
        and a YAML block scalar produces one without an author doing anything
        unusual.

        Refused rather than stripped. Trimming it would silently turn one
        authored identity into a different one, which is the same class of
        quiet substitution the selector rules exist to prevent.
        """
        with pytest.raises(Refused):
            parse(value)

    def test_the_record_refuses_a_line_feed_as_well(self) -> None:
        """Both entry paths, because a service composes references in code.

        A rule enforced only at the document boundary is a rule an in-process
        caller walks around.
        """
        with pytest.raises(ValueError):
            StateRef(state_key="north-tank\n", scope="COMPONENT")
        with pytest.raises(ValueError):
            StateRef(
                state_key="fuel-tank-volume",
                scope="COMPONENT",
                component_id="north-tank\n",
            )

    @pytest.mark.parametrize("value", [None, 17, "", ["fuel-tank-volume"]])
    def test_a_reference_that_is_not_text_is_refused(
        self, value: object
    ) -> None:
        with pytest.raises(Refused) as raised:
            parse(value)

        assert "must name the world state it concerns as text" in str(
            raised.value
        )

    def test_an_oversized_reference_is_refused_before_it_is_split(
        self,
    ) -> None:
        with pytest.raises(Refused) as raised:
            parse("a" * (MAX_STATE_REF_LENGTH + 1))

        assert "above the limit" in str(raised.value)


class TestTheRecordRefusesWhatTheGrammarDoes:
    """The structural half: a record that cannot hold it cannot be passed it.

    The parser is one way in. A service composing a reference in code is
    another, and a rule enforced only at the document boundary is a rule an
    in-process caller can walk around - which is the shape of defect T020A's
    review found twice.
    """

    def test_a_site_reference_with_a_component_cannot_be_built(self) -> None:
        with pytest.raises(ValueError) as raised:
            StateRef(
                state_key="example-demand",
                scope="SITE",
                component_id="load-res",
            )

        assert "no component to select" in str(raised.value)

    def test_an_unknown_scope_cannot_be_built(self) -> None:
        with pytest.raises(ValueError):
            StateRef(state_key="example-demand", scope="FEEDER")

    def test_a_state_key_carrying_a_selector_cannot_be_built(self) -> None:
        """Component identity lives beside the key and never inside it."""
        with pytest.raises(ValueError) as raised:
            StateRef(state_key="fuel-tank-volume@north", scope="COMPONENT")

        assert "never inside it" in str(raised.value)

    def test_a_site_reference_resolves_to_no_component(self) -> None:
        with pytest.raises(ValueError) as raised:
            site_state("example-demand").resolved_to("load-res")

        assert "no component in the claim" in str(raised.value)

    def test_resolving_keeps_the_key_and_adds_the_component(self) -> None:
        resolved = component_state("fuel-tank-volume").resolved_to(
            "north-tank"
        )

        assert resolved.state_key == "fuel-tank-volume"
        assert resolved.addressed_key == "fuel-tank-volume@north-tank"


class TestTheCanonicalSpellingRoundTrips:
    """What a run writes down is read back as the same address.

    Acceptance criterion 10's serialization half, tested on the grammar rather
    than through a run, so a form nothing in the fixtures happens to use is
    still covered.
    """

    @pytest.mark.parametrize(
        "value",
        [
            "fuel-tank-volume",
            "fuel-tank-volume@north-tank",
            "site:plane-of-array-irradiance",
            "component:fuel-tank-volume",
            "component:fuel-tank-volume@north-tank",
        ],
    )
    def test_parsing_the_rendered_address_gives_the_same_reference(
        self, value: str
    ) -> None:
        once = parse(value)
        twice = parse(once.addressed_key)

        assert twice == once
        assert twice.addressed_key == once.addressed_key

    def test_the_three_forms_render_distinctly(self) -> None:
        """Two addresses that mean different things must not spell the same.

        The whole product keys on this string - duplicate detection, blocking
        reason subjects, the row on the screen - so two distinct references
        rendering identically would collapse two facts into one wherever it
        is used.
        """
        rendered = {
            component_state("x").addressed_key,
            component_state("x", "north-tank").addressed_key,
            component_state("x", "south-tank").addressed_key,
            site_state("x").addressed_key,
        }

        assert len(rendered) == 4
