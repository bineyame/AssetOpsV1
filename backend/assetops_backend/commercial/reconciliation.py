"""3A7 (spec `specs/3A7-month-reconciled/spec.md` §2; rulings D-3A7.1 to D-3A7.13): one closed month reconciled
against the operator's own management accounts.

The finance lead records a closed month's revenue and fuel cost from the management accounts, for one mini-grid Site
or the organisation. Each read compares them, exactly and at its instant `k`, with the money the screen shows (4b's
definition, summed over the scope; D-3A7.1, D-3A7.3, D-3A7.9) within the tenant's tolerance at `k` (1 in 100 unless
the owner set another, RC8, D-3A7.12). Money reads Recorded only while a current statement compared on both headings
against recorded lines matches (it *opens* the gate, D-3A7.8) and no statement covering the month disagrees or cannot
be compared (D-3A7.2); otherwise it is not yet reconciled. A missing figure is never 0: a heading with no used line
matches only where the accounts themselves state 0.00, and that never opens the gate.

Commit 1 of D-SC1.28: the checks and the standing as codes and `Decimal`s. The sentences of §2.7 (`words`, `text`)
and `money_word` come in commit 2, as SC-1 statements.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Context, Decimal, Inexact, InvalidOperation, Rounded, localcontext
from typing import Any, Callable, Iterable, Mapping, Sequence
from uuid import UUID, uuid4

from assetops_backend.accounts.permissions import roles_of
from assetops_backend.commercial.model import SiteRow, StatementRow, ToleranceRow
from assetops_backend.commercial.months import CommercialMonths, MonthAmounts, MonthLine
from assetops_backend.commercial.store import CommercialStore
from assetops_backend.commercial.uploads import Actor, has_control_character
from assetops_backend.structure.evaluate import ORIGIN_ORDER
from assetops_backend.structure.money import COST_STATUSES
from assetops_backend.structure.read import SITE_TYPE_TO_STRUCTURE

HEADINGS = ("revenue", "fuel_cost")
DEFAULT_TOLERANCE = Decimal("0.01")
MATCHED, NOT_MATCHED, NOT_COMPARABLE = "MATCHED", "NOT_MATCHED", "NOT_COMPARABLE"
ZERO_STATED, MONTH_OPEN, NOT_RECEIVED, CURRENCY_MISMATCH = ("NONE_RECORDED_ZERO_STATED", "MONTH_OPEN",
                                                             "NOT_RECEIVED", "CURRENCY_MISMATCH")
RECONCILED, THIS_MONTH_NOT_MATCHED, THIS_MONTH_NOT_COMPARABLE, NO_STATEMENT, NONE_MATCHED = (
    "RECONCILED", "THIS_MONTH_NOT_MATCHED", "THIS_MONTH_NOT_COMPARABLE", "NO_STATEMENT", "NONE_MATCHED")
COMMAND = "commercial.accounts_statement"
MINI_GRID = "MINI_GRID"
#: D-3A4.9: 200 digits, and any rounding is an error. The comparison is made only here (D-3A7.10).
EXACT = Context(prec=200, traps=[Inexact, Rounded, InvalidOperation])

_PERIOD = re.compile(r"[0-9]{4}-(0[1-9]|1[0-2])", re.ASCII)
_CURRENCY = re.compile(r"[A-Z]{3}", re.ASCII)
_AMOUNT = re.compile(r"(0|[1-9][0-9]{0,11})\.[0-9]{2}", re.ASCII)
_TOLERANCE = re.compile(r"0\.[0-9]{1,4}", re.ASCII)
_OWNER_REF = re.compile(r"owner/owner-[a-z0-9-]+\.md", re.ASCII)
_MAX_TOLERANCE = Decimal("0.05")
_SOURCE_REF_MAX = 200


class ReconRefused(Exception):
    """A refused statement or tolerance (§2.5, §5). `params` are strings; nothing was written."""

    def __init__(self, code: str, params: Mapping[str, Any] | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.params = {k: str(v) for k, v in (params or {}).items()}


@dataclass(frozen=True)
class HeadingCheck:
    heading: str
    state: str                       # MATCHED | NOT_MATCHED | NOT_COMPARABLE
    reason: str | None               # NONE_RECORDED_ZERO_STATED | MONTH_OPEN | NOT_RECEIVED | CURRENCY_MISMATCH
    accounts: Decimal
    recorded: Decimal | None         # None unless compared: no used line, another currency, or the month open
    difference: Decimal | None       # recorded - accounts, exact
    allowed: Decimal                 # tolerance * accounts, exact
    record_currencies: tuple[str, ...]
    sources: tuple[str, ...]
    origins: tuple[str, ...]


@dataclass(frozen=True)
class StatementCheck:
    statement_id: UUID
    site_id: UUID | None
    site_code: str | None
    period: str
    currency: str
    tolerance: Decimal
    state: str
    opens: bool
    headings: tuple[HeadingCheck, HeadingCheck]
    recorded_by: UUID
    recorded_at: datetime
    recorded_by_script: bool
    source_ref: str


@dataclass(frozen=True)
class MoneyStanding:
    tenant_id: UUID
    site_id: UUID | None
    period: str
    known_at: datetime | None
    reconciled: bool
    reason: str                      # RECONCILED | THIS_MONTH_NOT_MATCHED | THIS_MONTH_NOT_COMPARABLE | NO_STATEMENT
    this_month: StatementCheck | None  # | NONE_MATCHED
    cited: StatementCheck | None     # the month that reconciled the money (RECONCILED only)
    tolerance: Decimal


# --- pure rules -----------------------------------------------------------------------------------------------


def _compare(accounts: Decimal, recorded: Decimal, tolerance: Decimal) -> str:
    """§2.2 rule 4, exact: `abs(recorded - accounts) <= tolerance * accounts`."""
    with localcontext(EXACT):
        return MATCHED if abs(recorded - accounts) <= tolerance * accounts else NOT_MATCHED


def _dim(line: MonthLine, name: str) -> str | None:
    return dict(line.dims).get(name)


def _used(heading: str, line: MonthLine) -> bool:
    """§2.1: 4b's revenue and fuel-cost rows (D-3A7.1)."""
    if line.measure != "AMOUNT":
        return False
    if heading == "revenue":
        return line.kind == "CHARGE"
    return line.kind == "EXPENSE" and _dim(line, "category") == "FUEL" and _dim(line, "status") in COST_STATUSES


