"""DEMO-A U6 / DEMO-SPARSE U6: the combined demo dataset build test (build sheet DEMO-SPARSE §5, DEMO-COMBINED §4).

One `tools/demo_combined.py prepare` (all three Sites, the shipped day list) in a module fixture on its own database
`assetops_demo3_t<run>_test`, then every acceptance row of `tools/demo_combined_finish.py` (`CHECKS`) as its own test,
read through `host/lab_app.py` in process. The **[IDX]** rows skip until IDX-GAPS is on this tree
(`finding_index.POLICY_VERSION == "finding-index/2"`); at merge none may skip. SP-7 writes to the dataset (add-day,
one tick), so it runs last. Slow tier: one prepare is about 20-25 min (backend/TESTING.md "Slow tier").
"""

from __future__ import annotations

import os
import re
import sys
import time
import uuid
from datetime import timedelta
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO / "host"))

import demo_combined as tool  # noqa: E402
import demo_combined_finish as finish  # noqa: E402
import demo_story_days as sd  # noqa: E402
from assetops_backend.analytics import finding_index  # noqa: E402

pytestmark = pytest.mark.slow

needs_v2 = pytest.mark.skipif(getattr(finding_index, "POLICY_VERSION", None) != finish.IDX_POLICY,
                              reason="needs IDX-GAPS")


@pytest.fixture(scope="module")
def demo():
    from sqlalchemy.engine import make_url

    base = os.environ.get("ASSETOPS_TEST_DATABASE_BASE_URL") or os.environ.get("ASSETOPS_TEST_DATABASE_URL")
    if not base:
        pytest.fail("ASSETOPS_TEST_DATABASE_URL is not set (backend/TESTING.md)")
    u = make_url(base)
    run = re.sub(r"[^a-z0-9]", "", (os.environ.get("ASSETOPS_TEST_RUN_ID") or uuid.uuid4().hex).lower())[:12]
    db = f"assetops_demo3_t{run}_test"
    saved = tool.PG_ADMIN
    # the test server's host and port (container: postgres-test:5432), not the tool's local-dev default
    tool.PG_ADMIN = u.set(drivername="postgresql", database=u.database).render_as_string(hide_password=False)
    d = tool.Demo(db, f"var/demo3_t{run}")
    d.url = u.set(drivername="postgresql+psycopg", database=db).render_as_string(hide_password=False)
    try:
        manifest = d.prepare()
        yield d, manifest
    finally:
        try:
            d.drop()
        finally:
            tool.PG_ADMIN = saved


@pytest.fixture(scope="module")
def ctx(demo):
    d, _ = demo
    return finish.load(d.work, finish.app_client(d.url, d.work))


def _case(check_id: str, idx: bool):
    fn = next(f for c, _, _, f in finish.CHECKS if c == check_id)

    def test(ctx) -> None:
        fn(ctx)

    test.__name__ = "test_" + re.sub(r"[^A-Za-z0-9]", "_", check_id)
    test.__doc__ = f"DEMO-SPARSE §5 row {check_id}" + (" [IDX]" if idx else "")
    return needs_v2(test) if idx else test


for _id, _idx, _mutates, _ in finish.CHECKS:
    if not _mutates:
        _t = _case(_id, _idx)
        globals()[_t.__name__] = _t


def test_self_check_ran_in_prepare(demo) -> None:
    """The prepare's self-check child wrote check.json with no failed row."""
    import json

    d, _ = demo
    doc = json.loads((d.work / "check.json").read_text(encoding="utf-8"))
    assert not [k for k, v in doc["rows"].items() if v["status"] == "fail"], doc["rows"]


def test_SP_7_append_only_and_rebuild_kinds(demo, ctx) -> None:
    """SP-7 (runs last: it writes). A delivered day refuses; a late day reads as a gap until one tick assesses it;
    the same day list resolved on a later S gives the same kinds per day with every date moved."""
    d, _ = demo
    with pytest.raises((sd.StoryDaysError, SystemExit)) as refused:
        d.add_day(finish.KOBO, "normal", day="S-14d")
    assert "DAY_HAS_EVIDENCE" in str(refused.value), refused.value

    added = d.add_day(finish.KOBO, "late")
    day = added["day"]
    lo = finish.at(day + "T00:00:00Z")
    params = {"domain": "mini-grid-dispatch", "from": finish.iso(lo), "to": finish.iso(lo + timedelta(days=1))}
    c = ctx.client
    before = c.get(f"/api/sites/{finish.KOBO}/finding-index", params=params)
    assert before.status_code == 200 and before.json()["status"] != "CURRENT", before.text[:300]
    d.deadline = time.monotonic() + 2 * 300  # the tool's 2x cap for one tick + comparison
    d.tick()
    after = c.get(f"/api/sites/{finish.KOBO}/finding-index", params=params)
    assert after.status_code == 200 and after.json()["status"] == "CURRENT", after.text[:300]

    story = d.story()
    first = [(x["site"], x["offset"], x["kind"]) for x in ctx.days]
    later = tool.resolve_story(finish.at(story["db_now"]) + timedelta(days=1))
    again = [(x["site"], x["offset"], x["kind"]) for x in later["days"]]
    assert again == first, (first, again)
    moved = {(x["site"], x["offset"]): x["day"] for x in later["days"]}
    assert all(finish.at(moved[(x["site"], x["offset"])] + "T00:00:00Z") - finish.at(x["day"] + "T00:00:00Z")
               == timedelta(days=1) for x in ctx.days), moved
