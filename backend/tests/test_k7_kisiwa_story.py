"""DIESEL-1 K7-D L0 (ruling DIESEL-1-R3l §9l.3): the Kisiwa story days in the demo prepare. No database.

Imports the tools as the K3 tests do. Every "must fail" names its mutation.
"""

from __future__ import annotations

import copy
import functools
import hashlib
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
for extra in (REPO / "tools", REPO / "backend" / "tests", REPO / "host" / "tests", REPO / "host"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

import demo_combined as dc  # noqa: E402
import demo_combined_kisiwa as kis  # noqa: E402
import demo_combined_rows as rows  # noqa: E402
from k7_story_pins import THREE_SITE_STORY_PINS  # noqa: E402

S = datetime(2026, 11, 6, tzinfo=timezone.utc)  # the story day of a prepare whose DB now is 2026-11-08 (S = floor - 2 d)
DB_NOW = datetime(2026, 11, 8, 10, 0, tzinfo=timezone.utc)


def _at(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def _day(n: int, hh: int = 0, mm: int = 0) -> datetime:
    return S + timedelta(days=n, hours=hh, minutes=mm)


@functools.lru_cache(maxsize=1)
def calendar() -> dict:
    return kis.resolve(S)


@functools.lru_cache(maxsize=1)
def derived() -> tuple[str, dict]:
    return kis.derived_log(kis.BASE_LOG.read_text(encoding="utf-8"), calendar())


def base_actions() -> list[dict]:
    return kis.parse_log(kis.BASE_LOG.read_text(encoding="utf-8"))["actions"]


def story_runs(k: dict | None = None) -> list[tuple[datetime, datetime]]:
    return [(_at(r["start"]), _at(r["end"])) for r in (k or calendar())["runs"]]


# ---- 1. the three-Site story stays byte-equal ---------------------------------------------------------------------

@pytest.mark.parametrize("db_now, sha, length, S", THREE_SITE_STORY_PINS)
def test_1_three_site_story_is_byte_equal(db_now: str, sha: str, length: int, S: str) -> None:
    """Must fail if any core loop iterates `SITES` (with Kisiwa in it) or Kisiwa leaks into a three-Site story."""
    story = dc.resolve_story(_at(db_now))
    text = json.dumps(story, indent=2)
    assert story["S"] == S
    assert (hashlib.sha256(text.encode("utf-8")).hexdigest(), len(text)) == (sha, length)


# ---- 2. Kisiwa resolve ------------------------------------------------------------------------------------------

def test_2_the_story_calendar_for_a_fixed_S() -> None:
    """§9l.3's table: night 1 = S-9d, each run 12:00Z to 12:00Z, received +10, assessed +30, raised +31; the move
    is 27 whole days and the story log is named by night 1's local date."""
    k = calendar()
    assert (k["delta_days"], k["story_log_id"], k["log_version"]) == (27, "kisiwa-001-story-20261028", 1)
    assert (k["import_at"], k["install_at"], k["setup_at"]) == tuple(
        dc.iso(_day(-11, h, m)) for h, m in ((9, 0), (9, 30), (11, 0)))
    for r in k["runs"]:
        n = r["k"]
        assert r["night_date"] == _day(n - 10).date().isoformat()
        assert (r["start"], r["end"]) == (dc.iso(_day(n - 10, 12)), dc.iso(_day(n - 9, 12)))
        assert (r["received_at"], r["assessed_at"], r["raised_at"]) == tuple(
            dc.iso(_day(n - 9, 12, m)) for m in (10, 30, 31))
    chain = dict(kis.order_chain(k))
    assert chain["night 4 raise"] == _day(-5, 12, 31) and chain["action.raised_at"] == _day(-5, 13)  # 16:00 local
    assert chain["night 6 window start"] == _day(-4, 15)  # 18:00 local
    assert chain["night 8 assessed"] == _day(-1, 12, 30) and chain["run 10 received"] == _day(1, 12, 10)
    assert _at(k["runs"][3]["start"]) + timedelta(hours=3) >= _day(-6) and _day(-6) <= _day(1)  # in the story week
    moved = {a["action_id"]: a for a in derived()[1]["actions"]}
    assert moved["kis-delivery-1"]["at"] == dc.iso(_day(-7, 7))
    assert (moved["kis-removal-1"]["at"], moved["kis-removal-1"]["sensor_disconnected"]["at"]) == (
        dc.iso(_day(-6, 22)), dc.iso(_day(-6, 21, 50)))
    assert moved["kis-dip-n4-0700"]["at"] == dc.iso(_day(-5, 4))
    assert moved["kis-sealed-1"]["at"] == moved["kis-sensor-power-1"]["at"] == dc.iso(_day(-4, 12))


def test_2_night_window_matches_the_product_rule() -> None:
    from assetops_backend.fuel_balance.rules import night_window

    for r in calendar()["runs"]:
        night = date.fromisoformat(r["night_date"])
        assert kis.night_opens(night) == night_window(night, kis.ZONE)[0]


def test_2_half_day_move_is_stop_s1() -> None:
    """Must fail if the whole-day guard is removed."""
    doc = kis.load_story_doc()
    doc["run1_start"] = "S-9d 00:00"
    with pytest.raises(dc.StoryClockError, match="STORY_SHIFT_NOT_WHOLE_DAYS"):
        kis.resolve(S, doc)


def test_2_four_installs_are_distinct_ordered_and_lead_run_1() -> None:
    story = dc.resolve_story(DB_NOW, kisiwa=True)
    assert story["install_order"] == ["kobo", "cold", "ev", "kisiwa"]
    assert list(story["installs"]) == ["kobo", "cold", "ev"]  # the three core Sites only
    assert story["kisiwa"] == kis.resolve(_at(story["S"]))
    for install in ("S-29d 11:00", "S-26d 06:15", "S-9d 11:30"):  # Kobo's instant, before EV, under the 1 h lead
        doc = kis.load_story_doc()
        doc["install_at"] = install
        with pytest.raises(dc.StoryClockError, match="INSTALL_CLOCK_CONFLICT"):
            dc.resolve_story(DB_NOW, kisiwa=True, kisiwa_doc=doc)


def test_2_every_adjacent_pair_swapped_is_stop_s2() -> None:
    """Must fail if the order check skips any pair."""
    chain = kis.order_chain(calendar())
    kis.check_order(chain)
    for i in range(len(chain) - 1):
        swapped = list(chain)
        (a, ta), (b, tb) = swapped[i], swapped[i + 1]
        swapped[i], swapped[i + 1] = (a, tb), (b, ta)
        with pytest.raises(dc.StoryClockError, match="STORY_CLOCK_ORDER"):
            kis.check_order(swapped)


def test_2_resolve_applies_the_order_check_and_its_side_conditions() -> None:
    doc = kis.load_story_doc()
    doc["action"]["assign_at"], doc["action"]["request"]["occurred_at"] = "S-5d 13:10", "S-5d 13:20"
    with pytest.raises(dc.StoryClockError, match="STORY_CLOCK_ORDER"):
        kis.resolve(S, doc)
    doc = kis.load_story_doc()
    doc["action"]["effective_at"] = "S-4d 12:01"
    with pytest.raises(dc.StoryClockError, match="STORY_CLOCK_ORDER"):
        kis.resolve(S, doc)


# ---- 3. the derived log -----------------------------------------------------------------------------------------

def test_3_derived_log_moves_only_the_instants() -> None:
    text, doc = derived()
    base = base_actions()
    strip = lambda a: {k: v for k, v in a.items() if k != "at"} | (  # noqa: E731
        {"sensor_disconnected": {k: v for k, v in a["sensor_disconnected"].items() if k != "at"}}
        if "sensor_disconnected" in a else {})
    assert [strip(a) for a in doc["actions"]] == [strip(a) for a in base]
    for moved, orig in zip(doc["actions"], base):
        assert _at(moved["at"]) - _at(orig["at"]) == timedelta(days=27)
        assert len(moved["at"]) == 20 and moved["at"].endswith("Z")
        if "sensor_disconnected" in orig:
            assert _at(moved["sensor_disconnected"]["at"]) - _at(orig["sensor_disconnected"]["at"]) == timedelta(27)
    assert (doc["log_id"], doc["log_version"], doc["site_code"], doc["timezone"]) == (
        "kisiwa-001-story-20261028", 1, "KISIWA-001", "Africa/Dar_es_Salaam")
    lines = text.split("\n")
    assert all(line.startswith("# ") for line in lines[:4]) and lines[4] == "{"
    assert "77777c82d82298ffba77a130f8d9ea2c6bb9a80c491ba4b2ac5248c4b735b634" in lines[2] and "27 whole days" in lines[2]
    assert "\r" not in text and text.endswith("}\n")
    assert kis.parse_log(text) == doc


def test_3_a_changed_shipped_log_is_stop_s3() -> None:
    """Must fail if the base hash check is removed."""
    with pytest.raises(SystemExit, match="BASE_LOG_CHANGED"):
        kis.derived_log(kis.BASE_LOG.read_text(encoding="utf-8") + "# edited\n", calendar())


@functools.lru_cache(maxsize=1)
def memory_kisiwa():
    """KISIWA-001 registered in memory at the story's import and install instants (K1's fixture path)."""
    from foundation_fakes import InMemoryFoundationStore

    store = InMemoryFoundationStore()
    k = calendar()
    kis.register_in(store, _at(k["import_at"]), _at(k["install_at"]))
    return store


def _story_draft(tmp_path: Path, k: int, text: str | None = None):
    import probe_kisiwa_nights as nights
    from fractions import Fraction

    from assetops_backend.runs.adapters.yaml_operational_action_log import YamlOperationalActionLog

    cal = calendar()
    path = kis.write_derived_log(tmp_path, derived()[0] if text is None else text, cal)
    reg = kis.story_registered(memory_kisiwa(), cal["setup_at"], cal["run1_start"],
                               YamlOperationalActionLog(root=path.parent))
    state = kis.load_handover()["runs"][k - 1]["start"]
    r = cal["runs"][k - 1]
    run = reg.draft(nights.day_document(float(Fraction(state["soc"])), float(Fraction(state["fuel"]))),
                    r["start"], r["end"], "v7", {"log_id": cal["story_log_id"], "log_version": 1})
    return run, reg, path


@pytest.mark.parametrize("k, ids", [(2, ["kis-delivery-1"]), (4, ["kis-removal-1"])])
def test_3_k0_freezes_the_derived_log(tmp_path, k: int, ids: list[str]) -> None:
    run, _, path = _story_draft(tmp_path, k)
    identity = run.deterministic_identity
    assert run.execution_status == "READY" and run.registered_basis is not None
    assert [e.split(":")[1] for e in identity.intervention_history] == ids
    log = identity.operational_action_log
    assert (log.log_id, log.log_version, log.sha256) == (
        "kisiwa-001-story-20261028", 1, kis.lf_sha256(path.read_text(encoding="utf-8")))


def test_3_k0_refuses_the_v1_id_under_the_story_name(tmp_path) -> None:
    """Must fail if the derived log keeps v1's `log_id`."""
    from assetops_backend.runs.refusals import RunSetupRefused

    text = derived()[0].replace('"log_id": "kisiwa-001-story-20261028"', '"log_id": "kisiwa-001-operational-actions"')
    with pytest.raises(RunSetupRefused) as refused:
        _story_draft(tmp_path, 2, text)
    assert refused.value.kind == "OPERATIONAL_ACTION_LOG_MISMATCH"


# ---- the S-5 guards on every run, in memory (physics, dips, history; the scratch prepare repeats them) -------------

@pytest.mark.parametrize("k", range(1, 11))
def test_run_guards_hold_for_every_story_run(tmp_path, k: int) -> None:
    """The whole-day move keeps F0's physics and dips exactly (§9l.1 item 2); any difference is stop S-5."""
    run, reg, path = _story_draft(tmp_path, k)
    _, doc = derived()
    placed = kis.straddle_check(doc["actions"], story_runs())
    out = kis.run_guards(run, reg, k, kis.load_handover(), doc["actions"], placed,
                         kis.lf_sha256(path.read_text(encoding="utf-8")), calendar())
    print(f"K7 run {k}: history {[e.split(':')[1] for e in out['history']]} physics {out['physics']} "
          f"dips {out['dips']}")
    assert out["physics"]["equal"]
    want_dips = sorted(a for a, n in placed.items() if n == k and a.startswith("kis-dip"))
    assert sorted(d["action_id"] for d in out["dips"]) == want_dips


def test_run_guard_physics_fails_on_a_changed_start_state(tmp_path) -> None:
    """Must fail: a run started from another state does not end where F0's run ended (the guard is not vacuous)."""
    run, reg, path = _story_draft(tmp_path, 3)
    handover = copy.deepcopy(kis.load_handover())
    handover["runs"][2]["end"]["fuel"] = "600"
    _, doc = derived()
    with pytest.raises(SystemExit, match="RUN_GUARD_PHYSICS"):
        kis.run_guards(run, reg, 3, handover, doc["actions"], kis.straddle_check(doc["actions"], story_runs()),
                       kis.lf_sha256(path.read_text(encoding="utf-8")), calendar())


# ---- 4. straddle --------------------------------------------------------------------------------------------------

def test_4_base_log_against_f0_runs_passes() -> None:
    base_runs = [(_at("2026-10-01T12:00:00Z") + timedelta(days=n), _at("2026-10-02T12:00:00Z") + timedelta(days=n))
                 for n in range(10)]
    placed = kis.straddle_check(base_actions(), base_runs)
    assert (placed["kis-delivery-1"], placed["kis-removal-1"], placed["kis-dip-n4-0700"], placed["kis-sealed-1"]) == (
        2, 4, 4, 6)
    assert kis.straddle_check(derived()[1]["actions"], story_runs()) == placed


def test_4_a_dip_at_the_last_run_end_and_a_crossing_removal_fail() -> None:
    runs = story_runs()
    dip = {"action_id": "x-dip", "kind": "TANK_DIP", "at": dc.iso(runs[-1][1])}
    with pytest.raises(SystemExit, match="ACTION_STRADDLES_RUN"):
        kis.straddle_check([dip], runs)
    removal = copy.deepcopy(next(a for a in derived()[1]["actions"] if a["kind"] == "FUEL_REMOVAL_UNRECORDED"))
    removal["at"] = dc.iso(runs[4][0] - timedelta(minutes=20))  # 45 min crossing run 5's start
    removal.pop("sensor_disconnected")
    with pytest.raises(SystemExit, match="ACTION_STRADDLES_RUN"):
        kis.straddle_check([removal], runs)
    sensor = copy.deepcopy(next(a for a in derived()[1]["actions"] if a["kind"] == "FUEL_REMOVAL_UNRECORDED"))
    sensor["sensor_disconnected"]["at"] = dc.iso(runs[4][0] - timedelta(minutes=10))
    with pytest.raises(SystemExit, match="ACTION_STRADDLES_RUN"):
        kis.straddle_check([sensor], runs)


# ---- 5. injector bodies -------------------------------------------------------------------------------------------

def _posts() -> dict[str, dict | None]:
    dips = {d["action_id"]: d["dip_l"] for d in kis.load_handover()["dips"]}
    return {a["action_id"]: kis.record_post(a, calendar(), dips) for a in derived()[1]["actions"]}


def test_5_injector_bodies_match_their_literals() -> None:
    posts = _posts()
    d = posts["kis-delivery-1"]
    assert (d["kind"], d["body"], d["quantity"], d["unit"], d["key"]) == (
        "FUEL_DELIVERY", "Fuel delivery of 300 L received, ticket KIS-DT-0001.", "300", "L", "kisiwa-kis-delivery-1")
    assert d["source_document_sha256"] == hashlib.sha256(b"Fuel delivery ticket KIS-DT-0001, 300 L").hexdigest()
    assert (d["occurred_at"], d["recorded_at"]) == (dc.iso(_day(-7, 7)), dc.iso(_day(-7, 7, 30)))
    n4 = posts["kis-dip-n4-0700"]
    assert (n4["kind"], n4["body"], n4["quantity"], n4["key"]) == (
        "TANK_DIP", "Tank dip at the 07:00 round: 706 L.", "706", "kisiwa-kis-dip-n4-0700")
    assert (n4["occurred_at"], n4["recorded_at"]) == (dc.iso(_day(-5, 4)), dc.iso(_day(-5, 4, 15)))
    assert posts["kis-dip-r6-1800"]["body"].startswith("Tank dip at the 18:00 round: ")
    assert posts["kis-removal-1"] is None and posts["kis-sealed-1"] is None and posts["kis-sensor-power-1"] is None
    visit = kis.site_visit_post(calendar(), "case-1")
    assert (visit["kind"], visit["body"], visit["key"], visit["case_id"], visit["quantity"]) == (
        "SITE_VISIT", "Tank cap sealed; tank sensor moved to its own protected supply.", "kisiwa-kis-sealed-1",
        "case-1", None)
    assert (visit["occurred_at"], visit["recorded_at"]) == (dc.iso(_day(-4, 12)), dc.iso(_day(-4, 12, 15)))
    assert sum(1 for p in posts.values() if p and p["kind"] == "TANK_DIP") == 11


# ---- 6. timeline order --------------------------------------------------------------------------------------------

def test_6_timeline_orders_records_before_publishes_and_assess_before_raise() -> None:
    posts = [p for p in _posts().values() if p]
    events = kis.timeline(calendar(), posts)
    assert [e[0] for e in events] == sorted(e[0] for e in events)
    position = {(e[2], e[3]["key"] if e[2] == "record" else e[3]): i for i, e in enumerate(events)}
    placed = kis.straddle_check(derived()[1]["actions"], story_runs())
    for p in posts:
        k = placed[p["key"].removeprefix("kisiwa-")]
        assert position[("record", p["key"])] < position[("publish", k)], p["key"]
    for k in range(1, 11):
        assert position[("publish", k)] < position[("assess", k)] < position[("raise", k)]
    tie = kis.timeline(calendar(), [{**posts[0], "recorded_at": calendar()["runs"][1]["received_at"]}])
    same = [e[2] for e in tie if e[0] == _at(calendar()["runs"][1]["received_at"])]
    assert same == ["record", "publish"]


# ---- 7. handover --------------------------------------------------------------------------------------------------

def test_7_handover_is_the_projection_of_the_committed_result() -> None:
    import probe_kisiwa_fuel as probe

    result_text = probe.RESULT.read_text(encoding="utf-8")
    assert kis.HANDOVER_FILE.read_text(encoding="utf-8") == probe.handover_text(result_text)
    assert probe.handover_current(result_text)
    h = kis.load_handover()
    assert (len(h["runs"]), len(h["dips"]), len(h["nights"])) == (10, 11, 10)
    assert h["source"]["actions_sha256"] == "77777c82d82298ffba77a130f8d9ea2c6bb9a80c491ba4b2ac5248c4b735b634"
    assert h["nights"][3]["readings"]["state"] == "UNEXPLAINED" and h["nights"][3]["night_date"] == "2026-10-04"


def test_7_a_one_character_change_makes_check_fail(tmp_path) -> None:
    """Must fail if `--check` stops comparing the handover."""
    import probe_kisiwa_fuel as probe

    result_text = probe.RESULT.read_text(encoding="utf-8")
    changed = tmp_path / "handover.json"
    changed.write_text(kis.HANDOVER_FILE.read_text(encoding="utf-8").replace('"dip_l": 706', '"dip_l": 707'),
                       encoding="utf-8")
    assert not probe.handover_current(result_text, changed)


# ---- 8. prepare paths ---------------------------------------------------------------------------------------------

@pytest.mark.parametrize("sites, after", [(["kobo", "cold", "ev"], True), (["kobo", "cold", "ev", "kisiwa"], True),
                                          (["kisiwa"], False)])
def test_8_finish_build_after_children_path(monkeypatch, sites: list[str], after: bool) -> None:
    demo = dc.Demo("assetops_demo3_kisiwa_test", "var/demo3_kisiwa")
    called: list[str] = []
    monkeypatch.setattr(demo, "after_children", lambda story, days: called.append("after") or {})
    monkeypatch.setattr(demo, "finish", lambda story, steps=None: called.append("finish"))
    monkeypatch.setattr(demo, "raise_deferred_drain", lambda: None)
    demo.finish_build({"sites": sites}, [], True, {}, {})
    assert called == (["after", "finish"] if after else ["finish"])


def test_8_objectives_never_see_kisiwa_and_links_use_route_forms() -> None:
    story = dc.resolve_story(DB_NOW, kisiwa=True)
    story["sites"] = ["kobo", "cold", "ev", "kisiwa"]
    assert set(dc.objectives_instants(story)) == {"KOBO-001", "COLD-LAB-001", "EV-LAB-001"}
    links = dc.story_links(story, [], None, 5490, {"finding": {"id": "f-9"}})
    kisiwa = [(label, url) for label, url in links if "KISIWA-001" in url]
    assert len(kisiwa) == 4
    base = "http://localhost:5490"
    for _, url in links:
        assert any(url[len(base):].startswith(form) for form in dc.LINK_FORMS), url
    assert (f"{base}/sites/KISIWA-001?date=2026-11-01") in [u for _, u in kisiwa]
    assert f"{base}/sites/KISIWA-001/performance/fuel?night=2026-10-31" in [u for _, u in kisiwa]
    # K7-F: the build document's shape (the Finding id on the Action) and the verification link once judged
    built = {"action": {"id": "a-7", "finding_id": "f-9"}, "verdict": {"state": "VERIFIED"}}
    links = dc.story_links(story, [], None, 5490, built)
    kisiwa = dict((label, url) for label, url in links if "KISIWA-001" in url)
    assert len(kisiwa) == 5
    for _, url in links:
        assert any(url[len(base):].startswith(form) for form in dc.LINK_FORMS), url
    assert kisiwa["KISIWA-001 unexplained-fuel finding"] == f"{base}/sites/KISIWA-001/fuel-findings/f-9"
    assert kisiwa["KISIWA-001 fuel verification"] == f"{base}/sites/KISIWA-001/domain-actions/a-7/fuel-verification"
    assert "KISIWA-001 fuel verification" not in dict(dc.story_links(story, [], None, 5490, {"action": {"id": "a-7"}}))
    assert not [u for _, u in dc.story_links({**story, "sites": ["kobo", "cold", "ev"]}, [], None, 5490,
                                             {"finding": {"id": "f-9"}}) if "KISIWA" in u]


def test_8_add_day_keeps_refusing_kisiwa_and_the_default_is_four_sites(monkeypatch) -> None:
    """K7-F flips the default prepare to all four Sites (§9l.3 "`--sites` default"); add-day still refuses Kisiwa."""
    with pytest.raises(SystemExit):
        dc.main(["--db", "assetops_demo3_kisiwa_test", "--work", "var/demo3_kisiwa", "add-day", "--site",
                 "KISIWA-001", "--kind", "normal"])
    assert dc.Demo.prepare.__defaults__[0] == ("kobo", "cold", "ev", "kisiwa") == dc.SITES
    seen: list[tuple] = []
    monkeypatch.setattr(dc.Demo, "prepare", lambda self, sites, **kw: seen.append(sites))
    dc.main(["--db", "assetops_demo3_kisiwa_test", "--work", "var/demo3_kisiwa", "prepare"])
    assert seen == [("kobo", "cold", "ev", "kisiwa")]
    # DIESEL-1-R3n §9o.1: Kisiwa's expected seconds feed the default 2x cap
    assert dc.EXPECTED_SECONDS["kisiwa"] == 3600


# ---- 9. row self-tests --------------------------------------------------------------------------------------------

def _window(k: int, night: dict) -> dict:
    """A stored window body that reproduces the handover's night (terms from the handover, a = 10, r = 4.9)."""
    r = night["readings"]
    move = timedelta(days=27)
    spans = ([[dc.iso(_at(rows.KIS_F0_GAP_SPAN[0]) + move), dc.iso(_at(rows.KIS_F0_GAP_SPAN[1]) + move)]]
             if k == 4 else [])
    return {"id": f"w-{k}", "revision": 1, "recorded_at": calendar()["runs"][k - 1]["assessed_at"],
            "state": r["state"], "reason": None, "gap_minutes": r["gap_minutes"], "gap_spans": spans,
            "limitations": ["REPORTING_GAP"] if k == 4 else [], "residual_low": r["residual_low_exact"],
            "residual_high": r["residual_high_exact"],
            "terms": {"opening_l": r["opening_exact"], "closing_l": r["closing_exact"],
                      "deliveries_l": r["deliveries_exact"], "delivery_tolerance_l": r["delivery_tolerance_exact"],
                      "loaded_litres": r["loaded_litres_exact"], "use_low": r["use_low_exact"],
                      "use_high": r["use_high_exact"], "idle_seconds": 0, "accuracy_l": "10", "no_load_l_per_h": "49/10"}}


def _windows() -> dict[int, dict]:
    return {n["k"]: _window(n["k"], n) for n in kis.load_handover()["nights"]}


KIS3_TOLERANCED = ("loaded_litres", "use_low", "use_high", "residual_low", "residual_high")


def test_9_kis3_passes_on_a_true_body() -> None:
    from fractions import Fraction

    out = rows.kis3(_windows(), kis.load_handover(), 27)
    assert out["nights"] == 10 and out["states"][4] == "UNEXPLAINED"
    # DIESEL-1-R3n §9o.3: the pass body prints the tolerance and the largest difference per toleranced term
    assert out["tolerance_l"] == "1/100000"
    assert sorted(out["max_diff_l"]) == sorted(KIS3_TOLERANCED)
    assert all(Fraction(v) <= Fraction(out["tolerance_l"]) for v in out["max_diff_l"].values())
    print("KIS-3 pass body:", json.dumps({k: out[k] for k in ("tolerance_l", "max_diff_l")}, sort_keys=True))


def test_9_kis3_max_diff_is_the_largest_difference_within_tolerance() -> None:
    """Differences inside 1/100000 L pass, and `max_diff_l` is the largest over the nights, exact, per term."""
    from fractions import Fraction

    windows = _windows()
    for k, extra in ((2, "1/400000"), (6, "3/400000"), (9, "1/200000")):
        t = windows[k]["terms"]
        t["use_low"] = str(Fraction(t["use_low"]) + Fraction(extra))
    handover = kis.load_handover()  # the stored band must reproduce, so the handover side moves for the residual
    night3 = next(n for n in handover["nights"] if n["k"] == 3)["readings"]
    night3["residual_high_exact"] = str(Fraction(night3["residual_high_exact"]) + Fraction("1/100000"))
    out = rows.kis3(windows, handover, 27)
    assert out["max_diff_l"] == {"loaded_litres": "0", "use_low": "3/400000", "use_high": "0", "residual_low": "0",
                                 "residual_high": "1/100000"}
    print("KIS-3 within-tolerance body:", json.dumps({k: out[k] for k in ("tolerance_l", "max_diff_l")},
                                                     sort_keys=True))


@pytest.mark.parametrize("night, change", [
    (1, {"state": "BELOW_MATERIALITY"}), (2, {"reason": "SFC_MISSING"}), (3, {"gap_minutes": 5}),
    (5, ("opening_l", "1")), (6, ("loaded_litres", "+1/1000")), (4, {"residual_low": "0"}),
    (9, ("use_high", "+1000001/100000000000")),  # K7-F: just beyond 1/100000 L
    (7, ("idle_seconds", 60)), (4, {"gap_spans": []}), (4, {"limitations": []}), (8, {"limitations": ["REPORTING_GAP"]}),
])
def test_9_kis3_fails_per_item(night: int, change) -> None:
    from fractions import Fraction

    windows = _windows()
    w = windows[night]
    if isinstance(change, tuple):
        key, value = change
        if isinstance(value, str) and value.startswith("+"):
            value = str(Fraction(w["terms"][key]) + Fraction(value[1:]))
        w["terms"][key] = value
    else:
        w.update(change)
    with pytest.raises(AssertionError):
        rows.kis3(windows, kis.load_handover(), 27)


def _kis9_body() -> dict:
    cal = calendar()
    posts = [p for p in _posts().values() if p] + [kis.site_visit_post(cal, "case-1")]
    records = [{"kind": p["kind"], "body": p["body"], "occurred_at": p["occurred_at"], "recorded_at": p["recorded_at"],
                "quantity": p["quantity"], "source_document_sha256": p["source_document_sha256"],
                "case_id": p.get("case_id")} for p in posts]
    doc = copy.deepcopy(derived()[1])  # a case mutates the actions; the cached log stays untouched
    placed = kis.straddle_check(doc["actions"], story_runs())
    dips = {d["action_id"]: d["dip_l"] for d in kis.load_handover()["dips"]}
    build_runs = [{"k": k, "history": kis.expected_history(doc["actions"], placed, k), "log_sha256": "s" * 64,
                   "dips": [{"action_id": a, "dip_l": dips[a]} for a, n in placed.items()
                            if n == k and a.startswith("kis-dip")]} for k in range(1, 11)]
    windows = _windows()
    finding = {"findings": [{"finding_id": "f-1", "lifecycle": "SUPPORTED", "window_id": "w-4", "window_revision": 1,
                             "thread_kinds": ["UNEXPLAINED_FUEL"], "consequence_state": "PRICED",
                             "price_revision_id": "p-1", "created_at": cal["runs"][3]["raised_at"]}],
               "diesel_v1_revision_id": "p-1"}
    action = {"origin_finding_id": "f-1", "case_id": "case-1", "case_state": "COMPLETE", "linked_case_ids": ["case-1"],
              "plan_recorded_at": [cal["plan"]["freeze_at"]], "outcome_recorded_at": [cal["evaluate_at"]]}
    return {"records": records, "handover": kis.load_handover(), "calendar": cal,
            "build": {"log": {"log_id": cal["story_log_id"], "log_version": 1, "sha256": "s" * 64}, "runs": build_runs},
            "actions": doc["actions"], "runs": story_runs(), "windows": windows, "finding": finding, "action": action}


def test_9_kis9_passes_on_a_true_body() -> None:
    out = rows.kis9(**_kis9_body())
    assert (out["records"], out["dips"], out["placed"]) == (13, 11, 15)


def _rec(body: dict, kind: str, index: int = 0) -> dict:
    return [r for r in body["records"] if r["kind"] == kind][index]


KIS9_FAILS = {
    "a-two-deliveries": lambda b: b["records"].append(dict(_rec(b, "FUEL_DELIVERY"))),
    "a-delivery-quantity": lambda b: _rec(b, "FUEL_DELIVERY").update(quantity="299"),
    "a-delivery-ticket": lambda b: _rec(b, "FUEL_DELIVERY").update(source_document_sha256="0" * 64),
    "a-delivery-recorded-late": lambda b: _rec(b, "FUEL_DELIVERY").update(
        recorded_at=dc.iso(_at(_rec(b, "FUEL_DELIVERY")["recorded_at"]) + timedelta(minutes=1))),
    "a-missing-dip": lambda b: b["records"].remove(_rec(b, "TANK_DIP", 3)),
    "a-dip-recorded-late": lambda b: _rec(b, "TANK_DIP", 2).update(
        recorded_at=dc.iso(_at(_rec(b, "TANK_DIP", 2)["recorded_at"]) + timedelta(minutes=5))),
    "a-site-visit-body": lambda b: _rec(b, "SITE_VISIT").update(body="Tank cap sealed."),
    "a-record-inside-removal": lambda b: b["records"].append(
        {**_rec(b, "SITE_VISIT"), "kind": "OPERATOR_LOG", "body": "Night round",
         "occurred_at": dc.iso(_day(-6, 22, 10)), "recorded_at": dc.iso(_day(-6, 22, 20))}),
    "a-record-names-removal": lambda b: b["records"].append(
        {**_rec(b, "SITE_VISIT"), "kind": "OPERATOR_LOG", "body": "Fuel removal seen", "occurred_at": dc.iso(_day(-3)),
         "recorded_at": dc.iso(_day(-3, 0, 5))}),
    "b-dip-quantity": lambda b: _rec(b, "TANK_DIP", 0).update(quantity="705"),
    "b-build-dip": lambda b: b["build"]["runs"][3]["dips"][0].update(dip_l=1),
    "c-straddle": lambda b: b["actions"].append({"action_id": "x", "kind": "TANK_SEALED", "at": dc.iso(_day(1, 12))}),
    "d-no-finding": lambda b: b.update(finding=None),
    "d-two-findings": lambda b: b["finding"]["findings"].append(dict(b["finding"]["findings"][0], finding_id="f-2")),
    "d-not-supported": lambda b: b["finding"]["findings"][0].update(lifecycle="CANDIDATE"),
    "d-other-window": lambda b: b["finding"]["findings"][0].update(window_id="w-5"),
    "d-window-revision": lambda b: b["finding"]["findings"][0].update(window_revision=2),
    "d-thread": lambda b: b["finding"]["findings"][0].update(thread_kinds=[]),
    "d-unpriced": lambda b: b["finding"]["findings"][0].update(consequence_state="UNPRICED"),
    "d-price-version": lambda b: b["finding"].update(diesel_v1_revision_id="p-2"),
    "e-no-action": lambda b: b.update(action=None),
    "e-origin": lambda b: b["action"].update(origin_finding_id="f-2"),
    "e-case-open": lambda b: b["action"].update(case_state="IN_PROGRESS"),
    "e-not-linked": lambda b: b["action"].update(linked_case_ids=[]),
    "e-visit-case": lambda b: _rec(b, "SITE_VISIT").update(case_id="case-2"),
    # K7-F: the plan frozen at plan.freeze_at, one verdict stored at evaluate_at
    "e-no-plan": lambda b: b["action"].update(plan_recorded_at=[]),
    "e-plan-stamp": lambda b: b["action"].update(plan_recorded_at=[dc.iso(_day(-4, 12, 31))]),
    "e-two-plans": lambda b: b["action"]["plan_recorded_at"].append(b["action"]["plan_recorded_at"][0]),
    "e-no-verdict": lambda b: b["action"].update(outcome_recorded_at=[]),
    "e-verdict-stamp": lambda b: b["action"].update(outcome_recorded_at=[dc.iso(_day(-1, 13, 1))]),
    "e-two-verdicts": lambda b: b["action"]["outcome_recorded_at"].append(b["action"]["outcome_recorded_at"][0]),
    "f-log-id": lambda b: b["build"]["log"].update(log_id="kisiwa-001-operational-actions"),
    "f-history": lambda b: b["build"]["runs"][1].update(history=[]),
    "f-run-log": lambda b: b["build"]["runs"][5].update(log_sha256="t" * 64),
    "g-window-stamp": lambda b: b["windows"][7].update(recorded_at=dc.iso(_day(-1, 13))),
    "g-finding-stamp": lambda b: b["finding"]["findings"][0].update(created_at=dc.iso(_day(-5, 12, 40))),
    "g-visit-stamp": lambda b: _rec(b, "SITE_VISIT").update(recorded_at=dc.iso(_day(-4, 12, 16))),
}


@pytest.mark.parametrize("name", sorted(KIS9_FAILS))
def test_9_kis9_fails_per_item(name: str) -> None:
    body = _kis9_body()
    KIS9_FAILS[name](body)
    with pytest.raises(AssertionError):
        rows.kis9(**body)


# ---- final steps (K4a and K6a merged): carry R3k2 L2, the raise and Action bodies --------------------------------------

def test_carry_r3k2_l2_a_summary_with_no_kisiwa_fails_every_kis_row() -> None:
    """A dataset with no KISIWA-001 Site is a failure with the carry's body, not a skip."""
    want = {"kisiwa": "missing: no KISIWA-001 Site in this dataset", "checked": 0}
    assert rows.KISIWA_MISSING_BODY == want
    exc = rows.KisiwaMissing()
    assert isinstance(exc, AssertionError) and exc.body == want
    got = rows.failed_result(exc)
    assert got["status"] == "fail" and got["read"] == want
    # an ordinary failure carries no body
    assert "read" not in rows.failed_result(AssertionError("x"))


def test_carry_r3k2_l2_no_kis_row_keeps_the_skip_branch() -> None:
    """Every KIS row's no-Site branch raises `KisiwaMissing`; nothing returns "not in this dataset"."""
    text = (Path(__file__).resolve().parents[2] / "tools" / "demo_combined_finish.py").read_text(encoding="utf-8")
    assert "not in this dataset" not in text
    # KIS-4, KIS-5, KIS-10 (K6b's, carried in K7-F), KIS-3, KIS-9, and K9's KIS-8 (wording half)
    assert text.count("raise KisiwaMissing()") == 6


def test_raise_and_action_steps_are_wired_to_the_merged_services() -> None:
    """The pending markers are gone; the Action body names the FUEL_BALANCE domain (DIESEL-1-R3m)."""
    import inspect

    assert not hasattr(kis, "K4A_PENDING")
    action_src = inspect.getsource(kis.record_action)
    assert '"domain": "FUEL_BALANCE"' in action_src and '"MINI"' not in action_src
    assert 'idempotency_key": "kisiwa-fuel-action"' in action_src
    assert "build_fuel_finding_service" in inspect.getsource(kis.raise_night)
    assert kis.INCIDENT_K == 4


# ---- K7-F: the freeze step (DIESEL-1-R3m §9m.5) -----------------------------------------------------------------------

class _FakeEngine:
    """Answers the night-4 window query with `w-4`."""

    def connect(self):
        import contextlib
        from types import SimpleNamespace

        result = SimpleNamespace(scalar_one=lambda: "w-4")
        return contextlib.nullcontext(SimpleNamespace(execute=lambda *a, **k: result))


def _fake_services(monkeypatch, cal: dict, state: str = "INEFFECTIVE", **plan_changes) -> list[tuple]:
    """K6b's service replaced by a fake that records each call with its clock's instant."""
    from types import SimpleNamespace

    from assetops_backend.actions import composition

    calls: list[tuple] = []
    plan = {"plan_id": "p-1", "recorded_at": cal["plan"]["freeze_at"], "effective_from": cal["action"]["complete_at"],
            "later_selection_rule": {"candidates": {"from": cal["runs"][5]["night_date"], "to": "x"}},
            "baseline_selection": {"window_id": "w-4"}, **plan_changes}

    def build(url, *, test_clock):
        def freeze(t, s, a):
            calls.append(("freeze", test_clock()))
            return 201, {"replayed": False, "plan": plan}

        def evaluate(t, s, a):
            calls.append(("evaluate", test_clock()))
            return {"state": state, "stored": state != "NOT_JUDGED", "replayed": False, "outcome_id": "o-1"}

        def summary(t, s, a, code=None):
            calls.append(("summary", test_clock()))
            return {"state": state}

        return SimpleNamespace(freeze_fuel_plan=freeze, evaluate_fuel_plan=evaluate, fuel_summary=summary,
                               store=object(), actions=SimpleNamespace(verification_ports=SimpleNamespace(
                                   fuel_windows=SimpleNamespace(dispose=lambda: calls.append(("dispose", None))))))

    monkeypatch.setattr(composition, "build_fuel_verification_service", build)
    return calls


@pytest.mark.parametrize("state", ["VERIFIED", "INEFFECTIVE", "INCONCLUSIVE"])
def test_k7f_freeze_and_evaluate_at_story_instants_record_the_verdict_as_computed(monkeypatch, state: str) -> None:
    cal = calendar()
    calls = _fake_services(monkeypatch, cal, state)
    out = kis.freeze_and_evaluate("postgresql+psycopg://x/y", _FakeEngine(), "t", "s", cal,
                                  {"id": "00000000-0000-0000-0000-000000000007"})
    freeze_at, evaluate_at = _at(cal["plan"]["freeze_at"]), _at(cal["evaluate_at"])
    assert (freeze_at, evaluate_at) == (_day(-4, 12, 30), _day(-1, 13))
    assert calls == [("freeze", freeze_at), ("dispose", None), ("evaluate", evaluate_at), ("summary", evaluate_at),
                     ("dispose", None)]
    assert out["verdict"]["state"] == state and out["verdict"]["evaluated_at"] == dc.iso(evaluate_at)
    assert out["plan"]["baseline_window_id"] == "w-4" and out["summary"] == {"state": state}
    # §9m.5: effective_from is the first COMPLETE occurred_at (S-4d 12:05), before night 6's window (S-4d 15:00)
    assert _at(out["plan"]["effective_from"]) == _day(-4, 12, 5) < kis.night_opens(date.fromisoformat(
        cal["runs"][5]["night_date"])) == _day(-4, 15)


@pytest.mark.parametrize("change", [
    {"effective_from": "2026-11-02T12:00:00+00:00"},                                        # the record, not COMPLETE
    {"later_selection_rule": {"candidates": {"from": "2026-11-03", "to": "x"}}},             # not night 6
    {"baseline_selection": {"window_id": "w-5"}},                                            # not night 4's window
    {"recorded_at": "2026-11-02T12:31:00+00:00"},                                            # not freeze_at
])
def test_k7f_a_plan_off_the_card_is_stop_s6(monkeypatch, change: dict) -> None:
    cal = calendar()
    _fake_services(monkeypatch, cal, **change)
    with pytest.raises(SystemExit, match="FREEZE \\(stop S-6\\)"):
        kis.freeze_and_evaluate("u", _FakeEngine(), "t", "s", cal, {"id": "00000000-0000-0000-0000-000000000007"})


def test_k7f_not_judged_is_stop_s6(monkeypatch) -> None:
    cal = calendar()
    _fake_services(monkeypatch, cal, "NOT_JUDGED")
    with pytest.raises(SystemExit, match="EVALUATE \\(stop S-6\\)"):
        kis.freeze_and_evaluate("u", _FakeEngine(), "t", "s", cal, {"id": "00000000-0000-0000-0000-000000000007"})


def test_k7f_build_freezes_after_the_action_and_before_the_threads() -> None:
    import inspect

    src = inspect.getsource(kis.build)
    action, freeze, threads = (src.index(s) for s in ("record_action(", "freeze_and_evaluate(", "threads(work)"))
    assert action < freeze < threads
