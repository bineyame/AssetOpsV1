"""OUT-B1: pure assembly of the Site outcome board (build spec §B.2; rulings B-Q14/Q18/Q19/Q20/Q28, addenda 1-2).

It imports only `outcomes/`. The domain composer (B2/B3) reads the ports and hands this module a `SiteFacts`. This
module attributes Findings, signals, Actions, cases and plans to the four category rows. It sets each outcome's state
and rolls each row up. It writes no storage and formats no money (B-Q14)."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from assetops_backend.outcomes.catalogue import (
    CATEGORIES, CATEGORY_DEFINITION, CATEGORY_ICON, CATEGORY_LABEL, COLD, EV, MINI, OUTCOME_BY_KEY, SITE_OUTCOMES,
    SiteOutcome, row_not_measured)
from assetops_backend.outcomes.outcome_map import finding_signal_key, outcome_roles
from assetops_backend.outcomes.status import (
    EVIDENCE_GAP, FINDING, NOT_MEASURED, SIGNAL_OPPORTUNITY, STATE_LABEL, STATE_TONE, Signal, outcome_state, roll_up)

OPEN_LIFECYCLES = ("SUPPORTED", "UNCONFIRMED")  # Portfolio membership rule (estate/portfolio.py:38)
CLOSED_CASE_STATES = ("COMPLETED", "CLOSED", "CANCELLED")
MAINTENANCE_REQUEST, INCIDENT = "MAINTENANCE_REQUEST", "INCIDENT"
NO_PLAN = "NO_PLAN"

SAFEGUARD_SUFFIX = " · checked here as a safeguard"  # mock outcomes.js:71
NOT_LINKED_SUFFIX = " · not linked to a finding"
OUTSIDE_VIEW_SUFFIX = " · linked finding outside this view"  # addendum 2 item 4
EARLIER_EMPTY_OPEN = "No earlier work has been checked for this"
EARLIER_EMPTY_NONE = "Not available yet · no completed work or checked change for this outcome"  # addendum 2
#: Rulings B addendum 1: Must not harm names every CHECKED outcome in another category, measured or not.
#: Set True to restore the withdrawn "excluding NOT_MEASURED" reading.
MUST_NOT_HARM_EXCLUDES_UNMEASURED = False

ISSUE_KIND_LABEL = {"FINDING": "Finding", "EVIDENCE_GAP": "Evidence gap", "RISK": "Risk",
                    "EARLY_WARNING": "Early warning", "OPPORTUNITY": "Opportunity"}  # outcomes.js:112

#: Mini Action in-hand label: the Portfolio workflow_label (estate/portfolio.py:137), two words renamed (outcomes.js:67).
WORKFLOW_IN_HAND = {"Recommendation not accepted": "Plan ready", "Outcome pending": "Awaiting verification"}
CASE_STATE_LABEL = {"OPEN": "Open", "IN_PROGRESS": "In progress", "ASSIGNED": "Assigned"}

#: Earlier interventions result labels for a mini Action, by verification state (§B.2 table). NO_PLAN / None: not listed.
ACTION_RESULT = {"VERIFIED": "Verified on test data", "INEFFECTIVE": "Did not fix it",
                 "INCONCLUSIVE": "Not determined", "PENDING": "Pending", "REASSESSMENT_PENDING": "Pending"}
REQUEST_REPEATED, REQUEST_UNVERIFIED = "Did not fix it", "Not yet verified"

#: Evidence link per (domain, category); None where the row is not measured (§B.2 table).
EVIDENCE_LINK: dict[tuple[str, str], tuple[str, str] | None] = {
    (MINI, "GROW_REVENUE"): ("Renewable evidence", "/sites/{c}/performance/renewable"),
    (MINI, "OPTIMIZE_COST"): ("Dispatch evidence", "/sites/{c}/performance/dispatch"),
    (MINI, "PROTECT_ASSET"): ("Battery evidence", "/sites/{c}/health"),
    (MINI, "ASSURE_PERFORMANCE"): ("Evidence overview", "/sites/{c}/evidence"),
    (COLD, "GROW_REVENUE"): None,
    (COLD, "OPTIMIZE_COST"): ("Financial bridge", "/sites/{c}/financials"),
    (COLD, "PROTECT_ASSET"): ("Cold-room evidence", "/sites/{c}/evidence"),
    (COLD, "ASSURE_PERFORMANCE"): ("Evidence overview", "/sites/{c}/evidence"),
    (EV, "GROW_REVENUE"): ("Financial bridge", "/sites/{c}/ev/financials"),
    (EV, "OPTIMIZE_COST"): None,
    (EV, "PROTECT_ASSET"): ("Depot evidence", "/sites/{c}/ev/evidence"),
    (EV, "ASSURE_PERFORMANCE"): ("Evidence overview", "/sites/{c}/ev/evidence"),
}

#: Confidence chips (§B.2 table).
READINESS_CONFIDENCE = {"FULL": ("High", "green"), "LIMITED": ("Limited", "amber"), "NONE": ("Low", "amber"),
                        "UNKNOWN": ("Unknown", "gray")}
DECLARED = {"label": "Declared", "tone": "neutral"}
PLAN_RECORD = {"label": "Plan record", "tone": "neutral"}

_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
_FINDING_REASONS = ("PRIMARY_FINDING_OPEN", "PRIMARY_FINDING_APPLIED", "SECONDARY_FINDING_OPEN")


def readiness_confidence(readiness: str | None) -> dict[str, str] | None:
    """The chip for a Site evidence readiness value; None (absent readiness) reads as Unknown."""
    label, tone = READINESS_CONFIDENCE.get(readiness or "UNKNOWN", READINESS_CONFIDENCE["UNKNOWN"])
    return {"label": label, "tone": tone}


# ---------------------------------------------------------------- inputs

@dataclass(frozen=True)
class FindingFact:
    finding_id: str
    revision_id: str
    title: str
    mechanism: str | None
    lifecycle: str
    href: str | None
    asset_id: str | None = None
    confidence_label: str | None = None
    #: Addendum 2 item 4: False for a Finding read only to resolve a link (outside the overview day). Such a
    #: Finding places linked work but drives no signal, issue or headline.
    in_window: bool = True

    @property
    def open(self) -> bool:
        return self.lifecycle in OPEN_LIFECYCLES


@dataclass(frozen=True)
class ActionFact:
    action_id: str
    code: str | None
    title: str
    origin_finding_id: str | None
    origin_revision_id: str | None
    applied: bool                      # application_state APPLIED or later (§1.4)
    open: bool                         # workflow_label not in ("Verified", "Resolution withdrawn") (B-Q18)
    verification_state: str | None     # NO_PLAN | PENDING | REASSESSMENT_PENDING | VERIFIED | INEFFECTIVE | ...
    href: str | None
    # Additions recorded in the packet (B1 deviation 2): the inputs the §B.2 labels and links need.
    workflow_label: str | None = None  # mini: estate/portfolio.py:137 text
    verification_href: str | None = None  # /sites/{c}/actions/{id}/verification?event_id=...
    is_domain: bool = False            # cold/EV domain Action: in hand only, never applied


@dataclass(frozen=True)
class CaseFact:
    case_id: str
    code: str | None
    kind: str                          # INCIDENT | MAINTENANCE_REQUEST
    title: str
    state: str
    asset_id: str | None
    asset_label: str | None
    finding_ids: tuple[str, ...]
    occurred_at: Any                   # comparable (datetime); only ordering is used
    href: str | None


@dataclass(frozen=True)
class PlanFact:
    plan_id: str
    code: str | None
    title: str
    trigger_kind: str                  # CALENDAR | RUN_HOURS
    next_due_at: Any                   # a Site-local date (has .day, .month), or None
    next_due_hours: float | int | None
    state: str
    asset_id: str | None
    href: str | None


#: Issue kind of each non-Finding signal (§B.2): headroom is an opportunity, the evidence gap is a gap.
SIGNAL_ISSUE_KIND = {"SIGNAL:PRODUCTIVE_USE_HEADROOM": "OPPORTUNITY", "SIGNAL:EVIDENCE_GAP": "EVIDENCE_GAP"}


@dataclass(frozen=True)
class SignalFact:
    """A non-Finding `SIGNAL:*` fact (B1 deviation 3). Its issue kind is derived from `signal_key`."""
    signal_key: str                    # a SIGNAL_ISSUE_KIND key
    open: bool
    text: str
    href: str | None = None

    @property
    def kind(self) -> str:
        return SIGNAL_ISSUE_KIND[self.signal_key]


@dataclass(frozen=True)
class Contributor:
    key: str
    label: str
    text: str
    confidence: Mapping[str, str] | None = None
    href: str | None = None


@dataclass(frozen=True)
class Option:
    text: str
    href: str | None = None


@dataclass(frozen=True)
class SiteFacts:
    domain: str
    site_code: str
    findings: tuple[FindingFact, ...] = ()
    actions: tuple[ActionFact, ...] = ()
    cases: tuple[CaseFact, ...] = ()
    plans: tuple[PlanFact, ...] = ()
    readiness: str | None = None
    contributors: Mapping[str, Sequence[Contributor]] = field(default_factory=dict)
    options: Mapping[str, Sequence[Option]] = field(default_factory=dict)
    signals_extra: tuple[SignalFact, ...] = ()
    headline: Mapping[str, str | None] = field(default_factory=dict)
    headline_money: Mapping[str, Mapping[str, Any] | None] = field(default_factory=dict)  # B-Q14 passthrough
    subline: Mapping[str, str | None] = field(default_factory=dict)
    settled: Mapping[str, bool] = field(default_factory=dict)  # per outcome key; absent = not settled
    warnings: tuple = ()               # C


# ---------------------------------------------------------------- helpers

def join_names(labels: Sequence[str]) -> str:
    """"A and B" / "A, B and C", sentence-cased on the first letter only (§B.2)."""
    parts = [labels[0]] + [lab[:1].lower() + lab[1:] for lab in labels[1:]]
    text = parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]
    return text[:1].upper() + text[1:]


def _item_text(code: str | None, title: str) -> str:
    """"{code} · {title}"; an item with no stored title (every mini Action, addendum 2 item 1) reads its code."""
    if code and title:
        return f"{code} · {title}"
    return code or title


def _action_name(a: "ActionFact") -> str:
    return a.code or a.title


def unresolved_links(facts: "SiteFacts") -> tuple[tuple[str, str], ...]:
    """(holder id, Finding id) for every case or Action link the composer could not resolve (addendum 2 item 4).
    The composer records these as its internal diagnostics; they are never on the wire."""
    known = {f.finding_id for f in facts.findings}
    out: list[tuple[str, str]] = []
    for a in sorted(facts.actions, key=lambda a: a.action_id):
        if a.origin_finding_id is not None and a.origin_finding_id not in known:
            out.append((a.action_id, a.origin_finding_id))
    for c in sorted(facts.cases, key=lambda c: c.case_id):
        out.extend((c.case_id, fid) for fid in c.finding_ids if fid not in known)
    return tuple(out)


def _plan_label(plan: PlanFact) -> str:
    if plan.trigger_kind == "RUN_HOURS" and plan.next_due_hours is not None:
        hours = plan.next_due_hours
        return f"Due at {int(hours) if float(hours).is_integer() else hours} operating hours"
    if plan.next_due_at is not None:
        return f"Due {plan.next_due_at.day} {_MONTHS[plan.next_due_at.month - 1]}"
    return plan.state.replace("_", " ").capitalize()


def _case_label(case: CaseFact) -> str:
    return CASE_STATE_LABEL.get(case.state) or case.state.replace("_", " ").capitalize()


def _categories(keys: Sequence[str]) -> list[str]:
    out: list[str] = []
    for k in keys:
        cat = OUTCOME_BY_KEY[k].category
        if cat not in out:
            out.append(cat)
    return out


class _Roles:
    """moves/checked outcome keys of one Finding or signal, resolved for the Site's domain."""

    def __init__(self, signal_key: str, domain: str) -> None:
        self.moves, self.checked = outcome_roles(signal_key, domain)
        self.move_cats = _categories(self.moves)
        self.checked_cats = [c for c in _categories(self.checked) if c not in self.move_cats]

    def checked_in(self, category: str, *, exclude_unmeasured: bool = False) -> list[str]:
        return [OUTCOME_BY_KEY[k].label for k in self.checked if OUTCOME_BY_KEY[k].category == category
                and not (exclude_unmeasured and not OUTCOME_BY_KEY[k].measured)]

    def checked_outside(self, category: str, *, exclude_unmeasured: bool) -> list[str]:
        return [OUTCOME_BY_KEY[k].label for k in self.checked if OUTCOME_BY_KEY[k].category != category
                and not (exclude_unmeasured and not OUTCOME_BY_KEY[k].measured)]


