"""MD-0 L2m (build sheet §10.2; MD0-S2 KOBO-001 only; MD0-S3 Q1 template DB): each test clones the input
template `assetops_mechanism_tpl_<fp8>_test` (`CREATE DATABASE ... TEMPLATE`, seconds), runs the derive step (step 10)
with this checkout's code, then asserts against the §2.6 expectations. The tests never seed.

- The template is built by `python tools/mechanism_dataset.py build --variant states --budget 540` (in parts,
  about 15 min). A missing or stale template (the input-writer fingerprint differs from this checkout) FAILS with
  `TEMPLATE_MISSING` / `TEMPLATE_STALE` and the rebuild command: stale inputs are never used.
- `ASSETOPS_MECHANISM_RECORD` names a JSON file the tests write the product's own reports to (the D-AW-3 skip
  report, grades that differ from §2.6, the late-fill occurrence order) for the packet.
- A disagreement with §2.6 is recorded with `pytest.xfail("MD-0-Fn ...")` after every hard assertion (R7); MD-0
  never changes a rule. MD-0b closed MD-0-F1 (its two xfails are hard assertions now) and adds the close variant
  (its own template `assetops_mechanism_tplc_<fp8>_test`, `build --variant close`).

Requires ASSETOPS_TEST_DATABASE_URL (backend/README-db.md); only its server is used, for the clone.
"""

from __future__ import annotations

import json
import os
import secrets
import time
from datetime import timedelta

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
    yield from _derived_clone(tmp_path, "states")


@pytest.fixture()
def mech_close(tmp_path):
    """MD-0b: the same on the close variant's template (§2.5)."""
    yield from _derived_clone(tmp_path, "close")


def _derived_clone(tmp_path, day_set: str):
    admin = md.admin_engine(URL)
    target = f"assetops_mechanism_c{secrets.token_hex(5)}_test"
    t0 = time.perf_counter()
    tag = md.clone_template(admin, target, day_set=day_set)
    clone_s = round(time.perf_counter() - t0, 1)
    url = md.database_url(URL, target)
    eng = create_engine(url, poolclass=NullPool)
    try:
        manifest = md.derive_clone(url, tag, tmp_path / "work")
        manifest["timings"]["clone"] = clone_s
        record("manifest" if day_set == "states" else f"manifest_{day_set}", manifest)
        yield eng, manifest
    finally:
        eng.dispose()
        md.drop_database(admin, target)
        admin.dispose()


def _core(key: str) -> bool:
    """productive_kwh / avoidable_gen_min, Site or per-subject (`measure@ref`): the MD0-S4 R1.5 hard grades."""
    return key.split("@")[0] in ("productive_kwh", "avoidable_gen_min")


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


#: MD0-S5 M2 invariant: the dispatch Findings before the renewable-hour channels were added (SELECT on
#: `assetops_mechanism_test`, derived from the template at 510acfa7c): anchor -> (episode start, episode end,
#: lifecycle, claim level, candidate/necessary/indeterminate minutes, end reason, recurrence, limitations,
#: transitions). The late D7 overrun has the same F01 shape; its baseline is D4's content at 2026-10-25 05:30Z.
DISPATCH_BASELINE = {
    "K-OVR-D4": ("2026-10-22T05:30Z", "06:00", "SUPPORTED", "CANDIDATE_AVOIDABLE", "30.0000", "0.0000", "0.0000",
                 "OFF_OBSERVED", "NOT_ESTABLISHED", "[]", "OPENED,BASIS_REFRESHED,BASIS_REFRESHED"),
    "K-OVR-D11": ("2026-10-29T05:30Z", "06:00", "SUPPORTED", "CANDIDATE_AVOIDABLE", "30.0000", "0.0000", "0.0000",
                  "OFF_OBSERVED", "NOT_ESTABLISHED", "[]", "OPENED,BASIS_REFRESHED,BASIS_REFRESHED,BASIS_REFRESHED"),
    "K-OVR-D14": ("2026-11-01T05:30Z", "06:00", "SUPPORTED", "CANDIDATE_AVOIDABLE", "30.0000", "0.0000", "0.0000",
                  "OFF_OBSERVED", "LINKED", "[]", "OPENED"),
}
LATE_D7_CONTENT = ("2026-10-25T05:30Z", "06:00", "SUPPORTED", "CANDIDATE_AVOIDABLE", "30.0000", "0.0000", "0.0000",
                   "OFF_OBSERVED", "[]")
