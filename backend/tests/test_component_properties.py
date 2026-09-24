"""Typed component properties: the carrier, its strictness, its compatibility.

T020A adds the second thing a Foundation may say about a component. A `Rating`
is the one nameplate magnitude a component was sold with; a property is a
named, typed, unit-carrying physical or control fact about the same component,
and a component may declare several.

Three things are proved here and they are the three ways the carrier could be
wrong:

- **it is one validator, for both document families.** A template declaring a
  property the Site store would refuse is a template that seeds an unreadable
  Site, which is the reason `foundation_parsing` exists at all. Every
  strictness case below runs against both parsers.
- **the vocabulary is closed and the unit belongs to it.** A model profile
  binds to a property by name, so a document that could coin its own keys
  could coin one no profile will ever look for; and the same quantity written
  in two units is two numbers a consumer would have to tell apart by reading
  text.
- **a Site written before this slice stays readable.** The compatibility path
  is the absent key, and it is a path rather than a shim: nothing is invented
  for a document that declares no properties, and a round trip returns an
  equal record.

What is deliberately NOT here: a controller, a setpoint anything writes, or a
Site-scoped Controls capability. A `CONTROL` property is an inspectable typed
value and nothing in this build consumes one.
"""

from __future__ import annotations

import copy
from typing import Any, Callable

import pytest

from assetops_backend.sites.models import (
    COMPONENT_PROPERTY_DEFINITIONS,
    COMPONENT_PROPERTY_KINDS,
    PROPERTY_UNITS,
)
from assetops_backend.sites.parsing import parse_site_template
from assetops_backend.sites.ports import (
    SiteConfigurationInvalid,
    SiteTemplateConfigurationInvalid,
)
from assetops_backend.sites.site_parsing import (
    parse_site_document,
    render_site_document,
)
from test_site_parsing import valid_site_document
from test_site_template_parsing import valid_document as valid_template_document


def generator_properties() -> list[dict[str, Any]]:
    """One physical and one control property on one component."""
    return [
        {
            "property_key": "specific-fuel-consumption",
            "value": 0.311,
            "unit": "L/kWh",
            "source": "TEMPLATE",
            "source_version": 2,
        },
        {
            "property_key": "minimum-runtime",
            "value": 30,
            "unit": "min",
            "source": "SITE",
            "source_version": 1,
        },
    ]


def template_with(properties: Any) -> dict[str, Any]:
    document = valid_template_document()
    document["foundation"]["components"][0]["properties"] = properties
    return document


def site_with(properties: Any) -> dict[str, Any]:
    document = valid_site_document()
    document["foundation"]["components"][0]["properties"] = properties
    return document


def parse_template_with(properties: Any) -> Any:
    return parse_site_template(
        template_with(properties), source="test-template.yaml"
    ).foundation.components[0]


def parse_site_with(properties: Any) -> Any:
    return parse_site_document(
        site_with(properties), source="test-site.yaml"
    ).foundation.components[0]


#: The same case, against both parsers. Two copies of these rules would let a
#: template declare a property the Site store refuses.
families = pytest.mark.parametrize(
    ("parse", "refusal"),
    [
        pytest.param(
            parse_template_with, SiteTemplateConfigurationInvalid, id="template"
        ),
        pytest.param(parse_site_with, SiteConfigurationInvalid, id="site"),
    ],
)

Mutate = Callable[[list[dict[str, Any]]], Any]


class TestTheVocabulary:
    def test_every_definition_names_a_unit_and_a_kind_it_declares(self) -> None:
        assert COMPONENT_PROPERTY_DEFINITIONS
        for key, definition in COMPONENT_PROPERTY_DEFINITIONS.items():
            assert definition.kind in COMPONENT_PROPERTY_KINDS, key
            assert definition.unit in PROPERTY_UNITS, key
            assert definition.display_name.strip(), key

    def test_the_unit_set_is_derived_rather_than_listed(self) -> None:
        """A unit listed by hand outlives the property that used it."""
        assert PROPERTY_UNITS == {
            definition.unit
            for definition in COMPONENT_PROPERTY_DEFINITIONS.values()
        }

    def test_both_kinds_are_declared_by_something(self) -> None:
        """Otherwise one of them is vocabulary nothing has ever used."""
        declared = {
            definition.kind
            for definition in COMPONENT_PROPERTY_DEFINITIONS.values()
        }
        assert declared == COMPONENT_PROPERTY_KINDS


