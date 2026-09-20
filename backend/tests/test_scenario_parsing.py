"""Strict-validation tests for ScenarioDefinition documents.

The scenario parser is the only thing standing between a defective definition
and a screen that renders it as though it were true. A timeline whose entries
share an identity, a version field a run could not freeze, or a target-site
declaration that means two contradictory things would all present as a normal
scenario, and nothing downstream could tell.

Every refusal below names one rule and breaks the canonical document in exactly
one way, so a passing test is about the rule in its name.

What is NOT tested here, because it is not the parser's job: whether the
declared target Site exists. That is resolved by `ScenarioDetailService` and
covered in `test_scenarios_api.py`. A parser that answered it would make a
shipped scenario unreadable on a machine where the Site had not been
configured, and would put a Site-store read inside document validation.
"""

from __future__ import annotations

import copy
from typing import Any, Callable

import pytest
from scenario_fixtures import scenario_document

from assetops_backend.scenarios.models import (
    EVENT_CATEGORIES,
    EXPECTATION_KINDS,
    PARAMETER_UNITS,
    SCENARIO_VERSION_FIELDS,
    TARGET_SITE_POLICIES,
    TIMELINE_ENTRY_KINDS,
)
from assetops_backend.scenarios.parsing import parse_scenario_document
from assetops_backend.scenarios.ports import ScenarioConfigurationInvalid

Mutation = Callable[[dict[str, Any]], None]


def parse(document: dict[str, Any], *, origin: str = "SHIPPED"):
    return parse_scenario_document(document, source="a test", origin=origin)


def mutated(mutate: Mutation) -> dict[str, Any]:
    document = copy.deepcopy(scenario_document())
    mutate(document)
    return document


class TestTheCanonicalDocumentParses:
    """Without this, every refusal below could pass for the wrong reason."""

    def test_the_fixture_is_valid(self) -> None:
        record = parse(scenario_document())

        assert record.scenario_id == "example-scenario"
        assert record.version.scenario_version == 2
        assert record.version.supersedes == 1
        assert len(record.timeline) == 3
        assert len(record.public_parameters) == 2
        assert len(record.private_expectations) == 1

    def test_origin_comes_from_the_store_and_not_the_document(self) -> None:
        """A user document that could claim SHIPPED would be claiming
        provenance it does not have."""
        assert parse(scenario_document(), origin="USER").origin == "USER"

        with pytest.raises(ScenarioConfigurationInvalid):
            parse(scenario_document(), origin="INVENTED")

        document = scenario_document()
        document["origin"] = "SHIPPED"
        with pytest.raises(ScenarioConfigurationInvalid):
            parse(document, origin="USER")


UNKNOWN_KEYS: list[Any] = [
    pytest.param(lambda d: d.update(seed=42), id="scenario"),
    pytest.param(lambda d: d["version"].update(label="1.0"), id="version"),
    pytest.param(
        lambda d: d["target_site"].update(site_type="MINIGRID"), id="target-site"
    ),
    pytest.param(
        lambda d: d["timeline"][0].update(at="2026-01-01T00:00:00Z"),
        id="timeline-entry",
    ),
    pytest.param(
        lambda d: d["timeline"][0]["parameters"][0].update(source="meter"),
        id="entry-parameter",
    ),
    pytest.param(
        lambda d: d["public_parameters"][0].update(private=True),
        id="public-parameter",
    ),
    pytest.param(
        lambda d: d["private_expectations"][0].update(severity="HIGH"),
        id="private-expectation",
    ),
]


@pytest.mark.parametrize("mutate", UNKNOWN_KEYS)
def test_an_unknown_key_is_refused(mutate: Mutation) -> None:
    with pytest.raises(ScenarioConfigurationInvalid, match="Unknown"):
        parse(mutated(mutate))


UNSUPPORTED_TAXONOMY_VALUES: list[Any] = [
    pytest.param(
        lambda d: d["timeline"][0].update(entry_kind="INJECTION"),
        id="entry-kind",
    ),
    pytest.param(
        lambda d: d["timeline"][0].update(category="FUEL"), id="category"
    ),
    pytest.param(
        lambda d: d["timeline"][0].update(category="load"), id="category-case"
    ),
    pytest.param(
        lambda d: d["target_site"].update(policy="ANY_SITE"), id="target-policy"
    ),
    pytest.param(
        lambda d: d["private_expectations"][0].update(oracle_kind="SEVERITY"),
        id="oracle-kind",
    ),
    pytest.param(
        lambda d: d["public_parameters"][0].update(unit="litres"),
        id="parameter-unit",
    ),
]


