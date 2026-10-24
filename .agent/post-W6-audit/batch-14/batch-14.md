# Post-W6 audit batch 14: W5 cold depth/work

IDs: `cooling`, `cold-health`, `cold-scenarios`, `cold-work`. Branch `audit/batch-14` at main `06745622` (product code identical to frozen `fddf5cad`), worktree `AssetOpsV1-review6`. Mock authority: `frontend/mockups/v69/index.html`, served by the same Vite origin and rendered at 1440x1000 and 390x900 CSS px.

All dispositions are **proposals** for the Architect. This batch adds no register rows. Machine-readable record: `batch-14.json` (88 pairs). Side-by-side view: `index.html`. Difference source: `differences.json` (written by `tools/differences.py`).

## Route reconciliation (`frontend/src/App.tsx`)

| ID | Mounted route | Status |
| --- | --- | --- |
| `cooling` | `SITE_PERFORMANCE_SUBTAB_ROUTE_PATH` `/sites/:siteId/performance/cooling` (COLDCHAIN branch, `ColdCooling`) | mounted |
| `cold-health` | `SITE_HEALTH_ROUTE_PATH` -> `SiteHealthFrame` (COLDCHAIN -> `ColdHealthDepth`) | mounted |
| `cold-scenarios` | `SITE_FINANCIAL_SCENARIOS_ROUTE_PATH` -> `SiteFinancialsFrame view="scenarios"` with `coldScenarioList` | mounted |
| `cold-work` | `SITE_WORK_ROUTE_PATH` -> `SiteWorkFrame` (domain Work, R88 Window) | mounted |

The routes are correct. **Spec producer error (B14-15):** the W5-01 producers named in the spec ("cold selected-depth replay", "authored scenario producer") were throwaway seed tests that were never committed (W5-01a/b phase handoffs), so they cannot be rerun unmodified. The register uses the screen ID `cold-cooling` (R05, R13), but the manifest ID is `cooling`.

## Producer, environment and capture

- **Producer (reviewed, unmodified):** `tools/w502_cold_work_walkthrough.py --work var/w502b_b14 --tag b14`, run as `prepare` (all five modes), then `serve`, then `drop`.
  - It creates the DBs `w502b_{positive,worstcase,pending,stale,unknown}_b14_test`. These come under the producer `*_test` authorization. I checked `pg_database` first: no `w502b` DB existed, and only batch 13's `assetops_audit_b13_test` was present.
  - Each mode carries the W5-01 selection: CURRENT, PENDING_RECOMPUTE, STALE_SOURCE or UNKNOWN. Cooling, Health and Scenarios are therefore read from the same reviewed producer.
  - **Port deviation:** `serve` hard-codes API ports 8971-8977, which are outside my 18401-18409 range. I checked they were free before starting.
  - The tool writes only to `var/w502b_b14` (gitignored). No tracked file changed.
- **Servers:** Vite ran on 127.0.0.1:5184 `--strictPort` and was restarted once per mode with `ASSETOPS_API_PORT=<mode port>` (`tools/run_phase.ps1`). Headless Chrome used CDP 9524. Every Vite PID I started was stopped by PID, and the walkthrough's `drop` stopped its recorded API PIDs and dropped its DBs.
- **Capture:** `tools/capture-b14.mjs` is batch 12's wrapper with CDP 9524 and an added `cold` DOM block.
  - The `cold` block records: '1 X' plural hits, `EV_CONNECTOR`, the Window form box and its error, alerts, card links, SVG count, 'Read full text' count and open disclosures.
  - An optional `openAll` flag sets `details.open` (viewer-only: no request and no mutation) for the all-disclosures-open state.
  - Targets are written by `tools/mk_targets.py` from the walkthrough manifest.
  - Claims: positive 294/300 (the 6 failures are the depth refused pairs, with 0 panels against 1-3), links 48/48, worstcase 24/24, pending 84/84, stale 48/48, unknown 48/48, forbidden 12/12, unavailable 12/12. Logs and per-phase summaries are in `logs/`.
- **Windows:**
  - W5-01 depth window: `2026-10-23T16:00Z-17:05Z` (stale: to 17:30Z).
  - Work window: UTC days 23-25 Oct.
  - Empty: 22 Oct, same hours.
  - Historical: pending DB with `known_at=K0` (the pre-late cutoff), which reads HISTORICAL, as in the W5-01 late-reading sequence.

## Cases and pairs (88)

| Screen | Cases (x2 widths) |
| --- | --- |
| cooling / cold-health / cold-scenarios | current-limited, empty-window, refused-reversed, no-window, work-day-window, all-open, pending, historical, stale, unknown (10 each) |
| cold-work | positive, zero, historical, refused-reversed, refused-span-32d, no-window, all-open, worstcase, worstcase-all-open, pending, stale, unknown, forbidden-403, store-unavailable-503 (14) |

That is 8 representative pairs plus 80 further states. Another 8 link-check captures are not counted: cold Overview with a window, bare cold Overview, cold Site Findings and cold Temperature.

**Not producible (B14-16):** a cold scenario with an authored row (authored, expanded, historical-with-row, or the five-row worst case). No reviewed producer commits one, so those layouts are unverified.

## Structural verdict

