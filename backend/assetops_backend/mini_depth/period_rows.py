"""ANY-1 AR-2: the board's mini depth served from stored read-period rows (architect answer 2026-11-10 §4; D-ANY.1-6).

Kinds `mini_depth.{renewable,fuel,service,backup}` (`site_period_read`, migration 0059). Each row body holds the hour
facts today's `MiniDepthRead._hour` derives on every page view - the selected head, the overlapping live jobs, the
"has an input changed since the selection" answer of `_cutoff_sha`, and the pending accepted IDs - computed once when
the inputs change (event register -> `snapshot_dirty` -> builder in the tick, or the backfill CLI), never on read.

- `mini_depth.renewable`: one row per Site-local day (period = the local day), its hours = that day's measured
  daylight and missing hours (`hour_windows` over the whole day, `store.daylight_hours` at build time). A day row, not
  one row per hour, so a day with no expected hour is a stored empty list rather than an absent row.
- `mini_depth.{fuel,service,backup}`: one row per Site-local day for the hour the board reads (local noon,
  `site_outcomes/mini.py:_depth`), period = that hour.
- Provenance: the link rows of a selected revision's exact accepted-ID set are stored once per revision in
  `revision_provenance` (`{"link_rows": [...]}`); a live job's pending IDs keep theirs in the hour body. The read
  resolves the same `mini_blocks` over them, so the classification and digests are today's.

The envelope itself is still composed per request by `mini_depth/read.py` from these facts (a request-time
`known_at`, HISTORICAL and the aggregate across days are request properties), with the functions today's compose uses.
"""

from __future__ import annotations

from dataclasses import fields
from datetime import date, datetime, timedelta
from typing import Any, Iterable, Mapping, Sequence
from uuid import UUID

from assetops_backend.chain.period_read import PeriodFragment
from assetops_backend.evidence.source_provenance import LinkRow

KIND_PREFIX = "mini_depth."
#: One version for the four kinds: their provenance blocks share it (`revision_provenance` key).
BUILDER_VERSION = "mini-depth-rows-2"  # 2: the stored hour carries `missing` (D-SR.62)
KINDS: tuple[str, ...] = tuple(f"{KIND_PREFIX}{d}" for d in ("renewable", "fuel", "service", "backup"))
_LINK_FIELDS = tuple(f.name for f in fields(LinkRow))
_TUPLE_FIELDS = frozenset({"evidence_gateway_source", "batch", "link", "publication"})


def kind_of(domain: str) -> str:
    return f"{KIND_PREFIX}{domain}"


def link_row_json(row: LinkRow) -> list[Any]:
    """A link row as a positional JSON list (the dataclass field order)."""
    return [list(v) if isinstance(v, tuple) else v for v in (getattr(row, n) for n in _LINK_FIELDS)]


def link_row_from_json(values: Sequence[Any]) -> LinkRow:
    if len(values) != len(_LINK_FIELDS):
        raise ValueError("A stored link row does not match the LinkRow fields.")
    return LinkRow(**{n: (tuple(v) if n in _TUPLE_FIELDS and v is not None else v)
                      for n, v in zip(_LINK_FIELDS, values)})


def group_link_rows(rows: Iterable[LinkRow]) -> dict[str, list[list[Any]]]:
    """Link rows by lowercase requested ID, each ID's rows in the adapter's order."""
    out: dict[str, list[list[Any]]] = {}
    for r in rows:
        out.setdefault(str(r.requested_id).lower(), []).append(link_row_json(r))
    return out


class StoredLinkRows:
    """A `LinkRowsOn` over stored link rows: the rows of each requested ID, in the requested order. An ID with no
    stored rows is a broken store (503), never a guessed "not found"."""

    def __init__(self, by_id: Mapping[str, Sequence[Sequence[Any]]]) -> None:
        self._by_id = {str(k).lower(): v for k, v in by_id.items()}

    def __call__(self, _c: Any, _t: UUID, _s: UUID, evidence_ids: list[str]) -> list[LinkRow]:
        from assetops_backend.mini_depth.read import MiniReadUnavailable

        out: list[LinkRow] = []
        for i in evidence_ids:
            stored = self._by_id.get(str(i).lower())
            if stored is None:
                raise MiniReadUnavailable("A stored mini-depth provenance row is missing.")
            out.extend(link_row_from_json(v) for v in stored)
        return out