@pytest.mark.parametrize("mutate", UNSUPPORTED_TAXONOMY_VALUES)
def test_an_unsupported_taxonomy_value_is_refused(mutate: Mutation) -> None:
    """The taxonomy is closed, so it is typed.

    An unsupported value would put a category on a screen, and later into a
    run and a simulator, that nothing in the product can interpret.
    """
    with pytest.raises(ScenarioConfigurationInvalid):
        parse(mutated(mutate))


MALFORMED_VERSION_FIELDS: list[Any] = [
    pytest.param(lambda d: d.update(version=None), id="absent"),
    pytest.param(lambda d: d.update(version="2"), id="not-an-object"),
    pytest.param(
        lambda d: d["version"].update(scenario_version="2"), id="version-text"
    ),
    pytest.param(
        lambda d: d["version"].update(scenario_version=0), id="version-zero"
    ),
    pytest.param(
        lambda d: d["version"].update(scenario_version=True), id="version-bool"
    ),
    pytest.param(
        lambda d: d["version"].update(scenario_version=2.5), id="version-float"
    ),
    pytest.param(
        lambda d: d["version"].update(version_valid_from="2026-01-01"),
        id="valid-from-date-only",
    ),
    pytest.param(
        lambda d: d["version"].update(version_valid_from="2026-01-01T00:00:00+02:00"),
        id="valid-from-offset",
    ),
    pytest.param(
        lambda d: d["version"].update(supersedes=2), id="supersedes-itself"
    ),
    pytest.param(
        lambda d: d["version"].update(supersedes=3), id="supersedes-the-future"
    ),
    pytest.param(
        lambda d: d["version"].update(supersedes="1"), id="supersedes-text"
    ),
]


@pytest.mark.parametrize("mutate", MALFORMED_VERSION_FIELDS)
def test_a_malformed_version_field_is_refused(mutate: Mutation) -> None:
    with pytest.raises(ScenarioConfigurationInvalid):
        parse(mutated(mutate))


def test_scenario_identity_and_version_are_distinct() -> None:
    """Two documents, same identity, different versions: one scenario.

    The invariant is settled even while the field list is provisional. If a
    version could be part of identity, a run that froze one would be pointing
    at a different scenario than the catalog lists.
    """
    first = parse(scenario_document())

    second_document = scenario_document()
    second_document["version"]["scenario_version"] = 3
    second_document["version"]["supersedes"] = 2
    second = parse(second_document)

    assert first.scenario_id == second.scenario_id
    assert first.version.scenario_version != second.version.scenario_version


def test_the_proposed_version_field_list_matches_what_the_parser_accepts() -> None:
    """The proposal on the screen and the fields in the code are one list.

    `SCENARIO_VERSION_FIELDS` is what the detail screen puts in front of the
    user for review. If the parser accepted a field the proposal did not name,
    or the proposal named one the parser did not accept, accepting the screen
    would settle something other than what shipped.
    """
    from assetops_backend.scenarios.parsing import VERSION_KEYS

    assert set(SCENARIO_VERSION_FIELDS) == {"scenario_id"} | set(VERSION_KEYS)


DUPLICATE_TIMELINE_IDENTITIES: list[Any] = [
    pytest.param(
        lambda d: d["timeline"][1].update(event_id="first-entry"),
        id="duplicate-event-id",
    ),
    pytest.param(
        lambda d: d["timeline"][1]["parameters"].append(
            {
                "parameter_id": "peak-demand",
                "display_name": "Again",
                "value": 1,
                "unit": "kW",
            }
        )
        or d["timeline"][1]["parameters"].append(
            {
                "parameter_id": "peak-demand",
                "display_name": "And again",
                "value": 2,
                "unit": "kW",
            }
        ),
        id="duplicate-parameter-id",
    ),
    pytest.param(
        lambda d: d["public_parameters"][1].update(
            parameter_id="quantity-parameter"
        ),
        id="duplicate-public-parameter-id",
    ),
    pytest.param(
        lambda d: d["private_expectations"].append(
            copy.deepcopy(d["private_expectations"][0])
        ),
        id="duplicate-expectation-id",
    ),
]


@pytest.mark.parametrize("mutate", DUPLICATE_TIMELINE_IDENTITIES)
def test_a_duplicate_identity_is_refused(mutate: Mutation) -> None:
    """A timeline identity is stable within a version because a future run
    refers to one by `(scenario_id, scenario_version, event_id)`."""
    with pytest.raises(ScenarioConfigurationInvalid, match="Duplicate"):
        parse(mutated(mutate))


