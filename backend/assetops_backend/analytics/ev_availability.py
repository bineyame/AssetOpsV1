"""W5-03a E1a: the selected observed connector-availability calculation, `ev-availability/1`.

A bounded observed-state proxy, labelled `Observed connector state`, never a physical availability certification.
Two independent facts: each enabled connector's configured service seconds (the selected time-valid Foundation's
own schedule, clipped to the half-open window) and the accepted, selected `ev_connector_state` transitions bound to
that connector. A transition classifies only its own observation interval `[event_time, min(next transition,
event_time + ev-status-cadence, window end))`; everything else scheduled is Unknown. Sessions, faults or the
schedule alone never fill the observed numerator.

Pure: the caller reads the Foundation revision, assets and accepted rows on its one selected snapshot connection
(`EvReadService.foundation_revision_on`, `assets_on`, `accepted_on`); this module holds no SQL and no I/O.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from typing import Any

from assetops_backend.analytics.ev import plain
from assetops_backend.ev_site_reads import _seconds, connector_service_windows

CALCULATION_VERSION = "ev-availability/1"
STATE_ROLE = "ev_connector_state"
AVAILABLE = "AVAILABLE"
UNAVAILABLE = "UNAVAILABLE"
UNKNOWN = "UNKNOWN"
#: The reported connector state -> the classified category; anything else (PLUGGED, AUTHORIZING, CHARGING or an
#: unrecognised value) is Unknown. A charging state alone does not prove the connector was available.
CATEGORY = {"AVAILABLE": AVAILABLE, "UNPLUGGED": AVAILABLE, "FAULTED": UNAVAILABLE, "DISABLED": UNAVAILABLE}
SCHEDULED, DECLARED_EMPTY, NOT_ESTABLISHED = "SCHEDULED", "DECLARED_EMPTY", "NOT_ESTABLISHED"
CADENCE_KEY = "ev-status-cadence"
_QUANT = Decimal("0.000001")
_ZERO = timedelta(0)

Span = tuple[datetime, datetime]


def ratio(num: Any, den: Any) -> str | None:
    """`Decimal(num) / Decimal(den)` quantized to six places, ROUND_HALF_EVEN; None for a null or zero denominator."""
    if num is None or den is None or Decimal(str(den)) == 0:
        return None
    return str((Decimal(str(num)) / Decimal(str(den))).quantize(_QUANT, rounding=ROUND_HALF_EVEN))


def selected_rows(accepted: list[dict[str, Any]], snap: dict[str, Any]) -> list[dict[str, Any]] | None:
    """The accepted rows inside the selected head's cited set (lowercase IDs), or None with no selected head: no
    pending-only or post-selection row classifies a second."""
    sel = snap.get("selected")
    if sel is None:
        return None
    ids = {str(x).lower() for x in sel["evidence_ids"]}
    return [r for r in accepted if str(r.get("evidence_id")).lower() in ids]


def selected_foundation(revision: dict[str, Any] | None, snap: dict[str, Any], lo: datetime | None,
                        hi: datetime | None) -> dict[str, Any] | None:
    """The selected head's own time-valid Foundation revision, else None. A missing head, zero or several
    `foundation_ids`, a revision that is not that single ID, or a validity that does not cover `[lo,hi)` is not
    established; a later effective revision is never substituted."""
    sel = snap.get("selected")
    if sel is None or revision is None or lo is None or hi is None or len(sel["foundation_ids"]) != 1:
        return None
    if str(sel["foundation_ids"][0]).lower() != str(revision["id"]).lower():
        return None
    start, end = revision.get("valid_from"), revision.get("valid_to")
    if not _utc(start) or start > lo or (end is not None and (not _utc(end) or end < hi)):
        return None
    return revision


def _utc(at: Any) -> bool:
    return isinstance(at, datetime) and at.utcoffset() == _ZERO


def _cadence(component: dict[str, Any]) -> timedelta | None:
    """The connector's `ev-status-cadence` in minutes as exact seconds (Decimal, no binary float), else None."""
    items = [p for p in component.get("properties") or () if p.get("property_key") == CADENCE_KEY]
    if len(items) != 1 or items[0].get("unit") != "min":
        return None
    try:
        minutes = Decimal(str(items[0].get("value")))
    except (InvalidOperation, ValueError):
        return None
    if not minutes.is_finite() or minutes <= 0:
        return None
    micro = minutes * 60 * 1_000_000
    if micro != micro.to_integral_value():
        return None
    return timedelta(microseconds=int(micro))


