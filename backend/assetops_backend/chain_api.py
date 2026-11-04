"""CH-5a2a (build sheet Part B §B1): the three `outcome-chain-1` read routes.

    GET /api/sites/{site_code}/chain                 the board route's admission, window parsing and refusals
                                                     (`outcome_api.board_site` / `board_window`): mini one day,
                                                     cold and EV `from`/`to` at most 31 days; `known_at`
    GET /api/estate/chain                            the estate summary's scope and Site set
                                                     (`outcome_api.estate_sites`)
    GET /api/sites/{site_code}/threads/{thread_id}   one thread of this Site at `known_at`; another Site's thread,
                                                     or an unknown id, is 404 THREAD_NOT_FOUND

`outcomes` (Site) and `rows` (estate) are the board composition's own rows, so a chain body and the board or the
summary it sits beside cannot disagree. The count claims (`counts`, `sites[].threads`) come from the one
`chain.claims.estate_count_claims` (CH-5a2b, §B14 Q7); money is never summed across Sites (`money_total` null, design A6). Each route runs inside
`perf.route`, so it has one read scope (ledger and memo) per request.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable
from uuid import UUID

from fastapi import APIRouter, Request, Response
from fastapi.encoders import jsonable_encoder

from assetops_backend import perf, read_scope
from assetops_backend.chain import site_chain
from assetops_backend.chain.measures import measures_for
from assetops_backend.chain.claims import estate_count_claims, opportunity_items
from assetops_backend.chain.read import SITE_TYPE_OF_DOMAIN, local_days, window_day
from assetops_backend.cold_assessment_api import Disclosure, allow_disclosure
from assetops_backend.estate_api import Authenticate, development_authenticate
from assetops_backend.finding_api import Access, development_access
from assetops_backend.outcome_api import (DISCLOSURE_REFUSAL, _instant, _refuse, board_site, board_window,
                                          estate_sites)
from assetops_backend.outcomes.catalogue import COLD, EV, MINI
from assetops_backend.site_outcomes.read import POLICY_VERSIONS, SiteOutcomeBoardService, SiteRef, wire
from assetops_backend.sites.cutover import ImportedSiteRegistry
from assetops_backend.sites.ports import SiteStoreUnavailable

SITE_CHAIN_ROUTE = "/api/sites/{site_code}/chain"
ESTATE_CHAIN_ROUTE = "/api/estate/chain"
THREAD_ROUTE = "/api/sites/{site_code}/threads/{thread_id}"


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


def build_chain_router(service: SiteOutcomeBoardService | None, registry: ImportedSiteRegistry, *,
                       estate: Any = None, tenant: Callable[[], UUID | None] = lambda: None,
                       access: Access = development_access, work_access: Access = development_access,
                       cold_disclosure: Disclosure = allow_disclosure, ev_disclosure: Disclosure = allow_disclosure,
                       authenticate: Authenticate = development_authenticate,
                       unavailable: tuple[type[BaseException], ...] = (),
                       policy_versions: Callable[[], dict[str, str | None]] = lambda: {}) -> APIRouter:
    """`policy_versions` is `chain.composition.chain_policy_versions` (injected: only the composition imports the
    chain adapters). `service` is the board service the outcome router serves (its `ChainReader` and thread port are the chain's
    reads); the other arguments are the outcome router's, passed the same values in `main.py`."""
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

    @router.get(SITE_CHAIN_ROUTE)
    def site_chain_route(site_code: str, request: Request, response: Response) -> dict[str, Any]:
        with perf.route(SITE_CHAIN_ROUTE, response):
            return _site_chain(site_code, request)

    def _site_chain(site_code: str, request: Request) -> dict[str, Any]:
        params = request.query_params
        ref = board_site(admitted, registry, site_code, "Site chain", request)
        known_at = _instant(params, "known_at")
        day, lo, hi, pin = board_window(ref, params)
        chain_reader = opened(ref)
        try:
            board = service.board(ref, day=day, lo=lo, hi=hi, known_at=known_at, pin=pin)
            w = board["window"]
            w_lo, w_hi, cutoff = _utc(w["from"]), _utc(w["to"]), _utc(w["known_at"])
            req = chain_reader.request(ref.tenant_id, known_at)
            facts = req.day(ref.site_id, _site_type(ref), local_days(w_lo, w_hi, ref.timezone))
            rows = req.threads(ref.site_id)
            threads = site_chain.threads_of(rows, site=ref.site_code, domain=ref.domain, tz=ref.timezone,
                                            lo=w_lo, hi=w_hi, day=window_day(w_lo, w_hi, ref.timezone),
                                            cutoff=cutoff)
            ids = {t["id"] for t in threads}
            actions = site_chain.actions_of(rows, ids, site=ref.site_code, tz=ref.timezone, cutoff=cutoff,
                                            verification=_verification(req, ref, rows, ids))
        except (SiteStoreUnavailable, *unavailable) as error:
            raise _refuse(503, "SITE_CHAIN_UNAVAILABLE", str(error)) from error
        return jsonable_encoder({
            "schema_version": site_chain.SCHEMA_VERSION,
            "site": {"code": ref.site_code, "tz": ref.timezone, "domain": _site_type(ref)},
            "window": w, "days": site_chain.days_of(facts, _measures(ref)),
            "outcomes": site_chain.outcomes_of(board["rows"]), "threads": threads, "actions": actions,
            "policy_versions": _versions(policy_versions)})

    @router.get(THREAD_ROUTE)
    def thread_route(site_code: str, thread_id: str, request: Request, response: Response) -> dict[str, Any]:
        with perf.route(THREAD_ROUTE, response):
            return _thread(site_code, thread_id, request)

    def _thread(site_code: str, thread_id: str, request: Request) -> dict[str, Any]:
        ref = board_site(admitted, registry, site_code, "Site thread", request)
        known_at = _instant(request.query_params, "known_at")
        chain_reader = opened(ref)
        try:
            tid = str(UUID(thread_id)).lower()
        except ValueError:
            tid = None
        try:
            req = chain_reader.request(ref.tenant_id, known_at)
            rows = req.threads(ref.site_id) if tid is not None else {}
            body = None if tid is None else site_chain.thread_detail(
                rows, tid, site=ref.site_code, domain=ref.domain, tz=ref.timezone, cutoff=known_at)
            if body is not None:
                body["actions"] = site_chain.actions_of(rows, {tid}, site=ref.site_code, tz=ref.timezone,
                                                        cutoff=known_at,
                                                        verification=_verification(req, ref, rows, {tid}))
        except (SiteStoreUnavailable, *unavailable) as error:
            raise _refuse(503, "SITE_CHAIN_UNAVAILABLE", str(error)) from error
        if body is None:
            raise _refuse(404, "THREAD_NOT_FOUND", f"No thread {thread_id!r} on Site {site_code!r}.")
        return jsonable_encoder({"schema_version": site_chain.SCHEMA_VERSION, "site": ref.site_code,
                                 "known_at": wire(known_at), "thread": body, "policy_versions": _versions(policy_versions)})

    @router.get(ESTATE_CHAIN_ROUTE)
    def estate_chain_route(request: Request, response: Response) -> dict[str, Any]:
        with perf.route(ESTATE_CHAIN_ROUTE, response):
            return _estate_chain(request)

    def _estate_chain(request: Request) -> dict[str, Any]:
        sites, parsed = estate_sites(request, authenticate=authenticate,
                                     estate=estate if service is not None else None, tenant=tenant,
                                     admitted=admitted, registry=registry, disclosed=disclosed,
                                     unavailable=unavailable)
        chain_reader = reader()
        lo, hi = parsed.from_.astimezone(timezone.utc), parsed.to.astimezone(timezone.utc)
        summary = service.summary(sites, lo, hi, parsed.known_at)
        req = chain_reader.request(sites[0].tenant_id if sites else None, parsed.known_at)
        items = opportunity_items(service.s.threads, sites, lo, hi, parsed.known_at)
        # §B14 Q7: the one count computation the Portfolio and estate Findings summaries also call.
        counted = estate_count_claims(req, sites, lo, hi, items, (SiteStoreUnavailable, *unavailable))
        grouped: dict[str, list[dict[str, Any]]] = {}
        for item in items or ():
            grouped.setdefault(item["site_code"], []).append(read_scope.thaw(item))
        by_code = {s["site_code"]: s for s in summary["sites"]}
        out = []
        for ref in sites:
            counts = counted.days.get(ref.site_code)
            entry = by_code.get(ref.site_code) or {}
            out.append({"code": ref.site_code, "domain": _site_type(ref),
                        "days": None if counts is None else counts.to_json(),  # None: the read failed, never zero
                        "rows": {r["category"]: {"state": r["state"], "state_label": r["state_label"]}
                                 for r in entry.get("rows", ())},
                        "threads": counted.threads.get(ref.site_code),
                        "opportunities": None if items is None else grouped.get(ref.site_code, [])})
        return jsonable_encoder({
            "schema_version": site_chain.SCHEMA_VERSION,
            "window": {"from": wire(lo), "to": wire(hi), "known_at": wire(parsed.known_at)},
            "sites": out, "counts": counted.claims_json(),
            "money_total": None, "policy_versions": _versions(policy_versions)})

    return router
