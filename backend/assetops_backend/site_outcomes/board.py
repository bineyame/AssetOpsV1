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
    ROW_NOT_MEASURED_EV_COST_UNPRICED, SiteOutcome, row_not_measured)
from assetops_backend.outcomes.objectives import (
    CONTRIBUTOR_LABEL, MET, MISSED, NOT_JUDGED, VERDICT_CHIP, ObjectiveFact, Reading, judge)
from assetops_backend.outcomes.outcome_map import ENTRIES, finding_signal_key, outcome_roles
from assetops_backend.outcomes.status import (
    EVIDENCE_GAP, FINDING, NOT_MEASURED, SIGNAL_OPPORTUNITY, STATE_LABEL, STATE_TONE, WARNING, Signal, outcome_state,
    roll_up)
from assetops_backend.outcomes.warnings import PLAN_DUE_SOON, PLAN_OVERDUE, REPEATED, Warning

OPEN_LIFECYCLES = ("SUPPORTED", "UNCONFIRMED")  # Portfolio membership rule (estate/portfolio.py:38)
CLOSED_CASE_STATES = ("COMPLETED", "CLOSED", "CANCELLED")
MAINTENANCE_REQUEST, INCIDENT = "MAINTENANCE_REQUEST", "INCIDENT"
NO_PLAN = "NO_PLAN"

SAFEGUARD_SUFFIX = " · checked here as a safeguard"  # mock outcomes.js:71
NOT_LINKED_SUFFIX = " · not linked to a finding"
OUTSIDE_VIEW_SUFFIX = " · linked finding outside this view"  # addendum 2 item 4
#: Addendum 3 M1: the suffix when the domain's Finding source is unsettled, so an unresolved link is not "outside".
NOT_LOADED_LINK_SUFFIX = " · Not available yet · linked finding could not be loaded"
UNRESOLVED_SUFFIXES = (OUTSIDE_VIEW_SUFFIX, NOT_LOADED_LINK_SUFFIX)
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
#: OUT-E E4 (build sheet OUT-E section 4): the Earlier entry's cost-check and before/after detail lines.
COST_PREFIX = "Modelled change after the trial · not realised savings: "
COST_CHANGE = COST_PREFIX + "{amount} {currency} less per kWh of feeder demand"
COST_NO_CHANGE = COST_PREFIX + "no lower cost per kWh of feeder demand"
COST_NOT_CALCULATED = "Modelled change not calculated: {words}"
COST_NOT_YET = "Not calculated yet"
#: POLISH D-2 (OUT-E L4): a modelled improvement is credited only to a VERIFIED trial.
COST_NOT_CREDITED = "The trial did not fix the problem, so no cost change is credited to it"
TRIAL_ATTRIBUTED = "{label} before the trial: {before} · after: {after}"
TRIAL_NOT_ATTRIBUTED = "Status changed; not attributed"
TRIAL_UNCHANGED = "{label}: {verdict} before and after the trial"
TRIAL_VERDICT = {MET: "met", MISSED: "missed"}
COST_REASON_WORDS = {
    "OUTCOME_INCONCLUSIVE": "the trial result is not determined",
    "WINDOW_INCOMPLETE": "a comparison hour is incomplete",
    "NOT_COMPARABLE": "the two hours are not comparable",
    "SOURCE_NOT_COHERENT": "the two hours come from different sources",
    "EVIDENCE_REPLAY_MISMATCH": "the readings changed after the result was recorded",
    "GENERATOR_KWH_UNKNOWN": "generator energy is not known for both hours",
    "ZERO_DEMAND": "an hour had no demand",
    "SFC_MISSING": "the generator fuel rate is not recorded",
    "SFC_DIFFERS": "the generator fuel rate differs between the hours",
    "PRICE_MISSING": "no diesel price covers both hours",
    "PRICE_BASIS_DIFFERS": "the two hours were priced from different diesel price records",
}
FINAL_VERIFICATION = ("VERIFIED", "INEFFECTIVE", "INCONCLUSIVE")
TRIAL_MEASURE = "avoidable_generator_minutes"  # the MG-2 objective (R593: before/after only on a zero target)
#: C: plan state labels when the plan's due cue fires (the plan itself stays DRAFT; register R08, R10).
PLAN_CUE_LABEL = {PLAN_OVERDUE: "Overdue", PLAN_DUE_SOON: "Due soon"}
REPAIR_MUST_NOT_HARM = ": a repair counts only when the fault it answers stops"

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
    #: LINK-LINEAGE: origin revision IDs for which the composer proved `refresh_chain` true for this shown revision.
    refreshed_from: tuple[str, ...] = ()

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
    # OUT-E E4: the verification summary's stored cost check and trial hours of the current outcome (last, defaulted)
    cost_check: Mapping[str, Any] | None = None   # {state, reason, nominal, upper, currency, recorded_at}
    trial_hours: Mapping[str, Any] | None = None  # {before_seconds, after_seconds}


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
    due_at: Any = None                 # C: the UTC instant of `next_due_at` (compared only)


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
    warnings: tuple[Warning, ...] = ()  # C: `outcomes/warnings.evaluate` order
    #: Addendum 2 item 6: appended to Site-local dates when the Site zone is unavailable (dates are then UTC).
    date_suffix: str = ""
    #: Addendum 3 M1: False when the domain's Finding source was refused, failed or not current.
    findings_settled: bool = True
    #: OUT-D U4: the Site's declared objectives (catalogue order), their readings per outcome key, and False when the
    #: objectives read failed (status rule 7c: an unjudged outcome is then Unknown, never "No objective declared").
    objectives: tuple[ObjectiveFact, ...] = ()
    readings: Mapping[str, Reading] = field(default_factory=dict)
    objectives_ok: bool = True
    #: IDX-GAPS U2: mini only, the Finding index gap line `{text, days}` under the rows; None = no gap day.
    finding_gaps: Mapping[str, Any] | None = None


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