def earlier_result_for_action(action: ActionFact) -> str | None:
    """Result label for a mini Action in Earlier interventions, or None when it is not listed (B-Q18)."""
    if action.is_domain or not action.applied:
        return None
    return ACTION_RESULT.get(action.verification_state or NO_PLAN)


def earlier_result_for_case(case: CaseFact, cases: Sequence[CaseFact]) -> str | None:
    """§B.2: a COMPLETED request is "Did not fix it" when another request on the same asset, or sharing a Finding,
    occurred later; otherwise "Not yet verified". Incidents and open requests are not listed."""
    if case.kind != MAINTENANCE_REQUEST or case.state != "COMPLETED":
        return None
    for other in cases:
        if other.case_id == case.case_id or other.kind != MAINTENANCE_REQUEST:
            continue
        related = (case.asset_id is not None and other.asset_id == case.asset_id) or (
            set(case.finding_ids) & set(other.finding_ids))
        if related and other.occurred_at is not None and case.occurred_at is not None \
                and other.occurred_at > case.occurred_at:
            return REQUEST_REPEATED
    return REQUEST_UNVERIFIED


# ---------------------------------------------------------------- assembly

def assemble(facts: SiteFacts) -> list[dict[str, Any]]:
    """The four board rows in canonical category order (§B.1 row shape)."""
    domain, code = facts.domain, facts.site_code
    roles = {f.finding_id: _Roles(finding_signal_key(f.mechanism), domain) for f in facts.findings}
    by_id = {f.finding_id: f for f in facts.findings}
    mini_actions = [a for a in facts.actions if not a.is_domain]

    def exact_actions(f: FindingFact) -> list[ActionFact]:
        return [a for a in mini_actions if a.origin_finding_id == f.finding_id
                and a.origin_revision_id == f.revision_id]

    # status signals
    signals: list[Signal] = []
    for f in facts.findings:
        if not f.in_window:
            continue
        applied = any(a.applied for a in exact_actions(f))
        for i, key in enumerate(roles[f.finding_id].moves):
            signals.append(Signal(FINDING, key, i == 0, f.open, applied, None, f.finding_id))
    sig_roles = {s.signal_key: _Roles(s.signal_key, domain) for s in facts.signals_extra}
    for s in facts.signals_extra:
        if not s.open:
            continue
        kind = SIGNAL_OPPORTUNITY if s.kind == "OPPORTUNITY" else EVIDENCE_GAP
        for i, key in enumerate(sig_roles[s.signal_key].moves):
            signals.append(Signal(kind, key, i == 0, True, False, None, s.signal_key))

    open_findings = sorted((f for f in facts.findings if f.open and f.in_window),
                           key=lambda f: (f.title, f.finding_id))
    rows = [_row(facts, cat, signals, roles, by_id, open_findings, sig_roles, exact_actions) for cat in CATEGORIES]
    return rows


