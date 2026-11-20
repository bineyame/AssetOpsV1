"""3B7a unit 2 (spec §3.2; D-3B7A.2, D-3B7A.6): build a snapshot at one instant, and verify one.

`build` takes `as_of` from its clock once and passes it as `known_at` to every read, so a record arriving during a
build is in every read or in none. The portfolio target is composed on serve (D-3B7A.4); the builder never reads
`TargetRead.portfolio` whole. `verify` rebuilds every payload at the stored `as_of` without writing and names each
part whose canonical JSON differs.
"""
from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from uuid import UUID, uuid4

from assetops_backend.chain.ports import SiteRef
from assetops_backend.commercial.months import PORTFOLIO_ZONE, month_bounds
from assetops_backend.structure.check import StructureError
from assetops_backend.structure.read import NOT_DECLARED, SITE_TYPE_TO_STRUCTURE, StructureRead, evaluate_inputs
from assetops_backend.structure.registry import REGISTRIES
from assetops_backend.structure.targets.lines import BudgetLineReader
from assetops_backend.structure.targets.read import TargetRead
from assetops_backend.structure_snapshot import codec
from assetops_backend.structure_snapshot.kinds import HeldKinds
from assetops_backend.structure_snapshot.model import BUILT_BY, SNAPSHOT_FORMAT, SnapshotRow
from assetops_backend.structure_snapshot.store import StructureSnapshotStore

_MONTH = re.compile(r"[0-9]{4}-(0[1-9]|1[0-2])", re.ASCII)


@dataclass(frozen=True)
class BuildResult:
    as_of: datetime
    portfolio_snapshot_id: UUID
    sites: Mapping[str, UUID]           # MINI_GRID Site code -> its new row id, in `sites` order
    excluded: tuple[str, ...]           # codes of the other types, in order
    rules_digest: str


@dataclass(frozen=True)
class Verification:
    snapshot_id: UUID
    matches: bool
    differences: tuple[str, ...]        # spec §3.2 paths, sorted
    rules_changed: bool                 # the row's rules_digest differs from the running one


def _check_month(month: str) -> str:
    if not isinstance(month, str) or _MONTH.fullmatch(month) is None:
        raise ValueError(f"month {month!r} is not YYYY-MM")
    return month


class SnapshotBuilder:
    def __init__(self, actual: StructureRead, targets: TargetRead, lines: BudgetLineReader,
                 store: StructureSnapshotStore, kinds: HeldKinds, rules: str, clock: Callable[[], datetime],
                 ids: Callable[[], UUID] = uuid4) -> None:
        self._actual = actual
        self._targets = targets
        self._lines = lines  # the reader inside `targets`
        self._store = store
        self._kinds = kinds
        self._rules = rules
        self._clock = clock
        self._ids = ids

    def _site_payload(self, tenant_id: UUID, site: SiteRef, month: str, as_of: datetime):
        inputs = self._actual.site_inputs(site, month, as_of)
        targets = self._targets.site(site, month, as_of)
        actual = evaluate_inputs(inputs)
        return codec.encode_site(tenant_id, site, month, as_of, inputs, actual, targets), targets

    def build(self, tenant_id: UUID, sites: Sequence[SiteRef], month: str, *, built_by: str) -> BuildResult:
        if not isinstance(built_by, str) or BUILT_BY.fullmatch(built_by) is None:
            raise ValueError("BAD_BUILT_BY")
        _check_month(month)
        key = SITE_TYPE_TO_STRUCTURE["MINIGRID"]
        reg = REGISTRIES[key]
        seen: set[object] = set()
        for s in sites:  # TargetRead.portfolio's refusals
            if s.tenant_id != tenant_id or s.site_code in seen or s.site_id in seen:
                raise StructureError("STRUCTURE_COMPOSE", key, s.site_code)
            seen.update((s.site_code, s.site_id))
        as_of = self._clock().astimezone(timezone.utc)

        rows: list[SnapshotRow] = []
        built: dict[str, UUID] = {}
        excluded: dict[str, tuple[str, ...]] = {}
        for site in sites:
            if SITE_TYPE_TO_STRUCTURE.get(site.site_type) != key:
                excluded[site.site_code] = NOT_DECLARED
                continue
            payload, targets = self._site_payload(tenant_id, site, month, as_of)
            row = SnapshotRow(
                id=self._ids(), tenant_id=tenant_id, site_id=site.site_id, period=month, structure_key=key,
                structure_version=reg.version, format=SNAPSHOT_FORMAT, as_of=as_of, built_by=built_by,
                closed_at_build=as_of >= month_bounds(month, site.timezone)[1], rules_digest=self._rules,
                held_kinds=tuple(self._kinds.of(tenant_id, site.site_id, known_at=as_of)),
                stamps=(targets.lines.stamp,), payload=payload, payload_sha256=codec.digest(payload),
                site_snapshot_ids=None)
            rows.append(row)
            built[site.site_code] = row.id

        pl = self._lines.portfolio(tenant_id, month, structure_key=key, known_at=as_of)
        payload = codec.encode_portfolio(tenant_id, month, key, reg.version, as_of, [s.site_code for s in sites],
                                         excluded, pl)
        portfolio = SnapshotRow(
            id=self._ids(), tenant_id=tenant_id, site_id=None, period=month, structure_key=key,
            structure_version=reg.version, format=SNAPSHOT_FORMAT, as_of=as_of, built_by=built_by,
            closed_at_build=as_of >= month_bounds(month, PORTFOLIO_ZONE)[1], rules_digest=self._rules,
            held_kinds=(), stamps=(pl.stamp,), payload=payload, payload_sha256=codec.digest(payload),
            site_snapshot_ids=tuple(r.id for r in rows))
        self._store.put([*rows, portfolio])  # SnapshotExists propagates; nothing is written
        return BuildResult(as_of, portfolio.id, MappingProxyType(built), tuple(excluded), self._rules)

    def verify(self, tenant_id: UUID, snapshot_id: UUID) -> Verification:
        (row,) = self._store.get(tenant_id, [snapshot_id])
        if row.site_id is not None or row.site_snapshot_ids is None:
            raise ValueError("verify takes a portfolio snapshot id")
        stored = codec.payload_of(row)
        differences: list[str] = []
        for site_row in self._store.get(tenant_id, row.site_snapshot_ids):
            site = codec.site_ref(site_row)
            payload, _ = self._site_payload(tenant_id, site, site_row.period, site_row.as_of)
            differences.extend(f"{site.site_code}:{part}" for part in _differing(
                codec.site_parts(site_row.payload), codec.site_parts(payload)))
        pl = self._lines.portfolio(tenant_id, row.period, structure_key=row.structure_key, known_at=row.as_of)
        payload = codec.encode_portfolio(tenant_id, row.period, row.structure_key, row.structure_version, row.as_of,
                                         stored["sites"], {c: tuple(r) for c, r in stored["sites_excluded"].items()},
                                         pl)
        differences.extend(f"portfolio:{part}" for part in _differing(
            codec.portfolio_parts(row.payload), codec.portfolio_parts(payload)))
        return Verification(row.id, not differences, tuple(sorted(differences)), row.rules_digest != self._rules)


def _differing(old: Mapping[str, str], new: Mapping[str, str]) -> list[str]:
    return [part for part in {**old, **new} if old.get(part) != new.get(part)]


__all__ = ["BuildResult", "SnapshotBuilder", "Verification"]
