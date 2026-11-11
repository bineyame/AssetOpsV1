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


@dataclass(frozen=True)
class PeriodKey:
    """ANY-1 AR-1: one stored read period (`site_period_read`, migration 0059) without its revision."""
    tenant_id: UUID
    site_id: UUID
    kind: str
    period_start: datetime


@dataclass(frozen=True)
class PeriodRow:
    """One revision of a stored read period: the fragment today's compose builds for that period (`body`, words as
    `{key, params}` per D-I18N.1), at its native grain, revisioned by input fingerprint (the `site_day_snapshot`
    rules: append-only, `computed_at` for "as known at k")."""
    tenant_id: UUID
    site_id: UUID
    kind: str
    period_start: datetime
    period_end: datetime
    local_day: date
    revision: int
    builder_version: str
    input_fp: str
    state: str
    body: dict[str, Any]
    computed_at: datetime | None = None

    def key(self) -> PeriodKey:
        return PeriodKey(self.tenant_id, self.site_id, self.kind, self.period_start)

    def to_json(self) -> dict[str, Any]:
        return {
            "site_id": str(self.site_id), "kind": self.kind,
            "period_start": self.period_start.isoformat(), "period_end": self.period_end.isoformat(),
            "local_day": self.local_day.isoformat(), "revision": self.revision,
            "builder_version": self.builder_version, "input_fp": self.input_fp, "state": self.state,
            "body": self.body,
            "computed_at": None if self.computed_at is None else self.computed_at.isoformat(),
        }


@dataclass(frozen=True)
class ProvenanceBlock:
    """The provenance of one selected assessment revision (`revision_provenance`): immutable, computed once per
    builder version."""
    tenant_id: UUID
    assessment_revision_id: UUID
    builder_version: str
    block: dict[str, Any]
    computed_at: datetime | None = None


@dataclass(frozen=True)
class PendingEvent:
    """An input event recorded at or before `k` and not consumed by the snapshots consumer by `k` (AR-1
    PENDING-at-k), or a still-queued dirty mark (live reads only)."""
    site_id: UUID
    local_day: date
    kind: str
    source: str  # "event" | "dirty"


class PeriodReadStore(Protocol):
    def latest(self, key: PeriodKey) -> tuple[int, str, str] | None:
        """(revision, input_fp, builder_version) of the latest revision, or None."""

    def append(self, row: PeriodRow) -> None: ...

    def read_latest(
        self,
        tenant_id: UUID,
        site_ids: Sequence[UUID],
        kinds: Sequence[str],
        from_day: date,
        to_day: date,
        known_at: datetime | None,
    ) -> list[PeriodRow]:
        """Latest revision per (Site, kind, period) with `local_day` in the range, in ONE statement."""

    def provenance(self, tenant_id: UUID, revision_ids: Sequence[UUID],
                   builder_version: str) -> dict[UUID, dict[str, Any]]: ...

    def append_provenance(self, block: ProvenanceBlock) -> bool:
        """Insert once; False when that (revision, builder version) is already stored (never overwritten)."""

    def unconsumed_at(self, tenant_id: UUID, site_ids: Sequence[UUID], types: Sequence[str],
                      known_at: datetime | None) -> list[Any]:
        """The `chain.events.Event`s recorded at or before `known_at` (live: now) that the snapshots consumer had
        not consumed by then, from the append-only `event_outbox` and `event_consumption` ledgers."""

    def dirty_marks(self, tenant_id: UUID, site_ids: Sequence[UUID], kinds: Sequence[str],
                    from_day: date, to_day: date) -> list[tuple[UUID, date, str]]:
        """Live only: the `snapshot_dirty` marks of these kinds still queued for a rebuild."""


class ChainInputReader(Protocol):
    """The single read port every measure adapter reads through (implemented in
    ``chain/adapters/postgres_chain_inputs.py``)."""

    def tenant_id(self, slug: str) -> UUID | None: ...

    def site(self, tenant_id: UUID, site_code: str) -> SiteRef | None: ...

    def first_evidence_time(self, tenant_id: UUID, site_id: UUID) -> datetime | None: ...

    def foundation_assets(self, ctx: DayCtx, component_type: str) -> list[str]: ...

    def readings(self, ctx: DayCtx, roles: Sequence[str], lo: datetime, hi: datetime) -> list[dict[str, Any]]: ...

    def productive_assets(self, ctx: DayCtx) -> list[dict[str, Any]]: ...

    def feeder_demand_readings(self, ctx: DayCtx, asset_id: str) -> list[dict[str, Any]]: ...

    def declared_price(self, ctx: DayCtx, assumption_key: str) -> dict[str, Any] | None: ...

    def renewable_hours(self, ctx: DayCtx) -> dict[str, Any]:
        """CH-9: `{"measured", "missing": [(from, to)], "hours": [{"from", "to", "head": {revision_id, result,
        evidence_ids} | None}]}` for the day's `mini_depth.store.daylight_hours` at the cutoff."""
        ...

    def service_hours(self, ctx: DayCtx) -> list[dict[str, Any]]:
        """CH-9 (CH9-R2 Q7): each Site-local clock hour of the period with its stored, selected `mini_service`
        revision at the cutoff: `[{"from", "to", "head": {revision_id, result, evidence_ids} | None}]`."""
        ...

    def dispatch_days(self, ctx: DayCtx) -> list[dict[str, Any]]: ...

    def run_evidence_intervals(self, ctx: DayCtx, run_ids: Sequence[str]) -> list[tuple[str, datetime, datetime]]: ...

    def selected_windows(
        self, ctx: DayCtx, analytic_ids: Sequence[str]
    ) -> list[tuple[datetime, datetime, str]]: ...

    def cold_temperature(self, ctx: DayCtx, lo: datetime, hi: datetime) -> dict[str, Any]: ...

    def cold_backup_chain(self, ctx: DayCtx, lo: datetime, hi: datetime) -> dict[str, Any]: ...

    def ev_window(self, ctx: DayCtx, lo: datetime, hi: datetime) -> dict[str, Any]: ...

    def renewable_pending(self, ctx: DayCtx) -> bool: ...

    def pending_jobs(self, ctx: DayCtx, domains: Sequence[str]) -> bool: ...