class TestWhatIsParsed:
    @families
    def test_a_component_may_declare_several(self, parse, refusal) -> None:
        component = parse(generator_properties())

        assert [item.property_key for item in component.properties] == [
            "specific-fuel-consumption",
            "minimum-runtime",
        ]
        assert [item.value for item in component.properties] == [0.311, 30.0]
        assert [item.unit for item in component.properties] == ["L/kWh", "min"]

    @families
    def test_the_kind_comes_from_the_vocabulary_not_the_document(
        self, parse, refusal
    ) -> None:
        """A document that could choose its own kind could disagree with the
        vocabulary, so there is no key for it to choose in."""
        component = parse(generator_properties())

        assert [item.kind for item in component.properties] == [
            "PHYSICAL",
            "CONTROL",
        ]

        with pytest.raises(refusal) as error:
            parse(
                [{**generator_properties()[0], "kind": "CONTROL"}]
            )
        assert "kind" in str(error.value)

    @families
    def test_provenance_is_carried_per_property(self, parse, refusal) -> None:
        """Which document declared this number, and at which version.

        Per property rather than per component, because a Site may declare one
        of its own beside one it copied - which is exactly what the fixture
        above does.
        """
        component = parse(generator_properties())

        assert [
            (item.source, item.source_version) for item in component.properties
        ] == [("TEMPLATE", 2), ("SITE", 1)]

    @families
    def test_the_rating_survives_beside_them(self, parse, refusal) -> None:
        """Two different kinds of fact, and neither derives from the other."""
        component = parse(generator_properties())

        assert component.rating is not None
        assert component.rating.value == 100
        assert component.rating.unit == "kW"


class TestStrictness:
    """Every one of these is refused before anything is written."""

    @pytest.mark.parametrize(
        "mutate",
        [
            pytest.param(
                lambda p: [p[0], copy.deepcopy(p[0])], id="duplicate-identity"
            ),
            pytest.param(
                lambda p: [{**p[0], "property_key": "invented-property"}],
                id="key-outside-the-vocabulary",
            ),
            pytest.param(
                lambda p: [{**p[0], "unit": "L/h"}], id="unit-the-key-is-not-in"
            ),
            pytest.param(
                lambda p: [{**p[0], "unit": None}], id="no-unit"
            ),
            pytest.param(
                lambda p: [{**p[0], "value": "a lot"}], id="value-as-text"
            ),
            pytest.param(
                lambda p: [{**p[0], "value": True}], id="value-as-a-flag"
            ),
            pytest.param(lambda p: [{**p[0], "value": -1}], id="negative-value"),
            pytest.param(
                lambda p: [{k: v for k, v in p[0].items() if k != "value"}],
                id="no-value",
            ),
            pytest.param(
                lambda p: [{**p[0], "source": "SOMEWHERE"}],
                id="source-outside-the-vocabulary",
            ),
            pytest.param(
                lambda p: [{k: v for k, v in p[0].items() if k != "source"}],
                id="no-source",
            ),
            pytest.param(
                lambda p: [{**p[0], "source_version": 0}],
                id="source-version-below-one",
            ),
            pytest.param(
                lambda p: [{**p[0], "source_version": "2"}],
                id="source-version-as-text",
            ),
            pytest.param(
                lambda p: [{**p[0], "setpoint": 50}], id="unknown-key"
            ),
            pytest.param(lambda p: [], id="empty-list"),
            pytest.param(lambda p: {}, id="not-a-list"),
            pytest.param(lambda p: ["a property"], id="entry-not-a-mapping"),
        ],
    )
    @families
    def test_a_malformed_property_is_refused(
        self, mutate: Mutate, parse, refusal
    ) -> None:
        with pytest.raises(refusal):
            parse(mutate(generator_properties()))

    @families
    def test_the_refusal_names_the_position_and_the_vocabulary(
        self, parse, refusal
    ) -> None:
        """A refusal a person cannot act on is a stack trace with prose."""
        with pytest.raises(refusal) as error:
            parse([{**generator_properties()[0], "property_key": "invented"}])

        message = str(error.value)
        assert "properties[0].property_key" in message
        # The offending key, quoted as what was got. `specific-fuel-consumption`
        # on its own is satisfied by the vocabulary listing the message
        # prints, so it says nothing about whether the refusal identifies the
        # document's own mistake - the same substring weakness an independent
        # review proved elsewhere in this slice.
        assert "got 'invented'" in message
        assert sorted(COMPONENT_PROPERTY_DEFINITIONS)[0] in message

    @families
    def test_a_wrong_unit_is_refused_by_the_property_it_is_on(
        self, parse, refusal
    ) -> None:
        """The case the vocabulary exists for, named separately.

        `L/h` is a legal unit elsewhere in this product. What makes it wrong
        here is the property it is written on: specific fuel consumption is
        `L/kWh`, and a litres-per-hour number is only true at one operating
        point (`D-2026-09-22-consumption-coefficient-unit`).
        """
        with pytest.raises(refusal) as error:
            parse([{**generator_properties()[0], "unit": "L/h"}])

        message = str(error.value)
        # The whole phrase: the message lists the vocabulary nowhere here, but
        # naming the unit and the key separately would still pass against a
        # refusal that paired them with something else.
        assert (
            "must be 'L/kWh' for property 'specific-fuel-consumption'"
            in message
        )


