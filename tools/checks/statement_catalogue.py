"""SC-1 statement catalogue guard (spec section 3.8; D-SC1.12, D-SC1.17, D-SC1.27, D-SC1.29).

Checks, in order: (1) the shipped catalogue loads; (2) every variant of every structured statement has a hand-written
case in `backend/tests/statement_cases/`; (3) the legacy ratchet (`statement-legacy-baseline.json`); (4) the
hand-built text scan in three scopes (mechanism, `ADOPTED`, ratchet with `statement-handbuilt-baseline.json`);
(5) no Site code in a statement key, variant id or vocabulary key; and no module outside `i18n` reaches a private
name or a private module of `i18n`.

    python tools/checks/statement_catalogue.py                   # exit 1 and one line per failure
    python tools/checks/statement_catalogue.py --self-test       # every guard plant fails with its code, N1-N4 pass
    python tools/checks/statement_catalogue.py --write-baseline  # writes a missing baseline (BASELINE_EXISTS else)
    python tools/checks/statement_catalogue.py --prune           # removes stale baseline entries, never adds
    options: --root <tree> (scan another tree), --adopt <repo path> (treat a path as ADOPTED; plants only)
"""
from __future__ import annotations

import ast
import hashlib
import importlib
import json
import os
import pkgutil
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PKG = "backend/assetops_backend"
I18N = f"{PKG}/i18n"
LEGACY_BASELINE = "tools/checks/statement-legacy-baseline.json"
HANDBUILT_BASELINE = "tools/checks/statement-handbuilt-baseline.json"

#: Scope (2): repo paths whose text is statements only (3A7 adds `commercial/reconciliation.py`, 5c `deep_dive/...`).
ADOPTED: tuple[str, ...] = ()
#: Scope (1): the modules SC-1 writes (D-SC1.29). `MECH_BRANCH` reads the four that dispatch by table.
MECHANISM = ("__init__", "schema", "facts", "formats", "conditions", "catalogue", "render", "wire")
MECH_BRANCH_FILES = ("formats", "conditions", "render", "wire")
#: The two pre-existing `i18n` modules, read by scope (3) (D-SC1.29).
LEGACY_I18N = ("messages", "locale")
#: `i18n` submodules a module outside `i18n` may import (D-SC1.22: `catalogue`, `formats`, `conditions`, `schema`
#: and the statement data are private; `facts`, `wire` and `render` hold only exported names).
PUBLIC_MODULES = ("messages", "locale", "render", "facts", "wire")
#: Trees read for `I18N_PRIVATE` / `I18N_BYPASS` (python outside `i18n/`, `backend/tests/`, `tools/checks/`).
IMPORT_ROOTS = ("backend", "tools", "simulator", "contracts", "gateway", "host", "field")
SKIP_PARTS = {"__pycache__", ".venv", "venv", "node_modules", "archive", ".git"}

LOG_METHODS = {"debug", "info", "warning", "error", "exception", "critical", "log"}
LOG_NAMES = {"logger", "log", "logging", "_log", "_logger", "LOG"}
KEY_CALLS = {"message", "Word", "Count", "KOfN", "Quantity", "Price", "Absent", "State", "Evidence"}
CHROME_CALLS = {"add_argument", "ArgumentParser", "add_parser", "APIRouter", "FastAPI"}
CHROME_KEYWORDS = {"help", "description", "epilog", "usage", "summary"}

UPPER_SNAKE = re.compile(r"^[A-Z][A-Z0-9_]*$")
DECIMAL = re.compile(r"^\d+(\.\d+)?$")
FORMAT_SPEC = re.compile(r"^,?(\.\d+)?[fd]?$")
CODE_FORM = re.compile(r"^[A-Za-z0-9_.\-]*$")
CAP_LOWER = re.compile(r"[A-Z][a-z]")
LOWER_WORD = re.compile(r"^[a-z]+$")
PROSE = re.compile(r"(?<![A-Za-z])(?=([A-Za-z]{2,}\s+[A-Za-z]{2,}))")
SQL_START = re.compile(r"^\s*(SELECT|INSERT|UPDATE|DELETE|WITH|CREATE|ALTER|DROP)\b")
LETTER = re.compile(r"[A-Za-z]")
LETTER_OR_SPACE = re.compile(r"[A-Za-z\s]")
WORD_MAP_VALUE = re.compile(r"^[A-Z][a-z]")


# --- helpers ---------------------------------------------------------------------------------------------------------


def _str(node) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, str)


def prose(text) -> bool:
    """Spec section 3.8.4 (3): two words of two or more letters, a lower-case letter among them, not SQL."""
    if not isinstance(text, str) or SQL_START.match(text):
        return False
    return any(re.search(r"[a-z]", m.group(1)) for m in PROSE.finditer(text))


def _call_name(call: ast.Call) -> str | None:
    f = call.func
    return f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None


def _attr_call(node, *names) -> bool:
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in names


def _module_call(node, module: str, *names) -> bool:
    return (_attr_call(node, *names) and isinstance(node.func.value, ast.Name) and node.func.value.id == module)