CORE = ("productive_kwh@load-mill", "avoidable_gen_min@generator")


def dispatch_content(engine, finding_id) -> tuple:
    """A Finding's latest-revision content (the DISPATCH_BASELINE columns), no ids or clocks."""
    with engine.connect() as c:
        return tuple(c.execute(text(
            "SELECT to_char(f.anchor_start AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI\"Z\"'), "
            "to_char(r.episode_end AT TIME ZONE 'UTC', 'HH24:MI'), r.lifecycle, r.claim_level, "
            "r.candidate_minutes::text, r.necessary_minutes::text, r.indeterminate_minutes::text, "
            "r.claim->>'end_reason', coalesce(r.claim->'recurrence'->>'status', r.claim->'recurrence'->>'reason'), "
            "r.limitations::text, (SELECT string_agg(x.transition, ',' ORDER BY x.revision_no) FROM finding_revision x "
            "WHERE x.finding_id = f.id) FROM finding f JOIN LATERAL (SELECT * FROM finding_revision y "
            "WHERE y.finding_id = f.id ORDER BY y.revision_no DESC LIMIT 1) r ON true WHERE f.id = :f"),
            {"f": str(finding_id)}).one())


def renewable_hours(engine, site_id) -> dict[str, tuple[str, list]]:
    """local day -> (decision, constraint codes) of the selected renewable-hour revision (mini-depth)."""
    with engine.connect() as c:
        rows = c.execute(text(
            "SELECT DISTINCT ON (s.window_start) r.result->'rows'->0 FROM mini_depth_selection s "
            "JOIN mini_depth_revision r ON r.id = s.revision_id WHERE s.site_id = :s AND s.domain = 'renewable' "
            "ORDER BY s.window_start, s.seq DESC"), {"s": site_id}).scalars().all()
    return {r["day"]: (r["decision"], sorted(r["constraints"])) for r in rows if r}


def study_eligible_days(engine, site_id) -> dict[str, int]:
    """first selected local day -> eligible days of each opportunity's latest revision."""
    with engine.connect() as c:
        rows = c.execute(text(
            "SELECT DISTINCT ON (opportunity_id) selected_hours->0->>'local_day', result->>'eligible_days' "
            "FROM mini_opportunity_revision WHERE site_id = :s ORDER BY opportunity_id, revision_no DESC"),
            {"s": site_id}).all()
    return {d: int(n) for d, n in rows}


def readiness(engine, site_id, n: int) -> str:
    """CH5a1-R R5 `readiness_of` over Dn's latest snapshot rows (the board's rule, pure)."""
    from assetops_backend.chain.read import readiness_of

    with engine.connect() as c:
        rows = c.execute(text(
            "SELECT DISTINCT ON (measure, subject_kind, subject_ref) local_day, measure, grade FROM site_day_snapshot "
            "WHERE site_id = :s AND local_day = :d ORDER BY measure, subject_kind, subject_ref, revision DESC"),
            {"s": site_id, "d": md.day(SPEC, n)}).all()
        measures = sorted(c.execute(text("SELECT DISTINCT measure FROM site_day_snapshot WHERE site_id = :s"),
                                    {"s": site_id}).scalars())
    return readiness_of(rows, [md.day(SPEC, n)], measures)


def verification_outcomes(engine, site_id) -> list[str]:
    with engine.connect() as c:
        return [r[0] for r in c.execute(text("SELECT outcome FROM verification_outcome WHERE site_id = :s "
                                             "ORDER BY recorded_at"), {"s": site_id})]


def _story_order(thread: dict) -> list[str]:
    return [str(f) for _, f, _, _ in sorted(thread["occurrences"], key=lambda r: r[3]) if f is not None]


