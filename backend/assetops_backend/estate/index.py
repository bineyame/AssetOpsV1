"""W3-01 estate Finding, Action and scope reads over one authorized, read-only REPEATABLE READ snapshot.

Every row, summary, cited ID, eligibility flag and selection token is computed over the full authorized selected
set before paging (`.agent/W3-01-build-spec.md` "Final implementer dry-read", commit 2). The store's `read(work)`
runs `work(snapshot)` inside its one transaction; this module holds no storage technology.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Callable

from assetops_backend import perf
from assetops_backend.chain import refs
from assetops_backend.chain.read import site_cutoff
from assetops_backend.chain.vocabulary import count_claim
from assetops_backend.estate.coverage import (
    ACTIONS, COVERED, CURRENT, DOMAIN_OF_SITE_TYPE, HISTORICAL, MINI_GRID, NOT_APPLICABLE, PARTIAL, PENDING, STALE,
    UNKNOWN, not_applicable, site_coverage)
from assetops_backend.estate.scope import (
    EstateRefusal, EstateRequest, EstateSelectionInconsistent, access_basis, cursor_after, cursor_known_at,
    cursor_marker, decode_cursor, decode_portfolio_cursor, encode_cursor, encode_portfolio_cursor,
    portfolio_cursor_key, selection_token, token_time, wire_time)
from assetops_backend.outcomes.display_code import finding_label
from assetops_backend.outcomes.outcome_map import categories_for, finding_signal_key, lens_flags

_LOG = logging.getLogger(__name__)

FINDINGS_SCHEMA, ACTIONS_SCHEMA, SCOPE_SCHEMA = "estate-finding-index-2", "estate-action-index-1", "estate-scope-1"
FINDINGS_ORDER, ACTIONS_ORDER = "episode_start desc, finding_id asc", "created_at desc, action_id asc"
LENS_FLAG = {"cost": "COST", "risks": "RISK", "opportunities": "OPPORTUNITY"}
Admit = Callable[[str], bool]


def _status(historical: bool, states: list[str]) -> str:
    """Estate precedence: explicit historical, then pending, then stale, then unknown, else current."""
    if historical:
        return HISTORICAL
    for state in (PENDING, STALE, UNKNOWN):
        if state in states:
            return state
    if PARTIAL in states:  # COV-PARTIAL: a partly checked Site is never a Current estate root
        return UNKNOWN
    return CURRENT


def _coverage_state(states: list[str]) -> str:
    applicable = [s for s in states if s != NOT_APPLICABLE]
    if all(s in COVERED for s in applicable):
        return "COMPLETE"
    return "UNKNOWN" if not any(s in COVERED for s in applicable) else "PARTIAL"


def _coverage_site(site: dict[str, Any], cov: dict[str, Any]) -> dict[str, Any]:
    return {"site_id": str(site["site_id"]), "state": cov["state"], "committed_watermark": wire_time(cov["watermark"]),
            "selection_id": None if cov["selection_id"] is None else str(cov["selection_id"]),
            "match_state": cov["match_state"], "job_state": cov["job_state"],
            "source_freshness": cov["source_freshness"], "days": cov.get("days")}


def _token_site(site: dict[str, Any], domain: str, cov: dict[str, Any]) -> dict[str, Any]:
    return {**cov, "site_id": site["site_id"], "domain": domain}


def _page(rows: list[dict[str, Any]], key: Callable[[dict[str, Any]], tuple], after: tuple | None,
          limit: int) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    remaining = rows if after is None else [r for r in rows if key(r) > after]
    page = remaining[:limit]
    return page, (page[-1] if len(remaining) > limit else None)


class _WindowRecorder:
    """Post-W6 W3-estate Q4/Q10: the caller's snapshot, recording the Site evidence cutoff and the exact selected
    windows `site_coverage` reads (no extra query), so a cold/EV Finding row knows which selected Site window
    holds it."""

    def __init__(self, snap: Any) -> None:
        self._snap, self.cutoff, self.windows = snap, None, []

    def __getattr__(self, name: str) -> Any:
        return getattr(self._snap, name)

    def evidence_cutoff(self, *args: Any) -> Any:
        self.cutoff = self._snap.evidence_cutoff(*args)
        return self.cutoff

    def selected_windows(self, *args: Any) -> list[dict[str, Any]]:
        self.windows = self._snap.selected_windows(*args)
        return self.windows


def _links(link_refs: dict[str, Any]) -> dict[str, Any]:
    """CH5a2-R4(a): a row's `links` (unchanged keys) and their `link_refs` sibling, each href from its Ref."""
    return {"links": refs.links_of(link_refs), "link_refs": link_refs}


