"""3A1 (spec §4): composes the commercial record service; the only importer of the Postgres adapter. 3A2 (spec §4,
D-3A2.6, R3): the upload settings and the upload service.

`commercial_upload_settings` is RC4 in code: `ASSETOPS_REAL_OPERATOR_DATA=on` exactly when the database is an operator
database (`assetops_op_<name>`). Detection is broad (any name starting `assetops_op`, any case, refuses the switch
off) and admission strict (the switch on needs the exact lower-case form). `create_app` runs it first, whatever the
key directory says.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone

from assetops_backend.commercial.adapters import file_key_store
from assetops_backend.commercial.adapters.postgres_commercial_store import (UNAVAILABLE, PostgresCommercialStore,
                                                                           database_name)
from assetops_backend.commercial.service import CommercialRecords
from assetops_backend.commercial.uploads import CommercialUploads
from assetops_backend.config import ConfigurationError

#: D-3A2.2: a connection failure is retried; the routes answer 503 for these.
COMMERCIAL_UNAVAILABLE = UNAVAILABLE
#: The key files (the adapter is imported here only).
FileKeyStore = file_key_store.FileKeyStore
create_key_file = file_key_store.create_key_file
KeyExists = file_key_store.KeyExists
KeyDirectoryMissing = file_key_store.KeyDirectoryMissing
REAL_DATA_ENV = "ASSETOPS_REAL_OPERATOR_DATA"
KEY_DIR_ENV = "ASSETOPS_PSEUDONYM_KEY_DIR"
_OPERATOR_DATABASE = re.compile(r"assetops_op_[a-z0-9_]{1,40}")
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
    name = database_name(database_url) if database_url else None
    if real_data:
        admitted = name is not None and _OPERATOR_DATABASE.fullmatch(name) is not None
    else:
        admitted = name is None or not name.lower().startswith("assetops_op")
    if not admitted:
        raise ConfigurationError(_MISMATCH)
    key_dir = os.environ.get(KEY_DIR_ENV)
    return UploadSettings(key_dir or None, real_data)


def build_commercial_records(database_url: str) -> CommercialRecords:
    return CommercialRecords(PostgresCommercialStore(database_url), clock=_now)


def build_commercial_uploads(database_url: str, settings: UploadSettings) -> CommercialUploads:
    if settings.key_dir is None:
        raise ConfigurationError("Commercial uploads need ASSETOPS_PSEUDONYM_KEY_DIR.")
    store = PostgresCommercialStore(database_url)
    return CommercialUploads(CommercialRecords(store, clock=_now), store, FileKeyStore(settings.key_dir), clock=_now,
                             real_data=settings.real_data)
