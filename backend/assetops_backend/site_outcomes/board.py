"""OUT-B1: pure assembly of the Site outcome board (build spec §B.2; rulings B-Q14/Q18/Q19/Q20/Q28, addenda 1-2).

It imports only `outcomes/`. The domain composer (B2/B3) reads the ports and hands this module a `SiteFacts`. This
module attributes Findings, signals, Actions, cases and plans to the four category rows. It sets each outcome's state
and rolls each row up. It writes no storage and formats no money (B-Q14)."""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import date
from typing import Any

from assetops_backend.chain import refs
from assetops_backend.chain.vocabulary import days_line as node_days_line, node_text, provenance_suffix
from assetops_backend.outcomes.display_code import display_code
from assetops_backend.outcomes.catalogue import (
    CATEGORIES, CATEGORY_DEFINITION, CATEGORY_ICON, CATEGORY_LABEL, COLD, EV, MINI, OUTCOME_BY_KEY, SITE_OUTCOMES,
    ROW_NOT_MEASURED_EV_COST_UNPRICED, SiteOutcome, row_not_measured)
from assetops_backend.outcomes.objectives import (
    CONTRIBUTOR_LABEL, MEASURES, MET, MISSED, NOT_JUDGED, VERDICT_CHIP, ObjectiveFact, Reading, judge, judge_month)
from assetops_backend.outcomes.outcome_map import ENTRIES, finding_signal_key, kpi_record, outcome_roles
from assetops_backend.outcomes.status import (
    EVIDENCE_GAP, FINDING, NO_OBJECTIVE, NOT_MEASURED, ON_TRACK, OPPORTUNITY, SIGNAL_OPPORTUNITY, STATE_LABEL, STATE_TONE, WARNING, Signal,
    outcome_state, roll_up)
from assetops_backend.outcomes.warnings import PLAN_DUE_SOON, PLAN_OVERDUE, REPEATED, Warning

OPEN_LIFECYCLES = ("SUPPORTED", "UNCONFIRMED")  # Portfolio membership rule (estate/portfolio.py:38)
CLOSED_CASE_STATES = ("COMPLETED", "CLOSED", "CANCELLED")
MAINTENANCE_REQUEST, INCIDENT = "MAINTENANCE_REQUEST", "INCIDENT"
NO_PLAN = "NO_PLAN"

SAFEGUARD_SUFFIX = " · checked here as a safeguard"  # mock outcomes.js:71
POTENTIAL_LABEL = "Opportunity"  # WALK1-3b §A2.1: the second header chip (R690)
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
WORKFLOW_IN_HAND = {"No action agreed yet": "Plan ready", "Outcome pending": "Awaiting verification"}
CASE_STATE_LABEL = {"OPEN": "Open", "IN_PROGRESS": "In progress", "ASSIGNED": "Assigned"}

#: Earlier interventions result labels for a mini Action, by verification state (§B.2 table). NO_PLAN / None: not listed.
#: CH-5a2b B7 (DS-R1): "Verified" takes `provenance_suffix` of the verified outcome's source class (`action_result`).
ACTION_RESULT = {"VERIFIED": "Verified", "INEFFECTIVE": "Did not fix it",
                 "INCONCLUSIVE": "Not determined", "PENDING": "Pending", "REASSESSMENT_PENDING": "Pending"}
REQUEST_REPEATED, REQUEST_UNVERIFIED = "Did not fix it", "Not yet verified"
#: OUT-E E4 (build sheet OUT-E section 4): the Earlier entry's cost-check and before/after detail lines.
#: POLISH §3.1 / Addendum 6 Q6: plain read-side copy (the stored `trial_fuel_comparison.LABEL` is unchanged).
COST_PREFIX = "Estimated effect of the trial (not money saved): "
COST_CHANGE = COST_PREFIX + "{amount} {currency} less supply cost per kWh."
COST_NO_CHANGE = COST_PREFIX + "no lower supply cost per kWh."
COST_NOT_CALCULATED = "Modelled change not calculated: {words}"
COST_NOT_YET = "Not calculated yet"
#: POLISH D-2 (OUT-E L4): a modelled improvement is credited only to a VERIFIED trial.
COST_NOT_CREDITED = "The trial did not fix the problem, so no cost change is credited to it"
#: CH-3 §5: the verified claim's scope (I-11), appended to the attributed trial line; the verdict is unchanged.
TRIAL_SCOPE = " · checked over {start}–{end} on {day}"
#: CH-3 §5: the four thread lines (row subline of the row where the Finding is the primary MOVES issue).
THREAD_BEFORE = "Before the change on {e}"
THREAD_AFTER_JUDGED = " · after the change: {state_label} from {day}"
THREAD_AFTER_NOT_JUDGED = " · after the change: not judged yet, no fully checked day since {e}"
THREAD_MONITORING = "Fix verified, monitoring ({code}) · {k} more fully checked days to close"
THREAD_CLOSED = "Fix verified and closed ({code}) · no return in {n} fully checked days"
THREAD_RECURRED = "Came back on {day} after the fix ({code})"
#: MB-1-R Q3: the thread line of an opportunity thread (the mill): a change to use spare solar, not a fix of a fault;
#: "checked and working" is the thread page's own word for RESOLVED_MONITORING.
OPP_THREAD_MONITORING = "Change checked and working ({code}) · {k} more fully checked days to close"
OPP_THREAD_CLOSED = "Change checked and closed ({code}) · spare solar not seen again in {n} fully checked days"
OPP_THREAD_SEEN_AGAIN = "Spare solar seen again on {day} after the change ({code})"
TRIAL_ATTRIBUTED = "Goal before the trial: {before}; after: {after}."
TRIAL_NOT_ATTRIBUTED = "Status changed; not attributed"
TRIAL_UNCHANGED = "{label}: {verdict} before and after the trial"
TRIAL_VERDICT = {MET: "met", MISSED: "missed"}
COST_REASON_WORDS = {
    "OUTCOME_INCONCLUSIVE": "the trial result is not determined",
    "WINDOW_INCOMPLETE": "a comparison hour is incomplete",
    "NOT_COMPARABLE": "the two hours are not comparable",
    "SOURCE_NOT_COHERENT": "the two hours come from different sources",
    "EVIDENCE_REPLAY_MISMATCH": "the readings changed after the result was recorded",
    "GENERATOR_KWH_UNKNOWN": "generator energy is not known for one or both hours",
    "ZERO_DEMAND": "an hour had no demand",
    "SFC_MISSING": "the generator fuel rate is not recorded",
    "SFC_DIFFERS": "the generator fuel rate differs between the hours",
    # FUEL-1 A2 (A2-R1): words for the two /2 reasons
    "IDLE_SECONDS_UNKNOWN": "the generator's idle time is not known for one or both hours",
    "NO_LOAD_RATE_DIFFERS": "the generator's idle fuel rate differs between the hours",
    "PRICE_MISSING": "no diesel price covers both hours",
    "PRICE_BASIS_DIFFERS": "the two hours were priced from different diesel price records",
}
FINAL_VERIFICATION = ("VERIFIED", "INEFFECTIVE", "INCONCLUSIVE")
TRIAL_MEASURE = "avoidable_generator_minutes"  # the MG-2 objective (R593: before/after only on a zero target)
#: C: plan state labels when the plan's due cue fires (the plan itself stays DRAFT; register R08, R10).
PLAN_CUE_LABEL = {PLAN_OVERDUE: "Overdue", PLAN_DUE_SOON: "Due soon"}
REPAIR_MUST_NOT_HARM = ": a repair counts only when the fault it answers stops"

