"""OUT-B2: the mini-grid composer. It reads the injected mini ports and builds the board's `SiteFacts`.

Sources and rules: build spec §B.4 "Mini (Kobo)", rulings B-Q6/Q10-Q14/Q17/Q18/Q22/Q23 and addendum 2. Every port is
an existing service bound by B4 (`site_outcomes/read.py`); this module calls them through `MiniPorts` and never
imports an adapter or another package's composition. A refused or failed port never refuses the board: it is named
in `MiniComposition.failed`, its contributor reads "Not available yet · this record could not be loaded", and
`read_state` is PARTIAL (B-Q17). Only the overview, dispatch, depth, readiness and Finding index reads can leave an
outcome UNKNOWN (addendum 2 item 5, addendum 3 M1)."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any
from zoneinfo import ZoneInfo

from assetops_backend.analytics.finding_episode import MECHANISM as FINDING_MECHANISM
from assetops_backend.analytics.plain import ALTERNATIVE_LABELS
from assetops_backend.estate.placement import place
from assetops_backend.estate.portfolio import action_for, workflow_label
from assetops_backend.mini_depth.inputs import MiniInputsRefused, Window, local_day_of, local_hour, local_noon, zone
from assetops_backend.outcomes.catalogue import MINI
from assetops_backend.site_outcomes.board import (
    DECLARED, MAINTENANCE_REQUEST, INCIDENT, PLAN_RECORD, ActionFact, CaseFact, Contributor, FindingFact, Option,
    PlanFact, SignalFact, SiteFacts, finding_moved_outcomes, readiness_confidence, unresolved_links)

GROW, COST, PROTECT, ASSURE = "GROW_REVENUE", "OPTIMIZE_COST", "PROTECT_ASSET", "ASSURE_PERFORMANCE"
WORK_WINDOW = timedelta(days=31)  # the Finding, Action, work and estate reads' maximum (B-Q22, addendum 2 item 4)
DEPTH_DOMAINS = ("renewable", "fuel", "service", "backup")
MAX_PAGES = 50

NOT_LOADED = "Not available yet · this record could not be loaded"
UTC_SUFFIX = " · UTC (Site time zone unavailable)"
GAP_GENERIC = "An evidence gap limits this conclusion"
NO_VERIFIED = "No verified result yet"
GROW_SUBLINE = "Sales to productive users are not metered, so revenue itself is not measured yet"
PROTECT_HEADLINE = "Battery and generator condition are not assessed"
PROTECT_SUBLINE = ("Battery and generator condition is not assessed; these are early warnings only. Power was "
                   "delivered, but what customers needed is not measured")
COST_NO_MONEY = "No priced exposure in this hour"
COST_MONEY = "exposure in this hour"
FIXED = {
    "cash": "Not available yet · no billing or payment records",
    "earnings": "Not available yet · needs site income, operating cost and capital records",
    "battery": "Not available yet · battery reserve readings are not read for this view",
    "plan_target": "Not available yet · no target declared for this site",
}
NO_FUEL_BALANCE = "No complete fuel balance yet"
PRICE_FALLBACK = "Declared price · see Assumptions"
NO_GEN_PLAN = "No preventive plan recorded"
SERVICE_MEASURED = "Delivered power measured; demand not measured"
NO_BACKUP_EVENT = "No backup event in this window"
SOLAR_NOT_READ = "Not available yet · solar headroom not read for this day"
SERVICE_NOT_READ = "Not available yet · delivered power not read for this hour"
HEADROOM_ISSUE = "Productive-use headroom"
OPTION_WHAT_IF = "Productive-use what-if"
OPTION_TRIAL = "Trial a lower generator stop setting"
OPTION_CHANGE = "Proposed setting change"
OPTION_RESTORE = "Restore battery reporting"
VERIFICATION_TEXT = {"PENDING": "{code} not yet verified", "NO_PLAN": "{code} not yet verified",
                     "REASSESSMENT_PENDING": "{code} not yet verified", "VERIFIED": "{code} verified on test data",
                     "INEFFECTIVE": "{code} did not meet its target", "INCONCLUSIVE": "{code} result not determined"}
PENDING_STATES = ("PENDING", "NO_PLAN", "REASSESSMENT_PENDING")
PENDING_CHIP = {"label": "Pending", "tone": "neutral"}
HIGH_CHIP = {"label": "High", "tone": "green"}
UNKNOWN_CHIP = {"label": "Unknown", "tone": "gray"}
#: Addendum 2 item 3: `place(...).confidence` words (portfolioWords.ts:38) as board chips.
PLACEMENT_CHIP = {"SUPPORTED_SOURCE_COHERENT": HIGH_CHIP, "LIMITED": {"label": "Limited", "tone": "amber"},
                  "UNKNOWN": UNKNOWN_CHIP}
READINESS_WORD = {"FULL": "Full", "LIMITED": "Limited", "NONE": "None", "UNKNOWN": "Unknown"}
CLOSED_LABELS = ("Verified", "Resolution withdrawn")  # B-Q18
#: The Portfolio's source words (`estate/placement.py:54`, `:59`), copied as a local plain-text mapping so the
#: composer imports no private estate name (B2 review L1); test_out_b2_mini asserts equality.
SOURCE_TEXT = {"REGISTERED_SIMULATION": "Generated test data source",
               "AUTHORED_DEMONSTRATION": "Prepared example data source", "MIXED": "Mixed sources"}
SOURCE_UNRESOLVED = "Source not resolved"
#: Addendum 3 M1: a mini Finding index body in one of these overall states leaves the Finding source unsettled.
UNSETTLED_INDEX_STATUS = ("FAILED", "STALE", "PENDING")
#: Addendum 3 L3: the diagnostics marker for an Action the Action index returned but the estate read did not.
ESTATE_ROW_MISSING = "ESTATE_ROW_MISSING"

#: Every fixed viewer string, for the vocabulary scan (tests/test_out_b2_vocabulary.py).
COPY = (NOT_LOADED, UTC_SUFFIX, GAP_GENERIC, NO_VERIFIED, GROW_SUBLINE, PROTECT_HEADLINE, PROTECT_SUBLINE,
        COST_NO_MONEY, COST_MONEY, *FIXED.values(), NO_FUEL_BALANCE, PRICE_FALLBACK, NO_GEN_PLAN, SERVICE_MEASURED,
        NO_BACKUP_EVENT, SOLAR_NOT_READ, SERVICE_NOT_READ, HEADROOM_ISSUE, OPTION_WHAT_IF, OPTION_TRIAL,
        OPTION_CHANGE, OPTION_RESTORE, *ALTERNATIVE_LABELS.values(), *SOURCE_TEXT.values(),
        SOURCE_UNRESOLVED, *READINESS_WORD.values())


@dataclass(frozen=True)
class MiniPorts:
    """Existing services, bound by B4 to the request's tenant, Site, access basis, gate and pin."""
    overview: Callable[[date], dict[str, Any]]                                   # site_overview/read.py:114
    depth: Callable[[str, datetime, datetime], dict[str, Any]]                   # mini_depth/read.py:338
    dispatch: Callable[[date], dict[str, Any]]                                   # analytics/dispatch_read.py:123
    assumption: Callable[[datetime], dict[str, Any]]                             # diesel_price_per_litre series
    finding_index: Callable[[datetime, datetime, str | None], dict[str, Any]]    # analytics/finding_index.py:262
    estate: Callable[[datetime, datetime], dict[str, Any]]                       # {site_cov, findings, actions}
    action_index: Callable[[datetime, datetime, str | None], dict[str, Any]]     # actions/site_index.py:160
    verification: Callable[[str], dict[str, Any]]                                # actions/verification.py:966
    action: Callable[[str, str], dict[str, Any] | None]                          # actions/service.py:653
    work: Callable[[str, datetime, datetime, str | None], dict[str, Any]]        # work/site_index.py:309
    plans: Callable[[datetime, datetime], list[dict[str, Any]]]                  # preventive DRAFT, this Site
    readiness: Callable[[datetime, datetime], str | None]                        # EstateEvidenceService (B4)


