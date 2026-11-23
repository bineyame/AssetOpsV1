"""3B4 unit 1 (spec §2.2, §3, §4.3; D-3B4.5, D-3B4.6, D-3B4.12, D-3B4.18, D-3B4.19, D-3B4.26): the rule. Pure.

One observation per observed leaf: the actual side against 5a's target side, adverse by the leaf's declared
direction and strictly outside its tolerance band, or a named state that writes nothing. Unknown is never zero: a
missing side, currency pair or band basis is a state of its own, never a gap or a band of 0.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from types import MappingProxyType
from uuid import UUID

from assetops_backend.structure import pins as _pins
from assetops_backend.structure import registry as _registry
from assetops_backend.structure.check import StructureError
from assetops_backend.structure.evaluate import SiteStructure
from assetops_backend.structure.observe import rules
from assetops_backend.structure_snapshot import codec
from assetops_backend.structure_snapshot.model import SiteMonthSnapshot

STATES = ("ACTUAL_NOT_AVAILABLE", "TARGET_NOT_AVAILABLE", "CURRENCY_MISMATCH", "NO_GAP", "FAVOURABLE",
          "TOLERANCE_NOT_AVAILABLE", "INSIDE_TOLERANCE", "RAISED")
NOT_COMPUTED = ("ACTUAL_NOT_AVAILABLE", "TARGET_NOT_AVAILABLE", "CURRENCY_MISMATCH", "TOLERANCE_NOT_AVAILABLE")
SOURCES = ("SITE", "STRUCTURE", "NONE")
CLAIM_FORMAT = 1


def _context() -> Context:
    return Context(prec=34, rounding=ROUND_HALF_EVEN)


@dataclass(frozen=True)
class ToleranceInForce:
    source: str                     # "SITE" (a declaration), "STRUCTURE" (the row's Tolerance), "NONE"
    of_factor: str | None
    pct: Decimal | None
    declaration_id: UUID | None     # SITE only


NO_TOLERANCE = ToleranceInForce("NONE", None, None, None)


@dataclass(frozen=True)
class Floor:
    """D-DD.153: what the tank's two level readings can be out by together, in the leaf's unit."""
    litres: Decimal                 # TANK_MARGIN_FACTOR x accuracy_l
    accuracy_l: Decimal
    basis: str                      # fuel_balance.rules.ACCURACY_BASES
    revision_id: str                # the Foundation revision that declares it


NO_FLOORS: Mapping[str, Floor] = MappingProxyType({})


@dataclass(frozen=True)
class FactorObservation:
    factor_id: str
    direction: str                  # UP or DOWN
    kind: str                       # rules.KINDS
    state: str                      # STATES
    unit: str                       # str(row.unit)
    currency: str | None            # the actual's, for a money unit; else None
    actual: Decimal | None
    target: Decimal | None
    gap: Decimal | None             # actual - target; None unless both are values in one currency
    band: Decimal | None            # None unless the tolerance could be computed
    tolerance: ToleranceInForce
    actual_evidence: str
    target_evidence: str
    sources: tuple[str, ...]        # sorted union of the actual's and the target's sources
    origins: tuple[str, ...]        # the actual's origins
    floor: Floor | None = None      # only when it set the band (D-DD.153)


def in_force(registry: _registry.Registry, factor_id: str,
             site_declaration: ToleranceInForce | None) -> ToleranceInForce:
    """D-3B4.6: a SITE declaration wins; else the row's tolerance as STRUCTURE; else NONE."""
    if site_declaration is not None:
        return site_declaration
    row_tol = registry.row(factor_id).tolerance
    if row_tol is not None:
        return ToleranceInForce("STRUCTURE", row_tol.of_factor, row_tol.pct, None)
    return NO_TOLERANCE


def observe(actual: SiteStructure, target: SiteStructure,
            declarations: Mapping[str, ToleranceInForce],
            floors: Mapping[str, Floor] = NO_FLOORS) -> tuple[FactorObservation, ...]:
    """Spec §2.2: one observation per leaf of `OBSERVED[key]`, in that order. `floors` reaches the leaves of
    `FLOORED[key]` only (D-DD.153)."""
    key = actual.structure_key
    if (actual.site_code, actual.month, actual.structure_key, actual.structure_version) != (
            target.site_code, target.month, target.structure_key, target.structure_version):
        raise StructureError("STRUCTURE_COMPOSE", key, actual.site_code)
    if key not in rules.OBSERVED:
        raise StructureError("STRUCTURE_OBSERVE_KEY", key, "-")
    registry = _registry.REGISTRIES[key]
    floored = rules.FLOORED.get(key, ())
    return tuple(_one(registry, key, leaf, direction, actual, target, declarations.get(leaf),
                      floors.get(leaf) if leaf in floored else None)
                 for leaf, direction in rules.OBSERVED[key].items())


def observe_site(site: SiteMonthSnapshot,
                 declarations: Mapping[str, ToleranceInForce],
                 floors: Mapping[str, Floor] = NO_FLOORS) -> tuple[FactorObservation, ...]:
    """D-3B4.26: the one place the actual side is chosen: the un-carried `site.actual` (D-3B4.5)."""
    return observe(site.actual, site.targets.structure, declarations, floors)