#: Evidence link per (domain, category); None where the row is not measured (§B.2 table).
EVIDENCE_LINK: dict[tuple[str, str], tuple[str, Callable[[str], dict[str, Any]]] | None] = {
    (MINI, "GROW_REVENUE"): ("Renewable evidence", lambda c: refs.evidence_ref(c, "renewable")),
    (MINI, "OPTIMIZE_COST"): ("Dispatch evidence", lambda c: refs.evidence_ref(c, "dispatch")),
    (MINI, "PROTECT_ASSET"): ("Battery evidence", lambda c: refs.site_ref(c, "health")),
    (MINI, "ASSURE_PERFORMANCE"): ("Evidence overview", lambda c: refs.evidence_ref(c)),
    (COLD, "GROW_REVENUE"): None,
    (COLD, "OPTIMIZE_COST"): ("Financial bridge", lambda c: refs.site_ref(c, "financials")),
    (COLD, "PROTECT_ASSET"): ("Cold-room evidence", lambda c: refs.evidence_ref(c)),
    (COLD, "ASSURE_PERFORMANCE"): ("Evidence overview", lambda c: refs.evidence_ref(c)),
    (EV, "GROW_REVENUE"): ("Financial bridge", lambda c: refs.site_ref(c, "ev_financials")),
    (EV, "OPTIMIZE_COST"): None,
    (EV, "PROTECT_ASSET"): ("Depot evidence", lambda c: refs.site_ref(c, "ev_evidence")),
    (EV, "ASSURE_PERFORMANCE"): ("Evidence overview", lambda c: refs.site_ref(c, "ev_evidence")),
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
    link_ref: Mapping[str, Any] | None  # CH-5a2a: a `chain.refs` Ref
    asset_id: str | None = None
    confidence_label: str | None = None
    #: Addendum 2 item 4: False for a Finding read only to resolve a link (outside the overview day). Such a
    #: Finding places linked work but drives no signal, issue or headline.
    in_window: bool = True
    #: CH3-R M3: the episode intersects the board's 31-day work window (mini; the thread-level line reads it).
    in_work_window: bool = False
    #: CH-2 §5.3: the Finding's thread `{id, occurrence_no, occurrences}`; None when it has no thread.
    #: CH-3 adds `segment_no`, `state` and `state_effective_day` on the board day as of its `known_at`.
    thread: Mapping[str, Any] | None = None
    #: CH-3: the read-time thread view (`chain/lifecycle.thread_view`); never on the wire.
    lifecycle_view: Mapping[str, Any] | None = None

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
    link_ref: Mapping[str, Any] | None
    # Additions recorded in the packet (B1 deviation 2): the inputs the §B.2 labels and links need.
    workflow_label: str | None = None  # mini: estate/portfolio.py:137 text
    verification_ref: Mapping[str, Any] | None = None  # ACTION Ref, view verification, event_id
    is_domain: bool = False            # cold/EV domain Action: in hand only, never applied
    # OUT-E E4: the verification summary's stored cost check and trial hours of the current outcome (last, defaulted)
    cost_check: Mapping[str, Any] | None = None   # {state, reason, nominal, upper, currency, recorded_at}
    trial_hours: Mapping[str, Any] | None = None  # {before_seconds, after_seconds}
    thread_id: str | None = None                  # CH-2: the Action's `chain_action.thread_id`; None = not linked
    segment_no: int | None = None                 # CH-3 §3: the Action's thread segment; None = not linked
    source_class: str | None = None               # CH5a2-R R2: the verified outcome's stored source class


@dataclass(frozen=True)
class OpportunityActionFact:
    """MB-1-R: an opportunity-origin domain Action on a mini board (the mill); never in `actions`, so In hand and
    Earlier are unchanged (R4)."""
    action_id: str
    code: str | None
    thread_id: str
    outcome: str | None                 # VERIFIED | INEFFECTIVE | INCONCLUSIVE known by the cutoff; None = not judged
    verdict_ref: Mapping[str, Any]      # the DOMAIN_VERDICT Ref (`site_chain.action_wire_ref`)
    #: MB-1b (MB-1-R §3.3): the thread's `lifecycle.thread_view` on the board day (None = no thread line), this
    #: Action's segment (`site_chain.actions_of`), the thread's first MOVES category, and whether the board's window
    #: sees every fully checked day since the verified day (False = no MONITORING count is shown).
    view: Mapping[str, Any] | None = None
    action_segment: int | None = None
    category: str | None = None
    count_known: bool = True
    source_class: str | None = None     # WD-1m-R: example-data class over the verdict's used days (None = none found)


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
    link_ref: Mapping[str, Any] | None


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
    link_ref: Mapping[str, Any] | None
    due_at: Any = None                 # C: the UTC instant of `next_due_at` (compared only)


#: Issue kind of each non-Finding signal (§B.2): headroom is an opportunity, the evidence gap is a gap.
def _link(ref: Mapping[str, Any] | None) -> dict[str, Any]:
    """CH5a2-R4(a): a linked item's `href` (kept until CH-7) built from its sibling `link_ref`, so they cannot
    disagree. No ref is no link."""
    return {"href": refs.href_for(ref), "link_ref": None if ref is None else dict(ref)}


SIGNAL_ISSUE_KIND = {"SIGNAL:PRODUCTIVE_USE_HEADROOM": "OPPORTUNITY", "SIGNAL:EVIDENCE_GAP": "EVIDENCE_GAP"}


@dataclass(frozen=True)
class SignalFact:
    """A non-Finding `SIGNAL:*` fact (B1 deviation 3). Its issue kind is derived from `signal_key`."""
    signal_key: str                    # a SIGNAL_ISSUE_KIND key
    open: bool
    text: str
    link_ref: Mapping[str, Any] | None = None
    ref: Mapping[str, Any] | None = None   # CH-4 §2.3: the OPPORTUNITY issue's study and thread

    @property
    def kind(self) -> str:
        return SIGNAL_ISSUE_KIND[self.signal_key]


@dataclass(frozen=True)
class Contributor:
    key: str
    label: str
    text: str
    confidence: Mapping[str, str] | None = None
    link_ref: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class Option:
    text: str
    link_ref: Mapping[str, Any] | None = None


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
    #: WALK1-3b §A2.3: per category, the contributor key the "Declared objective" lines follow; absent = after all.
    objective_after: Mapping[str, str] = field(default_factory=dict)
    #: CH-3 §5: the board's Site-local day and cutoff (the thread state is read on `day` as of `known_at`).
    day: Any = None        # datetime.date | None (this module imports only outcomes/ and these stdlib modules)
    known_at: Any = None   # datetime | None
    #: CH6a3-R2 M4: True only when the board window is exactly one Site-local day (`day` may then date a days line).
    one_day: bool = False
    #: CH6b1-R4 SPAN: the Site-local `(first, last)` days of the window the node claims sit under; a claim names its
    #: span in the days line only when the span differs from this.
    window_span: Any = None
    #: CH3-R M3: the board's 31-day work window `(work_lo, end)` (mini); None = no thread-level line.
    work_window: Any = None
    #: CH-6a3 §A5: per outcome key, the OutcomeEvaluator's node claims as JSON {"kpi", "earnings", "potential"}.
    nodes: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    #: CH-6a3: whether the EV window is priced at a stored tariff. None = not told (the Grow money decides, as before).
    #: The Grow money is now the earnings claim, which stays null while the days are not all known, so it can no
    #: longer stand for "a tariff exists".
    ev_priced: bool | None = None
    #: MB-1-R §2.3: the board's opportunity-origin domain Actions (the mill), apart from `actions` (R4).
    opportunity_actions: tuple[OpportunityActionFact, ...] = ()
    #: PV-1-R §3: the Assure row's verified-value entries (one per verified result with money, never added); mini only.
    verified_values: tuple[Mapping[str, Any], ...] = ()


# ---------------------------------------------------------------- helpers

NODE_KEYS = ("kpi", "earnings", "potential")


def grow_headline(nodes: Mapping[str, Any] | None) -> str | None:
    """§B3 / CH6b2-R Q6: the Grow row's `ob-val`: the earnings text when its basis is not NOT_KNOWN, else the
    potential text (its first line) when a potential was found, else the target text; None without nodes. The three
    stay labelled parts in the row body (I-07), never merged into one sentence."""
    if not nodes:
        return None
    earnings, potential, kpi = (nodes.get(k) or {} for k in ("earnings", "potential", "kpi"))
    if earnings.get("text") and earnings.get("basis") != "NOT_KNOWN":
        return earnings["text"]
    if potential.get("text") and potential["text"] != node_text("potential.none"):
        return str(potential["text"]).split("\n")[0]
    return kpi.get("text") or None


def row_nodes(facts: "SiteFacts", keys: Sequence[str], lead_key: str, row_state: str,
              states: Sequence[tuple[str, str]]) -> dict[str, Any]:
    """CH-6a3 §A5 / CH6a3-R Q1: the row's `nodes`, `days_line` and R7 `target_note`. `earnings` and `potential` are
    the first row outcome (catalogue order) holding that claim; `kpi` is the lead outcome's claim when it has an
    objective, else the first outcome with one, else the outcome with a `kpi` record ("No target set yet"). No node
    record and no objective: every node null. Each node carries its own `days_line` (no row-level line); an absent node is server-filled."""
    per = facts.nodes
    declared = {o.outcome_key for o in facts.objectives}

    def first(node: str) -> Any:
        return next((per[k][node] for k in keys if (per.get(k) or {}).get(node) is not None), None)

    kpi_key = (lead_key if lead_key in declared else next((k for k in keys if k in declared), None)) or next(
        (k for k in keys if kpi_record(k) is not None), None)
    nodes = {"kpi": None if kpi_key is None else (per.get(kpi_key) or {}).get("kpi"),
             "earnings": first("earnings"), "potential": first("potential")}
    day = facts.day if facts.one_day else None   # M4: a "No readings on {day}" line only for a one-day window
    if all(nodes[k] is None for k in NODE_KEYS):
        nodes = {k: None for k in NODE_KEYS}
    else:   # CH6a3-R2b H4: all three parts always present, each with its own days line from its own days
        fill = {"kpi": ("verdict.none", node_text("target.none"), node_text("target.days_none")),
                "potential": ("potential.none", node_text("potential.none"), None),
                "earnings": ("money.not_known", node_text("money.not_known"), None)}
        out: dict[str, Any] = {}
        for k in NODE_KEYS:
            n = nodes[k]
            if n is None:
                key, text, line = fill[k]
                out[k] = {"key": key, "value": None, "basis": "NOT_KNOWN", "days": None, "text": text, "days_line": line}
            else:
                sp = n.get("span")
                span = None if not sp else (date.fromisoformat(sp["first"]), date.fromisoformat(sp["last"]))
                line = node_days_line(n.get("days"), day, span, getattr(facts, "window_span", None))
                if line is None and k == "kpi" and n.get("value") is None and n.get("text") == node_text("target.none"):
                    line = node_text("target.days_none")
                out[k] = {**n, "days_line": line}
        nodes = out
    note = None
    if row_state == ON_TRACK and any(st == NO_OBJECTIVE for _, st in states):
        note = node_text("row.target_note", k=sum(1 for k in keys if k in declared), m=len(keys))
    return {"nodes": nodes, "target_note": note}


def join_names(labels: Sequence[str]) -> str:
    """"A and B" / "A, B and C", sentence-cased on the first letter only (§B.2)."""
    parts = [labels[0]] + [lab[:1].lower() + lab[1:] for lab in labels[1:]]
    text = parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]
    return text[:1].upper() + text[1:]


