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
        finally:  # as the tool's `main` does after a prepare; never raises, so a prepare failure propagates as is
            _release_busy(d)
        import shutil

        shutil.copyfile(d.work / "check.json", d.work / "check-prepare.json")  # the prepare's own self-check
        yield d, manifest
    finally:
        try:
            d.drop()
        finally:
            tool.PG_ADMIN = saved


def _release_busy(d) -> None:
    """Release the work folder's `.busy` (SP-7's add-day needs it free). It must never raise: it runs in the
    `finally` after `prepare`, and an error here would replace the prepare's own exception."""
    if not d.holds_busy:
        return
    try:
        (d.work / ".busy").unlink(missing_ok=True)
        d.holds_busy = False
    except OSError as exc:  # SP-7's add-day then refuses with the `.busy` message, naming the file
        print(f"could not release {d.work / '.busy'}: {exc}")


def _child(d, *argv: str, label: str):
    """One `finish` child in the private tree. A wall-cap stop (the tool's SystemExit) fails the row."""
    d.deadline = time.monotonic() + 2 * 300  # the tool's 2x cap for one bounded child
    try:
        return d.py(str(d.tree / "tools" / "demo_combined_finish.py"), *argv, cwd=d.tree / "backend" / "tests",
                    label=label, check=False)
    except SystemExit as exc:
        pytest.fail(f"finish {argv[0]} child stopped: {exc}")


def _get(d, path: str, params: dict) -> tuple[int, object]:
    """One read through `finish get`: a non-zero exit or output that is not one JSON line fails the row."""
    import json

    done = _child(d, "get", d.url, str(d.work), path, json.dumps(params), label="build-test-get")
    if done.returncode != 0:
        pytest.fail(f"finish get exited {done.returncode}: {done.stdout[-2000:]}")
    lines = [x for x in done.stdout.splitlines() if x.startswith("{")]
    if len(lines) != 1:
        pytest.fail(f"finish get printed {len(lines)} JSON lines, expected 1: {done.stdout[-2000:]}")
    try:
        out = json.loads(lines[0])
        return out["status_code"], out["body"]
    except (ValueError, KeyError, TypeError) as exc:
        pytest.fail(f"finish get output is not {{status_code, body}} JSON ({exc}): {lines[0][:2000]}")


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
    done = _child(d, "check", d.url, str(d.work), label="build-test-check")
    # `check` exits 0 when every row passed and 1 when a row failed (each row then fails on its own status);
    # any other exit, a missing or unparseable check.json, or a missing row fails every row
    if done.returncode not in (0, 1):
        pytest.fail(f"finish check exited {done.returncode}: {done.stdout[-2000:]}")
    try:
        rows = json.loads((d.work / "check.json").read_text(encoding="utf-8"))["rows"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        pytest.fail(f"finish check wrote no readable check.json ({exc}): {done.stdout[-2000:]}")
    missing = [c for c, _, m, _ in finish.CHECKS if not m and c not in rows]
    if missing:
        pytest.fail(f"finish check has no result for {missing}")
    failed = [c for c, r in rows.items() if r.get("status") == "fail"]
    if done.returncode != (1 if failed else 0):
        pytest.fail(f"finish check exit {done.returncode} disagrees with its rows (failed {failed})")
    return rows


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
    later = tool.resolve_story(finish.at(story["db_now"]) + timedelta(days=1))
    S, S2 = finish.at(story["S"]), finish.at(later["S"])
    assert S2 - S == timedelta(days=1), (story["S"], later["S"])
    # Addendum 4: a Site with no ruled weekday keeps the same (site, offset, kind) sequence, every date moved 1 day
    plain = lambda xs: [x for x in xs if x["site"] not in sd.SITE_WEEKDAY]  # noqa: E731
    first = [(x["site"], x["offset"], x["kind"]) for x in plain(ctx.days)]
    again = [(x["site"], x["offset"], x["kind"]) for x in plain(later["days"])]
    assert again == first, (first, again)
    moved = {(x["site"], x["offset"]): x["day"] for x in plain(later["days"])}
    assert all(finish.at(moved[(x["site"], x["offset"])] + "T00:00:00Z") - finish.at(x["day"] + "T00:00:00Z")
               == timedelta(days=1) for x in plain(ctx.days)), moved
    # a weekday-bound Site (`SITE_WEEKDAY`, R619): the same (site, listed day, kind) on both S, each resolved day
    # on the ruled weekday, inside (S + listed - 7 d, S + listed], at offset weekday_offset(site, S, listed)
    listed_doc = sd.load()
    for site, weekday in sd.SITE_WEEKDAY.items():
        listed = sorted(listed_doc["sites"][site], key=lambda e: sd.day_offset(e["day"]))
        seqs = []
        for on, xs in ((S, ctx.days), (S2, later["days"])):
            got = sorted((x for x in xs if x["site"] == site), key=lambda x: x["offset"])
            assert len(got) == len(listed), (site, on, got, listed)
            for e, x in zip(listed, got):
                n = sd.day_offset(e["day"])
                date = finish.at(x["day"] + "T00:00:00Z")
                assert date.weekday() == weekday, (site, on, e, x)
                assert on + timedelta(days=n - 7) < date <= on + timedelta(days=n), (site, on, e, x)
                assert x["offset"] == sd.weekday_offset(site, on, n), (site, on, e, x)
                assert x["kind"] == e["kind"], (site, on, e, x)
            seqs.append([(site, e["day"], x["kind"]) for e, x in zip(listed, got)])
        assert seqs[0] == seqs[1], (site, seqs)