def _finding_links(code: str, domain: str, fid: str, frid: str, rec: _WindowRecorder | None,
                   k: datetime) -> dict[str, Any]:
    """`_finding_link_refs` as the legacy `links` hrefs."""
    return refs.links_of(_finding_link_refs(code, domain, fid, frid, rec, k))


def _finding_link_refs(code: str, domain: str, fid: str, frid: str, rec: _WindowRecorder | None,
                       k: datetime) -> dict[str, Any]:
    """The Site home (EV `/sites/{code}/ev`) and the Finding route: mini-grid keeps its exact `revision_id`; a
    cold/EV Finding opens over the one selected Site window holding its winning revision with the proven row-local cutoff, else
    null (closure 5 B5 via `finding_window_href`)."""
    from assetops_backend.estate.evidence_money import finding_window_ref, site_home_ref  # import cycle
    if domain == MINI_GRID:
        finding = refs.finding_ref(code, fid, frid)
    else:
        holding = [w for w in (rec.windows if rec is not None else ())
                   if any(f["finding_revision_id"] == frid for f in w.get("findings") or ())]
        finding = (finding_window_ref(code, fid, holding[0]["window_start"], holding[0]["window_end"], rec.cutoff,
                                      rec.cutoff, k) if len(holding) == 1 else None)
    return {"finding": finding, "site": site_home_ref(code, domain)}


def opportunity_read(snap: Any, tenant_id: Any, scope: dict[str, Any], req: EstateRequest) -> list[dict[str, Any]] | None:
    """CH-4 §4: the opportunity items of every authorized Site in the request window as of the envelope's
    `known_at` (Findings and Portfolio share this one call). None only when the read raised (logged).
    One count rule for both: the count is `len(items)`, null only when this returns None."""
    try:
        reader = snap.opportunity_threads
    except (AttributeError, KeyError):  # a snapshot without the read (test fakes) has no opportunity items
        return []
    try:
        return reader(tenant_id, sorted(scope["ids"]), req.from_, req.to, scope["k"])
    except Exception:  # noqa: BLE001 - stated in the packet: the count reads "Unknown", never a guess
        _LOG.exception("opportunity read failed; the opportunity count and items are reported as not read")
        return None


