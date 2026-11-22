"""6a (`specs/6a-decision-records/spec.md` §3.2 to §3.5; D-P6.1 to D-P6.29): a decision on a Site's lever, its options
(always including no action), the one-off a person states for an option, the evaluation runs 6c writes, and the
executive's choice. This module computes no value (6c does) and holds codes only (D-0K4.19): a refusal's sentence is
rendered from statement `decision.refused`. It is in the SC-1 guard's `ADOPTED` scope. It imports no adapter.

The store is injected (`DecisionStore`); `MemoryDecisionStore` serves the unit tests and re-implements every identity
rule, both deferred checks of migration 0072 and the newest-first order.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from decimal import Decimal
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Callable, Literal, Mapping, Protocol
from uuid import UUID, uuid4

from assetops_backend.accounts.permissions import roles_of
from assetops_backend.actions.agreed import clean_title
from assetops_backend.chain.ports import SiteRef
from assetops_backend.i18n import Count, State, message, render
from assetops_backend.structure import pins as _pins
from assetops_backend.structure.levers import LEVERS, Lever, grid, option_key
from assetops_backend.structure.read import SITE_TYPE_TO_STRUCTURE
from assetops_backend.structure.registry import REGISTRIES

if TYPE_CHECKING:
    from assetops_backend.accounts.service import AccountService

NO_ACTION_KEY = "no-action"
RULE_VERSION = "decision-prepare-1"
HORIZON_DEFAULT = 12  # D-P6.15
HORIZON_MIN, HORIZON_MAX = 1, 60
COMMANDS = MappingProxyType({"prepare": "decision.prepare", "one_off": "decision.one_off",
                             "choose": "decision.choose"})
DISPOSITIONS = ("COMPARISON", "RECOMMENDED", "CONDITIONAL", "ACCEPTABLE", "DEFERRED", "REJECTED")
RUN_OUTCOMES = ("RECOMMENDED", "NO_ACTION_BEST", "RANKING_INCOMPLETE", "NOTHING_ADMITTED")
SOURCE_CLASSES = ("SIMULATED", "EMULATED", "RECORDED")  # weakest first
STATE_NOT_VALUED, STATE_WAITING, STATE_CHOSEN, STATE_UNDER_WAY, STATE_KEPT = (
    "NOT_VALUED", "WAITING", "CHOSEN", "UNDER_WAY", "KEPT_AS_IS")
AMOUNT_PLACES, AMOUNT_INTEGER_DIGITS, CURRENCY_LETTERS, BASIS_MAX = 2, 12, 3, 200

#: §3.3 refusal codes and their exit codes (3 only for the store).
REFUSAL_EXIT: Mapping[str, int] = MappingProxyType({
    **{code: 2 for code in (
        "UNKNOWN_TENANT", "PERSON_NOT_FOUND", "PERSON_ROLE_REQUIRED", "BAD_PERIOD", "BAD_HORIZON", "SITE_NOT_FOUND",
        "LEVER_UNKNOWN", "LEVER_SITE_TYPE", "FINDING_NOT_FOUND", "FINDING_NOT_ON_LEVER", "BAD_CURRENT",
        "ALREADY_PREPARED_OTHER", "DECISION_NOT_FOUND", "OPTION_NOT_FOUND", "NO_ACTION_ONE_OFF", "BAD_AMOUNT",
        "BAD_CURRENCY", "BAD_CREW_VISITS", "BAD_BASIS", "ALREADY_CHOSEN", "NOT_EVALUATED", "CHOOSE_NONE_INSTEAD",
        "OPTION_REJECTED", "ACTION_NOT_FOUND", "ACTION_SITE_MISMATCH", "BAD_UUID", "NO_DATABASE",
        "RECORD_INVALID")},
    "DECISIONS_UNAVAILABLE": 3})


@dataclass(frozen=True)
class DecisionRow:
    id: UUID
    tenant_id: UUID
    site_id: UUID
    structure_key: str
    lever_id: str
    purpose_factor_id: str
    finding_id: UUID | None
    period: str
    horizon_months: int
    current_settings: Mapping[str, Decimal]
    rule_version: str
    prepared_by_person_id: UUID
    prepared_role: str
    prepared_by_script: bool
    prepared_at: datetime


@dataclass(frozen=True)
class OptionRow:
    id: UUID
    tenant_id: UUID
    decision_id: UUID
    option_key: str
    generator: str
    settings: Mapping[str, Decimal]
    position: int


@dataclass(frozen=True)
class OneOffRow:
    id: UUID
    tenant_id: UUID
    option_id: UUID
    amount: Decimal
    currency: str
    crew_visits: int
    basis: str
    declared_by_person_id: UUID
    declared_role: str
    declared_by_script: bool
    declared_at: datetime


@dataclass(frozen=True)
class MissingInput:
    record_kind: str
    source_family: str
    factor_id: str | None


@dataclass(frozen=True)
class EffectRow:
    factor_id: str
    position: int
    change_per_month: Decimal | None
    unit: str
    currency: str | None
    missing: tuple[MissingInput, ...]


@dataclass(frozen=True)
class EvaluationRow:
    id: UUID
    option_id: UUID
    disposition: str
    reason_code: str | None
    rank: int | None
    monthly_change: Decimal | None
    horizon_change: Decimal | None
    one_off_id: UUID | None
    value: Decimal | None
    currency: str | None
    source_class: str
    evidence_class: str
    missing: tuple[MissingInput, ...]
    assumed: tuple[str, ...]
    admission: Mapping[str, Any] | None
    dawn: Mapping[str, Any] | None
    effects: tuple[EffectRow, ...]


@dataclass(frozen=True)
class RunRow:
    id: UUID
    tenant_id: UUID
    decision_id: UUID
    evaluator_version: str
    outcome: str
    study_sha256: str | None
    study_identity: Mapping[str, Any] | None
    known_at: datetime
    run_by_person_id: UUID
    run_role: str
    run_by_script: bool
    run_at: datetime
    evaluations: tuple[EvaluationRow, ...]  # option position order


@dataclass(frozen=True)
class ChoiceRow:
    id: UUID
    tenant_id: UUID
    decision_id: UUID
    option_id: UUID | None
    run_id: UUID
    agreed_action_id: UUID | None
    chosen_by_person_id: UUID
    chosen_role: str
    chosen_by_script: bool
    chosen_at: datetime


@dataclass(frozen=True)
class DecisionBundle:
    decision: DecisionRow
    site_code: str
    site_name: str
    options: tuple[OptionRow, ...]
    one_offs: Mapping[UUID, OneOffRow]  # latest, by option id
    run: RunRow | None
    choice: ChoiceRow | None
    names: Mapping[UUID, str]  # person id -> display name, for every person id in the bundle


@dataclass(frozen=True)
class Prepared:
    decision: DecisionRow
    options: tuple[OptionRow, ...]
    already_prepared: bool


@dataclass(frozen=True)
class Chosen:
    choice: ChoiceRow
    already_chosen: bool


class DecisionRefused(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code
        self.exit = REFUSAL_EXIT.get(code, 2)


class StoreUnavailable(Exception):
    """The store could not answer (the adapter wraps its driver's errors in this); `DECISIONS_UNAVAILABLE`."""


class DecisionStore(Protocol):
    def site(self, tenant_id: UUID, site_code: str) -> SiteRef | None: ...
    def site_by_id(self, tenant_id: UUID, site_id: UUID) -> SiteRef | None: ...  # D-P6.20; read by 6c
    def finding(self, tenant_id: UUID, site_id: UUID, finding_id: UUID) -> str | None: ...  # its mechanism
    def find_decision(self, tenant_id: UUID, site_id: UUID, lever_id: str, period: str,
                      finding_id: UUID | None) -> DecisionRow | None: ...
    def add_decision(self, row: DecisionRow, options: tuple[OptionRow, ...]) -> tuple[DecisionRow, bool]: ...
    def decision(self, tenant_id: UUID, decision_id: UUID) -> tuple[DecisionRow, tuple[OptionRow, ...]] | None: ...
    def add_one_off(self, row: OneOffRow) -> OneOffRow: ...
    def latest_one_offs(self, tenant_id: UUID, decision_id: UUID) -> Mapping[UUID, OneOffRow]: ...
    def add_run(self, run: RunRow) -> RunRow: ...  # 6c's writer
    def latest_run(self, tenant_id: UUID, decision_id: UUID) -> RunRow | None: ...
    def agreed_action_site(self, tenant_id: UUID, action_id: UUID) -> UUID | None | Literal[False]: ...
    def add_choice(self, row: ChoiceRow) -> tuple[ChoiceRow, bool]: ...
    def choice(self, tenant_id: UUID, decision_id: UUID) -> ChoiceRow | None: ...
    def for_tenant(self, tenant_id: UUID, period_from: str | None, period_to: str | None
                   ) -> tuple[DecisionBundle, ...]: ...


# --- the read's shapes (§3.5) --------------------------------------------------------------------------------------

@dataclass(frozen=True)
class OneOffView:
    amount: Decimal
    currency: str
    crew_visits: int
    basis: str
    declared_by_name: str
    declared_at: datetime


@dataclass(frozen=True)
class OptionView:
    option_key: str
    generator: str
    settings: Mapping[str, Decimal]
    position: int
    one_off: OneOffView | None
    evaluation: EvaluationRow | None  # from the latest run


@dataclass(frozen=True)
class RecommendedView:
    option_key: str
    value: Decimal
    currency: str


@dataclass(frozen=True)
class RunSummary:
    run_id: str
    outcome: str
    run_at: datetime
    run_by_name: str
    source_class: str  # the weakest of its evaluations'


@dataclass(frozen=True)
class ChoiceView:
    option_key: str | None
    chosen_by_name: str
    chosen_at: datetime
    run_id: str
    agreed_action_id: str | None


@dataclass(frozen=True)
class DecisionView:
    decision_id: str
    site_code: str
    site_name: str
    lever_id: str
    purpose_factor_id: str
    home_category: str
    finding_id: str | None
    period: str
    horizon_months: int
    prepared_by_name: str
    prepared_at: datetime
    state: str
    decides_role: str
    recommended: RecommendedView | None
    options: tuple[OptionView, ...]
    run: RunSummary | None
    choice: ChoiceView | None


def refusal_sentence(code: str) -> str:
    """A refusal's sentence (spec §3.4), rendered from `decision.refused`; the bounds are counts."""
    return render(message("decision.refused", code=State(code), least=Count(HORIZON_MIN, "month"),
                          most=Count(HORIZON_MAX, "month"), places=Count(AMOUNT_PLACES, "character"),
                          letters=Count(CURRENCY_LETTERS, "character"), chars=Count(BASIS_MAX, "character")))


def _period_ok(period: object) -> bool:
    # The shape of the table's period CHECK: four digits, a hyphen, a month from 01 to 12.
    if not isinstance(period, str) or len(period) != 7 or period.find("-") != 4:
        return False
    digits = period[:4] + period[5:]
    return digits.isascii() and digits.isdigit() and 1 <= int(period[5:]) <= 12


def _currency_ok(currency: object) -> bool:
    return (isinstance(currency, str) and len(currency) == CURRENCY_LETTERS and currency.isascii()
            and currency.isalpha() and currency.isupper())


def _now(clock: Callable[[], datetime]) -> datetime:
    """D-3C2.10: one clock read per method, in whole UTC seconds. A naive datetime is a programming error."""
    value = clock()
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("the clock must return an aware datetime")
    return value.astimezone(timezone.utc).replace(microsecond=0)


def _same_settings(a: Mapping[str, Decimal], b: Mapping[str, Decimal]) -> bool:
    return set(a) == set(b) and all(a[k] == b[k] for k in a)


def _weakest(classes: list[str]) -> str:
    return min(classes, key=SOURCE_CLASSES.index)


def _amount_ok(amount: Decimal) -> bool:
    if not isinstance(amount, Decimal) or not amount.is_finite() or amount < 0:
        return False
    exponent = amount.normalize().as_tuple().exponent
    if exponent < -AMOUNT_PLACES:
        return False
    return len(str(int(amount))) <= AMOUNT_INTEGER_DIGITS


class DecisionService:
    def __init__(self, store: DecisionStore, accounts: AccountService, *, clock: Callable[[], datetime],
                 new_id: Callable[[], UUID] = uuid4, levers: Mapping[str, Lever] = LEVERS) -> None:
        self._store = store
        self._accounts = accounts
        self._clock = clock
        self._new_id = new_id
        self._levers = levers

    def _call(self, fn, *args):
        try:
            return fn(*args)
        except StoreUnavailable:
            raise DecisionRefused("DECISIONS_UNAVAILABLE") from None

    def _admit(self, command: str, tenant_slug: str, as_email: str):
        """C1 to C3: the tenant, the active person, a held role of the command's at any Site."""
        tenant_id = self._accounts.tenant_by_slug(tenant_slug)
        if tenant_id is None:
            raise DecisionRefused("UNKNOWN_TENANT")
        person = self._accounts.onboard_person(as_email)
        if person is None or person.tenant_slug != tenant_slug or not person.active:
            raise DecisionRefused("PERSON_NOT_FOUND")
        held = {role for role, _ in person.roles}
        role = next((r for r in roles_of(command) if r in held), None)
        if role is None:
            raise DecisionRefused("PERSON_ROLE_REQUIRED")
        return tenant_id, person, role

    # --- prepare -----------------------------------------------------------------------------------------------

    def prepare(self, *, tenant_slug: str, as_email: str, site_code: str, lever_id: str, period: str,
                current: Mapping[str, Decimal], finding_id: UUID | None,
                horizon_months: int = HORIZON_DEFAULT) -> Prepared:
        now = _now(self._clock)
        tenant_id, person, role = self._admit(COMMANDS["prepare"], tenant_slug, as_email)
        if not _period_ok(period):  # P1
            raise DecisionRefused("BAD_PERIOD")
        if isinstance(horizon_months, bool) or not HORIZON_MIN <= horizon_months <= HORIZON_MAX:
            raise DecisionRefused("BAD_HORIZON")
        site = self._call(self._store.site, tenant_id, site_code)  # P2
        if site is None:
            raise DecisionRefused("SITE_NOT_FOUND")
        lever = self._levers.get(lever_id)  # P3
        if lever is None:
            raise DecisionRefused("LEVER_UNKNOWN")
        if lever.structure_key != SITE_TYPE_TO_STRUCTURE.get(site.site_type):
            raise DecisionRefused("LEVER_SITE_TYPE")
        if finding_id is not None:  # P4
            mechanism = self._call(self._store.finding, tenant_id, site.site_id, finding_id)
            if mechanism is None:
                raise DecisionRefused("FINDING_NOT_FOUND")
            if not self._pin_lists_lever(mechanism, lever_id):
                raise DecisionRefused("FINDING_NOT_ON_LEVER")
        names = {axis.name for axis in lever.axes}  # P5
        if set(current) != names or any(not isinstance(v, Decimal) or not v.is_finite() for v in current.values()):
            raise DecisionRefused("BAD_CURRENT")
        found = self._call(self._store.find_decision, tenant_id, site.site_id, lever_id, period, finding_id)  # P6
        if found is not None:
            _, options = self._call(self._store.decision, tenant_id, found.id)
            if _same_settings(current, found.current_settings) and horizon_months == found.horizon_months:
                return Prepared(found, options, True)
            raise DecisionRefused("ALREADY_PREPARED_OTHER")
        decision = DecisionRow(self._new_id(), tenant_id, site.site_id, lever.structure_key, lever_id,  # P7
                               lever.purpose_factor, finding_id, period, horizon_months, dict(current), RULE_VERSION,
                               person.person_id, role, True, now)
        options = [OptionRow(self._new_id(), tenant_id, decision.id, NO_ACTION_KEY, "NO_ACTION", dict(current), 0)]
        for point in grid(lever):
            if not _same_settings(point, current):
                options.append(OptionRow(self._new_id(), tenant_id, decision.id, option_key(lever, point),
                                         lever.generator, dict(point), len(options)))
        stored, already = self._call(self._store.add_decision, decision, tuple(options))
        if already:
            _, options_back = self._call(self._store.decision, tenant_id, stored.id)
            if _same_settings(current, stored.current_settings) and horizon_months == stored.horizon_months:
                return Prepared(stored, options_back, True)
            raise DecisionRefused("ALREADY_PREPARED_OTHER")
        return Prepared(stored, tuple(options), False)

    @staticmethod
    def _pin_lists_lever(mechanism: str, lever_id: str) -> bool:
        pin = _pins.pin_of(mechanism)
        return pin is not None and lever_id in REGISTRIES[pin.structure_key].row(pin.factor_id).levers

    # --- one-off -----------------------------------------------------------------------------------------------

    def state_one_off(self, *, tenant_slug: str, as_email: str, decision_id: UUID, option_key: str, amount: Decimal,
                      currency: str, crew_visits: int, basis: str) -> OneOffRow:
        now = _now(self._clock)
        tenant_id, person, _ = self._admit(COMMANDS["one_off"], tenant_slug, as_email)
        found = self._call(self._store.decision, tenant_id, decision_id)  # O1
        if found is None:
            raise DecisionRefused("DECISION_NOT_FOUND")
        decision, options = found
        role = self._covering_role(person.roles, decision.site_id)  # O1b (D-P6.24)
        if role is None:
            raise DecisionRefused("PERSON_ROLE_REQUIRED")
        option = next((o for o in options if o.option_key == option_key), None)  # O2
        if option is None:
            raise DecisionRefused("OPTION_NOT_FOUND")
        if option.generator == "NO_ACTION":
            raise DecisionRefused("NO_ACTION_ONE_OFF")
        if not _amount_ok(amount):  # O3
            raise DecisionRefused("BAD_AMOUNT")
        if not _currency_ok(currency):
            raise DecisionRefused("BAD_CURRENCY")
        if isinstance(crew_visits, bool) or not isinstance(crew_visits, int) or crew_visits < 0:
            raise DecisionRefused("BAD_CREW_VISITS")
        cleaned = clean_title(basis) if isinstance(basis, str) else None
        if cleaned is None:
            raise DecisionRefused("BAD_BASIS")
        row = OneOffRow(self._new_id(), tenant_id, option.id, amount.quantize(Decimal("0.01")), currency,  # O4
                        crew_visits, cleaned, person.person_id, role, True, now)
        return self._call(self._store.add_one_off, row)

    @staticmethod
    def _covering_role(roles: frozenset[tuple[str, UUID | None]], site_id: UUID) -> str | None:
        for role in roles_of(COMMANDS["one_off"]):
            for held, grant_site in roles:
                if held == role and (role != "SITE_MANAGER" or grant_site == site_id):
                    return role
        return None

    # --- choose ------------------------------------------------------------------------------------------------

    def choose(self, *, tenant_slug: str, as_email: str, decision_id: UUID, option_key: str | None,
               agreed_action_id: UUID | None) -> Chosen:
        now = _now(self._clock)
        tenant_id, person, role = self._admit(COMMANDS["choose"], tenant_slug, as_email)
        found = self._call(self._store.decision, tenant_id, decision_id)  # H1
        if found is None:
            raise DecisionRefused("DECISION_NOT_FOUND")
        decision, options = found
        by_key = {o.option_key: o for o in options}
        wanted = by_key.get(option_key) if option_key is not None else None
        wanted_id = None if wanted is None else wanted.id
        existing = self._call(self._store.choice, tenant_id, decision.id)  # H2
        if existing is not None:
            if existing.option_id == wanted_id and existing.agreed_action_id == agreed_action_id \
                    and (option_key is None or wanted is not None):
                return Chosen(existing, True)
            raise DecisionRefused("ALREADY_CHOSEN")
        run = self._call(self._store.latest_run, tenant_id, decision.id)  # H3
        if run is None:
            raise DecisionRefused("NOT_EVALUATED")
        if option_key is not None:  # H4
            if wanted is None:
                raise DecisionRefused("OPTION_NOT_FOUND")
            evaluation = next((e for e in run.evaluations if e.option_id == wanted.id), None)
            if evaluation is not None and evaluation.disposition == "COMPARISON":
                raise DecisionRefused("CHOOSE_NONE_INSTEAD")
            if evaluation is not None and evaluation.disposition == "REJECTED":
                raise DecisionRefused("OPTION_REJECTED")
        if agreed_action_id is not None:  # H5
            action_site = self._call(self._store.agreed_action_site, tenant_id, agreed_action_id)
            if action_site is False:
                raise DecisionRefused("ACTION_NOT_FOUND")
            if action_site is None or action_site != decision.site_id:
                raise DecisionRefused("ACTION_SITE_MISMATCH")
        row = ChoiceRow(self._new_id(), tenant_id, decision.id, wanted_id, run.id, agreed_action_id,  # H6
                        person.person_id, role, True, now)
        stored, already = self._call(self._store.add_choice, row)
        if already and (stored.option_id != wanted_id or stored.agreed_action_id != agreed_action_id):
            raise DecisionRefused("ALREADY_CHOSEN")  # a race past H2: the stored choice differs (D-P6.33)
        return Chosen(stored, already)

    # --- the read (§3.5) ---------------------------------------------------------------------------------------

    def for_tenant(self, tenant_id: UUID, *, period_from: str | None = None,
                   period_to: str | None = None) -> tuple[DecisionView, ...]:
        for bound in (period_from, period_to):
            if bound is not None and not _period_ok(bound):
                raise DecisionRefused("BAD_PERIOD")
        if period_from is not None and period_to is not None and period_from > period_to:
            return ()
        bundles = self._call(self._store.for_tenant, tenant_id, period_from, period_to)
        return tuple(self._view(b) for b in bundles)

    def _home_category(self, bundle: DecisionBundle) -> str:
        d = bundle.decision
        registry = REGISTRIES[d.structure_key]
        factor = registry.row(d.purpose_factor_id)
        if d.finding_id is not None:
            mechanism = self._call(self._store.finding, d.tenant_id, d.site_id, d.finding_id)
            pin = None if mechanism is None else _pins.pin_of(mechanism)
            if pin is not None:
                factor = REGISTRIES[pin.structure_key].row(pin.factor_id)
        return factor.home.category

    def _view(self, bundle: DecisionBundle) -> DecisionView:
        d, run, choice, names = bundle.decision, bundle.run, bundle.choice, bundle.names
        evaluations = {} if run is None else {e.option_id: e for e in run.evaluations}
        key_of = {o.id: o.option_key for o in bundle.options}
        options = []
        for o in bundle.options:
            one_off = bundle.one_offs.get(o.id)
            options.append(OptionView(
                o.option_key, o.generator, o.settings, o.position,
                None if one_off is None else OneOffView(one_off.amount, one_off.currency, one_off.crew_visits,
                                                        one_off.basis, names[one_off.declared_by_person_id],
                                                        one_off.declared_at),
                evaluations.get(o.id)))
        recommended = None
        if run is not None:
            for e in run.evaluations:
                if e.disposition == "RECOMMENDED" and e.value is not None and e.currency is not None:
                    recommended = RecommendedView(key_of[e.option_id], e.value, e.currency)
                    break
        if choice is not None and choice.option_id is None:
            state = STATE_KEPT
        elif choice is not None and choice.agreed_action_id is not None:
            state = STATE_UNDER_WAY
        elif choice is not None:
            state = STATE_CHOSEN
        elif run is not None:
            state = STATE_WAITING
        else:
            state = STATE_NOT_VALUED
        return DecisionView(
            str(d.id), bundle.site_code, bundle.site_name, d.lever_id, d.purpose_factor_id, self._home_category(bundle),
            None if d.finding_id is None else str(d.finding_id), d.period, d.horizon_months,
            names[d.prepared_by_person_id], d.prepared_at, state, roles_of(COMMANDS["choose"])[0], recommended,
            tuple(options),
            None if run is None else RunSummary(str(run.id), run.outcome, run.run_at, names[run.run_by_person_id],
                                                _weakest([e.source_class for e in run.evaluations])),
            None if choice is None else ChoiceView(
                None if choice.option_id is None else key_of[choice.option_id], names[choice.chosen_by_person_id],
                choice.chosen_at, str(choice.run_id),
                None if choice.agreed_action_id is None else str(choice.agreed_action_id)))


class MemoryDecisionStore:
    """A `DecisionStore` in memory, for the unit tests: the Postgres identity rules, both deferred checks (raising
    `DecisionRefused("RECORD_INVALID")`) and the newest-first order."""

    def __init__(self) -> None:
        self.sites: dict[tuple[UUID, str], tuple[SiteRef, str]] = {}
        self.names: dict[UUID, str] = {}
        self.findings: dict[tuple[UUID, UUID, UUID], str] = {}
        self.actions: dict[tuple[UUID, UUID], UUID | None] = {}
        self.decisions: list[DecisionRow] = []
        self.options: list[OptionRow] = []
        self.one_offs: list[OneOffRow] = []
        self.runs: list[RunRow] = []
        self.choices: list[ChoiceRow] = []

    def add_site(self, tenant_id: UUID, code: str, site_type: str, site_id: UUID | None = None,
                 name: str | None = None, timezone_name: str = "UTC") -> UUID:
        sid = site_id or uuid4()
        self.sites[(tenant_id, code.lower())] = (SiteRef(tenant_id, sid, code, site_type, timezone_name), name or code)
        return sid

    def add_person(self, person_id: UUID, display_name: str) -> None:
        self.names[person_id] = display_name

    def add_finding(self, tenant_id: UUID, site_id: UUID, finding_id: UUID, mechanism: str) -> None:
        self.findings[(tenant_id, site_id, finding_id)] = mechanism

    def add_agreed_action(self, tenant_id: UUID, action_id: UUID, site_id: UUID | None) -> None:
        self.actions[(tenant_id, action_id)] = site_id

    def site(self, tenant_id: UUID, site_code: str) -> SiteRef | None:
        found = self.sites.get((tenant_id, site_code.lower()))
        return None if found is None else found[0]

    def site_by_id(self, tenant_id: UUID, site_id: UUID) -> SiteRef | None:
        return next((ref for (t, _), (ref, _) in self.sites.items() if t == tenant_id and ref.site_id == site_id), None)

    def finding(self, tenant_id: UUID, site_id: UUID, finding_id: UUID) -> str | None:
        return self.findings.get((tenant_id, site_id, finding_id))

    def find_decision(self, tenant_id, site_id, lever_id, period, finding_id) -> DecisionRow | None:
        return next((d for d in self.decisions if (d.tenant_id, d.site_id, d.lever_id, d.period, d.finding_id)
                     == (tenant_id, site_id, lever_id, period, finding_id)), None)

    def add_decision(self, row: DecisionRow, options: tuple[OptionRow, ...]) -> tuple[DecisionRow, bool]:
        stored = self.find_decision(row.tenant_id, row.site_id, row.lever_id, row.period, row.finding_id)
        if stored is not None:
            return stored, True
        no_action = [o for o in options if o.generator == "NO_ACTION"]  # decision_has_no_action
        if len(no_action) != 1 or no_action[0].option_key != NO_ACTION_KEY or no_action[0].position != 0:
            raise DecisionRefused("RECORD_INVALID")
        if len({o.option_key for o in options}) != len(options) or len({o.position for o in options}) != len(options):
            raise DecisionRefused("RECORD_INVALID")
        self.decisions.append(replace(row))
        self.options.extend(options)
        return row, False

    def decision(self, tenant_id: UUID, decision_id: UUID):
        row = next((d for d in self.decisions if d.tenant_id == tenant_id and d.id == decision_id), None)
        if row is None:
            return None
        return row, tuple(sorted((o for o in self.options if o.decision_id == decision_id),
                                 key=lambda o: o.position))

    def add_one_off(self, row: OneOffRow) -> OneOffRow:
        if not any(o.id == row.option_id and o.tenant_id == row.tenant_id for o in self.options):
            raise DecisionRefused("RECORD_INVALID")
        self.one_offs.append(row)
        return row

    def latest_one_offs(self, tenant_id: UUID, decision_id: UUID) -> Mapping[UUID, OneOffRow]:
        ids = {o.id for o in self.options if o.decision_id == decision_id}
        latest: dict[UUID, OneOffRow] = {}
        for row in sorted((r for r in self.one_offs if r.option_id in ids and r.tenant_id == tenant_id),
                          key=lambda r: (r.declared_at, r.id)):
            latest[row.option_id] = row
        return latest

    def add_run(self, run: RunRow) -> RunRow:
        ids = [o.id for o in self.options if o.decision_id == run.decision_id]  # option_evaluation_run_complete
        of = {r.id: r.option_id for r in self.one_offs if r.tenant_id == run.tenant_id}
        for e in run.evaluations:  # D-P6.30: the evaluation's option is the decision's; the one-off is its option's
            if e.option_id not in ids or (e.one_off_id is not None and of.get(e.one_off_id) != e.option_id):
                raise DecisionRefused("RECORD_INVALID")
        if sorted(e.option_id for e in run.evaluations) != sorted(ids):
            raise DecisionRefused("RECORD_INVALID")
        self.runs.append(run)
        return run

    def latest_run(self, tenant_id: UUID, decision_id: UUID) -> RunRow | None:
        runs = [r for r in self.runs if r.tenant_id == tenant_id and r.decision_id == decision_id]
        return max(runs, key=lambda r: (r.run_at, r.id), default=None)

    def agreed_action_site(self, tenant_id: UUID, action_id: UUID) -> UUID | None | Literal[False]:
        return self.actions.get((tenant_id, action_id), False)

    def add_choice(self, row: ChoiceRow) -> tuple[ChoiceRow, bool]:
        stored = self.choice(row.tenant_id, row.decision_id)
        if stored is not None:
            return stored, True
        run = next((r for r in self.runs if r.tenant_id == row.tenant_id and r.id == row.run_id), None)
        ids = {o.id for o in self.options if o.decision_id == row.decision_id}
        if run is None or run.decision_id != row.decision_id or (row.option_id is not None and row.option_id not in ids):
            raise DecisionRefused("RECORD_INVALID")  # D-P6.30
        self.choices.append(row)
        return row, False

    def choice(self, tenant_id: UUID, decision_id: UUID) -> ChoiceRow | None:
        return next((c for c in self.choices if c.tenant_id == tenant_id and c.decision_id == decision_id), None)

    def for_tenant(self, tenant_id: UUID, period_from: str | None, period_to: str | None):
        rows = [d for d in self.decisions if d.tenant_id == tenant_id
                and (period_from is None or d.period >= period_from) and (period_to is None or d.period <= period_to)]
        out = []
        for d in sorted(rows, key=lambda r: (r.prepared_at, r.id), reverse=True):
            _, options = self.decision(tenant_id, d.id)
            ref = self.site_by_id(tenant_id, d.site_id)
            site_name = self.sites[(tenant_id, ref.site_code.lower())][1]
            one_offs = self.latest_one_offs(tenant_id, d.id)
            run, choice = self.latest_run(tenant_id, d.id), self.choice(tenant_id, d.id)
            people = {d.prepared_by_person_id, *(r.declared_by_person_id for r in one_offs.values())}
            if run is not None:
                people.add(run.run_by_person_id)
            if choice is not None:
                people.add(choice.chosen_by_person_id)
            out.append(DecisionBundle(d, ref.site_code, site_name, options, one_offs, run, choice,
                                      {p: self.names[p] for p in people}))
        return tuple(out)