@dataclass(frozen=True)
class MiniComposition:
    facts: SiteFacts
    read_state: str                                # AVAILABLE | PARTIAL
    failed: tuple[str, ...]                        # port names that refused or failed
    diagnostics: tuple[tuple[str, str], ...]       # unresolved (holder id, Finding id) links and (Action id,
    #                                                ESTATE_ROW_MISSING); never on the wire
    window: dict[str, datetime]                    # the overview day {from, to}
    timezone: str | None                           # the Site zone used for local dates, None = UTC fallback


class Reads:
    def __init__(self) -> None:
        self.failed: list[str] = []
        self.statuses: dict[str, set[str]] = {}

    def call(self, name: str, fn: Callable[..., Any], *args: Any) -> Any:
        try:
            return fn(*args)
        except Exception:  # noqa: BLE001 - B.3: a refused or failed producer read never refuses the board
            if name not in self.failed:
                self.failed.append(name)
            return None

    def pages(self, name: str, fn: Callable[..., dict[str, Any]], *args: Any,
              key: str = "rows") -> list[dict[str, Any]] | None:
        rows: list[dict[str, Any]] = []
        cursor = None
        for _ in range(MAX_PAGES):
            body = self.call(name, fn, *args, cursor)
            if body is None:
                return None
            rows += list(body.get(key) or ())
            if body.get("status") is not None:
                self.statuses.setdefault(name, set()).add(str(body["status"]))
            cursor = body.get("next_cursor")
            if not cursor:
                return rows
        self.failed.append(name)
        return None