def test_kobo_grades_threads_actions_and_story_time(mech) -> None:
    """§10.2 tests 1, 3 and 4 on one clone, plus the D-AW-3 record (MD0-S2)."""
    engine, m = mech
    days = m["days"]
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
    # MD0-S4 R1.5 (hard): full delivered days grade COMPLETE on productive_kwh and avoidable_gen_min, and GAP-K7
    # stays NO_DATA/PENDING before any fill. daylight_headroom_kw grades as the renewable hour supports: recorded.
    core = {d: {k: v for k, v in x.items() if _core(k)} for d, x in other.items()}
    assert not any(core.values()), core
    # MD0-S5 L1: both core measures are present (not only "not other than COMPLETE") on every delivered day.
    missing = {_iso(n): [k for k in CORE if g[_iso(n)].get(k) != "COMPLETE"] for n in days}
    assert not any(missing.values()), missing
    # MD0-S5 M2 (A): daylight_headroom_kw is COMPLETE on every delivered day (the renewable-hour channels all day).
    assert not other, other
    assert all(g[_iso(n)].get("daylight_headroom_kw") == "COMPLETE" for n in days), {_iso(n): g[_iso(n)] for n in days}
    assert gap and set(gap.values()) <= {"NO_DATA", "PENDING"}, gap
    # CH9-R4 F1: critical_served reads the single CRITICAL row (`mini-service/2`): COMPLETE on every delivered day.
    assert all(g[_iso(n)].get("critical_served") == "COMPLETE" for n in days), {_iso(n): g[_iso(n)] for n in days}
    assert gap.get("critical_served") in ("NO_DATA", "PENDING"), gap
    undelivered = {_iso(n): g.get(_iso(n), {}) for n in range(1, 15) if n not in days}
    record("grades_undelivered", undelivered)
    # MD-0b (CH5a1-R3 M1, was MD-0-F1): the seed drains the product mini worker over the whole story, so no
    # undelivered day is left PENDING on a queued job: GAP-K7 is NO_DATA on every measure, and readiness NONE.
    assert not any(v == "PENDING" for x in undelivered.values() for v in x.values()), undelivered
    assert gap and set(gap.values()) == {"NO_DATA"}, gap
    assert readiness(engine, m["site_id"], 7) == "NONE", gap
    assert m["drain_mini"]["processed"] > 0 and set(m["drain_mini"]["statuses"]) == {"DONE"}, m["drain_mini"]

    # MD0-S5 M2 (A): EXCLUDED on the busy noons, ELIGIBLE on the spare-solar days D12/D13; codes recorded as found.
    spare = set(SPEC["sites"]["kobo"]["noon"]["spare_solar_days"])
    hours = renewable_hours(engine, m["site_id"])
    record("renewable_hours", hours)
    assert {_iso(n): hours[_iso(n)][0] for n in days} == \
        {_iso(n): "ELIGIBLE" if n in spare else "EXCLUDED" for n in days}, hours
    assert all("CHARGE_OBLIGATION_ACTIVE" in hours[_iso(n)][1] for n in days if n not in spare), hours
    record("renewable_other_codes", {_iso(n): [c for c in hours[_iso(n)][1] if c != "CHARGE_OBLIGATION_ACTIVE"]
                                     for n in days if hours[_iso(n)][1] not in ([], ["CHARGE_OBLIGATION_ACTIVE"])})
    eligible = study_eligible_days(engine, m["site_id"])
    record("study_eligible_days", eligible)
    assert eligible.get(_iso(1)) == 0 and eligible.get(_iso(10)) == 2, eligible

    # MD0-S5 M2 invariant: the dispatch Findings are unchanged by the new channels.
    assert {a: dispatch_content(engine, f) for a, f in m["findings"].items()} == DISPATCH_BASELINE

    # 3. Threads: one generator thread with occurrences in story order D4, D11, D14 (the recurrence after apply).
    th = threads(engine, m["site_id"])
    gen = th[GENERATOR]
    record("generator_thread", gen)
    want = [m["findings"][a] for a in ("K-OVR-D4", "K-OVR-D11", "K-OVR-D14") if a in m["findings"]]
    assert _story_order(gen) == want, gen["occurrences"]
    # MD-0b: ACT-K1 reaches VERIFIED on the seeded readings through the real evaluator (no monkeypatch, no
    # replaced window evidence or source resolution), with an authored source pair, so the thread resolves.
    ev = m["verification"]["evaluation"]
    record("verification", m["verification"])
    assert ev["outcome"] == "VERIFIED", ev
    assert ev["source_classes"] == {"baseline": "AUTHORED_DEMONSTRATION", "later": "AUTHORED_DEMONSTRATION"}, ev
    assert verification_outcomes(engine, m["site_id"]) == ["VERIFIED"]
    states = [s for _, s, _ in gen["events"]]
    assert "CHANGE_APPLIED" in states and "RESOLVED_MONITORING" in states, gen["events"]
    with engine.connect() as c:
        links = c.execute(text("SELECT action_kind, thread_id FROM chain_action_thread WHERE site_id = :s"),
                          {"s": m["site_id"]}).all()
    assert [(k, str(t)) for k, t in links] == [("MINI_TRIAL", gen["id"])], links

    # 4. Story time: on D11 the thread is ACTION_IN_HAND (accepted 13:00); the D12 change effect and the VERIFIED
    # cause both land on D12 by the product's effective day (the evaluation ran D13 10:00 local): CHANGE_APPLIED then
    # RESOLVED_MONITORING on D12, so RESOLVED_MONITORING on S = D13 (§2.6 a, "since D12").
    assert _state_on(gen, 11) == "ACTION_IN_HAND", gen["events"]
    on_d12 = [s for _, s, d in gen["events"] if d == md.day(SPEC, 12)]
    assert on_d12 == ["CHANGE_APPLIED", "RESOLVED_MONITORING"], gen["events"]
    assert _state_on(gen, 13) == "RESOLVED_MONITORING", gen["events"]

    # D-AW-3 (MD0-S2; its lifecycle change is CH-6b R16): the D14 recurrence, verbatim from run_lifecycle(...).
    record("d_aw_3", {"skipped": m["lifecycle"]["skipped"], "skipped_causes": m["lifecycle"]["skipped_causes"],
                      "counts": m["lifecycle"]["counts"], "threads": m["lifecycle"]["threads"],
                      "state_on_d14": _state_on(gen, 14)})

    # Headroom (§2.6 b): W1 (0 eligible days) is never placed (skipped_ineligible 1); W2 places one OPEN thread.
    b = next(s for s in m["steps"]["bc"] if s["step"] == "b")
    record("step_b", b)
    head = th.get(HEADROOM)
    assert head is not None and b["skipped_ineligible"] == 1 and _state_on(head, 14) == "OPEN", \
        (head, b, m["studies"], m["noon_dropped"])


