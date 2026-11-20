"""5b unit 2 (spec §3.2; D-5B.1, D-5B.7, D-5B.12): the Site bridge. Pure.

The actual side is the Site's inputs with a missing cost line carried at its budget line (`carry`), folded by the one
evaluator (`evaluate_inputs`); the target side is 5a's. Each root of `BRIDGE_ROOTS` is bridged: the outcome first,
then cash. 5a's `checks` are kept for the screen and never used as a target (D-5B.1).
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType

from assetops_backend.structure import registry as _registry
from assetops_backend.structure.attribution.bridge import BridgeRow, bridge, by_home
from assetops_backend.structure.attribution.carry import carry_at_target
from assetops_backend.structure.attribution.rules import BRIDGE_ROOTS
from assetops_backend.structure.check import StructureError
from assetops_backend.structure.evaluate import SiteStructure
from assetops_backend.structure.read import SiteInputs, evaluate_inputs
from assetops_backend.structure.targets.read import SiteTargets


@dataclass(frozen=True)
class SiteBridge:
    site_code: str
    month: str
    structure_key: str
    structure_version: int
    roots: Mapping[str, BridgeRow]        # BRIDGE_ROOTS order: "contribution", then "collected"
    by_home: Mapping[str, Decimal]        # by_home(roots["contribution"])
    carried: tuple[str, ...]
    not_carried: Mapping[str, str]
    actual: SiteStructure                 # evaluate_inputs(carried.inputs): the actual side the bridge used
    targets: SiteTargets                  # as given; its `checks` are 5a's, never used as a target (D-5B.1)


def site_bridge(inputs: SiteInputs, targets: SiteTargets) -> SiteBridge:
    """Spec §3.2: carry, evaluate, then bridge each root against the target side."""
    ts = targets.structure
    if (inputs.structure_key, inputs.structure_version, inputs.month) != (
            ts.structure_key, ts.structure_version, ts.month):
        raise StructureError("STRUCTURE_COMPOSE", inputs.structure_key, inputs.site_code)
    reg = _registry.REGISTRIES[inputs.structure_key]
    c = carry_at_target(inputs, ts.values)
    actual = evaluate_inputs(c.inputs)
    roots = {root: bridge(reg, actual.values, ts.values, root) for root in BRIDGE_ROOTS[inputs.structure_key]}
    first = BRIDGE_ROOTS[inputs.structure_key][0]
    return SiteBridge(inputs.site_code, inputs.month, inputs.structure_key, inputs.structure_version,
                      MappingProxyType(roots), by_home(roots[first]), c.carried, c.not_carried, actual, targets)


__all__ = ["SiteBridge", "site_bridge"]
