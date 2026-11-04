"""MD-0 L0 (build sheet §10.1): the mechanism fixture's schema rules, the Dn map, the EV calendar, the gap
placement, the `late_fill` refusals and the `MECHANISM_DB_ONLY` name check. Pure: no database."""

from __future__ import annotations

import copy
from datetime import date, datetime, timezone

import pytest

import mechanism_dataset as md
from assetops_backend.evidence.adapters.authored_fixture_specs import AuthoredFixtureSpecs

SPEC = md.load()


def test_the_fixture_is_a_declared_authored_fixture() -> None:
    assert AuthoredFixtureSpecs().declared(md.FIXTURE_ID) == (md.FIXTURE_ID, md.FIXTURE_VERSION)


def test_dn_map() -> None:
    assert md.day(SPEC, 1) == date(2026, 10, 19) and md.day(SPEC, 1).weekday() == 0
    assert md.day(SPEC, 13) == date(2026, 10, 31) and md.day(SPEC, 14) == date(2026, 11, 1)
    assert md.day(SPEC, 13).isoformat() == SPEC["story"]["S"][:10]
    assert [n for n in range(1, 15) if md.day(SPEC, n).weekday() == 1] == [2, 9]
    assert md.local_instant(SPEC, "kobo", 1, "00:00") == datetime(2026, 10, 18, 21, tzinfo=timezone.utc)
    assert md.local_instant(SPEC, "cold", 3, "24:00") == datetime(2026, 10, 21, 21, tzinfo=timezone.utc)
    assert md.local_instant(SPEC, "ev", 2, "08:00") == datetime(2026, 10, 20, 8, tzinfo=timezone.utc)


def test_ev_days_are_the_declared_tuesdays() -> None:
    for name in md.DAY_SETS:
        assert SPEC["day_sets"][name]["ev"] == [2, 9]
    bad = copy.deepcopy(SPEC)
    bad["day_sets"]["full"]["ev"] = [2, 3]
    with pytest.raises(ValueError, match="not a Tuesday"):
        md.validate(bad)
    late = copy.deepcopy(SPEC)
    late["sites"]["ev"]["sessions"]["first_local"] = "09:00"
    with pytest.raises(ValueError, match="08:00-16:00"):
        md.validate(late)


def test_gaps_avoid_events_actions_and_studies() -> None:
    fixed = md._event_and_action_days(SPEC)
    assert all((g["site"], g["day"]) not in fixed for g in SPEC["gaps"])
    bad = copy.deepcopy(SPEC)
    bad["gaps"][0]["day"] = 4  # GAP-K7 onto the D4 overrun
    with pytest.raises(ValueError, match="gap falls"):
        md.validate(bad)
    for name in md.DAY_SETS:
        assert 7 not in SPEC["day_sets"][name]["kobo"]


@pytest.mark.parametrize("mutate, message", [
    (lambda s: s["sites"]["kobo"]["events"][0].pop("source"), "no source"),
    (lambda s: s["sites"]["cold"]["events"][0].__setitem__("grade", "COMPLETE"), "output key"),
    (lambda s: s["threads"][0].__setitem__("state", "OPEN"), "output key"),
    (lambda s: s.__setitem__("note", "objective MG-1"), "outcome id"),
    (lambda s: s.__setitem__("schema", "assetops.mechanism-dataset"), "schema"),
])
def test_schema_rules_refuse(mutate, message) -> None:
    bad = copy.deepcopy(SPEC)
    mutate(bad)
    with pytest.raises(ValueError, match=message):
        md.validate(bad)


def test_late_fill_refuses_all_but_the_declared_fillable_gap() -> None:
    assert md.fill_target(SPEC, "KOBO-001", 7)["id"] == "GAP-K7"
    assert md.fill_target(SPEC, "KOBO-001", 7, "overrun")["id"] == "GAP-K7"
    for code, args in (("DUPLICATE_DAY", ("KOBO-001", 6)), ("DAY_HAS_EVIDENCE", ("COLD-LAB-001", 3)),
                       ("DAY_HAS_EVIDENCE", ("EV-LAB-001", 2)), ("PREPARE_ONLY_KIND", ("KOBO-001", 7, "action"))):
        with pytest.raises(md.MechanismRefused, match=code):
            md.fill_target(SPEC, *args)


@pytest.mark.parametrize("name, allowed", [
    ("assetops_mechanism_test", True),
    ("assetops_mechanism_close_test", True),
    ("assetops_pt1a2b_main_test", True),
    ("assetops_pt7_gw3_test", True),
    ("assetops_polish_full_test", False),
    ("assetops_demo3_full_test", False),
    ("assetops_polish_client_test", False),
    ("assetops_test", False),
    ("assetops_mechanism", False),
    ("assetops_polish_pt1_main_test", False),
])
def test_mechanism_db_only(name, allowed) -> None:
    assert md.mechanism_db_allowed(name) is allowed
