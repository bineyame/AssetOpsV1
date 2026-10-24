# Post-W6 audit batch 16: W5 EV depth/work

IDs: `availability`, `energy`, `ev-health`, `ev-scenarios`, `ev-work`. Branch `audit/batch-16` at main `cb79b18b` (product code identical to frozen `fddf5cad`), worktree `AssetOpsV1-review5`. Mock authority: `frontend/mockups/v69/index.html`, served by the same Vite origin and rendered at 1440x1000 and 390x900 CSS px.

All dispositions are **proposals** for the Architect. This batch adds no register rows. Machine-readable record: `batch-16.json` (88 pairs plus 26 link-check captures that are not counted). Side-by-side view: `index.html`. Difference source: `differences.json`, written by `tools/differences.py`.

## Route reconciliation (`frontend/src/App.tsx`)

| ID | Mounted route | Status |
| --- | --- | --- |
| `availability` | `SITE_PERFORMANCE_SUBTAB_ROUTE_PATH` `/sites/:siteId/performance/availability` (EV branch, `EvAvailability` in `SiteAnalyticsFrames.tsx`) | mounted |
| `energy` | same route, `/performance/energy` (`EvEnergy`) | mounted |
| `ev-health` | `SITE_HEALTH_ROUTE_PATH`, where `SiteHealthFrame` dispatches EV_CHARGING to `EvHealthDepth` | mounted |
| `ev-scenarios` | `SITE_EV_SCENARIOS_ROUTE_PATH` `/sites/:siteId/ev/financials/scenarios` (`SiteEvFrame view="scenarios"`, `evScenarioList`) | mounted |
| `ev-work` | `SITE_WORK_ROUTE_PATH` -> `SiteWorkFrame` (domain Work, R112 Window) | mounted |

The routes are correct. Note: `SITE_FINANCIAL_SCENARIOS_ROUTE_PATH` (`/sites/EV-LAB-001/financials/scenarios`) is *not* the EV scenarios page. For an EV Site it reads 'Scenarios are read for mini-grid sites only.' (B16-16).

## Producer, environment and capture

- **Producer (reviewed, unmodified):** `W504_API_PORT_BASE=18600 tools/w504_ev_work_walkthrough.py --work var/w504a_b16 --tag b16`, run as `prepare`, `serve`, `attest`, then `drop`.
  - `W504_API_PORT_BASE` is the producer's own documented port knob (W5-04 V3b), so the APIs ran in my range 18601-18607 and did not collide with batch 15's 8971-8977.
  - DBs: `w504a_{positive,zero,worstcase,unknown}_b16_test` (producer `*_test` authorization). I checked `pg_database` first: no `w504a` DB existed, and only batch 15's `w502b_*_b15_test` DBs were present.
  - The tool writes only to `var/w504a_b16` (gitignored). No tracked file changed.
  - Logs and the manifest copy are in `logs/`.
- **Modes:** positive (ev-interrupted, attested INC/WR + links), zero, and worstcase (5 Actions with 160-code-point title and owner) were ready.
  - `unknown` (ev-missing-meter) came back **unavailable** ('the replay selected 0 SUPPORTED EV Findings'), so it was not served.
  - `pending` and `stale` are unavailable by design.
  - `forbidden` is a tool-local gate on the domain-work routes only.
  - `unavailable` is the whole API, stopped by `attest`.
- **Servers:** Vite ran on 127.0.0.1:5186 `--strictPort` and was restarted per mode (`tools/run_phase.ps1`, `tools/run_rest.ps1`). Headless Chrome used CDP 9526.
- **Capture:** `tools/capture-b16.mjs` is batch 14's capture-only wrapper (CDP 9526). It adds backtick-text, `cN · ENUM` raw-connector and inner vertical-scroll detection, and the plural regex now also covers sessions, connectors and records. Targets come from `tools/mk_targets.py`, generated from the walkthrough manifest.
- **Claims:** positive 400/408 (the 8 failures are the depth refused pairs, 0 panels against 1-3), zero 24/24, worstcase 48/48, forbidden 24/24, unavailable 22/24 (whole-API 503, see B16-13), links 70/72 (Sessions against the Overview mock is a deliberate cross-reference), links2 72/72, links3 12/12.
- **Windows:**
  - Depth window E: `2026-10-06T08:00Z-09:00Z`.
  - Empty: 5 Oct, same hours.
  - Early cutoff: `known_at=08:30Z`.
  - Work window W: UTC day 24-25 Oct.
  - Zero: 23-24 Oct.

## Cases and pairs (88)

| Screen | Cases (x2 widths) |
| --- | --- |
| availability / energy / ev-health / ev-scenarios | current, empty-window, known-at-before-watermark, refused-reversed, no-window, work-day-window, all-open (7 each). ev-health and ev-scenarios also have worstcase-db. availability also has forbidden-403 and store-unavailable-503 |
| ev-work | positive, historical, refused-reversed, refused-span-32d, no-window, all-open, zero, zero-mode-current-day, worstcase, worstcase-all-open, forbidden-403, store-unavailable-503 (12) |

That is 10 representative pairs plus 78 further states.

Link checks, not counted:
- EV Overview: the main-tab Overview and `/ev`.
- EV Site Findings and Sessions.
- Generic `/financials` and `/financials/scenarios`, `/ev/financials` and main-tab Evidence.
- ev-work-incidents (also refused) and ev-work-maintenance.
- ev-foundation.

**Not producible:**
- B16-09: any authored EV scenario, including the five-row worst case.
- B16-10: depth missing-meter, pending, historical, stale, status-gap and declared-empty-schedule states.

## Structural verdict

