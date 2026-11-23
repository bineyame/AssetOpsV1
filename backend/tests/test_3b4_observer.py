"""3B4 (spec §7 tests 1 to 9; tests 1, 1b and 3 landed with the `check.py` commit after 4a and 3B6, D-3B4.25).

No database. Expected tables and figures are literals from the pack (`derived-values.json`) and spec §2.1 and §6,
never read from `OBSERVED`, `signs` or `observe` (W2).
"""
from __future__ import annotations

import dataclasses
import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

import test_5b_attribution as t5b
from assetops_backend.chain.ports import SiteRef
from assetops_backend.structure.attribution.site import site_bridge
from assetops_backend.structure.check import OBSERVE_CODES, StructureError, check_all, check_observed, check_pins
from assetops_backend.structure.evaluate import LeafValue, Missing, SiteStructure, evaluate
from assetops_backend.structure.observe import observe as obs
from assetops_backend.structure.observe import rules
from assetops_backend.structure.read import evaluate_inputs
from assetops_backend.structure.registry import REGISTRIES
from assetops_backend.structure_snapshot.model import SiteMonthSnapshot

D = Decimal
MG = REGISTRIES["MINI_GRID"]
OCT = "2026-10"
PACK = Path(__file__).resolve().parents[2] / "Docs" / "demo-sprint" / "product-direction-layer4" / "derived-values.json"

#: Spec §2.1, written out (W2): the 19 observed leaves in registry leaf order, and the 12 not observed.
OBSERVED_LITERAL = (
    ("delivered_kwh", "DOWN"), ("unexplained_loss_kwh", "UP"), ("adjustments_kwh", "UP"), ("unmapped_kwh", "UP"),
    ("tariff", "DOWN"), ("productive_kwh", "DOWN"), ("productive_tariff", "DOWN"), ("in_transit", "UP"),
    ("outstanding", "UP"), ("necessary_l", "UP"), ("candidate_l", "UP"), ("unexplained_l", "UP"),
    ("diesel_price", "UP"), ("om", "UP"), ("staff", "UP"), ("reduced_days", "UP"), ("unserved_critical_kwh", "UP"),
    ("customer_hours_interrupted", "UP"), ("dawn_days_below", "UP"))

#: Test 2: the sign each leaf enters the bridge roots with (contribution, collected), worked by hand.
SIGNS_LITERAL = {
    "delivered_kwh": {1}, "unexplained_loss_kwh": {-1}, "adjustments_kwh": {-1}, "unmapped_kwh": {-1},
    "tariff": {1}, "productive_kwh": {1}, "productive_tariff": {1}, "in_transit": {-1}, "outstanding": {-1},
    "necessary_l": {-1}, "candidate_l": {-1}, "unexplained_l": {-1}, "diesel_price": {-1}, "om": {-1},
    "staff": {-1}, "technical_loss_kwh": {-1}, "extra_l": {-1}, "battery_throughput_kwh": {-1}, "wear_rate": {-1},
    "collection_cost": {-1}}


# --- F1: the pack sides ----------------------------------------------------------------------------------------------

def _pack(name: str) -> dict:
    return json.loads(PACK.read_text(encoding="utf-8"))["sites"][f"lakeside-power/{name}"]


def _missing() -> Missing:
    return Missing("TEST", "COMMERCIAL_RECORD", "NOT_RECEIVED", None, (), None, None)


def _side(name: str, side: str, *, drop: tuple[str, ...] = (), currency: dict | None = None) -> SiteStructure:
    nodes = _pack(name)["actual" if side == "actual" else "plan"]["nodes"]
    evidence, source = ("RECORDED", "pack:actual") if side == "actual" else ("DECLARED", "pack:plan")
    leaves = {}
    for row in MG.rows:
        if not row.is_leaf:
            continue
        cur = (currency or {}).get(row.factor_id, "USD") if rules.money_dimension(row.unit) else None
        if row.factor_id in drop:
            leaves[row.factor_id] = LeafValue(None, "NOT_AVAILABLE", (), None, _missing(), None)
        else:
            leaves[row.factor_id] = LeafValue(D(str(nodes[row.factor_id])), evidence, (source,), None, None, cur, ("source-emulated",))
    return SiteStructure(f"{name.upper()}-001", OCT, "MINI_GRID", MG.version, evaluate(MG, leaves))


