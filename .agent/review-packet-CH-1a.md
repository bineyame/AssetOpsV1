# Review packet CH-1a: day snapshots, quality grades, evidence class, subjects

- Branch `task/CH-1a-snapshots`, worktree `AssetOpsV1-ch1a`. Main `26f6edcea` (CH-0) is merged in.
- Authority: `AssetOpsV1-plan2\.agent\build-sheet-CH-1a.md`, including §5c. Pre-flight: `.agent/CH-1a-preflight.md`. Phase 1: `.agent/CH-1a-phase-1-handoff.md`.
- `B/` = `backend/assetops_backend/`. USER_REVIEW_REQUIRED: no screen changes. Architect rulings are needed on deviations D1–D4.

## Outcome

One builder (`B/chain/builder.py`) writes graded, insert-only `site_day_snapshot` rows for each Site, local day, subject and measure, using one policy, one calendar and the six measure implementations. One reader (`B/chain/reader.py`) answers `grade_counts` and `grade_counts_many`. The CLI is `python -m assetops_backend.chain.snapshots build|show`. The L3 clone reproduces §5, with the one exception in D1.

## Files materially changed (phase 2; phase 1 is listed in its handoff)

- `B/chain/adapters/postgres_chain_inputs.py`: the registered SELECT-only reader. It runs its own SELECTs and delegates to existing services built by their domains' composition functions.
- `B/chain/measure_impls.py`: the six measure implementations and `build_measure_set`.
- `B/chain/composition.py`: `build_chain_inputs`, `build_snapshot_builder`, `build_snapshot_reader`, `build_chain_services`.
- `B/chain/snapshots.py`: the CLI.
- `B/chain/ports.py`: the final `ChainInputReader` method list.
- `backend/tests/test_ch1a_snapshot_postgres.py`: the L2 test (4 tests).
- 24 test files: the migration head literal changes from `0041_walk1_objective_min_days` to `0043_chain_snapshots`. The 0041 test gains `THIS` (D6).
- `tools/checks/configuration-persistence.ps1`: `$snapshotWriter` is placed before `$trialComparisonWriter` in the driver list, so the estate self-test anchor `, $trialComparisonWriter)` stays unique.

## Acceptance per sheet item

| Item | Status | Evidence |
|---|---|---|
| §1 Migration 0043: CHECKs, indexes, trigger, refusing downgrade | Met | L2 `test_0043_catalogue_and_insert_only` and `test_downgrade_refused_with_rows_then_allowed` (refused with a row; after TRUNCATE it downgrades to 0041, then upgrades to head) |
| §2 Declared policy and calendar, versions in `input_fp` | Met (phase 1) | L0 `test_ch1a_grading.py` |
| §3 Six measures, no outcome literals (OL-1) | Met | A search for outcome-id literals `"(MG|CC|EV)-<digit>` in `B/chain/**/*.py` finds 0 matches |
| §3 Measures read only through `ChainInputReader`; no driver import | Met | Architecture seams guard passes. The chain domain is registered. `measure_impls.py` imports no driver |
| §4.1 Every grade from `grading.classify_day` | Met | The builder is the only caller. No second day-count rule exists |
| §4.2 Idempotent; a changed input writes revision 2 | Met | L2 productive test: writes `[T,T,T]`, then `[F,F,F]`, then `[F,F,T]` with revision 2. L3 rebuild writes 0 of 194 rows |
| §4.3 Store is insert-only | Met | L2: UPDATE and DELETE are refused by the trigger. The guard non-vacuity proof is under Checks |
| §4.4 `grade_counts_many` equals per-Site results, in one statement | Met | L2 counts the cursor executes: exactly 1 statement on `site_day_snapshot`. L3: 11.3 ms for 3 Sites over Oct (target ≤ 50 ms) |
| §4.5 CLI: tenant default and exit 2, no URL gives exit 1, JSON lines, default range | Met (L3 run); exit paths not unit-tested | `snapshots.py` |
| §5 L3 values | Met, except D1 | Table below |
| §5c Q1–Q8 rulings | Met, with the bases recorded in D2–D4 | |
| §6 L2 seeding (Q8) | Met | Stub reader with the real store for productive. Real noon implementation on MG-W402-001, decisions equal the mini-depth read's |
| §7 Guard registration, anti-vacuity | Met | Guards below |

