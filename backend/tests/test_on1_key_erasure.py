"""ON1 (spec §3.5, §6 "Keys, no database"; D-ON1.7, D-ON1.14): erasing a tenant's pseudonym key is terminal.

Files in `tmp_path` only. The autouse no-connect fixture (D-ON1.12) makes any database connection raise.
"""
from __future__ import annotations

import os
from uuid import uuid4

import psycopg
import pytest
import sqlalchemy.engine
from sqlalchemy import create_engine

from assetops_backend.commercial import pseudonym_key
from assetops_backend.commercial.composition import (FileKeyStore, KeyErased, create_key_file, erase_key_file,
                                                     key_state)
from assetops_backend.commercial.adapters.file_key_store import directory_ok
from assetops_backend.commercial.pseudonym import PseudonymKeyErased, PseudonymKeyMissing
from assetops_backend.database_target import PG_TARGET_ENV

ERASED_WORDS = ("This tenant's key was erased. A new key would not match the records already held; onboard the "
                "operator as a new tenant.\n")
ROOT = hasattr(os, "geteuid") and os.geteuid() == 0


def _no_connect(*_a, **_k):
    raise AssertionError("connection attempted")


@pytest.fixture(autouse=True)
def no_connect(monkeypatch):
    monkeypatch.setattr(psycopg, "connect", _no_connect)
    monkeypatch.setattr(psycopg.Connection, "connect", classmethod(_no_connect))
    monkeypatch.setattr(sqlalchemy.engine.Engine, "connect", _no_connect)
    for variable in PG_TARGET_ENV:
        monkeypatch.delenv(variable, raising=False)


def test_no_connect_fixture_holds() -> None:
    with pytest.raises(AssertionError, match="^connection attempted$"):
        create_engine("postgresql+psycopg://u:p@rc4.invalid:1/x").connect()


@pytest.fixture()
def keys(tmp_path):
    directory = tmp_path / "keys"
    directory.mkdir(mode=0o700)
    os.chmod(directory, 0o700)
    return directory


def _cli(capsys, *argv) -> tuple[int, str, str]:
    code = pseudonym_key.main(list(argv))
    out, err = capsys.readouterr()
    return code, out, err


# --- 1: erase, then never again --------------------------------------------------------------------------------------

def test_1_erase_writes_the_tombstone_and_removes_the_key(keys, capsys) -> None:
    tid = uuid4()
    create_key_file(keys, tid)
    assert _cli(capsys, "erase", "--dir", str(keys), "--tenant-id", str(tid)) == (0, "Erased.\n", "")
    tomb = keys / f"{tid}.erased"
    assert tomb.read_bytes() == b"erased\n" and tomb.stat().st_mode & 0o777 == 0o600
    assert not (keys / f"{tid}.key").exists()
    assert _cli(capsys, "erase", "--dir", str(keys), "--tenant-id", str(tid)) == (0, "Already erased.\n", "")
    before = sorted(p.name for p in keys.iterdir())
    assert _cli(capsys, "create", "--dir", str(keys), "--tenant-id", str(tid)) == (2, "", ERASED_WORDS)
    assert sorted(p.name for p in keys.iterdir()) == before


def test_1_crash_case_tombstone_and_key_both_present(keys, capsys) -> None:
    tid = uuid4()
    create_key_file(keys, tid)
    (keys / f"{tid}.erased").write_bytes(b"erased\n")
    assert _cli(capsys, "erase", "--dir", str(keys), "--tenant-id", str(tid)) == (0, "Erased.\n", "")
    assert not (keys / f"{tid}.key").exists()


def test_1_a_lost_key_is_still_erased_and_never_made_again(keys, capsys) -> None:
    tid = uuid4()
    assert _cli(capsys, "erase", "--dir", str(keys), "--tenant-id", str(tid)) == (0, "Erased.\n", "")
    assert (keys / f"{tid}.erased").exists()
    with pytest.raises(KeyErased):
        create_key_file(keys, tid)
    assert _cli(capsys, "create", "--dir", str(keys), "--tenant-id", str(tid)) == (2, "", ERASED_WORDS)
    assert not (keys / f"{tid}.key").exists()


def test_1_a_missing_directory_is_refused(tmp_path, capsys) -> None:
    code, out, err = _cli(capsys, "erase", "--dir", str(tmp_path / "none"), "--tenant-id", str(uuid4()))
    assert (code, out, err) == (2, "", "The key directory does not exist.\n")
    assert not (tmp_path / "none").exists()


