"""6c (`specs/6c-option-evaluator/spec.md` §5): the hand-written leaf maps and option changes the 6c tests share.

`leaves_for(registry, given)` gives every leaf of a registry: the given ones as written, an OPTION_ONLY leaf NEUTRAL at
its neutral, a CALENDAR leaf DERIVED with October's days, every other leaf NOT_AVAILABLE.
"""
from __future__ import annotations

from decimal import Decimal
from types import MappingProxyType

from assetops_backend.structure.difference import LeafChange
from assetops_backend.structure.evaluate import LeafValue, Missing
from assetops_backend.structure.registry import REGISTRIES, Registry

D = Decimal
MG, CC, EV = REGISTRIES["MINI_GRID"], REGISTRIES["COLD_CHAIN"], REGISTRIES["EV_DEPOT_CAPTIVE"]
CALENDAR = {"period_days": D(31), "nights_in_period": D(31), "minutes_per_day": D(1440)}


def _missing(registry: Registry, factor_id: str, carried_as: str | None = None) -> Missing:
    fb = registry.row(factor_id).filled_by
    return Missing(fb.kind, fb.family, "NOT_RECEIVED", carried_as, (), fb.words, None)


def leaves_for(registry: Registry, given: dict[str, LeafValue]) -> MappingProxyType:
    out = {}
    for row in registry.rows:
        if not row.is_leaf:
            continue
        fid = row.factor_id
        if fid in given:
            out[fid] = given[fid]
        elif row.absent == "OPTION_ONLY":
            out[fid] = LeafValue(row.neutral, "NEUTRAL", (), None, None, None, ())
        elif row.filled_by.family == "CALENDAR":
            out[fid] = LeafValue(CALENDAR[fid], "DERIVED", ("calendar",), None, None, None, ())
        else:
            out[fid] = LeafValue(None, "NOT_AVAILABLE", (), None, _missing(registry, fid), None, ())
    return MappingProxyType(out)


def stated(value, evidence: str = "DECLARED", currency: str | None = None,
           origins: tuple[str, ...] = ("unknown",)) -> LeafValue:
    return LeafValue(D(value), evidence, ("fixture",), None, None, currency, origins)


def recorded(value, currency: str | None = None, origin: str = "observed-financial") -> LeafValue:
    return stated(value, "RECORDED", currency, (origin,))


def assumed(registry: Registry, factor_id: str, value, currency: str) -> LeafValue:
    return LeafValue(D(value), "ESTIMATED", ("price",), None, _missing(registry, factor_id, "ASSUMPTION"), currency,
                     ("unknown",))


def change(delta, origin: str = "demo-simulated") -> LeafChange:
    return LeafChange(D(delta), "MODELLED", ("replay-study",), (origin,), None)


def f1_base(wear: bool = True) -> MappingProxyType:
    given = {"diesel_price": assumed(MG, "diesel_price", "1.25", "USD")}
    if wear:
        given["wear_rate"] = stated("0.05", currency="USD")
    return leaves_for(MG, given)


def f1_changes(avoided, added) -> dict[str, LeafChange]:
    return {"candidate_l": change(-D(avoided)), "battery_throughput_kwh": change(D(added))}


def c1_base(base_kwh: bool = True, crate_origin: str = "observed-financial") -> MappingProxyType:
    given = {"k_kwh_per_crate_day": stated(2), "crate_days": recorded(1000, origin=crate_origin),
             "elec_price": recorded("0.20", "USD")}
    if base_kwh:
        given["base_kwh"] = stated(3000)
    return leaves_for(CC, given)


C1_CHANGES = {"model_factor": change("-0.1", "field-integrated")}


def e1_base() -> MappingProxyType:
    return leaves_for(EV, {"peak_kwh": recorded(5000), "kwh_0000_0500": recorded(2000),
                           "peak_price": recorded("0.30", "USD"), "night_price": recorded("0.10", "USD")})


E1_CHANGES = {"peak_kwh": change(-1000, "field-integrated"), "kwh_0000_0500": change(1000, "field-integrated")}


# --- F1's decision (an injected lever, D-P6.21) and the decisions of C1 and E1 ------------------------------------

import dataclasses  # noqa: E402
import json  # noqa: E402
from datetime import datetime, timezone  # noqa: E402
from pathlib import Path  # noqa: E402
from uuid import UUID  # noqa: E402