def _subtree_ids(nodes) -> set[int]:
    out: set[int] = set()
    for n in nodes:
        out.update(id(m) for m in ast.walk(n))
    return out


class Tree:
    """A parsed module: parents, enclosing qualified names, and the exempt nodes of spec section 3.8.4."""

    def __init__(self, path: str, source: str, unserved: tuple):
        self.path = path
        self.tree = ast.parse(source, filename=path)
        self.parent: dict[int, ast.AST] = {}
        self.qual: dict[int, str] = {}
        self.nodes: list[ast.AST] = []
        stack = [(self.tree, "<module>")]
        while stack:  # one traversal: every node, its parent and its enclosing qualified name
            node, qual = stack.pop()
            self.nodes.append(node)
            self.qual[id(node)] = qual
            for child in ast.iter_child_nodes(node):
                self.parent[id(child)] = node
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    stack.append((child, child.name if qual == "<module>" else f"{qual}.{child.name}"))
                else:
                    stack.append((child, qual))
        exempt: list[ast.AST] = []
        self.fstring_parts: set[int] = set()
        self.format_specs: set[int] = set()
        self.all_values: set[int] = set()
        for n in self.nodes:
            if isinstance(n, ast.Expr) and _str(n.value):
                exempt.append(n.value)
            elif isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in LOG_METHODS \
                    and isinstance(n.func.value, ast.Name) and n.func.value.id in LOG_NAMES:
                exempt += n.args + [k.value for k in n.keywords]
            elif isinstance(n, ast.Raise) and isinstance(n.exc, ast.Call) and _call_name(n.exc) in unserved:
                exempt += n.exc.args + [k.value for k in n.exc.keywords]
            elif isinstance(n, ast.JoinedStr):
                self.fstring_parts.update(id(v) for v in n.values if isinstance(v, ast.Constant))
            elif isinstance(n, ast.FormattedValue) and n.format_spec is not None:
                self.format_specs.update(id(v) for v in ast.walk(n.format_spec) if isinstance(v, ast.Constant))
            elif isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in n.targets):
                self.all_values |= _subtree_ids([n.value])
        self.exempt = _subtree_ids(exempt)
        self.fstring_parts -= self.format_specs

    def live(self):
        return (n for n in self.nodes if id(n) not in self.exempt)

    def served_exception_text(self):
        """`str(e)`, `e.args` or `{e}` for `e` bound by `except ... as e`, outside the exemptions."""
        for h in self.nodes:
            if not isinstance(h, ast.ExceptHandler) or not h.name:
                continue
            for stmt in h.body:
                for n in ast.walk(stmt):
                    if id(n) in self.exempt:
                        continue
                    if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "str"
                            and len(n.args) == 1 and isinstance(n.args[0], ast.Name) and n.args[0].id == h.name) \
                            or (isinstance(n, ast.Attribute) and n.attr == "args" and isinstance(n.value, ast.Name)
                                and n.value.id == h.name) \
                            or (isinstance(n, ast.FormattedValue) and isinstance(n.value, ast.Name)
                                and n.value.id == h.name):
                        yield n


# --- scope (1): mechanism --------------------------------------------------------------------------------------------


def mechanism_hits(path: str, source: str, schema, instances: set, branch: bool) -> list[str]:
    t = Tree(path, source, schema.UNSERVED)
    out = []
    for n in t.live():
        if _str(n) and id(n) not in t.all_values:
            s = n.value
            if id(n) in t.format_specs:
                ok = bool(FORMAT_SPEC.match(s))
            elif id(n) in t.fstring_parts:
                ok = s in schema.SYMBOLS
            elif s in schema.TOKENS:
                ok = True
            elif UPPER_SNAKE.match(s):
                if s in instances:
                    out.append(f"MECH_INSTANCE {path}:{n.lineno} {s}")
                continue
            else:
                ok = s in schema.SYMBOLS or bool(DECIMAL.match(s))
            if not ok:
                out.append(f"MECH_LITERAL {path}:{n.lineno} {s!r}")
        if branch and (
                (isinstance(n, ast.Compare) and any(_str(o) for o in [n.left, *n.comparators]))
                or (isinstance(n, ast.MatchValue) and _str(n.value))
                or (isinstance(n, ast.IfExp) and (_str(n.body) or _str(n.orelse)))):
            out.append(f"MECH_BRANCH {path}:{n.lineno}")
    out += [f"MECH_LITERAL {path}:{n.lineno} served exception text" for n in t.served_exception_text()]
    return out


# --- scope (2): adopted ----------------------------------------------------------------------------------------------


def _key_context(t: Tree, node: ast.Constant) -> bool:
    """A plain lower-case word is code-form only where it is a key, not a word (spec section 3.8.4 (2))."""
    parent = t.parent.get(id(node))
    if isinstance(parent, ast.Dict) and any(k is node for k in parent.keys):
        return True
    if isinstance(parent, ast.Subscript) and parent.slice is node:
        return True
    keyword = None
    if isinstance(parent, ast.keyword):
        keyword, parent = parent.arg, t.parent.get(id(parent))
    if not isinstance(parent, ast.Call):
        return False
    name = _call_name(parent)
    position = next((i for i, a in enumerate(parent.args) if a is node), None)
    if name in ("getattr", "hasattr"):
        return position == 1
    if name in KEY_CALLS:
        return True
    return name == "Name" and (position == 1 or keyword == "source")