# ---------------------------------------------------------------- formatting

def num(value: Any) -> str | None:
    """A decimal value as display text: integers plain, otherwise one decimal place."""
    if value is None:
        return None
    try:
        d = Decimal(str(value))
    except InvalidOperation:
        return None
    if d == d.to_integral_value():
        return str(int(d))
    return f"{d.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP).normalize():f}"


def utc(value: Any) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    text = str(value)
    parsed = datetime.fromisoformat(text[:-1] + "+00:00" if text.endswith("Z") else text)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def site_zone(name: str | None) -> ZoneInfo | None:
    """The Site zone through `mini_depth/inputs.py` `zone` (B2 review L2); missing or invalid gives None."""
    try:
        return zone(name)
    except MiniInputsRefused:
        return None


MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def day_month(d: Any) -> str:
    """A Site-local date as "d MMM" (guide §4)."""
    return f"{d.day} {MONTHS[d.month - 1]}"


def plural(n: Any, one: str, many: str) -> str:
    """Addendum 3 L7: the singular for n = 1 in every "{n} ..." template."""
    try:
        return one if n is not None and Decimal(str(n)) == 1 else many
    except InvalidOperation:
        return many


def price_text(value: Any) -> str | None:
    """B2 review L6: a declared price for display: two decimal places, more only when the stored value has them."""
    try:
        d = Decimal(str(value))
    except InvalidOperation:
        return None
    cents = d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{cents:f}" if cents == d else f"{d.normalize():f}"


def limitation_text(limitation: str) -> str:
    """B-Q12: the plain label of the first known code (leading code, or a code named in the detail), else the
    generic sentence. A raw limitation string is never rendered."""
    lead = limitation.split(":", 1)[0].strip()
    if lead in ALTERNATIVE_LABELS:
        return ALTERNATIVE_LABELS[lead]
    for code, label in ALTERNATIVE_LABELS.items():
        if code in limitation:
            return label
    return GAP_GENERIC


def not_available(key: str, label: str, href: str | None = None) -> Contributor:
    return Contributor(key, label, NOT_LOADED, None, href)


