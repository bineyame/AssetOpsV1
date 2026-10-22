"""W3-02 commit 2 capture harness (copied from W3-01 commit 4) (capture-scoped, not product code).

Seeds the private `w302j_test` DB through the ordinary replay paths, then serves the real `create_app()` on
127.0.0.1:9751 in this process:

* KOBO-001 (mini-grid): the S4 F01 + F02 chain and the S6 Action chain (accepted, applied, plan frozen, bound) on
  the S4 fixture clock (`test_w301_estate_index_postgres.py::test_action_event_and_verification_counts_full_basis`).
* COLD-LAB-001: the W2-02 `late-reading` replay, settled (W2-03 worker).
* EV-LAB-001: the W2-05b `interrupted` replay, settled, with the W2-07 golden tariff and EV consequence worker.
* FOREIGN-001: a Site copied under a second tenant (never authorized for the `demo` tenant).

As in the golden `mixed` branch, every chain shares this one DB and the `demo` tenant, and the imports are re-dated
before 2026-10-05 (`imported_before`). The estate read clock is pinned TEST-SCOPED (`pin_read_at`) to the S4 fixture
present and then flows with wall time, so live page two reads land after the cursor cutoff.

Capture-only control endpoints (POST): `/__capture/empty-site` adds the no-selection `W301-EMPTY-001`;
`/__capture/late-kobo` delivers one late accepted KOBO reading on the F01 day (2026-10-06) through the S4 runner at
the next fixture minute, without assessing it (open job -> PENDING_RECOMPUTE), and moves the pinned present past it;
`/__capture/clock` returns the pinned present.
"""
import os
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

WT = Path(__file__).resolve().parents[2]
URL = "postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/w302j_test"
os.environ["ASSETOPS_TEST_DATABASE_URL"] = URL
os.environ["DATABASE_URL"] = URL
os.environ["ASSETOPS_TEST_TEMPLATE"] = "0"
sys.path.insert(0, str(WT / "backend" / "tests"))
os.chdir(WT)

from _pytest.monkeypatch import MonkeyPatch  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402

import pg_harness  # noqa: E402
import test_w202_cold_replay_postgres as w202  # noqa: E402
import test_w205b_ev_replay_postgres as w205b  # noqa: E402
from test_s4_finding_store_postgres import CaseRunner, run_case  # noqa: E402
from test_s6_action_store_postgres import CASES as S4_CASES  # noqa: E402
from test_s6_verification_evaluator_postgres import bound_plan, complete_windows, verifying  # noqa: E402
from test_w203_cold_replay_postgres import opened, run  # noqa: E402
from test_w206_ev_store_postgres import run_worker  # noqa: E402
from test_w207_ev_money_postgres import golden_tariff, money  # noqa: E402
from test_w301_estate_index_postgres import add_empty_site, db_now, imported_before, pin_read_at  # noqa: E402

from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore  # noqa: E402

mp = MonkeyPatch()
tmp = Path(tempfile.mkdtemp(prefix="w302j-"))
fresh = pg_harness.fresh_database()
mp.setattr(pg_harness, "fresh_database", lambda: fresh)

w202.hold_uuids(mp, w202.CASES.index("late-reading") + 1)
cold = w202.Chain("late-reading", tmp / "cold").open()
from test_w203_cold_replay_postgres import attest  # noqa: E402
attest(cold)
cold.start_release_upload()
run(cold)
print("cold settled", cold.tenant_id, cold.site_id, flush=True)
cold_settled_at = db_now(cold.engine)

w205b.hold_uuids(mp, 0x0500 + w205b.CASES.index("interrupted") + 1)
ev = w205b.Chain("interrupted", tmp / "ev").open()
ev.start_release_upload()
run_worker(ev)
tariff = golden_tariff(ev, idem="w301-capture-tariff-1")
money_rows = money(ev)
print("ev settled", ev.site_id, "tariff", tariff, "money", money_rows, flush=True)

store = PostgresFoundationStore(URL)
eng = create_engine(URL)
runner = CaseRunner(store, eng)
run_case(runner, S4_CASES["F01"])
run_case(runner, S4_CASES["F02"])
h = verifying(runner)
complete_windows(mp, h)
action_id, plan, binding = bound_plan(runner, h)
print("kobo action", action_id, "plan", plan["plan_id"], flush=True)

for site_id in (cold.site_id, ev.site_id, runner.site):
    imported_before(eng, runner.tenant, site_id, datetime(2026, 10, 4, tzinfo=timezone.utc))

