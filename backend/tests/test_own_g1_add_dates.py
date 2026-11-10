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
    done = {**published, "status": "DONE"}  # H1: only a finished night is built on
    assert kis.plan_night(k, b, [done], D("2026-11-08"), None, LATER)["start_state"] == {"soc": "90", "fuel": "500"}
    assert code(lambda: kis.plan_night(k, b, [published], D("2026-11-08"), None, LATER)) == "NIGHT_NOT_FINISHED"


PUBLISHED_1107 = {"night_date": "2026-11-07", "status": "PUBLISHED", "end_state": {"soc": "90", "fuel": "500"}}


def test_planner_resumes_a_published_night_first() -> None:
    """Must-fail guard (review H1): a night left PUBLISHED is planned first, never stepped over."""
    out = plan(sites=["kisiwa"], entries=[PUBLISHED_1107])["sites"]["kisiwa"]
    assert out["dates"][0] == D("2026-11-07") and out["dates"][:2] == [D("2026-11-07"), D("2026-11-08")]
    done = plan(sites=["kisiwa"], entries=[{**PUBLISHED_1107, "status": "DONE"}])["sites"]["kisiwa"]
    assert done["dates"][0] == D("2026-11-08")  # a DONE night is still the point to continue from
    assert code(lambda: plan(sites=["kisiwa"], entries=[PUBLISHED_1107], date_from=D("2026-11-08"))) == "GAP_NOT_ALLOWED"


def test_child_refuses_a_new_night_while_an_earlier_one_is_published() -> None:
    """Must-fail guard (review H1): nothing builds on a night whose own check did not finish."""
    story, _ = build()
    k, b = story["kisiwa"], _kisiwa_build()
    with pytest.raises(SystemExit) as refused:
        kis.plan_night(k, b, [PUBLISHED_1107], D("2026-11-08"), None, LATER)
    assert refused.value.error_code == "NIGHT_NOT_FINISHED"
    assert "2026-11-07" in str(refused.value) and "--from 2026-11-07" in str(refused.value)
    assert kis.plan_night(k, b, [PUBLISHED_1107], D("2026-11-07"), None, LATER)["resume"] is True


def test_child_refuses_to_resume_a_later_published_night_over_an_earlier_one() -> None:
    """Must-fail guard (review L-A): the stuck-night check runs before the PUBLISHED-resume branch returns."""
    story, _ = build()
    k, b = story["kisiwa"], _kisiwa_build()
    later = {"night_date": "2026-11-08", "status": "PUBLISHED", "end_state": {"soc": "80", "fuel": "400"}}
    with pytest.raises(SystemExit) as refused:
        kis.plan_night(k, b, [PUBLISHED_1107, later], D("2026-11-08"), None, LATER)
    assert refused.value.error_code == "NIGHT_NOT_FINISHED"
    assert "--from 2026-11-07" in str(refused.value)
    assert kis.plan_night(k, b, [PUBLISHED_1107, later], D("2026-11-07"), None, LATER)["resume"] is True


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
    verbs: list[str] = []
    monkeypatch.setattr(demo, "kisiwa_child", lambda verb, *a, **k: verbs.append(verb) or (0, {"preflight": {
        "fuel_stage": True, "entry_status": 422, "entry_code": "OPREC_ENTRY_INVALID"}}, ""))
    monkeypatch.setattr(demo, "py", lambda *a, **k: pytest.fail("a child was started in --dry-run"))
    monkeypatch.setattr(demo, "hold_busy", lambda *a, **k: pytest.fail("--dry-run took .busy"))
    for name in ("drain_mini", "drain", "counts", "tick", "_add_core_day", "add_kisiwa_night", "finish_check"):
        monkeypatch.setattr(demo, name, lambda *a, _n=name, **k: pytest.fail(f"{_n} was called in --dry-run"))
    out = demo.add_dates("all", dry_run=True)
    assert out["plan"]["order"] and sorted(p.name for p in tmp_path.iterdir()) == before
    assert verbs == ["preflight"]  # only the read-only preflight runs


