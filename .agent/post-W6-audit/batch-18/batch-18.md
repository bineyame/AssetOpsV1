# Post-W6 audit batch 18: W6 global lists

IDs: `incidents`, `maintenance`, `maintenance-preventive`, `oprecords`. Branch `audit/batch-18` at main `f99bca2e` (product code identical to frozen `fddf5cad`), worktree `AssetOpsV1-review6`. Mock authority: `frontend/mockups/v69/index.html`, served by the same Vite origin and rendered at 1440x1000 and 390x900 CSS px.

All dispositions are **proposals** for the Architect. This batch adds no register rows. Machine-readable record: `batch-18.json` (186 pairs). Side-by-side view: `index.html`. Difference source: `differences.json` (written by `tools/differences.py`). Digests: `logs/summary.txt` (one line per pair) and `logs/brief-all.txt`.

## Route reconciliation (`frontend/src/App.tsx`)

| ID | Mounted route | Status |
| --- | --- | --- |
| `incidents` | `INCIDENTS_PATH` `/incidents` -> `GlobalIncidentsFrame` | mounted |
| `maintenance` | `MAINTENANCE_PATH` `/maintenance` -> `GlobalMaintenanceFrame` | mounted |
| `maintenance-preventive` | `MAINTENANCE_PREVENTIVE_PATH` `/maintenance/preventive` -> `GlobalPreventiveFrame` | mounted |
| `oprecords` | `OPERATIONAL_RECORDS_PATH` `/operational-records` -> `OperationalRecordsFrame` | mounted |

The spec route table is correct for these IDs. The spec names "W6-01a/b/e fixtures"; the single producer is `tools/w601_seed.py` (fixtures `incidents`, `maintenance`, `preventive`, `operational`, `zero`, `historical`, `stress`, `linked`). It has no serve mode: the W6-01 evidence ran the plain product API over each seeded DB (`.agent/W6-01-evidence/B2/run_state.sh`), and this batch does the same.

## Producers, environment and capture

- **Mini (W6-01 producer, unmodified).** `python tools/w601_seed.py --db assetops_w601_b18<tag>_test --fixture <f> --clock <c>` for the 8 fixtures above, using the W6-01 clocks (2026-10-21 or 2026-10-20 at 12:00Z). The seed JSON is in `seed/`. Each DB was served by `uvicorn assetops_backend.main:app` with a per-start random `ASSETOPS_WORK_CURSOR_KEY_HEX` on 18801-18808 (`tools/start_apis.ps1`).
  - **503:** `DATABASE_URL` names `assetops_w601_b18absent_test`, which was never created (the W6-01 A2/B2/B3/E2 precedent).
  - **Empty scope:** the reviewed W6-01e TEST-ONLY composition `uvicorn api_empty_scope:app --app-dir .agent/W6-01-evidence/E2` over the operational DB. The global roots have no 403; EMPTY_SCOPE is their access-refusal state.
- **Cold (W502, unmodified).** `tools/w502_cold_work_walkthrough.py --work var/w502b_b18 --tag b18 prepare --modes positive,worstcase`. For the link landings it also ran `serve` (hard-coded ports 8971-8977, checked free first), then `drop`.
- **EV (W504, unmodified).** `tools/w504_ev_work_walkthrough.py --work var/w504a_b18 --tag b18 prepare / serve / attest / drop`, with the tool's own documented `W504_API_PORT_BASE=18800` (ports 18801-18807). Positive, zero and worstcase were ready; unknown, pending and stale are unavailable (the producer's own verdict).
  - The global lists were read through the plain product API on 18808/18809, because the W504 serve processes return 503 on every global root (B18-18).
- **DBs.** Before preparing I checked `pg_database`. Batch 17's `w504a_*_b17_test` DBs were present, and nothing `b18`. I created only `assetops_w601_b18{inc,maint,prev,op,zero,hist,stress,linked}_test`, `w502b_{positive,worstcase}_b18_test` and `w504a_{positive,zero,worstcase,unknown}_b18_test`, all under the `*_test` authorization, and dropped all of them at the end.
- **Servers.** Vite 127.0.0.1:5188 `--strictPort`, restarted per phase with `ASSETOPS_API_PORT` (`tools/driver.ps1`), and headless Chrome on CDP 9528. Every PID I started was stopped by PID. One warm-up navigation ran outside the batch folder before the first phase (the B15-13 precedent).
- **Capture.** `tools/capture-b18.mjs` is batch 15's wrapper with CDP 9528 and an added `b18` DOM block: status line, Showing/pager, Site and row links, alerts, plural, asset labels and enums. It only navigates, waits, screenshots and measures. `openAll` sets `details.open`, which is viewer-only.
  - Page-two URLs use a cursor from a read-only GET of the same API, with the frontend's own query.
  - Targets: `tools/mk_targets.py`. Claims passed in every phase (e.g. inc 96/96, op 180/180, cold 84/84, evwc 84/84, links 72/72, 48/48 and 72/72).