## L3 clone value table (`assetops_chainclone_ch1a_test` from polish, migrated, built 2026-10-01..11-02, then dropped)

| Site · day | Measure | Expected | Actual | |
|---|---|---|---|---|
| Kobo 28, 30, 31 Oct | `productive_kwh` | PARTIAL (~33%) | PARTIAL 28800/86400 (33.33%), all three days | ok |
| Kobo 28, 30, 31 Oct | `avoidable_gen_min` | PARTIAL (~33%) | PARTIAL 29100/86400. Value 31 Oct `{minutes: 200, indeterminate: 30}`; 28/30 Oct 0/0 | ok |
| Kobo 30 Oct | `productive_kwh` value | 168.3 kWh, 42.08 USD | `168.333` kWh, `42.08` USD, price revision `94bb9036…` | ok |
| Kobo 31 Oct | `productive_kwh` value | 0 kWh | `0.000` kWh, money `0.00` USD (Q7) | ok |
| Kobo 31 Oct | `noon_headroom_kw` | COMPLETE 25–31 kW | COMPLETE, 25–31, ELIGIBLE | ok |
| Kobo 21, 25, 26, 27, 29 Oct | all Kobo measures | NO_DATA, no value | NO_DATA, value null, all 15 rows | ok |
| EV 26 Oct | `charging_kwh` | NOT_EXPECTED | NOT_EXPECTED | ok |
| EV 27 Oct | `charging_kwh` | LOW (~1 of 8 h), 15 kWh, 4.50 USD | LOW 3600/28800, `15.000` kWh, `4.50` USD | ok |
| EV 20 Oct | `charging_kwh` | LOW, 9.00 USD | LOW 3600/28800, 30.000 kWh, `9.00` USD | ok |
| Cold 28 Oct | `backup_start_chain` | LOW | LOW 3900/86400, `{starts: 1, failed: 1}` | ok |
| Cold 28 Oct | `chamber_temp_c` | **NO_DATA** | **LOW 2100/86400, peak 4.8** | **D1** |
| Cold 31 Oct | `chamber_temp_c` | LOW (~65 min), peak 4.9 | LOW 3900/86400 (65 min), peak `4.9` | ok |

- Also shown: Kobo 28 and 30 Oct `noon_headroom_kw` is COMPLETE EXCLUDED 0/0.
- Grade counts over the 33 days:
  - Kobo: 8 PARTIAL, 25 NO_DATA.
  - Cold: 3 LOW, 30 NO_DATA.
  - EV: 2 LOW, 2 NO_DATA, 29 NOT_EXPECTED.
  - `enough_data_days` is 0 for every Site.
- Kobo has 97 rows, not 99: 1–2 Oct have no productive user yet (phase-1 risk; counted NO_DATA).
- **Build timing:**

  | Site | ms per measure-day | Build time |
  |---|---|---|
  | Kobo | 93.1 | 9.2 s |
  | Cold | 53.5 | 3.5 s |
  | EV | 37.8 | 1.2 s |

  The budget was ≤ 50 ms (est.). Kobo and Cold are over it (D7).
  The rebuild wrote 0 rows (Kobo 8.8 s, Cold 3.1 s, EV 0.9 s).
- **Chain coherence** on the clone (collected without `--known-at`, checked with `expected-today.json`): every rule reports 0 new findings, and the self-check passes 39 with 0 failures. The 56 requests all returned 200. Screens are unchanged.

## Checks (revision `19b0d317f`, except where named)

- **L2:** `run-host-tests.ps1 -- test_ch1a_snapshot_postgres.py` (L0 is `test_ch1a_grading.py`).
  - The first run gave 3 passed and 1 failed: noon graded PENDING. Fixed by D5.
  - The noon test then passed (102 s).
  - Final rerun at `19b0d317f`: L0 and L2 together gave **29 passed** (85 s).
