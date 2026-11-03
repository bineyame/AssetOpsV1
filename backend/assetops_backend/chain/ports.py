"""Ports of the day-snapshot chain (CH-1a): records crossing the adapter seam.

No driver imports here: the snapshot store and the chain input reader are
implemented in ``chain/adapters`` and wired in ``chain/composition.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Protocol, Sequence
from uuid import UUID


@dataclass(frozen=True)
class SiteRef:
    tenant_id: UUID
    site_id: UUID
    site_code: str
    site_type: str  # MINIGRID | COLDCHAIN | EV_CHARGING
    timezone: str


@dataclass(frozen=True)
class DayCtx:
    tenant_id: UUID
    site_id: UUID
    site_code: str
    domain: str
    tz: str
    local_day: date
    period_start_utc: datetime | None
    period_end_utc: datetime | None
    known_at: datetime | None


@dataclass(frozen=True)
class InputSet:
    ids: tuple[str, ...] = ()
    covered: list[tuple[datetime, datetime]] = field(default_factory=list)
    pending: bool = False
    # Adapter-private carry from inputs() to measure(); never stored, never fingerprinted.
    payload: Any = None


@dataclass(frozen=True)
class SnapshotKey:
    tenant_id: UUID
    site_id: UUID
    local_day: date
    subject_kind: str
    subject_ref: str
    measure: str


@dataclass(frozen=True)
class SnapshotRow:
    tenant_id: UUID
    site_id: UUID
    local_day: date
    subject_kind: str
    subject_ref: str
    measure: str
    evidence_class: str
    revision: int
    expected: bool
    required_seconds: int
    covered_seconds: int
    coverage_pct: str
    grade: str
    value: dict[str, Any] | None
    money: dict[str, Any] | None
    policy_version: str
    calendar_version: str
    catalogue_version: int
    input_fp: str
    computed_at: datetime | None = None

    def key(self) -> SnapshotKey:
        return SnapshotKey(self.tenant_id, self.site_id, self.local_day, self.subject_kind,
                           self.subject_ref, self.measure)

    def to_json(self) -> dict[str, Any]:
        return {
            "site_id": str(self.site_id),
            "local_day": self.local_day.isoformat(),
            "subject_kind": self.subject_kind,
            "subject_ref": self.subject_ref,
            "measure": self.measure,
            "evidence_class": self.evidence_class,
            "revision": self.revision,
            "expected": self.expected,
            "required_seconds": self.required_seconds,
            "covered_seconds": self.covered_seconds,
            "coverage_pct": self.coverage_pct,
            "grade": self.grade,
            "value": self.value,
            "money": self.money,
            "policy_version": self.policy_version,
            "calendar_version": self.calendar_version,
            "catalogue_version": self.catalogue_version,
            "input_fp": self.input_fp,
            "computed_at": None if self.computed_at is None else self.computed_at.isoformat(),
        }


class SnapshotStore(Protocol):
    def latest(self, key: SnapshotKey) -> tuple[int, str] | None:
        """(revision, input_fp) of the latest revision, or None."""

    def append(self, row: SnapshotRow) -> None: ...

    def read_latest(
        self,
        tenant_id: UUID,
        site_ids: Sequence[UUID],
        from_day: date,
        to_day: date,
        measures: Sequence[str] | None,
        known_at: datetime | None,
    ) -> list[SnapshotRow]:
        """Latest revision per (site, day, subject, measure), in ONE statement."""


class ChainInputReader(Protocol):
    """The single read port every measure adapter reads through (implemented in
    ``chain/adapters/postgres_chain_inputs.py``)."""

    def tenant_id(self, slug: str) -> UUID | None: ...

    def site(self, tenant_id: UUID, site_code: str) -> SiteRef | None: ...

    def first_evidence_time(self, tenant_id: UUID, site_id: UUID) -> datetime | None: ...

    def productive_assets(self, ctx: DayCtx) -> list[dict[str, Any]]: ...

    def feeder_demand_readings(self, ctx: DayCtx, asset_id: str) -> list[dict[str, Any]]: ...

    def declared_price(self, ctx: DayCtx, assumption_key: str) -> dict[str, Any] | None: ...

    def renewable_hour(self, ctx: DayCtx) -> dict[str, Any] | None: ...

    def dispatch_day(self, ctx: DayCtx) -> dict[str, Any] | None: ...

    def cold_windows(self, ctx: DayCtx) -> list[dict[str, Any]]: ...

    def ev_sessions(self, ctx: DayCtx) -> list[dict[str, Any]]: ...

    def pending_jobs(self, ctx: DayCtx, domains: Sequence[str]) -> bool: ...
