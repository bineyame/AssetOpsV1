# W5-02a core review (K1a, K1b, K1c)

Reviewer: fresh independent Claude reviewer, 2026-10-23. Branch `task/W5-02a-cold-action-root`, head `e3ada3df`, diff `main...HEAD` (merge-base `46a9936b`). `main` has since moved to `2dc2e5ed` (W6-01d). The two touch no common files, and `git merge-tree` merges them cleanly.

## Verdict: REVISE (one Medium; fix on the branch after an Architect file ruling)

The backend core is correct against K1a–K1c and the three W5-02a build rulings. One cross-surface regression blocks the merge. A Medium blocks under the project rule.

## Findings

### M1 (Medium, acceptance gap / regression): the W6 request-detail page rejects any request linked to a domain Action
- Where: `frontend/src/work/globalWorkClient.ts:339` and `:439`, together with `backend/assetops_backend/work/detail.py:75` (`"action_links": all_action_links(links)`).
- What is wrong: since K1c, `select_case_detail` puts domain links into `work_detail.action_links` with `action_event_id: null`. The W6 global request detail (`/api/work/requests/{case_id}`) nests that `work_detail`. Its frontend runtime validator `isWorkDetail` requires `isString(x.action_event_id)`. Line 531 turns a failed validation into `{status:"refused", code:"WORK_STORE_UNAVAILABLE"}`. `test_w601c_request_detail.py::test_domain_action_link_matches_w4` itself asserts that the raw `work_detail.action_links` row carries the domain key, so this payload does reach the client.
- Why it matters: any Maintenance request bound to a domain Action shows a false "store unavailable" on the mounted W6 Overview, Record and History pages. That is the exact destination K4a's `Inspect maintenance evidence` button opens for the linked WR, and it is what K3/K4 captures will hit. In open question 1 the builder called the W6 typing "type only", but this is a runtime check, not just a type.
- Exposure today: latent. `create_app` injects no domain SERVICE principal by default, so no product path writes a domain Action yet. It becomes live as soon as host wiring or the K2+ captures persist one.
- Fix: `globalWorkClient.ts` is on no card, so the Architect must rule first. Either (a) add `globalWorkClient.ts` and a W6 client test to K1c: accept `isNullableString(action_event_id)` plus optional `kind`/`finding_revision_id`, update the line-339 type, and add a test with a domain link in `work_detail`. Or (b) keep `work_detail.action_links` W1-only on the detail wire. (b) changes the W4 detail contract, so (a) is the smaller change.

### L1 (Low, test gap against named ruling tests; code verified by reading)
- `test_w502_domain_intent_postgres.py:216`: K1 ruling 1 names an operational-record ID and a `maintenance_record` from another case or Site as 422 cases. Only a random UUID is tested. `postgres_domain_intent.py:record_in_case` filters by tenant, Site, case and cutoff, so the behaviour is right.
- K1 ruling 3 names "retry the original key/body after the advance → 200". The retry at `:195` runs before the ASSIGN advance. The code does check idempotency before the head check, so it would return 200.
- K1 ruling 2's "absent Action plus invalid link → 404" is not asserted as one combined case. The service resolves the Action before any link lookup, so it holds by construction.
- Fix: add the missing assertions in a later run or at K5. This does not block.

### L2 (Low, residual): domain Site links point at a route that does not yet dispatch by domain
The W4 Site index, case detail and W6 global index now emit `/sites/{code}/actions/{id}/verification` for a domain Action, as K1c requires. Until K4a, the frontend route is the W1 Action page, which cannot load a domain ID. This is latent for the same reason as M1. It is not a defect of this merge.

## Checklist results
- **Every changed file is on a card:** yes. All 52 code files map to K1a/A2/A5, K1b/B3, K1c/C1 or the K1c build rulings (including `work_api.py`, `test_estate_guard.py`, `global_detail.py`, `test_w601c`, `workClient.ts`, `siteWorkCases.tsx`). The 17 head-pin files match A5 exactly.
- **Migration 0033:**
  - `down_revision = "0032_w5_cold_scenarios"`, and it is the sole head (no other migration names 0032 or 0033 as parent).
  - The downgrade takes ACCESS EXCLUSIVE locks, refuses any row with the exact A1 literal, then drops the W1 collision trigger, the other triggers, the tables and both functions. No cascade.
  - A1 constraints are present: scoped composite FKs, `domain_action_intent_criteria_count_chk`, root and one-successor uniques, the `(action_id, supersedes_id)` FK, the case-link uniques, a direct-SQL case-consistency trigger, and three `*_no_mutation` triggers on `w4_append_only()`.