def _one(registry, key, leaf, direction, actual: SiteStructure, target: SiteStructure,
         declaration: ToleranceInForce | None, floor: Floor | None = None) -> FactorObservation:
    row = registry.row(leaf)
    a, t = actual.values[leaf], target.values[leaf]
    tolerance = in_force(registry, leaf, declaration)
    money = rules.money_dimension(row.unit)
    gap = band = binding = None
    with localcontext(_context()):
        if a.value is None:
            state = "ACTUAL_NOT_AVAILABLE"
        elif t.value is None:
            state = "TARGET_NOT_AVAILABLE"
        elif money and a.currency != t.currency:
            state = "CURRENCY_MISMATCH"
        else:
            gap = a.value - t.value
            if gap == 0:
                state = "NO_GAP"
            elif (direction == rules.UP and gap < 0) or (direction == rules.DOWN and gap > 0):
                state = "FAVOURABLE"
            else:
                band = _band(tolerance, actual)
                if band is not None and tolerance.source != "NONE" and floor is not None and floor.litres > band:
                    band, binding = floor.litres, floor
                if band is None:
                    state = "TOLERANCE_NOT_AVAILABLE"
                elif abs(gap) <= band:
                    state = "INSIDE_TOLERANCE"
                else:
                    state = "RAISED"
    return FactorObservation(
        factor_id=leaf, direction=direction, kind=rules.kind_of(registry, key, leaf), state=state,
        unit=str(row.unit), currency=a.currency if money else None, actual=a.value, target=t.value, gap=gap,
        band=band, tolerance=tolerance, actual_evidence=a.evidence, target_evidence=t.evidence,
        sources=tuple(sorted(set(a.sources) | set(t.sources))), origins=tuple(a.origins), floor=binding)


def _band(tolerance: ToleranceInForce, actual: SiteStructure) -> Decimal | None:
    """Step 6: NONE gives 0; pct 0 gives 0 without reading `of_factor` (D-3B4.19); else pct/100 of abs(actual)."""
    if tolerance.source == "NONE":
        return Decimal(0)
    if tolerance.pct == 0:
        return Decimal(0)
    of = actual.values.get(tolerance.of_factor)
    if of is None or of.value is None:
        return None
    return tolerance.pct / 100 * abs(of.value)


def _dec(d: Decimal | None) -> str | None:
    return None if d is None else format(d, "f")


def _pct(d: Decimal | None) -> str | None:
    """`5` and `5.00` (and `0`, `0.00`) are one value in the basis (D-3B4.19)."""
    return None if d is None else format(d.normalize(), "f")


def _floor(f: Floor) -> dict:
    return {"litres": _dec(f.litres), "accuracy_l": _dec(f.accuracy_l), "basis": f.basis}


def basis(o: FactorObservation, structure_key: str, month: str) -> str:
    """Spec §2.2: sha256 hex over the observation's figures; no instant, snapshot id or declaration id. A floor that
    set the band is part of them (D-DD.153), without its revision id."""
    floor = {} if o.floor is None else {"floor": _floor(o.floor)}
    return codec.digest(codec.canonical({
        "structure_key": structure_key, "month": month, "factor_id": o.factor_id, "direction": o.direction,
        "kind": o.kind, "state": o.state, "unit": o.unit, "currency": o.currency, "actual": _dec(o.actual),
        "target": _dec(o.target), "gap": _dec(o.gap), "band": _dec(o.band),
        "tolerance": {"source": o.tolerance.source, "of_factor": o.tolerance.of_factor,
                      "pct": _pct(o.tolerance.pct)},
        "actual_evidence": o.actual_evidence, "target_evidence": o.target_evidence,
        "sources": list(o.sources), "origins": list(o.origins), **floor,
    }))


def also_pinned(structure_key: str, factor_id: str) -> tuple[str, ...]:
    """Spec §3: the `PINS` mechanisms on the same leaf, sorted."""
    return tuple(sorted(p.mechanism for p in _pins.PINS.values()
                        if p.structure_key == structure_key and p.factor_id == factor_id))


def claim(o: FactorObservation, *, structure_key: str, structure_version: int, month: str, snapshot_id: UUID,
          snapshot_as_of: datetime, tolerance_known_at: datetime) -> dict:
    """Spec §4.3 (D-3B4.18): the condition in the leaf's unit; no bridge value and no effect of acting."""
    home = _registry.REGISTRIES[structure_key].row(o.factor_id).home
    t = o.tolerance
    floor = {} if o.floor is None else {"floor": {**_floor(o.floor), "revision_id": o.floor.revision_id}}
    return {
        "format": CLAIM_FORMAT, "structure_key": structure_key, "structure_version": structure_version,
        "factor_id": o.factor_id, "home": None if home is None else home.category,
        "objective": None if home is None else home.objective, "kind": o.kind, "month": month,
        "direction": o.direction, "state": o.state, "unit": o.unit, "currency": o.currency,
        "actual": _dec(o.actual), "target": _dec(o.target), "gap": _dec(o.gap), "band": _dec(o.band),
        "tolerance": {"source": t.source, "of_factor": t.of_factor, "pct": _dec(t.pct),
                      "declaration_id": None if t.declaration_id is None else str(t.declaration_id)},
        "actual_evidence": o.actual_evidence, "target_evidence": o.target_evidence,
        "sources": list(o.sources), "origins": list(o.origins),
        "also_pinned": list(also_pinned(structure_key, o.factor_id)),
        "snapshot_id": str(snapshot_id), "snapshot_as_of": snapshot_as_of.isoformat(),
        "tolerance_known_at": tolerance_known_at.isoformat(), **floor,
    }
