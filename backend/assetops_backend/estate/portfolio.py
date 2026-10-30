"""W3-03 run 1a: the estate Portfolio scope, coverage, selected Finding rows, full-scope token and cursor.

One read-only snapshot (`PostgresEvidenceMoneyRead.read`) runs the four reviewed full-scope selectors once
(`select_finding_scope`, `select_action_scope`, `select_evidence_scope`, `select_financial_scope`) on one shared
`scope` (`.agent/W3-03-build-spec.md` closure 4 B1/B2). It reduces F/E/M independently (closure 5 S4), assembles one
`estate-selection/2` token from unions of each Site's full selected arrays, filters the Finding set to the
`SUPPORTED|UNCONFIRMED` management-action membership, re-sorts it in the Portfolio order and pages it with the
five-member marker. Run 1b adds the full-scope projections (selected lines, money, scope disclosure, five value
cards, objectives, evidence prompt, opportunity, progress, footer, summary) from the same six selector returns,
never from the page (`.agent/W3-03-build-spec.md` closure 1 projections, closure 2 N2/N5, r1a, r1b).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable
from urllib.parse import quote

from assetops_backend.estate.coverage import (
    COLD, COVERED, DOMAIN_OF_SITE_TYPE, EV, MINI_GRID, NOT_APPLICABLE, PENDING)
from assetops_backend.estate.evidence_money import (
    CONTRADICTORY, EMPTY, EMPTY_SCOPE, FULL, LIMITED, NONE, EstateEvidenceService, select_evidence_scope,
    site_home_href)
from assetops_backend.estate.evidence_money import _groups as evidence_gap_groups
from assetops_backend.estate.financials import (
    APPLICABLE, COMPARABLE, ELIGIBLE, SINGLE_LINE, UNPRICED, select_financial_scope)
from assetops_backend.estate.index import (
    LENS_FLAG, Admit, _coverage_site, _coverage_state, _token_site, select_action_scope, select_finding_scope)
from assetops_backend.estate.placement import GROUPS, place
from assetops_backend.outcomes.catalogue import CATEGORIES, OUTCOME_BY_KEY
from assetops_backend.outcomes.outcome_map import categories_for, finding_signal_key, outcome_roles
from assetops_backend.estate.scope import (
    SITE_TOKEN_ARRAYS, EstateRequest, estate_request, resume_after, selection_token, wire_time)

PORTFOLIO_SCHEMA = "estate-portfolio-1"
#: CC-R2 (R5.4): placement group first, then the existing most-recent-first order.
PORTFOLIO_ORDER = ("group_rank asc, episode_start desc nulls last, site_code_key asc, site_id asc, finding_id asc, "
                   "finding_revision_id asc")
#: Closure 1: only these selected lifecycle heads are current management work; the others stay in the token.
MEMBERS = ("SUPPORTED", "UNCONFIRMED")
COMPLETE, PARTIAL, UNKNOWN_STATE = "COMPLETE", "PARTIAL", "UNKNOWN"
CURRENT_STATUS, HISTORICAL_STATUS, PENDING_STATUS, UNKNOWN_STATUS = "CURRENT", "HISTORICAL", "PENDING", "UNKNOWN"
#: Closure 5 S4 unit classes: settled and known, unresolved, proven non-applicable.
G, U, N = "G", "U", "N"
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
    """CC-R2: `(group_rank, at is None, -ts, *marker[2:])`; the marker is `(group_rank, at, site_code_key, site_id,
    finding_id, finding_revision_id)`."""
    at = row["_at"]
    return (row["_marker"][0], at is None, 0.0 if at is None else -at.timestamp(), *row["_marker"][2:])


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


#: The public name of the exact Finding-to-Action join, for the Site outcome board (OUT-B2 review L1).
action_for = _action_for


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


def line_groups(lines: list[dict[str, Any]], groups: list[dict[str, Any]]) -> dict[str, str]:
    """CC-R2 (Q-C7): each line's Finding revision -> the `state` of the money group whose `line_keys` hold that
    line, from the same call's `compare()` groups (no query). A revision without a line is absent."""
    state_of = {key: g["state"] for g in groups for key in g["line_keys"]}
    out: dict[str, str] = {}
    for line in lines:
        frid = line.get("finding_revision_id")
        if frid is not None and line["line_key"] in state_of:
            out.setdefault(str(frid), state_of[line["line_key"]])
    return out


