"""3A3 S1 (spec §2.1, §5; D-3A3.1, D-3A3.12): one writer of commercial records.

An AST scan of `backend/assetops_backend`, `tools`, `host`, `simulator`, `gateway` and `field` (tests excluded):

- `CommercialRecords(` is called only in `commercial/composition.py`;
- in a module that imports from `assetops_backend.commercial`, other than `commercial/uploads.py` and
  `commercial/service.py`, any `.ingest` attribute (called or not) and any `getattr(<x>, "ingest")` fail;
- an import of the name `CommercialRecords` (aliased or not) outside `commercial/composition.py` and
  `commercial/uploads.py` fails;
- `build_commercial_uploads(` is called only in `main.py` and `load_emulated_exports.py` (a new caller is a reviewed
  change to `BUILD_CALLERS` and must call `refuse_operator_database` first unless it is the app);
- `build_commercial_records` exists nowhere.

Not seen (D-3A3.12, residual): `importlib` or names built from strings, and a module that receives a records service
without importing the package.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

TREE = Path(__file__).resolve().parents[2]
ROOTS = ("backend/assetops_backend", "tools", "host", "simulator", "gateway", "field")
BACKEND = "backend/assetops_backend/"
CONSTRUCTORS = {BACKEND + "commercial/composition.py"}
INGEST_ALLOWED = {BACKEND + "commercial/uploads.py", BACKEND + "commercial/service.py"}
IMPORT_ALLOWED = {BACKEND + "commercial/composition.py", BACKEND + "commercial/uploads.py"}
BUILD_CALLERS = {BACKEND + "main.py", BACKEND + "load_emulated_exports.py"}
PACKAGE = "assetops_backend.commercial"


def _imports_package(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and (node.module == PACKAGE
                                                                 or node.module.startswith(PACKAGE + ".")):
            return True
        if isinstance(node, ast.Import) and any(a.name == PACKAGE or a.name.startswith(PACKAGE + ".")
                                                for a in node.names):
            return True
    return False


def _called(node: ast.Call) -> str | None:
    f = node.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return None


def violations(rel: str, source: str) -> list[str]:
    tree = ast.parse(source)
    found: list[str] = []
    if "build_commercial_records" in source:
        found.append(f"{rel}: build_commercial_records")
    in_package = _imports_package(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = _called(node)
            if name == "CommercialRecords" and rel not in CONSTRUCTORS:
                found.append(f"{rel}:{node.lineno}: CommercialRecords(")
            if name == "build_commercial_uploads" and rel not in BUILD_CALLERS:
                found.append(f"{rel}:{node.lineno}: build_commercial_uploads(")
            if (in_package and rel not in INGEST_ALLOWED and name == "getattr" and len(node.args) >= 2
                    and isinstance(node.args[1], ast.Constant) and node.args[1].value == "ingest"):
                found.append(f"{rel}:{node.lineno}: getattr ingest")
        elif isinstance(node, ast.Attribute):
            if node.attr == "ingest" and in_package and rel not in INGEST_ALLOWED:
                found.append(f"{rel}:{node.lineno}: .ingest")
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name.rsplit(".", 1)[-1] for a in node.names]
            if "CommercialRecords" in names and rel not in IMPORT_ALLOWED:
                found.append(f"{rel}:{node.lineno}: import CommercialRecords")
            if "build_commercial_uploads" in names and rel not in BUILD_CALLERS:
                found.append(f"{rel}:{node.lineno}: import build_commercial_uploads")
    return found


def _scanned() -> list[tuple[str, Path]]:
    out = []
    for root in ROOTS:
        for path in sorted((TREE / root).rglob("*.py")):
            rel = path.relative_to(TREE).as_posix()
            parts = rel.split("/")
            if "tests" in parts or parts[-1].startswith("test_") or "node_modules" in parts:
                continue
            out.append((rel, path))
    return out


def test_s1_one_writer_of_commercial_records() -> None:
    scanned = _scanned()
    assert len(scanned) > 100 and any(rel == BACKEND + "commercial/uploads.py" for rel, _ in scanned)
    found = [v for rel, path in scanned for v in violations(rel, path.read_text(encoding="utf-8"))]
    assert found == []


def test_s1_the_allowed_callers_exist() -> None:
    scanned = {rel: path.read_text(encoding="utf-8") for rel, path in _scanned()}
    for rel in BUILD_CALLERS:
        assert "build_commercial_uploads(" in scanned[rel], rel
    assert "CommercialRecords(" in scanned[BACKEND + "commercial/composition.py"]


PLANTED = {
    "alias": "from assetops_backend.commercial.service import CommercialRecords as CR\nCR(store, clock=now)\n",
    "getattr": ("from assetops_backend.commercial import composition\n"
                "getattr(svc, \"ingest\")(tenant, data)\n"),
    "bound": "from assetops_backend.commercial import composition\nr = svc.ingest\nr(tenant, data)\n",
    "call": "from assetops_backend.commercial import composition\nsvc.ingest(tenant, data)\n",
    "construct": "from assetops_backend.commercial.composition import FileKeyStore\nCommercialRecords(store)\n",
    "builder": "from assetops_backend.commercial.composition import build_commercial_uploads as b\n"
               "build_commercial_uploads(url, settings)\n",
    "builder-alias": "from assetops_backend.commercial.composition import build_commercial_uploads as b\n"
                     "b(url, settings)\n",
    "deleted": "def build_commercial_records(url):\n    return None\n",
}


@pytest.mark.parametrize("name", sorted(PLANTED))
def test_s1_scanner_catches_each_planted_source(name: str) -> None:
    assert violations("tools/planted.py", PLANTED[name]) != []
