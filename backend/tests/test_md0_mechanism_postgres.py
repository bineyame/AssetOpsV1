"""MD-0 L2m (build sheet §10.2; MD0-S2 KOBO-001 only; MD0-S3 Q1 template DB): each test clones the input
template `assetops_mechanism_tpl_test` (`CREATE DATABASE ... TEMPLATE`, seconds), runs the derive step (step 10)
with this checkout's code, then asserts against the §2.6 expectations. The tests never seed.

- The template is built by `python tools/mechanism_dataset.py build --variant states --budget 540` (in parts,
  about 15 min). A missing or stale template (the input-writer fingerprint differs from this checkout) FAILS with
  `TEMPLATE_MISSING` / `TEMPLATE_STALE` and the rebuild command: stale inputs are never used.
- `ASSETOPS_MECHANISM_RECORD` names a JSON file the tests write the product's own reports to (the D-AW-3 skip
  report, grades that differ from §2.6, the late-fill occurrence order) for the packet.
- A disagreement with §2.6 is recorded with `pytest.xfail("MD-0-Fn ...")` after every hard assertion (R7); MD-0
  never changes a rule.

Requires ASSETOPS_TEST_DATABASE_URL (backend/README-db.md); only its server is used, for the clone.
"""

from __future__ import annotations

import json
import os
import secrets
import time

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from test_s1_bindings_postgres import engine  # noqa: F401

import mechanism_dataset as md

SPEC = md.load()
RECORD = os.environ.get("ASSETOPS_MECHANISM_RECORD")
GENERATOR, HEADROOM = "GENERATOR_SUPPORT_CANDIDATE", "PRODUCTIVE_USE_HEADROOM"


def record(key: str, value) -> None:
    if not RECORD:
        return
    data = json.loads(open(RECORD, encoding="utf-8").read()) if os.path.exists(RECORD) else {}
    data[key] = value
    with open(RECORD, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, default=str)


@pytest.fixture()
def mech(tmp_path):
    """(engine, manifest) on a fresh clone of the template, derived with this checkout's code; dropped after."""
    admin = md.admin_engine(URL)
    target = f"assetops_mechanism_c{secrets.token_hex(5)}_test"
    t0 = time.perf_counter()
    tag = md.clone_template(admin, target)
    clone_s = round(time.perf_counter() - t0, 1)
    url = md.database_url(URL, target)
    eng = create_engine(url, poolclass=NullPool)
    try:
        manifest = md.derive_clone(url, tag, tmp_path / "work")
        manifest["timings"]["clone"] = clone_s
        record("manifest", manifest)
        yield eng, manifest
    finally:
        eng.dispose()
        md.drop_database(admin, target)
        admin.dispose()


def _iso(n: int) -> str:
    return md.day(SPEC, n).isoformat()


def threads(engine, site_id) -> dict[str, dict]:
    """mechanism -> {id, occurrences [(no, finding_id, opportunity_id, episode_start)], events [(seq, state, day)]}"""
    out: dict[str, dict] = {}
    with engine.connect() as c:
        for tid, mech in c.execute(text("SELECT id, mechanism FROM finding_thread WHERE site_id = :s"),
                                   {"s": site_id}).all():
            occ = c.execute(text(
                "SELECT occurrence_no, finding_id, opportunity_id, episode_start FROM finding_thread_occurrence "
                "WHERE thread_id = :t ORDER BY occurrence_no"), {"t": tid}).all()
            ev = c.execute(text("SELECT seq, state, effective_day FROM finding_thread_event WHERE thread_id = :t "
                                "ORDER BY seq"), {"t": tid}).all()
            out[mech] = {"id": str(tid), "occurrences": [tuple(r) for r in occ], "events": [tuple(r) for r in ev]}
    return out


def _state_on(thread: dict, n: int) -> str | None:
    """The thread's state on Dn by story time: the last event whose effective day is on or before Dn."""
    on = [s for _, s, d in thread["events"] if d <= md.day(SPEC, n)]
    return on[-1] if on else None


def _story_order(thread: dict) -> list[str]:
    return [str(f) for _, f, _, _ in sorted(thread["occurrences"], key=lambda r: r[3]) if f is not None]


