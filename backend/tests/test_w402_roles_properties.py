"""W4-02 unit 1: `minigrid-roles-4` and the three typed mini-grid depth Foundation properties.

`D-2026-10-20-w4-02-buildspec` closure 1 Q1/Q9, closure 4 B2/N2/S5. Pure: no database.
"""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from assetops_backend.analytics import assessment_worker
from assetops_backend.sites.binding_roles import (
    BUS_STATES,
    COLD_ROLES_1,
    MINIGRID_ROLES_3,
    MINIGRID_ROLES_4,
    ROLE_SET_MINIGRID,
    ROLE_SET_MINIGRID_3,
    ROLE_SET_MINIGRID_4,
    ROLES_BY_SET,
    SERVED_ROLE_SETS_BY_SITE_TYPE,
    VERIFICATION_ROLE_SETS,
)
from assetops_backend.sites.models import COMPONENT_PROPERTY_DEFINITIONS, MINIGRID_PROPERTY_CARRIERS
from assetops_backend.sites.ports import SiteConfigurationInvalid
from assetops_backend.sites.site_parsing import parse_site_document

KOBO = yaml.safe_load((Path(__file__).resolve().parent / "fixtures" / "s1" / "kobo-001.yaml").read_text(
    encoding="utf-8"))
NEW_ROLES = {
    # role: (asset_type, canonical_unit, value_kind, cardinality, states, event_kinds)
    "storage_charge_requested_power": ("BATTERY", "kW", "NUMBER", "ONE", (), ()),
    "feeder_requested_power": ("LOAD", "kW", "NUMBER", "PER_ASSET", (), ()),
    "site_supply_state": ("AC_BUS", "state", "STATE", "ONE", ("ENERGIZED", "LOST", "UNKNOWN"), ()),
    "mini_backup_start_event": ("GENERATOR", "event", "EVENT", "ONE", (), ("START_REQUEST", "START_RESULT")),
    "mini_backup_bus_state": ("AC_BUS", "state", "STATE", "ONE", ("ENERGIZED", "DEENERGIZED", "UNKNOWN"), ()),
}


class TestRoles4:
    def test_roles_4_extends_roles_3_with_exactly_five_optional_roles(self) -> None:
        assert MINIGRID_ROLES_4[: len(MINIGRID_ROLES_3)] == MINIGRID_ROLES_3
        added = MINIGRID_ROLES_4[len(MINIGRID_ROLES_3):]
        assert [r.role for r in added] == list(NEW_ROLES)
        for role in added:
            assert (role.asset_type, role.canonical_unit, role.value_kind, role.cardinality, role.states,
                    role.event_kinds) == NEW_ROLES[role.role]
            assert role.required is False and role.covered_by == "CHANNEL" and role.critical_load is False
        channels = {r.role for r in MINIGRID_ROLES_4 if r.covered_by == "CHANNEL"}
        assert len(channels) == 17 and {r.role for r in MINIGRID_ROLES_4} - channels == {"battery_reserve"}

    def test_registration_is_opt_in_and_served(self) -> None:
        assert ROLES_BY_SET[ROLE_SET_MINIGRID_4] == MINIGRID_ROLES_4
        assert ROLE_SET_MINIGRID_4 in SERVED_ROLE_SETS_BY_SITE_TYPE["MINIGRID"]
        assert ROLE_SET_MINIGRID_4 not in SERVED_ROLE_SETS_BY_SITE_TYPE["COLDCHAIN"]
        assert ROLE_SET_MINIGRID != ROLE_SET_MINIGRID_4  # a new publication still defaults to roles-2
        assert VERIFICATION_ROLE_SETS == frozenset({ROLE_SET_MINIGRID_3, ROLE_SET_MINIGRID_4})

    def test_dispatch_reads_roles_4_with_its_six_unchanged_inputs(self) -> None:
        assert set(assessment_worker.ROLES_BY_SET) >= {ROLE_SET_MINIGRID_3, ROLE_SET_MINIGRID_4}
        assert assessment_worker.DOMAIN == "dispatch"
        names4 = set(assessment_worker.ROLES_BY_SET[ROLE_SET_MINIGRID_4])
        names3 = set(assessment_worker.ROLES_BY_SET[ROLE_SET_MINIGRID_3])
        assert set(assessment_worker.DISPATCH_ROLES) <= names3 <= names4

    def test_cold_vocabulary_is_unchanged(self) -> None:
        cold = {r.role: r for r in COLD_ROLES_1}
        assert cold["backup_start_event"].event_kinds == ("START_REQUEST", "START_RESULT")
        assert cold["backup_bus_state"].states == BUS_STATES == ("POWERED", "UNPOWERED")
        assert not {"mini_backup_start_event", "mini_backup_bus_state", "site_supply_state"} & set(cold)


