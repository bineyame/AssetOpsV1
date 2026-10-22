"""W5-01 C1: the extracted cold Site gate and the cold depth route without a database
(`.agent/W5-01-build-spec.md` "Shared selected read and guards", "C1").

The gate is `cold_site_api.build_cold_gate`, shared unchanged by the W2-04 Site reads and `/cold/cooling`. The
pure `ColdDepthReadService` composition is driven by an in-memory snapshot to prove the `cold-depth-1` envelope,
Site-code API links and that a selected step whose evidence ID is not an accepted record is never shown.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from assetops_backend.analytics import cold
from assetops_backend.analytics.cold_depth import (
    CONTEXT_ROWS,
    HEALTH_ROW_KEYS,
    ColdDepthReadService,
    door_pairs,
    health_rows,
)
from assetops_backend.analytics.cold_site_reads import cooling_response_state
from assetops_backend.analytics.cold_reads import ColdReadUnavailable
from assetops_backend.cold_depth_api import build_cold_depth_router
from assetops_backend.cold_site_api import build_cold_gate, build_cold_site_router

CODE = "COLD-READ"
W = "from=2026-10-06T19:00:00Z&to=2026-10-06T20:05:00Z"
LO = datetime(2026, 10, 6, 19, tzinfo=timezone.utc)
HI = datetime(2026, 10, 6, 20, 5, tzinfo=timezone.utc)
MARK = datetime(2026, 10, 22, 8, 30, 1, 123456, tzinfo=timezone.utc)


def _registry(site_type="COLDCHAIN"):
    site = SimpleNamespace(id=uuid4(), site_type=site_type)
    return SimpleNamespace(imported=lambda code: site if code == CODE else None,
                           tenant=lambda: SimpleNamespace(id=uuid4()))


class _Echo:
    def cooling(self, t, s, code, lo, hi, known_at):
        return {"route": "cooling", "code": code, "args": [str(x) for x in (lo, hi, known_at)]}

    def health(self, t, s, code, lo, hi, known_at):
        return {"route": "health", "code": code, "args": [str(x) for x in (lo, hi, known_at)]}


def depth_client(*, access=None, disclosure=None, site_type="COLDCHAIN", reads=_Echo()) -> TestClient:
    kw = {k: v for k, v in (("access", access), ("disclosure", disclosure)) if v is not None}
    app = FastAPI()
    app.include_router(build_cold_depth_router(_registry(site_type), reads, **kw))
    return TestClient(app)


def error(c: TestClient, path: str, status: int) -> str:
    response = c.get(f"/api/sites/{CODE}/cold/{path}" if not path.startswith("/") else path)
    assert response.status_code == status, response.text
    body = response.json()
    assert set(body) == {"error"} and set(body["error"]) == {"code", "message"}, body
    return body["error"]["code"]


def test_cold_depth_gate_and_links() -> None:
    c = depth_client()
    body = c.get(f"/api/sites/{CODE}/cold/cooling?{W}&known_at=2026-10-06T20:05:00.123456Z").json()
    assert body == {"route": "cooling", "code": CODE,
                    "args": [str(LO), str(HI), "2026-10-06 20:05:00.123456+00:00"]}
    assert c.get(f"/api/sites/{CODE}/cold/cooling").json()["args"] == ["None", "None", "None"]
    assert c.get(f"/api/sites/{CODE}/cold/health?{W}").json() == {"route": "health", "code": CODE,
                                                                   "args": [str(LO), str(HI), "None"]}
    assert error(c, f"health?{W}&cursor=x", 422) == "COLD_PARAMETER_UNKNOWN"
    assert error(depth_client(reads=None), f"health?{W}", 503) == "COLD_READ_UNAVAILABLE"
    # The copied refusal order and codes: scope before lookup, then parameters, window, Site, store, disclosure.
    assert error(depth_client(access=lambda r, code: 401), f"cooling?{W}", 401) == "UNAUTHENTICATED"
    assert error(depth_client(access=lambda r, code: 403), "/api/sites/OTHER/cold/cooling", 403) == \
        "SITE_SCOPE_FORBIDDEN"
    assert error(c, f"cooling?{W}&cursor=x", 422) == "COLD_PARAMETER_UNKNOWN"
    assert error(c, f"cooling?{W}&limit=5", 422) == "COLD_PARAMETER_UNKNOWN"
    assert error(c, "cooling?from=2026-10-06T19:00:00Z", 422) == "COLD_WINDOW_INVALID"
    assert error(c, "cooling?from=2026-10-06T20:00:00Z&to=2026-10-06T19:00:00Z", 422) == "COLD_WINDOW_INVALID"
    assert error(c, "cooling?from=2026-10-06T19:00:00Z&to=2026-10-06T19:00:00Z", 422) == "COLD_WINDOW_INVALID"
    assert error(c, "cooling?from=2026-09-01T00:00:00Z&to=2026-10-06T00:00:00Z", 422) == "COLD_WINDOW_TOO_LONG"
    assert error(c, f"cooling?{W}&known_at=2026-10-06T20:05:00", 422) == "COLD_TIME_INVALID"
    assert error(c, f"cooling?{W}&known_at=2026-10-06T20:05:00.1234567Z", 422) == "COLD_TIME_INVALID"
    assert error(c, f"cooling?{W}&known_at=2026-10-06T23:05:00%2B03:00", 422) == "COLD_TIME_INVALID"
    assert error(depth_client(site_type="MINIGRID"), f"cooling?{W}", 404) == "SITE_NOT_FOUND"
    assert error(c, f"/api/sites/OTHER/cold/cooling?{W}", 404) == "SITE_NOT_FOUND"
    assert error(depth_client(reads=None), f"cooling?{W}", 503) == "COLD_READ_UNAVAILABLE"
    assert error(depth_client(disclosure=lambda code, t, s: False), f"cooling?{W}", 403) == \
        "COLD_SOURCE_DISCLOSURE_FORBIDDEN"

    class _Down:
        def cooling(self, *a):
            raise ColdReadUnavailable("store down")
    assert error(depth_client(reads=_Down()), f"cooling?{W}", 503) == "COLD_READ_UNAVAILABLE"
    # No cursor, so no 409 route exists: an unknown sub-path is not served.
    assert c.get(f"/api/sites/{CODE}/cold/cooling/x?{W}").status_code == 404

    # The W2-04 router uses the same importable gate (same refusal for the same request).
    w2 = FastAPI()
    w2.include_router(build_cold_site_router(_registry(), None))
    assert error(TestClient(w2), f"overview?{W}", 503) == "COLD_READ_UNAVAILABLE"
    assert callable(build_cold_gate(_registry(), None))

    # Pure composition: envelope, Site-code links preserving from/to/known_at, exact selected IDs.
    body = ColdDepthReadService(_Reads(_snap())).cooling(T, S, "COLD READ/1", LO, HI, None)
    assert list(body) == ["schema_version", "site_id", "window", "selection", "cooling", "links"]
    assert body["schema_version"] == "cold-depth-1" and body["site_id"] == str(S)
    assert body["window"] == {"from": "2026-10-06T19:00:00.000000Z", "to": "2026-10-06T20:05:00.000000Z",
                              "known_at": cold.plain(MARK), "committed_watermark": cold.plain(MARK)}
    assert body["selection"]["state"] == "CURRENT"
    assert body["selection"]["assessment_revision_ids"] == sorted([str(REV_START), str(REV_EXC)])
    assert body["selection"]["accepted_evidence_ids"] == sorted(str(e) for e in ALL_IDS)
    assert body["selection"]["source_provenance"] == {"classification": "REGISTERED_SIMULATION"}
    query = "?from=2026-10-06T19%3A00%3A00.000000Z&to=2026-10-06T20%3A05%3A00.000000Z&known_at=" + \
        cold.plain(MARK).replace(":", "%3A")
    assert body["links"] == {"temperature": "/api/sites/COLD%20READ%2F1/cold/temperature" + query,
                             "backup": "/api/sites/COLD%20READ%2F1/cold/backup-chain" + query,
                             "evidence": "/api/sites/COLD%20READ%2F1/cold/evidence" + query,
                             "health": "/api/sites/COLD%20READ%2F1/cold/health" + query}
    cooling = body["cooling"]
    assert list(cooling) == ["recovery_state", "policy_high_deg_c", "selected_points", "observed_restart_at",
                             "observed_return_to_policy_at", "duration_lower_seconds", "duration_upper_seconds",
                             "comparison_state", "context"]
    assert cooling["policy_high_deg_c"] == "4"
    assert all(list(r) == ["label", "state", "evidence_ids", "duration_seconds"] for r in cooling["context"])
    # A selected COMPRESSOR step whose evidence ID is not an accepted record (missing selected ID) is not shown.
    assert cooling["selected_points"] == [
        {"role": cold.PROBE_ROLE, "source_time": "2026-10-06T19:25:00.000000Z", "evidence_ids": [str(PROBE)]}]
    assert cooling["recovery_state"] == "LIMITED" and cooling["comparison_state"] == "CONTEXT_MISSING"
    assert [cooling[k] for k in ("observed_restart_at", "observed_return_to_policy_at", "duration_lower_seconds",
                                 "duration_upper_seconds")] == [None, None, None, None]
    assert [r["label"] for r in cooling["context"]] == list(CONTEXT_ROWS)
    # A lone DOOR_OPEN is no pair: the door row stays Unknown; power is Observed from the selected grid row.
    states = {r["label"]: (r["state"], r["evidence_ids"], r["duration_seconds"]) for r in cooling["context"]}
    assert states["Door-open duration"] == ("Unknown", [], None)
    assert states["Power availability"] == ("Observed", [str(GRID)], None)
    assert all(states[k] == ("Unknown", [], None) for k in ("Ambient temperature", "Loading / batch", "Defrost"))
    # No selection: UNKNOWN recovery, empty arrays, null values; the envelope is still served.
    empty = ColdDepthReadService(_Reads(_snap(selected=False))).cooling(T, S, CODE, LO, HI, None)
    assert empty["selection"]["assessment_revision_ids"] == [] and empty["selection"]["accepted_evidence_ids"] == []
    assert empty["cooling"]["recovery_state"] == "UNKNOWN" and empty["cooling"]["selected_points"] == []
    assert empty["cooling"]["policy_high_deg_c"] is None
    assert all(r["state"] == "Unknown" for r in empty["cooling"]["context"])


def test_door_pairs() -> None:
    def row(kind, minute, second=0):
        return {"id": uuid4(), "record_kind": kind,
                "source_time": datetime(2026, 10, 6, 19, minute, second, tzinfo=timezone.utc)}
    o, cl = row("DOOR_OPEN", 10), row("DOOR_CLOSE", 11)
    assert door_pairs([cl, o]) == (sorted([str(o["id"]), str(cl["id"])]), 60)
    assert door_pairs([o]) == ([], None) and door_pairs([cl]) == ([], None) and door_pairs([]) == ([], None)
    assert door_pairs([row("DOOR_CLOSE", 10), row("DOOR_OPEN", 11)]) == ([], None)  # close before open
    same = row("DOOR_CLOSE", 10)
    assert door_pairs([o, same]) == ([], None)  # zero elapsed is not a positive duration
    # Q8: a zero-elapsed CLOSE is skipped and keeps the held OPEN.
    late = row("DOOR_CLOSE", 11)
    assert door_pairs([o, same, late]) == (sorted([str(o["id"]), str(late["id"])]), 60)
    # A further OPEN while one is held is ignored.
    again = row("DOOR_OPEN", 10, 30)
    assert door_pairs([o, again, late]) == (sorted([str(o["id"]), str(late["id"])]), 60)
    # Several matched pairs: one sum, all paired IDs sorted.
    o2, c2 = row("DOOR_OPEN", 20), row("DOOR_CLOSE", 20, 30)
    assert door_pairs([o, late, o2, c2]) == (sorted(str(r["id"]) for r in (o, late, o2, c2)), 90)


def test_cooling_response_state() -> None:
    assert cooling_response_state(None) == "UNAVAILABLE"
    limited = SimpleNamespace(result={"chains": [{"result": "OBSERVED_FAILURE",
                                                  "steps": [{"step": "GRID", "state": "OBSERVED"}]}]})
    assert cooling_response_state(limited) == "LIMITED"
    contradictory = SimpleNamespace(result={"chains": [{"result": "OBSERVED_FAILURE", "steps": [
        {"step": "GRID", "state": "OBSERVED"}, {"step": "START_RESULT", "state": "CONTRADICTORY"}]}]})
    assert cooling_response_state(contradictory) == "CONTRADICTORY"
    assert cooling_response_state(SimpleNamespace(result={"chains": []})) == "UNAVAILABLE"


# --- in-memory snapshot --------------------------------------------------------------------------------------

T, S = uuid4(), uuid4()
REV_EXC, REV_START = uuid4(), uuid4()
PROBE, COMPRESSOR_MISSING, GRID, DOOR = uuid4(), uuid4(), uuid4(), uuid4()
ALL_IDS = sorted([PROBE, COMPRESSOR_MISSING, GRID, DOOR], key=str)


def _snap(selected=True):
    steps = [{"step": "GRID", "state": "OBSERVED", "at": "2026-10-06T19:00:00.000000Z", "evidence_ids": [str(GRID)]},
             {"step": "COMPRESSOR", "state": "OBSERVED", "at": "2026-10-06T19:20:00.000000Z",
              "evidence_ids": [str(COMPRESSOR_MISSING)]},
             {"step": "PROBE", "state": "OBSERVED", "at": "2026-10-06T19:25:00.000000Z",
              "evidence_ids": [str(PROBE)]}]
    chosen = {}
    if selected:
        ids = [str(e) for e in ALL_IDS]
        chosen = {cold.EXCURSION_ANALYTIC: SimpleNamespace(revision_id=REV_EXC, result={"policy": {"policy_high": "4"}},
                                                           evidence_ids=ids),
                  cold.START_RESPONSE_ANALYTIC: SimpleNamespace(
                      revision_id=REV_START, evidence_ids=ids,
                      result={"chains": [{"result": "OBSERVED_FAILURE", "steps": steps}]})}
    return {"code": None, "t": T, "s": S, "lo": LO, "hi": HI, "known": MARK, "watermark": MARK,
            "selected": chosen, "state": "CURRENT" if selected else "UNKNOWN"}


class _Reads:
    def __init__(self, snap):
        self.snap = snap

    def within(self, work):
        return work("connection")

    def selection_on(self, c, t, s, code, lo, hi, known_at):
        return {**self.snap, "code": code}

    def envelope_on(self, c, snap, analytics):
        return {"source_provenance": {"classification": "REGISTERED_SIMULATION"}}

    def accepted_on(self, c, t, s, ids, *a):
        held = {str(PROBE): cold.PROBE_ROLE, str(GRID): cold.GRID_EVENT_ROLE, str(DOOR): cold.DOOR_ROLE}
        kinds = {str(DOOR): "DOOR_OPEN"}
        return [{"id": i, "role": held[i], "record_kind": kinds.get(i),
                 "source_time": datetime(2026, 10, 6, 19, 10, tzinfo=timezone.utc)} for i in ids if i in held]

    def foundation_on(self, c, snap):
        return None


# --- pure Health rows (C1 Health literal table) ----------------------------------------------------------------

GEN_A, GEN_B, COMP_A, PROBE_A = (str(uuid4()) for _ in range(4))
SRC_1, SRC_2 = uuid4(), uuid4()
LINKS = {"temperature": "/t", "backup": "/b", "evidence": "/e", "health": "/h"}


def _asset(asset_id, kind, code):
    return {"component_type": kind, "asset_id": asset_id, "asset_code": code, "display_name": None}


def _foundation(*components):
    return {"revision_id": str(uuid4()), "components": list(components)}


FULL = _foundation(_asset(GEN_A, "GENERATOR", "GEN-1"), _asset(COMP_A, "COMPRESSOR", "CMP-1"),
                   _asset(PROBE_A, "TEMPERATURE_PROBE", "PRB-1"))


def _ev(role, source=SRC_1):
    return {"id": uuid4(), "role": role, "source_id": source}


def _health(chains=None, start_policy=None, exc_links=None, exc_policy=None, accepted=(), foundation=FULL):
    selected = {}
    if chains is not None:
        selected[cold.START_RESPONSE_ANALYTIC] = SimpleNamespace(result={"chains": chains,
                                                                         "policy": start_policy or {}})
    if exc_links is not None or exc_policy is not None:
        selected[cold.EXCURSION_ANALYTIC] = SimpleNamespace(result={"links": exc_links or [],
                                                                    "policy": exc_policy or {}})
    snap = {"code": "COLD READ/1", "lo": LO, "hi": HI, "known": MARK, "selected": selected}
    return {r["kind"]: r for r in health_rows(snap, list(accepted), foundation, LINKS)}, \
        health_rows(snap, list(accepted), foundation, LINKS)


def _chain(result, *steps):
    return {"result": result, "steps": [{"step": n, "state": st, "evidence_ids": [str(e["id"]) for e in evs]}
                                        for n, st, evs in steps]}


def _cell(row):
    return (row["condition_state"], row["observation"], row["limitation"], row["evidence_ids"])


def test_health_rows() -> None:
    req, res, gen = _ev(cold.START_ROLE), _ev(cold.START_ROLE), _ev(cold.GENERATOR_STATE_ROLE)
    ghost = {"id": uuid4()}  # cited by a step, absent from the ledger
    failure = _chain("OBSERVED_FAILURE", ("START_REQUEST", "OBSERVED", [req]), ("START_RESULT", "OBSERVED", [res]),
                     ("GENERATOR", "OBSERVED", [gen]))
    # Exact row order and key order.
    by_kind, rows = _health(chains=[failure], accepted=[req, res, gen])
    assert [r["kind"] for r in rows] == ["BACKUP_GENERATOR", "COOLING_PLANT", "TEMPERATURE_SENSING"]
    assert [r["label"] for r in rows] == ["Backup generator", "Cooling plant", "Temperature sensing"]
    assert all(tuple(r) == HEALTH_ROW_KEYS for r in rows)
    assert [r["next_evidence"] for r in rows] == ["Witness an automatic-start test",
                                                  "Record matched loading, door and ambient context",
                                                  "Add calibrated spatial coverage"]
    query = "?from=2026-10-06T19%3A00%3A00.000000Z&to=2026-10-06T20%3A05%3A00.000000Z&known_at=" + \
        cold.plain(MARK).replace(":", "%3A")
    assert [r["link"] for r in rows] == ["/b", "/api/sites/COLD%20READ%2F1/cold/cooling" + query, "/e"]
    assert by_kind["BACKUP_GENERATOR"]["assets"] == [{"asset_id": GEN_A, "asset_code": "GEN-1", "display_name": None}]

    # Generator 1: Foundation resolved without a generator -> NOT_CONFIGURED, null asset and link.
    bare = _foundation(_asset(COMP_A, "COMPRESSOR", "CMP-1"), _asset(PROBE_A, "TEMPERATURE_PROBE", "PRB-1"))
    g = _health(chains=[failure], accepted=[req, res, gen], foundation=bare)[0]["BACKUP_GENERATOR"]
    assert _cell(g) == ("NOT_CONFIGURED", "Not configured",
                        "No backup generator is declared in the selected Foundation", [])
    assert (g["asset_id"], g["assets"], g["link"]) == (None, [], None)
    # Generator 2: contradictory beats failure; IDs of every START_RESULT step, ledger-present only.
    conflict = _chain("CONTRADICTORY", ("START_RESULT", "CONTRADICTORY", [res, ghost]))
    g = _health(chains=[failure, conflict], accepted=[req, res, gen])[0]["BACKUP_GENERATOR"]
    assert _cell(g) == ("UNKNOWN", "Start results conflict",
                        "Selected start results conflict; no condition is assessed", [str(res["id"])])
    step_conflict = _chain("OBSERVED_FAILURE", ("START_REQUEST", "OBSERVED", [req]),
                           ("START_RESULT", "CONTRADICTORY", [res]))
    assert _health(chains=[step_conflict], accepted=[req, res])[0]["BACKUP_GENERATOR"]["observation"] == \
        "Start results conflict"
    # Generator 3: failure, with the policy generator asset.
    g = _health(chains=[failure], start_policy={"generator_asset_id": GEN_A.upper()},
                accepted=[req, res, gen])[0]["BACKUP_GENERATOR"]
    assert _cell(g) == ("NEEDS_INVESTIGATION", "Automatic start failed",
                        "Failed automatic start observed; part not diagnosed",
                        sorted(str(e["id"]) for e in (req, res, gen)))
    assert g["asset_id"] == GEN_A and g["link"] == "/b"
    # A failure with no ledger-present ID falls through to success, then to no result.
    ghost_failure = _chain("OBSERVED_FAILURE", ("START_RESULT", "OBSERVED", [ghost]))
    success = _chain("OBSERVED_SUCCESS", ("START_RESULT", "OBSERVED", [res]))
    # Generator 4: success.
    g = _health(chains=[ghost_failure, success], accepted=[res])[0]["BACKUP_GENERATOR"]
    assert _cell(g) == ("UNKNOWN", "Automatic start succeeded",
                        "A successful start does not establish generator condition", [str(res["id"])])
    # Generator 5: nothing accepted.
    g = _health(chains=[ghost_failure], accepted=[])[0]["BACKUP_GENERATOR"]
    assert _cell(g) == ("UNKNOWN", "No accepted start result", "No accepted automatic-start result in this window", [])
    assert _cell(_health()[0]["BACKUP_GENERATOR"])[1] == "No accepted start result"

    # Generator asset: a policy asset not in `assets` falls back to the single asset; two assets, no match -> null.
    stranger = str(uuid4())
    assert _health(chains=[failure], start_policy={"generator_asset_id": stranger},
                   accepted=[req])[0]["BACKUP_GENERATOR"]["asset_id"] == GEN_A
    two = _foundation(_asset(GEN_A, "GENERATOR", "GEN-1"), _asset(GEN_B, "GENERATOR", "GEN-2"))
    assert _health(chains=[failure], start_policy={"generator_asset_id": stranger}, accepted=[req],
                   foundation=two)[0]["BACKUP_GENERATOR"]["asset_id"] is None
    assert _health(chains=[failure], start_policy={"generator_asset_id": GEN_B}, accepted=[req],
                   foundation=two)[0]["BACKUP_GENERATOR"]["asset_id"] == GEN_B

    # Compressor branches.
    comp = _ev(cold.COMPRESSOR_ROLE)
    with_comp = _chain("OBSERVED_FAILURE", ("COMPRESSOR", "OBSERVED", [comp, ghost]),
                       ("COMPRESSOR", "MISSING", [res]))
    p = _health(chains=[with_comp], accepted=[comp, res])[0]["COOLING_PLANT"]
    assert _cell(p) == ("UNKNOWN", "Condition unknown", "Comparable recovery and condition evidence absent",
                        [str(comp["id"])])
    assert p["asset_id"] == COMP_A
    p = _health(chains=[with_comp], accepted=[comp], foundation=_foundation())[0]["COOLING_PLANT"]
    assert _cell(p) == ("NOT_CONFIGURED", "Not configured", "No cooling plant is declared in the selected Foundation",
                        [])
    assert (p["asset_id"], p["link"]) == (None, None)
    two_comp = _foundation(_asset(COMP_A, "COMPRESSOR", "CMP-1"), _asset(str(uuid4()), "COMPRESSOR", "CMP-2"))
    assert _health(foundation=two_comp)[0]["COOLING_PLANT"]["asset_id"] is None

    # Probe branches: n = 0, 1, 2 distinct ledger source IDs, from SUPPORT links and OBSERVED PROBE steps.
    p1, p2, p3 = _ev(cold.PROBE_ROLE), _ev(cold.PROBE_ROLE), _ev(cold.PROBE_ROLE, SRC_2)
    not_probe = _ev(cold.DOOR_ROLE)
    links = [{"use": "SUPPORT", "evidence_id": str(p1["id"])}, {"use": "CONTEXT", "evidence_id": str(p3["id"])},
             {"use": "SUPPORT", "evidence_id": str(not_probe["id"])}]
    probe_chain = _chain("OBSERVED_FAILURE", ("PROBE", "OBSERVED", [p2]))
    t = _health(chains=[probe_chain], exc_links=links, accepted=[p1, p2, p3, not_probe])[0]["TEMPERATURE_SENSING"]
    assert _cell(t) == ("LIMITED", "Single-point observation",
                        "One accepted probe does not establish room-wide coverage",
                        sorted([str(p1["id"]), str(p2["id"])]))
    assert t["asset_id"] == PROBE_A and t["link"] == "/e"
    t = _health(exc_links=[], accepted=[])[0]["TEMPERATURE_SENSING"]
    assert _cell(t) == ("UNKNOWN", "No accepted probe", "No accepted probe observation in this window", [])
    both = links + [{"use": "SUPPORT", "evidence_id": str(p3["id"])}]
    t = _health(exc_links=both, accepted=[p1, p3])[0]["TEMPERATURE_SENSING"]
    assert _cell(t) == ("UNKNOWN", "Multiple probe observations",
                        "Multiple selected probes do not establish room-wide condition",
                        sorted([str(p1["id"]), str(p3["id"])]))
    t = _health(exc_links=links, accepted=[p1], foundation=_foundation())[0]["TEMPERATURE_SENSING"]
    assert _cell(t) == ("NOT_CONFIGURED", "Not configured",
                        "No temperature probe is declared in the selected Foundation", [])
    assert (t["asset_id"], t["link"]) == (None, None)
    # Probe asset: excursion policy, then START policy, then the single asset, else null.
    probe_b = str(uuid4())
    two_probes = _foundation(_asset(PROBE_A, "TEMPERATURE_PROBE", "PRB-1"),
                             _asset(probe_b, "TEMPERATURE_PROBE", "PRB-2"))
    assert _health(chains=[], start_policy={"probe_asset_id": PROBE_A}, exc_policy={"probe_asset_id": probe_b},
                   foundation=two_probes)[0]["TEMPERATURE_SENSING"]["asset_id"] == probe_b
    assert _health(chains=[], start_policy={"probe_asset_id": PROBE_A}, exc_policy={"probe_asset_id": stranger},
                   foundation=two_probes)[0]["TEMPERATURE_SENSING"]["asset_id"] == PROBE_A
    assert _health(exc_policy={"probe_asset_id": stranger}, foundation=two_probes)[0][
        "TEMPERATURE_SENSING"]["asset_id"] is None
    assert _health(exc_policy={"probe_asset_id": stranger})[0]["TEMPERATURE_SENSING"]["asset_id"] == PROBE_A
    # Q13: the Foundation's chamber probe is the third candidate; null gives no asset; a selected policy probe wins.
    chamber = {**two_probes, "chamber_probe_asset_id": probe_b}
    assert _health(foundation=chamber)[0]["TEMPERATURE_SENSING"]["asset_id"] == probe_b
    assert _health(foundation={**two_probes, "chamber_probe_asset_id": None})[0][
        "TEMPERATURE_SENSING"]["asset_id"] is None
    assert _health(exc_policy={"probe_asset_id": PROBE_A}, foundation=chamber)[0][
        "TEMPERATURE_SENSING"]["asset_id"] == PROBE_A

    # An unresolved Foundation never yields NOT_CONFIGURED: every row stays assessed with no asset.
    _, rows = _health(chains=[failure], exc_links=links, accepted=[req, res, gen, p1], foundation=None)
    assert all(r["condition_state"] != "NOT_CONFIGURED" and r["asset_id"] is None and r["assets"] == []
               and r["link"] is not None for r in rows)
    assert [r["condition_state"] for r in rows] == ["NEEDS_INVESTIGATION", "UNKNOWN", "LIMITED"]
