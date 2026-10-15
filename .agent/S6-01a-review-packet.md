# S6-01a review packet - Action store, controlled application and exact read

Task `tasks/S6-01a-action-store-read.md` (status `in_review`). Branch `task/S6-01a-action-store-read` from main `fd7afd2c`. Code-final revision `586d5fe1` after the reopen round below (slice review was on `375c8cf9`; closeout docs after it). Authority `D-2026-10-15-s601-action-store-and-ui` (`.agent/architect-S6-01-answers.md` Q1-Q5, M1-M3). USER_REVIEW_REQUIRED: **false** (non-UI). This phase-2 review is the slice review. Not merged.

## Outcome delivered

A real stored demonstration runs accept, apply, reload against PostgreSQL through the API. For a reviewed, current, SUPPORTED `GENERATOR_SUPPORT_CANDIDATE` FindingRevision, `reserve-trial-1` is served from persisted inputs. Accepting it creates an Action with an immutable snapshot and an ACCEPTED event. Apply then runs as one transaction:

1. lock the Action row;
2. run the S1 publish on that connection (Site lock, expected-revision check, no-change check, expected-reserve check, Foundation/SPLIT/binding rows);
3. insert the change artifact and APPLIED;
4. commit once.

An authorized same-Site failure rolls everything back, then appends FAILED in a separate transaction. A state-neutral backdated OBSERVED event can be recorded. Action and event reads take an exact `event_id` or `recorded_at` selector, and the change artifact has its own read. The `D-action-records` loader produces the committed API contract fixture that S6-01b consumes.

## Files materially changed

- `backend/migrations/versions/0014_action_store.py`: the six Action tables, FKs and append-only triggers. Phase 2 added `action_event_action_unique`, `action_policy_change_own_event_fk`, the event expected/current Foundation FKs (review L4) and `action_event_apply_basis`.
- `backend/assetops_backend/actions/`:
  - `adapters/postgres_action_store.py`: `apply`, `_insert_applied`, `_append_failed`, change reads, `current_foundation`.
  - `service.py`: `apply`, `authorize_*`, `_change_wire`, `_application_basis`, demonstration and money-consequence link.
  - `capability.py`: grants v2.
  - `composition.py`: `foundation_publish`, `S1_FAILURES`.
  - `ports.py`: `ApplyFailed`, `FoundationPublish`.
- `backend/assetops_backend/sites/`:
  - `foundation_service.py`: `CallerTransaction`, `written_ids`, the expected checks and `caller=`.
  - `adapters/postgres_foundation_store.py`: `publish_configuration(..., connection=, then=)` and the `_run(connection=)` path.
  - `foundation_records.py`: port signature.
- `backend/assetops_backend/action_api.py`: apply and change routes, refusal order. `main.py` passes `registry=`.
- Tests:
  - `backend/tests/test_s6_action_apply_postgres.py` (new, 11 tests).
  - `test_s6_action_records_postgres.py` and `s6_action_records.py` (new).
  - `fixtures/s6_action_api_contract.json` (new).
  - `test_s6_action_store_postgres.py` and `test_s6_action_rule.py` (grants v2).
- `tools/checks/configuration-persistence.ps1` (rule 8, phase 1).

## Acceptance criteria

