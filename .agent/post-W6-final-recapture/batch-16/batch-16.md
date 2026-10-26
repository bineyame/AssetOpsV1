# Final recapture batch 16: W5 EV depth/work

Main SHA 89a11477. Pairs 88 (frozen 88). Counts: FIXED 46, PASS 42

Method: original capture tool and producers (unmodified), same ports, fresh DBs; each pair compared with the frozen evidence (panel titles, heights, rows, columns, links, chips, typography, overflow, header band, tab-row scroll, caps) and the frozen mock (unchanged). Classification derived from measured deltas plus register/rulings; standing D1/D2/D4 rows and ruled caps count as PASS. FIXED = a measured signal that a frozen D3 difference is gone.

## REGRESSION-OPEN (0)
- none

## GAP (0)
- none

## Observations
- Producer `w504_ev_work_walkthrough.py` unmodified with env W504_API_PORT_BASE=18600 (its own documented knob), `--work var/w504a_b16 --tag b16` (DBs `w504a_<mode>_b16_test`): prepare, serve, attest, drop. `unknown`/`pending`/`stale` are recorded unavailable by the producer itself (as frozen); not pairs.
- 10 capture-claim FAILs in the frozen run vs 6 now: availability/energy refused-reversed (panel count 0 vs mock, calm 'Window cannot be read' card; same as frozen) and availability 503 (same as frozen). ev-health and ev-scenarios refused-reversed no longer fail (now render panels / calm card).
- Raw UUIDs / 'c1ab7371-...' codes still appear on Health (asset ids, session id) and in the Work Actions Source cell; standing B1-53 / open register rows, not new.
- Known open regressions (EV Finding `ev-id` scroller batch 08; cold depth refused-reversed B14-01) are on other screens; not in this batch.
- Link-check phases (links/links2/links3, uncounted app-only captures) not rerun.