def test_dry_run_runs_the_preflight_refusals_and_writes_nothing(monkeypatch, tmp_path: Path, capsys) -> None:
    story, days_json = build()
    demo = _demo()
    demo.work = tmp_path
    (tmp_path / "days.json").write_text(json.dumps(days_json), encoding="utf-8")
    before = sorted(p.name for p in tmp_path.iterdir())
    monkeypatch.setattr(demo, "story", lambda: story)
    monkeypatch.setattr(demo, "db_now", lambda: LATER)
    monkeypatch.setattr(demo, "site_zones", lambda: ZONES)
    monkeypatch.setattr(demo, "delivered_days", lambda code: set())
    monkeypatch.setattr(demo, "kisiwa_child", lambda verb, *a, **k: (1, None, ""))  # a build with no working child
    with pytest.raises(SystemExit) as refused:
        demo.add_dates("all", dry_run=True)
    assert refused.value.error_code == "BUILD_TOO_OLD"
    assert "add-dates plan" not in capsys.readouterr().out  # no plan is shown for a request the real run refuses
    assert sorted(p.name for p in tmp_path.iterdir()) == before


def test_wk6_calls_study_ending() -> None:
    """Must-fail guard (review L2): wk6 must select the study through `study_ending`, not by the newest study."""
    import inspect
    import demo_combined_finish as fin

    source = inspect.getsource(fin.wk6)
    assert "demo_rows.study_ending(found, ctx.day(1).date().isoformat())" in source and "max(" not in source


# ---- R5.2: settle each date before it is called checked ----------------------------------------------------------------

ZERO = {"KOBO-001": {f: 0 for f in ("dirty", "snapshots_pending", "threads_pending", "mini_deferred",
                                    "opportunity_live")}}
QUEUED = {"KOBO-001": {**ZERO["KOBO-001"], "mini_deferred": 24}}
DONE_RECORD = {"ticks": 2, "log": []}


VISIT = {"outcome": "COMPLETED", "sites": [{"site_code": "KISIWA-001", "stages": {"fuel_night": {"code": "OK"}}}]}


def _loop(monkeypatch, tmp_path: Path, dates: dict, *, counts=ZERO, record=DONE_RECORD, duplicate=False, drain=None,
          report=VISIT):
    """`add_dates` with every child replaced by a recorder; `dates` maps a date to the sites it holds."""
    story, _ = build()
    story = {**story, "sites": ["kobo", "cold", "ev", "kisiwa"]}
    demo = _demo()
    demo.work = tmp_path
    (tmp_path / "days.json").write_text(json.dumps({"days": []}), encoding="utf-8")
    calls: list = []
    sites = [s for s in ("kobo", "kisiwa") if any(s in v for v in dates.values())]
    monkeypatch.setattr(dc, "select_sites", lambda arg, st: sites)
    monkeypatch.setattr(dc, "plan_add_dates", lambda *a, **k: {
        "order": list(dates),
        "sites": {s: {"dates": [d for d, v in dates.items() if s in v], "kind": None, "skipped": [], "no_session": [],
                      "left_empty": {}} for s in sites}})
    monkeypatch.setattr(dc, "preflight_refusal", lambda *a: None)
    monkeypatch.setattr(demo, "story", lambda: story)
    monkeypatch.setattr(demo, "db_now", lambda: LATER)
    monkeypatch.setattr(demo, "site_zones", lambda: ZONES)
    monkeypatch.setattr(demo, "delivered_days", lambda code: set())

    def core(st, site_code, kind, day=None):
        calls.append(("core", site_code))
        if duplicate:
            raise sd.StoryDaysError("DUPLICATE_DAY", "x")
        return {"kind": "normal"}

    def child(verb, *args, **kw):
        calls.append(("child", verb))
        if verb == "preflight":
            return 0, {"preflight": {}}, ""
        if verb == "add-day":
            return 0, {"added": {"kind": "normal", "actions": [], "records": []}}, ""
        entry = {"window": {"revision": 1, "state": "WITHIN_MARGIN"}}
        return 0, {"verified": {"state": "DONE", "line": "x", "entry": entry}}, ""

    def do_drain(name="drain"):
        calls.append(("drain", name))
        if drain is not None:
            raise drain
        return record

    monkeypatch.setattr(demo, "_add_core_day", core)
    monkeypatch.setattr(demo, "kisiwa_child", child)
    monkeypatch.setattr(demo, "tick", lambda *a, **k: calls.append(("tick",)) or report)
    monkeypatch.setattr(demo, "drain_mini", lambda *a, **k: calls.append(("drain_mini",)))
    monkeypatch.setattr(demo, "drain", do_drain)
    monkeypatch.setattr(demo, "counts", lambda: calls.append(("counts",)) or counts)
    monkeypatch.setattr(dc.time, "sleep", lambda s: None)
    monkeypatch.setattr(demo, "finish_check", lambda: calls.append(("finish_check",)) or "PASS")
    return demo, calls


