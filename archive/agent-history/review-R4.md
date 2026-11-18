# Review R4.1: Portfolio Cold/EV thread state (light review)

Branch `task/R4-portfolio-thread-state`, head 4518f888f; diff `main...HEAD` (6 files).
Spec: build-sheet-OWN-GAPS-2026-11-08.md, "R4.1".

## Verdict: ACCEPT WITH NOTES (no High or Medium findings)

## Against R4.1
- `estate/portfolio.py:255-269`: rename and `unjoined` rule match the spec text exactly; comment updated as asked.
  `DOMAIN_OF_SITE_TYPE` keys on the stored site type (`estate/index.py:177, 242` set `_domain = site_type`), so
  COLDCHAIN/EV_CHARGING resolve to COLD/EV. No new query, port or migration.
- Mini-grid unchanged: a mini row with no joined Action gets `workflow_label(None)` = "No action agreed yet"
  (`portfolio.py:231-233`), and the frontend `threadState` (`EstatePortfolio.tsx:153`) requires that label to differ,
  so mini rows render as before. Must-fail test `test_e` is meaningful: dropping the domain test turns it "Pending".
- Cold temperature row (thread OPEN) keeps "No action agreed yet" -> "No action yet" (test_b, and the frontend case's
  second row). Start-failure/EV ACTION_IN_HAND -> "Pending" with ACT_NOW [EPISODE_OPEN, ACTION_PENDING] (test_a);
  EV CHANGE_APPLIED -> "Applied" (test_c); fuel unchanged (test_f).
- No `actionIndex.tsx`, `select_action_scope`, cursor or tool change.

## Fixture correction (held failure)
Confirmed. "Recommendation not accepted" occurs nowhere in `backend/assetops_backend` or `frontend/src`; the only
labels the server emits for an Action-less row are "No action agreed yet" or a THREAD_LABEL value
(`portfolio.py:231-233, 269`). The old default was an impossible server state, so changing
`portfolioFixtures.ts:113` and the expectation at `estatePortfolio.test.tsx:182` corrects a stale fixture, not a pinned
behaviour. All five importers of the fixture pass.

## Other consumers checked
`FUEL_THREAD_LABEL`/`fuelThread`: no remaining references. `workflow_label` readers: `placement.py:157` (takes the
label, intended), `site_outcomes/board.py` (own mini labels, not the Portfolio row), `tools/checks/chain_coherence.py:1469`
(COH L3, below), `tools/s602b_test_scoped_cases.py:329` (mini F-05, unaffected).

## Findings
- Low (residual risk, not a defect): `chain_coherence.py:1468-1473` COH L3 counts distinct "Verified" Portfolio
  threads against `count.verified_results`. Cold/EV rows with RESOLVED_MONITORING/CLOSED threads now read "Verified"
  and join that set. This should improve agreement (the claim already counts all verified threads), but it is a
  behaviour change for a check on the demo bundle; the E4/check-all run after merge is where it is proven.
- Low (test hygiene, preference): the new frontend case (`estatePortfolio.test.tsx:1057-1063`) builds the Cold row's
  finding ref with `kind: "FUEL_FINDING"`; harmless to the assertions, but a Cold ref kind would read truer.
- Low (note): spec named branch `task/R4-1-domain-row-thread-state`; built on `task/R4-portfolio-thread-state`.

## Checks run (by reviewer)
- pytest `test_r4_domain_row_thread_state.py test_w303_portfolio_workflow_labels.py test_cc_placement.py
  test_k8_estate_fuel.py test_ch2_threads.py`: 183 passed, 3.3 s (worktree code: test_f's THREAD_LABEL import proves it).
- vitest `src/estate/__tests__ src/work src/blocks` (covers all five `portfolioFixtures` importers): 16 files,
  336 passed, 0 failed.
- `npx.cmd tsc --noEmit`: exit 0.
- Not run: Postgres, full suites, production build, layout evidence (single-cell text change; not layout-sensitive
  beyond the existing MD-FUEL-K4-1 treatment). Demo-build proof (E4 item) remains to be done after merge.
