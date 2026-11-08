"""OWN-G1 (build sheet OWN-GAPS §4, Revision 2 R2-G1): the owner's `add-dates` tool. No database.

Pure planning, refusals, the Kisiwa night plan and its records, the tick-and-verify loop with fakes, the links, and
the KIS-row story bounds. The rehearsal on a clone (§4.7) is the DB proof.
"""

from __future__ import annotations

import functools
import hashlib
import json
import sys
from datetime import date, datetime, timedelta, timezone
from fractions import Fraction
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
for extra in (REPO / "tools", REPO / "backend" / "tests", REPO / "host" / "tests", REPO / "host"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

import demo_combined as dc  # noqa: E402
import demo_combined_kisiwa as kis  # noqa: E402
import demo_combined_rows as rows  # noqa: E402
import demo_story_days as sd  # noqa: E402

PREPARED = datetime(2026, 11, 8, 10, 0, tzinfo=timezone.utc)  # prepare day: S = 2026-11-06 (a Friday)
LATER = datetime(2026, 11, 12, 13, 0, tzinfo=timezone.utc)  # Thursday 16:00 in Dar es Salaam
ZONES = {"KOBO-001": "Africa/Addis_Ababa", "COLD-LAB-001": "Africa/Addis_Ababa", "EV-LAB-001": "Etc/UTC",
         "KISIWA-001": "Africa/Dar_es_Salaam"}
ALL = ["kobo", "cold", "ev", "kisiwa"]
D = date.fromisoformat


@functools.lru_cache(maxsize=1)
def _built() -> tuple[str, str]:
    story = dc.resolve_story(PREPARED, kisiwa=True)
    story["sites"] = list(ALL)
    days = story.pop("days")
    return json.dumps(story), json.dumps({"days": days, "doc": sd.load()})


def build() -> tuple[dict, dict]:
    story, days = _built()
    return json.loads(story), json.loads(days)


def plan(*, sites=ALL, date_from=None, date_to=None, kind=None, db_now=LATER, entries=(), days=None, delivered=None):
    story, days_json = build()
    return dc.plan_add_dates(story, days if days is not None else days_json, list(entries), sites=list(sites),
                             date_from=date_from, date_to=date_to, kind=kind, db_now=db_now, zones=ZONES,
                             delivered=delivered or {})


def code(fn) -> str:
    with pytest.raises(SystemExit) as refused:
        fn()
    return refused.value.error_code


def _kisiwa_build() -> dict:
    return {"runs": [{"physics": {"soc": "100", "fuel": "273943/300"}}]}


# ---- dates and timezones ---------------------------------------------------------------------------------------------

def test_calendar_date_and_story_offset_both_ways() -> None:
    S = datetime(2026, 11, 6, tzinfo=timezone.utc)
    for offset in (-9, 0, 1, 37):
        assert sd.date_offset(sd.offset_date(S, offset), S) == offset
    assert sd.date_offset(D("2026-11-09"), S) == 3 and sd.offset_date(S, -1) == D("2026-11-05")


def test_yesterday_is_per_site_timezone_across_a_utc_midnight() -> None:
    """R2-G1 header: at 22:30Z on a Monday, EV's (UTC) yesterday is Sunday; Kisiwa's local date is already Tuesday."""
    now = datetime(2026, 11, 9, 22, 30, tzinfo=timezone.utc)
    assert now.weekday() == 0
    assert sd.local_yesterday(now, ZONES["EV-LAB-001"]) == D("2026-11-08")
    assert sd.local_yesterday(now, ZONES["KISIWA-001"]) == D("2026-11-09")
    assert now.astimezone(kis.ZoneInfo(ZONES["KISIWA-001"])).date().weekday() == 1


def test_ev_lab_001_is_pinned_to_utc() -> None:
    text = (REPO / "backend" / "tests" / "fixtures" / "w2" / "ev-lab-001.yaml").read_text(encoding="utf-8")
    assert "timezone: Etc/UTC" in text


# ---- range planning ---------------------------------------------------------------------------------------------------

def test_defaults_per_site_and_date_major_order() -> None:
    p = plan()
    got = {s: [d.isoformat() for d in v["dates"]] for s, v in p["sites"].items()}
    assert got["kobo"] == ["2026-11-08", "2026-11-09", "2026-11-10", "2026-11-11"]  # last story day S+1
    assert got["cold"] == ["2026-11-07", "2026-11-08", "2026-11-09", "2026-11-10", "2026-11-11"]  # S+0
    assert got["ev"] == ["2026-11-10"]  # the next Tuesday after its last story Tuesday
    assert got["kisiwa"] == ["2026-11-07", "2026-11-08", "2026-11-09", "2026-11-10", "2026-11-11"]
    assert p["order"] == [D("2026-11-07") + timedelta(days=n) for n in range(5)]
    assert {s: v["kind"] for s, v in p["sites"].items()} == {"kobo": "normal", "cold": "normal", "ev": "normal",
                                                            "kisiwa": None}


def test_ev_tuesday_is_planned_and_a_wednesday_is_a_no_session_line() -> None:
    p = plan(sites=["ev"], date_from=D("2026-11-10"), date_to=D("2026-11-11"))["sites"]["ev"]
    assert p["dates"] == [D("2026-11-10")] and p["no_session"] == [D("2026-11-11")]
    lines = dc.plain_lines([], [], [{"site": "EV-LAB-001", "date": D("2026-11-11")}], {})
    assert lines == ["EV-LAB-001 2026-11-11: no charging session (the simulated charger runs on Tuesdays)"]


def test_already_present_dates_are_skipped_and_a_second_run_plans_nothing() -> None:
    story, days_json = build()
    first = plan(sites=["kobo"])["sites"]["kobo"]["dates"]
    S = dc.at(story["S"])
    added = [{"site": "kobo", "day": d.isoformat(), "offset": sd.date_offset(d, S), "kind": "normal",
              "received_at": "2026-11-12T12:00:00Z"} for d in first]
    again = {**days_json, "days": days_json["days"] + added}
    assert plan(sites=["kobo"], days=again)["sites"]["kobo"]["dates"] == []
    explicit = plan(sites=["kobo"], days=again, date_from=first[0], date_to=first[-1])["sites"]["kobo"]
    assert explicit["dates"] == [] and [r for _, r in explicit["skipped"]] == [dc.ALREADY_PRESENT] * len(first)
    delivered = plan(sites=["cold"], date_from=D("2026-11-07"), date_to=D("2026-11-07"),
                     delivered={"COLD-LAB-001": {"2026-11-07"}})["sites"]["cold"]
    assert delivered["dates"] == [] and delivered["skipped"] == [(D("2026-11-07"), dc.ALREADY_PRESENT)]


def test_a_later_from_leaves_core_days_empty() -> None:
    p = plan(sites=["kobo", "ev"], date_from=D("2026-11-10"))["sites"]
    assert p["kobo"]["left_empty"] == [D("2026-11-08"), D("2026-11-09")]
    assert p["ev"]["left_empty"] == []  # its default is that same Tuesday


# ---- whole-command refusals at their edges ----------------------------------------------------------------------------

def test_to_yesterday_passes_and_today_refuses() -> None:
    assert plan(sites=["kobo"], date_to=D("2026-11-11"))["sites"]["kobo"]["dates"][-1] == D("2026-11-11")
    assert code(lambda: plan(sites=["kobo"], date_to=D("2026-11-12"))) == "DATE_NOT_PAST"
    # EV is UTC: at 22:30Z its today is still the UTC date, Kobo's is already the next day
    late = datetime(2026, 11, 11, 22, 30, tzinfo=timezone.utc)
    assert code(lambda: plan(sites=["ev"], date_to=D("2026-11-11"), db_now=late)) == "DATE_NOT_PAST"
    assert plan(sites=["kobo"], date_to=D("2026-11-11"), db_now=late)["sites"]["kobo"]["dates"]


def test_story_day_edges() -> None:
    assert code(lambda: plan(sites=["kobo"], date_from=D("2026-11-07"))) == "STORY_DAY"
    assert plan(sites=["kobo"], date_from=D("2026-11-08"))["sites"]["kobo"]["dates"][0] == D("2026-11-08")
    assert code(lambda: plan(sites=["kisiwa"], date_from=D("2026-11-06"))) == "STORY_DAY"
    assert code(lambda: plan(sites=["cold"], date_to=D("2026-11-06"))) == "STORY_DAY"


def test_kisiwa_gap_of_one_day_refuses() -> None:
    assert code(lambda: plan(sites=["kisiwa"], date_from=D("2026-11-08"))) == "GAP_NOT_ALLOWED"
    assert plan(sites=["kisiwa"], date_from=D("2026-11-07"))["sites"]["kisiwa"]["dates"][0] == D("2026-11-07")


def test_from_after_to_kind_and_site_refusals() -> None:
    assert code(lambda: plan(date_from=D("2026-11-10"), date_to=D("2026-11-09"))) == "FROM_AFTER_TO"
    assert code(lambda: plan(sites=["kobo", "cold"], date_from=D("2026-11-10"), date_to=D("2026-11-10"),
                             kind="normal")) == "KIND_NEEDS_ONE_DATE"
    assert code(lambda: plan(sites=["kobo"], kind="overuse")) == "KIND_NEEDS_ONE_DATE"
    one = plan(sites=["kobo"], date_from=D("2026-11-10"), date_to=D("2026-11-10"), kind="overuse")
    assert one["sites"]["kobo"]["kind"] == "overuse"
    story, _ = build()
    assert code(lambda: dc.select_sites("KOBO-001,KISIWA-001", {**story, "sites": ["kobo", "cold", "ev"]})) == \
        "SITE_NOT_IN_BUILD"
    assert dc.select_sites("all", story) == ALL and dc.select_sites("KISIWA-001,KOBO-001", story) == ["kobo", "kisiwa"]


def test_kisiwa_default_end_is_the_last_finished_night() -> None:
    """R2-G1 Q1: night d's run ends d+1 12:00Z (15:00 local); it is added once that end + 5 min has passed."""
    story, _ = build()
    k = story["kisiwa"]
    assert kis.night_end(k, D("2026-11-11")) == datetime(2026, 11, 12, 12, 0, tzinfo=timezone.utc)
    assert kis.latest_finished_night(k, datetime(2026, 11, 12, 12, 5, tzinfo=timezone.utc)) == D("2026-11-11")
    assert kis.latest_finished_night(k, datetime(2026, 11, 12, 12, 4, 59, tzinfo=timezone.utc)) == D("2026-11-10")
    morning = datetime(2026, 11, 12, 6, 0, tzinfo=timezone.utc)
    p = plan(sites=["kisiwa"], db_now=morning)["sites"]["kisiwa"]
    assert p["dates"][-1] == D("2026-11-10") and p["skipped"] == []
    p = plan(sites=["kisiwa"], db_now=morning, date_to=D("2026-11-11"))["sites"]["kisiwa"]
    assert p["dates"][-1] == D("2026-11-10") and p["skipped"] == [(D("2026-11-11"), dc.NIGHT_NOT_OVER)]


def test_date_too_old_edge() -> None:
    story, _ = build()
    dip = kis.night_start(story["kisiwa"], D("2026-11-07")) + timedelta(minutes=180)
    edge = dip + timedelta(days=30) - timedelta(hours=1)
    assert not kis.date_too_old(story["kisiwa"], D("2026-11-07"), edge)
    assert kis.date_too_old(story["kisiwa"], D("2026-11-07"), edge + timedelta(seconds=1))
    later = edge + timedelta(seconds=1)
    assert code(lambda: plan(sites=["kisiwa"], db_now=later, date_to=D("2026-11-07"))) == "DATE_TOO_OLD"


def test_preflight_refusals_in_order() -> None:
    ok = {"fuel_stage": True, "entry_status": 422, "entry_code": "OPREC_ENTRY_INVALID"}
    assert dc.preflight_refusal(0, ok, True) is None
    assert dc.preflight_refusal(2, None, False).error_code == "BUILD_TOO_OLD"
    assert dc.preflight_refusal(0, None, True).error_code == "BUILD_TOO_OLD"
    assert dc.preflight_refusal(0, {**ok, "fuel_stage": False}, False) is None  # only checked with Kisiwa
    assert dc.preflight_refusal(0, {**ok, "fuel_stage": False}, True).error_code == "FUEL_STAGE_MISSING"
    off = dc.preflight_refusal(0, {**ok, "entry_status": 403, "entry_code": "WORK_WRITE_FORBIDDEN"}, True)
    assert off.error_code == "ENTRY_DISABLED" and "ASSETOPS_OPERATIONAL_ENTRY" in str(off)
    missing = dc.preflight_refusal(0, {**ok, "entry_status": 404, "entry_code": None}, True)
    assert missing.error_code == "ENTRY_DISABLED" and "(G3a)" in str(missing)


# ---- the Kisiwa night ------------------------------------------------------------------------------------------------

def test_kisiwa_kind_choice_edges() -> None:
    assert kis.choose_kind(None, Fraction(249999, 1000)) == "delivery"
    assert kis.choose_kind(None, Fraction(250)) == "normal"
    assert code(lambda: kis.choose_kind("normal", Fraction(249999, 1000))) == "FUEL_LOW_USE_DELIVERY"
    assert kis.choose_kind("delivery", Fraction(650)) == "delivery"
    assert code(lambda: kis.choose_kind("delivery", Fraction(651))) == "DELIVERY_TANK_FULL"
    assert code(lambda: kis.choose_kind("refill", Fraction(500))) == "UNKNOWN_KIND"


def test_plan_night_refusals_and_resume() -> None:
    story, _ = build()
    k, b = story["kisiwa"], _kisiwa_build()
    end = kis.night_end(k, D("2026-11-07"))
    first = kis.plan_night(k, b, [], D("2026-11-07"), None, end + timedelta(minutes=5))
    assert first["resume"] is False and first["kind"] == "normal" and first["start"] == "2026-11-07T12:00:00Z"
    assert code(lambda: kis.plan_night(k, b, [], D("2026-11-07"), None,
                                       end + timedelta(minutes=4, seconds=59))) == "DAY_NOT_IN_PAST"
    assert code(lambda: kis.plan_night(k, b, [], D("2026-11-08"), None, LATER)) == "NOT_NEXT_NIGHT"
    assert code(lambda: kis.plan_night(k, b, [], D("2026-11-06"), None, LATER)) == "DUPLICATE_DAY"
    published = {"night_date": "2026-11-07", "status": "PUBLISHED", "end_state": {"soc": "90", "fuel": "500"}}
    assert kis.plan_night(k, b, [published], D("2026-11-07"), None, LATER)["resume"] is True
    assert code(lambda: kis.plan_night(k, b, [{**published, "status": "DONE"}], D("2026-11-07"), None,
                                       LATER)) == "DUPLICATE_DAY"
    assert code(lambda: kis.plan_night(k, b, [], D("2026-11-07"), None, LATER, replay_exists=True)) == "PARTIAL_NIGHT"
    assert kis.plan_night(k, b, [published], D("2026-11-08"), None, LATER)["start_state"] == {"soc": "90",
                                                                                              "fuel": "500"}


def test_start_state_chains_done_and_published_over_the_story() -> None:
    b = _kisiwa_build()
    assert kis.start_state(b, []) == (Fraction(100), Fraction(273943, 300))
    entries = [{"night_date": "2026-11-07", "status": "DONE", "end_state": {"soc": "80", "fuel": "601/2"}},
               {"night_date": "2026-11-08", "status": "PUBLISHED", "end_state": {"soc": "70", "fuel": "240"}}]
    assert kis.start_state(b, entries) == (Fraction(70), Fraction(240))
    assert kis.start_state(b, entries[:1]) == (Fraction(80), Fraction(601, 2))


def test_actions_log_and_keys_are_deterministic() -> None:
    story, _ = build()
    night = D("2026-11-07")
    start = kis.night_start(story["kisiwa"], night)
    actions = kis.add_actions(start, night, "delivery")
    assert [(a["action_id"], a["at"]) for a in actions] == [
        ("kis-add-20261107-dip-1800", "2026-11-07T15:00:00Z"), ("kis-add-20261107-dip-0600", "2026-11-08T03:00:00Z"),
        ("kis-add-20261107-delivery", "2026-11-08T07:00:00Z")]
    assert actions[2]["ticket"] == {"reference": "KIS-DT-20261107", "volume_l": 300}
    assert [a["action_id"] for a in kis.add_actions(start, night, "normal")] == [a["action_id"] for a in actions[:2]]
    log_id = kis.add_log_id(story["S_date"], night)
    assert log_id == "kisiwa-001-story-20261106-add-20261107"
    text = kis.add_log_text(log_id, actions)
    assert text == kis.add_log_text(log_id, kis.add_actions(start, night, "delivery"))
    assert kis.parse_log(text)["log_id"] == log_id and text.startswith(kis.ADD_LOG_HEADER)
    assert hashlib.sha256(text.encode("utf-8")).hexdigest() == kis.lf_sha256(text)
    key = kis.entry_key("2026-11-06", night, "kis-add-20261107-dip-1800")
    assert key == "oprec-entry-" + hashlib.sha256(
        b"kisiwa-add|2026-11-06|2026-11-07|kis-add-20261107-dip-1800").hexdigest()[:32]
    dips = {"kis-add-20261107-dip-1800": 612, "kis-add-20261107-dip-0600": 540}
    bodies = kis.entry_bodies("2026-11-06", night, actions, dips)
    assert [(b["entry"], b["value"], b["taken_at_local"], b["ticket_reference"]) for b in bodies] == [
        ("TANK_DIP", "612", "2026-11-07T18:00", None), ("TANK_DIP", "540", "2026-11-08T06:00", None),
        ("FUEL_DELIVERY", "300", "2026-11-08T10:00", "KIS-DT-20261107")]
    assert len({b["idempotency_key"] for b in bodies}) == 3
    assert all(set(b) == {"entry", "value", "taken_at_local", "ticket_reference", "idempotency_key"} for b in bodies)


def test_wait_and_verify_window() -> None:
    entry = {"end": "2026-11-08T12:00:00Z", "received_at": "2026-11-12T13:00:00Z"}
    assert kis.wait_until(entry) == datetime(2026, 11, 12, 13, 5, tzinfo=timezone.utc)
    assert kis.wait_until({**entry, "received_at": "2026-11-08T12:10:00Z"}) == datetime(2026, 11, 8, 12, 30,
                                                                                          tzinfo=timezone.utc)
    good = {"revision": 1, "state": "WITHIN_MARGIN", "limitations": ["DELIVERY_RECORDED_LATE"]}
    assert kis.verify_window(None, 0, None)[0] == "ABSENT"
    assert kis.verify_window(good, 0, None)[0] == "DONE"  # any limitation set
    assert kis.verify_window(good, 0, {"code": "OK"})[0] == "DONE"
    assert kis.verify_window(good, 0, {"code": "FAILED"})[0] == "UNEXPECTED"
    assert kis.verify_window(good, 1, None)[0] == "UNEXPECTED"
    assert kis.verify_window({**good, "state": "UNEXPLAINED"}, 0, None)[0] == "UNEXPECTED"


# ---- the loop, with fakes --------------------------------------------------------------------------------------------

def _demo() -> dc.Demo:
    return dc.Demo("assetops_demo3_g1unit_test", "var/demo3_g1unit")


def test_tick_retry_count_while_the_window_is_absent(monkeypatch) -> None:
    demo = _demo()
    ticks, verifies = [], []
    states = iter(["ABSENT", "ABSENT", "DONE"])
    monkeypatch.setattr(dc.time, "sleep", lambda s: None)
    monkeypatch.setattr(demo, "tick", lambda: ticks.append(1) or {"outcome": "COMPLETED", "sites": []})

    def child(verb, payload, **kw):
        verifies.append(json.loads(payload))
        state = next(states)
        entry = {"window": {"revision": 1, "state": "WITHIN_MARGIN"}}
        return 0, {"verified": {"state": state, "line": "x", "entry": entry}}, ""

    monkeypatch.setattr(demo, "kisiwa_child", child)
    out = demo.tick_and_verify([{"site": "KISIWA-001", "date": D("2026-11-07"), "kind": "normal"}])
    assert len(ticks) == 3 and len(verifies) == 3 and out[0]["checked"] == "WITHIN_MARGIN (revision 1)"
    assert verifies[0] == {"night_date": "2026-11-07", "fuel_night": None}
    states = iter(["ABSENT"] * 3)
    ticks.clear()
    with pytest.raises(SystemExit) as refused:
        demo.tick_and_verify([{"site": "KISIWA-001", "date": D("2026-11-07"), "kind": "normal"}])
    assert refused.value.error_code == "ADD_NIGHT_UNEXPECTED" and len(ticks) == 3


def test_kisiwa_stage_reads_the_visited_site() -> None:
    report = {"sites": [{"site_code": "KOBO-001", "stages": {"s3": {"code": "OK"}}},
                        {"site_code": "KISIWA-001", "stages": {"fuel_night": {"code": "OK", "processed": 1}}}]}
    assert dc.kisiwa_stage(report) == (True, {"code": "OK", "processed": 1})
    assert dc.kisiwa_stage({"sites": [{"site_code": "KISIWA-001", "stages": {}}]}) == (False, None)
    assert dc.kisiwa_stage(None) == (False, None)


def test_dry_run_writes_nothing_and_calls_no_child(monkeypatch, tmp_path: Path) -> None:
    story, days_json = build()
    demo = _demo()
    demo.work = tmp_path
    (tmp_path / "days.json").write_text(json.dumps(days_json), encoding="utf-8")
    before = sorted(p.name for p in tmp_path.iterdir())
    monkeypatch.setattr(demo, "story", lambda: story)
    monkeypatch.setattr(demo, "db_now", lambda: LATER)
    monkeypatch.setattr(demo, "site_zones", lambda: ZONES)
    monkeypatch.setattr(demo, "delivered_days", lambda code: set())
    monkeypatch.setattr(demo, "py", lambda *a, **k: pytest.fail("a child was started in --dry-run"))
    out = demo.add_dates("all", dry_run=True)
    assert out["plan"]["order"] and sorted(p.name for p in tmp_path.iterdir()) == before


def test_busy_refuses_before_anything(monkeypatch, tmp_path: Path) -> None:
    story, _ = build()
    demo = _demo()
    demo.work = tmp_path
    (tmp_path / ".busy").write_text("prepare pid=1\n", encoding="utf-8")
    monkeypatch.setattr(demo, "story", lambda: story)
    with pytest.raises(SystemExit, match="another prepare/add-day holds"):
        demo.add_dates("all")


# ---- output ----------------------------------------------------------------------------------------------------------

def test_plain_lines() -> None:
    added = [{"site": "KISIWA-001", "date": D("2026-11-13"), "kind": "normal", "ticket": None},
             {"site": "KISIWA-001", "date": D("2026-11-14"), "kind": "delivery", "ticket": "KIS-DT-20261114"},
             {"site": "KOBO-001", "date": D("2026-11-13"), "kind": "normal"}]
    skipped = [{"site": "KISIWA-001", "date": D("2026-11-15"), "reason": dc.NIGHT_NOT_OVER,
                "text": "the night is not over yet (it ends 15:00 local)"}]
    lines = dc.plain_lines(added, skipped, [], {"COLD-LAB-001": [D("2026-11-12")]})
    assert lines == [
        "KOBO-001: added 13 Nov (normal); checked by the background refresh.",
        "COLD-LAB-001: left empty: 12 Nov.",
        "KISIWA-001: added 13 Nov (normal), 14 Nov (delivery, ticket KIS-DT-20261114) (delivery entered after the "
        "night); both nights checked: within margin; 15 Nov the night is not over yet (it ends 15:00 local)."]


def test_failed_rows_reads_check_json(tmp_path: Path) -> None:
    path = tmp_path / "check.json"
    path.write_text(json.dumps({"rows": {"KIS-1": {"status": "fail"}, "SP-3": {"status": "pass"}}}), encoding="utf-8")
    assert dc.failed_rows(path) == ["KIS-1"] and dc.failed_rows(tmp_path / "none.json") == []


def test_story_links_add_the_two_kisiwa_story_links() -> None:
    """R2-DS1a 1, for a fixed S."""
    story = {**build()[0], "S": "2026-11-06T00:00:00Z", "S_date": "2026-11-06"}
    got = dict(dc.story_links(story, [], None, 5490, {"action": {}}))
    base = "http://localhost:5490"
    assert got["KISIWA-001 Findings, story nights S-9d to S+1d"] == (
        f"{base}/sites/KISIWA-001/findings?from=2026-10-28T00:00:00Z&to=2026-11-08T00:00:00Z")
    assert got["KISIWA-001 Service, story hour S-3d 09:00-10:00Z"] == (
        f"{base}/sites/KISIWA-001/performance/service?from=2026-11-03T09:00:00Z&to=2026-11-03T10:00:00Z")
    assert all(url[len(base):].startswith(dc.LINK_FORMS) for url in got.values())


def test_added_night_links_and_the_live_dip_line() -> None:
    story, _ = build()
    night = D("2026-11-07")
    actions = kis.add_actions(kis.night_start(story["kisiwa"], night), night, "normal")
    entries = [{"night_date": "2026-11-07", "kind": "normal", "status": "DONE", "actions": actions,
                "dips": {"kis-add-20261107-dip-1800": 612, "kis-add-20261107-dip-0600": 540}},
               {"night_date": "2026-11-08", "status": "STARTED"}]
    links = dc.added_night_links(entries, 5490)
    assert links[0] == ("KISIWA-001 Fuel, added night 2026-11-07 (normal)",
                        "http://localhost:5490/sites/KISIWA-001/performance/fuel?night=2026-11-07")
    assert "taken 2026-11-08T06:00, value 540 L" in links[1][0] and len(links) == 2
    assert dc.added_night_links([], 5490) == []


# ---- the KIS rows read the story only (R2-G1 Q3) ---------------------------------------------------------------------

def test_kis_rows_are_bounded_to_the_story_calendar_with_an_added_night() -> None:
    story, _ = build()
    cal = story["kisiwa"]
    added = "2026-11-07"
    windows = [{"night_date": D(r["night_date"])} for r in cal["runs"]] + [{"night_date": D(added)}]
    assert len(rows.kis_story_windows(windows, cal)) == len(cal["runs"]) == 10
    lo, hi = rows.kis_story_range(cal)
    story_record = {"occurred_at": cal["runs"][-1]["start"]}
    added_dip = {"occurred_at": "2026-11-07T15:00:00Z"}
    assert rows.kis_story_records([story_record, added_dip], cal) == [story_record]
    assert hi == dc.at(cal["runs"][-1]["end"]) and lo == dc.at(cal["run1_start"])
    dispatch = [{"finding_id": "a", "episode_start": cal["runs"][2]["start"]},
                {"finding_id": "b", "episode_start": "2026-11-07T20:00:00Z"}]
    assert [r["finding_id"] for r in rows.kis_story_dispatch(dispatch, cal)] == ["a"]
