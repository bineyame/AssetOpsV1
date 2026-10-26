# Final recapture batch 13: W4 decisions/cases

Main SHA 89a11477. Pairs 54 (frozen 54). Counts: FIXED 31, PASS 23

Method: original capture tool and producers (unmodified), same ports, fresh DBs; each pair compared with the frozen evidence (panel titles, heights, rows, columns, links, chips, typography, overflow, header band, tab-row scroll, caps) and the frozen mock (unchanged). Classification derived from measured deltas plus register/rulings; standing D1/D2/D4 rows and ruled caps count as PASS. FIXED = a measured signal that a frozen D3 difference is gone.

## REGRESSION-OPEN (0)
- none

## GAP (0)
- none

## Run record
- W4-03 walkthrough unmodified: `--db assetops_audit_b13_test --work var/w403_b13`; DB created empty first (as in the frozen run), then prepare, serve (API 9761), replay-positive, capture --phase positive (producer, 98/98 checks passed), stocked, replay-late, capture --phase late (producer), drop. Vite 5183 (localhost, started plainly with npm per owner addendum), CDP 9523 for my captures and 9763 for the producer.
- Claims: part-one 168/168, part-stocked 24/24, part-late 130/132 (the 2 failures are opportunity refused-bad-known-at 'same panel count', app shows refusal copy only, same as frozen).
- Producer's own late capture reported FAILED 7/459 (frozen: 459/459 passed). These are producer-evidence checks against caps that were RETIRED/re-ruled after the frozen run: scenarios-populated panel 381/488 vs old 348/391 caps and inner vertical scroll boxes (post-W6-W4-rulings Q13 removed them deliberately; ratified 1200/1650); incidents-linked-stocked 1440 479 vs old 460 (ruled 500). Not counted as pairs. OBSERVATION: incidents-refused-overlay (producer scoped-503 overlay, not reachable by a capture-only wrapper) is 505 px at 1440 vs ruled 500 px cap (frozen 445), 479 at 390; evidence producer-w403-capture/incidents-refused-overlay-1440-app.png. The third table row is cut inside the labelled inner scroll region (intended). Producer-only state, flagged not counted.
- Alternatives: only the DB-time 409 state is reachable (producer lists alternatives-stocked/empty-current unproved; F02 future dated). Not a GAP vs frozen (same 3 pairs). Producer scoped-503 states remain producer evidence only.
- 390 screenshots viewed: incidents stocked/refused-long, maintenance empty-kobo, scenarios populated, alternatives 409, opportunity current/refused-bad-known-at. No cut text; no document overflow; Site tab row now wraps (frozen scrolled and hid Overview); opportunity bad-known-at header no longer 295 px tall. Standing: table scrollers at 390 (labelled by visible scrollbar + hint), opportunity breadcrumb root sentence (D1 B13-13), no site-tab row on alternatives/opportunity (D1/D3 Low frozen B13-11).

