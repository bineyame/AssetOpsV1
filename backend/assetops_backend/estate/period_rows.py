"""ANY-2 AR-4: Portfolio evidence served from stored read-period rows (architect answer 2026-11-10 §4; D-ANY.1-6).

Phase 1 (this module): kind `evidence.claim`, the mini-grid Evidence row's W1 claim-limit day.

- What is slow today: for every UTC claim day of every mini-grid Site in the requested range, `claim_limit_on` loads
  the selected window revision's full detail (run, every INTERVAL revision, the accepted Evidence) and
  `cited_provenance` resolves the link rows of every cited accepted ID. Both are facts of one exact window revision
  and never change for it.
- What is stored: one row per (Site, UTC claim day) - period = the UTC day, `local_day` = its date - whose body is
  the day's selected window revision ID and that revision's exact `_revision_detail` (tagged JSON, so dates, UUIDs
  and Decimals come back as the same types), built when its inputs change (register -> `snapshot_dirty` -> builder,
  or the backfill CLI). The link rows of the revision's interval Evidence are stored once per revision in
  `revision_provenance` (`{"link_rows": {id: [row, ...]}}`).
- What is read: the request's own dispatch day (the row `select_dispatch_days_on` gave the page; never stored here,
  AR-3 owns `dispatch.day`) plus the stored detail go through `ClaimLimitReadService.project_claim_limit`, the pure
  half of `claim_limit_on`, at the request's `known_at` and basis mode. The provenance projection runs today's
  `PublicProvenance.cited_set` over the stored link rows. So every value and word is today's.
- A day is served from its row only when the row exists at k, is not PENDING at k (an unconsumed input event, a live
  dirty mark, an older builder version on any Site-local day the UTC day touches) and names the same window revision
  as the page's dispatch day. Any other day is read as today (`claim_limit_on`), logged `period_row_absent` and
  counted (`row_misses()`): the stored rows decide nothing they were not built for.
- Rulings applied: a day whose page selection names no revision is projected with no stored input and no compose
  (D-ANY.5: absence renders as today renders no stored input). A row that exists but cannot be proven equal
  (PENDING on a touched local day, an older builder, another revision) is read as today for that day only, logged and
  counted (D-ANY.6a, the D-ANY.1 rule). OPEN Architect question: the page selected a revision (its dispatch day is
  still composed live, AR-3's `dispatch.day`) but no row is known at k. The claim-limit contract has no NO_DATA
  state that would not contradict the page's own selection, so that day is also read as today and flagged.
"""

from __future__ import annotations

import logging
from dataclasses import fields
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any, Callable, Iterable, Mapping, Sequence
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import text

from assetops_backend.chain.period_read import ABSENT_LOG_EVENT, PeriodFragment, served_kinds
from assetops_backend.evidence.source_provenance import LinkRow

LOG = logging.getLogger("assetops.estate.period_rows")
KIND_CLAIM = "evidence.claim"
#: Declared for the next phase (cold/EV pinned-window provenance, money lines with receipts); not built here.
KIND_PROVENANCE, KIND_MONEY = "evidence.provenance", "money.lines"
KINDS: tuple[str, ...] = (KIND_CLAIM,)
BUILDER_VERSION = "estate-evidence-rows-1"
MINIGRID = "MINIGRID"
_MISSES = [0]


def row_misses() -> int:
    """Claim days read as today because no current row could serve them, since process start."""
    return _MISSES[0]


# --- tagged JSON: the stored detail comes back as the same Python types ------------------------------------------

_TAGS = frozenset({"$t", "$d", "$u", "$n", "$l"})


def encode(value: Any) -> Any:
    if isinstance(value, datetime):
        return {"$t": value.isoformat()}
    if isinstance(value, date):
        return {"$d": value.isoformat()}
    if isinstance(value, UUID):
        return {"$u": str(value)}
    if isinstance(value, Decimal):
        return {"$n": str(value)}
    if isinstance(value, tuple):
        return {"$l": [encode(v) for v in value]}
    if isinstance(value, list):
        return [encode(v) for v in value]
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if not isinstance(k, str) or k in _TAGS:
                raise ValueError(f"A stored key must be a plain string, not {k!r}.")
            out[k] = encode(v)
        return out
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise ValueError(f"A {type(value).__name__} cannot be stored in a period row.")


