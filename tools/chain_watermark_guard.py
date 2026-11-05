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
_TARGET = re.compile(r"(?<![A-Za-z0-9_.])(?P<kw>FROM|JOIN)\s+(?:ONLY\s+)?(?P<name>[A-Za-z_][A-Za-z0-9_]*)"
                     r"(?P<tail>\s*[(.])?", re.I)
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
    return out


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

    from assetops_backend.chain.composition import prebuilt_requests
    from demo_combined_finish import app_client

    captured: dict[str, list[str]] = {}
    current: dict[str, str | None] = {"route": None}

    def listener(conn, cursor, statement, params, context, many):  # noqa: ANN001
        if current["route"] is not None:
            captured.setdefault(current["route"], []).append(statement)

    event.listen(Engine, "before_cursor_execute", listener)
    os.environ["ASSETOPS_RESPONSE_STORE"] = "off"  # every request composes, so its reads are captured
    client = app_client(url, work)
    requests = prebuilt_requests()
    statuses = {}
    try:
        for req in requests:
            for path in (req.path, *(("/api/estate/portfolio/scope-ids",) if req.path == "/api/estate/portfolio"
                                     else ())):
                current["route"] = path
                statuses[f"{path}?{req.query}"] = client.get(f"{path}?{req.query}").status_code
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
    return {"requests": len(statuses), "non_200": {k: v for k, v in statuses.items() if v != 200},
            "routes": per_route, "all": total}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--work", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    result = _run(args.database_url, args.work)
    text_out = json.dumps(result, indent=1, sort_keys=True)
    if args.out:
        args.out.write_text(text_out, encoding="utf-8")
    total = result["all"]
    print(f"requests {result['requests']} non-200 {len(result['non_200'])} tables read {len(total['read'])} "
          f"unresolved {total['unresolved']} untracked {total['untracked']} "
          f"event_consumption_read {total['event_consumption_read']}")
    return 0 if total["ok"] and not result["non_200"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