# ---------------------------------------------------------------- composer

def compose(ports: MiniPorts, *, site_code: str, day: date, site_timezone: str | None) -> MiniComposition:
    """`day` is the overview's UTC day (`selected_day` or `db_today()`); `site_timezone` is the zone the route's
    Site lookup carries, used only to build the mini depth windows. Local dates use the depth body's own
    `site.timezone`; if depth is refused they are UTC with the suffix (addendum 2 item 6)."""
    c = site_code
    reads = Reads()
    start = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    work_lo = end - WORK_WINDOW

    overview = reads.call("mini_overview", ports.overview, day)
    depth = _depth(reads, ports, start, site_timezone)
    depth_ok = all(depth.get(d) is not None for d in DEPTH_DOMAINS)
    zone_name = next((b["site"].get("timezone") for b in depth.values()
                      if b is not None and (b.get("site") or {}).get("timezone")), None)
    tz = site_zone(zone_name) if depth_ok else None
    dispatch = reads.call("dispatch", ports.dispatch, day)
    readiness = reads.call("evidence_readiness", ports.readiness, start, end)
    estate = reads.call("estate", ports.estate, work_lo, end)
    finding_rows = reads.pages("finding_index", ports.finding_index, work_lo, end)
    findings_ok = finding_rows is not None and not (reads.statuses.get("finding_index", set())
                                                    & set(UNSETTLED_INDEX_STATUS))
    if not findings_ok and "finding_index" not in reads.failed:
        reads.failed.append("finding_index")  # a non-current index body: PARTIAL, so text and notice agree
    action_rows = reads.pages("action_index", ports.action_index, work_lo, end)
    price = reads.call("assumptions", ports.assumption, start)
    plans = reads.call("plans", ports.plans, work_lo, end)
    cases: list[CaseFact] = []
    for kind, case_kind in (("incidents", INCIDENT), ("maintenance", MAINTENANCE_REQUEST)):
        rows = reads.pages("work_index", ports.work, kind, work_lo, end)
        cases += [case_fact(r, case_kind, c) for r in rows or ()]

    findings = _findings(finding_rows or (), estate, c, start, end)
    actions, has_change, missing_estate = _actions(reads, ports, action_rows or (), estate, c)
    plan_facts = tuple(plan_fact(p, tz) for p in plans or ())

    body = overview or {}
    freshness = (body.get("freshness") or {}).get("state")
    assessment = body.get("assessment") or {}
    base = overview is not None and freshness == "CURRENT" and assessment.get("state") != "CLOSED"
    settled = {"MG-1": base and depth_ok, "MG-6": base, "MG-3": base, "MG-2": base and dispatch is not None,
               "MG-5": base and depth_ok, "MG-4": base,
               "MG-7": base and readiness not in (None, "UNKNOWN")}
    for key in finding_moved_outcomes(MINI):  # addendum 3 M1: the Finding source is a status producer
        settled[key] = settled.get(key, False) and findings_ok

    limitations = [str(x) for x in assessment.get("limitations") or ()] if overview is not None else []
    renewable = (depth.get("renewable") or {}).get("cards") or {}
    eligible, assessed = renewable.get("eligible_days"), renewable.get("assessed_days")
    lead = next((f for f in sorted(findings, key=lambda f: (f.title, f.finding_id)) if f.open and f.in_window), None)

    signals = (SignalFact("SIGNAL:PRODUCTIVE_USE_HEADROOM", eligible is not None and eligible >= 1, HEADROOM_ISSUE,
                          f"/sites/{c}/performance/renewable"),
               SignalFact("SIGNAL:EVIDENCE_GAP", bool(limitations),
                          (f"{limitation_text(limitations[0])} limits this conclusion"
                           if limitations and limitation_text(limitations[0]) != GAP_GENERIC else GAP_GENERIC)))

    rc = readiness_confidence(readiness)
    contributors = {
        GROW: _grow(c, depth, eligible, assessed, rc),
        COST: _cost(c, dispatch, depth, price, lead, rc),
        PROTECT: _protect(c, depth, plan_facts, plans is None),
        ASSURE: _assure(c, actions, body, overview is not None, readiness, rc, limitations,
                        "action_read" in reads.failed or action_rows is None),
    }
    options = {GROW: (Option(OPTION_WHAT_IF, f"/sites/{c}/financials/scenarios"),),
               COST: tuple(o for o in (
                   Option(OPTION_TRIAL, f"/sites/{c}/findings/{lead.finding_id}/recommendation") if lead else None,
                   Option(OPTION_CHANGE, f"/sites/{c}/foundation/changes") if has_change else None) if o),
               PROTECT: (),
               ASSURE: (Option(OPTION_RESTORE, f"/sites/{c}/work"),) if limitations else ()}

    headroom = renewable.get("headroom_kw") or {}
    lo_kw, hi_kw = num(headroom.get("low")), num(headroom.get("high"))
    money = body.get("money") or {}
    priced = money.get("state") == "PRICED" and (money.get("eligibility") or {}).get("state") == "ELIGIBLE"
    avoidable, _ = _dispatch_minutes(dispatch)
    verified = sum(1 for a in actions if a.verification_state == "VERIFIED")
    headline = {GROW: f"{lo_kw}–{hi_kw} kW of daytime solar unused" if lo_kw and hi_kw else None,
                COST: (COST_MONEY if priced else COST_NO_MONEY) if overview is not None else None,
                PROTECT: PROTECT_HEADLINE,
                ASSURE: f"{verified} {plural(verified, 'verified result', 'verified results')}"
                if verified else NO_VERIFIED}
    headline_money = {COST: {k: money.get(k) for k in ("amount_low", "amount_high", "currency")} if priced else None}
    subline = {GROW: GROW_SUBLINE,
               COST: f"Generator stayed on {num(avoidable)} {plural(num(avoidable), 'minute', 'minutes')} longer "
                     "than needed"
               if avoidable is not None and avoidable > 0 else None,
               PROTECT: PROTECT_SUBLINE,
               ASSURE: limitation_text(limitations[0]) if limitations else None}

    facts = SiteFacts(domain=MINI, site_code=c, findings=findings, actions=actions, cases=tuple(cases),
                      plans=plan_facts, readiness=readiness, contributors=contributors, options=options,
                      signals_extra=signals, headline=headline, headline_money=headline_money, subline=subline,
                      settled=settled, date_suffix="" if tz is not None else UTC_SUFFIX,
                      findings_settled=findings_ok)
    failed = tuple(reads.failed)
    diagnostics = unresolved_links(facts) + tuple((aid, ESTATE_ROW_MISSING) for aid in missing_estate)
    return MiniComposition(facts, "PARTIAL" if failed else "AVAILABLE", failed, diagnostics,
                           {"from": start, "to": end}, zone_name if tz is not None else None)