def _code_form(t: Tree, node: ast.Constant) -> bool:
    s = node.value
    if len(s) == 1 and not s.isalpha():
        return True
    if not CODE_FORM.match(s) or CAP_LOWER.search(s):
        return False
    return not LOWER_WORD.match(s) or _key_context(t, node)


def _composes(n) -> bool:
    return _str(n) or isinstance(n, ast.JoinedStr) or (
        isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "str")


def adopted_hits(path: str, source: str, unserved: tuple) -> list[str]:
    t = Tree(path, source, unserved)
    lines: set[int] = set()
    for n in t.live():
        hit = (
            (_str(n) and not _code_form(t, n))
            or (isinstance(n, ast.Compare)
                and any(_str(o) and not UPPER_SNAKE.match(o.value) for o in [n.left, *n.comparators]))
            or isinstance(n, ast.JoinedStr)
            or (isinstance(n, ast.BinOp) and isinstance(n.op, ast.Mod) and (_str(n.left) or isinstance(n.left, ast.JoinedStr)))
            or _attr_call(n, "format", "format_map", "capitalize", "title", "swapcase")
            or (isinstance(n, ast.Call) and _call_name(n) == "Template")
            or (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name)
                and n.func.value.id == "textwrap")
            or (_attr_call(n, "replace") and len(n.args) >= 2 and _str(n.args[0]) and _str(n.args[1]))
            or _module_call(n, "re", "sub", "subn")
            or (_attr_call(n, "join") and _str(n.func.value))
            or (isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add) and (_composes(n.left) or _composes(n.right)))
            or (isinstance(n, ast.AugAssign) and isinstance(n.op, ast.Add) and _composes(n.value))
            or (isinstance(n, ast.IfExp) and (_str(n.body) or _str(n.orelse))))
        if hit:
            lines.add(n.lineno)
    lines.update(n.lineno for n in t.served_exception_text())
    return [f"HAND_BUILT {path}:{line}" for line in sorted(lines)]


# --- scope (3): ratchet ----------------------------------------------------------------------------------------------


def _prose_fstring(n) -> bool:
    return isinstance(n, ast.JoinedStr) and any(_str(v) and prose(v.value) for v in n.values)


def _chrome_values(t: Tree) -> set[int]:
    """Keyword values that are static chrome (spec section 3.8.4 (3)(g))."""
    decorators = {id(d) for n in t.nodes if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                  for d in n.decorator_list}
    out = []
    for n in t.nodes:
        if isinstance(n, ast.Call) and (_call_name(n) in CHROME_CALLS or id(n) in decorators):
            out += [k.value for k in n.keywords if k.arg in CHROME_KEYWORDS]
    return _subtree_ids(out)


_RATCHET_TYPES = (ast.JoinedStr, ast.BinOp, ast.Call, ast.AugAssign, ast.IfExp, ast.Constant, ast.Dict)


def ratchet_rules(n, t: Tree, chrome: set[int]) -> str | None:
    if not isinstance(n, _RATCHET_TYPES):
        return None
    if _prose_fstring(n):
        return "a"
    if (isinstance(n, ast.BinOp) and isinstance(n.op, ast.Mod) and _str(n.left) and prose(n.left.value)) \
            or (_attr_call(n, "format", "format_map") and _str(n.func.value) and prose(n.func.value.value)):
        return "b"
    if _module_call(n, "string", "Template") or _module_call(n, "textwrap", "fill", "wrap", "shorten"):
        return "c"
    if (isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add)
            and any((_str(o) and prose(o.value)) or _prose_fstring(o) for o in (n.left, n.right))) \
            or (isinstance(n, ast.AugAssign) and isinstance(n.op, ast.Add)
                and ((_str(n.value) and prose(n.value.value)) or _prose_fstring(n.value))):
        return "d"
    if _attr_call(n, "join") and (
            (_str(n.func.value) and LETTER_OR_SPACE.search(n.func.value.value))
            or (n.args and isinstance(n.args[0], (ast.List, ast.Tuple))
                and any(_str(e) and LETTER.search(e.value) for e in n.args[0].elts))):
        return "e"
    if isinstance(n, ast.IfExp) and (
            (_str(n.body) and _str(n.orelse) and LETTER.search(n.body.value) and LETTER.search(n.orelse.value))
            or any(_str(b) and prose(b.value) for b in (n.body, n.orelse))):
        return "f"
    if _str(n) and prose(n.value) and id(n) not in t.fstring_parts and id(n) not in chrome:
        return "g"
    if _attr_call(n, "capitalize", "title") \
            or ((_attr_call(n, "replace") or _module_call(n, "re", "sub", "subn")) and len(n.args) >= 2
                and _str(n.args[1]) and LETTER_OR_SPACE.search(n.args[1].value)):
        return "h"
    if isinstance(n, ast.Dict) and sum(1 for v in n.values if _str(v) and WORD_MAP_VALUE.match(v.value)) >= 2:
        return "i"
    return None


