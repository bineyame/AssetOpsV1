"""The breaker and control-state vocabulary ban, over the scenario domain.

T014's scan reads `assetops_backend.sites.models` and nothing else, so it would
never see a scenario. The scenario domain is exactly where the vocabulary would
arrive next: an equipment or intervention entry is the natural place to write
down what a breaker did, and a taxonomy value is the natural place to put it.

So the protection covers four surfaces, and all four are exercised here:

1. the scenario domain model and the parser's key vocabularies - what the code
   will accept;
2. `config/scenarios/fuel-loss-event.yaml` - what the product ships;
3. `backend/tests/scenario_fixtures.py` - what the tests author. A fixture is
   where a banned term would most plausibly arrive first, because a test needs
   a value and nobody reviews a fixture the way they review shipped content;
4. the identifiers a document may carry, refused by the PARSER at parse time
   rather than only by a scan, so a user-authored document in `var/scenarios/`
   that no test ever sees is refused too.

The ban is unconditional. It is not "if a typed taxonomy is introduced": the
taxonomy IS typed - the parser refuses an unsupported entry kind, category,
oracle kind, unit and target policy - so a conditional ban would be a rule
whose condition is already met and which therefore reads as though it might
not be.

## What the T017 review found here

The scan originally read mapping keys and upper-snake enum values only. A
scenario parameter key is neither: it is the lowercase identifier in the
`parameter_id` FIELD. So `parameter_id: breaker-position` passed the guard AND
the parser, and so did `event_id: auto-mode-change` and a `scenario_id` built
the same way.

The four deliberate violations the slice shipped did not find it, and the
reason is worth keeping: the parameter proof added `breaker_position` as a
mapping KEY, which the strict parser already refuses as an unknown key. It
failed, it failed loudly, and it never reached the vocabulary scan at all - it
passed for the wrong reason. A deliberate violation has to be one the rest of
the system would otherwise accept.

`TestAnAcceptedDocumentCannotCarryBannedVocabulary` below is the permanent form
of that: every document it builds is valid apart from one identifier, so the
only thing that can refuse it is the vocabulary rule.

Each scan asserts its own input is non-empty before asserting the ban. A scan
that found no vocabulary, no key, no enumerated value or no identifier would
pass on a tree where the scenario domain had been deleted, which is the failure
shape this project has now shipped seven times.
"""

from __future__ import annotations

from pathlib import Path

import yaml
import pytest
from control_vocabulary import (
    BANNED_CONTROL_VOCABULARY,
    IDENTIFIER_VALUED_KEYS,
    banned_terms_in,
    refusal,
    schema_vocabulary,
    tokens_of,
)
from scenario_fixtures import scenario_document

import assetops_backend.scenarios.models as scenario_models
import assetops_backend.scenarios.parsing as scenario_parsing
from assetops_backend.scenarios.parsing import parse_scenario_document
from assetops_backend.scenarios.ports import ScenarioConfigurationInvalid

REPO_ROOT = Path(__file__).resolve().parents[2]
SHIPPED_FUEL_LOSS_EVENT = REPO_ROOT / "config" / "scenarios" / "fuel-loss-event.yaml"


def shipped_document() -> object:
    return yaml.safe_load(SHIPPED_FUEL_LOSS_EVENT.read_text(encoding="utf-8"))


class TestTheScenarioDomainModel:
    def test_no_scenario_vocabulary_declares_a_position_or_a_mode(self) -> None:
        vocabularies = {
            f"{module.__name__}.{name}": value
            for module in (scenario_models, scenario_parsing)
            for name, value in vars(module).items()
            if isinstance(value, frozenset)
        }
        assert vocabularies, (
            "the scenario vocabulary scan found no frozenset, so it is not "
            "proving anything. Update the scan, do not delete it."
        )

        offences = [
            f"{name} declares {value!r}"
            for name, vocabulary in vocabularies.items()
            for value in sorted(vocabulary)
            if tokens_of(value) & set(BANNED_CONTROL_VOCABULARY)
        ]

        assert not offences, refusal("The scenario domain", offences)

    def test_the_scan_covers_the_taxonomy_it_is_meant_to_cover(self) -> None:
        """Without this, the scan above could be reading five unrelated sets.

        The taxonomy vocabularies are the ones a breaker word would arrive in,
        so the scan has to be able to see them by the names they are declared
        under.
        """
        for name in (
            "TIMELINE_ENTRY_KINDS",
            "EVENT_CATEGORIES",
            "PARAMETER_UNITS",
            "EXPECTATION_KINDS",
            "TARGET_SITE_POLICIES",
        ):
            assert isinstance(getattr(scenario_models, name), frozenset)

        for name in ("SCENARIO_KEYS", "TIMELINE_ENTRY_KEYS", "PARAMETER_KEYS"):
            assert isinstance(getattr(scenario_parsing, name), frozenset)


