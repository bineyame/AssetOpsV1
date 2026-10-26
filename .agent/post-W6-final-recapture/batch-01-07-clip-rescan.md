# Batches 01-07: clipped-text and inner-scroller re-scan

Date 2026-10-26. Evidence: the final-recapture captures of batches 01-07 (main 89a11477), compared with the frozen audit evidence (`.agent/post-W6-audit/batch-NN/*/evidence.json`). Code references are to current main 136ceb01. Since 89a11477 the app code has changed only through the merged recapture-fix branch 7306079d, and none of the lines cited here changed.

**Result: REGRESSION-OPEN 0.** There is 1 STANDING item (R217). There are 3 flags, not counted: unlabelled scrollers inside closed disclosures, all already present in the frozen capture. I re-captured nothing and ran no producers, servers or DBs.

## Method

1. **compare3 logic over the stored measures.** `tools/compare3.py` imports compare2's batch-02+ format, so it cannot read batch 01 as it is. I re-implemented compare3's inner-overflow step in `clip-rescan-01-07/rescan.py`. It uses the same signatures: hscroll by (cls, panel), clipped by (cls, text[:30]), with UUIDs normalised. It ran over all 356 pairs, each matched to its frozen pair (356/356 matched). Batch 01's `innerScroll`/`clipped` were mapped onto hscroll/clipped. `clip-rescan-01-07/agg.py` lists every clipped or scroller entry, not only the new ones. Output: `clip-rescan-01-07/rescan.json`.
2. **By eye.** I opened the 390-width app screenshot with the longest page for each of the 38 screen IDs, plus 4 extra pairs flagged in step 1 (42 images). I viewed them at native 390 px resolution as 3-column montages (`clip-rescan-01-07/tile.mjs`, headless Chrome, read-only). I also checked the 1440 images where a desktop scroller was measured (cold-findings, sitework).
3. **Code check of scroller reachability.** The stored measures carry no focus or label data, so I listed every `<DataTable>` on main that has no `labelledBy`. Without it, `DataTable` (frontend/src/ui/DataTable.tsx:55-62) renders no `role=region` and no `tabIndex`. I then mapped each one to the measured scrollers.

## Which pairs have which measures

| Batches | Pairs | Clipped text | Scrollers | What is missing |
|---|---|---|---|---|
| 02-07 | 316 | X and Y clip (overflow hidden/clip, ellipsis, Y overflow); any element; top 10 | cls, panel, sw/cw; top 10 | focusability, label, inner focusable descendant |
| 01 | 40 | X only, leaf elements, visible only (no line-clamp / Y clip); top 8 | cls and sizes, no panel; visible only | as above, plus Y clip and panel name |

- No pair reached the 8/10 entry cap, so no list was truncated.
- Page `overflowX` is 0 on all 356 pairs.
- **What no pair has:**
  - The probe-scrollers fields (focusable, role, label, inner). These exist from batch 08 on.
  - An all-disclosures-open capture: batches 01-07 had no `openAll` cases, frozen or new. Content inside disclosures was therefore never imaged.
  - In batches 02-07 the capture's filter still measured scrollers inside closed `<details>` (for example a 104 px `cw` at 1440 on sitework), which is what allows flags F1-F3 below. Batch 01's `vis()` filter excludes closed content, so the batch 01 disclosures are unmeasured.

## Step 1 result: what compare3 flags

Only 2 kinds of pair show a scroller or clipped entry that the frozen pair lacked:
- action-history verified-replay (1440/390) gained `code.action-ref` ellipsis entries. See S1.
- cold-findings stocked and no-window (1440/390) gained a `data-table__scroll` on "Findings at this site" (949/318 at 390, 1125/1120 at 1440). This is the new Findings table: B7-01, frozen index missing, now FIXED.

All other entries are identical to the frozen capture:
- **Clipped:**
  - visually-hidden table captions (`visually-hidden`, `w1f4-action-caption`, frontend/src/sites/w1f4-action.css:52-60);
  - batch 01 form controls ("Search sites", "Mode", "Lifecycle" placeholder/select text);
  - the "Changed value" caption;
  - `action-ref` on action-history.
- **Scrollers:** 37 groups of `data-table__scroll` plus the Finding/Recommendation section row `site-tabs__list` at 390. The section row was accepted in the frozen batch 03 text as a readable scroller with a visible scrollbar, and its items are links. It sits under R383/R395.

## Findings

### REGRESSION-OPEN (0)
- None. No text is cut at a panel or cell edge without a disclosure, no text overlaps, and there is no horizontal page overflow on any of the 42 images viewed. Every visible 390 table scroller I checked is a labelled `DataTable` region (tabindex 0) or holds links, and shows its grey scrollbar.

### STANDING (1)
- **S1 (R217 / B4-18, open D2): Action history shows the new Foundation version ID cut short.** The ID in the "Applied to the Site Foundation" row is an `action-ref` cut to 12ch (86 of 257 px) with an ellipsis. The full value is only in the `title` tooltip.
  - B4-18 records exactly this ("monospace UUIDs ellipsized to 86 px of 257 px"), and the batch-04 recapture noted it under R217.
  - verified-replay is newly flagged only because its frozen pair was the B4-19 error page. It now renders the normal table, so this is not new.
  - Cause: frontend/src/sites/w1f4-action.css:151-158 (`td small code` max-width 12ch, ellipsis) on frontend/src/sites/SiteAction.tsx:1407.
  - Evidence:
    - batch-04/s602b/action-history-verified-replay-390-app.png
    - batch-04/s601b/action-history-all-390-app.png
    - the 1440 versions of both.

