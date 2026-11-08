"""CH-5a2a (build sheet Part B §B1): the pure parts of the `outcome-chain-1` bodies.

`days_of` (the window's Site-local day grades from one `ChainRequest.day`), `threads_of` (the Site's threads in a
window, read on the board's day as of the state cutoff), `actions_of`, `thread_detail` and `outcomes_of` (the board
composition's rows, reduced to the chain's outcome fields). Categories and lens come only through `outcome_map`
(OL-1); state words only from `chain/vocabulary.py`. No I/O: the routes (`chain_api.py`) hand in the rows.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any, Iterable, Mapping, Sequence

from assetops_backend.chain import lifecycle as lc
from assetops_backend.chain import refs
from assetops_backend.chain.read import DayFacts, day_grade, local_days
from assetops_backend.chain.vocabulary import THREAD_STATE_WORDS
from assetops_backend.outcomes.outcome_map import categories_for, lens_flags, thread_signal_key

SCHEMA_VERSION = "outcome-chain-1"


def _iso(d: date | None) -> str | None:
    return None if d is None else d.isoformat()


def _local(at: datetime | None, tz: str | None) -> date | None:
    return None if at is None or not tz else lc.local_day(at, tz)


def days_of(facts: DayFacts, measures: Sequence[str]) -> list[dict[str, Any]]:
    """One entry per requested Site-local day: the day grade (`day_grade`, missing rows as CH5a1-R Q9) and each
    measure's own grade by the same rule."""
    out = []
    for d in facts.days:
        per = {m: list((facts.grades.get(d) or {}).get(m, {}).values()) for m in measures}
        per = {m: g for m, g in per.items() if g}
        out.append({"day": d.isoformat(), "grade": day_grade(per, measures),
                    "measures": {m: day_grade(per, [m]) for m in measures}})
    return out


def _events(rows: Mapping[str, Any]) -> dict[str, list[lc.Event]]:
    out: dict[str, list[lc.Event]] = {}
    for e in rows.get("events", ()):
        out.setdefault(e["thread_id"], []).append(lc.Event(int(e["seq"]), e["state"], e["cause_kind"],
                                                           str(e["cause_id"]), e["effective_day"],
                                                           e["recorded_at"], e["cause_known_at"]))
    return out


def _occurrences(rows: Mapping[str, Any]) -> dict[str, list[Mapping[str, Any]]]:
    out: dict[str, list[Mapping[str, Any]]] = {}
    for o in rows.get("occurrences", ()):
        out.setdefault(o["thread_id"], []).append(o)
    return out


def _occurrence_wire(o: Mapping[str, Any], tz: str | None) -> dict[str, Any]:
    no = o.get("opportunity_no")
    return {"finding_id": o["finding_id"], "opportunity_id": o["opportunity_id"],
            # No Finding public code is stored (pre-flight P3); an opportunity shows its CH-4 code.
            "code": None if no is None else f"OPP-{int(no):06d}",
            "day": _iso(_local(o["episode_start"], tz))}


def _in_window(occs: Iterable[Mapping[str, Any]], evs: Sequence[lc.Event], lo: datetime, hi: datetime,
               days: Sequence[date]) -> bool:
    for o in occs:
        start, end = o["episode_start"], o["episode_end"]
        if start is not None and start < hi and (end is None or end > lo):
            return True
    return bool(days) and any(days[0] <= e.effective_day <= days[-1] for e in evs)


def _thread_wire(site: str, tid: str, occs: Sequence[Mapping[str, Any]], evs: Sequence[lc.Event],
                 state: str | None, since: date | None, domain: str, tz: str | None) -> dict[str, Any]:
    mechanism = occs[0]["mechanism"] if occs else None
    key = thread_signal_key(mechanism)
    return {"id": tid, "mechanism": mechanism, "lens": lens_flags(key, domain),
            "categories": categories_for(key, domain), "state": state,
            "state_label": None if state is None else THREAD_STATE_WORDS.get(state),
            "since": _iso(since), "occurrences": [_occurrence_wire(o, tz) for o in occs],
            "ref": refs.thread_ref(site, tid)}


def threads_of(rows: Mapping[str, Any], *, site: str, domain: str, tz: str | None, lo: datetime, hi: datetime,
               day: date | None, cutoff: datetime | None) -> list[dict[str, Any]]:
    """The threads with a visible occurrence whose episode meets `[lo, hi)`, or an event effective on one of the
    window's Site-local days; each read on `day` (the board's `window_day`) from the events visible at `cutoff`."""
    days = local_days(lo, hi, tz)
    events, occs = _events(rows), _occurrences(rows)
    out = []
    for tid in sorted(occs):
        evs = lc.visible(events.get(tid, []), cutoff)
        if not _in_window(occs[tid], evs, lo, hi, days):
            continue
        state, since = lc.state_on(evs, day) if day is not None else (None, None)
        out.append(_thread_wire(site, tid, occs[tid], evs, state, since, domain, tz))
    return out