MALFORMED_ORDERING_OR_OFFSETS: list[Any] = [
    pytest.param(
        lambda d: d["timeline"][1].update(sequence=1), id="sequence-repeats"
    ),
    pytest.param(
        lambda d: d["timeline"][1].update(sequence=0), id="sequence-zero"
    ),
    pytest.param(
        lambda d: (
            d["timeline"][0].update(sequence=3),
            d["timeline"][2].update(sequence=1),
        ),
        id="sequence-decreases",
    ),
    pytest.param(
        lambda d: d["timeline"][0].update(sequence="1"), id="sequence-text"
    ),
    pytest.param(
        lambda d: d["timeline"][0].update(offset_minutes=-1),
        id="offset-negative",
    ),
    pytest.param(
        lambda d: d["timeline"][0].update(offset_minutes=10_001),
        id="offset-beyond-the-bound",
    ),
    pytest.param(
        lambda d: d["timeline"][0].update(offset_minutes=1.5),
        id="offset-fractional",
    ),
    pytest.param(
        lambda d: d["timeline"][0].update(offset_minutes="0"), id="offset-text"
    ),
    pytest.param(
        lambda d: d["timeline"][0].update(offset_minutes=True), id="offset-bool"
    ),
    pytest.param(lambda d: d.update(timeline=[]), id="empty-timeline"),
    pytest.param(lambda d: d.update(timeline={}), id="timeline-not-a-list"),
]


@pytest.mark.parametrize("mutate", MALFORMED_ORDERING_OR_OFFSETS)
def test_malformed_ordering_or_offsets_are_refused(mutate: Mutation) -> None:
    with pytest.raises(ScenarioConfigurationInvalid):
        parse(mutated(mutate))


MISPLACED_PRIVATE_EXPECTATIONS: list[Any] = [
    pytest.param(
        lambda d: d["timeline"][0].update(expected_outcome="detected"),
        id="expected-on-a-timeline-entry",
    ),
    pytest.param(
        lambda d: d["timeline"][0].update(oracle_kind="DETECTION"),
        id="oracle-kind-on-a-timeline-entry",
    ),
    pytest.param(
        lambda d: d["timeline"][0].update(
            private_expectations=[{"expectation_id": "x"}]
        ),
        id="expectations-nested-in-a-timeline-entry",
    ),
    pytest.param(
        lambda d: d["public_parameters"][0].update(assertion="within 10 L"),
        id="assertion-on-a-public-parameter",
    ),
    pytest.param(
        lambda d: d["target_site"].update(expectation="site is reachable"),
        id="expectation-on-the-target-site",
    ),
]


@pytest.mark.parametrize("mutate", MISPLACED_PRIVATE_EXPECTATIONS)
def test_a_misplaced_private_expectation_field_is_refused(
    mutate: Mutation,
) -> None:
    """The refusal names the boundary rather than reporting an unknown key.

    An author who writes an expectation into a public section has made a
    boundary mistake, not a typo, and the copy should say which section the
    field belongs in.
    """
    with pytest.raises(
        ScenarioConfigurationInvalid, match="Private expectation keys"
    ):
        parse(mutated(mutate))


MALFORMED_TARGET_SITE_DECLARATIONS: list[Any] = [
    pytest.param(lambda d: d.update(target_site=None), id="absent"),
    pytest.param(lambda d: d.update(target_site="MG-900"), id="not-an-object"),
    pytest.param(
        lambda d: d["target_site"].update(site_id="../../etc/passwd"),
        id="site-id-traversal",
    ),
    pytest.param(
        lambda d: d["target_site"].update(site_id="MG 900"),
        id="site-id-with-a-space",
    ),
    pytest.param(
        lambda d: d["target_site"].update(site_id=900), id="site-id-not-text"
    ),
    pytest.param(
        lambda d: d["target_site"].update(requirement=""),
        id="requirement-empty",
    ),
    pytest.param(
        lambda d: d["target_site"].pop("requirement"), id="requirement-absent"
    ),
]


@pytest.mark.parametrize("mutate", MALFORMED_TARGET_SITE_DECLARATIONS)
def test_a_malformed_target_site_declaration_is_refused(
    mutate: Mutation,
) -> None:
    with pytest.raises(ScenarioConfigurationInvalid):
        parse(mutated(mutate))


