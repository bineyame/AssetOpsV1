# DEMO-B review packet (combined-dataset captures, v70 comparison, walkthrough runbook)

Branch `task/DEMO-B-captures` (worktree `AssetOpsV1-demob`, from main `d2e8407e4`). Contract:
`.agent/build-sheet-DEMO-COMBINED.md` §6-§8, as amended by `.agent/build-sheet-DEMO-SPARSE.md` (§2, Addenda 1-4) and
`.agent/DEMO-A-packet.md` (Final round). No task file exists for DEMO-B under `tasks/`; the owner trigger is the
coordinator brief of 2026-11-01. USER_REVIEW: the owner walkthrough (sequence step 2) uses the runbook below.

## Outcome

- **B1** `tools/demo-combined-evidence.mjs` (`capture | mock-ids | compare`). It reads `<work>/story.json`, `kobo.json`
  and `days.json`, opens 14 screens at 1440 and 390 px in its own headless Chrome, waits for the reads to settle, writes
  full-page PNGs, measures the same blocks as `tools/measure-mock-panels.mjs` (plus overflow), and scans the visible
  text for codes, ids and developer words. `compare` pairs each capture with its v70 measurement.
- **B2** 28 product captures + 22 v70 mock captures, compared; 10 new register rows (R625-R634), 10 polish defects
  (P-01..P-10), and a client-copy list. No product code or data changed.
- **B3** the runbook below, timed on a real restart.

## Sheet mapping (COMBINED §6 → SPARSE calendar; build S = 2026-10-29, built 2026-10-31)

| COMBINED §6 screen | Captured as | URL (S = 2026-10-29) | v70 id |
|---|---|---|---|
| Portfolio S | `portfolio-week` (Addendum 2: the demo opens the week) | `/portfolio?from=10-23&to=10-30` | portfolio |
| Kobo Overview board S, default / all-open | `kobo-board-S`, `kobo-board-S-open` | `/sites/KOBO-001?date=2026-10-29` | mini |
| Kobo S+1 | `kobo-board-S1` | `/sites/KOBO-001?date=2026-10-30` | mini |
| ACT-048 verification with cost check (CO-4) | `kobo-verification` (ACT-000001); the cost check itself reads on the Kobo Cost row Earlier entry in `kobo-board-S` (R632) | `/sites/KOBO-001/actions/<id>/verification` | verification |
| GreenHarvest failure / normal event | `cold-board-failure` (S 16:00-17:05), `cold-board-normal` (S-7d 16:00-17:05) | `/sites/COLD-LAB-001?from&to` | cold |
| Depot board E | `ev-board-fault` (fault Tuesday S-2d 08:00-09:00, R619) | `/sites/EV-LAB-001/ev?from&to` | ev |
| Estate Findings with lenses | `findings-all`, `-cost`, `-risks`, `-opportunities` (week) | `/findings[/lens]?from&to` | findings, findings-cost, -risks, -opportunities |
| Maintenance preventive | `maintenance-preventive` (31 days S-28d..S+3d, R629) | `/maintenance/preventive?from&to` | maintenance-preventive |
| Work request overview | `wr-overview` (WR-000006 cold starter/control inspection) | `/maintenance/requests/<case>?site_id=COLD-LAB-001` | wr-overview |

Cold and EV boards use the event windows from `days.json` `start`/`end`, the windows the build's CO-7/CO-9 rows read: a
whole-day EV window reads every outcome Unknown ("No selected EV session assessment covers this window yet").

## Captures (all under `.agent/DEMO-B-captures/`)

`<key>-1440.png` and `<key>-390.png` for the 14 keys above; `captures.json` (URL, h1, page height, overflow, vocabulary
hits per capture), `product-measure.json`, `comparison.json`, `capture-run.log` (28 OK, exit 0, wall 270 s),
`compare-run.log`; mock side `mock/mock-<id>-{1440,390}.png` and `mock/mock-measure.json` (22, wall 56 s).
Every capture settled (no "Loading" sentence, text stable); no capture overflows horizontally at either width.

## Comparison summary (`compare-run.log`, panels mock/product, page height ratio at 1440)

