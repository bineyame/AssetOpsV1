"""W2-05a EV vocabulary, typed state property, connector enable schedule and EV Foundation validator (no database).

`.agent/W2-05a-build-spec.md` commit 1 (`D-2026-10-18-w2-05-buildspec`, Architect answers Q3-Q5).
"""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

from assetops_backend.sites import models
from assetops_backend.sites.ev_foundation import (
    EV_CONFIGURATION_INVALID,
    EvConfigurationInvalid,
    _find_cycle,
    validate_ev_schedule_interval,
)
from assetops_backend.sites.foundation_content import content_from_record
from assetops_backend.sites.foundation_service import ImportSource, _value_refusal_code, plan_import
from assetops_backend.sites.ports import SiteConfigurationInvalid
from assetops_backend.sites.site_parsing import parse_site_document, render_site_document

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "w2"
COLD = yaml.safe_load((FIXTURES / "cold-001.yaml").read_text(encoding="utf-8"))
UTC = timezone.utc


def prop(key, value, unit):
    return {"property_key": key, "value": value, "unit": unit, "source": "SITE", "source_version": 1}


def connector(cid):
    return {
        "component_id": cid, "component_type": "EV_CONNECTOR", "display_name": f"Connector {cid}",
        "properties": [
            prop("ev-connector-max-power", 60.0, "kW"),
            prop("ev-connector-enabled", "ENABLED", "state"),
            prop("ev-meter-resolution", 0.001, "kWh"),
            prop("ev-meter-error-bound", 0.001, "kWh"),
            prop("ev-status-cadence", 1.0, "min"),
            prop("ev-meter-cadence", 5.0, "min"),
            prop("ev-clock-error-bound", 30.0, "s"),
        ],
    }


def node(nid, cid, role):
    return {"node_id": nid, "component_id": cid, "node_role": role}


def edge(cid, a, b, medium):
    return {"connection_id": cid, "from_node": a, "to_node": b, "medium": medium}


def tuesday(start="08:00", end="16:00", offset=0, day="TUESDAY"):
    return {"weekday": day, "local_start": start, "local_end": end, "utc_offset_minutes": offset}


def ev_doc(zone="Etc/UTC"):
    return {
        "site_id": "EV-LAB-001", "display_name": "EV charging lab", "site_type": "EV_CHARGING",
        "location": {"country": "Ethiopia", "locality": "Addis Ababa"}, "timezone": zone,
        "lifecycle_status": "PLANNED", "origin": "USER", "source": {"mode": "SIMULATED"},
        "foundation": {
            "version": 1, "valid_from": "2026-10-01T00:00:00Z", "summary": "EV charging lab Foundation.",
            "components": [
                {"component_id": "feed-1", "component_type": "AC_BUS", "display_name": "Site feed",
                 "properties": [prop("ev-site-import-limit", 80.0, "kW")]},
                {"component_id": "site-meter-1", "component_type": "METER", "display_name": "Site import meter"},
                {"component_id": "charger-1", "component_type": "EV_CHARGER", "display_name": "Charger 1",
                 "properties": [prop("ev-charger-max-power", 60.0, "kW")]},
                connector("c1"),
                connector("c2"),
            ],
            "topology": {
                "nodes": [node("n-feed", "feed-1", "BUS"), node("n-meter", "site-meter-1", "METERING"),
                          node("n-charger", "charger-1", "CHARGER"), node("n-c1", "c1", "CONNECTOR"),
                          node("n-c2", "c2", "CONNECTOR")],
                "connections": [edge("e1", "n-feed", "n-meter", "AC"), edge("e2", "n-meter", "n-charger", "AC"),
                                edge("e3", "n-charger", "n-c1", "SIGNAL"),
                                edge("e4", "n-charger", "n-c2", "SIGNAL")],
            },
            "connector_enable_schedules": [
                {"connector_asset_id": "c1", "time_zone": zone, "weekly": [tuesday()]},
                {"connector_asset_id": "c2", "time_zone": zone, "weekly": [tuesday()]},
            ],
        },
    }