def ratchet_hits(path: str, source: str, unserved: tuple) -> list[tuple[str, int]]:
    """(fingerprint, line) per hit: `<rule>:<enclosing qualified name>:<sha1 of ast.unparse(node)>[:12]`.

    The self-test sets `SC1_GUARD_CACHE` to a folder of its temporary tree, so an unplanted module is scanned once
    across the plants (keyed by the hash of its path and source)."""
    cache = os.environ.get("SC1_GUARD_CACHE")
    if cache:
        entry = Path(cache) / (hashlib.sha1(f"{path}\0{source}".encode("utf-8")).hexdigest() + ".json")
        if entry.exists():
            return [tuple(h) for h in json.loads(entry.read_text(encoding="utf-8"))]
        found = _ratchet_scan(path, source, unserved)
        part = entry.with_suffix(f".{os.getpid()}.part")
        part.write_text(json.dumps(found), encoding="utf-8")
        os.replace(part, entry)  # plants run in parallel: never expose a half-written entry
        return found
    return _ratchet_scan(path, source, unserved)


def _ratchet_scan(path: str, source: str, unserved: tuple) -> list[tuple[str, int]]:
    t = Tree(path, source, unserved)
    chrome = _chrome_values(t)

    def fingerprint(rule, n):
        digest = hashlib.sha1(ast.unparse(n).encode("utf-8")).hexdigest()[:12]
        return f"{rule}:{t.qual.get(id(n), '<module>')}:{digest}", n.lineno

    out = []
    for n in t.live():
        rule = ratchet_rules(n, t, chrome)
        if rule:
            out.append(fingerprint(rule, n))
    out += [fingerprint("j", n) for n in t.served_exception_text()]
    return out


# --- imports of i18n from outside ------------------------------------------------------------------------------------


def _resolve(rel: str, node: ast.ImportFrom) -> str:
    if not node.level:
        return node.module or ""
    parts = Path(rel).with_suffix("").parts
    if parts and parts[0] == "backend":
        parts = parts[1:]
    base = list(parts[:-node.level]) if not rel.endswith("__init__.py") else list(parts[:len(parts) - node.level])
    return ".".join(base + ([node.module] if node.module else []))


def import_hits(rel: str, source: str) -> list[str]:
    tree = ast.parse(source, filename=rel)
    out, bound = [], set()
    package = "assetops_backend.i18n"
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name.startswith(package + "."):
                    sub = a.name[len(package) + 1:].split(".")[0]
                    if sub not in PUBLIC_MODULES:
                        out.append(f"I18N_BYPASS {rel}:{n.lineno} {a.name}")
                    if a.asname:
                        bound.add(a.asname)
        elif isinstance(n, ast.ImportFrom):
            module = _resolve(rel, n)
            if module == package:
                for a in n.names:
                    if a.name.startswith("_"):
                        out.append(f"I18N_PRIVATE {rel}:{n.lineno} {a.name}")
                    elif a.name in MECHANISM + ("statements",) and a.name not in PUBLIC_MODULES:
                        out.append(f"I18N_BYPASS {rel}:{n.lineno} {package}.{a.name}")
                    if a.name in MECHANISM + LEGACY_I18N + ("statements",):
                        bound.add(a.asname or a.name)
            elif module.startswith(package + "."):
                sub = module[len(package) + 1:].split(".")[0]
                if sub not in PUBLIC_MODULES:
                    out.append(f"I18N_BYPASS {rel}:{n.lineno} {module}")
                out += [f"I18N_PRIVATE {rel}:{n.lineno} {a.name}" for a in n.names
                        if a.name.startswith("_") and not a.name.startswith("__")]
    for n in ast.walk(tree):
        if isinstance(n, ast.Attribute) and n.attr.startswith("_") and not n.attr.startswith("__"):
            owner = ast.unparse(n.value)
            if owner in bound or owner.startswith(package + "."):
                out.append(f"I18N_PRIVATE {rel}:{n.lineno} {owner}.{n.attr}")
    return out


def _import_files(root: Path):
    for top in IMPORT_ROOTS:
        base = root / top
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*.py")):
            rel = p.relative_to(root).as_posix()
            if SKIP_PARTS.intersection(p.relative_to(root).parts) or rel.startswith(
                    (I18N + "/", "backend/tests/", "tools/checks/")):
                continue
            yield rel, p


# --- Site codes ------------------------------------------------------------------------------------------------------


def site_tokens(root: Path) -> set[str]:
    """Spec section 3.8 (5): letters of every value under a `site_id` or `site_code` key, 3 or more, case-folded."""
    import yaml

    loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
    out: set[str] = set()

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if k in ("site_id", "site_code"):
                    for s in (v if isinstance(v, list) else [v]):
                        if isinstance(s, str):
                            out.update(t.casefold() for t in re.split(r"[^A-Za-z]+", s) if len(t) >= 3)
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    files = [p for p in sorted((root / "config").rglob("*")) if p.suffix in (".yaml", ".yml", ".json")]
    files += sorted((root / "backend" / "conversions").glob("*.json"))
    for p in files:
        text = p.read_text(encoding="utf-8")
        walk([json.loads(text)] if p.suffix == ".json" else list(yaml.load_all(text, Loader=loader)))
    return out