def finding_moved_outcomes(domain: str) -> frozenset[str]:
    """Addendum 3 M1: every outcome a `FINDING:*` map entry of `domain` moves (mini MG-2; cold CC-6, CC-1; EV EV-1,
    EV-3). These are unsettled when the domain's Finding source is."""
    return frozenset(k for key in ENTRIES if key.startswith("FINDING:") for k in outcome_roles(key, domain)[0])


def unresolved_suffix(facts: "SiteFacts") -> str:
    """The state-label suffix of a case or Action whose linked Finding is absent (addendum 2 item 4, addendum 3 M1)."""
    return OUTSIDE_VIEW_SUFFIX if facts.findings_settled else NOT_LOADED_LINK_SUFFIX


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


def _plan_label(plan: PlanFact, date_suffix: str = "") -> str:
    if plan.trigger_kind == "RUN_HOURS" and plan.next_due_hours is not None:
        hours = plan.next_due_hours
        shown = int(hours) if float(hours).is_integer() else hours
        return f"Due at {shown} operating {'hour' if float(hours) == 1 else 'hours'}"  # addendum 3 L7
    if plan.next_due_at is not None:
        return f"Due {plan.next_due_at.day} {_MONTHS[plan.next_due_at.month - 1]}{date_suffix}"
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


class _WarningRoles:
    """MOVES/CHECKED outcome keys and categories of one warning, read from its wire `categories`."""

    def __init__(self, w: Warning) -> None:
        items = w.categories.get("items") or ()
        self.moves = [o["key"] for i in items if i["role"] == "MOVES" for o in i["outcomes"]]
        self.checked = [o["key"] for i in items if i["role"] == "CHECKED" for o in i["outcomes"]]
        self.move_cats = _categories(self.moves)
        self.checked_cats = [c for c in _categories(self.checked) if c not in self.move_cats]

    def checked_outside(self, category: str) -> list[str]:
        return [OUTCOME_BY_KEY[k].label for k in self.checked if OUTCOME_BY_KEY[k].category != category]


def earlier_result_for_action(action: ActionFact) -> str | None:
    """Result label for a mini Action in Earlier interventions, or None when it is not listed (B-Q18)."""
    if action.is_domain or not action.applied:
        return None
    return ACTION_RESULT.get(action.verification_state or NO_PLAN)


def per_kwh_amount(cost_check: Mapping[str, Any]) -> str:
    """`lo–hi` (one figure when equal): the stored nominal and upper change rounded to 3 decimals, half-even."""
    lo, hi = (_round3(cost_check[k]) for k in ("nominal", "upper"))
    return lo if lo == hi else f"{lo}–{hi}"


