# Post-W6 audit batch 19: W6 work request

IDs: `wr-overview`, `wr-record`, `wr-history`.

- Branch `audit/batch-19` at main `731126a9`; product code is identical to the frozen `fddf5cad`. Worktree `AssetOpsV1-review5`.
- Mock authority: `frontend/mockups/v69/index.html`, served by the same Vite origin, rendered at 1440x1000 and 390x900 CSS px.
- All dispositions are **proposals** for the Architect. This batch adds no register rows.
- Files: `batch-19.json` (194 pairs plus 10 link-check captures that are not counted), `index.html` (app beside mock), `differences.json` (written by `tools/differences.py`).

## Route reconciliation (`frontend/src/App.tsx`)

| ID | Mounted route | Status |
| --- | --- | --- |
| `wr-overview` | `WORK_REQUEST_ROUTE_PATH` `/maintenance/requests/:caseId?site_id=` (App.tsx:508, `WorkRequestOverviewFrame`) | mounted |
| `wr-record` | `WORK_REQUEST_RECORD_ROUTE_PATH` `.../record` (App.tsx:510) | mounted |
| `wr-history` | `WORK_REQUEST_HISTORY_ROUTE_PATH` `.../history` (App.tsx, `WorkRequestHistoryFrame`) | mounted |

The spec route table is correct. There is no Verification route: its tab is `Verification · Not available yet` (B19-03). Any other section address falls to the unshelled app catch-all (B19-12).

## Producers, environment and capture

All producers ran unmodified. Before preparing, I checked `pg_database`: batch 18's `assetops_w601_b18*` DBs were present, and my names never overlapped with them.

**W6 fixtures.** `tools/w601_seed.py --db assetops_w601_b19{detail,hist,linked,stress,maint}_test --fixture {detail,detail-history,detail-linked,stress,maintenance} --clock 2026-10-20T12:00:00Z`.
- These are the C2-C4 evidence fixtures. Seed outputs are in `seed/`. The DBs were dropped after capture.
- Served by `uvicorn assetops_backend.main:app` on 127.0.0.1:18901 (`tools/run_phase.ps1`).
- 403 and 503 came from the reviewed TEST-ONLY compositions `.agent/W6-01-evidence/C2/api_403.py` and `C4/api_503.py`.

**EV.** `W504_API_PORT_BASE=18900 tools/w504_ev_work_walkthrough.py --work var/w504a_b19 --tag b19`, run as prepare, serve, attest, then drop.
- APIs on 18901-18907. Modes: positive, zero and worstcase are ready; unknown, pending and stale are unavailable.

**Cold.** `tools/w502_cold_work_walkthrough.py --work var/w502b_b19 --tag b19`, run as prepare, serve, attest (ATTEST OK), then drop.
- Its API ports 8971-8977 are hard-coded. I confirmed they were free first. This is the same port deviation as batches 14 and 15.

**Finding the request IDs.** W5 WR case IDs came from a read-only `SELECT public_code,id FROM work_case WHERE kind='MAINTENANCE_REQUEST'` on the producer DB (`seed/ev-*.txt`, `seed/cold-*.txt`). Neither walkthrough manifest names its WR UUIDs.

**Servers.**
- Vite ran on 127.0.0.1:5189 `--strictPort`. It ran once against 18901 for the W6 fixtures, then was restarted per W5 mode (`tools/run_vite_phase.ps1`).
- Headless Chrome used CDP 9529.
- Every PID I started was stopped by PID. No DB or listener remains.

**Capture.** `tools/capture-b19.mjs` is batch 17's capture-only wrapper.
- One option is added: `pageNext` clicks History's client-only pager, which issues no request and adds no URL state. It is used for page 2.
- Claims:
  - detail 300/300, hist 72/72, linked 36/36, stress 72/72, maint 156/156, forbidden 36/36, unavailable 36/36.
  - ev-positive 72/72, ev-worstcase 96/96 (rerun after a transient render miss; the first run is kept in `logs/`), ev-forbidden 36/36, ev-unavailable 36/36.
  - cold-positive 72/72, cold-worstcase 108/108, cold-forbidden 36/36.
  - links 52/60: the 8 failures are deliberate app-only pages compared against an unrelated mock.