D1, D2 = D("2026-11-07"), D("2026-11-08")


def test_wk6_selects_the_study_by_its_last_day_not_the_newest() -> None:
    found = [{"id": "a", "last_day": "2026-11-06"}, {"id": "b", "last_day": "2026-11-07"},
             {"id": "c", "last_day": "2026-11-08"}]
    assert rows.study_ending(found, "2026-11-07")["id"] == "b"  # max() would return "c"
    with pytest.raises(AssertionError):
        rows.study_ending([found[0], found[2]], "2026-11-07")
    with pytest.raises(AssertionError):
        rows.study_ending([found[1], {"id": "d", "last_day": "2026-11-07"}], "2026-11-07")


def test_kobo_only_date_settles_before_it_is_checked(monkeypatch, tmp_path: Path) -> None:
    demo, calls = _loop(monkeypatch, tmp_path, {D1: ["kobo"]})
    out = demo.add_dates("all")
    assert calls == [("child", "preflight"), ("core", "KOBO-001"), ("drain_mini",), ("drain", "settle-2026-11-07"),
                     ("counts",), ("tick",), ("finish_check",)]  # R6.1: no tick before the drain; one after it
    assert out["added"][0]["checked"] == "settled (2 ticks)" and out["added"][0]["tick_failures"] == []


def test_a_kisiwa_date_verifies_then_drains(monkeypatch, tmp_path: Path) -> None:
    demo, calls = _loop(monkeypatch, tmp_path, {D1: ["kobo", "kisiwa"]})
    out = demo.add_dates("all")
    assert calls == [("child", "preflight"), ("core", "KOBO-001"), ("child", "add-day"), ("drain_mini",), ("tick",),
                     ("child", "verify-day"), ("drain", "settle-2026-11-07"), ("counts",), ("tick",),
                     ("finish_check",)]
    by_site = {a["site"]: a for a in out["added"]}
    assert by_site["KOBO-001"]["checked"] == "settled (2 ticks)"
    assert by_site["KISIWA-001"]["checked"] == "WITHIN_MARGIN (revision 1)"


def test_date_major_order_is_kept_with_a_drain_between_dates(monkeypatch, tmp_path: Path) -> None:
    demo, calls = _loop(monkeypatch, tmp_path, {D1: ["kobo", "kisiwa"], D2: ["kobo", "kisiwa"]})
    demo.add_dates("all")
    first_drain = calls.index(("drain", "settle-2026-11-07"))
    second_child = calls.index(("child", "add-day"), calls.index(("child", "add-day")) + 1)
    assert first_drain < second_child
    assert calls.count(("drain", "settle-2026-11-08")) == 1


def test_a_failed_drain_stops_the_command(monkeypatch, tmp_path: Path) -> None:
    demo, calls = _loop(monkeypatch, tmp_path, {D1: ["kobo", "kisiwa"], D2: ["kobo", "kisiwa"]},
                        drain=SystemExit("DRAIN FAILED: settle-2026-11-07: past 2N"))
    with pytest.raises(SystemExit) as stopped:
        demo.add_dates("all")
    text = str(stopped.value)
    assert text.startswith("KOBO-001, KISIWA-001 2026-11-07: the added data did not finish processing; DRAIN FAILED")
    assert text.endswith("prepare a fresh build before a demo.")
    assert calls.count(("child", "add-day")) == 1 and ("finish_check",) not in calls
    assert not (tmp_path / ".busy").exists()


