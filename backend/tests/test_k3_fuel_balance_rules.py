"""DIESEL-K3 L0 (`.agent/build-sheet-DIESEL-1.md` §9d.6 A1-A12): the `fuel-balance-1` rules, no database.

Each "must fail" names the mutation the test kills.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import pytest

from assetops_backend.actions import verification_rules as vr
from assetops_backend.financials import fuel_cost_v2
from assetops_backend.fuel_balance import rules
from assetops_backend.fuel_balance.model import PARAMETER_VERSION, FuelBalanceRefused
from assetops_backend.work.fuel_records import FuelRecord

ROOT = Path(__file__).resolve().parents[2]
PROBE = json.loads((ROOT / ".agent" / "DIESEL-F0" / "probe-result.json").read_text(encoding="utf-8"))
PACKAGE = ROOT / "backend" / "assetops_backend" / "fuel_balance"

TANK, GEN = "tank-1", "gen-1"
NIGHT = date(2026, 10, 4)
START = datetime(2026, 10, 4, 15, 0, tzinfo=timezone.utc)
END = datetime(2026, 10, 5, 9, 0, tzinfo=timezone.utc)
SLOT = timedelta(minutes=5)
A = rules.Declared(Fraction(10), "GENERIC_DEFAULT", "rev-a", START - timedelta(days=30))
SFC = rules.Declared(Fraction(355, 1000), None, "rev-s", START - timedelta(days=30))
R = rules.Declared(Fraction(49, 10), "GENERIC_DEFAULT", "rev-r", START - timedelta(days=30))


def ex(value) -> Fraction | None:
    return None if value is None else Fraction(value["exact"])


# --- synthetic accepted readings -----------------------------------------------------------------------------------


def level(at: datetime, litres, *, quality: str = "GOOD", rid: str | None = None, unit: str = "L") -> vr.Reading:
    return vr.Reading(id=rid or f"lvl-{at.isoformat()}-{litres}", role="fuel_level", asset_id=TANK,
                      measurement="STATE_AT_INSTANT", source_time=at, interval_start=None, interval_end=None,
                      value_text=str(litres), unit=unit, quality=quality)


def power(t: datetime, kw: str, *, quality: str = "GOOD") -> vr.Reading:
    return vr.Reading(id=f"pow-{t.isoformat()}", role="generator_power", asset_id=GEN, measurement="INTERVAL_MEAN",
                      source_time=t + SLOT, interval_start=t, interval_end=t + SLOT, value_text=kw, unit="kW",
                      quality=quality)


def state(t: datetime, value: str) -> vr.Reading:
    return vr.Reading(id=f"st-{t.isoformat()}", role="generator_state", asset_id=GEN, measurement="STATE_AT_INSTANT",
                      source_time=t, interval_start=None, interval_end=None, value_text=value, unit="state",
                      quality="GOOD")


def slots(start: datetime = START, end: datetime = END) -> list[datetime]:
    out, t = [], start
    while t < end:
        out.append(t)
        t += SLOT
    return out


def generator(kw=lambda i: "0", st=lambda i: "STOPPED", start: datetime = START, end: datetime = END,
              skip_power: int | None = None, skip_state: int | None = None, bad_power: int | None = None):
    out = []
    for i, t in enumerate(slots(start, end)):
        if i != skip_power:
            out.append(power(t, kw(i), quality="SUSPECT" if i == bad_power else "GOOD"))
        if i != skip_state:
            out.append(state(t, st(i)))
    return out


def levels(opening, closing, every_min: int = 30) -> list[vr.Reading]:
    """O at START, C at END and the opening value every `every_min` minutes in between (no reporting gap)."""
    out = [level(START, opening), level(END, closing)]
    t = START + timedelta(minutes=every_min)
    while t < END:
        out.append(level(t, opening))
        t += timedelta(minutes=every_min)
    return out


def record(kind: str, at: datetime, litres, *, root_recorded_at: datetime | None = None, n: int = 1) -> FuelRecord:
    rec = root_recorded_at or at + timedelta(minutes=15)
    return FuelRecord(root_id=f"root-{n}", head_id=f"head-{n}", code=f"REC-00000{n}", kind=kind, occurred_at=at,
                      recorded_at=rec, root_recorded_at=rec, quantity_l=Decimal(vr.fmt(Fraction(litres))),
                      ticket_sha256="ab" * 32 if kind == "FUEL_DELIVERY" else None, actor_id="service:test",
                      body="test")


def assess(readings, records=(), accuracy=A, sfc=SFC, no_load=R):
    return rules.assess(start=START, end=END, tank_asset_id=TANK, generator_asset_id=GEN, readings=readings,
                        records=list(records), accuracy=accuracy, sfc=sfc, no_load=no_load)


def band(opening, closing, loaded, deliveries=(), idle_h=0, a=10, r=Fraction(49, 10)):
    return rules.balance(opening=Fraction(opening), closing=Fraction(closing), deliveries=[Fraction(d) for d in deliveries],
                         loaded_litres=Fraction(loaded), idle_hours=Fraction(idle_h), accuracy_l=Fraction(a),
                         no_load_l_per_h=r)


# --- A1 parameters ---------------------------------------------------------------------------------------------------


def test_a1_parameters_are_f0_verbatim() -> None:
    import probe_kisiwa_fuel as f0

    declared = {k: v for k, v in rules.PARAMETERS.items() if k != "parameter_version"}
    assert declared == PROBE["assumptions"]["fuel_balance_1"] == f0.PARAMETERS
    assert rules.PARAMETERS["parameter_version"] == PARAMETER_VERSION == "fuel-balance-1/v1"
    assert rules.TANK_MARGIN_FACTOR * f0.ACCURACY_L == f0.TANK_MARGIN_L
    assert rules.DELIVERY_TOLERANCE == f0.DELIVERY_TOLERANCE == Fraction(1, 100)
    assert (rules.USE_LOW_FACTOR, rules.USE_HIGH_FACTOR) == (f0.USE_LOW_FACTOR, f0.USE_HIGH_FACTOR)
    assert rules.MATERIALITY_L == f0.MATERIALITY_L == 40
    assert (rules.EDGE_SEARCH_MIN, rules.GAP_LONGER_THAN_MIN, rules.SLOT_MIN) == (f0.EDGE_SEARCH_MIN,
                                                                                  f0.GAP_LONGER_THAN_MIN, f0.STEP)
    assert Fraction(fuel_cost_v2.MULTIPLIER) == rules.USE_HIGH_FACTOR


# --- A2 rule parity over all 10 nights ------------------------------------------------------------------------------


def _parity(terms: dict, ref: dict) -> None:
    keys = ("residual_low", "residual_high", "use_low", "use_high", "opening_minus_closing", "deliveries",
            "delivery_tolerance")
    got = band(terms["opening"], terms["closing"], terms["loaded"], terms["deliveries"])
    assert got["state"] == ref["state"]
    for key in keys:
        assert got[key] == ex(ref[key]), key


def test_a2_rule_parity_all_ten_nights() -> None:
    nights = PROBE["nights"]
    assert len(nights) == 10
    for night in nights:
        loaded = ex(night["loaded_litres"])
        assert night["idle_minutes"] == 0
        common = {"loaded": loaded, "deliveries": night["deliveries_l"]}
        read = night["readings"]
        assert read["state"] != "NOT_ASSESSED"
        _parity({**common, "opening": ex(night["opening_reading_l"]), "closing": ex(night["closing_reading_l"])},
                read)
        true = night["true_tank"]
        _parity({**common, "opening": ex(true["opening_minus_closing"]), "closing": 0}, true)


# --- A3 the idle term -------------------------------------------------------------------------------------------------


def _idle_night(r: rules.Declared) -> rules.WindowResult:
    running = set(range(25))  # 25 RUNNING samples at 0 kW, STOPPED from 25: 24 idle slots (slot 24 is the stop slot) = 7200 s
    readings = levels(100, 35) + generator(st=lambda i: "RUNNING" if i in running else "STOPPED")
    return assess(readings, no_load=r)


def test_a3_idle_term() -> None:
    out = _idle_night(R)
    assert out.terms["idle_seconds"] == 7200 and out.terms["loaded_litres"] == "0"
    assert Fraction(out.terms["use_high"]) == Fraction(539, 50) and Fraction(out.terms["use_low"]) == 0
    assert out.residual_low == Fraction(1711, 50)
    assert out.state == "BELOW_MATERIALITY"  # without the idle term: residual_low 45, UNEXPLAINED
    other = _idle_night(rules.Declared(Fraction(33, 10), "GENERIC_DEFAULT", "rev-r2", START - timedelta(days=1)))
    assert Fraction(other.terms["use_high"]) == Fraction(363, 50)  # r is the declared value, not a constant


# --- A14 the Kisiwa stop shape (DIESEL-1-R3h) ---------------------------------------------------------------------------


def test_a14_stop_slot_is_not_idle() -> None:
    k = 20
    kw = lambda i: "38" if i == k else "0"  # noqa: E731
    stop = generator(kw=kw, st=lambda i: "RUNNING" if k <= i <= k + 1 else "STOPPED")
    mine = rules.use_from_readings(START, END, stop, GEN)
    assert mine["idle_seconds"] == 0 and mine["generator_kwh"] is not None
    # converse: RUNNING at k+1 and k+2, 0 kW over both, STOPPED at k+3: slot k+1 idle, slot k+2 the stop slot
    longer = generator(kw=kw, st=lambda i: "RUNNING" if k <= i <= k + 2 else "STOPPED")
    assert rules.use_from_readings(START, END, longer, GEN)["idle_seconds"] == 300


# --- A4 the edges -------------------------------------------------------------------------------------------------------


def test_a4_edges() -> None:
    zero = band(500, 436, 40)
    assert zero["residual_low"] == 0 and zero["residual_high"] == 48 and zero["state"] == "WITHIN_MARGIN"
    forty = band(540, 436, 40)
    assert forty["residual_low"] == 40 and forty["state"] == "UNEXPLAINED"
    below = band(Fraction(540) - Fraction(1, 1000), 436, 40)
    assert below["residual_low"] == 40 - Fraction(1, 1000) and below["state"] == "BELOW_MATERIALITY"
    high0 = band(452, 436, 40)
    assert high0["residual_high"] == 0 and high0["state"] == "WITHIN_MARGIN"
    excess = band(451, 436, 40)
    assert excess["residual_high"] < 0 and excess["state"] == "EXCESS"


# --- A5 the delivery night high edge --------------------------------------------------------------------------------


def test_a5_delivery_night_exact() -> None:
    out = band(Fraction(656071667, 1000000), Fraction(912643333, 1000000), Fraction(26057, 600), [300])
    assert out["residual_high"] == Fraction(13671417, 500000)
    assert out["residual_low"] == Fraction(-41014249, 1500000)
    assert out["delivery_tolerance"] == 3
    assert band(500, 436, 40, [300, 150])["delivery_tolerance"] == Fraction(9, 2)


# --- A6 use only from accepted generator readings -------------------------------------------------------------------


def _kw(i: int) -> str:
    return "0" if i % 7 == 3 else f"{12 + i % 5}.{i:06d}"


def test_a6_use_from_accepted_readings() -> None:
    gen = generator(kw=_kw, st=lambda i: "RUNNING")
    out = assess(levels(700, 650) + gen)
    total = sum((Fraction(Decimal(_kw(i))) * Fraction(5, 60) for i in range(216)), Fraction(0))
    assert Fraction(out.terms["generator_kwh"]) == total
    assert Fraction(out.terms["loaded_litres"]) == Fraction(355, 1000) * total
    idle = sum(1 for i in range(216) if _kw(i) == "0")
    assert out.terms["idle_seconds"] == 300 * idle and out.reason is None

    for broken, reason in ((dict(skip_power=10), "GENERATOR_KWH_UNKNOWN"), (dict(skip_state=10), "IDLE_SECONDS_UNKNOWN"),
                           (dict(bad_power=10), "GENERATOR_KWH_UNKNOWN")):
        res = assess(levels(700, 650) + generator(kw=_kw, st=lambda i: "RUNNING", **broken))
        assert (res.state, res.reason, res.residual_low) == ("NOT_ASSESSED", reason, None), broken
        assert res.terms["unknown_slots"] == 1


def test_a6_kwh_and_idle_equal_a2_window_evidence() -> None:
    hour = START + timedelta(hours=2)
    gen = generator(kw=_kw, st=lambda i: "RUNNING")
    mine = rules.use_from_readings(hour, hour + timedelta(hours=1), gen, GEN)
    a2 = vr.window_evidence(hour, gen, load_asset_ids=[], critical_load_asset_id=None, reserves=[])
    assert vr.fmt(mine["generator_kwh"]) == a2["generator_kwh"]
    assert mine["idle_seconds"] == a2["generator_idle_seconds"] > 0
    # with a stop slot inside the hour (slot 24 is 0 kW, STOPPED from slot 25): both rules drop it, and agree
    stopped = generator(kw=_kw, st=lambda i: "RUNNING" if i <= 24 else "STOPPED")
    mine = rules.use_from_readings(hour, hour + timedelta(hours=1), stopped, GEN)
    a2 = vr.window_evidence(hour, stopped, load_asset_ids=[], critical_load_asset_id=None, reserves=[])
    assert mine["idle_seconds"] == a2["generator_idle_seconds"] == 0


def test_a6_static_no_run_or_simulator_reads() -> None:
    banned = re.compile(r"^\s*(?:from|import)\s+(assetops_simulator|host|tools|assetops_backend\.runs)\b", re.M)
    files = sorted(PACKAGE.rglob("*.py"))
    assert len(files) >= 7
    for path in files:
        source = path.read_text(encoding="utf-8")
        assert not banned.search(source), path
        assert "trajectory" not in source.lower(), path


# --- A7 opening and closing -----------------------------------------------------------------------------------------


def _levels(*pairs):
    return rules.accepted_levels([level(t, v) for t, v in pairs], TANK)


def test_a7_opening_and_closing() -> None:
    m = timedelta(minutes=1)
    o, c, conflict = rules.opening_closing(_levels((START, 700), (END, 650)), START, END)
    assert o == (START, 700) and c == (END, 650) and not conflict
    o, c, _ = rules.opening_closing(_levels((START - 30 * m, 701), (END + 30 * m, 651)), START, END)
    assert o == (START - 30 * m, 701) and c == (END + 30 * m, 651)
    o, c, _ = rules.opening_closing(_levels((START - 31 * m, 701), (END + 31 * m, 651)), START, END)
    assert o is None and c is None
    o, c, _ = rules.opening_closing(_levels((START - 20 * m, 1), (START - 5 * m, 2), (END + 5 * m, 3),
                                            (END + 20 * m, 4)), START, END)
    assert o[1] == 2 and c[1] == 3  # last in range opening, first in range closing

    gen = generator()
    assert assess([level(END, 650)] + gen).reason == "MISSING_OPENING"
    assert assess([level(START, 700)] + gen).reason == "MISSING_CLOSING"
    conflict = assess([level(START, 700, rid="x1"), level(START, 699, rid="x2"), level(END, 650)] + gen)
    assert conflict.reason == "FUEL_LEVEL_CONFLICT"
    same = assess([level(START, 700, rid="x1"), level(START, 700, rid="x2"), level(END, 650)] + gen)
    assert same.reason is None
    ignored = assess([level(START, 700), level(START, 1, quality="SUSPECT"), level(END + SLOT, 2, unit="gal"),
                      level(END, 650)] + gen)
    assert ignored.reason is None and ignored.terms["opening_l"] == "700" and ignored.terms["closing_l"] == "650"


# --- A8 gap -----------------------------------------------------------------------------------------------------------


def test_a8_gap() -> None:
    m = timedelta(minutes=1)
    assert rules.reporting_gap([START + 60 * m, END - 60 * m], START, START + 120 * m) == (0, ())
    assert rules.reporting_gap([START + 61 * m], START, START + 122 * m) == (
        122, ((START, START + 61 * m), (START + 61 * m, START + 122 * m)))
    assert rules.reporting_gap([], START, START + 61 * m) == (61, ((START, START + 61 * m),))
    # night 4: accepted readings every 15 min except 00:45 to 02:30 local (21:45Z to 23:30Z)
    a, b = datetime(2026, 10, 4, 21, 45, tzinfo=timezone.utc), datetime(2026, 10, 4, 23, 30, tzinfo=timezone.utc)
    times = [t for t in slots() if t.minute % 15 == 0 and not a < t < b]
    assert rules.reporting_gap(times, START, END) == (105, ((a, b),))


# --- A9 reason precedence -------------------------------------------------------------------------------------------


def test_a9_reason_precedence() -> None:
    m = timedelta(minutes=1)
    broken_gen = generator(skip_power=4, skip_state=5)
    no_open = [level(END, 650, rid="c1"), level(END, 640, rid="c2")]      # 4, plus 6 at the closing, 7, 8
    no_close = [level(START, 700, rid="o1"), level(START, 690, rid="o2")]  # 5, plus 6 at the opening, 7, 8
    conflict = no_close + [level(END, 650)]                                 # 6, 7, 8
    good = [level(START, 700), level(END + m, 650)]
    cases = [
        (dict(readings=no_open + broken_gen, accuracy=None, sfc=None, no_load=None), "NO_SENSOR_ACCURACY"),
        (dict(readings=no_open + broken_gen, sfc=None, no_load=None), "SFC_MISSING"),
        (dict(readings=no_open + broken_gen, no_load=None), "NO_LOAD_RATE_MISSING"),
        (dict(readings=no_open + broken_gen), "MISSING_OPENING"),
        (dict(readings=no_close + broken_gen), "MISSING_CLOSING"),
        (dict(readings=conflict + broken_gen), "FUEL_LEVEL_CONFLICT"),
        (dict(readings=good + broken_gen), "GENERATOR_KWH_UNKNOWN"),
        (dict(readings=good + generator(skip_state=5)), "IDLE_SECONDS_UNKNOWN"),
    ]
    for kwargs, reason in cases:
        out = assess(**kwargs)
        assert (out.state, out.reason, out.residual_low, out.residual_high) == ("NOT_ASSESSED", reason, None, None)
    assert assess(good + generator()).reason is None


# --- A10 limitations ------------------------------------------------------------------------------------------------


def test_a10_limitations() -> None:
    m = timedelta(minutes=1)
    gen = generator()
    at = START + 120 * m
    base = levels(700, 690)  # a reading every 30 min at 700, so the dip's nearest reading is 700 at `at`
    for dip, present in ((Fraction(720), False), (Fraction(720) + Fraction(1, 1000), True),
                         (Fraction(680), False), (Fraction(680) - Fraction(1, 1000), True)):
        out = assess(base + gen, [record("TANK_DIP", at + 10 * m, dip)])
        assert ("DIP_SENSOR_CONFLICT" in out.limitations) is present, dip
    # ties go to the earlier reading: 700 at `at`, 1000 at `at + 30`; a dip at `at + 15` reads 700
    sparse = [level(START, 700), level(END, 690)]
    tie = assess(sparse + [level(at, 700), level(at + 30 * m, 1000)] + gen, [record("TANK_DIP", at + 15 * m, 705)])
    assert "DIP_SENSOR_CONFLICT" not in tie.limitations
    late_tie = assess(sparse + [level(at, 700), level(at + 30 * m, 1000)] + gen,
                      [record("TANK_DIP", at + 15 * m, 995)])
    assert "DIP_SENSOR_CONFLICT" in late_tie.limitations
    # a dip with no reading within 30 min is not checked
    assert "DIP_SENSOR_CONFLICT" not in assess(sparse + gen, [record("TANK_DIP", at, 1)]).limitations

    for late, present in ((END + 30 * m, False), (END + 30 * m + timedelta(seconds=1), True)):
        out = assess(base + gen, [record("FUEL_DELIVERY", at, 300, root_recorded_at=late)])
        assert ("DELIVERY_RECORDED_LATE" in out.limitations) is present

    everything = assess(sparse + gen, [record("TANK_DIP", START + 5 * m, 1, n=1),
                                       record("FUEL_DELIVERY", at, 300, root_recorded_at=END + 31 * m, n=2)])
    assert everything.limitations == ("REPORTING_GAP", "DIP_SENSOR_CONFLICT", "DELIVERY_RECORDED_LATE")


# --- A11 window -----------------------------------------------------------------------------------------------------


def test_a11_window() -> None:
    start, end = rules.night_window(NIGHT, "Africa/Dar_es_Salaam")
    assert (start, end) == (START, END) and len(slots(start, end)) == 216
    # No IANA zone has a daylight-saving gap at exactly 18:00 (searched 1990-2030); the nearest real gaps at 18:00 are
    # date-line skips. Pacific/Apia skipped 2011-12-30 entirely; Antarctica/Vostok repeated 18:00 on 1994-01-31; and
    # Africa/Monrovia's 1970 offset (-0:44:30) puts 18:00 off a UTC five-minute boundary.
    for night, zone, why in ((date(2011, 12, 30), "Pacific/Apia", "does not exist"),
                             (date(1994, 1, 31), "Antarctica/Vostok", "is ambiguous"),
                             (date(1970, 6, 1), "Africa/Monrovia", "five-minute boundary"),
                             (NIGHT, None, "no time zone"), (NIGHT, "Not/AZone", "unknown")):
        with pytest.raises(FuelBalanceRefused) as bad:
            rules.night_window(night, zone)
        assert bad.value.code == "FUEL_BALANCE_WINDOW_INVALID" and why in bad.value.detail, (zone, bad.value.detail)
    # the night before Apia's skipped day ends at a noon that did not exist either
    with pytest.raises(FuelBalanceRefused):
        rules.night_window(date(2011, 12, 29), "Pacific/Apia")
    assert rules.night_window(date(2011, 12, 31), "Pacific/Apia")[0] == datetime(2011, 12, 31, 4, 0,
                                                                                   tzinfo=timezone.utc)


# --- A12 digest -----------------------------------------------------------------------------------------------------


def test_a12_digest() -> None:
    recs = [record("TANK_DIP", START + SLOT, 700)]

    def digest(evidence):
        return rules.input_sha256(night_date=NIGHT, start=START, end=END, tank_asset_id=TANK, generator_asset_id=GEN,
                                  accuracy=A, sfc=SFC, no_load=R, evidence_ids=evidence, records=recs)

    assert digest(["e2", "e1"]) == digest(["e1", "e2"])
    assert re.fullmatch(r"[0-9a-f]{64}", digest(["e1"]))
    assert digest(["e1", "e2", "e3"]) != digest(["e1", "e2"])


# --- A13 the production path composes (DIESEL-1-R3g) ----------------------------------------------------------------


def test_a13a_work_composition_exposes_k2_reader() -> None:
    from assetops_backend.work import composition as work_composition
    from assetops_backend.work.adapters.postgres_fuel_records import select_fuel_records

    assert "build_fuel_records_reader" in work_composition.__all__
    assert work_composition.build_fuel_records_reader() is select_fuel_records


def test_a13b_default_store_composes_without_connecting() -> None:
    from assetops_backend.actions.adapters.postgres_action_store import PostgresActionStore
    from assetops_backend.fuel_balance.composition import build_fuel_balance_store
    from assetops_backend.work.adapters.postgres_fuel_records import select_fuel_records

    store = build_fuel_balance_store("postgresql://unused@127.0.0.1:1/none")
    assert store._fuel_records is select_fuel_records
    assert isinstance(store._actions, PostgresActionStore)
    assert store._engine is None
    assert store.test_db_clock_override is None


def test_a13c_worker_default_branch_composes(monkeypatch: pytest.MonkeyPatch) -> None:
    from assetops_backend.fuel_balance import composition, worker
    from assetops_backend.work.adapters.postgres_fuel_records import select_fuel_records

    real = composition.build_fuel_balance_store
    calls: list[tuple] = []
    kept: list[object] = []

    def spy(*args, **kwargs):
        calls.append((args, kwargs))
        built = real(*args, **kwargs)
        kept.append(built)
        return built

    monkeypatch.setattr(composition, "build_fuel_balance_store", spy)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL is not set"):
        worker.main(["assess", "--site", "KISIWA-001", "--from", "2026-10-06", "--to", "2026-10-07"])
    assert calls == [((None,), {})]
    assert len(kept) == 1 and kept[0]._fuel_records is select_fuel_records
