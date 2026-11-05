"""CH-5c W6 (CH5c-R4 §8.1, R5-2): the listener guard over the relations a stored route reads.

    python tools/chain_watermark_guard.py --database-url <clone url> --work <work dir> [--out <json>]

Every statement a stored route runs is captured (`before_cursor_execute`). Each FROM/JOIN target is resolved in the
database: a CTE name of the same statement is local; a table is a base table; a view or materialized view resolves
through `pg_rewrite`/`pg_depend` to its base tables, recursively. A target that is none of these fails the guard
(`unresolved`). Every base table read must carry the four W2 change triggers (INSERT, UPDATE, DELETE, TRUNCATE),
read from `pg_trigger`, not from the declared list; one that does not fails it (`untracked`). No W1 count term is
in use (migration 0047 triggers every input), so W2 is the only accepted coverage. The store's own tables
(`chain_response`, `chain_input_change`) are exempt: the response store reads them outside the compose.

The CLI drives the pre-built route list (`config/chain/prebuilt-routes-v1.json`, `assetops_backend.chain.prebuilt`)
plus each Portfolio's scope-ids sub-route through the in-process app, and prints the read set, the failures and
whether `event_consumption` is read (R5-2: it may be excluded only if no stored route reads it).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Iterable

TOOLS = Path(__file__).resolve().parent
EXEMPT = frozenset({"chain_response", "chain_input_change"})
#: tgtype bits: 4 INSERT, 8 DELETE, 16 UPDATE, 32 TRUNCATE.
ALL_FOUR = 4 | 8 | 16 | 32
_TARGET = re.compile(r"(?<![A-Za-z0-9_.])(?P<kw>FROM|JOIN)\s+(?:ONLY\s+)?(?:(?P<schema>[A-Za-z_][A-Za-z0-9_]*)\.)?"
                     r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?P<tail>\s*[(.])?", re.I)
#: CH5c-R7 L3: one more item of a comma-joined FROM list after a relation and its optional alias.
_ALIAS = re.compile(r"\s+(?:AS\s+)?(?!(?:WHERE|JOIN|LEFT|RIGHT|INNER|FULL|CROSS|ON|GROUP|ORDER|LIMIT|UNION|WINDOW|"
                    r"HAVING|FOR|OFFSET|USING|NATURAL)\b)[A-Za-z_][A-Za-z0-9_]*", re.I)
_NEXT = re.compile(r"\s*,\s*(?:ONLY\s+)?(?:(?P<schema>[A-Za-z_][A-Za-z0-9_]*)\.)?(?P<name>[A-Za-z_][A-Za-z0-9_]*)"
                   r"(?P<tail>\s*[(.])?", re.I)
#: CH5c-R7 C3: the SQL wall-clock functions.
CLOCK_SQL = re.compile(r"\b(now\s*\(|clock_timestamp\s*\(|statement_timestamp\s*\(|transaction_timestamp\s*\(|"
                       r"current_date\b|current_timestamp\b|localtimestamp\b)", re.I)
_PREDICATE = re.compile(r"\b(WHERE|ON|HAVING)\b", re.I)
_CTE = re.compile(r"(?:\bWITH(?:\s+RECURSIVE)?|,)\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?:\([^()]*\)\s*)?AS\s+"
                  r"(?:NOT\s+)?(?:MATERIALIZED\s+)?\(", re.I)
#: Words a FROM can introduce that are not relations (`EXTRACT(x FROM y)`, `IS DISTINCT FROM y`, `FROM LATERAL`).
_NOT_RELATION_BEFORE = re.compile(r"(?:\bDISTINCT|\bEXTRACT\s*\(\s*\w+|\bBOTH|\bLEADING|\bTRAILING)\s*$", re.I)
_KEYWORDS = frozenset({"lateral", "select", "values", "rows"})


def targets(statement: str) -> set[str]:
    """The relation names a statement reads: FROM/JOIN targets that are not functions, columns, CTEs or keywords."""
    ctes = {m.lower() for m in _CTE.findall(statement)}
    out: set[str] = set()
    for m in _TARGET.finditer(statement):
        if m.group("tail") or m.group("name").lower() in _KEYWORDS:
            continue  # a function call `FROM f(...)` or a qualified column `FROM x.col`
        if m.group("kw").upper() == "FROM" and _NOT_RELATION_BEFORE.search(statement[:m.start()]):
            continue
        name = m.group("name").lower()
        if name not in ctes:
            out.add(name)
        if m.group("kw").upper() != "FROM":
            continue
        pos = m.end()
        while True:  # L3: `FROM a x, b y, c` names every relation of the list
            alias = _ALIAS.match(statement, pos)
            nxt = _NEXT.match(statement, alias.end() if alias else pos)
            if nxt is None or nxt.group("tail") or nxt.group("name").lower() in _KEYWORDS:
                break
            if nxt.group("name").lower() not in ctes:
                out.add(nxt.group("name").lower())
            pos = nxt.end()
    return out


def clock_in_predicate(statement: str) -> bool:
    """C3 listener rule: a SQL clock function after the statement's first WHERE/ON/HAVING (a predicate). A clock
    function in a select list (a read-instant capture) passes. Named residual: a clock in a sub-select's select
    list after a WHERE also counts (the safe direction)."""
    first = _PREDICATE.search(statement)
    return first is not None and CLOCK_SQL.search(statement, first.end()) is not None


#: CH5c-R7 F4 / CH5c2-R1 Q3: the audit events a compose may not raise outside the allowed path set.
_PATH_EVENTS = frozenset({"open", "os.listdir", "os.scandir"})
MODULES_FILE = TOOLS.parent / "config" / "chain" / "stored-composer-modules-v1.json"


def _norm(path: Any) -> str | None:
    if isinstance(path, int):
        return None  # an fd: its open was audited already
    if isinstance(path, bytes):
        path = os.fsdecode(path)
    return os.path.normcase(os.path.abspath(os.fspath(path)))


class ComposeAudit:
    """F4 + Q5, test-only. While a stored-route compose runs (`read_scope.COMPOSING` set), record every `open`,
    `os.listdir` or `os.scandir` of a path outside the allowed set (declared file-input roots, the `code_version`
    file set, the installed runtime) and every `socket.connect` (the DB driver connects in C, so any Python
    connect is a violation); and record the backend modules whose code runs (`sys.monitoring` PY_START). It
    records, never raises. An audit hook cannot be removed: `__exit__` deactivates it."""

    _active: "ComposeAudit | None" = None
    _installed = False

    def __init__(self) -> None:
        import site

        from assetops_backend import read_scope
        from assetops_backend.chain.adapters import file_inputs
        from assetops_backend.chain.watermark import MANIFEST_ENV

        root = TOOLS.parent
        allowed: list[Any] = list(file_inputs.prefixes())
        allowed += [root / "backend" / "assetops_backend", root / "backend" / "migrations", root / "config",
                    root / "host", root / "contracts", sys.prefix, sys.base_prefix, sys.exec_prefix,
                    *site.getsitepackages()]
        allowed += [os.environ[n] for n in MANIFEST_ENV if os.environ.get(n)]
        self.allowed = sorted({p for p in (_norm(a) for a in allowed) if p})
        self._backend = (_norm(root / "backend") or "") + os.sep
        self._composing = read_scope.COMPOSING
        self.violations: list[dict[str, str]] = []
        self.modules: set[str] = set()
        self._busy = False

    def _ok(self, path: str) -> bool:
        return any(path == a or path.startswith(a.rstrip(os.sep) + os.sep) for a in self.allowed)

    @staticmethod
    def _hook(event: str, args: tuple[Any, ...]) -> None:
        self = ComposeAudit._active
        if self is None or self._busy or (event not in _PATH_EVENTS and event != "socket.connect"):
            return
        route = self._composing.get()
        if route is None:
            return
        self._busy = True
        try:
            if event == "socket.connect":
                self.violations.append({"route": route, "event": event, "target": repr(args[1])[:200]})
                return
            path = _norm(args[0]) if args and args[0] is not None else _norm(".")
            if path is not None and not self._ok(path):
                self.violations.append({"route": route, "event": event, "target": path})
        finally:
            self._busy = False

    def _start(self, code: Any, offset: int) -> Any:  # noqa: ARG002
        if self._composing.get() is None:
            return None
        name = os.path.normcase(code.co_filename)
        if name.startswith(self._backend):
            rel = name[len(self._backend):]
            if rel.endswith(".py"):
                self.modules.add(rel[:-3].replace(os.sep, ".").removesuffix(".__init__"))
        return sys.monitoring.DISABLE  # recorded once; a compose-only code location needs no more events

    def __enter__(self) -> "ComposeAudit":
        if not ComposeAudit._installed:
            sys.addaudithook(ComposeAudit._hook)
            ComposeAudit._installed = True
        ComposeAudit._active = self
        tool = sys.monitoring.PROFILER_ID
        sys.monitoring.use_tool_id(tool, "assetops-compose-audit")
        sys.monitoring.register_callback(tool, sys.monitoring.events.PY_START, self._start)
        sys.monitoring.set_events(tool, sys.monitoring.events.PY_START)
        return self

    def __exit__(self, *exc: Any) -> None:
        tool = sys.monitoring.PROFILER_ID
        sys.monitoring.set_events(tool, 0)
        sys.monitoring.register_callback(tool, sys.monitoring.events.PY_START, None)
        sys.monitoring.free_tool_id(tool)
        sys.monitoring.restart_events()
        ComposeAudit._active = None


def listed_modules() -> list[str]:
    return json.loads(MODULES_FILE.read_text(encoding="utf-8"))["modules"]


def _kind(c: Any, name: str) -> str | None:
    from sqlalchemy import text

    return c.execute(text("SELECT c.relkind::text FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
                          "WHERE c.relname = :n AND n.nspname = current_schema()"), {"n": name}).scalar()


def _view_bases(c: Any, name: str) -> set[str]:
    from sqlalchemy import text

    return {r[0] for r in c.execute(text(
        "SELECT DISTINCT r.relname FROM pg_rewrite w "
        "JOIN pg_depend d ON d.classid = 'pg_rewrite'::regclass AND d.objid = w.oid "
        "AND d.refclassid = 'pg_class'::regclass "
        "JOIN pg_class r ON r.oid = d.refobjid "
        "WHERE w.ev_class = (SELECT c.oid FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE c.relname = :n AND n.nspname = current_schema()) AND d.refobjid <> w.ev_class"), {"n": name})}


def resolve(c: Any, names: Iterable[str]) -> tuple[set[str], set[str]]:
    """(base tables, unresolved names); views are expanded recursively through `pg_rewrite`/`pg_depend`."""
    bases: set[str] = set()
    unresolved: set[str] = set()
    seen: set[str] = set()
    todo = list(names)
    while todo:
        name = todo.pop()
        if name in seen:
            continue
        seen.add(name)
        kind = _kind(c, name)
        if kind in ("r", "p"):
            bases.add(name)
        elif kind in ("v", "m"):
            inner = _view_bases(c, name)
            if not inner:
                unresolved.add(name)
            todo.extend(inner)
        else:
            unresolved.add(name)
    return bases, unresolved


def triggered(c: Any) -> dict[str, int]:
    """Per table, the OR of the event bits of its W2 change triggers, from `pg_trigger`."""
    from sqlalchemy import text

    events: dict[str, int] = {}
    for table, tgtype in c.execute(text(
            "SELECT c.relname, t.tgtype FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid "
            "JOIN pg_proc p ON p.oid = t.tgfoid "
            "WHERE NOT t.tgisinternal AND p.proname LIKE 'chain\\_input\\_change\\_%'")):
        events[table] = events.get(table, 0) | (int(tgtype) & ALL_FOUR)
    return events


def check(c: Any, statements: Iterable[str]) -> dict[str, Any]:
    """The W6 verdict over captured statements, on connection `c`."""
    names: set[str] = set()
    for s in statements:
        names |= targets(s)
    bases, unresolved = resolve(c, names - EXEMPT)
    bases -= EXEMPT
    events = triggered(c)
    untracked = sorted(t for t in bases if events.get(t) != ALL_FOUR)
    return {"read": sorted(bases), "unresolved": sorted(unresolved), "untracked": untracked,
            "event_consumption_read": "event_consumption" in bases,
            "ok": not unresolved and not untracked}


def _run(url: str, work: Path) -> dict[str, Any]:
    sys.path.insert(0, str(TOOLS))
    from sqlalchemy import create_engine, event
    from sqlalchemy.engine import Engine

    from assetops_backend import read_scope
    from assetops_backend.chain.composition import prebuilt_requests
    from demo_combined_finish import app_client

    captured: dict[str, list[str]] = {}
    clock_predicates: list[dict[str, str]] = []
    current: dict[str, str | None] = {"route": None}

    def listener(conn, cursor, statement, params, context, many):  # noqa: ANN001
        if current["route"] is not None:
            captured.setdefault(current["route"], []).append(statement)
        if read_scope.COMPOSING.get() is not None and clock_in_predicate(statement):
            clock_predicates.append({"route": str(read_scope.COMPOSING.get()), "statement": statement[:400]})

    event.listen(Engine, "before_cursor_execute", listener)
    # CH-5c2: every request composes inside the compose scope (so F4, Q5 and C3 see it) and nothing is stored.
    os.environ["ASSETOPS_RESPONSE_STORE"] = "compose"
    client = app_client(url, work)
    requests = prebuilt_requests()
    statuses = {}
    audit = ComposeAudit()
    try:
        with audit:
            for req in requests:
                for path in (req.path, *(("/api/estate/portfolio/scope-ids",) if req.path == "/api/estate/portfolio"
                                         else ())):
                    current["route"] = path
                    statuses[f"{path}?{req.query}"] = client.get(f"{path}?{req.query}").status_code
                    current["route"] = None
            # The dateless board reads its day from the DB clock (`site_overview.read.db_today`, a read_instant
            # capture), so each board Site is also requested without `date=` (CH-5c2 Q5: `db_today` is exercised).
            for path in sorted({r.path for r in requests if r.path.endswith("/outcome-board")}):
                current["route"] = path
                statuses[f"{path}?"] = client.get(path).status_code
                current["route"] = None
    finally:
        event.remove(Engine, "before_cursor_execute", listener)
    engine = create_engine(url)
    try:
        with engine.connect() as c:
            per_route = {route: check(c, stmts) for route, stmts in captured.items()}
            total = check(c, [s for stmts in captured.values() for s in stmts])
    finally:
        engine.dispose()
    listed = set(listed_modules())
    unlisted = sorted(audit.modules - listed)
    total["clock_predicates"] = clock_predicates
    total["file_violations"] = audit.violations
    total["unlisted_modules"] = unlisted
    total["ok"] = total["ok"] and not clock_predicates and not audit.violations and not unlisted
    return {"requests": len(statuses), "non_200": {k: v for k, v in statuses.items() if v != 200},
            "routes": per_route, "all": total, "modules": sorted(audit.modules)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--work", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--modules-out", type=Path,
                        help="write the observed module list (for a reviewed diff of the committed list, Q5)")
    args = parser.parse_args(argv)
    result = _run(args.database_url, args.work)
    text_out = json.dumps(result, indent=1, sort_keys=True)
    if args.out:
        args.out.write_text(text_out, encoding="utf-8")
    if args.modules_out:
        args.modules_out.write_text(json.dumps({"modules": result["modules"]}, indent=1) + "\n", encoding="utf-8")
    total = result["all"]
    print(f"requests {result['requests']} non-200 {len(result['non_200'])} tables read {len(total['read'])} "
          f"unresolved {total['unresolved']} untracked {total['untracked']} "
          f"event_consumption_read {total['event_consumption_read']} clock_predicates {len(total['clock_predicates'])} "
          f"file_violations {len(total['file_violations'])} modules {len(result['modules'])} "
          f"unlisted_modules {total['unlisted_modules']}")
    return 0 if total["ok"] and not result["non_200"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
