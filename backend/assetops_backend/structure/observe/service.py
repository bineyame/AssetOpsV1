"""3B4 unit 3 (spec §5.1; D-3B4.7, D-3B4.10, D-3B4.11, D-3B4.21, D-3B4.25): the structure observer.

For a closed month's served, current portfolio snapshot, every observed leaf of every Site is observed against its
target (`observe.observe_site`) and each observation is applied to today's Finding store (`structure_apply`, spec
§4.3's table) in one transaction per Site, under the Site-month advisory lock. One Site's failure rolls back that
Site only and propagates after the earlier Sites committed. The basis is the observation's (`observe.basis`), never
the claim's, so a rebuilt snapshot with the same figures writes nothing.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from types import MappingProxyType
from typing import Any, Protocol
from uuid import UUID

from assetops_backend.analytics.assessment_inputs import sha256_json
from assetops_backend.commercial.months import month_bounds
from assetops_backend.structure.check import StructureError
from assetops_backend.structure.observe import observe as _observe
from assetops_backend.structure.observe import rules
from assetops_backend.structure_snapshot.model import SiteMonthSnapshot

REFUSALS = ("NO_SNAPSHOT", "REBUILD_NEEDED", "SNAPSHOT_NOT_CURRENT", "MONTH_OPEN")
NOT_OBSERVED_REASON = "STRUCTURE_NOT_OBSERVED"


class ObserveRefused(Exception):
    """Nothing was written; `code` is one of `REFUSALS`."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class FloorReadPort(Protocol):
    """D-DD.153: the tank's floor in force over the whole `window`, as known at `known_at`; None when there is none."""

    def read(self, tenant_id: UUID, site_id: UUID, window: tuple[datetime, datetime],
             known_at: datetime) -> _observe.Floor | None: ...


@dataclass(frozen=True)
class Written:
    factor_id: str
    transition: str
    finding_id: UUID
    revision_id: UUID


@dataclass(frozen=True)
class SiteResult:
    states: Mapping[str, str]          # factor_id -> state, in `OBSERVED` order
    written: tuple[Written, ...]


@dataclass(frozen=True)
class RunResult:
    month: str
    snapshot_id: UUID
    as_of: datetime
    sites: Mapping[str, SiteResult]                 # by site code, `asked` order
    excluded: Mapping[str, tuple[str, ...]]         # by site code, `asked` order


def tolerance_in_force(rows: tuple[Any, ...], structure_key: str, month: str,
                       known_at: datetime) -> dict[str, _observe.ToleranceInForce]:
    """Spec §4.3 last bullet: per leaf, the latest row with `valid_from <= month` and `recorded_at <= known_at`
    (`rows` in `recorded_at, id` order); `SET` gives a SITE tolerance, `CLEARED` gives none."""
    latest: dict[str, Any] = {}
    for row in rows:
        if row.structure_key == structure_key and row.valid_from <= month and row.recorded_at <= known_at:
            latest[row.factor_id] = row
    return {factor: _observe.ToleranceInForce("SITE", row.of_factor, Decimal(row.pct), row.id)
            for factor, row in latest.items() if row.state == "SET"}


def run_basis(bases: Mapping[str, str]) -> str:
    """Spec §4.2: `sha256_json` of the Site-month's sorted `(factor_id, basis)` pairs."""
    return sha256_json(sorted([factor, b] for factor, b in bases.items()))


class StructureObserver:
    def __init__(self, snapshots: Any, store: Any, findings: Any, assessments: Any,
                 clock: Callable[[], datetime], floors: FloorReadPort | None = None) -> None:
        self._snapshots, self._store, self._findings, self._assessments = snapshots, store, findings, assessments
        self._clock, self._floors = clock, floors

    def run(self, tenant_id: UUID, month: str) -> RunResult:
        served = self._snapshots.portfolio(tenant_id, month)
        if served.state in ("NO_SNAPSHOT", "REBUILD_NEEDED"):
            raise ObserveRefused(served.state)
        if not served.freshness.current:
            raise ObserveRefused("SNAPSHOT_NOT_CURRENT")
        snapshot = served.snapshot
        if not snapshot.closed_at_build or any(not s.closed_at_build for s in snapshot.sites.values()):
            raise ObserveRefused("MONTH_OPEN")
        known_at = self._clock()
        sites: dict[str, SiteResult] = {}
        excluded: dict[str, tuple[str, ...]] = {}
        for code in snapshot.asked:
            site = snapshot.sites.get(code)
            if site is None:
                if code in snapshot.sites_excluded:
                    excluded[code] = tuple(snapshot.sites_excluded[code])
                continue
            if site.actual.structure_key not in rules.OBSERVED:
                excluded[code] = (NOT_OBSERVED_REASON,)
                continue
            sites[code] = self._site(tenant_id, month, site, known_at)
        for code, reasons in snapshot.sites_excluded.items():
            excluded.setdefault(code, tuple(reasons))
        return RunResult(month, snapshot.snapshot_id, snapshot.as_of, MappingProxyType(sites),
                         MappingProxyType(excluded))

    def _floors_in_force(self, tenant_id: UUID, site_id: UUID, window: tuple[datetime, datetime],
                         known_at: datetime) -> dict[str, _observe.Floor]:
        """D-DD.153: the tank's floor on the unexplained litres; no port or no floor is today's relative band."""
        floor = None if self._floors is None else self._floors.read(tenant_id, site_id, window, known_at)
        return {} if floor is None else {"unexplained_l": floor}

    def _site(self, tenant_id: UUID, month: str, site: SiteMonthSnapshot, known_at: datetime) -> SiteResult:
        key, site_id = site.actual.structure_key, site.site.site_id
        declarations = tolerance_in_force(self._findings.tolerances(tenant_id, site_id), key, month, known_at)
        window = month_bounds(month, site.site.timezone)
        observations = _observe.observe_site(site, declarations, self._floors_in_force(tenant_id, site_id, window,
                                                                                       known_at))
        rows = self._store.get(tenant_id, [site.snapshot_id])
        if len(rows) != 1:
            raise StructureError("STRUCTURE_COMPOSE", key, site.site.site_code)
        input_sha = rows[0].payload_sha256   # D-3B4.21: the Site row's digest, never the portfolio's
        bases = {o.factor_id: _observe.basis(o, key, month) for o in observations}
        site_basis = run_basis(bases)
        written: list[Written] = []
        with self._assessments.transaction() as c:
            self._findings.structure_lock(c, site_id, month)
            for o in observations:
                claim = _observe.claim(o, structure_key=key, structure_version=site.actual.structure_version,
                                       month=month, snapshot_id=site.snapshot_id, snapshot_as_of=site.as_of,
                                       tolerance_known_at=known_at)

                def persist(conn, o=o, claim=claim):
                    return self._assessments.structure_persist(
                        conn, tenant_id, site_id, month, window, site_basis, site.as_of, o.factor_id, claim,
                        bases[o.factor_id], known_at)

                applied = self._findings.structure_apply(
                    c, tenant_id, site_id, key, month, window, o, basis=bases[o.factor_id], claim=claim,
                    input_evidence_sha256=input_sha, persist=persist, now=known_at)
                if applied is not None:
                    move, finding_id, revision_id = applied
                    written.append(Written(o.factor_id, move, finding_id, revision_id))
        return SiteResult(MappingProxyType({o.factor_id: o.state for o in observations}), tuple(written))


__all__ = ["NOT_OBSERVED_REASON", "REFUSALS", "ObserveRefused", "RunResult", "SiteResult", "StructureObserver",
           "Written", "run_basis", "tolerance_in_force"]
