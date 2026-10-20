"""Seed w207i_test: one W2-05b replay via the registered path, the EV worker, an authored tariff through the
existing publication API path and the EV consequence worker (W2-07 capture only)."""
import sys, tempfile
from pathlib import Path
sys.path.insert(0, r"C:\Users\assef\Bineyame\AssetOpsV1-review5\backend\tests")
from _pytest.monkeypatch import MonkeyPatch
import test_w205b_ev_replay_postgres as replay
from test_w206_ev_store_postgres import run_worker
from test_w207_ev_money_postgres import golden_tariff, money

case = sys.argv[1] if len(sys.argv) > 1 else "interrupted"
mp = MonkeyPatch()
replay.hold_uuids(mp, 0x0500 + replay.CASES.index(case) + 1)
built = replay.Chain(case, Path(tempfile.mkdtemp()) / case).open()
built.start_release_upload()
run_worker(built)
tariff = golden_tariff(built, idem="w207-capture-tariff-1")
rows = money(built)
print("seeded", case, built.tenant_id, built.site_id, "tariff", tariff, "money", rows)
built.close()
