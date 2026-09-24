"""Strict-parser tests for shipped Site template documents.

The parser is the YAML-configuration-authority seam for templates. These tests
cover the two refusals that carry product meaning - a template claiming Site
identity or Site lifecycle - and the ordinary-but-necessary refusals that keep
a defective or pathological document out of the product.
"""

from __future__ import annotations

import copy
from typing import Any

import pytest

from assetops_backend.sites.models import SiteTemplate
from assetops_backend.sites.parsing import (
    MAX_COMPONENTS,
    MAX_DOCUMENT_TEXT_LENGTH,
    parse_site_template,
)
from assetops_backend.sites.ports import SiteTemplateConfigurationInvalid


def valid_document() -> dict[str, Any]:
    return {
        "template_id": "test-archetype",
        "template_version": 2,
        "display_name": "Test Archetype",
        "foundation": {
            "site_type": "MINIGRID",
            "summary": "A template used by tests only.",
            "components": [
                {
                    "component_id": "pv-array",
                    "component_type": "PV_ARRAY",
                    "display_name": "PV array",
                    "rating": {"value": 100, "unit": "kW"},
                },
                {
                    "component_id": "site-meter",
                    "component_type": "METER",
                    "display_name": "Site meter",
                    "rating": None,
                },
            ],
            **foundation_content(),
        },
    }


def foundation_content() -> dict[str, Any]:
    """The four sections T014 adds, over the two components above.

    Small on purpose - two components, two devices, three signals, two
    mappings, two assumptions - but it exercises every reference the validator
    checks: a node naming a component, a connection naming two nodes, a device
    naming a component, and a mapping naming a device, one of that device's
    declared signals, and a component.
    """
    return {
        "topology": {
            "nodes": [
                {
                    "node_id": "pv-array",
                    "component_id": "pv-array",
                    "node_role": "GENERATION",
                },
                {
                    "node_id": "site-meter",
                    "component_id": "site-meter",
                    "node_role": "METERING",
                },
            ],
            "connections": [
                {
                    "connection_id": "array-to-meter",
                    "from_node": "pv-array",
                    "to_node": "site-meter",
                    "medium": "AC",
                }
            ],
        },
        "devices": [
            {
                "device_id": "pv-inverter-controller",
                "device_type": "CONTROLLER",
                "display_name": "PV inverter controller",
                "component_id": "pv-array",
                "signals": [
                    {
                        "signal_id": "ac-power",
                        "display_name": "AC output power",
                        "unit": "kW",
                    },
                    {
                        "signal_id": "lifetime-energy",
                        "display_name": "Lifetime energy delivered",
                        "unit": "kWh",
                    },
                ],
            },
            {
                "device_id": "site-meter-unit",
                "device_type": "METER",
                "display_name": "Site meter",
                "component_id": "site-meter",
                "signals": [
                    {
                        "signal_id": "bus-voltage",
                        "display_name": "Bus voltage",
                        "unit": "V",
                    }
                ],
            },
        ],
        "signal_mappings": [
            {
                "mapping_id": "pv-ac-power",
                "device_id": "pv-inverter-controller",
                "signal_id": "ac-power",
                "component_id": "pv-array",
            },
            {
                "mapping_id": "meter-bus-voltage",
                "device_id": "site-meter-unit",
                "signal_id": "bus-voltage",
                "component_id": "site-meter",
            },
        ],
        "control_assumptions": [
            {
                "assumption_id": "solar-first-dispatch",
                "display_name": "Solar is dispatched first",
                "component_id": None,
                "basis": "TEMPLATE",
                "statement": "A declared assumption about intended operation.",
            },
            {
                "assumption_id": "one-metering-point",
                "display_name": "One billing-relevant metering point",
                "component_id": "site-meter",
                "basis": "TEMPLATE",
                "statement": "The site meter is the one billing-relevant point.",
            },
        ],
    }