INVALID_TARGET_SITE_POLICY_SHAPES: list[Any] = [
    pytest.param(
        lambda d: d["target_site"].update(site_id=None),
        id="declared-site-without-a-site",
    ),
    pytest.param(
        lambda d: d["target_site"].update(template_id="hybrid-mini-grid-100kw"),
        id="declared-site-with-a-template",
    ),
    pytest.param(
        lambda d: d["target_site"].update(policy="TEMPLATE_DERIVED"),
        id="template-derived-with-a-site",
    ),
    pytest.param(
        lambda d: d["target_site"].update(
            policy="TEMPLATE_DERIVED", site_id=None, template_id=None
        ),
        id="template-derived-without-a-template",
    ),
    pytest.param(
        lambda d: d["target_site"].update(
            policy="TEMPLATE_DERIVED", site_id=None, template_id="Not An Id"
        ),
        id="template-derived-with-a-malformed-template",
    ),
]


@pytest.mark.parametrize("mutate", INVALID_TARGET_SITE_POLICY_SHAPES)
def test_an_invalid_target_site_policy_shape_is_refused(
    mutate: Mutation,
) -> None:
    """A declaration that looks complete and means two contradictory things.

    Worth its own family: the fields are all well formed individually, and it
    is only the combination that is wrong.
    """
    with pytest.raises(ScenarioConfigurationInvalid):
        parse(mutated(mutate))


def test_a_template_derived_target_parses_with_no_site() -> None:
    """The other policy is real, not a value nothing can use."""
    document = scenario_document()
    document["target_site"] = {
        "policy": "TEMPLATE_DERIVED",
        "site_id": None,
        "template_id": "hybrid-mini-grid-100kw",
        "requirement": "A site built from the hybrid mini-grid archetype.",
    }

    target = parse(document).target_site

    assert target.policy == "TEMPLATE_DERIVED"
    assert target.site_id is None
    assert target.template_id == "hybrid-mini-grid-100kw"


MALFORMED_PARAMETERS: list[Any] = [
    pytest.param(
        lambda d: d["public_parameters"][0].update(unit=None),
        id="number-without-a-unit",
    ),
    pytest.param(
        lambda d: d["public_parameters"][1].update(unit="kW"),
        id="text-with-a-unit",
    ),
    pytest.param(
        lambda d: d["public_parameters"][0].update(value=True),
        id="value-is-a-flag",
    ),
    pytest.param(
        lambda d: d["public_parameters"][0].update(value=None),
        id="value-absent",
    ),
    pytest.param(
        lambda d: d["public_parameters"][0].update(parameter_id="Peak Demand"),
        id="parameter-id-not-an-identifier",
    ),
]


@pytest.mark.parametrize("mutate", MALFORMED_PARAMETERS)
def test_a_malformed_parameter_is_refused(mutate: Mutation) -> None:
    with pytest.raises(ScenarioConfigurationInvalid):
        parse(mutated(mutate))


class TestVocabulariesAreNotVacuous:
    def test_no_closed_vocabulary_is_empty(self) -> None:
        """A vacuous allowlist accepts everything it is asked about."""
        for vocabulary in (
            TIMELINE_ENTRY_KINDS,
            EVENT_CATEGORIES,
            PARAMETER_UNITS,
            EXPECTATION_KINDS,
            TARGET_SITE_POLICIES,
        ):
            assert len(vocabulary) > 0

    def test_the_proposed_taxonomy_is_the_seven_the_checkpoint_asks_about(
        self,
    ) -> None:
        """The proposal on the screen is the vocabulary in the code.

        An eighth category added here without the review being asked about it
        would make accepting the screen settle something the screen never
        showed.
        """
        assert EVENT_CATEGORIES == frozenset(
            {
                "LOAD",
                "WEATHER",
                "EQUIPMENT",
                "DATA_QUALITY",
                "LOSS_OR_FRAUD",
                "INTERVENTION",
                "MAINTENANCE",
            }
        )

    def test_scenario_parameter_units_are_separate_from_site_vocabularies(
        self,
    ) -> None:
        """A nameplate rating, a reportable signal and an authored scenario
        parameter are three different kinds of fact."""
        from assetops_backend.sites.models import RATING_UNITS, SIGNAL_UNITS

        assert PARAMETER_UNITS is not RATING_UNITS
        assert PARAMETER_UNITS is not SIGNAL_UNITS
        assert "L/h" in PARAMETER_UNITS
        assert "L/h" not in RATING_UNITS and "L/h" not in SIGNAL_UNITS
        assert "kVA" in RATING_UNITS and "kVA" not in PARAMETER_UNITS
