"""CH-5b2 (build sheet CH-5b R1-R3, §2.1, §2.3; rulings CH5b2-R): the "Why?" trace of one outcome row.

One trace, two views (R1): `nodes` (each `{kind, label_key, ids, basis, grade}`, for audit and tests) and `text`
(`{title, say, comes_from, days_used, would_change, evidence_ref, evidence_label}`), rendered once here through
`chain/vocabulary.py`. The browser shows only `text`. Every node is built from a stored id; a node with no stored
id is not emitted, except the root `row_state`, which may have `ids: []` (CH5b2-R Q3).

Which sources the trace walks comes from `outcome_map` only (R2, OL-1): the Site's threads whose
`categories_for(thread_signal_key(mechanism))` names the category, moved or checked. No outcome id or map key is
built here. The category's measures are the `clean_day_measures` of those threads' mechanisms (CH5b2-R Q5 interim,
replaced by CH-6a1's `MEASURE:` records). Pure: the route (`chain_api.py`) hands in the board row, the day facts,
the threads, the Actions and the `trace_facts` read.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any, Mapping, Sequence

from assetops_backend.chain import refs
from assetops_backend.chain.grading import COMPLETE, LOW, NO_DATA, NOT_EXPECTED, PARTIAL, PENDING
from assetops_backend.chain.read import DayFacts, day_grade
from assetops_backend.chain.vocabulary import EXAMPLE_SOURCES, MEASURE_LABEL, day_text, why, why_days
from assetops_backend.outcomes.catalogue import CATEGORIES, CATEGORY_LABEL, SITE_OUTCOMES
from assetops_backend.outcomes.display_code import display_code
from assetops_backend.outcomes.outcome_map import CONTRIBUTIONS, NODE_EARNINGS

SCHEMA_VERSION = "outcome-chain-why-1"
#: The day class of each grade (CH5b2-R Q6): LOW is with NO_DATA, as the board's readiness rule
#: (`chain/read.py` `readiness_of`: LOW or NO_DATA only -> NONE) keeps it out of "checked".
DAY_CLASS = {COMPLETE: "checked", PARTIAL: "partial", LOW: "low", NO_DATA: "low", PENDING: "pending"}
#: R3: the day grades that leave a used measure to be checked.
UNCHECKED = (PARTIAL, LOW, NO_DATA, PENDING)
OPEN_STATES = ("OPEN", "RECURRED", "REOPENED")
#: R3 "an Action without a verdict": the thread has an Action and no verdict event yet.
AWAITING_VERDICT = ("ACTION_IN_HAND", "CHANGE_APPLIED")
MAX_FROM = 4
_WEAKEST_FIRST = (PENDING, NO_DATA, LOW, PARTIAL, COMPLETE)


class CategoryUnknown(ValueError):
    """`CATEGORY_UNKNOWN` (422): a category outside the four."""


def check_category(category: str | None) -> str:
    if category not in CATEGORIES:
        raise CategoryUnknown(str(category))
    return category


@dataclass(frozen=True)
class SiteTraceInput:
    site_code: str
    site_name: str
    domain: str
    category: str
    row: Mapping[str, Any]                       # the board composition's row for `category`
    facts: DayFacts                              # the window's snapshot grades (`ChainRequest.day`)
    site_measures: tuple[str, ...]               # the Site type's measures, in `MEASURES` order
    threads: Sequence[Mapping[str, Any]]         # `site_chain.threads_of`
    actions: Sequence[Mapping[str, Any]]         # `site_chain.actions_of`
    clean_measures: Mapping[str, Sequence[str]]  # `thread-lifecycle-v1.json` `clean_day_measures`
    trace_facts: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)  # `ChainRequest.trace_facts`


@dataclass(frozen=True)
class Trace:
    text: dict[str, Any]
    nodes: list[dict[str, Any]]
    unmatched: int = 0     # CH5b2-R Q8: lines not emitted because no board item matched (counted in the packet)
    open_days: int = 0     # CH6b3-R3 M2: the unchecked days behind "Checking n more days" on the board's window

    def to_json(self) -> dict[str, Any]:
        return {"text": self.text, "nodes": self.nodes}


def _node(kind: str, ids: Sequence[Any], basis: Any = None, grade: str | None = None) -> dict[str, Any]:
    return {"kind": kind, "label_key": f"why.{kind}", "ids": [str(i) for i in ids], "basis": basis, "grade": grade}


def related_threads(threads: Sequence[Mapping[str, Any]], category: str) -> list[Mapping[str, Any]]:
    """R2: the threads whose mapped categories name `category`, moved or checked (`categories_for` via the wire)."""
    return [t for t in threads
            if any(i.get("category") == category for i in (t.get("categories") or {}).get("items") or ())]


def used_measures(threads: Sequence[Mapping[str, Any]], clean: Mapping[str, Sequence[str]],
                  site_measures: Sequence[str]) -> tuple[str, ...]:
    """CH5b2-R Q5: the clean-day measures of the threads' mechanisms, in the Site type's measure order."""
    wanted = {m for t in threads for m in clean.get(t.get("mechanism") or "", ())}
    return tuple(m for m in site_measures if m in wanted)


def outcome_measures(domain: str, category: str) -> tuple[list[str], str | None]:
    """CH6a3-R Q3: the chain measures the category's outcomes record (`MEASURE:` sources, domain-filtered), and the
    measure behind its earnings node."""
    keys = {o.key for o in SITE_OUTCOMES if o.domain == domain and o.category == category}
    found = [r.source.partition(":")[2] for r in CONTRIBUTIONS if r.outcome in keys and r.source.startswith("MEASURE:")]
    earn = next((r.source.partition(":")[2] for r in CONTRIBUTIONS if r.outcome in keys and r.node == NODE_EARNINGS
                 and r.source.startswith("MEASURE:")), None)
    return found, earn


def _plain(value: Any) -> str:
    return f"{Decimal(str(value)).normalize():f}"


def price_lines(earnings: Mapping[str, Any] | None) -> tuple[str | None, str | None]:
    """The (energy, fuel) price lines of an earnings claim JSON; None where the claim carries no basis."""
    value = (earnings or {}).get("value") or {}
    energy = fuel = None
    if value.get("kwh") is not None:
        if value.get("price_count"):
            energy = why("why.from.price_several", kwh=_plain(value["kwh"]), n=value["price_count"])
        elif value.get("price"):
            energy = why("why.from.price", kwh=_plain(value["kwh"]), price=_plain(value["price"]["amount"]),
                         cur=value["price"].get("currency") or "")
    if value.get("litres_low") is not None and value.get("price"):
        lo, hi = _plain(value["litres_low"]), _plain(value["litres_high"])
        p = value["price"]
        fuel = (why("why.from.fuel_price_one", lo=lo, price=_plain(p["amount"]), cur=p.get("currency") or "")
                if lo == hi else
                why("why.from.fuel_price", lo=lo, hi=hi, price=_plain(p["amount"]), cur=p.get("currency") or ""))
        # FUEL-1 A3-R G5: owner decision 3, the example tank explained; only on example data with idle time
        if value.get("idle_seconds") and value.get("source_class") in EXAMPLE_SOURCES:
            fuel = fuel + " · " + why("why.from.fuel_idle_example")
    return energy, fuel


def _per(facts: DayFacts, d: date, measures: Sequence[str]) -> dict[str, list[str]]:
    return {m: list(((facts.grades.get(d) or {}).get(m) or {}).values()) for m in measures
            if (facts.grades.get(d) or {}).get(m)}


def day_grades(facts: DayFacts, measures: Sequence[str]) -> list[tuple[date, str]]:
    """Each window day's grade over `measures` (the board's `day_grade`: the weakest, a missing row NO_DATA)."""
    return [(d, day_grade(_per(facts, d, measures), measures)) for d in facts.days]


def days_line(facts: DayFacts, measures: Sequence[str]) -> str:
    graded = [(d, g) for d, g in day_grades(facts, measures) if g != NOT_EXPECTED]
    counts: dict[str, int] = {}
    for _, g in graded:
        counts[DAY_CLASS[g]] = counts.get(DAY_CLASS[g], 0) + 1
    one = DAY_CLASS[graded[0][1]] if len(facts.days) == 1 and graded else None
    return why_days(facts.days, counts, one)


def _weakest(grades: Sequence[str]) -> str | None:
    expected = [g for g in grades if g != NOT_EXPECTED]
    return next((g for g in _WEAKEST_FIRST if g in expected), None)


def _finding_title(row: Mapping[str, Any], finding_ids: Sequence[str]) -> str | None:
    """Q8: the board row's own `issues[]` Finding item for one of the thread's Findings (MOVES first)."""
    wanted = {str(f).lower() for f in finding_ids if f}
    items = [i for i in row.get("issues") or () if i.get("kind") == "FINDING"
             and str(((i.get("ref") or {}).get("finding_id")) or "").lower() in wanted]
    items.sort(key=lambda i: i.get("role") != "MOVES")
    if not items:
        return None
    text = str(items[0].get("text") or "")
    return text.split(" · ")[0] if items[0].get("role") == "CHECKED" else text


def _action_label(row: Mapping[str, Any], action_id: str) -> str | None:
    """Q8: the board's `in_hand` state label (or `earlier` result label) for that Action."""
    aid = str(action_id).lower()
    for key, label in (("in_hand", "state_label"), ("earlier", "result_label")):
        for item in row.get(key) or ():
            ref = item.get("link_ref") or {}
            if ref.get("kind") == "ACTION" and str(ref.get("id") or "").lower() == aid and item.get(label):
                return str(item[label])
    return None


