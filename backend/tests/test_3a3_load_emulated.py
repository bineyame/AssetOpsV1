"""3A3 L1 to L6 (spec `specs/3A3-emulators-contract-test/spec.md` §2.6 to §2.8, §5 "Loader, no database";
D-3A3.6, D-3A3.7, D-3A3.11): the emulated-export loader over injected in-memory services.

No test here can reach a database: an autouse fixture makes every psycopg and SQLAlchemy connection attempt raise
(proved by `test_no_connect_fixture_holds`), and every URL names the host `rc4.invalid`, port 1, which cannot
resolve. No URL here names a real database.

The emulator's files come from `tools/world_history.py` (`exports` and `records`) run on the fixture manifest in a
child process: product tests never import the simulator (dependency direction).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

import psycopg
import pytest
import sqlalchemy.engine
from sqlalchemy import create_engine

from assetops_backend import load_emulated_exports as loader
from assetops_backend.commercial.model import HeldUpload
from assetops_backend.commercial.service import CommercialRecords
from assetops_backend.commercial.uploads import CommercialUploads
from assetops_backend.database_target import PG_TARGET_ENV
from assetops_contracts.native import LAYOUTS, read_layout, render_layout
from test_3a1_commercial_service import Clock
from test_3a2_commercial_upload_service import KEY, T_SUBMIT, Keys, UploadMemoryStore
from test_3c1a_person_work import KISIWA, KOBO, People

TREE = Path(__file__).resolve().parents[2]
VIEW = TREE / "simulator" / "tests" / "world" / "fixtures" / "view_v1.json"
URL = "postgresql+psycopg://u:p@rc4.invalid:1/assetops_test"
KEYS = ("billing", "collections", "expenses", "budget")


def _no_connect(*_a, **_k):
    raise AssertionError("connection attempted")


@pytest.fixture(autouse=True)
def no_connect(monkeypatch):
    monkeypatch.setattr(psycopg, "connect", _no_connect)
    monkeypatch.setattr(psycopg.Connection, "connect", classmethod(_no_connect))
    monkeypatch.setattr(sqlalchemy.engine.Engine, "connect", _no_connect)
    for variable in PG_TARGET_ENV:
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setenv("DATABASE_URL", URL)


def test_no_connect_fixture_holds() -> None:
    with pytest.raises(AssertionError, match="^connection attempted$"):
        create_engine("postgresql+psycopg://u:p@rc4.invalid:1/x").connect()
    with pytest.raises(AssertionError, match="^connection attempted$"):
        psycopg.connect("host=rc4.invalid port=1 dbname=x")


# --- the in-memory world ---------------------------------------------------------------------------------------------

class HeldMemoryStore(UploadMemoryStore):
    """3A2's in-memory upload store plus spec §2.8's `held_uploads`, mirroring the adapter's query."""

    def held_uploads(self, tenant_id: UUID) -> tuple[HeldUpload, ...]:
        out = []
        for u in sorted((u for u in self.uploads if u.tenant_id == tenant_id), key=lambda u: str(u.id)):
            found = [d for d in self.decisions if d.tenant_id == tenant_id and d.upload_id == u.id]
            if found and found[0].decision != "ACCEPTED":
                continue
            out.append(HeldUpload(u.id, u.source_type, u.reader, u.file_sha256, not found))
        return tuple(out)


@pytest.fixture(scope="module")
def people() -> People:
    return People()


def world(people: People) -> SimpleNamespace:
    names = {pid: name.title() for name, pid in people.ids.items()}
    store = HeldMemoryStore(names)
    store.slugs[people.acme] = "acme"
    store.slugs[people.beta] = "beta"
    store.sites[(people.acme, KOBO.lower())] = people.kobo
    store.sites[(people.acme, KISIWA.lower())] = people.kisiwa
    clock = Clock(T_SUBMIT)
    svc = CommercialUploads(CommercialRecords(store, clock=clock), store, Keys({people.acme: KEY}), clock=clock,
                            real_data=False)
    return SimpleNamespace(store=store, svc=svc, accounts=people.svc)


@pytest.fixture()
def w(people):
    return world(people)


@pytest.fixture(scope="module")
def generated(tmp_path_factory) -> Path:
    """The emulator's files (`exports`) and DS1b's batches (`records`) for the fixture manifest."""
    out = tmp_path_factory.mktemp("generated")
    for command in ("exports", "records"):
        run = subprocess.run([sys.executable, str(TREE / "tools" / "world_history.py"), command, "--manifest",
                              str(VIEW), "--out", str(out / command)], capture_output=True, text=True, timeout=300)
        assert run.returncode == 0, run.stderr
    return out


@pytest.fixture(scope="module")
def emulated(generated) -> dict[str, list[dict]]:
    """The emulator's records for KOBO-001 and KISIWA-001 only, by key."""
    out = {}
    for key in KEYS:
        data = (generated / "exports" / f"lakeside-power.{key}.csv").read_bytes()
        read = read_layout(LAYOUTS[f"{key}-illustrative-1"], data, tenant_code="lakeside-power",
                           produced_at="2026-11-06T06:00:00+03:00", provenance="source-emulated")
        assert dict(read.refused) == {}
        out[key] = [r for r in read.obj["records"] if r.get("site_code") in (KOBO, KISIWA)]
    return out