Panel count, order and titles match the mock on all 82 non-refused pairs:
- cooling: 3 panels (Recovery curves, Context normalization, Next best evidence)
- cold-health: 1 panel (Condition and evidence)
- cold-scenarios: 1 panel (Financial scenarios)
- cold-work: 1 panel (Actions at this site)

The cooling strip, the four cards and the notice sit in mock order, as do the three cold-health cards. Table columns match.

- No page horizontal overflow (max 0) and no console errors on any pair.
- 390 scrolling is intended: the Site tab row (521 in 358) and the cooling chart (480 in 318) scroll inside their containers.
- The only clipping is the intended two-line clamp on the worst-case Work rows.

Panels over 1.3x the mock, with measured reasons:
- cooling, 390 Recovery curves: 1.75x (B14-06).
- cold-work worst case: 2.0-3.9x (B14-11).
- cold-health and cold-work, smaller empty/all-open cases: B14-17.

All of these are inside the W5-01 C2/C3 and W5-02 K2 ruled caps.

## Mandatory carried checks

| Item | Result |
| --- | --- |
| '1 incidents' plural | Not present: tabs read 'Incidents (1)'. **'1 actions'** appears in the cold-work strip in every one-Action state (the mock has the same typo). B14-03. |
| Raw `c1 · EV_CONNECTOR` | Not applicable (0 hits). Analogues: asset and evidence UUIDs (B14-05). |
| domainActionClient window error | **Confirmed:** a reversed window and a 32-day span both show 'The window may span at most 31 days.' (B14-02). Cold depth pages show the raw `COLD_WINDOW_INVALID` server text instead (B14-01). |
| R88/R112 Window control | R88 verified on cold-work: 33 px at 1440, 136 px stacked at 390. The depth pages have no control (B14-01, extend R88). |
| Prose size | 14 px panel text on cooling and on the cold-work empty state (B1-07/B2-03). |
| Tall 390 header | Depth refused pages, 288-318 px dark block. Normal elsewhere (92-95 px). |
| D3 R22/R23/R24/R37/R38/R60 | **R22 verified closed** (no Data sources panel on cold Health). The others do not touch these screens. |
| B7-03 / B7-01 cross-check | **Both still open.** The Overview Cooling card is unlinked, and the Maintenance card says 'Not recorded' with no Work link. The Overview says 'No incident recorded' while this producer has an INC and a completed WR inside the window. Cold Site Findings is still the mini index (B14-14). |

## Differences (proposals)

| ID | Screens | What | Proposed disposition |
| --- | --- | --- | --- |
| B14-X1 | all | Cross-cutting rows: B1-01, B1-04, B2-02, B1-07, B1-02 (depth refused 390), B1-53, B2-21/B3-04 (all UTC on an Addis Site) | Cite |
| B14-01 | depth | Refused: strip, cards and panels dropped; raw `COLD_WINDOW_INVALID` text; a Retry that cannot succeed; no window control | B6-13/B9-05; B1-53; D3 Low; extend R88 (D1) |
| **B14-02** | cold-work | One generic 'at most 31 days' message for a reversed window and for a 32-day span (carried item confirmed) | D3 Low, shared domainActionClient owner |
| B14-03 | cold-work | R88 verified (390: 136 px); '1 actions' plural | (a) R88; plural D3 Low |
| B14-04 | all | Neutral grey strip and Match chips (mock: amber/toned) | D3 Low or D2 (B12-02 seam) |
| B14-05 | cooling, health | Evidence UUIDs; asset UUID plus 'Full ID' although `asset_code` is on the wire | Cite B1-53 |
| B14-06 | cooling | Recovery curves 1.75x at 390 (chart plus ruled table, within the C2 cap); R05 verified; next step has no plan-test link and is missing a line | Ruling: accept under cap; D1 / D3 Low |
| B14-07 | cooling, health (unknown) | 'No selected cold assessment covers this window yet.' sits above populated 'Comparison limited' content | D3 Low candidate |
| B14-08 | cold-scenarios | The pending notice mentions 'the authored scenario' when 0 exist; 'Placeholder' literals remain on a built page | D3 Low; D4 under R25 / D2 |
| B14-09 | cold-work | The default window excludes today, so 0 Actions; the empty copy 'has been raised here yet' is false | D3 Low |
| B14-10 | all | Site main tabs drop from/to/known_at | D3 Low (shared tab seam) or fold into R88 |
| B14-11 | cold-work | Worst case within K2 caps (panel 457, page 1000/1152; all-open exempt) | Informational |
| B14-12 | cold-work | Real 403 and 503 render inside the panel | Informational |
| B14-13 | cold-health | R22 closed; R13/R14 present; subtitle | (a); D4 (extend R90) |
| B14-14 | link check | B7-03 and B7-01 still open, plus the incident/maintenance contradiction | Keep the D3s open; extend the B7-03 card |
| B14-15 | spec | W5-01 producers not committed; `cold-cooling` vs `cooling` | Correct the spec and register IDs |
| **B14-16** | cold-scenarios | Authored-scenario states not producible | Architect: commit a reviewed producer mode |
| B14-17 | health, work | Other >1.3x panels with measured reasons, within caps | Ruling: accept |

## Blockers

B14-16 (no committed authored cold-scenario producer). The port 8971-8977 deviation is recorded above. No DBs or processes remain.
