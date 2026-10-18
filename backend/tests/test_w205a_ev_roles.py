"""W2-05a spec commit 2 (no DB): `ev-roles-1`, the closed EV v4 channel table, IDENTITY_KWH and the EV gate.

`D-2026-10-18-w2-05-buildspec` "Role set", Q1, Q2, Q4, Q8.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from assetops_contracts.source_envelope_v4 import (
    V4_CHANNEL_MAPPINGS,
    V4_CHANNEL_MAPPINGS_BY_PROFILE,
    V4_COLD_CHANNEL_MAPPINGS,
    V4_EV_CHANNEL_MAPPINGS,
    V4_EV_MAPPING_PROFILE_ID,
    V4_EV_MAPPING_PROFILE_VERSION,
    V4_MAPPING_PROFILE_ID,
    V4_MAPPING_PROFILE_VERSION,
)

from assetops_backend.sites import binding_roles as br
from assetops_backend.sites.binding_service import BindingRefused, BindingRequest
from assetops_backend.sites.ev_foundation import ev_blocking_gaps
from assetops_backend.sites.site_parsing import parse_site_document, render_site_document

BACKEND = Path(__file__).resolve().parents[1]
FIXTURE = BACKEND / "tests" / "fixtures" / "w2" / "ev-lab-001.yaml"
CONVERSION = BACKEND / "conversions" / "ev-lab-001-bindings.json"
ROLES = br.roles_for(br.ROLE_SET_EV_1)
IDENTITY = {"kind": "IDENTITY", "parameters": {}}
KWH = {"kind": "IDENTITY_KWH", "parameters": {}}


def connector_tuples(prefix: str) -> set[tuple[str, str]]:
    return {(f"{prefix}-charger-controller", "session-event"), (f"{prefix}-connector-controller", "fault-event"),
            (f"{prefix}-connector-controller", "state"), (f"{prefix}-connector-controller", "requested-power"),
            (f"{prefix}-connector-controller", "allocated-limit"), (f"{prefix}-connector-meter", "energy"),
            (f"{prefix}-connector-meter", "power")}


class TestRoleSet:
    def test_site_type_serves_only_ev_roles_1(self) -> None:
        assert br.ROLE_SET_BY_SITE_TYPE["EV_CHARGING"] == "ev-roles-1"
        assert br.SERVED_ROLE_SETS_BY_SITE_TYPE["EV_CHARGING"] == frozenset({"ev-roles-1"})
        assert br.serves("EV_CHARGING", "ev-roles-1") and not br.serves("EV_CHARGING", "cold-roles-1")
        assert not br.serves("COLDCHAIN", "ev-roles-1")

    def test_exact_eight_roles(self) -> None:
        assert {(r.role, r.asset_type, r.canonical_unit, r.value_kind, r.cardinality, r.required)
                for r in ROLES.values()} == {
            ("ev_session_event", "EV_CONNECTOR", "event", "EVENT", "PER_ASSET", True),
            ("ev_connector_fault", "EV_CONNECTOR", "event", "EVENT", "PER_ASSET", False),
            ("ev_connector_state", "EV_CONNECTOR", "state", "STATE", "PER_ASSET", True),
            ("ev_connector_energy", "EV_CONNECTOR", "kWh", "INTERVAL_DELTA", "PER_ASSET", True),
            ("ev_connector_power", "EV_CONNECTOR", "kW", "NUMBER", "PER_ASSET", False),
            ("ev_site_import", "METER", "kW", "NUMBER", "ONE", False),
            ("ev_requested_power", "EV_CONNECTOR", "kW", "NUMBER", "PER_ASSET", False),
            ("ev_allocated_limit", "EV_CONNECTOR", "kW", "NUMBER", "PER_ASSET", False),
        }
        assert ROLES["ev_connector_state"].enum_states == (
            "AVAILABLE", "PLUGGED", "AUTHORIZING", "CHARGING", "FAULTED", "DISABLED")
        assert set(br.EV_CADENCE_PROPERTY_BY_ROLE) == set(ROLES)

    def test_older_role_sets_are_unchanged(self) -> None:
        assert br.ROLE_SET_BY_SITE_TYPE["COLDCHAIN"] == "cold-roles-1"
        assert br.ROLE_SET_BY_SITE_TYPE["MINIGRID"] == "minigrid-roles-2"
        assert br.CONVERSION_KINDS == ("IDENTITY", "ENUM")


class TestConversions:
    def test_energy_accepts_only_identity_kwh_from_kwh(self) -> None:
        energy = ROLES["ev_connector_energy"]
        assert br.conversion_problem(energy, "kWh", KWH) is None
        assert "use the IDENTITY_KWH" in br.conversion_problem(energy, "kWh", IDENTITY)
        assert "accepts only 'kWh'" in br.conversion_problem(energy, "kW", KWH)
        assert "no parameters" in br.conversion_problem(energy, "kWh", {"kind": "IDENTITY_KWH",
                                                                         "parameters": {"scale": 1}})

    @pytest.mark.parametrize("role,unit", [("ev_connector_power", "kW"), ("ev_site_import", "kW")])
    def test_identity_kwh_is_closed_to_energy(self, role, unit) -> None:
        assert "applies only to interval energy" in br.conversion_problem(ROLES[role], unit, KWH)
        assert br.conversion_problem(ROLES[role], unit, IDENTITY) is None

    def test_identity_kwh_is_refused_on_older_role_sets(self) -> None:
        cold = br.roles_for("cold-roles-1")["compressor_power"]
        assert "applies only to interval energy" in br.conversion_problem(cold, "kW", KWH)

    def test_state_and_events(self) -> None:
        state = ROLES["ev_connector_state"]
        assert br.conversion_problem(state, "state", {"kind": "ENUM", "parameters": {"map": {"x": "CHARGING"}}}) \
            is None
        assert br.conversion_problem(state, "state", {"kind": "ENUM", "parameters": {"map": {"x": "RUNNING"}}})
        assert br.conversion_problem(ROLES["ev_session_event"], "event", IDENTITY) is None


class TestClosedTable:
    def test_profile_lookup(self) -> None:
        assert (V4_MAPPING_PROFILE_ID, V4_MAPPING_PROFILE_VERSION) == ("simulator-lab-gateway-cold", 1)
        assert (V4_EV_MAPPING_PROFILE_ID, V4_EV_MAPPING_PROFILE_VERSION) == ("simulator-lab-gateway-ev", 1)
        assert V4_CHANNEL_MAPPINGS_BY_PROFILE[("simulator-lab-gateway-cold", 1)] is V4_COLD_CHANNEL_MAPPINGS
        assert V4_CHANNEL_MAPPINGS_BY_PROFILE[("simulator-lab-gateway-ev", 1)] is V4_EV_CHANNEL_MAPPINGS

    def test_ev_table_is_exactly_the_q1_tuples(self) -> None:
        assert set(V4_EV_CHANNEL_MAPPINGS) == connector_tuples("c1") | connector_tuples("c2") | {
            ("site-meter", "import")}
        assert all(V4_CHANNEL_MAPPINGS[k] == v for k, v in V4_EV_CHANNEL_MAPPINGS.items())

    def test_cold_table_is_unchanged(self) -> None:
        assert len(V4_COLD_CHANNEL_MAPPINGS) == 12
        assert all(e.role in br.roles_for("cold-roles-1") for e in V4_COLD_CHANNEL_MAPPINGS.values())
        assert not set(V4_COLD_CHANNEL_MAPPINGS) & set(V4_EV_CHANNEL_MAPPINGS)

    def test_reserved_w200_tuples_are_labelled_and_not_in_the_ev_profile(self) -> None:
        assert V4_CHANNEL_MAPPINGS[("charger-controller", "session-event")].role == "ev_session_event"
        assert V4_CHANNEL_MAPPINGS[("connector-controller", "fault-event")].role == "ev_connector_fault"
        assert ("charger-controller", "session-event") not in V4_EV_CHANNEL_MAPPINGS

    def test_entry_metadata_matches_roles(self) -> None:
        for (device, signal), entry in V4_EV_CHANNEL_MAPPINGS.items():
            role = ROLES[entry.role]
            assert entry.family == ("EVENT" if role.value_kind == "EVENT" else "MEASUREMENT"), (device, signal)
            assert set(entry.allowed_record_kinds) == set(role.event_kinds)
            if entry.family == "MEASUREMENT":
                assert entry.allowed_units == (role.canonical_unit,)
        energy = V4_EV_CHANNEL_MAPPINGS[("c1-connector-meter", "energy")]
        assert (energy.measurement, energy.requires_session, energy.allowed_units) == ("INTERVAL_DELTA", True,
                                                                                       ("kWh",))
        assert V4_EV_CHANNEL_MAPPINGS[("c2-connector-meter", "power")].measurement == "INTERVAL_MEAN"
        assert V4_EV_CHANNEL_MAPPINGS[("site-meter", "import")].requires_session is False
        assert V4_EV_CHANNEL_MAPPINGS[("c1-connector-controller", "state")].measurement == "STATE_AT_INSTANT"
        assert V4_EV_CHANNEL_MAPPINGS[("c1-charger-controller", "session-event")].requires_session is True


class TestFixture:
    def test_fixture_parses_and_round_trips(self) -> None:
        document = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))
        site = parse_site_document(document, source="ev-lab-001.yaml")
        assert (site.site_type, site.timezone) == ("EV_CHARGING", "Etc/UTC")
        assert parse_site_document(render_site_document(site), source="render") == site

    def test_every_binding_is_an_ev_table_tuple_on_its_connector(self) -> None:
        document = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))
        devices = {d["device_id"]: d for d in document["foundation"]["devices"]}
        bindings = json.loads(CONVERSION.read_text(encoding="utf-8"))["bindings"]
        assert {(b["device_id"], b["signal_id"]) for b in bindings} == set(V4_EV_CHANNEL_MAPPINGS)
        for b in bindings:
            entry = V4_EV_CHANNEL_MAPPINGS[(b["device_id"], b["signal_id"])]
            assert b["role"] == entry.role
            assert devices[b["device_id"]]["component_id"] == b["asset_code"]
            assert br.conversion_problem(ROLES[b["role"]], b["source_unit"], b["conversion"]) is None


class TestBlockingGaps:
    def content(self) -> dict:
        document = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))
        return document["foundation"]

    def complete(self) -> set[tuple[str, str]]:
        return {(r, c) for c in ("c1", "c2")
                for r in ("ev_connector_energy", "ev_session_event", "ev_connector_state")}

    def test_complete_has_no_gap_and_optional_roles_never_block(self) -> None:
        assert ev_blocking_gaps(self.content(), self.complete()) == []

    @pytest.mark.parametrize("role,code", [("ev_connector_energy", "METER_NOT_BOUND"),
                                           ("ev_session_event", "SESSION_EVENTS_NOT_BOUND"),
                                           ("ev_connector_state", "STATUS_NOT_BOUND")])
    def test_missing_required_role_per_connector(self, role, code) -> None:
        gaps = ev_blocking_gaps(self.content(), self.complete() - {(role, "c2")})
        assert [(g[0], g[1]) for g in gaps] == [(code, role)]

    def test_missing_limit_feed_and_connector(self) -> None:
        content = self.content()
        content["components"][0].pop("properties")
        assert [g[0] for g in ev_blocking_gaps(content, self.complete())] == ["FEED_OR_LIMIT_MISSING"]
        content["components"] = [c for c in content["components"]
                                 if c["component_type"] not in ("AC_BUS", "EV_CONNECTOR")]
        assert [g[0] for g in ev_blocking_gaps(content, set())] == ["CONNECTOR_NOT_DECLARED",
                                                                   "FEED_OR_LIMIT_MISSING"]


def test_a_submitted_cadence_field_is_a_request_refusal() -> None:
    item = {"device_id": "c1-connector-meter", "signal_id": "energy", "asset_id": None,
            "role": "ev_connector_energy", "source_unit": "kWh", "canonical_unit": "kWh", "conversion": KWH,
            "cadence_seconds": 300}
    with pytest.raises(BindingRefused) as caught:
        BindingRequest.from_wire(item, 0)
    assert caught.value.code == "BINDING_REQUEST_INVALID"
