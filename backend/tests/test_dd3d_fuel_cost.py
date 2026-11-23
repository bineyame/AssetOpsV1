"""DD3d.4 (D-DD.163, D-DD.169): fuel cost is what was burned x price, the invoices are fuel bought, the declared prices.

Pure: the registry, the evaluator over hand-written leaves, the commercial source's tables, the heading words, and the
three world price fixtures against the scenario manifest. No database; every expected value is a literal or the
manifest's own."""
from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest
import yaml

from assetops_backend.i18n.statements.en import vocabulary as words
from assetops_backend.structure import money
from assetops_backend.structure.check import StructureError
from assetops_backend.structure.evaluate import LeafValue, Missing, evaluate
from assetops_backend.structure.reconciliation import HEADING_WORDS
from assetops_backend.structure.registry import REGISTRIES, FilledBy
from assetops_backend.structure.sources import STATED_STATE
from assetops_backend.structure.targets.rules import BUDGET_STATED, MAIN_OF
from assetops_contracts.canonical.units import KWH, MONEY

MG = REGISTRIES["MINI_GRID"]
D = Decimal
BACKEND = Path(__file__).resolve().parents[1]
MANIFEST = BACKEND.parent / "Docs/demo-sprint/product-direction-layer4/demo-site-scenario-manifest.yaml"
WORLD = BACKEND / "conversions" / "world"
NAMES = {"KOBO-001": "Kobo", "KISIWA-001": "Kisiwa", "MTO-001": "Mto"}
BOUGHT = FilledBy("COMMERCIAL_RECORD", "EXPENSE (FUEL)", "Fuel invoices for the month")


def _leaves(**given: str | None) -> dict[str, LeafValue]:
    """Every MINI_GRID leaf absent except those given (None stays absent)."""
    out = {}
    for row in MG.rows:
        if not row.is_leaf:
            continue
        raw = given.get(row.factor_id)
        currency = "USD" if row.unit.has_money_dimension else None
        if raw is not None:
            out[row.factor_id] = LeafValue(D(raw), "RECORDED", ("t",), None, None, currency, ("source-emulated",))
        elif row.absent == "OPTION_ONLY":
            out[row.factor_id] = LeafValue(row.neutral, "NEUTRAL", ("option-only neutral",), None, None, None)
        else:
            fb = row.filled_by
            out[row.factor_id] = LeafValue(None, "NOT_AVAILABLE", (), None,
                                           Missing(fb.kind, fb.family, "NOT_RECEIVED", None, (), fb.words, None, None),
                                           None)
    return out


def test_1_the_structure_is_version_5_and_only_fuel_cost_lost_its_record() -> None:
    assert MG.version == 5
    assert {r.factor_id for r in MG.rows if r.stated_by is not None} == {"revenue", "metered_kwh", "billed_kwh"}
    assert dict(STATED_STATE["MINI_GRID"]) == {"revenue": "PROVIDED", "metered_kwh": "PROVIDED",
                                               "billed_kwh": "PROVIDED"}


@pytest.mark.parametrize(("litres", "price", "want"), [("500", "1.25", "625.00"), ("32", "1.25", "40.00")])
def test_2_fuel_cost_is_litres_burned_times_price(litres: str, price: str, want: str) -> None:
    v = evaluate(MG, _leaves(necessary_l=litres, candidate_l="0", unexplained_l="0", diesel_price=price), {})
    assert v["fuel_cost"].value == D(want) and v["fuel_cost"].stated is False


def test_3_no_litres_no_fuel_cost_and_never_the_invoices() -> None:
    v = evaluate(MG, _leaves(diesel_price="1.25"), {})
    assert v["fuel_cost"].value is None and v["cost_to_serve"].value is None
    assert "necessary_l" in v["fuel_cost"].missing_leaves


def test_4_the_invoices_are_fuel_bought() -> None:
    assert "fuel_cost" not in money._ROWS and "fuel_cost" not in money.READ_AS
    assert money._ROWS["fuel_bought"].kinds == ("EXPENSE",) and money._ROWS["fuel_bought"].money
    assert money.READ_AS["fuel_bought"] == BOUGHT
    assert "fuel_bought" not in {r.factor_id for r in MG.rows}  # not a structure row


def test_5_the_reconciliation_heading_is_fuel_bought() -> None:
    assert HEADING_WORDS == {"revenue": "REVENUE", "fuel_bought": "FUEL_BOUGHT"}
    tables = next(v for v in vars(words).values() if isinstance(v, dict) and "record_noun" in v)
    assert tables["heading"]["entries"]["FUEL_BOUGHT"]["label"] == "Fuel bought (invoices)"
    assert "FUEL_COST" not in tables["heading"]["entries"] and "FUEL_COST" not in tables["record_noun"]["entries"]
    assert tables["record_noun"]["entries"]["FUEL_BOUGHT"]["in_sentence"] == "fuel invoices"


@pytest.mark.parametrize("code", sorted(NAMES))
def test_6_the_declared_price_fixture_is_the_manifests(code: str) -> None:
    prices = next(t["prices"] for t in yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))["tenants"]
                  if t["tenant"] == "lakeside-power")["diesel_usd_per_l"]
    doc = json.loads((WORLD / f"lakeside-power.diesel-price.{code}.json").read_text(encoding="utf-8"))
    (step,) = doc["steps"]
    assert (doc["fixture"], doc["version"], doc["assumption_key"]) == (
        "demo-diesel-price-publications", 2, "diesel_price_per_litre")
    assert D(step["value"]) == D(str(prices[NAMES[code]]))
    assert {k: step[k] for k in step if k != "value"} == {
        "step": "v1", "change_kind": "INITIAL", "currency": "USD", "basis": "AUTHORED_ESTIMATE",
        "source_reference": "Declared diesel price per litre for this Site (world declaration); not a fuel invoice",
        "valid_from": "2026-06-30T21:00:00Z", "valid_to": None, "expected_prior_step": None,
        "idempotency_key": f"world-diesel-price-{code.lower()}-v1"}


