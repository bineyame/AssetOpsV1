# Post-W6 audit batch 04: W1 Action/work (human ledger)

Every disposition is a **PROPOSAL** for the Architect. This batch added no rows to `.agent/mock-departure-register.md`. Machine record: `batch-04.json`; side-by-side: `index.html`.

## Frozen run

- **main_sha**: d66f57e6 (product code identical to frozen fddf5cad; `git diff fddf5cad d66f57e6 -- frontend/src backend host` is empty)
- **branch**: audit/batch-04
- **worktree**: AssetOpsV1-review5
- **manifest_sha256**: f19aa2a30e2a5dcbc8683d04cb88c41ef75b9a95194ca2e4fc6650b9511c64af
- **mock_index_sha256**: bf8f6723fb8c223f5207bfc7d422d5c927f587aa8da511fa8fb64be6091f8e35
- **inventory_check**: spec 87 + 23 = 110 (verified by batch 01 on the same manifest hash); all 6 batch-04 IDs mounted
- **clock**: server real UTC, captured 2026-10-24 ~15:30-15:50 UTC; producer fixture clocks as recorded per pair
- **api**: http://127.0.0.1:18401 (s601b, then s602b replay); 18402 (s602b TEST-SCOPED guardrail case)
- **frontend**: http://localhost:5184 Vite dev (ASSETOPS_API_PORT=18401, restarted with 18402 for the case run); mock /mockups/v69/index.html#/<id>
- **viewports**: ['1440x1000 full-page', '390x900 mobile emulation full-page']
- **capture_tool**: .agent/post-W6-audit/batch-04/tools/capture-b4.mjs (batch-02 capture-b2.mjs with CDP port 9524; capture-only: navigate, wait, screenshot, measure DOM, record console errors)

Producers (reviewed, run unmodified, owner scratch-DB authorization 2026-10-24):
- `s601b_action_walkthrough.py --db assetops_s601b_audit --work var/s601b_audit_b4` prepare / links / serve --port 18401 / drop.
- `s602b_verification_walkthrough.py --db assetops_s602b_audit --work var/s602b_audit_b4` prepare (replay + 4 TEST-SCOPED case DBs) / links / serve --case guardrail --port 18401 (case API 18402) / drop.
- No seeding, no API fabrication, no product edit. Every spawned PID was stopped by PID. All `_audit` DBs and work folders were dropped by the producers' drop modes. Logs are in `logs/`.

## Route reconciliation

- `recommendation`: SITE_FINDING_VIEW_ROUTE_PATH /sites/:siteId/findings/:findingId/:findingView (recommendation in FINDING_CHILD_VIEWS) mounted
- `action-overview`: SITE_ACTION_ROUTE_PATH /sites/:siteId/actions/:actionId mounted (SiteActionFrame)
- `action-execution`: SITE_ACTION_VIEW_ROUTE_PATH /sites/:siteId/actions/:actionId/:actionView (execution) mounted
- `action-history`: same, history mounted
- `action-plan`: same, plan mounted
- `action-evidence`: same, evidence mounted
- `spec_route_table`: Correct for all six. Note: the explicit /actions/:id/overview segment renders 'No such Action section' (only the bare path is Overview), B4-24.

## Blockers

- None. The s601b and s602b _audit DBs (plus the 4 s602b case DBs) were created and dropped by the producers' own prepare/drop modes; batch 3's s404/s405/s408 DBs were untouched.

## Pairs (50, 12 representative)

