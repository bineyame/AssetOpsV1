# S3-02a review packet - selected-assessment capability and claim-limit read

Task `tasks/S3-02a-capability-read.md` (status `in_review`). Branch `task/S3-02a-capability-read` from main `71009bf6`. USER_REVIEW_REQUIRED: false (non-UI; mergeable after a fresh independent review). Review diff: `git diff 71009bf6..HEAD -- ':!.agent'`.

## Outcome

One versioned read (`s3-claim-limit-1`, schema `assetops.s3-claim-limit-read` v1) for one Site, UTC day and exact S3 `assessment_revision_id`: per-role capability spans (COVERED / MISSING / POOR_QUALITY / CONFLICTED / NOT_EVALUATED, minutes, pinned accepted Evidence IDs) and a claim ceiling (Candidate / Necessary / Indeterminate) that is current only for the window's CURRENT selection; otherwise PENDING / FAILED / STALE_PROJECTION / HISTORICAL with `historical_ceiling` only. Behind the Finding access seam and the Performance cutover gate. Callable public-ingestion fixture builder for S3-02b.

## Files

- `backend/assetops_backend/analytics/claim_limit_read.py` (new): `ClaimLimitReadService`, rule mapping, coverage spans, refusals.
- `backend/assetops_backend/claim_limit_api.py` (new): route and check order.
- `backend/assetops_backend/analytics/adapters/postgres_assessment_store.py`: `claim_limit_snapshot` (window snapshot + revision detail in one REPEATABLE READ); `_window` / `_revision_detail` extracted from the existing methods (same SQL, reads only).
- `backend/assetops_backend/analytics/composition.py`, `main.py`: wiring with `performance_gate`.
- `backend/tests/s3_claim_limit_records.py` (new): `build(runner, url)` fixture builder and manifest.
- `backend/tests/test_s3_capability_read_postgres.py`, `backend/tests/test_s3_claim_limit_postgres.py` (new); `backend/tests/fixtures/s3_claim_limit_api_samples.json` (normalised responses); `backend/TESTING.md` slice list.
- Closeout: task status, `.ai/CODE_STATE.md` "S3-02a", `.ai/ACTIVE_CONTEXT.md`, `.agent/S3-02a-handoff.md`.

## Acceptance criteria

| Criterion | Status | Evidence |
| --- | --- | --- |
| Versioned CapabilityReadiness/ceiling for one Site, half-open UTC day, exact revision; that assessment's accepted basis only; no later readings or other revision | Met | Coverage derives from the revision's stored segments and `revision_detail` evidence only (`claim_limit_read.py` `segment_roles`/`role_coverage`); window/revision read in one snapshot (`claim_limit_snapshot`). |
| Performance cutover gate: closed = 409 `PERFORMANCE_CUTOVER_CLOSED`, never UNASSESSED/empty | Met | `test_closed_cutover_gate_is_409_never_unassessed` (with and without revision); mutation M1 below. |
| Request identity seam 401/403/404 | Met | `finding_api.Access`/`development_access`; `test_identity_boundary`. |
| Echo tenant/Site, day/window, revision, run/model/cohort, cutoff, Foundation/binding IDs, accepted evidence IDs, source/analytic watermarks, built_at, read_at | Met | `test_full_candidate_is_a_current_complete_candidate_ceiling_with_echoed_lineage`, `test_reload_returns_the_same_capability_and_lineage`. |
| Per-role duration/quality, missing/conflicted spans, selection/rule basis, limitations; exact spans not aggregated away (Architect answer 4) | Met | `test_missing_pv_is_a_missing_span_not_zero_capability`, `test_poor_quality_and_conflict_keep_their_exact_subspans` (PCS POOR_QUALITY 08:05-08:20 kept between COVERED spans; PV CONFLICTED 08:20-08:30). |
| Candidate/Necessary/Indeterminate bounds; no physical capacity from configured capability | Met | Candidate COMPLETE 30 min, Candidate LIMITED, Indeterminate from missing PV (ingested); Necessary by snapshot mutation; `not_inferred` statement. |
| Positive ceiling needs current exact selection, complete rule assessment, accepted role evidence; LIMITED/UNKNOWN portions named | Met | `test_fail_closed_rules_withhold_a_positive_ceiling` (cohort, role problem inside a claim-carrying segment), `test_open_bound_and_configuration_are_named_reasons`; mutation M2. |
| No assessment = UNASSESSED; pending/failed/stale = no current positive claim; prior revision historical only | Met | `test_unassessed_and_no_revision_selected`, `test_pending_day_has_no_revision_and_no_claim`, `test_failed_recompute_keeps_the_prior_selection_as_non_current`, `test_stale_selection_makes_no_current_positive_claim`, `test_late_revision_withdraws_the_first_revision_to_history`; mutation M3. |
| Reject foreign Site/revision, revision outside window, unsupported rule, absent accepted lineage | Met | `test_wrong_site_window_revision_and_rule`, `test_unsupported_model_and_absent_lineage`. |
| Callable `s3_claim_limit_records.py::build` with manifest for S3-02b; check `I-sim-dispatch-cases` IDs against the rule | Met, with deviation D1 | Builder + manifest; `test_fixture_cases_select_the_expected_classifications`; samples file; handoff lists IDs and responses. |
| No private simulator truth | Met | Fixture is Batch V2 through the S2 ingestion service + S3 worker; no simulator import. |
| Audit new SQL writers (rule 8); writer probes | Met | No new writer SQL (only SELECTs moved); probes below. |
| No migration | Met | None added; S6-02a `0019` unaffected. |