| Criterion | Status | Evidence |
| --- | --- | --- |
| Action created on acceptance; recommendation key and acceptance digest pin the FoundationRevision; replay and 409 | Met (phase 1) | `test_s6_action_store_postgres.py::TestRecommendationAcceptAndReload` |
| `reserve-trial-1` rule, boundaries and typed reasons from persisted inputs | Met (phase 1) | `test_s6_action_rule.py`; SOC 30 vs 30.5 on persisted evidence |
| Accepted snapshot survives a reserve change; live status labelled separately | Met | phase-1 test; contract `recommendation:1#a.accepted_snapshot_live_status` |
| Apply: Action lock, then caller-owned S1 publish (Site lock, expected ID) then artifact and APPLIED, one commit; every written/superseded ID | Met | `TestApplyPublishesAtomically` checks every Foundation and binding row against the artifact |
| Action-before-Site lock order | Met | `test_action_row_is_locked_before_the_site`: while the Site is held, the apply waits on it and `FOR UPDATE NOWAIT` on the Action fails |
| Rollback of Foundation, bindings, artifact and APPLIED together | Met | `test_failure_after_the_s1_writes_rolls_everything_back` (failure injected after every insert) |
| Concurrent identical and distinct applies publish once | Met | `test_concurrent_identical_applies_publish_once` [200,200,200,201]; `..._distinct_...` [201,409×3] |
| FAILED after rollback: stale 409; invalid, no-change and backdate 422; retry returns the stored FAILED; fresh key applies; FAILED never reverts APPLIED | Met | `TestFailedAfterRollback` (3 tests), `TestJustStaleBasis` |
| `ACTION_ALREADY_APPLIED` 409 with no FAILED; identical applied retry returns the artifact before no-change | Met | `test_apply_artifact_reload_retry_and_already_applied` |
| 401, 403, capability, wrong-Site and unknown IDs append nothing | Met | `test_refusals_append_nothing`; `test_real_cross_site_reads_and_writes_are_404_and_fks_refuse` (a real second Site) |
| Effective time ≥ server recorded time and > ACCEPTED | Met | `ACTION_EFFECTIVE_TIME_INVALID` cases |
| OBSERVED bounds, retry, state-neutral; server order kept | Met (phase 1 + fixture) | `TestObservedAndExactHistory`; contract `action-history:1#a` |
| Exact selectors, ties, conflict 422 | Met | phase-1 tests; contract `action-history:1#a` |
| `GET /foundation/changes/{id}`; Action read `change` | Met | apply tests; contract `changes:1#a` |
| `D-action-records` fixture/loader with eligible and ineligible records, real records, manifest IDs | Met | `s6_action_records.py`; walkthrough below |
| Committed API contract fixture keyed by manifest IDs, checked against real responses | Met | `test_d_action_records_walkthrough_and_contract` (normalised equality, stable over 3 runs) |
| Rule-8 ninth writer | Met (phase 1) | `tools/check-all.ps1` 9/9 |
| S4 money consequence "only for its exact basis, labelled consequence" | Met as link | `money_consequence` links the exact FindingRevision's S4 consequence, labelled "Consequence", no amount (see deviations) |
| Demonstration label on Action reads | Met | `demonstration` uses `demonstration_case` on the origin episode, and on the recommendation |

## Phase-1 review fold-in

The coordinator relayed the findings. The review file itself (`AssetOpsV1-review3/.agent/S6-01a-phase-1-review.md`) was not present when this packet was written.

- **M1:** grants v2 requires `tenant_id`, `site_id` and `records` (manifest ID to Finding ID).
  - Accept targets the path Finding. Apply and OBSERVED target the Action's origin Finding.
  - Test `test_non_fixture_finding_and_its_action_are_refused_403`: accept, apply and observe all return 403, nothing is written, and the read capability shows "not a record".
- **L1:** the 409 is kept. The contract `notes.ACTION_ACCEPTANCE_CONFLICT` says it means "already accepted, follow `action_id`", and case `accept_conflict_already_accepted` is in the contract.
- **L3:** a real second Site gets 404 on read, events, change and apply, with no rows written. Direct inserts are refused by the composite FKs:
  - an Action on another Site;
  - an origin revision belonging to another Finding;
  - an event on another Site;
  - an event naming another Site's Foundation.
  - A same-Site control insert is accepted.
- **L4:** the event expected/current FKs are in 0014.
- **L5:** `occurred_at`, and also `effective_from`, are normalised to UTC before hashing.

## Checks run (all on `375c8cf9` unless noted)

- **Focused tests:**
  - `test_s6_action_rule.py` + `test_s6_action_store_postgres.py` + `test_s6_action_apply_postgres.py`: 78 passed (80 s).
  - `test_s6_action_records_postgres.py`: 1 passed (about 14 s). Run 3 times; normalised equality held each time.
- **Adjacent tests:** `test_s1_bindings_postgres`, `test_s1_foundation_postgres`, `test_s1_cutover`, `test_s1_bindings`, `test_s4_finding_read_postgres`, `test_s4_finding_api` and `test_pg_harness`: 116 passed.
- **`tools/check-all.ps1`:** 9/9 PASS. This includes the dependency registry. It used a temporary `.venv` junction, which was removed.
- **Mutation checks.** Each was reverted with `git checkout`, and the worktree was clean afterwards:
  - Action `FOR UPDATE` removed: 3 failed (lock order and both races).
  - FAILED append skipped: 2 failed.
  - `ALREADY_APPLIED` check removed: 2 failed.
  - S1 expected-revision check removed: 1 failed.
  - S1 expected-reserve check removed: 1 failed.
  - S1 opening its own transaction instead of using the caller's connection: 2 failed (rollback and artifact).
- **Full backend suite:** one run on `375c8cf9`.
  - Command: `pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder -q --durations=30`. Private base DB `assetops_s601a_test`, keep-awake running, 20-minute cap.
  - Result: **2207 passed, 1 failed, wall 648 s**. The summary line shows no skipped count.
  - The failure is `test_runs_api.py::TestTheShippedFuelLossEventAgainstAPropertylessFoundation::test_the_shipped_scenario_blocks_only_on_the_values_this_site_lacks`, with `FileNotFoundError ... AssetOpsV1-review2\var\sites\mg-001.yaml`. The gitignored `var/sites/*.yaml` files exist only in the main checkout; the phase-1 brief names this precondition.
  - Rerun of `test_runs_api.py` with those files copied in temporarily, then removed: 28 passed.
  - JUnit: the `--junitxml` path went through the Git Bash wrapper and no file was written. The zero-skip claim therefore rests on the pytest summary line, not on JUnit. For the JUnit form, rerun from PowerShell.