- **Scoped existing tests (§6.3 plus the handoff list),** on `91fbc51f3`, 282 s:
  - 173 passed, 2 failed: `test_walk1_objective_min_days_postgres` pinned head 0041 (D6).
  - The files: `test_ch1a_grading`, `test_w301_estate_coverage`, `test_cov_partial_portfolio`, `test_walk1_objective_min_days_postgres`, `test_w402_rules`, `test_w402_projection`, `test_w402_reads`, `test_w402_inputs_postgres`, `test_walk1_productive_sales`, `test_out_d5_objectives_postgres`, `test_out_b2_mini`, `test_s3_dispatch_read_postgres`, `test_out_b1_board`.
  - After D6: `test_walk1_objective_min_days_postgres` and `test_walk1_productive_price_postgres` gave 5 passed.
  - **Head-literal sample:** `test_s1_bindings_postgres`, `test_out_d1_schema_postgres`, `test_cc_schema_postgres`, `test_w502_domain_intent_postgres`, `test_s4_evidence_consequence_work_postgres` and `test_w203_cold_migration_postgres` gave 71 passed (584 s). The other 16 edited files are **not run** (D6).
  - Phase 1 had already run `test_out_b1_board` and `test_out_b4_board_postgres` after the `dispatch_minutes` move: 58 passed.
- **Architecture seams:** passed.
- **Agent workflow:** passed.
- **Estate guard self-tests** (`tools/checks/test_estate_guard.py`):
  - The first run gave 6 passed, 1 failed (`test_trial_comparison_writer_registered`). The anchor text had been changed by the phase-1 list edit.
  - After the reorder: 7 passed (362 s).
- **Chain coherence fixtures:** 51 passed.
- **Guard non-vacuity:** at `cace0cc01`, two violations were injected:
  - `DELETE FROM site_day_snapshot` in the store;
  - `INSERT INTO site_day_snapshot` in `postgres_chain_inputs.py`.

  The Architecture seams guard failed with four messages: a second writer, the store never deleting, the insert-only rule, and the table insert-only rule. Both files were restored with `git checkout --` and `git status` is clean.
- **Not run:** the full backend suite, vitest, the demo build, and the other guards (all deferred per §6).

## Deviations (for the Architect)

- **D1. Cold 28 Oct `chamber_temp_c` is LOW, not NO_DATA.**
  - The 28 Oct `cold-excursion` window (16:00–17:05 UTC) has a selected assessment with 35 min of probe coverage left after its gaps. So ruling Q6 gives 2100 s, and the peak is 4.8 °C from raw readings.
  - Not tuned. Either the §5 expectation or the Q6 basis needs a ruling.
- **D2. `backup_start_chain` coverage basis.** Every backup-chain role reading in the data is an instant: `grid_power_event`, `generator_state`, `transfer_result` and `backup_bus_state` have `interval_start` null in all rows. So Q5's "seconds covered by accepted readings" has no seconds.
  - Implemented: the selected `cold-start-response` window ∩ the period, counted only when at least one backup-role reading was accepted inside that window.
  - This matches §5's "covered by backup-role readings only in the session" (LOW, 65 min), but it is my basis, not a ruled one. Please rule it.
- **D3. `chamber_temp_c` coverage is the assessed window minus the gaps,** not the period minus the gaps.
  - Cold assessments are stored per exact window, and `ColdReadService` selects only a window that contains the request. "Period minus gaps" would therefore read about 23 h, COMPLETE.
  - This reading gives the expected 65 min on 31 Oct.
  - Cold and EV services are called once for each stored selected window that overlaps the local period.
- **D4. EV coverage (Q1).**
  - **Status spans.** `EvSiteReads` does not expose status intervals directly. The spans come from the existing pure `analytics/ev_availability.availability_on` (reported state transitions over `ev-status-cadence`), keeping spans with a known state, AVAILABLE or UNAVAILABLE. That module classifies CHARGING and PLUGGED as UNKNOWN, so session time is covered by the SUPPORT meter intervals.
  - **Unknown meter seconds.** They are excluded by construction, because they fall in neither set. They are not subtracted as a scalar.
  - **Connectors.** The union is taken across connectors.
  - **Overlapping windows.** The EV data has two overlapping selected windows each Tuesday (08:00–09:00 and 08:00–09:05). In each overlap cluster the window with the latest selection seq is kept (`latest_disjoint`), so no kWh or money is counted twice.
- **D5. PENDING for `noon_headroom_kw`** uses the mini-depth reader's own live-job rule (`mini_depth/read.py` `_JOBS`): a job cleared by a later selection of its hour is not live. Without it, MG-W402 graded PENDING after reconcile.
  - Dispatch, cold and EV use plain PENDING or LEASED `recompute_job` rows overlapping the period. For dispatch, a window status of PENDING also counts.
