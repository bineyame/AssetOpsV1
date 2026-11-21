"""DDR (spec §4, tests 6 memory half and 7; no database). Tests 8(a)-(g) join this file with the checker's gates."""
from __future__ import annotations

import hashlib
import importlib.util
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from assetops_backend.structure_snapshot.store import MemoryStructureSnapshotStore

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "ddr"


def _generator():
    spec = importlib.util.spec_from_file_location("make_board_budget_ddr", FIXTURES / "make_board_budget.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_7_the_generator_writes_the_committed_bytes(tmp_path, capsys) -> None:
    written = _generator().main(tmp_path)
    capsys.readouterr()
    committed = (FIXTURES / "ddr-board-budget.xlsx").read_bytes()
    assert written.read_bytes() == committed
    assert hashlib.sha256(committed).hexdigest() == "2f629a1fc77a087932dbf565969b67ddd290395dcfb010a214782dd62576ad75"


def test_6_portfolio_history_is_every_portfolio_row_by_as_of_memory() -> None:

    store = MemoryStructureSnapshotStore()
    tenant = uuid4()
    at = datetime(2026, 11, 20, 8, 0, tzinfo=timezone.utc)
    base = _row_like(store, tenant, at)
    later = replace(base, id=uuid4(), as_of=at + timedelta(hours=1))
    site_row = replace(base, id=uuid4(), site_id=uuid4())
    store.rows.extend([later, site_row, base])
    assert [r.as_of for r in store.portfolio_history(tenant, "2026-10")] == [at, at + timedelta(hours=1)]
    assert store.portfolio_history(tenant, "2026-09") == ()


def _row_like(store, tenant, at):
    from assetops_backend.structure_snapshot.model import SnapshotRow
    fields = {name: None for name in SnapshotRow.__dataclass_fields__}
    fields.update(id=uuid4(), tenant_id=tenant, site_id=None, period="2026-10", as_of=at)
    return SnapshotRow(**fields)
