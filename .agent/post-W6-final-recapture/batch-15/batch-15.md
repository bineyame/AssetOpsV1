# Final recapture batch 15: W5 cold cases/Action

Main SHA 89a11477. Pairs 88 (frozen 88). Counts: FIXED 38, PASS 50

Method: original capture tool and producers (unmodified), same ports, fresh DBs; each pair compared with the frozen evidence (panel titles, heights, rows, columns, links, chips, typography, overflow, header band, tab-row scroll, caps) and the frozen mock (unchanged). Classification derived from measured deltas plus register/rulings; standing D1/D2/D4 rows and ruled caps count as PASS. FIXED = a measured signal that a frozen D3 difference is gone.

## REGRESSION-OPEN (0)
- none

## GAP (0)
- none

## Run record
- W5-02b walkthrough `tools/w502_cold_work_walkthrough.py --work var/w502b_b15 --tag b15` unmodified: prepare (DBs w502b_*_b15_test, none blocked), serve (API 8971-8977, 7 healthy), attest (ATTEST OK), then drop. Vite 5185 on localhost restarted per mode with ASSETOPS_API_PORT (plain npm.cmd start, no policy override), CDP 9525. Targets from the walkthrough manifest.
- Claims: positive 270/276 (same 6 cold-action state-panel failures as frozen, R101: one untitled panel vs mock's 2), worstcase 72/72, pending 36/36, stale 36/36, unknown 36/36, forbidden 34/36 and unavailable 34/36 (same cold-action state panel). Unavailable was warmed up first with an uncounted navigation pass in /tmp (frozen run had the same compile blank, B15-13).
- 88 pairs = positive 46 + worstcase 12 + pending/stale/unknown/forbidden/unavailable 6 each.
- Standing/ruled inner scrollers, no new ones: case tables at 390 (data-table__scroll, visible scrollbar + 'Scroll the table' hint), one-line UUID scrollers inside the opened 'UTC and IDs' disclosure (W5-02c ruling 14), cold-action disclosure bodies. Two-line clamps carry 'Read full text'.
- 390 screenshots viewed: cold-action positive/not-found/invalid-known-at/worstcase, cold-work-maintenance no-window, cold-work-incidents worstcase. No cut text, no document overflow, no console errors.
- Not producible (as frozen B15-10): cold-action Related-activity for linked OPEN/IN_PROGRESS/CANCELLED requests; not counted as GAP (never reachable by this producer).

## All pairs
| Screen | Case | Width | Class | Why |
|---|---|---|---|---|
| cold-work-incidents | forbidden-403 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work-incidents | forbidden-403 | 390 | FIXED | fewer horizontal scrollers |
| cold-work-maintenance | forbidden-403 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work-maintenance | forbidden-403 | 390 | FIXED | fewer horizontal scrollers |
| cold-action | forbidden-403 | 1440 | FIXED | 14px prose reduced |
| cold-action | forbidden-403 | 390 | FIXED | 14px prose reduced |
| cold-work-incidents | pending | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work-incidents | pending | 390 | FIXED | fewer horizontal scrollers |
| cold-work-maintenance | pending | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work-maintenance | pending | 390 | FIXED | fewer horizontal scrollers |
| cold-action | pending | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-action | pending | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work-incidents | current | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work-incidents | current | 390 | FIXED | fewer horizontal scrollers |
| cold-work-incidents | positive-cutoff | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work-incidents | positive-cutoff | 390 | FIXED | fewer horizontal scrollers |
| cold-work-incidents | historical | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work-incidents | historical | 390 | FIXED | fewer horizontal scrollers |
| cold-work-incidents | zero | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work-incidents | zero | 390 | FIXED | fewer horizontal scrollers |
| cold-work-incidents | refused-reversed | 1440 | FIXED | tab rows changed |
| cold-work-incidents | refused-reversed | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| cold-work-incidents | refused-span-32d | 1440 | FIXED | tab rows changed |
| cold-work-incidents | refused-span-32d | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| cold-work-incidents | no-window | 1440 | FIXED | tab rows changed |
| cold-work-incidents | no-window | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| cold-work-incidents | all-open | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work-incidents | all-open | 390 | FIXED | all-disclosures-open state is exempt from closed caps (post-W6-W2-cold-rulings Q8, K3/K4 caps) and stays readable and unclipped at 390 (screens checked); Site t |
| cold-work-maintenance | current | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work-maintenance | current | 390 | FIXED | fewer horizontal scrollers |
| cold-work-maintenance | positive-cutoff | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work-maintenance | positive-cutoff | 390 | FIXED | fewer horizontal scrollers |
| cold-work-maintenance | historical | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work-maintenance | historical | 390 | FIXED | fewer horizontal scrollers |
| cold-work-maintenance | zero | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work-maintenance | zero | 390 | FIXED | fewer horizontal scrollers |
| cold-work-maintenance | refused-reversed | 1440 | FIXED | tab rows changed |
| cold-work-maintenance | refused-reversed | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| cold-work-maintenance | refused-span-32d | 1440 | FIXED | tab rows changed |
| cold-work-maintenance | refused-span-32d | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| cold-work-maintenance | no-window | 1440 | FIXED | default seven-day window (R338) now lists the request instead of the frozen empty state; ratio 1.73->1.16 (1440), 1.41->0.87 (390); the fact-list__value and 390 |
| cold-work-maintenance | no-window | 390 | FIXED | default seven-day window (R338) now lists the request instead of the frozen empty state; ratio 1.73->1.16 (1440), 1.41->0.87 (390); the fact-list__value and 390 |
| cold-work-maintenance | all-open | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work-maintenance | all-open | 390 | FIXED | all-disclosures-open state is exempt from closed caps (post-W6-W2-cold-rulings Q8, K3/K4 caps) and stays readable and unclipped at 390 (screens checked); Site t |
| cold-action | positive | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-action | positive | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-action | all-open | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-action | all-open | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-action | not-linked | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-action | not-linked | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-action | historical | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-action | historical | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-action | not-found | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-action | not-found | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-action | invalid-known-at | 1440 | FIXED | 14px prose reduced |
| cold-action | invalid-known-at | 390 | FIXED | 14px prose reduced |
| cold-action | future-known-at | 1440 | FIXED | 14px prose reduced |
| cold-action | future-known-at | 390 | FIXED | 14px prose reduced |
| cold-work-incidents | stale | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work-incidents | stale | 390 | FIXED | fewer horizontal scrollers |
| cold-work-maintenance | stale | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work-maintenance | stale | 390 | FIXED | fewer horizontal scrollers |
| cold-action | stale | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-action | stale | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work-incidents | unavailable-503 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work-incidents | unavailable-503 | 390 | FIXED | fewer horizontal scrollers |
| cold-work-maintenance | unavailable-503 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work-maintenance | unavailable-503 | 390 | FIXED | fewer horizontal scrollers |
| cold-action | unavailable-503 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-action | unavailable-503 | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work-incidents | unknown | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work-incidents | unknown | 390 | FIXED | fewer horizontal scrollers |
| cold-work-maintenance | unknown | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work-maintenance | unknown | 390 | FIXED | fewer horizontal scrollers |
| cold-action | unknown | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-action | unknown | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work-incidents | worstcase | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work-incidents | worstcase | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work-incidents | worstcase-all-open | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work-incidents | worstcase-all-open | 390 | PASS | all-disclosures-open state is exempt from closed caps (post-W6-W2-cold-rulings Q8, K3/K4 caps) and stays readable and unclipped at 390 (screens checked) |
| cold-work-maintenance | worstcase | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work-maintenance | worstcase | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work-maintenance | worstcase-all-open | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-work-maintenance | worstcase-all-open | 390 | PASS | all-disclosures-open state is exempt from closed caps (post-W6-W2-cold-rulings Q8, K3/K4 caps) and stays readable and unclipped at 390 (screens checked) |
| cold-action | worstcase | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-action | worstcase | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-action | worstcase-all-open | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-action | worstcase-all-open | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