- **Walkthrough** (reproducible: `ASSETOPS_S6_WALKTHROUGH_OUT=<file.json> pytest backend/tests/test_s6_action_records_postgres.py` on a private `*_test` DB). Rows written:
  - 2 Actions, 25 basis assessments, 50 basis evidence rows, 1 change and 3 change-binding rows.
  - 8 events, in this order: ACCEPTED (F01), ACCEPTED (F02), OBSERVED (recorded 00:30, occurred 00:10), FAILED STALE, FAILED VALUE, FAILED EFFECTIVE_TIME, APPLIED 01:04, FAILED NO_CHANGE (F02).
  - Foundation: v9 PUBLISH superseded at 01:04; v10 SPLIT [10-03, 11-02); v11 PUBLISH from 11-02, reserve 15.
  - 3 binding set revisions, as the artifact names them.
- **Layout evidence:** not applicable (non-UI).

## Known deviations and interpretations

1. **Money consequence.** The recommendation carries a labelled link to the exact FindingRevision's stored S4 consequence, with no amount and with the statement that the trial predicts no saving. It does not embed the S4 money read.
2. **Lowest usable SOC (review L2).** Per segment the rule selects the lowest usable reading. This is deliberately stricter than the ruling, which only requires some reading strictly above r+10.
3. **`application_basis` is the covering Foundation at read time.** An apply whose effective time falls in an already-recorded future period must name that period's revision; the expectation is checked against the revision covering `effective_from`. The fixture's no-change case shows this. Fix round (review L2): the label now says so, `covers_instant` is exposed, and the contract fixture carries an `application_basis` note for S6-01b.
4. **Reserve no longer matching the accepted basis.** The S1 seam is checked in this order: expected revision (409 stale), no-change (422), then expected reserve (409 stale, `foundation_code: FOUNDATION_EXPECTED_VALUE_STALE`).
5. **Refusal order changed for commands.** An unknown Finding or Action now returns 404 before the capability's 403, because the capability now depends on the target record. Phase 1 had capability before 404.
6. **Non-domain exceptions.** An internal error inside apply (not `ApplyFailed`) rolls back and writes no FAILED.
7. **Accepted Low L3.** The persisted ineligible record is SOC-at-headroom (`SOC_NOT_ABOVE_HEADROOM`); missing/conflicting SOC is covered at rule level only. Add a persisted record if S6-01b needs that copy.
8. **Accepted Low L4.** Unmapped S1 refusals are forced to 409 (`FAILURE_STATUS`), and non-`FoundationRefused` S1 errors roll back as 500 with no FAILED. Safe but untyped.
9. **Fix round L1.** `FOUNDATION_CLOCK_BEHIND` maps to 409 `ACTION_FOUNDATION_STALE` (`foundation_code` keeps the S1 code), so a publish committed after the apply's server time is stale + FAILED and never an earlier-recorded APPLIED.
10. **Phase-1 interpretations stand.** See `.agent/S6-01a-phase-1-handoff.md` "Choices to review" 1-7.

## Residual risk

- **Migration re-chain.** LR-01's `0014`/`0015` may reach main first. If so, re-chain `0014_action_store` onto main's head, and update the head pins at:
  - `backend/tests/test_s1_bindings_postgres.py:118`
  - `backend/tests/test_s2_evidence_ledger_postgres.py:445`
  - `backend/tests/test_s4_evidence_consequence_work_postgres.py:516,539`

  Then rerun the slice review and the full suite on the re-chained revision. This was not done here, per the brief.
- **The grants file is the only gate.** Under the development access check, the grants file is the only gate for SYSTEM demonstration commands. No runtime grants file is generated for a served demo: `fixture_grants` builds one per run and per DB.
- **Accept is two transactions.** Rule evaluation and the insert run in separate transactions, so a just-stale basis is caught only by apply's expected checks under the Site lock (tested: 409 plus FAILED).
- **Contract fixture size.** It is 350 KB. The comparison normalises UUIDs, digests and codes, so referential consistency is asserted separately in the test.

## Reopen round - `D-2026-10-15-s601-reopen` (code `586d5fe1`)

