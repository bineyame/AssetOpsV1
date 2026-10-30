"""OUT-C U2: maintenance visits over 60 days, and the early-warning facts of one Site (build sheet OUT-C §2 U2).

`maintenance_cases` widens B's 31-day recorded-time read (B-Q22) to three recorded-time windows, because the work
index filters requests by when they were recorded and caps a window at 31 days, while a visit may be recorded up
to 30 days after it occurred (`work/model.py` BACKDATE_LIMIT). The union is then filtered by occurrence (R571).
Incidents keep B's single read. No new port: the composers pass their existing `work` port."""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from assetops_backend.outcomes.outcome_map import finding_signal_key, outcome_roles
from assetops_backend.outcomes.warnings import PlanCue, Visit, WarningFacts
from assetops_backend.site_outcomes.board import MAINTENANCE_REQUEST, CaseFact, SiteFacts

VISIT_LOOKBACK = timedelta(days=60)
RECORD_WINDOW = timedelta(days=31)   # the work index's maximum window (work/site_index.py MAX_WINDOW)
SOON = timedelta(days=14)


def record_windows(to: datetime) -> tuple[tuple[datetime, datetime], ...]:
    """`[to-62 d, to-31 d)`, `[to-31 d, to)`, `[to, to+31 d)` by recorded time."""
    return ((to - 2 * RECORD_WINDOW, to - RECORD_WINDOW), (to - RECORD_WINDOW, to), (to, to + RECORD_WINDOW))


def maintenance_cases(reads: Any, work_port: Callable[..., dict[str, Any]], site_code: str,
                      to: datetime) -> list[CaseFact] | None:
    """Maintenance requests that occurred in `[to-60 d, to)`, deduplicated by case id; None when any read was
    refused (the read is then named `work_index` in `reads.failed`, so the board is PARTIAL)."""
    from assetops_backend.site_outcomes.mini import case_fact  # mini imports this module

    rows: dict[str, dict[str, Any]] = {}
    for lo, hi in record_windows(to):
        page = reads.pages("work_index", work_port, "maintenance", lo, hi)
        if page is None:
            return None
        for r in page:
            rows.setdefault(str(r["case_id"]), r)
    cases = [case_fact(r, MAINTENANCE_REQUEST, site_code) for r in rows.values()]
    return [x for x in cases if x.occurred_at is not None and to - VISIT_LOOKBACK <= x.occurred_at < to]


def _local_date(at: datetime, tz: ZoneInfo | None) -> Any:
    return at.astimezone(tz or timezone.utc).date()


def asset_name(label: str | None) -> str:
    """The text before " · " in a work row's asset label, else the label."""
    return (label or "").split(" · ", 1)[0]


def warning_facts(facts: SiteFacts, *, to: datetime, tz: ZoneInfo | None, suffix: str, lo: datetime,
                  **extras: Any) -> WarningFacts:
    """Visits, calendar plan cues and open Findings from the composed `SiteFacts`; `extras` carries the domain's
    own inputs (`reserve`, `faults`, `connectors_out`, `peak`)."""
    visits = tuple(
        Visit(case_id=c.case_id, code=c.code or "", asset_id=c.asset_id, asset_name=asset_name(c.asset_label),
              state=c.state, occurred_at=c.occurred_at, occurred_on=_local_date(c.occurred_at, tz),
              finding_ids=c.finding_ids, href=c.href)
        for c in facts.cases if c.kind == MAINTENANCE_REQUEST and c.occurred_at is not None)
    plans = tuple(
        PlanCue(plan_id=p.plan_id, code=p.code or "", title=p.title, due_at=p.due_at, due_on=p.next_due_at,
                asset_id=p.asset_id, href=p.href)
        for p in facts.plans if p.trigger_kind == "CALENDAR" and p.due_at is not None and p.next_due_at is not None)
    open_findings: dict[str, tuple[tuple[str, ...], str | None]] = {}
    for f in facts.findings:
        if f.open:
            moves, checked = outcome_roles(finding_signal_key(f.mechanism), facts.domain)
            open_findings[f.finding_id] = (moves + checked, f.href)
    days = (_local_date(lo, tz), _local_date(to - timedelta(microseconds=1), tz))
    return WarningFacts(domain=facts.domain, site_code=facts.site_code, to=to, visits_from=to - VISIT_LOOKBACK,
                        soon_until=to + SOON, window_days=days, date_suffix=suffix, visits=visits, plans=plans,
                        open_findings=open_findings, **extras)
