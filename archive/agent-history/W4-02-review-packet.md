# W4-02 review packet (mini-grid depth: renewable, service, fuel, backup)

Contract `.agent/W4-02-build-spec.md` (closures 1-5, Run 1-11 rulings q1-q11). Handoff `.agent/W4-02-phase-handoff.md`
(Runs 1-19 + unit 7 below). Rulings queue `.agent/W4-02-pending-rulings.md` (q12 applied; q13 readings non-blocking). Branch
`task/W4-02-mini-grid-depth`, head `b065ee8d` (+ this packet), main merged at `067113ec`. Lane A. USER_REVIEW: owner
W4 result review follows independent review. Full backend suite: **not run here by instruction** (runs beside the
final review).

**Final fix round (q14):** fixes `a9fdc260`..`9efa6715` (H2, H3, H4, M1, M2, M4, L1, L2, L4, L5, B-M1, B-L1..L4, L3);
recapture and checks against code head `9efa6715` on branch `task/W4-02-mini-grid-depth-clean`. Capture checks
**556/556**; **M3 closed** (served 08 Oct Overview Renewable card `Headroom 18–20 kW` at 1440 and 390). q14 readings
1-5 in pending-rulings await confirmation.

## Commits
| Unit | Commits | Content |
| --- | --- | --- |
| 1 | `00a5703a`..`1c4afc21` | `0029_w4_mini_depth`, roles-4/typed properties, writer, migration probes seeded before 0029 (q1) |
| 2 | `0f70936f`, `aca68ab4`; q2 `96945c4f` | pure renewable/service rules and coverage tests |
| 3 | `97401ff0`..`e35d9239` | pure fuel/backup rules, authored v4 profile/mapping, MG-W402-001 install, authored cases |
| 4 | `46682cfc`..`960b0e5b`; q7 `07af0afb`..`a44cb738`; q8 `605ac2d7` | inputs, projection, worker, S7 tick `mini` stage, HTTP replay selection seqs |
| 5 | `476773e9`; q9 `190735fb`, `39a22be1` | historical reads, dual provenance, `GET /api/sites/{code}/performance/mini/{domain}` |
| 6 | `ee461681`..`88294183` (q10 `a82c7a6a`) | Renewable, Service, Fuel, Backup pages; five-tab row; Overview Service/Fuel/Renewable cards |
| q11 | `607f73f5`, `33780a7a` | Run 11 rulings on the four pages + Overview; q12 readings |
| 7 | `3ec1fb25` | captures `.agent/W4-02-evidence/` |
| q14 fix round | `a9fdc260`..`9efa6715`; recapture + records (this round) | final-review fixes; captures 556/556 |
| q12 | `46226fe3`, `0ef42ba5`, `9e8d9e5d`, `b065ee8d` (q12-7); `34ab5d22` (q12-6); `ef979314` (q12-8); `99ce8f19` (q12-1..5, q11-5) | Run 12 rulings; recapture |

## q11 applied (`607f73f5`)
- Renewable (q11-1): `renewableDowngraded` (`frontend/src/sites/miniDepthClient.ts`) runs before `Watch`: currentness
  PENDING_RECOMPUTE/STALE_SOURCE/UNKNOWN, selected provenance absent/UNKNOWN/MIXED, or pending UNKNOWN/MIXED ->
  `Evidence limited`; low <= 0 stays `No usable headroom`; null/UNKNOWN stays `Not assessed`. Same rule withholds the
  Overview `Headroom` value.
- Service (q10-5): all four choices already matched (noninteractive `See effect on verification · Not available yet`,
  `{load_label} (critical)`/`Critical load`, hatched `Unknown` needed bar, Site-local 12:00-13:00 via `localHourWindow`).
- Fuel (q11-2): `Accepted tank reading with bounded uncertainty` for a bounded accepted reading; card note needs a
  bounded value and USE minutes, else `Modelled quantity unavailable`; `Fuel balance: Supported` for SUPPORTED.
- Backup (q11-3/4): `Start success` = count; note `Of {N} witnessed request/result pair(s) in shown chains` with
  N = chains whose REQUEST and START are both OBSERVED, only when N > 0 and count <= N, else `Witnessed pair count
  unavailable`; null card `No witnessed start request and result`. Latest chain by `(outage_start, chain_id)`; cited
  IDs in chain then mapped-step order (conflicting kept); header `Current claim (latest observed outage chain)`.
- Tests: `miniBackupRoutes` (+1 case, pair note fixed), `miniFuelRoutes` (+1), `miniRenewableRoutes` (MIXED pending),
  `s5SiteWindowOverview` (+1 unknown-source case; envelope gained provenance). Focused 5 files / 72 passed.