def _row_ids(row: Mapping[str, Any]) -> list[str]:
    out: list[str] = []
    for key in ("issues", "in_hand", "earlier", "contributors", "options"):
        for item in row.get(key) or ():
            rid = (item.get("link_ref") or {}).get("id")
            if rid and str(rid) not in out:
                out.append(str(rid))
    return out


def trace(x: SiteTraceInput) -> Trace:
    """R1-R3: the trace of one Site's `x.category` row."""
    threads = related_threads(x.threads, x.category)
    tids = {t["id"] for t in threads}
    actions = [a for a in x.actions if a.get("thread") in tids]
    extra, earn_measure = outcome_measures(x.domain, x.category)
    base = used_measures(threads, x.clean_measures, x.site_measures)
    measures = tuple(m for m in x.site_measures if m in set(base) | set(extra))
    energy_line, fuel_line = price_lines(((x.row.get("nodes") or {}).get("earnings")))
    counted = measures or tuple(x.site_measures)
    nodes = [_node("row_state", _row_ids(x.row), x.row.get("state"))]
    lines: list[str] = []
    unmatched = 0

    # measure_day: the window's snapshot rows of each used measure.
    for m in measures:
        ids, grades = [], []
        for d in x.facts.days:
            subjects = (x.facts.grades.get(d) or {}).get(m) or {}
            ids += [f"{d.isoformat()}/{m}/{s}" for s in sorted(subjects)]
            grades.append(day_grade(_per(x.facts, d, [m]), [m]))
        if ids:
            nodes.append(_node("measure_day", ids, m, _weakest(grades)))
        k = sum(1 for g in grades if g == COMPLETE)
        if k:
            lines.append(why("why.from.measure", label=MEASURE_LABEL.get(m, m), k=k, s="" if k == 1 else "s"))
            if m == earn_measure and energy_line:
                lines.append(energy_line)

    # analytic, finding, thread: the head revisions of the related threads' Findings.
    runs: list[str] = []
    for t in threads:
        occs = list(t.get("occurrences") or ())
        fids = [o["finding_id"] for o in occs if o.get("finding_id")]
        for fid in dict.fromkeys(fids):
            f = x.trace_facts.get(str(fid).lower())
            if f is None:
                continue
            nodes.append(_node("finding", [fid, f["revision_id"]], {"revision_no": f["revision_no"],
                                                                     "cited": f["cited"]}))
            if f.get("analytic_run_id") and f["analytic_run_id"] not in runs:
                runs.append(f["analytic_run_id"])
        nodes.append(_node("thread", [t["id"]], {"state": t.get("state"), "since": t.get("since")}))
        title = _finding_title(x.row, fids)
        days = sorted(o["day"] for o in occs if o.get("day"))
        if title and days:
            n = len(occs)
            lines.append(why("why.from.finding", title=title, n=n, s="" if n == 1 else "s",
                             first=day_text(date.fromisoformat(days[0]))))
        else:
            unmatched += 1
    if runs:
        nodes.insert(1 + sum(1 for n in nodes if n["kind"] == "measure_day"), _node("analytic", runs))

    if fuel_line:
        lines.append(fuel_line)
    for a in actions:
        nodes.append(_node("action", [a["id"]], {"code": a.get("code"), "verification": a.get("verification")}))
        label = _action_label(x.row, a["id"])
        if label:
            lines.append(why("why.from.action", code=display_code(a.get("code")) or "", label=label))
        else:
            unmatched += 1

    # R3: the first missing input.
    open_days = sum(1 for _, g in day_grades(x.facts, counted) if g in UNCHECKED)
    with_action = {a.get("thread") for a in actions}
    if open_days:
        change = why("why.change.days", n=open_days, s="" if open_days == 1 else "s")
    elif any(t.get("state") in OPEN_STATES and t["id"] not in with_action for t in threads):
        change = why("why.change.action")
    elif any(t.get("state") in AWAITING_VERDICT and t["id"] in with_action for t in threads):
        change = why("why.change.verdict")
    else:
        change = why("why.change.readings")

    evidence = (x.row.get("evidence_link") or {}).get("link_ref") or refs.evidence_ref(x.site_code)
    text = {"title": why("why.title", site=x.site_name, category=CATEGORY_LABEL[x.category]),
            "say": x.row.get("headline") or x.row.get("state_label"),
            "comes_from": lines[:MAX_FROM] or [why("why.from.none")],
            "days_used": days_line(x.facts, counted), "would_change": change,
            "evidence_ref": dict(evidence), "evidence_label": why("why.evidence", site=x.site_name)}
    return Trace(text, nodes, unmatched, open_days)


