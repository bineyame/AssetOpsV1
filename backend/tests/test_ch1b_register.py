"""CH-1b L0 (build sheet CH-1b §2, §6 step 1): register resolution per event type, Site-local days included.

`EVENT_FIXTURES` holds one resolution fixture per register event type; the register guard
(`tools/checks/test_event_register.py`) fails when a register type has none.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest

from assetops_backend.chain.adapters.file_chain_config import load_event_register
from assetops_backend.chain.events import Event, RegisterError, local_days, parse_register, resolve

UTC = timezone.utc
ADDIS = "Africa/Addis_Ababa"  # UTC+3, no DST
TODAY = date(2026, 11, 3)
D = date

#: ANY-1 AR-2: the board's stored mini depth kinds (`config/chain/event-register-v1.yaml` kinds).
MINI_KINDS = ("mini_depth.backup", "mini_depth.fuel", "mini_depth.renewable", "mini_depth.service")
#: type@version -> (subject, site type, timezone, expected (day, measure) marks, consumers)
EVENT_FIXTURES = {
    "reading.accepted@1": (
        {"roles": ["feeder_demand"], "asset_ids": [], "span": ["2026-10-30T20:30:00Z", "2026-10-30T21:30:00Z"]},
        "MINIGRID", ADDIS, {(d, m) for d in (D(2026, 10, 30), D(2026, 10, 31))
                            for m in ("productive_kwh", *MINI_KINDS, "dispatch.day")},  # AR-2 mini kinds; AR-3: the UTC days of [20:30Z - 6 h, 21:30Z + 6 h)
        ("snapshots",)),
    "assessment.revised@1": (
        {"analytic_ids": ["cold-start-response"], "windows": [["2026-10-31T00:00:00Z", "2026-10-31T01:00:00Z"]]},
        "COLDCHAIN", "UTC", {(D(2026, 10, 31), "backup_start_chain")}, ("snapshots",)),
    "job.changed@1": (
        {"domain": "ev_charging", "window": ["2026-11-01T22:00:00Z", "2026-11-02T02:00:00Z"], "status": "PENDING"},
        "EV_CHARGING", "UTC", {(D(2026, 11, 1), "charging_kwh"), (D(2026, 11, 2), "charging_kwh")}, ("snapshots",)),
    "price.revised@1": (
        {"key": "productive_use_price_per_kwh", "valid": ["2026-10-29T21:00:00Z", None]},
        # AR-4 contract line (rev 5): an open price revision restates money.lines from its valid date to today.
        "MINIGRID", ADDIS, {(D(2026, 10, 30) + timedelta(days=i), m) for i in range(5)
                            for m in ("productive_kwh", "money.lines")},
        ("snapshots",)),
    "foundation.revised@1": (
        {"valid_from": "2026-11-02T00:00:00Z"}, "MINIGRID", "UTC",
        {(d, m) for d in (D(2026, 11, 2), D(2026, 11, 3))
         for m in ("productive_kwh", "daylight_headroom_kw", "critical_served", "avoidable_gen_min", *MINI_KINDS,
                   "money.lines")}  # AR-4: money lines are a Site-local day kind
        # AR-3: UTC days from valid_from - 6 h through today + 1 (a UTC day can be one past the Site-local today);
        # AR-4's `evidence.claim` is an s3_day kind too, so it takes the same UTC days
        | {(d, m) for d in (D(2026, 11, 1), D(2026, 11, 2), D(2026, 11, 3), D(2026, 11, 4))
           for m in ("dispatch.day", "evidence.claim")},
        ("snapshots",)),
    "objective.revised@1": ({"ids": ["o1"]}, "MINIGRID", "UTC", set(), ()),
    "finding.revised@1": ({"ids": ["f1"]}, "COLDCHAIN", "UTC", set(), ("threads",)),
    "opportunity.revised@1": ({"ids": ["p1"]}, "MINIGRID", "UTC", set(), ("threads",)),
    "action.event@1": ({"ids": ["a1"]}, "MINIGRID", "UTC", set(), ("threads", "lifecycle")),
    "verification.outcome@1": ({"ids": ["v1"]}, "MINIGRID", "UTC", set(), ("lifecycle",)),
    "backfill.site@1": ({"from": "2026-10-01", "to": "2026-11-03"}, "MINIGRID", "UTC", set(), ()),
}


def _event(key: str, subject: dict) -> Event:
    name, _, version = key.partition("@")
    now = datetime(2026, 11, 3, tzinfo=UTC)
    return Event(uuid4(), name, int(version), now, now, "test", uuid4(), uuid4(), subject)


@pytest.mark.parametrize("key", sorted(EVENT_FIXTURES))
def test_each_event_type_resolves_to_its_days_and_measures(key: str) -> None:
    register = load_event_register()
    subject, site_type, tz, expected, consumers = EVENT_FIXTURES[key]
    assert set(resolve(register, _event(key, subject), site_type=site_type, tz=tz, today=TODAY)) == expected
    assert register.events[key].consumers == consumers


def test_every_register_type_has_a_fixture() -> None:
    assert set(load_event_register().events) == set(EVENT_FIXTURES)


def test_mini_depth_assessment_dirties_headroom_only() -> None:
    subject = {"domain": "renewable", "windows": [["2026-11-01T09:00:00Z", "2026-11-01T10:00:00Z"]]}
    marks = resolve(load_event_register(), _event("assessment.revised@1", subject), site_type="MINIGRID", tz="UTC",
                    today=TODAY)
    assert marks == [(D(2026, 11, 1), "daylight_headroom_kw"), (D(2026, 11, 1), "mini_depth.renewable"),
                     (D(2026, 11, 1), "money.lines")]  # AR-4 MN-2: the potential's study reads renewable


def test_a_measure_of_another_site_type_is_never_marked() -> None:
    subject = {"roles": ["chamber_temperature"], "span": ["2026-11-01T09:00:00Z", "2026-11-01T10:00:00Z"]}
    assert resolve(load_event_register(), _event("reading.accepted@1", subject), site_type="MINIGRID", tz="UTC",
                   today=TODAY) == []


@pytest.mark.parametrize("start, end, tz, expected", [
    # local midnight in Addis is 21:00Z: a span across it marks both local days
    ("2026-10-30T20:59:00Z", "2026-10-30T21:01:00Z", ADDIS, [D(2026, 10, 30), D(2026, 10, 31)]),
    # the same span in UTC stays on one day
    ("2026-10-30T20:59:00Z", "2026-10-30T21:01:00Z", "UTC", [D(2026, 10, 30)]),
    # the end is exclusive: a span ending exactly at local midnight does not touch the next day
    ("2026-10-30T20:00:00Z", "2026-10-30T21:00:00Z", ADDIS, [D(2026, 10, 30)]),
    # a point reading is its start day
    ("2026-10-30T21:00:00Z", "2026-10-30T21:00:00Z", ADDIS, [D(2026, 10, 31)]),
    # an open end runs to today, and every day is clamped to today
    ("2026-11-02T00:00:00Z", None, "UTC", [D(2026, 11, 2), D(2026, 11, 3)]),
    ("2026-11-05T00:00:00Z", "2026-11-06T00:00:00Z", "UTC", []),
])
def test_local_days(start, end, tz, expected) -> None:
    assert local_days(start, end, tz, TODAY) == expected


@pytest.mark.parametrize("payload", [
    {"register_version": 2, "events": {}, "inputs": {}},
    {"register_version": 1, "events": {"reading": {"days": "none"}}, "inputs": {}},
    {"register_version": 1, "events": {"a.b@1": {"days": "weekly"}}, "inputs": {}},
    {"register_version": 1, "events": {"a.b@1": {"days": "none", "measures": "by_role"}}, "inputs": {}},
    {"register_version": 1, "events": {"a.b@1": {"days": "none", "consumer": "outcomes"}}, "inputs": {}},
    {"register_version": 1, "events": {}, "inputs": {"m": {"outcomes": ["x"]}}},
])
def test_malformed_register_is_refused(payload) -> None:
    with pytest.raises(RegisterError):
        parse_register(payload)