- **D6. Head literals: 24 test files edited.**
  - This follows the precedent of `9382d059e`. A new migration cannot land without it, because 2 tests failed until the change.
  - Only 8 of the 24 files have been run.
  - Whichever of 0042 (CH-2) and 0043 merges second must repoint `down_revision` **and** redo these literals.
- **D7. Build time is over the ≤ 50 ms estimate for Kobo (93 ms) and Cold (54 ms).** It is spent in service round trips: the dispatch window twice per day, and one connection per service call. Not optimised in this slice.
- **D8. Smaller recorded choices.**
  - **`avoidable_gen_min`:**
    - An interval counts on the local day its `first_on` falls in.
    - Coverage is all the accepted interval readings the selected run used (Site level, not per generator).
    - Generators and chambers come from the Foundation component types GENERATOR and COLD_ROOM, in force at the period start.
  - **Productive kWh** is stored to 0.001. Money is priced on the unrounded kWh, as the board does.
  - **`dispatch_minutes`** keeps its dict signature, as moved unchanged (phase-1 note).
  - **Renames.** The module is `measure_impls.py`, not `measure_adapters.py`, and the function is `build_measure_set`. Guard rule 1's regex `[A-Za-z_.]*adapters(?:[.\s]|$)` matches any import line ending in or containing `…adapters`.

## DS-R1 (§5b) against the diff

- **Item 5, the calendar:** fixed in phase 1. Kobo and Cold are 24 h; EV is Tue 08:00–16:00 with `source`.
- **Item 4, the noon hour:** labelled keep in `measures.py`, and the period comes from the policy constant.
- **Item 3, generator-shaped subjects:** fixed. Subjects are generic asset ids from Foundation component types. Only the dispatch and backup implementations name GENERATOR.
- **Item 3, dispatch thresholds:** not touched.
- **New demo-shaped item for SWEEP-DS:** the D2 and D3 window-bound coverage. Coverage is limited to the assessed session windows, so it inherits the scenario run windows: Cold 16:00–17:05 UTC, EV 08:00–09:00/09:05.

## Residual risk

- The 16 head-literal files that were not run (D6).
- The CLI exit paths have no unit test.
- `ev_window` relies on `EvSiteReads.context_on`, `energy_on` and `consequence_on` and on the EV `within`/`accepted_on`/`status_on` methods, all public. It does not cover a CONTRADICTORY session state, beyond `complete_kwh` being null.
- Snapshot money for EV takes the stored consequence amount. A currency mix across windows gives null.

## User-review focus

- None in this slice: no screen reads the snapshots until CH-5a.
- The owner-facing effect of the grades (PARTIAL Kobo, LOW Cold and EV, until DD-1) is as §5c states.

## Fix round 1 (review REVISE + rulings CH1a-R; commit `6e708c713` plus this packet commit)