def test_late_fill_normal_fills_the_gap_and_changes_no_finding(mech) -> None:
    """§10.2 test 5."""
    engine, m = mech
    before = threads(engine, m["site_id"])
    with engine.connect() as c:
        k_before = c.execute(text("SELECT clock_timestamp()")).scalar_one()
        n_findings = c.execute(text("SELECT count(*) FROM finding WHERE site_id = :s"), {"s": m["site_id"]}).scalar_one()
    out = md.late_fill(md._url(engine), "KOBO-001", 7)
    # CH-9 owned test change: the fill queues mini work for every measured daylight hour and every service hour of
    # D7, while `late_fill` reconciles only the noon hour. The product worker drains them (as the build's
    # `drain_mini` step does), then step 10 runs again, and the day's grades are read after that.
    import uuid

    md.drain_mini(md._url(engine))
    md.derive(md._url(engine), uuid.UUID(out["tenant_id"]), uuid.UUID(out["site_id"]))
    out["snapshots"] = md.grades(engine, m["site_id"]).get(out["day"], {})
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
    # MD0-S4 R1.5 as amended by CH5a1-R3 M1 (hard; MD-0b drains the mini queue, was MD-0-F1): NO_DATA on every
    # measure before the fill; productive_kwh and avoidable_gen_min COMPLETE after it.
    assert {g for _, g in kept} == {"NO_DATA"}, kept
    assert all(v == "COMPLETE" for k, v in out["snapshots"].items() if _core(k)), out["snapshots"]
    # MD0-S5 L1: both core measures are present after the fill; M2 (A): so is a COMPLETE daylight_headroom_kw.
    assert all(out["snapshots"].get(k) == "COMPLETE" for k in CORE), out["snapshots"]
    assert set(out["snapshots"].values()) == {"COMPLETE"}, out["snapshots"]
    hours = renewable_hours(engine, m["site_id"])
    record("late_fill_normal_d7_hour", hours.get(_iso(7)))
    assert hours[_iso(7)][0] == "EXCLUDED" and "CHARGE_OBLIGATION_ACTIVE" in hours[_iso(7)][1], hours.get(_iso(7))