def _depth(reads: Reads, ports: MiniPorts, start: datetime, tz_name: str | None) -> dict[str, dict | None]:
    """B-Q6: the Site-local day containing the overview `window.start`; renewable reads that whole local day, the
    hourly domains read its local noon hour (reading recorded in the packet)."""
    try:  # the mini_depth/inputs.py helpers (addendum 2 item 6, B2 review L2); a refusal leaves depth unread
        name = tz_name or ""
        local_day = local_day_of(Window(start, start + timedelta(days=1)), name)
        noon = local_noon(local_day, name)
        day_lo = local_hour(local_day, 0, name).start
        day_hi = local_hour(local_day + timedelta(days=1), 0, name).start
    except MiniInputsRefused:
        reads.failed.append("mini_depth")
        return {d: None for d in DEPTH_DOMAINS}
    windows = {"renewable": (day_lo, day_hi)}
    windows.update({d: (noon.start, noon.end) for d in ("fuel", "service", "backup")})
    return {d: reads.call("mini_depth", ports.depth, d, *windows[d]) for d in DEPTH_DOMAINS}


def _dispatch_minutes(dispatch: dict[str, Any] | None) -> tuple[Decimal | None, Decimal | None]:
    """B-Q10: Σ candidate and Σ indeterminate minutes over the window's interval results."""
    if dispatch is None:
        return None, None
    a = u = Decimal(0)
    for interval in dispatch.get("intervals") or ():
        portions = (interval.get("result") or {}).get("portions_minutes") or {}
        a += Decimal(str(portions.get("candidate") or 0))
        u += Decimal(str(portions.get("indeterminate") or 0))
    return a, u