def parse(document):
    return parse_site_document(document, source="test document")


def comp(document, cid):
    return next(c for c in document["foundation"]["components"] if c["component_id"] == cid)


def refused(document, path_fragment):
    with pytest.raises(EvConfigurationInvalid) as caught:
        parse(document)
    assert path_fragment in caught.value.path, (caught.value.path, str(caught.value))
    assert caught.value.code == EV_CONFIGURATION_INVALID
    return caught.value


class TestVocabulary:
    def test_closed_vocabularies_carry_the_ev_members(self) -> None:
        assert "EV_CHARGING" in models.SITE_TYPES
        assert {"EV_CHARGER", "EV_CONNECTOR"} <= models.COMPONENT_TYPES
        assert {"CHARGER", "CONNECTOR"} <= models.TOPOLOGY_NODE_ROLES
        assert {"AC", "SIGNAL"} <= models.CONNECTION_MEDIA

    def test_nine_ev_properties_with_exact_unit_and_carrier(self) -> None:
        expected = {
            "ev-site-import-limit": ("kW", "AC_BUS"), "ev-charger-max-power": ("kW", "EV_CHARGER"),
            "ev-connector-max-power": ("kW", "EV_CONNECTOR"), "ev-connector-enabled": ("state", "EV_CONNECTOR"),
            "ev-meter-resolution": ("kWh", "EV_CONNECTOR"), "ev-meter-error-bound": ("kWh", "EV_CONNECTOR"),
            "ev-status-cadence": ("min", "EV_CONNECTOR"), "ev-meter-cadence": ("min", "EV_CONNECTOR"),
            "ev-clock-error-bound": ("s", "EV_CONNECTOR"),
        }
        assert set(models.EV_PROPERTY_CARRIERS) == set(expected)
        for key, (unit, carrier) in expected.items():
            assert models.COMPONENT_PROPERTY_DEFINITIONS[key].unit == unit
            assert models.EV_PROPERTY_CARRIERS[key] == carrier
        assert models.COMPONENT_PROPERTY_DEFINITIONS["ev-connector-enabled"].kind == "CONTROL"
        assert models.STATE_PROPERTY_VALUES == {"ev-connector-enabled": frozenset({"ENABLED", "DISABLED"})}