| Screen | Case | Width | Rep | Order match | Max ratio | >1.3 panels | Dark band 390 | Console | Differences | App | Mock |
|---|---|---|---|---|---|---|---|---|---|---|---|
| recommendation | accepted | 1440 | yes | True | 1.28 |  |  |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B4-01, B4-08, B4-09, B4-10, B4-12, B4-13, B4-14, B4-15, B1-53, B1-07 | [app](s601b/recommendation-accepted-1440-app.png) | [mock](s601b/recommendation-accepted-1440-mock.png) |
| recommendation | accepted | 390 | yes | True | 1.4 | Proposed intervention, Evidence needed to verify | 92 |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B1-03, B4-01, B4-08, B4-09, B4-10, B4-12, B4-13, B4-14, B4-15, B1-53, B1-07 | [app](s601b/recommendation-accepted-390-app.png) | [mock](s601b/recommendation-accepted-390-mock.png) |
| recommendation | latest-trial-open | 1440 |  | True | 1.3 |  |  |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B4-01, B4-08, B4-09, B4-10, B4-12, B4-13, B4-14, B4-15, B1-53, B1-07 | [app](s601b/recommendation-latest-trial-open-1440-app.png) | [mock](s601b/recommendation-latest-trial-open-1440-mock.png) |
| recommendation | latest-trial-open | 390 |  | True | 1.39 | Proposed intervention | 92 |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B1-03, B4-01, B4-08, B4-09, B4-10, B4-12, B4-13, B4-14, B4-15, B1-53, B1-07 | [app](s601b/recommendation-latest-trial-open-390-app.png) | [mock](s601b/recommendation-latest-trial-open-390-mock.png) |
| recommendation | unavailable | 1440 |  | True | 1.34 | Proposed intervention, Declare success before evaluating |  |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B4-01, B4-08, B4-09, B4-10, B4-12, B4-13, B4-14, B4-15, B1-53, B1-07, B4-25 | [app](s601b/recommendation-unavailable-1440-app.png) | [mock](s601b/recommendation-unavailable-1440-mock.png) |
| recommendation | unavailable | 390 |  | True | 1.42 | Proposed intervention | 92 |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B1-03, B4-01, B4-08, B4-09, B4-10, B4-12, B4-13, B4-14, B4-15, B1-53, B1-07, B4-25 | [app](s601b/recommendation-unavailable-390-app.png) | [mock](s601b/recommendation-unavailable-390-mock.png) |
| action-overview | recorded | 1440 | yes | True | 1.37 | Action scope |  |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B4-07, B4-16, R69-verified | [app](s601b/action-overview-recorded-1440-app.png) | [mock](s601b/action-overview-recorded-1440-mock.png) |
| action-overview | recorded | 390 | yes | True | 2.17 | Action scope | 92 |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B1-03, B4-07, B4-16, R69-verified | [app](s601b/action-overview-recorded-390-app.png) | [mock](s601b/action-overview-recorded-390-mock.png) |
| action-overview | pending-f02 | 1440 |  | True | 1.37 | Action scope |  |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B4-07, B4-16, R69-verified | [app](s601b/action-overview-pending-f02-1440-app.png) | [mock](s601b/action-overview-pending-f02-1440-mock.png) |
| action-overview | pending-f02 | 390 |  | True | 2.05 | Action scope | 92 |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B1-03, B4-07, B4-16, R69-verified | [app](s601b/action-overview-pending-f02-390-app.png) | [mock](s601b/action-overview-pending-f02-390-mock.png) |
| action-overview | unknown-section | 1440 |  | False | 0.38 |  |  |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B4-07, B4-16, R69-verified, B4-24, B1-07 | [app](s601b/action-overview-unknown-section-1440-app.png) | [mock](s601b/action-overview-unknown-section-1440-mock.png) |
| action-overview | unknown-section | 390 |  | False | 0.47 |  | 325 |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B1-03, B4-07, B4-16, R69-verified, B4-24, B1-07, B1-02 | [app](s601b/action-overview-unknown-section-390-app.png) | [mock](s601b/action-overview-unknown-section-390-mock.png) |
| action-execution | applied | 1440 | yes | True | 1.53 | Activity log |  |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B4-07, B4-17, B1-53, R69-verified | [app](s601b/action-execution-applied-1440-app.png) | [mock](s601b/action-execution-applied-1440-mock.png) |
| action-execution | applied | 390 | yes | True | 2.69 | Activity log | 92 |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B1-03, B4-07, B4-17, B1-53, R69-verified | [app](s601b/action-execution-applied-390-app.png) | [mock](s601b/action-execution-applied-390-mock.png) |
| action-execution | failed-pending | 1440 |  | True | 1.73 | Activity log |  |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B4-07, B4-17, B1-53, R69-verified | [app](s601b/action-execution-failed-pending-1440-app.png) | [mock](s601b/action-execution-failed-pending-1440-mock.png) |
| action-execution | failed-pending | 390 |  | True | 2.9 | Activity log | 92 |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B1-03, B4-07, B4-17, B1-53, R69-verified | [app](s601b/action-execution-failed-pending-390-app.png) | [mock](s601b/action-execution-failed-pending-390-mock.png) |
| action-history | all | 1440 | yes | True | 1.46 | Action history |  |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B4-07, B4-18, B4-20, B1-53, R69-verified | [app](s601b/action-history-all-1440-app.png) | [mock](s601b/action-history-all-1440-mock.png) |
| action-history | all | 390 | yes | True | 1.77 | Action history | 142 |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B1-03, B4-07, B4-18, B4-20, B1-53, R69-verified, B1-02 | [app](s601b/action-history-all-390-app.png) | [mock](s601b/action-history-all-390-mock.png) |
| action-history | event-failed-stale | 1440 |  | True | 1.49 | Action history |  |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B4-07, B4-18, B4-20, B1-53, R69-verified | [app](s601b/action-history-event-failed-stale-1440-app.png) | [mock](s601b/action-history-event-failed-stale-1440-mock.png) |
| action-history | event-failed-stale | 390 |  | True | 1.82 | Action history | 137 |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B1-03, B4-07, B4-18, B4-20, B1-53, R69-verified, B1-02 | [app](s601b/action-history-event-failed-stale-390-app.png) | [mock](s601b/action-history-event-failed-stale-390-mock.png) |
| action-history | recorded-at | 1440 |  | True | 1.25 |  |  |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B4-07, B4-18, B4-20, B1-53, R69-verified | [app](s601b/action-history-recorded-at-1440-app.png) | [mock](s601b/action-history-recorded-at-1440-mock.png) |
| action-history | recorded-at | 390 |  | True | 1.74 | Action history | 146 |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B1-03, B4-07, B4-18, B4-20, B1-53, R69-verified, B1-02 | [app](s601b/action-history-recorded-at-390-app.png) | [mock](s601b/action-history-recorded-at-390-mock.png) |
| action-history | selector-conflict | 1440 |  | True | 0.4 |  |  |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B4-07, B4-18, B4-20, B1-53, R69-verified | [app](s601b/action-history-selector-conflict-1440-app.png) | [mock](s601b/action-history-selector-conflict-1440-mock.png) |
| action-history | selector-conflict | 390 |  | True | 0.4 |  | 182 |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B1-03, B4-07, B4-18, B4-20, B1-53, R69-verified, B1-02 | [app](s601b/action-history-selector-conflict-390-app.png) | [mock](s601b/action-history-selector-conflict-390-mock.png) |
| action-plan | pre-plan-s601b | 1440 |  | True | 0.43 |  |  |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B4-07, B4-21, R69-verified, B4-23 | [app](s601b/action-plan-pre-plan-s601b-1440-app.png) | [mock](s601b/action-plan-pre-plan-s601b-1440-mock.png) |
| action-plan | pre-plan-s601b | 390 |  | True | 0.44 |  | 197 |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B1-03, B4-07, B4-21, R69-verified, B4-23, B1-02 | [app](s601b/action-plan-pre-plan-s601b-390-app.png) | [mock](s601b/action-plan-pre-plan-s601b-390-mock.png) |
| action-evidence | pre-plan-s601b | 1440 |  | True | 0.47 |  |  |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B4-07, B4-22, R69-verified, B4-23 | [app](s601b/action-evidence-pre-plan-s601b-1440-app.png) | [mock](s601b/action-evidence-pre-plan-s601b-1440-mock.png) |
| action-evidence | pre-plan-s601b | 390 |  | True | 0.53 |  | 189 |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B1-03, B4-07, B4-22, R69-verified, B4-23, B1-02 | [app](s601b/action-evidence-pre-plan-s601b-390-app.png) | [mock](s601b/action-evidence-pre-plan-s601b-390-mock.png) |
| recommendation | verified-replay | 1440 |  | True | 1.28 |  |  |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B4-01, B4-08, B4-09, B4-10, B4-12, B4-13, B4-14, B4-15, B1-53, B1-07 | [app](s602b/recommendation-verified-replay-1440-app.png) | [mock](s602b/recommendation-verified-replay-1440-mock.png) |
| recommendation | verified-replay | 390 |  | True | 1.4 | Proposed intervention, Evidence needed to verify | 92 |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B1-03, B4-01, B4-08, B4-09, B4-10, B4-12, B4-13, B4-14, B4-15, B1-53, B1-07 | [app](s602b/recommendation-verified-replay-390-app.png) | [mock](s602b/recommendation-verified-replay-390-mock.png) |
| action-overview | verified-replay | 1440 |  | True | 1.43 | Action scope |  |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B4-07, B4-16, R69-verified | [app](s602b/action-overview-verified-replay-1440-app.png) | [mock](s602b/action-overview-verified-replay-1440-mock.png) |
| action-overview | verified-replay | 390 |  | True | 2.4 | Action scope | 92 |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B1-03, B4-07, B4-16, R69-verified | [app](s602b/action-overview-verified-replay-390-app.png) | [mock](s602b/action-overview-verified-replay-390-mock.png) |
| action-execution | verified-replay | 1440 |  | True | 1.53 | Activity log |  |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B4-07, B4-17, B1-53, R69-verified | [app](s602b/action-execution-verified-replay-1440-app.png) | [mock](s602b/action-execution-verified-replay-1440-mock.png) |
| action-execution | verified-replay | 390 |  | True | 2.69 | Activity log | 92 |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B1-03, B4-07, B4-17, B1-53, R69-verified | [app](s602b/action-execution-verified-replay-390-app.png) | [mock](s602b/action-execution-verified-replay-390-mock.png) |
| action-history | verified-replay | 1440 |  | True | 1.21 |  |  | ERROR | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B4-07, B4-18, B4-20, B1-53, R69-verified, B4-19 | [app](s602b/action-history-verified-replay-1440-app.png) | [mock](s602b/action-history-verified-replay-1440-mock.png) |
| action-history | verified-replay | 390 |  | True | 2.42 | Action history | 92 | ERROR | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B1-03, B4-07, B4-18, B4-20, B1-53, R69-verified, B4-19 | [app](s602b/action-history-verified-replay-390-app.png) | [mock](s602b/action-history-verified-replay-390-mock.png) |
| action-plan | pass | 1440 | yes | True | 1.28 |  |  |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B4-07, B4-21, R69-verified | [app](s602b/action-plan-pass-1440-app.png) | [mock](s602b/action-plan-pass-1440-mock.png) |
| action-plan | pass | 390 | yes | True | 1.44 | Success criteria | 92 |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B1-03, B4-07, B4-21, R69-verified | [app](s602b/action-plan-pass-390-app.png) | [mock](s602b/action-plan-pass-390-mock.png) |
| action-plan | exact-plan | 1440 |  | True | 1.28 |  |  |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B4-07, B4-21, R69-verified | [app](s602b/action-plan-exact-plan-1440-app.png) | [mock](s602b/action-plan-exact-plan-1440-mock.png) |
| action-plan | exact-plan | 390 |  | True | 1.44 | Success criteria | 92 |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B1-03, B4-07, B4-21, R69-verified | [app](s602b/action-plan-exact-plan-390-app.png) | [mock](s602b/action-plan-exact-plan-390-mock.png) |
| action-evidence | pass | 1440 | yes | True | 1.32 | Evidence requirements |  |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B4-07, B4-22, R69-verified | [app](s602b/action-evidence-pass-1440-app.png) | [mock](s602b/action-evidence-pass-1440-mock.png) |
| action-evidence | pass | 390 | yes | True | 2.0 | Evidence requirements | 92 |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B1-03, B4-07, B4-22, R69-verified | [app](s602b/action-evidence-pass-390-app.png) | [mock](s602b/action-evidence-pass-390-mock.png) |
| action-plan | guardrail | 1440 |  | True | 1.37 | Success criteria |  |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B4-07, B4-21, R69-verified | [app](s602b-guardrail/action-plan-guardrail-1440-app.png) | [mock](s602b-guardrail/action-plan-guardrail-1440-mock.png) |
| action-plan | guardrail | 390 |  | True | 1.6 | Success criteria | 92 |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B1-03, B4-07, B4-21, R69-verified | [app](s602b-guardrail/action-plan-guardrail-390-app.png) | [mock](s602b-guardrail/action-plan-guardrail-390-mock.png) |
| action-evidence | guardrail | 1440 |  | True | 1.42 | Evidence requirements |  |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B4-07, B4-22, R69-verified | [app](s602b-guardrail/action-evidence-guardrail-1440-app.png) | [mock](s602b-guardrail/action-evidence-guardrail-1440-mock.png) |
| action-evidence | guardrail | 390 |  | True | 2.35 | Evidence requirements | 92 |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B1-03, B4-07, B4-22, R69-verified | [app](s602b-guardrail/action-evidence-guardrail-390-app.png) | [mock](s602b-guardrail/action-evidence-guardrail-390-mock.png) |
| action-overview | guardrail | 1440 |  | True | 1.43 | Action scope |  |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B4-07, B4-16, R69-verified | [app](s602b-guardrail/action-overview-guardrail-1440-app.png) | [mock](s602b-guardrail/action-overview-guardrail-1440-mock.png) |
| action-overview | guardrail | 390 |  | True | 2.4 | Action scope | 92 |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B1-03, B4-07, B4-16, R69-verified | [app](s602b-guardrail/action-overview-guardrail-390-app.png) | [mock](s602b-guardrail/action-overview-guardrail-390-mock.png) |
| recommendation | guardrail-hold | 1440 |  | True | 1.39 | Proposed intervention, Declare success before evaluating |  |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B4-01, B4-08, B4-09, B4-10, B4-12, B4-13, B4-14, B4-15, B1-53, B1-07 | [app](s602b-guardrail/recommendation-guardrail-hold-1440-app.png) | [mock](s602b-guardrail/recommendation-guardrail-hold-1440-mock.png) |
| recommendation | guardrail-hold | 390 |  | True | 1.55 | Proposed intervention | 92 |  | B1-01, B1-04, B4-03, B4-04, B4-05, B4-06, B4-11, B1-03, B4-01, B4-08, B4-09, B4-10, B4-12, B4-13, B4-14, B4-15, B1-53, B1-07 | [app](s602b-guardrail/recommendation-guardrail-hold-390-app.png) | [mock](s602b-guardrail/recommendation-guardrail-hold-390-mock.png) |