def portfolio_row(r: dict[str, Any], actions: list[dict[str, Any]], site_cov: dict[str, Any] | None = None,
                  line_group: str | None = None) -> dict[str, Any]:
    site = r["_site"]
    code = quote(site["site_code"], safe="")
    fid, frid = r["finding_id"], r["finding_revision_id"]
    action = _action_for(r, actions)
    placed = place(r, action, site_cov or {}, line_group)  # CC-R2: row facts only; `priority` stays null
    return {
        "site_id": r["site_id"], "site_code": r["site_code"], "site_name": r["site_name"], "domain": r["_domain"],
        "finding_id": fid, "finding_revision_id": frid, "finding_label": r["finding_label"], "title": r["title"],
        "mechanism": r["_mechanism"],
        # OUT-A2 (ruling A-Q5): the stored Site type mapped to its coverage domain, so this equals the Findings row.
        "categories": categories_for(finding_signal_key(r["_mechanism"]),
                                     DOMAIN_OF_SITE_TYPE.get(r["_domain"], NOT_APPLICABLE)),
        "episode_start": r["episode_start"], "episode_end": wire_time(r["_episode_end"]),
        "lifecycle": r["lifecycle"], "lens_flags": r["lens_flags"], "priority": r["priority"],
        "placement": placed.wire(), "confidence": placed.confidence,
        "confidence_reasons": list(placed.confidence_reasons),
        "consequence": r["consequence"],
        "action_id": None if action is None else action["action_id"],
        "action_title": None if action is None else action["action_title"],
        "action_state": None if action is None else action["application_state"],
        "application_state": None if action is None else action["application_state"],
        "resolution_state": None if action is None else action["resolution_state"],
        "verification_outcome": None if action is None else action["verification_outcome"],
        "workflow_label": workflow_label(action),
        "next_move": None, "source_provenance": r["source_provenance"],
        # Post-W6 W3-estate Q2/Q10 (S12 inert restriction removed): the Site home (EV `/sites/{code}/ev`) and the
        # Finding route `select_finding_scope` proved: mini-grid `revision_id`; cold/EV the selected Site window
        # holding the Finding with its proven row-local cutoff, else null.
        "links": {"site": r["links"]["site"], "finding": r["links"]["finding"],
                  "action": None if action is None else
                  f"/sites/{code}/actions/{action['action_id']}?event_id={action['selected_event_id']}"},
        "_at": r["_at"],
        "_marker": (placed.group_rank, r["_at"], str(site["site_code_key"]), r["site_id"].lower(), fid, frid)}


def category_counts(members: list[dict[str, Any]], known: bool) -> dict[str, dict[str, int | None]]:
    """OUT-A2: per category, the members carrying it in any role and the distinct Sites whose member's primary
    moved outcome is in it. A NOT_MAPPED member counts nowhere."""
    if not known:
        return {c: {"open_findings": None, "sites_with_primary_finding": None} for c in CATEGORIES}
    open_findings = {c: 0 for c in CATEGORIES}
    primary_sites: dict[str, set[str]] = {c: set() for c in CATEGORIES}
    for r in members:
        for c in {item["category"] for item in r["categories"]["items"]}:
            open_findings[c] += 1
        moves, _ = outcome_roles(finding_signal_key(r["mechanism"]),
                                 DOMAIN_OF_SITE_TYPE.get(r["domain"], NOT_APPLICABLE))
        if moves:
            primary_sites[OUTCOME_BY_KEY[moves[0]].category].add(r["site_id"])
    return {c: {"open_findings": open_findings[c], "sites_with_primary_finding": len(primary_sites[c])}
            for c in CATEGORIES}


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