def _item_text(code: str | None, title: str) -> str:
    """"{code} · {title}"; an item with no stored title (every mini Action, addendum 2 item 1) reads its code.
    POLISH §3: the code is shown in its display form."""
    code = display_code(code)
    if code and title:
        return f"{code} · {title}"
    return code or title


def _action_name(a: "ActionFact") -> str:
    return display_code(a.code) or a.title


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


def action_result(action: ActionFact, state: str | None) -> str | None:
    """The Earlier interventions result label of `state`; VERIFIED reads "Verified{provenance_suffix}" (B7)."""
    text = ACTION_RESULT.get(state)  # type: ignore[arg-type]
    return f"{text}{provenance_suffix(action.source_class)}" if state == "VERIFIED" and text else text


def earlier_result_for_action(action: ActionFact) -> str | None:
    """Result label for a mini Action in Earlier interventions, or None when it is not listed (B-Q18)."""
    if action.is_domain or not action.applied:
        return None
    return action_result(action, action.verification_state or NO_PLAN)


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
        base, scope = TRIAL_ATTRIBUTED.format(label=label, before=TRIAL_VERDICT[b], after=TRIAL_VERDICT[l]), trial_scope(hours)
        return base[:-1] + scope + "." if scope and base.endswith(".") else base + scope
    if b != l:
        return TRIAL_NOT_ATTRIBUTED
    return TRIAL_UNCHANGED.format(label=label, verdict=TRIAL_VERDICT[b])