def _segments(name: str) -> list[str]:
    return [s.casefold() for s in re.split(r"[_.]", name) if s]


# --- the catalogue ---------------------------------------------------------------------------------------------------


def _slot_specs(spec):
    if isinstance(spec, dict):
        yield spec
        if isinstance(spec.get("of"), dict):
            yield from _slot_specs(spec["of"])


def instance_codes(statement_sets, vocabularies) -> set[str]:
    """State values, absent reasons and vocabulary entry keys: instances the mechanism must never name."""
    out: set[str] = set()
    for statements in statement_sets:
        for st in statements.values():
            for spec in st.get("slots", {}).values():
                for s in _slot_specs(spec):
                    out.update(v for v in s.get("values", []) if isinstance(v, str))
                    out.update(v for v in s.get("absent", []) if isinstance(v, str))
    for vocab in vocabularies:
        for entry in vocab.values():
            out.update(entry.get("entries", {}))
    return out


def legacy_hashes(catalogue: dict) -> dict[str, str]:
    return {k: hashlib.sha256(v.encode("utf-8")).hexdigest()[:16]
            for k, v in sorted(catalogue["en"].items()) if isinstance(v, str)}


def _cases(root: Path):
    folder = root / "backend" / "tests" / "statement_cases"
    for info in sorted(pkgutil.iter_modules([str(folder)]), key=lambda i: i.name):
        module = importlib.import_module(f"statement_cases.{info.name}")
        for case in getattr(module, "CASES", []):
            yield info.name, case


def coverage(root: Path, cat, render_internal, message, worked_keys: set) -> list[str]:
    out = []
    statements = cat.statements["en"]
    covered: set[tuple] = set()
    for module, case in _cases(root):
        st = statements.get(case.key)
        if st is None:
            if case.key not in worked_keys:  # worked keys are covered by T9 through the test catalogue
                out.append(f"CASE_UNKNOWN {case.key} {case.variant} ({module})")
            continue
        served_mode = st.get("evidence", "inline") != "inline"
        ids = [v["id"] for v in st["variants"]]
        if case.variant not in ids or served_mode != (case.evidence is not None) or st.get("part_only"):
            out.append(f"CASE_UNKNOWN {case.key} {case.variant} ({module})")
            continue
        trace: list = []
        try:
            render_internal(message(case.key, **case.facts), "en", served_mode, trace)
        except Exception as exc:  # noqa: BLE001 - a case that cannot render chooses no variant
            out.append(f"CASE_VARIANT {case.key} {case.variant} ({type(exc).__name__} {getattr(exc, 'code', '')})")
            continue
        if not trace or trace[0] != (case.key, case.variant):
            out.append(f"CASE_VARIANT {case.key} {case.variant} (chose {trace[0] if trace else None})")
        covered.update(trace)
    for key, st in sorted(statements.items()):
        out += [f"CASE_MISSING {key} {v['id']}" for v in st["variants"] if (key, v["id"]) not in covered]
    return out


# --- the run ---------------------------------------------------------------------------------------------------------


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _ratchet_paths(root: Path, adopted: tuple):
    i18n = root / I18N
    for p in sorted((root / PKG).rglob("*.py")):
        rel = p.relative_to(root).as_posix()
        if "__pycache__" in p.parts or rel in adopted:
            continue
        if p.parent == i18n and p.stem in LEGACY_I18N or not p.is_relative_to(i18n):
            yield rel, p