def _row(facts: SiteFacts, cat: str, signals: list[Signal], roles: dict[str, _Roles], by_id: dict[str, FindingFact],
         open_findings: list[FindingFact], sig_roles: dict[str, _Roles], exact_actions) -> dict[str, Any]:
    domain, code = facts.domain, facts.site_code
    outcomes: list[SiteOutcome] = [o for o in SITE_OUTCOMES if o.domain == domain and o.category == cat]
    states = []
    for o in outcomes:
        st, reason = outcome_state(o, settled=bool(facts.settled.get(o.key, False)), signals=signals,
                                   readiness=facts.readiness)
        states.append((o, st, reason))
    row_state, lead_key = roll_up([(o.key, st) for o, st, _ in states])
    lead = OUTCOME_BY_KEY[lead_key]
    link = EVIDENCE_LINK.get((domain, cat))
    row: dict[str, Any] = {
        "category": cat, "label": CATEGORY_LABEL[cat], "definition": CATEGORY_DEFINITION[cat],
        "icon": CATEGORY_ICON[cat], "state": row_state, "state_label": STATE_LABEL[row_state],
        "tone": STATE_TONE[row_state], "lead_outcome": {"key": lead.key, "label": lead.label},
        "headline": None, "headline_money": None, "subline": None, "not_measured_text": None,
        "counts": {"issues": 0, "in_hand": 0}, "must_not_harm": None,
        "contributors": [], "issues": [], "options": [], "in_hand": [], "earlier": [], "earlier_empty_text": None,
        "evidence_link": None if link is None else {"label": link[0], "href": link[1].format(c=code)},
        "outcomes": [{"key": o.key, "label": o.label, "state": st, "reason": reason} for o, st, reason in states],
    }
    if row_state == NOT_MEASURED:
        row["not_measured_text"] = row_not_measured(domain, cat, lead)
        return row

    moves_here = [f for f in facts.findings if cat in roles[f.finding_id].move_cats]
    checked_here = [f for f in facts.findings if cat in roles[f.finding_id].checked_cats]

    # Issues: MOVES Findings by title, signals (MOVES before CHECKED), CHECKED Findings (B-Q20).
    issues: list[dict[str, Any]] = []
    for f in open_findings:
        if f in moves_here:
            issues.append(_finding_issue(f, "MOVES", f.title))
    open_signals = [s for s in facts.signals_extra if s.open]
    for role in ("MOVES", "CHECKED"):
        for s in open_signals:
            r = sig_roles[s.signal_key]
            if cat in (r.move_cats if role == "MOVES" else r.checked_cats):
                issues.append({"kind": s.kind, "role": role, "text": s.text, "href": s.href, "ref": None})
    for f in open_findings:
        if f in checked_here:
            issues.append(_finding_issue(f, "CHECKED", f.title + SAFEGUARD_SUFFIX))

    # Already in hand and Earlier interventions (B-Q18).
    in_hand: list[dict[str, Any]] = []
    earlier: list[dict[str, Any]] = []
    for a in sorted(facts.actions, key=lambda a: (a.code or "", a.action_id)):
        if a.origin_finding_id is None:
            continue
        origin = by_id.get(a.origin_finding_id)
        suffix = "" if origin is not None else OUTSIDE_VIEW_SUFFIX
        r = roles[origin.finding_id] if origin is not None else None
        move_cats = r.move_cats if r is not None else ["PROTECT_ASSET"]
        result = earlier_result_for_action(a)
        if result is not None:
            if cat in move_cats:
                earlier.append({"text": _item_text(a.code, a.title), "href": a.href, "result_label": result + suffix})
            elif r is not None and cat in r.checked_cats:
                names = r.checked_in(cat, exclude_unmeasured=MUST_NOT_HARM_EXCLUDES_UNMEASURED)
                if names:
                    earlier.append({"text": f"{join_names(names)} checked as safeguards in {_action_name(a)}",
                                    "href": a.verification_href or a.href, "result_label": result})
        elif a.open and cat in move_cats:
            label = "Open" if a.is_domain else WORKFLOW_IN_HAND.get(a.workflow_label or "", a.workflow_label or "Open")
            in_hand.append({"text": _item_text(a.code, a.title), "href": a.href, "state_label": label + suffix})

    for case in sorted(facts.cases, key=lambda c: (c.code or "", c.case_id)):
        cats, suffix = _case_placement(case, by_id, roles)
        if cat not in cats:
            continue
        if case.state not in CLOSED_CASE_STATES:
            label = _case_label(case) + suffix
            in_hand.append({"text": _item_text(case.code, case.title), "href": case.href, "state_label": label})
    for case in sorted(facts.cases, key=lambda c: (c.occurred_at is None, c.occurred_at, c.case_id)):
        cats, suffix = _case_placement(case, by_id, roles)
        result = earlier_result_for_case(case, facts.cases)
        if cat in cats and result is not None:
            earlier.append({"text": _item_text(case.code, case.title), "href": case.href,
                            "result_label": result + (suffix if suffix == OUTSIDE_VIEW_SUFFIX else "")})

    if cat == "PROTECT_ASSET":
        for p in sorted(facts.plans, key=lambda p: (p.code or "", p.plan_id)):
            if p.state in ("DRAFT", "ACTIVE"):
                in_hand.append({"text": _item_text(p.code, p.title), "href": p.href, "state_label": _plan_label(p)})

    # Must not harm (B-Q19, addendum 1): only where a mini Action verification exists.
    must_not_harm = None
    for f in sorted(moves_here, key=lambda f: (f.title, f.finding_id)):
        checks = [a for a in exact_actions(f) if a.verification_state not in (None, NO_PLAN)]
        names = roles[f.finding_id].checked_outside(cat, exclude_unmeasured=MUST_NOT_HARM_EXCLUDES_UNMEASURED)
        if checks and names:
            a = checks[0]
            must_not_harm = {"text": f"{join_names(names)} are checked as safeguards when {_action_name(a)} is "
                                     "verified; a gain that harms them does not count", "href": a.verification_href}
            break

    # Headline: the domain table, else the lead Finding's title on a Finding-driven state.
    headline = facts.headline.get(cat)
    lead_reason = next(reason for o, _, reason in states if o.key == lead_key)
    if headline is None and lead_reason in _FINDING_REASONS:
        primary = lead_reason != "SECONDARY_FINDING_OPEN"
        for f in open_findings:
            moves = roles[f.finding_id].moves
            if lead_key in moves and ((moves[0] == lead_key) == primary):
                headline = f.title
                break

    row.update({
        "headline": headline, "headline_money": facts.headline_money.get(cat), "subline": facts.subline.get(cat),
        "counts": {"issues": len(issues), "in_hand": len(in_hand)}, "must_not_harm": must_not_harm,
        "contributors": [_contributor(c) for c in facts.contributors.get(cat, ())],
        "issues": issues,
        "options": [{"text": o.text, "href": o.href} for o in facts.options.get(cat, ())],
        "in_hand": in_hand, "earlier": earlier,
        "earlier_empty_text": None if earlier else (
            EARLIER_EMPTY_OPEN if any(f.open and f.in_window for f in moves_here) else EARLIER_EMPTY_NONE),
    })
    return row


