"""OUT-B4 (§B.3): `SiteOutcomeBoardService`, the Site outcome board and the estate outcome summary.

It holds the existing domain services, injected by `composition.py`, and no storage. Per request it binds them to
the Site, tenant, access basis, cutoff and pin as the ports of `mini.py`, `cold.py` and `ev.py`, runs the domain
composer, and assembles the wire (`board.assemble`). It never calls HTTP. Every port body except the estate rows
passes through `jsonable_encoder`, so the composers see exactly what the domain routes serve (the B2/B3 fakes model
those wire bodies). The estate rows are the selectors' own rows (addendum 3 item 16, condition 1).

A refused or failed port never refuses the board (B.3 "Refusals"): the composer records it, its outcomes are
UNKNOWN and `read_state` is PARTIAL. A port whose service is not configured raises `PortUnavailable` the same way.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode
from uuid import UUID

from fastapi.encoders import jsonable_encoder

from assetops_backend.outcomes.catalogue import (
    CATALOGUE_VERSION, CATEGORIES, CATEGORY_DEFINITION, CATEGORY_ICON, CATEGORY_LABEL, COLD, EV, MINI)
from assetops_backend.outcomes.outcome_map import POLICY_VERSION
from assetops_backend.outcomes.status import NEEDS_ATTENTION, STATE_LABEL, STATE_TONE, STATUS_POLICY, UNKNOWN
from assetops_backend.outcomes.warnings import POLICY as WARNINGS_POLICY
from assetops_backend.site_outcomes import cold, ev, mini
from assetops_backend.site_outcomes.board import assemble

SCHEMA_VERSION = "site-outcome-board-1"
SUMMARY_SCHEMA_VERSION = "estate-outcome-summary-1"
POLICY_VERSIONS = {"catalogue": CATALOGUE_VERSION, "outcome_map": POLICY_VERSION, "status": STATUS_POLICY,
                   "warnings": WARNINGS_POLICY}
#: Stored Site type -> board domain (`mini_depth/read.py:50`, `sites/cold_foundation.py:31`, `sites/ev_foundation.py:36`).
DOMAIN_OF_SITE_TYPE = {"MINIGRID": MINI, "COLDCHAIN": COLD, "EV_CHARGING": EV}
FINDING_INDEX_DOMAIN = "mini-grid-dispatch"
DIESEL_PRICE_KEY = "diesel_price_per_litre"
ASSESSMENT_PAGE = 50  # the cold/EV Finding list default page (`cold_assessment_api.py` DEFAULT_LIMIT)
UNAVAILABLE = "UNAVAILABLE"
#: B-Q27: the Portfolio Grow card's short value (mock `outcomes.js:147`).
GROW_LEAD = "MG-1"
OPPORTUNITY = "OPPORTUNITY"


class PortUnavailable(RuntimeError):
    """A port whose service is not configured (no product database), or whose own gate is closed."""


@dataclass(frozen=True)
class SiteRef:
    """The route's Site record (`ImportedSiteRegistry.imported`): the zone is the stored `site.timezone`."""
    tenant_id: UUID
    site_id: UUID
    site_code: str
    site_name: str
    site_type: str
    timezone: str | None

    @property
    def domain(self) -> str | None:
        return DOMAIN_OF_SITE_TYPE.get(self.site_type)


