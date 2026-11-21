"""DS3 (spec `specs/DS3-bulk-loader/spec.md` §4 tests 1 to 3): the permitted-database rule, the world command's
refusals and output with injected fakes, and the bulk path's seams. No database is touched here."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import pytest

from assetops_backend import load_world_inputs
from assetops_backend.evidence import bulk_load
from assetops_backend.evidence.adapters import postgres_evidence_ledger as adapter
from assetops_backend.evidence.bulk_load import BulkLoaded, permitted_database

BACKEND = Path(__file__).resolve().parents[1]
PACKAGE = BACKEND / "assetops_backend"
HOST = "postgresql+psycopg://u:p@127.0.0.1:55432"


# --- test 1: permitted_database ---------------------------------------------------------------------------------


@pytest.mark.parametrize(("url", "environ", "expected"), [
    (f"{HOST}/assetops_test", {}, True),
    (f"{HOST}/assetops_pt1a_ds3bulk_test", {}, True),
    (f"{HOST}/assetops_ds3_audit1121", {}, True),
    (f"{HOST}/assetops_ds4_audit1125", {}, True),
    (f"{HOST}/assetops_polish_walk1113", {}, False),
    (f"{HOST}/assetops_op_kobo", {}, False),
    (f"{HOST}/assetops_op_kobo_test", {}, False),
    (f"{HOST}/_audit", {}, False),
    (f"{HOST}/assetops_testbed", {}, False),  # contains "test" without the suffix
    (f"{HOST}/assetops_test?dbname=assetops_op_kobo", {}, False),
    ("postgresql+psycopg://u:p@10.0.0.5:55432/assetops_test", {}, False),
    ("postgresql+psycopg://u:p@127.0.0.1:5432/assetops_test", {}, False),
    ("postgresql+psycopg://u:p@127.0.0.1/assetops_test", {}, False),
    ("postgresql+psycopg://u:p@127.0.0.1:55433/assetops_test", {"ASSETOPS_PG_PORT": "55433"}, True),
])
def test_permitted_database(url, environ, expected) -> None:
    assert permitted_database(url, environ) is expected


# --- test 2: the world command ------------------------------------------------------------------------------------


class Stub:
    def __init__(self, code: int = 0) -> None:
        self.code = code
        self.calls: list[list[str]] = []

    def __call__(self, argv) -> int:
        self.calls.append(list(argv))
        return self.code


class FakeLoad:
    loads: list[int] = []

    def __init__(self, ledger) -> None:
        self.ledger = ledger

    def load(self, raws):
        FakeLoad.loads.append(len(raws))
        return BulkLoaded(len(raws), 0, 10 * len(raws))


@pytest.fixture()
def world(tmp_path, monkeypatch):
    """Two tenants: `alpha` with both folders, `beta` with telemetry only. The real ledger class is replaced by one
    that records construction, so a refusal can prove no ledger was built."""
    for slug, parts in (("alpha", ("commercial", "telemetry")), ("beta", ("telemetry",))):
        for part in parts:
            (tmp_path / slug / part).mkdir(parents=True)
    for name in ("b.batch.json", "a.batch.json"):
        (tmp_path / "alpha" / "telemetry" / name).write_bytes(b"{}")
    (tmp_path / "beta" / "telemetry" / "c.batch.json").write_bytes(b"{}")
    built: list[str] = []

    class Ledger:
        def __init__(self, url) -> None:
            built.append(url)

    monkeypatch.setattr(adapter, "PostgresEvidenceLedger", Ledger)
    monkeypatch.setattr(bulk_load, "BulkEvidenceLoad", FakeLoad)
    FakeLoad.loads = []
    monkeypatch.setenv("DATABASE_URL", f"{HOST}/assetops_ds3_audit1121")
    for variable in ("PGDATABASE", "PGHOST", "PGHOSTADDR", "PGPORT", "PGSERVICE", "PGSERVICEFILE", "ASSETOPS_PG_PORT"):
        monkeypatch.delenv(variable, raising=False)
    return tmp_path, built


def run(world_dir, stub, *extra) -> int:
    return load_world_inputs.main(["--world", str(world_dir), "--submit-as", "s@x", "--accept-as", "a@x", *extra],
                                  load_exports=stub)


def test_no_database_is_refused(world, monkeypatch, capsys) -> None:
    path, built = world
    monkeypatch.delenv("DATABASE_URL")
    assert run(path, Stub()) == 2
    assert capsys.readouterr().err.startswith("NO_DATABASE - ")
    assert built == []


def test_a_database_not_permitted_is_refused_before_a_ledger_is_built(world, monkeypatch, capsys) -> None:
    path, built = world
    monkeypatch.setenv("DATABASE_URL", f"{HOST}/assetops_polish_walk1113")
    stub = Stub()
    assert run(path, stub) == 2
    assert capsys.readouterr().err.startswith("BULK_DATABASE_NOT_PERMITTED - ")
    assert built == [] and stub.calls == [] and FakeLoad.loads == []


def test_a_stray_file_in_a_tenant_directory_is_refused_before_a_ledger_is_built(world, capsys) -> None:
    path, built = world
    (path / "beta" / "notes.txt").write_text("x")
    stub = Stub()
    assert run(path, stub) == 2
    assert capsys.readouterr().err.startswith("WORLD_LAYOUT_UNKNOWN - ")
    assert built == [] and stub.calls == [] and FakeLoad.loads == []


def test_a_failed_commercial_step_exits_4_and_loads_no_telemetry(world, capsys) -> None:
    path, _ = world
    stub = Stub(3)
    assert run(path, stub) == 4
    err = capsys.readouterr().err
    assert err.rstrip("\n").endswith("COMMERCIAL_EXIT alpha 3")
    assert FakeLoad.loads == [] and len(stub.calls) == 1


def test_success_passes_the_commercial_folder_and_prints_one_line_per_tenant(world, capsys) -> None:
    path, built = world
    stub = Stub(0)
    assert run(path, stub) == 0
    assert stub.calls == [["--dir", str(path / "alpha" / "commercial"), "--tenant", "alpha", "--submit-as", "s@x",
                           "--accept-as", "a@x"]]
    lines = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert [set(line) for line in lines] == [{"tenant", "commercial_exit", "batches", "already_loaded", "envelopes"}] * 2
    assert lines == [
        {"tenant": "alpha", "commercial_exit": 0, "batches": 2, "already_loaded": 0, "envelopes": 20},
        {"tenant": "beta", "commercial_exit": None, "batches": 1, "already_loaded": 0, "envelopes": 10},
    ]
    assert FakeLoad.loads == [2, 1] and len(built) == 1


def test_a_tenant_with_telemetry_only_does_not_call_the_commercial_loader(world, capsys) -> None:
    path, _ = world
    stub = Stub(0)
    assert run(path, stub, "--tenant", "beta") == 0
    assert stub.calls == []
    [line] = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert line["tenant"] == "beta" and line["commercial_exit"] is None


# --- test 3: seams --------------------------------------------------------------------------------------------


def _modules():
    return sorted(PACKAGE.rglob("*.py"))


def _imports(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
            names.update(f"{node.module}.{alias.name}" for alias in node.names)
    return names


def test_bulk_admit_has_one_caller_and_no_http_module_reaches_the_bulk_path() -> None:
    callers = set()
    for path in _modules():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "bulk_admit":
                callers.add(path.relative_to(PACKAGE).as_posix())
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "bulk_admit":
                callers.add(path.relative_to(PACKAGE).as_posix())
        if path.name == "main.py" or path.name.endswith("_api.py"):
            reached = {n for n in _imports(tree) if re.search(r"(?:^|\.)(?:bulk_load|load_world_inputs)(?:\.|$)", n)}
            assert not reached, f"{path.relative_to(PACKAGE)} imports {sorted(reached)}"
    assert callers == {"evidence/bulk_load.py"}


def test_the_bulk_service_imports_no_simulator_host_or_commercial_module() -> None:
    names = _imports(ast.parse((PACKAGE / "evidence" / "bulk_load.py").read_text(encoding="utf-8")))
    bad = {n for n in names if n.startswith("simulator") or re.search(r"(?:^|\.)(?:host|commercial)(?:\.|_|$)", n)}
    assert not bad, sorted(bad)


def _string_constants(tree: ast.AST) -> list[str]:
    return [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def test_the_bulk_statements_target_only_the_ledger_input_tables_and_never_copy_or_upsert() -> None:
    statements = {name: getattr(adapter, name).text for name in ("_BULK_BATCH_SQL", "_BULK_EVIDENCE_SQL",
                                                                 "_BULK_DISPOSITION_SQL")}
    targets = {t.lower() for sql in statements.values() for t in re.findall(r"(?i)\b(?:INTO|UPDATE)\s+([a-z_]+)", sql)}
    assert targets and targets <= {"ingestion_batch", "accepted_evidence", "ingestion_disposition"}
    for name, sql in statements.items():
        assert not re.search(r"(?i)\b(?:COPY|MERGE|CREATE|TRUNCATE)\b|\bDO\s+UPDATE\b", sql), name
    # No COPY anywhere in the ledger writer, whatever constant it hides in.
    tree = ast.parse(Path(adapter.__file__).read_text(encoding="utf-8"))
    assert not [s for s in _string_constants(tree) if re.match(r"(?i)\s*COPY\s", s)]


def test_the_bulk_evidence_columns_are_persists_columns_in_order() -> None:
    tree = ast.parse(Path(adapter.__file__).read_text(encoding="utf-8"))
    persist = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_persist")
    persist_sql = "".join(_string_constants(persist))
    columns = re.compile(r"INSERT INTO accepted_evidence \(([^)]*)\)")
    [persist_columns] = columns.findall(persist_sql)
    [bulk_columns] = columns.findall(adapter._BULK_EVIDENCE_SQL.text)

    def split(text: str) -> list[str]:
        return [c.strip() for c in text.split(",")]

    assert split(bulk_columns) == split(persist_columns) and len(split(persist_columns)) == 42


class _Persisting:
    """A fake connection that captures `_persist`'s accepted_evidence INSERT and its parameters."""

    def __init__(self) -> None:
        self.sql, self.params = None, None

    def begin_nested(self):
        return type("Savepoint", (), {"commit": lambda s: None, "rollback": lambda s: None})()

    def execute(self, statement, params):
        self.sql, self.params = statement.text, params
        return type("Result", (), {"first": lambda s: ("inserted",)})()


