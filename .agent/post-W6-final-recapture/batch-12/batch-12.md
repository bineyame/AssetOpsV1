# Final recapture batch 12: W4 mini depth

Main SHA 89a11477. Pairs 42 (frozen 42). Counts: FIXED 25, PASS 17

Method: original capture tool and producers (unmodified), same ports, fresh DBs; each pair compared with the frozen evidence (panel titles, heights, rows, columns, links, chips, typography, overflow, header band, tab-row scroll, caps) and the frozen mock (unchanged). Classification derived from measured deltas plus register/rulings; standing D1/D2/D4 rows and ruled caps count as PASS. FIXED = a measured signal that a frozen D3 difference is gone.

## REGRESSION-OPEN (0)
- none

## GAP (0)
- none

## Run record
- W4-02 seed.py unmodified against w402r_test (accepted 3321/326, 123 jobs, 123 selections); it rewrote tracked .agent/W4-02-evidence/replay.json, copied to logs/replay-b12.json and the tracked file restored with git checkout. API host lab_app on 18201, Vite 5182 (localhost), CDP 9522. W4-03 walkthrough unmodified (--db assetops_audit_b12_test --work var/w403_b12; prepare, serve on 9761, replay-positive, then its own drop). All DBs dropped, servers stopped, var/w403_b12 removed.
- Capture claims: main 240/240 (frozen 232/240: the refused-invalid pairs now render the strip, cards and panels with 'Not assessed', so panel counts match the mock), w403 24/24, links 36/36.
- Refused-invalid (4 IDs x 2 widths): now keeps strip, four cards and all mock panels with honest 'Not assessed' (frozen: period bar + 'Period cannot be read' only) = FIXED. At 390 the Site tab row no longer scrolls horizontally (frozen site-tabs__list 521>358) on every pair = FIXED signal.
- Standing: table scrollers at 390 (data-table__scroll, labelled by visible scrollbar), backup closed 'Inspect IDs' disclosures hold mini-ids lists (same as frozen). No clipped text, no document overflow, no new inner scrollers. 390 screenshots viewed (backup positive, renewable refused).
- Uncounted: w403 link-check (mini-08) in xcheck-w403-link.json; Overview link checks (batch-12/links) 36/36.

## All pairs
| Screen | Case | Width | Class | Why |
|---|---|---|---|---|
| renewable | positive | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| renewable | positive | 390 | FIXED | fewer horizontal scrollers |
| service | positive | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| service | positive | 390 | FIXED | fewer horizontal scrollers |
| fuel | positive | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| fuel | positive | 390 | FIXED | fewer horizontal scrollers |
| backup | positive | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| backup | positive | 390 | FIXED | fewer horizontal scrollers |
| renewable | gap-limited | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| renewable | gap-limited | 390 | FIXED | fewer horizontal scrollers |
| service | gap-limited | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| service | gap-limited | 390 | FIXED | fewer horizontal scrollers |
| fuel | gap-limited | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| fuel | gap-limited | 390 | FIXED | fewer horizontal scrollers |
| backup | gap-limited | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| backup | gap-limited | 390 | FIXED | fewer horizontal scrollers |
| renewable | no-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| renewable | no-window | 390 | FIXED | fewer horizontal scrollers |
| service | no-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| service | no-window | 390 | FIXED | fewer horizontal scrollers |
| fuel | no-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| fuel | no-window | 390 | FIXED | fewer horizontal scrollers |
| backup | no-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| backup | no-window | 390 | FIXED | fewer horizontal scrollers |
| renewable | refused-invalid | 1440 | FIXED | panel set changed |
| renewable | refused-invalid | 390 | FIXED | fewer horizontal scrollers; panel set changed |
| service | refused-invalid | 1440 | FIXED | panel set changed |
| service | refused-invalid | 390 | FIXED | fewer horizontal scrollers; panel set changed |
| fuel | refused-invalid | 1440 | FIXED | panel set changed |
| fuel | refused-invalid | 390 | FIXED | fewer horizontal scrollers; panel set changed |
| backup | refused-invalid | 1440 | FIXED | panel set changed |
| backup | refused-invalid | 390 | FIXED | fewer horizontal scrollers; panel set changed |
| renewable | known-before-evidence | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| renewable | known-before-evidence | 390 | FIXED | fewer horizontal scrollers |
| service | known-before-evidence | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| service | known-before-evidence | 390 | FIXED | fewer horizontal scrollers |
| fuel | known-before-evidence | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| fuel | known-before-evidence | 390 | FIXED | fewer horizontal scrollers |
| backup | known-before-evidence | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| backup | known-before-evidence | 390 | FIXED | fewer horizontal scrollers |
| renewable | w403-decision-positive | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| renewable | w403-decision-positive | 390 | FIXED | fewer horizontal scrollers |
