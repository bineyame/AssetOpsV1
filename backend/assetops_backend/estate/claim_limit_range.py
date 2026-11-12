"""SR-7b (sequence doc rev 10 §10.3, rev 10a D-SR.24/25): one mini-grid Site's claim limit over a date range.

`claim_limit_range_body(service, tenant_id, site_code, req)` runs on ONE estate snapshot
(`EstatePortfolioService.read_snapshot`, an `EvidenceMoneySnapshot`) with the evidence-money claim-day pattern
(`estate/evidence_money.py` `mini_grid_rows`), unchanged: `dispatch_days` (AR-3 rows or the D-ANY.10 compose) ->
`note_page_days` -> per day `day_revision` -> `snap.claim_limit_on` (the stored AR-4 `evidence.claim` row, else
today's compose, counted by `row_misses`) -> `claim_limit_read.reduce_day`. No day ceiling is invented:
`current_ceiling` is null unless `reduce_day` gives one. A day with no selected window revision is NO_SELECTION and
carries no link (D-SR.25).
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote, urlencode

from assetops_backend.analytics import claim_limit_read as w1
from assetops_backend.estate.coverage import DOMAIN_OF_SITE_TYPE, MINI_GRID, dispatch_days
from assetops_backend.estate.period_rows import day_revision
from assetops_backend.estate.scope import EstateRequest, wire_time

SCHEMA = "site-claim-limit-range-1"
NO_SELECTION = "NO_SELECTION"
INDETERMINATE = (w1.UNKNOWN, w1.CONTRADICTORY)


class ClaimLimitRangeNotApplicable(Exception):
    """The Site is not a mini-grid Site (route 404)."""


def _text(value: Any) -> str | None:
    return None if value is None else str(value)


def day_link(site_code: str, day: str, revision_id: Any) -> str | None:
    """The existing one-day claim-limit section of Site Evidence (`EvidenceClaimLimit.tsx`, `day=&revision=`)."""
    if revision_id is None:
        return None
    return f"/sites/{quote(site_code, safe='')}/evidence?{urlencode({'day': day, 'revision': str(revision_id)})}"


def day_row(site_code: str, day: str, revision_id: Any, projection: dict[str, Any]) -> dict[str, Any]:
    """D-SR.25: the day row is `reduce_day(projection)`, plus the day's window revision and its link."""
    reduced = w1.reduce_day(projection)
    refusal = [dict(r) for r in projection.get("reasons") or ()
               if r["code"] != w1.HISTORICAL_SELECTION_UNAVAILABLE and not projection["available"]]
    reasons = [*reduced["reasons"], *refusal] or [dict(r) for r in projection.get("reasons") or ()]
    return {
        "day": day, "revision_id": _text(revision_id), "available": bool(reduced["available"]),
        "state": NO_SELECTION if revision_id is None else reduced["state"],
        "current_ceiling": reduced["current_ceiling"], "ceiling_statement": reduced["ceiling_statement"],
        "window_assessment_revision_id": _text(reduced["window_assessment_revision_id"]),
        "gap_count": len(reduced["gaps"]) + len(reduced["historical_gaps"]),
        "reasons": reasons, "link": day_link(site_code, day, revision_id)}


def claim_limit_range_body(service: Any, tenant_id: Any, site_code: str, req: EstateRequest,
                           timezone_name: str | None = None) -> dict[str, Any] | None:
    """None when the Site is not in the tenant's imported, admitted set (route 404). `timezone_name` is the
    route's stored `site.timezone` (the estate Site list carries none); it is echoed only."""

    def work(snap: Any) -> dict[str, Any] | None:
        scope = service._scope(snap, tenant_id, req, lambda code: code == site_code)
        if not scope["sites"]:
            return None
        site = scope["sites"][0]
        if DOMAIN_OF_SITE_TYPE.get(site["site_type"]) != MINI_GRID:
            raise ClaimLimitRangeNotApplicable(site_code)
        k, s = scope["k"], site["site_id"]
        days = dispatch_days(snap, tenant_id, s, req.from_, req.to, k)
        note = getattr(snap, "note_page_days", None)
        if note is not None:
            note(tenant_id, s, req.from_, req.to, k, days)
        mode = "historical" if snap.basis_historical else "live"
        rows = []
        for day in days:
            revision = day_revision(day)
            projection = snap.claim_limit_on(tenant_id, s, day["day"], revision, k, mode)
            rows.append(day_row(site["site_code"], day["day"].isoformat(), revision, projection))
        return {
            "schema_version": SCHEMA,
            "site": {"site_code": site["site_code"], "site_name": site.get("site_name"),
                     "timezone": timezone_name},
            "window": {"from": wire_time(req.from_), "to": wire_time(req.to), "known_at": wire_time(k),
                       "basis": "HISTORICAL" if snap.basis_historical else "CURRENT"},
            "days": rows,
            "summary": {"days_with_positive_claim": sum(1 for r in rows if r["current_ceiling"] is not None),
                        "days_indeterminate": sum(1 for r in rows if r["state"] in INDETERMINATE),
                        "days_without_selection": sum(1 for r in rows if r["state"] == NO_SELECTION),
                        "days_requested": len(rows)},
        }

    return service.read_snapshot(work)


__all__ = ["ClaimLimitRangeNotApplicable", "NO_SELECTION", "SCHEMA", "claim_limit_range_body", "day_link", "day_row"]
