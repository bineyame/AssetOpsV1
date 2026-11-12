"""CH-5c2 C3 static clock guard (L0, no database; CH5c-R7 C3, CH5c2-R1 Q1/Q5).

Over the stored-composer module set (`config/chain/stored-composer-modules-v1.json`, recorded by the W6 CLI and
changed only by a reviewed diff):

- no Python wall-clock read (`datetime.now`, `datetime.utcnow`, `date.today`, `time.time`, called or passed as a
  default) outside `read_scope.py`;
- no SQL clock function (`now()`, `clock_timestamp()`, ... , the W6 listener's `CLOCK_SQL`) in a string literal
  outside the named allowlist below. Each allowlisted site is a read-instant capture (its value is wrapped in
  `read_scope.read_instant`) or a writer that a stored compose never runs, keyed by (module, enclosing function).

A planted `datetime.now()` and a planted unlisted `now()` each fail the scan (non-vacuity, in this file).
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BACKEND = REPO / "backend"
sys.path.insert(0, str(REPO / "tools"))

from chain_watermark_guard import CLOCK_SQL  # noqa: E402

MODULES_FILE = REPO / "config" / "chain" / "stored-composer-modules-v1.json"

#: (module, enclosing function qualname) -> reason. Read-instant captures (CH5c2-R1 Q1, pre-flight §3) and the
#: writers that live in a composer module but never run in a stored compose (CH5c-R7 C3 "not in compose").
_CAPTURE = "read-instant capture: the snapshot's first statement, wrapped in read_scope.read_instant (Q1 §3)"
_WRITER = "writer: runs in a tick or a POST, never in a stored compose"
_B = "assetops_backend."
SQL_CLOCK_ALLOWLIST: dict[tuple[str, str], str] = {
    (_B + "analytics.adapters.postgres_assessment_store", "PostgresAssessmentStore.lease_mini_job.work"): _WRITER,
    (_B + "analytics.adapters.postgres_assessment_store", "PostgresAssessmentStore.fail_mini_job.work"): _WRITER,
    (_B + "analytics.adapters.postgres_assessment_store",
     "PostgresAssessmentStore.enqueue_opportunity_job.work"): _WRITER,
    (_B + "analytics.adapters.postgres_assessment_store",
     "PostgresAssessmentStore.lease_opportunity_job.work"): _WRITER,
    (_B + "analytics.adapters.postgres_assessment_store",
     "PostgresAssessmentStore.fail_opportunity_job.work"): _WRITER,
    (_B + "analytics.adapters.postgres_assessment_store", "PostgresAssessmentStore.dispatch_day_now.work"):
        "AR-3 row builder: the dispatch.day row is built as of its own read instant (D-ANY.5 as-built), in a"
        " worker, never in a stored compose",
    (_B + "analytics.adapters.postgres_assessment_store", "PostgresAssessmentStore._window_snapshot"): _CAPTURE,
    (_B + "analytics.adapters.postgres_assessment_store", "PostgresAssessmentStore._transaction_time"):
        _WRITER + " (the assessment write transaction's instant)",
    (_B + "chain.adapters.postgres_thread_sources", "PostgresThreadSources.lifecycle_inputs"): _CAPTURE,
    (_B + "estate.adapters.postgres_estate_read", "PostgresEstateRead.read"): _CAPTURE + "; L2 clock_timestamp()",
    (_B + "estate.adapters.postgres_evidence_money_read", "PostgresEvidenceMoneyRead.read"):
        _CAPTURE + "; L2 clock_timestamp()",
    (_B + "evidence.adapters.postgres_evidence_ledger", "PostgresEvidenceLedger.register_publication.work"): _WRITER,
    (_B + "evidence.adapters.postgres_evidence_ledger", "PostgresEvidenceLedger._decision_instant"):
        _WRITER + " (an evidence decision's instant)",
    (_B + "financials.adapters.postgres_assumption_store", "PostgresAssumptionStore.publish.work"): _WRITER,
    (_B + "financials.adapters.postgres_consequence_store", "PostgresConsequenceStore.append.work"): _WRITER,
    (_B + "financials.adapters.postgres_consequence_store", "PostgresConsequenceStore.db_now"):
        _WRITER + " (the scheduler's `now`: scheduling/tick.py, health.py)",
    (_B + "financials.adapters.postgres_consequence_store", "PostgresConsequenceStore.record_attempt.work"): _WRITER,
    (_B + "financials.adapters.postgres_consequence_store", "PostgresConsequenceStore.site_history.work"):
        "not in a stored compose: the consequence history route (financials.consequence_history, not in the set)",
    (_B + "financials.adapters.postgres_consequence_store", "_ev_attempt"): _WRITER,
    (_B + "financials.adapters.postgres_consequence_store", "EvUnit.__init__"): _WRITER + " (EV recompute unit)",
    (_B + "financials.adapters.postgres_consequence_store", "EvUnit.append"): _WRITER,
    (_B + "mini_depth.read", "MiniDepthRead._readonly"): _CAPTURE,
    (_B + "mini_depth.read", "MiniDepthRead.read"): _CAPTURE,
    (_B + "mini_depth.store", "PostgresMiniDepthStore._now"): _WRITER + " (the mini-depth job store)",
    # CH-9 merge: the default knowledge cutoff of a mini_decisions projection (`SELECT now()`), read by the
    # projection's writer-side callers; no stored-route composer calls it (W6 records 0 reads on the merged tree).
    (_B + "mini_depth.store", "database_now"): "not in a stored compose: a projection's default knowledge cutoff",
    (_B + "objectives.adapters.postgres_objective_store", "_insert_statement"):
        _WRITER + " (default recorded_at of the objective declaration INSERT; called only by PostgresObjectiveStore.declare)",
    # CH-5c2 (found by the F4/Q5 test on the real composers): a dateless board reads the board day from the
    # scheduler store's DB clock (`site_overview.read.db_today`); the rest of the store is the tick's writers.
    (_B + "scheduling.adapters.postgres_schedule_store", "PostgresScheduleStore.db_now"):
        "read-instant capture: the dateless board/overview day (`site_overview.read.db_today`), wrapped in "
        "read_scope.read_instant; it registers the next UTC midnight (C1)",
    **{(_B + "scheduling.adapters.postgres_schedule_store", "PostgresScheduleStore." + q):
       _WRITER + " (the tick's schedule store)"
       for q in ("claim_site.work", "claim_tick.work", "enrol.work", "fail_tick", "finish_tick", "record_s4",
                 "release_site", "set_cursor.work", "set_stage")},
    # DIESEL-K4b (R3j2 §9j2.5 item 1, found by the F4/Q5 test): the board now holds the fuel-balance store. Its board
    # read instant is K5's `night_context` capture; `transaction` (K3's assess) and `night_window_on` (K4a's raise)
    # are writers that a stored compose never calls.
    (_B + "fuel_balance.adapters.postgres_fuel_balance_store", "PostgresFuelBalanceStore.night_context.work"): _CAPTURE,
    (_B + "fuel_balance.adapters.postgres_fuel_balance_store", "PostgresFuelBalanceStore.transaction"):
        _WRITER + " (the fuel-balance assessment, K3)",
    (_B + "fuel_balance.adapters.postgres_fuel_balance_store", "PostgresFuelBalanceStore.schedule_inputs.work"):
        _WRITER + " (OWN-G2: the fuel_night tick stage's due-night read, scheduled.run_site; the same DB clock as "
        "`transaction`, which assesses each due night)",
    (_B + "fuel_balance.adapters.postgres_fuel_balance_store", "PostgresFuelBalanceStore.night_window_on"):
        _WRITER + " (the unexplained-fuel Finding raise, K4a)",
    (_B + "work.adapters.postgres_domain_action_index", "PostgresDomainActionRead.snapshot"): _CAPTURE,
    (_B + "work.adapters.postgres_global_read", "PostgresGlobalWorkRead.snapshot"): _CAPTURE,
    (_B + "work.adapters.postgres_work_read", "PostgresWorkRead.snapshot"): _CAPTURE,
}

#: Python clock reads allowed in composer modules: only the seam itself.
PY_CLOCK_MODULES = frozenset({"assetops_backend.read_scope"})

#: DRIFT-R1 2.3(a): Python clock reads allowed by (module, enclosing qualname), each with its reason.
PY_CLOCK_ALLOWLIST: dict[tuple[str, str], str] = {
    (_B + "financials.recompute", "_utc_now"):
        _WRITER + " (the recompute worker's default clock; only ConsequenceRecomputeWorker.run reads it; derive reads none)",
    (_B + "chain.period_read", "PeriodReader.__init__"):
        "the period read's default read-instant (`at = known_at or self._now()`), used only when the caller passes no"
        " known_at (CLEAN-1: the AR-3/AR-4 modules were missing from the module list; Architect to confirm the allowance)",
}

_PY_CLOCK_ATTRS = {("datetime", "now"), ("datetime", "utcnow"), ("date", "today"), ("time", "time")}


def listed_modules() -> list[str]:
    return json.loads(MODULES_FILE.read_text(encoding="utf-8"))["modules"]


def module_path(module: str) -> Path:
    base = BACKEND.joinpath(*module.split("."))
    return base / "__init__.py" if base.is_dir() else base.with_suffix(".py")


def _owner(node: ast.AST) -> str | None:
    """The trailing name of an attribute's value: `datetime` for `datetime.now` and `dt.datetime.now`."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def scan(source: str, module: str) -> tuple[list[tuple[str, str]], list[tuple[str, str, int]]]:
    """(python clock reads as (`module:line attr`, enclosing qualname), SQL clock literals as (module, qualname, line))."""
    tree = ast.parse(source)
    py: list[tuple[str, str]] = []
    sql: list[tuple[str, str, int]] = []

    # DRIFT-R1 2.3(b): a string used as an argument default is a statement fragment even without a keyword.
    defaults: set[int] = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            for d in [*n.args.defaults, *(k for k in n.args.kw_defaults if k is not None)]:
                if isinstance(d, ast.Constant) and isinstance(d.value, str):
                    defaults.add(id(d))

    docstrings = {id(n.body[0].value) for n in ast.walk(tree)
                  if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and n.body
                  and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant)}

    def visit(node: ast.AST, qual: str) -> None:
        for child in ast.iter_child_nodes(node):
            if id(child) in docstrings:
                continue
            name = qual
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = f"{qual}.{child.name}" if qual else child.name
            if isinstance(child, ast.Attribute) and (_owner(child.value), child.attr) in _PY_CLOCK_ATTRS:
                py.append((f"{module}:{child.lineno} {_owner(child.value)}.{child.attr}", qual or "<module>"))
            if isinstance(child, ast.Constant) and isinstance(child.value, str) and CLOCK_SQL.search(child.value):
                # Docstrings and comments-in-strings are prose, not SQL: only literals that look like a statement,
                # or that are an argument default (the fragment is interpolated into a statement elsewhere).
                if id(child) in defaults or any(
                        k in child.value.upper() for k in ("SELECT", "WHERE", "INSERT", "UPDATE", "VALUES", "SET ")):
                    sql.append((module, qual or "<module>", child.lineno))
            visit(child, name)

    visit(tree, "")
    return py, sql


