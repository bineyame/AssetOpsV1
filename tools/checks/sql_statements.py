"""Statement-level SQL write extractor for rule 8 (tools/checks/configuration-persistence.ps1), OPS-02.

Reads repo-relative Python paths (one per line) on stdin and prints a JSON array of write-shaped clauses:
{"path", "line", "kind", "text"}. The PowerShell rule applies the writer policy; this module only recognises
statements, so it stays table-agnostic and a new writer's tables are added to the policy tables, never here.

Recognition, all from the AST rather than source lines:
- every string expression is rendered whole: implicit concatenation, triple-quoted and escaped-newline text are a
  single constant; `+` chains, f-strings, `%`/`.format` templates and `"sep".join([...])` render their dynamic
  parts as `{?}`, so a dynamic target or SET list stays visibly unresolved instead of disappearing;
- SQL comments (`/* */`, `--`) become whitespace and whitespace collapses, so keywords split by comments,
  newlines or tabs read as one statement;
- a statement is split on `;` and then into clauses at each write head (INSERT INTO, UPDATE, DELETE FROM,
  TRUNCATE, MERGE INTO, COPY, CREATE/ALTER/DROP, GRANT), so a CTE or chained write is checked clause by clause;
  `DO UPDATE`, `THEN UPDATE|DELETE|INSERT` and row locks (`FOR [NO KEY] UPDATE`) stay inside their clause;
- SQLAlchemy Core `insert/update/delete(...)` (imported from sqlalchemy) and `<table>.insert/update/delete()`
  in a module that imports sqlalchemy's table constructors are synthesised into the equivalent SQL clause. A
  table or column that is not a literal renders as `{?}` so the policy refuses it.

String expression statements (docstrings and other no-op literals) are not executable and are skipped. The
script exits non-zero on a parse error: the guard fails hard rather than skipping a module.
"""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

UNKNOWN = "{?}"
# A comment marker inside a '...', "..." or $$...$$ literal is text, not a comment.
_COMMENT = re.compile(r"""('[^']*(?:''[^']*)*'|"[^"]*(?:""[^"]*)*"|\$\$.*?\$\$)|/\*.*?\*/|--[^\n]*""", re.S)
_SPACE = re.compile(r"\s+")
# Write heads. Lookbehinds are fixed-width because whitespace is already collapsed to one space.
_HEAD = re.compile(
    r"(?i)(?<![\w.])(?<!\bDO )(?<!\bTHEN )(?<!\bFOR )(?<!\bKEY )(?<!\bAS )(?:UPDATE\b|INSERT\s+INTO\b|DELETE\s+FROM\b|DELETE\b|TRUNCATE\b|"
    r"MERGE\s+INTO\b|COPY\b|CREATE\b|ALTER\b|DROP\b|GRANT\b)")
_CORE_VERBS = {"insert", "update", "delete"}
_TABLE_CTORS = {"table", "Table"}


def normalize(sql: str) -> str:
    sql = _COMMENT.sub(lambda m: m.group(1) or " ", sql)
    return _SPACE.sub(" ", sql).strip()


def clauses(sql: str) -> list[str]:
    out: list[str] = []
    for statement in normalize(sql).split(";"):
        statement = statement.strip()
        heads = [m.start() for m in _HEAD.finditer(statement)]
        for i, start in enumerate(heads):
            end = heads[i + 1] if i + 1 < len(heads) else len(statement)
            clause = statement[start:end].strip()
            if clause:
                out.append(clause)
    return out


class Renderer:
    """Render a string-valued expression, recording every node it consumed."""

    def __init__(self) -> None:
        self.consumed: set[int] = set()

    def render(self, node: ast.AST) -> str | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, (str, bytes)):
            self.consumed.add(id(node))
            return node.value if isinstance(node.value, str) else node.value.decode("latin-1")
        if isinstance(node, ast.JoinedStr):
            self.consumed.add(id(node))
            parts = []
            for value in node.values:
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    self.consumed.add(id(value))
                    parts.append(value.value)
                else:
                    parts.append(UNKNOWN)
            return "".join(parts)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left, right = self.render(node.left), self.render(node.right)
            if left is None and right is None:
                return None
            self.consumed.add(id(node))
            return (left if left is not None else UNKNOWN) + (right if right is not None else UNKNOWN)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
            left = self.render(node.left)
            if left is not None:
                self.consumed.add(id(node))
            return left
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "format":
                base = self.render(node.func.value)
                if base is not None:
                    self.consumed.add(id(node))
                return base
            if node.func.attr == "join" and len(node.args) == 1:
                sep = self.render(node.func.value)
                if sep is None:
                    return None
                self.consumed.add(id(node))
                arg = node.args[0]
                if isinstance(arg, (ast.List, ast.Tuple)):
                    return sep.join(self.render(e) or UNKNOWN for e in arg.elts)
                return UNKNOWN
        return None