# --- run 1b: full-scope projections (never from the page) --------------------------------------------------------

OPERATING_COST = "CANDIDATE_OPERATING_COST_EXPOSURE"
GROSS_TARIFF = "GROSS_TARIFF_SCENARIO"
OBJECTIVE_KEYS = ("SERVICE_PRODUCT", "BACKUP", "ASSET_CONDITION", "COST_CONTROL", "EVIDENCE")
OBJECTIVE_LABEL = {"FULL": "Full", "LIMITED": "Limited", "NONE": "None", "REVIEW": "Review",
                   "UNASSESSED": "Unassessed", "UNKNOWN": "Unknown", "NOT_APPLICABLE": "N/A"}
#: Closure 2 N5: the only emitted (key, state) reason strings.
OBJECTIVE_REASON = {
    **{(key, "UNKNOWN"): "No reviewed objective assessment" for key in OBJECTIVE_KEYS[:3]},
    **{(key, "NOT_APPLICABLE"): "Site configuration proves this objective is not applicable"
       for key in OBJECTIVE_KEYS[:3]},
    ("COST_CONTROL", "REVIEW"): "Eligible selected operating-cost consequence",
    ("COST_CONTROL", "UNASSESSED"): "No selected operating-cost consequence",
    ("COST_CONTROL", "UNKNOWN"): "Operating-cost basis or coverage is incomplete",
    ("COST_CONTROL", "NOT_APPLICABLE"): "Site configuration proves cost control is not applicable",
    ("EVIDENCE", "FULL"): "All applicable selected capabilities are full",
    ("EVIDENCE", "LIMITED"): "At least one selected capability is limited",
    ("EVIDENCE", "NONE"): "At least one selected capability has no support",
    ("EVIDENCE", "UNKNOWN"): "Evidence selection is missing, historical or unsettled",
    ("EVIDENCE", "NOT_APPLICABLE"): "Site configuration proves evidence is not applicable"}
PROMPT_TEXT = "{next_step} at {site_name} to address the selected evidence gap."
NO_GAP_TEXT, INCOMPLETE_TEXT = "No selected decision-changing evidence step", "Evidence coverage incomplete"
#: Closure 1 card table: (card, state) -> (detail, or None when the page formats it from money; basis_text; tone).
CARD_SLOTS = {
    ("OPERATING_COST", "COMPARABLE_GROUP"): (None, "Comparable selected basis", "amber"),
    ("OPERATING_COST", "SITE_OWNED"): (None, "Site-owned selected consequence", "amber"),
    ("OPERATING_COST", "UNPRICED"): (None, "Price not established", "neutral"),
    ("OPERATING_COST", "WITHHELD"): ("Inspect Site records and exclusions", "No combined operating-cost amount",
                                     "neutral"),
    ("OPERATING_COST", "NO_LINE"): ("No selected operating-cost consequence", "No value line", "neutral"),
    ("SERVICE_PRODUCT_RISK", "UNKNOWN"): ("No reviewed estate risk classification", "Risk count unavailable",
                                          "neutral"),
    ("PRODUCTIVE_USE", "UNSUPPORTED"): ("No reviewed opportunity Finding or headroom basis",
                                        "Demand and scenario basis unavailable", "neutral"),
    ("ASSET_LIFE", "UNSUPPORTED"): ("Capacity and life exposure are not assessed", "No reviewed life assessment",
                                    "neutral"),
    ("VERIFIED_RECOVERY", "NOT_ESTABLISHED"): ("Verification outcome is separate from recovered value",
                                               "Completed work does not establish savings", "neutral")}
CARD_DESTINATION = {"OPERATING_COST": "/financials", "SERVICE_PRODUCT_RISK": "/findings/risks",
                    "PRODUCTIVE_USE": None, "ASSET_LIFE": None, "VERIFIED_RECOVERY": "/financials"}
#: Literal value slots; the bounded amounts of COMPARABLE_GROUP/SITE_OWNED are formatted by the page (S10).
DISPLAYED_VALUE = {"WITHHELD": "Not comparable for this selection", "NO_LINE": "No supported value",
                   "UNPRICED": "Unpriced", "UNKNOWN": "Not assessed", "UNSUPPORTED": "Not established",
                   "NOT_ESTABLISHED": "Not established"}