def _case_placement(case: CaseFact, by_id: dict[str, FindingFact],
                    roles: dict[str, _Roles]) -> tuple[set[str], str]:
    """Categories and state-label suffix for a case. No link: PROTECT_ASSET, "not linked". Links that resolve: their
    Findings' MOVES categories. Links none of which resolve: kept under PROTECT_ASSET with the outside-view suffix
    (addendum 2 item 4, replacing review M1's assertion); the composer records them via `unresolved_links`."""
    if not case.finding_ids:
        return {"PROTECT_ASSET"}, NOT_LINKED_SUFFIX
    linked = [by_id[fid] for fid in case.finding_ids if fid in by_id]
    if not linked:
        return {"PROTECT_ASSET"}, OUTSIDE_VIEW_SUFFIX
    return {c for f in linked for c in roles[f.finding_id].move_cats}, ""


def _finding_issue(f: FindingFact, role: str, text: str) -> dict[str, Any]:
    return {"kind": "FINDING", "role": role, "text": text, "href": f.href,
            "ref": {"finding_id": f.finding_id, "finding_revision_id": f.revision_id}}


def _contributor(c: Contributor) -> dict[str, Any]:
    return {"key": c.key, "label": c.label, "text": c.text,
            "confidence": None if c.confidence is None else dict(c.confidence), "href": c.href}
