"""W3-03 run 1a: the estate Portfolio scope, coverage, selected Finding rows, full-scope token and cursor.

One read-only snapshot (`PostgresEvidenceMoneyRead.read`) runs the four reviewed full-scope selectors once
(`select_finding_scope`, `select_action_scope`, `select_evidence_scope`, `select_financial_scope`) on one shared
`scope` (`.agent/W3-03-build-spec.md` closure 4 B1/B2). It reduces F/E/M independently (closure 5 S4), assembles one
`estate-selection/2` token from unions of each Site's full selected arrays, filters the Finding set to the
`SUPPORTED|UNCONFIRMED` management-action membership, re-sorts it in the Portfolio order and pages it with the
five-member marker. Cards, objectives, prompt, progress, money and footer are run 1b.
"""

from __future__ import annotations

from typing import Any, Iterable
from urllib.parse import quote

from assetops_backend.estate.coverage import COVERED, MINI_GRID, NOT_APPLICABLE, PENDING
from assetops_backend.estate.evidence_money import (
    CONTRADICTORY, EMPTY, EMPTY_SCOPE, FULL, LIMITED, NONE, EstateEvidenceService, select_evidence_scope)
from assetops_backend.estate.financials import APPLICABLE, select_financial_scope
from assetops_backend.estate.index import (
    LENS_FLAG, Admit, _coverage_site, _token_site, select_action_scope, select_finding_scope)
from assetops_backend.estate.scope import (
    SITE_TOKEN_ARRAYS, EstateRequest, resume_after, selection_token, wire_time)

PORTFOLIO_SCHEMA = "estate-portfolio-1"
PORTFOLIO_ORDER = ("episode_start desc nulls last, site_code_key asc, site_id asc, finding_id asc, "
                   "finding_revision_id asc")
#: Closure 1: only these selected lifecycle heads are current management work; the others stay in the token.
MEMBERS = ("SUPPORTED", "UNCONFIRMED")
COMPLETE, PARTIAL, UNKNOWN_STATE = "COMPLETE", "PARTIAL", "UNKNOWN"
CURRENT_STATUS, HISTORICAL_STATUS, PENDING_STATUS, UNKNOWN_STATUS = "CURRENT", "HISTORICAL", "PENDING", "UNKNOWN"
#: Closure 5 S4 unit classes: settled and known, unresolved, proven non-applicable.
G, U, N = "G", "U", "N"
#: S12: the stored Site type whose exact Finding route is reviewed (W1 mini-grid only).
DOMAIN_FOR_LINK = {"MINIGRID": MINI_GRID}
_UNSETTLED_JOBS = ("PENDING", "FAILED", "NONE")
_UNRESOLVED_MATCH = ("MISSING", "PENDING")


# --- closure 5 S4: unit classes and the complete estate reduction ----------------------------------------------

def reduce_units(site_count: int, classes: Iterable[str]) -> str:
    """The four-row table: 0 Sites EMPTY; no U COMPLETE (including all-N); G and U PARTIAL; only U UNKNOWN."""
    if site_count == 0:
        return EMPTY
    counted = [c for c in classes if c != N]
    if U not in counted:
        return COMPLETE
    return PARTIAL if G in counted else UNKNOWN_STATE


def settled(cov: dict[str, Any]) -> bool:
    """A settled `CURRENT` or selected-as-of `HISTORICAL` basis (S4 row 3, r1a2 item 1): a selected head, a settled
    match and a non-stale source. `CURRENT` also refuses a pending/failed job; a selected `HISTORICAL` head is
    settled whatever its outstanding W3-01 job marker says (`NONE` = no selected as-of head stays U)."""
    if cov["state"] not in COVERED or cov["source_freshness"] == "STALE" or cov["match_state"] in _UNRESOLVED_MATCH:
        return False
    if cov["state"] == "HISTORICAL":
        return cov["job_state"] != "NONE"
    return cov["job_state"] not in _UNSETTLED_JOBS