def _findings(rows: Any, estate: dict[str, Any] | None, c: str, start: datetime,
              end: datetime) -> tuple[FindingFact, ...]:
    """Every index head over the work window, closed ones included (M1b). `in_window` = the episode intersects
    the overview day. Confidence: `place(...)` over the estate row of the same revision (addendum 2 item 3)."""
    estate_rows = {str(r["finding_revision_id"]): r for r in (estate or {}).get("findings") or ()}
    estate_actions = list((estate or {}).get("actions") or ())
    site_cov = (estate or {}).get("site_cov") or {}
    out = []
    for r in rows:
        episode = r.get("episode") or {}
        lo, hi = utc(episode.get("start")), utc(episode.get("end"))
        in_window = lo is not None and lo < end and (hi is None or hi > start)
        confidence = None
        er = estate_rows.get(str(r["finding_revision_id"])) if estate is not None else None
        if er is not None:
            try:
                confidence = place(er, action_for(er, estate_actions), site_cov, None).confidence
            except Exception:  # noqa: BLE001 - an unselectable Action leaves the chip null, never the board
                confidence = None
        out.append(FindingFact(str(r["finding_id"]), str(r["finding_revision_id"]), r["title"], FINDING_MECHANISM,
                               r["lifecycle"], (r.get("links") or {}).get("selected_revision"),
                               confidence_label=confidence, in_window=in_window))
    return tuple(out)


def _actions(reads: Reads, ports: MiniPorts, rows: Any, estate: dict[str, Any] | None,
             c: str) -> tuple[tuple[ActionFact, ...], bool, tuple[str, ...]]:
    """Action index rows; the workflow label from the estate Action of the same id fed to `workflow_label`
    unchanged (addendum 2 item 2); verification from the summary; a Foundation change from the Action read."""
    by_id = {str(a["action_id"]): a for a in (estate or {}).get("actions") or ()}
    out, has_change, missing = [], False, []
    for r in rows:
        aid = str(r["action_id"])
        event_id = str((r.get("selected_event") or {}).get("id") or "")
        state = r.get("state") or {}
        resolution = state.get("resolution") or {}
        estate_action = by_id.get(aid)
        label = NOT_LOADED if estate is None or estate_action is None else workflow_label(estate_action)
        if estate is not None and estate_action is None:  # addendum 3 L3: text and notice never disagree
            missing.append(aid)
            if "estate" not in reads.failed:
                reads.failed.append("estate")
        is_open = label not in CLOSED_LABELS if label != NOT_LOADED else resolution.get("state") not in (
            "RESOLVED", "RESOLUTION_WITHDRAWN")
        summary = reads.call("action_read", ports.verification, aid)
        detail = reads.call("action_read", ports.action, aid, event_id)
        has_change = has_change or bool(detail and detail.get("change"))
        origin = r.get("origin") or {}
        out.append(ActionFact(
            aid, r.get("action_code"), "", None if origin.get("finding_id") is None else str(origin["finding_id"]),
            None if origin.get("finding_revision_id") is None else str(origin["finding_revision_id"]),
            state.get("application") == "APPLIED", is_open, None if summary is None else summary.get("state"),
            (r.get("links") or {}).get("selected_event") or f"/sites/{c}/actions/{aid}?event_id={event_id}",
            workflow_label=label, verification_href=f"/sites/{c}/actions/{aid}/verification?event_id={event_id}"))
    return tuple(out), has_change, tuple(missing)