def test_kobo_grades_threads_actions_and_story_time(mech) -> None:
    """§10.2 tests 1, 3 and 4 on one clone, plus the D-AW-3 record (MD0-S2)."""
    engine, m = mech
    days, notes = m["days"], []
    assert m["role_set"] == "minigrid-roles-4" and m["published"] == ["price", "objective"]
    assert set(m["findings"]) == {e["anchor"] for e in SPEC["sites"]["kobo"]["events"] if e["day"] in days}

    # 1. Grades: D7 (GAP-K7) has no data; every delivered day is COMPLETE, else recorded (R7).
    g = md.grades(engine, m["site_id"])
    assert all(g.get(_iso(n)) for n in days), "a delivered day has no snapshot"
    gap = g.get(_iso(7), {})
    other = {_iso(n): {k: v for k, v in g[_iso(n)].items() if v != "COMPLETE"} for n in days}
    other = {d: v for d, v in other.items() if v}
    record("grades_gap_day", gap)
    record("grades_not_complete", other)
    if not gap or set(gap.values()) != {"NO_DATA"}:
        notes.append(f"MD-0-F1 GAP-K7 grades {gap}")
    if other:
        notes.append(f"MD-0-F2 delivered days graded other than COMPLETE: {other}")

    # 3. Threads: one generator thread with occurrences in story order D4, D11, D14 (the recurrence after apply).
    th = threads(engine, m["site_id"])
    gen = th[GENERATOR]
    record("generator_thread", gen)
    want = [m["findings"][a] for a in ("K-OVR-D4", "K-OVR-D11", "K-OVR-D14") if a in m["findings"]]
    assert _story_order(gen) == want, gen["occurrences"]
    # ACT-K1 reaches CHANGE_APPLIED; RESOLVED is not reached (MD0-PF Q3: verification is MD-0b).
    states = [s for _, s, _ in gen["events"]]
    assert "CHANGE_APPLIED" in states and "RESOLVED_MONITORING" not in states, gen["events"]
    with engine.connect() as c:
        links = c.execute(text("SELECT action_kind, thread_id FROM chain_action_thread WHERE site_id = :s"),
                          {"s": m["site_id"]}).all()
    assert [(k, str(t)) for k, t in links] == [("MINI_TRIAL", gen["id"])], links

    # 4. Story time: on D11 the thread is ACTION_IN_HAND (accepted 13:00), CHANGE_APPLIED from the D12 effect.
    assert _state_on(gen, 11) == "ACTION_IN_HAND", gen["events"]
    assert _state_on(gen, 12) == "CHANGE_APPLIED", gen["events"]

    # D-AW-3 (MD0-S2): the D14 occurrence during CHANGE_APPLIED, verbatim from run_lifecycle(...)["skipped_causes"].
    record("d_aw_3", {"skipped": m["lifecycle"]["skipped"], "skipped_causes": m["lifecycle"]["skipped_causes"],
                      "counts": m["lifecycle"]["counts"], "threads": m["lifecycle"]["threads"]})

    # Headroom (§2.6 b): W1 is never placed (skipped_ineligible 1); W2 places one OPEN thread.
    b = next(s for s in m["steps"]["bc"] if s["step"] == "b")
    record("step_b", b)
    head = th.get(HEADROOM)
    if head is None or b["skipped_ineligible"] != 1 or _state_on(head, 14) != "OPEN":
        notes.append(f"MD-0-F3 headroom: thread {head}, step b {b}, studies {m['studies']}, "
                     f"noon channels not bound {m['noon_dropped']}")
    if notes:
        pytest.xfail("; ".join(notes))


