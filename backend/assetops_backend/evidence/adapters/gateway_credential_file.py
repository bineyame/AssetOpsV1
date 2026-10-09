"""The gateway's protected upload-credential file (S2-02 phase 2).

The only place the raw bearer secret is written: once, owner-only, replaced
atomically, into the file the gateway reads as protected configuration
(`D-2026-10-09-s2-pilot-gateway-upload-credential`). Never a database row.
"""

from __future__ import annotations

import os
from pathlib import Path


def write_credential_file(path_text: str, token: str) -> None:
    """Write the secret owner-only, replacing atomically so a reader never sees half a token."""
    path = Path(path_text)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        temporary.unlink()
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="ascii", newline="\n") as handle:
        handle.write(token + "\n")
    os.replace(temporary, path)