def _observe(name: str, declarations: dict | None = None, *, drop_actual=(), drop_target=(), currency=None):
    return {o.factor_id: o for o in obs.observe(_side(name, "actual", drop=drop_actual),
                                                _side(name, "plan", drop=drop_target, currency=currency),
                                                declarations or {})}


# Spec §6 F1, written in the test: leaf -> (state, gap, kind); every other observed leaf is NO_GAP.
F1 = {
    "Kobo": {"adjustments_kwh": ("RAISED", "45", "BOTTOM_LINE"), "outstanding": ("RAISED", "278", "CASH"),
             "necessary_l": ("FAVOURABLE", "-211", "BOTTOM_LINE"), "candidate_l": ("RAISED", "25", "BOTTOM_LINE"),
             "unexplained_l": ("RAISED", "120", "BOTTOM_LINE"), "delivered_kwh": ("FAVOURABLE", "550", "BOTTOM_LINE")},
    "Kisiwa": {"adjustments_kwh": ("RAISED", "30", "BOTTOM_LINE"), "outstanding": ("RAISED", "270", "CASH"),
               "necessary_l": ("FAVOURABLE", "-1486", "BOTTOM_LINE"), "reduced_days": ("RAISED", "2", "PROTECT"),
               "delivered_kwh": ("FAVOURABLE", "450", "BOTTOM_LINE"),
               "candidate_l": ("RAISED", "69", "BOTTOM_LINE"),  # D-DD.164 (2026-11-23): M rev 16.23, -1483/67 -> -1486/69
               "unexplained_l": ("RAISED", "20", "BOTTOM_LINE")},
    "Mto": {"unexplained_loss_kwh": ("RAISED", "120", "BOTTOM_LINE"), "adjustments_kwh": ("RAISED", "40", "BOTTOM_LINE"),
            "unmapped_kwh": ("RAISED", "140", "BOTTOM_LINE"), "necessary_l": ("FAVOURABLE", "-300", "BOTTOM_LINE"),
            "candidate_l": ("RAISED", "32", "BOTTOM_LINE"),
            "in_transit": ("RAISED", "150", "CASH"), "outstanding": ("RAISED", "120", "CASH"),
            "reduced_days": ("RAISED", "4", "PROTECT"), "delivered_kwh": ("FAVOURABLE", "400", "BOTTOM_LINE")},
}
#: Spec §4.3 (D-3B4.18): the claim's key set, a literal.
CLAIM_KEYS = {"format", "structure_key", "structure_version", "factor_id", "home", "objective", "kind", "month",
              "direction", "state", "unit", "currency", "actual", "target", "gap", "band", "tolerance",
              "actual_evidence", "target_evidence", "sources", "origins", "also_pinned", "snapshot_id",
              "snapshot_as_of", "tolerance_known_at"}
PROTECT_LEAVES = {"reduced_days", "unserved_critical_kwh", "customer_hours_interrupted", "dawn_days_below"}
CASH_LEAVES = {"in_transit", "outstanding"}


#: Spec §2.1, written out (W2): the 12 leaves not observed and why.
NOT_OBSERVED_LITERAL = {
    "technical_loss_kwh": "DECLARED_SOURCE", "wear_rate": "DECLARED_SOURCE", "major_assets": "DECLARED_SOURCE",
    "standby_kw": "DECLARED_SOURCE", "lost_unit_kw": "DECLARED_SOURCE", "extra_l": "OPTION_ONLY",
    "battery_throughput_kwh": "OPTION_ONLY", "collection_cost": "OPTION_ONLY", "period_days": "CALENDAR",
    "hours_per_day": "EXPOSURE_RATE", "field_visits": "NO_OWNER_RULE_KIND", "liability": "NO_OWNER_RULE_KIND"}


