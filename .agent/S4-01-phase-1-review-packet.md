# S4-01 phase 1 review packet - `I-finding-store` and `D-finding-revisions`

Task: `tasks/S4-01-finding-identity.md`, phase 1 row (Status stays `active`; phases 2-3 follow).
Branch `task/S4-01-finding-identity`; phase 1 = `bcbc3f4` (store, matcher, spec, tests, guard), `6b891ef` (producer,
CLI), closeout commit. Diff for review: `git diff 5f7cd4c..HEAD`. Authority: `D-2026-10-12-finding-episode-and-revisions`,
`.agent/architect-A-finding-episode-answers.md`. Questions: `.agent/S4-01-questions-1.md` (Q1-Q9, fail-closed defaults).
Handoffs: `.agent/S4-01-phase-1-handoff.md`.

## Outcome delivered

- Persisted Finding store (migration 0009): `finding` (immutable key `gen-support:<asset>:<anchor>:<uuid8>`, anchor,
  cohort, matcher version, immutable `recurs_after_finding_id` / `split_from_finding_id`), append-only
  `finding_revision`, `finding_revision_assessment` (every interval + window revision cited, with run),
  `finding_revision_evidence` (cited accepted evidence only), `finding_merge`. All tables under `ledger_append_only`.
- Pure matcher `analytics/finding_episode.py` (`finding-episode-1`): open / extend / split / merge / recurrence /
  UNCONFIRMED / NO_LONGER_SUPPORTED / MODEL_REEVALUATED from CURRENT selected `dispatch-3.1` windows only; idempotent on
  `(finding, basis_sha256, transition)`.
- `analytics/finding_service.FindingMatcher` reads through `DispatchReadService.window` under a fence (selection seq +
  job marker) and applies through `PostgresFindingStore` (fifth guarded writer, INSERT-only, advisory lock, re-check).
- Operator CLI: `assess_dispatch match-findings` and `finding-rows` (read-only), wired via
  `analytics/composition.build_finding_matcher` / `build_finding_store`.
- `s4-finding-cases-v1`: committed specification `backend/conversions/s4-finding-cases-v1.json`; producer
  `tools/s4_finding_cases.py run|verify` runs F01-F06 and F08 through Batch V2 over TLS, central acceptance, the S3
  worker and the matcher; per-run IDs only in the work-dir artifact.

## Files materially changed

`backend/migrations/versions/0009_finding_store.py`, `backend/assetops_backend/analytics/finding_episode.py`,
`.../analytics/finding_service.py`, `.../analytics/adapters/postgres_finding_store.py`, `.../analytics/composition.py`,
`.../analytics/assess_dispatch.py`, `backend/conversions/s4-finding-cases-v1.json`,
`backend/tests/test_s4_finding_store_postgres.py` (head asserts moved to 0009 in `test_s1_bindings_postgres.py`,
`test_s2_evidence_ledger_postgres.py`), `tools/checks/configuration-persistence.ps1`, `tools/s4_finding_cases.py`.

## Acceptance criteria (phase 1)

| Criterion | Status | Evidence |
| --- | --- | --- |
| Migration for Finding/revision + assessment/evidence/episode relations | Met | 0009; append-only proven by `test_finding_rows_are_append_only` (UPDATE/DELETE refused) |
| Immutable ID/key, anchor, cohort, matcher version | Met | `finding` columns; F04 late-earlier keeps anchor 08:30 and ID while revision 2 bounds move to 08:00 |
| F01 candidate/open with bounded duration, distinct Necessary, cited accepted IDs | Met | producer + test: episode 08:00-09:00, `necessary_minutes > 0`, SUPPORTED cites evidence |
| F02 same ID across overlap and <=20-min gap incl. UTC midnight; changed basis appends | Met | 2 interval citations across 10-08/10-09; revision 2 extends to 00:55 |
| F03 recurrence with `recurs_after_finding_id` | Met | 09:30 Finding links to 08:00 (observed OFF, Q3) |
| F04 late earlier acceptance | Met | revision 2 selects a new S3 revision, revision 1 unchanged and reloadable |
| F05 UNCONFIRMED then NO_LONGER_SUPPORTED, no new Finding | Met | runtime 120 backdated -> UNCONFIRMED r2; runtime 0 + reserve 45 -> NO_LONGER_SUPPORTED r3 |
| F06 split + linked part; bridge merge with canonical/supersession, both histories kept | Met | SPLIT r2 + split part `split_from`; MERGED / MERGED_INTO with one `finding_merge` row |
| F07 model upgrade | Test-scoped | no reviewed later `dispatch-3.x`; `test_f07_test_scoped_model_upgrade_appends_a_revision` uses labelled `dispatch-3.1-s4-test-upgrade`; no live upgraded claim |
| F08 retry and absent basis | Met | unassessed / ambiguous cohort -> no Finding; replay after F05 and `verify` replay plan 0 |
| Stale window neither creates nor closes | Met | `test_stale_window_neither_creates_nor_closes` |
| Moved fence writes nothing | Met | `test_a_moved_fence_writes_nothing` |
| Per-run IDs in environment-bound artifact, not committed | Met | `%LOCALAPPDATA%/AssetOps/s4-finding-cases/s4-finding-cases-run.json` |
| Postgres reload before proceeding | Met | test `check` reloads; producer `verify` in a fresh process |
| Never insert Finding rows directly as fixture truth | Met | rows only via `match-findings`; guard limits Finding writes to the store |