def site_trace(req: Any, ref: Any, *, category: str, board: Mapping[str, Any], facts: DayFacts,
               site_measures: Sequence[str], clean_measures: Mapping[str, Sequence[str]],
               verification: Any, known_at: Any = None) -> Trace:
    """The route's one call (`chain_api.py`): the Site's thread history through the board's window
    (`site_chain.threads_through`, read on the board day), their Actions, one `trace_facts` read for their Findings,
    then `trace`. `req` is the request's `ChainRequest` (its thread read is the Site chain's memoised one);
    `verification(rows, thread_ids)` is the route's Action verification read.
    BL-50: threads and Actions are read at the board's visibility, `lifecycle_cutoff(known_at)` (the request's cutoff,
    None = now), never the window's `known_at` (Cold/EV's evidence-end cutoff hides a Finding assessed after its
    evidence ends)."""
    from assetops_backend.chain import site_chain
    from assetops_backend.chain.read import lifecycle_cutoff, window_day

    w = board["window"]
    lo, hi = _instant(w["from"]), _instant(w["to"])
    cutoff = lifecycle_cutoff(known_at)
    rows = req.threads(ref.site_id)
    threads = site_chain.threads_through(rows, site=ref.site_code, domain=ref.domain, tz=ref.timezone, hi=hi,
                                         day=window_day(lo, hi, ref.timezone), cutoff=cutoff)
    related = related_threads(threads, category)
    ids = {t["id"] for t in related}
    actions = site_chain.actions_of(rows, ids, site=ref.site_code, tz=ref.timezone, cutoff=cutoff,
                                    verification=verification(rows, ids))
    fids = [o["finding_id"] for t in related for o in t.get("occurrences") or () if o.get("finding_id")]
    row = next((r for r in board["rows"] if r["category"] == category), {})
    return trace(SiteTraceInput(
        site_code=ref.site_code, site_name=ref.site_name or ref.site_code, domain=ref.domain, category=category,
        row=row, facts=facts, site_measures=tuple(site_measures), threads=related, actions=actions,
        clean_measures=clean_measures, trace_facts=req.trace_facts(ref.site_id, fids)))