def write_files(directory: Path, emulated: dict[str, list[dict]]) -> Path:
    directory.mkdir(exist_ok=True)
    for key in KEYS:
        (directory / f"acme.{key}.csv").write_bytes(render_layout(LAYOUTS[f"{key}-illustrative-1"], emulated[key]))
    return directory


def run(w, directory: Path, *extra: str, submit: str = "ana@acme.example", accept: str | None = "fiona@acme.example",
        capsys=None) -> tuple[int, list[dict], str]:
    argv = ["--dir", str(directory), "--tenant", "acme", "--submit-as", submit]
    if accept is not None:
        argv += ["--accept-as", accept]
    code = loader.main([*argv, *extra], uploads=w.svc, accounts=w.accounts)
    out, err = capsys.readouterr()
    return code, [json.loads(line) for line in out.splitlines()], err


class Spy:
    def __init__(self) -> None:
        self.touched: list[str] = []

    def __getattr__(self, name: str):
        self.touched.append(name)
        raise AssertionError(f"service used: {name}")


# --- L1 --------------------------------------------------------------------------------------------------------------

OPERATOR = ["postgresql+psycopg://u:p@rc4.invalid:1/assetops_op_pilot1",
            "postgresql+psycopg://u:p@rc4.invalid:1/ASSETOPS_OP_X",
            "postgresql+psycopg://u:p@rc4.invalid:1/assetops_opx"]
UNCLEAR = ["postgresql+psycopg://u:p@rc4.invalid:1/assetops_test?dbname=assetops_op_x",
           "postgresql+psycopg://u:p@rc4.invalid:1/?dbname=assetops_op_x",
           "postgresql+psycopg://u:p@rc4.invalid:1/",
           "postgresql+psycopg://u:p@rc4.invalid:1/assetops_test?service=x"]


@pytest.mark.parametrize("url,code", [(u, "EMULATED_ON_OPERATOR_DATABASE") for u in OPERATOR]
                         + [(u, "DATABASE_URL_UNCLEAR") for u in UNCLEAR],
                         ids=["op_pilot1", "OP_X", "opx", "query-dbname", "slash-query-dbname", "empty-name",
                              "service"])
def test_l1_operator_or_unclear_database_refused_before_anything(tmp_path, monkeypatch, capsys, url, code) -> None:
    monkeypatch.setenv("DATABASE_URL", url)
    uploads, accounts = Spy(), Spy()
    result = loader.main(["--dir", str(tmp_path), "--tenant", "acme", "--submit-as", "ana@acme.example"],
                         uploads=uploads, accounts=accounts)
    err = capsys.readouterr().err
    assert result == 2 and err.startswith(code + " ")
    assert uploads.touched == [] and accounts.touched == []
    if code == "EMULATED_ON_OPERATOR_DATABASE":
        assert err.strip() == ("EMULATED_ON_OPERATOR_DATABASE Emulated exports are never loaded into an operator's "
                               "database.")