class TestParserAndRender:
    def test_complete_ev_document_parses_and_round_trips(self) -> None:
        record = parse(ev_doc())
        assert record.site_type == "EV_CHARGING"
        c1 = next(c for c in record.foundation.components if c.component_id == "c1")
        enabled = next(p for p in c1.properties if p.property_key == "ev-connector-enabled")
        assert enabled.value == "ENABLED" and enabled.unit == "state" and enabled.kind == "CONTROL"
        schedules = record.foundation.connector_enable_schedules
        assert [s.connector_asset_id for s in schedules] == ["c1", "c2"]
        assert schedules[0].weekly[0] == models.WeeklyEnableInterval("TUESDAY", "08:00", "16:00", 0)
        rendered = render_site_document(record)
        assert rendered["foundation"]["connector_enable_schedules"][0]["weekly"][0]["local_start"] == "08:00"
        assert parse(rendered) == record
        assert content_from_record(record)["connector_enable_schedules"][1]["connector_asset_id"] == "c2"

    def test_a_foundation_without_schedules_keeps_its_rendered_bytes(self) -> None:
        record = parse(copy.deepcopy(COLD))
        rendered = render_site_document(record)
        assert "connector_enable_schedules" not in rendered["foundation"]
        source_values = [p["value"] for c in COLD["foundation"]["components"] for p in c.get("properties") or ()]
        rendered_values = [p["value"] for c in rendered["foundation"]["components"] for p in c["properties"] or ()]
        assert rendered_values == source_values
        assert all(type(v) is float for v in rendered_values)

    @pytest.mark.parametrize("value", ["enabled", "ON", True, 1, None])
    def test_connector_enabled_accepts_only_the_exact_state_members(self, value) -> None:
        document = ev_doc()
        comp(document, "c1")["properties"][1]["value"] = value
        with pytest.raises(SiteConfigurationInvalid, match="ev-connector-enabled"):
            parse(document)

    def test_connector_enabled_needs_the_state_unit(self) -> None:
        document = ev_doc()
        comp(document, "c1")["properties"][1]["unit"] = "kW"
        with pytest.raises(SiteConfigurationInvalid, match="'state'"):
            parse(document)

    def test_a_numeric_property_still_refuses_a_string(self) -> None:
        document = ev_doc()
        comp(document, "c1")["properties"][0]["value"] = "ENABLED"
        with pytest.raises(SiteConfigurationInvalid, match="must be a number"):
            parse(document)

    def test_schedule_shape_is_strict(self) -> None:
        document = ev_doc()
        document["foundation"]["connector_enable_schedules"][0]["extra"] = 1
        with pytest.raises(SiteConfigurationInvalid, match="extra"):
            parse(document)
        document = ev_doc()
        document["foundation"]["connector_enable_schedules"][0]["weekly"][0]["utc_offset_minutes"] = True
        with pytest.raises(SiteConfigurationInvalid, match="utc_offset_minutes"):
            parse(document)
        document = ev_doc()
        document["foundation"]["connector_enable_schedules"][0]["connector_asset_id"] = "c9"
        with pytest.raises(SiteConfigurationInvalid, match="c9"):
            parse(document)

    def test_schedules_on_a_non_ev_site_are_refused(self) -> None:
        document = copy.deepcopy(COLD)
        document["foundation"]["connector_enable_schedules"] = [
            {"connector_asset_id": "cold-room", "time_zone": COLD["timezone"], "weekly": []}]
        with pytest.raises(SiteConfigurationInvalid, match="only an EV_CHARGING Site"):
            parse(document)


