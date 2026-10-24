# Post-W6 audit batch 12: W4 mini depth

IDs: `renewable`, `service`, `fuel`, `backup`. Branch `audit/batch-12` at main `6813b477` (product code identical to frozen `fddf5cad`), worktree `AssetOpsV1-review6`. Mock authority: `frontend/mockups/v69/index.html`, served by the same Vite origin and rendered at 1440x1000 and 390x900 CSS px.

## Route reconciliation

| ID | App route (`frontend/src/App.tsx`) | Status |
| --- | --- | --- |
| `renewable` | `SITE_PERFORMANCE_SUBTAB_ROUTE_PATH` `/sites/:siteId/performance/renewable` -> `SitePerformanceFrame` -> `MiniRenewable` (MINIGRID + `BUILT_MINI_PAGES`) | mounted |
| `service` | same route, `/performance/service` -> `MiniService` | mounted |
| `fuel` | same route, `/performance/fuel` -> `MiniFuel` | mounted |
| `backup` | same route, `/performance/backup` -> `MiniBackup`. The URL is shared with `coldbackup` and dispatched by Site type. | mounted |

The routes are correct. **Spec error (B12-13):** the spec's producer column names `tools/s402*` (S4-02 money tools). The real producer is W4-02's `.agent/W4-02-evidence/seed.py`, using `tools/w402_mini_depth_cases.py`. W4-03's `tools/w403_mini_decisions_walkthrough.py` provides the renewable decision CTA state.

## Producers, environment and capture

- **W4-02 seed (reviewed, unmodified).** Ran `.agent/W4-02-evidence/seed.py` with `PYTHONPATH=backend;backend/tests;gateway;simulator;contracts;host`. It installs MG-W402-001, issues the gateway credential, publishes and posts both authored variants through `POST /api/ingestion/batches`, and drains the mini worker. Result: accepted 3321 / 326, 123 jobs DONE, 123 selections. The seed hard-codes the DB `w402r_test`, which falls under the `*_test` authorization. I checked `pg_database` first: it did not exist, and only batch 11's `assetops_audit_b11_test` was present. I created the DB with `createdb` and dropped it afterwards. The seed rewrites the tracked `.agent/W4-02-evidence/replay.json`. I copied the new record to `logs/replay-b12.json` and restored the tracked file with `git checkout`. The API was `host/` `uvicorn lab_app:app` on 127.0.0.1:18201 with `DATABASE_URL=w402r_test`, and Vite ran on 5182 `--strictPort`.
- **W4-03 walkthrough (reviewed, unmodified)**, for the renewable decision CTA: `--db assetops_audit_b12_test --work var/w403_b12`, modes `prepare` (after `createdb`), `serve` and `replay-positive`, then `drop`. **Port deviation:** `serve` hard-codes API 127.0.0.1:9761. I checked it was free first. Vite was restarted on 5182 with `ASSETOPS_API_PORT=9761`.
- **Capture.** `tools/capture-b12.mjs` is batch 10's wrapper with CDP 9522 and a mini-page DOM block replacing the estate one. That block reads strip, cards, notice, refusal, the 'Not recorded'/'Not available yet' counts, enum/UUID counts and Overview card links. It only navigates, waits, screenshots and measures. `tools/mk_targets.py` writes the URLs, using the W4-02 unit-7 windows. Claims: main 232/240 (the 8 failures are the refused pairs, which have 0 panels against the mock's 3-4), w403 24/24, links 36/36. Logs are in `logs/`.
- `var/sites` did not cause a 503 on this DB (`/api/sites` returned 200), so nothing was moved. All PIDs I started were stopped by PID, and both DBs were dropped.

## Cases and pairs

- **positive:** all 4. Renewable covers 06-10 Oct local; the others cover the 06 Oct 12:00-13:00 local hour. Renewable's 5-row table is also the widest real worst case.
- **gap-limited** (missing/conflicting variant): all 4. Renewable covers 08-12 Oct; the others cover the 12 Oct hour.
- **no-window** (bare route, so browser today 2026-10-24): all 4. These are honest 'No selected assessment' states.
- **refused-invalid** (422 INVALID_WINDOW): renewable with 6 days, the others with 2 hours.
- **known-before-evidence** (positive window, `known_at=2026-10-01`): all 4.
- **w403-decision-positive:** renewable under the W4-03 producer, with the 'Opportunity decision ->' CTA.

Total **42 pairs**: 8 representative and 34 further states. Another 8 Overview link-check captures are not counted.

The producers cannot yield worst-case 160-character rows, multi-chain backup, populated fuel deliveries/closing, or a supported Service with a request baseline. Those layouts are unverified.

## Structural verdict

Panel count, order and titles match the mock on all 34 non-refused pairs:
- renewable: 3 panels
- service: 4 panels
- fuel: 3 panels
- backup: 4 panels

