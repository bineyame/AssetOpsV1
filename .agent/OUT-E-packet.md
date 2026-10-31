# OUT-E review packet - cost check after the generator trial

Task `tasks/OUT-E-cost-proof.md` (in_review, USER_REVIEW_REQUIRED: false). Branch `task/OUT-E-cost-proof`, from main
b94aee17. Contract `AssetOpsV1-plan2/.agent/build-sheet-OUT-E.md`. E2/E3 review `AssetOpsV1-plan2/.agent/OUT-E2-3-review.md`
(REVISE, all findings fixed). E4 Architect ruling 2026-10-31: option b.

## Outcome delivered
A newly inserted final verification outcome (VERIFIED, INEFFECTIVE, INCONCLUSIVE) appends one stored cost check: the
modelled cost change per kWh of feeder demand on the trial's own two hours, fuel rate and diesel price, or
"not calculated" with its reason. The verification summary serves it with the trial's stored before/after seconds. The
board shows it on the Optimize cost Earlier entry ("Modelled change after the trial · not realised savings: ...") with the
Supply cost per kWh before/after line (attributed only on VERIFIED), and the Assure Verified results line adds the modelled
change. On the real s602b data the Action sits under Protect (R595), so the Cost-row line is proven on fakes only.

## Commits and files
| Unit | Commits | Files |
|---|---|---|
| E1 | 8e39626d | CC-M merge (0036, 0037, `test_cc_schema_postgres.py`); `migrations/versions/0039_merge_objectives_cc.py`; 20 head-literal tests + `mini_depth_probe.py`; `test_out_d1_schema_postgres.py` |
| E2 | 0e849cba, 88c06602 | `actions/verification_rules.py` (`generator_kwh`); `financials/trial_fuel_comparison.py`; `tests/test_out_e2_trial_comparison.py`; `test_s6_verification_rules.py` |
| E3 | 0ec2c147, dabcbe6a, 88c06602, 2862e0b2 | `financials/adapters/postgres_trial_comparison_store.py`; `financials/composition.py`; `actions/verification.py` (hook); `actions/composition.py`; `actions/adapters/postgres_action_store.py` (`sfc_history`, `finite_decimal`); `tools/checks/configuration-persistence.ps1`; `tools/checks/test_estate_guard.py`; `tools/s602b_test_scoped_cases.py`; `test_s6_verification_evaluator_postgres.py` (`complete_windows`); `fixtures/s6_verification_api_contract.json`; `tests/out_e_trial_child.py`; `tests/test_out_e3_trial_comparison_postgres.py` |
| E4 | 9517749e, d11a2311 | `actions/verification.py` (`summary`); `site_outcomes/board.py`; `site_outcomes/mini.py`; `frontend/src/sites/outcomeBoardClient.ts`, `OutcomeBoard.tsx`, `__tests__/outcomeBoard.test.tsx`; `tests/test_out_e4_readback.py`, `_postgres.py`; `test_out_b1_board.py`, `test_out_b2_mini.py`, `test_out_b3_cold_ev.py` (`detail: None` in exact dicts) |
| E5 | 171c142c, e18c6e22, 223baa5b | register R590-R595; `tools/s602b_verification_walkthrough.py` (CASES + `verified`); `.agent/OUT-E-captures/` |

## Wire additions
- Evidence read (`GET .../verification/evidence`) windows: `generator_kwh` (review M1).
- Verification summary: `cost_check {state, reason, nominal, upper, currency, recorded_at} | null`, `trial_hours
  {before_seconds, after_seconds} | null`. The S6 contract fixture gained exactly these three keys.
- Board `earlier[].detail: string | null`. Schema versions unchanged.

## Acceptance (§8)
1. Met. CC-M merged; only the 0036/0037 docstrings changed; `alembic heads` = `0039_merge_objectives_cc`; both schema tests green.
2. Met. Worked example `1/24` / `11/240`, 0.125 and 1/12; one isolating test per reason plus precedence; reasons and states
   equal 0037's CHECK tuples (test imports both).
