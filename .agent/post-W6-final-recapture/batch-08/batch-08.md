# Final recapture batch 08: W2 EV Foundation/assessment

Main SHA 89a11477. Pairs 56 (frozen 56). Counts: FIXED 27, PASS 23, REGRESSION-OPEN 6

Method: original capture tool and producers (unmodified), same ports, fresh DBs; each pair compared with the frozen evidence (panel titles, heights, rows, columns, links, chips, typography, overflow, header band, tab-row scroll, caps) and the frozen mock (unchanged). Classification derived from measured deltas plus register/rulings; standing D1/D2/D4 rows and ruled caps count as PASS. FIXED = a measured signal that a frozen D3 difference is gone.

## REGRESSION-OPEN (6)
- ev-finding / interrupted / 1440: The 'cap exceeded Bounded conclusion 1.2->1.33' flag is inside the ruled 600 px cap (279 px; growth from the accepted Q7 'Inspect claim evidence' link) and is NOT the finding. Session id in Operational context ('SES ev-9ada0e59...', 64 chars) is now a one-line horizontal scroller (ev-id sw 429 > cw 347 at 1440, cw 159 at 390) instead of wrapping to 2/3 lines as in the frozen capture and as register R277 / W2-F M10-N1 css (.ev-id wrap) state; the id is visibly cut at the panel edge (390 also cuts 'Connector c1', 'Observed abort'). Frozen hscroll was none. Evidence: batch-08/interrupted/ev-finding-interrupted-1440-app.png vs post-W6-audit/batch-08/interrupted/. Suspected cause: a later generic one-line-id scroller rule overriding .ev-id wrap (css not located). (evidence interrupted/ev-finding-interrupted-1440-app.png)
- ev-finding / interrupted / 390: Session id in Operational context ('SES ev-9ada0e59...', 64 chars) is now a one-line horizontal scroller (ev-id sw 429 > cw 347 at 1440, cw 159 at 390) instead of wrapping to 2/3 lines as in the frozen capture and as register R277 / W2-F M10-N1 css (.ev-id wrap) state; the id is visibly cut at the panel edge (390 also cuts 'Connector c1', 'Observed abort'). Frozen hscroll was none. Evidence: batch-08/interrupted/ev-finding-interrupted-390-app.png vs post-W6-audit/batch-08/interrupted/. Suspected cause: a later generic one-line-id scroller rule overriding .ev-id wrap (css not located). (evidence interrupted/ev-finding-interrupted-390-app.png)
- ev-finding / no-window / 1440: The 'cap exceeded Bounded conclusion 1.2->1.33' flag is inside the ruled 600 px cap (279 px; growth from the accepted Q7 'Inspect claim evidence' link) and is NOT the finding. Session id in Operational context ('SES ev-9ada0e59...', 64 chars) is now a one-line horizontal scroller (ev-id sw 429 > cw 347 at 1440, cw 159 at 390) instead of wrapping to 2/3 lines as in the frozen capture and as register R277 / W2-F M10-N1 css (.ev-id wrap) state; the id is visibly cut at the panel edge (390 also cuts 'Connector c1', 'Observed abort'). Frozen hscroll was none. Evidence: batch-08/interrupted/ev-finding-no-window-1440-app.png vs post-W6-audit/batch-08/interrupted/. Suspected cause: a later generic one-line-id scroller rule overriding .ev-id wrap (css not located). (evidence interrupted/ev-finding-no-window-1440-app.png)
- ev-finding / no-window / 390: Session id in Operational context ('SES ev-9ada0e59...', 64 chars) is now a one-line horizontal scroller (ev-id sw 429 > cw 347 at 1440, cw 159 at 390) instead of wrapping to 2/3 lines as in the frozen capture and as register R277 / W2-F M10-N1 css (.ev-id wrap) state; the id is visibly cut at the panel edge (390 also cuts 'Connector c1', 'Observed abort'). Frozen hscroll was none. Evidence: batch-08/interrupted/ev-finding-no-window-390-app.png vs post-W6-audit/batch-08/interrupted/. Suspected cause: a later generic one-line-id scroller rule overriding .ev-id wrap (css not located). (evidence interrupted/ev-finding-no-window-390-app.png)
- ev-finding / recommendation-address / 1440: The 'cap exceeded Bounded conclusion 1.2->1.33' flag is inside the ruled 600 px cap (279 px; growth from the accepted Q7 'Inspect claim evidence' link) and is NOT the finding. Session id in Operational context ('SES ev-9ada0e59...', 64 chars) is now a one-line horizontal scroller (ev-id sw 429 > cw 347 at 1440, cw 159 at 390) instead of wrapping to 2/3 lines as in the frozen capture and as register R277 / W2-F M10-N1 css (.ev-id wrap) state; the id is visibly cut at the panel edge (390 also cuts 'Connector c1', 'Observed abort'). Frozen hscroll was none. Evidence: batch-08/interrupted/ev-finding-recommendation-address-1440-app.png vs post-W6-audit/batch-08/interrupted/. Suspected cause: a later generic one-line-id scroller rule overriding .ev-id wrap (css not located). (evidence interrupted/ev-finding-recommendation-address-1440-app.png)
- ev-finding / recommendation-address / 390: Session id in Operational context ('SES ev-9ada0e59...', 64 chars) is now a one-line horizontal scroller (ev-id sw 429 > cw 347 at 1440, cw 159 at 390) instead of wrapping to 2/3 lines as in the frozen capture and as register R277 / W2-F M10-N1 css (.ev-id wrap) state; the id is visibly cut at the panel edge (390 also cuts 'Connector c1', 'Observed abort'). Frozen hscroll was none. Evidence: batch-08/interrupted/ev-finding-recommendation-address-390-app.png vs post-W6-audit/batch-08/interrupted/. Suspected cause: a later generic one-line-id scroller rule overriding .ev-id wrap (css not located). (evidence interrupted/ev-finding-recommendation-address-390-app.png)