def trial_scope(hours: Mapping[str, Any]) -> str:
    """CH-3 §5 (I-11): the later window the verification judged, in Site-local time (the composer's
    `later_local` `{start, end, day}`); "" when it is not read."""
    local = hours.get("later_local")
    if not local:
        return ""
    return TRIAL_SCOPE.format(start=local["start"], end=local["end"], day=_short_day(local["day"]))


def action_detail(a: ActionFact, cat: str, facts: SiteFacts) -> str | None:
    """The Earlier ACT entry's `detail` in a MOVES row: the parts that apply, None when none. POLISH §3.1 (PA-2a review
    L1): a part that ends a sentence is followed by a single space; otherwise the parts are joined by " · "."""
    objective = next((o for o in facts.objectives if o.measure_key == TRIAL_MEASURE
                      and OUTCOME_BY_KEY[o.outcome_key].category == cat), None)
    parts = [cost_line(a) if cat == "OPTIMIZE_COST" else None, trial_line(a, objective)]
    out = ""
    for p in (x for x in parts if x):
        out = p if not out else out + (" " if out.endswith(".") else " · ") + p
    return out or None


#: POLISH Addendum 12 Q1: the stored kind of a board work item (cases carry theirs: INCIDENT | MAINTENANCE_REQUEST).
PLAN_KIND = "PLAN"


def _case_wire(case: CaseFact) -> dict[str, Any]:
    """POLISH Addendum 12 Q1: a case item's stored `kind` and its `occurred_at` (ISO UTC; None when not an instant)."""
    at = case.occurred_at
    if hasattr(at, "utcoffset") and hasattr(at, "isoformat"):  # stored instants are UTC (timestamptz)
        at = at.isoformat().replace("+00:00", "Z")
    elif not isinstance(at, str):
        at = None
    return {"kind": case.kind, "occurred_at": at}


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
    """OUT-D U4: MET | MISSED | NOT_JUDGED for a settled outcome; None when the outcome is not settled. A monthly
    measure is judged month to date (WALK1-3b `judge_month`)."""
    if not settled.get(o.outcome_key, False):
        return None
    measure = MEASURES.get(o.measure_key)
    return (judge_month if measure is not None and measure.monthly else judge)(o, readings.get(o.outcome_key))


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