def threads_through(rows: Mapping[str, Any], *, site: str, domain: str, tz: str | None, hi: datetime,
                    day: date | None, cutoff: datetime | None) -> list[dict[str, Any]]:
    """CH-5b2 (the "Why?" trace): every thread of the Site with a visible occurrence that started before `hi` and a
    state on `day` from the events visible at `cutoff`, with only those occurrences: a thread's history up to the
    window's end, so a row's lasting causes (an earlier Finding, its Action) are reached on a later day."""
    events, occs = _events(rows), _occurrences(rows)
    out = []
    for tid in sorted(occs):
        before = [o for o in occs[tid] if o["episode_start"] is not None and o["episode_start"] < hi]
        if not before or day is None:
            continue
        evs = [e for e in lc.visible(events.get(tid, []), cutoff) if e.effective_day <= day]
        state, since = lc.state_on(evs, day)
        if state is None:
            continue
        out.append(_thread_wire(site, tid, before, evs, state, since, domain, tz))
    return out


def actions_of(rows: Mapping[str, Any], thread_ids: Iterable[str], *, site: str, tz: str | None,
               cutoff: datetime | None, verification: Mapping[str, str | None]) -> list[dict[str, Any]]:
    """The linked Actions of the given threads: the segment by `lifecycle.action_segment` (the lookup's rule) and the
    verification state the caller read (`ChainRequest.action_facts`; None for a domain intent)."""
    wanted = set(thread_ids)
    events, occs = _events(rows), _occurrences(rows)
    out = []
    for a in rows.get("actions", ()):
        tid = a["thread_id"]
        if tid not in wanted:
            continue
        evs = lc.visible(events.get(tid, []), cutoff)
        # CH-9b1: the origin occurrence is the Finding's, or (a MINI domain Action) the opportunity's.
        key, ref = (("finding_id", a["origin_finding_id"]) if a.get("origin_finding_id") is not None
                    else ("opportunity_id", a.get("origin_opportunity_id")))
        origin = next((o for o in occs.get(tid, ()) if ref is not None and o[key] == ref), None)
        occ = None if origin is None else lc.Occurrence(origin[key], _local(origin["episode_start"], tz))
        seg = lc.action_segment(evs, occ, lc.accepted_day([_local(a["accepted_at"], tz)]))
        out.append({"id": a["action_id"], "code": a["action_code"], "kind": a["kind"], "thread": tid,
                    "segment_no": seg, "verification": verification.get(a["action_id"]),
                    "ref": action_wire_ref(site, a)})
    return out


def action_wire_ref(site: str, a: Mapping[str, Any]) -> dict[str, Any]:
    """DD1b2-R6 O1: a domain intent raised from an opportunity (the mill) has no Action page; its Ref is the verdict
    page. Every other Action (MINI_TRIAL, a Cold/EV Finding's domain intent) keeps its ACTION Ref.

    DIESEL-1-R3m: a fuel Action has no Action page; its Ref is the fuel verdict page."""
    if a["kind"] == "DOMAIN_INTENT" and a.get("origin_opportunity_id") is not None:
        return refs.domain_verdict_ref(site, a["action_id"])
    if a["kind"] == "DOMAIN_INTENT" and a.get("action_domain") == "FUEL_BALANCE":
        return refs.fuel_verdict_ref(site, a["action_id"])
    return refs.action_ref(site, a["action_id"])


def opportunity_actions(rows: Mapping[str, Any], *, site: str, tz: str | None, cutoff: datetime | None,
                        lo: datetime, hi: datetime) -> list[dict[str, Any]]:
    """MB-1 (FUEL-1 MB-1-R Q1/Q4): the Site's opportunity-origin domain Actions shown in `[lo, hi)` as of `cutoff`:
    kind DOMAIN_INTENT with `origin_opportunity_id` set and a thread; `accepted_at < hi` and (cutoff None or
    `accepted_at <= cutoff`); and the thread has an occurrence with an `opportunity_id` whose episode meets
    `[lo, hi)` (the `_finding_threads` predicate, claims.py:59-66). `outcome` is the stored decisive outcome when
    its `outcome_recorded_at` is known by `cutoff` (None = every one), else None (not judged as known)."""
    occs = _occurrences(rows)
    out = []
    for a in rows.get("actions", ()):
        tid, accepted = a.get("thread_id"), a.get("accepted_at")
        if a.get("kind") != "DOMAIN_INTENT" or a.get("origin_opportunity_id") is None or tid is None:
            continue
        if accepted is None or accepted >= hi or (cutoff is not None and accepted > cutoff):
            continue
        if not any(o.get("opportunity_id") is not None and o["episode_start"] is not None and o["episode_start"] < hi
                   and (o["episode_end"] is None or o["episode_end"] > lo) for o in occs.get(tid, ())):
            continue
        outcome, recorded = a.get("outcome"), a.get("outcome_recorded_at")
        known = outcome is not None and (cutoff is None or (recorded is not None and recorded <= cutoff))
        out.append({"action_id": a["action_id"], "code": a.get("action_code"), "thread_id": tid,
                    "origin_opportunity_id": a["origin_opportunity_id"], "accepted_at": accepted,
                    "outcome": outcome if known else None, "outcome_recorded_at": recorded if known else None,
                    # WD-1m (WD-1m-R §3): the verdict's example-data class follows the outcome's cutoff visibility
                    "source_class": a.get("source_class") if known else None,
                    "ref": action_wire_ref(site, a)})
    out.sort(key=lambda x: (x["code"] or "", x["action_id"]))
    return out


