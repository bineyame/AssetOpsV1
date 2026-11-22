"""0K4e (`specs/0K4e-candidate-energy/spec.md` §3 E9-E11; D-0K4.11, D-0K4.23): `dispatch-3.3` on a run-owned `*_test`
database holding the `CaseRunner` world (`test_s4_finding_store_postgres.py`) plus one planted night of
battery-support points, first assessed on `dispatch-3.2`.

The `dispatch-3.2` model is the analytic as it stood on `main` at the spec's build base (`BASE_3_2`), loaded from git
so the history is the real 3.2's. The fixture's days are each case's first delivery and the planted night
(2026-10-23 22:00 .. 23:00 UTC, PV 0, PCS 40 kW, SOC 80 %, reserve 20 %, three feeders at 10 kW; load and PV then go on
alone, PV 0 to 01:55 and 40 kW from 02:00 on 2026-10-24). By hand, with the Kobo Foundation's 200 kWh and 95 %:
held = 0.6 x 200 x 0.95 = 114 kWh; from 22:00 the need is 48 slots x 30 kW x 5/60 h = 120 kWh (132 > 114: SHORT); from
22:35 it is 41 slots = 102.5 kWh (112.75 <= 114: COVERED). So 3.2's 60 Candidate minutes on that night become 25.

Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database (run under `tools/heavy-slot.sh --db`); skipped otherwise.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import types
from datetime import date, datetime, timedelta, timezone
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace

import pytest

from test_s4_finding_store_postgres import SPEC, URL, CaseRunner  # noqa: F401

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

UTC = timezone.utc
REPO = Path(__file__).resolve().parents[2]
BASE_3_2 = "b96d5e978"                      # `main` when 0K4e was built: the analytic at `dispatch-3.2`
PLANTED_DAY = date(2026, 10, 23)
BATTERY_SUPPORT = "PV available plus PCS discharge capability covers load with 10 % headroom"
PLANTED = [
    {"do": "deliver", "decided": "2026-10-30T16:00:00Z", "blocks": [
        {"from": "2026-10-23T22:00:00Z", "to": "2026-10-23T23:00:00Z", "pv": "0", "dis": "40", "soc": "80",
         "stop_before": True, "stop_after": True},
        {"from": "2026-10-23T23:05:00Z", "to": "2026-10-24T01:55:00Z", "pv": "0", "only": ["load", "pv"]},
        {"from": "2026-10-24T02:00:00Z", "to": "2026-10-24T02:30:00Z", "pv": "40", "only": ["load", "pv"]}]},
]

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import Clock, engine, store  # noqa: F401

    import pg_harness
    from assetops_backend.analytics import dispatch_v3
    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.analytics.assessment_worker import DispatchAssessmentWorker
    from assetops_backend.analytics.claim_limit_read import ClaimLimitReadService
    from assetops_backend.structure.registry import REGISTRIES
    from assetops_backend.structure.litres.inputs import day_state
    from assetops_backend.structure.litres.rules import (
        ASSESSED, EDGE, ONE_EACH, DispatchDay, FuelCurve, LitreInputs, RunSpan, SpanUse, month_litres)


def _model_3_2():
    """The analytic at `BASE_3_2` as a module of its own (the stored-history model)."""
    try:
        source = subprocess.run(["git", "show", f"{BASE_3_2}:backend/assetops_backend/analytics/dispatch_v3.py"],
                                cwd=REPO, capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError) as exc:  # pragma: no cover - a clone without the history
        pytest.skip(f"dispatch-3.2 source not readable from git: {exc}")
    name = "dispatch_v3_at_3_2"
    module = types.ModuleType(name)
    sys.modules[name] = module
    exec(compile(source, f"{BASE_3_2}:dispatch_v3.py", "exec"), module.__dict__)
    assert module.MODEL_VERSION == "dispatch-3.2"
    return module


class Timed(SimpleNamespace):
    """A model as the worker reads it, with `assess()`'s wall time summed."""

    def __init__(self, module) -> None:
        super().__init__(ANALYTIC_ID=module.ANALYTIC_ID, MODEL_VERSION=module.MODEL_VERSION, seconds=0.0, calls=0)
        self._module = module

    def assess(self, inputs):
        started = time.perf_counter()
        try:
            return self._module.assess(inputs)
        finally:
            self.seconds += time.perf_counter() - started
            self.calls += 1


def _heads(assess, runner) -> dict:
    return {h.window.start.date(): h.model_version for h in assess.run_heads(runner.tenant, runner.site, "dispatch")}