class TestCompatibility:
    """A Site written before T020A stays readable, unchanged."""

    def test_a_document_declaring_no_properties_parses_to_none(self) -> None:
        """The absent key is the compatibility path.

        `None` is the document being silent. It is not an empty list, because
        an empty list is a screen's licence to state that this component HAS
        no properties, which the document never said.
        """
        document = valid_site_document()
        for component in document["foundation"]["components"]:
            component.pop("properties", None)

        record = parse_site_document(document, source="an older site")

        assert record.foundation.components
        for component in record.foundation.components:
            assert component.properties is None

    def test_such_a_document_round_trips_to_an_equal_record(self) -> None:
        """A write proves that what it stored is what was validated."""
        document = valid_site_document()
        for component in document["foundation"]["components"]:
            component.pop("properties", None)

        once = parse_site_document(document, source="an older site")
        twice = parse_site_document(
            render_site_document(once), source="the rendered site"
        )

        assert twice == once

    def test_a_document_declaring_properties_round_trips_too(self) -> None:
        once = parse_site_document(
            site_with(generator_properties()), source="a site"
        )
        twice = parse_site_document(
            render_site_document(once), source="the rendered site"
        )

        assert twice == once
        assert twice.foundation.components[0].properties is not None

    def test_the_rendered_document_writes_the_key_either_way(self) -> None:
        """Total rather than conditional, for the reason the four Foundation
        sections are: a conditional render makes a round trip depend on which
        keys the original document happened to carry."""
        document = valid_site_document()
        for component in document["foundation"]["components"]:
            component.pop("properties", None)

        rendered = render_site_document(
            parse_site_document(document, source="an older site")
        )

        for component in rendered["foundation"]["components"]:
            assert "properties" in component
            assert component["properties"] is None

    def test_an_updated_template_does_not_reach_an_existing_site(self) -> None:
        """Templates copy at creation; they never migrate a Site.

        Proved as the property rather than as a story: a Site record parsed
        from its own stored document is a function of that document alone, so
        a template that gains properties and a version cannot change it.

        What this does NOT do, and an independent review was right to name
        it: it parses an updated template between two reads of the same
        document rather than driving a repository or a service. There is no
        migration path to drive - no code in the product reads a template
        while reading a Site - and source inspection is what establishes
        that. This pins the half a test can pin: the read is a pure function
        of the stored document.
        """
        stored = valid_site_document()
        for component in stored["foundation"]["components"]:
            component.pop("properties", None)
        before = parse_site_document(stored, source="an older site")

        updated = valid_template_document()
        updated["template_version"] = 99
        updated["foundation"]["components"][0]["properties"] = (
            generator_properties()
        )
        parse_site_template(updated, source="the updated template")

        after = parse_site_document(stored, source="an older site")

        assert after == before
        assert after.template is not None
        assert after.template.template_version != 99


