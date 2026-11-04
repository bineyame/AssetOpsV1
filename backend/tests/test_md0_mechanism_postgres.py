"""MD-0 L2m (build sheet §10.2, as reduced by Architect MD0-S2 to KOBO-001): the mechanism dataset seeded through
the product writers into a pg_harness worker DB, then asserted against the §2.6 expectations.

- `ASSETOPS_MECHANISM_DAY_SET` picks the day set (`states` by default; `full` is measured through the L3m tool).
- `ASSETOPS_MECHANISM_RECORD` names a JSON file the tests write the product's own reports to (the D-AW-3 skip
  report, grades that differ from §2.6, the late-fill occurrence order) for the packet.
- A disagreement with §2.6 is recorded with `pytest.xfail("MD-0-Fn ...")` after every hard assertion (R7); MD-0
  never changes a rule.

Requires ASSETOPS_TEST_DATABASE_URL (backend/README-db.md).
"""

from __future__ import annotations

import json
import os

import pytest
from sqlalchemy import text

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from test_s1_bindings_postgres import engine, store  # noqa: F401

import mechanism_dataset as md

SPEC = md.load()
DAY_SET = os.environ.get("ASSETOPS_MECHANISM_DAY_SET", "states")
RECORD = os.environ.get("ASSETOPS_MECHANISM_RECORD")
GENERATOR, HEADROOM = "GENERATOR_SUPPORT_CANDIDATE", "PRODUCTIVE_USE_HEADROOM"


def record(key: str, value) -> None:
    if not RECORD:
        return
    data = json.loads(open(RECORD, encoding="utf-8").read()) if os.path.exists(RECORD) else {}
    data[key] = value
    with open(RECORD, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, default=str)


def seeded(store, engine) -> dict:  # noqa: F811
    manifest = md.seed_database(store, engine, "main", DAY_SET)
    record("manifest", manifest)
    return manifest


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


def test_kobo_grades_threads_actions_and_story_time(store, engine) -> None:  # noqa: F811
    """§10.2 tests 1, 3 and 4 on one seed, plus the D-AW-3 record (MD0-S2)."""
    m = seeded(store, engine)
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


def test_late_fill_normal_fills_the_gap_and_changes_no_finding(store, engine) -> None:  # noqa: F811
    """§10.2 test 5."""
    m = seeded(store, engine)
    before = threads(engine, m["site_id"])
    with engine.connect() as c:
        k_before = c.execute(text("SELECT clock_timestamp()")).scalar_one()
        n_findings = c.execute(text("SELECT count(*) FROM finding WHERE site_id = :s"), {"s": m["site_id"]}).scalar_one()
    out = md.late_fill(md._url(engine), "KOBO-001", 7)
    record("late_fill_normal", out)
    assert out["day"] == _iso(7) and out["events"] == [], out
    assert out["snapshots"] and set(out["snapshots"].values()) == {"COMPLETE"}, out["snapshots"]
    with engine.connect() as c:
        assert c.execute(text("SELECT count(*) FROM finding WHERE site_id = :s"),
                         {"s": m["site_id"]}).scalar_one() == n_findings
        kept = c.execute(text("SELECT grade FROM site_day_snapshot WHERE site_id = :s AND local_day = :d "
                              "AND subject_kind = 'SITE' AND computed_at <= :k"),
                         {"s": m["site_id"], "d": md.day(SPEC, 7), "k": k_before}).scalars().all()
    assert kept and set(kept) == {"NO_DATA"}, kept  # at k_before D7 was still NO_DATA
    after = threads(engine, m["site_id"])
    assert {k: [s for _, s, _ in v["events"]] for k, v in after.items()} == \
        {k: [s for _, s, _ in v["events"]] for k, v in before.items()}


def test_late_fill_overrun_joins_the_thread_in_story_order(store, engine) -> None:  # noqa: F811
    """§10.2 test 6: occurrence_no is append order; the packet records it as the product gives it (R7)."""
    m = seeded(store, engine)
    out = md.late_fill(md._url(engine), "KOBO-001", 7, "overrun")
    assert len(out["events"]) == 1, out
    gen = threads(engine, m["site_id"])[GENERATOR]
    record("late_fill_overrun", {"out": out, "occurrences": gen["occurrences"], "events": gen["events"]})
    f = m["findings"]
    assert _story_order(gen) == [f["K-OVR-D4"], out["events"][0], f["K-OVR-D11"], f["K-OVR-D14"]]


def test_late_fill_refuses_any_other_day(engine) -> None:  # noqa: F811
    for args, code in ((("KOBO-001", 6), "DUPLICATE_DAY"), (("KOBO-001", 7, "action"), "PREPARE_ONLY_KIND")):
        with pytest.raises(md.MechanismRefused, match=code):
            md.late_fill(md._url(engine), *args)