def without_foundation_content(document: dict[str, Any]) -> dict[str, Any]:
    """The same document with the four T014 sections left out entirely.

    Left out, not emptied. A foundation that declares no device says so by
    being silent; an empty list would be the document stating that the site has
    none, which is a different claim and one this schema refuses to let anyone
    make.
    """
    for key in ("topology", "devices", "signal_mappings", "control_assumptions"):
        document["foundation"].pop(key, None)
    return document


def parse(document: Any) -> SiteTemplate:
    return parse_site_template(document, source="test-document.yaml")


class TestValidDocument:
    def test_a_valid_document_parses_into_domain_records(self) -> None:
        template = parse(valid_document())

        assert template.template_id == "test-archetype"
        assert template.template_version == 2
        assert template.display_name == "Test Archetype"
        assert template.foundation.site_type == "MINIGRID"
        assert [c.component_id for c in template.foundation.components] == [
            "pv-array",
            "site-meter",
        ]
        assert template.foundation.components[0].rating is not None
        assert template.foundation.components[0].rating.value == 100.0
        assert template.foundation.components[0].rating.unit == "kW"
        assert template.foundation.components[1].rating is None

    def test_the_parsed_record_carries_no_site_identity(self) -> None:
        """A template record must not be usable as, or mistakable for, a Site."""
        template = parse(valid_document())

        for field in ("site_id", "lifecycle_status", "location", "timezone"):
            assert not hasattr(template, field)
            assert not hasattr(template.foundation, field)


class TestATemplateIsNotASite:
    @pytest.mark.parametrize(
        "field",
        ["site_id", "lifecycle_status", "location", "timezone"],
    )
    def test_a_site_only_field_is_refused_by_name(self, field: str) -> None:
        document = valid_document()
        document[field] = "MG-001"

        with pytest.raises(SiteTemplateConfigurationInvalid, match=field):
            parse(document)

    @pytest.mark.parametrize("field", ["site_id", "lifecycle_status"])
    def test_a_site_only_field_inside_foundation_is_refused_by_name(
        self, field: str
    ) -> None:
        document = valid_document()
        document["foundation"][field] = "MG-001"

        with pytest.raises(SiteTemplateConfigurationInvalid, match=field):
            parse(document)