def case_fact(r: dict[str, Any], kind: str, c: str) -> CaseFact:
    cid = str(r["case_id"])
    href = f"/maintenance/requests/{cid}" if kind == MAINTENANCE_REQUEST else f"/sites/{c}/work/incidents"
    fids = tuple(str(x["finding_id"]) for x in r.get("finding_links") or () if x.get("finding_id"))
    return CaseFact(cid, r.get("code"), kind, r.get("title") or "", r.get("state") or "",
                    None if r.get("asset_id") is None else str(r["asset_id"]), r.get("asset_label"), fids,
                    utc(r.get("occurred_at")), href)


def plan_fact(p: dict[str, Any], tz: ZoneInfo | None) -> PlanFact:
    due = utc(p.get("next_due_at"))
    hours = p.get("next_due_hours")
    return PlanFact(str(p["canonical_plan_id"]), p.get("code"), p.get("title") or "", p.get("trigger_kind") or "",
                    None if due is None else due.astimezone(tz or timezone.utc).date(),
                    None if hours is None else float(Decimal(str(hours))), p.get("state") or "",
                    None if p.get("asset_id") is None else str(p["asset_id"]), "/maintenance/preventive")


# ---------------------------------------------------------------- contributors (§B.4 mini table)

def _grow(c: str, depth: dict, eligible: Any, assessed: Any, rc: Any) -> tuple[Contributor, ...]:
    href = f"/sites/{c}/performance/renewable"
    if depth.get("renewable") is None:
        use = not_available("productive_use", "Productive use", href)
    elif eligible is None or assessed is None:
        use = Contributor("productive_use", "Productive use", SOLAR_NOT_READ, None, href)
    else:
        use = Contributor("productive_use", "Productive use",
                          f"Spare solar on {eligible} of {assessed} well-observed "
                          f"{plural(assessed, 'day', 'days')}", rc, href)
    return (use, Contributor("cash_collected", "Cash collected", FIXED["cash"]),
            Contributor("site_earnings", "Site earnings", FIXED["earnings"]))


def _cost(c: str, dispatch: Any, depth: dict, price: Any, lead: FindingFact | None,
          rc: Any) -> tuple[Contributor, ...]:
    a, u = _dispatch_minutes(dispatch)
    gen_href = f"/sites/{c}/performance/dispatch"
    if dispatch is None:
        gen = not_available("generator_use", "Generator use", gen_href)
    else:
        chip = PLACEMENT_CHIP.get(lead.confidence_label) if lead and lead.confidence_label else None
        gen = Contributor("generator_use", "Generator use", f"{num(a)} min avoidable, {num(u)} min unclear",
                          chip, gen_href)
    fuel_href = f"/sites/{c}/performance/fuel"
    if depth.get("fuel") is None:
        fuel = not_available("fuel", "Fuel", fuel_href)
    else:
        opening = (depth["fuel"].get("cards") or {}).get("opening_l")
        fuel = (Contributor("fuel", "Fuel", NO_FUEL_BALANCE, UNKNOWN_CHIP, fuel_href) if opening is None else
                Contributor("fuel", "Fuel", f"{num(opening)} L at the start of the window", rc, fuel_href))
    price_href = f"/sites/{c}/financials/assumptions"
    if price is None:
        fuel_price = not_available("fuel_price", "Fuel price", price_href)
    else:
        sel = price.get("selection") or {}
        p = sel.get("price") or {}
        shown = price_text(p.get("value")) if p.get("value") is not None else None
        text = (f"Declared at {shown} {p.get('currency')} per litre"
                if sel.get("state") == "PRICED" and shown is not None else PRICE_FALLBACK)
        fuel_price = Contributor("fuel_price", "Fuel price", text, DECLARED, price_href)
    return gen, fuel, fuel_price