def select_finding_scope(snap: Any, tenant_id: Any, req: EstateRequest,
                         scope: dict[str, Any], cutoffs: dict[str, Any] | None = None) -> tuple[list[tuple[dict[str, Any], str, dict[str, Any]]],
                                                          list[dict[str, Any]]]:
    """W3-03 closure 4 B1/B2: every authorized Site's `(site, domain, cov)` and every selected Finding row (all
    lifecycle heads) before lens/state filtering, sorting and paging, on the caller's one snapshot and `scope`.
    Private keys carry the Portfolio row facts (`_domain` stored Site type, `_episode_end`, `_mechanism`, and
    CC-R2's `_recurs_after`, `_transition`, `_revision_no`); the Findings root strips them with every other
    private key."""
    per_site, recorders = [], {}
    for site in scope["sites"]:
        domain = DOMAIN_OF_SITE_TYPE.get(site["site_type"])
        rec = None if domain in (None, MINI_GRID) else _WindowRecorder(snap)
        cov = (not_applicable() if domain is None
               else site_coverage(rec or snap, tenant_id, site["site_id"], domain, req.from_, req.to, scope["k"]))
        per_site.append((site, domain or NOT_APPLICABLE, cov))
        recorders[str(site["site_id"])] = rec
        if cutoffs is not None:
            # CH-5a2 B3 (R7): one cutoff per Site, through the one rule (`chain/read.py` `site_cutoff`): a cold/EV
            # Site's evidence cutoff (the board's resolved cutoff for that Site), never later than the estate
            # cutoff; a mini-grid Site has none (the envelope's cutoff applies). It replaces the per-row value.
            cutoffs[site["site_code"]] = (None if domain in (None, MINI_GRID) or rec is None
                                          else site_cutoff(domain, None, rec.cutoff, scope["k"]))
    rows: list[dict[str, Any]] = []
    for site, domain, cov in per_site:
        code = site["site_code"]
        rec = recorders[str(site["site_id"])]
        for r in cov["rows"]:
            # CH-5a2 B5 (I-21): one lens, the primary moved category's, through outcome_map only (OL-1). The
            # price stays in the consequence column.
            flags = lens_flags(finding_signal_key(r.get("mechanism")), domain)
            fid, frid = r["finding_id"], r["finding_revision_id"]
            rows.append({
                "finding_id": fid, "finding_revision_id": frid, "site_id": str(site["site_id"]),
                "site_code": code, "site_name": site["site_name"], "finding_label": finding_label(r["title"]),
                "title": r["title"], "priority": None, "confidence": None, "confidence_reasons": [],
                "lifecycle": r["lifecycle"], "lens_flags": flags, "consequence": r["consequence"],
                "source_provenance": r["source_provenance"], "episode_start": wire_time(r["episode_start"]),
                "status": cov["state"],
                # OUT-A2: the outcome categories of the stored mechanism on the coverage domain (NOT_MAPPED when
                # either is unknown).
                "categories": categories_for(finding_signal_key(r.get("mechanism")), domain),
                **_links(_finding_link_refs(code, domain, fid, frid, rec, scope["k"])),
                "_at": r["episode_start"], "_site": site, "_domain": site["site_type"],
                "_episode_end": r.get("episode_end"), "_mechanism": r.get("mechanism"),
                # CC-R2: the mini recurrence facts placement reads (null on cold and EV rows, C13).
                "_recurs_after": r.get("recurs_after_finding_id"), "_recurs_after_title": r.get("recurs_after_title"),
                "_transition": r.get("transition"),
                "_revision_no": r.get("revision_no")})
        if domain == MINI_GRID and cov["state"] in (CURRENT, HISTORICAL, PARTIAL):
            rows += _fuel_rows(snap, tenant_id, site, cov, req, scope["k"])
    return per_site, rows


# DIESEL-1-R3p, MOCK DEVIATION MD-FUEL-K4-1: the unexplained-fuel Finding joins the estate Finding rows here, after
# coverage and outside site_coverage/_mini_grid, so it never reaches select_financial_scope, selected_lines, money
# groups, estate_total or double_count_violations. Its money is its own fuel-residual-1 row, shown on its own and never
# added.
FUEL_MECHANISM = "UNEXPLAINED_FUEL"
# equals the stored fuel_residual_consequence_revision.basis and site_outcomes/mini.py FUEL_BASIS
FUEL_CONSEQUENCE_BASIS = "UNEXPLAINED_FUEL_AT_DECLARED_PRICE"


