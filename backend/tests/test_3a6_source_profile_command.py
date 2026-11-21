"""3A6 K1 to K4 (spec §2.7, §6 "Command, no database"; D-3A6.10, D-3A6.17): the `source_profile` command over
injected services (3A6's in-memory world and 3C1a's accounts). No URL here names a reachable database."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from assetops_backend import source_profile as command
from assetops_backend.database_target import PG_TARGET_ENV
from test_3a6_source_profiles import (KOBO_EXPECTED, KOBO_PROFILE, KOBO_SAMPLE, V1, cell, kobo_rows, make_world,
                                      people)

__all__ = ["people"]  # the module-scoped People fixture
URL = "postgresql+psycopg://u:p@rc4.invalid:1/assetops_test"


@pytest.fixture(autouse=True)
def database_url(monkeypatch):
    for variable in PG_TARGET_ENV:
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.delenv("ASSETOPS_REAL_OPERATOR_DATA", raising=False)
    monkeypatch.setenv("DATABASE_URL", URL)


@pytest.fixture()
def files(tmp_path) -> dict[str, Path]:
    out = {}
    for name, data in (("profile", KOBO_PROFILE), ("sample", KOBO_SAMPLE), ("expected", KOBO_EXPECTED)):
        out[name] = tmp_path / f"{name}.bin"
        out[name].write_bytes(data)
    return out


def run(capsys, people, world, *argv) -> tuple[int, list[dict], str]:
    code = command.main(list(argv), profiles=world.profiles, accounts=people.svc)
    out, err = capsys.readouterr()
    return code, [json.loads(line) for line in out.splitlines()], err


def three(files) -> list[str]:
    return ["--profile", str(files["profile"]), "--sample", str(files["sample"]), "--expected", str(files["expected"])]


def test_k1_check_is_admissible(capsys, people, files) -> None:
    world = make_world(people)
    code, lines, _ = run(capsys, people, world, "check", "--tenant", "acme", *three(files))
    assert code == 0 and lines[0]["state"] == "ADMISSIBLE" and lines[0]["reader"] == V1
    assert (lines[0]["version"], lines[0]["sample_rows"]) == (1, 4)
    assert world.store.profiles == []
    code, lines, _ = run(capsys, people, world, "admit", "--tenant", "acme", *three(files), "--as", "ana@acme.example")
    assert code == 0 and lines[0]["state"] == "ADMITTED" and len(world.store.profiles) == 1
    code, lines, _ = run(capsys, people, world, "admit", "--tenant", "acme", *three(files), "--as", "ana@acme.example")
    assert code == 0 and lines[0]["state"] == "ALREADY_ADMITTED" and len(world.store.profiles) == 1
    code, lines, _ = run(capsys, people, world, "check", "--tenant", "acme", *three(files))
    assert code == 0 and lines[0]["state"] == "ALREADY_ADMITTED"


def test_k2_admit_needs_the_role(capsys, people, files) -> None:
    world = make_world(people)
    code, lines, err = run(capsys, people, world, "admit", "--tenant", "acme", *three(files),
                           "--as", "peter@acme.example")
    assert (code, lines) == (2, []) and err.startswith("PERSON_ROLE_REQUIRED")
    assert world.store.profiles == []


def test_k3_refused_sample(capsys, people, files) -> None:
    def litres(n, cells):
        if n == 4:
            cells[cell("Litres")] = "4OO"
    files["sample"].write_bytes(kobo_rows(litres))
    code, lines, _ = run(capsys, people, make_world(people), "check", "--tenant", "acme", *three(files))
    assert code == 3 and lines[0]["state"] == "REFUSED" and lines[0]["code"] == "ADMIT_SAMPLE_ROW"
    assert lines[0]["text"] == ("Row 4 of the sample is refused: Litres: this value is not written the way this "
                                "layout reads it (for example, a date in another order).")
    assert "4OO" not in json.dumps(lines)


def test_k4_list_one_line_per_latest_profile(capsys, people, files) -> None:
    world = make_world(people)
    world.profiles.admit(world.tid, world.ana, KOBO_PROFILE, KOBO_SAMPLE, KOBO_EXPECTED)
    obj = json.loads(KOBO_PROFILE)
    world.profiles.admit(world.tid, world.ana, json.dumps(obj).encode(), KOBO_SAMPLE, KOBO_EXPECTED)
    code, lines, _ = run(capsys, people, world, "list", "--tenant", "acme")
    assert code == 0 and [(x["profile_id"], x["reader"], x["status"]) for x in lines] == [
        ("kobo-ledger-expenses", "profile.kobo-ledger-expenses.v2", "ILLUSTRATIVE")]
    assert lines[0]["admitted_by"] == str(world.ana.person_id)


def test_k_refusals_before_admission(capsys, people, files, monkeypatch) -> None:
    world = make_world(people)
    code, _, err = run(capsys, people, world, "list", "--tenant", "nope")
    assert code == 2 and err.startswith("TENANT_NOT_FOUND")
    code, _, err = run(capsys, people, world, "check", "--tenant", "acme", "--profile", str(files["profile"]),
                       "--sample", str(files["sample"].parent), "--expected", str(files["expected"]))
    assert code == 2 and err.startswith(f"FILE_UNREADABLE {files['sample'].parent}")
    monkeypatch.delenv("DATABASE_URL")
    code, _, err = run(capsys, people, world, "list", "--tenant", "acme")
    assert code == 2 and err.startswith("DATABASE_URL_REQUIRED")
