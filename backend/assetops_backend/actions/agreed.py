"""3C2 (`specs/3C2-agreed-change-action/spec.md` §2.2-§2.3; D-3C2.1 to D-3C2.14): the change agreed at the end of the
deep-dive, recorded as an Action by people, with its owner and due date. Nothing values it (RC9).

Not the S6-01a Actions (`actions/service.py`, `lifecycle.py`): those are opened from Findings by the system and have
no person who agreed them; this module never reads or writes them (D-3C2.1).

Text (D-3C2.14, commit 2): the state is the code `OPEN` or `OVERDUE`, and its word ("Open", "Overdue") is rendered
from vocabulary `action_state` through statement `agreed_action.state`; a refusal is its code and exit code, and its
sentence is rendered from statement `agreed_action.refused`. This module is in the SC-1 guard's `ADOPTED` scope: it
builds no English itself.
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass, replace
from datetime import date, datetime, timezone
from types import MappingProxyType
from typing import TYPE_CHECKING, Callable, Mapping, Protocol
from uuid import UUID, uuid4

from assetops_backend.accounts.permissions import roles_of
from assetops_backend.i18n import Count, State, Word, message, render
from assetops_backend.structure.read import SITE_TYPE_TO_STRUCTURE
from assetops_backend.structure.registry import REGISTRIES

if TYPE_CHECKING:
    from assetops_backend.accounts.service import AccountService

ORIGIN = "DEEP_DIVE"
COMMAND = "action.agree"
TITLE_MIN, TITLE_MAX = 1, 200
#: D-3C2.14: the state codes; `state_words` renders them through the `action_state` vocabulary.
STATE_OPEN, STATE_OVERDUE = "OPEN", "OVERDUE"
COVER_ALL, COVER_SITE = "ALL", "SITE"
#: D-3C2.6: the owner's cover by role; a role not listed owns nothing.
OWNER_COVER: Mapping[str, str] = MappingProxyType({
    "OPERATOR_EXECUTIVE": COVER_ALL, "FINANCE_AND_COMMERCIAL_LEAD": COVER_ALL, "SITE_MANAGER": COVER_SITE})
#: D-3C2.11's Unicode categories Cc, Cf, Zl, Zp, held upper-cased (code form) and compared with the upper-cased
#: category; the thirty general category codes stay distinct when upper-cased, so the rule is unchanged.
TITLE_REFUSED_CATEGORIES = frozenset({"CC", "CF", "ZL", "ZP"})

#: §2.3 refusal codes and their exit codes (3 only for the store).
REFUSAL_EXIT: Mapping[str, int] = MappingProxyType({
    "BAD_TITLE": 2, "UNKNOWN_TENANT": 2, "PERSON_NOT_FOUND": 2, "PERSON_ROLE_REQUIRED": 2, "SITE_NOT_FOUND": 2,
    "FACTOR_NEEDS_SITE": 2, "FACTOR_UNKNOWN": 2, "FACTOR_SITE_TYPE": 2, "OWNER_NOT_FOUND": 2, "OWNER_SCOPE": 2,
    "DUE_IN_PAST": 2, "BAD_DUE": 2, "NO_DATABASE": 2, "ACTIONS_UNAVAILABLE": 3})


@dataclass(frozen=True)
class IdentityKey:
    """The fields of `agreed_action_once`, the tenant apart."""
    created_by_person_id: UUID
    owner_person_id: UUID
    title: str
    due_on: date
    site_id: UUID | None
    factor_id: str | None


@dataclass(frozen=True)
class AgreedActionRow:
    """One `agreed_action` row, as written."""
    id: UUID
    tenant_id: UUID
    title: str
    site_id: UUID | None
    factor_id: str | None
    owner_person_id: UUID
    created_by_person_id: UUID
    created_role: str
    created_by_script: bool
    created_at: datetime
    due_on: date
    origin: str

    @property
    def key(self) -> IdentityKey:
        return IdentityKey(self.created_by_person_id, self.owner_person_id, self.title, self.due_on, self.site_id,
                           self.factor_id)


@dataclass(frozen=True)
class AgreedActionView:
    """One row as a reader sees it (names joined). `state_code` is `OPEN` or `OVERDUE` at the read's clock and
    `state_words` its rendered word (5c's mapping reads it)."""
    action_id: UUID
    title: str
    site_code: str | None
    factor_id: str | None
    owner_name: str
    created_by_name: str
    created_at: datetime
    due_on: date
    state_code: str
    state_words: str


@dataclass(frozen=True)
class Recorded:
    row: AgreedActionRow
    view: AgreedActionView
    already_recorded: bool


class AgreedActionRefused(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code
        self.exit = REFUSAL_EXIT[code]


class StoreUnavailable(Exception):
    """The store could not answer (the adapter wraps its driver's errors in this); `ACTIONS_UNAVAILABLE`."""


class AgreedActionStore(Protocol):
    def site(self, tenant_id: UUID, site_code: str) -> tuple[UUID, str, str] | None: ...  # (id, site_type, code)

    def find(self, tenant_id: UUID, key: IdentityKey) -> AgreedActionRow | None: ...

    def add(self, row: AgreedActionRow) -> tuple[AgreedActionRow, bool]: ...  # (stored, already_recorded)

    def for_tenant(self, tenant_id: UUID) -> tuple[tuple[AgreedActionRow, str | None, str, str], ...]:
        """(row, site_code, owner display name, creator display name), newest first by (created_at, id)."""
        ...


def state_code(due_on: date, today: date) -> str:
    """D-3C2.4: overdue from the day after the due date, by the UTC date at the read."""
    return STATE_OVERDUE if due_on < today else STATE_OPEN


def state_words(due_on: date, today: date) -> str:
    """The state's word (D-3C2.14): `state_code` rendered through vocabulary `action_state`."""
    return render(message("agreed_action.state", state=Word("action_state", state_code(due_on, today))))


def refusal_sentence(code: str) -> str:
    """A refusal's sentence (spec §2.5, D-3C2.14), rendered from `agreed_action.refused`; the title bounds are counts."""
    return render(message("agreed_action.refused", code=State(code), least=Count(TITLE_MIN, "character"),
                          most=Count(TITLE_MAX, "character")))


def clean_title(title: str) -> str | None:
    """D-3C2.11: spaces (U+0020) stripped as `btrim` does; None (BAD_TITLE) when empty, over 200 code points, holding
    a control, format or line/paragraph separator, or starting or ending with white space. No normalisation."""
    t = title.strip(" ")
    if not t or len(t) > TITLE_MAX:
        return None
    if any(unicodedata.category(c).upper() in TITLE_REFUSED_CATEGORIES for c in t):
        return None
    if t[0].isspace() or t[-1].isspace():
        return None
    return t


def owner_covers(roles: frozenset[tuple[str, UUID | None]], site_id: UUID | None) -> bool:
    """D-3C2.6: executive and finance lead anywhere; a Site manager at their own Site only; any other role never."""
    for role, grant_site in roles:
        cover = OWNER_COVER.get(role)
        if cover == COVER_ALL:
            return True
        if cover == COVER_SITE and site_id is not None and grant_site == site_id:
            return True
    return False


def _now(clock: Callable[[], datetime]) -> datetime:
    """D-3C2.10: one clock read per call, in whole UTC seconds. A naive datetime is a programming error."""
    value = clock()
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("the clock must return an aware datetime")
    return value.astimezone(timezone.utc).replace(microsecond=0)


def _view(row: AgreedActionRow, site_code: str | None, owner_name: str, creator_name: str,
          today: date) -> AgreedActionView:
    return AgreedActionView(row.id, row.title, site_code, row.factor_id, owner_name, creator_name, row.created_at,
                            row.due_on, state_code(row.due_on, today), state_words(row.due_on, today))


def _factor_known(factor_id: str) -> bool:
    return any(row.factor_id == factor_id for registry in REGISTRIES.values() for row in registry.rows)


class AgreedActionService:
    def __init__(self, store: AgreedActionStore, accounts: AccountService, *, clock: Callable[[], datetime],
                 new_id: Callable[[], UUID] = uuid4) -> None:
        self._store = store
        self._accounts = accounts
        self._clock = clock
        self._new_id = new_id

    def record(self, *, tenant_slug: str, as_email: str, title: str, owner_email: str, due_on: date,
               site_code: str | None, factor_id: str | None) -> Recorded:
        """§2.3, checked in this order; the first rule that fails refuses."""
        now = _now(self._clock)
        today = now.date()
        # 1. The title.
        t = clean_title(title)
        if t is None:
            raise AgreedActionRefused("BAD_TITLE")
        # 2. The tenant.
        tenant_id = self._accounts.tenant_by_slug(tenant_slug)
        if tenant_id is None:
            raise AgreedActionRefused("UNKNOWN_TENANT")
        # 3. The creator and the role that admits them.
        creator = self._accounts.onboard_person(as_email)
        if creator is None or creator.tenant_slug != tenant_slug or not creator.active:
            raise AgreedActionRefused("PERSON_NOT_FOUND")
        held = {role for role, _ in creator.roles}
        created_role = next((role for role in roles_of(COMMAND) if role in held), None)
        if created_role is None:
            raise AgreedActionRefused("PERSON_ROLE_REQUIRED")
        # 4. The Site.
        site_id: UUID | None = None
        site_type: str | None = None
        stored_code: str | None = None
        if site_code is not None:
            try:
                found = self._store.site(tenant_id, site_code)
            except StoreUnavailable:
                raise AgreedActionRefused("ACTIONS_UNAVAILABLE") from None
            if found is None:
                raise AgreedActionRefused("SITE_NOT_FOUND")
            site_id, site_type, stored_code = found
        # 5. The factor (D-3C2.8).
        if factor_id is not None:
            if site_id is None:
                raise AgreedActionRefused("FACTOR_NEEDS_SITE")
            if not _factor_known(factor_id):
                raise AgreedActionRefused("FACTOR_UNKNOWN")
            registry = REGISTRIES.get(SITE_TYPE_TO_STRUCTURE.get(site_type or "", ""))
            if registry is None or not any(row.factor_id == factor_id for row in registry.rows):
                raise AgreedActionRefused("FACTOR_SITE_TYPE")
        # 6. The owner (D-3C2.6); the owner may be the creator.
        owner = self._accounts.onboard_person(owner_email)
        if owner is None or owner.tenant_id != tenant_id or not owner.active:
            raise AgreedActionRefused("OWNER_NOT_FOUND")
        if not owner_covers(owner.roles, site_id):
            raise AgreedActionRefused("OWNER_SCOPE")
        # 7. The re-run (D-3C2.7), before the due check.
        key = IdentityKey(creator.person_id, owner.person_id, t, due_on, site_id, factor_id)
        try:
            stored = self._store.find(tenant_id, key)
        except StoreUnavailable:
            raise AgreedActionRefused("ACTIONS_UNAVAILABLE") from None
        if stored is not None:
            return Recorded(stored, _view(stored, stored_code, owner.display_name, creator.display_name, today), True)
        # 8. The due date.
        if due_on < today:
            raise AgreedActionRefused("DUE_IN_PAST")
        # 9. The write.
        row = AgreedActionRow(self._new_id(), tenant_id, t, site_id, factor_id, owner.person_id, creator.person_id,
                              created_role, True, now, due_on, ORIGIN)
        try:
            written, already = self._store.add(row)
        except StoreUnavailable:
            raise AgreedActionRefused("ACTIONS_UNAVAILABLE") from None
        return Recorded(written, _view(written, stored_code, owner.display_name, creator.display_name, today), already)

    def for_tenant(self, tenant_id: UUID) -> tuple[AgreedActionView, ...]:
        """Every agreed Action of the tenant, newest first by (created_at, id); one clock read."""
        today = _now(self._clock).date()
        return tuple(_view(row, code, owner, creator, today)
                     for row, code, owner, creator in self._store.for_tenant(tenant_id))


class MemoryAgreedActionStore:
    """An `AgreedActionStore` in memory, for the unit tests: the Postgres identity rule and newest-first order."""

    def __init__(self) -> None:
        self.sites: dict[tuple[UUID, str], tuple[UUID, str, str]] = {}
        self.names: dict[UUID, str] = {}
        self.rows: list[AgreedActionRow] = []

    def add_site(self, tenant_id: UUID, code: str, site_type: str, site_id: UUID | None = None) -> UUID:
        sid = site_id or uuid4()
        self.sites[(tenant_id, code.lower())] = (sid, site_type, code)
        return sid

    def add_person(self, person_id: UUID, display_name: str) -> None:
        self.names[person_id] = display_name

    def site(self, tenant_id: UUID, site_code: str) -> tuple[UUID, str, str] | None:
        return self.sites.get((tenant_id, site_code.lower()))

    def find(self, tenant_id: UUID, key: IdentityKey) -> AgreedActionRow | None:
        return next((r for r in self.rows if r.tenant_id == tenant_id and r.key == key), None)

    def add(self, row: AgreedActionRow) -> tuple[AgreedActionRow, bool]:
        stored = self.find(row.tenant_id, row.key)
        if stored is not None:
            return stored, True
        self.rows.append(replace(row))
        return row, False

    def _code(self, tenant_id: UUID, site_id: UUID | None) -> str | None:
        return next((code for (t, _), (sid, _, code) in self.sites.items() if t == tenant_id and sid == site_id), None)

    def for_tenant(self, tenant_id: UUID) -> tuple[tuple[AgreedActionRow, str | None, str, str], ...]:
        rows = sorted((r for r in self.rows if r.tenant_id == tenant_id), key=lambda r: (r.created_at, r.id),
                      reverse=True)
        return tuple((r, self._code(tenant_id, r.site_id), self.names[r.owner_person_id],
                      self.names[r.created_by_person_id]) for r in rows)