def assemble(facts: SiteFacts) -> list[dict[str, Any]]:
    """The four board rows in canonical category order (§B.1 row shape)."""
    domain, code = facts.domain, facts.site_code
    roles = {f.finding_id: _Roles(finding_signal_key(f.mechanism), domain) for f in facts.findings}
    by_id = {f.finding_id: f for f in facts.findings}
    mini_actions = [a for a in facts.actions if not a.is_domain]

    def linked_actions(f: FindingFact) -> list[ActionFact]:
        """CH-5a1 §A4: an Action belongs to a Finding through its thread and segment (CH-2/CH-3); without a thread
        (no thread port, or a database below 0042) the exact origin revision is kept."""
        if f.thread is None:
            return [a for a in mini_actions if a.origin_finding_id == f.finding_id
                    and a.origin_revision_id == f.revision_id]
        tid, seg = f.thread.get("id"), f.thread.get("segment_no")
        return [a for a in mini_actions if a.thread_id is not None and str(a.thread_id) == str(tid)
                and seg is not None and a.segment_no == seg]

    # status signals
    signals: list[Signal] = []
    for f in facts.findings:
        if not f.in_window:
            continue
        is_open, applied = finding_signal_state(f, linked_actions(f))
        for i, key in enumerate(roles[f.finding_id].moves):
            signals.append(Signal(FINDING, key, i == 0, is_open, applied, None, f.finding_id))
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


def finding_signal_state(f: FindingFact, linked: Sequence[ActionFact]) -> tuple[bool, bool]:
    """(open, applied) of a Finding's signal. CH-3 §5 (DS-R1 item 3): with a thread, the thread state on the board
    day in the Finding's segment decides: applied from CHANGE_APPLIED on, and a verified fix (RESOLVED_MONITORING or
    CLOSED) gives no open signal (I-02). Without a thread (no thread port, or a database below 0042) the
    exact-revision rule is kept."""
    if f.thread is None:
        return f.open, any(a.applied for a in linked)
    # CH5a-R §A5: the thread view carries its state classes (chain/lookup.py); the board holds no state tuples.
    return f.open and not f.thread.get("verified"), bool(f.thread.get("applied"))


def _short_day(d: Any) -> str:
    return f"{d.day} {d:%b}"


def _thread_action(f: FindingFact, facts: SiteFacts, earlier: bool) -> ActionFact | None:
    """The Action of the Finding's segment (or of an earlier segment), verified first, then by code."""
    seg = (f.thread or {}).get("segment_no")
    tid = (f.thread or {}).get("id")
    pool = [a for a in facts.actions if a.thread_id is not None and a.thread_id == tid and a.segment_no is not None
            and seg is not None and (a.segment_no < seg if earlier else a.segment_no == seg)]
    pool.sort(key=lambda a: (a.verification_state != "VERIFIED", -(a.segment_no or 0), a.code or "", a.action_id))
    return pool[0] if pool else None


def thread_line(f: FindingFact, facts: SiteFacts, state_label_on: Any = None) -> str | None:
    """CH-3 §5: the one thread line that applies to a Finding on the board day, else None (the text of
    `thread_line_item`)."""
    judge = None if state_label_on is None else (lambda day: (None, state_label_on(day)))
    item = thread_line_item(f, facts, judge)
    return None if item is None else item["text"]


def _line_item(kind: str, text: str, tid: str, action_code: str | None, site_code: str, effective: Any,
               after: Any = None, remaining: int | None = None, clean: int | None = None) -> dict[str, Any]:
    """CH-5a2 B4: one structured ThreadLine (lifted unchanged from `thread_line_item` for MB-1b)."""
    return {"kind": kind, "thread_id": tid, "action_code": action_code,
            "effective_day": None if effective is None else effective.isoformat(), "after": after,
            "remaining_days": remaining, "clean_days": clean, "ref": refs.thread_ref(site_code, tid),
            "text": text}


def opportunity_line_item(o: OpportunityActionFact, facts: SiteFacts) -> dict[str, Any] | None:
    """MB-1b (MB-1-R §3.3): the Grow row's ThreadLine of an opportunity-origin domain Action (the mill) on the board
    day, else None. MOCK DEVIATION MD-FUEL-MB1-2: v69's Grow row has no thread line; the CH-3 thread line (already a
    deviation on the Optimize row) also appears on Grow for an opportunity thread, in opportunity wording."""
    d, v = facts.day, o.view
    if v is None or d is None:
        return None
    code, e, tid = display_code(o.code), v.get("change_day"), o.thread_id

    def item(kind: str, text: str, effective: Any, remaining: int | None = None,
             clean: int | None = None) -> dict[str, Any]:
        return _line_item(kind, text, tid, o.code, facts.site_code, effective, None, remaining, clean)

    if e is not None and d < e:
        return item("BEFORE_CHANGE", THREAD_BEFORE.format(e=_short_day(e)), e)
    seg, n = o.action_segment, int(v["close_after"])
    if v.get("state") == "RECURRED" and seg is not None and seg < v["segment_no"] and v.get("recurred_day") is not None:
        day = v["recurred_day"]
        return item("RECURRED", OPP_THREAD_SEEN_AGAIN.format(day=_short_day(day), code=code), day)
    if v.get("state") == "CLOSED" and seg == v["segment_no"]:
        return item("CLOSED", OPP_THREAD_CLOSED.format(code=code, n=n), e, clean=n)
    if v.get("state") == "RESOLVED_MONITORING" and seg == v["segment_no"] and o.count_known:
        r = max(0, n - int(v["checked_days"]))
        return item("MONITORING", OPP_THREAD_MONITORING.format(code=code, k=r), e, remaining=r)
    return None