def run(root: Path, adopted: tuple, mode: str | None) -> list[str]:
    sys.path[:0] = [str(root / "backend"), str(root / "backend" / "tests")]
    try:
        catalogue = importlib.import_module("assetops_backend.i18n.catalogue")
    except Exception as exc:  # noqa: BLE001 - the load check reports the catalogue's own code
        return [f"LOAD {getattr(exc, 'code', type(exc).__name__)} {getattr(exc, 'key', '')} "
                f"{getattr(exc, 'detail', '')}".rstrip()]
    schema = importlib.import_module("assetops_backend.i18n.schema")
    messages = importlib.import_module("assetops_backend.i18n.messages")
    render = importlib.import_module("assetops_backend.i18n.render")
    worked = importlib.import_module("statement_cases.worked")
    cat = catalogue.current()
    out: list[str] = []

    # (1)-(2): coverage
    out += coverage(root, cat, render._render, messages.message, set(worked.WORKED))

    # (3): legacy ratchet
    hashes = legacy_hashes(messages.CATALOGUE)
    legacy_path = root / LEGACY_BASELINE
    legacy = _read_json(legacy_path)

    # (4): the scan
    i18n = root / I18N
    instances = instance_codes([*cat.statements.values(), worked.WORKED], cat.vocabulary.values())
    for p in sorted(i18n.glob("*.py")):
        rel = p.relative_to(root).as_posix()
        if p.stem in MECHANISM:
            out += mechanism_hits(rel, p.read_text(encoding="utf-8"), schema, instances, p.stem in MECH_BRANCH_FILES)
        elif p.stem not in LEGACY_I18N:
            out.append(f"MECH_UNSCOPED {rel}")
    for rel in adopted:
        if (root / rel).exists():
            out += adopted_hits(rel, (root / rel).read_text(encoding="utf-8"), schema.UNSERVED)
    hits: dict[str, list[tuple[str, int]]] = {}
    for rel, p in _ratchet_paths(root, adopted):
        found = ratchet_hits(rel, p.read_text(encoding="utf-8"), schema.UNSERVED)
        if found:
            hits[rel] = found
    handbuilt_path = root / HANDBUILT_BASELINE
    baseline = _read_json(handbuilt_path)

    if mode == "--write-baseline":
        for path, data in ((legacy_path, hashes), (handbuilt_path, {k: sorted(f for f, _ in v) for k, v in hits.items()})):
            if path.exists():
                out.append(f"BASELINE_EXISTS {path.relative_to(root).as_posix()}")
            else:
                _write_json(path, data)
        return [o for o in out if o.startswith("BASELINE_EXISTS")]
    if mode == "--prune":
        if legacy is not None:
            _write_json(legacy_path, {k: v for k, v in legacy.items() if hashes.get(k) == v})
        if baseline is not None:
            pruned = {}
            for path, prints in baseline.items():
                have = Counter(f for f, _ in hits.get(path, []))
                keep = [f for f in prints if have[f] > 0 and not have.subtract([f])]
                if keep and path not in adopted:
                    pruned[path] = sorted(keep)
            _write_json(handbuilt_path, pruned)
        return []

    if legacy is None:
        out.append(f"BASELINE_MISSING {LEGACY_BASELINE}")
    else:
        out += [f"LEGACY_NEW {k}" for k in hashes if k not in legacy]
        out += [f"LEGACY_CHANGED {k}" for k in hashes if k in legacy and legacy[k] != hashes[k]]
        out += [f"LEGACY_STALE {k}" for k in legacy if k not in hashes]
    if baseline is None:
        out.append(f"BASELINE_MISSING {HANDBUILT_BASELINE}")
    else:
        for path in sorted(set(hits) | set(baseline)):
            if path in adopted:
                if path in baseline:
                    out.append(f"HAND_BUILT_STALE {path} (ADOPTED)")
                continue
            have = Counter(f for f, _ in hits.get(path, []))
            want = Counter(baseline.get(path, []))
            extra = have - want
            for f, line in hits.get(path, []):
                if extra[f] > 0:
                    extra[f] -= 1
                    out.append(f"HAND_BUILT_NEW {path}:{line} {f}")
            out += [f"HAND_BUILT_STALE {path} {f}" for f in sorted((want - have).elements())]

    # (5): Site codes in keys; private i18n reached from outside
    tokens = site_tokens(root)
    names: list[tuple[str, str]] = []
    for statements in [*cat.statements.values(), worked.WORKED]:
        for key, st in statements.items():
            names.append((key, key))
            names += [(key, v["id"]) for v in st.get("variants", []) if isinstance(v.get("id"), str)]
    for vocab in cat.vocabulary.values():
        for vname, entry in vocab.items():
            names.append((vname, vname))
            names += [(vname, e) for e in entry.get("entries", {})]
    seen = set()
    for owner, name in names:
        for seg in _segments(name):
            if seg in tokens and (owner, name, seg) not in seen:
                seen.add((owner, name, seg))
                out.append(f"KEY_INSTANCE {owner} {name} {seg}")
    for rel, p in _import_files(root):
        text = p.read_text(encoding="utf-8")
        if "i18n" in text:
            out += import_hits(rel, text)
    return out


# --- self-test -------------------------------------------------------------------------------------------------------

_COPY = (PKG, "backend/tests/statement_cases", "config", "backend/conversions", LEGACY_BASELINE, HANDBUILT_BASELINE)
_PLANT = f"{PKG}/_sc1_plant.py"


def _append(text: str):
    return lambda s: s + "\n" + text


def _replace_once(old: str, new: str):
    def edit(s: str) -> str:
        assert s.count(old) >= 1, old
        return s.replace(old, new, 1)
    return edit


