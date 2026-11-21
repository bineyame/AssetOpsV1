"""ENV-1 (spec §2.1; D-ENV1.3, D-ENV1.8): parse slots bounded per network namespace.

A slot is an abstract-namespace Unix socket name, ``"\\0" + f"{namespace}.{pool}.{i}"``: holding it is ``bind``,
releasing it is ``close``. The kernel frees the name when the holder's descriptor closes, ``SIGKILL`` included, so a
dead holder never keeps a slot. Every process in one network namespace with ``ASSETOPS_PARSE_SLOT_NAMESPACE`` unset
shares one pool (``serve_tls``, the lab app and the loader on this host, whatever their uid or temporary directory);
a container or a ``PrivateNetwork`` unit has its own namespace and counts as another host. Any process in the
namespace can bind the names: the slots bound resources, they are not a security boundary (row 49).

No file system call and no logging: nothing is written to disk. Linux only (abstract socket names).
"""
from __future__ import annotations

import errno
import os
import re
import socket
import threading
import time
from contextlib import contextmanager
from types import MappingProxyType
from typing import Iterator, Mapping

NAMESPACE_ENV = "ASSETOPS_PARSE_SLOT_NAMESPACE"
DEFAULT_NAMESPACE = "assetops-parse"
POOLS = MappingProxyType({"commercial": 2, "reading": 2})
POLL_SECONDS = 0.05

_NAMESPACE = re.compile(r"[a-z0-9][a-z0-9-]{0,47}")
_POOL = re.compile(r"[a-z][a-z0-9-]{0,31}")


class SlotWaitExpired(Exception):
    """The wait passed its timeout; no slot was taken."""


class HostSlots:
    """``count`` slots of ``pool`` in ``namespace``, shared by every process of the network namespace."""

    def __init__(self, namespace: str, pool: str, count: int) -> None:
        if not isinstance(namespace, str) or not _NAMESPACE.fullmatch(namespace):
            raise ValueError("a slot namespace is 1 to 48 of a-z, 0-9 and '-', not starting with '-'")
        if not isinstance(pool, str) or not _POOL.fullmatch(pool):
            raise ValueError("a slot pool is 1 to 32 of a-z, 0-9 and '-', starting with a letter")
        if isinstance(count, bool) or not isinstance(count, int) or count < 1:
            raise ValueError("a slot count is an int >= 1")
        self.namespace, self.pool, self.count = namespace, pool, count
        self._names = tuple(f"\0{namespace}.{pool}.{i}" for i in range(count))

    @contextmanager
    def hold(self, timeout: float | None = None) -> Iterator[int]:
        """Take a free slot (its index), waiting up to ``timeout`` seconds (``None``: without end)."""
        if timeout is not None and (isinstance(timeout, bool) or not isinstance(timeout, (int, float))
                                    or not timeout > 0):
            raise ValueError("a slot wait timeout is None or a number > 0")
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            for index, name in enumerate(self._names):
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                try:
                    sock.bind(name)
                except OSError as error:
                    sock.close()
                    if error.errno == errno.EADDRINUSE:
                        continue
                    raise
                try:
                    yield index
                finally:
                    sock.close()
                return
            if deadline is not None and time.monotonic() >= deadline:
                raise SlotWaitExpired(f"no {self.pool} parse slot came free within {timeout} s")
            time.sleep(POLL_SECONDS)


def slot_namespace(environ: Mapping[str, str] = os.environ) -> str:
    """``ASSETOPS_PARSE_SLOT_NAMESPACE`` when set and non-empty, else ``DEFAULT_NAMESPACE``."""
    value = environ.get(NAMESPACE_ENV) or DEFAULT_NAMESPACE
    if not _NAMESPACE.fullmatch(value):
        raise ValueError(f"{NAMESPACE_ENV} must be 1 to 48 of a-z, 0-9 and '-', not starting with '-'")
    return value


_CACHE: dict[tuple[str, str], HostSlots] = {}
_CACHE_LOCK = threading.Lock()


def host_slots(pool: str) -> HostSlots:
    """Production: ``POOLS[pool]`` slots in ``slot_namespace()`` (read at each call), one object per (ns, pool)."""
    count = POOLS[pool]
    namespace = slot_namespace()
    with _CACHE_LOCK:
        key = (namespace, pool)
        if key not in _CACHE:
            _CACHE[key] = HostSlots(namespace, pool, count)
        return _CACHE[key]
