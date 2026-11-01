# POLISH PA-1 review packet: board truth

Task: `tasks/POLISH-PA-1-board-truth.md`. Branch `task/POLISH-PA-1-board-truth` from main `83918ac00`.
Contract: `.agent/build-sheet-POLISH.md` §1.1 (backend), §1.3 (connector copy), §1.6, §1.7, §5 PA-1, §6 D-2, §7,
Addendum 2 (pre-flight rulings) and Addendum 3 (captures). USER_REVIEW_REQUIRED: no (merge on review ACCEPT).

## Outcome delivered

| Diagnosis | Change |
|---|---|
| P-06 / R626 (§1.1) | `mini.py`: `COST_MONEY` "possible extra fuel cost on this day", `COST_NO_MONEY` "No fuel cost estimated for this day". PRICED with `Decimal(amount_high) == 0` gives `COST_ZERO` "No fuel cost estimated: the generator was on but delivered no measured power" and `headline_money[COST] = None`. `amount_low` is not tested. No idle-fuel model (owner Q1). |
| P-11 (§1.6, R635) | `board.py` `_row`: (EV, OPTIMIZE_COST) uses `catalogue.ROW_NOT_MEASURED_EV_COST_UNPRICED` "Energy cost per km needs odometer readings and a published charging tariff" unless `facts.headline_money["GROW_REVENUE"]` is set. EV-2 `missing_records` is unchanged (Addendum 2 Q-C: nothing renders it). |
| P-12 (§1.7) | `mini.no_run_day`: MG-7 settles when `base`, `assessment.claim_level == "COMPLETE"`, no `assessment.dispatch_intervals`, and readiness exactly `UNKNOWN`. The Assure chip then follows `outcome_state` ("No objective declared"); the Readings line is `NO_RUN_READINGS`. `claim_limit_read.reduce_day` unchanged. |
| P-12 Grow pre-flight (R636) | Grow is Unknown on S and S+1 because MG-1 cannot be judged without sales records (`mini.py` `mini_readings`, OBJECTIVE_NOT_JUDGED). Different cause; not changed. |
| §1.3 connector copy | `ev.py`: `Option(f"Investigate {connector_name(label)}", ...)` reads "Investigate Connector c1". |
| §6 D-2 (OUT-E L4) | `board.cost_line`: MODELLED_IMPROVEMENT with `verification_state != "VERIFIED"` returns `COST_NOT_CREDITED` "The trial did not fix the problem, so no cost change is credited to it". |
| OUT-E L3 (Addendum 2 Q-A) | `postgres_trial_comparison_store.history()`: `ORDER BY recorded_at, revision_no, id`. |

## Files materially changed

- `backend/assetops_backend/site_outcomes/{mini,board,ev}.py`, `outcomes/catalogue.py`,
  `financials/adapters/postgres_trial_comparison_store.py`.
- Tests: new `backend/tests/test_polish_pa1_board_truth.py` (8 pure compose/read tests),
  new `backend/tests/test_polish_pa1_trial_history_postgres.py`; pinned-string updates in `test_out_b2_mini.py`,
  `test_out_b3_cold_ev.py`, `test_out_a1_outcome_map.py` (vocabulary scan includes the new constant).
- Records: `.agent/mock-departure-register.md` (R635, R636 added; R626 backend part closed, closes with PB-2),
  `.ai/CODE_STATE.md` ("POLISH PA-1"), task file.

## Acceptance criteria

1. P-06 zero headline, copy, no money: **met**, `test_zero_priced_amount_reads_no_fuel_cost_estimated_without_money`,
   `test_non_zero_priced_amount_keeps_money_and_day_wording`, `test_unpriced_amount_reads_no_fuel_cost_for_this_day`.
2. P-11 conditional EV sentence: **met**, `test_ev_optimize_sentence_needs_a_priced_tariff` (both branches).
3. P-12 MG-7 settled: **met**, `test_complete_zero_interval_day_settles_mg7_with_unknown_readiness` (outcome
   NO_OBJECTIVE, row `state_label` "No objective declared", exact Readings text); `test_no_run_rule_is_narrow`
   (one interval, LIMITED claim, stale, readiness None all stay UNKNOWN; FULL readiness keeps the old line).
   Readings wording deviates, see below.
