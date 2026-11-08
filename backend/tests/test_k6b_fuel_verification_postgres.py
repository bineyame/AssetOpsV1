"""DIESEL-K6b L2 (build sheet DIESEL-1 §9m.4, ruling DIESEL-1-R3m): `fuel-residual-within-band-1` on Postgres, on its
own `assetops_k6_test`.

On the imported MINIGRID Site (K6a's `Kit`): synthetic K3 windows on the fuel store's virtual clock, the fuel Finding
through K4a's `raise_night`, the Action through K6a's `create_action`, then the case (request, record, ASSIGN,
COMPLETE, link). The verification service runs on its own test clock:

1. Freeze before the first later night: 201, the columns, `effective_from` = the COMPLETE `occurred_at`, a replay;
   before COMPLETE 409 NOT_APPLIED; after the first later night began 409 LATER_WINDOW_STARTED; a mill Action 409.
2. Evaluate: NOT_JUDGED with no row; VERIFIED stored with three metrics; a replay; a later UNEXPLAINED revision of a
   chosen night does not change the read-back. A separate state with a 90-minute gap: INEFFECTIVE, MISS_GAP_TEXT.
3. API: 200 with the wire; unknown id 404; a mill Action 409; the mill route on the fuel Action 409.
4. Chain: `_SITE_ACTIONS` reads `action_domain = 'FUEL_BALANCE'` and the thread's Action entry carries FUEL_VERDICT.

Item 5 (the mill path stays byte-equal): the CH-9b fixture's `freeze_domain_plan` / `evaluate_domain_plan` /
`domain_summary` outputs, normalized (ids, digests and instants made relative), equal the pins in
`fixtures/k6b_mill_pins.json`, which were captured on the branch's first commit, before any K6b code existed.
Set `K6B_CAPTURE_PINS=1` to (re)write the pins file instead of comparing (capture only on unchanged mill code).
"""

from __future__ import annotations

import json
import os
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

UTC = timezone.utc
PINS = Path(__file__).resolve().parent / "fixtures" / "k6b_mill_pins.json"
_UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
_SHA = re.compile(r"^[0-9a-f]{64}$")
_INSTANT = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(\+00:00|Z)$")
_DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if URL:
    import hashlib

    import pg_harness
    from sqlalchemy import text
    from test_ch2_thread_store_postgres import seeded  # noqa: F401
    from test_ch9b1_opportunity_actions_postgres import _create as create_mill, mill  # noqa: F401
    from test_ch9b3_mill_verdict_postgres import _after, _close, _frozen, _later, _snap
    from test_k6a_fuel_action_origin_postgres import CODE, NIGHT, OTHER_NIGHT, kit  # noqa: F401
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    from assetops_backend.actions import fuel_verification as fv
    from assetops_backend.actions.composition import build_fuel_verification_service
    from assetops_backend.chain import site_chain
    from assetops_backend.chain.adapters.postgres_chain_read import _SITE_ACTIONS, _SITE_EVENTS, _SITE_OCCURRENCES
    from assetops_backend.chain.backfill import run_threads
    from assetops_backend.chain.composition import build_thread_sources, build_thread_store
    from assetops_backend.fuel_balance import rules as fuel_rules


class Clock:
    def __init__(self, at: datetime) -> None:
        self.at = at

    def __call__(self) -> datetime:
        return self.at


def put(kit, night: date, state: str = "WITHIN_MARGIN", low: str | None = "-5", high: str | None = "10",
        gap: int = 0):  # noqa: F811
    """Append the night's next window revision on the fuel store's virtual clock (recorded at end + 1 h or later),
    with K3's `unknown_slots` term (0) so the night can count as fully checked."""
    fuel = kit.fuel
    start, end = fuel_rules.night_window(night, fuel.tz)
    fuel.clock.now = max(fuel.clock.now + timedelta(minutes=1), end + timedelta(hours=1))
    spans = [[fuel_rules.iso(start + timedelta(hours=6)), fuel_rules.iso(start + timedelta(hours=6, minutes=gap))]]

    def work(tx):
        row = {"tank_asset_id": fuel.tank, "generator_asset_id": fuel.gen, "night_date": night,
               "window_start": start, "window_end": end, "state": state,
               "reason": "MISSING_OPENING" if state == "NOT_ASSESSED" else None,
               "residual_low": None if state == "NOT_ASSESSED" else low,
               "residual_high": None if state == "NOT_ASSESSED" else high, "gap_minutes": gap,
               "gap_spans": spans if gap else [], "limitations": ["REPORTING_GAP"] if gap else [],
               "terms": {"accuracy_l": "10", "accuracy_revision_id": None, "sfc_revision_id": None,
                         "no_load_revision_id": None, "unknown_slots": 0},
               "evidence_ids": [], "record_ids": [],
               "input_sha256": hashlib.sha256(f"{night}{state}{low}{gap}{fuel.clock.now}".encode()).hexdigest()}
        return tx.append(tx.latest(fuel.tank, night), row)
    return fuel.store.transaction(fuel.t, fuel.s, work)


