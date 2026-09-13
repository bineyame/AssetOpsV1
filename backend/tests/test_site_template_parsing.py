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
        },
    }


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

        assert [name for name in public if name.startswith("parse")] == [
            "parse_site_template"
        ]

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