### Flags, not counted (pre-existing in the frozen capture, not cut text, no register row)

These are unlabelled `DataTable` scrollers with no tabindex, no role, no name and no focusable descendant. They sit inside closed disclosures, which these batches never opened. The content scrolls by touch, mouse or trackpad with a visible scrollbar. They do not pass the batch-17 probe's attribute test, though Chrome (155 here) makes such scrollers keyboard-focusable by default. Same class as the batch-17 note; not the one-line-ID class.
- **F1 Health "Technical details":** the two tables at frontend/src/sites/SiteHealth.tsx:623 and :772 overflow at 390 (640 and 663 px in 284 px, measured on health kobo001-gateways). Evidence: batch-02/part-health/health-kobo001-gateways-390-app.png (disclosure closed).
- **F2 Financials "How this was worked out":** the "Generator power readings counted" table at frontend/src/sites/FindingConsequence.tsx:455, inside the ExactReferences disclosure at :924. The mapping is by component; the measured nested scroller is 408 px in 286 px on financials priced-current/mixed. Its cells are times and plain `code` IDs.
- **F3 Asset (battery) "Technical details":** the channel ID table at frontend/src/sites/SiteBattery.tsx:482 (6 ID columns). Unmeasured: batch 01 does not measure closed content.

### Other observations (not clipping)
- **cold-findings at 1440:** the new table overflows its scroller by 5 px (1125/1120). This draws a full-width scrollbar although nothing is cut; the region is labelled (frontend/src/sites/ColdAssessmentViews.tsx:1293). Cosmetic. Image: batch-07/part-excursion/cold-findings-stocked-1440-app.png.
- **recommendation at 390:** the `battery` token in "Battery reserve 30% to 25% on battery" breaks mid-word ("batter / y") because of `word-break: break-all` on `.action-ref` (frontend/src/ui/primitives.css:3826-3830). It wraps; nothing is cut. Image: batch-04/s602b/recommendation-verified-replay-390-app.png.
- **foundation imported-period at 390:** the native period select shows "At 2026-09-30 00:00 UTC (from th…". This is the browser's own select truncation: the full option text is in the open list and repeated in the line above. Not counted.
- Scrollers measured at 1440 on action-evidence (1990/1088), evidence-analysis Deliveries (1209/1065) and sitework (853/104) are inside closed disclosures (not visible in the screenshots). Their tables are labelled: SiteWorkActions.tsx:240 and LedgerSiteEvidence.tsx:1038-1081.

## Pairs covered
- **By measures (step 1):** all 356 pairs. Batch 01: 40, 02: 62, 03: 72, 04: 50, 05: 26, 06: 46, 07: 60.
- **By eye (step 2), 390 app images. Longest page per screen ID, plus extras.**

batch-01:
- populated/asset-kobo001-battery
- s601b/changes-applied
- s602b/changes-effect
- populated/foundation-imported-period
- populated/readiness-now
- populated/sites-stocked
- populated/sld-battery

batch-02:
- part-dispatch/analysis-limited
- part-dispatch/dispatch-supported
- part-evidence/evidence-no-readings
- part-evidence/evidence-analysis-supported
- part-health/health-kobo001-gateways
- part-mini/mini-ordinary-no-amount

batch-03:
- part-s408-owner/assumptions-recorded-T3
- part-s408-owner/financials-priced
- part-s404-late/finding-late-stale
- part-s404/finding-evidence-latest
- part-s404/finding-history-version1
- part-s404/sitefindings-stocked

batch-04:
- s602b-guardrail/action-evidence-guardrail
- s602b/action-evidence-pass
- s601b/action-execution-failed-pending
- s601b/action-history-all
- s602b/action-history-verified-replay
- s602b/action-overview-verified-replay
- s602b/action-plan-exact-plan
- s602b/recommendation-verified-replay

batch-05:
- s603/sitework-positive
- s603/sitework-page1-limit1
- s602b-case-guardrail/verification-guardrail

batch-06:
- backup-failed/cold-finding-start-backup-failed
- excursion/cold-foundation-stocked
- excursion/cold-readiness-stocked
- excursion/cold-sld-stocked
- normal/coldbackup-normal
- backup-failed/temperature-backup-failed

batch-07:
- part-excursion/cold-stocked
- part-excursion/cold-assumptions-stocked
- part-excursion/cold-evidence-stocked
- part-excursion/cold-evidence-analysis-stocked
- part-excursion/cold-financials-stocked
- part-excursion/cold-findings-stocked

1440, checked where a desktop scroller was measured:
- batch-07 cold-findings-stocked
- batch-05 sitework-positive

## Not done
- No re-capture (step 3). Every suspected item could be judged from the stored measures and the code. F1-F3 could be confirmed with an `openAll` run of `batch-17/tools/probe-scrollers.mjs` (s701 for health, s408 for financials, the batch-01 populated serve for asset), if the coordinator wants that.
- No product code edited, nothing committed. Nothing to clean up.