# --- test 1: the tables, and the start-up path ------------------------------------------------------------------------

def test_1_tables_are_the_spec_literals_and_check_all_passes() -> None:
    assert tuple(rules.OBSERVED["MINI_GRID"].items()) == OBSERVED_LITERAL
    assert dict(rules.NOT_OBSERVED["MINI_GRID"]) == NOT_OBSERVED_LITERAL
    assert set(rules.OBSERVED) == set(rules.NOT_OBSERVED) == {"MINI_GRID"}
    check_all()
    check_observed()


# --- test 1b: import order (D-3B4.20) ---------------------------------------------------------------------------------

@pytest.mark.parametrize("module", ["assetops_backend.structure.check", "assetops_backend.structure.observe.rules",
                                    "assetops_backend.structure.evaluate"])
def test_1b_each_module_imports_first_in_a_fresh_interpreter(module: str) -> None:
    import os
    paths = [p for p in sys.path if p]
    env = {**os.environ, "PYTHONPATH": os.pathsep.join(paths)}
    # -I ignores PYTHONPATH, so the path is set inside the interpreter before the one import under test.
    code = f"import sys; sys.path[:0] = {paths!r}; import {module}"
    done = subprocess.run([sys.executable, "-I", "-c", code], env=env, capture_output=True, text=True, timeout=120)
    assert done.returncode == 0, done.stderr[-2000:]


def test_1b_check_all_passes_with_registries_the_observer_does_not_name() -> None:
    assert set(REGISTRIES) - set(rules.OBSERVED)          # 3B6's COLD and EV keys (D-3B4.25)
    check_all()


# --- test 3: each check_observed code on its own planted table --------------------------------------------------------

def _tables() -> tuple[dict, dict]:
    return ({k: dict(v) for k, v in rules.OBSERVED.items()}, {k: dict(v) for k, v in rules.NOT_OBSERVED.items()})


def _plant_key():
    o, n = _tables()
    o["NO_SUCH_KEY"], n["NO_SUCH_KEY"] = {}, {}
    return o, n, "NO_SUCH_KEY", "-"


def _plant_cover_removed():
    o, n = _tables()
    del o["MINI_GRID"]["dawn_days_below"]
    return o, n, "MINI_GRID", "dawn_days_below"


def _plant_cover_no_row():
    o, n = _tables()
    n["MINI_GRID"]["no_such_leaf"] = "DECLARED_SOURCE"
    return o, n, "MINI_GRID", "no_such_leaf"


def _plant_leaf():
    o, n = _tables()
    o["MINI_GRID"]["billed_kwh"] = "DOWN"
    return o, n, "MINI_GRID", "billed_kwh"


def _plant_source():
    o, n = _tables()
    del n["MINI_GRID"]["technical_loss_kwh"]
    o["MINI_GRID"]["technical_loss_kwh"] = "UP"
    return o, n, "MINI_GRID", "technical_loss_kwh"


def _plant_direction():
    o, n = _tables()
    o["MINI_GRID"]["outstanding"] = "DOWN"
    return o, n, "MINI_GRID", "outstanding"


def _plant_kind():
    o, n = _tables()
    del n["MINI_GRID"]["field_visits"]
    o["MINI_GRID"]["field_visits"] = "UP"
    return o, n, "MINI_GRID", "field_visits"


