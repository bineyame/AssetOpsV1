"""OUT-C U1: early warnings, policy `early-warnings/1` (build sheet OUT-C §2 U1, §3).

Pure. The composer passes instants (compared only), pre-computed bounds, Site-local dates (`.day`/`.month` only)
and pre-formatted number texts. Every bound is half-open and nothing fires when its input is absent. A warning
never carries money: no amount, currency, price or rate, in any key or text."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from assetops_backend.outcomes.outcome_map import categories_for, outcome_roles

POLICY = "early-warnings/1"

REPEATED = "REPEATED_MAINTENANCE_NO_RESULT"
PLAN_OVERDUE = "PLAN_OVERDUE"
PLAN_DUE_SOON = "PLAN_DUE_SOON"
BATTERY = "BATTERY_NEAR_RESERVE"
CHARGER_FAULT = "CHARGER_FAULT_OVERDUE_INSPECTION"
CONNECTOR_OUT = "CONNECTOR_OUT_OF_SERVICE"
PEAK = "PEAK_NEAR_IMPORT_LIMIT"
#: Sort order inside a badge (ruling L2): overdue before due soon, the repeat warning before connector and peak, so
#: a list cut to its first few entries never drops an overdue plan for a due-soon one.
KINDS = (REPEATED, PLAN_OVERDUE, PLAN_DUE_SOON, BATTERY, CHARGER_FAULT, CONNECTOR_OUT, PEAK)

#: A peak strictly closer than this fraction of the configured import limit fires.
PEAK_MARGIN = 0.10

RISK, EARLY_WARNING, OPPORTUNITY = "RISK", "EARLY_WARNING", "OPPORTUNITY"
BADGE_ORDER = (RISK, EARLY_WARNING, OPPORTUNITY)
BADGE_LABEL = {RISK: "Risk", EARLY_WARNING: "Early warning", OPPORTUNITY: "Opportunity"}
RECURRING, OBSERVED = "RECURRING", "OBSERVED"
PERSISTENCE_LABEL = {RECURRING: "Recurring", OBSERVED: "Observed"}
NEEDS_ATTENTION, WATCH = "NEEDS_ATTENTION", "WATCH"

PRICE_NEEDS = {
    REPEATED: "A cost per visit is not set for this site",
    PLAN_OVERDUE: "Needs repair cost and wear history",
    PLAN_DUE_SOON: "Needs repair cost and wear history",
    BATTERY: "Needs a tested battery wear model",
    CHARGER_FAULT: "Needs repair cost and fault history",
    CONNECTOR_OUT: "Needs the bus roster",
    PEAK: "Needs a demand forecast",
}
#: kind -> (badge, lens, status effect)
RULE = {
    REPEATED: (RISK, "COST", NEEDS_ATTENTION),
    PLAN_OVERDUE: (EARLY_WARNING, "RISK", WATCH),
    PLAN_DUE_SOON: (EARLY_WARNING, "RISK", WATCH),
    BATTERY: (EARLY_WARNING, "RISK", WATCH),
    CHARGER_FAULT: (EARLY_WARNING, "RISK", WATCH),
    CONNECTOR_OUT: (RISK, "RISK", WATCH),
    PEAK: (RISK, "RISK", WATCH),
}
PLAN_HREF = "/maintenance/preventive"
COMPLETED = "COMPLETED"
_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


@dataclass(frozen=True)
class Visit:
    case_id: str
    code: str
    asset_id: str | None
    asset_name: str
    state: str
    occurred_at: Any
    occurred_on: Any
    finding_ids: tuple[str, ...] = ()
    href: str | None = None


@dataclass(frozen=True)
class PlanCue:
    plan_id: str
    code: str
    title: str
    due_at: Any
    due_on: Any
    asset_id: str | None = None
    href: str | None = PLAN_HREF


@dataclass(frozen=True)
class WarningFacts:
    domain: str
    site_code: str
    to: Any
    visits_from: Any                     # to - 60 d (composer computes)
    soon_until: Any                      # to + 14 d (composer computes)
    window_days: tuple[Any, Any]         # Site-local first and last day of the window
    date_suffix: str = ""
    visits: tuple[Visit, ...] = ()
    plans: tuple[PlanCue, ...] = ()
    open_findings: Mapping[str, tuple[tuple[str, ...], str | None]] = field(default_factory=dict)
    reserve: tuple[int, int] | None = None                       # mini: (n at or near, m assessed)
    faults: tuple[tuple[str, str], ...] = ()                     # EV: (asset_id, label)
    connectors_out: tuple[tuple[str, str, str, str | None], ...] = ()  # EV: (asset_id, label, out, unknown)
    peak: tuple[float, float, str, str] | None = None            # EV: (peak, limit, peak text, limit text)


@dataclass(frozen=True)
class Warning:
    kind: str
    key: str
    subject: str                         # not on the wire
    badge: str
    lens: str
    title: str
    seen: str
    persistence: str
    price_needs: str
    status_effect: str
    categories: dict[str, Any]
    href: str | None
    evidence_refs: tuple[dict[str, Any], ...] = ()
    count: int | None = None
    subject_label: str | None = None
    visit_ids: tuple[str, ...] = ()      # not on the wire

    def wire(self, site_code: str, site_name: str) -> dict[str, Any]:
        return {"key": self.key, "kind": self.kind, "badge": self.badge, "badge_label": BADGE_LABEL[self.badge],
                "lens": self.lens, "title": self.title, "seen": self.seen, "persistence": self.persistence,
                "persistence_label": PERSISTENCE_LABEL[self.persistence], "price_needs": self.price_needs,
                "status_effect": self.status_effect, "categories": self.categories, "site_code": site_code,
                "site_name": site_name, "href": self.href, "evidence_refs": [dict(r) for r in self.evidence_refs],
                "count": self.count, "subject_label": self.subject_label}


def day_text(day: Any) -> str:
    """'d MMM' from a Site-local date (only `.day` and `.month` are read)."""
    return f"{day.day} {_MONTHS[day.month - 1]}"


def _dates(f: WarningFacts, days: list[Any]) -> str:
    return ", ".join(day_text(d) for d in days) + f.date_suffix


def _window_text(f: WarningFacts) -> str:
    d1, d2 = f.window_days
    if d1 == d2:
        return "on " + day_text(d1) + f.date_suffix
    return f"between {day_text(d1)} and {day_text(d2)}{f.date_suffix}"


def _make(f: WarningFacts, kind: str, subject: str, title: str, seen: str, href: str | None, *,
          linked: tuple[str, ...] = (), refs: list[dict[str, Any]] | None = None, count: int | None = None,
          subject_label: str | None = None, visit_ids: tuple[str, ...] = ()) -> Warning:
    badge, lens, effect = RULE[kind]
    return Warning(kind=kind, key=f"{kind}:{f.site_code}:{subject}", subject=subject, badge=badge, lens=lens,
                   title=title, seen=seen, persistence=RECURRING if kind == REPEATED else OBSERVED,
                   price_needs=PRICE_NEEDS[kind], status_effect=effect,
                   categories=categories_for("WARNING:" + kind, f.domain, linked), href=href,
                   evidence_refs=tuple(refs or ()), count=count, subject_label=subject_label, visit_ids=visit_ids)


def _repeated(f: WarningFacts) -> list[Warning]:
    own = outcome_roles("WARNING:" + REPEATED, f.domain)[0]
    by_asset: dict[str, list[Visit]] = {}
    for v in f.visits:
        if v.asset_id is not None and f.visits_from <= v.occurred_at < f.to:
            by_asset.setdefault(v.asset_id, []).append(v)
    out = []
    for asset_id, visits in by_asset.items():
        visits.sort(key=lambda v: (v.occurred_at, v.case_id))
        done = [v for v in visits if v.state == COMPLETED]
        if len(done) < 2:
            continue
        open_ids: list[str] = []
        for v in visits:
            for fid in v.finding_ids:
                if fid in f.open_findings and fid not in open_ids:
                    open_ids.append(fid)
        if not open_ids:
            continue
        linked: list[str] = []
        for fid in open_ids:
            for k in f.open_findings[fid][0]:
                if k not in own and k not in linked:
                    linked.append(k)
        latest = done[-1]
        name = latest.asset_name
        seen = (f"{name} visited {len(done)} times in 60 days ({_dates(f, [v.occurred_on for v in done])}); "
                "the linked finding is still open")
        refs = [{"kind": "WORK_CASE", "id": v.case_id, "label": v.code, "href": v.href} for v in done]
        refs += [{"kind": "FINDING", "id": fid, "label": None, "href": f.open_findings[fid][1]} for fid in open_ids]
        out.append(_make(f, REPEATED, asset_id, "Repeated maintenance without a result", seen, latest.href,
                         linked=tuple(linked), refs=refs, count=len(done), subject_label=name,
                         visit_ids=tuple(v.case_id for v in done)))
    return out


def _plan_ref(p: PlanCue) -> dict[str, Any]:
    return {"kind": "PLAN", "id": p.plan_id, "label": p.code, "href": p.href}


def _overdue(f: WarningFacts) -> list[PlanCue]:
    return [p for p in f.plans if p.due_at is not None and p.due_at < f.to]


def _plans(f: WarningFacts) -> list[Warning]:
    out = []
    for p in f.plans:
        if p.due_at is None:
            continue
        if p.due_at < f.to:
            out.append(_make(f, PLAN_OVERDUE, p.plan_id, f"{p.title} overdue",
                             f"Planned for {day_text(p.due_on)}{f.date_suffix}, not done", PLAN_HREF,
                             refs=[_plan_ref(p)]))
        elif p.due_at < f.soon_until:
            out.append(_make(f, PLAN_DUE_SOON, p.plan_id, f"{p.title} due soon",
                             f"Due {day_text(p.due_on)}{f.date_suffix}", PLAN_HREF, refs=[_plan_ref(p)]))
    return out


def _battery(f: WarningFacts) -> list[Warning]:
    if f.reserve is None or f.reserve[0] < 1:
        return []
    n, m = f.reserve
    seen = (f"During {n} of {m} assessed generator {'period' if m == 1 else 'periods'} on "
            f"{day_text(f.window_days[0])}{f.date_suffix}")
    return [_make(f, BATTERY, "site", "Battery at or near its reserve", seen,
                  f"/sites/{f.site_code}/performance/dispatch")]


def _faults(f: WarningFacts) -> list[Warning]:
    overdue = sorted(_overdue(f), key=lambda p: (p.due_at, p.plan_id))
    out = []
    for asset_id, label in f.faults:
        plan = next((p for p in overdue if p.asset_id == asset_id), None)
        if plan is None:
            continue
        seen = (f"{label} fault recorded in this window · inspection overdue since "
                f"{day_text(plan.due_on)}{f.date_suffix}")
        refs = [_plan_ref(plan), {"kind": "ASSET", "id": asset_id, "label": label, "href": None}]
        out.append(_make(f, CHARGER_FAULT, asset_id, "Charger fault and overdue inspection", seen,
                         f"/sites/{f.site_code}/health", refs=refs, subject_label=label))
    return out


def _connectors(f: WarningFacts) -> list[Warning]:
    out = []
    for asset_id, label, out_text, unknown_text in f.connectors_out:
        lead = f"{out_text} out and {unknown_text} unknown" if unknown_text else f"{out_text} out"
        name = label if label.lower().startswith("connector") else f"Connector {label}"  # "Connector c1" labels
        out.append(_make(f, CONNECTOR_OUT, asset_id, f"{name} out of service",
                         f"{lead} {_window_text(f)}", f"/sites/{f.site_code}/performance/availability",
                         refs=[{"kind": "ASSET", "id": asset_id, "label": label, "href": None}],
                         subject_label=label))
    return out


def _peak(f: WarningFacts) -> list[Warning]:
    if f.peak is None:
        return []
    peak, limit, peak_text, limit_text = f.peak
    if not limit or not peak > (1 - PEAK_MARGIN) * limit:  # strictly within the margin (72 of 80 does not fire)
        return []
    return [_make(f, PEAK, "site", "Peak close to the import limit", f"{peak_text} kW against {limit_text} kW",
                  f"/sites/{f.site_code}/performance/energy")]


def evaluate(f: WarningFacts) -> tuple[Warning, ...]:
    """Every warning that fires, sorted by badge (RISK, EARLY_WARNING, OPPORTUNITY), position in KINDS, then key."""
    found = _repeated(f) + _plans(f) + _battery(f) + _faults(f) + _connectors(f) + _peak(f)
    return tuple(sorted(found, key=lambda w: (BADGE_ORDER.index(w.badge), KINDS.index(w.kind), w.key)))