def _snapshot_3_2(engine, runner) -> dict:  # noqa: F811
    with engine.connect() as c:
        runs = c.execute(text(
            "SELECT r.id::text, md5(row_to_json(r)::text) FROM analytic_run r WHERE r.site_id = :s "
            "AND r.model_version = 'dispatch-3.2' ORDER BY r.id"), {"s": runner.site}).all()
        revisions = c.execute(text(
            "SELECT v.id::text, md5(row_to_json(v)::text) FROM assessment_revision v WHERE v.site_id = :s "
            "AND v.model_version = 'dispatch-3.2' ORDER BY v.id"), {"s": runner.site}).all()
    return {"runs": dict(runs), "revisions": dict(revisions)}


def _selected_segments(assess, runner, k) -> dict[date, list[dict]]:
    """Each fixture day's segments from its CURRENT default selection."""
    out: dict[date, list[dict]] = {}
    lo, hi = datetime(2026, 10, 5, tzinfo=UTC), datetime(2026, 10, 25, tzinfo=UTC)
    for d in assess.dispatch_spans(runner.tenant, runner.site, lo, hi, k):
        if d["run_id"] is None or d["status"] != "CURRENT":
            continue
        detail = assess.run_detail(runner.tenant, runner.site, d["run_id"])
        out[d["day"]] = [s for r in detail["revisions"] if r["scope"] == "INTERVAL"
                         for s in r["result"]["segments"]]
    return out


def _candidate(segments: dict[date, list[dict]]) -> tuple[int, Fraction]:
    found = [s for day in segments.values() for s in day if s["classification"] == "CANDIDATE_AVOIDABLE"]
    return len(found), sum((Fraction(s["minutes"]) for s in found), Fraction(0))


def _litres(assess, runner, k) -> dict[str, str]:
    """4d's split over the planted day from the stored selection (`month_litres` over `dispatch_spans`, D-4D.12's
    day states), with a constant 30 kW output at 0.3 L/kWh: the CaseRunner world has no generator-output or tank
    records for a whole month, so the use and the curve are fixed here and only the dispatch spans are the store's."""
    lo = datetime.combine(PLANTED_DAY, datetime.min.time(), UTC)
    hi = lo + timedelta(days=1)
    days = tuple(
        DispatchDay(d["day"], state, d["run_id"] if state == ASSESSED else None,
                    tuple(RunSpan(s, e, c) for s, e, c in d["spans"]) if state == ASSESSED else ())
        for d in assess.dispatch_spans(runner.tenant, runner.site, lo - EDGE, hi + EDGE, k)
        for state in (day_state(d["available"], d["status"], d["selected"], d["accepted_reading_count"]),))
    use = lambda a, b: SpanUse(Fraction(30) * Fraction(int((b - a).total_seconds()), 3600), 0)  # noqa: E731
    curve = FuelCurve(Fraction(3, 10), "foundation:test", None, None, (lo - 2 * EDGE, None))
    inp = LitreInputs("2026-10", lo, hi, k, ONE_EACH, days, use, lambda a, b: True, curve, ())
    filled_by = {f: REGISTRIES["MINI_GRID"].row(f).filled_by for f in ("necessary_l", "candidate_l", "unexplained_l")}
    month = month_litres(inp, filled_by)
    return {leaf: month.values[leaf].value for leaf in ("necessary_l", "candidate_l")}


def _record(payload: dict) -> None:
    folder = os.environ.get("OK4E_EVIDENCE_DIR")
    if folder:
        Path(folder).mkdir(parents=True, exist_ok=True)
        (Path(folder) / "e9_e11.json").write_text(json.dumps(payload, indent=1, default=str), encoding="utf-8")
    print("0K4E", json.dumps(payload, default=str))


