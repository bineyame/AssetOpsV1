"""3C0a (spec §3, §4, §9; rulings D-3C0A.5/.6/.11, R4-R8, MB1, MB2): the account service over an in-memory store.

The in-memory `AccountStore` below re-implements every store refusal (ROLE_ALREADY_HELD, GRANT_ALREADY_REMOVED,
LAST_EXECUTIVE, EMAIL_TAKEN, EXECUTIVE_EXISTS) and serialises `guarded_attempt` with a `threading.Lock` per key, so
the service's rules are tested without a database. The API test reuses it.
"""
from __future__ import annotations

import hashlib
import threading
from collections import defaultdict
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from typing import Callable
from uuid import UUID, uuid4

import pytest

from assetops_backend.accounts import passwords
from assetops_backend.accounts.model import (ROLES, Account, AccountRefused, GrantRow, PersonView, SessionRow)
from assetops_backend.accounts.service import AccountService
from assetops_backend.accounts.store import Attempt, StoreConflict

PW = "correct horse battery"
NEW_PW = "a newer passphrase"
EXEC = "OPERATOR_EXECUTIVE"
T0 = datetime(2026, 11, 20, 8, 0, tzinfo=timezone.utc)


class Clock:
    def __init__(self, now: datetime = T0) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now

    def advance(self, **delta: float) -> None:
        self.now = self.now + timedelta(**delta)


@dataclass
class _AttemptRow:
    id: UUID
    email_key_sha256: str
    at: datetime
    succeeded: bool
    person_id: UUID | None


