"""DD4b rejoin (D-DD.81, D-DD.91, D-DD.123): the EV depot run behind the one frame.

`build_telemetry` dispatches `ev-charger` to `EvSiteRun` through `VERTICAL_RUNS`; the run's seven-element rows are
bound, rounded and written by the frame; refusals are the frame's `TelemetryRefused`; the span may end at a local
instant (D-DD.103); the run's faults and CLOCK-1 come from module tables pinned to `M`."""

from __future__ import annotations

import json
from datetime import datetime

import pytest

from assetops_simulator.world import telemetry as tel
from assetops_simulator.world import telemetry_cold, telemetry_ev
from assetops_simulator.world.telemetry_ev import EvSiteRun

from .books_support import EV, built, files_by_name, manifest
from .conftest import REPOSITORY_ROOT
from .test_dd4_telemetry_ev import books, f_site

ON1 = REPOSITORY_ROOT / "backend/tests/fixtures/on1"
BINDINGS = REPOSITORY_ROOT / "backend/conversions/world"


def _sites() -> dict:
    onboarding = json.loads((ON1 / "metro-bus.onboarding.json").read_text(encoding="utf-8"))
    codes = [s["code"] for s in onboarding["sites"]]
    bindings = {c: json.loads((BINDINGS / f"{c}-bindings.json").read_text(encoding="utf-8")) for c in codes}
    return tel.site_inputs(onboarding, bindings)


def _decided(code: str) -> dict:
    out = books(code, faults=list(telemetry_ev.EV_FAULTS.get(code, ())))
    out["tariffs"] = []
    return out


def test_j1_the_frame_dispatches_ev_through_one_table() -> None:
    assert tel.VERTICAL_PACKS["ev-charger"] == ("ev-charger", 1)
    assert tel.VERTICAL_RUNS == {"cold-thermal": telemetry_cold.ColdSiteRun, "ev-charger": EvSiteRun}


def test_j2_ev_readings_are_bound_and_written_by_the_frame() -> None:
    sites = _sites()
    result = tel.build_telemetry({}, sites, {"EV-KAS": _decided("EV-KAS")}, start="2026-11-01", end="2026-11-02",
                                 only=("EV-KAS",))
    names = [n for n, _ in result.files]
    assert "metro-bus/telemetry/EV-KAS.2026-11-01.readings.json" in names
    day = json.loads(dict(result.files)["metro-bus/telemetry/EV-KAS.2026-11-01.readings.json"])
    site = next(s for s in sites["sites"] if s["code"] == "EV-KAS")
    bound = {(b["device_id"], b["signal_id"]) for b in site["bindings"]}
    assert {(r["source_id"], r["signal_id"]) for r in day["readings"]} <= bound
    events = [r for r in day["readings"] if "event" in r]
    assert events and all(r["value"] is None and r["unit"] == "event" for r in events)
    kinds = {r["event"]["record_kind"] for r in events}
    assert {"EV_SESSION_START", "EV_CONNECTOR_FAULT", "EV_SESSION_ABORT"} <= kinds
    for r in events:
        e = r["event"]
        assert set(e) >= {"record_kind", "outcome", "actor", "component_id", "ordinal", "correlation"}
        assert e["actor"] == "CONTROLLER" and isinstance(e["ordinal"], int) and e["ordinal"] >= 1
        if e["record_kind"].startswith("EV_SESSION"):
            assert e["session_id"] and e["connector_id"] == e["component_id"]
    manifest_doc = dict(result.manifests)["metro-bus/telemetry/EV-KAS.manifest.json"]
    assert manifest_doc["pack"] == {"model": "ev-charger", "version": 1}
    assert any(c["condition"] == "rotation" for c in manifest_doc["conditions"])


def test_j3_refusals_are_the_frames_and_the_span_ends_at_a_local_instant() -> None:
    with pytest.raises(tel.TelemetryRefused) as caught:
        EvSiteRun(f_site("EV-KAS"), books("EV-KAS", faults=[{"asset": "ch-k9", "at": "2026-11-01T00:00:00+03:00",
                                                             "source": "t"}]), "2026-11-01", "2026-11-01")
    assert caught.value.code == "TEL_FOUNDATION"
    r = EvSiteRun(f_site("EV-KAS"), books("EV-KAS"), "2026-11-05", "2026-11-06T06:00")
    for _ in r.days:
        r.advance_day()
    last = r.day_records(r.days[-1])
    assert r.days[-1].isoformat() == "2026-11-06"
    assert max(row[3] for row in last) == datetime.fromisoformat("2026-11-06T06:00:00+03:00")
    assert all(len(row) == 7 for row in last)
    assert {d["service_day"] for d in r.departures()} == {"2026-11-05"}


def test_j4_fault_and_clock_tables_are_pinned_to_m() -> None:
    sites = {s["code"]: s for t in manifest()["tenants"] if t["tenant"] == EV for s in t["sites"]}
    assert sorted(telemetry_ev.EV_FAULTS) == ["EV-KAS", "EV-RUI"]
    (kas,) = telemetry_ev.EV_FAULTS["EV-KAS"]
    assert kas["asset"] == sites["EV-KAS"]["incident"]["asset"].lower()
    assert datetime.fromisoformat(kas["at"]) == datetime.fromisoformat(sites["EV-KAS"]["incident"]["fault"]["at"])
    (rui,) = telemetry_ev.EV_FAULTS["EV-RUI"]
    assert sites["EV-RUI"]["incident"]["asset"] == "CH-R7 connector 2" and rui["asset"] == "ch-r7-c2"
    assert "6 Oct" in sites["EV-RUI"]["incident"]["fault"] and rui["at"].startswith("2026-10-06T")
    clock = next(d for d in manifest()["disorder_tests"] if d["id"] == "CLOCK-1")
    (c,) = telemetry_ev.EV_CLOCK["EV-EMB"]
    assert "4 min" in clock["what"] and c["minutes"] == 4 and c["charger"] == 3


def test_j5_ev_books_from_the_exported_roster() -> None:
    view, history, records, books_result = built()
    rosters = [f for f in books_result.files if f.key == telemetry_ev.ROSTER_KEY]
    assert [f for f in files_by_name(books_result) if f.endswith("ev-fleet-roster.csv")]
    out = telemetry_ev.ev_books_for(view, rosters)
    assert sorted(out) == ["EV-EMB", "EV-KAS", "EV-RUI"]
    assert out["EV-EMB"]["practice"] == telemetry_ev.PRACTICE and out["EV-KAS"]["practice"] == {}
    assert out["EV-KAS"]["faults"] == list(telemetry_ev.EV_FAULTS["EV-KAS"])
    assert out["EV-EMB"]["clock"] == list(telemetry_ev.EV_CLOCK["EV-EMB"])
    assert all(r["site_code"] == "EV-RUI" for r in out["EV-RUI"]["roster"])
    assert {t["kind"] for t in out["EV-EMB"]["tariffs"]} == {"TARIFF_SCHEDULE"}