portfolio 4/4 ×0.93 · mini 5/8 ×1.26 (extra = the R163 Site record disclosure's three panels) · verification 3/3 ×1.11 ·
cold failure 5/5 ×1.02, normal 5/5 ×0.64 (no incident that night, R616) · ev 5/5 ×0.99 · findings ×4 1/1 ×0.90-1.00 ·
preventive 1/1 ×1.04 · wr-overview 2/2 ×1.00. Cards match 4/4 where the mock has them. The panel structure matches
everywhere; the differences are content, triaged below.

**Already registered (cited, not repeated):** shell topbar/rail R114, R116, R117; mini R153 (UTC day control), R158
(hour timeline), R160 (Needs attention), R161 (money format), R162 (Next step), R163 (Site record), R388 (operating
context); portfolio R305, R502 (Placement), R620; findings R288, R291 (Not assessed priority/confidence), R575 (no
warnings on the week), R622; preventive R08, R10 (Not assessed / Draft); wr-overview R363, R365, R396; cold/EV
record-derived names R235.

**New register rows** (`.agent/mock-departure-register.md`, "DEMO-B additions"): R625 portfolio headlines without
numbers on the week; R626 Kobo day S "0.00 USD" over 200 avoidable minutes (open, cause unconfirmed); R627 Kobo Grow
Unknown / Assure No objective declared; R628 EV no tariff → unpriced; R629 work lists by recorded (build) time; R630 WR
repeat-visit notice absent (open); R631 two identical cold Finding titles; R632 verification values (verified trial)
and where the cost check reads; R633 mini freshness strip vs status bar; R634 Assure line without a modelled change.

## Polish-round defects (not fixed here)

- **P-01** `demo_combined.py links`/`serve` print board links `/sites/{code}/outcomes?...` and `/sites/KOBO-001/overview?date=`
  that are not routes ("Page not available"). Correct forms are in the runbook below.
- **P-02** Those links give cold/EV whole days; EV reads all Unknown on a day. They must carry the event window.
- **P-03** Portfolio table at 1440: the Confidence chip "Supported, coherent source" overlaps the Action cell
  ("No accepted Action") on all four rows (`portfolio-week-1440.png`).
- **P-04** Visible "MOCK DEVIATION" lines: wr-overview "D1 (R396)", "D2 (R363)", "D1 (R365)" at both widths; the Site
  tab row "D2 (R453)" under every Site Overview at 390 (in the text at 1440 too). The sheet requires none visible.
- **P-05** Raw ids on screen: full UUIDs in the Portfolio Finding cells; "Finding d374e29a"-style ids on estate
  Findings and WR; "REC <uuid>" on the EV timeline; all-open Kobo board: 251 UUIDs, `DEVELOPMENT_TENANT_OPERATOR_CONTEXT`,
  `LATEST_RECORDED_REVISION_OF_EACH_CANONICAL_FINDING`, raw ISO timestamps (`captures.json`).
- **P-06** Kobo day S: Needs attention with "0.00 USD exposure" and "0.00 to 0.00 USD" over 200 avoidable minutes (R626).
- **P-07** WR-000006 has no repeat-visit notice although the cold board shows the warning (R630).
- **P-08** EV fault window: Already in hand lists only PM-000013; the Action the build raised for the fault Finding
  (`ev.json` `fault_day.action`, code null) is not shown anywhere on the board. Diagnose.
- **P-09** Preventive reads "Overdue: Not assessed · No due evaluator" while the Kobo/cold/EV boards show plan-overdue
  warnings for the same plans: a client sees two answers.
- **P-10** Cold failure board: "What happened" says "No incident recorded" while INC-000005 is listed Open under Already
  in hand.

## Client-copy issues (seen in the captures; polish round)

- **Shell:** rail "Open Simulator Lab"; "Assets · Not available yet", "Settings · Not available yet"; UTC times on every page.
- **Names and codes:** "Cold replay lab", "EV charging lab" (mock GreenHarvest Cold Room, Depot Charging Hub);
  badges "Demonstration data · COLD-LAB-001"; zero-padded codes ACT-000001, WR-000006, INC-000005, PM-000013; asset
  codes "Connector c1", "generator-1", "compressor-1 · COMPRESSOR", "battery · BATTERY"; "Investigate connector Connector c1".
- **Kobo board:** "exposure in this hour" on a day view; "What happened in the selected hour" with "Hour not selected:
  this Overview reads one whole UTC day…"; "Day reading: Assessed. 1 operating period assessed; 13 measured roles
  covered" (S+1: "0 operating periods assessed"); "The source of these readings is open for current use"; "1036
  accepted readings on this day; the first 500 are listed"; "No rule yet says which gaps in the readings matter
  here"; lowercase lane labels "critical load delivered power"; "Bounded money consequence", "Current amount",
  "Cost range, money gate, source record and links"; "Open · version 2 · the Finding chosen for this day"; "1 Finding
  overlap this day"; Finding title "Generator support merits review: bounded candidate avoidable running"; the Cost
  Earlier line "Modelled change after the trial · not realised savings: no lower cost per kWh of feeder demand ·
  Supply cost per kWh before the trial: missed · after: met" (hard to read aloud).
- **Verification:** "Dig deeper: identifiers and typed values"; "Source Finding version"; "Finding version 2 is a new
  episode; it does not rewrite this trial"; "Technical result verified on test data · benefits: mini-grid operator".
- **Portfolio / Findings:** "Evidence cutoff 2026-11-01 02:09:11 UTC (latest at read time)" plus an empty
  "mm/dd/yyyy --:--:--" cutoff picker; "Opens current Site view"; "Basis not recorded", "Episode window not recorded",
  "No end is recorded for this episode"; "Supported, coherent source"; "Recommendation not accepted"; "Partly checked ·
  Value withheld"; "Not comparable for this selection"; "Policy trial awaiting outcome · 0" beside "Verified
  resolutions · 1"; "one global object model"; states "Supported / Unconfirmed / No longer supported / Merged"; "No
  supported lens"; card values "Coverage incomplete".
- **Cold / EV:** "Confidence: Bounded"; "Consequence basis: at least 19.5 °C·min; upper bound not established"; Next step
  "Automatic generator start failed in the accepted record"; "No accepted transfer to backup report for this chain";
  "Registered test reports; not physical charger observations"; "known at 27 Oct 09:00 UTC"; "Opens configuration at
  window end; evidence cutoff is not carried"; "Review recommendation · Not available yet".
- **Maintenance / WR:** "No due evaluator", "No accepted-evidence link", "Source unverified", "Nothing verified by this
  plan", "Listed by the time each plan was first recorded", "Completing a draft plan here is unavailable"; "No
  work-case outcome evaluator is available"; "As known at … UTC · Reload"; every request's narrative is "Witnessed
  failure requires inspection." (also on Kobo's routine generator inspections).

## Runbook (owner walkthrough; the same restart used here, timed 2026-11-01)

Kept build: `C:\Users\assef\Bineyame\AssetOpsV1-demo3`, work `var/demo3_full`, DB `assetops_demo3_full_test`, S = 2026-10-29.

1. **Prepare** (only to rebuild; it moves every date): from `AssetOpsV1-demo3`,
   `python tools/demo_combined.py --db assetops_demo3_full_test --work var/demo3_full prepare` - 797.6 s at `79dda4ea0`
   (DEMO-A Final round). Not rerun here.
2. **Serve** (PowerShell, from `AssetOpsV1-demo3`): set `$env:PYTHONPATH` to that tree's
   `backend;contracts;tools;simulator;gateway;host;field`, then
   `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe tools/demo_combined.py --db assetops_demo3_full_test --work var/demo3_full serve`.
   Measured: API answering on 8990 after **3.1 s**; first tick done **39 s**; first Performance comparison **41 s**; then
   one tick every 120 s. Wait for the first `performance:` line before showing anything (a stale build reads
   STALE_PROJECTION until then; DEMO-A caution 1).
3. **Frontend** (second PowerShell, from `frontend/` of a main checkout, here `AssetOpsV1-demob\frontend`):
   `$env:ASSETOPS_API_PORT="8990"; npm.cmd run dev -- --port 5490 --strictPort` - Vite ready in **1.6 s**. First Kobo
   Overview read through the proxy: 200 in **2.5 s**, `freshness.state` CURRENT.
4. **Links** (use these, not the `/outcomes` links `serve` prints, P-01):
   - Portfolio, week: `http://localhost:5490/portfolio?from=2026-10-23T00:00:00Z&to=2026-10-30T00:00:00Z`
   - Kobo day S / S+1: `http://localhost:5490/sites/KOBO-001?date=2026-10-29` / `?date=2026-10-30`
   - Kobo trial verification: `http://localhost:5490/sites/KOBO-001/actions/f2a48968-a662-4b19-92d6-d8dbb7bc05fb/verification`
   - GreenHarvest failure: `http://localhost:5490/sites/COLD-LAB-001?from=2026-10-29T16:00:00Z&to=2026-10-29T17:05:00Z`
     (normal night: `2026-10-22T16:00:00Z` to `2026-10-22T17:05:00Z`)
   - Depot fault: `http://localhost:5490/sites/EV-LAB-001/ev?from=2026-10-27T08:00:00Z&to=2026-10-27T09:00:00Z`
   - Findings: `http://localhost:5490/findings?from=2026-10-23T00:00:00Z&to=2026-10-30T00:00:00Z` (`/findings/cost|risks|opportunities`)
   - Maintenance (must reach the build day, R629): `http://localhost:5490/maintenance/preventive?from=2026-10-01T00:00:00Z&to=2026-11-01T00:00:00Z`;
     WR-000006 opens from the Corrective list on the same window.
   After a rebuild, quote the new dates from `python tools/demo_combined.py ... links` and apply the P-01 route forms.
5. **Captures** (optional, with 2-3 running): `node tools/demo-combined-evidence.mjs capture <demo3>\var\demo3_full <out>`
   (28 captures, 270-303 s), then `node tools/measure-mock-panels.mjs --mock frontend/mockups/v70 <out>/mock $(node tools/demo-combined-evidence.mjs mock-ids)`
   (56 s) and `node tools/demo-combined-evidence.mjs compare <out> <out>/mock/mock-measure.json`.
6. **Stop:** Ctrl+C in each window, or `taskkill /PID <pid> /T /F` on the serve and npm PIDs (the serve tree holds
   uvicorn). Check ports 8990 and 5490 are free.

## Checks run

- `node --check tools/demo-combined-evidence.mjs` at each commit; final full capture run on `5d6ff3cf9` (28/28 OK, exit 0);
  `3dc50c75b` adds only the find-step width checks (re-run on wr-overview, 2/2 OK).
- `tools\check-all.ps1 -Python C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe`: see "Guards".
- No backend/frontend suites: the slice adds one `.mjs` tool and `.agent` records; no product code, no Python.
- Processes started here (serve 16300/19900, Vite 24816/11972, headless Chrome per run) were stopped by PID; ports
  8990/5490 free at the end; keep-awake untouched.

## Guards

- First run at `56fdc1f3e`: 10/11; **Evidence width check (W1-UX-06) failed** on
  `demo-combined-evidence.mjs:182-183` (the work-request find step resized and navigated without `requireWidth`).
  Fixed in `3dc50c75b` (two `requireWidth` calls; behaviour otherwise unchanged); the find step re-run once
  (`DEMOB_ONLY=wr-overview`, 2/2 OK, same WR-000006 page).
- Rerun at `3dc50c75b`: **All 11 guards passed** (exit 0, 361 s).

## Known deviations

- The sheet's "Kobo Overview board" and the `links` board URLs do not exist as routes; the board lives on the Site
  Overview. Captures use the Overview routes (P-01).
- CO-4: the verification page carries no cost check (neither mock nor product); it is captured where it reads, the Kobo
  Cost row Earlier entry (R632, R590). R594's Assure modelled line does not show on this data (R634).
- The tool's vocabulary scan reads `innerText`, so it also counts text hidden by CSS at one width (R453 at 1440).
- `demo_combined.py` was not changed (Python; P-01/P-02 go to the polish round).

## Residual risk / review focus

- Triage judgement: whether R626 (0.00 USD) and R630/P-08 are data or product defects is unconfirmed; they must be
  diagnosed before the client demo.
- R633 may duplicate an older mini row not found by keyword search.
- The all-open Kobo capture clicks every `aria-expanded="false"` button and `<details>` in `<main>`; it is a stress
  view (pageH ×10.7), not a demo view.
