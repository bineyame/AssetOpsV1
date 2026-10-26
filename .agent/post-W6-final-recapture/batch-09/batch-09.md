# Final recapture batch 09: W2 EV Site

Main SHA 89a11477. Pairs 50 (frozen 50). Counts: FIXED 32, PASS 18

Method: original capture tool and producers (unmodified), same ports, fresh DBs; each pair compared with the frozen evidence (panel titles, heights, rows, columns, links, chips, typography, overflow, header band, tab-row scroll, caps) and the frozen mock (unchanged). Classification derived from measured deltas plus register/rulings; standing D1/D2/D4 rows and ruled caps count as PASS. FIXED = a measured signal that a frozen D3 difference is gone.

## REGRESSION-OPEN (0)
- none

## GAP (0)
- none

## All pairs
| Screen | Case | Width | Class | Why |
|---|---|---|---|---|
| ev | complete | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev | complete | 390 | FIXED | fewer horizontal scrollers |
| ev-evidence | complete | 1440 | FIXED | 14px prose reduced |
| ev-evidence | complete | 390 | FIXED | 14px prose reduced; fewer horizontal scrollers |
| ev-evidence-analysis | complete | 1440 | FIXED | [Accepted records behind the conclusions] table columns changed |
| ev-evidence-analysis | complete | 390 | FIXED | fewer horizontal scrollers; [Accepted records behind the conclusions] table columns changed |
| ev-financials | complete | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-financials | complete | 390 | FIXED | fewer horizontal scrollers |
| ev-assumptions | complete | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-assumptions | complete | 390 | FIXED | fewer horizontal scrollers |
| ev | interrupted | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev | interrupted | 390 | FIXED | fewer horizontal scrollers |
| ev | no-selection | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev | no-selection | 390 | FIXED | fewer horizontal scrollers |
| ev | refused | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev | refused | 390 | FIXED | fewer horizontal scrollers |
| ev | no-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev | no-window | 390 | FIXED | fewer horizontal scrollers |
| ev-evidence | interrupted | 1440 | FIXED | 14px prose reduced |
| ev-evidence | interrupted | 390 | FIXED | 14px prose reduced; fewer horizontal scrollers |
| ev-evidence | no-selection | 1440 | FIXED | 14px prose reduced |
| ev-evidence | no-selection | 390 | FIXED | 14px prose reduced; fewer horizontal scrollers |
| ev-evidence | refused | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-evidence | refused | 390 | FIXED | fewer horizontal scrollers |
| ev-evidence | no-window | 1440 | FIXED | 14px prose reduced |
| ev-evidence | no-window | 390 | FIXED | 14px prose reduced; fewer horizontal scrollers |
| ev-evidence-analysis | interrupted | 1440 | FIXED | [Accepted records behind the conclusions] table columns changed |
| ev-evidence-analysis | interrupted | 390 | FIXED | fewer horizontal scrollers; [Accepted records behind the conclusions] table columns changed |
| ev-evidence-analysis | no-selection | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-evidence-analysis | no-selection | 390 | FIXED | fewer horizontal scrollers |
| ev-evidence-analysis | refused | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-evidence-analysis | refused | 390 | FIXED | fewer horizontal scrollers |
| ev-evidence-analysis | no-window | 1440 | FIXED | [Accepted records behind the conclusions] table columns changed |
| ev-evidence-analysis | no-window | 390 | FIXED | fewer horizontal scrollers; [Accepted records behind the conclusions] table columns changed |
| ev-financials | interrupted | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-financials | interrupted | 390 | FIXED | fewer horizontal scrollers |
| ev-financials | no-selection | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-financials | no-selection | 390 | FIXED | fewer horizontal scrollers |
| ev-financials | refused | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-financials | refused | 390 | FIXED | fewer horizontal scrollers |
| ev-financials | no-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-financials | no-window | 390 | FIXED | fewer horizontal scrollers |
| ev-assumptions | interrupted | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-assumptions | interrupted | 390 | FIXED | fewer horizontal scrollers |
| ev-assumptions | no-selection | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-assumptions | no-selection | 390 | FIXED | fewer horizontal scrollers |
| ev-assumptions | refused | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-assumptions | refused | 390 | FIXED | fewer horizontal scrollers |
| ev-assumptions | no-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-assumptions | no-window | 390 | FIXED | fewer horizontal scrollers |

## Uncounted cross-check
- findings-check (ev-findings, 4 captures, batch-09/findings-check, xcheck-findings-check.json): no regress flags; at 390 the Findings panel is 0.42x the mock height (frozen 1.73x), no new scrollers, no overflow. Servers: API 18901, Vite 5189, CDP 9529; DB assetops_audit_b09_test (dropped). Seed ev interrupted then ev complete, unmodified. 390 screenshots viewed (ev, ev-evidence, ev-financials, ev-evidence-analysis, ev-assumptions, refused, complete): no text cut outside labelled table scroll regions.
