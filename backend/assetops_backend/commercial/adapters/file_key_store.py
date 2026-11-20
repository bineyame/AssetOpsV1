"""3A2 (spec §3.4; D-3A2.5, R12): the pseudonym key files, one per tenant, outside the database. ON1 (spec §3.5;
D-ON1.7, D-ON1.14): erasure is terminal.

`FileKeyStore(directory).key(tenant_id)` reads `<directory>/<tenant_id>.key` with `O_RDONLY | O_NOFOLLOW` and checks it
with `fstat` on that descriptor: absent is `PseudonymKeyMissing`; a symlink (`ELOOP`), anything but a regular file of
exactly 32 bytes, or a mode readable or writable by group or others, is `PseudonymKeyUnusable`.

`create_key_file(directory, tenant_id)` writes 32 bytes from `secrets.token_bytes` with `O_WRONLY | O_CREAT | O_EXCL`
and mode 0600. An existing key is never replaced (`KeyExists`) and a missing directory is never created
(`KeyDirectoryMissing`). Only `commercial/composition.py` imports this module.

ON1: an erased key leaves a tombstone `<directory>/<tenant_id>.erased`. `_tombstoned` is the one detection, by
`os.lstat`, failing closed: only `FileNotFoundError` means "no tombstone"; a file, a symlink, a dangling symlink or a
permission error each mean "erased". `FileKeyStore.key`, `create_key_file`, `key_state` and `erase_key_file` use it.
"""
from __future__ import annotations

import errno
import os
import secrets
import stat
from pathlib import Path
from uuid import UUID

from assetops_backend.commercial.pseudonym import PseudonymKeyErased, PseudonymKeyMissing, PseudonymKeyUnusable

KEY_BYTES = 32
TOMBSTONE = b"erased\n"


class KeyExists(Exception):
    """A key already exists for this tenant; it is never replaced."""


class KeyDirectoryMissing(Exception):
    """The key directory does not exist; it is never created here."""


class KeyErased(Exception):
    """ON1: this tenant's key was erased; a new key would not match the records already held."""


def _path(directory: Path | str, tenant_id: UUID) -> Path:
    return Path(directory) / f"{UUID(str(tenant_id))}.key"


def _tombstone(directory: Path | str, tenant_id: UUID) -> Path:
    return Path(directory) / f"{UUID(str(tenant_id))}.erased"


def _tombstoned(directory: Path | str, tenant_id: UUID) -> bool:
    """D-ON1.14: whether the tenant's key was erased. Anything but a plain "not found" is erased (fails closed)."""
    try:
        os.lstat(_tombstone(directory, tenant_id))
    except FileNotFoundError:
        return False
    except OSError:
        return True
    return True


class FileKeyStore:
    def __init__(self, directory: Path | str) -> None:
        self._directory = Path(directory)

    def key(self, tenant_id: UUID) -> bytes:
        if _tombstoned(self._directory, tenant_id):
            raise PseudonymKeyErased()
        try:
            fd = os.open(_path(self._directory, tenant_id), os.O_RDONLY | os.O_NOFOLLOW)
        except FileNotFoundError:
            raise PseudonymKeyMissing() from None
        except OSError as error:
            if error.errno != errno.ELOOP:
                raise
            symlink = True
        else:
            symlink = False
        if symlink:  # raised outside the handler
            raise PseudonymKeyUnusable()
        try:
            info = os.fstat(fd)
            usable = stat.S_ISREG(info.st_mode) and info.st_mode & 0o077 == 0 and info.st_size == KEY_BYTES
            data = os.read(fd, KEY_BYTES + 1) if usable else b""
        finally:
            os.close(fd)
        if len(data) != KEY_BYTES:
            raise PseudonymKeyUnusable()
        return data


def create_key_file(directory: Path | str, tenant_id: UUID) -> None:
    if not Path(directory).is_dir():
        raise KeyDirectoryMissing()
    if _tombstoned(directory, tenant_id):
        raise KeyErased()
    try:
        fd = os.open(_path(directory, tenant_id), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        raise KeyExists() from None
    try:
        os.fchmod(fd, 0o600)
        data = secrets.token_bytes(KEY_BYTES)
        written = 0
        while written < KEY_BYTES:
            written += os.write(fd, data[written:])
    finally:
        os.close(fd)


def key_state(directory: Path | str, tenant_id: UUID) -> str:
    """ON1: `ERASED`, `PRESENT` or `MISSING`; no key byte is read."""
    if _tombstoned(directory, tenant_id):
        return "ERASED"
    return "PRESENT" if os.path.lexists(_path(directory, tenant_id)) else "MISSING"


def erase_key_file(directory: Path | str, tenant_id: UUID) -> str:
    """ON1 (D-ON1.14): write the tombstone if absent, then unlink the key if present, then sync the directory.
    `ALREADY_ERASED` when the tombstone stood and no key was unlinked, else `ERASED` (also when neither existed: the
    tombstone now forbids a new key)."""
    if not Path(directory).is_dir():
        raise KeyDirectoryMissing()
    had_tomb = _tombstoned(directory, tenant_id)
    if not had_tomb:
        fd = os.open(_tombstone(directory, tenant_id), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        try:
            os.fchmod(fd, 0o600)
            os.write(fd, TOMBSTONE)
            os.fsync(fd)
        finally:
            os.close(fd)
    key = _path(directory, tenant_id)
    unlinked = False
    if os.path.lexists(key):
        os.unlink(key)
        unlinked = True
    dir_fd = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)
    return "ALREADY_ERASED" if had_tomb and not unlinked else "ERASED"


def directory_ok(directory: Path | str) -> bool:
    """ON1 (R10): the key directory exists, is a directory and is readable by its owner only."""
    try:
        info = os.stat(directory)
    except OSError:
        return False
    return stat.S_ISDIR(info.st_mode) and info.st_mode & 0o077 == 0