def _ratio(text: str) -> tuple[int, int]:
    """An exact `fmt` string (decimal or `p/q`) as (numerator, denominator); board.py stays stdlib-minimal."""
    text = str(text).strip()
    if "/" in text:
        p, q = text.split("/")
        return int(p), int(q)
    negative = text.startswith("-")
    whole, _, frac = text.lstrip("-").partition(".")
    num = int(whole or "0") * 10 ** len(frac) + int(frac or "0")
    return (-num if negative else num), 10 ** len(frac)


def _round3(text: str) -> str:
    """Exact half-even rounding to 3 decimals: 1/24 -> 0.042, 11/240 -> 0.046."""
    num, den = _ratio(text)
    q, r = divmod(num * 1000, den)
    if 2 * r > den or (2 * r == den and q % 2 == 1):
        q += 1
    sign, q = ("-" if q < 0 else ""), abs(q)
    return f"{sign}{q // 1000}.{q % 1000:03d}"


def cost_line(a: ActionFact) -> str | None:
    """OUT-E E4 Cost line (Optimize cost row): the stored cost check of the Action's current outcome, read as stored."""
    cc = a.cost_check
    if cc is None:
        return COST_NOT_YET if a.verification_state in FINAL_VERIFICATION else None
    if cc.get("state") == "MODELLED_IMPROVEMENT":
        if a.verification_state != "VERIFIED":
            return COST_NOT_CREDITED
        return COST_CHANGE.format(amount=per_kwh_amount(cc), currency=cc.get("currency") or "")
    if cc.get("state") == "MODELLED_NO_IMPROVEMENT":
        return COST_NO_CHANGE
    words = COST_REASON_WORDS.get(cc.get("reason") or "")
    return COST_NOT_CALCULATED.format(words=words) if words else COST_NOT_YET


def trial_line(a: ActionFact, objective: ObjectiveFact | None) -> str | None:
    """OUT-E E4 before/after line: the row's MG-2 objective (zero target only, R593) judged on the trial's two stored
    hours; attributed to the trial only when its verification passed."""
    hours = a.trial_hours or {}
    before, after = hours.get("before_seconds"), hours.get("after_seconds")
    if objective is None or not objective.target_is_zero or before is None or after is None:
        return None
    b, l = (judge(objective, Reading(s / 60, True, None)) for s in (before, after))  # zero target: sign only
    if b not in TRIAL_VERDICT or l not in TRIAL_VERDICT:
        return None
    label = OUTCOME_BY_KEY[objective.outcome_key].label
    if a.verification_state == "VERIFIED":
        return TRIAL_ATTRIBUTED.format(label=label, before=TRIAL_VERDICT[b], after=TRIAL_VERDICT[l])
    if b != l:
        return TRIAL_NOT_ATTRIBUTED
    return TRIAL_UNCHANGED.format(label=label, verdict=TRIAL_VERDICT[b])


def action_detail(a: ActionFact, cat: str, facts: SiteFacts) -> str | None:
    """The Earlier ACT entry's `detail` in a MOVES row: the parts that apply, joined by " · "; None when none."""
    objective = next((o for o in facts.objectives if o.measure_key == TRIAL_MEASURE
                      and OUTCOME_BY_KEY[o.outcome_key].category == cat), None)
    parts = [cost_line(a) if cat == "OPTIMIZE_COST" else None, trial_line(a, objective)]
    return " · ".join(p for p in parts if p) or None


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

def objective_verdict(o: ObjectiveFact, readings: Mapping[str, Reading], settled: Mapping[str, bool]) -> str | None:
    """OUT-D U4: MET | MISSED | NOT_JUDGED for a settled outcome; None when the outcome is not settled."""
    if not settled.get(o.outcome_key, False):
        return None
    return judge(o, readings.get(o.outcome_key))


def objective_verdicts(facts: SiteFacts) -> dict[str, str | None]:
    """Per declared outcome of the Site, its verdict (`objective_verdict`)."""
    return {f.outcome_key: objective_verdict(f, facts.readings, facts.settled) for f in facts.objectives}