4. Connector wording: **met**, `test_out_b3_cold_ev.py` option assertion "Investigate Connector C2".
5. COST_NOT_CREDITED: **met**, `test_modelled_improvement_is_credited_only_to_a_verified_trial`.
6. History order: **met**, `test_history_orders_by_time_then_revision_across_two_outcomes` (two outcomes, one
   Action, interleaved times, a same-time pair whose uuid order is the reverse of revision order).
7. Captures: **deferred to PA-3 (Addendum 3)**. Not run; serve was not started.
8. Register and guards: R635/R636 added; check-all result below.

Non-vacuity: with the pre-slice `mini.py`, `board.py` and `catalogue.py` restored from `83918ac00`, the new pure
file fails 7 of 8 (restored afterwards with `git checkout HEAD`). The history test's same-time pair has
ids in reverse revision order, so the old `ORDER BY recorded_at, id` yields `(o1,2)` before `(o1,1)`; that
mutation was not separately executed against Postgres.

## Checks run (revision `68823980a` code; later commits are a test assertion and records)

- Pure scoped: `pytest backend/tests --ignore-glob="*_postgres.py" --ignore=backend/tests/test_w502_domain_intent_api.py
  -k "board or outcome or mini or ev_site or polish or out_e or vocabulary"`: **450 passed, 3 skipped**, 12 s.
  (`test_w502_domain_intent_api.py` fails to collect without `ASSETOPS_TEST_DATABASE_URL` - `NameError: COLD`
  from its URL-gated import; pre-existing and untouched, so ignored here.)
- Postgres scoped via `tools\run-host-tests.ps1` (default `assetops_test` base, run-owned DBs):
  `test_polish_pa1_trial_history_postgres.py test_out_e3_trial_comparison_postgres.py
  test_out_e4_readback_postgres.py test_out_b4_board_postgres.py test_w207_ev_site_reads_postgres.py`:
  **30 passed**, 810.9 s.
- `tools\check-all.ps1 -Python ...plan2\.venv\Scripts\python.exe` at `ddf5b7537`: **All 11 guards passed** (11/11; PB-0 not yet merged).
- `-Tier all`: not run (no schema or plumbing touched; the sheet does not ask for it).
- Frontend: not touched; no vitest run.

## Known deviations

- **Readings line wording (§1.7, Addendum 2).** The ruled text "No generator run to check on this day · readings
  complete" fails the product vocabulary guard (`frontend/src/test/productVocabulary.json` bans "run" and "running";
  `test_out_b2_vocabulary.py` failed on it). The guard was not loosened. Shipped:
  **"Generator not used on this day, so nothing to check · readings complete"**. Architect to confirm or re-word.
  Note for PA-2: §3 Finding titles "Generator may have run longer than needed" and "... extra generator running ..."
  will hit the same guard.
- Read-only pre-flight: the board/overview of the kept DB was read in process with
  `default_transaction_read_only=on` and the kept build's own tree code; no file under the private tree changed.

## Residual risk

- On S+1 the Readings contributor keeps the readiness chip, which reads "Unknown" beside "readings complete"
  (the sheet does not rule the chip).
- `COST_NOT_CREDITED` ("did not fix the problem") also applies to INCONCLUSIVE/PENDING with a modelled improvement,
  as the sheet states it; those states cannot normally carry MODELLED_IMPROVEMENT.
- Frontend fixtures (`frontend/src/test/outcomeBoardFixture.ts`, `outcomeBoard.test.tsx`) still carry the old
  "exposure in this hour" headline; Lane B (PB-2) owns them.
- Screen proof waits for PA-3's "PA-1/PA-2 screen check".

## User-review focus

Readings wording deviation; the zero-cost headline as the honest Q1 answer.
