# DD-1b2b handoff (partial: steps 1-2 done; resume at step 3)

Card: `build-sheet-DD-1.md` **"DD1b2-R6"** (owed list O1-O20, steps 0-9) **as amended by "DD1b2-R7"** (end of the file; R7 rewrites O2, O8(2), O17, §7, step 6 and the §3 outcome table). Pre-flight: `.agent/DD-1b2b-preflight.md` (`5c05dd0a3`). Worktree `AssetOpsV1-dd1b2`, branch `task/DD-1b2-finish-rehearsal`. The handover is early, after step 2 rather than at step 5, because the first builder's context was heavy.

## Done

| Step | Result | Evidence |
|---|---|---|
| 1 | Dropped `assetops_demo3_dd1b2{p,q,r}_test` (`m`, `n` never existed). Deleted `var/demo3_dd1b2{m,n,p,q,r}`. Ran `npm ci` in `frontend` (179 packages, exit 0) | MEASURED: afterwards `pg_database LIKE 'assetops_demo3_dd1b2%'` = `[]`; `var/demo3_*` is absent |
| 2 | O1 committed as `44919e51f`. `chain/refs.py`: kind `DOMAIN_VERDICT` in `KINDS`, `domain_verdict_ref`, `href_for` → `/sites/{s}/domain-actions/{id}/verification`. `chain/site_chain.py`: `action_wire_ref(site, a)` used in `actions_of`. Frontend: `chainRef.ts` union, a `routeFor` case → `siteMillVerificationHref`, a `route-refs.json` row, `routeRefs.test.ts:15` | MEASURED: `test_dd1b2b_action_ref.py` + `test_ch5a2_refs.py` 70 passed; vitest `routeRefs.test.ts` 60 passed. Non-vacuous: with the branch in `action_wire_ref` disabled, `test_domain_intent_from_an_opportunity_is_the_verdict_page` FAILED; restored by `git checkout` |

`tsc --noEmit` has not been run yet; it belongs to step 5.

## Anchors for step 3 onward (READ)

- `tools/demo_combined.py`:
  - `prepare` `:360`: the cap is computed at `:366-368`; there is no `--cap-seconds` yet. The CLI is `main` `:736`; `add-day` and `--assess-now` are at `:757-761`.
  - `finish_build` `:454`, `after_children` `:467` (backfill-bcd at `:491`, where R8 drain 1 goes after it), `finish` `:496` (the `tick(times=2)` is at `:513`, and R8 drain 2 goes after it, before the self-check at `:514`).
  - `drain_mini` `:522`, `tick` `:539` (runs performance + prebuild on every call; R7 Q3: each drain iteration uses the raw `TICK --no-prebuild`, then performance once and prebuild once). `TICK` `:67`, `EXPECTED_SECONDS` `:63`, `PG_ADMIN` `:52`, `DB_RE` `:53`, ports `:57`.
- Counts for the done condition (O2 + R7 Q1):
  - dirty: `snapshot_dirty` per Site (`PostgresEventStore.queued`, `chain/adapters/postgres_event_store.py:146`).
  - pending: `PostgresEventStore.pending(consumer, t, s, types)` `:103`, for consumer `snapshots` and consumer `threads`, with types from `load_event_register().consumes(<consumer>)`, partitioned at `@` as in `scheduling/stages.py` `chain_snapshots`.
  - Kobo mini deferred: `live_mini_jobs`, PENDING or LEASED (`stages.py:151-156`).
  - Live opportunity jobs: the `live_opportunity_jobs` of the assessment store (`scheduling/tick.py:224`).
  - N = max over Sites of ceil((dirty + snapshots pending)/200) + 2, where 200 = `chain_snapshot_items` (`tick.py:75`).
- `tools/checks/perf_budget.py` CLI `:178-185` has no `--story` flag; build one (DD1b2-R Q9). `chain_perf_probe.py:35-42` has hardcoded dates.
- The O7 line is `docs/demo-sprint/client-demo-plan.html:588`. Keep the cell up to "(WN-6/7)." and replace the rest (R7 Q12).
- Whole list (MEASURED offline): 54 runs; Kobo 48 (47 delivering), Cold 3, EV 3. S-3 is kind `late` (`received_at` S-1 12:30, `assess: build`).
- Free RAM at 09:41Z was 3.3 GB (coordinator). R7 Q7's start condition is ≥ 2.5 GB for 2 min with nothing heavy running. Stop only below 1 GB on two consecutive samples, or after 15 min with no output.
- Step 6 start: by 17:30Z, otherwise the next morning at or after 05:00Z (R7 Q8).
- L2 base `assetops_dd1b2b_test` through `tools\run-host-tests.ps1`, dropped after (R7 Q9).

## Next

Step 3 (O2, O3, `tick --until-drained`, L0 + L2), then step 4, step 5, and the one rehearsal (step 6), as R6 §6 and R7 order them. The rehearsal is the one run: if it stops, keep the DB and go back to the coordinator.

## Open risks

- The whole-list time is unmeasured; my estimate is 120-160 min against the 10800 s cap.
- The 8 stuck `snapshots` events (`DD-0c-probe-results.md:45`): the same ids on two ticks is a §7 stop.