def objective_contributor(o: ObjectiveFact, reading: Reading | None, verdict: str | None) -> Contributor:
    """The "Declared objective" line: target sentence · actual (target only without an actual), verdict chip."""
    actual = None if reading is None else reading.actual_text
    return Contributor(f"declared_objective:{o.outcome_key}", CONTRIBUTOR_LABEL,
                       f"{o.target_text} · {actual}" if actual else o.target_text,
                       dict(VERDICT_CHIP[verdict or NOT_JUDGED]))


def objectives_wire(facts: SiteFacts) -> list[dict[str, Any]]:
    """The board's top-level `objectives` list. Verdict codes are wire data and never rendered."""
    verdicts = objective_verdicts(facts)
    return [{"outcome_key": f.outcome_key, "outcome_label": OUTCOME_BY_KEY[f.outcome_key].label, "source": f.source,
             "revision_id": f.revision_id, "source_note": f.source_note, "verdict": verdicts[f.outcome_key]}
            for f in facts.objectives]


BASIS_REFRESHED = "BASIS_REFRESHED"


def refresh_chain(revisions: Sequence[Mapping] | None, origin_id: str, shown_id: str) -> bool:
    """True iff every revision after the origin up to and including the shown one is BASIS_REFRESHED with the
    origin's lifecycle and episode bounds. `revisions` = history rows in revision_no order (every page).
    D-2026-10-31-board-action-refresh-lineage; revisions after the shown one are never read."""
    if not revisions:
        return False
    by_id = {str(r.get("id")): r for r in revisions}
    o, s = by_id.get(str(origin_id)), by_id.get(str(shown_id))
    if o is None or s is None:
        return False
    o_no, s_no = int(o["revision_no"]), int(s["revision_no"])
    if o_no >= s_no:
        return False
    between = sorted((r for r in revisions if o_no < int(r["revision_no"]) <= s_no),
                     key=lambda r: int(r["revision_no"]))
    if [int(r["revision_no"]) for r in between] != list(range(o_no + 1, s_no + 1)):
        return False
    o_ep = o.get("episode") or {}
    for r in between:
        ep = r.get("episode") or {}
        if (r.get("transition") != BASIS_REFRESHED or r.get("lifecycle") != o.get("lifecycle")
                or ep.get("start") != o_ep.get("start") or ep.get("end") != o_ep.get("end")):
            return False
    return True


def assemble(facts: SiteFacts) -> list[dict[str, Any]]:
    """The four board rows in canonical category order (§B.1 row shape)."""
    domain, code = facts.domain, facts.site_code
    roles = {f.finding_id: _Roles(finding_signal_key(f.mechanism), domain) for f in facts.findings}
    by_id = {f.finding_id: f for f in facts.findings}
    mini_actions = [a for a in facts.actions if not a.is_domain]

    def linked_actions(f: FindingFact) -> list[ActionFact]:
        """Exact revision, or a basis-only refresh chain (D-2026-10-31-board-action-refresh-lineage)."""
        return [a for a in mini_actions if a.origin_finding_id == f.finding_id
                and (a.origin_revision_id == f.revision_id or a.origin_revision_id in f.refreshed_from)]

    # status signals
    signals: list[Signal] = []
    for f in facts.findings:
        if not f.in_window:
            continue
        applied = any(a.applied for a in linked_actions(f))
        for i, key in enumerate(roles[f.finding_id].moves):
            signals.append(Signal(FINDING, key, i == 0, f.open, applied, None, f.finding_id))
    sig_roles = {s.signal_key: _Roles(s.signal_key, domain) for s in facts.signals_extra}
    for s in facts.signals_extra:
        if not s.open:
            continue
        kind = SIGNAL_OPPORTUNITY if s.kind == "OPPORTUNITY" else EVIDENCE_GAP
        for i, key in enumerate(sig_roles[s.signal_key].moves):
            signals.append(Signal(kind, key, i == 0, True, False, None, s.signal_key))
    warn_roles = [(w, _WarningRoles(w)) for w in facts.warnings]
    for w, r in warn_roles:  # C: a warning sets status through its MOVES outcomes only
        for i, key in enumerate(r.moves):
            signals.append(Signal(WARNING, key, i == 0, True, False, w.status_effect, w.key))

    open_findings = sorted((f for f in facts.findings if f.open and f.in_window),
                           key=lambda f: (f.title, f.finding_id))
    rows = [_row(facts, cat, signals, roles, by_id, open_findings, sig_roles, linked_actions, warn_roles)
            for cat in CATEGORIES]
    return rows


