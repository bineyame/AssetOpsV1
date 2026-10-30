"""OUT-C U1: early-warning rules, positive and negative per rule (build sheet OUT-C §2 U1)."""
from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone

from assetops_backend.outcomes.catalogue import COLD, EV, MINI
from assetops_backend.outcomes.outcome_map import outcome_roles
from assetops_backend.outcomes.warnings import (
    BATTERY, CHARGER_FAULT, CONNECTOR_OUT, PEAK, PEAK_MARGIN, PLAN_DUE_SOON, PLAN_OVERDUE, PRICE_NEEDS, REPEATED,
    PlanCue, Visit, WarningFacts, evaluate)

TO = datetime(2026, 10, 29, tzinfo=timezone.utc)
FROM = TO - timedelta(days=60)
SOON = TO + timedelta(days=14)
DAY = date(2026, 10, 28)
COLD_KEYS = outcome_roles("FINDING:COLD_START_FAILURE", COLD)
F_KEYS = COLD_KEYS[0] + COLD_KEYS[1]  # CC-6, CC-1, CC-5, CC-3


def facts(domain: str = COLD, **kw) -> WarningFacts:
    base = WarningFacts(domain=domain, site_code="S1", to=TO, visits_from=FROM, soon_until=SOON,
                        window_days=(DAY, DAY))
    return replace(base, **kw)


def visit(i: int, at: datetime, *, state: str = "COMPLETED", asset: str | None = "a1", links=("f1",)) -> Visit:
    return Visit(case_id=f"c{i}", code=f"WR-{i}", asset_id=asset, asset_name="generator-1", state=state,
                 occurred_at=at, occurred_on=at.date(), finding_ids=tuple(links), href=f"/work/c{i}")


OPEN = {"f1": (F_KEYS, "/findings/f1")}


def kinds(ws) -> list[str]:
    return [w.kind for w in ws]


# ---- REPEATED_MAINTENANCE_NO_RESULT

def test_repeat_needs_two_completed_visits() -> None:
    one = facts(visits=(visit(1, TO - timedelta(days=5)),), open_findings=OPEN)
    assert evaluate(one) == ()
    two = facts(visits=(visit(1, TO - timedelta(days=5)), visit(2, TO - timedelta(days=2))), open_findings=OPEN)
    (w,) = evaluate(two)
    assert (w.kind, w.key, w.count, w.subject_label, w.href) == (
        REPEATED, f"{REPEATED}:S1:a1", 2, "generator-1", "/work/c2")
    assert (w.badge, w.lens, w.status_effect, w.persistence) == ("RISK", "COST", "NEEDS_ATTENTION", "RECURRING")
    assert w.title == "Repeated maintenance without a result"
    assert w.seen == "generator-1 visited 2 times in 60 days (24 Oct, 27 Oct); the linked finding is still open"
    assert [r["kind"] for r in w.evidence_refs] == ["WORK_CASE", "WORK_CASE", "FINDING"]
    assert w.evidence_refs[0] == {"kind": "WORK_CASE", "id": "c1", "label": "WR-1", "href": "/work/c1"}
    assert w.evidence_refs[2] == {"kind": "FINDING", "id": "f1", "label": None, "href": "/findings/f1"}
    assert w.visit_ids == ("c1", "c2")
    assert w.fault_name == "linked finding"  # no fault name on record: the fallback


def test_repeat_fault_name_only_when_every_open_link_agrees() -> None:
    """Rulings C final review F1: one shared fault name, else "linked finding"."""
    vs = (visit(1, TO - timedelta(days=5), links=("f1", "f2")), visit(2, TO - timedelta(days=2)))
    two = {"f1": (F_KEYS, "/findings/f1"), "f2": (F_KEYS, "/findings/f2")}
    start = "automatic start failure"
    (w,) = evaluate(facts(visits=vs, open_findings=two, fault_names={"f1": start, "f2": start}))
    assert w.fault_name == start
    assert w.seen == f"generator-1 visited 2 times in 60 days (24 Oct, 27 Oct); the {start} is still open"
    assert w.wire("S1", "x")["fault_name"] == start
    (w,) = evaluate(facts(visits=vs, open_findings=two, fault_names={"f1": start}))
    assert w.fault_name == "linked finding" and w.seen.endswith("the linked finding is still open")
    (w,) = evaluate(facts(visits=vs, open_findings=two, fault_names={"f1": start, "f2": "other fault"}))
    assert w.fault_name == "linked finding"
    assert all(x.fault_name is None for x in evaluate(facts(MINI, reserve=(2, 3))))  # only REPEATED sets it