## GAP (0)
- none

## Notes for the coordinator
- Producer `.agent/W2-F-evidence/seed.py ev <case>` (unmodified; interrupted, complete, missing-meter, fault, contradictory; `ASSETOPS_TEST_TEMPLATE=0`) against `assetops_audit_b08_test` (created by me, dropped at the end); API 18801 restarted per phase, Vite 5188, CDP 9528. Record ids deterministic and equal to frozen; frozen targets reused. Inventory check captured against the same interrupted seed. Frozen interrupted evidence = part1 merged with part2 (the 5 recaptured pairs).
- REGRESSION-OPEN (6 pairs, one cause): ev-finding Overview Session id no longer wraps (see above). Seen only on the EV Finding Overview; 390 pairs are not flagged by the automatic comparison (cap check only), classified by reading the screenshots.
- Capture FAILs (2 of 192 claims): ev-finding evidence-child 'same panel count' (app shows one 'Finding section' unavailable panel vs mock three) is the frozen state (B8 inventory, unchanged).
- Observation: refusal/unknown-id panels gained a collapsed details disclosure (96 -> 121 px).
- FIXED signals: tab row no longer scrolls at 390; several panel ratios dropped.

## All pairs
| Screen | Case | Width | Class | Why |
|---|---|---|---|---|
| sessions | complete | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| sessions | complete | 390 | FIXED | fewer horizontal scrollers |
| sessions | complete-default-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| sessions | complete-default-window | 390 | FIXED | fewer horizontal scrollers |
| ev-foundation | complete-replay | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-foundation | complete-replay | 390 | FIXED | fewer horizontal scrollers |
| ev-readiness | complete-replay | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-readiness | complete-replay | 390 | FIXED | fewer horizontal scrollers |
| sessions | contradictory | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| sessions | contradictory | 390 | FIXED | fewer horizontal scrollers |
| sessions | contradictory-default-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| sessions | contradictory-default-window | 390 | FIXED | fewer horizontal scrollers |
| sessions | fault | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| sessions | fault | 390 | FIXED | fewer horizontal scrollers |
| sessions | fault-default-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| sessions | fault-default-window | 390 | FIXED | fewer horizontal scrollers |
| ev-foundation | stocked | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-foundation | stocked | 390 | FIXED | fewer horizontal scrollers |
| ev-foundation | no-version | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-foundation | no-version | 390 | FIXED | fewer horizontal scrollers |
| ev-readiness | stocked | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-readiness | stocked | 390 | FIXED | fewer horizontal scrollers |
| ev-readiness | no-version | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-readiness | no-version | 390 | FIXED | fewer horizontal scrollers |
| ev-sld | stocked | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-sld | stocked | 390 | FIXED | fewer horizontal scrollers |
| ev-sld | no-version | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-sld | no-version | 390 | FIXED | fewer horizontal scrollers |
| sessions | interrupted | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| sessions | interrupted | 390 | FIXED | fewer horizontal scrollers |
| sessions | default-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| sessions | default-window | 390 | FIXED | fewer horizontal scrollers |
| sessions | no-selection | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| sessions | no-selection | 390 | FIXED | fewer horizontal scrollers |
| sessions | refused | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| sessions | refused | 390 | FIXED | fewer horizontal scrollers |
| ev-finding | interrupted | 1440 | REGRESSION-OPEN | The 'cap exceeded Bounded conclusion 1.2->1.33' flag is inside the ruled 600 px cap (279 px; growth from the accepted Q7 'Inspect claim evidence' link) and is N |
| ev-finding | interrupted | 390 | REGRESSION-OPEN | Session id in Operational context ('SES ev-9ada0e59...', 64 chars) is now a one-line horizontal scroller (ev-id sw 429 > cw 347 at 1440, cw 159 at 390) instead  |
| ev-finding | no-window | 1440 | REGRESSION-OPEN | The 'cap exceeded Bounded conclusion 1.2->1.33' flag is inside the ruled 600 px cap (279 px; growth from the accepted Q7 'Inspect claim evidence' link) and is N |
| ev-finding | no-window | 390 | REGRESSION-OPEN | Session id in Operational context ('SES ev-9ada0e59...', 64 chars) is now a one-line horizontal scroller (ev-id sw 429 > cw 347 at 1440, cw 159 at 390) instead  |
| ev-finding | refused | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-finding | refused | 390 | FIXED | fewer horizontal scrollers |
| ev-finding | unknown-id | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-finding | unknown-id | 390 | FIXED | fewer horizontal scrollers |
| ev-finding | recommendation-address | 1440 | REGRESSION-OPEN | The 'cap exceeded Bounded conclusion 1.2->1.33' flag is inside the ruled 600 px cap (279 px; growth from the accepted Q7 'Inspect claim evidence' link) and is N |
| ev-finding | recommendation-address | 390 | REGRESSION-OPEN | Session id in Operational context ('SES ev-9ada0e59...', 64 chars) is now a one-line horizontal scroller (ev-id sw 429 > cw 347 at 1440, cw 159 at 390) instead  |
| ev-finding | evidence-child | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| ev-finding | evidence-child | 390 | FIXED | fewer horizontal scrollers |
| ev-findings | inventory-check | 1440 | FIXED | [Findings at this site] table columns changed |
| ev-findings | inventory-check | 390 | FIXED | Findings at this site ratio 1.73->0.64; [Findings at this site] table columns changed |
| ev-findings | inventory-check-window | 1440 | FIXED | [Findings at this site] table columns changed |
| ev-findings | inventory-check-window | 390 | FIXED | Findings at this site ratio 1.73->0.64; [Findings at this site] table columns changed |
| sessions | missing-meter | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| sessions | missing-meter | 390 | FIXED | fewer horizontal scrollers |
| sessions | missing-meter-default-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| sessions | missing-meter-default-window | 390 | FIXED | fewer horizontal scrollers |
