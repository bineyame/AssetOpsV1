# Final recapture batch 14: W5 cold depth/work

Main SHA 89a11477. Pairs 88 (frozen 88). Counts: FIXED 44, PASS 38, REGRESSION-OPEN 6

Method: original capture tool and producers (unmodified), same ports, fresh DBs; each pair compared with the frozen evidence (panel titles, heights, rows, columns, links, chips, typography, overflow, header band, tab-row scroll, caps) and the frozen mock (unchanged). Classification derived from measured deltas plus register/rulings; standing D1/D2/D4 rows and ruled caps count as PASS. FIXED = a measured signal that a frozen D3 difference is gone.

## REGRESSION-OPEN (6)
- cooling / refused-reversed / 1440: Frozen D3 B14-01 persists: refused window (from after to) renders the card 'Cold depth/Cold scenarios unavailable' with the raw code text "COLD_WINDOW_INVALID 'from' must be before 'to'." and a Retry that cannot succeed; strip, cards and all mock panels are dropped (0 vs 1-3 panels); no window control. Register R244/R261 read closed but their Q13 split left cold depth (W5-cold-Work) and the one-refusal-set copy was not applied here (cold-work was fixed, R461). Suspected cause: cold depth refusal path (ColdCooling/ColdHealthDepth/cold scenarios error branch) still prints the server code and message verbatim (evidence positive/cooling-refused-reversed-1440-app.png)
- cooling / refused-reversed / 390: Frozen D3 B14-01 persists: refused window (from after to) renders the card 'Cold depth/Cold scenarios unavailable' with the raw code text "COLD_WINDOW_INVALID 'from' must be before 'to'." and a Retry that cannot succeed; strip, cards and all mock panels are dropped (0 vs 1-3 panels); no window control. Register R244/R261 read closed but their Q13 split left cold depth (W5-cold-Work) and the one-refusal-set copy was not applied here (cold-work was fixed, R461). Suspected cause: cold depth refusal path (ColdCooling/ColdHealthDepth/cold scenarios error branch) still prints the server code and message verbatim (evidence positive/cooling-refused-reversed-390-app.png)
- cold-health / refused-reversed / 1440: Frozen D3 B14-01 persists: refused window (from after to) renders the card 'Cold depth/Cold scenarios unavailable' with the raw code text "COLD_WINDOW_INVALID 'from' must be before 'to'." and a Retry that cannot succeed; strip, cards and all mock panels are dropped (0 vs 1-3 panels); no window control. Register R244/R261 read closed but their Q13 split left cold depth (W5-cold-Work) and the one-refusal-set copy was not applied here (cold-work was fixed, R461). Suspected cause: cold depth refusal path (ColdCooling/ColdHealthDepth/cold scenarios error branch) still prints the server code and message verbatim (evidence positive/cold-health-refused-reversed-1440-app.png)
- cold-health / refused-reversed / 390: Frozen D3 B14-01 persists: refused window (from after to) renders the card 'Cold depth/Cold scenarios unavailable' with the raw code text "COLD_WINDOW_INVALID 'from' must be before 'to'." and a Retry that cannot succeed; strip, cards and all mock panels are dropped (0 vs 1-3 panels); no window control. Register R244/R261 read closed but their Q13 split left cold depth (W5-cold-Work) and the one-refusal-set copy was not applied here (cold-work was fixed, R461). Suspected cause: cold depth refusal path (ColdCooling/ColdHealthDepth/cold scenarios error branch) still prints the server code and message verbatim (evidence positive/cold-health-refused-reversed-390-app.png)
- cold-scenarios / refused-reversed / 1440: Frozen D3 B14-01 persists: refused window (from after to) renders the card 'Cold depth/Cold scenarios unavailable' with the raw code text "COLD_WINDOW_INVALID 'from' must be before 'to'." and a Retry that cannot succeed; strip, cards and all mock panels are dropped (0 vs 1-3 panels); no window control. Register R244/R261 read closed but their Q13 split left cold depth (W5-cold-Work) and the one-refusal-set copy was not applied here (cold-work was fixed, R461). Suspected cause: cold depth refusal path (ColdCooling/ColdHealthDepth/cold scenarios error branch) still prints the server code and message verbatim (evidence positive/cold-scenarios-refused-reversed-1440-app.png)
- cold-scenarios / refused-reversed / 390: Frozen D3 B14-01 persists: refused window (from after to) renders the card 'Cold depth/Cold scenarios unavailable' with the raw code text "COLD_WINDOW_INVALID 'from' must be before 'to'." and a Retry that cannot succeed; strip, cards and all mock panels are dropped (0 vs 1-3 panels); no window control. Register R244/R261 read closed but their Q13 split left cold depth (W5-cold-Work) and the one-refusal-set copy was not applied here (cold-work was fixed, R461). Suspected cause: cold depth refusal path (ColdCooling/ColdHealthDepth/cold scenarios error branch) still prints the server code and message verbatim (evidence positive/cold-scenarios-refused-reversed-390-app.png)

