"""SnapshotBuilder (CH-1a §4.2): one builder, one coverage policy, one calendar.

For each subject: period -> inputs -> grade -> value (when covered > 0, AG-4:
calculate anyway) -> money (when a value exists) -> fingerprint. An unchanged
fingerprint writes nothing; a changed one appends ``revision = latest + 1``.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta
from typing import Mapping, Sequence

from . import grading
from .measures import CATALOGUE_VERSION, MEASURES, MeasureAdapter, MeasureSpec, measures_for
from .policy import CoveragePolicy, OperatingCalendar
from .ports import DayCtx, SiteRef, SnapshotKey, SnapshotRow, SnapshotStore


@dataclass(frozen=True)
class Written:
    row: SnapshotRow
    written: bool  # False: unchanged fingerprint, nothing appended


class SnapshotBuilder:
    def __init__(
        self,
        store: SnapshotStore,
        adapters: Mapping[str, MeasureAdapter],
        policy: CoveragePolicy,
        calendar: OperatingCalendar,
        *,
        catalogue_version: int = CATALOGUE_VERSION,
    ) -> None:
        self._store = store
        self._adapters = adapters
        self._policy = policy
        self._calendar = calendar
        self._catalogue_version = catalogue_version

    def build(
        self, tenant_id, site: SiteRef, local_day: date, measure: str, known_at: datetime | None = None
    ) -> list[Written]:
        spec: MeasureSpec = MEASURES[measure]
        adapter = self._adapters[spec.adapter]
        entry = self._calendar.entry_for(site.site_code)
        bounds = grading.period_bounds(entry, site.timezone, local_day, spec.period)
        ctx = DayCtx(
            tenant_id=tenant_id, site_id=site.site_id, site_code=site.site_code, domain=site.site_type,
            tz=site.timezone, local_day=local_day,
            period_start_utc=None if bounds is None else bounds[0],
            period_end_utc=None if bounds is None else bounds[1],
            known_at=known_at,
        )
        out: list[Written] = []
        for subject_ref in adapter.subjects(ctx):
            out.append(self._one(ctx, spec, adapter, subject_ref, bounds))
        return out

    def _one(self, ctx: DayCtx, spec: MeasureSpec, adapter: MeasureAdapter, subject_ref: str,
             bounds: tuple[datetime, datetime] | None) -> Written:
        expected = bounds is not None
        if expected:
            inputs = adapter.inputs(ctx, subject_ref)
            required = int((bounds[1] - bounds[0]).total_seconds())
            covered = grading.covered_seconds(inputs.covered, bounds[0], bounds[1])
            ids, pending = inputs.ids, inputs.pending
        else:
            inputs, required, covered, ids, pending = None, 0, 0, (), False
        grade = grading.classify_day(expected, required, covered, pending, self._policy.bands, spec.threshold)
        value = adapter.measure(ctx, subject_ref, inputs) if (expected and covered > 0) else None
        money = adapter.money(ctx, subject_ref, value) if value is not None else None
        fp = grading.input_fp(ids, pending, self._policy.policy_version, self._calendar.calendar_version,
                              self._catalogue_version, adapter.key)
        key = SnapshotKey(ctx.tenant_id, ctx.site_id, ctx.local_day, spec.subject_kind, subject_ref, spec.key)
        latest = self._store.latest(key)
        row = SnapshotRow(
            tenant_id=ctx.tenant_id, site_id=ctx.site_id, local_day=ctx.local_day,
            subject_kind=spec.subject_kind, subject_ref=subject_ref, measure=spec.key,
            evidence_class=spec.evidence_class, revision=1 if latest is None else latest[0] + 1,
            expected=expected, required_seconds=required, covered_seconds=covered,
            coverage_pct=grading.coverage_pct(required, covered), grade=grade, value=value, money=money,
            policy_version=self._policy.policy_version, calendar_version=self._calendar.calendar_version,
            catalogue_version=self._catalogue_version, input_fp=fp,
        )
        if latest is not None and latest[1] == fp:
            # CH-1a L6: nothing is appended, so the row reports the stored revision
            return Written(replace(row, revision=latest[0]), False)
        self._store.append(row)
        return Written(row, True)

    def build_range(
        self,
        tenant_id,
        site: SiteRef,
        from_day: date,
        to_day: date,
        measures: Sequence[str] | None = None,
        known_at: datetime | None = None,
    ) -> list[Written]:
        keys = [m.key for m in measures_for(site.site_type)]
        if measures is not None:
            keys = [k for k in keys if k in set(measures)]
        out: list[Written] = []
        day = from_day
        while day <= to_day:
            for key in keys:
                out.extend(self.build(tenant_id, site, day, key, known_at))
            day += timedelta(days=1)
        return out