class TestProperties:
    @pytest.mark.parametrize("key", ["ev-connector-max-power", "ev-connector-enabled", "ev-meter-resolution",
                                     "ev-meter-error-bound", "ev-status-cadence", "ev-meter-cadence",
                                     "ev-clock-error-bound"])
    def test_a_declared_connector_missing_a_required_property_is_refused(self, key) -> None:
        document = ev_doc()
        c2 = comp(document, "c2")
        c2["properties"] = [p for p in c2["properties"] if p["property_key"] != key]
        error = refused(document, f"components[4].properties.{key}")
        assert "no default" in str(error)

    def test_a_declared_charger_missing_its_rating_is_refused(self) -> None:
        document = ev_doc()
        comp(document, "charger-1").pop("properties")
        refused(document, "components[2].properties.ev-charger-max-power")

    def test_missing_site_import_limit_is_publishable(self) -> None:
        document = ev_doc()
        comp(document, "feed-1").pop("properties")
        assert parse(document).site_type == "EV_CHARGING"

    def test_no_feed_and_no_connector_is_publishable(self) -> None:
        document = ev_doc()
        f = document["foundation"]
        f["components"] = [comp(document, "charger-1")]
        f["topology"] = None
        f.pop("connector_enable_schedules")
        assert parse(document).foundation.connector_enable_schedules is None

    @pytest.mark.parametrize("cid,index,key,value", [
        ("feed-1", 0, "ev-site-import-limit", 0.0), ("charger-1", 0, "ev-charger-max-power", 0.0),
        ("c1", 0, "ev-connector-max-power", 0.0), ("c1", 2, "ev-meter-resolution", 0.0),
        ("c1", 4, "ev-status-cadence", 0.0), ("c1", 5, "ev-meter-cadence", 0.0),
        ("c1", 6, "ev-clock-error-bound", 0.0)])
    def test_strictly_positive_values(self, cid, index, key, value) -> None:
        document = ev_doc()
        comp(document, cid)["properties"][index]["value"] = value
        refused(document, f"properties.{key}")

    def test_meter_error_bound_may_be_zero(self) -> None:
        document = ev_doc()
        comp(document, "c1")["properties"][3]["value"] = 0.0
        parse(document)

    @pytest.mark.parametrize("index,key,value", [
        (6, "ev-clock-error-bound", 86400.0), (2, "ev-meter-resolution", 100000000.0),
        (3, "ev-meter-error-bound", 100000000.0), (3, "ev-meter-error-bound", 0.0)])
    def test_unit_range_boundaries_are_inclusive(self, index, key, value) -> None:
        """Run 8 L3: `s` is bounded to 0..86400 and `kWh` to 0..1e8, inclusive."""
        document = ev_doc()
        comp(document, "c1")["properties"][index]["value"] = value
        parse(document)

    @pytest.mark.parametrize("index,key,value", [
        (6, "ev-clock-error-bound", 1e300), (6, "ev-clock-error-bound", 86400.001),
        (6, "ev-clock-error-bound", float("inf")), (6, "ev-clock-error-bound", float("nan")),
        (2, "ev-meter-resolution", 1e300), (2, "ev-meter-resolution", 100000000.001),
        (3, "ev-meter-error-bound", float("inf")), (3, "ev-meter-error-bound", -0.001)])
    def test_unit_range_outliers_and_nonfinite_values_are_refused(self, index, key, value) -> None:
        document = ev_doc()
        comp(document, "c1")["properties"][index]["value"] = value
        with pytest.raises(SiteConfigurationInvalid) as caught:
            parse(document)
        # The parser-wide range names the property position; the service maps it to EV_CONFIGURATION_INVALID
        # (test_w205a_ev_foundation_postgres: test_out_of_range_clock_bound_is_refused_as_ev_configuration_invalid).
        assert f"properties[{index}].value" in str(caught.value) or "finite" in str(caught.value)

    @pytest.mark.parametrize("index,key,value", [(4, "ev-status-cadence", 1.5), (5, "ev-meter-cadence", 5.5)])
    def test_cadence_above_its_ceiling_is_refused(self, index, key, value) -> None:
        document = ev_doc()
        comp(document, "c1")["properties"][index]["value"] = value
        error = refused(document, f"properties.{key}")
        assert "ceiling" in str(error)

    def test_property_on_the_wrong_carrier_is_refused(self) -> None:
        document = ev_doc()
        comp(document, "charger-1")["properties"].append(prop("ev-meter-cadence", 5.0, "min"))
        refused(document, "components[2].properties[1]")

    def test_wrong_unit_is_refused_by_the_shared_parser(self) -> None:
        document = ev_doc()
        comp(document, "c1")["properties"][6]["unit"] = "min"
        with pytest.raises(SiteConfigurationInvalid, match="'s'"):
            parse(document)

    def test_ev_site_value_refusals_carry_the_ev_code(self) -> None:
        assert _value_refusal_code("EV_CHARGING") == "EV_CONFIGURATION_INVALID"
        assert _value_refusal_code("COLDCHAIN") == "FOUNDATION_VALUE_INVALID"


