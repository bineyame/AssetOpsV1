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

from datetime import datetime, timedelta
from typing import Any, Callable, Iterable, Mapping

from assetops_backend import perf, read_scope
from assetops_backend.chain import refs
from assetops_backend.chain.lookup import public_thread
from assetops_backend.chain.read import lifecycle_cutoff
from assetops_backend.chain.claims import CLAIM_KEYS
from assetops_backend.chain.threads import OPEN_CLASS, VERIFIED_CLASS, classify
from assetops_backend.chain.vocabulary import (CHECKED_DAYS_BASIS, count_basis, evidence_gap_text)
from assetops_backend.outcomes.credit import recovered_value
from assetops_backend.estate.coverage import (
    COLD, COVERED, DOMAIN_OF_SITE_TYPE, EV, MINI_GRID, NOT_APPLICABLE, PARTIAL, PENDING)
from assetops_backend.estate.evidence_money import (
    CONTRADICTORY, EMPTY, EMPTY_SCOPE, FULL, LIMITED, NONE, EstateEvidenceService, _admit_any, _by_window,
    select_evidence_scope, site_home_ref)
from assetops_backend.estate.evidence_money import _groups as evidence_gap_groups
from assetops_backend.estate.financials import (
    APPLICABLE, COMPARABLE, ELIGIBLE, SINGLE_LINE, UNPRICED, partial_money, select_financial_scope)
from assetops_backend.estate.index import (
    LENS_FLAG, Admit, _coverage_site, _coverage_state, _token_site, opportunity_read, select_action_scope,
    select_finding_scope)
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
#: COV-PARTIAL §3: some Site is partly checked and every other Site is settled; never Current.
PARTIAL_STATUS = "PARTIAL"
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


def attach_threads(snap: Any, tenant_id: Any, f_rows: list[dict[str, Any]], a_rows: list[dict[str, Any]],
                   req: Any = None, known_at: Any = None, cutoffs: Mapping[str, Any] | None = None) -> None:
    """CH-2 (build sheet §5.1): each Finding row's thread (`_thread`: id, occurrence number, occurrence count) and
    each Action row's thread (`_thread_id`), from one snapshot query. A snapshot without the thread port, or a row
    with no thread, carries None, and `_action_for` then matches no Action (CH-5a2 B3: no exact-revision join).
    `cutoffs` is the Site code -> evidence cutoff map (`select_finding_scope(cutoffs=)`, CH-5a2 B3/R7); it is kept
    for its callers but no longer bounds the lifecycle (D-E4.2)."""
    port = getattr(snap, "threads", None)
    found: dict[str, Any] = {"findings": {}, "actions": {}}
    segments_at: dict[Any, dict[str, int]] = {}  # cutoff -> {action_id: segment at that cutoff}
    default = known_at if known_at is not None else (None if req is None else req.known_at)
    if port is not None and (f_rows or a_rows):
        # CH-3 §5, CH3-R (AG-27, COH-13): the thread state on each Site's local day holding the window's last
        # instant (as the board reads it). CH6b2-R2 (`chain.read.lifecycle_cutoff`), D-E4.2: every row's lifecycle
        # (thread state and Action segments) is read at the request cutoff `k`, the envelope's resolved
        # `window.known_at` (`known_at`, D-b rule coalesce(cause_known_at, recorded_at) <= k), as one group. A
        # cold/EV Site's evidence cutoff (`cutoffs[site_code]`) bounds evidence only, never the lifecycle: an action
        # agreed after the Site's last reading is still agreed. Review side-question 1: `_thread_cutoff` is that same
        # value, so a row's Finding segment and the Action segment it is compared with come from one cutoff.
        cutoff = lifecycle_cutoff(default)
        for r in f_rows:
            r["_thread_cutoff"] = cutoff
        fids = [r["finding_id"] for r in f_rows]
        # CH5a1-R2 R-1: occurrence visibility is bounded by the envelope's transaction-time `default` alone.
        kw = {} if req is None else {"day_at": req.to - timedelta(microseconds=1), "known_at": cutoff,
                                     "visible_at": default}
        part = port(tenant_id, fids, [a["action_id"] for a in a_rows], **kw)
        for key in ("findings", "actions"):
            found.setdefault(key, {}).update(part.get(key) or {})
        segments_at[cutoff] = part.get("action_segments") or {}
    for r in f_rows:
        r["_thread"] = found["findings"].get(str(r["finding_id"]).lower())
    for a in a_rows:
        aid = str(a["action_id"]).lower()
        a["_thread_id"] = found["actions"].get(aid)
        a["_segment_no"] = (segments_at.get(lifecycle_cutoff(default)) or {}).get(aid)
        a["_segment_at"] = {c: seg[aid] for c, seg in segments_at.items() if aid in seg}