class TestTheShippedDefinition:
    def test_the_shipped_definition_exists(self) -> None:
        assert SHIPPED_FUEL_LOSS_EVENT.is_file()

    def test_the_shipped_definition_has_schema_positions_to_scan(self) -> None:
        """Proves the scan below is over a non-empty set.

        All three halves are asserted. A document with keys but no enumerated
        values would make the value half vacuous, and that half is where a
        taxonomy value lands. A document with no identifiers would make the
        third half vacuous, and that is the half the T017 review found missing
        - so it is asserted here rather than assumed.
        """
        found = list(schema_vocabulary(shipped_document()))

        keys = [term for kind, term in found if kind == "key"]
        values = [term for kind, term in found if kind == "value"]
        identifiers = [term for kind, term in found if kind == "identifier"]

        assert len(keys) > 20, keys
        assert len(values) > 5, values
        assert len(identifiers) > 20, identifiers

    def test_the_shipped_definition_declares_no_position_or_mode(self) -> None:
        offences = banned_terms_in(shipped_document())

        assert not offences, refusal(
            "config/scenarios/fuel-loss-event.yaml", offences
        )


class TestTheParserFixtures:
    def test_the_fixture_has_schema_positions_to_scan(self) -> None:
        found = list(schema_vocabulary(scenario_document()))

        assert len([term for kind, term in found if kind == "key"]) > 20
        assert len([term for kind, term in found if kind == "value"]) > 5
        assert len([term for kind, term in found if kind == "identifier"]) > 5

    def test_the_fixture_declares_no_position_or_mode(self) -> None:
        offences = banned_terms_in(scenario_document())

        assert not offences, refusal(
            "backend/tests/scenario_fixtures.py", offences
        )


class TestTheScanCanActuallyFail:
    """The scan is only protection if a violation fails it.

    This is the fail-case anchor. It is not a substitute for the deliberate
    violation the slice carries in its review packet - that one proves the scan
    fails on the real model and the real shipped document - but it proves the
    mechanism itself is not inert, and it keeps proving it after the packet has
    been filed.
    """

    def test_a_banned_category_value_is_caught(self) -> None:
        document = scenario_document()
        document["timeline"][0]["category"] = "BREAKER_TRIPPED"

        offences = banned_terms_in(document)

        assert offences
        assert "BREAKER" in refusal("a test", offences) or any(
            "BREAKER" in offence for offence in offences
        )

    def test_a_banned_mapping_key_is_caught(self) -> None:
        """Kept, with what it actually proves written down.

        This is the shape the slice's original parameter proof used. It does
        prove the key half of the scan reaches a nested mapping - but as a
        refusal proof it is weak, because the parser refuses an unknown mapping
        key before the vocabulary rule is ever consulted. The identifier cases
        in `TestAnAcceptedDocumentCannotCarryBannedVocabulary` are the ones
        that prove the rule itself.
        """
        document = scenario_document()
        document["timeline"][0]["parameters"][0]["breaker_position"] = "x"

        assert banned_terms_in(document)

    def test_a_banned_entry_kind_is_caught(self) -> None:
        document = scenario_document()
        document["timeline"][0]["entry_kind"] = "MANUAL_OVERRIDE"

        assert banned_terms_in(document)

    @pytest.mark.parametrize(
        "mutate",
        [
            pytest.param(
                lambda d: d["timeline"][0]["parameters"][0].update(
                    parameter_id="breaker-position"
                ),
                id="parameter-id",
            ),
            pytest.param(
                lambda d: d["timeline"][0].update(event_id="auto-mode-change"),
                id="event-id",
            ),
            pytest.param(
                lambda d: d.update(scenario_id="breaker-trip-event"),
                id="scenario-id",
            ),
            pytest.param(
                lambda d: d["private_expectations"][0].update(
                    expectation_id="manual-override-is-detected"
                ),
                id="expectation-id",
            ),
        ],
    )
    def test_a_banned_identifier_is_caught(self, mutate) -> None:
        """The half the scan was missing, over every identifier it owns."""
        document = scenario_document()
        mutate(document)

        assert banned_terms_in(document)

    def test_free_text_prose_is_not_a_schema_position(self) -> None:
        """The ban is about vocabulary, not about English.

        Without this the scan would be over-broad, and an over-broad guard gets
        relaxed the first time it blocks something legitimate - which is how a
        guard stops being one.
        """
        document = scenario_document()
        document["timeline"][0]["description"] = (
            "The valve was closed and the generator ran in manual mode."
        )

        assert not banned_terms_in(document)


