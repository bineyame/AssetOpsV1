> Finished; historical. Archived from .agent/WALK-perf-review.md on 2026-11-18 (declutter step 4).
# WALK-perf review (fix/WALK-perf, worktree /opt/assetecon/AssetOpsV1-walkperf)

Reviewer: fresh Claude reviewer (did not author). Base main a1957a47a. Commits f6c67e34b and 6aa49760f. Diff `main...HEAD`: 9 files, +360/-46.
Judged against `.agent/WALK-perf-ruling-2026-11-14.md` F1-F3 and `.agent/WALK-perf-packet.md`.

## Verdict: ACCEPT WITH NOTES

F1, F2 and F3 follow the ruling. I found no path where a stored hit serves a body the gate would now refuse, or a stale body.
- M1 is a test gap.
- M2 is a guard-reporting gap.

Neither is a defect in the served bytes. I recommend fixing both on the branch, which is cheap. If the coordinator merges first for the walk, both must land before the W6 / final complete review relies on this route.

## Answers to the focus questions

**1. Can a hit serve a body the gate would refuse, or a stale one? No.**

The gate (`main.py:425 performance_gate`) reads three kinds of input:
- **DB tables:** `lineage_breaks` and `selected_intervals` read `analytic_run`, `analytic_run_selection`, `analytic_run_evidence`, `analytic_run_assessment`, `assessment_revision`, `ingestion_disposition`, `foundation_revision` and `recompute_job`. All of them are in `INPUT_TABLES` (`migrations/versions/0047_chain_response.py:29-50`).
- **Files:** the newest performance comparison (F root `migration-performance/{site_key}`), the legacy claims (`assessments/sites/{site_code}.json`), and the legacy inventory and store root (`evidence/sites`, `registry`, `commits`). All are in `config/chain/file-inputs-v1.json`. Each route's `sites=(site,)` resolves them for that Site.
- **Constants:** the environment identity, `MODEL_VERSION`, and `BRACKET` (a fixed 6 h).

The gate reads no clock. The Overview's `empty_legacy` stays outside compose but comes from `site_cutover_basis`, which is in W. A 409 refusal raised inside compose propagates out of `ResponseStore.serve` before any insert (`chain/response_store.py:193-196`), so refusals still never store.

One behaviour change, benign: a gate store-down is now raised inside compose. It still surfaces as the same typed 503. It never reaches the INFRA-1 stale path, because the HTTPException leaves `_composed` before the `sc.degraded` check.

**2. Is the financials key complete? Yes.**

| Key part | Where it comes from |
|---|---|
| route | `FINANCIALS_ROUTE` |
| tenant | `StoredRoute.tenant_id` |
| site | `sites=(site,)`, plus the explicit `site` field |
| finding | explicit field |
| revision (or None) | explicit field |
| locale | added by the store |
| code version | `version()` in the lookup (`response_store.py:177-183`) |
| watermark | Site-scoped W + F, where `watermark_sites=(site,)` |

The route has no `known_at` or as-of parameter, so it is a live body. It expires at the Site's next local midnight, or at any boundary registered through `read_scope`.

- **Revision None.** With the gate open, this key serves the head revision. The head moves through `finding`/`finding_revision`, which are in W.
- **No clock reads.** I found no `now()`, `CURRENT_DATE` or `datetime.now` on the read path: `finding_read`, `money_eligibility`, `consequence_read` and the assumption read. The clock reads exist only in the `*recompute` write paths. Prices ("today's price timeline") are `financial_assumption_*` rows, which are in W.
- **`price_action` is pure.** The guard flags it as unlisted, but it has no file or DB input.
- **Frontend.** It requests `.../financials?revision_id=…` (`frontend/src/sites/financialsClient.ts:496-498`), which is the key that prebuild builds.

**3. Can F3 leave ranges cold after a data change?** Only as a performance gap, never as wrong data. The store re-checks W on every request.
- A data change on any prebuilt Site, or on the estate, makes a prebuilt route miss. `states` then holds a non-`hit` entry, so `warm_due` returns True.
- A change seen while a warm is running is kept pending (`warm_pending`).
- A tick that fails before the prebuild leaves states None, which also warms.
- Ranges whose `valid_until` passes without any prebuilt route missing are refreshed within 30 min at most.

**4. The deviation (`chain_paths` takes the first KOBO Overview that names a Finding).** Sound, and more robust than "the first Overview". The weakness is that it still skips silently when no Overview names a Finding. See M2.

**5. Are the tests adequate?** Adequate for the control flow:
- the gate is skipped on a hit and run once on a miss;
- a closed gate returns 409 and stores nothing;
- the key varies by finding and by revision;
- the no-store path works;
- the prebuild de-duplicates and retries;
- the `warm_due` table.

They use a fake store only, which leaves a gap. See M1.

## Findings