def fuel_verdict_actions(rows: Mapping[str, Any], *, site: str, cutoff: datetime | None,
                         lo: datetime, hi: datetime) -> list[dict[str, Any]]:
    """DIESEL-1-R3m: `opportunity_actions` for the Site's FUEL_BALANCE domain Actions: kind DOMAIN_INTENT with
    `action_domain` FUEL_BALANCE and a thread; the same `accepted_at` test; the thread has an occurrence with a
    `finding_id` whose episode meets `[lo, hi)`. `outcome` is the stored decisive outcome when known by `cutoff`."""
    occs = _occurrences(rows)
    out = []
    for a in rows.get("actions", ()):
        tid, accepted = a.get("thread_id"), a.get("accepted_at")
        if a.get("kind") != "DOMAIN_INTENT" or a.get("action_domain") != "FUEL_BALANCE" or tid is None:
            continue
        if accepted is None or accepted >= hi or (cutoff is not None and accepted > cutoff):
            continue
        if not any(o.get("finding_id") is not None and o["episode_start"] is not None and o["episode_start"] < hi
                   and (o["episode_end"] is None or o["episode_end"] > lo) for o in occs.get(tid, ())):
            continue
        outcome, recorded = a.get("outcome"), a.get("outcome_recorded_at")
        known = outcome is not None and (cutoff is None or (recorded is not None and recorded <= cutoff))
        out.append({"action_id": a["action_id"], "code": a.get("action_code"), "thread_id": tid,
                    "outcome": outcome if known else None, "outcome_recorded_at": recorded if known else None,
                    "source_class": a.get("source_class") if known else None,
                    "ref": action_wire_ref(site, a)})
    out.sort(key=lambda x: (x["code"] or "", x["action_id"]))
    return out


def thread_detail(rows: Mapping[str, Any], thread_id: str, *, site: str, domain: str, tz: str | None,
                  cutoff: datetime | None) -> dict[str, Any] | None:
    """`/sites/{code}/threads/{id}`: the thread (None when it is not this Site's, or has no visible occurrence),
    its state from the last visible event, and its visible events."""
    occs = _occurrences(rows).get(thread_id)
    if not occs:
        return None
    evs = lc.visible(_events(rows).get(thread_id, []), cutoff)
    last = evs[-1] if evs else None
    body = _thread_wire(site, thread_id, occs, evs, None if last is None else last.state,
                        None if last is None else last.effective_day, domain, tz)
    body["events"] = [{"seq": e.seq, "state": e.state, "state_label": THREAD_STATE_WORDS.get(e.state),
                       "effective_day": e.effective_day.isoformat(), "cause_kind": e.cause_kind} for e in evs]
    return body


def _row_refs(row: Mapping[str, Any]) -> list[dict[str, Any]]:
    found: list[Any] = []
    for key in ("issues", "in_hand", "earlier", "contributors", "options"):
        found += [item.get("link_ref") for item in row.get(key) or ()]
    found.append((row.get("evidence_link") or {}).get("link_ref"))
    seen, out = set(), []
    for r in found:
        if not r:
            continue
        k = json.dumps(r, sort_keys=True, default=str)
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out


def outcomes_of(board_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """The board composition's rows (`assemble(facts)`), with their link Refs and `thread_lines` (§B1)."""
    return [{"category": r["category"], "state": r["state"], "state_label": r["state_label"],
             "headline": r.get("headline"), "thread_lines": list(r.get("thread_lines") or ()),
             "refs": _row_refs(r),
             # CH-6a3 §A5: the row's node claims, copied (absent on a row built before CH-6a3 -> null nodes).
             "nodes": dict(r.get("nodes") or {"kpi": None, "earnings": None, "potential": None}),
             "target_note": r.get("target_note")} for r in board_rows]
