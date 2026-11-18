# S6-02a phase 1 handoff (verification core)

Branch `task/S6-02a-verification-core` (worktree `AssetOpsV1-review4`). Commits on top of `07de54ac`:
`c85529c1` migration/lock/rules, then roles-3/Lab profile, then `3b57514b` plan freeze/reads, then guard probes.
Not merged. Phase 1 is complete as scoped below; phase 2 is the evaluator and slice review.

## What landed (anchors)

- **Migration** `backend/migrations/versions/0019_verification_core.py` (after `0018_finding_match_deferral`):
  insert-only `verification_plan` (window/same-clock/order CHECKs, same-Site FKs, `supersedes_plan_id` chain,
  one root per Action, idempotency unique), `verification_selection_binding`, and phase-2 tables
  `verification_evaluation_request`, `verification_outcome` (VERIFIED/INEFFECTIVE/INCONCLUSIVE only;
  `GUARDRAIL_FAIL` reason only on INEFFECTIVE), `verification_metric`. `action_event` gains `RESOLVED` /
  `RESOLUTION_WITHDRAWN`, command `EVALUATE`, channel `SYSTEM_JOB`, columns `verification_plan_id` /
  `verification_outcome_id`, and `action_event_evaluator_job` (actor `service:verification-evaluator`, basis
  `SYSTEM_VERIFICATION_EVALUATOR`, non-null `triggering_job`). Downgrade refuses when plans/resolutions exist.
  Head assertions bumped in five existing tests.
- **Battery-scoped trial lock** `postgres_action_store.py` `trial_lock` / `_trial_actions` / `trial_actions`:
  key `action-trial:tenant:site:asset:field:rule`; `accept` guards over every Action at that scope (any Finding).
  `service.py` `recommendation` and accept pre-check use the same scope (no live offer: every battery of the Site).
  `is_unresolved`/`lifecycle.reduce` are unchanged (resolution events are phase 2).
- **Rules** `actions/verification_rules.py` (pure, Fraction): `window_problem`, `slot_starts`, `power_slot`,
  `soc_samples`, `reserve_at_slots`, `window_evidence`, `comparability`, `target_days`, `target_window`,
  `target_met`, `bands_payload`. Tests `test_s6_verification_rules.py` (45).
- **Roles/Lab**: `minigrid-roles-3` (`sites/binding_roles.py`; `critical_load_requested_power`,
  `critical_load_delivered_power`, LOAD/kW/ONE, bound to the first `critical-load-priority` load, enforced by
  `BINDING_CRITICAL_LOAD_MISMATCH` in `binding_service.validate_bindings`), `verification-readiness-1`
  Lab/real-Site messages exposed as `readiness().verification_readiness` for roles-3 only. Default publication set
  stays roles-2. Mini-grid model v4 (`simulator/.../packs/mini_grid.py`, state `load-requested-power`) and
  `registered-kobo-publication` v4 (`runs/profiles.py`, five-minute INTERVAL_MEAN power, five-minute SOC/status,
  `clinic-meter/requested-power` and `clinic-meter/delivered-power`). Fixture
  `backend/conversions/kobo-001-s6-verification-demo-config.json`. Proof `host/tests/test_s6_verification_publication.py`
  (incl. Postgres `test_interval_declarations_survive_central_acceptance`).
- **Service/API** `actions/verification.py` (`VerificationService.freeze`, `bind_later_selection`, `plan`,
  `evidence`), routes in `action_api.py`: `POST .../verification/plans`, `POST .../verification/plans/{plan_id}/later-selection`,
  `GET .../verification/plan`, `GET .../verification/evidence` (`plan_id` | `recorded_at`, conflict 422, 404).
  Capability command `VERIFY` added to `lifecycle.COMMANDS`.
- **Guards**: `$actionTables` += five verification tables (`configuration-persistence.ps1:707-709`); probes in
  `tools/writer_guard_probes.py` (plan update, outcome delete, binding upsert, reverse metric insert, plan insert control).
- **Fixture**: `backend/tests/fixtures/s6_action_api_contract.json` regenerated. Normalised diff is exactly three
  paths: `blocking_actions` grows 1 -> 2 (the other-Finding Action on the same battery). Existing two-Action tests
  create the second Action through the store with a pass-through guard (`s6_action_records.accepted_before_battery_hold`).

## Proof run (phase 1, focused)

- `test_s6_verification_plan_postgres.py` 5 passed; with adjacent s6 store/apply/records, s3 dispatch, s1 bindings,
  s3 role vocabulary, rules: `109 passed` (`-n 4 --dist loadfile`).
- Mutations (`scratchpad/s602a/mutate.py`), all KILLED, tree clean: battery lock removed; comparability UNKNOWN
  not overriding; trailing slot gap accepted; later-window cutoff removed; positive-Candidate check removed.
- `check-architecture.ps1` and `check-agent-workflow.ps1` passed.
- Writer probes NOT proven: `tools/writer_guard_probes.py` was stopped by the host for low memory after 33 probe
  lines (all earlier probes CAUGHT; the new verification probes were not reached). The interrupted probe's
  mutation of `postgres_schedule_store.py` was restored with `git checkout`. Rerun the probes in phase 2/review.

## Next (phase 2)

Evaluator job (outcome + metrics + RESOLVED/RESOLUTION_WITHDRAWN in one transaction under `trial_lock`), per-window
S4-05 source resolution, S3/S4 pending-work gates and REASSESSMENT_PENDING, `lifecycle.reduce`/`is_unresolved` from
latest resolution, guardrail block `PRIOR_TRIAL_GUARDRAIL_FAILED` and overlap block `PRIOR_TRIAL_REASSESSMENT_OVERLAP`
(R1: only late evidence that invalidated the closure counts; test both sides), evaluation request route,
outcome/history reads, Action/Recommendation/Change verification state, versioned API fixture, the
`D-verification-window` replay manifest (two registered Lab runs on a roles-3 Site), grants `VERIFY` for the demo,
full suite and `check-all`.

## Open risks / deviations

- "Later run has begun" is detected from accepted later-window evidence only; no Lab run-start signal is consulted.
- Freeze takes each day's latest DEFAULT selection; it does not yet gate on S3 CURRENT/no pending jobs (phase 2 gates).
- The replay manifest itself is not produced in phase 1 (profile, model, roles, fixture and acceptance proof are).
- The S4 case Site used by the Postgres tests binds roles-2, so its evidence reads are never complete (by design).
- Rules timestamps serialise as `...000000Z`; other API fields use `+00:00`.
- Mini-grid v4 and profile v4 are new; v1-v3 outputs were re-run unchanged by the sub-implementer's simulator/host tests.
