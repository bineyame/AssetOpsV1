"""DD5a unit 3 (spec §4.6 as amended by D-DD.139 and D-DD.140): `load_world_inputs` seals each tenant's
`telemetry/*.readings.json` into `<slug>/sealed/` once and loads the sealed batches. The Site's binding snapshot is
resolved by an injected resolver here (the database resolver is `test_dd5a_load_world_postgres.py`); the bulk load is
a recording fake. No database."""
from __future__ import annotations

import json
from dataclasses import replace

import pytest
from test_dd5a_world_seal import _context

from assetops_backend import load_world_inputs
from assetops_backend.evidence import bulk_load, composition
from assetops_backend.evidence.bulk_load import BulkLoaded
from assetops_backend.evidence.world_seal import WorldSealRefused

HOST = "postgresql+psycopg://u:p@127.0.0.1:55432"
DIGEST = "d" * 64


class FakeLoad:
    raws: list[list[bytes]] = []

    def __init__(self, ledger) -> None:
        self.ledger = ledger

    def load(self, raws):
        FakeLoad.raws.append(list(raws))
        return BulkLoaded(len(raws), 0, sum(len(json.loads(r)["envelopes"]) for r in raws))


def _readings(code: str, day: str, n: int) -> bytes:
    rows = [{"source_id": "chamber-probe", "signal_id": "temperature", "start": f"{day}T{h:02d}:00:00+03:00",
             "end": f"{day}T{h:02d}:00:00+03:00", "value": "4.000", "unit": "degC"} for h in range(n)]
    return json.dumps({"day": day, "role_set": "cold-roles-1", "schema": "assetops.world-readings/1",
                       "site_code": code, "timezone": "Africa/Nairobi", "readings": rows}).encode()


class Resolver:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def __call__(self, slug, code, start, end, foundation_digest):
        self.calls.append((slug, code, start, end, foundation_digest))
        if code != "COLD-X":
            raise WorldSealRefused("WORLD_TELEMETRY_UNRESOLVED", f"site {code}")
        return replace(_context(), foundation_digest=foundation_digest)


@pytest.fixture()
def world(tmp_path, monkeypatch):
    telemetry = tmp_path / "alpha" / "telemetry"
    telemetry.mkdir(parents=True)
    for day, n in (("2026-10-12", 3), ("2026-10-13", 2)):
        (telemetry / f"COLD-X.{day}.readings.json").write_bytes(_readings("COLD-X", day, n))
    (tmp_path / "site-inputs.json").write_text(json.dumps(
        {"sites": [{"tenant": "alpha", "code": "COLD-X", "foundation_digest": DIGEST}]}))

    class Ledger:
        def __init__(self, url) -> None:
            pass

    monkeypatch.setattr(composition, "PostgresEvidenceLedger", Ledger)
    monkeypatch.setattr(bulk_load, "BulkEvidenceLoad", FakeLoad)
    FakeLoad.raws = []
    monkeypatch.setenv("DATABASE_URL", f"{HOST}/assetops_dd5a_audit1123")
    for variable in ("PGDATABASE", "PGHOST", "PGHOSTADDR", "PGPORT", "PGSERVICE", "PGSERVICEFILE", "ASSETOPS_PG_PORT"):
        monkeypatch.delenv(variable, raising=False)
    return tmp_path


def run(path, resolver) -> int:
    return load_world_inputs.main(["--world", str(path), "--submit-as", "s@x", "--accept-as", "a@x"],
                                  seal_context=resolver)


def _sealed(path) -> dict[str, tuple[bytes, int]]:
    (folder,) = (path / "alpha" / "sealed").iterdir()
    return {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in sorted(folder.iterdir())}


def test_readings_are_sealed_beside_the_inputs_and_the_sealed_batches_load(world, capsys) -> None:
    resolver = Resolver()
    assert run(world, resolver) == 0
    line = json.loads(capsys.readouterr().out)
    assert (line["readings_files"], line["sealed_batches"], line["envelopes"]) == (2, 2, 5)
    sealed = _sealed(world)
    assert sorted(sealed) == [f"COLD-X.{_context().bindings[('chamber-probe', 'temperature')]['source_id']}."
                              f"{d}.1.batch.json" for d in ("2026-10-12", "2026-10-13")]
    assert FakeLoad.raws == [[sealed[n][0] for n in sorted(sealed)]]
    (call,) = resolver.calls
    assert call[:2] == ("alpha", "COLD-X") and call[4] == DIGEST
    assert (call[2].isoformat(), call[3].isoformat()) == ("2026-10-12T00:00:00+03:00", "2026-10-13T01:00:00+03:00")


def test_a_rerun_writes_no_new_sealed_bytes(world, capsys) -> None:
    assert run(world, Resolver()) == 0
    first = _sealed(world)
    assert run(world, Resolver()) == 0
    assert _sealed(world) == first
    assert FakeLoad.raws[0] == FakeLoad.raws[1]