def _sqlalchemy_names(tree: ast.Module) -> tuple[dict[str, str], set[str], set[str]]:
    """Names bound to sqlalchemy verbs (bound name -> verb), to table constructors, and to sqlalchemy modules."""
    verbs: dict[str, str] = {}
    tables: set[str] = set()
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "sqlalchemy":
            for alias in node.names:
                bound = alias.asname or alias.name
                if alias.name in _CORE_VERBS:
                    verbs[bound] = alias.name
                elif alias.name in _TABLE_CTORS:
                    tables.add(bound)
                else:  # `from sqlalchemy.dialects import postgresql`, `from sqlalchemy import sql`: a namespace
                    modules.add(bound)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] == "sqlalchemy":
                    modules.add(alias.asname or alias.name.split(".")[0])
    return verbs, tables, modules


def _root(node: ast.AST) -> str | None:
    """The root name of a dotted chain: `sqlalchemy.dialects.postgresql` -> `sqlalchemy`."""
    while isinstance(node, ast.Attribute):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def _literal_table(node: ast.AST, tables: set[str], modules: set[str]) -> str | None:
    if not isinstance(node, ast.Call) or not node.args:
        return None
    func = node.func
    is_ctor = (isinstance(func, ast.Name) and func.id in tables) or (
        isinstance(func, ast.Attribute) and func.attr in _TABLE_CTORS and _root(func.value) in modules)
    first = node.args[0]
    if is_ctor and isinstance(first, ast.Constant) and isinstance(first.value, str):
        return first.value
    return None


def _core_clause(call: ast.Call, verb: str, table: str | None, parents: dict[int, ast.AST]) -> str:
    columns: list[str] | None = []
    where = upsert = False
    node: ast.AST = call
    while True:
        attr = parents.get(id(node))
        outer = parents.get(id(attr)) if attr is not None else None
        if not (isinstance(attr, ast.Attribute) and isinstance(outer, ast.Call) and outer.func is attr):
            break
        if attr.attr == "values" and columns is not None:
            for kw in outer.keywords:
                if kw.arg is None:
                    columns = None
                    break
                columns.append(kw.arg)
            for arg in outer.args if columns is not None else []:
                if isinstance(arg, ast.Dict) and all(
                        isinstance(k, ast.Constant) and isinstance(k.value, str) for k in arg.keys):
                    columns.extend(k.value for k in arg.keys)  # type: ignore[union-attr]
                else:
                    columns = None
                    break
        elif attr.attr in ("where", "filter", "filter_by"):
            where = True
        elif attr.attr.startswith("on_conflict_do_update"):
            upsert = True
        node = outer
    target = table if table and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table) else UNKNOWN
    cols = [UNKNOWN] if columns is None else columns
    if verb == "insert":
        text = f"INSERT INTO {target} ({', '.join(cols) if cols else UNKNOWN}) VALUES ({UNKNOWN})"
        return text + (" ON CONFLICT DO UPDATE SET " + UNKNOWN if upsert else "")
    if verb == "update":
        sets = ", ".join(f"{c} = :{c}" if c != UNKNOWN else UNKNOWN for c in cols) if cols else UNKNOWN
        return f"UPDATE {target} SET {sets}" + (" WHERE " + UNKNOWN if where else "")
    return f"DELETE FROM {target}" + (" WHERE " + UNKNOWN if where else "")


def extract(path: str, source: str) -> list[dict[str, object]]:
    tree = ast.parse(source, filename=path)
    parents: dict[int, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[id(child)] = parent
    verbs, tables, modules = _sqlalchemy_names(tree)
    renderer = Renderer()
    found: list[dict[str, object]] = []
    for node in ast.walk(tree):  # breadth-first: an enclosing expression renders before its parts
        if isinstance(node, ast.Call):
            func = node.func
            verb = None
            table = None
            if isinstance(func, ast.Name) and func.id in verbs:
                verb = verbs[func.id]
                table = _literal_table(node.args[0], tables, modules) if node.args else None
            elif isinstance(func, ast.Attribute) and func.attr in _CORE_VERBS:
                if _root(func.value) in modules:
                    verb = func.attr
                    table = _literal_table(node.args[0], tables, modules) if node.args else None
                elif (tables or modules) and not node.args and not node.keywords:
                    verb = func.attr  # <table>.insert()/update()/delete(); dict.update() always takes an argument
                    table = _literal_table(func.value, tables, modules)
            if verb is not None:
                for clause in clauses(_core_clause(node, verb, table, parents)):
                    found.append({"path": path, "line": node.lineno, "kind": "core", "text": clause})
        if id(node) in renderer.consumed:
            continue
        if isinstance(node, ast.Expr):
            renderer.render(node.value)  # a bare string statement (docstring) is never executed
            continue
        if not isinstance(node, ast.expr):
            continue
        rendered = renderer.render(node)
        if rendered is None:
            continue
        for clause in clauses(rendered):
            found.append({"path": path, "line": node.lineno, "kind": "string", "text": clause})
    return found


def main() -> int:
    root = Path.cwd()
    results: list[dict[str, object]] = []
    # PowerShell 5.1 prefixes native stdin with a UTF-8 BOM under a UTF-8 console code page.
    for raw in sys.stdin.buffer.read().decode("utf-8-sig").splitlines():
        rel = raw.strip().lstrip("﻿")
        if not rel:
            continue
        try:
            source = (root / rel).read_text(encoding="utf-8")
            results.extend(extract(rel, source))
        except (OSError, SyntaxError, UnicodeDecodeError) as exc:
            print(f"sql_statements: cannot read {rel}: {exc}", file=sys.stderr)
            return 2
    json.dump(results, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
