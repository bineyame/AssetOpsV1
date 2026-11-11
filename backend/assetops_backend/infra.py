"""INFRA-1 (D-E5.47): the one decision whether a read failure is an infrastructure failure.

A failure is transient (infrastructure) when the exception, or anything in its `__cause__`/`__context__` chain, is
a DB or network connection error: SQLAlchemy `OperationalError`, `InterfaceError`, `DisconnectionError` or
`TimeoutError` (the pool timeout); psycopg `OperationalError` (`TooManyConnections` is one); a `DBAPIError` with
`connection_invalidated`; `ConnectionError`, `OSError` or `socket.timeout`.

A wrapper class alone is never transient: `LedgerUnavailable`, `*StoreUnavailable` and `PortUnavailable` are also
raised for deterministic states ("DATABASE_URL is not set", "not wired"), which keep their honest PARTIAL/UNKNOWN.

The deterministic file-system `OSError` subclasses (a missing file, a permission refusal) are not connection errors
and are not transient (packet, Known Deviations): a missing manifest is a stable state, never "retry later".

The driver classes are matched by their defining module and name along the exception's MRO, so this module imports
no database driver (the configuration-persistence guard keeps drivers in the adapters). The global `handle_error`
backstop lives in the response-store adapter (`chain/adapters/postgres_response_store.install_handle_error_hook`).
"""
from __future__ import annotations

import socket
from typing import Any

_SA_TRANSIENT = frozenset({"OperationalError", "InterfaceError", "DisconnectionError", "TimeoutError"})
_FILE_STATES = (FileNotFoundError, FileExistsError, IsADirectoryError, NotADirectoryError, PermissionError)


def _driver_class(error: BaseException, package: str, names: frozenset[str]) -> bool:
    """`error` is (a subclass of) a class named in `names` defined in `package` (or a submodule)."""
    return any(c.__name__ in names and (c.__module__ == package or c.__module__.startswith(package + "."))
               for c in type(error).__mro__)


def _one(error: BaseException) -> bool:
    if _driver_class(error, "sqlalchemy", _SA_TRANSIENT):
        return True
    if _driver_class(error, "psycopg", frozenset({"OperationalError"})):  # incl. errors.TooManyConnections
        return True
    if _driver_class(error, "sqlalchemy", frozenset({"DBAPIError"})) and getattr(error, "connection_invalidated",
                                                                               False):
        return True
    if isinstance(error, _FILE_STATES):
        return False
    return isinstance(error, (ConnectionError, OSError, socket.timeout))


def is_transient(error: BaseException | None) -> bool:
    """True when `error` or anything in its cause/context chain is an infrastructure (connection) failure."""
    seen: set[int] = set()
    stack: list[Any] = [error]
    while stack:
        e = stack.pop()
        if e is None or id(e) in seen:
            continue
        seen.add(id(e))
        if _one(e):
            return True
        stack.append(e.__cause__)
        stack.append(e.__context__)
        orig = getattr(e, "orig", None)  # a SQLAlchemy StatementError carries the DBAPI error as `orig`
        if isinstance(orig, BaseException):
            stack.append(orig)
    return False


def is_connection_error(error: BaseException | None) -> bool:
    """The `handle_error` backstop's test on `ctx.original_exception`: a SQLAlchemy or psycopg
    `OperationalError` (a statement error such as `ProgrammingError` is not)."""
    return error is not None and (_driver_class(error, "sqlalchemy", frozenset({"OperationalError"}))
                                  or _driver_class(error, "psycopg", frozenset({"OperationalError"})))
