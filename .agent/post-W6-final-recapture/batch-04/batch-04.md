# Final recapture batch 04: W1 Action/work

Main SHA 89a11477. Pairs 50 (frozen 50). Counts: FIXED 50

Method: original capture tool and producers (unmodified), same ports, fresh DBs; each pair compared with the frozen evidence (panel titles, heights, rows, columns, links, chips, typography, overflow, header band, tab-row scroll, caps) and the frozen mock (unchanged). Classification derived from measured deltas plus register/rulings; standing D1/D2/D4 rows and ruled caps count as PASS. FIXED = a measured signal that a frozen D3 difference is gone.

## REGRESSION-OPEN (0)
- none

## GAP (0)
- none

## Notes for the coordinator
- Producers s601b (assetops_s601b_audit, var/s601b_audit) and s602b (assetops_s602b_audit + 4 case DBs, serve --case guardrail on 18401/18402) ran unmodified on Vite 5184, CDP 9524; all dropped, Vite stopped. Record IDs were re-mapped by role (accepted revision, F02 action, FAILED/STALE event, OBSERVED event, plan, guardrail case) from the producers' own walkthrough.json / replay.json / cases.json.
- OBSERVATION (classified PASS under open D2 row R217, but worth an explicit ruling): the action-history pages still show raw failure codes (ACTION_VALUE_INVALID, ACTION_EFFECTIVE_TIME_INVALID) and ellipsized monospace ids ('4eba0044-5...', 'change record 55ce756c-2...') in the Meaning column; see s601b/action-history-all-1440-app.png and -event-failed-stale-1440-app.png. The Q15 copy mapping (for example 'The proposed value was outside the allowed range') is not applied on these history rows. R217 lists them inside its D2 text, so they are not a new difference, but they are raw system vocabulary/UUIDs on a client-facing page.
- Caps: Action overview Action scope 1.37-1.43x/2.05-2.40x, Activity log 1.53-1.73x/2.69-2.90x, Success criteria / Evidence requirements 1.38-1.51x, recommendation Proposed intervention up to 1.55x at 390 are unchanged from the frozen capture (standing D1/D2 rows R215-R217).

## All pairs
| Screen | Case | Width | Class | Why |
|---|---|---|---|---|
| recommendation | accepted | 1440 | FIXED | h1 text changed; tab rows changed |
| recommendation | accepted | 390 | FIXED | h1 text changed; tab rows changed; fewer horizontal scrollers |
| recommendation | latest-trial-open | 1440 | FIXED | h1 text changed; tab rows changed |
| recommendation | latest-trial-open | 390 | FIXED | h1 text changed; tab rows changed; fewer horizontal scrollers |
| recommendation | unavailable | 1440 | FIXED | h1 text changed; tab rows changed |
| recommendation | unavailable | 390 | FIXED | h1 text changed; tab rows changed; fewer horizontal scrollers |
| action-overview | recorded | 1440 | FIXED | tab rows changed |
| action-overview | recorded | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| action-overview | pending-f02 | 1440 | FIXED | tab rows changed |
| action-overview | pending-f02 | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| action-overview | unknown-section | 1440 | FIXED | tab rows changed |
| action-overview | unknown-section | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| action-execution | applied | 1440 | FIXED | tab rows changed |
| action-execution | applied | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| action-execution | failed-pending | 1440 | FIXED | tab rows changed |
| action-execution | failed-pending | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| action-history | all | 1440 | FIXED | tab rows changed |
| action-history | all | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| action-history | event-failed-stale | 1440 | FIXED | tab rows changed |
| action-history | event-failed-stale | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| action-history | recorded-at | 1440 | FIXED | tab rows changed |
| action-history | recorded-at | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| action-history | selector-conflict | 1440 | FIXED | tab rows changed |
| action-history | selector-conflict | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| action-plan | pre-plan-s601b | 1440 | FIXED | tab rows changed |
| action-plan | pre-plan-s601b | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| action-evidence | pre-plan-s601b | 1440 | FIXED | tab rows changed |
| action-evidence | pre-plan-s601b | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| action-plan | guardrail | 1440 | FIXED | tab rows changed |
| action-plan | guardrail | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| action-evidence | guardrail | 1440 | FIXED | tab rows changed |
| action-evidence | guardrail | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| action-overview | guardrail | 1440 | FIXED | tab rows changed |
| action-overview | guardrail | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| recommendation | guardrail-hold | 1440 | FIXED | h1 text changed; tab rows changed |
| recommendation | guardrail-hold | 390 | FIXED | h1 text changed; tab rows changed; fewer horizontal scrollers |
| recommendation | verified-replay | 1440 | FIXED | h1 text changed; tab rows changed |
| recommendation | verified-replay | 390 | FIXED | h1 text changed; tab rows changed; fewer horizontal scrollers |
| action-overview | verified-replay | 1440 | FIXED | tab rows changed |
| action-overview | verified-replay | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| action-execution | verified-replay | 1440 | FIXED | tab rows changed |
| action-execution | verified-replay | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| action-history | verified-replay | 1440 | FIXED | B4-19/R218 closed: the duplicated raw 'RESOLVED' row with the wrong 'Trial accepted' meaning is gone (now 'Applied to the Site Foundation' / 'Trial outcome reco |
| action-history | verified-replay | 390 | FIXED | B4-19/R218 closed (duplicate raw RESOLVED row gone, counts consistent); Action history ratio 2.42->2.06, inside the Q37 800 px cap; truncated change-record ids  |
| action-plan | pass | 1440 | FIXED | tab rows changed |
| action-plan | pass | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| action-plan | exact-plan | 1440 | FIXED | tab rows changed |
| action-plan | exact-plan | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| action-evidence | pass | 1440 | FIXED | tab rows changed |
| action-evidence | pass | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