def _row(facts: SiteFacts, cat: str, signals: list[Signal], roles: dict[str, _Roles], by_id: dict[str, FindingFact],
         open_findings: list[FindingFact], sig_roles: dict[str, _Roles], linked_actions,
         warn_roles: Sequence[tuple[Warning, _WarningRoles]] = ()) -> dict[str, Any]:
    domain, code = facts.domain, facts.site_code
    outcomes: list[SiteOutcome] = [o for o in SITE_OUTCOMES if o.domain == domain and o.category == cat]
    declared = {f.outcome_key: f for f in facts.objectives}
    verdicts = objective_verdicts(facts)
    states = []
    for o in outcomes:
        st, reason = outcome_state(o, settled=bool(facts.settled.get(o.key, False)), signals=signals,
                                   readiness=facts.readiness, objective=verdicts.get(o.key),
                                   objectives_ok=facts.objectives_ok)
        states.append((o, st, reason))
    # OUT-D U4: one "Declared objective" line per objective of this row's outcomes, after the domain contributors,
    # in catalogue order. A not-measured outcome shows none (R583).
    objective_lines = [objective_contributor(declared[o.key], facts.readings.get(o.key), verdicts.get(o.key))
                       for o, st, _ in states if o.key in declared and st != NOT_MEASURED]
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
        if (domain, cat) == (EV, "OPTIMIZE_COST") and facts.headline_money.get("GROW_REVENUE") is None:
            row["not_measured_text"] = ROW_NOT_MEASURED_EV_COST_UNPRICED  # POLISH §1.6: no priced EV tariff
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
    for role in ("MOVES", "CHECKED"):  # C: warnings last, MOVES then CHECKED, in `evaluate` order
        for w, r in warn_roles:
            if cat in (r.move_cats if role == "MOVES" else r.checked_cats):
                issues.append({"kind": w.badge, "role": role, "text": w.title, "href": w.href, "ref": w.key})
    repeat_cats: dict[str, set[str]] = {}
    for w, r in warn_roles:
        if w.kind == REPEATED:
            for cid in w.visit_ids:
                repeat_cats.setdefault(cid, set()).update(r.move_cats)

    # Already in hand and Earlier interventions (B-Q18).
    in_hand: list[dict[str, Any]] = []
    earlier: list[dict[str, Any]] = []
    for a in sorted(facts.actions, key=lambda a: (a.code or "", a.action_id)):
        if a.origin_finding_id is None:
            continue
        origin = by_id.get(a.origin_finding_id)
        suffix = "" if origin is not None else unresolved_suffix(facts)
        r = roles[origin.finding_id] if origin is not None else None
        move_cats = r.move_cats if r is not None else ["PROTECT_ASSET"]
        result = earlier_result_for_action(a)
        if result is not None:
            if cat in move_cats:
                earlier.append({"text": _item_text(a.code, a.title), "href": a.href, "result_label": result + suffix,
                                "detail": action_detail(a, cat, facts)})
            elif r is not None and cat in r.checked_cats:
                names = r.checked_in(cat, exclude_unmeasured=MUST_NOT_HARM_EXCLUDES_UNMEASURED)
                if names:
                    earlier.append({"text": f"{join_names(names)} checked as safeguards in {_action_name(a)}",
                                    "href": a.verification_href or a.href, "result_label": result, "detail": None})
        elif a.open and cat in move_cats:
            label = "Open" if a.is_domain else WORKFLOW_IN_HAND.get(a.workflow_label or "", a.workflow_label or "Open")
            in_hand.append({"text": _item_text(a.code, a.title), "href": a.href, "state_label": label + suffix})

    for case in sorted(facts.cases, key=lambda c: (c.code or "", c.case_id)):
        cats, suffix = _case_placement(case, by_id, roles, unresolved_suffix(facts))
        if cat not in cats | repeat_cats.get(case.case_id, set()):
            continue
        if case.state not in CLOSED_CASE_STATES:
            label = _case_label(case) + suffix
            in_hand.append({"text": _item_text(case.code, case.title), "href": case.href, "state_label": label})
    for case in sorted(facts.cases, key=lambda c: (c.occurred_at is None, c.occurred_at, c.case_id)):
        cats, suffix = _case_placement(case, by_id, roles, unresolved_suffix(facts))
        result = earlier_result_for_case(case, facts.cases)
        if cat in cats | repeat_cats.get(case.case_id, set()) and result is not None:
            earlier.append({"text": _item_text(case.code, case.title), "href": case.href,
                            "result_label": result + (suffix if suffix in UNRESOLVED_SUFFIXES else ""), "detail": None})

    if cat == "PROTECT_ASSET":
        cue = {w.subject: w.kind for w in facts.warnings if w.kind in PLAN_CUE_LABEL}
        for p in sorted(facts.plans, key=lambda p: (p.code or "", p.plan_id)):
            if p.state in ("DRAFT", "ACTIVE"):
                label = PLAN_CUE_LABEL[cue[p.plan_id]] if p.plan_id in cue else _plan_label(p, facts.date_suffix)
                in_hand.append({"text": _item_text(p.code, p.title), "href": p.href, "state_label": label})

    # Must not harm (B-Q19, addendum 1): only where a mini Action verification exists.
    must_not_harm = None
    for f in sorted(moves_here, key=lambda f: (f.title, f.finding_id)):
        checks = [a for a in linked_actions(f) if a.verification_state not in (None, NO_PLAN)]
        names = roles[f.finding_id].checked_outside(cat, exclude_unmeasured=MUST_NOT_HARM_EXCLUDES_UNMEASURED)
        if checks and names:
            a = checks[0]
            must_not_harm = {"text": f"{join_names(names)} are checked as safeguards when {_action_name(a)} is "
                                     "verified; a gain that harms them does not count", "href": a.verification_href}
            break
    if must_not_harm is None:  # C: a repeat-visit warning moving this row, checked against outcomes elsewhere
        for w, r in warn_roles:
            names = r.checked_outside(cat)
            if w.kind == REPEATED and cat in r.move_cats and names:
                finding_href = next((x["href"] for x in w.evidence_refs if x["kind"] == "FINDING"), None)
                must_not_harm = {"text": join_names(names) + REPAIR_MUST_NOT_HARM, "href": finding_href}
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
        "contributors": [_contributor(c) for c in (*facts.contributors.get(cat, ()), *objective_lines)],
        "issues": issues,
        "options": [{"text": o.text, "href": o.href} for o in facts.options.get(cat, ())],
        "in_hand": in_hand, "earlier": earlier,
        "earlier_empty_text": None if earlier else (
            EARLIER_EMPTY_OPEN if any(f.open and f.in_window for f in moves_here) else EARLIER_EMPTY_NONE),
    })
    return row