## Builder readings, all runs (status)
| Run | Reading | Status |
| --- | --- | --- |
| 1 | R1 mixed v3/v4 channel validation for roles-4 | ruled q1 |
| 2 | unit-2 readings 1-15 (renewable/service rules; text at `aca68ab4`) | ruled q2 |
| 3 | unit-3 readings 1-13 (handoff "Readings applied in unit 3": SFC in force, tank edges, fuel never SUPPORTED, outage/REQUEST/START/POWER/LOAD/SERVICE steps, PASS/FAIL, backup status, MG-W402-001 Foundation, event component, authored cases, in-process replay, unregistered fixture) | ruled q3 |
| 6 | q4-3 tank-edge unavailability; any bad supply row blocks every chain; unusable chain INCOMPLETE; pinned critical rows only | ruled q5 |
| 8 | unbound rows dropped not cited; `local_hour` end = start + 1 h UTC; worker cutoff test in step 4 | accepted by q5/q6 |
| 9 | q6 1-6 projection shapes (no per-hour renewable status, row coverage, instant roles, SFC ID null, freshness, start count) | ruled q6 |
| 10 | `Observation.source_id` positional; start pair = OBSERVED START with one outcome; tank source count | ruled q6/q7 |
| 11-12 | q7 S7 tick DDL; q8 legacy MINIGRID without roles-4 | ruled q7, q8 |
| 13 | q9 1-10 read/API (basis wire, no default window, dual provenance, ...) | ruled q9 |
| 15-16 | q10 1-5 (no-headroom word, CTA copy, unbuilt tabs, registry nodes, service choices) | ruled q10, q11-1 |
| 17-18 | q11 1-4 (downgraded word, fuel copy, backup copy, readiness rows) | ruled q11 |
| 19 | **q11-5 a-h Overview cards** (currentness gate on all three; service SUPPORTED + delivered; renewable SUPPORTED + both bounds; fuel any status; unavailable/loading copy; `View detail →` exact window; Dispatch not refreshed; no capability-table Backup row) | ruled Run 12 |
| unit 7 | **q12-1..5** (provenance read of q11-1; q11-1 on Overview; pair plural; scope header; USE minutes = non-null coverage) | ruled Run 12; q12-1 served numeric Renewable headroom (final review M3) **closed**: served 08 Oct Overview capture `Headroom 18–20 kW` passes (final fix round) |
| unit 7 | **q12-6** Overview unreachable live; **q12-7** height budgets; **q12-8** UNKNOWN selected provenance on seed | ruled Run 12 |

## Captures (`.agent/W4-02-evidence/`: `seed.py`, `capture.mjs`, `evidence.json`, `replay.json`, `mock-measure.json`)
**Final fix round recapture (revision `9efa6715`):** fresh private `w402r_test` seeded by `seed.py` (same harness;
accepted 3321 / 326, 123 jobs DONE, 123 selections; stored Service results carry `critical_delivered_coverage`), served
by uvicorn 9748 + vite 6146; DB dropped and servers stopped afterwards. 11 cases x 2 widths (new: `mini numeric` =
Overview `?date=2026-10-08`, files `mini-numeric-{1440,390}-app.png`). **556 passed, 0 failed.** New assertions, on the
fresh load with every disclosure closed: H2 no `authored_demonstration`/raw UPPER_SNAKE enum text on every page, and the
four Performance pages show `Prepared example data, not field readings`; H3 strip starts `Reads on this Overview:` and
the ruled mini-grid objective; M4 Needs-attention reason exactly the ruled sentence, `The Findings list is closed` once;
M3 renewable card `Headroom 18–20 kW` (the value renders only when the q12 provenance/currentness/noon-row gates pass);
M2 critical card note `Critical-service delivered power record · Measured 60 of 60 minutes`, row `Clinic feeder delivered
power`; M1 every `.v69-claim-button` border 0/none and transparent background (3 per width seen); L1 no `not known` bar
value (Unknown bars seen); H4 backup 1440 closed readiness panel <= 316 px with all four rows (incl. `Witnessed outcome`)
inside every clipping box, unscrolled. Non-vacuous: M3 regex temporarily set to `MW` -> 2 failures
(`mini numeric 1440/390: M3 ...`), reverted. Viewed against mocks: M3 Overview (panel order and five cards match
`mock-mini-1440`), backup 1440 (four readiness rows visible, matches `mock-backup-1440`), service 1440 (matches
`mock-service-1440`; critical card 3.87 kW from its own record, bar/table 4 kW).

Earlier (q12 run) capture record follows.
Seed (q12 run): private `w402q_test` (created, dropped after), harness of `test_w402_replay_selection_postgres.py`:
MG-W402-001 installed (now with its persisted `NO_LEGACY_EVIDENCE` basis, q12-6); each of the 29 exact sealed Batch V2
bodies published first with `assetops_backend.publish_source` (`assetops.w4-mini-depth-cases` v1, q12-8), then posted to
`POST /api/ingestion/batches`: accepted positive 3321 / missing-conflicting 326; worker 123 jobs DONE, 123 selections.
`replay.json` holds body digests, publication IDs and selection seqs (no credential). Read only via uvicorn 9748 + vite
6146. Positive = 06 Oct (renewable 06-10 Oct); gap = 12 Oct (renewable 08-12 Oct). Revision `b065ee8d`.

