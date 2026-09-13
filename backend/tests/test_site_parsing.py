"""Strict-parser tests for Site documents.

The parser is the YAML-configuration-authority seam for Sites, and it is the
one that matters most: a Site document may be user-authored, so it is
untrusted input crossing a strict boundary. These tests cover the refusals
that keep a defective or hostile document out of the product, the round trip
that lets a write prove it stored what was validated, and the request parsing
whose messages a user actually reads.
"""

from __future__ import annotations

import copy
from typing import Any

import pytest

from assetops_backend.sites.models import SiteRecord
from assetops_backend.sites.ports import SiteConfigurationInvalid
from assetops_backend.sites.site_parsing import (
    MAX_COMPONENTS,
    SITE_DOCUMENT_LIMITS,
    parse_create_site_request,
    parse_site_document,
    render_site_document,
)


def valid_site_document() -> dict[str, Any]:
    return {
        "site_id": "MG-002",
        "display_name": "Kalangala Mini-Grid",
        "site_type": "MINIGRID",
        "location": {"country": "Uganda", "locality": "Kalangala"},
        "timezone": "Africa/Kampala",
        "lifecycle_status": "PLANNED",
        "origin": "USER",
        "source": {"mode": "SIMULATED"},
        "template": {
            "template_id": "hybrid-mini-grid-100kw",
            "template_version": 1,
        },
        "foundation": {
            "version": 1,
            "valid_from": "2026-01-01T00:00:00Z",
            "summary": "A site used by tests only.",
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


def valid_create_request() -> dict[str, Any]:
    return {
        "template_id": "hybrid-mini-grid-100kw",
        "site_id": "MG-002",
        "display_name": "Kalangala Mini-Grid",
        "location": {"country": "Uganda", "locality": "Kalangala"},
        "timezone": "Africa/Kampala",
    }


def parse(document: Any) -> SiteRecord:
    return parse_site_document(document, source="test-site.yaml")


class TestValidDocument:
    def test_a_valid_document_parses_into_domain_records(self) -> None:
        record = parse(valid_site_document())

        assert record.site_id == "MG-002"
        assert record.display_name == "Kalangala Mini-Grid"
        assert record.site_type == "MINIGRID"
        assert record.location.country == "Uganda"
        assert record.location.locality == "Kalangala"
        assert record.timezone == "Africa/Kampala"
        assert record.lifecycle_status == "PLANNED"
        assert record.origin == "USER"
        assert record.source.mode == "SIMULATED"
        assert record.template is not None
        assert record.template.template_id == "hybrid-mini-grid-100kw"
        assert record.template.template_version == 1
        assert record.foundation.version == 1
        assert [c.component_id for c in record.foundation.components] == [
            "pv-array",
            "site-meter",
        ]
        assert record.foundation.components[1].rating is None

    def test_the_record_carries_no_evidence_or_health_field(self) -> None:
        """A configuration-only Site has no operational state to carry."""
        record = parse(valid_site_document())

        for field in (
            "last_data",
            "source_health",
            "evidence_availability",
            "operational_status",
            "integration_readiness",
        ):
            assert not hasattr(record, field)

    def test_the_record_carries_no_lab_or_simulator_flag(self) -> None:
        """`source.mode` is the simulator tag. There is no second field."""
        record = parse(valid_site_document())

        for field in ("created_in_lab", "is_simulator_site", "lab", "simulator"):
            assert not hasattr(record, field)

    def test_a_site_without_template_provenance_parses(self) -> None:
        """A Site that came from no template claims no template provenance."""
        document = valid_site_document()
        document["origin"] = "SHIPPED"
        document["template"] = None

        assert parse(document).template is None


class TestOriginAndModeAreIndependent:
    @pytest.mark.parametrize(
        ("origin", "mode"),
        [
            ("USER", "SIMULATED"),
            ("USER", "LIVE"),
            ("SHIPPED", "SIMULATED"),
            ("SHIPPED", "LIVE"),
        ],
    )
    def test_every_combination_of_origin_and_mode_parses(
        self, origin: str, mode: str
    ) -> None:
        """Neither is derived from, defaulted from, or constrained by the other.

        In M1 only `USER` plus `SIMULATED` is reachable, because the Lab is
        the only creation path. That is a fact about the milestone, not a rule
        about the fields, so the parser must accept all four.
        """
        document = valid_site_document()
        document["origin"] = origin
        document["source"] = {"mode": mode}

        record = parse(document)

        assert record.origin == origin
        assert record.source.mode == mode

    def test_lifecycle_is_not_constrained_by_mode_either(self) -> None:
        document = valid_site_document()
        document["lifecycle_status"] = "ACTIVE"
        document["source"] = {"mode": "SIMULATED"}

        record = parse(document)

        assert record.lifecycle_status == "ACTIVE"
        assert record.source.mode == "SIMULATED"


class TestStrictness:
    def test_there_is_no_lenient_path(self) -> None:
        import assetops_backend.sites.site_parsing as site_parsing

        public = [name for name in dir(site_parsing) if not name.startswith("_")]

        assert [name for name in public if name.startswith("parse")] == [
            "parse_create_site_request",
            "parse_site_document",
        ]

    @pytest.mark.parametrize(
        "mutate",
        [
            pytest.param(lambda d: d.update(extra="x"), id="unknown-site-key"),
            pytest.param(
                lambda d: d.update(created_in_lab=True), id="banned-lab-flag"
            ),
            pytest.param(
                lambda d: d.update(last_data="2 min ago"), id="banned-evidence-field"
            ),
            pytest.param(
                lambda d: d["location"].update(extra="x"), id="unknown-location-key"
            ),
            pytest.param(
                lambda d: d["source"].update(health="ONLINE"), id="unknown-source-key"
            ),
            pytest.param(
                lambda d: d["template"].update(extra="x"), id="unknown-template-key"
            ),
            pytest.param(
                lambda d: d["foundation"].update(topology=[]),
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
        document = valid_site_document()
        mutate(document)

        with pytest.raises(SiteConfigurationInvalid, match="Unknown"):
            parse(document)

    @pytest.mark.parametrize(
        ("mutate", "message"),
        [
            pytest.param(
                lambda d: d.__setitem__("site_id", "MG/002"), "site_id", id="bad-id"
            ),
            pytest.param(
                lambda d: d.__delitem__("display_name"),
                "display_name",
                id="missing-display-name",
            ),
            pytest.param(
                lambda d: d.__setitem__("site_type", "MICROGRID"),
                "site_type",
                id="unsupported-site-type",
            ),
            pytest.param(
                lambda d: d.__setitem__("lifecycle_status", "RUNNING"),
                "lifecycle_status",
                id="unsupported-lifecycle",
            ),
            pytest.param(
                lambda d: d.__setitem__("origin", "LAB"),
                "origin",
                id="unsupported-origin",
            ),
            pytest.param(
                lambda d: d.__setitem__("source", {"mode": "RECORDED"}),
                "mode",
                id="unsupported-mode",
            ),
            pytest.param(
                lambda d: d.__setitem__("timezone", "Kampala"),
                "timezone",
                id="non-iana-timezone",
            ),
            pytest.param(
                lambda d: d.__delitem__("timezone"),
                "timezone",
                id="missing-timezone",
            ),
            pytest.param(
                lambda d: d.__setitem__("location", {"country": "Uganda"}),
                "locality",
                id="missing-locality",
            ),
            pytest.param(
                lambda d: d["foundation"].__setitem__("version", 0),
                "version",
                id="foundation-version-out-of-range",
            ),
            pytest.param(
                lambda d: d["foundation"].__setitem__("valid_from", "yesterday"),
                "valid_from",
                id="unparseable-validity",
            ),
            pytest.param(
                lambda d: d["foundation"].__setitem__("components", []),
                "components",
                id="no-components",
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
                    "value", True
                ),
                "value",
                id="boolean-rating",
            ),
            pytest.param(
                lambda d: d["template"].__setitem__("template_version", "1"),
                "template_version",
                id="template-version-not-an-integer",
            ),
        ],
    )
    def test_invalid_values_are_refused_with_the_offending_field(
        self, mutate: Any, message: str
    ) -> None:
        document = valid_site_document()
        mutate(document)

        with pytest.raises(SiteConfigurationInvalid, match=message):
            parse(document)

    def test_duplicate_component_identities_are_refused(self) -> None:
        document = valid_site_document()
        document["foundation"]["components"].append(
            copy.deepcopy(document["foundation"]["components"][0])
        )

        with pytest.raises(SiteConfigurationInvalid, match="Duplicate"):
            parse(document)

    def test_a_non_mapping_document_is_refused(self) -> None:
        with pytest.raises(SiteConfigurationInvalid, match="mapping"):
            parse(["site_id"])

    def test_free_text_with_a_control_character_is_refused(self) -> None:
        document = valid_site_document()
        document["display_name"] = "KalangalaMini-Grid"

        with pytest.raises(SiteConfigurationInvalid, match="control character"):
            parse(document)

    def test_markup_in_free_text_is_stored_as_text_rather_than_refused(self) -> None:
        """Free text is text. It is never markup, identity, a path, or a route.

        The product's protection is that it renders as text and is never used
        for lookup, so a display name containing angle brackets is a poor name
        rather than a security boundary this parser has to guess at.
        """
        document = valid_site_document()
        document["display_name"] = "<b>Kalangala</b>"

        record = parse(document)

        assert record.display_name == "<b>Kalangala</b>"
        assert record.site_id == "MG-002"


class TestPathologicalDocuments:
    def test_an_oversized_document_is_refused(self) -> None:
        document = valid_site_document()
        document["foundation"]["summary"] = "x" * (
            SITE_DOCUMENT_LIMITS.max_text_length + 1
        )

        with pytest.raises(SiteConfigurationInvalid, match="more than"):
            parse(document)

    def test_an_over_cardinality_document_is_refused(self) -> None:
        document = valid_site_document()
        component = document["foundation"]["components"][0]
        document["foundation"]["components"] = [
            {**copy.deepcopy(component), "component_id": f"component-{index}"}
            for index in range(MAX_COMPONENTS + 1)
        ]

        with pytest.raises(SiteConfigurationInvalid, match="above the limit"):
            parse(document)

    def test_a_deeply_nested_document_is_refused(self) -> None:
        nested: Any = "leaf"
        for _ in range(20):
            nested = {"nested": nested}

        document = valid_site_document()
        document["foundation"]["components"][0]["rating"] = nested

        with pytest.raises(SiteConfigurationInvalid, match="nested deeper"):
            parse(document)


class TestRoundTrip:
    def test_rendering_a_record_produces_a_document_the_parser_accepts(self) -> None:
        """This is what lets a write prove it stored what was validated."""
        record = parse(valid_site_document())

        rendered = render_site_document(record)

        assert parse_site_document(rendered, source="rendered") == record

    def test_rendering_covers_every_field_the_parser_requires(self) -> None:
        record = parse(valid_site_document())

        assert set(render_site_document(record)) == set(valid_site_document())


class TestCreateRequestParsing:
    def test_a_valid_request_parses_into_identity_level_fields(self) -> None:
        request = parse_create_site_request(valid_create_request())

        assert request.site_id == "MG-002"
        assert request.template_id == "hybrid-mini-grid-100kw"
        assert request.display_name == "Kalangala Mini-Grid"
        assert request.country == "Uganda"
        assert request.locality == "Kalangala"
        assert request.timezone == "Africa/Kampala"

    def test_the_request_cannot_choose_its_own_provenance(self) -> None:
        """Origin, mode, lifecycle, and Foundation are the service's to set."""
        for field, value in (
            ("origin", "SHIPPED"),
            ("source", {"mode": "LIVE"}),
            ("lifecycle_status", "ACTIVE"),
            ("foundation", {}),
            ("template_version", 99),
        ):
            request = valid_create_request()
            request[field] = value

            with pytest.raises(SiteConfigurationInvalid, match="Unknown"):
                parse_create_site_request(request)

        parsed = parse_create_site_request(valid_create_request())
        for field in ("origin", "source", "lifecycle_status", "foundation"):
            assert not hasattr(parsed, field)

    @pytest.mark.parametrize(
        ("mutate", "expected"),
        [
            pytest.param(
                lambda r: r.__setitem__("site_id", "MG 002"),
                "not a valid site ID",
                id="malformed-site-id",
            ),
            pytest.param(
                lambda r: r.__delitem__("display_name"),
                "Display name is required",
                id="missing-display-name",
            ),
            pytest.param(
                lambda r: r["location"].__delitem__("country"),
                "Location country is required",
                id="missing-country",
            ),
            pytest.param(
                lambda r: r.__delitem__("timezone"),
                "Timezone is required",
                id="missing-timezone",
            ),
            pytest.param(
                lambda r: r.__setitem__("template_id", "Hybrid Mini Grid"),
                "template_id",
                id="malformed-template-id",
            ),
        ],
    )
    def test_each_refusal_names_what_is_wrong(
        self, mutate: Any, expected: str
    ) -> None:
        request = valid_create_request()
        mutate(request)

        with pytest.raises(SiteConfigurationInvalid, match=expected):
            parse_create_site_request(request)

    def test_the_four_refusals_the_user_meets_are_distinct(self) -> None:
        """Distinct readable reasons, not one generic failure."""
        messages = []
        for mutate in (
            lambda r: r.__setitem__("site_id", "MG 002"),
            lambda r: r.__delitem__("display_name"),
            lambda r: r.__delitem__("timezone"),
            lambda r: r["location"].__delitem__("locality"),
        ):
            request = valid_create_request()
            mutate(request)
            with pytest.raises(SiteConfigurationInvalid) as refusal:
                parse_create_site_request(request)
            messages.append(str(refusal.value))

        assert len(set(messages)) == len(messages)
        for message in messages:
            assert "Traceback" not in message
            assert len(message) > 20

    def test_a_non_mapping_request_is_refused(self) -> None:
        with pytest.raises(SiteConfigurationInvalid, match="must be an object"):
            parse_create_site_request("MG-002")
