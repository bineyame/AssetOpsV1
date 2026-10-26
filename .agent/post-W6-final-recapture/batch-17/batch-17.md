# Final recapture batch 17: W5 EV cases/Action

Main SHA 89a11477. Pairs 84 (frozen 84). Counts: FIXED 32, PASS 52

Method: original capture tool and producers (unmodified), same ports, fresh DBs; each pair compared with the frozen evidence (panel titles, heights, rows, columns, links, chips, typography, overflow, header band, tab-row scroll, caps) and the frozen mock (unchanged). Classification derived from measured deltas plus register/rulings; standing D1/D2/D4 rows and ruled caps count as PASS. FIXED = a measured signal that a frozen D3 difference is gone.

## REGRESSION-OPEN (0)
- none

## GAP (0)
- none

## Observations
- Producer `w504_ev_work_walkthrough.py` unmodified with env W504_API_PORT_BASE=18700 (its documented knob), `--work var/w504a_b17 --tag b17` (DBs `w504a_<mode>_b17_test`): prepare, serve, attest, drop. unknown/pending/stale recorded unavailable by the producer itself (as frozen). Capture claims: 0 FAIL in every phase.
- **Flag (inner overflow check, probe `tools/probe-scrollers.mjs`, `logs/probe-scrollers*.json`)**: in the open 'UTC and IDs' cell on Incidents and Maintenance (all-open positive and worstcase-all-open, 1440 and 390; 2-3 per page, 10-15 in worstcase) the Case ID / Version ID / record ID is a one-line `dd.fact-list__value` horizontal scroller (36-char id, 218 px in 99-180 px) with no tabindex, role or accessible name, so the id is cut and not keyboard reachable. Present in the frozen capture too and accepted there (B13-18), so not counted as a new regression, but it is the same mechanism and class as the batch 08 EV Finding `ev-id` scroller (CSS `.work-cases[data-domain-cases="EV_CHARGING"] td .fact-list__value:has(> code){overflow-x:auto}` in `frontend/src/sites/w1f4-changes-work.css`; the L11 focus fix lives in `KeyValueValue` in V69Layout.tsx and not in `Fact` in ui/DataTable.tsx). The labelled data-table regions at 390 (role=region, tabindex 0) are fine. Images: ev-work-incidents-all-open-390-app.png, ev-work-maintenance-all-open-390-app.png.
- Raw ids (UUIDs, sha256 fence) remain inside open disclosures (standing B1-53 / open rows).
- Link-check phase (uncounted) not rerun.