class TestTopology:
    def test_orphan_connector_is_refused(self) -> None:
        document = ev_doc()
        document["foundation"]["topology"]["connections"].pop()
        refused(document, "components[4]")

    def test_connector_with_two_parent_chargers_is_refused(self) -> None:
        document = ev_doc()
        f = document["foundation"]
        f["components"].append({"component_id": "charger-2", "component_type": "EV_CHARGER",
                                "display_name": "Charger 2", "properties": [prop("ev-charger-max-power", 60.0, "kW")]})
        f["topology"]["nodes"].append(node("n-charger-2", "charger-2", "CHARGER"))
        f["topology"]["connections"] += [edge("e5", "n-meter", "n-charger-2", "AC"),
                                         edge("e6", "n-charger-2", "n-c1", "SIGNAL")]
        error = refused(document, "components[3]")
        assert "more than one parent charger" in str(error)

    def test_charger_not_fed_when_a_feed_is_declared_is_refused(self) -> None:
        document = ev_doc()
        document["foundation"]["topology"]["connections"].pop(1)
        refused(document, "components[2]")

    def test_a_second_feed_is_refused_with_its_path(self) -> None:
        # QD: an EV Foundation declares at most one AC_BUS; the path names the extra feed.
        document = ev_doc()
        f = document["foundation"]
        f["components"].append({"component_id": "feed-2", "component_type": "AC_BUS", "display_name": "Feed 2"})
        f["topology"]["nodes"].append(node("n-feed-2", "feed-2", "BUS"))
        f["topology"]["connections"].append(edge("e5", "n-feed-2", "n-meter", "AC"))
        error = refused(document, "components[5]")
        assert "second AC_BUS" in str(error)

    def test_a_second_feed_without_topology_is_refused(self) -> None:
        document = ev_doc()
        f = document["foundation"]
        f["components"].insert(1, {"component_id": "feed-2", "component_type": "AC_BUS",
                                   "display_name": "Feed 2"})
        f["topology"] = None
        f["connector_enable_schedules"] = [{"connector_asset_id": c, "time_zone": "Etc/UTC", "weekly": []}
                                           for c in ("c1", "c2")]
        refused(document, "components[1]")

    def test_unfed_meter_is_refused_once_a_feed_is_declared(self) -> None:
        # QC: every declared meter must have the declared feed as its parent, even one feeding no charger.
        document = ev_doc()
        f = document["foundation"]
        f["components"].append({"component_id": "meter-2", "component_type": "METER", "display_name": "Meter 2"})
        f["topology"]["nodes"].append(node("n-meter-2", "meter-2", "METERING"))
        error = refused(document, "components[5]")
        assert "not connected to the declared feed" in str(error)

    def test_no_feed_is_publishable_as_incomplete_configuration(self) -> None:
        # QC: without an AC_BUS, a declared meter, charger and connectors publish when every property and
        # schedule entry is valid and no connector has service hours.
        document = ev_doc()
        f = document["foundation"]
        f["components"] = [c for c in f["components"] if c["component_id"] != "feed-1"]
        f["topology"]["nodes"] = [n for n in f["topology"]["nodes"] if n["node_id"] != "n-feed"]
        f["topology"]["connections"] = f["topology"]["connections"][1:]
        for entry in f["connector_enable_schedules"]:
            entry["weekly"] = []
        site = parse(document)
        assert [c.component_type for c in site.foundation.components] == [
            "METER", "EV_CHARGER", "EV_CONNECTOR", "EV_CONNECTOR"]

    def test_no_feed_with_service_hours_is_refused(self) -> None:
        # QC: any nonempty schedule needs the complete feed->meter->charger->connector path.
        document = ev_doc()
        f = document["foundation"]
        f["components"] = [c for c in f["components"] if c["component_id"] != "feed-1"]
        f["topology"]["nodes"] = [n for n in f["topology"]["nodes"] if n["node_id"] != "n-feed"]
        f["topology"]["connections"] = f["topology"]["connections"][1:]
        f["connector_enable_schedules"][1]["weekly"] = []
        refused(document, "connector_enable_schedules[0].weekly")

    def test_duplicate_directed_edge_is_refused(self) -> None:
        document = ev_doc()
        document["foundation"]["topology"]["connections"].append(edge("e9", "n-meter", "n-charger", "AC"))
        refused(document, "topology.connections[4]")

    @pytest.mark.parametrize("a,b,medium", [("n-c1", "n-charger", "SIGNAL"), ("n-charger", "n-c1", "AC"),
                                            ("n-feed", "n-charger", "AC"), ("n-charger", "n-meter", "AC")])
    def test_undeclared_edge_shapes_are_refused(self, a, b, medium) -> None:
        document = ev_doc()
        document["foundation"]["topology"]["connections"].append(edge("e9", a, b, medium))
        refused(document, "topology.connections[4]")

    def test_wrong_node_role_is_refused(self) -> None:
        document = ev_doc()
        document["foundation"]["topology"]["nodes"][2]["node_role"] = "LOAD"
        refused(document, "topology.nodes[2].node_role")

    def test_cycle_detection(self) -> None:
        # The closed edge table admits no cycle among EV types (a reversed edge is refused as an undeclared
        # shape above); the detector itself still finds one.
        assert _find_cycle({"a": ["b"], "b": ["c"], "c": ["a"]}) == ["a", "b", "c", "a"]
        assert _find_cycle({"a": ["b"], "b": ["c"]}) is None


