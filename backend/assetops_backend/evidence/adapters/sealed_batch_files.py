"""DD5a (D-DD.140): the sealed Batch V2 files beside a world's inputs, `<slug>/sealed/*.batch.json`.

Written once by `load_world_inputs` (a re-run re-seals and compares, never rewrites), read by `world check` C6. The
folder is the caller's (a generated world's inputs directory, outside the product's stores); nothing here is served.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Sequence


class SealedBatchFiles:
    def __init__(self, folder: Path) -> None:
        self.folder = folder

    def existing(self) -> dict[str, bytes]:
        if not self.folder.is_dir():
            return {}
        return {p.name: p.read_bytes() for p in sorted(self.folder.glob("*.batch.json"))}

    def write_new(self, batches: Sequence[tuple[str, bytes]]) -> None:
        """Each `(name, bytes)` not present yet; a present name is never rewritten."""
        for name, body in batches:
            path = self.folder / name
            if path.exists():
                continue
            self.folder.mkdir(parents=True, exist_ok=True)
            # Exclusive create plus fsync, as `legacy_comparison_file`: never an overwrite, never a silent short file.
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
            with os.fdopen(fd, "wb") as handle:
                handle.write(body)
                handle.flush()
                os.fsync(handle.fileno())