def _heading(heading: str, accounts: Decimal, tolerance: Decimal, currency: str,
             months: Sequence[MonthAmounts]) -> HeadingCheck:
    lines = [line for month in months for line in month.lines if _used(heading, line)]
    currencies = tuple(sorted({line.currency for line in lines if line.currency is not None}))
    sources = tuple(sorted({f"commercial:{s}" for line in lines for s in line.source_systems}))
    held = {line.provenance for line in lines}
    origins = tuple(o for o in ORIGIN_ORDER if o in held)
    with localcontext(EXACT):
        allowed = tolerance * accounts

    def made(state: str, reason: str | None, recorded: Decimal | None = None,
             difference: Decimal | None = None) -> HeadingCheck:
        return HeadingCheck(heading, state, reason, accounts, recorded, difference, allowed, currencies, sources,
                            origins)

    if any(not month.closed for month in months):
        return made(NOT_COMPARABLE, MONTH_OPEN)
    if not lines:
        return made(MATCHED, ZERO_STATED) if accounts == 0 else made(NOT_COMPARABLE, NOT_RECEIVED)
    if currencies != (currency,) or any(line.currency is None for line in lines):
        return made(NOT_COMPARABLE, CURRENCY_MISMATCH)
    with localcontext(EXACT):
        recorded = Decimal(0)
        for line in lines:
            recorded = recorded + line.value
        difference = recorded - accounts
    return made(_compare(accounts, recorded, tolerance), None, recorded, difference)