def test_e9_e11_dispatch_3_3_reassesses_3_2_history(store, engine, monkeypatch) -> None:  # noqa: F811
    model_3_2 = Timed(_model_3_2())
    # Before the deploy: the reads judge a selection CURRENT against the live model's version (`derive_status`).
    monkeypatch.setattr(dispatch_v3, "MODEL_VERSION", "dispatch-3.2")
    runner = CaseRunner(store, engine, model=model_3_2)
    assess = PostgresAssessmentStore(URL)
    try:
        decided = datetime(2026, 10, 30, 8, tzinfo=UTC)
        for case in SPEC["cases"]:                    # each case's first delivery (F02: both, its night spans midnight)
            deliveries = [s for s in case["steps"] if s["do"] == "deliver"]
            for step in deliveries if case["case_id"] == "F02" else deliveries[:1]:
                runner.step({**step, "decided": decided.strftime("%Y-%m-%dT%H:%M:%SZ")})
                decided += timedelta(minutes=30)
        for step in PLANTED:
            runner.step(step)
        runner.step({"do": "assess"})
        k = runner.tick()

        # --- on 3.2 (pre-flight item 3, labelled: the fixture's days, not 1-31 Oct) ------------------------------
        heads = _heads(assess, runner)
        assert heads and set(heads.values()) == {"dispatch-3.2"}
        before = _selected_segments(assess, runner, k)
        assert PLANTED_DAY in before
        count_32, minutes_32 = _candidate(before)
        support = [s for s in before[PLANTED_DAY] if s["classification"] == "CANDIDATE_AVOIDABLE"
                   and BATTERY_SUPPORT in s["reasons"]]
        assert support, "precondition: a 3.2 Candidate segment reaches the battery-support branch"
        planted_32 = _candidate({PLANTED_DAY: before[PLANTED_DAY]})
        assert planted_32[1] == 60
        litres_32 = _litres(assess, runner, k)
        history = _snapshot_3_2(engine, runner)
        assert history["runs"] and history["revisions"]
        seconds_32, calls_32 = model_3_2.seconds, model_3_2.calls

        monkeypatch.undo()                                     # the deploy: dispatch-3.3 is the live model
        assert dispatch_v3.MODEL_VERSION == "dispatch-3.3"
        stale = assess.dispatch_spans(runner.tenant, runner.site, datetime(2026, 10, 23, tzinfo=UTC),
                                      datetime(2026, 10, 24, tzinfo=UTC), runner.tick())[0]
        assert stale["status"] == "STALE_PROJECTION"           # 3.2's selection reads stale until reassessed

        # --- E11: the reconcile pass enqueues every window whose last default selection is 3.2, and only those ---
        model_3_3 = Timed(dispatch_v3)
        worker = DispatchAssessmentWorker(assess, model=model_3_3, clock=Clock(runner.tick()))
        scheduled = worker.reconcile(runner.tenant, runner.site)
        assert sorted(w.start.date() for w in scheduled) == sorted(d for d, v in heads.items() if v == "dispatch-3.2")
        for outcome in worker.run_pending(reconcile=False):
            assert outcome.status == "DONE", outcome.error
        assert DispatchAssessmentWorker(assess, model=model_3_3, clock=Clock(runner.tick())).reconcile(
            runner.tenant, runner.site) == []
        k = runner.tick()

        # --- E9: 3.2 history unchanged; the default selection is 3.3; Candidate minutes at most 3.2's ------------
        assert _snapshot_3_2(engine, runner) == history
        assert set(_heads(assess, runner).values()) == {"dispatch-3.3"}
        after = _selected_segments(assess, runner, k)
        assert set(after) == set(before)
        count_33, minutes_33 = _candidate(after)
        assert minutes_33 <= minutes_32
        planted_33 = _candidate({PLANTED_DAY: after[PLANTED_DAY]})
        assert planted_33[1] == 25                                     # 22:35 .. 23:00, by hand
        states = {e["state"] for s in after[PLANTED_DAY] for e in s.get("energy_cover", [])}
        assert {"SHORT", "COVERED"} <= states and "NOT_CONFIGURED" not in states

        # --- E10: 4d moves litres only between candidate and necessary; the claim limit reads a 3.3 window -----
        litres_33 = _litres(assess, runner, k)
        total = lambda x: x["necessary_l"] + x["candidate_l"]  # noqa: E731
        assert total(litres_33) == total(litres_32)
        assert litres_33["candidate_l"] < litres_32["candidate_l"]
        day = assess.dispatch_spans(runner.tenant, runner.site, datetime(2026, 10, 23, tzinfo=UTC),
                                    datetime(2026, 10, 24, tzinfo=UTC), k)[0]
        revision = next(r for r in assess.run_detail(runner.tenant, runner.site, day["run_id"])["revisions"]
                        if r["scope"] == "INTERVAL")
        assert revision["model_version"] == "dispatch-3.3"
        body = ClaimLimitReadService(assess).read(runner.tenant, runner.site, PLANTED_DAY, revision["id"])
        assert body["claim_limit"]["ceiling"] is not None

        _record({"database": URL.rsplit("/", 1)[-1], "fixture_days": sorted(str(d) for d in before),
                 "dispatch_3_2": {"candidate_segments": count_32, "candidate_minutes": str(minutes_32),
                                  "planted_night_candidate_minutes": str(planted_32[1]), "litres": litres_32,
                                  "assess_seconds": round(seconds_32, 3), "assess_calls": calls_32},
                 "dispatch_3_3": {"candidate_segments": count_33, "candidate_minutes": str(minutes_33),
                                  "planted_night_candidate_minutes": str(planted_33[1]), "litres": litres_33,
                                  "assess_seconds": round(model_3_3.seconds, 3), "assess_calls": model_3_3.calls},
                 "reconciled_windows": sorted(str(w.start.date()) for w in scheduled)})
    finally:
        pg_harness.dispose(assess, runner.findings)
        sys.modules.pop("dispatch_v3_at_3_2", None)
