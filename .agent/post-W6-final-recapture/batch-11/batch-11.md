# Final recapture batch 11: W3 estate composition

Main SHA 89a11477. Pairs 66 (frozen 66). Counts: FIXED 6, PASS 60

Method: original capture tool and producers (unmodified), same ports, fresh DBs; each pair compared with the frozen evidence (panel titles, heights, rows, columns, links, chips, typography, overflow, header band, tab-row scroll, caps) and the frozen mock (unchanged). Classification derived from measured deltas plus register/rulings; standing D1/D2/D4 rows and ruled caps count as PASS. FIXED = a measured signal that a frozen D3 difference is gone.

## REGRESSION-OPEN (0)
- none

## GAP (0)
- none

## Run record
- W3-03 test_serve_portfolio.py unmodified via pytest, DB assetops_audit_b11_test (W303_DB), port 9781: clean (W303_ROUTER=capture: positive, guards, historical, then /__capture/mode tenant=foreign (empty), auth=deny (401), then /__capture/empty-site (partial)); W303_COLD_DRAIN=0 (pending); W303_NO_CURSOR_KEY=1 (503). W3-02 serve.py unmodified, w302j_test, port 9751: positive, /__capture/empty-site (partial-week), /__capture/late-kobo (pending). Vite 5181 (localhost; 127.0.0.1 not served), CDP 9521. All DBs dropped, servers stopped.
- Capture claim counts: positive 36/36, guards 96/108, historical 36/36, empty 12/12, 401 10/12, partial 36/36, pending 36/36, 503 10/12, w302 34/36 x3; every failing claim is a refused/503 pair with 0 app panels vs mock panels (same as frozen).
- Portfolio under W3-02 producer refuses (503 SITE_STORE_UNAVAILABLE) as frozen (B11-16).
- w303-links: 34 app-only link-destination captures (uncounted, xcheck): no horizontal scroller, clipping, overflow or console error on any destination (frozen had 18 targets).
- Not captured (as frozen): refusal-409 (needs a click).
- 390 screenshots viewed (portfolio, financials, evidence): no cut text outside labelled table scroll regions.

## All pairs
| Screen | Case | Width | Class | Why |
|---|---|---|---|---|
| globalevidence | w302-partial-week | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| globalevidence | w302-partial-week | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| globalfinancials | w302-partial-week | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| globalfinancials | w302-partial-week | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| portfolio | w302-partial-week | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| portfolio | w302-partial-week | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| globalevidence | w302-pending-late-kobo | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| globalevidence | w302-pending-late-kobo | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| globalfinancials | w302-pending-late-kobo | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| globalfinancials | w302-pending-late-kobo | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| portfolio | w302-pending-late-kobo | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| portfolio | w302-pending-late-kobo | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| globalevidence | w302-positive | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| globalevidence | w302-positive | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| globalfinancials | w302-positive | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| globalfinancials | w302-positive | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| portfolio | w302-positive | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| portfolio | w302-positive | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| portfolio | w303-refusal-401 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| portfolio | w303-refusal-401 | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| portfolio | w303-refusal-503 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| portfolio | w303-refusal-503 | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| portfolio | w303-empty-foreign-tenant | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| portfolio | w303-empty-foreign-tenant | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| globalevidence | refused-reversed | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| globalevidence | refused-reversed | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| globalevidence | refused-over-31d | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| globalevidence | refused-over-31d | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| globalevidence | no-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| globalevidence | no-window | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| globalfinancials | refused-reversed | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| globalfinancials | refused-reversed | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| globalfinancials | refused-over-31d | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| globalfinancials | refused-over-31d | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| globalfinancials | no-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| globalfinancials | no-window | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| portfolio | refused-reversed | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| portfolio | refused-reversed | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| portfolio | refused-over-31d | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| portfolio | refused-over-31d | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| portfolio | no-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| portfolio | no-window | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| globalevidence | w303-historical | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| globalevidence | w303-historical | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| globalfinancials | w303-historical | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| globalfinancials | w303-historical | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| portfolio | w303-historical | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| portfolio | w303-historical | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| globalevidence | w303-partial | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| globalevidence | w303-partial | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| globalfinancials | w303-partial | 1440 | FIXED | Consequence register grew 279->365 px (302->389 partial) only because the frozen 604 px inner vertical scroller (rows cut at the panel edge, 2 of 4 rows visible |
| globalfinancials | w303-partial | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| portfolio | w303-partial | 1440 | FIXED | fewer horizontal scrollers |
| portfolio | w303-partial | 390 | FIXED | fewer horizontal scrollers |
| globalevidence | w303-pending | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| globalevidence | w303-pending | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| globalfinancials | w303-pending | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| globalfinancials | w303-pending | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| portfolio | w303-pending | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| portfolio | w303-pending | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| globalevidence | w303-positive | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| globalevidence | w303-positive | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| globalfinancials | w303-positive | 1440 | FIXED | Consequence register grew 279->365 px (302->389 partial) only because the frozen 604 px inner vertical scroller (rows cut at the panel edge, 2 of 4 rows visible |
| globalfinancials | w303-positive | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| portfolio | w303-positive | 1440 | FIXED | fewer horizontal scrollers |
| portfolio | w303-positive | 390 | FIXED | fewer horizontal scrollers |