# --- 2: the key store refuses every tombstone form -------------------------------------------------------------------

def _tomb(keys, tid, form: str) -> None:
    path = keys / f"{tid}.erased"
    if form == "file":
        path.write_bytes(b"erased\n")
    elif form == "symlink":
        (keys / "elsewhere").write_bytes(b"x")
        path.symlink_to(keys / "elsewhere")
    elif form == "dangling symlink":
        path.symlink_to(keys / "nothing-here")
    elif form == "mode 000":
        path.write_bytes(b"erased\n")
        os.chmod(path, 0)


FORMS = ["file", "symlink", "dangling symlink", "mode 000"]


@pytest.mark.parametrize("form", FORMS)
def test_2_the_key_store_raises_erased_with_any_tombstone(keys, form) -> None:
    if form == "mode 000" and ROOT:
        pytest.skip("root reads a mode-000 file")
    tid = uuid4()
    create_key_file(keys, tid)  # a key file still present
    _tomb(keys, tid, form)
    with pytest.raises(PseudonymKeyErased):
        FileKeyStore(keys).key(tid)


def test_2_crash_case_the_store_never_reads_a_key_beside_a_tombstone(keys) -> None:
    tid = uuid4()
    create_key_file(keys, tid)
    assert len(FileKeyStore(keys).key(tid)) == 32
    _tomb(keys, tid, "file")
    with pytest.raises(PseudonymKeyErased):
        FileKeyStore(keys).key(tid)
    other = uuid4()
    with pytest.raises(PseudonymKeyMissing):
        FileKeyStore(keys).key(other)


def test_2_crash_case_a_tombstone_that_cannot_be_written_leaves_the_key(keys, monkeypatch) -> None:
    """The tombstone comes first: if writing it fails, the key is still there (never MISSING, which would let a
    later onboarding mint a new key)."""
    tid = uuid4()
    create_key_file(keys, tid)
    real_open = os.open

    def failing_open(path, *args, **kwargs):
        if str(path).endswith(".erased"):
            raise OSError("disk full")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(os, "open", failing_open)
    with pytest.raises(OSError):
        erase_key_file(keys, tid)
    monkeypatch.setattr(os, "open", real_open)
    assert key_state(keys, tid) == "PRESENT"


# --- 3: the 3A2 upload path ------------------------------------------------------------------------------------------

def test_3_an_upload_with_an_erased_key_is_409_with_its_words(keys) -> None:
    from test_3a2_commercial_upload_service import People, b_bill, encode, make_world, refused

    from assetops_backend.i18n import render

    people = People()
    people.sign("amina")
    w = make_world(people, keys=FileKeyStore(keys))
    missing = refused(lambda: w.svc.check(w.tid, w.kobo, w.ana, encode(b_bill())))
    assert (missing.status, missing.code) == (409, "PSEUDONYM_KEY_MISSING")
    create_key_file(keys, w.tid)
    erase_key_file(keys, w.tid)
    erased = refused(lambda: w.svc.check(w.tid, w.kobo, w.ana, encode(b_bill())))
    assert (erased.status, erased.code) == (409, "PSEUDONYM_KEY_ERASED")
    assert render(erased.words, "en") == (
        "This organisation's customer identities were erased, so its exports are no longer received.")


# --- 4: key_state and directory_ok -----------------------------------------------------------------------------------

def test_4_key_state(keys) -> None:
    tid = uuid4()
    assert key_state(keys, tid) == "MISSING"
    create_key_file(keys, tid)
    assert key_state(keys, tid) == "PRESENT"
    erase_key_file(keys, tid)
    assert key_state(keys, tid) == "ERASED"


@pytest.mark.parametrize("form", ["dangling symlink", "mode 000"])
def test_4_key_state_is_erased_for_odd_tombstones(keys, form) -> None:
    tid = uuid4()
    _tomb(keys, tid, form)
    assert key_state(keys, tid) == "ERASED"


def test_4_directory_ok(tmp_path, keys) -> None:
    assert directory_ok(keys)
    assert not directory_ok(tmp_path / "none")
    (tmp_path / "a-file").write_bytes(b"")
    os.chmod(tmp_path / "a-file", 0o700)
    assert not directory_ok(tmp_path / "a-file")
    loose = tmp_path / "loose"
    loose.mkdir()
    os.chmod(loose, 0o750)
    assert not directory_ok(loose)