@pytest.mark.parametrize(("plant", "code"), [
    (_plant_key, "STRUCTURE_OBSERVE_KEY"), (_plant_cover_removed, "STRUCTURE_OBSERVE_COVER"),
    (_plant_cover_no_row, "STRUCTURE_OBSERVE_COVER"), (_plant_leaf, "STRUCTURE_OBSERVE_LEAF"),
    (_plant_source, "STRUCTURE_OBSERVE_SOURCE"), (_plant_direction, "STRUCTURE_OBSERVE_DIRECTION"),
    (_plant_kind, "STRUCTURE_OBSERVE_KIND")])
def test_3_each_code_fires_on_its_plant_and_no_earlier_code(plant, code: str) -> None:
    o, n, key, leaf = plant()
    with pytest.raises(StructureError) as raised:
        check_observed(o, n)
    assert (raised.value.code, raised.value.structure_key, raised.value.factor_id) == (code, key, leaf)


def test_3_codes_are_the_spec_order() -> None:
    assert OBSERVE_CODES == ("STRUCTURE_OBSERVE_KEY", "STRUCTURE_OBSERVE_COVER", "STRUCTURE_OBSERVE_LEAF",
                             "STRUCTURE_OBSERVE_SOURCE", "STRUCTURE_OBSERVE_DIRECTION", "STRUCTURE_OBSERVE_KIND")
    check_observed()          # the real tables pass


# --- test 2: signs ---------------------------------------------------------------------------------------------------

def test_2_signs_agree_with_the_literal_map() -> None:
    got = rules.reached(MG, "MINI_GRID")
    assert {k: set(v) for k, v in got.items()} == SIGNS_LITERAL
    for leaf, direction in OBSERVED_LITERAL:
        if leaf in SIGNS_LITERAL:
            assert SIGNS_LITERAL[leaf] == ({-1} if direction == "UP" else {1}), leaf
    assert not (PROTECT_LEAVES | {"hours_per_day"}) & set(got)
    assert set(rules.signs(MG, "collected")) == {
        "delivered_kwh", "technical_loss_kwh", "unexplained_loss_kwh", "adjustments_kwh", "unmapped_kwh", "tariff",
        "productive_kwh", "productive_tariff", "in_transit", "outstanding"}


def test_2_observed_table_is_the_spec_literal() -> None:
    assert tuple(rules.OBSERVED["MINI_GRID"].items()) == OBSERVED_LITERAL


# --- test 4: F1 ------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("name", ["Kobo", "Kisiwa", "Mto"])
def test_4_pack_sides(name: str) -> None:
    got = _observe(name)
    assert tuple(got) == tuple(leaf for leaf, _ in OBSERVED_LITERAL)
    for leaf, o in got.items():
        state, gap, kind = F1[name].get(leaf, ("NO_GAP", "0", None))
        assert o.state == state, (leaf, o.state)
        assert o.gap == D(gap), (leaf, o.gap)
        if kind is not None:
            assert o.kind == kind, leaf
        expected_kind = ("PROTECT" if leaf in PROTECT_LEAVES else "CASH" if leaf in CASH_LEAVES else "BOTTOM_LINE")
        assert o.kind == expected_kind, leaf
        # the rule's two halves: RAISED is adverse by direction, FAVOURABLE never raised
        if o.state == "RAISED":
            assert (o.gap > 0) == (o.direction == "UP")
        if o.state == "FAVOURABLE":
            assert (o.gap < 0) == (o.direction == "UP")


def test_4_bands_are_two_percent_of_the_actual_diesel() -> None:
    kobo, kisiwa = _observe("Kobo")["unexplained_l"], _observe("Kisiwa")["unexplained_l"]
    assert kobo.band == D("12.68") and kobo.tolerance.source == "STRUCTURE"
    assert kisiwa.band == D("18.06") and kisiwa.state == "RAISED"  # 2 % of 903 L (D-DD.164, M rev 16.23)
    assert _observe("Kobo")["outstanding"].band == D(0)
    assert _observe("Kobo")["outstanding"].currency == "USD" and _observe("Kobo")["necessary_l"].currency is None


