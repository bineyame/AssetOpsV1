"""S6-02b walkthrough: the TEST-SCOPED verification cases, built and served from one private database each.

    python tools/s602b_test_scoped_cases.py build <database-url> <work> <case>
    python tools/s602b_test_scoped_cases.py serve <database-url> <work> <case> <port>

Run by `tools/s602b_verification_walkthrough.py` only, from its private tree's `backend/tests` with that tree's
code and tests on PYTHONPATH and `ASSETOPS_TEST_DATABASE_URL` set to the private database (the builders read it at
import). Never run against a `*_test` database: nothing here resets or migrates one.

What they are. S6-02a's own evaluator test builders (`backend/tests/test_s6_verification_evaluator_postgres.py`)
over the S4 F01/F02 cases of a `minigrid-roles-2` Site: S6-01 accept/apply, S6-02a plan freeze, later binding,
evaluation, RESOLVED / RESOLUTION_WITHDRAWN and prior-trial holds are real rows written by the real services.
Three cases replace only the pure window evidence and the per-window source resolution with the evaluator tests'
labelled authored complete windows (`complete_windows`: source AUTHORED_DEMONSTRATION, fixture
`D-verification-window-test-scoped`), because the roles-2 Site can never complete a window. The `inconclusive`
case uses no fake at all. None of them is a Lab run; the walkthrough labels every page that shows one.

`serve` is the walkthrough's wrapper: the product application (`host/lab_app.py`) with the Action clock pinned to
the case's recorded end (`pinned_at`, the builders' own clock when the case finished: the fixture rows are recorded
2026-10-29..11-02, so today's clock would read a later, different state) and, for the authored cases, the same
window and source fakes the builders used. Stored outcomes, metrics, events, history and holds are read unchanged.

Cases: target_miss (INEFFECTIVE, TARGET_MISS), guardrail (INEFFECTIVE, GUARDRAIL_FAIL, hold on the different
Finding F02), inconclusive (real roles-2 windows: INCONCLUSIVE), withdrawn (VERIFIED -> RESOLVED -> late reading ->
REASSESSMENT_PENDING -> overlap accept of F02 -> RESOLUTION_WITHDRAWN -> re-settled INCONCLUSIVE), estate (CC-R2 D5:
F01 VERIFIED next to S4 F03's recurring 09:30 Finding, the MG-B stand-in, and S4 F05 through its UNCONFIRMED match,
the MG-C stand-in; the build asserts their Portfolio placement and the no-double-count invariant before it writes).
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

UTC = timezone.utc
CASES = ("target_miss", "guardrail", "inconclusive", "withdrawn", "estate")
TEST_SCOPED = "TEST-SCOPED example (S6-02a evaluator builders over a roles-2 Site; not a Lab run)"
LABELS = {
    "target_miss": "Target not met (INEFFECTIVE, TARGET_MISS) - authored complete windows",
    "guardrail": "Trial missed a safety or service limit (INEFFECTIVE, GUARDRAIL_FAIL) and the hold on a "
                 "different Finding - authored complete windows",
    "inconclusive": "Could not conclude (INCONCLUSIVE) - the real roles-2 windows are incomplete; no fake",
    "withdrawn": "VERIFIED, then late evidence: resolution withdrawn, overlap hold, re-settled INCONCLUSIVE - "
                 "authored complete windows plus the real late reading",
    "estate": "Portfolio placement (CC-R2): a VERIFIED change, a recurrence with no Action and an unconfirmed "
              "Finding on one Site - authored complete windows",
}
#: CC-R2: the Portfolio read the `estate` case asserts (build spec CC-R2 "Producer" 1).
ESTATE_PORTFOLIO = "/api/estate/portfolio?from=2026-10-01T00:00:00Z&to=2026-11-03T00:00:00Z"


class Patch:
    """The one `monkeypatch.setattr` the builders call, outside pytest (the process ends with the case)."""

    def setattr(self, target, name, value) -> None:
        setattr(target, name, value)


def window_fake(params: dict) -> None:
    """The builders' `complete_windows` window and source fakes, re-applied in the serving process."""
    import test_s6_verification_evaluator_postgres as ev

    class H:
        class service:
            verification_ports = None

    ev.complete_windows(Patch(), H, baseline_soc=params["baseline_soc"], later_soc=params["later_soc"],
                        inject=set(params["inject"]))
    ports = H.service.verification_ports
    import assetops_backend.actions.composition as composition

    composition.verification_ports = lambda url: ports


