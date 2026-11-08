# Review packet R4.1 (branch task/R4-portfolio-thread-state, from caa3fdf23)

Status: built; all checks green (held failure resolved, see below).

## Files
- `backend/assetops_backend/estate/portfolio.py`: `FUEL_THREAD_LABEL` renamed `THREAD_LABEL`; `portfolio_row` `unjoined` rule (fuel mechanism, or no Action on a Cold/EV Site); mini-grid unchanged.
- `frontend/src/estate/EstatePortfolio.tsx`: `fuelThread` -> `threadState = action_id === null && workflow_label !== "No action agreed yet"`; MOCK DEVIATION comment extended.
- `backend/tests/test_r4_domain_row_thread_state.py` (new, no DB), `frontend/src/estate/__tests__/estatePortfolio.test.tsx` (one new case).

## R4.1 item -> evidence
- Rename + rule: `FUEL_THREAD_LABEL` had no other references (grep over py/ts/tsx).
- (a) Cold ACTION_IN_HAND -> Pending, ACT_NOW [EPISODE_OPEN, ACTION_PENDING]; (b) Cold OPEN; (c) EV CHANGE_APPLIED -> Applied; (d) Cold no thread; (e) mini-grid no Action + ACTION_IN_HAND -> "No action agreed yet"; (f) fuel row unchanged: 6 tests pass.
- Existing backend files run with them: test_w303_portfolio_workflow_labels, test_cc_placement, test_k8_estate_fuel, test_ch2_threads: 183 passed total (new file included), no change to any existing backend assertion.
- Vitest `src/estate/__tests__` (5 files): 118 passed, 1 failed. New R4.1 case passes. `tsc --noEmit`: exit 0.
- Not run: Postgres, full suites, layout evidence.

## STOP item for the Architect
Existing test `estatePortfolio.test.tsx:182` ("rendersEveryFindingColumnAndFourLensStates") expects cell 5 = "No action yet Recommendation not accepted Review finding". Its default fixture (`portfolioFixtures.ts:113`) has `action_id: null` and `workflow_label: "Recommendation not accepted"`, a label the server never emits for a row without an Action. Under the spec condition that row is now a thread-state row (bold label, no "No action yet"). This is not an in-hand-thread pin, so per R4.1 I did not edit it. Suggested one-line fix: change the fixture default to `"No action agreed yet"` and the line-182 expectation to "No action yet No action agreed yet Review finding" (check other tests using that default).

## Held failure -> resolved (stale fixture; server evidence portfolio.py:229/269)
Coordinator-approved: "Recommendation not accepted" is never emitted by the server (only "No action agreed yet"). `portfolioFixtures.ts:113` default now "No action agreed yet"; `estatePortfolio.test.tsx:182` expects "No action yet No action agreed yet Review finding". Rerun: `src/estate/__tests__` plus the other importers (`work/globalMaintenance`, `blocks/evidenceTrace`): 7 files, 166 passed, 0 failed; `tsc --noEmit` exit 0. No other test depended on the old label. The Stop item above is superseded by this.

## Residual
- node_modules in the worktree is a junction to the plan2 checkout (untracked/ignored; not committed).