Panel count, order and titles match the mock on all 78 non-refused, non-503 pairs:
- availability: 3 panels
- energy: 3 panels
- ev-health: 1 panel (Condition and evidence)
- ev-scenarios: 1 panel (Financial scenarios)
- ev-work: 1 panel (Actions at this site)

Table columns match on ev-health, the energy bridge and ev-work. There is no page horizontal overflow (max 0) and no console error on any pair. At 390 the Site tab row scrolls inside its container (521 in 358), as do the energy tables (640 in 318) and the all-open worst-case Work table (820 in 318). The only clipping is the intended two-line clamp on the worst-case Work rows.

Every page is inside the W5-03 page caps and the W5-04 ruling 25/50 caps. Panels over 1.3x have measured reasons: ev-health 1.64x/1.59x (B16-11), ev-work worst case (B16-12), and the energy all-open and Work empty states (B16-17).

## Mandatory carried checks

| Item | Result |
| --- | --- |
| '1 incidents' plural (B13-01) | Not on these five screens. The ev-work strip correctly reads '1 action'. **Recurs on ev-work-incidents** ('Scoped to EV · 1 incidents', '1 maintenance'). New plurals: availability '1 scheduled hours' (B16-06); Sessions and EV Overview '1 accepted starts', '1 observed aborts', 'of 1 attempts' (B16-14/15). |
| Raw `c1 · EV_CONNECTOR` | **Confirmed** in the ev-work-maintenance Asset cell. The five audited screens use 'Connector c1' (0 hits). B16-14 |
| domainActionClient window error | **Confirmed on EV** (B16-02 = B14-02): a reversed window and a 32-day span both give 'The window may span at most 31 days.' The EV depth pages show the raw `EV_WINDOW_INVALID` text instead (B16-01). ev-work-incidents shows the backticked server text (B13-04 recurs). |
| R88/R112 Window control | R112 built and verified on ev-work: 33 px at 1440, 136 px stacked at 390. Its register status still reads 'planned'. The depth pages have no control (B16-01; extend R88/R112). |
| Prose size | 14 px panel sentences on availability and the ev-work empty state (B1-07/B2-03). |
| Tall 390 header | Depth refused pages have a 288-318 px dark block; the 503 page has mainTop 397. Normal elsewhere (92 px). |
| D3 R22/R23/R24/R37/R38/R60 | **R60 verified**: ev-health has only Condition and evidence, with no Data sources panel. R24 (ev-work-incidents) holds: times are Etc/UTC, which is Site-local. The others do not touch these screens. |
| B13-07 capped Scenarios inner scroll | Not checkable: no authored EV rows (B16-09). The 0-item panel has no inner scroll. |
| B9-02 / B9-10 | **Both still open** against the now-built pages (B16-15). The EV Overview Availability card says 'Not assessed' while the page shows 57.7%. Charger condition is unlinked. EV Site Findings is still the mini-grid index. |

## Differences (proposals)

| ID | Screens | What | Proposed disposition |
| --- | --- | --- | --- |
| B16-X1 | all | B1-01, B1-04, B2-02, B1-07, B1-02 (refused/503 at 390), B1-53. B2-21 is not applicable (Etc/UTC Site) | Cite |
| B16-01 | depth | B14-01 recurs: refused drops all furniture, raw `EV_WINDOW_INVALID`, useless Retry, no window control | Cite B14-01 |
| **B16-02** | ev-work | B14-02 recurs: one '31 days' message for a reversed window and a 32-day span | Cite B14-02 (D3 Low) |
| B16-03 | ev-work | R112 and R113 verified; plural correct on EV; R112 status stale | (a); update R112 status |
| B16-04 | ev-work | B14-09 recurs: the default window excludes today; false 'raised here yet' | Cite B14-09 |
| B16-05 | ev-health, ev-work | Asset, session and Finding UUIDs | Cite B1-53/B14-05 |
| B16-06 | availability | '1 scheduled hours' plural; card units h/min against the mock's connector-h | D3 Low; D4 candidate |
| B16-07 | energy | Bridge row 1 'Unknown' despite 15 kWh; 'scenario is being refreshed' on a CURRENT read with no scenario; point-only chart | D3 Low; D4 candidate |
| B16-08 | ev-scenarios | B14-08 recurs: 'Placeholder' literals; cold/mini example copy | Cite B14-08 |
| **B16-09** | ev-scenarios | No committed producer authors an EV scenario | **Blocker**: Architect to commit a producer mode |
| B16-10 | depth | Missing-meter, pending, historical, stale, status-gap and declared-empty states have no committed producer; the forbidden gate covers Work only | Spec/producer note |
| B16-11 | ev-health | 1.64x/1.59x within the 410/540 cap; R56-R60, R95, R96 and R103 verified | (a); accept |
| B16-12 | ev-work | Worst case within ruling-25 caps | Informational |
| B16-13 | ev-work | 403 in panel; the 503 vector is a whole-API stop | Informational |
| B16-14 | link check | B13-01 and B13-04 recur; `c1 · EV_CONNECTOR` confirmed; Sessions plurals and hashes | Cite |
| B16-15 | link check | B9-02 (57.7% against 'Not assessed') and B9-10 still open | Keep the D3s open |
| **B16-16** | all | EV main tabs Overview, Evidence and Financials land on placeholder or mini-grid pages, while `/ev`, `/ev/evidence` and `/ev/financials` are built | **D3 Medium**, shared tab seam with B14-10 |
| B16-17 | energy, work, availability | Other >1.3x or short panels have measured reasons; all page caps hold | Accept |

## Blockers

- B16-09: no committed authored EV-scenario producer.
- B16-10: depth states have no committed producer.

The ports came from the producer's own knob (18601-18607), and the `unknown` mode was unavailable. No DBs or processes remain after `drop` (see `logs/w504-drop.log`).
