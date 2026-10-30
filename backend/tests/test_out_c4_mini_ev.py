"""OUT-C U4: mini battery and EV warnings from fake ports (build sheet OUT-C §2 U4)."""
from __future__ import annotations

from datetime import timedelta

import test_out_b2_mini as b2
import test_out_b3_cold_ev as b3

from assetops_backend.site_outcomes import ev, mini

PROTECT = mini.PROTECT


def interval(*constraints: str) -> dict:
    return {"result": {"portions_minutes": {"candidate": "0", "indeterminate": "0"},
                       "binding_constraints": list(constraints)}}


def mini_run(dispatch=None, refuse=()):
    over = {} if dispatch is None else {"dispatch": dispatch}
    return b2.run(b2.Fake(refuse=refuse, **over))


# --------------------------------------------------------------- mini

def test_reserve_count_reads_binding_constraints_only() -> None:
    body = {"intervals": [interval("BATTERY_AT_RESERVE"), interval("BATTERY_NEAR_RESERVE", "GENERATOR_MINIMUM"),
                          interval("GENERATOR_MINIMUM"),
                          {"result": {"reason": "battery near reserve", "binding_constraints": []}}]}
    assert mini.reserve_counts(body) == (2, 4)
    assert mini.reserve_counts({"intervals": []}) == (0, 0)
    assert mini.reserve_counts(None) is None


def test_battery_contributor_texts_and_plurals() -> None:
    comp, rows = mini_run({"intervals": [interval("BATTERY_AT_RESERVE"), interval()]})
    battery = b2.contributor(rows[PROTECT], "battery")
    assert battery["text"] == "At or near the reserve during 1 of 2 assessed generator periods"
    assert battery["confidence"] == {"label": "Limited", "tone": "amber"}
    (w,) = [x for x in comp.facts.warnings if x.kind == "BATTERY_NEAR_RESERVE"]
    assert w.seen == "During 1 of 2 assessed generator periods on 20 Oct"
    _, rows = mini_run({"intervals": [interval("BATTERY_NEAR_RESERVE")]})
    assert b2.contributor(rows[PROTECT], "battery")["text"] == (
        "At or near the reserve during 1 of 1 assessed generator period")
    _, rows = mini_run({"intervals": [interval(), interval(), interval()]})
    assert b2.contributor(rows[PROTECT], "battery")["text"] == "No generator period at or near the reserve (3 assessed)"
    _, rows = mini_run({"intervals": []})
    assert b2.contributor(rows[PROTECT], "battery")["text"] == mini.NO_PERIOD_ASSESSED


def test_failed_dispatch_leaves_mg4_unknown() -> None:
    comp, rows = mini_run(refuse=("dispatch",))
    battery = b2.contributor(rows[PROTECT], "battery")
    assert (battery["text"], battery["confidence"]) == (mini.NOT_LOADED, None)
    assert b2.outcome(rows[PROTECT], "MG-4") == "UNKNOWN"
    assert not [w for w in comp.facts.warnings if w.kind == "BATTERY_NEAR_RESERVE"]


def test_protect_headline_counts_mg4_warnings() -> None:
    # the fake's PM-2 calendar plan is due soon: one MG-4 warning; the battery warning makes two
    _, rows = mini_run({"intervals": [interval()]})
    assert rows[PROTECT]["headline"] == "1 early warning on battery and generator"
    _, rows = mini_run({"intervals": [interval("BATTERY_AT_RESERVE")]})
    assert rows[PROTECT]["headline"] == "2 early warnings on battery and generator"
    assert rows[PROTECT]["state"] == "WATCH"
    _, rows = b2.run(b2.Fake(refuse=("plans",), dispatch={"intervals": [interval()]}))
    assert rows[PROTECT]["headline"] == "Battery stayed clear of its reserve in 1 assessed generator period"
    _, rows = b2.run(b2.Fake(refuse=("plans", "dispatch")))
    assert rows[PROTECT]["headline"] == mini.PROTECT_HEADLINE


def test_protect_clear_headline() -> None:
    """Rulings C final review L2."""
    assert mini.protect_clear((0, 24)) == "Battery stayed clear of its reserve in 24 assessed generator periods"
    assert mini.protect_clear((0, 1)) == "Battery stayed clear of its reserve in 1 assessed generator period"
    assert mini.protect_clear((0, 0)) == mini.PROTECT_HEADLINE
    assert mini.protect_clear(None) == mini.PROTECT_HEADLINE


# --------------------------------------------------------------- EV

HEALTH = {"health": {"rows": [{"kind": "CONNECTOR", "label": "C2", "asset_id": "a-c2", "asset_code": "c2",
                               "condition_state": "NEEDS_INVESTIGATION"}]}}
AVAIL = {"availability": {"connectors": [
    {"asset_id": "a-c1", "label": "C1", "known_unavailable_seconds": 0, "unknown_seconds": 0},
    {"asset_id": "a-c2", "label": "C2", "known_unavailable_seconds": 5400, "unknown_seconds": 1800},
    {"asset_id": "a-c3", "label": "C3", "known_unavailable_seconds": 600, "unknown_seconds": 0}]}}
OVERDUE_PLAN = [{"canonical_plan_id": "p9", "code": "PM-9", "title": "Connector inspection",
                 "trigger_kind": "CALENDAR", "next_due_at": b3.T(0, 0, 15), "next_due_hours": None, "state": "DRAFT",
                 "asset_id": "a-c2"}]


def ev_run(**over):
    return b3.run_ev(b3.Fake(**{"ev_depth": HEALTH, "ev_availability": AVAIL, **over}))


