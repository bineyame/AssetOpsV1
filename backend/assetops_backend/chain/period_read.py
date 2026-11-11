"""ANY-1 AR-1: the stored read-period foundation (architect answer 2026-11-10 §4; D-ANY.1-2, D-MONEY.1-4, D-I18N.1).

Compute when data changes, not when someone looks. Every range-bound page part will read stored rows at its native
grain (`site_period_read`, migration 0059): one revisioned row per (Site, kind, period) whose `body` is the exact
fragment today's compose builds for that period, produced by the existing pure functions (AR-2..AR-4 declare the
kinds; AR-1 declares none). This module holds the generic parts:

- the row contract (`validate_body`): words are `{key, params}` messages (D-I18N.1), never composed text; money lines
  carry the amount with its receipt in the original currency (D-MONEY.1-2), and no body carries a total (D-MONEY.3);
- the fingerprint (`period_fp`): kind, builder version, the builder's input material and every money `rate_ref`
  (D-MONEY.4), so a price correction or a builder change appends a new revision;
- `PeriodReadBuilder`: one builder for every kind, the `SnapshotBuilder` rules (an unchanged fingerprint writes
  nothing; a changed one appends `revision = latest + 1`; old revisions stay for "as known at k");
- `PeriodReader`: ONE row statement per Sites x range x kinds, then PENDING-at-k from the append-only outbox and
  consumption ledgers (an input event recorded at or before k and not consumed by k), the live dirty queue, and a
  row of an older builder version. The read path never computes a period.

`served_kinds()` is the AR-0 parity switch: the kinds whose page parts compose from rows (`ASSETOPS_PERIOD_READ_KINDS`,
comma-separated; empty = today's compose everywhere). AR-1 switches nothing.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from dataclasses import dataclass, field, replace
from datetime import date, datetime, time, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any, Callable, Iterable, Mapping, Protocol, Sequence
from uuid import UUID
from zoneinfo import ZoneInfo

from .events import EventRegister, KIND_PATTERN, resolve
from .grading import NO_DATA, PENDING
from .ports import DayCtx, PeriodKey, PeriodReadStore, PeriodRow, ProvenanceBlock, SiteRef

LOG = logging.getLogger("assetops.chain.period_read")
SERVED_KINDS_ENV = "ASSETOPS_PERIOD_READ_KINDS"
STATE_PATTERN = re.compile(r"^[A-Z][A-Z_]{0,39}$")
#: Body fields that hold words: their value is a message `{key, params}` (or null), never composed text (D-I18N.1).
WORD_FIELDS = frozenset({"label", "text", "title", "message", "sentence", "note", "summary", "description",
                         "caption", "headline"})
#: D-MONEY.3: no row kind writes a cross-Site, cross-currency or verified-result total.
TOTAL_FIELDS = frozenset({"total", "totals", "grand_total", "estate_total", "portfolio_total", "sum_total"})
MONEY_AREA = "money"
RECEIPT_KEYS = ("v", "formula", "qty", "unit", "rate", "rate_unit", "rate_ref", "segments", "fx")
CURRENCY = re.compile(r"^[A-Z]{3}$")
CENT = Decimal("0.01")


class PeriodContractError(ValueError):
    """A period body breaks the stored-row contract (D-I18N.1, D-MONEY.1-3)."""


def served_kinds() -> frozenset[str]:
    raw = os.environ.get(SERVED_KINDS_ENV, "")
    return frozenset(k.strip() for k in raw.split(",") if k.strip())


# --- the row contract ---------------------------------------------------------------------------------------------


def is_message(value: Any) -> bool:
    return (isinstance(value, dict) and set(value) == {"key", "params"} and isinstance(value["key"], str)
            and bool(value["key"]) and isinstance(value["params"], dict)
            and all(isinstance(p, (str, int, float)) and not isinstance(p, bool) for p in value["params"].values()))


def money_amount(qty: Any, rate: Any) -> str:
    """D-MONEY.1: the amount from the UNROUNDED quantity and rate, rounded to the cent half-up."""
    return str((Decimal(str(qty)) * Decimal(str(rate))).quantize(CENT, rounding=ROUND_HALF_UP))


def money_line(*, qty: Any, unit: str, rate: Any, rate_unit: str, rate_ref: str, currency: str, basis: str,
               formula: str = "qty*rate", low: Any = None, high: Any = None) -> dict[str, Any]:
    """One stored money line with its receipt (D-MONEY.1). A ranged line passes `low`/`high` and stores no amount."""
    receipt = {"v": 1, "formula": formula, "qty": str(qty), "unit": unit, "rate": str(rate), "rate_unit": rate_unit,
               "rate_ref": rate_ref, "segments": None, "fx": None}
    line: dict[str, Any] = {"currency": currency, "basis": basis, "receipt": receipt}
    if low is not None or high is not None:
        line.update({"low": str(low), "high": str(high)})
    else:
        line["amount"] = money_amount(qty, rate)
    return line


def _decimal(value: Any, where: str) -> Decimal:
    if not isinstance(value, str):
        raise PeriodContractError(f"{where}: a stored amount is a decimal string")
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise PeriodContractError(f"{where}: {value!r} is not a decimal") from exc


def validate_money_line(line: Any, where: str) -> None:
    if not isinstance(line, dict):
        raise PeriodContractError(f"{where}: a money line is an object")
    allowed = {"amount", "low", "high", "currency", "basis", "receipt", "label"}
    if set(line) - allowed:
        raise PeriodContractError(f"{where}: unknown money line keys {sorted(set(line) - allowed)} (no converted "
                                  "amounts or totals, D-MONEY.2-3)")
    if not isinstance(line.get("currency"), str) or not CURRENCY.match(line["currency"]):
        raise PeriodContractError(f"{where}: currency is the original ISO 4217 code (D-MONEY.2)")
    if not isinstance(line.get("basis"), str) or not line["basis"]:
        raise PeriodContractError(f"{where}: a money line names its basis")
    ranged = "low" in line or "high" in line
    if ranged == ("amount" in line):
        raise PeriodContractError(f"{where}: a money line has an amount, or low and high, not both")
    receipt = line.get("receipt")
    if not isinstance(receipt, dict) or tuple(sorted(receipt)) != tuple(sorted(RECEIPT_KEYS)):
        raise PeriodContractError(f"{where}: the receipt has exactly {RECEIPT_KEYS} (D-MONEY.1)")
    if receipt["segments"] is not None or receipt["fx"] is not None:
        raise PeriodContractError(f"{where}: receipt segments and fx are null until BL-67 (D-MONEY.1-2)")
    if not isinstance(receipt["rate_ref"], str) or not receipt["rate_ref"]:
        raise PeriodContractError(f"{where}: the receipt names its rate_ref (the assumption revision)")
    if ranged:
        if _decimal(line.get("low"), where + ".low") > _decimal(line.get("high"), where + ".high"):
            raise PeriodContractError(f"{where}: low is above high")
    else:
        amount = _decimal(line["amount"], where + ".amount")
        if amount != amount.quantize(CENT):
            raise PeriodContractError(f"{where}: the amount is rounded to the cent")
        if receipt["formula"] == "qty*rate" and money_amount(receipt["qty"], receipt["rate"]) != line["amount"]:
            raise PeriodContractError(f"{where}: the amount does not reproduce from its receipt (D-MONEY.1)")
    if "label" in line and line["label"] is not None and not is_message(line["label"]):
        raise PeriodContractError(f"{where}.label: words are {{key, params}} (D-I18N.1)")


def _walk(value: Any, where: str) -> None:
    if isinstance(value, dict):
        for k, v in value.items():
            if not isinstance(k, str):
                raise PeriodContractError(f"{where}: object keys are strings")
            if k in TOTAL_FIELDS:
                raise PeriodContractError(f"{where}.{k}: no stored totals (D-MONEY.3)")
            if k in WORD_FIELDS and v is not None and not is_message(v):
                raise PeriodContractError(f"{where}.{k}: words are stored as {{key, params}}, never composed text "
                                          "(D-I18N.1)")
            if k != "params":
                _walk(v, f"{where}.{k}")
    elif isinstance(value, list):
        for i, v in enumerate(value):
            _walk(v, f"{where}[{i}]")


def validate_provenance(block: Any, where: str) -> None:
    if not isinstance(block, dict):
        raise PeriodContractError(f"{where}: a provenance block is an object")
    _walk(block, where)


def validate_body(kind: str, body: Any) -> None:
    """The stored-row contract every kind's body meets before it is appended."""
    if not KIND_PATTERN.match(kind):
        raise PeriodContractError(f"kind {kind!r} is not '<area>.<name>'")
    if not isinstance(body, dict):
        raise PeriodContractError(f"{kind}: a body is an object")
    _walk(body, kind)
    if kind.split(".", 1)[0] == MONEY_AREA:
        lines = body.get("lines")
        if not isinstance(lines, list):
            raise PeriodContractError(f"{kind}: a money body holds its per-Site `lines`")
        for i, line in enumerate(lines):
            validate_money_line(line, f"{kind}.lines[{i}]")