# FOREIGN-001: a second tenant with its own imported Site (copied rows, new identities).
foreign_tenant = str(uuid4())
with eng.begin() as c:
    def copy(table: str, where: str, params: dict, pick: dict) -> None:
        cols = [r[0] for r in c.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = :t ORDER BY ordinal_position"),
            {"t": table})]
        c.execute(text(f"INSERT INTO {table} ({', '.join(cols)}) SELECT {', '.join(pick.get(x, x) for x in cols)} "
                       f"FROM {table} WHERE {where}"), params)
    tcols = [r[0] for r in c.execute(text(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'tenant'"))]
    tpick = {"id": "CAST(:ft AS uuid)"}
    for k in ("slug", "slug_key", "name", "display_name"):
        if k in tcols:
            tpick[k] = "'w301-foreign'"
    copy("tenant", "id = :t", {"ft": foreign_tenant, "t": str(runner.tenant)}, tpick)
    foreign_site = str(uuid4())
    copy("site", "id = :s", {"fs": foreign_site, "ft": foreign_tenant, "s": str(runner.site)},
         {"id": "CAST(:fs AS uuid)", "tenant_id": "CAST(:ft AS uuid)", "site_code": "'FOREIGN-001'",
          "site_code_key": "'foreign-001'", "name": "'Foreign tenant Site'"})
    copy("site_import", "site_id = :s", {"fi": str(uuid4()), "fs": foreign_site, "ft": foreign_tenant,
                                         "s": str(runner.site)},
         {"id": "CAST(:fi AS uuid)", "site_id": "CAST(:fs AS uuid)", "tenant_id": "CAST(:ft AS uuid)"})
print("foreign", foreign_tenant, foreign_site, flush=True)

state = {"base": max(max(h.clock.at, runner.now) + timedelta(minutes=1), db_now(eng)), "t0": time.monotonic()}


def present() -> datetime:
    return state["base"] + timedelta(seconds=time.monotonic() - state["t0"])


pin_read_at(mp, present)
# W3-02: the Evidence read runs on `EvidenceMoneySnapshot`, so pin its read time to the same fixture present
# (TEST-SCOPED, as `test_w302_evidence_scope_snapshot_postgres.py::mini` does); every query stays real.
from assetops_backend.estate.adapters import postgres_evidence_money_read as pemr  # noqa: E402

_RealEvidenceSnapshot = pemr.EvidenceMoneySnapshot


class _PinnedEvidenceSnapshot(_RealEvidenceSnapshot):
    def __init__(self, owner, c, read_at) -> None:
        super().__init__(owner, c, present())


mp.setattr(pemr, "EvidenceMoneySnapshot", _PinnedEvidenceSnapshot)
print("pinned present", present().isoformat(), "cold settled (db clock)", cold_settled_at.isoformat(), flush=True)

from fastapi import FastAPI  # noqa: E402
import uvicorn  # noqa: E402

from assetops_backend.main import create_app  # noqa: E402

app: FastAPI = create_app()
extra = {}


@app.post("/__capture/empty-site")
def empty_site() -> dict:
    extra["empty"] = add_empty_site(eng, runner.site, "W301-EMPTY-001")
    imported_before(eng, runner.tenant, extra["empty"], datetime(2026, 10, 4, tzinfo=timezone.utc))
    return {"site_id": extra["empty"], "at": present().isoformat()}


@app.post("/__capture/late-kobo")
def late_kobo() -> dict:
    before = present().replace(microsecond=0)
    decided = (before + timedelta(minutes=1)).replace(second=0)
    runner.step({"do": "deliver", "decided": decided.strftime("%Y-%m-%dT%H:%M:%SZ"),
                 "blocks": [{"from": "2026-10-06T10:00:00Z", "to": "2026-10-06T10:00:00Z", "soc": "50",
                             "only": ["soc"]}]})
    state["base"], state["t0"] = runner.now + timedelta(minutes=1), time.monotonic()
    return {"before": before.isoformat(), "decided": runner.now.isoformat(), "present": present().isoformat()}


@app.post("/__capture/clock")
def clock() -> dict:
    return {"present": present().isoformat(), "db_now": db_now(eng).isoformat(),
            "tenant": str(runner.tenant), "foreign_tenant": foreign_tenant, "foreign_site": foreign_site}


print("serving", flush=True)
uvicorn.run(app, host="127.0.0.1", port=9751, log_level="warning")