from assetops_backend.decisions.models import SETTING_GRID_CHANGES  # noqa: E402
from assetops_backend.decisions.records import DecisionRow, OneOffRow, OptionRow  # noqa: E402
from assetops_backend.structure.levers import LEVERS, Lever, SettingAxis, grid, option_key  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "decisions"
TENANT = UUID(int=0xA)
SITE = UUID(int=0xB)
PERSON = UUID(int=0xC)
AT = datetime(2026, 11, 24, 9, 0, tzinfo=timezone.utc)
CURRENT = {"stop_soc_pct": D(90), "reserve_soc_pct": D(30)}
TEST_LEVER = Lever("test_stop_reserve", "MINI_GRID", "candidate_l", "SETTING_GRID",
                   (SettingAxis("stop_soc_pct", (D(90), D(80), D(70), D(60)), "%"),
                    SettingAxis("reserve_soc_pct", (D(30), D(25)), "%")),
                   "stop-{stop_soc_pct}-reserve-{reserve_soc_pct}", ("candidate_l", "battery_throughput_kwh"))
F1G_LEVER = dataclasses.replace(TEST_LEVER, axes=(SettingAxis("stop_soc_pct", (D(90), D(60)), "%"),
                                                  TEST_LEVER.axes[1]))
TEST_GRID = {"test_stop_reserve": SETTING_GRID_CHANGES["generator_stop_reserve"]}


def decision_of(lever: Lever | None, structure_key: str = "MINI_GRID", current=None, keys=(), period="2026-10"):
    """A decision and its options in position order: no action first, then the lever's grid minus today."""
    current = CURRENT if current is None else current
    did = UUID(int=0xD)
    row = DecisionRow(did, TENANT, SITE, structure_key, "none" if lever is None else lever.lever_id,
                      "contribution" if lever is None else lever.purpose_factor, None, period, 12, dict(current),
                      "decision-prepare-1", PERSON, "ANALYST", True, AT)
    options = [OptionRow(UUID(int=0x100), TENANT, did, "no-action", "NO_ACTION", dict(current), 0)]
    points = [] if lever is None else [p for p in grid(lever) if dict(p) != dict(current)]
    for point in points:
        options.append(OptionRow(UUID(int=0x100 + len(options)), TENANT, did, option_key(lever, point),
                                 "SETTING_GRID", dict(point), len(options)))
    for key in keys:
        options.append(OptionRow(UUID(int=0x100 + len(options)), TENANT, did, key, "SETTING_GRID", {}, len(options)))
    return row, tuple(options)


def one_off_of(option: OptionRow, amount="90.00", currency="USD") -> OneOffRow:
    return OneOffRow(UUID(int=0x200 + option.position), TENANT, option.id, D(amount), currency, 0,
                     "Technician sets the controller on a routine visit", PERSON, "SITE_MANAGER", True, AT)


def study_doc(name: str = "study-f1.json") -> dict:
    return json.loads((FIXTURES / name).read_text())


def write_study(tmp_path: Path, doc: dict, name: str = "study.json") -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(doc))
    return path


def case_doc(doc: dict, case_id: str) -> dict:
    return next(c for c in doc["cases"] if c["case_id"] == case_id)


REAL_LEVER = LEVERS["generator_stop_reserve"]


# --- planted registries (D-P6.40): one rule each, with literal numbers --------------------------------------------------

from assetops_backend.structure.registry import FactorRow, FilledBy  # noqa: E402

_LITRES = MG.row("diesel_l").unit


def planted(rows: dict[str, str | None], neutral: dict[str, Decimal] | None = None) -> Registry:
    """A registry of litre rows: a leaf has `None` for its expression; `contribution` is the outcome."""
    neutral = neutral or {}
    return Registry("PLANT", 1, tuple(
        FactorRow(fid, expr, _LITRES, None, None if expr else FilledBy("PLANT_FAMILY", f"{fid}_record"),
                  "OPTION_ONLY" if fid in neutral else None, None, neutral=neutral.get(fid))
        for fid, expr in rows.items()))


#: a changed leaf through `/`, `ceil`, `floor`, `min` and `max`
OPS = planted({"a": None, "b": None, "c": None, "ratio": "a / b", "cap": "ceil(a / b)", "fl": "floor(a / b)",
               "lo": "min(a, c)", "hi": "max(a, c)", "contribution": "ratio + cap + fl + lo + hi"})
#: a product of two changed leaves
PRODUCT = planted({"a": None, "b": None, "prod": "a * b", "contribution": "prod"})
#: the option-only neutral zero short cut: a * n, n neutral at 0, a without a value
NEUTRAL = planted({"a": None, "n": None, "x": None, "q": "a * n * x", "contribution": "q"}, {"n": Decimal(0)})
#: a node resting on an assumption, read by the outcome through a product
ASSUMING = planted({"a": None, "w": None, "s": "w * 2", "contribution": "a * s"})
#: a division
DIVISION = planted({"a": None, "z": None, "r": "a / z", "contribution": "r"})
#: the outcome as a leaf: an option's monthly change is the change on it
OUTCOME_LEAF = planted({"contribution": None})
