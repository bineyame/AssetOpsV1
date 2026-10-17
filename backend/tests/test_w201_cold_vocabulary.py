"""W2-01 cold vocabulary, cold-roles-1, cold Foundation validator and contact mapping (no database).

`.agent/W2-technical-design-cold.md` section 3 (`D-2026-10-17-w2-01-answers` A-I, W2-02 channel closure).
"""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

from assetops_contracts.source_envelope_v4 import V4_CHANNEL_MAPPINGS
from assetops_backend.sites import models
from assetops_backend.sites.binding_roles import (
    COLD_ROLES_1,
    ROLE_SET_BY_SITE_TYPE,
    ROLE_SET_COLD_1,
    SERVED_ROLE_SETS_BY_SITE_TYPE,
    conversion_problem,
    roles_for,
)
from assetops_backend.sites.cold_foundation import (
    CONTACT_HEALTH_ABSENT,
    CONTACT_NO_DIAGNOSTIC,
    CONTACT_UNVERIFIED,
    ContactFacts,
    contact_document,
)
from assetops_backend.sites.foundation_parsing import UNIT_RANGES
from assetops_backend.sites.ports import SiteConfigurationInvalid
from assetops_backend.sites.site_parsing import parse_site_document

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "w2"
COMPLETE = yaml.safe_load((FIXTURES / "cold-001.yaml").read_text(encoding="utf-8"))
MISSING_PROBE = yaml.safe_load((FIXTURES / "cold-002.yaml").read_text(encoding="utf-8"))
I = {"kind": "IDENTITY", "parameters": {}}


def parse(document):
    return parse_site_document(document, source="test document")


def doc():
    return copy.deepcopy(COMPLETE)


def component(document, component_id):
    return next(c for c in document["foundation"]["components"] if c["component_id"] == component_id)


def set_property(document, component_id, key, value, unit=None):
    for item in component(document, component_id)["properties"]:
        if item["property_key"] == key:
            item["value"] = value
            if unit is not None:
                item["unit"] = unit
            return
    raise AssertionError(key)


def connections(document):
    return document["foundation"]["topology"]["connections"]


def edge(cid, a, b, medium):
    return {"connection_id": cid, "from_node": a, "to_node": b, "medium": medium}


class TestVocabulary:
    def test_closed_vocabularies_carry_the_cold_members(self) -> None:
        assert {"COLD_ROOM", "TEMPERATURE_PROBE", "COMPRESSOR", "TRANSFER_SWITCH"} <= models.COMPONENT_TYPES
        assert {"COLD_ROOM", "SENSOR", "COOLING", "SWITCH"} <= models.TOPOLOGY_NODE_ROLES
        assert models.CONNECTION_MEDIA == {"AC", "DC", "FUEL", "SIGNAL", "THERMAL"}
        assert "event" in models.SIGNAL_UNITS and "degC" in models.RATING_UNITS
        assert "COLDCHAIN" in models.SITE_TYPES

    def test_thirteen_cold_properties_with_exact_unit_kind_and_carrier(self) -> None:
        expected = {
            "cold-thermal-capacity": ("COLD_ROOM", "PHYSICAL", "kWh/degC"),
            "cold-heat-leak": ("COLD_ROOM", "PHYSICAL", "kW/degC"),
            "cold-cooling-capacity": ("COMPRESSOR", "PHYSICAL", "kW"),
            "cold-door-heat": ("COLD_ROOM", "PHYSICAL", "kWh/min"),
            "cold-control-low": ("COLD_ROOM", "CONTROL", "degC"),
            "cold-control-high": ("COLD_ROOM", "CONTROL", "degC"),
            "cold-policy-low": ("COLD_ROOM", "CONTROL", "degC"),
            "cold-policy-high": ("COLD_ROOM", "CONTROL", "degC"),
            "cold-min-excursion": ("COLD_ROOM", "CONTROL", "min"),
            "cold-return-hysteresis": ("COLD_ROOM", "CONTROL", "degC"),
            "cold-start-timeout": ("GENERATOR", "CONTROL", "min"),
            "cold-probe-error": ("TEMPERATURE_PROBE", "PHYSICAL", "degC"),
            "cold-compressor-start-delay": ("COMPRESSOR", "PHYSICAL", "min"),
        }
        actual = {
            key: (models.COLD_PROPERTY_CARRIERS[key], d.kind, d.unit)
            for key, d in models.COMPONENT_PROPERTY_DEFINITIONS.items() if key.startswith("cold-")
        }
        assert actual == expected
        assert {u: UNIT_RANGES[u] for u in ("kWh/degC", "kW/degC", "kWh/min", "degC", "kW", "min")} == {
            "kWh/degC": (0, 10000), "kW/degC": (0, 1000), "kWh/min": (0, 1000), "degC": (-40, 60),
            "kW": (0, 100000), "min": (0, 100000)}