def _fuel_consequence(q: Any, live: bool) -> dict[str, Any]:
    """§9p.2 item 6: the row's own `fuel-residual-1` interval; PRICED only on a CURRENT Site."""
    from assetops_backend.fuel_balance import finding_text as fuel_text

    out = {"state": "UNPRICED", "amount": None, "amount_low": None, "amount_high": None, "currency": None,
           "source_revision_id": None, "basis": FUEL_CONSEQUENCE_BASIS}
    if q is None:
        return out
    out["source_revision_id"] = str(q["id"])
    if q.get("state") != "PRICED":
        return out
    if not live:
        out["state"] = "UNKNOWN"
        return out
    low = fuel_text.money(q["amount_low"])
    out.update(state="PRICED", amount=low, amount_low=low, amount_high=fuel_text.money(q["amount_high"]),
               currency=q.get("currency"))
    return out


def _fuel_rows(snap: Any, tenant_id: Any, site: dict[str, Any], cov: dict[str, Any], req: EstateRequest,
               k: datetime) -> list[dict[str, Any]]:
    """DIESEL-1-R3p §9p.2 item 4: one estate row per unexplained-fuel Finding of this mini Site (every key a mini row
    has, in the same order); none from a snapshot without the read."""
    from assetops_backend.estate.evidence_money import site_home_ref  # import cycle
    from assetops_backend.fuel_balance import finding_text as fuel_text

    reader = getattr(snap, "fuel_findings", None)
    if reader is None:
        return []
    code, out = site["site_code"], []
    for item in reader(tenant_id, site["site_id"], req.from_, req.to, k):
        f = item["finding"]
        fid, frid = str(f.finding_id), str(f.revision_id)
        out.append({
            "finding_id": fid, "finding_revision_id": frid, "site_id": str(site["site_id"]),
            "site_code": code, "site_name": site["site_name"], "finding_label": finding_label(fuel_text.TITLE),
            "title": fuel_text.TITLE, "priority": None, "confidence": None, "confidence_reasons": [],
            "lifecycle": str(f.lifecycle), "lens_flags": lens_flags(finding_signal_key(FUEL_MECHANISM), MINI_GRID),
            "consequence": _fuel_consequence(f.consequence, cov["state"] == CURRENT),
            "source_provenance": snap.finding_provenance(tenant_id, site["site_id"], frid, item["evidence_ids"]),
            "episode_start": wire_time(f.window.window_start), "status": cov["state"],
            "categories": categories_for(finding_signal_key(FUEL_MECHANISM), MINI_GRID),
            **_links({"finding": refs.fuel_finding_ref(code, fid), "site": site_home_ref(code, MINI_GRID)}),
            "_at": f.window.window_start, "_site": site, "_domain": site["site_type"],
            "_episode_end": f.window.window_end, "_mechanism": FUEL_MECHANISM,
            "_recurs_after": None, "_recurs_after_title": None, "_transition": None,
            "_revision_no": f.revision_no})
    return out


def select_action_scope(snap: Any, tenant_id: Any, req: EstateRequest,
                        scope: dict[str, Any]) -> tuple[list[tuple[dict[str, Any], dict[str, Any]]],
                                                         list[dict[str, Any]]]:
    """W3-03 closure 4 B1/B2: every authorized Site's `(site, cov)` and every selected Action created in the
    requested window, before sorting and paging, on the caller's one snapshot and `scope`."""
    per_site = []
    for site in scope["sites"]:
        applicable = DOMAIN_OF_SITE_TYPE.get(site["site_type"]) == MINI_GRID
        cov = (site_coverage(snap, tenant_id, site["site_id"], ACTIONS, req.from_, req.to, scope["k"])
               if applicable else not_applicable())
        per_site.append((site, cov))
    rows = []
    for site, cov in per_site:
        code = site["site_code"]
        for r in cov["rows"]:
            rows.append({**{k: v for k, v in r.items() if not k.startswith("_")},
                         "site_id": str(site["site_id"]), "site_code": code, "site_name": site["site_name"],
                         "created_at": wire_time(r["created_at"]),
                         **_links({"action": refs.action_ref(code, r["action_id"], event_id=r["selected_event_id"]),
                                   "source": None if r.get("source_finding_id") is None else refs.finding_ref(
                                       code, r["source_finding_id"], r.get("source_finding_revision_id"))}),
                         "_at": r["created_at"], "_raw": r})
    return per_site, rows


