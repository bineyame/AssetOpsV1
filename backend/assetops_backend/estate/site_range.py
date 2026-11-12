"""SR-5a (Architect rev 9 §9.4, D-SR.9/D-SR.11): one mini-grid Site over a date range, `site-range-overview-1`.

`site_range_body(service, tenant_id, site_code, req)` composes the body on ONE estate snapshot from the selectors the
Portfolio itself calls (`select_finding_scope`, `select_action_scope` + `attach_threads`, `select_evidence_scope`,
`select_financial_scope`), with a one-Site admit, so every Site figure equals the Portfolio's for the same range and
cutoff by construction. The per-day list reads the Site's dispatch days through `coverage.dispatch_days` (the AR-3
stored rows when served, the D-ANY.10 absent-run compose otherwise) and names each gap with the D-E5.46 words.

No AR-4 file is edited; this module only imports from them. Nothing here opens a connection: every read runs on the
snapshot `service.read_snapshot` hands `work`.
"""
from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any

from assetops_backend.estate.coverage import DOMAIN_OF_SITE_TYPE, MINI_GRID, PENDING
from assetops_backend.estate.evidence_money import select_evidence_scope
from assetops_backend.estate.financials import ELIGIBLE, money_covered, partial_money, select_financial_scope
from assetops_backend.estate.index import _coverage_site, select_action_scope, select_finding_scope
from assetops_backend.estate.portfolio import (
    COMPLETE, CURRENT_STATUS, EMPTY, HISTORICAL_STATUS, MEMBERS, PARTIAL, PARTIAL_STATUS, PENDING_STATUS, U,
    UNKNOWN_STATUS, VERIFIED_CLAIM, attach_threads, evidence_unit, finding_unit, money_pending, money_units,
    operating_cost_card, progress, public, reduce_units, thread_progress, workflow_label)
from assetops_backend.estate.range_days import (  # noqa: F401 - the state names are this module's wire values
    ANALYSED, GAP_STATES, NO_READINGS, NOT_ANALYSED, NOT_ENOUGH_READINGS, NOT_EXPECTED, READINGS_CONFLICT,
    STATE_OF_REASON, STILL_PROCESSING, range_day_states)
from assetops_backend.estate.scope import EstateRequest, wire_time
from assetops_backend.site_outcomes.mini import CLOSED_LABELS
from assetops_backend.site_overview.read import intersects

SCHEMA = "site-range-overview-1"
FINDINGS, CLEAR = "FINDINGS", "CLEAR"


class RangeOverviewNotApplicable(Exception):
    """The Site is not a mini-grid Site: its Overview already reads the range (route 404)."""


def _dec(value: Any) -> Decimal:
    return Decimal(str(value))


def _sum_lines(lines: list[dict[str, Any]]) -> tuple[dict[str, str] | None, str]:
    """`partial_money`'s rule over a line set: SUMMED in one currency with no shared overlap group."""
    eligible = [x for x in lines if x["eligibility"] == ELIGIBLE and x["amount"] is not None]
    currencies = {x["amount"]["currency"] for x in eligible}
    groups = [x["overlap_group"] for x in eligible if x["overlap_group"] is not None]
    if not eligible:
        return None, "NO_ELIGIBLE_LINES"
    if len(currencies) > 1:
        return None, "CURRENCY_MIXED"
    if len(groups) != len(set(groups)):
        return None, "OVERLAPPING"
    return {"low": str(sum(_dec(x["amount"]["low"]) for x in eligible)),
            "high": str(sum(_dec(x["amount"]["high"]) for x in eligible)),
            "currency": currencies.pop()}, "SUMMED"


