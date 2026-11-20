"""3A4 (spec `specs/3A4-amounts-by-month/spec.md` §3; D-3A4.1 to D-3A4.11): the commercial store read as money by
month.

Every month is computed on each call from the store's latest revisions (D-3A4.1); nothing is stored. A revision is
placed in its recognition month, or, for a SETTLEMENT without one, in the Site-local month of `settled_at` (D-3A4.2).
Each placed revision contributes to lines keyed by `(kind, dims, measure, currency, unit, provenance, basis)`
(D-3A4.3, D-3A4.10); sums are exact or fail (D-3A4.9); budget lines are listed, never summed (D-3A4.4); a heading
with no placed record has no line (D-3A4.5). Each read carries a stamp, a digest of the revisions placed in its
month, so a reader learns its read is out of date by asking `stale` (D-3A4.6). Nothing here imports `structure`
(D-3A4.8).
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Context, Decimal, Inexact, InvalidOperation, Rounded, localcontext
from typing import Callable, Iterable, Sequence
from uuid import UUID
from zoneinfo import ZoneInfo

from assetops_backend.commercial.model import RevisionRow
from assetops_backend.commercial.store import CommercialStore
from assetops_contracts.canonical import LEAF_FACTORS, loads_canonical, parse_record

MONEY_KINDS = ("CHARGE", "RECEIPT", "SETTLEMENT", "ADJUSTMENT", "EXPENSE", "BUDGET_LINE")
MEASURES = ("AMOUNT", "QUANTITY", "DECLARED")
BASES = ("RECOGNITION_PERIOD", "SETTLED_AT")
PROVENANCE_ORDER = ("observed-financial", "field-integrated", "bench-tested", "source-emulated", "demo-simulated")
DUPLICATE_DECLARATION = "DUPLICATE_DECLARATION"
PORTFOLIO_ZONE = "UTC"

_PERIOD = re.compile(r"[0-9]{4}-(0[1-9]|1[0-2])", re.ASCII)
#: §3.3: the dims of each kind, in order; `status` is the record's status, the rest are body fields.
_DIMS = {
    "CHARGE": ("line_type", "tariff_class"),
    "RECEIPT": ("status", "method"),
    "SETTLEMENT": ("provider",),
    "ADJUSTMENT": ("reason_code",),
    "EXPENSE": ("category", "status"),
    "BUDGET_LINE": ("factor_id", "version_ref", "line_ref"),
}


def _exact() -> Context:
    """D-3A4.9: 200 digits, and any rounding is an error."""
    return Context(prec=200, traps=[Inexact, Rounded, InvalidOperation])


@dataclass(frozen=True)
class MonthKey:
    site_id: UUID | None
    period: str


@dataclass(frozen=True)
class MonthStamp:
    site_id: UUID | None
    period: str
    digest: str


@dataclass(frozen=True)
class MonthLine:
    kind: str
    dims: tuple[tuple[str, str | None], ...]
    measure: str
    value: Decimal | None
    currency: str | None
    unit: str | None
    provenance: str
    record_count: int
    basis: str
    source_systems: tuple[str, ...]
    note: str | None


@dataclass(frozen=True)
class Received:
    source_system: str
    provenance: str
    record_count: int


@dataclass(frozen=True)
class MonthAmounts:
    tenant_id: UUID
    site_id: UUID | None
    period: str
    closed: bool
    known_at: datetime | None
    lines: tuple[MonthLine, ...]
    received: tuple[Received, ...]
    stamp: MonthStamp


def month_bounds(period: str, tz: str) -> tuple[datetime, datetime]:
    """§3.2: `[local midnight of day 1, local midnight of day 1 of the next month)` in `tz`, as UTC instants (the rule
    of 3B3's `month_window`, written here, not imported: D-3A4.8)."""
    year, month = int(period[:4]), int(period[5:7])
    zone = ZoneInfo(tz)
    nxt = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    lo = datetime(year, month, 1, tzinfo=zone).astimezone(timezone.utc)
    hi = datetime(nxt.year, nxt.month, 1, tzinfo=zone).astimezone(timezone.utc)
    return lo, hi


def _check_period(period: str) -> None:
    if not isinstance(period, str) or _PERIOD.fullmatch(period) is None:
        raise ValueError("period must be YYYY-MM")


def _placement(row: RevisionRow, tz: str) -> tuple[str, str] | None:
    """§3.2 by columns only: (period, basis), or None for a revision that has no month."""
    if row.recognition_period is not None:
        return row.recognition_period, "RECOGNITION_PERIOD"
    if row.kind == "SETTLEMENT" and row.settled_at is not None:
        return row.settled_at.astimezone(ZoneInfo(tz)).strftime("%Y-%m"), "SETTLED_AT"
    return None


def _digest(site_id: UUID | None, period: str, rows: Iterable[RevisionRow]) -> str:
    head = f"{site_id or '-'}|{period}"
    body = "\n".join(sorted(f"{r.record_id}:{r.id}" for r in rows))
    return hashlib.sha256(f"{head}\n{body}".encode("utf-8")).hexdigest()


def _sort_key(line: MonthLine):
    return (MONEY_KINDS.index(line.kind), [(v is not None, v or "") for _, v in line.dims],
            MEASURES.index(line.measure), line.currency or "", line.unit or "",
            PROVENANCE_ORDER.index(line.provenance), BASES.index(line.basis))


def _measures(record) -> list[tuple[str, Decimal, str | None, str | None]]:
    """§3.3 / D-3A4.10: (measure, value, currency, unit) of one parsed record."""
    if record.kind == "BUDGET_LINE":
        factor = record.body["factor_id"]
        unit = str(LEAF_FACTORS[factor].unit) if factor in LEAF_FACTORS else None
        return [("DECLARED", record.body["value"], record.body.get("currency"), unit)]
    out = []
    if record.amount is not None:
        out.append(("AMOUNT", record.amount[0], record.amount[1], None))
    if record.quantity is not None:
        out.append(("QUANTITY", record.quantity[0], None, record.quantity[1]))
    return out


def _parse(row: RevisionRow):
    try:
        return parse_record(loads_canonical(row.canonical.encode("utf-8")))
    except Exception:  # noqa: BLE001 - a stored canonical that does not parse is a bug, never a figure
        pass
    raise RuntimeError("stored canonical does not parse")  # outside the handler: no cause, no context


def _lines(placed: Sequence[tuple[RevisionRow, str]]) -> tuple[MonthLine, ...]:
    groups: dict[tuple, list] = {}
    for row, basis in placed:
        record = _parse(row)
        dims = tuple((name, record.status if name == "status" else record.body.get(name))
                     for name in _DIMS[row.kind])
        for measure, value, currency, unit in _measures(record):
            key = (row.kind, dims, measure, currency, unit, row.provenance, basis)
            groups.setdefault(key, []).append((value, row.source_system))
    lines = []
    with localcontext(_exact()):
        for (kind, dims, measure, currency, unit, provenance, basis), parts in groups.items():
            note = None
            if measure == "DECLARED":  # D-3A4.4: listed, never summed
                value = parts[0][0] if len(parts) == 1 else None
                note = None if len(parts) == 1 else DUPLICATE_DECLARATION
            else:
                value = Decimal(0)
                for part, _system in parts:
                    value = value + part
                if value == 0:
                    value = value.copy_abs()
            lines.append(MonthLine(kind, dims, measure, value, currency, unit, provenance, len(parts), basis,
                                   tuple(sorted({s for _, s in parts})), note))
    return tuple(sorted(lines, key=_sort_key))


def _received(rows: Iterable[RevisionRow]) -> tuple[Received, ...]:
    counts: dict[tuple[str, str], int] = {}
    for row in rows:
        counts[(row.source_system, row.provenance)] = counts.get((row.source_system, row.provenance), 0) + 1
    ordered = sorted(counts.items(), key=lambda kv: (kv[0][0], PROVENANCE_ORDER.index(kv[0][1])))
    return tuple(Received(system, provenance, n) for (system, provenance), n in ordered)


class CommercialMonths:
    def __init__(self, store: CommercialStore, *, clock: Callable[[], datetime]) -> None:
        self._store = store
        self._clock = clock

    # --- placement ----------------------------------------------------------------------------------------------

    def _site_zone(self, tenant_id: UUID, site_id: UUID) -> str:
        zones = self._store.site_zones(tenant_id)
        if site_id not in zones:
            raise LookupError("unknown Site")
        return zones[site_id]

    def _placed_site(self, tenant_id: UUID, site_id: UUID, period: str, tz: str,
                     known_at: datetime | None) -> list[tuple[RevisionRow, str]]:
        out = []
        for row in self._store.latest_revisions(tenant_id, site_id=site_id, known_at=known_at):
            if row.kind not in MONEY_KINDS:
                continue
            placed = _placement(row, tz)
            if placed is not None and placed[0] == period:
                out.append((row, placed[1]))
        return out

    def _placed_portfolio(self, tenant_id: UUID, period: str,
                          known_at: datetime | None) -> list[tuple[RevisionRow, str]]:
        rows = self._store.latest_revisions(tenant_id, kind="BUDGET_LINE", recognition_period=period,
                                            known_at=known_at)
        return [(row, "RECOGNITION_PERIOD") for row in rows if row.site_id is None]

    def _month(self, tenant_id: UUID, site_id: UUID | None, period: str, tz: str,
               placed: list[tuple[RevisionRow, str]], known_at: datetime | None) -> MonthAmounts:
        _lo, hi = month_bounds(period, tz)
        cutoff = known_at if known_at is not None else self._clock()
        rows = [row for row, _basis in placed]
        return MonthAmounts(tenant_id=tenant_id, site_id=site_id, period=period, closed=cutoff >= hi,
                            known_at=known_at, lines=_lines(placed), received=_received(rows),
                            stamp=MonthStamp(site_id, period, _digest(site_id, period, rows)))

    # --- the reads ----------------------------------------------------------------------------------------------

    def site_month(self, tenant_id: UUID, site_id: UUID, period: str, *,
                   known_at: datetime | None = None) -> MonthAmounts:
        _check_period(period)
        tz = self._site_zone(tenant_id, site_id)
        placed = self._placed_site(tenant_id, site_id, period, tz, known_at)
        return self._month(tenant_id, site_id, period, tz, placed, known_at)

    def portfolio_month(self, tenant_id: UUID, period: str, *, known_at: datetime | None = None) -> MonthAmounts:
        """Portfolio-level records only (`site_id` None), in UTC."""
        _check_period(period)
        placed = self._placed_portfolio(tenant_id, period, known_at)
        return self._month(tenant_id, None, period, PORTFOLIO_ZONE, placed, known_at)

    def stale(self, tenant_id: UUID, stamps: Sequence[MonthStamp]) -> tuple[MonthStamp, ...]:
        """The given stamps whose month's current digest differs, in input order."""
        out = []
        for stamp in stamps:
            _check_period(stamp.period)
            if stamp.site_id is None:
                rows = [r for r, _ in self._placed_portfolio(tenant_id, stamp.period, None)]
            else:
                tz = self._site_zone(tenant_id, stamp.site_id)
                rows = [r for r, _ in self._placed_site(tenant_id, stamp.site_id, stamp.period, tz, None)]
            if _digest(stamp.site_id, stamp.period, rows) != stamp.digest:
                out.append(stamp)
        return tuple(out)

    def months_touched(self, tenant_id: UUID, intake_id: UUID) -> tuple[MonthKey, ...]:
        """Each money revision the intake wrote: its month and, when it supersedes one, the month it left."""
        zones = self._store.site_zones(tenant_id)
        keys: set[MonthKey] = set()
        for new, old in self._store.intake_revisions(tenant_id, intake_id):
            for row in (new, old):
                if row is None or row.kind not in MONEY_KINDS:
                    continue
                tz = PORTFOLIO_ZONE if row.site_id is None else zones[row.site_id]
                placed = _placement(row, tz)
                if placed is not None:
                    keys.add(MonthKey(row.site_id, placed[0]))
        return tuple(sorted(keys, key=lambda k: (k.site_id is not None, str(k.site_id or ""), k.period)))
