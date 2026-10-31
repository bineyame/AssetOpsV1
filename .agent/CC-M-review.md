# CC-M review: combined schema slice (owner Q14), migrations 0036 and 0037

Reviewer: fresh Claude reviewer (not the author). Branch `task/CC-M-combined-schema` at `01e272b7`, diffed against
`main` `9cec4fcb`. Authority: `.agent/build-spec-commercial-2026-10-27.md` "CC-M", Q-C12, Q-C13, Q-C42.

## Verdict: ACCEPT

There are no High or Medium findings. The tier-4 full backend and frontend suites are still pending; they are the
coordinator's merge gate, and this review did not run them.

## Verified

- **0036** (`backend/migrations/versions/0036_cc_mini_contribution.py:23-38`). It drops the named
  `mini_scenario_revision_kind_check` and recreates it with `PRODUCTIVE_USE_CONTRIBUTION` added. The downgrade takes an
  ACCESS EXCLUSIVE lock, raises while any row uses the kind, and then restores the four-kind CHECK. That restored CHECK
  is byte-identical to 0030:82. The chain `down_revision = "0035_w5_ev_work"` is correct.
- **0037** (`backend/migrations/versions/0037_cc_trial_cost_comparison.py:49-94`) matches the spec table
  column for column:
  - Types and nullability are as specified, with nullable `supersedes_revision_id`, `reason` and `price_revision_id`.
  - `price_revision_id` has no FK.
  - The `SHA` and `KEY` columns are as specified, and `DEMO_ACTOR` is identical to 0019:33-42.
  - The site, action and outcome FKs are present, as is the self FK on `(verification_outcome_id, id)`, which is
    backed by `_outcome_id_unique`.
  - The CHECKs are present: `revision_no > 0`, the chain check `(revision_no = 1) = (supersedes_revision_id IS NULL)`,
    the formula, the 3 states, the 11 reasons, and reason-iff-UNAVAILABLE.
  - The uniques are present: `(outcome, revision_no)`, `(outcome, basis_sha256)` and `(action_id, idempotency_key)`.
  - The index is on `(tenant_id, site_id, action_id, recorded_at)`.
  - The trigger `trial_cost_comparison_revision_immutable` runs BEFORE UPDATE OR DELETE and calls `w4_append_only()`
    from 0027.
  - The downgrade drops the table.
- **No existing migration was edited.** `git diff --name-status` over `backend/migrations` shows only the two new files
  (A).
- **The head literal is updated everywhere.** I grepped `0035` across `*.py/ps1/ini/toml/mjs/ts` myself. No
  "current head" use of `"0035_w5_ev_work"` remains, and every site the spec lists now reads
  `0037_cc_trial_cost_comparison`. The uses that remain are all legitimate:
  - downgrade targets: `test_cc_schema_postgres.py` `PREVIOUS`, and the `test_w504` `REFUSED` text;
  - the 0036 `down_revision`;
  - comments and docstrings;
  - `test_w504_ev_intent_postgres.py:46` `MIGRATION`, which now carries the
    `get_revision(...).down_revision == PARENT` assertion at :125. That assertion names the migration under test, not
    the head, so it is correct. Without the change it would have asserted that 0037 descends from 0034.
- **The `configuration-persistence.ps1` deferral is correct.** The spec places the guard extension in CC-D2 ("CC-D2
  Files, Guard" at spec:253; §0.2 "CC-D2 only" at spec:32; Q-C13). CC-M adds no writer, so a writer-path rule would
  have nothing to register.
- **The test** (`backend/tests/test_cc_schema_postgres.py`):
  - It asserts the full catalog: columns, constraint names by type, the index and the trigger.
  - It checks that the kind is admitted at head, refused at 0035 (by constraint name), and that the 0036 downgrade is
    refused while a row uses the kind.
  - It runs the 0035 round trip and calls `assert_at_head`.
  - It asserts each CHECK, FK and UNIQUE by constraint name.
  - It checks that the trigger refuses both UPDATE and DELETE.
  - The trial rows hang off a real outcome. The packet claims the test is non-vacuous; I did not re-verify that claim,
    but the assertions name the constraints, which makes the claim plausible.

## Findings

### Low

- **L1 (preference; no fix needed for merge).** The spec gate at `.agent/build-spec-commercial-2026-10-27.md:241`
  names a fresh `assetops_cc_schema_test`. The test instead uses the module-fresh DB from `pg_harness` (through the
  `engine` fixture), and that DB serves the same purpose. This is an equivalent substitute, not an acceptance gap.
- **L2 (residual risk, spec-chosen).** The 0037 downgrade at
  `backend/migrations/versions/0037_cc_trial_cost_comparison.py:98-99` drops the table without checking for rows. The
  spec asks for exactly this. Once CC-D2 writes rows, a downgrade below 0037 will discard reassessment history without
  warning. Unlike 0036, there is no refusal guard. If that matters, it belongs to CC-D2 or a later Architect decision.
- **L3 (cosmetic).** `w4_append_only()` raises "W4 work history is append only" for this table too. The packet already
  names this, and the spec chose the function.

## Checks run (by this reviewer, revision `01e272b7`)

- `pytest tests/test_cc_schema_postgres.py -q` ran on a fresh `assetops_ccmrev_test`, which I created in
  `assetopsv1-postgres-1` and dropped afterwards. Result: **3 passed**, 20.6 s.
- `tools/check-architecture.ps1`, run directly with `ASSETOPS_GUARD_PYTHON` set to the plan2 venv: **passed**.
- `tools/check-agent-workflow.ps1`, run the same way: **passed**.

## Not verified

- I did not rerun the 20 edited head-literal test files. The packet reports 246 passed and 0 failed in 1854 s at
  `b64013b6`. The only commit after that, `01e272b7`, touches docs and the task file only.
- The full backend suite, frontend suite, `tsc` and build are tier 4 and pending. That is out of scope by dispatch.
- I did not independently reproduce the packet's non-vacuity run (constraint and trigger removed, 2 of 3 failing).