# --- test 5: tolerance -----------------------------------------------------------------------------------------------

def _site(of: str, pct: str) -> obs.ToleranceInForce:
    return obs.ToleranceInForce("SITE", of, D(pct), uuid.UUID(int=7))


def test_5_tolerance() -> None:
    o = _observe("Kobo", {"candidate_l": _site("diesel_l", "5")})["candidate_l"]
    assert (o.state, o.band, o.tolerance.source) == ("INSIDE_TOLERANCE", D("31.7"), "SITE")
    o = _observe("Kobo", {"candidate_l": _site("diesel_l", "2")})["candidate_l"]
    assert (o.state, o.band) == ("RAISED", D("12.68"))
    o = _observe("Kisiwa", {"unexplained_l": _site("unexplained_l", "100")})["unexplained_l"]
    assert (o.state, o.band, o.gap) == ("INSIDE_TOLERANCE", D("20"), D("20"))  # equal is inside (strict outside)
    o = _observe("Mto", {"unexplained_loss_kwh": _site("delivered_kwh", "1")},
                 drop_actual=("delivered_kwh",))["unexplained_loss_kwh"]
    assert (o.state, o.band, o.gap) == ("TOLERANCE_NOT_AVAILABLE", None, D("120"))
    # a SITE declaration beats the row's default
    o = _observe("Kobo", {"unexplained_l": _site("diesel_l", "20")})["unexplained_l"]
    assert (o.state, o.band, o.tolerance.source) == ("INSIDE_TOLERANCE", D("126.8"), "SITE")


def test_5_pct_zero_is_band_zero_without_reading_of_factor() -> None:  # D-3B4.19
    o = _observe("Kobo", {"candidate_l": _site("diesel_l", "0")})["candidate_l"]
    assert (o.state, o.band, o.gap) == ("RAISED", D(0), D("25"))
    # diesel_l unknown (unexplained_l actual removed): band 0 is still known
    got = _observe("Kobo", {"candidate_l": _site("diesel_l", "0.00")}, drop_actual=("unexplained_l",))
    assert got["candidate_l"].band == D(0) and got["candidate_l"].state == "RAISED"
    got = _observe("Kobo", {"candidate_l": _site("diesel_l", "5")}, drop_actual=("unexplained_l",))
    assert got["candidate_l"].state == "TOLERANCE_NOT_AVAILABLE"
    o = _observe("Kisiwa", {"unexplained_l": _site("diesel_l", "0")})["unexplained_l"]
    assert (o.state, o.gap, o.band) == ("RAISED", D("20"), D(0))


# --- test 6: unknown is not zero -------------------------------------------------------------------------------------

def test_6_unknown_is_not_zero() -> None:
    o = _observe("Kobo", drop_actual=("om",))["om"]
    assert (o.state, o.gap, o.band, o.actual) == ("ACTUAL_NOT_AVAILABLE", None, None, None)
    o = _observe("Kobo", drop_target=("outstanding",))["outstanding"]
    assert (o.state, o.gap) == ("TARGET_NOT_AVAILABLE", None)
    o = _observe("Kobo", currency={"outstanding": "KES"})["outstanding"]
    assert (o.state, o.gap, o.currency) == ("CURRENCY_MISMATCH", None, "USD")


def _snapshot(inputs, targets, *, sid: uuid.UUID | None = None, at: datetime | None = None) -> SiteMonthSnapshot:
    site = SiteRef(uuid.UUID(int=1), uuid.UUID(int=2), inputs.site_code, "MINIGRID", "Africa/Nairobi")
    return SiteMonthSnapshot(sid or uuid.uuid4(), uuid.UUID(int=1), site, inputs.month,
                             at or datetime(2026, 11, 5, tzinfo=timezone.utc), "service:test", True, (), inputs,
                             evaluate_inputs(inputs), targets)


