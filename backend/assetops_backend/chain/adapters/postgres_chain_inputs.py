"""PostgreSQL chain input reader (CH-1a §3): the one read port every measure adapter reads through.

SELECT only (guard rule 8, a registered ``$pgReaders`` entry). It reads its own small SELECTs (Site, tenant,
Foundation assets, accepted readings, stored selections, live jobs) and delegates to the existing read services,
which ``chain/composition.py`` builds through their own domains' composition functions and injects here:

- ``mini``: ``mini_depth.read.MiniDepthRead`` (productive users and readings);
- ``assumptions``: ``financials`` ``AssumptionReadService`` (declared prices, the ``covers`` rule);
- ``dispatch``: ``analytics`` ``DispatchReadService`` (the S3 UTC-day window);
- ``cold``: ``analytics`` ``ColdReadService`` (temperature gaps, backup chains, per stored window);
- ``ev_reads`` / ``ev_site``: ``analytics`` ``EvReadService`` and ``EvSiteReads`` (per stored window).

Cold and EV assessments are selected per exact stored window, so the cold and EV calls are made once per
selected window overlapping the local period (``selected_windows``).
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from assetops_backend.analytics.ev_availability import UNKNOWN as EV_UNKNOWN
from assetops_backend.analytics.ev_availability import availability_on
from assetops_backend.chain.ports import DayCtx, SiteRef

_LIVE = ("PENDING", "LEASED")

_ACCEPTED = (
    "SELECT e.id, e.role, e.asset_id, e.source_time, e.interval_start, e.interval_end, e.quality, "
    "e.normalized_value_text, e.normalized_unit FROM accepted_evidence e JOIN ingestion_disposition d "
    "ON d.batch_id = e.batch_id AND d.ordinal = e.ordinal "
    "WHERE e.tenant_id = :t AND e.site_id = :s AND d.decision = 'ACCEPTED' AND d.accepted_evidence_id = e.id "
    "AND e.received_at <= :k AND d.decided_at <= :k AND e.role = ANY(:roles) "
    "AND COALESCE(e.interval_end, e.source_time) >= :lo AND COALESCE(e.interval_start, e.source_time) < :hi "
    "ORDER BY e.source_time, e.id")

_RENEWABLE_HEAD = (
    "SELECT r.id, r.result, COALESCE((SELECT array_agg(v.evidence_id::text ORDER BY v.evidence_id::text) "
    "FROM mini_depth_revision_evidence v WHERE v.tenant_id = r.tenant_id AND v.site_id = r.site_id "
    "AND v.revision_id = r.id), '{}') "
    "FROM mini_depth_selection s JOIN mini_depth_revision r "
    "ON r.tenant_id = s.tenant_id AND r.site_id = s.site_id AND r.id = s.revision_id "
    "WHERE s.tenant_id = :t AND s.site_id = :s AND s.domain = 'renewable' AND s.window_start = :lo "
    "AND s.window_end = :hi AND s.selected_at <= :k AND r.knowledge_cutoff <= :k "
    "ORDER BY s.selected_at DESC, s.seq DESC LIMIT 1")

_RUN_EVIDENCE = (
    "SELECT e.id, e.interval_start, e.interval_end FROM analytic_run_evidence x JOIN accepted_evidence e "
    "ON e.id = x.evidence_id WHERE x.tenant_id = :t AND x.site_id = :s AND x.run_id = ANY(CAST(:runs AS uuid[])) "
    "AND e.interval_start IS NOT NULL AND e.interval_end IS NOT NULL ORDER BY e.interval_start, e.id")

_WINDOWS = (
    "SELECT sel.window_start, sel.window_end, max(sel.seq), (array_agg(sel.run_id ORDER BY sel.seq DESC))[1] FROM analytic_run_selection sel JOIN analytic_run r "
    "ON r.id = sel.run_id WHERE sel.tenant_id = :t AND sel.site_id = :s AND sel.analytic_id = ANY(:a) "
    "AND sel.window_start < :hi AND sel.window_end > :lo AND r.knowledge_cutoff <= :k AND sel.selected_at <= :k "
    "GROUP BY sel.window_start, sel.window_end ORDER BY sel.window_start, sel.window_end")

#: CH-1b residual 2: a live job visible at the cutoff that no later selection of its window (visible at the cutoff)
#: has cleared, as `_RENEWABLE_JOBS` does for the mini-depth hour.
_JOBS = (
    "SELECT EXISTS (SELECT 1 FROM recompute_job j WHERE j.tenant_id = :t AND j.site_id = :s AND j.domain = ANY(:d) "
    "AND j.status = ANY(:st) AND j.window_start < :hi AND j.window_end > :lo AND j.available_at <= :k "
    "AND NOT EXISTS (SELECT 1 FROM analytic_run_selection x WHERE x.tenant_id = j.tenant_id "
    "AND x.site_id = j.site_id AND x.window_start = j.window_start AND x.window_end = j.window_end "
    "AND x.selected_at > j.available_at AND x.selected_at <= :k))")


#: `mini_depth/read.py` `_JOBS`: a live job no later selection of its hour (visible at the cutoff) has cleared.
_RENEWABLE_JOBS = (
    "SELECT EXISTS (SELECT 1 FROM recompute_job j WHERE j.tenant_id = :t AND j.site_id = :s "
    "AND j.domain = 'mini_renewable' AND j.window_start < :hi AND j.window_end > :lo "
    "AND j.status IN ('PENDING', 'LEASED') AND j.available_at <= :k AND NOT EXISTS (SELECT 1 "
    "FROM mini_depth_selection x WHERE x.tenant_id = j.tenant_id AND x.site_id = j.site_id "
    "AND x.domain = 'renewable' AND x.window_start = j.window_start AND x.window_end = j.window_end "
    "AND x.selected_at > j.available_at AND x.selected_at <= :k))")


def instant(value: Any) -> datetime | None:
    """A stored or serialised instant as an aware datetime (ISO ``Z`` accepted); None stays None."""
    if value is None or isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def latest_disjoint(windows: Sequence[tuple]) -> list[tuple]:
    """Overlapping stored windows (re-selections of one run with a different end) count once: within each
    cluster of overlapping windows the one with the latest selection seq is kept, so no energy or money is
    summed twice."""
    clusters: list[list[tuple[datetime, datetime, int]]] = []
    for w in sorted(windows):
        if clusters and w[0] < max(x[1] for x in clusters[-1]):
            clusters[-1].append(w)
        else:
            clusters.append([w])
    return [(lambda w: (w[0], w[1], *w[3:]))(max(cl, key=lambda x: x[2])) for cl in clusters]


class PostgresChainInputs:
    def __init__(self, database_url: str | None = None, *, engine: Engine | None = None, mini: Any = None,
                 assumptions: Any = None, dispatch: Any = None, cold: Any = None, ev_reads: Any = None,
                 ev_site: Any = None) -> None:
        if engine is None and not database_url:
            raise RuntimeError("DATABASE_URL is not set, so the chain inputs cannot be read.")
        self._engine = engine or create_engine(database_url, pool_pre_ping=True)
        self._owns_engine = engine is None
        self.mini, self.assumptions, self.dispatch = mini, assumptions, dispatch
        self.cold, self.ev_reads, self.ev_site = cold, ev_reads, ev_site

    def dispose(self) -> None:
        for svc in (self.mini, self.cold, self.ev_reads):
            if svc is not None and hasattr(svc, "dispose"):
                svc.dispose()
        if self._owns_engine:
            self._engine.dispose()

    def _one(self, sql: str, params: dict[str, Any]) -> Any:
        with self._engine.connect() as c:
            return c.execute(text(sql), params).first()

    def _all(self, sql: str, params: dict[str, Any]) -> list[Any]:
        with self._engine.connect() as c:
            return list(c.execute(text(sql), params).all())

    @staticmethod
    def _subject_instant(ctx: DayCtx) -> datetime:
        """CH-1a L2: the instant subjects are resolved at; the period start, else the Site-local day start (a
        NOT_EXPECTED day still writes one row per subject)."""
        if ctx.period_start_utc is not None:
            return ctx.period_start_utc
        from zoneinfo import ZoneInfo

        local = datetime(ctx.local_day.year, ctx.local_day.month, ctx.local_day.day, tzinfo=ZoneInfo(ctx.tz))
        return local.astimezone(timezone.utc)

    def _known(self, ctx: DayCtx) -> datetime:
        if ctx.known_at is not None:
            return ctx.known_at
        return datetime.now(timezone.utc)

    # --- identity ----------------------------------------------------------------------------------------

    def tenant_id(self, slug: str) -> UUID | None:
        r = self._one("SELECT id FROM tenant WHERE slug = :slug", {"slug": slug})
        return None if r is None else r[0]

    def site(self, tenant_id: UUID, site_code: str) -> SiteRef | None:
        r = self._one("SELECT id, site_code, site_type, timezone FROM site WHERE tenant_id = :t "
                      "AND site_code_key = lower(:code)", {"t": tenant_id, "code": site_code})
        return None if r is None else SiteRef(tenant_id, r[0], r[1], r[2], r[3])

    def first_evidence_time(self, tenant_id: UUID, site_id: UUID) -> datetime | None:
        r = self._one("SELECT min(source_time) FROM accepted_evidence WHERE tenant_id = :t AND site_id = :s",
                      {"t": tenant_id, "s": site_id})
        return None if r is None else r[0]

    def foundation_assets(self, ctx: DayCtx, component_type: str) -> list[str]:
        """Asset ids (lowercase text) of the Foundation components of `component_type` in the revision(s) in
        force at the period start (else the local day start, CH-1a L2) and recorded by the cutoff; sorted."""
        p = {"t": ctx.tenant_id, "s": ctx.site_id, "k": self._known(ctx), "at": self._subject_instant(ctx)}
        rows = self._all(
            "SELECT content FROM foundation_revision WHERE tenant_id = :t AND site_id = :s "
            "AND recorded_at <= :k AND (superseded_at IS NULL OR superseded_at > :k) "
            "AND valid_from <= :at AND (valid_to IS NULL OR valid_to > :at)", p)
        codes = set()
        for (content,) in rows:
            content = content if isinstance(content, dict) else json.loads(content)
            codes |= {x.get("component_id") for x in content.get("components") or ()
                      if x.get("component_type") == component_type}
        if not codes:
            return []
        ids = self._all("SELECT asset_code, id FROM asset WHERE tenant_id = :t AND site_id = :s", p)
        return sorted(str(i).lower() for code, i in ids if code in codes)

    # --- readings ----------------------------------------------------------------------------------------

    def readings(self, ctx: DayCtx, roles: Sequence[str], lo: datetime, hi: datetime) -> list[dict[str, Any]]:
        """Accepted, cutoff-visible readings of `roles` touching `[lo, hi)`."""
        rows = self._all(_ACCEPTED, {"t": ctx.tenant_id, "s": ctx.site_id, "k": self._known(ctx), "lo": lo,
                                     "hi": hi, "roles": list(roles)})
        return [{"evidence_id": str(r[0]).lower(), "role": r[1], "asset_id": None if r[2] is None else str(r[2]),
                 "source_time": r[3], "interval_start": r[4], "interval_end": r[5], "quality": r[6],
                 "value": r[7], "unit": r[8]} for r in rows]

    def productive_assets(self, ctx: DayCtx) -> list[dict[str, Any]]:
        try:
            return self.mini.productive_users(tenant_id=ctx.tenant_id, site_id=ctx.site_id,
                                               at=self._subject_instant(ctx), known_at=ctx.known_at)
        except RuntimeError:  # MiniReadUnavailable: no single Foundation revision covers the instant
            return []

    def feeder_demand_readings(self, ctx: DayCtx, asset_id: str) -> list[dict[str, Any]]:
        return self.mini.productive_readings(tenant_id=ctx.tenant_id, site_id=ctx.site_id,
                                             asset_ids=[UUID(asset_id)], lo=ctx.period_start_utc,
                                             hi=ctx.period_end_utc, known_at=ctx.known_at)

    def declared_price(self, ctx: DayCtx, assumption_key: str) -> dict[str, Any] | None:
        """The stored price selection valid at the period start (``AssumptionReadService.series``)."""
        series = self.assumptions.series(ctx.tenant_id, ctx.site_id, assumption_key,
                                         valid_at=ctx.period_start_utc, recorded_at=ctx.known_at)
        return (series or {}).get("selection")

    # --- mini renewable / dispatch -----------------------------------------------------------------------

    def renewable_hour(self, ctx: DayCtx) -> dict[str, Any] | None:
        """The stored, selected renewable revision for the exact noon hour (no recomputation)."""
        r = self._one(_RENEWABLE_HEAD, {"t": ctx.tenant_id, "s": ctx.site_id, "lo": ctx.period_start_utc,
                                        "hi": ctx.period_end_utc, "k": self._known(ctx)})
        if r is None:
            return None
        result = r[1] if isinstance(r[1], dict) else json.loads(r[1])
        return {"revision_id": str(r[0]).lower(), "result": result, "evidence_ids": [str(x) for x in r[2]]}

    def dispatch_days(self, ctx: DayCtx) -> list[dict[str, Any]]:
        """The S3 dispatch window of every UTC day overlapping the local period (ruling Q3d)."""
        lo, hi = ctx.period_start_utc, ctx.period_end_utc
        out, day = [], lo.astimezone(timezone.utc).date()
        last = (hi - timedelta(microseconds=1)).astimezone(timezone.utc).date()
        while day <= last:
            out.append(self.dispatch.window(ctx.tenant_id, ctx.site_id, day))
            day += timedelta(days=1)
        return out

    def run_evidence_intervals(self, ctx: DayCtx, run_ids: Sequence[str]) -> list[tuple[str, datetime, datetime]]:
        """The accepted interval readings the given analytic runs used (``analytic_run_evidence``)."""
        if not run_ids:
            return []
        rows = self._all(_RUN_EVIDENCE, {"t": ctx.tenant_id, "s": ctx.site_id, "runs": [str(r) for r in run_ids]})
        return [(str(r[0]).lower(), r[1], r[2]) for r in rows]

    # --- cold / EV (per stored selected window) ----------------------------------------------------------

    def selected_windows(self, ctx: DayCtx, analytic_ids: Sequence[str]) -> list[tuple[datetime, datetime, str]]:
        rows = self._all(_WINDOWS, {"t": ctx.tenant_id, "s": ctx.site_id, "a": list(analytic_ids),
                                    "lo": ctx.period_start_utc, "hi": ctx.period_end_utc, "k": self._known(ctx)})
        return latest_disjoint([(r[0], r[1], int(r[2]), str(r[3]).lower()) for r in rows])

    def cold_temperature(self, ctx: DayCtx, lo: datetime, hi: datetime) -> dict[str, Any]:
        return self.cold.temperature(ctx.tenant_id, ctx.site_id, ctx.site_code, lo, hi, ctx.known_at)

    def cold_backup_chain(self, ctx: DayCtx, lo: datetime, hi: datetime) -> dict[str, Any]:
        return self.cold.backup_chain(ctx.tenant_id, ctx.site_id, ctx.site_code, lo, hi, ctx.known_at)

    def ev_window(self, ctx: DayCtx, lo: datetime, hi: datetime) -> dict[str, Any]:
        """One stored EV window on one snapshot: the accepted SUPPORT connector-meter intervals, the reported
        connector-status spans with a known state (``ev_availability``, ruling Q1), the energy, the session
        denominator and the selected consequence."""
        site, reads = self.ev_site, self.ev_reads

        def work(c):
            ev_ctx = site.context_on(c, ctx.tenant_id, ctx.site_id, ctx.site_code, lo, hi, ctx.known_at)
            snap = ev_ctx["snap"]
            accepted = reads.accepted_on(c, snap)
            meter = [(r["interval_start"], r["interval_end"]) for r in accepted
                     if r["role"] == "ev_connector_energy" and r["use"] == "SUPPORT"
                     and r["interval_start"] is not None and r["interval_end"] is not None]
            availability = availability_on(reads, c, snap)
            status = [(instant(x["from"]), instant(x["to"])) for row in availability["connectors"]
                      for x in row["spans"] if x["state"] != EV_UNKNOWN]
            energy, _ = site.energy_on(ev_ctx)
            _, denominator = reads.status_on(snap)
            money = site.consequence_on(ev_ctx)
            ids = sorted({str(r["evidence_id"]).lower() for r in accepted})
            return {"selected": snap["selected"] is not None, "meter": meter, "status": status, "energy": energy,
                    "denominator": denominator, "money": money, "evidence_ids": ids}

        return reads.within(work)

    # --- currentness -------------------------------------------------------------------------------------

    def renewable_pending(self, ctx: DayCtx) -> bool:
        """The mini-depth reader's own live-job rule for the noon hour (a job cleared by a later selection is
        not pending)."""
        r = self._one(_RENEWABLE_JOBS, {"t": ctx.tenant_id, "s": ctx.site_id, "lo": ctx.period_start_utc,
                                        "hi": ctx.period_end_utc, "k": self._known(ctx)})
        return bool(r and r[0])

    def pending_jobs(self, ctx: DayCtx, domains: Sequence[str]) -> bool:
        r = self._one(_JOBS, {"t": ctx.tenant_id, "s": ctx.site_id, "d": list(domains), "st": list(_LIVE),
                              "lo": ctx.period_start_utc, "hi": ctx.period_end_utc, "k": self._known(ctx)})
        return bool(r and r[0])


__all__ = ["PostgresChainInputs", "instant"]
