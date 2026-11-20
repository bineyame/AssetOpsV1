"""3C0a (spec §6): composes the account service; the only importer of the Postgres adapter."""
from __future__ import annotations

import os
from datetime import datetime, timezone

from assetops_backend.accounts.adapters.postgres_account_store import UNAVAILABLE, PostgresAccountStore
from assetops_backend.accounts.service import AccountService
from assetops_backend.config import ConfigurationError

SECURE_ENV = "ASSETOPS_SESSION_COOKIE_SECURE"
REQUIRE_PERSON_ENV = "ASSETOPS_REQUIRE_PERSON"
#: The store errors the account routes answer 503 (R14), as reading-upload's `unavailable` tuple.
ACCOUNTS_UNAVAILABLE = UNAVAILABLE


def _now() -> datetime:
    return datetime.now(timezone.utc)


def build_account_service(database_url: str) -> AccountService:
    return AccountService(PostgresAccountStore(database_url), clock=_now)


def require_person() -> bool:
    """3C1a (spec §2, D-3C1.1, R10): `ASSETOPS_REQUIRE_PERSON` unset or `off` is off, `on` is on, anything else
    refuses. Read once, in `create_app`; `3C0b` turns it on."""
    value = os.environ.get(REQUIRE_PERSON_ENV)
    if value is None or value == "off":
        return False
    if value == "on":
        return True
    raise ConfigurationError("ASSETOPS_REQUIRE_PERSON must be 'on', 'off' or unset")


def session_cookie_secure() -> bool:
    """Unset or `on`: the cookie is `Secure`; `off` (local http only): it is not; anything else refuses."""
    value = os.environ.get(SECURE_ENV)
    if value is None or value == "on":
        return True
    if value == "off":
        return False
    raise ConfigurationError("ASSETOPS_SESSION_COOKIE_SECURE must be 'on', 'off' or unset")