def test_6b_the_uncarried_actual() -> None:  # D-3B4.26, plant P9
    inputs, targets = t5b._kisiwa()
    got = {o.factor_id: o for o in obs.observe_site(_snapshot(inputs, targets), {})}
    assert got["om"].state == "ACTUAL_NOT_AVAILABLE"
    assert site_bridge(inputs, targets).actual.values["om"].value is not None


# --- test 7: basis ---------------------------------------------------------------------------------------------------

def test_7_basis_ignores_instants_and_ids() -> None:
    inputs, targets = t5b._kisiwa()
    a = obs.observe_site(_snapshot(inputs, targets), {"unexplained_l": _site("diesel_l", "5")})
    b = obs.observe_site(_snapshot(inputs, targets, at=datetime(2026, 12, 1, tzinfo=timezone.utc)),
                         {"unexplained_l": dataclasses.replace(_site("diesel_l", "5.00"), declaration_id=uuid.uuid4())})
    assert [obs.basis(x, "MINI_GRID", OCT) for x in a] == [obs.basis(x, "MINI_GRID", OCT) for x in b]


def test_7_basis_moves_with_every_listed_field() -> None:
    o = _observe("Kobo")["unexplained_l"]
    base = obs.basis(o, "MINI_GRID", OCT)
    assert obs.basis(o, "COLD_CHAIN", OCT) != base and obs.basis(o, "MINI_GRID", "2026-11") != base
    changes = {"factor_id": "candidate_l", "direction": "DOWN", "kind": "CASH", "state": "INSIDE_TOLERANCE",
               "unit": "KWH", "currency": "USD", "actual": D("121"), "target": D("1"), "gap": D("119"),
               "band": D("23.7"), "actual_evidence": "MEASURED", "target_evidence": "ESTIMATED",
               "sources": ("other",), "origins": ("observed-financial",),
               "tolerance": dataclasses.replace(o.tolerance, source="SITE")}
    for name, value in changes.items():
        assert obs.basis(dataclasses.replace(o, **{name: value}), "MINI_GRID", OCT) != base, name
    for tol in (dataclasses.replace(o.tolerance, of_factor="necessary_l"), dataclasses.replace(o.tolerance, pct=D(3))):
        assert obs.basis(dataclasses.replace(o, tolerance=tol), "MINI_GRID", OCT) != base
    assert obs.basis(dataclasses.replace(o, tolerance=dataclasses.replace(o.tolerance, pct=D("2.00"))),
                     "MINI_GRID", OCT) == base  # 2.0 and 2.00 are one value


# --- test 8: F2, the 5b world ----------------------------------------------------------------------------------------

#: Pre-flight (c): the observed leaves the 5b world gives Kobo no October actual for.
F2_NOT_SUPPLIED = {"delivered_kwh", "unexplained_loss_kwh", "adjustments_kwh", "unmapped_kwh", "tariff",
                   "productive_tariff", "necessary_l", "candidate_l", "unexplained_l", "reduced_days",
                   "unserved_critical_kwh", "customer_hours_interrupted", "dawn_days_below"}


LITRE_LEAVES = ("necessary_l", "candidate_l", "unexplained_l")


def _kobo_5b(fb=None, floors=obs.NO_FLOORS) -> dict:
    w = t5b._world()
    actual, targets = t5b.reads(w, fb)
    s = t5b.ref(w, t5b.KOBO)
    return {o.factor_id: o for o in obs.observe(actual.site(s, OCT, t5b.READ_AT),
                                                targets.site(s, OCT, t5b.READ_AT).structure, {}, floors)}