class EstateIndexService:
    #: CH-5a2b (§B14 Q7/Q8): the injected `chain.claims.EstateClaims` (`main.py`); None -> every claim NOT_KNOWN.
    count_claims: Callable[..., Any] | None = None

    def __init__(self, store: Any) -> None:
        self.store = store

    def _claims(self, tenant_id: Any, scope: dict[str, Any], req: EstateRequest) -> Any:
        """The one count computation (`chain.claims.estate_count_claims`) over the whole Site scope (no lens) in the
        request window at the request's own `known_at`, as `/estate/chain` reads it; None when not injected."""
        if self.count_claims is None:
            return None
        return self.count_claims(tenant_id, [s["site_code"] for s in scope["sites"]], req.from_, req.to,
                                 req.known_at)

    @staticmethod
    def claims_json(counted: Any, keys: tuple[str, ...]) -> dict[str, Any]:
        """`summary.claims` (wire-only until CH-5b / CH-6b): every key NOT_KNOWN when the computation is absent."""
        if counted is not None:
            return counted.claims_json(keys)
        return {k: count_claim(k, None, None).to_json() for k in keys}

    def _read(self, work: Callable[[Any], dict[str, Any]]) -> dict[str, Any]:
        """S12/S15: an inconsistent selected lineage is retried once in a fresh snapshot, then 409."""
        try:
            with perf.timed("estate.snapshot"):  # QW-1: one estate snapshot read, its work included
                return self.store.read(work)
        except EstateSelectionInconsistent:
            try:
                return self.store.read(work)
            except EstateSelectionInconsistent as error:
                raise EstateRefusal("ESTATE_SELECTION_INCONSISTENT") from error

    @staticmethod
    def _scope(snap: Any, tenant_id: Any, req: EstateRequest, admit: Admit) -> dict[str, Any]:
        """Read time, cutoff and the authorized imported Site set. The tenant is the server's; a denied candidate
        never enters a row, count or digest."""
        if req.kind == "portfolio":
            # W3-03 r1b Q-1b-1: the key is checked on every Portfolio request (page one and an empty scope too)
            # before any selection read; the MAC verifies before any cursor field is trusted.
            key = portfolio_cursor_key()
            cursor = None if req.cursor is None else decode_portfolio_cursor(req.cursor, key)
        else:
            cursor = None if req.cursor is None else decode_cursor(req.kind, req.cursor)
        read_at: datetime = snap.read_at
        known = req.known_at
        if known is not None and known > read_at:
            raise EstateRefusal("INVALID_KNOWN_AT")
        k = read_at if known is None else known
        if cursor is not None:
            # Run 8 ruling 2: the cursor's six-digit cutoff is the effective cutoff for every page-two read, whether
            # page one omitted or supplied `known_at`. A supplied cutoff must equal it at full precision, or be its
            # wire-second copy, which is normalized to the cursor instant before any read; else 409.
            cursor_k = cursor_known_at(cursor)
            if known is not None and known != cursor_k and not (
                    known.microsecond == 0 and known == cursor_k.replace(microsecond=0)):
                raise EstateRefusal("ESTATE_BASIS_CHANGED")
            k = cursor_k
        token_k = k
        snap.historical = k < read_at  # the response label (Run 8 ruling 2)
        snap.continuation = cursor is not None
        # c2 r1 M1: the selection basis is page one's mode, carried by the cursor; a continuation never re-derives it.
        snap.basis_historical = (snap.historical if cursor is None
                                 else cursor["page_one_mode"] == "historical")
        with perf.timed("estate.imported_sites"):  # QW-1
            candidates = [] if tenant_id is None else snap.imported_sites(tenant_id, req.to)
        sites = [s for s in candidates if admit(s["site_code"])]
        ids = [str(s["site_id"]) for s in sites]
        return {"k": k, "token_k": token_k, "historical": snap.historical, "sites": sites, "ids": ids,
                "cursor": cursor, "page_one_mode": "historical" if snap.basis_historical else "live",
                "access_basis": access_basis(tenant_id, ids)}

    @staticmethod
    def _fence(tenant_id: Any, req: EstateRequest, scope: dict[str, Any], token: str) -> tuple | None:
        cursor = scope["cursor"]
        if cursor is None:
            return None
        expected = {"tenant_id": None if tenant_id is None else str(tenant_id).lower(),
                    "authorized_site_ids": sorted(x.lower() for x in scope["ids"]),
                    "access_basis": scope["access_basis"], "from": token_time(req.from_), "to": token_time(req.to),
                    "selection_token": token}
        if req.kind in ("findings", "portfolio"):  # W3-03 B1/B2: Portfolio fences its lens and null state filter
            expected.update(lens=req.lens, state_filter=req.state_filter)
        if any(cursor.get(key) != value for key, value in expected.items()):
            raise EstateRefusal("ESTATE_BASIS_CHANGED")
        return cursor_after(cursor)

    @staticmethod
    def _cursor(tenant_id: Any, req: EstateRequest, scope: dict[str, Any], token: str, *after: Any) -> str:
        """Findings/Actions pass `(at, row_id)` (bytes unchanged); Evidence, Financials and Portfolio pass their ordered
        marker. Portfolio carries `kind` and its lens with a null state filter (W3-03 closure 4 B1/B2)."""
        payload: dict[str, Any] = {
            "v": 1, "tenant_id": None if tenant_id is None else str(tenant_id).lower(),
            "authorized_site_ids": sorted(x.lower() for x in scope["ids"]), "access_basis": scope["access_basis"],
            "from": token_time(req.from_), "to": token_time(req.to), "known_at": token_time(scope["token_k"]),
            "selection_token": token, "after": cursor_marker(req.kind, after),
            "page_one_mode": scope["page_one_mode"]}
        if req.kind == "findings":
            payload.update(lens=req.lens, state_filter=req.state_filter)
        else:
            payload["kind"] = req.kind
            if req.kind == "portfolio":  # W3-03 r1b Q-1b-1: only Portfolio is authenticated
                payload.update(lens=req.lens, state_filter=None)
                return encode_portfolio_cursor(payload, portfolio_cursor_key())
        return encode_cursor(payload)

    @staticmethod
    def _envelope(schema: str, tenant_id: Any, req: EstateRequest, scope: dict[str, Any], covered: int,
                  status: str, coverage: dict[str, Any]) -> dict[str, Any]:
        return {"schema_version": schema,
                "scope": {"tenant_id": None if tenant_id is None else str(tenant_id),
                          "authorized_site_count": len(scope["sites"]), "covered_site_count": covered,
                          "access_basis": scope["access_basis"]},
                "window": {"from": wire_time(req.from_), "to": wire_time(req.to), "bounds": "[from, to)",
                           "known_at": wire_time(scope["k"])},
                "status": status, "coverage": coverage}

    # --- Findings ---------------------------------------------------------------------------------------------

    def _finding_coverage(self, snap: Any, tenant_id: Any, req: EstateRequest,
                          scope: dict[str, Any]) -> list[tuple[dict[str, Any], str, dict[str, Any]]]:
        return select_finding_scope(snap, tenant_id, req, scope)[0]

    def findings(self, tenant_id: Any, req: EstateRequest, admit: Admit) -> dict[str, Any]:
        return self._read(lambda snap: self._findings(snap, tenant_id, req, admit))

    def _findings(self, snap: Any, tenant_id: Any, req: EstateRequest, admit: Admit) -> dict[str, Any]:
        scope = self._scope(snap, tenant_id, req, admit)
        per_site, rows = select_finding_scope(snap, tenant_id, req, scope)
        states = [cov["state"] for _, _, cov in per_site]
        complete = _coverage_state(states) == "COMPLETE"
        basis = rows if req.lens == "all" else [r for r in rows if LENS_FLAG[req.lens] in r["lens_flags"]]
        wanted = {"all": None, "supported": "SUPPORTED", "unconfirmed": "UNCONFIRMED",
                  "no_longer_supported": "NO_LONGER_SUPPORTED", "merged": "MERGED"}[req.state_filter]
        shown = basis if wanted is None else [r for r in basis if r["lifecycle"] == wanted]
        shown.sort(key=lambda r: (-r["_at"].timestamp(), r["finding_id"]))
        token = selection_token(tenant_id, scope["ids"], req.from_, req.to, scope["token_k"], req.lens, req.state_filter,
                                [_token_site(site, domain, cov) for site, domain, cov in per_site])
        after = self._fence(tenant_id, req, scope, token)
        key = (lambda r: (-r["_at"].timestamp(), r["finding_id"]))
        page, last = _page(shown, key, None if after is None else (-after[0].timestamp(), after[1]), req.limit)
        summary: dict[str, Any] = {"high_priority": None, "low_confidence": None, "awaiting_verification": None,
                                   "basis_count": None, "supported_findings": None}
        if complete:
            awaiting = 0
            for site, domain, cov in per_site:
                pairs = [(r["finding_id"], r["finding_revision_id"]) for r in basis if r["_site"] is site]
                if domain == MINI_GRID and pairs:
                    awaiting += snap.awaiting_verification(tenant_id, site["site_id"], pairs, scope["k"])
            summary.update(awaiting_verification=awaiting, basis_count=len(basis),
                           supported_findings=sum(1 for r in basis if r["lifecycle"] == "SUPPORTED"))
        if scope["historical"]:  # q12 ruling 1: a HISTORICAL response carries `as_of`, complete or not
            summary["as_of"] = wire_time(scope["k"])
        covered = sum(1 for s in states if s in COVERED)
        body = self._envelope(FINDINGS_SCHEMA, tenant_id, req, scope, covered, _status(scope["historical"], states),
                              {"state": _coverage_state(states),
                               "sites": [_coverage_site(site, cov) for site, _, cov in per_site]})
        # CH4-R R4: opportunity items are a separate, unpaged array (bounded by Sites, one per thread); the Finding
        # rows, order, total_count, token and cursor are unchanged.
        # COUNT RULE (shared with the Portfolio `summary.opportunity_count`): the count is the number of opportunity
        # items the read returned, whatever the lens, state filter or Finding-coverage completeness; it is null ONLY
        # when the opportunity read itself failed (sheet §2.3). A failed read carries `opportunities: null` so the
        # page says "could not be read" instead of an empty lens.
        items = opportunity_read(snap, tenant_id, scope, req)
        summary["opportunity_count"] = None if items is None else len(items)
        # CH-5a2b (§B13 R3, §B14 Q10): lens-independent, the whole scope on every lens.
        summary["claims"] = self.claims_json(self._claims(tenant_id, scope, req), ("count.opportunities",))
        opportunities = None if items is None else [] if req.lens not in ("all", "opportunities") else [
            i for i in items if req.state_filter == "all" or i["filter_state"] == req.state_filter]
        body.update({"lens": req.lens, "state_filter": req.state_filter, "summary": summary, "order": FINDINGS_ORDER,
                     "opportunities": opportunities,
                     "total_count": len(shown) if complete else None,
                     "rows": [{k: v for k, v in r.items() if not k.startswith("_")} for r in page],
                     "next_cursor": None if last is None else self._cursor(tenant_id, req, scope, token, last["_at"],
                                                                          last["finding_id"]),
                     "selection_token": token})
        return body

    # --- Actions ----------------------------------------------------------------------------------------------

    def actions(self, tenant_id: Any, req: EstateRequest, admit: Admit) -> dict[str, Any]:
        return self._read(lambda snap: self._actions(snap, tenant_id, req, admit))

    def _actions(self, snap: Any, tenant_id: Any, req: EstateRequest, admit: Admit) -> dict[str, Any]:
        scope = self._scope(snap, tenant_id, req, admit)
        per_site, rows = select_action_scope(snap, tenant_id, req, scope)
        states = [cov["state"] for _, cov in per_site]
        complete = _coverage_state(states) == "COMPLETE"
        rows.sort(key=lambda r: (-r["_at"].timestamp(), r["action_id"]))
        token = selection_token(tenant_id, scope["ids"], req.from_, req.to, scope["token_k"], None, None,
                                [_token_site(site, ACTIONS, cov) for site, cov in per_site])
        after = self._fence(tenant_id, req, scope, token)
        key = (lambda r: (-r["_at"].timestamp(), r["action_id"]))
        page, last = _page(rows, key, None if after is None else (-after[0].timestamp(), after[1]), req.limit)
        summary: dict[str, Any] = {"open_actions": None, "due_overdue": None, "verification_window": None,
                                   "verified_in_30_days": None, "basis_count": None}
        if complete:
            summary.update(open_actions=sum(1 for r in rows if r["_raw"]["_open"]),
                           verification_window=sum(1 for r in rows if r["_raw"]["_verification_window"]),
                           verified_in_30_days=sum(1 for r in rows if r["_raw"]["_verified_recent"]),
                           basis_count=len(rows))
        if scope["historical"]:  # q12 ruling 1: a HISTORICAL response carries `as_of`, complete or not
            summary["as_of"] = wire_time(scope["k"])
        covered = sum(1 for s in states if s in COVERED or s == NOT_APPLICABLE)
        applicable = [s for s in states if s != NOT_APPLICABLE]
        body = self._envelope(ACTIONS_SCHEMA, tenant_id, req, scope, covered,
                              _status(scope["historical"], applicable),
                              {"state": _coverage_state(states), "sites": [_coverage_site(s, c) for s, c in per_site]})
        body.update({"summary": summary, "order": ACTIONS_ORDER, "total_count": len(rows) if complete else None,
                     "rows": [{k: v for k, v in r.items() if not k.startswith("_")} for r in page],
                     "next_cursor": None if last is None else self._cursor(tenant_id, req, scope, token, last["_at"],
                                                                          last["action_id"]),
                     "selection_token": token})
        return body

    # --- scope ------------------------------------------------------------------------------------------------

    def site_list(self, tenant_id: Any, req: EstateRequest, admit: Admit) -> dict[str, Any]:
        """CH-5a1 R2 (CH5a1-R Q3): the summary's Site list: `_scope` only, on the one estate snapshot `scope()`
        would open, never `_finding_coverage`; so no selection inconsistency (409) can arise from it."""
        def work(snap: Any) -> dict[str, Any]:
            scope = self._scope(snap, tenant_id, req, admit)
            return {"sites": [{"site_id": str(site["site_id"]), "site_code": site["site_code"],
                               "site_name": site["site_name"]} for site in scope["sites"]],
                    "known_at": wire_time(scope["k"])}
        return self._read(work)

    def scope(self, tenant_id: Any, req: EstateRequest, admit: Admit) -> dict[str, Any]:
        def work(snap: Any) -> dict[str, Any]:
            scope = self._scope(snap, tenant_id, req, admit)
            per_site = self._finding_coverage(snap, tenant_id, req, scope)
            return {"schema_version": SCOPE_SCHEMA,
                    "sites": [{"site_id": str(site["site_id"]), "site_code": site["site_code"],
                               "site_name": site["site_name"], "coverage_state": cov["state"]}
                              for site, _, cov in per_site],
                    "authorized_site_count": len(per_site),
                    "covered_site_count": sum(1 for _, _, cov in per_site if cov["state"] in COVERED),
                    "access_basis": scope["access_basis"], "known_at": wire_time(scope["k"])}
        return self._read(work)
