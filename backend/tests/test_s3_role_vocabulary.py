"""S3-01 phase 1: `minigrid-roles-2` and the generator demo-property publication.

`D-2026-10-11-s3-dispatch-interval-assessment`; Architect batch 5 "S3-01
Planner questions". roles-1 stays readable for every set recorded under it.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from test_s1_bindings import CONVERTED_AT, converted
from test_s1_cutover import Clock

from assetops_backend.sites.binding_roles import (
    MINIGRID_ROLES,
    ROLE_SET_BY_SITE_TYPE,
    roles_for,
    serves,
)
from assetops_backend.sites.binding_service import BindingRefused, BindingRequest, BindingService
from assetops_backend.sites.foundation_service import FoundationRefused, FoundationService

CONFIG_FROM = datetime(2026, 10, 1, 0, 0, 0, tzinfo=timezone.utc)
GENERATOR_DEMO = (
    {"property_key": "generator-rated-power", "value": 40, "unit": "kW", "source": "TEMPLATE", "source_version": 2},
    {"property_key": "start-soc-threshold", "value": 35, "unit": "%", "source": "TEMPLATE", "source_version": 2},
    {"property_key": "stop-soc-threshold", "value": 90, "unit": "%", "source": "TEMPLATE", "source_version": 2},
    {"property_key": "start-delay", "value": 5, "unit": "min", "source": "TEMPLATE", "source_version": 2},
)


class TestVocabulary:
    def test_roles_2_adds_exactly_the_two_optional_capability_channels(self) -> None:
        one, two = roles_for("minigrid-roles-1"), roles_for("minigrid-roles-2")
        assert set(two) - set(one) == {"pv_available_power", "pcs_discharge_capability"}
        assert {k: two[k] for k in one} == one
        pv, pcs = two["pv_available_power"], two["pcs_discharge_capability"]
        assert (pv.asset_type, pv.canonical_unit, pv.cardinality, pv.required) == ("INVERTER", "kW", "ONE", False)
        assert (pcs.asset_type, pcs.canonical_unit, pcs.cardinality, pcs.required) == (
            "POWER_CONVERSION_SYSTEM", "kW", "ONE", False,
        )
        # roles-1 is unchanged: observed power is not a capability.
        assert tuple(roles_for("minigrid-roles-1").values()) == MINIGRID_ROLES

    def test_minigrid_publishes_roles_2_and_still_serves_roles_1(self) -> None:
        assert ROLE_SET_BY_SITE_TYPE["MINIGRID"] == "minigrid-roles-2"
        assert serves("MINIGRID", "minigrid-roles-1") and serves("MINIGRID", "minigrid-roles-2")
        assert not serves("MINIGRID", "minigrid-roles-3")


class TestPublication:
    def test_replayed_conversion_keeps_roles_1(self) -> None:
        store, result, _ = converted()
        (only,) = store.binding_sets(result.tenant.id, result.site.id)
        assert only.role_set == "minigrid-roles-1"

    def test_a_later_publication_records_roles_2_and_keeps_the_earlier_roles_1_segment(self) -> None:
        store, result, _ = converted()
        (old,) = store.binding_sets(result.tenant.id, result.site.id)
        requests = [
            BindingRequest(
                device_id=b.device_id, signal_id=b.signal_id, asset_id=str(b.asset_id) if b.asset_id else None,
                role=b.role, source_unit=b.source_unit, canonical_unit=b.canonical_unit, conversion=b.conversion,
            )
            for b in old.bindings
        ]
        service = BindingService(store, Clock(CONVERTED_AT.replace(minute=59)))
        with pytest.raises(BindingRefused) as refused:
            service.publish(result.tenant, result.site, requests=requests, effective_from=CONFIG_FROM,
                            note="x", role_set="minigrid-roles-9")
        assert refused.value.code == "BINDING_ROLE_SET_UNKNOWN"
        service.publish(result.tenant, result.site, requests=requests, effective_from=CONFIG_FROM, note="roles-2")
        current = sorted(
            (s for s in store.binding_sets(result.tenant.id, result.site.id) if s.superseded_at is None),
            key=lambda s: s.valid_from,
        )
        assert [(s.role_set, s.origin) for s in current] == [
            ("minigrid-roles-1", "SPLIT"), ("minigrid-roles-2", "PUBLISH"),
        ]


class TestGeneratorDemoProperties:
    def test_later_effective_revision_carries_template_provenance_and_splits_history(self) -> None:
        store, result, _ = converted()
        service = FoundationService(store, "demo", Clock(CONVERTED_AT.replace(minute=59)))
        published = service.publish_component_properties(
            result.tenant, result.site, asset_code="generator", properties=GENERATOR_DEMO,
            effective_from=CONFIG_FROM, note="Simulated demo configuration",
        )
        generator = next(c for c in published.changed.content["components"] if c["component_id"] == "generator")
        keys = {p["property_key"]: p for p in generator["properties"]}
        assert keys["start-delay"] == GENERATOR_DEMO[3]
        assert keys["minimum-runtime"]["value"] == 30.0  # imported value untouched
        assert published.changed.valid_from == CONFIG_FROM
        earlier = [r for r in store.revisions(result.tenant.id, result.site.id)
                   if r.superseded_at is None and r.valid_from < CONFIG_FROM]
        assert earlier and all(
            "start-delay" not in {p["property_key"] for c in r.content["components"] for p in c.get("properties") or ()}
            for r in earlier
        )
        with pytest.raises(FoundationRefused) as again:
            service.publish_component_properties(
                result.tenant, result.site, asset_code="generator", properties=GENERATOR_DEMO,
                effective_from=CONFIG_FROM, note="again",
            )
        assert again.value.code == "FOUNDATION_NO_CHANGE"

    def test_an_unknown_property_is_refused_by_the_strict_parser(self) -> None:
        store, result, _ = converted()
        service = FoundationService(store, "demo", Clock(CONVERTED_AT.replace(minute=59)))
        with pytest.raises(FoundationRefused) as refused:
            service.publish_component_properties(
                result.tenant, result.site, asset_code="generator",
                properties=({"property_key": "made-up", "value": 1, "unit": "kW", "source": "TEMPLATE",
                             "source_version": 2},),
                effective_from=CONFIG_FROM, note="x",
            )
        assert refused.value.code == "FOUNDATION_VALUE_INVALID"