def thread_line_item(f: FindingFact, facts: SiteFacts, judge: Any = None) -> dict[str, Any] | None:
    """CH-5a2 B4: the structured ThreadLine of a Finding on the board day, else None. `judge(day)` gives the row's
    `(state, state_label)` on a day after the change; `text` is the CH-3 literal, rendered exactly as before."""
    view, d = f.lifecycle_view, facts.day
    if view is None or f.thread is None or d is None:
        return None
    state, e = f.thread.get("state"), view.get("change_day")
    tid = str(f.thread.get("id"))

    def item(kind: str, text: str, a: ActionFact | None, effective: Any, after: Any = None,
             remaining: int | None = None, clean: int | None = None) -> dict[str, Any]:
        return _line_item(kind, text, tid, None if a is None else a.code, facts.site_code, effective, after,
                          remaining, clean)

    if e is not None and d < e:
        line = THREAD_BEFORE.format(e=_short_day(e))
        first = view.get("first_complete_after_change")
        judged = None if first is None or judge is None else judge(first)
        a = _thread_action(f, facts, earlier=False)
        if first is not None and judged is not None and judged[1] is not None:
            return item("BEFORE_CHANGE", line + THREAD_AFTER_JUDGED.format(state_label=judged[1], day=_short_day(first)),
                        a, e, {"state": judged[0], "day": first.isoformat()})
        return item("BEFORE_CHANGE", line + THREAD_AFTER_NOT_JUDGED.format(e=_short_day(e)), a, e)
    if state == "RECURRED":
        a = _thread_action(f, facts, earlier=True)
        day = view.get("recurred_day")
        if a is None or day is None:
            return None
        return item("RECURRED", THREAD_RECURRED.format(day=_short_day(day), code=display_code(a.code)), a, day)
    if f.thread.get("verified"):
        a = _thread_action(f, facts, earlier=False)
        if a is None:
            return None
        n = int(view.get("close_after") or 0)
        if state == "CLOSED":
            return item("CLOSED", THREAD_CLOSED.format(code=display_code(a.code), n=n), a, e, clean=n)
        k = max(0, n - int(view.get("checked_days") or 0))
        return item("MONITORING", THREAD_MONITORING.format(code=display_code(a.code), k=k), a, e, remaining=k)
    return None


def thread_line_findings(facts: SiteFacts) -> list[FindingFact]:
    """The Findings whose thread line a board shows, in (title, id) order. Every in-window Finding (CH-3 §5), and,
    CH3-R M3 (thread-level, mini boards): for a thread with no in-window Finding, its latest occurrence on the
    board when the thread's latest occurrence or an Action of it lies in the board's 31-day work window
    (`work_lo`..`end`) and its state on the board day is RESOLVED_MONITORING, CLOSED or RECURRED."""
    shown = [f for f in facts.findings if f.in_window]
    if facts.work_window is not None:
        have = {str(f.thread.get("id")) for f in shown if f.thread is not None}
        latest: dict[str, FindingFact] = {}
        for f in facts.findings:
            if f.in_window or f.thread is None or str(f.thread.get("id")) in have:
                continue
            tid = str(f.thread.get("id"))
            prior = latest.get(tid)
            if prior is None or (int(f.thread.get("occurrence_no") or 0), f.finding_id) > (
                    int(prior.thread.get("occurrence_no") or 0), prior.finding_id):  # type: ignore[union-attr]
                latest[tid] = f
        acted = {a.thread_id for a in facts.actions if a.thread_id is not None}
        for tid, f in latest.items():
            recent = f.in_work_window or tid in acted
            if recent and f.thread.get("later"):  # type: ignore[union-attr]
                shown.append(f)
    return sorted(shown, key=lambda f: (f.title, f.finding_id))


