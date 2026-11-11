"""CH-5a2a B1 / CH5a2-R4(b): the screen-link `Ref` union and `href_for`, the only backend builder of a screen path.

A Ref is a plain JSON object (`{"kind": ..., ...}`), mirrored by the TS `Ref` in `frontend/src/shell/operatorSiteRoutes.ts`.
`href_for(ref)` here and `routeFor(ref)` in `frontend/src/shell/operatorSiteRoutes.ts` produce the same path; the
shared fixture `frontend/src/shell/__fixtures__/route-refs.json` holds one row per kind and enumerated view and is
read by both test suites.

Kinds:
- THREAD {site, id}: no screen yet (CH-5b), so `href_for` returns None.
- FINDING {site, id, revision?, view?, window?: {from, to, known_at}}.
- ACTION {site, id, view?, event_id?, recorded_at?}.
- OPPORTUNITY {site, id, known_at?}.
- CASE {site, id}: the work-request screen `/maintenance/requests/{id}`.
- EVIDENCE {site, capability?, window?: {from, to, known_at?}}: Site Evidence, or one Performance capability.
- SITE {site, view?, window?}: one enumerated Site view (`SITE_VIEWS`), the Site home when absent.
- ESTATE {view}: one enumerated estate path (`ESTATE_VIEWS`). No estate builder takes a query today.
- FUEL_FINDING {site, id, revision?}: an unexplained-fuel Finding's own page (DIESEL-1-R3l).
- FUEL_VERDICT {site, id}: a fuel domain Action's verdict page (DIESEL-1-R3m); no query.
- PRICES {site, key?, need?}: PR-1 (BL-68 §4.1), the Site price page `/sites/{site}/financials/prices`, opened at one
  price key or one model/data need. The frontend appends the shared range and `return`; the server never does.

Encoding is the frontend builders' own: path segments as `encodeURIComponent` (`quote(safe="")`), queries as
`URLSearchParams` (`urlencode`). There is no free path, and no outcome id (OL-1).
"""
from __future__ import annotations

from typing import Any, Mapping
from urllib.parse import parse_qsl, quote, urlencode

Ref = Mapping[str, Any]

KINDS = ("THREAD", "FINDING", "ACTION", "DOMAIN_VERDICT", "OPPORTUNITY", "CASE", "EVIDENCE", "SITE", "ESTATE",
         "FUEL_FINDING", "FUEL_VERDICT", "PRICES")

#: PR-1: the Site price page (`sitePricesHref`), under the Site's Financials tab (architect-answer-price-it §4.1).
PRICES_SUFFIX = "/financials/prices"

#: `siteFindingViewHref` (`FINDING_CHILD_VIEWS`).
FINDING_VIEWS = ("evidence", "history", "recommendation", "alternatives")
#: `siteActionHref` (`ACTION_CHILD_VIEWS`), the B1 subset.
ACTION_VIEWS = ("verification", "plan", "history")

#: One value per Site builder not covered by another kind: view -> suffix after `/sites/{site}`.
SITE_VIEWS: dict[str, str] = {
    "home": "",                                           # siteDetailHref
    "foundation": "/foundation",                          # siteFoundationHref
    "foundation_changes": "/foundation/changes",          # SITE_FOUNDATION_CHANGES_ROUTE_PATH
    "findings": "/findings",                              # siteFindingsHref
    "financials": "/financials",                          # siteFinancialsHref
    "financial_assumptions": "/financials/assumptions",   # siteFinancialAssumptionsHref
    "financial_scenarios": "/financials/scenarios",       # siteFinancialScenariosHref
    "ev": "/ev",                                          # siteEvHref(overview)
    "ev_evidence": "/ev/evidence",                        # siteEvHref(evidence)
    "ev_analysis": "/ev/evidence/analysis",               # siteEvHref(analysis)
    "ev_financials": "/ev/financials",                    # siteEvHref(financials)
    "ev_assumptions": "/ev/financial-assumptions",        # siteEvHref(assumptions)
    "ev_scenarios": "/ev/financials/scenarios",           # siteEvHref(scenarios)
    "work": "/work",                                      # siteWorkHref
    "work_incidents": "/work/incidents",                  # siteWorkIncidentsHref
    "work_maintenance": "/work/maintenance",              # siteWorkMaintenanceHref
    "health": "/health",                                  # siteHealthHref
    "assets": "/assets",                                  # siteAssetsHref
}