Panel titles and order match the mock on every pair, except the deliberate unknown-section error state (B4-24). App page horizontal overflow is 0 on all 50 pairs. Inner scrollers: Site tab row at 390 (B4-04), and the Activity log/History tables at 390 (readable scroll).

## Differences and proposed dispositions

### B4-01 (recommendation)

- Observed: Rail selects 'Sites' on every Recommendation case; the mock selects 'Findings' (Finding-rooted page).
- Evidence: s601b/recommendation-accepted-1440-{app,mock}.png
- Proposed: (c) D3 candidate: renderable with the pathname-scoped rail override R69 already uses for Action paths. Overlaps batch 03 Finding pages; one shared shell fix.

### R69-verified (action-overview, action-execution, action-history, action-plan, action-evidence)

- Observed: Rail selects 'Actions' on every W1 Action detail path and state, as the mock does.
- Evidence: s601b/action-overview-recorded-1440-app.png
- Proposed: (a) R69 D5, status 'resolved: W5-02c K4a (merge f8137643)' verified at fddf5cad. No difference.

### B4-03 (action-* (all five))

- Observed: Breadcrumb is Finding-rooted 'Sites / Kobo mini-grid / Findings / Action [/ section]' with a generic 'Action' crumb; mock is Action-rooted 'Actions > ACT-048 > <section> · site: Kobo Mini-grid'. The rail (R69) says Actions while the breadcrumb says Findings.
- Evidence: s601b/action-overview-recorded-1440-{app,mock}.png
- Proposed: (c) D3 candidate: /actions (W3-01) and the Action code are both available, so the mock trail is renderable.