class TestColdRoles:
    def test_cold_roles_1_is_registered_and_names_the_closed_role_list(self) -> None:
        assert ROLE_SET_BY_SITE_TYPE["COLDCHAIN"] == ROLE_SET_COLD_1 == "cold-roles-1"
        assert SERVED_ROLE_SETS_BY_SITE_TYPE["COLDCHAIN"] == {ROLE_SET_COLD_1}
        assert ROLE_SET_BY_SITE_TYPE["MINIGRID"] == "minigrid-roles-2"
        assert [(r.role, r.asset_type, r.canonical_unit, r.value_kind, r.cardinality, r.required, r.covered_by)
                for r in COLD_ROLES_1] == [
            ("chamber_temperature", "TEMPERATURE_PROBE", "degC", "NUMBER", "PER_ASSET", True, "CHANNEL"),
            ("cold_policy_low", "COLD_ROOM", "degC", "NUMBER", "PER_ASSET", True, "FOUNDATION_CONTROL"),
            ("cold_policy_high", "COLD_ROOM", "degC", "NUMBER", "PER_ASSET", True, "FOUNDATION_CONTROL"),
            ("compressor_state", "COMPRESSOR", "state", "STATE", "PER_ASSET", True, "CHANNEL"),
            ("compressor_power", "COMPRESSOR", "kW", "NUMBER", "PER_ASSET", False, "CHANNEL"),
            ("grid_state", "METER", "state", "STATE", "ONE", True, "CHANNEL"),
            ("backup_start_event", "GENERATOR", "event", "EVENT", "ONE", True, "CHANNEL"),
            ("generator_state", "GENERATOR", "state", "STATE", "ONE", True, "CHANNEL"),
            ("backup_bus_state", "AC_BUS", "state", "STATE", "ONE", True, "CHANNEL"),
            ("grid_power_event", "METER", "event", "EVENT", "ONE", True, "CHANNEL"),
            ("transfer_result", "TRANSFER_SWITCH", "event", "EVENT", "ONE", False, "CHANNEL"),
            ("door_event", "COLD_ROOM", "event", "EVENT", "PER_ASSET", False, "CHANNEL"),
            ("ambient_temperature", "TEMPERATURE_PROBE", "degC", "NUMBER", "PER_ASSET", False, "CHANNEL"),
            ("manual_temperature", "COLD_ROOM", "degC", "EVENT", "PER_ASSET", False, "CHANNEL"),
        ]
        assert "backup_request" not in roles_for(ROLE_SET_COLD_1) and "backup_result" not in roles_for(ROLE_SET_COLD_1)
        assert roles_for(ROLE_SET_COLD_1)["backup_start_event"].event_kinds == ("START_REQUEST", "START_RESULT")

    def test_the_closed_v4_table_names_exactly_the_cold_channel_roles(self) -> None:
        named = {entry.role for entry in V4_CHANNEL_MAPPINGS.values() if entry.role is not None}
        channel_roles = {r.role for r in COLD_ROLES_1 if r.covered_by == "CHANNEL"}
        assert named == channel_roles
        roles = roles_for(ROLE_SET_COLD_1)
        for entry in V4_CHANNEL_MAPPINGS.values():
            if entry.role is not None and entry.family == "EVENT":
                assert set(entry.allowed_record_kinds) == set(roles[entry.role].event_kinds)

    def test_event_identity_triple_is_valid_only_for_events(self) -> None:
        roles = roles_for(ROLE_SET_COLD_1)
        assert conversion_problem(roles["backup_start_event"], "event", I) is None
        assert conversion_problem(roles["manual_temperature"], "degC", I) is None
        assert "not an event channel" in conversion_problem(roles["chamber_temperature"], "event", I)
        assert conversion_problem(roles["grid_power_event"], "degC", I) is not None
        enum = {"kind": "ENUM", "parameters": {"map": {"x": "LOST"}}}
        assert "an event" in conversion_problem(roles["grid_power_event"], "event", enum)

    def test_state_enums_are_role_specific(self) -> None:
        roles = roles_for(ROLE_SET_COLD_1)

        def enum(*members):
            return {"kind": "ENUM", "parameters": {"map": {m.lower(): m for m in members}}}

        assert conversion_problem(roles["compressor_state"], "state", enum("OFF", "RUNNING")) is None
        assert "OFF, STARTING" in conversion_problem(roles["compressor_state"], "state", enum("STOPPED"))
        assert conversion_problem(roles["grid_state"], "state", enum("AVAILABLE", "LOST")) is None
        assert conversion_problem(roles["grid_state"], "state", enum("RUNNING")) is not None
        assert conversion_problem(roles["backup_bus_state"], "state", enum("POWERED", "UNPOWERED")) is None
        assert conversion_problem(roles["generator_state"], "state", enum("OFF")) is not None
        # MINIGRID generator state keeps the generator members.
        mg = roles_for("minigrid-roles-2")["generator_state"]
        assert conversion_problem(mg, "state", enum("STOPPED", "RUNNING")) is None