def decode(value: Any) -> Any:
    if isinstance(value, list):
        return [decode(v) for v in value]
    if isinstance(value, dict):
        if len(value) == 1 and next(iter(value)) in _TAGS:
            tag, v = next(iter(value.items()))
            return {"$t": datetime.fromisoformat, "$d": date.fromisoformat, "$u": UUID, "$n": Decimal,
                    "$l": lambda xs: tuple(decode(x) for x in xs)}[tag](v)
        return {k: decode(v) for k, v in value.items()}
    return value


_LINK_FIELDS = tuple(f.name for f in fields(LinkRow))


def link_row_encode(row: LinkRow) -> dict[str, Any]:
    return encode({n: getattr(row, n) for n in _LINK_FIELDS})


def link_row_decode(value: Mapping[str, Any]) -> LinkRow:
    raw = decode(dict(value))
    if set(raw) != set(_LINK_FIELDS):
        raise ValueError("A stored link row does not match the LinkRow fields.")
    return LinkRow(**raw)


# --- days ---------------------------------------------------------------------------------------------------------

def utc_days(lo: datetime, hi: datetime) -> list[date]:
    """The UTC dates whose day intersects `[lo, hi)` (the claim days `select_dispatch_days_on` would return)."""
    out, day = [], lo.astimezone(timezone.utc).date()
    while datetime.combine(day, time(0), timezone.utc) < hi:
        if datetime.combine(day + timedelta(days=1), time(0), timezone.utc) > lo:
            out.append(day)
        day += timedelta(days=1)
    return out


def local_days_of(day: date, tz: str) -> list[date]:
    """The Site-local dates the UTC day `day` touches (the register dirties local days)."""
    zone = ZoneInfo(tz)
    lo = datetime.combine(day, time(0), timezone.utc)
    hi = lo + timedelta(days=1) - timedelta(microseconds=1)
    first, last = lo.astimezone(zone).date(), hi.astimezone(zone).date()
    return [first + timedelta(days=i) for i in range((last - first).days + 1)]


def day_revision(day: Mapping[str, Any]) -> Any:
    """The window revision a dispatch day selects (`mini_grid_rows`' rule): None when unavailable or unselected."""
    return day.get("window_assessment_revision_id") if day.get("available") and day.get("selection") is not None \
        else None


def _key(value: Any) -> str | None:
    return None if value is None else str(value).lower()


def interval_evidence_ids(detail: Mapping[str, Any] | None) -> list[str]:
    run = (detail or {}).get("run") or {}
    return sorted({str(e).lower() for r in run.get("revisions") or () if r.get("scope") == "INTERVAL"
                   for e in r.get("evidence_ids") or ()})


# --- the builder --------------------------------------------------------------------------------------------------

