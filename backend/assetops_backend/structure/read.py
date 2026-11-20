"""3B3: the structure read, Site and portfolio (spec §4; D-3B3.5, D-3B3.10, D-3B3.13; R10, P10).

A service only: no route and nothing stored (D-3B3.5). Every value comes from leaves on each call, through the
`LeafSource` port, and is folded by `evaluate`. `3B7a` serves it from the snapshot; `3B5` shows it.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime
from types import MappingProxyType
from typing import TYPE_CHECKING
from uuid import UUID

from assetops_backend.chain.ports import SiteRef
from assetops_backend.structure import registry as _registry
from assetops_backend.structure.check import StructureError
from assetops_backend.structure.evaluate import Composition, LeafValue, SiteStructure, compose, evaluate

if TYPE_CHECKING:
    from assetops_backend.structure.sources import LeafSource, StatedSource

#: R10: the Site types with a declared structure. Cold-room and EV Sites need `3B6`.
SITE_TYPE_TO_STRUCTURE: Mapping[str, str] = MappingProxyType({"MINIGRID": "MINI_GRID"})
#: The reason a Site of a type with no structure is left out of a portfolio whole.
NOT_DECLARED = ("STRUCTURE_NOT_DECLARED",)
_MONTH = re.compile(r"[0-9]{4}-(0[1-9]|1[0-2])", re.ASCII)


@dataclass(frozen=True)
class PortfolioStructure:
    month: str
    structure_key: str
    structure_version: int
    composition: Composition
    sites: tuple[str, ...]  # every Site asked for, in the order given


@dataclass(frozen=True)
class SiteCount:
    """D-3B3.13: "k of n sites". n is every Site asked for; `out` names those not in k, in the order asked."""
    k: int
    n: int
    out: tuple[tuple[str, tuple[str, ...]], ...]


def site_count(portfolio: PortfolioStructure, factor_id: str) -> SiteCount | None:
    """The factor's k of n over the Sites the portfolio was asked for; None when the factor is not composed."""
    value = portfolio.composition.values.get(factor_id)
    if value is None:
        return None
    out = []
    for code in portfolio.sites:
        if code in value.included:
            continue
        if code in value.excluded:
            reasons = value.excluded[code]
        else:
            reasons = portfolio.composition.sites_excluded.get(code) or NOT_DECLARED
        out.append((code, tuple(reasons)))
    return SiteCount(len(value.included), len(portfolio.sites), tuple(out))


def _month(month: str) -> str:
    if not isinstance(month, str) or _MONTH.fullmatch(month) is None:
        raise ValueError(f"month {month!r} is not YYYY-MM")
    return month


@dataclass(frozen=True)
class SiteInputs:
    """3B7a unit 0 (D-3B7A.10): what one Site-month read gave, before evaluation."""
    site_code: str
    month: str
    structure_key: str
    structure_version: int
    leaves: Mapping[str, LeafValue]  # every leaf of the registry, in registry order
    stated: Mapping[str, LeafValue]  # every stated_by row in registry order; empty when no StatedSource is wired


def evaluate_inputs(inputs: SiteInputs) -> SiteStructure:
    """Fold `inputs` by the registry of its key; a version that is not the registry's is STRUCTURE_COMPOSE."""
    reg = _registry.REGISTRIES[inputs.structure_key]
    if reg.version != inputs.structure_version:
        raise StructureError("STRUCTURE_COMPOSE", inputs.structure_key, inputs.site_code)
    return SiteStructure(inputs.site_code, inputs.month, reg.structure_key, reg.version,
                         evaluate(reg, inputs.leaves, inputs.stated))


class StructureRead:
    def __init__(self, sources: "LeafSource", stated: "StatedSource | None" = None) -> None:
        self._sources = sources
        self._stated = stated  # 4b1 (spec §2.5): None reads every node from its expression, as 3B3

    def site_inputs(self, site: SiteRef, month: str, known_at: datetime | None = None) -> "SiteInputs":
        """3B7a unit 0: the Site's leaves (and stated rows) read through the ports, before any evaluation."""
        from assetops_backend.structure.sources import ReadContext

        key = SITE_TYPE_TO_STRUCTURE.get(site.site_type)
        if key is None:
            raise StructureError(NOT_DECLARED[0], str(site.site_type), site.site_code)
        reg = _registry.REGISTRIES[key]
        ctx = ReadContext(site, _month(month), known_at)
        leaves = {row.factor_id: self._sources.leaf(ctx, row.factor_id) for row in reg.rows if row.is_leaf}
        stated = {} if self._stated is None else {row.factor_id: self._stated.stated(ctx, row.factor_id)
                                                  for row in reg.rows if row.stated_by is not None}
        return SiteInputs(site.site_code, month, reg.structure_key, reg.version,
                          MappingProxyType(leaves), MappingProxyType(stated))

    def site(self, site: SiteRef, month: str, known_at: datetime | None = None) -> SiteStructure:
        """Every leaf of the Site's structure read through the port, then evaluated (spec §4)."""
        return evaluate_inputs(self.site_inputs(site, month, known_at))

    def portfolio(self, tenant_id: UUID, sites: Sequence[SiteRef], month: str,
                  known_at: datetime | None = None) -> PortfolioStructure:
        """The MINI_GRID Sites composed factor by factor; any other type left out whole (R10, P10)."""
        _month(month)
        key = SITE_TYPE_TO_STRUCTURE["MINIGRID"]
        reg = _registry.REGISTRIES[key]
        seen: set[object] = set()
        for site in sites:
            if site.tenant_id != tenant_id or site.site_code in seen or site.site_id in seen:
                raise StructureError("STRUCTURE_COMPOSE", key, site.site_code)
            seen.update((site.site_code, site.site_id))
        per_site = {s.site_code: self.site(s, month, known_at) for s in sites
                    if SITE_TYPE_TO_STRUCTURE.get(s.site_type) == key}
        excluded = MappingProxyType({s.site_code: NOT_DECLARED for s in sites
                                     if SITE_TYPE_TO_STRUCTURE.get(s.site_type) is None})
        composition = replace(compose(reg, per_site), sites_excluded=excluded)
        return PortfolioStructure(month, reg.structure_key, reg.version, composition,
                                  tuple(s.site_code for s in sites))


__all__ = ["NOT_DECLARED", "SITE_TYPE_TO_STRUCTURE", "PortfolioStructure", "SiteCount", "SiteInputs", "StructureRead",
           "evaluate_inputs", "site_count"]
