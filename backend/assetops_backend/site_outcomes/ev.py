"""OUT-B3: the EV charging composer. It reads the injected EV ports and builds the board's `SiteFacts`.

Sources and rules: build spec §B.4 "EV (Depot)", rulings B-Q7/Q14/Q17/Q18/Q21/Q26 and addenda 2-3. Every port is an
existing service bound by B4. Session counts come from the overview `denominator` (addendum 3 c); `needs_attention`
is never a count source. Closed Findings linked by a case or a domain Action are resolved through the single
`finding(...)` read (addendum 3 d). The Finding source (list and single reads) is a status producer (addendum 3 M1).
Dates use the route Site record's zone, else UTC with the suffix (addendum 3 b)."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from assetops_backend.analytics.ev import MECHANISM as EV_MECHANISM
from assetops_backend.outcomes.catalogue import EV
from assetops_backend.site_outcomes.board import (
    DECLARED, INCIDENT, MAINTENANCE_REQUEST, CaseFact, Contributor, FindingFact, Option, SiteFacts,
    finding_moved_outcomes, readiness_confidence, unresolved_links)
from assetops_backend.site_outcomes.cold import SETTLED_CURRENTNESS, domain_action
from assetops_backend.site_outcomes.mini import (
    NOT_LOADED, UTC_SUFFIX, WORK_WINDOW, MiniComposition as Composition, Reads, case_fact, day_month, num, plan_fact,
    plural, site_zone, utc)

GROW, COST, PROTECT, ASSURE = "GROW_REVENUE", "OPTIMIZE_COST", "PROTECT_ASSET", "ASSURE_PERFORMANCE"

NO_SESSION_ASSESSMENT = "Not available yet · no session assessment covers this window"
CHARGER_USE = "Not available yet · connector capacity not read"
NO_SETTLEMENT = "Not available yet · no settlement records"
NO_SETTLEMENT_ASSURE = "Not available yet · no settlement records · reconciles the revenue shown under Grow revenue"
ALL_AVAILABLE = "All connectors available"
NO_FAULT = "No charger fault recorded"
SITE_POWER_NOT_READ = "Not available yet · site power not read"
NO_WARRANTY = "Not available yet · no warranty record"
NO_ROSTER = "Not available yet · no bus roster connected"
EVERY_END = "Every session has an accepted end"
NO_STATUS_GAP = "No status gap"
TARIFF_ESTIMATE = "gross tariff estimate"
NO_TARIFF = "Gross tariff estimate not available yet"
PROTECT_SUBLINE = "Charger condition is not assessed"
EVIDENCE_LIMITED = "Evidence limited · no verified result yet"
NO_VERIFIED = "No verified result yet"
OPTION_WHAT_IFS = "Charging what-ifs"
#: A fault-stopped connector: the health row `kind` CONNECTOR with `condition_state` NEEDS_INVESTIGATION
#: (`analytics/ev_depth.py:173-205`).
FAULT_KIND, FAULT_STATE = "CONNECTOR", "NEEDS_INVESTIGATION"

COPY = (NO_SESSION_ASSESSMENT, CHARGER_USE, NO_SETTLEMENT, NO_SETTLEMENT_ASSURE, ALL_AVAILABLE, NO_FAULT,
        SITE_POWER_NOT_READ, NO_WARRANTY, NO_ROSTER, EVERY_END, NO_STATUS_GAP, TARIFF_ESTIMATE, NO_TARIFF,
        PROTECT_SUBLINE, EVIDENCE_LIMITED, NO_VERIFIED, OPTION_WHAT_IFS)


@dataclass(frozen=True)
class EvPorts:
    """Existing services, bound by B4 to the request's tenant, Site, access basis and cutoff."""
    overview: Callable[[datetime, datetime], dict[str, Any]]                     # ev_site_reads.py:595
    findings: Callable[[datetime, datetime, str | None], dict[str, Any]]         # assessment store :3342 (list)
    finding: Callable[[str, datetime, datetime], dict[str, Any] | None]          # assessment store :3352 (single)
    health: Callable[[datetime, datetime], dict[str, Any]]                       # EvDepthReadService.health
    availability: Callable[[datetime, datetime], dict[str, Any]]                 # EvDepthReadService.availability
    domain_actions: Callable[[datetime, datetime, str | None], dict[str, Any]]   # work/domain_action_index.py
    work: Callable[[str, datetime, datetime, str | None], dict[str, Any]]        # work/site_index.py:309
    plans: Callable[[datetime, datetime], list[dict[str, Any]]]                  # preventive DRAFT, this Site
    readiness: Callable[[datetime, datetime], str | None]                        # EstateEvidenceService (B4)