def test_8_5b_world_kobo_october() -> None:
    got = _kobo_5b()
    o = got["outstanding"]
    assert (o.state, format(o.gap, "f"), o.kind) == ("RAISED", "278.00", "CASH")
    # DD3d.4: the 5b world now supplies the three litre leaves (`pack_litres`), as its fuel cost is litres times a price
    not_supplied = F2_NOT_SUPPLIED - set(LITRE_LEAVES)
    assert {k for k, v in got.items() if v.actual is None} == not_supplied
    for leaf in not_supplied:
        assert got[leaf].state == "ACTUAL_NOT_AVAILABLE", leaf
    # The rule (D-3B4.6, P5 rule 3): an UP leaf with a leak's target of 0. Candidate litres carry no tolerance (band 0),
    # so 25 L are raised; unexplained litres carry 2 % of the 634 L used (12.68 L), so 120 L are raised; necessary
    # litres (489 of a 700 L target) are favourable.
    assert {f: (got[f].state, got[f].actual, got[f].target, got[f].gap, got[f].band, got[f].tolerance.source)
            for f in LITRE_LEAVES} == {
        "necessary_l": ("FAVOURABLE", D("489"), D("700"), D("-211"), None, "NONE"),
        "candidate_l": ("RAISED", D("25"), D(0), D("25"), D(0), "NONE"),
        "unexplained_l": ("RAISED", D("120"), D(0), D("120"), D("12.68"), "STRUCTURE")}
    assert [k for k, v in got.items() if v.state == "RAISED"] == ["outstanding", "candidate_l", "unexplained_l"]
    # Kobo's declared tank floor (2a = 50 L, D-DD.153) sets the band, and 120 L are still beyond it
    floored = _kobo_5b(floors={"unexplained_l": obs.Floor(D(50), D(25), "GENERIC_DEFAULT", "rev")})
    assert (floored["unexplained_l"].state, floored["unexplained_l"].band) == ("RAISED", D(50))
    assert floored["candidate_l"] == got["candidate_l"]  # the floor is for the tank balance only


def test_8b_5b_world_without_litres() -> None:
    """The pin before DD3d.4: a Site whose readings give no litres has no litre actual, so nothing is raised on them."""
    from test_4b_money_leaves import fallback

    got = _kobo_5b(fallback())
    assert {k for k, v in got.items() if v.actual is None} == F2_NOT_SUPPLIED
    for leaf in F2_NOT_SUPPLIED:
        assert got[leaf].state == "ACTUAL_NOT_AVAILABLE", leaf
    assert [k for k, v in got.items() if v.state == "RAISED"] == ["outstanding"]


# --- test 9: the pin -------------------------------------------------------------------------------------------------

def test_9_pin_of_key_and_also_pinned() -> None:
    key = rules.finding_key("MINI_GRID", "candidate_l", OCT, "UP")
    assert key == "structure:MINI_GRID:candidate_l:2026-10:UP"
    assert rules.pin_of_key(key) == ("MINI_GRID", "candidate_l")
    for bad in ("structure:MINI_GRID:candidate_l:2026-10:SIDEWAYS", "fuel:MINI_GRID:candidate_l:2026-10:UP",
                "structure:mini_grid:candidate_l:2026-10:UP"):
        with pytest.raises(ValueError):
            rules.pin_of_key(bad)
    got = _observe("Kobo")
    kw = dict(structure_key="MINI_GRID", structure_version=MG.version, month=OCT, snapshot_id=uuid.UUID(int=3),
              snapshot_as_of=datetime(2026, 11, 5, tzinfo=timezone.utc),
              tolerance_known_at=datetime(2026, 11, 6, tzinfo=timezone.utc))
    assert obs.claim(got["candidate_l"], **kw)["also_pinned"] == ["GENERATOR_SUPPORT_CANDIDATE"]
    assert obs.claim(got["unexplained_l"], **kw)["also_pinned"] == ["UNEXPLAINED_FUEL"]
    assert obs.claim(got["outstanding"], **kw)["also_pinned"] == []
    c = obs.claim(got["outstanding"], **kw)
    assert (c["home"], c["objective"], c["unit"], c["currency"], c["gap"]) == ("OPTIMIZE_COST", "O3",
                                                                              "MONEY", "USD", "278.0")
    assert set(c) == CLAIM_KEYS
    check_pins()


