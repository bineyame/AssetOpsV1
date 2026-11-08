"""OWN-G2 (build sheet OWN-GAPS §2.4, §2.7; rulings R1, R2-G2 Q1-Q4, Q11, Q12): the due-night rule, pure.

Each case names the wrong implementation it fails on. `FakeStore`/`FakeService` are shared with
`test_own_g2_fuel_night_stage.py`.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

import pytest

from assetops_backend.fuel_balance import rules, scheduled
from assetops_backend.fuel_balance.model import AssessResult, DuePlan, FuelBalanceRefused, ScheduleInputs
from assetops_backend.fuel_balance.scheduled import due_nights, latest_closed_night, night_of, run_site

TZ = "Africa/Dar_es_Salaam"  # UTC+3, no DST
UTC = timezone.utc
EAT = timezone(timedelta(hours=3))
L = date(2026, 11, 5)
END_L = datetime(2026, 11, 6, 9, 0, tzinfo=UTC)  # night L ends 12:00 local on 6 Nov
KNOWN = END_L + timedelta(hours=2)
TANK, GEN = "00000000-0000-0000-0000-00000000000a", "00000000-0000-0000-0000-00000000000b"


def inputs(reading_nights=None, records=(), latest=None, known_at=KNOWN, tank=TANK) -> ScheduleInputs:
    return ScheduleInputs(known_at, TZ, tank, None if tank is None else GEN, dict(reading_nights or {}),
                          tuple(records), dict(latest or {}))


def seen(*nights: date, at: datetime = KNOWN - timedelta(hours=1)) -> dict[date, datetime]:
    return {n: at for n in nights}


def inside(night: date) -> datetime:
    """An instant inside night `night` (local 23:00)."""
    return datetime.combine(night, time(23), EAT).astimezone(UTC)


# --- shared fakes ------------------------------------------------------------------------------------------------


class Window:
    def __init__(self, revision: int, state: str = "WITHIN_MARGIN") -> None:
        self.revision, self.state = revision, state


class Raised:
    def __init__(self, status: str) -> None:
        self.status = status


class FakeStore:
    """`schedule_inputs` plus scripted assess outcomes; every call is recorded."""

    def __init__(self, data: ScheduleInputs, outcomes: dict | None = None) -> None:
        self.data, self.outcomes, self.calls = data, outcomes or {}, []

    def schedule_inputs(self, tenant_id, site_id, record_lookback):
        self.calls.append(("schedule_inputs", record_lookback))
        return self.data

    def assess(self, night: date):
        self.calls.append(("assess", night))
        outcome = self.outcomes.get(night, ("APPENDED", 1))
        if isinstance(outcome, Exception):
            raise outcome
        status, revision = outcome
        return AssessResult(Window(revision), status == "APPENDED")


class FakeService:
    def __init__(self, store: FakeStore) -> None:
        self.store = store

    def assess_night(self, tenant_id, site_id, night):
        return self.store.assess(night)


class FakeFindings:
    def __init__(self, statuses: dict | None = None) -> None:
        self.statuses, self.calls = statuses or {}, []

    def raise_night(self, tenant_id, site_id, night):
        self.calls.append(night)
        return Raised(self.statuses.get(night, "NO_FINDING"))


@pytest.fixture(autouse=True)
def fake_service(monkeypatch):
    monkeypatch.setattr(scheduled, "FuelBalanceService", FakeService)


# --- 1. bucket edges (R2-G2 Q1) ----------------------------------------------------------------------------------


def test_1_bucket_edges_in_site_local_time() -> None:
    d = date(2026, 11, 5)
    assert night_of(datetime(2026, 11, 5, 17, 29)) is None          # fails if the bucket starts at 17:00
    assert night_of(datetime(2026, 11, 5, 17, 30)) == d             # fails if it starts at 18:00
    assert night_of(datetime(2026, 11, 6, 12, 29)) == d             # fails if it ends at 12:00
    assert night_of(datetime(2026, 11, 6, 12, 30)) == d  # fails if the end is open (the closing search includes end + 30 min)
    assert night_of(datetime(2026, 11, 6, 12, 30, 1)) is None  # fails past end + 30 min
    assert night_of(datetime(2026, 11, 5, 17, 29, 59)) is None
    assert scheduled.bucket_bounds() == (time(17, 30), time(12, 30))


def test_1_rev1_the_bucket_follows_the_rule_constants(monkeypatch) -> None:
    monkeypatch.setattr(rules, "NIGHT_START", time(19))
    monkeypatch.setattr(rules, "NIGHT_END", time(11))
    assert scheduled.bucket_bounds() == (time(18, 30), time(11, 30))  # fails on typed literals
    assert night_of(datetime(2026, 11, 5, 17, 30)) is None
    assert night_of(datetime(2026, 11, 5, 18, 30)) == date(2026, 11, 5)
    assert night_of(datetime(2026, 11, 6, 11, 30)) == date(2026, 11, 5)
    assert night_of(datetime(2026, 11, 6, 11, 30, 1)) is None


# --- 2. closed edge ----------------------------------------------------------------------------------------------


def test_2_closed_edge_is_the_service_rule() -> None:
    assert latest_closed_night(TZ, END_L + timedelta(minutes=30)) == L          # end + EDGE <= known_at
    assert latest_closed_night(TZ, END_L + timedelta(minutes=30, seconds=-1)) == L - timedelta(days=1)


# --- 3. a closed night with no reading is not due (the S+1 case) -------------------------------------------------


def test_3_a_closed_night_without_readings_is_not_due() -> None:
    plan = due_nights(inputs(seen(L - timedelta(days=1))))
    assert plan == DuePlan(True, (L - timedelta(days=1),))  # fails if range(L-6, L+1) is used directly
    assert due_nights(inputs({})) == DuePlan(True, ())


def test_3_an_open_night_with_readings_is_not_due() -> None:
    plan = due_nights(inputs(seen(L, L + timedelta(days=1))))
    assert plan.nights == (L,)  # night L+1 is still open at KNOWN


# --- 4. quiet ----------------------------------------------------------------------------------------------------


def test_4_quiet_five_minutes() -> None:
    assert due_nights(inputs(seen(L, at=KNOWN - timedelta(minutes=4, seconds=59)))).nights == ()
    assert due_nights(inputs(seen(L, at=KNOWN - timedelta(minutes=5)))).nights == (L,)


# --- 5. record set -----------------------------------------------------------------------------------------------


def test_5_record_set() -> None:
    old = L - timedelta(days=10)
    held = KNOWN - timedelta(days=9)
    base = seen(old)
    # a record on night L-10 recorded after the night's latest window -> due
    later = inputs(base, [(inside(old), held + timedelta(seconds=1))], {old: held})
    assert due_nights(later).nights == (old,)
    # recorded_at == latest -> not due (fails on >=)
    assert due_nights(inputs(base, [(inside(old), held)], {old: held})).nights == ()
    # a night with no window and a record -> due
    assert due_nights(inputs(base, [(inside(old), held)], {})).nights == (old,)
    # a record on a night without readings -> not due (a record is only a trigger of a ready night)
    assert due_nights(inputs({}, [(inside(old), held)], {})).nights == ()
    # a record between nights (local 14:00) touches no night
    midday = datetime.combine(old, time(14), EAT).astimezone(UTC)
    assert due_nights(inputs(base, [(midday, held)], {})).nights == ()


def test_5_records_older_than_the_lookback_are_not_read() -> None:
    """The 32-day record never reaches `due_nights`: the read range is `[known_at - RECORD_LOOKBACK, known_at]`
    (the Postgres file proves the read); here the lookback the stage asks for is pinned."""
    store = FakeStore(inputs({}))
    run_site(store, FakeFindings(), "t", "s", 10, None)
    assert store.calls == [("schedule_inputs", timedelta(days=31))]
    assert scheduled.RECORD_LOOKBACK == timedelta(days=31) and scheduled.QUIET == timedelta(minutes=5)
    assert scheduled.BASE_NIGHTS == 7 and scheduled.EDGE == timedelta(minutes=30)


def test_base_set_is_the_last_seven_closed_nights() -> None:
    nights = [L - timedelta(days=k) for k in range(0, 9)]
    plan = due_nights(inputs(seen(*nights)))
    assert plan.nights == tuple(sorted(nights[:7]))  # L-7 and L-8 need a record to be due


# --- 6. order and limit ------------------------------------------------------------------------------------------


def test_6_ascending_order_and_limit() -> None:
    nights = [L - timedelta(days=k) for k in range(5)]
    store = FakeStore(inputs(seen(*nights)))
    out = run_site(store, FakeFindings(), "t", "s", 3, None)
    assert [c[1] for c in store.calls if c[0] == "assess"] == sorted(nights)[:3]
    assert (out["processed"], out["deferred"]) == (3, 2) and out["eligible"] is True
    assert [n["night_date"] for n in out["nights"]] == [d.isoformat() for d in sorted(nights)[:3]]


# --- 7. ineligible (R2-G2 Q12) -----------------------------------------------------------------------------------


@pytest.mark.parametrize("why", ["no tank", "two generators"])
def test_7_ineligible_makes_one_read_and_no_assess_or_raise(why) -> None:
    # The adapter returns tank=None for 0 tanks and for 2 generators alike (`schedule_inputs`).
    store, findings = FakeStore(inputs(seen(L), tank=None)), FakeFindings()
    out = run_site(store, findings, "t", "s", 10, None)
    assert out == {"code": "OK", "eligible": False, "processed": 0, "deferred": 0}
    assert [c[0] for c in store.calls] == ["schedule_inputs"] and findings.calls == []
    assert due_nights(inputs(seen(L), tank=None)) == DuePlan(False, ())


def test_assets_unsupported_mid_run_stops_as_ineligible() -> None:
    from assetops_backend.fuel_balance.model import ASSETS_UNSUPPORTED

    nights = [L - timedelta(days=1), L]
    store = FakeStore(inputs(seen(*nights)), {L: FuelBalanceRefused(ASSETS_UNSUPPORTED, "two tanks now")})
    out = run_site(store, FakeFindings(), "t", "s", 10, None)
    assert out["eligible"] is False and (out["processed"], out["deferred"]) == (1, 1)
