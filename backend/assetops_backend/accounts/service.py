"""3C0a (spec §3, §4.2; D-3C0A.5-.7, .11, R4-R8, MB1, MB2): sign-in, sessions, role grants and onboarding writes.

- Sign-in runs exactly one scrypt verification on every path that reaches the store, refused or not (R4): the stored
  hash when one exists, else `DUMMY_HASH`; the status check comes after it. Every refusal is the one
  `SIGN_IN_REFUSED` (D-3C0A.6). Count, verification and the attempt row run under the per-email lock
  (`AccountStore.guarded_attempt`, R5).
- A session is a random token; only its SHA-256 is stored. It is valid for 12 hours from sign-in, absolute, while not
  revoked, the account is ACTIVE and it is not older than the latest password (R8, MB1).
- Roles are read from the held grants at each `resolve` (OD-14).
"""
from __future__ import annotations

import hashlib
import math
import secrets
from datetime import datetime, timedelta
from typing import Callable
from uuid import UUID, uuid4

from assetops_backend.accounts import passwords
from assetops_backend.accounts.model import (EXECUTIVE, LOCK_MINUTES, ONBOARDING, ROLES, SESSION_HOURS, SITE_ROLE,
                                             Account, AccountRefused, GrantRow, PersonPrincipal, PersonView, SignedIn)
from assetops_backend.accounts.store import AccountStore, StoreConflict

#: The HTTP status each store refusal answers with.
_CONFLICT_STATUS = {"ROLE_ALREADY_HELD": 409, "GRANT_ALREADY_REMOVED": 409, "LAST_EXECUTIVE": 409,
                    "EMAIL_TAKEN": 409, "EXECUTIVE_EXISTS": 409, "ROLE_REQUIRED": 403,
                    "ACCOUNTS_STORE_REFUSED": 422}
STATUSES = ("ACTIVE", "DISABLED")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _token() -> str:
    return secrets.token_urlsafe(32)


def _uuid(value: UUID | str) -> UUID | None:
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except ValueError:
        return None


def _conflict(conflict: StoreConflict, **params) -> AccountRefused:
    if conflict.constraint is not None:
        params = {**params, "constraint": conflict.constraint}
    return AccountRefused(conflict.code, _CONFLICT_STATUS.get(conflict.code, 409), params)