def _state_on(view: Mapping[str, Any], day: Any) -> str | None:
    last = None
    for _, state, eff in view.get("events") or ():
        if eff <= day:
            last = state
    return last


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
    keys = {o.key for o in outcomes}
    lead = OUTCOME_BY_KEY[lead_key]
    link = EVIDENCE_LINK.get((domain, cat))
    row: dict[str, Any] = {
        "category": cat, "label": CATEGORY_LABEL[cat], "definition": CATEGORY_DEFINITION[cat],
        "icon": CATEGORY_ICON[cat], "state": row_state, "state_label": STATE_LABEL[row_state],
        "tone": STATE_TONE[row_state], "lead_outcome": {"key": lead.key, "label": lead.label},
        "headline": None, "headline_money": None, "subline": None, "thread_lines": [], "not_measured_text": None,
        "counts": {"issues": 0, "in_hand": 0}, "must_not_harm": None,
        "contributors": [], "issues": [], "options": [], "in_hand": [], "earlier": [], "earlier_empty_text": None,
        "evidence_link": None if link is None else {"label": link[0], **_link(link[1](code))},
        "outcomes": [{"key": o.key, "label": o.label, "state": st, "reason": reason} for o, st, reason in states],
        "potential": None,
        **row_nodes(facts, [o.key for o in outcomes], lead_key, row_state, [(o.key, st) for o, st, _ in states]),
    }
    if cat == "GROW_REVENUE":   # CH6b2-R Q6 (§B3): the board's Grow headline, from its three parts
        row["grow_headline"] = grow_headline(row.get("nodes"))
    if cat == "ASSURE_PERFORMANCE" and facts.verified_values:   # PV-1-R §3: nodes only; the board shows no new line
        row["nodes"] = {**row["nodes"], "verified_values": [dict(v) for v in facts.verified_values]}
    if row_state == NOT_MEASURED:
        row["not_measured_text"] = row_not_measured(domain, cat, lead)
        if (domain, cat) == (EV, "OPTIMIZE_COST") and (
                facts.headline_money.get("GROW_REVENUE") is None if facts.ev_priced is None else not facts.ev_priced):
            row["not_measured_text"] = ROW_NOT_MEASURED_EV_COST_UNPRICED  # POLISH §1.6: no priced EV tariff
        return row

    moves_here = [f for f in facts.findings if cat in roles[f.finding_id].move_cats]
    checked_here = [f for f in facts.findings if cat in roles[f.finding_id].checked_cats]

    # Issues: MOVES Findings by title, signals (MOVES before CHECKED), CHECKED Findings (B-Q20).
    issues: list[dict[str, Any]] = []
    for f in open_findings:
        if f in moves_here:
            issues.append(_finding_issue(f, "MOVES", f.title, _primary(roles[f.finding_id].moves, cat)))
    open_signals = [s for s in facts.signals_extra if s.open]
    for role in ("MOVES", "CHECKED"):
        for s in open_signals:
            r = sig_roles[s.signal_key]
            if cat in (r.move_cats if role == "MOVES" else r.checked_cats):
                issues.append({"kind": s.kind, "role": role, "text": s.text, **_link(s.link_ref),
                               "ref": None if s.ref is None else dict(s.ref)})
    for f in open_findings:
        if f in checked_here:
            issues.append(_finding_issue(f, "CHECKED", f.title + SAFEGUARD_SUFFIX, False))
    for role in ("MOVES", "CHECKED"):  # C: warnings last, MOVES then CHECKED, in `evaluate` order
        for w, r in warn_roles:
            if cat in (r.move_cats if role == "MOVES" else r.checked_cats):
                issues.append({"kind": w.badge, "role": role, "text": w.title, **_link(w.link_ref), "ref": w.key})
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
        if origin is None and a.is_domain and a.thread_id is not None:
            # CH-2 §5.2 (I-09 display): a domain Action on the thread of a Finding shown on the board
            origin = next((f for f in sorted(facts.findings, key=lambda f: (not f.in_window, f.finding_id))
                           if f.thread is not None and f.thread.get("id") == a.thread_id), None)
        suffix = "" if origin is not None else unresolved_suffix(facts)
        r = roles[origin.finding_id] if origin is not None else None
        move_cats = r.move_cats if r is not None else ["PROTECT_ASSET"]
        result = earlier_result_for_action(a)
        if result is None and a.open and _earlier_segment(a, facts):
            result = action_result(a, a.verification_state or "PENDING") or ACTION_RESULT["PENDING"]  # CH-3 §3
        if result is not None:
            if cat in move_cats:
                earlier.append({"text": _item_text(a.code, a.title), **_link(a.link_ref),
                                "result_label": result + suffix,
                                "detail": action_detail(a, cat, facts)})
            elif r is not None and cat in r.checked_cats:
                names = r.checked_in(cat, exclude_unmeasured=MUST_NOT_HARM_EXCLUDES_UNMEASURED)
                if names:
                    earlier.append({"text": f"{join_names(names)} checked as safeguards in {_action_name(a)}",
                                    **_link(a.verification_ref or a.link_ref), "result_label": result, "detail": None})
        elif a.open and cat in move_cats:
            label = "Open" if a.is_domain else WORKFLOW_IN_HAND.get(a.workflow_label or "", a.workflow_label or "Open")
            in_hand.append({"text": _item_text(a.code, a.title), **_link(a.link_ref), "state_label": label + suffix})

    for case in sorted(facts.cases, key=lambda c: (c.code or "", c.case_id)):
        cats, suffix = _case_placement(case, by_id, roles, unresolved_suffix(facts))
        if cat not in cats | repeat_cats.get(case.case_id, set()):
            continue
        if case.state not in CLOSED_CASE_STATES:
            label = _case_label(case) + suffix
            in_hand.append({"text": _item_text(case.code, case.title), **_link(case.link_ref), "state_label": label,
                            **_case_wire(case)})
    for case in sorted(facts.cases, key=lambda c: (c.occurred_at is None, c.occurred_at, c.case_id)):
        cats, suffix = _case_placement(case, by_id, roles, unresolved_suffix(facts))
        result = earlier_result_for_case(case, facts.cases)
        if cat in cats | repeat_cats.get(case.case_id, set()) and result is not None:
            earlier.append({"text": _item_text(case.code, case.title), **_link(case.link_ref),
                            "result_label": result + (suffix if suffix in UNRESOLVED_SUFFIXES else ""), "detail": None,
                            **_case_wire(case)})

    if cat == "PROTECT_ASSET":
        cue = {w.subject: w.kind for w in facts.warnings if w.kind in PLAN_CUE_LABEL}
        for p in sorted(facts.plans, key=lambda p: (p.code or "", p.plan_id)):
            if p.state in ("DRAFT", "ACTIVE"):
                label = PLAN_CUE_LABEL[cue[p.plan_id]] if p.plan_id in cue else _plan_label(p, facts.date_suffix)
                in_hand.append({"text": _item_text(p.code, p.title), **_link(p.link_ref), "state_label": label,
                                "kind": PLAN_KIND})

    # Must not harm (B-Q19, addendum 1): only where a mini Action verification exists.
    must_not_harm = None
    for f in sorted(moves_here, key=lambda f: (f.title, f.finding_id)):
        checks = [a for a in linked_actions(f) if a.verification_state not in (None, NO_PLAN)]
        names = roles[f.finding_id].checked_outside(cat, exclude_unmeasured=MUST_NOT_HARM_EXCLUDES_UNMEASURED)
        if checks and names:
            a = checks[0]
            must_not_harm = {"text": f"{join_names(names)} are checked as safeguards when {_action_name(a)} is "
                                     "verified; a gain that harms them does not count", **_link(a.verification_ref)}
            break
    if must_not_harm is None:  # C: a repeat-visit warning moving this row, checked against outcomes elsewhere
        for w, r in warn_roles:
            names = r.checked_outside(cat)
            if w.kind == REPEATED and cat in r.move_cats and names:
                finding_link = next((x.get("link_ref") for x in w.evidence_refs if x["kind"] == "FINDING"), None)
                must_not_harm = {"text": join_names(names) + REPAIR_MUST_NOT_HARM, **_link(finding_link)}
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

    # WALK1-3b §A2.1: an open opportunity on a row whose state is not "Opportunity" is carried as its potential.
    potential = None
    if row_state != OPPORTUNITY and any(s.kind == SIGNAL_OPPORTUNITY and s.open and s.outcome in keys
                                        for s in signals):
        text = next((i["text"] for i in issues if i["kind"] == "OPPORTUNITY"), None)
        potential = {"label": POTENTIAL_LABEL, "text": text}
    domain_lines = list(facts.contributors.get(cat, ()))
    after = facts.objective_after.get(cat)
    at = next((i + 1 for i, c in enumerate(domain_lines) if c.key == after), len(domain_lines))
    ordered = (*domain_lines[:at], *objective_lines, *domain_lines[at:])

    # CH-3 §5: the thread line of each in-window Finding whose primary MOVES outcome is in this row.
    def state_on(f: FindingFact, day: Any) -> tuple[str, str] | None:
        """Ruling Q2: this row's (state, state label) with the Finding's thread state on `day` and the board's
        verdicts (CH-5a2 B4: the state code is the ThreadLine `after.state`)."""
        view = f.lifecycle_view or {}
        st = _state_on(view, day)
        alt = [replace(s, open=f.open and st not in view.get("verified_states", ()),
                       applied=st in view.get("applied_states", ()))
               if s.kind == FINDING and s.ref == f.finding_id else s for s in signals]
        alt_states = [(o.key, outcome_state(o, settled=bool(facts.settled.get(o.key, False)), signals=alt,
                                            readiness=facts.readiness, objective=verdicts.get(o.key),
                                            objectives_ok=facts.objectives_ok)[0]) for o in outcomes]
        if not alt_states:
            return None
        rolled = roll_up(alt_states)[0]
        return rolled, STATE_LABEL[rolled].lower()

    # CH-5a2 B4: structured lines; the subline joins their texts exactly as before (one per distinct text).
    thread_lines: list[dict[str, Any]] = []
    for f in thread_line_findings(facts):
        moves = roles[f.finding_id].moves
        if moves and OUTCOME_BY_KEY[moves[0]].category == cat:
            line = thread_line_item(f, facts, lambda day, f=f: state_on(f, day))
            if line and all(line["text"] != x["text"] for x in thread_lines):
                thread_lines.append(line)
    # MB-1b (MB-1-R §3.3), MOCK DEVIATION MD-FUEL-MB1-2: an opportunity thread's line (the mill) after the Findings'.
    for o in sorted(facts.opportunity_actions, key=lambda o: (o.code or "", o.action_id)):
        if o.category == cat:
            line = opportunity_line_item(o, facts)
            if line and all(line["text"] != x["text"] for x in thread_lines):
                thread_lines.append(line)
    subline = " · ".join(x for x in (facts.subline.get(cat), *(t["text"] for t in thread_lines)) if x) or None

    row.update({
        "potential": potential,
        "headline": headline, "headline_money": facts.headline_money.get(cat), "subline": subline,
        "thread_lines": thread_lines,
        "counts": {"issues": len(issues), "in_hand": len(in_hand)}, "must_not_harm": must_not_harm,
        "contributors": [_contributor(c) for c in ordered],
        "issues": issues,
        "options": [{"text": o.text, **_link(o.link_ref)} for o in facts.options.get(cat, ())],
        "in_hand": in_hand, "earlier": earlier,
        "earlier_empty_text": None if earlier else (
            EARLIER_EMPTY_OPEN if any(f.open and f.in_window for f in moves_here) else EARLIER_EMPTY_NONE),
    })
    return row


