"""3B7a unit 1 (spec §2.2): what the snapshot store keeps and what the served read returns.

`PortfolioMonthSnapshot.actual()` and `.targets()` compose on serve from the frozen Site values (D-3B7A.4): the same
`compose` the fresh reads use, so no stored total can disagree with its parts. Neither reads a record.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from types import MappingProxyType
from uuid import UUID

from assetops_backend.chain.ports import SiteRef
from assetops_backend.commercial.months import MonthStamp
from assetops_backend.structure.evaluate import SiteStructure, compose
from assetops_backend.structure.read import SITE_TYPE_TO_STRUCTURE, PortfolioStructure, SiteInputs
from assetops_backend.structure.registry import REGISTRIES
from assetops_backend.structure.targets.lines import BudgetLines
from assetops_backend.structure.targets.read import PortfolioTargets, SiteTargets

SNAPSHOT_FORMAT = 1
BUILT_BY = re.compile(r"(person:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
                      r"|service:[a-z][a-z0-9._-]{0,63})", re.ASCII)  # fullmatch
#: D-3B7A.11: always this order.
REASONS = ("RECORDS", "MONTH_CLOSED", "RULES", "STRUCTURE_VERSION", "FORMAT")
STATES = ("SERVED", "NO_SNAPSHOT", "REBUILD_NEEDED")


@dataclass(frozen=True)
class SnapshotRow:
    """One per Site-month build, one per portfolio build (D-3B7A.1). Never updated or deleted."""
    id: UUID
    tenant_id: UUID
    site_id: UUID | None                  # None: the portfolio row
    period: str
    structure_key: str
    structure_version: int
    format: int
    as_of: datetime                       # UTC; the build instant and every read's known_at
    built_by: str
    closed_at_build: bool
    rules_digest: str                     # §2.5, the running digest at build (D-3B7A.11)
    held_kinds: tuple[str, ...]           # Site row: sorted kinds held at as_of (D-3B7A.12); portfolio row: ()
    stamps: tuple[MonthStamp, ...]        # Site row: (its site_month stamp,); portfolio row: (portfolio_month stamp,)
    payload: str
    payload_sha256: str
    site_snapshot_ids: tuple[UUID, ...] | None   # portfolio row only: its Site rows, in payload "sites" order


@dataclass(frozen=True)
class SiteMonthSnapshot:
    snapshot_id: UUID
    tenant_id: UUID
    site: SiteRef
    month: str
    as_of: datetime
    built_by: str
    closed_at_build: bool
    stamps: tuple[MonthStamp, ...]
    inputs: SiteInputs
    actual: SiteStructure
    targets: SiteTargets


@dataclass(frozen=True)
class PortfolioMonthSnapshot:
    snapshot_id: UUID
    tenant_id: UUID
    month: str
    as_of: datetime
    built_by: str
    closed_at_build: bool
    stamps: tuple[MonthStamp, ...]                  # its own portfolio stamp only
    asked: tuple[str, ...]                          # every Site code built for, in the order given
    sites_excluded: Mapping[str, tuple[str, ...]]   # a type with no structure: NOT_DECLARED
    sites: Mapping[str, SiteMonthSnapshot]          # the MINI_GRID Sites, in `asked` order
    portfolio_lines: BudgetLines

    def _structure(self, per_site: Mapping[str, SiteStructure]) -> PortfolioStructure:
        key = SITE_TYPE_TO_STRUCTURE["MINIGRID"]
        reg = REGISTRIES[key]
        composition = replace(compose(reg, per_site), sites_excluded=MappingProxyType(dict(self.sites_excluded)))
        return PortfolioStructure(self.month, key, reg.version, composition, self.asked)

    def actual(self) -> PortfolioStructure:
        """The structure's composition over the frozen Sites' actual values (D-3B7A.4), never a screen figure."""
        return self._structure({code: s.actual for code, s in self.sites.items()})

    def targets(self) -> PortfolioTargets:
        """The target side composed over the frozen Sites' targets; the operator-level lines as stored."""
        structure = self._structure({code: s.targets.structure for code, s in self.sites.items()})
        return PortfolioTargets(structure, MappingProxyType({code: s.targets for code, s in self.sites.items()}),
                                self.portfolio_lines)


@dataclass(frozen=True)
class Freshness:
    current: bool                          # reasons == ()
    reasons: tuple[str, ...]               # a subsequence of REASONS
    stale_stamps: tuple[MonthStamp, ...]   # CommercialMonths.stale's answer, input order
    changed_kinds: tuple[str, ...]         # "<site_code>:<kind>", held now xor held at build; asked order, kind sorted
    untracked: tuple[str, ...]             # §2.4


@dataclass(frozen=True)
class Served:
    state: str                             # one of STATES
    snapshot: SiteMonthSnapshot | PortfolioMonthSnapshot | None   # None unless SERVED
    as_of: datetime | None                 # None only for NO_SNAPSHOT
    freshness: Freshness | None            # None only for NO_SNAPSHOT


__all__ = ["BUILT_BY", "REASONS", "SNAPSHOT_FORMAT", "STATES", "Freshness", "PortfolioMonthSnapshot", "Served",
           "SiteMonthSnapshot", "SnapshotRow"]