def _protect(c: str, depth: dict, plans: tuple[PlanFact, ...], plans_failed: bool) -> tuple[Contributor, ...]:
    battery = Contributor("battery", "Battery", FIXED["battery"], None, f"/sites/{c}/health")
    run_hours = [p for p in sorted(plans, key=lambda p: (p.code or "", p.plan_id)) if p.trigger_kind == "RUN_HOURS"]
    if plans_failed:
        generator = not_available("generator", "Generator", "/maintenance/preventive")
    elif not run_hours:
        generator = Contributor("generator", "Generator", NO_GEN_PLAN, PLAN_RECORD, "/maintenance/preventive")
    else:
        due = run_hours[0].next_due_hours
        generator = Contributor("generator", "Generator",
                                f"Service due at {num(due)} operating {plural(num(due), 'hour', 'hours')} · hours "
                                "since service not recorded"
                                if due is not None else NO_GEN_PLAN, PLAN_RECORD, "/maintenance/preventive")
    svc_href = f"/sites/{c}/performance/service"
    if depth.get("service") is None:
        service = not_available("service_delivery", "Service delivery", svc_href)
    elif (depth["service"].get("cards") or {}).get("delivered_load_kw") is None:
        service = Contributor("service_delivery", "Service delivery", SERVICE_NOT_READ, None, svc_href)
    else:
        service = Contributor("service_delivery", "Service delivery", SERVICE_MEASURED, UNKNOWN_CHIP, svc_href)
    bk_href = f"/sites/{c}/performance/backup"
    if depth.get("backup") is None:
        backup = not_available("backup_readiness", "Backup readiness", bk_href)
    else:
        cards = depth["backup"].get("cards") or {}
        outages, starts = cards.get("outage_count"), cards.get("start_success_count")
        text = (NO_BACKUP_EVENT if not outages and starts is None
                else f"{starts or 0} backup {plural(starts or 0, 'start', 'starts')} recorded")
        backup = Contributor("backup_readiness", "Backup readiness", text, UNKNOWN_CHIP, bk_href)
    return battery, generator, service, backup


def _assure(c: str, actions: tuple[ActionFact, ...], body: dict, overview_ok: bool, readiness: Any, rc: Any,
            limitations: list[str], actions_failed: bool) -> tuple[Contributor, ...]:
    out: list[Contributor] = []
    mine = sorted((a for a in actions if not a.is_domain), key=lambda a: (a.code or "", a.action_id))
    if actions_failed and not mine:
        out.append(not_available("verified_results", "Verified results"))
    elif not mine:
        out.append(Contributor("verified_results", "Verified results", NO_VERIFIED))
    for a in mine:
        state = a.verification_state
        text = VERIFICATION_TEXT.get(state or "", None)
        out.append(Contributor("verified_results", "Verified results",
                               text.format(code=a.code) if text else NOT_LOADED,
                               PENDING_CHIP if state in PENDING_STATES else None, a.verification_href))
    out.append(Contributor("actual_against_plan", "Actual against plan", FIXED["plan_target"]))
    if not overview_ok:
        out.append(not_available("readings", "Readings", f"/sites/{c}/evidence"))
    else:
        src = ((body.get("money") or {}).get("source_provenance") or {}).get("state")
        word = READINESS_WORD.get(readiness or "UNKNOWN", "Unknown")
        out.append(Contributor("readings", "Readings",
                               f"{SOURCE_TEXT.get(src or 'UNKNOWN', SOURCE_UNRESOLVED)} · readiness {word}",
                               rc, f"/sites/{c}/evidence"))
    if limitations:
        out.append(Contributor("battery_reporting", "Battery reporting", limitation_text(limitations[0]),
                               HIGH_CHIP, f"/sites/{c}/evidence"))
    return tuple(out)
