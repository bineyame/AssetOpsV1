"""DD5a fix round (L3): sealed files are written by exclusive create plus fsync."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from assetops_backend.evidence.adapters.sealed_batch_files import SealedBatchFiles


def test_each_new_file_is_fsynced(tmp_path, monkeypatch) -> None:
    synced: list[int] = []
    real = os.fsync
    monkeypatch.setattr(os, "fsync", lambda fd: (synced.append(fd), real(fd))[1])
    SealedBatchFiles(tmp_path / "a" / "b").write_new([("x.batch.json", b"1"), ("y.batch.json", b"2")])
    assert len(synced) >= 2 and (tmp_path / "a" / "b" / "y.batch.json").read_bytes() == b"2"


def test_a_file_that_appears_between_the_check_and_the_write_is_never_overwritten(tmp_path, monkeypatch) -> None:
    folder = tmp_path / "s"
    folder.mkdir()
    (folder / "x.batch.json").write_bytes(b"other")
    monkeypatch.setattr(Path, "exists", lambda self: False)
    with pytest.raises(FileExistsError):
        SealedBatchFiles(folder).write_new([("x.batch.json", b"mine")])
    assert (folder / "x.batch.json").read_bytes() == b"other"