## Cases and pairs (194)

- **Representative pairs:** `positive-wr1-in-progress` for each ID at 1440 and 390 (WR-000001: IN_PROGRESS after COMPLETE+REOPEN, 2 revisions, record, REC link).
- **Lifecycle states:**
  - open (maint WR-000001)
  - in progress by assignment (maint WR-000005, KOBO-002)
  - completed (maint WR-000006; cold WR-000002)
  - cancelled from open (maint WR-000004; detail WR-000002)
  - historical COMPLETED at `known_at=11:59:04Z`
  - historical revision 2 against current revision 3 (detail-history)
  - verification window: **not producible** (B19-10)
- **Domains:** mini (KOBO-001/002), cold (COLD-LAB-001, linked, Finding and Action), EV (EV-LAB-001, connector asset, Action-linked).
- **Worst case:** mini stress (200-char unbroken title, 128-char owner, 4000-char narrative/activity, 500-char correction), cold and EV 160-code-point requests. Each has an all-disclosures-open variant.
- **History paging:** page 1 (5 of 6 rows) and page 2 (row 6 plus the R41 gaps), closed and all-open.
- **Refusals and no-fetch:** 404, wrong Site, other tenant, cutoff before creation, malformed UUID, no `site_id`, bad `known_at`, 403 (test-only), 503 (test-only outage, and the stopped EV API).
- **W5 'forbidden' principals:** EV and cold. The page loads (B19-15).
- **Link checks (not counted):** four unknown sub-tab addresses, and the global Maintenance row link.

## Structural verdict

- **Panel count, order and titles match the mock on every loaded pair:**
  - Overview: Work done | Lifecycle.
  - Record: Maintenance record · activity, with the four mock columns and six item labels.
  - History: History, Time/Event/By.
- **Header, strip and tabs:** the strip cells, tab order, breadcrumb form and the header 'Open site' all follow the mock.
- **Typography and colour:** h1, h2, td, th, body and prose sizes, the family and the panel tokens equal the mock exactly.
- **Overflow:** no page horizontal overflow on any pair. At 390, tables scroll inside their panels.
- **Defects:** one recurring console warning on wr-record (B19-08), and the refusal-shell defects (B19-07).
- **Heights:** closed states are within the C2-C4 caps. Panels above 1.3x carry measured reasons (B19-11).

## Mandatory carried checks

| Item | Result |
| --- | --- |
| '1 incidents' plural (B13-01) | No counts on these screens. The global Maintenance card reads '1 requests in progress or open' (B19-14, batch 18). |
| Raw `c1 · EV_CONNECTOR` | **Confirmed** in the EV Overview Asset row. Cold shows 'generator-1 · GENERATOR' (B19-06). |
| domainActionClient window error | Not applicable: the WR pages use globalWorkClient, with no window. Distinct inputs get distinct sentences (B19-16). |
| R88/R112 Window control | Not present by design. A date bar sits there instead (B19-02). |
| Prose size | 12 px matches. The only 14 px sentence is the record empty state (B19-X1). |
| Tall 390 header | Refusals: 234-296 px. Short empty record pages: 126 px (B1-02). |
| D3 R22/R23/R24/R37/R38/R60 | None touches these screens. The R24 Site-local precedent supports B2-21 here (KOBO and COLD are Africa/Addis_Ababa; the app shows UTC). |
| B4-03/B4-04/B4-05/B5-01 chrome | Do not recur: code-rooted breadcrumb, no Site tab row, Open site present (B19-01). |
| B4-19 event fall-through | Does not recur. Unknown kinds read 'Event X · meaning not established', which is honest but a raw code (B19-10). |
| B13-04/B15-03/B17-06 refusal copy and false Retry | Raw text does not recur. The false Reload on 403/404 and the empty shell panels do (B19-07). |
| B17-05 short-ID labels | Recur: 'Finding a1e1219d', 'Action 98b2dfc6', and a full record UUID in History (B19-05). |
| B17-08 unknown sub-tab addresses | No silent mis-render. They land on an unshelled catch-all instead (B19-12). |