def _usable(row: dict[str, Any], component_id: str) -> bool:
    """A selected state row that may classify time: not EXCLUDED, GOOD, clock attested, UTC source/sent/receipt
    instants with receipt not before source or send, and a connector ID that is absent or this component's."""
    if row.get("use") == "EXCLUDED" or row.get("quality") != "GOOD" or row.get("reason") == "CLOCK_UNATTESTED":
        return False
    source, sent, received = row.get("source_time"), row.get("sent_at"), row.get("received_at")
    if not (_utc(source) and _utc(sent) and _utc(received)) or received < source or received < sent:
        return False
    connector = row.get("connector_id")
    return connector is None or str(connector) == component_id


def _observations(rows: list[dict[str, Any]], component_id: str, cadence: timedelta | None,
                  hi: datetime) -> list[tuple[datetime, datetime, str, list[str]]]:
    """Classified observation intervals `(from, to, category, evidence_ids)` from one connector's rows. Equal-time
    rows form one transition: equal values merge, different values (or an unusable row) conflict and that whole
    cadence-sized interval is Unknown. Evidence-ID order never chooses a winner."""
    ordered = sorted(rows, key=lambda r: (r["source_time"], str(r["evidence_id"]).lower()))
    groups: list[tuple[datetime, list[dict[str, Any]]]] = []
    for r in ordered:
        if groups and groups[-1][0] == r["source_time"]:
            groups[-1][1].append(r)
        else:
            groups.append((r["source_time"], [r]))
    out = []
    for i, (at, group) in enumerate(groups):
        if cadence is None:
            continue
        end = min(at + cadence, hi)
        if i + 1 < len(groups):
            end = min(end, groups[i + 1][0])
        if end <= at:
            continue
        values = {str(r.get("value")) for r in group}
        usable = all(_usable(r, component_id) for r in group)
        category = CATEGORY.get(values.pop(), UNKNOWN) if usable and len(values) == 1 else UNKNOWN
        ids = sorted({str(r["evidence_id"]).lower() for r in group}) if category != UNKNOWN else []
        out.append((at, end, category, ids))
    return out


def _classify(windows: list[Span], observations) -> list[dict[str, Any]]:
    """Ordered spans over the scheduled windows: each classified observation clipped to them, Unknown elsewhere,
    adjacent equal-state spans unioned (their evidence IDs too)."""
    pieces: list[tuple[datetime, datetime, str, list[str]]] = []
    for a, b in windows:
        cursor = a
        for start, end, category, ids in observations:
            s, e = max(start, a), min(end, b)
            if e <= s or category == UNKNOWN:
                continue
            if s > cursor:
                pieces.append((cursor, s, UNKNOWN, []))
            pieces.append((s, e, category, ids))
            cursor = e
        if cursor < b:
            pieces.append((cursor, b, UNKNOWN, []))
    merged: list[list[Any]] = []
    for s, e, category, ids in pieces:
        if merged and merged[-1][1] == s and merged[-1][2] == category:
            merged[-1][1] = e
            merged[-1][3] = sorted(set(merged[-1][3]) | set(ids))
        else:
            merged.append([s, e, category, list(ids)])
    return [{"from": s, "to": e, "state": category, "evidence_ids": ids} for s, e, category, ids in merged]


def _measure(spans: list[dict[str, Any]], state: str | None = None) -> timedelta:
    return sum((x["to"] - x["from"] for x in spans if state is None or x["state"] == state), _ZERO)