def test_a_stopped_command_prints_the_dates_already_added(monkeypatch, tmp_path: Path, capsys) -> None:
    demo, calls = _loop(monkeypatch, tmp_path, {D1: ["kobo"], D2: ["kobo"]})
    real = demo.drain

    def second_fails(name="drain"):
        if name == "settle-2026-11-08":
            raise SystemExit("DRAIN FAILED: settle-2026-11-08: past 2N")
        return real(name)

    monkeypatch.setattr(demo, "drain", second_fails)
    with pytest.raises(SystemExit):
        demo.add_dates("all")
    out = capsys.readouterr().out
    assert "The command stopped. These dates were already added and settled:" in out
    tail = out.split("The command stopped.")[1]
    assert "added 7 Nov" in tail and "8 Nov" not in tail


def test_a_mini_depth_failure_in_a_settle_gets_the_drain_wording(monkeypatch, tmp_path: Path) -> None:
    demo, calls = _loop(monkeypatch, tmp_path, {D1: ["kobo"]})

    def failing() -> None:
        raise SystemExit("mini-depth FAILED: [{'job': 1}]")

    monkeypatch.setattr(demo, "drain_mini", failing)
    with pytest.raises(SystemExit) as stopped:
        demo.add_dates("all")
    text = str(stopped.value)
    assert text.startswith("KOBO-001 2026-11-07: the added data did not finish processing; mini-depth FAILED")
    assert text.endswith("prepare a fresh build before a demo.") and ("finish_check",) not in calls
    assert not (tmp_path / ".busy").exists()


def test_no_check_still_settles(monkeypatch, tmp_path: Path) -> None:
    demo, calls = _loop(monkeypatch, tmp_path, {D1: ["kobo"]})
    demo.add_dates("all", no_check=True)
    assert ("drain_mini",) in calls and ("drain", "settle-2026-11-07") in calls and ("finish_check",) not in calls
    assert ("tick",) not in calls  # R6.1: no tick of its own under --no-check


def test_nothing_added_and_nothing_pending_does_not_settle(monkeypatch, tmp_path: Path) -> None:
    """Must-fail guard (R6.1): with the closing tick removed this fails."""
    demo, calls = _loop(monkeypatch, tmp_path, {D1: ["kobo"]}, duplicate=True)
    demo.add_dates("all")
    assert calls == [("child", "preflight"), ("core", "KOBO-001"), ("counts",), ("tick",), ("finish_check",)]


def test_closing_tick_retries_while_kisiwa_is_not_visited(monkeypatch, tmp_path: Path) -> None:
    demo, calls = _loop(monkeypatch, tmp_path, {D1: ["kobo"]}, duplicate=True, report={"outcome": "COMPLETED", "sites": []})
    demo.add_dates("all")
    assert calls[-4:] == [("tick",), ("tick",), ("tick",), ("finish_check",)]  # the closing tick plus two extra


def test_work_left_by_an_earlier_run_is_settled_at_the_end(monkeypatch, tmp_path: Path) -> None:
    demo, calls = _loop(monkeypatch, tmp_path, {D1: ["kobo"]}, duplicate=True, counts=QUEUED)
    demo.add_dates("all")
    assert calls == [("child", "preflight"), ("core", "KOBO-001"), ("counts",), ("drain_mini",), ("drain", "settle-close"),
                     ("tick",), ("finish_check",)]


