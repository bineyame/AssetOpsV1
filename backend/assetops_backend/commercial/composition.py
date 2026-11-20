"""3A1 (spec §4): composes the commercial record service; the only importer of the Postgres adapter. 3A2 (spec §4,
D-3A2.6, R3): the upload settings and the upload service.

`commercial_upload_settings` is RC4 in code: `ASSETOPS_REAL_OPERATOR_DATA=on` exactly when the database is an operator
database (`assetops_op_<name>`). Detection is broad (any name starting `assetops_op`, any case, refuses the switch
off) and admission strict (the switch on needs the exact lower-case form). `create_app` runs it first, whatever the
key directory says. RC4-F1: the name is `database_target`'s, the database psycopg is really handed.
"""
from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from assetops_backend.commercial.adapters import file_key_store
from assetops_backend.commercial.adapters.postgres_commercial_store import UNAVAILABLE, PostgresCommercialStore
from assetops_backend.commercial.months import CommercialMonths
from assetops_backend.commercial.store import CommercialStore
from assetops_backend.commercial.service import CommercialRecords
from assetops_backend.commercial.uploads import CommercialUploads
from assetops_backend.config import ConfigurationError
from assetops_backend.database_target import (OPERATOR_DATABASE, DatabaseTargetUnclear, database_target,
                                             is_operator_name)

#: D-3A2.2: a connection failure is retried; the routes answer 503 for these.
COMMERCIAL_UNAVAILABLE = UNAVAILABLE
#: The key files (the adapter is imported here only).
FileKeyStore = file_key_store.FileKeyStore
create_key_file = file_key_store.create_key_file
KeyExists = file_key_store.KeyExists
KeyDirectoryMissing = file_key_store.KeyDirectoryMissing
REAL_DATA_ENV = "ASSETOPS_REAL_OPERATOR_DATA"
KEY_DIR_ENV = "ASSETOPS_PSEUDONYM_KEY_DIR"
_MISMATCH = ("Real operator data needs its own database (assetops_op_<name>) and ASSETOPS_REAL_OPERATOR_DATA=on, "
             "together.")


@dataclass(frozen=True)
class UploadSettings:
    key_dir: str | None  # the key directory as configured; None: uploads are off (403 COMMERCIAL_UPLOAD_OFF)
    real_data: bool


def _now() -> datetime:
    return datetime.now(timezone.utc)


def commercial_upload_settings(database_url: str | None) -> UploadSettings:
    switch = os.environ.get(REAL_DATA_ENV)
    if switch is None or switch == "off":
        real_data = False
    elif switch == "on":
        real_data = True
    else:
        raise ConfigurationError(_MISMATCH)
    name = None
    if database_url:
        # RC4-F1 (D-RC4F1.1): the database psycopg is handed, or a refusal whatever the switch says.
        try:
            name = database_target(database_url).name
        except DatabaseTargetUnclear as e:
            raise ConfigurationError(f"DATABASE_URL must name one database plainly ({e.reason}).") from None
    if real_data:
        admitted = name is not None and OPERATOR_DATABASE.fullmatch(name) is not None
    else:
        admitted = name is None or not is_operator_name(name)
    if not admitted:
        raise ConfigurationError(_MISMATCH)
    key_dir = os.environ.get(KEY_DIR_ENV)
    return UploadSettings(key_dir or None, real_data)


class OperatorDatabaseRefused(Exception):
    """3A3 (spec §2.6; D-3A3.6): an `assetops_op*` database (any case). Carries no part of the URL."""


def refuse_operator_database(url: str) -> None:
    """3A3 (spec §2.6 step 2): before any connection, refuse a URL that does not name one database plainly
    (`DatabaseTargetUnclear`, RC4-F1) or that names an operator's database (`OperatorDatabaseRefused`). Every non-app
    caller of `build_commercial_uploads` calls this first (S1's allowlist)."""
    target = database_target(url)
    if is_operator_name(target.name):
        raise OperatorDatabaseRefused()


def build_commercial_uploads(database_url: str, settings: UploadSettings) -> CommercialUploads:
    if settings.key_dir is None:
        raise ConfigurationError("Commercial uploads need ASSETOPS_PSEUDONYM_KEY_DIR.")
    store = PostgresCommercialStore(database_url)
    return CommercialUploads(CommercialRecords(store, clock=_now), store, FileKeyStore(settings.key_dir), clock=_now,
                             real_data=settings.real_data)

def build_commercial_months(database_url: str) -> CommercialMonths:
    """3A4 (spec §3.5): money by month over the Postgres store, with the UTC clock."""
    return CommercialMonths(PostgresCommercialStore(database_url), clock=_now)


@dataclass(frozen=True)
class CommercialReads:
    """4b1 (spec §2.6): the month reads and the store they rest on, for the structure's money leaves (4b2)."""

    months: CommercialMonths
    store: CommercialStore
    dispose: Callable[[], None]


def build_commercial_reads(database_url: str) -> CommercialReads:
    """One Postgres store, the months over it; `dispose` disposes that store."""
    store = PostgresCommercialStore(database_url)
    return CommercialReads(CommercialMonths(store, clock=_now), store, store.dispose)