## Differences (proposals)

| ID | Screens | What | Proposed disposition |
| --- | --- | --- | --- |
| B19-X1 | all | B1-01, B1-04, B1-07 (record empty sentence only), B1-02 (390 refusals), B2-21 (UTC on EAT Sites), B1-53 | Cite |
| B19-01 | all | Panels, strip, tabs, breadcrumb, Open site and typography match; no B4/B5 chrome analogue | (a) informational |
| B19-02 | all | Added 'As known at … UTC · Reload' date-bar row (spec P-C2-4, unregistered) | (b) candidate D2 |
| B19-03 | all | 'Verification · Not available yet' tab (unregistered); at 390 it pushes History off-screen (411/358 px) | (b) D1 row + (c) D3 Low for the 390 clipping |
| B19-04 | overview, record | Honest gaps (Not set / Not recorded / Not established, Latest activity line, Record n group row, lifecycle note) spec-ruled but unregistered; R34 verified resolved | (b) candidate D1/D4 rows |
| B19-05 | all | UUID-prefix Finding/Action labels; full maintenance-record UUID in History; R39/R42 verified | Cite B17-05/B1-53, D3 Low |
| B19-06 | overview | 'c1 · EV_CONNECTOR' and 'generator-1 · GENERATOR' raw asset labels | Cite B16-14/B17-02, D3 Low |
| B19-07 | all (refusals) | Empty Work done/Lifecycle shells with a lifecycle claim; Reload on 403/404; inert button-styled Open site; no-site sentence | (c) D3 Low; cite B17-06/B15-03 |
| B19-08 | record | Console validateDOMNesting `<div>` in `<p>` (WorkRequestRecord.tsx:116-121) | (c) D3 Low defect |
| B19-09 | history | R19/R39/R41/R42 verified; unregistered client pager | (a) + (b) candidate D2 |
| B19-10 | all | Open, in-progress, completed and cancelled all captured; VERIFICATION_WINDOW not producible; raw fall-through latent | Architect item stays open; D3 Low latent |
| B19-11 | all | Within the C2-C4 caps; >1.3x panels have measured reasons; all-open exempt | Accept; Architect to confirm caps once |
| B19-12 | link check | Unknown request sections hit an unshelled 'This address is not served' page | Cite B17-08; D3 Low |
| B19-13 | all (historical) | Historical date bar shows minutes only (cutoff 12:00:01 reads 12:00) | (c) D3 Low |
| B19-14 | link check | Global list opens the exact request (R32 resolved); '1 requests' plural | Note for batch 18; cite B13-01 |
| B19-15 | all | W5 'forbidden' principal still reads the request via the global route (development_access) | Architect/security note |
| B19-16 | all | Mandatory checks summary; 390 full-height screenshot header artifact | Informational |
| B19-17 | all | Breadcrumb styled as blue '/' links against the mock's grey '›' crumbs | D3 Low shared, or cite batch 18 |
| B19-18 | all | Producer/capture notes, pager click, EV rerun | Informational |

## Blockers

- **VERIFICATION_WINDOW cannot be captured.** No W4 command enters it, so the carried Architect item stays open. The CANCELLED half is now captured for the WR screens.
- **Neither W5 walkthrough yields a WR 403.** Their forbidden principal is not consulted by the global route (B19-15). The only WR 403 comes from the reviewed W6 test-only composition.