def _quantity(lines: list[dict[str, Any]]) -> dict[str, Any] | None:
    """The at-stake quantity of the ELIGIBLE lines; null on mixed units, an overlap group or a missing bound."""
    eligible = [x for x in lines if x["eligibility"] == ELIGIBLE and x["amount"] is not None]
    units = {(x.get("quantity") or {}).get("unit") for x in eligible}
    if not eligible or len(units) != 1 or None in units or any(x["overlap_group"] is not None for x in eligible):
        return None
    bounds = [x["quantity"] for x in eligible]
    if any(b.get("low") is None or b.get("high") is None for b in bounds):
        return None
    return {"low": str(sum(_dec(b["low"]) for b in bounds)), "high": str(sum(_dec(b["high"]) for b in bounds)),
            "unit": units.pop()}


def _status(historical: bool, domain: str, cov: dict, e_domain: str, e_cov: dict, e_rows: list, m_domain: str,
            m_cov: dict, m_lines: list) -> str:
    """`_portfolio`'s status rule over this one Site (count 1); each unit uses its own scope tuple's domain and
    the money unit the Site's own per-site lines, as `_portfolio` does (`portfolio.py:801-818`)."""
    f = finding_unit(domain, cov)
    e = evidence_unit(e_domain, e_cov, e_rows)
    m = list(money_units(m_domain, m_cov, m_lines).values())
    all_g = all(c != U for c in (f, e, *m))
    partial = cov["state"] == e_cov["state"] == m_cov["state"] == PARTIAL
    pending = money_pending(m_cov, m_lines) or any(
        c["state"] == PENDING or c["job_state"] == "PENDING" for c in (cov, e_cov, m_cov))
    states = [reduce_units(1, [x]) for x in (f, e)] + [reduce_units(1, m)]
    if historical:
        return HISTORICAL_STATUS
    if pending:
        return PENDING_STATUS
    if partial and (all_g or partial):
        return PARTIAL_STATUS
    if any(state != COMPLETE for state in states):
        return UNKNOWN_STATUS
    return CURRENT_STATUS