def test_late_fill_normal_fills_the_gap_and_changes_no_finding(mech) -> None:
    """§10.2 test 5."""
    engine, m = mech
    before = threads(engine, m["site_id"])
    with engine.connect() as c:
        k_before = c.execute(text("SELECT clock_timestamp()")).scalar_one()
        n_findings = c.execute(text("SELECT count(*) FROM finding WHERE site_id = :s"), {"s": m["site_id"]}).scalar_one()
    out = md.late_fill(md._url(engine), "KOBO-001", 7)
    record("late_fill_normal", out)
    assert out["day"] == _iso(7) and out["events"] == [], out
    with engine.connect() as c:
        assert c.execute(text("SELECT count(*) FROM finding WHERE site_id = :s"),
                         {"s": m["site_id"]}).scalar_one() == n_findings
        kept = c.execute(text("SELECT measure, grade FROM site_day_snapshot WHERE site_id = :s AND local_day = :d "
                              "AND computed_at <= :k"),
                         {"s": m["site_id"], "d": md.day(SPEC, 7), "k": k_before}).all()
        newer = c.execute(text("SELECT count(*) FROM site_day_snapshot WHERE site_id = :s AND local_day = :d "
                               "AND computed_at > :k"),
                          {"s": m["site_id"], "d": md.day(SPEC, 7), "k": k_before}).scalar_one()
    assert kept, "D7 had no snapshot before the fill"
    assert newer, "the late fill wrote no new D7 snapshot revision"  # the fill is seen by step 10 at real time
    after = threads(engine, m["site_id"])
    assert {k: [s for _, s, _ in v["events"]] for k, v in after.items()} == \
        {k: [s for _, s, _ in v["events"]] for k, v in before.items()}
    # §2.6 expectations, recorded as the product gives them (R7): D7 NO_DATA at k_before, COMPLETE after.
    record("late_fill_normal_before", [tuple(r) for r in kept])
    notes = []
    if {g for _, g in kept} != {"NO_DATA"}:
        notes.append(f"MD-0-F1 D7 before the fill {sorted(set(map(tuple, kept)))}")
    if set(out["snapshots"].values()) != {"COMPLETE"}:
        notes.append(f"MD-0-F4 D7 after the fill {out['snapshots']}")
    if notes:
        pytest.xfail("; ".join(notes))


def test_late_fill_overrun_joins_the_thread_in_story_order(mech) -> None:
    """§10.2 test 6: occurrence_no is append order; the packet records it as the product gives it (R7)."""
    engine, m = mech
    out = md.late_fill(md._url(engine), "KOBO-001", 7, "overrun")
    assert out["day"] == _iso(7) and out["readings"] > 0, out
    gen = threads(engine, m["site_id"])[GENERATOR]
    record("late_fill_overrun", {"out": out, "occurrences": gen["occurrences"], "events": gen["events"]})
    f = m["findings"]
    if len(out["events"]) != 1:  # §2.6 expects one new Finding; recorded as the product gives it (R7)
        pytest.xfail(f"MD-0-F5 the late D7 overrun produced {len(out['events'])} Findings "
                     f"({out['readings']} readings, real decision clock); thread order {_story_order(gen)}")
    assert _story_order(gen) == [f["K-OVR-D4"], out["events"][0], f["K-OVR-D11"], f["K-OVR-D14"]]


def test_late_fill_refuses_any_other_day(engine) -> None:  # noqa: F811
    for args, code in ((("KOBO-001", 6), "DUPLICATE_DAY"), (("KOBO-001", 7, "action"), "PREPARE_ONLY_KIND")):
        with pytest.raises(md.MechanismRefused, match=code):
            md.late_fill(md._url(engine), *args)


def test_template_clone_refuses_untagged_and_stale_then_clones_a_current_one() -> None:
    """MD0-S3 Q1: an unfinished build (no tag) and a stale fingerprint are refused; a current tag clones, and the
    clone carries the template's rows. Uses its own scratch template (an empty migrated clone name), seconds."""
    admin = md.admin_engine(URL)
    tpl, target = (f"assetops_mechanism_c{secrets.token_hex(5)}_test" for _ in range(2))
    try:
        with admin.connect() as c:
            c.execute(text(f'CREATE DATABASE "{tpl}"'))
        eng = create_engine(md.database_url(URL, tpl), poolclass=NullPool)
        with eng.begin() as c:
            c.execute(text("CREATE TABLE mark (v text)"))
            c.execute(text("INSERT INTO mark VALUES ('input')"))
        eng.dispose()
        with pytest.raises(md.MechanismRefused, match="TEMPLATE_MISSING"):
            md.clone_template(admin, target, tpl)
        md.tag_template(admin, md.make_tag({"site": {}}, "states", fingerprint="0" * 64), tpl)
        with pytest.raises(md.MechanismRefused, match="TEMPLATE_STALE"):
            md.clone_template(admin, target, tpl)
        md.tag_template(admin, md.make_tag({"site": {}}, "states"), tpl)
        assert md.clone_template(admin, target, tpl)["fingerprint"] == md.input_fingerprint()
        eng = create_engine(md.database_url(URL, target), poolclass=NullPool)
        with eng.connect() as c:
            assert c.execute(text("SELECT v FROM mark")).scalar_one() == "input"
        eng.dispose()
        with pytest.raises(md.MechanismRefused, match="MECHANISM_DB_ONLY"):
            md.clone_template(admin, "assetops_polish_full_test", tpl)
    finally:
        for name in (target, tpl):
            md.drop_database(admin, name)
        admin.dispose()
