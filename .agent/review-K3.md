# Review: DIESEL-K3 fuel balance (`fuel-balance-1`, 0055, R3g, R3h)

- Reviewer: Claude Opus (independent first review; did not author the slice). 2026-11-08.
- Branch `task/DIESEL-K3-fuel-balance`, head `0ea5fcce6`, diff `git diff main...HEAD` (merge-base `cad10d20d`). Main has moved to `7ea2fada9` since; none of its new commits touch `backend/migrations`, `verification_rules.py`, `work/composition.py`, `test_tfc2.py` or rule 8, so there is no 0055 renumber or conflict.
- Judged against `.agent/build-sheet-DIESEL-1.md` §9d (R3d), §9g (R3g), §9h (R3h), §9c.3 L2, and the owner decisions (unexplained fuel, never theft; 6 pm to noon).

## Verdict: ACCEPT

There are no High or Medium findings. The two Lows below are test and documentation gaps and do not block the merge.

## Findings

### L1 (Low, test gap): no test pins STARTING or FAILED as a stop marker
- `backend/assetops_backend/actions/verification_rules.py:375` sets `NOT_RUNNING_STATES = {"STOPPED", "STARTING", "FAILED"}`. Every R3h test uses `STOPPED` as the end sample (`backend/tests/test_tfc2.py:172-185`, `test_k3_fuel_balance_rules.py:177-185`, `:246-249`).
- I applied §9h.5's second mutation (`NOT_RUNNING_STATES = {"STOPPED"}`) to a scratch copy: all 29 tfc2 and K3 L0 tests still pass.
- §9h.5 asks only that the non-GOOD case still passes under this mutation, and it does, so this is not an acceptance gap.
- Failure scenario: a later edit narrows the set to `{"STOPPED"}`. A generator that trips (RUNNING at `t`, 0 kWh, FAILED at `t + 5`) would again score its stop slot as 300 s of idle fuel in A2 and in the fuel balance, and no test would catch it.
- Fix: one extra assertion in `test_window_idle_seconds_exclude_the_stop_slot` with a FAILED (or STARTING) sample at the window end, expecting 3300.

### L2 (Low, documentation): stale docstrings in `fuel_balance/rules.py`
- `rules.py:9-10` says the slot helpers are "imported by name and never edited". After R3h, `verification_rules.py` is edited and the idle test is the shared `idle_slot`.
- `rules.py:174` (the `use_from_readings` docstring) runs past the file's line width.
- Failure scenario: none at runtime. A future reader, K6 for example, may believe `verification_rules.py` is still unedited and miss R3h when it merges main before its own edit.
- Fix: reword `rules.py:9-10` to name `idle_slot` and R3h, and wrap line 174.

## Checks against the dispatch

1. **Calculation.**
   - **Parameters:** `PARAMETERS` minus `parameter_version` is byte-equal to `tools/probe_kisiwa_fuel.py:80-94`. `diff` of the source lines shows only the added `parameter_version` line. The dict also equals `probe-result.json` `assumptions.fuel_balance_1` and `f0.PARAMETERS`, with the same key order.
   - **Use source:** use comes only from accepted generator readings, via `_power_slot`, `_instant` and `idle_slot` (`rules.py:171-201`).
   - **Idle term:** it uses the Site's declared rate, `no_load.value` (`rules.py:300`, `:221`). The rate needs a recognised basis on the rate's own revision (`service.py:93-99`).
   - **Band:** the band and its evaluation order are F0's (`rules.py:214-235`).
   - **Reasons:** the eight reasons follow §9d.2's precedence through `model.REASONS` (`rules.py:302-306`).
   - **Gaps:** gap spans are stored, for NOT_ASSESSED windows too.
   - **No run or trajectory reads:** no module under `fuel_balance/` imports a run, the simulator, `host` or `tools`, or contains "trajectory". A6's static test covers this, and I confirmed it by grep.
2. **Shared slot rule (R3h).**
   - **Scope:** `idle_slot` (`verification_rules.py:378-385`) removes a slot only when the accepted end sample is a not-running state. `_instant` returns None for a missing, conflicting or non-GOOD sample, so those cases keep the slot idle.
   - **Byte-equality:** the lookahead's payload is discarded, so window evidence ids, problems, `plan_sha256` and the details are unchanged. The golden files are untouched, and the Postgres byte-equality tests pass (below).
   - **Kobo impact:** the statement is consistent with `.agent/fuel-story-design-2026-11-07.md:66,137`. The trial hour 09:00-10:00 local sits inside the 07:05-10:55 idle run, and the later hour has no run, so neither window contains a stop. fuel-cost-2 does not call `idle_slot`: grep finds only `window_evidence` and `fuel_balance/rules.py` as callers. I could not check the demo database's money directly. `test_out_e3_trial_comparison_postgres.py` passing is the backstop.
   - **Spec deviation (tfc2 fourth case): sound.**
     - §9h's case ("RUNNING at 0-5, then a non-GOOD sample at slot 6 gives 1800") is unattainable. A non-GOOD sample at slot 6's own instant makes slot 6's state UNKNOWN, so `generator_idle_seconds` becomes None. A non-GOOD sample makes `_instant` UNKNOWN even when a GOOD sample is also present.
     - The window end is the only instant where a non-GOOD sample can be a slot's end sample without being some slot's own state.
     - The builder's case (RUNNING 0-11, a SUSPECT STOPPED at `T0 + 60 min`, expecting 3600) tests exactly §9h's intent: only a positive, accepted stop marker removes a slot. It kills an implementation that ignores quality, which would give 3300, and it kills the inverted lookahead.
     - Like the spec's own third and fourth cases, it does not on its own kill the deletion of the lookahead. The test function does, through its first two cases.