The status strip, the four-card row and the notice sit in mock order. Table columns match, except backup's 'Current claim (latest observed outage chain)'. No panel exceeds 1.3x the mock. The maximum is 1.14 (service gap-limited), and the empty states run 0.18-0.75x. There is no page horizontal overflow. Tables at 390 and the fuel bridge scroll internally by design (q12-7). The only console error appears on the Overview link check (B12-12). The refused state keeps the period bar and a 'Period cannot be read' box but drops the strip, cards and panels.

## Cross-cutting (cited)

| ID | Pairs |
| --- | --- |
| B1-01/B2-01 top bar | all 42 |
| B1-04/B2-36 rail 'Not available yet' | all 42 |
| B2-02 page-local window | all 42. The period bar is the R88/R112 seam; propose extending those D1 rows. |
| B1-07/B2-03 14 px prose | all 34 non-refused |
| B1-02/B2-04 tall 390 header | refused-invalid 390, all 4 IDs (about 237 px dark block). Long pages show the normal 92 px. |
| B1-53 raw codes/UUIDs | service load codes `load-clinic`/`load-mill`/`load-res`; backup 'Inspect IDs' UUID lists; raw UTC ISO period line (B12-10) |
| B2-21/B3-04 UTC | mostly closed: the Site-local window is primary and the raw UTC line remains |
| B3-01 duplicate tab row | does not recur |
| B6-13/B9-05 refused furniture | recurs on refused-invalid, all 4. A banner is present here (B12-06). |
| B7-03/B9-02 | 'Not recorded' does not occur. The 'Not available yet' analogue is B12-07. |
| B2-08/B2-10 | The Overview links reach service/fuel/renewable with exact windows. B2-08 (no Dispatch/Battery link) recurs on MG-W402-001. There is no Backup card, by ruling. B2-10 does not touch these pages. |

Carried checks: '1 incidents' and `c1 · EV_CONNECTOR` do not occur. The domainActionClient copy is not used, but the mini 422 copy is one generic sentence for distinct invalid inputs (B12-06). D3 rows R22/R23/R24/R37/R38/R60 do not touch these screens. R88/R112 cover only cold/EV Work today.

## Differences (all dispositions are proposals)

| ID | Screens | What | Proposed disposition |
| --- | --- | --- | --- |
| B12-X1 | all | Cross-cutting rows above | Cite; extend R88/R112 (D1) to mini Performance |
| **B12-01** | all | The register has no row for any W4-02 screen despite many ruled departures (Q19-Q24, q9-q12, B3) | Architect registers each one (D1/D2) or reclassifies it as D3 |
| B12-02 | all | Tones missing: strip/decision chips neutral grey; bars single blue (mock amber/green/red/grey) | D3 Low (shared tone tokens) or D2 |
| B12-03 | renewable | No confidence chip, although spec line 51 requires 'Confidence: Not assessed' | D3 Low, or D1 if ruled later |
| **B12-04** | renewable | W4-02 state shows 'The evidence changed. Reload this page.' for 409 PERFORMANCE_CUTOVER_CLOSED from `/opportunities`; `decisionRefusalCopy` maps every 409 to that sentence | D3 Low-Medium (copy keyed on the error code) |
| B12-05 | renewable gap | 'Not assessed · No selected assessment' sits beside populated cards and 'Solar headroom on 3 of 3 assessed days'; Q19 says 'Recurrence is not established' unless 5 complete days | D3 Low (Architect to confirm Q19 still holds) |
| B12-06 | all refused | Strip/cards/panels dropped (0 vs 3-4); one generic 422 sentence for 6-day and 2-hour errors | Cite B6-13/B9-05; copy D3 Low with the domainActionClient fix owner, or D2 |
| B12-07 | renewable, service | 'Compare with Dispatch evidence · Not available yet' (q9-8, multi-UTC-day windows) and 'See effect on verification · Not available yet' (Q20) where the mock has live links | D1 register rows; optional D2 Dispatch first-day link |
| B12-08 | all | Example content replaced (grain mill, Day N, roles, column label, 'Browse Actions'); strip limitations behind a disclosure | D1/D4 or D2, registered |
| B12-09 | service | Inner sub-heading 'Delivered power by addressed load' repeats the next panel's title | D3 Low |
| B12-10 | all | Raw load codes, UUID lists, raw UTC ISO line | Cite B1-53 |
| B12-11 | all | Text card headlines smaller or wrapping; unequal 390 card heights | D3 Low or D2 (B10-02 seam) |
| B12-12 | link check | Overview links correct; B2-08 recurs; React duplicate-key console warning on mini Overview (W4-03 state) | Cite B2-08; duplicate key D3 Low (`mini`) |
| B12-13 | spec | Producer column says `tools/s402*` | Correct the spec |
| B12-14 | all | Structure, heights (max 1.14) and overflow pass | Informational |

## Blockers

None. The port 9761 deviation, the hard-coded `w402r_test` DB and the restored `replay.json` are recorded above.
