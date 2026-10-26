# Final recapture batch 06: W2 cold Foundation/assessment

Main SHA 89a11477. Pairs 46 (frozen 46). Counts: FIXED 24, PASS 22

Method: original capture tool and producers (unmodified), same ports, fresh DBs; each pair compared with the frozen evidence (panel titles, heights, rows, columns, links, chips, typography, overflow, header band, tab-row scroll, caps) and the frozen mock (unchanged). Classification derived from measured deltas plus register/rulings; standing D1/D2/D4 rows and ruled caps count as PASS. FIXED = a measured signal that a frozen D3 difference is gone.

## REGRESSION-OPEN (0)
- none

## GAP (0)
- none

## Notes for the coordinator
- Producer `.agent/W2-F-evidence/seed.py` (unmodified; cold excursion, normal, backup-failed, each recreating the DB; `ASSETOPS_TEST_TEMPLATE=0`) ran against `assetops_audit_b06_test` (created by me, dropped at the end). API 18601 (host/lab_app.py, restarted per phase), Vite 5186, CDP 9526. Record ids are deterministic (hold_uuids) and equal the frozen ids, so the frozen targets were reused as is.
- FIXED signal on 30 pairs: the 390 Site tab row no longer scrolls horizontally (23 pairs report fewer horizontal scrollers) and the Site tab rows changed. coldbackup/normal: the 14px prose line in the chain panel is gone (14px prose reduced, panel 148->125 / 179->156).
- Observation: the refused / unknown-id / start-refused-window states now show a collapsed technical-details disclosure in the refusal panel (panel 96->113 px at 1440, 96->129 px at 390; temperature/coldbackup refused pageH 934->1060 and 1056->1281 at 390). Not an overflow or cap breach; flagged for visibility only.
- No horizontal page overflow, no console errors, no new raw vocabulary, caps unchanged or lower.

## All pairs
| Screen | Case | Width | Class | Why |
|---|---|---|---|---|
| temperature | backup-failed | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| temperature | backup-failed | 390 | FIXED | fewer horizontal scrollers |
| coldbackup | backup-failed | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| coldbackup | backup-failed | 390 | FIXED | fewer horizontal scrollers |
| coldbackup | default-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| coldbackup | default-window | 390 | FIXED | fewer horizontal scrollers |
| cold-finding | start-backup-failed | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-finding | start-backup-failed | 390 | FIXED | fewer horizontal scrollers |
| cold-finding | start-refused-window | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-finding | start-refused-window | 390 | FIXED | fewer horizontal scrollers |
| cold-foundation | stocked | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-foundation | stocked | 390 | FIXED | fewer horizontal scrollers |
| cold-foundation | no-version | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-foundation | no-version | 390 | FIXED | fewer horizontal scrollers |
| cold-readiness | stocked | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-readiness | stocked | 390 | FIXED | fewer horizontal scrollers |
| cold-readiness | no-version | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-readiness | no-version | 390 | FIXED | fewer horizontal scrollers |
| cold-sld | stocked | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-sld | stocked | 390 | FIXED | fewer horizontal scrollers |
| cold-sld | no-version | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-sld | no-version | 390 | FIXED | fewer horizontal scrollers |
| temperature | excursion | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| temperature | excursion | 390 | FIXED | fewer horizontal scrollers |
| temperature | no-selection | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| temperature | no-selection | 390 | FIXED | fewer horizontal scrollers |
| temperature | refused | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| temperature | refused | 390 | FIXED | fewer horizontal scrollers |
| coldbackup | excursion | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| coldbackup | excursion | 390 | FIXED | fewer horizontal scrollers |
| coldbackup | no-selection | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| coldbackup | no-selection | 390 | FIXED | fewer horizontal scrollers |
| coldbackup | refused | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| coldbackup | refused | 390 | FIXED | fewer horizontal scrollers |
| cold-finding | start-excursion | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-finding | start-excursion | 390 | FIXED | fewer horizontal scrollers |
| cold-finding | unknown-id | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-finding | unknown-id | 390 | FIXED | fewer horizontal scrollers |
| cold-finding | excursion-finding | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-finding | excursion-finding | 390 | FIXED | fewer horizontal scrollers |
| temperature | normal | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| temperature | normal | 390 | FIXED | fewer horizontal scrollers |
| coldbackup | normal | 1440 | FIXED | 14px prose reduced |
| coldbackup | normal | 390 | FIXED | 14px prose reduced; fewer horizontal scrollers |
| cold-foundation | normal-replay | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| cold-foundation | normal-replay | 390 | FIXED | fewer horizontal scrollers |