def action_segment_for(a: dict[str, Any], row: dict[str, Any]) -> int | None:
    """The Action's thread segment read at the Finding row's cutoff (else at the default cutoff)."""
    at = a.get("_segment_at") or {}
    cutoff = row.get("_thread_cutoff")
    return at[cutoff] if cutoff in at else a.get("_segment_no")


VERIFIED_CLAIM = "count.verified_results"


def priority_site_count(counted: Any) -> int | None:
    """CH6b3-R Q4b: Sites with an open or in-hand thread in the one count computation (a Site with a fix in hand still
    needs attention until verified); None when the computation or any Site's thread read failed, never 0."""
    per_site = None if counted is None else list(counted.threads.values())
    if per_site is None or any(t is None for t in per_site):
        return None
    return sum(1 for t in per_site if t["open"] + t["in_hand"] > 0)


def _same_segment(action_seg: int | None, finding_seg: int | None) -> bool:
    """CH-3 §3 (CH-2 L1): an Action is current for a Finding only in the Finding's segment; unknown on either side
    matches (the join's rule)."""
    return finding_seg is None or action_seg is None or action_seg == finding_seg


def _action_for(row: dict[str, Any], actions: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Closure 4 S9 / r1a Q-1a-1, CH-2 §5.1 (I-03): an Action matches a Finding row when the row's Finding
    occurrence is on the Action's thread, in the same segment. CH-5a2 B3: the exact
    `(origin_finding_id, origin_finding_revision_id)` fallback is deleted; an Action without a thread link matches
    no row (an honest "No action agreed yet"; COH-11 flags it). Several matches choose the latest selected Action event
    `recorded_at`, then `action_id` ascending."""
    thread = (row.get("_thread") or {}).get("id")
    segment = (row.get("_thread") or {}).get("segment_no")

    def same_segment(a: dict[str, Any]) -> bool:
        """CH-3 §3 (CH-2 L1): on a thread, an Action is current for a Finding only in the Finding's segment, both
        read at the row's cutoff."""
        return _same_segment(action_segment_for(a, row), segment)

    matches = [a for a in actions if thread is not None and a.get("_thread_id") == thread and same_segment(a)]
    if not matches:
        return None
    if any(a["_raw"].get("_selected_recorded_at") is None for a in matches):
        raise ActionSelectionError("A matching Action has no selected event time.")
    return min(matches, key=lambda a: (-a["_raw"]["_selected_recorded_at"].timestamp(), a["action_id"]))


#: The public name of the Finding-to-Action join, for the Site outcome board (OUT-B2 review L1).
action_for = _action_for


def workflow_label(action: dict[str, Any] | None) -> str:
    """Closure 5 S7: the first matching selected fact; table order is precedence."""
    if action is None:
        return "No action agreed yet"
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


#: DIESEL-1-R3p, generalised by R4.1: a row whose Action the Portfolio does not join (the fuel row, FUEL_BALANCE
#: domain, and every Cold/EV row, since `select_action_scope` reads mini-grid Actions only) reads its thread state
#: with the existing workflow words.
THREAD_LABEL = {"RESOLVED_MONITORING": "Verified", "CLOSED": "Verified", "CHANGE_APPLIED": "Applied",
                "ACTION_IN_HAND": "Pending"}


def portfolio_row(r: dict[str, Any], actions: list[dict[str, Any]], site_cov: dict[str, Any] | None = None,
                  line_group: str | None = None) -> dict[str, Any]:
    site = r["_site"]
    fid, frid = r["finding_id"], r["finding_revision_id"]
    action = _action_for(r, actions)
    unjoined = r.get("_mechanism") == "UNEXPLAINED_FUEL" or (
        action is None and DOMAIN_OF_SITE_TYPE.get(r["_domain"], NOT_APPLICABLE) in (COLD, EV))
    label = (THREAD_LABEL.get((r.get("_thread") or {}).get("state"), "No action agreed yet") if unjoined else None)
    placed = place(r, action, site_cov or {}, line_group, label=label)  # CC-R2: row facts only; `priority` null
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
        # CH-2 §5.3: additive; null when the Finding has no thread (CH-5a renders recurrence).
        "thread": public_thread(r.get("_thread")),  # CH-5a1 L3: the wire keys only, never the state classes
        # CH-2 L2: the matched Action's own thread (its chain_action_thread link), so COH-11 observes the link.
        "action_thread_id": None if action is None else action.get("_thread_id"),
        # CH-3 (packet deviation, additive): the matched Action's thread segment, so COH-15 observes the rule.
        "action_segment_no": None if action is None else action_segment_for(action, r),
        "action_id": None if action is None else action["action_id"],
        "action_title": None if action is None else action["action_title"],
        "action_state": None if action is None else action["application_state"],
        "application_state": None if action is None else action["application_state"],
        "resolution_state": None if action is None else action["resolution_state"],
        "verification_outcome": None if action is None else action["verification_outcome"],
        "workflow_label": workflow_label(action) if label is None else label,
        "next_move": None, "source_provenance": r["source_provenance"],
        # Post-W6 W3-estate Q2/Q10 (S12 inert restriction removed): the Site home (EV `/sites/{code}/ev`) and the
        # Finding route `select_finding_scope` proved: mini-grid `revision_id`; cold/EV the selected Site window
        # holding the Finding with its proven row-local cutoff, else null.
        **refs.split_links({"site": r["link_refs"]["site"], "finding": r["link_refs"]["finding"],
                            "action": None if action is None else refs.action_ref(
                                site["site_code"], action["action_id"], event_id=action["selected_event_id"])}),
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


def disclosure_provenance(block: dict[str, Any] | None) -> dict[str, Any] | None:
    """CH-5c R8: the disclosure's per-Site provenance keeps its scalar fields only. The frontend reads it only as
    `=== null` ("No selected source basis"); the id arrays (`evidence_ids`, `reasons[]`) were never rendered."""
    return None if block is None else {k: v for k, v in block.items() if not isinstance(v, (list, tuple))}


#: CH-5c Q9: the private body key that carries the per-Site selected ids for `GET /api/estate/portfolio/scope-ids`.
SCOPE_IDS_KEY = "_scope_ids"


def split_scope_ids(body: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """CH-5c Q9: the Portfolio body without its private scope ids, and the ids (one item per disclosed Site)."""
    ids = body.pop(SCOPE_IDS_KEY, [])
    return body, ids


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
    # CH-4 §2.3: from the opportunity items (FOUND/NONE); UNKNOWN only when the opportunity read raised.
    ("PRODUCTIVE_USE", "FOUND"): (None, "Listed under Findings › Opportunities", "green"),
    ("PRODUCTIVE_USE", "NONE"): ("No opportunity found in this period", "Listed under Findings › Opportunities",
                                 "neutral"),
    ("PRODUCTIVE_USE", "UNKNOWN"): ("Opportunities could not be read", "Listed under Findings › Opportunities",
                                    "neutral"),
    ("ASSET_LIFE", "UNSUPPORTED"): ("Capacity and life exposure are not assessed", "No reviewed life assessment",
                                    "neutral"),
    ("VERIFIED_RECOVERY", "NOT_ESTABLISHED"): ("Verification outcome is separate from recovered value",
                                               "Completed work does not establish savings", "neutral")}
CARD_DESTINATION = {"OPERATING_COST": refs.estate_ref("financials"),
                    "SERVICE_PRODUCT_RISK": refs.estate_ref("findings_risks"),
                    "PRODUCTIVE_USE": refs.estate_ref("findings_opportunities"), "ASSET_LIFE": None,
                    "VERIFIED_RECOVERY": refs.estate_ref("financials")}
#: Literal value slots; the bounded amounts of COMPARABLE_GROUP/SITE_OWNED are formatted by the page (S10).
DISPLAYED_VALUE = {"WITHHELD": "Can't be compared across these sites yet", "NO_LINE": "No supported value",
                   "UNPRICED": "Unpriced", "UNKNOWN": "Not assessed", "UNSUPPORTED": "Not established",
                   "NOT_ESTABLISHED": "Not established"}


def public(item: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in item.items() if not k.startswith("_")}


def _card(key: str, state: str, *, line_keys: Iterable[str] = (), group_key: str | None = None,
          currency: str | None = None, detail: str | None = None,
          price_action: dict[str, Any] | None = None) -> dict[str, Any]:
    slot_detail, basis_text, tone = CARD_SLOTS[(key, state)]
    return {"key": key, "state": state, "display_value": DISPLAYED_VALUE.get(state), "currency": currency,
            "line_keys": sorted(line_keys), "group_key": group_key, "basis": None,
            **_destination(CARD_DESTINATION[key]), "detail": detail if slot_detail is None else slot_detail,
            "basis_text": basis_text, "tone": tone, "price_action": price_action}


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
                     detail=f"{heads[0]['site_name']} · consequence recorded without a price",
                     price_action=heads[0].get("price_action"))  # PR-1: the one unpriced line's link
    if not heads:
        return _card("OPERATING_COST", "NO_LINE")
    return _card("OPERATING_COST", "WITHHELD", line_keys=keys)