@dataclass
class BoardServices:
    """The existing services (§B.3 list). Any may be None; its port then raises `PortUnavailable`."""
    # mini
    overview: Any = None              # SiteOverviewRead (site_overview/read.py:114)
    overview_source: Callable[[str, UUID, UUID], tuple[bool, str]] | None = None  # S2 basis + gate, as the route
    mini_depth: Any = None            # MiniDepthRead (mini_depth/read.py:338)
    dispatch: Any = None              # DispatchReadService (analytics/dispatch_read.py:123)
    finding_index: Any = None         # FindingIndexService (analytics/finding_index.py:262)
    performance_gate: Callable[[str, UUID, UUID], tuple[bool, str]] | None = None   # dispatch route gate
    finding_index_gate: Callable[[str, UUID, UUID], tuple[bool, str]] | None = None  # index route gate
    assumptions: Any = None           # AssumptionReadService (financials/assumption_read.py:63)
    action_index: Any = None          # ActionIndexService (actions/site_index.py:160)
    actions: Any = None               # ActionService (actions/service.py:655)
    verification: Any = None          # VerificationService (actions/verification.py:966)
    # cold and EV
    cold_site: Any = None             # ColdSiteReadService (analytics/cold_site_reads.py:314)
    cold_reads: Any = None            # ColdReadService findings (postgres_assessment_store.py:2361)
    ev_site: Any = None               # EvSiteReads (ev_site_reads.py:595)
    ev_reads: Any = None              # EvReadService findings/finding (postgres_assessment_store.py:3342/3352)
    ev_depth: Any = None              # EvDepthReadService (analytics/ev_depth.py)
    domain_actions: Any = None        # DomainActionReadService (work/domain_action_index.py:375)
    # shared
    work_index: Any = None            # site work lists (work/site_index.py:309)
    global_work: Any = None           # PostgresGlobalWorkRead (snapshot) for select_preventive
    select_preventive: Callable[..., list[dict[str, Any]]] | None = None  # work/global_index.py:388
    estate: Any = None                # EstatePortfolioService (site_readiness, site_work_rows)
    parse_finding_index: Callable[..., Any] | None = None   # analytics/finding_index.py:134
    parse_action_index: Callable[..., Any] | None = None    # actions/site_index.py:116
    parse_work_list: Callable[..., Any] | None = None       # work/site_index.py:108
    parse_domain_index: Callable[..., Any] | None = None    # work/domain_action_index.py:86
    action_selector: Callable[[UUID | None, datetime | None], Any] | None = None  # actions/lifecycle.py:146
    access_basis: str = ""            # the Finding-route access basis (finding_api.ACCESS_BASIS)
    work_access_basis: str = ""       # work_api.ACCESS_BASIS


def wire(at: datetime | None) -> str | None:
    """A UTC instant as the routes print it: seconds as `...Z`, microseconds kept when present."""
    if at is None:
        return None
    at = at.astimezone(timezone.utc)
    text = at.strftime("%Y-%m-%dT%H:%M:%S") + (f".{at.microsecond:06d}" if at.microsecond else "")
    return text + "Z"


def _need(service: Any, name: str) -> Any:
    if service is None:
        raise PortUnavailable(f"{name} is not configured")
    return service


def _open(gate: Callable[[str, UUID, UUID], tuple[bool, str]] | None, site: SiteRef, name: str) -> None:
    permitted, reason = _need(gate, name)(site.site_code, site.tenant_id, site.site_id)
    if not permitted:
        raise PortUnavailable(f"{name} closed: {reason}")


def covering_days(lo: datetime, hi: datetime) -> tuple[datetime, datetime]:
    """OUT-B addendum 7: `[floor_utc_day(lo), ceil_utc_day(hi))`. A bound already at midnight is unchanged. The estate
    methods never widen; only the composer does, and the estate then applies its own window rule (over 31 days
    refuses INVALID_WINDOW)."""
    lo, hi = lo.astimezone(timezone.utc), hi.astimezone(timezone.utc)
    floor = lo.replace(hour=0, minute=0, second=0, microsecond=0)
    ceil = hi.replace(hour=0, minute=0, second=0, microsecond=0)
    return floor, (ceil if ceil == hi else ceil + timedelta(days=1))


def mini_summary_day(to: datetime) -> date:
    """B-Q7: the UTC day of the Portfolio `to`, the previous day when `to` is midnight."""
    to = to.astimezone(timezone.utc)
    midnight = (to.hour, to.minute, to.second, to.microsecond) == (0, 0, 0, 0)
    return (to - timedelta(days=1)).date() if midnight else to.date()


WINDOW_BASIS_DAY, WINDOW_BASIS_EVENT, WINDOW_BASIS_PERIOD = "DAY", "LATEST_EVENT", "PERIOD"


def latest_window(windows: list[tuple[datetime, datetime]] | None) -> tuple[datetime, datetime] | None:
    """OUT-W: the latest assessed event inside the period: max window_end, then max window_start. None for None/[]."""
    return max(windows, key=lambda w: (w[1], w[0])) if windows else None