def _bindings_of(sql: str) -> dict[str, tuple[str, str]]:
    """column -> ("scalar", param) or ("array", param), read from the statement text itself."""
    columns = [c.strip() for c in re.search(r"INSERT INTO accepted_evidence \(([^)]*)\)", sql).group(1).split(",")]
    values = re.search(r"\bVALUES \((.*?)\) ON CONFLICT", sql)
    if values:
        return {c: ("scalar", v.strip()[1:]) for c, v in zip(columns, values.group(1).split(","))}
    select = re.search(r"\bSELECT (.*?) FROM unnest\((.*)\) AS s\(([^)]*)\)", sql)
    expressions = [e.strip() for e in select.group(1).split(", ")]
    arrays = re.findall(r"CAST\(:(\w+) AS \w+\[\]\)", select.group(2))
    aliases = [a.strip() for a in select.group(3).split(",")]
    by_alias = dict(zip(aliases, arrays))
    out = {}
    for column, expression in zip(columns, expressions):
        scalar = re.fullmatch(r"CAST\(:(\w+) AS \w+\)", expression)
        out[column] = ("scalar", scalar.group(1)) if scalar else ("array", by_alias[expression[2:]])
    return out


def test_the_bulk_statement_binds_what_persist_binds_column_by_column() -> None:
    """Reviewer guide item 2 as a test: one decision whose every field is distinct, bound by `_persist` and by the bulk
    builder; each of the 42 columns (the generated id apart) receives the same value. Test 8's Kobo fixtures are all
    IDENTITY conversions, so a swap of value and normalized value (P1) or of two v4 ids (P15) shows here."""
    from types import SimpleNamespace as N

    envelope = N(message_id="m", sequence_epoch="ep", sequence=7, device_id="dev", signal_id="sig", family="fam",
                 measurement="meas", quality="q", unavailable_reason="ur", value="raw-value", unit="raw-unit",
                 record_kind="rk", event_id="eid", correlation_id="cid", session_id="sess", connector_id="conn",
                 actor="act", outcome="out")
    decision = N(ordinal=3, envelope=envelope, envelope_text="body", envelope_sha256="sha",
                 binding=N(asset_id="asset", role="role", binding_revision_id="brev"),
                 normalized_value_text="normalized-value", normalized_unit="norm-unit", conversion_kind="ck",
                 source_time="st", published_at="pub", interval_start="is", interval_end="ie",
                 configuration_outdated="outdated")
    batch = N(tenant_id="t", site_id="site", id="batch", gateway_id="g", source_id="src", received_at="recv",
              foundation_revision_id="f", binding_set_revision_id="bs", source_mode="mode")
    fake = _Persisting()
    adapter.PostgresEvidenceLedger._persist(None, fake, batch, decision, "decided")
    persisted = {column: fake.params[param] for column, (_, param) in _bindings_of(fake.sql).items()}
    params = adapter._bulk_evidence_params("t", "site", "batch", "g", "src", "recv",
                                           N(foundation_revision_id="f", binding_set_revision_id="bs"), "mode",
                                           [decision], ["new-id"])
    bulk = {column: params[param] if kind == "scalar" else params[param][0]
            for column, (kind, param) in _bindings_of(adapter._BULK_EVIDENCE_SQL.text).items()}
    assert set(bulk) == set(persisted) and len(bulk) == 42
    differing = {c: (persisted[c], bulk[c]) for c in persisted if c != "id" and persisted[c] != bulk[c]}
    assert differing == {}
    assert len({v for c, v in persisted.items() if c != "id"}) == 41  # every field distinct: a swap cannot hide
