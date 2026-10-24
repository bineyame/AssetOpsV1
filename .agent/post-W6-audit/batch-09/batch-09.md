# Post-W6 audit, batch 09: W2 EV Site

IDs: `ev`, `ev-evidence`, `ev-evidence-analysis`, `ev-financials`, `ev-assumptions`. Branch `audit/batch-09` at main `6ce25119` (product code identical to frozen `fddf5cad`), worktree `AssetOpsV1-review6`. Mock authority: `frontend/mockups/v69/index.html`, served by the same Vite origin and rendered at 1440x1000 and 390x900 CSS px.

All dispositions are **proposals** for the Architect. This batch adds no register rows.

Machine-readable record: `batch-09.json` (50 pairs, plus 4 uncounted cross-check captures). Side-by-side view: `index.html`. Difference source: `differences.json` (written by `tools/differences.py`).

## Run record

- **Producer (reviewed, unmodified).** `.agent/W2-F-evidence/seed.py`, the W2-F unit-5 capture seed. Its EV path runs the W2-05b EV replay, then the EV worker, then an authored tariff through the store path, then the EV consequence worker. It uses ordinary replay paths only. I ran it twice: `ev interrupted` (site `00000502-...0002`) and `ev complete` (site `00000501-...0002`). `PYTHONPATH` was set to this worktree's `backend;gateway;simulator;contracts;host`, as in batch 7.
- **Database.** `assetops_audit_b09_test` in `assetopsv1-postgres-1`, under rule (a). I checked `pg_database` first: only batch 8's `assetops_audit_b08_test` was present, and I did not touch it. I created my DB before seeding, the seed reset it between phases, and I dropped it `WITH (FORCE)` after capture. No producer `_audit` DB was needed.
- **Servers.** API: `host/` `uvicorn lab_app:app` on 127.0.0.1:18901 (`DATABASE_URL` = the audit DB). PID 23396 served the interrupted phase and PID 11604 the complete phase. Vite ran with `--port 5189 --strictPort` and `ASSETOPS_API_PORT=18901` (PID 25660). Chrome used CDP 9529 and was started and killed by the capture script. All servers were stopped by PID.
- **Capture.** `tools/capture-b9.mjs` is `capture-b7.mjs` with only the CDP port and profile prefix changed. It is capture-only: it navigates, waits, takes screenshots and measures the DOM. Targets are written by `tools/mk_targets.py` and use the W2-F `capture.mjs` windows (`Q`, `QBAD`). Claims: interrupted 240/240, complete 60/60, findings cross-check 24/24. Logs are in `logs/`.
- **Cases.** Interrupted producer, for all five IDs: stocked (W2-F `Q`: 2026-10-06 08:00Z to 09:05Z, `known_at` 09:00Z), no-selection (the same hours on 10-05), refused (from > to) and no-window (bare route). Complete producer: the `Q` window, for all five IDs. That gives 25 cases x 2 widths = **50 pairs**: 10 representative pairs plus 40 further states.

## Inventory reconciliation against `frontend/src/App.tsx`

| ID | Mounted route | Status |
| --- | --- | --- |
| `ev` | `SITE_EV_ROUTE_PATH` `/sites/:siteId/ev` | mounted (App.tsx:390) |
| `ev-evidence` | `SITE_EV_EVIDENCE_ROUTE_PATH` `/ev/evidence` | mounted |
| `ev-evidence-analysis` | `SITE_EV_ANALYSIS_ROUTE_PATH` `/ev/evidence/analysis` | mounted |
| `ev-financials` | `SITE_EV_FINANCIALS_ROUTE_PATH` `/ev/financials` | mounted |
| `ev-assumptions` | `SITE_EV_ASSUMPTIONS_ROUTE_PATH` `/ev/financial-assumptions` | mounted |

The spec route table (rows 54-58) matches. No route-table error was found for this batch.

## Mandatory carried UI-pass checks

| Item | Result on batch-09 screens |
| --- | --- |
| `.prose` / panel sentences 14 px vs mock 12 px | Seen on the ev Overview (timeline sentence, money, Next step, SLD note), the Analysis "How a claim limit is set" panel and the Financials "Not included" panel. Cite B1-07/B2-03. |
| Tall dark header at 390 on short pages | Appears on 9 pairs (B9-X1): ev-evidence refused, ev-evidence-analysis no-selection and refused, ev-financials refused, and all five ev-assumptions cases (126-259 px). Cite B1-02/B2-04. |
| `1 incidents` plural | Not applicable. |
| Raw `c1 · EV_CONNECTOR` | Does **not** recur. Analysis reads "Connector c1 · connector status", and the bare `c1` code is left as a Data sources sub-label (B1-53). |
| One generic window error | The refused EV reads repeat "Choose a valid UTC start and end, up to 31 days." in every panel, for a window that is reversed rather than too long (B7-11, B9-05). |
| 390 Window control (R88/R112) | There is no window control at all; the window is set by URL only (B9-01, cites B7-02). R112 covers ev-work only. |

## Existing D3 rows R22/R23/R24/R37/R38/R60

