# Final recapture batch 18: W6 global lists

Main SHA 89a11477. Pairs 186 (frozen 186). Counts: FIXED 57, PASS 129

Method: original capture tool and producers (unmodified), same ports, fresh DBs; each pair compared with the frozen evidence (panel titles, heights, rows, columns, links, chips, typography, overflow, header band, tab-row scroll, caps) and the frozen mock (unchanged). Classification derived from measured deltas plus register/rulings; standing D1/D2/D4 rows and ruled caps count as PASS. FIXED = a measured signal that a frozen D3 difference is gone.

## REGRESSION-OPEN (0)
- none

## GAP (0)
- none

## Run notes
- Main HEAD 0e99aaee, app code SHA 89a11477 (no diff in frontend backend tools host simulator contracts). Vite on localhost:5188 started plainly via npm.cmd (tools/swap-vite.sh), no policy override; stopped by PID. APIs 18801-18809, CDP 9528 (probe 9538).
- Producers unmodified: tools/w601_seed.py x8 (assetops_w601_b18<tag>_test, frozen clocks), tools/w502_cold_work_walkthrough.py prepare (tag b18, positive+worstcase) and its own drop, tools/w504_ev_work_walkthrough.py prepare, serve and attest (base 18800, tag b18) and its own drop. EMPTY_SCOPE uses the reviewed TEST-ONLY .agent/W6-01-evidence/E2/api_empty_scope over the operational DB. All b18 DBs dropped, var/ folders removed, no listeners left.
- Windows: mini W (2026-10-14..21) and the frozen stress/linked windows unchanged (fixed clocks); cold and EV windows 2026-10-25..2026-10-27 (producer work day is now 2026-10-26; the frozen run used day-6..day+1).
- First EV capture (part-ev-noattest, raw/cmp-ev-noattest.json) ran before the producer's attest step created the EV INC and WR; it showed empty lists and is not counted. After attest the ev phase was recaptured (part-ev).
- First stress attempt (part-stress-attempt1, logs/capture-stress-attempt1.log) failed 14 claims because the Vite dev server died silently mid-run (no error in its log); recaptured whole (part-stress) with a restarted Vite, 96/96 claims. Not counted.
- Page-two cursors: API cursor key is random per start, so page-two targets were generated from the capture-round API; the probe round regenerated them (probe-tgt/).
- Cap check: compare3 reports ratio growth against the frozen capture; tools/postcap.py re-evaluated every closed (not all-open) panel against the ruled absolute caps (.agent/post-W6-W6-caps-rulings.md ruling 2). No panel exceeds a ruled cap (closed peaks at 1440/390: Incident cases 647/737 vs 700/800; Corrective work requests 657/737 vs 700/800; Preventive plan 489/690 vs 600/690, so the 390 case sits exactly at its cap as ruling 2 anticipates; Operational records 631/685 vs 650/780; Case boundaries 103/126 vs 150; Record a manual reading 325/513 vs 400/600; How records are used 325/223 vs 400/300).
- Clipped cells: tools/postsig.py confirmed every clipped cell carries its visible disclosure (Full title text, Full record text, or the ruling-4 Show full); the rest of 'clipped text changed' deltas are different data, the same designed clamps.
- Scroller probe (tools/probe-scrollers.mjs, 9538, 6 s settle plus a warm-up navigation) ran on all 186 pairs (probe round for ev used the capture phase's 3.5 s probe on the first, pre-attest DB, then the post-attest ev phase was reprobed with the final tool): every horizontal scroller is the labelled, focusable data-table scroller (aria-labelledby the table heading); zero unfocusable scrollers. The 1440 oprecords horizontal scroll (B18-07) is gone. Notes: cold/EV one-row tables at 390 scroll as designed.
- Inner vertical scrollers: at 390 (and 1440 for tall rows) table panels hold an inner vertical scroll region capped near the ruled height; the next row is partly visible at its edge (intended, labelled, visible scrollbar).
- 390 screenshots opened by me (distinct screens): incidents positive / refused-reversed / worstcase-all-open / cold; maintenance positive / worstcase-all-open / coldwc / ev-all-open (empty-state); preventive positive; oprecords positive / worstcase-all-open. No text cut other than the designed clamps with disclosure and table scroller edges. Refusal, 503, empty-scope and zero screens share the same frames (checked via DOM panels/vocab, no overflow, no console errors).
- Cited, not recounted: EV Finding ev-id scroller (batch 08), cold depth refused-reversed raw code card (batch 14, B14-01), UUID scrollers in open 'UTC and IDs' cells (B13-18); none are on these global pages.
- Standing (not counted): shell/top-bar B1-01, rail B1-04, page-local window controls B2-02, 14px prose B1-07, UTC columns B2-21, 'service:w401-fixture' and id8 labels (R30 / B1-53), tall dark 390 header on short pages B1-02, MOCK DEVIATION D1/D4 labels visible on screen (R73, R355, R358, R362).
- Link-landing captures (part-linkcold/linkev/linkmini) are uncounted in the frozen index and were not rerun, so B18-03/B18-04 (cold Finding link, EV Site link) are not re-verified here.
- Observation: 'Not assessed' cards, Severity 'Not recorded' columns remain (B18-09, ruled in the build spec).

## All pairs
| Screen | Case | Width | Class | Why |
|---|---|---|---|---|
| incidents | unavailable-503 | 1440 | FIXED | breadcrumb added above h1 (B18-08) |
| incidents | unavailable-503 | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | unavailable-503 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | unavailable-503 | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance-preventive | unavailable-503 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance-preventive | unavailable-503 | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| oprecords | unavailable-503 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| oprecords | unavailable-503 | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| incidents | cold | 1440 | FIXED | breadcrumb added above h1 (B18-08) |
| incidents | cold | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | cold | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | cold | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance-preventive | cold | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance-preventive | cold | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| oprecords | cold | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| oprecords | cold | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| incidents | cold-all-open | 1440 | FIXED | breadcrumb added above h1 (B18-08) |
| incidents | cold-all-open | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | cold-all-open | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | cold-all-open | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| incidents | cold-default-window | 1440 | FIXED | breadcrumb added above h1 (B18-08) |
| incidents | cold-default-window | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| incidents | coldwc | 1440 | FIXED | breadcrumb added above h1 (B18-08) |
| incidents | coldwc | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | coldwc | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | coldwc | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance-preventive | coldwc | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance-preventive | coldwc | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| oprecords | coldwc | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| oprecords | coldwc | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| incidents | coldwc-all-open | 1440 | FIXED | breadcrumb added above h1 (B18-08) |
| incidents | coldwc-all-open | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | coldwc-all-open | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | coldwc-all-open | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| incidents | coldwc-default-window | 1440 | FIXED | breadcrumb added above h1 (B18-08) |
| incidents | coldwc-default-window | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| incidents | ev | 1440 | FIXED | breadcrumb added above h1 (B18-08) |
| incidents | ev | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | ev | 1440 | FIXED | raw EV_CONNECTOR code gone (B18-02); plural '1 requests' fixed (B18-01) |
| maintenance | ev | 390 | FIXED | raw EV_CONNECTOR code gone (B18-02); plural '1 requests' fixed (B18-01) |
| maintenance-preventive | ev | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance-preventive | ev | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| oprecords | ev | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| oprecords | ev | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| incidents | ev-all-open | 1440 | FIXED | breadcrumb added above h1 (B18-08) |
| incidents | ev-all-open | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | ev-all-open | 1440 | FIXED | raw EV_CONNECTOR code gone (B18-02); plural '1 requests' fixed (B18-01) |
| maintenance | ev-all-open | 390 | FIXED | raw EV_CONNECTOR code gone (B18-02); plural '1 requests' fixed (B18-01) |
| incidents | ev-default-window | 1440 | FIXED | 14px prose reduced; [Incident cases] table columns changed; breadcrumb added above h1 (B18-08); default window now lists today rows (B18-12) |
| incidents | ev-default-window | 390 | FIXED | 14px prose reduced; [Incident cases] table columns changed; default window now lists today rows (B18-12) |
| incidents | evwc | 1440 | FIXED | breadcrumb added above h1 (B18-08) |
| incidents | evwc | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | evwc | 1440 | FIXED | raw EV_CONNECTOR code gone (B18-02) |
| maintenance | evwc | 390 | FIXED | raw EV_CONNECTOR code gone (B18-02) |
| maintenance-preventive | evwc | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance-preventive | evwc | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| oprecords | evwc | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| oprecords | evwc | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| incidents | evwc-all-open | 1440 | FIXED | breadcrumb added above h1 (B18-08) |
| incidents | evwc-all-open | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | evwc-all-open | 1440 | FIXED | raw EV_CONNECTOR code gone (B18-02) |
| maintenance | evwc-all-open | 390 | FIXED | raw EV_CONNECTOR code gone (B18-02) |
| incidents | evwc-default-window | 1440 | FIXED | 14px prose reduced; [Incident cases] table columns changed; breadcrumb added above h1 (B18-08); default window now lists today rows (B18-12) |
| incidents | evwc-default-window | 390 | FIXED | 14px prose reduced; [Incident cases] table columns changed; default window now lists today rows (B18-12) |
| incidents | historical | 1440 | FIXED | breadcrumb added above h1 (B18-08) |
| incidents | historical | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| incidents | historical-current | 1440 | FIXED | breadcrumb added above h1 (B18-08) |
| incidents | historical-current | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance-preventive | historical | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance-preventive | historical | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance-preventive | historical-current | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance-preventive | historical-current | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| incidents | positive | 1440 | FIXED | breadcrumb added above h1 (B18-08) |
| incidents | positive | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| incidents | all-open | 1440 | FIXED | breadcrumb added above h1 (B18-08) |
| incidents | all-open | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| incidents | page-two | 1440 | FIXED | breadcrumb added above h1 (B18-08) |
| incidents | page-two | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| incidents | refused-reversed | 1440 | FIXED | breadcrumb added above h1 (B18-08) |
| incidents | refused-reversed | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| incidents | refused-span-32d | 1440 | FIXED | breadcrumb added above h1 (B18-08) |
| incidents | refused-span-32d | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| incidents | refused-one-bound | 1440 | FIXED | breadcrumb added above h1 (B18-08) |
| incidents | refused-one-bound | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| incidents | refused-bad-known-at | 1440 | FIXED | breadcrumb added above h1 (B18-08) |
| incidents | refused-bad-known-at | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| incidents | no-window | 1440 | FIXED | Incident cases ratio 2.67->1.08; [Incident cases] table columns changed; breadcrumb added above h1 (B18-08) |
| incidents | no-window | 390 | FIXED | fewer horizontal scrollers; Incident cases ratio 2.75->0.87; [Incident cases] table columns changed |
| incidents | linked | 1440 | FIXED | breadcrumb added above h1 (B18-08) |
| incidents | linked | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | linked | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | linked | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | linked-all-open | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | linked-all-open | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | positive | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | positive | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | all-open | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | all-open | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | page-two | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | page-two | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | refused-reversed | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | refused-reversed | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | refused-span-32d | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | refused-span-32d | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | refused-one-bound | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | refused-one-bound | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | refused-bad-known-at | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | refused-bad-known-at | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | no-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | no-window | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| oprecords | positive | 1440 | FIXED | fewer horizontal scrollers; table horizontal scroll at 1440 gone (B18-07) |
| oprecords | positive | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| oprecords | all-open | 1440 | FIXED | fewer horizontal scrollers; table horizontal scroll at 1440 gone (B18-07) |
| oprecords | all-open | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| oprecords | page-two | 1440 | FIXED | fewer horizontal scrollers; table horizontal scroll at 1440 gone (B18-07) |
| oprecords | page-two | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| oprecords | kind-OPERATOR_LOG | 1440 | FIXED | fewer horizontal scrollers; table horizontal scroll at 1440 gone (B18-07) |
| oprecords | kind-OPERATOR_LOG | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| oprecords | kind-MANUAL_READING | 1440 | FIXED | fewer horizontal scrollers; table horizontal scroll at 1440 gone (B18-07) |
| oprecords | kind-MANUAL_READING | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| oprecords | kind-SHIFT_NOTE | 1440 | FIXED | fewer horizontal scrollers; table horizontal scroll at 1440 gone (B18-07) |
| oprecords | kind-SHIFT_NOTE | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| oprecords | kind-SITE_VISIT | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| oprecords | kind-SITE_VISIT | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| oprecords | historical | 1440 | FIXED | fewer horizontal scrollers; table horizontal scroll at 1440 gone (B18-07) |
| oprecords | historical | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| oprecords | invalid-kind | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| oprecords | invalid-kind | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| oprecords | refused-reversed | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| oprecords | refused-reversed | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| oprecords | refused-span-32d | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| oprecords | refused-span-32d | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| oprecords | refused-one-bound | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| oprecords | refused-one-bound | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| oprecords | refused-bad-known-at | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| oprecords | refused-bad-known-at | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| oprecords | no-window | 1440 | FIXED | fewer horizontal scrollers; [Operational records] table columns changed; table horizontal scroll at 1440 gone (B18-07) |
| oprecords | no-window | 390 | FIXED | fewer horizontal scrollers; [Operational records] table columns changed |
| incidents | one-row | 1440 | FIXED | breadcrumb added above h1 (B18-08) |
| incidents | one-row | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance-preventive | positive | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance-preventive | positive | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance-preventive | all-open | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance-preventive | all-open | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance-preventive | refused-reversed | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance-preventive | refused-reversed | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance-preventive | refused-span-32d | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance-preventive | refused-span-32d | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance-preventive | refused-one-bound | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance-preventive | refused-one-bound | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance-preventive | refused-bad-known-at | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance-preventive | refused-bad-known-at | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance-preventive | no-window | 1440 | FIXED | [Preventive plan] table columns changed |
| maintenance-preventive | no-window | 390 | FIXED | fewer horizontal scrollers; [Preventive plan] table columns changed |
| incidents | empty-scope | 1440 | FIXED | breadcrumb added above h1 (B18-08) |
| incidents | empty-scope | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | empty-scope | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | empty-scope | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance-preventive | empty-scope | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance-preventive | empty-scope | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| oprecords | empty-scope | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| oprecords | empty-scope | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| incidents | worstcase | 1440 | FIXED | breadcrumb added above h1 (B18-08) |
| incidents | worstcase | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| incidents | worstcase-all-open | 1440 | FIXED | breadcrumb added above h1 (B18-08) |
| incidents | worstcase-all-open | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | worstcase | 1440 | FIXED | plural '1 requests' fixed (B18-01) |
| maintenance | worstcase | 390 | FIXED | plural '1 requests' fixed (B18-01) |
| maintenance | worstcase-all-open | 1440 | FIXED | plural '1 requests' fixed (B18-01) |
| maintenance | worstcase-all-open | 390 | FIXED | plural '1 requests' fixed (B18-01) |
| maintenance-preventive | worstcase | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance-preventive | worstcase | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance-preventive | worstcase-all-open | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance-preventive | worstcase-all-open | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| oprecords | worstcase | 1440 | FIXED | fewer horizontal scrollers; table horizontal scroll at 1440 gone (B18-07) |
| oprecords | worstcase | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| oprecords | worstcase-all-open | 1440 | FIXED | fewer horizontal scrollers; table horizontal scroll at 1440 gone (B18-07) |
| oprecords | worstcase-all-open | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| incidents | zero | 1440 | FIXED | breadcrumb added above h1 (B18-08) |
| incidents | zero | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | zero | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance | zero | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance-preventive | zero | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| maintenance-preventive | zero | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| oprecords | zero | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| oprecords | zero | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
