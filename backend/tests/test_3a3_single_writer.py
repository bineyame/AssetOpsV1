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

3A6 (spec §2.9; D-3A6.7, D-3A6.14) adds tagged clauses: every finding is `f"{tag} {rel}:{lineno}: {detail}"`, the
contracts package joins the scan, import aliases are resolved per module, and dynamic imports (`S1-DYN`,
`S1-DYN-COMMERCIAL`), `sys.modules` (`S1-SYSMOD`, `S1-SYSMOD-COMMERCIAL`), `runpy` (`S1-RUNPY`), the names
`"ingest"`/`"CommercialRecords"` as strings (`S1-NAME`), attribute access by a non-constant name (`S1-ATTR`,
`S1-OPERATOR`) and `eval`/`exec`/`compile` in the commercial and native packages (`S1-EVAL`) are rules. Each clause has
its own plant in `PLANTED_TAGGED`; the allowlists equal the scan's findings.

Still not seen (residual, D-3A6.14): a module that imports nothing commercial and calls `.ingest` on a service it is
handed, or uses a non-constant attribute name (plant n2); `__getattribute__`; `vars(obj)[name]` with a non-constant
name; a non-test tool named `test_*.py` (the filter hides `tools/checks/test_event_register.py`).
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

TREE = Path(__file__).resolve().parents[2]
ROOTS = ("backend/assetops_backend", "tools", "host", "simulator", "gateway", "field",
         "contracts/assetops_contracts")  # 3A6 (spec §2.9): the contracts package joins the scan
BACKEND = "backend/assetops_backend/"
CONSTRUCTORS = {BACKEND + "commercial/composition.py"}
INGEST_ALLOWED = {BACKEND + "commercial/uploads.py", BACKEND + "commercial/service.py"}
IMPORT_ALLOWED = {BACKEND + "commercial/composition.py", BACKEND + "commercial/uploads.py"}
BUILD_CALLERS = {BACKEND + "main.py", BACKEND + "load_emulated_exports.py"}
PACKAGE = "assetops_backend.commercial"


# --- 3A6 (spec §2.9; D-3A6.7, D-3A6.14): dynamic imports, sys.modules, runpy, names built from strings ------------

#: Each entry is exactly a finding of the scan at branch time (`test_s1_allowlists_are_exact`).
DYNAMIC_IMPORT_ALLOWED = frozenset({
    BACKEND + "chain/adapters/file_chain_config.py",  # loads a chain configuration module named in its file
    BACKEND + "chain/adapters/file_inputs.py",  # loads the named chain input adapter
    "tools/checks/import_root_probe.py",  # probes where each package imports from (the module-path record)
    "tools/checks/neutral_tests.py",  # the neutral runner imports each test module it runs
    "tools/mechanism_dataset.py",  # loads the simulator's mechanism modules by name
    "tools/validate-test-selection.py",  # imports the selection rules it validates
    "host/conftest.py",  # the host suite's plugin loading
    # 3B7a, merged after spec rev 2 listed the seven above (packet: Known Deviations): locates the contracts package
    # (find_spec runs none of its code) so the code digest covers it
    BACKEND + "structure_snapshot/adapters/code_digest.py",
    # 3A6 fix round r5 (spec §2.12): the forkserver preloads the pure contracts package
    BACKEND + "commercial/envelope.py",
})
SYS_MODULES_ALLOWED = frozenset({
    "tools/mechanism_dataset.py",  # registers the modules it loads by name
    "tools/probe_kisiwa_fuel.py",  # registers a probe module before running it
})
RUNPY_ALLOWED: frozenset[str] = frozenset()  # the scan finds none
DYNAMIC_CALLS = frozenset({"importlib.import_module", "importlib.reload", "importlib.__import__",
                           "importlib.util.find_spec", "importlib.util.spec_from_file_location",
                           "importlib.util.module_from_spec", "__import__", "builtins.__import__"})
ATTR_CALLS = frozenset({"getattr", "setattr", "hasattr", "delattr", "builtins.getattr", "builtins.setattr",
                        "builtins.hasattr", "builtins.delattr"})
OPERATOR_NAMES = frozenset({"operator.attrgetter", "operator.methodcaller"})
EVAL_CALLS = frozenset({"eval", "exec", "compile", "builtins.eval", "builtins.exec", "builtins.compile"})
EVAL_ROOTS = (BACKEND + "commercial/", "contracts/assetops_contracts/native/")
SYS_MODULES_METHODS = frozenset({"get", "pop", "setdefault", "__getitem__"})


