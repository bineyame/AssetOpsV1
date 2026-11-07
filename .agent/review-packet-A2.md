# Review packet: FUEL-1 A2, trial-fuel-comparison/2, priced total, no-sum credit

- Spec: `.agent/build-sheet-FUEL-1.md` §4.2 (with §1); owner decisions `.agent/owner-fuel-scope-2026-11-07.md`, `.agent/owner-kisiwa-scope-2026-11-07.md` (never a combined savings total; fuel and mill money never added). A1 review `.agent/review-A1.md` L1 and L2 closed here.
- Branch `task/FUEL-A2-trial-fuel-comparison`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-a2`, cut from main `826d91572` (main has since moved to `a5fd09971`, one `.agent` doc only, no overlap).
- Builder: Claude (Opus). No migration (0053 from A1 already carries `/2` and both reasons).
- USER_REVIEW_REQUIRED: no (nothing visible; A3 makes it visible). One Architect confirmation is asked (D1 below).

## Outcome delivered

- **Window idle seconds** (`verification_rules.window_evidence`): `generator_idle_seconds` = 300 s per slot whose sampled `generator_state` is `RUNNING` and whose slot generator kWh is exactly 0; None if any slot's state or generator kWh is unknown. It is a top-level window key like `generator_kwh`, so the stored `details` keep-list (`verification.py:770`) and the attribution keep-list exclude it, and plan content never holds window totals. `RUNNING_STATES` is a local constant (the module stays import-free) mirroring `analytics/dispatch.py:97`.
- **`trial-fuel-comparison/2`** (`financials/trial_fuel_comparison.py`): `FORMULA_V2`, `WindowFacts.idle_seconds=None`, `NoLoadValue`, `no_load_for` (`sfc_for` semantics), `compare(..., no_load_in_force=())`. `/2` iff `no_load_for` finds one positive rate for each window. Window fuel = SFC x gen kWh + r x idle s / 3600, upper x `MULTIPLIER`. Reasons `IDLE_SECONDS_UNKNOWN`, `NO_LOAD_RATE_DIFFERS` placed after `SFC_DIFFERS` and applied to `/2` only. On a `/2` MODELLED_IMPROVEMENT the result gains `priced_total = {amount, currency, basis: "TRIAL_HOUR_MODELLED_FUEL", window: [later_start, later_end], fuel_change_l}` (nominal costs and litres, baseline minus later). `LABEL` unchanged; no annualising. Without a rate over both windows the result is `/1` and byte-equal (keys, values, digest).
- **Hook and read** (`verification.py`): `_cost_check` passes the window idle seconds and `store.no_load_history(...)` (new, beside `sfc_history`, sharing one `_generator_property_history` helper in `postgres_action_store.py`; SFC behaviour unchanged). `_cost_check_read` adds `priced_total` (stored value or None).
- **No-sum credit** (`outcomes/credit.py:recovered_value`): returns `{"state": "CREDITED", "text": None, "items": [{key, currency, amount, basis}]}`, one per credited result, keyed by the cost check's `outcome_id`, never summed; raises on a repeated key or a credited check without an outcome id. `"amounts"` removed; readers renamed (`estateClient.ts`, `test_ch3_rows.py`, `test_w303_portfolio_api.py`; `portfolioFixtures.ts` holds `null`, unchanged). `estate/portfolio.recovered` stamps each check with its outcome id before the rule.
- **Demo figures, computed in `test_tfc2.py` from the inputs:** baseline 12 RUNNING slots at 0 kWh (3600 s), later 0, r 3.3, 1.25 USD/L, 15 kWh demand: `fuel_change_l` 3.3, `priced_total.amount` 4.125 (money2 4.12), per demand kWh 0.275.

## Files materially changed

| File | Change |
|---|---|
| `backend/assetops_backend/actions/verification_rules.py` | `generator_idle_seconds`, `RUNNING_STATES` |
| `backend/assetops_backend/financials/trial_fuel_comparison.py` | `/2`, reasons, `NoLoadValue`, `priced_total` |
| `backend/assetops_backend/actions/verification.py` | `_cost_check` idle + no-load history; `_cost_check_read` `priced_total` |
| `backend/assetops_backend/actions/adapters/postgres_action_store.py` | `no_load_history`, shared helper |
| `backend/assetops_backend/outcomes/credit.py` | per-result items, never summed, fail loud |
| `backend/assetops_backend/estate/portfolio.py` | `recovered` keys checks by outcome id |
| `backend/assetops_backend/site_outcomes/board.py` | two `COST_REASON_WORDS` entries (D1) |
| `frontend/src/estate/estateClient.ts` | `recovered_value.items` type |
| tests | new `test_tfc2.py`; `test_out_e2_trial_comparison.py`, `test_ch3_rows.py`, `test_w303_portfolio_api.py`, `test_fuel_cost_v2.py`, `test_fuel_cost_v2_postgres.py`, `test_out_e3_trial_comparison_postgres.py` |

## Acceptance criteria (§4.2)

| Criterion | Status | Evidence |
|---|---|---|
| Window idle seconds, None when unknown | Met | `test_tfc2.py::test_window_idle_seconds_*` |
| Same exclusion as `gen_total`; no plan digest or stored detail byte changes | Met | keep-lists unchanged; `test_out_e3_trial_comparison_postgres.py` asserts `plan_sha256` frozen == stored and `generator_idle_seconds` not in details keys (4 passed) |
| `FORMULA_V2`, `idle_seconds` default, `no_load_in_force`, v2 iff rate over both windows | Met | `test_v1_byte_equal_without_a_rate_in_force_over_both_windows` (no rate, one window only, rate 0, two rates) |
| Window fuel with idle term, upper x multiplier | Met | idle-only, loaded-only, mixed tests |
| Two reasons after `SFC_DIFFERS` | Met | `test_out_e2` isolation + precedence (13 reasons), `test_reasons_equal_the_0037_table_check_and_0053_widening` |
| `priced_total` on MODELLED_IMPROVEMENT | Met (`/2` only, see D2) | `test_idle_only_demo_figures_from_the_inputs` |
| `_cost_check` passes idle seconds and `no_load_history` | Met (code); L0 only for `/2` through the hook (R1) | |
| `_cost_check_read` additive `priced_total` | Met | |
| `COST_CHECK_SOURCE` pre-flight | No finding | Not shown anywhere: no frontend file holds it and `_cost_check_read` does not expose `intervention_cost`; stored data untouched |
| `recovered_value` never sums, `items`, fail loud, readers renamed | Met | `test_recovered_value_never_sums_two_items_in_one_currency`, `..._fails_loud_on_two_items_with_one_key` |
| Expected demo figures computed from inputs | Met | `test_tfc2.py` |
| `test_out_e*` cost-check tests green | Met | see Checks |
| A1 L1: stored fuel-cost-2 head reads CURRENT | Met | `test_fuel_cost_v2_postgres.py::test_stored_fuel_cost_2_head_reads_current` (`read` and `select_consequence_on`) |
| A1 L2: basis outside three; loaded reading on non-declaring revision | Met | `test_fuel_cost_v2.py` two new tests (bridge-label assertion not added) |

## Checks run (worktree, Python `AssetOpsV1-plan2\.venv`, `assetops_backend` resolves into `AssetOpsV1-a2`)

- Touched L0: `test_tfc2 test_out_e2_trial_comparison test_ch3_rows test_out_e4_readback test_s6_verification_rules test_s6_verification_verdict test_w303_portfolio_api test_out_d4_board test_ch6b2_portfolio_cards test_fuel_cost_v2 test_out_a1_outcome_map`: 261 passed, 1 skipped (the w303 Postgres case, no URL set in that run).
- Adjacent L0 (60 non-Postgres files: `test_out_*`, `test_s6_*`, `test_ch3*`, `test_ch5*`, `test_ch6*`, `test_w303*`, `test_fuel_cost*`, `test_s4_fuel*`, both contract files): 1263 passed, 5 failed, 1 skipped, 66 s. The 5 failures also fail on main `a5fd09971` with this branch absent (same run there: 5 failed, 66 passed): `test_ch5a1_scope::test_window_memo_excludes_knowledge_at_only_without_a_cutoff` (`prefetched` kwarg), `test_ch5a2_contract::test_chain_body_equals_its_golden[estate_week_2026-10-25]`, `test_ch5c2_clock_guard` x2 (`financials/recompute.py:214 datetime.now`, `postgres_objective_store` allowlist), `test_out_d2_objectives::test_policy_is_v2` (`outcome-status/4`). Not caused by A2.
- Postgres, own base `assetops_a2_test` (created empty; harness clones), 127.0.0.1:55432, free RAM 3.6-4.6 GB before each: `test_fuel_cost_v2_postgres.py test_out_e3_trial_comparison_postgres.py` at `a5abb3368`: 12 passed, 208 s. `test_out_e3_trial_comparison_postgres.py` re-run at `7a390ea66` after its two added asserts: 4 passed, 202 s.
- Frontend: `npm ci` then `npx tsc --noEmit -p .` in `frontend/`: exit 0 (112 s together). No frontend test touched (the only fixture holds `recovered_value: null`).
- Non-vacuity: (1) `consequence_read.select_consequence_on` reverted to `fc.quantify`/`fc.consequence` -> the L1 test fails with `STALE / TECHNICAL_INPUT_CHANGED`; restored with `git checkout`. (2) a summed field `21.125` injected into `recovered_value` -> the no-sum test fails on the sum check; restored.
- Guards at `7a390ea66`, `ASSETOPS_GUARD_PYTHON` = plan2 venv, no execution-policy override: `tools/check-architecture.ps1` "Architecture check passed." exit 0; `tools/check-agent-workflow.ps1` "Agent workflow check passed." exit 0 (381 s together).
- Not run (per ruling): full suite, prepare, baseline build, `test_demo_combined_postgres`.

## Known deviations and judgement calls

- **D1 (Architect to confirm): two board reason words.** `test_out_e4_readback` pins `set(board.COST_REASON_WORDS) == set(REASSESSMENT_REASONS)`, so the two new reasons need words in `site_outcomes/board.py` (an MB-1/A3 file, not in A2's list). Builder-proposed, vocabulary-checked: `IDLE_SECONDS_UNKNOWN` "the generator's idle time is not known for both hours"; `NO_LOAD_RATE_DIFFERS` "the generator's idle fuel rate differs between the hours". Neither is reached on Kobo (one rate, idle seconds known). Two dict lines next to `SFC_DIFFERS`; a merge with MB-1 should be trivial.
- **D2: `priced_total` only on `/2`.** The sheet lists it under the `/2` changes; adding it to `/1` would break "v1 byte-equal" and start crediting existing `/1` results.
- **D3: v2 selection read literally.** A rate in force over only one window, several rates over one window, or a rate <= 0 select `/1` (no rate "in force over both"), not a refusal.
- **D4: `/2` result shape.** For the digest to cover r and the idle seconds, a `/2` basis adds `idle_seconds` and `no_load_l_per_h` per window; a `/2` result adds `windows.*.idle_seconds` and `no_load: {value_l_per_h}` (None when the rates differ). `/1` keys are unchanged.
- **D5: the declared basis (GENERIC_DEFAULT) is not carried in the trial result.** The sheet does not ask for it; A3's "generic" label can read the Foundation (A1 property) or the Architect can add it.

## Residual risk

- **R1 (for A3):** `/2` through the real hook (`no_load_history` on Postgres, idle seconds from stored readings) is proven at L0 only; the store helper is the SFC path parameterised, and the SFC path stays green in `test_out_e3`. A3's Kobo scratch prepare is the first end-to-end run.
- **R2:** the estate `cost_checks` port (`estate/adapters/postgres_estate_read.py:366`) reads `{state, currency}` only, so `portfolio.recovered` never credits even after A2; the Assure note keeps "No money credited · modelled, not saved". This contradicts §1.3's "clause text is None while CREDITED" gap forecast, harmlessly. PV-1 reads value lines from the board, so it is unaffected; the Architect may decide whether the port should carry `priced_total` and `outcome_id`.
- **R3:** `recovered_value` raises on a repeated outcome id. The Portfolio's action rows key by `_outcome_id`; two rows naming the same credited outcome would raise. Unreachable today (R2).
- **R4:** `evidence()` (`verification.py:696`) wires whole windows, so the read-only evidence API now also shows `generator_idle_seconds`, as it already shows `generator_kwh`.

## User-review focus

None for the owner. Reviewer: D1 words and file, D3 selection, D4 digest coverage, `_reason` ordering.
