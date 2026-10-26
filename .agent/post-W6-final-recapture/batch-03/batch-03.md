# Final recapture batch 03: W1 Finding/money

Main SHA 89a11477. Pairs 72 (frozen 72). Counts: FIXED 59, PASS 13

Method: original capture tool and producers (unmodified), same ports, fresh DBs; each pair compared with the frozen evidence (panel titles, heights, rows, columns, links, chips, typography, overflow, header band, tab-row scroll, caps) and the frozen mock (unchanged). Classification derived from measured deltas plus register/rulings; standing D1/D2/D4 rows and ruled caps count as PASS. FIXED = a measured signal that a frozen D3 difference is gone.

## REGRESSION-OPEN (0)
- none

## GAP (0)
- none

## Notes
- Producers run unmodified with their own _audit names on API 18301, Vite 5183, CDP 9523: s404 (assetops_s404_owner_audit; prepare, serve, late), s408 (--suffix _audit, owner then mixed), s405 (--only owner --suffix _audit). All DBs dropped, var work folders removed.
- Record IDs are regenerated on each prepare; target URLs were re-mapped by role (priced / unpriced / quantity-unavailable / mixed / p01). s404 Finding: first Positive-day row with four revisions (2cf9704f, version 1 8edde4f5); the frozen run used a different four-revision Finding of the same day, so wording of one Finding may differ slightly. s408 unpriced = latest UNPRICED revision of the second Finding.
- Cap proofs: finding 'Where to look next' and 'What limits this conclusion' within the ruled 650/1000 and 500/800 caps; Interpretation history now 2.2-3.2x at 1440 (frozen 4.5-8.6x) and 3.1-4.0x at 390 (frozen 7-17x), inside the 800/1400 Q23 cap; Revision history 2.1-2.6x / 3.1-3.8x (frozen 3.5-4.25x at 390).
- Financials 'What happened -> what it means in money' 2.11x/3.1x on the priced case is unchanged from the frozen capture (standing).