## Producer run (`.agent/S4-01-finding-cases-run.txt`)

`.venv/Scripts/python.exe tools/s4_finding_cases.py run` on `6b891ef`: DB `assetops_s4cases`, TLS port 8763, no
Lab/gateway process. Every match step checked OK, 0 check failures; produced in 161 s; fresh-process verify: evidence
digests for all 7 cases match (93/130/102/93/277/52/93 readings), 10 Findings / 25 revisions reloaded match, replay
`match-findings` planned 0 -> `VERIFY PASSED`, exit 0. Final counts: 10 findings, 25 revisions, 56 assessment
citations, 1680 cited evidence rows, 1 merge. The TLS server was stopped (no listener on 8763 afterwards).

## Checks run

- Backend with Postgres (isolated `assetops_s4p1b_test`, dropped afterwards): `1841 passed, 21 warnings in 612.32s` (no skips; includes the 5 S4 Postgres tests)
- Host: `667 passed, 3 warnings in 590.42s`. Gateway: `164 passed in 63.23s`. Simulator (from `simulator/`): `265 passed in 3.99s`.
- `tools/check-all.ps1 -ExecutionPolicy Bypass`: `All 6 guards passed.`
- Guard proof (non-vacuous): on `bcbc3f4`, an `UPDATE finding_revision` in the store and an `INSERT INTO finding` in
  `finding_service.py` each failed `check-architecture.ps1` (handoff). On `6b891ef`, an `INSERT INTO finding_revision`
  appended to `assess_dispatch.py` failed with "A second product database writer in ...assess_dispatch.py:77"; reverted
  with `git checkout --`, tree clean.
- No frontend change in phase 1; frontend suites not run. Layout evidence: not applicable (no UI).

## Known deviations

- Fixture provenance (Q6): F01-F08 are labelled authenticated Batch V2 fault fixtures, not gateway-sealed. Fix round 1
  adds `F01-gateway`, a baseline Candidate through the ordinary registered gateway path (see Fix round 1).
- Minimum-runtime control has no product route; the producer publishes it through `FoundationService` in the copied
  tree, labelled (Q8). Reserve goes through the product API.
- Spec `decided` instants are ordering labels over HTTP; the real server clock decides (Q9). The Postgres test applies
  them exactly.
- Revision uniqueness differs from the technical design's `UNIQUE(finding_id, assessment_revision_id)` (Q1).
- F07 test-scoped (task allows; owner must be told).

## Residual risk

- Recurrence links chain across case days in the one fixture Site (each case is bounded by observed OFF), e.g. the
  10-08 Finding `recurs_after` the 10-06 one; the spec asserts links only for F03/F06. Correct under Q3, but visible
  in phase 2 reads.
- Backdated controls append collateral revisions to Findings on earlier days (10-06..10-19 after the 10-21 control; F05: 8 collateral + 1 named). Fix round 1 labels them BASIS_REFRESHED (Q5/C1).
- Matcher reads every assessed day per pass (linear); 3+-way merges and mixed split+merge are implemented but only
  two-way cases are fixture-tested. No pure unit tests for `finding_episode.plan` (handoff optional item 2 not done).
- Producer DB `assetops_s4cases` was dropped after the run; rerun `run` (about 3 minutes) to re-create and verify.

## User-review focus

USER_REVIEW_REQUIRED: true for S4-01 at the owner checkpoint after phase 3; phase 1 needs an independent Claude review
(store/matcher/fixture), not an owner check. Reviewer: F01, F04, F05, F06 and F07 after reload; Q1-Q9 defaults; the
collateral-revision behaviour; the guard; rerun `tools/s4_finding_cases.py run` and the S4 Postgres tests.

## Fix round 1 (review `.agent/S4-01-phase-1-review.md`; rulings `D-2026-10-12-s4-finding-phase-1-clarifications`)