def story(kit, tag: str = "k6b", night: date | None = None):  # noqa: F811
    """The fuel Finding, its Action and the COMPLETE linked case; returns (action id, effective_from, later nights)."""
    put(kit, night or NIGHT, "UNEXPLAINED", "45", "60")
    raised = kit.fuel.raise_(night or NIGHT)
    status, action = kit.create(kit.body(raised, key=f"{tag}-fuel-action"))
    assert status == 201, action
    case_id, _ = kit.complete_case(action["id"], tag)
    (occurred,) = kit.rows("SELECT occurred_at FROM work_event WHERE case_id = :c AND kind = 'COMPLETE'", c=case_id)[0]
    effective = occurred.astimezone(UTC)
    return action["id"], effective, fv.later_nights(effective, kit.fuel.tz), case_id


def window_start(kit, night: date) -> datetime:  # noqa: F811
    return fuel_rules.night_window(night, kit.fuel.tz)[0]


def window_end(kit, night: date) -> datetime:  # noqa: F811
    return fuel_rules.night_window(night, kit.fuel.tz)[1]


def service(clock):
    return build_fuel_verification_service(URL, test_clock=clock)


def dispose(svc) -> None:
    pg_harness.dispose(svc.store)
    svc.actions.verification_ports.fuel_windows.dispose()


class _Norm:
    """Ids, digests and instants made run-independent: a UUID by first-seen order, a digest as `<sha>`, an instant
    as seconds after the plan's `effective_from`, a date as days after the effective day."""

    def __init__(self, effective: datetime, eff_day: date, tz: str) -> None:
        self.effective, self.eff_day, self.ids, self.tz = effective, eff_day, {}, ZoneInfo(tz)

    def __call__(self, v):
        if isinstance(v, dict):
            return {k: self(x) for k, x in v.items()}
        if isinstance(v, (list, tuple)):
            return [self(x) for x in v]
        if isinstance(v, str):
            if _UUID.match(v):
                return self.ids.setdefault(v, f"<uuid:{len(self.ids)}>")
            if _SHA.match(v):
                return "<sha>"
            if _INSTANT.match(v):
                at = datetime.fromisoformat(v.replace("Z", "+00:00"))
                local = at.astimezone(self.tz)
                if (local.minute, local.second, local.microsecond) == (0, 0, 0):  # a calendar instant (midnight, noon)
                    return f"<d{(local.date() - self.eff_day).days:+d} {local:%H}h>"
                return f"<t{(at - self.effective).total_seconds():+.6f}s>"  # a clock instant: after effective_from
            if _DAY.match(v):
                return f"<d{(date.fromisoformat(v) - self.eff_day).days:+d}>"
            v = re.sub(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                       lambda m: self.ids.setdefault(m.group(), f"<uuid:{len(self.ids)}>"), v)
            return re.sub(r"\d{4}-\d{2}-\d{2}", lambda m: f"<d{(date.fromisoformat(m.group()) - self.eff_day).days:+d}>",
                          v)
        return v


def _mill_outputs(mill) -> dict:  # noqa: F811
    """The CH-9b3 VERIFIED story (`test_verified_stores_one_domain_outcome...`) through the three mill methods."""
    svc, clock, aid, eff, tz = _frozen(mill, "k6b-mill-pin")
    try:
        replay = svc.freeze_domain_plan(mill.t, mill.s, aid)
        before = svc.domain_summary(mill.t, mill.s, aid)
        not_yet = svc.evaluate_domain_plan(mill.t, mill.s, aid)
        _later(mill, eff, "11.5")
        _snap(mill, eff, "999")
        clock.at = _after(eff, tz, 5)
        judged = svc.evaluate_domain_plan(mill.t, mill.s, aid)
        again = svc.evaluate_domain_plan(mill.t, mill.s, aid)
        after = svc.domain_summary(mill.t, mill.s, aid)
        with mill.engine.connect() as c:
            effective = c.execute(text("SELECT effective_from FROM verification_plan WHERE domain_action_id = :a"),
                                  {"a": aid}).scalar_one().astimezone(UTC)
    finally:
        _close(mill)
    norm = _Norm(effective, eff, tz)
    norm(aid)
    return norm({"freeze_replay": list(replay), "summary_before": before, "evaluate_not_judged": not_yet,
                 "evaluate_judged": judged, "evaluate_replay": again, "summary_after": after})