### B4-04 (all six)

- Observed: An extra Site tab row (Overview ... Evidence, Findings current) sits above the page sub-tabs. The mock shows only the page sub-tab row on these screens. At 390 the row overflows (521 px in 358 px) with a visible grey scroll bar and a cut-off 'W...' item.
- Evidence: s601b/action-overview-recorded-390-{app,mock}.png; s601b/recommendation-accepted-1440-{app,mock}.png
- Proposed: (c) D3 candidate (faithful alternative: drop the row, keep breadcrumb/Open site), or (b) candidate D2 if the Architect keeps Site navigation. There is no Rxx today.

### B4-05 (all six)

- Observed: The mock's header 'Open site' button is absent.
- Evidence: s601b/action-plan-pre-plan-s601b-1440-mock.png vs app
- Proposed: (c) D3 candidate (minor; the Site route exists).

### B4-06 (all six)

- Observed: Subtitle: Action reads 'Kobo mini-grid · an action raised from a finding' where the mock has 'What is the current intervention and outcome state?'. Recommendation reads 'Kobo mini-grid · generator support finding' where the mock has 'F-104 · proposed policy intervention and declared success criterion'. h1 values are from the selected records.
- Evidence: s601b/*-1440-{app,mock}.png
- Proposed: (b) candidate D4 (record-derived title/subtitle replaces illustrative copy).

### B4-07 (action-* (all five))

- Observed: Sub-tab 'Application' vs mock 'Execution'. It is deliberate: SiteAction.tsx:81 'the label is the operator's word', and the URL segment stays /execution. There is no register row.
- Evidence: s601b/action-execution-applied-1440-{app,mock}.png
- Proposed: (b) candidate D2 (plain-language label); needs a register row and the owner's note.

### B4-08 (recommendation)

- Observed: Finding sub-tab 'Analysis · Not available yet' is non-interactive; the mock has a live 'Analysis'.
- Evidence: s601b/recommendation-accepted-1440-app.png
- Proposed: (a) R21 D2, status 'built', verified (visible, noninteractive, mock order kept).

### B4-09 (recommendation)

- Observed: Breadcrumb reads 'Findings / Finding code unavailable / Recommendation' where the mock has F-104. The h1 'Generator support review' comes from the record (mock: 'Generator support merits review').
- Evidence: s601b/recommendation-accepted-1440-{app,mock}.png
- Proposed: Code: (b) candidate D1 (no public W1 Finding code; analogue of R65/R74 for cold/EV). Title: candidate D4.

### B4-10 (recommendation)

- Observed: An extra unboxed page line, 'Analysis unavailable for this Finding section; use the Finding overview and evidence.', sits above the state strip on every case. It is not in the mock, and the Analysis sub-tab already says Not available yet (R21).
- Evidence: s601b/recommendation-*-1440-app.png
- Proposed: (c) D3 candidate (redundant extra line; R21 already states the gap).

### B4-11 (all six)

- Observed: W1 state-line pattern: Recommendation, Plan and Evidence carry a page-level status strip (badge, current-state chip, sentence, As of, Open Verification, 'How this was worked out'), and Overview, Application and History carry an in-panel badge line, note sentences and a closing disclosure. On Action pages the mock has none of these; on Recommendation it has a one-line context strip.
- Evidence: s602b/action-plan-pass-1440-{app,mock}.png
- Proposed: Cite B1-05: candidate D2 shell pattern (W1-UX provenance/state line). It drives part of every >1.3x ratio below.

### B4-12 (recommendation)

- Observed: Proposed intervention adds a 'Trial only' paragraph, a Source row, accepted-note lines and a disclosure. When held, the Accept button is a disabled 'Accept trial (SYSTEM demonstration)' with an amber hold callout; when accepted, no button shows. Ratio 1.28-1.39 at 1440 and 1.32-1.55 at 390 (worst: guardrail-hold 710/457).
- Evidence: s601b/recommendation-*.png; s602b-guardrail/recommendation-guardrail-hold-390-app.png
- Proposed: (b) candidate D2 (honest trial caveat and hold) plus D4 values. The >1.3x needs a reviewed ruling (W1-F5b reason carried). '(SYSTEM demonstration)' and the monospace 'battery' asset code: B1-53.

### B4-13 (recommendation)

- Observed: Declare success adds the lead 'How the trial will be judged' and a footer note. Role 'Limit' vs mock 'Guardrail'. Held, unavailable and guardrail-hold cases show no criteria table, only the gap sentence (139 px vs 367 px at 390).
- Evidence: s601b/recommendation-unavailable-1440-app.png
- Proposed: Wording: candidate D2. Empty state: candidate D1 (criteria exist only with an accepted trial). Honest missing state.

### B4-14 (recommendation)

- Observed: The closing notice 'Accepting creates managed work...' is a left-bar callout at about 14 px; the mock has an 11 px info callout with an icon.
- Evidence: s601b/recommendation-accepted-1440-{app,mock}.png
- Proposed: Cite B1-06/B1-07 (shared callout/typography D3 candidate).

### B4-15 (recommendation)

- Observed: Evidence needed to verify: items 'Applied change record' / 'Later operating readings' vs mock 'Applied configuration record' / 'Later operating evidence'. The app adds a verification chip and an 'Open verification' line. Held cases show only a gap sentence (123 px vs 234 px).
- Evidence: s601b/recommendation-accepted-1440-{app,mock}.png
- Proposed: Wording: candidate D2. Gap state: candidate D1.

### B4-16 (action-overview)

- Observed: Action scope has 6 rows vs 5 (adds Application). Source carries multiple links. Outcome is a chip plus a Verification link. Two note lines and a disclosure follow. Owner reads 'Not recorded'. Ratio 1.37-1.43 at 1440 and 2.05-2.40 at 390, where long values wrap in the right column.
- Evidence: s601b/action-overview-recorded-{1440,390}-{app,mock}.png
- Proposed: Rows/notes: candidate D2 (with B4-11). Owner: candidate D1 (no owner field). The 390 ratio >2x needs a measured cap ruling.

### B4-17 (action-execution)

- Observed: Activity log has 5 columns vs 3 (adds Recorded, and Acted by = 'SYSTEM demonstration'), plus a state badge line, a note, a 'Show all N steps' footer and a disclosure. The failed-pending case adds the real Apply form (date input plus 'Apply trial (SYSTEM demonstration)'). Ratio 1.53-1.73 at 1440 and 2.69-2.90 at 390: rows wrap in narrow columns and Acted by sits in an inner scroller (383-428 px in 318 px).
- Evidence: s601b/action-execution-{applied,failed-pending}-{1440,390}-*.png
- Proposed: (b) candidate D2 (extra columns, apply control). It needs a 390 cap ruling (e.g. hide Recorded/Acted by below a breakpoint) or D3 if the Architect caps at the mock columns. Actor string: B1-53.

### B4-18 (action-history)

- Observed: Action history has 4 columns vs 2 (adds Recorded, and Select with adjacent 'This event' / 'Through this time' links and no separator). Meaning shows raw failure codes (ACTION_VALUE_INVALID, ACTION_EFFECTIVE_TIME_INVALID, ACTION_FOUNDATION_STALE) and monospace UUIDs ellipsized to 86 px of 257 px. Ratio 1.46-1.49 at 1440 and 1.74-2.42 at 390.
- Evidence: s601b/action-history-all-1440-{app,mock}.png
- Proposed: Columns: candidate D2. Codes and UUIDs: B1-53 (D3 candidate). Adjacent links: minor D3 candidate (separator).

### B4-19 (action-history (s602b verified-replay))

- Observed: DEFECT. Console 'Encountered two children with the same key' (key af604653-..., both widths). The API returns 3 events (ACCEPTED, APPLIED, RESOLVED af604653). The app renders a first row 'RESOLVED' (raw kind) with meaning 'Trial accepted; nothing on the Site changed.', which is wrong: the event-meaning function falls through to the ACCEPTED sentence at SiteAction.tsx:1338. That row sits beside the resolution record 'Resolved' with the same id. The footnote 'Latest at read time: 3 of 3 events' contradicts the button 'Show all 5 events'.
- Evidence: s602b/action-history-verified-replay-1440-app.png; s602b/evidence.json consoleErrors
- Proposed: (c) D3 defect: map the RESOLVED/RESOLUTION_WITHDRAWN Action event kinds (label and meaning), de-duplicate against resolution_events or key by source+id, and make the counts consistent. W1 mini/Action fix slice.

### B4-20 (action-history)

- Observed: The chip 'Every recorded event' and the sentence 'everything recorded ... 6 of 6 events' sit beside a table showing the latest 3 rows with 'Show all 6 events'.
- Evidence: s601b/action-history-all-1440-app.png
- Proposed: (c) D3 candidate (copy contradicts the visible rows; minor).

### B4-21 (action-plan)

- Observed: Success criteria has 5 rows vs 4 (adds 'Windows (UTC)'). The criterion column renders as bold row headers (mock: regular td); line-height is 16.5 px vs 17.6 px. The app adds a 'Fixed ... the current plan · Open the applied change' line, a 'Dig deeper' disclosure and a footer note; guardrail adds a failed-limit line. Ratio 1.28-1.37 at 1440 and 1.44-1.60 at 390.
- Evidence: s602b/action-plan-pass-1440-{app,mock}.png; s602b-guardrail/action-plan-guardrail-390-app.png
- Proposed: Rows/notes: candidate D2. Bold row headers and line-height: (c) minor D3 candidate typography.

### B4-22 (action-evidence)

- Observed: Evidence requirements has 4 rows vs 3, with status cells holding a chip plus detail text. 'Available' is a green success-tone chip where the mock uses the blue info tone. Row headers are bold. The app adds a readings note, a disclosure (slot tables, closed by default) and a footer. Text is duplicated: 'Registered Lab trial data / Registered Lab trial data'. Ratio 1.32-1.42 at 1440 and 2.00-2.35 at 390.
- Evidence: s602b/action-evidence-pass-1440-{app,mock}.png
- Proposed: Tone: (c) D3 candidate (status token mismatch; cf. B1-14). Rows/detail: candidate D2. Duplicated source text: D3 candidate copy. 390 >2x needs a cap ruling.

### B4-23 (action-plan, action-evidence (s601b pre-plan))

- Observed: Before a frozen plan, the panels show gap sentences only ('No success criteria recorded...', no table): 0.43-0.53x.
- Evidence: s601b/action-plan-pre-plan-s601b-390-app.png
- Proposed: (b) candidate D1 honest missing state (no plan before application). Accept as state.

### B4-24 (action-overview (unknown section /nosuch))

- Observed: 'No such Action section' panel with a generic h1 'Action'. The Action sub-tab row is removed. The sentence is at 14 px. At 390 the dark header is 325 px. There is no mock state. Note: an explicit '/overview' segment also resolves to this state (SiteAnalyticsFrames.tsx:1622); the in-app Overview link uses the bare path.
- Evidence: s601b/action-overview-unknown-section-390-app.png
- Proposed: Error state: Architect to confirm the W1 pattern (no Rxx). 14 px: B1-07. Header: B1-02. '/overview' alias: minor D3 candidate if the canonical sub-tab name should resolve.

### B4-25 (recommendation (s601b 'unavailable' link))

- Observed: The producer labels Finding 8cf723d2 'unavailable (SOC at headroom)', but the page renders the battery hold 'Held: an earlier trial is still open' (hold takes precedence). The SOC-headroom unavailable state cannot be observed from this producer.
- Evidence: s601b/recommendation-unavailable-1440-app.png
- Proposed: Coverage note, not a visual difference. Architect to confirm precedence; no register row.

## Cross-cutting findings cited (not re-described)

- B1-01: all 50 pairs
- B1-03: all 25 pairs at 390
- B1-04/B2-36: all pairs (rail Assets/Settings Not available yet)
- B1-02/B2-04: 7 pairs at 390 (see ui_pass_checks)
- B1-07/B2-03: recommendation (all cases), action-overview unknown-section
- B1-53: recommendation (SYSTEM demonstration, monospace 'battery'), action-execution (Acted by / Apply button), action-history (failure codes, UUIDs, 'RESOLVED')
- B1-05: all six (state line), via B4-11
- B2-02: not present

## Register checks

- R21: built; Recommendation 'Analysis · Not available yet' visible and noninteractive (B4-08)
- R69: resolved (W5-02c K4a f8137643); Actions rail active on all W1 Action detail pairs
- R22: cold-health; not on batch-04 screens
- R23: cold-work-incidents; not on batch-04 screens
- R24: ev-work-incidents; not on batch-04 screens
- R37: cold-performance; not on batch-04 screens
- R38: cold-evidence-analysis; not on batch-04 screens
- R60: ev-health; not on batch-04 screens

## Mandatory UI-pass checks

- prose_14_vs_12: Observed: the Recommendation closing notice is about 14 px (mock 11 px callout); the unknown-section sentence is 14 px. In-panel text is 10-12 px (B1-07, B4-14, B4-24).
- tall_dark_header_390: Observed: dark band 325 px (unknown section), 197 (pre-plan Plan), 189 (pre-plan Evidence), 182 (history selector conflict), 146 (history recorded_at), 142 (history all), 137 (history event), against 92 px on taller pages (B1-02).
- plural_1_incidents: Not applicable: no count+noun incident/maintenance copy. Attempt counts read correctly ('1 recorded, 1 failed', '3 failed attempts').
- raw_EV_CONNECTOR_label: Not applicable (mini Site). Related raw vocabulary observed: B1-53.
- domainActionClient_generic_window_error: Not applicable: W1 battery Actions use actionClient.ts, not domainActionClient.ts; no window inputs.
- R88_R112_window_control: Not applicable: no Window control on these screens (B2-02 not present).

## Panels over 1.3x (measured reasons; each needs a reviewed ruling, none is an automatic pass)

- recommendation P1 (B4-12): extra trial caveat, Source row, notes, disclosure and hold callout. P3 at 390 1.40x: verification chip line.
- action-overview (B4-16): +1 row, multi-link Source, note lines and disclosure; at 390 long values wrap (2.05-2.40x).
- action-execution (B4-17): +2 columns, state line, footer and disclosure; failed adds the apply form; at 390 narrow-column wrapping (2.69-2.90x).
- action-history (B4-18): +2 columns, a code/UUID second line per row, state line and disclosure (1.46-2.42x).
- action-plan (B4-21): +1 row, fixed-at line, disclosure and footer; guardrail failed-limit line (1.28-1.60x).
- action-evidence (B4-22): +1 row, chip+detail cells, readings note, disclosure and footer (1.32-2.35x).
