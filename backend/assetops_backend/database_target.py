"""RC4-F1 (spec §2.1, D-RC4F1.1): the database a URL really reaches, as libpq will reach it, or a refusal.

`make_url(url).database` is the path's name, but the psycopg dialect lets a query `dbname` win, an empty name falls
to the environment, and libpq fills an absent host, port or name from `PG*` variables or a service file. Every
decision about a database by its name (RC4, the backfill's protected databases) asks `database_target`, which refuses
every URL or environment in which the URL alone does not say the target. No connection, no dialect import.
"""
from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass

from sqlalchemy.engine import make_url

DRIVERS = frozenset({"postgresql", "postgresql+psycopg", "postgresql+psycopg2"})
#: An allowlist: a libpq keyword added later is refused until reviewed.
ALLOWED_QUERY = frozenset({"connect_timeout", "sslmode", "sslrootcert", "application_name"})
PG_TARGET_ENV = ("PGDATABASE", "PGHOST", "PGHOSTADDR", "PGPORT", "PGSERVICE", "PGSERVICEFILE")
NAME = re.compile(r"[A-Za-z0-9_]{1,63}")
OPERATOR_PREFIX = "assetops_op"  # broad detection: any case
OPERATOR_DATABASE = re.compile(r"assetops_op_[a-z0-9_]{1,40}")  # strict admission


@dataclass(frozen=True)
class DatabaseTarget:
    host: str
    port: int | None
    name: str


class DatabaseTargetUnclear(ValueError):
    """`reason` is a code, plus a key or variable name; never a value from the URL (it may hold a password)."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def database_target(url: str, environ: Mapping[str, str] | None = None) -> DatabaseTarget:
    env = os.environ if environ is None else environ
    try:
        parsed = make_url(url)
    except Exception:  # noqa: BLE001 - any parse failure is the same refusal, and never echoes the URL
        raise DatabaseTargetUnclear("URL_UNREADABLE") from None
    if parsed.drivername not in DRIVERS:
        raise DatabaseTargetUnclear("DRIVER_NOT_POSTGRES")
    for key, value in parsed.query.items():
        if key not in ALLOWED_QUERY:
            raise DatabaseTargetUnclear(f"QUERY_KEY {key}")
        if isinstance(value, tuple):
            raise DatabaseTargetUnclear(f"QUERY_REPEATED {key}")
    if not parsed.host:
        raise DatabaseTargetUnclear("HOST_MISSING")
    if "," in parsed.host:
        raise DatabaseTargetUnclear("HOST_MULTIPLE")
    if not parsed.database:
        raise DatabaseTargetUnclear("NAME_MISSING")
    if not NAME.fullmatch(parsed.database):
        raise DatabaseTargetUnclear("NAME_NOT_PLAIN")
    for variable in PG_TARGET_ENV:
        if env.get(variable):
            raise DatabaseTargetUnclear(f"ENVIRONMENT {variable}")
    return DatabaseTarget(parsed.host, parsed.port, parsed.database)


def is_operator_name(name: str) -> bool:
    return name.lower().startswith(OPERATOR_PREFIX)