def test_repeat_needs_an_open_linked_finding() -> None:
    vs = (visit(1, TO - timedelta(days=5)), visit(2, TO - timedelta(days=2)))
    assert evaluate(facts(visits=vs, open_findings={})) == ()  # closed or unresolved: not in open_findings
    assert evaluate(facts(visits=vs, open_findings={"other": (F_KEYS, None)})) == ()
    # the link may sit on any visit of the asset in the window, in any state
    vs2 = (visit(1, TO - timedelta(days=5), links=()), visit(2, TO - timedelta(days=2), links=()),
           visit(3, TO - timedelta(days=1), state="OPEN"))
    assert kinds(evaluate(facts(visits=vs2, open_findings=OPEN))) == [REPEATED]


def test_repeat_window_bounds_half_open() -> None:
    inside = (visit(1, FROM), visit(2, TO - timedelta(days=1)))
    assert kinds(evaluate(facts(visits=inside, open_findings=OPEN))) == [REPEATED]
    early = (visit(1, FROM - timedelta(seconds=1)), visit(2, TO - timedelta(days=1)))
    assert evaluate(facts(visits=early, open_findings=OPEN)) == ()
    at_to = (visit(1, TO - timedelta(days=3)), visit(2, TO))
    assert evaluate(facts(visits=at_to, open_findings=OPEN)) == ()


def test_repeat_null_asset_never_fires() -> None:
    vs = (visit(1, TO - timedelta(days=5), asset=None), visit(2, TO - timedelta(days=2), asset=None))
    assert evaluate(facts(visits=vs, open_findings=OPEN)) == ()


def test_repeat_four_open_three_completed_is_one_warning() -> None:
    vs = tuple(visit(i, TO - timedelta(days=10 - i), state="OPEN") for i in range(4)) + tuple(
        visit(10 + i, TO - timedelta(days=5 - i)) for i in range(3))
    (w,) = evaluate(facts(visits=vs, open_findings=OPEN))
    assert w.count == 3 and w.visit_ids == ("c10", "c11", "c12") and w.href == "/work/c12"


def test_repeat_categories_link_excludes_own_key() -> None:
    vs = (visit(1, TO - timedelta(days=5)), visit(2, TO - timedelta(days=2)))
    (w,) = evaluate(facts(visits=vs, open_findings=OPEN))
    items = w.categories["items"]
    assert items[0]["role"] == "MOVES" and [o["key"] for o in items[0]["outcomes"]] == ["CC-3"]
    checked = [o["key"] for i in items if i["role"] == "CHECKED" for o in i["outcomes"]]
    assert checked == ["CC-6", "CC-1", "CC-5"] and "CC-3" not in checked


# ---- PLAN_OVERDUE / PLAN_DUE_SOON

def plan(due: datetime | None, pid: str = "p1", asset: str | None = "a1") -> PlanCue:
    return PlanCue(plan_id=pid, code="PM-1", title="Witnessed backup start test", due_at=due,
                   due_on=due.date() if due else None, asset_id=asset)