## All pairs
| Screen | Case | Width | Class | Why |
|---|---|---|---|---|
| finding | late-stale | 1440 | FIXED | Panel grew only by ruled additions (Alternatives link, Recommendation/Financials links, W3 rulings Q15/R192); closed heights stay inside the ruled caps: Where t |
| finding | late-stale | 390 | FIXED | Panel grew only by ruled additions (Alternatives link, Recommendation/Financials links, W3 rulings Q15/R192); closed heights stay inside the ruled caps: Where t |
| finding-history | late-stale | 1440 | FIXED | tab rows changed; [Revision history] table columns changed |
| finding-history | late-stale | 390 | FIXED | tab rows changed; fewer horizontal scrollers; Revision history ratio 3.5->3.13; [Revision history] table columns changed |
| sitefindings | late-stale | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| sitefindings | late-stale | 390 | FIXED | fewer horizontal scrollers |
| finding | open | 1440 | FIXED | Panel grew only by ruled additions (Alternatives link, Recommendation/Financials links, W3 rulings Q15/R192); closed heights stay inside the ruled caps: Where t |
| finding | open | 390 | FIXED | Panel grew only by ruled additions (Alternatives link, Recommendation/Financials links, W3 rulings Q15/R192); closed heights stay inside the ruled caps: Where t |
| finding | version1 | 1440 | FIXED | Panel grew only by ruled additions (Alternatives link, Recommendation/Financials links, W3 rulings Q15/R192); closed heights stay inside the ruled caps: Where t |
| finding | version1 | 390 | FIXED | Panel grew only by ruled additions (Alternatives link, Recommendation/Financials links, W3 rulings Q15/R192); closed heights stay inside the ruled caps: Where t |
| finding | notfound | 1440 | FIXED | tab rows changed |
| finding | notfound | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| finding-evidence | latest | 1440 | FIXED | tab rows changed |
| finding-evidence | latest | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| finding-evidence | notfound | 1440 | FIXED | h1 text changed; tab rows changed |
| finding-evidence | notfound | 390 | FIXED | h1 text changed; tab rows changed; fewer horizontal scrollers |
| finding-history | latest | 1440 | FIXED | tab rows changed; [Revision history] table columns changed |
| finding-history | latest | 390 | FIXED | tab rows changed; fewer horizontal scrollers; Revision history ratio 3.5->3.13; [Revision history] table columns changed |
| finding-history | version1 | 1440 | FIXED | tab rows changed; [Revision history] table columns changed |
| finding-history | version1 | 390 | FIXED | tab rows changed; fewer horizontal scrollers; Revision history ratio 4.25->3.81; [Revision history] table columns changed |
| finding-history | notfound | 1440 | FIXED | h1 text changed; tab rows changed |
| finding-history | notfound | 390 | FIXED | h1 text changed; tab rows changed; fewer horizontal scrollers |
| sitefindings | stocked | 1440 | FIXED | Findings at this site ratio 1.76->1.57 |
| sitefindings | stocked | 390 | FIXED | fewer horizontal scrollers; Findings at this site ratio 1.66->1.49 |
| sitefindings | page2 | 1440 | FIXED | Findings at this site ratio 1.58->1.39 |
| sitefindings | page2 | 390 | FIXED | fewer horizontal scrollers; Findings at this site ratio 1.51->1.33 |
| sitefindings | empty | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| sitefindings | empty | 390 | FIXED | fewer horizontal scrollers |
| sitefindings | stale | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| sitefindings | stale | 390 | FIXED | fewer horizontal scrollers |
| sitefindings | failed | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| sitefindings | failed | 390 | FIXED | fewer horizontal scrollers |
| sitefindings | unassessed | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| sitefindings | unassessed | 390 | FIXED | fewer horizontal scrollers |
| sitefindings | nowindow | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| sitefindings | nowindow | 390 | FIXED | fewer horizontal scrollers |
| financials | priced-current | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| financials | priced-current | 390 | FIXED | fewer horizontal scrollers |
| finding | priced-current | 1440 | FIXED | Panel grew only by ruled additions (Alternatives link, Recommendation/Financials links, W3 rulings Q15/R192); closed heights stay inside the ruled caps: Where t |
| finding | priced-current | 390 | FIXED | Panel grew only by ruled additions (Alternatives link, Recommendation/Financials links, W3 rulings Q15/R192); closed heights stay inside the ruled caps: Where t |
| assumptions | single-price | 1440 | FIXED | Interpretation history ratio 5.31->3.23; [Interpretation history] table columns changed |
| assumptions | single-price | 390 | FIXED | fewer horizontal scrollers; Interpretation history ratio 10.13->3.97; [Interpretation history] table columns changed |
| financials | mixed-withheld | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| financials | mixed-withheld | 390 | FIXED | Panel grew by the ruled 'Inspect technical basis' link (W3 Q22/R199); +26 px, no ruled cap exceeded, no overflow or clipping; fewer horizontal scrollers |
| assumptions | mixed-withheld | 1440 | FIXED | Interpretation history ratio 2.63->1.68; [Interpretation history] table columns changed |
| assumptions | mixed-withheld | 390 | FIXED | fewer horizontal scrollers; Interpretation history ratio 4.06->2.26; [Interpretation history] table columns changed |
| finding-evidence | mixed-source | 1440 | FIXED | tab rows changed |
| finding-evidence | mixed-source | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| financials | priced | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| financials | priced | 390 | FIXED | fewer horizontal scrollers |
| financials | unpriced | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| financials | unpriced | 390 | FIXED | Panel grew by the ruled 'Inspect technical basis' link (W3 Q22/R199); +26 px, no ruled cap exceeded, no overflow or clipping; fewer horizontal scrollers |
| financials | quantity-unavailable | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| financials | quantity-unavailable | 390 | FIXED | Panel grew by the ruled 'Inspect technical basis' link (W3 Q22/R199); +26 px, no ruled cap exceeded, no overflow or clipping; fewer horizontal scrollers |
| financials | nofinding | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| financials | nofinding | 390 | FIXED | fewer horizontal scrollers |
| financials | notfound | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| financials | notfound | 390 | FIXED | fewer horizontal scrollers |
| finding | priced | 1440 | FIXED | Panel grew only by ruled additions (Alternatives link, Recommendation/Financials links, W3 rulings Q15/R192); closed heights stay inside the ruled caps: Where t |
| finding | priced | 390 | FIXED | Panel grew only by ruled additions (Alternatives link, Recommendation/Financials links, W3 rulings Q15/R192); closed heights stay inside the ruled caps: Where t |
| finding-evidence | labelled | 1440 | FIXED | tab rows changed |
| finding-evidence | labelled | 390 | FIXED | tab rows changed; fewer horizontal scrollers |
| finding-history | priced | 1440 | FIXED | tab rows changed; [Revision history] table columns changed |
| finding-history | priced | 390 | FIXED | tab rows changed; fewer horizontal scrollers; Revision history ratio 2.3->2.12; [Revision history] table columns changed |
| assumptions | default | 1440 | FIXED | Interpretation history ratio 8.64->3.23; [Interpretation history] table columns changed |
| assumptions | default | 390 | FIXED | fewer horizontal scrollers; Interpretation history ratio 17.0->3.88; [Interpretation history] table columns changed |
| assumptions | recorded-T1 | 1440 | FIXED | Interpretation history ratio 5.31->3.23; [Interpretation history] table columns changed |
| assumptions | recorded-T1 | 390 | FIXED | fewer horizontal scrollers; Interpretation history ratio 10.13->3.97; [Interpretation history] table columns changed |
| assumptions | recorded-T3 | 1440 | FIXED | Interpretation history ratio 8.64->3.23; [Interpretation history] table columns changed |
| assumptions | recorded-T3 | 390 | FIXED | fewer horizontal scrollers; Interpretation history ratio 17.0->3.88; [Interpretation history] table columns changed |
| assumptions | T3-page2 | 1440 | FIXED | 14px prose reduced; Interpretation history ratio 4.46->2.23; [Interpretation history] table columns changed |
| assumptions | T3-page2 | 390 | FIXED | 14px prose reduced; fewer horizontal scrollers; Interpretation history ratio 7.0->3.11; [Interpretation history] table columns changed |
