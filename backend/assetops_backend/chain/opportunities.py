"""CH-4 (build sheet CH-4 §2.1): the opportunity items, one shape shared by Findings › Opportunities, the Portfolio
`opportunity` block and the Site board's OPPORTUNITY issue. `opportunity_items` is the only derivation of "seen in
the period" and of the item copy; both read adapters feed it the rows of `lookup.OPPORTUNITY_LOOKUP`. Pure."""

from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Callable, Sequence
from zoneinfo import ZoneInfo

from assetops_backend.chain import lifecycle as lc
from assetops_backend.chain import vocabulary as v
from assetops_backend.estate.coverage import DOMAIN_OF_SITE_TYPE
from assetops_backend.outcomes.outcome_map import categories_for, lens_flags, thread_signal_key

_US = timedelta(microseconds=1)
_FILTER_STATE = {"SUPPORTED": "supported", "LIMITED": "unconfirmed", "UNKNOWN": "unconfirmed"}


def _at(value: Any) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _d(value: Any) -> date | None:
    if value is None or isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _utc_z(day: date, tz: str) -> str:
    return datetime.combine(day, time.min, tzinfo=ZoneInfo(tz)).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def opportunity_items(rows: Sequence[Any], window_from: datetime, window_to: datetime, k: datetime | None,
                      close_after: int | Callable[[str | None], int] = 7) -> list[dict[str, Any]]:
    """`OPPORTUNITY_LOOKUP` rows -> one item per opportunity thread seen in `[window_from, window_to)` (each Site's
    own local days, AG-27) as of `k` (None = as known now). §2.1: an occurrence is visible when
    `coalesce(source_known_at, joined_at) <= k`; its study head is the latest selection with `selected_at <= k`; it
    is seen when its episode meets the window's local days and the head has at least one eligible day; the item is
    built from the thread's latest seen study; `state` is the thread state on the local day of `window_to − 1 µs`."""
    occ: dict[tuple[str, str], tuple[Any, ...]] = {}
    events: dict[str, list[lc.Event]] = {}
    for row in rows:
        kind, ref, thread_id, num, _cnt, at1, at2, tz, mechanism, txt3, day1 = tuple(row)[:11]
        if kind == "E":
            events.setdefault(thread_id, []).append(lc.Event(int(num), tz, mechanism, ref, day1, at1, at2))
            continue
        if kind != "O":
            continue
        study = json.loads(txt3) if isinstance(txt3, str) else dict(txt3 or {})
        site_type = tuple(row)[11] if len(tuple(row)) > 11 else None
        known = _at(study.get("source_known_at")) or _at(study.get("joined_at"))
        if k is not None and known is not None and known > k:
            continue
        selected = _at(study.get("selected_at"))
        if k is not None and selected is not None and selected > k:
            continue
        key = (str(thread_id), str(ref).lower())
        rank = (selected or datetime.min.replace(tzinfo=timezone.utc), int(study.get("seq") or 0))
        prior = occ.get(key)
        if prior is None or rank > prior[0]:
            occ[key] = (rank, int(num), at1, at2, tz, mechanism, study, site_type)
    by_thread: dict[str, list[tuple[str, tuple[Any, ...]]]] = {}
    for (tid, oid), o in occ.items():
        by_thread.setdefault(tid, []).append((oid, o))
    items: list[dict[str, Any]] = []
    for tid, occs in by_thread.items():
        seen = []
        for oid, (_, num, start, end, tz, mechanism, study, site_type) in occs:
            if int(study.get("eligible_days") or 0) < 1 or start is None or not tz:
                continue
            lo_day = lc.local_day(window_from, tz)
            hi_day = lc.local_day(window_to - _US, tz)
            first = lc.local_day(start, tz)
            last = lc.local_day((end or start + timedelta(days=1)) - _US, tz)
            if first <= hi_day and last >= lo_day:
                seen.append((oid, num, start, tz, mechanism, study, site_type))
        if not seen:
            continue
        oid, num, start, tz, mechanism, study, site_type = max(
            seen, key=lambda x: (_d(x[5]["last_day"]), int(x[5].get("public_no") or 0)))
        on = lc.local_day(window_to - _US, tz)
        view = lc.thread_view(events.get(tid, []), lc.Occurrence(oid, lc.local_day(start, tz)), on, k, (),
                              close_after(site_type) if callable(close_after) else close_after)
        items.append(_item(tid, oid, len(occs), view, on, tz, mechanism, study, site_type))
    items.sort(key=lambda i: (i["site_code"], -_d(i["study"]["last_day"]).toordinal(), i["study"]["code"]))
    return items


def _item(tid: str, oid: str, occurrences: int, view: dict[str, Any], on: date, tz: str, mechanism: str,
          study: dict[str, Any], site_type: str | None) -> dict[str, Any]:
    code, name = study["site_code"], study["site_name"]
    first, last = _d(study["first_day"]), _d(study["last_day"])
    status = study.get("status")
    eligible, assessed = int(study.get("eligible_days") or 0), int(study.get("assessed_days") or 0)
    headroom = study.get("headroom_kw")
    state = view["state"]
    eff = view["state_effective_day"]
    signal = thread_signal_key(mechanism)
    domain = DOMAIN_OF_SITE_TYPE.get(site_type or "", "")
    study_code = f"OPP-{int(study['public_no']):06d}"
    return {
        "thread_id": tid, "site_id": study.get("site_id"), "site_code": code, "site_name": name,
        "mechanism": mechanism, "domain": site_type,
        "title": v.OPP_TITLE[mechanism].format(site=name), "short_label": v.OPP_SHORT[mechanism].format(site=name),
        "state": state, "state_label": v.THREAD_STATE_WORDS.get(state or ""),
        "state_effective_day": None if eff is None else eff.isoformat(), "state_day": on.isoformat(),
        "occurrences": occurrences,
        "study": {"opportunity_id": oid, "code": study_code, "first_day": first.isoformat(),
                  "last_day": last.isoformat(), "status": status, "eligible_days": eligible,
                  "assessed_days": assessed, "headroom_kw": headroom, "window_hours": 1},
        "evidence": status, "evidence_label": v.EVIDENCE_LABEL.get(status or ""),
        "seen_line": v.seen_line(eligible, assessed, first, last),
        "value_line": v.value_line(status, headroom),
        "limit_line": v.limit_line(status, study.get("limitation_codes") or (), study.get("decisions") or ()),
        "lens_flags": lens_flags(signal, domain), "categories": categories_for(signal, domain),
        "filter_state": "no_longer_supported" if state == "WITHDRAWN" else _FILTER_STATE.get(status or "", "unconfirmed"),
        "links": {"opportunity": f"/sites/{code}/opportunities/{oid}",
                  "evidence": (f"/sites/{code}/performance/renewable?from={_utc_z(first, tz)}"
                               f"&to={_utc_z(last + timedelta(days=1), tz)}"),
                  "site": f"/sites/{code}"},
        "ref": {"kind": "OPPORTUNITY", "site": code, "id": oid},
        "thread_ref": {"kind": "THREAD", "site": code, "id": tid}}