def test_tick_failures_are_carried_and_do_not_stop_the_command(monkeypatch, tmp_path: Path, capsys) -> None:
    failure = {"site": "KOBO-001", "stage": "mini"}
    demo, calls = _loop(monkeypatch, tmp_path, {D1: ["kobo"]},
                        record={"ticks": 2, "log": [{"tick": 1, "tick_failure": failure}, {"tick": 2}]})
    out = demo.add_dates("all")
    assert out["added"][0]["tick_failures"] == [failure] and ("finish_check",) in calls
    assert "(a background step reported a failure; see logs)" in capsys.readouterr().out


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


# ---- DATA-1 (D-E5.30): Kisiwa's added nights continue the Site's one recording session --------------------------------

def _fake_gateway(monkeypatch) -> list[dict]:
    """The real `add_night` / `_publish_night` with the database, the simulator and the gateway replaced: each
    `_publish_and_accept` call is recorded (its night folder, epoch and gateway state)."""
    from types import SimpleNamespace

    import execution_adapter
    import pg_harness
    import probe_kisiwa_nights as nights
    import test_s6_verification_replay as rp
    from assetops_backend.sites.adapters import postgres_foundation_store as pfs

    calls: list[dict] = []
    run = SimpleNamespace(execution_status="READY", registered_basis=object(), run_id="run-fake", blocking_reasons=())
    reg = SimpleNamespace(draft=lambda *a, **k: run, sim=lambda version: None)
    stocks = {nights.SOC: Fraction(90), nights.FUEL: Fraction(500)}
    trajectory = SimpleNamespace(boundaries=[SimpleNamespace(stocks=stocks)] * 400)
    monkeypatch.setattr(kis, "story_registered", lambda *a, **k: reg)
    monkeypatch.setattr(kis, "_db_now", lambda url: LATER)
    monkeypatch.setattr(kis, "_wait", lambda url, entry: None)
    monkeypatch.setattr(pfs, "PostgresFoundationStore", lambda url: object())
    monkeypatch.setattr(pg_harness, "dispose", lambda *a, **k: None)
    monkeypatch.setattr(nights, "day_document", lambda *a, **k: {})
    monkeypatch.setattr(execution_adapter, "run_to_end", lambda *a, **k: SimpleNamespace(trajectory=trajectory))
    monkeypatch.setattr(rp, "_publish_and_accept", lambda tmp, run_, epoch, received, *, gateway_dir=None, keep=None:
                        calls.append({"tmp": tmp, "epoch": epoch, "gateway_dir": gateway_dir, "keep": keep})
                        or {"batches": 1})
    monkeypatch.setenv(kis.ENTRY_ENV, "on")
    return calls


def _kisiwa_work(tmp_path: Path) -> Path:
    story, _ = build()
    (tmp_path / "story.json").write_text(json.dumps(story), encoding="utf-8")
    (tmp_path / "kisiwa.json").write_text(json.dumps(_kisiwa_build()), encoding="utf-8")
    return tmp_path


def _finish(work: Path, night: str) -> None:
    """What `verify-day` leaves behind: the night's entry DONE."""
    kis.write_days(work, [{**e, "status": "DONE"} if e["night_date"] == night else e for e in kis.read_days(work)])


def _added_nights(monkeypatch, tmp_path: Path) -> tuple[Path, list[dict]]:
    calls = _fake_gateway(monkeypatch)
    monkeypatch.setattr(kis, "_post_records", lambda *a, **k: [])
    work = _kisiwa_work(tmp_path)
    for night in ("2026-11-07", "2026-11-08", "2026-11-09"):
        kis.add_night("postgresql://fake", work, {"night_date": night, "kind": None})
        _finish(work, night)
    return work, calls


def test_data1_every_added_night_continues_one_session_on_one_gateway_state(monkeypatch, tmp_path: Path) -> None:
    """D-E5.30: three added nights publish on one epoch through the Site's one gateway state `work/kisiwa-gateway`
    (the same as the story build's, so the sequence continues across processes); each keeps its own night folder."""
    work, calls = _added_nights(monkeypatch, tmp_path)
    assert len(calls) == 3
    assert len({c["epoch"] for c in calls}) == 1, [c["epoch"] for c in calls]
    assert {c["gateway_dir"] for c in calls} == {work / "kisiwa-gateway"}, [c["gateway_dir"] for c in calls]
    assert len({c["tmp"] for c in calls}) == 3