# --- D-DD.178: a budget line states its heading's target whether or not a record states the actual --------------------

GOLDEN = Path(__file__).resolve().parent / "golden" / "dd3d_targets_before.json"
CODES = ("KOBO-001", "KISIWA-001", "MTO-001")


def target_worlds() -> dict:
    """5a's fixture Sites as `TargetRead` gives them: as they are, each with no diesel price, and with the delivered
    kWh's prices known. Every field of every value but the structure version, as text; a budget line's random revision
    id is named by the factor it states."""
    import test_5a_targets as t5a

    w = t5a.lakeside()
    out = {}
    for name, overrides in (("as-is", lambda c: None), ("priced", lambda c: t5a.PRICED),
                            ("no-price", lambda c: {c: {"diesel_price": t5a._actual_absent("diesel_price")}})):
        for code in CODES:
            got = t5a.read_site(w, code, overrides(code))
            lines = {v.sources[0]: f"budget:{f}" for f, v in got.structure.values.items()
                     if len(v.sources) == 1 and v.sources[0].startswith("budget:")}
            out[f"{name}/{code}"] = {
                "values": {f: [None if v.value is None else format(v.value, "f"), v.evidence,
                               sorted(lines.get(x, x) for x in v.sources), v.currency, list(v.origins), v.stated,
                               None if v.computed is None else format(v.computed, "f"), list(v.missing_leaves), list(v.assumed_leaves), list(v.detail_missing),
                               None if v.missing is None else [v.missing.cause, v.missing.carried_as, v.missing.note]] for f, v in got.structure.values.items()},
                "checks": [repr(c) for c in got.checks], "currency": got.currency}
    return out


def test_7_the_target_side_is_what_it_was_before_fuel_cost_was_unstated() -> None:
    """The golden was written by this function on main aae7d9826, where `fuel_cost` still had `stated_by` (v4)."""
    assert target_worlds() == json.loads(GOLDEN.read_text(encoding="utf-8"))


def test_8_fuel_cost_is_never_a_target_check() -> None:
    """Its target is the budget line itself, so it is not checked against the budget line."""
    import test_5a_targets as t5a

    w = t5a.lakeside()
    seen = {c.factor_id for code in CODES for c in t5a.read_site(w, code).checks}
    assert seen and not seen & {"fuel_cost", "revenue", "billed_kwh"}


def test_9_without_a_price_mtos_fuel_target_is_the_budget_line() -> None:
    import test_5a_targets as t5a

    w = t5a.lakeside()
    v = t5a.read_site(w, "MTO-001", {"MTO-001": {"diesel_price": t5a._actual_absent("diesel_price")}}).structure.values
    assert (v["fuel_cost"].value, v["fuel_cost"].evidence, v["fuel_cost"].stated) == (D("375.00"), "DECLARED", True)
    assert v["necessary_l"].value is None and v["diesel_price"].value is None


def _stated_fuel(value: str = "875.00") -> dict[str, LeafValue]:
    return {"fuel_cost": LeafValue(D(value), "DECLARED", ("budget",), None, None, "USD", ("source-emulated",))}


def test_10_only_the_caller_that_names_it_may_state_fuel_cost() -> None:
    leaves = _leaves(necessary_l="500", candidate_l="0", unexplained_l="0", diesel_price="1.25")
    with pytest.raises(StructureError) as refused:
        evaluate(MG, leaves, _stated_fuel())
    assert (refused.value.code, refused.value.factor_id) == ("STRUCTURE_STATED", "fuel_cost")
    v = evaluate(MG, leaves, _stated_fuel(), stated_nodes=frozenset({"fuel_cost"}))["fuel_cost"]
    assert (v.value, v.computed, v.stated) == (D("875.00"), D("625.00"), True)


@pytest.mark.parametrize("name", ["necessary_l", "not_a_factor"])
def test_11_stated_nodes_name_no_leaf_and_no_unknown_row(name: str) -> None:
    with pytest.raises(StructureError) as refused:
        evaluate(MG, _leaves(), {}, stated_nodes=frozenset({name}))
    assert (refused.value.code, refused.value.factor_id) == ("STRUCTURE_STATED", name)


def test_12_every_budget_stated_node_could_be_stated_by_a_record() -> None:
    """The registry check's rule for `stated_by`: a non-leaf, summed over Sites, in money or kWh."""
    assert dict(BUDGET_STATED) == {"MINI_GRID": frozenset({"billed_kwh", "revenue", "fuel_cost"})}
    for key, nodes in BUDGET_STATED.items():
        assert nodes == {h for heads in MAIN_OF[key].values() for h in heads}  # derived, never a second list
        for node in nodes:
            row = REGISTRIES[key].row(node)
            assert not row.is_leaf and row.composes == "SUM" and str(row.unit) in (str(MONEY), str(KWH)), node


def test_13_only_the_target_side_names_stated_nodes() -> None:
    package = BACKEND / "assetops_backend"
    callers = {p.relative_to(package).as_posix() for p in package.rglob("*.py")
               if "stated_nodes=" in p.read_text(encoding="utf-8")}
    assert callers == {"structure/targets/read.py"}
