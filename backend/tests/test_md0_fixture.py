"""MD-0 L0 (build sheet §10.1): the mechanism fixture's schema rules, the Dn map, the Kobo-only scope (MD0-S2), the
gap placement, the `late_fill` refusals and the `MECHANISM_DB_ONLY` name check. Pure: no database."""

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
    assert md.local_instant(SPEC, "kobo", 14, "24:00") == datetime(2026, 11, 1, 21, tzinfo=timezone.utc)


def test_kobo_only_with_one_recurrence_after_the_apply() -> None:
    # MD0-S2: Cold and EV are removed (their normal data is proved on DD-1's real baseline).
    assert set(SPEC["sites"]) == {"kobo"} and {g["id"] for g in SPEC["gaps"]} == {"GAP-K7"}
    assert all(set(SPEC["day_sets"][n]) == {"kobo", "source"} for n in md.DAY_SETS)
    effective = SPEC["sites"]["kobo"]["actions"][0]["effective"]["day"]
    after = [e["day"] for e in SPEC["sites"]["kobo"]["events"] if e["day"] >= effective]
    assert after == [14] and all(14 in SPEC["day_sets"][n]["kobo"] for n in md.DAY_SETS)
    bad = copy.deepcopy(SPEC)
    bad["sites"]["cold"] = {"site_code": "COLD-LAB-001", "time_zone": "Africa/Addis_Ababa"}
    with pytest.raises(ValueError, match="KOBO-001 only"):
        md.validate(bad)


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
    (lambda s: s["sites"]["kobo"]["events"][1].__setitem__("grade", "COMPLETE"), "output key"),
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
    for code, args in (("DUPLICATE_DAY", ("KOBO-001", 6)), ("DUPLICATE_DAY", ("COLD-LAB-001", 3)),
                       ("PREPARE_ONLY_KIND", ("KOBO-001", 7, "action"))):
        with pytest.raises(md.MechanismRefused, match=code):
            md.fill_target(SPEC, *args)
    held = copy.deepcopy(SPEC)
    held["gaps"][0]["fill"] = False  # a declared gap that holds evidence (the removed GAP-C3/E2 shape)
    with pytest.raises(md.MechanismRefused, match="DAY_HAS_EVIDENCE"):
        md.fill_target(held, "KOBO-001", 7)


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
