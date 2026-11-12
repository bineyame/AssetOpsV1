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

import logging
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import date, datetime, timezone
from typing import Any, Callable
from urllib.parse import urlencode
from uuid import UUID

from fastapi.encoders import jsonable_encoder

from assetops_backend import perf, read_scope
from assetops_backend.analytics.finding_index import DOMAINS as FINDING_INDEX_DOMAINS
from assetops_backend.analytics.finding_index import POLICY_VERSION as FINDING_INDEX_POLICY
from assetops_backend.chain.outcomes import site_nodes
from assetops_backend.chain.read import (SITE_TYPE_OF_DOMAIN, lifecycle_cutoff, local_days, site_cutoff, window_day,
                                         window_days)
from assetops_backend.chain.read import board_day as local_board_day
from assetops_backend.chain.claims import (SITES_DISRUPTED, VERIFIED_RESULTS, EstateCounts, estate_count_claims,
                                           opportunity_items)
from assetops_backend.chain.vocabulary import (CHECKED_DAYS_BASIS, COST_SMALL, INCOME_LABELS, NOT_KNOWN_TEXT,
                                               card_text, count_card_value, day_counts, days_line, estate_income,
                                               money_text, node_text, sites_text)
from assetops_backend.outcomes.catalogue import (
    CATALOGUE_VERSION, CATEGORIES, CATEGORY_DEFINITION, CATEGORY_ICON, CATEGORY_LABEL, COLD, EV, MINI,
    SITE_OUTCOMES)
from assetops_backend.outcomes.credit import MONEY_NOT_CREDITED
from assetops_backend.outcomes.objectives import POLICY as OBJECTIVES_POLICY
from assetops_backend.outcomes.outcome_map import POLICY_VERSION
from assetops_backend.outcomes.status import NEEDS_ATTENTION, STATE_LABEL, STATE_TONE, STATUS_POLICY, UNKNOWN
from assetops_backend.outcomes.warnings import POLICY as WARNINGS_POLICY
from assetops_backend.site_outcomes import cold, ev, mini
from assetops_backend.site_outcomes.board import assemble, objectives_wire, with_threads

SCHEMA_VERSION = "site-outcome-board-1"
SUMMARY_SCHEMA_VERSION = "estate-outcome-summary-1"
LOG = logging.getLogger(__name__)

POLICY_VERSIONS = {"catalogue": CATALOGUE_VERSION, "outcome_map": POLICY_VERSION, "status": STATUS_POLICY,
                   "warnings": WARNINGS_POLICY, "objectives": OBJECTIVES_POLICY,
                   "finding_index": FINDING_INDEX_POLICY}
#: Stored Site type -> board domain (`mini_depth/read.py:50`, `sites/cold_foundation.py:31`, `sites/ev_foundation.py:36`).
DOMAIN_OF_SITE_TYPE = {"MINIGRID": MINI, "COLDCHAIN": COLD, "EV_CHARGING": EV}
FINDING_INDEX_DOMAIN = "mini-grid-dispatch"
#: CH5a1-R Q6: the index's (Finding domain, analytic) scope, read by `ChainRequest.findings`.
FINDING_SCOPE = FINDING_INDEX_DOMAINS[FINDING_INDEX_DOMAIN]
DIESEL_PRICE_KEY = "diesel_price_per_litre"
PRODUCTIVE_PRICE_KEY = "productive_use_price_per_kwh"  # WALK1-3 §4.1 (financials/assumptions.py)
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
    objectives: Any = None            # PostgresObjectiveStore.current (OUT-D U3)
    threads: Any = None               # CH-2: PostgresThreadSources.lookup (chain/adapters/postgres_thread_sources.py)
    chain_reader: Any = None          # CH-5a1: ChainReader (chain/read.py), one `request` per board read
    thread_policy: Callable[[], Any] | None = None  # MB-1a-R2: chain.composition.thread_lifecycle_policy (composition.py injects it; OUT-B4)
    # shared
    work_index: Any = None            # site work lists (work/site_index.py:309)
    global_work: Any = None           # PostgresGlobalWorkRead (snapshot) for select_preventive
    select_preventive: Callable[..., list[dict[str, Any]]] | None = None  # work/global_index.py:388
    estate: Any = None                # EstatePortfolioService (site_readiness, site_work_rows)
    parse_action_index: Callable[..., Any] | None = None    # actions/site_index.py:116
    parse_work_list: Callable[..., Any] | None = None       # work/site_index.py:108
    parse_domain_index: Callable[..., Any] | None = None    # work/domain_action_index.py:86
    action_selector: Callable[[UUID | None, datetime | None], Any] | None = None  # actions/lifecycle.py:146
    access_basis: str = ""            # the Finding-route access basis (finding_api.ACCESS_BASIS)
    work_access_basis: str = ""       # work_api.ACCESS_BASIS
    fuel_balance: Any = None          # PostgresFuelBalanceStore (DIESEL-1-R3j2; K4b's fuel_windows/fuel_findings/has_windows)


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


#: CH6b1-R Q2 (R14): mini Sites are judged on `window_day`, every other Site on the requested window (PERIOD).
WINDOW_BASIS_DAY, WINDOW_BASIS_PERIOD = "DAY", "PERIOD"
PROTECT_CATEGORY = cold.PROTECT
_MISS = object()   # CH6b1-R3: "no windows were read for this Site" (the board reads its own)


def contained_windows(windows: list[dict[str, Any]] | None, lo: datetime, hi: datetime) -> list[dict[str, Any]]:
    """CH6b1-R3: the selected evidence windows lying INSIDE `[lo, hi)` (`lo <= start`, `end <= hi`). The estate read
    returns every window that intersects; one that reaches outside the requested window is never read."""
    return [w for w in windows or () if lo <= w["window_start"] and w["window_end"] <= hi]


def latest_contained_window(windows: list[dict[str, Any]] | None) -> tuple[datetime, datetime] | None:
    """The latest assessed event of `windows`: overlapping windows chain into one event (touching ends are
    separate); the event with the latest end wins; inside it the most recently selected window (selected_at, seq,
    selection_id). None for None/[]."""
    if not windows:
        return None
    events: list[list[dict[str, Any]]] = []
    for w in sorted(windows, key=lambda w: (w["window_start"], w["window_end"])):
        if events and w["window_start"] < max(x["window_end"] for x in events[-1]):
            events[-1].append(w)
        else:
            events.append([w])
    event = max(events, key=lambda e: (max(x["window_end"] for x in e), min(x["window_start"] for x in e)))
    best = max(event, key=lambda w: (w["selected_at"], w["seq"], str(w["selection_id"])))
    return best["window_start"], best["window_end"]
#: CH6b1-R Q4: the earnings claim keys that are Portfolio income (`INCOME_LABELS`).
INCOME_KEYS = tuple(f"money.{label}" for label in INCOME_LABELS)


