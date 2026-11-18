# Review packet: FIX-MAIN-1 (latent full-suite failures on main, plus M4)

Branch `task/FIX-MAIN-1` from main `c036f8a49`. Commits: cf27a0423 (goldens, runs_api), e10f215cc (M4 and the runner
`ensure` step), 58a50096e (CO-1/CO-1b per Architect ruling R1). This packet commit follows. Not merged. Brief: plan row
CH5a1-R3 / FIX-MAIN-1, build sheet CH-5a §A14. No product code changed: `git diff c036f8a49 -- backend/assetops_backend host`
is empty.

## Failures: cause and fix

| failure (CH-5a1 run 20261104-163109-be9c25) | cause | fix |
|---|---|---|
| `test_demo_combined_postgres` x25 (module set-up `SELF-CHECK FAILED`; 24 follow-on errors) | Reproduced with a host prepare on c036f8a49 (`assetops_demo3_fixmainone_test`, `var/demo3_fixmain1`): 22 pass, 1 fail, **CO-1** `{'MG-2': ('NEEDS_ATTENTION','PRIMARY_FINDING_OPEN')}`. Since CH-3 (c9150f459) the board takes "applied" from the thread state on the board day (`site_outcomes/board.py:600-608`). CHANGE_APPLIED is dated by the APPLIED event's `effective_from` (`chain/lifecycle_run.py:41`). The Kobo thread reads ACTION_IN_HAND on S (2 Nov), then CHANGE_APPLIED and RESOLVED_MONITORING from 3 Nov. CO-1 still expected the pre-CH-3 exact-revision branch. No bisect was needed. | Reported and stopped. **Architect R1, option (a)**: the expectation is stale, the CH-3 semantics are correct, and the expectation owner is CH-3. `tools/demo_combined_finish.py`: CO-1 keeps the link, safeguard and no-outside assertions. It now asserts that the change day (Site-local `story.kobo.action.effective_from`) is after S, that MG-2 is `('NEEDS_ATTENTION','PRIMARY_FINDING_OPEN')` with the cost row at NEEDS_ATTENTION, and that the subline holds `THREAD_BEFORE` followed by `THREAD_AFTER_[NOT_]JUDGED` (both imported from board.py). It records which one appeared: `THREAD_AFTER_NOT_JUDGED`. New **CO-1b** (S+1): no OPTIMIZE_COST outcome is PRIMARY_FINDING_OPEN, and the board carries `Fix verified, monitoring (ACT-001)`. |
| `test_w301_estate_golden_postgres` x6 (`$.opportunities` absent) | CH-4 (fbb6d29a6) added the opportunity block at `estate/index.py:345-349`, and the goldens predate it | Regenerated with `ASSETOPS_WRITE_W301_GOLDEN=1`. The diff is 46 added lines and nothing removed: 23 `"opportunities": []` and 23 `"summary.opportunity_count": 0`. Both keys come from that one CH-4 block (line 345 sets the count, 346-349 set the array). The count key is the only addition beyond the `opportunities` key the brief named. |
| `test_runs_api::...blocks_only_on_the_values_this_site_lacks` | The test read the gitignored `var/sites/mg-001.yaml`, which only a developer checkout has | Committed a copy as `backend/tests/fixtures/sites/mg-001.yaml` (from plan2 `var/sites`, 285 lines) and pointed the test at it |
| MD-0 L2m `TEMPLATE_MISSING` in the container | `postgres-test` never had the template; nothing built it | `tools/run-backend-suite-in-container.sh`: when any target holds a `test_*.py` that calls `clone_template(`, it runs `tools/mechanism_dataset.py ensure` (reuse, else one unbudgeted build) before pytest, logging to `<run>/mechanism-template.log`. Non-zero means `REFUSED` and exit 2, before pytest. The tool reaches the container server through `ASSETOPS_MECHANISM_SERVER_URL`. |

