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
from assetops_backend.commercial.envelope import ParseEnvelope, default_envelope
from assetops_backend.commercial.months import CommercialMonths
from assetops_backend.commercial.profiles import SourceProfiles
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
#: ON1 (spec §3.5; D-ON1.7, D-ON1.14): terminal erasure.
KeyErased = file_key_store.KeyErased
key_state = file_key_store.key_state
erase_key_file = file_key_store.erase_key_file
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


class FileKeyFiles:
    """ON1 (spec §3.1, §3.5): the onboarding command's `KeyFiles` port over one key directory."""

    def __init__(self, directory: str) -> None:
        self._directory = directory

    def directory_ok(self) -> bool:
        return file_key_store.directory_ok(self._directory)

    def state(self, tenant_id) -> str:
        return file_key_store.key_state(self._directory, tenant_id)

    def create(self, tenant_id) -> None:
        file_key_store.create_key_file(self._directory, tenant_id)


class OperatorDatabaseRefused(Exception):
    """3A3 (spec §2.6; D-3A3.6): an `assetops_op*` database (any case). Carries no part of the URL."""


def refuse_operator_database(url: str) -> None:
    """3A3 (spec §2.6 step 2): before any connection, refuse a URL that does not name one database plainly
    (`DatabaseTargetUnclear`, RC4-F1) or that names an operator's database (`OperatorDatabaseRefused`). Every non-app
    caller of `build_commercial_uploads` calls this first (S1's allowlist)."""
    target = database_target(url)
    if is_operator_name(target.name):
        raise OperatorDatabaseRefused()


def build_commercial_uploads(database_url: str, settings: UploadSettings, *,
                             envelope: ParseEnvelope | None = None) -> CommercialUploads:
    """`envelope`: the parse envelope (spec §2.12); omitted, the process's one shared `default_envelope()`."""
    if settings.key_dir is None:
        raise ConfigurationError("Commercial uploads need ASSETOPS_PSEUDONYM_KEY_DIR.")
    envelope = envelope if envelope is not None else default_envelope()
    store = PostgresCommercialStore(database_url)
    profiles = SourceProfiles(store, clock=_now, real_data=settings.real_data, envelope=envelope)  # 3A6 (spec §2.6)
    return CommercialUploads(CommercialRecords(store, clock=_now), store, FileKeyStore(settings.key_dir), clock=_now,
                             real_data=settings.real_data, profiles=profiles, envelope=envelope)


def build_source_profiles(database_url: str, *,
                          envelope: ParseEnvelope | None = None) -> tuple[SourceProfiles, Callable[[], None]]:
    """3A6 (spec §2.6, §2.7): the admission service for the `source_profile` command, on the same settings path
    (`commercial_upload_settings`: the real-data switch follows the database); and its store's `dispose`."""
    settings = commercial_upload_settings(database_url)
    store = PostgresCommercialStore(database_url)
    return SourceProfiles(store, clock=_now, real_data=settings.real_data, envelope=envelope), store.dispose

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