def build(url: str, work: Path, case: str) -> None:
    import pg_harness
    from alembic import command

    command.upgrade(pg_harness._alembic(url), "head")
    from sqlalchemy import create_engine

    import test_s6_verification_evaluator_postgres as ev
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore
    from test_s4_finding_store_postgres import CaseRunner, run_case
    from test_s6_action_store_postgres import CASES as S4
    from test_s6_verification_plan_postgres import applied_action, deliver_later, freeze, verifying

    engine = create_engine(url)
    store = PostgresFoundationStore(url)
    runner = CaseRunner(store, engine)
    run_case(runner, S4["F01"])
    run_case(runner, S4["F02"])
    if case == "estate":
        estate_findings(runner, url, S4)
    h = verifying(runner)
    fake = {"baseline_soc": "50", "later_soc": "50", "inject": []}
    findings = h.findings()
    out: dict = {"label": LABELS[case], "scope": TEST_SCOPED, "authored_windows": case != "inconclusive"}
    try:
        p2 = ev.proposal_of(h, "2026-10-08")
        if case == "target_miss":
            ev.complete_windows(Patch(), h)
            action_id, plan, _ = ev.bound_plan(runner, h, later=deliver_later)
            outcome = ev.evaluate(h, action_id, "eval-0001").json()["outcome"]
            assert outcome["outcome"] == "INEFFECTIVE" and outcome["reasons"] == ["TARGET_MISS"], outcome
            out["expect"] = {"current_state": "INEFFECTIVE", "outcome": "INEFFECTIVE", "label": "Target not met"}
        elif case == "guardrail":
            fake |= {"baseline_soc": "30", "later_soc": "29"}
            ev.complete_windows(Patch(), h, baseline_soc="30", later_soc="29")
            action_id, plan, _ = ev.bound_plan(runner, h)
            made = ev.evaluate(h, action_id, "eval-0001").json()
            outcome = made["outcome"]
            assert outcome["outcome"] == "INEFFECTIVE" and outcome["reasons"][0] == "GUARDRAIL_FAIL", outcome
            assert ev.guard_code(h, runner, p2) == "PRIOR_TRIAL_GUARDRAIL_FAILED"
            out["expect"] = {"current_state": "INEFFECTIVE", "outcome": "INEFFECTIVE",
                             "label": "Trial missed a safety or service limit", "resolution": ["RESOLVED"]}
            out["recommendation"] = {"finding": str(findings["2026-10-08"]), "revision": p2["finding_revision_id"],
                                     "state": "PRIOR_TRIAL_GUARDRAIL_FAILED", "other_finding": True}
        elif case == "inconclusive":
            action_id = applied_action(runner, h)
            plan = freeze(h, action_id).json()["plan"]
            early = ev.evaluate(h, action_id, "eval-0001").json()
            assert early["state"] == "PENDING", early
            h.clock.at = ev.CLOSED
            ev.later_generator_off(runner)
            ev.caught_up(runner, h, ev.CLOSED)
            assert ev.bind(h, action_id, plan["plan_id"], "bind-0001").status_code == 201
            outcome = ev.evaluate(h, action_id, "eval-0003").json()["outcome"]
            assert outcome["outcome"] == "INCONCLUSIVE", outcome
            out["expect"] = {"current_state": "INCONCLUSIVE", "outcome": "INCONCLUSIVE", "label": "Could not conclude"}
        elif case == "estate":  # the `withdrawn` case's steps up to and including its first VERIFIED evaluation
            inject = set()
            ev.complete_windows(Patch(), h, inject=inject)
            action_id, plan, _ = ev.bound_plan(runner, h)
            h.clock.at = ev.CLOSED + timedelta(hours=1)
            outcome = ev.evaluate(h, action_id, "eval-0001").json()["outcome"]
            assert outcome["outcome"] == "VERIFIED", outcome
            fake["inject"] = sorted(inject)
            out["expect"] = {"current_state": "VERIFIED", "outcome": "VERIFIED"}
        else:  # withdrawn
            inject: set = set()
            ev.complete_windows(Patch(), h, inject=inject)
            action_id, plan, _ = ev.bound_plan(runner, h)
            h.clock.at = ev.CLOSED + timedelta(hours=1)
            first = ev.evaluate(h, action_id, "eval-0001").json()["outcome"]
            assert first["outcome"] == "VERIFIED", first
            late = ev.late_reading(runner, "2026-11-02T13:00:00Z")
            inject.update(late)
            ev.store_accept(h, runner, p2, "accept-f02-late", datetime(2026, 11, 2, 13, 30, tzinfo=UTC))
            h.clock.at = datetime(2026, 11, 2, 14, 0, tzinfo=UTC)
            withdrawn = ev.evaluate(h, action_id, "eval-0002").json()
            assert withdrawn["withdrawn"] is True, withdrawn
            ev.caught_up(runner, h, h.clock.at)
            assert ev.bind(h, action_id, plan["plan_id"], "bind-0002").status_code == 201
            outcome = ev.evaluate(h, action_id, "eval-0003").json()["outcome"]
            assert outcome["outcome"] == "INCONCLUSIVE" and outcome["supersedes_outcome_id"] == first["outcome_id"]
            fake["inject"] = sorted(inject)
            out["withdrawn_outcome"] = first["outcome_id"]
            out["expect"] = {"current_state": "INCONCLUSIVE", "outcome": "INCONCLUSIVE", "label": "Could not conclude",
                             "resolution": ["RESOLVED", "RESOLUTION_WITHDRAWN"]}
            out["recommendation"] = {"finding": str(findings["2026-10-06"]),
                                     "revision": h.recommendation(findings["2026-10-06"]).json()["latest_revision_id"],
                                     "state": "PRIOR_TRIAL_REASSESSMENT_OVERLAP", "other_finding": False}
        pinned = max(h.clock.at, runner.now) + timedelta(minutes=1)
        out |= {"action": action_id, "plan": plan["plan_id"] if isinstance(plan, dict) else plan,
                "outcome": outcome["outcome_id"], "outcome_reasons": outcome["reasons"],
                "pinned_at": pinned.isoformat(), "fake": fake if case != "inconclusive" else None,
                "findings": {day: str(fid) for day, fid in findings.items()}}
    finally:
        h.close()
        import pg_harness as pg

        pg.dispose(runner.findings)
        pg.dispose(store)
        engine.dispose()
    if case == "estate":  # any failure exits non-zero before the case file (and so before any capture) exists
        out["placement"] = estate_assertions(out)
    (work / f"case-{case}.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(f"case {case}: {outcome['outcome']} {outcome['reasons']} action {action_id}")


def estate_findings(runner, url: str, S4: dict) -> None:
    """CC-R2 case `estate`: S4 F03 (its 09:30 anchor recurs after 08:00 with no Action: the MG-B stand-in), S4 F05
    through and including its first UNCONFIRMED match (the MG-C stand-in), then diesel price v1 (build spec CC-D2
    "Price": one revision covers both verification windows), before any Action or evaluation."""
    from test_s4_finding_store_postgres import check, run_case

    run_case(runner, S4["F03"])
    for step in S4["F05"]["steps"]:
        outcome = runner.step(step)
        if step["do"] == "match":
            check(runner, outcome, step["expect"], "F05", bool(step.get("collateral")))
            if any(x.get("lifecycle") == "UNCONFIRMED" for x in step["expect"]):
                break
    else:
        raise SystemExit("S4 F05 has no UNCONFIRMED match step")
    from assetops_backend.financials.adapters.postgres_assumption_store import PostgresAssumptionStore
    from assetops_backend.publish_assumption import main as publish

    prices = Path(__file__).resolve().parents[1] / "backend" / "conversions" / "demo-diesel-price-publications.json"
    store = PostgresAssumptionStore(url)
    try:
        code = publish(["fixture", "--site", "KOBO-001", "--file", str(prices), "--step", "v1"], store=store)
    finally:
        import pg_harness as pg

        pg.dispose(store)
    if code != 0:
        raise SystemExit(f"diesel price v1 publication failed ({code})")


def _cursor_key() -> None:
    """The Portfolio route needs a deployment cursor key; a TEST-SCOPED process gets a random one when none is set
    (the post-W6 audit `start_apis.ps1` pattern), never a committed value."""
    import os
    import secrets

    from assetops_backend.estate.scope import PORTFOLIO_CURSOR_KEY_ENV

    os.environ.setdefault(PORTFOLIO_CURSOR_KEY_ENV, secrets.token_hex(32))


def pinned_app(spec: dict):
    """`host/lab_app.py` with the case's window fakes and its Action clock pinned at `pinned_at` (as `serve`)."""
    pinned = datetime.fromisoformat(spec["pinned_at"])
    if spec["fake"] is not None:
        window_fake(spec["fake"])
    import assetops_backend.main as main

    real = main.build_action_service

    def pinned_service(*args, **kwargs):
        kwargs["clock"] = lambda: pinned
        return real(*args, **kwargs)

    main.build_action_service = pinned_service
    sys.path.insert(0, str(Path.cwd().parents[1] / "host"))
    import lab_app

    return lab_app.app


def _placed(row: dict | None) -> tuple:
    if row is None:
        return (None, [])
    return (row["placement"]["group"], [x["code"] for x in row["placement"]["reasons"]])


def estate_assertions(spec: dict) -> dict:
    """CC-R2 Producer 1 end assertions on the served Portfolio body; returns the three rows' placements."""
    from fastapi.testclient import TestClient

    from assetops_backend.estate.money_invariants import double_count_violations

    _cursor_key()
    response = TestClient(pinned_app(spec)).get(ESTATE_PORTFOLIO)
    if response.status_code != 200:
        raise SystemExit(f"estate: Portfolio read {response.status_code}: {response.text[:400]}")
    body = response.json()
    rows = body["rows"]
    failures: list[str] = []

    def one(name: str, pick) -> dict | None:
        found = [r for r in rows if pick(r)]
        if len(found) != 1:
            failures.append(f"{name}: {len(found)} matching rows")
            return None
        return found[0]

    f01 = one("F01 (verified Action)", lambda r: r["action_id"] == spec["action"])
    f03 = one("F03 09:30 recurrence", lambda r: r["episode_start"] == "2026-10-11T09:30:00Z")
    f05 = one("F05 unconfirmed", lambda r: r["episode_start"] == "2026-10-21T08:00:00Z")
    if _placed(f01) != ("MONITOR", ["VERIFIED_WATCH_RETURN"]):
        failures.append(f"F01 placed {_placed(f01)}")
    group, codes = _placed(f03)
    if group != "ACT_NOW" or "RECURRED" not in codes or "NO_ACTION_RECORDED" not in codes:
        failures.append(f"F03 09:30 placed {_placed(f03)}")
    group, codes = _placed(f05)
    if group != "NEEDS_INVESTIGATION" or "LIFECYCLE_UNCONFIRMED" not in codes:
        failures.append(f"F05 placed {_placed(f05)}")
    if any(r["source_provenance"]["state"] in ("UNKNOWN", "MIXED") for r in (f01, f03, f05) if r is not None):
        failures.append("a KOBO-001 row resolves to source UNKNOWN or MIXED (build spec CC-R2 Stop)")
    violations = double_count_violations(body)
    if violations:
        failures.append(f"double-count violations: {violations}")
    if any(r["priority"] is not None for r in rows):
        failures.append("a row has a numeric priority")
    if body["next_cursor"] is not None:
        failures.append("the estate Portfolio does not fit one page")
    if failures:
        detail = [(r["episode_start"], r["lifecycle"], r["source_provenance"]["state"], r["workflow_label"],
                   _placed(r)) for r in rows]
        raise SystemExit("estate: placement assertions failed:\n  " + "\n  ".join(failures) + f"\nrows: {detail}")
    print(f"estate: F01 {_placed(f01)}, F03 {_placed(f03)}, F05 {_placed(f05)}; no double count")
    key = lambda r: f"{r['finding_id']}|{r['finding_revision_id']}"  # noqa: E731 - the page's data-portfolio-row
    # CC-R2-Q4 ruling: the capture script finds the three rows by these keys.
    return {"F01": _placed(f01), "F03": _placed(f03), "F05": _placed(f05),
            "counts": body["summary"]["placement_counts"],
            "rows": {"F01": key(f01), "F03": key(f03), "F05": key(f05)}}


def serve(url: str, work: Path, case: str, port: int) -> None:
    spec = json.loads((work / f"case-{case}.json").read_text(encoding="utf-8"))
    pinned = datetime.fromisoformat(spec["pinned_at"])
    if case == "estate":
        _cursor_key()
    app = pinned_app(spec)
    import uvicorn

    print(f"TEST-SCOPED case {case} served on 127.0.0.1:{port}, Action clock pinned at {pinned.isoformat()}",
          flush=True)
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


def main() -> None:
    if len(sys.argv) < 5 or sys.argv[1] not in ("build", "serve") or sys.argv[4] not in CASES:
        raise SystemExit(__doc__)
    cmd, url, work, case = sys.argv[1], sys.argv[2], Path(sys.argv[3]), sys.argv[4]
    if url.rsplit("/", 1)[-1].endswith("_test") or "assetops_s602b" not in url:
        raise SystemExit("Refused: only a private assetops_s602b* database, never *_test")
    if cmd == "build":
        build(url, work, case)
    else:
        serve(url, work, case, int(sys.argv[5]))


if __name__ == "__main__":
    main()