def _statement_state(headings: Sequence[HeadingCheck]) -> str:
    states = {h.state for h in headings}
    if states == {MATCHED}:
        return MATCHED
    return NOT_MATCHED if NOT_MATCHED in states else NOT_COMPARABLE


def _latest(rows: Iterable[Any], at: Callable[[Any], datetime]) -> Any:
    return max(rows, key=lambda r: (at(r), str(r.id)))


def _tolerance_at(rows: Sequence[ToleranceRow], k: datetime) -> Decimal:
    known = [r for r in rows if r.set_at <= k]
    return Decimal(_latest(known, lambda r: r.set_at).tolerance) if known else DEFAULT_TOLERANCE


def _current(rows: Sequence[StatementRow], k: datetime) -> dict[tuple[UUID | None, str], StatementRow]:
    """§2.3: the latest statement existing at `k` for each (site_id, period), by `recorded_at` then `id` text."""
    groups: dict[tuple[UUID | None, str], list[StatementRow]] = {}
    for row in rows:
        if row.recorded_at <= k:
            groups.setdefault((row.site_id, row.period), []).append(row)
    return {key: _latest(group, lambda r: r.recorded_at) for key, group in groups.items()}


def percentage(tolerance: Decimal) -> str:
    """§2.7: the tolerance as a percentage (`1%`, `0.5%`)."""
    with localcontext(EXACT):
        return format((tolerance * 100).normalize(), "f") + "%"


def _cites(text: str, token: str) -> bool:
    """§2.4: `token` appears as a whole token (not preceded by a digit or `.`, not followed by a digit)."""
    return re.search(r"(?<![0-9.])" + re.escape(token) + r"(?![0-9])", text) is not None


class _Read:
    """One call's view (handshake R9): the Sites, the tolerance and the months, each read at most once."""

    def __init__(self, months: CommercialMonths, store: CommercialStore, tenant_id: UUID,
                 known_at: datetime | None) -> None:
        self.months = months
        self.tenant_id = tenant_id
        self.known_at = known_at
        self.k = known_at if known_at is not None else months.clock()
        self.sites: tuple[SiteRow, ...] = store.site_rows(tenant_id)
        self.codes = {s.site_id: s.site_code for s in self.sites}
        self.tolerance = _tolerance_at(store.tolerances(tenant_id), self.k)
        self._months: dict[tuple[UUID, str], MonthAmounts] = {}
        self._checks: dict[UUID, StatementCheck] = {}

    def scope(self, site_id: UUID | None) -> tuple[UUID, ...]:
        """§2.1: one Site, or every mini-grid Site of the tenant (D-3A7.11)."""
        if site_id is not None:
            return (site_id,)
        return tuple(s.site_id for s in self.sites if SITE_TYPE_TO_STRUCTURE.get(s.site_type) == MINI_GRID)

    def month(self, site_id: UUID, period: str) -> MonthAmounts:
        key = (site_id, period)
        if key not in self._months:
            self._months[key] = self.months.site_month(self.tenant_id, site_id, period, known_at=self.known_at)
        return self._months[key]

    def check(self, row: StatementRow) -> StatementCheck:
        if row.id not in self._checks:
            months = [self.month(sid, row.period) for sid in self.scope(row.site_id)]
            headings = tuple(_heading(name, Decimal(amount), self.tolerance, row.currency, months)
                             for name, amount in (("revenue", row.revenue), ("fuel_cost", row.fuel_cost)))
            state = _statement_state(headings)
            opens = state == MATCHED and all(h.reason is None for h in headings)
            self._checks[row.id] = StatementCheck(
                statement_id=row.id, site_id=row.site_id, site_code=self.codes.get(row.site_id) if row.site_id else None,
                period=row.period, currency=row.currency, tolerance=self.tolerance, state=state, opens=opens,
                headings=headings, recorded_by=row.recorded_by, recorded_at=row.recorded_at,
                recorded_by_script=row.recorded_by_script, source_ref=row.source_ref)
        return self._checks[row.id]

    def cited_order(self, current: Iterable[StatementRow]) -> list[StatementRow]:
        """§2.3: period descending, the organisation's before Sites', then Site code."""
        by_period = sorted(current, key=lambda r: (r.site_id is not None, self.codes.get(r.site_id, "")))
        return sorted(by_period, key=lambda r: r.period, reverse=True)


