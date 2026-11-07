# Review packet: DIESEL-K3 fuel balance (fuel-balance-1)

Branch `task/DIESEL-K3-fuel-balance`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-k3`. Card: `.agent/build-sheet-DIESEL-1.md` §9d; rulings R3d, R3g (§9g), R3h (§9h).
This packet supersedes `.agent/DIESEL-K3-phase-A-handoff.md`.

## Outcome
`fuel-balance-1` night windows: rules from accepted readings (A2's slot rule, F0's band verbatim), append-only `fuel_balance_window` (migration 0055), store, read port, service, CLI, rule-8 writer membership. The Kisiwa nights 2, 4, 6 match F0 on `assetops_k3_test`, including `idle_seconds == 0`.

## Commits (oldest first)
202535b81 phase A; f864e9e1a rule-8 reorder; 7ded13f1c phase B parity test; ba8f47596 R3g composition builder + A13; 3c239ad2c parity builds store via composition; 5a8a0d6fd R3h fix round (this round).

## S4 exceptions (named, narrow)
1. **R3g (§9g), `work/composition.py`**: adds `build_fuel_records_reader()` (returns K2's `select_fuel_records`, lazy import) and its `__all__` entry, so `fuel_balance/composition.py` can wire K2's read without importing `work.adapters` (rule 1). Diff: +1 `__all__` name, +7 lines.
2. **R3h (§9h), `actions/verification_rules.py`**: `NOT_RUNNING_STATES = frozenset({"STOPPED","STARTING","FAILED"})` and `idle_slot(slot_start, state_value, slot_kwh, state_readings)` next to `RUNNING_STATES`; `window_evidence` line `elif gen_value in RUNNING_STATES and slot_gen_kwh == 0:` becomes `elif idle_slot(t, gen_value, slot_gen_kwh, state_readings):`. The look-ahead's evidence ids and problems are discarded, so window digests, stored details and goldens are byte-equal. `fuel_balance/rules.py` `use_from_readings` calls the same `idle_slot`.

Cause (R3h §9h.2): on every Kisiwa night two stop slots (19:05 and 00:15 UTC) are sampled RUNNING at `t`, 0 kW over `[t, t+5)`, STOPPED at `t+5` (phase F stops after the sample at the stop instant). Old rule scored them 2 x 300 s = 600 s idle; dispatch's `_off_after` already reads them as stopped.

## Other edits
- **K2 head-agnostic edit** (`test_k2_fuel_records_postgres.py`): the three single-head assertions compared to K2's own 0054; 0055 now follows it, so they compare to `alembic_head()`. K2's own precedent; assertions on `PREVIOUS`/down_revision kept.
- **Rule-8 reorder** (`tools/checks/configuration-persistence.ps1`): `$fuelBalanceWriter` is listed before `$trialComparisonWriter` in `$pgWriters` so the estate-guard self-test's anchor on the last writer entry is preserved. Plus fuel-balance domain, insert-only checks, ownership and anti-vacuity.

## Proofs
- **Phase A must-fail proofs**: performed by the earlier phase-A builder per §9d.6 A (each "must fail" names its killing mutation); cited, not re-run here.
- **A13** (production-path wiring, `test_a13a/b/c`): fail-before: renaming `build_fuel_records_reader` in `work/composition.py` (the pre-R3g state, no builder) makes `test_a13a`, `a13b`, `a13c` fail (ImportError at `fuel_balance/composition.py:21`; 3 failed); reverted with `git checkout`, 3 passed. Pass-after: A13 passes at head (A1-A14 plus tfc2 and s6 files: 85 passed).
- **R3h new tests**: `test_tfc2.py::test_window_idle_seconds_exclude_the_stop_slot` (stop mid-window 1500 not 1800; STOPPED end sample 3300; no end sample 3600; SUSPECT end sample 3600), K3 A14 (stop shape 0; converse 300), A3 fixture `running = set(range(25))` (expected numbers unchanged), A6 extended with a stop slot (K3 and `window_evidence` both 0). Deviation: the card's fourth tfc2 case ("non-GOOD sample at slot 6 -> 1800") cannot yield 1800 because slot 6's own state would then be unknown (idle None), so the case is a SUSPECT end sample at the window end (3600, no positive stop marker). Existing tfc2 tests unchanged.
- **F0 ten-night unit parity**: `test_a2_rule_parity_all_ten_nights` passes (K3 L0).
- **Kisiwa L2 parity (part C)**: `host/tests/test_k3_fuel_balance_parity.py` unedited, `assetops_k3_test`: 6 passed in 1117.43 s (0:18:37), nights 2, 4, 6, `idle_seconds == 0`.
- **Byte-equality**: `ch9b2_reserve_trial_golden.json` and `s6_verification_api_contract.json` untouched (git status clean); their Postgres tests pass: `test_ch9b2_reserve_byte_equal_postgres.py`, `test_s6_verification_evaluator_postgres.py`, `test_out_e3_trial_comparison_postgres.py`, `test_k3_fuel_balance_postgres.py`: 28 passed, 417.21 s, `assetops_k3_test`.
- Localised non-DB: `test_tfc2.py`, `test_s6_verification_rules.py`, `test_s6_verification_verdict.py`, `test_k3_fuel_balance_rules.py`: 85 passed.
- Probes: `probe_kisiwa_fuel.py --check` "probe result current"; `probe_kisiwa_nights.py --check` "probe result current (G6 pass)".

## Kobo impact (A2, §9h.6)
Kobo's idle-fuel money in the demo does not change. A2 changes only in a verification window containing a stop slot (RUNNING sample, 0 kWh, then a not-running sample). Kobo's baseline hour (09:00-10:00 local) sits inside a run idling 07:05-10:55 and its later hour has no run; neither contains a stop, so both keep 3600 s and 0 s. fuel-cost-2 counts idle inside dispatch's Candidate time, already ending at the last RUNNING sample, so it is unaffected. In general a trial window with a stop would previously have gained 300 s per stop (0.275 L nominal, 0.3025 L at 3.3 L/h, about 0.34-0.38 USD); no demo window has one. A3's check (stored trial-hour idle = 12 slots) stands as backstop.

## Checks
`tools\check-all.ps1 -Python <plan2 venv>`: "All 17 guards passed" (after `npm ci` in `frontend`; estate guard self-tests 15 passed in 1456.90 s on a contended machine).

## Residual risk
`idle_slot` undercounts at most one slot per stop (at most 0.45 L `use_high` per stop against a 2a = 20 L margin). `rules.py` no longer imports `RUNNING_STATES`.

## User review
Not required by the card; K3's first review (Opus) applies the two R3h mutations (§9h.5).