| Page · state | Observed (1440) |
| --- | --- |
| renewable + | `Watch`, `Selected sources: authored_demonstration`, Current; 41–43 / 20 / 18–20 kW / 4 of 5 days |
| renewable gap | `Not assessed`, `No selected assessment`; 3 / 3 days |
| service + | `Service assessment: Supported` (authored); 20 kW, None seen, 3.87 kW, 0 kWh |
| service gap | `Unknown`; only Delivered 20 kW; honest null notes |
| fuel + | `Fuel balance: Unknown`; Expected use 0–2.39 L, note disclosure `Modelled from generator output` |
| fuel gap | `Fuel balance: evidence limited`; `Modelled quantity unavailable` |
| backup + | `Backup readiness: Unknown`; `1 witnessed success`; 3 min; readiness cells `{N} cited records` + `Inspect IDs` |
| backup gap | strip summary `Outage-chain assessment: evidence limited`; chain Incomplete; null-card notes |
| Overview 06 Oct | five cards Service, Dispatch, Battery, Fuel, Renewable: `Delivered 20 kW` (60 of 60 min covered), Dispatch `CLOSED`, Battery `Not available`, `Expected use 0–2.39 L`, Renewable `Unknown` (06 Oct is the excluded day, no headroom) |
| Overview 12 Oct | five cards; Service/Fuel/Renewable `Unknown` (LIMITED/UNKNOWN reads) |

Checks: **424 passed, 0 failed** (`capture.mjs`, all 10 cases x 2 widths): page width at 1440/390 (also with every
disclosure and drawer opened), region count/kind/title order equal to the mock, every region height within its
Run 9 budget (closed **and** opened), 390 table internal scroll minimums, five Overview cards in order. Overview card
rows measure 140 px at 1440 (mock 150) and 466-485 at 390 (mock 507). Bounded regions that scroll internally by design
(q12-7): renewable windows table (390), service loads table (390) and unlock list (gap), fuel bridge (390), backup
readiness (1440); no region clips (probe: no bounded panel body overflows without its own scroller).

## Checks run (final fix round, head `9efa6715`)
- Focused backend (private `w402r_test`, dropped): all 17 `test_w402_*.py` (incl. `test_w402_reads_postgres`,
  `test_w402_overview_reason`, `test_w402_overview_basis_postgres`, `test_w402_migration_postgres`) +
  `test_s5_overview_read` + `test_w401_migration_postgres`: **149 passed** (1071 s).
- Frontend full `npx vitest run`: 98 files, **2412 passed**. `tsc --noEmit`: 0. `npm run build`: passed.
  `tools/check-all.ps1` (includes architecture and agent-workflow): all 11 guards passed.
- Full backend suite: not run (instruction); runs at the same revision beside the re-review.

## Checks run (q12 run, serial)
- `tsc --noEmit`: 0. `npm run build`: passed (9.7 s). `tools/check-all.ps1`: all 11 guards passed.
- Frontend full `npx vitest run` at `b065ee8d`: 98 files, **2404 passed** (164 s).
- Focused backend (private `w402t_test`, dropped): `test_w402_overview_basis_postgres.py` 3 passed (non-vacuous: with
  the route's basis branch removed, the serve test fails with 409; reverted); adjacent `test_s5_overview_postgres`,
  `test_s5_overview_read`, `test_w402_migration_postgres`, `test_s1_cutover`, `test_t027_overview`,
  `test_s1_bindings_postgres`: 110 passed (84 s).
- Earlier runs: see handoff "Checks" lines (Run 6-20).
- Full backend Postgres suite: not run (instruction).

## Accepted limitations (per rulings)
- Fuel never SUPPORTED in W4-02 (no delivery completeness); residual `Cannot compute`; delivery never `0 L` (q3, q11-2).
- Backup readiness heading always `Unknown`; `Witnessed outcome` always `No accepted record` / `Readiness remains
  unverified`; `No outage in the selected hour` unreachable with instant supply reports (q3-8, q11-3d, q11-4).
- `What was needed` always hatched Unknown; verification CTA and Opportunity decision are `· Not available yet` (q10, q11).
- Renewable recurrence not established; demand/sale/tariff `Not assessed` (q9).
- No Overview Backup card or read (B3); no capability-table Backup row in this tree (q11-5h).
- Dispatch link only, financials null (`No linked dispatch consequence` inert) (q9, q11-2).

## Residual risk / review focus
- q12-6 schema: `site_cutover_basis` was added inside this branch's unmerged `0029_w4_mini_depth` (as the q8 amend did),
  not a new 0030; any DB already at 0029 from earlier runs lacks it (test DBs only). Wiring uses the Postgres
  Foundation store's `no_legacy_evidence_basis` (other stores keep the 409 default).
- q12-7: closed disclosures hide limitation lists, ID lists and coverage text by default (strip summary
  `Limited by N conditions`; backup strip summary is the chain-status chip). Reviewer: side-by-side with the mock.
- Overview Renewable shows a value only on a SUPPORTED day with a matching noon row; neither captured day has one
  (06 excluded, 12 limited); 07-10 Oct would. Builder readings logged as q13 (non-blocking).