## Checks run (revision `edd86e0d` unless stated; `37343acc` changed only test pool disposal)

- Focused: `pytest backend/tests/test_s3_capability_read_postgres.py backend/tests/test_s3_claim_limit_postgres.py` -> 24 passed (28.9 s).
- Adjacent (after the store refactor, at `3f7c1fbf`): `test_s3_dispatch_read_postgres.py test_s3_performance_cutover.py test_s4_finding_index_postgres.py` -> 46 passed (140.7 s).
- Mutations (at `3f7c1fbf`, each reverted with `git checkout --`): M1 gate check disabled -> `test_closed_cutover_gate...` fails; M2 withheld ignored in `interval_ceiling` -> both fail-closed cases fail; M3 `current = True` -> late-revision, stale and failed tests fail.
- `python tools/writer_guard_probes.py` (default runner, ~100 min): completed, last lines `ALLOWED controls provenance insert and arbiter` / `tree restored`; exit status was not captured (piped). Re-run `--seam`: exit 0, 68 CAUGHT, 4 ALLOWED, tree restored.
- `tools/check-all.ps1`: All 9 guards passed (architecture, navigation, agent workflow, registry, delivery/mock-gap fixtures, missing-claim scan, screen ledger).
- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: Registry valid: 234 nodes, 11 linked pilot panels.
- Full backend suite at `37343acc` (final code revision; later commits are `.agent` only): `pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder -q -p no:cacheprovider --junitxml=<abs>` from PowerShell, private base DB `assetops_s302a_test`, keep-awake running, cap 25 min -> 2412 passed, wall 17:30; JUnit tests=2412 failures=0 errors=0 skipped=0. Two earlier runs are superseded: at `edd86e0d` 6 failed with Postgres `too many clients already` while another agent's Postgres work ran (this branch's tests then also held one undisposed store pool per request; `37343acc` disposes them); at `37343acc` 1 failed on missing `var/sites/mg-001.yaml` (worktree had no `var/sites`; copied from the main checkout for the run per the brief and removed afterwards).

## Known deviations

- D1: The fixture does not reuse the `tools/s3_dispatch_cases.py` producer DB (registered gateway over TLS); it uses the reviewed S4 `CaseRunner` path (sealed Batch V2 through the S2 ingestion service under the registered gateway principal, then the S3 worker), so the builder is callable in-process like `s6_action_records.build`. The producer's cases were checked against the rule only by reading their definitions (Candidate, missing PCS + UNAVAILABLE, contradiction fault fixture, late central acceptance); their IDs are per-run and not reused.
- D2: Necessary, open bound, cohort, configuration and absent lineage are proven by mutating a real snapshot (`Mutating` store in tests), not by ingested cases.
- D3: Unknown rule text in a segment's `missing` is mapped to MISSING (fail closed) by text matching on `dispatch-3.2` problem strings; another model version is refused (`SUPPORTED_MODELS`).
- Registry nodes `I-capability-read`, `I-claim-limit-read`, `I-S3-02a` left `open` pending review.

## Residual risk

- The rule parses stored segment text; a future model changing `_PROBLEM_TEXT` must bump `SUPPORTED_MODELS`/`RULE_ID`.
- Generator-state evidence is attached to segments by placed time (it is interval-level in the stored result).
- `supported_minutes` is the stored string (e.g. "30"); minutes in spans are floats.

## Review focus

Fail-closed paths in `interval_ceiling` and currentness (`in_selection` + `derive_status`), the single-snapshot store method, and whether span derivation from stored segments meets "exact role-coverage spans" (Architect answer 4).