class EvidenceClaimKindBuilder:
    """`chain.period_read.KindBuilder` for `evidence.claim` over the read-only estate Evidence reader
    (`PostgresEvidenceMoneyRead`): its one-transaction snapshot, the dispatch-day selection and the exact revision
    detail `claim_limit_snapshot_on` loads, and the link rows `cited_provenance` resolves."""

    kind = KIND_CLAIM
    builder_version = BUILDER_VERSION

    def __init__(self, estate_read: Any | Callable[[], Any]) -> None:
        self._estate = estate_read

    def _read(self) -> Any:
        return self._estate() if callable(self._estate) and not hasattr(self._estate, "read") else self._estate

    def fragments(self, ctx: Any, site: Any) -> Sequence[PeriodFragment]:
        if site.site_type != MINIGRID:
            return []
        days = utc_days(ctx.period_start_utc, ctx.period_end_utc)
        return self._read().read(lambda snap: [self.fragment(snap, ctx.tenant_id, site.site_id, d) for d in days])

    def fragment(self, snap: Any, t: UUID, s: UUID, day: date) -> PeriodFragment:
        lo = datetime.combine(day, time(0), timezone.utc)
        hi = lo + timedelta(days=1)
        found = [d for d in snap.dispatch_days(t, s, lo, hi, snap.read_at) if d.get("day") == day]
        rid = day_revision(found[0]) if found else None
        detail = None
        provenance: dict[UUID, dict[str, Any]] = {}
        if rid is not None:
            detail = snap._o.claim_limits.store.claim_limit_snapshot_on(snap._c, t, s, day, rid, snap.read_at)[1]
            ids = interval_evidence_ids(detail)
            if detail is not None:
                grouped: dict[str, list[dict[str, Any]]] = {i: [] for i in ids}
                for row in (snap._o.provenance_reads(snap._c).link_rows(t, s, ids) if ids else ()):
                    grouped.setdefault(str(row.requested_id).lower(), []).append(link_row_encode(row))
                provenance[UUID(str(rid))] = {"link_rows": grouped}
        state = "NO_DAY" if not found else "UNASSESSED" if rid is None else "SELECTED"
        body = {"day": day.isoformat(), "revision_id": _key(rid), "detail": encode(detail)}
        return PeriodFragment(lo, hi, state, body, inputs=body, provenance=provenance, local_day=day)


def kind_builders(estate_read: Any) -> dict[str, EvidenceClaimKindBuilder]:
    return {KIND_CLAIM: EvidenceClaimKindBuilder(estate_read)}


def kind_versions() -> dict[str, str]:
    return {k: BUILDER_VERSION for k in KINDS}


# --- the read -----------------------------------------------------------------------------------------------------

class EvidenceRows:
    """The `(reader, store)` pair the estate Evidence reader serves `evidence.claim` days from (None kinds served =
    today's compose everywhere; `ASSETOPS_PERIOD_READ_KINDS` is the kill switch)."""

    def __init__(self, reader: Any, store: Any) -> None:
        self.reader, self.store = reader, store

    def request(self, snap: Any) -> "RequestRows | None":
        return RequestRows(self, snap) if KIND_CLAIM in served_kinds() else None