def hour_json(h: Any, *, pending_link_rows: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """One `read._Hour` as stored facts. The stored `state` is the build-time live state (never HISTORICAL)."""
    from assetops_backend.mini_depth.read import iso

    head = None
    if h.head is not None:
        head = {"seq": h.head.seq, "revision_id": str(h.head.revision_id),
                "knowledge_cutoff": iso(h.head.knowledge_cutoff), "input_sha256": h.head.input_sha256,
                "result": h.head.result, "evidence_ids": list(h.head.evidence_ids)}
    return {"local_day": h.day.isoformat(), "window_start": iso(h.window.start), "window_end": iso(h.window.end),
            "head": head, "job_state": h.job_state, "state": h.state,
            "pending_ids": None if h.pending_ids is None else list(h.pending_ids), "job_ids": list(h.job_ids),
            "pending_link_rows": None if h.pending_ids is None else dict(pending_link_rows or {}),
            "missing": bool(h.missing)}


def _instant(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def hour_from_json(value: Mapping[str, Any], *, historical: bool, pending: bool) -> Any:
    """A stored hour as `read._Hour` at a request: CURRENT reads HISTORICAL for an explicit earlier cutoff (as
    `_hour`), and a period PENDING at k (an unconsumed input event, a live dirty mark or an older builder version)
    reads PENDING_RECOMPUTE over its stored head (architect answer §4 "Late and corrected data")."""
    from assetops_backend.mini_depth import rules
    from assetops_backend.mini_depth.read import _Head, _Hour

    head = value.get("head")
    h = None
    if head is not None:
        h = _Head(int(head["seq"]), UUID(head["revision_id"]), _instant(head["knowledge_cutoff"]),
                  head["input_sha256"], head["result"], tuple(head["evidence_ids"]))
    state = value["state"]
    if pending and h is not None:
        state = "PENDING_RECOMPUTE"
    elif state == "CURRENT" and historical:
        state = "HISTORICAL"
    pending_ids = value.get("pending_ids")
    return _Hour(date.fromisoformat(value["local_day"]),
                 rules.Window(_instant(value["window_start"]), _instant(value["window_end"])), h,
                 value["job_state"], state, None if pending_ids is None else tuple(pending_ids),
                 tuple(value.get("job_ids") or ()), bool(value.get("missing")))


def absent_hour(day: date, window: Any) -> Any:
    """D-ANY.5 M1: no stored row at k renders as today's compose renders no selection visible at k."""
    from assetops_backend.mini_depth.read import _Hour

    return _Hour(day, window, None, "NONE", "UNKNOWN", None, ())


def absent_renewable_windows(site_code: str, tz_name: str, day: date) -> list[tuple[date, Any]]:
    """The hours `store.daylight_hours` gives a day with nothing known at k: none outside the declared operating
    period, else the no-binding hours (configuration only, no reading read)."""
    from zoneinfo import ZoneInfo

    from assetops_backend.chain.composition import load_operating_calendar
    from assetops_backend.chain.grading import period_bounds
    from assetops_backend.chain.policy import PERIOD_OPERATING_HOURS
    from assetops_backend.mini_depth.inputs import local_hour
    from assetops_backend.mini_depth.store import NO_PV_BINDING

    bounds = period_bounds(load_operating_calendar().entry_for(site_code), ZoneInfo(tz_name), day,
                           PERIOD_OPERATING_HOURS)
    if bounds is None:
        return []
    return [(day, local_hour(day, h, tz_name)) for h in sorted({*NO_PV_BINDING.hours, *NO_PV_BINDING.missing})]


class MiniDepthKindBuilder:
    """`chain.period_read.KindBuilder` for one mini depth kind, over the read-only `MiniDepthRead` (its own `_hour`,
    the compose's per-hour logic, at the build transaction's clock)."""

    builder_version = BUILDER_VERSION

    def __init__(self, domain: str, mini: Any) -> None:
        self.domain = domain
        self.kind = kind_of(domain)
        self._mini = mini

    def fragments(self, ctx: Any, site: Any) -> Sequence[PeriodFragment]:
        built = self._mini.build_period(tenant_id=ctx.tenant_id, site_id=site.site_id, domain=self.domain,
                                        local_day=ctx.local_day)
        if built is None:
            return []
        start, end, hours, provenance = built
        body = {"hours": hours}
        states = [h["state"] for h in hours] or ["UNKNOWN"]
        from assetops_backend.mini_depth.read import aggregate_state

        return [PeriodFragment(start, end, aggregate_state(states), body, inputs=body,
                               provenance={UUID(k): {"link_rows": v} for k, v in provenance.items()})]


def kind_builders(mini: Any) -> dict[str, MiniDepthKindBuilder]:
    from assetops_backend.mini_depth.store import DOMAINS

    return {kind_of(d): MiniDepthKindBuilder(d, mini) for d in DOMAINS}


def day_span(first: date, n: int) -> list[date]:
    return [first + timedelta(days=i) for i in range(n)]


__all__ = ["BUILDER_VERSION", "KINDS", "MiniDepthKindBuilder", "StoredLinkRows", "absent_hour",
           "absent_renewable_windows", "group_link_rows", "hour_from_json", "hour_json", "kind_builders", "kind_of",
           "link_row_from_json", "link_row_json"]
