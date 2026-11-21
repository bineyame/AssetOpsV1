"""3A7 (spec `specs/3A7-month-reconciled/spec.md` §2; rulings D-3A7.1 to D-3A7.15): one closed month reconciled
against the operator's own management accounts. A reading of the structure over commercial records, so it lives under
`structure` (D-3A7.14; the commercial package never imports `structure`, D-3A4.8).

The finance lead records a closed month's revenue and fuel cost from the management accounts, for one mini-grid Site
or the organisation. Each read compares them, exactly and at its instant `k`, with the money the screen shows (4b's
definition, summed over the scope; D-3A7.1, D-3A7.3, D-3A7.9) within the tenant's tolerance at `k` (1 in 100 unless
the owner set another, RC8, D-3A7.12). Money reads Recorded only while a current statement compared on both headings
against recorded lines matches (it *opens* the gate, D-3A7.8) and no statement covering the month disagrees or cannot
be compared (D-3A7.2); otherwise it is not yet reconciled. A missing figure is never 0: a heading with no used line
matches only where the accounts themselves state 0.00, and that never opens the gate.

Every sentence is an SC-1 statement (`i18n/statements/en/reconciliation.py`, D-SC1.28): this module hands the composer
typed facts and keeps no word of its own (it is in the statement guard's `ADOPTED`). The record forms it validates
against live with the rows (`commercial/model.py`).
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from decimal import (Context, Decimal, DivisionByZero, Inexact, InvalidOperation, Overflow, Rounded, localcontext)
from typing import Any, Callable, Iterable, Mapping, Sequence
from uuid import UUID, uuid4

from assetops_backend.accounts.permissions import roles_of
from assetops_backend.commercial.model import (AMOUNT_FORM, CURRENCY_FORM, OWNER_REF_FORM, PERIOD_FORM, TOLERANCE_FORM,
                                               SiteRow, StatementRow, ToleranceRow, cites_figure, cites_slug,
                                               percent_token)
from assetops_backend.commercial.months import CommercialMonths, MonthAmounts
from assetops_backend.commercial.store import CommercialStore
from assetops_backend.commercial.uploads import Actor, has_control_character
from assetops_backend.i18n import (Absent, Count, Evidence, Items, Message, Money, Month, Name, Percent, State, Word,
                                   message, render)
from assetops_backend.structure.evaluate import weakest_origin
from assetops_backend.structure.money import line_origins, line_sources, used_lines
from assetops_backend.structure.read import SITE_TYPE_TO_STRUCTURE

#: The headings, in order (spec §2.1), each with its key in the `heading` vocabulary.
HEADING_WORDS = {"revenue": "REVENUE", "fuel_cost": "FUEL_COST"}
HEADINGS = tuple(HEADING_WORDS)
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
#: D-3A7.10: the share is computed for display only; the formats round it.
DISPLAY = Context(prec=34, traps=[InvalidOperation, DivisionByZero, Overflow])
#: The evidence of the finance lead's figures and of the tolerance: declared from the operator's own accounts or by
#: the owner (RC8), so "Recorded" on the page (D-SC1.18).
FINANCIAL = "observed-financial"
DECLARED = Evidence("DECLARED", FINANCIAL)
#: A heading's state as the heading statement names it: its reason where it has one.
_WORD_STATE = {ZERO_STATED: "ZERO_STATED"}
#: The statement refusals that have a sentence (`set-tolerance`'s refusals are codes only, spec §5).
REFUSALS = ("RECON_ROLE", "RECON_PERIOD", "RECON_SITE_UNKNOWN", "RECON_SITE_TYPE", "RECON_CURRENCY", "RECON_AMOUNT",
            "RECON_SOURCE_REF", "RECON_MONTH_OPEN")
#: The standing reasons whose sentence names this month's own statement.
_NAMES_THIS_MONTH = (THIS_MONTH_NOT_MATCHED, THIS_MONTH_NOT_COMPARABLE)
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
    words: Message
    text: str


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
    words: Message
    text: str


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
    words: Message                   # the standing sentence
    text: str
    #: D-3A7.13: for THIS_MONTH_NOT_MATCHED and THIS_MONTH_NOT_COMPARABLE, the `text` of each of `this_month`'s
    #: headings that is not MATCHED, in heading order; otherwise empty. Each is its own rendered sentence: the
    #: composer joins no sentences, so a reader shows them after `text` (packet, Known deviations D1).
    details: tuple[str, ...]


# --- pure rules -----------------------------------------------------------------------------------------------


def _compare(accounts: Decimal, recorded: Decimal, tolerance: Decimal) -> str:
    """§2.2 rule 4, exact: `abs(recorded - accounts) <= tolerance * accounts`."""
    with localcontext(EXACT):
        return MATCHED if abs(recorded - accounts) <= tolerance * accounts else NOT_MATCHED


def _month(period: str) -> Month:
    return Month(int(period[:4]), int(period[5:]))


def _scope(site_code: str | None) -> dict[str, Any]:
    """SC-1 §5.4's `reconciliation.scope` facts: a Site by its code, or the organisation."""
    if site_code is None:
        return {"scope": State("ORGANISATION"), "site": Absent("ORGANISATION")}
    return {"scope": State("SITE"), "site": Name(site_code, "site.code")}


