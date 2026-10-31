# FIX-S4-DOMAIN review packet

Task: `tasks/FIX-S4-domain-filter.md`. Ruling: Addendum 3, ruling 1 of
`AssetOpsV1-plan2/.agent/build-sheet-DEMO-SPARSE.md`. Branch `task/FIX-S4-domain-filter`, from main `ee678cbe5`.

## Outcome delivered

`PostgresFindingStore.episodes` now returns only one domain's and one analytic's Findings. The defaults are
`mini_grid` (`finding_episode.DOMAIN`) and `dispatch` (`dispatch.ANALYTIC_ID`). An open cold Finding on the same Site
no longer reaches the mini dispatch matcher, so `plan_pass` no longer crashes and the Site's later tick stages run.

## Files materially changed

- `backend/assetops_backend/analytics/adapters/postgres_finding_store.py`: imports `ANALYTIC_ID as DISPATCH_ANALYTIC_ID`.
  `episodes(tenant_id, site_id, domain=DOMAIN, analytic_id=DISPATCH_ANALYTIC_ID)`. The WHERE gains
  `AND f.domain = :d AND f.analytic_id = :a`, the same predicate `_index_snapshot` uses.
- `backend/tests/test_s4_finding_domain_filter.py` (new, pure): a recording connection checks the default parameters,
  the explicit parameters and the predicate text.
- `backend/tests/test_s4_finding_domain_filter_postgres.py` (new, Postgres): the F01 mini window is delivered and
  assessed, and an open cold excursion Finding (`episode_end` NULL) is inserted. The test asserts the following:
  - The cold Finding reads under its own domain and analytic.
  - The default read is empty.
  - The matcher pass plans exactly one write, a mini OPENED anchored at 2026-10-06 08:00Z.
  - The cold Finding still has one open revision.
  - A replay plans nothing.
- Closeout records: `tasks/FIX-S4-domain-filter.md`, `.ai/ACTIVE_CONTEXT.md` and `.ai/CODE_STATE.md` "FIX-S4-DOMAIN".

The callers of `episodes` are `FindingMatcher.match` (`finding_service.py:67`) and `stale_plan` in
`test_s4_finding_store_postgres.py:171`. Both use the defaults. `git grep "def episodes"` finds no fake or protocol
implementing `episodes`, so no fake needed an update.

## Acceptance (ruling 1)

| Criterion | Status |
|---|---|
| `episodes` signature with domain/analytic defaults | Met, using the existing constants. |
| WHERE has `f.domain = :d AND f.analytic_id = :a` | Met. |
| Every fake implementing `episodes` updated | Met. None exists. |
| No special case for a NULL `episode_end` in the matcher | Met. `finding_episode.py` is untouched. |
| Postgres test: open cold Finding plus a mini Finding on one Site; the pass completes and plans only the mini episode | Met. |
| Unit test that `episodes` passes the domain and analytic | Met. |

## Non-vacuous proof

The fix was committed first. The old store was then restored with `git checkout HEAD~1 -- <store>`.

- **Unchanged tests on the old store.** All 3 new tests failed. The pure tests failed on the missing predicate and a
  TypeError on the arity. The Postgres test failed on the arity.
- **Postgres test with the explicit-argument assertions removed.** The matcher pass itself failed:
  `finding_episode.py:287 TypeError: '<' not supported between instances of 'NoneType' and 'datetime.datetime'`,
  raised from `plan_pass`, then `_unsupported_write`.

The store and the test were then restored with `git checkout HEAD -- ...`, and `git status` was clean. The observed
crash line is 287, a None/datetime comparison in the same NULL-end family. The ruling cites 296-299, `None + timedelta`.

## Checks run

- **New tests, host venv against `assetops_test`.** Result: 3 passed.
- **Scoped container run.** Command: `tools/run-backend-suite-in-container.ps1 -Tier fast -Targets <58 files>`. Run
  `20261031-132002-84e54d`, 4 workers. Result: **653 passed** in 1037s, exit 0.
  - The 58 files are every `test_s4_*`, `test_idx_gaps_*`, `test_w20x*cold*`, `test_fix01_cold*`, `test_w301_cold*`,
    `test_w402_cold*` and `test_w501_cold*` file.
  - `tools/select-tests.py --base ee678cbe5` selected 180 files. The coordinator brief scoped the run to the s4,
    finding-index and cold sets, so the other selected files were not run.
- **First run of `tools\check-all.ps1 -Python <plan2 venv>`.** 9 of 11 guards passed. The missing-claim scan and its
  fixtures failed with `MODULE_NOT_FOUND typescript`, because the worktree had no `frontend/node_modules`. This was an
  environment precondition, not a code failure. I added a junction to plan2's `frontend/node_modules`, which git
  ignores, and reran check-all. The rerun result is under Closeout checks.
- **`-Tier all`** has not been run. It waits for the coordinator's go, as the brief requires.

## Known deviations

- Test fixture: the cold Finding is inserted directly with SQL, not through `cold_apply`. Its revision fires the
  `cold_consequence_dirty_on_finding_revision` trigger, which needs a COLD_ROOM in the assessment's Foundation basis,
  and the mini Site has none. The test disables that one trigger inside its own insert transaction and re-enables it
  before commit. DDL is transactional, so nothing leaks to other tests. The matcher read does not depend on the
  trigger.

## Residual risk

- `_fence` still counts `finding_revision` rows across every domain on the Site. A cold revision written between the
  mini read and the mini apply therefore moves the mini fence. The result is a re-plan, not wrong data, and this fix
  does not change it.

## User-review focus

USER_REVIEW_REQUIRED: false. A fresh independent review gates the merge. After the merge, DEMO-A merges main and is
rebuilt once.

## Closeout checks

I reran `tools\check-all.ps1 -Python <plan2 venv>` on `5fd7a0fdb`, after adding the `frontend/node_modules`
junction. Result: **all 11 guards passed**, exit 0. The estate guard self-tests passed 7 of 7, and the missing-claim
scan reported 43 tagged uses and 10 baselined occurrences.
