"""CH-5a2a (build sheet Part B §B1): the three `outcome-chain-1` read routes; CH-5b2: the two "Why?" routes.

    GET /api/sites/{site_code}/chain                 the board route's admission, window parsing and refusals
                                                     (`outcome_api.board_site` / `board_window`): mini one day,
                                                     cold and EV `from`/`to` at most 31 days; `known_at`
    GET /api/estate/chain                            the estate summary's scope and Site set
                                                     (`outcome_api.estate_sites`)
    GET /api/sites/{site_code}/threads/{thread_id}   one thread of this Site, its state the last visible event at the
                                                     board's cutoff (cold/EV: optional `from`/`to`, CH5a2b-R Q11);
                                                     another Site's thread, or an unknown id, is 404 THREAD_NOT_FOUND
    GET /api/sites/{site_code}/chain/why?category    CH-5b2: the "Why?" trace of one board row (`chain/why.py`),
                                                     the Site chain's window and refusals, plus 422 CATEGORY_UNKNOWN
    GET /api/estate/chain/why?category               CH-5b2: the per-Site traces of the estate scope; no money summed

`outcomes` (Site) and `rows` (estate) are the board composition's own rows, so a chain body and the board or the
summary it sits beside cannot disagree. The count claims (`counts`, `sites[].threads`) come from the one
`chain.claims.estate_count_claims` (CH-5a2b, §B14 Q7); money is never summed across Sites (`money_total` null, design A6). Each route runs inside
`perf.route`, so it has one read scope (ledger and memo) per request.

CH-5b2 (CH5b2-R Q1/Q2): all five routes are stored routes (`ResponseStore.serve`). The Site routes key on the board's
key (one Site, its own watermark) plus `category` or the thread id; the estate routes on the summary's parsed scope
and admission plus `category`. Every response carries `Cache-Control: private, no-cache`; a stored body carries its
`ETag`, and a matching `If-None-Match` is a `304` answered before any composition. With the store off (or compose
only) there is no ETag and no 304.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Callable, Iterator
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.encoders import jsonable_encoder

from assetops_backend import perf, read_scope
from assetops_backend.chain import site_chain, why
from assetops_backend.chain.measures import measures_for
from assetops_backend.chain.claims import (counted_threads, disrupting, estate_count_claims,
                                           opportunity_items)
from assetops_backend.chain.read import SITE_TYPE_OF_DOMAIN, lifecycle_cutoff, local_days, window_day
from assetops_backend.chain.response_store import ResponseStore, StoredRoute, finish, parsed_key
from assetops_backend.cold_assessment_api import Disclosure, allow_disclosure
from assetops_backend.estate.scope import EstateRefusal, parse_request as parse_estate
from assetops_backend.estate_api import Authenticate, development_authenticate
from assetops_backend.finding_api import Access, development_access
from assetops_backend.outcome_api import (DISCLOSURE_REFUSAL, _instant, _refuse, board_site, board_window,
                                          estate_sites, site_ref)
from assetops_backend.outcomes.catalogue import COLD, EV, MINI
from assetops_backend.site_outcomes.read import (
    POLICY_VERSIONS, SiteOutcomeBoardService, SiteRef, portfolio_parts, wire)
from assetops_backend.sites.cutover import ImportedSiteRegistry
from assetops_backend.sites.ports import SiteStoreUnavailable

SITE_CHAIN_ROUTE = "/api/sites/{site_code}/chain"
ESTATE_CHAIN_ROUTE = "/api/estate/chain"
THREAD_ROUTE = "/api/sites/{site_code}/threads/{thread_id}"
SITE_WHY_ROUTE = "/api/sites/{site_code}/chain/why"
ESTATE_WHY_ROUTE = "/api/estate/chain/why"
CACHE_CONTROL = "private, no-cache"


PROTECT_ASSET = "PROTECT_ASSET"


def _versions(chain_versions: Callable[[], dict[str, str | None]]) -> dict[str, str | None]:
    return {**chain_versions(), "status": POLICY_VERSIONS["status"]}


def _utc(text: Any) -> datetime | None:
    return None if text is None else datetime.fromisoformat(str(text).replace("Z", "+00:00"))


def _site_type(ref: SiteRef) -> str:
    return SITE_TYPE_OF_DOMAIN[ref.domain]


def _measures(ref: SiteRef) -> tuple[str, ...]:
    return tuple(m.key for m in measures_for(_site_type(ref)))


def _verification(req: Any, ref: SiteRef, rows: Any, thread_ids: set[str]) -> dict[str, str | None]:
    ids = [a["action_id"] for a in rows.get("actions", ())
           if a["thread_id"] in thread_ids and a["kind"] == "MINI_TRIAL"]
    return {f.action_id: f.verification_state for f in req.action_facts(ref.site_id, ref.site_code, ids)}


def _category(params: Any) -> str:
    values = params.getlist("category")
    try:
        return why.check_category(values[0] if len(values) == 1 else None)
    except why.CategoryUnknown as error:
        raise _refuse(422, "CATEGORY_UNKNOWN", "'category' must be one of GROW_REVENUE, OPTIMIZE_COST, "
                                               "PROTECT_ASSET or ASSURE_PERFORMANCE.") from error


@contextmanager
def _private_refusals() -> Iterator[None]:
    """4xx and 5xx refusals carry `Cache-Control` too (§2.2: every chain and why response)."""
    try:
        yield
    except HTTPException as error:
        error.headers = {**(error.headers or {}), "Cache-Control": CACHE_CONTROL}
        raise


def _done(out: Any, response: Response) -> Any:
    """Every chain and why response carries `Cache-Control` (§2.2); a stored `Response` also keeps the injected
    response's headers (`Server-Timing`)."""
    if isinstance(out, Response):
        out = finish(out, response)
        out.headers["Cache-Control"] = CACHE_CONTROL
        return out
    response.headers["Cache-Control"] = CACHE_CONTROL
    return out


