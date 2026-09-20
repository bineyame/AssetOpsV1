"""The breaker and control-state vocabulary ban, over the scenario domain.

T014's scan reads `assetops_backend.sites.models` and nothing else, so it would
never see a scenario. The scenario domain is exactly where the vocabulary would
arrive next: an equipment or intervention entry is the natural place to write
down what a breaker did, and a taxonomy value is the natural place to put it.

So the protection grows to three surfaces, and all three are scanned here:

1. the scenario domain model and the parser's key vocabularies - what the code
   will accept;
2. `config/scenarios/fuel-loss-event.yaml` - what the product ships;
3. `backend/tests/scenario_fixtures.py` - what the tests author. A fixture is
   where a banned term would most plausibly arrive first, because a test needs
   a value and nobody reviews a fixture the way they review shipped content.

The ban is unconditional. It is not "if a typed taxonomy is introduced": the
taxonomy IS typed - the parser refuses an unsupported entry kind, category,
oracle kind, unit and target policy - so a conditional ban would be a rule
whose condition is already met and which therefore reads as though it might
not be.

Each scan asserts its own input is non-empty before asserting the ban. A scan
that found no vocabulary, no key and no enumerated value would pass on a tree
where the scenario domain had been deleted, which is the failure shape this
project has shipped six times.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from control_vocabulary import (
    BANNED_CONTROL_VOCABULARY,
    banned_terms_in,
    refusal,
    schema_vocabulary,
    tokens_of,
)
from scenario_fixtures import scenario_document

import assetops_backend.scenarios.models as scenario_models
import assetops_backend.scenarios.parsing as scenario_parsing

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

        Both halves are asserted: a document with keys but no enumerated values
        would make the value half of the ban vacuous, and that half is the one
        a taxonomy value would land in.
        """
        found = list(schema_vocabulary(shipped_document()))

        keys = [term for kind, term in found if kind == "key"]
        values = [term for kind, term in found if kind == "value"]

        assert len(keys) > 20, keys
        assert len(values) > 5, values

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

    def test_a_banned_parameter_key_is_caught(self) -> None:
        document = scenario_document()
        document["timeline"][0]["parameters"][0]["breaker_position"] = "x"

        assert banned_terms_in(document)

    def test_a_banned_entry_kind_is_caught(self) -> None:
        document = scenario_document()
        document["timeline"][0]["entry_kind"] = "MANUAL_OVERRIDE"

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