def test_late_fill_overrun_joins_the_thread_in_story_order(mech) -> None:
    """§10.2 test 6: occurrence_no is append order; the packet records it as the product gives it (R7)."""
    engine, m = mech
    before = threads(engine, m["site_id"])
    out = md.late_fill(md._url(engine), "KOBO-001", 7, "overrun")
    assert out["day"] == _iso(7) and out["readings"] > 0, out
    gen = threads(engine, m["site_id"])[GENERATOR]
    record("late_fill_overrun", {"out": out, "occurrences": gen["occurrences"], "events": gen["events"]})
    f = m["findings"]
    # MD0-S4 R1.5 (hard; was MD-0-F5): the late D7 overrun opens exactly one Finding.
    assert len(out["events"]) == 1, (out["events"], out["readings"], _story_order(gen))
    assert _story_order(gen) == [f["K-OVR-D4"], out["events"][0], f["K-OVR-D11"], f["K-OVR-D14"]]
    # MD0-S5 L3: the late occurrence changes no thread state (OPEN, ACTION_IN_HAND, CHANGE_APPLIED).
    after = threads(engine, m["site_id"])
    assert {k: [s for _, s, _ in v["events"]] for k, v in after.items()} == \
        {k: [s for _, s, _ in v["events"]] for k, v in before.items()}
    # MD0-S5 M2 invariant: the late D7 Finding has the F01 content (D4's, re-dated).
    late = dispatch_content(engine, out["events"][0])
    record("late_d7_finding", late)
    assert late[:8] + (late[9],) == LATE_D7_CONTENT, late  # its recurrence and transitions are recorded


def test_close_variant_resolves_closes_after_seven_clean_days_and_recurs(mech_close) -> None:
    """§10.2 test 8 (MD-0b, §2.6 e): ACT-K2 VERIFIED -> RESOLVED_MONITORING, CLOSED on the 7th fully checked day
    after it (`close_after_clean_complete_days.default = 7`), RECURRED on the D13 overrun after the close."""
    engine, m = mech_close
    close = md.variant_spec(SPEC, "close")
    assert m["variant"] == "close" and m["days"] == list(range(1, 15)), (m["variant"], m["days"])
    assert set(m["findings"]) == {"K-OVR-D2", "K-OVR-D13"}, m["findings"]
    ev = m["verification"]["evaluation"]
    record("close_verification", m["verification"])
    assert ev["outcome"] == "VERIFIED", ev
    assert ev["source_classes"] == {"baseline": "AUTHORED_DEMONSTRATION", "later": "AUTHORED_DEMONSTRATION"}, ev
    assert verification_outcomes(engine, m["site_id"]) == ["VERIFIED"]
    g = md.grades(engine, m["site_id"])
    other = {d: {k: v for k, v in x.items() if v != "COMPLETE"} for d, x in g.items()}
    record("close_grades_not_complete", {d: v for d, v in other.items() if v})
    assert all(g.get(_iso(n)) for n in m["days"]), "a delivered day has no snapshot"
    assert not any(other.get(_iso(n)) for n in m["days"]), other  # every day fully checked (no gap, §2.5)
    gen = threads(engine, m["site_id"])[GENERATOR]
    record("close_generator_thread", gen)
    assert _story_order(gen) == [m["findings"]["K-OVR-D2"], m["findings"]["K-OVR-D13"]], gen["occurrences"]
    by_state = {}
    for _, state, d in gen["events"]:
        by_state.setdefault(state, d)
    resolved = by_state.get("RESOLVED_MONITORING")
    action = close["sites"]["kobo"]["actions"][0]
    record("close_resolved_day", str(resolved))
    # the product's effective day of the VERIFIED cause: on or after the change's day, by the evaluation's day
    # §2.6 e / DS-R1: VERIFIED is dated on the change's effective day (D3), so RESOLVED is D3 and CLOSED is D10 exactly.
    assert resolved == md.day(SPEC, 3), gen["events"]
    assert md.day(SPEC, action["effective"]["day"]) == resolved, gen["events"]
    # 7 fully checked days after the verified day (none of D5..D11 has an occurrence): CLOSED on the 7th.
    assert by_state.get("CLOSED") == md.day(SPEC, 10) == resolved + timedelta(days=7), gen["events"]
    assert by_state.get("RECURRED") == md.day(SPEC, 13), gen["events"]
    assert [s for _, s, _ in gen["events"]][-3:] == ["RESOLVED_MONITORING", "CLOSED", "RECURRED"], gen["events"]
    assert _state_on(gen, 12) == "CLOSED" and _state_on(gen, 14) == "RECURRED", gen["events"]
    record("close_lifecycle", {"skipped": m["lifecycle"]["skipped"], "skipped_causes": m["lifecycle"]["skipped_causes"],
                               "counts": m["lifecycle"]["counts"]})


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