class TestNoControlCapabilityIsImplied:
    """A `CONTROL` property is an inspectable value, not a controller."""

    def test_a_control_property_declares_no_control_state(self) -> None:
        """The T016 restriction is untouched.

        No switching position, no breaker state, no operating mode: the
        vocabulary carries quantities with units and nothing that could be
        mistaken for a control model.
        """
        from control_vocabulary import BANNED_CONTROL_VOCABULARY, tokens_of

        names = set(COMPONENT_PROPERTY_DEFINITIONS) | {
            definition.unit
            for definition in COMPONENT_PROPERTY_DEFINITIONS.values()
        }
        assert names
        for banned in BANNED_CONTROL_VOCABULARY:
            offenders = sorted(
                name for name in names if banned in tokens_of(name)
            )
            assert not offenders, (
                f"{banned!r} is control-state vocabulary, declared in the "
                f"property vocabulary as {offenders}."
            )

    def test_no_shipped_profile_binds_a_control_property(self) -> None:
        """The one consumer this build could have, asserted as an absence.

        Narrower than "nothing in the product consumes one", which is what
        this used to be called, and an independent review was right that the
        name overstated the scan: it reads the shipped model profiles and
        nothing else. What makes the wider claim true today is that a model
        profile's binding is the only mechanism that reads a declared
        property at all - source inspection establishes that, and this
        establishes that no profile uses it on a control key.

        The first controller that consumes one is T024's, and a binding that
        reached for one here would be a Site-scoped Controls capability
        arriving without the slice that owns it.
        """
        from assetops_backend.runs.profiles import MODEL_PROFILES

        control_keys = {
            key
            for key, definition in COMPONENT_PROPERTY_DEFINITIONS.items()
            if definition.kind == "CONTROL"
        }
        assert control_keys, "the scan would be vacuous"

        bound = {
            state.foundation_binding.property_key
            for profile in MODEL_PROFILES
            for state in profile.supported_states
            if state.foundation_binding is not None
        }
        assert bound, "the scan would be vacuous"
        assert bound & control_keys == set()