class AccountService:
    def __init__(self, store: AccountStore, *, clock: Callable[[], datetime],
                 token: Callable[[], str] = _token) -> None:
        self._store = store
        self._clock = clock
        self._token = token

    # --- sign-in and sessions ---------------------------------------------------------------------------------------

    def sign_in(self, email: str, password: str) -> SignedIn:
        now = self._clock()
        typed = password[:passwords.MAX_PASSWORD]  # only the first 128 characters reach scrypt (R9)
        too_long = len(password) > passwords.MAX_PASSWORD
        try:
            _, key = passwords.normalise_email(email)
        except AccountRefused:
            passwords.verify_password(typed, passwords.DUMMY_HASH)  # no row: it can match no account (D-3C0A.11)
            raise AccountRefused("SIGN_IN_REFUSED", 401) from None

        def verify() -> tuple[bool, UUID | None]:
            account = self._store.account_by_email_key(key)
            credential = self._store.current_credential(account.id) if account is not None else None
            matched = passwords.verify_password(typed, credential[0] if credential else passwords.DUMMY_HASH)
            if account is None or credential is None or too_long or not matched:
                return False, None
            if self._store.current_status(account.id) != "ACTIVE":  # after the verification (R4)
                return False, None
            return True, account.id

        attempt = self._store.guarded_attempt(hashlib.sha256(key.encode("ascii")).hexdigest(), now, verify)
        if attempt.locked:
            minutes = math.ceil((attempt.retry_at - now) / timedelta(minutes=1))
            raise AccountRefused("SIGN_IN_LOCKED", 429, {"minutes": max(1, minutes)})
        if not attempt.succeeded or attempt.person_id is None:
            raise AccountRefused("SIGN_IN_REFUSED", 401)
        account = self._store.account_by_email_key(key)
        assert account is not None and account.id == attempt.person_id
        token = self._token()
        session_id, expires = uuid4(), now + timedelta(hours=SESSION_HOURS)
        self._store.add_session(session_id, account.tenant_id, account.id, _sha256(token), now, expires)
        return SignedIn(self._principal(account, session_id, expires, now), token, expires)

    def sign_out(self, token: str | None) -> None:
        if token:
            self._store.revoke(_sha256(token), self._clock())

    def resolve(self, token: str | None) -> PersonPrincipal | None:
        if not token:
            return None
        session = self._store.session(_sha256(token))
        if session is None or session.revoked_at is not None:
            return None
        now = self._clock()
        if now >= session.expires_at:
            return None
        credential = self._store.current_credential(session.person_id)
        if credential is None or session.created_at < credential[1]:  # a new password ends older sessions (MB1)
            return None
        if self._store.current_status(session.person_id) != "ACTIVE":
            return None
        account = self._store.account(session.tenant_id, session.person_id)
        if account is None:
            return None
        return self._principal(account, session.id, session.expires_at, now)

    def _principal(self, account: Account, session_id: UUID, expires: datetime, now: datetime) -> PersonPrincipal:
        roles = frozenset((g.role, g.site_id) for g in self._store.held_grants(account.tenant_id, account.id))
        return PersonPrincipal(account.id, account.tenant_id, account.display_name, roles, session_id, expires, now)

    def tenant(self, principal: PersonPrincipal) -> tuple[str, str] | None:
        """(slug, name) of the principal's tenant (MB2)."""
        return self._store.tenant(principal.tenant_id)

    # --- Organisation reads -----------------------------------------------------------------------------------------

    def people(self, principal: PersonPrincipal) -> tuple[PersonView, ...]:
        return self._store.people(principal.tenant_id)

    def grant_record(self, principal: PersonPrincipal) -> tuple[GrantRow, ...]:
        return self._store.grant_rows(principal.tenant_id)

    # --- grants -----------------------------------------------------------------------------------------------------

    def grant(self, principal: PersonPrincipal, person_id: UUID | str, role: str, site_code: str | None) -> GrantRow:
        if not principal.has_role(EXECUTIVE):
            raise AccountRefused("ROLE_REQUIRED", 403)
        if role not in ROLES:
            raise AccountRefused("ROLE_UNKNOWN", 422)
        if (role == SITE_ROLE) != (site_code is not None):
            raise AccountRefused("ROLE_SITE_RULE", 422)
        pid = _uuid(person_id)
        target = self._store.account(principal.tenant_id, pid) if pid is not None else None
        if target is None:
            raise AccountRefused("PERSON_NOT_FOUND", 404)
        site_id = None
        if site_code is not None:
            site_id = self._store.site_id(principal.tenant_id, site_code)
            if site_id is None:
                raise AccountRefused("SITE_NOT_FOUND", 404)
        row_id = uuid4()
        row = GrantRow(row_id, row_id, principal.tenant_id, target.id, target.display_name, role, site_id, site_code,
                       "GRANTED", principal.person_id, principal.display_name, None, self._clock())
        try:
            return self._store.add_grant(row, principal.person_id)  # the store answers the row as recorded (the Site's own code)
        except StoreConflict as conflict:
            raise _conflict(conflict, name=target.display_name) from None

    def remove(self, principal: PersonPrincipal, grant_id: UUID | str) -> GrantRow:
        if not principal.has_role(EXECUTIVE):
            raise AccountRefused("ROLE_REQUIRED", 403)
        gid = _uuid(grant_id)
        granted = self._store.grant_row(principal.tenant_id, gid) if gid is not None else None
        if granted is None or granted.action != "GRANTED":
            raise AccountRefused("GRANT_NOT_FOUND", 404)
        row = GrantRow(uuid4(), granted.row_id, granted.tenant_id, granted.person_id, granted.display_name,
                       granted.role, granted.site_id, granted.site_code, "REMOVED", principal.person_id,
                       principal.display_name, None, self._clock())
        try:
            return self._store.add_removal(row, principal.person_id)
        except StoreConflict as conflict:
            raise _conflict(conflict) from None

    # --- the onboarding command's writes (P2), each by `service:onboarding` ----------------------------------------

    def onboard_create(self, tenant_slug: str, email: str, display_name: str, password: str, *,
                       executive: bool) -> UUID:
        tenant = self._store.tenant_by_slug(tenant_slug)
        if tenant is None:
            raise AccountRefused("TENANT_NOT_FOUND", 404)
        email, key = passwords.normalise_email(email)
        display_name = display_name.strip() if isinstance(display_name, str) else ""
        if not 1 <= len(display_name) <= 120:
            raise AccountRefused("BAD_NAME", 422)
        if self._store.account_by_email_key(key) is not None:
            raise AccountRefused("EMAIL_TAKEN", 409)
        passwords.check_policy(password)
        stored = passwords.hash_password(password)
        now = self._clock()
        account = Account(uuid4(), tenant[0], email, display_name)
        grant = None
        if executive:
            row_id = uuid4()
            grant = GrantRow(row_id, row_id, account.tenant_id, account.id, display_name, EXECUTIVE, None, None,
                             "GRANTED", None, None, ONBOARDING, now)
        try:
            self._store.create_account(account, stored, now, ONBOARDING, grant)
        except StoreConflict as conflict:
            raise _conflict(conflict) from None
        return account.id

    def _onboard_account(self, email: str) -> Account:
        try:
            _, key = passwords.normalise_email(email)
        except AccountRefused:
            raise AccountRefused("PERSON_NOT_FOUND", 404) from None
        account = self._store.account_by_email_key(key)
        if account is None:
            raise AccountRefused("PERSON_NOT_FOUND", 404)
        return account

    def onboard_set_password(self, email: str, password: str) -> UUID:
        account = self._onboard_account(email)
        passwords.check_policy(password)
        try:
            self._store.set_credential(account.tenant_id, account.id, passwords.hash_password(password),
                                       self._clock(), ONBOARDING)
        except StoreConflict as conflict:
            raise _conflict(conflict) from None
        return account.id

    def onboard_set_status(self, email: str, status: str, reason: str | None) -> UUID:
        if status not in STATUSES:
            raise ValueError(f"status must be one of {STATUSES}")
        account = self._onboard_account(email)
        if reason is not None:
            reason = reason.strip()
            if not 1 <= len(reason) <= 500:
                raise AccountRefused("BAD_REASON", 422)
        try:
            self._store.set_status(account.tenant_id, account.id, status, reason, self._clock(), ONBOARDING)
        except StoreConflict as conflict:
            raise _conflict(conflict) from None
        return account.id