class SiteOutcomeBoardService:
    def __init__(self, services: BoardServices) -> None:
        self.s = services

    # ------------------------------------------------------------------ ports

    def _shared(self, site: SiteRef, known_at: datetime | None, widen: bool = False) -> dict[str, Callable[..., Any]]:
        s, t, sid, c = self.s, site.tenant_id, site.site_id, site.site_code
        known = [] if known_at is None else [wire(known_at)]

        def work(kind: str, lo: datetime, hi: datetime, cursor: str | None) -> dict[str, Any]:
            req = _need(s.parse_work_list, "work parser")(wire(lo), wire(hi), None, known, cursor)
            return jsonable_encoder(_need(s.work_index, "work_index").read(
                t, sid, c, kind, req, access_basis=s.work_access_basis))

        def plans(lo: datetime, hi: datetime) -> list[dict[str, Any]]:
            select = _need(s.select_preventive, "select_preventive")

            def read(gx: Any) -> list[dict[str, Any]]:
                sites = [x for x in gx.imported_sites(t, hi) if str(x["site_id"]).lower() == str(sid).lower()]
                return [r["wire"] for r in select(gx, t, sites, lo, hi, known_at or gx.read_at)]

            return jsonable_encoder(_need(s.global_work, "global_work").snapshot(read))

        def readiness(lo: datetime, hi: datetime) -> str | None:
            if widen:  # cold and EV: the covering UTC days (addendum 7); mini windows are already whole days
                lo, hi = covering_days(lo, hi)
            return _need(s.estate, "estate").site_readiness(t, c, lo, hi, known_at)

        return {"work": work, "plans": plans, "readiness": readiness}

    def _domain_actions(self, site: SiteRef, known_at: datetime | None) -> Callable[..., dict[str, Any]]:
        s = self.s
        known = [] if known_at is None else [wire(known_at)]

        def domain_actions(lo: datetime, hi: datetime, cursor: str | None) -> dict[str, Any]:
            req = _need(s.parse_domain_index, "domain index parser")(wire(lo), wire(hi), None, known, cursor)
            return jsonable_encoder(_need(s.domain_actions, "domain_action_index").index(
                site.tenant_id, site.site_id, site.site_code, req))

        return domain_actions

    def mini_ports(self, site: SiteRef, known_at: datetime | None = None,
                   pin: tuple[UUID, UUID | None] | None = None) -> mini.MiniPorts:
        s, t, sid, c = self.s, site.tenant_id, site.site_id, site.site_code
        shared = self._shared(site, known_at)

        def overview(day: date) -> dict[str, Any]:
            permitted, reason = _need(s.overview_source, "overview source")(c, t, sid)
            return jsonable_encoder(_need(s.overview, "mini_overview").read(
                c, t, sid, day, access_basis=s.access_basis, source_open=bool(permitted), source_reason=reason,
                pinned=pin))

        def depth(domain: str, lo: datetime, hi: datetime) -> dict[str, Any]:
            return jsonable_encoder(_need(s.mini_depth, "mini_depth").read(
                tenant_id=t, site_id=sid, site_code=c, domain=domain, lo=lo, hi=hi, known_at=known_at))

        def dispatch(day: date) -> dict[str, Any]:
            _open(s.performance_gate, site, "performance gate")
            return jsonable_encoder(_need(s.dispatch, "dispatch").window(t, sid, day))

        def assumption(at: datetime) -> dict[str, Any]:
            return jsonable_encoder(_need(s.assumptions, "assumptions").series(
                t, sid, DIESEL_PRICE_KEY, valid_at=at, recorded_at=known_at))  # addendum 4 #4: None = current

        def finding_index(lo: datetime, hi: datetime, cursor: str | None) -> dict[str, Any]:
            _open(s.finding_index_gate, site, "finding index gate")
            req = _need(s.parse_finding_index, "finding index parser")(
                FINDING_INDEX_DOMAIN, wire(lo), wire(hi), None, cursor)
            return jsonable_encoder(_need(s.finding_index, "finding_index").read(
                t, sid, c, req, access_basis=s.access_basis))

        def estate(day_lo: datetime, day_hi: datetime, work_lo: datetime, work_hi: datetime) -> dict[str, Any]:
            rows = _need(s.estate, "estate").site_work_rows(t, c, day_lo, day_hi, work_lo, work_hi, known_at)
            if rows is None:
                raise PortUnavailable("the Site is not in the estate scope")
            return rows

        def action_index(lo: datetime, hi: datetime, cursor: str | None) -> dict[str, Any]:
            req = _need(s.parse_action_index, "action index parser")(wire(lo), wire(hi), None, cursor)
            return jsonable_encoder(_need(s.action_index, "action_index").read(
                t, sid, c, req, access_basis=s.access_basis))

        def verification(action_id: str) -> dict[str, Any]:
            return jsonable_encoder(_need(s.verification, "verification").summary(t, sid, c, UUID(action_id)))

        def action(action_id: str, event_id: str) -> dict[str, Any] | None:
            pick = _need(s.action_selector, "action selector")(UUID(event_id) if event_id else None, None)
            body = _need(s.actions, "action_read").action(t, sid, c, UUID(action_id), pick)
            return None if body is None else jsonable_encoder(body)

        return mini.MiniPorts(overview=overview, depth=depth, dispatch=dispatch, assumption=assumption,
                              finding_index=finding_index, estate=estate, action_index=action_index,
                              verification=verification, action=action, work=shared["work"],
                              plans=shared["plans"], readiness=shared["readiness"])

    def cold_ports(self, site: SiteRef, known_at: datetime | None = None) -> cold.ColdPorts:
        s, t, sid, c = self.s, site.tenant_id, site.site_id, site.site_code
        shared = self._shared(site, known_at, widen=True)

        def overview(lo: datetime | None, hi: datetime | None) -> dict[str, Any]:
            return jsonable_encoder(_need(s.cold_site, "cold_overview").overview(t, sid, c, lo, hi, known_at))

        def findings(lo: datetime, hi: datetime, cursor: str | None) -> dict[str, Any]:
            return jsonable_encoder(_need(s.cold_reads, "cold_findings").findings(
                t, sid, c, lo, hi, known_at, cursor, ASSESSMENT_PAGE))

        return cold.ColdPorts(overview=overview, findings=findings,
                              domain_actions=self._domain_actions(site, known_at), work=shared["work"],
                              plans=shared["plans"], readiness=shared["readiness"])

    def ev_ports(self, site: SiteRef, known_at: datetime | None = None) -> ev.EvPorts:
        s, t, sid, c = self.s, site.tenant_id, site.site_id, site.site_code
        shared = self._shared(site, known_at, widen=True)

        def overview(lo: datetime | None, hi: datetime | None) -> dict[str, Any]:
            return jsonable_encoder(_need(s.ev_site, "ev_overview").overview(t, sid, c, lo, hi, known_at))

        def findings(lo: datetime, hi: datetime, cursor: str | None) -> dict[str, Any]:
            return jsonable_encoder(_need(s.ev_reads, "ev_findings").findings(
                t, sid, c, lo, hi, known_at, cursor, ASSESSMENT_PAGE))

        def finding(finding_id: str, lo: datetime, hi: datetime) -> dict[str, Any] | None:
            body = _need(s.ev_reads, "ev_findings").finding(t, sid, c, UUID(finding_id), lo, hi, known_at)
            return None if body is None else jsonable_encoder(body)

        def health(lo: datetime, hi: datetime) -> dict[str, Any]:
            return jsonable_encoder(_need(s.ev_depth, "ev_depth").health(t, sid, c, lo, hi, known_at))

        def availability(lo: datetime, hi: datetime) -> dict[str, Any]:
            return jsonable_encoder(_need(s.ev_depth, "ev_availability").availability(t, sid, c, lo, hi, known_at))

        return ev.EvPorts(overview=overview, findings=findings, finding=finding, health=health,
                          availability=availability, domain_actions=self._domain_actions(site, known_at),
                          work=shared["work"], plans=shared["plans"], readiness=shared["readiness"])

    # ------------------------------------------------------------------ compose

    def compose(self, site: SiteRef, *, day: date | None = None, lo: datetime | None = None,
                hi: datetime | None = None, known_at: datetime | None = None,
                pin: tuple[UUID, UUID | None] | None = None) -> tuple[mini.MiniComposition, dict[str, Any]]:
        """The domain composition and its window `{from, to}`. Mini takes the overview's UTC `day` (the route
        resolves `selected_day` / `db_today()`); cold and EV take `lo`/`hi` unchanged (B-Q7). With no window, cold
        and EV first read their overview with none, as their pages do, and use the window it resolved."""
        domain = site.domain
        if domain == MINI:
            if day is None:
                day = _need(self.s.overview, "mini_overview").db_today()
            comp = mini.compose(self.mini_ports(site, known_at, pin), site_code=site.site_code, day=day,
                                site_timezone=site.timezone)
            return comp, comp.window
        if domain not in (COLD, EV):
            raise ValueError(f"no outcome board for Site type {site.site_type!r}")
        ports = self.cold_ports(site, known_at) if domain == COLD else self.ev_ports(site, known_at)
        resolved: dict[str, Any] = {}
        if lo is None or hi is None:
            window = (ports.overview(None, None) or {}).get("window") or {}
            resolved["known_at"] = window.get("known_at")
            lo, hi = mini.utc(window.get("from")), mini.utc(window.get("to"))
            if lo is None or hi is None:
                raise PortUnavailable("the overview resolved no window")
        read_overview = ports.overview

        def overview(a: datetime | None, b: datetime | None) -> dict[str, Any]:
            body = read_overview(a, b)
            resolved["known_at"] = ((body or {}).get("window") or {}).get("known_at")
            return body

        composer = cold.compose if domain == COLD else ev.compose
        comp = composer(replace(ports, overview=overview), site_code=site.site_code, lo=lo, hi=hi,
                        site_timezone=site.timezone)
        # addendum 4 #5: the cutoff used is the request's; without one, the overview body's resolved cutoff
        cutoff = known_at if known_at is not None else mini.utc(resolved.get("known_at"))
        return comp, {"from": lo, "to": hi, "known_at": cutoff}

    def board(self, site: SiteRef, *, day: date | None = None, lo: datetime | None = None,
              hi: datetime | None = None, known_at: datetime | None = None,
              pin: tuple[UUID, UUID | None] | None = None) -> dict[str, Any]:
        comp, window = self.compose(site, day=day, lo=lo, hi=hi, known_at=known_at, pin=pin)
        query = {"from": wire(window["from"]), "to": wire(window["to"])}
        if known_at is not None:
            query["known_at"] = wire(known_at)
        if pin is not None:
            query["finding_id"] = str(pin[0])
            if pin[1] is not None:
                query["finding_revision_id"] = str(pin[1])
        return {
            "schema_version": SCHEMA_VERSION, "policy_versions": dict(POLICY_VERSIONS),
            "site_code": site.site_code, "site_id": str(site.site_id), "site_name": site.site_name,
            "domain": site.domain,
            "window": {"from": wire(window["from"]), "to": wire(window["to"]),
                       "known_at": wire(window.get("known_at", known_at))},
            "read_state": comp.read_state,
            "rows": jsonable_encoder(assemble(comp.facts)),
            "warnings": jsonable_encoder([w.wire(site.site_code, site.site_name) for w in comp.facts.warnings]),
            "links": {"self": f"/api/sites/{site.site_code}/outcome-board?{urlencode(query)}"},
            "_short_values": dict(comp.short_values),  # stripped by the route; read by the estate summary
        }

    # ------------------------------------------------------------------ estate summary

    def _event_window(self, site: SiteRef, lo: datetime, hi: datetime,
                      known_at: datetime | None) -> tuple[datetime, datetime] | None:
        """OUT-W: the latest selected window of a cold or EV Site inside `[lo, hi)`, by the Evidence root's rule.
        Any failure (unconfigured estate, refusal, store error) is None: the window choice never fails a Site."""
        try:
            return latest_window(_need(self.s.estate, "estate").site_selected_windows(
                site.tenant_id, site.site_code, lo, hi, known_at))
        except Exception:  # noqa: BLE001 - falls back to the period, which reads Unknown where nothing covers it
            return None

    def summary(self, sites: list[SiteRef], lo: datetime, hi: datetime,
                known_at: datetime | None = None) -> dict[str, Any]:
        """`GET /api/estate/outcome-summary` (§B.1): one board per authorized Site, serially (B-Q8), in the
        Portfolio Site order the caller passes. Mini reads the UTC day of `to` (B-Q7); cold and EV `from`/`to`
        unchanged. A Site whose board read fails is UNAVAILABLE with four UNKNOWN rows."""
        out = []
        warnings: list[dict[str, Any]] = []  # C: each Site's board warnings, in Site order; a failed Site adds none
        for site in sites:
            # OUT-W (P-C1 option A): a cold or EV Site is judged on its latest assessed event inside the period;
            # with none, or when the window choice fails, on the period itself. Mini reads its UTC day (B-Q7).
            if site.domain == MINI:
                basis, b_day, b_lo, b_hi = WINDOW_BASIS_DAY, mini_summary_day(hi), None, None
            else:
                ev_win = self._event_window(site, lo, hi, known_at)
                basis = WINDOW_BASIS_PERIOD if ev_win is None else WINDOW_BASIS_EVENT
                b_day, (b_lo, b_hi) = None, ((lo, hi) if ev_win is None else ev_win)
            try:
                body = self.board(site, day=b_day, lo=b_lo, hi=b_hi, known_at=known_at)
                rows = [_summary_row(r, body["_short_values"]) for r in body["rows"]]
                read_state = body["read_state"]
                warnings += body["warnings"]
                window: dict[str, Any] | None = body["window"]
                window_basis: str | None = basis
            except Exception:  # noqa: BLE001 - one Site's failure never refuses the summary (§B.1)
                rows = [_unknown_row(cat) for cat in CATEGORIES]
                read_state = UNAVAILABLE
                window, window_basis = None, None
            href = _overview_href(site, window if window_basis == WINDOW_BASIS_EVENT else None, known_at)
            out.append({"site_id": str(site.site_id), "site_code": site.site_code, "site_name": site.site_name,
                        "domain": site.domain, "overview_href": href, "read_state": read_state,
                        "rows": rows, "window": window, "window_basis": window_basis})
        categories = [{"category": cat, "label": CATEGORY_LABEL[cat], "definition": CATEGORY_DEFINITION[cat],
                       "icon": CATEGORY_ICON[cat],
                       "sites_needing_attention": sum(1 for x in out for r in x["rows"]
                                                      if r["category"] == cat and r["state"] == NEEDS_ATTENTION),
                       "warning_count": sum(1 for w in warnings
                                            if any(i["category"] == cat for i in w["categories"]["items"]))}
                      for cat in CATEGORIES]
        return {"schema_version": SUMMARY_SCHEMA_VERSION, "policy_versions": dict(POLICY_VERSIONS),
                "window": {"from": wire(lo), "to": wire(hi)}, "sites": out, "categories": categories,
                "warnings": warnings}