class SiteOutcomeBoardService:
    def __init__(self, services: BoardServices) -> None:
        self.s = services

    # ------------------------------------------------------------------ ports

    def _shared(self, site: SiteRef, known_at: datetime | None) -> dict[str, Callable[..., Any]]:
        s, t, sid, c = self.s, site.tenant_id, site.site_id, site.site_code
        known = [] if known_at is None else [wire(known_at)]

        prefetched: dict[tuple[str, datetime, datetime], dict[str, Any]] = {}

        def work(kind: str, lo: datetime, hi: datetime, cursor: str | None) -> dict[str, Any]:
            if cursor is None and (kind, lo, hi) in prefetched:
                return prefetched.pop((kind, lo, hi))
            if cursor is None and kind == "incidents" and not prefetched:
                prefetched.update(_work_batch(hi))
                if (kind, lo, hi) in prefetched:
                    return prefetched.pop((kind, lo, hi))
            req = _need(s.parse_work_list, "work parser")(wire(lo), wire(hi), None, known, cursor)
            return jsonable_encoder(_need(s.work_index, "work_index").read(
                t, sid, c, kind, req, access_basis=s.work_access_basis))

        def _work_batch(to: datetime) -> dict[tuple[str, datetime, datetime], dict[str, Any]]:
            """ANY-2 AR-6: the board's four first-page work-index reads (incidents over the 31-day work window, the
            three maintenance recorded-time windows of `visits.record_windows`) in ONE snapshot; each body equals
            that read on its own at the same instant. Any failure leaves nothing prefetched and the four reads run
            one by one exactly as before (their own failure handling)."""
            from assetops_backend.site_outcomes.visits import record_windows

            specs = [("incidents", to - mini.WORK_WINDOW, to), *(("maintenance", a, b) for a, b in record_windows(to))]
            service = s.work_index
            if service is None or s.parse_work_list is None or not hasattr(service, "read_many"):
                return {}
            try:
                reqs = [(kind, s.parse_work_list(wire(a), wire(b), None, known, None)) for kind, a, b in specs]
                bodies = service.read_many(t, sid, c, reqs, access_basis=s.work_access_basis)
            except Exception:  # noqa: BLE001 - B.3: the single reads below own the refusal and its PARTIAL board
                return {}
            return {spec: jsonable_encoder(body) for spec, body in zip(specs, bodies)}

        def plans(lo: datetime, hi: datetime) -> list[dict[str, Any]]:
            select = _need(s.select_preventive, "select_preventive")

            def read(gx: Any) -> list[dict[str, Any]]:
                sites = [x for x in gx.imported_sites(t, hi) if str(x["site_id"]).lower() == str(sid).lower()]
                return [r["wire"] for r in select(gx, t, sites, lo, hi, known_at or gx.read_at)]

            return jsonable_encoder(_need(s.global_work, "global_work").snapshot(read))

        def readiness(lo: datetime, hi: datetime) -> str | None:
            """CH-5a1 R5 (CH5a1-R Q8): `readiness_of` pooled over every Site-local day `[lo, hi)` intersects."""
            req = _need(s.chain_reader, "chain reader").request(t, known_at)
            return req.day(sid, SITE_TYPE_OF_DOMAIN[site.domain], local_days(lo, hi, site.timezone)).readiness

        def chain_rows(lo: datetime, hi: datetime) -> tuple[Any, ...]:
            """CH-6a3: the snapshot rows of the same memoised day read (no new statement)."""
            req = _need(s.chain_reader, "chain reader").request(t, known_at)
            return tuple(req.day(sid, SITE_TYPE_OF_DOMAIN[site.domain], local_days(lo, hi, site.timezone)).rows)

        return {"work": work, "plans": plans, "readiness": readiness, "chain_rows": chain_rows,
                "objectives": lambda: _need(s.objectives, "objectives").current(t, sid, known_at)}

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

        def chain() -> Any:
            return _need(s.chain_reader, "chain reader").request(t, known_at)

        def source() -> tuple[bool, str]:  # R4: the overview's source gate, without the overview read
            permitted, reason = _need(s.overview_source, "overview source")(c, t, sid)
            return bool(permitted), reason

        def chain_day(days: tuple[date, ...], board_days: tuple[date, ...]) -> Any:
            return chain().day(sid, SITE_TYPE_OF_DOMAIN[MINI], days, board_days)

        def chain_findings(lo: datetime, hi: datetime) -> Any:
            _open(s.finding_index_gate, site, "finding index gate")
            return chain().findings(sid, *FINDING_SCOPE, lo, hi)

        def findings_settled() -> bool:
            return chain().findings_settled(sid)

        def readings_began() -> datetime | None:  # PB-7
            return chain().readings_began(sid)

        def action_facts(action_ids: list[str]) -> Any:
            return chain().action_facts(sid, c, action_ids)

        def money(fid: str, rid: str, is_latest: bool, source_open: bool, settled: bool) -> Any:
            return chain().money_head(sid, fid, rid, is_latest=is_latest, source_open=source_open, settled=settled)

        def depth(domain: str, lo: datetime, hi: datetime) -> dict[str, Any]:
            return jsonable_encoder(_need(s.mini_depth, "mini_depth").read(
                tenant_id=t, site_id=sid, site_code=c, domain=domain, lo=lo, hi=hi, known_at=known_at))

        def dispatch(day: date) -> dict[str, Any]:
            _open(s.performance_gate, site, "performance gate")
            return jsonable_encoder(_need(s.dispatch, "dispatch").window(t, sid, day))

        def assumption(at: datetime) -> dict[str, Any]:
            return jsonable_encoder(_need(s.assumptions, "assumptions").series(
                t, sid, DIESEL_PRICE_KEY, valid_at=at, recorded_at=known_at))  # addendum 4 #4: None = current

        # CH-5a2b R1: the chip's placement facts and the labels' Action rows from the ChainReader (the estate
        # snapshot read is gone from the board).
        def placement_facts(revision_ids: list[str]) -> Any:
            return chain().placement_facts(sid, revision_ids)

        def action_rows() -> Any:
            return chain().action_rows(sid)

        def action_index(lo: datetime, hi: datetime, cursor: str | None) -> dict[str, Any]:
            req = _need(s.parse_action_index, "action index parser")(wire(lo), wire(hi), None, cursor)
            return jsonable_encoder(_need(s.action_index, "action_index").read(
                t, sid, c, req, access_basis=s.access_basis))

        # WALK1-3 §4.3: the productive users, their measured use and the declared productive-use price. The SQL
        # lives in the read-only mini-depth reader (`mini_depth/read.py`); the price is the diesel series read.
        def productive_users(at: datetime) -> list[dict[str, Any]]:
            return _need(s.mini_depth, "mini_depth").productive_users(
                tenant_id=t, site_id=sid, at=at, known_at=known_at)

        def productive_readings(asset_ids: list[Any], lo: datetime, hi: datetime) -> list[dict[str, Any]]:
            return _need(s.mini_depth, "mini_depth").productive_readings(
                tenant_id=t, site_id=sid, asset_ids=asset_ids, lo=lo, hi=hi, known_at=known_at)

        def productive_price(at: datetime) -> dict[str, Any]:
            return jsonable_encoder(_need(s.assumptions, "assumptions").series(
                t, sid, PRODUCTIVE_PRICE_KEY, valid_at=at, recorded_at=known_at))

        # CH9-R4 F2: the Portfolio's opportunity read (CH-4 `opportunity_threads`); no thread port = no items.
        def opportunity(lo: datetime, hi: datetime) -> Any:
            return [] if s.threads is None else s.threads.opportunity_threads(t, [sid], lo, hi, known_at)

        # MB-1-R Q1(c): the Site's thread rows at the request cutoff (memoised with the claims' read), that cutoff
        # and the lifecycle policy (`BoardServices.thread_policy`, None when not injected); None without a chain reader (no opportunity Actions).
        def chain_threads() -> Any:
            if s.chain_reader is None:
                return None
            req = chain()
            return mini.ChainThreads(req.threads(sid), req.k, None if s.thread_policy is None else s.thread_policy())

        # PV-1-R §1: the verdict page's own `value` of a VERIFIED mill Action (MV-1), through the injected service.
        def verdict_value(action_id: str) -> Any:
            return jsonable_encoder(_need(s.verification, "verification").domain_summary(t, sid, UUID(action_id))["value"])

        # DIESEL-1-R3j2 §9j2.5 item 1: the fuel-balance store's reads as known at the board cutoff (None = the store's
        # own read instant). No store: each port raises `PortUnavailable`, recorded by `Reads` (PARTIAL; MG-8 UNKNOWN).
        fuel_ctx: dict[str, Any] = {}

        def fuel_context() -> tuple[str | None, datetime]:
            if not fuel_ctx:
                _tz, tank, now = _need(s.fuel_balance, "fuel_balance").night_context(t, sid)
                fuel_ctx.update(tank=tank, k=known_at if known_at is not None else now)
            return fuel_ctx["tank"], fuel_ctx["k"]

        def fuel_has_windows() -> bool:
            _tank, k = fuel_context()
            return bool(_need(s.fuel_balance, "fuel_balance").has_windows(t, sid, k))

        def fuel_windows(lo: date, hi: date) -> Any:
            tank, k = fuel_context()
            return () if tank is None else _need(s.fuel_balance, "fuel_balance").windows(t, sid, UUID(tank), lo, hi, k)

        def fuel_findings(lo: datetime, hi: datetime) -> Any:
            _tank, k = fuel_context()  # R3j3 L1: the same cutoff as the window reads
            return _need(s.fuel_balance, "fuel_balance").fuel_findings(t, sid, lo, hi, k)

        return mini.MiniPorts(source=source, depth=depth, dispatch=dispatch, assumption=assumption,
                              chain_day=chain_day, chain_findings=chain_findings, findings_settled=findings_settled,
                              readings_began=readings_began,
                              placement_facts=placement_facts, action_rows=action_rows, action_index=action_index, action_facts=action_facts, money=money,
                              work=shared["work"], plans=shared["plans"], objectives=shared["objectives"],
                              pin=pin, productive_users=productive_users,
                              productive_readings=productive_readings, productive_price=productive_price,
                              opportunity=opportunity, chain_threads=chain_threads, verdict_value=verdict_value,
                              fuel_windows=fuel_windows, fuel_findings=fuel_findings,
                              fuel_has_windows=fuel_has_windows)

    def cold_ports(self, site: SiteRef, known_at: datetime | None = None) -> cold.ColdPorts:
        s, t, sid, c = self.s, site.tenant_id, site.site_id, site.site_code
        shared = self._shared(site, known_at)

        def overview(lo: datetime | None, hi: datetime | None) -> dict[str, Any]:
            return jsonable_encoder(_need(s.cold_site, "cold_overview").overview(t, sid, c, lo, hi, known_at))

        def findings(lo: datetime, hi: datetime, cursor: str | None) -> dict[str, Any]:
            return jsonable_encoder(_need(s.cold_reads, "cold_findings").findings(
                t, sid, c, lo, hi, known_at, cursor, ASSESSMENT_PAGE))

        def finding(finding_id: str, lo: datetime, hi: datetime) -> dict[str, Any] | None:
            # FX-COLD-LINKED (D-E5.8): by id at `known_at`, never filtered by the selected assessment or window
            body = _need(s.cold_reads, "cold_findings").linked_finding(t, sid, c, UUID(finding_id), known_at)
            return None if body is None else jsonable_encoder(body)

        return cold.ColdPorts(overview=overview, findings=findings, finding=finding,
                              domain_actions=self._domain_actions(site, known_at), work=shared["work"],
                              plans=shared["plans"], readiness=shared["readiness"], objectives=shared["objectives"],
                              chain_rows=shared["chain_rows"])

    def ev_ports(self, site: SiteRef, known_at: datetime | None = None) -> ev.EvPorts:
        s, t, sid, c = self.s, site.tenant_id, site.site_id, site.site_code
        shared = self._shared(site, known_at)

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
                          work=shared["work"], plans=shared["plans"], readiness=shared["readiness"],
                          objectives=shared["objectives"], chain_rows=shared["chain_rows"])

    # ------------------------------------------------------------------ compose

    def event_window(self, site: SiteRef, lo: datetime, hi: datetime, known_at: datetime | None,
                     windows: Any = _MISS) -> tuple[datetime, datetime] | None:
        """CH6b1-R3: the latest selected evidence window of a cold or EV Site that lies inside `[lo, hi)`. `windows`
        are the summary's batch read for this Site (`_MISS`: read this Site's own). None = nothing contained, or the
        read failed (counted `summary.window_fallback` and logged): the composers then read `[lo, hi)` itself, so
        a Site with no contained event shows their none or not-known state and nothing outside `[lo, hi)` is read."""
        try:
            if windows is _MISS:
                windows = _need(self.s.estate, "estate").site_selected_windows(
                    site.tenant_id, site.site_code, lo, hi, known_at)
            return latest_contained_window(contained_windows(windows, lo, hi))
        except Exception as error:  # noqa: BLE001 - the window choice never fails a Site
            read_scope.note_failure("site_selected_windows", error)
            perf.record("summary.window_fallback", 0.0)
            LOG.warning("outcome board: contained windows for %s fell back to the requested window (%s)",
                        site.site_code, type(error).__name__)
            return None

    def compose(self, site: SiteRef, *, day: date | None = None, lo: datetime | None = None,
                hi: datetime | None = None, known_at: datetime | None = None,
                pin: tuple[UUID, UUID | None] | None = None,
                windows: Any = _MISS) -> tuple[mini.MiniComposition, dict[str, Any]]:
        """The domain composition and its window `{from, to}`. Mini takes the Site-local board `day` (R6; the
        route resolves `selected_day` / `db_today()`); cold and EV take `lo`/`hi` unchanged (B-Q7). With no window, cold
        and EV first read their overview with none, as their pages do, and use the window it resolved."""
        domain = site.domain
        if domain == MINI:
            if day is None:
                day = _need(self.s.overview, "mini_overview").db_today()
            comp = mini.compose(self.mini_ports(site, known_at, pin), site_code=site.site_code, day=day,
                                site_timezone=site.timezone)
            # Review L1: the mini read resolves no cutoff of its own (its producers read "as known now"), so its
            # cutoff is the request's, else None = as known now; passed explicitly, by the same helper as cold/EV.
            return comp, {**comp.window, "known_at": board_cutoff(domain, known_at, None)}
        if domain not in (COLD, EV):
            raise ValueError(f"no outcome board for Site type {site.site_type!r}")
        ports = self.cold_ports(site, known_at) if domain == COLD else self.ev_ports(site, known_at)
        composer = cold.compose if domain == COLD else ev.compose
        # CH6b1-R3: over a requested window the evidence is the latest selected window INSIDE it (its facts, findings,
        # cost and repeat warning); the board's window stays the requested one. With no window the overview resolves it.
        event = self.event_window(site, lo, hi, known_at, windows) if lo is not None and hi is not None else None
        read_lo, read_hi = event if event is not None else (lo, hi)
        # DD1b1-R2: the Action read runs to the REQUESTED end, not the event's (an Action follows its evidence)
        actions_to = hi if event is not None else None
        r_lo, r_hi, cutoff, comp = self.cold_ev_cutoff(
            site, ports, read_lo, read_hi, known_at,
            lambda p, a, b: composer(p, site_code=site.site_code, lo=a, hi=b, site_timezone=site.timezone,
                                     actions_to=actions_to))
        if event is None:
            lo, hi = r_lo, r_hi
        elif event[1] - event[0] < hi - lo:   # CH6b1-R5: a longer window names the event's own date and time
            lead = comp.facts.headline.get(PROTECT_CATEGORY)
            if lead is not None:
                dated = cold.dated_lead(lead, event, mini.site_zone(site.timezone))
                comp = replace(comp, facts=replace(comp.facts, headline={**comp.facts.headline, PROTECT_CATEGORY: dated}))
        return comp, {"from": lo, "to": hi, "known_at": cutoff}

    @staticmethod
    def cold_ev_cutoff(site: SiteRef, ports: Any, lo: datetime | None, hi: datetime | None,
                       known_at: datetime | None, use: Callable[[Any, datetime, datetime], Any] | None = None
                       ) -> tuple[datetime, datetime, datetime | None, Any]:
        """CH5a2b-R Q11 (review L3): the ONE cold/EV cutoff resolution, used by the board (`compose`), never copied (the thread route reads lifecycle at `lifecycle_cutoff`). Without a window, the overview's default window
        (`ports.overview(None, None)`); then the overview read over `[lo, hi)` (inside `use`, the composer, when
        given; else read once here), and `board_cutoff` over that body's `window.known_at` (addendum 4 #5: the
        request's cutoff, else the overview's resolved one). Returns `(lo, hi, cutoff, use's result)`."""
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

        out = use(replace(ports, overview=overview), lo, hi) if use is not None else overview(lo, hi)
        return lo, hi, board_cutoff(site.domain, known_at, resolved.get("known_at")), out

    def board(self, site: SiteRef, *, day: date | None = None, lo: datetime | None = None,
              hi: datetime | None = None, known_at: datetime | None = None,
              pin: tuple[UUID, UUID | None] | None = None,
              node_days: tuple[date, ...] | None = None, windows: Any = _MISS) -> dict[str, Any]:
        """The board body. `node_days` (the estate summary only, CH6b1-R Q1) adds `_window`: the rows' nodes and the
        Site's income earnings re-evaluated over those Site-local days; the board route never passes it."""
        comp, window = self.compose(site, day=day, lo=lo, hi=hi, known_at=known_at, pin=pin, windows=windows)
        # CH-3 §5: the thread state is read on the board's Site-local day; mini boards take their overview day, cold
        # and EV the window's last day. CH6b2-R2, D-E3b.1 (E4-C5): the lifecycle is read as known at the REQUEST's
        # cutoff `k` (`lifecycle_cutoff`, as `/chain` and the Portfolio do), never at the evidence cutoff: a Finding is
        # known after the evidence it assesses, so the evidence cutoff hides its OPEN and any Action agreed after it.
        # The evidence (facts.known_at, every evidence read) stays at `cutoff`; time-travel honesty is the state day.
        # Visibility is bitemporal on each event's cause time (CH3-R D-b, 0045), so a backfilled event whose cause
        # was recorded by the story cutoff shows, and one whose cause was recorded at build time stays hidden.
        cutoff = window.get("known_at")  # `board_cutoff`, resolved by `compose` for every domain (review L1)
        # R6, CH5a2-R R7: every board's day is `window_day` of its window (mini: the board day D), the rule the
        # summary card reads.
        start, end = mini.utc(window.get("from")), mini.utc(window.get("to"))
        board_day = window_day(start, end, site.timezone)
        if self.s.threads is not None:  # CH-2 §5.2: one thread lookup per board; no thread port = no threads
            # CH6a3-R2 M4: a days line may name the board day only when the window is exactly that Site-local day.
            one_day = board_day is not None and (start, end) == local_board_day(board_day, site.timezone)
            wd = window_days(start, end, site.timezone) if start is not None and end is not None else ()
            facts = replace(comp.facts, day=board_day, known_at=cutoff, one_day=one_day,
                            window_span=(wd[0], wd[-1]) if wd else None)
            extra: dict[str, Any] = {}
            if site.domain == MINI and start is not None:  # CH-4 §4.4: the renewable five days of the board
                try:
                    extra = {"site_id": site.site_id,
                             "opportunity_window": mini.renewable_bounds(start, site.timezone)}
                except mini.MiniInputsRefused:
                    extra = {}
            comp = replace(comp, facts=with_threads(facts, self.s.threads.lookup(
                site.tenant_id, [f.finding_id for f in facts.findings], [a.action_id for a in facts.actions],
                day=board_day, known_at=lifecycle_cutoff(known_at), visible_at=known_at,  # R-1: request bounds visibility
                **extra)))
        extra_body = {} if node_days is None else {"_window": self._window_parts(site, comp, node_days, known_at)}
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
            "objectives": jsonable_encoder(objectives_wire(comp.facts)),
            "objectives_read": comp.facts.objectives_ok,
            "finding_gaps": jsonable_encoder(comp.facts.finding_gaps),
            "warnings": jsonable_encoder([w.wire(site.site_code, site.site_name) for w in comp.facts.warnings]),
            "links": {"self": f"/api/sites/{site.site_code}/outcome-board?{urlencode(query)}"},
            "_short_values": dict(comp.short_values),  # stripped by the route; read by the estate summary
            # WALK1-1 (WN-1): stripped by the route like `_short_values`. No production reader remains: the estate
            # Assure card's verified count is the chain claim's value (K6c), not this board sum.
            # MB-1-R Q5: plus the opportunity-origin domain Actions (the mill), the Assure headline's number.
            "_verified_results": sum(1 for a in comp.facts.actions if a.verification_state == "VERIFIED")
            + sum(1 for o in comp.facts.opportunity_actions if o.outcome == "VERIFIED")
            # DIESEL-1-R3u: plus the fuel verdicts (FUEL_BALANCE domain Actions), as the Assure headline counts them.
            + sum(1 for f in comp.facts.fuel_verdicts if f.outcome == "VERIFIED"),
            **extra_body,
        }

    def _window_parts(self, site: SiteRef, comp: Any, node_days: tuple[date, ...],
                      known_at: datetime | None) -> dict[str, Any]:
        """CH6b1-R Q1/Q4: the composer's `NodeInputs` re-evaluated over `node_days` (`window_days`, the frame of the
        Site's `days`), with the snapshot rows of those days (the memoised `claim_days` read) merged into the
        composer's rows (same statement shape and cutoff, so one row per key). Returns `{"nodes": {category: row
        nodes}, "earnings": {label: claim}}`: the rows' nodes by `assemble` (lead and server fills as the board),
        and every outcome's income earnings claim that comes from a record (server fills are never earnings)."""
        inp = getattr(comp, "node_inputs", None)
        if inp is None or not node_days:
            return {"nodes": {}, "earnings": {}}
        extra: tuple[Any, ...] = ()
        if self.s.chain_reader is not None:   # no reader: the composer's rows only (its own read failed the same)
            req = self.s.chain_reader.request(site.tenant_id, known_at)
            extra = req.day(site.site_id, SITE_TYPE_OF_DOMAIN[site.domain], node_days).rows
        rows = {(r.measure, r.local_day, getattr(r, "subject_kind", None), r.subject_ref): r
                for r in (*inp.rows, *extra)}
        nodes = site_nodes(replace(inp, window=(node_days[0], node_days[-1]), rows=tuple(rows.values())),
                           [o.key for o in SITE_OUTCOMES if o.domain == site.domain])
        facts = replace(comp.facts, nodes=nodes, day=node_days[-1], one_day=len(node_days) == 1,
                        window_span=(node_days[0], node_days[-1]))
        earnings = {}
        for per in nodes.values():
            claim = (per or {}).get("earnings")
            if claim is not None and claim["key"] in INCOME_KEYS:
                earnings.setdefault(claim["key"].removeprefix("money."), claim)
        return {"nodes": {r["category"]: r.get("nodes") for r in jsonable_encoder(assemble(facts))},
                "earnings": earnings}

    # ------------------------------------------------------------------ estate summary

    def summary(self, sites: list[SiteRef], lo: datetime, hi: datetime,
                known_at: datetime | None = None) -> dict[str, Any]:
        """`GET /api/estate/outcome-summary` (§B.1): one board per authorized Site, serially (B-Q8), in the
        Portfolio Site order the caller passes, after ONE snapshot read for every Site (`seed_snapshots`). Mini
        reads `window_day` (DAY); cold and EV the requested window (PERIOD, CH6b1-R Q2). Each Site's row nodes and
        income earnings are over its `window_days` (Q1). A Site whose board read fails is UNAVAILABLE with four
        UNKNOWN rows."""
        self.seed_snapshots(sites, lo, hi, known_at)
        return self._summary(sites, lo, hi, known_at, self.contained_many(sites, lo, hi, known_at))

    def contained_many(self, sites: list[SiteRef], lo: datetime, hi: datetime,
                       known_at: datetime | None) -> dict[str, Any]:
        """CH6b1-R3: every cold/EV Site's selected windows over `[lo, hi)` in ONE estate snapshot
        (`site_selected_windows_many`), by Site code. A fallback (no batch, more than one tenant, a failure) is
        counted `summary.window_fallback` and logged; each Site then reads its own windows."""
        codes = [x.site_code for x in sites if x.domain in (COLD, EV)]
        estate, tenants = self.s.estate, {x.tenant_id for x in sites}
        if not codes:
            return {}
        try:
            if len(tenants) != 1 or not hasattr(estate, "site_selected_windows_many"):
                raise PortUnavailable("no batched window read")
            with perf.timed("summary.contained_windows"):
                return dict(estate.site_selected_windows_many(next(iter(tenants)), codes, lo, hi, known_at))
        except Exception as error:  # noqa: BLE001 - an optimization; each board reads its own windows
            read_scope.note_failure("site_selected_windows_many", error)
            perf.record("summary.window_fallback", 0.0)
            LOG.warning("outcome summary: the batched window read fell back to per-Site reads (%s)",
                        type(error).__name__)
            return {}

    def snapshot_specs(self, sites: list[SiteRef], lo: datetime,
                       hi: datetime) -> list[tuple[UUID, str, tuple[date, ...]]]:
        """CH6b1-R Q3: the exact `ChainRequest.day` keys the summary's Sites read: each composer's range (mini: the
        work window ending on `window_day`; cold/EV: `local_days(lo, hi)`) and `window_days` (`claim_days` and the
        Portfolio nodes)."""
        specs = []
        for site in sites:
            if site.domain not in (MINI, COLD, EV):
                continue
            kind, tz = SITE_TYPE_OF_DOMAIN[site.domain], site.timezone
            if site.domain == MINI:
                _, end = local_board_day(window_day(lo, hi, tz), tz)
                specs.append((site.site_id, kind, local_days(end - mini.WORK_WINDOW, end, tz)))
            else:
                specs.append((site.site_id, kind, local_days(lo, hi, tz)))
            specs.append((site.site_id, kind, window_days(lo, hi, tz)))
        return specs

    def seed_snapshots(self, sites: list[SiteRef], lo: datetime, hi: datetime,
                       known_at: datetime | None) -> int | None:
        """CH6b1-R Q3: one `read_latest` for all Sites, seeding the read scope's `chain.day` memo. A fallback (no
        reader, more than one tenant, a port without the batch, or a failure) is counted (`summary.seed_fallback`)
        and logged, never silent; every Site then reads its own range as before."""
        tenants = {site.tenant_id for site in sites}
        specs = self.snapshot_specs(sites, lo, hi)
        if not specs:
            return 0
        placed: int | None = None
        try:
            if self.s.chain_reader is not None and len(tenants) == 1:
                with perf.timed("summary.seed_snapshots"):
                    placed = self.s.chain_reader.request(next(iter(tenants)), known_at).seed_days(specs)
        except Exception as error:  # noqa: BLE001 - the batch is an optimization; each Site reads its own range
            read_scope.note_failure("seed_snapshots", error)
            LOG.warning("outcome summary: the one snapshot read fell back to per-Site reads (%s)",
                        type(error).__name__)
            placed = None
        if placed is None:
            perf.record("summary.seed_fallback", 0.0)
            if self.s.chain_reader is None or len(tenants) != 1:   # CH6b1 L3: the no-reader/multi-tenant path logs too
                LOG.warning("outcome summary: no one snapshot read (%s); each Site reads its own range",
                            "no chain reader" if self.s.chain_reader is None else "more than one tenant")
        return placed

    def summary_window(self, site: SiteRef, lo: datetime, hi: datetime,
                       known_at: datetime | None) -> tuple[str, date | None, datetime | None, datetime | None]:
        """(basis, day, lo, hi) of one Site's board inside the summary (the estate "Why?" reads the same board).
        CH6b1-R Q2 (R14): mini reads `window_day` (DAY); every other Site the requested window (PERIOD), so a
        cold/EV Site with no event in the window shows its composer's none/not-known state, never an older event.
        CH6b1-R3: its evidence is the latest selected window inside the requested window (`event_window`)."""
        if site.domain == MINI:
            return WINDOW_BASIS_DAY, window_day(lo, hi, site.timezone), None, None
        return WINDOW_BASIS_PERIOD, None, lo, hi

    def _summary(self, sites: list[SiteRef], lo: datetime, hi: datetime,
                 known_at: datetime | None, contained: dict[str, Any] | None = None) -> dict[str, Any]:
        out = []
        warnings: list[dict[str, Any]] = []  # C: each Site's board warnings, in Site order; a failed Site adds none
        # OUT-D U4 (review M2): Sites whose board loaded AND whose objectives were read, and of those the ones that
        # list a declared objective; every other Site (a failed board or a failed objectives read) is unread.
        read_sites = objective_sites = 0
        verified_read = 0  # WALK1-1 (WN-1): the Sites whose board loaded (`verified_sites_unread`)
        for site in sites:
            basis, b_day, b_lo, b_hi = self.summary_window(site, lo, hi, known_at)
            earnings: dict[str, Any] | None = None
            try:
                with perf.timed(f"board.{site.site_code}"):  # QW-1: each Site's board inside the summary
                    body = self.board(site, day=b_day, lo=b_lo, hi=b_hi, known_at=known_at,
                                      node_days=window_days(lo, hi, site.timezone),
                                      windows=(contained or {}).get(site.site_code, _MISS))
                parts = body.get("_window") or {"nodes": {}, "earnings": {}}
                earnings = parts["earnings"]
                rows = [_summary_row(r, body["_short_values"], parts["nodes"].get(r["category"]))
                        for r in body["rows"]]
                read_state = body["read_state"]
                warnings += body["warnings"]
                window: dict[str, Any] | None = body["window"]
                window_basis: str | None = basis
                verified_read += 1
                if body.get("objectives_read"):
                    read_sites += 1
                    objective_sites += 1 if body.get("objectives") else 0
            except Exception as error:  # noqa: BLE001 - one Site's failure never refuses the summary (§B.1)
                read_scope.note_failure(f"board.{site.site_code}", error)
                rows =[_unknown_row(cat) for cat in CATEGORIES]
                read_state = UNAVAILABLE
                window, window_basis = None, None
            out.append({"site_id": str(site.site_id), "site_code": site.site_code, "site_name": site.site_name,
                        "domain": site.domain, "overview_href": _overview_href(site), "read_state": read_state,
                        "rows": rows, "window": window, "window_basis": window_basis, "earnings": earnings})
        _, money_total = portfolio_parts(out)
        counted = self.estate_counts(sites, lo, hi, known_at)
        categories = [{"category": cat, "label": CATEGORY_LABEL[cat], "definition": CATEGORY_DEFINITION[cat],
                       "icon": CATEGORY_ICON[cat],
                       "sites_needing_attention": sum(1 for x in out for r in x["rows"]
                                                      if r["category"] == cat and r["state"] == NEEDS_ATTENTION),
                       "warning_count": sum(1 for w in warnings
                                            if any(i["category"] == cat for i in w["categories"]["items"]))}
                      for cat in CATEGORIES]
        return {"schema_version": SUMMARY_SCHEMA_VERSION, "policy_versions": dict(POLICY_VERSIONS),
                "window": {"from": wire(lo), "to": wire(hi)}, "sites": out, "categories": categories,
                "warnings": warnings, "objective_site_count": objective_sites if read_sites else None,
                "objective_sites_unread": len(sites) - read_sites,
                # DIESEL-1-R3u (CH6b3-R3 L2): one computation, the chain claim's value; None without a reader.
                "verified_result_count": None if counted is None else counted.claims[VERIFIED_RESULTS].value,
                "verified_sites_unread": len(sites) - verified_read, "money_total": money_total,
                # CH6b2-R Q1: the ONE card builder; `/api/estate/chain` carries the same `cards`.
                "cards": portfolio_cards(out, counted, money_total, categories,
                                         objective_sites if read_sites else None, len(sites) - read_sites),
                # PF-C1: the one coverage line, from the same `counted.days` the cards count.
                "coverage_line": portfolio_coverage(out, counted)}

    def estate_counts(self, sites: list[SiteRef], lo: datetime, hi: datetime,
                      known_at: datetime | None) -> EstateCounts | None:
        """CH6b2-R Q1: the one count computation (`estate_count_claims`) over this service's chain reader and thread
        port, the call `/estate/chain` makes; None (every card count NOT_KNOWN) without a reader or on a failure."""
        if self.s.chain_reader is None or not sites or len({x.tenant_id for x in sites}) != 1:
            return None
        try:
            req = self.s.chain_reader.request(sites[0].tenant_id, known_at)
            found = opportunity_items(self.s.threads, sites, lo, hi, known_at)
            return estate_count_claims(req, sites, lo, hi, found, (Exception,))
        except Exception as error:  # noqa: BLE001 - a failed count is NOT_KNOWN on the card, never zero
            read_scope.note_failure("estate_counts", error)
            LOG.warning("outcome summary: the estate counts could not be read (%s)", type(error).__name__)
            return None