class TestStrictness:
    def test_there_is_no_lenient_path(self) -> None:
        """The only entry point is the strict one."""
        import assetops_backend.sites.parsing as parsing

        public = [name for name in dir(parsing) if not name.startswith("_")]

        # Two, and the second is the point: the Foundation content below the
        # component list is validated by `foundation_parsing`, which the Site
        # parser calls too. A template that grew its own copy of those rules
        # could accept a topology the Site store refuses, and the Site it
        # seeded would then be unreadable in the store it was written to.
        assert [name for name in public if name.startswith("parse")] == [
            "parse_component_properties",
            "parse_foundation_content",
            "parse_site_template",
        ]

    def test_the_foundation_content_validator_is_the_one_the_site_parser_uses(
        self,
    ) -> None:
        import assetops_backend.sites.parsing as parsing
        import assetops_backend.sites.site_parsing as site_parsing

        assert (
            parsing.parse_foundation_content is site_parsing.parse_foundation_content
        )
        assert (
            parsing.parse_component_properties
            is site_parsing.parse_component_properties
        )

    @pytest.mark.parametrize(
        "mutate",
        [
            pytest.param(lambda d: d.update(extra="x"), id="unknown-template-key"),
            pytest.param(
                lambda d: d["foundation"].update(extra="x"),
                id="unknown-foundation-key",
            ),
            pytest.param(
                lambda d: d["foundation"]["components"][0].update(extra="x"),
                id="unknown-component-key",
            ),
            pytest.param(
                lambda d: d["foundation"]["components"][0]["rating"].update(extra="x"),
                id="unknown-rating-key",
            ),
        ],
    )
    def test_unknown_keys_are_refused(self, mutate: Any) -> None:
        document = valid_document()
        mutate(document)

        with pytest.raises(SiteTemplateConfigurationInvalid, match="Unknown"):
            parse(document)

    @pytest.mark.parametrize(
        ("mutate", "message"),
        [
            pytest.param(
                lambda d: d.__setitem__("template_id", "Not An Id"),
                "template_id",
                id="identifier-charset",
            ),
            pytest.param(
                lambda d: d.__setitem__("template_id", "../escape"),
                "template_id",
                id="identifier-traversal",
            ),
            pytest.param(
                lambda d: d.__setitem__("template_version", "1"),
                "template_version",
                id="version-not-an-integer",
            ),
            pytest.param(
                lambda d: d.__setitem__("template_version", 0),
                "template_version",
                id="version-out-of-range",
            ),
            pytest.param(
                lambda d: d.__delitem__("foundation"),
                "foundation",
                id="missing-foundation",
            ),
            pytest.param(
                lambda d: d["foundation"].__setitem__("site_type", "MICROGRID"),
                "site_type",
                id="unsupported-site-type",
            ),
            pytest.param(
                lambda d: d["foundation"]["components"][0].__setitem__(
                    "component_type", "WIND_TURBINE"
                ),
                "component_type",
                id="unsupported-component-type",
            ),
            pytest.param(
                lambda d: d["foundation"]["components"][0]["rating"].__setitem__(
                    "unit", "megawatts"
                ),
                "unit",
                id="unsupported-rating-unit",
            ),
            pytest.param(
                lambda d: d["foundation"]["components"][0]["rating"].__setitem__(
                    "value", -1
                ),
                "value",
                id="negative-rating",
            ),
            pytest.param(
                lambda d: d["foundation"]["components"][0]["rating"].__setitem__(
                    "value", True
                ),
                "value",
                id="boolean-rating",
            ),
            pytest.param(
                lambda d: d["foundation"].__setitem__("components", []),
                "components",
                id="no-components",
            ),
        ],
    )
    def test_invalid_values_are_refused_with_the_offending_field(
        self, mutate: Any, message: str
    ) -> None:
        document = valid_document()
        mutate(document)

        with pytest.raises(SiteTemplateConfigurationInvalid, match=message):
            parse(document)

    def test_duplicate_component_identities_are_refused(self) -> None:
        document = valid_document()
        duplicate = copy.deepcopy(document["foundation"]["components"][0])
        document["foundation"]["components"].append(duplicate)

        with pytest.raises(SiteTemplateConfigurationInvalid, match="Duplicate"):
            parse(document)

    def test_a_non_mapping_document_is_refused(self) -> None:
        with pytest.raises(SiteTemplateConfigurationInvalid, match="mapping"):
            parse(["template_id"])


class TestPathologicalDocuments:
    def test_an_oversized_document_is_refused(self) -> None:
        document = valid_document()
        document["foundation"]["summary"] = "x" * (MAX_DOCUMENT_TEXT_LENGTH + 1)

        with pytest.raises(SiteTemplateConfigurationInvalid, match="more than"):
            parse(document)

    def test_an_over_cardinality_document_is_refused(self) -> None:
        document = valid_document()
        component = document["foundation"]["components"][0]
        document["foundation"]["components"] = [
            {**copy.deepcopy(component), "component_id": f"component-{index}"}
            for index in range(MAX_COMPONENTS + 1)
        ]

        with pytest.raises(SiteTemplateConfigurationInvalid, match="above the limit"):
            parse(document)

    def test_a_deeply_nested_document_is_refused(self) -> None:
        nested: Any = "leaf"
        for _ in range(20):
            nested = {"nested": nested}

        document = valid_document()
        document["foundation"]["components"][0]["rating"] = nested

        with pytest.raises(SiteTemplateConfigurationInvalid, match="nested deeper"):
            parse(document)