def rate_refs(body: Any) -> list[str]:
    """Every receipt `rate_ref` in a body (D-MONEY.4: the fingerprint includes them)."""
    found: set[str] = set()

    def walk(v: Any) -> None:
        if isinstance(v, dict):
            receipt = v.get("receipt")
            if isinstance(receipt, dict) and isinstance(receipt.get("rate_ref"), str):
                found.add(receipt["rate_ref"])
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)

    walk(body)
    return sorted(found)


def _canonical(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _canonical(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        items = [_canonical(v) for v in value]
        return sorted(items, key=lambda x: json.dumps(x, sort_keys=True)) if isinstance(value, (set, frozenset)) \
            else items
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (UUID, Decimal)):
        return str(value)
    return value


def period_fp(kind: str, builder_version: str, inputs: Any, body: Mapping[str, Any]) -> str:
    """sha256 over the kind, builder version, the builder's input material and every money `rate_ref`."""
    material = {"kind": kind, "builder_version": builder_version, "inputs": _canonical(inputs),
                "rate_refs": rate_refs(body)}
    return hashlib.sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


# --- the builder --------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class PeriodFragment:
    """One period a kind builder produced: the body today's compose builds for it, and the input material."""
    period_start: datetime
    period_end: datetime
    state: str
    body: dict[str, Any]
    inputs: Any = None
    provenance: Mapping[UUID, dict[str, Any]] = field(default_factory=dict)


class KindBuilder(Protocol):
    kind: str
    builder_version: str

    def fragments(self, ctx: DayCtx, site: SiteRef) -> Sequence[PeriodFragment]:
        """Every period of the kind whose Site-local day is `ctx.local_day`, from the existing pure functions."""


@dataclass(frozen=True)
class PeriodWritten:
    row: PeriodRow
    written: bool  # False: unchanged fingerprint and builder version, nothing appended


def day_bounds(tz: str, local_day: date) -> tuple[datetime, datetime]:
    zone = ZoneInfo(tz)
    lo = datetime.combine(local_day, time(0), zone)
    hi = datetime.combine(local_day + timedelta(days=1), time(0), zone)
    return lo.astimezone(timezone.utc), hi.astimezone(timezone.utc)


class PeriodReadBuilder:
    """The one builder of `site_period_read` (rebuilt per dirty (Site, day, kind) in the tick, or by the backfill)."""

    def __init__(self, store: PeriodReadStore, builders: Mapping[str, KindBuilder]) -> None:
        for kind, b in builders.items():
            if b.kind != kind or not KIND_PATTERN.match(kind) or not b.builder_version:
                raise PeriodContractError(f"kind builder {kind!r} is mis-declared")
        self._store = store
        self._builders = dict(builders)

    @property
    def kinds(self) -> frozenset[str]:
        return frozenset(self._builders)

    def versions(self) -> dict[str, str]:
        return {k: b.builder_version for k, b in self._builders.items()}

    def build(self, tenant_id: UUID, site: SiteRef, local_day: date, kind: str,
              known_at: datetime | None = None) -> list[PeriodWritten]:
        builder = self._builders[kind]
        lo, hi = day_bounds(site.timezone, local_day)
        ctx = DayCtx(tenant_id=tenant_id, site_id=site.site_id, site_code=site.site_code, domain=site.site_type,
                     tz=site.timezone, local_day=local_day, period_start_utc=lo, period_end_utc=hi,
                     known_at=known_at)
        out: list[PeriodWritten] = []
        for frag in builder.fragments(ctx, site):
            out.append(self._one(tenant_id, site, local_day, builder, frag))
        return out

    def _one(self, tenant_id: UUID, site: SiteRef, local_day: date, builder: KindBuilder,
             frag: PeriodFragment) -> PeriodWritten:
        if frag.period_end <= frag.period_start:
            raise PeriodContractError(f"{builder.kind}: a period ends after it starts")
        if not STATE_PATTERN.match(frag.state):
            raise PeriodContractError(f"{builder.kind}: state {frag.state!r} is an upper-case code")
        validate_body(builder.kind, frag.body)
        for rev_id, block in sorted(frag.provenance.items(), key=lambda kv: str(kv[0])):
            validate_provenance(block, f"{builder.kind}.provenance[{rev_id}]")
            self._store.append_provenance(ProvenanceBlock(tenant_id, rev_id, builder.builder_version, block))
        fp = period_fp(builder.kind, builder.builder_version, frag.inputs, frag.body)
        key = PeriodKey(tenant_id, site.site_id, builder.kind, frag.period_start)
        latest = self._store.latest(key)
        row = PeriodRow(tenant_id=tenant_id, site_id=site.site_id, kind=builder.kind,
                        period_start=frag.period_start, period_end=frag.period_end, local_day=local_day,
                        revision=1 if latest is None else latest[0] + 1, builder_version=builder.builder_version,
                        input_fp=fp, state=frag.state, body=frag.body)
        if latest is not None and latest[1] == fp and latest[2] == builder.builder_version:
            return PeriodWritten(replace(row, revision=latest[0]), False)
        self._store.append(row)
        return PeriodWritten(row, True)

    def build_range(self, tenant_id: UUID, site: SiteRef, from_day: date, to_day: date,
                    kinds: Sequence[str] | None = None) -> list[PeriodWritten]:
        keys = sorted(self._builders if kinds is None else [k for k in kinds if k in self._builders])
        out: list[PeriodWritten] = []
        day = from_day
        while day <= to_day:
            for kind in keys:
                out.extend(self.build(tenant_id, site, day, kind))
            day += timedelta(days=1)
        return out


# --- the reader ---------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class PeriodRead:
    row: PeriodRow
    pending: tuple[str, ...] = ()  # reasons: "event", "dirty", "builder_version"


#: D-ANY.5 M1: a requested (Site, day, kind) with no row at k renders exactly as today's compose renders no stored
#: input at k (`chain/reader.py`: a requested measure with no snapshot row is NO_DATA).
NO_ROW_STATE = NO_DATA
ABSENT_LOG_EVENT = "period_row_absent"
_ABSENT_SEEN = [0]


def absent_count() -> int:
    """Live absent (Site, day, kind) reads since process start (perf reports it; D-ANY.5 M1)."""
    return _ABSENT_SEEN[0]


@dataclass
class PeriodReadResult:
    rows: list[PeriodRead]
    #: (site_id, local_day, kind) -> reasons, for every requested day and kind that is PENDING at k (with or
    #: without a stored row: a missing period on a pending day is pending, not absent).
    pending: dict[tuple[UUID, date, str], tuple[str, ...]]
    statements: int = 0
    #: D-ANY.5 M1: every requested (site_id, local_day, kind) with no stored row at k, sorted; never silent.
    absent: tuple[tuple[UUID, date, str], ...] = ()

    def is_pending(self, site_id: UUID, local_day: date, kind: str) -> bool:
        return (site_id, local_day, kind) in self.pending

    def is_absent(self, site_id: UUID, local_day: date, kind: str) -> bool:
        return (site_id, local_day, kind) in self.absent

    def day_state(self, site_id: UUID, local_day: date, kind: str) -> str | None:
        """PENDING at k, else the no-row rule's state for an absent day, else None (the stored rows render)."""
        if self.is_pending(site_id, local_day, kind):
            return PENDING
        if self.is_absent(site_id, local_day, kind):
            return NO_ROW_STATE
        return None


class PeriodReader:
    def __init__(self, store: PeriodReadStore, register: EventRegister, versions: Mapping[str, str],
                 now: Callable[[], datetime] | None = None) -> None:
        self._store = store
        self._register = register
        self._versions = dict(versions)
        self._now = now or (lambda: datetime.now(timezone.utc))

    def read(self, tenant_id: UUID, sites: Sequence[SiteRef], kinds: Sequence[str], from_day: date,
             to_day: date, known_at: datetime | None = None) -> PeriodReadResult:
        site_ids = [s.site_id for s in sites]
        wanted = sorted(set(kinds))
        rows = self._store.read_latest(tenant_id, site_ids, wanted, from_day, to_day, known_at)
        statements = 1
        pending: dict[tuple[UUID, date, str], set[str]] = {}

        def add(key: tuple[UUID, date, str], reason: str) -> None:
            pending.setdefault(key, set()).add(reason)

        at = known_at or self._now()
        types = self._register.consumes("snapshots")
        by_id = {s.site_id: s for s in sites}
        if types and site_ids and wanted:
            statements += 1
            for ev in self._store.unconsumed_at(tenant_id, site_ids, types, known_at):
                site = by_id.get(ev.site_id)
                if site is None:
                    continue
                today = at.astimezone(ZoneInfo(site.timezone)).date()
                for day, kind in resolve(self._register, ev, site_type=site.site_type, tz=site.timezone,
                                         today=today):
                    if kind in wanted and from_day <= day <= to_day:
                        add((site.site_id, day, kind), "event")
        if known_at is None and site_ids and wanted:
            statements += 1
            for site_id, day, kind in self._store.dirty_marks(tenant_id, site_ids, wanted, from_day, to_day):
                add((site_id, day, kind), "dirty")
        out: list[PeriodRead] = []
        for r in sorted(rows, key=lambda r: (str(r.site_id), r.kind, r.period_start)):
            reasons = set(pending.get((r.site_id, r.local_day, r.kind), ()))
            if self._versions.get(r.kind) != r.builder_version:
                reasons.add("builder_version")
                add((r.site_id, r.local_day, r.kind), "builder_version")
            out.append(PeriodRead(r, tuple(sorted(reasons))))
        have = {(r.site_id, r.local_day, r.kind) for r in rows}
        absent: list[tuple[UUID, date, str]] = []
        day = from_day
        while day <= to_day:
            for site_id in site_ids:
                absent.extend((site_id, day, kind) for kind in wanted if (site_id, day, kind) not in have)
            day += timedelta(days=1)
        absent.sort(key=lambda a: (str(a[0]), a[1], a[2]))
        if absent and known_at is None:  # no fallback compose on the serve path: log and count (D-ANY.5 M1)
            _ABSENT_SEEN[0] += len(absent)
            LOG.warning(ABSENT_LOG_EVENT, extra={"event": ABSENT_LOG_EVENT, "tenant_id": str(tenant_id),
                                                 "count": len(absent), "first": [str(absent[0][0]),
                                                                                 absent[0][1].isoformat(),
                                                                                 absent[0][2]]})
        return PeriodReadResult(out, {k: tuple(sorted(v)) for k, v in sorted(pending.items(),
                                                                               key=lambda kv: str(kv[0]))},
                                statements, tuple(absent))


def stale_rows(rows: Iterable[PeriodRow], versions: Mapping[str, str]) -> list[PeriodRow]:
    """Rows written by another builder version than the current one (the backfill rebuilds their days)."""
    return [r for r in rows if versions.get(r.kind) != r.builder_version]


__all__ = ["ABSENT_LOG_EVENT", "NO_ROW_STATE", "absent_count", "KindBuilder", "PeriodContractError", "PeriodFragment", "PeriodRead", "PeriodReadBuilder",
           "PeriodReadResult", "PeriodReader", "PeriodWritten", "SERVED_KINDS_ENV", "day_bounds", "is_message",
           "money_amount", "money_line", "period_fp", "rate_refs", "served_kinds", "stale_rows", "validate_body",
           "validate_money_line"]