Commits `7781821`, `6bfd145`, `43d3268`, `db28578`, `71dd0b6`. Migration 0009 edited in place (unmerged).

| Finding | Change | Anchor |
|---|---|---|
| B1 split ownership | Each episode is reserved for the cluster containing its anchor; each cluster then takes its earliest-anchor eligible episode; absorbed episodes merge into their home owner | `analytics/finding_episode.py` |
| B2 interleaved passes | `Fence.finding_revisions` = count of the Site's `finding_revision` rows (append-only), so a pass planned before another pass committed refuses with `FindingFenceMoved` | `adapters/postgres_finding_store.py` |
| B3 / Q3 recurrence | Link only when `site.covered(prior.end, new.start)`, prior OFF-after observed and new OFF-before observed; else unlinked | `_recurrence` |
| B4 / Q2 bridges | A bridge also needs every gap instant in an observed segment or an observed stop (`_fully_covered`, `_stops`; `IntervalBasis.last_on`) | `_bridges` |
| Q4 basis | basis = support digest + interval + selected window revision IDs + window input digests + cited | `window_basis` |
| Q5 / C1 | `support_sha256` column; provenance-only change -> `BASIS_REFRESHED` (owner and unsupported paths) | 0009, matcher |
| C3 reopen | Candidate over a NO_LONGER_SUPPORTED episode -> `REOPENED` | 0009 CHECK, matcher |
| C7 moved fence | Postgres test applies a real planned OPENED write after the fence moves | `tests/test_s4_finding_store_postgres.py` |
| Q6 gateway | `F01-gateway`: `kobo-mini-grid-prolonged` v2 Lab run, 2026-10-02 03:00-11:00Z, roles-2, sealed by the durable registered gateway (epoch `s4-gateway-epoch-1`), direct TLS, `process-jobs`, `match-findings` | `tools/s4_finding_cases.py gateway_case` |

Tests that failed before the fix: new pure `tests/test_s4_finding_episode.py` (16). Against the pre-fix matcher
(signature shim) 8 fail - B1 split, B3 unassessed-day and no-OFF recurrence, mixed split+merge, reopen,
BASIS_REFRESHED, out-of-order OFF, empty span in gap - and 8 pass (regression coverage). New Postgres
`test_a_pass_planned_before_another_pass_committed_opens_no_duplicate` (B2).

Mutation proofs (committed first, reverted with `git checkout --`): fence without `finding_revisions` -> interleaving
test "DID NOT RAISE FindingFenceMoved"; fence check disabled -> moved-fence test "DID NOT RAISE".

Q6 note: the first attempt on 2026-10-04 was refused by the Lab: `LIFECYCLE_TIMING_NOT_ALIGNED`
("generator-minimum-runtime@generator is 0 min ... must be a whole, positive multiple of the step"). The 10-03 setup
control sets 0 minutes, so the gateway case runs on 10-02 (roles-2, template minimum runtime, before the setup
controls) and runs after every fixture case, so no fixture expectation sees it. Architect may prefer a positive
runtime setup control so the gateway day shares the fixture controls (question for the next batch).

Producer (`.agent/S4-01-finding-cases-run.txt`, commit `71dd0b6`): every match step OK, 0 check failures, 195 s;
F01-gateway 198 sealed batches, 329 accepted readings all under `s4-gateway-epoch-1` and the registered gateway ID,
1 Finding OPENED SUPPORTED at 05:15Z. Verify: 8 case evidence digests match, 11 Findings / 30 revisions reloaded
match, replay planned 0 -> `VERIFY PASSED`. Counts 11 / 30 / 66 citations / 1920 cited evidence / 1 merge
(was 10 / 25 / 56 / 1680 / 1); BASIS_REFRESHED 12, SUPPORT_CHANGED 2. Recurrence links only same-day (F03, F06);
the phase-1 cross-day chain is gone (B3). DB dropped; no listener on 8730/8763, no gateway pipe left.

Checks (after `71dd0b6`): backend with Postgres (isolated `assetops_s4fix2_test`, dropped) `1858 passed, 19 warnings
in 553.71s`; host `667 passed, 3 warnings in 579.55s`; gateway `164 passed in 52.71s`; simulator `265 passed in
3.24s`; `check-all.ps1` `All 6 guards passed.`; `check-agent-workflow.ps1` `Agent workflow check passed.`
(backend and host ran on `db28578`; `71dd0b6` changes only the producer's gateway day).

New questions with fail-closed defaults: `.agent/S4-01-questions-2.md` (Q10-Q15; Q14 = BASIS_REFRESHED volume for
phase 2/3 History grouping, Q15 = gateway case day).