def duration_text(seconds: Any) -> str | None:
    """Seconds as "{h} h {m} min" / "{m} min"."""
    try:
        total = int(round(float(Decimal(str(seconds))) / 60))
    except (InvalidOperation, ValueError, TypeError):
        return None
    hours, minutes = divmod(total, 60)
    if hours and minutes:
        return f"{hours} h {minutes} min"
    return f"{hours} h" if hours else f"{minutes} min"


def compose(ports: EvPorts, *, site_code: str, lo: datetime, hi: datetime,
            site_timezone: str | None) -> Composition:
    c = site_code
    reads = Reads()
    tz = site_zone(site_timezone)
    suffix = "" if tz is not None else UTC_SUFFIX
    work_lo = hi - WORK_WINDOW

    overview = reads.call("ev_overview", ports.overview, lo, hi)
    finding_rows = reads.pages("ev_findings", ports.findings, lo, hi, key="items")
    health = reads.call("ev_depth", ports.health, lo, hi)
    availability = reads.call("ev_availability", ports.availability, lo, hi)
    action_rows = reads.pages("domain_action_index", ports.domain_actions, work_lo, hi)
    readiness = reads.call("evidence_readiness", ports.readiness, lo, hi)
    plans = reads.call("plans", ports.plans, work_lo, hi)
    cases: list[CaseFact] = []
    for kind, case_kind in (("incidents", INCIDENT), ("maintenance", MAINTENANCE_REQUEST)):
        rows = reads.pages("work_index", ports.work, kind, work_lo, hi)
        cases += [case_fact(r, case_kind, c) for r in rows or ()]
    actions = tuple(domain_action(r, c) for r in action_rows or () if r.get("title") is not None)  # B-Q21

    findings_ok = finding_rows is not None
    findings = [_finding(r) for r in finding_rows or ()]
    if findings_ok:  # addendum 3 (d): resolve each linked Finding the SUPPORTED-only list lacks
        known = {f.finding_id for f in findings}
        linked = sorted({a.origin_finding_id for a in actions if a.origin_finding_id}
                        | {fid for case in cases for fid in case.finding_ids})
        for fid in (x for x in linked if x not in known):
            try:
                row = ports.finding(fid, lo, hi)
            except Exception:  # noqa: BLE001 - a refused single read unsettles the Finding source (M1)
                findings_ok = False
                if "ev_findings" not in reads.failed:
                    reads.failed.append("ev_findings")
                continue
            if row is not None:
                findings.append(_finding(row))

    body = overview or {}
    base = overview is not None and (body.get("currentness") or {}).get("state") in SETTLED_CURRENTNESS
    settled = {o: base for o in ("EV-1", "EV-3", "EV-4", "EV-5")}
    settled["EV-7"] = base and readiness not in (None, "UNKNOWN")
    for key in finding_moved_outcomes(EV):  # addendum 3 M1
        settled[key] = settled.get(key, False) and findings_ok

    rc = readiness_confidence(readiness)
    den = body.get("denominator") if overview is not None else None
    den = den or {}
    started, completed = den.get("started"), den.get("completed")
    fault, incomplete, contradictory = den.get("fault_aborted"), den.get("incomplete"), den.get("contradictory")
    unknown = None if incomplete is None or contradictory is None else incomplete + contradictory
    kwh = num((body.get("energy") or {}).get("complete_kwh"))
    connectors = list(((availability or {}).get("availability") or {}).get("connectors") or ())
    out_connectors = [x for x in connectors if (x.get("known_unavailable_seconds") or 0) > 0]
    fault_rows = [r for r in ((health or {}).get("health") or {}).get("rows") or ()
                  if r.get("kind") == FAULT_KIND and r.get("condition_state") == FAULT_STATE]

    def stamp(value: Any) -> str | None:
        at = utc(value)
        if at is None:
            return None
        local = at.astimezone(tz or timezone.utc)
        return f"{day_month(local)} {local:%H:%M}"

    contributors = {
        GROW: (_charging(overview is not None, kwh, completed, rc),
               Contributor("charger_use", "Charger use", CHARGER_USE),
               Contributor("energy_billed", "Energy billed against metered", NO_SETTLEMENT)),
        COST: (),
        PROTECT: (_session_service(overview is not None, fault, unknown, rc),
                  _availability(availability, connectors, rc),
                  _condition(health, fault_rows, rc),
                  _site_power(body, overview is not None, rc),
                  Contributor("warranty", "Warranty", NO_WARRANTY)),
        ASSURE: (Contributor("departures", "Departures against the timetable", NO_ROSTER),
                 Contributor("energy_billed", "Energy billed against metered", NO_SETTLEMENT_ASSURE, None,
                             f"/sites/{c}/ev/financials"),
                 _session_records(overview is not None, incomplete, rc),
                 _status_gap(availability, connectors, stamp, suffix, rc)),
    }

    money = body.get("consequence_summary") or {}
    priced = money.get("state") == "PRICED" and money.get("amount") is not None
    out_text = None
    if out_connectors:
        first = out_connectors[0]
        out_text = (f"Connector {first.get('label')} was out of service for "
                    f"{duration_text(first.get('known_unavailable_seconds'))}; which departures were affected is "
                    "not known yet.")
    missing_seconds = sum(int(x.get("unknown_seconds") or 0) for x in connectors) if availability else 0
    assure_sub = None
    if (incomplete or 0) > 0 or missing_seconds > 0:
        assure_sub = (f"{incomplete or 0} {plural(incomplete or 0, 'session end', 'session ends')} and "
                      f"{duration_text(missing_seconds)} of connector status are missing")
    headline = {GROW: TARIFF_ESTIMATE if priced else NO_TARIFF,
                PROTECT: (None if None in (fault, unknown, started) else
                          f"{fault} interrupted · {unknown} unknown of {started} "
                          f"{plural(started, 'session', 'sessions')}"),
                ASSURE: EVIDENCE_LIMITED if readiness in ("LIMITED", "NONE") else NO_VERIFIED}
    headline_money = {GROW: ({"amount_low": money.get("amount"), "amount_high": money.get("amount"),
                              "currency": money.get("currency")} if priced else None)}
    subline = {GROW: f"{kwh} kWh delivered in complete sessions" if kwh is not None else None,
               PROTECT: f"{out_text} {PROTECT_SUBLINE}" if out_text else PROTECT_SUBLINE,
               ASSURE: assure_sub}

    label = (fault_rows[0].get("label") if fault_rows else out_connectors[0].get("label") if out_connectors
             else None)
    lead = next((f for f in sorted(findings, key=lambda f: (f.title, f.finding_id)) if f.open and f.in_window), None)
    action = next((a for a in sorted(actions, key=lambda a: (a.code or "", a.action_id))
                   if lead is not None and a.origin_finding_id == lead.finding_id), None)
    investigate = action.href if action is not None else lead.href if lead is not None else None
    options = {GROW: (Option(OPTION_WHAT_IFS, f"/sites/{c}/ev/financials/scenarios"),), COST: (),
               PROTECT: (Option(f"Investigate connector {label}", investigate),) if label and investigate else (),
               ASSURE: ()}

    facts = SiteFacts(domain=EV, site_code=c, findings=tuple(findings), actions=actions, cases=tuple(cases),
                      plans=tuple(plan_fact(p, tz) for p in plans or ()), readiness=readiness,
                      contributors=contributors, options=options, headline=headline, headline_money=headline_money,
                      subline=subline, settled=settled, date_suffix=suffix, findings_settled=findings_ok)
    failed = tuple(reads.failed)
    return Composition(facts, "PARTIAL" if failed else "AVAILABLE", failed, unresolved_links(facts),
                       {"from": lo, "to": hi}, site_timezone if tz is not None else None)