class MemoryStore:
    """An `AccountStore` in memory. Current state is derived from rows, as in Postgres."""

    def __init__(self) -> None:
        self.tenants: dict[UUID, tuple[str, str]] = {}
        self.sites: dict[tuple[UUID, str], tuple[UUID, str]] = {}
        self.accounts: dict[UUID, Account] = {}
        self.credentials: list[tuple[UUID, str, datetime, UUID]] = []
        self.statuses: list[tuple[UUID, str, str | None, datetime, UUID]] = []
        self.grants: list[GrantRow] = []
        self.sessions: dict[str, SessionRow] = {}
        self.attempts: list[_AttemptRow] = []
        self._tenant_lock = threading.Lock()
        self._key_locks: dict[str, threading.Lock] = defaultdict(threading.Lock)

    # --- test helpers -------------------------------------------------------------------------------------------
    def add_tenant(self, slug: str, name: str) -> UUID:
        tid = uuid4()
        self.tenants[tid] = (slug, name)
        return tid

    def add_site(self, tenant_id: UUID, code: str) -> UUID:
        sid = uuid4()
        self.sites[(tenant_id, code.lower())] = (sid, code)
        return sid

    def add_bare_account(self, tenant_id: UUID, email: str, name: str, at: datetime) -> UUID:
        """An account with an ACTIVE status and no credential (spec §3: refused like a wrong password)."""
        pid = uuid4()
        self.accounts[pid] = Account(pid, tenant_id, email, name)
        self.statuses.append((pid, "ACTIVE", None, at, uuid4()))
        return pid

    # --- the port -----------------------------------------------------------------------------------------------
    def tenant_by_slug(self, slug: str) -> tuple[UUID, str] | None:
        return next(((tid, name) for tid, (s, name) in self.tenants.items() if s == slug), None)

    def tenant(self, tenant_id: UUID) -> tuple[str, str] | None:
        return self.tenants.get(tenant_id)

    def tenant_slug(self, tenant_id: UUID) -> str | None:
        found = self.tenants.get(tenant_id)
        return None if found is None else found[0]

    def site_id(self, tenant_id: UUID, site_code: str) -> UUID | None:
        found = self.sites.get((tenant_id, site_code.lower()))
        return None if found is None else found[0]

    def _site_code(self, site_id: UUID | None) -> str | None:
        return next((code for (sid, code) in self.sites.values() if sid == site_id), None)

    def account_by_email_key(self, key: str) -> Account | None:
        return next((a for a in self.accounts.values() if a.email.lower() == key), None)

    def account(self, tenant_id: UUID, person_id: UUID) -> Account | None:
        found = self.accounts.get(person_id)
        return found if found is not None and found.tenant_id == tenant_id else None

    def current_credential(self, person_id: UUID) -> tuple[str, datetime] | None:
        rows = sorted((c for c in self.credentials if c[0] == person_id), key=lambda c: (c[2], c[3]))
        return None if not rows else (rows[-1][1], rows[-1][2])

    def current_status(self, person_id: UUID) -> str | None:
        rows = sorted((s for s in self.statuses if s[0] == person_id), key=lambda s: (s[3], s[4]))
        return None if not rows else rows[-1][1]

    def _held(self, tenant_id: UUID) -> list[GrantRow]:
        removed = {g.grant_id for g in self.grants if g.action == "REMOVED"}
        return [g for g in self.grants if g.tenant_id == tenant_id and g.action == "GRANTED" and g.row_id not in removed]

    def held_grants(self, tenant_id: UUID, person_id: UUID) -> tuple[GrantRow, ...]:
        return tuple(g for g in self._held(tenant_id) if g.person_id == person_id)

    def _active_executives(self, tenant_id: UUID) -> set[UUID]:
        return {g.person_id for g in self._held(tenant_id)
                if g.role == EXEC and self.current_status(g.person_id) == "ACTIVE"}

    def guarded_attempt(self, key_sha256: str, now: datetime,
                        verify: Callable[[], tuple[bool, UUID | None]]) -> Attempt:
        with self._key_locks[key_sha256]:
            mine = [a for a in self.attempts if a.email_key_sha256 == key_sha256]
            last_success = max((a.at for a in mine if a.succeeded), default=None)
            since = now - timedelta(minutes=15)
            if last_success is not None and last_success > since:
                since = last_success
            failures = sorted((a for a in mine if not a.succeeded and a.at > since),
                              key=lambda a: (a.at, a.id), reverse=True)[:5]
            if len(failures) >= 5:
                return Attempt(locked=True, retry_at=failures[-1].at + timedelta(minutes=15))
            succeeded, person_id = verify()
            self.attempts.append(_AttemptRow(uuid4(), key_sha256, now, succeeded, person_id if succeeded else None))
            before = now - timedelta(days=30)
            self.attempts = [a for a in self.attempts if not a.at < before]
            return Attempt(locked=False, succeeded=succeeded, person_id=person_id if succeeded else None)

    def grant_row(self, tenant_id: UUID, grant_id: UUID) -> GrantRow | None:
        return next((g for g in self.grants if g.tenant_id == tenant_id and g.row_id == grant_id), None)

    def add_session(self, id: UUID, tenant_id: UUID, person_id: UUID, token_sha256: str, created_at: datetime,
                    expires_at: datetime) -> None:
        assert token_sha256 not in self.sessions
        self.sessions[token_sha256] = SessionRow(id, tenant_id, person_id, created_at, expires_at, None)

    def session(self, token_sha256: str) -> SessionRow | None:
        return self.sessions.get(token_sha256)

    def revoke(self, token_sha256: str, at: datetime) -> None:
        found = self.sessions.get(token_sha256)
        if found is not None and found.revoked_at is None:
            self.sessions[token_sha256] = replace(found, revoked_at=at)

    def people(self, tenant_id: UUID) -> tuple[PersonView, ...]:
        views = [PersonView(a.id, a.display_name, a.email, self.current_status(a.id) or "ACTIVE",
                            self.held_grants(tenant_id, a.id))
                 for a in self.accounts.values() if a.tenant_id == tenant_id]
        return tuple(sorted(views, key=lambda v: (v.display_name.casefold(), v.email.lower())))

    def grant_rows(self, tenant_id: UUID) -> tuple[GrantRow, ...]:
        return tuple(sorted((g for g in self.grants if g.tenant_id == tenant_id),
                            key=lambda g: (g.at, str(g.row_id)), reverse=True))

    def _require_executive(self, tenant_id: UUID, actor_person_id: UUID) -> None:
        if actor_person_id not in self._active_executives(tenant_id):
            raise StoreConflict("ROLE_REQUIRED")

    def add_grant(self, row: GrantRow, actor_person_id: UUID) -> GrantRow:
        with self._tenant_lock:
            self._require_executive(row.tenant_id, actor_person_id)
            if any(g.person_id == row.person_id and g.role == row.role and g.site_id == row.site_id
                   for g in self._held(row.tenant_id)):
                raise StoreConflict("ROLE_ALREADY_HELD")
            row = replace(row, site_code=self._site_code(row.site_id))
            self.grants.append(row)
            return row

    def add_removal(self, row: GrantRow, actor_person_id: UUID) -> GrantRow:
        with self._tenant_lock:
            self._require_executive(row.tenant_id, actor_person_id)
            if any(g.action == "REMOVED" and g.grant_id == row.grant_id for g in self.grants):
                raise StoreConflict("GRANT_ALREADY_REMOVED")
            if row.role == EXEC and not (self._active_executives(row.tenant_id) - {row.person_id}):
                raise StoreConflict("LAST_EXECUTIVE")
            self.grants.append(row)
            return row

    def create_account(self, account: Account, password_hash: str, created_at: datetime, by: str,
                       executive_grant: GrantRow | None) -> None:
        with self._tenant_lock:
            if self.account_by_email_key(account.email.lower()) is not None:
                raise StoreConflict("EMAIL_TAKEN")
            if executive_grant is not None and self._active_executives(account.tenant_id):
                raise StoreConflict("EXECUTIVE_EXISTS")
            self.accounts[account.id] = account
            self.credentials.append((account.id, password_hash, created_at, uuid4()))
            self.statuses.append((account.id, "ACTIVE", None, created_at, uuid4()))
            if executive_grant is not None:
                self.grants.append(executive_grant)

    def set_credential(self, tenant_id: UUID, person_id: UUID, password_hash: str, at: datetime, by: str) -> None:
        self.credentials.append((person_id, password_hash, at, uuid4()))

    def set_status(self, tenant_id: UUID, person_id: UUID, status: str, reason: str | None, at: datetime,
                   by: str) -> None:
        with self._tenant_lock:
            if status == "DISABLED" and person_id in self._active_executives(tenant_id) \
                    and not (self._active_executives(tenant_id) - {person_id}):
                raise StoreConflict("LAST_EXECUTIVE")
            self.statuses.append((person_id, status, reason, at, uuid4()))


