"""Seed w206g_test with one W2-05b replay through the registered path and the EV worker (capture only)."""
import sys, tempfile
from pathlib import Path
sys.path.insert(0, r"C:\Users\assef\Bineyame\AssetOpsV1-review5\backend\tests")
from _pytest.monkeypatch import MonkeyPatch
import test_w205b_ev_replay_postgres as replay
from test_w206_ev_store_postgres import run_worker

case = sys.argv[1] if len(sys.argv) > 1 else "interrupted"
mp = MonkeyPatch()
replay.hold_uuids(mp, 0x0500 + replay.CASES.index(case) + 1)
built = replay.Chain(case, Path(tempfile.mkdtemp()) / case).open()
built.start_release_upload()
run_worker(built)
print("seeded", case, built.tenant_id, built.site_id)
built.close()