- **R24** (EV site-local time): the stored EV Site timezone is `Etc/UTC`, so the UTC window lines are site-local here. However, the Analysis `Measured (EAT)` column still converts with a fixed UTC+3 (`EvSiteViews.tsx:1092`, `eatTime`), against the stored zone. This is the R24 pattern not applied on this screen (B9-X1, proposed D3 Low).
- **R38** precedent: the EV Analysis shows `REC {UUID} · No analysis link` with no unproved anchor, which is consistent with R38.
- **R40** (Availability/Energy destinations built): these routes are not promoted on the EV Site screens (B9-02, B9-06, B9-08).
- R22, R23, R37 and R60 do not touch these screens.

## Earlier W2 structural findings (W2-F), rechecked at this SHA

M5, M8, M9, M10, M11 and M12 are all still closed on these screens (details in B9-11). No W2-F finding has reopened. M3 was scoped to cold, and its EV analogue is open as B9-05.

## Batch 7 findings rechecked on EV

| B7 ID | On EV | Where |
| --- | --- | --- |
| B7-01 | **recurs** on the EV Site Findings list (cross-check only; `ev-findings` is not in this batch) | B9-10 |
| B7-02 | recurs | B9-01 |
| B7-03 | recurs: Availability is hard-coded "Not assessed" although the page is linked and built; Charger condition is hard-coded and unlinked although Health is built | B9-02 |
| B7-04 | does not recur for event wording; a new padded-slot defect appears instead | B9-03 |
| B7-07 | recurs: Portfolio evidence link, generic or unbuilt-labelled next steps, Contact "Unknown" | B9-06 |
| B7-08 | recurs: 3-line UUID record cells and 1.50x height; the date defect is latent | B9-07 |
| B7-11 | recurs, with different sentence text | B9-05 |

## Layout checks

- App page horizontal overflow is 0 on all 50 pairs. There is no clipped text, no console error and no crash.
- Panel count, titles and order equal the mock on all 50 pairs, including the refused and no-selection states.
- At 390 the Site tab row scrolls horizontally (521 px in 358 px). Evidence, Analysis, Financials and Assumptions tables scroll inside their panels (640/900/900/600 px in 318 px) and stay readable.
- Panels over 1.3x the mock:

| Screen | Panel | Ratio | Where |
| --- | --- | --- | --- |
| ev-evidence-analysis | Accepted records behind the conclusions | 1.50 | 1440 interrupted, no-window, complete |
| ev | Charging activity and site power | 1.30 (355/273, at the threshold) | 390 no-selection (chart legend gap lines) |

Each one's measured reason is in its difference entry, and each needs a reviewed ruling.

## Differences (proposals)

| ID | Screens | Summary | Proposed disposition |
| --- | --- | --- | --- |
| B9-X1 | all | Cross-cutting citations: B1-01, B1-04, B1-07, B1-02, B2-21/B3-04 (plus fixed-EAT Measured column on a UTC Site), B1-53, B3-15 | cite existing IDs; EAT column D3 Low (R24 precedent) |
| B9-01 | all five | No window control; URL only (B7-02) | extend R112/R88 (D1) or the topbar fix |
| B9-02 | ev | Card label-as-link; Availability hard-coded "Not assessed" while linked to the built page; Charger condition hard-coded although Health is built (B7-03) | (c) D3 (R40 expiry not applied); label-link D3 Low |
| B9-03 | ev | Timeline padded to 7 slots with "No accepted event" placeholders; B7-04 wording does not recur | D3 Low |
| B9-04 | ev | Recommendation honest-unavailable; no F-code; SLD link placement; chart form; strip narrative; repeated money headline | R65 (D1); D3 Low; D1/D2 |
| **B9-05 (Medium)** | ev, evidence, analysis, financials (+assumptions) refused | Refused states drop the window line, strip and tiles with no banner (EV analogue of the cold M3 fix); one generic sentence | (c) D3; copy cites B7-11; Assumptions refusal cites B7-10 |
| B9-06 | ev-evidence | Portfolio evidence "Not available yet"; "Review financials" vs "Review energy"; "Work · Not available yet" although built; Contact Unknown; padded next-evidence rows; complete-case Cause "Limited" with nothing interrupted (B7-07) | D3 / D1+D2 / D3 Low |
| B9-07 | ev-evidence-analysis | 3-line UUID record cells, window-start sample rows, 1.50x at 1440 (B7-08) | height ruling; R38 + B1-53 |
| B9-08 | ev-financials | Close match; Sessions/Finding vs Energy/F-130; chip colour | R65 (D1); D3 Low; D2 |
| B9-09 | ev-assumptions | Close match; window line; missing "Not connected" chip (B7-10) | D2/D3 Low |
| **B9-10 (High, cites B7-01)** | ev-findings (cross-check) | The EV Site Findings list shows the mini-grid index with a false "not released" reason while the EV findings API returns 1 current Finding | (c) D3, same fix slice as B7-01 |
| B9-11 | all | W2-F re-check: M5/M8/M9/M10/M11/M12 closed | informational |

## Blockers

None. Pending and historical states cannot be produced by this producer (W2-F covered them only in jsdom), so they were not captured.
