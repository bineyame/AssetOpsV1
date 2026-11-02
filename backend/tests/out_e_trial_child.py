"""OUT-E E3 child: one cost-check scenario built by the S6 evaluator test builders on a fresh case database.

    python out_e_trial_child.py <case-database-url> <out.json> <case>

Run by `test_out_e3_trial_comparison_postgres.py` only, from `backend/tests` with `ASSETOPS_TEST_DATABASE_URL` set
to the case database (the builders read it at import). Cases: `verified` (the s602b `verified` steps, then the same
evaluation re-posted: a replay), `target_miss`, `inconclusive` (the s602b steps; real roles-2 windows) and
`failure` (target_miss windows with the cost-check store's `append` raising). Diesel price v1 is published after
the Finding cases and before any evaluation. Writes the stored cost-check revisions, outcomes and plan digests.
"""

from __future__ import annotations

import json
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))


def run(url: str, case: str) -> dict:
    from sqlalchemy import create_engine, text

    import test_s6_verification_evaluator_postgres as ev
    from s602b_test_scoped_cases import VERIFIED_WINDOWS, Patch, publish_price_v1
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore
    from test_s4_finding_store_postgres import CaseRunner, run_case
    from test_s6_action_store_postgres import CASES as S4
    from test_s6_verification_plan_postgres import applied_action, deliver_later, freeze, verifying

    engine = create_engine(url)
    store = PostgresFoundationStore(url)
    runner = CaseRunner(store, engine)
    run_case(runner, S4["F01"])
    run_case(runner, S4["F02"])
    h = verifying(runner)
    rec: dict = {"case": case}
    try:
        publish_price_v1(url, runner.now)
        if case == "verified":
            ev.complete_windows(Patch(), h, **VERIFIED_WINDOWS)
            action_id, plan, _ = ev.bound_plan(runner, h)
            h.clock.at = ev.CLOSED + timedelta(hours=1)
            first = ev.evaluate(h, action_id, "eval-0001")
            again = ev.evaluate(h, action_id, "eval-0001")
            rec["status"] = [first.status_code, again.status_code]
            rec["replayed"] = again.json()["replayed"]
            outcome = first.json()["outcome"]
        elif case in ("target_miss", "failure"):
            ev.complete_windows(Patch(), h)
            if case == "failure":
                from assetops_backend.financials.adapters import postgres_trial_comparison_store as st

                def boom(self, row):
                    raise RuntimeError("injected cost-check store failure")

                st.PostgresTrialComparisonStore.append = boom
            action_id, plan, _ = ev.bound_plan(runner, h, later=deliver_later)
            made = ev.evaluate(h, action_id, "eval-0001")
            rec["status"] = [made.status_code]
            outcome = made.json()["outcome"]
        elif case == "inconclusive":
            action_id = applied_action(runner, h)
            plan = freeze(h, action_id).json()["plan"]
            assert ev.evaluate(h, action_id, "eval-0001").json()["state"] == "PENDING"
            h.clock.at = ev.CLOSED
            ev.later_generator_off(runner)
            ev.caught_up(runner, h, ev.CLOSED)
            assert ev.bind(h, action_id, plan["plan_id"], "bind-0001").status_code == 201
            made = ev.evaluate(h, action_id, "eval-0003")
            rec["status"] = [made.status_code]
            outcome = made.json()["outcome"]
        else:
            raise SystemExit(f"unknown case {case}")
        rec["outcome"] = {k: outcome[k] for k in ("outcome_id", "outcome", "reasons")}
        rec["plan_sha256_frozen"] = plan["plan_sha256"]
        with engine.connect() as c:
            rec["revisions"] = [dict(r._mapping) for r in c.execute(text(
                "SELECT verification_outcome_id, revision_no, state, reason, result, intervention_cost, "
                "price_revision_id, actor_kind, actor_id, source_channel, idempotency_key "
                "FROM trial_cost_comparison_revision ORDER BY recorded_at"))]
            rec["outcomes"] = c.execute(text("SELECT count(*) FROM verification_outcome")).scalar_one()
            rec["plan_sha256_stored"] = c.execute(text("SELECT plan_sha256 FROM verification_plan WHERE id = :p"),
                                                  {"p": plan["plan_id"]}).scalar_one()
            details = c.execute(text("SELECT details FROM verification_outcome WHERE id = :o"),
                                {"o": outcome["outcome_id"]}).scalar_one()
            rec["details_window_keys"] = sorted(details["windows"]["baseline"])
    finally:
        h.close()
        import pg_harness as pg

        pg.dispose(runner.findings)
        pg.dispose(store)
        engine.dispose()
    return rec


if __name__ == "__main__":
    out = run(sys.argv[1], sys.argv[3])
    Path(sys.argv[2]).write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