def test_data1_a_calendar_day_spanning_two_nights_resolves_to_one_session(monkeypatch, tmp_path: Path) -> None:
    """D-E5.30: 8 Nov (Site-local) holds night 7 Nov's 00:00-12:00 and night 8 Nov's 18:00-24:00. With the epochs
    the tool publishes them under, the dispatch cohort for that day is SELECTED_UNIQUE, not AMBIGUOUS."""
    from uuid import UUID, uuid4

    from assetops_backend.analytics.assessment_inputs import AcceptedReading, Window
    from assetops_backend.analytics.cohort import select_cohort

    _, calls = _added_nights(monkeypatch, tmp_path)
    by_night = dict(zip(("2026-11-07", "2026-11-08"), (c["epoch"] for c in calls)))
    gateway, source = UUID(int=1), UUID(int=2)

    def reading(when: datetime, epoch: str, seq: int) -> AcceptedReading:
        return AcceptedReading(
            evidence_id=uuid4(), envelope_sha256=f"sha-{seq}", batch_id=UUID(int=9), gateway_id=gateway,
            source_id=source, sequence_epoch=epoch, sequence=seq, role="battery-soc", asset_id=UUID(int=3),
            source_time=when, interval_start=None, interval_end=None, published_at=when, received_at=when,
            accepted_at=when, quality="GOOD", value="90", unit="%", foundation_revision_id=UUID(int=4),
            binding_set_revision_id=UUID(int=5), binding_revision_id=UUID(int=6), source_mode="SIMULATED")

    day = Window(datetime(2026, 11, 7, 21, 0, tzinfo=timezone.utc), datetime(2026, 11, 8, 21, 0, tzinfo=timezone.utc))
    morning = datetime(2026, 11, 8, 6, 0, tzinfo=timezone.utc)  # 09:00 local, night 7 Nov
    evening = datetime(2026, 11, 8, 16, 0, tzinfo=timezone.utc)  # 19:00 local, night 8 Nov
    got = select_cohort((reading(morning, by_night["2026-11-07"], 200), reading(evening, by_night["2026-11-08"], 201)),
                        day)
    assert got.status == "SELECTED_UNIQUE", (got.status, got.reason)


def _night_readings(start: datetime, end: datetime, epoch: str, keep, first_seq: int) -> list:
    """One night's battery-soc readings as the simulator emits them: every 5 minutes from its start to its end, both
    instants included (so consecutive nights both emit their shared boundary), filtered by the `keep` the tool
    passed to `_publish_and_accept` (None sends all), numbered on the session in publish order."""
    from uuid import UUID, uuid4

    from assetops_backend.analytics.assessment_inputs import AcceptedReading

    out, t = [], start
    while t <= end:
        if keep is None or keep(t.strftime("%Y-%m-%dT%H:%M:%SZ")):
            seq = first_seq + len(out)
            out.append(AcceptedReading(
                evidence_id=uuid4(), envelope_sha256=f"sha-{epoch}-{seq}", batch_id=UUID(int=9), gateway_id=UUID(int=1),
                source_id=UUID(int=2), sequence_epoch=epoch, sequence=seq, role="battery-soc", asset_id=UUID(int=3),
                source_time=t, interval_start=None, interval_end=None, published_at=t, received_at=t, accepted_at=t,
                quality="GOOD", value="90", unit="%", foundation_revision_id=UUID(int=4),
                binding_set_revision_id=UUID(int=5), binding_revision_id=UUID(int=6), source_mode="SIMULATED"))
        t += timedelta(minutes=5)
    return out