def _plants(base: Path) -> list[tuple]:
    """(name, {repo path: edit or text}, args, required code, allowed codes); allowed None: must pass (N1-N4)."""
    baseline = _read_json(base / HANDBUILT_BASELINE) or {}
    leaf = next(p for p in sorted(baseline) if not p.startswith(I18N + "/") and not p.endswith("__init__.py"))
    common = f"{I18N}/statements/en/common.py"
    cases = "backend/tests/statement_cases/common.py"
    msgs, loc = f"{I18N}/messages.py", f"{I18N}/locale.py"
    first_legacy = next(iter(_read_json(base / LEGACY_BASELINE) or {"": ""}))
    adopt = ["--adopt", _PLANT]
    head = "from assetops_backend.i18n import message\n"
    adopted = {
        "P13": "def f(x):\n    return f\"The gap is {x}.\"\n",
        "P13a": "X = \"Not available\"\n",
        "P13b": "def f(xs):\n    return \" \".join([x for x in xs])\n",
        "P13c": "X = \"\".join([\"Not \", \"available\"])\n",
        "P13d": "def f(x):\n    return \"a\" if x else \"an\"\n",
        "P13e": "import string\nT = string.Template(\"$x\")\n",
        "P13f": "import textwrap\ndef f(s):\n    return textwrap.fill(s)\n",
        "P13g": "def f(x, unit):\n    return str(x) + unit\n",
        "P13h": "def f(s):\n    s += \"x\"\n    return s\n",
        "P13i": "M = {\"A\": \"Recorded\", \"B\": \"Measured\"}\n",
        "P13j": "from fastapi import HTTPException\ndef f(x):\n    raise HTTPException(409, detail=f\"{x}\")\n",
        "P13k": "def f(x):\n    return _refuse(409, \"X\", f\"{x}\")\n",
        "P13l": "def f(g):\n    try:\n        g()\n    except Exception as e:\n        return dict(detail=str(e))\n",
        "P13m": "def f(code):\n    return code.replace(\"_\", \" \")\n",
        "P13n": "def f(code):\n    return code.capitalize()\n",
        "P13o": "def f(x):\n    return \"%s left\" % x\n",
        "P13p": "def f(x):\n    return \"{} left\".format(x)\n",
        "P13q": "def f(word):\n    if word == \"below\":\n        return 1\n",
        "N1": "import logging\nlogger = logging.getLogger(__name__)\ndef f(x):\n    logger.info(f\"read {x} rows\")\n",
        "N2": "def f(x):\n    raise ValueError(f\"bad value {x}\")\n",
        "N3": head + "from decimal import Decimal\nfrom assetops_backend.i18n import Evidence, Money\n\n\ndef f():\n"
              "    \"\"\"The headline of the deep dive.\"\"\"\n    return message(\"deep_dive.headline\", gap=Money("
              "Decimal(\"5\"), \"USD\", Evidence(\"DERIVED\", \"source-emulated\")))\n",
    }
    out = [(name, {_PLANT: body}, adopt, None if name.startswith("N") else "HAND_BUILT", {"HAND_BUILT"})
           for name, body in adopted.items()]
    out += [
        ("P12", {cases: _replace_once(
            "    Case(\"common.budget_lines\", \"one\", {\"factors\": Items((Word(\"factor\", \"om\"),))}, "
            "\"a budget line for O&M\"),  # B1\n", "")}, [], "CASE_MISSING", {"CASE_MISSING"}),
        ("P14", {msgs: _replace_once("    \"en\": {\n", "    \"en\": {\n        \"sc1.p14\": \"{count}\",\n")},
         [], "LEGACY_NEW", {"LEGACY_NEW", "HAND_BUILT_NEW", "HAND_BUILT_STALE"}),  # (i): `CATALOGUE` is a word map
        ("P17", {common: _replace_once("STATEMENTS = {\n", "STATEMENTS = {\n    \"reconciliation.kobo_heading\": "
                                       "{\"slots\": {}, \"variants\": [{\"id\": \"plain\", \"text\": \"Heading.\"}]},\n"),
                 cases: _append("CASES.append(Case(\"reconciliation.kobo_heading\", \"plain\", {}, \"Heading.\"))\n")},
         [], "KEY_INSTANCE", {"KEY_INSTANCE"}),
        ("P42", {msgs: lambda s: _edit_template(s, first_legacy)}, [], "LEGACY_CHANGED",
         {"LEGACY_CHANGED", "HAND_BUILT_NEW", "HAND_BUILT_STALE"}),
        ("P43", {leaf: _append("def _p43(x):\n    return f\"the gap is {x} today\"\n")}, [], "HAND_BUILT_NEW",
         {"HAND_BUILT_NEW"}),
        ("P44", {leaf: lambda s: ""}, [], "HAND_BUILT_STALE", {"HAND_BUILT_STALE"}),
        ("P45", {f"{I18N}/formats.py": _append("_P45 = \"less than\"\n")}, [], "MECH_LITERAL", {"MECH_LITERAL"}),
        ("P46", {f"{I18N}/render.py": _append("def _p46(spec):\n    if spec[\"type\"] == \"money\":\n        return 1\n")},
         [], "MECH_BRANCH", {"MECH_BRANCH"}),
        ("P47", {f"{I18N}/catalogue.py": _append("_P47 = \"MATCHED\"\n")}, [], "MECH_INSTANCE", {"MECH_INSTANCE"}),
        ("P48", {_PLANT: "from assetops_backend.i18n import catalogue\n\n\ndef f(c):\n    with catalogue._use(c):\n"
                         "        return 1\n"}, [], "I18N_PRIVATE", {"I18N_PRIVATE", "I18N_BYPASS"}),
        ("P49", {_PLANT: "import assetops_backend.i18n.formats\n"}, [], "I18N_BYPASS", {"I18N_BYPASS"}),
        ("P50", {}, ["--write-baseline"], "BASELINE_EXISTS", {"BASELINE_EXISTS"}),
        ("P51", {f"{I18N}/extra.py": "X = 1\n"}, [], "MECH_UNSCOPED", {"MECH_UNSCOPED"}),
        ("P52", {f"{I18N}/conditions.py": _append("_P52 = \"const\"\n")}, [], "MECH_LITERAL", {"MECH_LITERAL"}),
        ("P52b", {f"{I18N}/conditions.py": _append("_P52 = {\"params\": 1}\n")}, [], "MECH_LITERAL", {"MECH_LITERAL"}),
        ("P53", {msgs: _replace_once("    \"en\": {\n", "    \"en\": {\n        \"sc1.p53\": \"A new sentence here.\",\n")},
         [], "HAND_BUILT_NEW", {"HAND_BUILT_NEW", "HAND_BUILT_STALE", "LEGACY_NEW"}),
        ("P53b", {loc: _append("def _p53(x):\n    return f\"the locale {x} is not known\"\n")}, [], "HAND_BUILT_NEW",
         {"HAND_BUILT_NEW"}),
        ("P53c", {msgs: lambda s: _edit_template(s, list((_read_json(base / LEGACY_BASELINE) or {}))[-1])}, [],
         "LEGACY_CHANGED", {"LEGACY_CHANGED", "HAND_BUILT_NEW", "HAND_BUILT_STALE"}),
        ("N4", {leaf: _append("def _n4(p):\n    return f\"SELECT id FROM site WHERE code = {p}\"\n")}, [], None,
         None),
    ]
    return out


