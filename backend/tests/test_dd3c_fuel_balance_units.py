"""DD3c part 3 (D-DD.117): the fuel balance on a multi-unit Site. One FUEL_TANK and at least one GENERATOR; the
window's `generator_asset_id` is the lead unit (first GENERATOR in declared Foundation order, D-DD.43); model-implied
litres are the sum of each unit's burn on its own SFC and no-load rate (D-DD.113's shape); the digest and terms
change only above one unit, so a one-unit Site is byte-identical to main (golden captured on main 23d2cd9f6).
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace

import pytest

from assetops_backend.actions import verification_rules as vr
from assetops_backend.fuel_balance import rules
from assetops_backend.fuel_balance.model import ASSETS_UNSUPPORTED, FuelBalanceRefused
from assetops_backend.work.fuel_records import FuelRecord

GOLDEN = Path(__file__).resolve().parent / "fixtures" / "dd3c" / "fuel-balance-one-unit-golden.json"
NIGHT = date(2026, 10, 4)
START = datetime(2026, 10, 4, 15, 0, tzinfo=timezone.utc)
END = datetime(2026, 10, 5, 9, 0, tzinfo=timezone.utc)
SLOT = timedelta(minutes=5)
TANK, GEN, GEN2, OTHER = "tank-1", "gen-1", "gen-2", "gen-9"
SINCE = START - timedelta(days=30)
A = rules.Declared(Fraction(10), "GENERIC_DEFAULT", "rev-a", SINCE)
SFC = rules.Declared(Fraction(355, 1000), None, "rev-s", SINCE)
SFC2 = rules.Declared(Fraction(3, 10), None, "rev-s2", SINCE)
R = rules.Declared(Fraction(49, 10), "GENERIC_DEFAULT", "rev-r", SINCE)
R2 = rules.Declared(Fraction(3), "GENERIC_DEFAULT", "rev-r2", SINCE)


def level(at: datetime, litres) -> vr.Reading:
    return vr.Reading(id=f"lvl-{at.isoformat()}-{litres}", role="fuel_level", asset_id=TANK,
                      measurement="STATE_AT_INSTANT", source_time=at, interval_start=None, interval_end=None,
                      value_text=str(litres), unit="L", quality="GOOD")


def levels(opening, closing) -> list[vr.Reading]:
    out, t = [level(START, opening), level(END, closing)], START + timedelta(minutes=30)
    while t < END:
        out.append(level(t, opening))
        t += timedelta(minutes=30)
    return out


def unit_readings(asset: str, kw=lambda i: "0", st=lambda i: "STOPPED", skip_power: int | None = None):
    out, t, i = [], START, 0
    while t < END:
        if i != skip_power:
            out.append(vr.Reading(id=f"pow-{asset}-{i}", role="generator_power", asset_id=asset,
                                  measurement="INTERVAL_MEAN", source_time=t + SLOT, interval_start=t,
                                  interval_end=t + SLOT, value_text=kw(i), unit="kW", quality="GOOD"))
        out.append(vr.Reading(id=f"st-{asset}-{i}", role="generator_state", asset_id=asset,
                              measurement="STATE_AT_INSTANT", source_time=t, interval_start=None, interval_end=None,
                              value_text=st(i), unit="state", quality="GOOD"))
        t, i = t + SLOT, i + 1
    return out


def record(kind: str, at: datetime, litres, n: int = 1) -> FuelRecord:
    rec = at + timedelta(minutes=15)
    return FuelRecord(root_id=f"root-{n}", head_id=f"head-{n}", code=f"REC-00000{n}", kind=kind, occurred_at=at,
                      recorded_at=rec, root_recorded_at=rec, quantity_l=Decimal(vr.fmt(Fraction(litres))),
                      ticket_sha256="ab" * 32 if kind == "FUEL_DELIVERY" else None, actor_id="service:test",
                      body="test")


def _run(i: int) -> str:
    return "RUNNING" if i < 60 else "STOPPED"


#: One-unit nights, each (readings, records, sfc, no_load); the golden holds main's result and digest for each.
ONE_UNIT_CASES = {
    "loaded": (levels(500, 460) + unit_readings(GEN, kw=lambda i: "10" if i < 60 else "0", st=_run), (), SFC, R),
    "idle": (levels(100, 35) + unit_readings(GEN, st=lambda i: "RUNNING" if i < 25 else "STOPPED"), (), SFC, R),
    "delivery": (levels(300, 700) + unit_readings(GEN, kw=lambda i: "6" if i < 40 else "0",
                                                   st=lambda i: "RUNNING" if i < 40 else "STOPPED"),
                 (record("FUEL_DELIVERY", START + timedelta(hours=2), 400), record("TANK_DIP", START + SLOT, 300, 2)),
                 SFC, R),
    "no_sfc": (levels(500, 460) + unit_readings(GEN, kw=lambda i: "10" if i < 60 else "0", st=_run), (), None, R),
}


def _plain(value):
    if isinstance(value, Fraction):
        return vr.fmt(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return value


def serialise(result: rules.WindowResult, digest: str) -> dict:
    return {"result": _plain(asdict(result)), "digest": digest}


def one_unit(name: str) -> dict:
    readings, records, sfc, no_load = ONE_UNIT_CASES[name]
    units = (rules.GeneratorUnit(GEN, sfc, no_load),)
    result = rules.assess(start=START, end=END, tank_asset_id=TANK, units=units, readings=readings,
                          records=list(records), accuracy=A)
    digest = rules.input_sha256(night_date=NIGHT, start=START, end=END, tank_asset_id=TANK, units=units, accuracy=A,
                                evidence_ids=sorted(r.id for r in readings), records=records)
    return serialise(result, digest)


@pytest.mark.parametrize("name", sorted(ONE_UNIT_CASES))
def test_f1_one_unit_result_and_digest_equal_main(name: str) -> None:
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert golden["captured_on"] == "23d2cd9f6"
    assert json.dumps(one_unit(name), sort_keys=True) == json.dumps(golden["cases"][name], sort_keys=True)
    assert "units" not in one_unit(name)["result"]["terms"]


# --- two units -------------------------------------------------------------------------------------------------


def two_units(gen=lambda i: "10" if i < 24 else "0", gen2=lambda i: "20" if i < 12 else "0", sfc2=SFC2, r2=R2,
              st=lambda i: "RUNNING" if i < 24 else "STOPPED", st2=lambda i: "RUNNING" if i < 12 else "STOPPED",
              skip2: int | None = None, opening=500, closing=480):
    readings = (levels(opening, closing) + unit_readings(GEN, kw=gen, st=st)
                + unit_readings(GEN2, kw=gen2, st=st2, skip_power=skip2)
                + unit_readings(OTHER, kw=lambda i: "50", st=lambda i: "RUNNING"))
    units = (rules.GeneratorUnit(GEN, SFC, R), rules.GeneratorUnit(GEN2, sfc2, r2))
    return rules.assess(start=START, end=END, tank_asset_id=TANK, units=units, readings=readings, records=[],
                        accuracy=A), units, readings


def test_f2_two_units_burn_each_on_its_own_sfc() -> None:
    out, _, _ = two_units()
    # gen-1: 24 slots x 10 kW x 5 min = 20 kWh at 0.355; gen-2: 12 x 20 kW x 5 min = 20 kWh at 0.3 -> 7.1 + 6 = 13.1 L
    assert Fraction(out.terms["generator_kwh"]) == 40
    assert Fraction(out.terms["loaded_litres"]) == Fraction(131, 10)
    assert Fraction(out.terms["use_low"]) == Fraction(9, 10) * Fraction(131, 10)
    assert [u["asset_id"] for u in out.terms["units"]] == [GEN, GEN2]
    by_unit = {u["asset_id"]: u for u in out.terms["units"]}
    assert Fraction(by_unit[GEN]["loaded_litres"]) == Fraction(71, 10)
    assert Fraction(by_unit[GEN2]["loaded_litres"]) == 6
    assert by_unit[GEN2]["sfc_l_per_kwh"] == "0.3" and by_unit[GEN2]["sfc_revision_id"] == "rev-s2"
    assert out.state != "NOT_ASSESSED" and out.reason is None


def test_f3_two_units_idle_each_on_its_own_no_load_rate() -> None:
    out, _, _ = two_units(gen=lambda i: "0", gen2=lambda i: "0", opening=100, closing=90)
    # gen-1 idles 23 slots (the stop slot is not idle), gen-2 idles 11: 6900 s at 4.9 L/h and 3300 s at 3 L/h
    idle_litres = Fraction(6900, 3600) * Fraction(49, 10) + Fraction(3300, 3600) * 3
    assert Fraction(out.terms["use_high"]) == Fraction(11, 10) * idle_litres
    assert out.terms["idle_seconds"] == 6900 + 3300


def test_f4_a_unit_without_sfc_gives_sfc_missing() -> None:
    out, _, _ = two_units(sfc2=None)
    assert (out.state, out.reason) == ("NOT_ASSESSED", "SFC_MISSING")
    out, _, _ = two_units(r2=None)
    assert (out.state, out.reason) == ("NOT_ASSESSED", "NO_LOAD_RATE_MISSING")


def test_f5_a_unit_with_unknown_kwh_gives_kwh_unknown() -> None:
    out, _, _ = two_units(skip2=3)
    assert (out.state, out.reason) == ("NOT_ASSESSED", "GENERATOR_KWH_UNKNOWN")
    assert out.terms["unknown_slots"] == 1


def test_f6_relevant_readings_take_every_unit() -> None:
    _, _, readings = two_units()
    kept = rules.relevant_readings(readings, TANK, (GEN, GEN2))
    assert {r.asset_id for r in kept} == {TANK, GEN, GEN2}
    assert {r.asset_id for r in rules.relevant_readings(readings, TANK, GEN)} == {TANK, GEN}


def _digest(units, ids=("e1",)):
    return rules.input_sha256(night_date=NIGHT, start=START, end=END, tank_asset_id=TANK, units=units, accuracy=A,
                              evidence_ids=ids, records=())


def test_f7_two_unit_digest_covers_every_unit() -> None:
    _, units, _ = two_units()
    base = _digest(units)
    assert base != _digest(units[:1])
    assert base != _digest((units[0], rules.GeneratorUnit(GEN2, SFC, R2)))
    assert base != _digest((units[0], rules.GeneratorUnit(GEN2, SFC2, R)))
    assert base != _digest((units[1], units[0]))


# --- the service: lead unit in the column, every unit read ------------------------------------------------------


class _Tx:
    """A fake store transaction: two GENERATOR units whose asset codes sort opposite to their declared order."""

    def __init__(self, generators: int = 2, tanks: int = 1) -> None:
        self.known_at = END + timedelta(hours=1)
        self.appended: dict | None = None
        assets = [SimpleNamespace(id=TANK, asset_code="T-1", asset_type="FUEL_TANK")] * tanks
        gens = [SimpleNamespace(id=GEN, asset_code="Z-GEN-LEAD", asset_type="GENERATOR"),
                SimpleNamespace(id=GEN2, asset_code="A-GEN-SECOND", asset_type="GENERATOR")][:generators]
        self._assets = assets + sorted(gens, key=lambda g: g.asset_code)  # the adapter orders by asset_code
        self._order = [g.asset_code for g in gens]
        self._sfc = {GEN: Fraction(355, 1000), GEN2: Fraction(3, 10)}
        self._readings, _, _ = None, None, None
        _, _, self._readings = two_units()

    def active_assets(self):
        return self._assets

    def component_order(self, lo, hi):
        return list(self._order)

    def timezone(self):
        return "UTC"

    def lock(self, *_):
        pass

    def latest(self, *_):
        return None

    def fuel_records(self, *_):
        return ()

    def properties(self, asset_code, keys, lo, hi):
        values = {k: [] for k in keys}
        if "fuel-level-sensor-accuracy" in values:
            values["fuel-level-sensor-accuracy"] = [(10, "L")]
            values["fuel-level-sensor-accuracy-basis"] = [("GENERIC_DEFAULT", "state")]
        if "generator-no-load-fuel-rate-basis" in values:
            values["generator-no-load-fuel-rate-basis"] = [("GENERIC_DEFAULT", "state")]
        return [SimpleNamespace(revision_id="rev-f", valid_from=SINCE, valid_to=None, values=values)]

    def sfc_history(self, gen_id, lo, hi):
        return [SimpleNamespace(value_l_per_kwh=self._sfc[gen_id], property_revision_id=f"sfc-{gen_id}",
                                valid_from=SINCE, valid_to=None)]

    def no_load_history(self, gen_id, lo, hi):
        return [SimpleNamespace(value_l_per_h=Fraction(49, 10), foundation_revision_id="rev-f", valid_from=SINCE,
                                valid_to=None)]

    def readings(self, lo, hi, roles):
        return list(self._readings)

    def append(self, latest, row):
        self.appended = row
        return row


def test_f8_service_keys_the_window_on_the_lead_unit_and_reads_every_unit() -> None:
    from assetops_backend.fuel_balance.service import FuelBalanceService

    tx = _Tx()
    result = FuelBalanceService._assess(tx, NIGHT)
    row = tx.appended
    assert result.created is True
    assert row["generator_asset_id"] == GEN  # declared first, though its asset code sorts last
    assert [u["asset_id"] for u in row["terms"]["units"]] == [GEN, GEN2]
    assert Fraction(row["terms"]["loaded_litres"]) == Fraction(131, 10)
    assert {e for e in row["evidence_ids"] if e.startswith(("pow-", "st-"))} == {
        r.id for r in tx._readings if r.asset_id in (GEN, GEN2)}


@pytest.mark.parametrize("generators,tanks", [(0, 1), (1, 2), (2, 0)])
def test_f9_service_refuses_without_one_tank_and_a_generator(generators: int, tanks: int) -> None:
    from assetops_backend.fuel_balance.service import FuelBalanceService

    with pytest.raises(FuelBalanceRefused) as err:
        FuelBalanceService._assess(_Tx(generators=generators, tanks=tanks), NIGHT)
    assert err.value.args[0] == ASSETS_UNSUPPORTED