3. Met. E3 Postgres: verified -> 1 revision MODELLED_IMPROVEMENT `1/24` (SFC 0.3, 1.25 USD); replay (200) appends none;
   inconclusive -> UNAVAILABLE/OUTCOME_INCONCLUSIVE; target_miss -> MODELLED_NO_IMPROVEMENT `0`; injected store failure ->
   outcome recorded (201), no revision; `plan_sha256` equal at freeze and after; `details` windows have no `generator_kwh`.
4. Partly met (Architect ruling, option b). Assure line on real data: "ACT-000001 verified on test data · modelled change
   0.042–0.046 USD less per kWh of feeder demand". The Cost-row Earlier detail ("Modelled change after the trial · not
   realised savings: 0.042–0.046 USD less per kWh of feeder demand · Supply cost per kWh before the trial: missed · after:
   met") and the not-verified "Status changed; not attributed" are proven by fake-port tests; on the s602b board day the
   Finding index is UNASSESSED, so the Action is under Protect with detail null and the Cost Earlier list is empty (R595 open).
   Codes are ACT-000001 on this data, not ACT-048.
5. Met pending the `-Tier all` line below: guard registers the writer and three probes fail without it/without the INSERT/
   with a foreign write; check-all 11/11; full vitest only the 3 known failures.

## Checks run
- E1 focused: 22 files, 269 passed, 31m38s.
- E3 tier (after review fixes, 2862e0b2): evaluator, holds, plan, E3, E4 Postgres, b4 board, w301, w303 ×2, site action
  index: 62 passed, 15m24s.
- Pure: E2 + E4 unit 38 passed; board family (b1, b2, b3, c2, c3, d2, d4) 159 passed; vitest outcomeBoard 17 passed; `tsc` clean.
- `tools/check-all.ps1` (ASSETOPS_GUARD_PYTHON set): All 11 guards passed (estate guard self-tests 7 passed).
- Full vitest at 223baa5b: 3534 passed, 3 failed (`w1f4VerificationStructure`, known).
- Full backend: `tools\run-backend-suite-in-container.ps1 -Tier all` at 223baa5b, started 05:49:27: RESULT_PENDING
- Captures: `.agent/OUT-E-captures/README.txt` (Overview refused on the case DBs; board recorded as API JSON per case).

## Known deviations
- Recorded at the service clock: the store writes the caller's `recorded_at` (the evaluation's clock) instead of
  `clock_timestamp()`. Came out of the M1 fixture fix: the wall-clock stamp made the contract fixture unstable.
- `_window_replay`, not `_replay`: the sheet's name already exists on `VerificationService` (plan-freeze replay); the first
  E3 commit shadowed it and broke freeze replays (caught by the evaluator tests, fixed dabcbe6a).
- Hook payload is `{outcome_id, intervention_cost}` (review L1, CC-D2 definition).
- `ZERO_DEMAND` also covers an unknown feeder total (unreachable once both windows are complete).
- E3 Postgres DBs are `assetops_out_e_trial_<case>_test` (one fresh DB per case), not one `assetops_out_e_trial_test`.
- Guard probes are appended to `tools/checks/test_estate_guard.py` (run by check-all) rather than a new file.
- board.py stays stdlib-minimal (its import test): rounding is exact integer half-even, not Fraction/Decimal.
- Captures: Kobo Overview is refused on the s602b case DBs (no passing S2 comparison; OUT-B4 Addendum 1/6), so no board
  screenshot shows the cost check; the per-case board API JSON is the evidence.
- The walkthrough `CASES` gained `verified` so `prepare` builds it.

## Residual risk
- Every evaluation now writes a cost-check revision (PRICE_MISSING when no price is published); no row-count test broke and
  no money line is shown for not-improved checks (captures README).
- The Cost-row read-back on real data is unproven until the combined dataset (R595).

## User-review focus
Copy on the Earlier entry and Assure line (§4); "not realised savings" is the only "saving" word on screen.