def _edit_template(source: str, key: str) -> str:
    """Changes one legacy template's text (a word added before its closing quote)."""
    marker = f"\"{key}\": "
    start = source.index(marker) + len(marker)
    quote = source.index("\"", start + 1)
    while source[quote - 1] == "\\":
        quote = source.index("\"", quote + 1)
    return source[:quote] + " Edited" + source[quote:]


def _clone(base: Path, dest: Path) -> None:
    shutil.copytree(base, dest, copy_function=os.link)


def _write(root: Path, rel: str, edit) -> None:
    path = root / rel
    old = path.read_text(encoding="utf-8") if path.exists() else ""
    new = edit(old) if callable(edit) else edit
    if path.exists():
        path.unlink()  # hard-linked from the base copy: never write through the link
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(new, encoding="utf-8")


def _guard(root: Path, args: list[str]) -> tuple[int, list[str]]:
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(root / "backend"), str(root / "backend" / "tests")]),
               PYTHONDONTWRITEBYTECODE="1", SC1_GUARD_CACHE=str(root.parent / "cache"))
    proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--root", str(root), *args], env=env,
                          capture_output=True, text=True, timeout=300)
    lines = [ln for ln in proc.stdout.splitlines() if ln and not ln.startswith("OK ")]
    if proc.returncode and not lines:
        lines = [f"CRASH {proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else proc.returncode}"]
    return proc.returncode, lines


def self_test() -> int:
    with tempfile.TemporaryDirectory(prefix="sc1-guard-") as tmp:
        base = Path(tmp) / "base"
        (Path(tmp) / "cache").mkdir()
        for rel in _COPY:
            src, dst = REPO / rel, base / rel
            if src.is_dir():
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__"))
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        code, lines = _guard(base, [])
        if code:
            print("FAIL self-test: the unplanted copy fails\n  " + "\n  ".join(lines[:20]))
            return 1
        plants = _plants(base)

        def one(plant):
            name, edits, args, required, allowed = plant
            root = Path(tmp) / name
            _clone(base, root)
            for rel, edit in edits.items():
                _write(root, rel, edit)
            code, lines = _guard(root, args)
            codes = {ln.split()[0] for ln in lines}
            if required is None:
                ok = code == 0
            else:
                ok = code != 0 and required in codes and codes <= allowed
            shutil.rmtree(root, ignore_errors=True)
            return name, ok, required, lines

        failed = 0
        with ThreadPoolExecutor(max_workers=int(os.environ.get("SC1_GUARD_WORKERS", "4"))) as pool:
            for name, ok, required, lines in pool.map(one, plants):
                status = "ok  " if ok else "FAIL"
                expect = required or "pass"
                print(f"{status} {name}: expected {expect}; got {', '.join(sorted({ln.split()[0] for ln in lines})) or 'pass'}")
                if not ok:
                    failed += 1
                    print("     " + "\n     ".join(lines[:8]))
        print(f"{'OK' if not failed else 'FAIL'} statement catalogue self-test: {len(plants) - failed} of "
              f"{len(plants)} plants behave")
        return 1 if failed else 0


def main(argv: list[str]) -> int:
    root, adopted, mode = REPO, list(ADOPTED), None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--root":
            root, i = Path(argv[i + 1]).resolve(), i + 1
        elif a == "--adopt":
            adopted.append(argv[i + 1])
            i += 1
        elif a in ("--write-baseline", "--prune", "--self-test"):
            mode = a
        else:
            print(f"usage: unknown argument {a}")
            return 2
        i += 1
    if mode == "--self-test":
        return self_test()
    out = run(root, tuple(adopted), mode)
    for line in out:
        print(line)
    if not out:
        print(f"OK statement catalogue: load, coverage, legacy, scan ({len(adopted)} adopted), keys, imports")
    return 1 if out else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