# --- fixtures ---------------------------------------------------------------------------------------------------

@dataclass
class World:
    store: MemoryStore
    clock: Clock
    svc: AccountService
    tenant: UUID
    other: UUID
    site: UUID
    other_site: UUID
    exec_id: UUID


@pytest.fixture()
def world() -> World:
    store, clock = MemoryStore(), Clock()
    svc = AccountService(store, clock=clock)
    tenant = store.add_tenant("acme", "Acme Power")
    other = store.add_tenant("beta", "Beta Cold")
    site = store.add_site(tenant, "KOBO-001")
    other_site = store.add_site(other, "BETA-001")
    exec_id = svc.onboard_create("acme", "amina@acme.example", "Amina", PW, executive=True)
    clock.advance(seconds=1)
    return World(store, clock, svc, tenant, other, site, other_site, exec_id)


def _person(w: World, email: str, name: str, tenant: str = "acme") -> UUID:
    pid = w.svc.onboard_create(tenant, email, name, PW, executive=False)
    w.clock.advance(seconds=1)
    return pid


def _principal(w: World, email: str, pw: str = PW):
    signed = w.svc.sign_in(email, pw)
    w.clock.advance(seconds=1)
    return w.svc.resolve(signed.token)


def _key_sha(email: str) -> str:
    return hashlib.sha256(email.strip().lower().encode("ascii")).hexdigest()


def _refused(call, code: str, status: int) -> AccountRefused:
    with pytest.raises(AccountRefused) as refused:
        call()
    assert (refused.value.code, refused.value.status) == (code, status), (refused.value.code, refused.value.status)
    return refused.value


# --- sign-in ----------------------------------------------------------------------------------------------------

def test_sign_in_writes_one_succeeded_attempt_and_a_session(world: World) -> None:
    w = world
    signed = w.svc.sign_in("  Amina@ACME.example ", PW)
    assert signed.principal.person_id == w.exec_id and signed.principal.has_role(EXEC)
    assert signed.expires_at == w.clock.now + timedelta(hours=12)
    assert signed.principal.session_expires_at == signed.expires_at
    [attempt] = w.store.attempts
    assert (attempt.succeeded, attempt.person_id, attempt.email_key_sha256) == (
        True, w.exec_id, _key_sha("amina@acme.example"))
    [session] = w.store.sessions.values()
    assert session.person_id == w.exec_id and session.expires_at - session.created_at == timedelta(hours=12)
    # Only the token's SHA-256 is stored, never the token.
    assert list(w.store.sessions) == [hashlib.sha256(signed.token.encode("ascii")).hexdigest()]
    assert signed.token not in repr(w.store.__dict__)