## GAP (0)
- none

## Run record
- W5-02b walkthrough `tools/w502_cold_work_walkthrough.py --work var/w502b_b14 --tag b14` unmodified: prepare (DBs w502b_{positive,worstcase,pending,stale,unknown}_b14_test), serve (API 8971-8977), then drop. Vite 5184 on localhost restarted per mode with ASSETOPS_API_PORT (started plainly via npm.cmd, no policy override), CDP 9524. Targets from the walkthrough manifest (windows 23 Oct 16:00-17:05Z; work windows from the manifest).
- Claims: positive 294/300 (same 6 refused-reversed 'same panel count' failures as frozen), links 48/48 (uncounted), worstcase 24/24, pending 84/84, stale 48/48, unknown 48/48, forbidden 12/12, unavailable 12/12.
- 88 pairs = positive 50 + pending 14 + stale 8 + unknown 8 + worstcase 4 + forbidden 2 + unavailable 2.
- Observation (not counted, frozen B14-05 -> B1-53 cite): cooling Recovery curves table prints full evidence UUIDs (selected-point table); cold-health asset ids are now collapsed behind 'Full ID'.
- Standing: cooling chart scroller at 390 (480 in 318, labelled by visible scrollbar), cold-work tables scroll at 390 with scrollbar and 'Next page'/'Show all' controls, two-line clamps with 'Read full text'.
- 390 screenshots viewed: cold-work no-window/worstcase/forbidden/unavailable/span-32d, cooling empty-window/pending/refused-reversed, cold-health current-limited/refused-reversed, cold-scenarios current-limited; 1440 cold-scenarios refused. No cut text, no document overflow, no console errors, no new inner scrollers.
- Uncounted link check (xcheck-links.json): cold Site Findings table scroller (1125 in 1120 at 1440, 949 in 318 at 390, data-table__scroll) is new vs the frozen link check; likely the intended table scroller, not a pair, not classified.