## All pairs
| Screen | Case | Width | Class | Why |
|---|---|---|---|---|
| ev-work | forbidden-403 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-work | forbidden-403 | 390 | FIXED | fewer horizontal scrollers |
| availability | forbidden-403 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| availability | forbidden-403 | 390 | FIXED | fewer horizontal scrollers |
| availability | current | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| availability | current | 390 | FIXED | fewer horizontal scrollers |
| energy | current | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| energy | current | 390 | FIXED | fewer horizontal scrollers |
| ev-health | current | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-health | current | 390 | FIXED | fewer horizontal scrollers |
| ev-scenarios | current | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-scenarios | current | 390 | FIXED | fewer horizontal scrollers |
| ev-work | positive | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-work | positive | 390 | FIXED | fewer horizontal scrollers |
| availability | empty-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| availability | empty-window | 390 | FIXED | fewer horizontal scrollers |
| energy | empty-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| energy | empty-window | 390 | FIXED | Import power panel +28-32 px at 390 (ratio 1.28->1.41 on empty/early-window states) is the visible 'MOCK DEVIATION D1 (R06)' label line, a standing registered D |
| ev-health | empty-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-health | empty-window | 390 | FIXED | fewer horizontal scrollers; Condition and evidence ratio 1.41->1.21 |
| ev-scenarios | empty-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-scenarios | empty-window | 390 | FIXED | fewer horizontal scrollers |
| availability | known-at-before-watermark | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| availability | known-at-before-watermark | 390 | FIXED | fewer horizontal scrollers |
| energy | known-at-before-watermark | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| energy | known-at-before-watermark | 390 | FIXED | Import power panel +28-32 px at 390 (ratio 1.28->1.41 on empty/early-window states) is the visible 'MOCK DEVIATION D1 (R06)' label line, a standing registered D |
| ev-health | known-at-before-watermark | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-health | known-at-before-watermark | 390 | FIXED | fewer horizontal scrollers; Condition and evidence ratio 1.41->1.21 |
| ev-scenarios | known-at-before-watermark | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-scenarios | known-at-before-watermark | 390 | FIXED | fewer horizontal scrollers |
| ev-work | historical | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-work | historical | 390 | FIXED | fewer horizontal scrollers |
| availability | refused-reversed | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| availability | refused-reversed | 390 | FIXED | fewer horizontal scrollers |
| energy | refused-reversed | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| energy | refused-reversed | 390 | FIXED | fewer horizontal scrollers |
| ev-health | refused-reversed | 1440 | FIXED | panel set changed |
| ev-health | refused-reversed | 390 | FIXED | fewer horizontal scrollers; panel set changed |
| ev-scenarios | refused-reversed | 1440 | FIXED | panel set changed |
| ev-scenarios | refused-reversed | 390 | FIXED | fewer horizontal scrollers; panel set changed |
| ev-work | refused-reversed | 1440 | FIXED | tab rows changed |
| ev-work | refused-reversed | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| ev-work | refused-span-32d | 1440 | FIXED | tab rows changed |
| ev-work | refused-span-32d | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| availability | no-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| availability | no-window | 390 | FIXED | fewer horizontal scrollers |
| energy | no-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| energy | no-window | 390 | FIXED | fewer horizontal scrollers |
| ev-health | no-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-health | no-window | 390 | FIXED | fewer horizontal scrollers |
| ev-scenarios | no-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-scenarios | no-window | 390 | FIXED | fewer horizontal scrollers |
| ev-work | no-window | 1440 | FIXED | tab rows changed; Actions at this site ratio 1.43->1.01; [Actions at this site] table columns changed |
| ev-work | no-window | 390 | PASS | No-window now defaults to the current week, which holds 1 Action (frozen run's DB day held 0), so the standard labelled focusable DataTable region (role=region, |
| availability | work-day-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| availability | work-day-window | 390 | FIXED | fewer horizontal scrollers |
| energy | work-day-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| energy | work-day-window | 390 | FIXED | Import power panel +28-32 px at 390 (ratio 1.28->1.41 on empty/early-window states) is the visible 'MOCK DEVIATION D1 (R06)' label line, a standing registered D |
| ev-health | work-day-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-health | work-day-window | 390 | FIXED | fewer horizontal scrollers; Condition and evidence ratio 1.41->1.21 |
| ev-scenarios | work-day-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-scenarios | work-day-window | 390 | FIXED | fewer horizontal scrollers |
| availability | all-open | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| availability | all-open | 390 | FIXED | fewer horizontal scrollers |
| energy | all-open | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| energy | all-open | 390 | FIXED | Import power panel +28-32 px at 390 (ratio 1.28->1.41 on empty/early-window states) is the visible 'MOCK DEVIATION D1 (R06)' label line, a standing registered D |
| ev-health | all-open | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-health | all-open | 390 | FIXED | fewer horizontal scrollers |
| ev-scenarios | all-open | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-scenarios | all-open | 390 | FIXED | fewer horizontal scrollers |
| ev-work | all-open | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-work | all-open | 390 | FIXED | fewer horizontal scrollers |
| ev-work | store-unavailable-503 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-work | store-unavailable-503 | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| availability | store-unavailable-503 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| availability | store-unavailable-503 | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-work | worstcase | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-work | worstcase | 390 | FIXED | fewer horizontal scrollers |
| ev-work | worstcase-all-open | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-work | worstcase-all-open | 390 | FIXED | fewer horizontal scrollers |
| ev-health | worstcase-db | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-health | worstcase-db | 390 | FIXED | fewer horizontal scrollers |
| ev-scenarios | worstcase-db | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-scenarios | worstcase-db | 390 | FIXED | fewer horizontal scrollers |
| ev-work | zero | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-work | zero | 390 | FIXED | fewer horizontal scrollers |
| ev-work | zero-mode-current-day | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-work | zero-mode-current-day | 390 | FIXED | fewer horizontal scrollers |