## All pairs
| Screen | Case | Width | Class | Why |
|---|---|---|---|---|
| ev-work-incidents | forbidden-403 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-work-incidents | forbidden-403 | 390 | FIXED | fewer horizontal scrollers |
| ev-work-maintenance | forbidden-403 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-work-maintenance | forbidden-403 | 390 | FIXED | fewer horizontal scrollers |
| ev-action | forbidden-403 | 1440 | FIXED | h1 text changed; 14px prose reduced |
| ev-action | forbidden-403 | 390 | FIXED | h1 text changed; 14px prose reduced |
| ev-work-incidents | positive | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-work-incidents | positive | 390 | FIXED | fewer horizontal scrollers |
| ev-work-incidents | historical-index-known-at | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-work-incidents | historical-index-known-at | 390 | FIXED | fewer horizontal scrollers |
| ev-work-incidents | refused-reversed | 1440 | FIXED | tab rows changed |
| ev-work-incidents | refused-reversed | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| ev-work-incidents | refused-span-32d | 1440 | FIXED | tab rows changed |
| ev-work-incidents | refused-span-32d | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| ev-work-incidents | no-window | 1440 | PASS | No-window now defaults to the current day/week, which holds 1 incident (frozen run's DB day held none), so the table and its closed 'UTC and IDs' disclosure now |
| ev-work-incidents | no-window | 390 | PASS | No-window now defaults to the current day/week, which holds 1 incident (frozen run's DB day held none), so the table and its closed 'UTC and IDs' disclosure now |
| ev-work-incidents | all-open | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-work-incidents | all-open | 390 | FIXED | all-disclosures-open state is exempt from closed caps (frozen B17-13 Accept; all-open exempt); ratio moved 3.04->3.29 (worstcase 6.57->6.82) only from the longe |
| ev-work-maintenance | positive | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-work-maintenance | positive | 390 | FIXED | fewer horizontal scrollers |
| ev-work-maintenance | historical-index-known-at | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-work-maintenance | historical-index-known-at | 390 | FIXED | fewer horizontal scrollers |
| ev-work-maintenance | refused-reversed | 1440 | FIXED | tab rows changed |
| ev-work-maintenance | refused-reversed | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| ev-work-maintenance | refused-span-32d | 1440 | FIXED | tab rows changed |
| ev-work-maintenance | refused-span-32d | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| ev-work-maintenance | no-window | 1440 | PASS | No-window now defaults to the current day/week, which holds 1 work request (frozen run's DB day held none), so the table renders; the inner scrollers are the sa |
| ev-work-maintenance | no-window | 390 | PASS | No-window now defaults to the current day/week, which holds 1 work request (frozen run's DB day held none), so the table renders; the inner scrollers are the sa |
| ev-work-maintenance | all-open | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-work-maintenance | all-open | 390 | FIXED | all-disclosures-open state is exempt from closed caps (frozen B17-13 Accept; all-open exempt); ratio moved 3.32->3.59 (worstcase 7.41->7.68) only from the open  |
| ev-action | positive-current | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-action | positive-current | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-action | historical-before-intent | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-action | historical-before-intent | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-action | historical-before-action | 1440 | FIXED | h1 text changed |
| ev-action | historical-before-action | 390 | FIXED | h1 text changed |
| ev-action | not-found-404 | 1440 | FIXED | h1 text changed |
| ev-action | not-found-404 | 390 | FIXED | h1 text changed |
| ev-action | refused-reversed | 1440 | FIXED | h1 text changed; panel set changed |
| ev-action | refused-reversed | 390 | FIXED | h1 text changed; panel set changed |
| ev-action | refused-span-32d | 1440 | FIXED | h1 text changed; panel set changed |
| ev-action | refused-span-32d | 390 | FIXED | h1 text changed; panel set changed |
| ev-action | refused-bad-known-at | 1440 | FIXED | h1 text changed; 14px prose reduced |
| ev-action | refused-bad-known-at | 390 | FIXED | h1 text changed; 14px prose reduced |
| ev-action | no-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-action | no-window | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-action | all-open | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-action | all-open | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-work-incidents | store-unavailable-503 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-work-incidents | store-unavailable-503 | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-work-maintenance | store-unavailable-503 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-work-maintenance | store-unavailable-503 | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-action | store-unavailable-503 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-action | store-unavailable-503 | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-action | worstcase-positive-action | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-action | worstcase-positive-action | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-action | worstcase-160-2 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-action | worstcase-160-2 | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-action | worstcase-160-all-open | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-action | worstcase-160-all-open | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-action | worstcase-160-3 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-action | worstcase-160-3 | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-action | worstcase-160-4 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-action | worstcase-160-4 | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-action | worstcase-160-5 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-action | worstcase-160-5 | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-work-incidents | worstcase-five-160 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-work-incidents | worstcase-five-160 | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-work-incidents | worstcase-five-160-all-open | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-work-incidents | worstcase-five-160-all-open | 390 | PASS | all-disclosures-open state is exempt from closed caps (frozen B17-13 Accept; all-open exempt); ratio moved 3.04->3.29 (worstcase 6.57->6.82) only from the longe |
| ev-work-maintenance | worstcase-five-160 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-work-maintenance | worstcase-five-160 | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-work-maintenance | worstcase-five-160-all-open | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-work-maintenance | worstcase-five-160-all-open | 390 | PASS | all-disclosures-open state is exempt from closed caps (frozen B17-13 Accept; all-open exempt); ratio moved 3.32->3.59 (worstcase 7.41->7.68) only from the open  |
| ev-work-incidents | zero | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-work-incidents | zero | 390 | FIXED | fewer horizontal scrollers |
| ev-work-incidents | zero-prior-day | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-work-incidents | zero-prior-day | 390 | FIXED | fewer horizontal scrollers |
| ev-work-maintenance | zero | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-work-maintenance | zero | 390 | FIXED | fewer horizontal scrollers |
| ev-work-maintenance | zero-prior-day | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-work-maintenance | zero-prior-day | 390 | FIXED | fewer horizontal scrollers |
| ev-action | zero-mode-current | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-action | zero-mode-current | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