## All pairs
| Screen | Case | Width | Class | Why |
|---|---|---|---|---|
| scenarios | populated | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| scenarios | populated | 390 | FIXED | Financial scenarios 1.33x mock at 390 (488 px), inside ruled 1200/1650 caps (W4 caps Q18 item 4); frozen inner vertical cap/hidden second row gone; fewer horizo |
| scenarios | empty-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| scenarios | empty-window | 390 | FIXED | fewer horizontal scrollers |
| scenarios | refused-reversed | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| scenarios | refused-reversed | 390 | FIXED | fewer horizontal scrollers |
| scenarios | kobo-no-scenarios | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| scenarios | kobo-no-scenarios | 390 | FIXED | fewer horizontal scrollers |
| alternatives | db-time-409-late | 1440 | FIXED | tab rows changed |
| alternatives | db-time-409-late | 390 | FIXED | tab rows changed |
| opportunity-finding | late-settled-current | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| opportunity-finding | late-settled-current | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| opportunity-finding | stale-k-before-late | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| opportunity-finding | stale-k-before-late | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| opportunity-finding | refused-bad-known-at | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| opportunity-finding | refused-bad-known-at | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| sitework-incidents | late-stocked | 1440 | FIXED | clamped Decision-context/narrative lines now carry a 'Read full text' disclosure (frozen B13-06 clamp without recovery; the measured clipped entry is the same t |
| sitework-incidents | late-stocked | 390 | FIXED | clamped Decision-context/narrative lines now carry a 'Read full text' disclosure (frozen B13-06 clamp without recovery; the measured clipped entry is the same t |
| sitework-maintenance | late-stocked | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| sitework-maintenance | late-stocked | 390 | FIXED | fewer horizontal scrollers |
| opportunity-finding | missing-day-limited | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| opportunity-finding | missing-day-limited | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| sitework-incidents | one-incident | 1440 | FIXED | clamped Decision-context/narrative lines now carry a 'Read full text' disclosure (frozen B13-06 clamp without recovery; the measured clipped entry is the same t |
| sitework-incidents | one-incident | 390 | FIXED | clamped Decision-context/narrative lines now carry a 'Read full text' disclosure (frozen B13-06 clamp without recovery; the measured clipped entry is the same t |
| sitework-maintenance | one-request | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| sitework-maintenance | one-request | 390 | FIXED | fewer horizontal scrollers |
| sitework-incidents | empty-kobo | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| sitework-incidents | empty-kobo | 390 | FIXED | fewer horizontal scrollers |
| sitework-maintenance | empty-kobo | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| sitework-maintenance | empty-kobo | 390 | FIXED | fewer horizontal scrollers |
| sitework-incidents | empty-past-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| sitework-incidents | empty-past-window | 390 | FIXED | fewer horizontal scrollers |
| sitework-incidents | refused-reversed | 1440 | FIXED | tab rows changed |
| sitework-incidents | refused-reversed | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| sitework-maintenance | refused-reversed | 1440 | FIXED | tab rows changed |
| sitework-maintenance | refused-reversed | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| sitework-incidents | refused-long | 1440 | FIXED | tab rows changed |
| sitework-incidents | refused-long | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| sitework-incidents | no-window | 1440 | FIXED | clamped Decision-context/narrative lines now carry a 'Read full text' disclosure (frozen B13-06 clamp without recovery; the measured clipped entry is the same t |
| sitework-incidents | no-window | 390 | FIXED | clamped Decision-context/narrative lines now carry a 'Read full text' disclosure (frozen B13-06 clamp without recovery; the measured clipped entry is the same t |
| opportunity-finding | supported-current | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| opportunity-finding | supported-current | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| opportunity-finding | supported-historical | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| opportunity-finding | supported-historical | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| scenarios | positive-default | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| scenarios | positive-default | 390 | FIXED | Financial scenarios 1.33x mock at 390 (488 px), inside ruled 1200/1650 caps (W4 caps Q18 item 4); frozen inner vertical cap/hidden second row gone; fewer horizo |
| alternatives | db-time-409 | 1440 | FIXED | tab rows changed |
| alternatives | db-time-409 | 390 | FIXED | tab rows changed |
| alternatives | no-revision | 1440 | FIXED | tab rows changed |
| alternatives | no-revision | 390 | FIXED | tab rows changed |
| sitework-incidents | stocked | 1440 | FIXED | clamped Decision-context/narrative lines now carry a 'Read full text' disclosure (frozen B13-06 clamp without recovery; the measured clipped entry is the same t |
| sitework-incidents | stocked | 390 | FIXED | clamped Decision-context/narrative lines now carry a 'Read full text' disclosure (frozen B13-06 clamp without recovery; the measured clipped entry is the same t |
| sitework-maintenance | stocked | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| sitework-maintenance | stocked | 390 | FIXED | fewer horizontal scrollers |