- **H1 fixed.** `test_w205a_ev_migration.py` now compares index NAMES: after the downgrade to 0023 the set difference is exactly `{accepted_evidence_ev_measurement, accepted_evidence_site_role_time}` and nothing new appears. File passes.
- **M1 fixed (with the Architect's extension, sheet §4.1 `input_fp(ids, pending, ...)`).**
  - `pending` is in the fingerprint (the grade is not).
  - `selected_windows` now returns `(start, end, run_id)` (port, Postgres adapter, `latest_disjoint`). The fingerprint ids gain `run:<assessment run id>` for `chamber_temp_c`, `backup_start_chain` and `charging_kwh`, and `selection:<run id>` for `avoidable_gen_min`. `noon_headroom_kw` already names the `mini_depth_revision` id (`revision:`).
  - New `backend/tests/test_ch1a_reassessment.py` (11 tests): per measure (5), a re-assessment over the same evidence ids appends revision 2 and an unchanged rebuild writes nothing; per measure (5), PENDING then completed with the same ids appends revision 2 with a non-PENDING grade; plus the Cold `basis` value.
  - Non-vacuity: removing `pending` from the fingerprint fails the 5 PENDING tests; removing the run/selection/revision ids fails the 5 re-assessment tests. Both reverted (`git status` clean).
- **L1.** Cold has 64 rows (2 measures x 33 days minus 2). 1 Oct has no subjects for either measure: the only Foundation revision starts 2026-10-01 00:00 UTC and the Addis day starts 2026-09-30 21:00 UTC, so no component is in force at the period start and the reader counts the day NO_DATA.
- **L4.** `unknown_meter_seconds` removed from `ev_window` (D4: unknown seconds are excluded from both sets by construction).
- **D6 (CH1a-R).** One helper, `pg_harness.alembic_head()`, reads the sole Alembic head from the scripts. All 24 files (23 tests plus `mini_depth_probe.py`) import it instead of the literal, so the next migration touches none of them. The 0041 test keeps its own `THIS` revision.
- **D3 (chamber coverage).** The assessment's gap rule (`cold._gaps`: expected instants at the policy cadence, bridge up to 10 min) exists only inside an assessed window and needs the policy; applying it over the 24 h day would be new analytic code. So coverage stays on the **assessed-window basis** and the value carries `basis: "assessed_window"`. Clone finding: accepted `chamber_temperature` readings exist only in a one-hour slot per story day (24 Oct 13 readings, 28 Oct 7, 31 Oct 13, all 16:00-17:00 UTC), not for about 23 h. So the clone case is "readings only in the window", which is LOW either way; a 24 h reading-based count would not change today's grades. (24 Oct has readings but no selected assessment, so it is NO_DATA.)
- **D2 (backup).** Window basis accepted; value carries `basis: "assessed_window"`.
- **D1.** The corrected §5 row for Cold 28 Oct `chamber_temp_c` is **LOW 2100 s, peak 4.8** (confirmed again on the fresh clone).
- **D7.** Budget is now <= 100 ms per measure-day. Measured on the fresh clone (build / rebuild): Kobo 69.3 / 62.1 ms, Cold 37.3 / 35.0 ms, EV 27.4 / 22.9 ms. Within budget (the reviewer's 114 ms was a noisier run; no optimisation).
- **Fresh clone `assetops_chainclone_fx1a_test`** (from polish, migrated, built 2026-10-01..11-02): 97 / 64 / 33 rows; rebuild wrote 0. Value table as above, unchanged: Kobo 30 Oct 168.333 kWh / 42.08 USD, 31 Oct 0.000 / 0.00; noon 31 Oct COMPLETE 25-31; avoidable 31 Oct 200/30; EV 27 Oct LOW 15.000 kWh / 4.50 USD, 20 Oct 30.000 / 9.00, 26 Oct NOT_EXPECTED; Cold 28 Oct backup LOW 3900 `{starts 1, failed 1}`, chamber LOW 2100 peak 4.8; Cold 31 Oct chamber LOW 3900 peak 4.9. Grades: Kobo 8 COMPLETE (noon), 16 PARTIAL, 73 NO_DATA; Cold 6 LOW, 58 NO_DATA; EV 2 LOW, 2 NO_DATA, 29 NOT_EXPECTED. Coherence without `--known-at` against `expected-today.json`: 56 requests all 200, every rule 0 new, self-check 39 pass 0 fail. Clone dropped.
- **Tests (host Postgres, `run-host-tests.ps1`, no skips):**
  - All 25 changed files plus the new tests, in chunks: 60 passed (154 s), 80 (249 s), 69 (487 s), 45 (475 s), 35 (726 s: over the 600 s chunk cap for four files; completed, not killed). Total 289 passed, 0 failed.
  - L0 `test_ch1a_grading` + `test_ch1a_reassessment`: 36 passed; L2 `test_ch1a_snapshot_postgres` inside the first chunk.
  - Board / scoped set (`test_w301_estate_coverage`, `test_cov_partial_portfolio`, `test_w402_rules/projection/reads/inputs_postgres`, `test_walk1_productive_sales`, `test_out_b2_mini`, `test_s3_dispatch_read_postgres`, `test_out_b1_board`, `test_out_b4_board_postgres`): 149 passed (208 s).
  - Architecture check passed; agent-workflow check passed; estate guard self-tests 7 passed (362 s).
- **Not run:** full backend suite, vitest (not in this fix round's brief).
- **Open for the Architect:** L2 (subject-less non-operating days count NO_DATA for ASSET measures) and L3 (Cold measures take Site-wide readings, not filtered by asset) remain latent v1 limits, for CH-1b.