def kinds(comp) -> list[str]:
    return [w.kind for w in comp.facts.warnings]


def test_connector_out_of_service_exactly_when_unavailable_time_exists() -> None:
    comp, _ = ev_run()
    out = [w for w in comp.facts.warnings if w.kind == "CONNECTOR_OUT_OF_SERVICE"]
    assert [(w.title, w.seen) for w in out] == [
        # the UTC day [20 Oct, 21 Oct) spans two Nairobi days (UTC+3)
        ("Connector C2 out of service", "1 h 30 min out and 30 min unknown between 20 Oct and 21 Oct"),
        ("Connector C3 out of service", "10 min out between 20 Oct and 21 Oct")]
    assert all("None" not in w.seen for w in comp.facts.warnings)


def test_connector_text_has_no_double_prefix() -> None:
    """OUT-C review L1: labels that already read "Connector c1" are not prefixed again."""
    assert ev.connector_name("Connector c1") == "Connector c1" and ev.connector_name("C2") == "Connector C2"
    avail = {"availability": {"connectors": [
        {"asset_id": "a-c1", "label": "Connector c1", "known_unavailable_seconds": 600, "unknown_seconds": 0}]}}
    _, rows = ev_run(ev_availability=avail)
    text = b3.contributor(rows[ev.PROTECT], "connector_availability")["text"]
    assert text.startswith("Connector c1: 10 min out") and "Connector Connector" not in text
    assert rows[ev.PROTECT]["subline"].startswith("Connector c1 was out of service for 10 min")


def test_peak_fires_only_close_to_the_limit_and_needs_both_numbers() -> None:
    assert "PEAK_NEAR_IMPORT_LIMIT" not in kinds(ev_run()[0])  # 76 of 120 kW
    near = dict(b3.EV_OVERVIEW, site_power={"observed_peak_kw": "76", "configured_limit_kw": "80"})
    comp, _ = ev_run(ev_overview=near)
    (w,) = [x for x in comp.facts.warnings if x.kind == "PEAK_NEAR_IMPORT_LIMIT"]
    assert w.seen == "76 kW against 80 kW"
    at_margin = dict(b3.EV_OVERVIEW, site_power={"observed_peak_kw": "72", "configured_limit_kw": "80"})
    assert "PEAK_NEAR_IMPORT_LIMIT" not in kinds(ev_run(ev_overview=at_margin)[0])
    # review L3: peak is passed only when both values are numbers
    for power in ({"observed_peak_kw": None, "configured_limit_kw": "80"},
                  {"observed_peak_kw": "76", "configured_limit_kw": None}, {"observed_peak_kw": "x"}, {}):
        assert ev.peak_facts({"site_power": power}) is None, power
    assert ev.peak_facts({"site_power": {"observed_peak_kw": "79.5", "configured_limit_kw": 80}}) == (
        79.5, 80.0, "79.5", "80")


def test_charger_fault_needs_an_overdue_plan_on_the_faulted_connector() -> None:
    assert "CHARGER_FAULT_OVERDUE_INSPECTION" not in kinds(ev_run()[0])
    comp, rows = ev_run(plans=OVERDUE_PLAN)
    (w,) = [x for x in comp.facts.warnings if x.kind == "CHARGER_FAULT_OVERDUE_INSPECTION"]
    assert w.seen == "C2 fault recorded in this window · inspection overdue since 15 Oct"
    assert w.href == f"/sites/{b3.E}/health"
    issues = [i["text"] for i in rows[PROTECT]["issues"]]
    assert "Charger fault and overdue inspection" in issues and "Connector inspection overdue" in issues


def test_window_days_are_site_local() -> None:
    from datetime import timedelta

    def seen(lo, hi):
        comp = ev.compose(b3.ev_ports(b3.Fake(ev_depth=HEALTH, ev_availability=AVAIL)), site_code=b3.E, lo=lo,
                          hi=hi, site_timezone=b3.ZONE)
        return [w.seen for w in comp.facts.warnings if w.kind == "CONNECTOR_OUT_OF_SERVICE"][0]
    local = b3.LO - timedelta(hours=3)  # Nairobi midnight
    assert seen(local, local + timedelta(days=1)) == "1 h 30 min out and 30 min unknown on 20 Oct"
    assert seen(local, local + timedelta(days=2)) == "1 h 30 min out and 30 min unknown between 20 Oct and 21 Oct"


# --------------------------------------------------------------- window anchors (U2 review L1)

def _maintenance_windows(calls) -> list[tuple]:
    return [(args[1], args[2]) for name, args in calls if name == "work" and args[0] == "maintenance"]


def test_mini_visit_windows_are_anchored_at_the_board_day_end() -> None:
    from assetops_backend.site_outcomes import visits
    fake = b2.Fake()
    b2.run(fake)
    (incidents,) = [args for name, args in fake.calls if name == "work" and args[0] == "incidents"]
    end = incidents[2]  # the board day's end, the same `end` every day-bounded read uses
    assert end - incidents[1] > timedelta(days=1)  # the incident window starts well before the day: not `start`
    assert _maintenance_windows(fake.calls) == list(visits.record_windows(end))
    assert _maintenance_windows(fake.calls)[1][1] == end


def test_ev_visit_windows_are_anchored_at_the_window_end() -> None:
    from assetops_backend.site_outcomes import visits
    fake = b3.Fake()
    b3.run_ev(fake)
    assert b3.LO != b3.HI
    assert _maintenance_windows(fake.calls) == list(visits.record_windows(b3.HI))