class RequestRows:
    """One estate snapshot's stored claim days: the page's own dispatch days are noted as `dispatch_days` returns
    them; the first claim day of a Site reads that Site's rows over the noted range (one reader read, one
    provenance statement)."""

    def __init__(self, rows: EvidenceRows, snap: Any) -> None:
        self._rows, self._snap = rows, snap
        self._days: dict[tuple[str, date, datetime], dict[str, Any]] = {}
        self._ranges: dict[str, tuple[UUID, datetime, datetime, datetime]] = {}
        self._loaded: dict[str, tuple[dict[date, dict[str, Any]], dict[str, list[LinkRow]]]] = {}
        self.statements = 0

    def note_days(self, t: UUID, s: UUID, from_: datetime, to: datetime, k: datetime,
                  days: Iterable[Mapping[str, Any]]) -> None:
        sid = str(s).lower()
        for d in days:
            if isinstance(d.get("day"), date):
                self._days[(sid, d["day"], k)] = dict(d)
        lo, hi = (from_, to) if sid not in self._ranges else (min(from_, self._ranges[sid][1]),
                                                               max(to, self._ranges[sid][2]))
        if sid in self._ranges and (lo, hi) != self._ranges[sid][1:3]:
            self._loaded.pop(sid, None)  # a wider range than loaded: reload on the next claim day
        self._ranges[sid] = (t, lo, hi, k)

    def _load(self, sid: str) -> tuple[dict[date, dict[str, Any]], dict[str, list[LinkRow]]]:
        if sid in self._loaded:
            return self._loaded[sid]
        t, lo, hi, k = self._ranges[sid]
        from assetops_backend.chain.ports import SiteRef

        r = self._snap._c.execute(text("SELECT site_code, site_type, timezone FROM site WHERE tenant_id = :t "
                                       "AND id = :s"), {"t": t, "s": UUID(sid)}).one()
        site = SiteRef(t, UUID(sid), r[0], r[1], r[2])
        days = utc_days(lo, hi)
        known = None if not self._snap.basis_historical else k
        result = self._rows.reader.read(t, [site], [KIND_CLAIM], days[0] - timedelta(days=1),
                                        days[-1] + timedelta(days=1), known)
        self.statements += result.statements
        served: dict[date, dict[str, Any]] = {}
        for read in result.rows:
            row = read.row
            if row.kind != KIND_CLAIM or read.pending or row.local_day not in days:
                continue
            if any(result.is_pending(site.site_id, d, KIND_CLAIM) for d in local_days_of(row.local_day,
                                                                                          site.timezone)):
                continue
            served[row.local_day] = row.body
        rids = sorted({b["revision_id"] for b in served.values() if b.get("revision_id")})
        links: dict[str, list[LinkRow]] = {}
        if rids:
            self.statements += 1
            blocks = self._rows.store.provenance(t, [UUID(x) for x in rids], BUILDER_VERSION)
            for block in blocks.values():
                for eid, rows in (block.get("link_rows") or {}).items():
                    links[eid] = [link_row_decode(v) for v in rows]
        self._loaded[sid] = (served, links)
        return self._loaded[sid]

    def claim(self, service: Any, t: UUID, s: UUID, day: date, rid: Any, k: datetime,
              basis_mode: str) -> dict[str, Any] | None:
        """The stored claim day projected at k, or None (read it as today) when no current row serves it."""
        sid = str(s).lower()
        page_day = self._days.get((sid, day, k))
        if page_day is None or sid not in self._ranges:
            return self._miss(t, s, day, "no page day")
        selected = {**page_day, "transaction_time": self._snap.read_at}
        if rid is None:  # D-ANY.5: no revision selected needs no stored input; never a compose, never a row
            return service.project_claim_limit(t, s, day, None, k, selected, None, basis_mode=basis_mode)
        served, _ = self._load(sid)
        body = served.get(day)
        if body is None:  # see module doc: the page selected a revision no row at k holds (Architect question)
            return self._miss(t, s, day, "absent")
        if body.get("revision_id") != _key(rid) or body.get("detail") is None:  # D-ANY.6a: not provably equal
            return self._miss(t, s, day, "revision differs")
        return service.project_claim_limit(t, s, day, rid, k, selected, decode(body["detail"]),
                                           basis_mode=basis_mode)

    def link_rows(self, s: UUID, ids: Sequence[str]) -> dict[tuple[str, str], list[LinkRow]] | None:
        """The stored link rows of every cited ID of Site `s` (the `_Prefetched` shape), or None if any is not
        stored (then the cited set is resolved as today)."""
        sid = str(s).lower()
        if sid not in self._ranges:
            return None
        _, links = self._load(sid)
        keys = [str(i).lower() for i in ids]
        if any(k not in links for k in keys):
            return None
        return {(sid, k): links[k] for k in keys}

    @staticmethod
    def _miss(t: UUID, s: UUID, day: date, why: str) -> None:
        _MISSES[0] += 1
        LOG.info(ABSENT_LOG_EVENT, extra={"event": ABSENT_LOG_EVENT, "kind": KIND_CLAIM, "tenant_id": str(t),
                                          "site_id": str(s), "day": day.isoformat(), "why": why})
        return None


__all__ = ["BUILDER_VERSION", "EvidenceClaimKindBuilder", "EvidenceRows", "KIND_CLAIM", "KIND_MONEY",
           "KIND_PROVENANCE", "KINDS", "RequestRows", "day_revision", "decode", "encode", "interval_evidence_ids",
           "kind_builders", "kind_versions", "link_row_decode", "link_row_encode", "local_days_of", "row_misses",
           "utc_days"]