def _tolerance(tolerance: Decimal) -> Percent:
    return Percent(tolerance, DECLARED)


def heading_words(heading: str, state: str, reason: str | None, accounts: Decimal, recorded: Decimal | None,
                  tolerance: Decimal, currency: str, period: str, record_currencies: Sequence[str], *,
                  origins: Sequence[str] = ()) -> Message:
    """§2.7 as SC-1 §5.1's `reconciliation.heading`. The facts are computed here, exactly, and handed over; the
    statement chooses the sentence, the rounding and whether the share shows. The records' figures carry the weakest
    origin of the used lines (`origins`; none named reads "Estimated"); the difference and the share derive from
    them and the accounts, so they carry that origin too (the accounts' origin is the strongest)."""
    origin = weakest_origin(origins)
    with localcontext(EXACT):
        allowed = tolerance * accounts
    facts: dict[str, Any] = {
        "state": State(_WORD_STATE.get(reason, reason or state)),
        "heading": Word("heading", HEADING_WORDS[heading]),
        "records": Word("record_noun", HEADING_WORDS[heading]),
        "accounts": Money(accounts, currency, DECLARED),
        "allowed": Money(allowed, currency, Evidence("DERIVED", FINANCIAL)),
        "tolerance": _tolerance(tolerance),
        "month": _month(period),
        "currency": Name(currency, "statement.currency"),
    }
    if record_currencies:
        facts["record_currencies"] = Items(tuple(Name(c, "record.currency") for c in record_currencies))
    if recorded is not None:
        with localcontext(EXACT):
            difference = recorded - accounts
        facts["recorded"] = Money(recorded, currency, Evidence("RECORDED", origin))
        facts["difference"] = Money(difference, currency, Evidence("DERIVED", origin))
        facts["share"] = Absent("ACCOUNTS_ZERO") if accounts == 0 else _share(difference, accounts, origin)
    return message("reconciliation.heading", **facts)


def _share(difference: Decimal, accounts: Decimal, origin: str | None) -> Percent:
    """D-3A7.10: the gap as a fraction of the accounts' figure, for display (the format rounds it up)."""
    with localcontext(DISPLAY):
        return Percent(abs(difference) / accounts, Evidence("DERIVED", origin))


def statement_words(state: str, period: str, site_code: str | None, tolerance: Decimal) -> Message:
    """§2.7's statement sentence: one statement's live check."""
    return message("reconciliation.statement", state=State(state), month=_month(period), **_scope(site_code),
                   tolerance=_tolerance(tolerance))


def standing_words(reason: str, shown: StatementCheck | None, site_code: str | None, tolerance: Decimal) -> Message:
    """§2.7's standing sentence. `shown` is the month the sentence names (the cited month, or this month's
    statement); with none, the scope is the standing's own and no month is named."""
    facts: dict[str, Any] = {"reason": State(reason), "tolerance": _tolerance(tolerance)}
    if shown is None:
        facts.update(_scope(site_code))
    else:
        facts.update(_scope(shown.site_code), month=_month(shown.period))
    return message("reconciliation.standing", **facts)


def money_word(figure: Money, standing: MoneyStanding) -> str:
    """§2.3 through the shared evidence format (D-SC1.16): the figure's own evidence word, with "not yet reconciled"
    while the standing is not reconciled. `figure` is the money the reader shows, with its own evidence."""
    marked = Evidence(figure.evidence.evidence, figure.evidence.origin, standing.reconciled)
    return render(message("reconciliation.money_word", figure=Money(figure.value, figure.currency, marked)))


#: A refusal's params as the refusal statement's facts.
_REFUSAL_FACTS: Mapping[str, Callable[[str], dict[str, Any]]] = {
    "site": lambda value: {"site": Name(value, "site.code")},
    "heading": lambda value: {"heading": Word("heading", HEADING_WORDS[value])},
    "period": lambda value: {"month": _month(value)},
}


def refusal_words(refused: ReconRefused) -> Message:
    """§2.5's refusal sentence for a refused statement; `KeyError` for a code that has none (`set-tolerance`'s)."""
    if refused.code not in REFUSALS:
        raise KeyError(refused.code)
    facts: dict[str, Any] = {"code": State(refused.code), "limit": Count(_SOURCE_REF_MAX, "character")}
    for name, value in refused.params.items():
        facts.update(_REFUSAL_FACTS[name](value))
    return message("reconciliation.refused", **facts)