class TestSchedule:
    def schedules(self, document):
        return document["foundation"]["connector_enable_schedules"]

    def test_missing_entry_is_refused(self) -> None:
        document = ev_doc()
        self.schedules(document).pop()
        refused(document, "components[4]")

    def test_duplicate_entry_is_refused(self) -> None:
        document = ev_doc()
        self.schedules(document)[1]["connector_asset_id"] = "c1"
        refused(document, "connector_enable_schedules[1].connector_asset_id")

    def test_entry_must_name_a_connector(self) -> None:
        document = ev_doc()
        self.schedules(document)[1]["connector_asset_id"] = "charger-1"
        refused(document, "connector_enable_schedules[1].connector_asset_id")

    def test_zone_must_equal_the_site_timezone(self) -> None:
        document = ev_doc()
        self.schedules(document)[0]["time_zone"] = "Africa/Addis_Ababa"
        refused(document, "connector_enable_schedules[0].time_zone")

    @pytest.mark.parametrize("field,value", [("weekday", "tuesday"), ("weekday", "TUE"), ("local_start", "8:00"),
                                             ("local_start", "24:00"), ("local_end", "16:60")])
    def test_invalid_endpoint_spelling_is_refused(self, field, value) -> None:
        document = ev_doc()
        self.schedules(document)[0]["weekly"][0][field] = value
        refused(document, f"weekly[0].{field}")

    @pytest.mark.parametrize("start,end", [("16:00", "08:00"), ("08:00", "08:00")])
    def test_reversed_or_zero_interval_is_refused(self, start, end) -> None:
        document = ev_doc()
        self.schedules(document)[0]["weekly"] = [tuesday(start, end)]
        refused(document, "connector_enable_schedules[0].weekly[0]")

    def test_overlap_is_refused_but_adjacent_and_other_days_are_not(self) -> None:
        document = ev_doc()
        self.schedules(document)[0]["weekly"] = [tuesday("08:00", "12:00"), tuesday("12:00", "16:00"),
                                                 tuesday("09:00", "10:00", day="WEDNESDAY")]
        parse(document)
        self.schedules(document)[0]["weekly"].append(tuesday("11:00", "13:00"))
        error = refused(document, "connector_enable_schedules[0].weekly[3]")
        assert "overlaps" in str(error)

    def test_disabled_connector_marked_available_is_refused(self) -> None:
        document = ev_doc()
        comp(document, "c1")["properties"][1]["value"] = "DISABLED"
        refused(document, "connector_enable_schedules[0].weekly")
        self.schedules(document)[0]["weekly"] = []
        parse(document)

    def test_enabled_connector_may_declare_no_hours(self) -> None:
        document = ev_doc()
        self.schedules(document)[1]["weekly"] = []
        parse(document)

    def test_enablement_without_a_supply_path_is_refused(self) -> None:
        document = ev_doc()
        f = document["foundation"]
        f["components"] = [c for c in f["components"] if c["component_id"] not in ("feed-1", "site-meter-1")]
        f["topology"]["nodes"] = f["topology"]["nodes"][2:]
        f["topology"]["connections"] = f["topology"]["connections"][2:]
        error = refused(document, "connector_enable_schedules[0].weekly")
        assert "without a charger fed" in str(error)
        for entry in self.schedules(document):
            entry["weekly"] = []
        parse(document)