- **Environment fix (capture-only).** The ignored `var/sites/kobo-001.yaml` in this worktree is stale against the W6 import (`/api/sites` 503). It was moved aside for the mini link-landing captures only and then restored, as batch 10 did.

## Cases and pairs (186)

| Screen | Cases (each at 1440 and 390) |
| --- | --- |
| incidents (29) | positive, all-open, page-two, no-window, 4 refusals (reversed, 32-day span, one bound, bad known_at), unavailable-503, empty-scope, zero, historical + historical-current, one-row, linked, worstcase(+all-open), cold, cold-all-open, cold-default-window, coldwc(+all-open, default-window), ev, ev-all-open, ev-default-window, evwc(+all-open, default-window) |
| maintenance (23) | positive, all-open, page-two, no-window, 4 refusals, 503, empty-scope, zero, linked(+all-open), worstcase(+all-open), cold(+all-open), coldwc(+all-open), ev(+all-open), evwc(+all-open) |
| maintenance-preventive (18) | positive, all-open, no-window, 4 refusals, 503, empty-scope, zero, historical root + current, worstcase(+all-open), cold, coldwc, ev, evwc |
| oprecords (23) | positive, all-open, page-two, kind OPERATOR_LOG / MANUAL_READING / SHIFT_NOTE / SITE_VISIT (filtered zero), historical, invalid-kind, no-window, 4 refusals, 503, empty-scope, zero, worstcase(+all-open), cold, coldwc, ev, evwc |

That is 8 representative pairs plus 178 further states. There are also 16 link-landing captures (`part-linkcold`, `part-linkev`, `part-linkmini`, at both widths), which are not counted.

**Not producible:**
- A single list holding mini, cold and EV rows: no reviewed producer seeds all three into one DB.
- Preventive plans or operational records at cold or EV Sites: W502 and W504 write none.
- Five 160-character rows on preventive or oprecords: W6 `stress` writes one long plan and one long record. The five-160-char case is covered on incidents and maintenance by the cold and EV worstcase producers.
- Pending or stale global states: the global roots expose CURRENT, HISTORICAL and EMPTY_SCOPE only.

## Structural verdict

Panel count, order and titles match the mock on **all 186 pairs**:
- incidents: 'Incident cases', 'Case boundaries'
- maintenance: 'Corrective work requests'
- preventive: 'Preventive plan'
- oprecords: 'Operational records', 'Record a manual reading', 'How records are used'

Refusals keep their panels with the state sentence above them. Columns match the mock exactly on every table (7 / 6 / 7 / 8). There are no console errors and no page horizontal overflow on any pair.

Tables scroll horizontally at 390, as intended. At 1440, oprecords also scrolls horizontally (B18-07) and maintenance scrolls vertically inside a capped panel (B18-06). Clipping is only the intended two-line clamp plus 'Full title text' on long rows. Panels over 1.3x have measured reasons within the W6-01 caps (B18-16).

## Mandatory carried checks

