# W4-02 review packet (mini-grid depth: renewable, service, fuel, backup)

Contract `.agent/W4-02-build-spec.md` (closures 1-5, Run 1-11 rulings q1-q11). Handoff `.agent/W4-02-phase-handoff.md`
(Runs 1-19 + unit 7 below). Rulings queue `.agent/W4-02-pending-rulings.md` (q12 open). Branch
`task/W4-02-mini-grid-depth`, head `3ec1fb25` (+ this packet), main merged at `c632077b`. Lane A. USER_REVIEW: owner
W4 result review follows independent review. Full backend suite: **not run here by instruction** (runs beside the
final review).

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
| 19 | **q11-5 a-h Overview cards** (currentness gate on all three; service SUPPORTED + delivered; renewable SUPPORTED + both bounds; fuel any status; unavailable/loading copy; `View detail →` exact window; Dispatch not refreshed; no capability-table Backup row) | **open** |
| unit 7 | **q12-1..5** (provenance read of q11-1; q11-1 on Overview; pair plural; scope header; USE minutes = non-null coverage) | **open** |
| unit 7 | **q12-6** Overview unreachable live; **q12-7** height budgets; **q12-8** UNKNOWN selected provenance on seed | **open** |

## Captures (`.agent/W4-02-evidence/`: `seed.py`, `capture.mjs`, `evidence.json`, `replay.json`, `mock-measure.json`)
Seed: private `w402p_test` (created, dropped after), harness of `test_w402_replay_selection_postgres.py`: MG-W402-001
installed, gateway credential issued by the provisioning CLI, both authored variants posted to
`POST /api/ingestion/batches` (TLS boundary): accepted positive 3321 / missing-conflicting 326; worker 123 jobs DONE,
123 selections (seqs/revision IDs in `replay.json`, no credential). Read only via uvicorn 9748 + vite 6146. Mock via
`node tools/measure-mock-panels.mjs` (renewable, service, fuel, backup, mini). Files `{screen}-{positive|gap}-{1440|390}-app.png`,
`mock-{screen}-{w}.png`. Positive = 06 Oct (renewable 06-10 Oct); gap = 12 Oct (renewable 08-12 Oct). Revision `33780a7a`.

| Page · state | Observed (1440) |
| --- | --- |
| renewable + | `Evidence limited` (LIMITED, sources unknown); cards 41–43 / 20 / 18–20 kW / 4 of 5 days; 5 rows, 06 Oct Excluded |
| renewable gap | `Not assessed`, `No selected assessment`; 3 / 3 days |
| service + | `Service assessment: Limited` (Source class unknown); 20 kW, 3.87 kW critical, 0 kWh; clinic row Supported |
| service gap | `Unknown`; only Delivered 20 kW; honest null notes |
| fuel + | `Fuel balance: Unknown`; Expected use 0–2.39 L, note `... for 60 min × selected fuel coefficient ...`; bridge 5 rows |
| fuel gap | `Fuel balance: evidence limited`; `Modelled quantity unavailable` |
| backup + | `Backup readiness: Unknown` + `Outage-chain assessment: evidence limited`; `1 witnessed success` / `Of 1 witnessed request/result pair in shown chains`; 3 min vs target 5; chain Pass; `Open Dispatch → ?day=2026-10-06`, `Browse Actions → /actions` |
| backup gap | chain Incomplete with `Conflicting records 12:06`; null-card notes |
| Overview | `Awaiting evidence migration` (S5) on both days: mini cards not mounted (q12-6) |

Checks (296): pass on page overflow for all four pages at both widths (scrollW <= 1425/390), region count/kind
order and panel titles equal to the mock, 390 table internal scroll minimums. **Fail: 39 region heights** (renewable
10, service 11, fuel 10, backup 8; worst backup readiness 598/316 at 1440, 2441/471 at 390, from the q11-4 UUID list)
and 6 Overview checks (cards absent; 1440 scrollW 1440 on a page shorter than the viewport). Not fixed: q12-7.

## Checks run (this run, serial)
- `tsc --noEmit`: 0. `npm run build`: passed (10.3 s).
- Frontend full `npx vitest run` at `3ec1fb25`: 98 files, 2401 passed, 1 failed (188 s):
  `siteFindingEvidence.test.tsx > Finding frame sections (S4-03 phase 2) > renders Evidence as ...` (empty text
  content). File not touched by this branch; reruns alone: fail, pass, pass, pass -> intermittent.
- `tools/check-all.ps1`: all 11 guards passed.
- Earlier runs (handoff "Checks" lines): unit 3 focused 230 + gateway 93 + cold/provenance 74 passed; units 4-5
  focused Postgres sets (Run 6-14: e.g. 48 passed Run 10, `test_w402_reads*` 17 passed Run 13); Run 19 full frontend
  98 files / 2399 passed, check-all 11/11.
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
- q12-7 budgets: the pages render honest content but 39 regions exceed the Run 9 height budgets; needs a ruling.
- q12-6: Overview mini cards are proved only in jsdom; live MG-W402-001 Overview is the S5 migration state.
- q12-8: positive `Watch`/`Supported` states not reachable on the seeded replay (sources UNKNOWN); jsdom-only.
- Intermittent `siteFindingEvidence` test (outside W4-02).
