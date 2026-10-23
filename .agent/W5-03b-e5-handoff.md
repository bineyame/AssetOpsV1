# W5-03b E5 handoff: authored EV scenario store (backend only)

Branch `task/W5-03b-e5-backend`, based on `29d7539c` (main `3bdc7d02` plus the W5-03b pre-flight). This was built under the lane-2 ruling (`.agent/W5-02b-K2-rulings.md` "Lane 2 ruling"), the E5 card, and the "E5 consolidated correction" (P-E5-1..10, P-34-2/3). It touches no frontend file, no Site route, nav or registry file, and makes no captures.

## Units and commits

| Commit | Content |
| --- | --- |
| `c769a1df` | Migration `0034_w5_ev_scenarios`, whose `down_revision` is exactly `0033_w5_cold_work`, plus the 18 sole-head pins (P-E5-1) moved to 0034. The `test_w501` chain assertion now names `0033` literally. Downgrade targets keep 0033/0032/0030. |
| `303c4971` | `ev_scenarios/{rules,store,service}.py`, `ev_scenarios_api.py`, `EvReadService.selected_provenance_on` and `.scenario_basis_on` (`postgres_assessment_store.py`), `EvSiteReads.scenario_money_on` (`ev_site_reads.py`), and the `main.py` mount directly after the E1b depth mount. |
| `0932ce41` and the next commit | The rule-8 E5 blocks after each C4 peer in `configuration-persistence.ps1` (declaration, writer list, both resets, forbidden DML, INSERT-only, unseen, probe names). The probe corpus in `writer_guard_probes.py` (doc, constant, probes, controls). The follow-up commit restores two C4 closing braces that the insert script displaced. |
| `1c212bc2` | `backend/tests/test_w503_ev_scenarios_postgres.py` |

The public methods W5-04 will call are `EvReadService.scenario_basis_on(c,t,s,code,lo,hi,known_at)`, `EvReadService.selected_provenance_on(c,snap,ids)` and `EvSiteReads.scenario_money_on(c,snap,cutoff=None)`. The service is `EvScenarioService(store, ev_reads, ev_site_reads)`, which takes the site reader alongside `ev_reads` as P-E5-2 requires.

## Checks (actual output)

- **P-E5-7 pre-check, before the schema commit:** the E1 `Chain` cases `complete` and `fault` each select 1 `energy_complete` session revision at the 09:00 watermark. The `late-record` case at 09:00 selects only an `INCOMPLETE` session, so that case cannot be authored (see judgment call 8).
- **E5 file:** 9 passed. The three tests later fixed (money-head window filter, counts order, pending fixture) were rerun and gave 3 passed.
- **Focused run:** this covered the E5 file, the 17 head-pin test files (`mini_depth_probe.py` is a helper they import), `test_w503_ev_depth`, `test_w503_ev_availability` and `test_w207_ev_site_reads`. It ran on `1c212bc2` with `-n 4 --dist loadfile` and private base DB `assetops_w503e5_test`.
  - Result: 268 tests, 267 passed, 1 failed, 0 skipped, 0 errors (JUnit), in 4095 s under machine contention.
  - The one failure was `test_s405_publication_postgres.py::TestAdmissionLockCost::test_measure_open_batch_lock_cost_against_the_unbound_baseline`, a timing bound (`assert 146.735 < (80.611 + 50)`). Rerun alone it gave 1 passed in 25 s. It does not touch E5 code.
  - An earlier attempt failed at collection in every worker with `AttributeError: shell32` (ctypes failing to load a Windows DLL). That was environmental, and the retry above collected normally.
- **Writer probes:** default runner, all 13 new names. 11 were CAUGHT and the 2 controls were ALLOWED, and the tree was restored.
- **`tools/check-all.ps1`:** all 11 guards passed. `check-architecture.ps1` also passes on its own.
- **Cleanup:** the keep-awake PID 5648 I started has been stopped. `assetops_w503e5_test` is dropped, and the harness dropped its run-owned clones. `frontend/tsconfig.tsbuildinfo` stays untracked.
- **Still needed:** the coordinator runs the full suite, because `main.py` and a migration changed.

## Judgment calls (please confirm at review)

