# Post-W6 audit, batch 13: W4 decisions/cases

IDs: `scenarios`, `alternatives`, `opportunity-finding`, `sitework-incidents`, `sitework-maintenance`. Branch `audit/batch-13` at main `d1d91a55` (product code identical to frozen `fddf5cad`), worktree `AssetOpsV1-review5`. Mock authority: `frontend/mockups/v69/index.html`, served by the same Vite origin and rendered at 1440x1000 and 390x900 CSS px.

All dispositions are **proposals** for the Architect. This batch adds no register rows.

Machine-readable record: `batch-13.json` (54 pairs). Side-by-side view: `index.html`. Difference source: `differences.json` (written by `tools/differences.py`).

## Run record

- **Producer (reviewed, unmodified).** `tools/w403_mini_decisions_walkthrough.py`, the W4-03 two-Site walkthrough (fixture `backend/tests/fixtures/w4/w403-mini-decisions.json`: KOBO-001 with W1 F02, MG-W402-001 from the W4-02 installer). It is the spec's producer for all five IDs: it seeds the MG Site work cases through W4-01 `WorkService`. Modes run in order:
  1. `prepare`
  2. `serve`
  3. `replay-positive`
  4. my capture `part-one`
  5. `capture --phase positive` (the producer's own capture; it seeds the reviewed stock of four more Incidents and two more Requests)
  6. my capture `part-stocked`
  7. `replay-late`
  8. `capture --phase late`
  9. my capture `part-late`
  10. `drop`

  `PYTHONPATH=backend;backend/tests;contracts;gateway;simulator;host`. Selected IDs: OPP-000001 `850a3228-33f7-4ab7-9dab-ac88cc3b9a9e` (current, historical, stale and late reads), OPP-000004 (missing-day branch), SCN-000002/SCN-000003, INC-000001 and WR-000002 (positive), INC-000003..6 and WR-000007/8 (stock), and the KOBO F02 Finding at its pinned revision.
- **Not run: `.agent/W4-01-evidence/seed.py`.** It hard-codes `ROOT = ...\AssetOpsV1-review`, which is another worktree, and the `w401h_test` DB. Running it unmodified would import code from outside this worktree. The W4-03 walkthrough covers the same two Site Work screens with reviewed stock.
- **Database.** The walkthrough requires a name ending in `_test`, so I used `assetops_audit_b13_test` (rule a). Its `prepare` resets an existing DB rather than creating one, so I created the empty DB first with `CREATE DATABASE`. The producer's `drop` mode removed it, together with `var/w403_b13`. Before preparing, `pg_database` showed batch 12's `assetops_audit_b12_test`, and batch 12 was serving the same walkthrough on 9761 (PID 18348). I waited until its server and DB were gone. I touched no other DB.
- **Ports (deviation).** The walkthrough hard-codes API 9761, and its own capture tool hard-codes CDP 9763. Both are outside 18301-18309/9523. Running the producer unmodified took precedence. I confirmed both ports were free (after batch 12 released 9761). Vite ran on 127.0.0.1:5183 `--strictPort` with `ASSETOPS_API_PORT=9761`. My capture used CDP 9523. I stopped serve (PID 9496) and Vite (PID 16216) by PID; Chrome was started and killed by the capture scripts.
- **Stale `var/sites/kobo-001.yaml`.** It did not matter. The walkthrough serves KOBO-001 from its private byte copy, digest-checked against `site_import`, and `/api/sites/KOBO-001` returned 200 (`kobo_reads`). I did not move the yaml.
- **Capture.** `tools/capture-b13.mjs` is `capture-b11.mjs` with these changes:
  - CDP port 9523 and its own profile prefix;
  - a read-only `mainText` probe for the plural and raw-text checks.

  It is capture-only: it navigates, waits, takes screenshots and measures the DOM. Targets come from `tools/mk_targets.py`, which reads the producer's own `positive.json`/`replay.json`. Logs are in `logs/`.
- **Producer evidence (not counted).** Both producer capture phases passed: 98 positive checks and 459 late checks. I copied their `evidence*.json`, `stock.json` and the two scoped-503 screenshots (`alternatives-read-503`, `incidents-refused-overlay`) into `producer-w403-capture/`. A capture-only wrapper may not inject a 503, so these states are producer evidence only. The producer itself lists `alternatives-stocked` and `alternatives-empty-current` as unproved, because F02's basis is dated 2026-10-29.
- **Cases (27 x 2 widths = 54 pairs).**
  - `sitework-incidents`:
    - one-incident;
    - empty-kobo and empty-past-window;
    - refused-reversed and refused-long (36 days);
    - no-window;
    - stocked and late-stocked (representative: stocked).
  - `sitework-maintenance`:
    - one-request;
    - empty-kobo;
    - refused-reversed;
    - stocked and late-stocked (representative: stocked).
  - `scenarios`:
    - positive-default and populated (representative: populated);
    - empty-window;
    - kobo-no-scenarios;
    - refused-reversed.
  - `alternatives`: db-time-409 (representative), no-revision and db-time-409-late. This is the only reachable state.
  - `opportunity-finding`:
    - supported-current (representative) and supported-historical;
    - late-settled-current;
    - stale-k-before-late;
    - missing-day-limited;
    - refused-bad-known-at.
  - Worst case: no producer mode offers five 160-character rows.

## Inventory reconciliation against `frontend/src/App.tsx`

| ID | Mounted route | Status |
| --- | --- | --- |
| `scenarios` | `SITE_FINANCIAL_SCENARIOS_ROUTE_PATH` `/sites/:siteId/financials/scenarios` -> `SiteFinancialsFrame view="scenarios"` | mounted (App.tsx:452) |
| `alternatives` | `SITE_FINDING_VIEW_ROUTE_PATH` `/sites/:siteId/findings/:findingId/:view` with `view=alternatives` (`FINDING_CHILD_VIEWS`) | mounted (App.tsx:459-465) |
| `opportunity-finding` | `SITE_OPPORTUNITY_ROUTE_PATH` `/sites/:siteId/opportunities/:opportunityId` -> `SiteOpportunityFrame` | mounted (App.tsx:456) |
| `sitework-incidents` | `SITE_WORK_INCIDENTS_ROUTE_PATH` -> `SiteWorkCasesFrame kind="incidents"` | mounted (App.tsx:471) |
| `sitework-maintenance` | `SITE_WORK_MAINTENANCE_ROUTE_PATH` -> `SiteWorkCasesFrame kind="maintenance"` | mounted (App.tsx:475) |

The spec route table (rows 67-68 and 73-75) matches. One note: the "W4 case producer, selected Site cases" for the Site Work IDs is in practice the W4-03 walkthrough's MG cases. The W4-01 seed is pinned to another worktree.

## Mandatory carried UI-pass checks

| Item | Result on batch-13 screens |
| --- | --- |
| `1 incidents` / `1 maintenance` | **Recurs.** The strip reads `Scoped to Mini-grid · 1 incidents` and `1 maintenance` (B13-01). The source is the shared `siteWorkCases.tsx:373`, so the cold and EV Work screens inherit it. |
| `.prose` 14 px vs 12 px | Recurs on opportunity-finding only (14 px vs 12 px). Work, Scenarios and Alternatives use 12 px. |
| Tall dark header at 390 | 295 px on opportunity refused-bad-known-at 390. Other 390 refusals are 146-214 px against the mock's 131. Cite B1-02/B2-04. |
| Raw `c1 · EV_CONNECTOR` | Not present. Raw server text with backticks appears on Work refusals (B13-04). |
| One generic window error | Work: distinct sentences for reversed vs over-31-day (no recurrence). Opportunity: the domain analogue recurs. A 422 `INVALID_KNOWN_AT` shows "Decisions are unavailable right now. Try again." (B13-03, Medium). Scenarios: reversed only (B13-09). |
| 390 Window control (R88/R112) | R88/R112 cover cold/EV Work only. Mini Site Work puts its date inputs inside the panel head; Scenarios has no control at all (B13-07). This needs an R88/R112 extension or a new row. |

## Existing D3 rows R22/R23/R24/R37/R38/R60

- None names these screens.
- **R23/R24 (site-local Work window) are resolved for cold and EV only.** The mini branch of the same component still prints UTC for a Site stored as Africa/Nairobi (B13-02, Medium). R23/R24's reasoning applies.
- R22, R37, R38 and R60 do not touch W4.

## Layout checks

- App page horizontal overflow is 0 on all 54 pairs. There are no console errors and no crashes.
- Panel count, titles and order equal the mock on every non-refusal pair. Opportunity refused-bad-known-at shows refusal copy only.
- Over 1.3x: only the stocked five-row Incidents panel, at 1.40x (443/316) at 1440. That is within the reviewed W4 u9 cap of 460 and needs a register cap ruling (B13-17). Everything else is 0.30-1.23x. The low ratios are refusal or 409 states.
- Scroll containers:
  - The Work tables scroll horizontally at 390 (720-760 px in 324 px) and stay readable.
  - The Site tab row overflows at 390 and hides "Overview" (B13-18, B4-04).
  - **The Scenarios table hides its second of two rows inside a capped inner scroll at both widths (B13-07).**
- Clipped text: Decision-context and narrative clamps on Site Work (B13-06).

## Differences (proposals)

| ID | Screens | Summary | Proposed disposition |
| --- | --- | --- | --- |
| B13-X1 | all | Cites B1-01, B1-04/B2-36, B2-02, B2-21/B3-04, B1-53, B1-07 (opportunity), B1-02 (one pair); B3-01 does not recur | cite existing IDs |
| **B13-01 (Medium)** | sitework-incidents/maintenance | "1 incidents" / "1 maintenance" plural; shared component | (c) D3 shared copy fix; cold/EV inherit |
| **B13-02 (Medium)** | sitework-incidents | Window in UTC although the MG timezone is stored; cold/EV use siteWindowText | (c) D3, R23/R24 analogue |
| **B13-03 (Medium)** | opportunity-finding (+ alternatives refusals) | 422 INVALID_KNOWN_AT rendered as "Decisions are unavailable right now. Try again."; contradicts W4-03 closure 4 reading 3 | (c) D3 |
| B13-04 | sitework-* refused | Raw backtick server message; "Count unknown · work source unavailable" and "(—)" counts on an input error | (c) D3 Low; shared with cold/EV |
| B13-05 | sitework-* | Per-row "UTC and IDs" disclosure; on Maintenance it sits in the Asset column | D2 row or D3 Low |
| B13-06 | sitework-incidents | Decision-context and narrative lines clamped with an ellipsis | D3 Low or D2 row |
| **B13-07 (Medium)** | scenarios | Two-row table cut by a placeholder-derived cap (row 2 hidden); no window control (URL only) | (c) D3 (re-rule the cap); extend R88/R112 or a D1 row |
| B13-08 | scenarios | Authored rows replace the placeholder; "Scenario creation unavailable" | D4/D2 row (R25/R27 pattern); D1 |
| B13-09 | scenarios refused | Server sentence only; other inputs unverified | cite B7-11 |
| B13-10 | alternatives | Only the DB-time 409 is reachable; populated geometry unaudited; "Reload" cannot succeed | informational; audit blocked |
| B13-11 | alternatives | "Finding code unavailable" crumb; money tab; subtitle; Open site as a link; no Site tab row (B4-04 not recurring, B4-05 resolved) | cite B3-02/B4-06; D1; D3 Low |
| B13-12 | alternatives, opportunity | Rail selects Sites; the mock selects Findings | D3 Low or extend R69 |
| B13-13 | opportunity-finding | Breadcrumb root is the disabled long sentence (spec-ruled, no row) | D1 row |
| B13-14 | opportunity-finding | Energy/tariff "Unavailable in this read" and scenario name unavailable, while the gross $2.50 and scenario tariff exist elsewhere | D1 row |
| B13-15 | opportunity-finding | Fixed subtitle claims an authored scenario when none is linked | D3 Low |
| B13-16 | sitework-* | Strip detail and footer copy differ (create flow unavailable) | extend R35 (D1) |
| B13-17 | sitework-incidents | Stocked panel 1.40x at 1440, within the W4 u9 cap of 460; no worst-case fixture | cap ruling / register row |
| B13-18 | sitework-*, scenarios | Site tab row at 390 auto-scrolls and hides Overview | cite B4-04 |
| B13-19 | all | Empty, refused, one-incident, stocked, historical, stale, limited and 409 states behave as specified | informational |
| B13-20 | hand-off | Cold/EV Work inherit B13-01/04/05, not B13-02; B4-19 does not recur; B5-01/B4-03 not applicable | informational |

## Blockers

None blocking. Limits:

- **Alternatives populated/empty** are unaudited, because F02's basis is future-dated. The producer itself lists them as unproved.
- **Scoped 503 states** exist only as producer evidence: a capture-only wrapper may not inject a 503.
- **No worst-case fixture** (five 160-character rows) is offered.
- **The W4-01 seed** is pinned to another worktree, so it was not run.
- **Deviations:** producer ports 9761/9763, and the DB created empty before `prepare`.