def test_l1_pgdatabase_in_the_environment_is_unclear(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("PGDATABASE", "assetops_op_x")
    uploads, accounts = Spy(), Spy()
    result = loader.main(["--dir", str(tmp_path), "--tenant", "acme", "--submit-as", "ana@acme.example"],
                         uploads=uploads, accounts=accounts)
    assert result == 2 and capsys.readouterr().err.startswith("DATABASE_URL_UNCLEAR ENVIRONMENT PGDATABASE ")
    assert uploads.touched == [] and accounts.touched == []


def test_l1_database_url_required(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.delenv("DATABASE_URL")
    assert loader.main(["--dir", str(tmp_path), "--tenant", "acme", "--submit-as", "a@b.c"],
                       uploads=Spy(), accounts=Spy()) == 2
    assert capsys.readouterr().err.startswith("DATABASE_URL_REQUIRED ")


# --- L2, L6 ----------------------------------------------------------------------------------------------------------

def test_l2_load_accept_and_rerun(w, tmp_path, emulated, capsys) -> None:
    directory = write_files(tmp_path / "x", emulated)
    code, lines, err = run(w, directory, capsys=capsys)
    assert code == 0, err
    assert [(l["file"], l["state"], l.get("decided_by_script")) for l in lines] == [
        (f"acme.{k}.csv", "ACCEPTED", True) for k in KEYS]
    assert [l["counts"]["refused"] for l in lines] == [0, 0, 0, 0]
    assert len(w.store.uploads) == 4 and len(w.store.decisions) == 4
    assert {d.decided_by for d in w.store.decisions} == {w.accounts.onboard_person("fiona@acme.example").person_id}
    assert len(w.store.revisions) == sum(len(emulated[k]) for k in KEYS)
    code, lines, _ = run(w, directory, capsys=capsys)
    assert code == 0 and [l["state"] for l in lines] == ["NOTHING_NEW"] * 4
    assert len(w.store.uploads) == 4


def test_l6_without_accept_then_already_waiting_then_decided(w, tmp_path, emulated, capsys) -> None:
    directory = write_files(tmp_path / "x", emulated)
    code, first, _ = run(w, directory, accept=None, capsys=capsys)
    assert code == 0 and [l["state"] for l in first] == ["WAITING"] * 4
    assert all("decided_by_script" not in l for l in first)
    code, again, _ = run(w, directory, accept=None, capsys=capsys)
    assert code == 0 and [l["state"] for l in again] == ["ALREADY_WAITING"] * 4
    assert [l["upload_id"] for l in again] == [l["upload_id"] for l in first]
    assert len(w.store.uploads) == 4
    code, decided, _ = run(w, directory, capsys=capsys)
    assert code == 0 and [(l["state"], l["decided_by_script"]) for l in decided] == [("ACCEPTED", True)] * 4
    assert [l["upload_id"] for l in decided] == [l["upload_id"] for l in first]
    assert len(w.store.uploads) == 4 and len(w.store.decisions) == 4


# --- L3 to L5 --------------------------------------------------------------------------------------------------------

def test_l3_unknown_file(w, tmp_path, emulated, capsys) -> None:
    directory = write_files(tmp_path / "x", emulated)
    (directory / "notes.txt").write_text("x")
    code, lines, err = run(w, directory, capsys=capsys)
    assert (code, lines) == (2, []) and err.startswith("EXPORT_FILE_UNKNOWN notes.txt ")
    assert w.store.uploads == []


def test_l3_paths_mixed(w, tmp_path, emulated, capsys) -> None:
    directory = write_files(tmp_path / "x", emulated)
    (directory / "acme.budget_workbook.json").write_bytes(b"{}")
    code, lines, err = run(w, directory, capsys=capsys)
    assert (code, lines) == (2, []) and err.startswith("EXPORT_PATHS_MIXED budget_workbook ")


@pytest.mark.parametrize("submit,accept,code", [
    ("hugo@beta.example", "fiona@acme.example", "PERSON_NOT_FOUND"),
    ("nobody@acme.example", None, "PERSON_NOT_FOUND"),
    ("peter@acme.example", "fiona@acme.example", "PERSON_ROLE_REQUIRED"),
    ("ana@acme.example", "ana@acme.example", "PERSON_ROLE_REQUIRED"),
    ("fiona@acme.example", "fiona@acme.example", "PERSON_SAME_FOR_BOTH"),
], ids=["other-tenant", "unknown", "site-manager-submits", "analyst-accepts", "same-for-both"])
def test_l3_people(w, tmp_path, emulated, capsys, submit, accept, code) -> None:
    directory = write_files(tmp_path / "x", emulated)
    result, lines, err = run(w, directory, submit=submit, accept=accept, capsys=capsys)
    assert (result, lines) == (2, []) and err.startswith(code + " ")
    assert w.store.uploads == []


def test_l4_refused_submission_exits_3_after_earlier_files(w, tmp_path, emulated, capsys) -> None:
    directory = write_files(tmp_path / "x", emulated)
    budget = directory / "acme.budget.csv"
    rows = budget.read_text(encoding="utf-8").split("\n")
    header = rows[0].split(",")
    rows[0] = ",".join([header[1], header[0], *header[2:]])
    budget.write_text("\n".join(rows), encoding="utf-8")
    code, lines, err = run(w, directory, capsys=capsys)
    assert code == 3 and err.startswith("UPLOAD_FILE_REFUSED ")
    assert [(l["file"], l["state"]) for l in lines] == [(f"acme.{k}.csv", "ACCEPTED") for k in KEYS[:3]]
    assert len(w.store.uploads) == 3


def test_l5_path_switched_across_runs(w, tmp_path, emulated, generated, capsys) -> None:
    assert run(w, write_files(tmp_path / "x", emulated), capsys=capsys)[0] == 0
    batch = (generated / "records" / "lakeside-power.budget_workbook.json").read_bytes()  # a DS1b batch
    other = tmp_path / "y"
    other.mkdir()
    (other / "acme.budget_workbook.json").write_bytes(batch)
    before = len(w.store.uploads)
    code, lines, err = run(w, other, capsys=capsys)
    assert (code, lines) == (2, []) and err.startswith("EXPORT_PATH_SWITCHED budget_workbook ")
    assert len(w.store.uploads) == before


def test_parser_is_public() -> None:
    args = loader.build_parser().parse_args(["--dir", "d", "--tenant", "acme", "--submit-as", "a@b.c"])
    assert (str(args.dir), args.tenant, args.submit_as, args.accept_as) == ("d", "acme", "a@b.c", None)


def test_environment_untouched() -> None:
    assert os.environ["DATABASE_URL"] == URL
