"""3B4 (spec §7 tests 2, 4 to 9; tests 1, 1b and 3 land with the `check.py` commit after 4a and 3B6, spec §0).

No database. Expected tables and figures are literals from the pack (`derived-values.json`) and spec §2.1 and §6,
never read from `OBSERVED`, `signs` or `observe` (W2).
"""
from __future__ import annotations

import dataclasses
import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

import test_5b_attribution as t5b
from assetops_backend.chain.ports import SiteRef
from assetops_backend.structure.attribution.site import site_bridge
from assetops_backend.structure.check import check_pins
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
             "necessary_l": ("RAISED", "30", "BOTTOM_LINE"), "candidate_l": ("RAISED", "330", "BOTTOM_LINE"),
             "unexplained_l": ("RAISED", "120", "BOTTOM_LINE"), "delivered_kwh": ("FAVOURABLE", "550", "BOTTOM_LINE")},
    "Kisiwa": {"adjustments_kwh": ("RAISED", "30", "BOTTOM_LINE"), "outstanding": ("RAISED", "270", "CASH"),
               "necessary_l": ("RAISED", "80", "BOTTOM_LINE"), "reduced_days": ("RAISED", "2", "PROTECT"),
               "delivered_kwh": ("FAVOURABLE", "450", "BOTTOM_LINE"),
               "unexplained_l": ("INSIDE_TOLERANCE", "20", "BOTTOM_LINE")},
    "Mto": {"unexplained_loss_kwh": ("RAISED", "120", "BOTTOM_LINE"), "adjustments_kwh": ("RAISED", "40", "BOTTOM_LINE"),
            "unmapped_kwh": ("RAISED", "140", "BOTTOM_LINE"), "necessary_l": ("RAISED", "20", "BOTTOM_LINE"),
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
    assert kobo.band == D("23.6") and kobo.tolerance.source == "STRUCTURE"
    assert kisiwa.band == D("48") and kisiwa.state == "INSIDE_TOLERANCE"
    assert _observe("Kobo")["outstanding"].band == D(0)
    assert _observe("Kobo")["outstanding"].currency == "USD" and _observe("Kobo")["necessary_l"].currency is None


# --- test 5: tolerance -----------------------------------------------------------------------------------------------

def _site(of: str, pct: str) -> obs.ToleranceInForce:
    return obs.ToleranceInForce("SITE", of, D(pct), uuid.UUID(int=7))


def test_5_tolerance() -> None:
    o = _observe("Kobo", {"necessary_l": _site("diesel_l", "5")})["necessary_l"]
    assert (o.state, o.band, o.tolerance.source) == ("INSIDE_TOLERANCE", D("59"), "SITE")
    o = _observe("Kobo", {"necessary_l": _site("diesel_l", "2")})["necessary_l"]
    assert (o.state, o.band) == ("RAISED", D("23.6"))
    o = _observe("Kisiwa", {"unexplained_l": _site("unexplained_l", "100")})["unexplained_l"]
    assert (o.state, o.band, o.gap) == ("INSIDE_TOLERANCE", D("20"), D("20"))  # equal is inside (strict outside)
    o = _observe("Mto", {"unexplained_loss_kwh": _site("delivered_kwh", "1")},
                 drop_actual=("delivered_kwh",))["unexplained_loss_kwh"]
    assert (o.state, o.band, o.gap) == ("TOLERANCE_NOT_AVAILABLE", None, D("120"))
    # a SITE declaration beats the row's default
    o = _observe("Kobo", {"unexplained_l": _site("diesel_l", "20")})["unexplained_l"]
    assert (o.state, o.band, o.tolerance.source) == ("INSIDE_TOLERANCE", D("236"), "SITE")


def test_5_pct_zero_is_band_zero_without_reading_of_factor() -> None:  # D-3B4.19
    o = _observe("Kobo", {"necessary_l": _site("diesel_l", "0")})["necessary_l"]
    assert (o.state, o.band, o.gap) == ("RAISED", D(0), D("30"))
    # diesel_l unknown (candidate_l actual removed): band 0 is still known
    got = _observe("Kobo", {"necessary_l": _site("diesel_l", "0.00")}, drop_actual=("candidate_l",))
    assert got["necessary_l"].band == D(0) and got["necessary_l"].state == "RAISED"
    got = _observe("Kobo", {"necessary_l": _site("diesel_l", "5")}, drop_actual=("candidate_l",))
    assert got["necessary_l"].state == "TOLERANCE_NOT_AVAILABLE"
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


def test_8_5b_world_kobo_october() -> None:
    w = t5b._world()
    actual, targets = t5b.reads(w)
    s = t5b.ref(w, t5b.KOBO)
    got = {o.factor_id: o for o in obs.observe(actual.site(s, OCT, t5b.READ_AT),
                                               targets.site(s, OCT, t5b.READ_AT).structure, {})}
    o = got["outstanding"]
    assert (o.state, format(o.gap, "f"), o.kind) == ("RAISED", "278.00", "CASH")
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
