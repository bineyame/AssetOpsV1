# Final recapture batch 05: W1 verification

Main SHA 89a11477. Pairs 26 (frozen 26). Counts: FIXED 22, PASS 4

Method: original capture tool and producers (unmodified), same ports, fresh DBs; each pair compared with the frozen evidence (panel titles, heights, rows, columns, links, chips, typography, overflow, header band, tab-row scroll, caps) and the frozen mock (unchanged). Classification derived from measured deltas plus register/rulings; standing D1/D2/D4 rows and ruled caps count as PASS. FIXED = a measured signal that a frozen D3 difference is gone.

## REGRESSION-OPEN (0)
- none

## GAP (0)
- none

## Notes for the coordinator
- Producers s603 (assetops_s603_owner_audit) and s602b (assetops_s602b_audit + 4 case DBs; replay plus `serve --case` per case) ran unmodified; Vite 5185, CDP 9525; DBs dropped, var/ removed, servers stopped by PID. Action and outcome ids were re-mapped by role from the producers' own `links` output; the s602b replay was re-prepared once and the same record roles were used.
- FIXED signal on all verification pairs: the duplicate Site tab row above the Action tabs is gone (frozen B5-01), and at 390 the tab row no longer scrolls horizontally. Sitework invalid-window: Incidents/Maintenance tabs no longer show a count dash.
- Caps unchanged from frozen: Activity/Outcome evidence 1.34-1.43x (1440), sitework Actions table 1.36x/1.65x, all under the W1-F5b overage rulings.
- Console errors none; no overflow; no new raw vocabulary.

## All pairs
| Screen | Case | Width | Class | Why |
|---|---|---|---|---|
| verification | guardrail | 1440 | FIXED | tab rows changed |
| verification | guardrail | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| verification | inconclusive | 1440 | FIXED | tab rows changed |
| verification | inconclusive | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| verification | target_miss | 1440 | FIXED | tab rows changed |
| verification | target_miss | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| verification | withdrawn | 1440 | FIXED | tab rows changed |
| verification | withdrawn | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| verification | verified-current | 1440 | FIXED | tab rows changed |
| verification | verified-current | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| verification | historical-outcome | 1440 | FIXED | tab rows changed |
| verification | historical-outcome | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| verification | selector-conflict | 1440 | FIXED | tab rows changed |
| verification | selector-conflict | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| verification | unknown-action | 1440 | FIXED | tab rows changed |
| verification | unknown-action | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| sitework | positive | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| sitework | positive | 390 | FIXED | fewer horizontal scrollers |
| sitework | page1-limit1 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| sitework | page1-limit1 | 390 | FIXED | fewer horizontal scrollers |
| sitework | zero | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| sitework | zero | 390 | FIXED | fewer horizontal scrollers |
| sitework | no-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| sitework | no-window | 390 | FIXED | fewer horizontal scrollers |
| sitework | invalid-window | 1440 | FIXED | tab rows changed |
| sitework | invalid-window | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
