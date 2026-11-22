"""6c (spec §3.1): the study file's bytes, read from disk. The only file read of the evaluation; the configuration
persistence guard keeps file access inside `decisions/adapters/`. `decisions/composition.py` injects it."""
from __future__ import annotations

from os import PathLike
from pathlib import Path

__all__ = ["read_study_bytes"]


def read_study_bytes(path: str | PathLike) -> bytes:
    return Path(path).read_bytes()