def _overview_href(site: SiteRef, window: dict[str, Any] | None = None, known_at: datetime | None = None) -> str:
    """The `estate/evidence_money.py` `site_home_href` rule: EV Sites open at `/sites/{code}/ev`. OUT-W: with the
    event window the Site was judged on, the link opens the Site on it (`known_at` only when the request had one)."""
    base = f"/sites/{site.site_code}/ev" if site.domain == EV else f"/sites/{site.site_code}"
    if window is None:
        return base
    query = [("from", window["from"]), ("to", window["to"])]
    if known_at is not None:
        query.append(("known_at", wire(known_at)))
    return base + "?" + urlencode(query)


def _summary_row(row: dict[str, Any], short_values: dict[str, str]) -> dict[str, Any]:
    lead = row.get("lead_outcome") or {}
    short = (short_values.get(row["category"]) if lead.get("key") == GROW_LEAD and row["state"] == OPPORTUNITY
             else None)
    return {"category": row["category"], "state": row["state"], "state_label": row["state_label"],
            "tone": row["tone"], "lead_outcome": row.get("lead_outcome"), "headline": row.get("headline"),
            "short_value": short}


def _unknown_row(category: str) -> dict[str, Any]:
    return {"category": category, "state": UNKNOWN, "state_label": STATE_LABEL[UNKNOWN], "tone": STATE_TONE[UNKNOWN],
            "lead_outcome": None, "headline": None, "short_value": None}
