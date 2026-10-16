"""S3-01 phase 1: `minigrid-roles-2` and the generator demo-property publication.

`D-2026-10-11-s3-dispatch-interval-assessment`; Architect batch 5 "S3-01
Planner questions". roles-1 stays readable for every set recorded under it.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from test_s1_bindings import CONVERTED_AT, converted
from test_s1_cutover import Clock

from assetops_backend.sites.binding_roles import (
    MINIGRID_ROLES,
    ROLE_SET_BY_SITE_TYPE,
    VERIFICATION_MESSAGES,
    VERIFICATION_POINT_ROLES,
    VERIFICATION_POWER_ROLES,
    VERIFICATION_READINESS_VERSION,
    roles_for,
    serves,
)
from assetops_backend.sites.binding_service import BindingRefused, BindingRequest, BindingService, readiness
from assetops_backend.sites.demo_configuration import DemoConfigurationConflict, apply_demo_configuration
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
        # S6-02a: roles-3 is served (opt-in by explicit role_set); new publications stay roles-2.
        assert serves("MINIGRID", "minigrid-roles-3")
        assert not serves("MINIGRID", "minigrid-roles-4")


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


# --- S6-02a: minigrid-roles-3 and verification readiness -----------------------------------------

CONVERSIONS = Path(__file__).resolve().parents[1] / "conversions"
S3_DEMO = json.loads((CONVERSIONS / "kobo-001-s3-dispatch-demo-config.json").read_text(encoding="utf-8"))
VERIFICATION = json.loads((CONVERSIONS / "kobo-001-s6-verification-demo-config.json").read_text(encoding="utf-8"))
CRITICAL = {"critical_load_requested_power", "critical_load_delivered_power"}


def _apply(store, result, fixture):
    clock = Clock(CONVERTED_AT + timedelta(minutes=10))
    return apply_demo_configuration(store, FoundationService(store, "demo", clock), BindingService(store, clock),
                                    result.tenant, result.site, fixture)


def _readiness_at(store, result, at):
    view = FoundationService(store, "demo", Clock(CONVERTED_AT + timedelta(hours=1))).read(
        result.site, result.tenant, at, None)
    return readiness(view.site, view.revision, view.registrations, view.binding_set)


class TestRoles3:
    def test_roles_3_adds_exactly_the_two_optional_critical_load_power_roles(self) -> None:
        two, three = roles_for("minigrid-roles-2"), roles_for("minigrid-roles-3")
        assert set(three) - set(two) == CRITICAL
        assert {k: three[k] for k in two} == two
        for name in CRITICAL:
            role = three[name]
            assert (role.asset_type, role.canonical_unit, role.value_kind, role.cardinality, role.required) == (
                "LOAD", "kW", "NUMBER", "ONE", False)
            assert role.critical_load
        assert three["critical_load_requested_power"].label == "Critical load requested power"
        assert three["critical_load_delivered_power"].label == "Critical load delivered power"
        assert ROLE_SET_BY_SITE_TYPE["MINIGRID"] == "minigrid-roles-2"
        assert set(VERIFICATION_POWER_ROLES) | set(VERIFICATION_POINT_ROLES) <= set(three)
        assert set(VERIFICATION_MESSAGES) == set(VERIFICATION_POWER_ROLES) | set(VERIFICATION_POINT_ROLES)
        assert all(lab and site for lab, site in VERIFICATION_MESSAGES.values())

    def test_verification_fixture_publishes_roles_3_and_keeps_roles_2_and_1_segments(self) -> None:
        store, result, _ = converted()
        _apply(store, result, S3_DEMO)
        applied = _apply(store, result, VERIFICATION)
        assert applied.bindings_published and applied.periods[-1]["role_set"] == "minigrid-roles-3"
        assert set(applied.capability_channels) >= {
            "clinic-meter/requested-power->critical_load_requested_power",
            "clinic-meter/delivered-power->critical_load_delivered_power",
        }
        current = sorted((s for s in store.binding_sets(result.tenant.id, result.site.id) if s.superseded_at is None),
                         key=lambda s: s.valid_from)
        assert list(dict.fromkeys(s.role_set for s in current)) == ["minigrid-roles-1", "minigrid-roles-2", "minigrid-roles-3"]
        again = _apply(store, result, VERIFICATION)
        assert not again.bindings_published and not again.properties_published

    def test_a_critical_load_role_naming_another_load_is_refused(self) -> None:
        store, result, _ = converted()
        _apply(store, result, S3_DEMO)
        wrong = json.loads(json.dumps(VERIFICATION))
        for item in wrong["bindings"]["add"]:
            if item["role"] in CRITICAL:
                item["asset_code"] = "load-mill"
        with pytest.raises(DemoConfigurationConflict) as refused:
            _apply(store, result, wrong)
        assert "BINDING_CRITICAL_LOAD_MISMATCH" in str(refused.value)

    def test_readiness_adds_verification_readiness_only_for_roles_3(self) -> None:
        store, result, _ = converted()
        _apply(store, result, S3_DEMO)
        roles_2 = _readiness_at(store, result, datetime(2026, 10, 3, tzinfo=timezone.utc))
        assert roles_2["role_set"] == "minigrid-roles-2" and "verification_readiness" not in roles_2
        roles_1 = _readiness_at(store, result, datetime(2026, 10, 1, 12, tzinfo=timezone.utc))
        assert roles_1["role_set"] == "minigrid-roles-1" and "verification_readiness" not in roles_1
        _apply(store, result, VERIFICATION)
        later = _readiness_at(store, result, datetime(2026, 10, 3, tzinfo=timezone.utc))
        assert set(later) == set(roles_2) and later["role_set"] == "minigrid-roles-2"
        assert [r["role"] for r in later["roles"]] == [r["role"] for r in roles_2["roles"]]
        ready = _readiness_at(store, result, datetime(2026, 10, 13, tzinfo=timezone.utc))
        assert ready["role_set"] == "minigrid-roles-3"
        assert ready["verification_readiness"] == {
            "version": VERIFICATION_READINESS_VERSION, "ready": True, "missing": []}

    def test_readiness_names_each_unbound_verification_role_with_lab_and_site_messages(self) -> None:
        store, result, _ = converted()
        (old,) = store.binding_sets(result.tenant.id, result.site.id)
        requests = [
            BindingRequest(
                device_id=b.device_id, signal_id=b.signal_id, asset_id=str(b.asset_id) if b.asset_id else None,
                role=b.role, source_unit=b.source_unit, canonical_unit=b.canonical_unit, conversion=b.conversion,
            )
            for b in old.bindings
        ]
        BindingService(store, Clock(CONVERTED_AT.replace(minute=59))).publish(
            result.tenant, result.site, requests=requests, effective_from=CONFIG_FROM, note="roles-3 bare",
            role_set="minigrid-roles-3")
        view = _readiness_at(store, result, datetime(2026, 10, 2, tzinfo=timezone.utc))
        verification = view["verification_readiness"]
        assert verification["version"] == VERIFICATION_READINESS_VERSION and verification["ready"] is False
        missing = {m["role"]: m for m in verification["missing"]}
        assert set(missing) == {"pv_available_power", "pcs_discharge_capability"} | CRITICAL
        entry = missing["critical_load_requested_power"]
        assert entry["label"] == "Critical load requested power"
        assert "five-minute" in entry["lab_message"] and "five-minute" in entry["site_message"]
        assert (entry["lab_message"], entry["site_message"]) == VERIFICATION_MESSAGES["critical_load_requested_power"]
        # Configuration readiness is unchanged by the optional verification roles.
        assert view["missing_roles"] == []