def _instant(text: Any) -> Any:
    from datetime import datetime

    return None if text is None else datetime.fromisoformat(str(text).replace("Z", "+00:00"))


def disrupted_lines(sites: Sequence[tuple[str, Sequence[Mapping[str, Any]], Mapping[str, Any]]]) -> list[str]:
    """CH6b2-R Q2(b): the Protect card's "Why?" `comes_from`: one "{Site}: {thread title}" per thread counted in
    `count.sites_disrupted`, over `(Site name, its disrupting threads, its board's Protect row)` in Site order (never
    cut to `MAX_FROM`, so the number is traceable), then the mock's early-warning line. The title is the board row's
    own Finding item; a thread without one is named by its state and first day (MOCK DEVIATION)."""
    lines = []
    for name, threads, row in sites:
        for t in threads:
            occs = t.get("occurrences") or ()
            title = _finding_title(row, [o["finding_id"] for o in occs if o.get("finding_id")])
            days = sorted(o["day"] for o in occs if o.get("day"))
            if title:
                lines.append(why("why.from.disrupted", site=name, title=title))
            else:
                lines.append(why("why.from.disrupted_untitled", site=name, state=t.get("state_label") or "",
                                 first=day_text(date.fromisoformat(days[0])) if days else ""))
    return [*lines, why("why.from.warnings_apart")]