3. **Migration 0055.**
   - **Schema:** columns, constraints, index and trigger match §9d.4 exactly. `test_b1_migration_up_down_up_on_empty_table` passes, and so does the downgrade refused with a row.
   - **Revisions:** a revision is appended only when `input_sha256` differs (`service.py:106-107`), with `recorded_at = known_at` (`postgres_fuel_balance_store.py:146`).
   - **Clock:** CLOCK_BACKWARDS keeps `recorded_at` monotone in `revision`.
4. **Read port.**
   - `windows()` returns, per night, `DISTINCT ON (night_date)` the latest revision with `recorded_at <= known_at` (`:219-223`). This is as-known correct, given the monotone `recorded_at` above.
   - `window()` returns a fixed revision by id, scoped to tenant and Site.
   - Both reads run `REPEATABLE READ READ ONLY`. B6 and the parity "as known" test cover both.
5. **Must-fail tests.** I re-ran nine mutations on scratch copies (`%TEMP%\...\scratchpad\mut`); no repo file was edited.
   - Dropping the idle term: A3 fails.
   - `<=` to `<` in WITHIN_MARGIN: A4 fails.
   - Dropping `+ D_tol` from the high edge: A5 and A2 fail.
   - Deleting the lookahead: A3, A14, the A6 parity test and the new tfc2 test fail.
   - Inverting the lookahead: six tests fail.
   - `NOT_RUNNING_STATES = {"STOPPED"}`: everything passes, as §9h.5 requires (see L1).
   - K2 L1 on `postgres_fuel_records.py:33`, against `assetops_k3_test`:
     - root kind only: B4 fails;
     - root tank only: B3 and B4 fail;
     - both: B2, B3 and B4 fail. B2 fails on a `TypeError`, still a failure.
   - This matches §9d.6 B's mapping.
   - **Cross-kind lateness:** B4 pins it both ways. A record retyped late but first recorded on time gets no `DELIVERY_RECORDED_LATE`. A FUEL_DELIVERY first recorded at `end + 31 min` is flagged.
6. **Parity.**
   - **F0 ten-night unit parity:** `test_a2_rule_parity_all_ten_nights` passes. It is exact on the readings and true-tank terms.
   - **Kisiwa L2 (part C): not re-run by me.** It takes about 19 minutes. I cite the packet: 6 passed in 1117.43 s on `assetops_k3_test`, nights 2, 4 and 6, with `idle_seconds == 0`. The packet's evidence predates only the packet-only commit `0ea5fcce6`, so it covers the code under review.
   - I read the test. Its exact and toleranced items, the 1/100000 L tolerance, the night-4 spans, the as-known revisions and the CLI REUSED step match §9d.6 C. It builds its store through `build_fuel_balance_store`, as R3g requires.
7. **S4 exceptions and other edits.**
   - **`work/composition.py`:** the edit is exactly §9g.2, `build_fuel_records_reader` with a lazy import and an `__all__` entry. A13a, A13b and A13c pass.
   - **K2 head-agnostic edit:** I re-read it. It still asserts a single head and 0054's `down_revision`, and K2's Postgres tests pass.
   - **Rule-8 reorder:** list membership is unchanged; only the order moves.
   - **Rule-8 domain and writer:** the fuel-balance domain and writer entries are insert-only and anti-vacuity, mirroring the trial-comparison writer.
8. **Wording.** No added line contains theft, stolen, stole, siphon or pilfer. The search ran over `git diff main...HEAD`, excluding `.agent`. K3 adds no client-visible text.
9. **Process deviation.** The builder used `Set-Content` on a repo file for a mutation proof and then restored it. I note it and do not block on it. The worktree is clean at head.

## Checks run (what I saw)

- **Imports:** they resolve into the k3 worktree (`rules.py`, `verification_rules.py` and `probe_kisiwa_fuel.py` paths printed).
- **Non-DB tests:** `test_k3_fuel_balance_rules.py`, `test_tfc2.py`, `test_s6_verification_rules.py`, `test_s6_verification_verdict.py`, `test_k2_fuel_records.py` and `test_fuel_cost_v2.py` gave 129 passed in 7.81 s.
- **Postgres tests** (`assetops_k3_test`; 3.29 GB free RAM checked first):
  - `test_k3_fuel_balance_postgres.py` and `test_k2_fuel_records_postgres.py`: 18 passed in 32.25 s;
  - `test_ch9b2_reserve_byte_equal_postgres.py`, `test_s6_verification_evaluator_postgres.py` and `test_out_e3_trial_comparison_postgres.py`: 18 passed in 417.74 s.
- **Guards** (run directly, no `-ExecutionPolicy`, `ASSETOPS_GUARD_PYTHON` set to the plan2 venv): `tools\check-architecture.ps1` printed "Architecture check passed." and `tools\check-agent-workflow.ps1` printed "Agent workflow check passed."
- **Not run:** the full suite (not in scope), `check-all.ps1` (I cite the packet's "All 17 guards passed"), part C parity (cited above) and both probe `--check`s (cited from the packet).

## Residual risk (beyond the packet)

- **As-known reads:**
  - `known_at` is taken at transaction start. Readings, SFC and the rate are read on the Action store's own connections, so evidence decided before `known_at` but committed after the read can be missed. A later re-assess picks it up as a new revision, since rows are append-only, so the error heals itself.
  - Assets and timezone are read as they are now, not as known at `known_at`.
  - Both are invisible on the prepared demo database, which uses virtual clocks.
- **Head assertion:** K3's `test_b1_single_alembic_head` hard-codes 0055 as head. K4's 0056 must make the same head-agnostic edit that K3 made to K2, which is the precedent.
