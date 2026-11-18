# Review: FUEL-1 A2, trial-fuel-comparison/2, priced total, no-sum credit

- Reviewer: fresh Claude reviewer (did not author the slice).
- Branch `task/FUEL-A2-trial-fuel-comparison`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-a2`. Diff reviewed: `git diff 826d91572...HEAD` (head `94001adfa`; code at `7a390ea66`, then packet-only commits).
- Spec: `.agent/build-sheet-FUEL-1.md` §4.2 with §1; `.agent/review-A1.md` L1/L2; owner `.agent/owner-fuel-scope-2026-11-07.md`.

## Verdict: FIX

One High: A2 adds two **new** Postgres test failures that pass on unchanged main code. The fix is mechanical: regenerate two read-body fixtures and check the diff. The maths, the reason precedence, the `/1` byte-equality, the no-sum credit and the A1 L1/L2 closures are correct. After H1 is fixed and the two files rerun green, this can merge. The Lows do not block.

## Findings

### H1 (High, new regression): two read-body goldens now fail

- **Where:** `backend/assetops_backend/actions/verification_rules.py:540` adds `generator_idle_seconds` to every window. `evidence()` (`verification.py:696`, `"windows": _wire(windows)`) returns whole windows, so the key reaches the public evidence body. `_cost_check_read` (`verification.py:1210`) adds `priced_total` to the `verification.cost_check` read body.
- **Failing tests:**
  - `backend/tests/test_ch9b2_reserve_byte_equal_postgres.py::test_reserve_trial_bodies_and_rows_are_byte_equal`: `differences(got, want)` returns `['bodies.action', 'bodies.evidence']`. The golden is `fixtures/ch9b2_reserve_trial_golden.json`, which pins `generator_kwh` at `:2923` and `:4328`, with no idle key.
  - `backend/tests/test_s6_verification_evaluator_postgres.py::TestResolutionAndHolds::test_verified_resolves_then_late_evidence_withdraws_and_overlap_blocks`: `check_contract` `_shape` mismatch at `:583`. The fixture `fixtures/s6_verification_api_contract.json` has windows without the idle key, and `cost_check` at `:1844` has no `priced_total`.
- **Proof the failures are A2's:**
  - On the A2 worktree, both fail: 2 failed, 110 s.
  - The same two tests pass on the plan2 checkout (main `e6e3bedd1`), whose `backend/` and `frontend/src` equal `826d91572`, against the same base `assetops_a2_test`: 2 passed, 84 s.
- **Why it matters:** the merge puts two red tests on main. They would surface in E2's full suite as unexplained failures, mixed into the five pre-existing ones. The packet's "Adjacent" run covered only non-Postgres files, so it could not see these. OUT-E E3 had the same situation for `generator_kwh` and fixed it in `dabcbe6ab` ("S6 contract fixture gains generator_kwh, cost_check, trial_hours only").
- **Fix (test fixtures only):**
  1. Regenerate the CH-9b2 golden with `CH9B2_CAPTURE=1` and the S6 contract with `ASSETOPS_WRITE_S6_VERIFICATION_CONTRACT=1`, on `assetops_a2_test`.
  2. Confirm `git diff` on the two JSON files adds only `generator_idle_seconds` per window (evidence bodies) and `priced_total: null` (cost-check read bodies), and nothing else.
  3. Rerun both tests green. Note the refresh in the packet, because the CH-9b2 docstring says the golden was captured from unchanged 0051 code.
- **Alternative (Architect's call):** keep the evidence API unchanged by stripping the key in `evidence()`. I do not recommend it, because `generator_kwh` is already exposed there.

### L1 (Low, spec gap; Architect or A3): a MODELLED_IMPROVEMENT can store a negative `priced_total`

- **Where:** `trial_fuel_comparison.py:195-200`.
- **The gap:** the state comes from the per-demand-kWh change. The priced total is the absolute cost difference.
- **Example inside the 10% demand band:**
  - baseline: 10 kWh generator, 0 s idle, 100 kWh demand;
  - later: 10 kWh generator, 300 s idle, 110 kWh demand;
  - r = 3.3 L/h, price 1.25 USD/L.
- **Result (reproduced with `test_tfc2` helpers):** `MODELLED_IMPROVEMENT`, `change_per_demand_kwh.nominal = 1/3520`, `priced_total = {amount: "-0.34375", fuel_change_l: "-0.275", ...}`.
- **What contains it, and where it leaks:** `credit.credited` refuses it (`amount <= 0`), so the Portfolio is safe. But the row is stored append-only and is exposed by `_cost_check_read`. A3's planned `COST_PRICED` ("about {l} L less diesel in the trial hour") would then read "about -0.3 L less diesel".
- **Not reached on Kobo:** the baseline is all idle and the later hour has no idle.
- **Fix, one of:**
  - add `priced_total` only when `amount > 0` (a one-line condition plus one test here);
  - or A3 guards its copy on a positive amount.
- The sheet text literally says "on MODELLED_IMPROVEMENT", so this needs an Architect ruling, not a builder change.

### L2 (Low, test gap): the `/2` path through the real hook and store is unproven (packet R1)

- **What is untested:**
  - `PostgresActionStore.no_load_history` (`postgres_action_store.py:637`) has no Postgres test with a declared rate;
  - no test asserts `_cost_check_read`'s `priced_total` is passed through (the regenerated S6 fixture will pin only its null shape).
- **Mitigation:** the store helper is the SFC path with the field, unit and constructor parameterised, and the SFC path stays green in `test_out_e3`. `NO_LOAD_FIELD` matches A1's vocabulary key (`sites/models.py:275`).
- **Failure scenario:** a wrong unit or field literal makes every Kobo trial silently stay `/1`, with no priced total. A3's scratch prepare would be the first place it shows.
- **Fix:** A3's prepare must assert `formula == "trial-fuel-comparison/2"` on the stored ACT-001 cost check. A3 already plans this check through its PROBE_CHOSEN finish row. Optionally, add one L2 case to `test_out_e3` with a declared rate.

### L3 (Low, stale comment): the estate port docstring says no priced total is stored

- **Where:** `estate/adapters/postgres_estate_read.py:367-369` still says "no priced total is stored, so the money rule credits nothing".
- **The true reason now:** `/2` rows do store one; the port simply does not read it (packet R2).
- **Fix:** reword it now, or leave it to PV-1, which owns this area.

### L4 (Preference): D1 wording

- **Current text:** `board.py:90`, "the generator's idle time is not known for both hours". It can be read as "known for neither".
- **Suggestion:** "the generator's idle time is not known for one of the hours".
- `NO_LOAD_RATE_DIFFERS`'s text is plain and fine.

## Review focus answers

1. **Fuel maths and precedence.** Correct.
   - **Idle seconds:** `generator_idle_seconds` adds 300 s for a slot only when its state is in `RUNNING_STATES` and its slot kWh `== 0`. It is None if any slot's state or kWh is unknown. This is stricter than the sheet, but harmless: an unknown state already makes the window incomplete (`known &= gen_value is not None`), so `WINDOW_INCOMPLETE` or `GENERATOR_KWH_UNKNOWN` fire first.
   - **Version selection:** `/2` needs `no_load_for` to give exactly one positive rate for each window. `test_v1_byte_equal_...` covers no rate, a rate on one window only, a rate of 0, and a duplicate rate.
   - **`/1` byte-equality:** `_window` adds `idle_seconds` and the basis idle keys only under `v2`, and the `_fuel`/`_cost` scratch keys are deleted. So `/1` keys, values and digest are equal; the test compares whole dicts.
   - **`priced_total`:** amount = baseline nominal cost minus later nominal cost. Both use the same price revision, guaranteed by `PRICE_BASIS_DIFFERS`. Demo figures: 3.3 L, 4.125 USD, 0.275 USD/kWh, computed from the inputs.
   - **Digest (D4):** it covers the idle seconds and r per window, and `test_digest_covers_the_idle_inputs` bites. `priced_total` is derived from digested inputs.
2. **No-sum credit.** Correct.
   - `recovered_value` gives one item per credited result, never sums, raises on a repeated or missing key, and keeps input order.
   - **`amounts` grep (backend, frontend, tools, contracts, fixtures):** the only readers were `estateClient.ts`, `test_ch3_rows.py` and `test_w303_portfolio_api.py`, all renamed. `portfolioFixtures.ts` holds `null`. The other `amounts` hits (`chain/vocabulary.py:426`, `chain_coherence.py:1193`, `s404-finding-index-evidence.mjs`) are unrelated locals. `test_w303_portfolio_*_postgres` read only `state`.
   - **The no-sum test:** checks every numeric leaf against the sum, so it fails if anything is summed.
3. **D1 and the other decisions.**
   - **D1 (board words):** acceptable. `test_out_e4_readback` pins `set(COST_REASON_WORDS) == set(REASSESSMENT_REASONS)`, so A2 cannot avoid it. Two dict lines merge trivially with MB-1. The wording is plain (see L4).
   - **D2 (`priced_total` on `/2` only):** right. Adding it to `/1` would break byte-equality and start crediting old rows.
   - **D3 (selection read literally):** right, and fail-safe to `/1`.
   - **D5 (declared basis not in the trial result):** acceptable for A2. A3 should take the "generic" label from the Foundation revision in force over the trial windows, not the current revision. The owner requires the 3.3 L/h rate to be labelled generic, and the trial digest does not carry the basis.
4. **A1 L1/L2.**
   - **L1 closed:** `test_stored_fuel_cost_2_head_reads_current` covers both `read` and `select_consequence_on`, and the packet records the non-vacuity revert.
   - **L2's first two gaps closed:** the basis outside the three, and the loaded reading on a non-declaring revision. Both tests are exact.
   - **L2's third gap (bridge and overview label naming fuel-cost-2):** it need not be closed before A2 merges. It is A1 display code that A2 does not touch, and it becomes visible only in A3. Close it in A3, which makes those labels visible.
5. **Do the tests bite?** Yes for the maths, reasons, precedence, the `/1` equality, the digest and the credit. The gaps are L2 and the H1 goldens, which the builder never ran.
6. **Regression risk.**
   - **Existing trial results:** stay `/1` (`test_out_e3` asserts `/1` and no `priced_total`).
   - **Kobo boards:** unchanged until A3 declares the rate. Then ACT-001 becomes `/2`, and the board's per-kWh `COST_CHANGE` line changes value, because idle fuel enters the per-kWh rate. A3 owns that copy.
   - **Portfolio:** inert. The estate `cost_checks` port reads `{state, currency}` only (R2), so it still reads NOT_CREDITED and §1.3's forecast "no clause" gap does not occur.
   - **R3:** the raise on a duplicate outcome id is unreachable while R2 holds. PV-1 should keep it in mind if it reads priced totals.
7. **Pre-existing failures.** Confirmed: on the branch, the same five fail, and on plan2 main they fail identically. A2 adds no new L0 failure; its two new failures are the Postgres ones in H1. The five are:
   - `test_ch5a1_scope::test_window_memo_excludes_knowledge_at_only_without_a_cutoff`;
   - `test_ch5a2_contract::test_chain_body_equals_its_golden[estate_week_2026-10-25]`;
   - `test_ch5c2_clock_guard` x2;
   - `test_out_d2_objectives::test_policy_is_v2`.

## Checks I ran

- **Interpreter.** plan2 venv, with PYTHONPATH pinned to the worktree. `assetops_backend.__file__` resolves to `C:\Users\assef\Bineyame\AssetOpsV1-a2\backend\assetops_backend\__init__.py`.
- **Touched and adjacent L0.** `test_tfc2 test_out_e2_trial_comparison test_ch3_rows test_out_e4_readback test_s6_verification_rules test_s6_verification_verdict test_w303_portfolio_api test_out_d4_board test_ch6b2_portfolio_cards test_fuel_cost_v2 test_out_a1_outcome_map test_out_b2_vocabulary`: 267 passed, 1 skipped (the w303 Postgres case; no URL set), 13.5 s.
- **Pre-existing failures.** `test_ch5a1_scope test_ch5a2_contract test_ch5c2_clock_guard test_out_d2_objectives test_out_e4_readback test_ch6b2_portfolio_cards`: branch 5 failed / 142 passed; plan2 main the same 5 failed / 140 passed.
- **Postgres, own base `assetops_a2_test` (harness clones), 4.1 GB free RAM beforehand.** The two H1 tests:
  - branch: 2 failed (110 s); CH-9b2 rerun alone shows `['bodies.action', 'bodies.evidence']`;
  - main code: 2 passed (84 s).
- **Frontend.** `npx.cmd tsc --noEmit -p .` in `frontend/`: exit 0. No frontend test file was touched, so vitest was not run.
- **Read, not rerun:** the builder's `test_fuel_cost_v2_postgres` and `test_out_e3_trial_comparison_postgres` runs (12 and 4 passed at the code revision), and the guards. The packet records "Architecture check passed" and "Agent workflow check passed" at `7a390ea66`.

## Not verified

- No full suite, prepare or `test_demo_combined_postgres` was run, per the ruling.
- Other Postgres files that might pin verification read bodies were not run. I grepped the fixtures: `s6_action_api_contract.json` holds `cost_check: null` and no window bodies, so it is likely unaffected, but it is unverified. The builder should run `test_s6_action_records_postgres.py` with the H1 reruns.
- The vitest suite was not run.