- **Head pins:** correct. `mini_depth_probe.py` keeps the 0032 step, adds the empty 0033 step and a no-rows check. `test_w501` now asserts the chain 0033→0032→0030.
- **Collision triggers and W1 409:**
  - `reject_cross_domain_action_code()` takes the advisory lock, queries the opposite table, and raises 23505 with constraint `action_cross_domain_code_conflict` and the exact message.
  - `postgres_action_store.accept` pre-checks after `nextval`, and maps only that constraint, outside `_run`, to 409 `ACTION_CODE_CONFLICT`.
  - The domain writer maps it to 409 `DOMAIN_INTENT_CONFLICT`.
  - Tests cover both directions, concurrency in both orders and propagation of unknown IntegrityErrors.
- **Rule-8 writer block and probes:**
  - `$domainIntentWriter` is in `$pgWriters`, `$pgWritesSeen` and `$pgDriverSeen`.
  - The INSERT-only, own-tables-only, foreign-writer and per-table anti-vacuity checks are present.
  - The reader is in `$pgReaders`; the four A5 probe names are in `$workProbeNames` and in `NEGATIVE`, with three controls.
  - The HTTP regex gains bare `source_publication`, and `domain_work_api.py` contains none of the forbidden tokens.
- **Union index:**
  - `PAGE_DEFAULT, PAGE_MAX = 5, 100` on the new index only; W4 is untouched.
  - The W4 literals are reused exactly (`model.MESSAGES`), in B3 order (window, limit, known_at shape, future known_at, cursor), with 409 `WORK_BASIS_CHANGED`.
  - The Postgres test proves 6 rows give a page of 5 plus a cursor.
- **`global_detail.py`:** uses the literal `by_key.get(action_selection_key(x))`. The key is `("ACTION", id, event)` for W1 and `("DOMAIN_ACTION", id, finding_revision_id)` for domain links. Covered by the W6-01c test.
- **Producer modes:**
  - Every mode uses R-relative clocks: install D+12:00, setup D+15:00, release D+17:10.
  - STALE is the plain shifted document with `WINDOW_MINUTES["stale"]=90`. The exact wider window is enqueued before the worker runs. The test asserts the latest SUPPORT time `<= end < window_end - 10m`, then STALE_SOURCE in the W5-01 read, the pin and coverage, with K0 corroborated.
  - PENDING holds a probe and releases it late, leaving the job unrun. Pin, coverage and W5-01 all read `PENDING_RECOMPUTE` at the late `decided_at`, over the unchanged assessment revision.
  - UNKNOWN runs a fresh DB with the no-probe replay (asserted CURRENT), then the always-on seeded empty-support copy (new run, assessment and selection, original `knowledge_cutoff`, `clock_timestamp()` times), then a domain Action pinned to the START_RESPONSE Finding and linked to a real W4 request. Pin, coverage and W5-01 all read UNKNOWN.

## Architect item: is the "by elimination" UNKNOWN reason within the ruling?
Yes, it is within ruling 3. `cold_reads.currentness_state` returns UNKNOWN on only four conditions: no selection, no latest probe, a null window end, or a future window end. PENDING and HISTORICAL take precedence and are excluded because the observed state is UNKNOWN. The tests rule out each of the other conditions:
- no selection: `assessment_revision_ids` is non-empty and contains the seeded revision;
- null or future window: `window.to < known_at`, and `pin.window_end <= DB now`;
- missing Finding or FK failure: the pin is non-null, with lineage, on the selected START_RESPONSE revision.

Zero SUPPORT links then means `latest_probe_at is None`. That leaves the no-usable-probe branch as the only cause.

One optional improvement: `_snapshot` already records `NO_PROBE_NOTE` in `limitations` even though the `cold-depth-1` wire drops it. One assertion on the snapshot's `limitations` would turn the inference into a direct proof. This is a recommendation, not a blocker.

## Readiness item 29
It can close on the producer evidence. `test_w502_cold_scenario_producer.py` (ordinary replay, wider-window STALE, seeded UNKNOWN) and the three link-state tests in `test_w502_domain_work_links_postgres.py` pass on `e3ada3df`, which is the merged-base branch head (W5-01b and W6-01c are in its base). Record the closure when W5-02a-core merges after M1 is fixed. The C4 browser STALE/UNKNOWN capture gate may then open for K2b.

## Checks run by this reviewer
- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed.
- `npx.cmd tsc --noEmit` (frontend): exit 0. I did not run `npm.cmd test` or `npm.cmd run build`, so the frontend suite and build are unverified by me. The diff's frontend changes are type and key only.
- Focused backend tests, `-n 3`, one private DB `assetops_w502rv_test` plus harness clones, all dropped afterwards. Files: `test_w502_cold_scenario_producer`, `test_w502_domain_work_links_postgres`, `test_w502_domain_intent_{model,api,postgres}`, `test_w502_domain_action_index_{api,postgres}`, `test_s6_action_store_postgres`, `test_w601{a,b,c}_*`, `test_w403_work_links_postgres`, `test_w401_work_api`. Result: **104 passed**, 0 failed, 614 s.
- Not rerun: the full backend suite and `tools/check-all.ps1`. The packet cites check-all 11/11 on `d7ff896c`. Only the handoff text changed after that commit. I did not inspect the full-suite JUnit numbers.