def _earlier_segment(a: ActionFact, facts: SiteFacts) -> bool:
    """CH-3 §3 (CH-2 L1): an Action linked to an earlier segment of its thread than the segment current on the board
    day is never in hand; it is listed under Earlier."""
    if a.thread_id is None or a.segment_no is None:
        return False
    current = [int(f.lifecycle_view.get("segment_current") or 0) for f in facts.findings
               if f.lifecycle_view is not None and f.thread is not None and f.thread.get("id") == a.thread_id]
    return bool(current) and a.segment_no < max(current)


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


def _primary(moves: Sequence[str], cat: str) -> bool:
    """CH-5a2 B5 (I-21): the row is the Finding's lens row when its category is the one of `moves[0]`."""
    return bool(moves) and OUTCOME_BY_KEY[moves[0]].category == cat


def _finding_issue(f: FindingFact, role: str, text: str, primary: bool) -> dict[str, Any]:
    return {"kind": "FINDING", "role": role, "text": text, "primary": primary, **_link(f.link_ref),
            "ref": {"finding_id": f.finding_id, "finding_revision_id": f.revision_id,
                    "thread": None if f.thread is None else {k: f.thread[k] for k in f.thread.get("wire_keys", ())
                                                             if k in f.thread}}}


def with_threads(facts: SiteFacts, found: Mapping[str, Mapping[str, Any]]) -> SiteFacts:
    """CH-2: the composition's facts with each Finding's thread and each Action's thread id from one lookup
    (`chain/lookup.py` shape: `{"findings": {id: {...}}, "actions": {id: thread_id}}`)."""
    fs, acts = found.get("findings") or {}, found.get("actions") or {}
    views, segs = found.get("lifecycle") or {}, found.get("action_segments") or {}
    opps = found.get("opportunities") or []
    if opps:  # CH-4 §4.4: the headroom signal links to the opportunity seen in the board's five days (R7: `open` kept)
        item = opps[0]
        thread = {"id": item["thread_id"], "occurrence_no": None, "occurrences": item["occurrences"],
                  "segment_no": None, "state": item["state"], "state_effective_day": item["state_effective_day"],
                  "state_day": item["state_day"]}
        ref = {"opportunity_id": item["study"]["opportunity_id"], "code": item["study"]["code"], "thread": thread}
        facts = replace(facts, signals_extra=tuple(
            replace(s, link_ref=item["link_refs"]["opportunity"], ref=ref)
            if s.signal_key == "SIGNAL:PRODUCTIVE_USE_HEADROOM" else s for s in facts.signals_extra))
    return replace(facts,
                   findings=tuple(replace(f, thread=fs.get(f.finding_id.lower()),
                                          lifecycle_view=views.get(f.finding_id.lower())) for f in facts.findings),
                   actions=tuple(replace(a, thread_id=acts.get(a.action_id.lower()),
                                         segment_no=segs.get(a.action_id.lower())) for a in facts.actions))


def _contributor(c: Contributor) -> dict[str, Any]:
    return {"key": c.key, "label": c.label, "text": c.text,
            "confidence": None if c.confidence is None else dict(c.confidence), **_link(c.link_ref)}