## All pairs
| Screen | Case | Width | Class | Why |
|---|---|---|---|---|
| cold-work | forbidden-403 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work | forbidden-403 | 390 | FIXED | fewer horizontal scrollers |
| cooling | pending | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cooling | pending | 390 | FIXED | fewer horizontal scrollers |
| cold-health | pending | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-health | pending | 390 | FIXED | fewer horizontal scrollers |
| cold-scenarios | pending | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-scenarios | pending | 390 | FIXED | fewer horizontal scrollers |
| cooling | historical | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cooling | historical | 390 | FIXED | fewer horizontal scrollers |
| cold-health | historical | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-health | historical | 390 | FIXED | fewer horizontal scrollers |
| cold-scenarios | historical | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-scenarios | historical | 390 | FIXED | fewer horizontal scrollers |
| cold-work | pending | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work | pending | 390 | FIXED | fewer horizontal scrollers |
| cooling | current-limited | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cooling | current-limited | 390 | FIXED | fewer horizontal scrollers |
| cold-health | current-limited | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-health | current-limited | 390 | FIXED | fewer horizontal scrollers |
| cold-scenarios | current-limited | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-scenarios | current-limited | 390 | FIXED | fewer horizontal scrollers |
| cold-work | positive | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work | positive | 390 | FIXED | fewer horizontal scrollers |
| cooling | empty-window | 1440 | FIXED | [Recovery curves] table columns changed |
| cooling | empty-window | 390 | PASS | Recovery curves 412 px vs mock 235 (1.75x) = standing D1 R335 (chart plus accessible selected-point table); frozen 236 px had no table |
| cold-health | empty-window | 1440 | FIXED | Condition and evidence ratio 1.44->1.27 |
| cold-health | empty-window | 390 | FIXED | fewer horizontal scrollers |
| cold-scenarios | empty-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-scenarios | empty-window | 390 | FIXED | fewer horizontal scrollers |
| cold-work | zero | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work | zero | 390 | FIXED | fewer horizontal scrollers |
| cold-work | historical | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work | historical | 390 | FIXED | fewer horizontal scrollers |
| cooling | refused-reversed | 1440 | REGRESSION-OPEN | Frozen D3 B14-01 persists: refused window (from after to) renders the card 'Cold depth/Cold scenarios unavailable' with the raw code text "COLD_WINDOW_INVALID ' |
| cooling | refused-reversed | 390 | REGRESSION-OPEN | Frozen D3 B14-01 persists: refused window (from after to) renders the card 'Cold depth/Cold scenarios unavailable' with the raw code text "COLD_WINDOW_INVALID ' |
| cold-health | refused-reversed | 1440 | REGRESSION-OPEN | Frozen D3 B14-01 persists: refused window (from after to) renders the card 'Cold depth/Cold scenarios unavailable' with the raw code text "COLD_WINDOW_INVALID ' |
| cold-health | refused-reversed | 390 | REGRESSION-OPEN | Frozen D3 B14-01 persists: refused window (from after to) renders the card 'Cold depth/Cold scenarios unavailable' with the raw code text "COLD_WINDOW_INVALID ' |
| cold-scenarios | refused-reversed | 1440 | REGRESSION-OPEN | Frozen D3 B14-01 persists: refused window (from after to) renders the card 'Cold depth/Cold scenarios unavailable' with the raw code text "COLD_WINDOW_INVALID ' |
| cold-scenarios | refused-reversed | 390 | REGRESSION-OPEN | Frozen D3 B14-01 persists: refused window (from after to) renders the card 'Cold depth/Cold scenarios unavailable' with the raw code text "COLD_WINDOW_INVALID ' |
| cold-work | refused-reversed | 1440 | FIXED | tab rows changed |
| cold-work | refused-reversed | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| cold-work | refused-span-32d | 1440 | FIXED | tab rows changed |
| cold-work | refused-span-32d | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| cooling | no-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cooling | no-window | 390 | FIXED | fewer horizontal scrollers |
| cold-health | no-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-health | no-window | 390 | FIXED | fewer horizontal scrollers |
| cold-scenarios | no-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-scenarios | no-window | 390 | FIXED | fewer horizontal scrollers |
| cold-work | no-window | 1440 | FIXED | default seven-day window (R338) now lists the Action row instead of the frozen empty state; Site tab row wraps at 390; 390 table scroller (822 in 318, sticky he |
| cold-work | no-window | 390 | FIXED | default seven-day window (R338) now lists the Action row instead of the frozen empty state; Site tab row wraps at 390; 390 table scroller (822 in 318, sticky he |
| cooling | work-day-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cooling | work-day-window | 390 | FIXED | fewer horizontal scrollers |
| cold-health | work-day-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-health | work-day-window | 390 | FIXED | fewer horizontal scrollers |
| cold-scenarios | work-day-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-scenarios | work-day-window | 390 | FIXED | fewer horizontal scrollers |
| cooling | all-open | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cooling | all-open | 390 | FIXED | fewer horizontal scrollers |
| cold-health | all-open | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-health | all-open | 390 | FIXED | fewer horizontal scrollers |
| cold-scenarios | all-open | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-scenarios | all-open | 390 | FIXED | fewer horizontal scrollers |
| cold-work | all-open | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work | all-open | 390 | FIXED | fewer horizontal scrollers |
| cooling | stale | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cooling | stale | 390 | FIXED | fewer horizontal scrollers |
| cold-health | stale | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-health | stale | 390 | FIXED | fewer horizontal scrollers |
| cold-scenarios | stale | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-scenarios | stale | 390 | FIXED | fewer horizontal scrollers |
| cold-work | stale | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work | stale | 390 | FIXED | fewer horizontal scrollers |
| cold-work | store-unavailable-503 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work | store-unavailable-503 | 390 | FIXED | fewer horizontal scrollers |
| cooling | unknown | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cooling | unknown | 390 | FIXED | fewer horizontal scrollers |
| cold-health | unknown | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-health | unknown | 390 | FIXED | fewer horizontal scrollers |
| cold-scenarios | unknown | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-scenarios | unknown | 390 | FIXED | fewer horizontal scrollers |
| cold-work | unknown | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work | unknown | 390 | FIXED | fewer horizontal scrollers |
| cold-work | worstcase | 1440 | PASS | identical to frozen: intended two-line clamp on five 160-char rows, each carrying 'Read full text' (1 px width delta only) |
| cold-work | worstcase | 390 | PASS | identical to frozen: intended two-line clamp on five 160-char rows, each carrying 'Read full text' (1 px width delta only) |
| cold-work | worstcase-all-open | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work | worstcase-all-open | 390 | FIXED | fewer horizontal scrollers |