@pytest.fixture()
def spy(monkeypatch):
    calls: list[str] = []
    real = passwords.verify_password

    def counting(password: str, stored: str) -> bool:
        calls.append(stored)
        return real(password, stored)

    monkeypatch.setattr(passwords, "verify_password", counting)
    return calls


def _setup_path(w: World, path: str) -> tuple[str, str, str | None]:
    """(email, password, the stored hash verification must use; None means DUMMY_HASH)."""
    if path == "wrong password":
        return "amina@acme.example", PW + "!", w.store.current_credential(w.exec_id)[0]
    if path == "unknown email":
        return "nobody@acme.example", PW, None
    if path == "disabled":
        pid = _person(w, "joseph@acme.example", "Joseph")
        w.svc.onboard_set_status("joseph@acme.example", "DISABLED", "left")
        return "joseph@acme.example", PW, w.store.current_credential(pid)[0]
    if path == "no credential":
        w.store.add_bare_account(w.tenant, "peter@acme.example", "Peter", w.clock.now)
        return "peter@acme.example", PW, None
    if path == "malformed email":
        return "not an email", PW, None
    if path == "129-character password":
        return "amina@acme.example", PW + "x" * (129 - len(PW)), w.store.current_credential(w.exec_id)[0]
    raise AssertionError(path)


PATHS = ("wrong password", "unknown email", "disabled", "no credential", "malformed email", "129-character password")


@pytest.mark.parametrize("path", PATHS)
def test_every_refused_path_is_one_refusal_after_exactly_one_verification(world: World, spy, path: str) -> None:
    w = world
    email, pw, stored = _setup_path(w, path)
    before = len(w.store.attempts)
    spy.clear()
    refused = _refused(lambda: w.svc.sign_in(email, pw), "SIGN_IN_REFUSED", 401)
    assert refused.params == {}
    assert spy == [stored if stored is not None else passwords.DUMMY_HASH]
    new = w.store.attempts[before:]
    if path == "malformed email":
        assert new == []  # D-3C0A.11: it can match no account, so no row
    else:
        assert [(a.succeeded, a.person_id) for a in new] == [(False, None)]
        assert new[0].email_key_sha256 == _key_sha(email)


def test_the_129_character_password_reaches_scrypt_cut_to_128(world: World, monkeypatch) -> None:
    seen: list[str] = []
    real = passwords.verify_password
    monkeypatch.setattr(passwords, "verify_password", lambda pw, stored: seen.append(pw) or real(pw, stored))
    # The first 128 characters are the right password padded, so only the length refuses it.
    long = PW + "y" * (129 - len(PW))
    world.svc.onboard_set_password("amina@acme.example", long[:128])
    _refused(lambda: world.svc.sign_in("amina@acme.example", long), "SIGN_IN_REFUSED", 401)
    assert [len(pw) for pw in seen] == [128]


def test_the_sixth_attempt_locks_writes_nothing_and_unlocks_after_the_window(world: World) -> None:
    w = world
    for _ in range(5):
        _refused(lambda: w.svc.sign_in("amina@acme.example", "wrong password!"), "SIGN_IN_REFUSED", 401)
        w.clock.advance(minutes=1)
    w.clock.advance(seconds=-30)  # the 5th failure was at 4 min; now 4.5 min after the 1st
    count = len(w.store.attempts)
    locked = _refused(lambda: w.svc.sign_in("amina@acme.example", PW), "SIGN_IN_LOCKED", 429)
    assert locked.params == {"minutes": 11}  # ceil(15 - 4.5)
    assert len(w.store.attempts) == count
    w.clock.now = w.store.attempts[-5].at + timedelta(minutes=14, seconds=59)
    assert _refused(lambda: w.svc.sign_in("amina@acme.example", PW), "SIGN_IN_LOCKED", 429).params == {"minutes": 1}
    w.clock.now = w.store.attempts[-5].at + timedelta(minutes=15)
    assert w.svc.sign_in("amina@acme.example", PW).principal.person_id == w.exec_id


