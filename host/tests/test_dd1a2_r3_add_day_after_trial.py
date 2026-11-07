"""DD1a2-R3 (H1) L2: the live day after the Kobo trial. Own `*_test` DB. The child's trial chain on S+0 and S+1
(`demo_combined_kobo.build`, the trial entries only), then the prepare's own tick, then the live add on S+2:

  * `steady` on S+2 is refused by name (`FULL_DAY_AFTER_TRIAL`) before anything is provisioned (no new readings);
  * `normal` on S+2 is planned (`plan_add_runs`), delivered by the child's `add_day`, and the prepare's tick runs 3 times;
  * ACT-K1 reads VERIFIED through `VerificationService.current_state` before the add and after every tick.

The story clock is resolved one day earlier than the DB now, so S+2 has ended in real time whatever the hour the test
runs (the live demo adds the day right after it ends; the stored facts are the same). Fail: stop and report, never tune.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")


def _state(url: str, ids: dict, tenant_id, site_id) -> dict:
    from assetops_backend.actions.adapters.postgres_action_store import PostgresActionStore
    from assetops_backend.actions.composition import verification_ports
    from assetops_backend.actions.verification import VerificationService

    store = PostgresActionStore(url)
    try:
        actions = SimpleNamespace(store=store, clock=lambda: __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc), verification_ports=verification_ports(url))
        return VerificationService(actions).current_state(tenant_id, site_id, UUID(ids["action"]))
    finally:
        store.dispose() if hasattr(store, "dispose") else None


def _tick(url: str) -> int:
    import demo_combined as dc

    done = subprocess.run([sys.executable, *dc.TICK, "--no-prebuild"], capture_output=True, text=True, env=os.environ)
    return done.returncode


def test_h1_normal_on_s_plus_2_holds_act_k1_verified_and_steady_there_is_refused(tmp_path: Path) -> None:
    import pg_harness
    import psycopg
    import demo_combined as dc
    import demo_combined_kobo as dk
    import demo_story_days as sd

    url = pg_harness.fresh_database()
    assert url.split("/")[-1].endswith("_test") and "polish" not in url and "demo3" not in url
    os.environ["DATABASE_URL"] = url
    plain = url.replace("+psycopg", "")

    def q(sql: str):
        with psycopg.connect(plain, autocommit=True) as c:
            return c.execute(sql).fetchall()

    db_now = q("SELECT clock_timestamp()")[0][0]
    doc = sd.load()
    story = dc.resolve_story(db_now - timedelta(days=1), days_doc=doc)  # S+2 ended yesterday: addable at any hour
    rows = [r for r in story.pop("days") if r["site"] == "kobo" and r["kind"].startswith("trial-")]
    assert sorted(r["offset"] for r in rows) == [0, 1]
    (tmp_path / "days.json").write_text(json.dumps({"days": rows}), encoding="utf-8")
    ids = dk.build(url, tmp_path, story)
    tenant_id, site_id = q("SELECT tenant_id, id FROM site WHERE site_code = 'KOBO-001'")[0]

    current = sd.from_payload(rows)
    S = dc.at(story["S"])
    installs = {n: dc.at(story[n]["install_at"]) for n in dc.SITES}

    def delivered() -> set[str]:
        return {r[0] for r in q(
            "SELECT DISTINCT to_char(e.source_time AT TIME ZONE s.timezone, 'YYYY-MM-DD') FROM accepted_evidence e "
            "JOIN ingestion_disposition d ON d.batch_id = e.batch_id AND d.ordinal = e.ordinal "
            "JOIN site s ON s.id = e.site_id WHERE s.site_code = 'KOBO-001'")}

    def readings() -> int:
        return q("SELECT count(*) FROM accepted_evidence")[0][0]

    states: dict[str, str] = {}
    for n in (1, 2):
        assert _tick(url) == 0
    states["before_add"] = _state(url, ids, tenant_id, site_id)["state"]
    assert states["before_add"] == "VERIFIED", states

    n_before = readings()
    now = q("SELECT clock_timestamp()")[0][0]
    with pytest.raises(sd.StoryDaysError) as err:  # the guard: refused before any provisioning
        sd.plan_add_runs(doc, current, "kobo", "steady", S, now, day="S+2d", delivered_days=delivered(),
                         installs=installs)
    assert err.value.error_code == "FULL_DAY_AFTER_TRIAL" and readings() == n_before

    runs = sd.plan_add_runs(doc, current, "kobo", "normal", S, now, day="S+2d", delivered_days=delivered(),
                            installs=installs)
    assert len(runs) == 1 and runs[0].kind == "normal" and runs[0].offset == 2
    dk.add_day(url, tmp_path, [r.payload() for r in runs])
    assert readings() > n_before
    states["after_add"] = _state(url, ids, tenant_id, site_id)["state"]
    for n in (1, 2, 3):
        assert _tick(url) == 0
        states[f"tick_{n}"] = _state(url, ids, tenant_id, site_id)["state"]
    print("\nDD1a2-R3 L2, ACT-K1 current_state:", json.dumps(states))
    assert [states[f"tick_{n}"] for n in (1, 2, 3)] == ["VERIFIED"] * 3, states