def estate_text(category: str, sites: Sequence[tuple[str, Trace]],
                comes_from: Sequence[str] | None = None, days_used: str | None = None,
                window_open: Mapping[str, int] | None = None) -> dict[str, Any]:
    """CH5b2-R Q9: the estate text over the per-Site traces (Site order). No money is summed (design A6).
    `comes_from` replaces the per-Site lines (CH6b2-R Q2b: the Protect card's counted threads). CH6b3-R3 M2:
    `days_used`, when given, is the card's own days line (it replaces the per-Site join); `window_open` (by Site
    name) is each Site's unchecked days on the estate window, replacing the board-day count in "Checking n more
    days" (a Site with none is skipped)."""
    n = len(sites)
    readings = why("why.change.readings")

    def site_change(name: str, t: Trace) -> str | None:
        if window_open is None or t.open_days <= 0:
            return t.text["would_change"]
        k = window_open.get(name, 0)
        return why("why.change.days", n=k, s="" if k == 1 else "s") if k > 0 else None

    # MOCK DEVIATION (CH5b2-R Q9): the mock has one sentence per Portfolio card; the estate takes the first Site
    # line that is not "New readings that differ", else that line.
    change = next((c for c in (site_change(name, t) for name, t in sites) if c and c != readings), readings)
    return {"title": why("why.title", site="Portfolio", category=CATEGORY_LABEL[category]),
            "say": why("why.estate.say", category=CATEGORY_LABEL[category], n=n, s="" if n == 1 else "s"),
            "comes_from": list(comes_from) if comes_from is not None else
            [why("why.estate.from", site=name, say=t.text["say"]) for name, t in sites][:MAX_FROM]
            or [why("why.from.none")],
            "days_used": days_used if days_used is not None else
            " · ".join(why("why.estate.days", site=name, days=t.text["days_used"]) for name, t in sites),
            # MOCK DEVIATION (CH5b2-R2, owner CH-5b3): the mock pf: links carry a label per category (Renewable
            # evidence, Kobo financials, Risk findings, Estate evidence); the estate has one link, so one label.
            "would_change": change, "evidence_ref": refs.estate_ref("findings"),
            "evidence_label": why("why.evidence", site="Portfolio")}