def test_a_success_resets_the_count(world: World) -> None:
    w = world
    for _ in range(4):
        _refused(lambda: w.svc.sign_in("amina@acme.example", "wrong password!"), "SIGN_IN_REFUSED", 401)
        w.clock.advance(seconds=10)
    w.svc.sign_in("amina@acme.example", PW)
    w.clock.advance(seconds=10)
    _refused(lambda: w.svc.sign_in("amina@acme.example", "wrong password!"), "SIGN_IN_REFUSED", 401)
    w.clock.advance(seconds=10)
    _refused(lambda: w.svc.sign_in("amina@acme.example", "wrong password!"), "SIGN_IN_REFUSED", 401)


def test_an_unknown_email_locks_like_a_known_one_and_keys_are_hashes(world: World) -> None:
    w = world
    for _ in range(5):
        _refused(lambda: w.svc.sign_in("Ghost@Nowhere.example", PW), "SIGN_IN_REFUSED", 401)
        w.clock.advance(seconds=5)
    _refused(lambda: w.svc.sign_in("ghost@nowhere.example", PW), "SIGN_IN_LOCKED", 429)
    assert {a.email_key_sha256 for a in w.store.attempts} == {_key_sha("ghost@nowhere.example")}
    assert "ghost" not in repr(w.store.attempts).lower()


def test_attempts_older_than_30_days_are_purged_on_insert(world: World) -> None:
    w = world
    _refused(lambda: w.svc.sign_in("ghost@nowhere.example", PW), "SIGN_IN_REFUSED", 401)
    w.clock.advance(days=30, seconds=1)
    w.svc.sign_in("amina@acme.example", PW)
    assert [a.succeeded for a in w.store.attempts] == [True]


# --- sessions ---------------------------------------------------------------------------------------------------

def test_resolve_ends_at_12_hours_absolute(world: World) -> None:
    w = world
    signed = w.svc.sign_in("amina@acme.example", PW)
    w.clock.advance(hours=12, seconds=-1)
    principal = w.svc.resolve(signed.token)
    assert principal is not None and principal.session_expires_at == signed.expires_at
    assert principal.at == w.clock.now
    w.clock.advance(seconds=1)
    assert w.svc.resolve(signed.token) is None


def test_resolve_none_for_no_unknown_or_signed_out_token(world: World) -> None:
    w = world
    assert w.svc.resolve(None) is None and w.svc.resolve("") is None and w.svc.resolve("unknown") is None
    signed = w.svc.sign_in("amina@acme.example", PW)
    w.svc.sign_out(signed.token)
    assert w.svc.resolve(signed.token) is None
    w.svc.sign_out(signed.token)  # idempotent
    w.svc.sign_out(None)
    w.svc.sign_out("unknown")


def test_resolve_none_for_a_disabled_account(world: World) -> None:
    w = world
    _person(w, "joseph@acme.example", "Joseph")
    signed = w.svc.sign_in("joseph@acme.example", PW)
    w.clock.advance(seconds=1)
    w.svc.onboard_set_status("joseph@acme.example", "DISABLED", "left")
    assert w.svc.resolve(signed.token) is None
    w.clock.advance(seconds=1)  # state is the latest row by time
    w.svc.onboard_set_status("joseph@acme.example", "ACTIVE", None)
    assert w.svc.resolve(signed.token) is not None


def test_resolve_none_after_a_later_password(world: World) -> None:
    """R8 / MB1: a new password ends older sessions; a session created at set_at stays valid."""
    w = world
    signed = w.svc.sign_in("amina@acme.example", PW)
    w.clock.advance(seconds=1)
    w.svc.onboard_set_password("amina@acme.example", NEW_PW)
    assert w.svc.resolve(signed.token) is None
    fresh = w.svc.sign_in("amina@acme.example", NEW_PW)  # same clock instant as set_at
    assert w.svc.resolve(fresh.token) is not None


def test_roles_are_read_at_each_resolve(world: World) -> None:
    w = world
    pid = _person(w, "joseph@acme.example", "Joseph")
    executive = _principal(w, "amina@acme.example")
    signed = w.svc.sign_in("joseph@acme.example", PW)
    assert w.svc.resolve(signed.token).roles == frozenset()
    row = w.svc.grant(executive, pid, "SITE_MANAGER", "kobo-001")
    w.clock.advance(seconds=1)
    joseph = w.svc.resolve(signed.token)
    assert joseph.roles == frozenset({("SITE_MANAGER", w.site)})
    assert joseph.has_role("SITE_MANAGER", w.site) and not joseph.has_role("SITE_MANAGER")
    assert not joseph.has_role("SITE_MANAGER", w.other_site)
    w.svc.remove(executive, row.grant_id)
    assert w.svc.resolve(signed.token).roles == frozenset()