def _aliases(tree: ast.AST) -> dict[str, str]:
    """Each name an import binds, mapped to the dotted name it stands for (per module)."""
    out: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.asname:
                    out[a.asname] = a.name
                else:
                    top = a.name.split(".", 1)[0]
                    out[top] = top
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            for a in node.names:
                out[a.asname or a.name] = f"{node.module}.{a.name}"
    return out


def _qual(node: ast.AST, aliases: dict[str, str]) -> str | None:
    """The dotted name an expression stands for (a bare unimported name stands for itself), else None."""
    if isinstance(node, ast.Name):
        return aliases.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        inner = _qual(node.value, aliases)
        return None if inner is None else f"{inner}.{node.attr}"
    return None


def _string_args(node: ast.Call) -> list[str]:
    values = list(node.args) + [k.value for k in node.keywords]
    return [v.value for v in values if isinstance(v, ast.Constant) and isinstance(v.value, str)]


def _preload_strings(node: ast.Call) -> list[str]:
    """r5 (spec §2.12): the module names a `set_forkserver_preload` call names, inside a list or tuple too."""
    values = list(node.args) + [k.value for k in node.keywords]
    for v in list(values):
        if isinstance(v, (ast.List, ast.Tuple)):
            values.extend(v.elts)
    return [v.value for v in values if isinstance(v, ast.Constant) and isinstance(v.value, str)]


def _commercial_string(value: str) -> bool:
    return value.startswith(PACKAGE) or "/commercial/" in value


def _imports_package(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and (node.module == PACKAGE
                                                                 or node.module.startswith(PACKAGE + ".")):
            return True
        if (isinstance(node, ast.ImportFrom) and node.module == PACKAGE.rsplit(".", 1)[0] and node.level == 0
                and any(a.name == PACKAGE.rsplit(".", 1)[1] for a in node.names)):  # D-3A6.20 F6
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


def violations(rel: str, source: str, *, dynamic_allowed: frozenset[str] = DYNAMIC_IMPORT_ALLOWED,
               sys_modules_allowed: frozenset[str] = SYS_MODULES_ALLOWED,
               runpy_allowed: frozenset[str] = RUNPY_ALLOWED) -> list[str]:
    """Every finding as `f"{tag} {rel}:{lineno}: {detail}"`, the tag naming its clause (spec §2.9)."""
    tree = ast.parse(source)
    found: list[str] = []

    def add(tag: str, node: ast.AST | None, detail: str) -> None:
        found.append(f"{tag} {rel}:{getattr(node, 'lineno', 0)}: {detail}")

    if "build_commercial_records" in source:
        add("S1-BUILD", None, "build_commercial_records")
    in_package = _imports_package(tree)
    aliases = _aliases(tree)
    attr_scope = in_package and rel not in INGEST_ALLOWED
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = _called(node)
            qual = _qual(node.func, aliases)
            if name == "CommercialRecords" and rel not in CONSTRUCTORS:
                add("S1-CTOR", node, "CommercialRecords(")
            if name == "build_commercial_uploads" and rel not in BUILD_CALLERS:
                add("S1-BUILD", node, "build_commercial_uploads(")
            if (attr_scope and name == "getattr" and len(node.args) >= 2
                    and isinstance(node.args[1], ast.Constant) and node.args[1].value == "ingest"):
                add("S1-INGEST", node, "getattr ingest")
            if qual in DYNAMIC_CALLS:
                if rel not in dynamic_allowed:
                    add("S1-DYN", node, qual)
                if any(_commercial_string(v) for v in _string_args(node)):
                    add("S1-DYN-COMMERCIAL", node, qual)
            if isinstance(node.func, ast.Attribute) and node.func.attr == "set_forkserver_preload":  # r5, §2.12
                if rel not in dynamic_allowed:
                    add("S1-DYN", node, "set_forkserver_preload")
                if any(_commercial_string(v) for v in _preload_strings(node)):
                    add("S1-DYN-COMMERCIAL", node, "set_forkserver_preload")
            if (isinstance(node.func, ast.Attribute) and node.func.attr in SYS_MODULES_METHODS
                    and _qual(node.func.value, aliases) == "sys.modules" and node.args
                    and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)
                    and node.args[0].value.startswith(PACKAGE)):
                add("S1-SYSMOD-COMMERCIAL", node, f"sys.modules.{node.func.attr}")
            if attr_scope and qual in ATTR_CALLS and not (
                    len(node.args) >= 2 and isinstance(node.args[1], ast.Constant)
                    and isinstance(node.args[1].value, str)):
                add("S1-ATTR", node, f"{qual} by a non-constant name")
            if qual in EVAL_CALLS and rel.startswith(EVAL_ROOTS):
                add("S1-EVAL", node, qual)
        elif isinstance(node, ast.Subscript):
            if (_qual(node.value, aliases) == "sys.modules" and isinstance(node.slice, ast.Constant)
                    and isinstance(node.slice.value, str) and node.slice.value.startswith(PACKAGE)):
                add("S1-SYSMOD-COMMERCIAL", node, "sys.modules[...]")
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name.rsplit(".", 1)[-1] for a in node.names]
            if "CommercialRecords" in names and rel not in IMPORT_ALLOWED:
                add("S1-IMPORT", node, "import CommercialRecords")
            if "build_commercial_uploads" in names and rel not in BUILD_CALLERS:
                add("S1-BUILD", node, "import build_commercial_uploads")
            modules = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
            if rel not in runpy_allowed and any(m == "runpy" or m.startswith("runpy.") for m in modules):
                add("S1-RUNPY", node, "import runpy")
        elif isinstance(node, ast.Constant) and node.value in ("ingest", "CommercialRecords"):
            if rel not in INGEST_ALLOWED | IMPORT_ALLOWED:
                add("S1-NAME", node, repr(node.value))
        if isinstance(node, ast.Attribute) and node.attr == "ingest" and in_package and rel not in INGEST_ALLOWED:
            add("S1-INGEST", node, ".ingest")
        if isinstance(node, (ast.Name, ast.Attribute)) and not isinstance(node.ctx, ast.Store):
            qual = _qual(node, aliases)
            if qual == "sys.modules" and rel not in sys_modules_allowed:
                add("S1-SYSMOD", node, "sys.modules")
            if qual in DYNAMIC_CALLS and rel not in dynamic_allowed:  # a reference, not only a call (D-3A6.20 F6)
                add("S1-DYN", node, qual)
            if qual in EVAL_CALLS and rel.startswith(EVAL_ROOTS):
                add("S1-EVAL", node, qual)
            if attr_scope and qual in OPERATOR_NAMES:
                add("S1-OPERATOR", node, qual)
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


