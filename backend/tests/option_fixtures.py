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
