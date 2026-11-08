"""DIESEL-K9 (coordinator, carries from `.agent/followups-fuel-kisiwa-2026-11-07.md`): L0 tests of two
`tools/demo_combined_finish.py` call sites that otherwise only run inside a 2 h prepare.

- K6b review L4: `_kisiwa_fuel` hands the fuel store UUIDs (the window id and the tank asset id), never strings.
- K7-F review L1: `kis_10` reads the Kisiwa board on the outcome's Site-local day + 1 and the estate summary on a
  UTC-midnight window, and passes those bodies to `demo_rows.kis10`.

No database: psycopg and the two store builders are replaced by fakes.
"""

from __future__ import annotations

import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

import demo_combined_finish as finish  # noqa: E402

def _psycopg_import_gaps(source: str) -> list[str]:
    """R3u U4: names of the functions that use `psycopg` without `import psycopg` in their own body, plus a module-level
    `import psycopg` (the module has none, so a function that relies on one would raise NameError at run time)."""
    import ast

    tree = ast.parse(source)
    gaps = [f"<module>:{n.lineno}" for n in tree.body if isinstance(n, ast.Import) and any(a.name == "psycopg" for a in n.names)]
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        uses = any(isinstance(x, ast.Name) and x.id == "psycopg" for x in ast.walk(fn))
        imports = any(isinstance(x, ast.Import) and any(a.name == "psycopg" for a in x.names) for x in ast.walk(fn))
        if uses and not imports:
            gaps.append(fn.name)
    return gaps


def test_every_finish_function_using_psycopg_imports_it_locally_r3u() -> None:
    path = Path(finish.__file__)
    assert _psycopg_import_gaps(path.read_text(encoding="utf-8")) == []
    assert any("psycopg" in line for line in path.read_text(encoding="utf-8").splitlines())  # non-vacuous: it is used


def test_the_psycopg_import_guard_fails_on_the_rehearsal_shape_r3u() -> None:
    src = Path(finish.__file__).read_text(encoding="utf-8")
    start = src.index("def mill5(")
    planted = src[:start] + src[start:].replace("    import psycopg\n", "", 1)   # mill5's local import removed
    assert _psycopg_import_gaps(planted) == ["mill5"]
    assert _psycopg_import_gaps("import psycopg\n\ndef f():\n    psycopg.connect()\n") == ["<module>:1", "f"]


T, S, AID = UUID(int=1), UUID(int=2), UUID(int=3)
WINDOW_ID, TANK_ID = "00000000-0000-4000-8000-0000000000a1", "00000000-0000-4000-8000-0000000000b2"
RECORDED = datetime(2026, 10, 20, 9, 30, tzinfo=timezone.utc)  # 12:30 in Dar es Salaam, 20 Oct


class _Result:
    def __init__(self, row):
        self.row = row

    def fetchone(self):
        return self.row


class _Conn:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql: str, params=()):
        if "FROM site" in sql:
            return _Result((T, S))
        if "FROM domain_action" in sql:
            return _Result((AID,))
        if "FROM chain_action" in sql:
            return _Result(("action-thread",))
        if "finding_thread_occurrence" in sql:
            return _Result(("finding-thread",))
        raise AssertionError(sql)


class _Window:
    def __init__(self, night: date):
        self.night_date, self.revision, self.input_sha256 = night, 1, "sha"


class _FuelStore:
    def __init__(self):
        self.calls: list[tuple[str, tuple]] = []

    def window(self, t, s, window_id):
        self.calls.append(("window", (t, s, window_id)))
        return _Window(date(2026, 10, 14))

    def windows(self, t, s, tank, lo, hi, known_at):
        self.calls.append(("windows", (t, s, tank)))
        return (_Window(date(2026, 10, 14)),)

    def dispose(self):
        pass


class _ActionStore:
    def fuel_plan_context(self, t, s, aid):
        return {"plan": {"basis": {"tank_asset_id": TANK_ID},
                         "later_selection_rule": {"candidates": {"from": "2026-10-16T00:00:00+00:00"}}},
                "action": {"origin_finding_id": "f-1"}}

    def domain_outcomes(self, t, s, aid):
        return [{"details": {"baseline": {"window_id": WINDOW_ID}, "later": [{"window_id": WINDOW_ID}]},
                 "recorded_at": RECORDED}]

    def dispose(self):
        pass


def test_kisiwa_fuel_hands_the_store_uuids(monkeypatch: pytest.MonkeyPatch) -> None:
    import psycopg

    import assetops_backend.actions.composition as actions_comp
    import assetops_backend.fuel_balance.composition as fuel_comp

    fuel = _FuelStore()
    monkeypatch.setattr(psycopg, "connect", lambda *a, **k: _Conn())
    monkeypatch.setattr(actions_comp, "build_action_store", lambda url: _ActionStore())
    monkeypatch.setattr(fuel_comp, "build_fuel_balance_store", lambda url: fuel)
    ctx = finish.Ctx(client=None, work=Path("."), url="postgresql+psycopg://x/y_test")
    out = finish._kisiwa_fuel(ctx)
    assert out is not None and fuel.calls
    for name, (_t, _s, ident) in fuel.calls:
        assert isinstance(ident, UUID), (name, type(ident))  # fails if either `UUID(str(...))` wrap is dropped
    assert {(n, str(i[2])) for n, i in fuel.calls} == {("window", WINDOW_ID), ("windows", TANK_ID)}


class _Ctx(finish.Ctx):
    def get(self, path: str, **params) -> dict:
        self.reads.append((path, params))
        if path.endswith("/outcome-board"):
            return {"site_code": finish.KISIWA, "rows": []}
        return {"cards": {"ASSURE_PERFORMANCE": {"value_lines": ["mill line"]}}}


def test_kis_10_reads_the_board_day_and_a_utc_midnight_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _Ctx(client=None, work=Path("."))
    ctx.reads = []
    ctx.cache["kisiwa_fuel"] = {
        "fc": {"action": {"timezone": "Africa/Dar_es_Salaam", "action_code": "ACT-000004"},
               "applied": {"occurred_at": "x"}, "origin_window_id": WINDOW_ID},
        "outcome": {"recorded_at": RECORDED}, "plan": {"p": 1}, "action_thread": "a", "finding_thread": "f"}
    seen = {}
    monkeypatch.setattr(finish.demo_rows, "kis10", lambda *a: seen.setdefault("args", a) and {"ok": True})
    assert finish.kis_10(ctx) == {"kisiwa": "present", "ok": True}
    (board_path, board_q), (summary_path, summary_q) = ctx.reads
    # the board: the outcome's Site-local day + 1 (21 Oct in Dar es Salaam opens at 20 Oct 21:00Z)
    assert board_path == f"/api/sites/{finish.KISIWA}/outcome-board"
    assert board_q == {"from": "2026-10-20T21:00:00Z", "to": "2026-10-21T21:00:00Z"}
    # the summary: UTC midnights only (the estate routes refuse any other bound)
    assert summary_path == "/api/estate/outcome-summary"
    for bound in (summary_q["from"], summary_q["to"]):
        assert bound.endswith("T00:00:00Z"), summary_q
    assert summary_q == {"from": "2026-10-14T00:00:00Z", "to": "2026-10-22T00:00:00Z"}
    args = seen["args"]
    assert args[6] == {"site_code": finish.KISIWA, "rows": []} and args[7] == "ACT-000004" and args[8] == ["mill line"]
    assert args[0] == {"p": 1} and args[3] == WINDOW_ID and (args[4], args[5]) == ("a", "f")