# --- 3A6 (spec §2.9; D-3A6.14): one plant per clause, each giving exactly its tags ------------------------------------

PLANTED_TAGGED = (
    ("p01", "tools/planted.py", "import importlib\nm = importlib.import_module(name)\n", {"S1-DYN"}),
    ("p02", "tools/planted.py", "from importlib import import_module as im\nm = im(name)\n", {"S1-DYN"}),
    ("p03", "tools/planted.py", "import importlib as il\nm = il.import_module(name)\n", {"S1-DYN"}),
    ("p04", "tools/planted.py", "m = __import__(name)\n", {"S1-DYN"}),
    ("p05", "tools/planted.py", "import importlib\nm = importlib.__import__(name)\n", {"S1-DYN"}),
    ("p06", "tools/planted.py", "import importlib.util\nx = importlib.util.find_spec(name)\n", {"S1-DYN"}),
    ("p07", "tools/mechanism_dataset.py",
     "import importlib\nm = importlib.import_module(\"assetops_backend.commercial.service\")\n", {"S1-DYN-COMMERCIAL"}),
    ("p08", "tools/mechanism_dataset.py",
     "import importlib.util as u\nx = u.spec_from_file_location(\"x\", \"backend/assetops_backend/commercial/service.py\")\n",
     {"S1-DYN-COMMERCIAL"}),
    ("p09", "tools/planted.py", "import sys\nm = sys.modules[name]\n", {"S1-SYSMOD"}),
    ("p10", "tools/mechanism_dataset.py", "import sys\nm = sys.modules[\"assetops_backend.commercial.service\"]\n",
     {"S1-SYSMOD-COMMERCIAL"}),
    ("p11", "tools/planted.py", "from sys import modules as mods\nm = mods.get(name)\n", {"S1-SYSMOD"}),
    ("p12", "tools/planted.py", "import runpy\nrunpy.run_module(name)\n", {"S1-RUNPY"}),
    ("p13", "tools/planted.py", "from runpy import run_path\nrun_path(name)\n", {"S1-RUNPY"}),
    ("p14", "tools/planted.py", "name = \"ingest\"\n", {"S1-NAME"}),
    ("p15", "tools/planted.py", "name = \"CommercialRecords\"\n", {"S1-NAME"}),
    ("p16", "tools/planted.py", "from assetops_backend.commercial import composition\nf = getattr(svc, name)\n",
     {"S1-ATTR"}),
    ("p17", "tools/planted.py", "from assetops_backend.commercial import composition\nsetattr(svc, name, f)\n",
     {"S1-ATTR"}),
    ("p18", "tools/planted.py", "from assetops_backend.commercial import composition\nx = hasattr(svc, name)\n",
     {"S1-ATTR"}),
    ("p19", "tools/planted.py", "from assetops_backend.commercial import composition\ndelattr(svc, name)\n",
     {"S1-ATTR"}),
    ("p20", "tools/planted.py",
     "import operator\nfrom assetops_backend.commercial import composition\nf = operator.attrgetter(name)\n",
     {"S1-OPERATOR"}),
    ("p21", "tools/planted.py",
     "from operator import methodcaller as mc\nfrom assetops_backend.commercial import composition\nf = mc(name)\n",
     {"S1-OPERATOR"}),
    ("p22", BACKEND + "commercial/planted.py", "x = eval(s)\n", {"S1-EVAL"}),
    ("p23", BACKEND + "commercial/planted.py", "exec(s)\n", {"S1-EVAL"}),
    ("p24", BACKEND + "commercial/planted.py", "x = compile(s, \"f\", \"exec\")\n", {"S1-EVAL"}),
    ("p25", "contracts/assetops_contracts/native/planted.py", "import builtins\nx = builtins.exec(s)\n", {"S1-EVAL"}),
    ("p26", "tools/planted.py", "import importlib\nim = importlib.import_module\nm = im(name)\n", {"S1-DYN"}),
    ("p27", BACKEND + "commercial/planted.py", "e = eval\ne(s)\n", {"S1-EVAL"}),
    ("p28", "tools/planted.py", "from assetops_backend import commercial\nf = getattr(svc, name)\n", {"S1-ATTR"}),
    ("p-env", "tools/planted.py",
     "import multiprocessing as mp\nmp.get_context(\"forkserver\").set_forkserver_preload([name])\n", {"S1-DYN"}),
    ("p-env-c", BACKEND + "commercial/envelope.py",
     "import multiprocessing as mp\nmp.set_forkserver_preload([\"assetops_backend.commercial.service\"])\n",
     {"S1-DYN-COMMERCIAL"}),
    ("n1", BACKEND + "commercial/planted.py", "import re\nx = re.compile(s)\n", set()),
    ("n2", "tools/planted.py", "x = getattr(obj, name)\n", set()),  # no commercial import: the stated residual
    ("n3", "tools/mechanism_dataset.py", "import importlib\nm = importlib.import_module(name)\n", set()),  # allowlisted
)


@pytest.mark.parametrize("rel,source,tags", [p[1:] for p in PLANTED_TAGGED], ids=[p[0] for p in PLANTED_TAGGED])
def test_s1_each_clause_has_its_plant(rel: str, source: str, tags: set[str]) -> None:
    assert {v.split(" ", 1)[0] for v in violations(rel, source)} == tags


def test_s1_allowlists_are_exact() -> None:
    scanned = {rel: path.read_text(encoding="utf-8") for rel, path in _scanned()}
    open_scan = {rel: violations(rel, src, dynamic_allowed=frozenset(), sys_modules_allowed=frozenset(),
                                 runpy_allowed=frozenset()) for rel, src in scanned.items()}
    for tag, allowed in (("S1-DYN", DYNAMIC_IMPORT_ALLOWED), ("S1-SYSMOD", SYS_MODULES_ALLOWED),
                         ("S1-RUNPY", RUNPY_ALLOWED)):
        holders = {rel for rel, found in open_scan.items() if any(v.split(" ", 1)[0] == tag for v in found)}
        assert holders == set(allowed), (tag, sorted(holders ^ set(allowed)))