class CommercialReconciliation:
    def __init__(self, months: CommercialMonths, store: CommercialStore, *,
                 owner_file: Callable[[str], bytes | None] | None = None) -> None:
        """`owner_file(owner_ref)` returns the bytes of that file under the owner root, or None when it is absent
        (§2.4; the composition builds it from the repository root, tests from a temporary folder). Without it no
        tolerance can be set and 1 in 100 stands. It is a port: this module touches no file (the persistence guard)."""
        self._months = months
        self._store = store
        self._owner_file = owner_file

    # --- reads ----------------------------------------------------------------------------------------------------

    def tolerance(self, tenant_id: UUID, *, known_at: datetime | None = None) -> Decimal:
        k = known_at if known_at is not None else self._months.clock()
        return _tolerance_at(self._store.tolerances(tenant_id), k)

    def check(self, tenant_id: UUID, statement: StatementRow, *, known_at: datetime | None = None) -> StatementCheck:
        """§2.2 for one statement, at `k`."""
        return _Read(self._months, self._store, tenant_id, known_at).check(statement)

    def statements(self, tenant_id: UUID, *, known_at: datetime | None = None) -> tuple[StatementCheck, ...]:
        """The statements current at `k`, by (period, the organisation's first, Site code)."""
        read = _Read(self._months, self._store, tenant_id, known_at)
        current = _current(self._store.accounts_statements(tenant_id), read.k).values()
        ordered = sorted(current, key=lambda r: (r.period, r.site_id is not None, read.codes.get(r.site_id, "")))
        return tuple(read.check(r) for r in ordered)

    def standing(self, tenant_id: UUID, site_id: UUID | None, period: str, *,
                 known_at: datetime | None = None) -> MoneyStanding:
        """§2.3: whether money of this Site-month (or the organisation's month) reads reconciled at `k`."""
        rows = self._store.accounts_statements(tenant_id)
        read = _Read(self._months, self._store, tenant_id, known_at)
        current = _current(rows, read.k)
        keys = ([(site_id, period)] if site_id is not None else []) + [(None, period)]
        covering = [current[key] for key in keys if key in current]  # Site first
        checks = [read.check(r) for r in covering]

        def made(reconciled: bool, reason: str, this_month: StatementCheck | None,
                 cited: StatementCheck | None = None) -> MoneyStanding:
            return MoneyStanding(tenant_id, site_id, period, known_at, reconciled, reason, this_month, cited,
                                 read.tolerance)

        for state, reason in ((NOT_MATCHED, THIS_MONTH_NOT_MATCHED), (NOT_COMPARABLE, THIS_MONTH_NOT_COMPARABLE)):
            for check in checks:
                if check.state == state:
                    return made(False, reason, check)
        gate = next((c for c in (read.check(r) for r in read.cited_order(current.values())) if c.opens), None)
        if gate is not None:
            this_month = checks[0] if checks else None
            return made(True, RECONCILED, this_month, this_month or gate)
        return made(False, NO_STATEMENT if not current else NONE_MATCHED, checks[0] if checks else None)

    # --- writes ---------------------------------------------------------------------------------------------------

    def record(self, tenant_id: UUID, actor: Actor, *, site_code: str | None, period: str, currency: str,
               revenue: str, fuel_cost: str, source_ref: str, by_script: bool) -> StatementCheck:
        """§2.5: refusals in order, nothing written; then the live check and one statement row."""
        if actor.role not in roles_of(COMMAND):
            raise ReconRefused("RECON_ROLE")
        if not isinstance(period, str) or _PERIOD.fullmatch(period) is None:
            raise ReconRefused("RECON_PERIOD")
        read = _Read(self._months, self._store, tenant_id, None)
        site_id: UUID | None = None
        if site_code is not None:
            found = [s for s in read.sites if s.site_code.lower() == site_code.lower()]
            if not found:
                raise ReconRefused("RECON_SITE_UNKNOWN", {"site": site_code})
            if SITE_TYPE_TO_STRUCTURE.get(found[0].site_type) != MINI_GRID:
                raise ReconRefused("RECON_SITE_TYPE", {"site": site_code})
            site_id = found[0].site_id
        if not isinstance(currency, str) or _CURRENCY.fullmatch(currency) is None:
            raise ReconRefused("RECON_CURRENCY")
        for heading, amount in (("revenue", revenue), ("fuel_cost", fuel_cost)):
            if not isinstance(amount, str) or _AMOUNT.fullmatch(amount) is None:
                raise ReconRefused("RECON_AMOUNT", {"heading": heading})
        if (not isinstance(source_ref, str) or not 1 <= len(source_ref) <= _SOURCE_REF_MAX
                or source_ref != source_ref.strip() or has_control_character(source_ref)):
            raise ReconRefused("RECON_SOURCE_REF")
        scope = read.scope(site_id)
        if not scope:
            raise ReconRefused("RECON_SITE_UNKNOWN")  # an organisation with no mini-grid Site
        if any(not read.month(sid, period).closed for sid in scope):
            raise ReconRefused("RECON_MONTH_OPEN", {"period": period})
        row = StatementRow(id=uuid4(), tenant_id=tenant_id, site_id=site_id, period=period, currency=currency,
                           revenue=revenue, fuel_cost=fuel_cost, source_ref=source_ref, recorded_at=read.k,
                           recorded_by=actor.person_id, recorded_role=actor.role, recorded_by_script=by_script,
                           result_at_record=NOT_COMPARABLE, tolerance_at_record=format(read.tolerance, "f"))
        check = read.check(row)
        self._store.add_accounts_statement(StatementRow(**{**vars(row), "result_at_record": check.state}))
        return check

    def set_tolerance(self, tenant_id: UUID, tolerance: str, owner_ref: str) -> None:
        """§2.4: `0 < tolerance <= 0.05`, at most four decimals, citing an owner file under the owner root whose
        text names the tenant's slug and the figure (as written or as its percentage), each as a whole token."""
        if not isinstance(tolerance, str) or _TOLERANCE.fullmatch(tolerance) is None:
            raise ReconRefused("TOLERANCE_INVALID")
        value = Decimal(tolerance)
        if not Decimal(0) < value <= _MAX_TOLERANCE:
            raise ReconRefused("TOLERANCE_INVALID")
        if not isinstance(owner_ref, str) or _OWNER_REF.fullmatch(owner_ref) is None:
            raise ReconRefused("OWNER_REF_INVALID")
        slug = self._store.tenant_slug(tenant_id)
        data = self._owner_file(owner_ref) if self._owner_file is not None else None
        if slug is None or data is None:
            raise ReconRefused("OWNER_REF_INVALID")
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = ""
        if not (_cites(text, slug) and (_cites(text, tolerance) or _cites(text, percentage(value)))):
            raise ReconRefused("OWNER_REF_INVALID")
        self._store.add_tolerance(ToleranceRow(id=uuid4(), tenant_id=tenant_id, tolerance=tolerance,
                                               owner_ref=owner_ref, owner_ref_sha256=hashlib.sha256(data).hexdigest(),
                                               set_at=self._months.clock()))


__all__ = ["CURRENCY_MISMATCH", "DEFAULT_TOLERANCE", "EXACT", "HEADINGS", "CommercialReconciliation",
           "HeadingCheck", "MoneyStanding", "ReconRefused", "StatementCheck", "percentage"]