1. **Money cutoff.** `scenario_money_on` calls `_select(ctx)` with `cutoff=None`, which gives the current head. It passes a given `cutoff` through to `_select_as_of`. E5 passes none. The as-of branch bounds `recorded_at` by a wall-clock cutoff, so the 09:00 evidence watermark would always give null IDs, and the spec says the evidence clock is independent of DB time. Only a CURRENT selection can be authored. If the as-of path was meant, the change is one argument in `service._basis`.
2. **Limit refusal.** I used the existing `EV_LIMIT_INVALID` (422, range 1..100, ASCII digits). The E5 table lists no limit code and adds no new one.
3. **Correction errors.** An unknown or invalid root ID returns 404 `DECISION_NOT_FOUND`. A predecessor that is not in the root returns 422 `DECISION_LINK_SCOPE_INVALID`. Both follow the C4 pattern; neither code is in the E5 table.
4. **Index order.** The index is `(tenant_id,site_id,recorded_at DESC,id)` as the E5 text gives it. The merged C4 index uses `id DESC`.
5. **No-service code.** A missing service or database returns 503 `EV_READ_UNAVAILABLE` from the unchanged `ev_gate`. The spec allows either 503 code. A store failure returns `DECISION_STORE_UNAVAILABLE`.
6. **Foreign Foundation.** If the revision `foundation_revision_on` resolves to is not in the selected head's `foundation_ids`, it counts as foreign: the Foundation is treated as null and the request gets 422.
7. **Selection provenance.** `selection.source_provenance` is the selected block, the E1 convention. `selection.accepted_evidence_ids` is the union of `ev_session_evidence` and `ev_meter_interval` over the selected session revisions (P-E5-3). Meter evidence that is outside the window's `accepted_on` set gives 422.
8. **Pending/historical test fixture.** Because the registered late-record session is incomplete at 09:00, the pending/historical test uses the `complete` chain plus a test-local `late_import`. That helper is a clone of the merged E1 `add_import`, with its ACCEPTED disposition `decided_at` set to 09:05. It moves the watermark and queues the job. No scenario row is seeded, and `energy_complete` is not bypassed.
9. **Write path.** `store.reading` wraps the selection read. Failures on append go through C4's `transaction()` path: one retry, then 503.
10. **List payload.** The DTO has no `total_pages`, following the E5 DTO literally. The API imports `_instant` and `_Refused` from `ev_assessment_api` to reuse the gate's exact time and refusal behaviour.

No question file was written: nothing contradicted merged code. The items above are spec-reading calls, each isolated to a single place in the code.

## Fix round (branch task/W5-03b-e5-fix, rulings in .agent/W5-03b-e5-rulings.md)

Commit 7034cae7 holds code and tests (one commit). Unchanged: `main.py`, the migration 0034, the rule-8 guards and the writer probes (no schema or guard change, so no probe rerun is needed).

| Finding / ruling | Change |
| --- | --- |
| A1 current money head | No code change: `service._basis` already calls `scenario_money_on(c, snap)` with no cutoff. Covered by the baseline test (priced IDs equal the W2-07 head and cited tariff) and by the stale and fault cases (both IDs null, scenario accepted). |
| A2 limit | No code change (422 `EV_LIMIT_INVALID`, "'limit' must be 1 to 100."). Test: exact body for limit=0 and the 51-root default page. |
| A3 correction identity | No code change (404 DECISION_NOT_FOUND, 422 DECISION_LINK_SCOPE_INVALID, 422 EV_SCENARIO_INVALID for a malformed predecessor shape). Exact messages asserted in `test_command_refusals_and_replay`. |
| A4 index/order | No code change. Index already pinned in `test_schema_constraints`; new `test_equal_recorded_at_pagination_order`. |
| A5 currency | `EvSiteReads.scenario_money_on` now also returns `currency` (never persisted). `EvScenarioService._authorable(basis, cmd)` refuses a different authored currency when a tariff revision is selected (422 EV_SCENARIO_INVALID, the ruled message). Test: `test_currency_must_match_priced_tariff` (KES+USD refused with [0,0], KES ok, correction refused, unpriced+USD ok with null IDs). |
| A6 foreign meter | `foreign_meter_evidence` in `scenario_basis_on` is also true for a meter ID absent from the head's `evidence_ids`. Tests (e) and (f) in `test_baseline_foundation_and_foreign_meter_refusals`; positive test asserts accepted, head and provenance membership. |
| M1 / ruling 7 | `foundation_revision_id` is now null when the head cites no Foundation IDs (fallback no longer validates). `test_baseline_foundation_and_foreign_meter_refusals` cases (a)-(d), each 422 and [0,0]; correction path too. |
| L1 malformed 503 | `test_malformed_stored_basis_and_root_window_are_503` (missing cutoff, to, from; restored after delete). |
| L2 default page | `test_default_page_is_fifty` (51 roots, 50 then 1; page two keeps clocks, window, selection). |
| L3 race | `test_write_race_retries_once_then_503` (one race 201, same-key race 200, correction race, two races 503; counts checked). |

Verification so far: DB-free only (py_compile, the 2 DB-free tests in the E5 file, collection of all 15, check-all). The new and changed Postgres tests have NOT been run; they await the batch.