def test_plan_bounds() -> None:
    (w,) = evaluate(facts(plans=(plan(TO),)))
    assert (w.kind, w.title, w.seen) == (PLAN_DUE_SOON, "Witnessed backup start test due soon", "Due 29 Oct")
    assert evaluate(facts(plans=(plan(SOON),))) == ()
    (w,) = evaluate(facts(plans=(plan(TO - timedelta(seconds=1)),)))
    assert (w.kind, w.title, w.seen) == (
        PLAN_OVERDUE, "Witnessed backup start test overdue", "Planned for 28 Oct, not done")
    assert (w.badge, w.lens, w.status_effect, w.href) == ("EARLY_WARNING", "RISK", "WATCH", "/maintenance/preventive")
    assert w.evidence_refs == ({"kind": "PLAN", "id": "p1", "label": "PM-1", "href": "/maintenance/preventive"},)
    assert w.key == f"{PLAN_OVERDUE}:S1:p1"
    assert [o["key"] for o in w.categories["items"][0]["outcomes"]] == ["CC-5"]


def test_plan_without_due_date_never_fires() -> None:
    assert evaluate(facts(plans=(plan(None),))) == ()  # RUN_HOURS plan


def test_date_suffix_follows_dates() -> None:
    (w,) = evaluate(facts(plans=(plan(TO + timedelta(days=1)),), date_suffix=" · UTC"))
    assert w.seen == "Due 30 Oct · UTC"


# ---- BATTERY_NEAR_RESERVE

def test_battery_reserve() -> None:
    assert evaluate(facts(MINI)) == ()
    assert evaluate(facts(MINI, reserve=(0, 3))) == ()
    (w,) = evaluate(facts(MINI, reserve=(2, 3)))
    assert (w.kind, w.title, w.seen) == (BATTERY, "Battery at or near its reserve",
                                         "During 2 of 3 assessed generator periods on 28 Oct")
    assert (w.key, w.href, w.badge, w.status_effect) == (
        f"{BATTERY}:S1:site", "/sites/S1/performance/dispatch", "EARLY_WARNING", "WATCH")
    assert [o["key"] for o in w.categories["items"][0]["outcomes"]] == ["MG-4"]
    (w,) = evaluate(facts(MINI, reserve=(1, 1)))
    assert w.seen == "During 1 of 1 assessed generator period on 28 Oct"


# ---- CHARGER_FAULT_OVERDUE_INSPECTION

def test_charger_fault_needs_overdue_plan_on_same_asset() -> None:
    fault = (("c1", "Connector 1"),)
    assert evaluate(facts(EV, faults=fault)) == ()
    other = evaluate(facts(EV, faults=fault, plans=(plan(TO - timedelta(days=4), asset="c2"),)))
    assert kinds(other) == [PLAN_OVERDUE]
    soon = evaluate(facts(EV, faults=fault, plans=(plan(TO + timedelta(days=4), asset="c1"),)))
    assert kinds(soon) == [PLAN_DUE_SOON]
    ws = evaluate(facts(EV, faults=fault, plans=(plan(TO - timedelta(days=4), asset="c1"),)))
    assert kinds(ws) == [PLAN_OVERDUE, CHARGER_FAULT]  # KINDS order (L2)
    w = ws[1]
    assert w.seen == "Connector 1 fault recorded in this window · inspection overdue since 25 Oct"
    assert (w.key, w.href, w.subject_label) == (f"{CHARGER_FAULT}:S1:c1", "/sites/S1/health", "Connector 1")
    assert [r["kind"] for r in w.evidence_refs] == ["PLAN", "ASSET"]
    assert w.evidence_refs[1] == {"kind": "ASSET", "id": "c1", "label": "Connector 1", "href": None}
    assert [o["key"] for o in w.categories["items"][0]["outcomes"]] == ["EV-4"]


# ---- CONNECTOR_OUT_OF_SERVICE

def test_connector_out_of_service() -> None:
    assert evaluate(facts(EV)) == ()
    (w,) = evaluate(facts(EV, connectors_out=(("c1", "1", "2 h", "15 min"),)))
    assert (w.kind, w.title, w.seen) == (CONNECTOR_OUT, "Connector 1 out of service",
                                         "2 h out and 15 min unknown on 28 Oct")
    assert (w.badge, w.lens, w.href) == ("RISK", "RISK", "/sites/S1/performance/availability")
    assert w.evidence_refs == ({"kind": "ASSET", "id": "c1", "label": "1", "href": None},)
    two_days = facts(EV, connectors_out=(("c1", "1", "2 h", None),), window_days=(DAY, date(2026, 10, 29)))
    (w,) = evaluate(two_days)
    assert w.seen == "2 h out between 28 Oct and 29 Oct" and "None" not in w.seen
    (w,) = evaluate(facts(EV, connectors_out=(("c1", "Connector c1", "2 h", None),)))
    assert w.title == "Connector c1 out of service"  # w504 labels already name the connector


