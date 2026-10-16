# S6-02a review packet - frozen verification, evaluator and exact read

Task `tasks/S6-02a-verification-core.md` (Status `in_review`; USER_REVIEW_REQUIRED false: non-UI, mergeable after a
fresh independent slice review). Branch `task/S6-02a-verification-core`, worktree `AssetOpsV1-review4`, main
`e39a3c20` merged in. Phase 1: `.agent/S6-02a-phase-1-handoff.md`, review `.agent/S6-02a-phase-1-review.md`.
Phase 2: `.agent/S6-02a-phase-2-handoff.md`. Final revision `f88f3c8c` (code; this packet is gitignored).

## Outcome delivered

- Phase-1 review fixes F1-F8 (below).
- Evaluator job: one transaction under the battery `trial_lock` writes evaluation request, outcome, metrics and
  RESOLVED / RESOLUTION_WITHDRAWN. Identical retries (same key, or same basis with a new key) return the same outcome
  ID; a changed basis appends a superseding outcome (`supersedes_outcome_id`). Only `service:verification-evaluator`
  over `SYSTEM_JOB` writes resolution events; the VERIFY caller never supplies a verdict (CLIENT_AUTHORITY_FORBIDDEN).
- Verdict `decide`: VERIFIED / INEFFECTIVE (GUARDRAIL_FAIL only for a measured guardrail failure; TARGET_MISS) /
  INCONCLUSIVE when anything required is unknown, with known failures kept as `KNOWN_FAILURE:*`.
- Per-window S4-05 source resolution (`source_pair`, never the union). S3 `derive_status` + S4 `match_state` gates;
  PENDING (window open, not bound) and REASSESSMENT_PENDING (non-current or moved day, late evidence, changed
  covering Foundation) as read states, not outcomes.
