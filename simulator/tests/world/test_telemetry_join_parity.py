"""D-DD.81's join and D-DD.91's event rows (DD4a): `build_telemetry` dispatches on the Site's pack family, the cold
room's pack rows are bound, rounded and written by the one frame, and mini-grid stays byte-identical.

The mini-grid golden (`golden/telemetry_join_kobo_main.json`) was written from main at DD3a's merge (759759598),
before D-DD.90, D-DD.103 and the join: Kobo's 7 days from 2026-07-01 on D-DD.75 W1's inputs. The readings bytes are
compared whole. The readings manifest is compared whole except the two keys rulings add: D-DD.103's `span.to` and
D-DD.90's `2026-11` in the default sun table (both asserted here). DD3b2 regenerated it from the writer (D-DD.104's warm-up
start, D-DD.97's shape and D-DD.129's conditions move W1's inputs; the kernel and pack v8 are main's, D-DD.93): its
`source` names the revision.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re

import pytest

from assetops_simulator.world import telemetry as tel
from assetops_simulator.world import telemetry_cold

from .conftest import HERE, REPOSITORY_ROOT, load_fixture

GOLDEN = json.loads((HERE / "golden" / "telemetry_join_kobo_main.json").read_text(encoding="utf-8"))
ON1 = REPOSITORY_ROOT / "backend/tests/fixtures/on1"
BINDINGS = REPOSITORY_ROOT / "backend/conversions/world"
W1_BOOKS = {
    "months": {"2026-07": {"delivered_kwh": 8592, "unexplained_l": 12}},
    "fuel_notes": [{"at": "2026-07-01T10:00:00+03:00", "litres": 400},
                   {"at": "2026-07-05T10:00:00+03:00", "litres": 400}],
    "day_weights": {"classes": {"WD": [1, 2, 3, 4, 5], "SA": [6], "SU": [7]}, "WD": "1.00", "SA": "0.97", "SU": "0.90"},
    "sun_weights": tel.DEFAULT_SUN_WEIGHTS,  # D-DD.129: a required key (W1 ran on the default)
}
W1_ROWS = {
    "FUEL_TANK": [("tank-capacity", "2500", "L")],
    "GENERATOR": [("generator-no-load-fuel-rate", "0.62", "L/h"), ("generator-minimum-load", "30", "%")],
    "BATTERY": [("battery-charge-taper-start", "95", "%")],
}
THIKA_EVENTS = [{"kind": "GRID_LOSS", "at": "2026-10-06T19:11:00+03:00", "source": "incident.backup"},
                {"kind": "GENERATOR_FAILURE", "at": "2026-10-06T19:11:00+03:00", "source": "incident.backup"},
                {"kind": "GENERATOR_HAND_START", "at": "2026-10-06T19:14:00+03:00", "source": "incident.backup"},
                {"kind": "GRID_RESTORE", "at": "2026-10-06T22:00:00+03:00", "source": "Assumed"}]


def _sites(operator: str, codes: tuple[str, ...]) -> dict:
    onboarding = json.loads((ON1 / f"{operator}.onboarding.json").read_text(encoding="utf-8"))
    bindings = {c: json.loads((BINDINGS / f"{c}-bindings.json").read_text(encoding="utf-8")) for c in codes}
    if "KOBO-001" in bindings:
        # D-DD.114: Kobo's conversion moved to roles-5 after this golden was written from main (roles-4); the role-set
        # name is the only change in the file and enters the bytes, so the golden is checked on main's label.
        assert bindings["KOBO-001"]["role_set"] == "minigrid-roles-5"
        bindings["KOBO-001"] = {**bindings["KOBO-001"], "role_set": "minigrid-roles-4"}
    return tel.site_inputs(onboarding, bindings)


def _w1_kobo() -> dict:
    sites = _sites("lakeside-power", ("KISIWA-001", "KOBO-001", "MTO-001"))
    kobo = copy.deepcopy(next(s for s in sites["sites"] if s["code"] == "KOBO-001"))
    for component in kobo["foundation"]["components"]:
        # D-DD.153: the tank's declared level accuracy is new in `/2` after this golden; it moves the foundation digest only.
        component["properties"] = [p for p in component["properties"]
                                   if not p["property_key"].startswith("fuel-level-sensor-accuracy")]
        for key, value, unit in W1_ROWS.get(component["type"], ()):
            component["properties"] = [p for p in component["properties"] if p["property_key"] != key]
            component["properties"].append({"property_key": key, "value": value, "unit": unit})
    return kobo


def _cold_books(events=(), ledger=()) -> dict:
    history = load_fixture()["history"]
    return {"ledger": list(ledger), "cooling": history["families"]["cooling"], "seasons": history["seasons"],
            "day_classes": history["day_classes"], "events": list(events)}


def _move(code: str, at: str, direction: str, n: int) -> dict:
    return {"site_code": code, "clocks": {"occurred_at": at}, "quantity": {"value": str(n), "unit": "crate"},
            "body": {"batch_ref": "B-1", "direction": direction}}


# ---- mini-grid: byte-identical to main --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def kobo_result() -> tel.TelemetryResult:
    return tel.build_telemetry({}, {"sites": [_w1_kobo()]}, {"KOBO-001": W1_BOOKS}, start="2026-07-01",
                               end="2026-07-07")


def test_kobo_seven_days_readings_bytes_equal_mains(kobo_result: tel.TelemetryResult) -> None:
    days = {p: hashlib.sha256(b).hexdigest() for p, b in kobo_result.files if p.endswith(".readings.json")}
    expected = {p: d for p, d in GOLDEN["files"].items() if p.endswith(".readings.json")}
    assert len(days) == 7
    assert days == expected


def test_kobo_seven_days_manifest_equals_mains_but_the_ruled_keys(kobo_result: tel.TelemetryResult) -> None:
    path = "lakeside-power/telemetry/KOBO-001.manifest.json"
    manifest = copy.deepcopy(dict(kobo_result.manifests)[path])
    assert manifest["span"].pop("to") == "2026-07-08T00:00:00+03:00"  # D-DD.103
    seasons = manifest["conditions"]["sun_outside_calendar"]["weights"]["seasons"]
    assert seasons.pop("2026-11") == "short_rains"  # D-DD.90
    assert manifest == GOLDEN["manifests"][path]


# ---- the dispatch and the cold frame ----------------------------------------------------------------------------


@pytest.fixture(scope="module")
def thika_day() -> tuple[dict, list[dict]]:
    thika = next(s for s in _sites("harvest-cold", ("COLD-THIKA",))["sites"])
    ledger = [_move("COLD-THIKA", "2026-10-06T08:00:00+03:00", "IN", 20)]
    result = tel.build_telemetry({}, {"sites": [thika]}, {"COLD-THIKA": _cold_books(THIKA_EVENTS, ledger)},
                                 start="2026-10-06", end="2026-10-06")
    files = dict(result.files)
    document = json.loads(files["harvest-cold/telemetry/COLD-THIKA.2026-10-06.readings.json"])
    return dict(result.manifests)["harvest-cold/telemetry/COLD-THIKA.manifest.json"], document["readings"]


def test_a_cold_room_is_written_by_the_frame_with_its_bindings(thika_day) -> None:
    manifest, rows = thika_day
    bound = {(b["device_id"], b["signal_id"]): b for b in _sites("harvest-cold", ("COLD-THIKA",))["sites"][0]["bindings"]}
    assert rows and all((r["source_id"], r["signal_id"]) in bound for r in rows)
    assert all(r["unit"] == bound[(r["source_id"], r["signal_id"])]["source_unit"] for r in rows)
    chamber = [r for r in rows if r["source_id"] == "chamber-probe"]
    assert len(chamber) == 288 and all(re.fullmatch(r"-?\d+\.\d{3}", r["value"]) for r in chamber)
    assert chamber[0]["start"] == chamber[0]["end"] == "2026-10-06T00:00:00+03:00"
    assert manifest["pack"] == {"model": "cold-thermal", "version": 2}
    assert manifest["span"] == {"first": "2026-10-06", "last": "2026-10-06", "to": "2026-10-07T00:00:00+03:00"}
    assert manifest["private_parameters"]["model"] == "cold-thermal/2"
    assert {c["condition"] for c in manifest["conditions"]} >= {"GRID_LOSS", "GENERATOR_HAND_START"}


def test_event_rows_carry_the_v4_event_fields_and_ties_keep_the_packs_order(thika_day) -> None:
    _manifest, rows = thika_day
    start = [r for r in rows if r["signal_id"] == "start-event"]
    assert [(r["start"][11:16], r["event"]["record_kind"], r["event"]["outcome"], r["event"]["actor"],
             r["event"]["ordinal"]) for r in start] == [
        ("19:11", "START_REQUEST", "REQUESTED", "CONTROLLER", 1), ("19:11", "START_RESULT", "FAILED", "CONTROLLER", 2),
        ("19:14", "START_RESULT", "SUCCEEDED", "OPERATOR", 3)]
    for r in start:
        assert r["value"] is None and r["unit"] == "event" and r["start"] == r["end"]
        assert set(r["event"]) == {"record_kind", "outcome", "actor", "component_id", "ordinal", "correlation"}
        assert r["event"]["correlation"][0] == "outage" and r["event"]["component_id"] == "generator-1"
    door = [r for r in rows if r["source_id"] == "door-sensor"]
    assert [r["event"]["correlation"] for r in door] == [["door-cycle", 1], ["door-cycle", 1]]  # the pack's key (D-DD.91 wrote `door`)
    measurements = [r for r in rows if r["unit"] != "event"]
    assert measurements and all("event" not in r for r in measurements)
    keys = [(r["start"], r["source_id"], r["signal_id"], r.get("event", {}).get("ordinal", 0)) for r in rows]
    assert keys == sorted(keys)


def test_an_ev_depot_is_a_vertical_run() -> None:
    """D-DD.123: the EV depot is written by `EvSiteRun` behind this frame (`test_dd4_ev_join` writes its days)."""
    depot = next(s for s in _sites("metro-bus", ("EV-EMB",))["sites"])
    assert tel.pack_family(depot) == "ev-charger" and tel.VERTICAL_PACKS["ev-charger"] == ("ev-charger", 1)


@pytest.mark.parametrize("edit", ["drop", "unit"])
def test_a_cold_channel_without_its_binding_or_with_a_wrong_event_unit_refuses(edit: str) -> None:
    thika = copy.deepcopy(next(s for s in _sites("harvest-cold", ("COLD-THIKA",))["sites"]))
    door = next(b for b in thika["bindings"] if b["device_id"] == "door-sensor")
    if edit == "drop":
        thika["bindings"].remove(door)
    else:
        door["source_unit"] = "state"
    ledger = [_move("COLD-THIKA", "2026-10-06T08:00:00+03:00", "IN", 20)]
    with pytest.raises(tel.TelemetryRefused) as caught:
        tel.build_telemetry({}, {"sites": [thika]}, {"COLD-THIKA": _cold_books(ledger=ledger)}, start="2026-10-06",
                            end="2026-10-06")
    assert caught.value.code == "TEL_BINDING"


def test_the_cold_module_keeps_no_frame_of_its_own() -> None:
    source = (REPOSITORY_ROOT / "simulator/assetops_simulator/world/telemetry_cold.py").read_text(encoding="utf-8")
    for banned in ("QUANTUM", "readings_bytes", "class TelemetryRefused", "record_kind} {r.outcome",
                   "ValueError("):
        assert banned not in source, banned
    assert telemetry_cold.TelemetryRefused is tel.TelemetryRefused