# --- grants and removals ----------------------------------------------------------------------------------------

def test_grant_refusals_in_order(world: World) -> None:
    w = world
    pid = _person(w, "joseph@acme.example", "Joseph")
    outsider = _person(w, "omar@beta.example", "Omar", tenant="beta")
    executive = _principal(w, "amina@acme.example")
    joseph = _principal(w, "joseph@acme.example")
    # ROLE_REQUIRED comes first, even for an unknown role and an unknown person.
    _refused(lambda: w.svc.grant(joseph, "not-a-uuid", "WIZARD", "X"), "ROLE_REQUIRED", 403)
    _refused(lambda: w.svc.grant(executive, "not-a-uuid", "WIZARD", "X"), "ROLE_UNKNOWN", 422)
    _refused(lambda: w.svc.grant(executive, "not-a-uuid", "SITE_MANAGER", None), "ROLE_SITE_RULE", 422)
    _refused(lambda: w.svc.grant(executive, "not-a-uuid", "ANALYST", "KOBO-001"), "ROLE_SITE_RULE", 422)
    _refused(lambda: w.svc.grant(executive, "not-a-uuid", "ANALYST", None), "PERSON_NOT_FOUND", 404)
    _refused(lambda: w.svc.grant(executive, uuid4(), "ANALYST", None), "PERSON_NOT_FOUND", 404)
    _refused(lambda: w.svc.grant(executive, outsider, "ANALYST", None), "PERSON_NOT_FOUND", 404)
    _refused(lambda: w.svc.grant(executive, pid, "SITE_MANAGER", "BETA-001"), "SITE_NOT_FOUND", 404)
    _refused(lambda: w.svc.grant(executive, pid, "SITE_MANAGER", "NOPE-001"), "SITE_NOT_FOUND", 404)
    first = w.svc.grant(executive, str(pid), "ANALYST", None)
    assert (first.role, first.site_id, first.action, first.by_person_id, first.by_service) == (
        "ANALYST", None, "GRANTED", w.exec_id, None)
    assert (first.display_name, first.by_display_name, first.grant_id) == ("Joseph", "Amina", first.row_id)
    held = _refused(lambda: w.svc.grant(executive, pid, "ANALYST", None), "ROLE_ALREADY_HELD", 409)
    assert held.params == {"name": "Joseph"}
    assert len([g for g in w.store.grants if g.person_id == pid]) == 1
    assert not any(g.person_id == outsider for g in w.store.grants)


def test_removal_refusals_in_order(world: World) -> None:
    w = world
    pid = _person(w, "joseph@acme.example", "Joseph")
    outsider_exec = w.svc.onboard_create("beta", "omar@beta.example", "Omar", PW, executive=True)
    executive = _principal(w, "amina@acme.example")
    joseph = _principal(w, "joseph@acme.example")
    omar = _principal(w, "omar@beta.example")
    granted = w.svc.grant(executive, pid, "ANALYST", None)
    w.clock.advance(seconds=1)
    beta_grant = w.store.held_grants(w.other, outsider_exec)[0]
    _refused(lambda: w.svc.remove(joseph, "not-a-uuid"), "ROLE_REQUIRED", 403)
    _refused(lambda: w.svc.remove(executive, "not-a-uuid"), "GRANT_NOT_FOUND", 404)
    _refused(lambda: w.svc.remove(executive, uuid4()), "GRANT_NOT_FOUND", 404)
    _refused(lambda: w.svc.remove(executive, beta_grant.row_id), "GRANT_NOT_FOUND", 404)
    _refused(lambda: w.svc.remove(omar, granted.row_id), "GRANT_NOT_FOUND", 404)
    removal = w.svc.remove(executive, str(granted.row_id))
    assert (removal.action, removal.grant_id, removal.person_id, removal.role) == (
        "REMOVED", granted.row_id, pid, "ANALYST")
    w.clock.advance(seconds=1)
    _refused(lambda: w.svc.remove(executive, removal.row_id), "GRANT_NOT_FOUND", 404)  # a REMOVED row's id
    _refused(lambda: w.svc.remove(executive, granted.row_id), "GRANT_ALREADY_REMOVED", 409)
    own = w.store.held_grants(w.tenant, w.exec_id)[0]
    _refused(lambda: w.svc.remove(executive, own.row_id), "LAST_EXECUTIVE", 409)