def test_a_changed_sealed_byte_refuses_and_loads_nothing(world, capsys) -> None:
    assert run(world, Resolver()) == 0
    capsys.readouterr()
    name = sorted(_sealed(world))[0]
    target = next((world / "alpha" / "sealed").iterdir()) / name
    body = bytearray(target.read_bytes())
    body[len(body) // 2] ^= 1  # one byte changed
    target.write_bytes(bytes(body))
    assert run(world, Resolver()) == 2
    assert capsys.readouterr().err.startswith(f"WORLD_SEALED_BYTES_DIFFER {name} ")
    assert len(FakeLoad.raws) == 1


def test_an_unknown_site_refuses_with_exit_2_naming_the_file(world, capsys) -> None:
    telemetry = world / "alpha" / "telemetry"
    (telemetry / "NOPE.2026-10-12.readings.json").write_bytes(_readings("NOPE", "2026-10-12", 1))
    json_path = world / "site-inputs.json"
    data = json.loads(json_path.read_text())
    data["sites"].append({"tenant": "alpha", "code": "NOPE", "foundation_digest": DIGEST})
    json_path.write_text(json.dumps(data))
    assert run(world, Resolver()) == 2
    assert capsys.readouterr().err == "WORLD_TELEMETRY_UNRESOLVED NOPE.2026-10-12.readings.json site NOPE\n"
    assert FakeLoad.raws == [] and not (world / "alpha" / "sealed").exists()


def test_a_site_missing_from_the_site_inputs_refuses(world, capsys) -> None:
    (world / "site-inputs.json").write_text(json.dumps({"sites": []}))
    assert run(world, Resolver()) == 2
    assert capsys.readouterr().err.startswith("WORLD_TELEMETRY_UNRESOLVED COLD-X.2026-10-12.readings.json ")


def test_staged_sealed_and_disorder_folders_are_accepted(world, capsys) -> None:
    for part in ("staged", "sealed", "disorder"):
        (world / "alpha" / part).mkdir(exist_ok=True)
    assert run(world, Resolver()) == 0


# --- DD5a fix round: D-DD.167 (sealed/ keyed per database), L1, L2, L3 --------------------------------------------------

def _folders(path) -> list[str]:
    return sorted(p.name for p in (path / "alpha" / "sealed").iterdir())


class OtherDatabase(Resolver):
    """A rebuilt database: the same Site and inputs under new binding ids."""

    def __call__(self, slug, code, start, end, foundation_digest):
        context = super().__call__(slug, code, start, end, foundation_digest)
        source = "99999999-9999-4999-8999-999999999999"
        return replace(context, binding_set_id="88888888-8888-4888-8888-888888888888",
                       bindings={k: {**v, "source_id": source} for k, v in context.bindings.items()})


def test_a_fresh_database_on_unchanged_inputs_writes_a_new_context_folder_and_exits_0(world, capsys) -> None:
    assert run(world, Resolver()) == 0
    (first,) = _folders(world)
    before = {p.name: p.read_bytes() for p in (world / "alpha" / "sealed" / first).iterdir()}
    assert len(first) == 12 and int(first, 16) >= 0
    assert run(world, OtherDatabase()) == 0
    capsys.readouterr()
    assert len(_folders(world)) == 2
    assert {p.name: p.read_bytes() for p in (world / "alpha" / "sealed" / first).iterdir()} == before


def test_the_output_line_carries_sealed_dir_as_slug_sealed_context12(world, capsys) -> None:
    assert run(world, Resolver()) == 0
    line = json.loads(capsys.readouterr().out)
    (folder,) = _folders(world)
    assert line["sealed_dir"] == f"alpha/sealed/{folder}/"


def test_the_same_database_rerun_uses_the_same_folder_and_writes_no_new_bytes(world) -> None:
    assert run(world, Resolver()) == 0
    (folder,) = _folders(world)
    stamps = {p.name: p.stat().st_mtime_ns for p in (world / "alpha" / "sealed" / folder).iterdir()}
    assert run(world, Resolver()) == 0
    assert _folders(world) == [folder]
    assert {p.name: p.stat().st_mtime_ns for p in (world / "alpha" / "sealed" / folder).iterdir()} == stamps


def test_a_stray_file_in_the_context_folder_refuses_stray(world, capsys) -> None:
    assert run(world, Resolver()) == 0
    capsys.readouterr()
    (folder,) = _folders(world)
    (world / "alpha" / "sealed" / folder / "COLD-X.stray.2026-10-12.1.batch.json").write_text("{}")
    assert run(world, Resolver()) == 2
    assert " stray" in capsys.readouterr().err


def test_a_row_refusal_names_the_file_that_holds_the_row(world, capsys) -> None:
    path = world / "alpha" / "telemetry" / "COLD-X.2026-10-13.readings.json"
    document = json.loads(path.read_bytes())
    document["readings"][0]["source_id"] = "ghost"
    path.write_text(json.dumps(document))
    assert run(world, Resolver()) == 2
    assert capsys.readouterr().err.startswith("WORLD_TELEMETRY_UNRESOLVED COLD-X.2026-10-13.readings.json ")


def test_a_contract_rejection_exits_2_with_a_named_code_and_its_file(world, capsys) -> None:
    path = world / "alpha" / "telemetry" / "COLD-X.2026-10-13.readings.json"
    document = json.loads(path.read_bytes())
    document["readings"][0]["value"] = "1.5E3"
    document["readings"][0]["event"] = {"record_kind": "COLD_DOOR", "outcome": "OPEN", "actor": "x", "component_id": "c",
                                        "ordinal": 1, "correlation": ["door", 1], "session_id": None}
    path.write_text(json.dumps(document))
    code = run(world, Resolver())
    err = capsys.readouterr().err
    assert code == 2 and err.startswith("WORLD_") and "COLD-X.2026-10-13.readings.json" in err, err