def money_pending(cov: dict[str, Any], lines: list[dict[str, Any]]) -> bool:
    """r1b Q-1b-3: W3-02's private `_pending_guard` (a selected cold `withheld` or EV `ERROR_PENDING` window, with or
    without a line) is authoritative. A selected `PENDING` line on an uncovered window stays sufficient evidence
    (r1b reading 2) but is not a prerequisite; `_windows_covered=false` alone is UNKNOWN, not PENDING."""
    if cov.get("_pending_guard"):
        return True
    return not cov.get("_windows_covered") and any(line.get("eligibility") == "PENDING" for line in lines)


def finding_unit(domain: str, cov: dict[str, Any]) -> str:
    """F from the Site's selected Finding `site_coverage`; an unknown physical configuration is U, never N."""
    return U if domain == NOT_APPLICABLE or not settled(cov) else G


def evidence_unit(domain: str, cov: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    """S4 E table for one authorized Site. No row is unproved applicability (U), never N."""
    if domain == NOT_APPLICABLE or not settled(cov) or not rows:
        return U
    for row in rows:
        if row["raw_state"] == "HISTORICAL":
            # A selected as-of head is settled; its display readiness is cleared by the historical rule, so only a
            # selected as-of CONTRADICTORY or a row without a selected head is unresolved.
            if not row["selected_revision_ids"] or row["readiness"] == CONTRADICTORY:
                return U
        elif row["readiness"] not in (FULL, LIMITED, NONE):
            return U
    return G


def money_units(domain: str, cov: dict[str, Any], lines: list[dict[str, Any]]) -> dict[str, str]:
    """S4 M table: one unit per W3-02-applicable category of the Site plus any selected category outside it
    (e.g. RECORDED_REPAIR); other domains' categories are N and absent. `_windows_covered` is the per-Site
    category-window coverage whose conjunction is W3-02's `UNKNOWN_COVERAGE`."""
    if domain == NOT_APPLICABLE:
        return {"UNPROVED_CONFIGURATION": U}
    known = settled(cov) and bool(cov.get("_windows_covered"))
    categories = sorted({*APPLICABLE[domain], *(line["category"] for line in lines)})
    return {category: G if known else U for category in categories}


# --- row projection ----------------------------------------------------------------------------------------------

def order_key(row: dict[str, Any]) -> tuple:
    at = row["_at"]
    return (at is None, 0.0 if at is None else -at.timestamp(), *row["_marker"][1:])


class ActionSelectionError(RuntimeError):
    """An Action row reached the Portfolio join without its selected event time: an internal selection error."""


def _action_for(row: dict[str, Any], actions: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Closure 4 S9 / r1a Q-1a-1: the exact `(origin_finding_id, origin_finding_revision_id)` join; several matches
    choose the latest selected Action event `recorded_at`, then `action_id` ascending. No fallback."""
    matches = [a for a in actions if (a["source_finding_id"], a["source_finding_revision_id"])
               == (row["finding_id"], row["finding_revision_id"])]
    if not matches:
        return None
    if any(a["_raw"].get("_selected_recorded_at") is None for a in matches):
        raise ActionSelectionError("A matching Action has no selected event time.")
    return min(matches, key=lambda a: (-a["_raw"]["_selected_recorded_at"].timestamp(), a["action_id"]))


def workflow_label(action: dict[str, Any] | None) -> str:
    """Closure 5 S7: the first matching selected fact; table order is precedence."""
    if action is None:
        return "Recommendation not accepted"
    if action["resolution_state"] == "RESOLVED" and action["verification_outcome"] == "VERIFIED":
        return "Verified"
    if action["resolution_state"] == "RESOLUTION_WITHDRAWN":
        return "Resolution withdrawn"
    if action["_raw"].get("_verification_window") and action["resolution_state"] != "RESOLVED":
        return "Outcome pending"
    if action["application_state"] == "PENDING":
        return "Pending"
    if action["application_state"] == "APPLIED":
        return "Applied"
    return "No action yet"


def portfolio_row(r: dict[str, Any], actions: list[dict[str, Any]]) -> dict[str, Any]:
    site = r["_site"]
    code = quote(site["site_code"], safe="")
    fid, frid = r["finding_id"], r["finding_revision_id"]
    action = _action_for(r, actions)
    return {
        "site_id": r["site_id"], "site_code": r["site_code"], "site_name": r["site_name"], "domain": r["_domain"],
        "finding_id": fid, "finding_revision_id": frid, "finding_label": r["finding_label"], "title": r["title"],
        "mechanism": r["_mechanism"], "episode_start": r["episode_start"], "episode_end": wire_time(r["_episode_end"]),
        "lifecycle": r["lifecycle"], "lens_flags": r["lens_flags"], "priority": r["priority"],
        "confidence": r["confidence"], "confidence_reasons": r["confidence_reasons"],
        "consequence": r["consequence"],
        "action_id": None if action is None else action["action_id"],
        "action_title": None if action is None else action["action_title"],
        "action_state": None if action is None else action["application_state"],
        "application_state": None if action is None else action["application_state"],
        "resolution_state": None if action is None else action["resolution_state"],
        "verification_outcome": None if action is None else action["verification_outcome"],
        "workflow_label": workflow_label(action),
        "next_move": None, "source_provenance": r["source_provenance"],
        "links": {"site": f"/sites/{code}",
                  # S12: only the W1 mini-grid exact Finding route is reviewed; cold/EV stay inert.
                  "finding": (f"/sites/{code}/findings/{fid}?revision_id={frid}"
                              if DOMAIN_FOR_LINK.get(r["_domain"]) else None),
                  "action": None if action is None else
                  f"/sites/{code}/actions/{action['action_id']}?event_id={action['selected_event_id']}"},
        "_at": r["_at"], "_marker": (r["_at"], str(site["site_code_key"]), r["site_id"].lower(), fid, frid)}


# --- the token ---------------------------------------------------------------------------------------------------

def _ids(values: Iterable[Any]) -> list[str]:
    return sorted({str(v).lower() for v in values if v is not None})


def _evidence_arrays(rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    """As W3-02 `_evidence` builds its token arrays."""
    return {"selected_assessment_revision_ids": _ids(x for r in rows for x in r["_assessments"]),
            "cited_accepted_evidence_ids": _ids(x for r in rows for x in (*r["_cited"], *r["_token_cited"]))}


def _money_arrays(cov: dict[str, Any], lines: list[dict[str, Any]]) -> dict[str, list[str]]:
    """As W3-02 `financials_body` builds its token arrays."""
    return {"selected_finding_revision_ids": _ids(x["finding_revision_id"] for x in lines),
            "selected_consequence_revision_ids": _ids(x["consequence_revision_id"] for x in lines),
            "selected_assumption_revision_ids": _ids(a for x in lines for a in x["assumption_revision_ids"]),
            "selected_assessment_revision_ids": _ids([*(cov.get("selected_assessment_revision_ids") or ()),
                                                      *cov.get("_sessions", ())]),
            "cited_accepted_evidence_ids": _ids(e for x in lines for e in x["basis_evidence_ids"])}


def token_site(site: dict[str, Any], domain: str, cov: dict[str, Any], parts: list[dict[str, Any]]) -> dict:
    """S4/S5: the Finding-domain `site_coverage` base plus, per array, the union of every root's full arrays."""
    arrays = {key: _ids(x for part in (cov, *parts) for x in (part.get(key) or ())) for key in SITE_TOKEN_ARRAYS}
    return _token_site(site, domain, {**cov, **arrays})


# --- the service -------------------------------------------------------------------------------------------------

class EstatePortfolioService(EstateEvidenceService):
    """`GET /api/estate/portfolio` over the shared W3-01 authorization, cutoff, fence, cursor and envelope."""

    def portfolio(self, tenant_id: Any, req: EstateRequest, admit: Admit) -> dict[str, Any]:
        return self._read(lambda snap: self._portfolio(snap, tenant_id, req, admit))

    def _portfolio(self, snap: Any, tenant_id: Any, req: EstateRequest, admit: Admit) -> dict[str, Any]:
        scope = self._scope(snap, tenant_id, req, admit)
        f_sites, f_rows = select_finding_scope(snap, tenant_id, req, scope)
        a_sites, a_rows = select_action_scope(snap, tenant_id, req, scope)
        e_sites, _ = select_evidence_scope(snap, tenant_id, req, scope)
        m_sites, _, _, _, _, _ = select_financial_scope(snap, tenant_id, req, scope)
        by = lambda per: {str(x[0]["site_id"]): x for x in per}  # noqa: E731 - per-Site lookup
        actions_by, evidence_by, money_by = by(a_sites), by(e_sites), by(m_sites)

        units, token_sites, covered = {"F": [], "E": [], "M": []}, [], 0
        pending = False
        for site, domain, cov in f_sites:
            sid = str(site["site_id"])
            _, e_domain, e_cov, e_rows = evidence_by[sid]
            _, m_domain, m_cov, m_lines = money_by[sid]
            f = finding_unit(domain, cov)
            e = evidence_unit(e_domain, e_cov, e_rows)
            m = list(money_units(m_domain, m_cov, m_lines).values())
            units["F"].append(f)
            units["E"].append(e)
            units["M"] += m
            covered += all(c != U for c in (f, e, *m))
            pending = pending or money_pending(m_cov, m_lines) or any(
                c["state"] == PENDING or c["job_state"] == "PENDING" for c in (cov, e_cov, m_cov))
            token_sites.append(token_site(site, domain, cov, [
                actions_by[sid][1], {**e_cov, **_evidence_arrays(e_rows)}, {**m_cov, **_money_arrays(m_cov, m_lines)}]))
        count = len(scope["sites"])
        states = {key: reduce_units(count, units[key]) for key in ("F", "E", "M")}
        if count == 0:
            status = EMPTY_SCOPE
        elif snap.basis_historical:  # S1/S2: page two keeps page one's basis mode, never the captured cutoff
            status = HISTORICAL_STATUS
        elif pending:
            status = PENDING_STATUS
        elif any(state != COMPLETE for state in states.values()):
            status = UNKNOWN_STATUS
        else:
            status = CURRENT_STATUS

        token = selection_token(tenant_id, scope["ids"], req.from_, req.to, scope["token_k"], req.lens, None,
                                token_sites)
        after = self._fence(tenant_id, req, scope, token)
        members = [portfolio_row(r, a_rows) for r in f_rows if r["lifecycle"] in MEMBERS]
        shown = members if req.lens == "all" else [r for r in members if LENS_FLAG[req.lens] in r["lens_flags"]]
        shown.sort(key=order_key)
        start = 0 if after is None else resume_after([r["_marker"] for r in shown], after)
        page = shown[start:start + req.limit]
        last = page[-1] if start + req.limit < len(shown) else None

        coverage_state = reduce_units(count, [*units["F"], *units["E"], *units["M"]])
        body = self._envelope(PORTFOLIO_SCHEMA, tenant_id, req, scope, covered, status,
                              {"state": coverage_state, "finding_state": states["F"],
                               "evidence_state": states["E"], "money_state": states["M"],
                               "sites": [_coverage_site(site, cov) for site, _, cov in f_sites]})
        # r1a M1: the all-lens count is an estate claim; only complete (or complete-empty) Finding coverage makes it.
        summary: dict[str, Any] = {"finding_count": len(members) if states["F"] in (COMPLETE, "EMPTY") else None}
        body.update({"lens": req.lens, "summary": summary, "order": PORTFOLIO_ORDER, "total_count": len(shown),
                     "rows": [{k: v for k, v in r.items() if not k.startswith("_")} for r in page],
                     "next_cursor": None if last is None else self._cursor(tenant_id, req, scope, token,
                                                                          *last["_marker"]),
                     "selection_token": token})
        return body
