"""DD3d-a (D-DD.153): the unexplained-fuel tolerance is max(relative x consumption, 2a), a the tank's declared level
accuracy. Pure; no database. Figures are literals from D-DD.153's table, never read from the rule (W2).

The `fuel_balance` night code, the night text, the verification rules and `structure/litres/` carry no edit.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace

import pytest

from assetops_backend.chain.ports import SiteRef
from assetops_backend.commercial.months import month_bounds
from assetops_backend.fuel_balance.adapters.postgres_fuel_balance_store import AssetRow, PropertyRevision
from assetops_backend.structure.evaluate import LeafValue, SiteStructure, evaluate
from assetops_backend.structure.observe import observe as obs
from assetops_backend.structure.observe import rules
from assetops_backend.structure.observe.floor import StoreFloorRead
from assetops_backend.structure.observe.service import StructureObserver
from assetops_backend.structure.registry import REGISTRIES
from assetops_backend.structure.targets.read import SiteTargets
from assetops_backend.structure_snapshot.model import SiteMonthSnapshot
from test_3b4_observer import _missing, _pack

D = Decimal
MG = REGISTRIES["MINI_GRID"]
UTC = timezone.utc
LAKESIDE = Path(__file__).resolve().parent / "fixtures" / "on1" / "lakeside-power.onboarding.json"
T, S = uuid.UUID(int=1), uuid.UUID(int=2)
KNOWN = datetime(2026, 11, 6, tzinfo=UTC)


def floor(a: str) -> obs.Floor:
    return obs.Floor(D(2) * D(a), D(a), "GENERIC_DEFAULT", f"rev-{a}")


def side(name: str, which: str, values: dict, *, drop: tuple[str, ...] = (), month: str = "2026-10") -> SiteStructure:
    nodes = _pack(name)["actual" if which == "actual" else "plan"]["nodes"]
    leaves = {}
    for row in MG.rows:
        if not row.is_leaf:
            continue
        cur = "USD" if rules.money_dimension(row.unit) else None
        if row.factor_id in drop:
            leaves[row.factor_id] = LeafValue(None, "NOT_AVAILABLE", (), None, _missing(), None)
        else:
            figure = values.get(row.factor_id, nodes[row.factor_id])
            leaves[row.factor_id] = LeafValue(D(str(figure)), "RECORDED", ("pack",), None, None, cur,
                                              ("source-emulated",))
    return SiteStructure(f"{name.upper()}-001", month, "MINI_GRID", MG.version, evaluate(MG, leaves))


def litres(total: str, unexplained: str) -> dict:
    """The three fuel leaves whose sum is the consumption `total`."""
    return {"necessary_l": D(total) - D(unexplained), "candidate_l": D(0), "unexplained_l": D(unexplained)}


def pair(total: str, unexplained: str, *, name: str = "Kobo", target: str = "0", month: str = "2026-10",
         drop_actual=(), drop_target=()):
    return (side(name, "actual", litres(total, unexplained), drop=drop_actual, month=month),
            side(name, "plan", {"unexplained_l": D(target)}, drop=drop_target, month=month))


def one(sides, floors=None, declarations=None, leaf="unexplained_l") -> obs.FactorObservation:
    kwargs = {} if floors is None else {"floors": floors}
    return {o.factor_id: o for o in obs.observe(*sides, declarations or {}, **kwargs)}[leaf]


def strings(o: obs.FactorObservation) -> tuple[str, str]:
    claim = obs.claim(o, structure_key="MINI_GRID", structure_version=MG.version, month="2026-10",
                      snapshot_id=uuid.UUID(int=3), snapshot_as_of=KNOWN, tolerance_known_at=KNOWN)
    return obs.basis(o, "MINI_GRID", "2026-10"), json.dumps(claim)


def site_tolerance(pct: str) -> dict:
    return {"unexplained_l": obs.ToleranceInForce("SITE", "diesel_l", D(pct), uuid.UUID(int=7))}


def test_only_unexplained_litres_has_an_absolute_floor() -> None:
    assert dict(rules.FLOORED) == {"MINI_GRID": ("unexplained_l",)}
    for key, leaves in rules.FLOORED.items():
        assert set(leaves) <= set(rules.OBSERVED[key])


# --- P1: the relative band dominates, and the tie ---------------------------------------------------------------------

@pytest.mark.parametrize(("total", "unexplained", "state"), [
    ("3000", "40", "INSIDE_TOLERANCE"), ("3000", "70", "RAISED"),          # rel 60 > 50
    ("2500", "50", "INSIDE_TOLERANCE"), ("2500", "50.01", "RAISED")])      # the tie: rel 50 = floor 50, no bind
def test_p1_relative_dominates_is_byte_identical(total, unexplained, state) -> None:
    sides = pair(total, unexplained)
    with_floor, without = one(sides, {"unexplained_l": floor("25")}), one(sides, {})
    assert with_floor.state == state and with_floor.floor is None
    assert with_floor.band == D(total) / 50
    assert with_floor == without == one(sides)
    assert strings(with_floor) == strings(without)
    assert '"floor"' not in strings(with_floor)[1]


# --- P2: no adverse gap, or no band -----------------------------------------------------------------------------------

@pytest.mark.parametrize(("sides", "state"), [
    (pair("634.22", "0"), "NO_GAP"), (pair("634.22", "5", target="9"), "FAVOURABLE"),
    (pair("634.22", "12", drop_actual=("unexplained_l",)), "ACTUAL_NOT_AVAILABLE"),
    (pair("634.22", "12", drop_target=("unexplained_l",)), "TARGET_NOT_AVAILABLE"),
    (pair("634.22", "12", drop_actual=("necessary_l",)), "TOLERANCE_NOT_AVAILABLE")])
def test_p2_no_band_is_byte_identical(sides, state) -> None:
    with_floor, without = one(sides, {"unexplained_l": floor("25")}), one(sides, {})
    assert with_floor.state == state and with_floor.band is None and with_floor.floor is None
    assert with_floor == without
    assert strings(with_floor) == strings(without)


# --- P3: a leaf not in FLOORED ----------------------------------------------------------------------------------------

def test_p3_a_floor_for_another_leaf_is_filtered() -> None:
    sides = (side("Kobo", "actual", {}), side("Kobo", "plan", {}))
    declared = {leaf: obs.ToleranceInForce("SITE", "diesel_l", D(0), uuid.UUID(int=7))
                for leaf in rules.OBSERVED["MINI_GRID"]}
    floors = {leaf: floor("500") for leaf in rules.OBSERVED["MINI_GRID"] if leaf != "unexplained_l"}
    with_floors, without = obs.observe(*sides, declared, floors=floors), obs.observe(*sides, declared)
    assert with_floors == without
    assert [strings(o) for o in with_floors] == [strings(o) for o in without]
    # non-vacuous: a floor of 1,000 on these leaves, all with a declared tolerance, would have moved them
    assert {o.factor_id for o in without if o.state == "RAISED"} >= {"candidate_l", "adjustments_kwh", "outstanding"}


# --- the binding cases (D-DD.153's table) -----------------------------------------------------------------------------

@pytest.mark.parametrize(("name", "total", "unexplained", "a", "state", "rel", "band", "before"), [
    ("Kobo", "12", "12", "25", "INSIDE_TOLERANCE", "0.24", "50", "RAISED"),          # July, August
    ("Kobo", "634.22", "120", "25", "RAISED", "12.6844", "50", "RAISED"),            # October
    ("Kisiwa", "707.02", "18", "50", "INSIDE_TOLERANCE", "14.1404", "100", "RAISED")])  # September
def test_the_floor_binds(name, total, unexplained, a, state, rel, band, before) -> None:
    sides = pair(total, unexplained, name=name)
    o, without = one(sides, {"unexplained_l": floor(a)}), one(sides, {})
    assert (without.state, without.band, without.floor) == (before, D(rel), None)
    assert (o.state, o.band) == (state, D(band))
    assert o.floor == floor(a)
    (basis, claim_text), (plain_basis, plain_claim) = strings(o), strings(without)
    assert basis != plain_basis
    claim = json.loads(claim_text)
    assert claim["floor"] == {"litres": band, "accuracy_l": a, "basis": "GENERIC_DEFAULT", "revision_id": f"rev-{a}"}
    assert "floor" not in json.loads(plain_claim)


def test_the_basis_carries_the_floor_without_its_revision() -> None:
    sides = pair("12", "12")
    a, b = floor("25"), obs.Floor(D(50), D(25), "GENERIC_DEFAULT", "another revision, same figures")
    c = obs.Floor(D(50), D(25), "SITE_CALIBRATION", "rev-25")
    first, second, third = (strings(one(sides, {"unexplained_l": f}))[0] for f in (a, b, c))
    assert first == second != third


def test_equal_to_the_floor_is_inside() -> None:
    assert one(pair("634.22", "50"), {"unexplained_l": floor("25")}).state == "INSIDE_TOLERANCE"
    assert one(pair("634.22", "50.01"), {"unexplained_l": floor("25")}).state == "RAISED"


def test_a_declared_zero_percent_keeps_the_floor() -> None:
    o = one(pair("634.22", "20"), {"unexplained_l": floor("25")}, site_tolerance("0"))
    assert (o.state, o.band, o.floor) == ("INSIDE_TOLERANCE", D(50), floor("25"))


def test_no_declared_tolerance_takes_no_floor() -> None:
    """`source == "NONE"` keeps the band 0: the floor widens a tolerance, it never makes one."""
    row = MG.row("unexplained_l")
    assert row.tolerance is not None
    actual, target = pair("634.22", "20")
    bare = SimpleNamespace(row=lambda leaf: SimpleNamespace(tolerance=None, unit=row.unit, home=row.home))
    real_kind = rules.kind_of
    try:
        rules.kind_of = lambda registry, key, leaf: "BOTTOM_LINE"
        o = obs._one(bare, "MINI_GRID", "unexplained_l", rules.UP, actual, target, None, floor("25"))
    finally:
        rules.kind_of = real_kind
    assert (o.state, o.band, o.floor) == ("RAISED", D(0), None)


# --- the port: the accuracy in force -----------------------------------------------------------------------------------

START = datetime(2026, 1, 1, tzinfo=UTC)
WINDOW = month_bounds("2026-07", "Africa/Nairobi")


def revision(a, *, basis="GENERIC_DEFAULT", unit="L", rid="r1", lo=START, hi=None) -> PropertyRevision:
    return PropertyRevision(rid, lo, hi, {"fuel-level-sensor-accuracy": [] if a is None else [(a, unit)],
                                          "fuel-level-sensor-accuracy-basis": [] if basis is None
                                          else [(basis, "state")]})


class FakeFuel:
    """`FuelReadPort`: one transaction over the given tanks and property revisions."""

    def __init__(self, revisions, tanks: int = 1) -> None:
        self.revisions, self.calls = revisions, []
        self.assets = [AssetRow(f"g{i}", f"generator-{i}", "GENERATOR") for i in range(2)]
        self.assets += [AssetRow(f"t{i}", f"fuel-tank-{i}", "FUEL_TANK") for i in range(tanks)]

    def read_at(self, tenant_id, site_id, known_at, work):
        self.calls.append((tenant_id, site_id, known_at))
        return work(self)

    def active_assets(self):
        return self.assets

    def properties(self, asset_code, keys, lo, hi):
        assert asset_code == "fuel-tank-0" and (lo, hi) == WINDOW
        assert keys == ("fuel-level-sensor-accuracy", "fuel-level-sensor-accuracy-basis")
        return self.revisions


def read(revisions, tanks: int = 1):
    return StoreFloorRead(FakeFuel(revisions, tanks)).read(T, S, WINDOW, KNOWN)


def test_the_floor_is_twice_the_declared_accuracy() -> None:
    fuel = FakeFuel([revision(25)])
    assert StoreFloorRead(fuel).read(T, S, WINDOW, KNOWN) == obs.Floor(D(50), D(25), "GENERIC_DEFAULT", "r1")
    assert fuel.calls == [(T, S, KNOWN)]
    got = read([revision(0.35)])
    assert (got.litres, got.accuracy_l) == (D("0.7"), D("0.35"))
    assert isinstance(got.litres, Decimal) and Fraction(got.litres) == Fraction(7, 10)


@pytest.mark.parametrize(("revisions", "tanks"), [
    ([], 1), ([revision(None)], 1), ([revision(25, unit="%")], 1), ([revision(25, basis=None)], 1),
    ([revision(25, basis="GUESS")], 1), ([revision(0)], 1),
    ([revision(25)], 0), ([revision(25)], 2),                                         # not exactly one tank
    ([revision(25, lo=datetime(2026, 7, 15, tzinfo=UTC))], 1),                        # starts mid-month
    ([revision(25, hi=datetime(2026, 7, 15, tzinfo=UTC)), revision(30, rid="r2", lo=datetime(2026, 7, 15, tzinfo=UTC))],
     1)])
def test_no_single_accuracy_over_the_month_is_no_floor(revisions, tanks) -> None:
    assert read(revisions, tanks) is None


# --- the service: the floor reaches the observation --------------------------------------------------------------------

class Stores:
    """Every store the observer touches; `structure_apply` records what it was given."""

    def __init__(self) -> None:
        self.applied: dict[str, tuple] = {}

    def tolerances(self, tenant_id, site_id):
        return ()

    def get(self, tenant_id, ids):
        return (SimpleNamespace(payload_sha256="0" * 64),)

    def transaction(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def structure_lock(self, c, site_id, month):
        pass

    def structure_apply(self, c, tenant_id, site_id, key, month, window, o, *, basis, claim, **kwargs):
        self.applied[o.factor_id] = (o, claim)
        return None


def run(floors) -> tuple[obs.FactorObservation, dict, dict]:
    month = "2026-07"
    actual, target = pair("12", "12", month=month)
    ref = SiteRef(T, S, "KOBO-001", "MINIGRID", "Africa/Nairobi")
    site = SiteMonthSnapshot(uuid.UUID(int=4), T, ref, month, KNOWN, "service:test", True, (), None, actual,
                             SiteTargets(target, None, (), "USD"))
    stores = Stores()
    args = () if floors is ... else (floors,)
    observer = StructureObserver(None, stores, stores, stores, lambda: KNOWN, *args)
    result = observer._site(T, month, site, KNOWN)
    o, claim = stores.applied["unexplained_l"]
    return o, claim, dict(result.states)


def test_kobo_july_is_inside_tolerance_through_the_service() -> None:
    o, claim, states = run(StoreFloorRead(FakeFuel([revision(25)])))
    assert (o.state, o.band, states["unexplained_l"]) == ("INSIDE_TOLERANCE", D(50), "INSIDE_TOLERANCE")
    assert claim["floor"] == {"litres": "50", "accuracy_l": "25", "basis": "GENERIC_DEFAULT", "revision_id": "r1"}


@pytest.mark.parametrize("floors", [
    ..., SimpleNamespace(read=lambda *a: None),                                       # the negative control
    StoreFloorRead(FakeFuel([revision(25)], tanks=2)),
    StoreFloorRead(FakeFuel([revision(25, lo=datetime(2026, 7, 15, tzinfo=UTC))]))])
def test_without_a_floor_kobo_july_is_raised_on_the_relative_band(floors) -> None:
    o, claim, states = run(floors)
    assert (o.state, o.band, o.floor, states["unexplained_l"]) == ("RAISED", D("0.24"), None, "RAISED")
    assert "floor" not in claim


# --- the declarations ---------------------------------------------------------------------------------------------------

@pytest.mark.parametrize(("code", "capacity", "a"), [("KOBO-001", 2500, 25), ("KISIWA-001", 5000, 50),
                                                     ("MTO-001", 1000, 10)])
def test_each_mini_grid_tank_declares_one_percent_of_its_capacity(code, capacity, a) -> None:
    document = json.loads(LAKESIDE.read_text(encoding="utf-8"))
    [site] = [s for s in document["sites"] if s["code"] == code]
    [tank] = [c for c in site["components"] if c["type"] == "FUEL_TANK"]
    assert tank["id"] == "fuel-tank"
    assert [(p["property_key"], p["value"], p["unit"], p["source"], p["source_version"]) for p in tank["properties"]] \
        == [("tank-capacity", capacity, "L", "SITE", 1), ("fuel-level-sensor-accuracy", a, "L", "SITE", 1),
            ("fuel-level-sensor-accuracy-basis", "GENERIC_DEFAULT", "state", "SITE", 1)]
