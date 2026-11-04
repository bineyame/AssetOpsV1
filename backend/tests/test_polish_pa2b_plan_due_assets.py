"""POLISH PA-2b: pure pins of the shared plan due rule and the plain asset labels (build sheet §1.4, §3 asset labels,
Addendum 6 Q2 and Q4). Captures are deferred to PA-3 (Addendum 3); the read-level shape is pinned in
`test_w601b_global_maintenance.py::test_preventive_due_summary_over_all_pages`."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from assetops_backend.outcomes import warnings as w
from assetops_backend.chain import refs as R
from assetops_backend.outcomes.asset_words import asset_label, asset_word
from assetops_backend.outcomes.plan_due import (
    DUE_SOON, NOT_ASSESSED, NOT_DUE, OVERDUE, plan_due_state, soon_until)
from assetops_backend.site_outcomes import visits
from assetops_backend.work.site_index import asset_fields

TO = datetime(2026, 11, 1, tzinfo=timezone.utc)


# ---- plan_due_state (§1.4) --------------------------------------------------------------------------------------

def test_due_boundaries() -> None:
    assert plan_due_state("CALENDAR", TO - timedelta(microseconds=1), TO) == OVERDUE
    assert plan_due_state("CALENDAR", TO, TO) == DUE_SOON  # due exactly at `to` is not overdue
    assert plan_due_state("CALENDAR", TO + timedelta(days=14) - timedelta(microseconds=1), TO) == DUE_SOON
    assert plan_due_state("CALENDAR", TO + timedelta(days=14), TO) == NOT_DUE
    assert soon_until(TO) == TO + timedelta(days=14)


def test_demo_plans_read_as_the_diagnosis() -> None:
    """§1.4 DB reading for `to` = 1 Nov: PM-009 (25 Oct) and PM-013 (21 Oct) overdue, PM-004 (2 Nov) and PM-010
    (7 Nov) due soon, PM-003 on hours of use."""
    day = lambda d: datetime(2026, 10, d, tzinfo=timezone.utc) if d > 9 else datetime(2026, 11, d, tzinfo=timezone.utc)
    assert [plan_due_state("CALENDAR", day(d), TO) for d in (25, 21, 2, 7)] == [OVERDUE, OVERDUE, DUE_SOON, DUE_SOON]
    assert plan_due_state("RUN_HOURS", None, TO) == NOT_ASSESSED


def test_not_assessed_cases() -> None:
    assert plan_due_state("RUN_HOURS", TO - timedelta(days=3), TO) == NOT_ASSESSED
    assert plan_due_state("CALENDAR", None, TO) == NOT_ASSESSED
    assert plan_due_state(None, TO, TO) == NOT_ASSESSED


def test_board_warnings_use_the_helper_with_unchanged_behaviour() -> None:
    cue = lambda pid, due: w.PlanCue(plan_id=pid, code="PM-000001", title=f"Service {pid}", due_at=due,
                                     due_on=due.date(), asset_id=None, link_ref=R.estate_ref("maintenance_preventive"))
    f = w.WarningFacts(domain="MINI_GRID", site_code="S1", to=TO, visits_from=TO - timedelta(days=60),
                       soon_until=soon_until(TO), window_days=(TO.date(), TO.date()),
                       plans=(cue("a", TO - timedelta(days=1)), cue("b", TO), cue("c", TO + timedelta(days=14))))
    kinds = {x.subject: x.kind for x in w._plans(f)}
    assert kinds == {"a": w.PLAN_OVERDUE, "b": w.PLAN_DUE_SOON}
    assert [p.plan_id for p in w._overdue(f)] == ["a"]


# ---- asset labels (§3, Addendum 6 Q4) ---------------------------------------------------------------------------

def test_asset_words_by_type_and_site() -> None:
    assert asset_word("GENERATOR", "COLDCHAIN") == "Backup generator"
    assert asset_word("GENERATOR", "MINIGRID") == "Generator"
    assert asset_word("GENERATOR", "EV_CHARGING") == "Generator"
    assert asset_word("COMPRESSOR", "COLDCHAIN") == "Compressor"
    assert asset_word("BATTERY", "MINIGRID") == "Battery"
    assert asset_word("CONNECTOR", "EV_CHARGING") == "Connector"
    assert asset_word("EV_CONNECTOR", "EV_CHARGING") == "Connector"
    assert asset_word("EV_CHARGER", "EV_CHARGING") == "Charger"
    assert asset_word("POWER_CONVERSION_SYSTEM", "MINIGRID") == "Power conversion system"
    assert asset_word(None, "MINIGRID") is None


def test_asset_label_appends_the_code_only_when_ambiguous() -> None:
    assert asset_label("generator-1", "GENERATOR", "COLDCHAIN", 1) == "Backup generator"
    assert asset_label("compressor-1", "COMPRESSOR", "COLDCHAIN", 1) == "Compressor"
    assert asset_label("battery", "BATTERY", "EV_CHARGING", 1) == "Battery"
    assert asset_label("c1", "CONNECTOR", "EV_CHARGING", 2) == "Connector c1"
    assert asset_label("c1", "CONNECTOR", "EV_CHARGING", 0) == "Connector"  # the asset itself retired
    assert asset_label("generator-1", "GENERATOR", "MINIGRID", None) == "Generator"
    assert asset_label(None, "GENERATOR", "MINIGRID", 1) is None
    assert asset_label("x-1", None, "MINIGRID", 3) == "x-1"


def test_work_rows_carry_label_and_type() -> None:
    row = {"asset_code": "generator-1", "asset_type": "GENERATOR", "asset_type_count": 1}
    assert asset_fields(row, "COLDCHAIN") == ("Backup generator", "GENERATOR")
    assert asset_fields({"asset_code": None, "asset_type": None}, "COLDCHAIN") == (None, None)
    assert asset_fields({"asset_code": "c2", "asset_type": "CONNECTOR", "asset_type_count": 2}, "EV_CHARGING") == (
        "Connector c2", "CONNECTOR")


def test_repeat_warning_names_the_plain_asset() -> None:
    assert visits.asset_name("Backup generator") == "Backup generator"
    assert visits.asset_name(None) == ""
