# Final recapture batch 07: W2 cold Site

Main SHA 89a11477. Pairs 60 (frozen 60). Counts: FIXED 36, PASS 24

Method: original capture tool and producers (unmodified), same ports, fresh DBs; each pair compared with the frozen evidence (panel titles, heights, rows, columns, links, chips, typography, overflow, header band, tab-row scroll, caps) and the frozen mock (unchanged). Classification derived from measured deltas plus register/rulings; standing D1/D2/D4 rows and ruled caps count as PASS. FIXED = a measured signal that a frozen D3 difference is gone.

## REGRESSION-OPEN (0)
- none

## GAP (0)
- none

## Notes for the coordinator
- Producer `.agent/W2-F-evidence/seed.py` (unmodified; cold excursion, then cold normal; `ASSETOPS_TEST_TEMPLATE=0`) against `assetops_audit_b07_test` (created by me, dropped at the end). API 18701 restarted per phase, Vite 5187, CDP 9527. Record ids are deterministic and equal the frozen ids; frozen targets reused.
- FIXED signals: cold-findings now renders the mini-grid-style Findings table (Finding, Domain, Priority, Confidence, State, Main consequence, Lens) with 2 rows in stocked/no-window states, and a short empty/refused state otherwise (frozen B7-01 index missing; panel ratios 1.31-1.35 -> 0.39-0.96); the Accepted-records table columns changed on cold-evidence-analysis; tab row no longer scrolls at 390 (28 pairs).
- Observation: refused states on cold, cold-evidence, cold-evidence-analysis, cold-financials, cold-assumptions gained a collapsed details disclosure (96/119 -> 113/136 px at 1440, up to 152-170 px at 390); the Chamber temperature panel gained one link. Not overflow or cap breaches.
- No horizontal page overflow, no console errors, no new raw vocabulary.

## All pairs
| Screen | Case | Width | Class | Why |
|---|---|---|---|---|
| cold-findings | stocked | 1440 | FIXED | [Findings at this site] table columns changed |
| cold-findings | stocked | 390 | FIXED | Findings at this site ratio 1.31->0.96; [Findings at this site] table columns changed |
| cold-findings | no-selection | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-findings | no-selection | 390 | FIXED | fewer horizontal scrollers; Findings at this site ratio 1.31->0.42 |
| cold-findings | refused | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-findings | refused | 390 | FIXED | fewer horizontal scrollers; Findings at this site ratio 1.35->0.39 |
| cold-findings | no-window | 1440 | FIXED | [Findings at this site] table columns changed |
| cold-findings | no-window | 390 | FIXED | Findings at this site ratio 1.31->0.96; [Findings at this site] table columns changed |
| cold | stocked | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold | stocked | 390 | FIXED | fewer horizontal scrollers |
| cold | no-selection | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold | no-selection | 390 | FIXED | fewer horizontal scrollers |
| cold | refused | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold | refused | 390 | FIXED | fewer horizontal scrollers |
| cold | no-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold | no-window | 390 | FIXED | fewer horizontal scrollers |
| cold-evidence | stocked | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-evidence | stocked | 390 | FIXED | fewer horizontal scrollers |
| cold-evidence | no-selection | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-evidence | no-selection | 390 | FIXED | fewer horizontal scrollers |
| cold-evidence | refused | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-evidence | refused | 390 | FIXED | fewer horizontal scrollers |
| cold-evidence | no-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-evidence | no-window | 390 | FIXED | fewer horizontal scrollers |
| cold-evidence-analysis | stocked | 1440 | FIXED | [Accepted records behind the conclusions] table columns changed |
| cold-evidence-analysis | stocked | 390 | FIXED | fewer horizontal scrollers; [Accepted records behind the conclusions] table columns changed |
| cold-evidence-analysis | no-selection | 1440 | FIXED | [Accepted records behind the conclusions] table columns changed |
| cold-evidence-analysis | no-selection | 390 | FIXED | fewer horizontal scrollers; [Accepted records behind the conclusions] table columns changed |
| cold-evidence-analysis | refused | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-evidence-analysis | refused | 390 | FIXED | fewer horizontal scrollers |
| cold-evidence-analysis | no-window | 1440 | FIXED | [Accepted records behind the conclusions] table columns changed |
| cold-evidence-analysis | no-window | 390 | FIXED | fewer horizontal scrollers; [Accepted records behind the conclusions] table columns changed |
| cold-financials | stocked | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-financials | stocked | 390 | FIXED | fewer horizontal scrollers |
| cold-financials | no-selection | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-financials | no-selection | 390 | FIXED | fewer horizontal scrollers |
| cold-financials | refused | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-financials | refused | 390 | FIXED | fewer horizontal scrollers |
| cold-financials | no-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-financials | no-window | 390 | FIXED | fewer horizontal scrollers |
| cold-assumptions | stocked | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-assumptions | stocked | 390 | FIXED | fewer horizontal scrollers |
| cold-assumptions | no-selection | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-assumptions | no-selection | 390 | FIXED | fewer horizontal scrollers |
| cold-assumptions | refused | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-assumptions | refused | 390 | FIXED | fewer horizontal scrollers |
| cold-assumptions | no-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-assumptions | no-window | 390 | FIXED | fewer horizontal scrollers |
| cold-findings | normal | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-findings | normal | 390 | FIXED | fewer horizontal scrollers; Findings at this site ratio 1.31->0.42 |
| cold | normal | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold | normal | 390 | FIXED | fewer horizontal scrollers |
| cold-evidence | normal | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-evidence | normal | 390 | FIXED | fewer horizontal scrollers |
| cold-evidence-analysis | normal | 1440 | FIXED | [Accepted records behind the conclusions] table columns changed |
| cold-evidence-analysis | normal | 390 | FIXED | fewer horizontal scrollers; [Accepted records behind the conclusions] table columns changed |
| cold-financials | normal | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-financials | normal | 390 | FIXED | fewer horizontal scrollers |
| cold-assumptions | normal | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-assumptions | normal | 390 | FIXED | fewer horizontal scrollers |
