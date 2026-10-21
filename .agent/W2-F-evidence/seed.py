"""Seed w2fe_test for the W2-F unit-5 captures, through the ordinary W2 replay path only (no hand-seeded evidence).

cold <case>: W2-02 cold replay (registered path) -> attestation -> release upload -> W2-03 worker -> W2-04 drain.
ev <case>:   W2-05b EV replay -> EV worker -> authored tariff through the store path -> EV consequence worker.
Each run recreates the database (the replay harness refuses any name not ending in `_test`)."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend" / "tests"))
from _pytest.monkeypatch import MonkeyPatch  # noqa: E402

kind, case = sys.argv[1], sys.argv[2]
mp = MonkeyPatch()
if kind == "cold":
    import test_w202_cold_replay_postgres as replay
    from test_w203_cold_replay_postgres import attest, run
    from test_w204_cold_consequence import drain

    replay.hold_uuids(mp, replay.CASES.index(case) + 1)
    built = replay.Chain(case, Path(tempfile.mkdtemp()) / case).open()
    attest(built)
    built.start_release_upload()
    run(built)
    drain(built)
    print("seeded cold", case, built.tenant_id, built.site_id)
else:
    import test_w205b_ev_replay_postgres as replay
    from test_w206_ev_store_postgres import run_worker
    from test_w207_ev_money_postgres import golden_tariff, money

    replay.hold_uuids(mp, 0x0500 + replay.CASES.index(case) + 1)
    built = replay.Chain(case, Path(tempfile.mkdtemp()) / case).open()
    built.start_release_upload()
    run_worker(built)
    tariff = golden_tariff(built, idem="w2f-capture-tariff-1")
    print("seeded ev", case, built.tenant_id, built.site_id, "tariff", tariff, "money", money(built))
built.close()