def test_an_executive_removes_their_own_role_when_another_exists(world: World) -> None:
    w = world
    pid = _person(w, "joseph@acme.example", "Joseph")
    executive = _principal(w, "amina@acme.example")
    w.svc.grant(executive, pid, EXEC, None)
    w.clock.advance(seconds=1)
    own = w.store.held_grants(w.tenant, w.exec_id)[0]
    w.svc.remove(executive, own.row_id)
    assert w.store._active_executives(w.tenant) == {pid}


def test_an_executive_grant_on_a_disabled_account_does_not_count(world: World) -> None:
    w = world
    pid = _person(w, "joseph@acme.example", "Joseph")
    w.svc.onboard_set_status("joseph@acme.example", "DISABLED", "on leave")
    executive = _principal(w, "amina@acme.example")
    granted = w.svc.grant(executive, pid, EXEC, None)  # P13: a grant to a DISABLED account is allowed
    assert granted.action == "GRANTED"
    w.clock.advance(seconds=1)
    own = w.store.held_grants(w.tenant, w.exec_id)[0]
    _refused(lambda: w.svc.remove(executive, own.row_id), "LAST_EXECUTIVE", 409)


def test_disabling_the_last_active_executive_is_refused(world: World) -> None:
    w = world
    _refused(lambda: w.svc.onboard_set_status("amina@acme.example", "DISABLED", "left"), "LAST_EXECUTIVE", 409)
    assert w.store.current_status(w.exec_id) == "ACTIVE"


def test_the_record_is_newest_first_and_state_is_derived(world: World) -> None:
    w = world
    pid = _person(w, "joseph@acme.example", "Joseph")
    executive = _principal(w, "amina@acme.example")
    first = w.svc.grant(executive, pid, "ANALYST", None)
    w.clock.advance(seconds=1)
    removal = w.svc.remove(executive, first.row_id)
    w.clock.advance(seconds=1)
    again = w.svc.grant(executive, pid, "ANALYST", None)
    record = w.svc.grant_record(executive)
    assert [r.row_id for r in record][:3] == [again.row_id, removal.row_id, first.row_id]
    assert record[-1].by_service == "service:onboarding" and record[-1].role == EXEC
    assert [r.at for r in record] == sorted((r.at for r in record), reverse=True)
    joseph = _principal(w, "joseph@acme.example")
    assert joseph.roles == frozenset({("ANALYST", None)})
    people = w.svc.people(joseph)  # any signed-in person reads Organisation
    assert [p.display_name for p in people] == ["Amina", "Joseph"]
    assert [g.row_id for g in people[1].grants] == [again.row_id]


# --- onboarding -------------------------------------------------------------------------------------------------

def test_onboarding_refusals(world: World) -> None:
    w = world
    _refused(lambda: w.svc.onboard_create("nope", "x@acme.example", "X", PW, executive=False), "TENANT_NOT_FOUND", 404)
    _refused(lambda: w.svc.onboard_create("acme", "bad", "X", PW, executive=False), "BAD_EMAIL", 422)
    _refused(lambda: w.svc.onboard_create("beta", "AMINA@acme.example", "X", "short", executive=False),
             "EMAIL_TAKEN", 409)  # across tenants, and before the password policy
    _refused(lambda: w.svc.onboard_create("acme", "x@acme.example", "X", "short", executive=False),
             "PASSWORD_POLICY", 422)
    _refused(lambda: w.svc.onboard_create("acme", "x@acme.example", "X", PW, executive=True), "EXECUTIVE_EXISTS", 409)
    _refused(lambda: w.svc.onboard_set_password("nobody@acme.example", NEW_PW), "PERSON_NOT_FOUND", 404)
    _refused(lambda: w.svc.onboard_set_password("amina@acme.example", " " * 20), "PASSWORD_POLICY", 422)
    _refused(lambda: w.svc.onboard_set_status("nobody@acme.example", "DISABLED", "x"), "PERSON_NOT_FOUND", 404)
    assert len(w.store.accounts) == 1