## M4: per-fingerprint templates
- `backend/tests/mechanism_dataset.py`: `template_name(fp)` gives `assetops_mechanism_tpl_<fp8>_test`. `templates()` lists them newest first by tag `built_at`. `find_template()` returns the one whose tag matches this checkout (its own traced module list re-hashed) and whose name carries that fingerprint, else `TEMPLATE_STALE` or `TEMPLATE_MISSING`. `publish_template()` tags the staging DB, ends any sessions on it, renames it, and then `prune_list` drops all but the two newest. `clone_template(admin, target)` uses `find_template` by default. `MECHANISM_DB_RE` adds `_tpl_<hex8>` and `_tplb_<hex8>`.
- `tools/mechanism_dataset.py`: `states` builds into the staging DB `assetops_mechanism_tplb_<hex8>_test`, whose name is kept in `seed-state.json` so `--resume` works. A fresh build drops an abandoned staging DB. Also new: `ensure`, a multi-template `status`, `drop --variant legacy`, and the `ASSETOPS_MECHANISM_SERVER_URL` override.
- **Migration:** the legacy `assetops_mechanism_tpl_test` (CH-5a1's branch) is outside `TEMPLATE_RE`, so it is never looked up, pruned or replaced. CH-5a1 keeps using it until it merges main. After that, `drop --variant legacy` removes it on request.

## Checks run (all on this branch, c036f8a49 base)
- Demo self-check with no new prepare: the edited finish ran against the existing evidence DB after one `demo_combined.py tick`. The first re-check without a tick failed CO-1, CO-2 and CO-5/SP-1 with `PRODUCER_NOT_SETTLED` / `HEARTBEAT_STALE 789 s`, because the scheduler had been idle for 13 min since the prepare. After the tick: **self-check 24 pass, 0 fail, 0 skipped**. The private tree's finish file was restored afterwards.
- `test_demo_combined_postgres`: **deferred to E2**. Its module fixture always runs its own full prepare (about 25 min), so it cannot reuse the evidence DB. Collection shows 26 tests, including `test_CO_1b`.
- Container, scoped (`-Workers 2`): run `20261104-183858-633bd2` on targets md0_mechanism_postgres, md0_fixture, runs_api and w301_estate_golden. `ensure` **built** `assetops_mechanism_tpl_85d439a2_test` in 683 s. pytest gave 84 passed, 2 xfailed, 0 failed, 0 errors, wall 454 s. JUnit: tests 86, failures 0, errors 0, skipped 2, where the 2 are the xfails (see below).
- Container, md0_mechanism_postgres alone: run `20261104-190012-830f03`. `ensure` **reused** the template in 1 s. 4 passed, 2 xfailed.
- Host: `test_w301_estate_golden_postgres` 6 passed (verify run after the rewrite). `test_runs_api -k Propertyless` 4 passed. `test_md0_fixture.py` 46 passed, including the new `template_name` and `prune_list` tests and the regex rows.
- `check-architecture.ps1` passed. `check-agent-workflow.ps1` passed, on the final code.
- **No full suite was run**: the coordinator's correction applied owner rule OD-P4 (scoped tests only until the end-game run).

## Known deviations and residual risk
- **xfail versus the zero-skip check:** now that the template exists, `test_kobo_grades_threads_actions_and_story_time` and `test_late_fill_normal_fills_the_gap_and_changes_no_finding` run and xfail (MD-0-F1, owner CH-5a1 R5). JUnit counts these as `skipped`, so a JUnit zero-skip check reports skipped=2. In the earlier full run they errored at set-up instead. **Needs a coordinator or Architect call:** either count xfail separately in the zero-skip rule, or wait for CH-5a1 R5.
- **Golden diff:** it also carries `summary.opportunity_count` (same CH-4 block). Read the brief's "only difference" as that CH-4 block.
- **`ensure` failure proof is partial:** against an unreachable port, the tool did not fail fast. It hung in connect and was ended by `timeout` (exit 124). The runner's refusal branch was shown with a forced non-zero (exit 2). Inside the container, a hang is bounded by the runner's cap, not by `ensure` itself.
- **Concurrent builds:** a build that prunes while another run is cloning an older template could drop that template mid-clone. That needs three or more live fingerprints on one server.
- **CO-6 (Architect note):** at main `01133225a` (CH-5a1 `summary_day`), CO-6 may fail. That would be **waiting on owner Q7**, and it was not touched. This branch is on c036f8a49, where CO-6 passes.
- The evidence DB `assetops_demo3_fixmainone_test` (55432) and `var/demo3_fixmain1` are kept for the review. Drop them with `tools/demo_combined.py --db assetops_demo3_fixmainone_test --work var/demo3_fixmain1 drop`.

## Review focus
CO-1/CO-1b against ruling R1. `find_template`/`publish_template` naming and pruning. The runner's ensure gate (`clone_template(` grep).
USER_REVIEW: not flagged; the coordinator decides.