def _case_placement(case: CaseFact, by_id: dict[str, FindingFact], roles: dict[str, _Roles],
                    unresolved: str = OUTSIDE_VIEW_SUFFIX) -> tuple[set[str], str]:
    """Categories and state-label suffix for a case. No link: PROTECT_ASSET, "not linked". Links that resolve: their
    Findings' MOVES categories. Links none of which resolve: kept under PROTECT_ASSET with the outside-view suffix
    (addendum 2 item 4, replacing review M1's assertion); the composer records them via `unresolved_links`."""
    if not case.finding_ids:
        return {"PROTECT_ASSET"}, NOT_LINKED_SUFFIX
    linked = [by_id[fid] for fid in case.finding_ids if fid in by_id]
    if not linked:
        return {"PROTECT_ASSET"}, unresolved
    return {c for f in linked for c in roles[f.finding_id].move_cats}, ""


def _finding_issue(f: FindingFact, role: str, text: str) -> dict[str, Any]:
    return {"kind": "FINDING", "role": role, "text": text, "href": f.href,
            "ref": {"finding_id": f.finding_id, "finding_revision_id": f.revision_id}}


def _contributor(c: Contributor) -> dict[str, Any]:
    return {"key": c.key, "label": c.label, "text": c.text,
            "confidence": None if c.confidence is None else dict(c.confidence), "href": c.href}