def test_onboarding_records_the_service_and_creates_no_other_role(world: World) -> None:
    w = world
    pid = _person(w, "joseph@acme.example", "Joseph")
    assert w.store.held_grants(w.tenant, pid) == ()
    [grant] = w.store.held_grants(w.tenant, w.exec_id)
    assert (grant.by_service, grant.by_person_id, grant.role, grant.site_id) == (
        "service:onboarding", None, EXEC, None)
    assert ROLES[0] == EXEC


# --- RV1-L2: names and reasons ---------------------------------------------------------------------------------

@pytest.mark.parametrize("name", ["", "   ", "x" * 121])
def test_a_bad_name_is_refused_bad_name_422(world: World, name: str) -> None:
    w = world
    _refused(lambda: w.svc.onboard_create("acme", "x@acme.example", name, PW, executive=False), "BAD_NAME", 422)
    assert len(w.store.accounts) == 1


def test_a_padded_name_is_trimmed(world: World) -> None:
    w = world
    pid = w.svc.onboard_create("acme", "x@acme.example", "  Padded Name \n", PW, executive=False)
    assert w.store.accounts[pid].display_name == "Padded Name"
    pid = w.svc.onboard_create("acme", "y@acme.example", "n" * 120, PW, executive=False)
    assert w.store.accounts[pid].display_name == "n" * 120


@pytest.mark.parametrize("reason", ["", "  ", "r" * 501])
def test_a_bad_reason_is_refused_bad_reason_422(world: World, reason: str) -> None:
    w = world
    _person(w, "joseph@acme.example", "Joseph")
    before = len(w.store.statuses)
    _refused(lambda: w.svc.onboard_set_status("joseph@acme.example", "DISABLED", reason), "BAD_REASON", 422)
    assert len(w.store.statuses) == before


def test_a_padded_reason_is_trimmed(world: World) -> None:
    w = world
    _person(w, "joseph@acme.example", "Joseph")
    w.svc.onboard_set_status("joseph@acme.example", "DISABLED", "  left  ")
    assert w.store.statuses[-1][2] == "left"


# --- RV1-L3: a lone surrogate ----------------------------------------------------------------------------------

SURROGATE_PW = "\ud800" + "a" * 14


@pytest.mark.parametrize("known", [True, False])
def test_a_lone_surrogate_sign_in_is_the_one_401_after_one_verification(world: World, spy, known: bool) -> None:
    w = world
    email = "amina@acme.example" if known else "nobody@acme.example"
    spy.clear()
    refused = _refused(lambda: w.svc.sign_in(email, SURROGATE_PW), "SIGN_IN_REFUSED", 401)
    assert refused.params == {}
    assert len(spy) == 1


def test_a_lone_surrogate_password_fails_the_policy(world: World) -> None:
    w = world
    for pw in ("\ud800" + "a" * 14, "a" * 14 + "\udfff", "a" * 6 + "\udc00" + "a" * 6):
        _refused(lambda: w.svc.onboard_create("acme", "x@acme.example", "X", pw, executive=False),
                 "PASSWORD_POLICY", 422)
        _refused(lambda: w.svc.onboard_set_password("amina@acme.example", pw), "PASSWORD_POLICY", 422)


# --- RV1-R2: the actor is re-checked inside the store -----------------------------------------------------------

def test_the_memory_store_refuses_a_grant_and_a_removal_by_a_former_executive(world: World) -> None:
    w = world
    pid = _person(w, "joseph@acme.example", "Joseph")
    executive = _principal(w, "amina@acme.example")
    own = w.store.held_grants(w.tenant, w.exec_id)[0]
    w.svc.grant(executive, pid, EXEC, None)
    w.clock.advance(seconds=1)
    w.svc.remove(executive, own.row_id)  # Amina is no longer an executive; her principal is stale
    w.clock.advance(seconds=1)
    _refused(lambda: w.svc.grant(executive, pid, "ANALYST", None), "ROLE_REQUIRED", 403)
    mine = w.store.held_grants(w.tenant, pid)[0]
    _refused(lambda: w.svc.remove(executive, mine.row_id), "ROLE_REQUIRED", 403)
