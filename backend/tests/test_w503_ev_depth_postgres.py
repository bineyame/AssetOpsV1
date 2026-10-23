"""W5-03a E1b: the selected EV Availability, Energy and Health depth API (`ev-depth-1`).

Pure tests cover the projections and the gate with a fake reader; the persisted tests replay W2-05b's registered
`Chain` through `ev_depth_cases.py` on a private `*_test` database (window `[08:00, 09:00)`).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from assetops_backend.analytics.ev_depth import (
    ENERGY_KEYS,
    health,
    import_samples,
    peak_below_limit,
    peak_sample_at,
)
from assetops_backend.ev_depth_api import build_ev_depth_router
from ev_depth_cases import HI, HISTORICAL_KNOWN_AT, LO, QUERY, URL, chain, pending, settled  # noqa: F401

needs_db = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

CODE = "EV-LAB-001"
TOP = ["schema_version", "site_id", "window", "selection"]
WINDOW = ["from", "to", "known_at", "committed_watermark"]
SELECTION = ["state", "assessment_revision_id", "session_revision_ids", "accepted_evidence_ids", "source_provenance"]
LINKS = ["sessions", "evidence_analysis", "financials"]
HEALTH = ["foundation_revision_id", "rows", "battery"]
HEALTH_ROW = ["kind", "label", "asset_id", "asset_code", "condition_state", "observation", "limitation",
              "next_evidence", "session_id", "evidence_ids"]
T, S = UUID(int=1), UUID(int=2)


# --- pure -------------------------------------------------------------------------------------------------


def _imp(n: int, minute: int, value: str, *, quality="GOOD", use=None, unit="kW", length=5) -> dict:
    end = LO + timedelta(minutes=minute)
    return {"evidence_id": f"00000000-0000-4000-8000-{n:012x}", "role": "ev_site_import", "value": value,
            "unit": unit, "quality": quality, "use": use, "measurement": "INTERVAL_MEAN", "source_time": end,
            "interval_start": end - timedelta(minutes=length), "interval_end": end}


def test_import_samples_peak_and_limit() -> None:
    rows = [_imp(3, 15, "60"), _imp(1, 15, "60"), _imp(2, 10, "0.5"), _imp(4, 20, "70", quality="SUSPECT"),
            _imp(5, 25, "80", use="EXCLUDED"), _imp(6, 30, "90", unit="W"), _imp(7, 35, "-1"), _imp(8, 40, "NaN"),
            _imp(9, 65, "99"), _imp(10, 45, "99"), _imp(1, 15, "60")]
    selected = {"selected": {"evidence_ids": [r["evidence_id"] for r in rows if r["evidence_id"][-2:] != "0a"]},
                "lo": LO, "hi": HI}
    samples = import_samples(rows, selected)
    # Equal-time samples stay separate; only an identical evidence ID is deduplicated; an unselected row is dropped.
    assert samples == [
        {"source_time": "2026-10-06T08:10:00.000000Z", "import_kw": "0.5", "evidence_id": rows[2]["evidence_id"]},
        {"source_time": "2026-10-06T08:15:00.000000Z", "import_kw": "60", "evidence_id": rows[1]["evidence_id"]},
        {"source_time": "2026-10-06T08:15:00.000000Z", "import_kw": "60", "evidence_id": rows[0]["evidence_id"]}]
    assert peak_sample_at(samples) == "2026-10-06T08:15:00.000000Z" and peak_sample_at([]) is None
    assert import_samples(rows, {"selected": None, "lo": LO, "hi": HI}) == []
    assert [peak_below_limit(*x) for x in (("60", "80"), ("80", "80"), ("81", "80"), (None, "80"), ("1", None))] \
        == ["YES", "NO", "NO", "UNKNOWN", "UNKNOWN"]


def _foundation(meter_fed_by_bus: bool = True) -> dict:
    components = [{"component_id": "feed-1", "component_type": "AC_BUS"},
                  {"component_id": "site-meter-1", "component_type": "METER", "display_name": "Site import meter"},
                  {"component_id": "c2-meter", "component_type": "METER"},
                  {"component_id": "charger-1", "component_type": "EV_CHARGER"},
                  {"component_id": "c2", "component_type": "EV_CONNECTOR", "display_name": "Connector c2"},
                  {"component_id": "c1", "component_type": "EV_CONNECTOR"},
                  {"component_id": "c3", "component_type": "EV_CONNECTOR"}]
    nodes = [{"node_id": "n-feed", "component_id": "feed-1", "node_role": "BUS" if meter_fed_by_bus else "CHARGER"},
             {"node_id": "n-meter", "component_id": "site-meter-1", "node_role": "METERING"},
             {"node_id": "n-c2m", "component_id": "c2-meter", "node_role": "METERING"},
             {"node_id": "n-charger", "component_id": "charger-1", "node_role": "CHARGER"}]
    connections = [{"from_node": "n-feed", "to_node": "n-meter"}, {"from_node": "n-charger", "to_node": "n-c2m"}]
    return {"id": "f-9", "content": {"components": components, "topology": {"nodes": nodes,
                                                                          "connections": connections}}}


ASSETS = {"c1": "a-c1", "c2": "a-c2", "site-meter-1": "a-m", "c2-meter": "a-c2m", "feed-1": "a-f",
          "charger-1": "a-ch"}


def test_health_rows_battery_and_meter_role() -> None:
    sessions = [{"session_id": "s-2", "connector_asset_id": "a-c2", "fault_evidence_id": "e-2",
                 "start_at": "2026-10-06T08:11:00.000000Z"},
                {"session_id": "s-1", "connector_asset_id": "a-c2", "fault_evidence_id": "e-1",
                 "start_at": "2026-10-06T08:11:00.000000Z"},
                {"session_id": "s-3", "connector_asset_id": "a-c1", "fault_evidence_id": None,
                 "start_at": "2026-10-06T08:01:00.000000Z"}]
    body = health(_foundation(), ASSETS, sessions, ["i-1", "i-2"])
    assert list(body) == HEALTH and body["foundation_revision_id"] == "f-9"
    assert body["battery"] == {"condition_state": "UNKNOWN",
                               "limitation": "Battery configuration is not established by this Foundation."}
    assert all(list(r) == HEALTH_ROW for r in body["rows"])
    # c3 has no scoped asset: no row. Connectors by asset_code, then meters by asset_code.
    assert [(r["kind"], r["asset_code"], r["label"]) for r in body["rows"]] == [
        ("CONNECTOR", "c1", "c1"), ("CONNECTOR", "c2", "Connector c2"), ("UNKNOWN", "c2-meter", "c2-meter"),
        ("SITE_METER", "site-meter-1", "Site import meter")]
    c1, c2, c2m, meter = body["rows"]
    assert (c1["condition_state"], c1["observation"], c1["session_id"], c1["evidence_ids"]) == (
        "UNKNOWN", "Condition unknown", None, [])
    assert (c2["condition_state"], c2["observation"], c2["limitation"], c2["next_evidence"], c2["session_id"],
            c2["evidence_ids"]) == ("NEEDS_INVESTIGATION", "Session interruption observed",
                                    "Fault-stopped session observed; cause not diagnosed",
                                    "Retrieve diagnostic log and witness a complete session", "s-1", ["e-1", "e-2"])
    assert (c2m["observation"], c2m["limitation"]) == ("Meter role not established",
                                                       "No selected Site-import binding for this meter")
    assert (meter["observation"], meter["limitation"], meter["evidence_ids"]) == ("Sampled import only", None,
                                                                                  ["i-1", "i-2"])
    assert {r["condition_state"] for r in body["rows"]} <= {"UNKNOWN", "NEEDS_INVESTIGATION"}
    # Without a BUS-fed meter node the Site meter role is not established.
    assert [r["kind"] for r in health(_foundation(False), ASSETS, [], [])["rows"]][2:] == ["UNKNOWN", "UNKNOWN"]
    assert health(None, ASSETS, sessions, ["i-1"]) == {"foundation_revision_id": None, "rows": [],
                                                       "battery": body["battery"]}


class _FakeReads:
    def __init__(self) -> None:
        self.calls = []

    def availability(self, *args):
        self.calls.append(args)
        return {"ok": True}

    energy = health = availability


def _gate_client(*, site_type="EV_CHARGING", access=None, reads="fake") -> tuple[TestClient, _FakeReads]:
    fake = _FakeReads()
    site = SimpleNamespace(id=S, site_type=site_type)
    registry = SimpleNamespace(imported=lambda code: site if code == CODE else None,
                               tenant=lambda: SimpleNamespace(id=T))
    app = FastAPI()
    kw = {} if access is None else {"access": access}
    app.include_router(build_ev_depth_router(registry, fake if reads == "fake" else None, **kw))
    return TestClient(app), fake


def _code(c: TestClient, path: str, status: int) -> str:
    response = c.get(path)
    assert response.status_code == status, response.text
    body = response.json()
    assert set(body) == {"error"} and set(body["error"]) == {"code", "message"}
    return body["error"]["code"]


@pytest.mark.parametrize("route", ["availability", "energy", "health"])
def test_gate_refusals_without_database(route) -> None:
    base = f"/api/sites/{CODE}/ev/{route}"
    c, fake = _gate_client()
    assert c.get(f"{base}?{QUERY}").json() == {"ok": True}
    assert fake.calls == [(T, S, CODE, LO, HI, None)]
    assert _code(c, f"{base}?{QUERY}&from=2026-10-06T08:00:00Z", 422) == "EV_PARAMETER_UNKNOWN"
    assert _code(c, f"{base}?{QUERY}&cursor=x", 422) == "EV_PARAMETER_UNKNOWN"
    assert _code(c, f"{base}?from=2026-10-06T08:00:00Z", 422) == "EV_WINDOW_INVALID"
    assert _code(c, f"{base}?from=2026-10-06T09:00:00Z&to=2026-10-06T08:00:00Z", 422) == "EV_WINDOW_INVALID"
    assert _code(c, f"{base}?from=2026-10-01T00:00:00Z&to=2026-11-02T00:00:00Z", 422) == "EV_WINDOW_TOO_LONG"
    assert _code(c, f"{base}?from=nope&to=2026-10-06T08:00:00Z", 422) == "EV_TIME_INVALID"
    assert _code(c, f"/api/sites/NOPE/ev/{route}", 404) == "SITE_NOT_FOUND"
    assert _code(_gate_client(site_type="COLDCHAIN")[0], base, 404) == "SITE_NOT_FOUND"
    assert _code(_gate_client(access=lambda r, s: 401)[0], f"/api/sites/NOPE/ev/{route}", 401) == "UNAUTHENTICATED"
    assert _code(_gate_client(access=lambda r, s: 403)[0], base, 403) == "SITE_SCOPE_FORBIDDEN"
    assert _code(_gate_client(reads=None)[0], base, 503) == "EV_READ_UNAVAILABLE"


def test_main_mounts_the_three_depth_routes() -> None:
    from assetops_backend.main import create_app

    c = TestClient(create_app())
    for route in ("availability", "energy", "health"):
        # Mounted: the gate answers with its typed wrapper, never the framework's unknown-route 404.
        body = c.get(f"/api/sites/{CODE}/ev/{route}?{QUERY}").json()
        assert set(body) == {"error"}, (route, body)


# --- persisted -------------------------------------------------------------------------------------------


def _client(built, access=None) -> TestClient:
    from assetops_backend.financials.composition import build_ev_depth_read_service

    site = SimpleNamespace(id=built.site_id, site_type="EV_CHARGING")
    registry = SimpleNamespace(imported=lambda code: site if code == CODE else None,
                               tenant=lambda: SimpleNamespace(id=built.tenant_id))
    app = FastAPI()
    kw = {} if access is None else {"access": access}
    app.include_router(build_ev_depth_router(registry, build_ev_depth_read_service(URL), **kw))
    return TestClient(app)


def _get(c: TestClient, route: str, query: str = QUERY) -> dict:
    response = c.get(f"/api/sites/{CODE}/ev/{route}?{query}")
    assert response.status_code == 200, response.text
    return response.json()


def _envelope(body: dict, key: str) -> None:
    assert list(body) == TOP + [key, "links"]
    assert body["schema_version"] == "ev-depth-1"
    assert list(body["window"]) == WINDOW and list(body["selection"]) == SELECTION and list(body["links"]) == LINKS


def _snapshot(built, known_at=None) -> tuple[dict, dict, list, list]:
    from assetops_backend.analytics.composition import build_ev_read_service

    reads = build_ev_read_service(URL)
    try:
        def work(c):
            snap, body = reads.open_on(c, built.tenant_id, built.site_id, CODE, LO, HI, known_at)
            return snap, body, reads.accepted_on(c, snap), reads.sessions_on(c, snap)
        return reads.within(work)
    finally:
        reads.dispose()


@needs_db
def test_energy_health_selected_snapshot(chain) -> None:  # noqa: F811
    built = settled(chain, "fault")
    c = _client(built)
    snap, body, accepted, sessions = _snapshot(built)
    sel = snap["selected"]
    for key in ("availability", "energy", "health"):
        read = _get(c, key)
        _envelope(read, key)
        assert read["window"] == {**{k: body["window"][k] for k in ("from", "to", "known_at")},
                                  "committed_watermark": "2026-10-06T09:00:00.000000Z"}
        assert read["selection"]["state"] == "CURRENT"
        assert read["selection"]["assessment_revision_id"] == str(sel["revision_id"]).lower()
        assert read["selection"]["accepted_evidence_ids"] == sel["evidence_ids"]
        assert read["selection"]["session_revision_ids"] == sorted(
            str(x).lower() for x in sel["result"]["session_revision_ids"])
        assert read["selection"]["source_provenance"] == body["selected_source_provenance"]
    energy = _get(c, "energy")["energy"]
    assert list(energy) == list(ENERGY_KEYS)
    imports = [r for r in accepted if r["role"] == "ev_site_import" and r["evidence_id"] in sel["evidence_ids"]]
    assert energy["import_sample_count"] == len(energy["import_samples"]) == len(imports) > 0
    assert all(list(x) == ["source_time", "import_kw", "evidence_id"] for x in energy["import_samples"])
    assert energy["import_samples"] == sorted(energy["import_samples"], key=lambda x: (x["source_time"],
                                                                                       x["evidence_id"]))
    assert energy["configured_import_limit_kw"] == "80" and energy["power_constraint_state"] == "UNKNOWN"
    assert energy["peak_below_limit"] == "YES" and energy["observed_peak_import_kw"] is not None
    peak = max(energy["import_samples"], key=lambda x: float(x["import_kw"]))
    assert energy["peak_sample_at"] == peak["source_time"]
    h = _get(c, "health")["health"]
    assert list(h) == HEALTH and h["foundation_revision_id"] == str(sel["foundation_ids"][0]).lower()
    assert [(r["kind"], r["asset_code"]) for r in h["rows"]] == [("CONNECTOR", "c1"), ("CONNECTOR", "c2"),
                                                                 ("SITE_METER", "site-meter-1")]
    assert all(list(r) == HEALTH_ROW for r in h["rows"])
    faulted = [x for x in sessions if x["fault_evidence_id"] is not None]
    by_code = {r["asset_code"]: r for r in h["rows"]}
    for code in ("c1", "c2"):
        mine = [x for x in faulted if x["connector_asset_id"] == by_code[code]["asset_id"]]
        assert by_code[code]["condition_state"] == ("NEEDS_INVESTIGATION" if mine else "UNKNOWN")
        assert by_code[code]["evidence_ids"] == sorted({x["fault_evidence_id"] for x in mine})
    assert by_code["site-meter-1"]["evidence_ids"] == sorted(x["evidence_id"] for x in imports)
    assert h["battery"]["condition_state"] == "UNKNOWN"


@needs_db
def test_energy_baseline_rows(chain) -> None:  # noqa: F811
    from assetops_backend.financials.composition import build_ev_site_read_service

    complete = settled(chain, "complete")
    energy = _get(_client(complete), "energy")["energy"]
    overview = build_ev_site_read_service(URL).overview(complete.tenant_id, complete.site_id, CODE, LO, HI, None)
    assert energy["metered_complete_kwh"] == overview["energy"]["complete_kwh"] == "30.000"
    assert energy["partial_kwh"] == overview["energy"]["partial_kwh"]
    assert energy["unknown_seconds"] == overview["energy"]["unknown_seconds"] == 0
    assert energy["observed_peak_import_kw"] == overview["site_power"]["observed_peak_kw"]
    assert energy["configured_import_limit_kw"] == overview["site_power"]["configured_limit_kw"]
    money = energy["consequence"]
    assert money is None or money["state"] in ("ESTIMATED", "UNPRICED", "WITHHELD")
    complete.close()


@needs_db
def test_partial_energy_and_pending_selection(chain) -> None:  # noqa: F811
    partial = settled(chain, "missing-meter")
    energy = _get(_client(partial), "energy")["energy"]
    assert energy["metered_complete_kwh"] is None and energy["partial_kwh"] == "25.000"
    assert energy["unknown_seconds"] == 300
    partial.close()
    late = pending(chain)
    snap, body, _, _ = _snapshot(late)
    read = _get(_client(late), "availability")
    assert read["selection"]["state"] == "PENDING_RECOMPUTE"
    assert read["window"]["committed_watermark"] == "2026-10-06T09:05:00.000000Z"
    # The selected block, never the pending alias.
    assert read["selection"]["source_provenance"] == body["selected_source_provenance"]
    assert read["selection"]["source_provenance"] != body["pending_source_provenance"]
    old = _get(_client(late), "availability", f"{QUERY}&known_at={HISTORICAL_KNOWN_AT}")
    assert old["selection"]["state"] == "HISTORICAL"


@needs_db
def test_router_refusals_and_links(chain) -> None:  # noqa: F811
    built = settled(chain, "complete")
    c = _client(built)
    read = _get(c, "availability")
    w = read["window"]
    q = f"?from={w['from']}&to={w['to']}&known_at={w['known_at']}"
    assert read["links"] == {"sessions": f"/api/sites/{CODE}/ev/sessions{q}",
                             "evidence_analysis": f"/api/sites/{CODE}/ev/evidence/analysis{q}",
                             "financials": f"/api/sites/{CODE}/ev/financials{q}"}
    assert _code(c, f"/api/sites/{CODE}/ev/energy?from=2026-10-06T09:00:00Z&to=2026-10-06T08:00:00Z", 422) \
        == "EV_WINDOW_INVALID"
    assert _code(c, f"/api/sites/{CODE}/ev/health?{QUERY}&known_at=2026-10-07T00:00:00Z", 422) == "EV_TIME_INVALID"
    assert _code(_client(built, access=lambda r, s: 403), f"/api/sites/{CODE}/ev/health?{QUERY}", 403) \
        == "SITE_SCOPE_FORBIDDEN"
    # An unselected window: every count null, never zero, and no selected IDs.
    other = _get(c, "availability", "from=2026-10-06T09:00:00Z&to=2026-10-06T10:00:00Z")
    assert other["selection"]["state"] == "UNKNOWN" and other["selection"]["accepted_evidence_ids"] == []
    assert other["availability"]["schedule_state"] == "NOT_ESTABLISHED"
    assert other["availability"]["scheduled_seconds"] is None
    assert _get(c, "energy", "from=2026-10-06T09:00:00Z&to=2026-10-06T10:00:00Z")["energy"]["import_samples"] == []


def test_window_constants() -> None:
    assert LO == datetime(2026, 10, 6, 8, tzinfo=timezone.utc) and HI - LO == timedelta(hours=1)