def violations(modules: list[str], sources: dict[str, str] | None = None) -> list[str]:
    out: list[str] = []
    for module in modules:
        source = (sources or {}).get(module)
        if source is None:
            source = module_path(module).read_text(encoding="utf-8")
        py, sql = scan(source, module)
        if module not in PY_CLOCK_MODULES:
            out.extend(f"python clock {hit}" for hit, qual in py if (module, qual) not in PY_CLOCK_ALLOWLIST)
        out.extend(f"sql clock {m}:{line} in {q}" for m, q, line in sql if (m, q) not in SQL_CLOCK_ALLOWLIST)
    return out


def test_module_list_is_recorded_and_resolves() -> None:
    modules = listed_modules()
    assert modules, "the W6 CLI module list is empty: record it with --modules-out and review the diff"
    assert "assetops_backend.read_scope" in modules
    missing = [m for m in modules if not module_path(m).is_file()]
    assert missing == []


def test_composer_modules_have_no_unaccounted_clock_read() -> None:
    assert violations(listed_modules()) == []


def test_schedule_inputs_is_called_only_by_the_tick_stage() -> None:
    """D-E2.1: the `schedule_inputs` clock read is allow-listed as a writer; this makes that claim checkable."""
    callers = set()
    for path in sorted((BACKEND / "assetops_backend").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "schedule_inputs":
                callers.add(path.relative_to(BACKEND).as_posix())
    assert callers == {"assetops_backend/fuel_balance/scheduled.py"}
    assert "assetops_backend.fuel_balance.scheduled" not in listed_modules()


def test_allowlist_has_no_stale_entry() -> None:
    present = set()
    for module in listed_modules():
        present |= {(m, q) for m, q, _ in scan(module_path(module).read_text(encoding="utf-8"), module)[1]}
    assert sorted(set(SQL_CLOCK_ALLOWLIST) - present) == []
    py_present = set()
    for module in listed_modules():
        py_present |= {(module, q) for _, q in scan(module_path(module).read_text(encoding="utf-8"), module)[0]}
    assert sorted(set(PY_CLOCK_ALLOWLIST) - py_present) == []


def test_python_allowlist_is_keyed_by_function_and_still_catches_a_planted_clock() -> None:
    key = _B + "financials.recompute"
    assert violations([key]) == []  # the allowlisted `_utc_now` passes
    planted = "from datetime import datetime\ndef _utc_now():\n    return datetime.now()\n"
    assert violations(["assetops_backend.not_allowlisted"], {"assetops_backend.not_allowlisted": planted}) == [
        "python clock assetops_backend.not_allowlisted:3 datetime.now"]
    # the same function name in the allowlisted module is accepted, any other function there is not
    assert violations([key], {key: planted}) == []
    other = planted.replace("_utc_now", "_other")
    assert violations([key], {key: other}) == [f"python clock {key}:3 datetime.now"]


def test_default_argument_clock_literal_fails() -> None:
    assert violations(["m"], {"m": 'def f(c, at="now()"):\n    return c\n'}) == ["sql clock m:1 in f"]
    assert violations(["m"], {"m": 'f = lambda at="clock_timestamp()": at\n'}) == ["sql clock m:1 in <module>"]
    assert violations(["m"], {"m": 'def g(c):\n    return "now()"\n'}) == []  # a bare non-default prose literal stays quiet


def test_planted_python_clock_fails() -> None:
    module = "assetops_backend.chain.response_store"
    planted = module_path(module).read_text(encoding="utf-8") + "\n\ndef _planted():\n    return datetime.now()\n"
    assert any("python clock" in v and "datetime.now" in v for v in violations([module], {module: planted}))
    default = "import datetime\nclass X:\n    def __init__(self, clock=None):\n        self.clock = clock or datetime.datetime.utcnow\n"
    assert violations(["m"], {"m": default}) == ["python clock m:4 datetime.utcnow"]


def test_planted_sql_clock_fails() -> None:
    planted = 'def f(c):\n    return c.execute("SELECT 1 FROM t WHERE t.at <= now()")\n'
    assert violations(["m"], {"m": planted}) == ["sql clock m:2 in f"]