def site_range_body(service: Any, tenant_id: Any, site_code: str, req: EstateRequest) -> dict[str, Any] | None:
    """The `site-range-overview-1` body, or None when the Site is not in the authorized imported set (route 404).
    Raises `RangeOverviewNotApplicable` for a Site that is not a mini-grid Site."""
    admit = lambda code: code == site_code  # noqa: E731 - one-Site admit, the Portfolio's own scope rule

    def work(snap: Any) -> dict[str, Any] | None:
        scope = service._scope(snap, tenant_id, req, admit)
        if not scope["sites"]:
            return None
        site = scope["sites"][0]
        if DOMAIN_OF_SITE_TYPE.get(site["site_type"]) != MINI_GRID:
            raise RangeOverviewNotApplicable(site_code)
        k, sid = scope["k"], str(site["site_id"])
        cutoffs: dict[str, Any] = {}
        f_sites, f_rows = select_finding_scope(snap, tenant_id, req, scope, cutoffs)
        a_sites, a_rows = select_action_scope(snap, tenant_id, req, scope)
        attach_threads(snap, tenant_id, f_rows, a_rows, req, k, cutoffs)
        e_sites, _ = select_evidence_scope(snap, tenant_id, req, scope)
        m_sites, m_lines, applicable, groups, _, _ = select_financial_scope(snap, tenant_id, req, scope)
        _, domain, cov = f_sites[0]
        f_state = reduce_units(1, [finding_unit(domain, cov)])
        _, e_domain, e_cov, e_rows = e_sites[0]
        _, m_domain, m_cov, m_site_lines = m_sites[0]  # the per-site tuple lines `_portfolio` passes on
        site_lines = [x for x in m_lines if x["site_id"] == sid]

        day_rule = range_day_states(snap, tenant_id, site, req, scope, cov)  # D-SR.22, the one day rule
        members = [r for r in f_rows if r["lifecycle"] in MEMBERS]
        cov_days = cov.get("days") or None
        money_read = money_covered(m_cov)
        days_out = []
        for d, rule in day_rule.items():
            row, state = rule["row"], rule["state"]
            lo = datetime.combine(d, time(0), tzinfo=timezone.utc)
            hi = lo + timedelta(days=1)
            count = sum(1 for r in members if intersects(r["_at"], r.get("_episode_end"), lo, hi))
            if state == ANALYSED:
                state = FINDINGS if count > 0 else CLEAR
            gap = state in GAP_STATES or state in (STILL_PROCESSING, NOT_EXPECTED)
            day_lines = [x for x in site_lines if (x.get("window_start") or "")[:10] == d.isoformat()]
            if gap or not money_read:
                amount, money_state = None, "WITHHELD"
            else:
                amount, money_state = _sum_lines(day_lines)
            readings = None if row is None else row.get("accepted_reading_count")
            days_out.append({"day": d.isoformat(), "state": state,
                             "finding_count": None if state in GAP_STATES else count,
                             "money": amount, "money_state": money_state,
                             "accepted_readings": None if state in GAP_STATES else readings})

        prog, _ = progress(a_sites, a_rows, k, {(r["finding_id"], r["finding_revision_id"]) for r in f_rows}, f_rows)
        thread_counts = thread_progress(f_rows)
        if thread_counts is not None:
            prog["verified_resolution_count"] = thread_counts["verified_resolution_count"]
        if service.count_claims is not None:
            counted = service._claims(tenant_id, scope, req)
            prog["verified_resolution_count"] = None if counted is None else counted.claims[VERIFIED_CLAIM].value
        complete_actions = prog["pending_trial_count"] is not None
        pairs = [(r["finding_id"], r["finding_revision_id"]) for r in f_rows]
        awaiting = snap.awaiting_verification(tenant_id, site["site_id"], pairs, k) if pairs else 0

        status = _status(bool(snap.basis_historical), domain, cov, e_domain, e_cov, e_rows, m_domain, m_cov,
                         m_site_lines)
        # D-SR.28: the Portfolio's `finding_known` rule (`portfolio.py:870-872`) for this one Site
        finding_known = f_state in (COMPLETE, EMPTY) or status == PARTIAL_STATUS
        analysed = [x for x in days_out if x["state"] in (FINDINGS, CLEAR)]
        values = [x["accepted_readings"] for x in analysed]
        coverage_entry = _coverage_site(site, cov)
        requested = None if cov_days is None else cov_days["requested"]
        checked = None if cov_days is None else cov_days["checked"]
        return {
            "schema_version": SCHEMA,
            "site": {"site_code": site["site_code"], "site_name": site["site_name"], "site_type": site["site_type"],
                     "timezone": site.get("timezone")},
            "window": {"from": wire_time(req.from_), "to": wire_time(req.to), "known_at": wire_time(k),
                       "basis": "HISTORICAL" if snap.basis_historical else "CURRENT"},
            "status": status,
            "coverage": coverage_entry,
            "money": {"card": public(operating_cost_card(site_lines, applicable, groups)),
                      "partial": partial_money(site, m_cov, m_site_lines),
                      "quantity": _quantity(site_lines)},
            "findings": {"count": len(members) if finding_known else None,
                         "confirmed": sum(1 for r in members if r["lifecycle"] == "SUPPORTED"),
                         "not_confirmed": sum(1 for r in members if r["lifecycle"] == "UNCONFIRMED"),
                         "awaiting_verification": awaiting},
            "actions": {"open": sum(1 for a in a_rows if workflow_label(a) not in CLOSED_LABELS)
                        if complete_actions else None,
                        "awaiting_verification": prog["pending_trial_count"],
                        "verified_resolution_count": prog["verified_resolution_count"]},
            "dispatch": {"days_requested": requested, "days_analysed": checked,
                         "days_with_findings": sum(1 for x in days_out if x["state"] == FINDINGS),
                         "accepted_readings": None if any(v is None for v in values) else sum(values)},
            "days": days_out,
            "links": {"findings": f"/sites/{site['site_code']}/findings",
                      "day": f"/sites/{site['site_code']}?day={{day}}"},
        }

    return service.read_snapshot(work)