def public(item: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in item.items() if not k.startswith("_")}


def _card(key: str, state: str, *, line_keys: Iterable[str] = (), group_key: str | None = None,
          currency: str | None = None, detail: str | None = None) -> dict[str, Any]:
    slot_detail, basis_text, tone = CARD_SLOTS[(key, state)]
    return {"key": key, "state": state, "display_value": DISPLAYED_VALUE.get(state), "currency": currency,
            "line_keys": sorted(line_keys), "group_key": group_key, "basis": None,
            "destination": CARD_DESTINATION[key], "detail": detail if slot_detail is None else slot_detail,
            "basis_text": basis_text, "tone": tone}


def operating_cost_card(lines: list[dict[str, Any]], applicable: dict[str, bool],
                        groups: list[dict[str, Any]]) -> dict[str, Any]:
    """Closure 2 N2 first match over every selected operating-cost head before paging; rule (1) tests **line**
    eligibility, so a lone UNPRICED line reaches rule (4) whatever its one-line group says (S11)."""
    heads = [x for x in lines if x["category"] == OPERATING_COST]
    parts = [g for g in groups if g["category"] == OPERATING_COST and g["line_keys"]]
    keys = [x["line_key"] for x in heads]
    if (applicable.get(OPERATING_COST) is False or len(parts) > 1
            or any(x["eligibility"] not in (ELIGIBLE, UNPRICED) for x in heads)):
        return _card("OPERATING_COST", "WITHHELD", line_keys=keys)
    if parts and parts[0]["state"] == COMPARABLE and len(heads) == len(parts[0]["line_keys"]):
        return _card("OPERATING_COST", "COMPARABLE_GROUP", line_keys=keys, group_key=parts[0]["group_key"],
                     currency=parts[0]["currency"])
    if len(heads) == 1 and heads[0]["eligibility"] == ELIGIBLE and parts and parts[0]["state"] == SINGLE_LINE:
        return _card("OPERATING_COST", "SITE_OWNED", line_keys=keys, group_key=parts[0]["group_key"],
                     currency=(heads[0]["amount"] or {}).get("currency"))
    if len(heads) == 1 and heads[0]["eligibility"] == UNPRICED:
        return _card("OPERATING_COST", "UNPRICED", line_keys=keys,
                     detail=f"{heads[0]['site_name']} · consequence recorded without a price")
    if not heads:
        return _card("OPERATING_COST", "NO_LINE")
    return _card("OPERATING_COST", "WITHHELD", line_keys=keys)