def availability(foundation: dict[str, Any] | None, assets: dict[str, str], accepted: list[dict[str, Any]] | None,
                 lo: datetime | None, hi: datetime | None) -> dict[str, Any]:
    """The `availability` wire object. `foundation` is the selected time-valid revision (`selected_foundation`) or
    None (not established); `accepted` the selected accepted rows (`selected_rows`) or None with no selected head.
    With no established schedule every count and rate is null; a declared `weekly: []` is zero seconds with null
    rates; never 0% or 100% by default."""
    components = {} if foundation is None else {
        c.get("component_id"): c for c in foundation["content"].get("components") or ()
        if c.get("component_type") == "EV_CONNECTOR"}
    windows = [] if foundation is None or lo is None or hi is None or accepted is None else \
        connector_service_windows(foundation, assets, lo, hi)
    kinds = [w["schedule"] for w in windows]
    if not kinds or "NONE" in kinds:
        state = NOT_ESTABLISHED
    elif "WEEKLY" in kinds:
        state = SCHEDULED
    else:
        state = DECLARED_EMPTY
    rows = []
    for w in windows:
        component = components.get(w["component_id"]) or {}
        label = component.get("display_name") or w["component_id"]
        row: dict[str, Any] = {"asset_id": w["asset_id"], "label": label, "scheduled_seconds": None,
                               "known_available_seconds": None, "known_unavailable_seconds": None,
                               "unknown_seconds": None, "spans": []}
        if state != NOT_ESTABLISHED:
            mine = [r for r in accepted or () if r.get("role") == STATE_ROLE
                    and str(r.get("asset_id")).lower() == str(w["asset_id"]).lower()]
            spans = _classify(w["windows"], _observations(mine, w["component_id"], _cadence(component), hi))
            row.update({"scheduled_seconds": _seconds(_measure(spans)),
                        "known_available_seconds": _seconds(_measure(spans, AVAILABLE)),
                        "known_unavailable_seconds": _seconds(_measure(spans, UNAVAILABLE)),
                        "unknown_seconds": _seconds(_measure(spans, UNKNOWN)),
                        "spans": [{**x, "from": plain(x["from"]), "to": plain(x["to"])} for x in spans]})
        rows.append(row)
    rows.sort(key=lambda r: (r["label"], r["asset_id"]))
    keys = ("scheduled_seconds", "known_available_seconds", "known_unavailable_seconds", "unknown_seconds")
    totals = {k: None if state == NOT_ESTABLISHED else _sum(r[k] for r in rows) for k in keys}
    available, unavailable = totals["known_available_seconds"], totals["known_unavailable_seconds"]
    scheduled, unknown = totals["scheduled_seconds"], totals["unknown_seconds"]
    known = None if available is None else Decimal(str(available)) + Decimal(str(unavailable))
    return {
        "calculation_version": CALCULATION_VERSION,
        "schedule_state": state,
        **totals,
        "known_time_ratio": None if not known else ratio(available, known),
        "full_lower": ratio(available, scheduled),
        "full_upper": None if scheduled is None else ratio(Decimal(str(available)) + Decimal(str(unknown)), scheduled),
        "connectors": rows,
    }


def _sum(values) -> int | float:
    return _seconds(sum((timedelta(seconds=v) for v in values), _ZERO))


def availability_on(reads: Any, c: Any, snap: dict[str, Any]) -> dict[str, Any]:
    """`availability` over one selected snapshot connection `c`: the selected head's own time-valid Foundation
    revision, the Site's assets and the accepted rows intersected with the selected cited set."""
    lo, hi = snap["lo"], snap["hi"]
    revision = selected_foundation(reads.foundation_revision_on(c, snap), snap, lo, hi)
    rows = selected_rows(reads.accepted_on(c, snap), snap)
    return availability(revision, reads.assets_on(c, snap), rows, lo, hi)
