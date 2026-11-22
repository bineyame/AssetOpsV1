"""DD3c part 4 (D-DD.113): the litres split per GENERATOR unit. Each unit runs on its own curve over its own use; the
Site's litres are the sum; one tank. One unit: Kobo's October month is byte-equal to main
(`test_dd3c_kobo_one_unit_golden.py`). Expected values are hand-computed: unit B runs 20 kW (5/3 kWh a slot) in
every slot of Kobo's eleven 07:00-13:00 CANDIDATE spans (72 slots a day) at 1/2 L/kWh: 11 x 72 x 5/3 x 1/2 = 660 L.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime, timedelta
from decimal import Decimal
from fractions import Fraction
from types import SimpleNamespace
from uuid import UUID

import test_4d_litre_split as d4

from assetops_backend.structure.litres import rules
from assetops_backend.structure.litres.rules import FuelCurve, UnitFuel, month_litres

SFC2 = "foundation:sfc-2"
B_LITRES = Decimal(660)


def unit_b(curve: FuelCurve | None = None, idle: set | None = None) -> UnitFuel:
    w = d4.World([], d4.slots_of([s for s in d4.kobo_spans() if s.claim == d4.CAND]), idle=idle or set())
    return UnitFuel("gen-b", w.use, curve or FuelCurve(Fraction(1, 2), SFC2, Fraction(2), "foundation:nl-2",
                                                       (datetime(2026, 1, 1, tzinfo=d4.UTC), None)))


def two_units(**kw):
    a = d4.kobo()
    one = a.inputs()
    return dataclasses.replace(one, units=(*one.units, unit_b(**kw)))


def value(month, leaf):
    return month.values[leaf].value


def test_l1_two_units_burn_each_on_its_own_curve_summed() -> None:
    one, two = d4.run(d4.kobo()), month_litres(two_units(), d4.FB)
    assert value(two, "necessary_l") == value(one, "necessary_l")
    assert value(two, "candidate_l") == value(one, "candidate_l") + B_LITRES
    assert value(two, "unexplained_l") == value(one, "unexplained_l") - B_LITRES
    assert two.modelled_window_l == one.modelled_window_l + B_LITRES
    assert SFC2 in two.values["candidate_l"].sources
    assert two.values["candidate_l"].sources.index(d4.SFC) < two.values["candidate_l"].sources.index(SFC2)


def test_l2_a_unit_without_a_curve_gives_fuel_curve_missing() -> None:
    month = month_litres(two_units(curve=FuelCurve(None, None, None, None, None)), d4.FB)
    assert {v.missing.note for v in month.values.values()} == {rules.FUEL_CURVE_MISSING}


def test_l3_the_curve_window_is_the_units_intersection() -> None:
    late = FuelCurve(Fraction(1, 2), SFC2, Fraction(2), "foundation:nl-2", (datetime(2026, 10, 15, tzinfo=d4.UTC), None))
    month = month_litres(two_units(curve=late), d4.FB)
    assert month.values["unexplained_l"].missing.note == rules.FUEL_CURVE_MISSING


def test_l4_a_units_idle_without_its_rate_gives_no_load_rate_missing() -> None:
    idle = {d4.local(2026, 10, 3, 6, 0).astimezone(d4.UTC)}
    curve = FuelCurve(Fraction(1, 2), SFC2, None, None, (datetime(2026, 1, 1, tzinfo=d4.UTC), None))
    month = month_litres(two_units(curve=curve, idle=idle), d4.FB)
    assert {v.missing.note for v in month.values.values()} == {rules.NO_LOAD_RATE_MISSING}


# ------------------------------------------------------------------------------ inputs: one tank, every unit


class Tx:
    def __init__(self, generators: int, tanks: int) -> None:
        self.assets = [SimpleNamespace(id=UUID(int=10 + i), asset_type="GENERATOR", asset_code=f"GEN-{i}")
                       for i in range(generators)]
        self.assets += [SimpleNamespace(id=UUID(int=20 + i), asset_type="FUEL_TANK", asset_code=f"TANK-{i}")
                        for i in range(tanks)]
        self.sfc_reads: list = []
        self.reading_ids: list = []

    def active_assets(self):
        return self.assets

    def sfc_history(self, gen_id, lo, hi):
        from assetops_backend.mini_depth.rules import SfcValue
        self.sfc_reads.append(gen_id)
        return [SfcValue(UUID(int=100 + gen_id.int), Decimal("0.3") + Decimal(gen_id.int - 10) / 10,
                         lo - timedelta(days=60), None)]

    def no_load_history(self, gen_id, lo, hi):
        return []

    def fuel_records(self, tank_id, lo, hi):
        return []

    def readings(self, lo, hi, roles):
        return []


def read(tx: Tx):
    from assetops_backend.chain.ports import SiteRef
    from assetops_backend.structure.litres.inputs import StoreLitreInputs
    fuel = SimpleNamespace(read_at=lambda t, s, k, work: work(tx))
    spans = SimpleNamespace(dispatch_spans=lambda *a: ())
    site = SiteRef(UUID(int=1), UUID(int=2), "KISIWA-001", "MINIGRID", "Africa/Dar_es_Salaam")
    return StoreLitreInputs(fuel, spans).read(site, "2026-10", d4.KNOWN_AT)


def test_l5_two_generators_and_one_tank_is_one_each_with_every_unit_on_its_own_curve() -> None:
    tx = Tx(2, 1)
    inp = read(tx)
    assert inp.assets == rules.ONE_EACH
    assert [u.unit for u in inp.units] == [str(UUID(int=10)), str(UUID(int=11))]
    assert [u.curve.sfc for u in inp.units] == [Fraction(3, 10), Fraction(2, 5)]
    assert tx.sfc_reads == [UUID(int=10), UUID(int=11)]


def test_l6_two_tanks_stay_not_one_each() -> None:
    assert read(Tx(2, 2)).assets == rules.NOT_ONE_EACH
    assert read(Tx(0, 1)).assets == rules.NOT_ONE_EACH