def _boundary_cohort(calls: list[dict], kisiwa: dict, *, honour_keep: bool):
    """Nights 7 and 8 Nov published as the recorded calls say, and the dispatch cohort of the UTC day holding their
    shared boundary instant (night 7 Nov's end = night 8 Nov's start)."""
    from assetops_backend.analytics.assessment_inputs import Window
    from assetops_backend.analytics.cohort import select_cohort

    readings: list = []
    for call, night in zip(calls, (D("2026-11-07"), D("2026-11-08"))):
        readings += _night_readings(kis.night_start(kisiwa, night), kis.night_end(kisiwa, night), call["epoch"],
                                    call["keep"] if honour_keep else None, len(readings) + 1)
    boundary = kis.night_end(kisiwa, D("2026-11-07")).astimezone(timezone.utc)
    lo = boundary.replace(hour=0, minute=0)
    window = Window(lo, lo + timedelta(days=1))
    inside = tuple(r for r in readings if lo - timedelta(hours=1) <= r.source_time < lo + timedelta(days=1, hours=1))
    return select_cohort(inside, window), sum(r.source_time == boundary for r in inside), boundary


def test_data1_a_shared_boundary_instant_is_published_once_on_the_session(monkeypatch, tmp_path: Path) -> None:
    """DATA-1 fix H1: consecutive nights share their boundary instant (night 7 Nov ends where night 8 Nov starts) and
    the simulator emits it in both. On one epoch two readings at one instant are a REPORTS_OVERLAP (`cohort.py`
    `series_limits`), which dispatch answers AMBIGUOUS_SERIES. With the `keep` `add_night` passes, the boundary is
    published once and the day's cohort has no overlap limit; sending both nights whole (the control) does."""
    work, calls = _added_nights(monkeypatch, tmp_path)
    kisiwa = json.loads((work / "story.json").read_text(encoding="utf-8"))["kisiwa"]
    got, at_boundary, boundary = _boundary_cohort(calls[:2], kisiwa, honour_keep=True)
    assert got.status == "SELECTED_UNIQUE", (got.status, got.reason)
    assert at_boundary == 1, (boundary, at_boundary)
    assert [x.kind for x in got.limits if x.kind == "REPORTS_OVERLAP"] == [], got.limits
    control, twice, _ = _boundary_cohort(calls[:2], kisiwa, honour_keep=False)
    assert twice == 2 and any(x.kind == "REPORTS_OVERLAP" and x.start == boundary for x in control.limits), (
        twice, control.limits)
    # the first added night continues after the story's last night, so its own start is not sent again
    first = kis.night_start(kisiwa, D("2026-11-07"))
    assert calls[0]["keep"] is not None and calls[0]["keep"](first.strftime("%Y-%m-%dT%H:%M:%SZ")) is False
    assert calls[0]["keep"]((first + timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")) is True


def test_data1_resume_after_an_interrupted_night_publishes_once_on_the_same_session(monkeypatch,
                                                                                    tmp_path: Path) -> None:
    """D-E5.30 with R1 step 9: a night interrupted after its readings (PUBLISHED, records not posted) resumes without
    publishing again; the next night then continues the same session on the same gateway state."""
    calls = _fake_gateway(monkeypatch)
    work = _kisiwa_work(tmp_path)

    def interrupted(*a, **k):
        raise RuntimeError("interrupted before the records")

    monkeypatch.setattr(kis, "_post_records", interrupted)
    with pytest.raises(RuntimeError):
        kis.add_night("postgresql://fake", work, {"night_date": "2026-11-07", "kind": None})
    assert [e["status"] for e in kis.read_days(work)] == ["PUBLISHED"] and len(calls) == 1
    monkeypatch.setattr(kis, "_post_records", lambda *a, **k: [{"code": "R-1"}])
    resumed = kis.add_night("postgresql://fake", work, {"night_date": "2026-11-07", "kind": None})
    assert resumed["records"] == [{"code": "R-1"}] and len(calls) == 1  # resumed at step 5, never republished
    _finish(work, "2026-11-07")
    kis.add_night("postgresql://fake", work, {"night_date": "2026-11-08", "kind": None})
    assert len(calls) == 2 and calls[0]["epoch"] == calls[1]["epoch"], [c["epoch"] for c in calls]
    assert calls[0]["gateway_dir"] == calls[1]["gateway_dir"] == work / "kisiwa-gateway"