def portfolio_parts(sites: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """CH6b1-R Q4: the ONE function that builds the Portfolio's per-Site parts and `money_total` from the summary's
    `sites[]`; the summary and `/api/estate/chain` both call it, so they agree by construction. Per Site code:
    `rows` = {category: {state, state_label, lead, nodes}} and `earnings` = {label: claim} (None: the board read
    failed). `money_total` = `estate_income` over every Site with an income earnings claim, in Site order."""
    parts: dict[str, dict[str, Any]] = {}
    income: list[tuple[str, dict[str, Any]]] = []
    for s in sites:
        earnings = s.get("earnings")
        parts[s["site_code"]] = {
            "rows": {r["category"]: {"state": r["state"], "state_label": r["state_label"],
                                     "lead": r.get("lead_outcome"), "nodes": r.get("nodes")}
                     for r in s.get("rows") or ()},
            "earnings": earnings}
        for label in INCOME_LABELS:
            claim = (earnings or {}).get(label)
            if claim is not None:
                income.append((s.get("site_name") or s["site_code"], claim))
    return parts, estate_income(income)


GROW, PROTECT, ASSURE = "GROW_REVENUE", "PROTECT_ASSET", "ASSURE_PERFORMANCE"
COST = "OPTIMIZE_COST"


def _coverage_days(d: dict[str, Any]) -> str:
    """One Site's days as the coverage line reads them: the days line, then the days with no readings received and
    the days still processing (PF-C review Low: the "Why?" days say what the coverage line says)."""
    line = days_line(d) or ""
    if d["no_data"]:
        line += card_text("coverage.no_data", x=d["no_data"])
    if d["pending"]:
        line += card_text("coverage.pending", q=d["pending"])
    return line


def _site_days(sites: list[dict[str, Any]], days_of: Callable[[dict[str, Any]], Any], *, full: bool = False) -> str | None:
    """The card's M1 days line (mock `PFDAYS`): "{Site}: {line}" per Site with days, " · "-joined. `full` adds the
    coverage line's no-readings and still-processing parts."""
    lines = []
    for s in sites:
        d = days_of(s)
        line = (_coverage_days(c) if (c := day_counts(d)) is not None else None) if full else days_line(d)
        if line:
            lines.append(card_text("days.site", site=s.get("site_name") or s["site_code"], line=line))
    return " · ".join(lines) or None


def _own_days(sites: list[dict[str, Any]], days_of: Callable[[dict[str, Any]], Any],
              counted: EstateCounts | None, all_sites: list[dict[str, Any]] | None = None) -> str | None:
    """PF-C2 (proposal §4): a card's own days line only when its day set differs from the shared coverage line's (a
    Site whose claim days are not that Site's counted days, e.g. a separate study); else None, the line says it.
    A card over only some Sites (`all_sites` given: Grow, the income Sites) names just those Sites' days, so its
    "Why?" days never name a Site its figure does not use (PF-C review Low)."""
    shared = (lambda s: None) if counted is None else (lambda s: counted.days.get(s["site_code"]))
    # HON-1: a claim over the line's arrival days is the line's day set, so it reads the line's count (a data-gap
    # day out), never a second "7 of 7" beside the line's "6 of 7".
    arrived = getattr(counted, "arrived", None) or {}
    same = (lambda s: day_counts(arrived.get(s["site_code"], shared(s))))
    if counted is not None and all(day_counts(days_of(s)) in (day_counts(shared(s)), same(s)) for s in sites):
        return None if all_sites is None or len(sites) == len(all_sites) else _site_days(sites, shared, full=True)
    return _site_days(sites, days_of)


def portfolio_coverage(sites: list[dict[str, Any]], counted: EstateCounts | None) -> dict[str, Any]:
    """PF-C1 (proposal §4, v71 `pf-coverage`; owner walkthrough 2026-11-10 item 2): the ONE coverage line of the
    Portfolio, built from the same `counted.days` (the chain day grades) the cards count, so the line and the card
    figures cannot disagree. Server text only (CH-6b2: the browser renders, never composes). `days_text` is every
    Site's days line, the "Why?" days of a card that has no line of its own."""
    if counted is None:
        return {"state": "NOT_KNOWN", "lead": card_text("coverage.lead.not_known"), "rule": None, "sites": [],
                "days_text": None}
    rows = []
    for s in sites:
        name = s.get("site_name") or s["site_code"]
        d = day_counts(counted.days.get(s["site_code"]))
        if d is None:
            rows.append({"site_code": s["site_code"], "site_name": name, "complete": False,
                         "text": card_text("coverage.site_not_known", site=name)})
            continue
        line = _coverage_days(d)
        line = line[:1].lower() + line[1:]
        rows.append({"site_code": s["site_code"], "site_name": name, "complete": d["complete"] == d["expected"],
                     "text": card_text("coverage.site", site=name, line=line)})
    complete = all(r["complete"] for r in rows)
    return {"state": "COMPLETE" if complete else "INCOMPLETE",
            "lead": card_text("coverage.lead.complete" if complete else "coverage.lead.incomplete"),
            "rule": card_text("coverage.rule"), "sites": rows,
            "days_text": _site_days(sites, lambda s: counted.days.get(s["site_code"]), full=True)}


def _income_days(s: dict[str, Any]) -> Any:
    earnings = s.get("earnings") or {}
    return next((earnings[k].get("days") for k in INCOME_LABELS if earnings.get(k)), None)


def _grow_card(sites: list[dict[str, Any]], money_total: dict[str, Any],
               counted: EstateCounts | None = None) -> dict[str, Any]:
    """CH6b2-R Q4/Q5: the Grow value from `money_total` (its own "At least" form; mixed currencies -> its text),
    else NOT_KNOWN (the kept gap `G-portfolio-grow-revenue`; the "possible" short-value fallback was dead code and is
    removed, CH6b2-R2 L3, BL-22); and the three parts Target, Potential, Estimated income."""
    target, potential = [], []
    for s in sites:
        name = s.get("site_name") or s["site_code"]
        row = next((r for r in s.get("rows") or () if r["category"] == GROW), None) or {}
        nodes = row.get("nodes") or {}
        if (nodes.get("kpi") or {}).get("value") is not None:   # MD-CH6-6: a Site whose Grow kpi has a record
            target.append(card_text("grow.site", site=name, text=nodes["kpi"]["text"]))
        text = (nodes.get("potential") or {}).get("text")
        if text and text != node_text("potential.none"):
            potential.append(card_text("grow.site", site=name, text=str(text).split("\n")[0]))
    total = money_total.get("value")
    lines = list(money_total.get("lines") or ())
    mixed = total is None and money_total.get("text") == node_text("money.currency_mixed")
    missing = False
    if total is not None:
        amount = money_text(total["amount"], None, total.get("currency"))
        value = {"text": card_text("grow.at_least", amount=amount)
                 if money_total.get("basis") == CHECKED_DAYS_BASIS else amount,
                 "small": card_text("grow.small.estimated")}
    elif mixed:
        value = {"text": money_total["text"], "small": None}
    else:
        value, missing = {"text": NOT_KNOWN_TEXT, "small": None}, True
    note = money_total.get("text")
    return {"value": value, "missing": missing, "detail": None,
            "basis_text": card_text("grow.basis.income" if total is not None or mixed else "grow.basis.none"),
            "days_line": _own_days([s for s in sites if _income_days(s) is not None], _income_days, counted, sites),
            "tone": "green" if total is not None or mixed else "neutral", "claim": money_total,
            "parts": {"target": " · ".join(target) or card_text("grow.target.none"),
                      "potential": " · ".join(potential) or card_text("grow.potential.none"),
                      "income": " · ".join(lines) or note or NOT_KNOWN_TEXT,
                      "income_note": note if lines and note != NOT_KNOWN_TEXT else None}}


def _cost_claim(s: dict[str, Any]) -> dict[str, Any] | None:
    """CH5d1-R 2.1: the Site's Optimize cost claim, its `OPTIMIZE_COST` row's `nodes.earnings` (None for a failed
    board, whose row has no nodes)."""
    row = next((r for r in s.get("rows") or () if r["category"] == COST), None) or {}
    return (row.get("nodes") or {}).get("earnings")


def _optimize_card(sites: list[dict[str, Any]], counted: EstateCounts | None = None) -> dict[str, Any]:
    """CH5d1-R 2.1: the Optimize card from each Site's chain cost claim (`avoided_cost@1` over `money_head`), the
    claim the board shows, so the card and its "Why?" share one source. Never summed across Sites (design A6,
    D-AW-5): one priced Site shows its claim text byte-equal; two or more list each Site's claim."""
    priced = [(s, c) for s in sites if (c := _cost_claim(s)) is not None and c.get("value") is not None]
    name = lambda s: s.get("site_name") or s["site_code"]   # noqa: E731
    small = lambda c: COST_SMALL[c["key"].removeprefix("money.")]   # noqa: E731  (unknown label: KeyError)
    claim = None
    if not priced:
        value, detail, basis, tone = ({"text": NOT_KNOWN_TEXT, "small": None}, card_text("cost.detail.none"),
                                      card_text("cost.basis.none"), "neutral")
    elif len(priced) == 1:
        (s, claim), = priced
        value = {"text": claim["text"], "small": small(claim)}
        detail, basis, tone = card_text("cost.detail.one", site=name(s)), card_text("cost.basis.money"), "amber"
    else:
        value = {"text": card_text("cost.sites", sites=sites_text(len(priced))), "small": None}
        detail = " · ".join(card_text("cost.site", site=name(s), text=c["text"], small=small(c)) for s, c in priced)
        basis, tone = card_text("cost.basis.money"), "amber"
    days = {s["site_code"]: c.get("days") for s, c in priced}
    return {"value": value, "missing": False, "detail": detail, "basis_text": basis,
            "days_line": _own_days([s for s, _ in priced], lambda s: days[s["site_code"]], counted),
            "tone": tone, "claim": claim}


def portfolio_cards(sites: list[dict[str, Any]], counted: EstateCounts | None, money_total: dict[str, Any],
                    categories: list[dict[str, Any]], objective_sites: int | None,
                    objectives_unread: int) -> dict[str, dict[str, Any]]:
    """CH6b2-R Q1 (build sheet CH-6 §B2): the ONE builder of the Portfolio's four cards (Grow, Optimize, Protect,
    Assure), called by the summary and carried by `/api/estate/chain`, so they agree by construction. Each card is
    `{value: {text, small}, missing, detail, basis_text, days_line, tone, claim, parts?}`; the browser renders markup
    only. Optimize is each Site's chain cost claim (CH5d1-R 2.1). The Portfolio-body clauses are its `card_notes`.
    PF-C2: Protect and Assure count every Site's days, the shared coverage line's (`portfolio_coverage`), so they
    carry no days line; Grow and Optimize carry theirs only when their days differ."""
    claims = {} if counted is None else counted.claims_json()

    def claim(key: str) -> dict[str, Any]:
        return claims.get(key) or {"key": key, "value": None, "basis": "NOT_KNOWN", "days": None,
                                   "text": NOT_KNOWN_TEXT}

    disrupted, verified = claim(SITES_DISRUPTED), claim(VERIFIED_RESULTS)
    protect = next((c for c in categories if c["category"] == PROTECT), None)
    w = None if protect is None else protect["warning_count"]
    n = objective_sites
    if n is None or (n == 0 and objectives_unread > 0):
        assure_detail = None
    elif n == 0:
        assure_detail = card_text("assure.targets_none")
    else:
        unjudged = card_text("assure.unchecked", sites=sites_text(objectives_unread)) if objectives_unread else ""
        assure_detail = card_text("assure.targets", sites=sites_text(n), unjudged=unjudged)
    # PV-1-R §2: one line per verified result with money, Site order then code order; no total, no sum.
    value_lines = [card_text("assure.value_line", site=s.get("site_name") or s["site_code"], text=e["text"])
                   for s in sites
                   for r in s.get("rows") or () if r["category"] == ASSURE
                   for e in (r.get("nodes") or {}).get("verified_values") or ()]
    # DIESEL-1-R3j (§9j.11), MOCK DEVIATION MD-FUEL-K4-3: one line per unexplained-fuel Finding, Site order then night
    # order (the node's order); no total, no sum, no arithmetic across entries or with any other card.
    fuel_lines = [card_text("protect.fuel_line", site=s.get("site_name") or s["site_code"], text=e["text"])
                  for s in sites
                  for r in s.get("rows") or () if r["category"] == PROTECT
                  for e in (r.get("nodes") or {}).get("unexplained_fuel") or ()]
    return {
        GROW: _grow_card(sites, money_total, counted),
        COST: _optimize_card(sites, counted),
        PROTECT: {"value": count_card_value(disrupted), "missing": False,
                  "detail": card_text("protect.detail.none") if w is None
                  else card_text("protect.detail", w=w, warnings="warning" if w == 1 else "warnings"),
                  "basis_text": card_text("protect.basis"), "days_line": None,
                  "tone": "red" if (disrupted.get("value") or 0) >= 1 else "neutral", "claim": disrupted,
                  "fuel_lines": fuel_lines,
                  "fuel_note": card_text("protect.fuel_separate") if fuel_lines else None},
        ASSURE: {"value": count_card_value(verified, card_text("assure.zero")), "missing": False,
                 "detail": assure_detail, "basis_text": card_text("assure.basis"), "days_line": None,
                 "tone": "neutral", "claim": verified, "value_lines": value_lines,
                 "value_note": card_text("assure.values_separate") if value_lines else MONEY_NOT_CREDITED},
    }


def _overview_href(site: SiteRef) -> str:
    """The `estate/evidence_money.py` `site_home_href` rule: EV Sites open at `/sites/{code}/ev`. CH6b1-R Q2: every
    Site is judged on the requested window (or its `window_day`), so the link is the base Site link."""
    return f"/sites/{site.site_code}/ev" if site.domain == EV else f"/sites/{site.site_code}"


def _summary_row(row: dict[str, Any], short_values: dict[str, str],
                 nodes: dict[str, Any] | None = None) -> dict[str, Any]:
    lead = row.get("lead_outcome") or {}
    short = (short_values.get(row["category"]) if lead.get("key") == GROW_LEAD
             and (row["state"] == OPPORTUNITY or row.get("potential")) else None)
    return {"category": row["category"], "state": row["state"], "state_label": row["state_label"],
            "tone": row["tone"], "lead_outcome": row.get("lead_outcome"), "headline": row.get("headline"),
            "short_value": short, "headline_money": row.get("headline_money"), "nodes": nodes}


def _unknown_row(category: str) -> dict[str, Any]:
    return {"category": category, "state": UNKNOWN, "state_label": STATE_LABEL[UNKNOWN], "tone": STATE_TONE[UNKNOWN],
            "lead_outcome": None, "headline": None, "short_value": None, "headline_money": None, "nodes": None}


def board_cutoff(domain: str | None, known_at: datetime | None, resolved: Any) -> datetime | None:
    """addendum 4 #5, CH3-R, CH-5a1 R7: the one cutoff rule of a board read, `chain/read.py` `site_cutoff`: mini ->
    the request's cutoff (None = as known now); cold/EV -> the read's resolved cutoff (the overview body's
    `window.known_at`) bounded by the request's, else the request's."""
    return site_cutoff(domain, known_at, mini.utc(resolved), known_at)