def _finding(r: dict[str, Any]) -> FindingFact:
    links = r.get("links") or {}
    return FindingFact(str(r["finding_id"]), str(r["revision_id"]), r.get("title") or "", EV_MECHANISM,
                       r.get("lifecycle") or "", links.get("self") or links.get("finding"))


def _charging(ok: bool, kwh: str | None, completed: Any, rc: Any) -> Contributor:
    if not ok:
        return Contributor("charging_delivered", "Charging delivered", NOT_LOADED)
    if kwh is None or completed is None:
        return Contributor("charging_delivered", "Charging delivered", NO_SESSION_ASSESSMENT)
    return Contributor("charging_delivered", "Charging delivered",
                       f"{kwh} kWh in {completed} complete {plural(completed, 'session', 'sessions')}", rc)


def _session_service(ok: bool, fault: Any, unknown: Any, rc: Any) -> Contributor:
    if not ok:
        return Contributor("session_service", "Session service", NOT_LOADED)
    if fault is None or unknown is None:
        return Contributor("session_service", "Session service", NO_SESSION_ASSESSMENT)
    return Contributor("session_service", "Session service",
                       f"{fault} fault-aborted {plural(fault, 'session', 'sessions')}, {unknown} "
                       f"{plural(unknown, 'outcome', 'outcomes')} unknown", rc)