def value_cards(lines: list[dict[str, Any]], applicable: dict[str, bool],
                groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The five cards in mock order. No reviewed RISK producer exists, so risk is UNKNOWN (closure 4 N4); the other
    three are fixed unsupported/not-established slots that never inherit mock values."""
    return [operating_cost_card(lines, applicable, groups), _card("SERVICE_PRODUCT_RISK", "UNKNOWN"),
            _card("PRODUCTIVE_USE", "UNSUPPORTED"), _card("ASSET_LIFE", "UNSUPPORTED"),
            _card("VERIFIED_RECOVERY", "NOT_ESTABLISHED")]


def _cell(key: str, state: str, destination: str | None = None) -> dict[str, Any]:
    return {"key": key, "state": state, "label": OBJECTIVE_LABEL[state], "reason": OBJECTIVE_REASON[(key, state)],
            "destination": destination}


#: Post-W6 W3-estate Q10: the mounted Site route under `/sites/{code}` of each objective with a fixed target per
#: domain. EV has no configured Backup objective (None: "No configured objective"); Cost control and Evidence
#: come from the Site's selected window (`objective_destinations`).
OBJECTIVE_ROUTE = {
    MINI_GRID: {"SERVICE_PRODUCT": "/performance/service", "BACKUP": "/performance/backup",
                "ASSET_CONDITION": "/health"},
    COLD: {"SERVICE_PRODUCT": "/performance/temperature", "BACKUP": "/performance/backup",
           "ASSET_CONDITION": "/health"},
    EV: {"SERVICE_PRODUCT": "/performance/sessions", "BACKUP": None, "ASSET_CONDITION": "/health"}}


def objective_destinations(code: str, domain: str, rows: list[dict[str, Any]]) -> dict[str, str | None]:
    """Post-W6 W3-estate Q10: each matrix cell's mounted Site route. Mini-grid Cost control and Evidence open
    `/financials` and `/evidence`; cold/EV reuse the selected-window helpers: the latest evidence row whose
    `window_links` proved its window (closure 5 B5) gives `site_readiness` and the same `_money_links` bridge
    query, else the Site home (EV `/sites/{code}/ev`). An unknown Site configuration has no destination."""
    if domain not in OBJECTIVE_ROUTE:
        return dict.fromkeys(OBJECTIVE_KEYS)
    base = f"/sites/{quote(code, safe='')}"
    out = {key: None if route is None else base + route for key, route in OBJECTIVE_ROUTE[domain].items()}
    if domain == MINI_GRID:
        return {**out, "COST_CONTROL": f"{base}/financials", "EVIDENCE": f"{base}/evidence"}
    home = site_home_href(code, domain)
    proven = [r for r in rows if r["links"]["site_readiness_label"] is None and "?" in r["links"]["site_readiness"]]
    if not proven:
        return {**out, "COST_CONTROL": home, "EVIDENCE": home}
    latest = max(proven, key=lambda r: (r["window_end"] or "", r["window_start"] or ""))
    readiness = latest["links"]["site_readiness"]
    bridge = f"{base}/financials" if domain == COLD else f"{base}/ev/financials"
    return {**out, "COST_CONTROL": f"{bridge}?{readiness.split('?', 1)[1]}", "EVIDENCE": readiness}


def evidence_cell_state(domain: str, cov: dict[str, Any], rows: list[dict[str, Any]], historical: bool) -> str:
    """The per-Site W3-02 readiness reduction; a historical display, an unsettled selection or CONTRADICTORY
    readiness is UNKNOWN (closure 4 N6)."""
    if historical or evidence_unit(domain, cov, rows) == U:
        return "UNKNOWN"
    states = [r["readiness"] for r in rows]
    if all(s == FULL for s in states):
        return "FULL"
    return "NONE" if NONE in states else "LIMITED"


def cost_cell_state(domain: str, cov: dict[str, Any], lines: list[dict[str, Any]]) -> str:
    """S19: a configured domain without the operating-cost category under `APPLICABLE` is NOT_APPLICABLE; mini-grid
    is REVIEW for an eligible operating-cost line, UNASSESSED on complete money coverage with no line, else UNKNOWN.
    An unknown configuration is UNKNOWN, never N/A."""
    if domain == NOT_APPLICABLE:
        return "UNKNOWN"
    if OPERATING_COST not in APPLICABLE[domain]:
        return "NOT_APPLICABLE"
    mine = [x for x in lines if x["category"] == OPERATING_COST]
    if any(x["eligibility"] == ELIGIBLE for x in mine):
        return "REVIEW"
    if not mine and all(c == G for c in money_units(domain, cov, lines).values()):
        return "UNASSESSED"
    return "UNKNOWN"


def objective(site: dict[str, Any], e: tuple, m: tuple, historical: bool) -> dict[str, Any]:
    """One matrix item per authorized Site; the first three cells have no reviewed objective producer."""
    _, e_domain, e_cov, e_rows = e
    _, m_domain, m_cov, m_lines = m
    to = objective_destinations(site["site_code"], DOMAIN_OF_SITE_TYPE.get(site["site_type"], NOT_APPLICABLE),
                                e_rows)
    cells = [_cell(key, "UNKNOWN", to[key]) for key in OBJECTIVE_KEYS[:3]]
    cells.append(_cell("COST_CONTROL", cost_cell_state(m_domain, m_cov, m_lines), to["COST_CONTROL"]))
    cells.append(_cell("EVIDENCE", evidence_cell_state(e_domain, e_cov, e_rows, historical), to["EVIDENCE"]))
    return {"site_id": str(site["site_id"]), "site_code": site["site_code"], "site_name": site["site_name"],
            "domain": site["site_type"], "cells": cells}


def evidence_prompt(evidence_state: str, gaps: list[dict[str, Any]]) -> dict[str, Any]:
    """Closure 2 N5 / closure 4 N5: incomplete coverage wins; else the first canonical gap with a nonnull step and
    its first Site with a code in the group's `(site_code_key, site_id)` order; null-step gaps are skipped."""
    out = {"state": "COVERAGE_INCOMPLETE", "text": INCOMPLETE_TEXT, "site_id": None, "site_code": None,
           "gap_code": None, "destination": "/evidence"}
    if evidence_state not in (COMPLETE, EMPTY):
        return out
    for gap in gaps:
        if gap["next_step"] is None:
            continue
        for sid, code, name in zip(gap["site_ids"], gap["site_codes"], gap["site_names"]):
            if code is not None:
                return {**out, "state": "AVAILABLE", "site_id": sid, "site_code": code, "gap_code": gap["gap_code"],
                        "text": PROMPT_TEXT.format(next_step=gap["next_step"], site_name=name)}
    return {**out, "state": "NO_GAP", "text": NO_GAP_TEXT}


def _plan_id(plans: list[dict[str, Any]], k: datetime) -> str | None:
    """The selected plan active at the cutoff, else the latest recorded selected plan; null when none."""
    active = [p for p in plans if p["later_start"] <= k < p["later_end"]]
    pick = max(active or plans, key=lambda p: (p["recorded_at"], str(p["id"])), default=None)
    return None if pick is None else str(pick["id"])


def progress(a_sites: list[tuple], a_rows: list[dict[str, Any]], k: datetime,
             selected_pairs: set[tuple[str, str]]) -> tuple[dict[str, Any], bool]:
    """Closure 1 Q21 / r1b: every full-scope selected Action (several per origin pair, and one whose origin revision
    is no longer selected), `(recorded_at desc nulls last, action_id)`. r1b2 R10 adds the tenth field
    `origin_revision_selected`: the exact origin `(finding_id, finding_revision_id)` is in `selected_pairs`, the full
    selected Finding revision set before lifecycle/lens/page filtering (a disclosure fact only). Counts only on
    complete applicable Action coverage (cold/EV NOT_APPLICABLE does not force null)."""
    complete = _coverage_state([cov["state"] for _, cov in a_sites]) == "COMPLETE"
    rows = []
    for a in a_rows:
        raw = a["_raw"]
        at = raw.get("_selected_recorded_at")
        rows.append({"action_id": a["action_id"], "action_code": a["action_code"],
                     "selected_action_event_id": a["selected_event_id"],
                     "verification_plan_id": _plan_id(raw.get("_plans") or [], k),
                     "verification_outcome_id": None if raw.get("_outcome_id") is None else str(raw["_outcome_id"]),
                     "application_state": a["application_state"], "resolution_state": a["resolution_state"],
                     "verification_outcome": a["verification_outcome"], "recorded_at": wire_time(at),
                     "origin_revision_selected": (a["source_finding_id"], a["source_finding_revision_id"])
                     in selected_pairs, "_at": at})
    rows.sort(key=lambda r: (r["_at"] is None, 0.0 if r["_at"] is None else -r["_at"].timestamp(), r["action_id"]))

    def count(flag: str) -> int | None:
        return sum(1 for a in a_rows if a["_raw"].get(flag)) if complete else None

    return {"state": "NO_COMPARABLE_BASELINE", "completed_activity_count": None,
            "pending_trial_count": count("_verification_window"),
            "verified_resolution_count": count("_verified_recent"), "recovered_value": None,
            "rows": [public(r) for r in rows]}, complete


def _exact(bounds: dict[str, Any] | None) -> bool:
    return bool(bounds) and bounds.get("low") is not None and bounds.get("low") == bounds.get("high")


def footer(m_sites: list[tuple], lines: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Closure 1: the first eligible EV gross-tariff line with exact quantity and amount and a reviewed EV route
    (not the current-view fallback), ordered `(site_code_key, site_id, line_key)`; never a group or a Finding."""
    keys = {str(site["site_id"]).lower(): str(site["site_code_key"]) for site, _, _, _ in m_sites}
    eligible = [x for x in lines if x["domain"] == EV and x["category"] == GROSS_TARIFF
                and x["eligibility"] == ELIGIBLE and _exact(x["quantity"]) and _exact(x["amount"])
                and x["links"].get("current_view_label") is None and x["links"].get("evidence")]  # r1b2 R12
    if not eligible:
        return None
    x = min(eligible, key=lambda x: (keys.get(x["site_id"].lower(), ""), x["site_id"].lower(), x["line_key"]))
    return {"line_key": x["line_key"], "site_name": x["site_name"], "quantity_display": None,
            "amount_display": None, "source_provenance": x["source_provenance"], "window_start": x["window_start"],
            "window_end": x["window_end"], "destination": x["links"]["evidence"]}


# --- the service -------------------------------------------------------------------------------------------------

class EstatePortfolioService(EstateEvidenceService):
    """`GET /api/estate/portfolio` over the shared W3-01 authorization, cutoff, fence, cursor and envelope."""

    def portfolio(self, tenant_id: Any, req: EstateRequest, admit: Admit) -> dict[str, Any]:
        return self._read(lambda snap: self._portfolio(snap, tenant_id, req, admit))

    def site_work_rows(self, tenant_id: Any, site_code: str, day_from: datetime, day_to: datetime,
                       work_from: datetime, work_to: datetime, known_at: datetime | None = None
                       ) -> dict[str, Any] | None:
        """OUT-B4 (addendum 3 item 16, signature per addendum 5 point 2): one Site's Finding and Action rows exactly
        as `select_finding_scope` and `select_action_scope` emit them for `_portfolio` (private keys and `_raw`
        included; condition 1: no shaping or reduction), plus that Site's Finding coverage (`site_cov`, the value
        `_portfolio` hands `place`). The Finding rows and `site_cov` cover the board day (estate coverage yields
        rows only when every requested day is selected, `estate/coverage.py:91-133`); the Action rows cover the
        31-day work window. One `self._read` snapshot and cutoff for both. None when the Site is not in the
        authorized imported set for the board day. The request kind is "findings" (no cursor is ever passed)."""
        day = estate_request("findings", day_from, day_to, known_at)  # addendum 7: the estate window rule
        work_req = estate_request("findings", work_from, work_to, known_at)
        admit = lambda code: code == site_code  # noqa: E731 - one-Site admit

        def work(snap: Any) -> Any:
            f_sites, f_rows = select_finding_scope(snap, tenant_id, day, self._scope(snap, tenant_id, day, admit))
            if not f_sites:
                return None
            _, a_rows = select_action_scope(snap, tenant_id, work_req, self._scope(snap, tenant_id, work_req, admit))
            return {"site_cov": f_sites[0][2], "findings": f_rows, "actions": a_rows}

        return self._read(work)

    def _portfolio(self, snap: Any, tenant_id: Any, req: EstateRequest, admit: Admit) -> dict[str, Any]:
        scope = self._scope(snap, tenant_id, req, admit)
        f_sites, f_rows = select_finding_scope(snap, tenant_id, req, scope)
        a_sites, a_rows = select_action_scope(snap, tenant_id, req, scope)
        e_sites, e_rows_all = select_evidence_scope(snap, tenant_id, req, scope)
        m_sites, m_lines_all, applicable, groups, exclusions, diagnostics = select_financial_scope(
            snap, tenant_id, req, scope)
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
        cov_of = {str(site["site_id"]): cov for site, _, cov in f_sites}
        group_of = line_groups(m_lines_all, groups)
        members = [portfolio_row(r, a_rows, cov_of.get(r["site_id"]), group_of.get(str(r["finding_revision_id"])))
                   for r in f_rows if r["lifecycle"] in MEMBERS]
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
        empty = count == 0
        gaps = evidence_gap_groups(e_rows_all)
        prog, actions_complete = progress(a_sites, a_rows, scope["k"],
                                          {(r["finding_id"], r["finding_revision_id"]) for r in f_rows})
        finding_known, evidence_known = states["F"] in (COMPLETE, EMPTY), states["E"] in (COMPLETE, EMPTY)
        # r1a M1 / wire: estate counts are claims only on complete (or complete-empty) coverage of their root.
        summary: dict[str, Any] = {
            "finding_count": len(members) if finding_known else None, "priority_site_count": None,
            "opportunity_count": (sum(1 for r in members if LENS_FLAG["opportunities"] in r["lens_flags"])
                                  if finding_known else None),
            "evidence_gap_site_count": len({sid for g in gaps for sid in g["site_ids"]}) if evidence_known else None,
            "accepted_action_count": len(a_rows) if actions_complete else None,
            "verified_resolution_count": prog["verified_resolution_count"],
            "combined_value": None, "combined_value_state": "NOT_COMPARABLE",
            # CC-R2: over `members` (all lenses, like `finding_count`); all five keys; null unless F is known.
            "placement_counts": {g: (sum(1 for r in members if r["placement"]["group"] == g) if finding_known else None)
                                 for g in GROUPS},
            # OUT-A2 (ruling A-Q11): over `members`; all four keys; both counts null unless F is known.
            "category_counts": category_counts(members, finding_known)}
        # r1b2 R11: one batched provenance read for every represented Site with a selected ID (no per-Site query
        # loop); a Site without a selected ID has null provenance ("No selected source basis").
        site_ids = [_ids([*(x for key in SITE_TOKEN_ARRAYS for x in item[key]), cov["selection_id"]])
                    for (_, _, cov), item in zip(f_sites, token_sites)]
        wanted = [(site["site_id"], item["cited_accepted_evidence_ids"], ids)
                  for (site, _, _), item, ids in zip(f_sites, token_sites, site_ids) if ids]
        resolved = iter(snap.cited_provenance_many(tenant_id, wanted) if wanted else [])
        disclosure_sites = []
        for (site, domain, cov), ids in zip(f_sites, site_ids):
            disclosure_sites.append({"site_id": str(site["site_id"]), "site_code": site["site_code"],
                                     "site_name": site["site_name"], "domain": site["site_type"],
                                     "window": {"from": wire_time(req.from_), "to": wire_time(req.to)},
                                     "coverage": _coverage_site(site, cov), "selected_revision_ids": ids,
                                     "source_provenance": next(resolved) if ids else None})
        body.update({"lens": req.lens, "summary": summary,
                     "value_cards": value_cards(m_lines_all, applicable, groups),
                     "objectives": [objective(site, evidence_by[str(site["site_id"])], money_by[str(site["site_id"])],
                                              bool(snap.basis_historical)) for site, _, _ in f_sites],
                     "evidence_prompt": evidence_prompt(states["E"], gaps),
                     "opportunity": {"state": "UNSUPPORTED", "finding_id": None, "scenario_amount": None,
                                     "headroom": None, "destination": None},
                     "progress": prog, "footer": footer(m_sites, m_lines_all),
                     "selected_lines": [public(x) for x in m_lines_all],
                     "money": {"groups": [] if empty else groups, "exclusions": [] if empty else exclusions,
                               "diagnostics": [] if empty else diagnostics, "estate_total": None},
                     "scope_disclosure": {"sites": disclosure_sites, "exclusions": [] if empty else exclusions},
                     "order": PORTFOLIO_ORDER, "total_count": len(shown),
                     "rows": [{k: v for k, v in r.items() if not k.startswith("_")} for r in page],
                     "next_cursor": None if last is None else self._cursor(tenant_id, req, scope, token,
                                                                          *last["_marker"]),
                     "selection_token": token})
        return body