| Item | Result |
| --- | --- |
| '1 incidents' plural | Not on global incidents (card note 'Open or in progress in this window'). **'1 requests in progress or open'** on maintenance (EV positive, mini stress): B18-01, owner B13-01/B15-02. The Site tabs reached from the global INC links still read '1 incidents'. |
| Raw `c1 · EV_CONNECTOR` | **Confirmed** on maintenance EV rows (1 and 5 rows). Cold rows show 'generator-1 · GENERATOR', against R89's 'backup generator'. B18-02. |
| domainActionClient window error | Not used here. globalWorkClient gives one plain sentence, 'Choose a valid date range of at most 31 days.', for reversed, span and missing bound; 'Choose a valid cutoff time.' for a bad known_at. No raw server text, and no false 'work source unavailable': B13-04/B15-03 do not recur. The refusal block has no live-region role. B18-13. |
| R88/R112 Window control | Neither applies. These are estate pages with the B2-02 page-local From/To/Show records/Reload control (about 165 px stacked at 390), as on the batch-10 estate lists. R18 (URL-only cutoff) verified. |
| Prose size | 14 px against the mock's 12 px on incidents 'Case boundaries' and oprecords 'How records are used' (B1-07). Table cells match (11 px). |
| Tall 390 header | **Confirmed** on short pages at 390: refusals, 503 and empty scope show a 103-174 px dark block, against 92 px populated (B1-02). |
| D3 R22/R23/R24/R37/R38/R60 | None touch these screens. R23/R24 resolved Site-local time on the Site tabs only. The global Start/When columns stay UTC (B18-X1, B2-21). R38's principle (labelled reference until the exact target is proved) is what B18-03 asks for. |
| B13-01/B15-02, B13-02, B13-04/B15-03, B15-06, B14-09, B10-04, B11-01 | B13-01/B15-02: '1 requests' (B18-01). B13-02: UTC is estate-wide here (B2-21, not B13-02's mini-only defect). B13-04/B15-03: do not recur. B15-06: recurs, requests windowed by created_at (B18-12). B14-09: recurs, the default window excludes today (B18-12). B10-04: does not recur, since cold and EV rows ARE linked; but cold Finding links contradict R66 (B18-03). B11-01: **recurs**, the EV Site link opens the generic page (B18-04). |

## Differences (proposals)

| ID | Screens | What | Proposed disposition |
| --- | --- | --- | --- |
| B18-X1 | all | Cross-cutting rows: B1-01, B1-04, B2-02, B1-07, B1-02 (390 short pages), B1-53 ('service:w401-fixture', id8 labels), B2-21/B3-04 | Cite |
| B18-01 | maintenance | '1 requests in progress or open' | D3 Low, shared plural owner (B13-01/B15-02) |
| B18-02 | maintenance | Raw 'c1 · EV_CONNECTOR' and 'generator-1 · GENERATOR' (R89 says 'backup generator') | D3 Low/Medium |
| **B18-03** | incidents, maintenance | Cold Finding links to /findings/{id}?revision_id, which the cold frame ignores; contradicts R66 (Site tab plain label) | D3 Medium |
| **B18-04** | all (EV rows) | EV Site link opens the generic 'Awaiting evidence migration' page, not /ev | D3 Medium, B11-01 recurrence |
| B18-05 | incidents, maintenance, oprecords | Page two from a URL says 'Showing 1–1 of 6' / '1–2 of 7' | D3 Low |
| B18-06 | maintenance | Panel capped at 609 px with an inner vertical scroll at 1440; rows 4-5 hidden | Architect remeasure; D3 Low if kept |
| B18-07 | oprecords | Table needs a horizontal scroll at 1440 (1150/1105) | D3 Low |
| B18-08 | incidents | No breadcrumb (siblings have one; the mock shows 'Incidents') | D3 Low, B1-01 family |
| B18-09 | incidents, maintenance | 'Not assessed' cards, Severity 'Not recorded', Verification/Warranty columns: ruled in the build spec, but unregistered and unlabelled | (b) D1 rows + MOCK DEVIATION label |
| B18-10 | incidents | WR codes plain though the request route is mounted; INC code goes to the Site tab | WR: D3 Low or D1; INC: extend R73/R85 (D1) |
| B18-11 | incidents | INC link pins known_at on a current read, so the landing shows a historical notice | D3 Low |
| B18-12 | all | Default window excludes today (EV case invisible); requests windowed by created_at, unstated | D3 Low, cite B14-09/B15-06 |
| B18-13 | all | One plain window sentence for three input errors; no live-region role | Copy: accept; role: D3 Low |
| B18-14 | oprecords | Inert form shows mock facts (GreenHarvest Site, '6 Oct 2026 · 16:00 EAT') | (b) D4, or extend R12 |
| B18-15 | all | R07-R12, R17, R18, R28-R31, R32/R33 resolved, R39 verified | (a) verified |
| B18-16 | all | >1.3x panels explained by rows and disclosures, within W6-01 caps | Informational; accept except B18-06 |
| B18-17 | all | Link landing per domain: mini all correct; cold correct except Findings; EV correct except Site | Informational |
| B18-18 | env | Global roots 503 without ASSETOPS_WORK_CURSOR_KEY_HEX even on page one; W504 serve unset; stale var/sites | Architect; informational |

## Blockers

None for this batch's scope. Coverage gaps (not producible) are listed above. Port deviation: W502 `serve` hard-codes 8971-8977 (checked free; used only for the cold link landings). All servers were stopped by PID, and all `b18` DBs were dropped (W502/W504 by their own `drop`, the W6 DBs by `DROP DATABASE ... WITH (FORCE)`).
