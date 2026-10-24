# Post-W6 audit batch 15: W5 cold cases/Action

IDs: `cold-work-incidents`, `cold-work-maintenance`, `cold-action`. Branch `audit/batch-15` at main `1e3e9e8a` (product code identical to frozen `fddf5cad`), worktree `AssetOpsV1-review6`. Mock authority: `frontend/mockups/v69/index.html`, served by the same Vite origin and rendered at 1440x1000 and 390x900 CSS px.

All dispositions are **proposals** for the Architect. This batch adds no register rows. Machine-readable record: `batch-15.json` (88 pairs). Side-by-side view: `index.html`. Difference source: `differences.json` (written by `tools/differences.py`). One-line-per-pair digest: `logs/brief-all.txt`.

## Route reconciliation (`frontend/src/App.tsx`)

| ID | Mounted route | Status |
| --- | --- | --- |
| `cold-work-incidents` | `SITE_WORK_INCIDENTS_ROUTE_PATH` `/sites/:siteId/work/incidents` -> `SiteWorkCasesFrame kind="incidents"` | mounted |
| `cold-work-maintenance` | `SITE_WORK_MAINTENANCE_ROUTE_PATH` `/sites/:siteId/work/maintenance` -> `SiteWorkCasesFrame kind="maintenance"` | mounted |
| `cold-action` | `SITE_ACTION_VIEW_ROUTE_PATH` `/sites/:siteId/actions/:actionId/verification` (domain Action region of `SiteAnalyticsFrames.tsx`) | mounted |

The spec route table is correct for these IDs, and so are its producers: the W502 selected case reads and the W5-02c declared-criteria detail reads are the same committed tool.

## Producer, environment and capture

- **Producer (reviewed, unmodified):** `tools/w502_cold_work_walkthrough.py --work var/w502b_b15 --tag b15`, run as `prepare` (all five modes, none blocked), then `serve` (7 healthy APIs), `attest` (ATTEST OK) and `drop`. Logs are in `logs/w502-*.log`.
  - DBs: `w502b_{positive,worstcase,pending,stale,unknown}_b15_test`, under the producer `*_test` authorization. I checked `pg_database` first: no `w502b` DB existed, and only batch 13's `assetops_audit_b13_test` was present.
  - **Port deviation (as in batch 14):** `serve` hard-codes API ports 8971-8977, which are outside 18501-18509. I checked they were free first.
  - The tool writes only to `var/w502b_b15` (gitignored).
