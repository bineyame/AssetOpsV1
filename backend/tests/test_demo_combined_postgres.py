"""DEMO-A U6 / DEMO-SPARSE U6: the combined demo dataset build test (build sheet DEMO-SPARSE §5, DEMO-COMBINED §4).

One `tools/demo_combined.py prepare` (all three Sites, the shipped day list) in a module fixture on its own database
`assetops_demo3_t<run>_test`, then every acceptance row of `tools/demo_combined_finish.py` (`CHECKS`) as its own test,
read through `host/lab_app.py` in a child process of the private tree (`finish check` once after the prepare; SP-7's
reads through `finish get`). The rows cannot read in this process: the file stores resolve under the importing
package's REPO_ROOT, and the dataset's stores are in the private tree, not this worktree. The **[IDX]** rows skip until IDX-GAPS is on this tree
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
        try:
            manifest = d.prepare()
        finally:  # as the tool's `main` does after a prepare: release the work folder for SP-7's add-day
            if d.holds_busy:
                (d.work / ".busy").unlink(missing_ok=True)
                d.holds_busy = False
        import shutil

        shutil.copyfile(d.work / "check.json", d.work / "check-prepare.json")  # the prepare's own self-check
        yield d, manifest
    finally:
        try:
            d.drop()
        finally:
            tool.PG_ADMIN = saved


def _child(d, *argv: str, label: str):
    d.deadline = time.monotonic() + 2 * 300  # the tool's 2x cap for one bounded child
    return d.py(str(d.tree / "tools" / "demo_combined_finish.py"), *argv, cwd=d.tree / "backend" / "tests",
                label=label, check=False)


def _get(d, path: str, params: dict) -> tuple[int, object]:
    import json

    done = _child(d, "get", d.url, str(d.work), path, json.dumps(params), label="build-test-get")
    line = next((x for x in reversed(done.stdout.splitlines()) if x.startswith("{")), None)
    assert done.returncode == 0 and line, done.stdout[-2000:]
    out = json.loads(line)
    return out["status_code"], out["body"]


@pytest.fixture(scope="module")
def ctx(demo):
    d, _ = demo
    return finish.load(d.work, None)


@pytest.fixture(scope="module")
def checked(demo) -> dict:
    """A fresh `finish check` in the private tree after the prepare (not the prepare's own check.json)."""
    import json

    d, _ = demo
    (d.work / "check.json").unlink(missing_ok=True)
    _child(d, "check", d.url, str(d.work), label="build-test-check")
    return json.loads((d.work / "check.json").read_text(encoding="utf-8"))["rows"]


def _case(check_id: str, idx: bool):
    def test(checked) -> None:
        got = checked[check_id]
        assert got["status"] == "pass", got

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
    doc = json.loads((d.work / "check-prepare.json").read_text(encoding="utf-8"))
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
    code, before = _get(d, f"/api/sites/{finish.KOBO}/finding-index", params)
    assert code == 200 and before["status"] != "CURRENT", (code, str(before)[:300])
    d.deadline = time.monotonic() + 2 * 300  # the tool's 2x cap for one tick + comparison
    d.tick()
    code, after = _get(d, f"/api/sites/{finish.KOBO}/finding-index", params)
    assert code == 200 and after["status"] == "CURRENT", (code, str(after)[:300])

    story = d.story()
    first = [(x["site"], x["offset"], x["kind"]) for x in ctx.days]
    later = tool.resolve_story(finish.at(story["db_now"]) + timedelta(days=1))
    again = [(x["site"], x["offset"], x["kind"]) for x in later["days"]]
    assert again == first, (first, again)
    moved = {(x["site"], x["offset"]): x["day"] for x in later["days"]}
    assert all(finish.at(moved[(x["site"], x["offset"])] + "T00:00:00Z") - finish.at(x["day"] + "T00:00:00Z")
               == timedelta(days=1) for x in ctx.days), moved