class TestANumberThatCannotBeStoredOrShown:
    """Non-finite values and a percentage above one hundred, refused.

    Both were accepted until an independent review reproduced them. They are
    kept in a class of their own because they are a different kind of defect
    from the malformed cases above: those are documents a person got wrong,
    and these are documents that parse, persist, and then break something far
    away from the parser that let them in.
    """

    @pytest.mark.parametrize(
        "value", [float("nan"), float("inf"), float("-inf")], ids=str
    )
    @families
    def test_a_non_finite_value_is_refused(self, value, parse, refusal) -> None:
        """`nan < 0` and `inf < 0` are both False.

        So a range written as a pair of comparisons admits them, which is
        exactly what happened: the negativity check below was the only numeric
        rule and both slipped past it.
        """
        with pytest.raises(refusal) as error:
            parse([{**generator_properties()[0], "value": value}])

        assert "must be a finite number" in str(error.value)

    @families
    def test_a_finite_value_still_parses(self, parse, refusal) -> None:
        """Non-vacuous: the rule is about finiteness and not about numbers."""
        component = parse([{**generator_properties()[0], "value": 0.42}])

        assert component.properties[0].value == 0.42

    @pytest.mark.parametrize("value", [101, 100.5, -0.5], ids=str)
    @families
    def test_a_percentage_outside_its_own_range_is_refused(
        self, value, parse, refusal
    ) -> None:
        """A percentage of what a component holds cannot exceed all of it.

        The bound is the unit's rather than the property's
        (`UNIT_RANGES`): keying it on `%` states a fact about the quantity,
        where a per-property range table would be a general validation
        mechanism a four-member vocabulary has not earned.
        """
        with pytest.raises(refusal):
            parse(
                [
                    {
                        **generator_properties()[0],
                        "property_key": "reserve-state-of-charge",
                        "unit": "%",
                        "value": value,
                    }
                ]
            )

    @pytest.mark.parametrize("value", [0, 25, 100], ids=str)
    @families
    def test_a_percentage_inside_it_parses(self, value, parse, refusal) -> None:
        """Non-vacuous, and the endpoints are included deliberately: an empty
        reserve and a full one are both declarable."""
        component = parse(
            [
                {
                    **generator_properties()[0],
                    "property_key": "reserve-state-of-charge",
                    "unit": "%",
                    "value": value,
                }
            ]
        )

        assert component.properties[0].value == float(value)

    @families
    def test_a_unit_with_no_implied_range_is_left_alone(
        self, parse, refusal
    ) -> None:
        """`L/kWh` has no natural ceiling and does not get an invented one."""
        component = parse([{**generator_properties()[0], "value": 9_999.0}])

        assert component.properties[0].value == 9_999.0

    def test_an_infinite_value_never_reaches_the_store(self, tmp_path) -> None:
        """Parse-level refusal is not by itself evidence the store is safe.

        The review got positive infinity into a real writable Site store
        through the parser, so this goes through the write path rather than
        the parser alone. The template record is constructed directly rather
        than parsed, which is the only way such a value can still exist: it
        stands for a record that reached the creation service from somewhere
        this test cannot foresee.

        What is proved is the guarantee the creation service actually makes -
        **the materialized document is validated before anything is written**.
        The store is left empty, which is the half a parser test cannot show.
        """
        from assetops_backend.sites.adapters.yaml_user_site_store import (
            WritableYamlSiteStore,
        )
        from assetops_backend.sites.models import (
            ComponentProperty,
            SiteTemplate,
            TemplateComponent,
            TemplateFoundation,
        )
        from assetops_backend.sites.ports import SiteConfigurationInvalid
        from assetops_backend.sites.service import SiteCreationService
        from assetops_backend.sites.site_parsing import CreateSiteRequest

        root = tmp_path / "sites"
        store = WritableYamlSiteStore(root)

        def template_with_value(value: float) -> SiteTemplate:
            return SiteTemplate(
                template_id="test-archetype",
                template_version=2,
                display_name="Test Archetype",
                foundation=TemplateFoundation(
                    site_type="MINIGRID",
                    summary="A template used by tests only.",
                    components=(
                        TemplateComponent(
                            component_id="generator",
                            component_type="GENERATOR",
                            display_name="Diesel generator",
                            rating=None,
                            properties=(
                                ComponentProperty(
                                    property_key="specific-fuel-consumption",
                                    value=value,
                                    unit="L/kWh",
                                    kind="PHYSICAL",
                                    source="TEMPLATE",
                                    source_version=2,
                                ),
                            ),
                        ),
                    ),
                ),
            )

        class Catalog:
            def __init__(self, template: SiteTemplate) -> None:
                self.template = template

            def list_templates(self):
                return (self.template,)

            def get_template(self, template_id: str) -> SiteTemplate:
                return self.template

        def create(value: float, site_id: str) -> None:
            SiteCreationService(
                store, Catalog(template_with_value(value))
            ).create_site_from_template(
                CreateSiteRequest(
                    template_id="test-archetype",
                    site_id=site_id,
                    display_name="A site",
                    country="Uganda",
                    locality="Kalangala",
                    timezone="Africa/Kampala",
                )
            )

        with pytest.raises(SiteConfigurationInvalid) as error:
            create(float("inf"), "MG-900")

        assert "must be a finite number" in str(error.value)
        assert store.list_sites() == ()
        assert not list(root.glob("*.yaml")) if root.exists() else True

        # Non-vacuous: the same path with a finite value does write, so the
        # empty store above is the refusal and not a broken fixture.
        create(0.311, "MG-901")
        assert [site.site_id for site in store.list_sites()] == ["MG-901"]