def test_publish_renames_the_build_to_its_fingerprint_and_find_matches_only_it() -> None:
    """CH5a1-R3 M4: a finished staging build is tagged and renamed `assetops_mechanism_tpl_<fp8>_test`;
    `find_template` returns it for its own fingerprint and refuses another as stale. Scratch fingerprint, no prune."""
    admin = md.admin_engine(URL)
    fp = secrets.token_hex(32)
    staging, name = f"assetops_mechanism_tplb_{secrets.token_hex(4)}_test", md.template_name(fp)
    try:
        with admin.connect() as c:
            c.execute(text(f'CREATE DATABASE "{staging}"'))
        published, dropped = md.publish_template(admin, staging, md.make_tag({"site": {}}, "states", fingerprint=fp),
                                                 keep=10_000)
        assert (published, dropped) == (name, [])
        with admin.connect() as c:
            names = {r[0] for r in c.execute(text("SELECT datname FROM pg_database"))}
        assert name in names and staging not in names
        assert md.read_tag(admin, name)["fingerprint"] == fp
        assert name in [n for n, _ in md.templates(admin)]
        assert md.find_template(admin, fp) == name
        with pytest.raises(md.MechanismRefused, match="TEMPLATE_STALE|TEMPLATE_MISSING"):
            md.find_template(admin, "0" * 64)
    finally:
        for n in (staging, name):
            md.drop_database(admin, n)
        admin.dispose()


def test_grow_headroom_has_one_source_summary_value_line_and_portfolio(mech, tmp_path) -> None:
    """CH9-R4 F2: on MD-0 states the estate summary row, the study value line (Findings › Opportunities) and the
    Portfolio opportunity headroom name the same lo–hi, because the board's Grow headline reads the selected study
    through the Portfolio's read. Served in-process by `host/lab_app.py`, as the L3m collect does."""
    import json as _json
    import secrets as _secrets

    from demo_combined import KEY_NAMES
    from demo_combined_finish import app_client

    engine, _ = mech
    work = tmp_path / "f2"
    work.mkdir()
    (work / "keys.json").write_text(_json.dumps({k: _secrets.token_hex(32) for k in KEY_NAMES}), encoding="utf-8")
    client = app_client(engine.url.render_as_string(hide_password=False), work)
    w = {"from": "2026-10-03T00:00:00Z", "to": "2026-11-02T00:00:00Z"}  # the L3m month window
    portfolio = client.get("/api/estate/portfolio", params={**w, "lens": "all"}).json()
    opps = client.get("/api/estate/findings", params={**w, "lens": "opportunities", "state": "all"}).json()
    summary = client.get("/api/estate/outcome-summary", params=w).json()
    lo_hi = portfolio["opportunity"]["headroom"]
    assert lo_hi is not None and portfolio["opportunity"]["state"] == "FOUND"
    pair = f"{lo_hi['low']}–{lo_hi['high']}"
    [item] = [i for i in opps["opportunities"] if i["site_code"] == "KOBO-001"]
    assert item["study"]["headroom_kw"] == lo_hi and item["value_line"].startswith(f"{pair} kW over ")
    [kobo] = [s for s in summary["sites"] if s["site_code"] == "KOBO-001"]
    grow = next(r for r in kobo["rows"] if r["category"] == "GROW_REVENUE")
    assert grow["short_value"] == f"{pair} kW unused"
    record("f2_headroom", {"portfolio": lo_hi, "value_line": item["value_line"], "summary": grow["short_value"]})