#: The estate path constants (`operatorSiteRoutes.ts` FINDINGS_PATH .. OPERATIONAL_RECORDS_PATH).
ESTATE_VIEWS: dict[str, str] = {
    "portfolio": "/portfolio",
    "findings": "/findings",
    "findings_cost": "/findings/cost",
    "findings_risks": "/findings/risks",
    "findings_opportunities": "/findings/opportunities",
    "actions": "/actions",
    "evidence": "/evidence",
    "financials": "/financials",
    "incidents": "/incidents",
    "maintenance": "/maintenance",
    "maintenance_preventive": "/maintenance/preventive",
    "operational_records": "/operational-records",
}

WINDOW_KEYS = ("from", "to", "known_at")


def _seg(value: Any) -> str:
    return quote(str(value), safe="")


def _site(ref: Ref) -> str:
    return f"/sites/{_seg(ref['site'])}"


def _with(path: str, pairs: list[tuple[str, Any]]) -> str:
    kept = [(k, str(v)) for k, v in pairs if v is not None and v != ""]
    return f"{path}?{urlencode(kept)}" if kept else path


def _window(ref: Ref) -> list[tuple[str, Any]]:
    w = ref.get("window") or {}
    return [(k, w.get(k)) for k in WINDOW_KEYS]


def href_for(ref: Ref | None) -> str | None:
    """The screen path of one Ref; None for no Ref and for a THREAD (no screen yet). An unknown kind or view raises."""
    if ref is None:
        return None
    kind = ref["kind"]
    if kind == "THREAD":
        return None
    if kind == "FINDING":
        base = f"{_site(ref)}/findings/{_seg(ref['id'])}"
        view = ref.get("view")
        if view is not None:
            if view not in FINDING_VIEWS:
                raise ValueError(f"unknown FINDING view {view!r}")
            base = f"{base}/{view}"
        if ref.get("window"):
            return _with(base, _window(ref))
        return _with(base, [("revision_id", ref.get("revision"))])
    if kind == "ACTION":
        base = f"{_site(ref)}/actions/{_seg(ref['id'])}"
        view = ref.get("view")
        if view is not None:
            if view not in ACTION_VIEWS:
                raise ValueError(f"unknown ACTION view {view!r}")
            base = f"{base}/{view}"
        return _with(base, [("event_id", ref.get("event_id")), ("recorded_at", ref.get("recorded_at"))])
    if kind == "DOMAIN_VERDICT":  # DD1b2-R6 O1: a MINI domain Action's verdict page (`siteMillVerificationHref`)
        return f"{_site(ref)}/domain-actions/{_seg(ref['id'])}/verification"
    if kind == "FUEL_FINDING":  # DIESEL-1-R3l: the unexplained-fuel Finding at its own address (`siteFuelFindingHref`)
        return _with(f"{_site(ref)}/fuel-findings/{_seg(ref['id'])}", [("revision_id", ref.get("revision"))])
    if kind == "FUEL_VERDICT":  # DIESEL-1-R3m: a fuel domain Action's verdict page (`siteFuelVerificationHref`)
        return f"{_site(ref)}/domain-actions/{_seg(ref['id'])}/fuel-verification"
    if kind == "PRICES":  # PR-1: the Site price page at one price key or one need (`sitePricesHref`)
        return _with(f"{_site(ref)}{PRICES_SUFFIX}", [("key", ref.get("key")), ("need", ref.get("need"))])
    if kind == "OPPORTUNITY":
        return _with(f"{_site(ref)}/opportunities/{_seg(ref['id'])}", [("known_at", ref.get("known_at"))])
    if kind == "CASE":
        return f"/maintenance/requests/{_seg(ref['id'])}"
    if kind == "EVIDENCE":
        cap = ref.get("capability")
        base = f"{_site(ref)}/performance/{_seg(cap)}" if cap else f"{_site(ref)}/evidence"
        return _with(base, _window(ref))
    if kind == "SITE":
        view = ref.get("view") or "home"
        if view not in SITE_VIEWS:
            raise ValueError(f"unknown SITE view {view!r}")
        return _with(f"{_site(ref)}{SITE_VIEWS[view]}", _window(ref))
    if kind == "ESTATE":
        view = ref["view"]
        if view not in ESTATE_VIEWS:
            raise ValueError(f"unknown ESTATE view {view!r}")
        return ESTATE_VIEWS[view]
    raise ValueError(f"unknown Ref kind {kind!r}")