- **Servers:** Vite 127.0.0.1:5185 `--strictPort`, restarted per mode with `ASSETOPS_API_PORT` (`tools/run_phase.ps1` for positive, `tools/driver.ps1` for the rest). The per-phase child form blocked on an inherited stdout pipe after its capture had finished, so the remaining phases ran in one detached driver. Headless Chrome used CDP 9525. Every Vite PID I started was stopped by PID.
- **Capture:** `tools/capture-b15.mjs` is batch 14's wrapper with CDP 9525 and an added `b15` DOM block. It records the breadcrumb, header buttons, strip, Related sentence, Inspect control, criteria, rows' `data-work-state` and body text. `openAll` sets `details.open`, which is viewer-only. Targets come from `tools/mk_targets.py`, built from the walkthrough manifest's `case_reads`, `detail_reads`, `reads` and `cutoffs`.
  - Claims: positive 270/276 (the 6 failures are the cold-action state-panel pairs: 1 untitled panel against the mock's 2, per R101), worstcase 72/72, pending 36/36, stale 36/36, unknown 36/36, forbidden 34/36 and unavailable 34/36 (cold-action state panel in both).
  - The first unavailable run had a cold-compile blank (B15-13). It was rerun with a warm-up navigation outside the batch folder.

## Cases and pairs (88)

| Screen | Cases (x2 widths) |
| --- | --- |
| cold-work-incidents / cold-work-maintenance | current, positive-cutoff, historical, zero, refused-reversed, refused-span-32d, no-window, all-open, worstcase, worstcase-all-open, pending, stale, unknown, forbidden-403, unavailable-503 (15 each) |
| cold-action | positive, all-open, not-linked (K1), historical (K3), not-found, invalid-known-at, future-known-at, worstcase, worstcase-all-open, pending, stale, unknown, forbidden-403, unavailable-503 (14) |

That is 6 representative pairs plus 82 further states. "Limited" here means the pending, stale, unknown and historical currentness states.

**Not producible (B15-10):** the producer links only a COMPLETED request to an Action, and the five worst-case requests (COMPLETED + 4 OPEN) are not linked to any Action. The cold-action Related-activity copy for a linked OPEN/IN_PROGRESS request (R102), VERIFICATION_WINDOW or CANCELLED therefore cannot be captured.

## Structural verdict

Panel count, order and titles match the mock on all 76 loaded pairs:
- the case tabs: one panel, 'Incidents at this site' or 'Maintenance at this site', with the mock's five columns in order;
- cold-action: 'Declared outcome criteria' (3 columns, 4 mock-exact rows) and 'Related activity'.

The 12 cold-action state pairs (not-found, 422 client and server, 403, 503) show one untitled panel, as ruled by R101.

- No page horizontal overflow and no console errors on any pair.
- Clipping is only the intended two-line clamp on the worst-case rows (R94). The case tables scroll horizontally at 390 (R93).
- The Action chrome matches the mock (B15-01). Panels over 1.3x all have a measured reason and sit within the K3/K4 caps (B15-09).

## Mandatory carried checks

| Item | Result |
| --- | --- |
| '1 incidents' plural | **Confirmed** on the incidents strip in every one-row state. '1 maintenance' is the same on the maintenance strip. The mock has the same literal. B15-02. |
| Raw `c1 · EV_CONNECTOR` | Not applicable (0 hits). Analogues: 'Action 5198a58a' link labels, Finding id8, and basis 'COMPLETE' and 'List fence sha256' (B15-X1, B1-53). |
| domainActionClient window error | The case tabs do not use it. They show distinct but raw server texts ('`from` must be before `to`.' and 'The window may span at most 31 days.'), under a false strip cause, 'work source unavailable' (B15-03). B14-02 remains cold-work only. cold-action: bad and future `known_at` both show 'Cold work unavailable' with Retry (B15-04). |
| R88/R112 Window control | R88 verified on both case tabs: 33 px at 1440, 136 px stacked at 390. cold-action has no control, by design. R112 is EV-only. B15-05. |
| Prose size | cold-action panel prose is 14 px against the mock's 12 px (B1-07). The case tabs match (11/12 px). |
| Tall 390 header | **Confirmed** on the cold-action state panels: 275-334 px dark block. Case-tab refusals keep their furniture, at 107-118 px. |
| D3 R22/R23/R24/R37/R38/R60 | **R23 verified closed:** the Window column is Site-local, e.g. 19:11 for 16:11Z (B15-12). The others do not touch these screens. |
| Carried Architect item (VERIFICATION_WINDOW/CANCELLED copy) | Still open in code (DomainActionVerification.tsx:92-96), and not producible. B15-10. |
| B4-03/B4-04/B4-05/B5-01 Action chrome | **Do not recur** on cold-action (B15-01). |
| B4-19 raw event-code fall-through | Not applicable: these screens show no event history, and all chips are labelled (B15-11). |
| B14-02 / B14-03 / B14-04 / B14-09 | B14-02 does not recur on the case tabs (distinct messages, see B15-03). B14-03's plural recurs as B15-02. B14-04: the case chips are toned (Open, Completed, Unverified), so it does not recur here. B14-09 extends to maintenance (B15-06). |

## Differences (proposals)

| ID | Screens | What | Proposed disposition |
| --- | --- | --- | --- |
| B15-X1 | all | Cross-cutting rows: B1-01, B1-04, B2-02, B1-07 (cold-action), B1-02 (cold-action states at 390), B1-53, B2-21/B3-04 | Cite |
| B15-01 | cold-action | Action-rooted breadcrumb, a single Verification tab row, Open site, rail on Actions: B4-03/04/05 and B5-01 do not recur | (a) R69 verified; the cold shell is the precedent for the W1 fix |
| B15-02 | cases | '1 incidents' / '1 maintenance' | D3 Low, shared plural owner with B14-03 |
| B15-03 | cases | Raw backticked window error; strip says 'work source unavailable' for an invalid input or 403; badge-styled 'This list cannot be shown'; 'As of: time not recorded' | D3 Low (W4 refusal copy); cite B1-53 |
| B15-04 | cold-action | 'Cold work unavailable' with Retry for a bad or future `known_at` and for a 403; raw 'known_at' and Site code; differs from the case tabs | R101 verified; copy D3 Low (with B15-03/B12-06) |
| B15-05 | cases | R88 verified (136 px at 390); window kept in subtab links | (a) R88 |
| B15-06 | cases | Default window shows Incidents (1) but Maintenance (0): requests are windowed by created_at while their 'Occurred' time is inside the window, and no copy says so | D3 Low (extends B14-09); Architect to confirm |
| B15-07 | cases | Closing notice drops the mock's 'New work starts...' sentence; R01 lists cold-work only | (b) D1: extend R01 |
| B15-08 | all | Link departures R65/R66/R68/R70-R73/R89 present as registered | (a) verified |
| B15-09 | all | >1.3x panels: empty/basis, all-open UUIDs, worst case, 390 Related; all within the K3/K4 caps | Informational; propose accept |
| **B15-10** | cold-action | VERIFICATION_WINDOW/CANCELLED (and R102 OPEN) Related copy: still the generic sentence in code; not producible | Architect: rule the copy and add a producer mode |
| B15-11 | all | R91 currentness notices placed and toned per status | (a) R91 |
| B15-12 | incidents | R23 closed (Site-local Window column) | (a) |
| B15-13 | capture | Cold-compile blank on the first navigation (unavailable 1440), retaken | Informational |

## Blockers

None for this batch's scope. B15-10 is a coverage gap: there is no producer mode for a linked OPEN, VERIFICATION_WINDOW or CANCELLED request. The port 8971-8977 deviation is recorded above. No DBs or processes remain.