Ruling `AssetOpsV1-gap-planning/.agent/architect-S6-01-reopen-answers.md`, option (c). Files: `actions/service.py` (`prior_action`, `prior_action_refusal`, `is_unresolved`, `_prior_guard`, `recommendation`, `accept`), `actions/adapters/postgres_action_store.py` (`_finding_actions`, `actions_for_finding`, `accept(..., guard=)` with the per-trial advisory lock), `actions/ports.py`, `actions/reserve_trial.py` (`LIVE_RECOMPUTATION_FAILED`), tests and the regenerated fixture.

| Ruling item | Status | Evidence |
| --- | --- | --- |
| Read returns prior Actions of the canonical Finding: origin revision (ID, number, `is_selected_revision`), application and outcome state, exact link; not hidden by stale basis, later revision or failed recomputation | Met | `prior_actions.items` is read before the live rule; store test (newer revision, live `FOUNDATION_BASIS_STALE` and `FINDING_NOT_CURRENT`), F04 test (live AVAILABLE), contract cases on both clocks |
| Selected revision and accepted snapshot labelled separately | Met | `revision_id` vs `prior_actions.items[].origin`; ACCEPTED body unchanged; `is_selected_revision` true only on the origin revision |
| New acceptance held by an unresolved earlier Action: typed 409 `PRIOR_ACTION_UNRESOLVED` with `blocking_action_id`, `origin_finding_revision_id`, `links`; live reason separate (`live_status`) | Met | store test (stale live), F04 test (AVAILABLE live), contract `accept_newer_revision_prior_action_unresolved`; counts unchanged |
| No Accept capability for the new key | Met | `system_demo_capability.allowed=false`, reason `PRIOR_ACTION_UNRESOLVED: ...`; read `state=PRIOR_ACTION_UNRESOLVED`, `proposal=null` |
| Identical retry of the accepted key returns its Action | Met | F04 test `again` (200, same action ID); records `accept_replayed` |
| Atomic recheck: simultaneous accepts on two revisions make one unresolved trial (Postgres) | Met | `TestPriorActionAtomicRecheck` (one created, one `PRIOR_ACTION_UNRESOLVED`, 1 Action row) |
| Contract fixture: recorded-clock AVAILABLE and served-clock stale cases; NOTES for S6-01b | Met | `recommendation:1#a.latest_revision_after_apply` (live AVAILABLE), `..._served_clock_stale` (clock 2026-10-15, live `FOUNDATION_BASIS_STALE`); `notes.prior_actions`, `notes.PRIOR_ACTION_UNRESOLVED` |

Checks (on `586d5fe1`, private DB `assetops_s601areopen_test`, dropped afterwards):
- Fixture regenerated with `ASSETOPS_WRITE_S6_CONTRACT=1`, then the 4 S6 files: **81 passed** (105 s), normalised equality held.
- `tools/check-architecture.ps1`: passed.
- Mutations, each reverted with `git checkout`, tree clean afterwards:
  - guard predicate releases every state (`UNRESOLVED_APPLICATION = ()`): 4 failed (3 store tests, records);
  - applied Actions treated as resolved (`(PENDING,)`): records test failed;
  - per-trial advisory lock removed: race test failed (both created);
  - store-side guard skipped (service pre-check only): race test failed (both created).
- Full backend suite: one run on `586d5fe1` from PowerShell, `pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder -q --durations=30 --junitxml=...` (var/sites copied in and removed; keep-awake on; 20-min cap): **2210 passed in 546 s**; JUnit cases=2210 skipped=0 failed=0.

Reopen deviations and interpretations:
- R1. **Every post-acceptance state blocks.** After acceptance an Action is PENDING (failed attempts keep it PENDING) or APPLIED, and the outcome is always PENDING here. The ruling also says a completed verification is not permission until S6-02 defines resolved/closed, so no reduced state releases the guard (`UNRESOLVED_APPLICATION`). S6-02 must add the release.
- R2. **Scope of the block.** Same Finding, `reserve-trial-1`, field `battery_reserve`, and the live proposal's asset when one is offered (any asset when the live rule offers none). A selected revision with its own Action and no new key on offer shows its ACCEPTED snapshot and no block.
- R3. **Race proof is store-level.** Once revision 2 exists the service refuses revision 1 (`FINDING_REVISION_NOT_LATEST`), so the test drives `store.accept` with the two real server proposals and the service's own guard, holding each transaction 1 s after its check.
- R4. **Served clock.** The served-clock case reads at 2026-10-15T12:00Z, the date of the S6-01b served walkthrough.
- R5. **`LIVE_RECOMPUTATION_FAILED`.** If the revision's rule inputs cannot be read after currentness succeeded, the read still returns prior Actions with this live reason, instead of 404.

## User-review focus

None required (non-UI). S6-01b carries the owner checkpoint and consumes `backend/tests/fixtures/s6_action_api_contract.json`.
