"""3A2 (spec §3.4; D-3A2.5, R12): the pseudonym key files, one per tenant, outside the database.

`FileKeyStore(directory).key(tenant_id)` reads `<directory>/<tenant_id>.key` with `O_RDONLY | O_NOFOLLOW` and checks it
with `fstat` on that descriptor: absent is `PseudonymKeyMissing`; a symlink (`ELOOP`), anything but a regular file of
exactly 32 bytes, or a mode readable or writable by group or others, is `PseudonymKeyUnusable`.

`create_key_file(directory, tenant_id)` writes 32 bytes from `secrets.token_bytes` with `O_WRONLY | O_CREAT | O_EXCL`
and mode 0600. An existing key is never replaced (`KeyExists`) and a missing directory is never created
(`KeyDirectoryMissing`). Only `commercial/composition.py` imports this module.
"""
from __future__ import annotations

import errno
import os
import secrets
import stat
from pathlib import Path
from uuid import UUID

from assetops_backend.commercial.pseudonym import PseudonymKeyMissing, PseudonymKeyUnusable

KEY_BYTES = 32


class KeyExists(Exception):
    """A key already exists for this tenant; it is never replaced."""


class KeyDirectoryMissing(Exception):
    """The key directory does not exist; it is never created here."""


def _path(directory: Path | str, tenant_id: UUID) -> Path:
    return Path(directory) / f"{UUID(str(tenant_id))}.key"


class FileKeyStore:
    def __init__(self, directory: Path | str) -> None:
        self._directory = Path(directory)

    def key(self, tenant_id: UUID) -> bytes:
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