### M1 (Medium, test gap): no test exercises Financials invalidation through the real store
- **Where.** `backend/tests/conftest.py:60` sets `ASSETOPS_RESPONSE_STORE=off` by default. Every existing Postgres financials test therefore composes uncached, including `test_pr3_price_entry`, `test_s4_consequence_recompute_postgres` and `test_w302_financials_links_postgres`. The new file (`backend/tests/test_walkperf_gate_in_compose.py:24-40`) keys a fake store on `(route, request)` and never models W.
- **Why it matters.** Nothing automated shows that a price assignment, a new FindingRevision or a consequence recompute turns a stored Financials body into a miss. Taken with the guard gap, the "never stale" property of this new stored route rests on my static table review alone.
- **Fix.** Add one Postgres test with `ASSETOPS_RESPONSE_STORE=on`, modelled on `test_ch5c_response_store_postgres.py`:
  1. GET financials and see `stored`.
  2. GET again and see `hit`.
  3. Write a price assignment, or recompute the consequence.
  4. GET again: the response is a miss (`stored`), and its `consequence` differs.

### M2 (Medium): the watermark guard passes silently without covering Financials
- **Where.** `tools/chain_watermark_guard.py:204-210`.
- **What is wrong.** When no prebuilt KOBO Overview names a Finding (any DB whose gate is closed), no financials path is added, and the guard still returns rc 0 with `unresolved []` and `untracked []`. This is exactly how the known gap stayed invisible except for the packet's note.
- **Fix.** Record the skip in the guard's JSON output, for example `"financials": "not exercised: no KOBO Overview names a Finding"`. W6 and the final complete review can then see it.

### L1 (Low, residual): new failure surface and cost in the prebuild
- **Where.** `backend/assetops_backend/chain/prebuild.py:106-110, 114`.
- **What.** Any financials fetch that is not a 200 now makes the prebuild `FAILED`. That is a `PrebuildRefused` at prepare time; in serve the failure is logged and the API keeps serving. The extra first-build time is unmeasured: one compose of about 2.3 s per distinct (finding, revision) found in Overviews and index rows.
- **Fix.** Nothing is needed now. Record the first-tick `prebuild_ms` and the `non_200` count at deploy.

### L2 (Low): the `warm_due({}, ...) is False` case
- **Where.** `backend/tests/test_walkperf_gate_in_compose.py:224`, `tools/demo_combined.py` `warm_due`.
- **What.** Empty states (nothing returned 200) mean no warm. That only happens on a fully failed prebuild, so it is a corner case. It is pinned by a test as intended behaviour, which is a preference, not a gap.

## Known gap: should it block the merge?

It does not block the merge for the walkthrough. The proposed post-deploy live check is **not** a substitute for the guard, however:
- "Stored, under 0.4 s, body equal to an unstored read" proves the speed and the bytes at one instant.
- It cannot show that a later change to an untracked input would invalidate the body. Only the guard (compose-scope table and file audit) or M1's invalidation test shows that.

My static review finds every table and file on the financials compose path inside W and F, so the residual risk is low. My recommendation:
1. Merge after the live check.
2. Land M1 (preferably on the branch before merge, since it is about 30 lines).
3. Before the final complete review, run the guard on a `_test` DB with an open gate where a KOBO Overview names a Finding. A fixture DB is fine; the walk DB is not to be cloned.

## Checks run (by me, this revision 6aa49760f)

Python was `/opt/assetecon/AssetOpsV1/.venv/bin/python`, with `PYTHONPATH` set to the worktree packages (I confirmed `assetops_backend` imports from the worktree). `ASSETOPS_TEST_DATABASE_URL` pointed at the base `assetops_test`; the harness clones run-owned DBs.

- **Packet's targeted set: 155 passed, 0 failed, 19 s.** The files were `test_walkperf_gate_in_compose`, `test_s5_overview_read`, `test_e4_prebuilt_routes_generator`, `test_e4_prebuilt_routes_source`, `test_sr83_guard_route_terms`, `test_sr83_store_term`, `test_infra1_degraded_store`, `test_ch5c2_clock_guard`, `test_s4_finding_api`, `test_s4_finding_index_reach` and `test_ch5c_store_off`.
- **Adjacent financials and store tests: 266 passed, 2 failed, 89 s.** The files were `test_pr1_price_action`, `test_pr3_price_entry`, `test_s4_consequence_recompute_postgres`, `test_w302_financials_links_postgres`, `test_w302_money_api`, `test_s4_assumption_read_api`, `test_e4_performance_on_change`, `test_warm1_ranges`, `test_demo_combined_finish_rows` and `test_ch5c_response_store_postgres`. The 2 failures also fail on main a1957a47a in the main worktree, so they are pre-existing and not caused by this branch:
  - `test_w302_money_api::test_w302_money_exact_selected_heads_and_unpriced_cold` (a links dict mismatch);
  - `test_demo_combined_finish_rows::test_kis8_protect_passes_on_the_node_line_and_fails_otherwise` (DID NOT RAISE).
- **Not run:**
  - **Full suite:** not run, per the sprint policy.
  - **check-all:** not rerun; the packet reports 21/21.
  - **Watermark guard:** not rerun; it needs a clone and an open-gate DB.
  - **Frontend:** untouched by this diff.
  - **Live walk serve and DB:** not touched.