def links_of(link_refs: Mapping[str, Ref | None]) -> dict[str, str | None]:
    """A legacy `links` dict built from its `link_refs` sibling (same keys), so the two cannot disagree."""
    return {key: href_for(ref) for key, ref in link_refs.items()}


def split_links(entries: Mapping[str, Any]) -> dict[str, Any]:
    """`{"links": ..., "link_refs": ...}` from one dict of Refs (keys ending `_label` are text and stay in `links`
    only): every href is `href_for` of its Ref."""
    links = {k: v if k.endswith("_label") else href_for(v) for k, v in entries.items()}
    link_refs = {k: None if v is None else dict(v) for k, v in entries.items() if not k.endswith("_label")}
    return {"links": links, "link_refs": link_refs}


# --- constructors (the only way body code makes a Ref; None-valued keys are left out) -------------------------

def _ref(kind: str, **fields: Any) -> dict[str, Any]:
    return {"kind": kind, **{k: v for k, v in fields.items() if v is not None}}


def window(lo: Any, hi: Any, known_at: Any = None) -> dict[str, Any]:
    return {k: v for k, v in (("from", lo), ("to", hi), ("known_at", known_at)) if v is not None}


def thread_ref(site: str, thread_id: str) -> dict[str, Any]:
    return _ref("THREAD", site=site, id=thread_id)


def finding_ref(site: str, finding_id: str, revision: str | None = None, *, view: str | None = None,
                window: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return _ref("FINDING", site=site, id=str(finding_id), revision=None if revision is None else str(revision),
                view=view, window=None if not window else dict(window))


def action_ref(site: str, action_id: str, *, view: str | None = None, event_id: str | None = None,
               recorded_at: str | None = None) -> dict[str, Any]:
    return _ref("ACTION", site=site, id=str(action_id), view=view,
                event_id=None if event_id is None else str(event_id), recorded_at=recorded_at)


def domain_verdict_ref(site: str, action_id: str) -> dict[str, Any]:
    """DD1b2-R6 O1: the verdict page of a domain Action raised from an opportunity (the mill); no query."""
    return _ref("DOMAIN_VERDICT", site=site, id=str(action_id))


def fuel_finding_ref(site: str, finding_id: str, revision: str | None = None) -> dict[str, Any]:
    """DIESEL-1-R3l: an unexplained-fuel Finding's own page (`/sites/{site}/fuel-findings/{id}?revision_id=`)."""
    return _ref("FUEL_FINDING", site=site, id=str(finding_id), revision=None if revision is None else str(revision))


def fuel_verdict_ref(site: str, action_id: str) -> dict[str, Any]:
    """DIESEL-1-R3m: the verdict page of a fuel domain Action (`/sites/{site}/domain-actions/{id}/fuel-verification`)."""
    return _ref("FUEL_VERDICT", site=site, id=str(action_id))


def prices_ref(site: str, *, key: str | None = None, need: str | None = None) -> dict[str, Any]:
    """PR-1: the Site price page, opened at one price `key` (SET_PRICE) or one `need` (NEEDS_MODEL), never both."""
    if key is not None and need is not None:
        raise ValueError("a PRICES ref names a price key or a need, not both")
    return _ref("PRICES", site=site, key=key, need=need)


def opportunity_ref(site: str, opportunity_id: str, known_at: str | None = None) -> dict[str, Any]:
    return _ref("OPPORTUNITY", site=site, id=str(opportunity_id), known_at=known_at)


def case_ref(site: str, case_id: str) -> dict[str, Any]:
    return _ref("CASE", site=site, id=str(case_id))


def evidence_ref(site: str, capability: str | None = None,
                 window: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return _ref("EVIDENCE", site=site, capability=capability, window=None if not window else dict(window))


def site_ref(site: str, view: str | None = None, window: Mapping[str, Any] | None = None) -> dict[str, Any]:
    if view is not None and view not in SITE_VIEWS:
        raise ValueError(f"unknown SITE view {view!r}")
    return _ref("SITE", site=site, view=None if view == "home" else view,
                window=None if not window else dict(window))


def estate_ref(view: str) -> dict[str, Any]:
    if view not in ESTATE_VIEWS:
        raise ValueError(f"unknown ESTATE view {view!r}")
    return _ref("ESTATE", view=view)


def query_window(query: str | None) -> dict[str, Any] | None:
    """The `from`/`to`/`known_at` of an already-proven window query (`evidence_money.proven_window_query`)."""
    if not query:
        return None
    pairs = dict(parse_qsl(query))
    return window(pairs.get("from"), pairs.get("to"), pairs.get("known_at"))
