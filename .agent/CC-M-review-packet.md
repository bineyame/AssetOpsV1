# CC-M review packet: combined schema slice (owner Q14), migrations 0036 and 0037

Task `tasks/CC-M-combined-schema.md` (Status `in_progress`: phase 1 built; the tier-4 full suites wait for the
coordinator's go). Branch `task/CC-M-combined-schema` from `main` `9cec4fcb`. Contract:
`.agent/build-spec-commercial-2026-10-27.md` "CC-M", Q-C12 and Q-C42.

PYTHONPATH (PowerShell):
```
$env:PYTHONPATH = "C:\Users\assef\Bineyame\AssetOpsV1-ccm\backend;C:\Users\assef\Bineyame\AssetOpsV1-ccm\contracts;C:\Users\assef\Bineyame\AssetOpsV1-ccm\simulator;C:\Users\assef\Bineyame\AssetOpsV1-ccm\gateway;C:\Users\assef\Bineyame\AssetOpsV1-ccm\host;C:\Users\assef\Bineyame\AssetOpsV1-ccm"
```
Python `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe`; `assetops_backend.__file__` names the
`-ccm` worktree. Test DB `assetops_ccm_test` (created for this slice, `assetopsv1-postgres-1`).

## Outcome delivered

- `0036_cc_mini_contribution` (down `0035_w5_ev_work`): drops and recreates the named
  `mini_scenario_revision_kind_check` with `PRODUCTIVE_USE_CONTRIBUTION` added. Downgrade locks the table, raises
  `Downgrade of 0036_cc_mini_contribution refused: PRODUCTIVE_USE_CONTRIBUTION scenario revisions exist.` if any row
  uses the kind, else restores the exact 0030 four-kind CHECK.
- `0037_cc_trial_cost_comparison` (down `0036_cc_mini_contribution`): the append-only
  `trial_cost_comparison_revision` exactly per the CC-M table, with 0019's `SHA`, `KEY` and `DEMO_ACTOR` copied
  into the module (0019 is not edited). Named constraints: `_site_fk` → `site(tenant_id, id)`, `_action_fk` →
  `action(tenant_id, site_id, id)`, `_outcome_fk` `(action_id, verification_outcome_id)` → `verification_outcome
  (action_id, id)`, `_supersedes_fk` → self `(verification_outcome_id, id)` (backed by `_outcome_id_unique`);
  `_revision_no_check`, `_chain_check` `(revision_no = 1) = (supersedes_revision_id IS NULL)`, `_formula_check`,
  `_state_check` (3 states), `_reason_check` (the 11 `REASSESSMENT_REASONS`), `_reason_state_check`; UNIQUEs
  `_revision_no_unique`, `_basis_unique`, `_idempotency_unique (action_id, idempotency_key)`; index `_order
  (tenant_id, site_id, action_id, recorded_at)`; trigger `trial_cost_comparison_revision_immutable` →
  `w4_append_only()`. Downgrade drops the table.
- Head literal `0035_w5_ev_work` → `0037_cc_trial_cost_comparison` at every "current head" site listed in CC-M
  (re-grepped: the same 22 sites in 21 files). Downgrade-target uses stay (`test_w504` `REFUSED`, its docstring).
  `test_w504_ev_intent_postgres.py` gains `MIGRATION = "0035_w5_ev_work"` for its one `get_revision(...)
  .down_revision == PARENT` assertion, which names the migration under test, not the head (the `test_w503` pattern).
- No existing migration edited (the Stop did not trigger).

## Files materially changed

- `backend/migrations/versions/0036_cc_mini_contribution.py`, `0037_cc_trial_cost_comparison.py` (new)
- `backend/tests/test_cc_schema_postgres.py` (new, 3 tests)
- Head literal: `backend/tests/mini_depth_probe.py` and 20 `backend/tests/test_*.py` files (one line each; w504 two)
- `tasks/CC-M-combined-schema.md`, `.ai/ACTIVE_CONTEXT.md` (Lane C line), this packet

## Acceptance criteria

| Gate | Status | Evidence |
|---|---|---|
| upgrade head, downgrade 0035, upgrade head on a fresh `*_test` DB | met | `test_contribution_kind_gate_downgrade_refusal_and_round_trip` (module-fresh DB via `pg_harness.fresh_database`) |
| trigger refuses UPDATE and DELETE | met | `test_trial_rows_chain_scope_and_append_only` ("append only") |
| new kind passes after 0036, fails before | met | same round-trip test: insert at head; refused at 0035 with `constraint_name == mini_scenario_revision_kind_check`; 0036 downgrade refusal while a row uses it |
| chain CHECK refuses revision 2 without supersedes | met | `_chain_check` asserted by constraint name (and revision 1 with a supersedes) |
| `pg_harness.assert_at_head` | met | catalog and round-trip tests |
| full backend + frontend suites (tier 4) | pending | coordinator's go |

The trial rows hang off a real INCONCLUSIVE verification outcome (S4 F01/F02 → S6-01 apply → S6-02a real roles-2
path). The mini scenario kind rows are replica-role direct SQL (CHECKs apply, FK/append-only triggers do not),
because they exercise only the CHECK and the downgrade guard.

## Checks run (phase 1)

- `pytest tests/test_cc_schema_postgres.py` on `assetops_ccm_test`: 3 passed, 22.5 s.
- Non-vacuity: with `_chain_check` and the trigger removed from 0037 (committed first, reverted with
  `git checkout --`), 2 of 3 failed (`DID NOT RAISE DBAPIError`); restored, 3 passed.
- Head-literal files (the 20 changed `test_*.py`, together): 246 passed, 0 failed, 1854 s wall (revision `b64013b6`, `assetops_ccm_test`).
- `tools/check-architecture.ps1`: Architecture check passed. `tools/check-agent-workflow.ps1`: Agent workflow check
  passed. Both run directly, no policy override.
- Coordinator go after review ACCEPT (`.agent/CC-M-review.md`): main `f6237c95` (incl. TEL-06) merged clean as
  `f6090364`. Full backend suite (normal command, `-n 2 --dist loadfile --no-loadscope-reorder`, base
  `assetops_ccm_test`, keep-awake running, cap 200 min): **not completed**. Claude Code's memory-pressure reaper
  stopped it at about 29% with no failure reported up to that point (all dots). No JUnit file. Not restarted, as the
  reaper's notice instructs; it needs a fresh go when memory allows. Run DBs `assetops_ccm_pt21143e8a_{tpl,gw0,gw1}_test`
  are left for the harness's orphan sweep on the next run. No pytest processes are left.
- Rerun on the owner's go (same command and revision `f6090364`; the leftover run DBs were dropped first with
  `pg_harness.cleanup_run`): **not completed**. The memory-pressure reaper stopped it again at about 80%, roughly
  35 min in. No test failure was recorded before the stop. The one `F` in the log comes right after `[gw0] node
  down: Not properly terminated`, which is the worker being killed. No JUnit file. Not restarted. Run DBs
  `assetops_ccm_pt7904a9a5_*` were dropped with `cleanup_run`. No pytest processes are left.
- Not run yet: a completed full backend suite, frontend suite, typecheck, build.

## Known deviations

- None from the spec. The `configuration-persistence.ps1` extension (Q-C13) is placed in CC-D2 by the spec
  ("CC-D2 Files, Guard"; §0.2 "CC-D2 only"); CC-M adds no writer, so no guard rule is added here and the guards pass
  with the new table unregistered. If the coordinator meant it to land in CC-M, it needs the CC-D2 writer path first.
- Packet name: the dispatch names `.agent/CC-M-review-packet.md`; §0.1 groups CC-M with D2 under `-C3-`.

## Residual risk

- Alembic downgrades that cross 0037/0036 (W2-W5 migration tests) now drop the empty trial table and restore the
  kind CHECK first; fine while those tests hold no CC rows. The full suite confirms.
- `w4_append_only()` raises "W4 work history is append only" for this table too (spec-chosen function).

## User-review focus

`USER_REVIEW_REQUIRED`: no (schema only, no UI). A fresh Claude review per slice; CC-M reviews with CC-D2 (group C3).
