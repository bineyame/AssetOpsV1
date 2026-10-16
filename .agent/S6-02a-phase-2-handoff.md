# S6-02a phase 2 handoff (verification core: evaluator, holds, reads, replay)

Branch `task/S6-02a-verification-core` (worktree `AssetOpsV1-review4`), on top of the phase-2 brief `ffcfa1cf`:
`3a564e27` review fixes F1-F8 + evaluator core, `02153973` evaluator Postgres/API tests + verdict tests + API fixture,
`f4eaf141` demo grants include VERIFY, `d4a99292` source-pair mutation survivor pinned, `1b1f82b1` replay manifest +
Lab replay test, `f88f3c8c` closeout docs. Not merged. Phase 2 is the last phase; next is the fresh slice review.

## Anchors

- Pure verdict: `actions/verification_rules.py` `decide`, `source_pair` (end of file); F6 filter and F7 `_iso` in
  `window_evidence` / `_iso`.
- Service: `actions/verification.py` `VerificationPorts`, `_day_states`, `freeze` (F1 `changed_from`, F2 baseline
  CURRENT), `bind_later_selection` (F2/F4), `_assess`, `evaluate` (`compose` decides writes under the lock),
  `current_state`, `outcome`, `history`, `summary`.
- Store (ninth writer): `postgres_action_store.py` `acceptance_fence` (F3, shared with S2 `_coalesce_job`),
  `record_evaluation`, `_insert_evaluator_event`, `late_evidence`, `outcomes`, `covering_ids`, `window_bindings`,
  `is_superseded`; binding idempotency in `append_selection_binding`; migration 0019 binding columns.
- Holds: `actions/service.py` `is_unresolved`, `guardrail_closed`, `reassessment_overlaps`, `trial_refusal`,
  `prior_action_refusal`; `lifecycle.latest_resolution`.
- Composition `actions/composition.py` `verification_ports`; routes in `action_api.py` (evaluations, outcome,
  history; `verification` on Action/Change/Recommendation reads).
- Tests: `test_s6_verification_verdict.py` (10), `test_s6_verification_evaluator_postgres.py` (11),
  `test_s6_verification_plan_postgres.py` (5, updated for F2/F5), `host/tests/test_s6_verification_replay.py` (2).
- Fixtures: `backend/tests/fixtures/s6_verification_api_contract.json` (write with
  `ASSETOPS_WRITE_S6_VERIFICATION_CONTRACT=1`), `s6_action_api_contract.json` (regenerated, additive only),
  `backend/conversions/d-verification-window-v1.json`.

## Open risks

- No VERIFIED Lab replay: the shipped mini-grid generator starts/stops on SOC thresholds and ignores the reserve, so
  lowering the reserve lengthens generator time and breaks initial-SOC comparability; the replay is complete and
  source-coherent but settles INCONCLUSIVE. Needs an Architect decision (model/profile change or accept).
- Verdict/hold Postgres cases use TEST-SCOPED complete windows and an authored source fake over the roles-2 Site.
- Registered scenario/profile lineage is not centrally observable; the pair check uses class, fixtures or distinct
  run digests only.
- Evaluator reads evidence before taking the lock; evidence accepted in that gap with an earlier `decided_at` is not
  flagged late. Freeze fence: an acceptance waiting on the fence may carry a `decided_at` before the plan's
  `recorded_at`.
- Change read keeps apply-time `outcome: PENDING` beside the live `verification` block.
- `.venv` in this worktree is a junction to the main checkout's venv (check-all needs it).

## Fix round 1 notes (for S6-02b and the merge)

- F5 (S6-02b): take the verification presentation from the Action read's `verification` block (`current_state`), never from `state.outcome`; `state.outcome` follows resolution events and keeps VERIFIED until the evaluator appends RESOLUTION_WITHDRAWN, and the Change read keeps its apply-time `outcome: PENDING`.
- F4: an INCONCLUSIVE Action continues by freezing a new plan with `supersedes_plan_id` (`VerificationService._continuation_check`); refusals are `VERIFICATION_PLAN_EVALUATED` with `reason`. The shipped Lab replay's INCONCLUSIVE can now lead to a later trial plan.
- F2: RESOLUTION_WITHDRAWN payload carries `attribution`, `invalidating_evidence`, `basis_changes`, `candidate_evidence_ids`; overlap reads CAUSAL only.
- F3 deviation: moved baseline selection settles INCONCLUSIVE (`BASELINE_SELECTION_CHANGED`), recoverable via F4 continuation.
- Merge with S4-05b (coordinator note): whichever merges second keeps both `source=` and `publish=` wiring, drops every `demonstration` field, regenerates the contract fixtures, reruns `test_s6_*` and greps for `demonstration_`. This fix round touched `actions/service.py` only in `reassessment_overlaps` and added no `demonstration_label` use.

## Fix round 2 notes (re-review R1; R2/R3 carried)

- R1 fixed: `_attribution` replays each changed window by acceptance prefix (`arrivals`); a reading is causal only when its own arrival changes the window result and it entered the used evidence. Duplicates and no-change readings stay in `candidate_evidence_ids` only and never move the overlap boundary. Same-instant readings are tested one by one (others excluded via `_windows(exclude=...)`) and recorded jointly only when none changes the result alone.
- R2 carried (Low, fail-toward-hold): a bound late reading whose only effect is to make the per-window source resolution non-coherent (identical values, another run/class) records `NONE`; the ordinary hold remains, no permanent overlap. Close by comparing per-window source resolution of the closed vs reassessed evidence ID sets under closure-time provenance.
- R3 carried (Low, fail-toward-hold): a reading whose only effect is to move a pinned S3 selection while the window result is unchanged records `INDETERMINATE` (ordinary hold, never an overlap), per the ruling's "cannot be established" clause.