- `lifecycle.reduce` / `is_unresolved` from the latest resolution. Holds `PRIOR_TRIAL_GUARDRAIL_FAILED` and
  `PRIOR_TRIAL_REASSESSMENT_OVERLAP` (R1: only the withdrawal's named late evidence counts; both sides tested),
  shared by the accept guard (under the lock) and the Recommendation read.
- Routes: POST `.../verification/evaluations`; GET `.../verification/outcome` (`outcome_id` | `recorded_at`, typed
  conflict, historical label), `.../verification/history`. Action, Change and Recommendation reads carry
  `verification`.
- Versioned API fixture `backend/tests/fixtures/s6_verification_api_contract.json` (`+00:00` asserted on every
  timestamp). Replay manifest `backend/conversions/d-verification-window-v1.json` with
  `host/tests/test_s6_verification_replay.py`. Demo grants include VERIFY.

## Files materially changed (phase 2)

`backend/assetops_backend/actions/{verification.py, verification_rules.py, service.py, lifecycle.py, composition.py,
adapters/postgres_action_store.py}`, `backend/assetops_backend/action_api.py`,
`backend/migrations/versions/0019_verification_core.py` (binding idempotency columns), tests
`backend/tests/test_s6_verification_{verdict,evaluator_postgres,plan_postgres}.py`, `backend/tests/s6_action_records.py`,
fixtures `s6_verification_api_contract.json` (new), `s6_action_api_contract.json` (regenerated: normalised diff is
additive only - `verification_plan_id`/`verification_outcome_id` on events, `verification` on reads, the F8 note),
`backend/conversions/d-verification-window-v1.json`, `host/tests/test_s6_verification_replay.py`.

## Phase-1 review fixes

| ID | Fix | Proof |
| --- | --- | --- |
| F1 | Freeze refuses `VERIFICATION_FOUNDATION_NOT_COMPARABLE` unless the baseline revision is the change's split or superseded revision | `TestCurrentnessGates::test_f1_...` (intervening runtime publication, refused) beside the plan pass case; mutation killed |
| F2 | Freeze needs every baseline day S3 CURRENT; binding needs `later_end` passed, head plan and CURRENT later days; evaluation needs both pinned windows CURRENT on the pinned run and S4 matched | stale and FAILED baseline days refused; binding before/after `later_end`; pinned later day turning STALE -> REASSESSMENT_PENDING; mutation killed |
| F3 | Cutoff kept as first accepted later-window report; freeze takes the S2 acceptance advisory lock (`_coalesce_job` key) so check+insert serialize with acceptance; no S2 change | other role/asset at exactly `later_start` trips it; report just before does not; held (unaccepted) report does not; freeze waits on an in-flight acceptance (pg_locks); mutation killed |
| F4 | Binding `idempotency_key` + `payload_sha256` persisted and compared; non-head plan refused | plan and evaluator tests |
| F5 | Race test prints outcomes, sleep 0.2 s | file passes |
| F6 | Window evidence filtered to the plan battery (SOC) and bound assets | `test_f6_...` |
| F7 | `+00:00` everywhere (rules `_iso`) | `test_f7_...`; fixture asserts every timestamp |
| F8 | `notes.pre_s6_02a_second_action` in `s6_action_api_contract.json` | fixture |

## Acceptance criteria (phase 2 row)

- Every verdict/guardrail: unit (`test_s6_verification_verdict.py`, 10) + Postgres VERIFIED, guardrail INEFFECTIVE,
  target-miss INEFFECTIVE, real INCONCLUSIVE - met (verdict Postgres cases use TEST-SCOPED windows, see KD2).
- Per-window provenance - met (real UNKNOWN per window on Kit evidence; REGISTERED_SIMULATION pair PASS in the replay).
- Pending/late/backdated Foundation - met (late evidence; FOUNDATION_CHANGED blocker in code; backdated runtime case
  covered at freeze by F1).
- Same/different Finding races - evaluator waits on the trial lock (mutation killed); battery race from phase 1.
- Evaluation trigger and overlap timing, both sides - met. Exact cutoff/retry - met. 401/403/404 - met.
- Adjacent S6 store/apply/records - pass. Fixture regenerated with additive diff - met. Rule-8 guard cases - probe
  corpus 72/72 caught, controls allowed. Private DB run->accept->reload - replay test.
- Complete positive replay path - NOT met (KD1).

## Checks run

- `tools/check-all.ps1` at `f88f3c8c`: 9/9 guards passed (worktree `.venv` is a junction to the main venv).
  Registry checker `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: exit 0.
- `tools/writer_guard_probes.py --seam` (full corpus incl. the five verification probes): 72 CAUGHT, controls
  ALLOWED, exit 0, tree restored (27 min). The rule-8 guard also caught a real dynamic-table insert during the build.
- Mutations (`scratchpad/mutate2.py`), all KILLED, tree clean: unknown-overrides-failure, MIXED source accepted (after
  a strengthened test), guardrail closure releases hold, overlap ignores evidence time, evaluator skips trial lock,
  freeze skips acceptance fence, non-CURRENT day treated current, F1 tie removed.
- Focused: verdict 10, evaluator 11, plan 5, rules 45, S6 store/apply/records 21, host replay+publication 7 passed.
- Full suite at `f88f3c8c` (PowerShell): `python -m pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder -q
  -p no:cacheprovider --junitxml=<scratchpad>/s602a-full2-junit.xml`, base DB `assetops_s602ap2_test`: **2464 passed,
  0 failed, 0 skipped, 0 errors** (JUnit), wall 1233 s (20.5 min, under the 40-min cap). A first run at the same
  revision had 1 failure, `test_runs_api.py::...test_the_shipped_scenario_blocks_only_on_the_values_this_site_lacks`
  (`FileNotFoundError: var\sites\mg-001.yaml`): the worktree lacked the gitignored `var/sites`; copied from the main
  checkout per the brief, file rerun 28 passed, then the full rerun above. Keep-awake was not running (host policy).

## Known deviations

1. **No VERIFIED Lab replay.** The shipped mini-grid generator starts at 35 % and stops at 90 % SOC and never reads
   the reserve; lowering it (30 -> 25) drains the battery further, lengthens generator time (03:45-09:35 vs
   03:45-09:15) and puts initial SOC 5 points apart. The replay is complete (12/12 slots per window, every role,
   terminal SOC) and source-coherent (two REGISTERED_SIMULATION runs, distinct digests) but settles INCONCLUSIVE
   (`NOT_COMPARABLE`, known target and terminal-SOC failures). Faking conditions was refused. Architect decision
   needed: a reserve-aware dispatch model/profile version, or accept the complete-but-inconclusive replay.
2. Verdict/hold Postgres cases replace only the pure window evidence and source resolution with labelled
   TEST-SCOPED complete windows (the roles-2 S4 case Site can never complete a window); the API fixture says so.
3. Registered scenario/profile lineage is not centrally observable (no scenario in provenance); the pair check uses
   source class, authored fixtures, or distinct run digests.
4. Overlap is derived at read time from the withdrawal payload's named evidence and Action `created_at`, not stored.
5. The manifest's non-pass cases point at test-scoped Postgres tests, not Lab replays.

## Residual risk

Narrow late-evidence gap between the evaluator's read and its commit; an acceptance that waited on the freeze fence
may carry an earlier `decided_at`; Change read keeps its apply-time `outcome: PENDING` beside `verification`; demo
scripts must expect 503 on 5 s lock contention; registry nodes stay `open` until review.

## User-review focus

None required (non-UI). Architect: KD1. Reviewer: `evaluate.compose` resolution sequencing, `reassessment_overlaps`
window, `current_state` reasons, and the F3 fence choice.