def interval(document, valid_from, valid_to):
    record = parse(document)
    validate_ev_schedule_interval(record.foundation, timezone_name=record.timezone, valid_from=valid_from,
                                  valid_to=valid_to, source="test")


def berlin(start="08:00", end="16:00", offset=60, day="TUESDAY"):
    document = ev_doc("Europe/Berlin")
    for entry in document["foundation"]["connector_enable_schedules"]:
        entry["weekly"] = [tuesday(start, end, offset, day)]
    return document


class TestEffectiveInterval:
    def test_utc_open_ended_revision_is_accepted(self) -> None:
        interval(ev_doc(), datetime(2026, 10, 1, tzinfo=UTC), None)

    def test_fixed_offset_zone_open_ended_is_accepted_with_its_offset(self) -> None:
        document = ev_doc("Africa/Addis_Ababa")
        for entry in document["foundation"]["connector_enable_schedules"]:
            entry["weekly"] = [tuesday(offset=180)]
        interval(document, datetime(2026, 10, 1, tzinfo=UTC), None)
        for entry in document["foundation"]["connector_enable_schedules"]:
            entry["weekly"] = [tuesday(offset=0)]
        with pytest.raises(EvConfigurationInvalid, match="does not match"):
            interval(document, datetime(2026, 10, 1, tzinfo=UTC), None)

    def test_dst_zone_needs_a_bounded_revision(self) -> None:
        with pytest.raises(EvConfigurationInvalid, match="bounded revision"):
            interval(berlin(), datetime(2026, 11, 1, tzinfo=UTC), None)

    def test_dst_zone_bounded_inside_one_offset_is_accepted(self) -> None:
        interval(berlin(), datetime(2026, 11, 1, tzinfo=UTC), datetime(2027, 3, 1, tzinfo=UTC))

    def test_bounded_interval_crossing_an_offset_change_is_refused(self) -> None:
        with pytest.raises(EvConfigurationInvalid, match="not the stated 60 min"):
            interval(berlin(), datetime(2027, 1, 1, tzinfo=UTC), datetime(2027, 6, 1, tzinfo=UTC))

    def test_nonexistent_local_instant_is_refused(self) -> None:
        # 2027-03-28 is the Sunday Europe/Berlin skips 02:00-03:00.
        with pytest.raises(EvConfigurationInvalid, match="does not exist") as caught:
            interval(berlin("02:30", "04:00", 60, "SUNDAY"), datetime(2027, 3, 1, tzinfo=UTC),
                     datetime(2027, 3, 29, tzinfo=UTC))
        assert caught.value.path.endswith("weekly[0].local_start")

    def test_ambiguous_local_instant_is_refused(self) -> None:
        # 2026-10-25 is the Sunday Europe/Berlin repeats 02:00-03:00.
        with pytest.raises(EvConfigurationInvalid, match="ambiguous"):
            interval(berlin("01:00", "02:30", 120, "SUNDAY"), datetime(2026, 10, 20, tzinfo=UTC),
                     datetime(2026, 10, 27, tzinfo=UTC))

    def test_import_runs_the_open_ended_check(self) -> None:
        record = parse(berlin())
        with pytest.raises(EvConfigurationInvalid, match="bounded revision"):
            plan_import(object(), ImportSource(path="ev.yaml", sha256="0" * 64, record=record),
                        datetime(2026, 10, 1, tzinfo=UTC))
