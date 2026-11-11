"""INFRA-1 (D-E5.47): the one decision whether a read failure is an infrastructure failure.

A failure is transient (infrastructure) when the exception, or anything in its `__cause__`/`__context__` chain, is
a DB or network connection error: SQLAlchemy `OperationalError`, `InterfaceError`, `DisconnectionError` or
`TimeoutError` (the pool timeout); psycopg `OperationalError` (`TooManyConnections` is one); a `DBAPIError` with
`connection_invalidated`; `ConnectionError`, `OSError` or `socket.timeout`.

A wrapper class alone is never transient: `LedgerUnavailable`, `*StoreUnavailable` and `PortUnavailable` are also
raised for deterministic states ("DATABASE_URL is not set", "not wired"), which keep their honest PARTIAL/UNKNOWN.

The deterministic file-system `OSError` subclasses (a missing file, a permission refusal) are not connection errors
and are not transient (packet, Known Deviations): a missing manifest is a stable state, never "retry later".
"""
from __future__ import annotations

import socket
from typing import Any

from sqlalchemy import exc as sa_exc

try:  # psycopg is the production driver; a process without it still decides on the SQLAlchemy classes
    import psycopg as _psycopg
except ImportError:  # pragma: no cover - the backend always installs psycopg
    _psycopg = None

_SA = (sa_exc.OperationalError, sa_exc.InterfaceError, sa_exc.DisconnectionError, sa_exc.TimeoutError)
_FILE_STATES = (FileNotFoundError, FileExistsError, IsADirectoryError, NotADirectoryError, PermissionError)


def _one(error: BaseException) -> bool:
    if isinstance(error, _SA):
        return True
    if _psycopg is not None and isinstance(error, _psycopg.OperationalError):  # incl. errors.TooManyConnections
        return True
    if isinstance(error, sa_exc.DBAPIError) and getattr(error, "connection_invalidated", False):
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


def _on_handle_error(ctx: Any) -> None:
    """The backstop (D-E5.47 rule 2): mark the current read scope when the engine reports a disconnect or an
    `OperationalError`, so a composer catch that drops the cause still cannot store a degraded body. A pre-ping
    failure is the pool recovering a stale connection (it reconnects), never a failed read."""
    if getattr(ctx, "is_pre_ping", False):
        return
    if ctx.is_disconnect or isinstance(ctx.original_exception, (sa_exc.OperationalError,)) or (
            _psycopg is not None and isinstance(ctx.original_exception, _psycopg.OperationalError)):
        from assetops_backend import read_scope

        read_scope.mark_degraded("db.handle_error")


def install_handle_error_hook() -> None:
    """Register the one global `handle_error` listener on every `Engine` (idempotent; `create_app` calls it)."""
    from sqlalchemy import event
    from sqlalchemy.engine import Engine

    if not event.contains(Engine, "handle_error", _on_handle_error):
        event.listen(Engine, "handle_error", _on_handle_error)
