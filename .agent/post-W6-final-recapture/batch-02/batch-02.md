# Final recapture batch 02: W1 Overview/Evidence

Main SHA 89a11477. Pairs 62 (frozen 62). Counts: FIXED 42, PASS 20

Method: original capture tool and producers (unmodified), same ports, fresh DBs; each pair compared with the frozen evidence (panel titles, heights, rows, columns, links, chips, typography, overflow, header band, tab-row scroll, caps) and the frozen mock (unchanged). Classification derived from measured deltas plus register/rulings; standing D1/D2/D4 rows and ruled caps count as PASS. FIXED = a measured signal that a frozen D3 difference is gone.

## REGRESSION-OPEN (0)
- none

## GAP (0)
- none

## Notes
- Producers: s302 (evidence, evidence-analysis), s701 (health), s5_overview/s501 (mini) were run UNMODIFIED with their own `_audit` DB names (assetops_s302_audit, assetops_s701_owner_audit, assetops_s501_owner_audit) and var/*_audit work folders on API 18201, Vite 5182, CDP 9522. The frozen run used run_renamed_producer.py (name-rewriting wrapper, now forbidden), so that wrapper was not used.
- Dispatch and analysis (22 pairs): captured after the owner authorized running tools/s3_dispatch_walkthrough.py UNMODIFIED (owner-s3walk-authorization-2026-10-26.md): prepare dropped and recreated assetops_s3walk (copy of assetops_s3cases, read only), work folder %LOCALAPPDATA%/AssetOps/s3-dispatch-walkthrough; serve --port 18201, Vite 5182, CDP 9522. assetops_s3walk was NOT dropped afterwards (owner's walkthrough DB, producer has no drop). Interval ids from the frozen targets still resolved. FIXED signals: 390 tab row no longer scrolls; dispatch window-id-as-revision no longer throws the frozen TypeError (now renders the mini-grid Site page; panel set changed, reviewed). Capture-claim FAILs 2/132 are analysis-spec-route 'Awaiting evidence migration' = frozen B2-31.
- Evidence-analysis 'Accepted records behind the conclusions' 452 px at 1440 / 662 at 390 closed, 531/740 with a record opened: inside the Q23 caps (1200/1800). Time column header now 'Measured (EAT)'.
- Standing caps unchanged: health Data sources 2.69x/2.22x (R166 D1), mini Operating context / Needs attention 1.39-1.60x (R160 D4, R388 D1), mini 390 Operating context 2.33-2.77x and Bounded money 1.66-1.76x (as frozen), evidence 390 Data sources 1.36-1.45x.

## All pairs
| Screen | Case | Width | Class | Why |
|---|---|---|---|---|
| dispatch | supported | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| dispatch | supported | 390 | FIXED | fewer horizontal scrollers |
| dispatch | limited | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| dispatch | limited | 390 | FIXED | fewer horizontal scrollers |
| dispatch | limited-no-selection | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| dispatch | limited-no-selection | 390 | FIXED | fewer horizontal scrollers |
| dispatch | refused-failed | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| dispatch | refused-failed | 390 | FIXED | fewer horizontal scrollers |
| dispatch | stale-pending | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| dispatch | stale-pending | 390 | FIXED | fewer horizontal scrollers |
| dispatch | default-no-day | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| dispatch | default-no-day | 390 | FIXED | fewer horizontal scrollers |
| dispatch | window-id-as-revision | 1440 | FIXED | h1 text changed; tab rows changed; panel set changed |
| dispatch | window-id-as-revision | 390 | FIXED | h1 text changed; tab rows changed; panel set changed |
| analysis | supported | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| analysis | supported | 390 | FIXED | fewer horizontal scrollers |
| analysis | limited | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| analysis | limited | 390 | FIXED | fewer horizontal scrollers |
| analysis | refused-failed | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| analysis | refused-failed | 390 | FIXED | fewer horizontal scrollers |
| analysis | spec-route | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| analysis | spec-route | 390 | FIXED | fewer horizontal scrollers |
| evidence-analysis | record-opened | 1440 | FIXED | 14px prose reduced; Accepted records behind the conclusions ratio 3.42->2.0; [Accepted records behind the conclusions] table columns changed |
| evidence-analysis | record-opened | 390 | FIXED | 14px prose reduced; Accepted records behind the conclusions ratio 3.33->1.99; [Accepted records behind the conclusions] table columns changed |
| evidence | stocked | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| evidence | stocked | 390 | FIXED | fewer horizontal scrollers |
| evidence | no-readings | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| evidence | no-readings | 390 | FIXED | fewer horizontal scrollers |
| evidence | window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| evidence | window | 390 | FIXED | fewer horizontal scrollers |
| evidence-analysis | no-selection | 1440 | FIXED | [Accepted records behind the conclusions] table columns changed |
| evidence-analysis | no-selection | 390 | FIXED | [Accepted records behind the conclusions] table columns changed |
| evidence-analysis | supported | 1440 | FIXED | [Accepted records behind the conclusions] table columns changed; [How each limit is set] table columns changed |
| evidence-analysis | supported | 390 | FIXED | [Accepted records behind the conclusions] table columns changed; [How each limit is set] table columns changed |
| evidence-analysis | indeterminate | 1440 | FIXED | [Accepted records behind the conclusions] table columns changed; [How each limit is set] table columns changed |
| evidence-analysis | indeterminate | 390 | FIXED | fewer horizontal scrollers; [Accepted records behind the conclusions] table columns changed; [How each limit is set] table columns changed |
| evidence-analysis | limited | 1440 | FIXED | [Accepted records behind the conclusions] table columns changed; [How each limit is set] table columns changed |
| evidence-analysis | limited | 390 | FIXED | fewer horizontal scrollers; [Accepted records behind the conclusions] table columns changed; [How each limit is set] table columns changed |
| evidence-analysis | historical | 1440 | FIXED | [Accepted records behind the conclusions] table columns changed; [How each limit is set] table columns changed |
| evidence-analysis | historical | 390 | FIXED | [Accepted records behind the conclusions] table columns changed; [How each limit is set] table columns changed |
| evidence-analysis | stale | 1440 | FIXED | [Accepted records behind the conclusions] table columns changed; [How each limit is set] table columns changed |
| evidence-analysis | stale | 390 | FIXED | [Accepted records behind the conclusions] table columns changed; [How each limit is set] table columns changed |
| evidence-analysis | refused-other-day | 1440 | FIXED | [Accepted records behind the conclusions] table columns changed |
| evidence-analysis | refused-other-day | 390 | FIXED | [Accepted records behind the conclusions] table columns changed |
| health | kobo001-gateways | 1440 | FIXED | [Data sources · data quality, not equipment condition] table columns changed |
| health | kobo001-gateways | 390 | FIXED | fewer horizontal scrollers; [Data sources · data quality, not equipment condition] table columns changed |
| health | kobo002-nogateway | 1440 | FIXED | [Data sources · data quality, not equipment condition] table columns changed |
| health | kobo002-nogateway | 390 | FIXED | fewer horizontal scrollers; [Data sources · data quality, not equipment condition] table columns changed |
| health | unknown-site-refused | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| health | unknown-site-refused | 390 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| mini | priced | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| mini | priced | 390 | FIXED | fewer horizontal scrollers |
| mini | held | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| mini | held | 390 | FIXED | fewer horizontal scrollers |
| mini | ordinary-no-amount | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| mini | ordinary-no-amount | 390 | FIXED | fewer horizontal scrollers |
| mini | failed | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| mini | failed | 390 | FIXED | fewer horizontal scrollers |
| mini | unassessed | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| mini | unassessed | 390 | FIXED | fewer horizontal scrollers |
| mini | default-no-date | 1440 | FIXED | What happened in the selected hour ratio 1.4->1.03; Operating context ratio 1.39->1.08; Needs attention ratio 1.39->1.08; [Operating context] table columns chan |
| mini | default-no-date | 390 | FIXED | fewer horizontal scrollers; Operating context ratio 2.33->1.17; Bounded money consequence ratio 1.76->1.12; [Operating context] table columns changed |