def _with(component_id: str, key: str, value: float) -> dict:
    doc = copy.deepcopy(KOBO)
    for component in doc["foundation"]["components"]:
        if component["component_id"] == component_id:
            component["properties"] = list(component.get("properties") or []) + [{
                "property_key": key, "value": value, "unit": COMPONENT_PROPERTY_DEFINITIONS[key].unit,
                "source": "TEMPLATE", "source_version": 1}]
    return doc


def _parse(doc: dict):
    return parse_site_document(doc, source="test document")


class TestTypedProperties:
    def test_definitions_and_carriers(self) -> None:
        got = {k: (COMPONENT_PROPERTY_DEFINITIONS[k].unit, COMPONENT_PROPERTY_DEFINITIONS[k].kind)
               for k in MINIGRID_PROPERTY_CARRIERS}
        assert got == {"pv-available-uncertainty": ("kW", "PHYSICAL"),
                       "renewable-retained-margin": ("kW", "CONTROL"),
                       "backup-recovery-target": ("min", "CONTROL")}
        assert MINIGRID_PROPERTY_CARRIERS == {"pv-available-uncertainty": "INVERTER",
                                              "renewable-retained-margin": "AC_BUS",
                                              "backup-recovery-target": "AC_BUS"}

    @pytest.mark.parametrize(("component", "key", "value"), [
        ("pv-inverter", "pv-available-uncertainty", 0.0),
        ("pv-inverter", "pv-available-uncertainty", 2.5),
        ("ac-bus", "renewable-retained-margin", 0.0),
        ("ac-bus", "backup-recovery-target", 5.0),
    ])
    def test_accepted_on_the_carrier(self, component, key, value) -> None:
        site = _parse(_with(component, key, value))
        props = {p.property_key: p.value for c in site.foundation.components for p in (c.properties or ())}
        assert props[key] == value

    @pytest.mark.parametrize(("component", "key"), [
        ("ac-bus", "pv-available-uncertainty"),
        ("pv-inverter", "renewable-retained-margin"),
        ("battery", "backup-recovery-target"),
    ])
    def test_wrong_carrier_is_refused(self, component, key) -> None:
        with pytest.raises(SiteConfigurationInvalid, match=f"{key} belongs on a"):
            _parse(_with(component, key, 1.0))

    @pytest.mark.parametrize(("component", "key", "value", "match"), [
        ("ac-bus", "backup-recovery-target", 0.0, "must be greater than zero"),
        ("pv-inverter", "pv-available-uncertainty", -1.0, "is a magnitude"),
        ("ac-bus", "renewable-retained-margin", -0.5, "is a magnitude"),
    ])
    def test_sign_is_refused(self, component, key, value, match) -> None:
        with pytest.raises(SiteConfigurationInvalid, match=match):
            _parse(_with(component, key, value))

    def test_wrong_unit_is_refused(self) -> None:
        doc = _with("ac-bus", "backup-recovery-target", 5.0)
        for component in doc["foundation"]["components"]:
            for prop in component.get("properties") or ():
                if prop["property_key"] == "backup-recovery-target":
                    prop["unit"] = "s"
        with pytest.raises(SiteConfigurationInvalid):
            _parse(doc)