def productive_use_card(items: list[dict[str, Any]] | None) -> dict[str, Any]:
    """CH-4 §2.3: FOUND (detail = the items' short labels) or NONE from the opportunity items."""
    if items is None:
        return _card("PRODUCTIVE_USE", "UNKNOWN")
    if not items:
        return _card("PRODUCTIVE_USE", "NONE")
    return _card("PRODUCTIVE_USE", "FOUND", detail=" · ".join(i["short_label"] for i in items))


def opportunity_block(items: list[dict[str, Any]] | None) -> dict[str, Any]:
    """CH-4 §2.3: the Portfolio `opportunity` block from the same items as Findings › Opportunities."""
    found = bool(items)
    return {"state": "UNKNOWN" if items is None else "FOUND" if found else "NONE", "items": list(items or []),
            "finding_id": None, "scenario_amount": None,
            "headroom": items[0]["study"]["headroom_kw"] if found else None,
            **_destination(refs.estate_ref("findings_opportunities"))}


def value_cards(lines: list[dict[str, Any]], applicable: dict[str, bool],
                groups: list[dict[str, Any]], opportunities: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """The five cards in mock order. No reviewed RISK producer exists, so risk is UNKNOWN (closure 4 N4); the other
    three are fixed unsupported/not-established slots that never inherit mock values."""
    return [operating_cost_card(lines, applicable, groups), _card("SERVICE_PRODUCT_RISK", "UNKNOWN"),
            productive_use_card(opportunities), _card("ASSET_LIFE", "UNSUPPORTED"),
            _card("VERIFIED_RECOVERY", "NOT_ESTABLISHED")]


def _destination(ref: dict[str, Any] | None) -> dict[str, Any]:
    """CH5a2-R4(a): a card or cell `destination` (kept until CH-7) and its sibling `link_ref`, one from the other."""
    return {"destination": refs.href_for(ref), "link_ref": None if ref is None else dict(ref)}


def _cell(key: str, state: str, destination: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"key": key, "state": state, "label": OBJECTIVE_LABEL[state], "reason": OBJECTIVE_REASON[(key, state)],
            **_destination(destination)}


#: Post-W6 W3-estate Q10: the mounted Site route under `/sites/{code}` of each objective with a fixed target per
#: domain. EV has no configured Backup objective (None: "No configured objective"); Cost control and Evidence
#: come from the Site's selected window (`objective_destinations`).
OBJECTIVE_ROUTE: dict[str, dict[str, Callable[[str], dict[str, Any]] | None]] = {
    MINI_GRID: {"SERVICE_PRODUCT": lambda c: refs.evidence_ref(c, "service"),
                "BACKUP": lambda c: refs.evidence_ref(c, "backup"),
                "ASSET_CONDITION": lambda c: refs.site_ref(c, "health")},
    COLD: {"SERVICE_PRODUCT": lambda c: refs.evidence_ref(c, "temperature"),
           "BACKUP": lambda c: refs.evidence_ref(c, "backup"),
           "ASSET_CONDITION": lambda c: refs.site_ref(c, "health")},
    EV: {"SERVICE_PRODUCT": lambda c: refs.evidence_ref(c, "sessions"), "BACKUP": None,
         "ASSET_CONDITION": lambda c: refs.site_ref(c, "health")}}


def objective_destinations(code: str, domain: str, rows: list[dict[str, Any]]) -> dict[str, str | None]:
    """`objective_destination_refs` as hrefs."""
    return refs.links_of(objective_destination_refs(code, domain, rows))


def objective_destination_refs(code: str, domain: str, rows: list[dict[str, Any]]) -> dict[str, dict[str, Any] | None]:
    """Post-W6 W3-estate Q10: each matrix cell's mounted Site route. Mini-grid Cost control and Evidence open
    `/financials` and `/evidence`; cold/EV reuse the selected-window helpers: the latest evidence row whose
    `window_links` proved its window (closure 5 B5) gives `site_readiness` and the same `_money_links` bridge
    query, else the Site home (EV `/sites/{code}/ev`). An unknown Site configuration has no destination."""
    if domain not in OBJECTIVE_ROUTE:
        return dict.fromkeys(OBJECTIVE_KEYS)
    out = {key: None if route is None else route(code) for key, route in OBJECTIVE_ROUTE[domain].items()}
    if domain == MINI_GRID:
        return {**out, "COST_CONTROL": refs.site_ref(code, "financials"), "EVIDENCE": refs.evidence_ref(code)}
    home = site_home_ref(code, domain)
    proven = [r for r in rows if r["links"]["site_readiness_label"] is None
              and (r["link_refs"]["site_readiness"] or {}).get("window")]
    if not proven:
        return {**out, "COST_CONTROL": home, "EVIDENCE": home}
    latest = max(proven, key=lambda r: (r["window_end"] or "", r["window_start"] or ""))
    readiness = latest["link_refs"]["site_readiness"]
    bridge = refs.site_ref(code, "financials" if domain == COLD else "ev_financials", readiness["window"])
    return {**out, "COST_CONTROL": bridge, "EVIDENCE": readiness}


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
    to = objective_destination_refs(site["site_code"], DOMAIN_OF_SITE_TYPE.get(site["site_type"], NOT_APPLICABLE),
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
           "gap_code": None, **_destination(refs.estate_ref("evidence"))}
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
    active = [p for p in plans if read_scope.within(p["later_start"], p["later_end"], k)]
    pick = max(active or plans, key=lambda p: (p["recorded_at"], str(p["id"])), default=None)
    return None if pick is None else str(pick["id"])


def progress(a_sites: list[tuple], a_rows: list[dict[str, Any]], k: datetime,
             selected_pairs: set[tuple[str, str]],
             f_rows: list[dict[str, Any]] | None = None) -> tuple[dict[str, Any], bool]:
    """Closure 1 Q21 / r1b: every full-scope selected Action (several per origin pair, and one whose origin revision
    is no longer selected), `(recorded_at desc nulls last, action_id)`. r1b2 R10 adds the tenth field
    `origin_revision_selected`: the exact origin `(finding_id, finding_revision_id)` is in `selected_pairs`, the full
    selected Finding revision set before lifecycle/lens/page filtering (a disclosure fact only). CH-5a2 B6 (I-01,
    COH-8) adds `origin_selected`: the Action's thread holds, in the Action's segment, a selected Finding (any
    revision; `f_rows` with their `_thread`); the exact revision stays as the audit fact. Counts only on
    complete applicable Action coverage (cold/EV NOT_APPLICABLE does not force null)."""
    complete = _coverage_state([cov["state"] for _, cov in a_sites]) == "COMPLETE"
    on_thread = [r for r in f_rows or () if (r.get("_thread") or {}).get("id") is not None]
    rows = []
    for a in a_rows:
        raw = a["_raw"]
        thread = a.get("_thread_id")
        # CH-5a2b (review L1): per Finding row, the Action's segment read at that row's own cutoff (`_action_for`).
        origin_selected = thread is not None and any(
            r["_thread"]["id"] == thread and _same_segment(action_segment_for(a, r), r["_thread"].get("segment_no"))
            for r in on_thread)
        at = raw.get("_selected_recorded_at")
        rows.append({"action_id": a["action_id"], "action_code": a["action_code"],
                     "selected_action_event_id": a["selected_event_id"],
                     "verification_plan_id": _plan_id(raw.get("_plans") or [], k),
                     "verification_outcome_id": None if raw.get("_outcome_id") is None else str(raw["_outcome_id"]),
                     "application_state": a["application_state"], "resolution_state": a["resolution_state"],
                     "verification_outcome": a["verification_outcome"], "recorded_at": wire_time(at),
                     "origin_revision_selected": (a["source_finding_id"], a["source_finding_revision_id"])
                     in selected_pairs, "origin_selected": origin_selected, "_at": at})
    rows.sort(key=lambda r: (r["_at"] is None, 0.0 if r["_at"] is None else -r["_at"].timestamp(), r["action_id"]))

    def count(flag: str) -> int | None:
        return sum(1 for a in a_rows if a["_raw"].get(flag)) if complete else None

    return {"state": "NO_COMPARABLE_BASELINE", "completed_activity_count": None,
            "pending_trial_count": count("_verification_window"),
            "verified_resolution_count": count("_verified_recent"), "recovered_value": None,
            "rows": [public(r) for r in rows]}, complete


#: CH-3 §5: thread states (chain/lifecycle.py VERIFIED_STATES / ATTENTION_STATES).
VERIFIED_THREAD_STATES = VERIFIED_CLASS
ATTENTION_THREAD_STATES = OPEN_CLASS


def thread_progress(f_rows: list[dict[str, Any]]) -> dict[str, int] | None:
    """CH-3 §5 (I-24): over the window's Finding rows' threads (state on the window's last day as of its cutoff):
    `verified_resolution_count` = threads in RESOLVED_MONITORING or CLOSED; `priority_site_count` = Sites with a
    thread in OPEN, RECURRED or REOPENED. None when no row carries a thread (no thread port, or below 0042)."""
    # Review L3: one state per thread, independent of row order: the row of the thread's highest segment (its
    # current state), then the highest occurrence number.
    best: dict[str, tuple[tuple[int, int], str, Any]] = {}
    for r in f_rows:
        t = r.get("_thread")
        if not t:
            continue
        rank = (int(t.get("segment_no") or 0), int(t.get("occurrence_no") or 0))
        prior = best.get(str(t["id"]))
        if prior is None or rank > prior[0]:
            best[str(t["id"])] = (rank, str(r["site_id"]), t.get("state"))
    threads = {tid: (sid, st) for tid, (_, sid, st) in best.items()}
    if not threads:
        return None
    # CH5a2b-R Q7: the one classifier; the legacy fields stay on this Finding-row set until CH-6b.
    return {"verified_resolution_count": classify(st for _, st in threads.values())["verified"],
            "priority_site_count": len({sid for sid, st in threads.values() if classify([st])["open"]})}


def card_notes(summary: dict[str, Any], authorized: int) -> dict[str, str | None]:
    """CH6b2-R Q1: the Portfolio-body clauses of the Protect and Assure cards as ONE server line each, rendered as
    its own line and never joined in the browser. CH6b3-R3 M1: "days checked" means graded COMPLETE (the card's days
    line), so the coverage clause is gone. Protect: None. Assure: the evidence-gap clause.
    PV-1-R §2: the money clause is the Assure card's `value_note` (`portfolio_cards`)."""
    on_checked = summary.get("count_basis") == CHECKED_DAYS_BASIS
    return {"PROTECT_ASSET": None,
            "ASSURE_PERFORMANCE": evidence_gap_text(summary.get("evidence_gap_site_count"), authorized, on_checked)}


def recovered(snap: Any, tenant_id: Any, a_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """CH-3 §5 (OD-3 / AG-24), CH3-R, FUEL-1 A2: one item per credited result (a stored, priced, positive total on
    a MODELLED_IMPROVEMENT cost check of a VERIFIED outcome), keyed by its verification outcome id and never summed,
    or "No money credited · modelled, not saved". The per-kWh rate is never summed. The estate `cost_checks` port
    reads state and currency only (no priced total), so this still reads not credited (PV-1 owns the value lines)."""
    port = getattr(snap, "cost_checks", None)
    ids = [str(a["_raw"]["_outcome_id"]) for a in a_rows if a["_raw"].get("_outcome_id") is not None]
    checks = port(tenant_id, ids) if port is not None and ids else {}

    def check(outcome_id: str) -> dict[str, Any] | None:
        found = checks.get(outcome_id.lower())
        return None if found is None else {**found, "outcome_id": outcome_id.lower()}

    return recovered_value([(check(str(a["_raw"]["_outcome_id"])), a.get("verification_outcome"))
                            for a in a_rows if a["_raw"].get("_outcome_id") is not None])


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
            "window_end": x["window_end"], **_destination(x["link_refs"]["evidence"])}


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
        31-day work window. COV-PARTIAL: one board day is never PARTIAL (`test_cov_partial.py` T10). One
        `self._read` snapshot and cutoff for both. None when the Site is not in the
        authorized imported set for the board day. The request kind is "findings" (no cursor is ever passed)."""
        day = estate_request("findings", day_from, day_to, known_at)  # addendum 7: the estate window rule
        work_req = estate_request("findings", work_from, work_to, known_at)
        admit = lambda code: code == site_code  # noqa: E731 - one-Site admit

        def work(snap: Any) -> Any:
            f_sites, f_rows = select_finding_scope(snap, tenant_id, day, self._scope(snap, tenant_id, day, admit))
            if not f_sites:
                return None
            _, a_rows = select_action_scope(snap, tenant_id, work_req, self._scope(snap, tenant_id, work_req, admit))
            attach_threads(snap, tenant_id, f_rows, a_rows)
            return {"site_cov": f_sites[0][2], "findings": f_rows, "actions": a_rows}

        return self._read(work)

    def site_work_rows_many(self, tenant_id: Any, windows: Mapping[str, tuple[datetime, datetime, datetime, datetime]],
                            known_at: datetime | None = None, *, snap: Any = None
                            ) -> dict[str, dict[str, Any] | None]:
        """QW-2: `site_work_rows` for several Sites, each on its own `(day_from, day_to, work_from, work_to)`, on ONE
        snapshot (the caller's `snap` when given) with one scope per distinct window. Each value equals the
        single-Site method's for that Site (the same rows in the same order); None outside the authorized set."""

        def work(snap: Any) -> dict[str, dict[str, Any] | None]:
            out: dict[str, dict[str, Any] | None] = {code: None for code in windows}
            for (day_from, day_to, work_from, work_to), codes in _by_window(windows).items():
                day = estate_request("findings", day_from, day_to, known_at)
                work_req = estate_request("findings", work_from, work_to, known_at)
                f_sites, f_rows = select_finding_scope(snap, tenant_id, day,
                                                       self._scope(snap, tenant_id, day, _admit_any(codes)))
                if not f_sites:
                    continue
                present = [site["site_code"] for site, _, _ in f_sites]
                _, a_rows = select_action_scope(snap, tenant_id, work_req,
                                                self._scope(snap, tenant_id, work_req, _admit_any(present)))
                attach_threads(snap, tenant_id, f_rows, a_rows)
                for site, _, cov in f_sites:
                    sid = str(site["site_id"])
                    out[site["site_code"]] = {"site_cov": cov, "findings": [r for r in f_rows if r["site_id"] == sid],
                                              "actions": [r for r in a_rows if r["site_id"] == sid]}
            return out

        return work(snap) if snap is not None else self._read(work)

    def read_snapshot(self, work: Callable[[Any], Any]) -> Any:
        """QW-2: one estate snapshot for a caller's batched `*_many` reads (`snap=`), with the S12/S15 retry."""
        return self._read(work)

    def _portfolio(self, snap: Any, tenant_id: Any, req: EstateRequest, admit: Admit) -> dict[str, Any]:
        lap = perf.Laps("portfolio")  # QW-1: section timers (no value changes)
        scope = self._scope(snap, tenant_id, req, admit)
        lap("scope")
        cutoffs: dict[str, Any] = {}
        f_sites, f_rows = select_finding_scope(snap, tenant_id, req, scope, cutoffs)
        lap("findings")
        a_sites, a_rows = select_action_scope(snap, tenant_id, req, scope)
        attach_threads(snap, tenant_id, f_rows, a_rows, req, scope["k"], cutoffs)
        opp_items = opportunity_read(snap, tenant_id, scope, req)  # CH-4 §4.2: the Findings items, same call
        lap("actions")
        e_sites, e_rows_all = select_evidence_scope(snap, tenant_id, req, scope)
        lap("evidence")
        m_sites, m_lines_all, applicable, groups, exclusions, diagnostics = select_financial_scope(
            snap, tenant_id, req, scope)
        lap("money")
        by = lambda per: {str(x[0]["site_id"]): x for x in per}  # noqa: E731 - per-Site lookup
        actions_by, evidence_by, money_by = by(a_sites), by(e_sites), by(m_sites)

        units, token_sites, covered = {"F": [], "E": [], "M": []}, [], 0
        pending = False
        partial_sites, settled_or_partial = 0, True
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
            all_g = all(c != U for c in (f, e, *m))
            partial = cov["state"] == e_cov["state"] == m_cov["state"] == PARTIAL
            covered += all_g
            partial_sites += partial
            settled_or_partial = settled_or_partial and (all_g or partial)
            pending = pending or money_pending(m_cov, m_lines) or any(
                c["state"] == PENDING or c["job_state"] == "PENDING" for c in (cov, e_cov, m_cov))
            token_sites.append(token_site(site, domain, cov, [
                actions_by[sid][1], {**e_cov, **_evidence_arrays(e_rows)}, {**m_cov, **_money_arrays(m_cov, m_lines)}]))
        lap("coverage")
        count = len(scope["sites"])
        states = {key: reduce_units(count, units[key]) for key in ("F", "E", "M")}
        if count == 0:
            status = EMPTY_SCOPE
        elif snap.basis_historical:  # S1/S2: page two keeps page one's basis mode, never the captured cutoff
            status = HISTORICAL_STATUS
        elif pending:
            status = PENDING_STATUS
        elif partial_sites and settled_or_partial:
            status = PARTIAL_STATUS
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
        lap("rows")

        coverage_state = reduce_units(count, [*units["F"], *units["E"], *units["M"]])
        body = self._envelope(PORTFOLIO_SCHEMA, tenant_id, req, scope, covered, status,
                              {"state": coverage_state, "finding_state": states["F"],
                               "evidence_state": states["E"], "money_state": states["M"],
                               # PARTIAL-MONEY: a PARTIAL Site's analysed-days amount from its money lines.
                               "sites": [{**_coverage_site(site, cov), **({} if (m := partial_money(
                                   site, money_by[str(site["site_id"])][2], money_by[str(site["site_id"])][3])) is None
                                   else {"money": m})} for site, _, cov in f_sites]})
        empty = count == 0
        gaps = evidence_gap_groups(e_rows_all)
        prog, actions_complete = progress(a_sites, a_rows, scope["k"],
                                          {(r["finding_id"], r["finding_revision_id"]) for r in f_rows}, f_rows)
        thread_counts = thread_progress(f_rows)
        if thread_counts is not None:  # CH-3 §5 (I-24): counts from thread states when the threads are read
            prog["verified_resolution_count"] = thread_counts["verified_resolution_count"]
        prog["recovered_value"] = recovered(snap, tenant_id, a_rows)
        # WALK1-1 (WN-2): counts are claims on complete (or complete-empty) coverage of their root, or, on a PARTIAL
        # estate, over the checked days (a PARTIAL Site's rows already drop every head touching an unchecked day,
        # `coverage.py` §2.5). Nothing is extrapolated; money is unchanged (D-W1-4).
        coverage_basis = ("COMPLETE" if states["F"] in (COMPLETE, EMPTY)
                          else "CHECKED_DAYS" if status == PARTIAL_STATUS else None)
        finding_known = coverage_basis is not None
        # Pre-flight E1: `select_evidence_scope` emits rows for a PARTIAL mini-grid Site (one per dispatch day,
        # unchecked days UNASSESSED with no typed gap), so the evidence gap count follows the same rule.
        evidence_known = states["E"] in (COMPLETE, EMPTY) or coverage_basis == "CHECKED_DAYS"
        # CH-5a2b (§B13 R3, §B14 Q7-Q9): the PC-1 count claims from the one chain computation, and
        # `summary.count_basis` from the one basis rule over their day grades. `coverage_basis` above keeps only the
        # nullability of `finding_count` / `evidence_gap_site_count` until CH-6b.
        counted = self._claims(tenant_id, scope, req)
        claims = self.claims_json(counted, CLAIM_KEYS)
        priority_sites = None if thread_counts is None else thread_counts["priority_site_count"]
        if self.count_claims is not None:  # CH6b3-R Q4b: both legacy fields read the claims (BL-35 retires the names)
            prog["verified_resolution_count"] = None if counted is None else counted.claims[VERIFIED_CLAIM].value
            priority_sites = priority_site_count(counted)
        summary: dict[str, Any] = {
            "finding_count": len(members) if finding_known else None,
            "priority_site_count": priority_sites,
            "opportunity_count": None if opp_items is None else len(opp_items),
            "opportunity_labels": None if opp_items is None else [i["short_label"] for i in opp_items],
            "evidence_gap_site_count": len({sid for g in gaps for sid in g["site_ids"]}) if evidence_known else None,
            "accepted_action_count": len(a_rows) if actions_complete else None,
            "verified_resolution_count": prog["verified_resolution_count"],
            "combined_value": None, "combined_value_state": "NOT_COMPARABLE",
            # CC-R2: over `members` (all lenses, like `finding_count`); all five keys; null unless F is known.
            "placement_counts": {g: (sum(1 for r in members if r["placement"]["group"] == g) if finding_known else None)
                                 for g in GROUPS},
            # OUT-A2 (ruling A-Q11): over `members`; all four keys; both counts null unless F is known.
            "category_counts": category_counts(members, finding_known),
            "count_basis": count_basis(claims[CLAIM_KEYS[0]]["days"]),
            "claims": claims,
            "checked_days": [{"site_id": str(site["site_id"]), "site_name": site["site_name"],
                              "checked": cov["days"]["checked"], "requested": cov["days"]["requested"],
                              "withheld": bool(cov["days"].get("withheld"))}
                             for site, _, cov in f_sites if cov["state"] == PARTIAL and cov.get("days")]}
        summary["card_notes"] = card_notes(summary, len(scope["sites"]))
        # r1b2 R11: one batched provenance read for every represented Site with a selected ID (no per-Site query
        # loop); a Site without a selected ID has null provenance ("No selected source basis").
        lap("summary")
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
                                     "coverage": _coverage_site(site, cov), "selected_revision_count": len(ids),
                                     "source_provenance": disclosure_provenance(next(resolved)) if ids else None})
        lap("disclosure")
        body.update({"lens": req.lens, "summary": summary,
                     "value_cards": value_cards(m_lines_all, applicable, groups, opp_items),
                     "objectives": [objective(site, evidence_by[str(site["site_id"])], money_by[str(site["site_id"])],
                                              bool(snap.basis_historical)) for site, _, _ in f_sites],
                     "evidence_prompt": evidence_prompt(states["E"], gaps),
                     "opportunity": opportunity_block(opp_items),
                     "progress": prog, "footer": footer(m_sites, m_lines_all),
                     "selected_lines": [public(x) for x in m_lines_all],
                     "money": {"groups": [] if empty else groups, "exclusions": [] if empty else exclusions,
                               "diagnostics": [] if empty else diagnostics, "estate_total": None},
                     "scope_disclosure": {"sites": disclosure_sites, "exclusions": [] if empty else exclusions},
                     # CH-5c Q9: the ids leave the body; the scope-ids sub-route serves them when the disclosure opens.
                     SCOPE_IDS_KEY: [{"site_id": str(site["site_id"]), "selected_revision_ids": ids}
                                     for (site, _, _), ids in zip(f_sites, site_ids)],
                     "order": PORTFOLIO_ORDER, "total_count": len(shown),
                     "rows": [{k: v for k, v in r.items() if not k.startswith("_")} for r in page],
                     "next_cursor": None if last is None else self._cursor(tenant_id, req, scope, token,
                                                                          *last["_marker"]),
                     "selection_token": token})
        lap("cards")
        return body