# ---- PEAK_NEAR_IMPORT_LIMIT

def test_peak_margin() -> None:
    assert PEAK_MARGIN == 0.10
    assert evaluate(facts(EV)) == ()
    assert evaluate(facts(EV, peak=(72.0, 80.0, "72", "80"))) == ()
    assert evaluate(facts(EV, peak=(60.0, 80.0, "60", "80"))) == ()
    (w,) = evaluate(facts(EV, peak=(76.0, 80.0, "76", "80")))
    assert (w.kind, w.title, w.seen, w.href) == (PEAK, "Peak close to the import limit", "76 kW against 80 kW",
                                                 "/sites/S1/performance/energy")
    items = w.categories["items"]
    assert [(i["role"], [o["key"] for o in i["outcomes"]]) for i in items] == [
        ("MOVES", ["EV-5"]), ("CHECKED", ["EV-1"])]


# ---- shared

def test_sort_order_and_price_needs_closed() -> None:
    ws = evaluate(facts(EV, peak=(76.0, 80.0, "76", "80"), connectors_out=(("c1", "1", "2 h", "1 min"),),
                        faults=(("c1", "1"),), plans=(plan(TO - timedelta(days=1), asset="c1"),
                                                      plan(TO + timedelta(days=1), pid="p2"))))
    assert kinds(ws) == [CONNECTOR_OUT, PEAK, PLAN_OVERDUE, PLAN_DUE_SOON, CHARGER_FAULT]  # KINDS order (L2)
    for w in ws:
        assert w.price_needs == PRICE_NEEDS[w.kind]
        assert w.persistence == "OBSERVED"
    assert set(PRICE_NEEDS) == {REPEATED, PLAN_OVERDUE, PLAN_DUE_SOON, BATTERY, CHARGER_FAULT, CONNECTOR_OUT, PEAK}


def test_kinds_order_overdue_first_and_repeat_before_connector_and_peak() -> None:
    from assetops_backend.outcomes.warnings import KINDS
    assert KINDS.index(PLAN_OVERDUE) < KINDS.index(PLAN_DUE_SOON)
    assert KINDS.index(REPEATED) < KINDS.index(CONNECTOR_OUT) < KINDS.index(PEAK)
    # a due-soon plan whose key sorts first still follows an overdue one
    ws = evaluate(facts(plans=(plan(TO + timedelta(days=1), pid="a"), plan(TO - timedelta(days=1), pid="z"))))
    assert kinds(ws) == [PLAN_OVERDUE, PLAN_DUE_SOON]
    vs = (visit(1, TO - timedelta(days=5)), visit(2, TO - timedelta(days=2)))
    ws = evaluate(facts(EV, visits=vs, open_findings={"f1": (outcome_roles("FINDING:EV_INTERRUPTION", EV)[0], None)},
                        peak=(76.0, 80.0, "76", "80"), connectors_out=(("c1", "1", "2 h", None),)))
    assert kinds(ws) == [REPEATED, CONNECTOR_OUT, PEAK]


def test_wire_keys() -> None:
    (w,) = evaluate(facts(MINI, reserve=(2, 3)))
    body = w.wire("S1", "Kobo Mini-grid")
    assert list(body) == ["key", "kind", "badge", "badge_label", "lens", "title", "seen", "persistence",
                          "persistence_label", "price_needs", "status_effect", "categories", "site_code",
                          "site_name", "href", "evidence_refs", "count", "subject_label", "fault_name"]
    assert "subject" not in body and "visit_ids" not in body and "source_label" not in body
    assert (body["badge_label"], body["persistence_label"]) == ("Early warning", "Observed")