class TestTheIdentifierAuditIsComplete:
    """Every identifier-valued position is classified, not just the one found.

    An `_id` field in the scenario schema is an identifier-valued position by
    construction. Each one is either vocabulary this domain owns - scanned and
    refused - or a reference into another identity space, which is deliberately
    excluded and named here. A new `_id` field added to the schema fails this
    until somebody decides which it is, which is the point: the review found
    one missing position, and the answer to that is not to fix one position.
    """

    #: References into other identity spaces. The scenario domain does not own
    #: how a Site or a site template is named, and refusing a token there would
    #: refuse a legitimately-named Site rather than protect scenario vocabulary.
    NOT_SCENARIO_VOCABULARY = frozenset({"site_id", "template_id"})

    def test_every_identifier_field_in_the_schema_is_classified(self) -> None:
        schema_keys = set().union(
            scenario_parsing.SCENARIO_KEYS,
            scenario_parsing.VERSION_KEYS,
            scenario_parsing.TARGET_SITE_KEYS,
            scenario_parsing.TIMELINE_ENTRY_KEYS,
            scenario_parsing.PARAMETER_KEYS,
            scenario_parsing.EXPECTATION_KEYS,
        )

        identifier_fields = {key for key in schema_keys if key.endswith("_id")}
        assert identifier_fields, (
            "the audit found no identifier field in the scenario schema, so it "
            "is not proving anything. Update the audit, do not delete it."
        )

        unclassified = identifier_fields - IDENTIFIER_VALUED_KEYS - self.NOT_SCENARIO_VOCABULARY
        assert not unclassified, (
            f"Identifier fields {sorted(unclassified)} are in the scenario "
            "schema but are neither scanned as scenario vocabulary nor named "
            "as references into another identity space. Decide which they are: "
            "an identifier is rendered as the name of a thing, so an "
            "unclassified one is a position the breaker/control ban does not "
            "reach."
        )

    def test_nothing_is_scanned_that_the_schema_does_not_declare(self) -> None:
        """The other direction: a scanned key nothing declares is dead."""
        schema_keys = set().union(
            scenario_parsing.SCENARIO_KEYS,
            scenario_parsing.TIMELINE_ENTRY_KEYS,
            scenario_parsing.PARAMETER_KEYS,
            scenario_parsing.EXPECTATION_KEYS,
        )

        assert IDENTIFIER_VALUED_KEYS <= schema_keys


class TestAnAcceptedDocumentCannotCarryBannedVocabulary:
    """The permanent proof, on documents the rest of the parser accepts.

    Each document below differs from the valid fixture in exactly one
    identifier, and that identifier is well formed: lowercase alphanumeric
    words separated by hyphens, the shape the parser has always accepted. So
    the refusal cannot come from an unknown key, a malformed identifier, or an
    unsupported enum value. The only rule that can refuse it is the
    breaker/control vocabulary rule, which is what makes this a proof rather
    than a coincidence.
    """

    BANNED_IDENTIFIERS = [
        pytest.param(
            lambda d: d["timeline"][0]["parameters"][0].update(
                parameter_id="breaker-position"
            ),
            "parameter_id",
            id="parameter-id",
        ),
        pytest.param(
            lambda d: d["public_parameters"][0].update(parameter_id="auto-mode"),
            "parameter_id",
            id="public-parameter-id",
        ),
        pytest.param(
            lambda d: d["timeline"][0].update(event_id="breaker-tripped"),
            "event_id",
            id="event-id",
        ),
        pytest.param(
            lambda d: d.update(scenario_id="manual-transfer-event"),
            "scenario_id",
            id="scenario-id",
        ),
        pytest.param(
            lambda d: d["private_expectations"][0].update(
                expectation_id="breaker-state-is-reported"
            ),
            "expectation_id",
            id="expectation-id",
        ),
    ]

    @pytest.mark.parametrize("mutate,field", BANNED_IDENTIFIERS)
    def test_the_parser_refuses_it(self, mutate, field: str) -> None:
        document = scenario_document()
        mutate(document)

        with pytest.raises(
            ScenarioConfigurationInvalid, match="control-state vocabulary"
        ) as refused:
            parse_scenario_document(document, source="a test", origin="SHIPPED")

        assert field in str(refused.value)

    @pytest.mark.parametrize("mutate,field", BANNED_IDENTIFIERS)
    def test_the_scan_reports_it(self, mutate, field: str) -> None:
        document = scenario_document()
        mutate(document)

        offences = banned_terms_in(document)

        assert offences
        assert any(offence.startswith("identifier ") for offence in offences)

    @pytest.mark.parametrize("mutate,field", BANNED_IDENTIFIERS)
    def test_the_same_document_is_valid_without_that_one_change(
        self, mutate, field: str
    ) -> None:
        """Without this, the refusals above could be about anything.

        The fixture is parsed unmutated, so the only difference between a
        document that parses and one that is refused is the identifier. That is
        what the original `breaker_position: CLOSED` proof could not say: the
        document it built was refused for being malformed, and would have been
        refused with the vocabulary rule deleted.
        """
        parse_scenario_document(
            scenario_document(), source="a test", origin="SHIPPED"
        )

    def test_the_banned_identifiers_are_well_formed(self) -> None:
        """They pass the shape rule, so only the vocabulary rule can refuse."""
        for identifier in (
            "breaker-position",
            "auto-mode",
            "breaker-tripped",
            "manual-transfer-event",
            "breaker-state-is-reported",
        ):
            assert scenario_parsing.IDENTIFIER_PATTERN.match(identifier)