def build_chain_router(service: SiteOutcomeBoardService | None, registry: ImportedSiteRegistry, *,
                       estate: Any = None, tenant: Callable[[], UUID | None] = lambda: None,
                       access: Access = development_access, work_access: Access = development_access,
                       cold_disclosure: Disclosure = allow_disclosure, ev_disclosure: Disclosure = allow_disclosure,
                       authenticate: Authenticate = development_authenticate,
                       unavailable: tuple[type[BaseException], ...] = (),
                       policy_versions: Callable[[], dict[str, str | None]] = lambda: {},
                       lifecycle: Callable[[], Any] = lambda: None,
                       responses: ResponseStore | None = None) -> APIRouter:
    """`policy_versions` is `chain.composition.chain_policy_versions` and `lifecycle` its `thread_lifecycle_policy`
    (injected: only the composition imports the chain adapters). `service` is the board service the outcome router
    serves (its `ChainReader` and thread port are the chain's reads); the other arguments are the outcome router's,
    passed the same values in `main.py`. `responses` is the stored route store (None: every request composes)."""
    router = APIRouter()
    disclosures = {COLD: cold_disclosure, EV: ev_disclosure}

    def admitted(request: Request, code: str) -> int | None:
        return access(request, code) or work_access(request, code)

    def disclosed(ref: SiteRef) -> bool:
        check = disclosures.get(ref.domain)
        return check is None or bool(check(ref.site_code, ref.tenant_id, ref.site_id))

    def reader() -> Any:
        chain_reader = None if service is None else service.s.chain_reader
        if chain_reader is None:
            raise _refuse(503, "SITE_CHAIN_UNAVAILABLE", "No product database is configured.")
        return chain_reader

    def opened(ref: SiteRef) -> Any:
        """After admission and parsing, as the board route orders its refusals: 503, then disclosure."""
        chain_reader = reader()
        if not disclosed(ref):
            raise _refuse(403, DISCLOSURE_REFUSAL[ref.domain],
                          f"The source provenance of Site {ref.site_code!r} may not be disclosed to this caller.")
        return chain_reader

    def clean_measures() -> dict[str, tuple[str, ...]]:
        policy = lifecycle()
        return {} if policy is None else dict(policy.clean_day_measures)

    def site_served(route: str, ref: SiteRef, request: Request, key: dict[str, Any],
                    compose: Callable[[], dict[str, Any]]) -> Any:
        """The board's stored-route key (one Site, its own watermark) plus the route's own parameters."""
        if responses is None:
            return compose()[route]
        site = UUID(str(ref.site_id))
        return responses.serve(StoredRoute(route, ref.tenant_id, {"site": ref.site_id, "domain": ref.domain, **key},
                                           sites=(site,), watermark_sites=(site,)), compose,
                               request.headers.get("if-none-match"))

    def window_key(day: Any, lo: Any, hi: Any, known_at: Any, pin: Any) -> dict[str, Any]:
        return {"day": day, "from": lo, "to": hi, "known_at": known_at,
                "pin": None if pin is None else [str(x) if x is not None else None for x in pin]}

    def site_parts(ref: SiteRef, chain_reader: Any, day: Any, lo: Any, hi: Any, known_at: Any,
                   pin: Any) -> dict[str, Any]:
        """The Site chain's reads: the board, the window's day facts, the threads and their Actions."""
        try:
            board = service.board(ref, day=day, lo=lo, hi=hi, known_at=known_at, pin=pin)
            w = board["window"]
            w_lo, w_hi = _utc(w["from"]), _utc(w["to"])
            req = chain_reader.request(ref.tenant_id, known_at)
            facts = req.day(ref.site_id, _site_type(ref), local_days(w_lo, w_hi, ref.timezone))
            rows = req.threads(ref.site_id)
            threads = site_chain.threads_of(rows, site=ref.site_code, domain=ref.domain, tz=ref.timezone,
                                            lo=w_lo, hi=w_hi, day=window_day(w_lo, w_hi, ref.timezone),
                                            cutoff=lifecycle_cutoff(known_at))
            ids = {t["id"] for t in threads}
            actions = site_chain.actions_of(rows, ids, site=ref.site_code, tz=ref.timezone, cutoff=lifecycle_cutoff(known_at),
                                            verification=_verification(req, ref, rows, ids))
        except (SiteStoreUnavailable, *unavailable) as error:
            raise _refuse(503, "SITE_CHAIN_UNAVAILABLE", str(error)) from error
        return {"board": board, "window": w, "req": req, "facts": facts, "threads": threads, "actions": actions}

    def site_trace(ref: SiteRef, parts: dict[str, Any], category: str) -> why.Trace:
        """`chain.why.site_trace` over the Site chain's reads (its thread history, Actions and `trace_facts`)."""
        req = parts["req"]
        try:
            return why.site_trace(req, ref, category=category, board=parts["board"], facts=parts["facts"],
                                  site_measures=_measures(ref), clean_measures=clean_measures(),
                                  verification=lambda rows, ids: _verification(req, ref, rows, ids))
        except (SiteStoreUnavailable, *unavailable) as error:
            raise _refuse(503, "SITE_CHAIN_UNAVAILABLE", str(error)) from error

    @router.get(SITE_CHAIN_ROUTE)
    def site_chain_route(site_code: str, request: Request, response: Response) -> Any:
        with perf.route(SITE_CHAIN_ROUTE, response), _private_refusals():
            out = _site_chain(site_code, request)
        return _done(out, response)

    def _site_chain(site_code: str, request: Request) -> Any:
        params = request.query_params
        ref = board_site(admitted, registry, site_code, "Site chain", request)
        known_at = _instant(params, "known_at")
        day, lo, hi, pin = board_window(ref, params)
        chain_reader = opened(ref)

        def compose() -> dict[str, Any]:
            p = site_parts(ref, chain_reader, day, lo, hi, known_at, pin)
            return {SITE_CHAIN_ROUTE: jsonable_encoder({
                "schema_version": site_chain.SCHEMA_VERSION,
                "site": {"code": ref.site_code, "tz": ref.timezone, "domain": _site_type(ref)},
                "window": p["window"], "days": site_chain.days_of(p["facts"], _measures(ref)),
                "outcomes": site_chain.outcomes_of(p["board"]["rows"]), "threads": p["threads"],
                "actions": p["actions"], "policy_versions": _versions(policy_versions)})}

        return site_served(SITE_CHAIN_ROUTE, ref, request, window_key(day, lo, hi, known_at, pin), compose)

    @router.get(SITE_WHY_ROUTE)
    def site_why_route(site_code: str, request: Request, response: Response) -> Any:
        with perf.route(SITE_WHY_ROUTE, response), _private_refusals():
            out = _site_why(site_code, request)
        return _done(out, response)

    def _site_why(site_code: str, request: Request) -> Any:
        params = request.query_params
        ref = board_site(admitted, registry, site_code, "Site chain", request)
        known_at = _instant(params, "known_at")
        day, lo, hi, pin = board_window(ref, params)
        category = _category(params)
        chain_reader = opened(ref)

        def compose() -> dict[str, Any]:
            p = site_parts(ref, chain_reader, day, lo, hi, known_at, pin)
            t = site_trace(ref, p, category)
            return {SITE_WHY_ROUTE: jsonable_encoder({
                "schema_version": why.SCHEMA_VERSION, "site": {"code": ref.site_code}, "category": category,
                "window": p["window"], **t.to_json()})}

        return site_served(SITE_WHY_ROUTE, ref, request,
                           {**window_key(day, lo, hi, known_at, pin), "category": category}, compose)

    @router.get(THREAD_ROUTE)
    def thread_route(site_code: str, thread_id: str, request: Request, response: Response) -> Any:
        with perf.route(THREAD_ROUTE, response), _private_refusals():
            out = _thread(site_code, thread_id, request)
        return _done(out, response)

    def _thread(site_code: str, thread_id: str, request: Request) -> Any:
        ref = board_site(admitted, registry, site_code, "Site thread", request)
        known_at = _instant(request.query_params, "known_at")
        _, lo, hi, _ = board_window(ref, request.query_params)  # CH5a2b-R Q11: optional from/to (cold/EV)
        chain_reader = opened(ref)
        try:
            tid = str(UUID(thread_id)).lower()
        except ValueError:
            tid = None

        def compose() -> dict[str, Any]:
            try:
                req = chain_reader.request(ref.tenant_id, known_at)
                rows = req.threads(ref.site_id) if tid is not None else {}
                # CH6b2-R3 (M-R2-1): the lifecycle is read at `lifecycle_cutoff(k)` for every domain, as `site_parts`
                # and the claims do, so the detail never contradicts the chain row or the card.
                cutoff = lifecycle_cutoff(known_at)
                body = None if tid is None else site_chain.thread_detail(
                    rows, tid, site=ref.site_code, domain=ref.domain, tz=ref.timezone, cutoff=cutoff)
                if body is not None:
                    body["actions"] = site_chain.actions_of(rows, {tid}, site=ref.site_code, tz=ref.timezone,
                                                            cutoff=cutoff,
                                                            verification=_verification(req, ref, rows, {tid}))
            except (SiteStoreUnavailable, *unavailable) as error:
                raise _refuse(503, "SITE_CHAIN_UNAVAILABLE", str(error)) from error
            if body is None:
                raise _refuse(404, "THREAD_NOT_FOUND", f"No thread {thread_id!r} on Site {site_code!r}.")
            return {THREAD_ROUTE: jsonable_encoder({
                "schema_version": site_chain.SCHEMA_VERSION, "site": ref.site_code, "known_at": wire(known_at),
                "thread": body, "policy_versions": _versions(policy_versions)})}

        return site_served(THREAD_ROUTE, ref, request,
                           {"from": lo, "to": hi, "known_at": known_at, "thread": tid or thread_id}, compose)

    def estate_served(route: str, request: Request, items: list[tuple[str, str]], extra: dict[str, Any],
                      compose: Callable[[], dict[str, Any]]) -> Any:
        """The summary's stored-route rule: its parsed scope and admission (every refusal from `estate_sites`)."""
        tenant_id = tenant() if responses is not None and service is not None and estate is not None else None
        if tenant_id is None or authenticate(request) == 401:
            return compose()[route]
        try:
            parsed = parse_estate("scope", items)
        except EstateRefusal:
            return compose()[route]

        def admit(code: str) -> bool:  # `estate_sites`' admission and disclosure, per Site code
            if admitted(request, code) is not None:
                return False
            site = registry.imported(code)
            return site is not None and disclosed(site_ref(site))

        return responses.serve(StoredRoute(route, tenant_id, {**parsed_key(parsed), **extra}, admit=admit), compose,
                               request.headers.get("if-none-match"))

    def scope(request: Request, items: list[tuple[str, str]]) -> tuple[list[SiteRef], Any]:
        return estate_sites(request, authenticate=authenticate, estate=estate if service is not None else None,
                            tenant=tenant, admitted=admitted, registry=registry, disclosed=disclosed,
                            unavailable=unavailable, items=items)

    @router.get(ESTATE_CHAIN_ROUTE)
    def estate_chain_route(request: Request, response: Response) -> Any:
        with perf.route(ESTATE_CHAIN_ROUTE, response), _private_refusals():
            out = _estate_chain(request)
        return _done(out, response)

    def _estate_chain(request: Request) -> Any:
        items = request.query_params.multi_items()

        def compose() -> dict[str, Any]:
            sites, parsed = scope(request, items)
            chain_reader = reader()
            lo, hi = parsed.from_.astimezone(timezone.utc), parsed.to.astimezone(timezone.utc)
            summary = service.summary(sites, lo, hi, parsed.known_at)
            req = chain_reader.request(sites[0].tenant_id if sites else None, parsed.known_at)
            found = opportunity_items(service.s.threads, sites, lo, hi, parsed.known_at)
            # §B14 Q7: the one count computation the Portfolio and estate Findings summaries also call.
            counted = estate_count_claims(req, sites, lo, hi, found, (SiteStoreUnavailable, *unavailable))
            grouped: dict[str, list[dict[str, Any]]] = {}
            for item in found or ():
                grouped.setdefault(item["site_code"], []).append(read_scope.thaw(item))
            # CH6b1-R Q4: the one function the summary also calls builds rows, nodes, earnings and money_total.
            parts, money_total = portfolio_parts(summary["sites"])
            out = []
            for ref in sites:
                counts = counted.days.get(ref.site_code)
                part = parts.get(ref.site_code) or {"rows": {}, "earnings": None}
                out.append({"code": ref.site_code, "domain": _site_type(ref),
                            "days": None if counts is None else counts.to_json(),  # None: the read failed, never 0
                            "rows": part["rows"], "earnings": part["earnings"],
                            "threads": counted.threads.get(ref.site_code),
                            "opportunities": None if found is None else grouped.get(ref.site_code, [])})
            return {ESTATE_CHAIN_ROUTE: jsonable_encoder({
                "schema_version": site_chain.SCHEMA_VERSION,
                "window": {"from": wire(lo), "to": wire(hi), "known_at": wire(parsed.known_at)},
                "sites": out, "counts": counted.claims_json(),
                "money_total": money_total, "cards": summary["cards"],   # CH6b2-R Q1: the summary's one builder
                "policy_versions": _versions(policy_versions)})}

        return estate_served(ESTATE_CHAIN_ROUTE, request, items, {}, compose)

    @router.get(ESTATE_WHY_ROUTE)
    def estate_why_route(request: Request, response: Response) -> Any:
        with perf.route(ESTATE_WHY_ROUTE, response), _private_refusals():
            out = _estate_why(request)
        return _done(out, response)

    def _estate_why(request: Request) -> Any:
        items = [(k, v) for k, v in request.query_params.multi_items() if k != "category"]

        def compose() -> dict[str, Any]:
            sites, parsed = scope(request, items)
            category = _category(request.query_params)
            chain_reader = reader()
            lo, hi = parsed.from_.astimezone(timezone.utc), parsed.to.astimezone(timezone.utc)
            traced: list[tuple[SiteRef, why.Trace]] = []
            disrupted: list[tuple[str, Any, Any]] = []
            for ref in sites:  # each Site's board as the summary reads it (`summary_window`)
                _, day, b_lo, b_hi = service.summary_window(ref, lo, hi, parsed.known_at)
                parts = site_parts(ref, chain_reader, day, b_lo, b_hi, parsed.known_at, None)
                traced.append((ref, site_trace(ref, parts, category)))
                if category == PROTECT_ASSET:  # CH6b2-R Q2(b): the threads `count.sites_disrupted` counts
                    try:
                        threads = disrupting(counted_threads(parts["req"], ref, lo, hi))
                    except (SiteStoreUnavailable, *unavailable) as error:
                        raise _refuse(503, "SITE_CHAIN_UNAVAILABLE", str(error)) from error
                    row = next((r for r in parts["board"]["rows"] if r["category"] == PROTECT_ASSET), {})
                    disrupted.append((ref.site_name or ref.site_code, threads, row))
            comes_from = why.disrupted_lines(disrupted) if category == PROTECT_ASSET else None
            return {ESTATE_WHY_ROUTE: jsonable_encoder({
                "schema_version": why.SCHEMA_VERSION, "category": category,
                "window": {"from": wire(lo), "to": wire(hi), "known_at": wire(parsed.known_at)},
                "text": why.estate_text(category, [(ref.site_name or ref.site_code, t) for ref, t in traced],
                                        comes_from),
                "sites": [{"code": ref.site_code, **t.to_json()} for ref, t in traced]})}

        category = request.query_params.getlist("category")
        return estate_served(ESTATE_WHY_ROUTE, request, items,
                             {"category": category[0] if len(category) == 1 else category}, compose)

    return router