class TestColdFoundationValidator:
    def test_both_fixtures_parse(self) -> None:
        assert parse(doc()).site_type == "COLDCHAIN"
        assert parse(copy.deepcopy(MISSING_PROBE)).site_type == "COLDCHAIN"

    def test_signed_temperatures_are_valid(self) -> None:
        d = doc()
        set_property(d, "cold-room", "cold-policy-low", -25.0)
        set_property(d, "cold-room", "cold-policy-high", -15.0)
        set_property(d, "cold-room", "cold-control-low", -22.0)
        set_property(d, "cold-room", "cold-control-high", -18.0)
        parse(d)

    @pytest.mark.parametrize("band", ["policy", "control"])
    def test_low_not_below_high_is_refused(self, band) -> None:
        d = doc()
        set_property(d, "cold-room", f"cold-{band}-low", 8.0)
        set_property(d, "cold-room", f"cold-{band}-high", 8.0)
        with pytest.raises(SiteConfigurationInvalid, match="must be below its high"):
            parse(d)

    def test_wrong_unit_is_refused(self) -> None:
        d = doc()
        set_property(d, "cold-room", "cold-policy-low", 2.0, unit="kW")
        with pytest.raises(SiteConfigurationInvalid, match="must be 'degC'"):
            parse(d)

    def test_out_of_range_temperature_is_refused(self) -> None:
        d = doc()
        set_property(d, "cold-room", "cold-policy-low", -41.0)
        with pytest.raises(SiteConfigurationInvalid, match="between -40 and 60"):
            parse(d)

    def test_property_on_the_wrong_carrier_is_refused(self) -> None:
        d = doc()
        component(d, "compressor")["properties"].append(
            {"property_key": "cold-probe-error", "value": 0.2, "unit": "degC", "source": "SITE", "source_version": 1})
        with pytest.raises(SiteConfigurationInvalid, match="belongs on a TEMPERATURE_PROBE"):
            parse(d)

    @pytest.mark.parametrize("key", ["cold-thermal-capacity", "cold-heat-leak", "cold-min-excursion"])
    def test_zero_thermal_fact_is_refused(self, key) -> None:
        d = doc()
        set_property(d, "cold-room", key, 0.0)
        with pytest.raises(SiteConfigurationInvalid, match="greater than zero"):
            parse(d)

    def test_hysteresis_must_be_inside_the_control_band(self) -> None:
        d = doc()
        set_property(d, "cold-room", "cold-return-hysteresis", 3.0)  # band 3..6 is 3 wide
        with pytest.raises(SiteConfigurationInvalid, match="smaller than its control band width"):
            parse(d)

    def test_duplicate_probe_room_link_is_refused(self) -> None:
        d = doc()
        connections(d).append(edge("room-to-ambient", "cold-room", "ambient-probe", "SIGNAL"))
        with pytest.raises(SiteConfigurationInvalid, match="already has a primary chamber probe"):
            parse(d)

    def test_one_probe_primary_for_two_rooms_is_refused(self) -> None:
        d = doc()
        room2 = copy.deepcopy(component(d, "cold-room"))
        room2.update(component_id="cold-room-2", display_name="Second room")
        d["foundation"]["components"].append(room2)
        d["foundation"]["topology"]["nodes"].append(
            {"node_id": "cold-room-2", "component_id": "cold-room-2", "node_role": "COLD_ROOM"})
        connections(d).append(edge("room2-to-chamber-probe", "cold-room-2", "chamber-probe", "SIGNAL"))
        with pytest.raises(SiteConfigurationInvalid, match="already the primary probe of room"):
            parse(d)

    def test_duplicate_edge_is_refused(self) -> None:
        d = doc()
        connections(d).append(edge("bus-to-compressor-again", "backup-bus", "compressor", "AC"))
        with pytest.raises(SiteConfigurationInvalid, match="duplicates backup-bus -> compressor"):
            parse(d)

    def test_a_back_edge_that_would_close_a_cycle_is_refused(self) -> None:
        # transfer -> bus exists; bus -> transfer would close a directed cycle. The section 3 edge-type
        # table admits no type cycle, so it is refused there first; `_find_cycle` is the second guard.
        d = doc()
        connections(d).append(edge("bus-to-transfer", "backup-bus", "transfer-switch", "AC"))
        with pytest.raises(SiteConfigurationInvalid, match="does not declare"):
            parse(d)

    def test_cycle_guard_refuses_when_the_type_table_would_admit_one(self, monkeypatch) -> None:
        from assetops_backend.sites import cold_foundation

        widened = dict(cold_foundation.COLD_EDGE_TYPES)
        widened["AC"] = widened["AC"] | {("AC_BUS", "TRANSFER_SWITCH")}
        monkeypatch.setattr(cold_foundation, "COLD_EDGE_TYPES", widened)
        d = doc()
        connections(d).append(edge("bus-to-transfer", "backup-bus", "transfer-switch", "AC"))
        with pytest.raises(SiteConfigurationInvalid, match="directed cycle"):
            parse(d)

    def test_cycle_detector_finds_a_type_valid_cycle(self) -> None:
        from assetops_backend.sites.cold_foundation import _find_cycle

        assert _find_cycle({"a": ["b"], "b": ["c"], "c": ["a"]}) == ["a", "b", "c", "a"]
        assert _find_cycle({"a": ["b"], "b": ["c"]}) is None

    def test_medium_endpoint_types_are_checked(self) -> None:
        d = doc()
        connections(d).append(edge("compressor-to-probe", "compressor", "ambient-probe", "SIGNAL"))
        with pytest.raises(SiteConfigurationInvalid, match="COMPRESSOR to TEMPERATURE_PROBE over SIGNAL"):
            parse(d)

    def test_node_role_must_match_component_type(self) -> None:
        d = doc()
        node = next(n for n in d["foundation"]["topology"]["nodes"] if n["node_id"] == "compressor")
        node["node_role"] = "LOAD"
        with pytest.raises(SiteConfigurationInvalid, match="must have node role COOLING"):
            parse(d)

    def test_undeclared_transfer_switch_is_refused(self) -> None:
        d = doc()
        d["foundation"]["components"] = [c for c in d["foundation"]["components"]
                                         if c["component_id"] != "transfer-switch"]
        d["foundation"]["devices"] = [x for x in d["foundation"]["devices"] if x["component_id"] != "transfer-switch"]
        with pytest.raises(SiteConfigurationInvalid, match="transfer-switch"):
            parse(d)

    def test_minigrid_sites_are_untouched_by_cold_rules(self) -> None:
        kobo = yaml.safe_load((FIXTURES.parent / "s1" / "kobo-001.yaml").read_text(encoding="utf-8"))
        assert parse(kobo).site_type == "MINIGRID"


class TestContact:
    NOW = datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc)

    def test_mapping_follows_the_section_3_rule(self) -> None:
        assert contact_document(ContactFacts(None, "UNKNOWN")) == {"state": "NEVER", "as_of": None, "limitations": []}
        recent = contact_document(ContactFacts(self.NOW, "CURRENT"))
        assert recent == {"state": "RECENT", "as_of": "2026-10-17T12:00:00Z", "limitations": []}
        assert contact_document(ContactFacts(self.NOW, "STALE"))["state"] == "STALE"
        unknown = contact_document(ContactFacts(self.NOW, "UNKNOWN"))
        assert unknown["state"] == "STALE" and unknown["limitations"] == [CONTACT_UNVERIFIED]
        assert contact_document(None) == {
            "state": "NEVER", "as_of": None, "limitations": [CONTACT_HEALTH_ABSENT]}
        assert contact_document(None, CONTACT_NO_DIAGNOSTIC) == {
            "state": "NEVER", "as_of": None, "limitations": [CONTACT_NO_DIAGNOSTIC]}
