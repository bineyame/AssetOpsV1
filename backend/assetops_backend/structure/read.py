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
from assetops_backend.structure.evaluate import Composition, SiteStructure, compose, evaluate

if TYPE_CHECKING:
    from assetops_backend.structure.sources import LeafSource

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


def _month(month: str) -> str:
    if not isinstance(month, str) or _MONTH.fullmatch(month) is None:
        raise ValueError(f"month {month!r} is not YYYY-MM")
    return month


class StructureRead:
    def __init__(self, sources: "LeafSource") -> None:
        self._sources = sources

    def site(self, site: SiteRef, month: str, known_at: datetime | None = None) -> SiteStructure:
        """Every leaf of the Site's structure read through the port, then evaluated (spec §4)."""
        from assetops_backend.structure.sources import ReadContext

        key = SITE_TYPE_TO_STRUCTURE.get(site.site_type)
        if key is None:
            raise StructureError(NOT_DECLARED[0], str(site.site_type), site.site_code)
        reg = _registry.REGISTRIES[key]
        ctx = ReadContext(site, _month(month), known_at)
        leaves = {row.factor_id: self._sources.leaf(ctx, row.factor_id) for row in reg.rows if row.is_leaf}
        return SiteStructure(site.site_code, month, reg.structure_key, reg.version, evaluate(reg, leaves))

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


__all__ = ["NOT_DECLARED", "SITE_TYPE_TO_STRUCTURE", "PortfolioStructure", "StructureRead"]