def test_5_mill_path_outputs_equal_the_first_commit_pins(mill) -> None:  # noqa: F811
    got = json.loads(json.dumps(_mill_outputs(mill), sort_keys=True, default=str))
    if os.environ.get("K6B_CAPTURE_PINS") == "1":
        PINS.write_text(json.dumps(got, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        pytest.skip("pins captured")
    want = json.loads(PINS.read_text(encoding="utf-8"))
    assert got == want, _diff(got, want)


def _plan_row(kit, aid):  # noqa: F811
    with kit.engine.connect() as c:
        return c.execute(text("SELECT * FROM verification_plan WHERE domain_action_id = :a"), {"a": aid}).one()


def _count(kit, sql: str, **p) -> int:  # noqa: F811
    return kit.rows(sql, **p)[0][0]


# --- 1 and 2: freeze, evaluate, read back ---------------------------------------------------------------------------

def test_1_2_freeze_evaluate_and_read_back(kit) -> None:  # noqa: F811
    aid, effective, later, case_id = story(kit)
    clock = Clock(effective + timedelta(seconds=1))
    svc = service(clock)
    try:
        assert window_start(kit, later[0]) > clock.at, "the freeze must happen before the first later night"
        status, body = svc.freeze_fuel_plan(kit.t, kit.s, aid)
        assert status == 201 and body["replayed"] is False, body
        row = _plan_row(kit, aid)
        (rev, window_id) = kit.rows("SELECT d.origin_finding_revision_id, r.claim->>'fuel_balance_window_id' FROM "
                                    "domain_action d JOIN finding_revision r ON r.id = d.origin_finding_revision_id "
                                    "WHERE d.id = :a", a=aid)[0]
        assert row.rule_id == fv.FUEL and row.plan_version == fv.FUEL_PLAN_VERSION and row.action_id is None
        assert str(row.domain_action_id) == aid and row.origin_finding_revision_id == rev
        assert row.effective_from == effective and row.triggering_fixture == fv.FUEL_LEVER
        assert row.later_start == window_start(kit, later[0]) and row.later_end - row.later_start == timedelta(days=14)
        assert row.baseline_end == window_end(kit, NIGHT) and row.baseline_selection["window_id"] == window_id
        assert row.target == fv.TARGET and row.guardrails == {} and row.recorded_at == clock.at
        assert row.basis["applied"]["case_id"] == case_id and row.idempotency_key == f"fuel-plan-{aid}"
        again = svc.freeze_fuel_plan(kit.t, kit.s, aid)
        assert again[0] == 200 and again[1]["replayed"] is True and again[1]["plan"]["plan_id"] == str(row.id)

        # evaluation: a NOT_ASSESSED night is skipped (by grade); two COMPLETE nights while open: not judged
        put(kit, later[0], "NOT_ASSESSED")
        put(kit, later[1])
        put(kit, later[2])
        clock.at = window_end(kit, later[2]) + timedelta(hours=2)
        got = svc.evaluate_fuel_plan(kit.t, kit.s, aid)
        assert got == {"state": "NOT_JUDGED", "stored": False, "not_judged_text": fv.LATER_TEXT.format(n=2)}
        assert _count(kit, "SELECT count(*) FROM verification_outcome WHERE domain_action_id = :a", a=aid) == 0
        live = svc.fuel_summary(kit.t, kit.s, aid, CODE)
        assert live["state"] == "NOT_JUDGED" and live["not_judged_text"] == fv.LATER_TEXT.format(n=2)

        put(kit, later[3])
        clock.at = window_end(kit, later[3]) + timedelta(hours=2)
        got = svc.evaluate_fuel_plan(kit.t, kit.s, aid)
        assert got["state"] == "VERIFIED" and got["stored"] is True, got
        replay = svc.evaluate_fuel_plan(kit.t, kit.s, aid)
        assert replay["replayed"] is True and replay["outcome_id"] == got["outcome_id"]
        metrics = kit.rows("SELECT m.window_name, m.state, m.value_text FROM verification_metric m JOIN "
                           "verification_outcome o ON o.id = m.outcome_id WHERE o.domain_action_id = :a "
                           "ORDER BY m.window_name", a=aid)
        assert [tuple(m) for m in metrics] == [("BASELINE", "PASS", "45.0 to 60.0 L"), ("COMPARISON", "PASS", None),
                                               ("LATER", "PASS", "3 of 3")]
        before = svc.fuel_summary(kit.t, kit.s, aid, CODE)
        assert before["state"] == "VERIFIED" and before["headline"] == "Fuel stayed accounted for"
        assert before["sentence"] == fv.VERIFIED_TEXT.format(n=3) and before["fixed_line"] == fv.FIXED_LINE
        assert before["value"] is None and before["cost_check"] is None
        assert [n["role"] for n in before["nights"]] == ["BASELINE", "LATER", "LATER", "LATER"]
        assert before["activity"]["case_href"] == f"/maintenance/requests/{case_id}"

        # a later UNEXPLAINED revision of a chosen night never changes the stored verdict's read-back
        put(kit, later[2], "UNEXPLAINED", "30", "50")
        clock.at += timedelta(days=1)
        after = svc.fuel_summary(kit.t, kit.s, aid, CODE)
        assert after == before
    finally:
        dispose(svc)


def test_2_a_sensor_gap_night_is_ineffective(kit) -> None:  # noqa: F811
    aid, effective, later, _ = story(kit, "k6b-gap")
    clock = Clock(effective + timedelta(seconds=1))
    svc = service(clock)
    try:
        assert svc.freeze_fuel_plan(kit.t, kit.s, aid)[0] == 201
        put(kit, later[0])
        put(kit, later[1], gap=90)
        put(kit, later[2])
        clock.at = window_end(kit, later[2]) + timedelta(hours=2)
        got = svc.evaluate_fuel_plan(kit.t, kit.s, aid)
        assert got["state"] == "INEFFECTIVE" and got["stored"] is True, got
        body = svc.fuel_summary(kit.t, kit.s, aid, CODE)
        assert body["headline"] == "Target not met"
        assert body["sentence"] == fv.MISS_GAP_TEXT.format(date=f"{later[1].day} {later[1]:%b}")
        assert body["nights"][2]["sensor_text"] == "No readings for 90 min" and body["nights"][2]["result_text"] == \
            "Sensor gap"
    finally:
        dispose(svc)


def test_1_refusals_not_applied_and_later_window_started(kit) -> None:  # noqa: F811
    put(kit, OTHER_NIGHT, "UNEXPLAINED", "45", "60")
    raised = kit.fuel.raise_(OTHER_NIGHT)
    status, action = kit.create(kit.body(raised, key="k6b-late-action"))
    assert status == 201, action
    clock = Clock(datetime.now(UTC))
    svc = service(clock)
    try:
        with pytest.raises(fv.ActionRefused) as e:
            svc.freeze_fuel_plan(kit.t, kit.s, action["id"])
        assert (e.value.status, e.value.code) == (409, "VERIFICATION_ACTION_NOT_APPLIED")
        case_id, _ = kit.complete_case(action["id"], "k6b-late")
        (occurred,) = kit.rows("SELECT occurred_at FROM work_event WHERE case_id = :c AND kind = 'COMPLETE'",
                               c=case_id)[0]
        first_night = fv.later_nights(occurred.astimezone(UTC), kit.fuel.tz)[0]
        clock.at = window_start(kit, first_night) + timedelta(minutes=1)
        with pytest.raises(fv.ActionRefused) as e:
            svc.freeze_fuel_plan(kit.t, kit.s, action["id"])
        assert (e.value.status, e.value.code) == (409, "VERIFICATION_LATER_WINDOW_STARTED")
        clock.at = window_start(kit, first_night)  # the instant itself has begun (`<=`)
        with pytest.raises(fv.ActionRefused):
            svc.freeze_fuel_plan(kit.t, kit.s, action["id"])
        assert _count(kit, "SELECT count(*) FROM verification_plan WHERE domain_action_id = :a", a=action["id"]) == 0
        with pytest.raises(fv.ActionRefused) as e:
            svc.freeze_fuel_plan(kit.t, kit.s, uuid4())
        assert (e.value.status, e.value.code) == (404, "ACTION_NOT_FOUND")
    finally:
        dispose(svc)


def test_1_3_mill_action_is_refused_and_the_mill_route_refuses_a_fuel_action(mill) -> None:  # noqa: F811
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from assetops_backend.action_api import build_action_router

    action = create_mill(mill, idempotency_key="k6b-mill-0001")
    svc = service(Clock(datetime.now(UTC)))
    try:
        with pytest.raises(fv.ActionRefused) as e:
            svc.freeze_fuel_plan(mill.t, mill.s, action["id"])
        assert (e.value.status, e.value.code) == (409, "VERIFICATION_FAMILY_UNSUPPORTED")
        assert e.value.message == "Only an Action raised from an unexplained-fuel Finding has a fuel verification plan."
        assert svc.evaluate_fuel_plan(mill.t, mill.s, action["id"]) == {"state": "NO_PLAN", "stored": False}
        app = FastAPI()
        app.include_router(build_action_router(svc.actions, {"MILL-1": ("MILL-1", mill.t, mill.s)}.get,
                                               gate=lambda c, t, s: (True, "test gate")))
        got = TestClient(app).get(f"/api/sites/MILL-1/domain-work/actions/{action['id']}/fuel-verification")
        assert got.status_code == 409 and got.json()["detail"]["code"] == "VERIFICATION_FAMILY_UNSUPPORTED"
    finally:
        dispose(svc)


def test_3_api_and_4_chain(kit) -> None:  # noqa: F811
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from assetops_backend.action_api import build_action_router

    aid, effective, later, _ = story(kit, "k6b-api")
    clock = Clock(effective + timedelta(seconds=1))
    svc = service(clock)
    try:
        assert svc.freeze_fuel_plan(kit.t, kit.s, aid)[0] == 201
        for night in later[:3]:
            put(kit, night)
        clock.at = window_end(kit, later[2]) + timedelta(hours=2)
        assert svc.evaluate_fuel_plan(kit.t, kit.s, aid)["state"] == "VERIFIED"
        app = FastAPI()
        app.include_router(build_action_router(svc.actions, {CODE: (CODE, kit.t, kit.s)}.get,
                                               gate=lambda c, t, s: (True, "test gate")))
        http = TestClient(app)
        ok = http.get(f"/api/sites/{CODE}/domain-work/actions/{aid}/fuel-verification")
        assert ok.status_code == 200, ok.text
        body = ok.json()
        assert body["state"] == "VERIFIED" and body["value"] is None and body["cost_check"] is None
        assert body["origin"]["ref"]["kind"] == "FUEL_FINDING" and "access_basis" in body
        assert http.get(f"/api/sites/{CODE}/domain-work/actions/{uuid4()}/fuel-verification").status_code == 404
        mill_route = http.get(f"/api/sites/{CODE}/domain-work/actions/{aid}/verification")
        assert mill_route.status_code == 409 and mill_route.json()["detail"]["message"] == (
            "Only a MINI Action raised from an opportunity has a midday verification.")
    finally:
        dispose(svc)

    readers, writer = build_thread_sources(URL), build_thread_store(URL)
    try:
        run_threads(readers, writer, kit.t, kit.s)
    finally:
        pg_harness.dispose(readers, writer)
    p = {"t": kit.t, "s": kit.s, "k": None}
    with kit.engine.connect() as c:
        rows = {name: tuple(dict(r) for r in c.execute(sql, p).mappings().all())
                for name, sql in (("occurrences", _SITE_OCCURRENCES), ("events", _SITE_EVENTS),
                                  ("actions", _SITE_ACTIONS))}
    (mine,) = [a for a in rows["actions"] if a["action_id"] == aid]
    assert mine["action_domain"] == "FUEL_BALANCE" and mine["outcome"] == "VERIFIED"
    (entry,) = site_chain.actions_of(rows, [mine["thread_id"]], site=CODE, tz=kit.fuel.tz, cutoff=None,
                                     verification={})
    assert entry["ref"] == {"kind": "FUEL_VERDICT", "site": CODE, "id": aid}
    (verdict,) = site_chain.fuel_verdict_actions(rows, site=CODE, cutoff=None, lo=effective - timedelta(days=60),
                                                 hi=clock.at + timedelta(days=1))
    assert verdict["outcome"] == "VERIFIED" and verdict["ref"]["kind"] == "FUEL_VERDICT"


def _diff(a, b, path="") -> list[str]:
    if isinstance(a, dict) and isinstance(b, dict):
        return [x for k in sorted(set(a) | set(b)) for x in _diff(a.get(k), b.get(k), f"{path}.{k}")]
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return [x for i, (p, q) in enumerate(zip(a, b)) for x in _diff(p, q, f"{path}[{i}]")]
    return [] if a == b else [f"{path}: {a!r} != {b!r}"]
