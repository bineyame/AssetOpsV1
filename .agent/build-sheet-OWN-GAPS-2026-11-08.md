

## D-SR.31-38 Every tab follows the range; SR-10 to SR-14 (Architect, Claude, 2026-11-12 night, owner-directed, logged for owner review)

- Owner, verbatim (`.agent/owner-all-tabs-respect-range-2026-11-12.md`): "all tabs should respect the date range without exception"; "we have to work on the items and reassess on saturday and not limit what is in or not now". Detail: sequence doc **Revision 10b**.

### D-SR.31 Fuel and Backup ranges come from stored day rows, not a chain measure.
- Correction to 10a: `avoidable_gen_min` is dispatch minutes, not fuel. A new MINIGRID measure would change every day grade, so it is ruled out. Two `site_period_read` kinds, `mini_depth.fuel_day` and `mini_depth.backup_day` (local_day grain, every Site-local hour through `MiniDepthRead._hour`), with the existing register, tick and `period_backfill` CLI. There is no migration and no builder-version bump. An absent row reads STILL_PROCESSING.

### D-SR.32 SR-10 Fuel range (Kobo, 0.9 with the core).
- `fuel-range` route, `site-fuel-range-1`, a modelled expected-use band per day, and residual never summed. Page `MiniFuelRange.tsx`. MOCK DEVIATION R727.

### D-SR.33 SR-11 Backup range (0.6).
- `backup-range` route, `site-backup-range-1`, backup start sequences per day de-duplicated by chain, never an outage count. Page `MiniBackupRange.tsx`. MOCK DEVIATION R728.

### D-SR.34 Sweep result.
- Data tabs that still had a label instead of range output: Kisiwa fuel-check nights (SR-10k, 0.25), Evidence rejections (SR-12a, 0.3), Evidence analytics readiness (SR-12b, 0.25), Foundation changes list (SR-13, 0.2), price and EV assumption history (SR-14, 0.3, R729).

### D-SR.35 What stays N (not a period).
- Foundation and its views and SLD (configuration), battery/asset configuration pages (pending the SR-4 asset list; readings mean SR-9), the Sites index, and single-record detail pages. The owner confirms this on Saturday.

### D-SR.36 Demo backfill.
- `period_backfill build` for the two kinds on KOBO-001 and KISIWA-001 after the VPS prepare. If the head-count pre-flight shows missing fuel/backup heads, stop and ask; no reconcile without a ruling.

### D-SR.37 Lanes and order.
- G: SR-4, then SR-12a, SR-12b, SR-13. H: SR-5, then SR-5c, SR-5d, SR-14. I: SR-6, then SR-10k. J: SR-7, then SR-11. K: SR-8, then SR-10. The non-range items follow in priority order, with AR-4 and WARM-1 first if unmerged.
- Merge order: SR-4, 5 core, 6, 7, 8, 5c, 5d, 10, 11, 10k, 12a, 12b, 13, 14, then the rest.
- Package about 18.6 units (was 15.8). The freeze tail is at risk; nothing is dropped now.

### D-SR.38 Saturday reassessment replaces the drop order.
- Sat 14 Nov 12:00. Inputs: merged and ACCEPTed units, High/Medium findings, the parity/timing JSONs, the rehearsal check, and units left per lane. Candidates to the owner, in deferral order: DATA-10/13, FR-B, UQ-FI-3, DATA-5/4/8, MB-1, UP-1, SR-14, SR-13, SR-12b. The options are after the freeze, or the freeze moved to Sun 15 Nov 20:00.

Decisions logged for owner review: **D-SR.31-38**.