# --- spec §4.3's lifecycle table, every cell against a literal (review L1) ----------------------------------------------

_W = ("NO_GAP", "FAVOURABLE", "INSIDE_TOLERANCE")
_U = ("ACTUAL_NOT_AVAILABLE", "TARGET_NOT_AVAILABLE", "CURRENCY_MISMATCH", "TOLERANCE_NOT_AVAILABLE")
_NLS = ("NO_LONGER_SUPPORTED", "NO_LONGER_SUPPORTED")


def _expected(held: str | None, same_basis: bool, state: str):
    """The spec table written out per held lifecycle; `None` is "write nothing"."""
    if held is None:
        return ("OPENED", "SUPPORTED") if state == "RAISED" else None
    if held == "SUPPORTED":
        if state == "RAISED":
            return None if same_basis else ("SUPPORT_CHANGED", "SUPPORTED")
        if state in _W:
            return _NLS
        if state in _U:
            return ("UNCONFIRMED", "UNCONFIRMED")
    if held == "UNCONFIRMED":
        if state == "RAISED":
            return ("REOPENED", "SUPPORTED")
        if state in _W:
            return _NLS
    if held == "NO_LONGER_SUPPORTED" and state == "RAISED":
        return ("REOPENED", "SUPPORTED")
    return None


@pytest.mark.parametrize("held", [None, "SUPPORTED", "UNCONFIRMED", "NO_LONGER_SUPPORTED"])
@pytest.mark.parametrize("same", [True, False])
@pytest.mark.parametrize("state", ["RAISED", *_W, *_U])
def test_11_transition_walks_every_cell_of_the_table(held, same, state) -> None:
    assert rules.transition(held, "b" if held else None, state, "b" if same else "c") == _expected(held, same, state)


def test_11_the_named_rows() -> None:
    t = rules.transition
    assert t("UNCONFIRMED", "b", "RAISED", "b") == ("REOPENED", "SUPPORTED")
    assert t("UNCONFIRMED", "b", "INSIDE_TOLERANCE", "b") == _NLS
    assert t("UNCONFIRMED", "b", "FAVOURABLE", "b") == _NLS
    assert t("UNCONFIRMED", "b", "NO_GAP", "b") == _NLS
    assert t("NO_LONGER_SUPPORTED", "b", "ACTUAL_NOT_AVAILABLE", "b") is None
    assert t("UNCONFIRMED", "b", "TARGET_NOT_AVAILABLE", "b") is None


def test_15_tolerance_read_is_as_known() -> None:  # review L2: a later-recorded declaration is not yet known
    from types import SimpleNamespace as NS

    from assetops_backend.structure.observe.service import tolerance_in_force

    t0 = datetime(2026, 11, 1, tzinfo=timezone.utc)
    t1, t2 = datetime(2026, 11, 2, tzinfo=timezone.utc), datetime(2026, 11, 3, tzinfo=timezone.utc)
    mk = lambda rid, at, pct, state="SET": NS(id=rid, structure_key="MINI_GRID", factor_id="necessary_l",
                                              valid_from="2026-10", recorded_at=at, state=state, of_factor="diesel_l",
                                              pct=pct)
    rows = (mk(1, t0, "5"), mk(2, t2, "9"))
    got = tolerance_in_force(rows, "MINI_GRID", "2026-10", t1)["necessary_l"]
    assert (got.pct, got.declaration_id) == (Decimal(5), 1)                 # the later row is not yet recorded
    assert tolerance_in_force(rows, "MINI_GRID", "2026-10", t2)["necessary_l"].declaration_id == 2
    assert tolerance_in_force((mk(1, t0, "5"), mk(2, t2, None, "CLEARED")), "MINI_GRID", "2026-10", t1)["necessary_l"]