def _heading(heading: str, accounts: Decimal, tolerance: Decimal, currency: str, period: str,
             months: Sequence[MonthAmounts]) -> HeadingCheck:
    lines = [line for month in months for line in used_lines(heading, month.lines)]
    currencies = tuple(sorted({line.currency for line in lines if line.currency is not None}))
    sources = line_sources(lines)
    origins = line_origins(lines)
    with localcontext(EXACT):
        allowed = tolerance * accounts

    def made(state: str, reason: str | None, recorded: Decimal | None = None,
             difference: Decimal | None = None) -> HeadingCheck:
        words = heading_words(heading, state, reason, accounts, recorded, tolerance, currency, period, currencies,
                              origins=origins)
        return HeadingCheck(heading, state, reason, accounts, recorded, difference, allowed, currencies, sources,
                            origins, words, render(words))

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
            amounts = {"revenue": row.revenue, "fuel_cost": row.fuel_cost}
            headings = tuple(_heading(name, Decimal(amounts[name]), self.tolerance, row.currency, row.period, months)
                             for name in HEADINGS)
            state = _statement_state(headings)
            opens = state == MATCHED and all(h.reason is None for h in headings)
            code = self.codes.get(row.site_id) if row.site_id else None
            words = statement_words(state, row.period, code, self.tolerance)
            self._checks[row.id] = StatementCheck(
                statement_id=row.id, site_id=row.site_id, site_code=code,
                period=row.period, currency=row.currency, tolerance=self.tolerance, state=state, opens=opens,
                headings=headings, recorded_by=row.recorded_by, recorded_at=row.recorded_at,
                recorded_by_script=row.recorded_by_script, source_ref=row.source_ref, words=words, text=render(words))
        return self._checks[row.id]

    def cited_order(self, current: Iterable[StatementRow]) -> list[StatementRow]:
        """§2.3: period descending, the organisation's before Sites', then Site code."""
        by_period = sorted(current, key=lambda r: (r.site_id is not None, self.codes.get(r.site_id, "")))
        return sorted(by_period, key=lambda r: r.period, reverse=True)


class CommercialReconciliation:
    def __init__(self, months: CommercialMonths, store: CommercialStore, *,
                 owner_file: Callable[[str], bytes | None] | None = None) -> None:
        """`owner_file(owner_ref)` returns the bytes of that file under the owner root, or None when it is absent
        (§2.4, D-3A7.15; the command builds it from the owner root and the composition passes it through, tests use
        an in-memory reader). Without it no tolerance can be set and 1 in 100 stands. It is a port: this module
        touches no file (the persistence guard)."""
        self._months = months
        self._store = store
        self._owner_file = owner_file

    # --- reads ----------------------------------------------------------------------------------------------------

    def site(self, tenant_id: UUID, site_code: str) -> SiteRow | None:
        """The tenant's Site with this code (any case, as `record` matches it), or None."""
        return next((s for s in self._store.site_rows(tenant_id) if s.site_code.lower() == site_code.lower()), None)

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
            shown = cited if reconciled else (this_month if reason in _NAMES_THIS_MONTH else None)
            words = standing_words(reason, shown, read.codes.get(site_id) if site_id else None, read.tolerance)
            details = (tuple(h.text for h in this_month.headings if h.state != MATCHED)
                       if this_month is not None and reason in _NAMES_THIS_MONTH else ())
            return MoneyStanding(tenant_id, site_id, period, known_at, reconciled, reason, this_month, cited,
                                 read.tolerance, words, render(words), details)

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
        if not isinstance(period, str) or PERIOD_FORM.fullmatch(period) is None:
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
        if not isinstance(currency, str) or CURRENCY_FORM.fullmatch(currency) is None:
            raise ReconRefused("RECON_CURRENCY")
        amounts = {"revenue": revenue, "fuel_cost": fuel_cost}
        for heading in HEADINGS:
            if not isinstance(amounts[heading], str) or AMOUNT_FORM.fullmatch(amounts[heading]) is None:
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
                           result_at_record=NOT_COMPARABLE, tolerance_at_record=str(read.tolerance))
        check = read.check(row)
        self._store.add_accounts_statement(StatementRow(**{**vars(row), "result_at_record": check.state}))
        return check

    def set_tolerance(self, tenant_id: UUID, tolerance: str, owner_ref: str) -> ToleranceRow:
        """§2.4: `0 < tolerance <= 0.05`, at most four decimals, citing an owner file under the owner root whose
        text names the tenant's slug and the figure (as written or as its percentage), each as a whole token."""
        if not isinstance(tolerance, str) or TOLERANCE_FORM.fullmatch(tolerance) is None:
            raise ReconRefused("TOLERANCE_INVALID")
        value = Decimal(tolerance)
        if not Decimal(0) < value <= _MAX_TOLERANCE:
            raise ReconRefused("TOLERANCE_INVALID")
        if not isinstance(owner_ref, str) or OWNER_REF_FORM.fullmatch(owner_ref) is None:
            raise ReconRefused("OWNER_REF_INVALID")
        slug = self._store.tenant_slug(tenant_id)
        data = self._owner_file(owner_ref) if self._owner_file is not None else None
        if slug is None or data is None:
            raise ReconRefused("OWNER_REF_INVALID")
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = ""
        if not (cites_slug(text, slug) and (cites_figure(text, tolerance) or cites_figure(text, percent_token(value)))):
            raise ReconRefused("OWNER_REF_INVALID")
        row = ToleranceRow(id=uuid4(), tenant_id=tenant_id, tolerance=tolerance, owner_ref=owner_ref,
                           owner_ref_sha256=hashlib.sha256(data).hexdigest(), set_at=self._months.clock())
        self._store.add_tolerance(row)
        return row