def _availability(body: Any, connectors: list, rc: Any) -> Contributor:
    if body is None:
        return Contributor("connector_availability", "Connector availability", NOT_LOADED)
    parts = [f"Connector {x.get('label')}: {duration_text(x.get('known_unavailable_seconds') or 0)} out, "
             f"{duration_text(x.get('unknown_seconds') or 0)} unknown" for x in connectors
             if (x.get("known_unavailable_seconds") or 0) > 0 or (x.get("unknown_seconds") or 0) > 0]
    return Contributor("connector_availability", "Connector availability", "; ".join(parts) or ALL_AVAILABLE, rc)


def _condition(body: Any, fault_rows: list, rc: Any) -> Contributor:
    if body is None:
        return Contributor("charger_condition", "Charger condition", NOT_LOADED)
    if fault_rows:
        return Contributor("charger_condition", "Charger condition",
                           f"Fault recorded on {fault_rows[0].get('label')}", rc)
    return Contributor("charger_condition", "Charger condition", NO_FAULT, rc)


def _site_power(body: dict, ok: bool, rc: Any) -> Contributor:
    if not ok:
        return Contributor("site_power", "Site power", NOT_LOADED)
    power = body.get("site_power") or {}
    peak, limit = num(power.get("observed_peak_kw")), num(power.get("configured_limit_kw"))
    if peak is not None and limit is not None:
        return Contributor("site_power", "Site power", f"Peak {peak} kW of the {limit} kW import limit", rc)
    if limit is not None:  # §B.4: "Declared" for the limit when the peak is null
        return Contributor("site_power", "Site power", f"{limit} kW import limit declared; peak not read", DECLARED)
    return Contributor("site_power", "Site power", SITE_POWER_NOT_READ)


def _session_records(ok: bool, incomplete: Any, rc: Any) -> Contributor:
    if not ok:
        return Contributor("session_records", "Session records", NOT_LOADED)
    if incomplete is None:
        return Contributor("session_records", "Session records", NO_SESSION_ASSESSMENT)
    if incomplete == 0:
        return Contributor("session_records", "Session records", EVERY_END, rc)
    return Contributor("session_records", "Session records",
                       f"{incomplete} {plural(incomplete, 'session has', 'sessions have')} no accepted end", rc)


def _status_gap(body: Any, connectors: list, stamp: Callable[[Any], str | None], suffix: str,
                rc: Any) -> Contributor:
    if body is None:
        return Contributor("connector_status", "Connector status", NOT_LOADED)
    spans = sorted((s for x in connectors for s in x.get("spans") or () if s.get("state") == "UNKNOWN"),
                   key=lambda s: str(s.get("from")))
    if not spans:
        return Contributor("connector_status", "Connector status", NO_STATUS_GAP, rc)
    first = spans[0]
    return Contributor("connector_status", "Connector status",
                       f"Missing {stamp(first.get('from'))}–{stamp(first.get('to'))}{suffix}", rc)
