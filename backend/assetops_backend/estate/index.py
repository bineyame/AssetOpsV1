"""W3-01 estate Finding, Action and scope reads over one authorized, read-only REPEATABLE READ snapshot.

Every row, summary, cited ID, eligibility flag and selection token is computed over the full authorized selected
set before paging (`.agent/W3-01-build-spec.md` "Final implementer dry-read", commit 2). The store's `read(work)`
runs `work(snapshot)` inside its one transaction; this module holds no storage technology.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

from assetops_backend.estate.coverage import (
    ACTIONS, COVERED, CURRENT, DOMAIN_OF_SITE_TYPE, HISTORICAL, MINI_GRID, NOT_APPLICABLE, PENDING, STALE, UNKNOWN,
    not_applicable, site_coverage)
from assetops_backend.estate.scope import (
    EstateRefusal, EstateRequest, EstateSelectionInconsistent, access_basis, cursor_after, cursor_known_at,
    decode_cursor, encode_cursor, selection_token, token_time, wire_time)

FINDINGS_SCHEMA, ACTIONS_SCHEMA, SCOPE_SCHEMA = "estate-finding-index-1", "estate-action-index-1", "estate-scope-1"
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
            "source_freshness": cov["source_freshness"]}


def _token_site(site: dict[str, Any], domain: str, cov: dict[str, Any]) -> dict[str, Any]:
    return {**cov, "site_id": site["site_id"], "domain": domain}


def _page(rows: list[dict[str, Any]], key: Callable[[dict[str, Any]], tuple], after: tuple | None,
          limit: int) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    remaining = rows if after is None else [r for r in rows if key(r) > after]
    page = remaining[:limit]
    return page, (page[-1] if len(remaining) > limit else None)


class EstateIndexService:
    def __init__(self, store: Any) -> None:
        self.store = store

    def _read(self, work: Callable[[Any], dict[str, Any]]) -> dict[str, Any]:
        """S12/S15: an inconsistent selected lineage is retried once in a fresh snapshot, then 409."""
        try:
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
        read_at: datetime = snap.read_at
        cursor = None if req.cursor is None else decode_cursor(req.kind, req.cursor)
        known = req.known_at
        if cursor is not None:
            pinned = cursor_known_at(cursor)
            if known is not None and known.replace(microsecond=0) != pinned.replace(microsecond=0):
                raise EstateRefusal("ESTATE_BASIS_CHANGED")
            known = pinned  # Reading: the cursor carries its page-one cutoff
        if known is not None and known > read_at:
            raise EstateRefusal("INVALID_KNOWN_AT")
        k = read_at if known is None else known
        snap.historical = k < read_at
        candidates = [] if tenant_id is None else snap.imported_sites(tenant_id, req.to)
        sites = [s for s in candidates if admit(s["site_code"])]
        ids = [str(s["site_id"]) for s in sites]
        return {"k": k, "historical": snap.historical, "sites": sites, "ids": ids, "cursor": cursor,
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
        if req.kind == "findings":
            expected.update(lens=req.lens, state_filter=req.state_filter)
        if any(cursor.get(key) != value for key, value in expected.items()):
            raise EstateRefusal("ESTATE_BASIS_CHANGED")
        at, row_id = cursor_after(cursor)
        return at, row_id

    @staticmethod
    def _cursor(tenant_id: Any, req: EstateRequest, scope: dict[str, Any], token: str, at: datetime,
                row_id: str) -> str:
        payload: dict[str, Any] = {
            "v": 1, "tenant_id": None if tenant_id is None else str(tenant_id).lower(),
            "authorized_site_ids": sorted(x.lower() for x in scope["ids"]), "access_basis": scope["access_basis"],
            "from": token_time(req.from_), "to": token_time(req.to), "known_at": token_time(scope["k"]),
            "selection_token": token, "after": [token_time(at), row_id]}
        if req.kind == "findings":
            payload.update(lens=req.lens, state_filter=req.state_filter)
        else:
            payload["kind"] = "actions"
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
        out = []
        for site in scope["sites"]:
            domain = DOMAIN_OF_SITE_TYPE.get(site["site_type"])
            cov = (not_applicable() if domain is None
                   else site_coverage(snap, tenant_id, site["site_id"], domain, req.from_, req.to, scope["k"]))
            out.append((site, domain or NOT_APPLICABLE, cov))
        return out

    def findings(self, tenant_id: Any, req: EstateRequest, admit: Admit) -> dict[str, Any]:
        return self._read(lambda snap: self._findings(snap, tenant_id, req, admit))

    def _findings(self, snap: Any, tenant_id: Any, req: EstateRequest, admit: Admit) -> dict[str, Any]:
        scope = self._scope(snap, tenant_id, req, admit)
        per_site = self._finding_coverage(snap, tenant_id, req, scope)
        states = [cov["state"] for _, _, cov in per_site]
        complete = _coverage_state(states) == "COMPLETE"
        rows: list[dict[str, Any]] = []
        for site, _, cov in per_site:
            code = site["site_code"]
            for r in cov["rows"]:
                flags = ["COST"] if r["consequence"]["state"] == "PRICED" else []
                fid, frid = r["finding_id"], r["finding_revision_id"]
                rows.append({
                    "finding_id": fid, "finding_revision_id": frid, "site_id": str(site["site_id"]),
                    "site_code": code, "site_name": site["site_name"], "finding_label": f"Finding {fid[:8]}",
                    "title": r["title"], "priority": None, "confidence": None, "confidence_reasons": [],
                    "lifecycle": r["lifecycle"], "lens_flags": flags, "consequence": r["consequence"],
                    "source_provenance": r["source_provenance"], "episode_start": wire_time(r["episode_start"]),
                    "status": cov["state"],
                    "links": {"finding": f"/sites/{code}/findings/{fid}?revision_id={frid}", "site": f"/sites/{code}"},
                    "_at": r["episode_start"], "_site": site})
        basis = rows if req.lens == "all" else [r for r in rows if LENS_FLAG[req.lens] in r["lens_flags"]]
        wanted = {"all": None, "supported": "SUPPORTED", "unconfirmed": "UNCONFIRMED",
                  "no_longer_supported": "NO_LONGER_SUPPORTED", "merged": "MERGED"}[req.state_filter]
        shown = basis if wanted is None else [r for r in basis if r["lifecycle"] == wanted]
        shown.sort(key=lambda r: (-r["_at"].timestamp(), r["finding_id"]))
        token = selection_token(tenant_id, scope["ids"], req.from_, req.to, scope["k"], req.lens, req.state_filter,
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
            if scope["historical"]:
                summary["as_of"] = wire_time(scope["k"])
        covered = sum(1 for s in states if s in COVERED)
        body = self._envelope(FINDINGS_SCHEMA, tenant_id, req, scope, covered, _status(scope["historical"], states),
                              {"state": _coverage_state(states),
                               "sites": [_coverage_site(site, cov) for site, _, cov in per_site]})
        body.update({"lens": req.lens, "state_filter": req.state_filter, "summary": summary, "order": FINDINGS_ORDER,
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
        per_site = []
        for site in scope["sites"]:
            applicable = DOMAIN_OF_SITE_TYPE.get(site["site_type"]) == MINI_GRID
            cov = (site_coverage(snap, tenant_id, site["site_id"], ACTIONS, req.from_, req.to, scope["k"])
                   if applicable else not_applicable())
            per_site.append((site, cov))
        states = [cov["state"] for _, cov in per_site]
        complete = _coverage_state(states) == "COMPLETE"
        rows = []
        for site, cov in per_site:
            code = site["site_code"]
            for r in cov["rows"]:
                rows.append({**{k: v for k, v in r.items() if not k.startswith("_")},
                             "site_id": str(site["site_id"]), "site_code": code, "site_name": site["site_name"],
                             "created_at": wire_time(r["created_at"]),
                             "links": {"action": f"/sites/{code}/actions/{r['action_id']}?event_id="
                                                 f"{r['selected_event_id']}",
                                       "source": f"/sites/{code}/findings/{r['source_finding_id']}?revision_id="
                                                 f"{r['source_finding_revision_id']}"},
                             "_at": r["created_at"], "_raw": r})
        rows.sort(key=lambda r: (-r["_at"].timestamp(), r["action_id"]))
        token = selection_token(tenant_id, scope["ids"], req.from_, req.to, scope["k"], None, None,
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
            if scope["historical"]:
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
