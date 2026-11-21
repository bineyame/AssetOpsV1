"""5b unit 3 (spec §4.2; D-5B.12, D-5B.13): the bridge read. No route and nothing stored.

Each call pins one instant (the `known_at` given, else its clock once, in UTC) and passes it to every read below it,
so the target (which may read the actual itself, for `AT_ACTUAL` targets) and the actual are taken from one state.
From a snapshot, `5c` calls `site_bridge` and `portfolio_bridge` directly: the same functions.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import datetime, timezone
from uuid import UUID

from assetops_backend.chain.ports import SiteRef
from assetops_backend.structure.attribution.portfolio import PortfolioBridge, portfolio_bridge
from assetops_backend.structure.attribution.site import SiteBridge, site_bridge
from assetops_backend.structure.read import SITE_TYPE_TO_STRUCTURE, StructureRead
from assetops_backend.structure.targets.read import TargetRead


class BridgeRead:
    def __init__(self, actual: StructureRead, targets: TargetRead, clock: Callable[[], datetime]) -> None:
        self._actual = actual
        self._targets = targets
        self._clock = clock

    def _pin(self, known_at: datetime | None) -> datetime:
        """D-5B.13: one instant per call, in UTC."""
        k = known_at if known_at is not None else self._clock()
        if k.tzinfo is None:
            raise ValueError("known_at must carry a time zone")
        return k.astimezone(timezone.utc)

    def site(self, site: SiteRef, month: str, known_at: datetime | None = None) -> SiteBridge:
        k = self._pin(known_at)
        targets = self._targets.site(site, month, k)  # 3B6 (D-3B6.17): its refusal comes before any leaf read
        return site_bridge(self._actual.site_inputs(site, month, k), targets)

    def portfolio(self, tenant_id: UUID, sites: Sequence[SiteRef], month: str,
                  known_at: datetime | None = None) -> PortfolioBridge:
        k = self._pin(known_at)
        pt = self._targets.portfolio(tenant_id, sites, month, k)  # its refusals are this read's
        key = pt.structure.structure_key
        bridges = {s.site_code: site_bridge(self._actual.site_inputs(s, month, k), pt.sites[s.site_code])
                   for s in sites if SITE_TYPE_TO_STRUCTURE.get(s.site_type) == key}
        return portfolio_bridge(bridges, [s.site_code for s in sites], pt.structure.composition.sites_excluded,
                                pt.portfolio_lines, month, key, pt.structure.structure_version)


__all__ = ["BridgeRead"]
